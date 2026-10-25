#!/usr/bin/env python3
"""AUDIT (read-only): flag `flash bank <name> <driver> ...` invocations in tcl/
whose DRIVER NAME is not a compiled flash driver.

WHY THIS IS A SEPARATE TOOL
---------------------------
tools/audit_dangling_refs.py resolves `source [find X]` FILE references only.  A
config can source every file it names and still abort at run time because the
driver string it hands to `flash bank` was never imported:

    tcl/target/stm32h5x.cfg: flash bank $_CHIPNAME.flash_ns stm32h5x ...
    src/flash/nor/drivers.c:  (no &stm32h5x_flash entry)
    -> Error: flash driver 'stm32h5x' not found

That is a NAME-resolution failure, not a file-resolution one, so no other tool
here covered it.  This tool only reads; the sole writes anywhere happen inside a
temp dir created by --selftest.

HOW THE COMPILED DRIVER SET IS RESOLVED (no binary needed)
---------------------------------------------------------
1. Parse the NOR table in src/flash/nor/drivers.c
   (`static const struct flash_driver * const flash_drivers[] = { &sym, ... };`)
   and take each symbol (e.g. `&stm32h5x_flash`).
2. Map symbol -> `.name`: candidates are Makefile.am's NOR_DRIVERS + NORHEADERS
   (`%D%` -> src/flash/nor) and then a bounded glob of src/flash/nor/*.c and
   *.h, so a symbol in an unlisted file is still found.  `const struct
   flash_driver <sym> = { ... };` is located by brace matching and `.name` is
   read from THAT block only - a driver source holds other `.name` fields (its
   own command table) which must not leak in.  An unresolvable symbol aborts the
   run (exit 2) rather than being silently skipped.  Only NOR matters:
   `flash bank <name> <driver>` resolves against this table.

SCANNING, AND HOW THE DRIVER FIELD IS CLASSIFIED
------------------------------------------------
Every tcl/**/*.cfg and tcl/**/*.tcl, line by line, tokenized the way Tcl reads
it: whitespace-separated words, brace-quoted words collapsed to their content
(`{flash bank} x drv ...`, the form Tcl prints in tracebacks), quote tracking,
`[...]` reduced to a dynamic marker, and `#` a comment only where a command
could start (line start or after `;`).  So commented-out `# flash bank` lines
and trailing `... # note` are handled, while `flash probe`, `flash write_image`
and `flash banks` never match.  A literal driver field is checked against the
compiled set; a miss is a FAIL (exit 1).  A dynamic field (`$V`, `${V}suffix`,
`[...]`) has no statically known value: reported separately, never counted as
missing (known limitation).
"""

import argparse, pathlib, re, shutil, sys, tempfile, collections

HERE = pathlib.Path(__file__).resolve().parent.parent
NOR = pathlib.Path("src/flash/nor")
TABLE_RE = re.compile(r"flash_drivers\[\]\s*=\s*\{(?P<body>.*?)\n\};", re.S)
DEF_RE = re.compile(r"const\s+struct\s+flash_driver\s+(\w+)\s*=\s*\{")
NAME_RE = re.compile(r'\.name\s*=\s*"([^"]*)"')
BANK_RE = re.compile(r"^flash\s+bank$")


def read_text(p: pathlib.Path) -> str:
    """UTF-8, errors replaced: some paths here are non-ASCII and the Windows
    console defaults to GBK."""
    return p.read_text(encoding="utf-8", errors="replace")


def candidates(nor: pathlib.Path) -> list[pathlib.Path]:
    """Makefile.am's NOR_DRIVERS/NORHEADERS first, then a bounded glob so a
    symbol living in an unlisted file is still found."""
    listed = []
    if (mk := nor / "Makefile.am").is_file():
        text = read_text(mk)
        for var in ("NOR_DRIVERS", "NORHEADERS"):
            m = re.search(rf"^{var}\s*=\s*(?P<b>(?:.*\\\n)*.*)$", text, re.M)
            for tok in (m.group("b") if m else "").replace("\\\n", " ").split():
                tok = tok.replace("%D%", NOR.as_posix()).strip("\\")
                if tok.endswith((".c", ".h")):
                    listed.append(nor.parent.parent / tok)
    files = [f for f in listed if f.is_file()]
    files += [f for f in sorted(list(nor.glob("*.c")) + list(nor.glob("*.h")))
              if f not in files]
    return files


def symbol_names(nor: pathlib.Path) -> dict[str, tuple[str, str]]:
    """sym -> (".name" value, "file:line" of the definition)."""
    found: dict[str, tuple[str, str]] = {}
    for src in candidates(nor):
        text = read_text(src)
        for dm in DEF_RE.finditer(text):
            i, depth, j = text.index("{", dm.end() - 1), 0, text.index("{", dm.end() - 1)
            while j < len(text) and depth >= 0:
                depth += (text[j] == "{") - (text[j] == "}")
                if depth == 0:
                    break
                j += 1
            if nm := NAME_RE.search(text[i:j + 1]):
                found.setdefault(dm.group(1), (
                    nm.group(1), f"{src.as_posix()}:{text[:i].count(chr(10)) + 1}"))
    return found


def load_compiled_drivers(root: pathlib.Path) -> tuple[set[str], dict[str, str]]:
    """-> (compiled NOR driver names, symbol -> "name" provenance)."""
    table = root / NOR / "drivers.c"
    if not table.is_file():
        raise SystemExit(f"audit_flash_drivers: cannot find {table}")
    m = TABLE_RE.search(read_text(table))
    if not m:
        raise SystemExit(f"audit_flash_drivers: no flash_drivers[] in {table}")
    syms, names, prov, unresolved = symbol_names(root / NOR), set(), {}, []
    for sym in re.findall(r"&(\w+)", m.group("body")):
        if syms.get(sym) is None:
            unresolved.append(sym)
        else:
            names.add(syms[sym][0])
            prov[sym] = syms[sym][1]
    if unresolved:
        raise SystemExit("audit_flash_drivers: cannot resolve .name for symbol(s) "
                         + ", ".join(unresolved) + " - aborting, not skipping them")
    return names, prov


def words(line: str) -> list[str]:
    """Approximate Tcl word splitting for one line - state resets per line,
    which is how these configs are written (one command per line)."""
    out, cur, quote, stack, start, i = [], "", False, [], True, 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == "\\" and i + 1 < len(line):
                cur, i = cur + line[i:i + 2], i + 2
                continue
            if c == '"':
                quote = False
                out.append(cur)
                cur = ""
            else:
                cur += c
        elif c in " \t" or (c == ";" and not stack):
            out += [cur] if cur else []
            cur, start = "", True
        elif c == "#" and start:
            out += [cur] if cur else []
            break
        elif c == '"' and not cur:
            quote = True
        elif c == "{":
            # a brace-quoted word collapses; inside a word (`${VAR}suffix`,
            # nested braces) the brace stays part of that word
            stack.append("q" if (not stack and not cur)
                         else "v" if cur.endswith("$") else "i")
            if stack[-1] != "q":
                cur += c
        elif c == "}":
            if not stack:                      # stray close: next command starts
                out += [cur] if cur else []
                cur, start = "", True
            elif stack.pop() == "q" and not stack:
                out.append(cur)
                cur = ""
            else:
                cur += c
        elif c == "[" and not stack and not cur:
            j, d = i + 1, 1
            while j < len(line) and d > 0:
                d += (line[j] == "[") - (line[j] == "]")
                j += 1
            out.append("[...]")
            i = j
            continue
        else:
            start = False
            cur += c
        i += 1
    return out + [cur] if cur else out


def scan_tcl(root: pathlib.Path) -> dict:
    """Walk tcl/ and collect every `flash bank` invocation."""
    res = {"files": collections.Counter(), "invocations": 0,
           "refs": collections.Counter(), "dynamic": collections.Counter(),
           "loc": collections.defaultdict(list)}
    for p in sorted((root / "tcl").rglob("*")):
        if p.suffix not in (".cfg", ".tcl"):
            continue
        res["files"][p.suffix] += 1
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            w = words(line)
            if w and BANK_RE.match(w[0]) and len(w) > 1:
                w = ["flash", "bank"] + w[1:]        # `{flash bank} ...`
            if len(w) < 4 or w[0] != "flash" or w[1] != "bank":
                continue                             # other flash subcommands
            res["invocations"] += 1
            driver, where = w[3], f"{p.as_posix()}:{lineno}"
            res["dynamic" if ("$" in driver or "[" in driver)
                else "refs"][driver] += 1
            res["loc"][driver].append(where)
    return res


def report(root: pathlib.Path, drivers: set[str], res: dict) -> int:
    """Print the audit and return the process exit status (1 if anything is
    missing from the compiled driver set)."""
    missing = sorted(n for n in res["refs"] if n not in drivers)
    print(f"root: {root}\n"
          f"compiled NOR drivers resolved from {NOR.as_posix()}/drivers.c: {len(drivers)}\n"
          f"scanned: {sum(res['files'].values())} files ({res['files']['.cfg']} .cfg, "
          f"{res['files']['.tcl']} .tcl)\n"
          f"flash bank invocations: {res['invocations']}\n"
          f"distinct literal driver names referenced: {len(res['refs'])}\n"
          f"dynamic driver fields (not checkable statically): "
          f"{sum(res['dynamic'].values())}"
          "\n\nliteral driver references (name: count, first site):")
    for n in sorted(res["refs"]):
        print(f"  {n}: {res['refs'][n]}   {res['loc'][n][0]}"
              + ("" if n in drivers else "   <-- NOT COMPILED"))
    print(f"\ndynamic driver fields: {len(res['dynamic'])} distinct expression(s)")
    for e in sorted(res["dynamic"]):
        locs = res["loc"][e]
        print(f"  {e}: {res['dynamic'][e]}   {locs[0]}"
              + ("" if len(locs) <= 1 else f" (+{len(locs) - 1} more)"))
    print(f"\ndrivers NOT in the compiled set: {len(missing)}")
    for n in missing:
        for site in res["loc"][n]:
            print(f"  MISSING driver '{n}' at {site}")
    print("\naudit_flash_drivers: " + (
        f"FAIL ({len(missing)} driver name(s) not compiled: {', '.join(missing)})"
        if missing else f"OK (n={len(drivers)} compiled drivers, "
        f"{res['invocations']} flash bank invocations, 0 missing)"))
    return 1 if missing else 0


MINI = {
    "src/flash/nor/drivers.c":
        "static const struct flash_driver * const flash_drivers[] = {\n"
        "\t&faux_flash,\n};\n",
    "src/flash/nor/faux.c":
        'const struct flash_driver faux_flash = {\n\t.name = "faux",\n};\n',
    "tcl/t.cfg":
        "# flash bank commented ghost2 0 0 0 0 cpu\n"      # comment: ignored
        "flash bank ok faux 0x1000 0 0 0 cpu\n"            # compiled: fine
        "flash bank bad ghost 0x2000 0 0 0 cpu\n"          # absent: must FAIL
        "{flash bank} brace faux 0x3000 0 0 0 cpu\n"       # traceback form
        "flash bank dyn $_TARGETNAME 0x4000 0 0 0 cpu\n"   # dynamic, unchecked
        "flash probe 0\nflash write_image erase x.bin 0\n",
}


def selftest() -> int:
    """Prove the detector fires on a synthetic tree, then that the real tree is
    clean.  The real tree is only read; the synthetic one is a temp dir removed
    on the way out."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="audit_flash_drivers_"))
    try:
        for rel, body in MINI.items():
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        drivers, _ = load_compiled_drivers(tmp)
        res = scan_tcl(tmp)
        missing = sorted(n for n in res["refs"] if n not in drivers)
        print(f"selftest: synthetic tree {tmp}\n"
              f"selftest: compiled={sorted(drivers)} invocations={res['invocations']} "
              f"literal={sorted(res['refs'])} dynamic={dict(res['dynamic'])}\n"
              f"selftest: missing={missing}")
        rc = report(tmp, drivers, res)
        assert drivers == {"faux"}, drivers
        assert missing == ["ghost"], missing
        assert res["invocations"] == 4, res["invocations"]
        assert dict(res["dynamic"]) == {"$_TARGETNAME": 1}, dict(res["dynamic"])
        assert rc == 1, rc
        real_drivers, _ = load_compiled_drivers(HERE)
        real = scan_tcl(HERE)
        real_missing = sorted(n for n in real["refs"] if n not in real_drivers)
        print(f"selftest: real tree -> {len(real_drivers)} drivers, "
              f"{real['invocations']} invocations, missing={real_missing}")
        assert not real_missing, real_missing
        print("selftest: OK (not vacuous: synthetic 'ghost' detected -> exit 1; "
              "real tree clean -> exit 0)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(HERE), help="checkout to audit")
    ap.add_argument("--selftest", action="store_true",
                    help="build a synthetic tree and prove the detector fires")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    root = pathlib.Path(args.root).resolve()
    drivers, prov = load_compiled_drivers(root)
    print(f"resolved {len(drivers)} compiled NOR drivers "
          f"(stm32h5x_flash -> {prov.get('stm32h5x_flash', 'absent')})")
    return report(root, drivers, scan_tcl(root))


if __name__ == "__main__":
    raise SystemExit(main())
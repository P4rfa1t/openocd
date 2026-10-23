#!/usr/bin/env python3
"""Repair tcl configs whose `source [find ...]` still points at the OLD flat
upstream layout after upstream reorganized tcl/target/ into vendor
subdirectories (tcl/target/ti_tms570.cfg -> tcl/target/ti/tms570.cfg).

WHY THIS EXISTS
---------------
Files imported from forks were written against the pre-reorganization tree, so
they say `source [find target/ti_tms570.cfg]`. Upstream moved BOTH the directory
AND dropped the vendor prefix from the filename. The file therefore exists, but
under a different path, and the import merged by content so the referencing
line was never rewritten.

Detection is deliberately conservative: a reference is only rewritten when the
literal path does NOT exist AND exactly one candidate exists whose vendor
prefix matches the directory and whose basename matches after stripping the
vendor prefix. Anything ambiguous is reported, never guessed.

Idempotent: re-running after a successful repair reports 0 rewrites.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TCL = ROOT / "tcl"

# `source [find target/ti_tms570.cfg]`  and  `source [find target/ti/foo.cfg]`
SRC_RE = re.compile(r"(source\s*\[\s*find\s+)([\w./-]+)(\s*\])")

# Upstream renames that cannot be derived mechanically from the old name.
# Each entry was verified by hand: the target file exists, and it declares the
# same `if { [info exists X] }` variables the referencing config sets. Do not
# add speculative entries here -- an unverified alias breaks a board config
# silently at runtime.
RENAMES = {
    # tcl/target/ti-cjtag.cfg -> tcl/target/ti/cjtag.cfg
    # (vendor subdirectory added AND the "ti-" prefix dropped)
    "target/ti-cjtag.cfg": "target/ti/cjtag.cfg",
    # tcl/fpga/altera-cycloneiii.cfg -> tcl/fpga/altera/cyclone-iii.cfg
    # (vendor subdirectory added, "altera-" prefix dropped, named hyphenated)
    "fpga/altera-cycloneiii.cfg": "fpga/altera/cyclone-iii.cfg",
    # tcl/target/adspsc58x.cfg -> tcl/target/adspsc58x_memory_map.xml only
    # No .cfg exists anywhere in upstream or in the local tree; the generic
    # config was never published. NOT aliased -- see unresolved report.
}


def strip_comments(text: str) -> str:
    """Blank out TCL comments so commented-out lines never drive a rewrite.

    Kept as a helper for callers that only want to *detect*, this is not used
    for the rewrite itself (we must preserve the original bytes).
    """
    out = []
    for line in text.splitlines(True):
        s = line.lstrip()
        out.append("" if s.startswith("#") else line)
    return "".join(out)


def resolve(rel: str, tcl_root: Path) -> Path | None:
    """Resolve a `[find X]` path the way OpenOCD does: relative to tcl/."""
    p = (tcl_root / rel).resolve()
    try:
        p.relative_to(tcl_root.resolve())
    except ValueError:
        return None  # escaped the tcl/ tree; never rewrite those
    return p


def find_repair(rel: str, tcl_root: Path) -> tuple[str, str] | None:
    """Return (old_rel, new_rel) if a unique relocated file can be proven."""
    cur = resolve(rel, tcl_root)
    if cur is None or cur.is_file():
        return None

    parts = Path(rel).parts
    if len(parts) < 2:
        return None
    parent = Path(*parts[:-1])
    name = parts[-1]
    stem = Path(name).stem
    suffix = Path(name).suffix

    base = tcl_root / parent
    if not base.is_dir():
        return None

    # Upstream reorganized tcl/target/ in TWO different ways, and both must
    # be handled:
    #
    #   (1) vendor subdirectory added, filename unchanged
    #         target/am335x.cfg   ->  target/ti/am335x.cfg
    #   (2) vendor subdirectory added AND vendor prefix dropped from filename
    #         target/ti_tms570.cfg ->  target/ti/tms570.cfg
    #
    # Case (1) is far more common (ti/, st/, nordic/, nxp/, ...). Both are
    # matched only when the result is UNIQUE, so an ambiguous name is reported
    # rather than guessed.
    cands: list[Path] = []

    # Case (1): same filename inside any vendor subdirectory.
    for sub in sorted(base.iterdir()):
        if sub.is_dir() and (sub / name).is_file():
            cands.append(sub / name)

    # Case (2): vendor prefix stripped from the filename, inside a directory
    # whose name is that prefix.
    if not cands:
        for sub in sorted(base.iterdir()):
            if not sub.is_dir():
                continue
            prefix = f"{sub.name}_"
            if stem.startswith(prefix):
                c = sub / f"{stem[len(prefix):]}{suffix}"
                if c.is_file():
                    cands.append(c)

    if len(cands) == 1:
        return rel, str(cands[0].relative_to(tcl_root)).replace("\\", "/")

    # Case (3): upstream added a vendor subdirectory AND renamed the file to a
    # normalized form.  The hyphenation/prefix changes are not mechanically
    # expressible, so this case is handled by an explicit alias table below
    # rather than by fuzzy matching -- a wrong guess here breaks a board
    # config silently, which is worse than leaving it reported.
    if not cands:
        alias = RENAMES.get(rel)
        if alias and (tcl_root / alias).is_file():
            return rel, alias

    return None


def main() -> int:
    if not TCL.is_dir():
        print("ERROR: tcl/ not found", file=sys.stderr)
        return 1

    rewrites = []
    unresolved = []

    for path in sorted(TCL.rglob("*")):
        if path.suffix not in (".cfg", ".tcl"):
            continue
        raw = path.read_text(encoding="utf-8", errors="surrogateescape")
        new = raw
        for m in SRC_RE.finditer(raw):
            lead, rel, tail = m.group(1), m.group(2), m.group(3)
            if "$" in rel:
                continue  # dynamic path, cannot reason statically
            fix = find_repair(rel, TCL)
            if fix:
                old_rel, new_rel = fix
                new = new.replace(f"{lead}{old_rel}{tail}", f"{lead}{new_rel}{tail}")
                rewrites.append((str(path.relative_to(ROOT)), old_rel, new_rel))
            else:
                cur = resolve(rel, TCL)
                if cur is not None and not cur.is_file():
                    # only report live (non-comment) references
                    line = raw[: m.start()].count("\n") + 1
                    src_line = raw.splitlines()[line - 1].lstrip()
                    if not src_line.startswith("#"):
                        unresolved.append(
                            (str(path.relative_to(ROOT)), line, rel)
                        )

        if new != raw:
            with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
                f.write(new)

    print(f"rewrites : {len(rewrites)}")
    for f, o, n in rewrites:
        print(f"  {f}\n      {o}  ->  {n}")

    print(f"\nunresolved live references: {len(unresolved)}")
    for f, ln, r in unresolved:
        print(f"  {f}:{ln}  -> {r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

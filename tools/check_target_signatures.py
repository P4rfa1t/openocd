#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Static check: do the merged target backends still match upstream's
struct target_type callback signatures?

The compiler is the real judge, but a full CI round trip costs ~15 minutes.
This script catches the common failure mode -- a third-party fork that was
written against an older upstream -- by comparing the *types* of the
parameters of every function each backend installs into `struct target_type`
against the prototypes upstream declares in src/target/target_type.h.

Parameter *names* are irrelevant to C type compatibility, so they are
stripped before comparing.  A mismatch here is a certain problem; a match is
a strong hint, not a proof of compilation.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TT = ROOT / "src" / "target" / "target_type.h"

# Files that install a struct target_type of their own.
BACKENDS = [
    "c28x.c",
    "tms320.c",
    "quark_d2000.c",
    "quark_se.c",
    "vortex86.c",
    "loongarch.c",
    "mchp_ri4_bridge.c",
    "vexriscv.c",
]

# Pointer/array/function declarators we do not want to treat as a type.
NOISE = {"const", "struct", "volatile", "restrict", "inline"}


def type_words(params: str) -> list[str]:
    """Reduce a parameter list to its type words, dropping parameter names.

    'struct target *target'   -> ['struct', 'target', '*']
    'target_addr_t address'   -> ['target_addr_t']
    'const uint8_t *buffer'   -> ['uint8_t', '*']
    """
    params = re.sub(r"/\*.*?\*/", " ", params, flags=re.S)
    params = re.sub(r"\[[^\]]*\]", " ", params)          # array parameters
    out = []
    for p in params.split(","):
        p = p.replace("*", " * ").strip()
        if not p:
            continue
        toks = p.split()
        # Drop the trailing identifier: the last token is the parameter name
        # unless the parameter is a bare array (already stripped above) or
        # an unnamed type.
        if len(toks) > 1 and re.fullmatch(r"[A-Za-z_]\w*", toks[-1]) \
                and toks[-1] not in NOISE:
            # A trailing '*' glued to the name means the name is the pointer
            # target: "char *name" -> toks ['char','*','name'].
            toks = toks[:-1]
        toks = [t for t in toks if t not in NOISE or t == "struct"]
        # "struct" alone carries no type name; keep it only when a name follows.
        cleaned = []
        for i, t in enumerate(toks):
            if t == "struct":
                continue
            cleaned.append(t)
        if cleaned:
            out.append(" ".join(cleaned))
    return out


def upstream_callbacks() -> dict[str, str]:
    """field name -> parameter list, from src/target/target_type.h.

    Function pointers are matched by their `(*name)(params)` shape.  The
    struct also carries plain data members (`.name`, `.commands`, ...); those
    are collected too so that a backend installing a field upstream does not
    have is still reported.
    """
    text = TT.read_text(encoding="utf-8", errors="replace")
    cb = {}
    for m in re.finditer(r"\(\s*\*\s*(\w+)\s*\)\s*\(([^;]*?)\)\s*;", text, re.S):
        cb[m.group(1)] = m.group(2)
    # Plain members: "type *name;" / "const struct command_registration *commands;"
    body = text
    for m in re.finditer(r"^\s*(?:const\s+)?[A-Za-z_][\w ]*?\s*\*\s*(\w+)\s*;",
                         body, re.M):
        name = m.group(1)
        cb.setdefault(name, "")
    return cb


def installed_callbacks(path: pathlib.Path) -> dict[str, str]:
    """field name -> installed function, from the backend's initializer."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"struct\s+target_type\s+\w+\s*=\s*\{(.*?)\n\};", text, re.S)
    if not m:
        return {}
    fields = {}
    for fm in re.finditer(r"^\s*\.(\w+)\s*=\s*&?(\w+)\s*,", m.group(1), re.M):
        fields[fm.group(1)] = fm.group(2)
    return fields


def definition_params(text: str, func: str) -> str | None:
    """Parameter list of `func`'s definition, or None when not in this file."""
    pat = re.compile(
        r"(?:^|\n)[ \t]*(?:static\s+|extern\s+)?[A-Za-z_][\w \t\*]*?"
        r"\b" + re.escape(func) + r"\s*\(([^;{]*?)\)\s*\{",
        re.M,
    )
    m = pat.search(text)
    return m.group(1) if m else None


def main() -> int:
    up = upstream_callbacks()
    problems = []
    checked = 0
    skipped = 0

    for name in BACKENDS:
        path = ROOT / "src" / "target" / name
        if not path.exists():
            problems.append(f"{name}: file missing")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fields = installed_callbacks(path)
        if not fields:
            problems.append(f"{name}: no struct target_type initializer found")
            continue
        for field, func in sorted(fields.items()):
            if field not in up:
                problems.append(
                    f"{name}: .{field} is not a member of upstream struct target_type"
                )
                continue
            if field in ("name", "type", "custom_halt_step_watchpoint"):
                continue
            if not func:
                continue
            params = definition_params(text, func)
            if params is None:
                # Defined in another translation unit (lakemont.c,
                # x86_32_common.c, hello.c); upstream's own header owns the
                # prototype there, so there is nothing to compare here.
                skipped += 1
                continue
            want = type_words(up[field])
            got = type_words(params)
            checked += 1
            if want != got:
                problems.append(
                    f"{name}: .{field} -> {func}\n"
                    f"      upstream: ({', '.join(want)})\n"
                    f"      backend : ({', '.join(got)})"
                )

    print(f"compared {checked} callback signatures "
          f"({skipped} defined elsewhere) across {len(BACKENDS)} backends")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for p in problems:
            print("  " + p)
        return 1
    print("no signature mismatch found")
    return 0


if __name__ == "__main__":
    sys.exit(main())

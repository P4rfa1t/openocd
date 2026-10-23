#!/usr/bin/env python3
"""Add extern declarations for the third-party adapter drivers to
src/jtag/interface.h.

WHY THIS EXISTS
---------------
src/jtag/interfaces.c only *uses* each `<name>_adapter_driver` symbol; the
declaration lives in src/jtag/interface.h, next to the 47 upstream ones.
CI run 2 (39159942812) failed with:

    interface.c:72:18: error: 'dbgagent_adapter_driver' undeclared here
    interface.c:78:18: error: 'dirtyjtag_adapter_driver' undeclared here
    interface.c:105:18: error: 'ice1000_adapter_driver' undeclared here

because the first implementation pass registered the drivers in interfaces.c
without declaring them.  Rather than weaken the build, the symbols are declared
where upstream declares its own.

The block is kept in strict ASCII-alphabetic order, matching the surrounding
list and the "Keep in alphabetic order" comment in interfaces.c.

Idempotent: entries already present are left untouched; the file is only
rewritten when something actually changes.

LINE ENDINGS
------------
This file is LF-only in the repository.  Python's default text mode applies
universal-newline translation, which turned a one-line insertion into a
438-line "rewrite every line" diff (CRLF on write-back).  All I/O below is
therefore explicitly newline="\n" so the diff stays minimal.
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
TARGET = HERE / "src" / "jtag" / "interface.h"

# Symbols verified present in the driver sources (grep 'struct adapter_driver
# <name> = {' across src/jtag/drivers/).  ice1000.c registers two adapters and
# adi_dbg_agent.c registers two, so five names cover four source files.
SYMBOLS = [
    "dbgagent_adapter_driver",
    "dirtyjtag_adapter_driver",
    "ice1000_adapter_driver",
    "ice1500_adapter_driver",
    "ice2000_adapter_driver",
    "mp_dbgagent_adapter_driver",
]

PREFIX = "extern struct adapter_driver "
SUFFIX = ";"


def sort_key(symbol: str) -> str:
    """ASCII-lower key so the list sorts like the upstream one."""
    return symbol.lower()


def main() -> int:
    # newline="" keeps line endings exactly as stored; we rewrite them
    # verbatim so an LF-only file stays LF-only.
    with open(TARGET, encoding="utf-8", newline="") as f:
        text = f.read()

    if "\r\n" in text:
        print("ERROR: interface.h has CRLF endings; expected LF-only. Aborting so "
              "the line-ending damage is not baked in.", file=sys.stderr)
        return 1

    lines = text.splitlines(keepends=True)

    # Collect every `extern struct adapter_driver X;` line that is a plain
    # single-name declaration (upstream never wraps them across lines).
    idx_of: dict[str, int] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(PREFIX) and stripped.endswith(SUFFIX):
            name = stripped[len(PREFIX):-len(SUFFIX)].strip()
            if name.isidentifier():
                idx_of[name] = i

    if not idx_of:
        print("ERROR: could not find the extern declaration block", file=sys.stderr)
        return 1

    block_start = min(idx_of.values())
    block_end = max(idx_of.values())  # inclusive

    # The upstream block must be contiguous; if it is not, editing by index
    # would scatter our lines into unrelated code.
    expected = block_end - block_start + 1
    if len(set(range(block_start, block_end + 1)) - set(idx_of.values())):
        print("ERROR: extern block is not contiguous; refusing to edit", file=sys.stderr)
        return 1
    if len(idx_of) != expected:
        print("ERROR: duplicate declaration lines; refusing to edit", file=sys.stderr)
        return 1

    added = [s for s in SYMBOLS if s not in idx_of]
    removed_stale = [s for s in idx_of if s in SYMBOLS and False]  # placeholder

    if not added and not removed_stale:
        print("interface.h: all 6 declarations already present, nothing to do")
        return 0

    # Rebuild the block from scratch in sorted order: upstream names plus ours.
    all_names = sorted(list(idx_of) + added, key=sort_key)
    indent = lines[block_start][: len(lines[block_start]) - len(lines[block_start].lstrip())]
    new_block = [f"{indent}{PREFIX}{n}{SUFFIX}\n" for n in all_names]

    new_lines = lines[:block_start] + new_block + lines[block_end + 1:]
    with open(TARGET, "w", encoding="utf-8", newline="") as f:
        f.write("".join(new_lines))

    print(f"interface.h: added {len(added)} declaration(s): {', '.join(added)}")
    print(f"interface.h: extern block now {len(all_names)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

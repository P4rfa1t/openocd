#!/usr/bin/env python3
"""AUDIT (read-only): find `source [find X]` references in tcl/ that do not
resolve to a file.

WHY THIS IS A SEPARATE TOOL
---------------------------
tools/verify_tree.py checks the overlay against manifest/PROVENANCE.json: it
asks "is every file the manifest lists still present with the recorded hash?".
That answers a provenance question, not a correctness question.  A config can
be perfectly present and still be dead because the thing it sources is missing,
and a missing file can be intentional (the user asked for it to be dropped).

This tool asks the other question: starting from every TCL file that ships,
does each reference lead somewhere?  It only reads; it never writes.

RESOLUTION RULES (mirroring OpenOCD's own `find` proc in src/helper/startup.tcl)
  * `[find a/b/c.cfg]` resolves as tcl/a/b/c.cfg
  * bare tokens and anything containing `$` are skipped: they are variables or
    command fragments, not literal paths
  * a reference may be a glob (e.g. `[find target/*.cfg]`); each glob is
    expanded
"""

from __future__ import annotations

import glob
import pathlib
import re
import sys
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent.parent
TCL = HERE / "tcl"

FIND = re.compile(r"\[find\s+([^\[\]]+)\]")
# A token that looks like a path we can resolve: contains a slash or ends in a
# config suffix, and has no interpolation in it.
LITERAL = re.compile(r"^[A-Za-z0-9_./*-]+$")


def main() -> int:
    if not TCL.is_dir():
        print("ERROR: tcl/ not found", file=sys.stderr)
        return 1

    missing: dict[str, list[str]] = defaultdict(list)   # token -> who references it
    ok_files = 0
    ok_refs = 0
    scanned: Counter[str] = Counter()

    for p in sorted(TCL.rglob("*")):
        if p.suffix not in (".cfg", ".tcl"):
            continue
        scanned[p.suffix] += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for group in FIND.findall(text):
            tokens = group.split()
            if not tokens:
                continue
            tok = tokens[0].strip()
            # Only literal path-shaped tokens; skip variables and commands.
            if not LITERAL.match(tok):
                continue
            if not ("/" in tok or tok.endswith((".cfg", ".tcl", ".txt"))):
                continue

            target = TCL / tok
            if any(c in tok for c in "*?["):
                if glob.glob(str(target)):
                    ok_refs += 1
                else:
                    missing[tok].append(p.as_posix())
                continue

            if target.is_file():
                ok_files += 1
                ok_refs += 1
            else:
                missing[tok].append(p.as_posix())

    print(f"scanned: {scanned['.cfg']} .cfg, {scanned['.tcl']} .tcl")
    print(f"resolved references: {ok_refs} ({ok_files} direct, rest glob-expanded)")
    print(f"unresolved references: {len(missing)}")

    if missing:
        print()
        for tok in sorted(missing):
            who = missing[tok]
            shown = ", ".join(sorted(who)[:3])
            more = "" if len(who) <= 3 else f" (+{len(who) - 3} more)"
            print(f"  MISSING tcl/{tok}")
            print(f"          referenced by: {shown}{more}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

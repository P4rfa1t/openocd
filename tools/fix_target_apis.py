#!/usr/bin/env python3
"""Adapt the merged third-party target backends to upstream API names.

Two mechanical renames, both verified against the current upstream headers:

  * struct breakpoint field `set`  -> `is_set`
    (src/target/breakpoints.h:33 is `bool is_set;`; there is no `set`.)

  * `tap_state_t` -> `enum tap_state`
    (upstream has no `tap_state_t` typedef at all; only `enum tap_state`,
    declared in src/jtag/interface.h.  The typedef was removed upstream, so
    any third-party file still spelling tap_state_t was written against an
    old tree.)

The script is idempotent and preserves line endings, because this repo has a
mix of LF and CRLF sources and rewriting one as the other produces a whole-file
diff (that mistake already cost a 870-line phantom diff once).
"""

import pathlib
import re
import sys

TARGETS = [
    "src/target/quark_d2000.c",
    "src/target/quark_se.c",
    "src/target/vortex86.c",
]

# `iter->set` / `iter->set = 0` but NOT `is_set` and NOT `.set_xxx`
RE_FIELD = re.compile(r"(->|\.)(?!is_set\b)set\b(?!\s*\()")
# bare type name -> enum tag
RE_TAP = re.compile(r"\btap_state_t\b")


def patch(path, old, new):
    """Apply one regex substitution, keeping the file's own line endings."""
    with open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    updated, count = old.subn(new, text)
    if count:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(updated)
    return count


def main():
    total = 0
    for rel in TARGETS:
        path = pathlib.Path(rel)
        if not path.exists():
            print(f"  skip {rel} (absent)")
            continue
        a = patch(path, RE_FIELD, r"\1is_set")
        b = patch(path, RE_TAP, "enum tap_state")
        total += a + b
        print(f"  {rel}: is_set={a} enum_tap_state={b}")
    print(f"TOTAL replacements: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

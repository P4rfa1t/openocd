#!/usr/bin/env python3
"""Check that the ported rvmax / rv32m1 sources match upstream's API.

The rvmax and rv32m1 backends were imported from two vendor forks:

    src/target/rvmax/     analogdevicesinc/openocd @ ad75bfb79b
    src/target/rv32m1/    zephyrproject-rtos/openocd @ 18de087755
    src/flash/nor/rv32m1.c  zephyrproject-rtos/openocd @ 18de087755

Both forks were written against an older OpenOCD.  The port to this tree's
upstream baseline is a fixed, small set of changes.  This script asserts
that every one of them is present and that none of the old forms survived.
It is a check, not a fixer: it never writes to the tree, so it can be run
in CI or after a re-import without any risk of clobbering a later edit.

Run it with:

    python tools/port_new_archs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (file, pattern that must NOT appear, why)
FORBIDDEN = [
    ("src/target/rvmax/encoding.h", r"\bRISCV_CSR_ENCODING_H\b",
     "collides with upstream src/target/riscv/encoding.h"),
    ("src/target/rvmax/encoding.h", r"\bRISCV_ENCODING_H\b",
     "collides with upstream src/target/riscv/encoding.h"),
    ("src/target/rvmax/gdb_regs.h", r"\bTARGET__RISCV__GDB_REGS_H\b",
     "misleading name borrowed from upstream's riscv backend"),
    ("src/target/rvmax/rvmax.c", r"\bgettimeofday\b",
     "not available on Windows; use timeval_ms()"),
    ("src/target/rvmax/rvmax.c", r"\btimeval_add_time\b",
     "removed from upstream src/helper/time_support.h"),
    ("src/target/rvmax/rvmax.c", r"\btimeval_compare\b",
     "removed from upstream src/helper/time_support.h"),
    ("src/target/rv32m1/rv32m1.c", r"\bJim_Interp\b",
     "upstream's target_type.target_create takes no interpreter"),
    ("src/target/rv32m1/rv32m1.c", r"(?<!OOCD_)\bLIST_HEAD\s*\(",
     "upstream src/helper/list.h has no bare LIST_HEAD macro"),
    ("src/target/rv32m1/rv32m1.c", r"\bgettimeofday\b",
     "not available on Windows; use timeval_ms()"),
    ("src/target/rv32m1/rv32m1.c", r"\btimeval_add_time\b",
     "removed from upstream src/helper/time_support.h"),
    ("src/flash/nor/rv32m1.c", r"^struct flash_driver rv32m1_flash",
     "upstream's driver.h declares every driver as const"),
]

# (file, pattern that must appear, why)
REQUIRED = [
    ("src/target/rvmax/encoding.h", r"\bRVMAX_CSR_ENCODING_H\b",
     "renamed guard"),
    ("src/target/rvmax/encoding.h", r"\bRVMAX_ENCODING_H\b",
     "renamed guard"),
    ("src/target/rvmax/gdb_regs.h", r"\bRVMAX_GDB_REGS_H\b",
     "renamed guard"),
    ("src/target/rvmax/opcodes.h", r"\bRVMAX_OPCODES_H\b",
     "added guard"),
    ("src/target/rvmax/rvmax.c", r"\btimeval_ms\(\)",
     "upstream's monotonic millisecond clock"),
    ("src/target/rv32m1/rv32m1.c", r"\bOOCD_LIST_HEAD\s*\(",
     "upstream's list macro"),
    ("src/target/rv32m1/rv32m1.c", r"\btimeval_ms\(\)",
     "upstream's monotonic millisecond clock"),
    ("src/flash/nor/rv32m1.c", r"\bconst struct flash_driver rv32m1_flash\b",
     "upstream's driver.h declares every driver as const"),
]

# The command names these backends register.  Upstream's or1k backend
# registers the unprefixed tap_select / du_select / addreg, and OpenOCD
# silently keeps the first registration of a command name, so an unprefixed
# second backend would be driven by the first one's handler.  Prefixing is
# what lets the three coexist.
PREFIXED_COMMANDS = {
    "src/target/rvmax/rvmax.c": [
        "rvmax_tap_select", "rvmax_tap_list",
        "rvmax_du_select", "rvmax_du_list",
        "rvmax_addreg", "rvmax_auth",
    ],
    "src/target/rv32m1/rv32m1.c": [
        "rv32m1_tap_select", "rv32m1_tap_list",
        "rv32m1_du_select", "rv32m1_du_list",
        "rv32m1_core_select",
    ],
}

# TCL configs that call those commands have to use the prefixed spelling.
TCL_CALLERS = {
    "tcl/target/rv32m1_ri5cy.cfg": ["rv32m1_tap_select", "rv32m1_du_select",
                                     "rv32m1_core_select"],
    "tcl/target/rv32m1_zero_riscy.cfg": ["rv32m1_tap_select", "rv32m1_du_select",
                                          "rv32m1_core_select"],
}


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        sys.exit("missing file: %s" % rel)
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    problems = []

    for rel, pattern, why in FORBIDDEN:
        text = read(rel)
        for m in re.finditer(pattern, text, re.M):
            line = text.count("\n", 0, m.start()) + 1
            problems.append("%s:%d: must not contain %r (%s)"
                            % (rel, line, m.group(0), why))

    for rel, pattern, why in REQUIRED:
        if not re.search(pattern, read(rel), re.M):
            problems.append("%s: must contain %r (%s)" % (rel, pattern, why))

    for rel, names in PREFIXED_COMMANDS.items():
        text = read(rel)
        for name in names:
            if not re.search(r'"%s"' % re.escape(name), text):
                problems.append("%s: does not register command %r" % (rel, name))

    for rel, names in TCL_CALLERS.items():
        text = read(rel)
        for name in names:
            if not re.search(r"^\s*%s\b" % re.escape(name), text, re.M):
                problems.append("%s: does not call %r" % (rel, name))
        # The unprefixed spellings must be gone: OpenOCD would resolve them
        # to upstream's or1k handler.
        for old in ("tap_select", "du_select", "core_select"):
            if re.search(r"^\s*%s\b" % re.escape(old), text, re.M):
                problems.append("%s: still calls the unprefixed %r" % (rel, old))

    for p in problems:
        print("problem: " + p)
    if problems:
        print("\n%d problem(s) found" % len(problems))
        return 1

    print("rvmax / rv32m1 port checks: all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

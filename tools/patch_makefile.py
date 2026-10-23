#!/usr/bin/env python3
"""Patch src/jtag/drivers/Makefile.am to add the merged third-party adapters.

Written as a file rather than a heredoc because the lines we insert end with a
literal backslash (make line continuation), which is painful to escape through
nested shell/heredoc quoting.
"""
import sys

PATH = "src/jtag/drivers/Makefile.am"
BACKSLASH = chr(92)

ADD = [
    "# Third-party adapters merged into this tree (see configure.ac).",
    "if DIRTYJTAG",
    "DRIVERFILES += %D%/dirtyjtag.c",
    "endif",
    "if ADI_ICE1000",
    "DRIVERFILES += %D%/ice1000.c",
    "endif",
    "if ADI_ICE1500",
    "DRIVERFILES += %D%/ice1500.c",
    "endif",
    "if ADI_DBGAGENT",
    "DRIVERFILES += %D%/adi_dbg_agent.c",
    "endif",
    "if ADI_USBMUX",
    "DRIVERFILES += %D%/usbmux.c",
    "endif",
]

HEADER_LINE = "\t%D%/usbmux.h " + BACKSLASH

with open(PATH, encoding="utf-8") as f:
    lines = f.read().split("\n")

# Idempotency guard: don't insert twice.
if any("DIRTYJTAG" in l for l in lines):
    print("already patched, nothing to do")
    sys.exit(0)

idx = next(i for i, l in enumerate(lines) if l.startswith("DRIVERHEADERS = "))
lines[idx:idx] = ADD

h = idx + len(ADD)
assert lines[h].startswith("DRIVERHEADERS = "), lines[h]
lines.insert(h + 1, HEADER_LINE)

with open(PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("patched", PATH)

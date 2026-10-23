#!/usr/bin/env python3
"""Stage the rvmax / rv32m1 sources into their final in-tree locations.

The upstream OpenOCD layout keeps a target architecture that needs its own
private headers in a subdirectory (src/target/riscv, src/target/openrisc, ...)
and compiles it into a per-architecture convenience library that libtarget.la
links against.  rvmax and rv32m1 follow the same shape:

    src/target/rvmax/       -> libtarget.la via librvmax.la
    src/target/rv32m1/      -> libtarget.la via librv32m1.la
    src/flash/nor/rv32m1.c  -> the NOR flash driver for the same chips

Bytes are copied verbatim; the only edits happen afterwards in a separate,
explicitly reviewable step (see tools/port_new_archs.py).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (source, destination) pairs, all relative to the repository root.
PLAN = [
    # --- rvmax: Analog Devices MAX32655/MAX32680/MAX32690/MAX78000/MAX78002 ---
    ("raw/stage-rvmax/rvmax.c", "src/target/rvmax/rvmax.c"),
    ("raw/stage-rvmax/rvmax.h", "src/target/rvmax/rvmax.h"),
    ("raw/stage-rvmax/rvmax_du.h", "src/target/rvmax/rvmax_du.h"),
    ("raw/stage-rvmax/rvmax_du_adv.c", "src/target/rvmax/rvmax_du_adv.c"),
    ("raw/stage-rvmax/rvmax_tap.h", "src/target/rvmax/rvmax_tap.h"),
    ("raw/stage-rvmax/rvmax_tap_mohor.c", "src/target/rvmax/rvmax_tap_mohor.c"),
    ("raw/stage-rvmax/encoding.h", "src/target/rvmax/encoding.h"),
    ("raw/stage-rvmax/gdb_regs.h", "src/target/rvmax/gdb_regs.h"),
    ("raw/stage-rvmax/opcodes.h", "src/target/rvmax/opcodes.h"),
    # --- rv32m1: Renesas RZ/Five + M33 (RI5CY / ZERO-RISCY) ---
    ("raw/stage-rv32m1/target/rv32m1.c", "src/target/rv32m1/rv32m1.c"),
    ("raw/stage-rv32m1/target/rv32m1.h", "src/target/rv32m1/rv32m1.h"),
    ("raw/stage-rv32m1/target/rv32m1_du.h", "src/target/rv32m1/rv32m1_du.h"),
    ("raw/stage-rv32m1/target/rv32m1_du_adv.c", "src/target/rv32m1/rv32m1_du_adv.c"),
    ("raw/stage-rv32m1/target/rv32m1_tap.h", "src/target/rv32m1/rv32m1_tap.h"),
    ("raw/stage-rv32m1/target/rv32m1_tap_mohor.c", "src/target/rv32m1/rv32m1_tap_mohor.c"),
    # --- the matching NOR flash driver ---
    ("raw/stage-rv32m1/flash/rv32m1.c", "src/flash/nor/rv32m1.c"),
]


def main() -> int:
    missing = [src for src, _ in PLAN if not (ROOT / src).is_file()]
    if missing:
        for src in missing:
            print(f"missing source: {src}", file=sys.stderr)
        return 2

    for src, dst in PLAN:
        src_path = ROOT / src
        dst_path = ROOT / dst
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_path, dst_path)
        print(f"{dst}  ({dst_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

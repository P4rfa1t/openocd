#!/usr/bin/env python3
"""Keep the ICE-1000 firmware flashing chain compiled but unused.

Dropping the unreachable get_firmware_filename() call (see fix_driver_apis.py)
left ice1000_update_firmware() with no callers.  -Wall enables
-Wunused-function and cross-build.sh adds -Werror, so an unannotated static
function breaks the build.

The function itself is a complete, working implementation (ihex image load,
per-section CDC flashing, CRC-16/CCITT verification) and is the only way to
update the probe's firmware from OpenOCD, so it is kept and marked
__attribute__((unused)) rather than deleted.  Annotating it also keeps the
three helpers it calls (ice1000_send_flash_data, ice1000_firmware_crc,
crc16_ccitt) considered as referenced, so they need no annotation of their own.
"""
import sys

PATH = "src/jtag/drivers/ice1000.c"
OLD = "static int ice1000_update_firmware(const char *filename)\n{"
NEW = "static int __attribute__((unused)) ice1000_update_firmware(const char *filename)\n{"

with open(PATH, encoding="utf-8") as f:
    s = f.read()

if NEW in s:
    print("already patched")
    sys.exit(0)

n = s.count(OLD)
if n != 1:
    sys.exit(f"expected 1 occurrence, found {n}")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(s.replace(OLD, NEW))
print("patched", PATH)

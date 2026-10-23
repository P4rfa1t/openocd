#!/usr/bin/env python3
"""Give usbmux_create_header internal linkage.

usbmux.c defines it without `static` and usbmux.h does not declare it, yet it
is only ever called from within usbmux.c.  Leaving it external pollutes the
link namespace and would break a build that turns on -Wmissing-prototypes.
"""
PATH = "src/jtag/drivers/usbmux.c"

OLD = "void usbmux_create_header(uint8_t *header,"
NEW = "static void usbmux_create_header(uint8_t *header,"

with open(PATH, encoding="utf-8") as f:
    s = f.read()

if NEW in s:
    print("already patched")
    raise SystemExit(0)

if s.count(OLD) != 1:
    raise SystemExit(f"expected 1 occurrence, found {s.count(OLD)}")

s = s.replace(OLD, NEW)
with open(PATH, "w", encoding="utf-8") as f:
    f.write(s)
print("patched", PATH)

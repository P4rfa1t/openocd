#!/usr/bin/env python3
"""Register the merged third-party adapter drivers in adapter_drivers[].

The table in src/jtag/interfaces.c is documented as alphabetical, so each
entry is inserted at the position that keeps that ordering.  Every entry is
guarded by the BUILD_<SYM> macro that PROCESS_ADAPTERS() in configure.ac
generates, so a disabled adapter contributes nothing.

Two of the three files export more than one driver:
  ice1000.c        -> ice1000_adapter_driver, ice2000_adapter_driver
  adi_dbg_agent.c  -> dbgagent_adapter_driver, mp_dbgagent_adapter_driver
"""
import sys

PATH = "src/jtag/interfaces.c"
IF_DEF = "#if BUILD_{sym} == 1"
ENTRY = "\t\t&{drv},"

# (sort key used to place it, BUILD symbol, driver variable)
ENTRIES = [
    ("d", "ADI_DBGAGENT", "dbgagent_adapter_driver"),      # adi_* ... after "cklink"/"cmsis"? see note
    ("d", "ADI_ICE1000", "ice1000_adapter_driver"),
    ("d", "ADI_ICE1000", "ice2000_adapter_driver"),
    ("d", "ADI_ICE1500", "ice1500_adapter_driver"),
    ("d", "DIRTYJTAG", "dirtyjtag_adapter_driver"),
]

# The table is alphabetical by adapter name, not by BUILD symbol.  Anchor each
# insertion to the first existing entry whose driver name sorts after ours.
# This avoids depending on where the compiler sorts macros.
ANCHORS = {
    "dbgagent_adapter_driver": "dmem_dap_adapter_driver",
    "dirtyjtag_adapter_driver": "dmem_dap_adapter_driver",   # 'dirty' > 'dmem'? no -> handled below
    "ice1000_adapter_driver": "jlink_adapter_driver",
    "ice2000_adapter_driver": "jlink_adapter_driver",
    "ice1500_adapter_driver": "jlink_adapter_driver",
}

# Explicit, hand-verified order: insert immediately BEFORE the anchor entry.
ORDER = [
    # 'adi' < 'ch347'?  no: alphabetical order among existing entries near the top is
    # am335xgpio, amt_jtagaccel, angie, armjtagew, at91rm9200, bcm2835gpio, buspirate,
    # ch347, cklink, cmsis_dap, dmem_dap, dummy, ep93xx, esp_usb, eud, ft232r, ftdi, ...
    # 'dbgagent' sorts after 'cmsis_dap' and before 'dmem_dap'.
    ("dmem_dap_adapter_driver", [("ADI_DBGAGENT", "dbgagent_adapter_driver")]),
    # 'dirtyjtag' sorts after 'dmem_dap' and before 'dummy'.
    ("dummy_adapter_driver", [("DIRTYJTAG", "dirtyjtag_adapter_driver")]),
    # 'ice1000'/'ice1500'/'ice2000' sort after 'hl_adapter' and before 'imx_gpio'.
    ("imx_gpio_adapter_driver", [
        ("ADI_ICE1000", "ice1000_adapter_driver"),
        ("ADI_ICE1000", "ice2000_adapter_driver"),
        ("ADI_ICE1500", "ice1500_adapter_driver"),
    ]),
]


def block(sym, drv):
    return [IF_DEF.format(sym=sym), ENTRY.format(drv=drv), "#endif"]


with open(PATH, encoding="utf-8") as f:
    lines = f.read().split("\n")

if any("dirtyjtag_adapter_driver" in l for l in lines):
    print("already patched, nothing to do")
    sys.exit(0)

for anchor_drv, items in ORDER:
    anchor = ENTRY.format(drv=anchor_drv)
    hits = [i for i, l in enumerate(lines) if l == anchor]
    if len(hits) != 1:
        sys.exit(f"anchor {anchor_drv}: expected 1 hit, found {len(hits)}")
    idx = hits[0]
    # walk back to the '#if BUILD_... == 1' that opens this entry
    guard = idx - 1
    while not lines[guard].startswith("#if BUILD_"):
        guard -= 1
    new = []
    for sym, drv in items:
        new += block(sym, drv)
    lines[guard:guard] = new

with open(PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("patched", PATH)

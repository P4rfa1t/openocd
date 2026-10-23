#!/usr/bin/env python3
"""Carry the merged third-party drivers across API drift in upstream OpenOCD.

Three independent fixes, each tied to a concrete build failure seen on the
GitHub Actions Windows job:

1. dirtyjtag.c defines `static int min(int, int)`.  On MinGW, <windows.h>
   (pulled in via src/helper/system.h -> winsock2.h -> windows.h) has already
   defined `min` as a function-like macro in windef.h, so the definition is
   rewritten by the preprocessor into nonsense.  Renaming the helper is safer
   than #undef min, which would also change the meaning of any later use of the
   macro inside this translation unit.

2. ice1000.c called get_firmware_filename(), which does not exist anywhere in
   this tree -- it was a private helper of the fork that never got copied over,
   and the fork registers no command that could supply such a filename, so the
   firmware-update path was unreachable dead code.  The call and its block are
   removed; a comment records what was there.

3. struct swd_driver in src/jtag/swd.h declares read_reg/write_reg as returning
   int (they used to return void).  ice1000's implementations already compute
   the queue result and then throw it away; propagating it is both what the
   current API wants and more correct.
"""
import sys

MIN_OLD = "static int min(int a, int b)"
MIN_NEW = "static int djt_min(int a, int b)"

SWD_DECLS = {
    "static void ice1000_swd_write_reg(uint8_t cmd, uint32_t value, uint32_t ap_delay_clk);":
        "static int ice1000_swd_write_reg(uint8_t cmd, uint32_t value, uint32_t ap_delay_clk);",
    "static void ice1000_swd_read_reg(uint8_t cmd, uint32_t *value, uint32_t ap_delay_clk);":
        "static int ice1000_swd_read_reg(uint8_t cmd, uint32_t *value, uint32_t ap_delay_clk);",
    "static void ice1000_swd_write_reg(uint8_t cmd, uint32_t value, uint32_t ap_delay_clk)\n{":
        "static int ice1000_swd_write_reg(uint8_t cmd, uint32_t value, uint32_t ap_delay_clk)\n{",
    "static void ice1000_swd_read_reg(uint8_t cmd, uint32_t *value, uint32_t ap_delay_clk)\n{":
        "static int ice1000_swd_read_reg(uint8_t cmd, uint32_t *value, uint32_t ap_delay_clk)\n{",
}

# The two bodies are otherwise identical in shape: log a message, fall through.
SWD_BODY_OLD = """	if (retval != ERROR_OK)
		LOG_ERROR("%s SWD {} register failed", adi_cable_name());
}}"""
SWD_BODY_NEW = """	if (retval != ERROR_OK)
		LOG_ERROR("%s SWD {} register failed", adi_cable_name());

	return retval;
}}"""

FW_OLD = "\tchar *firmware_filename = get_firmware_filename();\n"
FW_NEW = ""

FW_BLOCK_OLD = """	if (firmware_filename) {
		ret = ice1000_update_firmware(firmware_filename);
		if (ret == ERROR_OK)
			LOG_INFO("The firmware has been updated successfully. "
					 "Please unplug the %s cable and reconnect it to finish the update process.",
					 cable_name);
		else
			LOG_ERROR("The firmware failed to update.");
		return ERROR_JTAG_INIT_FAILED;
	}

"""
FW_BLOCK_NEW = """	/*
	 * The fork this driver came from called a private get_firmware_filename()
	 * here to flash the probe on connect.  Neither that helper nor a command to
	 * name the file exists in this tree, so the path was unreachable and has
	 * been dropped.  To bring it back, resolve the file with
	 * find_file() from helper/configuration.h and call
	 * ice1000_update_firmware(), which is still present.
	 */

"""


def edit(path, pairs, required=True):
    with open(path, encoding="utf-8") as f:
        s = f.read()
    before = s
    for old, new in pairs:
        if new and new in s and old not in s:
            continue  # already applied
        n = s.count(old)
        if n != 1:
            if required:
                sys.exit(f"{path}: expected 1 occurrence of {old[:60]!r}, found {n}")
            continue
        s = s.replace(old, new)
    if s == before:
        print(f"  {path}: nothing changed")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)
    print(f"  {path}: patched")


print("1) dirtyjtag: rename min()")
edit("src/jtag/drivers/dirtyjtag.c", [
    (MIN_OLD, MIN_NEW),
    ("command[2] = min(255, num_cycles);", "command[2] = djt_min(255, num_cycles);"),
    ("num_cycles -= min(255, num_cycles);", "num_cycles -= djt_min(255, num_cycles);"),
    ("sent_bits = min(240, scan_size);", "sent_bits = djt_min(240, scan_size);"),
])

print("2) ice1000: swd_reg return type void -> int")
edit("src/jtag/drivers/ice1000.c", [(o, n) for o, n in SWD_DECLS.items()])
edit("src/jtag/drivers/ice1000.c", [
    (SWD_BODY_OLD.format("write"), SWD_BODY_NEW.format("write")),
    (SWD_BODY_OLD.format("read"), SWD_BODY_NEW.format("read")),
])

print("3) ice1000: drop unreachable firmware-update path")
edit("src/jtag/drivers/ice1000.c", [
    (FW_OLD, FW_NEW),
    (FW_BLOCK_OLD, FW_BLOCK_NEW),
])

print("done")

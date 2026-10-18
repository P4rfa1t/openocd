#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Wire the third-party target architecture groups into the build.

Upstream keeps every architecture in one `libtarget.la`; a group is just a
variable appended to %C%_libtarget_la_SOURCES.  Each architecture also has to
appear in `target_types[]` in src/target/target.c, because `target create`
looks the name up there -- a source file that compiles but is not in that table
is unreachable from TCL.

Only groups that passed a symbol-conflict scan are listed here.  The ARC fork
(arc32.c and friends) is deliberately absent: it redefines `arcv2_target`,
which upstream arc.c already provides.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# group name -> (source files, target_type symbols, trigger macro)
# The trigger macro comes from configure.ac so a group can be switched off at
# configure time; TARGETS_ALL is always 1, so it is only a readability aid.
GROUPS = [
    ("C28X",      ["c28x.c"],                                    ["c28x_target"],
     "TARGETS_ALL"),
    ("TMS320",    ["tms320.c"],                                  ["tms320_target"],
     "TARGETS_ALL"),
    ("HEXAGON",   ["hexagon.c"],                                 ["hexagon_target"],
     "TARGETS_ALL"),
    ("QUARK",     ["quark_d2000.c", "quark_se.c"],
     ["quark_d2000_target", "quark_se_target"],                  "TARGETS_ALL"),
    ("VORTEX86",  ["vortex86.c"],                                ["vortex86_target"],
     "TARGETS_ALL"),
    ("OR1K_JTAG", ["or1k_jtag.c", "or1k_jtag_adv.c"],             [],
     "TARGETS_ALL"),
    ("LOONGARCH", ["loongarch.c", "loongarch_ejtag.c", "loongarch_pracc.c"],
     ["loongarch_target"],                                       "TARGETS_ALL"),
    ("MCHP_RI4",  ["mchp_ri4_bridge.c", "mchp_ri4_native.c"],
     ["mchp_ri4_bridge_target"],                                 "TARGETS_ALL"),
    ("VEXRISCV",  ["vexriscv.c"],                                ["vexriscv_target"],
     "TARGETS_ALL"),
]

# Headers that have to be listed so `make dist` ships them.
HEADERS = [
    "c28x.h", "tms320.h", "hexagon.h", "lakemont.h", "quark_d2000.h",
    "quark_se.h", "x86_32_common.h", "vortex86.h", "or1k_jtag.h",
    "or1k_jtag_adv.h", "loongarch.h", "loongarch_ejtag.h", "loongarch_pracc.h",
    "loongarch_modules.h", "mchp_ri4_bridge.h", "mchp_ri4_native.h",
    "vexriscv.h",
]

BEGIN = "# --- third-party target architectures (tools/patch_target_groups.py) ---"
END = "# --- end third-party target architectures ---"


def read_lf(path):
    """Read as text, remembering the dominant line ending.

    The tree is mixed: most C sources are LF but configure.ac and some
    autotools inputs are CRLF.  Rewriting either one in the other style
    produces a whole-file diff, so we echo back whatever the file already
    used and leave the rest of its bytes alone.
    """
    raw = path.read_bytes()
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    eol = "\r\n" if crlf > lf else "\n"
    text = raw.replace(b"\r\n", b"\n").decode()
    return text, eol


def write_lf(path, text, eol):
    if eol != "\n":
        text = text.replace("\n", eol)
    path.write_bytes(text.encode())


def patch_makefile():
    path = ROOT / "src/target/Makefile.am"
    text, eol = read_lf(path)

    # Drop a previous run so the script stays idempotent.
    text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n", "",
                  text, flags=re.S)

    src = [BEGIN, ""]
    for name, files, _syms, macro in GROUPS:
        var = f"{name}_SRC"
        src.append(f"{var} = \\")
        for i, f in enumerate(files):
            sep = " \\" if i < len(files) - 1 else ""
            src.append(f"\t%D%/{f}{sep}")
        src.append("")
        src.append(f"%C%_libtarget_la_SOURCES += $({var})")
        src.append("")
    src.append("# Headers, so `make dist` ships them.")
    src.append("%C%_libtarget_la_SOURCES += \\")
    for i, h in enumerate(HEADERS):
        sep = " \\" if i < len(HEADERS) - 1 else ""
        src.append(f"\t%D%/{h}{sep}")
    src.append("")
    src.append(END)
    src.append("")

    block = "\n".join(src)

    # Append at the very end: automake does not care where the += lives, and
    # the tail of the file is the least likely place for an upstream merge
    # conflict to land.
    if not text.endswith("\n"):
        text += "\n"
    write_lf(path, text + block, eol)

    # The sources are added through +=, so they must not appear twice.
    for _name, files, _syms, _macro in GROUPS:
        for f in files:
            hits = re.findall(rf"^\s*%D%/{re.escape(f)}\s*\\?$", text, re.M)
            if hits:
                sys.exit(f"{f} is already listed in src/target/Makefile.am")
    print("  src/target/Makefile.am  patched")


def patch_target_c():
    path = ROOT / "src/target/target.c"
    text, eol = read_lf(path)

    if BEGIN in text:
        text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n", "",
                      text, flags=re.S)

    syms = []
    for name, _files, tsyms, macro in GROUPS:
        for s in tsyms:
            syms.append((s, macro))

    lines = [BEGIN, "#if BUILD_TARGETS_ALL == 1"]
    for s, macro in syms:
        lines.append(f"\t&{s},")
    lines.append("#endif")
    lines.append(END)
    lines.append("")
    block = "\n".join(lines)

    # Insert inside target_types[] rather than appending a second list: the
    # array is what `target create` consults.  Put the entries before the
    # closing brace so the existing alphabetic body stays untouched.
    m = re.search(r"(static struct target_type \*target_types\[\] = \{\n)(.*?)(\n\};)",
                  text, re.S)
    if not m:
        sys.exit("could not find target_types[] in src/target/target.c")
    text = text[:m.end(2)] + "\n" + block + text[m.end(2):]

    write_lf(path, text, eol)
    print(f"  src/target/target.c      {len(syms)} target types registered")


def patch_configure():
    path = ROOT / "configure.ac"
    text, eol = read_lf(path)

    if "AC_DEFINE([BUILD_TARGETS_ALL]" in text:
        print("  configure.ac             already patched")
        return

    anchor = "AC_DEFINE([BUILD_]ADAPTER_SYM([adapter_driver]), [1],"
    if anchor not in text:
        sys.exit("could not find the AC_DEFINE anchor block in configure.ac")

    # One switch for the whole set.  BUILD_TARGETS_ALL has to be defined in
    # both branches: the guards in target.c are `#if BUILD_TARGETS_ALL == 1`,
    # and an undefined macro evaluates to 0, which would silently drop every
    # new architecture instead of failing loudly.
    block = (
        "AC_ARG_ENABLE([third-party-targets],\n"
        "  AS_HELP_STRING([--disable-third-party-targets],\n"
        "    [do not build the merged third-party target architectures]),\n"
        "  [enable_third_party_targets=$enableval],\n"
        "  [enable_third_party_targets=yes])\n"
        "\n"
        "AS_IF([test \"x$enable_third_party_targets\" = xyes], [\n"
        "\tAC_DEFINE([BUILD_TARGETS_ALL], [1],\n"
        "\t\t[build the merged third-party target architectures])\n"
        "], [\n"
        "\tAC_DEFINE([BUILD_TARGETS_ALL], [0],\n"
        "\t\t[build the merged third-party target architectures])\n"
        "])\n"
        "AM_CONDITIONAL([TARGETS_ALL], [test \"x$enable_third_party_targets\" = xyes])\n"
        "\n"
    )
    text = text.replace(anchor, block + anchor, 1)
    write_lf(path, text, eol)
    print("  configure.ac             --disable-third-party-targets added")


def patch_or1k_include():
    """Point the flat or1k_jtag*.c at the openrisc/ subdirectory.

    Upstream moved the OpenRISC core into src/target/openrisc/, and GCC only
    auto-searches the *including file's* directory for "..." includes.  The
    fork sources still sit at src/target/ and still say #include "or1k.h", so
    the compiler would not find openrisc/or1k.h.
    """
    fixed = 0
    for name in ("or1k_jtag.c", "or1k_jtag_adv.c"):
        path = ROOT / "src/target" / name
        if not path.exists():
            continue
        text, eol = read_lf(path)
        new = text.replace('#include "or1k.h"', '#include "openrisc/or1k.h"')
        if new != text:
            write_lf(path, new, eol)
            fixed += 1
    print(f"  src/target/or1k_jtag*.c  {fixed} include(s) repointed")


def main():
    if not (ROOT / "src/target/Makefile.am").exists():
        sys.exit("run me from inside the openocd checkout")

    print("wiring third-party target architectures:")
    patch_configure()
    patch_makefile()
    patch_target_c()
    patch_or1k_include()
    print("done -- run ./bootstrap && ./configure next")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Wire the third-party target architecture groups into the build.

Upstream keeps every architecture in one `libtarget.la`; a group is just a
variable appended to %C%_libtarget_la_SOURCES.  Each architecture also has to
appear in `target_types[]` in src/target/target.c, because `target create`
looks the name up there -- a source file that compiles but is not in that table
is unreachable from TCL.

Only groups that passed a real compile are listed here.

Two groups were dropped after they failed that compile, and they are recorded
here so nobody re-adds them by hand:

  * HEXAGON   -- calls enable_dbg_sys_pwr(), which exists nowhere in the tree,
                 and dap_get_debugbase(), which is `static` in arm_adi_v5.c.
  * OR1K_JTAG -- the fork defines its own `struct or1k_jtag`, but upstream
                 openrisc/or1k.h already defines a *different* struct with that
                 exact name; the two cannot coexist in one link unit.
  * ARC       -- redefines `arcv2_target`, which upstream arc.c already provides.

This script is the single source of truth for that wiring: it owns the
configure switches, the automake source list and the target_types[] table,
and it is idempotent, so it can be re-run after a rebase without piling up
duplicate blocks.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# One entry per merged architecture group:
#
#   name      prefix of the automake source variable
#   files     sources compiled into libtarget.la
#   symbols   target_type symbols the group exports
#   c_guard   C condition that has to hold for the group to be referenced
#              from target.c.  It is a *macro comparison*, not #ifdef, so the
#              macro has to be defined in both branches of configure.ac.
#   mk_guard  automake conditional that has to hold for the sources to be
#              compiled at all (None -> always, inside the TARGETS_ALL block)
#   cppflags  extra CPPFLAGS the group needs
#   libadd    extra LIBADD the group needs
GROUPS = [
    {
        "name": "C28X",
        "files": ["c28x.c"],
        "symbols": ["c28x_target"],
        "c_guard": "BUILD_TARGETS_ALL == 1",
        "mk_guard": None,
    },
    {
        "name": "TMS320",
        "files": ["tms320.c"],
        "symbols": ["tms320_target"],
        "c_guard": "BUILD_TARGETS_ALL == 1",
        "mk_guard": None,
    },
    {
        "name": "QUARK",
        "files": ["quark_d2000.c", "quark_se.c"],
        "symbols": ["quark_d2000_target", "quark_se_target"],
        "c_guard": "BUILD_TARGETS_ALL == 1",
        "mk_guard": None,
    },
    {
        "name": "VORTEX86",
        "files": ["vortex86.c"],
        "symbols": ["vortex86_target"],
        "c_guard": "BUILD_TARGETS_ALL == 1",
        "mk_guard": None,
    },
    {
        "name": "LOONGARCH",
        "files": ["loongarch.c", "loongarch_ejtag.c", "loongarch_pracc.c"],
        "symbols": ["loongarch_target"],
        "c_guard": "BUILD_TARGETS_ALL == 1",
        "mk_guard": None,
    },
    {
        # The RI4 bridge speaks to the probe over raw USB, so the whole group
        # needs libusb-1.x.  Upstream allows a build without libusb, hence the
        # dedicated BUILD_MCHP_RI4 guard instead of BUILD_TARGETS_ALL.
        "name": "MCHP_RI4",
        "files": ["mchp_ri4_bridge.c", "mchp_ri4_native.c"],
        "symbols": ["mchp_ri4_bridge_target"],
        "c_guard": "BUILD_MCHP_RI4 == 1",
        "mk_guard": "USE_LIBUSB1",
        "cppflags": ["$(LIBUSB1_CFLAGS)"],
        "libadd": ["$(LIBUSB1_LIBS)"],
    },
    {
        # VexRiscv parses a YAML blob with libyaml, so the target needs the
        # library at compile *and* link time.  Without it the target is simply
        # not built, hence the dedicated BUILD_VEXRISCV guard.
        "name": "VEXRISCV",
        "files": ["vexriscv.c"],
        "symbols": ["vexriscv_target"],
        "c_guard": "BUILD_VEXRISCV == 1",
        "mk_guard": "HAVE_LIBYAML",
        "cppflags": ["$(LIBYAML_CFLAGS)"],
        "libadd": ["$(LIBYAML_LIBS)"],
    },
]

# Headers that no single source file owns, so the "same basename" rule cannot
# find them.  Everything else is derived from the group list.  Note that
# lakemont.h and x86_32_common.h are *not* here: upstream src/target already
# lists them, and listing them twice makes automake complain about a
# duplicate source.
EXTRA_HEADERS = ["loongarch_modules.h", "vexriscv-csrs.h"]


def all_headers():
    seen = []
    for g in GROUPS:
        for f in g["files"]:
            h = f.rsplit(".", 1)[0] + ".h"
            if h not in seen:
                seen.append(h)
    for h in EXTRA_HEADERS:
        if h not in seen:
            seen.append(h)
    return sorted(seen)


HEADERS = all_headers()


def guards_in_order():
    """Group the symbols by C guard, keeping the declaration order."""
    order = []
    buckets = {}
    for g in GROUPS:
        guard = g["c_guard"]
        if guard not in buckets:
            buckets[guard] = []
            order.append(guard)
        for s in g["symbols"]:
            if s not in buckets[guard]:
                buckets[guard].append(s)
    return [(guard, buckets[guard]) for guard in order]


# target.c is C and Makefile.am is automake, and they disagree about what a
# comment looks like: /* */ inside a Makefile.am is a syntax error, and
# "# ---" inside C is a stray preprocessing directive.  Keep both spellings.
BEGIN_C = "/* --- third-party target architectures (tools/patch_target_groups.py) --- */"
END_C = "/* --- end third-party target architectures --- */"
BEGIN_MK = "# --- third-party target architectures (tools/patch_target_groups.py) ---"
END_MK = "# --- end third-party target architectures ---"

# configure.ac uses # comments too, so the automake markers above would be
# ambiguous.  Distinct text, and note that END_AC must not be a substring of
# anything the script writes.
BEGIN_AC = "# --- third-party targets: configure switches (tools/patch_target_groups.py) ---"
END_AC = "# --- third-party targets: end of configure switches ---"

# The m4 macro whose body must never contain one of our blocks.
MACRO_HEAD = "m4_define([PROCESS_ADAPTERS], ["
# The macro is closed by a "])" in column one, but the block that used to be
# pasted into the body also ends a line with "])" (the AS_IF that guards
# BUILD_TARGETS_ALL), so a plain text.find() stops in the middle of the body.
# The real end is the last column-one "])" before the macro is called.
MACRO_CALL = "PROCESS_ADAPTERS([USB1_ADAPTERS],"


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


# The PROCESS_ADAPTERS macro body, verbatim from upstream.  An early version
# of this script pasted the third-party configure switches into that body:
# the anchor it used ("AC_DEFINE([BUILD_]ADAPTER_SYM([adapter_driver]), [1],")
# also occurs *inside* the macro, so the block was expanded once per adapter
# and automake died with "conditional TARGETS_ALL was already defined".
# Repairing that by deleting the offending lines one by one kept leaving
# the surrounding indentation damaged, so the body is now restored
# wholesale from this constant: the file ends up either byte-identical to
# upstream or exactly this text.
UPSTREAM_MACRO_BODY = """m4_define([PROCESS_ADAPTERS], [
  m4_foreach([adapter_driver], [$1], [
	AS_IF([test $2], [
		AS_IF([test "x$ADAPTER_VAR([adapter_driver])" != "xno"], [
			AC_DEFINE([BUILD_]ADAPTER_SYM([adapter_driver]), [1],
			          [1 if you want the ]ADAPTER_DESC([adapter_driver]).)
		], [
			AC_DEFINE([BUILD_]ADAPTER_SYM([adapter_driver]), [0],
			          [0 if you do not want the ]ADAPTER_DESC([adapter_driver]).)
		])
	], [
		AS_IF([test "x$ADAPTER_VAR([adapter_driver])" = "xyes"], [
			AC_MSG_ERROR([$3 is required for [adapter_driver] "ADAPTER_DESC([adapter_driver])".])
		])
		ADAPTER_VAR([adapter_driver])=no
		AC_DEFINE([BUILD_]ADAPTER_SYM([adapter_driver]), [0],
                  [0 if you do not want the ]ADAPTER_DESC([adapter_driver]).)
	])
	AM_CONDITIONAL(ADAPTER_SYM([adapter_driver]), [test "x$ADAPTER_VAR([adapter_driver])" != "xno"])
  ])
])"""


def macro_body_span(text):
    """Locate the PROCESS_ADAPTERS macro body in *text*.

    Returns (start, end) so that text[start:end] is exactly the macro
    body, or None when the macro is not there.  The macro's own closing
    "])" is in column one -- but so is the closing bracket of every AS_IF
    that was ever pasted into the body, so the "first column-one ])" rule
    only holds once the body is clean.  The two broken shapes are detected
    explicitly instead.
    """
    start = text.find(MACRO_HEAD)
    if start < 0:
        return None

    first_close = text.find("\n])", start)
    if first_close < 0:
        return None
    first_close += len("\n])")

    # A marked block that ended up inside the body.
    blk = text.find(BEGIN_AC, start)
    if 0 <= blk < first_close:
        blk_end = text.find(END_AC, blk)
        if blk_end >= 0:
            blk_end += len(END_AC)
            close = text.find("\n])", blk_end)
            if close >= 0:
                return start, close + len("\n])")
        return start, first_close

    # The legacy unmarked block.
    legacy = text.find("AC_ARG_ENABLE([third-party-targets]", start)
    if 0 <= legacy < first_close:
        marker = text.find("AM_CONDITIONAL([TARGETS_ALL]", legacy)
        if marker >= 0:
            marker = text.find("\n", marker) + 1
            close = text.find("\n])", marker)
            if close >= 0:
                return start, close + len("\n])")
        return start, first_close

    return start, first_close


def restore_macro_body(text):
    """Put the upstream macro body back, verbatim.

    Our block must never live inside that body: it would be expanded once
    per adapter.  Restoring the body from the constant above also repairs
    the indentation damage the earlier line-by-line repair left behind.
    """
    span = macro_body_span(text)
    if span is None:
        return text
    start, end = span
    if text[start:end] == UPSTREAM_MACRO_BODY:
        return text
    return text[:start] + UPSTREAM_MACRO_BODY + text[end:]


def patch_makefile():
    path = ROOT / "src/target/Makefile.am"
    text, eol = read_lf(path)

    # Drop a previous run so the script stays idempotent.
    text = re.sub(re.escape(BEGIN_MK) + r".*?" + re.escape(END_MK) + r"\n", "",
                  text, flags=re.S)

    src = [BEGIN_MK, ""]

    # The whole block sits behind the configure switch, so that
    # --disable-third-party-targets really keeps the sources out of the build.
    src.append("if TARGETS_ALL")
    src.append("")

    for g in GROUPS:
        var = "%s_SRC" % g["name"]
        guarded = g["mk_guard"]
        if guarded:
            src.append("if %s" % guarded)
        src.append("%s = \\" % var)
        files = g["files"]
        for i, f in enumerate(files):
            sep = " \\" if i < len(files) - 1 else ""
            src.append("\t%%D%%/%s%s" % (f, sep))
        src.append("")
        src.append("%%C%%_libtarget_la_SOURCES += $(%s)" % var)
        src.append("")
        for flag in g.get("cppflags", []):
            src.append("%%C%%_libtarget_la_CPPFLAGS += %s" % flag)
        for lib in g.get("libadd", []):
            src.append("%%C%%_libtarget_la_LIBADD += %s" % lib)
        if g.get("cppflags") or g.get("libadd"):
            src.append("")
        if guarded:
            src.append("endif")
            src.append("")

    # zlib is only used by the RI4 script loader, which unpacks a .gz probe
    # firmware catalogue.  It is a soft dependency: without it the loader
    # reports that it cannot read the file.
    src.append("if HAVE_ZLIB")
    src.append("%C%_libtarget_la_CPPFLAGS += $(ZLIB_CFLAGS)")
    src.append("%C%_libtarget_la_LIBADD += $(ZLIB_LIBS)")
    src.append("endif")
    src.append("")

    src.append("# Headers, so `make dist` ships them.")
    src.append("%C%_libtarget_la_SOURCES += \\")
    for i, h in enumerate(HEADERS):
        sep = " \\" if i < len(HEADERS) - 1 else ""
        src.append("\t%%D%%/%s%s" % (h, sep))
    src.append("")

    src.append("endif")
    src.append("")
    src.append(END_MK)
    src.append("")

    block = "\n".join(src)

    # Append at the very end: automake does not care where the += lives, and
    # the tail of the file is the least likely place for an upstream merge
    # conflict to land.
    if not text.endswith("\n"):
        text += "\n"
    final = text + block
    write_lf(path, final, eol)

    # The sources are added through +=, so they must not appear twice.
    for g in GROUPS:
        for f in g["files"]:
            hits = re.findall(r"^\s*%%D%%/%s\s*\\?$" % re.escape(f), final, re.M)
            if len(hits) > 1:
                sys.exit("%s is listed %d times in src/target/Makefile.am"
                         % (f, len(hits)))

    # The same is true for the headers.  Upstream already lists lakemont.h
    # and x86_32_common.h, so a stale copy of this list would make automake
    # fail with "duplicate source" -- catch it here instead.
    for h in HEADERS:
        hits = re.findall(r"^\s*%%D%%/%s\s*\\?$" % re.escape(h), final, re.M)
        if len(hits) > 1:
            sys.exit("%s is listed %d times in src/target/Makefile.am"
                     % (h, len(hits)))

    print("  src/target/Makefile.am  patched")


def patch_target_c():
    path = ROOT / "src/target/target.c"
    text, eol = read_lf(path)

    # Remove the previous run *and* the blank line it left behind: each
    # insert adds one empty line, so repeated runs piled them up.
    if BEGIN_C in text:
        text = re.sub(r"\n*" + re.escape(BEGIN_C) + r".*?" + re.escape(END_C)
                      + r"\n*", "\n\n", text, flags=re.S)

    groups = guards_in_order()

    # target.c has no declaration of its own for these; upstream declares the
    # built-in ones in target_type.h.  Without an extern the compiler treats
    # each `&foo_target` as an undeclared identifier.
    decl = [BEGIN_C]
    for guard, syms in groups:
        decl.append("#if %s" % guard)
        for s in syms:
            decl.append("extern struct target_type %s;" % s)
        decl.append("#endif")
    decl.append(END_C)
    decl.append("")
    decl_block = "\n".join(decl)

    # target_types[] is what `target create` consults, so the entries have to
    # go into that array rather than into a second list.  The entries are
    # put before the closing brace so the existing alphabetic body stays
    # untouched.
    arr = [BEGIN_C]
    for guard, syms in groups:
        arr.append("#if %s" % guard)
        for s in syms:
            arr.append("\t&%s," % s)
        arr.append("#endif")
    arr.append(END_C)
    arr.append("")
    block = "\n".join(arr)

    marker = "static struct target_type *target_types[] = {"
    if marker not in text:
        sys.exit("could not find target_types[] in src/target/target.c")

    # The cleanup above only clears blocks that follow the marker, so the
    # declarations in front of it survive; re-insert them only when gone.
    if BEGIN_C not in text[:text.index(marker)]:
        # decl_block already ends with a newline; one more keeps the list a
        # single blank line away from the array.
        text = text.replace(marker, decl_block + "\n" + marker, 1)

    m = re.search(r"(static struct target_type \*target_types\[\] = \{\n)(.*?)(\n\};)",
                  text, re.S)
    if not m:
        sys.exit("could not find target_types[] in src/target/target.c")
    # m.end(2) sits right after the last array entry; collapse the blank
    # line before "};" so this does not stack a new one every run.
    head = text[:m.end(2)].rstrip("\n")
    tail = text[m.end(2):]
    while tail.startswith("\n"):
        tail = tail[1:]
    text = head + "\n" + block.rstrip("\n") + "\n\n" + tail

    write_lf(path, text, eol)
    count = sum(len(s) for _g, s in groups)
    print("  src/target/target.c      %d target types registered" % count)


def patch_configure():
    path = ROOT / "configure.ac"
    text, eol = read_lf(path)

    # Our block must never live inside the m4 body: it would be expanded
    # once per adapter.
    text = restore_macro_body(text)

    # The block must sit at top level, *after* the PROCESS_ADAPTERS macro is
    # closed and after the PKG_CHECK_MODULES probes it wants to follow.
    anchor = "PROCESS_ADAPTERS([USB1_ADAPTERS],"
    if anchor not in text:
        sys.exit("could not find the PROCESS_ADAPTERS call list in configure.ac")

    # Idempotency: everything the script owns lives between two marker
    # comments, so a re-run deletes exactly its own block and nothing else.
    if BEGIN_AC in text:
        i = text.index(BEGIN_AC)
        j = text.index(END_AC) + len(END_AC)
        while text[j:j + 1] == "\n":
            j += 1
        text = text[:i] + text[j:]

    block = "\n".join([
        BEGIN_AC,
        "# One switch for the whole merged set.  BUILD_TARGETS_ALL has to be",
        "# defined in both branches: the guards in target.c are",
        "# `#if BUILD_TARGETS_ALL == 1`, and an undefined macro evaluates to",
        "# 0, which would silently drop every new architecture instead of",
        "# failing loudly.",
        "AC_ARG_ENABLE([third-party-targets],",
        "  AS_HELP_STRING([--disable-third-party-targets],",
        "    [do not build the merged third-party target architectures]),",
        "  [enable_third_party_targets=$enableval],",
        "  [enable_third_party_targets=yes])",
        "",
        "AS_IF([test \"x$enable_third_party_targets\" = xyes], [",
        "\tAC_DEFINE([BUILD_TARGETS_ALL], [1],",
        "\t\t[build the merged third-party target architectures])",
        "], [",
        "\tAC_DEFINE([BUILD_TARGETS_ALL], [0],",
        "\t\t[build the merged third-party target architectures])",
        "])",
        "AM_CONDITIONAL([TARGETS_ALL], [test \"x$enable_third_party_targets\" = xyes])",
        "",
        "# The RI4 bridge talks to the probe over raw USB, so it needs",
        "# libusb-1.x.  Upstream allows a build without libusb, so the group",
        "# gets its own guard instead of riding on BUILD_TARGETS_ALL.",
        "AS_IF([test \"x$enable_third_party_targets\" = xyes -a \"x$use_libusb1\" = xyes], [",
        "\tAC_DEFINE([BUILD_MCHP_RI4], [1],",
        "\t\t[build the Microchip RI4 target])",
        "], [",
        "\tAC_DEFINE([BUILD_MCHP_RI4], [0],",
        "\t\t[build the Microchip RI4 target])",
        "])",
        "",
        "# VexRiscv parses a YAML blob via libyaml.  Without it the target",
        "# is simply not built, so this is a soft dependency: no",
        "# AC_MSG_ERROR.",
        "PKG_CHECK_MODULES([LIBYAML], [yaml-0.1],",
        "\t[use_libyaml=yes], [use_libyaml=no])",
        "AM_CONDITIONAL([HAVE_LIBYAML], [test \"x$use_libyaml\" = xyes])",
        "AS_IF([test \"x$use_libyaml\" = xyes], [",
        "\tAC_DEFINE([HAVE_LIBYAML], [1], [define if libyaml is available])",
        "], [",
        "\tAC_DEFINE([HAVE_LIBYAML], [0], [define if libyaml is available])",
        "])",
        "AS_IF([test \"x$enable_third_party_targets\" = xyes -a \"x$use_libyaml\" = xyes], [",
        "\tAC_DEFINE([BUILD_VEXRISCV], [1],",
        "\t\t[build the VexRiscv target])",
        "], [",
        "\tAC_DEFINE([BUILD_VEXRISCV], [0],",
        "\t\t[build the VexRiscv target])",
        "])",
        "",
        "# zlib unpacks the gzipped probe firmware catalogue the RI4",
        "# loader reads.  Soft dependency for the same reason as libyaml.",
        "PKG_CHECK_MODULES([ZLIB], [zlib],",
        "\t[use_zlib=yes], [use_zlib=no])",
        "AM_CONDITIONAL([HAVE_ZLIB], [test \"x$use_zlib\" = xyes])",
        "AS_IF([test \"x$use_zlib\" = xyes], [",
        "\tAC_DEFINE([HAVE_ZLIB], [1], [define if zlib is available])",
        "], [",
        "\tAC_DEFINE([HAVE_ZLIB], [0], [define if zlib is available])",
        "])",
        END_AC,
        "",
        "",
    ])
    # The block carries its own leading and trailing newline, so the
    # previous statement and the anchor stay on their own lines.
    text = text.replace(anchor, block + anchor, 1)
    write_lf(path, text, eol)
    print("  configure.ac             --disable-third-party-targets added")


def verify_files_exist():
    """Fail loudly if the group list names a file that is not in the tree.

    This is the check that would have caught hexagon.h / or1k_jtag.h before
    they reached CI: automake silently accepts a missing header in
    SOURCES, so the mistake only shows up as a "no rule to make target"
    message much later, or never (for headers, which are not compiled).
    """
    missing = []
    for g in GROUPS:
        for f in g["files"]:
            if not (ROOT / "src/target" / f).exists():
                missing.append("src/target/%s" % f)
    for h in HEADERS:
        if not (ROOT / "src/target" / h).exists():
            missing.append("src/target/%s" % h)
    if missing:
        sys.exit("these files are listed but do not exist:\n  " +
                 "\n  ".join(missing))
    print("  file list                %d headers, all present" % len(HEADERS))


def main():
    if not (ROOT / "src/target/Makefile.am").exists():
        sys.exit("run me from inside the openocd checkout")

    print("wiring third-party target architectures:")
    verify_files_exist()
    patch_configure()
    patch_makefile()
    patch_target_c()
    print("done -- run ./bootstrap && ./configure next")


if __name__ == "__main__":
    main()

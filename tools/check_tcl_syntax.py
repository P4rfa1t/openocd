#!/usr/bin/env python3
"""AUDIT (read-only): parse every TCL file this tree ships.

WHY THIS EXISTS
---------------
The TCL subsystem is the part of OpenOCD a user meets first: a config that does
not parse takes the whole session down with it, and unlike C code there is no
compiler that would have caught it.  The other checks in tools/ answer different
questions - verify_tree.py asks whether the overlay matches manifest/, and
audit_dangling_refs.py asks whether every [find ...] leads somewhere.  Neither
of them ever reads a config as TCL, so a stray brace or an unterminated quote
could sit in the tree indefinitely.

This tool closes that gap: it hands every tracked tcl/ file to a TCL interpreter
and asks it the two questions an interpreter can answer without running the
config,
  * can the file be read and decoded?  (a file the interpreter cannot open is
    indistinguishable from a missing one at runtime)
  * is the script complete?  (info complete reports unterminated braces, quotes,
    brackets and a trailing backslash)

It never executes the configurations - no target is touched, no adapter is
opened - and it never writes inside the tree.

EXIT CODES
----------
0  every file parsed, or no interpreter was available (printed as SKIP)
1  at least one file failed to open or reported incomplete

Use --quiet to print only the summary line.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

QUIET = "--quiet" in sys.argv[1:]

TCLSH_CANDIDATES = ("tclsh", "tclsh8.6", "tclsh8.7", "tclsh9.0", "tclsh86")


def find_tclsh():
    """First usable interpreter, honouring $TCLSH.  Returns None when absent."""
    override = os.environ.get("TCLSH")
    if override:
        return override if shutil.which(override) or pathlib.Path(override).is_file() else None
    for name in TCLSH_CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    return None


def tcl_files():
    """Tracked tcl/ configurations, or a filesystem walk when git is missing."""
    try:
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "ls-files", "tcl/*.cfg", "tcl/*.tcl"],
            capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout
        files = [line for line in out.splitlines() if line.strip()]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    return sorted(
        p.as_posix() for p in pathlib.Path("tcl").rglob("*")
        if p.is_file() and p.suffix in (".cfg", ".tcl")
    )


# The interpreter has to open the list itself, so the path travels as a Tcl
# literal.  Braces around it make backslashes and spaces literal; a Windows
# path is written with forward slashes, which every Tcl build accepts.
DRIVER = """set n 0; set bad 0; set of 0
set fh [open {%(list)s} r]
fconfigure $fh -encoding utf-8
set list [read $fh]
close $fh
foreach f [split [string trim $list] "\n"] {
    if {$f eq ""} { continue }
    incr n
    if {[catch {set h [open $f r]; fconfigure $h -encoding utf-8; \
                set data [read $h]; close $h} err]} {
        puts "OPENFAIL\t$f"
        incr of
        continue
    }
    if {![info complete $data]} {
        puts "INCOMPLETE\t$f"
        incr bad
    }
}
puts "CHECKED $n OPENFAIL $of TOTAL_INCOMPLETE $bad"
"""


def main():
    files = tcl_files()
    if not files:
        print("check_tcl_syntax: no tcl files found")
        return 1

    tclsh = find_tclsh()
    if not tclsh:
        print(f"check_tcl_syntax: SKIP (no TCL interpreter found; {len(files)} files unchecked)")
        return 0

    fd, list_path = tempfile.mkstemp(prefix="tclcheck-", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(files) + "\n")

    fd, drv_path = tempfile.mkstemp(prefix="tclcheck-", suffix=".tcl")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(DRIVER % {"list": pathlib.Path(list_path).as_posix()})

    try:
        run = subprocess.run(
            [tclsh, drv_path], capture_output=True, text=True, encoding="utf-8",
        )
    finally:
        for p in (list_path, drv_path):
            try:
                os.unlink(p)
            except OSError:
                pass

    lines = (run.stdout or "").splitlines()
    summary = next((l for l in reversed(lines) if l.startswith("CHECKED ")), None)
    for line in lines:
        if line.startswith("OPENFAIL\t") or line.startswith("INCOMPLETE\t"):
            print("  " + line.replace("\t", ": "))

    if summary is None:
        print("check_tcl_syntax: FAIL (interpreter produced no summary)")
        print((run.stderr or "").strip()[:2000])
        return 1

    fields = dict(zip(("CHECKED", "OPENFAIL", "TOTAL_INCOMPLETE"),
                      (summary.split()[1], summary.split()[3], summary.split()[5])))
    bad = int(fields["OPENFAIL"]) + int(fields["TOTAL_INCOMPLETE"])
    if bad:
        print(f"check_tcl_syntax: FAIL ({summary})")
        return 1
    print(f"check_tcl_syntax: OK ({fields[r'CHECKED']} files parsed, 0 problems)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

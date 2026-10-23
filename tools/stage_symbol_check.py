#!/usr/bin/env python3
"""Check staged third-party sources for symbols that do not exist upstream.

For every function-like identifier used in a staged file, decide whether the
upstream tree (headers only, to avoid picking up static definitions) declares
it.  Anything left over is a candidate for a missing dependency.

Usage: python tools/stage_symbol_check.py
"""
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(errors="backslashreplace")

STAGE = os.path.join("raw", "stage-new-imports")

# Identifiers that are defined by the staged files themselves or that are
# intentionally local.
KNOWN_LOCAL_PREFIX = (
    "al_", "rbb_", "al_link", "rbb", "jtag_add_tdi_seq", "jtag_add_tms_seq",
    "tap_state", "interface_add_tdi_seq",
)


def upstream_headers():
    files = subprocess.run(
        ["git", "ls-files", "src"], capture_output=True, text=True).stdout.split()
    return [f for f in files if f.endswith(".h")]


def declared_symbols():
    out = set()
    for h in upstream_headers():
        try:
            t = open(h, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        out.update(re.findall(r"\b([a-z_][a-z0-9_]*)\s*\(", t))
        out.update(re.findall(r"#define\s+([A-Za-z_][A-Za-z0-9_]*)", t))
        out.update(re.findall(r"\b([A-Z_][A-Z0-9_]{3,})\b", t))
    return out


def strip_noise(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r'"(?:\\.|[^"\\])*"', '""', src)
    return src


def main():
    decl = declared_symbols()
    print("upstream header symbols: %d" % len(decl))
    files = []
    for root, _dirs, names in os.walk(STAGE):
        for n in sorted(names):
            if n.endswith((".c", ".h")):
                files.append(os.path.join(root, n))
    for f in sorted(files):
        src = strip_noise(open(f, encoding="utf-8", errors="replace").read())
        ids = set(re.findall(r"\b([a-z_][a-z0-9_]*)\s*\(", src))
        unknown = sorted(
            i for i in ids
            if i not in decl and not i.startswith(KNOWN_LOCAL_PREFIX)
        )
        rel = os.path.relpath(f, STAGE)
        print("\n### %s -- unresolved calls: %d" % (rel, len(unknown)))
        for u in unknown:
            print("    %s" % u)


if __name__ == "__main__":
    main()

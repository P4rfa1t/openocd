#!/usr/bin/env python3
"""Deep link check for the staged third-party files.

For every staged file, list the identifiers it uses that are defined
neither in the upstream src/ tree nor in the staged set itself.  Those are
hard link errors: the build will fail on them.

Usage: python tools/deep_link_check.py
"""
import collections
import os
import re
import sys

sys.stdout.reconfigure(errors="backslashreplace")

STAGE = os.path.join("raw", "stage-new-imports")

IDENT = re.compile(r"\b[A-Za-z_]\w*\b")

SKIP = set("""int char long short unsigned signed void float double size_t bool
uint8_t uint16_t uint32_t uint64_t int8_t int16_t int32_t int64_t uintptr_t intptr_t
FILE va_list memcpy memset memmove memcmp strlen strcpy strncpy strcmp strncmp strchr
strrchr strstr strtok sprintf snprintf printf fprintf sscanf malloc calloc realloc free
exit abort atoi atol atof strtol strtoul strtod rand srand time clock getenv errno
EINVAL ENOMEM EIO EOF SEEK_SET SEEK_CUR SEEK_END static const volatile inline struct
union enum typedef register return if else for while do switch case break continue
default goto sizeof NULL true false""".split())


def defs_of(txt):
    d = set()
    pats = [
        r"^(?!\s)(?:static\s+|extern\s+|const\s+|inline\s+)*[A-Za-z_][\w\s\*]*?\b(\w+)\s*\([^;{]*\)\s*\{",
        r"^\s*(?:static\s+|extern\s+|const\s+)*[A-Za-z_][\w\s\*]*?\b(\w+)\s*\([^;]*\)\s*;",
        r"^\s*#\s*define\s+(\w+)",
        r"^(?!\s)(?:struct|union)\s+\w+\s+\**(\w+)\s*=\s*\{",
        r"^\s*(\w+)\s*(?:=\s*[^,]+)?\s*,\s*$",
        r"^\s+(\w+)\s*(?:\[[^\]]*\])?\s*;",
        r"typedef\s+.*?(\w+)\s*;",
    ]
    for p in pats:
        for m in re.finditer(p, txt, re.M):
            d.add(m.group(1))
    for m in re.finditer(r"^\s*(?:struct|union)\s+\w+\s*\{(.*?)^\}", txt, re.M | re.S):
        for m2 in re.finditer(r"\b(\w+)\s*(?:;|\[|,|\))", m.group(1)):
            d.add(m2.group(1))
    for m in re.finditer(r"\benum\s+(\w+)\s*\{(.*?)\}", txt, re.S):
        d.add(m.group(1))
        for m2 in re.finditer(r"\b(\w+)\b", m.group(2)):
            d.add(m2.group(1))
    return d


def main():
    staged = []
    for dp, _d, fs in os.walk(STAGE):
        for fn in fs:
            if fn.endswith((".c", ".h")):
                staged.append(os.path.join(dp, fn))
    staged.sort()

    up = set()
    for dp, dirs, fs in os.walk("src"):
        dirs[:] = [d for d in dirs if d not in (".git", "jimtcl", "libjaylink")]
        for fn in fs:
            if not fn.endswith((".c", ".h")):
                continue
            try:
                up |= defs_of(open(os.path.join(dp, fn),
                                   encoding="utf-8", errors="replace").read())
            except OSError:
                pass

    own = set()
    for p in staged:
        own |= defs_of(open(p, encoding="utf-8", errors="replace").read())

    print("### identifiers used but defined nowhere ###\n")
    for p in staged:
        rel = os.path.relpath(p, STAGE).replace(os.sep, "/")
        txt = open(p, encoding="utf-8", errors="replace").read()
        txt = re.sub(r"/\*.*?\*/", " ", txt, flags=re.S)
        txt = re.sub(r"//[^\n]*", " ", txt)
        txt = re.sub(r'"(\\.|[^"\\])*"', ' "" ', txt)
        miss = collections.Counter()
        where = {}
        for i, line in enumerate(txt.split("\n"), 1):
            for ident in IDENT.findall(line):
                if ident in up or ident in own or ident in SKIP:
                    continue
                if ident.isupper() and "_" in ident:
                    continue
                miss[ident] += 1
                where.setdefault(ident, i)
        if miss:
            print("--- %s ---" % rel)
            for ident, n in miss.most_common(30):
                print("    %-44s x%-4d first@L%d" % (ident, n, where[ident]))
            print()


if __name__ == "__main__":
    main()

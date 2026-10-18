#!/usr/bin/env python3
"""
Verify the merged tree against its own manifest.

This is the offline gate that runs AFTER fetching or after a rebase onto a new
upstream release. It deliberately makes NO network calls, so it can be used as
a CI check.

Checks
------
1. every provenance entry has a real file on disk;
2. every third-party file on disk is recorded in provenance;
3. the recorded SHA-256 still matches the bytes on disk;
4. no imported file is also present upstream (which would mean a pointless
   or conflicting copy);
5. every .cfg parses as balanced Tcl braces/brackets (cheap corruption check);
6. licence coverage: every source repo has an SPDX id or is flagged for audit.
"""

import hashlib
import json
import os
import sys
from collections import Counter

MANIFEST = "manifest/PROVENANCE.json"
UPSTREAM_INDEX = "manifest/upstream-index.txt"
# Directories that hold imported content. Everything else in the tree is
# upstream code and is therefore not subject to the 1:1 accounting.
TREES = ("tcl", "src")


def load_prov(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tcl_balance(text):
    """Braces and brackets must balance, ignoring comments and quoted text.

    An earlier revision counted only double quotes and flagged icepick.cfg as
    unbalanced, which was a FALSE POSITIVE: OpenOCD .cfg files legitimately
    contain braces inside double-quoted TCL strings and inside `#` comments
    (e.g. `-eval { ... }` bodies with `[if {...}]`). Tcl comments and quoted
    strings must both be stripped before counting.
    """
    depth = {"{": 0, "[": 0}
    close = {"}": "{", "]": "["}
    state = "code"   # code | quote | comment
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if state == "code":
            if ch == "\\":
                i += 2
                continue
            if ch == "#":
                state = "comment"
            elif ch == '"':
                state = "quote"
            elif ch in depth:
                depth[ch] += 1
            elif ch in close:
                depth[close[ch]] -= 1
                if depth[close[ch]] < 0:
                    return False
        elif state == "quote":
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                state = "code"
        else:  # comment
            if ch == "\n":
                state = "code"
        i += 1
    # An unterminated quote or an open block at EOF is a real defect.
    if state == "quote":
        return False
    return depth["{"] == 0 and depth["["] == 0


def normalise(p):
    """Fold path shape so upstream's reorganisation is detected.

    Upstream moved TCL into vendor subdirectories AND dropped redundant vendor
    prefixes from the filenames, so one upstream file answers to several fork
    paths:

        upstream tcl/target/ti/cc13x0.cfg
        fork     tcl/target/ti_cc13x0.cfg     (prefix in the filename)
        fork     tcl/board/ti/am642evm.cfg vs tcl/board/ti_am642evm.cfg

    Comparing only exact paths let 102 such duplicates into the tree - including
    70 board files and 29 target files that upstream has shipped for years. A
    stem-only test is not enough either: `ti_am642evm.cfg` and `am642evm.cfg`
    share no stem.
    """
    return p.replace("_", "").replace("-", "").replace("/", "").casefold()


def check(files, upstream=set(), upstream_norm=None):
    stray = [k for k, v in files.items() if not isinstance(v, dict)]
    if stray:
        print(f"  WARNING: {len(stray)} non-record provenance keys ignored: "
              f"{stray[:6]}")
        files = {k: v for k, v in files.items() if isinstance(v, dict)}
    errors, warns = [], []
    if upstream_norm is None:
        upstream_norm = {normalise(p): p for p in upstream}

    on_disk = set()
    for top in TREES:
        for dirpath, _dirs, names in os.walk(top):
            for n in names:
                on_disk.add(os.path.relpath(os.path.join(dirpath, n)).replace(os.sep, "/"))
    on_disk -= upstream

    for rel, rec in files.items():
        if not os.path.exists(rel):
            errors.append(f"recorded but missing: {rel}")
            continue
        data = open(rel, "rb").read()
        if hashlib.sha256(data).hexdigest() != rec["sha256"]:
            errors.append(f"sha256 mismatch: {rel}")
        if not rec.get("source_commit"):
            warns.append(f"no commit pin: {rel}")
        if not rec.get("license"):
            warns.append(f"no SPDX resolved: {rel}")
        # Redundancy is an ERROR here, not a note.
        #
        # These are pure duplicates of files upstream already ships, reached
        # because upstream renamed when it reorganised into vendor
        # subdirectories. Keeping them is actively harmful: the stale copy
        # shadows the upstream one that upstream actually maintains.
        if rel in upstream:
            errors.append(f"exact duplicate of upstream {rel}")
        else:
            alt = upstream_norm.get(normalise(rel))
            if alt:
                errors.append(f"renamed duplicate: {rel} == upstream {alt}")

    for rel in sorted(on_disk - set(files)):
        errors.append(f"on disk but unrecorded: {rel}")

    bad_tcl = []
    for rel in sorted(files):
        if not rel.endswith((".cfg", ".tcl")) or not os.path.exists(rel):
            continue
        try:
            text = open(rel, encoding="utf-8").read()
        except UnicodeDecodeError:
            errors.append(f"not utf-8: {rel}")
            continue
        if not tcl_balance(text):
            bad_tcl.append(rel)
    for rel in bad_tcl:
        errors.append(f"unbalanced tcl: {rel}")

    lic = Counter(r.get("license") or "UNLICENSED" for r in files.values())
    unknown = sum(v for k, v in lic.items()
                  if k in ("UNLICENSED", "NOASSERTION", "other"))

    return {
        "recorded": len(files),
        "on_disk": len(on_disk),
        "errors": errors,
        "warns": warns,
        "licenses": dict(lic),
        "licence_unresolved_files": unknown,
        "duplicate_providers": _dupes(files),
    }


def _dupes(files):
    """How many files exist in more than one source repo (dedup value)."""
    n = Counter(len(r["also_present_in"]) + 1 for r in files.values())
    return dict(n)


def main():
    if not os.path.exists(MANIFEST):
        print(f"missing {MANIFEST}")
        return 1
    upstream = set()
    if os.path.exists(UPSTREAM_INDEX):
        upstream = {l.strip() for l in open(UPSTREAM_INDEX, encoding="utf-8")
                    if l.strip()}

    prov = load_prov(MANIFEST)
    r = check(prov.get("files", {}), upstream)

    print(f"recorded : {r['recorded']}")
    print(f"on disk  : {r['on_disk']}")
    print(f"errors   : {len(r['errors'])}")
    for e in r["errors"][:15]:
        print(f"    ERROR {e}")
    print(f"warns    : {len(r['warns'])}")
    for w in r["warns"][:5]:
        print(f"    warn  {w}")
    print(f"licences : {r['licenses']}")
    print(f"licence-unresolved files: {r['licence_unresolved_files']}")
    print(f"copies-per-file histogram: {r['duplicate_providers']}")

    rc = 1 if r["errors"] else 0
    print("\n" + ("VERIFY: FAIL" if rc else "VERIFY: PASS"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Verify the produced overlay and patch worklist against their own manifest.

This is the offline gate that runs AFTER fetching. It deliberately makes NO
network calls, so it can be used as a CI check.

Checks
------
1. every provenance entry has a real file on disk;
2. every file on disk is recorded in provenance;
3. the recorded SHA-256 still matches the bytes on disk;
4. no overlay file is also present upstream (which would mean a pointless
   or conflicting copy);
5. every .cfg parses as balanced Tcl braces/brackets (cheap corruption check);
6. licence coverage: every source repo has an SPDX id or is flagged for audit.
"""

import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

TIER1 = "overlay"
TIER2 = "manifest/tier2"
MANIFEST = "overlay/PROVENANCE.json"
UPSTREAM_INDEX = "manifest/upstream-index.txt"


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

    Comparing only exact paths let 102 such duplicates into the overlay -
    including 70 board files and 29 target files that upstream has shipped for
    years. A stem-only test is not enough either: `ti_am642evm.cfg` and
    `am642evm.cfg` share no stem.
    """
    return p.replace("_", "").replace("-", "").replace("/", "").casefold()


def check_tier(root, prov_path, upstream=set(), upstream_norm=None):
    prov = load_prov(prov_path)
    # Defensive: only the per-file map is valid here. A provenance document
    # also carries metadata keys ("upstream", "tier", "files", ...); if those
    # ever leak into this dict, every later lookup misbehaves with a confusing
    # AttributeError, so drop them explicitly and loudly.
    files = prov.get("files", {}) if isinstance(prov, dict) else {}
    stray = [k for k, v in files.items() if not isinstance(v, dict)]
    if stray:
        print(f"  WARNING: {len(stray)} non-record provenance keys ignored: "
              f"{stray[:6]}")
        files = {k: v for k, v in files.items() if isinstance(v, dict)}
    errors, warns, notes = [], [], []
    if upstream_norm is None:
        upstream_norm = {normalise(p): p for p in upstream}

    on_disk = set()
    for dirpath, _dirs, names in os.walk(root):
        for n in names:
            rel = os.path.relpath(os.path.join(dirpath, n), root)
            rel = rel.replace(os.sep, "/")
            # PROVENANCE.json is this tool's own metadata, not imported
            # content. Counting it made every run report exactly one spurious
            # "on disk but unrecorded" error.
            if rel == "PROVENANCE.json":
                continue
            on_disk.add(rel)

    for rel, rec in files.items():
        fp = os.path.join(root, rel)
        if not os.path.exists(fp):
            errors.append(f"recorded but missing: {rel}")
            continue
        data = open(fp, "rb").read()
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
        # subdirectories. Shipping them is actively harmful: the overlay is
        # meant to be searched FIRST, so the stale flat-named copy wins over
        # upstream's maintained one and silently shadows upstream fixes.
        if rel in upstream:
            errors.append(f"exact duplicate of upstream {rel}")
        else:
            alt = upstream_norm.get(normalise(rel))
            if alt:
                errors.append(f"renamed duplicate: {rel} == upstream {alt}")

    for rel in sorted(on_disk - set(files)):
        if rel == "PROVENANCE.json":
            continue
        errors.append(f"on disk but unrecorded: {rel}")

    bad_tcl = []
    for rel in sorted(files):
        if not rel.endswith((".cfg", ".tcl")):
            continue
        fp = os.path.join(root, rel)
        if os.path.exists(fp):
            try:
                text = open(fp, encoding="utf-8").read()
            except UnicodeDecodeError:
                errors.append(f"not utf-8: {rel}")
                continue
            if not tcl_balance(text):
                bad_tcl.append(rel)
    for rel in bad_tcl:
        errors.append(f"unbalanced tcl: {rel}")

    # licence coverage
    lic = Counter(r.get("license") or "UNLICENSED"
                  for r in files.values())
    unknown = sum(v for k, v in lic.items()
                  if k in ("UNLICENSED", "NOASSERTION", "other"))

    return {
        "root": root,
        "recorded": len(files),
        "on_disk": len(on_disk),
        "errors": errors,
        "warns": warns,
        "notes": notes,
        "licenses": dict(lic),
        "licence_unresolved_files": unknown,
        "duplicate_providers": _dupes(files),
    }


def _dupes(files):
    """How many files exist in more than one source repo (dedup value)."""
    n = Counter(len(r["also_present_in"]) + 1 for r in files.values())
    return dict(n)


def main():
    upstream = set()
    if os.path.exists(UPSTREAM_INDEX):
        upstream = {l.strip() for l in open(UPSTREAM_INDEX, encoding="utf-8")
                    if l.strip()}

    results = []
    for root, mpath in ((TIER1, MANIFEST), (TIER2, "manifest/tier2/PROVENANCE.json")):
        if not os.path.exists(mpath):
            print(f"skip {root}: no {mpath}")
            continue
        results.append(check_tier(root, mpath, upstream))

    rc = 0
    for r in results:
        print(f"\n=== {r['root']} ===")
        print(f"  recorded : {r['recorded']}")
        print(f"  on disk  : {r['on_disk']}")
        print(f"  errors   : {len(r['errors'])}")
        for e in r["errors"][:15]:
            print(f"      ERROR {e}")
        print(f"  warns    : {len(r['warns'])}")
        for w in r["warns"][:5]:
            print(f"      warn  {w}")
        print(f"  notes    : {len(r['notes'])} (also-exists-upstream; "
              f"overlay defers to upstream at runtime)")
        print(f"  licences : {r['licenses']}")
        print(f"  licence-unresolved files: {r['licence_unresolved_files']}")
        print(f"  copies-per-file histogram: {r['duplicate_providers']}")
        if r["errors"]:
            rc = 1

    print("\n" + ("VERIFY: FAIL" if rc else "VERIFY: PASS"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Merge the per-tier PROVENANCE.json files into one manifest/PROVENANCE.json.

The keys of the merged file are paths inside the OpenOCD tree (tcl/..., src/...),
i.e. exactly where the files live after the merge, so the manifest and the
working tree stay 1:1.

Idempotent: reading and writing the same file twice is a no-op.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ["manifest/tier1-PROVENANCE.json", "manifest/tier2-PROVENANCE.json"]
OUT = "manifest/PROVENANCE.json"


def main() -> int:
    refresh = "--refresh" in sys.argv[1:]
    files: dict = {}
    meta: dict = {}
    for rel in SOURCES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"skip missing {rel}")
            continue
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        for path, rec in data.get("files", {}).items():
            if refresh and os.path.exists(os.path.join(ROOT, path)):
                import hashlib
                rec = dict(rec)
                rec["sha256"] = hashlib.sha256(
                    open(os.path.join(ROOT, path), "rb").read()).hexdigest()
            files[path] = rec
        for key in ("upstream", "upstream_branch", "integrity", "unresolved_references"):
            if key in data:
                meta[key] = data[key]

    missing = sorted(p for p in files if not os.path.exists(os.path.join(ROOT, p)))
    if missing:
        print(f"ERROR: {len(missing)} recorded files missing on disk, e.g. {missing[:5]}")
        return 1

    out = {
        "upstream": meta.get("upstream", "openocd-org/openocd"),
        "upstream_branch": meta.get("upstream_branch", "master"),
        "file_count": len(files),
        "integrity": meta.get("integrity", {}),
        "unresolved_references": meta.get("unresolved_references", {}),
        "files": dict(sorted(files.items())),
    }
    dest = os.path.join(ROOT, OUT)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"wrote {OUT}: {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
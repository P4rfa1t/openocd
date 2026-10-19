#!/usr/bin/env python3
"""Merge the per-tier PROVENANCE.json files into one manifest/PROVENANCE.json.

The keys of the merged file are paths inside the OpenOCD tree (tcl/..., src/...),
i.e. exactly where the files live after the merge, so the manifest and the
working tree stay 1:1.

Idempotent: reading and writing the same file twice is a no-op.

FORMAT CONTRACT
---------------
The manifest is written with json.dumps(indent=2, ensure_ascii=False) and LF
line endings, and the file is written through newline="\\n" so a Windows
checkout does not silently turn the whole manifest into CRLF. The previous
version used indent=1 and the default newline translation, which produced a
19000-line diff that had nothing to do with the actual content change.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ["manifest/tier1-PROVENANCE.json", "manifest/tier2-PROVENANCE.json"]
OUT = "manifest/PROVENANCE.json"

# Keys that are merged from the tier files into the combined document. The
# per-file map is merged separately because it is keyed by path.
META_KEYS = (
    "upstream",
    "upstream_branch",
    "unresolved_references",
    "pruned_as_upstream_redundant",
    "removed_from_tree",
)


def main() -> int:
    refresh = "--refresh" in sys.argv[1:]
    files: dict = {}
    meta: dict = {}
    for rel in SOURCES:
        path = ROOT / rel
        if not path.exists():
            print(f"skip missing {rel}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for rel_path, rec in data.get("files", {}).items():
            if refresh and (ROOT / rel_path).exists():
                rec = dict(rec)
                rec["sha256"] = hashlib.sha256(
                    (ROOT / rel_path).read_bytes()).hexdigest()
            files[rel_path] = rec
        for key in META_KEYS:
            if key in data:
                value = data[key]
                if key == "removed_from_tree" and key in meta:
                    # Keep one trail, not one per tier.
                    known = {e.get("path") for e in meta[key] if isinstance(e, dict)}
                    for entry in value:
                        if entry.get("path") not in known:
                            meta[key].append(entry)
                else:
                    meta[key] = value

    missing = sorted(p for p in files if not (ROOT / p).exists())
    if missing:
        print(f"ERROR: {len(missing)} recorded files missing on disk, e.g. {missing[:5]}")
        return 1

    on_disk = sum(1 for p in files if (ROOT / p).exists())
    pinned = sum(1 for v in files.values() if v.get("source_commit"))
    integrity = {
        "recorded": len(files),
        "on_disk": on_disk,
        "pinned": pinned,
        "note": "recorded == on_disk; pinned == recorded means fully traceable",
    }

    out = {
        "upstream": meta.get("upstream", "openocd-org/openocd"),
        "upstream_branch": meta.get("upstream_branch", "master"),
        "file_count": len(files),
        "integrity": integrity,
        "unresolved_references": meta.get("unresolved_references", {}),
        "files": dict(sorted(files.items())),
    }
    for key in ("pruned_as_upstream_redundant", "removed_from_tree"):
        if key in meta:
            out[key] = meta[key]

    dest = ROOT / OUT
    dest.write_text(
        json.dumps(out, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8", newline="\n")
    print(f"wrote {OUT}: {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

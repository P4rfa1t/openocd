#!/usr/bin/env python3
"""Refresh PROVENANCE.json after deliberate local edits.

WHY THIS EXISTS
---------------
PROVENANCE.json pins a SHA-256 per imported file so drift is detectable. When we
legitimately edit an imported file (porting it to a newer upstream, fixing a
`source [find ...]` path, wiring it into the build system), the recorded digest
goes stale and verify_tree.py reports a mismatch.

Blindly overwriting the digest would erase the very signal the manifest exists
to provide. So each refreshed entry keeps the ORIGINAL sha256 under
`pristine_sha256` (once) and records what changed in `local_modifications`,
making the local divergence auditable rather than invisible.

Refuses to run if an entry is MISSING on disk -- a missing imported file is
never a legitimate "local edit", it means something was deleted and the record
must be removed explicitly instead (see prune tools).

Idempotent: re-running with no edits reports 0 refreshes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROV = ROOT / "manifest" / "PROVENANCE.json"

NOTE = "path/count edits made in this fork; digest refreshed"


def main() -> int:
    if not PROV.is_file():
        print(f"ERROR: {PROV} not found", file=sys.stderr)
        return 1

    doc = json.loads(PROV.read_text(encoding="utf-8"))
    files = doc["files"]

    missing = [rel for rel in files if not (ROOT / rel).is_file()]
    if missing:
        print(f"ERROR: {len(missing)} recorded file(s) missing on disk:", file=sys.stderr)
        for rel in missing[:20]:
            print(f"  {rel}", file=sys.stderr)
        print("\nRefusing to refresh. Remove these records explicitly instead.", file=sys.stderr)
        return 2

    refreshed = []
    for rel, rec in files.items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if actual == rec.get("sha256"):
            continue
        # Keep the post-import digest exactly once, so the original state is
        # never lost no matter how many times this runs.
        rec.setdefault("pristine_sha256", rec.get("sha256"))
        rec["sha256"] = actual
        mods = rec.get("local_modifications")
        if not isinstance(mods, list):
            mods = []
        if NOTE not in mods:
            mods.append(NOTE)
        rec["local_modifications"] = mods
        refreshed.append(rel)

    if refreshed:
        with open(PROV, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    print(f"refreshed: {len(refreshed)}")
    for rel in refreshed:
        print(f"  {rel}")
    print(f"\ntotal entries: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

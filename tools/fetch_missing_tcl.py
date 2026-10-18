#!/usr/bin/env python3
"""Re-fetch a tcl config that the import missed, and record its provenance.

WHY THIS EXISTS
---------------
Some forks ship board configs that `source` a target config which lives in the
same fork but was NOT part of the de-duplication import (upstream does not have
it, so it never entered consolidated.json). The board config then points at a
file that does not exist, and OpenOCD fails at `source [find ...]` time.

Example: tcl/board/adspsc589_ezbrd.cfg (from analogdevicesinc/openocd) sources
tcl/target/adspsc58x.cfg, which only exists in that same fork.

This tool fetches such files directly from their source repo at the EXACT
commit recorded for the sibling file in PROVENANCE.json, so the addition stays
commit-pinned and auditable rather than floating on a branch head.

Idempotent: an existing destination file is never overwritten.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROV = ROOT / "manifest" / "PROVENANCE.json"

# (source_repo, source_path, local_path, sibling_that_proves_the_commit)
WANTED = [
    (
        "analogdevicesinc/openocd",
        "tcl/target/adspsc58x.cfg",
        "tcl/target/adspsc58x.cfg",
        "tcl/board/adspsc589_minibrd.cfg",
    ),
]


def api(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "openocd-import"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main() -> int:
    token = os.environ.get("GH_TOKEN") or None
    if not PROV.is_file():
        print(f"ERROR: {PROV} not found", file=sys.stderr)
        return 1
    doc = json.loads(PROV.read_text(encoding="utf-8"))
    files = doc["files"]

    added = 0
    for repo, src_path, local_path, sibling in WANTED:
        dest = ROOT / local_path
        if dest.is_file():
            print(f"skip (exists): {local_path}")
            continue

        sib = files.get(sibling)
        if not sib:
            print(f"ERROR: sibling {sibling} not in manifest; cannot pin commit", file=sys.stderr)
            return 1
        commit = sib["source_commit"]

        data = api(
            f"https://api.github.com/repos/{repo}/contents/{src_path}?ref={commit}", token
        )
        if data.get("encoding") != "base64":
            print(f"ERROR: unexpected encoding for {src_path}", file=sys.stderr)
            return 1
        raw = base64.b64decode(data["content"])

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(raw)

        files[local_path] = {
            "source_repo": repo,
            "source_branch": sib.get("source_branch", ""),
            "source_commit": commit,
            "source_path": src_path,
            "license": sib.get("license", "NOASSERTION"),
            "stars_at_import": sib.get("stars_at_import", 0),
            "also_present_in": [],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "note": f"re-fetched: required by {sibling}",
        }
        added += 1
        print(f"added {local_path} ({len(raw)} bytes) from {repo}@{commit[:8]}")

    if added:
        with open(PROV, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        print(f"\nmanifest updated: {len(files)} entries")
    else:
        print("\nnothing to add")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

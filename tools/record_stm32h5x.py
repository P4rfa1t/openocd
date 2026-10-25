#!/usr/bin/env python3
"""Record the imported stm32h5x flash driver in the tier-2 provenance manifest.

Two files were imported from zuyih/openocd@5422b51c81253e7d212c36775ded24f525f4c783
(pristine copies, no local edits):

    src/flash/nor/stm32h5x.c
    src/flash/nor/stm32h5x.h

Idempotent: re-running after the manifest is already up to date changes nothing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TIER2 = ROOT / "manifest/tier2-PROVENANCE.json"

REPO = "zuyih/openocd"
BRANCH = "master"
COMMIT = "5422b51c81253e7d212c36775ded24f525f4c783"
ALSO_IN = [
    "STMicroelectronics/OpenOCD",
    "galippi/openocd.STM32.Win7",
    "scmrtos/openocd-scmrtos",
]
PATHS = ["src/flash/nor/stm32h5x.c", "src/flash/nor/stm32h5x.h"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    data = json.loads(TIER2.read_text(encoding="utf-8"))
    files = data["files"]
    added = []
    for rel in PATHS:
        f = ROOT / rel
        if not f.exists():
            print(f"ERROR: {rel} not on disk")
            return 1
        digest = sha256(f)
        rec = files.get(rel)
        if rec is not None and rec.get("sha256") == digest:
            continue
        files[rel] = {
            "source_repo": REPO,
            "source_branch": BRANCH,
            "source_commit": COMMIT,
            "source_path": rel,
            "license": "NOASSERTION",
            "stars_at_import": 0,
            "also_present_in": ALSO_IN,
            "sha256": digest,
            "pristine_sha256": digest,
            "local_modifications": [],
        }
        added.append(rel)

    n = len(files)
    data["files"] = dict(sorted(files.items()))
    data["file_count"] = n
    data["integrity"] = {
        "recorded": n,
        "on_disk": sum(1 for p in files if (ROOT / p).exists()),
        "pinned": sum(1 for v in files.values() if v.get("source_commit")),
        "unpinned": sum(1 for v in files.values() if not v.get("source_commit")),
        "note": "recorded == on_disk; pinned == recorded means fully traceable",
    }
    TIER2.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(f"tier2: {n} files (added {added or 'nothing'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
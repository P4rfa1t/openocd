#!/usr/bin/env python3
"""
Reconcile manifest/tier*-PROVENANCE.json with the tree as it actually is.

WHY THIS EXISTS
---------------
The provenance manifest is a 1:1 inventory: every key is a path in the tree
and every key must have a file on disk. verify_tree.py enforces that and
refuses to pass otherwise.

Several third-party files were deliberately removed from this fork after
they were imported, for reasons that are recorded in the fork's own git
history:

  * nds32 / cortex_a8 / cortex_m3 (27 files) - upstream and the vendor both
    dropped the architecture; the imported copies target a target_type
    interface that has moved on.
  * hexagon / or1k_jtag (6 files) - they collide with upstream symbols
    (`struct or1k_jtag` exists upstream too, and ARC defines `arcv2_target`
    twice).
  * seven mangled copies of two upstream files - upstream ships the real
    thing under its own Unicode name; the copies were URL-escape or
    mojibake variants of it.

Deleting the file but leaving the manifest entry behind is worse than a
missing file: the manifest then claims content the tree does not have, and
every licence statement derived from it points at a non-existent file.

SAFETY
------
A record is only dropped when BOTH hold:

  1. the file does not exist on disk, AND
  2. git confirms the path is not present in HEAD, i.e. the removal was
     committed on purpose rather than lost by accident.

Anything else is left alone and reported as an error, because an uncommitted
or unknown disappearance is a real problem, not a bookkeeping detail.

Idempotent: re-running with nothing deleted reports 0 pruned.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TIERS = ["manifest/tier1-PROVENANCE.json", "manifest/tier2-PROVENANCE.json"]
TRAIL_KEY = "removed_from_tree"

# Several paths in the manifest carry non-ASCII bytes (mojibake names imported
# from a fork that had mangled them). Printing them on a Windows console with
# a legacy code page raises UnicodeEncodeError, so the stream is widened to
# backslashreplace: a mangled name is still readable, just escaped.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")

# Files that upstream ships under its own (Unicode) name and that this fork
# restored verbatim. The mangled copies are dropped in favour of upstream's.
UPSTREAM_EQUIVALENT = {
    "tcl/target/1986#U0432#U04351#U0442.cfg": "tcl/target/1986ве1т.cfg",
    "tcl/target/1986Be1T.cfg": "tcl/target/1986ве1т.cfg",
    "tcl/target/1986Ð²Ðµ1Ñ‚.cfg": "tcl/target/1986ве1т.cfg",
    "tcl/target/#U043a1879x#U04311#U044y.cfg": "tcl/target/к1879xб1я.cfg",
    "tcl/target/k1879h61ya.cfg": "tcl/target/к1879xб1я.cfg",
    "tcl/target/k1879x61R.cfg": "tcl/target/к1879xб1я.cfg",
    "tcl/target/Ðº1879xÐ±1Ñ.cfg": "tcl/target/к1879xб1я.cfg",
}

# The two files above are keyed by their mangled names; the map is written
# with the exact byte sequences that appear in the manifest.
UPSTREAM_EQUIVALENT.update({
    "tcl/target/#U043a1879x#U04311#U044f.cfg": "tcl/target/к1879xб1я.cfg",
    "tcl/target/Ðº1879xÐ±1Ñ\x8f.cfg": "tcl/target/к1879xб1я.cfg",
})


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stdout


def tracked_paths() -> set[str]:
    out = git("ls-files", "-z")
    return {p for p in out.split("\x00") if p}


def deleting_commit(path: str) -> str:
    """The commit that removed `path` from the tree, if any."""
    out = git("log", "--diff-filter=D", "--format=%H", "-1", "--", path)
    return out.strip()


def reason_for(path: str) -> str | None:
    """Why the file is gone, or None when we cannot tell."""
    if path in UPSTREAM_EQUIVALENT:
        return (f"upstream ships this file as {UPSTREAM_EQUIVALENT[path]}; "
                "the mangled copy was dropped")
    commit = deleting_commit(path)
    if not commit:
        return None
    subject = git("log", "-1", "--format=%s", commit).strip()
    return f"removed on purpose in {commit[:12]} ({subject})"


def main() -> int:
    tracked = tracked_paths()
    total_pruned = 0
    problems: list[str] = []

    for tier_rel in TIERS:
        tier_path = ROOT / tier_rel
        if not tier_path.is_file():
            print(f"skip missing {tier_rel}")
            continue

        doc = json.loads(tier_path.read_text(encoding="utf-8"))
        files = doc.get("files")
        if not isinstance(files, dict):
            problems.append(f"{tier_rel}: no usable 'files' map")
            continue

        trail = doc.setdefault(TRAIL_KEY, [])
        known = {e.get("path") for e in trail if isinstance(e, dict)}

        pruned = []
        for rel in list(files):
            if (ROOT / rel).exists():
                continue
            if rel in tracked:
                problems.append(
                    f"{tier_rel}: {rel} is tracked by git but missing on disk")
                continue
            reason = reason_for(rel)
            if reason is None:
                problems.append(
                    f"{tier_rel}: {rel} is missing and git does not record a "
                    "deletion for it - refusing to prune")
                continue
            rec = files.pop(rel)
            total_pruned += 1
            pruned.append(rel)
            if rel not in known:
                entry = {"path": rel, "reason": reason}
                if rel in UPSTREAM_EQUIVALENT:
                    entry["upstream_path"] = UPSTREAM_EQUIVALENT[rel]
                entry["sha256_at_removal"] = rec.get("sha256")
                trail.append(entry)

        if pruned:
            doc["file_count"] = len(files)
            integrity = doc.setdefault("integrity", {})
            integrity["recorded"] = len(files)
            integrity["on_disk"] = sum(1 for p in files if (ROOT / p).exists())
            pinned = sum(1 for v in files.values() if v.get("source_commit"))
            integrity["pinned"] = pinned
            if "unpinned" in integrity:
                integrity["unpinned"] = len(files) - pinned
            integrity["note"] = (
                "recorded == on_disk; pinned == recorded means fully traceable")
            # The manifest is written with indent=2 and unescaped non-ASCII,
            # exactly like the files it replaces. Keeping that byte layout
            # means the diff only shows the entries that actually changed.
            tier_path.write_text(
                json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8", newline="\n")
            print(f"{tier_rel}: pruned {len(pruned)}")
            for p in pruned:
                print(f"    - {p}")
        else:
            # The entry set already matches the tree. The integrity counters
            # are still recomputed, because they were written when the
            # manifest was first generated and the tree has changed since.
            integrity = doc.get("integrity", {})
            recorded = len(files)
            on_disk = sum(1 for p in files if (ROOT / p).exists())
            pinned = sum(1 for v in files.values() if v.get("source_commit"))
            wanted = {
                "recorded": recorded,
                "on_disk": on_disk,
                "pinned": pinned,
            }
            if "unpinned" in integrity:
                wanted["unpinned"] = recorded - pinned
            wanted["note"] = (
                "recorded == on_disk; pinned == recorded means fully traceable")
            if integrity != wanted or doc.get("file_count") != recorded:
                doc["file_count"] = recorded
                doc["integrity"] = wanted
                tier_path.write_text(
                    json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")
                print(f"{tier_rel}: refreshed integrity counters "
                      f"(recorded={recorded} on_disk={on_disk} pinned={pinned})")
            else:
                print(f"{tier_rel}: nothing to prune")

    print(f"\npruned total: {total_pruned}")
    if problems:
        print(f"\nPROBLEMS ({len(problems)}):")
        for p in problems:
            print(f"  {p}")
        return 2
    print("OK: manifest and tree agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

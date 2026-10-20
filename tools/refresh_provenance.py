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

TWO KINDS OF DIVERGENCE, AND THEY MUST NOT BE CONFLATED
-------------------------------------------------------
* "line endings normalised to LF" -- the file's CONTENT is byte-identical to
  what the source fork published, but the bytes on disk use CRLF. This happens
  for the handful of files that were published with CRLF, while this fork
  standardises on LF (see .gitattributes and tools/normalize_eol.py). The
  content did not change; only the line terminators did.
* "content edited in this fork" -- a real edit: a path fix, a signature port,
  a build-system wiring change. The content differs.

Both directions have to be tried to tell them apart. A file published with
CRLF has a recorded digest over CRLF bytes; after this fork normalises the
tree to LF, the LF form no longer matches, and the only way to recognise it
as "same content, different terminators" is to re-expand the LF bytes back
to CRLF and compare. The reverse case (published LF, stored CRLF) is the one
the Windows checkout produced.

Lumping the two together would claim edits that never happened and hide the
ones that did.

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
# The two per-tier manifests are the source of truth; the combined manifest is
# regenerated from them by tools/build_provenance.py. Refreshing all three
# keeps them consistent whichever one a caller happens to read.
TARGETS = (
    "manifest/tier1-PROVENANCE.json",
    "manifest/tier2-PROVENANCE.json",
    "manifest/PROVENANCE.json",
)

NOTE_EDIT = "content edited in this fork; digest refreshed"
NOTE_EOL = "line endings normalised to LF; content byte-identical to the published file"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify(current: bytes, recorded: str) -> str:
    """Return the note describing how `current` diverges from `recorded`."""
    if sha(current) == recorded:
        return ""
    if sha(current.replace(b"\r\n", b"\n")) == recorded:
        return NOTE_EOL
    if sha(current.replace(b"\n", b"\r\n")) == recorded:
        return NOTE_EOL
    return NOTE_EDIT


def main() -> int:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return 0

    if not all((ROOT / t).is_file() for t in TARGETS):
        print(f"ERROR: expected {', '.join(TARGETS)}", file=sys.stderr)
        return 1

    eol_fixed: list[str] = []
    edited: list[str] = []
    seen: set[str] = set()

    for target in TARGETS:
        path = ROOT / target
        doc = json.loads(path.read_text(encoding="utf-8"))
        files = doc.get("files", {})

        missing = [rel for rel in files if not (ROOT / rel).is_file()]
        if missing:
            print(f"ERROR: {target}: {len(missing)} recorded file(s) missing on disk:",
                  file=sys.stderr)
            for rel in missing[:20]:
                print(f"  {rel}", file=sys.stderr)
            print("\nRefusing to refresh. Remove these records explicitly instead.",
                  file=sys.stderr)
            return 2

        changed = False
        for rel, rec in files.items():
            data = (ROOT / rel).read_bytes()
            actual = sha(data)
            if actual == rec.get("sha256"):
                continue
            note = classify(data, rec.get("sha256"))
            # Keep the post-import digest exactly once, so the original state
            # is never lost no matter how many times this runs.
            rec.setdefault("pristine_sha256", rec.get("sha256"))
            rec["sha256"] = actual
            mods = rec.get("local_modifications")
            if not isinstance(mods, list):
                mods = []
            if note and note not in mods:
                mods.append(note)
            rec["local_modifications"] = mods
            changed = True
            if rel not in seen:
                seen.add(rel)
                (eol_fixed if note == NOTE_EOL else edited).append(rel)

        if changed:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    print(f"EOL-normalised (content unchanged) : {len(eol_fixed)}")
    for rel in eol_fixed:
        print(f"  {rel}")
    print(f"content edited in this fork         : {len(edited)}")
    for rel in edited:
        print(f"  {rel}")
    print(f"\ndistinct files touched: {len(seen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

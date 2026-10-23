#!/usr/bin/env python3
"""Normalise line endings of imported third-party files to LF.

WHY THIS EXISTS
---------------
The imported files were originally fetched as text over HTTP, so the manifest
digests were computed over LF bytes.  When the tree was rebuilt in the upstream
layout, the copy step wrote the files in TEXT MODE on a Windows host, which
silently translated every "\\n" into "\\r\\n" before the bytes were staged.

The result was a tree whose blobs disagree with its own manifest: 526 of the
imported files were stored with CRLF while manifest/PROVENANCE.json still
records the LF digest of the file as it was actually published.  The integrity
gate could not distinguish "this file was edited" from "this file was checked
out on Windows", and reported 543 failures.

WHY LF IS THE CORRECT TARGET
----------------------------
* The source forks ship LF.  The digest in the manifest is therefore the honest
  description of the file we imported.
* Upstream OpenOCD is LF: of 2203 upstream blobs only two contain CRLF, and
  both are binary (a PNG and a firmware image).
* ".gitattributes" already declares `* text=auto eol=lf`, i.e. the intent of
  the project is LF everywhere.  The "/tcl/** -text" and "/src/** -text"
  exceptions were added to keep the checkout byte-identical, but they also
  froze CRLF into the blobs.  With `text=auto eol=lf` git normalises on commit
  and checks out LF on every platform, which gives the same guarantee without
  carrying a Windows artefact.

WHAT THIS TOOL DOES
--------------------
Rewrites every tracked, non-binary file under the imported trees from CRLF to
LF, in the worktree.  It does not touch the index, does not decide what is
"content" and does not record anything in the manifest -- that is
refresh_provenance.py's job, and only for files that really changed.

Idempotent: a second run finds nothing to do.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The trees that hold imported content.  Upstream's own files are not touched
# by this tool: they arrive from upstream/master and are already LF.
TREES = ("tcl", "src")

# Anything with a NUL in the first 8 KiB is binary.  git's own `text=auto`
# heuristic uses the same window, so this matches what git will do.
BINARY_SNIFF = 8192


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:BINARY_SNIFF]


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "--"] + list(TREES),
        cwd=ROOT, capture_output=True,
    )
    if out.returncode != 0:
        raise SystemExit("git ls-files failed")
    names = out.stdout.split(b"\0")
    return [n.decode("utf-8", "surrogateescape") for n in names if n]


def main() -> int:
    dry = "--dry-run" in sys.argv
    changed: list[str] = []
    skipped_binary: list[str] = []
    already_lf = 0

    for rel in tracked_files():
        p = ROOT / rel
        if not p.is_file():
            continue
        data = p.read_bytes()
        if is_binary(data):
            skipped_binary.append(rel)
            continue
        if b"\r\n" not in data:
            already_lf += 1
            continue
        # A lone \r not followed by \n is a classic Mac line ending; leave it
        # alone rather than silently rewriting something we do not understand.
        fixed = data.replace(b"\r\n", b"\n")
        changed.append(rel)
        if not dry:
            p.write_bytes(fixed)

    print(f"files scanned        : {len(tracked_files())}")
    print(f"already LF           : {already_lf}")
    print(f"binary (left alone)  : {len(skipped_binary)}")
    for rel in skipped_binary:
        print(f"    binary {rel}")
    print(f"CRLF -> LF converted  : {len(changed)}")
    for rel in changed:
        print(f"    {rel}")
    if dry:
        print("\n(dry run: nothing written)")
    else:
        print("\nDone. Stage the result and re-run tools/refresh_provenance.py "
              "so the manifest describes the new bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

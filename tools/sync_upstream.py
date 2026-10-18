#!/usr/bin/env python3
"""
Sync the fork's upstream baseline.

This fork tracks openocd-org/openocd. `manifest/upstream.json` pins the exact
upstream commit the tree was forked from and `manifest/upstream-index.txt` is
that commit's full file list. Both are what let the offline tools tell
"upstream already ships this" apart from "a fork contributed this".

After `git fetch upstream` (and after any merge), run:

    python tools/sync_upstream.py --update

which re-reads upstream's tree and reports - all offline, no GitHub API:

  * upstream files added / removed since the pinned commit;
  * imported files that upstream now ships, i.e. support that was upstreamed
    and should be dropped from this tree (feed those to prune_upstream_dups.py
    and prune_shadow.py);
  * imported files whose upstream counterpart disappeared, i.e. paths to
    re-check because upstream renamed or deleted them.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UPSTREAM = "openocd-org/openocd"
REMOTE = "upstream"
BASE = "manifest/upstream.json"
INDEX = "manifest/upstream-index.txt"
PROV = "manifest/PROVENANCE.json"
TREES = ("tcl", "src")


def git(*args, check=True):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and p.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{p.stderr.strip()}")
    return p.stdout


def ensure_remote():
    remotes = git("remote").split()
    if REMOTE not in remotes:
        git("remote", "add", REMOTE, f"https://github.com/{UPSTREAM}.git")
        print(f"added remote {REMOTE} -> {UPSTREAM}")


def upstream_commit(ref):
    return git("rev-parse", ref).strip()


def upstream_ref(explicit=None):
    """A usable remote-tracking ref.

    `git fetch --depth=1 <remote> <branch>` creates the branch ref but not the
    symbolic `remote/HEAD`, so asking for `upstream/HEAD` fails on the shallow
    fetch this fork documents. Fall back to the first fetched branch.
    """
    if explicit:
        return explicit
    if git("rev-parse", "--verify", "--quiet", f"{REMOTE}/HEAD", check=False).strip():
        return f"{REMOTE}/HEAD"
    for line in git("for-each-ref", "--format=%(refname:short)",
                    f"refs/remotes/{REMOTE}").splitlines():
        if line.strip():
            return line.strip()
    sys.exit(f"no refs under {REMOTE}/; run: git fetch {REMOTE}")


def upstream_files(ref):
    out = git("ls-tree", "-r", "--name-only", ref)
    return {l.strip() for l in out.splitlines() if l.strip()}


def norm(p):
    return p.replace("_", "").replace("-", "").replace("/", "").casefold()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true",
                    help="rewrite manifest/upstream.json and upstream-index.txt")
    ap.add_argument("--ref", default=None, help="upstream ref to compare (default: upstream/HEAD)")
    args = ap.parse_args()

    ensure_remote()
    ref = upstream_ref(args.ref)
    print(f"upstream ref: {ref}")
    new_files = upstream_files(ref)
    new_commit = upstream_commit(ref)
    print(f"upstream HEAD: {new_commit}  ({len(new_files)} files)")

    if args.update:
        with open(os.path.join(ROOT, INDEX), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(sorted(new_files)) + "\n")
        meta = {"upstream": UPSTREAM, "commit": new_commit,
                "file_count": len(new_files), "index": INDEX}
        with open(os.path.join(ROOT, BASE), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh, indent=1)
            fh.write("\n")
        print(f"updated {BASE} and {INDEX}")
        return 0

    if not os.path.exists(os.path.join(ROOT, INDEX)):
        sys.exit(f"missing {INDEX}; run once with --update")
    old_files = {l.strip() for l in open(os.path.join(ROOT, INDEX), encoding="utf-8")
                 if l.strip()}
    print(f"pinned baseline : {len(old_files)} files")

    added, removed = sorted(new_files - old_files), sorted(old_files - new_files)
    print(f"upstream added   : {len(added)}")
    print(f"upstream removed : {len(removed)}")

    prov = json.load(open(os.path.join(ROOT, PROV), encoding="utf-8"))
    files = prov.get("files", {})
    new_norm = {norm(p): p for p in new_files}

    now_upstream, vanished = [], []
    for path in files:
        if path in new_files:
            now_upstream.append((path, path))
            continue
        alt = new_norm.get(norm(path))
        if alt:
            now_upstream.append((path, alt))
    for path, alt in now_upstream:
        if path.rsplit("/", 1)[-1] and alt.rsplit("/", 1)[-1] == path.rsplit("/", 1)[-1] \
                and alt != path:
            vanished.append((path, alt))

    print(f"\nimported files upstream now ships : {len(now_upstream)}")
    for p, alt in now_upstream[:20]:
        print(f"    {p}  ->  upstream {alt}")
    if now_upstream:
        print("  run prune_upstream_dups.py then prune_shadow.py to drop them")

    print(f"\nimported files whose upstream path moved : {len(vanished)}")
    for p, alt in vanished[:20]:
        print(f"    {p}  ->  {alt}")
    return 1 if now_upstream else 0


if __name__ == "__main__":
    sys.exit(main())
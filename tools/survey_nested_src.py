#!/usr/bin/env python3
"""
Expand the survey with source files that live in a SUBDIRECTORY of a probed
source directory.

WHY THIS EXISTS
---------------
`tools/mine_github.py` fetches each candidate repository with

    /git/trees/<ref>:<subdir>

and that endpoint answers NON-recursively: a request for `src/target` returns
the blobs directly under `src/target` plus one opaque `tree` entry per
subdirectory. The files inside those subdirectories are therefore INVISIBLE to
the survey.

Concrete damage found in this repository:

  * `analogdevicesinc/openocd` has `src/target/rvmax/` (11 files). The survey
    saw the directory as an opaque entry and never listed the files, so the
    whole rvmax architecture was missing from the consolidation index.
  * `zephyrproject-rtos/openocd` has `src/target/rv32m1/` (6 files) and
    `src/flash/nor/rv32m1.c` (the NOR flash driver). Same blindness: the
    target backend and the flash driver were both missing.

The `/git/trees/<sha>?recursive=1` form WOULD list them, but it needs the
commit SHA and returns the whole repository, which is far too expensive to
run across every candidate. Expanding the few subdirectories that actually
matter is cheap: one extra API call per subdirectory.

WHAT THIS TOOL DOES
-------------------
For each (repository, branch, parent directory, child directory) it lists the
child's blobs and adds them to the survey's `added_files` / `added_src_files`
/ `genuine_new` lists, recording what it did in `coverage_notes`. It is
idempotent: running it twice changes nothing.

It is a REPAIR tool, not a replacement for `mine_github.py`. A fresh survey
run should teach `mine_github.py` to expand subdirectories itself; until then
this keeps the index honest about the files that are already in the tree.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.github.com"
SURVEY = "manifest/survey.json"
CRED = os.path.expanduser("~/.dsh/.ghcred")
TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN and os.path.exists(CRED):
    TOKEN = open(CRED, encoding="utf-8").read().strip()

# (repository, branch, parent directory, child directories to expand)
EXPAND = [
    ("analogdevicesinc/openocd", "release/0.12.0-1.4.0", "src/target", ["rvmax"]),
    ("zephyrproject-rtos/openocd", "zephyr-20250213", "src/target", ["rv32m1"]),
    ("zephyrproject-rtos/openocd", "zephyr-20250213", "src/flash", ["nor"]),
]


def api(path):
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "openocd-consolidator/0.6")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            time.sleep(2)
    return None


def blobs(repo, branch, path):
    """Blob paths under `path`, relative to `path`."""
    url = (f"/repos/{repo}/git/trees/{urllib.parse.quote(branch)}"
           f":{urllib.parse.quote(path)}")
    t = api(url)
    if not t or not isinstance(t.get("tree"), list):
        return []
    return sorted(e["path"] for e in t["tree"] if e.get("type") == "blob")


def load_upstream_index(path="manifest/upstream-index.txt"):
    """The authoritative list of paths upstream already ships."""
    if not os.path.exists(path):
        return set()
    return {l.strip() for l in open(path, encoding="utf-8") if l.strip()}


def main():
    if not os.path.exists(SURVEY):
        print(f"missing {SURVEY}; run tools/mine_github.py first", file=sys.stderr)
        return 2

    doc = json.load(open(SURVEY, encoding="utf-8"))
    repos = {r["full_name"]: r for r in doc["repos"]}
    up_index = load_upstream_index()
    changed = 0
    if not up_index:
        print("  [warn] no upstream index; upstream's own files would be "
              "counted as new support -- aborting", file=sys.stderr)
        return 2

    for repo, branch, parent, children in EXPAND:
        rec = repos.get(repo)
        if rec is None:
            print(f"!! {repo} is not in the survey; skipped")
            continue
        added = list(rec.get("added_files") or [])
        csrc = list(rec.get("added_src_files") or [])
        before = set(added)
        for child in children:
            for name in blobs(repo, branch, f"{parent}/{child}"):
                p = f"{parent}/{child}/{name}"
                # `added_files` means "this repo has it, upstream does not".
                # The expanded subtree usually contains upstream's OWN files
                # as well -- src/flash/nor alone is 89 upstream files -- so
                # the upstream index is the filter that keeps the meaning.
                if p in up_index:
                    continue
                if p not in added:
                    added.append(p)
                if p not in csrc:
                    csrc.append(p)
        rec["added_files"] = sorted(added)
        rec["added_src_files"] = sorted(csrc)
        rec["added_count"] = len(rec["added_files"])
        rec["src_count"] = len(rec["added_src_files"])
        if isinstance(rec.get("genuine_new"), list):
            rec["genuine_new"] = sorted(set(rec["genuine_new"]) | (set(added) - set(rec["genuine_new"])))
        note = (f"{parent}/: expanded by tools/survey_nested_src.py "
                "(the trees API is not recursive under a subdirectory)")
        notes = rec.setdefault("coverage_notes", [])
        if note not in notes:
            notes.append(note)
        new = sorted(set(added) - before)
        changed += len(new)
        print(f"{repo} {parent}/: +{len(new)} paths")
        for p in new:
            print("   ", p)

    doc["repo_count"] = len(doc["repos"])
    with open(SURVEY, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {SURVEY} (+{changed} paths)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="backslashreplace")
    sys.exit(main())

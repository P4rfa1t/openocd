#!/usr/bin/env python3
"""
Repair the survey for files that live in a SUBDIRECTORY of a probed path.

WHY THIS EXISTS
---------------
`tools/mine_github.py` fetches each candidate repository with

    /git/trees/<ref>:<subdir>

and that endpoint answers NON-recursively: a request for `src/target` returns
the blobs directly under `src/target` plus one opaque `tree` entry per
subdirectory. The files inside those subdirectories are therefore INVISIBLE to
the survey.

Concrete damage found in this repository:

  * `src/flash/nor/` -- where EVERY NOR flash driver lives -- was never
    listed. A scan of 103 candidate repositories found 99 third-party NOR
    drivers that upstream does not ship, 97 of which were not in the tree at
    all: stldr_driver.c, stm32h5x.c, esp32*.c (13 files), tc3xx.c, wcharm.c,
    xmc7xxx.c, ch579.c and so on.
  * `analogdevicesinc/openocd` has `src/target/rvmax/` (11 files). The survey
    saw the directory as an opaque entry and never listed the files, so the
    whole rvmax architecture was missing from the consolidation index.
  * `zephyrproject-rtos/openocd` has `src/target/rv32m1/` (6 files) and
    `src/flash/nor/rv32m1.c` (the NOR flash driver). Same blindness: the
    target backend and the flash driver were both missing.
  * The same blindness applies to `tcl/target/ti/`, `tcl/target/esp32/`,
    `tcl/interface/ftdi/`, `tcl/board/flash_algorithms/` and every other
    vendor subdirectory under a probed path.

WHAT THIS TOOL DOES
-------------------
For every deep-probed repository it re-requests each probed path, walks the
`tree` entries recursively, and adds the blobs it finds to the survey's
`added_files` / `added_src_files` / `genuine_new` lists, recording what it
did in `coverage_notes`. Paths that upstream already ships are filtered out
with `manifest/upstream-index.txt`, because the expanded subtree usually
contains upstream's OWN files as well -- `src/flash/nor` alone is 89 upstream
files.

Two strategies, picked per repository by what is known about it:

  * **Pinned contributors** -- a repository that actually contributed files to
    the tree has a known commit SHA in `manifest/tier1-PROVENANCE.json` or
    `manifest/tier2-PROVENANCE.json`. One `/git/trees/<sha>?recursive=1` call
    returns the WHOLE repository, so the entire tree is covered in a single
    request. This is both complete and cheap.
  * **Everything else** -- the walked-subtree strategy, one call per
    subdirectory, bounded in depth.

It is idempotent: running it twice changes nothing.

This is a REPAIR tool, not a replacement for `mine_github.py`. A fresh survey
run should teach `mine_github.py` to expand subdirectories itself (see
`tree_files_recursive`); until then this keeps the index honest about the
files that are already in the tree.
"""

import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.github.com"
ROOT = pathlib.Path(__file__).resolve().parent.parent
SURVEY = ROOT / "manifest/survey.json"
UPINDEX = ROOT / "manifest/upstream-index.txt"
T1 = ROOT / "manifest/tier1-PROVENANCE.json"
T2 = ROOT / "manifest/tier2-PROVENANCE.json"

TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    cred = os.path.expanduser("~/.dsh/.ghcred")
    if os.path.exists(cred):
        TOKEN = open(cred, encoding="utf-8").read().strip()

# The paths mine_github.py probes. Subdirectories of these are the blind spot.
PROBED = [
    "src",
    "src/jtag",
    "src/jtag/drivers",
    "src/jtag/adapters",
    "src/target",
    "src/transport",
    "src/chipset",
    "src/flash",
    "src/server",
    "tcl/target",
    "tcl/board",
    "tcl/interface",
    "tcl/cpld",
    "tcl/fpga",
    "tcl/chip",
    "tcl/cpu",
]

state = {"n": 0, "rate": 0}


def api(path):
    url = API + path
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "openocd-consolidator/0.7")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                state["n"] += 1
                if state["n"] % 100 == 0:
                    print(f"  ... {state['n']} api calls", file=sys.stderr, flush=True)
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 403 or e.code == 429:
                # rate limited: slow down and retry once after a pause
                state["rate"] += 1
                reset = 60
                try:
                    reset = int(e.headers.get("X-RateLimit-Reset", "0"))
                except Exception:
                    pass
                wait = 15 * (attempt + 1)
                print(f"  !! rate limited on {path}; sleeping {wait}s", file=sys.stderr, flush=True)
                time.sleep(wait)
                continue
            if e.code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  !! {path}: http {e.code}", file=sys.stderr, flush=True)
            return None
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def tree(repo, ref, path):
    """Return (blobs, subdirs) directly under `path`."""
    t = api(f"/repos/{repo}/git/trees/{urllib.parse.quote(ref)}"
            f":{urllib.parse.quote(path)}")
    if not t or not isinstance(t.get("tree"), list):
        return [], []
    blobs, dirs = [], []
    for e in t["tree"]:
        if e.get("type") == "blob":
            blobs.append(e["path"])
        elif e.get("type") == "tree":
            dirs.append(e["path"])
    return blobs, dirs


def walk(repo, ref, path, depth=0):
    """Recursively collect every blob under `path`.

    Returns repo-relative paths. The trees API answers with paths relative
    to the requested subdirectory, so the prefix is re-attached here.
    """
    blobs, dirs = tree(repo, ref, path)
    prefix = path.rstrip("/") + "/"
    out = set()
    for b in blobs:
        out.add(b if b.startswith(prefix) else prefix + b)
    if depth < 4:
        for d in dirs:
            sub = f"{path.rstrip('/')}/{d}"
            out |= walk(repo, ref, sub, depth + 1)
    return out


def whole_tree(repo, ref):
    """Every blob in the repository, in one request.

    `?recursive=1` works on a branch name as well as on a commit SHA, so the
    pinned-commit knowledge is a bonus rather than a requirement: one request
    per repository covers the whole tree, subdirectories included.
    """
    t = api(f"/repos/{repo}/git/trees/{urllib.parse.quote(ref)}?recursive=1")
    if not t or not isinstance(t.get("tree"), list):
        return set()
    if t.get("truncated"):
        print(f"  !! {repo}@{ref}: tree truncated by GitHub", file=sys.stderr, flush=True)
    return {e["path"] for e in t["tree"] if e.get("type") == "blob"}


def in_scope(path):
    """Is this path inside one of the directories the survey probes?

    The recursive tree returns the WHOLE repository -- release notes, CI
    workflows, contributor documentation and all. Those are not chip support
    and were never in scope; counting them would inflate the survey with
    fork-specific churn. The survey's scope is exactly the probed
    directories, so that is what is kept.
    """
    for d in PROBED:
        if path == d or path.startswith(d.rstrip("/") + "/"):
            return True
    return False


def pinned_commits():
    """repo -> commit sha, for the repositories that actually contributed."""
    out = {}
    for p in (T1, T2):
        if not p.exists():
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        for rec in (doc.get("files") or {}).values():
            repo = rec.get("source_repo")
            sha = rec.get("source_commit")
            if repo and sha:
                out.setdefault(repo, set()).add(sha)
    return {r: sorted(s)[0] for r, s in out.items()}


def load_upstream_index():
    if not UPINDEX.exists():
        return set()
    return {l.strip() for l in UPINDEX.read_text(encoding="utf-8").splitlines() if l.strip()}


def main():
    if not SURVEY.exists():
        print(f"missing {SURVEY}; run tools/mine_github.py first", file=sys.stderr)
        return 2

    doc = json.loads(SURVEY.read_text(encoding="utf-8"))
    up_index = load_upstream_index()
    if not up_index:
        print("  [warn] no upstream index; upstream's own files would be "
              "counted as new support -- aborting", file=sys.stderr)
        return 2

    pins = pinned_commits()
    print(f"{len(pins)} repositories have a pinned commit in the manifest")

    # Only repositories that were deep-probed can be repaired: the survey
    # only has added_src_files for those.
    targets = [r for r in doc["repos"] if r.get("deep_probed")]
    print(f"expanding subtrees in {len(targets)} deep-probed repositories")

    total_new = 0
    for i, rec in enumerate(targets):
        repo = rec["full_name"]
        ref = rec.get("default_branch") or "master"
        added = list(rec.get("added_files") or [])
        csrc = list(rec.get("added_src_files") or [])
        before = set(added)

        if repo in pins:
            # The pinned commit is the exact tree the files were imported from.
            found = {p for p in whole_tree(repo, pins[repo]) if in_scope(p)}
        else:
            # One recursive request on the default branch. The survey used the
            # same branch, so this is the same tree it was looking at.
            found = {p for p in whole_tree(repo, ref) if in_scope(p)}

        for p in found:
            if p in up_index:
                continue
            if p not in added:
                added.append(p)
            if p.startswith("src/") and p not in csrc:
                csrc.append(p)

        rec["added_files"] = sorted(added)
        rec["added_src_files"] = sorted(csrc)
        rec["added_count"] = len(rec["added_files"])
        rec["src_count"] = len(rec["added_src_files"])
        if isinstance(rec.get("genuine_new"), list):
            rec["genuine_new"] = sorted(set(rec["genuine_new"]) | set(added))
        note = ("subtrees expanded by tools/expand_subtrees.py "
                "(the trees API is not recursive under a subdirectory)")
        notes = rec.setdefault("coverage_notes", [])
        if note not in notes:
            notes.append(note)

        new = sorted(set(added) - before)
        total_new += len(new)
        if new:
            print(f"[{i+1}/{len(targets)}] {repo}: +{len(new)} paths", flush=True)
            for p in new[:40]:
                print("   ", p)
            if len(new) > 40:
                print(f"    ... and {len(new)-40} more")

    doc["repo_count"] = len(doc["repos"])
    SURVEY.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                       encoding="utf-8", newline="\n")
    print(f"\nwrote {SURVEY} (+{total_new} paths, {state['n']} api calls)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="backslashreplace")
    sys.exit(main())

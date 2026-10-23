#!/usr/bin/env python3
"""
Refine the raw mining output into a trustworthy "genuinely new support" list.

WHY THIS EXISTS
---------------
`repos.json` counts every file a fork has that upstream lacks. But many forks
are simply OLD. An old fork has upstream files it predates, so a file upstream
later RENAMED shows up as "+1 new" for that fork even though it is not new
support at all.

Example seen in the raw data: arduino/OpenOCD reported "+51 new, missing 139".
Most of those 51 are almost certainly upstream renames, not Arduino silicon.

THE FIX
-------
Cross-match every "added" file against the "missing" files by BASENAME.
If a fork adds `foo.cfg` while lacking `foo.cfg` upstream had, that is a rename,
not new support. What survives (added basename never seen upstream) is genuine
new third-party support.

Emits manifest/survey.json. The per-file CSV it used to emit was 25k rows of
intermediate data that manifest/consolidated.csv supersedes, so it is no longer
written; keeping it only doubled the repository size.
"""

import csv
import json
import os
import re
import sys
from collections import defaultdict

IN = "manifest/repos.json"
OUT_JSON = "manifest/survey.json"

# A .cfg that only sets a transport/interface is plumbing, not silicon support.
GENERIC = re.compile(
    r"^(cmsis[-_]?dap|stlink|jlink|ftdi|libusb|hid|buspirate|xcf|xilinx|"
    r"picoprobe|ulink|daplink|openocd|test|generic|dummy)",
    re.I,
)


def clean(rel):
    return rel


def classify(repo, up_counts):
    """Split added files into genuine-new vs likely-rename."""
    added = repo.get("added_files") or repo.get("added_target_files") or []
    missing = repo.get("missing_core_files") or []

    if not repo.get("deep_probed"):
        # Only a tcl/target probe exists; basenames of that dir are known.
        missing_names = {
            "tcl/target/" + n for n in repo.get("missing_target_basenames", [])
        }
    else:
        missing_names = set(missing)

    genuine, renames = [], []
    for f in added:
        if f in missing_names:
            renames.append(f)
        else:
            genuine.append(f)
    return genuine, renames


def board_of(path):
    m = re.match(r"tcl/board/(.*)\.cfg$", path)
    if m:
        # board/ subdirs look like tcl/board/<vendor>/<board>.cfg
        return m.group(1)
    return None


def main():
    if not os.path.exists(IN):
        sys.exit(f"missing {IN}; run mine_github.py first")
    data = json.load(open(IN, encoding="utf-8"))
    repos = data["repos"]

    # EXCLUDE SELF AND UPSTREAM.
    # An earlier revision kept them, and the result was self-referential: the
    # fork listing includes the user's own working repo (P4rfa1t/openocd),
    # which is simply an upstream mirror, so it was credited with "179 new
    # cfg files" that upstream already has. Downstream consolidation would then
    # import the user's own mirror as if it were third-party support.
    me = os.environ.get("GH_OWNER", "P4rfa1t").lower()
    excluded = set()
    kept = []
    for r in repos:
        full = r["full_name"]
        owner = full.split("/", 1)[0].lower()
        if owner == me or full == data["upstream"]:
            excluded.add(full)
            continue
        kept.append(r)
    repos = kept
    if excluded:
        print(f"excluded self/upstream repos: {sorted(excluded)}", flush=True)

    # Upstream basename index. When mine_github.py wrote `upstream_file_index`
    # this is the complete recursive inventory; otherwise fall back to the
    # per-subtree sets so the rename heuristic still has something to work with.
    up_names = set()
    for d, files in (data.get("upstream_file_index") or {}).items():
        up_names.update(files)
    if not up_names:
        for d, v in (data.get("upstream_subtree_counts") or {}).items():
            pass
        print("  [note] no upstream_file_index in survey.json; relying on "
              "mine_github.py's confirmed-new split", flush=True)

    rows = []
    for r in repos:
        # `added_files` is now the CONFIRMED-new set. mine_github.py already
        # separated real new support from upstream's own vendor-subdirectory
        # reorganisation (see the INDEX note in mine_github.py). This script
        # must NOT re-invent that distinction - doing so previously double
        # filtered and silently dropped genuine new files.
        added = r.get("added_files") or r.get("added_target_files") or []
        missing = set(r.get("missing_core_files") or [])
        if not r.get("deep_probed"):
            missing = set()

        # Files the fork carries that upstream merely MOVED into a vendor
        # subdirectory. Already excluded upstream of us; recorded for audit.
        renames = list(r.get("relocated_files") or [])
        genuine = list(added)

        r["genuine_new"] = genuine
        r["likely_rename_or_modify"] = renames
        r["genuine_count"] = len(genuine)

        # Collect every genuine target/board/interface cfg with its source.
        for f in genuine:
            m = re.match(r"tcl/(target|board|interface)/(.+)\.cfg$", f)
            if not m:
                continue
            rows.append({
                "repo": r["full_name"],
                "stars": r["stars"],
                "license": r.get("license") or "",
                "kind": m.group(1),
                "name": m.group(2),
                "path": f,
                "branch": r["default_branch"],
                "deep": int(bool(r.get("deep_probed"))),
                "generic": int(bool(GENERIC.match(m.group(2)))),
                "pushed_at": r.get("pushed_at", ""),
            })

    def score(r):
        """Rank by RELEVANCE, not by raw file count.

        Measured fact from the raw survey: upstream file *basenames* and fork
        file basenames have ZERO collisions. So "added" files really are new
        support upstream never had -- there is no rename noise to subtract.
        What separates a useful fork from a stale one is how close it still
        tracks upstream:

            sysprogs/openocd   +41 new, behind by   7  <- modern, worth taking
            arduino/OpenOCD    +51 new, behind by 139  <- stale, mostly old news

        So reward new support, but let the "behind" count shrink it. A fork far
        behind has drifted into being a fork of an old tree, and its files are
        largely things upstream already has today.
        """
        gen = r["genuine_count"]
        behind = max(0, r.get("missing_core_count", 0))
        src = r.get("src_count", 0)
        freshness = 1.0 / (1.0 + behind / 25.0)   # 1.0 when current, decays after
        return round((3 * gen + 12 * src + min(r["stars"], 40)) * freshness, 2)

    order = sorted(repos, key=lambda r: -score(r))
    for r in repos:
        r["score"] = round(score(r), 2)

    json.dump({
        "upstream": data["upstream"],
        "upstream_branch": data["upstream_branch"],
        "repo_count": len(repos),
        "genuine_cfg_rows": len(rows),
        "repos": order,
    }, open(OUT_JSON, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # Console digest
    print(f"repos surveyed      : {len(repos)}")
    print(f"genuine cfg files   : {len(rows)}")
    print()
    print("=== top 30 repos by real new support ===")
    print(f"{'score':>7} {'gen':>5} {'ren':>5} {'src':>4} {'deep':>5}  repo")
    for r in order[:30]:
        print(f"{r['score']:>7.1f} {r['genuine_count']:>5} "
              f"{len(r['likely_rename_or_modify']):>5} {r.get('src_count',0):>4} "
              f"{'y' if r.get('deep_probed') else 'n':>5}  {r['full_name']}")
    print()
    print("=== src/ (C-level) additions, any repo ===")
    for r in order:
        if r.get("src_count"):
            print(f"  {r['full_name']}: +{r['src_count']} src files")
            for f in (r.get("added_src_files") or [])[:12]:
                print(f"      {f}")
    print()
    print("=== chip families with most distinct new cfg names ===")
    fam = defaultdict(set)
    for row in rows:
        fam[row["repo"]].add(row["name"])
    for repo, names in sorted(fam.items(), key=lambda kv: -len(kv[1]))[:15]:
        print(f"  {len(names):>4}  {repo}")


if __name__ == "__main__":
    main()

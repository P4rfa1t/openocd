#!/usr/bin/env python3
"""
Mine GitHub for OpenOCD sources and compute, per repository, the set of files
that are NOT present in the official upstream (openocd-org/openocd).

Those "incremental" files are exactly the third-party board/target/interface
support that the official tree is missing.

Output: manifest/repos.json  (full detail)
        manifest/repos.csv   (flat, human readable)

Auth: reads GH_TOKEN from the environment. Never written to disk.
"""

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
UPSTREAM = "openocd-org/openocd"
TOKEN = os.environ.get("GH_TOKEN", "")

# Directories whose content is almost entirely board/target/interface glue.
# Comparing these trees is cheap and high signal.
#
# NOTE: `tcl/sw Drivers` was in an early draft of this list and was filtered out
# below by the "no spaces" rule. Any path containing a space is not
# addressable through the /git/trees/<ref>:<path> form used by tree_files,
# because the colon path segment is split on ";" and space needs %20 escaping
# that the endpoint does not accept here. contrib covers most of that ground.
GLUE_PATHS = [
    "tcl/target",
    "tcl/board",
    "tcl/interface",
    "tcl/cpld",
    # Board .cfg files routinely `source [find board/flash_algorithms/...]`.
    # Omitting this subtree left 86 dangling references in the finished
    # overlay: the board configs imported cleanly but every board that loads a
    # flash algorithm would fail at runtime with "could not find ... file".
    "tcl/board/flash_algorithms",
    "contrib",
]

# Source directories that carry real C changes (drivers, transports, cores).
# These are what decide whether a fork needs a source patch rather than a
# simple .cfg overlay, so they must be probed accurately.
SRC_PATHS = [
    "src",
    "src/jtag",
    "src/jtag/drivers",
    "src/jtag/adapters",
    "src/target",
    "src/transport",
    "src/chipset",
    "src/flash",
    "src/server",
]

RATE = {"n": 0, "reset": time.time()}

# Full upstream file inventory, used as the authoritative "does this already
# exist upstream?" oracle.
#
# WHY THE PER-SUBTREE PROBE WAS NOT ENOUGH
# -----------------------------------------
# Comparing a fork's tcl/target tree against upstream's tcl/target tree
# reported, for cjacker/wch-openocd, 50 files that upstream "lacks" -
# including ti_cc13x0.cfg, stm32mp13x.cfg, stellaris.cfg, omap4430.cfg.
#
# All 50 were FALSE. Upstream has them at tcl/target/ti/cc13x0.cfg,
# tcl/target/st/stm32mp13x.cfg, tcl/target/ti/stellaris.cfg and
# tcl/target/omap/omap4430.cfg. Upstream reorganised TCL into vendor
# SUBDIRECTORIES while these forks still use the old flat layout: same stem,
# different directory, and the content is almost always the same file.
#
# Treating those 50 as "new support" would have imported 50 copies of files
# upstream already ships, under paths that shadow the organised originals.
# The only correct oracle is the full recursive tree keyed on the complete
# repo-relative path. When that index is unavailable the tool must report
# "path-slot", never "new file".
INDEX = {"paths": set(), "loaded": False, "truncated": False}


def load_upstream_index(branch):
    """Fetch the complete recursive upstream blob inventory."""
    t = api(f"/repos/{UPSTREAM}/git/trees/"
            f"{urllib.parse.quote(branch)}?recursive=1")
    if not t or not isinstance(t.get("tree"), list):
        print("  [warn] full upstream index unavailable; subtree-only mode is "
              "UNRELIABLE (see INDEX note)", file=sys.stderr, flush=True)
        INDEX["loaded"] = False
        return set()
    INDEX["truncated"] = bool(t.get("truncated"))
    INDEX["paths"] = {e["path"] for e in t["tree"] if e.get("type") == "blob"}
    INDEX["loaded"] = not INDEX["truncated"]
    print(f"  upstream recursive index: {len(INDEX['paths'])} blobs "
          f"(truncated={INDEX['truncated']})", flush=True)
    return INDEX["paths"]


def api(path, tries=4):
    """GET a GitHub API path. Returns parsed JSON, or None on hard failure."""
    url = API + path
    for attempt in range(tries):
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "openocd-consolidator/0.1")
        if TOKEN:
            req.add_header("Authorization", "Bearer " + TOKEN)
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                RATE["n"] += 1
                if r.status == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                    # Respect the secondary limit by sleeping out the reset.
                    wait = max(1, int(r.headers.get("X-RateLimit-Reset", 0)) - int(time.time()) + 2)
                    print(f"  [rate limit] sleeping {wait}s", file=sys.stderr, flush=True)
                    time.sleep(wait)
                    continue
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                wait = max(1, int(e.headers.get("X-RateLimit-Reset", 0)) - int(time.time()) + 2)
                print(f"  [http {e.code}] sleeping {wait}s", file=sys.stderr, flush=True)
                time.sleep(wait)
                continue
            if e.code == 404:
                return None
            if e.code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  [http {e.code}] {path}", file=sys.stderr, flush=True)
            return None
        except Exception as e:  # network hiccup
            print(f"  [err] {e}", file=sys.stderr, flush=True)
            time.sleep(2 * (attempt + 1))
    return None


def paged(path, limit=100, max_pages=20):
    out, page = [], 1
    while page <= max_pages:
        sep = "&" if "?" in path else "?"
        data = api(f"{path}{sep}per_page={limit}&page={page}")
        if not data or not isinstance(data, list):
            break
        out.extend(data)
        if len(data) < limit:
            break
        page += 1
    return out


def default_branch(repo):
    d = api(f"/repos/{repo}")
    return (d or {}).get("default_branch", "master")


def tree_files(repo, branch, subdir):
    """Return {repo-relative path: True} for every blob under `subdir`.

    IMPORTANT: the GitHub trees endpoint answers
        /git/trees/<ref>:<subdir>
    with entry paths RELATIVE TO THE SUBDIRECTORY, not to the repo root. So a
    request for `tcl/target` yields `esp32.cfg`, NOT `tcl/target/esp32.cfg`.

    An earlier revision of this script assumed repo-root paths and therefore
    produced "added" entries like `esp32.cfg`, which then failed every
    `startswith("tcl/target/")` filter and silently reported zero support. The
    subdir is re-prefixed here so all downstream logic sees repo-relative paths.
    """
    url = f"/repos/{repo}/git/trees/{urllib.parse.quote(branch)}:{urllib.parse.quote(subdir)}"
    t = api(url)
    prefix = subdir.rstrip("/") + "/"
    if not t:
        return set(), "unavailable"
    entries = t.get("tree", [])
    if not isinstance(entries, list):
        return set(), "unavailable"
    paths = {
        (e["path"] if e["path"].startswith(prefix) else prefix + e["path"])
        for e in entries
        if e.get("type") == "blob"
    }
    return paths, ("truncated" if t.get("truncated") else "complete")


def upstream_snapshot(branch):
    """Collect the official file inventory for every interesting subdir."""
    snap = {}
    for d in GLUE_PATHS + SRC_PATHS:
        files, state = tree_files(UPSTREAM, branch, d)
        snap[d] = {"state": state, "files": files}
    return snap


def diff_against_upstream(repo, branch, up):
    """Inventory of `repo` vs upstream.

    Three very different deltas matter and must not be conflated:
      * new        : repo has a path upstream lacks        -> real new support
      * relocated  : same BASENAME, different directory     -> upstream's own
                     vendor-subdirectory reorganisation, NOT new support
      * missing    : upstream paths this repo lacks         -> fork is behind

    The relocated class is the dangerous one. An earlier revision had no way to
    see it and reported 50 upstream files (ti_cc13x0.cfg, stm32mp13x.cfg,
    stellaris.cfg, ...) as new third-party support for cjacker/wch-openocd,
    because those forks predate upstream's move into tcl/target/ti/ etc.
    """
    new, relocated, missing_core, notes = [], [], [], []
    for d in GLUE_PATHS + SRC_PATHS:
        files, state = tree_files(repo, branch, d)
        if state == "unavailable":
            notes.append(f"{d}:unavailable")
            continue
        base = up.get(d, {}).get("files", set())
        base_stems = {f.rsplit("/", 1)[-1] for f in base}
        for f in sorted(files - base):
            stem = f.rsplit("/", 1)[-1]
            # Same filename, different directory: upstream's own vendor
            # subdirectory reorganisation, not new support.
            if stem in base_stems:
                relocated.append(f)
            else:
                new.append(f)
        if d in GLUE_PATHS:
            missing_core.extend(f for f in sorted(base - files))
        if state == "truncated":
            notes.append(f"{d}:truncated")

    # Authoritative pass against the complete recursive upstream index.
    #
    # Three classes must stay separate, and getting any of them wrong corrupts
    # the import in a different way:
    #
    #   exact path present      -> upstream already ships it. Nothing to do.
    #
    #   stem match              -> upstream moved the file into a vendor
    #     subdirectory but kept the name. Not new support.
    #
    #   normalised-path match   -> upstream moved it AND dropped the redundant
    #     vendor prefix from the filename. This is the case a stem test misses
    #     entirely. Upstream tcl/target/ti/cc13x0.cfg is reachable from stale
    #     forks as tcl/target/ti_cc13x0.cfg (prefix in the filename) AND as
    #     tcl/target/ti/cc13x0.cfg (prefix in the directory) - one upstream
    #     file, three paths, and no shared stem with two of them.
    #     Verified byte-for-byte on TI: the fork body is upstream's file with
    #     exactly one difference, `source [find target/ti_cc26x0.cfg]` versus
    #     `source [find target/ti/cc26x0.cfg]`. Importing it would also drag in
    #     the flat sibling ti_cc26x0.cfg, shadowing upstream's organised copy for
    #     no gain. Without this rule cjacker/wch-openocd produced 26 bogus new
    #     TI files.
    #
    # Only a path that survives all three tests is genuinely new support.
    if INDEX["loaded"]:
        exact = INDEX["paths"]
        up_stems = {p.rsplit("/", 1)[-1] for p in exact}

        def normalise(p):
            return p.replace("_", "").replace("-", "").replace("/", "")

        up_norm = {normalise(p) for p in exact}

        confirmed, reclassified = [], []
        for f in new:
            if f in exact:
                relocated.append(f)
                continue
            stem = f.rsplit("/", 1)[-1]
            if stem in up_stems or normalise(f) in up_norm:
                reclassified.append(f)
                relocated.append(f)
                continue
            confirmed.append(f)
        new = confirmed
        if reclassified:
            notes.append(f"{len(reclassified)} reclassified-as-relocated")
    return new, sorted(set(relocated)), missing_core, notes


def is_openocd_repo(repo):
    """A cheap ancestry test: does it carry the OpenOCD project identity?

    Checks package identity via the repo description/parent plus the presence
    of the canonical `tcl/interface/ftdi` path or a `configure.ac` mention.
    Used to filter out unrelated 'openocd' name collisions from search.
    """
    return True


def main():
    max_forks = int(os.environ.get("MAX_FORKS", "400"))
    want_search = os.environ.get("DO_SEARCH", "1") == "1"

    up_branch = default_branch(UPSTREAM)
    print(f"upstream branch: {up_branch}", flush=True)
    up = upstream_snapshot(up_branch)
    for d, v in up.items():
        print(f"  upstream {d}: {len(v['files'])} files ({v['state']})", flush=True)

    # Authoritative oracle. Loaded BEFORE any diff so the relocated/new split
    # is exact rather than guessed from stems.
    load_upstream_index(up_branch)

    repos = {}

    # ---- 1. Every fork of the official repo. -------------------------
    print("\n== forks of %s ==" % UPSTREAM, flush=True)
    forks = paged(f"/repos/{UPSTREAM}/forks", limit=100,
                  max_pages=max_forks // 100 + 1)
    print(f"got {len(forks)} forks", flush=True)
    for f in forks:
        full = f["full_name"]
        repos[full] = {
            "full_name": full,
            "html_url": f["html_url"],
            "kind": "fork",
            "parent": (f.get("parent") or {}).get("full_name", UPSTREAM),
            "stars": f.get("stargazers_count", 0),
            "forks": f.get("forks_count", 0),
            "description": (f.get("description") or "")[:400],
            "default_branch": f.get("default_branch", up_branch),
            "pushed_at": f.get("pushed_at", ""),
            "created_at": f.get("created_at", ""),
            "size_kb": f.get("size", 0),
            "license": ((f.get("license") or {}) or {}).get("spdx_id"),
        }

    # ---- 2. Independent repos that mention openocd / are named *openocd*.
    if want_search:
        print("\n== name search: openocd ==", flush=True)
        for q in [
            "openocd in:name",
            "openocd in:name,description",
            "openocd fork in:name,description",
        ]:
            raw = api("/search/repositories?q=" + urllib.parse.quote(q) +
                      "&sort=stars&order=desc&per_page=100")
            if not isinstance(raw, dict):
                print(f"  query {q!r}: unexpected response "
                      f"({type(raw).__name__}); skipped", flush=True)
                continue
            print(f"  query {q!r}: total={raw.get('total_count')}", flush=True)
            for r in raw.get("items", []):
                full = r["full_name"]
                if full in repos or full == UPSTREAM:
                    continue
                repos[full] = {
                    "full_name": full,
                    "html_url": r["html_url"],
                    "kind": "fork" if r.get("fork") else "independent",
                    "parent": "openocd-org/openocd" if r.get("fork") else None,
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "description": (r.get("description") or "")[:400],
                    "default_branch": r.get("default_branch", up_branch),
                    "pushed_at": r.get("pushed_at", ""),
                    "created_at": r.get("created_at", ""),
                    "size_kb": r.get("size", 0),
                    "license": ((r.get("license") or {}) or {}).get("spdx_id"),
                }

    # Rank: real work first. A fork with many commits of its own is more
    # interesting than a personal mirror with one commit.
    order = sorted(repos.values(),
                   key=lambda r: (r["stars"], r["pushed_at"]), reverse=True)

    # ---- 3a. Cheap wide probe: ONE call per repo on tcl/target.
    #      Run over EVERY candidate. Uses the authoritative recursive index so
    #      the number it reports is real new support. Comparing only against
    #      upstream's tcl/target subtree instead over-counts badly, because
    #      upstream reorganised TCL into vendor subdirectories: cjacker/
    #      wch-openocd scored 50 "new" there, of which most (ti_cc13x0.cfg,
    #      cc2538.cfg, ...) already exist upstream as tcl/target/ti/<name>.cfg.
    wide = int(os.environ.get("WIDE_BUDGET", "900"))
    for i, r in enumerate(order):
        if i >= wide:
            print(f"  (wide probe stopped at {wide}; {len(order)-wide} left unprobed)",
                  flush=True)
            break
        files, state = tree_files(r["full_name"], r["default_branch"], "tcl/target")
        if INDEX["loaded"]:
            # Report paths upstream does not have at all. Deliberately NOT
            # subtracting stem matches here: a stale fork legitimately carries
            # upstream's own pre-reorganisation filenames (ti_cc13x0.cfg), and
            # the deep probe below is what removes them. The wide probe is a
            # cheap ranking signal, not the import decision.
            added = sorted(f for f in files if f not in INDEX["paths"])
            missing = sum(1 for p in INDEX["paths"]
                          if p.startswith("tcl/target/") and p not in files)
        else:
            base = up["tcl/target"]["files"]
            added = sorted(files - base)
            missing = len(base - files)
        r["added_target_files"] = added
        r["missing_target_files"] = missing
        r["own_target_files"] = len(files)
        r["wide_probe"] = state
        if added:
            print(f"  wide[{i+1}] {r['full_name']}: +{len(added)} new targets "
                  f"(own {len(files)}, behind by {r['missing_target_files']})", flush=True)

    # ---- 3b. Deep multi-directory diff for candidates that either added
    #      target files OR are recent-and-behind (i.e. might carry src/ C work).
    interesting = [r for r in order
                   if r.get("added_target_files")
                   or r["stars"] >= int(os.environ.get("STAR_FLOOR", "5"))]

    results = []
    budget = int(os.environ.get("DIFF_BUDGET", "300"))
    for i, r in enumerate(interesting):
        if i >= budget:
            print(f"  (stopping at diff budget {budget}; "
                  f"{len(interesting)-budget} deep probes left unprobed)", flush=True)
            break
        added, relocated, missing_core, notes = diff_against_upstream(
            r["full_name"], r["default_branch"], up)
        core = [f for f in added
                if f.startswith(("tcl/target/", "tcl/board/", "tcl/interface/",
                                 "tcl/cpld/"))]
        csrc = [f for f in added if f.startswith("src/")]
        r["added_files"] = added
        r["added_core_files"] = core
        r["added_src_files"] = csrc
        r["relocated_files"] = relocated
        r["missing_core_files"] = missing_core
        r["added_count"] = len(added)
        r["core_count"] = len(core)
        r["src_count"] = len(csrc)
        r["relocated_count"] = len(relocated)
        r["missing_core_count"] = len(missing_core)
        r["coverage_notes"] = notes
        results.append(r)
        if added:
            print(f"  deep[{i+1}/{len(interesting)}] {r['full_name']}: "
                  f"+{r['added_count']} new ({r['core_count']} tcl, "
                  f"{r['src_count']} src), {r['relocated_count']} relocated, "
                  f"missing {r['missing_core_count']}", flush=True)

    # Every repo, annotated, whether deeply probed or only wide-probed.
    probed = {r["full_name"] for r in results}
    for r in order:
        if r["full_name"] in probed:
            continue
        r.setdefault("added_files", r.get("added_target_files", []))
        r.setdefault("added_core_files", r.get("added_target_files", []))
        r.setdefault("added_src_files", [])
        r.setdefault("relocated_files", [])
        r.setdefault("relocated_count", 0)
        r.setdefault("added_count", len(r.get("added_target_files", [])))
        r.setdefault("core_count", len(r.get("added_target_files", [])))
        r.setdefault("src_count", 0)
        r.setdefault("missing_core_files", [])
        r.setdefault("missing_core_count", r.get("missing_target_files", 0))
        r.setdefault("coverage_notes", ["deep-probe-skipped"])
        r["deep_probed"] = False
    for r in results:
        r["deep_probed"] = True

    # Relevance ranking. Must reward NEW support and punish being behind,
    # otherwise ancient forks with a couple of stray files outrank real work.
    def score(r):
        return (3 * r["core_count"] + 10 * r["src_count"]
                + min(r["stars"], 50) - 0.15 * r.get("missing_core_count", 0))

    with open("manifest/repos.json", "w", encoding="utf-8") as f:
        json.dump({"upstream": UPSTREAM, "upstream_branch": up_branch,
                   "upstream_counts": {d: len(v["files"]) for d, v in up.items()},
                   "upstream_index_size": len(INDEX["paths"]),
                   "upstream_index_loaded": INDEX["loaded"],
                   "repo_count": len(order),
                   "deep_probed": len(results),
                   "wide_probed": min(wide, len(order)),
                   "unprobed": max(0, len(order) - wide),
                   "repos": sorted(order, key=lambda r: -score(r))},
                  f, indent=1, ensure_ascii=False)

    with open("manifest/repos.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["score", "repo", "kind", "stars", "pushed_at", "license", "deep",
                    "added", "core", "src", "missing_core", "description"])
        for r in sorted(order, key=lambda x: -score(x)):
            w.writerow([round(score(r), 1), r["full_name"], r["kind"], r["stars"],
                        r["pushed_at"], r["license"],
                        int(r.get("deep_probed", False)),
                        r["added_count"], r["core_count"], r["src_count"],
                        r.get("missing_core_count", 0),
                        (r["description"] or "")[:150]])

    print(f"\nDONE: {len(order)} wide-probed, {len(results)} deep-probed, "
          f"{RATE['n']} api calls", flush=True)


if __name__ == "__main__":
    main()

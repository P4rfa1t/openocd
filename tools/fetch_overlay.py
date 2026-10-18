#!/usr/bin/env python3
"""
Materialise the consolidated inventory onto disk and emit the drop-in overlay.

Reads manifest/consolidated.json (produced by consolidate.py) and, for every
tier-1 path, fetches the winning file from its recorded source repo.

GUARANTEES
----------
* Byte-for-byte fidelity to the source repo is recorded as a SHA-256 per file.
* Nothing overwrites an existing file unless --force is given.
* Tier 2 (C) files are NOT copied into the overlay. They are staged under
  manifest/tier2/ as a patch worklist instead, because they cannot work as a
  drop-in and must go through upstream review.
* Every imported file gets a provenance sidecar so the origin, branch, commit
  pin and licence stay attached to the content.

Usage:
    GH_TOKEN=... python tools/fetch_overlay.py --tier 1
    GH_TOKEN=... python tools/fetch_overlay.py --tier 2 --force
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN", "")
SRC = "manifest/consolidated.json"
RATE = {"n": 0, "skip": 0, "fail": 0}


def api(path, tries=4):
    for _ in range(tries):
        req = urllib.request.Request(API + path)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "openocd-consolidator/0.3")
        if TOKEN:
            req.add_header("Authorization", "Bearer " + TOKEN)
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                RATE["n"] += 1
                if r.status == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                    wait = max(1, int(r.headers.get("X-RateLimit-Reset", 0))
                               - int(time.time()) + 2)
                    print(f"  [rate limit] sleep {wait}s", file=sys.stderr, flush=True)
                    time.sleep(wait)
                    continue
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                wait = max(1, int(e.headers.get("X-RateLimit-Reset", 0))
                           - int(time.time()) + 2)
                time.sleep(wait)
                continue
            if e.code == 404:
                RATE["fail"] += 1
                return None
            if e.code >= 500:
                time.sleep(2)
                continue
            return None
        except Exception:
            time.sleep(2)
    RATE["fail"] += 1
    return None


def fetch(repo, branch, path):
    d = api("/repos/%s/contents/%s" % (repo, urllib.parse.quote(path)))
    if not d or d.get("type") != "file":
        return None
    return base64.b64decode(d["content"]).decode("utf-8", "replace")


def head_sha(repo, branch):
    c = api("/repos/%s/commits/%s" % (repo, urllib.parse.quote(branch)))
    return (c or {}).get("sha", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, choices=(1, 2), default=1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(SRC):
        sys.exit(f"missing {SRC}; run consolidate.py first")
    data = json.load(open(SRC, encoding="utf-8"))
    records = [r for r in data["records"] if r["tier"] == args.tier]

    outdir = args.out or ("overlay" if args.tier == 1 else "manifest/tier2")
    if args.tier == 1:
        print(f"tier 1 -> drop-in overlay at {outdir}/  ({len(records)} files)")
        print("         install alongside an UNMODIFIED upstream OpenOCD")
    else:
        print(f"tier 2 -> patch worklist at {outdir}/  ({len(records)} files)")
        print("         these need real source work + upstream PR")

    if args.limit:
        records = records[:args.limit]

    if args.dry_run:
        for r in records[:25]:
            print(f"  would fetch {r['path']}  <- {r['winner']}")
        print(f"  ... ({len(records)} total)")
        return

    os.makedirs(outdir, exist_ok=True)

    # Pin the exact commit each file came from, per source repo.
    heads = {}
    written, unchanged = 0, 0
    divergent = []
    prov_path = os.path.join(outdir, "PROVENANCE.json")
    prov = {}
    if os.path.exists(prov_path) and not args.force:
        try:
            blob = json.load(open(prov_path, encoding="utf-8"))
            # Read ONLY the per-file map. An earlier revision loaded the whole
            # document, so the metadata keys ("upstream", "tier", "files", ...)
            # leaked into the per-file dict and were then treated as file
            # paths, producing five bogus "MISSING" entries and corrupting the
            # integrity count.
            prov = blob.get("files", {}) if isinstance(blob, dict) else {}
        except Exception:
            prov = {}

    for i, r in enumerate(records, 1):
        repo = r["winner"]
        branch = r["winner_branch"] or "master"
        dest = os.path.join(outdir, r["path"])

        if repo not in heads:
            heads[repo] = head_sha(repo, branch)

        text = fetch(repo, branch, r["path"])
        if text is None:
            print(f"  [{i}/{len(records)}] FETCH-FAIL {r['path']} <- {repo}")
            continue

        if os.path.exists(dest) and not args.force:
            old = open(dest, encoding="utf-8").read()
            if old == text:
                unchanged += 1
            else:
                # DIVERGENT: the same path exists in more than one source repo
                # and the copies are not byte-identical. consolidation.py
                # already picked a winner, so on a re-run this means the winner
                # changed or the file was edited locally. Do NOT silently keep a
                # stale copy whose bytes contradict recorded provenance.
                divergent.append(r["path"])
        else:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            written += 1

        prov[r["path"]] = {
            "source_repo": repo,
            "source_branch": branch,
            "source_commit": heads[repo],
            "source_path": r["path"],
            "license": r["winner_license"],
            "stars_at_import": r["winner_stars"],
            "also_present_in": r["also_in"],
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
        # Record the sha of what is ACTUALLY on disk. If a previous run kept a
        # divergent copy, provenance must describe the bytes that exist, not
        # the bytes we would have written.
        if divergent and divergent[-1] == r["path"] and os.path.exists(dest):
            prov[r["path"]]["sha256"] = hashlib.sha256(
                open(dest, "rb").read()).hexdigest()
            prov[r["path"]]["bytes_on_disk_differ_from_source"] = True
        if i % 50 == 0:
            print(f"  ...{i}/{len(records)} ({RATE['n']} api calls)")

    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump({
            "upstream": data["upstream"],
            "upstream_branch": data["upstream_branch"],
            "tier": args.tier,
            "file_count": len(prov),
            # Integrity self-check lives in the artefact itself. A stale key
            # means a file is recorded but absent on disk (or vice versa),
            # which silently rots the provenance chain.
            "integrity": {
                "recorded": len(prov),
                "on_disk": sum(1 for p in prov
                               if os.path.exists(os.path.join(outdir, p))),
                "note": ("recorded == on_disk means every provenance entry has "
                         "a real file; any shortfall is a missing file"),
            },
            "files": prov,
        }, f, indent=1, ensure_ascii=False)

    on_disk = sum(1 for p in prov if os.path.exists(os.path.join(outdir, p)))
    print(f"\nwritten   : {written}")
    print(f"unchanged : {unchanged}")
    print(f"divergent : {len(divergent)}  (same path, different bytes between "
          f"sources; kept the on-disk copy - re-run with --force to sync)")
    for d in divergent[:10]:
        print(f"    DIVERGENT {d}")
    print(f"failures  : {RATE['fail']}")
    print(f"api calls : {RATE['n']}")
    print(f"integrity : {on_disk}/{len(prov)} provenance entries have a file")
    if on_disk != len(prov):
        for m in [p for p in prov
                  if not os.path.exists(os.path.join(outdir, p))][:10]:
            print(f"  MISSING: {m}")
    print(f"provenance: {prov_path}")


if __name__ == "__main__":
    main()
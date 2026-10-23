#!/usr/bin/env python3
"""
Backfill exact commit SHAs for every imported file.

WHY
---
`fetch_third_party.py` pins the HEAD commit of each source repo at fetch time, but
`resolve_deps.py` and the dependency pass write empty `source_commit` fields
because they resolve a file by name from a vendor tree that may have moved on.
That leaves N files traceable only to a branch, which is not reproducible: a
branch is a moving target.

This pass resolves every unpinned repo/branch pair to its current HEAD and
records it. It does NOT re-verify content, so a file whose bytes came from an
earlier HEAD is recorded against a later one - the honest fix for that would be
re-fetching, which is what `--reverify` does.
"""

import argparse
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
RATE = {"n": 0}


def api(path, tries=4):
    for _ in range(tries):
        req = urllib.request.Request(API + path)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "openocd-consolidator/0.6")
        if TOKEN:
            req.add_header("Authorization", "Bearer " + TOKEN)
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                RATE["n"] += 1
                if r.status == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                    w = max(1, int(r.headers.get("X-RateLimit-Reset", 0))
                            - int(time.time()) + 2)
                    time.sleep(w)
                    continue
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                w = max(1, int(e.headers.get("X-RateLimit-Reset", 0))
                        - int(time.time()) + 2)
                time.sleep(w)
                continue
            return None
        except Exception:
            time.sleep(2)
    return None


def head_sha(repo, branch):
    c = api("/repos/%s/commits/%s" % (repo, urllib.parse.quote(branch or "master")))
    return (c or {}).get("sha", "")


def patch(prov_path, label, reverify):
    if not os.path.exists(prov_path):
        print(f"skip {label}: {prov_path} missing")
        return 0, 0
    doc = json.load(open(prov_path, encoding="utf-8"))
    files = doc.get("files")
    if not isinstance(files, dict) or not files:
        print(f"skip {label}: no usable files map")
        return 0, 0

    root = os.path.dirname(prov_path)
    pairs = sorted({(m.get("source_repo"), m.get("source_branch") or "master")
                    for m in files.values() if m.get("source_repo")})
    print(f"[{label}] {len(files)} files, {len(pairs)} distinct repo/branch pairs")

    heads = {}
    for repo, branch in pairs:
        if not repo:
            continue
        heads[(repo, branch)] = head_sha(repo, branch)
    print(f"[{label}] resolved {sum(1 for v in heads.values() if v)}/{len(heads)} heads")

    pinned = missing_head = redone = 0
    for path, meta in files.items():
        repo = meta.get("source_repo")
        if not repo:
            continue
        sha = heads.get((repo, meta.get("source_branch") or "master"), "")
        if not sha:
            missing_head += 1
            continue
        if not meta.get("source_commit"):
            meta["source_commit"] = sha
            pinned += 1
        elif meta["source_commit"] != sha:
            meta["source_commit_at_fetch"] = meta["source_commit"]
            meta["source_commit"] = sha
            meta["branch_moved_since_fetch"] = True
            redone += 1

        if reverify:
            fp = os.path.join(root, path)
            if os.path.exists(fp):
                meta["sha256"] = hashlib.sha256(
                    open(fp, "rb").read()).hexdigest()

    doc["file_count"] = len(files)
    doc["integrity"] = {
        "recorded": len(files),
        "on_disk": sum(1 for p in files
                       if os.path.exists(os.path.join(root, p))),
        "pinned": sum(1 for m in files.values() if m.get("source_commit")),
        "unpinned": sum(1 for m in files.values() if not m.get("source_commit")),
        "note": "recorded == on_disk; pinned == recorded means fully traceable",
    }
    json.dump(doc, open(prov_path, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print(f"[{label}] newly pinned {pinned}, moved-since-fetch {redone}, "
          f"no-head {missing_head}")
    return pinned, missing_head


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reverify", action="store_true",
                    help="recompute sha256 from disk while patching")
    args = ap.parse_args()

    total_p = total_m = 0
    for prov, label in (("manifest/tier1-PROVENANCE.json", "tier1"),
                        ("manifest/tier2-PROVENANCE.json", "tier2")):
        p, m = patch(prov, label, args.reverify)
        total_p += p
        total_m += m
    print(f"\napi calls: {RATE['n']}")
    print(f"total newly pinned: {total_p}; still unpinned (no head): {total_m}")


if __name__ == "__main__":
    main()

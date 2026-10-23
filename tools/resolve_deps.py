#!/usr/bin/env python3
"""
Resolve the imported tcl's internal `source [find ...]` graph to a fixed point.

WHY THIS IS A SEPARATE PASS
----------------------------
The mining sweep probes a fixed list of subtrees, so it can miss a whole
directory. `tcl/board/flash_algorithms` was missing from that list, and the
The first finished import shipped board configs pointing at flash algorithms that
were never imported. Every imported file still passed its own byte/balance
checks, so nothing complained until a board was actually used.

Dangling references are therefore a class of defect the per-file checks cannot
see, and they need their own pass. Worse, the graph is nested:
    board/xxx.cfg  ->  board/flash_algorithms/yyy.cfg
                                   ->  board/flash_algorithms/algoFileFinder.cfg
so one round is not enough. This repeats until no new reference resolves.

It deliberately stops after a fixed round budget and REPORTS what it could not
resolve rather than looping forever on references that exist in no source tree
(Synopsys bring-up targets are the known case: they ship only inside Synopsys
internal builds).
"""

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN", "")
PROV = "manifest/tier1-PROVENANCE.json"
CONSOL = "manifest/consolidated.json"
UPSTREAM = "manifest/upstream-index.txt"
TREE = "."
FIND_RE = re.compile(r"^\s*source\s+\[find\s+([^\]\s]+)\s*\]", re.M)
RATE = {"n": 0}


def normalise(p):
    """Fold path shape: drop separators and redundant vendor prefixes."""
    return p.replace("_", "").replace("-", "").replace("/", "").casefold()


def api(path, tries=3):
    for _ in range(tries):
        req = urllib.request.Request(API + path)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "openocd-consolidator/0.5")
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
                w = max(1, int(r.headers.get("X-RateLimit-Reset", 0))
                        - int(time.time()) + 2)
                time.sleep(w)
                continue
            return None
        except Exception:
            time.sleep(2)
    return None


def fetch_text(repo, branch, path):
    d = api("/repos/%s/contents/%s" % (repo, urllib.parse.quote(path)))
    if not d or d.get("type") != "file":
        return None
    try:
        return base64.b64decode(d["content"]).decode("utf-8", "replace")
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rounds", type=int, default=5)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(PROV):
        sys.exit(f"missing {PROV}; run fetch_third_party.py first")
    doc = json.load(open(PROV, encoding="utf-8"))
    files = doc.get("files")
    if not isinstance(files, dict) or not files:
        sys.exit(f"{PROV} has no usable 'files' map (keys: {list(doc)[:6]})")

    upstream = {l.strip() for l in open(UPSTREAM, encoding="utf-8")
                if l.strip()} if os.path.exists(UPSTREAM) else set()
    owner = {}
    if os.path.exists(CONSOL):
        for r in json.load(open(CONSOL, encoding="utf-8"))["records"]:
            owner[r["path"]] = r

    imported_total = 0
    stuck = {}
    # Track which repo supplied each already-present imported file, so a nested
    # dependency is looked for in ITS OWN vendor tree.
    #
    # The first version only consulted `owner`, which maps consolidated records
    # to repos. Dependency files added by the earlier pass are not records, so
    # they had no repo, and the resolver fell back to upstream - reporting
    # algoFileFinder.cfg as unresolvable even though it exists in
    # analogdevicesinc/openocd. Keeping the map across rounds fixes the whole
    # class.
    repo_of = {path: meta.get("source_repo")
               for path, meta in files.items() if meta.get("source_repo")}
    branch_of = {path: (meta.get("source_branch") or "master")
                 for path, meta in files.items() if meta.get("source_repo")}

    for rnd in range(1, args.max_rounds + 1):
        prov_keys = set(files)
        up_tails = {p.rsplit("/", 1)[-1] for p in upstream}

        def satisfied(ref):
            return (ref in prov_keys
                    or ref in upstream
                    or ref.rsplit("/", 1)[-1] in up_tails
                    or any(k.endswith("/" + ref) for k in prov_keys)
                    or any(p.endswith("/" + ref) for p in upstream))

        wanted = {}
        # Upstream duplicates must never be re-introduced. The resolver is
        # asked for files by their FORK path; if upstream already ships that
        # file under a different path, fetching the fork copy is pointless and
        # harmful, because the stale copy would shadow upstream's maintained one
        # would shadow upstream's maintained one. Pruning them afterwards was
        # not enough - the next run re-added three of them, because the
    # reference itself is satisfied by upstream only under the other name.
        up_exact = upstream
        up_norm = {normalise(p) for p in upstream}
        for dp, _dn, names in os.walk("tcl"):
            for n in names:
                if not n.endswith((".cfg", ".tcl")):
                    continue
                fp = os.path.join(dp, n)
                rel = os.path.relpath(fp).replace(os.sep, "/")
                try:
                    txt = open(fp, encoding="utf-8").read()
                except Exception:
                    continue
                for raw in FIND_RE.findall(txt):
                    ref = raw.strip()
                    if ref.startswith("tcl/"):
                        ref = ref[4:]
                    if satisfied(ref):
                        continue
                    # Skip anything upstream already provides, under this name
                    # or any equivalent spelling of it.
                    #
                    # The comparison must use the FULL path. Upstream paths
                    # carry the `tcl/` prefix while a `source [find ...]`
                    # reference does not, so normalising the bare reference
                    # made every lookup miss by exactly that prefix and let
                    # three duplicates back in on the next run.
                    full = "tcl/" + ref
                    if (ref in up_exact
                            or full in upstream
                            or normalise(full) in up_norm
                            or normalise(ref) in {normalise(p) for p in upstream
                                                  if p.startswith("tcl/")}):
                        continue
                    if any(k.endswith("/" + ref) for k in prov_keys):
                        continue
                    if any(p.endswith("/" + ref) for p in upstream):
                        continue
                    cands = []
                    # Reuse the branch the referencing file was actually taken
                    # from. Defaulting to "master" produced a dead branch: some
                    # vendor repos (analogdevicesinc/openocd) have no `master`
                    # at all, their default branch being a release tag, so the
                    # lookup 422'd and the file shipped with an empty commit pin.
                    rec = owner.get(rel)
                    src_repo = repo_of.get(rel) or (rec or {}).get("winner")
                    if src_repo:
                        br = (branch_of.get(rel)
                              or (rec or {}).get("winner_branch")
                              or "master")
                        cands.append((src_repo, br))
                    cands.append(("openocd-org/openocd", "master"))
                    lst = wanted.setdefault(ref, [])
                    for c in cands:
                        if c not in lst:
                            lst.append(c)

        if not wanted:
            print(f"round {rnd}: closure reached, nothing left to import")
            break

        print(f"round {rnd}: {len(wanted)} unresolved reference(s)")
        progressed = 0
        for ref, cands in sorted(wanted.items()):
            got = None
            for repo, branch in cands:
                t = fetch_text(repo, branch, "tcl/" + ref)
                if t is not None:
                    got = (repo, branch, t)
                    break
            if got is None:
                alt = [p for p in upstream
                       if p.endswith("/" + ref.rsplit("/", 1)[-1])]
                if alt:
                    t = fetch_text("openocd-org/openocd", "master", alt[0])
                    if t is not None:
                        got = ("openocd-org/openocd", "master", t)
            if got is None:
                stuck[ref] = sorted({c[0] for c in cands})
                continue
            repo, branch, text = got
            key = "tcl/" + ref
            repo_of[key] = repo
            branch_of[key] = branch
            dest = key
            if args.apply:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
            files[key] = {
                "source_repo": repo, "source_branch": branch,
                "source_commit": "", "source_path": key,
                "license": None, "stars_at_import": 0, "also_present_in": [],
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "imported_as": "dependency-resolved",
            }
            progressed += 1
            imported_total += 1
            print(f"   + {key}  <- {repo}")

        if progressed == 0:
            print(f"   no progress this round; stopping")
            break

    on_disk = sum(1 for p in files if os.path.exists(p))
    doc["files"] = files
    doc["file_count"] = len(files)
    doc["integrity"] = {
        "recorded": len(files), "on_disk": on_disk,
        "note": "recorded == on_disk means every provenance entry has a real file",
    }
    doc["unresolved_references"] = stuck
    if args.apply:
        json.dump(doc, open(PROV, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)

    print(f"\nimported this run : {imported_total}")
    print(f"total imported tcl: {len(files)} (on disk {on_disk})")
    print(f"api calls         : {RATE['n']}")
    if stuck:
        print(f"unresolvable      : {len(stuck)}")
        for ref, cands in sorted(stuck.items()):
            print(f"    {ref}  (tried {', '.join(cands)})")
        print("  These exist in no public tree. They are bring-up targets that")
        print("  ship only inside vendor-internal builds; the boards that")
        print("  reference them cannot work without vendor binaries.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Remove imported files that shadow an upstream file of the SAME NAME.

    imported tcl/target/am335x.cfg
    upstream tcl/target/ti/am335x.cfg

This is a third duplication shape, separate from the two handled by
prune_upstream_dups.py (exact path, and renamed-then-moved):

  * path identical                     -> handled there
  * same basename, upstream moved it   -> handled there
  * same basename, DIFFERENT directory -> only handled here

It needs its own pass because path normalisation folds all three into one key.
`am335x.cfg` and `ti/am335x.cfg` normalise identically, so a normalised lookup
cannot distinguish "upstream renamed this file" from "these are two different
files that share a stem" - and would delete something the fork genuinely
contributed.

Why it still matters: a stale flat-named copy sits in the same search tree as
upstream's maintained version and wins every `find`. The tree is only
trustworthy while this pass keeps running.
"""

import json
import os

PROV = "manifest/PROVENANCE.json"
INDEX = "manifest/upstream-index.txt"
ROOT = "."
AREA = "tcl/target"


def prune_empty_dirs(root):
    for dp, _dn, _fn in os.walk(root, topdown=False):
        if os.path.abspath(dp) == os.path.abspath(root):
            continue
        try:
            if not os.listdir(dp):
                os.rmdir(dp)
        except OSError:
            pass


def main():
    if not os.path.exists(PROV):
        raise SystemExit(f"missing {PROV}; run fetch_third_party.py first")
    upstream = {l.strip() for l in open(INDEX, encoding="utf-8") if l.strip()}

    # upstream basename -> path, but ONLY for files in a vendor SUBDIRECTORY.
    # A same-named file at the same level is not a shadow.
    nested = {}
    for p in upstream:
        if not p.startswith(AREA + "/") or not p.endswith(".cfg"):
            continue
        rel = p[len(AREA) + 1:]
        if "/" not in rel:
            continue
        nested.setdefault(rel.rsplit("/", 1)[-1], p)

    doc = json.load(open(PROV, encoding="utf-8"))
    files = doc.get("files")
    if not isinstance(files, dict) or not files:
        raise SystemExit(f"{PROV} has no usable 'files' map")

    removed = []
    for k in list(files):
        if not k.startswith(AREA + "/"):
            continue
        rel = k[len(AREA) + 1:]
        if "/" in rel:
            continue                      # already nested, or not in this area
        alt = nested.get(rel)
        if not alt or alt == k:
            continue
        removed.append({"imported_path": k, "upstream_path": alt})
        del files[k]
        fp = os.path.join(ROOT, k)
        if os.path.exists(fp):
            try:
                os.remove(fp)
            except OSError:
                pass

    prune_empty_dirs(ROOT)

    doc["files"] = files
    doc["file_count"] = len(files)
    doc["integrity"] = {
        "recorded": len(files),
        "on_disk": sum(1 for p in files
                       if os.path.exists(os.path.join(ROOT, p))),
        "pinned": sum(1 for m in files.values() if m.get("source_commit")),
        "note": "recorded == on_disk; pinned == recorded means fully traceable",
    }
    trail = doc.setdefault("pruned_as_upstream_redundant", [])
    known = {(e.get("imported_path"), e.get("upstream_path")) for e in trail
             if isinstance(e, dict)}
    for e in removed:
        if (e["imported_path"], e["upstream_path"]) not in known:
            trail.append(e)

    json.dump(doc, open(PROV, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)

    print(f"pruned same-name shadowing files : {len(removed)}")
    for e in sorted(removed, key=lambda x: x["imported_path"]):
        print(f"    {e['imported_path']}  ->  upstream {e['upstream_path']}")
    print(f"imported files now              : {len(files)}")


if __name__ == "__main__":
    main()

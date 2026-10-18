#!/usr/bin/env python3
"""
Remove overlay files that duplicate what upstream already ships.

Two distinct shapes of duplication exist, and this script only handles the
first. Handling both here caused the second to be missed, so they are separate
scripts on purpose:

  1. EXACT      - `tcl/interface/jlink.cfg` in both places.
  2. RENAMED    - upstream reorganised TCL into vendor subdirectories and
                  dropped the redundant vendor prefix from the filename, so
                  `ti_cc13x0.cfg` became `tcl/target/ti/cc13x0.cfg`.
     Shape 3, SAME NAME / DIFFERENT DIRECTORY (`am335x.cfg` vs
     `tcl/target/ti/am335x.cfg`), is handled by prune_shadow.py, because
     normalising the path folds shapes 2 and 3 into the same key and would
     report a false match against two genuinely different files.

Leaving any of these in the overlay is harmful, not merely redundant: `-s`
puts the overlay FIRST on OpenOCD's search path, so a stale flat-named copy
shadows upstream's maintained file and silently wins forever.

The removed set is appended to `pruned_as_upstream_redundant` as an audit
trail. It is APPENDED, not replaced, because prune_shadow.py writes its own
entries into the same key and a full re-run must not erase them.
"""

import json
import os

PROV = "overlay/PROVENANCE.json"
INDEX = "manifest/upstream-index.txt"


def norm(p):
    return p.replace("_", "").replace("-", "").replace("/", "").casefold()


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
        raise SystemExit(f"missing {PROV}; run fetch_overlay.py first")
    if not os.path.exists(INDEX):
        raise SystemExit(f"missing {INDEX}; it is the baseline for this check")

    doc = json.load(open(PROV, encoding="utf-8"))
    files = doc.get("files")
    if not isinstance(files, dict) or not files:
        raise SystemExit(f"{PROV} has no usable 'files' map")

    upstream = {l.strip() for l in open(INDEX, encoding="utf-8") if l.strip()}
    up_norm = {}
    for p in upstream:
        up_norm.setdefault(norm(p), p)

    removed = []
    for k in list(files):
        hit = k if k in upstream else up_norm.get(norm(k))
        if not hit:
            continue
        removed.append({"overlay_path": k, "upstream_path": hit})
        del files[k]
        fp = os.path.join("overlay", k)
        if os.path.exists(fp):
            try:
                os.remove(fp)
            except OSError:
                pass

    prune_empty_dirs("overlay")

    doc["files"] = files
    doc["file_count"] = len(files)
    doc["integrity"] = {
        "recorded": len(files),
        "on_disk": sum(1 for p in files
                       if os.path.exists(os.path.join("overlay", p))),
        "pinned": sum(1 for m in files.values() if m.get("source_commit")),
        "note": "recorded == on_disk; pinned == recorded means fully traceable",
    }
    trail = doc.setdefault("pruned_as_upstream_redundant", [])
    known = {(e.get("overlay_path"), e.get("upstream_path")) for e in trail
             if isinstance(e, dict)}
    for e in removed:
        if (e["overlay_path"], e["upstream_path"]) not in known:
            trail.append(e)

    json.dump(doc, open(PROV, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)

    print(f"pruned exact/renamed duplicates : {len(removed)}")
    print(f"overlay files now               : {len(files)}")
    print(f"audit trail entries total       : {len(trail)}")


if __name__ == "__main__":
    main()
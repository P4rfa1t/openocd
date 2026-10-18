#!/usr/bin/env python3
"""
Cross-repo consolidation of genuine third-party OpenOCD support.

Takes the per-repo mining output and produces ONE deduplicated inventory of
support that official OpenOCD does not have.

THE DEDUP PROBLEM THAT MATTERS
------------------------------
The same chip support is duplicated across many forks. WCH CH32V appears in
cjacker/wch-openocd, Seneral/riscv-openocd-wch, kprasadvnsi/riscv-openocd-wch,
newbrain/riscv-openocd-wch AND stacksmashing/openocd-tamarin - five repos, near
identical file lists. Importing all five would produce five conflicting copies
of the same 140 files.

So the inventory is keyed on the repo-relative PATH, and for each path we keep
exactly one provenance winner chosen by an explicit, recorded policy:

  1. prefer the source whose repo tracks upstream most closely
     (fewest files it is missing) - least likely to ship obsolete configs;
  2. then prefer the most recently pushed;
  3. then prefer more stars (community validation);
  4. deterministic final tiebreak on repo name.

Every rejected duplicate is retained in the manifest so the decision is
auditable and reversible.

Outputs:
  manifest/consolidated.json    full provenance + per-file record
  manifest/consolidated.csv     one row per unique path
"""

import csv
import json
import os
import re
import unicodedata
from collections import defaultdict

SURVEY = "manifest/survey.json"
OUT_JSON = "manifest/consolidated.json"
OUT_CSV = "manifest/consolidated.csv"

GLUE_RE = re.compile(r"^tcl/(target|board|interface|cpld)(/.+)?$")

# Tier 2 means "needs a real source change to add NEW CHIP SUPPORT".
# Files that qualify:
#   * a new flash bank driver      src/flash/nor/*.c|h
#   * a new adapter/transport      src/jtag/drivers/*.c|h
#   * a new target/arch backend    src/target/*.c|h
#   * the registration glue that binds those into the driver tables
#
# Explicitly EXCLUDED, because they are not chip support and would corrupt a
# patch worklist if treated as such:
#   * build-system files (CMakeLists.txt, Makefile.in, Makefile.am) - these
#     differ trivially between trees and are not importable as-is;
#   * non-C/C++ payloads that some repos carry (Rust, Python, TypeScript,
#     .zip) - they belong to those repos' own tooling, not to OpenOCD;
#   * core internals like src/jtag/core.c, src/server/server.c, which exist
#     upstream under the same name and are therefore *modified*, not added -
#     their delta needs a real diff against upstream, not a file copy.
CORE_EXISTING_UPSTREAM = re.compile(
    r"^src/(jtag/core\.c|jtag/interface\.c|jtag/transport\.c|"
    r"flash/nor/core\.c|server/server\.c|openocd\.c|main\.c|"
    r"helper/logging\.c|helper/command\.c)$")

C_EXT = (".c", ".h")

# src/ files that every OpenOCD tree has always had under the SAME name, but
# which some forks RESTRUCTURED (flat src/jtag/*.c vs upstream's
# src/jtag/drivers/*.c). They are not new support - they are the same code at a
# different path, so a file copy would create a duplicate driver.
#
# Evidence: the blackmagic fork's libusb1_common.c opens with
#   "Copyright (C) 2009 by Zachary T Welch" and the Nuvoton fork's
#   ft2232.c with "Copyright (C) 2009 by Oyvind Harboe" / SoftPLC - both are
#   long-standing upstream OpenOCD authors, i.e. these are upstream's own
#   generic USB backends, not vendor contributions.
RESTRUCTURED_UPSTREAM = {
    "src/jtag/drivers/libusb0_common.c",
    "src/jtag/drivers/libusb0_common.h",
    "src/jtag/drivers/libusb1_common.c",
    "src/jtag/drivers/libusb1_common.h",
    "src/jtag/drivers/libusb_common.h",
    "src/jtag/drivers/usb_common.c",
    "src/jtag/drivers/usb_common.h",
    "src/jtag/drivers/ft2232.c",
    "src/jtag/drivers/ftdi.c",
    "src/jtag/drivers/ftdi.h",
    "src/jtag/drivers/ftd2xx_common.h",
    "src/jtag/drivers/picoprobe.c",
    "src/jtag/drivers/hla_usb.c",
    "src/jtag/drivers/stlink_usb.h",
    "src/jtag/drivers/jtag_usb_common.c",
    "src/jtag/drivers/driver.h",
    "src/jtag/driver.h",
    "src/jtag/transport.c",
    "src/jtag/transport.h",
    "src/flash/mflash.c",
    "src/flash/mflash.h",
    "src/target/a64_disassembler.c",
    "src/target/a64_disassembler.h",
    "src/target/oocd_trace.c",
    "src/target/oocd_trace.h",
    "src/server/server_stubs.c",
}


def tier(path):
    """1 = tcl/ config, 2 = new C chip support, 0 = not importable."""
    if GLUE_RE.match(path):
        return 1
    if not path.startswith("src/"):
        return 0
    if not path.endswith(C_EXT):
        return 0                       # CMakeLists, Makefile.in, .rs, .py ...
    if path in RESTRUCTURED_UPSTREAM:
        return 0                       # same code, older directory layout
    if CORE_EXISTING_UPSTREAM.match(path):
        return 0                       # needs a diff, not a copy
    if re.match(r"^src/(flash/nor|flash/drivers|jtag/drivers|jtag/adapters|"
                r"target|transport|server)/", path):
        return 2
    return 0


def kind(path):
    m = GLUE_RE.match(path)
    if m:
        # Keep the flash_algorithms bucket distinct: board configs depend on
        # it, so it needs its own provenance column in the report.
        if m.group(2) and m.group(2).startswith("/flash_algorithms/"):
            return "flash_algorithms"
        return m.group(1)
    return "src"


def pick_winner(cands):
    """Choose ONE provenance source for a path, with a recorded rationale.

    Policy, applied in strict order:
      1. fewest files the repo is missing vs upstream  -> least stale
      2. most recently pushed                            -> best maintained
      3. more stars                                      -> more validated
      4. repo name                                       -> deterministic
    """
    def sort_key(c):
        r = c["repo_meta"]
        return (
            r.get("missing_core_count", 999),
            _neg_date(r.get("pushed_at")),   # sorts DESC via _neg
            -r.get("stars", 0),
            c["repo"],
        )
    return sorted(cands, key=sort_key)[0]


class _neg:
    """Helper to sort a date string descending inside an ascending sort."""
    __slots__ = ("s",)

    def __init__(self, s):
        self.s = s or ""

    def __lt__(self, o):
        return self.s > o.s

    def __eq__(self, o):
        return self.s == o.s


def _neg_date(s):
    return _neg((s or "")[:10])


def fold_key(path):
    """Collision-insensitive key for a TCL filename.

    Two upstream-and-fork realities make raw path equality wrong:

    * Case. `tcl/target/1986Be1T.cfg` (fork) and `tcl/target/1986BE1T.cfg`
      (another fork) hold the SAME configuration - verified by identical
      SHA-256. On Windows and on macOS's default APFS they are the same file,
      so keeping both produced two provenance rows, one file on disk, and a
      bogus "recorded but missing" integrity error.
    * Unicode form. `tcl/target/1986в1т.cfg` appears in both NFC and NFD
      spellings across repos (1986U+0432 U+0435 1 U+0442). macOS HFS+
      normalises to NFD, Linux does not, so the same chip config can be
      recorded twice under different byte sequences.

    Folding case and applying NFC makes one logical target one record. The
    representative path kept is the one from the highest-priority source, so
    provenance stays faithful.
    """
    return unicodedata.normalize("NFC", path).casefold()


def load_upstream_index(path="manifest/upstream-index.txt"):
    """Load the authoritative upstream file inventory if present.

    `manifest/upstream-index.txt` is the full recursive blob list from
    openocd-org/openocd (2199 entries). It is the same baseline
    `mine_github.py` fetches, materialised to disk so downstream steps can
    agree on it without another API call.
    """
    if not os.path.exists(path):
        print("  [warn] no upstream index; upstream-duplicate filtering "
              "DISABLED (run mine_github.py to create it)", flush=True)
        return set(), {}
    lines = {l.strip() for l in open(path, encoding="utf-8") if l.strip()}
    norm = {}
    for p in lines:
        norm.setdefault(norm_key(p), p)
    # Basename -> upstream path, but only for files inside a vendor
    # subdirectory, so "same name, different directory" shadows can be told
    # apart from "same name, same level".
    nested = {}
    for p in lines:
        if p.startswith("tcl/target/") and p.endswith(".cfg") \
                and "/" in p[len("tcl/target/"):]:
            nested.setdefault(p.rsplit("/", 1)[-1], p)
    return lines, {"norm": norm, "nested": nested}


def norm_key(p):
    return p.replace("_", "").replace("-", "").replace("/", "").casefold()


def upstream_conflict(path, up_exact, up_idx):
    """Return the upstream path this imported path duplicates, else None.

    Three shapes, and all three must be rejected here rather than after the
    manifest is written:

      1. identical path
      2. renamed-then-moved   ti_cc13x0.cfg   -> tcl/target/ti/cc13x0.cfg
      3. same name elsewhere  am335x.cfg      -> tcl/target/ti/am335x.cfg

    Shapes 2 and 3 both collapse under a normalised key, which is exactly why
    shape 3 needs its own lookup: `am335x.cfg` and `ti/am335x.cfg` normalise
    the same, so one normalised test cannot tell them apart and would delete a
    file the fork really contributed.

    Doing this in post-processing (prune_*.py) left the manifest and the disk
    disagreeing: consolidated.json still listed 610 records while the tree
    held 505 files, so any re-run of fetch_third_party.py silently re-added all
    177 duplicates. The manifest has to be the single source of truth.
    """
    if not up_exact:
        return None
    if path in up_exact:
        return path
    alt = up_idx["norm"].get(norm_key(path))
    if alt and alt != path:
        return alt
    if path.startswith("tcl/target/") and "/" not in path[len("tcl/target/"):]:
        alt = up_idx["nested"].get(path.rsplit("/", 1)[-1])
        if alt and alt != path:
            return alt
    return None


def main():
    data = json.load(open(SURVEY, encoding="utf-8"))
    repos = {r["full_name"]: r for r in data["repos"]}

    up_exact, up_idx = load_upstream_index()

    # folded key -> candidate sources
    by_path = defaultdict(list)
    skipped = defaultdict(int)
    pruned = []
    for r in data["repos"]:
        meta = r
        if not r.get("deep_probed"):
            continue  # only fully-probed repos contribute reliable lists
        for p in (r.get("added_files") or []):
            t = tier(p)
            if t == 0:
                skipped[p] += 1
                continue
            clash = upstream_conflict(p, up_exact, up_idx)
            if clash:
                pruned.append({"imported_path": p, "upstream_path": clash})
                continue
            by_path[fold_key(p)].append(
                {"repo": r["full_name"], "repo_meta": meta, "path": p})

    records = []
    dup_count = 0
    for _key, cands in sorted(by_path.items()):
        cands.sort(key=lambda c: pick_winner([c])["repo"])
        win = pick_winner(cands)
        path = win["path"]
        # every distinct spelling seen for this logical file
        spellings = sorted({c["path"] for c in cands})
        dup_count += max(0, len({c["repo"] for c in cands}) - 1)
        records.append({
            "path": path,
            "tier": tier(path),
            "kind": kind(path),
            "winner": win["repo"],
            "winner_branch": win["repo_meta"].get("default_branch"),
            "winner_license": win["repo_meta"].get("license"),
            "winner_stars": win["repo_meta"].get("stars"),
            "also_in": sorted({c["repo"] for c in cands} - {win["repo"]}),
            "sources": len({c["repo"] for c in cands}),
            # Distinct spellings of the same logical file, if any.
            "path_spellings": spellings if len(spellings) > 1 else [],
        })

    t1 = [r for r in records if r["tier"] == 1]
    t2 = [r for r in records if r["tier"] == 2]

    # Which repos contributed the winning files? That is the real "shortlist".
    contrib = defaultdict(lambda: {"tier1": 0, "tier2": 0})
    for r in records:
        contrib[r["winner"]]["tier1" if r["tier"] == 1 else "tier2"] += 1

    by_kind = defaultdict(int)
    for r in records:
        by_kind[r["kind"]] += 1

    out = {
        "upstream": data["upstream"],
        "upstream_branch": data["upstream_branch"],
        "unique_paths": len(records),
        "tier1_drop_in_tcl": len(t1),
        "tier2_needs_c_patch": len(t2),
        "duplicates_collapsed": dup_count,
        "by_kind": dict(by_kind),
        "excluded_from_import": {
            "count": len(skipped),
            "note": ("build-system files, non-C payloads, and core internals "
                     "that exist upstream under the same name and therefore "
                     "need a real diff rather than a file copy"),
            "paths": sorted(skipped),
        },
        # Recorded here so the manifest, not a side effect, is the source of
        # truth for what was dropped and why. Previously this filtering only
        # happened after the manifest was written, leaving consolidated.json
        # (610 records) and the tree (505 files) disagreeing - and any
        # re-run of fetch_third_party.py re-added all 177 duplicates.
        "pruned_as_upstream_redundant": sorted(
            pruned, key=lambda e: e["imported_path"]),
        "pruned_upstream_duplicate_count": len(pruned),
        "contributors": {k: v for k, v in
                         sorted(contrib.items(),
                                key=lambda kv: -(kv[1]["tier1"] + kv[1]["tier2"]))},
        "records": records,
    }
    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tier", "kind", "path", "winner_repo", "branch",
                    "license", "stars", "copies", "also_in"])
        for r in sorted(records, key=lambda x: (x["tier"], x["kind"], x["path"])):
            w.writerow([r["tier"], r["kind"], r["path"], r["winner"],
                        r["winner_branch"], r["winner_license"],
                        r["winner_stars"], r["sources"],
                        " ".join(r["also_in"])])

    print(f"unique paths consolidated : {len(records)}")
    print(f"  tier 1 (drop-in .cfg)   : {len(t1)}")
    print(f"  tier 2 (needs C patch)  : {len(t2)}")
    print(f"duplicates collapsed      : {dup_count}")
    print(f"by kind                   : {dict(by_kind)}")
    print("\n=== contributing repos (files they uniquely won) ===")
    for repo, c in list(out["contributors"].items())[:20]:
        print(f"  {c['tier1']:>4} tcl  {c['tier2']:>3} src   {repo}")
    print(f"\n-> {OUT_JSON}\n-> {OUT_CSV}")


if __name__ == "__main__":
    main()
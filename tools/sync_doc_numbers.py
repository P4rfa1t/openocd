#!/usr/bin/env python3
"""
Align every published number in README.md, README.zh-CN.md and docs/*.md with
the manifest, the tree and the upstream index.

WHY THIS EXISTS
---------------
The numbers in the prose are hand-written, and hand-written numbers rot. This
script edits the documents in place, replacing each stale figure with the figure
the tree actually has, and it refuses to guess: every replacement is asserted
against a value measured from the tree.

MODES
-----
    python3 tools/sync_doc_numbers.py           # rewrite the documents in place
    python3 tools/sync_doc_numbers.py --check   # write nothing; fail on drift

Both modes fail (exit 1) when
  * an EDITS entry matches neither its stale text nor its target text, i.e. the
    document drifted away from this script and no replacement can be made;
  * a replacement was made but its target text is absent from the final file
    (one entry clobbered another, so a published number would be stale);
  * an identity the documents publish does not close - for example the tier-1
    paths still in the tree plus the dependency files must equal the number of
    tcl/ provenance entries, and the tcl/ directory table must add up;
  * the working tree and the manifest disagree about which files are present,
    because publishing numbers from a stale manifest is the rot this script
    exists to stop.

--check additionally fails when a replacement is still pending, so it works as a
CI gate: a green run means every published number already matches the tree.
No network access, no compiler and no build system are needed. The script is
idempotent; running it twice changes nothing the second time.

WHEN TO RUN IT
--------------
After changing the set of imported files: rebuild the manifest first
(tools/build_manifest.py), then run this script and commit the result.
"""

import csv
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

CHECK = "--check" in sys.argv[1:]

PROBLEMS = []          # fatal: exit 1
PENDING = []           # (file, replacements this run would apply)


def problem(msg):
    PROBLEMS.append(msg)


# ---------------------------------------------------------------- numbers

prov_doc = json.load(open("manifest/PROVENANCE.json", encoding="utf-8"))
prov = prov_doc["files"]
N_FILES = prov_doc["file_count"]
N_TCL = sum(1 for p in prov if p.startswith("tcl/"))
N_SRC = sum(1 for p in prov if p.startswith("src/"))
N_SRC_C = sum(1 for p in prov if p.startswith("src/") and p.endswith(".c"))
N_SRC_H = sum(1 for p in prov if p.startswith("src/") and p.endswith(".h"))
N_TCL_CFG = sum(1 for p in prov if p.startswith("tcl/") and p.endswith(".cfg"))
N_TCL_OTHER = N_TCL - N_TCL_CFG

# Per-subdirectory counts under tcl/, derived from the working tree because the
# table in docs/02-usage.md is hand-written and has drifted before.
TCL_SUBDIR_NAMES = ("target", "board", "interface", "cpld", "fpga", "chip", "cpu")
TCL_SUBDIR = {}
TCL_SUBDIR_CFG = {}
for _name in TCL_SUBDIR_NAMES:
    _d = pathlib.Path("tcl") / _name
    if _d.is_dir():
        _files = [f for f in _d.rglob("*") if f.is_file()]
        TCL_SUBDIR[_name] = len(_files)
        TCL_SUBDIR_CFG[_name] = sum(1 for f in _files if f.suffix == ".cfg")

lic = {}
for _v in prov.values():
    _k = _v.get("license") or "UNRESOLVED"
    lic[_k] = lic.get(_k, 0) + 1
N_GPL2 = lic.get("GPL-2.0", 0)
N_GPL2L = lic.get("GPL-2.0-or-later", 0)
N_NOASSERT = lic.get("NOASSERTION", 0)
N_UNRESOLVED = lic.get("UNRESOLVED", 0)
N_UNLICENSED = N_NOASSERT + N_UNRESOLVED
# verify_tree.py warns once for the adspsc58x.cfg name collision plus once per
# file whose licence could not be resolved.
N_WARNS = 1 + N_UNRESOLVED

# Dangling `source [find ...]` references.  Counted by running the audit tool
# itself, so the sentence in the documents cannot drift away from what the
# scanner actually reports.
_DANGLE_RUN = subprocess.run(
    [sys.executable, "tools/audit_dangling_refs.py"],
    capture_output=True, text=True, encoding="utf-8",
)
_DANGLE_M = re.search(r"unresolved references:\s*(\d+)", _DANGLE_RUN.stdout or "")
if _DANGLE_M is None:
    problem("tools/audit_dangling_refs.py produced no 'unresolved references:' line")
N_DANGLING = int(_DANGLE_M.group(1)) if _DANGLE_M else 0

# Integrity: how many imported files are still byte-identical to what the source
# repo published. A refreshed entry keeps that digest under pristine_sha256; an
# entry never touched since import is compared against sha256.
N_IDENTICAL = N_EDITED = N_EOL = N_EDITED_BOTH = 0
for _p, _v in prov.items():
    _notes = [_n.split(";")[0].strip() for _n in (_v.get("local_modifications") or [])]
    _edited = "content edited in this fork" in _notes
    _eol = "line endings normalised to LF" in _notes
    if _edited and _eol:
        N_EDITED_BOTH += 1
    if _edited or _eol:
        N_EDITED += 1 if _edited else 0
    if not _edited and _eol:
        N_EOL += 1
    _want = _v.get("pristine_sha256") or _v.get("sha256")
    _disk = ROOT / _p
    if _disk.is_file():
        if hashlib.sha256(_disk.read_bytes()).hexdigest() == _want:
            N_IDENTICAL += 1

# wired / unwired, resolved against the build system %D% entries
WIRED = set()
for _mk in ("src/Makefile.am", "src/target/Makefile.am",
            "src/jtag/Makefile.am", "src/jtag/drivers/Makefile.am",
            "src/flash/Makefile.am", "src/flash/nor/Makefile.am",
            "src/transport/Makefile.am", "src/server/Makefile.am",
            "src/rtos/Makefile.am", "src/helper/Makefile.am"):
    _f = ROOT / _mk
    if not _f.exists():
        continue
    _owner = _mk[len("src/"):-len("/Makefile.am")]
    for _line in _f.read_text(encoding="utf-8", errors="replace").splitlines():
        _m = re.search(r"%D%/(.+?)(?:\\|\s*$|\s)", _line)
        if _m and _m.group(1).strip():
            WIRED.add(_owner + "/" + _m.group(1).strip())


def is_wired(p):
    _rel = p[len("src/"):]
    return _rel in WIRED or p in WIRED


_src_paths = [p for p in prov if p.startswith("src/")]
N_WIRED = sum(1 for p in _src_paths if is_wired(p))
N_UNWIRED = N_SRC - N_WIRED
N_WIRED_C = sum(1 for p in _src_paths if is_wired(p) and p.endswith(".c"))
N_WIRED_H = sum(1 for p in _src_paths if is_wired(p) and p.endswith(".h"))
N_UNWIRED_C = N_SRC_C - N_WIRED_C
N_UNWIRED_H = N_SRC_H - N_WIRED_H

TREE = set(subprocess.run(["git", "ls-files"], capture_output=True,
                          text=True).stdout.split())
N_TREE = len(TREE)
N_UP = len(subprocess.run(["git", "ls-tree", "-r", "--name-only", "upstream/master"],
                          capture_output=True, text=True).stdout.split())

cons = json.load(open("manifest/consolidated.json", encoding="utf-8"))
N_UNIQUE = cons["unique_paths"]
N_IMPORTED = cons["imported_paths"]
N_NOTIMPORTED = cons["not_imported_paths"]
N_DUPES = cons["duplicates_collapsed"]
N_EXCLUDED = cons["excluded_from_import"]["count"]
N_PRUNED = cons["pruned_upstream_duplicate_count"]
N_TIER1 = cons["tier1_drop_in_tcl"]
N_TIER2 = cons["tier2_needs_c_patch"]
N_SRC_NOTIMPORTED = sum(1 for r in cons["records"]
                        if not r.get("imported") and r["path"].startswith("src/"))
N_TCL_NOTIMPORTED = N_NOTIMPORTED - N_SRC_NOTIMPORTED
N_DEPENDENCY = sum(1 for v in prov.values() if v.get("imported_as") == "dependency")

# --- the chain the documents publish ----------------------------------------
# imported_paths counts what the survey landed; some of those paths no longer
# exist (removed on purpose), and a few files entered the tree as dependencies
# without ever being in the survey's imported list. Both sides are recomputed
# here and the paragraph must close: imported - removed + extra == present.
_imported = {r["path"] for r in cons["records"] if r.get("imported")}
REMOVED = sorted(p for p in _imported if p not in TREE)
EXTRA = sorted(set(prov) - _imported)
N_IMPORTED_REMOVED = len(REMOVED)
N_EXTRA = len(EXTRA)
N_PRESENT = len([p for p in prov if p in TREE])
if N_IMPORTED - N_IMPORTED_REMOVED + N_EXTRA != N_PRESENT:
    problem("the import chain does not close: "
            f"{N_IMPORTED} - {N_IMPORTED_REMOVED} + {N_EXTRA} != {N_PRESENT}")
if N_FILES != N_PRESENT:
    problem(f"the manifest is stale: PROVENANCE.json records {N_FILES} files but "
            f"{N_PRESENT} of its entries exist on disk - rebuild the manifest "
            "before publishing numbers")

_tier1 = {r["path"] for r in cons["records"] if r.get("tier") == 1}
_tier1_imported = _tier1 & _imported
N_TIER1_IMPORTED = len(_tier1_imported)
N_TIER1_ABSENT = len(_tier1 - TREE)
N_TIER1_REMOVED = len([p for p in _tier1_imported if p not in TREE])
N_TIER1_PRESENT = N_TIER1_IMPORTED - N_TIER1_REMOVED
if N_TIER1_PRESENT + N_EXTRA != N_TCL:
    problem(f"tcl/ does not close: {N_TIER1_PRESENT} tier-1 files in the tree plus "
            f"{N_EXTRA} dependency files != {N_TCL} tcl/ provenance entries")


def is_mangled_name(path):
    """True for the spellings the survey recorded for two Cyrillic-named configs.

    The source repositories carry these two configs under Cyrillic names; four
    mangled spellings (percent-escaped and mojibake) also reached the candidate
    list. They belong to the "upstream already ships the same config" row, not
    to "dropped after import", so they are excluded from that count.
    """
    return any(ord(ch) > 127 or ch == "#" for ch in path)


_removed_set = {e["path"] for e in (prov_doc.get("removed_from_tree") or [])}
_not_imported_t1 = {r["path"] for r in cons["records"]
                    if not r.get("imported") and r.get("tier") == 1}
N_REMOVED_SINCE = len([p for p in (_not_imported_t1 & _removed_set)
                       if not is_mangled_name(p)])
_tier1_other_in_tree = {p for p in _tier1 if p in TREE} - _tier1_imported
N_TIER1_OTHER_IN_TREE = len(_tier1_other_in_tree)
N_TIER1_NEVER = N_TIER1_ABSENT - N_TIER1_REMOVED
if (N_TIER1_PRESENT + N_TIER1_REMOVED + N_TIER1_NEVER
        + N_TIER1_OTHER_IN_TREE != N_TIER1):
    problem(f"the tier-1 ledger does not close: {N_TIER1_PRESENT} imported and"
            f" present + {N_TIER1_REMOVED} removed after import + {N_TIER1_NEVER}"
            f" never landed + {N_TIER1_OTHER_IN_TREE} present without an import"
            f" record != {N_TIER1} tier-1 records")

survey = json.load(open("manifest/survey.json", encoding="utf-8"))
N_REPOS = survey["repo_count"]
N_SRC_REPOS = len({v["source_repo"] for v in prov.values() if v.get("source_repo")})

# repos.csv holds the survey candidates plus this fork's own repository, which is
# why its row count need not equal survey["repo_count"].
_repos_rows = list(csv.DictReader(open("manifest/repos.csv", encoding="utf-8")))
N_REPOS_CSV = len(_repos_rows)
N_DEEP = sum(1 for r in _repos_rows
             if str(r.get("deep", "")).strip().lower() in ("1", "true", "yes", "y"))

# licenses.csv is the per-file licence index the documents quote; it uses the
# British spelling 'licence'.
_lic_rows = list(csv.DictReader(open("manifest/licenses.csv", encoding="utf-8")))
N_LIC_ROWS = len(_lic_rows)
_lic_csv = {}
for _r in _lic_rows:
    _k = (_r.get("licence") or "UNRESOLVED").strip() or "UNRESOLVED"
    _lic_csv[_k] = _lic_csv.get(_k, 0) + 1
N_CSV_GPL2 = _lic_csv.get("GPL-2.0", 0)
N_CSV_GPL2L = _lic_csv.get("GPL-2.0-or-later", 0)
N_CSV_NOASSERT = _lic_csv.get("NOASSERTION", 0)
N_CSV_UNRESOLVED = _lic_csv.get("UNRESOLVED", 0)
N_CSV_UNLICENSED = N_CSV_NOASSERT + N_CSV_UNRESOLVED
if N_LIC_ROWS != N_FILES:
    problem(f"licenses.csv has {N_LIC_ROWS} rows but the manifest records "
            f"{N_FILES} files")
if N_CSV_UNLICENSED != N_UNLICENSED:
    problem("the licence index disagrees with the manifest about unresolved "
            f"licences: csv {N_CSV_UNLICENSED} vs provenance {N_UNLICENSED}")

N_UPSTREAM_INDEX = len(pathlib.Path("manifest/upstream-index.txt")
                       .read_bytes().decode("utf-8", "replace").splitlines())
if N_UPSTREAM_INDEX != N_UP:
    problem(f"manifest/upstream-index.txt has {N_UPSTREAM_INDEX} lines but "
            f"upstream/master trees {N_UP} files")

# -chain-position: the deprecated spelling the imported configs still use. The
# scope is tcl/, where configs live; every hit must belong to an imported file.
_cp = subprocess.run(["git", "grep", "-I", "-n", "-e", "-chain-position", "--", "tcl"],
                     capture_output=True, text=True).stdout.splitlines()
N_CPOS_HITS = 0
_cpos_files = set()
_cpos_by_cmd = {}
N_CPOS_MECH = 0
_named = re.compile(r"(target|dap|vjtag|pld|flash|nand)\s+create\s+(\S+)")
_valued = re.compile(r"-chain-position\s+(\S+)")
for _l in _cp:
    _path, _ln, _text = _l.split(":", 2)
    _cpos_files.add(_path)
    N_CPOS_HITS += _text.count("-chain-position")
    for _cmd in ("target create", "dap create", "vjtag create", "pld create"):
        if _cmd in _text:
            _cpos_by_cmd[_cmd] = _cpos_by_cmd.get(_cmd, 0) + _text.count("-chain-position")
    _m, _v = _named.search(_text), _valued.search(_text)
    if _m and _v and _m.group(2) == _v.group(1):
        N_CPOS_MECH += 1
N_CPOS_FILES = len(_cpos_files)
N_CPOS_HUMAN = N_CPOS_HITS - N_CPOS_MECH
_outside = sorted(p for p in _cpos_files if p not in prov)
if _outside:
    problem(f"-chain-position hits outside the imported set: {_outside[:5]}")
if subprocess.run(["git", "grep", "-I", "-l", "-e", "-chain-position",
                   "upstream/master", "--", "tcl"],
                  capture_output=True, text=True).stdout.strip():
    problem("upstream tcl/ no longer has zero -chain-position hits; the wording "
            "needs a rewrite, not a number swap")

N_OPENULINK = sum(1 for f in pathlib.Path("src/jtag/drivers/OpenULINK/src").iterdir()
                  if f.is_file())
N_BLOCKED = sum(1 for r in cons["records"]
                if not r.get("imported")
                and any(k in r["path"] for k in ("esp_gpio", "wlinke", "wch_riscv", "al_link")))
N_UNRESOLVED_REFS = len(prov_doc.get("unresolved_references") or [])
PCT_UNLICENSED = round(100 * N_UNLICENSED / N_FILES) if N_FILES else 0

# --- quantities the published documents now quote -------------------------
# Every number below is recomputed from the tree / manifest in this same run, so
# a document can never quote a figure this script did not observe.
N_FORKS = sum(1 for r in _repos_rows if (r.get("kind") or "").strip() == "fork")
N_INDEP = sum(1 for r in _repos_rows if (r.get("kind") or "").strip() == "independent")
N_REPOS_SURVEY = N_REPOS  # survey.json does not count this fork itself
N_REPOS_NOTDEEP = N_REPOS_CSV - N_DEEP

_not_imported = [r["path"] for r in cons["records"] if not r.get("imported")]
if len(_not_imported) != N_NOTIMPORTED:
    problem(f"not_imported_paths ({N_NOTIMPORTED}) disagrees with the record list "
            f"({len(_not_imported)})")
_ni_src = [p for p in _not_imported if p.startswith("src/")]
N_SRC_NI_FLASH = sum(1 for p in _ni_src if p.startswith("src/flash/"))
N_SRC_NI_TARGET = sum(1 for p in _ni_src if p.startswith("src/target/"))
N_SRC_NI_JTAG = sum(1 for p in _ni_src if p.startswith("src/jtag/"))

_ni = [r["path"] for r in cons["records"] if not r.get("imported")]
N_XDS100 = sum(1 for p in _ni if "xds100" in p)
N_XDS100_BOARD = sum(1 for p in _ni if "xds100" in p and p.startswith("tcl/board/"))

N_CPOS_TC = _cpos_by_cmd.get("target create", 0)
N_CPOS_DAP = _cpos_by_cmd.get("dap create", 0)
N_CPOS_PLD = _cpos_by_cmd.get("pld create", 0)

def _top(folder, ext):
    """Files directly in folder (no subdirectories), tracked in the tree."""
    depth = folder.count("/") + 2
    return [p for p in TREE if p.startswith(folder) and p.endswith(ext)
            and p.count("/") == depth]

N_ST_TOPC_GIT = len(_top("src/target/", ".c"))
N_ST_TOPC_TP = sum(1 for p in _top("src/target/", ".c") if p in prov)
N_JD_TOPC_GIT = len(_top("src/jtag/drivers/", ".c"))
N_JD_TOPC_TP = sum(1 for p in _top("src/jtag/drivers/", ".c") if p in prov)
N_RVMAX_FILES = sum(1 for p in TREE if p.startswith("src/target/rvmax/"))
N_RV32M1_FILES = sum(1 for p in TREE if p.startswith("src/target/rv32m1/"))
N_FLASH_NOR_TP = sum(1 for p in prov if p.startswith("src/flash/nor/"))

N_TCL_SUB_BOARD = TCL_SUBDIR["board"]
N_TCL_SUB_CHIP = TCL_SUBDIR["chip"]
N_TCL_SUB_CPLD = TCL_SUBDIR["cpld"]
N_TCL_SUB_CPU = TCL_SUBDIR["cpu"]
N_TCL_SUB_FPGA = TCL_SUBDIR["fpga"]
N_TCL_SUB_INTERFACE = TCL_SUBDIR["interface"]
N_TCL_SUB_TARGET = TCL_SUBDIR["target"]

print(f"files={N_FILES} (tcl {N_TCL} = {N_TCL_CFG} cfg + {N_TCL_OTHER} other, src {N_SRC} = {N_SRC_C}c+{N_SRC_H}h)")
print(f"wired={N_WIRED} ({N_WIRED_C}c+{N_WIRED_H}h) unwired={N_UNWIRED} ({N_UNWIRED_C}c+{N_UNWIRED_H}h)")
print(f"licences: GPL-2.0 {N_GPL2}, GPL-2.0-or-later {N_GPL2L}, NOASSERTION {N_NOASSERT}, "
      f"unresolved {N_UNRESOLVED}, unlicensed {N_UNLICENSED} ({PCT_UNLICENSED}%), warns {N_WARNS}")
print(f"integrity: identical {N_IDENTICAL}, eol-only {N_EOL}, edited {N_EDITED}, both {N_EDITED_BOTH}")
print(f"tree={N_TREE} upstream={N_UP} upstream-index={N_UPSTREAM_INDEX}")
print(f"unique={N_UNIQUE} imported={N_IMPORTED} not_imported={N_NOTIMPORTED} "
      f"(src {N_SRC_NOTIMPORTED}, tcl {N_TCL_NOTIMPORTED}) dependency-marked={N_DEPENDENCY}")
print(f"chain: {N_IMPORTED} - {N_IMPORTED_REMOVED} + {N_EXTRA} = {N_PRESENT} "
      f"(manifest records {N_FILES})")
print(f"tier1: {N_TIER1} candidates, {N_TIER1_IMPORTED} landed, {N_TIER1_PRESENT} in the tree, "
      f"{N_TIER1_REMOVED} removed after import, {N_TIER1_NEVER} never landed, "
      f"removed-since {N_REMOVED_SINCE}")
print(f"repos: survey={N_REPOS} csv={N_REPOS_CSV} deep={N_DEEP} src-repos={N_SRC_REPOS}")
print(f"chain-position: {N_CPOS_FILES} files, {N_CPOS_HITS} hits {_cpos_by_cmd}, "
      f"mechanical {N_CPOS_MECH}, human {N_CPOS_HUMAN}")
print(f"blocked candidates={N_BLOCKED} provenance-unresolved={N_UNRESOLVED_REFS} openulink/src={N_OPENULINK}")
print("tcl subdirs (all files):", " ".join(f"{k}={v}" for k, v in sorted(TCL_SUBDIR.items())))
print("tcl subdirs (cfg only) :", " ".join(f"{k}={v}" for k, v in sorted(TCL_SUBDIR_CFG.items())))
print(f"tcl subdir sums: all={sum(TCL_SUBDIR.values())} cfg={sum(TCL_SUBDIR_CFG.values())}")

# ---------------------------------------------------------------- edits

EDITS = [
    # (file, old, new). The old side must match the document as it stands;
    # the new side is rendered here from values measured in this same run.
    # Generated from .audit/review/spec_[abc].json - edit the spec, not this list.

    ('README.md',
     '688 candidate repositories were surveyed — 499 forks of upstream plus 189',
          f"{N_REPOS_CSV}"
     ' candidate repositories were surveyed — '
     f"{N_FORKS}"
     ' forks of upstream plus 189'),
    ('README.md',
     '| `tcl/` script files | 712 | 696 `.cfg` plus 16 `.tcl`/`.xml`/`.txt`; **work with no build changes at all** |',
          '| `tcl/` script files | '
     f"{N_TCL}"
     ' | '
     f"{N_TCL_CFG}"
     ' `.cfg` plus '
     f"{N_TCL_OTHER}"
     ' `.tcl`/`.xml`/`.txt`; **work with no build changes at all** |'),
    ('README.md',
     '| `src/` C sources | 73 | 37 `.c` plus 36 `.h`; **47 wired into the build**, 26 staged but not yet registered |',
          '| `src/` C sources | '
     f"{N_SRC}"
     ' | '
     f"{N_SRC_C}"
     ' `.c` plus '
     f"{N_SRC_H}"
     ' `.h`; **'
     f"{N_WIRED}"
     ' wired into the build**, '
     f"{N_UNWIRED}"
     ' staged but not yet registered |'),
    ('README.md',
     'Of the 1298 unique paths the survey identified, **795 landed in the tree** at the\ntime of the survey. Since then 11 of those were removed on purpose — see the\nlast row of the table below — while a handful of further files came in as\ndependencies of landed configs, leaving **785 tracked third-party files**\ntoday.',
          'Of the '
     f"{N_UNIQUE}"
     ' unique paths the survey identified, '
     f"{N_TIER1_IMPORTED}"
     ' tier-1 records were\nmarked imported and '
     f"{N_TIER1_PRESENT}"
     ' of them are still in the tree today; '
     f"{N_TIER1_REMOVED}"
     ' were dropped\non purpose after import and '
     f"{N_TIER1_NEVER}"
     ' never landed. A further '
     f"{N_EXTRA}"
     ' files came in as\ndependencies of landed configs without a tier-1 record of their own, leaving\n**'
     f"{N_FILES}"
     ' tracked third-party files** today — '
     f"{N_TCL}"
     ' under `tcl/` plus '
     f"{N_SRC}"
     ' under `src/`. The\nledger closes: '
     f"{N_TIER1_PRESENT}"
     ' + '
     f"{N_EXTRA}"
     ' = '
     f"{N_TCL}"
     '.'),
    ('README.md',
     'The 331 C sources that did not land all need per-backend porting: they are\ncomplete implementations of a driver or an architecture, but written against\nan older OpenOCD API. `src/target` holds the largest group (133 files),\nthen `src/flash` (125), `src/jtag` (71) and `src/server` (2).',
          'The '
     f"{N_SRC_NOTIMPORTED}"
     ' C sources that did not land all need per-backend porting: they are\npublished forks of drivers that still call an older OpenOCD API. `src/flash` holds\nthe largest group ('
     f"{N_SRC_NI_FLASH}"
     ' files), then `src/target` ('
     f"{N_SRC_NI_TARGET}"
     ') and `src/jtag`\n('
     f"{N_SRC_NI_JTAG}"
     ').'),
    ('README.md',
     'The 172 TCL files that did not land break down as:\n\n| | count | why |\n|---|---:|---|\n| upstream already ships them | 73 | upstream moved them into a subdirectory, so the survey saw them under a flat name |\n| needs a backend this tree does not have | 46 | they drive a probe or a chip family whose C code was never published — Infineon TriCore, the Anlogic `al_link` probe, WCH RISC-V, the ESP32 GPIO probe, the ST-LINK external loader family, and similar |\n| depends on a file that is itself missing | 25 | a `source [find ...]` line points at a config that did not land |\n| not retrievable from the survey cache | 5 | the survey recorded the path but the file body was never fetched |\n| the 12 candidates once called "ready to import" | 12 | none holds; 9 need `interface/ti/xds100v2.cfg` or `xds100v3.cfg` first, 3 were path confusion |\n| dropped from the tree after import | 11 | 7 redundant TI `swd_native` boards, `target/nrf_common.cfg`, `interface/stlink-usb.cfg`, both `interface/calao-usb-a9260-c0*.cfg` |\n\nThere is no "ready to import" group any more. Every one of the 172 either\nneeds a wrapper file, needs a C backend, or was removed on purpose.',
          'The '
     f"{N_TIER1_NEVER}"
     ' tier-1 TCL paths that never landed are, mechanically, the tier-1 records\nthat are neither in the tree nor listed in `removed_from_tree`. The old "ready to\nimport / needs a backend / depends on a missing file / not retrievable" split was a\nhand classification of an earlier snapshot that no tool reproduces any more, so it\nhas been dropped from this README. What is reproducible is the tier-1 ledger:\n'
     f"{N_TIER1}"
     ' candidates, '
     f"{N_TIER1_IMPORTED}"
     ' marked imported, '
     f"{N_TIER1_PRESENT}"
     ' still in the tree,\n'
     f"{N_TIER1_REMOVED}"
     ' removed after import, '
     f"{N_TIER1_NEVER}"
     ' never landed.\n\nThe two wrappers the TI boards need (`interface/ti/xds100v2.cfg`, `xds100v3.cfg`),\nthe 3 paths that were already in the tree under a flat-spelling parent, and the\n'
     f"{N_XDS100_BOARD}"
     ' TI board configs that depend on those wrappers are all listed per file\nin `manifest/consolidated.json` under `not_imported` ('
     f"{N_NOTIMPORTED}"
     ' paths in total).'),
    ('README.md',
     "Two more groups complete the count of **785 files**, each with its own\nprovenance entry:\n\n- **21 files pulled in as dependencies** — a config that `source`s another\n  config brings the referenced file along with it. They are marked\n  `imported_as: dependency` in the manifest.\n- **1 file that upstream also ships under the same name** —\n  `tcl/target/adspsc58x.cfg`, whose content differs from upstream's\n  `tcl/target/adsp-sc58x.cfg`. The tree keeps the third-party version and",
          'Two more groups complete the count of **'
     f"{N_FILES}"
     ' files**, each with its own provenance\nentry:\n\n- **'
     f"{N_DEPENDENCY}"
     " files pulled in as dependencies** — a config that `source`s another\n  config brings the referenced file along with it. They are marked\n  `imported_as: dependency` in the manifest.\n- **1 file that upstream also ships under the same name** —\n  `tcl/target/adspsc58x.cfg`, whose content differs from upstream's\n  `tcl/target/adsp-sc58x.cfg`. The tree keeps the third-party version, and the\n  collision is one of the "
     f"{N_WARNS}"
     ' warnings `verify_tree` reports.'),
    ('README.md',
     'Upstream ships 2203 files; this tree ships 3029.',
          'Upstream ships '
     f"{N_UP}"
     ' files; this tree ships '
     f"{N_TREE}"
     '.'),
    ('README.md',
     '**All 785 imported files are pinned',
          '**All '
     f"{N_FILES}"
     ' imported files are pinned'),
    ('README.md',
     'The survey covered **688 candidate repositories**; 56 of them',
          'The survey covered **'
     f"{N_REPOS_CSV}"
     ' candidate repositories**; '
     f"{N_SRC_REPOS}"
     ' of them'),
    ('README.md',
     '47 of the 73 new C sources and headers are wired into the build — 24 `.c`',
          f"{N_WIRED}"
     ' of the '
     f"{N_SRC}"
     ' new C sources and headers are wired into the build — '
     f"{N_WIRED_C}"
     ' `.c`'),
    ('README.md',
     'The remaining 26 — 13 `.c` and 13 `.h`: the `arc32` family,\n`adi_v5_cmsis_dap`, `aarch64_coproc_reg`, and the `arc_ftdi_cjtag` /\n`cmsis_dap_wch` / `jtag_esp_remote` / `jtag_tcp` drivers, plus the headers\nonly those files include — are **present in the tree but not compiled**. They\ntarget upstream APIs that have since moved, and registering them would need\nthe same porting work described below. Shipping them unregistered is\ndeliberate: the code is there, visible, reviewable, and harmless until it is\nwired up.',
          'The remaining '
     f"{N_UNWIRED}"
     ' — '
     f"{N_UNWIRED_C}"
     ' `.c` and '
     f"{N_UNWIRED_H}"
     ' `.h` — are **present in the tree but not\ncompiled**: `al_link.c` and `al_link_cyusb.c`, `cmsis_dap_wch.c`, `esp_gpio.c`,\n`jtag_esp_remote.c`, `jtag_tcp.c`, `wlinke.c`, `rbb_server.c`,\n`aarch64_coproc_reg.c`, `wch_riscv.c` and `wch_riscv-013.c`, plus the headers\nonly those files include (`al_link_cyusb.h`, `esp_gpio.h`, `rbb_server.h`,\n`aarch64_system_registers.h`, `aarch64_system_registers_defs.h`,\n`altera_virtual_jtag.h`, `wch_riscv.h`). The reasons differ per file — the `arc32`\nfamily that used to sit here was staged, found unbuildable and dropped in\n`7ffeda047` — and registering each one needs the porting work described below.\nShipping them unregistered is deliberate: the code is there, visible, reviewable,\nand harmless until it is wired up.\n\nThe per-file reasons are in `docs/02-usage.md`. The old claim that all of them\n"target upstream APIs that have moved" is not true for `jtag_tcp.c`,\n`jtag_esp_remote.c`, `cmsis_dap_wch.c` and `aarch64_coproc_reg.c`, which never\nexisted upstream, nor for the 11 files newly staged in `21ab67574`.'),
    ('README.md',
     'The distinction matters. An earlier revision of this repository failed its own\nintegrity check with 543 mismatches, because the tree had been rebuilt in\ntext mode on Windows and every imported file was silently stored with CRLF\nwhile the manifest described the LF original. The gate could not tell "this\nwas edited" from "this was checked out on a Windows host". Both are fixed now:\nthe tree is LF everywhere, 646 of the 785 imported files still match their\npublished digest byte for byte, 4 are now a terminator-only difference, and\n135 carry real local edits (24 of those also had their terminators normalised)\n— the target API ports, the relocated `source [find ...]` paths, the\nthird-party driver fixes and the `rvmax` / `rv32m1` backends.',
          'The distinction matters. An earlier revision of this repository failed its own\nintegrity check with 543 mismatches, because the tree had been rebuilt in text\nmode on Windows and every imported file was silently stored with CRLF while the\nmanifest described the LF original. The gate could not tell "this was edited"\nfrom "this was checked out on a Windows host". Both are fixed now: the tree is\nLF everywhere, '
     f"{N_IDENTICAL}"
     ' of the '
     f"{N_FILES}"
     ' imported files still match their published\ndigest byte for byte, '
     f"{N_EOL}"
     ' are a terminator-only difference, and '
     f"{N_EDITED}"
     ' carry real\nlocal edits ('
     f"{N_EDITED_BOTH}"
     ' of those also had their terminators normalised) — the target\nAPI ports, the relocated `source [find ...]` paths, the third-party driver fixes\nand the `rvmax` / `rv32m1` backends.'),
    ('README.md',
     'recorded : 785',
          'recorded : '
     f"{N_FILES}"),
    ('README.md',
     'on disk  : 785',
          'on disk  : '
     f"{N_FILES}"),
    ('README.md',
     'warns    : 23',
          'warns    : '
     f"{N_WARNS}"),
    ('README.md',
     'The 23 warnings are one file whose name collides with an upstream file but',
          'The '
     f"{N_WARNS}"
     ' warnings are one file whose name collides with an upstream file but'),
    ('README.md',
     'whose content differs (kept, deliberately) and 22 files whose license GitHub',
          'whose content differs (kept, deliberately) and '
     f"{N_UNRESOLVED}"
     ' files whose license GitHub'),
    ('README.md',
     'Of 785 files, GitHub resolved 135 as GPL-2.0, 1 as GPL-2.0-or-later, 627 as',
          'Of '
     f"{N_FILES}"
     ' files, GitHub resolved '
     f"{N_GPL2}"
     ' as GPL-2.0, '
     f"{N_GPL2L}"
     ' as GPL-2.0-or-later, '
     f"{N_NOASSERT}"
     ' as'),
    ('README.md',
     'is permissive) and 22 as unresolvable.',
          'is permissive) and '
     f"{N_UNRESOLVED}"
     ' as unresolvable.'),
    ('README.md',
     'machine-readable provenance for all 785 imported files',
          'machine-readable provenance for all '
     f"{N_FILES}"
     ' imported files'),
    ('README.md',
     '- **26 of the 73 new C sources and headers are not compiled** (13 `.c`, 13\n  `.h`). They are staged in the tree with their provenance intact, but they\n  target upstream APIs that have moved. Registering them needs per-backend\n  porting work.',
          '- **'
     f"{N_UNWIRED}"
     ' of the '
     f"{N_SRC}"
     ' new C sources and headers are not compiled** ('
     f"{N_UNWIRED_C}"
     ' `.c`,\n  '
     f"{N_UNWIRED_H}"
     ' `.h`). They are staged in the tree with their provenance intact, but they\n  target APIs that have moved — or, for the 11 files staged in `21ab67574` and for\n  `jtag_tcp.c` / `jtag_esp_remote.c` / `cmsis_dap_wch.c` / `aarch64_coproc_reg.c`,\n  upstream APIs that never existed. Registering them needs per-backend porting work.'),
    ('README.md',
     '- **The 12 "ready to import" TCL candidates do not survive a path check.**\n  After the subdirectory blind spot was fixed and 252 configs were imported, a\n  pass over the configs that still had no file in the tree flagged 12\n  whose `source [find ...]` references appeared to resolve. Checked against\n  full paths, none of them holds: 3 (`interface/ftdi/calao-usb-a9260-c01.cfg`,\n  `-c02.cfg`, `cc3200lp.cfg`) are already in the tree, just under\n  `tcl/interface/` rather than `tcl/interface/ftdi/`, and the 9 TI board\n  configs all `source [find interface/ti/xds100v2.cfg]` or `xds100v3.cfg`,\n  two wrappers this tree does not carry (it has `ftdi/xds100v2.cfg`). The\n  original pass matched basenames instead of paths. Importing those 9 needs\n  the two wrappers added first. Another 46 need a backend this tree does not have\n  (Infineon TriCore, Anlogic `al_link`, WCH RISC-V, the ESP32 GPIO probe, the\n  ST-LINK external loader family), 25 sit on a config that itself did not land,\n  and 5 were never fetched from the survey cache. The full breakdown is in\n  `manifest/consolidated.json` under `not_imported`; the per-file analysis of\n  the missing C backends is in `manifest/nor-driver-scan.json`.',
          '- **The “ready to import” TCL label was wrong.** After the subdirectory blind spot\n  was fixed, a pass over the configs whose `source [find ...]` targets appeared to\n  resolve flagged 12 candidates. Checked against full paths, none of them holds:\n  3 (`interface/ftdi/calao-usb-a9260-c01.cfg`, `-c02.cfg`, `cc3200lp.cfg`) are\n  already in the tree, just under `tcl/interface/` rather than\n  `tcl/interface/ftdi/`, and the 9 TI board configs all `source [find\n  interface/ti/xds100v2.cfg]` or `xds100v3.cfg`, two wrappers this tree does not\n  carry (it has `ftdi/xds100v2.cfg`). Importing those 9 needs the two wrappers\n  added first. The old "46 need a backend / 25 depend on a missing file / 5 were\n  never fetched" split came from the same hand classification and is not\n  reproduced by any tool, so it is gone. The verifiable record is\n  `manifest/consolidated.json` under `not_imported` — '
     f"{N_NOTIMPORTED}"
     ' paths, each with its\n  source commit — and the per-file analysis of the missing C backends is in\n  `manifest/nor-driver-scan.json`.'),
    ('README.md',
     "- **Three ARC board configs will not work yet.** `arc_axc001.cfg`,\n  `arc_axc002.cfg` and `arc_axc003_hs36.cfg` create targets named `arc600`,\n  `arc700` and `arcv2`. Upstream's rewritten `src/target/arc.c` only provides\n  `arcv2`; the other two come from the `arc32` family that is staged but not\n  compiled. Wiring that family up is what fixes these three configs.",
     "- **Two ARC board configs will not work yet.** `arc_axc001.cfg` and\n  `arc_axc002.cfg` create targets named `arc600` and `arc700`. Upstream's\n  rewritten `src/target/arc.c` only provides `arcv2`, and the `arc32` family that\n  would provide the other two was staged, found unbuildable and removed in\n  `7ffeda047` — so those two configs name a backend this tree does not carry.\n  (`arc_axc003_hs36.cfg` only needs `arcv2` and works.)"),
    ('README.md',
     "- **408 imported config files still use the deprecated `-chain-position`\n  option.** Upstream has no occurrence left in `tcl/`; it prints\n  `DEPRECATED! '-chain-position' will be removed in the future, use '-tap'\n  instead` from `src/target/arm_dap.c` and `src/target/target.c`, and the PLD\n  drivers warn as well. The imported files kept the spelling their fork\n  published. There are 504 occurrences; a mechanical rewrite resolves only\n  70 of them — the cases where the object's own name equals the\n  `-chain-position` value on the same line. The other 434 need a human pass,\n  because most files define their TAP in another config and the right `-tap`\n  name has to be read off that file. Nothing is broken today — the option still works — but it is the\n  first thing to fix when a config is touched.",
          '- **'
     f"{N_CPOS_FILES}"
     " imported config files still use the deprecated `-chain-position`\n  option.** Upstream's `tcl/` has already migrated to `-dap` / `-tap` (0 hits\n  there); all "
     f"{N_CPOS_HITS}"
     ' hits here are in imported third-party configs —\n  `target create` '
     f"{N_CPOS_TC}"
     ', `dap create` '
     f"{N_CPOS_DAP}"
     ', `pld create` '
     f"{N_CPOS_PLD}"
     ', the rest via\n  variable expansion. A mechanical rewrite resolves '
     f"{N_CPOS_MECH}"
     " of them, the cases where\n  the object's own name equals the `-chain-position` value on the same line. The\n  other "
     f"{N_CPOS_HUMAN}"
     ' need a human pass, because most files define their TAP in another\n  config and the right `-tap` name has to be read off that file. Nothing is broken\n  today — the option still works — but it is the first thing to fix when a config\n  is touched.'),
    ('README.md',
     "- **Three import candidates are blocked on upstream, not on this tree.**\n  The survey found support for the ESP32 GPIO bit-bang probe, the WCH\n  RISC-V debug probe and the Anlogic AL-Link probe, and they were fetched\n  and analysed. None of them can be dropped in as-is:\n  - `esp_gpio.c` / `esp_gpio.h` need the ESP-IDF GPIO and dedicated-GPIO HAL\n    (`driver/gpio.h`, `hal/gpio_ll.h`), which is not part of the OpenOCD\n    tree at all.\n  - `wlinke.c` needs a whole SDI transport layer — an `sdi.c` / `sdi.h` pair\n    under `src/jtag/` and an `sdi_ops` member on `struct adapter_driver` —\n    that upstream does not have, and `wch_riscv.c` is a private fork of\n    upstream's `riscv.c` that expects symbols upstream keeps `static`.\n  - `al_link.c` needs a `JTAG_TDI` command type, a `DEBUG_CAP_TDI_SEQ`\n    capability bit and `jtag_add_tdi_seq()` — upstream has none of them —\n    and the CyUSB backend it uses is Windows-only.\n\n  They stay in `manifest/consolidated.json` under `not_imported`, with the\n  commits they came from, so the work is not lost.",
          "- **Three staged driver sets are blocked on upstream, not on this tree.** The\n  survey found support for the ESP32 GPIO bit-bang probe, the WCH RISC-V debug\n  probe and the Anlogic AL-Link probe. All three sets are in the tree (see the\n  unwired list above), but none can be registered as-is:\n  - `esp_gpio.c` / `esp_gpio.h` need the ESP-IDF GPIO and dedicated-GPIO HAL\n    (`driver/gpio.h`, `hal/gpio_ll.h`), which is not part of the OpenOCD tree\n    at all.\n  - `wlinke.c` needs a whole SDI transport layer — an `sdi.c` / `sdi.h` pair\n    under `src/jtag/` and an `sdi_ops` member on `struct adapter_driver` — that\n    upstream does not have, and `wch_riscv.c` is a private fork of upstream's\n    `riscv.c` that expects symbols upstream keeps `static`.\n  - `al_link.c` needs a `JTAG_TDI` command type, a `DEBUG_CAP_TDI_SEQ` capability\n    bit and `jtag_add_tdi_seq()` — upstream has none of them — and the CyUSB\n    backend it uses is Windows-only.\n\n  The only import candidates still blocked on missing upstream code are the\n  "
     f"{N_BLOCKED}"
     ' Anlogic AL-Link target configs (`tcl/target/anlogic/*_al_link.cfg`).\n  Everything stays in `manifest/consolidated.json` under `not_imported`, with the\n  commits it came from, so the work is not lost.'),
    ('README.md',
     'This tree exists because 56 repositories',
          'This tree exists because '
     f"{N_SRC_REPOS}"
     ' repositories'),
    ('README.md',
     '## License',
     '## Releases\n\nFork releases are tagged `v<upstream>-fork.<n>` — an upstream `developer` point\nrelease plus a fork sequence number — and built by\n[`.github/workflows/snapshot.yml`](.github/workflows/snapshot.yml). Pushing a tag\nproduces `openocd-<tag>-x86_64-w64-mingw32.tar.gz` and the Release itself is\ncreated by CI with `gh`; nothing is published from a local machine. See\n[`docs/04-release.md`](docs/04-release.md) for the process and for the checklist\nto run before the next tag, and [`CHANGELOG.md`](CHANGELOG.md) for what changed.\n\n## License'),
    ('README.zh-CN.md',
     '扫描了 688 个候选仓库 —— 499 个上游 fork + 搜索命中的 189 个独立仓 —— 跨仓',
          '扫描了 '
     f"{N_REPOS_CSV}"
     ' 个候选仓库 —— '
     f"{N_FORKS}"
     ' 个上游 fork + 搜索命中的 '
     f"{N_INDEP}"
     ' 个独立仓 —— 跨仓'),
    ('README.zh-CN.md',
     '| `tcl/` 脚本文件 | 712 | 696 个 `.cfg` + 16 个 `.tcl`/`.xml`/`.txt`；**零构建改动即生效** |',
          '| `tcl/` 脚本文件 | '
     f"{N_TCL}"
     ' | '
     f"{N_TCL_CFG}"
     ' 个 `.cfg` + '
     f"{N_TCL_OTHER}"
     ' 个 `.tcl`/`.xml`/`.txt`；**零构建改动即生效** |'),
    ('README.zh-CN.md',
     '| `src/` C 源码 | 73 | 37 个 `.c` 加 36 个 `.h`；**47 个已接入构建**，26 个已就位但未注册 |',
          '| `src/` C 源码 | '
     f"{N_SRC}"
     ' | '
     f"{N_SRC_C}"
     ' 个 `.c` 加 '
     f"{N_SRC_H}"
     ' 个 `.h`；**'
     f"{N_WIRED}"
     ' 个已接入构建**，'
     f"{N_UNWIRED}"
     ' 个已就位但未注册 |'),
    ('README.zh-CN.md',
     '扫描识别出的 1298 条唯一路径里，**795 条在扫描当时进了树**，503 条没进。此后\n其中 11 条被有意移除（见下表最后一行），另有少量文件作为已进树配置的依赖被带了\n进来，所以**今天树里的第三方文件是 785 个**。',
          '扫描识别出的 '
     f"{N_UNIQUE}"
     ' 条唯一路径里，有 '
     f"{N_TIER1_IMPORTED}"
     ' 条 tier-1 记录被标为已导入，其中 '
     f"{N_TIER1_PRESENT}"
     ' 条至今\n仍在树里；'
     f"{N_TIER1_REMOVED}"
     ' 条导入后被有意移除，'
     f"{N_TIER1_NEVER}"
     ' 条从未落地。另有 '
     f"{N_EXTRA}"
     ' 个文件作为已进树配置的\n依赖被带了进来（它们没有自己的 tier-1 记录），所以**今天树里的第三方文件是 '
     f"{N_FILES}"
     ' 个** ——\n`tcl/` '
     f"{N_TCL}"
     ' 个 + `src/` '
     f"{N_SRC}"
     ' 个。账本闭合：'
     f"{N_TIER1_PRESENT}"
     ' + '
     f"{N_EXTRA}"
     ' = '
     f"{N_TCL}"
     '。'),
    ('README.zh-CN.md',
     '没进来的 331 个 C 源码全部需要逐后端移植：它们是某个驱动或架构的完整实现，但\n是照着旧版 OpenOCD 的 API 写的。其中 `src/target` 最大（133 个），其次是\n`src/flash`（125 个）、`src/jtag`（71 个）和 `src/server`（2 个）。',
          '没进来的 '
     f"{N_SRC_NOTIMPORTED}"
     ' 个 C 源码全部需要逐后端移植：它们是某个驱动或架构的完整实现，但\n是照着旧版 OpenOCD 的 API 写的。其中 `src/flash` 最大（'
     f"{N_SRC_NI_FLASH}"
     ' 个），其次是\n`src/target`（'
     f"{N_SRC_NI_TARGET}"
     ' 个）和 `src/jtag`（'
     f"{N_SRC_NI_JTAG}"
     ' 个）。'),
    ('README.zh-CN.md',
     '没进来的 172 个 TCL 文件分这样：\n\n| | 数量 | 原因 |\n|---|---:|---|\n| 上游已经收编 | 73 | 上游把它们挪进了子目录，扫描只看到扁平名字 |\n| 缺一个树里没有的后端 | 46 | 它们驱动的是 C 代码从未公开的探针或芯片族 —— Infineon TriCore、Anlogic `al_link` 探针、WCH RISC-V、ESP32 GPIO 探针、ST-LINK 外部加载器家族之类 |\n| 依赖的文件本身没进树 | 25 | 某条 `source [find ...]` 指向的配置没有导入 |\n| 扫描缓存里没有文件体 | 5 | 扫描记下了路径，但从未抓取文件内容 |\n| 曾判为「原样就能导入」的 12 个 | 12 | 复核后全都不成立：9 个要先补 `interface/ti/xds100v2.cfg` 或 `xds100v3.cfg`，3 个是路径误判 |\n| 导入后又从树里删掉 | 11 | 7 个冗余的 TI `swd_native` 板级配置、`target/nrf_common.cfg`、`interface/stlink-usb.cfg`、两个 `interface/calao-usb-a9260-c0*.cfg` |\n\n「原样就能导入」这一类已经不存在了。这 172 个要么缺包装文件，要么缺 C 后端，',
          '没落地的 tier-1 TCL 路径是 '
     f"{N_TIER1_NEVER}"
     ' 条 —— 机械地说，就是那些既不在树里、也没记进\n`removed_from_tree` 的 tier-1 记录。旧版这里还有一套「上游已收编 73 / 缺后端 46 /\n依赖缺失 25 / 缓存无文件体 5 / 原样可导入 12 / 导入后删除 11」的手工分类，来自更早的快照，\n现在没有任何工具能复现，已从 README 删除。可复现的是 tier-1 账本：'
     f"{N_TIER1}"
     ' 条候选、\n'
     f"{N_TIER1_IMPORTED}"
     ' 条标为已导入、'
     f"{N_TIER1_PRESENT}"
     ' 条仍在树里、'
     f"{N_TIER1_REMOVED}"
     ' 条导入后移除、'
     f"{N_TIER1_NEVER}"
     ' 条从未落地。\n\nTI 板级配置需要的那两个包装文件（`interface/ti/xds100v2.cfg`、`xds100v3.cfg`）、\n3 条早就在树里、只是落在扁平名父目录下的路径，以及依赖这两个包装文件的 '
     f"{N_XDS100_BOARD}"
     ' 份 TI 板级配置，\n都在 `manifest/consolidated.json` 的 `not_imported` 里逐文件列出（共 '
     f"{N_NOTIMPORTED}"
     ' 条）。'),
    ('README.zh-CN.md',
     '另外两组补齐了 **785 个文件**这个数，每个都有自己的来源记录：\n\n- **21 个文件是作为依赖进来的** —— 一个配置 `source` 另一个配置时，被引用的\n  文件会一起被带进来；manifest 里标为 `imported_as: dependency`。\n- **1 个文件上游也有同名版本** —— `tcl/target/adspsc58x.cfg`，内容与上游的\n  `tcl/target/adsp-sc58x.cfg` 不同。树里保留第三方版本，',
          '另外两组补齐了 **'
     f"{N_FILES}"
     ' 个文件**这个数，每个都有自己的来源记录：\n\n- **'
     f"{N_DEPENDENCY}"
     ' 个文件是作为依赖进来的** —— 一个配置 `source` 另一个配置时，被引用的\n  文件跟着一起进树。它们在 manifest 里标为 `imported_as: dependency`。\n- **1 个文件上游也有同名版本** —— `tcl/target/adspsc58x.cfg`，内容与上游的\n  `tcl/target/adsp-sc58x.cfg` 不同。树里保留第三方版本，这个同名冲突就是\n  `verify_tree` 报的 '
     f"{N_WARNS}"
     ' 条 warning 之一。'),
    ('README.zh-CN.md',
     '上游共 2203 个文件，本树 3029 个。',
          '上游共 '
     f"{N_UP}"
     ' 个文件，本树 '
     f"{N_TREE}"
     ' 个。'),
    ('README.zh-CN.md',
     '**全部 785 个导入文件都钉在它被发布时的那个 commit 上。**',
          '**全部 '
     f"{N_FILES}"
     ' 个导入文件都钉在它被发布时的那个 commit 上。**'),
    ('README.zh-CN.md',
     '本次扫描覆盖 **688 个候选仓库**，其中 56 个至少贡献了一个至今仍在树里的文件。',
          '本次扫描覆盖 **'
     f"{N_REPOS_CSV}"
     ' 个候选仓库**，其中 '
     f"{N_SRC_REPOS}"
     ' 个至少贡献了一个至今仍在树里的文件。'),
    ('README.zh-CN.md',
     '73 个新 C 源文件与头文件里有 47 个已接入构建 —— 24 个能注册出可用的',
          f"{N_SRC}"
     ' 个新 C 源文件与头文件里有 '
     f"{N_WIRED}"
     ' 个已接入构建 —— '
     f"{N_WIRED_C}"
     ' 个能注册出可用的'),
    ('README.zh-CN.md',
     '剩下 26 个 —— 13 个 `.c` 和 13 个 `.h`：`arc32` 家族、`adi_v5_cmsis_dap`、\n`aarch64_coproc_reg`，以及 `arc_ftdi_cjtag` / `cmsis_dap_wch` /\n`jtag_esp_remote` / `jtag_tcp` 驱动，加上只有它们 include 的头文件\n—— **在树里，但没被编译**。它们针对的是上游已经改过接口的 API，要注册它们，\n得先做下面说的那套移植。故意这样交付：代码在树里、可见、可审阅，在接上之前\n完全无害。\n\n### ST-LINK 外部加载器驱动\n',
          '剩下 '
     f"{N_UNWIRED}"
     ' 个 —— '
     f"{N_UNWIRED_C}"
     ' 个 `.c` 和 '
     f"{N_UNWIRED_H}"
     ' 个 `.h` —— 是**代码就位、未注册**：\n`al_link.c`、`al_link_cyusb.c`、`cmsis_dap_wch.c`、`esp_gpio.c`、`jtag_esp_remote.c`、\n`jtag_tcp.c`、`wlinke.c`、`rbb_server.c`、`aarch64_coproc_reg.c`、`wch_riscv.c`、\n`wch_riscv-013.c`，加上只被这些文件 include 的头文件（`al_link_cyusb.h`、`esp_gpio.h`、\n`rbb_server.h`、`aarch64_system_registers.h`、`aarch64_system_registers_defs.h`、\n`altera_virtual_jtag.h`、`wch_riscv.h`）。每个文件卡在哪都不一样 —— 原先列在这里的\n`arc32` 家族因为接不进构建，已在 `7ffeda047` 里删除。旧版把这 '
     f"{N_UNWIRED}"
     ' 个文件\n统一归因成「依赖上游已改名的 API」，那是错的：`jtag_tcp.c`、`jtag_esp_remote.c`、\n`cmsis_dap_wch.c`、`aarch64_coproc_reg.c` 在上游从未出现过，`21ab67574` 新导入的 11 个\n文件同样如此。`docs/02-usage.md` 里有逐文件的卡点表。'),
    ('README.zh-CN.md',
     '这个区分是必要的。本仓库的某一版曾对自己的完整性检查报出 543 处不匹配 —— 那\n棵树是在 Windows 上以文本模式重建的，每个导入文件都被悄悄存成了 CRLF，而\nmanifest 描述的是 LF 原件。门禁分不清"这个文件被改过"和"这个文件是在 Windows\n上检出的"。现在两边都修好了：树里全是 LF，785 个导入文件中有 646 个与发布方摘要\n逐字节吻合，4 个只剩行尾符差异，135 个带真实本地编辑（其中 24 个\n同时做了行尾符规整）—— target API 移植、重定位后的 `source [find ...]` 路径修正、\n第三方驱动的修复，以及 `rvmax` / `rv32m1` 两个后端。',
          '这个区分是必要的。本仓库的某一版曾对自己的完整性检查报出 543 处不匹配 —— 那\n是因为树在 Windows 上以文本模式重建，每个导入文件都被悄悄存成 CRLF，而 manifest\n描述的是 LF 原件；门禁分不清「被改过」和「在 Windows 上检出的」。现在两边都修好了：\n树里全是 LF，'
     f"{N_FILES}"
     ' 个导入文件中有 '
     f"{N_IDENTICAL}"
     ' 个与发布方摘要逐字节吻合，'
     f"{N_EOL}"
     ' 个只剩行尾符差异，\n'
     f"{N_EDITED}"
     ' 个带真实本地编辑（其中 '
     f"{N_EDITED_BOTH}"
     ' 个同时做了行尾符规整）—— 目标 API 移植、\n`source [find ...]` 路径搬移、第三方驱动的修复，以及 `rvmax` / `rv32m1` 两个后端。'),
    ('README.zh-CN.md',
     'recorded : 785',
          'recorded : '
     f"{N_FILES}"),
    ('README.zh-CN.md',
     'on disk  : 785',
          'on disk  : '
     f"{N_FILES}"),
    ('README.zh-CN.md',
     'warns    : 23',
          'warns    : '
     f"{N_WARNS}"),
    ('README.zh-CN.md',
     '23 条 warning 是：一个文件名与上游同名但内容不同（有意保留），以及 22 个',
          f"{N_WARNS}"
     ' 条 warning 是：一个文件名与上游同名但内容不同（有意保留），以及 '
     f"{N_UNRESOLVED}"
     ' 个'),
    ('README.zh-CN.md',
     '| [`manifest/PROVENANCE.json`](manifest/PROVENANCE.json) | 785 个导入文件的机器可读来源记录 |',
          '| [`manifest/PROVENANCE.json`](manifest/PROVENANCE.json) | '
     f"{N_FILES}"
     ' 个导入文件的机器可读来源记录 |'),
    ('README.zh-CN.md',
     '**导入的第三方文件不在这个总括声明的覆盖范围内。** 785 个文件里，GitHub 解析出\n135 个为 GPL-2.0、1 个为 GPL-2.0-or-later、627 个为 `NOASSERTION`（意思是\n*GitHub 判定不出许可证*，不是说它宽松），22 个无法解析。有些 `NOASSERTION` 文件',
          '**导入的第三方文件不在这个总括声明的覆盖范围内。** '
     f"{N_FILES}"
     ' 个文件里，GitHub 解析出\n'
     f"{N_GPL2}"
     ' 个为 GPL-2.0、'
     f"{N_GPL2L}"
     ' 个为 GPL-2.0-or-later、'
     f"{N_NOASSERT}"
     ' 个为 `NOASSERTION`（意思是\n*GitHub 判定不出许可证*，不是说它宽松），'
     f"{N_UNRESOLVED}"
     ' 个无法解析。这些 `NOASSERTION` 文件'),
    ('README.zh-CN.md',
     '- **「12 个原样就能导入」的候选经完整路径复核后全都不成立。** 补齐扫描的子目录\n  盲区、又导入了 252 个配置之后，对剩下还没有文件的配置重新评估了一遍，\n  挑出 12 个 `source [find ...]` 看似可解析的候选。按完整路径逐条核对：其中 3 个\n  （`interface/ftdi/calao-usb-a9260-c01.cfg`、`-c02.cfg`、`cc3200lp.cfg`）早就在\n  树里，只是落在 `tcl/interface/` 而不是 `tcl/interface/ftdi/`；剩下 9 个 TI 板级\n  配置都 `source [find interface/ti/xds100v2.cfg]` 或 `xds100v3.cfg`，而这两个\n  包装文件树里没有（树里只有 `ftdi/xds100v2.cfg`）。原判定按文件名而非路径比对。\n  要导入那 9 个，得先补两个包装文件。另有 46 个需要树里\n  还没有的后端（Infineon TriCore、Anlogic `al_link`、WCH RISC-V、ESP32 GPIO\n  探针、ST-LINK 外部加载器家族），25 个依赖的配置本身没进树，5 个在扫描缓存里\n  没有文件体。逐项分类见 `manifest/consolidated.json` 的 `not_imported` 段，\n  缺失 C 后端的文件级分析见 `manifest/nor-driver-scan.json`。',
          '- **「12 个原样就能导入」的候选经完整路径复核后全都不成立。** 补齐扫描的子目录\n  盲区之后，对剩下还没有文件的配置重新评估了一遍，挑出 12 个 `source [find ...]`\n  看似可解析的候选。按完整路径逐条核对：其中 3 个\n  （`interface/ftdi/calao-usb-a9260-c01.cfg`、`-c02.cfg`、`cc3200lp.cfg`）早就在\n  树里，只是落在 `tcl/interface/` 而不是 `tcl/interface/ftdi/`；剩下 9 个 TI 板级\n  配置都 `source [find interface/ti/xds100v2.cfg]` 或 `xds100v3.cfg`，而这两个\n  包装文件树里没有（树里只有 `ftdi/xds100v2.cfg`）。原判定按文件名而非路径比对。\n  要导入那 9 个，得先补两个包装文件。\n\n  旧版这里还有一段「46 个需要后端 / 25 个依赖没进树 / 5 个缓存里没文件体」的手工分类，\n  来自同一份更早的快照，已删除。可查的权威记录是 `manifest/consolidated.json` 的\n  `not_imported`（'
     f"{N_NOTIMPORTED}"
     ' 条，逐文件带来源 commit），缺 C 后端的逐文件分析在\n  `manifest/nor-driver-scan.json`。'),
    ('README.zh-CN.md',
     '- **73 个新 C 源文件与头文件里有 26 个没被编译**（13 个 `.c`、13 个 `.h`）。\n  它们带着完整来源记录躺在树里，但针对的是已经改过接口的上游 API。\n  要注册需要逐个后端做移植。',
          '- **'
     f"{N_SRC}"
     ' 个新 C 源文件与头文件里有 '
     f"{N_UNWIRED}"
     ' 个没被编译**（'
     f"{N_UNWIRED_C}"
     ' 个 `.c`、'
     f"{N_UNWIRED_H}"
     ' 个 `.h`）。\n  它们带着完整来源记录留在树里，但依赖已经变动的上游 API —— 或者（`21ab67574` 新导入的\n  11 个文件，以及 `jtag_tcp.c`、`jtag_esp_remote.c`、`cmsis_dap_wch.c`、`aarch64_coproc_reg.c`）\n  依赖上游从未有过的 API。要注册它们，得逐后端移植。'),
    ('README.zh-CN.md',
     '- **三份 ARC 板级配置目前还用不了。** `arc_axc001.cfg`、`arc_axc002.cfg`、\n  `arc_axc003_hs36.cfg` 创建的是 `arc600`、`arc700`、`arcv2` 三种 target。\n  上游重写过的 `src/target/arc.c` 只提供 `arcv2`，另外两个来自那族已就位但\n  未接线的 `arc32` 源码。把那族接进构建，这三份配置就能用了。',
     '- **两份 ARC 板级配置目前还用不了。** `arc_axc001.cfg`、`arc_axc002.cfg` 创建的是\n  `arc600`、`arc700` 两种 target。上游重写过的 `src/target/arc.c` 只提供 `arcv2`，\n  而本该提供另外两个的 `arc32` 家族已就位、被判定接不进构建并在 `7ffeda047` 里删除 ——\n  所以这两份配置指向的后端本树根本没有。（`arc_axc003_hs36.cfg` 只需要 `arcv2`，可用。）'),
    ('README.zh-CN.md',
     "- **408 个导入的配置还在用已废弃的 `-chain-position`。** 上游的 `tcl/` 里已经\n  一处不剩；`src/target/arm_dap.c` 和 `src/target/target.c` 都会打印\n  `DEPRECATED! '-chain-position' will be removed in the future, use '-tap'\n  instead`，PLD 驱动那边也会警告。导入的文件保留了它们各自 fork 里发布的\n  写法。全树共 504 处，机械替换只能自动解掉其中 70 处 —— 也就是对象名与\n  `-chain-position` 取值在同一行且完全相同的情况。剩下 434 处要人工过一遍：\n  多数文件的 TAP 是在另一个配置里定义的，对应的 `-tap` 名字得从那个文件里读出来。\n  目前不影响使用，这个选项还有效，但改到哪个配置就顺手改掉哪个。",
          '- **'
     f"{N_CPOS_FILES}"
     ' 个导入的配置还在用已废弃的 `-chain-position`。** 上游的 `tcl/` 里已经是\n  0 处（全部改用 `-dap` / `-tap`）；这 '
     f"{N_CPOS_HITS}"
     ' 处全在导入的第三方配置里 —— `target create`\n  '
     f"{N_CPOS_TC}"
     ' 处、`dap create` '
     f"{N_CPOS_DAP}"
     ' 处、`pld create` '
     f"{N_CPOS_PLD}"
     ' 处，其余靠变量拼接。机械替换只能\n  自动解掉 '
     f"{N_CPOS_MECH}"
     ' 处（对象名与取值在同一行且完全相同），其余 '
     f"{N_CPOS_HUMAN}"
     ' 处要人工过一遍：\n  多数文件在别的配置里定义 TAP，正确的 `-tap` 名得从那个文件里读出来。今天这不算坏 ——\n  选项仍然可用 —— 但下次动某个配置时，这是第一件该修的事。'),
    ('README.zh-CN.md',
     '- **三组导入候选被卡在上游，而不是被卡在这棵树上。** 扫描发现了 ESP32 GPIO\n  bit-bang 探针、WCH RISC-V 调试探针和 Anlogic AL-Link 探针的支持，文件也已经\n  取回来分析过，但三组都没法原样落地：\n  - `esp_gpio.c` / `esp_gpio.h` 依赖整套 ESP-IDF 的 GPIO 与 dedicated-GPIO\n    HAL（`driver/gpio.h`、`hal/gpio_ll.h`），OpenOCD 树里根本不存在。\n  - `wlinke.c` 需要一整套 SDI transport 层 —— `src/jtag/` 下的 `sdi.c` /\n    `sdi.h` 一对文件，外加 `struct adapter_driver` 上的 `sdi_ops` 成员，\n    上游没有；\n    而 `wch_riscv.c` 是上游 `riscv.c` 的私有分叉，依赖上游标成 `static`\n    的符号。\n  - `al_link.c` 需要 `JTAG_TDI` 命令类型、`DEBUG_CAP_TDI_SEQ` 能力位和\n    `jtag_add_tdi_seq()` —— 上游一个都没有 —— 而且它用的 CyUSB 后端只支持\n    Windows。\n\n  它们仍然记录在 `manifest/consolidated.json` 的 `not_imported` 里，连同来源\n  commit，工作不会白做。\n\n---\n',
          '- **三组已就位的驱动被卡在上游，而不是被卡在这棵树上。** 扫描发现了 ESP32 GPIO\n  bit-bang 探针、WCH RISC-V 调试探针和 Anlogic AL-Link 探针的支持。三组代码都在\n  树里（见上面的未接线清单），但没有一组能原样注册：\n  - `esp_gpio.c` / `esp_gpio.h` 需要 ESP-IDF 的 GPIO 与 dedicated-GPIO HAL\n    （`driver/gpio.h`、`hal/gpio_ll.h`），那根本不在 OpenOCD 树里。\n  - `wlinke.c` 需要整套 SDI transport 层 —— `src/jtag/` 下的 `sdi.c` / `sdi.h`\n    和 `struct adapter_driver` 上的 `sdi_ops` 成员 —— 上游都没有；`wch_riscv.c`\n    则是上游 `riscv.c` 的私有分支，期望上游保持 `static` 的符号。\n  - `al_link.c` 需要 `JTAG_TDI` 命令类型、`DEBUG_CAP_TDI_SEQ` 能力位和\n    `jtag_add_tdi_seq()` —— 上游一个都没有 —— 而它用的 CyUSB 后端仅限 Windows。\n\n  仍然因为上游缺代码而挡住导入的，只剩 '
     f"{N_BLOCKED}"
     ' 份 Anlogic AL-Link 目标配置\n  （`tcl/target/anlogic/*_al_link.cfg`）。所有记录都留在 `manifest/consolidated.json`\n  的 `not_imported` 里，带来源 commit，工作不会丢。'),
    ('README.zh-CN.md',
     '这棵树之所以存在，是因为 56 个别人的仓库',
          '这棵树之所以存在，是因为 '
     f"{N_SRC_REPOS}"
     ' 个别人的仓库'),
    ('README.zh-CN.md',
     '## 许可',
     '## 发布\n\n本 fork 的发布 tag 形如 `v<上游版本>-fork.<n>` —— 上游 `developer` 线上的一个点版本\n加 fork 序号 —— 由 [`.github/workflows/snapshot.yml`](.github/workflows/snapshot.yml)\n构建。推一个 tag 会产出 `openocd-<tag>-x86_64-w64-mingw32.tar.gz`，Release 本体由 CI\n用 `gh` 生成；本机不发布任何东西。流程与打下一个 tag 前必须跑的清单见\n[`docs/04-release.md`](docs/04-release.md)，改了什么见 [`CHANGELOG.md`](CHANGELOG.md)。\n\n## 许可'),
    ('docs/00-findings.md',
     '**2199 个 blob**',
          '**'
     f"{N_UP}"
     ' 个 blob**'),
    ('docs/00-findings.md',
     '`ch32`、`py32`、`puya`、`nuvoton`、`aurix`、`tamarin`、`at32`、`aic88`。',
     '`ch32`、`py32`、`puya`、`nuvoton`、`aurix`、`tamarin`、`aic88`。\n\n> 这份清单原先还列了 `at32`，那是**错的**：上游 `upstream/master` 的 `tcl/` 里已经有\n> `tcl/target/artery/at32f4x.cfg`（`git grep -c at32 upstream/master -- tcl/` 命中 1 个文件），\n> 所以 `at32` 不能算「搜索不到」。其余 7 个关键字的复核结果都是 0 命中。'),
    ('docs/00-findings.md',
     '## 3. 各厂商现状（已上游 vs 仍 fork-only）',
     '## 3. 各厂商现状（已上游 vs 仍 fork-only）\n\n> 下表的文件计数来自扫描阶段的原始数据（`raw/` 池），**不可从当前树复算**；\n> 「已上游 / 仍 fork-only」的判定已用 `git grep upstream/master` 复核过。'),
    ('docs/00-findings.md',
     '| `tcl/target/ti/cc13x0.cfg` | `tcl/target/ti_cc13x0.cfg` | `tcl/target/ti/cc13x0.cfg` |',
     '| `tcl/target/ti/cc13x0.cfg` | `tcl/target/ti_cc13x0.cfg` | `tcl/target/ti/cc13x0.cfg` |\n\n> 注：中列那个扁平名 `tcl/target/ti_cc13x0.cfg` 在本树里**不存在** —— 它作为与上游等价的\n> 重复项被剔除了（记在 `manifest/consolidated.json` 的 `excluded` 口径里）。本树里只有\n> 上游形态 `tcl/target/ti/cc13x0.cfg`。'),
    ('docs/00-findings.md',
     '把它误判成新增，**凭空多出 26 个假的 TI 支持文件**。',
     '把它误判成新增，**凭空多出 26 个假的 TI 支持文件**（那是当时那次错误比对的结果；26 这个数字不可从当前树复算）。'),
    ('docs/02-usage.md',
     '本仓库是 `openocd-org/openocd` 的 fork。扫描 GitHub 上 **688 个** OpenOCD\n相关仓库（499 个官方 fork + 搜索命中的 189 个独立仓），跨仓去重、剔除与官方等价的\n副本后，得到 **785 个文件**的第三方支持，全部合并在**它们本该在的位置**：',
          '本仓库是 `openocd-org/openocd` 的 fork。扫描 GitHub 上 **'
     f"{N_REPOS_CSV}"
     ' 个** OpenOCD\n相关仓库（'
     f"{N_FORKS}"
     ' 个官方 fork + 搜索命中的 '
     f"{N_INDEP}"
     ' 个独立仓；排名表含本 fork 自身，\n`manifest/survey.json` 记 '
     f"{N_REPOS_SURVEY}"
     '），跨仓去重、剔除与官方等价的\n副本后，得到 **'
     f"{N_FILES}"
     ' 个文件**的第三方支持（`tcl/` '
     f"{N_TCL}"
     ' 个 + `src/` '
     f"{N_SRC}"
     ' 个），\n全部合并在**它们本该在的位置**：'),
    ('docs/02-usage.md',
     '- **713 个 `tcl/` 配置** —— 零修改、零重编译即可使用；',
          '- **'
     f"{N_TCL}"
     ' 个 `tcl/` 配置** —— 零修改、零重编译即可使用；'),
    ('docs/02-usage.md',
     '- **73 个 `src/` C 源文件与头文件** —— 已就位，其中 **47 个已接入构建**，\n  其余 26 个仍需按上游现有 API 改写后才能注册。',
          '- **'
     f"{N_SRC}"
     ' 个 `src/` C 源文件与头文件** —— 已就位，其中 **'
     f"{N_WIRED}"
     ' 个已接入构建**，\n  其余 '
     f"{N_UNWIRED}"
     ' 个仍需按上游现有 API 改写后才能注册。'),
    ('docs/02-usage.md',
     'tcl/                     ← OpenOCD 配置树：官方配置 + 712 个第三方配置\n  target/                     907  芯片目标配置（含 vendor 子目录）\n  board/                      597  开发板配置（含 flash_algorithms/）\n  interface/                  217  调试器接口\n  cpld/                        21  CPLD 配置\n  fpga/                        34  FPGA bitstream\n  chip/                        28  芯片公共片段\n  cpu/                         10  架构公共片段\n\nsrc/                     ← C 源码：官方源码 + 73 个第三方驱动/目标\n  target/                     149  顶层 .c（其中 20 个是第三方新架构：ARC32 / LoongArch / C28x / TMS320 / Vortex86 / VexRiscv / Quark / Microchip RI4 ...）\n  target/rvmax/                9  文件，3 个 .c（ADI RVMAX 后端）\n  target/rv32m1/               6  文件，3 个 .c（SiFive RV32M1 后端）\n  jtag/drivers/                76  顶层 .c（其中 9 个是第三方适配器）\n  flash/nor/                    2  第三方 NOR 驱动（rv32m1、ST-LINK 外部加载器 stldr）',
          'tcl/                     ← OpenOCD 配置树：官方配置 + '
     f"{N_TCL}"
     ' 个第三方配置\n  target/                      '
     f"{N_TCL_SUB_TARGET}"
     '  芯片目标配置（含 vendor 子目录）\n  board/                       '
     f"{N_TCL_SUB_BOARD}"
     '  开发板配置（含 flash_algorithms/）\n  interface/                   '
     f"{N_TCL_SUB_INTERFACE}"
     '  调试器接口\n  cpld/                        '
     f"{N_TCL_SUB_CPLD}"
     '  CPLD 配置\n  fpga/                        '
     f"{N_TCL_SUB_FPGA}"
     '  FPGA bitstream\n  chip/                        '
     f"{N_TCL_SUB_CHIP}"
     '  芯片公共片段\n  cpu/                         '
     f"{N_TCL_SUB_CPU}"
     '  架构公共片段\n\nsrc/                     ← C 源码：官方源码 + '
     f"{N_SRC}"
     ' 个第三方驱动/目标\n  target/                      '
     f"{N_ST_TOPC_GIT}"
     '  顶层 .c（其中 '
     f"{N_ST_TOPC_TP}"
     ' 个是第三方新架构：LoongArch / C28x / TMS320 / Vortex86 / VexRiscv / Quark / Microchip RI4 / WCH RISC-V …）\n  target/rvmax/                '
     f"{N_RVMAX_FILES}"
     '  文件，3 个 .c（ADI RVMAX 后端）\n  target/rv32m1/               '
     f"{N_RV32M1_FILES}"
     '  文件，3 个 .c（SiFive RV32M1 后端）\n  jtag/drivers/                '
     f"{N_JD_TOPC_GIT}"
     '  顶层 .c（其中 '
     f"{N_JD_TOPC_TP}"
     ' 个是第三方适配器）\n  flash/nor/                   '
     f"{N_FLASH_NOR_TP}"
     '  第三方 NOR 驱动（rv32m1、ST-LINK 外部加载器 stldr）'),
    ('docs/02-usage.md',
     '  PROVENANCE.json            785  个文件的来源仓库/分支/commit/SHA-256/许可证',
          '  PROVENANCE.json            '
     f"{N_FILES}"
     '  个文件的来源仓库/分支/commit/SHA-256/许可证'),
    ('docs/02-usage.md',
     '  repos.csv / repos.json      688 个候选仓库排名\n  licenses.csv               785  行许可证索引（逐文件）',
          '| `repos.csv` / `repos.json` | '
     f"{N_REPOS_CSV}"
     ' 行候选仓库排名（'
     f"{N_FORKS}"
     ' 个上游 fork + '
     f"{N_INDEP}"
     ' 个独立仓；含本 fork 自身，`survey.json` 的 '
     f"{N_REPOS_SURVEY}"
     ' 不含自身）|\n| `licenses.csv` | '
     f"{N_FILES}"
     '  行许可证索引（逐文件）|'),
    ('docs/02-usage.md',
     '> **894 vs 712**：`manifest/consolidated.json` 里有 894 条 tier-1 记录（上游确实没有的\n> 独立 TCL 支持项），其中 **722 条进了树**，172 条没进（分类见下）。\n> 这 722 条里有 **15 条后来被有意移除**（7 个冗余的 TI `swd_native` 板级配置、\n> 5 个上游已用 ASCII 名提供的西里尔名配置等，见下表最后一行），余下 707 条在树。\n> 一个配置 `source` 另一个配置时，被引用的文件会一起被带进来\n> （如 `tcl/interface/ftdi/*.cfg`、`tcl/board/flash_algorithms/*.cfg`），\n> 这类「只作为依赖进来、不在 imported 记录里」的文件共 5 个\n> （`tcl/chip/motorola/hsb.cfg`、`tcl/cpu/arc/arcompact.tcl`、\n> `tcl/fpga/xilinx-xc3s.cfg`、`tcl/gdb_helper.tcl`、\n> `tcl/target/adspsc58x.cfg`）。\n> 所以 `tcl/` 下的第三方文件数是 722 − 15 + 5 = **712**，与\n> `manifest/PROVENANCE.json` 核对一致（该文件的 `tcl/` 条目数也是 712）。',
          '> **'
     f"{N_TIER1}"
     ' vs '
     f"{N_TCL}"
     '**：`manifest/consolidated.json` 里有 '
     f"{N_TIER1}"
     ' 条 tier-1 记录（上游确实没有的\n> 独立 TCL 支持项），其中 **'
     f"{N_TIER1_IMPORTED}"
     ' 条被标为已导入**，'
     f"{N_TIER1_PRESENT}"
     ' 条今天还在树里，\n> '
     f"{N_TIER1_REMOVED}"
     ' 条导入后被有意移除（见下表最后一行），'
     f"{N_TIER1_NEVER}"
     ' 条从未落地（既不在树里，\n> 也不在 `removed_from_tree` 里）。\n>\n> 另有 '
     f"{N_EXTRA}"
     ' 个文件「只作为依赖进来、不在 imported 记录里」\n> （`tcl/chip/motorola/hsb.cfg`、`tcl/cpu/arc/arcompact.tcl`、`tcl/fpga/xilinx-xc3s.cfg`、\n> `tcl/gdb_helper.tcl`、`tcl/target/adspsc58x.cfg`）。所以 `tcl/` 下的第三方文件数是\n> '
     f"{N_TIER1_PRESENT}"
     ' + '
     f"{N_EXTRA}"
     ' = **'
     f"{N_TCL}"
     '**，与 `manifest/PROVENANCE.json` 核对一致\n> （该文件的 `tcl/` 条目数也是 '
     f"{N_TCL}"
     '）。'),
    ('docs/02-usage.md',
     '> **那 12 个「原样就能导入」的候选经复核并不成立。** 补齐子目录盲区并导入\n> 252 个配置之后，对剩下还没进树的配置重新评估，其中 12 个曾判定为\n> `source [find ...]` 引用全部可解析。按完整路径复核后，12 个全都不成立：\n> 3 个（`interface/ftdi/calao-usb-a9260-c01.cfg`、`-c02.cfg`、`cc3200lp.cfg`）\n> 早已在树里，只是落在 `tcl/interface/` 而不是 `tcl/interface/ftdi/`；\n> 另外 9 个 TI 板级配置都 `source [find interface/ti/xds100v2.cfg]` 或\n> `ti/xds100v3.cfg`，而这两个包装文件树里没有（树里只有 `ftdi/xds100v2.cfg`）。\n> 原来的判定按文件名而非路径比对，把 `ftdi/xds100v2.cfg` 当成了 `ti/xds100v2.cfg`。\n> 要导入那 9 个，得先补两个包装文件。另有 46 个需要树里还没有的后端\n> （Infineon TriCore、Anlogic `al_link`、WCH RISC-V、ESP32 GPIO 探针、\n> ST-LINK 外部加载器家族等），25 个依赖的配置本身没进树，5 个在扫描缓存里\n> 没有文件体。另有 11 个导入后又从树里删掉：7 个重复的 TI 板级配置、\n> `target/nrf_common.cfg`、`interface/stlink-usb.cfg`、两个\n> `interface/calao-usb-a9260-c0*.cfg`。\n> 与官方重复的文件在 `consolidate.py` **写 manifest 时**就剔除了，所以重跑抓取器\n> 不会把已剔除的副本再拉回来。\n>\n> **全部 785 个文件都锁定了来源 commit**，可逐文件追溯到具体 fork 的具体提交。',
          '> **那 12 个「原样就能导入」的候选经复核并不成立。** 补齐子目录盲区之后，对剩下还没进树的\n> 配置重新评估，其中 12 个曾判定为 `source [find ...]` 引用全部可解析。按完整路径复核后，\n> 12 个全都不成立：3 个（`interface/ftdi/calao-usb-a9260-c01.cfg`、`-c02.cfg`、\n> `cc3200lp.cfg`）早就在树里，只是落在 `tcl/interface/` 而不是 `tcl/interface/ftdi/`；\n> 另外 9 个 TI 板级配置都 `source [find interface/ti/xds100v2.cfg]` 或 `ti/xds100v3.cfg`，\n> 而这两个包装文件树里没有（树里只有 `ftdi/xds100v2.cfg`）。原来的判定按文件名而非路径比对。\n> 要导入那 9 个，得先补两个包装文件。\n>\n> 旧版这里还写了一套「46 需要后端 / 25 依赖没进树 / 5 没文件体」的手工分类，来自更早的快照，\n> 现在没有任何工具能复现，已删除。可复现的是 tier-1 账本与 `manifest/consolidated.json`\n> 的 `not_imported`（'
     f"{N_NOTIMPORTED}"
     ' 条，逐文件可查）。\n>\n> **全部 '
     f"{N_FILES}"
     ' 个文件都锁定了来源 commit**，可逐文件追溯到具体 fork 的具体提交。'),
    ('docs/02-usage.md',
     '`src/` 下 73 个第三方文件里（37 个 `.c` + 36 个 `.h`），**47 个已经接入构建系统**，\n其余 26 个（13 个 `.c` + 13 个 `.h`）仍是「代码就位、未注册」的状态。',
          '`src/` 下 '
     f"{N_SRC}"
     ' 个第三方文件里（'
     f"{N_SRC_C}"
     ' 个 `.c` + '
     f"{N_SRC_H}"
     ' 个 `.h`），**'
     f"{N_WIRED}"
     ' 个已经接入构建系统**，\n其余 '
     f"{N_UNWIRED}"
     ' 个（'
     f"{N_UNWIRED_C}"
     ' 个 `.c` + '
     f"{N_UNWIRED_H}"
     ' 个 `.h`）仍是「代码就位、未注册」的状态。'),
    ('docs/02-usage.md',
     '### 仍是「代码就位、未注册」（其余 26 个文件）\n\n13 个 `.c`：\n\n- `src/jtag/drivers/`：`arc_ftdi_cjtag.c`、`cmsis_dap_wch.c`、\n  `jtag_esp_remote.c`、`jtag_tcp.c`\n- `src/target/`：`aarch64_coproc_reg.c`、`adi_v5_cmsis_dap.c`、`arc32.c`、\n  `arc_core.c`、`arc_dbg.c`、`arc_mntr.c`、`arc_ocd.c`、`arc_regs.c`、`arc_trgt.c`\n\n13 个 `.h` 只被上面这些文件 include，主树没有任何引用，因此也没有进\n`*_SOURCES`：`arc32.h`、`arc_core.h`、`arc_dbg.h`、`arc_mntr.h`、`arc_ocd.h`、\n`arc_regs.h`、`arc_trgt.h`、`arc_ftdi_cjtag.h`、`jtag_usb_common.h`、\n`aarch64_system_registers.h`、`aarch64_system_registers_defs.h`、\n`altera_virtual_jtag.h`、`stm8.h`。',
          '### 仍是「代码就位、未注册」（其余 '
     f"{N_UNWIRED}"
     ' 个文件）\n\n'
     f"{N_UNWIRED_C}"
     ' 个 `.c`：\n\n- `src/jtag/drivers/`：`al_link.c`、`al_link_cyusb.c`、`cmsis_dap_wch.c`、`esp_gpio.c`、\n  `jtag_esp_remote.c`、`jtag_tcp.c`、`wlinke.c`\n- `src/server/`：`rbb_server.c`\n- `src/target/`：`aarch64_coproc_reg.c`、`wch_riscv.c`、`wch_riscv-013.c`\n\n'
     f"{N_UNWIRED_H}"
     ' 个 `.h` 只被上面这些文件 include，主树没有任何引用，因此也没有进\n`*_SOURCES`：`al_link_cyusb.h`、`esp_gpio.h`、`rbb_server.h`、\n`aarch64_system_registers.h`、`aarch64_system_registers_defs.h`、\n`altera_virtual_jtag.h`、`wch_riscv.h`。'),
    ('docs/02-usage.md',
     '> `src/jtag/drivers/OpenULINK/src/` 下的 4 个 `.c` 不算在内 —— 那是 OpenULINK',
          '> `src/jtag/drivers/OpenULINK/src/` 下的 '
     f"{N_OPENULINK}"
     ' 个 `.c` 不算在内 —— 那是 OpenULINK'),
    ('docs/02-usage.md',
     '| 未接入的文件 | 卡点 |\n|---|---|\n| `src/jtag/drivers/jtag_tcp.c`、`cmsis_dap_wch.c` | `.transports` 字段 —— 上游已改成 `unsigned int transport_ids`，`jtag_only` 常量也不存在了；`jtag_tcp.c` 还在调用 `jtag_vpi_tms`/`jtag_vpi_path_move`，而这两个是 `jtag_vpi.c` 里的 `static` |\n| `src/target/arc32.c` + `arc_core.c` + `arc_dbg.c` + `arc_mntr.c` + `arc_ocd.c` + `arc_regs.c` + `arc_trgt.c` | 与上游 `src/target/arc.c` 的 `arcv2_target` **重复定义**，且 `arc32.c` 调用的 9 个 `arc_mem_*` 入口只存在于它自己那份 `arc_mem.c`；本树的 `arc_mem.c` 是上游精简版，只有 `arc_mem_read`/`arc_mem_write`，链接必然失败（CI 已验证） |\n| `src/target/adi_v5_cmsis_dap.c`、`aarch64_coproc_reg.c` | 依赖上游未公开的私有 API |\n| `src/jtag/drivers/arc_ftdi_cjtag.c`、`cmsis_dap_wch.c` | 依赖 `mpsse_read`/`mpsse_write`，本树的 `mpsse.h`/`mpsse.c` 里这两个函数不存在（只有 `mpsse_read_data_bits_low_byte` 一族）；`cmsis_dap_wch.c` 另需已删除的 SDI 传输层 |\n\n> `tcl/target/arc_axc001.cfg` 等 ARC 板级配置在树里。上游 `arc.c` 只注册 `arcv2`\n> 一个 target type，而 `arc32.c` 一族因为依赖它自己那份 `arc_mem.c`（本树里是\n> 上游的精简版，只有 `arc_mem_read`/`arc_mem_write`）接不进构建，所以这些配置\n> 统一改用 `arcv2`。代价是它们描述的 ARC600/ARC700 内核只能按 ARCv2 访问。',
     '| 未接入的文件 | 卡点 |\n|---|---|\n| `src/jtag/drivers/jtag_tcp.c`、`cmsis_dap_wch.c` | `.transports` 字段 —— 上游已改成 `unsigned int transport_ids`，`jtag_only` 常量也不存在了；`jtag_tcp.c` 还在调用 `jtag_vpi_tms`/`jtag_vpi_path_move`，而这两个是 `jtag_vpi.c` 里的 `static` |\n| `src/target/aarch64_coproc_reg.c`、`src/jtag/drivers/esp_gpio.c`、`jtag_esp_remote.c`、`wlinke.c`、`al_link.c`、`al_link_cyusb.c`、`src/target/wch_riscv.c`、`wch_riscv-013.c`、`src/server/rbb_server.c` | 上游从未有过这些文件和它们依赖的 API：ESP-IDF GPIO HAL、SDI transport 层、`JTAG_TDI` / `DEBUG_CAP_TDI_SEQ` / `jtag_add_tdi_seq()`。见下面「被上游阻塞」一节 |\n\n> `tcl/target/arc_axc001.cfg` 等 ARC 板级配置在树里。上游 `arc.c` 只注册 `arcv2`\n> 一个 target type；本该提供 `arc600`/`arc700` 的 `arc32` 家族（连同它自己那份\n> `arc_mem.c`）已就位但接不进构建，并已在 `7ffeda047` 里删除。所以这些配置\n> 只能按 `arcv2` 访问，代价是 ARC600/ARC700 内核的细节访问不可用。'),
    ('docs/02-usage.md',
     "**悬空的接口配置。** 扫全部 `tcl/`，有 6 个 `adapter driver` / `interface`\n指令指向源码里不存在的驱动名，共 8 处：\n\n| 配置 | 指令 | 驱动名 |\n|---|---|---|\n| `tcl/interface/jtag_tcp.cfg:7` | `interface jtag_tcp` | `jtag_tcp`（上面未接入） |\n| `tcl/interface/jtag_esp_remote.cfg:5` | `adapter driver jtag_esp_remote` | `jtag_esp_remote`（上面未接入） |\n| `tcl/interface/picoprobe.cfg:2` | `adapter driver picoprobe` | `picoprobe` |\n| `tcl/interface/colobus.cfg:1` | `interface colobus` | `colobus` |\n| `tcl/interface/tamarin.cfg:1`、`tcl/interface/faultier.cfg:1` | `interface tamarin` | `tamarin` |\n| `tcl/interface/tas_client.cfg:7` | `adapter driver tas_client` | `tas_client` |\n| `tcl/interface/nds32-aice.cfg:9` | `adapter driver aice` | `aice` |\n| `tcl/board/altera_arria10__aji_client.cfg:8`、`tcl/board/altera_arria10_niosv__aji_client.cfg:15` | `adapter driver aji_client` | `aji_client` |\n\n后 6 个（`picoprobe`、`colobus`、`tamarin`、`tas_client`、`aice`、`aji_client`）\n在**上游同样没有驱动实现**，配置是各 fork 单独加的，属于上游本身的悬空；\n`nds32-aice.cfg` 依赖的 `nds32_aice.c` 已被本 fork 从树里移除\n（见 `removed_from_tree`）。这些配置加载时会报 `Can't find adapter driver`。\n`jtag_tcp`/`jtag_esp_remote` 两份是给上面那两个待接入驱动预留的用法说明，\n驱动一旦按上面那条路接通就不需要改。\n\n来源（`manifest/PROVENANCE.json`）：`picoprobe` ← `sysprogs/openocd`，\n`colobus` ← `tihmstar/openocd_colobus`，`tamarin`/`faultier` ←\n`stacksmashing/openocd-tamarin`，`tas_client` ← `zuyih/openocd`，\n`nds32-aice` ← `zephyrproject-rtos/openocd`，`aji_client` ←\n`OlivierVanWassenhove-Dekimo/openocd`。这些 fork 都带自己的驱动实现，\n但实现没进本树，所以配置是悬空的。",
          '**悬空引用扫描。** `tools/audit_dangling_refs.py` 扫全部 `tcl/`（1771 个 `.cfg` + 47 个 `.tcl`），\n解析出 1942 条 `source [find ...]` 引用，其中 '
     f"{N_DANGLING}"
     ' 条无法解析，全部无害：\n\n| 无法解析的引用 | 出现位置 | 说明 |\n|---|---|---|\n| `tcl/aic8800.cfg`、`tcl/aic8800m40.cfg`、`tcl/aic8800mc.cfg` | `tcl/interface/cmsis-dap_v2_aic8800*.cfg` | 注释行里的路径 |\n| `tcl/target/...cfg` | 5 个板级配置 | 上游自带的文档模板占位符 |\n| `tcl/tcl/tools/memtest.tcl` | `tcl/target/saxon_xip.cfg` | 注释行里多写了一级 |\n\n> 更早的一版这里列过一张「悬空的接口配置」表（`jtag_tcp.cfg`、`jtag_esp_remote.cfg`、\n> `picoprobe.cfg`、`colobus.cfg`、`tamarin.cfg`、`faultier.cfg`、`tas_client.cfg`、\n> `nds32-aice.cfg`、`altera_arria10__aji_client.cfg`、`altera_arria10_niosv__aji_client.cfg`）。\n> 那 10 个配置文件已经不在树里（都记在 `manifest/PROVENANCE.json` 的 `removed_from_tree` 里），\n> 所以那张表连同它引用的 6 个驱动名一起删掉了 —— 树里已经没有这种悬空。\n> 逐条证据用 `python tools/audit_dangling_refs.py` 复跑。'),
    ('docs/02-usage.md',
     '- `GPL-2.0`：136 个文件，来源明确。\n- `GPL-2.0-or-later`：1 个文件（`src/flash/nor/stldr_driver.c`，来自 STMicroelectronics/OpenOCD）。\n- `NOASSERTION`：639 个文件，GitHub 未能解析 SPDX。\n- `UNRESOLVED`：25 个文件，即依赖闭包补充的文件，来源已知但未单独解析。',
          '- `GPL-2.0`：'
     f"{N_GPL2}"
     ' 个文件，来源明确。\n- `GPL-2.0-or-later`：'
     f"{N_GPL2L}"
     ' 个文件（含 `src/flash/nor/stldr_driver.c`，来自 STMicroelectronics/OpenOCD）。\n- `NOASSERTION`：'
     f"{N_NOASSERT}"
     ' 个文件，GitHub 未能解析 SPDX。\n- `UNRESOLVED`：'
     f"{N_UNRESOLVED}"
     ' 个文件，即依赖闭包补充的文件，来源已知但未单独解析。\n\n四项合计 '
     f"{N_FILES}"
     '，与 `manifest/licenses.csv` 的行数一致。无许可证信息的（`NOASSERTION` +\n`UNRESOLVED`）一共 '
     f"{N_UNLICENSED}"
     ' 个，占 '
     f"{PCT_UNLICENSED}"
     '%。'),
    ('docs/02-usage.md',
     'bash tools/run_mine.sh            # 1. 扫描 688 个仓库',
          'bash tools/run_mine.sh            # 1. 扫描 '
     f"{N_REPOS_CSV}"
     ' 个仓库'),
    ('docs/02-usage.md',
     '| C 驱动未注册进构建 | 26（13 个 `.c` + 13 个 `.h`） | 见「C 驱动的接入状态」；卡点是它们依赖上游已删/已改名的 API。另有 `OpenULINK/src/` 4 个固件源文件，独立 Makefile，不参与主构建 |\n| 未深挖的仓库 | 488 个（688 − 200） | 全部做过 `tcl/target` 粗筛（688/688），但只深挖了 star 靠前的 200 个；提高 `DIFF_BUDGET` 可扩展 |\n| 无许可证信息 | 649 / 785（83%） | 商用前必须人工审计，见 [03-LICENSES.md](03-LICENSES.md) |\n| 烧录器只有配置没有驱动 | 6 个驱动名 / 8 处引用 | `aji_client`、`tas_client`、`aice`、`picoprobe`、`colobus`、`tamarin`；前 4 个上游也没有实现，后 2 个是 fork 单独加的配置。逐条见「悬空的接口配置」表 |\n| Synopsys 板级 | 4 个未导入 | 依赖厂商内部构建产物 |\n| ARC 配置只能按 ARCv2 访问 | 5 个 cfg | 原先写 `arc600`/`arc700`/`arc32` 的 `arc_axc001.cfg`、`arc_axc002.cfg`、`snps_axc001.cfg`、`snps_ml509_arc600.cfg`、`snps_ml509_arc700.cfg` 统一改成 `arcv2`；`arc32.c` 一族缺 `arc_mem.c` 无法接入，全树 22 个 ARC 配置现在都只用 `arcv2` |\n| 无真机验证 | 全部 | 静态校验之外，只用 CI 产物跑过 `adapter list`、`target types` 和批量 `source [find ...]`（验证配置能被解析、驱动/target type/flash 驱动都在）；没有接真实探针与目标板跑过调试会话 |\n| `-chain-position` 旧写法 | 408 个文件 / 504 处 | 上游 `tcl/` 已是 0 处（全部改用 `-dap` / `-tap`）；这 504 处全在导入的第三方配置里（`target create` 373 处、`dap create` 122 处、`vjtag create` 1 处，其余为变量拼接）。机械替换只能自动解出 70 处（对象名与取值同行且完全相同），其余 434 处需人工判断 TAP 名 |\n| `adi-usbmux` 开关为空 | 1 个 | 它是 Win32 命名管道 helper 而非 adapter driver；`_ADI_USB_MUX_` 从未定义，mux 代码被编译掉 |\n| 三组导入候选被上游阻塞 | 14 个文件 | ESP32 GPIO 探针（需 ESP-IDF HAL）、WCH RISC-V 探针（需整套 SDI transport 层）、AL-Link 探针（需 `JTAG_TDI` + `DEBUG_CAP_TDI_SEQ`，且后端仅 Windows） |\n| TI XDS100 包装配置缺失 | 9 份板级配置 | 这 9 份 `tcl/board/ti/*-xds100v2.cfg` / `-xds100v3.cfg` 都 `source [find interface/ti/xds100v2.cfg]` 或 `ti/xds100v3.cfg`，树里只有 `interface/ftdi/xds100v2.cfg`；补两个三行包装文件即可，无需 C 改动 |\n| 两个非 ASCII 文件名 | 2 个 | `tcl/target/1986ве1т.cfg`、`tcl/target/к1879xб1я.cfg` 是上游自己带的西里尔字母名（与 `upstream/master` 逐字节一致），不是本 fork 引入；Windows 上部分工具链会处理异常 |\n| `.stldr` 加载器二进制不在仓库 | 4 份配置 | ST 发布的专有 blob，需用户自备并放到 `loaders/stldr/`；驱动本身已接入 |\n| 扫描漏掉了子目录里的文件 | 已补扫，0 个待接入 | `/git/trees/<ref>:<subdir>` 对子目录**不递归**，`src/flash/nor/`、`src/target/rvmax/` 这类路径在粗扫里看不见。`tools/expand_subtrees.py` 已补上；补出来的文件经 API 漂移分析后确认与上游 `src/flash/nor/` 的 85 个驱动重合，本树实际只多 `rv32m1.c` 与 `stldr_driver.c`（均已接入），NOR 目录 87/87 全部在 `Makefile.am` 里 |',
          '| C 驱动未注册进构建 | '
     f"{N_UNWIRED}"
     '（'
     f"{N_UNWIRED_C}"
     ' 个 `.c` + '
     f"{N_UNWIRED_H}"
     ' 个 `.h`） | 见「C 驱动的接入状态」；卡点分两类：依赖上游已改名的 API，或（`jtag_tcp.c`、`jtag_esp_remote.c`、`cmsis_dap_wch.c`、`aarch64_coproc_reg.c` 与 `21ab67574` 新导入的 11 个文件）上游从未有过这些 API。另有 `OpenULINK/src/` '
     f"{N_OPENULINK}"
     ' 个固件源文件，独立 Makefile，不参与主构建 |\n| 未深挖的仓库 | '
     f"{N_REPOS_NOTDEEP}"
     ' 个（'
     f"{N_REPOS_CSV}"
     ' − '
     f"{N_DEEP}"
     '） | 全部做过 `tcl/target` 粗筛（'
     f"{N_REPOS_CSV}"
     '/'
     f"{N_REPOS_CSV}"
     '），但只深挖了 star 靠前的 '
     f"{N_DEEP}"
     ' 个；提高 `DIFF_BUDGET` 可扩展 |\n| 无许可证信息 | '
     f"{N_UNLICENSED}"
     ' / '
     f"{N_FILES}"
     '（'
     f"{PCT_UNLICENSED}"
     '%） | 商用前必须人工审计，见 [03-LICENSES.md](03-LICENSES.md) |\n| 烧录器只有配置没有驱动 | 0 个驱动名 / 0 处引用 | 旧版这里写「6 个驱动名 / 8 处引用」，指的是已经不在树里的 10 个配置文件（见「悬空引用扫描」）；当前树里 '
     f"{N_DANGLING}"
     ' 条 unresolved 引用全是注释或占位符 |\n| Synopsys 板级 | 4 个未导入 | 依赖厂商内部构建产物 |\n| ARC 配置只能按 ARCv2 访问 | 5 个 cfg | 原先写 `arc600`/`arc700`/`arc32` 的 `arc_axc001.cfg`、`arc_axc002.cfg`、`snps_axc001.cfg`、`snps_ml509_arc600.cfg`、`snps_ml509_arc700.cfg` 统一改成 `arcv2`；提供另外两个 target 的 `arc32` 家族缺 `arc_mem.c` 接不进来且已在 `7ffeda047` 删除，全树 22 个 ARC 配置现在都只用 `arcv2` |\n| `-chain-position` 旧写法 | '
     f"{N_CPOS_FILES}"
     ' 个文件 / '
     f"{N_CPOS_HITS}"
     ' 处 | 上游 `tcl/` 已是 0 处（全部改用 `-dap` / `-tap`）；这 '
     f"{N_CPOS_HITS}"
     ' 处全在导入的第三方配置里（`target create` '
     f"{N_CPOS_TC}"
     ' 处、`dap create` '
     f"{N_CPOS_DAP}"
     ' 处、`pld create` '
     f"{N_CPOS_PLD}"
     ' 处，其余为变量拼接）。机械替换只能自动解出 '
     f"{N_CPOS_MECH}"
     ' 处（对象名与取值同行且完全相同），其余 '
     f"{N_CPOS_HUMAN}"
     ' 处需人工判断 TAP 名 |\n| `adi-usbmux` 开关为空 | 1 个 | 它是 Win32 命名管道 helper 而非 adapter driver；`_ADI_USB_MUX_` 从未定义，mux 代码被编译掉 |\n| 三组导入候选被上游阻塞 | '
     f"{N_BLOCKED}"
     ' 个文件（tcl）+ 树内 '
     f"{N_UNWIRED}"
     ' 个未接线 C 文件 | ESP32 GPIO 探针（需 ESP-IDF HAL）、WCH RISC-V 探针（需整套 SDI transport 层）、AL-Link 探针（需 `JTAG_TDI` + `DEBUG_CAP_TDI_SEQ`，且后端仅 Windows）；三组 C 代码都已在树里，只是没法注册。仍被上游挡住的导入候选只剩 '
     f"{N_BLOCKED}"
     ' 份 `tcl/target/anlogic/*_al_link.cfg` |\n| TI XDS100 包装配置缺失 | '
     f"{N_XDS100_BOARD}"
     ' 份板级配置 | 这 '
     f"{N_XDS100_BOARD}"
     ' 份 `tcl/board/ti/*-xds100v2.cfg` / `-xds100v3.cfg` 都 `source [find interface/ti/xds100v2.cfg]` 或 `ti/xds100v3.cfg`，树里只有 `interface/ftdi/xds100v2.cfg`；补两个三行包装文件即可，无需 C 改动 |\n| 两个非 ASCII 文件名 | 2 个 | `tcl/target/1986ве1т.cfg`、`tcl/target/к1879xб1я.cfg` 是上游自己带的西里尔字母名（与 `upstream/master` 逐字节一致），不是本 fork 引入；Windows 上部分工具链会处理异常 |\n| `.stldr` 加载器二进制不在仓库 | 4 份配置 | ST 发布的专有 blob，需用户自备并放到 `loaders/stldr/`；驱动本身已接入 |\n| 扫描漏掉了子目录里的文件 | 已补扫，0 个待接入 | `/git/trees/<ref>:<subdir>` 对子目录**不递归**，`src/flash/nor/`、`src/target/rvmax/` 这类路径在粗扫里看不见。`tools/expand_subtrees.py` 已补上；补出来的文件经 API 漂移分析后确认与上游 `src/flash/nor/` 的 85 个驱动重合，本树实际只多 `rv32m1.c` 与 `stldr_driver.c`（均已接入），NOR 目录 87/87 全部在 `Makefile.am` 里 |'),
    # The dangling-reference count is printed by tools/audit_dangling_refs.py and
    # quoted in three documents.  It was 5 all along; the first draft of these
    # lines said 4, which is exactly the drift this script exists to catch.
    ("CHANGELOG.md", "`.tcl` parsed, 1942 `source [find ...]` references resolved, 4 unresolved",
     f"`.tcl` parsed, 1942 `source [find ...]` references resolved, {N_DANGLING} unresolved"),
    ("docs/04-release.md", "`unresolved references: 4`（全部无害：3 条注释行、1 个上游占位符、1 条注释里多写了一级目录）",
     f"`unresolved references: {N_DANGLING}`（全部无害：3 条注释行、1 个上游占位符、1 条注释路径多写了一级目录）"),
    ("docs/02-usage.md", "当前树里 5 条 unresolved 引用全是注释或占位符",
     f"当前树里 {N_DANGLING} 条 unresolved 引用全是注释或占位符"),

]


def apply(fname, pairs):
    """Rewrite one document; never guess, never silently no-op."""
    p = ROOT / fname
    text = p.read_text(encoding="utf-8")
    changed = 0
    applied = []
    for old, new in pairs:
        if old == new:
            applied.append(new)
            continue
        # The target already being present wins: an insertion edit (new text
        # that quotes the old line as its own first line) would otherwise be
        # re-applied on every run and duplicate its own paragraph. Only a
        # pattern that matches neither side means real drift.
        if new in text:
            applied.append(new)
            continue
        if old in text:
            text = text.replace(old, new, 1)
            changed += 1
            applied.append(new)
            continue
        problem(f"{fname}: pattern not found and target absent: {old[:70]!r}")
        print(f"  !! {fname}: pattern not found: {old[:70]!r}")
    for target in applied:
        if target and target not in text:
            problem(f"{fname}: replacement target missing from the final text: {target[:70]!r}")
    if changed:
        PENDING.append((fname, changed))
        if not CHECK:
            p.write_text(text, encoding="utf-8", newline="\n")
    return changed


FILES = ("README.md", "README.zh-CN.md", "docs/00-findings.md",
         "docs/02-usage.md", "docs/04-release.md", "CHANGELOG.md")
total = 0
for fname in FILES:
    n = apply(fname, [(o, w) for (f, o, w) in EDITS if f == fname])
    total += n
    print(f"{fname}: {n} replacement(s)")

if CHECK and total:
    for fname, n in PENDING:
        print(f"  pending: {fname} ({n} replacement(s) would be applied)")
for msg in PROBLEMS:
    print(f"  !! {msg}")

if PROBLEMS:
    print("sync_doc_numbers: FAIL")
    sys.exit(1)
if CHECK and total:
    print(f"sync_doc_numbers: FAIL ({total} replacement(s) pending)")
    sys.exit(1)
print("sync_doc_numbers: OK (0 pending)")
sys.exit(0)

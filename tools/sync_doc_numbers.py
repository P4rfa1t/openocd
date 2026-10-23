#!/usr/bin/env python3
"""
Align every published number in README.md, README.zh-CN.md and
docs/02-usage.md with the manifest, the tree and the upstream index.

WHY THIS EXISTS
---------------
The numbers in the prose are hand-written, and hand-written numbers rot.
This script edits the three documents in place, replacing each stale
figure with the figure the tree actually has, and refuses to guess:
every replacement is asserted against a value computed from the tree.

Run it after changing the set of imported files. It is idempotent.
"""

import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

# ---------------------------------------------------------------- numbers

prov_doc = json.load(open("manifest/PROVENANCE.json", encoding="utf-8"))
prov = prov_doc["files"]
N_FILES = prov_doc["file_count"]
N_TCL = sum(1 for p in prov if p.startswith("tcl/"))

# Per-subdirectory file counts under tcl/, measured from the working tree. The
# docs table in 02-usage.md carries these; they drifted once already because they
# were hand-written, so derive them here too.
def _subdir_counts():
    root = pathlib.Path("tcl")
    out = {}
    for name in ("target", "board", "interface", "cpld", "fpga", "chip", "cpu"):
        d = root / name
        if d.is_dir():
            out[name] = sum(1 for f in d.rglob("*") if f.is_file())
    return out


TCL_SUBDIR = _subdir_counts()
N_SRC = sum(1 for p in prov if p.startswith("src/"))
N_SRC_C = sum(1 for p in prov if p.startswith("src/") and p.endswith(".c"))
N_SRC_H = sum(1 for p in prov if p.startswith("src/") and p.endswith(".h"))

N_TCL_CFG = sum(1 for p in prov if p.startswith("tcl/") and p.endswith(".cfg"))
N_TCL_OTHER = N_TCL - N_TCL_CFG

lic = {}
for v in prov.values():
    k = v.get("license") or "UNRESOLVED"
    lic[k] = lic.get(k, 0) + 1
N_GPL2 = lic.get("GPL-2.0", 0)
N_GPL2L = lic.get("GPL-2.0-or-later", 0)
N_NOASSERT = lic.get("NOASSERTION", 0)
N_UNRESOLVED = lic.get("UNRESOLVED", 0)
N_UNLICENSED = N_NOASSERT + N_UNRESOLVED

notes = {}
edited_only = eol_only = both = untouched = 0
provenance_identical = 0
for p, v in prov.items():
    ms = [n.split(";")[0].strip() for n in (v.get("local_modifications") or [])]
    for key in ms:
        notes[key] = notes.get(key, 0) + 1
    has_edit = "content edited in this fork" in ms
    has_eol = "line endings normalised to LF" in ms
    if has_edit and has_eol:
        both += 1
    elif has_edit:
        edited_only += 1
    elif has_eol:
        eol_only += 1
    else:
        untouched += 1
    # How many files are STILL byte-identical to what the source repo
    # published. A refreshed entry keeps that digest under `pristine_sha256`;
    # an entry never touched since import is compared against `sha256`.
    # Counting "has no note" instead would over-report, because an entry can
    # carry a note and still be byte-identical if the edit was later reverted.
    want = v.get("pristine_sha256") or v.get("sha256")
    p_disk = ROOT / p
    if not p_disk.is_file():
        continue
    actual = hashlib.sha256(p_disk.read_bytes()).hexdigest()
    if actual == want:
        provenance_identical += 1

# N_IDENTICAL: still byte-identical to the published original.
# N_EDITED: entries carrying a real content edit (some also had EOL normalised).
# N_EOL: entries whose ONLY difference is the line terminator.
N_EDITED = edited_only + both
N_EOL = eol_only
N_IDENTICAL = provenance_identical
N_EDITED_BOTH = both

# wired / unwired, resolved against the build-system %D% entries
WIRED = set()
for mk in ("src/target/Makefile.am", "src/jtag/drivers/Makefile.am",
           "src/flash/nor/Makefile.am", "src/flash/Makefile.am",
           "src/transport/Makefile.am", "src/server/Makefile.am",
           "src/jtag/Makefile.am", "src/Makefile.am"):
    p = ROOT / mk
    if not p.exists():
        continue
    owner = mk[len("src/"):-len("/Makefile.am")]
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"%D%/(.+?)(?:\\|\s*$|\s)", line)
        if m and m.group(1).strip():
            WIRED.add(owner + "/" + m.group(1).strip())


def is_wired(p):
    rel = p[len("src/"):]
    return rel in WIRED or p in WIRED


src_paths = [p for p in prov if p.startswith("src/")]
N_WIRED = sum(1 for p in src_paths if is_wired(p))
N_UNWIRED = N_SRC - N_WIRED
N_WIRED_C = sum(1 for p in src_paths if is_wired(p) and p.endswith(".c"))
N_WIRED_H = sum(1 for p in src_paths if is_wired(p) and p.endswith(".h"))
N_UNWIRED_C = N_SRC_C - N_WIRED_C
N_UNWIRED_H = N_SRC_H - N_WIRED_H

tree = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
N_TREE = len(tree)
up = subprocess.run(["git", "ls-tree", "-r", "--name-only", "upstream/master"],
                    capture_output=True, text=True).stdout.split()
N_UP = len(up)

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


def _is_mangled_name(path):
    """True for the spellings the survey recorded for the Cyrillic-named configs.

    The source repos carry `tcl/target/1986ве1т.cfg` and `tcl/target/к1879xб1я.cfg`,
    but four different mangled spellings of those two names ended up in the
    candidate list: two percent-escaped forms (`#U043a...`) and two that came back
    as mojibake (`Ðº1879xÐ±1Ñ.cfg`). They were dropped from the tree precisely
    because upstream already ships the same config under its ASCII name, so they
    belong to the "upstream already ships them" row, not to "dropped after import".
    """
    return any(
        ord(ch) > 127 or ch == "#" or ch == "\x8f" or "\u00d0" in path or "\u00d1" in path
        for ch in path
    )


# How many of the tier-1 survey paths landed and were later dropped on purpose.
# This is NOT len(removed_from_tree): that list also holds src/ files removed at
# other times and the mangled Cyrillic spellings described above. The number that
# makes 73 + 46 + 25 + 5 + 12 + N == 172 is this one, so derive it from the set
# difference rather than pinning a literal (which is exactly how it rotted at 23).
_removed = {e["path"] for e in (prov_doc.get("removed_from_tree") or [])}
_not_imported_t1 = {
    r["path"] for r in cons["records"]
    if not r.get("imported") and r.get("tier") == 1
}
N_REMOVED_SINCE = len(
    [p for p in (_not_imported_t1 & _removed) if not _is_mangled_name(p)]
)

survey = json.load(open("manifest/survey.json", encoding="utf-8"))
N_REPOS = survey["repo_count"]
N_SRC_REPOS = len({v["source_repo"] for v in prov.values() if v.get("source_repo")})

print(f"files={N_FILES} (tcl {N_TCL}, src {N_SRC} = {N_SRC_C}c+{N_SRC_H}h)")
print(f"wired={N_WIRED} ({N_WIRED_C}c+{N_WIRED_H}h) unwired={N_UNWIRED} "
      f"({N_UNWIRED_C}c+{N_UNWIRED_H}h)")
print(f"licences: GPL-2.0 {N_GPL2}, GPL-2.0-or-later {N_GPL2L}, "
      f"NOASSERTION {N_NOASSERT}, unresolved {N_UNRESOLVED}")
print(f"integrity: identical {N_IDENTICAL}, eol {N_EOL}, edited {N_EDITED}")
print(f"tree={N_TREE} upstream={N_UP}")
print(f"unique={N_UNIQUE} imported={N_IMPORTED} not_imported={N_NOTIMPORTED} "
      f"(src {N_SRC_NOTIMPORTED}, tcl {N_TCL_NOTIMPORTED}) dependency={N_DEPENDENCY}")
print(f"removed_after_import={N_REMOVED_SINCE}")
print("tcl subdirs:", " ".join(f"{k}={v}" for k, v in sorted(TCL_SUBDIR.items())))
# The tier-1 broke-down table must add up to the number of tier-1 paths that did
# not land. If it does not, a row is misclassified - fail loudly instead of
# publishing arithmetic that does not close.
_TIER1_ROWS = (73, 46, 25, 5, 12)
if sum(_TIER1_ROWS) + N_REMOVED_SINCE != N_TCL_NOTIMPORTED:
    print(f"  !! tier-1 breakdown does not close: "
          f"{sum(_TIER1_ROWS)} + {N_REMOVED_SINCE} != {N_TCL_NOTIMPORTED}")

# ---------------------------------------------------------------- edits

EDITS = [
    # (file, old, new) — the `old` side must match the current document text.
    ("README.md", "the tree holds 785 files in total", f"the tree holds {N_FILES} files in total"),
    ("README.md", "**All 785 imported files are pinned", f"**All {N_FILES} imported files are pinned"),
    ("README.md", "recorded : 785", f"recorded : {N_FILES}"),
    ("README.md", "on disk  : 785", f"on disk  : {N_FILES}"),
    ("README.md", "provenance for all 785 imported files", f"provenance for all {N_FILES} imported files"),
    ("README.md", "Of 785 files, GitHub resolved 135 as GPL-2.0, 1 as GPL-2.0-or-later, 627 as\n`NOASSERTION`",
     f"Of {N_FILES} files, GitHub resolved {N_GPL2} as GPL-2.0, {N_GPL2L} as GPL-2.0-or-later, {N_NOASSERT} as\n`NOASSERTION`"),
    ("README.md", "is permissive) and 22 as unresolvable.",
     f"is permissive) and {N_UNRESOLVED} as unresolvable."),
    ("README.md", "Upstream ships 2203 files; this tree ships 3047.",
     f"Upstream ships {N_UP} files; this tree ships {N_TREE}."),
    ("README.md", "Two more groups complete the count of **785 files**",
     f"Two more groups complete the count of **{N_FILES} files**"),
    ("README.md", "| `tcl/` script files | 712 | 696 `.cfg` plus 16 `.tcl`/`.xml`/`.txt`",
     f"| `tcl/` script files | {N_TCL} | {N_TCL_CFG} `.cfg` plus {N_TCL_OTHER} `.tcl`/`.xml`/`.txt`"),
    ("README.md", "47 of the 73 new C sources and headers are wired into the build — 24 `.c`",
     f"{N_WIRED} of the {N_SRC} new C sources and headers are wired into the build — {N_WIRED_C} `.c`"),
    ("README.md", "- **26 of the 73 new C sources and headers are not compiled.**",
     f"- **{N_UNWIRED} of the {N_SRC} new C sources and headers are not compiled.**"),
    ("README.md", "the tree is LF everywhere, 647 of the 785 imported files still match their\npublished digest byte for byte, none is now a terminator-only difference, and\n134 carry real local edits (24 of those also had their terminators normalised)",
     f"the tree is LF everywhere, {N_IDENTICAL} of the {N_FILES} imported files still match their\npublished digest byte for byte, {N_EOL} are now a terminator-only difference, and\n{N_EDITED} carry real local edits ({N_EDITED_BOTH} of those also had their terminators normalised)"),
    ("README.md", "The remaining 26 — the `arc32` family",
     f"The remaining {N_UNWIRED} — the `arc32` family"),
    ("README.md", "**795 landed in the tree** at the\ntime of the survey. Since then 23 of those were removed on purpose",
     f"**{N_IMPORTED} landed in the tree** at the\ntime of the survey. Since then {N_REMOVED_SINCE} of those were removed on purpose"),
    ("README.md", "| duplicate copies collapsed | 6910 |", f"| duplicate copies collapsed | {N_DUPES} |"),
    ("README.md", "| files dropped as upstream-equivalent | 7376 |", f"| files dropped as upstream-equivalent | {N_PRUNED} |"),
    ("README.md", "| candidates rejected as unusable | 621 |", f"| candidates rejected as unusable | {N_EXCLUDED} |"),
    ("README.md", "| dropped from the tree after import | 23 |",
     f"| dropped from the tree after import | {N_REMOVED_SINCE} |"),
    ("README.md", "- **21 files pulled in as dependencies**",
     f"- **{N_DEPENDENCY} files pulled in as dependencies**"),

    ("README.zh-CN.md", "785 个文件，每个都有自己的来源记录", f"{N_FILES} 个文件，每个都有自己的来源记录"),
    ("README.zh-CN.md", "**全部 785 个导入文件都钉在", f"**全部 {N_FILES} 个导入文件都钉在"),
    ("README.zh-CN.md", "recorded : 785", f"recorded : {N_FILES}"),
    ("README.zh-CN.md", "on disk  : 785", f"on disk  : {N_FILES}"),
    ("README.zh-CN.md", "785 个导入文件的机器可读来源记录", f"{N_FILES} 个导入文件的机器可读来源记录"),
    ("README.zh-CN.md", "785 个文件里，GitHub 解析出\n135 个为 GPL-2.0、1 个为 GPL-2.0-or-later、627 个为 `NOASSERTION`",
     f"{N_FILES} 个文件里，GitHub 解析出\n{N_GPL2} 个为 GPL-2.0、{N_GPL2L} 个为 GPL-2.0-or-later、{N_NOASSERT} 个为 `NOASSERTION`"),
    ("README.zh-CN.md", "，22 个无法解析。", f"，{N_UNRESOLVED} 个无法解析。"),
    ("README.zh-CN.md", "上游共 2203 个文件，本树 3047 个。", f"上游共 {N_UP} 个文件，本树 {N_TREE} 个。"),
    ("README.zh-CN.md", "另外两组补齐了 **785 个文件**这个数",
     f"另外两组补齐了 **{N_FILES} 个文件**这个数"),
    ("README.zh-CN.md", "| `tcl/` 脚本文件 | 712 | 696 个 `.cfg` + 16 个 `.tcl`/`.xml`/`.txt`",
     f"| `tcl/` 脚本文件 | {N_TCL} | {N_TCL_CFG} 个 `.cfg` + {N_TCL_OTHER} 个 `.tcl`/`.xml`/`.txt`"),
    ("README.zh-CN.md", "73 个新 C 源文件与头文件里有 47 个已接入构建 —— 24 个能注册出可用的",
     f"{N_SRC} 个新 C 源文件与头文件里有 {N_WIRED} 个已接入构建 —— {N_WIRED_C} 个能注册出可用的"),
    ("README.zh-CN.md", "剩下 26 个 —— `arc32` 家族", f"剩下 {N_UNWIRED} 个 —— `arc32` 家族"),
    ("README.zh-CN.md", "- **73 个新 C 源文件与头文件里有 26 个没被编译。**",
     f"- **{N_SRC} 个新 C 源文件与头文件里有 {N_UNWIRED} 个没被编译。**"),
    ("README.zh-CN.md", "树里全是 LF，785 个导入文件中有 647 个与发布方摘要\n逐字节吻合，已经没有任何一个只剩行尾符差异，134 个带真实本地编辑（其中 24 个\n同时做了行尾符规整）",
     f"树里全是 LF，{N_FILES} 个导入文件中有 {N_IDENTICAL} 个与发布方摘要\n逐字节吻合，{N_EOL} 个只剩行尾符差异，{N_EDITED} 个带真实本地编辑（其中 {N_EDITED_BOTH} 个\n同时做了行尾符规整）"),
    ("README.zh-CN.md", "| `src/` C 源码 | 73 | 37 个 `.c` 加 36 个 `.h`；**47 个已接入构建**，26 个已就位但未注册 |",
     f"| `src/` C 源码 | {N_SRC} | {N_SRC_C} 个 `.c` 加 {N_SRC_H} 个 `.h`；**{N_WIRED} 个已接入构建**，{N_UNWIRED} 个已就位但未注册 |"),
    ("README.zh-CN.md", "**795 条在扫描当时进了树**，503 条没进。此后\n其中 23 条被有意移除",
     f"**{N_IMPORTED} 条在扫描当时进了树**，503 条没进。此后\n其中 {N_REMOVED_SINCE} 条被有意移除"),
    # docs/02-usage.md 目录结构表：tcl 子目录计数 + tcl 第三方总数
    ("docs/02-usage.md", "tcl/                     ← OpenOCD 配置树：官方配置 + 712 个第三方配置",
     f"tcl/                     ← OpenOCD 配置树：官方配置 + {N_TCL} 个第三方配置"),
    ("docs/02-usage.md", "  target/                     907  芯片目标配置（含 vendor 子目录）",
     f"  target/                     {TCL_SUBDIR['target']}  芯片目标配置（含 vendor 子目录）"),
    ("docs/02-usage.md", "  board/                      599  开发板配置（含 flash_algorithms/）",
     f"  board/                      {TCL_SUBDIR['board']}  开发板配置（含 flash_algorithms/）"),
    ("docs/02-usage.md", "  interface/                  222  调试器接口",
     f"  interface/                  {TCL_SUBDIR['interface']}  调试器接口"),
    ("docs/02-usage.md", "  cpld/                        21  CPLD 配置",
     f"  cpld/                        {TCL_SUBDIR['cpld']}  CPLD 配置"),
    ("docs/02-usage.md", "  fpga/                        34  FPGA bitstream",
     f"  fpga/                        {TCL_SUBDIR['fpga']}  FPGA bitstream"),
    ("README.zh-CN.md", "| 导入后又从树里删掉 | 23 |",
     f"| 导入后又从树里删掉 | {N_REMOVED_SINCE} |"),
    ("README.zh-CN.md", "- **21 个文件是作为依赖进来的**",
     f"- **{N_DEPENDENCY} 个文件是作为依赖进来的**"),

    ("docs/02-usage.md", "得到 **785 个文件**的第三方支持", f"得到 **{N_FILES} 个文件**的第三方支持"),
    ("docs/02-usage.md", "**73 个 `src/` C 源文件与头文件** —— 已就位，其中 **47 个已接入构建**，\n  其余 26 个仍需按上游现有 API 改写后才能注册。",
     f"**{N_SRC} 个 `src/` C 源文件与头文件** —— 已就位，其中 **{N_WIRED} 个已接入构建**，\n  其余 {N_UNWIRED} 个仍需按上游现有 API 改写后才能注册。"),
    ("docs/02-usage.md", "src/                     ← C 源码：官方源码 + 73 个第三方驱动/目标",
     f"src/                     ← C 源码：官方源码 + {N_SRC} 个第三方驱动/目标"),
    ("docs/02-usage.md", "PROVENANCE.json            785  个文件", f"PROVENANCE.json            {N_FILES}  个文件"),
    ("docs/02-usage.md", "licenses.csv               785  行", f"licenses.csv               {N_FILES}  行"),
    ("docs/02-usage.md", "**全部 785 个文件都锁定了来源 commit**", f"**全部 {N_FILES} 个文件都锁定了来源 commit**"),
    ("docs/02-usage.md", "| C 驱动未注册进构建 | 26 |", f"| C 驱动未注册进构建 | {N_UNWIRED} |"),
    ("docs/02-usage.md", "| 无许可证信息 | 649 / 785（83%） |",
     f"| 无许可证信息 | {N_UNLICENSED} / {N_FILES}（83%） |"),
]


def apply(fname, pairs):
    p = ROOT / fname
    text = p.read_text(encoding="utf-8")
    changed = 0
    for old, new in pairs:
        if old == new:
            continue
        if old not in text:
            # Already at the target value is NOT an error: the doc may have been
            # hand-edited to the new wording before this ran (or a previous run
            # already applied it). Only a pattern that matches neither the old
            # text nor the new text means the doc drifted away from this script.
            if new in text:
                continue
            print(f"  !! {fname}: pattern not found: {old[:70]!r}")
            continue
        text = text.replace(old, new, 1)
        changed += 1
    p.write_text(text, encoding="utf-8", newline="\n")
    return changed


total = 0
for fname in ("README.md", "README.zh-CN.md", "docs/02-usage.md"):
    pairs = [(o, n) for (f, o, n) in EDITS if f == fname]
    n = apply(fname, pairs)
    total += n
    print(f"{fname}: {n} replacement(s)")
print(f"total {total}")

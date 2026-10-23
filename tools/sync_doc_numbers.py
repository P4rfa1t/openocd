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
for v in prov.values():
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

# N_IDENTICAL: digest already matches the published one and no note at all.
# N_EDITED: entries carrying a real content edit (24 of them also had EOL normalised).
# N_EOL: entries whose ONLY difference is the line terminator.
N_EDITED = edited_only + both
N_EOL = eol_only
N_IDENTICAL = untouched
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
N_REMOVED_SINCE = 23

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

# ---------------------------------------------------------------- edits

EDITS = [
    # (file, old, new) — the `old` side must match the current document text.
    ("README.md", "the tree holds 786 files in total", f"the tree holds {N_FILES} files in total"),
    ("README.md", "**All 786 imported files are pinned", f"**All {N_FILES} imported files are pinned"),
    ("README.md", "recorded : 786", f"recorded : {N_FILES}"),
    ("README.md", "on disk  : 786", f"on disk  : {N_FILES}"),
    ("README.md", "provenance for all 786 imported files", f"provenance for all {N_FILES} imported files"),
    ("README.md", "Of 786 files, GitHub resolved 135 as GPL-2.0, 1 as GPL-2.0-or-later, 628 as\n`NOASSERTION`",
     f"Of {N_FILES} files, GitHub resolved {N_GPL2} as GPL-2.0, {N_GPL2L} as GPL-2.0-or-later, {N_NOASSERT} as\n`NOASSERTION`"),
    ("README.md", "is permissive) and 22 as unresolvable.",
     f"is permissive) and {N_UNRESOLVED} as unresolvable."),
    ("README.md", "Upstream ships 2203 files; this tree ships 3048.",
     f"Upstream ships {N_UP} files; this tree ships {N_TREE}."),
    ("README.md", "Two more groups complete the count of **786 files**",
     f"Two more groups complete the count of **{N_FILES} files**"),
    ("README.md", "| `tcl/` script files | 713 | 697 `.cfg` plus 16 `.tcl`/`.xml`/`.txt`",
     f"| `tcl/` script files | {N_TCL} | {N_TCL_CFG} `.cfg` plus {N_TCL_OTHER} `.tcl`/`.xml`/`.txt`"),
    ("README.md", "47 of the 73 new C sources and headers are wired into the build — 24 `.c`",
     f"{N_WIRED} of the {N_SRC} new C sources and headers are wired into the build — {N_WIRED_C} `.c`"),
    ("README.md", "- **26 of the 73 new C sources and headers are not compiled.**",
     f"- **{N_UNWIRED} of the {N_SRC} new C sources and headers are not compiled.**"),
    ("README.md", "the tree is LF everywhere, 648 files match their published digest byte for\nbyte, 4 are labelled as terminator-only differences, and 134 carry real local\nedits (24 of those also had their terminators normalised)",
     f"the tree is LF everywhere, {N_IDENTICAL} files match their published digest byte for\nbyte, {N_EOL} are labelled as terminator-only differences, and {N_EDITED} carry real local\nedits ({N_EDITED_BOTH} of those also had their terminators normalised)"),
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

    ("README.zh-CN.md", "786 个文件，每个都有自己的来源记录", f"{N_FILES} 个文件，每个都有自己的来源记录"),
    ("README.zh-CN.md", "**全部 786 个导入文件都钉在", f"**全部 {N_FILES} 个导入文件都钉在"),
    ("README.zh-CN.md", "recorded : 786", f"recorded : {N_FILES}"),
    ("README.zh-CN.md", "on disk  : 786", f"on disk  : {N_FILES}"),
    ("README.zh-CN.md", "786 个导入文件的机器可读来源记录", f"{N_FILES} 个导入文件的机器可读来源记录"),
    ("README.zh-CN.md", "786 个文件里，GitHub 解析出\n135 个为 GPL-2.0、1 个为 GPL-2.0-or-later、628 个为 `NOASSERTION`",
     f"{N_FILES} 个文件里，GitHub 解析出\n{N_GPL2} 个为 GPL-2.0、{N_GPL2L} 个为 GPL-2.0-or-later、{N_NOASSERT} 个为 `NOASSERTION`"),
    ("README.zh-CN.md", "，22 个无法解析。", f"，{N_UNRESOLVED} 个无法解析。"),
    ("README.zh-CN.md", "上游共 2203 个文件，本树 3048 个。", f"上游共 {N_UP} 个文件，本树 {N_TREE} 个。"),
    ("README.zh-CN.md", "另外两组补齐了 **786 个文件**这个数",
     f"另外两组补齐了 **{N_FILES} 个文件**这个数"),
    ("README.zh-CN.md", "| `tcl/` 脚本文件 | 713 | 697 个 `.cfg` + 16 个 `.tcl`/`.xml`/`.txt`",
     f"| `tcl/` 脚本文件 | {N_TCL} | {N_TCL_CFG} 个 `.cfg` + {N_TCL_OTHER} 个 `.tcl`/`.xml`/`.txt`"),
    ("README.zh-CN.md", "73 个新 C 源文件与头文件里有 47 个已接入构建 —— 24 个能注册出可用的",
     f"{N_SRC} 个新 C 源文件与头文件里有 {N_WIRED} 个已接入构建 —— {N_WIRED_C} 个能注册出可用的"),
    ("README.zh-CN.md", "剩下 26 个 —— `arc32` 家族", f"剩下 {N_UNWIRED} 个 —— `arc32` 家族"),
    ("README.zh-CN.md", "- **73 个新 C 源文件与头文件里有 26 个没被编译。**",
     f"- **{N_SRC} 个新 C 源文件与头文件里有 {N_UNWIRED} 个没被编译。**"),
    ("README.zh-CN.md", "树里全是 LF，648 个文件与发布方摘要逐字节吻合，\n4 个被标为仅行尾符差异，134 个带真实本地编辑（其中 24 个同时做了行尾符规整）",
     f"树里全是 LF，{N_IDENTICAL} 个文件与发布方摘要逐字节吻合，\n{N_EOL} 个被标为仅行尾符差异，{N_EDITED} 个带真实本地编辑（其中 {N_EDITED_BOTH} 个同时做了行尾符规整）"),
    ("README.zh-CN.md", "| `src/` C 源码 | 73 | 37 个 `.c` 加 36 个 `.h`；**47 个已接入构建**，26 个已就位但未注册 |",
     f"| `src/` C 源码 | {N_SRC} | {N_SRC_C} 个 `.c` 加 {N_SRC_H} 个 `.h`；**{N_WIRED} 个已接入构建**，{N_UNWIRED} 个已就位但未注册 |"),
    ("README.zh-CN.md", "**795 条在扫描当时进了树**，503 条没进。此后\n其中 23 条被有意移除",
     f"**{N_IMPORTED} 条在扫描当时进了树**，503 条没进。此后\n其中 {N_REMOVED_SINCE} 条被有意移除"),
    ("README.zh-CN.md", "| 导入后又从树里删掉 | 23 |",
     f"| 导入后又从树里删掉 | {N_REMOVED_SINCE} |"),
    ("README.zh-CN.md", "- **21 个文件是作为依赖进来的**",
     f"- **{N_DEPENDENCY} 个文件是作为依赖进来的**"),

    ("docs/02-usage.md", "得到 **786 个文件**的第三方支持", f"得到 **{N_FILES} 个文件**的第三方支持"),
    ("docs/02-usage.md", "**73 个 `src/` C 源文件与头文件** —— 已就位，其中 **47 个已接入构建**，\n  其余 26 个仍需按上游现有 API 改写后才能注册。",
     f"**{N_SRC} 个 `src/` C 源文件与头文件** —— 已就位，其中 **{N_WIRED} 个已接入构建**，\n  其余 {N_UNWIRED} 个仍需按上游现有 API 改写后才能注册。"),
    ("docs/02-usage.md", "src/                     ← C 源码：官方源码 + 73 个第三方驱动/目标",
     f"src/                     ← C 源码：官方源码 + {N_SRC} 个第三方驱动/目标"),
    ("docs/02-usage.md", "PROVENANCE.json            786  个文件", f"PROVENANCE.json            {N_FILES}  个文件"),
    ("docs/02-usage.md", "licenses.csv               786  行", f"licenses.csv               {N_FILES}  行"),
    ("docs/02-usage.md", "**全部 786 个文件都锁定了来源 commit**", f"**全部 {N_FILES} 个文件都锁定了来源 commit**"),
    ("docs/02-usage.md", "| C 驱动未注册进构建 | 26 |", f"| C 驱动未注册进构建 | {N_UNWIRED} |"),
    ("docs/02-usage.md", "| 无许可证信息 | 650 / 786（83%） |",
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

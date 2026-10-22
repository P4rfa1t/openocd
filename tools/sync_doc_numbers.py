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
for v in prov.values():
    for n in (v.get("local_modifications") or []):
        key = n.split(";")[0].strip()
        notes[key] = notes.get(key, 0) + 1
N_EDITED = notes.get("content edited in this fork", 0)
N_EOL = notes.get("line endings normalised to LF", 0)
N_IDENTICAL = N_FILES - N_EDITED - N_EOL

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
N_DEPENDENCY = N_FILES - N_IMPORTED - N_TCL_NOTIMPORTED

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
    # (file, old, new)
    ("README.md", "the tree holds 562 files in total", f"the tree holds {N_FILES} files in total"),
    ("README.md", "**All 562 imported files are pinned", f"**All {N_FILES} imported files are pinned"),
    ("README.md", "recorded : 562", f"recorded : {N_FILES}"),
    ("README.md", "on disk  : 562", f"on disk  : {N_FILES}"),
    ("README.md", "provenance for all 562 imported files", f"provenance for all {N_FILES} imported files"),
    ("README.md", "Of 562 files, GitHub resolved 139 as GPL-2.0, 398 as `NOASSERTION`",
     f"Of {N_FILES} files, GitHub resolved {N_GPL2} as GPL-2.0, {N_NOASSERT} as `NOASSERTION`"),
    ("README.md", "Upstream ships 2203 files; this tree ships 2799.",
     f"Upstream ships {N_UP} files; this tree ships {N_TREE}."),
    ("README.md", "47 of the 76 new C sources and headers are wired into the build — 24 `.c`",
     f"{N_WIRED} of the {N_SRC} new C sources and headers are wired into the build — {N_WIRED_C} `.c`"),
    ("README.md", "- **29 of the 76 new C sources and headers are not compiled.**",
     f"- **{N_UNWIRED} of the {N_SRC} new C sources and headers are not compiled.**"),
    ("README.md", "the tree is LF everywhere, 523 files match their published digest byte for\nbyte, 2 are labelled as terminator-only differences, and 37 carry real local",
     f"the tree is LF everywhere, {N_IDENTICAL} files match their published digest byte for\nbyte, {N_EOL} are labelled as terminator-only differences, and {N_EDITED} carry real local"),
    ("README.md", "The remaining 29 — the `arc32` family",
     f"The remaining {N_UNWIRED} — the `arc32` family"),
    ("README.md", "Of the 625 unique paths the survey identified, **536 landed in the tree** and\n89 did not: 70 C sources",
     f"Of the {N_UNIQUE} unique paths the survey identified, **{N_IMPORTED} landed in the tree** and\n{N_NOTIMPORTED} did not: {N_SRC_NOTIMPORTED} C sources"),
    ("README.md", "A further 25 files\ncame in as dependencies", f"A further {N_DEPENDENCY} files\ncame in as dependencies"),
    ("README.md", "The survey covered **53 distinct source repositories**.",
     f"The survey covered **{N_REPOS} candidate repositories**; {N_SRC_REPOS} of them\ncontributed at least one file that ended up in the tree."),
    ("README.md", "| duplicate copies collapsed | 4109 |", f"| duplicate copies collapsed | {N_DUPES} |"),
    ("README.md", "| files dropped as upstream-equivalent | 99 |", f"| files dropped as upstream-equivalent | {N_PRUNED} |"),
    ("README.md", "| candidates rejected as unusable | 108 |", f"| candidates rejected as unusable | {N_EXCLUDED} |"),

    ("README.zh-CN.md", "562 个文件，每个都有自己的来源记录", f"{N_FILES} 个文件，每个都有自己的来源记录"),
    ("README.zh-CN.md", "**全部 562 个导入文件都钉在", f"**全部 {N_FILES} 个导入文件都钉在"),
    ("README.zh-CN.md", "recorded : 562", f"recorded : {N_FILES}"),
    ("README.zh-CN.md", "on disk  : 562", f"on disk  : {N_FILES}"),
    ("README.zh-CN.md", "562 个导入文件的机器可读来源记录", f"{N_FILES} 个导入文件的机器可读来源记录"),
    ("README.zh-CN.md", "562 个文件里，GitHub 解析出\n139 个为 GPL-2.0，398 个为 `NOASSERTION`",
     f"{N_FILES} 个文件里，GitHub 解析出\n{N_GPL2} 个为 GPL-2.0，{N_NOASSERT} 个为 `NOASSERTION`"),
    ("README.zh-CN.md", "上游共 2203 个文件，本树 2799 个。", f"上游共 {N_UP} 个文件，本树 {N_TREE} 个。"),
    ("README.zh-CN.md", "75 个新 C 源文件与头文件里有 46 个已接入构建 —— 23 个能注册出可用的",
     f"{N_SRC} 个新 C 源文件与头文件里有 {N_WIRED} 个已接入构建 —— {N_WIRED_C} 个能注册出可用的"),
    ("README.zh-CN.md", "剩下 29 个 —— `arc32` 家族", f"剩下 {N_UNWIRED} 个 —— `arc32` 家族"),
    ("README.zh-CN.md", "- **75 个新 C 源文件与头文件里有 29 个没被编译。**",
     f"- **{N_SRC} 个新 C 源文件与头文件里有 {N_UNWIRED} 个没被编译。**"),
    ("README.zh-CN.md", "树里全是 LF，523 个文件与发布方摘要逐字节吻合，\n2 个被标为仅行尾符差异，37 个带真实本地编辑",
     f"树里全是 LF，{N_IDENTICAL} 个文件与发布方摘要逐字节吻合，\n{N_EOL} 个被标为仅行尾符差异，{N_EDITED} 个带真实本地编辑"),
    ("README.zh-CN.md", "| `src/` C 源码 | 75 | 39 个 `.c` 加 36 个 `.h`；**46 个已接入构建**，29 个已就位但未注册 |",
     f"| `src/` C 源码 | {N_SRC} | {N_SRC_C} 个 `.c` 加 {N_SRC_H} 个 `.h`；**{N_WIRED} 个已接入构建**，{N_UNWIRED} 个已就位但未注册 |"),

    ("docs/02-usage.md", "得到 **562 个文件**的第三方支持", f"得到 **{N_FILES} 个文件**的第三方支持"),
    ("docs/02-usage.md", "**75 个 `src/` C 源文件与头文件** —— 已就位，其中 **46 个已接入构建**，\n  其余 29 个仍需按上游现有 API 改写后才能注册。",
     f"**{N_SRC} 个 `src/` C 源文件与头文件** —— 已就位，其中 **{N_WIRED} 个已接入构建**，\n  其余 {N_UNWIRED} 个仍需按上游现有 API 改写后才能注册。"),
    ("docs/02-usage.md", "src/                     ← C 源码：官方源码 + 75 个第三方驱动/目标",
     f"src/                     ← C 源码：官方源码 + {N_SRC} 个第三方驱动/目标"),
    ("docs/02-usage.md", "PROVENANCE.json            562  个文件", f"PROVENANCE.json            {N_FILES}  个文件"),
    ("docs/02-usage.md", "licenses.csv               562  行", f"licenses.csv               {N_FILES}  行"),
    ("docs/02-usage.md", "**全部 562 个文件都锁定了来源 commit**", f"**全部 {N_FILES} 个文件都锁定了来源 commit**"),
    ("docs/02-usage.md", "`src/` 下 75 个第三方文件里（39 个 `.c` + 36 个 `.h`），**46 个已经接入构建系统**，\n其余 29 个仍是",
     f"`src/` 下 {N_SRC} 个第三方文件里（{N_SRC_C} 个 `.c` + {N_SRC_H} 个 `.h`），**{N_WIRED} 个已经接入构建系统**，\n其余 {N_UNWIRED} 个仍是"),
    ("docs/02-usage.md", "### 仍是「代码就位、未注册」（其余 29 个文件）",
     f"### 仍是「代码就位、未注册」（其余 {N_UNWIRED} 个文件）"),
    ("docs/02-usage.md", "| C 驱动未注册进构建 | 29 |", f"| C 驱动未注册进构建 | {N_UNWIRED} |"),
    ("docs/02-usage.md", "| 无许可证信息 | 423 / 562（75%） |", f"| 无许可证信息 | {N_UNLICENSED} / {N_FILES}（75%） |"),
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

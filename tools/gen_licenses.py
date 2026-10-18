#!/usr/bin/env python3
"""
Generate the third-party licence notice.

Every file in this repository came from someone else's OpenOCD fork, so the
repository as a whole is NOT one project with one licence. OpenOCD itself is
GPL-2.0-or-later, and almost every fork inherits that, but a minority ship
headers that say otherwise and some carry no SPDX at all.

`tools/verify_tree.py` reports "N files with unresolved SPDX" as a warning.
That warning is not actionable until you can see WHICH files and from WHERE, so
this pass produces that table: repo -> licence -> file count -> file list.

The output is intended to be read by a human before any commercial use, and to
be regenerated whenever the imported set changes.
"""

import collections
import json
import os

OUT_MD = "docs/03-LICENSES.md"
OUT_CSV = "manifest/licenses.csv"


def load(prov_path):
    with open(prov_path, encoding="utf-8") as f:
        doc = json.load(f)
    return doc.get("files", {})


def main():
    sources = [
        ("tcl/ 配置（随树直接可用）", "manifest/tier1-PROVENANCE.json"),
        ("src/ C 源码（需在构建系统注册）", "manifest/tier2-PROVENANCE.json"),
    ]

    sections = []
    rows = []
    total_by_lic = collections.Counter()

    for title, path in sources:
        files = load(path)
        by_repo = collections.defaultdict(
            lambda: {"lic": collections.Counter(), "files": []})
        for rel, meta in files.items():
            # NOASSERTION and "other" are as unusable as a blank: GitHub
            # reported a value but it tells you nothing about the terms.
            lic = (meta.get("license") or "UNRESOLVED").strip()
            if lic in ("NOASSERTION", "other"):
                lic = "NOASSERTION"
            repo = meta.get("source_repo") or "?"
            by_repo[repo]["lic"][lic] += 1
            by_repo[repo]["files"].append((rel, lic, meta.get("source_commit", "")))
            total_by_lic[lic] += 1
            rows.append({
                "tier": title, "repo": repo, "licence": lic,
                "path": rel, "commit": meta.get("source_commit", ""),
                "branch": meta.get("source_branch", ""),
            })

        lines = [f"## {title}\n",
                 f"文件数：**{len(files)}**\n",
                 "| 来源仓库 | SPDX | 文件数 |", "|---|---|---:|"]
        order = sorted(by_repo.items(),
                       key=lambda kv: -sum(kv[1]["lic"].values()))
        for repo, info in order:
            lic_str = ", ".join(f"{k}({v})" for k, v in info["lic"].most_common())
            lines.append(f"| [`{repo}`](https://github.com/{repo}) | {lic_str} | "
                         f"{sum(info['lic'].values())} |")
        lines.append("")

        unresolved = [(r, f) for r, info in by_repo.items()
                      for f in info["files"]
                      if f[1] in ("UNRESOLVED", "NOASSERTION", "other")]
        if unresolved:
            lines.append(f"### ⚠️ 需人工审计（{len(unresolved)} 个文件无许可证信息）\n")
            lines.append("这些文件的来源仓库在 GitHub 上未解析出许可证，"
                         "商用前必须逐个查看文件头部的版权声明。\n")
            for repo in sorted({r for r, _ in unresolved}):
                names = sorted(f[0] for r, f in unresolved if r == repo)
                lines.append(f"<details><summary><code>{repo}</code> "
                             f"({len(names)} 个)</summary>\n")
                for n in names:
                    lines.append(f"- `{n}`")
                lines.append("\n</details>\n")
        sections.append("\n".join(lines))

    head = [
        "# 第三方许可证清单\n",
        "> 由 `tools/gen_licenses.py` 生成。**本仓库汇集了他人的 OpenOCD fork，"
        "整体许可不统一**，任何商用前请先读这一页。\n",
        "## 总览\n",
        "| SPDX | 文件数 |", "|---|---:|",
    ]
    for lic, n in total_by_lic.most_common():
        head.append(f"| {lic} | {n} |")
    head.append("")
    # "UNRESOLVED" means nobody recorded a licence for the file. "NOASSERTION"
    # means GitHub looked at the repo and could not determine one. They are the
    # same practical problem, so they must be reported together - counting only
    # UNRESOLVED would have shown "4% unresolved" while 75% of files actually
    # carry no usable licence.
    unknown = sum(v for k, v in total_by_lic.items()
                  if k in ("UNRESOLVED", "NOASSERTION", "other"))
    total = max(1, sum(total_by_lic.values()))
    head.append(f"**{unknown} 个文件（{unknown / total:.0%}）没有可用的许可证信息**，"
                f"必须逐个审计文件头部的版权声明后才能商用。\n")
    head.append(
        "> 已知事实：OpenOCD 上游是 GPL-2.0-or-later，大多数 fork 继承该许可，"
        "所以实务上大概率都是 GPL。但 `NOASSERTION` 只表示「GitHub 没能解析出来」，"
        "**不等于宽松许可** —— 在少数 fork 里它对应的是专有许可。"
        f"逐文件清单见 `manifest/licenses.csv` 与下方折叠区。\n")

    # newline="" -- without it Python translates LF to os.linesep on
    # Windows, rewriting the whole generated doc as CRLF and producing a
    # full-file diff on every regeneration.
    with open(OUT_MD, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(head) + "\n" + "\n".join(sections))
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        import csv
        w = csv.DictWriter(f, fieldnames=["tier", "repo", "licence", "path",
                                           "branch", "commit"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["tier"], r["repo"], r["path"])))

    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_CSV} ({len(rows)} rows)")
    print("licence distribution:", dict(total_by_lic))


if __name__ == "__main__":
    main()
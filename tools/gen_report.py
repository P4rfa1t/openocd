#!/usr/bin/env python3
"""
Generate the consolidation report from the manifests.

Everything numeric in docs/ comes from here, so the report can never drift out
of sync with the data. Re-run after any change to manifest/*.json.
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict

SURVEY = "manifest/survey.json"
CONSOL = "manifest/consolidated.json"
REPOS_CSV = "manifest/repos.csv"
OUT_MD = "docs/01-inventory.md"

CHIP_FAMILIES = [
    ("WCH CH32V RISC-V", ("ch32", "wch-riscv", "wch_riscv")),
    ("Espressif ESP32", ("esp32", "esp_common", "xtensa-core-esp32")),
    ("Artery AT32", ("at32",)),
    ("Puya PY32", ("py32", "puya")),
    ("Nuvoton N76K", ("nu3", "nuvoton")),
    ("AndesTech NDS", ("nds32", "nds")),
    ("Infineon AURIX", ("tc3", "aurix")),
    ("Synopsys ARC", ("arc_", "arc-")),
    ("Analog Devices ADuC/ADSC", ("aduc", "adsc", "am13")),
    ("LicheeTang", ("licheetang",)),
    ("Nordic nRF", ("nrf",)),
    ("Raspberry Pi RP2040/2350", ("rp2040", "rp2350")),
    ("Kontron K1921VK", ("k1921",)),
    ("TI Stellaris/TMS/OMAP", ("stellaris", "tms570", "omap", "davinci")),
]


def load(p):
    if not os.path.exists(p):
        sys.exit(f"missing {p}; run the mining/consolidation pipeline first")
    return json.load(open(p, encoding="utf-8"))


def main():
    consol = load(CONSOL)
    survey = load(SURVEY)

    repos = {r["full_name"]: r for r in survey["repos"]}
    recs = consol["records"]
    t1 = [r for r in recs if r["tier"] == 1]
    t2 = [r for r in recs if r["tier"] == 2]

    contrib = defaultdict(lambda: {"t1": 0, "t2": 0})
    for r in recs:
        contrib[r["winner"]]["t1" if r["tier"] == 1 else "t2"] += 1

    lic = Counter((r.get("winner_license") or "unknown") for r in recs)
    behind = Counter()
    for r in recs:
        m = repos.get(r["winner"], {}).get("missing_core_count", 0)
        behind[r["winner"]] = m

    lines = []
    A = lines.append
    A("# OpenOCD 第三方支持 · 整合清单\n")
    A(f"> 由 `tools/gen_report.py` 自动生成，数据源 `manifest/*.json`，请勿手改。\n")
    A("## 1. 总览\n")
    A(f"| 指标 | 数值 |")
    A(f"|---|---|")
    A(f"| 扫描候选仓库 | {survey['repo_count']} |")
    A(f"| 完整深挖仓库 | {consol and len([r for r in repos.values() if r.get('deep_probed')])} |")
    A(f"| 去重后唯一新增路径 | {consol['unique_paths']} |")
    A(f"| 第一层：可直接覆盖的 TCL | {consol['tier1_drop_in_tcl']} |")
    A(f"| 第二层：需要改 C 源码 | {consol['tier2_needs_c_patch']} |")
    A(f"| 折叠掉的重复副本 | {consol['duplicates_collapsed']} |")
    A(f"| 判定为不可导入并排除 | {consol['excluded_from_import']['count']} |")
    A("")
    A("按目录分布：\n")
    A("| 目录 | 文件数 |")
    A("|---|---|")
    for k, v in sorted(consol["by_kind"].items(), key=lambda kv: -kv[1]):
        A(f"| `{k}` | {v} |")
    A("")

    A("## 2. 贡献来源（去重后独占胜出的文件数）\n")
    A("| 仓库 | 第一层 TCL | 第二层 C | 落后上游文件数 | SPDX |")
    A("|---|---:|---:|---:|---|")
    for repo, c in sorted(contrib.items(),
                          key=lambda kv: -(kv[1]["t1"] + kv[1]["t2"]))[:30]:
        info = repos.get(repo, {})
        A(f"| [`{repo}`](https://github.com/{repo}) | {c['t1']} | {c['t2']} | "
          f"{behind.get(repo, 0)} | {info.get('license') or '未声明'} |")
    A("")

    A("## 3. 芯片家族覆盖\n")
    A("| 家族 | overlay 文件数 | 主要来源 |")
    A("|---|---:|---|")
    for name, keys in CHIP_FAMILIES:
        hits = [r for r in t1
                if any(k in r["path"].lower() for k in keys)]
        if not hits:
            A(f"| {name} | 0 | — |")
            continue
        top = Counter(h["winner"] for h in hits).most_common(2)
        A(f"| {name} | {len(hits)} | "
          + ", ".join(f"`{r}`({n})" for r, n in top) + " |")
    A("")

    A("## 4. 许可证分布\n")
    A("| SPDX | 文件数 |")
    A("|---|---:|")
    for k, v in lic.most_common():
        A(f"| {k} | {v} |")
    A("")
    unresolved = sum(v for k, v in lic.items()
                      if k in ("unknown", "NOASSERTION", "other"))
    if unresolved:
        A(f"> ⚠️ **{unresolved} 个文件**来自 GitHub 未解析出 SPDX 的仓库，"
          f"导入前需人工审计头部许可声明。\n")

    A("## 5. 排除项说明\n")
    A(f"共排除 {consol['excluded_from_import']['count']} 个路径，原因：\n")
    A(consol["excluded_from_import"]["note"] + "\n")
    sample = consol["excluded_from_import"]["paths"][:12]
    if sample:
        A("示例：\n")
        for p in sample:
            A(f"- `{p}`")
        A("")

    A("## 6. 第二层（需要改 C）明细\n")
    # Group by the DIRECTORY, not by path[:3]. Slicing three segments turned
    # every src/target/<file>.c into its own "directory" row, so this section
    # degenerated into a per-file list instead of the per-subsystem summary it
    # is meant to be.
    bydir = defaultdict(list)
    for r in t2:
        parts = r["path"].split("/")
        d = "/".join(parts[:-1]) if len(parts) > 1 else parts[0]
        bydir[d].append(r)
    A("| 目录 | 文件数 | 主要来源 |")
    A("|---|---:|---|")
    for d, rs in sorted(bydir.items(), key=lambda kv: -len(kv[1])):
        top = Counter(x["winner"] for x in rs).most_common(2)
        A(f"| `{d}/` | {len(rs)} | "
          + ", ".join(f"`{r}`({n})" for r, n in top) + " |")
    A("")

    A("### 6.1 值得优先上游化的驱动\n")
    A("价值/工作量比最高的是**单文件 flash 驱动**，因为它们建立在成熟的通用内核"
      "之上，不需要动内核代码：\n")
    interesting = [
        r for r in t2
        if r["path"].startswith(("src/flash/nor/", "src/jtag/drivers/"))
        and r["path"].endswith(".c")
    ]
    A("| 文件 | 来源 | 落后上游 |")
    A("|---|---|---:|")
    for r in sorted(interesting, key=lambda x: x["path"])[:25]:
        A(f"| `{r['path']}` | `{r['winner']}` | "
          f"{repos.get(r['winner'], {}).get('missing_core_count', 0)} |")
    A("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD} ({len(lines)} lines)")
    print(f"  tier1={consol['tier1_drop_in_tcl']} tier2={consol['tier2_needs_c_patch']}")


if __name__ == "__main__":
    main()
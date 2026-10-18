# openocd-third-party-support

**`openocd-org/openocd` 的 fork** —— 把散落在 GitHub 各家 fork 里、从未上游化的
芯片 / 开发板 / 烧录器支持，直接合并进 OpenOCD 源码树。

上游文件原封不动躺在 `src/`、`tcl/`、`doc/`、`contrib/` 里；新增的第三方支持
落在**它们本该在的位置**：

```
tcl/target/xxx.cfg            ← 芯片目标配置
tcl/board/xxx.cfg             ← 开发板配置
tcl/interface/xxx.cfg         ← 调试器接口
src/jtag/drivers/xxx.c        ← 烧录器驱动
src/target/xxx.c              ← 新架构支持
```

没有外挂目录，没有搜索路径技巧，没有"先装官方、再叠一层"。更新时只需
`git fetch upstream && git merge upstream/master` —— 上游重命名 TCL、加驱动、
改构建脚本，冲突由 git 正常呈现，而不是被一份静默遮蔽的副本吞掉。

---

## 合并了什么

扫描 688 个 OpenOCD 相关仓库，跨仓去重、剔除与官方等价的副本后：

| 内容 | 数量 | 位置 | 状态 |
|---|---:|---|---|
| `tcl/` 配置 | 505 | 与官方同一目录 | **随构建生效**（上游 `Makefile.am` 用 `find` 通配安装，无需改构建脚本） |
| `src/` C 源码 | 127 | 与官方同一目录 | 已就位，**仍需在构建系统里注册**（见下文「未完成的部分」） |
| 折叠掉的重复副本 | 4109 | — | 去重后只保留一个胜出版本 |
| 与官方重复而剔除 | 99 | — | 上游已收编该支持 |

全部 **632 个文件都锁定了来源 commit**，可逐文件追溯到具体 fork 的具体提交：

```bash
python - <<'PY'
import json
f = json.load(open("manifest/PROVENANCE.json", encoding="utf-8"))["files"]
p = f["tcl/target/nucleo_l552ze.cfg"]
print(p["source_repo"], p["source_branch"], p["source_commit"], p["license"])
PY
```

## 构建

就是标准的 OpenOCD 构建，没有额外步骤：

```bash
git clone --recursive <this repo>
cd openocd
./bootstrap && ./configure && make -j
sudo make install
```

Windows 见上游 `README.Windows.md`（本仓库未改动）。

验证用的上游基线（commit + 全量文件清单）记录在
`manifest/upstream.json` 与 `manifest/upstream-index.txt`。

## 使用

编译安装后，所有新配置都在标准搜索路径下：

```bash
openocd -f interface/xxx.cfg -f target/xxx.cfg -f board/xxx.cfg
```

也可以直接从源码树运行未安装的版本：

```bash
./src/openocd -s tcl -f board/xxx.cfg
```

## 目录

```
tcl/            OpenOCD 配置树（官方 + 505 个第三方配置）
src/            C 源码（官方 + 127 个第三方驱动/目标）
doc/ testing/ contrib/ jimtcl/   上游原有内容，未改动

manifest/       合并过程的可审计产物（唯一事实来源）
  PROVENANCE.json            632 个文件的来源仓库/分支/commit/SHA-256/许可证
  tier1-PROVENANCE.json      └ tcl/ 部分（抓取器直接写出的中间产物）
  tier2-PROVENANCE.json      └ src/ 部分
  consolidated.json          去重决策：胜出者、被折叠的重复、上游重复项
  upstream.json              本 fork 所基于的上游 commit
  upstream-index.txt         该 commit 的全量文件清单，去重判定基准
  repos.csv / repos.json     688 个候选仓库排名
  survey.json                粗筛原始结果
  licenses.csv               逐文件许可证索引

docs/00-findings.md     调研结论 + 方法论修正记录（踩过的坑）
docs/01-inventory.md    清单报告（自动生成）
docs/02-usage.md        使用说明、构建、未完成的部分
docs/03-LICENSES.md     许可证清单（自动生成）

tools/              可复现的流水线，全部步骤幂等
```

> **480 vs 505**：`manifest/consolidated.json` 记录 480 个上游确实没有的独立支持项；
> 磁盘上有 505 个 `tcl` 文件，差额 25 个是为满足 `source [find ...]` 引用而补齐的依赖。
> 与官方重复的文件在 `consolidate.py` **写 manifest 时**就剔除了，所以重跑抓取器
> 不会把已剔除的副本再拉回来。

## 维护

### 跟上官方主线

```bash
git fetch upstream && git merge upstream/master
python tools/sync_upstream.py            # 官方新增/删除了什么、哪些支持已被上游收编
python tools/verify_tree.py              # 必须 VERIFY: PASS
```

`tools/sync_upstream.py` 纯离线，只用 git：

- 对比 `manifest/upstream-index.txt` 与当前上游，列出官方新增 / 删除的文件；
- 找出**本 fork 里有、而官方现在也提供的**文件 —— 这些是该删掉改用官方版本的支持，
  退出码非 0，CI 里可以直接当门禁；
- 找出官方对应路径被移动（改名）的导入文件，提醒复查。

清理命令：

```bash
python tools/prune_upstream_dups.py    # 路径相同 / 改名后相同
python tools/prune_shadow.py            # 同名但目录不同（如 am335x.cfg vs ti/am335x.cfg）
python tools/build_provenance.py        # 重新汇总 PROVENANCE.json
python tools/verify_tree.py             # 必须回到 errors: 0
```

> `prune_shadow.py` 必须独立存在：规范化比对会把 `am335x.cfg` 和
> `ti/am335x.cfg` 折叠成同一个键，而它们是两个不同的文件。早期漏掉这一类，
> 结果 16 个扁平副本长期遮蔽着官方版本。

### 吸收新的 fork

```bash
export GH_TOKEN=<token>          # 仅从环境变量读取，绝不写入任何文件
export PYTHONIOENCODING=utf-8    # 部分文件名含非 GBK 字符

bash tools/run_mine.sh            # 扫描全部候选仓库
python tools/refine_survey.py     # 过滤噪声
python tools/consolidate.py       # 跨仓去重 + 剔除官方已有
python tools/run_fetch.sh         # 抓取（tier1→tcl/，tier2→src/）
python tools/resolve_deps.py --apply    # 补齐 source 引用依赖，直到闭合
python tools/pin_commits.py              # 回填 commit pin
python tools/gen_report.py               # 清单报告
python tools/gen_licenses.py             # 许可证清单
python tools/build_provenance.py         # 汇总 PROVENANCE.json
python tools/verify_tree.py              # 完整性校验，必须 PASS
```

一键跑完整流水线（`--apply` 才写入，默认只报告）：

```bash
python tools/pipeline.py --apply
python tools/pipeline.py --apply --tier 2     # 连 src/ 一起
```

**增量性**：`consolidate.py` 按路径去重，抓取器默认不覆盖已有文件，
重复跑只会补上新增的部分。

### 提交前必须通过

```bash
python tools/verify_tree.py      # VERIFY: PASS，且 errors: 0
```

当前状态：

```
recorded 632 / on disk 632 / pinned 632 / errors 0
```

## 完整性保证

`tools/verify_tree.py`（纯离线，可当 CI 检查）：

- 每个 provenance 条目都有真实文件，**1:1 对账**
- 每个文件的 SHA-256 与记录一致（`.gitattributes` 已关闭 `tcl/`、`src/` 的
  EOL 转换，否则 Windows 上的 `core.autocrlf` 会让校验全灭）
- 没有「记录了但磁盘缺失」或「磁盘有但未记录」
- 没有与官方等价或同名遮蔽的重复副本
- 所有 `.cfg`/`.tcl` 的花括号与方括号在忽略注释和引号后平衡
- 许可证覆盖率统计

## 未完成的部分

| 项目 | 规模 | 说明 |
|---|---|---|
| C 驱动未注册进构建 | 127 | 文件已在 `src/` 的正确位置，但 `configure.ac` / `Makefile.am` / `drivers.c` / `target.c` 里还没有对应条目，需要逐个评估能否编译后再注册 |
| 无许可证信息 | 476 / 632（75%） | 商用前必须人工审计，见 [docs/03-LICENSES.md](docs/03-LICENSES.md) |
| 烧录器只有配置没有驱动 | 7 个 | `dbgagent`、`aji_client`、`tas_client`、`ddmi_usb`、`aice`、`mpdbgagent`、`ice2000` |
| Synopsys 板级不可用 | 4 个 | 依赖厂商内部构建产物 |
| 未深挖的仓库 | 488 / 688 | 全部做过粗筛，只深挖了 star 靠前的 200 个 |
| 无运行时验证 | 全部 | 校验全是静态的，未在真机上 `source` 过 |

## 安全

`GH_TOKEN` 只从环境变量读取，**绝不写入任何文件**。所有工具脚本在缺少该变量时
直接失败而不是降级成匿名限流运行。

## 许可

OpenOCD 上游是 GPL-2.0-or-later。**本仓库汇集了他人的 fork，整体许可并不统一**：
156 个文件明确标注 GPL-2.0，451 个来自 GitHub 无法解析 SPDX 的仓库，25 个
来源已知但未标注。逐文件清单见 [docs/03-LICENSES.md](docs/03-LICENSES.md)。
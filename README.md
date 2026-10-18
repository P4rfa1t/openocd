# OpenOCD 第三方支持整合层

把散落在 GitHub 各家 fork 里、从未上游化的 OpenOCD 芯片/板级/烧录器支持
收敛成**一个可增量维护的仓库**。

**它不是 OpenOCD 的 fork**，也不包含 OpenOCD 本身。它是一层**外挂**，
配合官方 `openocd-org/openocd` 使用。

---

## 为什么是「外挂」而不是「合并进源码」

上游根 `Makefile.am` 用**通配符**安装 TCL 文件：

```makefile
TCL_FILES = find $(srcdir)/tcl -name '*.cfg' -o -name '*.tcl' -o -name '*.txt'
```

没有硬编码文件清单，所以新增 `.cfg` **不需要改 `configure.ac`、不需要重新编译**。
任何"自动生成构建条目"的方案都是凭空制造复杂度。

于是分成两层：

| 层 | 内容 | 数量 | 怎么用 |
|---|---|---|---|
| **第一层 overlay** | 纯 TCL 配置 | 505 | `openocd -s overlay -f board/xxx.cfg`，**立即可用** |
| **第二层 worklist** | 新 C 驱动/新架构 | 127 | 需改源码并走上游 PR，**当前不可用** |

---

## 快速开始

```bash
# 只用官方 OpenOCD + 本仓库的额外支持
openocd -s /path/to/this-repo/overlay -f board/xxx.cfg
```

搜索路径里 overlay 在前，官方目录在后：官方文件始终可用，
overlay 只补官方没有的部分。

复制进安装目录（会先报告哪些文件会覆盖官方内容）：

```bash
python tools/install_overlay.py --kind windows            # 试运行
python tools/install_overlay.py --kind windows --apply    # 实际写入
```

> ⚠️ 用 `-s` 搜索路径模式时 **overlay 优先于官方**。
> 本仓库已剔除所有与官方等价或同名遮蔽的副本，但如果你手工往 overlay 里加文件，
> 它会遮蔽官方版本。参见 `docs/02-usage.md` 的「已知风险」一节。

---

## 目录

```
overlay/            第一层：505 个可直接使用的 TCL 文件
  tcl/target/       284  芯片目标配置
  tcl/board/        137  开发板配置（含 flash_algorithms/ 10 个）
  tcl/interface/     45  调试器接口
  tcl/cpld/          14  CPLD 配置
  ...               以及 FPGA bitstream、芯片/架构公共片段
  PROVENANCE.json   逐文件来源：仓库 / 分支 / commit / SHA-256 / 许可证

manifest/tier2/     第二层：127 个需要改 C 的文件（工作清单，非可直接使用）
manifest/           全部中间产物与去重决策，可审计

docs/00-findings.md     调研结论 + 方法论修正记录（踩过的坑）
docs/01-inventory.md    清单报告（自动生成）
docs/02-usage.md        使用说明与已知缺口
docs/03-LICENSES.md     许可证清单（自动生成）

tools/              可复现的流水线，全部步骤幂等
```

> **480** 是上游确实没有的独立支持项，来自 `manifest/consolidated.json`；
> **505** 是磁盘文件数（额外含 25 个为满足 `source` 引用而补齐的依赖）。
> `manifest/consolidated.json` 是**唯一的事实来源** —— 它对官方重复的剔除与
> `overlay/` 的内容严格一致，重跑 `fetch_overlay.py` 不会重新引入已剔除的副本。

---

## 维护：吸收新 fork / 跟上官方主线

### 1. 定期同步官方，重新生成清单

官方把 TCL 收进厂商子目录时会改文件名，所以**每次官方更新后都要重新核对**，
否则 overlay 里的旧副本会长期遮蔽官方修复。

```bash
export GH_TOKEN=<token>          # 仅从环境变量读取
export PYTHONIOENCODING=utf-8    # 部分文件名含非 GBK 字符

bash tools/run_mine.sh            # 扫描全部候选仓库
python tools/refine_survey.py     # 过滤噪声
python tools/consolidate.py       # 跨仓去重
bash tools/run_fetch.sh           # 抓取 + 自动校验
python tools/resolve_deps.py --apply        # 补齐 source 引用依赖
python tools/prune_upstream_duplicates.py   # 剔除与官方等价的重复
python tools/prune_shadow.py                # 剔除遮蔽官方的同名扁平文件
python tools/pin_commits.py                 # 回填 commit pin
python tools/gen_report.py                  # 清单报告
python tools/gen_licenses.py                # 许可证清单
python tools/verify_overlay.py              # 完整性校验，必须 PASS
```

官方重复由 `consolidate.py` **在写 manifest 时**剔除，所以 manifest 与 overlay
始终一致。早期版本在写完之后用 `prune_*.py` 事后剔除，导致两者数字对不上
（610 条记录 vs 505 个文件），任何人重跑 `fetch_overlay.py` 都会把已删的重复
重新拉回来。这两个脚本现在只作为**存量仓库的清理工具**保留。

**增量更新**：`consolidate.py` 按路径去重，`fetch_overlay.py` 默认不覆盖已有文件，
所以重复跑只会补上新增的部分。

### 2. 合并一个新的 fork

```bash
python tools/consolidate.py              # 重新计算唯一清单
python tools/fetch_overlay.py --tier 1   # 抓取缺失文件
python tools/verify_overlay.py           # 必须 PASS 才提交
```

如果新 fork 带来的是 C 代码，会自动落到 `manifest/tier2/`，
成为走 upstream PR 的候选。

### 3. 上游新增了某个支持 → 清理

`verify_overlay.py` 会把「与官方等价」的重复报为 **ERROR**。
出现这类错误说明官方已经收编了该支持，应当从 overlay 删除，改用官方版本。

### 4. 提交前必须通过

```bash
python tools/verify_overlay.py     # VERIFY: PASS，且 errors: 0
```

---

## 完整性保证

`tools/verify_overlay.py`（纯离线，可当 CI 检查）：

- 每个 provenance 条目都有真实文件，**1:1 对账**
- 每个文件的 SHA-256 与记录一致
- 没有「记录了但磁盘缺失」或「磁盘有但未记录」
- 没有与官方等价或同名遮蔽的重复副本
- 所有 `.cfg`/`.tcl` 的花括号与方括号在忽略注释和引号后平衡
- 许可证覆盖率统计

当前状态：

```
overlay    recorded 505 / on disk 505 / pinned 505 / errors 0
tier2      recorded 127 / on disk 127 / pinned 127 / errors 0
```

**全部 632 个文件都锁定了来源 commit**，可逐文件追溯到具体 fork 的具体提交。

---

## 已知缺口

| 缺口 | 规模 | 说明 |
|---|---|---|
| 未深挖的仓库 | 488 / 688 | 全部做过粗筛，只深挖了 star 靠前的 200 个 |
| 无许可证信息 | 476 / 632（75%） | 商用前必须人工审计，见 [docs/03-LICENSES.md](docs/03-LICENSES.md) |
| 烧录器只有配置没有驱动 | 7 个 | `dbgagent`、`aji_client`、`tas_client`、`ddmi_usb`、`aice`、`mpdbgagent`、`ice2000` |
| Synopsys 板级不可用 | 4 个 | 依赖厂商内部构建产物 |
| 无运行时验证 | 全部 | 校验全是静态的，未在真机上 `source` 过 |

---

## 安全

`GH_TOKEN` 只从环境变量读取，**绝不写入任何文件**。
所有工具脚本在缺少该变量时会直接失败而不是降级。
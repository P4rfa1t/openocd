# 整合结果与使用说明

## 一句话结论

扫描 GitHub 上 **688 个** OpenOCD 相关仓库（500 个官方 fork + 搜索命中的独立仓），
去重并剔除与官方重复的部分后，得到 **505 个文件**的第三方支持：

- **464 个上游确实没有的独立支持项** —— 零修改、零重编译即可配合官方 OpenOCD 使用；
- 另含 **41 个为满足 `source` 引用而补齐的依赖文件**；
- 另有 **127 个 C 源文件**必须改源码，已整理成走 upstream PR 的工作清单。

另有 **177 个与官方重复的文件已剔除**（详见「已处理的重复问题」）。

## 目录结构

```
overlay/                    ← 第一层：直接可用（505 个文件）
  tcl/target/                   284  芯片目标配置
  tcl/board/                    147  开发板配置（含 flash_algorithms/ 10 个）
  tcl/interface/                 47  调试器接口
  tcl/cpld/                      14  CPLD 配置
  tcl/fpga/                       2  FPGA bitstream
  tcl/chip/, tcl/cpu/             2  芯片/架构公共片段
  PROVENANCE.json               每个文件的来源仓库/分支/commit/SHA-256/许可证

manifest/tier2/             ← 第二层：需要改 C（127 个文件）
  src/target/                   92  新架构支持（ARC / WCH RISC-V / NDS32 ...）
  src/jtag/drivers/             33  新适配器与传输层
  src/server/                    2  remote_bitbang 服务端
  PROVENANCE.json

manifest/consolidated.json  逐文件来源与去重决策（可审计、可回溯）
manifest/repos.csv          688 个候选仓库的排名表
manifest/licenses.csv       632 行许可证索引（逐文件）
manifest/upstream-index.txt 官方上游全量文件清单（2199 个 blob），去重判定的基准
docs/01-inventory.md        自动生成的清单报告
docs/03-LICENSES.md         自动生成的许可证清单
tools/                      全部工具脚本
```

> **464** 是去重后上游确实没有的独立支持项；
> **505** 是磁盘文件数（额外含 41 个为满足 `source` 引用而补齐的依赖文件）。
> 另有 **177** 个与官方重复的文件已剔除 —— 上游把 TCL 收进厂商子目录时
> 同时改了文件名（如 `ti_cc13x0.cfg` → `tcl/target/ti/cc13x0.cfg`），
> 老 fork 的扁平副本若留在 overlay 里会**遮蔽官方文件**，因为搜索路径 overlay 在前。
>
> **全部 632 个文件都锁定了来源 commit**，可逐文件追溯到具体 fork 的具体提交。

> ⚠️ `manifest/consolidated.json` 里仍是**剔除前**的 582 条记录，
> 所以 `fetch_overlay.py --tier 1` 的提示数字（582）比磁盘上的 505 多。
> 差额就是那两个 prune 步骤删掉的重复副本。若要让 manifest 与磁盘一致，
> 需要把 prune 步骤接进 `consolidate.py`（见 README「可优化」一节）。

## 为什么这样分层

上游根 `Makefile.am` 用**通配符**安装 TCL 文件：

```makefile
TCL_FILES = find $(srcdir)/tcl -name '*.cfg' -o -name '*.tcl' -o -name '*.txt'
```

没有硬编码文件清单，所以新增 `.cfg` **不需要改 `configure.ac`、不需要重新编译**。
任何"自动生成构建条目"的方案都是凭空制造复杂度。

因此：

- **第一层（纯 TCL）**：把文件放进搜索路径即可生效。
- **第二层（C 代码）**：必须真正改源码并走上游 PR，无法用文件覆盖实现。

## 怎么用

### 方式 A：搜索路径（推荐，零侵入）

```bash
openocd -s "/c/Users/P4rfa1t/Documents/openocd/overlay" -f board/xxx.cfg
```

OpenOCD 会先在 overlay 里找 `target/`，找不到再回落到官方安装目录。
官方文件始终优先，overlay 只补缺。

### 方式 B：复制进安装目录

```bash
python tools/install_overlay.py --kind windows            # 试运行
python tools/install_overlay.py --kind windows --apply    # 实际写入
```

`copy` 模式会先报告哪些文件会覆盖上游已有内容，确认后再写。
`search-path` 模式只生成一个引导文件。

## 已知的 4 处悬空引用

以下引用在任何公开仓库里都不存在，属于厂商内部交付的 bring-up 目标：

| 缺失文件 | 被谁引用 |
|---|---|
| `target/snps_aml8626x.cfg` | `board/synopsys_amla3.cfg` |
| `target/snps_angel4.cfg` | `board/synopsys_angel4.cfg` |
| `target/snps_haps51.cfg` | `board/synopsys_haps51.cfg` |
| `target/snps_ml509.cfg` | `board/synopsys_ml509.cfg` |

这 4 个 Synopsys 板级配置在 `intel/OpenOCD` 里本身就没有配套 target，
需要 Synopsys 内部构建产物才能用。**除此之外全部引用闭合。**

## 许可证提醒

- `GPL-2.0`：125 个文件，来源明确。
- `NOASSERTION`：457 个文件，GitHub 未能解析 SPDX。
- `UNLICENSED`：100 个文件，即依赖闭包补充的文件，来源已知但未单独解析。

后两类在商用前需人工审计头部声明。逐文件来源见 `overlay/PROVENANCE.json`。

## 复现全流程

```bash
export GH_TOKEN=<你的 token>      # 仅从环境变量读取，绝不写入文件
export PYTHONIOENCODING=utf-8    # 部分文件名含非 GBK 字符

bash tools/run_mine.sh            # 1. 扫描 688 个仓库
python tools/refine_survey.py     # 2. 过滤噪声、排除自身仓库
python tools/consolidate.py       # 3. 跨仓去重、选定来源
bash tools/run_fetch.sh           # 4. 抓取文件 + 自动校验
python tools/resolve_deps.py --apply         # 5. 补齐引用依赖直到闭合
python tools/prune_upstream_duplicates.py    # 6. 剔除与官方等价的重复
python tools/prune_shadow.py                 # 7. 剔除遮蔽官方的同名扁平文件
python tools/pin_commits.py                  # 8. 回填 commit pin
python tools/gen_report.py                   # 9. 清单报告
python tools/gen_licenses.py                 # 10. 许可证清单
python tools/verify_overlay.py               # 11. 完整性校验，必须 PASS
```

每一步都可单独重跑；重复运行不会破坏已有结果。

## 已知缺口

| 缺口 | 规模 | 说明 |
|---|---|---|
| 未深挖的仓库 | 488 个（688 − 200） | 全部做过 `tcl/target` 粗筛（688/688），但只深挖了 star 靠前的 200 个；提高 `DIFF_BUDGET` 可扩展 |
| 无许可证信息 | 476 / 632（75%） | 商用前必须人工审计，见 [03-LICENSES.md](03-LICENSES.md) |
| 烧录器只有配置没有驱动 | 7 个 | `dbgagent`、`aji_client`、`tas_client`、`ddmi_usb`、`aice`、`mpdbgagent`、`ice2000` |
| Synopsys 板级 | 4 个不可用 | 依赖厂商内部构建产物 |
| 无运行时验证 | 全部 | 校验全是静态的，未在真机上 `source` 过 |

## 已处理的重复问题

历史上 overlay 曾混入两类与官方重复的文件，现已由工具自动剔除：

1. **与官方等价**（路径相同，或规范化后相同，如 `ti_cc13x0.cfg`
   ↔ `tcl/target/ti/cc13x0.cfg`）—— 共 161 个，
   由 `prune_upstream_duplicates.py` 剔除，`verify_overlay.py` 报为 ERROR。
2. **同名但目录不同**（如 `am335x.cfg` ↔ `tcl/target/ti/am335x.cfg`）—— 共 16 个。
   规范化比对会把两者折叠成同一个键，所以上一类检测不出来，
   由 `prune_shadow.py` 单独处理。

这两类若留在 overlay 里都会**遮蔽官方文件**，因为 `-s` 让 overlay 排在搜索路径前面，
结果是长期运行在几年前的旧配置上。
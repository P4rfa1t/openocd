# 整合结果与使用说明

## 一句话结论

本仓库是 `openocd-org/openocd` 的 fork。扫描 GitHub 上 **688 个** OpenOCD
相关仓库（500 个官方 fork + 搜索命中的独立仓），跨仓去重、剔除与官方等价的
副本后，得到 **632 个文件**的第三方支持，全部合并在**它们本该在的位置**：

- **505 个 `tcl/` 配置** —— 零修改、零重编译即可使用；
- **127 个 `src/` C 源文件** —— 已就位，但还需要在构建系统里注册才能编译进产物。

另有 **99 个与官方重复的文件已剔除**，**4109 个跨仓重复副本被折叠**
（详见「已处理的重复问题」）。

## 目录结构

```
tcl/                     ← OpenOCD 配置树：官方配置 + 505 个第三方配置
  target/                     284  芯片目标配置
  board/                      147  开发板配置（含 flash_algorithms/ 10 个）
  interface/                   47  调试器接口
  cpld/                        14  CPLD 配置
  fpga/                         2  FPGA bitstream
  chip/, cpu/                   2  芯片/架构公共片段

src/                     ← C 源码：官方源码 + 127 个第三方驱动/目标
  target/                     92  新架构支持（ARC / WCH RISC-V / NDS32 ...）
  jtag/drivers/               33  新适配器与传输层
  server/                      2  remote_bitbang 服务端

manifest/                ← 合并过程的可审计产物（唯一事实来源）
  PROVENANCE.json             632 个文件的来源仓库/分支/commit/SHA-256/许可证
  consolidated.json           去重决策：胜出者、被折叠的重复、上游重复项
  upstream.json               本 fork 所基于的上游 commit
  upstream-index.txt          该 commit 的全量文件清单，去重判定基准
  repos.csv / repos.json      688 个候选仓库排名
  licenses.csv                632 行许可证索引（逐文件）

docs/                    调研结论 / 清单报告 / 使用说明 / 许可证清单
tools/                   全部工具脚本
```

> **480 vs 505**：`manifest/consolidated.json` 记录 480 个上游确实没有的独立支持项；
> 磁盘上有 505 个 `tcl` 文件，差额 25 个是为满足 `source [find ...]` 引用而补齐的依赖文件。
> 与官方重复的文件在 `consolidate.py` **写 manifest 时**就剔除了，所以重跑抓取器
> 不会把已剔除的副本再拉回来。
>
> **全部 632 个文件都锁定了来源 commit**，可逐文件追溯到具体 fork 的具体提交。

## 为什么直接合并，而不是外挂一层

上游根 `Makefile.am` 用**通配符**安装 TCL 文件：

```makefile
TCL_FILES = find $(srcdir)/tcl -name '*.cfg' -o -name '*.tcl' -o -name '*.txt'
```

所以新增 `.cfg` 不需要改 `configure.ac`、不需要重新生成构建条目 —— 放进
`tcl/` 就够了。C 代码同理，放进 `src/jtag/drivers/`、`src/target/`。

两种布局的实际差别在于**更新**：

| | 外挂 overlay | 合并进源码树（本仓库） |
|---|---|---|
| 上游把 TCL 收进厂商子目录并改名 | overlay 里的旧副本静默遮蔽官方修复 | git 报冲突，由人决定 |
| 合并新 fork 的同名文件 | 目录里撞名，只能挑一个 | 走正常的合并 / 重命名流程 |
| 上游删除某个配置 | overlay 副本继续留着，来源 fork 都没了 | 上游删除即删除 |
| 交付给用户 | 需要装官方版 + 装 overlay + `-s` | 一个二进制 |

## 构建

```bash
./bootstrap && ./configure && make -j && sudo make install
```

Windows 见上游 `README.Windows.md`（本仓库未改动）。

## 怎么用

```bash
openocd -f interface/xxx.cfg -f target/xxx.cfg -f board/xxx.cfg
```

直接从源码树运行未安装的版本：

```bash
./src/openocd -s tcl -f board/xxx.cfg
```

## 未完成：C 驱动还没进构建系统

`src/` 下 127 个第三方文件已经在正确的目录里，但**没有**在以下位置注册：

- `configure.ac` —— 没有对应的 `AC_CHECK_LIB` / 特性检测；
- `Makefile.am`、`src/Makefile.am`、`src/jtag/drivers/Makefile.am`、
  `src/target/Makefile.am`、`src/server/Makefile.am` —— 没有源文件条目；
- `src/jtag/drivers/drivers.c`、`src/target/target.c`、`src/server/server.c`
  —— 没有驱动注册函数；
- `config.h` —— 没有 `BUILD_*` 开关；
- `doc/manual/` —— 没有手册章节。

因此当前构建产物**只包含官方支持的驱动**，`tcl/` 里的配置对已编译的驱动
立即可用，对尚未注册的驱动则会在运行时报告驱动不存在。要启用某个驱动，
按上游 CONTRIBUTING 的方式补齐上面五处，逐个验证能编译后再提交。

一个可行的起点：`tcl/jtag/` 与 `tcl/interface/` 里如果有对应的驱动配置，
就说明该驱动在 fork 里是完整可用的，优先注册。

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

- `GPL-2.0`：156 个文件，来源明确。
- `NOASSERTION`：451 个文件，GitHub 未能解析 SPDX。
- `UNRESOLVED`：25 个文件，即依赖闭包补充的文件，来源已知但未单独解析。

后两类在商用前需人工审计头部声明。逐文件来源见 `manifest/PROVENANCE.json`，
汇总见 [03-LICENSES.md](03-LICENSES.md)。

## 复现全流程

```bash
export GH_TOKEN=<你的 token>      # 仅从环境变量读取，绝不写入文件
export PYTHONIOENCODING=utf-8    # 部分文件名含非 GBK 字符

bash tools/run_mine.sh            # 1. 扫描 688 个仓库
python tools/refine_survey.py     # 2. 过滤噪声、排除自身仓库
python tools/consolidate.py       # 3. 跨仓去重、选定来源
bash tools/run_fetch.sh           # 4. 抓取文件 + 自动校验
python tools/resolve_deps.py --apply   # 5. 补齐引用依赖直到闭合
python tools/pin_commits.py            # 6. 回填 commit pin
python tools/gen_report.py             # 7. 清单报告
python tools/gen_licenses.py           # 8. 许可证清单
python tools/build_provenance.py       # 9. 汇总 PROVENANCE.json
python tools/prune_upstream_dups.py    # 10. 剔除与官方等价的重复
python tools/prune_shadow.py           # 11. 剔除遮蔽官方的同名扁平文件
python tools/verify_tree.py            # 12. 完整性校验，必须 PASS
```

每一步都可单独重跑；重复运行不会破坏已有结果。一键版本：

```bash
python tools/pipeline.py --apply
```

## 已知缺口

| 缺口 | 规模 | 说明 |
|---|---|---|
| C 驱动未注册进构建 | 127 | 见「未完成：C 驱动还没进构建系统」 |
| 未深挖的仓库 | 488 个（688 − 200） | 全部做过 `tcl/target` 粗筛（688/688），但只深挖了 star 靠前的 200 个；提高 `DIFF_BUDGET` 可扩展 |
| 无许可证信息 | 476 / 632（75%） | 商用前必须人工审计，见 [03-LICENSES.md](03-LICENSES.md) |
| 烧录器只有配置没有驱动 | 7 个 | `dbgagent`、`aji_client`、`tas_client`、`ddmi_usb`、`aice`、`mpdbgagent`、`ice2000` |
| Synopsys 板级 | 4 个不可用 | 依赖厂商内部构建产物 |
| 无运行时验证 | 全部 | 校验全是静态的，未在真机上 `source` 过 |

## 已处理的重复问题

合并过程中曾混入两类与官方重复的文件，现已由工具自动剔除：

1. **与官方等价**（路径相同，或规范化后相同，如 `ti_cc13x0.cfg`
   ↔ `tcl/target/ti/cc13x0.cfg`）—— 由 `prune_upstream_dups.py` 剔除，
   `verify_tree.py` 报为 ERROR。
2. **同名但目录不同**（如 `am335x.cfg` ↔ `tcl/target/ti/am335x.cfg`）。
   规范化比对会把两者折叠成同一个键，所以上一类检测不出来，
   由 `prune_shadow.py` 单独处理。

在这两种布局里它们都会**长期遮蔽官方文件**：外挂布局下 `-s` 让 overlay 排在搜索
路径前面，合并布局下旧副本和新文件躺在同一个目录里，结果都是运行在几年前的
旧配置上。所以 `tools/sync_upstream.py` 在发现官方已收编某项支持时会以非 0 退出。
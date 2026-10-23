# OpenOCD 第三方支持整合

[![snapshot](https://github.com/P4rfa1t/openocd/actions/workflows/snapshot.yml/badge.svg)](https://github.com/P4rfa1t/openocd/actions/workflows/snapshot.yml)

`openocd-org/openocd` 的 fork。把散落在各家社区 fork 里、从未上游化的芯片 /
开发板 / 烧录器支持，**直接合并进源码树本身** —— 同样的目录、同样的构建系统、
同样的 `git merge`。

> 英文版见 [`README.md`](README.md)。

---

## 为什么需要它

OpenOCD 上游对新增 target 一直很保守。一份芯片支持通常在某个维护者的 fork
里躺上几年 —— 有时是永远 —— 因为 PR 一直没提上来。同时同一份板级配置在 40 个
仓库之间被复制粘贴，每个仓库的拼写还略有差别，于是 `openocd -f board/xxx.cfg`
在这台机器上能用、在那台机器上不能用。

把这些 fork 收进一个外挂目录并不能解决问题。外挂目录必须遮蔽官方文件的搜索
路径，于是上游某次重命名之后，被遮蔽的旧副本还在悄悄生效。那不叫合并，叫覆盖。

**本仓库是一个真正的 fork。** 上游文件待在 `src/`、`tcl/`、`doc/`、`contrib/`，
就在上游放它们的地方。第三方支持待在它该在的目录：

```
tcl/target/xxx.cfg        ← 芯片目标配置
tcl/board/xxx.cfg         ← 开发板配置
tcl/interface/xxx.cfg     ← 调试器接口
src/jtag/drivers/xxx.c    ← 烧录器驱动
src/target/xxx.c          ← 新架构后端
```

更新只要一条命令，冲突也是真正能读懂的冲突：

```bash
git fetch upstream
git merge upstream/master
```

上游重组目录时，git 会把冲突摆在你面前，而不是让一个被遮蔽的搜索路径继续
悄悄供着过期的副本。

---

## 合并了什么

扫描了 689 个候选仓库 —— 500 个上游 fork + 搜索命中的 189 个独立仓 —— 跨仓
去重，并剔除与官方等价的文件。

| | 数量 | 说明 |
|---|---:|---|
| `tcl/` 脚本文件 | 702 | 686 个 `.cfg` + 16 个 `.tcl`/`.xml`/`.txt`；**零构建改动即生效** |
| `src/` C 源码 | 65 | 35 个 `.c` 加 30 个 `.h`；**47 个已接入构建**，18 个已就位但未注册 |
| 折叠掉的重复副本 | 6910 | 每条路径只保留一个胜出版本 |
| 与官方重复而剔除 | 7376 | 上游已经收编，或上游已把它挪到子目录 |
| 判定不可用而排除 | 621 | 构建系统文件、非 C 负载，以及上游已同名的核心内部文件 |

扫描识别出的 1298 条唯一路径里，有 747 条 tier-1 记录被标为已导入，其中 697 条至今
仍在树里；50 条导入后被有意移除，147 条从未落地。另有 5 个文件作为已进树配置的
依赖被带了进来（它们没有自己的 tier-1 记录），所以**今天树里的第三方文件是 767 个** ——
`tcl/` 702 个 + `src/` 65 个。账本闭合：697 + 5 = 702。

没进来的 260 个 C 源码全部需要逐后端移植：它们是某个驱动或架构的完整实现，但
是照着旧版 OpenOCD 的 API 写的。其中 `src/flash` 最大（125 个），其次是
`src/target`（85 个）和 `src/jtag`（50 个）。

没落地的 tier-1 TCL 路径是 147 条 —— 机械地说，就是那些既不在树里、也没记进
`removed_from_tree` 的 tier-1 记录。旧版这里还有一套「上游已收编 73 / 缺后端 46 /
依赖缺失 25 / 缓存无文件体 5 / 原样可导入 12 / 导入后删除 11」的手工分类，来自更早的快照，
现在没有任何工具能复现，已从 README 删除。可复现的是 tier-1 账本：894 条候选、
747 条标为已导入、697 条仍在树里、50 条导入后移除、147 条从未落地。

TI 板级配置需要的那两个包装文件（`interface/ti/xds100v2.cfg`、`xds100v3.cfg`）、
3 条早就在树里、只是落在扁平名父目录下的路径，以及依赖这两个包装文件的 9 份 TI 板级配置，
都在 `manifest/consolidated.json` 的 `not_imported` 里逐文件列出（共 407 条）。
要么是有意删掉的。

另外两组补齐了 **767 个文件**这个数，每个都有自己的来源记录：

- **21 个文件是作为依赖进来的** —— 一个配置 `source` 另一个配置时，被引用的
  文件跟着一起进树。它们在 manifest 里标为 `imported_as: dependency`。
- **1 个文件上游也有同名版本** —— `tcl/target/adspsc58x.cfg`，内容与上游的
  `tcl/target/adsp-sc58x.cfg` 不同。树里保留第三方版本，这个同名冲突就是
  `verify_tree` 报的 25 条 warning 之一。
  `tools/verify_tree.py` 会把这次同名冲突报成一条 warning。

上游共 2203 个文件，本树 3032 个。

**全部 767 个导入文件都钉在它被发布时的那个 commit 上。** 任何一个文件都能回溯
到具体的 fork 和具体的提交：

```bash
python - <<'PY'
import json
files = json.load(open("manifest/PROVENANCE.json", encoding="utf-8"))["files"]
entry = files["tcl/target/nucleo_l552ze.cfg"]
print(entry["source_repo"], entry["source_branch"], entry["source_commit"], entry["license"])
PY
```

本次扫描覆盖 **689 个候选仓库**，其中 53 个至少贡献了一个至今仍在树里的文件。

### `tcl/` 文件立即可用

上游根 `Makefile.am` 用通配符安装 TCL，不是硬编码文件清单：

```makefile
TCL_FILES = find $(srcdir)/$(TCL_PATH) -name '*.cfg' -o -name '*.tcl' -o -name '*.txt'
```

所以新增的 `.cfg` 会被 `make install` 收进去 —— **不用改 `configure.ac`、不用改
`Makefile.am`、不用重新编译**。任何"给这些文件自动生成构建条目"的方案，都是在
凭空制造并不存在的复杂度。

### `src/` 文件分两种状态

65 个新 C 源文件与头文件里有 47 个已接入构建 —— 24 个能注册出可用的
`target_type` 或 `adapter_driver` 的 `.c`，加上它们需要的头文件：

| 组 | 后端 | 构建开关 |
|---|---|---|
| `TARGETS_ALL` | `c28x`、`tms320`、`quark_d2000`、`quark_se`、`vortex86`、`loongarch`、`rvmax`、`rv32m1` | `--disable-third-party-targets` 可整组关掉 |
| `MCHP_RI4` | `mchp_ri4_bridge` | 还需要 libusb1 |
| `VEXRISCV` | `vexriscv` | 还需要 libyaml |

新增的 target type 一共 10 个，adapter driver 6 个 —— `dirtyjtag`、`ice1000`、
`ice2000`、`ice1500`、`dbgagent`、`mp_dbgagent` —— 跟上游的 38 个 target type、
45 个 adapter driver 并列注册。

`rvmax` 与 `rv32m1` 的命令都带架构前缀 —— `rvmax_tap_select`、
`rv32m1_du_select`、`rv32m1_core_select` 等等。上游 `or1k` 后端注册的是没有前缀的
`tap_select` / `du_select` / `addreg`，而 OpenOCD 对重复的命令名是**静默忽略**的：
后注册的会沿用前一个的 handler。如果不加前缀，第二个后端就会被第一个的 handler
接管。加上前缀之后，三者可以共存。

剩下 18 个 —— 11 个 `.c` 和 7 个 `.h` —— 是**代码就位、未注册**：
`al_link.c`、`al_link_cyusb.c`、`cmsis_dap_wch.c`、`esp_gpio.c`、`jtag_esp_remote.c`、
`jtag_tcp.c`、`wlinke.c`、`rbb_server.c`、`aarch64_coproc_reg.c`、`wch_riscv.c`、
`wch_riscv-013.c`，加上只被这些文件 include 的头文件（`al_link_cyusb.h`、`esp_gpio.h`、
`rbb_server.h`、`aarch64_system_registers.h`、`aarch64_system_registers_defs.h`、
`altera_virtual_jtag.h`、`wch_riscv.h`）。每个文件卡在哪都不一样 —— 原先列在这里的
`arc32` 家族因为接不进构建，已在 `7ffeda047` 里删除。旧版把这 18 个文件
统一归因成「依赖上游已改名的 API」，那是错的：`jtag_tcp.c`、`jtag_esp_remote.c`、
`cmsis_dap_wch.c`、`aarch64_coproc_reg.c` 在上游从未出现过，`21ab67574` 新导入的 11 个
文件同样如此。`docs/02-usage.md` 里有逐文件的卡点表。

### ST-LINK 外部加载器驱动

`src/flash/nor/stldr_driver.c` 是 STMicroelectronics 的外部加载器驱动，从
`STMicroelectronics/OpenOCD` 的 `openocd-cubeide-r7` 分支导入。它让一个 flash
bank 可以由 ST-LINK 固件 blob 来烧写，而不是靠专用 flash 算法 —— 较新的 STM32
系列就是这样烧的。

驱动基本按厂商原样导入，只改了两处：

- **ELF 结构在文件内自带定义。** `.stldr` 是个 ELF32 object，驱动自己手工遍历
  section header 和符号表，没走 OpenOCD 通用的 image 层。`<elf.h>` 并非每个构建
  宿主都有 —— Windows 发布版是用 MinGW 交叉编译的，那里没有 `elf.h` —— 所以文件
  自带它需要的 `Elf32_Shdr` / `Elf32_Sym` 定义，并包在 `#ifndef HAVE_ELF_H` 里，
  有 elf.h 的宿主仍然用系统的。
- **超时参数改成无符号。** `stldr_exec_function()` 原本是 `int`，而
  `target_run_algorithm()` 的形参是 `unsigned int`。

**`.stldr` 加载器二进制本身不在本仓库里。** 它们是 ST 发布的专有 blob，用到它们
的四份导入配置会在运行时去 `loaders/stldr/...` 找：

| 配置 | 需要的加载器 |
|---|---|
| `tcl/target/stm32v8x.cfg` | 按板子用 `stldr set_loader` 指定 |
| `tcl/target/stm32l4plusx.cfg` | 按板子用 `stldr set_loader` 指定 |
| `tcl/board/art_pi2.cfg` | `loaders/stldr/ART-Pi2_ST_winbond_64MB.stldr` |
| `tcl/board/atk_cnn647b.cfg` | `loaders/stldr/MX25UM25645G_ATK-CNN647B_ExtMemLoader.stldr` |

把需要的加载器复制到 `openocd` 可执行文件旁边的 share 目录，再让配置指过去。

---

## 构建

这是一棵标准的 OpenOCD 树，没有额外步骤。

```bash
git clone --recursive https://github.com/P4rfa1t/openocd.git
cd openocd
./bootstrap && ./configure && make -j
sudo make install
```

第三方 target 架构默认开启。只要上游的树：

```bash
./configure --disable-third-party-targets
```

三个可选依赖是**探测**而不是**必需**。缺哪个库，就只是少了用它的那个组，
configure 不会因此失败：

| 依赖 | 开了才能用 |
|---|---|
| `libusb-1.0` | `mchp_ri4_bridge` 的 USB 后端、全部 ADI 探针 |
| `libyaml-0.1` | `vexriscv` 目标 |
| `zlib` | `mchp_ri4` 的固件下载（`.gz` 脚本包） |

Windows 见上游的 `README.Windows.md`，本 fork 没有改动它。

### CI：预编译的 Windows 包

`.github/workflows/snapshot.yml` 用 MinGW 交叉编译 x86_64 Windows 包并作为
workflow artifact 上传。它就是上游自己的 workflow，只改了目标三元组和去掉
发布 Release 那一步；依赖清单（libusb1、hidapi、libftdi、capstone、libjaylink、
jimtcl、libyaml、zlib）和构建配方都是上游的。

---

## 每一处改动都可追溯

### 来源清单

`manifest/PROVENANCE.json` 逐文件记录：来源仓库、分支、确切 commit、GitHub
解析出的许可证、文件发布时的 SHA-256，以及任何本地改动。分层的
`manifest/tier1-PROVENANCE.json` / `manifest/tier2-PROVENANCE.json` 保存合并前
的同一份数据。

偏差分成两种形式记录，因为它们含义不同：

- `content edited in this fork` —— 真实改动：移植到新版上游 API、修复
  `source [find ...]` 路径、构建系统修正。
- `line endings normalised to LF` —— 内容与 fork 发布的字节完全一致，只有行
  尾符不同。

这个区分是必要的。本仓库的某一版曾对自己的完整性检查报出 543 处不匹配 —— 那
是因为树在 Windows 上以文本模式重建，每个导入文件都被悄悄存成 CRLF，而 manifest
描述的是 LF 原件；门禁分不清「被改过」和「在 Windows 上检出的」。现在两边都修好了：
树里全是 LF，767 个导入文件中有 548 个与发布方摘要逐字节吻合，2 个只剩行尾符差异，
217 个带真实本地编辑（其中 26 个同时做了行尾符规整）—— 目标 API 移植、
`source [find ...]` 路径搬移、第三方驱动的修复，以及 `rvmax` / `rv32m1` 两个后端。

被有意移除的文件仍留在 manifest 的 `removed_from_tree` 段里，连同移除原因和
移除它的那次提交。审计链是双向的。

### 校验

```bash
python tools/verify_tree.py
```

```
recorded : 767
on disk  : 767
errors   : 0
warns    : 25
VERIFY: PASS
```

25 条 warning 是：一个文件名与上游同名但内容不同（有意保留），以及 24 个
GitHub 解析不出许可证的文件。

### 其它工具

| 工具 | 作用 |
|---|---|
| `tools/verify_tree.py` | 离线完整性门禁：记录的文件都在、摘要吻合、不与上游重复、TCL 花括号平衡 |
| `tools/refresh_provenance.py` | 有意编辑后刷新摘要，原摘要保留在 `pristine_sha256` |
| `tools/normalize_eol.py` | 把文本文件归一为 LF，二进制按 git 同款的 8 KiB NUL 启发式跳过 |
| `tools/sync_upstream.py` | 报告相对钉住的上游 commit，上游新增 / 删除 / 收编了什么 |
| `tools/prune_deleted.py` | 删掉树里已被有意移除的文件的 manifest 记录 |
| `tools/prune_upstream_dups.py` | 删掉上游现已拥有的导入文件 |
| `tools/prune_shadow.py` | 删掉上游换目录后残留的影子副本 |
| `tools/build_provenance.py` | 把两个分层 manifest 合并成总表 |
| `tools/consolidate.py` | 从扫描原始数据重建整合索引 |
| `tools/survey_nested_src.py` | 修补扫描：被探测目录下的**子目录**里的源文件 |
| `tools/expand_subtrees.py` | 修补扫描：递归走 trees API 当成不透明条目的那些子目录 |
| `tools/sync_doc_numbers.py` | 按 manifest 重写文档里手写的数字，让它们不会漂移 |
| `tools/gen_licenses.py` | 重新生成 `docs/03-LICENSES.md` 与 `manifest/licenses.csv` |
| `tools/gen_report.py` | 重新生成 `docs/01-inventory.md` |
| `tools/patch_target_groups.py` | 幂等地把 target 组接进 `configure.ac`、`src/target/Makefile.am`、`src/target/target.c` |
| `tools/patch_interfaces.py`、`tools/patch_interface_h.py`、`tools/patch_makefile.py`、`tools/patch_usbmux.py` | 同类的适配器驱动幂等接线 |
| `tools/check_target_signatures.py` | 把第三方后端的回调签名与上游 `target_type` 逐个比对 |
| `tools/port_new_archs.py` | 只读：断言 rvmax / rv32m1 的移植项全部到位，且旧写法没有残留 |
| `tools/stage_new_archs.py` | 把暂存的 rvmax / rv32m1 源码逐字节复制到树内对应位置 |
| `tools/stage_new_imports.py` | 把新批准的第三方文件下载到暂存目录，不直接进树 |
| `tools/stage_symbol_check.py`、`tools/deep_link_check.py` | 只读：找出暂存文件用到但上游没有定义的标识符 |
| `tools/fix_target_apis.py`、`tools/fix_driver_apis.py` | 把导入的后端移植过上游 API 漂移 |
| `tools/fix_relocated_sources.py` | 修复仍指向旧扁平路径的 `source [find ...]` 引用 |
| `tools/audit_dangling_refs.py` | 只读：找出解析不到任何文件的 `source [find X]` 引用 |
| `tools/audit_target_headers.py` | 只读：核对每个第三方 target 的 include 在树里是否成立 |
| `tools/fetch_third_party.py`、`tools/fetch_missing_tcl.py` | 从钉住的 commit 重新拉取导入文件 |
| `tools/mine_github.py`、`tools/refine_survey.py`、`tools/resolve_deps.py`、`tools/pin_commits.py` | 扫描阶段：发现、分类、钉住候选仓库 |
| `tools/pipeline.py`、`tools/run_mine.sh`、`tools/run_fetch.sh` | 端到端的扫描流水线 |

`tools/patch_target_groups.py` 是刻意做成幂等的 —— 连跑两次产出逐字节相同的
文件；树里每一块它自己的代码都带哨兵注释，脚本据此找回并替换自己的工作。

---

## 文档

| 文件 | 内容 |
|---|---|
| [`docs/00-findings.md`](docs/00-findings.md) | 调研阶段：机制是什么、试过什么、哪里想错了 |
| [`docs/01-inventory.md`](docs/01-inventory.md) | 清单：扫了多少仓库、多少文件、来自哪里 |
| [`docs/02-usage.md`](docs/02-usage.md) | 使用说明与已知限制清单 |
| [`docs/03-LICENSES.md`](docs/03-LICENSES.md) | 逐文件许可证表 |
| [`manifest/PROVENANCE.json`](manifest/PROVENANCE.json) | 767 个导入文件的机器可读来源记录 |

---

## 发布

本 fork 的发布 tag 形如 `v<上游版本>-fork.<n>` —— 上游 `developer` 线上的一个点版本
加 fork 序号 —— 由 [`.github/workflows/snapshot.yml`](.github/workflows/snapshot.yml)
构建。推一个 tag 会产出 `openocd-<tag>-x86_64-w64-mingw32.tar.gz`，Release 本体由 CI
用 `gh` 生成；本机不发布任何东西。流程与打下一个 tag 前必须跑的清单见
[`docs/04-release.md`](docs/04-release.md)，改了什么见 [`CHANGELOG.md`](CHANGELOG.md)。

## 许可

继承自上游的 OpenOCD 源码为 GPL-2.0-or-later；文档为
GFDL-1.2-no-invariants-or-later。见 `COPYING` 与 `LICENSES/`。

**导入的第三方文件不在这个总括声明的覆盖范围内。** 767 个文件里，GitHub 解析出
123 个为 GPL-2.0、5 个为 GPL-2.0-or-later、615 个为 `NOASSERTION`（意思是
*GitHub 判定不出许可证*，不是说它宽松），24 个无法解析。这些 `NOASSERTION` 文件
自带专有声明，例如 Analog Devices 的 flash 算法，写着 "This software is
proprietary to Analog Devices, Inc."。

因此本仓库**没有单一的属于自己的许可**。如果你打算再分发，请先读
`manifest/licenses.csv` 与 `docs/03-LICENSES.md`。`LICENSE` 文件把这件事写全
了。

---

## 已知限制

- **「12 个原样就能导入」的候选经完整路径复核后全都不成立。** 补齐扫描的子目录
  盲区之后，对剩下还没有文件的配置重新评估了一遍，挑出 12 个 `source [find ...]`
  看似可解析的候选。按完整路径逐条核对：其中 3 个
  （`interface/ftdi/calao-usb-a9260-c01.cfg`、`-c02.cfg`、`cc3200lp.cfg`）早就在
  树里，只是落在 `tcl/interface/` 而不是 `tcl/interface/ftdi/`；剩下 9 个 TI 板级
  配置都 `source [find interface/ti/xds100v2.cfg]` 或 `xds100v3.cfg`，而这两个
  包装文件树里没有（树里只有 `ftdi/xds100v2.cfg`）。原判定按文件名而非路径比对。
  要导入那 9 个，得先补两个包装文件。

  旧版这里还有一段「46 个需要后端 / 25 个依赖没进树 / 5 个缓存里没文件体」的手工分类，
  来自同一份更早的快照，已删除。可查的权威记录是 `manifest/consolidated.json` 的
  `not_imported`（407 条，逐文件带来源 commit），缺 C 后端的逐文件分析在
  `manifest/nor-driver-scan.json`。
- **65 个新 C 源文件与头文件里有 18 个没被编译**（11 个 `.c`、7 个 `.h`）。
  它们带着完整来源记录留在树里，但依赖已经变动的上游 API —— 或者（`21ab67574` 新导入的
  11 个文件，以及 `jtag_tcp.c`、`jtag_esp_remote.c`、`cmsis_dap_wch.c`、`aarch64_coproc_reg.c`）
  依赖上游从未有过的 API。要注册它们，得逐后端移植。
- **四份 Synopsys 板级配置没导入。** `board/synopsys_amla3.cfg`、
  `board/synopsys_angel4.cfg`、`board/synopsys_haps51.cfg`、
  `board/synopsys_ml509.cfg` 发布在 `intel/OpenOCD` 里，但任何公开仓库都没有
  对应的 target 文件 —— 它们是需要 Synopsys 内部构建产物的 bring-up 板。引用
  它们的文件因此也没导入，所以没留下悬空引用。它们记录在
  `manifest/consolidated.json` 的 `not_imported` 里。
- **上游的命名漂移被保留而非修掉。** 同一个板子在多个 fork 里有多种拼写时，
  只保留胜出的那一种，其余被折叠 —— 落败者记录在
  `manifest/consolidated.json` 的 `path_spellings` 里。
- **上游基线是钉住的。** `manifest/upstream.json` 记录树是从哪个上游 commit
  分叉的，`tools/sync_upstream.py` 能报告相对任意 ref 的差异。
- **两份 ARC 板级配置目前还用不了。** `arc_axc001.cfg`、`arc_axc002.cfg` 创建的是
  `arc600`、`arc700` 两种 target。上游重写过的 `src/target/arc.c` 只提供 `arcv2`，
  而本该提供另外两个的 `arc32` 家族已就位、被判定接不进构建并在 `7ffeda047` 里删除 ——
  所以这两份配置指向的后端本树根本没有。（`arc_axc003_hs36.cfg` 只需要 `arcv2`，可用。）
- **401 个导入的配置还在用已废弃的 `-chain-position`。** 上游的 `tcl/` 里已经是
  0 处（全部改用 `-dap` / `-tap`）；这 493 处全在导入的第三方配置里 —— `target create`
  366 处、`dap create` 119 处、`pld create` 6 处，其余靠变量拼接。机械替换只能
  自动解掉 69 处（对象名与取值在同一行且完全相同），其余 424 处要人工过一遍：
  多数文件在别的配置里定义 TAP，正确的 `-tap` 名得从那个文件里读出来。今天这不算坏 ——
  选项仍然可用 —— 但下次动某个配置时，这是第一件该修的事。
- **`adi-usbmux` 开关是空的。** `src/jtag/drivers/usbmux.c` 是 Win32 命名管道
  helper，不是 adapter driver，但它现在被挂在 `PROCESS_ADAPTERS` 上，于是
  `--enable-adi-usbmux` 存在，而树里根本没有叫 `usbmux` 的 `adapter_driver`。
  更麻烦的是 `dbgagent` 驱动用来判断「要不要走 mux」的那个宏
  `_ADI_USB_MUX_` 全仓从未定义，所以 `adi_dbg_agent.c` 里的 mux 代码被编译
  掉了，`use_usbmux` 命令实际是空操作。源 fork 的做法是把它当成普通的
  `AC_ARG_ENABLE([usbmux])` helper，用 `USE_USBMUX` 包起来 —— 应该改回那个
  形态。
- **三组已就位的驱动被卡在上游，而不是被卡在这棵树上。** 扫描发现了 ESP32 GPIO
  bit-bang 探针、WCH RISC-V 调试探针和 Anlogic AL-Link 探针的支持。三组代码都在
  树里（见上面的未接线清单），但没有一组能原样注册：
  - `esp_gpio.c` / `esp_gpio.h` 需要 ESP-IDF 的 GPIO 与 dedicated-GPIO HAL
    （`driver/gpio.h`、`hal/gpio_ll.h`），那根本不在 OpenOCD 树里。
  - `wlinke.c` 需要整套 SDI transport 层 —— `src/jtag/` 下的 `sdi.c` / `sdi.h`
    和 `struct adapter_driver` 上的 `sdi_ops` 成员 —— 上游都没有；`wch_riscv.c`
    则是上游 `riscv.c` 的私有分支，期望上游保持 `static` 的符号。
  - `al_link.c` 需要 `JTAG_TDI` 命令类型、`DEBUG_CAP_TDI_SEQ` 能力位和
    `jtag_add_tdi_seq()` —— 上游一个都没有 —— 而它用的 CyUSB 后端仅限 Windows。

  仍然因为上游缺代码而挡住导入的，只剩 9 份 Anlogic AL-Link 目标配置
  （`tcl/target/anlogic/*_al_link.cfg`）。所有记录都留在 `manifest/consolidated.json`
  的 `not_imported` 里，带来源 commit，工作不会丢。

---

## 参与贡献

欢迎提 PR，标准很具体：

1. **不要加一份上游已有的文件的副本。** 先查；本次扫描找到 6910 份这样的
   重复，以及 7376 个上游后来已经收编的文件。
2. **改了导入文件就刷新 manifest。** 跑
   `python tools/refresh_provenance.py` 并把结果一起提交，让摘要与文件一致，
   改动被记录而不是被掩盖。
3. **移植后端要在 `tools/patch_target_groups.py` 里接线**，不要手改
   `configure.ac` 和 `src/target/Makefile.am` —— 那两块归脚本管，手改会被覆盖。
4. **保持全树 LF。** `.gitattributes` 会强制，漂移了就用
   `tools/normalize_eol.py` 修回来。

---

## 致谢

这棵树之所以存在，是因为 53 个别人的仓库发布了上游不肯收的芯片支持。他们的
提交、代码和许可声明都保留在 `manifest/` 里。上游 OpenOCD 的作者们打下了这棵
树所依赖的全部基础。

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

扫描了 688 个候选仓库 —— 499 个上游 fork + 搜索命中的 189 个独立仓 —— 跨仓
去重，并剔除与官方等价的文件。

| | 数量 | 说明 |
|---|---:|---|
| `tcl/` 脚本文件 | 739 | 722 个 `.cfg` + 17 个 `.tcl`/`.xml`/`.txt`；**零构建改动即生效** |
| `src/` C 源码 | 73 | 37 个 `.c` 加 36 个 `.h`；**47 个已接入构建**，26 个已就位但未注册 |
| 折叠掉的重复副本 | 6910 | 每条路径只保留一个胜出版本 |
| 与官方重复而剔除 | 7376 | 上游已经收编，或上游已把它挪到子目录 |
| 判定不可用而排除 | 621 | 构建系统文件、非 C 负载，以及上游已同名的核心内部文件 |

扫描识别出的 1298 条唯一路径里，**809 条进了树**，489 条没进。

没进来的 328 个 C 源码全部需要逐后端移植：它们是某个驱动或架构的完整实现，但
是照着旧版 OpenOCD 的 API 写的。其中 `src/target` 最大（133 个），其次是
`src/flash`（125 个）、`src/jtag`（68 个）和 `src/server`（2 个）。

没进来的 161 个 TCL 文件分这样：

| | 数量 | 原因 |
|---|---:|---|
| 上游已经收编 | 73 | 上游把它们挪进了子目录，扫描只看到扁平名字 |
| 缺一个树里没有的后端 | 46 | 它们驱动的是 C 代码从未公开的探针或芯片族 —— Infineon TriCore、Anlogic `al_link` 探针、WCH RISC-V、ESP32 GPIO 探针、ST-LINK 外部加载器家族之类 |
| 依赖的文件本身没进树 | 25 | 某条 `source [find ...]` 指向的配置没有导入 |
| **原样就能导入** | **12** | 它们的 `source [find ...]` 引用全部可解析，且所需的驱动、target type、flash 算法树里都已经有了 |
| 扫描缓存里没有文件体 | 5 | 扫描记下了路径，但从未抓取文件内容 |

另外两组补齐了 **812 个文件**这个数，每个都有自己的来源记录：

- **5 个文件是作为依赖进来的** —— 一个配置 `source` 另一个配置时，被引用的
  文件会一起被带进来；manifest 里标为 `imported_as: dependency`。
- **1 个文件上游也有同名版本** —— `tcl/target/adspsc58x.cfg`，内容与上游的
  `tcl/target/adsp-sc58x.cfg` 不同。树里保留第三方版本，
  `tools/verify_tree.py` 会把这次同名冲突报成一条 warning。

上游共 2203 个文件，本树 3074 个。

**全部 812 个导入文件都钉在它被发布时的那个 commit 上。** 任何一个文件都能回溯
到具体的 fork 和具体的提交：

```bash
python - <<'PY'
import json
files = json.load(open("manifest/PROVENANCE.json", encoding="utf-8"))["files"]
entry = files["tcl/target/nucleo_l552ze.cfg"]
print(entry["source_repo"], entry["source_branch"], entry["source_commit"], entry["license"])
PY
```

本次扫描覆盖 **688 个候选仓库**，其中 58 个至少贡献了一个最终进树的文件。

### `tcl/` 文件立即可用

上游根 `Makefile.am` 用通配符安装 TCL，不是硬编码文件清单：

```makefile
TCL_FILES = find $(srcdir)/$(TCL_PATH) -name '*.cfg' -o -name '*.tcl' -o -name '*.txt'
```

所以新增的 `.cfg` 会被 `make install` 收进去 —— **不用改 `configure.ac`、不用改
`Makefile.am`、不用重新编译**。任何"给这些文件自动生成构建条目"的方案，都是在
凭空制造并不存在的复杂度。

### `src/` 文件分两种状态

73 个新 C 源文件与头文件里有 47 个已接入构建 —— 24 个能注册出可用的
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

剩下 26 个 —— 13 个 `.c` 和 13 个 `.h`：`arc32` 家族、`adi_v5_cmsis_dap`、
`aarch64_coproc_reg`，以及 `arc_ftdi_cjtag` / `cmsis_dap_wch` /
`jtag_esp_remote` / `jtag_tcp` 驱动，加上只有它们 include 的头文件
—— **在树里，但没被编译**。它们针对的是上游已经改过接口的 API，要注册它们，
得先做下面说的那套移植。故意这样交付：代码在树里、可见、可审阅，在接上之前
完全无害。

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
棵树是在 Windows 上以文本模式重建的，每个导入文件都被悄悄存成了 CRLF，而
manifest 描述的是 LF 原件。门禁分不清"这个文件被改过"和"这个文件是在 Windows
上检出的"。现在两边都修好了：树里全是 LF，769 个文件与发布方摘要逐字节吻合，
4 个被标为仅行尾符差异，42 个带真实本地编辑 —— target API 移植、重定位后的
`source [find ...]` 路径修正、第三方驱动的修复，以及 `rvmax` / `rv32m1` 两个后端。

被有意移除的文件仍留在 manifest 的 `removed_from_tree` 段里，连同移除原因和
移除它的那次提交。审计链是双向的。

### 校验

```bash
python tools/verify_tree.py
```

```
recorded : 812
on disk  : 812
errors   : 0
warns    : 26
VERIFY: PASS
```

26 条 warning 是：一个文件名与上游同名但内容不同（有意保留），以及 25 个
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
| [`manifest/PROVENANCE.json`](manifest/PROVENANCE.json) | 812 个导入文件的机器可读来源记录 |

---

## 许可

继承自上游的 OpenOCD 源码为 GPL-2.0-or-later；文档为
GFDL-1.2-no-invariants-or-later。见 `COPYING` 与 `LICENSES/`。

**导入的第三方文件不在这个总括声明的覆盖范围内。** 812 个文件里，GitHub 解析出
141 个为 GPL-2.0、1 个为 GPL-2.0-or-later、648 个为 `NOASSERTION`（意思是
*GitHub 判定不出许可证*，不是说它宽松），25 个无法解析。有些 `NOASSERTION` 文件
自带专有声明，例如 Analog Devices 的 flash 算法，写着 "This software is
proprietary to Analog Devices, Inc."。

因此本仓库**没有单一的属于自己的许可**。如果你打算再分发，请先读
`manifest/licenses.csv` 与 `docs/03-LICENSES.md`。`LICENSE` 文件把这件事写全
了。

---

## 已知限制

- **12 个 TCL 文件原样就能导入，但还没导。** 补齐扫描的子目录盲区、又导入了 252
  个配置之后，对剩下 161 个还没有文件的配置重新评估了一遍：有 12 个的
  `source [find ...]` 引用全部可解析，所需的驱动、target type、flash 算法树里
  也都已经有了，一个 C 文件都不用改，只要把文件本身放进来。另有 46 个需要树里
  还没有的后端（Infineon TriCore、Anlogic `al_link`、WCH RISC-V、ESP32 GPIO
  探针、ST-LINK 外部加载器家族），25 个依赖的配置本身没进树，5 个在扫描缓存里
  没有文件体。逐项分类见 `manifest/consolidated.json` 的 `not_imported` 段，
  缺失 C 后端的文件级分析见 `manifest/nor-driver-scan.json`。
- **73 个新 C 源文件与头文件里有 26 个没被编译**（13 个 `.c`、13 个 `.h`）。
  它们带着完整来源记录躺在树里，但针对的是已经改过接口的上游 API。
  要注册需要逐个后端做移植。
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
- **三份 ARC 板级配置目前还用不了。** `arc_axc001.cfg`、`arc_axc002.cfg`、
  `arc_axc003_hs36.cfg` 创建的是 `arc600`、`arc700`、`arcv2` 三种 target。
  上游重写过的 `src/target/arc.c` 只提供 `arcv2`，另外两个来自那族已就位但
  未接线的 `arc32` 源码。把那族接进构建，这三份配置就能用了。
- **192 个导入的配置还在用已废弃的 `-chain-position`。** 上游的 `tcl/` 里已经
  一处不剩；`src/target/arm_dap.c` 和 `src/target/target.c` 都会打印
  `DEPRECATED! '-chain-position' will be removed in the future, use '-tap'
  instead`，PLD 驱动那边也会警告。导入的文件保留了它们各自 fork 里发布的
  写法。机械替换只能自动处理 219 处里的 49 处 —— 多数文件的 TAP 是在另一个
  配置里定义的，对应的 `-tap` 名字得从那个文件里读出来，剩下的要人工过一遍。
  目前不影响使用，这个选项还有效，但改到哪个配置就顺手改掉哪个。
- **`adi-usbmux` 开关是空的。** `src/jtag/drivers/usbmux.c` 是 Win32 命名管道
  helper，不是 adapter driver，但它现在被挂在 `PROCESS_ADAPTERS` 上，于是
  `--enable-adi-usbmux` 存在，而树里根本没有叫 `usbmux` 的 `adapter_driver`。
  更麻烦的是 `dbgagent` 驱动用来判断「要不要走 mux」的那个宏
  `_ADI_USB_MUX_` 全仓从未定义，所以 `adi_dbg_agent.c` 里的 mux 代码被编译
  掉了，`use_usbmux` 命令实际是空操作。源 fork 的做法是把它当成普通的
  `AC_ARG_ENABLE([usbmux])` helper，用 `USE_USBMUX` 包起来 —— 应该改回那个
  形态。
- **三组导入候选被卡在上游，而不是被卡在这棵树上。** 扫描发现了 ESP32 GPIO
  bit-bang 探针、WCH RISC-V 调试探针和 Anlogic AL-Link 探针的支持，文件也已经
  取回来分析过，但三组都没法原样落地：
  - `esp_gpio.c` / `esp_gpio.h` 依赖整套 ESP-IDF 的 GPIO 与 dedicated-GPIO
    HAL（`driver/gpio.h`、`hal/gpio_ll.h`），OpenOCD 树里根本不存在。
  - `wlinke.c` 需要一整套 SDI transport 层 —— `src/jtag/` 下的 `sdi.c` /
    `sdi.h` 一对文件，外加 `struct adapter_driver` 上的 `sdi_ops` 成员，
    上游没有；
    而 `wch_riscv.c` 是上游 `riscv.c` 的私有分叉，依赖上游标成 `static`
    的符号。
  - `al_link.c` 需要 `JTAG_TDI` 命令类型、`DEBUG_CAP_TDI_SEQ` 能力位和
    `jtag_add_tdi_seq()` —— 上游一个都没有 —— 而且它用的 CyUSB 后端只支持
    Windows。

  它们仍然记录在 `manifest/consolidated.json` 的 `not_imported` 里，连同来源
  commit，工作不会白做。

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

这棵树之所以存在，是因为 58 个别人的仓库发布了上游不肯收的芯片支持。他们的
提交、代码和许可声明都保留在 `manifest/` 里。上游 OpenOCD 的作者们打下了这棵
树所依赖的全部基础。

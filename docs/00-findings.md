# OpenOCD 第三方针源整合 · 调研结论

> 全部结论均来自本次实际 API 探测（2026-10-18），未验证项已明确标注。
>
> ⚠️ 本文件由调研阶段写成，其中「上游基线」一节用的是**按子目录比较**得到的数字，
> 已被后续发现证明不可靠（见文末「方法论修正」）。请以 `docs/01-inventory.md`
> 为准，本文件仅保留调研期的定性结论与待验证线索。

## 0. 核心机制结论（决定整个方案）

上游根 `Makefile.am` 用**通配符**安装 TCL 文件，不存在硬编码文件清单：

```makefile
TCL_FILES = find $(srcdir)/tcl -name '*.cfg' -o -name '*.tcl' -o -name '*.txt' | \
        sed -e 's,^$(srcdir)/$(TCL_PATH),,'
```

**推论**：把额外 `.cfg` / `.tcl` 放进同样的脚本目录即可生效，
**不需要修改 `configure.ac` 或 `Makefile.am`，不需要重新编译**。
任何"自动生成构建条目"的方案都是凭空制造复杂度。

## 1. 上游基线

> ⚠️ 下表是按子目录枚举所得，**不可信**。上游实际把 TCL 重组进了厂商子目录
> （`tcl/target/ti/`、`tcl/target/st/`、`tcl/target/nordic/` …），
> 子目录枚举会把它们漏掉。正确基线是全量递归索引：**2203 个 blob**。
> 详见 `manifest/upstream-index.txt`。

在全部 `tcl/` 中**搜索不到**以下关键字，即对应支持确实尚未上游化：
`ch32`、`py32`、`puya`、`nuvoton`、`aurix`、`tamarin`、`aic88`。

> 这份清单原先还列了 `at32`，那是**错的**：上游 `upstream/master` 的 `tcl/` 里已经有
> `tcl/target/artery/at32f4x.cfg`（`git grep -c at32 upstream/master -- tcl/` 命中 1 个文件），
> 所以 `at32` 不能算「搜索不到」。其余 7 个关键字的复核结果都是 0 命中。

## 2. 分层结论：什么能直接覆盖，什么必须打补丁

OpenOCD fork 新增的内容只落在两个桶里。

**桶一 · 纯 TCL，零编译**（`tcl/target/`、`tcl/board/`、`tcl/interface/`）
另外还有一类"看着像 C 其实不是"：只是**为已有 C 驱动写配置**的新 `.cfg`。
例如 AT32 系列（`vllogic` 的 119 个文件）本质是 Cortex-M4 + 类 STM32F1 flash，
用上游现成的 flash 驱动即可，**不需要任何新 C 代码**。

**桶二 · 必须改 C 源码**
- `src/flash/nor/*.c` — 新的 flash bank 驱动
- `src/jtag/drivers/*.c` — 新的适配器/传输层（WCH、ESP usb-bridge、BlackMagic、AJI、TAS）
- `src/target/*.c` — 新的架构支持（`nds32.c`、`arc_*.c`）
- 以及 `src/flash/nor/core.c`、`src/jtag/core.c`、`src/jtag/interface.c` 的注册登记

按文件数计，多数价值在桶一；但**所有阻塞性工作都在桶二**。

## 3. 各厂商现状（已上游 vs 仍 fork-only）

> 下表的文件计数来自扫描阶段的原始数据（`raw/` 池），**不可从当前树复算**；
> 「已上游 / 仍 fork-only」的判定已用 `git grep upstream/master` 复核过。

| 厂商 / 仓库 | TCL | C | 结论 |
|---|---|---|---|
| **WCH CH32V** `cjacker/wch-openocd` | 109 | 71 | **仍 fork-only**，上游无任何 `ch32*` |
| **ESP32** `espressif/openocd-esp32` | 92 | 29 | TCL 已上游；**flash 驱动仍 fork-only** |
| **Puya PY32** `l0ud/openocd-puya` | 有 | `puyaf0x.c` | **仍 fork-only** |
| **Artery AT32** `vllogic/openocd_cmsis-dap_v2` | 119 | 11 | **仍 fork-only**，纯 TCL 收益高 |
| **Nuvoton** `OpenNuvoton/OpenOCD-Nuvoton` | 87 | 62 | **仍 fork-only** |
| **Nordic nRF5** | TCL 已上游 | `nrf51.c` | 仅 flash 驱动 fork-only |
| **TI** `TexasInstruments/ti-openocd` | 155 | 21 | **混合**：`cc26xx.c` 已上游，cc23/cc27/MSPM 未上游 |
| **ST** `STMicroelectronics/OpenOCD` | 136 | 0 | **几乎纯 TCL** |
| **Synopsys ARC** `intel/OpenOCD`（已归档） | 184 | 81 | **仍 fork-only** |
| **AURIX** `go2sh/aurix-openocd` | 有 | `tc3xx.c` | **仍 fork-only** |
| **Black Magic** `walmis/openocd-blackmagic` | 有 | 有 | **仍 fork-only** |

### 已在上游、无需再导入
ESP32 TCL、Nordic 全家桶、Kontron `k1921vk01t.cfg`、TI `stellaris.cfg`、`nds32v5.cfg`、TI `cc26xx` flash 驱动。

## 4. 许可证（必须逐文件记录，不可统一假设）

- 多数仓库实测为 `GPL-2.0-or-later`。
- `OpenNuvoton/OpenOCD-Nuvoton` 为 `GPL-2.0`。
- `raspberrypi/openocd` 与 `flipperdevices/openocd` 的 SPDX 报为 **"other"**，**导入前必须逐文件审计头注释**。

> 注意：**"ESP32 是 Apache-2.0" 的说法是错的**。那说的是 ESP-IDF，
> 不是 OpenOCD fork；OpenOCD fork 是 GPL-2.0-or-later。
> 上游自己的 per-file 头也很松散（如 `tcl/target/stm32f1x.cfg` 只写裸 `# SPDX-License-Identifier: GPL`），
> 所以要**定一个统一策略**，而不是继承每个文件的写法。

## 5. 已知数据陷阱（重要）

用文件名做 diff 会产生**上游重命名噪声**：`ti_msp432.cfg`、`nds32-aice.cfg`、
`nordic_nrf51_dk.cfg`、`ti_cc26x0.cfg` 在几乎每个 fork 里都出现"缺失"，
但它们只是上游把它们**移进了子目录**（`tcl/target/nordic/`、`tcl/target/ti/`），
并不是真正的新文件。

> ⚠️ 本节末尾那句"实测 basename 零碰撞，所以新增判定可靠"是**错的**，已被推翻。
> 见文末「方法论修正」第 3 条：上游重组时同时改了目录**和**文件名
> （`ti_cc13x0.cfg` → `tcl/target/ti/cc13x0.cfg`），basename 比对根本匹配不上。

## 6. 方案建议

**分层合并（已实现为单一源码树）。**

- **`tcl/`**：纯 TCL 文件合并进官方配置树的对应目录。零重编译，
  也是唯一能处理**已归档**仓库（Intel、Flipper）和许可证待审计仓库的方案。
- **`src/`**：桶二的 C 代码合并进官方源码树的对应目录，但**不自动进构建**
  —— 每个驱动仍需在 `configure.ac` / `Makefile.am` / `drivers.c` / `target.c`
  里注册。可以按厂商分别提上游 PR（`at32xx.c`、`wchriscv.c`、`puyaf0x.c`、
  `esp32*.c`、`cc23xx/cc27xx/mspm33`）。建议从 **Artery AT32** 和
  **TI cc23xx/cc27xx** 入手 —— 它们是"单文件 flash 驱动 + 成熟通用内核"，
  价值/工作量比最高，也最可能被接受。

调研阶段曾判断「只能做成外挂层」，那是错的：上游根 `Makefile.am` 用通配符
安装 TCL，新增文件不需要改构建脚本；C 代码放进 `src/` 后由 git 正常处理合并
冲突，比一份静默遮蔽官方文件的 overlay 更适合长期维护。

## 7. 未能验证 / 需注意

- 早期一批探测用了我**猜的文件名**（`riscv.c`、`cmsis-dap.c`）当对照组，全部 404；
  换成真实存在的文件（`README.md`、`src/target/armv7m.c`）后返回 200，
  证明是文件名猜错而非文件缺失。报告中每个 404 都来自**带真实对照组**的批次。
- STM32G0/G4 的上游状态未确认（路径猜测失败）。
- `esden`、`DCVostok`、`foss-for-mips-arc-processors`、`sandeepmistry`、
  `stacksmashing`、`erwango`、`hikob` 的许可证/时间戳缺失（限流）。
- 生态侧未验证：Silicon Labs Gecko SDK、Nordic nrfutil（**纯 Python，很可能与 OpenOCD 无关**）、
  Debian/AUR 补丁、Zephyr。

---

## 8. 方法论修正（实现阶段发现的三类错误）

调研阶段的方法有系统性缺陷，实现过程中逐个暴露并修正。**这三条是本项目最容易复发的坑**：

### 8.1 GitHub trees 接口返回的是「相对子目录」的路径

请求 `/git/trees/<ref>:tcl/target` 时，条目路径是 `esp32.cfg` 而不是
`tcl/target/esp32.cfg`。早期代码假设是仓库根相对路径，导致所有
`startswith("tcl/target/")` 过滤全部落空，**每一个 fork 都报「0 个新增」**，
而报告里显示的却是「+77 新增」——两个数字来自不同阶段，互相矛盾却没人核对。

### 8.2 fork 列表包含用户自己的镜像

GitHub 的 forks 接口返回了 `P4rfa1t/openocd`（即当前工作目录对应的仓库）。
它只是上游的镜像，却被计为「179 个新增 cfg」。
自引用会让整份报告失真，必须显式排除。

### 8.3 上游重组同时改了目录和文件名（最隐蔽）

上游把 TCL 收进了厂商子目录，**并且**去掉了文件名里冗余的厂商前缀：

| 上游真实路径 | 老 fork 里的路径 | 老 fork 里的另一形态 |
|---|---|---|
| `tcl/target/ti/cc13x0.cfg` | `tcl/target/ti_cc13x0.cfg` | `tcl/target/ti/cc13x0.cfg` |

> 注：中列那个扁平名 `tcl/target/ti_cc13x0.cfg` 在本树里**不存在** —— 它作为与上游等价的
> 重复项被剔除了（记在 `manifest/consolidated.json` 的 `excluded` 口径里）。本树里只有
> 上游形态 `tcl/target/ti/cc13x0.cfg`。

**一个上游文件对应两个 fork 路径，且与其中两个都没有相同的 basename。**
逐字节比对确认：fork 版内容与上游一致，唯一差别是内部引用写成了
`source [find target/ti_cc26x0.cfg]` 而上游是 `source [find target/ti/cc26x0.cfg]`。

只按 basename 比对会漏掉 `ti_cc13x0.cfg`，
把它误判成新增，**凭空多出 26 个假的 TI 支持文件**（那是当时那次错误比对的结果；26 这个数字不可从当前树复算）。
最终规则是三级判定：

1. 路径完全相同 → 上游已有
2. basename 相同 → 上游只是挪了目录
3. **规范化路径相同**（去 `_`、`-`、`/` 后比对）→ 上游挪了目录并改了名

只有三级都不命中的，才算真新增。

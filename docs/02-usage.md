# 整合结果与使用说明

## 一句话结论

本仓库是 `openocd-org/openocd` 的 fork。扫描 GitHub 上 **688 个** OpenOCD
相关仓库（499 个官方 fork + 搜索命中的 189 个独立仓），跨仓去重、剔除与官方等价的
副本后，得到 **801 个文件**的第三方支持，全部合并在**它们本该在的位置**：

- **728 个 `tcl/` 配置** —— 零修改、零重编译即可使用；
- **73 个 `src/` C 源文件与头文件** —— 已就位，其中 **47 个已接入构建**，
  其余 26 个仍需按上游现有 API 改写后才能注册。

另有 **7376 个与官方重复的文件已剔除**，**6910 个跨仓重复副本被折叠**
（详见「已处理的重复问题」）。

## 目录结构

```
tcl/                     ← OpenOCD 配置树：官方配置 + 728 个第三方配置
  target/                     913  芯片目标配置（含 vendor 子目录）
  board/                      604  开发板配置（含 flash_algorithms/）
  interface/                  224  调试器接口
  cpld/                        23  CPLD 配置
  fpga/                        35  FPGA bitstream
  chip/                        28  芯片公共片段
  cpu/                         10  架构公共片段

src/                     ← C 源码：官方源码 + 73 个第三方驱动/目标
  target/                     149  顶层 .c（其中 20 个是第三方新架构：ARC32 / LoongArch / C28x / TMS320 / Vortex86 / VexRiscv / Quark / Microchip RI4 ...）
  target/rvmax/                9  文件，3 个 .c（ADI RVMAX 后端）
  target/rv32m1/               6  文件，3 个 .c（SiFive RV32M1 后端）
  jtag/drivers/                76  顶层 .c（其中 9 个是第三方适配器）
  flash/nor/                    2  第三方 NOR 驱动（rv32m1、ST-LINK 外部加载器 stldr）

manifest/                ← 合并过程的可审计产物（唯一事实来源）
  PROVENANCE.json            801  个文件的来源仓库/分支/commit/SHA-256/许可证
  consolidated.json           去重决策：胜出者、被折叠的重复、上游重复项
  upstream.json               本 fork 所基于的上游 commit
  upstream-index.txt          该 commit 的全量文件清单，去重判定基准
  repos.csv / repos.json      688 个候选仓库排名
  licenses.csv               801  行许可证索引（逐文件）

docs/                    调研结论 / 清单报告 / 使用说明 / 许可证清单
tools/                   全部工具脚本
```

> **894 vs 728**：`manifest/consolidated.json` 里有 894 条 tier-1 记录（上游确实没有的
> 独立 TCL 支持项），其中 **722 条进了树**，172 条没进（分类见下）。
> 一个配置 `source` 另一个配置时，被引用的文件会一起被带进来
> （如 `tcl/interface/ftdi/*.cfg`、`tcl/board/flash_algorithms/*.cfg`）。
> 所以 `tcl/` 下的第三方文件数是 722 + 5 个「只作为依赖进来、不在 imported 记录里」
> + 1 个与上游同名的 `tcl/target/adspsc58x.cfg` = **728**。
>
> **那 12 个「原样就能导入」的候选经复核并不成立。** 补齐子目录盲区并导入
> 252 个配置之后，对剩下还没进树的配置重新评估，其中 12 个曾判定为
> `source [find ...]` 引用全部可解析。按完整路径复核后，12 个全都不成立：
> 3 个（`interface/ftdi/calao-usb-a9260-c01.cfg`、`-c02.cfg`、`cc3200lp.cfg`）
> 早已在树里，只是落在 `tcl/interface/` 而不是 `tcl/interface/ftdi/`；
> 另外 9 个 TI 板级配置都 `source [find interface/ti/xds100v2.cfg]` 或
> `ti/xds100v3.cfg`，而这两个包装文件树里没有（树里只有 `ftdi/xds100v2.cfg`）。
> 原来的判定按文件名而非路径比对，把 `ftdi/xds100v2.cfg` 当成了 `ti/xds100v2.cfg`。
> 要导入那 9 个，得先补两个包装文件。另有 46 个需要树里还没有的后端
> （Infineon TriCore、Anlogic `al_link`、WCH RISC-V、ESP32 GPIO 探针、
> ST-LINK 外部加载器家族等），25 个依赖的配置本身没进树，5 个在扫描缓存里
> 没有文件体。另有 11 个导入后又从树里删掉：7 个重复的 TI 板级配置、
> `target/nrf_common.cfg`、`interface/stlink-usb.cfg`、两个
> `interface/calao-usb-a9260-c0*.cfg`。
> 与官方重复的文件在 `consolidate.py` **写 manifest 时**就剔除了，所以重跑抓取器
> 不会把已剔除的副本再拉回来。
>
> **全部 801 个文件都锁定了来源 commit**，可逐文件追溯到具体 fork 的具体提交。

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

**可选依赖**（探测不到就只是不编那一组，不会让 configure 失败）：

| 依赖 | 开了才能用 |
|---|---|
| `libusb-1.0` | `mchp_ri4_bridge` 目标后端、全部 ADI 探针 |
| `libyaml-0.1` | `vexriscv` 目标 |
| `zlib` | `mchp_ri4` 的固件下载（`.gz` 脚本包） |

**第三方 target 开关**：`--enable-third-party-targets`（默认开）控制
`c28x` / `tms320` / `quark_d2000` / `quark_se` / `vortex86` / `loongarch` /
`rvmax` / `rv32m1` / `mchp_ri4_bridge` / `vexriscv` 这 10 个新架构。
`--disable-third-party-targets` 会把它们从构建里完全拿掉（`src/target/Makefile.am`
整块包在 `if TARGETS_ALL` 里，所以是真的关，不是摆设）。

**预编译 Windows 包**：每次 push 由 GitHub Actions 打出
`openocd-<tag>-x86_64-w64-mingw32.tar.gz`（含 openocd.exe、所需 DLL 与
`share/openocd/scripts` 全套 TCL 配置），从 Actions 页面的 artifact 下载即可。
构建流程是上游自带的 `contrib/cross-build.sh`，本仓库额外编了 libyaml 与 zlib
这两个静态依赖，以及 `--enable-dirtyjtag --enable-adi-ice1000 --enable-adi-ice1500
--enable-adi-dbgagent --enable-adi-usbmux` 一组驱动开关。

Windows 手动编译见上游 `README.Windows.md`（本仓库未改动）。

## 怎么用

```bash
openocd -f interface/xxx.cfg -f target/xxx.cfg -f board/xxx.cfg
```

直接从源码树运行未安装的版本：

```bash
./src/openocd -s tcl -f board/xxx.cfg
```

## C 驱动的接入状态

`src/` 下 73 个第三方文件里（37 个 `.c` + 36 个 `.h`），**47 个已经接入构建系统**，
其余 26 个（13 个 `.c` + 13 个 `.h`）仍是「代码就位、未注册」的状态。

### 已接入的适配器（5 个文件，6 个探针名）

| 探针名 | 源文件 | 说明 |
|---|---|---|
| `dirtyjtag` | `dirtyjtag.c` | DirtyJTAG，libusb 直连 |
| `ice1000` / `ice2000` | `ice1000.c` | ADI ICE-1000、ICE-2000，一个文件注册两个 `adapter_driver` |
| `ice1500` | `ice1500.c` | ADI ICE-1500 |
| `dbgagent` | `adi_dbg_agent.c` | ADI Debug Agent |
| `mpdbgagent` | `adi_dbg_agent.c` | ADI 多核 Debug Agent，同一个编译单元里的第二个 `adapter_driver` |
| — | `usbmux.c/h` | Windows 命名管道多路复用辅助层，供 ADI 在 `_ADI_USB_MUX_` 下选用 |

接入点共五处，全部按上游的写法补齐：

1. `configure.ac` —— `DIRTYJTAG_ADAPTER` / `ADI_ADAPTERS` / `ADI_USBMUX_HELPER`
   三组 `m4_define`（第 183–196 行），加进 `AC_ARG_ADAPTERS` 列表、
   `PROCESS_ADAPTERS` 调用（`:715`–`:717`）和 `configure` 末尾的汇总表。
   `dirtyjtag` 默认 auto；ADI 四件套要求 libusb-1.x；usbmux 仅 Windows。
2. `src/jtag/drivers/Makefile.am` —— 6 条 `if <SYM>` / `DRIVERFILES +=`（`:227`–`:248`）。
3. `src/jtag/interface.h` —— 6 条 `extern struct adapter_driver ...;`（`:386`–`:436`），
   字母序插入上游那块声明表。
4. `src/jtag/interfaces.c` —— 6 条 `&<name>_adapter_driver,`，各由
   `#if BUILD_<SYM> == 1` 包住（`:72`–`:135`）。
5. `.github/workflows/snapshot.yml` —— `OPENOCD_CONFIG` 里加
   `--enable-dirtyjtag --enable-adi-ice1000 --enable-adi-ice1500
   --enable-adi-dbgagent --enable-adi-mpdbgagent --enable-adi-usbmux`。

> `mp_dbgagent_adapter_driver`（`adi_dbg_agent.c` 里的第二个 `adapter_driver`）
> 已在 `interface.h` 声明、在 `interfaces.c` 注册（`:135`），
> 并有独立的 `--enable-adi-mpdbgagent` 开关。

CI 产物（`openocd-<tag>-x86_64-w64-mingw32.tar.gz`）实测：

```
$ ./bin/openocd.exe -c "adapter list" -c shutdown
...
dbgagent       { jtag }
dirtyjtag      { jtag }
ice1000        { jtag swd }
ice2000        { jtag swd }
ice1500        { jtag }
```

> 注意用 `-c` 而不是 `-f`。`-f` 的参数是**配置文件路径**，走的是 tcl 的
> `find` proc 去磁盘里找文件，写成 `-f "adapter driver dirtyjtag"` 会报
> `Can't find adapter driver`，看起来像驱动没编进去，其实是参数用错了。

### 已接入的 flash 驱动（2 个文件）

| 驱动名 | 源文件 | 说明 |
|---|---|---|
| `rv32m1` | `src/flash/nor/rv32m1.c` | SiFive RV32M1 内部 flash |
| `stldr` | `src/flash/nor/stldr_driver.c` | STMicroelectronics 外部加载器（ST-LINK 固件 blob） |

`stldr` 来自 `STMicroelectronics/OpenOCD` 的 `openocd-cubeide-r7` 分支。
它让一个 flash bank 由 ST-LINK 固件 blob 烧写，而不是靠专用 flash 算法 ——
较新的 STM32 系列就是这样烧的。

按厂商原样导入，只改了两处：

1. **ELF 结构在文件内自带定义。** `.stldr` 是 ELF32 object，驱动自己手工遍历
   section header 与符号表，没走 OpenOCD 通用的 image 层。`<elf.h>` 并非每个构建
   宿主都有 —— Windows 发布版用 MinGW 交叉编译，那里没有 `elf.h` —— 所以文件
   自带所需的 `Elf32_Shdr` / `Elf32_Sym`，并以 `#ifndef HAVE_ELF_H` 守卫，
   有 elf.h 的宿主仍用系统头。
2. **超时参数改为无符号。** `stldr_exec_function()` 原本取 `int`，而
   `target_run_algorithm()` 的形参是 `unsigned int`。

接线三处，全部按字母序插入上游的 NOR 驱动表：

- `src/flash/nor/Makefile.am` 的 `NOR_DRIVERS`（`%D%/stmsmi.c` 之后）；
- `src/flash/nor/driver.h` 的 `extern const struct flash_driver ...` 声明表；
- `src/flash/nor/drivers.c` 的 `flash_drivers[]` 数组。

> **`.stldr` 加载器二进制不在本仓库里** —— 它们是 ST 发布的专有 blob。
> 四份导入配置会在运行时去 `loaders/stldr/...` 找：
>
> | 配置 | 需要的加载器 |
> |---|---|
> | `tcl/target/stm32v8x.cfg` | 按板子用 `stldr set_loader` 指定 |
> | `tcl/target/stm32l4plusx.cfg` | 按板子用 `stldr set_loader` 指定 |
> | `tcl/board/art_pi2.cfg` | `loaders/stldr/ART-Pi2_ST_winbond_64MB.stldr` |
> | `tcl/board/atk_cnn647b.cfg` | `loaders/stldr/MX25UM25645G_ATK-CNN647B_ExtMemLoader.stldr` |
>
> 把需要的加载器复制到 `openocd` 可执行文件旁边的 share 目录，再让配置指过去。

### 已接入的芯片架构（10 个 target_type）

这一批是本 fork 新增的**芯片架构**，不只是探针。接线点同样在五个地方，
但入口换成 `--enable-third-party-targets`（默认开）：

| target_type | 源文件 | 配套 tcl |
|---|---|---|
| `c28x` | `c28x.c` | 无（上游也无，手写 `target create ... c28x` 即可） |
| `tms320` | `tms320.c` | 无 |
| `quark_d2000` | `quark_d2000.c` | `tcl/target/quark_d2000.cfg` + 3 个 board |
| `quark_se` | `quark_se.c` | `tcl/target/quark_se.cfg` + `tcl/board/quark_se.cfg` |
| `vortex86` | `vortex86.c` | 无 |
| `loongarch` | `loongarch.c` + `loongarch_ejtag.c` + `loongarch_pracc.c` | `tcl/target/loongson2k300.cfg` |
| `mchp_ri4_bridge` | `mchp_ri4_bridge.c` + `mchp_ri4_native.c` | `tcl/target/mchp-ri4.cfg`、`dspic33-ri4.cfg`、`pic18-ri4.cfg`、`pic32mz-ri4.cfg` |
| `vexriscv` | `vexriscv.c` | `tcl/target/arty7_*.cfg`、`murax*.cfg`、`saxon*.cfg`、`briey.cfg`、`vexriscv_sim.cfg` |
| `rvmax` | `rvmax/rvmax.c` + `rvmax_du_adv.c` + `rvmax_tap_mohor.c` | `tcl/target/max32655_riscv.cfg`、`max32680_riscv.cfg`、`max32690_riscv.cfg`、`max78000_riscv.cfg`、`max78002_riscv.cfg` |
| `rv32m1` | `rv32m1/rv32m1.c` + `rv32m1_du_adv.c` + `rv32m1_tap_mohor.c` | `tcl/target/rv32m1_ri5cy.cfg`、`rv32m1_zero_riscy.cfg` |

接线细节：

1. `configure.ac:637`–`:698` —— `AC_ARG_ENABLE([third-party-targets])` 加上
   `BUILD_TARGETS_ALL` / `BUILD_MCHP_RI4` / `BUILD_VEXRISCV` 三个宏。
   `BUILD_MCHP_RI4` 额外要求 libusb-1.x，`BUILD_VEXRISCV` 额外要求 libyaml。
   **三个宏都在 0/1 两个分支里定义**，否则 `-Wundef` 会让未定义宏静默取 0。
2. `src/target/Makefile.am` —— 整块包在 `if TARGETS_ALL` 里（`--disable-third-party-targets`
   真的能关掉）；`MCHP_RI4_SRC` 再包一层 `if USE_LIBUSB1`，
   `VEXRISCV_SRC` 再包一层 `if HAVE_LIBYAML`。
   `RVMAX_SRC` / `RV32M1_SRC` 直接列 `%D%/rvmax/xxx.c` 这样的子目录路径
   —— 上游 `src/jtag/drivers/Makefile.am` 里的 `versaloon` 就是同一种写法，
   且 `configure.ac:19` 已开 `subdir-objects`。
3. `src/target/target.c` —— extern 块（`:75`–`:92`）和 `target_types[]`（`:94` 起）
   各加一组，**三组分别用 `BUILD_TARGETS_ALL` / `BUILD_MCHP_RI4` / `BUILD_VEXRISCV`
   守卫**，与 Makefile 的条件严格对应 —— 否则没有 libyaml 的机器会在链接期
   找不到 `vexriscv_target`。
4. 三个可选依赖：`libyaml-0.1`（vexriscv）、`libusb-1.0`（mchp_ri4）、
   `zlib`（mchp_ri4 的固件下载）。都是**软依赖** —— 探测不到就只是不编那一组，
   不会让 configure 失败。
5. `tools/patch_target_groups.py` 是这部分的唯一可信来源，**幂等**：连跑 3 次
   `configure.ac` / `src/target/Makefile.am` / `src/target/target.c` 字节完全一致。
   改了上面任何一处都要改脚本，不要手改生成结果。
6. `rvmax` 与 `rv32m1` 的命令都带架构前缀（`rvmax_tap_select`、
   `rv32m1_du_select`、`rv32m1_core_select` 等）。上游 `or1k` 注册的是无前缀的
   `tap_select` / `du_select` / `addreg`，而 OpenOCD 对重名命令是**静默忽略**的
   （`src/helper/command.c` 的 `register_command()` 命中已有名字就复用它），
   所以无前缀的第二个后端会被前一个的 handler 接管。加前缀后三者可共存。

### 仍是「代码就位、未注册」（其余 26 个文件）

13 个 `.c`：

- `src/jtag/drivers/`：`arc_ftdi_cjtag.c`、`cmsis_dap_wch.c`、
  `jtag_esp_remote.c`、`jtag_tcp.c`
- `src/target/`：`aarch64_coproc_reg.c`、`adi_v5_cmsis_dap.c`、`arc32.c`、
  `arc_core.c`、`arc_dbg.c`、`arc_mntr.c`、`arc_ocd.c`、`arc_regs.c`、`arc_trgt.c`

13 个 `.h` 只被上面这些文件 include，主树没有任何引用，因此也没有进
`*_SOURCES`：`arc32.h`、`arc_core.h`、`arc_dbg.h`、`arc_mntr.h`、`arc_ocd.h`、
`arc_regs.h`、`arc_trgt.h`、`arc_ftdi_cjtag.h`、`jtag_usb_common.h`、
`aarch64_system_registers.h`、`aarch64_system_registers_defs.h`、
`altera_virtual_jtag.h`、`stm8.h`。

> `src/jtag/drivers/OpenULINK/src/` 下的 4 个 `.c` 不算在内 —— 那是 OpenULINK
> 固件子工程，自带独立 `Makefile`，不参与主构建。

没接入的原因不是遗漏，而是**这些驱动依赖上游已删除或改名的 API**，
直接编译会失败。逐个看：

| 未接入的文件 | 卡点 |
|---|---|
| `src/jtag/drivers/jtag_tcp.c`、`cmsis_dap_wch.c` | `.transports` 字段 —— 上游已改成 `unsigned int transport_ids`，`jtag_only` 常量也不存在了；`jtag_tcp.c` 还在调用 `jtag_vpi_tms`/`jtag_vpi_path_move`，而这两个是 `jtag_vpi.c` 里的 `static` |
| `src/target/arc32.c` + `arc_core.c` + `arc_dbg.c` + `arc_mntr.c` + `arc_ocd.c` + `arc_regs.c` + `arc_trgt.c` | 与上游 `src/target/arc.c` 的 `arcv2_target` **重复定义**，且 `arc32.c` 调用的 9 个 `arc_mem_*` 入口只存在于它自己那份 `arc_mem.c`；本树的 `arc_mem.c` 是上游精简版，只有 `arc_mem_read`/`arc_mem_write`，链接必然失败（CI 已验证） |
| `src/target/adi_v5_cmsis_dap.c`、`aarch64_coproc_reg.c` | 依赖上游未公开的私有 API |
| `src/jtag/drivers/arc_ftdi_cjtag.c`、`cmsis_dap_wch.c` | 依赖 `mpsse_read`/`mpsse_write`，本树的 `mpsse.h`/`mpsse.c` 里这两个函数不存在（只有 `mpsse_read_data_bits_low_byte` 一族）；`cmsis_dap_wch.c` 另需已删除的 SDI 传输层 |

> `tcl/target/arc_axc001.cfg` 等 ARC 板级配置在树里。上游 `arc.c` 只注册 `arcv2`
> 一个 target type，而 `arc32.c` 一族因为依赖它自己那份 `arc_mem.c`（本树里是
> 上游的精简版，只有 `arc_mem_read`/`arc_mem_write`）接不进构建，所以这些配置
> 统一改用 `arcv2`。代价是它们描述的 ARC600/ARC700 内核只能按 ARCv2 访问。

要接入某个驱动，得先按上游现有 API 重写，逐个验证能编译后再提交。
`tools/patch_target_groups.py` 与 `tools/patch_makefile.py`、
`tools/patch_interfaces.py`、`tools/patch_interface_h.py` 可以作模板。

**悬空的接口配置。** 扫全部 `tcl/`，有 6 个 `adapter driver` / `interface`
指令指向源码里不存在的驱动名，共 8 处：

| 配置 | 指令 | 驱动名 |
|---|---|---|
| `tcl/interface/jtag_tcp.cfg:7` | `interface jtag_tcp` | `jtag_tcp`（上面未接入） |
| `tcl/interface/jtag_esp_remote.cfg:5` | `adapter driver jtag_esp_remote` | `jtag_esp_remote`（上面未接入） |
| `tcl/interface/picoprobe.cfg:2` | `adapter driver picoprobe` | `picoprobe` |
| `tcl/interface/colobus.cfg:1` | `interface colobus` | `colobus` |
| `tcl/interface/tamarin.cfg:1`、`tcl/interface/faultier.cfg:1` | `interface tamarin` | `tamarin` |
| `tcl/interface/tas_client.cfg:7` | `adapter driver tas_client` | `tas_client` |
| `tcl/interface/nds32-aice.cfg:9` | `adapter driver aice` | `aice` |
| `tcl/board/altera_arria10__aji_client.cfg:8`、`tcl/board/altera_arria10_niosv__aji_client.cfg:15` | `adapter driver aji_client` | `aji_client` |

后 6 个（`picoprobe`、`colobus`、`tamarin`、`tas_client`、`aice`、`aji_client`）
在**上游同样没有驱动实现**，配置是各 fork 单独加的，属于上游本身的悬空；
`nds32-aice.cfg` 依赖的 `nds32_aice.c` 已被本 fork 从树里移除
（见 `removed_from_tree`）。这些配置加载时会报 `Can't find adapter driver`。
`jtag_tcp`/`jtag_esp_remote` 两份是给上面那两个待接入驱动预留的用法说明，
驱动一旦按上面那条路接通就不需要改。

来源（`manifest/PROVENANCE.json`）：`picoprobe` ← `sysprogs/openocd`，
`colobus` ← `tihmstar/openocd_colobus`，`tamarin`/`faultier` ←
`stacksmashing/openocd-tamarin`，`tas_client` ← `zuyih/openocd`，
`nds32-aice` ← `zephyrproject-rtos/openocd`，`aji_client` ←
`OlivierVanWassenhove-Dekimo/openocd`。这些 fork 都带自己的驱动实现，
但实现没进本树，所以配置是悬空的。


## 4 份 Synopsys 板级配置未导入

`intel/OpenOCD` 里有这四份 Synopsys bring-up 板级配置，它们 `source` 的
target 在任何公开仓库里都不存在（属于 Synopsys 内部交付）：

| 未导入的板级配置 | 缺失的 target |
|---|---|
| `board/synopsys_amla3.cfg` | `target/snps_aml8626x.cfg` |
| `board/synopsys_angel4.cfg` | `target/snps_angel4.cfg` |
| `board/synopsys_haps51.cfg` | `target/snps_haps51.cfg` |
| `board/synopsys_ml509.cfg` | `target/snps_ml509.cfg` |

因为配套的 target 根本不存在，这四份 board 配置**没有被导入树**，
所以树里不存在任何悬空引用 —— `git grep` 全仓 0 命中。
这四条记录保留在 `manifest/PROVENANCE.json` 的 `unresolved_references` 段里，
作为「为什么这四个文件没进来」的审计痕迹。

## 许可证提醒

- `GPL-2.0`：136 个文件，来源明确。
- `GPL-2.0-or-later`：1 个文件（`src/flash/nor/stldr_driver.c`，来自 STMicroelectronics/OpenOCD）。
- `NOASSERTION`：639 个文件，GitHub 未能解析 SPDX。
- `UNRESOLVED`：25 个文件，即依赖闭包补充的文件，来源已知但未单独解析。

后两类在商用前需人工审计头部声明 —— `NOASSERTION` **不等于**宽松许可，
部分文件带明确的专有声明（例如 `analogdevicesinc/openocd` 的 flash 算法写着
"This software is proprietary to Analog Devices, Inc."）。
逐文件来源见 `manifest/PROVENANCE.json`，
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
python tools/prune_deleted.py          # 12. 把已被有意删除的文件从 manifest 里摘掉
python tools/normalize_eol.py         # 13. 把所有文本文件归一为 LF
python tools/refresh_provenance.py     # 14. 重算摘要，并标注哪些文件被本 fork 改过
python tools/verify_tree.py            # 15. 完整性校验，必须 PASS
```

每一步都可单独重跑；重复运行不会破坏已有结果。一键版本：

```bash
python tools/pipeline.py --apply
```

`verify_tree.py` 是硬门禁：它会核对每个 manifest 条目的 SHA-256、
确认树里的每个第三方文件都有来源记录、确认没有与官方重复的同名文件、
并检查每个 `.cfg` 的 Tcl 花括号是否平衡。只有它报 `VERIFY: PASS` 才允许提交。

## 已知缺口

| 缺口 | 规模 | 说明 |
|---|---|---|
| C 驱动未注册进构建 | 26（13 个 `.c` + 13 个 `.h`） | 见「C 驱动的接入状态」；卡点是它们依赖上游已删/已改名的 API。另有 `OpenULINK/src/` 4 个固件源文件，独立 Makefile，不参与主构建 |
| 未深挖的仓库 | 488 个（688 − 200） | 全部做过 `tcl/target` 粗筛（688/688），但只深挖了 star 靠前的 200 个；提高 `DIFF_BUDGET` 可扩展 |
| 无许可证信息 | 664 / 801（83%） | 商用前必须人工审计，见 [03-LICENSES.md](03-LICENSES.md) |
| 烧录器只有配置没有驱动 | 6 个驱动名 / 8 处引用 | `aji_client`、`tas_client`、`aice`、`picoprobe`、`colobus`、`tamarin`；前 4 个上游也没有实现，后 2 个是 fork 单独加的配置。逐条见「悬空的接口配置」表 |
| Synopsys 板级 | 4 个未导入 | 依赖厂商内部构建产物 |
| ARC 配置只能按 ARCv2 访问 | 5 个 cfg | 原先写 `arc600`/`arc700`/`arc32` 的 `arc_axc001.cfg`、`arc_axc002.cfg`、`snps_axc001.cfg`、`snps_ml509_arc600.cfg`、`snps_ml509_arc700.cfg` 统一改成 `arcv2`；`arc32.c` 一族缺 `arc_mem.c` 无法接入，全树 22 个 ARC 配置现在都只用 `arcv2` |
| 无真机验证 | 全部 | 静态校验之外，只用 CI 产物跑过 `adapter list`、`target types` 和批量 `source [find ...]`（验证配置能被解析、驱动/target type/flash 驱动都在）；没有接真实探针与目标板跑过调试会话 |
| `-chain-position` 旧写法 | 408 个文件 / 504 处 | 上游 `tcl/` 已是 0 处（全部改用 `-dap` / `-tap`）；这 504 处全在导入的第三方配置里（`target create` 373 处、`dap create` 122 处、`vjtag create` 1 处，其余为变量拼接）。机械替换只能自动解出 70 处（对象名与取值同行且完全相同），其余 434 处需人工判断 TAP 名 |
| `adi-usbmux` 开关为空 | 1 个 | 它是 Win32 命名管道 helper 而非 adapter driver；`_ADI_USB_MUX_` 从未定义，mux 代码被编译掉 |
| 三组导入候选被上游阻塞 | 14 个文件 | ESP32 GPIO 探针（需 ESP-IDF HAL）、WCH RISC-V 探针（需整套 SDI transport 层）、AL-Link 探针（需 `JTAG_TDI` + `DEBUG_CAP_TDI_SEQ`，且后端仅 Windows） |
| TI XDS100 包装配置缺失 | 9 份板级配置 | 这 9 份 `tcl/board/ti/*-xds100v2.cfg` / `-xds100v3.cfg` 都 `source [find interface/ti/xds100v2.cfg]` 或 `ti/xds100v3.cfg`，树里只有 `interface/ftdi/xds100v2.cfg`；补两个三行包装文件即可，无需 C 改动 |
| 两个非 ASCII 文件名 | 2 个 | `tcl/target/1986ве1т.cfg`、`tcl/target/к1879xб1я.cfg` 是上游自己带的西里尔字母名（与 `upstream/master` 逐字节一致），不是本 fork 引入；Windows 上部分工具链会处理异常 |
| `.stldr` 加载器二进制不在仓库 | 4 份配置 | ST 发布的专有 blob，需用户自备并放到 `loaders/stldr/`；驱动本身已接入 |
| 扫描漏掉了子目录里的文件 | 已补扫，0 个待接入 | `/git/trees/<ref>:<subdir>` 对子目录**不递归**，`src/flash/nor/`、`src/target/rvmax/` 这类路径在粗扫里看不见。`tools/expand_subtrees.py` 已补上；补出来的文件经 API 漂移分析后确认与上游 `src/flash/nor/` 的 85 个驱动重合，本树实际只多 `rv32m1.c` 与 `stldr_driver.c`（均已接入），NOR 目录 87/87 全部在 `Makefile.am` 里 |

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
旧配置上。所以 `tools/sync_upstream.py` 在发现官方已收编某项支持时会以非 0 退出
（`return 1 if now_upstream else 0`），提醒你把已经上游化的第三方支持删掉。
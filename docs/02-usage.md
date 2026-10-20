# 整合结果与使用说明

## 一句话结论

本仓库是 `openocd-org/openocd` 的 fork。扫描 GitHub 上 **688 个** OpenOCD
相关仓库（499 个官方 fork + 搜索命中的 189 个独立仓），跨仓去重、剔除与官方等价的
副本后，得到 **562 个文件**的第三方支持，全部合并在**它们本该在的位置**：

- **487 个 `tcl/` 配置** —— 零修改、零重编译即可使用；
- **75 个 `src/` C 源文件与头文件** —— 已就位，其中 **46 个已接入构建**，
  其余 29 个仍需按上游现有 API 改写后才能注册。

另有 **99 个与官方重复的文件已剔除**，**4109 个跨仓重复副本被折叠**
（详见「已处理的重复问题」）。

## 目录结构

```
tcl/                     ← OpenOCD 配置树：官方配置 + 487 个第三方配置
  target/                     688  芯片目标配置（含 vendor 子目录）
  board/                      605  开发板配置（含 flash_algorithms/）
  interface/                  207  调试器接口
  cpld/                        23  CPLD 配置
  fpga/                        35  FPGA bitstream
  chip/                        28  芯片公共片段
  cpu/                         10  架构公共片段

src/                     ← C 源码：官方源码 + 75 个第三方驱动/目标
  target/                     109  顶层 .c（其中 20 个是第三方新架构：ARC32 / LoongArch / C28x / TMS320 / Vortex86 / VexRiscv / Quark / Microchip RI4 ...）
  target/rvmax/                3  .c（ADI RVMAX 后端）
  target/rv32m1/               3  .c（SiFive RV32M1 后端）
  jtag/drivers/                65  顶层 .c（其中 13 个是第三方适配器）
  flash/nor/                    1  第三方 NOR 驱动（rv32m1）

manifest/                ← 合并过程的可审计产物（唯一事实来源）
  PROVENANCE.json            562  个文件的来源仓库/分支/commit/SHA-256/许可证
  consolidated.json           去重决策：胜出者、被折叠的重复、上游重复项
  upstream.json               本 fork 所基于的上游 commit
  upstream-index.txt          该 commit 的全量文件清单，去重判定基准
  repos.csv / repos.json      688 个候选仓库排名
  licenses.csv               562  行许可证索引（逐文件）

docs/                    调研结论 / 清单报告 / 使用说明 / 许可证清单
tools/                   全部工具脚本
```

> **480 vs 487**：`manifest/consolidated.json` 里有 480 条 tier-1 记录（上游确实没有的
> 独立 TCL 支持项），其中 **461 条进了树**，19 条因引用了从未公开的 target/interface 而没进。
> 另有 **26 个文件是作为依赖进来的** —— 一个配置 `source` 另一个配置时，被引用的文件
> 会一起被带进来（如 `tcl/interface/ftdi/*.cfg`、`tcl/board/flash_algorithms/*.cfg`）。
> 所以 `tcl/` 下的第三方文件数是 461 + 26 = **487**。
> 与官方重复的文件在 `consolidate.py` **写 manifest 时**就剔除了，所以重跑抓取器
> 不会把已剔除的副本再拉回来。
>
> **全部 562 个文件都锁定了来源 commit**，可逐文件追溯到具体 fork 的具体提交。

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

`src/` 下 75 个第三方文件里（39 个 `.c` + 36 个 `.h`），**46 个已经接入构建系统**，
其余 29 个仍是「代码就位、未注册」的状态。

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

### 仍是「代码就位、未注册」（其余 29 个文件）

- `configure.ac` —— 没有对应的特性检测；
- `src/jtag/drivers/Makefile.am`、`src/target/Makefile.am`、
  `src/server/Makefile.am` —— 没有源文件条目；
- `src/jtag/interface.h` / `src/jtag/interfaces.c` —— 没有声明与注册项；
- `config.h` —— 没有 `BUILD_*` 开关；
- `doc/manual/` —— 没有手册章节。

没接入的原因不是遗漏，而是**这些驱动依赖上游已删除或改名的 API**，
直接编译会失败。逐个看：

| 未接入的文件 | 卡点 |
|---|---|
| `src/jtag/drivers/jtag_tcp.c`、`ch347_jtag.c`、`cmsis_dap_usb.c` | `.transports` 字段 —— 上游已改成 `unsigned int transport_ids` |
| `src/target/arc32.c` + `arc_core.c` + `arc_dbg.c` + `arc_mntr.c` + `arc_ocd.c` + `arc_regs.c` + `arc_trgt.c` | 与上游 `src/target/arc.c` 的 `arcv2_target` **重复定义**，且它是旧式 ARC 整体实现，上游已重写 |
| `src/target/adi_v5_cmsis_dap.c`、`aarch64_coproc_reg.c` | 依赖上游未公开的私有 API |
| `src/jtag/drivers/blackmagic.c`、`cmsis_dap_wch.c`、`jtag_esp_remote.c`、`arc_ftdi_cjtag.c` | SDI 传输层（`struct sdi_driver`）整个传输层已从上游删除 |

> `tcl/target/arc_axc001.cfg` 等 ARC 板级配置在树里，但它们 `target create` 的是
> `arc600` / `arc700` / `arcv2` —— 这三个名字上游 `arc.c` 只提供 `arcv2`，
> 所以那几份配置目前**开箱即用不了**。要修就得先把 `arc32.c` 一族接进构建。

要接入某个驱动，得先按上游现有 API 重写，逐个验证能编译后再提交。
`tools/patch_target_groups.py` 与 `tools/patch_makefile.py`、
`tools/patch_interfaces.py`、`tools/patch_interface_h.py` 可以作模板。


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

- `GPL-2.0`：139 个文件，来源明确。
- `NOASSERTION`：398 个文件，GitHub 未能解析 SPDX。
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
| C 驱动未注册进构建 | 29 | 见「C 驱动的接入状态」；卡点是它们依赖上游已删/已改名的 API |
| 未深挖的仓库 | 488 个（688 − 200） | 全部做过 `tcl/target` 粗筛（688/688），但只深挖了 star 靠前的 200 个；提高 `DIFF_BUDGET` 可扩展 |
| 无许可证信息 | 423 / 562（75%） | 商用前必须人工审计，见 [03-LICENSES.md](03-LICENSES.md) |
| 烧录器只有配置没有驱动 | 4 个 | `aji_client`、`tas_client`、`ddmi_usb`、`aice`（`dbgagent`/`ice2000` 已随本次接入进产物） |
| Synopsys 板级 | 4 个未导入 | 依赖厂商内部构建产物 |
| ARC 板级配置开箱即用不了 | 3 个 cfg | `arc_axc001/002/003_hs36.cfg` 需要的 `arc600`/`arc700` 来自未接入的 `arc32.c` 一族 |
| 无运行时验证 | 全部 | 校验全是静态的，未在真机上 `source` 过 |
| `-chain-position` 旧写法 | 192 个文件 / 219 处 | 上游 `tcl/` 已清零；机械替换只能自动解出 49 处，其余需人工判断 TAP 名 |
| `adi-usbmux` 开关为空 | 1 个 | 它是 Win32 命名管道 helper 而非 adapter driver；`_ADI_USB_MUX_` 从未定义，mux 代码被编译掉 |
| 三组导入候选被上游阻塞 | 14 个文件 | ESP32 GPIO 探针（需 ESP-IDF HAL）、WCH RISC-V 探针（需整套 SDI transport 层）、AL-Link 探针（需 `JTAG_TDI` + `DEBUG_CAP_TDI_SEQ`，且后端仅 Windows） |

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
# 整合结果与使用说明

## 一句话结论

本仓库是 `openocd-org/openocd` 的 fork。扫描 GitHub 上 **688 个** OpenOCD
相关仓库（500 个官方 fork + 搜索命中的独立仓），跨仓去重、剔除与官方等价的
副本后，得到 **632 个文件**的第三方支持，全部合并在**它们本该在的位置**：

- **505 个 `tcl/` 配置** —— 零修改、零重编译即可使用；
- **127 个 `src/` C 源文件** —— 已就位，其中 **5 个已接入构建**并验证可编译，
  其余 122 个仍需按上游现有 API 改写后才能注册。

另有 **99 个与官方重复的文件已剔除**，**4109 个跨仓重复副本被折叠**
（详见「已处理的重复问题」）。

## 目录结构

```
tcl/                     ← OpenOCD 配置树：官方配置 + 494 个第三方配置
  target/                     689  芯片目标配置（含 vendor 子目录）
  board/                      604  开发板配置（含 flash_algorithms/）
  interface/                  207  调试器接口
  cpld/                        23  CPLD 配置
  fpga/                        35  FPGA bitstream
  chip/                        28  芯片公共片段
  cpu/                         10  架构公共片段

src/                     ← C 源码：官方源码 + 92 个第三方驱动/目标
  target/                     124  顶层 .c（其中 39 个是第三方新架构：ARC / NDS32 / LoongArch / C28x ...）
  jtag/drivers/                65  顶层 .c（其中 5 个是已接入构建的第三方适配器）

manifest/                ← 合并过程的可审计产物（唯一事实来源）
  PROVENANCE.json            586  个文件的来源仓库/分支/commit/SHA-256/许可证
  consolidated.json           去重决策：胜出者、被折叠的重复、上游重复项
  upstream.json               本 fork 所基于的上游 commit
  upstream-index.txt          该 commit 的全量文件清单，去重判定基准
  repos.csv / repos.json      688 个候选仓库排名
  licenses.csv               586  行许可证索引（逐文件）

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

**预编译 Windows 包**：每次 push 由 GitHub Actions 打出
`openocd-<tag>-x86_64-w64-mingw32.tar.gz`（含 openocd.exe、所需 DLL 与
`share/openocd/scripts` 全套 TCL 配置），从 Actions 页面的 artifact 下载即可。
构建流程是上游自带的 `contrib/cross-build.sh`，本仓库只加了驱动开关。

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

`src/` 下原有的 127 个第三方文件里，**只有 5 个文件已经接入构建系统**，
其余仍是「代码就位、未注册」的状态。

### 已接入（5 个文件，4 个探针）

| 探针名 | 源文件 | 说明 |
|---|---|---|
| `dirtyjtag` | `dirtyjtag.c` | DirtyJTAG，libusb 直连 |
| `ice1000` / `ice2000` | `ice1000.c` | ADI ICE-1000、ICE-2000，一个文件注册两个 `adapter_driver` |
| `ice1500` | `ice1500.c` | ADI ICE-1500 |
| `dbgagent` | `adi_dbg_agent.c` | ADI Debug Agent |
| `mpdbgagent` | `adi_dbg_agent.c` | 同上文件的第二个 `adapter_driver`，**已定义但未注册** |
| — | `usbmux.c/h` | Windows 命名管道多路复用辅助层，供 ADI 在 `_ADI_USB_MUX_` 下选用 |

接入点共五处，全部按上游的写法补齐：

1. `configure.ac` —— `DIRTYJTAG_ADAPTER` / `ADI_ADAPTERS` / `ADI_USBMUX_HELPER`
   三组 `m4_define`，加进 `AC_ARG_ADAPTERS` 列表、`PROCESS_ADAPTERS` 调用和
   `configure` 末尾的汇总表。`dirtyjtag` 默认 auto。
2. `src/jtag/drivers/Makefile.am` —— 5 条 `if <SYM>` / `DRIVERFILES +=`。
3. `src/jtag/interface.h` —— 6 条 `extern struct adapter_driver ...;`，
   字母序插入上游那块声明表。
4. `src/jtag/interfaces.c` —— 5 条 `&<name>_adapter_driver,`，各由
   `#if BUILD_<SYM> == 1` 包住。
5. `.github/workflows/snapshot.yml` —— `OPENOCD_CONFIG` 里加
   `--enable-dirtyjtag --enable-adi-ice1000 --enable-adi-ice1500
   --enable-adi-dbgagent --enable-adi-usbmux`。

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

### 仍是「代码就位、未注册」（其余 122 个文件）

- `configure.ac` —— 没有对应的特性检测；
- `src/jtag/drivers/Makefile.am`、`src/target/Makefile.am`、
  `src/server/Makefile.am` —— 没有源文件条目；
- `src/jtag/interface.h` / `src/jtag/interfaces.c` —— 没有声明与注册项；
- `config.h` —— 没有 `BUILD_*` 开关；
- `doc/manual/` —— 没有手册章节。

没接入的原因不是遗漏，而是**这些驱动依赖上游已删除的 API**，直接编译会失败：

| 依赖的旧 API | 上游现状 |
|---|---|
| `.transports` 字段 | 已改为 `unsigned int transport_ids` |
| SDI 传输层（`struct sdi_driver`、`sdi_transports`） | 整个传输层已删除 |
| `riscv_dmi_direct_register_provider()`、`TRANSPORT_DDMI` | 该私有 API 从未进上游 |
| `hidapi.h` | 部分 fork 里是死 include |

要接入某个驱动，得先按上游现有 API 重写，逐个验证能编译后再提交。
`tools/` 下的 `patch_makefile.py`、`patch_interfaces.py`、`patch_interface_h.py`
就是这次接入 5 个文件用的脚本，可作模板。


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
| C 驱动未注册进构建 | 122 | 见「C 驱动的接入状态」；卡点是它们依赖上游已删 API |
| 未深挖的仓库 | 488 个（688 − 200） | 全部做过 `tcl/target` 粗筛（688/688），但只深挖了 star 靠前的 200 个；提高 `DIFF_BUDGET` 可扩展 |
| 无许可证信息 | 476 / 632（75%） | 商用前必须人工审计，见 [03-LICENSES.md](03-LICENSES.md) |
| 烧录器只有配置没有驱动 | 4 个 | `aji_client`、`tas_client`、`ddmi_usb`、`aice`（`dbgagent`/`mpdbgagent`/`ice2000` 已随本次接入进产物） |
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
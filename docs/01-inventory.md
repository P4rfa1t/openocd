# OpenOCD 第三方支持 · 整合清单

> 由 `tools/gen_report.py` 自动生成，数据源 `manifest/*.json`，请勿手改。

## 1. 总览

| 指标 | 数值 |
|---|---|
| 扫描候选仓库 | 688 |
| 完整深挖仓库 | 200 |
| 去重后唯一新增路径 | 607 |
| 第一层：可直接覆盖的 TCL | 480 |
| 第二层：需要改 C 源码 | 127 |
| 折叠掉的重复副本 | 4109 |
| 判定为不可导入并排除 | 107 |

按目录分布：

| 目录 | 文件数 |
|---|---|
| `target` | 284 |
| `board` | 137 |
| `src` | 127 |
| `interface` | 45 |
| `cpld` | 14 |

## 2. 贡献来源（去重后独占胜出的文件数）

| 仓库 | 第一层 TCL | 第二层 C | 落后上游文件数 | SPDX |
|---|---:|---:|---:|---|
| [`analogdevicesinc/openocd`](https://github.com/analogdevicesinc/openocd) | 57 | 5 | 6 | NOASSERTION |
| [`espressif/openocd-esp32`](https://github.com/espressif/openocd-esp32) | 50 | 3 | 1 | NOASSERTION |
| [`rxmnjke/openocd`](https://github.com/rxmnjke/openocd) | 48 | 0 | 0 | NOASSERTION |
| [`foss-for-mips-arc-processors/openocd`](https://github.com/foss-for-mips-arc-processors/openocd) | 34 | 13 | 401 | GPL-2.0 |
| [`sysprogs/openocd`](https://github.com/sysprogs/openocd) | 43 | 3 | 9 | NOASSERTION |
| [`intel/OpenOCD`](https://github.com/intel/OpenOCD) | 33 | 8 | 429 | GPL-2.0 |
| [`zephyrproject-rtos/openocd`](https://github.com/zephyrproject-rtos/openocd) | 11 | 22 | 70 | NOASSERTION |
| [`zuyih/openocd`](https://github.com/zuyih/openocd) | 26 | 1 | 0 | NOASSERTION |
| [`TexasInstruments/ti-openocd`](https://github.com/TexasInstruments/ti-openocd) | 19 | 0 | 49 | NOASSERTION |
| [`Icey7122/openocd`](https://github.com/Icey7122/openocd) | 10 | 7 | 0 | NOASSERTION |
| [`xsession/openocd`](https://github.com/xsession/openocd) | 8 | 8 | 5 | NOASSERTION |
| [`aesc-silicon/elements-openocd`](https://github.com/aesc-silicon/elements-openocd) | 11 | 4 | 33 | NOASSERTION |
| [`ciniml/openocd`](https://github.com/ciniml/openocd) | 13 | 0 | 195 | GPL-2.0 |
| [`andestech/nds-openocd`](https://github.com/andestech/nds-openocd) | 0 | 10 | 127 | NOASSERTION |
| [`vllogic/openocd_cmsis-dap_v2`](https://github.com/vllogic/openocd_cmsis-dap_v2) | 10 | 0 | 7 | NOASSERTION |
| [`OpenNuvoton/OpenOCD-Nuvoton`](https://github.com/OpenNuvoton/OpenOCD-Nuvoton) | 10 | 0 | 312 | GPL-2.0 |
| [`fatalfeel/openocd_integrated`](https://github.com/fatalfeel/openocd_integrated) | 10 | 0 | 86 | NOASSERTION |
| [`kevinmehall/openOCD`](https://github.com/kevinmehall/openOCD) | 2 | 7 | 528 | GPL-2.0 |
| [`esden/openocd`](https://github.com/esden/openocd) | 6 | 2 | 557 | GPL-2.0 |
| [`linux-msm/openocd`](https://github.com/linux-msm/openocd) | 1 | 6 | 36 | NOASSERTION |
| [`ut2or1/openocd`](https://github.com/ut2or1/openocd) | 7 | 0 | 2 | NOASSERTION |
| [`AnlogicInfo/al_openocd`](https://github.com/AnlogicInfo/al_openocd) | 1 | 5 | 122 | NOASSERTION |
| [`walmis/openocd-blackmagic`](https://github.com/walmis/openocd-blackmagic) | 5 | 1 | 216 | GPL-2.0 |
| [`ImproperCatGirl/openocd`](https://github.com/ImproperCatGirl/openocd) | 4 | 2 | 3 | NOASSERTION |
| [`riscv-collab/riscv-openocd`](https://github.com/riscv-collab/riscv-openocd) | 5 | 1 | 28 | NOASSERTION |
| [`Seneral/riscv-openocd-wch`](https://github.com/Seneral/riscv-openocd-wch) | 0 | 4 | 122 | NOASSERTION |
| [`OlivierVanWassenhove-Dekimo/openocd`](https://github.com/OlivierVanWassenhove-Dekimo/openocd) | 4 | 0 | 1 | NOASSERTION |
| [`MotorolaMobilityLLC/openocd`](https://github.com/MotorolaMobilityLLC/openocd) | 4 | 0 | 318 | GPL-2.0 |
| [`DCVostok/openocd-k1921vk`](https://github.com/DCVostok/openocd-k1921vk) | 4 | 0 | 59 | NOASSERTION |
| [`hikob/openocd`](https://github.com/hikob/openocd) | 4 | 0 | 508 | GPL-2.0 |

## 3. 芯片家族覆盖

| 家族 | overlay 文件数 | 主要来源 |
|---|---:|---|
| WCH CH32V RISC-V | 4 | `zuyih/openocd`(1), `mengfanyuc/openocd`(1) |
| Espressif ESP32 | 47 | `espressif/openocd-esp32`(47) |
| Artery AT32 | 47 | `rxmnjke/openocd`(47) |
| Puya PY32 | 1 | `vllogic/openocd_cmsis-dap_v2`(1) |
| Nuvoton N76K | 0 | — |
| AndesTech NDS | 5 | `zephyrproject-rtos/openocd`(5) |
| Infineon AURIX | 0 | — |
| Synopsys ARC | 29 | `foss-for-mips-arc-processors/openocd`(27), `intel/OpenOCD`(2) |
| Analog Devices ADuC/ADSC | 6 | `sysprogs/openocd`(5), `analogdevicesinc/openocd`(1) |
| LicheeTang | 0 | — |
| Nordic nRF | 2 | `ciniml/openocd`(1), `riscv-collab/riscv-openocd`(1) |
| Raspberry Pi RP2040/2350 | 4 | `raspberrypi/openocd`(2), `zephyrproject-rtos/openocd`(1) |
| Kontron K1921VK | 3 | `DCVostok/openocd-k1921vk`(3) |
| TI Stellaris/TMS/OMAP | 3 | `zuyih/openocd`(1), `ciniml/openocd`(1) |

## 4. 许可证分布

| SPDX | 文件数 |
|---|---:|
| NOASSERTION | 451 |
| GPL-2.0 | 156 |

> ⚠️ **451 个文件**来自 GitHub 未解析出 SPDX 的仓库，导入前需人工审计头部许可声明。

## 5. 排除项说明

共排除 107 个路径，原因：

build-system files, non-C payloads, and core internals that exist upstream under the same name and therefore need a real diff rather than a file copy

示例：

- `contrib/60-openocd-nuvoton.rules`
- `contrib/99-openocd.rules`
- `contrib/coresight-trace.txt`
- `contrib/openocd.udev`
- `src/CMakeLists.txt`
- `src/DAP.c`
- `src/DAP.cpp`
- `src/DAP.h`
- `src/DAP_config.cpp`
- `src/DAP_config.h`
- `src/DAP_vendor.c`
- `src/FreeRTOSConfig.h`

## 6. 第二层（需要改 C）明细

| 目录 | 文件数 | 主要来源 |
|---|---:|---|
| `src/target/` | 92 | `zephyrproject-rtos/openocd`(22), `foss-for-mips-arc-processors/openocd`(11) |
| `src/jtag/drivers/` | 33 | `analogdevicesinc/openocd`(5), `AnlogicInfo/al_openocd`(3) |
| `src/server/` | 2 | `AnlogicInfo/al_openocd`(2) |

### 6.1 值得优先上游化的驱动

价值/工作量比最高的是**单文件 flash 驱动**，因为它们建立在成熟的通用内核之上，不需要动内核代码：

| 文件 | 来源 | 落后上游 |
|---|---|---:|
| `src/jtag/drivers/adi_dbg_agent.c` | `analogdevicesinc/openocd` | 6 |
| `src/jtag/drivers/al_link.c` | `AnlogicInfo/al_openocd` | 122 |
| `src/jtag/drivers/al_link_cyusb.c` | `AnlogicInfo/al_openocd` | 122 |
| `src/jtag/drivers/arc_ftdi_cjtag.c` | `foss-for-mips-arc-processors/openocd` | 401 |
| `src/jtag/drivers/blackmagic.c` | `walmis/openocd-blackmagic` | 216 |
| `src/jtag/drivers/bonobo.c` | `stacksmashing/openocd` | 218 |
| `src/jtag/drivers/ch347_jtag.c` | `meriac/openocd` | 49 |
| `src/jtag/drivers/cmsis_dap_usb.c` | `dynm/openocd-starbleed` | 196 |
| `src/jtag/drivers/cmsis_dap_wch.c` | `zuyih/openocd` | 0 |
| `src/jtag/drivers/colobus.c` | `tihmstar/openocd_colobus` | 40 |
| `src/jtag/drivers/ddmi_demo.c` | `ImproperCatGirl/openocd` | 3 |
| `src/jtag/drivers/dirtyjtag.c` | `stache3000/openocd-dirtyjtag` | 7 |
| `src/jtag/drivers/esp_gpio.c` | `espressif/openocd-esp32` | 1 |
| `src/jtag/drivers/ftdi_rvswd.c` | `ImproperCatGirl/openocd` | 3 |
| `src/jtag/drivers/ice1000.c` | `analogdevicesinc/openocd` | 6 |
| `src/jtag/drivers/ice1500.c` | `analogdevicesinc/openocd` | 6 |
| `src/jtag/drivers/jtag_esp_remote.c` | `espressif/openocd-esp32` | 1 |
| `src/jtag/drivers/jtag_tcp.c` | `aesc-silicon/elements-openocd` | 33 |
| `src/jtag/drivers/mpsse-d2xx.c` | `hackpascal/openocd` | 49 |
| `src/jtag/drivers/mpsse-libusb.c` | `hackpascal/openocd` | 49 |
| `src/jtag/drivers/stlink_usb_hla_multicore.c` | `sysprogs/openocd` | 9 |
| `src/jtag/drivers/tamarin.c` | `stacksmashing/openocd-tamarin` | 85 |
| `src/jtag/drivers/usbmux.c` | `analogdevicesinc/openocd` | 6 |
| `src/jtag/drivers/wlink.c` | `fxsheep/openocd_wchlink-rv` | 140 |
| `src/jtag/drivers/wlinke.c` | `Seneral/riscv-openocd-wch` | 122 |


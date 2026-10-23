# OpenOCD 第三方支持 · 整合清单

> 由 `tools/gen_report.py` 自动生成，数据源 `manifest/*.json`，请勿手改。

## 1. 总览

| 指标 | 数值 |
|---|---|
| 扫描候选仓库 | 688 |
| 完整深挖仓库 | 200 |
| 去重后唯一新增路径 | 1298 |
| 第一层：合并进 `tcl/` 的配置 | 894 |
| 第二层：合并进 `src/` 的 C 源码 | 404 |
| 折叠掉的重复副本 | 6910 |
| 判定为不可导入并排除 | 621 |

按目录分布：

| 目录 | 文件数 |
|---|---|
| `target` | 545 |
| `src` | 404 |
| `board` | 195 |
| `interface` | 130 |
| `cpld` | 14 |
| `flash_algorithms` | 10 |

## 2. 贡献来源（去重后独占胜出的文件数）

| 仓库 | 第一层 TCL | 第二层 C | 落后上游文件数 | SPDX |
|---|---:|---:|---:|---|
| [`xsession/openocd`](https://github.com/xsession/openocd) | 259 | 20 | 5 | NOASSERTION |
| [`analogdevicesinc/openocd`](https://github.com/analogdevicesinc/openocd) | 67 | 32 | 6 | NOASSERTION |
| [`espressif/openocd-esp32`](https://github.com/espressif/openocd-esp32) | 51 | 40 | 1 | NOASSERTION |
| [`zuyih/openocd`](https://github.com/zuyih/openocd) | 67 | 23 | 0 | NOASSERTION |
| [`OpenNuvoton/OpenOCD-Nuvoton`](https://github.com/OpenNuvoton/OpenOCD-Nuvoton) | 54 | 2 | 312 | GPL-2.0 |
| [`sysprogs/openocd`](https://github.com/sysprogs/openocd) | 45 | 10 | 9 | NOASSERTION |
| [`rxmnjke/openocd`](https://github.com/rxmnjke/openocd) | 48 | 5 | 0 | NOASSERTION |
| [`foss-for-mips-arc-processors/openocd`](https://github.com/foss-for-mips-arc-processors/openocd) | 36 | 13 | 401 | GPL-2.0 |
| [`AnlogicInfo/al_openocd`](https://github.com/AnlogicInfo/al_openocd) | 28 | 20 | 122 | NOASSERTION |
| [`andestech/nds-openocd`](https://github.com/andestech/nds-openocd) | 0 | 48 | 127 | NOASSERTION |
| [`zephyrproject-rtos/openocd`](https://github.com/zephyrproject-rtos/openocd) | 14 | 29 | 70 | NOASSERTION |
| [`intel/OpenOCD`](https://github.com/intel/OpenOCD) | 34 | 8 | 429 | GPL-2.0 |
| [`fatalfeel/openocd_integrated`](https://github.com/fatalfeel/openocd_integrated) | 10 | 26 | 86 | NOASSERTION |
| [`aesc-silicon/elements-openocd`](https://github.com/aesc-silicon/elements-openocd) | 16 | 10 | 33 | NOASSERTION |
| [`ImproperCatGirl/openocd`](https://github.com/ImproperCatGirl/openocd) | 6 | 14 | 3 | NOASSERTION |
| [`TexasInstruments/ti-openocd`](https://github.com/TexasInstruments/ti-openocd) | 19 | 0 | 49 | NOASSERTION |
| [`Icey7122/openocd`](https://github.com/Icey7122/openocd) | 10 | 7 | 0 | NOASSERTION |
| [`OlivierVanWassenhove-Dekimo/openocd`](https://github.com/OlivierVanWassenhove-Dekimo/openocd) | 4 | 12 | 1 | NOASSERTION |
| [`kevinmehall/openOCD`](https://github.com/kevinmehall/openOCD) | 4 | 12 | 528 | GPL-2.0 |
| [`vllogic/openocd_cmsis-dap_v2`](https://github.com/vllogic/openocd_cmsis-dap_v2) | 10 | 4 | 7 | NOASSERTION |
| [`hackpascal/openocd`](https://github.com/hackpascal/openocd) | 10 | 3 | 49 | NOASSERTION |
| [`ciniml/openocd`](https://github.com/ciniml/openocd) | 13 | 0 | 195 | GPL-2.0 |
| [`MotorolaMobilityLLC/openocd`](https://github.com/MotorolaMobilityLLC/openocd) | 7 | 4 | 318 | GPL-2.0 |
| [`linux-msm/openocd`](https://github.com/linux-msm/openocd) | 2 | 7 | 36 | NOASSERTION |
| [`riscv-collab/riscv-openocd`](https://github.com/riscv-collab/riscv-openocd) | 7 | 2 | 28 | NOASSERTION |
| [`esden/openocd`](https://github.com/esden/openocd) | 7 | 2 | 557 | GPL-2.0 |
| [`DCVostok/openocd-k1921vk`](https://github.com/DCVostok/openocd-k1921vk) | 5 | 3 | 59 | NOASSERTION |
| [`ut2or1/openocd`](https://github.com/ut2or1/openocd) | 8 | 0 | 2 | NOASSERTION |
| [`David-lau/openocd-geehy`](https://github.com/David-lau/openocd-geehy) | 4 | 3 | 54 | NOASSERTION |
| [`go2sh/aurix-openocd`](https://github.com/go2sh/aurix-openocd) | 1 | 6 | 44 | NOASSERTION |

## 3. 芯片家族覆盖

| 家族 | tcl/ 文件数 | 主要来源 |
|---|---:|---|
| WCH CH32V RISC-V | 4 | `zuyih/openocd`(1), `mengfanyuc/openocd`(1) |
| Espressif ESP32 | 47 | `espressif/openocd-esp32`(47) |
| Artery AT32 | 47 | `rxmnjke/openocd`(47) |
| Puya PY32 | 1 | `vllogic/openocd_cmsis-dap_v2`(1) |
| Nuvoton N76K | 0 | — |
| AndesTech NDS | 5 | `zephyrproject-rtos/openocd`(5) |
| Infineon AURIX | 13 | `zuyih/openocd`(13) |
| Synopsys ARC | 30 | `foss-for-mips-arc-processors/openocd`(28), `intel/OpenOCD`(2) |
| Analog Devices ADuC/ADSC | 6 | `sysprogs/openocd`(5), `analogdevicesinc/openocd`(1) |
| LicheeTang | 0 | — |
| Nordic nRF | 2 | `ciniml/openocd`(1), `riscv-collab/riscv-openocd`(1) |
| Raspberry Pi RP2040/2350 | 4 | `raspberrypi/openocd`(2), `zephyrproject-rtos/openocd`(1) |
| Kontron K1921VK | 3 | `DCVostok/openocd-k1921vk`(3) |
| TI Stellaris/TMS/OMAP | 3 | `zuyih/openocd`(1), `ciniml/openocd`(1) |

## 4. 许可证分布

下表覆盖去重后的全部 **1298 个候选路径**（其中 795 个已导入本树）。

| SPDX | 候选文件数 | 已导入文件数 |
|---|---:|---:|
| NOASSERTION | 1064 | 652 |
| GPL-2.0 | 234 | 143 |

> ⚠️ 已导入的 **652 个文件**来自 GitHub 未解析出 SPDX 的仓库，头部许可声明需人工审计。

## 5. 排除项说明

共排除 621 个路径，原因：

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
| `src/flash/nor/` | 98 | `espressif/openocd-esp32`(20), `xsession/openocd`(12) |
| `src/target/` | 96 | `zephyrproject-rtos/openocd`(22), `foss-for-mips-arc-processors/openocd`(11) |
| `src/jtag/drivers/` | 34 | `analogdevicesinc/openocd`(5), `AnlogicInfo/al_openocd`(3) |
| `src/target/nds32_new/` | 30 | `andestech/nds-openocd`(30) |
| `src/jtag/drivers/libjaylink/libjaylink/` | 25 | `fatalfeel/openocd_integrated`(25) |
| `src/target/espressif/` | 17 | `espressif/openocd-esp32`(17) |
| `src/target/riscv/` | 13 | `andestech/nds-openocd`(6), `ImproperCatGirl/openocd`(4) |
| `src/target/aurix/` | 11 | `zuyih/openocd`(7), `go2sh/aurix-openocd`(4) |
| `src/target/rvmax/` | 10 | `analogdevicesinc/openocd`(10) |
| `src/flash/nor/adsp/spi/` | 9 | `analogdevicesinc/openocd`(9) |
| `src/jtag/drivers/aji_client/aji/` | 8 | `OlivierVanWassenhove-Dekimo/openocd`(8) |
| `src/flash/nor/adsp/` | 7 | `analogdevicesinc/openocd`(7) |
| `src/flash/nor/dwcssi/` | 6 | `AnlogicInfo/al_openocd`(6) |
| `src/jtag/drivers/tas_client/` | 6 | `zuyih/openocd`(5), `go2sh/aurix-openocd`(1) |
| `src/target/rv32m1/` | 6 | `zephyrproject-rtos/openocd`(6) |
| `src/flash/nor/vexriscv_algo/` | 5 | `aesc-silicon/elements-openocd`(5) |
| `src/jtag/drivers/aji_client/` | 4 | `OlivierVanWassenhove-Dekimo/openocd`(3), `ManniMetzger/openocd`(1) |
| `src/target/anlogic/` | 4 | `AnlogicInfo/al_openocd`(4) |
| `src/target/riscv/dtm/` | 4 | `ImproperCatGirl/openocd`(4) |
| `src/flash/nor/devs/` | 2 | `AnlogicInfo/al_openocd`(2) |
| `src/jtag/drivers/ftd2xx/` | 2 | `AnlogicInfo/al_openocd`(2) |
| `src/server/` | 2 | `AnlogicInfo/al_openocd`(2) |
| `src/jtag/drivers/angie/include/` | 1 | `riscv-collab/riscv-openocd`(1) |
| `src/jtag/drivers/libjaylink/` | 1 | `fatalfeel/openocd_integrated`(1) |
| `src/jtag/drivers/OpenULINK/include/` | 1 | `kevinmehall/openOCD`(1) |
| `src/jtag/drivers/usb_blaster/` | 1 | `OpenNuvoton/OpenOCD-Nuvoton`(1) |
| `src/target/xscale/` | 1 | `OpenNuvoton/OpenOCD-Nuvoton`(1) |

### 6.1 值得优先上游化的驱动

价值/工作量比最高的是**单文件 flash 驱动**，因为它们建立在成熟的通用内核之上，不需要动内核代码：

| 文件 | 来源 | 落后上游 |
|---|---|---:|
| `src/flash/nor/adsp/adsp218xx.c` | `analogdevicesinc/openocd` | 6 |
| `src/flash/nor/adsp/adsp_helper.c` | `analogdevicesinc/openocd` | 6 |
| `src/flash/nor/adsp/adspsc59x_a55_dma.c` | `analogdevicesinc/openocd` | 6 |
| `src/flash/nor/adsp/adspsc5xx_a5.c` | `analogdevicesinc/openocd` | 6 |
| `src/flash/nor/adsp/spi/adsp_spi.c` | `analogdevicesinc/openocd` | 6 |
| `src/flash/nor/adsp/spi/adsp_spi_dbg.c` | `analogdevicesinc/openocd` | 6 |
| `src/flash/nor/adsp/spi/adsp_spi_device.c` | `analogdevicesinc/openocd` | 6 |
| `src/flash/nor/aducm302x.c` | `analogdevicesinc/openocd` | 6 |
| `src/flash/nor/aic8800.c` | `vllogic/openocd_cmsis-dap_v2` | 7 |
| `src/flash/nor/aic8800m40.c` | `vllogic/openocd_cmsis-dap_v2` | 7 |
| `src/flash/nor/aic8800mc.c` | `vllogic/openocd_cmsis-dap_v2` | 7 |
| `src/flash/nor/air001.c` | `HalfSweet/openocd` | 53 |
| `src/flash/nor/apm32f003.c` | `David-lau/openocd-geehy` | 54 |
| `src/flash/nor/apm32f1x.c` | `David-lau/openocd-geehy` | 54 |
| `src/flash/nor/apm32f4x.c` | `David-lau/openocd-geehy` | 54 |
| `src/flash/nor/at32f4xx.c` | `rxmnjke/openocd` | 0 |
| `src/flash/nor/at32qspi.c` | `rxmnjke/openocd` | 0 |
| `src/flash/nor/at32xx.c` | `rxmnjke/openocd` | 0 |
| `src/flash/nor/aurix_eflash.c` | `zuyih/openocd` | 0 |
| `src/flash/nor/cadence_qspi.c` | `OlivierVanWassenhove-Dekimo/openocd` | 1 |
| `src/flash/nor/cc23xx.c` | `xsession/openocd` | 5 |
| `src/flash/nor/cc27xx.c` | `xsession/openocd` | 5 |
| `src/flash/nor/cc_lpf3_base.c` | `xsession/openocd` | 5 |
| `src/flash/nor/cc_lpf3_flash.c` | `xsession/openocd` | 5 |
| `src/flash/nor/ch32f2x.c` | `mengfanyuc/openocd` | 53 |


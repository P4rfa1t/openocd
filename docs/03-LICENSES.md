# 第三方许可证清单

> 由 `tools/gen_licenses.py` 生成。**本仓库汇集了他人的 OpenOCD fork，整体许可不统一**，任何商用前请先读这一页。

## 总览

| SPDX | 文件数 |
|---|---:|
| NOASSERTION | 451 |
| GPL-2.0 | 156 |
| UNRESOLVED | 25 |

**476 个文件（75%）没有可用的许可证信息**，必须逐个审计文件头部的版权声明后才能商用。

> 已知事实：OpenOCD 上游是 GPL-2.0-or-later，大多数 fork 继承该许可，所以实务上大概率都是 GPL。但 `NOASSERTION` 只表示「GitHub 没能解析出来」，**不等于宽松许可** —— 在少数 fork 里它对应的是专有许可。逐文件清单见 `manifest/licenses.csv` 与下方折叠区。

## 第一层 overlay（可直接使用）

文件数：**505**

| 来源仓库 | SPDX | 文件数 |
|---|---|---:|
| [`analogdevicesinc/openocd`](https://github.com/analogdevicesinc/openocd) | NOASSERTION(57), UNRESOLVED(10) | 67 |
| [`espressif/openocd-esp32`](https://github.com/espressif/openocd-esp32) | NOASSERTION(50), UNRESOLVED(1) | 51 |
| [`rxmnjke/openocd`](https://github.com/rxmnjke/openocd) | NOASSERTION(48) | 48 |
| [`sysprogs/openocd`](https://github.com/sysprogs/openocd) | NOASSERTION(43) | 43 |
| [`foss-for-mips-arc-processors/openocd`](https://github.com/foss-for-mips-arc-processors/openocd) | GPL-2.0(34), UNRESOLVED(2) | 36 |
| [`intel/OpenOCD`](https://github.com/intel/OpenOCD) | GPL-2.0(33), UNRESOLVED(1) | 34 |
| [`zuyih/openocd`](https://github.com/zuyih/openocd) | NOASSERTION(26), UNRESOLVED(2) | 28 |
| [`TexasInstruments/ti-openocd`](https://github.com/TexasInstruments/ti-openocd) | NOASSERTION(19) | 19 |
| [`ciniml/openocd`](https://github.com/ciniml/openocd) | GPL-2.0(13) | 13 |
| [`zephyrproject-rtos/openocd`](https://github.com/zephyrproject-rtos/openocd) | NOASSERTION(11) | 11 |
| [`OpenNuvoton/OpenOCD-Nuvoton`](https://github.com/OpenNuvoton/OpenOCD-Nuvoton) | GPL-2.0(10), UNRESOLVED(1) | 11 |
| [`aesc-silicon/elements-openocd`](https://github.com/aesc-silicon/elements-openocd) | NOASSERTION(11) | 11 |
| [`vllogic/openocd_cmsis-dap_v2`](https://github.com/vllogic/openocd_cmsis-dap_v2) | NOASSERTION(10) | 10 |
| [`Icey7122/openocd`](https://github.com/Icey7122/openocd) | NOASSERTION(10) | 10 |
| [`fatalfeel/openocd_integrated`](https://github.com/fatalfeel/openocd_integrated) | NOASSERTION(10) | 10 |
| [`ut2or1/openocd`](https://github.com/ut2or1/openocd) | NOASSERTION(7), UNRESOLVED(2) | 9 |
| [`MotorolaMobilityLLC/openocd`](https://github.com/MotorolaMobilityLLC/openocd) | GPL-2.0(4), UNRESOLVED(4) | 8 |
| [`xsession/openocd`](https://github.com/xsession/openocd) | NOASSERTION(8) | 8 |
| [`esden/openocd`](https://github.com/esden/openocd) | GPL-2.0(6) | 6 |
| [`walmis/openocd-blackmagic`](https://github.com/walmis/openocd-blackmagic) | GPL-2.0(5) | 5 |
| [`riscv-collab/riscv-openocd`](https://github.com/riscv-collab/riscv-openocd) | NOASSERTION(5) | 5 |
| [`DCVostok/openocd-k1921vk`](https://github.com/DCVostok/openocd-k1921vk) | NOASSERTION(4), UNRESOLVED(1) | 5 |
| [`OlivierVanWassenhove-Dekimo/openocd`](https://github.com/OlivierVanWassenhove-Dekimo/openocd) | NOASSERTION(4) | 4 |
| [`hikob/openocd`](https://github.com/hikob/openocd) | GPL-2.0(4) | 4 |
| [`ImproperCatGirl/openocd`](https://github.com/ImproperCatGirl/openocd) | NOASSERTION(4) | 4 |
| [`David-lau/openocd-geehy`](https://github.com/David-lau/openocd-geehy) | NOASSERTION(4) | 4 |
| [`sony/openocd-nuttx`](https://github.com/sony/openocd-nuttx) | GPL-2.0(2), UNRESOLVED(1) | 3 |
| [`nmenon/openocd`](https://github.com/nmenon/openocd) | NOASSERTION(3) | 3 |
| [`raspberrypi/openocd`](https://github.com/raspberrypi/openocd) | NOASSERTION(3) | 3 |
| [`sysprogs/esp8266-openocd`](https://github.com/sysprogs/esp8266-openocd) | GPL-2.0(3) | 3 |
| [`luyi1888/openocd`](https://github.com/luyi1888/openocd) | NOASSERTION(2) | 2 |
| [`stacksmashing/openocd-tamarin`](https://github.com/stacksmashing/openocd-tamarin) | NOASSERTION(2) | 2 |
| [`kevinmehall/openOCD`](https://github.com/kevinmehall/openOCD) | GPL-2.0(2) | 2 |
| [`Lichee-Pi/LicheeTang_openocd`](https://github.com/Lichee-Pi/LicheeTang_openocd) | GPL-2.0(2) | 2 |
| [`loopj/openocd-efm32s2`](https://github.com/loopj/openocd-efm32s2) | NOASSERTION(2) | 2 |
| [`STMicroelectronics/OpenOCD`](https://github.com/STMicroelectronics/OpenOCD) | NOASSERTION(2) | 2 |
| [`os-fpga/openocd`](https://github.com/os-fpga/openocd) | NOASSERTION(1) | 1 |
| [`snowcap-electronics/OpenOCD`](https://github.com/snowcap-electronics/OpenOCD) | GPL-2.0(1) | 1 |
| [`Blinkinlabs/OpenOCD`](https://github.com/Blinkinlabs/OpenOCD) | GPL-2.0(1) | 1 |
| [`AnlogicInfo/al_openocd`](https://github.com/AnlogicInfo/al_openocd) | NOASSERTION(1) | 1 |
| [`kvth/openocd-swd-in-out`](https://github.com/kvth/openocd-swd-in-out) | NOASSERTION(1) | 1 |
| [`tihmstar/openocd_colobus`](https://github.com/tihmstar/openocd_colobus) | NOASSERTION(1) | 1 |
| [`stache3000/openocd-dirtyjtag`](https://github.com/stache3000/openocd-dirtyjtag) | NOASSERTION(1) | 1 |
| [`linux-msm/openocd`](https://github.com/linux-msm/openocd) | NOASSERTION(1) | 1 |
| [`matrix-io/matrix-creator-openocd`](https://github.com/matrix-io/matrix-creator-openocd) | GPL-2.0(1) | 1 |
| [`karlp/openocd-hacks`](https://github.com/karlp/openocd-hacks) | NOASSERTION(1) | 1 |
| [`HalfSweet/openocd`](https://github.com/HalfSweet/openocd) | NOASSERTION(1) | 1 |
| [`mengfanyuc/openocd`](https://github.com/mengfanyuc/openocd) | NOASSERTION(1) | 1 |
| [`transcelestial/openocd`](https://github.com/transcelestial/openocd) | NOASSERTION(1) | 1 |
| [`pebble/openocd`](https://github.com/pebble/openocd) | GPL-2.0(1) | 1 |
| [`go2sh/aurix-openocd`](https://github.com/go2sh/aurix-openocd) | NOASSERTION(1) | 1 |
| [`cjacker/wch-openocd`](https://github.com/cjacker/wch-openocd) | NOASSERTION(1) | 1 |
| [`padhialuo0426/openocd`](https://github.com/padhialuo0426/openocd) | NOASSERTION(1) | 1 |

### ⚠️ 需人工审计（383 个文件无许可证信息）

这些文件的来源仓库在 GitHub 上未解析出许可证，商用前必须逐个查看文件头部的版权声明。

<details><summary><code>AnlogicInfo/al_openocd</code> (1 个)</summary>

- `tcl/interface/al_link.cfg`

</details>

<details><summary><code>DCVostok/openocd-k1921vk</code> (5 个)</summary>

- `tcl/board/vostok_vg015_dev.cfg`
- `tcl/interface/ftdi/vostok_vg015_dev.cfg`
- `tcl/target/k1921vg015.cfg`
- `tcl/target/k1921vk028.cfg`
- `tcl/target/k1921vk035.cfg`

</details>

<details><summary><code>David-lau/openocd-geehy</code> (4 个)</summary>

- `tcl/target/apm32e1x.cfg`
- `tcl/target/apm32f003.cfg`
- `tcl/target/apm32f0xx.cfg`
- `tcl/target/apm32s1x.cfg`

</details>

<details><summary><code>HalfSweet/openocd</code> (1 个)</summary>

- `tcl/target/air001.cfg`

</details>

<details><summary><code>Icey7122/openocd</code> (10 个)</summary>

- `tcl/cpld/altera-max10.cfg`
- `tcl/cpld/xilinx-xc3s.cfg`
- `tcl/cpld/xilinx-xc4v.cfg`
- `tcl/cpld/xilinx-xc4vfx_40_60_100_140.cfg`
- `tcl/cpld/xilinx-xc5v.cfg`
- `tcl/cpld/xilinx-xc5vfx_100_130_200.cfg`
- `tcl/cpld/xilinx-xc6s.cfg`
- `tcl/cpld/xilinx-xc6v.cfg`
- `tcl/cpld/xilinx-xcu.cfg`
- `tcl/target/loongson2k300.cfg`

</details>

<details><summary><code>ImproperCatGirl/openocd</code> (4 个)</summary>

- `tcl/interface/ddmi_demo.cfg`
- `tcl/target/ch32x035.txt`
- `tcl/target/rp2350-riscv.cfg`
- `tcl/target/wch_min.cfg`

</details>

<details><summary><code>MotorolaMobilityLLC/openocd</code> (4 个)</summary>

- `tcl/chip/motorola/hsb.cfg`
- `tcl/interface/ftdi/moto_mdk_jtag.cfg`
- `tcl/interface/ftdi/moto_mdk_swd.cfg`
- `tcl/interface/ftdi/moto_mdk_swd_reset.cfg`

</details>

<details><summary><code>OlivierVanWassenhove-Dekimo/openocd</code> (4 个)</summary>

- `tcl/board/altera_arria10__aji_client.cfg`
- `tcl/board/altera_arria10_niosv__aji_client.cfg`
- `tcl/target/1986Be1T.cfg`
- `tcl/target/k1879x61R.cfg`

</details>

<details><summary><code>OpenNuvoton/OpenOCD-Nuvoton</code> (1 个)</summary>

- `tcl/interface/jtagkey.cfg`

</details>

<details><summary><code>STMicroelectronics/OpenOCD</code> (2 个)</summary>

- `tcl/target/stm32h7rx.cfg`
- `tcl/target/stm32v8x.cfg`

</details>

<details><summary><code>TexasInstruments/ti-openocd</code> (19 个)</summary>

- `tcl/board/ti_cc35x1e_launchpad.cfg`
- `tcl/board/ti_lp_em_cc2340r5.cfg`
- `tcl/board/ti_lp_em_cc2340r53.cfg`
- `tcl/board/ti_lp_em_cc2341.cfg`
- `tcl/board/ti_lp_em_cc2745P10.cfg`
- `tcl/board/ti_lp_em_cc2745R74.cfg`
- `tcl/board/ti_lp_em_cc2745r10.cfg`
- `tcl/board/ti_lp_em_cc2755P10.cfg`
- `tcl/board/ti_lp_em_cc2755P20.cfg`
- `tcl/board/ti_lp_em_cc2755R10.cfg`
- `tcl/board/ti_lp_em_cc2755R74.cfg`
- `tcl/board/ti_lp_em_cc2765R10.cfg`
- `tcl/board/ti_mspm33_launchpad.cfg`
- `tcl/target/ti_cc2341.cfg`
- `tcl/target/ti_cc23xx.cfg`
- `tcl/target/ti_cc27xx.cfg`
- `tcl/target/ti_cc35x1e.cfg`
- `tcl/target/ti_lpf3.cfg`
- `tcl/target/ti_mspm33.cfg`

</details>

<details><summary><code>aesc-silicon/elements-openocd</code> (11 个)</summary>

- `tcl/interface/jtag_tcp.cfg`
- `tcl/target/arty7_linux.cfg`
- `tcl/target/arty7_uboot.cfg`
- `tcl/target/briey.cfg`
- `tcl/target/murax.cfg`
- `tcl/target/murax_xip.cfg`
- `tcl/target/saxon.cfg`
- `tcl/target/saxon_linux.cfg`
- `tcl/target/saxon_xip.cfg`
- `tcl/target/ti_msp432p4xx.cfg`
- `tcl/target/vexriscv_sim.cfg`

</details>

<details><summary><code>analogdevicesinc/openocd</code> (67 个)</summary>

- `tcl/board/adsp21835w_ev_ezkit.cfg`
- `tcl/board/adsp21835w_ev_som.cfg`
- `tcl/board/adsp21846w_ev_ezkit.cfg`
- `tcl/board/adsp21846w_ev_som.cfg`
- `tcl/board/adspsc573_ezkit.cfg`
- `tcl/board/adspsc589_ezbrd.cfg`
- `tcl/board/adspsc589_minibrd.cfg`
- `tcl/board/adspsc5xx_ezbrd.tcl`
- `tcl/board/adspsc835w_ev_ezkit.cfg`
- `tcl/board/adspsc835w_ev_som.cfg`
- `tcl/board/adspsc846w_ev_som.cfg`
- `tcl/board/adspsc846w_mp_ezkit.cfg`
- `tcl/board/ev-sc594-som-consumer.cfg`
- `tcl/board/ev-sc594-som.cfg`
- `tcl/board/ev-sc598-som.cfg`
- `tcl/board/flash_algorithms/2183x_otp.cfg`
- `tcl/board/flash_algorithms/2184x_otp.cfg`
- `tcl/board/flash_algorithms/algoFileFinder.cfg`
- `tcl/board/flash_algorithms/is25wp02gg.cfg`
- `tcl/board/flash_algorithms/is72wvo32m8Awo256.cfg`
- `tcl/board/flash_algorithms/issi22tf16g.cfg`
- `tcl/board/flash_algorithms/issi25lp512m.cfg`
- `tcl/board/flash_algorithms/mx66u1g45g.cfg`
- `tcl/board/flash_algorithms/s26kl512s.cfg`
- `tcl/board/flash_algorithms/w25q128fv.cfg`
- `tcl/interface/adi-dbgagent.cfg`
- `tcl/interface/adi-mpdbgagent.cfg`
- `tcl/interface/ice1000.cfg`
- `tcl/interface/ice1500.cfg`
- `tcl/interface/ice2000.cfg`
- `tcl/target/adi_proc_tracker.tcl`
- `tcl/target/adsp2183x.cfg`
- `tcl/target/adsp2184x.cfg`
- `tcl/target/adspsc57x.cfg`
- `tcl/target/adspsc57x_memory_map.xml`
- `tcl/target/adspsc57x_single_SHARC.cfg`
- `tcl/target/adspsc58x_memory_map.xml`
- `tcl/target/adspsc58x_single_SHARC.cfg`
- `tcl/target/adspsc59x.cfg`
- `tcl/target/adspsc59x_a55.cfg`
- `tcl/target/adspsc59x_memory_map.xml`
- `tcl/target/adspsc59x_single_SHARC.cfg`
- `tcl/target/adspsc5xx.tcl`
- `tcl/target/adspsc83x.cfg`
- `tcl/target/adspsc84x.cfg`
- `tcl/target/adspsc84x_core0.cfg`
- `tcl/target/adspsc8xx.tcl`
- `tcl/target/aducm36x.cfg`
- `tcl/target/max32520.cfg`
- `tcl/target/max32570.cfg`
- `tcl/target/max32572.cfg`
- `tcl/target/max32655_riscv.cfg`
- `tcl/target/max32657.cfg`
- `tcl/target/max32658.cfg`
- `tcl/target/max32665.cfg`
- `tcl/target/max32665_nsrst.cfg`
- `tcl/target/max32666_nsrst.cfg`
- `tcl/target/max32680_riscv.cfg`
- `tcl/target/max32690_riscv.cfg`
- `tcl/target/max32xxx.cfg`
- `tcl/target/max78000.cfg`
- `tcl/target/max78000_nsrst.cfg`
- `tcl/target/max78000_riscv.cfg`
- `tcl/target/max78002.cfg`
- `tcl/target/max78002_riscv.cfg`
- `tcl/target/xtensa-core-adspsc83x.cfg`
- `tcl/target/xtensa-core-adspsc84x.cfg`

</details>

<details><summary><code>cjacker/wch-openocd</code> (1 个)</summary>

- `tcl/target/wch-riscv.cfg`

</details>

<details><summary><code>espressif/openocd-esp32</code> (51 个)</summary>

- `tcl/board/esp32c2-bridge.cfg`
- `tcl/board/esp32c3-bridge.cfg`
- `tcl/board/esp32c5-bridge.cfg`
- `tcl/board/esp32c5-builtin.cfg`
- `tcl/board/esp32c5-ftdi.cfg`
- `tcl/board/esp32c5-lpcore-bridge.cfg`
- `tcl/board/esp32c5-lpcore-builtin.cfg`
- `tcl/board/esp32c5-lpcore-ftdi.cfg`
- `tcl/board/esp32c6-bridge.cfg`
- `tcl/board/esp32c6-ftdi.cfg`
- `tcl/board/esp32c6-lpcore-bridge.cfg`
- `tcl/board/esp32c6-lpcore-builtin.cfg`
- `tcl/board/esp32c6-lpcore-ftdi.cfg`
- `tcl/board/esp32c61-bridge.cfg`
- `tcl/board/esp32c61-builtin.cfg`
- `tcl/board/esp32c61-ftdi.cfg`
- `tcl/board/esp32h2-bridge.cfg`
- `tcl/board/esp32h2-ftdi.cfg`
- `tcl/board/esp32h21-bridge.cfg`
- `tcl/board/esp32h21-builtin.cfg`
- `tcl/board/esp32h21-ftdi.cfg`
- `tcl/board/esp32h4-bridge.cfg`
- `tcl/board/esp32h4-builtin.cfg`
- `tcl/board/esp32h4-ftdi.cfg`
- `tcl/board/esp32p4-bridge.cfg`
- `tcl/board/esp32p4-builtin.cfg`
- `tcl/board/esp32p4-ftdi.cfg`
- `tcl/board/esp32p4-lpcore-bridge.cfg`
- `tcl/board/esp32p4-lpcore-builtin.cfg`
- `tcl/board/esp32p4-lpcore-ftdi.cfg`
- `tcl/board/esp32s31-bridge.cfg`
- `tcl/board/esp32s31-builtin.cfg`
- `tcl/board/esp32s31-ftdi.cfg`
- `tcl/board/esp32s31-lpcore-bridge.cfg`
- `tcl/board/esp32s31-lpcore-builtin.cfg`
- `tcl/board/esp32s31-lpcore-ftdi.cfg`
- `tcl/interface/esp_gpio_jtag.cfg`
- `tcl/interface/esp_gpio_swd.cfg`
- `tcl/interface/ftdi/esp_ftdi.cfg`
- `tcl/interface/jtag_esp_remote.cfg`
- `tcl/target/esp32-solo-1.cfg`
- `tcl/target/esp32c5-lpcore.cfg`
- `tcl/target/esp32c5.cfg`
- `tcl/target/esp32c6-lpcore.cfg`
- `tcl/target/esp32c61.cfg`
- `tcl/target/esp32h21.cfg`
- `tcl/target/esp32h4.cfg`
- `tcl/target/esp32p4-lpcore.cfg`
- `tcl/target/esp32p4.cfg`
- `tcl/target/esp32s31-lpcore.cfg`
- `tcl/target/esp32s31.cfg`

</details>

<details><summary><code>fatalfeel/openocd_integrated</code> (10 个)</summary>

- `tcl/target/imx6d-1gb.cfg`
- `tcl/target/imx6q-2gb.cfg`
- `tcl/target/imx7d-1gb.cfg`
- `tcl/target/imx8-ngb.cfg`
- `tcl/target/imx8.cfg`
- `tcl/target/imx8m-ngb.cfg`
- `tcl/target/nt98528-ngb.cfg`
- `tcl/target/nt98528.cfg`
- `tcl/target/rk3566-ngb.cfg`
- `tcl/target/rk3566.cfg`

</details>

<details><summary><code>foss-for-mips-arc-processors/openocd</code> (2 个)</summary>

- `tcl/cpu/arc/arcompact.tcl`
- `tcl/interface/ftdi/arc_sdp.cfg`

</details>

<details><summary><code>go2sh/aurix-openocd</code> (1 个)</summary>

- `tcl/target/renesas_rz_g2.cfg`

</details>

<details><summary><code>intel/OpenOCD</code> (1 个)</summary>

- `tcl/interface/snps_sdp.cfg`

</details>

<details><summary><code>karlp/openocd-hacks</code> (1 个)</summary>

- `tcl/interface/wlink.cfg`

</details>

<details><summary><code>kvth/openocd-swd-in-out</code> (1 个)</summary>

- `tcl/interface/c20-swd.cfg`

</details>

<details><summary><code>linux-msm/openocd</code> (1 个)</summary>

- `tcl/interface/eud.cfg`

</details>

<details><summary><code>loopj/openocd-efm32s2</code> (2 个)</summary>

- `tcl/target/efm32s2.cfg`
- `tcl/target/efm32s2_g23.cfg`

</details>

<details><summary><code>luyi1888/openocd</code> (2 个)</summary>

- `tcl/interface/dirtyjtag-cjtag.cfg`
- `tcl/target/rv1106-mcu.cfg`

</details>

<details><summary><code>mengfanyuc/openocd</code> (1 个)</summary>

- `tcl/target/ch32f2x.cfg`

</details>

<details><summary><code>nmenon/openocd</code> (3 个)</summary>

- `tcl/board/ti_am64xx_swd_native.cfg`
- `tcl/board/ti_j784s4_swd_native.cfg`
- `tcl/target/stm32wbax.cfg`

</details>

<details><summary><code>os-fpga/openocd</code> (1 个)</summary>

- `tcl/board/gemini.cfg`

</details>

<details><summary><code>padhialuo0426/openocd</code> (1 个)</summary>

- `tcl/target/ws63.cfg`

</details>

<details><summary><code>raspberrypi/openocd</code> (3 个)</summary>

- `tcl/interface/raspberrypi-swd.cfg`
- `tcl/target/rp2040-rescue.cfg`
- `tcl/target/rp2350-rescue.cfg`

</details>

<details><summary><code>riscv-collab/riscv-openocd</code> (5 个)</summary>

- `tcl/board/sifive-e31arty-cjtag.cfg`
- `tcl/board/sifive-e31arty-onboard-ftdi.cfg`
- `tcl/board/stm32mp13x_dk.cfg`
- `tcl/board/stm32mp15x_dk2.cfg`
- `tcl/target/nrf_common.cfg`

</details>

<details><summary><code>rxmnjke/openocd</code> (48 个)</summary>

- `tcl/cpld/xilinx-xcr3256.cfg`
- `tcl/target/at32a403axx.cfg`
- `tcl/target/at32a423xx.cfg`
- `tcl/target/at32f011xx.cfg`
- `tcl/target/at32f402xx.cfg`
- `tcl/target/at32f402xx_qspi.cfg`
- `tcl/target/at32f403_spim_type1_remap0.cfg`
- `tcl/target/at32f403_spim_type2_remap0.cfg`
- `tcl/target/at32f403a_407_spim_type1_remap0.cfg`
- `tcl/target/at32f403a_407_spim_type1_remap1.cfg`
- `tcl/target/at32f403a_407_spim_type2_remap0.cfg`
- `tcl/target/at32f403a_407_spim_type2_remap1.cfg`
- `tcl/target/at32f403axG.cfg`
- `tcl/target/at32f403axx.cfg`
- `tcl/target/at32f403xG.cfg`
- `tcl/target/at32f403xx.cfg`
- `tcl/target/at32f405xx.cfg`
- `tcl/target/at32f405xx_qspi.cfg`
- `tcl/target/at32f407xG.cfg`
- `tcl/target/at32f407xx.cfg`
- `tcl/target/at32f413_spim_type1_remap0.cfg`
- `tcl/target/at32f413_spim_type1_remap1.cfg`
- `tcl/target/at32f413_spim_type2_remap0.cfg`
- `tcl/target/at32f413_spim_type2_remap1.cfg`
- `tcl/target/at32f413xx.cfg`
- `tcl/target/at32f415xx.cfg`
- `tcl/target/at32f421xx.cfg`
- `tcl/target/at32f422xx.cfg`
- `tcl/target/at32f423xx.cfg`
- `tcl/target/at32f425xx.cfg`
- `tcl/target/at32f426xx.cfg`
- `tcl/target/at32f435xG.cfg`
- `tcl/target/at32f435xG_qspi.cfg`
- `tcl/target/at32f435xM.cfg`
- `tcl/target/at32f435xM_qspi.cfg`
- `tcl/target/at32f435xx.cfg`
- `tcl/target/at32f435xx_qspi.cfg`
- `tcl/target/at32f437xG.cfg`
- `tcl/target/at32f437xG_qspi.cfg`
- `tcl/target/at32f437xM.cfg`
- `tcl/target/at32f437xM_qspi.cfg`
- `tcl/target/at32f437xx.cfg`
- `tcl/target/at32f437xx_qspi.cfg`
- `tcl/target/at32f45xx.cfg`
- `tcl/target/at32l021xx.cfg`
- `tcl/target/at32m412xx.cfg`
- `tcl/target/at32m416xx.cfg`
- `tcl/target/at32wb415xx.cfg`

</details>

<details><summary><code>sony/openocd-nuttx</code> (1 个)</summary>

- `tcl/interface/ftdi/sony-ft232h-with-resistor.cfg`

</details>

<details><summary><code>stache3000/openocd-dirtyjtag</code> (1 个)</summary>

- `tcl/interface/dirtyjtag.cfg`

</details>

<details><summary><code>stacksmashing/openocd-tamarin</code> (2 个)</summary>

- `tcl/interface/faultier.cfg`
- `tcl/interface/tamarin.cfg`

</details>

<details><summary><code>sysprogs/openocd</code> (43 个)</summary>

- `tcl/board/rs14100.cfg`
- `tcl/board/st_nucleo_l476rg.cfg`
- `tcl/board/stm32mp25x_dk.cfg`
- `tcl/board/twr-k40.cfg`
- `tcl/interface/cc3200lp.cfg`
- `tcl/interface/picoprobe.cfg`
- `tcl/interface/ti-icdi-auto.cfg`
- `tcl/target/aducm3027.cfg`
- `tcl/target/aducm3029.cfg`
- `tcl/target/aducm302x.tcl`
- `tcl/target/aducm4050.cfg`
- `tcl/target/aducm4x50.tcl`
- `tcl/target/bluenrg-lp.cfg`
- `tcl/target/imx6_dual.cfg`
- `tcl/target/imx6_quad.cfg`
- `tcl/target/imxrt.cfg`
- `tcl/target/ke02.cfg`
- `tcl/target/ke04.cfg`
- `tcl/target/ke06.cfg`
- `tcl/target/kex.cfg`
- `tcl/target/kinetis_128k.cfg`
- `tcl/target/kinetis_1m.cfg`
- `tcl/target/kinetis_256k.cfg`
- `tcl/target/kinetis_32k.cfg`
- `tcl/target/kinetis_512k.cfg`
- `tcl/target/kinetis_64k.cfg`
- `tcl/target/kinetis_generic.cfg`
- `tcl/target/lpc1549.cfg`
- `tcl/target/lpc15xx.cfg`
- `tcl/target/lpc546xx.cfg`
- `tcl/target/lpc55sxx.cfg`
- `tcl/target/pic32mm.cfg`
- `tcl/target/raspberry.cfg`
- `tcl/target/raspberrypi2.cfg`
- `tcl/target/raspberrypi3.cfg`
- `tcl/target/raspberrypi3_single.cfg`
- `tcl/target/raspberrypi4.cfg`
- `tcl/target/rm57x.cfg`
- `tcl/target/rs14100.cfg`
- `tcl/target/stm32g0x_alt.cfg`
- `tcl/target/stm32g4x_alt.cfg`
- `tcl/target/swj-dp-legacy.tcl`
- `tcl/target/ti_tms570ls1224.cfg`

</details>

<details><summary><code>tihmstar/openocd_colobus</code> (1 个)</summary>

- `tcl/interface/colobus.cfg`

</details>

<details><summary><code>transcelestial/openocd</code> (1 个)</summary>

- `tcl/target/lpc55xx.cfg`

</details>

<details><summary><code>ut2or1/openocd</code> (9 个)</summary>

- `tcl/board/arty_s7.cfg`
- `tcl/board/iar_lpc1768.cfg`
- `tcl/cpld/xilinx-xc7.cfg`
- `tcl/cpld/xilinx-xc7v.cfg`
- `tcl/cpld/xilinx-xc7vh580t.cfg`
- `tcl/cpld/xilinx-xc7vh870t.cfg`
- `tcl/fpga/xilinx-dna.cfg`
- `tcl/fpga/xilinx-xc3s.cfg`
- `tcl/target/zynq_7000.cfg`

</details>

<details><summary><code>vllogic/openocd_cmsis-dap_v2</code> (10 个)</summary>

- `tcl/board/st_nucleo_l5.cfg`
- `tcl/interface/atlink.cfg`
- `tcl/interface/atlink_dap_v2.cfg`
- `tcl/interface/cmsis-dap_v2_aic8800.cfg`
- `tcl/interface/cmsis-dap_v2_aic8800m40.cfg`
- `tcl/interface/cmsis-dap_v2_aic8800mc.cfg`
- `tcl/target/aic8800.cfg`
- `tcl/target/aic8800m40.cfg`
- `tcl/target/aic8800mc.cfg`
- `tcl/target/py32f0xx.cfg`

</details>

<details><summary><code>xsession/openocd</code> (8 个)</summary>

- `tcl/interface/mchp-ri4.cfg`
- `tcl/target/#U043a1879x#U04311#U044f.cfg`
- `tcl/target/1986#U0432#U04351#U0442.cfg`
- `tcl/target/dspic33-ri4.cfg`
- `tcl/target/mchp-renode.cfg`
- `tcl/target/mchp-ri4.cfg`
- `tcl/target/pic18-ri4.cfg`
- `tcl/target/pic32mz-ri4.cfg`

</details>

<details><summary><code>zephyrproject-rtos/openocd</code> (11 个)</summary>

- `tcl/board/nds32_xc5.cfg`
- `tcl/board/snps_hsdk_smp.cfg`
- `tcl/interface/nds32-aice.cfg`
- `tcl/target/nds32v2.cfg`
- `tcl/target/nds32v3.cfg`
- `tcl/target/nds32v3m.cfg`
- `tcl/target/rp2040-core0.cfg`
- `tcl/target/rv32m1_ri5cy.cfg`
- `tcl/target/rv32m1_zero_riscy.cfg`
- `tcl/target/snps_hsdk_smp.cfg`
- `tcl/target/vd_xtensa_jtag.cfg`

</details>

<details><summary><code>zuyih/openocd</code> (28 个)</summary>

- `tcl/board/art_pi2.cfg`
- `tcl/board/atk_cnn647b.cfg`
- `tcl/board/omap2420_h4.cfg`
- `tcl/board/st_nucleo_c5.cfg`
- `tcl/board/st_nucleo_h5.cfg`
- `tcl/board/ti_am625_swd_native.cfg`
- `tcl/board/ti_am62a7_swd_native.cfg`
- `tcl/board/ti_am62p_swd_native.cfg`
- `tcl/board/ti_beagleboard.cfg`
- `tcl/board/ti_beagleboard_xm.cfg`
- `tcl/board/ti_beaglebone-base.cfg`
- `tcl/board/ti_beaglebone.cfg`
- `tcl/board/ti_beaglebone_black.cfg`
- `tcl/board/ti_j721e_swd_native.cfg`
- `tcl/board/ti_j722s_swd_native.cfg`
- `tcl/gdb_helper.tcl`
- `tcl/interface/ch347.cfg`
- `tcl/interface/tas_client.cfg`
- `tcl/target/ch32f1x.cfg`
- `tcl/target/ch579.cfg`
- `tcl/target/infineon/aurix_program.tcl`
- `tcl/target/stm32c5x.cfg`
- `tcl/target/stm32h5x.cfg`
- `tcl/target/stm32l4plusx.cfg`
- `tcl/target/stm32wb0x.cfg`
- `tcl/target/stm32wl3x.cfg`
- `tcl/target/stm32wl4x.cfg`
- `tcl/target/xmc7xxx.cfg`

</details>

## 第二层 C 源码（需打补丁）

文件数：**127**

| 来源仓库 | SPDX | 文件数 |
|---|---|---:|
| [`zephyrproject-rtos/openocd`](https://github.com/zephyrproject-rtos/openocd) | NOASSERTION(22) | 22 |
| [`foss-for-mips-arc-processors/openocd`](https://github.com/foss-for-mips-arc-processors/openocd) | GPL-2.0(13) | 13 |
| [`andestech/nds-openocd`](https://github.com/andestech/nds-openocd) | NOASSERTION(10) | 10 |
| [`intel/OpenOCD`](https://github.com/intel/OpenOCD) | GPL-2.0(8) | 8 |
| [`xsession/openocd`](https://github.com/xsession/openocd) | NOASSERTION(8) | 8 |
| [`kevinmehall/openOCD`](https://github.com/kevinmehall/openOCD) | GPL-2.0(7) | 7 |
| [`Icey7122/openocd`](https://github.com/Icey7122/openocd) | NOASSERTION(7) | 7 |
| [`linux-msm/openocd`](https://github.com/linux-msm/openocd) | NOASSERTION(6) | 6 |
| [`analogdevicesinc/openocd`](https://github.com/analogdevicesinc/openocd) | NOASSERTION(5) | 5 |
| [`AnlogicInfo/al_openocd`](https://github.com/AnlogicInfo/al_openocd) | NOASSERTION(5) | 5 |
| [`aesc-silicon/elements-openocd`](https://github.com/aesc-silicon/elements-openocd) | NOASSERTION(4) | 4 |
| [`Seneral/riscv-openocd-wch`](https://github.com/Seneral/riscv-openocd-wch) | NOASSERTION(4) | 4 |
| [`espressif/openocd-esp32`](https://github.com/espressif/openocd-esp32) | NOASSERTION(3) | 3 |
| [`hackpascal/openocd`](https://github.com/hackpascal/openocd) | NOASSERTION(3) | 3 |
| [`sysprogs/openocd`](https://github.com/sysprogs/openocd) | NOASSERTION(3) | 3 |
| [`ImproperCatGirl/openocd`](https://github.com/ImproperCatGirl/openocd) | NOASSERTION(2) | 2 |
| [`fxsheep/openocd_wchlink-rv`](https://github.com/fxsheep/openocd_wchlink-rv) | NOASSERTION(2) | 2 |
| [`esden/openocd`](https://github.com/esden/openocd) | GPL-2.0(2) | 2 |
| [`yottatsa/openocd`](https://github.com/yottatsa/openocd) | NOASSERTION(2) | 2 |
| [`walmis/openocd-blackmagic`](https://github.com/walmis/openocd-blackmagic) | GPL-2.0(1) | 1 |
| [`stacksmashing/openocd`](https://github.com/stacksmashing/openocd) | GPL-2.0(1) | 1 |
| [`meriac/openocd`](https://github.com/meriac/openocd) | NOASSERTION(1) | 1 |
| [`dynm/openocd-starbleed`](https://github.com/dynm/openocd-starbleed) | GPL-2.0(1) | 1 |
| [`zuyih/openocd`](https://github.com/zuyih/openocd) | NOASSERTION(1) | 1 |
| [`tihmstar/openocd_colobus`](https://github.com/tihmstar/openocd_colobus) | NOASSERTION(1) | 1 |
| [`stache3000/openocd-dirtyjtag`](https://github.com/stache3000/openocd-dirtyjtag) | NOASSERTION(1) | 1 |
| [`intel/aji_openocd`](https://github.com/intel/aji_openocd) | NOASSERTION(1) | 1 |
| [`stacksmashing/openocd-tamarin`](https://github.com/stacksmashing/openocd-tamarin) | NOASSERTION(1) | 1 |
| [`riscv-collab/riscv-openocd`](https://github.com/riscv-collab/riscv-openocd) | NOASSERTION(1) | 1 |
| [`mabl/openocd_chibios`](https://github.com/mabl/openocd_chibios) | GPL-2.0(1) | 1 |

### ⚠️ 需人工审计（93 个文件无许可证信息）

这些文件的来源仓库在 GitHub 上未解析出许可证，商用前必须逐个查看文件头部的版权声明。

<details><summary><code>AnlogicInfo/al_openocd</code> (5 个)</summary>

- `src/jtag/drivers/al_link.c`
- `src/jtag/drivers/al_link_cyusb.c`
- `src/jtag/drivers/al_link_cyusb.h`
- `src/server/rbb_server.c`
- `src/server/rbb_server.h`

</details>

<details><summary><code>Icey7122/openocd</code> (7 个)</summary>

- `src/target/loongarch.c`
- `src/target/loongarch.h`
- `src/target/loongarch_ejtag.c`
- `src/target/loongarch_ejtag.h`
- `src/target/loongarch_modules.h`
- `src/target/loongarch_pracc.c`
- `src/target/loongarch_pracc.h`

</details>

<details><summary><code>ImproperCatGirl/openocd</code> (2 个)</summary>

- `src/jtag/drivers/ddmi_demo.c`
- `src/jtag/drivers/ftdi_rvswd.c`

</details>

<details><summary><code>Seneral/riscv-openocd-wch</code> (4 个)</summary>

- `src/jtag/drivers/wlinke.c`
- `src/target/wch_riscv-013.c`
- `src/target/wch_riscv.c`
- `src/target/wch_riscv.h`

</details>

<details><summary><code>aesc-silicon/elements-openocd</code> (4 个)</summary>

- `src/jtag/drivers/jtag_tcp.c`
- `src/target/vexriscv-csrs.h`
- `src/target/vexriscv.c`
- `src/target/vexriscv.h`

</details>

<details><summary><code>analogdevicesinc/openocd</code> (5 个)</summary>

- `src/jtag/drivers/adi_dbg_agent.c`
- `src/jtag/drivers/ice1000.c`
- `src/jtag/drivers/ice1500.c`
- `src/jtag/drivers/usbmux.c`
- `src/jtag/drivers/usbmux.h`

</details>

<details><summary><code>andestech/nds-openocd</code> (10 个)</summary>

- `src/target/jsmn.h`
- `src/target/nds_vtarget.c`
- `src/target/nds_vtarget.h`
- `src/target/nds_vtarget_cmd.c`
- `src/target/nds_vtarget_common.h`
- `src/target/ndsv5_ace.c`
- `src/target/ndsv5_ace.h`
- `src/target/ndsv5_burner_server.c`
- `src/target/ndsv5_cmd.c`
- `src/target/ndsv5_profiling.c`

</details>

<details><summary><code>espressif/openocd-esp32</code> (3 个)</summary>

- `src/jtag/drivers/esp_gpio.c`
- `src/jtag/drivers/esp_gpio.h`
- `src/jtag/drivers/jtag_esp_remote.c`

</details>

<details><summary><code>fxsheep/openocd_wchlink-rv</code> (2 个)</summary>

- `src/jtag/drivers/wlink.c`
- `src/jtag/drivers/wlink.h`

</details>

<details><summary><code>hackpascal/openocd</code> (3 个)</summary>

- `src/jtag/drivers/mpsse-d2xx.c`
- `src/jtag/drivers/mpsse-libusb.c`
- `src/jtag/drivers/mpsse-private.h`

</details>

<details><summary><code>intel/aji_openocd</code> (1 个)</summary>

- `src/jtag/drivers/jtag_usb_common.h`

</details>

<details><summary><code>linux-msm/openocd</code> (6 个)</summary>

- `src/target/aarch64_coproc_reg.c`
- `src/target/aarch64_system_registers.h`
- `src/target/aarch64_system_registers_defs.h`
- `src/target/hexagon.c`
- `src/target/hexagon.h`
- `src/target/stm8.h`

</details>

<details><summary><code>meriac/openocd</code> (1 个)</summary>

- `src/jtag/drivers/ch347_jtag.c`

</details>

<details><summary><code>riscv-collab/riscv-openocd</code> (1 个)</summary>

- `src/jtag/drivers/xlnx-pcie-xvc.c`

</details>

<details><summary><code>stache3000/openocd-dirtyjtag</code> (1 个)</summary>

- `src/jtag/drivers/dirtyjtag.c`

</details>

<details><summary><code>stacksmashing/openocd-tamarin</code> (1 个)</summary>

- `src/jtag/drivers/tamarin.c`

</details>

<details><summary><code>sysprogs/openocd</code> (3 个)</summary>

- `src/jtag/drivers/stlink_usb_hla_multicore.c`
- `src/target/hla_target_hla_multicore.c`
- `src/target/stm8_hla_multicore.c`

</details>

<details><summary><code>tihmstar/openocd_colobus</code> (1 个)</summary>

- `src/jtag/drivers/colobus.c`

</details>

<details><summary><code>xsession/openocd</code> (8 个)</summary>

- `src/target/c28x.c`
- `src/target/c28x.h`
- `src/target/mchp_ri4_bridge.c`
- `src/target/mchp_ri4_bridge.h`
- `src/target/mchp_ri4_native.c`
- `src/target/mchp_ri4_native.h`
- `src/target/tms320.c`
- `src/target/tms320.h`

</details>

<details><summary><code>yottatsa/openocd</code> (2 个)</summary>

- `src/target/vortex86.c`
- `src/target/vortex86.h`

</details>

<details><summary><code>zephyrproject-rtos/openocd</code> (22 个)</summary>

- `src/target/nds32.c`
- `src/target/nds32.h`
- `src/target/nds32_aice.c`
- `src/target/nds32_aice.h`
- `src/target/nds32_cmd.c`
- `src/target/nds32_cmd.h`
- `src/target/nds32_disassembler.c`
- `src/target/nds32_disassembler.h`
- `src/target/nds32_edm.h`
- `src/target/nds32_insn.h`
- `src/target/nds32_reg.c`
- `src/target/nds32_reg.h`
- `src/target/nds32_tlb.c`
- `src/target/nds32_tlb.h`
- `src/target/nds32_v2.c`
- `src/target/nds32_v2.h`
- `src/target/nds32_v3.c`
- `src/target/nds32_v3.h`
- `src/target/nds32_v3_common.c`
- `src/target/nds32_v3_common.h`
- `src/target/nds32_v3m.c`
- `src/target/nds32_v3m.h`

</details>

<details><summary><code>zuyih/openocd</code> (1 个)</summary>

- `src/jtag/drivers/cmsis_dap_wch.c`

</details>

# 第三方许可证清单

> 由 `tools/gen_licenses.py` 生成。**本仓库汇集了他人的 OpenOCD fork，整体许可不统一**，任何商用前请先读这一页。

## 总览

| SPDX | 文件数 |
|---|---:|
| NOASSERTION | 615 |
| GPL-2.0 | 123 |
| UNRESOLVED | 24 |
| GPL-2.0-or-later | 5 |

**639 个文件（83%）没有可用的许可证信息**，必须逐个审计文件头部的版权声明后才能商用。

> 已知事实：OpenOCD 上游是 GPL-2.0-or-later，大多数 fork 继承该许可，所以实务上大概率都是 GPL。但 `NOASSERTION` 只表示「GitHub 没能解析出来」，**不等于宽松许可** —— 在少数 fork 里它对应的是专有许可。逐文件清单见 `manifest/licenses.csv` 与下方折叠区。

## tcl/ 配置（随树直接可用）

文件数：**702**

| 来源仓库 | SPDX | 文件数 |
|---|---|---:|
| [`xsession/openocd`](https://github.com/xsession/openocd) | NOASSERTION(226) | 226 |
| [`analogdevicesinc/openocd`](https://github.com/analogdevicesinc/openocd) | NOASSERTION(58), UNRESOLVED(10) | 68 |
| [`espressif/openocd-esp32`](https://github.com/espressif/openocd-esp32) | NOASSERTION(47), UNRESOLVED(1) | 48 |
| [`rxmnjke/openocd`](https://github.com/rxmnjke/openocd) | NOASSERTION(47) | 47 |
| [`sysprogs/openocd`](https://github.com/sysprogs/openocd) | NOASSERTION(43) | 43 |
| [`foss-for-mips-arc-processors/openocd`](https://github.com/foss-for-mips-arc-processors/openocd) | GPL-2.0(33), UNRESOLVED(2) | 35 |
| [`intel/OpenOCD`](https://github.com/intel/OpenOCD) | GPL-2.0(29) | 29 |
| [`TexasInstruments/ti-openocd`](https://github.com/TexasInstruments/ti-openocd) | NOASSERTION(19) | 19 |
| [`zuyih/openocd`](https://github.com/zuyih/openocd) | NOASSERTION(16), UNRESOLVED(2) | 18 |
| [`aesc-silicon/elements-openocd`](https://github.com/aesc-silicon/elements-openocd) | NOASSERTION(15) | 15 |
| [`ciniml/openocd`](https://github.com/ciniml/openocd) | GPL-2.0(13) | 13 |
| [`zephyrproject-rtos/openocd`](https://github.com/zephyrproject-rtos/openocd) | NOASSERTION(10) | 10 |
| [`vllogic/openocd_cmsis-dap_v2`](https://github.com/vllogic/openocd_cmsis-dap_v2) | NOASSERTION(10) | 10 |
| [`fatalfeel/openocd_integrated`](https://github.com/fatalfeel/openocd_integrated) | NOASSERTION(10) | 10 |
| [`hackpascal/openocd`](https://github.com/hackpascal/openocd) | NOASSERTION(10) | 10 |
| [`Icey7122/openocd`](https://github.com/Icey7122/openocd) | NOASSERTION(9) | 9 |
| [`ut2or1/openocd`](https://github.com/ut2or1/openocd) | NOASSERTION(7), UNRESOLVED(1) | 8 |
| [`MotorolaMobilityLLC/openocd`](https://github.com/MotorolaMobilityLLC/openocd) | GPL-2.0(4), UNRESOLVED(4) | 8 |
| [`OpenNuvoton/OpenOCD-Nuvoton`](https://github.com/OpenNuvoton/OpenOCD-Nuvoton) | GPL-2.0(8) | 8 |
| [`esden/openocd`](https://github.com/esden/openocd) | GPL-2.0(6) | 6 |
| [`walmis/openocd-blackmagic`](https://github.com/walmis/openocd-blackmagic) | GPL-2.0(5) | 5 |
| [`riscv-collab/riscv-openocd`](https://github.com/riscv-collab/riscv-openocd) | NOASSERTION(5) | 5 |
| [`DCVostok/openocd-k1921vk`](https://github.com/DCVostok/openocd-k1921vk) | NOASSERTION(4), UNRESOLVED(1) | 5 |
| [`AnlogicInfo/al_openocd`](https://github.com/AnlogicInfo/al_openocd) | NOASSERTION(5) | 5 |
| [`David-lau/openocd-geehy`](https://github.com/David-lau/openocd-geehy) | NOASSERTION(4) | 4 |
| [`sony/openocd-nuttx`](https://github.com/sony/openocd-nuttx) | GPL-2.0(2), UNRESOLVED(1) | 3 |
| [`hikob/openocd`](https://github.com/hikob/openocd) | GPL-2.0(3) | 3 |
| [`raspberrypi/openocd`](https://github.com/raspberrypi/openocd) | NOASSERTION(3) | 3 |
| [`luyi1888/openocd`](https://github.com/luyi1888/openocd) | NOASSERTION(2) | 2 |
| [`linux-msm/openocd`](https://github.com/linux-msm/openocd) | NOASSERTION(2) | 2 |
| [`kevinmehall/openOCD`](https://github.com/kevinmehall/openOCD) | GPL-2.0(2) | 2 |
| [`Lichee-Pi/LicheeTang_openocd`](https://github.com/Lichee-Pi/LicheeTang_openocd) | GPL-2.0(2) | 2 |
| [`loopj/openocd-efm32s2`](https://github.com/loopj/openocd-efm32s2) | NOASSERTION(2) | 2 |
| [`STMicroelectronics/OpenOCD`](https://github.com/STMicroelectronics/OpenOCD) | NOASSERTION(2) | 2 |
| [`os-fpga/openocd`](https://github.com/os-fpga/openocd) | NOASSERTION(1) | 1 |
| [`snowcap-electronics/OpenOCD`](https://github.com/snowcap-electronics/OpenOCD) | GPL-2.0(1) | 1 |
| [`Blinkinlabs/OpenOCD`](https://github.com/Blinkinlabs/OpenOCD) | GPL-2.0(1) | 1 |
| [`kvth/openocd-swd-in-out`](https://github.com/kvth/openocd-swd-in-out) | NOASSERTION(1) | 1 |
| [`stache3000/openocd-dirtyjtag`](https://github.com/stache3000/openocd-dirtyjtag) | NOASSERTION(1) | 1 |
| [`corecode/openocd-swd`](https://github.com/corecode/openocd-swd) | GPL-2.0(1) | 1 |
| [`tokuden/openocd-win-ftd2xx`](https://github.com/tokuden/openocd-win-ftd2xx) | NOASSERTION(1) | 1 |
| [`matrix-io/matrix-creator-openocd`](https://github.com/matrix-io/matrix-creator-openocd) | GPL-2.0(1) | 1 |
| [`HalfSweet/openocd`](https://github.com/HalfSweet/openocd) | NOASSERTION(1) | 1 |
| [`mengfanyuc/openocd`](https://github.com/mengfanyuc/openocd) | NOASSERTION(1) | 1 |
| [`sysprogs/esp8266-openocd`](https://github.com/sysprogs/esp8266-openocd) | GPL-2.0(1) | 1 |
| [`transcelestial/openocd`](https://github.com/transcelestial/openocd) | NOASSERTION(1) | 1 |
| [`pebble/openocd`](https://github.com/pebble/openocd) | GPL-2.0(1) | 1 |
| [`go2sh/aurix-openocd`](https://github.com/go2sh/aurix-openocd) | NOASSERTION(1) | 1 |
| [`ImproperCatGirl/openocd`](https://github.com/ImproperCatGirl/openocd) | NOASSERTION(1) | 1 |
| [`nmenon/openocd`](https://github.com/nmenon/openocd) | NOASSERTION(1) | 1 |
| [`padhialuo0426/openocd`](https://github.com/padhialuo0426/openocd) | NOASSERTION(1) | 1 |

### ⚠️ 需人工审计（589 个文件无许可证信息）

这些文件的来源仓库在 GitHub 上未解析出许可证，商用前必须逐个查看文件头部的版权声明。

<details><summary><code>AnlogicInfo/al_openocd</code> (5 个)</summary>

- `tcl/target/anlogic/al_fpga.cfg`
- `tcl/target/anlogic/init.cfg`
- `tcl/target/anlogic/onecable.cfg`
- `tcl/target/anlogic/sf1.cfg`
- `tcl/target/anlogic/softcore_direct.cfg`

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

<details><summary><code>Icey7122/openocd</code> (9 个)</summary>

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

<details><summary><code>ImproperCatGirl/openocd</code> (1 个)</summary>

- `tcl/target/rp2350-riscv.cfg`

</details>

<details><summary><code>MotorolaMobilityLLC/openocd</code> (4 个)</summary>

- `tcl/chip/motorola/hsb.cfg`
- `tcl/interface/ftdi/moto_mdk_jtag.cfg`
- `tcl/interface/ftdi/moto_mdk_swd.cfg`
- `tcl/interface/ftdi/moto_mdk_swd_reset.cfg`

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

<details><summary><code>aesc-silicon/elements-openocd</code> (15 个)</summary>

- `tcl/interface/ftdi/alinx.cfg`
- `tcl/interface/ftdi/c232hm_ddhsl_0.cfg`
- `tcl/interface/ftdi/digilent-nexys4-ddr.cfg`
- `tcl/interface/ftdi/ft2232h_breakout.cfg`
- `tcl/interface/ftdi/phytec-dh-006.cfg`
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

<details><summary><code>analogdevicesinc/openocd</code> (68 个)</summary>

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
- `tcl/target/adspsc58x.cfg`
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

<details><summary><code>espressif/openocd-esp32</code> (48 个)</summary>

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
- `tcl/interface/ftdi/esp_ftdi.cfg`
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

<details><summary><code>hackpascal/openocd</code> (10 个)</summary>

- `tcl/target/mediatek/memc.tcl`
- `tcl/target/mediatek/mmio.tcl`
- `tcl/target/mediatek/mt7620.cfg`
- `tcl/target/mediatek/mt7621.cfg`
- `tcl/target/mediatek/mt7622.cfg`
- `tcl/target/mediatek/mt7628.cfg`
- `tcl/target/mediatek/mt7629.cfg`
- `tcl/target/mediatek/mt7981.cfg`
- `tcl/target/mediatek/mt7986.cfg`
- `tcl/target/mediatek/mt7988.cfg`

</details>

<details><summary><code>kvth/openocd-swd-in-out</code> (1 个)</summary>

- `tcl/interface/c20-swd.cfg`

</details>

<details><summary><code>linux-msm/openocd</code> (2 个)</summary>

- `tcl/interface/eud.cfg`
- `tcl/target/qualcomm/qcom.cfg`

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

<details><summary><code>nmenon/openocd</code> (1 个)</summary>

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
- `tcl/board/stm32mp15x_dk2.cfg`
- `tcl/interface/ftdi/arty-onboard-ftdi.cfg`
- `tcl/interface/ftdi/digilent-hs2-cjtag.cfg`

</details>

<details><summary><code>rxmnjke/openocd</code> (47 个)</summary>

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

<details><summary><code>sysprogs/openocd</code> (43 个)</summary>

- `tcl/board/rs14100.cfg`
- `tcl/board/st_nucleo_l476rg.cfg`
- `tcl/board/stm32mp25x_dk.cfg`
- `tcl/board/twr-k40.cfg`
- `tcl/interface/cc3200lp.cfg`
- `tcl/interface/ftdi/olimex-arm-usb-ocd-h-swd.cfg`
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

<details><summary><code>tokuden/openocd-win-ftd2xx</code> (1 个)</summary>

- `tcl/interface/ftdi/np1167.cfg`

</details>

<details><summary><code>transcelestial/openocd</code> (1 个)</summary>

- `tcl/target/lpc55xx.cfg`

</details>

<details><summary><code>ut2or1/openocd</code> (8 个)</summary>

- `tcl/board/arty_s7.cfg`
- `tcl/board/iar_lpc1768.cfg`
- `tcl/cpld/xilinx-xc7.cfg`
- `tcl/cpld/xilinx-xc7v.cfg`
- `tcl/cpld/xilinx-xc7vh580t.cfg`
- `tcl/cpld/xilinx-xc7vh870t.cfg`
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

<details><summary><code>xsession/openocd</code> (226 个)</summary>

- `tcl/board/ti/cc35x1e-launchpad.cfg`
- `tcl/board/ti/mspm0c1103-cmsis-dap.cfg`
- `tcl/board/ti/mspm0c1103-xds110.cfg`
- `tcl/board/ti/tms320f280049-xds110.cfg`
- `tcl/board/ti/tms320f28069-xds110.cfg`
- `tcl/board/ti/tms320f28m35x-xds110.cfg`
- `tcl/interface/ftdi/xds100.cfg`
- `tcl/interface/mchp-ri4.cfg`
- `tcl/interface/microchip/icd4-cmsis-dap.cfg`
- `tcl/interface/microchip/pickit4-cmsis-dap.cfg`
- `tcl/interface/ti/msp-fet.cfg`
- `tcl/interface/ti/unsupported-closed.cfg`
- `tcl/interface/ti/xds100.cfg`
- `tcl/interface/ti/xds200.cfg`
- `tcl/interface/ti/xds560.cfg`
- `tcl/target/dspic33-ri4.cfg`
- `tcl/target/mchp-renode.cfg`
- `tcl/target/mchp-ri4.cfg`
- `tcl/target/pic18-ri4.cfg`
- `tcl/target/pic32mz-ri4.cfg`
- `tcl/target/ti/c2000-icepick-scan.cfg`
- `tcl/target/ti/cc35x1e.cfg`
- `tcl/target/ti/mspm0c1103.cfg`
- `tcl/target/ti/tms320-generic-scan.cfg`
- `tcl/target/ti/tms320/family/c55xx.cfg`
- `tcl/target/ti/tms320/family/c620x.cfg`
- `tcl/target/ti/tms320/family/c621x.cfg`
- `tcl/target/ti/tms320/family/c646x.cfg`
- `tcl/target/ti/tms320/family/c64xp.cfg`
- `tcl/target/ti/tms320/family/c64xx.cfg`
- `tcl/target/ti/tms320/family/c66xx.cfg`
- `tcl/target/ti/tms320/family/c670x.cfg`
- `tcl/target/ti/tms320/family/c671x.cfg`
- `tcl/target/ti/tms320/family/c672x.cfg`
- `tcl/target/ti/tms320/family/c674x.cfg`
- `tcl/target/ti/tms320/family/c71x.cfg`
- `tcl/target/ti/tms320/family/c71x_v2.cfg`
- `tcl/target/ti/tms320/family/c75x.cfg`
- `tcl/target/ti/tms320/generated/66ak2e05.cfg`
- `tcl/target/ti/tms320/generated/66ak2g01.cfg`
- `tcl/target/ti/tms320/generated/66ak2g02.cfg`
- `tcl/target/ti/tms320/generated/66ak2g12.cfg`
- `tcl/target/ti/tms320/generated/66ak2h06.cfg`
- `tcl/target/ti/tms320/generated/66ak2h12.cfg`
- `tcl/target/ti/tms320/generated/66ak2h14.cfg`
- `tcl/target/ti/tms320/generated/66ak2l06.cfg`
- `tcl/target/ti/tms320/generated/am273x.cfg`
- `tcl/target/ti/tms320/generated/am5706.cfg`
- `tcl/target/ti/tms320/generated/am5708.cfg`
- `tcl/target/ti/tms320/generated/am5716.cfg`
- `tcl/target/ti/tms320/generated/am5718.cfg`
- `tcl/target/ti/tms320/generated/am5726.cfg`
- `tcl/target/ti/tms320/generated/am5726_reva.cfg`
- `tcl/target/ti/tms320/generated/am5728.cfg`
- `tcl/target/ti/tms320/generated/am5728_reva.cfg`
- `tcl/target/ti/tms320/generated/am5729.cfg`
- `tcl/target/ti/tms320/generated/am5746.cfg`
- `tcl/target/ti/tms320/generated/am5748.cfg`
- `tcl/target/ti/tms320/generated/am5749.cfg`
- `tcl/target/ti/tms320/generated/am5766.cfg`
- `tcl/target/ti/tms320/generated/am5768.cfg`
- `tcl/target/ti/tms320/generated/awr1642.cfg`
- `tcl/target/ti/tms320/generated/awr1843.cfg`
- `tcl/target/ti/tms320/generated/awr2943.cfg`
- `tcl/target/ti/tms320/generated/awr2944.cfg`
- `tcl/target/ti/tms320/generated/awr6843.cfg`
- `tcl/target/ti/tms320/generated/awr6843aop.cfg`
- `tcl/target/ti/tms320/generated/f28m35e20b1.cfg`
- `tcl/target/ti/tms320/generated/f28m35h22c1.cfg`
- `tcl/target/ti/tms320/generated/f28m35h52c1.cfg`
- `tcl/target/ti/tms320/generated/f28m35m20b1.cfg`
- `tcl/target/ti/tms320/generated/f28m35m22c1.cfg`
- `tcl/target/ti/tms320/generated/f28m35m52c1.cfg`
- `tcl/target/ti/tms320/generated/f28m36h33b2.cfg`
- `tcl/target/ti/tms320/generated/f28m36h33c2.cfg`
- `tcl/target/ti/tms320/generated/f28m36h53b2.cfg`
- `tcl/target/ti/tms320/generated/f28m36h53c2.cfg`
- `tcl/target/ti/tms320/generated/f28m36p53c2.cfg`
- `tcl/target/ti/tms320/generated/f28m36p63c2.cfg`
- `tcl/target/ti/tms320/generated/iwr1642.cfg`
- `tcl/target/ti/tms320/generated/iwr1843.cfg`
- `tcl/target/ti/tms320/generated/iwr1843aop.cfg`
- `tcl/target/ti/tms320/generated/iwr6843.cfg`
- `tcl/target/ti/tms320/generated/iwr6843aop.cfg`
- `tcl/target/ti/tms320/generated/tci6630k2l.cfg`
- `tcl/target/ti/tms320/generated/tci6634k2k.cfg`
- `tcl/target/ti/tms320/generated/tci6636k2h.cfg`
- `tcl/target/ti/tms320/generated/tci6638k2k.cfg`
- `tcl/target/ti/tms320/generated/tms320c2801.cfg`
- `tcl/target/ti/tms320/generated/tms320c2802.cfg`
- `tcl/target/ti/tms320/generated/tms320c2810.cfg`
- `tcl/target/ti/tms320/generated/tms320c2811.cfg`
- `tcl/target/ti/tms320/generated/tms320c2812.cfg`
- `tcl/target/ti/tms320/generated/tms320c28341.cfg`
- `tcl/target/ti/tms320/generated/tms320c28342.cfg`
- `tcl/target/ti/tms320/generated/tms320c28343.cfg`
- `tcl/target/ti/tms320/generated/tms320c28344.cfg`
- `tcl/target/ti/tms320/generated/tms320c28345.cfg`
- `tcl/target/ti/tms320/generated/tms320c28346.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800132.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800133.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800135.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800137.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800153.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800155.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800155_q1.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800157.cfg`
- `tcl/target/ti/tms320/generated/tms320f2800157_q1.cfg`
- `tcl/target/ti/tms320/generated/tms320f280021.cfg`
- `tcl/target/ti/tms320/generated/tms320f280022.cfg`
- `tcl/target/ti/tms320/generated/tms320f280023.cfg`
- `tcl/target/ti/tms320/generated/tms320f280023c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280024.cfg`
- `tcl/target/ti/tms320/generated/tms320f280024c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280025.cfg`
- `tcl/target/ti/tms320/generated/tms320f280025c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280033.cfg`
- `tcl/target/ti/tms320/generated/tms320f280034.cfg`
- `tcl/target/ti/tms320/generated/tms320f280036.cfg`
- `tcl/target/ti/tms320/generated/tms320f280036c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280037.cfg`
- `tcl/target/ti/tms320/generated/tms320f280037c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280038.cfg`
- `tcl/target/ti/tms320/generated/tms320f280038c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280039.cfg`
- `tcl/target/ti/tms320/generated/tms320f280039c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280040.cfg`
- `tcl/target/ti/tms320/generated/tms320f280040c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280041.cfg`
- `tcl/target/ti/tms320/generated/tms320f280041c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280045.cfg`
- `tcl/target/ti/tms320/generated/tms320f280048.cfg`
- `tcl/target/ti/tms320/generated/tms320f280048c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280049.cfg`
- `tcl/target/ti/tms320/generated/tms320f280049c.cfg`
- `tcl/target/ti/tms320/generated/tms320f280049m.cfg`
- `tcl/target/ti/tms320/generated/tms320f2801.cfg`
- `tcl/target/ti/tms320/generated/tms320f28015.cfg`
- `tcl/target/ti/tms320/generated/tms320f28016.cfg`
- `tcl/target/ti/tms320/generated/tms320f2802.cfg`
- `tcl/target/ti/tms320/generated/tms320f28020.cfg`
- `tcl/target/ti/tms320/generated/tms320f280200.cfg`
- `tcl/target/ti/tms320/generated/tms320f28021.cfg`
- `tcl/target/ti/tms320/generated/tms320f28022.cfg`
- `tcl/target/ti/tms320/generated/tms320f280220.cfg`
- `tcl/target/ti/tms320/generated/tms320f28023.cfg`
- `tcl/target/ti/tms320/generated/tms320f280230.cfg`
- `tcl/target/ti/tms320/generated/tms320f28026.cfg`
- `tcl/target/ti/tms320/generated/tms320f280260.cfg`
- `tcl/target/ti/tms320/generated/tms320f28027.cfg`
- `tcl/target/ti/tms320/generated/tms320f280270.cfg`
- `tcl/target/ti/tms320/generated/tms320f28030.cfg`
- `tcl/target/ti/tms320/generated/tms320f28031.cfg`
- `tcl/target/ti/tms320/generated/tms320f28032.cfg`
- `tcl/target/ti/tms320/generated/tms320f28033.cfg`
- `tcl/target/ti/tms320/generated/tms320f28034.cfg`
- `tcl/target/ti/tms320/generated/tms320f28035.cfg`
- `tcl/target/ti/tms320/generated/tms320f28044.cfg`
- `tcl/target/ti/tms320/generated/tms320f28050.cfg`
- `tcl/target/ti/tms320/generated/tms320f28051.cfg`
- `tcl/target/ti/tms320/generated/tms320f28052.cfg`
- `tcl/target/ti/tms320/generated/tms320f28052f.cfg`
- `tcl/target/ti/tms320/generated/tms320f28052m.cfg`
- `tcl/target/ti/tms320/generated/tms320f28053.cfg`
- `tcl/target/ti/tms320/generated/tms320f28054.cfg`
- `tcl/target/ti/tms320/generated/tms320f28054f.cfg`
- `tcl/target/ti/tms320/generated/tms320f28054m.cfg`
- `tcl/target/ti/tms320/generated/tms320f28055.cfg`
- `tcl/target/ti/tms320/generated/tms320f2806.cfg`
- `tcl/target/ti/tms320/generated/tms320f28062.cfg`
- `tcl/target/ti/tms320/generated/tms320f28063.cfg`
- `tcl/target/ti/tms320/generated/tms320f28064.cfg`
- `tcl/target/ti/tms320/generated/tms320f28065.cfg`
- `tcl/target/ti/tms320/generated/tms320f28066.cfg`
- `tcl/target/ti/tms320/generated/tms320f28067.cfg`
- `tcl/target/ti/tms320/generated/tms320f28068.cfg`
- `tcl/target/ti/tms320/generated/tms320f28069.cfg`
- `tcl/target/ti/tms320/generated/tms320f28074.cfg`
- `tcl/target/ti/tms320/generated/tms320f28075.cfg`
- `tcl/target/ti/tms320/generated/tms320f28076.cfg`
- `tcl/target/ti/tms320/generated/tms320f28079.cfg`
- `tcl/target/ti/tms320/generated/tms320f2808.cfg`
- `tcl/target/ti/tms320/generated/tms320f2809.cfg`
- `tcl/target/ti/tms320/generated/tms320f2810.cfg`
- `tcl/target/ti/tms320/generated/tms320f2811.cfg`
- `tcl/target/ti/tms320/generated/tms320f2812.cfg`
- `tcl/target/ti/tms320/generated/tms320f28232.cfg`
- `tcl/target/ti/tms320/generated/tms320f28234.cfg`
- `tcl/target/ti/tms320/generated/tms320f28235.cfg`
- `tcl/target/ti/tms320/generated/tms320f28332.cfg`
- `tcl/target/ti/tms320/generated/tms320f28333.cfg`
- `tcl/target/ti/tms320/generated/tms320f28334.cfg`
- `tcl/target/ti/tms320/generated/tms320f28335.cfg`
- `tcl/target/ti/tms320/generated/tms320f28374d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28374s.cfg`
- `tcl/target/ti/tms320/generated/tms320f28375d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28375s.cfg`
- `tcl/target/ti/tms320/generated/tms320f28376d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28376s.cfg`
- `tcl/target/ti/tms320/generated/tms320f28377d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28377s.cfg`
- `tcl/target/ti/tms320/generated/tms320f28378d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28378s.cfg`
- `tcl/target/ti/tms320/generated/tms320f28379d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28379s.cfg`
- `tcl/target/ti/tms320/generated/tms320f2837hd.cfg`
- `tcl/target/ti/tms320/generated/tms320f28384d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28384s.cfg`
- `tcl/target/ti/tms320/generated/tms320f28386d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28386s.cfg`
- `tcl/target/ti/tms320/generated/tms320f28388d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28388s.cfg`
- `tcl/target/ti/tms320/generated/tms320f28plc83.cfg`
- `tcl/target/ti/tms320/generated/tms320f28plc84.cfg`
- `tcl/target/ti/tms320/generated/tms320f28plc85.cfg`
- `tcl/target/ti/tms320/generated/tms320f28plc90d.cfg`
- `tcl/target/ti/tms320/generated/tms320f28plc93.cfg`
- `tcl/target/ti/tms320/generated/tms320f28plc95.cfg`
- `tcl/target/ti/tms320/generated/tms320r2810.cfg`
- `tcl/target/ti/tms320/generated/tms320r2812.cfg`
- `tcl/target/ti/tms320/generated/tpr12.cfg`
- `tcl/target/ti/tms320/index.cfg`
- `tcl/target/ti/tms320f280049.cfg`
- `tcl/target/ti/tms320f28069.cfg`
- `tcl/target/ti/tms320f28m35x-dual-core.cfg`
- `tcl/target/ti/tms320f28m35x.cfg`

</details>

<details><summary><code>zephyrproject-rtos/openocd</code> (10 个)</summary>

- `tcl/board/nds32_xc5.cfg`
- `tcl/board/snps_hsdk_smp.cfg`
- `tcl/target/nds32v2.cfg`
- `tcl/target/nds32v3.cfg`
- `tcl/target/nds32v3m.cfg`
- `tcl/target/rp2040-core0.cfg`
- `tcl/target/rv32m1_ri5cy.cfg`
- `tcl/target/rv32m1_zero_riscy.cfg`
- `tcl/target/snps_hsdk_smp.cfg`
- `tcl/target/vd_xtensa_jtag.cfg`

</details>

<details><summary><code>zuyih/openocd</code> (18 个)</summary>

- `tcl/board/art_pi2.cfg`
- `tcl/board/atk_cnn647b.cfg`
- `tcl/board/st_nucleo_c5.cfg`
- `tcl/board/st_nucleo_h5.cfg`
- `tcl/board/ti_beaglebone.cfg`
- `tcl/board/ti_beaglebone_black.cfg`
- `tcl/gdb_helper.tcl`
- `tcl/interface/ch347.cfg`
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

## src/ C 源码（需在构建系统注册）

文件数：**65**

| 来源仓库 | SPDX | 文件数 |
|---|---|---:|
| [`analogdevicesinc/openocd`](https://github.com/analogdevicesinc/openocd) | NOASSERTION(14) | 14 |
| [`xsession/openocd`](https://github.com/xsession/openocd) | NOASSERTION(8) | 8 |
| [`zephyrproject-rtos/openocd`](https://github.com/zephyrproject-rtos/openocd) | NOASSERTION(7) | 7 |
| [`Icey7122/openocd`](https://github.com/Icey7122/openocd) | NOASSERTION(7) | 7 |
| [`AnlogicInfo/al_openocd`](https://github.com/AnlogicInfo/al_openocd) | GPL-2.0(4), UNRESOLVED(1) | 5 |
| [`aesc-silicon/elements-openocd`](https://github.com/aesc-silicon/elements-openocd) | NOASSERTION(4) | 4 |
| [`Seneral/riscv-openocd-wch`](https://github.com/Seneral/riscv-openocd-wch) | GPL-2.0-or-later(2), GPL-2.0(1), UNRESOLVED(1) | 4 |
| [`intel/OpenOCD`](https://github.com/intel/OpenOCD) | GPL-2.0(4) | 4 |
| [`espressif/openocd-esp32`](https://github.com/espressif/openocd-esp32) | GPL-2.0-or-later(2), NOASSERTION(1) | 3 |
| [`linux-msm/openocd`](https://github.com/linux-msm/openocd) | NOASSERTION(3) | 3 |
| [`yottatsa/openocd`](https://github.com/yottatsa/openocd) | NOASSERTION(2) | 2 |
| [`STMicroelectronics/OpenOCD`](https://github.com/STMicroelectronics/OpenOCD) | GPL-2.0-or-later(1) | 1 |
| [`zuyih/openocd`](https://github.com/zuyih/openocd) | NOASSERTION(1) | 1 |
| [`stache3000/openocd-dirtyjtag`](https://github.com/stache3000/openocd-dirtyjtag) | NOASSERTION(1) | 1 |
| [`kevinmehall/openOCD`](https://github.com/kevinmehall/openOCD) | GPL-2.0(1) | 1 |

### ⚠️ 需人工审计（50 个文件无许可证信息）

这些文件的来源仓库在 GitHub 上未解析出许可证，商用前必须逐个查看文件头部的版权声明。

<details><summary><code>AnlogicInfo/al_openocd</code> (1 个)</summary>

- `src/jtag/drivers/al_link.c`

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

<details><summary><code>Seneral/riscv-openocd-wch</code> (1 个)</summary>

- `src/target/wch_riscv.h`

</details>

<details><summary><code>aesc-silicon/elements-openocd</code> (4 个)</summary>

- `src/jtag/drivers/jtag_tcp.c`
- `src/target/vexriscv-csrs.h`
- `src/target/vexriscv.c`
- `src/target/vexriscv.h`

</details>

<details><summary><code>analogdevicesinc/openocd</code> (14 个)</summary>

- `src/jtag/drivers/adi_dbg_agent.c`
- `src/jtag/drivers/ice1000.c`
- `src/jtag/drivers/ice1500.c`
- `src/jtag/drivers/usbmux.c`
- `src/jtag/drivers/usbmux.h`
- `src/target/rvmax/encoding.h`
- `src/target/rvmax/gdb_regs.h`
- `src/target/rvmax/opcodes.h`
- `src/target/rvmax/rvmax.c`
- `src/target/rvmax/rvmax.h`
- `src/target/rvmax/rvmax_du.h`
- `src/target/rvmax/rvmax_du_adv.c`
- `src/target/rvmax/rvmax_tap.h`
- `src/target/rvmax/rvmax_tap_mohor.c`

</details>

<details><summary><code>espressif/openocd-esp32</code> (1 个)</summary>

- `src/jtag/drivers/jtag_esp_remote.c`

</details>

<details><summary><code>linux-msm/openocd</code> (3 个)</summary>

- `src/target/aarch64_coproc_reg.c`
- `src/target/aarch64_system_registers.h`
- `src/target/aarch64_system_registers_defs.h`

</details>

<details><summary><code>stache3000/openocd-dirtyjtag</code> (1 个)</summary>

- `src/jtag/drivers/dirtyjtag.c`

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

<details><summary><code>zephyrproject-rtos/openocd</code> (7 个)</summary>

- `src/flash/nor/rv32m1.c`
- `src/target/rv32m1/rv32m1.c`
- `src/target/rv32m1/rv32m1.h`
- `src/target/rv32m1/rv32m1_du.h`
- `src/target/rv32m1/rv32m1_du_adv.c`
- `src/target/rv32m1/rv32m1_tap.h`
- `src/target/rv32m1/rv32m1_tap_mohor.c`

</details>

<details><summary><code>zuyih/openocd</code> (1 个)</summary>

- `src/jtag/drivers/cmsis_dap_wch.c`

</details>

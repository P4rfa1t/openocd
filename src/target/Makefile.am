# SPDX-License-Identifier: GPL-2.0-or-later

%C%_libtarget_la_LIBADD = %D%/openrisc/libopenrisc.la \
	%D%/riscv/libriscv.la \
	%D%/xtensa/libxtensa.la \
	%D%/espressif/libespressif.la

%C%_libtarget_la_CPPFLAGS = $(AM_CPPFLAGS)

STARTUP_TCL_SRCS += %D%/startup.tcl

noinst_LTLIBRARIES += %D%/libtarget.la
%C%_libtarget_la_SOURCES = \
	$(TARGET_CORE_SRC) \
	$(ARM_DEBUG_SRC) \
	$(ARMV4_5_SRC) \
	$(ARMV6_SRC) \
	$(ARMV7_SRC) \
	$(ARM_MISC_SRC) \
	$(AVR32_SRC) \
	$(MIPS32_SRC) \
	$(STM8_SRC) \
	$(INTEL_IA32_SRC) \
	$(ESIRISC_SRC) \
        $(ARC_SRC) \
	%D%/avrt.c \
	%D%/dsp563xx.c \
	%D%/dsp563xx_once.c \
	%D%/dsp5680xx.c \
	%D%/hla_target.c \
	$(ARMV8_SRC) \
	$(MIPS64_SRC)

if HAVE_CAPSTONE
%C%_libtarget_la_CPPFLAGS += $(CAPSTONE_CFLAGS)
%C%_libtarget_la_LIBADD += $(CAPSTONE_LIBS)
%C%_libtarget_la_SOURCES += %D%/oocd_capstone.c
endif

TARGET_CORE_SRC = \
	%D%/algorithm.c \
	%D%/register.c \
	%D%/image.c \
	%D%/breakpoints.c \
	%D%/target.c \
	%D%/target_request.c \
	%D%/testee.c \
	%D%/semihosting_common.c \
	%D%/smp.c \
	%D%/rtt.c

ARMV4_5_SRC = \
	%D%/armv4_5.c \
	%D%/armv4_5_mmu.c \
	%D%/armv4_5_cache.c \
	$(ARM7_9_SRC)

ARM7_9_SRC = \
	%D%/arm7_9_common.c \
	%D%/arm7tdmi.c \
	%D%/arm720t.c \
	%D%/arm9tdmi.c \
	%D%/arm920t.c \
	%D%/arm966e.c \
	%D%/arm946e.c \
	%D%/arm926ejs.c \
	%D%/feroceon.c

ARM_MISC_SRC = \
	%D%/fa526.c \
	%D%/xscale.c

ARMV6_SRC = \
	%D%/arm11.c \
	%D%/arm11_dbgtap.c

ARMV7_SRC = \
	%D%/armv7m.c \
	%D%/armv7m_cache.c \
	%D%/armv7m_trace.c \
	%D%/cortex_m.c \
	%D%/armv7a.c \
	%D%/armv7a_mmu.c \
	%D%/cortex_a.c \
	%D%/ls1_sap.c \
	%D%/mem_ap.c

ARMV8_SRC = \
	%D%/armv8_dpm.c \
	%D%/armv8_opcodes.c \
	%D%/aarch64.c \
	%D%/armv8.c \
	%D%/armv8_cache.c

ARM_DEBUG_SRC = \
	%D%/arm_dpm.c \
	%D%/arm_jtag.c \
	%D%/arm_disassembler.c \
	%D%/arm_simulator.c \
	%D%/arm_semihosting.c \
	%D%/arm_adi_v5.c \
	%D%/arm_dap.c \
	%D%/armv7a_cache.c \
	%D%/armv7a_cache_l2x.c \
	%D%/adi_v5_dapdirect.c \
	%D%/adi_v5_jtag.c \
	%D%/adi_v5_swd.c \
	%D%/embeddedice.c \
	%D%/trace.c \
	%D%/etb.c \
	%D%/etm.c \
	%D%/etm_dummy.c \
	%D%/arm_tpiu_swo.c \
	%D%/arm_cti.c

AVR32_SRC = \
	%D%/avr32_ap7k.c \
	%D%/avr32_jtag.c \
	%D%/avr32_mem.c \
	%D%/avr32_regs.c

MIPS32_SRC = \
	%D%/mips32.c \
	%D%/mips_m4k.c \
	%D%/mips32_pracc.c \
	%D%/mips32_dmaacc.c \
	%D%/mips_ejtag.c

MIPS64_SRC = \
	%D%/mips64.c \
	%D%/mips32_pracc.c \
	%D%/mips64_pracc.c \
	%D%/mips_mips64.c \
	%D%/trace.c \
	%D%/mips_ejtag.c

STM8_SRC = \
	%D%/stm8.c

INTEL_IA32_SRC = \
	%D%/quark_x10xx.c \
	%D%/quark_d20xx.c \
	%D%/lakemont.c \
	%D%/x86_32_common.c

ESIRISC_SRC = \
	%D%/esirisc.c \
	%D%/esirisc_jtag.c \
	%D%/esirisc_trace.c

# The third-party ARC backend (foss-for-mips-arc-processors/openocd,
# branch arc-2026.09) is a superset of upstream's single-type arc.c: it
# registers the arc600, arc700 AND arcv2 target types, and it is the only
# implementation that registers the "arc jtag" command group that every
# tcl/cpu/arc/*.tcl script drives. Upstream arc.c registers no commands at all,
# so the tcl layer cannot work against it.
#
# The two implementations both define arcv2_target, so exactly one may be
# compiled. The fork keeps the upstream files in the tree for reference but
# builds the third-party backend.
#
# arc_core.c and arc_trgt.c also came with that import, but nothing in the
# backend or the tree calls the three functions they export
# (arc_core_soft_reset_halt, arc_core_type_info, arc_trgt_request_data) and
# they include the upstream arc.h rather than arc32.h, so they are left out of
# the build instead of being silently linked into nothing.
ARC_SRC = \
        %D%/arc32.c \
        %D%/arc_dbg.c \
        %D%/arc_jtag.c \
        %D%/arc_mntr.c \
        %D%/arc_ocd.c \
        %D%/arc_regs.c

%C%_libtarget_la_SOURCES += \
	%D%/algorithm.h \
	%D%/arm.h \
	%D%/arm_coresight.h \
	%D%/arm_dpm.h \
	%D%/arm_jtag.h \
	%D%/arm_adi_v5.h \
	%D%/armv7a_cache.h \
	%D%/armv7a_cache_l2x.h \
	%D%/armv7a_mmu.h \
	%D%/arm_disassembler.h \
	%D%/arm_opcodes.h \
	%D%/arm_simulator.h \
	%D%/arm_semihosting.h \
	%D%/arm7_9_common.h \
	%D%/arm7tdmi.h \
	%D%/arm720t.h \
	%D%/arm9tdmi.h \
	%D%/arm920t.h \
	%D%/arm926ejs.h \
	%D%/arm966e.h \
	%D%/arm946e.h \
	%D%/arm11.h \
	%D%/arm11_dbgtap.h \
	%D%/armv4_5.h \
	%D%/armv4_5_mmu.h \
	%D%/armv4_5_cache.h \
	%D%/armv7a.h \
	%D%/armv7m.h \
	%D%/armv7m_cache.h \
	%D%/armv7m_trace.h \
	%D%/armv8.h \
	%D%/armv8_dpm.h \
	%D%/armv8_opcodes.h \
	%D%/armv8_cache.h \
	%D%/avrt.h \
	%D%/dsp563xx.h \
	%D%/dsp563xx_once.h \
	%D%/dsp5680xx.h \
	%D%/breakpoints.h \
	%D%/cortex_m.h \
	%D%/cortex_a.h \
	%D%/aarch64.h \
	%D%/embeddedice.h \
	%D%/etb.h \
	%D%/etm.h \
	%D%/etm_dummy.h \
	%D%/arm_tpiu_swo.h \
	%D%/image.h \
	%D%/mips32.h \
	%D%/mips64.h \
	%D%/mips_cpu.h \
	%D%/mips_m4k.h \
	%D%/mips_mips64.h \
	%D%/mips_ejtag.h \
	%D%/mips32_pracc.h \
	%D%/mips32_dmaacc.h \
	%D%/mips64_pracc.h \
	%D%/register.h \
	%D%/target.h \
	%D%/target_type.h \
	%D%/trace.h \
	%D%/target_request.h \
	%D%/trace.h \
	%D%/xscale.h \
	%D%/smp.h \
	%D%/avr32_ap7k.h \
	%D%/avr32_jtag.h \
	%D%/avr32_mem.h \
	%D%/avr32_regs.h \
	%D%/semihosting_common.h \
	%D%/lakemont.h \
	%D%/x86_32_common.h \
	%D%/arm_cti.h \
	%D%/esirisc.h \
	%D%/esirisc_jtag.h \
	%D%/esirisc_regs.h \
	%D%/esirisc_trace.h \
	%D%/arc.h \
	%D%/arc_cmd.h \
	%D%/arc_jtag.h \
	%D%/arc_mem.h \
	%D%/rtt.h \
	%D%/oocd_capstone.h

include %D%/openrisc/Makefile.am
include %D%/riscv/Makefile.am
include %D%/xtensa/Makefile.am
include %D%/espressif/Makefile.am
# --- third-party target architectures (tools/patch_target_groups.py) ---

if TARGETS_ALL

C28X_SRC = \
	%D%/c28x.c

%C%_libtarget_la_SOURCES += $(C28X_SRC)

TMS320_SRC = \
	%D%/tms320.c

%C%_libtarget_la_SOURCES += $(TMS320_SRC)

QUARK_SRC = \
	%D%/quark_d2000.c \
	%D%/quark_se.c

%C%_libtarget_la_SOURCES += $(QUARK_SRC)

VORTEX86_SRC = \
	%D%/vortex86.c

%C%_libtarget_la_SOURCES += $(VORTEX86_SRC)

LOONGARCH_SRC = \
	%D%/loongarch.c \
	%D%/loongarch_ejtag.c \
	%D%/loongarch_pracc.c

%C%_libtarget_la_SOURCES += $(LOONGARCH_SRC)

if USE_LIBUSB1
MCHP_RI4_SRC = \
	%D%/mchp_ri4_bridge.c \
	%D%/mchp_ri4_native.c

%C%_libtarget_la_SOURCES += $(MCHP_RI4_SRC)

%C%_libtarget_la_CPPFLAGS += $(LIBUSB1_CFLAGS)
%C%_libtarget_la_LIBADD += $(LIBUSB1_LIBS)

endif

if HAVE_LIBYAML
VEXRISCV_SRC = \
	%D%/vexriscv.c

%C%_libtarget_la_SOURCES += $(VEXRISCV_SRC)

%C%_libtarget_la_CPPFLAGS += $(LIBYAML_CFLAGS)
%C%_libtarget_la_LIBADD += $(LIBYAML_LIBS)

endif

RVMAX_SRC = \
	%D%/rvmax/rvmax.c \
	%D%/rvmax/rvmax_du_adv.c \
	%D%/rvmax/rvmax_tap_mohor.c

%C%_libtarget_la_SOURCES += $(RVMAX_SRC)

RV32M1_SRC = \
	%D%/rv32m1/rv32m1.c \
	%D%/rv32m1/rv32m1_du_adv.c \
	%D%/rv32m1/rv32m1_tap_mohor.c

%C%_libtarget_la_SOURCES += $(RV32M1_SRC)

if HAVE_ZLIB
%C%_libtarget_la_CPPFLAGS += $(ZLIB_CFLAGS)
%C%_libtarget_la_LIBADD += $(ZLIB_LIBS)
endif

# Headers, so `make dist` ships them.
%C%_libtarget_la_SOURCES += \
	%D%/c28x.h \
	%D%/loongarch.h \
	%D%/loongarch_ejtag.h \
	%D%/loongarch_modules.h \
	%D%/loongarch_pracc.h \
	%D%/mchp_ri4_bridge.h \
	%D%/mchp_ri4_native.h \
	%D%/quark_d2000.h \
	%D%/quark_se.h \
	%D%/rv32m1/rv32m1.h \
	%D%/rv32m1/rv32m1_du.h \
	%D%/rv32m1/rv32m1_tap.h \
	%D%/rvmax/encoding.h \
	%D%/rvmax/gdb_regs.h \
	%D%/rvmax/opcodes.h \
	%D%/rvmax/rvmax.h \
	%D%/rvmax/rvmax_du.h \
	%D%/rvmax/rvmax_tap.h \
	%D%/tms320.h \
	%D%/vexriscv-csrs.h \
	%D%/vexriscv.h \
	%D%/vortex86.h

endif

# --- end third-party target architectures ---

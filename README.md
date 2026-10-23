# OpenOCD Third-Party Support

[![snapshot](https://github.com/P4rfa1t/openocd/actions/workflows/snapshot.yml/badge.svg)](https://github.com/P4rfa1t/openocd/actions/workflows/snapshot.yml)

A fork of [`openocd-org/openocd`](https://github.com/openocd-org/openocd) that folds
chip, board and programmer support from community forks **into the source tree
itself** — the same directories, the same build system, the same `git merge`.

> A Chinese-language version of this document lives in [`README.zh-CN.md`](README.zh-CN.md).

---

## Why this exists

OpenOCD's upstream has always been conservative about new targets. A chip
support usually lives in a maintainer's fork for years — sometimes forever —
because the pull request never arrives. Meanwhile the same board config gets
copy-pasted between 40 repositories, each with a slightly different spelling,
and `openocd -f board/whatever.cfg` works on one machine and not the next.

Collecting those forks into a separate overlay directory does not fix this.
An overlay has to shadow the official file search path, so a later upstream
rename silently keeps serving the stale copy. There is no merge, only
overwrite.

**This repository is a real fork.** Upstream files sit in `src/`, `tcl/`,
`doc/`, `contrib/` exactly where upstream put them. Third-party support sits
in the directories it belongs in:

```
tcl/target/xxx.cfg        ← chip target config
tcl/board/xxx.cfg         ← board config
tcl/interface/xxx.cfg     ← debug probe interface
src/jtag/drivers/xxx.c    ← programmer driver
src/target/xxx.c          ← new architecture backend
```

Updating is one command, and the conflicts are real conflicts you can read:

```bash
git fetch upstream
git merge upstream/master
```

When upstream reorganises a directory, git shows you the conflict. It does not
silently keep serving a stale duplicate from a shadowed search path.

---

## What was merged

689 candidate repositories were surveyed — 500 forks of upstream plus 189
independent repositories found by search — deduplicated across repositories,
and stripped of files that are equivalent to what upstream already ships.

| | count | notes |
|---|---:|---|
| `tcl/` script files | 702 | 686 `.cfg` plus 16 `.tcl`/`.xml`/`.txt`; **work with no build changes at all** |
| `src/` C sources | 65 | 35 `.c` plus 30 `.h`; **47 wired into the build**, 18 staged but not yet registered |
| duplicate copies collapsed | 6910 | one winner kept per path |
| files dropped as upstream-equivalent | 7376 | upstream already ships them, or ships them under another path |
| candidates rejected as unusable | 621 | build-system files, non-C payloads and core internals that exist upstream under the same name |

Of the 1298 unique paths the survey identified, 747 tier-1 records were
marked imported and 697 of them are still in the tree today; 50 were dropped
on purpose after import and 147 never landed. A further 5 files came in as
dependencies of landed configs without a tier-1 record of their own, leaving
**767 tracked third-party files** today — 702 under `tcl/` plus 65 under `src/`. The
ledger closes: 697 + 5 = 702.

The 260 C sources that did not land all need per-backend porting: they are
published forks of drivers that still call an older OpenOCD API. `src/flash` holds
the largest group (125 files), then `src/target` (85) and `src/jtag`
(50).

The 147 tier-1 TCL paths that never landed are, mechanically, the tier-1 records
that are neither in the tree nor listed in `removed_from_tree`. The old "ready to
import / needs a backend / depends on a missing file / not retrievable" split was a
hand classification of an earlier snapshot that no tool reproduces any more, so it
has been dropped from this README. What is reproducible is the tier-1 ledger:
894 candidates, 747 marked imported, 697 still in the tree,
50 removed after import, 147 never landed.

The two wrappers the TI boards need (`interface/ti/xds100v2.cfg`, `xds100v3.cfg`),
the 3 paths that were already in the tree under a flat-spelling parent, and the
9 TI board configs that depend on those wrappers are all listed per file
in `manifest/consolidated.json` under `not_imported` (407 paths in total).

Two more groups complete the count of **767 files**, each with its own provenance
entry:

- **21 files pulled in as dependencies** — a config that `source`s another
  config brings the referenced file along with it. They are marked
  `imported_as: dependency` in the manifest.
- **1 file that upstream also ships under the same name** —
  `tcl/target/adspsc58x.cfg`, whose content differs from upstream's
  `tcl/target/adsp-sc58x.cfg`. The tree keeps the third-party version, and the
  collision is one of the 25 warnings `verify_tree` reports.

Upstream ships 2203 files; this tree ships 3032.

**All 767 imported files are pinned to the exact commit they came from.** Any
file can be traced back to the fork and the commit that published it:

```bash
python - <<'PY'
import json
files = json.load(open("manifest/PROVENANCE.json", encoding="utf-8"))["files"]
entry = files["tcl/target/nucleo_l552ze.cfg"]
print(entry["source_repo"], entry["source_branch"], entry["source_commit"], entry["license"])
PY
```

The survey covered **689 candidate repositories**; 53 of them
contributed at least one file that is still in the tree.

### The `tcl/` files work immediately

Upstream's root `Makefile.am` installs TCL with a wildcard, not a hardcoded
list:

```makefile
TCL_FILES = find $(srcdir)/$(TCL_PATH) -name '*.cfg' -o -name '*.tcl' -o -name '*.txt'
```

So a new `.cfg` is picked up by `make install` with **no change to
`configure.ac` or `Makefile.am` and no recompilation**. Any scheme that
generates build entries for these files is inventing complexity that does not
exist.

### The `src/` files are split

47 of the 65 new C sources and headers are wired into the build — 24 `.c`
files that register a working `target_type` or `adapter_driver`, plus the
headers they need:

| group | backends | build switch |
|---|---|---|
| `TARGETS_ALL` | `c28x`, `tms320`, `quark_d2000`, `quark_se`, `vortex86`, `loongarch`, `rvmax`, `rv32m1` | `--disable-third-party-targets` turns the group off |
| `MCHP_RI4` | `mchp_ri4_bridge` | also needs libusb1 |
| `VEXRISCV` | `vexriscv` | also needs libyaml |

Ten target types in total are new to this tree, and six adapter drivers —
`dirtyjtag`, `ice1000`, `ice2000`, `ice1500`, `dbgagent`, `mp_dbgagent` — are
registered alongside upstream's 38 target types and 45 adapter drivers.

The `rvmax` and `rv32m1` backends register their commands with an
architecture prefix — `rvmax_tap_select`, `rv32m1_du_select`,
`rv32m1_core_select` and so on. Upstream's `or1k` backend registers the
unprefixed `tap_select` / `du_select` / `addreg` names, and OpenOCD silently
ignores a second registration of an existing command name, so an unprefixed
second backend would have been driven by the first one's handler. With the
prefixes, all three coexist.

The remaining 18 — 11 `.c` and 7 `.h` — are **present in the tree but not
compiled**: `al_link.c` and `al_link_cyusb.c`, `cmsis_dap_wch.c`, `esp_gpio.c`,
`jtag_esp_remote.c`, `jtag_tcp.c`, `wlinke.c`, `rbb_server.c`,
`aarch64_coproc_reg.c`, `wch_riscv.c` and `wch_riscv-013.c`, plus the headers
only those files include (`al_link_cyusb.h`, `esp_gpio.h`, `rbb_server.h`,
`aarch64_system_registers.h`, `aarch64_system_registers_defs.h`,
`altera_virtual_jtag.h`, `wch_riscv.h`). The reasons differ per file — the `arc32`
family that used to sit here was staged, found unbuildable and dropped in
`7ffeda047` — and registering each one needs the porting work described below.
Shipping them unregistered is deliberate: the code is there, visible, reviewable,
and harmless until it is wired up.

The per-file reasons are in `docs/02-usage.md`. The old claim that all of them
"target upstream APIs that have moved" is not true for `jtag_tcp.c`,
`jtag_esp_remote.c`, `cmsis_dap_wch.c` and `aarch64_coproc_reg.c`, which never
existed upstream, nor for the 11 files newly staged in `21ab67574`.

### The ST-LINK external loader driver

`src/flash/nor/stldr_driver.c` is the STMicroelectronics external-loader
driver, imported from `STMicroelectronics/OpenOCD` at branch
`openocd-cubeide-r7`. It lets a flash bank be programmed by an ST-LINK
firmware blob instead of by a dedicated flash algorithm, which is how the
newer STM32 families are programmed.

The driver was taken as the vendor published it, with two adjustments:

- **The ELF structures are defined locally.** A `.stldr` file is an ELF32
  object, and the driver walks its section headers and symbol table by hand
  rather than through OpenOCD's generic image loader. `<elf.h>` is not
  available on every build host — the Windows release build cross-compiles
  with MinGW, which has no `elf.h` — so the file carries the handful of
  `Elf32_Shdr` / `Elf32_Sym` definitions it needs, guarded by
  `#ifndef HAVE_ELF_H` so a host that does have the header keeps using it.
- **The timeout argument is unsigned.** `stldr_exec_function()` took an
  `int` where `target_run_algorithm()` expects an `unsigned int`.

**The `.stldr` loader binaries themselves are not in this repository.** They
are proprietary blobs published by ST, and the four imported configs that use
them look for them at `loaders/stldr/...` at run time:

| config | loader it expects |
|---|---|
| `tcl/target/stm32v8x.cfg` | set per board with `stldr set_loader` |
| `tcl/target/stm32l4plusx.cfg` | set per board with `stldr set_loader` |
| `tcl/board/art_pi2.cfg` | `loaders/stldr/ART-Pi2_ST_winbond_64MB.stldr` |
| `tcl/board/atk_cnn647b.cfg` | `loaders/stldr/MX25UM25645G_ATK-CNN647B_ExtMemLoader.stldr` |

Copy the loader you need next to the `openocd` executable's share directory
and point the config at it.

---

## Building

This is a standard OpenOCD tree. There is no extra step.

```bash
git clone --recursive https://github.com/P4rfa1t/openocd.git
cd openocd
./bootstrap && ./configure && make -j
sudo make install
```

Third-party target architectures are on by default. To build upstream's tree
only:

```bash
./configure --disable-third-party-targets
```

Three optional dependencies are probed, not required. A missing library only
removes the group that needs it; `configure` never fails because of them.

| dependency | enables |
|---|---|
| `libusb-1.0` | the `mchp_ri4_bridge` USB backend and every ADI probe |
| `libyaml-0.1` | the `vexriscv` target |
| `zlib` | `mchp_ri4` firmware download (`.gz` script bundles) |

Windows: see upstream's `README.Windows.md`. This fork does not change it.

### CI: prebuilt Windows package

`.github/workflows/snapshot.yml` cross-compiles an x86_64 Windows package with
MinGW and uploads it as a workflow artifact. It is upstream's own workflow with
the target triplet and the release-publishing step adjusted; the dependency
list (libusb1, hidapi, libftdi, capstone, libjaylink, jimtcl, libyaml, zlib)
and the build recipe are upstream's.

---

## Tracking every change

### Provenance

`manifest/PROVENANCE.json` records, per file: the source repository, the
branch, the exact commit, the license as GitHub resolved it, the SHA-256 of
the file as published, and any local divergence. Two per-tier manifests
(`manifest/tier1-PROVENANCE.json`, `manifest/tier2-PROVENANCE.json`) hold the
same data before it is merged.

Divergence is recorded in two distinct forms, because they mean different
things:

- `content edited in this fork` — a real change: a port to a newer upstream
  API, a repaired `source [find ...]` path, a build-system fix.
- `line endings normalised to LF` — the content is byte-identical to what the
  fork published; only the terminators differ.

The distinction matters. An earlier revision of this repository failed its own
integrity check with 543 mismatches, because the tree had been rebuilt in text
mode on Windows and every imported file was silently stored with CRLF while the
manifest described the LF original. The gate could not tell "this was edited"
from "this was checked out on a Windows host". Both are fixed now: the tree is
LF everywhere, 548 of the 767 imported files still match their published
digest byte for byte, 2 are a terminator-only difference, and 217 carry real
local edits (26 of those also had their terminators normalised) — the target
API ports, the relocated `source [find ...]` paths, the third-party driver fixes
and the `rvmax` / `rv32m1` backends.

Files that were deliberately removed stay in the manifests under
`removed_from_tree`, with the reason and the commit that removed them. The
audit trail is bidirectional.

### Verifying

```bash
python tools/verify_tree.py
```

```
recorded : 767
on disk  : 767
errors   : 0
warns    : 25
VERIFY: PASS
```

The 25 warnings are one file whose name collides with an upstream file but
whose content differs (kept, deliberately) and 24 files whose license GitHub
could not resolve.

### Other tools

| tool | what it does |
|---|---|
| `tools/verify_tree.py` | offline integrity gate: every recorded file present, digests match, no upstream duplicates, TCL braces balanced |
| `tools/refresh_provenance.py` | refresh digests after a deliberate edit, keeping the original under `pristine_sha256` |
| `tools/normalize_eol.py` | normalise text files to LF, skipping binaries by the same 8 KiB NUL heuristic git uses |
| `tools/sync_upstream.py` | report what upstream added, removed or absorbed since the pinned commit |
| `tools/prune_deleted.py` | drop manifest records for files intentionally removed from the tree |
| `tools/prune_upstream_dups.py` | drop imported files upstream now has |
| `tools/prune_shadow.py` | drop shadow copies of files upstream moved to another directory |
| `tools/build_provenance.py` | merge the two tier manifests into the combined one |
| `tools/consolidate.py` | rebuild the consolidation index from the survey data |
| `tools/survey_nested_src.py` | repair the survey for source files in a subdirectory of a probed directory |
| `tools/expand_subtrees.py` | repair the survey by walking the subdirectories the trees API treats as opaque |
| `tools/sync_doc_numbers.py` | rewrite the hand-written counts in the docs from the manifests, so they cannot drift |
| `tools/gen_licenses.py` | regenerate `docs/03-LICENSES.md` and `manifest/licenses.csv` |
| `tools/gen_report.py` | regenerate `docs/01-inventory.md` |
| `tools/patch_target_groups.py` | idempotent wiring of the target groups into `configure.ac`, `src/target/Makefile.am` and `src/target/target.c` |
| `tools/patch_interfaces.py`, `tools/patch_interface_h.py`, `tools/patch_makefile.py`, `tools/patch_usbmux.py` | the same kind of idempotent wiring for the adapter drivers |
| `tools/check_target_signatures.py` | compare the third-party backends' callback signatures against upstream's `target_type` |
| `tools/port_new_archs.py` | read-only: assert that the rvmax / rv32m1 port is complete and that no pre-port form survived |
| `tools/stage_new_archs.py` | copy the staged rvmax / rv32m1 sources into their in-tree locations, byte for byte |
| `tools/stage_new_imports.py` | download newly approved third-party files into a staging directory, never into the tree |
| `tools/stage_symbol_check.py`, `tools/deep_link_check.py` | read-only: find identifiers the staged files use that upstream does not define |
| `tools/fix_target_apis.py`, `tools/fix_driver_apis.py` | port the imported backends across upstream API drift |
| `tools/fix_relocated_sources.py` | repair `source [find ...]` references left pointing at a flat path upstream has since reorganised |
| `tools/audit_dangling_refs.py` | read-only: find `source [find X]` references that resolve to nothing |
| `tools/audit_target_headers.py` | read-only: check every third-party target's includes against the tree |
| `tools/fetch_third_party.py`, `tools/fetch_missing_tcl.py` | re-fetch imported files from their pinned commits |
| `tools/mine_github.py`, `tools/refine_survey.py`, `tools/resolve_deps.py`, `tools/pin_commits.py` | the survey stage: discover, classify and pin the candidate repositories |
| `tools/pipeline.py`, `tools/run_mine.sh`, `tools/run_fetch.sh` | the survey pipeline end to end |

`tools/patch_target_groups.py` is idempotent by design — running it twice
produces byte-identical files, and the tree carries a sentinel comment marking
every block it owns so the script can find and replace its own work.

---

## Documentation

| file | contents |
|---|---|
| [`docs/00-findings.md`](docs/00-findings.md) | the research phase: what the mechanism is, what was tried, what was wrong |
| [`docs/01-inventory.md`](docs/01-inventory.md) | the inventory: how many repositories, how many files, where they came from |
| [`docs/02-usage.md`](docs/02-usage.md) | usage notes, and the list of known limitations |
| [`docs/03-LICENSES.md`](docs/03-LICENSES.md) | per-file license table |
| [`manifest/PROVENANCE.json`](manifest/PROVENANCE.json) | machine-readable provenance for all 767 imported files |

---

## Releases

Fork releases are tagged `v<upstream>-fork.<n>` — an upstream `developer` point
release plus a fork sequence number — and built by
[`.github/workflows/snapshot.yml`](.github/workflows/snapshot.yml). Pushing a tag
produces `openocd-<tag>-x86_64-w64-mingw32.tar.gz` and the Release itself is
created by CI with `gh`; nothing is published from a local machine. See
[`docs/04-release.md`](docs/04-release.md) for the process and for the checklist
to run before the next tag, and [`CHANGELOG.md`](CHANGELOG.md) for what changed.

## License

The OpenOCD sources inherited from upstream are GPL-2.0-or-later; the
documentation is GFDL-1.2-no-invariants-or-later. See `COPYING` and `LICENSES/`.

**The imported third-party files are not covered by that blanket statement.**
Of 767 files, GitHub resolved 123 as GPL-2.0, 5 as GPL-2.0-or-later, 615 as
`NOASSERTION` (which means *GitHub could not determine a license* — not that it
is permissive) and 24 as unresolvable. Some `NOASSERTION` files carry their own
proprietary notices, for example the Analog Devices flash algorithms, which
state that the software is proprietary to Analog Devices, Inc.

This repository therefore has **no single license of its own**. If you intend
to redistribute it, read `manifest/licenses.csv` and `docs/03-LICENSES.md`
first. The `LICENSE` file spells this out in full.

---

## Known limitations

- **18 of the 65 new C sources and headers are not compiled** (11 `.c`,
  7 `.h`). They are staged in the tree with their provenance intact, but they
  target APIs that have moved — or, for the 11 files staged in `21ab67574` and for
  `jtag_tcp.c` / `jtag_esp_remote.c` / `cmsis_dap_wch.c` / `aarch64_coproc_reg.c`,
  upstream APIs that never existed. Registering them needs per-backend porting work.
- **The “ready to import” TCL label was wrong.** After the subdirectory blind spot
  was fixed, a pass over the configs whose `source [find ...]` targets appeared to
  resolve flagged 12 candidates. Checked against full paths, none of them holds:
  3 (`interface/ftdi/calao-usb-a9260-c01.cfg`, `-c02.cfg`, `cc3200lp.cfg`) are
  already in the tree, just under `tcl/interface/` rather than
  `tcl/interface/ftdi/`, and the 9 TI board configs all `source [find
  interface/ti/xds100v2.cfg]` or `xds100v3.cfg`, two wrappers this tree does not
  carry (it has `ftdi/xds100v2.cfg`). Importing those 9 needs the two wrappers
  added first. The old "46 need a backend / 25 depend on a missing file / 5 were
  never fetched" split came from the same hand classification and is not
  reproduced by any tool, so it is gone. The verifiable record is
  `manifest/consolidated.json` under `not_imported` — 407 paths, each with its
  source commit — and the per-file analysis of the missing C backends is in
  `manifest/nor-driver-scan.json`.
- **Four Synopsys board configs were left out.** `board/synopsys_amla3.cfg`,
  `board/synopsys_angel4.cfg`, `board/synopsys_haps51.cfg` and
  `board/synopsys_ml509.cfg` are published in `intel/OpenOCD` but have no
  matching target file in any public repository — they are bring-up boards
  that need a Synopsys-internal build. The files that *would* have referenced
  them were therefore not imported either, so no dangling reference is left
  behind. They are listed in `manifest/consolidated.json` under
  `not_imported`.
- **Upstream naming drift is preserved, not fixed.** Where a fork published
  several spellings of the same board, the winning spelling was kept and the
  others were collapsed — the losers are recorded in
  `manifest/consolidated.json` under `path_spellings`.
- **The upstream baseline is pinned.** `manifest/upstream.json` records the
  upstream commit the tree was forked from. `tools/sync_upstream.py` reports
  the delta against any other ref.
- **Two ARC board configs will not work yet.** `arc_axc001.cfg` and
  `arc_axc002.cfg` create targets named `arc600` and `arc700`. Upstream's
  rewritten `src/target/arc.c` only provides `arcv2`, and the `arc32` family that
  would provide the other two was staged, found unbuildable and removed in
  `7ffeda047` — so those two configs name a backend this tree does not carry.
  (`arc_axc003_hs36.cfg` only needs `arcv2` and works.)
- **401 imported config files still use the deprecated `-chain-position`
  option.** Upstream's `tcl/` has already migrated to `-dap` / `-tap` (0 hits
  there); all 493 hits here are in imported third-party configs —
  `target create` 366, `dap create` 119, `pld create` 6, the rest via
  variable expansion. A mechanical rewrite resolves 69 of them, the cases where
  the object's own name equals the `-chain-position` value on the same line. The
  other 424 need a human pass, because most files define their TAP in another
  config and the right `-tap` name has to be read off that file. Nothing is broken
  today — the option still works — but it is the first thing to fix when a config
  is touched.
- **The `adi-usbmux` switch is inert.** `src/jtag/drivers/usbmux.c` is a
  Win32 named-pipe helper, not an adapter driver, but it is currently wired
  through `PROCESS_ADAPTERS`, so `--enable-adi-usbmux` exists without there
  being any `adapter_driver` called `usbmux`. Worse, `_ADI_USB_MUX_` — the
  macro the `dbgagent` driver checks to route traffic through the mux — is
  never defined anywhere, so the mux code in `adi_dbg_agent.c` compiles out
  and the `use_usbmux` command is a no-op. The source fork treats it as a
  plain `AC_ARG_ENABLE([usbmux])` helper guarded by `USE_USBMUX`; that is
  the shape this should go back to.
- **Three staged driver sets are blocked on upstream, not on this tree.** The
  survey found support for the ESP32 GPIO bit-bang probe, the WCH RISC-V debug
  probe and the Anlogic AL-Link probe. All three sets are in the tree (see the
  unwired list above), but none can be registered as-is:
  - `esp_gpio.c` / `esp_gpio.h` need the ESP-IDF GPIO and dedicated-GPIO HAL
    (`driver/gpio.h`, `hal/gpio_ll.h`), which is not part of the OpenOCD tree
    at all.
  - `wlinke.c` needs a whole SDI transport layer — an `sdi.c` / `sdi.h` pair
    under `src/jtag/` and an `sdi_ops` member on `struct adapter_driver` — that
    upstream does not have, and `wch_riscv.c` is a private fork of upstream's
    `riscv.c` that expects symbols upstream keeps `static`.
  - `al_link.c` needs a `JTAG_TDI` command type, a `DEBUG_CAP_TDI_SEQ` capability
    bit and `jtag_add_tdi_seq()` — upstream has none of them — and the CyUSB
    backend it uses is Windows-only.

  The only import candidates still blocked on missing upstream code are the
  9 Anlogic AL-Link target configs (`tcl/target/anlogic/*_al_link.cfg`).
  Everything stays in `manifest/consolidated.json` under `not_imported`, with the
  commits it came from, so the work is not lost.

---

## Contributing

Pull requests are welcome, and the bar is specific:

1. **Do not add a copy of a file upstream already has.** Check first; the
   survey found 6910 such duplicates and 7376 files that upstream had since
   absorbed.
2. **If you change an imported file, refresh the manifest.** Run
   `python tools/refresh_provenance.py` and commit the result, so the digest
   matches the file and the change is recorded rather than hidden.
3. **If you port a backend, wire it up in `tools/patch_target_groups.py`,**
   not by hand-editing `configure.ac` and `src/target/Makefile.am`. The script
   owns those blocks and will otherwise overwrite your change.
4. **Keep the tree LF.** `.gitattributes` enforces it; `tools/normalize_eol.py`
   fixes a tree that has drifted.

---

## Acknowledgements

This tree exists because 53 repositories of other people published chip
support that upstream would not take. Their commits, their code and their
license statements are preserved in `manifest/`. The original authors of
upstream OpenOCD did the work this fork is built on.

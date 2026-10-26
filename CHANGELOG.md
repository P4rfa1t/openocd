# Changelog

## Unreleased

### Fixed

- The `package` job no longer installs `texlive`. It is a 299 MB metapackage
  (1.2 GB installed) pulling in ghostscript, dvisvgm and a dozen font packages,
  and nothing in this workflow builds a PDF: `make all` needs only `makeinfo`
  from `texinfo`, and `doc/openocd.1` is a checked-in file. The 2026-10-27 run
  spent 30 minutes inside the install step retrying `fonts-urw-base35` from the
  Azure mirror, which is why the whole job looked hung; the `package-linux` job,
  which never asked for texlive, finished its install in seconds on the same
  runner. Both install steps now also carry `timeout-minutes: 15` and
  `Acquire::Retries=3 -o Acquire::http::Timeout=30`, so a stalling mirror fails
  fast and by name instead of silently eating the job.

## v0.12.0-fork.2

Second tagged release of this fork: a native Linux package next to the Windows
one, the `stm32h5x` flash driver this tree's own target config was missing, and
the first hardware-verified flash bank.

### Fixed

- `stm32h5x`: `tcl/target/stm32h5x.cfg:73` used a flash driver that had never
  been imported, so the config could be parsed but failed at runtime with
  `Error: flash driver 'stm32h5x' not found`. Imported `src/flash/nor/stm32h5x.c`
  and `.h` plus the `contrib/loaders/flash/stm32/` write algorithm, and wired all
  four registration points. Proven against a local build:
  `strings src/openocd.exe | grep -c stm32h5x` → 105 (release build: 0), and the
  target config now sources clean up to `shutdown command invoked`.
- `tcl/target/stm32h5x.cfg:73`–`:74`: the two `flash bank` lines this fork had
  commented out in `e1e45ebf8` (`# driver 'stm32h5x' not in tree`) are restored,
  so the banks exist again. Verified on real hardware (STLINK V2J46S7 →
  STM32H50xx): `flash banks` lists `stm32h5x.flash_ns` at `0x08000000` and
  `stm32h5x.flash_alias_s` at `0x0c000000`, and `flash probe 0` reports
  `device idcode = 0x10036474 (STM32H50xx - Rev Y), flash size = 128kbytes,
  dual-bank`. The file is byte-identical to the published one again, so its
  provenance record no longer carries an "edited in this fork" note. The other
  six configs touched by that commit (`aic8800` ×3, `k1921vg015`, `rs14100`,
  `stm32c5x`) stay commented until their drivers are imported.
- The `tcl/` ledger closure in `tools/sync_doc_numbers.py` now counts the
  dependency files that are actually under `tcl/` instead of extras from every
  tree, so a `src/` addition no longer breaks the `tcl/` identity.
- Six `calloc(sizeof(T), 1)` call sites in `src/jtag/drivers/linuxgpiod.c` and
  `src/flash/nor/stldr_driver.c` became `calloc(1, sizeof(T))`. gcc ≥ 14 turns
  the old argument order into `-Werror=calloc-transposed-args`, which is what
  stopped the first native Linux build; both files now compile warning-free under
  `-Werror` again (the mingw cross build had the same landmine waiting).

### Added

- `tools/audit_flash_drivers.py`: resolves the compiled NOR driver names from
  `src/flash/nor/drivers.c` and `src/flash/nor/*.c`, then scans
  `tcl/**/*.{cfg,tcl}` for `flash bank` driver references. A config-only driver
  reference now fails the gate instead of the user's session.
- Linux package job in the same workflow (`package-linux`, artifact
  `openocd-linux`): native x86_64 build against the current runner's `-dev`
  packages, installed into one relocatable tree, published with every non-glibc
  library it linked against bundled in `lib/` and an `$ORIGIN/../lib` rpath, so
  the unpacked tree runs on a host that has nothing but the C library. Built on
  `ubuntu-latest` (glibc 2.39), so the binary wants glibc ≥ 2.39. Upstream has no
  Linux job. The `release` job now waits for both package jobs and attaches both
  archives to a `v*` tag.

## v0.12.0-fork.1

First tagged release of this fork. Everything below is measured against the tree at
`main`, not asserted from memory; every number is cross-checked by
`tools/sync_doc_numbers.py --check` in CI.

### Added

- 769 third-party files imported from 53 distinct source repositories (702 under
  `tcl/`, 67 under `src/`), each pinned to the exact commit it came from and
  recorded in `manifest/PROVENANCE.json`.
- Windows package pipeline (`.github/workflows/snapshot.yml`, derived from
  upstream's workflow): `package` builds the x86_64 mingw cross build, `gate`
  runs `tools/verify_tree.py` and `tools/sync_doc_numbers.py --check`, `release`
  attaches both artifacts to a `v*` tag with `gh`.
- Audit trail: `docs/00-findings.md`, `docs/01-inventory.md`, `docs/02-usage.md`,
  `docs/03-LICENSES.md`, `docs/04-release.md`.

### Verified

- `python3 tools/verify_tree.py` → `recorded : 769 / on disk : 769 / errors : 0 /
  warns : 25 / VERIFY: PASS` (the 25 warnings are 24 files whose licence GitHub
  could not resolve plus one deliberate same-name-different-content collision).
- Integrity vs the published digests: 548 files byte-identical, 2 terminator-only
  differences, 191 with real local edits, 26 of those also terminator-normalised.
- `tcl/` is usable with no build step: 702 imported configs, 1771 `.cfg` + 47
  `.tcl` parsed, 1942 `source [find ...]` references resolved, 5 unresolved
  (all harmless: three comment lines, one upstream placeholder, one comment path
  with an extra directory).
- Build wiring: 49 of the 67 imported C sources and headers are registered in the
  Automake inputs; 18 (11 `.c`, 7 `.h`) are staged but not compiled, with the
  per-file blockers listed in `docs/02-usage.md`.

### Known gaps

- Eight TCL commands used by imported configs (`pmmw`, `mem_ap_write_reg`,
  `mem_ap_read_reg`, `reg_set`, `reg_clear`, `memap_mmw`, `hla_close`,
  `stm32n6x_boot1`; 198 uses) are defined neither here nor upstream: the source
  forks patched them into their own OpenOCD. Configs that call them fail at that
  line.
- 18 imported C files are not registered in the build (they need upstream APIs
  that were renamed or that never existed upstream); `OpenULINK/src/` ships 6
  firmware sources with its own Makefile, outside the main build.
- 401 imported configs still use the deprecated `-chain-position` option
  (493 occurrences; 69 can be rewritten mechanically, 424 need a human pass).
- 9 import candidates remain blocked upstream (ESP32 GPIO probe, WCH RISC-V
  probe, Anlogic AL-Link probe and their TCL wrappers).
- 641 of 769 imported files (83%) have no licence information in their source
  repository and need a manual header audit before commercial use.

### Changed

- Documentation numbers are generated from the tree by
`tools/sync_doc_numbers.py`; the script fails CI when any published number
drifts from the tree.

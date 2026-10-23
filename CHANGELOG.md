# Changelog

## v0.12.0-fork.1

First tagged release of this fork. Everything below is measured against the tree at
`main`, not asserted from memory; every number is cross-checked by
`tools/sync_doc_numbers.py --check` in CI.

### Added

- 767 third-party files imported from 53 distinct source repositories (702 under
  `tcl/`, 65 under `src/`), each pinned to the exact commit it came from and
  recorded in `manifest/PROVENANCE.json`.
- Windows package pipeline (`.github/workflows/snapshot.yml`, derived from
  upstream's workflow): `package` builds the x86_64 mingw cross build, `gate`
  runs `tools/verify_tree.py` and `tools/sync_doc_numbers.py --check`, `release`
  attaches the artifact to a `v*` tag with `gh`.
- Audit trail: `docs/00-findings.md`, `docs/01-inventory.md`, `docs/02-usage.md`,
  `docs/03-LICENSES.md`, `docs/04-release.md`.

### Verified

- `python3 tools/verify_tree.py` → `recorded : 767 / on disk : 767 / errors : 0 /
  warns : 25 / VERIFY: PASS` (the 25 warnings are 24 files whose licence GitHub
  could not resolve plus one deliberate same-name-different-content collision).
- Integrity vs the published digests: 548 files byte-identical, 2 terminator-only
  differences, 191 with real local edits, 26 of those also terminator-normalised.
- `tcl/` is usable with no build step: 702 imported configs, 1771 `.cfg` + 47
  `.tcl` parsed, 1942 `source [find ...]` references resolved, 5 unresolved
  (all harmless: three comment lines, one upstream placeholder, one comment path
  with an extra directory).
- Build wiring: 47 of the 65 imported C sources and headers are registered in the
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
- 639 of 767 imported files (83%) have no licence information in their source
  repository and need a manual header audit before commercial use.

### Changed

- Documentation numbers are generated from the tree by
`tools/sync_doc_numbers.py`; the script fails CI when any published number
drifts from the tree.

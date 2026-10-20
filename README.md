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

688 candidate repositories were surveyed — 499 forks of upstream plus 189
independent repositories found by search — deduplicated across repositories,
and stripped of files that are equivalent to what upstream already ships.

| | count | notes |
|---|---:|---|
| `tcl/` script files | 487 | 472 `.cfg` plus 15 `.tcl`/`.xml`/`.txt`; **work with no build changes at all** |
| `src/` C sources | 59 | 30 wired into the build, 29 staged but not yet registered |
| duplicate copies collapsed | 4109 | one winner kept per path |
| files dropped as upstream-equivalent | 99 | upstream already has them |
| candidates rejected as unusable | 107 | build-system files, non-C payloads and core internals that exist upstream under the same name |

Of the 607 unique paths the survey identified, **520 landed in the tree** and
87 did not: 68 C sources that need per-backend porting, and 19 TCL files that
reference a target or interface upstream never published (4 board, 7 interface,
8 target) — the four Synopsys bring-up boards among them. A further 26 files
came in as dependencies — a config that `source`s another config pulls the
referenced file in with it — so the tree holds 546 files in total, each one
with its own provenance entry.

Upstream ships 2203 files; this tree ships 2798.

**All 546 imported files are pinned to the exact commit they came from.** Any
file can be traced back to the fork and the commit that published it:

```bash
python - <<'PY'
import json
files = json.load(open("manifest/PROVENANCE.json", encoding="utf-8"))["files"]
entry = files["tcl/target/nucleo_l552ze.cfg"]
print(entry["source_repo"], entry["source_branch"], entry["source_commit"], entry["license"])
PY
```

The survey covered **53 distinct source repositories**.

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

30 of the 59 new C sources are wired into the build and register a working
`target_type` or `adapter_driver`:

| group | backends | build switch |
|---|---|---|
| `TARGETS_ALL` | `c28x`, `tms320`, `quark_d2000`, `quark_se`, `vortex86`, `loongarch` | `--disable-third-party-targets` turns the group off |
| `MCHP_RI4` | `mchp_ri4_bridge` | also needs libusb1 |
| `VEXRISCV` | `vexriscv` | also needs libyaml |

The remaining 29 — the `arc32` family, `adi_v5_cmsis_dap`,
`aarch64_coproc_reg`, the `blackmagic` / `ch347_jtag` / `cmsis_dap_usb` /
`jtag_tcp` drivers, and a few headers — are **present in the tree but not
compiled**. They target upstream APIs that have since moved, and registering
them would need the same porting work described below. Shipping them
unregistered is deliberate: the code is there, visible, reviewable, and
harmless until it is wired up.

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
integrity check with 543 mismatches, because the tree had been rebuilt in
text mode on Windows and every imported file was silently stored with CRLF
while the manifest described the LF original. The gate could not tell "this
was edited" from "this was checked out on a Windows host". Both are fixed now:
the tree is LF everywhere, 517 files match their published digest byte for
byte, 2 are labelled as terminator-only differences, and 27 carry real local
edits — the target API ports, the relocated `source [find ...]` paths and the
third-party driver fixes.

Files that were deliberately removed stay in the manifests under
`removed_from_tree`, with the reason and the commit that removed them. The
audit trail is bidirectional.

### Verifying

```bash
python tools/verify_tree.py
```

```
recorded : 546
on disk  : 546
errors   : 0
warns    : 26
VERIFY: PASS
```

The 26 warnings are one file whose name collides with an upstream file but
whose content differs (kept, deliberately) and 25 files whose license GitHub
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
| `tools/gen_licenses.py` | regenerate `docs/03-LICENSES.md` and `manifest/licenses.csv` |
| `tools/gen_report.py` | regenerate `docs/01-inventory.md` |
| `tools/patch_target_groups.py` | idempotent wiring of the target groups into `configure.ac`, `src/target/Makefile.am` and `src/target/target.c` |
| `tools/patch_interfaces.py`, `tools/patch_interface_h.py`, `tools/patch_makefile.py`, `tools/patch_usbmux.py` | the same kind of idempotent wiring for the adapter drivers |
| `tools/check_target_signatures.py` | compare the third-party backends' callback signatures against upstream's `target_type` |
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
| [`manifest/PROVENANCE.json`](manifest/PROVENANCE.json) | machine-readable provenance for all 546 imported files |

---

## License

The OpenOCD sources inherited from upstream are GPL-2.0-or-later; the
documentation is GFDL-1.2-no-invariants-or-later. See `COPYING` and `LICENSES/`.

**The imported third-party files are not covered by that blanket statement.**
Of 546 files, GitHub resolved 139 as GPL-2.0, 382 as `NOASSERTION` (which
means *GitHub could not determine a license* — not that it is permissive) and
25 as unresolvable. Some `NOASSERTION` files carry their own proprietary
notices, for example the Analog Devices flash algorithms, which state that the
software is proprietary to Analog Devices, Inc.

This repository therefore has **no single license of its own**. If you intend
to redistribute it, read `manifest/licenses.csv` and `docs/03-LICENSES.md`
first. The `LICENSE` file spells this out in full.

---

## Known limitations

- **29 of the 59 new C sources are not compiled.** They are staged in the tree
  with their provenance intact, but they target upstream APIs that have moved.
  Registering them needs per-backend porting work.
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
- **Three ARC board configs will not work yet.** `arc_axc001.cfg`,
  `arc_axc002.cfg` and `arc_axc003_hs36.cfg` create targets named `arc600`,
  `arc700` and `arcv2`. Upstream's rewritten `src/target/arc.c` only provides
  `arcv2`; the other two come from the `arc32` family that is staged but not
  compiled. Wiring that family up is what fixes these three configs.
- **192 imported config files still use the deprecated `-chain-position`
  option.** Upstream has no occurrence left in `tcl/`; it prints
  `DEPRECATED! '-chain-position' will be removed in the future, use '-tap'
  instead` from `src/target/arm_dap.c` and `src/target/target.c`, and the PLD
  drivers warn as well. The imported files kept the spelling their fork
  published. A mechanical rewrite only resolves 49 of the 219 occurrences
  automatically, because most files define their TAP in another config and
  the right `-tap` name has to be read off that file; the rest need a human
  pass. Nothing is broken today — the option still works — but it is the
  first thing to fix when a config is touched.
- **The `adi-usbmux` switch is inert.** `src/jtag/drivers/usbmux.c` is a
  Win32 named-pipe helper, not an adapter driver, but it is currently wired
  through `PROCESS_ADAPTERS`, so `--enable-adi-usbmux` exists without there
  being any `adapter_driver` called `usbmux`. Worse, `_ADI_USB_MUX_` — the
  macro the `dbgagent` driver checks to route traffic through the mux — is
  never defined anywhere, so the mux code in `adi_dbg_agent.c` compiles out
  and the `use_usbmux` command is a no-op. The source fork treats it as a
  plain `AC_ARG_ENABLE([usbmux])` helper guarded by `USE_USBMUX`; that is
  the shape this should go back to.
- **Three import candidates are blocked on upstream, not on this tree.**
  The survey found support for the ESP32 GPIO bit-bang probe, the WCH
  RISC-V debug probe and the Anlogic AL-Link probe, and they were fetched
  and analysed. None of them can be dropped in as-is:
  - `esp_gpio.c` / `esp_gpio.h` need the ESP-IDF GPIO and dedicated-GPIO HAL
    (`driver/gpio.h`, `hal/gpio_ll.h`), which is not part of the OpenOCD
    tree at all.
  - `wlinke.c` needs a whole SDI transport layer — an `sdi.c` / `sdi.h` pair
    under `src/jtag/` and an `sdi_ops` member on `struct adapter_driver` —
    that upstream does not have, and `wch_riscv.c` is a private fork of
    upstream's `riscv.c` that expects symbols upstream keeps `static`.
  - `al_link.c` needs a `JTAG_TDI` command type, a `DEBUG_CAP_TDI_SEQ`
    capability bit and `jtag_add_tdi_seq()` — upstream has none of them —
    and the CyUSB backend it uses is Windows-only.

  They stay in `manifest/consolidated.json` under `not_imported`, with the
  commits they came from, so the work is not lost.

---

## Contributing

Pull requests are welcome, and the bar is specific:

1. **Do not add a copy of a file upstream already has.** Check first; the
   survey found 4109 such duplicates and 99 files that upstream had since
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

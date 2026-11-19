# Layout

The emulator is component `g7250-emu` of the OpenG7250 umbrella, at `re/emu/`.
Its internal structure follows spec §13 (`G7250-emulator-test-spec-v0.5.md`).
Generated artifacts go in `re/emu/.private/` (git-ignored); locally installed
tooling in `re/emu/tools/` (git-ignored); decrypted images never enter any
repo (see `SECURITY.md`).

## Place in the umbrella

The former separate repositories map onto the umbrella
as follows (see the umbrella `README.md` for the full layout):

| Former repo | Umbrella path | Side | Role |
| --- | --- | --- | --- |
| `g7250-base` | `re/analysis/` | RE | RE findings, consumed here as data (`deps/re-analysis.lock`). `fventuri/g7250-base` itself is now an external comparison source, not a part of the umbrella. |
| `g7250-emu` | `re/emu/` (**this component**) | RE | Emulator, harness, tests, hash manifest |
| `g7250-his` | `his/` (planned) | Gate | Clean-room hardware-interface spec, the only hardware source for the firmware. Still a separate repo; migrates after review at the gate. |
| `g7250-fw` | `product/firmware/` | Product | Clean-room firmware (headless Main first). Never checked out in an RE work tree. |
| — | `testbench/` (planned) | Shared | Black-box tests against the specs |

## Component structure (§13.1)

```
re/emu/
├── README.md CLEANROOM.md SECURITY.md LICENSE AGENTS.md
├── deps/re-analysis.lock        pinned re/analysis commit (consumed as data)
├── images/                      manifest.yaml (provenance hashes) + verify.py
├── platforms/                   .resc / .repl (Main, Control, overlays, SLIP)
├── models/                      csharp/ (Renode peripherals), devices/, system/
├── harness/g7250emu/            Python: bootcore, runners, observe, imagemap
├── firmware-tests/              own small clean-room test firmwares (incl. M0)
├── tests/baseline/              m1_smoke, boot_milestone, fpga_boot, acceptance_ae
├── docs/                        design docs, this spec, status reports, architecture
├── local.config (git-ignored)   image-map path, image hashes, HIS location
├── tools/       (git-ignored)   renode-1.17.0/  pinned Renode portable (arm64)
└── .private/    (git-ignored)   runs, logs, recordings, heatmaps, build output
```

Directories from §13 not yet populated (`matrix/`, `ci/`, further `tests/`
suites) are created when the work that needs them begins (see spec §14).

## Key artifacts

- `harness/g7250emu/`: `bootcore`, `m1_run` (`--fpga`), `control_run`,
  `slip_run`, `r0_confirm`, `observe` (strict / hang / heatmap), `imagemap`,
  `platform_extras`.
- `models/csharp/`: `G7250Slaves` (EEPROM, CH394), `G7250Gpioe` (fused
  GPIOE+FPGA).
- `models/devices/`, `models/system/`: host-tested device, plant and power
  logic.
- `platforms/*.repl`: `g7250_main`, `g7250_control`, the I2C/CH394/FPGA
  overlays, SLIP.

Milestone history (M0 spike, M1 scaffolding, M2, D2, M8c) is in the status
reports under `docs/`.

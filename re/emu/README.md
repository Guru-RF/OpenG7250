# re/emu — G7250 emulator

Emulator and automated test environment for the Xiegu G7250, running the stock
Main and Control firmware on Renode. Component `g7250-emu` of the
[OpenG7250](../../README.md) umbrella, **RE side**: built from the umbrella's
own RE findings in [`re/analysis/`](../analysis/) and from public sources (see
`CLEANROOM.md` here and the umbrella [`CLEANROOM.md`](../../CLEANROOM.md)).

Imported from the former stand-alone `g7250-emu` repository at tag `emu-v1`,
with its history.

## Place in the umbrella

| Path | Relation to the emulator |
| --- | --- |
| `re/analysis/` | RE findings consumed **as data**, pinned in `deps/re-analysis.lock`. New findings about the stock firmware go to `re/analysis/docs/`, never here. |
| `his/` | Hardware-interface spec, the only channel from RE to the product side. Lives in the separate `g7250-his` repo until it migrates into `his/` after review at the gate. |
| `product/firmware/` | Clean-room firmware (formerly `g7250-fw`). Product side: never read or touched from an RE work tree. |
| `testbench/` | Black-box tests against the specs; tests relying on stock-firmware behaviour stay here. |

## No decryption

The emulator does **no** decryption. You supply already-decrypted application
images in a local folder **outside any repository**; the emulator reads that
folder through local configuration and checks each image against a hash. The
hash itself is user-supplied and kept in the git-ignored `local.config`; the
tracked `images/manifest.yaml` carries only provenance hashes of the encrypted
vendor package. Image bytes, image hashes and key material are never committed,
logged or distributed. See `SECURITY.md`.

## Status

The A–E emulator job is complete; the consolidated gate
`tests/baseline/acceptance_ae.sh` passes. Details: `docs/EMU-JOB-STATUS.md`,
`docs/HANDOVER.md`.

| Milestone | State |
| --- | --- |
| M0 platform spike (Renode go/no-go) | done, GO (`docs/M0-report.md`) |
| M1 stock Main boot to service loop | done (`docs/M1-status.md`) |
| M2 Control boot to GUI loop | done (`docs/M2-control-status.md`) |
| D1 two-machine SLIP, D2 fused GPIOE+FPGA model | done (`docs/D2-action-plan.md`) |
| M8c R0 power-model confirmation | done (`docs/M8c-R0-report.md`) |

## Local setup (all git-ignored, in `re/emu/`)

- `tools/renode-1.17.0/`: the pinned Renode portable (osx-arm64).
- `local.config`:
  ```
  image_map            = /abs/dir/outside/any/repo   # main.bin, control.bin
  image_sha256.main    = <hex>                       # user-supplied, never committed
  image_sha256.control = <hex>
  his_dir              = /abs/path/to/g7250-his      # until his/ is in the umbrella
  ```
- `.private/`: every generated artifact (runs, logs, heatmaps, build output).

## Tests (run from `re/emu/`)

```
bash tests/baseline/m1_smoke.sh          # fast gate, no image needed
bash tests/baseline/acceptance_ae.sh     # full A–E acceptance (needs image-map)
python3 harness/g7250emu/m1_run.py       # Main boot (--fpga: with the FPGA model, slow)
python3 harness/g7250emu/control_run.py  # Control boot
python3 harness/g7250emu/slip_run.py     # two-machine SLIP
```

All image-driven scripts refuse cleanly (exit 2) without an image-map.

## Layout

See `docs/REPO_LAYOUT.md` (follows spec §13). The full design is in
`docs/G7250-emulator-test-spec-v0.5.md`; the hardware/solution architecture
document is in `docs/architecture/` (written before the umbrella; its repo
names are historical).

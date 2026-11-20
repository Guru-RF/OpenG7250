# re/emu — handover

The G7250 emulator + test harness, imported from `g7250-emu` at tag **emu-v1**
(commit d64f0d4) into `re/emu/` with full history. Nothing pushed.

## State: A–E emulator job complete
Verified by the consolidated gate `tests/baseline/acceptance_ae.sh` →
**A–E ACCEPTANCE: ALL PASS** (one targeted check per item):
- A  stock Main boots to its service loop (60 s VT, no hang); A5 forced default
  IP 192.168.3.199:50001.
- B1 functional EEPROM (settings load); B2 functional CH394 on SPI6 — chip-side
  SIPR = 192.168.3.199 (A1.12).
- C/C2 Control boots to its GUI service loop (GT911 touch, codec, DMA2D) via the
  LTDC CDSR stub.
- D1 two-machine SLIP (USART2↔USART2) carries 0xC0 frames.
- D2 fused GPIOE+FPGA port: "Check complete!", version 1.0.0, DRDY-paced RX I/Q,
  zero FPGA bus errors (`m1_run.py --fpga`; `tests/baseline/fpga_boot.sh`).
- E1 dual-signal hang verdict; E2 PW-1 PowerModel confirmation (`r0_confirm.py`);
  E3 boot-milestone test; E4 HIS 00–80 (in the separate `g7250-his` repo).

## How to run the tests (from `re/emu/`)
Prereqs (all LOCAL, git-ignored — see "Clean-room" below):
- `tools/renode-1.17.0/` — the pinned Renode portable (osx-arm64).
- Decrypted stock images OUTSIDE any repo; point to them with
  `image_map = /abs/dir` in `local.config`, and put their hashes in
  `local.config` as `image_sha256.main = <hex>` / `image_sha256.control = <hex>`.
  The tracked `images/manifest.yaml` stays blank. **Never commit that hash.**
- `his_dir = /abs/path/to/g7250-his` in `local.config` (or env `G7250_HIS`) for
  the E4 check, until the HIS migrates into the umbrella `his/`.

Commands:
- Fast gate, no image needed:            `bash tests/baseline/m1_smoke.sh`
- Full A–E acceptance (needs image-map): `bash tests/baseline/acceptance_ae.sh`
- Main boot:                             `python3 harness/g7250emu/m1_run.py`
- Main boot with the FPGA model (slow, opt-in): `python3 harness/g7250emu/m1_run.py --fpga`
- Control boot:                          `python3 harness/g7250emu/control_run.py`
- Two-machine SLIP:                      `python3 harness/g7250emu/slip_run.py`
All image-driven scripts skip/refuse cleanly (exit 2) with no image-map.

## Integration points (branch emu/integrate) — closed
1. ✅ `README.md`, `AGENTS.md`, `docs/REPO_LAYOUT.md` (and `CLEANROOM.md`,
   `SECURITY.md`) adapted to the umbrella: g7250-fw → product/firmware;
   findings → `re/analysis/docs/`; HIS → `his/`.
2. ✅ Data pin switched: `deps/g7250-base.lock` → `deps/re-analysis.lock`
   (re/analysis at 71382c2); regression `acceptance_ae.sh`: **A–E ACCEPTANCE: ALL PASS** (10 of 10, 2026-11-19).
3. ✅ `local.config`, `.private/`, `tools/` copied (APFS clone) from the former
   `g7250-emu` checkout, which stays untouched as a read-only backup.

Still open: `docs/architecture/` and the model/platform source comments still
name `g7250-base`/`g7250-his`/`g7250-fw` (historical; the lock file explains
the mapping). Re-pointing E4 to `his/` happens automatically once it migrates.

## Clean-room / policy (must stay true)
- The emulator does NO decryption; decrypted images live outside any repo.
- `images/manifest.yaml` carries hashes only; the decrypted-image hash is filled
  LOCALLY and never committed (it was discarded before the import).
- Local commits on branches only; no push without an explicit go (umbrella AGENTS.md rule 4).
- The hardware-interface spec (HIS) lives in the separate `g7250-his` repo
  (sections 00–80); it migrates to `his/` only after review at the gate.
- `images/manifest.yaml` never carries a decrypted-image hash; it lives only in
  the git-ignored `local.config`.

## Key artifacts
harness/g7250emu: bootcore, m1_run (--fpga), control_run, slip_run, r0_confirm,
observe (strict/hang/heatmap), imagemap, platform_extras.
models/csharp: G7250Slaves (EEPROM/CH394), G7250Gpioe (fused GPIOE+FPGA).
models/devices + models/system: host-tested device/plant/power logic.
platforms/*.repl: g7250_main, g7250_control, the I2C/CH394/FPGA overlays, SLIP.
tests/baseline: m1_smoke, boot_milestone, fpga_boot, acceptance_ae.
docs: M1-status, M2-control-status, M8c-R0-report, EMU-JOB-STATUS, D2-action-plan.

## Continuation
Taken over by the `openg7250-emu` session, which closed the integration points.

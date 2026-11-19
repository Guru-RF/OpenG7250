# g7250-emu

Emulator and automated test environment for the Xiegu G7250. **Clean-room,
RE side:** built from the public RE documentation in `g7250-base` and from
public sources (see `CLEANROOM.md`).

The projects are kept as separate local repositories under `~/Repos/on8st/`;
there is **no shared GitHub organisation** for now. See `docs/REPO_LAYOUT.md`.

## No decryption

The emulator does **no** decryption. You supply already-decrypted application
images in a local folder **outside any repository**; the emulator reads that
folder through local configuration and checks each image against a **hash-only
manifest** (`images/manifest.yaml`, verified by `images/verify.py`). Image
bytes and key material are never committed, logged or distributed. See
`SECURITY.md`.

## Status

| Milestone | State |
| --- | --- |
| **M0** platform spike (Renode go/no-go) | **done — GO.** See `docs/M0-report.md` |
| M1 stock Main boot | next |

M0 result in one line: Renode 1.17.0's `cortex-m7` model has the dp-FPU, MPU,
DWT and cache-maintenance behaviour the stock firmware needs, and emulation
speed clears the threshold; the FPGA/GPIO path must be a fused model (risk R3).

## Quickstart (no images needed for M0)

```
make -C firmware-tests/m0                         # build the clean-room M0 test firmware
python3 harness/g7250emu/m0_run.py --runs 3       # run on pinned Renode, measure, report
```

Requires `arm-none-eabi-gcc` and the pinned Renode in `tools/` (both local,
git-ignored where binary). Generated output goes to the git-ignored
`.private/`.

## Layout

See `docs/REPO_LAYOUT.md` (follows spec §13). The full design is in
`docs/G7250-emulator-test-spec-v0.5.md`; the hardware/solution architecture
document is in `docs/architecture/`.

# Clean-room rules (g7250-emu)

This repository is the **reverse-engineering (RE) side** of the G7250 project.
It is deliberately kept separate from the clean-room firmware so that the new
firmware can never be contaminated by implementation detail taken from the
stock images. These rules apply to every contributor — human or agent.

See spec §12 (`docs/G7250-emulator-test-spec-v0.5.md`) for the full rationale.

## What lives here (RE side)

- Emulator platform models, the test harness, the test suites and the
  hash-only image manifest.
- Design docs and model docs, each citing its public or RE source.
- A pinned snapshot of `g7250-base` consumed **as data** (`deps/g7250-base.lock`).

## What must NOT cross into the firmware repo (`g7250-fw`)

- Decrypted stock images, disassembly, traces, heatmaps, memory dumps,
  register maps derived from the images — none of it.
- The only channel from RE knowledge to the firmware is the reviewed
  **hardware-interface spec** (`g7250-his`): hardware facts only, no stock
  implementation detail. Models in this repo cite the HIS paragraph per
  feature.

## No decryption in this tooling

The emulator performs **no decryption**. The user supplies already-decrypted
application images in a local image-map **outside any git work tree**; the
emulator checks them against `images/manifest.yaml` (hashes only) and refuses
to run on a mismatch. See `SECURITY.md`.

## Commits

- Local commits on branches only; **no push and no PR without an explicit go**
  from the owner.
- Identity and trailer rules follow the owner's conventions (author ON8ST).
- Findings about the stock firmware go as RE docs to `g7250-base`, never here.

## Legal

A Belgian IP lawyer is consulted before any publication and before firmware
work (`g7250-fw` F2). Nothing — images, packages, derived dumps — is ever
distributed. Because no decryption loader exists in this tooling, the tooling
itself raises no Art. 7(1)(c) (EU Directive 2009/24/EC) concern; obtaining and
using the images remains the user's responsibility under that advice.

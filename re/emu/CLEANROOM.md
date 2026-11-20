# Clean-room rules (re/emu)

This component is on the **reverse-engineering (RE) side** of the OpenG7250
umbrella. It is deliberately kept separate from the clean-room firmware so that
the new firmware can never be contaminated by implementation detail taken from
the stock images. These rules apply to every contributor — human or agent — in
addition to the umbrella [`CLEANROOM.md`](../../CLEANROOM.md).

See spec §12 (`docs/G7250-emulator-test-spec-v0.5.md`) for the full rationale.

## What lives here (RE side)

- Emulator platform models, the test harness, the test suites and the
  hash-only image manifest.
- Design docs and model docs, each citing its public or RE source.
- A pinned snapshot of `re/analysis/` consumed **as data** (`deps/re-analysis.lock`).

## What must NOT cross into the firmware (`product/firmware/`)

- Decrypted stock images, disassembly, traces, heatmaps, memory dumps,
  register maps derived from the images — none of it.
- The only channel from RE knowledge to the firmware is the reviewed
  **hardware-interface spec** (`his/`; for now the separate `g7250-his` repo):
  hardware facts only, no stock implementation detail. Models in this
  component cite the HIS paragraph per feature.

## No decryption in this tooling

The emulator performs **no decryption**. The user supplies already-decrypted
application images in a local image-map **outside any git work tree**; the
emulator checks them against `images/manifest.yaml` (hashes only) and refuses
to run on a mismatch. See `SECURITY.md`.

## Commits

- Local commits on branches only; **no push and no PR without an explicit go**
  from the owner.
- Identity and trailer rules follow the owner's conventions (author ON8ST).
- Findings about the stock firmware go as RE docs to `re/analysis/docs/`, never here.

## Distribution

Nothing — images, packages, derived dumps — is ever distributed. No decryption
loader exists in this tooling; it decrypts, encrypts and packages nothing.
Obtaining and using the images remains the user's responsibility. Pushes and
PRs need an explicit go from the repository owner (umbrella `AGENTS.md`
rule 4).

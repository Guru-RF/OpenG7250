# Roadmap

| Phase | Component | Goal |
|---|---|---|
| 1. RE | `re/analysis` | Understand startup, hardware interfaces and protocols of the V1.0.1 images; document findings |
| 2. Emulator | `re/emu` | Run the stock images against platform models; hash-checked images; regression suite |
| 3. HIS | `his` | Reviewed hardware-interface spec with hardware facts only |
| 4. Firmware | `fw` | Clean-room firmware "G7250-P1", built from the HIS and public datasheets |

## Open integration steps

- Add `g7250-emu` as submodule `re/emu/` once its current work is finished, and
  switch its data pin (`deps/g7250-base.lock`) from `g7250-base` to `re/analysis`,
  with a regression run.
- Create `g7250-his` and `g7250-fw` with their own remotes and add them as
  submodules `his/` and `fw/`.

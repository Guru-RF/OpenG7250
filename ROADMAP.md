# Roadmap

| Phase | Component | Goal |
|---|---|---|
| 1. RE | `re/analysis` | Understand startup, hardware interfaces and protocols of the V1.0.1 images; document findings |
| 2. Emulator | `re/emu` | Run the stock Main and Control images against platform models; hash-checked images; regression suite |
| 3. HIS | `his` | Reviewed hardware-interface spec with hardware facts only |
| 4. Spec | `product/spec` | Network interface spec based on the public OpenHPSDR protocols, with own board id and fields for the G7250; details in `product/spec/` |
| 5. Test bench | `testbench` | Automated black-box tests against the specs; design of the HIL test bench |
| 6. Firmware | `product/firmware` | New firmware, starting with a headless Main for AetherSDR, built from `his` and `product/spec` |
| 7. Website | `website` | Possibly later |

## Open integration steps

- Add `g7250-emu` as submodule `re/emu/` once its current work is finished, and
  switch its data pin (`deps/g7250-base.lock`) from `g7250-base` to `re/analysis`,
  with a regression run.
- Gate review of `his/` done: cleared by gate review 2
  (`re/analysis/docs/his-gate-review-2.md`; review 1 in
  `re/analysis/docs/his-gate-review-1.md`). The product side may read `his/`.
  From now on every change to `his/` goes through the gate before the product
  side reads it.
- Create `g7250-testbench` and `g7250-firmware` with their own remotes and add
  them as submodules. (`g7250-spec` is merged into `product/spec/`.)
- Decide which parts of the emulator's current harness and tests move to
  `g7250-testbench`.

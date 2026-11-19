# 0019 — The reference model lives on the product side; the test bench stays black-box

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19

## Context

Every part of the spec gets a reference model and conformance tests before it is built in
firmware (0001, design note item 5). The umbrella repository plans `testbench/` as a shared
submodule `g7250-testbench` for "automated black-box tests against the specs" and the design
of the hardware-in-the-loop test bench (umbrella README and ROADMAP). Shared means that the
reverse-engineering side may work in it too.

The reference model is a simulated G7250-P2: an executable version of the spec, which the
conformance tests run against before real firmware exists.

## Options considered

### A. Reference model on the product side, e.g. `product/refmodel/` (chosen)

- For: the model is an executable form of the spec and therefore product work. It is built
  only from the spec and the HIS, in a work tree without `re/` (umbrella AGENTS.md rule 1).
- For: the test bench stays purely black-box: it knows the spec and talks to a network
  endpoint, whether that is the reference model or a radio.
- For: the smallest risk that RE knowledge leaks into the model.
- Against: one more product-side location to maintain.

### B. Reference model inside the shared test bench

- For: model and tests in one place.
- Against: anyone working in the shared test bench could shape the model, including from
  the RE side. The model would then no longer be provably clean-room.

### C. No separate model; tests only against firmware

- Against: contradicts "spec first" (0001). Tests could only run once firmware exists.

## Decision

Option A. The reference model lives on the product side (proposed path `product/refmodel/`).
The shared test bench contains only black-box tests that take the spec as input and run
against a network endpoint.

## Consequences

- Conformance tests are specified in the spec (Annex X3 and the part C tests) with id,
  procedure, expected result and source requirement, so the test bench can implement them
  from the spec alone.
- Creating `product/refmodel/` and the `g7250-testbench` submodule needs a go from ON8ST and a
  work tree that contains them (none of the current checkouts do).
- The model and the tests are licensed under 0018 (code: GPL-3.0-or-later unless a vendor SDK
  forbids it; the model needs no vendor SDK).

## Sources

- Discussion with ON8ST, 2026-11-19.
- Umbrella README.md and ROADMAP.md (product-side checkout): `testbench/` "Shared",
  "Automated black-box tests against the specs".
- Decisions 0001, 0018.

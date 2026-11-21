# 0027 — The test bench is a folder of the umbrella repository, not a separate submodule

- Status: accepted (ON8ST, 2026-11-20: "als deel van de openg7250 repo. Dat is voorzien in de
  structuur")
- Date: 2026-11-20
- Amends: 0019 (accepted), only where it names the test bench a submodule `g7250-testbench`.

## Context

0019 placed the reference model on the product side and kept the shared test bench
black-box. It described the test bench, following the umbrella README and ROADMAP at that
time, as a shared submodule `g7250-testbench` at `testbench/`, and said that creating it needs
a go from ON8ST. ON8ST decided on 2026-11-20 that the test bench is part of the OpenG7250
umbrella repository itself, as already foreseen in its structure.

## Decision

1. The test bench lives at `testbench/` in the OpenG7250 umbrella repository, as an ordinary
   folder. There is no separate `g7250-testbench` repository and no submodule.
2. Everything else in 0019 stands: the test bench contains only black-box tests that take the
   spec (Annex X3, part C tests) as input and run against a network endpoint, the reference
   model, the radio or another endpoint, and the reference model stays at `product/refmodel/`.
3. The product-side work tree currently holds only `product/` (sparse checkout, cone mode).
   Work on `testbench/` from the product side needs `testbench` added to that checkout; the
   openg7250 session arranges it when the test bench work starts.
4. Code in `testbench/` follows 0018 (GPL-3.0-or-later).

## Consequences

- Handover "Still open" item 3 and 0019 Consequences read "the `testbench/` folder of the
  umbrella repository" instead of "the `g7250-testbench` submodule".
- No new repository is created.

## Sources

- ON8ST, 2026-11-20, in this session.
- Decisions 0018, 0019.

# 0037 — g7250ctl in Rust, sharing the protocol crate

- Status: proposed (advice recorded on ON8ST's request, 2026-11-20; ON8ST may still change it)
- Date: 2026-11-20
- Builds on: 0026 (g7250ctl as reference implementation), 0033 (firmware in Rust).

## Decision (proposed)

1. `g7250ctl` is written in Rust.
2. It shares the protocol crate (message formats, encoding, status codes of spec part A) with
   the firmware and the reference model.
3. It ships as one static binary for Linux, macOS and Windows.

## Note on independence

0026 makes `g7250ctl` the reference implementation and 0019 makes the reference model an
independent executable form of the spec. If the CLI, the firmware and the model share one
protocol crate, a mistake in that crate is the same in all three and the conformance tests
between them cannot see it. The black-box tests in `testbench/`, written from the spec text
(0027, 0034), are then the independent check; they MUST NOT use the shared crate.

## Consequences

- `product/tools/g7250ctl/README.md` and `product/refmodel/README.md` name Rust.
- `testbench/README.md`: tests do not use the shared protocol crate.

## Sources

- ON8ST, 2026-11-20, relayed by the openg7250 session; decisions 0019, 0026, 0027, 0033, 0034.

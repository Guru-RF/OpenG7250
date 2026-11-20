# G7250-P2 reference model

An executable model of a G7250 running the new firmware, built from the specification only, so
that the conformance tests can run before real firmware exists.

- Status: **planned. No code yet.** The project is in the spec phase; code starts in the build
  phase (decision 0028, Decision 4).
- Source of truth: `product/spec/` (network-interface spec parts A–C, decisions,
  `spec/register-map.yaml`). The model is built only from the spec and the cleared HIS. Never
  from the reverse-engineering side (decision 0019).
- Used by: the black-box tests in `testbench/` of the umbrella repository (decision 0027) and
  the management CLI `product/tools/g7250ctl/` (decision 0026).

## Planned scope, in order

1. **Management channel** (spec part A, A1): UDP 7251; identification, statistics, the update
   commands with two simulated image slots, the streaming installer for a foreign image
   (A1.8a item 3), authentication with the secret, the status codes of Table A1-3. Tests:
   T-A1-*.
2. **G7250-P2 discovery and register map** (part B): discovery reply with board type 200, the
   register map generated from `spec/register-map.yaml`.
3. **RX streams**, then the **TX safety core** (part A3, B10): arm, keying, limits, faults, with
   simulated sensors.
4. **TCI profile** (part C), for level 2.

The model simulates hardware behaviour only where the spec needs it (for example forward power
that decays after an unkey, for T-A1-51). It never models how the stock firmware behaves, and
it tests the foreign-image path with a synthetic opaque image (spec A1.8a item 10).

## Language (decisions 0033, 0037, proposed)

Rust, an independent implementation written from the spec only: it never uses the firmware's
protocol crate, and the firmware never uses this code (0037).

## Licence

GPL-3.0-or-later, © 2026 ON8ST (decisions 0018, 0019).

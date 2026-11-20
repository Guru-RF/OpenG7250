# G7250-P2 reference model

An executable model of a G7250 running the new firmware, built from the specification only, so
that the conformance tests can run before real firmware exists.

- Status: planned. No code yet.
- Source of truth: `product/spec/` (network-interface spec parts A–C, decisions,
  `spec/register-map.yaml`). The model is built only from the spec and, once it has passed its
  gate, the HIS. Never from the reverse-engineering side (decision 0019).
- Used by: the black-box tests of the shared test bench (`testbench/`, planned) and the
  management CLI `product/tools/g7250ctl/` (decision 0026).
- Licence: GPL-3.0-or-later, © 2026 ON8ST (decisions 0018, 0019).

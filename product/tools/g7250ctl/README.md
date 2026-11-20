# g7250ctl

Command-line tool for managing the firmware of a G7250 running the new firmware (G7250-P2):
discover and identify, show version and state, install an image (new firmware or an
owner-supplied factory image), verify, activate, abort, rollback, return to factory firmware,
enter vendor recovery, read logs and set the first management secret.

- Status: planned. No code yet.
- Protocol: the management protocol of `product/spec/spec/network-interface.md` part A
  (A1.1a, A1.3–A1.10, A1.8, A1.8a). This tool is its reference implementation; any gap found
  while building it is fixed in the spec first (decision 0026, proposed).
- Tests: every A1 conformance test of Annex X3, first against the reference model in
  `product/refmodel/` (decision 0019), then against the radio.
- AetherSDR's firmware page follows on the same protocol (`product/spec/spec/annex-aethersdr.md`,
  Q-O4).
- The first install on a radio still running factory firmware cannot use this protocol; it
  depends on HIS-19 (decision 0025, proposed).
- Clean room: built only from `product/spec/` and, once it has passed its gate, the HIS. Never
  from the reverse-engineering side.
- Licence: GPL-3.0-or-later, © 2026 ON8ST (decisions 0018, 0026).

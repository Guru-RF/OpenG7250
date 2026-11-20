# 0026 — Firmware management lives on the host side: protocol in the spec, CLI as reference, AetherSDR on the same protocol

- Status: accepted (ON8ST, 2026-11-20, after review on the decision page)
- Date: 2026-11-20
- Builds on: 0008 (management channel), 0024 (switching between stock and new firmware),
  0025 (one installation path on the main unit), 0019 (reference model), 0018 (licences),
  0013 (AetherSDR as integration route).

## Context

ON8ST's direction of 2026-11-20, relayed by the openg7250 session on his request:

1. Firmware management lives on the host side, in host software such as AetherSDR: install
   new firmware, return to stock, show the version and state.
2. Separately, a simple standalone CLI tool for development and test that implements the same
   protocol.
3. Suggested order: the management protocol (the `RETURN_TO_STOCK` / `ENTER_VENDOR_RECOVERY`
   commands of 0024 plus image transfer, verify and version query) is defined in `product/spec`
   first; the CLI is its first, reference implementation; AetherSDR integration follows on the
   same protocol.
4. Decide where the CLI lives.

The management channel and its commands are already specified in spec part A (A1, Table A1-2:
`IDENTIFY`, `GET_STATS`, the `UPDATE_*` commands, `ROLLBACK`, `RETURN_TO_STOCK`,
`ENTER_VENDOR_RECOVERY`; A1.8 update, A1.8a return to stock; 0008, 0020 §27, 0024). The radio
side never had a user interface for updates: the controller is out of scope (0023) and the
installation path must not need it (0025).

## Options considered

### A. Protocol in the spec; CLI as reference implementation; AetherSDR on the same protocol (chosen)

- For: one protocol, specified once, with conformance tests; every host that implements it
  can manage the firmware.
- For: the CLI is small, scriptable and testable against the reference model (0019) before
  hardware exists; it shows that the specification is implementable and gives AetherSDR a
  worked example.
- For: AetherSDR stays the user-facing route (0013) without owning the protocol.
- Against: two host implementations to keep in step with the spec. Mitigated by the conformance
  tests and by the CLI being the reference.

### B. AetherSDR only

- For: one implementation.
- Against: no tool for development, test and recovery when AetherSDR is not available or not
  yet integrated; ties firmware management to an external project's release cycle.

### C. CLI only

- For: simplest.
- Against: against ON8ST's direction; normal users would need a command line to update or
  return to stock.

### D. A management user interface in the firmware (web page)

- Against: already rejected (0008 T4: a browser interface, if ever, is a PC tool, not in the
  firmware); costs a socket and code on a small processor (HIS-18).

## Decision

Option A.

1. **Protocol.** The management protocol of spec part A (A1.3–A1.10, Tables A1-1 to A1-3) is the
   single protocol for firmware management. It covers at least: identification and version
   query (`IDENTIFY`, record fields), image transfer (`UPDATE_BEGIN`, `UPDATE_BLOCK`), verify
   (`UPDATE_VERIFY`), activation (`UPDATE_ACTIVATE`), state (`UPDATE_STATUS`), abort and rollback
   (`UPDATE_ABORT`, `ROLLBACK`), and return to stock (`RETURN_TO_STOCK`,
   `ENTER_VENDOR_RECOVERY`, and an owner-supplied stock image through the same update path,
   0024, 0025). Any gap found while building the CLI is fixed in the spec first.
2. **CLI.** A standalone command-line tool, working name `g7250ctl`, is the first and reference
   implementation of that protocol. It offers: discover and identify, show version and state,
   install an image (new firmware or an owner-supplied stock image, 0025), verify, activate,
   abort, rollback, return to stock, enter vendor recovery, read logs, and set the first secret
   (0008). It is tested against the reference model (0019) and later against the radio.
3. **Location.** The CLI lives at `product/tools/g7250ctl/` in the umbrella repository, on the
   product side next to `product/spec/` and the planned `product/refmodel/` (0019). It is
   separate from `product/spec/tools/`, which holds the tools that check the spec itself.
   Creating the directory needs a go from ON8ST and a work tree that contains it (the current
   sparse checkout holds only `product/spec/`).
4. **AetherSDR.** AetherSDR's integration (annex Q-O4: a separate tool or a page) uses the same
   protocol: install new firmware, return to stock, show version and state. It follows the CLI,
   not the other way round. Upstream work needs a go from ON8ST (AGENTS.md rule 6).
5. **Licence.** The CLI is host software written by this project: GPL-3.0-or-later, © ON8ST,
   consistent with 0018 and compatible with AetherSDR (GPL-3.0).

## Consequences

- Spec part A states that firmware management is done by host software over the management
  channel, names the CLI as reference implementation, and adds conformance tests that the CLI
  must pass against the reference model.
- The annex "Changes needed in AetherSDR" answers Q-O4: a firmware page in AetherSDR on the same
  protocol, after the CLI.
- **Open dependency — first install.** The very first install, on a radio still running the
  stock firmware, cannot use this protocol, because the stock firmware does not implement it.
  How that step works (the stock update path, its interface, whether it needs the controller,
  the image the main unit accepts) depends on HIS-19 and comes only through the HIS after its
  gate (0025 R4/R5). Until then the CLI covers new → new and new → stock; stock → new is open.
- Design note §8 and the handover list `product/tools/g7250ctl/` as planned work next to
  `product/refmodel/`.

## Sources

- ON8ST, 2026-11-20, relayed by the openg7250 session on his request.
- Decisions 0008, 0013, 0018, 0019, 0023, 0024, 0025; spec part A A1.

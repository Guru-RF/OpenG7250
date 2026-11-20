# Changelog — G7250-P2 network-interface spec

- © 2026 ON8ST, CC BY 4.0 (see `LICENSE.md`)

All dates 2026-11-19. Decision numbers refer to `decisions/`.

## After rc4 (on branch spec/draft, not yet tagged)

- ON8ST reviewed rc4 and accepted 0020–0024 (2026-11-20).
- 0023: only the main-unit firmware is replaced; the controller keeps its stock
  firmware and is out of scope (part A "Scope of the firmware", B1.9).
- 0024: switching between stock and new firmware is reversible; the vendor's own
  update and recovery path is never disabled; an owner-supplied stock image can be installed
  from the new firmware; `RETURN_TO_STOCK` and `ENTER_VENDOR_RECOVERY` management commands
  (A1.8a).
- `review-guide-rc4.md` for ON8ST's review.

## rc4 — release candidate 4

- Fixes from the full reviews of rc3 and the rc4 draft (0022 §74–§87, 0021 §43–§46): keyer
  elements and the CW hang delay count as keyed for RF-path purposes; CW break-in set/clear and
  CW with PTT (B10.5b); "RF while not keyed" in element gaps; restart by the run bit keeps the
  RX-side settings of the same host ([P2] "Detailed operation"); frequency encoding fixed to a
  phase word on a virtual 122.88 MHz clock; limit reaction times; write-session timer only
  refreshed by authenticated requests; one commanded reset at a time; TCI: TX source frozen
  while keyed, TX_ENABLE as permission, AetherSDR rewrites TCI session state after every P2
  session end, DUC0 is the effective TX frequency on level 1, level-1 CW hang bounded at 2 s.

## rc3 — release candidate 3

- Fixes from the reviews of rc2 (0022 §62–§73, 0021 §27–§42): PEP estimate from the DUC
  samples when the detector has no PEP; DUC FIFO bounded while unkeyed; TX settings reset at
  session end; bounded RF-gone waits; factory reset atomic; management reply caps; TCI keyed
  liveness table covering every source; AetherSDR never arms on a TX request; level-1 mode
  class follows the transmitted signal.

## rc2 — release candidate 2

- Fixes from the independent review of rc1 (0022 §33–§51) and of the rc2 draft (0022 §52–§61):
  RF path set for the TX frequency at every key (split included), set-up phase so the arm is
  reachable for standard P2 hosts, ordering of High Priority packets (numbered and unnumbered
  hosts), CWX bit meaning and key-down cap, ATU tune retries and state after a failed tune,
  commanded resets only after RF is gone (bounded wait), one conservative power mapping for
  every limit in force, DHCP address changes end the session, P2 accepted from the own subnet
  only, factory-reset scope.
- Tools: register map lists G7250 extensions and checks itself (lint L8).

## rc1 — release candidate 1 (tag `spec-rc1`)

Covers `network-interface.md` (parts A and B), `part-c-tci-profile.md` (part C),
`annex-aethersdr.md`, `glossary.md` and the generated `register-map.yaml` and
`traceability-auto.md`.

- Every requirement cites a source; every remaining TBD names a HIS question (or G6).
  Checked by `tools/spec_lint.py` (0 findings, 299 test ids), `tools/trace.py` (every
  decision cited or explained), `tools/budget.py` (all required scenarios within the 60 % SPI
  target).
- Contains proposed decisions 0020 (rc1 detail choices), 0021 (TCI profile choices) and 0022
  (fixes from two independent reviews and a byte-by-byte check against P2 V4.4), for review by
  ON8ST.
- Open: hardware values from the HIS (`open-questions-his.md`, HIS-01 to HIS-20).

## History of the drafts

| Part | Draft | What changed |
|------|-------|--------------|
| A, B | 1 | M1 sections: transport, discovery, session, RX IQ; annexes for P2 differences, clarifications and tests. |
| A, B | 2 | Aligned with accepted decisions 0003–0008: capability record, streams, telemetry, safety, management channel. |
| A, B | 3 | All open points without a HIS dependency resolved (0020); B11 error handling written; register addresses. |
| A, B | 4 | First independent review and P2 byte check fixed (0022 §1–§21). |
| A, B | 5 | Second review of the transmit side fixed (0022 §22–§32): key rule, relay switching sequence, ATU tune cycle, CW backstop, fault hold-off, `LIMIT_INHIBIT`. |
| C | 1 | TCI 2.1 profile: transport, initialization, command subset, `G7250_` extensions, multiple clients, safety. |
| C | 2 | Open points without a HIS dependency resolved (0021 §1–§17). |
| C | 3 | First review fixed (0021 §18–§26): keyed liveness without Pong, part B symbols verbatim, arm holder. |
| C | 4 | Second review fixed, rules referenced from part A/B (0022 §22–§32). |
| Annex | 1–2 | Changes needed in AetherSDR, from its public source; follow-ups from parts B and C. |

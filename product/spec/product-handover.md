# Product handover (g7250-spec → product/spec/)

Date: 2026-11-19. Source of everything below: the start brief and the discussion with ON8ST
on 2026-11-19, as recorded in `decisions/`.

## Where things stand

- Spec release candidate **rc4** is tagged locally as `spec-rc4` on branch `spec/rc1`
  (tracks origin/spec/rc1; not pushed). `spec-rc1` (93c247b) is the earlier pushed tag.
- rc4 passed repeated independent reviews; the last verification found OPEN HIGH 0,
  OPEN MEDIUM 0. Remaining LOW clarifications for a later pass: which key starts the zero-run
  count, the DUC sample tap before TX DC/IQ correction (HIS-18), leakage below `P_rf_off`
  (HIS-11), the zero-sample rule on level 2, CWX request going to 0 through bit [0], DUC rate
  change advice, and one key-latency definition with the DUC FIFO between the A3.1a key and
  the PTT key.
- Files: `spec/network-interface.md` (parts A, B), `spec/part-c-tci-profile.md`,
  `spec/annex-aethersdr.md`, `spec/glossary.md`, `spec/CHANGELOG.md`, generated
  `spec/register-map.yaml` and `spec/traceability-auto.md`; `design-note.md` draft 4 (rc4).
- Checks: `python3 tools/spec_lint.py` (0 findings, 483 test ids), `python3 tools/trace.py`,
  `python3 tools/budget.py`, `python3 tools/regmap.py` (`--check` to verify).
- Level 1 is G7250-P2: openHPSDR Protocol 2, board type 200 (0016, 0002).
- Clean room: do not fetch, check out or read `his/` or the `his/integrate` branch until the RE
  session reports that the HIS has passed its gate (it has not yet).

## Decisions

| #    | Title | Status |
|------|-------|--------|
| 0001 | Structure of the design note and the network-interface spec | accepted |
| 0002 | Board type of G7250-P2: 200 (0xC8), chosen ourselves; openHPSDR to be informed | accepted; notice sent as TAPR/OpenHPSDR-Firmware#6 |
| 0003 | Capability block: short P2 discovery reply (board type 200, never 254/255) + read-only capability record in the G7250 register map | accepted |
| 0004 | Streams: one DDC at 48–384 ksps (384 only if SPI ≥ ~50 MHz), TX IQ 24-bit 192 ksps, mic only if HIS-17, no wideband yet; unsupported requests refused | accepted |
| 0005 | Control fields on P2: standard fields where identical; G7250 functions and TX safety in a G7250 register map (P2 memory-mapped registers) | accepted |
| 0006 | Telemetry: standard P2 status fields where identical, calibrated and formula-compatible; G7250 sensors and state in register map | accepted |
| 0007 | Watchdog and safety: token-based TX arm, 13 disarm events, keyed timeout 300 ms, takeover always allowed but disarms, limits table, two fault classes | accepted |
| 0008 | Management channel: own UDP port on the 8th socket, challenge-response writes, signed updates with rollback, never keys the radio | accepted |
| 0009 | Stay as close to the standard protocol as possible (now P2, see 0016) | accepted |
| 0010 | No compatibility modes for now (HL2 rejected, ANAN out of scope for now) | accepted |
| 0011 | Two-level product interface: L1 G7250-P2 (was G7250-P1, see 0016) / L2 TCI with on-board DSP. Single owner, shared safety core, L2 only after gate G6 | accepted |
| 0012 | Every integration supports full functionality including TX; no SoapySDR module | accepted |
| 0013 | AetherSDR is the initial integration route for level 1; no separate bridge | accepted |
| 0014 | One TCI profile (spec part C) for AetherSDR on level 1 and the firmware on level 2 | accepted |
| 0015 | Host that does not know the board type: RX only; TX needs an arm in the G7250 register map | accepted |
| 0016 | Level 1 uses openHPSDR Protocol 2 instead of Protocol 1; AetherSDR P2 support built by us if needed | accepted. Revises 0001, 0009, 0011; 0005 and 0015 rewritten |
| 0017 | G7250-P2 offers no DDC audio stream (port 1028); frees one of the 8 CH394Q sockets | accepted |
| 0018 | Licences: documents CC BY 4.0, firmware GPL-3.0-or-later (Apache-2.0 if the vendor SDK forbids GPL), AetherSDR backend GPL-3.0; © ON8ST | accepted |
| 0019 | Reference model on the product side (`product/refmodel/`); shared test bench stays black-box | accepted |
| 0020 | rc1 detail choices: ports 7250 (register map) and 7251 (management), address map, codes, timers, B11 error handling | proposed (review at rc1) |
| 0021 | TCI profile choices: port 50001, PROTOCOL ExpertSDR3,2.1, DEVICE G7250, TX policy, mode class from MODULATION, FLOAT32 IQ, LAN restrictions | proposed (review at rc1) |
| 0022 | rc1 review fixes: RF path frozen while keyed, takeover procedure, non-owner TX IQ discarded, fault classes, limit tiers, SWR fold-back, level-switch procedure, rate limits | proposed (review at rc1) |

All numbers 0001–0018 are now in use.

## Open questions for ON8ST

Decided on 2026-11-20 (ON8ST):
- 0020, 0021 and 0022 stay **proposed** until ON8ST has reviewed rc4 himself and comes back
  with comments.
- `.claude/settings.json` stays as it is (the deny rules naming the decrypted-firmware folder
  remain, also in the history).
- **Go** for the RE session to push branch `spec/rc1` and tag `spec-rc4` to the fork
  (on8st/OpenG7250). The spec PR to Guru-RF follows after PR #1, with a separate go.

Still open:
1. ON8ST's review of rc4 and the acceptance of 0020–0022.
2. Go for an AetherSDR RFC issue (annex Q-O1); shared P2 refactor vs. self-contained backend
   (Q-O2).
3. Go to create `product/refmodel/` and the `g7250-testbench` submodule (0019).

Watch TAPR/OpenHPSDR-Firmware#6 for a reply on board type 200.

## Open questions for the HIS

In `open-questions-his.md` (HIS-01 to HIS-19).

## Next step

1. (Done: 0013, `sources.md`.) Still open in `sources.md`: read the Radioddity product page
   (HTTP 429 on 2026-11-19), read the TCI 2.1 PDF and check its terms, find a manufacturer
   manual.
2. (Done: `open-questions-his.md`.)
3. (Done: `design-note.md` draft 1; review by ON8ST.)
4. (Done, accepted: 0003, 0004, 0006, 0007, 0008.) Next: update the spec draft to the
   accepted decisions (B4 capability block, sample rates, telemetry, transmit, register map,
   B3.9 Set IP now accepted as P2), and update the illustrated design note.
5. (Draft 1 done: `spec/network-interface.md`.)

# Product handover (g7250-spec → product/spec/)

Date: 2026-11-19. Source of everything below: the start brief and the discussion with ON8ST
on 2026-11-19, as recorded in `decisions/`.

## Where things stand

- Spec release candidate rc1 is being finished on branch `restructure/umbrella` (local only).
  Files: `spec/network-interface.md` (parts A and B, draft 4), `spec/part-c-tci-profile.md`
  (TCI profile), `spec/annex-aethersdr.md`, `spec/glossary.md`, generated
  `spec/register-map.yaml` and `spec/traceability-auto.md`; `design-note.md` draft 2.
- Checks: `python3 tools/spec_lint.py` (0 findings required), `python3 tools/trace.py`,
  `python3 tools/budget.py`, `python3 tools/regmap.py` (regenerate after B8 or A1-2 changes).
- Level 1 is G7250-P2: openHPSDR Protocol 2, board type 200 (0016, 0002). Analyses in
  `analysis/`. Primary product source: the G7250 operation manual (`sources.md`).
- Before any push: `.claude/settings.json` in the history contains local paths and the name of
  a decrypted stock-firmware folder; it must be removed from the history or the push must be a
  cleaned, squashed tree (ON8ST to decide).

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

None blocking. 0003–0008 were accepted on 2026-11-19 after an interactive round (answers
recorded in each file under "Resolved"). Small items still open are listed in those files
under "Still open".

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

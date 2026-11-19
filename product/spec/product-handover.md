# Product handover (g7250-spec → product/spec/)

Date: 2026-11-19. Source of everything below: the start brief and the discussion with ON8ST
on 2026-11-19, as recorded in `decisions/`.

## Where things stand

- The g7250-spec branch `docs/initial-structure` has been subtree-merged into
  `product/spec/` in the main repo (merge commit a29155b, local, not pushed).
- `design-note.md` exists as draft 1 (2026-11-19), for review by ON8ST.
  `spec/network-interface.md` exists as draft 1 (part B for M1: B1–B3, B5, B6 written;
  B4 and later sections wait for 0003–0008 to be accepted). `sources.md` and `open-questions-his.md` exist.
- Level 1 is G7250-P2: openHPSDR Protocol 2, board type 200 (0016, 0002). The P2, P1, HL2
  and AetherSDR sources and the CH394 datasheet have been read; the TCI 2.1 PDF has not.
- Analyses: `analysis/p1-vs-p2.md`, `analysis/ch394-network-budget.md`.
- The G7250 operation manual rev 0.1 is the primary product source (`sources.md`).

## Decisions

| #    | Title | Status |
|------|-------|--------|
| 0001 | Structure of the design note and the network-interface spec | accepted |
| 0002 | Board type of G7250-P2: 200 (0xC8), chosen ourselves; openHPSDR to be informed | accepted; notice sent as TAPR/OpenHPSDR-Firmware#6 |
| 0003 | Capability block: short P2 discovery reply (board type 200, never 254/255) + read-only capability record in the G7250 register map | proposed |
| 0004 | Streams: one DDC at 48–384 ksps (384 only if SPI ≥ ~50 MHz), TX IQ 24-bit 192 ksps, mic only if HIS-17, no wideband yet; unsupported requests refused | proposed |
| 0005 | Control fields on P2: standard fields where identical; G7250 functions and TX safety in a G7250 register map (P2 memory-mapped registers) | accepted |
| 0006 | Telemetry: standard P2 status fields where identical, calibrated and formula-compatible; G7250 sensors and state in register map | proposed |
| 0007 | Watchdog and safety: token-based TX arm, 13 disarm events, keyed timeout 300 ms, takeover always allowed but disarms, limits table, two fault classes | proposed |
| 0008 | Management channel: own UDP port on the 8th socket, challenge-response writes, signed updates with rollback, never keys the radio | proposed |
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

All numbers 0001–0018 are now in use.

## Open questions for ON8ST

Each proposed decision ends with its own list (0003: 6, 0004: 9, 0006: 6, 0007: 12,
0008: 5, spec draft: 5 provisional statements). The ones that block most:

1. Accept 0003, 0004, 0006, 0007, 0008 (all proposed, 2026-11-19).
2. 0007: takeover always allowed (disarms) vs refused while armed.
3. 0007: default maximum continuous TX time; keyed timeout 300 ms OK on Wi-Fi hosts?
4. 0004: 60 % SPI design target; 384 ksps only if SPI ≥ ~50 MHz; refuse vs clamp unsupported rates.
5. 0008: how the first management secret is set on a radio in factory state.
6. 0006: calibrated, formula-compatible encoding instead of raw ADC words.
7. 0003: one extra request after discovery to read the capability record.
8. Spec B2.3: one local port for the register map in both directions (now also in 0005).

Watch TAPR/OpenHPSDR-Firmware#6 for a reply on board type 200.

## Open questions for the HIS

In `open-questions-his.md` (HIS-01 to HIS-19).

## Next step

1. (Done: 0013, `sources.md`.) Still open in `sources.md`: read the Radioddity product page
   (HTTP 429 on 2026-11-19), read the TCI 2.1 PDF and check its terms, find a manufacturer
   manual.
2. (Done: `open-questions-his.md`.)
3. (Done: `design-note.md` draft 1; review by ON8ST.)
4. (Done, proposed: 0003, 0004, 0006, 0007, 0008.) After acceptance: fill spec B4 and the
   sample-rate, telemetry, transmit and register-map sections.
5. (Draft 1 done: `spec/network-interface.md`.)

# Product handover (g7250-spec → product/spec/)

Date: 2026-11-19. Source of everything below: the start brief and the discussion with ON8ST
on 2026-11-19, as recorded in `decisions/`.

## Where things stand

- The g7250-spec branch `docs/initial-structure` has been subtree-merged into
  `product/spec/` in the main repo (merge commit a29155b, local, not pushed).
- Neither document has been written yet. Only the structure was agreed, plus several
  decisions. `design-note.md`, `spec/`, `sources.md` and `open-questions-his.md` do not
  exist yet.
- No technical P1 or TCI details have been checked against public sources yet. Everything
  about frames, ports and board ids is still unverified.

## Decisions

| #    | Title | Status |
|------|-------|--------|
| 0001 | Structure of the design note and the network-interface spec | accepted |
| 0002 | Board type of G7250-P2: 200 (0xC8), chosen ourselves; openHPSDR to be informed | accepted; notice sent as TAPR/OpenHPSDR-Firmware#6 |
| 0005 | Control fields on P2: standard fields where identical; G7250 functions and TX safety in a G7250 register map (P2 memory-mapped registers) | accepted |
| 0009 | Stay as close to the standard protocol as possible (now P2, see 0016) | accepted |
| 0010 | No compatibility modes for now (HL2 rejected, ANAN out of scope for now) | accepted |
| 0011 | Two-level product interface: L1 G7250-P2 (was G7250-P1, see 0016) / L2 TCI with on-board DSP. Single owner, shared safety core, L2 only after gate G6 | accepted |
| 0012 | Every integration supports full functionality including TX; no SoapySDR module | accepted |
| 0013 | AetherSDR is the initial integration route for level 1; no separate bridge | accepted |
| 0014 | One TCI profile (spec part C) for AetherSDR on level 1 and the firmware on level 2 | accepted |
| 0015 | Host that does not know the board type: RX only; TX needs an arm in the G7250 register map | accepted |
| 0016 | Level 1 uses openHPSDR Protocol 2 instead of Protocol 1; AetherSDR P2 support built by us if needed | accepted. Revises 0001, 0009, 0011; 0005 and 0015 rewritten |

Numbers 0003, 0004 and 0006–0008 are reserved for: capability block,
streams and sample rates, telemetry, watchdog and safety (including the TX arm from 0015),
management channel.

## Open questions for ON8ST

1. Does the CH394 finding change the choice for P2 (0016)? P2 needs 8 sockets with one
   receiver; a CH394Q has exactly 8, a CH394L 4. See `analysis/ch394-network-budget.md`.

None otherwise. Watch TAPR/OpenHPSDR-Firmware#6 for a reply on board type 200.

Level 1 is called G7250-P2 (ON8ST, 2026-11-19).

Analysis: `analysis/p1-vs-p2.md`. AetherSDR facts (P1 TX via HL2, P2 receive-only via
ANAN-G2, TCI server announcing protocol 2.1) come from its README, read 2026-11-19.

## Open questions for the HIS (to put into `open-questions-his.md`)

- ADC type and sample clock: which sample rates are feasible?
- Sensors: forward/reflected power, SWR, temperature, supply voltage.
- ATU control.
- Antenna and filter switching, including a safe RX default state for a host that has not
  armed TX (0015).
- Where PTT and TX interlock sit.
- Network hardware of the main unit: Ethernet is present (ON8ST, 2026-11-19, see
  `sources.md` [G7250-TOFF]). ON8ST saw a WCH CH394 during hardware inspection: confirm,
  and which variant (CH394Q 8 sockets / CH394L 4 sockets), which interface and clock to the
  processor, socket or MACRAW mode. See `analysis/ch394-network-budget.md`. Wi-Fi still open.
- Compute resources (DSP/FPGA/MCU), memory, network stack (TCP, WebSocket). These are
  needed for gate G6.

## Next step

1. (Done: 0013, `sources.md`.) Still open in `sources.md`: read the Radioddity product page
   (HTTP 429 on 2026-11-19), read the TCI 2.1 PDF and check its terms, find a manufacturer
   manual.
2. Create `open-questions-his.md` from the list above.
3. Write `design-note.md` (both levels on G7250-P2, milestones M1–M7 and G6, out-of-scope list
   as amended by 0010–0012 and 0016).
4. Decisions 0003 (capability block) and 0007 (watchdog and safety).
5. Write spec part B (level 1 on P2, starting with M1: discovery, capability block, RX-IQ),
   with sources cited.

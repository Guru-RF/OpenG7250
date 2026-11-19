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
| 0005 | C&C fields: standard P1, HL2 addresses only with identical meaning; TX safety on G7250 addresses | accepted |
| 0009 | Stay as close to standard Protocol 1 as possible | accepted |
| 0010 | No compatibility modes for now (HL2 rejected, ANAN out of scope for now) | accepted |
| 0011 | Two-level product interface: L1 G7250-P1 / L2 TCI with on-board DSP. Single owner, shared safety core, L2 only after gate G6 | accepted |
| 0012 | Every integration supports full functionality including TX; no SoapySDR module | accepted |
| 0013 | AetherSDR is the initial integration route for level 1; no separate bridge | accepted |
| 0014 | One TCI profile (spec part C) for AetherSDR on level 1 and the firmware on level 2 | accepted |
| 0015 | Host that does not know the board id: RX only; TX needs an explicit G7250 arm | accepted |

Numbers 0002–0004 and 0006–0008 are reserved for: board-id value, capability block,
streams and sample rates, telemetry, watchdog and safety (including the TX arm from 0015),
management channel.

## Open questions for ON8ST

None at the moment. The earlier questions were settled in 0005, 0014 and 0015, and 0001
is accepted.

## Open questions for the HIS (to put into `open-questions-his.md`)

- ADC type and sample clock: which sample rates are feasible?
- Sensors: forward/reflected power, SWR, temperature, supply voltage.
- ATU control.
- Antenna and filter switching, including a safe RX default state for a host that has not
  armed TX (0015).
- Where PTT and TX interlock sit.
- Compute resources (DSP/FPGA/MCU), memory, network stack (TCP, WebSocket). These are
  needed for gate G6.

## Next step

1. (Done: 0013.)
2. Create `sources.md`, collecting and checking the public sources: P1 documentation, HL2
   documentation, the TCI spec (version and terms of use), and the G7250 product
   specifications and manual.
3. Write `design-note.md` (both levels, milestones M1–M7 and G6, out-of-scope list as
   amended by 0010–0012).
4. Write spec part B (level 1, starting with M1: discovery, capability block, RX-IQ), with
   sources cited.

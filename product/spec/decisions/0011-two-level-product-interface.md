# 0011 — Two-level product interface

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19
- Revised by 0016 (Protocol 2 instead of Protocol 1), 2026-11-19: level 1 uses P2; point 5 ("Protocol 2 stays out of scope") no longer applies.

## Context

The start brief (ON8ST, 2026-11-19) defines the firmware as a native OpenHPSDR Protocol 1
interface with its own board id, with TCI, CAT and rigctl offered by the host. ON8ST
proposed to offer the product on two levels: a bare-bones SDR interface and a complete
radio interface with on-board DSP over TCI (discussion, 2026-11-19). The stock G7250 works
as a standalone radio according to its public product specifications (Radioddity, user
manual), so the hardware can demodulate; how much compute is available is an open question
for the HIS.

## Decision

1. The product offers two levels:
   - Level 1, SDR: G7250-P1 (Protocol 1, own board id). Raw IQ, C&C and telemetry; DSP in
     the host.
   - Level 2, Radio: a TCI server in the radio, with DSP on board.
2. Single owner: only one level controls the RF chain at a time, and only that owner may
   transmit. The active level is visible in the capability block and in the management
   channel.
3. Shared safety core: watchdog, TX limits (SWR, temperature, power, maximum TX time) and
   the fault state sit below both levels, independent of the protocol. A level may make the
   limits stricter, never looser.
4. Order: level 1 first (M1–M5). Level 2 only after feasibility gate G6 (HIS answers on
   compute, memory and network stack): M6 TCI RX, M7 TCI TX.
5. CAT and rigctl stay on the host side. Protocol 2 and compatibility modes stay out of
   scope (0010).

## Consequences

- The design note describes both levels and the shared architecture:
  hardware -> safety core -> RF control core -> IQ path (level 1) / DSP path (level 2),
  plus a separate management channel.
- The out-of-scope list changes: "TCI in firmware" and "DSP in the radio" become
  "not before M6, and only after G6".
- The network spec has three parts: A common (management channel, level selection and
  ownership, safety behaviour visible on the network), B level 1 (G7250-P1), C level 2 (TCI,
  placeholder until after G6).
- The capability block of level 1 says whether level 2 exists and whether it is active.
- Before part C is written, the TCI version to follow and its terms of use must be checked.
- New open questions for the HIS: compute resources (DSP/FPGA/MCU), memory, network stack
  (TCP, WebSocket).

## Sources

- Start brief, ON8ST, 2026-11-19.
- Discussion with ON8ST, 2026-11-19.
- Public G7250 product specifications (Radioddity) and user manual — to be listed in
  `sources.md`.

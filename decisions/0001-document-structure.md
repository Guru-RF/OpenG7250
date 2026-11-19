# 0001 — Structure of the design note and the network-interface spec

- Status: proposed (ON8ST: "a strong starting point", 2026-11-19; one point under review, see Open points)
- Date: 2026-11-19

## Context

The start brief from ON8ST (2026-11-19) asks for a first version of two documents:
(1) a design note describing the product, its users, its milestones and what is out of
scope, and (2) the network-interface spec. The structure is proposed first and agreed
before the documents are written out (start brief, "Werkwijze").

Source for all product intent below: the start brief from ON8ST, 2026-11-19.
Protocol details are not yet verified against public documents; they will be cited in
the documents themselves (AGENTS.md rule 3).

## Proposal

### Repository layout

```
design-note.md               (1) product, users, milestones, scope
spec/network-interface.md    (2) normative spec (RFC 2119 MUST/SHOULD/MAY)
decisions/NNNN-<slug>.md     one decision per file: context, options, choice, consequences, sources
sources.md                   public sources with short keys ([P1], [HL2], [TCI], ...) used for citations
open-questions-his.md        questions only the hardware-interface spec (HIS) can answer
```

### (1) Design note

1. Purpose: new firmware for the G7250 Main, speaking native OpenHPSDR Protocol 1
   with its own board id "G7250-P1".
2. Users and host: AetherSDR as primary host; behaviour of other P1 clients when they see an
   unknown board id.
3. The radio from public specifications (Radioddity, user manual): one receiver, 100 W HF,
   90 W on 6 m, internal ATU, two antenna connectors.
4. Architecture boundary: firmware = P1, watchdog, safety; host = DSP, TCI, CAT, rigctl.
5. Principles: no impersonation of another board; clean room; spec first, with a reference
   model and conformance tests for every part.
6. Milestones, each with testable exit criteria:
   - M1: discovery, capability block, RX-IQ — first in g7250-testbench against the
     reference model, then in firmware.
   - M2: C&C (frequency, antenna, filters) and telemetry.
   - M3: watchdog specified and tested.
   - M4: TX (only after M3).
   - M5: management channel (update, configuration).
7. Out of scope: TCI, CAT and rigctl in firmware; Protocol 2; emulation of HL2 or ANAN;
   more receivers than the hardware has; DSP in the radio.
8. Dependencies and open questions: HIS, AetherSDR change, testbench.

### (2) Network-interface spec

1. Scope and conformance language.
2. Transport: UDP port 1024, P1 framing, endpoints, sequence numbers, byte order.
3. Discovery: request and reply, busy state, board-id byte, firmware version.
4. Capability block: location (proposed: spare bytes of the discovery reply, with magic and
   version), fields (name "G7250-P1", number of RX, sample rates, antennas, ATU, TX power per
   band, telemetry flags), versioning.
5. Session control: start/stop, second host.
6. Streams: RX-IQ (format, sample rates); mic/audio stream (sent or ignored); wideband
   (yes/no); TX-IQ reserved until M4.
7. C&C map: one table per C0 address, each row marked standard P1 / HL2-compatible
   extension / G7250 extension / reserved, with a source; behaviour on unknown addresses.
8. Telemetry: fields in the C&C returns, scale, unit, update rate (physical origin from HIS).
9. Watchdog and safety (normative, gate for M4): host timeout -> RX stop and TX off;
   maximum TX time; SWR, temperature and power limits; state after reset or fault.
10. Management channel, separate from P1: own port and protocol for firmware update,
    configuration, logs, identification. This version: boundaries and requirements only.
11. Error handling and robustness: malformed packets, sequence gaps, overruns.
12. Conformance tests per section, run by g7250-testbench against the reference model.
13. Annexes: differences from standard P1 and from the HL2 extensions; changes needed in
    AetherSDR.

### Decisions to open

| #    | Decision                                         | Note |
|------|--------------------------------------------------|------|
| 0002 | Numeric value of the board id                    | 8-bit byte; the name "G7250-P1" goes in the capability block; pick a value outside the known P1/HL2 values |
| 0003 | Format and location of the capability block      | |
| 0004 | Streams and sample rates                         | depends partly on HIS (ADC, sample clock) |
| 0005 | C&C fields: standard vs extensions               | reuse HL2 extensions where they fit, or standard P1 plus own addresses |
| 0006 | Telemetry                                        | |
| 0007 | Watchdog and safety                              | |
| 0008 | Management channel                               | |

### Open questions for the HIS (first list)

- ADC type and sample clock (which sample rates are feasible).
- Available sensors: forward/reflected power, SWR, temperature, supply voltage.
- ATU control.
- Antenna and filter switching.
- Where PTT and TX interlock sit in hardware.

## Open points

- ON8ST questions whether a P1 interface with its own board id, which requires applications
  to be adapted, should be complemented by a more generic standard interface. Options are
  being worked out; outcome to be recorded as a separate decision.
- Should C&C be HL2-compatible where possible (proposed) or standard P1 plus own addresses?
- Should a host that does not know the board id still be able to receive RX-IQ (generic P1)?

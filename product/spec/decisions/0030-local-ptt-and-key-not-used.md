# 0030 — Local PTT and key inputs on the main unit are not used in v1.0

- Status: accepted (ON8ST, 2026-11-20, answers to the HIS impact analysis §4, relayed by the openg7250 session and confirmed in this session)
- Date: 2026-11-20

## Context

HIS 85 (`2a38b7f`): PTT input PH6 and the CW key or paddle contacts PH3/PH4 are on the Main
(HIGH); RX-only firmware MUST NOT transmit on any change of them. The spec so far allowed the
KEY input as one local requester (A3.1a, B10.9) if it reaches the main unit (HIS-17).

## Decision

1. In v1.0 the firmware does not use PH6, PH3 or PH4. It behaves as if no PTT or KEY input
   reaches the main unit: they key nothing and are reported as 0.
2. The rules of the spec for the KEY input (hardware CW, B10.9) stay as written for a later
   version, but do not apply in v1.0; the tests for them are marked "not in v1.0".

## Consequences

- A3.1a requester list, A3.7, High Priority status byte 4 bits [0]–[2], B10.9: v1.0 note.
- Tests T-A3-07, T-A3-42, T-B10-15, T-B10-37: "not in v1.0 (0030)".

## Sources

- [HIS] HIS 85 (`2a38b7f`); ON8ST, 2026-11-20; decisions 0007, 0022 §65.

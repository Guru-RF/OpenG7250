# 0013 — AetherSDR is the initial integration route for level 1

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19

## Context

Level 1 (G7250-P1, 0011) delivers raw IQ; the DSP runs on the host. Every integration must
support full functionality including transmit (0012). Three routes were presented
(discussion, 2026-11-19):

1. Native support in existing P1 applications through upstream patches.
2. AetherSDR as integration hub (TCI, CAT, rigctl offered by the host, as in the start brief).
3. A host-side bridge that does the DSP and offers the same TCI interface as level 2.

ON8ST judged route 3 the best in principle. Route 3 is in essence what AetherSDR already
does, and that work is not to be duplicated (ON8ST, 2026-11-19).

## Decision

AetherSDR is the initial integration route for a usable application on level 1.
No separate host-side bridge is built.

## Consequences

- AetherSDR is the integration point for third-party applications on level 1; what it
  offers to them (TCI, CAT, rigctl, audio) is AetherSDR's responsibility, not part of the
  firmware or of this spec.
- The spec has to give AetherSDR everything it needs for full functionality, including TX
  (0012): board id, capability block, C&C, telemetry and safety behaviour.
- Route 1 (upstream patches in other P1 applications) is not planned. It remains possible
  later because of 0009.
- Whether AetherSDR's host-side TCI matches spec part C (level 2) is not decided here.

## Sources

- Start brief, ON8ST, 2026-11-19.
- Discussion with ON8ST, 2026-11-19.

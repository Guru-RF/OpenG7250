# 0036 — Transmit is part of r1.0, armable only once calibrated

- Status: accepted (ON8ST, 2026-11-20, relayed by the openg7250 session)
- Date: 2026-11-20
- Builds on: 0007, 0012, 0015, 0022, 0032, 0035.

## Context

The spec already defines the complete transmit path: keying over the network on both levels
(B10, part C C5.5, C7), the TX arm (0007, 0015), PA drive and bias (B10.8; [HIS] HIS 85), the
protections and limits (A3, Table A3-2), and the ATU tune cycle (A3.9b, 0032). The transmit
values need the radio (Annex P).

## Decision

1. Transmit is in scope for release r1.0 of the firmware: network keying, PA drive and bias,
   protections and the ATU.
2. TX is armable only once the transmit parameters of Annex P are set from measurements; until
   then every arm gets `NOT_CALIBRATED` and the ATU stays in bypass (0035 item 2, 0032).
3. This does not change the scope of the spec, which already covers TX; it fixes that r1.0
   ships with TX and that TX is enabled by calibration, not by a later firmware.

## Consequences

- Record `tx` bit 1 is 1 in r1.0; bit 4 follows the calibration (Annex P).
- The milestones of the design note that put TX after M3/M4 stay; r1.0 includes them.

## Sources

- ON8ST, 2026-11-20; decisions 0007, 0012, 0015, 0022, 0032, 0035; [HIS] HIS 85 (`9d10e72`).

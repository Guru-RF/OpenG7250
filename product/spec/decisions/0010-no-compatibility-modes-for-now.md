# 0010 — No compatibility modes for now

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19
- Note after 0016 (2026-11-19): level 1 is now G7250-P2 with board type 200 (0002); read
  "G7250-P2" for "G7250-P1" below.

## Context

ON8ST asked whether the radio could also present itself as an existing P1 board, so that
existing applications work without change (see 0001, Open points). Two candidates came up:

- Hermes-Lite 2: rejected by ON8ST because the HL2 has no 100 W amplifier and no ATU.
- ANAN: considered. A compatibility mode would conflict with the principle "we do not
  impersonate another board" (start brief, ON8ST, 2026-11-19), and would need careful mapping
  of TX drive and power/SWR calibration to avoid wrong readings or overdrive.

## Decision

No compatibility modes are in scope for now. The radio identifies only as G7250-P1.
The principle "we do not impersonate another board" stays in force.

## Consequences

- The design note lists HL2 and ANAN compatibility modes as out of scope.
- An ANAN mode may be reconsidered later. That requires a new decision that explicitly
  revises the principle, preceded by research in public sources (ANAN board ids, C&C
  semantics, client handling of drive and power).

## Sources

- Start brief, ON8ST, 2026-11-19.
- Discussion with ON8ST, 2026-11-19.

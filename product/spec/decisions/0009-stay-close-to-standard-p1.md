# 0009 — Stay as close to standard Protocol 1 as possible

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19

## Context

G7250-P1 uses its own board id (start brief, ON8ST, 2026-11-19). Every P1 application
therefore has to learn that id before it can use the radio. ON8ST asked which options
exist to reduce that burden (see 0001, Open points).

## Decision

Frame format, streams and standard C&C fields keep exactly their standard Protocol 1
meaning. G7250 extensions are placed only on addresses or bits that standard P1 leaves
free, and each one is marked as an extension in the C&C map of the spec.

## Consequences

- An existing P1 application should only need to recognise the new board id, with little or
  no further change. This is to be verified per application against public sources.
- Every deviation from standard P1 must be listed in the spec annex "Differences from
  standard P1".
- This decision does not settle whether HL2-style extensions are reused (decision 0005).

## Sources

- Start brief, ON8ST, 2026-11-19.
- Discussion with ON8ST, 2026-11-19.

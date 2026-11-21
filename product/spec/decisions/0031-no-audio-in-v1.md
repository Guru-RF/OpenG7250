# 0031 — No audio through the main unit's codec in v1.0

- Status: accepted (ON8ST, 2026-11-20, answers to the HIS impact analysis §4, relayed by the openg7250 session and confirmed in this session)
- Date: 2026-11-20

## Context

HIS 50 (`2a38b7f`): the Main has an AIC3204 codec with I²S, and audio between Main and Control
crosses the CTRL cable as analog. This could carry receive audio to the controller's speaker
and microphone audio for TX, which 0017 and 0004 had excluded on the premise that the main unit
has no audio.

## Decision

1. No audio in v1.0. 0017 (no DDC audio stream) and the microphone part of 0004 stay.
2. The codec stays in reset (HIS 85 safe-state table, HIS 50).
3. Audio through the codec is a later option, for a later decision.

## Consequences

- None in the normative text beyond the safe state; analysis §4 item 3 closed.

## Sources

- [HIS] HIS 50, HIS 85 (`2a38b7f`); ON8ST, 2026-11-20; decisions 0004, 0017.

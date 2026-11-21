# 0002 — Board type value of G7250-P2: 200 (0xC8)

- Status: accepted (ON8ST, 2026-11-19: choose a value ourselves and inform the openHPSDR
  project; value 200 accepted)
- Date: 2026-11-19

## Context

G7250-P2 identifies itself by the board type byte in the P2 discovery reply (byte 11)
[P2]. 0001 planned this decision for a P1 board id; after 0016 it is a P2 board type.

The P2 document assigns [P2]:

- 0 ATLAS, 1 HERMES (ANAN-10, 100), 2 HERMES (ANAN-10E, 100B), 3 ANGELIA (ANAN-100D),
  4 ORION (ANAN-200D), 5 ORION Mk II (ANAN-7000/8000DLE), 6 Hermes Lite, 10 SATURN (ANAN-G2);
- 7, 8 and 9 reserved;
- 254: an XML hardware description follows (Appendix B, "To be written");
- 255: a full hardware description follows (Appendix C).

Values are handed out upward from 0. SATURN got 10 in V4.0 (2023) [P2]. The document also
shows that the project lists boards from outside Apache Labs: V1.1 "Changed Hermes Lite
reference number from 5 to 6" [P2].

No registry or licence governs these values. The only risk is a collision: if openHPSDR
later assigns our value to another board, a host would take the G7250 for that board.

ON8ST decided not to ask for a value but to choose one ourselves and inform the openHPSDR
project (2026-11-19).

## Options considered

### A. A value far from both ends of the used range: 200 (0xC8) (chosen)

- For: the assigned range grows upward from 0 and is now at 10. At the current pace (one new
  value in years) it will not reach 200.
- For: well away from 254 and 255, which have a special meaning, and from the values just
  below them, in case the project ever adds more description formats there.
- For: an easy value to recognise in a packet dump (0xC8, decimal 200).
- Against: still not reserved by anyone. Informing the project reduces, but does not remove,
  the risk.

### B. The next free value: 11

- For: follows the project's own pattern.
- Against: it is the value the project is most likely to give to its next board. The chance
  of a collision is the highest of all options.

### C. One of the reserved values 7, 8 or 9

- Against: the document marks them reserved [P2], so the project has plans or at least claims
  for them. Rejected.

### D. Only 254 or 255, without a value of our own

Report board type 255 and describe the G7250 in the full description (Appendix C) [P2].

- For: no number of our own at all.
- Against: 255 says "a description follows", not "this is a G7250". Appendix C has no field
  for a board name or vendor [P2], so a host still cannot tell the G7250 from any other board
  using 255.
- Against: whether hosts handle 255 at all has not been checked.

### E. Ask the openHPSDR project for a value first

- For: the lowest risk of a collision, if they agree.
- Against: makes progress depend on a reply from outside. ON8ST chose not to do this.

## Decision

Option A. G7250-P2 reports board type 200 (0xC8) in byte 11 of the P2 discovery reply. The
openHPSDR project is informed of this value.

## Consequences

- Spec section 3 (discovery) fixes byte 11 = 200 for G7250-P2.
- The name "G7250-P2" (0016) goes in the capability block (0003), not in the board type.
- Whether the capability block uses the board type 255 description (Appendix C) is decided in
  0003. If it does, the G7250 needs a way to give both its own value and the description;
  0003 has to solve that.
- **Informing openHPSDR.** A short notice to the openHPSDR project, stating that G7250-P2
  uses board type 200 and asking them to avoid it. This is an outward action: channel,
  account and text need a go from ON8ST before anything is sent (AGENTS.md rule 6).
  Sent with that go on 2026-11-19 as https://github.com/TAPR/OpenHPSDR-Firmware/issues/6
  (text in `outreach/openhpsdr-board-type-200.md`).
- The notice proposes 200 and offers to use another value if openHPSDR prefers one
  (ON8ST, 2026-11-19). If they name a value, or later assign 200 to another board, this
  decision is revised.
- The behaviour of P2 hosts that see an unknown board type is covered in 0015.

## Sources

- Discussion with ON8ST, 2026-11-19.
- Decisions 0001, 0003 (reserved), 0015, 0016.
- [P2] openHPSDR Ethernet Protocol V4.4, github.com/TAPR/OpenHPSDR-Firmware,
  `Protocol 2/Documentation/`: discovery reply byte 11 (board type list), Appendix B,
  Appendix C, revision history (V1.1, V4.0).

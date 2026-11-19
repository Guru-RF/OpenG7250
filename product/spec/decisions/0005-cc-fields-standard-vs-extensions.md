# 0005 — Control fields on P2: standard fields where identical, G7250 functions in memory-mapped registers

- Status: proposed (rewritten for Protocol 2 after 0016, 2026-11-19). The P1 version was
  accepted by ON8ST on 2026-11-19; this rewrite still needs acceptance.
- Date: 2026-11-19
- Supersedes: the P1 version of this decision ("standard P1, HL2 addresses only with
  identical meaning"), which lapsed with 0016.

## Context

Level 1 is G7250-P2: openHPSDR Protocol 2 with a G7250 board type (0016; name confirmed by
ON8ST, 2026-11-19). 0009, as revised by 0016, says: stay as close to standard P2 as possible,
with extensions only where P2 leaves room, each marked as an extension.

How P2 carries control [P2]:

- Separate packets from the host: General (rarely changing settings), DDC-specific,
  DUC-specific, and High Priority (run, PTT, frequencies, drive level, open-collector
  outputs, Alex filter and antenna words, step attenuators). Each is sent when a value
  changes.
- In the High Priority packet, byte 4 bit [0] is run and bit [1] enables transmit. Byte 345
  is the DUC0 drive level, 0–255. Bytes 1396–1397 are a "client control word" for accessory
  hardware, bit [0] = TUNE (added in V4.4). Bytes 1428–1435 carry the Alex TX relay word and
  the Alex filter, preamplifier and antenna word.
- The General packet has an Apollo ATU enable bit (byte 58 bit [1]) and a PA enable bit
  (byte 58 bit [0]).
- P2 defines **memory-mapped registers**: a packet from the host and one from the hardware,
  each carrying up to 240 pairs of a 16-bit address and a 32-bit data word. The ports are set
  in the General packet (bytes 29–32); the document gives the default port as "xxxx", so it
  is not defined. The full-description discovery reply has a flag "Memory mapped registers
  supported" (Appendix C, byte 23). P2 defines no address map.
- Many bytes in the standard packets are marked "Reserved for future use". Several of them
  have been given a meaning in later revisions: the client control word and the CAT-over-TCP
  port (V4.3–V4.4), and the upper 16 bits of Alex 1 reused for Alex 0 TX relay data (V4.3).

The G7250 needs control that P2 does not describe for its hardware, at least for the
internal ATU, the two antenna connectors and the 100 W PA [G7250]. The exact list depends on
the HIS.

## Options considered

### A. Standard P2 fields where the meaning is identical; G7250 functions in memory-mapped registers (chosen)

1. A G7250 function that a standard P2 field describes exactly (same bits, scale, unit and
   side effects) uses that field. Examples to check: run, PTT, frequencies, drive level,
   step attenuator, the TUNE bit in the client control word.
2. Every other G7250 function goes into a **G7250 register map** carried by the P2
   memory-mapped register packets. The spec defines the addresses, the data layout and the
   ports, because P2 leaves all three open.
3. Reserved bytes in the standard packets are never used for G7250 functions.
4. Everything to do with TX safety (arming, limits, fault state) is in the G7250 register
   map, even if a standard field looks similar (see 0015, 0007).

- For: uses an extension mechanism that P2 itself defines, including a discovery flag that
  tells the host it is there. That is the closest to "stay close to standard P2" (0009).
- For: no collision with future openHPSDR revisions, because P2 assigns no addresses in the
  memory-mapped space.
- For: one place for all G7250 specifics, with room for 65,536 addresses. The map can be
  versioned and announced in the capability block (0003).
- Against: the registers travel in their own packets, not in the High Priority packet. A
  G7250 setting that must change at the same moment as PTT needs care in the spec (ordering,
  confirmation by the radio).
- Against: P2 leaves the default port undefined, so we have to choose one. A host that does
  not know the G7250 does not use the registers at all, which is intended (see 0015).

### B. Use reserved bytes in the standard P2 packets

Put G7250 fields in bytes marked "Reserved for future use", for example High Priority byte 4
bits [2]–[7] or the unused DUC1–DUC3 and Alex 2–7 slots.

- For: G7250 settings travel in the same packet as PTT and frequency, so they change at the
  same moment.
- For: no extra port or packet type.
- Against: reserved bytes get a meaning in later P2 revisions, as happened in V4.3 and V4.4.
  A later revision could give one of our bytes a different meaning, and a host following
  that revision would then set the wrong thing on a 100 W radio.
- Against: it reads as standard P2 but is not. A generic host has no way to see that the
  bytes mean something else on the G7250.

### C. A G7250-specific packet on its own port

Define a new packet type and port for G7250 control.

- For: complete freedom of layout, including fields that are set atomically with PTT if the
  packet also carries PTT.
- Against: it duplicates what the memory-mapped registers already offer in P2.
- Against: a new port and packet that no P2 document mentions, so further from the
  standard than option A.

### D. Reuse Alex, Apollo or other accessory fields with approximately the same meaning

Map the G7250 ATU onto the Apollo bits and its antenna switching onto the Alex word, even
where the meaning differs.

- For: some P2 hosts would partly control the G7250 without any change.
- Against: a near match is exactly the case where a host sets the wrong thing without
  noticing. For PA, ATU and antenna control on a 100 W radio that is a safety risk.
- Against: the Alex and Apollo fields describe specific external TAPR/Apache accessories
  [P2], not the G7250 hardware.
- Rule 1 of option A still allows a single field of this kind if it is checked to be
  identical.

### E. Everything G7250-specific over the management channel

Keep P2 strictly standard and put G7250 control on the separate management channel (0001,
spec section 10).

- For: P2 stays completely untouched.
- Against: the management channel is meant for update, configuration, logs and
  identification (0001, spec section 10), not for real-time radio control. Antenna and ATU
  control would be on a different connection from PTT and frequency.
- Against: every host needs a second connection for normal operation.

## Decision

Option A. G7250-P2 uses a standard P2 field when its meaning is identical to what the G7250
needs. All other G7250 functions, and everything to do with TX safety, are in a G7250
register map carried by the P2 memory-mapped register packets. Reserved bytes in the
standard packets are not used.

## Consequences

- Spec part B gets two tables:
  - a P2 field table: per standard P2 field, whether the G7250 uses it, ignores it or
    rejects it, with a source;
  - a G7250 register map: address, name, data layout, direction, access, and source (HIS or
    decision).
- The spec defines the memory-mapped ports, because P2 gives the default as "xxxx". The
  G7250 sets the "Memory mapped registers supported" flag in its full description
  (Appendix C, byte 23), if the capability block uses that reply (0003).
- "Identical meaning" for a standard field is checked against [P2] per field. If in doubt,
  the function goes into the register map.
- The spec says how a register write is confirmed (for example, the radio echoes the value
  in a memory-mapped packet to the host) and in which order register writes and High
  Priority packets take effect. This matters for antenna and ATU changes around PTT.
- The annex "Differences from standard P2" lists every standard field the G7250 ignores or
  rejects and the whole register map.
- The list of G7250 registers depends on the HIS (antenna and filter switching, ATU control,
  sensors). Until the HIS answers, part B can only reserve them.
- TX arming and safety state are specified in 0015 and 0007, as registers in this map.

## Sources

- Discussion with ON8ST, 2026-11-19.
- Decisions 0001, 0007 (reserved), 0009, 0015, 0016.
- [P2] openHPSDR Ethernet Protocol V4.4, github.com/TAPR/OpenHPSDR-Firmware, `Protocol 2/Documentation/`:
  General packet (bytes 29–32, 58), High Priority packet (bytes 4, 345, 1396–1397,
  1428–1435), memory-mapped register packets, Appendix C (byte 23), revision history (V4.3,
  V4.4).
- [G7250] Public G7250 product specifications (Radioddity) — to be listed in `sources.md`.

# 0005 — C&C fields: standard P1, HL2 addresses only with identical meaning

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19
- Revised by 0016 (Protocol 2 instead of Protocol 1), 2026-11-19: to be rewritten for the P2 packet structure; the HL2 rule applies to P1 addresses and lapses.

## Context

Protocol 1 carries command and control (C&C) in the frame headers. The address C0 selects
which register the bytes C1–C4 set. Standard P1 leaves some addresses and bits free, and
the Hermes Lite 2 (HL2) project has published extensions that use some of them. Both are to
be listed in `sources.md` as [P1] and [HL2]. Neither has been checked against those sources
yet.

Decisions already made:

- 0009: standard fields keep their standard P1 meaning exactly. Extensions go only on
  addresses or bits that standard P1 leaves free, and each one is marked as an extension.
- 0010: no HL2 compatibility mode. The HL2 has no 100 W amplifier and no ATU (ON8ST,
  2026-11-19).
- 0012: every integration supports full functionality including TX.

The G7250 needs control that standard P1 does not have, at least for the 100 W PA, the
internal ATU and two antenna connectors (public product specifications, Radioddity; 0001,
design note item 3). Which controls are needed exactly depends on the HIS.

## Options considered

### A. Standard P1, plus HL2 addresses only where the meaning is identical (chosen)

Standard P1 is the base. For a function that is not in standard P1:

1. If a published HL2 extension does exactly the same thing (same bits, same scale, same
   unit, same side effects), the G7250 uses that HL2 address and bit layout.
2. Otherwise, including when the HL2 field is only similar, the function gets a G7250
   address.
3. Everything to do with TX safety (arming, limits, fault state) always gets a G7250
   address, even if HL2 has something comparable (see 0015).

- For: follows 0009. A function that already has a public, documented place does not get a
  second one.
- For: a P1 host that already implements the HL2 extensions can reuse that code for those
  functions.
- For: does not conflict with 0010. The board id stays G7250-P1, so an HL2 application does
  not see the radio as an HL2. Only addresses are shared, not the identity.
- For: the "identical meaning" rule removes the main risk of reusing HL2 addresses, which is
  a field that almost matches and makes a host silently set the wrong thing.
- Against: the C&C map has three kinds of rows (standard, HL2-compatible, G7250). Each HL2
  row must be checked against the HL2 documentation and cited.
- Against: we depend on the HL2 documentation staying stable. If HL2 changes the meaning of
  an address we use, the G7250 meaning does not follow automatically.

### B. Standard P1 plus G7250 addresses only

No HL2 addresses. Everything outside standard P1 gets a G7250 address.

- For: no dependency on HL2 meaning or on its documentation. The map has only two kinds of
  rows.
- For: no risk at all that an HL2-aware host misreads a G7250 field.
- Against: functions that HL2 already places publicly get a second place. A host that
  supports both HL2 and G7250 needs two code paths for the same function.
- Against: the free address space of standard P1 is limited, and we would fill more of it.

### C. Adopt the full HL2 extension map

Use the whole HL2 extension map, including fields that only roughly match the G7250, and add
G7250 addresses only for what HL2 has no field for at all.

- For: the most reuse for hosts that know HL2.
- Against: in practice this is close to the HL2 compatibility mode that 0010 rejected.
  Fields that are meaningful on an HL2 but not on the G7250, or the other way round, would
  have to be redefined or ignored.
- Against: a near match is exactly the case where a host sets the wrong thing without
  noticing. For PA and antenna control on a 100 W radio, that is a safety risk.

### D. Standard P1 only; everything else over the management channel

C&C stays strictly standard P1. Everything specific to the G7250 (ATU, PA, antenna,
telemetry) goes over the separate management channel (0001, spec section 10).

- For: the P1 stream is fully standard, and no C&C extensions are needed at all.
- Against: the management channel is meant for update, configuration, logs and
  identification, not for real-time radio control (0001, spec section 10). Antenna, filter
  and PA control would then sit on a different channel from the frequency and MOX
  commands they belong with, and the two channels would have to stay in step.
- Against: every host needs a second connection for normal operation, even for receiving.

## Decision

Option A. Standard P1 is the base. An HL2 extension is reused only if its meaning is
identical to what the G7250 needs. Everything else, and everything to do with TX safety,
gets a G7250 address.

## Consequences

- The C&C map in spec part B marks each row as standard P1, HL2-compatible extension, G7250
  extension or reserved, with a source (0001, spec section 7). An HL2-compatible row cites
  the HL2 documentation for the field it reuses.
- "Identical meaning" is checked per field against [HL2] in `sources.md`, before the row is
  written. If in doubt, the field gets a G7250 address.
- The annex "Differences from standard P1 and from the HL2 extensions" lists every
  HL2-compatible row and every G7250 extension.
- The list of G7250 functions that need C&C depends on the HIS (antenna and filter
  switching, ATU control, sensors). Until the HIS answers, part B can only reserve them.
- TX arming and safety state are specified in 0007 and 0015, not here.

## Sources

- Discussion with ON8ST, 2026-11-19.
- Decisions 0001, 0009, 0010, 0012.
- Protocol 1 documentation and HL2 documentation — to be listed in `sources.md` as [P1] and
  [HL2]; not yet checked.
- Public G7250 product specifications (Radioddity) — to be listed in `sources.md`.

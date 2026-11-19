# 0003 — Capability block: standard short discovery reply with board type 200; capability record as read-only registers in the G7250 register map

- Status: proposed (to be accepted by ON8ST)
- Date: 2026-11-19

## Context

A host has to learn what the radio can do before it uses it: name, versions, receivers,
sample rates, antennas, ATU, transmit power, telemetry, which streams exist, and whether
level 2 exists and is active. 0001 called this the "capability block" (spec section 4) and
first proposed putting it in the spare bytes of the discovery reply, with a magic number and a
version. That proposal was made for Protocol 1. Level 1 is now G7250-P2, openHPSDR Protocol 2
with board type 200 (0016, 0002), and 0016 asked to check first whether P2's own
self-description covers the need.

What P2 offers [P2]:

- **Discovery.** The host sends a 60-byte Discovery packet to port 1024: byte 4 = 0x02,
  bytes 5–59 zero. The packet has no field in which the host can ask for a particular reply
  format.
- **Two reply formats.** "In order to allow for SDR hardware to provide complete details of
  all features available two reply formats are provided": (1) "where prior knowledge of the
  hardware is known by the Host software", and (2) "where the full description of the
  configuration of the hardware and its capabilities are provided".
- **Short reply (format 1), 60 bytes.** Byte 4 = 0x02 (0x03 if already connected to another
  host), bytes 5–10 MAC, byte 11 board type, byte 12 protocol version supported, byte 13
  firmware code version, bytes 14–19 Mercury 0–3, Penny and Metis code versions (Atlas
  systems only), byte 20 number of DDCs implemented, byte 21 frequency or phase word,
  byte 22 available endian modes and IQ formats, byte 23 beta version. Bytes 24–59 are
  "Reserved for future use (AD0ES)" in the table; the text says "Byte 24 – Reserved".
- **Reserved discovery bytes are being claimed.** The revision history of V3.1 says
  "Reserved … Byte 23 of Discovery Reply Packet for future use" (AD0ES). In V4.4 byte 23 is
  "Beta version" and the reservation for AD0ES sits on byte 24. Whatever the exact history, the
  reserved area of this reply is not free; it is held for someone else's future use.
- **Board type 255 (Appendix C).** A long reply (bytes 0–1439) with byte 11 = 255. It has
  flags and values such as host update of firmware supported (byte 20), memory mapped
  registers supported (byte 23), DSP clock (bytes 27–30), number of ADCs (byte 36), number of
  DDCs (byte 39), wideband data (bytes 42–50), individual DDC sample rates and minimum and
  maximum DDC rate in ksps (bytes 51–55), synchronous DDCs (byte 57), DDC Audio CODEC
  (byte 59), number of DUCs (byte 70), microphone (byte 72), DUC I&Q rate and format
  (bytes 79–82), CW and open-collector features (bytes 84–93), DDC calibration (bytes 94–95),
  number of general-purpose ADCs (byte 96). Bytes 14–19 are "Spare" and bytes 97–1439 are
  "For future use". There is no field for a board name, vendor, antennas, an internal ATU,
  transmit power, or sensors other than through general-purpose ADCs.
- **Board type 254 (Appendix B, XML).** "To be written".
- **An inconsistency.** The text under byte 4 of the short reply says that byte 4 = 0xFE
  (0xFF if running) means "subsequent bytes contain the hardware configuration", with a
  reference to Appendix A. Appendix C itself uses byte 4 = 0x02/0x03 and byte 11 = 255.
  Which of the two existing hosts follow, if any, has not been checked (unverified).
- **Memory-mapped registers.** A packet from the host and one from the hardware, each with up
  to 240 pairs of a 16-bit address and a 32-bit data word (bytes 4–1443). The hardware-to-host
  packet "should be sent whenever data changes and optionally periodically". P2 defines no
  read request, no address map and no default port (both ports are "xxxx"; General packet
  bytes 29–32 set them).
- **Session start.** After discovery the host sets up the General, DDC and DUC packets and
  then sends a High Priority packet with the run bit. A host that sends C&C to hardware that
  is already connected to another host takes it over. P2 does not say whether a memory-mapped
  register packet counts as a C&C packet for takeover or for the one-second watchdog
  (unverified; the "Detailed operation" section speaks only of "any C&C packet").

What is already decided:

- Board type 200 in byte 11; the name "G7250-P2" goes in the capability block, not in the
  board type (0002). Using 255 would hide 200; 0002 asks this decision to solve that.
- G7250-specific functions live in a G7250 register map carried by the P2 memory-mapped
  register packets. Standard P2 fields are used only where their meaning is identical.
  Reserved bytes in the standard packets are not used (0005).
- A host that does not know board type 200 may receive but never transmit; TX needs an arm in
  the register map, and the radio reports the arm state in a G7250 register (0015).
- No DDC audio, no socket on port 1028 (0017). One receiver is assumed (0001, HIS-02 open).
- The capability block of level 1 says whether level 2 exists and whether it is active
  (0011).
- The CH394Q has 8 sockets; G7250-P2 with one receiver uses 7, the register map included; one
  is left for the management channel (0017, 0008, `analysis/ch394-network-budget.md`).
- Sample rates are being decided in 0004 (written in parallel). This decision assumes
  48–384 ksps as provisional, final after HIS-01 (`analysis/ch394-network-budget.md`).

## Options considered

### A. Standard short discovery reply with board type 200; capability record as read-only registers in the G7250 register map (chosen)

The discovery reply is the P2 short format (format 1), filled exactly as P2 defines it:
board type 200, true values in bytes 12–23, bytes 24–59 zero. Everything else a host needs to
know is a **capability record**: a block of read-only registers at a fixed place in the
G7250 register map (0005), sent by the radio in standard P2 memory-mapped register packets.

- For: the discovery reply is plain P2. Every field has its P2 meaning; nothing in it can
  collide with a later P2 revision. That is what 0009 and 0005 ask.
- For: board type 200 stays visible in byte 11, so a host knows "this is a G7250" from the
  first packet (0002). Format 1 is the format P2 itself defines for hardware "where prior
  knowledge of the hardware is known by the Host software", which is exactly the case for a
  host with a G7250 backend.
- For: a generic P2 host still gets what it needs to set up receive from the standard bytes
  (number of DDCs, frequency or phase word, endian modes and IQ format; bytes 20–22) [P2].
- For: the register map already exists for G7250 control (0005), and it has room: 65,536
  addresses, 240 address/data pairs per packet [P2]. The capability record needs no new
  packet type, no new port and no extra socket; it uses the register-map socket that is
  already in the budget (0017).
- For: the record can be versioned and extended without limit from P2, because P2 assigns no
  addresses in the memory-mapped space [P2]. Fields can be as rich as the G7250 needs (a
  transmit-power table per band, telemetry flags), which neither 36 reserved bytes nor
  Appendix C can hold.
- For: only a host that knows the G7250 reads the record. That is the same group of hosts that
  can use the register map at all, and the same split as the TX arm (0015).
- Against: the capabilities are not in the discovery reply. A host has to send one more
  packet to the register port and wait for the answer before it knows sample rates, antennas
  and power.
- Against: P2 has no register read request. The spec has to define one (a request register,
  see Decision) and say where the answer goes when the host has not yet set the
  memory-mapped ports in a General packet.
- Against: P2 does not say whether a memory-mapped packet is C&C. A host must be able to read
  the record of a radio that is already in use without taking it over and without touching
  the watchdog. The G7250 has to define this, and it is a clarification of P2 to be listed in
  the annex "Differences from standard P2".
- Against: the default memory-mapped port is "xxxx" in P2 [P2], so the G7250 picks one (0005).
  A host must know that port before it can read anything; it learns it from the G7250 spec,
  not from the radio.

### B. Board type 255 with the Appendix C full hardware description

Report byte 11 = 255 and fill the Appendix C reply [P2].

- For: it is the self-description that P2 itself defines, and analysis `p1-vs-p2.md` and 0016
  pointed at it as the natural place.
- For: a host that already parses Appendix C learns the DDC, DUC, sample-rate, wideband and
  audio facts of the G7250 without any G7250-specific code. The "Memory mapped registers
  supported" flag (byte 23) would announce the register map in a standard way, and "DDC Audio
  CODEC supported" = 0 (byte 59) would say what 0017 needs.
- Against: byte 11 can only hold one value. With 255 the board type 200 is gone, and
  Appendix C has no field for a name or vendor [P2]. A host cannot tell a G7250 from any other
  board that uses 255. This is exactly the problem 0002 raised.
- Against: Appendix C has no fields for antennas, an internal ATU, an external tuner
  interface, transmit power per band or mode, sensors, TX arm, or level 2. Those would have to
  go either in its spare bytes 14–19 and "For future use" bytes 97–1439, which 0005 rules out,
  or in the register map anyway. So option B does not remove the register-map record; it only
  adds a second description that must be kept consistent with it.
- Against: whether existing P2 hosts handle board type 255 at all, and whether they follow
  Appendix C or the 0xFE/0xFF wording under byte 4, has not been checked (unverified). It is
  possible that no host parses it.
- Against: a host that does not know the G7250 but parses Appendix C would get a complete
  description of a radio it cannot transmit on (0015) and would have no way to see why.

### C. A capability record in the reserved bytes 24–59 of the short discovery reply, with magic and version

Keep board type 200 and put a G7250 record (magic number, version, fields) in the 36 bytes
that P2 marks reserved. This was the first idea in 0001, for P1.

- For: everything is in one packet that every host receives anyway. A host knows all
  capabilities right after discovery, before any session and without any risk of taking over
  a running radio.
- For: the magic number and version would let a host tell a G7250 record from zeros or from
  another vendor's use of the bytes.
- Against: the bytes are reserved by P2, and the table marks them "Reserved for future use
  (AD0ES)": they are held for a named future use [P2]. The revision history shows that this
  reserved area of the discovery reply has been touched before (V3.1, byte 23) [P2]. The rule
  of 0005, "reserved bytes in the standard packets are not used", is written for the C&C
  packets, but its reason applies here word for word: a later revision can give the bytes a
  meaning, and a host following that revision would misread a G7250. This decision therefore
  states that the rule of 0005 also covers the discovery reply, including bytes 24–59.
- Against: a magic number lowers the risk but does not remove it. A host following a later
  P2 revision would not look for our magic; it would just read the bytes.
- Against: 36 bytes are too small for the full list (name, versions, sample-rate set,
  antennas, ATU, a transmit-power table for ten bands [G7250-MAN], telemetry, level 2). A
  second place would be needed anyway.
- Against: it reads as standard P2 but is not, the same objection as 0005 option B.

### D. Capabilities only over the management channel

Leave discovery and the register map without any capability record; a host asks the
management channel (0001 spec section 10, 0008).

- For: P2 is not touched at all, not even by a read-only register range.
- Against: the management channel is not designed yet (0008), and it is meant for update,
  configuration, logs and identification (0001), not for the facts a P2 host needs to open an
  IQ session.
- Against: every host needs a second protocol and a second connection just to start
  receiving. The management channel has the one remaining socket (0017); its protocol and
  port are open.
- Against: 0011 asks for the active level to be visible in the capability block of level 1
  itself, not only in the management channel.
- The management channel may still **repeat** identification and level information; that is a
  question for 0008, not an alternative to a level-1 record.

### E. Board type 200 normally, the Appendix C reply only on a G7250-specific request

Answer discovery with the short reply (200), and send an Appendix C reply (255) only when the
host asks for it, for example with a flag in the discovery packet or a second discovery
packet in a G7250 format.

- For: board type 200 stays visible by default, and a host that wants Appendix C can still get
  it.
- Against: the Discovery packet has only zero bytes after byte 4 [P2]. A flag there is a use of
  bytes P2 defines as zero, the same objection as option C.
- Against: all the objections to option B about missing fields remain: a register-map record
  is still needed, and two descriptions must agree.
- Against: a host that asks for the 255 reply must already know the G7250, so it can just as
  well read the register map.

### F. Two discovery replies, one with board type 200 and one with 255

- For: no request flag needed; both pieces of information arrive.
- Against: P2 hosts list one device per reply. A host would very likely show two radios with
  the same MAC and IP (unverified, but a real risk). Rejected.

### G. A G7250 command code on port 1024 that returns a capability packet

Define a new byte-4 command value (P2 uses 0x02 discovery, 0x03 set IP address, 0x04 erase,
0x05 program [P2]) whose reply carries the capability record.

- For: like option C, the record could be read before any session, on the port every host
  already uses.
- Against: unassigned command codes are the same kind of space as reserved bytes; a later P2
  revision may assign the value.
- Against: it adds a packet type that no P2 document describes, while the register map
  already gives a P2-defined place.

## Decision

Option A.

### 1. Discovery reply

G7250-P2 answers a Discovery packet with the P2 short reply (format 1) [P2]:

| Byte | Content on the G7250 | Source |
|------|----------------------|--------|
| 0–3 | sequence number 0 | [P2] |
| 4 | 0x02, or 0x03 when another host has a session (the case of level 2 active is open, see Consequences) | [P2], 0011 |
| 5–10 | MAC address | [P2]; storage HIS-15 |
| 11 | 200 | 0002 |
| 12 | P2 version implemented, decimal (44 for V4.4) | [P2] |
| 13 | firmware version in P2 form (decimal, "15 = 1.5"); the full version is in the capability record | [P2] |
| 14–19 | 0 (Atlas only) | [P2] |
| 20 | number of DDCs; must equal the record field `num_ddc` | [P2]; HIS-02 |
| 21 | 0 = frequency, 1 = phase word | [P2]; HIS-04 |
| 22 | endian modes and IQ formats supported | [P2]; 0004 |
| 23 | 0, or non-zero for a beta firmware | [P2] |
| 24–59 | 0 | rule below |

The G7250 never reports board type 254 or 255, never uses byte 4 = 0xFE/0xFF, and does not
send the Appendix C reply.

**Reserved bytes in the discovery reply.** The rule of 0005 ("reserved bytes in the standard
packets are not used") also covers the discovery reply. Bytes 24–59 are sent as zero and carry
no G7250 meaning. Bytes 14–19 are sent as zero.

### 2. Capability record

- **Place.** A read-only range of the G7250 register map, `CAP_BASE` to
  `CAP_BASE + CAP_LENGTH − 1`. The exact addresses are fixed in spec part B; this decision
  proposes `CAP_BASE` = 0x0000. The whole range is at most 239 registers, so that one
  hardware-to-host memory-mapped packet (240 pairs [P2]) carries the request echo plus the
  whole record, and a host always sees one consistent copy.
- **Encoding.** One field per 32-bit register, big-endian like the rest of P2 [P2]. Text is
  ASCII, 4 characters per register, first character in bits [31:24], padded with 0x00.
  Frequencies in Hz (32 bits reach 4.29 GHz). Power in units of 0.1 W.
- **When it is sent.**
  1. On request: the host writes the register `CAP_REQUEST` (an address in the G7250 control
     range, fixed in part B). The radio answers with one memory-mapped packet that holds the
     whole record.
  2. Once, unasked, when a host starts a session (its first General packet).
  Writes to any address in the record range are ignored, and the radio answers with the
  current values (so a host can see that the write had no effect).
- **Reading without taking over.** A memory-mapped packet that contains only a write to
  `CAP_REQUEST` is not C&C on the G7250: it does not take over a session, does not start one,
  and does not feed the watchdog. The answer goes to the source IP address and port of the
  request when the host has no session; otherwise to the host's memory-mapped port set in the
  General packet (bytes 31–32) [P2]. This is a clarification of P2 and is listed in the annex
  "Differences from standard P2".
- **Stability.** The values are constant for the duration of a session. They may change only
  between sessions (for example after a firmware update, a region change of the TX bands, or a
  change of the active level). Dynamic state is not part of the record: TX armed (0015), fault
  state and limits in force (0007), and telemetry values (0006) are separate status registers.

### 3. Fields (record version 1.0)

Offsets are relative to `CAP_BASE`. "HIS-nn" means the value is not known yet and comes from
that HIS question; the value shown is the current assumption. Bit numbers are 0 = LSB.

| Offset | Name | Content | Value / source |
|--------|------|---------|----------------|
| 0x00 | `cap_magic` | ASCII "G725" = 0x47373235 | this decision |
| 0x01 | `cap_version` | [31:16] major, [15:0] minor of this record format | 1.0 |
| 0x02 | `cap_length` | number of registers in the record, header included | as built |
| 0x03 | `regmap_version` | [31:16] major, [15:0] minor of the G7250 register map (0005) | part B |
| 0x04–0x07 | `product_name` | "G7250-P2", padded with 0x00 (16 characters max) | 0002, 0016 |
| 0x08 | `fw_version` | [31:24] major, [23:16] minor, [15:0] build | as built |
| 0x09 | `p2_version` | P2 version implemented, as discovery byte 12 | [P2] |
| 0x0A | `hw_revision` | main-unit hardware revision, 0 = not identified | HIS-18 (unverified whether a revision can be read at all) |
| 0x0B | `level` | bit 0 level 1 present (always 1); bit 1 level 2 present in this firmware; bit 2 level 2 active; bits [7:4] active level (0 none, 1, 2) | 0011; level 2 only after G6 |
| 0x0C | `streams` | bit 0 RX IQ; bit 1 TX IQ (DUC); bit 2 DDC audio (always 0, 0017); bit 3 microphone data; bit 4 wideband data; bit 5 time stamping of IQ | bit 0 = 1; bit 1 per `tx` below; bit 3 HIS-17 (assumed 0); bit 4 HIS-01, HIS-18 (assumed 0); bit 5 = 0 |
| 0x0D | `num_adc` | number of RF ADCs | HIS-01, HIS-03 (assumed 1) |
| 0x0E | `num_ddc` | number of DDCs; equals discovery byte 20 | HIS-02 (assumed 1) |
| 0x0F | `num_duc` | number of DUCs | assumed 1: one transmitter [G7250-MAN]; how it is built is HIS-18 |
| 0x10 | `ddc_rates` | bit mask of P2 DDC rates: bit 0 48, bit 1 96, bit 2 192, bit 3 384, bit 4 768, bit 5 1536 ksps [P2] | provisional 0x0F (48–384 ksps), 0004, HIS-01 |
| 0x11 | `duc_format` | [31:16] TX IQ rate in ksps, [7:0] bits per sample | 192, 24 [P2]; HIS-18 for feasibility |
| 0x12 | `dsp_clock_hz` | DSP clock in Hz, same meaning as Appendix C bytes 27–30 | HIS-04 |
| 0x13 | `rx_range_count` | number of valid receive ranges below (max 4) | 2 [G7250-MAN] |
| 0x14–0x1B | `rx_range[0..3]` | pairs of start Hz, stop Hz | 500,000–30,000,000; 50,000,000–54,000,000 [G7250-MAN] |
| 0x1C | `antennas` | [7:0] number of antenna connectors; bit 8 host can select; bit 9 separate RX-only input | 2 [G7250-MAN]; bit 8 HIS-06; bit 9 HIS-06/-07 (assumed 0) |
| 0x1D | `atu` | bit 0 internal ATU present; bit 1 host can control it; bit 2 per-band memory; bit 3 external tuner interface present; bit 4 host can control the external tuner interface | bits 0, 2, 3 = 1 [G7250-MAN]; bit 1 HIS-08; bit 4 HIS-09 |
| 0x1E | `atu_range` | [31:16] minimum, [15:0] maximum load in Ω | 20, 150 [G7250-MAN] |
| 0x1F | `telemetry` | bit 0 forward power; bit 1 reverse power; bit 2 PA temperature; bit 3 supply voltage; bit 4 supply current; bit 5 PA current; bit 6 ADC overload | HIS-11; meaning and scale in 0006 |
| 0x20 | `tx` | bit 0 TX hardware present; bit 1 TX implemented in this firmware (0 before M4); bit 2 TX arm required (always 1, 0015) | bit 0 = 1 [G7250-MAN]; bit 1 per milestone; bit 2 = 1 |
| 0x21 | `tx_band_count` | number of valid entries below (max 16) | 10 [G7250-MAN] |
| 0x22–0x51 | `tx_band[0..15]` | 3 registers per band: start Hz; stop Hz; [31:16] maximum power SSB/CW/FM, [15:0] maximum power AM, both in 0.1 W | ranges per region [G7250-MAN]; 100 W SSB/CW/NFM, 25 W AM [G7250-MAN]; 50 MHz power not in the manual (90 W in [G7250-PUDX], [G7250-RIGPIX], unverified), HIS-12 |
| 0x52 | `mgmt` | bit 0 management channel present; [31:16] its port | 0008 |
| 0x53 | `regmap_groups` | bit mask of register groups present in the G7250 map (for example antenna, ATU, TX arm and safety, telemetry, external interfaces); assignment in part B | 0005, 0007 |

Notes on the fields:

- The transmit-power values are the nominal maxima of the hardware in the configured region,
  not the limits in force. The safety core may set lower limits (0007, 0011); those are status,
  not capability.
- Where a field has an Appendix C counterpart (`num_adc` byte 36, `num_ddc` byte 39,
  `dsp_clock_hz` bytes 27–30, DDC audio byte 59, microphone byte 72, DUC rate and format
  bytes 79–80) [P2], it uses the same meaning, so that code written for Appendix C maps over
  directly. Only the location differs.
- `streams` bit 2 and `num_ddc` must agree with what the radio actually does: no socket on
  port 1028 (0017), and only as many DDC I&Q ports as `num_ddc` (`analysis/ch394-network-budget.md`).

### 4. Versioning and extension rules

1. `cap_version` minor changes only add fields at the end of the record and increase
   `cap_length`. A host reads `cap_length` and ignores registers beyond the fields it knows.
2. A field that a host knows but that lies beyond `cap_length` counts as absent: its value is
   "no" for flags and "not reported" for numbers.
3. Unused bits in a bit mask are 0 and may get a meaning in a later minor version. Hosts ignore
   bits they do not know. A new bit is always defined so that 0 means the old behaviour.
4. A field is never moved, removed or given a different meaning within one major version.
   Such a change needs a new major version. A host that does not know the major version must
   not rely on the record. It may still receive with the standard P2 setup, as any other host
   (0015), and should tell the user that the firmware is newer than the host.
5. `cap_magic` never changes. A host that reads a different magic is not talking to a G7250
   capability record.
6. `regmap_version` is versioned by the same rules, independently of the record. A host
   decides which register groups to use from `regmap_groups`, not from comparing version
   numbers.
7. The record never uses more than 239 registers (one packet, see section 2). If that is ever
   too small, a second range is added with its own request register, announced by a bit in
   `regmap_groups`.

### 5. A host that does not know board type 200

- It sees a standard P2 short reply with an unknown board type in byte 11 and true values in
  bytes 12–23. Whether it lists the radio, refuses it, or treats it as a generic P2 device
  depends on the host and has not been checked for any host (unverified; 0015).
- If it opens a session, it can set up receive from bytes 20–22 and the standard DDC packets,
  at a rate the G7250 supports. Rates outside `ddc_rates` are handled as specified in 0004.
- It never reads the capability record and never writes the register map, so it never arms TX
  and cannot transmit (0015).
- It may send DDC audio to port 1028, where nothing listens (0017).
- A host that parses Appendix C will find no Appendix C reply and fall back to whatever it does
  for an unknown short reply.

## Consequences

- Spec section 3 (discovery) gets the byte table of section 1 above, with bytes 14–19 and
  24–59 sent as zero.
- Spec section 4 (capability block) gets the field table, the encoding, the request and answer
  rules, and the versioning rules. Addresses are fixed there, in the register map of part B.
- 0005 is read as covering the discovery reply too (section 1 above). 0005 itself need not
  change, but part B states the rule for all standard packets, the discovery reply included.
- 0002's open point is settled: board type 200 stays in byte 11; the G7250 does not use 255,
  so no way to give both is needed. The name "G7250-P2" is in `product_name`.
- 0005's consequence "the G7250 sets the Memory mapped registers supported flag in its full
  description, if the capability block uses that reply" does not apply: there is no full
  description. A G7250 host knows the register map from board type 200 and the spec.
- 0017's consequence on Appendix C byte 59 does not apply either; DDC audio = 0 is reported in
  `streams` bit 2.
- The memory-mapped default ports must be fixed in part B before M1 (0005), because a host
  needs them to send `CAP_REQUEST`.
- Part B defines `CAP_REQUEST` and the rule that a request-only memory-mapped packet is not
  C&C (no takeover, no watchdog effect). It goes in the annex "Differences from standard P2".
  0007 must check that this does not open a path around the single-owner rule; it cannot,
  since the record is read-only, but the check belongs there.
- The reference model and conformance tests in g7250-testbench check: discovery reply bytes
  (including zero bytes 14–19 and 24–59), `num_ddc` = byte 20, record answer in one packet,
  writes to the record ignored, request without session does not take over or start a session.
- The AetherSDR G7250 backend reads the record after discovery and before opening a session,
  and uses it for sample rates, antennas, ATU, TX power and the TX implemented flag. This goes
  in the annex "Changes needed in AetherSDR".
- 0004 must agree with `ddc_rates` and with discovery byte 22. 0006 defines the telemetry bits
  and their scale. 0008 decides whether the management channel repeats identification and the
  active level, and fills `mgmt`.
- Every field marked HIS-nn above stays provisional until the HIS answers. M1 needs at least
  HIS-01, -02, -04, -15 for the values in this record (design note, section 6).

## Open points for ON8ST

- What discovery reports while level 2 is active: byte 4 = 0x03 ("in use", the closest P2
  meaning [P2]), or no reply at all? Proposed: 0x03, with `level` bits [7:4] = 2 in the record.
  To be settled with 0008 and spec part A.
- Is it acceptable that the capability record is not in the discovery reply, so that a host
  needs one extra request? The alternative with everything in discovery (option C) conflicts
  with the reserved-bytes rule.
- Is a transmit-power table per band and mode in the record wanted, or is a single maximum per
  mode enough? The table follows the per-region band list of [G7250-MAN].
- Should the record carry a unit serial number? Not proposed: the MAC address is already in the
  discovery reply, and a serial would depend on HIS-15/HIS-18.

## Sources

- Discussion with ON8ST, 2026-11-19 (task brief for this decision).
- Decisions 0001, 0002, 0004 (being written), 0005, 0006–0008 (reserved), 0009, 0011, 0015,
  0016, 0017.
- `analysis/p1-vs-p2.md`, `analysis/ch394-network-budget.md`, `open-questions-his.md`
  (HIS-01, -02, -03, -04, -06, -07, -08, -09, -11, -12, -15, -17, -18).
- [P2] openHPSDR Ethernet Protocol V4.4, github.com/TAPR/OpenHPSDR-Firmware,
  `Protocol 2/Documentation/`: "Detailed operation" (session start, takeover, "any C&C
  packet"); Discovery packet (bytes 4–59); Discovery reply, format 1 (bytes 0–59, byte 4
  including the 0xFE/0xFF note, board type list, bytes 12–24); command codes 0x02–0x05;
  General packet bytes 29–32; Memory mapped registers from PC and from hardware (bytes 0–1443,
  "sent whenever data changes and optionally periodically", default port "xxxx"); DDC sample
  rates 48/96/192/384/768/1536 ksps; Appendix B ("To be written"); Appendix C (bytes 11–96 and
  97–1439); revision history V3.1.
- [G7250-MAN] Xiegu G7250 Operation Manual rev 0.1: receive and transmit ranges, TX power,
  antennas, ATU, TUNER interface.
- [G7250-PUDX], [G7250-RIGPIX]: 90 W on 50 MHz (secondary, unverified).

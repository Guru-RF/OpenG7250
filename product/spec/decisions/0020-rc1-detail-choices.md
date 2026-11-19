# 0020 — Detail choices for spec release candidate rc1 (network interface, parts A and B)

- Status: proposed (for ON8ST review at rc1), 2026-11-19
- Date: 2026-11-19
- Applies to: `spec/network-interface.md` (draft 3, rc1 candidate), parts A and B.
- Builds on: 0003, 0004, 0005, 0006, 0007, 0008 (accepted), 0011, 0015, 0016, 0017; agrees
  with 0021 (TCI profile choices) on §2, §25 and §31.

## Context

The rc1 definition of done says: every "TBD" left in the spec carries a HIS id (a hardware
value); every other open point is closed by a design choice. Decisions 0003–0008 leave a
number of values to "spec part A" or "spec part B" (0003, "Not for ON8ST, left to spec part
B"; 0005, Consequences; 0007, "Still open"; 0008, Consequences). This decision collects those
choices in one place so that ON8ST can review them together. None of them depends on the
hardware; where a value does, it stays "TBD (HIS-xx)" in the spec.

The AetherSDR survey (`spec/annex-aethersdr.md`, questions Q-S1 to Q-S4) raised four points
for part B; they are decided in §13 and §14.

Each item gives the choice, one to three alternatives, and the reason. The section number
(§n) is what the spec cites as "0020 §n".

Sources used throughout: [P2] openHPSDR Ethernet Protocol V4.4; [CH394] WCH CH394 manual 1,
V1.2; [G7250-MAN]; [AETHER-SRC]; [PIHPSDR]; decisions listed above.

---

## 1. Register-map UDP port: 7250

**Choice.** The G7250 register map uses local UDP port **7250**, for both directions (0005,
Consequences). It is the default of [P2] General packet bytes 29–30 (the port the G7250
receives on). Bytes 31–32 are decided in §13.

- Alternative A: 1030 (next to the P2 defaults). For: easy to remember next to 1024–1029.
  Against: [P2] General bytes 21–22 put the wideband ports at base 1027 plus 0–7, so
  1027–1034 are P2 defaults; 1030 collides with the default wideband port of ADC3.
- Alternative B: 1115 (just above the DDC range 1035–1114). For: outside every P2 default.
  Against: no mnemonic; a reader may take it for a 81st DDC port.
- Alternative C: an IANA "dynamic" port (49152–65535). For: never registered to anyone.
  Against: hosts and firewalls often treat that range as ephemeral; a host's own socket may
  get the same number, which confuses captures.

**Reason.** 7250 lies outside every range a P2 host places radio-side ports in by default:
1024–1029, wideband 1027–1034 and DDC 1035–1114 ([P2] General bytes 5–22). It names the
radio, so it is easy to recognise in a capture. The port only has to be unique on the radio
itself (the G7250 is the only listener at its address), so a registration elsewhere does not
matter; the IANA registry was not checked.

## 2. Management UDP port: 7251

**Choice.** The management channel uses local UDP port **7251** (0008, Transport 1–2).

- Alternative A: 1024 + a command code (shared with P2). Against: rejected in 0008 (T3).
- Alternative B: 50250 or another high port. For: far from P2. Against: no relation to the
  register port; in the ephemeral range on many systems.

**Reason.** Outside 1024–1029 and 1035–1114 as 0008 Transport 2 requires, and outside the
wideband defaults 1027–1034 ([P2] General bytes 21–22). Next to the register port, so one
firewall rule "UDP 1024–1035, 7250–7251" covers a G7250 with one DDC.

## 3. Register address map, groups and `regmap_groups`

**Choice.** 16-bit addresses ([P2] memory-mapped packets, Address [15:0]) in blocks of 256
registers. Each block is one group; bit *n* of `regmap_groups` says group *n* is present.

| Group bit | Block | Group | Present |
|-----------|-------|-------|---------|
| 0 | 0x0000–0x00FF | capability record (`CAP_BASE` = 0x0000, 0003 §2); 0x0000–0x00EE usable (239 registers), 0x00EF–0x00FF reserved | always |
| 1 | 0x0100–0x01FF | session and stream status, requests | always |
| 2 | 0x0200–0x02FF | TX arm, TX state, limits and faults | from M3 (arm accepted only when `tx` bit 1 = 1) |
| 3 | 0x0300–0x03FF | telemetry | when at least one sensor exists (HIS-11) |
| 4 | 0x0400–0x04FF | internal ATU | per HIS-08 |
| 5 | 0x0500–0x05FF | antenna | per HIS-06 |
| 6 | 0x0600–0x06FF | front end and filters (reserved) | 0 until HIS-07 |
| 7 | 0x0700–0x07FF | external interfaces (SEND, TUNER; reserved) | 0 until HIS-09 |
| 8–31 | 0x0800–0x1FFF | reserved for later groups | 0 |
| — | 0x2000–0xFFFE | reserved | — |
| — | 0xFFFF | no-operation (padding) address, §4 | — |

Registers:

| Address | Name | Address | Name |
|---------|------|---------|------|
| 0x0100 | `CAP_REQUEST` | 0x0213 | `FAULT_CLASS` |
| 0x0101 | `STREAM_STATUS` | 0x0214 | `TRIP_COUNT` |
| 0x0102 | `LINK_STATUS` | 0x0215 | `FAULT_CLEAR` |
| 0x0103 | `WRITE_STATUS` | 0x0220 | `LIMIT_STATUS` |
| 0x0200 | `TX_ARM_TOKEN` | 0x0230 | `LIMIT_TX_TIME` |
| 0x0201 | `TX_ARM` | 0x0231 | `LIMIT_FWD_POWER` |
| 0x0202 | `TX_ARM_STATE` | 0x0232 | `LIMIT_SWR` |
| 0x0203 | `TX_STATE` | 0x0233 | `LIMIT_PA_TEMP` |
| 0x0204 | `TX_MODE_CLASS` | 0x0234–0x023F | further limits (reserved) |
| 0x0205 | `KEYED_TIMEOUT` | 0x0300–0x0303 | `TLM_PA_TEMP` (sensors 0–3) |
| 0x0206 | `WATCHDOG_STATE` | 0x0304 | `TLM_PA_CURRENT` |
| 0x0210 | `SAFETY_STATE` | 0x0305 | `TLM_SUPPLY_CURRENT` |
| 0x0211 | `FAULT_CODE` | 0x0306 | `TLM_SWR` |
| 0x0212 | `FAULT_FLAGS` | 0x0307 | `SENSOR_VALID` |
| 0x0400 | `ATU_TUNE` | 0x0401 | `ATU_STATE` |
| 0x0500 | `ANT_STATE` | | |

The 0007 "trip counter" is named `TRIP_COUNT`. `WRITE_STATUS` is new (§11).

- Alternative A: one flat list from 0x0100 upwards. For: compact. Against: no room to grow a
  group without splitting it; a group bit then means nothing.
- Alternative B: groups of 4096. For: more room. Against: no need; 256 per group is ample, and
  smaller blocks keep a host's sparse table small.

**Reason.** Groups map one-to-one to `regmap_groups` bits (0003 §3, §4 rule 6), so a host
decides from one bit and one block. The record block keeps the 239-register ceiling
(0003 §2) with room for 0x00EF–0x00FF as a guard. Gaps inside each block (0x0207–0x020F,
0x0216–0x021F) leave room for related registers.

## 4. Memory-mapped packet length and padding

**Choice.** A memory-mapped packet carries *n* pairs, 1 ≤ *n* ≤ 240, and is 4 + 6*n* bytes
long. The G7250 sends only the pairs it has (variable length). It accepts any length ≥ 10;
a trailing incomplete pair is ignored. Pairs with address 0xFFFF are padding and ignored.
The pair (0x0000, 0x00000000) is also treated as padding, since `cap_magic` is never 0, so a
host that pads a 1444-byte packet with zeros gets no answers for the padding.

- Alternative A: always 1444 bytes ([P2] shows 240 pairs). For: one size. Against: wastes SPI
  time and network for one-pair echoes; [P2] does not say the packet must be full.

**Reason.** [P2] defines the pair layout but not a count field; length is the only count.
Short packets keep event pushes cheap (0006 rates).

## 5. `CAP_REQUEST` value

**Choice.** Writing **0x00000001** requests the record. Other values are rejected
(`BAD_VALUE`, §11) and reserved for later requests (for example a second range, 0003 §4
rule 7 gives it its own register anyway).

- Alternative: any value requests the record. For: simplest. Against: no room for variants;
  a stray write triggers a 240-pair answer.

**Reason.** Explicit, cheap, extensible.

## 6. `regmap_version` starting value

**Choice.** **0x00010000** (1.0) in the first firmware that ships the register map; minor
increases when registers are added, major when one changes meaning (0003 §4 rule 6).

- Alternative: 0x00000001 (0.1) until M4. Against: a host would treat every pre-M4 build as
  unstable; groups already say what exists.

**Reason.** Same start as `cap_version` (0003 §3).

## 7. `ARM_MAGIC` value and the token

**Choice.** `ARM_MAGIC` = **0x47375458** (ASCII "G7TX"). The token MUST also never equal
`ARM_MAGIC`, since `token XOR ARM_MAGIC` would then be 0, which disarms (0007 Decision 1).
A correct arm write while already armed with the same token is a no-op and is echoed; it
does not raise the generation.

- Alternative A: 0xA5A5A5A5. For: classic pattern. Against: unreadable in a capture; easily
  produced by memory-test patterns.
- Alternative B: a random constant. Against: no benefit; the arm is not security (0007, 1C).

**Reason.** Readable in a hex dump, non-zero, not 0xFFFFFFFF, different from `cap_magic`
(0x47373235).

## 8. Bit layouts and reason codes

**Choice.** All registers are 32-bit, bit 0 = LSB (0003 §2). Unused bits are 0; codes not
listed are reserved.

`TX_ARM_STATE`: [3:0] state 0 disarmed, 1 armed, 2 inhibited; [15:8] last reject reason;
[23:16] last drop reason; [31:24] arm generation (+1 per accepted arm, wraps at 255).

Arm reject reasons: 0 none; 1 `NOT_OWNER`; 2 `NOT_RUNNING`; 3 `WATCHDOG_DISABLED`;
4 `IN_FAULT`; 5 `INHIBITED`; 6 `PTT_ACTIVE`; 7 `LEVEL_NOT_ACTIVE`; 8 `MAINTENANCE`;
9 `NO_MODE_CLASS`; 10 `BAD_TOKEN`; 11 `TX_NOT_IMPLEMENTED`.

Drop reasons (0007 drop list): 0 none; 1 `HOST_DISARM`; 2 `RUN_CLEARED`; 3 `WATCHDOG`;
4 `TAKEOVER`; 5 `RESET` (state after reset); 6 `FAULT` (events 6 and 13); 8 `LINK_DOWN`;
9 `SESSION_CHANGED`; 10 `LEVEL_CHANGE`; 11 `MAINTENANCE`; 12 `REDISCOVERY`;
0x40 + limit id: `LIMIT_<name>` (event 7).

Limit ids (shared by `LIMIT_STATUS`, `TX_STATE` and drop reasons): 1 TX frequency; 2 SWR;
3 PA temperature; 4 forward power; 5 supply voltage; 6 supply or PA current; 7 maximum
continuous TX time; 8 ATU tune time; 9 sensor plausibility; 10 RF while not keyed.

`TX_STATE`: bit 0 keyed (PA actually keyed); bit 1 a `WARN` is active; bit 2 a `REDUCE` is
active; bit 3 last TX request not keyed because the frequency is outside the TX ranges;
bit 4 PA disabled by the host (§22); bit 5 an inhibit is active; [11:8] TX source 0 none,
1 PTT, 2 CWX, 3 KEY, 4 ATU; [23:16] last unkey reason 0 none, 1 TX request released,
2 keyed timeout, 3 TX IQ underrun, 4 limit, 5 arm dropped; [31:24] limit id when the last
unkey reason is 4.

`LIMIT_STATUS`: bit *n* = limit *n* is limiting (`WARN` or `REDUCE` active); bit 16 + *n* =
limit *n* tripped (`UNKEY` or stronger) since the last TX request.

`SAFETY_STATE`: 0 normal, 1 fault. `FAULT_CLASS`: 0 none, 1 host-clearable, 2 latched until
reset. `FAULT_CODE`: 0 none; 1–10 the limit id whose `FAULT` action fired (for example 2 =
repeated SWR trips, 3 = PA temperature T4); 16 TX path not blocked (drop event 13);
17 processor watchdog reset seen at start-up; 18 start-up self-test failed; 19 internal
error. `FAULT_FLAGS`: bit *c* set for every fault code *c* (1–31) since the last clear.
`TRIP_COUNT`: number of limit trips with action `UNKEY` or stronger since power-on,
saturating at 0xFFFFFFFF; not cleared over P2.

`STREAM_STATUS`: one byte per stream, [7:0] DDC0, [15:8] DUC0, [23:16] microphone,
[31:24] wideband. In each byte, bit 7 = running; [6:0] reason it does not run: 0 none (or
running); 1 not enabled by the host; 2 not offered by this firmware; 3 sample rate not
offered; 4 sample size not offered; 5 data format not offered (General byte 39); 6 time
stamp or VITA-49 requested; 7 wideband parameters not offered; 8 link below 100 Mbit/s;
9 not running (run bit clear); 10 maintenance (update); 11 VNA mode requested; 12 EER
requested.

`LINK_STATUS`: [15:0] negotiated speed in Mbit/s (10 or 100; 0 = link down); bit 16 full
duplex; bit 17 a non-default P2 port request was not honoured (§13), latched until the next
session; [31:24] session refusal reason 0 none, 1 link below 100 Mbit/s.

`WATCHDOG_STATE`: bit 0 General byte 38 bit [0] as last written; bit 1 effective state;
bit 2 no General packet received yet (timer counts as enabled).

`ATU_TUNE`: 1 starts a tune, 0 aborts one. `ATU_STATE`: 0 off or bypassed, 1 in line,
2 tuning, 3 tuned, 4 failed. `ANT_STATE`: [7:0] connector number from 1; 0 unknown.
`SENSOR_VALID`: bit *n* has the meaning of capability field `telemetry` bit *n*; bit 7 for
PA temperature sensors 1–3 together.

- Alternative: separate registers per field. For: no masking. Against: many more addresses
  and pushes; a state and its reason would arrive in different pairs.

**Reason.** One register holds a state and its reason, so a host sees both in one pair; codes
follow the order of the lists in 0007 so that review is easy.

## 9. `TX_MODE_CLASS` enumeration

**Choice.** 0 none declared (reset value; not writable); 1 SSB, including data modes sent as
SSB; 2 CW; 3 AM; 4 FM. Other values are rejected (`BAD_VALUE`). Power classes: 1, 2, 4 at
100 W, 3 at 25 W [G7250-MAN]. The class returns to 0 at session end; a change while keyed
takes effect at once.

- Alternative A: a separate DATA class. For: a later duty-cycle limit. Against: no such limit
  exists; part C maps data modes to SSB (0014). Can be added as value 5 in a minor version.
- Alternative B: classes by power only (100 W, 25 W). Against: loses the mode for logging.

**Reason.** Matches the power classes of [G7250-MAN] and 0007 rule 3 with the least choice.

## 10. `LIMIT_<name>` registers and units

**Choice.** Four per-session limits in milli-units (0006 option 3A): `LIMIT_TX_TIME` in ms
(built-in 300 000, 0007 Resolved 3); `LIMIT_FWD_POWER` in mW, an upper bound on all bands
and classes; `LIMIT_SWR` in 1000 × SWR, replacing S2 when stricter (S1 then becomes the
lower of S1 and the written value); `LIMIT_PA_TEMP` in m°C, replacing T3 when stricter.
Writing 0 returns the limit to its built-in value. All return to built-in at session end
(0007 rule 2).

- Alternative: units of 0.1 W and seconds. For: matches the record. Against: two unit
  systems in one register map; B8.6 already says milli-units.

**Reason.** One unit rule for the whole register map.

## 11. Write confirmation, rejected writes, ordering

**Choice.**

- Every pair of a host memory-mapped packet is processed in order. For each written address
  the G7250 answers with the pair (address, value now in force), in one or more packets sent
  within 5 ms of receipt. For `TX_ARM` the answer is `TX_ARM_STATE` (0007 rule 2).
- A rejected write leaves the value unchanged; the answer carries the value in force and a
  `WRITE_STATUS` pair: [31:16] the address, [15:8] a counter of rejections (wraps), [7:0]
  reason 1 `UNKNOWN_ADDRESS` (also an address of an absent group), 2 `READ_ONLY`,
  3 `NOT_OWNER`, 4 `BAD_VALUE`, 5 `LOOSER_LIMIT`, 6 `BUSY` (maintenance).
- The value takes effect before the answer is sent. P2 orders nothing between ports [P2]; a
  host that needs a write in force before a High Priority action MUST wait for the answer.
  Writes are idempotent except `FAULT_CLEAR` and `ATU_TUNE`, and these are harmless to
  repeat (a clear without a fault is rejected; a start while tuning is a no-op). A host MAY
  repeat a write after 100 ms without an answer.

- Alternative A: no echo; the host reads back. Against: P2 has no read request; pushes are on
  change only.
- Alternative B: echo only for rejected writes. Against: a lost echo and a lost write look
  the same.

**Reason.** Closes 0005 Consequences ("how a write is confirmed and the ordering against
High Priority packets") with one rule for every register; the reject reason is visible at
once.

## 12. Writes from non-owners

**Choice.** Only `CAP_REQUEST` is accepted from any host. Every other write from a host that
is not the owner, or when there is no session, is rejected (`NOT_OWNER`) and answered to the
writer's source address and port. It has no other effect: no takeover, no watchdog feed.

- Alternative: allow harmless writes from anyone. Against: none is needed; every writable
  register is owner state.

**Reason.** Single owner (0011 point 2; 0007 rule 1), visible to the writer.

## 13. Non-default P2 ports (General bytes 5–22, 29–32) and the register destination (Q-S2)

**Choice.**

- Radio-side ports (bytes 5–12, 15–22, 29–30, all of which name G7250 local ports [P2]):
  zero means the default and is honoured. A non-zero value equal to the default is honoured.
  Any other value is **not honoured**: the G7250 keeps the default port, logs it, and sets
  `LINK_STATUS` bit 17. Bytes 13–14 stay ignored (0017).
- Bytes 31–32 (the host's destination port, Annex X2 C10): a non-zero value is honoured; it
  costs no socket. **Zero means the owner's source port** (A2.2), so a host with one socket
  needs no second one (Q-S2).

- Alternative A: honour relocation by reopening sockets [CH394] 7.2.5. For: pure P2.
  Against: the default set shares sockets (1025 for DDC-specific in and status out; 1026 for
  DUC-specific in and microphone out; 1027 for High Priority in and wideband out, [P2]
  General bytes 5–22), so moving one field of a pair needs a ninth socket the CH394Q does
  not have. Restricting moves to pairs is a rule no P2 host knows.
- Alternative B: refuse the whole session on a non-default port. Against: harsh for a request
  that changes nothing else.

**Reason.** Socket budget (0008; 0017; [CH394]). AetherSDR sends zero in bytes 29–32
([AETHER-SRC] `P2Protocol.cpp:79–93`). The guard of 0008 Transport 2 (never onto the
management port) becomes a special case.

## 14. Stream destinations, local source ports, discovery from a second socket (Q-S1, Q-S3, Q-S4)

**Choice.**

- Destination of every radio-to-host stream (DDC0, status, microphone, wideband, register
  pushes) is the owner's source IP address and UDP port, fixed when the session starts.
  [P2] says these go to "the Source Port of the Host that initiated the Discovery Packet" and
  that the General packet is sent from that same port ([P2] General packet "Source Port"),
  so for a P2 host both are the same port. Where they differ, the owner's port wins. As a
  result a run bit without a preceding discovery starts the streams normally; discovery is
  not a precondition of a session ([P2] "Detailed operation" restart path).
- Local source ports, for demultiplexing by sender port (Q-S4): discovery reply 1024; High
  Priority status 1025; microphone 1026; wideband 1027; DDC0 1035; register map 7250;
  management 7251 (Table B2-1).
- A discovery from the owner's IP address on another UDP port (for example a host's picker
  socket) is from another host (0007 Resolved 4): it is answered with 0x03 while a session
  runs and is **not** a `REDISCOVERY` drop event (Q-S1).
- A `CAP_REQUEST`-only packet sent from the future session socket before the first General
  packet is not C&C: it does not start a session and does not make that port the owner; the
  owner is set only by the run bit (A2.3; 0003 §2) (Q-S3).

- Alternative for Q-S1: treat any discovery from the owner's IP as `REDISCOVERY`. Against:
  AetherSDR's 5 s picker sweep ([AETHER-SRC] `AnanDiscovery.cpp:240–263`) would disarm
  every 5 s.
- Alternative for the destination: the most recent discovery's source port. Against: the
  picker socket would steal the DDC stream.

**Reason.** One owner identity (IP and port) for everything; robust against hosts with a
separate discovery socket.

## 15. Firmware release numbering and discovery byte 13

**Choice.** Releases are numbered major.minor, minor 0–9 (after x.9 comes (x+1).0), plus a
16-bit build number; `fw_version` = [31:24] major, [23:16] minor, [15:0] build (0003 §3).
Byte 13 = major × 10 + minor, capped at 255. Byte 23 is non-zero for a beta build ([P2]
byte 23).

- Alternative A: minor 0–99, byte 13 = build mod 256. Against: P2 hosts show byte 13 as a
  version ([P2] "15 = 1.5").
- Alternative B: byte 13 = major only. Against: loses minor releases in P2 hosts.

**Reason.** Byte 13 stays a faithful P2 version up to 25.5.

## 16. Watchdog and keyed-timeout timing tolerance

**Choice.** The G7250 MUST NOT go to standby while the last C&C packet from the owner is
less than 1000 ms old, and MUST be in standby no later than 1100 ms after it. Keyed timeout:
not before `KEYED_TIMEOUT`, and unkeyed no later than `KEYED_TIMEOUT` + 10 ms.

- Alternative: ±10 %. Against: "−10 %" would cut a host that follows [P2] to the letter.

**Reason.** [P2] promises at least one second; the upper bound makes it testable.

## 17. `KEYED_TIMEOUT` at session end; rejected writes

**Choice.** It returns to 500 ms at session end, like the limits (0007 rule 2). A value
outside 100–500 ms is rejected with `BAD_VALUE` (§11); the value in force stays.

**Alternative.** Keep the written value until reset. Against: a new host would inherit it.

**Reason.** Per-session state is reset with the session (A3.6).

## 18. DUC rate and bits value 0

**Choice.** DUC-specific bytes 14–15 = 0 is read as 192 ksps and byte 16 = 0 as 24 bits.

- Alternative: refuse 0. Against: [P2] uses "zero means default" throughout (General ports,
  wideband bytes 26–28, DUC byte 17), and DDC byte 22 = 0 is already read as 24 (B6.5).

**Reason.** Consistent with B6.5 and [P2] convention.

## 19. Sequence counters on rate change and resume; incoming gaps

**Choice.** An outgoing counter restarts only at power-on and on stop ([P2] DDC packet,
"Sequence Number"). A DDC0 rate change, a resume after a refusal, or after DDC-specific
byte 7 bit [0] was cleared, does not restart it. A packet dropped by the G7250 (overrun, §28)
still uses its number, so the host sees a gap. Incoming sequence numbers are never used to
reject or reorder; gaps on port 1029 (DUC I&Q) and 1027 (High Priority) are counted per
session and readable over management (`GET_STATS`, §27).

- Alternative: restart on every change. Against: the host would see a jump to 0 that looks
  like a new session.

**Reason.** [P2] lists only power-on and stop as reset points.

## 20. Refused 10 Mbit/s link: what is sent, and how the speed is read

**Choice.** On a link below 100 Mbit/s no session starts: a run bit gives no owner and no
stream, and no High Priority status is sent. The G7250 answers each High Priority packet with
the run bit set, and each `CAP_REQUEST`, with a register packet holding `LINK_STATUS` and
`STREAM_STATUS`, to the sender, at most once per 100 ms. The speed is read from the
CH394Q PHY configuration register, bit SPDS (0 = 10 Mbit/s, 1 = 100 Mbit/s) and LINKS for
link up [CH394] section 7.1.15; whether the existing design leaves that register usable is
HIS-14.

- Alternative: send High Priority status (low rate) anyway. For: a P2 host sees the radio
  alive. Against: 0004 point 9 says no stream starts; a G7250-aware host learns more from
  `LINK_STATUS`.

**Reason.** Keeps 0004 point 9 literal and still tells the host why.

## 21. Set IP to a unicast address

**Choice.** Accepted with the same rules when sent to the unit's own unicast address or to
the subnet's directed broadcast address, not only to 255.255.255.255 (0008 point 6).

- Alternative: ignore unless sent to 255.255.255.255. For: literal [P2]. Against: no safety
  gain (any LAN host can broadcast); some host tools send it unicast.

**Reason.** The MAC in bytes 5–10 identifies the unit ([P2] Set IP Address packet);
destination address adds nothing. Listed as a clarification, not a deviation.

## 22. Unsupported P2 fields

**Choice.**

- General byte 37 bit [2] VNA: not offered; set → refused, DDC0 does not run while it stands,
  `STREAM_STATUS` reason 11 (0004 point 7 rule).
- General byte 58 bit [0] PA enable: honoured as an extra condition: while 0, a TX request
  does not key; reported in `TX_STATE` bit 4. No exciter-only output is offered. Meaning
  identical to [P2] ("Bit[0] when set enables the PA"), so it is a standard field (0005
  rule 1).
- High Priority byte 1400 (transverter enable, audio mute; ANAN-8000DLE): ignored; no
  transverter output [G7250-MAN] and no audio on the main unit (0017).
- DUC-specific byte 5 bit [0] EER: not offered; set → refused like a DUC rate, DUC I&Q not
  accepted and TX refused, `STREAM_STATUS` reason 12. [P2] changes the meaning of the I&Q
  pairs in EER mode, so following it unsupported would transmit wrong data.
- DUC-specific byte 17 CW ramp: 5–10 ms honoured; 0 and any other value mean the G7250
  default of 8 ms ([P2] byte 17: "0 indicates … a default should be used"). Whether the
  hardware CW path can shape the ramp is HIS-12.

- Alternative for VNA and EER: ignore. Against: the host would believe a mode that is not
  there; 0004 point 7 chose refusal for the same case.
- Alternative for PA enable: ignore. Against: a host that disables the PA expects no RF.

**Reason.** Refuse what would change the meaning of data; honour what makes TX safer.

## 23. TX range region configuration

**Choice.** The region whose transmit ranges apply is a management configuration item
(new C-6, authenticated), stored with the rest of C-1–C-5. Factory default: the
intersection of the transmit ranges of all regions in [G7250-MAN] (TX only where every region
allows). A region change is refused (`SESSION_RUNNING`) while a P2 session runs, so the
record stays constant within a session (0003 §2).

- Alternative A: a default region (for example IARU Region 1). Against: wrong for units
  elsewhere.
- Alternative B: region over P2 registers. Against: a P2 host could loosen the band edges,
  against 0007 rule 1 and 0011 point 3.

**Reason.** Safe by default; changed only by the owner of the radio.

## 24. Management timers

**Choice.** First-secret window 300 s of uptime from the moment the network is up; it is
used up when it runs to its end or a secret is set, and a restart before that opens a fresh
300 s window (0008 S3, "a few minutes"). Trial-boot confirmation within 60 s of start
(0008 U-6). Write-session idle timeout 60 s (0008 S5). Challenge validity 10 s, one use.
Host retransmit timeout 500 ms, at most 5 tries.

- Alternative: 600 s window. Against: doubles the exposure 0008 S3 describes.

**Reason.** Long enough to run a tool after first power-on; short enough to limit S3.

## 25. P2 host while level 2 is active

**Choice.** While level 2 is active a P2 C&C packet does not take the RF chain: no session,
no takeover, no stream; the P2 C&C ports have no socket on level 2 (0008, Socket budget).
Discovery answers 0x03 (0003, Resolved). Switching levels is done only over the management
channel (A1.6 C-2). This agrees with 0021 §16, which decides the same point for part C.

- Alternative: a P2 takeover switches to level 1. Against: an auto-connecting P2 host would
  end a TCI session; 0007 Resolved 5 accepted that risk only within level 1.

**Reason.** One owner per level, level selection in one place (0011 points 2 and 4).

## 26. Capability record version 1.1

**Choice.** Version 1.1 adds the fields 0006 asks for at the end of the record (0003 §4
rule 1): `cap_version` = 0x00010001, `cap_length` = 0xCF (207).

| Offset | Name | Content |
|--------|------|---------|
| 0xB9 | `status_fill` | bit mask of High Priority status fields that are filled: bit 0 byte 4 [0]; bit 1 byte 4 [1]–[2]; bit 2 byte 4 [4]; bit 3 byte 5; bit 4 bytes 6–7; bit 5 bytes 14–15; bit 6 bytes 22–23; bit 7 byte 30; bit 8 bytes 31–36; bit 9 bytes 39–40; bit 10 bytes 49–50 |
| 0xBA | `clock_ref` | bit 0 reference PLL present (0 = "no reference PLL", status byte 4 [4] always 0) (HIS-05) |
| 0xBB | `coupler` | [3:0] position of the forward and reverse coupler: 0 not reported, 1 between PA and ATU, 2 on the antenna side of the ATU (HIS-08, HIS-11) |
| 0xBC | `tlm_rates` | [31:16] snapshot period in ms (1000); [15:8] fast period during TX in ms (10); [7:0] minimum spacing of event pushes in ms (1) |
| 0xBD | `status_rates` | [31:16] High Priority status period in ms when not transmitting (50); [15:0] while transmitting (1) |
| 0xBE | `tlm_count` | number of valid telemetry descriptors (max 8) |
| 0xBF–0xCE | `tlm_desc[0..7]` | 2 registers each: [31:16] telemetry register address, [15:0] sensor update period in ms; [31:16] resolution and [15:0] hysteresis, both in the register's milli-units |

A telemetry register is present when it has a descriptor. Values depend on HIS-11.

- Alternative: a separate telemetry description range. Against: two requests; still well
  under the 239-register limit.

**Reason.** Closes B4.9 with one minor version; v1.0 hosts ignore the new fields (0003 §4).

## 27. Management message format (requirement level)

**Choice.** UDP, big-endian, one message per datagram.

| Bytes | Field |
|-------|-------|
| 0–3 | magic 0x47374D47 ("G7MG") |
| 4, 5 | protocol version major, minor (1, 0) |
| 6 | type: 1 request, 2 reply |
| 7 | flags: bit 0 authenticated (HMAC trailer present), bit 1 more blocks follow |
| 8–11 | request id, chosen by the host, echoed in the reply |
| 12–13 | command |
| 14–15 | status (0 in requests) |
| 16–17 | payload length *N* |
| 18 … 17 + *N* | payload |
| next 32 | HMAC-SHA256 over the challenge and bytes 0 … 17 + *N*, if flag bit 0 |

Requests are at most 1000 bytes (they must fit a 1 KB socket buffer with the 8-byte CH394Q
header, [CH394] section 12.2.4); replies at most 1400 bytes; update blocks carry 512 data
bytes. A repeated request id from the same host gets the stored reply again, not a second
execution.

Commands: 0x0001 `IDENTIFY`; 0x0002 `GET_STATS`; 0x0010 `GET_CHALLENGE`;
0x0011 `SET_FIRST_SECRET`; 0x0012 `CHANGE_SECRET`; 0x0013 `END_WRITE_SESSION`;
0x0020 `GET_CONFIG`; 0x0021 `SET_CONFIG`; 0x0022 `FACTORY_RESET`; 0x0023 `SWITCH_LEVEL`;
0x0024 `RESTART`; 0x0030 `READ_LOG`; 0x0031 `CLEAR_LOG`; 0x0040 `UPDATE_BEGIN`;
0x0041 `UPDATE_BLOCK`; 0x0042 `UPDATE_VERIFY`; 0x0043 `UPDATE_ACTIVATE`;
0x0044 `UPDATE_ABORT`; 0x0045 `UPDATE_STATUS`; 0x0046 `ROLLBACK`.

Status codes: 0 OK; 1 accepted, in progress; 16 unknown command; 17 malformed; 18
unsupported protocol version; 19 too large; 32 authentication required; 33 authentication
failed; 34 rate-limited; 35 busy (another writer); 36 first-secret window closed or secret
already set; 48 invalid configuration; 49 not allowed (would loosen a limit or touch TX);
50 refused while armed or transmitting; 51 wrong hardware; 52 older image without downgrade
flag; 53 bad block CRC; 54 block out of order; 55 verification failed; 56 not supported in
this firmware; 57 refused while a P2 session runs.

Error handling: wrong magic → dropped without reply; correct magic but fewer than 18 bytes or
a length that does not match → reply 17 if the request id is readable, else dropped; unknown
major version → reply 18 with the G7250's version in the header. Payload layouts are fixed
with the reference model (0019) before M5; they do not change the framing.

- Alternative A: TLV-only, no fixed header. Against: harder to filter in captures.
- Alternative B: CoAP (RFC 7252). For: a standard. Against: a stack and options the firmware
  does not need; the HMAC scheme of 0008 still has to be added.

The management port 7251 (§2) differs from the TCI default port 50001 (0021 §2).

**Reason.** Fulfils 0008 Transport 3–4 and the Consequences list at the level rc1 needs.

## 28. Error handling (B11)

**Choice.**

- **Principle.** A packet the G7250 does not act on has no effect at all: no watchdog feed, no
  takeover, no change of state. Errors are counted (`GET_STATS`) and, where a host can be
  told, reported in a status register.
- **Short packets.** Discovery needs ≥ 5 bytes (byte 4); Set IP ≥ 15; General, DUC-specific
  ≥ 60; DDC-specific, High Priority, DUC I&Q ≥ 1444; memory-mapped ≥ 10 (§4). A shorter
  packet is discarded whole. Bytes beyond the [P2] length are ignored.
- **Unknown command on port 1024** (byte 4 not 0x00, 0x02, 0x03, 0x04, 0x05): ignored without
  reply.
- **Closed ports, including 1028.** [CH394] describes only the receipt of ICMP "port
  unreachable" (GINT UNREACH, UNIP, UNPORT, sections 7.1.7, 7.1.13, 7.1.14); it does not say
  whether the CH394Q sends one for a datagram to a port with no open socket. Firmware rule:
  nothing reaches the firmware for such a port and the firmware sends nothing in reply; a
  host MUST NOT depend on either silence or an ICMP message. The conformance test records
  what the chip does.
- **RX overrun.** When a DDC0 packet cannot be handed to the CH394Q in time (socket transmit
  buffer full), the whole packet is dropped, its sequence number is used (§19), and High
  Priority status byte 30 bit [0] is set ([P2]). No partial packet is sent.
- **TX overrun.** A DUC I&Q packet that finds the DUC FIFO full is discarded whole; the
  CH394Q has no UDP flow control [CH394] 12.2.4. Underflow is B10.5.
- **Stale sessions.** The 1 s watchdog ends a session whose host is gone. With the hardware
  timer disabled (allowed only while not armed) the session stays until a takeover, as [P2]
  says; an ICMP port unreachable for the owner's port ([CH394] 7.1.7) is logged and counted,
  and does not end the session. A stale management write session ends after 60 s (§24).
- **RX frequency outside `rx_range`.** Tuned as requested; not refused or clamped; receiver
  performance there is not specified.

- Alternative for short packets: act on the bytes present. Against: a truncated High
  Priority packet would read PTT and drive from missing bytes.

**Reason.** Predictable, testable, and safe: partial data never acts.

## 29. Limit-table design values

**Choice.** SWR: 3 `UNKEY` trips within 10 s → `FAULT` (class 1). Forward power: if still
over the limit 200 ms after `REDUCE` started, `UNKEY`. Supply voltage: recovery after 2 s
continuously inside the range. These are firmware timing choices, to be reviewed when HIS-12
gives the power-control loop speed; thresholds stay HIS values.

- Alternative: N = 5 in 30 s. Against: lets a bad antenna be hit for longer.

**Reason.** Short enough to protect the PA, long enough to ride out a single arc.

## 30. Unit of the DDC sample-rate field

**Choice.** DDC-specific bytes 18–19 carry the rate in ksps (48, 96, 192, 384). Confirmed in
two public hosts: AetherSDR ([AETHER-SRC] `P2Protocol.cpp:123–125`) and piHPSDR
([PIHPSDR] `new_protocol.c:1403–1404`). Closes 0004 "Still open" (DDC rate units).

**Reason.** Two independent hosts agree, and [P2] lists the values as "48/96/192/384/768/1536"
(DDC-specific bytes 18–19) with "Valid rates are 48/96/192/384/768/1536 ksps".

## 31. TCI client allow-list (configuration item from 0021 §10)

**Choice.** New management configuration item C-7 (authenticated write, stored and validated
with C-1 to C-6): a list of 0 to 8 entries, each an IPv4 address with a prefix length 0–32
(/32 = one address). Factory default: empty, which means "any address in the radio's own
subnet" (0021 §10 point 1). The list applies to TCI connections only. When a new list is
applied, open TCI connections from addresses it no longer allows are closed and logged.

- Alternative: apply the list also to P2 and management. Against: P2 hosts cannot be told
  why they are refused, and a wrong list could lock the owner out of the management channel
  that is needed to fix it.

**Reason.** Smallest rule that implements 0021 §10; the management port stays reachable.

---

## Consequences

- `spec/network-interface.md` draft 3 (rc1 candidate) applies §1–§31, cites them as
  "0020 §n", writes B11 in full, and lists the new deviations in Annex X1 (non-default ports
  not honoured; P2 not served while level 2 is active) and clarifications in Annex X2 (stream
  destination; Set IP unicast).
- Annex X3 gets tests for B11 and for the new rules.
- `spec/register-map.yaml` (planned for lint L7) takes the addresses of §3 and layouts of §8.
- The AetherSDR annex can drop Q-S1 to Q-S4 once ON8ST accepts §13 and §14.

## Sources

- [P2] openHPSDR Ethernet Protocol V4.4: "Detailed operation"; Set IP Address packet;
  General packet bytes 5–39, 58 and "Source Port"; DDC-specific packet bytes 7, 18–22; DUC
  specific packet bytes 5, 14–17; High Priority packet bytes 4, 1400; memory-mapped packets
  (Address, Data, "Sequence Number", "Destination Port"); DDC packet "Sequence Number";
  High Priority status byte 30.
- [CH394] WCH CH394 manual 1, V1.2: sections 7.1.7 (GINT UNREACH), 7.1.13 (UNIP), 7.1.14
  (UNPORT), 7.1.15 (PHY_CFG: SPDS, LINKS), 7.2.5 (Sn_PORT), 12.2.4 (UDP mode, 8-byte receive
  header, no flow control).
- [G7250-MAN] Xiegu G7250 Operation Manual rev 0.1: TX power per mode, transmit ranges.
- [AETHER-SRC] AetherSDR source, commit 9f7cbeb: `P2Protocol.cpp:79–93`, `:123–125`;
  `AnanDiscovery.cpp:240–263`. [PIHPSDR] piHPSDR source, commit 422bec5:
  `new_protocol.c:1403–1404`.
- Decisions 0003, 0004, 0005, 0006, 0007, 0008, 0011, 0014, 0015, 0017, 0019;
  `spec/annex-aethersdr.md` (Q-S1 to Q-S4).

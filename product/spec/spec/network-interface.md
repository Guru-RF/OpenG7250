# G7250 network interface specification

- Version: draft 2, 2026-11-19
- Status: draft. Brings the text in line with decisions 0003, 0004, 0006, 0007 and 0008, all
  accepted by ON8ST on 2026-11-19. Focus: milestone M1 (discovery, capability block, RX IQ on
  G7250-P2); sections for M2–M5 are written as far as the decisions allow.
- © 2026 ON8ST, CC BY 4.0 (see `LICENSE.md`).
- Structure: decision 0001, "(2) Network-interface spec", as revised by 0016, split into parts
  A, B and C by 0011.

Sources are cited by key (see `sources.md`) or by decision number (see `decisions/`).
Citations of [P2] give the packet name and byte number of [P2] V4.4. A value that depends on
an open hardware question is written "TBD (HIS-xx)" (see `open-questions-his.md`). A value
that no accepted decision fixes yet is written "TBD" with the decision or section that has to
fix it. Register names in `CODE` style are symbolic; their addresses are in B8.

The key words of B1.2 apply to the whole document, parts A, B and C.

---

## Part A — Common to both levels

Part A holds what applies to every level (0011, Consequences): the management channel, level
selection and ownership, and the safety behaviour that a host can see on the network.

### A1 Management channel

This section fixes the requirements of the management channel. Packet formats, the port
number and the timeouts are TBD (0008, Consequences: "Spec part A gets a section 'Management
channel' with: the port number, the packet framing, …").

A1.1 **Purpose.** The management channel carries identification, configuration, logs and
firmware update, on a connection separate from G7250-P2 and TCI (0001 spec section 10; 0008).

A1.2 **Transport.** The management channel MUST use its own UDP port, served by the eighth
socket of the CH394Q (0008, Decision, Transport 1; 0017). That socket is reserved at both
levels, MUST be open whenever the network is up, and MUST NOT be closed to make room for
another level (0008, Transport 1; Socket budget).

A1.3 **Port number.** TBD (0008, Transport 2). It MUST lie outside 1024–1029 and outside the
DDC range 1035–1114 ([P2] General packet bytes 17–18; 0008, Transport 2). If a General packet
moves a P2 port onto the management port, the G7250 MUST NOT give the management socket away;
it MUST keep the default for that P2 port and log the conflict (0008, Transport 2; B2.3;
Annex X1, D21). The port is announced in the capability record field `mgmt` (B4, 0003).

A1.4 **Framing.** The channel is request/response. Every request MUST carry a request id;
every reply MUST echo it and carry a status code. Large transfers MUST be split into numbered
blocks, each acknowledged; the host retransmits on a timeout (0008, Transport 3). The channel
has its own protocol version, reported in identification, independent of the P2 version and
of the capability-record version (0008, Transport 4). Formats, status codes and timeouts: TBD
(0008, Consequences).

A1.5 **Identification** (read; no authentication) (0008, Functions):

- model "G7250", MAC address (HIS-15), serial number if the hardware has one (HIS-15) (I-1);
- versions of the main-unit firmware (running image and other slot), boot loader, FPGA if
  present, hardware (I-2; which exist: HIS-18);
- integrity result of both images and update state: normal, trial boot, rolled back (I-3);
- whether a secret is set, and whether the first-secret window is open and for how long
  (I-3a);
- active level, owner of the RF chain (host IP address and UDP port, or none) and TX arm
  state; read-only (I-4; 0011 point 2; 0015);
- uptime, last reset cause (HIS-13), and the management, P2 and capability-record protocol
  versions (I-5).

Identification MUST also be answered to a broadcast request (I-6).

A1.6 **Configuration** (write needs authentication, A1.10) (0008, Functions):

- network: static or DHCP; address, netmask, gateway (C-1; [CH394] sections 7.1.2–7.1.5);
- level selection: default level at power-on, and a request to switch level now; level 2 is
  selectable only once it exists, after gate G6 (C-2; 0011 point 4);
- safety settings that MAY only be made stricter than the built-in limits: maximum TX time,
  power limit per band, SWR and temperature limits; built-in limits and the TX band edges per
  region MUST NOT be writable (C-3; 0011 point 3; 0007 sub-decision 4 rule 1);
- configuration MUST be validated as a whole before it is applied, stored in non-volatile
  memory with a version and a check value, and survive a restart; a network change is applied
  after the reply is sent; if the new network configuration cannot be brought up, or an
  address conflict is detected ([CH394] section 7.1.7, GINT IP_CONFLI), the G7250 MUST fall
  back to the previous configuration and log it (C-4);
- a factory reset of network configuration and secrets MUST be possible over this channel
  (authenticated) and MUST also be possible locally without the network; the local path is
  TBD (HIS-17, HIS-19) (C-5).

A1.7 **Logs** (read without authentication; clearing needs authentication) (0008, Functions):
a ring buffer of events with an uptime timestamp in ms, wall-clock time only if the main unit
knows it (HIS-17) (L-1). The log MUST record at least: resets and their cause, safety-core
trips and faults, TX arm and disarm, host takeover, level changes, configuration changes with
the source address (including P2 Set IP, B3.9), every update step, authentication failures and
port conflicts (L-2; 0007, Consequences). It is read in pages by sequence number (L-3). Size
and persistence across reset: TBD (HIS-18).

A1.8 **Firmware update** (authenticated) (0008, Functions, U-1 to U-10):

- An update MUST be refused while TX is armed or the radio is transmitting. Once an update
  starts, the G7250 MUST leave RUN, refuse any new P2 RUN or arm, and stay in the receive-safe
  state of 0015 until it restarts (U-1; 0007 drop event 11, `MAINTENANCE`).
- One package per update, with a header: magic, target hardware id and revision, component
  list, versions, length, SHA-256 [FIPS-180-4] per component, and a signature field that is
  reserved and empty in this version. An image for other hardware MUST be refused before
  anything is written (U-2; 0008 option I1).
- Transfer in numbered blocks with a CRC-32 each, into a staging area that is not the running
  image; resumable; abandonable without effect on the running image (U-3).
- The staged image MUST be hashed and compared with the header before activation. No
  signature is checked in this version (U-4; 0008, Resolved 5).
- Activation MUST be atomic; power loss before the switch leaves the old image running (U-5).
- The first boot of a new image is a trial; without self-confirmation within a time TBD, the
  boot loader MUST return to the previous image and log the rollback (U-6). Feasibility of
  two slots and atomic boot choice: TBD (HIS-18, HIS-19) (U-10).
- The boot loader is not updated through this channel (U-7).
- An image older than the running one MUST be refused unless the request carries an explicit
  "downgrade" flag; a downgrade is logged; configuration the older image does not understand
  is kept but not used, and the reply says so (U-8; 0008, Resolved 3).
- A recovery path that does not depend on this firmware MUST exist; which one is TBD
  (HIS-19, HIS-17) (U-9).
- The G7250 MUST NOT program itself through P2 Erase and Program packets (B3.9).

A1.9 **Management never keys the radio.** No request on this channel MAY set PTT, the TX
arm, drive level or any RF output, and none MAY loosen a safety limit (0008 S1; 0011
point 3; 0015; 0007).

A1.10 **Security on a LAN** (0008, Security):

- Writes (configuration, level switch, log clear, update, rollback) MUST require a per-radio
  secret, proven by challenge and response: a fresh random challenge from the radio, answered
  with HMAC-SHA256 [RFC2104], [FIPS-180-4] over the challenge and the request. The secret
  never crosses the network. Reads need no authentication (S2). Source of randomness: TBD
  (HIS-20).
- **First secret.** In factory state, during a one-time window after the first power-on or
  after a factory reset, the first host that sends a "set first secret" request sets it,
  without confirmation on the controller. Window length: TBD (a few minutes, 0008 S3). The
  window MUST open only while no secret is set, MUST NOT reopen without a factory reset, and
  the claim MUST be logged with its source address (S3; 0008, Resolved 1). Risk, stated by
  0008: anyone on the LAN during the window can claim the radio.
- Requests MUST be answered only from the radio's own subnet and never from a broadcast
  source, except identification; authentication failures MUST be rate-limited and logged
  (S4).
- One writer at a time: a write session is held by one host (address and port) with an idle
  timeout (TBD); others get "busy" for writes and normal answers for reads (S5).
- No confidentiality in this version (S6).
- P2 Set IP on port 1024 is the one unauthenticated write (B3.9; S7).

A1.11 **DHCP.** Provisional (0008, Socket budget, "Proposed … to be fixed in spec part A;
depends on HIS-14"): the DHCP exchange at power-on runs before the P2 sockets are opened;
lease renewals borrow the management socket for the few seconds the exchange takes. TBD
(HIS-14).

### A2 Ownership and level selection

A2.1 **Single owner.** Only one level controls the RF chain at a time, and only that level's
owner MAY transmit (0011 point 2).

A2.2 **Owner identity.** On level 1 the owner is the host of the current session, identified
by its source IP address and UDP port together (0007, Terms; Resolved 4). A host MUST send all
its C&C packets of one session from one UDP source port (0007, Consequences, "keep one UDP
socket and port per session"). A host that reopens its socket on a new port is a different
host; its first C&C packet is a takeover (A2.4; B5.7).

A2.3 **Session.** A session starts when a host sets RUN (High Priority byte 4 bit [0]) from 0
to 1 while the radio is not in a session. It ends when RUN is cleared, the P2 watchdog sends
the radio to standby, another host takes over, or the radio resets (0007, Terms).

A2.4 **Takeover.** Takeover by another host MUST be allowed at any time. On the first C&C
packet from a host that is not the owner, the G7250 MUST unkey, drop the arm (`TAKEOVER`),
issue a new token, send a last `TX_ARM_STATE` to the old owner, and only then process the new
host's packet. The new owner starts unarmed (0007, Decision 3; Resolved 1). Hosts SHOULD warn
the user before taking over a radio that reports 0x03 in discovery byte 4 ([P2] Discovery
reply byte 4 NOTE; 0007, Resolved 5). There is no radio-side protection against an
auto-connecting host on level 1 (0007, Resolved 5).

A2.5 **Active level.** The active level MUST be visible in the capability record field
`level` (B4; 0003) and in management identification (A1.5, I-4) (0011 point 2). While level 2
is active, P2 discovery MUST answer with byte 4 = 0x03, and `level` bits [7:4] = 2 (0003,
Resolved). The default level at power-on and a level switch are set over the management
channel (A1.6, C-2). A change of active level MUST drop the arm (`LEVEL_CHANGE`, 0007 drop
event 10), and an arm is accepted only while level 1 is active (0007 rule 1). Whether P2 C&C
from a host can take the RF chain from an active level 2: TBD (part C; no decision).

A2.6 **Read without ownership.** Any host MAY read the capability record without taking over
or starting a session (B4.4; 0003 §2) and MAY read management identification, logs and status
(A1.5, A1.7).

### A3 Safety behaviour visible on the network

The safety core sits below both levels; a level MAY make limits stricter, never looser (0011
point 3). This section states the level-independent behaviour; B5 and B10 give the P2 side and
B8 the registers.

A3.1 **One TX authority.** The PA MUST key only when the owner of the active level has armed
TX and a TX request arrives (0015; 0007 sub-decisions 1 and 6). On level 1 the arm handshake
is B10.2. The arm is a protection against accidents, not security: P2 has no authentication,
and anyone on the LAN who sees the token can arm ([P2]; 0007 option 1C, "Against").

A3.2 **Events that drop the arm.** Each drop MUST unkey first, then disarm, then issue a new
token and push `TX_ARM_STATE` with the reason (0007 sub-decision 1 rule 5). The complete list
is Table A3-1.

Table A3-1 — Arm drop events (0007 sub-decision 1, rule 5)

| # | Event | Reason code (symbolic) |
|---|-------|------------------------|
| 1 | Owner writes 0 to `TX_ARM` | `HOST_DISARM` |
| 2 | RUN cleared (High Priority byte 4 bit [0] = 0) | `RUN_CLEARED` |
| 3 | P2 watchdog: no C&C from the owner for 1 s (B5.6) | `WATCHDOG` |
| 4 | Takeover, including the owner's IP address on another UDP port (A2.4) | `TAKEOVER` |
| 5 | Any reset: power-on, brown-out, processor watchdog, software reset (HIS-13) | state after reset is disarmed; logged (A1.7) |
| 6 | Entry into the fault state (A3.5) | `FAULT` |
| 7 | Limit trip with action `DISARM` or `FAULT` (A3.4) | `LIMIT_<name>` |
| 8 | Ethernet link down, if the CH394Q reports it (HIS-14) | `LINK_DOWN` |
| 9 | Loss of the socket or port set-up the session uses (for example a General packet moving the High Priority or DUC ports) | `SESSION_CHANGED` |
| 10 | Change of active level (A2.5) | `LEVEL_CHANGE` |
| 11 | Start of a firmware update or of a configuration change of limits over the management channel (A1.8) | `MAINTENANCE` |
| 12 | New Discovery from the owner while armed | `REDISCOVERY` |
| 13 | A TX path that must be blocked is found not blocked (A3.7) | `FAULT` |

Not drop events (they end the transmission but keep the arm): the keyed timeout and TX IQ
underrun (B10.5), maximum continuous TX time and other `UNKEY`-level limit trips; changes of
frequency, antenna, filters or drive while not keyed (0007 rule 5).

A3.3 **Limit actions**, in increasing order (0007, Decision 4):

- `WARN`: flag in `TX_STATE`, no effect on TX;
- `REDUCE`: the radio lowers drive below the host's drive level until the value is back
  inside the limit; TX continues; the host's value is not changed (0007 rule 4);
- `UNKEY`: ends the current transmission; a new 0→1 TX request is needed; arm kept;
- `DISARM`: unkey and drop the arm;
- `FAULT`: unkey, drop the arm, enter the fault state (A3.5).

A3.4 **Limits.** Each limit has a built-in value, an action and a recovery rule (Table A3-2).
Rules (0007, Decision 4, rules 1–5):

1. A limit that a host may change has a `LIMIT_<name>` register (B8). A write MUST be accepted
   only if it is equal to or stricter than the built-in value; a looser write MUST be rejected
   (not clamped) and reported. Built-in values are not writable over P2; over the management
   channel they may only be tightened, never beyond the hardware rating (A1.6; HIS-12).
2. Tightened values return to the built-in values when the session ends. Persistent tightening
   is management configuration (A1.6).
3. The host MUST declare a TX mode class before arming (B10.3).
4. The mapping of P2 drive level 0–255 ([P2] High Priority byte 345) to power is TBD (HIS-12).
5. All limits apply on both levels (0011). ATU tuning uses its own SWR and power profile, TBD
   (HIS-08, HIS-12).

Table A3-2 — TX limits (0007, Decision 4; values TBD unless a public source is given)

| Limit | Measured by | Threshold(s) | Action | Recovery |
|-------|-------------|--------------|--------|----------|
| TX frequency | DUC0 frequency ([P2] High Priority bytes 329–332) | outside the transmit ranges of [G7250-MAN] for the configured region (region configuration: TBD) | TX request ignored (no key) | inside a range again |
| SWR | forward and reflected power (HIS-11) | above S1: `REDUCE`; above S2: `UNKEY`; evaluated only above a minimum forward power; S1, S2, minimum TBD (HIS-11, HIS-12) | as listed | `UNKEY`: next TX request; N trips in T s → `FAULT`; N, T TBD |
| PA temperature | PA sensor (HIS-11) | T1 `WARN`, T2 `REDUCE`, T3 `UNKEY` with inhibit, T4 `FAULT`; all TBD (HIS-11, HIS-12) | as listed | inhibit lifts below T3 minus hysteresis (TBD) |
| Forward power | forward power (HIS-11) vs band and TX mode class | 100 W SSB/CW/NFM, 25 W AM [G7250-MAN]; 50 MHz TBD (90 W in [G7250-PUDX], [G7250-RIGPIX]; HIS-12); margin TBD | `REDUCE`; if still over after TBD ms, `UNKEY` | next TX request |
| Supply voltage | supply sensor (HIS-11) | starting values 13.8 V ±15 % (11.73–15.87 V) [G7250-MAN]; final HIS-11, HIS-12 | under-voltage while keyed: `REDUCE`, below a lower value (TBD) `UNKEY`; over-voltage: `UNKEY` with inhibit | inside range for TBD s |
| Supply / PA current | current sensor, if any (HIS-11) | above 23 A [G7250-MAN]; final HIS-12 | `UNKEY` | next TX request |
| Maximum continuous TX time | firmware timer, any TX source | 5 min built-in (0007, Resolved 3); may be set stricter, never looser; to be checked against the thermal rating (HIS-12) | `UNKEY` (arm kept) | next TX request |
| ATU tune time | firmware timer | initial tuning ≤ 10 s [G7250-MAN] plus margin TBD (HIS-08) | `UNKEY`, tune reported failed | next tune command |
| Sensor plausibility | all of the above | sensor missing, stuck or out of range (HIS-11) | `FAULT` | A3.5 |
| RF while not keyed | forward power (HIS-11) | above TBD with no TX active | `FAULT` | A3.5 |

A3.5 **Fault state** (0007, Decision 5):

- **Classes.** Class 1, host-clearable: limit faults with a measurable condition (temperature
  T4, repeated SWR trips, supply). Class 2, latched until reset: sensor failure, RF while not
  keyed, a TX path not blocked, internal consistency errors.
- **Entry.** Any `FAULT` action of Table A3-2, N repeated trips, drop event 13, a processor
  watchdog reset seen at start-up (HIS-13), or an internal error.
- **Effect.** Unkey, drop the arm (`FAULT`), release SEND and the TUNER trigger, refuse arm
  requests. RX MUST continue, so that the host can still see the radio and the fault.
- **Reporting.** `SAFETY_STATE`, `FAULT_CODE` (first cause), `FAULT_FLAGS` (latched bitmask
  since the last clear), `FAULT_CLASS` and a trip counter, pushed on change (B8) and logged
  (A1.7). The P2 High Priority status packet stays standard (0005; B9.2).
- **Clearing.** Class 1: the owner writes the current fault code to `FAULT_CLEAR`; accepted
  only if the condition is gone. Class 2: only by a reset (power cycle, or a reset over the
  management channel). A clear MUST NOT re-arm. A class 2 fault is not stored across a reset;
  the start-up self-check detects a persistent cause again, and the fault is logged (0007,
  Resolved 9).

A3.6 **State after power-on, any reset, and every session end** (0007, Decision 5): PA and
its bias off, TX path disabled, SEND and TUNER trigger released (HIS-09, HIS-10, HIS-13); not
armed, new token, built-in limits, watchdog counted as enabled; ATU not tuning, ATU in or out
as stored per band, or out until the HIS says otherwise (HIS-08); antenna default TBD
(HIS-06); filters for the default RX frequency, preamplifier off, attenuation TBD (HIS-07).
What the hardware does between reset and the moment the firmware drives these pins is
HIS-13; if the PA can key from floating lines, M4 waits for a mitigation (0007).

A3.7 **Other TX paths.** Local inputs (controller microphone PTT, KEY) MUST be reported and
MUST NOT key the radio by themselves on level 1; the controller has no standalone operation
while level 1 runs (0007, Decision 6; Resolved 6). SEND, the TUNER trigger and internal ATU
tuning are under the arm (B10.9). Controller TX functions (ATU key, SWR scan) are refused
while level 1 runs unless they reach the main unit as reportable requests (HIS-17). If a path
cannot be blocked, M4 is blocked for that path until ON8ST decides (HIS-10, HIS-17; 0007,
Decision 6).

A3.8 **Management** never changes the TX state (A1.9).

---

## Part B — Level 1: G7250-P2

### B1 Scope and conformance language

B1.1 This part specifies the network interface of level 1 of the G7250 main-unit firmware,
called **G7250-P2**: openHPSDR Protocol 2 with a G7250 board type (0016, 0002).

B1.2 The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD
NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY" and "OPTIONAL" in this document are to be
interpreted as described in BCP 14 (RFC 2119, RFC 8174) when, and only when, they appear in all
capitals, as shown here. "The G7250" means the G7250 main unit running firmware that
conforms to this part. "The host" means a P2 host application.

B1.3 **Normative reference.** [P2] openHPSDR Ethernet Protocol V4.4 (see `sources.md`). Where
this document says "[P2]" without a version, V4.4 is meant.

B1.4 **Default rule.** The G7250 MUST behave as [P2] specifies, for every packet, field and
procedure, unless this document states a deviation (0009 as revised by 0016).

B1.5 **Deviations.** Every deviation from [P2] MUST be stated in the section concerned and
listed in Annex X1 (0009, Consequences; 0005, Consequences). A behaviour that is not in
Annex X1 is not a deviation.

B1.6 **Clarifications.** Where [P2] is ambiguous or contradicts itself, this document states
the reading the G7250 follows and lists it in Annex X2. A clarification is not a deviation:
it picks one of the readings [P2] allows.

B1.7 **Extensions.** G7250 functions that no standard P2 field describes with identical
meaning are carried in the G7250 register map on the P2 memory-mapped register packets
(0005; B8). Reserved bytes in the standard P2 packets MUST NOT be given a G7250 meaning (0005,
rule 3). This rule also covers the discovery reply, bytes 14–19 and 24–59 included (0003 §1).

B1.8 **Scope of this draft.** B1–B6 cover M1. B7–B11 are written as far as decisions
0003–0008 allow; open values are TBD. Wideband data is M2 (0004 point 4); transmit (B10) is M4
and only after M3 (design note §6; 0007, header).

### B2 Transport

B2.1 **UDP over IPv4.** All G7250-P2 packets are UDP datagrams; IP and UDP headers are as per
the UDP/IP standards ([P2], "openHPSDR Host to Hardware Protocol" and "openHPSDR Hardware to
Host Protocol"). Diagrams in this document show the UDP payload only, starting at byte 0
([P2], same sections).

B2.2 **Link.** The Ethernet interface is 10/100 Mbit/s; Gigabit is not available. Source:
WCH CH394Q, 10/100 MAC and PHY [CH394] (ON8ST hardware inspection, 2026-11-19; to be
confirmed, HIS-14). A host MUST NOT assume Gigabit throughput. The throughput towards the
host is further limited by the SPI link between processor and CH394Q, at most 62 MHz [CH394]
(`analysis/ch394-network-budget.md` §2; 0004, "Throughput arithmetic"; HIS-14). On a link
below 100 Mbit/s the G7250 refuses the session (B5.8; 0004 point 9).

B2.3 **Local ports.** The G7250 MUST open exactly the local UDP ports in Table B2-1, and no
other port for level 1. Sources: [P2] General packet bytes 5–32 (defaults); socket
analysis (`analysis/ch394-network-budget.md`, addendum); 0005; 0008; 0017.

Table B2-1 — Local UDP ports of the G7250 (level 1)

| # | Local port | In (host → G7250) | Out (G7250 → host) | Status in G7250-P2 | Source |
|---|-----------|-------------------|--------------------|--------------------|--------|
| 1 | 1024 | Discovery, General packet, Set IP (Erase/Program ignored, B3.9) | Discovery reply | MUST be open | [P2] "Detailed operation"; General packet; Discovery reply; 0008 points 5–6 |
| 2 | 1025 | DDC-specific packet | High Priority status (B9.2) | MUST be open | [P2] General bytes 5–6, 11–12 |
| 3 | 1026 | DUC-specific packet | Microphone data, only if HIS-17 shows a path (B6.11) | MUST be open | [P2] General bytes 7–8, 19–20; 0004 point 3 |
| 4 | 1027 | High Priority packet | Wideband ADC0 data, from M2 (B6.10) | MUST be open | [P2] General bytes 9–10, 21–22; 0004 point 4 |
| – | 1028 | DDC audio | – | MUST NOT be opened | 0017 |
| 5 | 1029 | DUC0 I&Q | – | MUST be open (used from M4) | [P2] General bytes 15–16; 0012 |
| 6 | 1035 | – | DDC0 I&Q | MUST be open | [P2] General bytes 17–18 |
| 7 | TBD (B8.1) | G7250 register map (memory-mapped registers from PC) | G7250 register map (memory-mapped registers from hardware) | MUST be open | [P2] General bytes 29–32; 0005 |
| 8 | TBD (A1.3) | Management channel | Management channel | MUST be open, at both levels | 0008, Transport 1 |

- Ports 1036 and up (DDC1 and further, [P2] General bytes 17–18) are not opened while the
  G7250 implements one DDC (0004 point 1). Number of DDCs: TBD (HIS-02).
- **Memory-mapped register port.** [P2] gives the default of General bytes 29–30 and 31–32 as
  "xxxx", so it is undefined; this document defines it (0005; 0003, "left to spec part B").
  The port number is TBD (B8.1). The G7250 MUST use one and the same local port for both
  directions (0005, Consequences; 0017). Using a defined default is a deviation (Annex X1, D2).
- **Port 1028.** The G7250 opens no socket on port 1028 (0017). A host SHOULD NOT send DDC
  audio packets. The G7250 accepts General packet bytes 13–14 and ignores them (0017). How
  the CH394Q reacts to a datagram for a closed port (silent drop or ICMP port unreachable) is
  TBD (0017, Consequences; [CH394] does not say). This is a deviation (Annex X1, D1).
- **Non-default ports.** [P2] lets the host set every port in General bytes 5–22 and 29–32,
  zero meaning the default. Whether the G7250 honours non-default values is TBD (no decision).
  In any case: the G7250 MUST NOT use more sockets than Table B2-1
  (`analysis/ch394-network-budget.md`); it MUST NOT move a P2 port onto the management port
  (A1.3; 0008, Transport 2); and a General packet that moves a port the armed session uses
  drops the arm (`SESSION_CHANGED`, Table A3-1 event 9). Until this is decided, a host SHOULD
  send zero in these bytes.
- **Socket budget.** Table B2-1 uses all 8 CH394Q sockets: 7 for G7250-P2, one for the
  management channel (0008, Socket budget; 0017; [CH394]). The division of the 16 + 16 KB
  socket buffers is TBD (indicative split in 0004, Consequences, "CH394Q buffer split";
  HIS-14).

B2.4 **Remote endpoint.** The G7250 MUST reply to the discovery from local port 1024 to the
IP address and source port of the host's discovery packet ([P2] "Detailed operation";
Discovery reply, "Source Port", "Destination Port"). The G7250 MUST send DDC I&Q data to the
source port of the host that initiated the discovery ([P2] DDC packet, "Destination Port").

B2.5 **Byte order and integer interpretation.** Multi-byte fields MUST be sent and read MSB
first (network byte order, big-endian), and all values are unsigned integers unless stated
otherwise ([P2] "openHPSDR Host to Hardware Protocol"; General packet byte 39: zero selects
Big-Endian). The same applies from the G7250 to the host; [P2] "openHPSDR Hardware to Host
Protocol" writes "MSB first (little Endian)", which the G7250 reads as MSB first (Annex X2,
C1). The G7250 offers no other endian mode (B3.7; 0004 point 1).

B2.6 **Packet length.** No G7250-P2 UDP payload exceeds 1444 bytes (byte 0 to byte 1443),
the largest payload in [P2] (High Priority packet, DDC-specific packet, memory-mapped
register packets, DDC I&Q packet, DUC I&Q packet, all ending at byte 1443).

B2.7 **Sequence numbers.** Every packet starts with a 4-byte sequence number, bytes 0–3,
MSB first ([P2] "Detailed operation"). For each local port and direction the G7250 sends on,
it MUST keep its own counter that starts at 0x00000000, increments by one per packet and
rolls over after 0xFFFFFFFF ([P2] DDC packet, Memory mapped registers from hardware,
"Sequence Number"). The counter MUST be reset to zero at power-on and whenever a stop is
received (B5.4) ([P2] DDC packet, "Sequence Number"). The discovery reply always carries
sequence number 0 ([P2] Discovery reply bytes 0–3). On the receive side the G7250 SHOULD NOT
reject a packet because of its sequence number (provisional, B11; [P2] General, DDC-specific
and High Priority packets give the host's sequence number as 0x00000000, Annex X2, C2).
Detection and reporting of gaps: TBD (B11).

### B3 Discovery

B3.1 **Listening.** The G7250 MUST listen on UDP port 1024 for discovery packets at all
times while level 1 is reachable, including while running ([P2] "Detailed operation";
Discovery reply byte 4, value 0x03), and while level 2 is active, answering with byte 4 = 0x03
(0003, Resolved; A2.5). Discovery is also answered on a link below 100 Mbit/s (0004 point 9).

B3.2 **Discovery request.** A discovery request is a UDP payload to port 1024 with byte 4 =
0x02 ([P2] Discovery packet). Bytes 0–3 are the sequence number, set to 0x00000000 by the
host; bytes 5–59 are zero ([P2] Discovery packet). The G7250:

- MUST answer a request sent to its own unicast address, to the limited broadcast
  255.255.255.255, and to the directed broadcast address of its subnet ([P2] Discovery packet,
  "Destination Address");
- MUST answer regardless of the endian mode selected by an earlier General packet ([P2]
  Discovery packet, NOTE; Discovery reply byte 22, NOTE);
- SHOULD NOT require bytes 0–3 or 5–59 to be zero to answer (provisional, B11);
- MUST answer every request with exactly one reply.

A discovery from the owner while TX is armed drops the arm (`REDISCOVERY`, Table A3-1 event
12). A discovery from any other host has no effect on the session.

B3.3 **Discovery reply.** The G7250 MUST reply with the [P2] short reply (format 1), a 60-byte
payload (bytes 0–59), from local port 1024 to the host's IP address and source port ([P2]
Discovery reply, "Source Port", "Destination Port"; 0003 §1). The reply always uses the
format below, irrespective of the selected endian mode ([P2] Discovery reply byte 22, NOTE).
The G7250 MUST NOT report board type 254 or 255, MUST NOT use byte 4 = 0xFE or 0xFF, and MUST
NOT send the Appendix C reply (0003 §1).

Table B3-1 — G7250 discovery reply ([P2] Discovery reply, format 1; 0003 §1)

| Byte | [P2] field | G7250 value | Source |
|------|-----------|-------------|--------|
| 0–3 | Seq # | 0x00000000 | [P2] Discovery reply bytes 0–3 |
| 4 | Response to discovery | 0x02 or 0x03, see B3.4 | [P2] byte 4; 0003 §1 |
| 5–10 | Board MAC, MSB first | the G7250's MAC address; TBD (HIS-15) | [P2] bytes 5–10 |
| 11 | Board type | 200 (0xC8) | 0002; 0003 §1; [P2] byte 11 |
| 12 | openHPSDR protocol version supported | 44 (V4.4), see B3.5 | [P2] byte 12; B1.3 |
| 13 | Firmware code version | see B3.5 | [P2] byte 13; 0003 §1 |
| 14–19 | Mercury 0–3, Penny, Metis code versions | 0x00 | [P2] bytes 14–19 (Atlas only); 0003 §1 |
| 20 | Number of DDCs implemented | equal to record field `num_ddc`; TBD (HIS-02), assumed 1 | [P2] byte 20; 0003 §1; 0004 point 8 |
| 21 | Frequency or phase word | 0 = frequency, 1 = phase; TBD (HIS-04) | [P2] byte 21 |
| 22 | Available endian modes | 0x00 (Big-Endian, 3-byte I&Q only), see B3.7 | [P2] byte 22; 0004 point 1 |
| 23 | Beta version | 0x00 for a release; non-zero for a beta build | [P2] byte 23; 0003 §1 |
| 24–59 | Reserved (AD0ES) / unassigned | 0x00, no G7250 meaning | [P2] byte 24; 0003 §1 |

B3.4 **Status byte (byte 4).**

- The G7250 MUST send 0x02 when it is not running, or when it is running and the discovery
  comes from the owner ([P2] Discovery reply byte 4; A2.2).
- The G7250 MUST send 0x03 when it is running and the discovery comes from any host that is
  not the owner, including the owner's IP address with another UDP source port ([P2] Discovery
  reply byte 4; 0007, Resolved 4; Annex X2, C7). "Running" means the run bit is set (B5.3).
- The G7250 MUST send 0x03 while level 2 is active (0003, Resolved; Annex X2, C8).
- The G7250 MUST NOT send 0xFE or 0xFF (0003 §1; Annex X2, C3).

B3.5 **Version encoding.** [P2] bytes 12 and 13 are single bytes that the host reads as a
decimal number with one implied decimal place: 104 is version 10.4 ([P2] Discovery reply
"Byte 12", "Byte 13").

- Byte 12 MUST be 44, since the normative reference is V4.4 (B1.3); it MUST equal record
  field `p2_version` (0003 §3).
- Byte 13 MUST carry the G7250 firmware version in P2 form, major × 10 + minor ("15 = 1.5"),
  taken from record field `fw_version` (0003 §1 and §3). The full version, with build number,
  is in `fw_version` (B4). The numbering scheme of G7250 releases, and byte 13 for a minor
  version above 9 or a result above 255, are TBD (no decision; 0008 does not fix it).

B3.6 **MAC address.** Bytes 5–10 MUST hold the MAC address the G7250 uses on the link, MSB
first ([P2] Discovery reply, "MAC"). The MAC address MUST be unique per unit, because the
host uses it to tell radios apart and to address Set IP packets ([P2] Set IP Address packet).
The record carries no serial number; the MAC suffices (0003, Resolved). Where it is stored
and whether it is unique per unit: TBD (HIS-15).

B3.7 **Endian modes and DDC data format (byte 22).** The G7250 offers only Big-Endian with
3-byte I&Q: no little-endian, float or double format (0004 point 1, option 2A). Byte 22 MUST
therefore be 0x00, which [P2] defines as "Big-Endian and I&Q data is in 3 Byte format" ([P2]
Discovery reply byte 22). A General packet byte 39 that asks for another format is refused
(B6.3; B11).

B3.8 **Frequency or phase word (byte 21).** The value MUST match what the G7250 accepts in the
High Priority frequency fields ([P2] High Priority packet bytes 9–12, 329–332) and in General
packet byte 37 bit [3]. If the G7250 reports phase (1), the host computes
`phase_word = 2^32 × f(Hz) / DSP clock (Hz)` ([P2] General packet byte 37); the DSP clock is
given in record field `dsp_clock_hz` (0003 §3; Annex X2, C4). Value and DSP clock: TBD
(HIS-04).

B3.9 **Other port-1024 commands.**

- **Erase (0x04) and Program (0x05)** ([P2] Erase and Program packets) MUST be ignored
  without a reply; a P2 host then hits its own timeout (0008, Decision point 5). They MUST NOT
  change the firmware or any stored state. The G7250 does not claim the V3.8 firmware checksum
  feature ([P2] revision history V3.8; Command Reply bytes 13–14; 0008 point 5). Firmware is
  updated only through the management channel (A1.8). Deviation: Annex X1, D12.
- **Set IP Address (0x03)** ([P2] Set IP Address packet) MUST be accepted exactly as [P2]
  specifies (0008 point 6; Resolved 2): a packet to 255.255.255.255:1024 whose bytes 5–10 hold
  the G7250's MAC address sets the IP address in bytes 11–14; 0.0.0.0 selects DHCP; the G7250
  stores it and responds with a Discovery reply ([P2] Set IP Address packet; Command reply
  packet, "Set IP"). The G7250 MUST NOT add preconditions: no refusal while armed or while a
  P2 session runs, and no option to disable it (0008 point 6). The change MUST be logged with
  its source address (A1.7; 0008 L-2), which is not visible on the wire. The stored value is
  the network configuration of A1.6 (C-1), applied after the reply, with the fallback on an
  address conflict (0008 point 6; C-4). Applying a new address ends the network set-up of a
  running session; while armed this is drop event 9 (`SESSION_CHANGED`, Table A3-1). A Set IP
  packet whose bytes 5–10 hold another MAC address is not for this unit and MUST be ignored
  ([P2] Set IP Address packet, "MAC Address"). Whether a Set IP sent to the unicast address is
  accepted: TBD (B11). Risk stated in 0008 S7: any host on the LAN that knows the MAC can
  change the address and so cut a running session; it cannot key the radio.

### B4 Capability block

B4.1 **Form.** The capability block is a **capability record**: a read-only range of the
G7250 register map (B8), sent by the G7250 in standard [P2] "Memory mapped registers from
hardware" packets (0003, Decision option A). It is not in the discovery reply (0003 §1).

B4.2 **Place.** The record occupies `CAP_BASE` to `CAP_BASE + CAP_LENGTH − 1`, at most 239
registers, so that one memory-mapped packet (240 pairs [P2]) carries the request echo plus the
whole record and a host always sees one consistent copy (0003 §2). Proposed: `CAP_BASE` =
0x0000 (0003 §2), so the version 1.0 record occupies 0x0000–0x00B8. Final address: TBD (B8.1).

B4.3 **Encoding.** One field per 32-bit register, big-endian ([P2] memory-mapped packets, Data
[31:0]; 0003 §2). Text is ASCII, 4 characters per register, first character in bits [31:24],
padded with 0x00. Frequencies in Hz. Power in units of 0.1 W. Bit numbers: 0 = LSB (0003 §2,
§3).

B4.4 **When the record is sent** (0003 §2):

1. **On request.** The host writes the register `CAP_REQUEST` (address TBD, B8). The G7250
   MUST answer with one memory-mapped packet that holds the echo of the `CAP_REQUEST` pair and
   the whole record. The data value to write: TBD.
2. **Unasked, once,** when a host starts a session, which 0003 places at the host's first
   General packet.
3. **Destination.** To the source IP address and UDP port of the request when the requesting
   host is not the owner (has no session); otherwise to the owner's memory-mapped port set in
   General packet bytes 31–32, or to the default port (B8.1) if those bytes are zero ([P2]
   General packet bytes 31–32; 0003 §2).

B4.5 **Request-only packet is not C&C.** A memory-mapped packet that contains only a write to
`CAP_REQUEST` MUST NOT take over a session, MUST NOT start one, and MUST NOT feed the watchdog
(0003 §2; Resolved). More generally, no memory-mapped packet is C&C on the G7250 (B5.6; 0007
sub-decision 2.1). Listed in Annex X1, D11.

B4.6 **Read-only.** Writes to any address in the record range MUST be ignored, and the G7250
MUST answer with the current values of the addresses written, so that the host sees that the
write had no effect (0003 §2).

B4.7 **Stability.** Record values MUST be constant for the duration of a session. They MAY
change only between sessions: after a firmware update, a region change of the TX bands, a
change of the active level, a new per-unit calibration, or a change of link speed (0003 §2).
Dynamic state is not in the record: TX armed, fault state and limits in force, telemetry
values, current link speed and session refusal reason are separate status registers (B8;
0003 §2).

B4.8 **Fields, record version 1.0.** Offsets are relative to `CAP_BASE`. "HIS-nn" means the
value is not known yet; the value shown is the current assumption (0003 §3).

Table B4-1 — Capability record, version 1.0 (0003 §3)

| Offset | Name | Content | Value / source |
|--------|------|---------|----------------|
| 0x00 | `cap_magic` | ASCII "G725" = 0x47373235; never changes | 0003 §3, §4 rule 5 |
| 0x01 | `cap_version` | [31:16] major, [15:0] minor of the record format | 0x00010000 (1.0) |
| 0x02 | `cap_length` | number of registers in the record, header included | 0xB9 (185) for version 1.0 (0003 §3, notes) |
| 0x03 | `regmap_version` | [31:16] major, [15:0] minor of the G7250 register map | TBD (B8) |
| 0x04–0x07 | `product_name` | "G7250-P2", padded with 0x00: 0x47373235, 0x302D5032, 0, 0 | 0002, 0016 |
| 0x08 | `fw_version` | [31:24] major, [23:16] minor, [15:0] build | as built; B3.5 |
| 0x09 | `p2_version` | as discovery byte 12 | 44 ([P2]; B3.5) |
| 0x0A | `hw_revision` | main-unit hardware revision, 0 = not identified | HIS-18 |
| 0x0B | `level` | bit 0 level 1 present (always 1); bit 1 level 2 present in this firmware; bit 2 level 2 active; bits [7:4] active level (0 none, 1, 2) | 0011; 0003, Resolved; level 2 only after G6 |
| 0x0C | `streams` | bit 0 RX IQ; bit 1 TX IQ (DUC); bit 2 DDC audio (always 0); bit 3 microphone data; bit 4 wideband data; bit 5 IQ time stamping | bit 0 = 1; bit 1 per `tx` bit 1; bit 2 = 0 (0017); bit 3 per HIS-17 (assumed 0); bit 4 = 0 before M2, 1 from M2 (0004 point 4; HIS-01, HIS-18); bit 5 = 0 (0004 point 1) |
| 0x0D | `num_adc` | number of RF ADCs | HIS-01, HIS-03 (assumed 1) |
| 0x0E | `num_ddc` | number of DDCs; equals discovery byte 20 | HIS-02 (assumed 1) |
| 0x0F | `num_duc` | number of DUCs | assumed 1 [G7250-MAN]; HIS-18 |
| 0x10 | `ddc_rates` | bit mask: bit 0 48, bit 1 96, bit 2 192, bit 3 384, bit 4 768, bit 5 1536 ksps | 0x0F if 384 ksps is offered, else 0x07 (B6.7; 0004 point 6); bits 4, 5 always 0 (0004 point 7) |
| 0x11 | `duc_format` | [31:16] TX IQ rate in ksps, [7:0] bits per sample | 0x00C00018 (192 ksps, 24 bits; 0004 point 2); HIS-18 |
| 0x12 | `dsp_clock_hz` | DSP clock in Hz, as [P2] Appendix C bytes 27–30 | HIS-04 |
| 0x13 | `rx_range_count` | number of valid receive ranges (max 4) | 2 [G7250-MAN] |
| 0x14–0x1B | `rx_range[0..3]` | pairs of start Hz, stop Hz | 500,000–30,000,000; 50,000,000–54,000,000 [G7250-MAN]; unused pairs 0 |
| 0x1C | `antennas` | [7:0] number of antenna connectors; bit 8 host can select; bit 9 separate RX-only input | 2 [G7250-MAN]; bit 8 HIS-06; bit 9 HIS-06, HIS-07 (assumed 0) |
| 0x1D | `atu` | bit 0 internal ATU present; bit 1 host can control it; bit 2 per-band memory; bit 3 external tuner interface present; bit 4 host can control the external tuner interface | bits 0, 2, 3 = 1 [G7250-MAN]; bit 1 HIS-08; bit 4 HIS-09 |
| 0x1E | `atu_range` | [31:16] minimum, [15:0] maximum load in Ω | 20, 150 [G7250-MAN] |
| 0x1F | `telemetry` | bit 0 forward power; bit 1 reverse power; bit 2 PA temperature; bit 3 supply voltage; bit 4 supply current; bit 5 PA current; bit 6 ADC overload | HIS-11; meaning in B9 (0006) |
| 0x20 | `tx` | bit 0 TX hardware present; bit 1 TX implemented in this firmware (0 before M4); bit 2 TX arm required (always 1); bit 3 declared TX mode class required for arm (always 1) | bit 0 = 1 [G7250-MAN]; bit 1 per milestone; bit 2 = 1 (0015); bit 3 = 1 (0007) |
| 0x21 | `tx_band_count` | number of valid entries below (max 16) | 10 [G7250-MAN] |
| 0x22–0x51 | `tx_band[0..15]` | 3 registers per band: start Hz; stop Hz; [31:16] maximum power SSB/CW/FM, [15:0] maximum power AM, both in 0.1 W | ranges per region [G7250-MAN]; 1000 (100 W) and 250 (25 W) [G7250-MAN]; 50 MHz TBD (HIS-12; 90 W in [G7250-PUDX], [G7250-RIGPIX]) |
| 0x52 | `mgmt` | bit 0 management channel present; [31:16] its port | bit 0 = 1 (0008); port TBD (A1.3) |
| 0x53 | `regmap_groups` | bit mask of register groups present in the G7250 map | bit assignment TBD (B8.3; 0003 §3) |
| 0x54 | `link` | [15:0] minimum link speed in Mbit/s for a session | 100 (0004 point 9; [CH394]) |
| 0x55 | `wb_format` | wideband: [31:16] samples per packet, [15:8] bits per sample, [7:0] update rate in ms; 0 when `streams` bit 4 = 0 | from M2: 0x02001032 (512, 16, 50 ms; 0004 point 4) |
| 0x56 | `wb_frame` | wideband: [7:0] packets per frame; 0 when `streams` bit 4 = 0 | from M2: 8 (0004 point 4) |
| 0x57 | `cal_info` | bit 0 power constants per band (set *i* applies to `tx_band[i]`; else set 0 applies to all bands); bits 1–4 forward power, reverse power, exciter power, supply volts filled; [15:8] number of power constant sets (1, or `tx_band_count`); [31:16] ADC full-scale divisor *N* | 0006; per unit and per band HIS-11; *N* = 4095 in [P2] Appendix A |
| 0x58 | `cal_supply_c` | supply constant *c* in units of 10⁻⁶, for `V = x / N × c` | this unit's calibration (0006; HIS-11) |
| 0x59–0xB8 | `cal_power[0..15]` | 6 registers per set, units of 10⁻⁶: forward *c1*, *c2*; reverse *c1*, *c2*; exciter *c1*, *c2*, for `W = (x / N × c1)² / c2` | this unit's calibration (0006; HIS-11); unused sets 0 |

Notes (0003 §3):

- Transmit-power values are the nominal maxima in the configured region, not the limits in
  force; limits in force are status (B8; A3.4).
- Fields with an Appendix C counterpart (`num_adc` byte 36, `num_ddc` byte 39, `dsp_clock_hz`
  bytes 27–30, DDC audio byte 59, microphone byte 72, DUC rate and format bytes 79–80) have the
  same meaning as there ([P2] Appendix C).
- `streams` bit 2 and `num_ddc` MUST agree with what the radio does: no socket on port 1028
  (0017), and only as many DDC I&Q ports as `num_ddc`.
- The record carries no serial number (0003, Resolved).

B4.9 **Fields still to be added.** 0006 ("What the host learns from the capability block")
asks the record to also state: for each standard status field whether it is filled; the
coupler position relative to the ATU (HIS-08, HIS-11); for each telemetry register presence,
resolution, sensor update rate and hysteresis; the telemetry rates in use; and "no reference
PLL" (B9.2, byte 4 bit [4]). Version 1.0 (0003 §3) covers only part of this (`telemetry`,
`cal_info`). The extra fields are TBD and will be added at the end of the record in a minor
version (0003 §4 rule 1).

B4.10 **Versioning rules** (0003 §4):

1. A `cap_version` minor change only adds fields at the end of the record and increases
   `cap_length`. A host MUST read `cap_length` and MUST ignore registers beyond the fields it
   knows.
2. A field the host knows that lies beyond `cap_length` counts as absent: "no" for flags,
   "not reported" for numbers.
3. Unused bits in a bit mask MUST be 0; they MAY get a meaning in a later minor version, always
   so that 0 means the old behaviour. Hosts MUST ignore bits they do not know.
4. A field MUST NOT be moved, removed or given another meaning within one major version. A
   host that does not know the major version MUST NOT rely on the record; it MAY still receive
   with the standard P2 set-up (0015) and SHOULD tell the user that the firmware is newer than
   the host.
5. `cap_magic` never changes; a different magic means "not a G7250 capability record".
6. `regmap_version` follows the same rules, independently. A host decides which register
   groups to use from `regmap_groups`, not by comparing version numbers.
7. The record MUST NOT exceed 239 registers. If more is needed, a second range with its own
   request register is added and announced by a bit in `regmap_groups`.

B4.11 **Host that does not know board type 200.** It sees a standard short reply with an
unknown board type, can set up receive from bytes 20–22 and the standard DDC packets, never
reads the record, never writes the register map, and so can never arm or transmit (0003 §5;
0015). Rates outside `ddc_rates` are refused (B6.7).

### B5 Session, ownership and watchdog

B5.1 **Order of a session start.** The host establishes a session as follows ([P2]
"Detailed operation"; General packet introduction; DDC specific packet introduction; High
Priority data packet introduction):

1. discovery request and reply on port 1024 (B3);
2. a G7250-aware host reads the capability record (B4.4; 0003, Consequences);
3. General packet to port 1024; the first General packet after a discovery reply MUST be
   Big-Endian, and its byte 39 selects the data format for all later packets ([P2] General
   packet byte 39); the G7250 then sends the capability record once, unasked (B4.4);
4. DDC-specific packet to port 1025 (B6.5), and DUC-specific packet to port 1026 (B10.6);
5. High Priority packet to port 1027 with byte 4 bit [0] (run) set. This starts the session
   (A2.3; 0007, Terms).

B5.2 The G7250 MUST NOT send DDC I&Q data before it has received a High Priority packet with
the run bit set ([P2] "Detailed operation": run "in order to start data from the Hardware").
If the run bit arrives before any General or DDC-specific packet, the G7250 MUST use the [P2]
defaults and the G7250 safe RX state (0015, Consequences; A3.6; RX default state TBD, HIS-06,
HIS-07). Behaviour for a run bit from a host that sent no discovery (no known destination port
for DDC data, B2.4): TBD (B11).

B5.3 **Run.** High Priority byte 4 bit [0] set enables the G7250, clear disables it ([P2] High
Priority packet, "Byte 4"). While run is set, DDC0 is enabled (B6.5) and no refusal applies
(B6.7, B5.8), the G7250 MUST send DDC0 I&Q (B6).

B5.4 **Stop.** A High Priority packet from the owner with byte 4 bit [0] clear stops the
session: the G7250 MUST stop all outgoing streams and reset its outgoing sequence counters
(B2.7) ([P2] High Priority packet byte 4; DDC packet, "Sequence Number"), and MUST unkey and
drop the arm (`RUN_CLEARED`, Table A3-1 event 2; 0007). The G7250 MUST keep answering
discovery on port 1024 (B3.1). Restart: by a new High Priority packet with run set, or by a
new discovery and full set-up ([P2] "Detailed operation").

B5.5 **Owner.** The owner is the host of the current session, identified by source IP address
and UDP port (A2.2; 0007, Resolved 4). The host MUST send all C&C packets of a session from
one source port (A2.2).

B5.6 **Watchdog** (0007, sub-decision 2):

- **C&C packets.** C&C packets are the four [P2] "Control Elements" packets: General,
  DDC-specific, DUC-specific and High Priority (0007 sub-decision 2.1; Annex X2, C6).
  Memory-mapped register packets are not C&C: they MUST NOT feed the watchdog (0007 sub-decision
  2.1 and Resolved 8; 0003, Resolved) and MUST NOT cause a takeover (B5.7). Packets from hosts
  other than the owner MUST NOT feed the watchdog (0007 sub-decision 2.1).
- **Timeout.** In RUN, if no C&C packet from the owner arrives for 1 s, the G7250 MUST go to
  standby: unkey, drop the arm (`WATCHDOG`), release SEND and the TUNER trigger, and stop the
  RX streams, as in [P2] standby ([P2] "Detailed operation"; 0007 sub-decision 2.1). The host
  SHOULD send a C&C packet every 100 ms ([P2] "Detailed operation"). Timing tolerance: TBD.
- **Hardware-timer bit** (General packet byte 38 bit [0]) (0007 Decision 2.3, option 2F):
  - the G7250 MUST store the value last written; the effective timer is
    `written OR armed`;
  - while not armed, the bit MUST be honoured as [P2] specifies ([P2] General packet byte 38);
  - while armed, a clear MUST NOT disable the timer; the clear takes effect again after
    disarm (0015; Annex X1, D4);
  - an arm request while the written bit is clear MUST be rejected (`WATCHDOG_DISABLED`,
    B10.2);
  - before any General packet the timer counts as enabled;
  - `WATCHDOG_STATE` reports the value written and the effective state (B8).
- **Keyed timeout** while transmitting: B10.5.

Note: a session with the timer disabled (allowed only while not armed) holds the radio "in
use" after its host has gone and keeps sending RX IQ to it; the next host takes over (0007,
option 2F "Against").

B5.7 **Takeover.** Takeover is always allowed (A2.4; 0007, Decision 3). On the first C&C
packet from a host that is not the owner, the G7250 MUST unkey, drop the arm (`TAKEOVER`),
issue a new token, send a last `TX_ARM_STATE` to the old owner, and only then process the new
host's packet; the new host becomes owner and starts unarmed. A host that reopens its socket
on a new UDP port takes over from itself (0007, Resolved 4). Only the arm part deviates from
[P2] ([P2] Discovery reply byte 4 NOTE; Annex X1, D5, D6).

B5.8 **Link below 100 Mbit/s.** On a link slower than 100 Mbit/s the G7250 MUST refuse the
session: it answers discovery but starts no stream (no DDC0, DUC0, microphone or wideband data),
and reports the reason ("link speed below 100 Mbit/s") in a status register (`LINK_STATUS`,
B8) (0004 point 9; Resolved). The record field `link` gives the minimum speed (B4.8; 0003 §3).
How the firmware reads the negotiated speed from the CH394Q and the exact reason code: TBD
(HIS-14; 0004, Consequences). Whether the High Priority status packet is sent on such a link:
TBD. Annex X1, D15.

B5.9 **Transmit bit.** High Priority byte 4 bit [1] has no effect unless TX is armed (0015;
B10). Bits [2]–[7] never key the G7250 (0007 sub-decision 1 rule 4; Annex X2, C5).

### B6 Streams from the radio: RX IQ, wideband, microphone

B6.1 **Port and endpoint.** DDC0 I&Q MUST be sent from local port 1035 ([P2] General packet
bytes 17–18; DDC packet, "Source Port") to the host's discovery source port (B2.4). One DDC is
implemented, and DDC0 takes its data from ADC0 only (0004 point 1; HIS-02, HIS-01, HIS-03).

B6.2 **Packet format.** Each DDC0 packet MUST have the layout of Table B6-1 ([P2] DDC packet,
"DDC I&Q Data (DDC0 default port 1035)"; 0004 point 1), 1444 bytes in total.

Table B6-1 — DDC0 I&Q packet ([P2] DDC packet; 0004 point 1)

| Byte | Field | G7250 value | Source |
|------|-------|-------------|--------|
| 0–3 | Seq # [31:0] | per-port counter, B2.7 | [P2] DDC packet bytes 0–3 |
| 4–11 | Time stamp [63:0] | 0 (B6.6) | [P2] bytes 4–11; 0004 option 2C |
| 12–13 | Bits per sample [15:0] | 24 (0x0018) | [P2] bytes 12–13; 0004 point 1 |
| 14–15 | I&Q samples per frame [15:0] | 238 (0x00EE) | [P2] bytes 14–15; B6.4 |
| 16–18 | I sample 0 [23:0] | signed two's complement | [P2] bytes 16–18 |
| 19–21 | Q sample 0 [23:0] | signed two's complement | [P2] bytes 19–21 |
| 22–1437 | I and Q samples 1–236 | same layout, 6 bytes per sample | [P2] DDC packet |
| 1438–1440 | I sample 237 | | [P2] (follows from layout) |
| 1441–1443 | Q sample 237 [23:0] | | [P2] bytes 1441–1443 |

B6.3 **Samples and format.** Each I and Q value MUST be a 24-bit signed two's-complement
integer, MSB first, I before Q, samples in time order ([P2] DDC packet, "DDC I/Q Samples";
NOTE on I and Q order). Only 24 bits per sample and the Big-Endian 3-byte format are offered;
no float, double or little-endian format (0004 point 1). A General packet byte 39 that asks for
any other format MUST NOT be followed, and DDC0 MUST NOT run while that request stands; the
reason is reported in `STREAM_STATUS` (0004 point 7; B8). Byte 39 values that select only
Big-Endian (bit [0]) and/or 3-byte (bit [2]), and 0x00, are read as the offered format
(provisional; Annex X2, C9).

B6.4 **Samples per packet.** Each packet MUST carry 238 I&Q samples: 16 + 238 × 6 = 1444 bytes
([P2] DDC packet table, last sample "Q Sample 237" at bytes 1441–1443; 0004 point 1). Bytes
14–15 MUST state the number of samples that follow ([P2] DDC packet, "I&Q Samples per frame").
A host MUST read bytes 14–15 rather than assume 238 ([P2], same field). Informative: at
384 ksps this is about 1613 packets per second and 18.6 Mbit/s payload (0004, "Per stream").

B6.5 **DDC-specific packet.** The G7250 MUST accept the DDC-specific packet on port 1025
([P2] DDC specific packet) and treat its fields as in Table B6-2. Fields not listed are
ignored.

Table B6-2 — DDC-specific packet fields ([P2] DDC specific packet)

| Byte | Field | G7250 behaviour | Source |
|------|-------|-----------------|--------|
| 4 | Number of ADCs | accepted; the G7250 uses its own ADC count, TBD (HIS-01) | [P2] byte 4 |
| 5 | Dither ADC0–7 | bit [0]: honoured if the ADC supports dither, else ignored; TBD (HIS-01) | [P2] byte 5 |
| 6 | Random ADC0–7 | bit [0]: as byte 5; TBD (HIS-01) | [P2] byte 6 |
| 7 | DDC enable DDC0–7 | bit [0] honoured: DDC0 sends I&Q only while set and run is set; bits [1]–[7] ignored | [P2] byte 7; B5.3; 0004 point 7 ("Enables for DDC1–DDC79 are ignored") |
| 8–16 | DDC enable DDC8–79 | ignored | [P2] bytes 8–16; 0004 point 7 |
| 17 | ADC for DDC0 | 0 (ADC0) honoured; other values TBD (HIS-01, HIS-03) | [P2] byte 17; 0004 point 1 |
| 18–19 | Sampling rate DDC0, ksps | offered rates honoured (B6.7); any other value: refused, DDC0 does not run (B6.7) | [P2] bytes 18–19; 0004 points 1, 7 |
| 20–21 | CIC1, CIC2 DDC0 | ignored ("For future use" in [P2]) | [P2] bytes 20–21 |
| 22 | Sample size DDC0 | 24 honoured; 0 read as the default 24; any other value: refused, DDC0 does not run | [P2] byte 22; 0004 point 7 |
| 23–496 | ADC, rate, CIC, size DDC1–79 | ignored | [P2] bytes 23–496; 0004 point 7 |
| 1363–1442 | Sync DDC0–79 | ignored; synchronous DDCs not supported unless HIS-03 shows a second ADC | [P2] bytes 1363–1442; HIS-03 |
| 1443 | Currently not used | ignored | [P2] byte 1443 |

A change of DDC0 sampling rate to another offered rate while running SHOULD take effect
without a stop, since [P2] sends the DDC-specific packet "when a parameter changes" ([P2] DDC
specific packet, introduction). Whether the sequence counter restarts on a rate change, or
when DDC0 resumes after a refusal: TBD (no decision; 0004 does not fix it).

B6.6 **Time stamp.** Time stamps and VITA-49 are not offered: bytes 4–11 of each DDC packet
MUST be sent as zero (0004 option 2C, point 1). A General packet with byte 37 bit [0] (time
stamp) or bit [1] (VITA-49) set MUST NOT be followed, and DDC0 MUST NOT run while it stands;
the reason is reported in `STREAM_STATUS` (0004 point 7). Record `streams` bit 5 = 0 (B4.8).

B6.7 **Sample rates.**

- The offered DDC0 rates are 48, 96, 192 and 384 ksps ([P2] DDC-specific bytes 18–19; 0004
  point 1, option 1B). 384 ksps is offered only if the SPI clock is about 50 MHz or more;
  below that the maximum is 192 ksps (0004 point 6; Resolved). SPI clock: TBD (HIS-14). The
  set also depends on what the ADC chain can produce (HIS-01). The offered set MUST be stated
  in `ddc_rates` (B4.8).
- 768 and 1536 ksps MUST NOT be offered, not even receive-only (0004 point 7; Resolved).
- A DDC-specific packet with a DDC0 rate outside the offered set MUST be refused: DDC0 does not
  run (it stops if running) until a valid DDC-specific packet arrives, and the reason is
  reported in `STREAM_STATUS` (0004 point 7, option 6D). The rate MUST NOT be clamped to an
  offered value, and the previous rate MUST NOT be kept (0004 point 7; options 6A, 6B, 6C
  rejected). Annex X1, D13.
- Design target: worst-case SPI load (RX at the maximum rate, TX, status at 1 ms, all offered
  streams) at or below 60 % at the actual SPI clock (0004 point 6). Informative.

B6.8 **Receive frequency.** DDC0 frequency is set by High Priority bytes 9–12, in Hz or as a
phase word as declared in discovery byte 21 ([P2] High Priority packet bytes 9–12; General
packet byte 37 bit [3]; B3.8). Range: 0.5–30 MHz and 50–54 MHz [G7250-MAN], also in
`rx_range` (B4.8). Behaviour outside the range: TBD (B11).

B6.9 **Pacing.** The G7250 SHOULD send a DDC0 packet as soon as 238 samples are available, to
keep latency low (provisional, no decision; by analogy with [P2] "Detailed operation", which
gives this advice for DUC data; the CH394Q has no flow control in UDP mode, [CH394] section
12.2.4). Overrun behaviour: TBD (B11).

B6.10 **Wideband data (milestone M2).** (0004 point 4; option 5C; Resolved.)

- Not offered before M2: a General packet byte 23 enable MUST NOT be followed and no wideband
  packets are sent (0004 point 7). Record `streams` bit 4 = 0, `wb_format` = `wb_frame` = 0.
- From M2, for ADC0 only, out from local port 1027 ([P2] General bytes 21–22): fixed
  parameters 512 samples per packet, 16-bit samples, 8 packets per frame, one frame every 50 ms
  (4096 samples per frame, 20 frames per second), in [P2] Wideband Data packets of 1028 bytes
  (bytes 0–3 sequence number, 512 samples of 16 bits) ([P2] Wideband Data packet; General
  bytes 24–28; 0004 point 4). Stated in `wb_format` and `wb_frame` (B4.8).
- From M2, an enable for ADC0 (General byte 23 bit [0]) MUST be followed only while bytes
  24–28 are 0 or equal to the fixed values (512, 16, 50, 8). Any other value: wideband does not
  run until the request is valid, reason in `STREAM_STATUS`. Enables for other ADCs are not
  followed (0004 point 7). A zero byte 27 or 28 means the G7250 fixed value, not the [P2]
  default of 20 ms or 32 packets (Annex X1, D14).
- Informative: 160 packets/s, 1.32 Mbit/s payload, about 2.3 % SPI at 62 MHz (0004 point 4).
  The frequency resolution is the ADC rate / 4096 (HIS-01). Depends on HIS-01 and HIS-18; if
  raw ADC blocks cannot be delivered, this is revisited (0004 point 4).

B6.11 **Microphone data.** Offered only if HIS-17 shows that the controller's microphone
reaches the main unit, then exactly as [P2] Microphone Data packet: 48 ksps, 16-bit, 64
samples per packet, 132 bytes, out from port 1026 (0004 point 3). Otherwise not offered:
the G7250 MUST NOT send a silent microphone stream for timing (0004 point 3; option 4C
rejected). Record `streams` bit 3 (B4.8).

B6.12 **DDC audio.** Not offered (0017; B2.3).

### B7 P2 field table

Per standard P2 field of the host-to-radio packets: honoured, ignored, refused, or TBD (0005,
Consequences). "Honoured" means as [P2] specifies (B1.4). "Ignored" means accepted with no
effect. "Refused" means the request is not followed and the stream concerned does not run,
with the reason in `STREAM_STATUS` (0004 point 7). The DDC-specific packet is in Table B6-2,
the DUC-specific packet in Table B10-1, the High Priority status packet (radio to host) in
Table B9-1.

Table B7-1 — General packet ([P2] General packet to SDR)

| Byte | Field | G7250 behaviour | Source |
|------|-------|-----------------|--------|
| 4 | Command 0x00 | honoured | [P2] byte 4 |
| 5–12, 15–22 | Port numbers | zero = default honoured; non-default TBD; never onto the management port; moving a port the armed session uses drops the arm | B2.3; 0008 Transport 2; 0007 drop event 9 |
| 13–14 | DDC audio port | ignored | 0017 |
| 23 | Wideband enable | before M2: not followed; from M2: bit [0] per B6.10; other bits not followed | 0004 point 7 |
| 24–28 | Wideband parameters | from M2: 0 or the fixed values; otherwise refused | 0004 point 7; B6.10 |
| 29–32 | Memory-mapped ports | zero = G7250 default port (B8.1); non-default TBD | 0005; B2.3 |
| 33–36 | Envelope PWM | ignored ("Reserved for future use" in [P2]) | [P2] bytes 33–36; 0005 rule 3 |
| 37 [0], [1] | Time stamp, VITA-49 | set: refused (DDC0 does not run while it stands) | 0004 point 7 |
| 37 [2] | VNA mode | TBD (no decision) | [P2] byte 37 |
| 37 [3] | Frequency or phase word | must match discovery byte 21; TBD (HIS-04) | B3.8 |
| 38 [0] | Hardware timer enable | honoured while not armed; forced on while armed; must be set to arm | 0007 Decision 2.3; B5.6 |
| 39 | Endian and I&Q format | Big-Endian 3-byte honoured; anything else refused | 0004 points 1, 7; B6.3 |
| 40–55 | Reserved | ignored | [P2]; 0005 rule 3 |
| 56, 57 | Atlas bus configuration, 10 MHz reference source | ignored ("For Atlas based systems" in [P2]) | [P2] bytes 56–57 |
| 58 [0] | PA enable | TBD (no decision; HIS-12) | [P2] byte 58 |
| 58 [1] | Apollo ATU enable | ignored; the internal ATU is controlled through the register map (`ATU_TUNE`) | 0005 option D; 0007 Decision 6 |
| 58 [2], [3] | Mercury common frequency, clock source | ignored (Atlas only in [P2]) | [P2] byte 58 |
| 59 | Alex enable | TBD; ignored unless HIS-06/HIS-07 show identical meaning | 0005 option D, rule 1 |

Table B7-2 — High Priority packet ([P2] High Priority data packet)

| Byte | Field | G7250 behaviour | Source |
|------|-------|-----------------|--------|
| 4 [0] | Run | honoured | [P2] byte 4; B5.3, B5.4 |
| 4 [1] | Transmit (PTT0) | TX request; keys only when armed, on a 0→1 edge after arm confirmation, within all limits | 0015; 0007 rules 2, 4; B10 |
| 4 [2]–[7] | PTT1–PTT3 / reserved | ignored; never key | 0007 rule 4; Annex X2, C5 |
| 5 [0]–[2] | CWX, dot, dash | TX request under the arm, as PTT | 0007 Decision 6 |
| 6–8 | CWX1–CWX3 | ignored (reserved) | [P2]; 0005 rule 3 |
| 9–12 | DDC0 frequency / phase word | honoured | [P2] bytes 9–12; B6.8 |
| 13–328 | DDC1–DDC79 frequency | ignored while one DDC (HIS-02) | [P2]; 0004 point 1 |
| 329–332 | DUC0 frequency / phase word | honoured; outside the TX ranges a TX request does not key | [P2] bytes 329–332; A3.4 |
| 333–344 | DUC1–DUC3 frequency | ignored (reserved) | [P2]; 0005 rule 3 |
| 345 | DUC0 drive level 0–255 | honoured; mapping to power TBD (HIS-12); `REDUCE` acts radio-side | [P2] byte 345; 0007 rule 4 |
| 346–348 | DUC1–DUC3 drive | ignored (reserved) | [P2]; 0005 rule 3 |
| 1396–1397 | Client control word | bit [0] TUNE accepted as information; does not start the internal ATU; other bits ignored | 0007 Decision 6; 0005 rule 1 |
| 1398–1399 | CAT over TCP port | ignored; CAT stays on the host side | 0011 point 5 |
| 1400 | Transverter and audio enable | TBD (no decision) | [P2] byte 1400 |
| 1401 | Open-collector outputs | ignored; no such outputs [G7250-MAN] | 0007 Decision 6 |
| 1402, 1403 | Metis user outputs, Mercury attenuator | ignored (Atlas only in [P2]) | [P2] bytes 1402–1403 |
| 1404–1427 | Alex 2–7 | ignored (reserved) | [P2]; 0005 rule 3 |
| 1428–1435 | Alex 0, Alex 1 words | TBD; ignored unless HIS-06/HIS-07 show identical meaning | 0005 option D, rule 1 |
| 1436–1441 | Step attenuators 2–7 | ignored (reserved) | [P2]; 0005 rule 3 |
| 1442 | Step attenuator ADC1 | ignored unless a second ADC exists (HIS-03) | [P2] byte 1442 |
| 1443 | Step attenuator ADC0 | TBD (HIS-07; identical-meaning check, 0005 rule 1) | [P2] byte 1443 |

Other host-to-radio packets: DUC I&Q (B10.7); memory-mapped registers from PC (B8); Erase,
Program, Set IP (B3.9); DDC audio (not received, B2.3).

The P2 field table is complete for M1. Rows marked TBD are closed when the HIS answers or a
decision is taken (0005, Consequences).

### B8 G7250 register map

B8.1 **Port and packets.** The G7250 register map is carried by [P2] "Memory mapped registers
from PC" and "Memory mapped registers from hardware" packets: up to 240 pairs of a 16-bit
address and a 32-bit data word, bytes 4–1443 ([P2]; 0005). The G7250 uses one local port for
both directions (B2.3; 0005, Consequences). Default port number: TBD (0003, "left to spec part
B"; 0005). It has to be fixed before M1, because a host needs it to send `CAP_REQUEST` (0003,
Consequences). Informative: a number in 1024–1029 or 1035–1114 would collide with [P2]
default or DDC ports ([P2] General bytes 5–22).

B8.2 **Sending.** The G7250 sends a memory-mapped packet whenever data changes and optionally
periodically ([P2] Memory mapped registers from hardware); B9.4 gives the telemetry rates.
Register packets and High Priority status packets are not synchronised; a host MUST NOT
assume they describe the same instant (0006, Consequences).

B8.3 **Groups and addresses.** Addresses are TBD except the capability record (proposed
0x0000–0x00B8, B4.2). The bit assignment of `regmap_groups` (B4.8) is TBD; candidate groups
named in 0003: antenna, ATU, TX arm and safety, telemetry, external interfaces. Registers for
antenna, filter and front-end control are reserved until the HIS answers (HIS-06, HIS-07,
HIS-09; 0005, Consequences).

B8.4 **Write confirmation and ordering.** For `TX_ARM` the confirmation is the push of
`TX_ARM_STATE` and keying needs a TX-request edge after it (B10.2; 0007 rule 2). Writes to the
capability record are answered with the current values (B4.6). The general confirmation rule
for other writes and their ordering against High Priority packets: TBD (0005, Consequences).

B8.5 **Writes from a host that is not the owner.** `CAP_REQUEST` is accepted from any host
(B4.4). `TX_ARM` from a host that is not the owner is rejected (0007 rule 1). `FAULT_CLEAR` is
accepted only from the owner (0007 Decision 5). Other writes from non-owners: TBD (B11).

B8.6 **Units.** Analogue telemetry registers are signed 32-bit integers in milli-units of an SI
unit (mV, mA, mW, m°C; SWR as 1000 × SWR). Status registers are enumerations or bit fields
(0006 option 3A).

Table B8-1 — G7250 registers (symbolic; "RO" = read-only, radio → host; "WO" = written by
the host; address TBD unless stated)

| Name | Address | Dir / access | Content, units | Sent | Source |
|------|---------|--------------|----------------|------|--------|
| capability record (Table B4-1) | `CAP_BASE` + offset; proposed 0x0000–0x00B8 | RO | Table B4-1 | on `CAP_REQUEST`; once per session | 0003 §2, §3 |
| `CAP_REQUEST` | TBD (control range) | WO, any host | write requests the record; value TBD | — | 0003 §2 |
| `STREAM_STATUS` | TBD | RO | per stream (DDC0, DUC0, microphone, wideband): running or not, and refusal reason (for example "DDC0 rate not offered"); codes TBD | on change | 0004 point 7, Consequences |
| `LINK_STATUS` | TBD | RO | current link speed; session refusal reason ("link speed below 100 Mbit/s"); codes TBD | on change | 0003 §2; 0004 point 9 |
| `TX_ARM_TOKEN` | TBD | RO | 32-bit token, never 0 or 0xFFFFFFFF, differs from the previous token | at session start and on every change | 0007 Decision 1 |
| `TX_ARM` | TBD | WO, owner | `token XOR ARM_MAGIC` arms; 0 disarms; any other value rejected | — | 0007 Decision 1 |
| `TX_ARM_STATE` | TBD | RO | disarmed / armed / inhibited; arm generation counter (+1 per arm); last reject reason; last drop reason (Table A3-1); layout TBD | on every change | 0007 Decision 1; 0006 |
| `TX_STATE` | TBD | RO | keyed or not (PA actually keyed); source of the current TX (PTT, CWX, KEY, ATU); active inhibits; `WARN` flags; last unkey reason (keyed timeout, underrun, limit) | on every change (event) | 0007 Decisions 1, 2, 4; 0006 |
| `TX_MODE_CLASS` | TBD | WO, owner | declared TX mode class; enumeration TBD, with at least the power classes of [G7250-MAN] (SSB/CW/NFM 100 W; AM 25 W) | — | 0007 Decision 4 rule 3 |
| `KEYED_TIMEOUT` | TBD | WO, owner | ms; default 500; host may write 100–500 | — | 0007 Decision 2; Resolved 2 |
| `WATCHDOG_STATE` | TBD | RO | General byte 38 bit [0] as written; effective state | on change | 0007 Decision 2.3 |
| `LIMIT_<name>` | TBD | WO, owner | per-session stricter value of a limit in Table A3-2 (for example maximum continuous TX time); units TBD; looser value rejected | — | 0007 Decision 4 rule 1 |
| `LIMIT_STATUS` | TBD | RO | bit field, per limit (SWR, temperature, power, max TX time, supply): "limiting", "tripped" | event | 0006; 0007 |
| `SAFETY_STATE` | TBD | RO | normal / fault | event | 0007 Decision 5 |
| `FAULT_CODE` | TBD | RO | first cause; enumeration, 0 = none; codes TBD | event | 0007 Decision 5; 0006 |
| `FAULT_FLAGS` | TBD | RO | latched bitmask of all causes since the last clear | event | 0007 Decision 5 |
| `FAULT_CLASS` | TBD | RO | 1 host-clearable, 2 latched until reset | event | 0007 Decision 5 |
| trip counter | TBD | RO | number of limit trips; name and scope TBD | event | 0007 Decision 5 |
| `FAULT_CLEAR` | TBD | WO, owner | write the current fault code to clear a class 1 fault | — | 0007 Decision 5 |
| `ATU_TUNE` | TBD | WO, owner | starts internal ATU tuning (a TX request under the arm); layout TBD | — | 0007 Decision 6; HIS-08 |
| `ATU_STATE` | TBD | RO | off/bypassed, in line, tuning, tuned, failed | event | 0006; HIS-08 |
| `ANT_STATE` | TBD | RO | antenna actually selected | event | 0006; HIS-06 |
| `TLM_PA_TEMP` | TBD | RO | m°C, signed; one or more sensors | slow | 0006; HIS-11 |
| `TLM_PA_CURRENT` | TBD | RO | mA | fast | 0006; HIS-11 |
| `TLM_SUPPLY_CURRENT` | TBD | RO | mA (if separate from PA current) | fast | 0006; HIS-11 |
| `TLM_SWR` | TBD | RO | 1000 × SWR as used by the safety core; 0 = not valid | fast | 0006; 0007 |
| `SENSOR_VALID` | TBD | RO | bit field, one bit per sensor | event | 0006; HIS-11 |

Constant `ARM_MAGIC`: 32-bit value TBD (0007, "Still open").

Names introduced in this table and not in the decisions (`STREAM_STATUS`, `LINK_STATUS`,
`LIMIT_STATUS`, `ATU_STATE`, `ANT_STATE`, `TLM_*`, `SENSOR_VALID`) label registers that 0003,
0004 and 0006 describe without a name. 0006 "TX state: PA actually keyed" and "TX arm state,
and reason of the last disarm" are carried by `TX_STATE` and `TX_ARM_STATE` of 0007. Every
telemetry register exists only if the HIS confirms the sensor or state; absent sensors are
flagged absent in the capability record, not reported as 0 (0006, Decision).

### B9 Telemetry

B9.1 **Split.** Telemetry that a standard High Priority status field describes with identical
meaning is sent there; everything else is in the G7250 register map (0006 option 1A; 0005).

B9.2 **High Priority status packet** (radio → host, from the port of General bytes 11–12,
default 1025) ([P2] High Priority Status packet; 0006, Decision).

Table B9-1 — High Priority status packet ([P2]; 0006, Decision)

| Bytes | G7250 use | Depends on |
|-------|-----------|------------|
| 0–3 | sequence number, per [P2] (B2.7) | — |
| 4 [0] | PTT input that reaches the main unit (for example the controller microphone PTT); reports the input, never keys TX by itself | HIS-10, HIS-17; 0015; A3.7 |
| 4 [1], [2] | dot, dash of the KEY input, if it reaches the main unit; else 0 | HIS-17 |
| 4 [4] | 1 only if a reference PLL exists and is locked; otherwise 0 | HIS-05 |
| 4 [3], [5]–[7] | 0 | [P2] ([5], [6] "no longer supported") |
| 5 | bit [0] ADC0 overload; other bits 0 unless more ADCs exist | HIS-01, HIS-03 |
| 6–7 | exciter forward power, raw ADC word, only if a separate exciter detector exists; else 0 | HIS-11 |
| 8–13, 16–21, 24–29, 43–48 | 0 (reserved / unused) | 0005 rule 3 |
| 14–15 | PA forward power, raw ADC word, always filled (no Alex) | HIS-11; Annex X1, D19 |
| 22–23 | PA reverse power, raw ADC word, always filled (no Alex) | HIS-11; Annex X1, D19 |
| 30 | [0] DDC FIFO overflow and [2] DUC FIFO underflow from the firmware's own buffers; [1] mic overflow only if microphone data exists; [3] 0 (no speaker) | 0004, HIS-17, 0017 |
| 31–32, 35–36 | DDC and DUC buffer depth in samples, from the firmware's own buffers | 0004 |
| 33–34 | mic FIFO depth if microphone data exists; else 0 | HIS-17 |
| 37–38 | 0 (speaker FIFO; no speaker) | 0017 |
| 39–40 | ADC0 max magnitude in the message period, scaled to 15 bits as [P2] describes, if the DDC chain can provide it; else 0 | HIS-01, HIS-18 |
| 41–42 | 0 unless a second ADC exists | HIS-03 |
| 49–50 | supply voltage at the power input, raw ADC word | HIS-11 |
| 51–59 | 0 (user-specific in [P2]) | 0006 option 1B rejected |

B9.3 **Encoding of the standard fields.** The power and supply fields MUST carry raw ADC
words, exactly as [P2] does; this is not a deviation (0006 option 2A, Decision). The host
converts them with the [P2] Appendix A formulas and this unit's constants from the capability
record (B4.8; 0003 §3):

- supply: `V = x / N × c`, with *N* from `cal_info` [31:16] and *c* = `cal_supply_c` × 10⁻⁶;
- power: `W = (x / N × c1)² / c2`, with *c1*, *c2* from `cal_power[set]` × 10⁻⁶, for
  forward, reverse and exciter power; set *i* applies to `tx_band[i]` if `cal_info` bit 0 is
  set, else set 0 applies to all bands.

There are no fixed constants for board type 200; the constants are those of this unit, per
band where the hardware needs it (0006, Resolved; HIS-11). Taking them from the record
instead of [P2] Appendix A is listed in Annex X1, D20. The safety core uses its own calibrated
values, not these words through the host formula; host display and firmware limits can differ
where the formula does not fit exactly (0006 option 2A, "Against"). Which coupler position the
forward and reverse values describe: TBD (HIS-08, HIS-11; B4.9). A generic P2 host has no
constants for this unit and may show wrong power and supply values (0006, Consequences).

B9.4 **Rates.**

- High Priority status: every 50 ms, every 1 ms while transmitting, and immediately when an
  input bit (bytes 4, 5) changes; immediate sends are limited to one per 1 ms ([P2] High
  Priority Status packet; 0006, Decision). If 1 ms is too costly (HIS-14, HIS-18), this is
  revisited and listed as a deviation (0006, Consequences).
- Register map (placeholders until HIS-11, HIS-14, HIS-18; 0006, Decision; Resolved): event
  registers immediately on change, at most one packet per 1 ms; fast registers every 10 ms
  while transmitting, otherwise with the periodic snapshot; a periodic snapshot of all
  telemetry registers every 1 s in one memory-mapped packet; analogue registers also on change
  beyond a hysteresis stated in the capability record (hysteresis field TBD, B4.9).

B9.5 **G7250 telemetry registers.** The registers of B8 marked slow, fast or event in Table
B8-1, in the units of B8.6. The firmware computes SWR itself; the `TLM_SWR` register is the
value the limits act on. Forward and reverse power are not duplicated in registers (0006,
Decision). Raw readings behind the engineering-unit registers and calibration writes go
through the management channel, not the register map (0006, Consequences; A1).

### B10 Transmit (milestone M4)

Transmit MUST NOT be enabled in a firmware before M3 is closed: record `tx` bit 1 = 0 (B4.8;
design note §6; 0007, header). This section applies from M4.

B10.1 **Every TX request needs the arm.** TX requests are: High Priority byte 4 bit [1] (PTT),
byte 5 bit [0] (CWX), a KEY closure in hardware CW, internal ATU tuning (`ATU_TUNE`) and any
controller request. None of them keys the radio unless TX is armed (0015; 0007 sub-decision 1
rule 4). High Priority byte 4 bits [2]–[7] never key (0007 rule 4).

B10.2 **Arm handshake** (0007, Decision 1, option 1C):

1. The G7250 pushes `TX_ARM_TOKEN` at session start and whenever it changes.
2. The owner writes `TX_ARM_TOKEN XOR ARM_MAGIC` to `TX_ARM`. 0 disarms; any other value
   MUST be rejected.
3. The arm write MUST be accepted only if all of these hold; otherwise it MUST be rejected with
   a reason in `TX_ARM_STATE`: it comes from the owner; RUN is set; the watchdog is
   effectively on and General byte 38 bit [0] was written as set (else `WATCHDOG_DISABLED`);
   the radio is not in fault; no limit inhibit is active; High Priority byte 4 bit [1] is 0 at
   that moment; level 1 is the active level; no firmware update is in progress; a TX mode class
   has been declared in `TX_MODE_CLASS` for this session (else `NO_MODE_CLASS`) (0007 rule 1).
4. The arm takes effect when the G7250 pushes `TX_ARM_STATE` = armed with a new generation
   number. The host MUST wait for it. After arming, the G7250 MUST key only on a 0→1 edge of a
   TX request that arrives after the confirmation; a PTT bit that was already 1 does not key
   (0007 rule 2; [P2] does not order memory-mapped and High Priority packets).
5. The token MUST differ from the previous one; it need not be unpredictable (0007 rule 3;
   generation: HIS-18, HIS-20).
6. The arm is dropped by the events of Table A3-1.

B10.3 **TX mode class.** The host MUST declare the class in `TX_MODE_CLASS` before arming and
MUST update it whenever its TX mode changes. The AM limit (25 W [G7250-MAN]) applies whenever
the declared class is AM. The power measurement applies whatever the host declares. A missing
declaration is never replaced by a default class; the arm is refused (`NO_MODE_CLASS`) (0007
rule 3; Resolved 7). Annex X1, D9.

B10.4 **Limits and faults.** Table A3-2 and A3.5 apply; actions are reported in `TX_STATE`,
`LIMIT_STATUS`, `SAFETY_STATE` and the fault registers (B8). Maximum continuous TX time: 5 min
built-in, `UNKEY` with the arm kept; a host MAY set it stricter through its `LIMIT_<name>`
register, never looser (0007, Resolved 3). TX frequency outside the transmit ranges: the TX
request does not key (Table A3-2).

B10.5 **Keyed timeout and TX IQ underrun** (0007, Decision 2):

- While keyed, the owner MUST send a High Priority packet at least every 100 ms ([P2]
  "Detailed operation", recommended rate). If no High Priority packet from the owner arrives
  within `KEYED_TIMEOUT`, the G7250 MUST unkey, keep the arm, and report the reason in
  `TX_STATE`. `KEYED_TIMEOUT` defaults to 500 ms; the host MAY write a shorter value, floor
  100 ms; a value above 500 ms or below 100 ms MUST NOT be accepted (0007 Decision 2;
  Resolved 2). Whether it returns to 500 ms at session end, and how a rejected write is
  reported: TBD. Annex X1, D7.
- In a non-CW TX, a DUC FIFO underflow ([P2] High Priority status byte 30 bit [2]) lasting
  longer than TBD ms (HIS-18) MUST unkey, arm kept (0007 Decision 2). Annex X1, D8.
- After an unkey the host needs a new 0→1 TX request (A3.3).

B10.6 **DUC-specific packet.** Accepted on port 1026 ([P2] DUC specific packet).

Table B10-1 — DUC-specific packet ([P2] DUC specific packet)

| Byte | Field | G7250 behaviour | Source |
|------|-------|-----------------|--------|
| 4 | Number of DACs | ignored ("Presently unused" in [P2]) | [P2] byte 4 |
| 5 [1] | CW | honoured: selects hardware CW from KEY | [P2] byte 5; 0007 Decision 6 |
| 5 [2]–[6] | Reverse keys, iambic, sidetone, mode B, strict spacing | honoured for the hardware keyer; sidetone TBD (no speaker on the main unit, HIS-17) | [P2] byte 5; 0007 Decision 6 |
| 5 [7] | Break-in | honoured | [P2] byte 5; 0007 Decision 6 |
| 5 [0] | EER | TBD (no decision) | [P2] byte 5 |
| 6–8 | Sidetone level, frequency | TBD (HIS-17) | [P2] bytes 6–8 |
| 9, 10 | Keyer speed, weight | honoured | [P2] bytes 9–10; 0007 Decision 6 |
| 11–12 | Hang delay, ms | honoured | [P2] bytes 11–12; 0007 Decision 6 |
| 13 | RF delay, ms | honoured; SEND asserted before RF | [P2] byte 13; 0007 Decision 6 |
| 14–15 | DUC0 sampling rate | 192 honoured; any other value refused: DUC I&Q not accepted and transmit refused (PA off) until a valid packet; value 0 TBD | [P2] bytes 14–15; 0004 points 2, 7 |
| 16 | DUC0 bits | 24 honoured; any other value refused, as bytes 14–15; value 0 TBD | [P2] byte 16; 0004 points 2, 7 |
| 17 | CW ramp period | TBD (no decision) | [P2] byte 17 |
| 18–49 | Reserved | ignored | [P2]; 0005 rule 3 |
| 50, 51 | Line in, mic boost, Orion mic; line-in gain | TBD (HIS-17) | [P2] bytes 50–51 |
| 52–56 | Reserved | ignored | [P2]; 0005 rule 3 |
| 57–59 | RX step attenuator during TX | byte 59 (ADC0) TBD (HIS-07); bytes 57–58 ignored unless more ADCs (HIS-03) | [P2] bytes 57–59 |

B10.7 **TX IQ (DUC0).** In on port 1029, 192 ksps, 24-bit I and Q, 240 samples per packet,
1444-byte packets as [P2] DUC I&Q Data packet ([P2] DUC I&Q Data packet; "Detailed operation"
NOTE2; 0004 point 2). Record `duc_format` (B4.8). TX IQ is accepted only while no refusal of
B10.6 stands; the PA keys only under B10.2.

B10.8 **Drive level.** High Priority byte 345 is honoured; mapping to power TBD (HIS-12);
`REDUCE` lowers drive on the radio side without changing the host's value (0007 rule 4).

B10.9 **Other TX paths** (0007, Decision 6; A3.7):

| Path | Rule |
|------|------|
| Controller mic PTT | reported in status byte 4 bit [0] if it reaches the main unit (HIS-17); never keys by itself |
| KEY (Morse) | reported as dot/dash, status byte 4 bits [1]–[2]; keys hardware CW only when armed, CW selected (DUC-specific byte 5 bit [1]) and all limits pass; delays per DUC-specific bytes 5, 11–13 (HIS-17) |
| Host CWX | High Priority byte 5; a TX request under the arm |
| SEND output | asserted only while armed and keyed, before RF (RF delay), released after RF; released on every drop event, on standby and in fault (HIS-09) |
| TUNER trigger | under the arm, as ATU tuning (HIS-09) |
| Internal ATU tuning | a TX request: needs arm, owner, frequency in a range, limits, own profile and time limit; started by `ATU_TUNE` (HIS-08); tune power TBD (HIS-08, HIS-12) |
| P2 TUNE bit (High Priority 1396–1397 bit [0]) | information only; does not start the internal ATU |
| Controller ATU key, SWR scan, other controller TX functions | refused while level 1 runs, unless they reach the main unit as reportable requests (HIS-17) |
| Open-collector outputs (High Priority byte 1401) | ignored |

On level 1, controller inputs never key the radio (0007, Resolved 6).

### B11 Error handling and robustness

Only the rules below are decided; the rest is TBD (0001 spec section 11; no decision yet).

B11.1 **Requests not offered.** The G7250 MUST NOT clamp a request to an offered value and
MUST NOT silently keep a previous setting. It refuses: the stream concerned does not run until
a valid request arrives, and the reason is reported in `STREAM_STATUS` (0004 point 7; options
6A–6C rejected). Cases: B6.3, B6.6, B6.7, B6.10, B10.6. Annex X1, D13.

B11.2 **Session refusal** on a link below 100 Mbit/s, with the reason in `LINK_STATUS` (B5.8).

B11.3 **Register writes.** Writes to the capability record are ignored and answered with the
current values (B4.6). Arm writes that fail a precondition are rejected with a reason in
`TX_ARM_STATE` (B10.2). Looser limit writes are rejected, not clamped, and reported (A3.4).

B11.4 **Port 1024.** Erase and Program are ignored without a reply (B3.9).

B11.5 **TBD.** Malformed or short packets; unknown command bytes on port 1024; Set IP to a
unicast address (B3.9); writes to unknown register addresses; register writes from hosts that
are not the owner (B8.5); a run bit without a preceding discovery (B5.2); sequence gaps and
their reporting (B2.7); RX and TX overruns (B6.9); frequencies outside the receive range
(B6.8); the CH394Q reaction to packets on closed ports (0017); reason-code values for
`STREAM_STATUS`, `LINK_STATUS`, `TX_ARM_STATE` and `FAULT_CODE`.

---

## Part C — Level 2: TCI (placeholder)

Part C will define the single G7250 TCI profile, followed by both AetherSDR on level 1 and
the firmware's TCI server on level 2 (0014). Base: [TCI] Transceiver Control Interface,
protocol 2.1 (`sources.md`, read 2026-11-19 in part). Level 2 is built only after gate G6
(0011 point 4). Level 2 sockets share the CH394Q with the management socket, which stays open
(0008, Socket budget; A1.2).

---

## Annex X1 — Differences from standard P2

Every deviation of G7250-P2 from [P2] (B1.5). All decisions listed are accepted; values marked
TBD in the sections concerned may still be open.

| Id | Deviation | [P2] behaviour | G7250 behaviour | Decision | Spec section |
|----|-----------|----------------|-----------------|----------|--------------|
| D1 | No DDC audio stream | Host may send DDC audio to port 1028 ([P2] DDC Audio packet; General bytes 13–14) | No socket on port 1028; General bytes 13–14 ignored; record `streams` bit 2 = 0 | 0017 | B2.3, B4 |
| D2 | Memory-mapped register port defined | Default port "xxxx", undefined ([P2] General bytes 29–32) | Defined default port (TBD), one port for both directions; carries the G7250 register map | 0005, 0003 | B2.3, B8.1 |
| D3 | TX needs an explicit token arm | High Priority byte 4 bit [1] enables transmit ([P2]) | No TX request (PTT, CWX, KEY, ATU) keys unless armed by token handshake; keying only on an edge after confirmation; arm dropped by the events of Table A3-1 | 0015, 0007 | B10.1, B10.2, A3.2 |
| D4 | Hardware timer forced on while armed | Host may clear General byte 38 bit [0] ([P2]) | Clear honoured only while not armed; arming requires the bit set | 0015, 0007 | B5.6 |
| D5 | Takeover drops the arm | Second host's C&C takes over ([P2] Discovery reply byte 4 NOTE) | Takeover always allowed, but unkeys and drops the arm first; new owner starts unarmed | 0007 | B5.7, A2.4 |
| D6 | Owner is IP address and UDP port | "different Host" not defined ([P2]) | A C&C packet from the owner's IP on another source port is a takeover; host must use one source port per session | 0007 | B5.5, A2.2; X2 C7 |
| D7 | Keyed timeout | Only the 1 s watchdog ([P2] "Detailed operation") | While keyed, High Priority at least every 100 ms; none within `KEYED_TIMEOUT` (500 ms) unkeys, arm kept | 0007 | B10.5 |
| D8 | TX IQ underrun unkeys | No such rule ([P2]) | DUC underflow longer than TBD ms in non-CW TX unkeys | 0007 | B10.5 |
| D9 | TX mode class required | No such field ([P2]) | Arm refused without `TX_MODE_CLASS` | 0007 | B10.3 |
| D10 | Safety core overrides PTT | Bit [1] enables transmit ([P2]) | Limits may reduce drive or unkey while PTT is set; 5 min maximum continuous TX; no key outside the TX ranges | 0007, 0011 | A3.4, B10.4 |
| D11 | Memory-mapped packets are not C&C | "any C&C packet" feeds the watchdog; not stated for memory-mapped packets ([P2]) | No memory-mapped packet feeds the watchdog or takes over; a `CAP_REQUEST`-only packet does not start a session; its answer goes to the request's source when the host is not the owner | 0003, 0007 | B4.4, B4.5, B5.6; X2 C6 |
| D12 | Erase and Program ignored | Erase/Program reprogram the EEPROM; Command Reply ([P2]) | Ignored without reply; V3.8 checksum not claimed; update only via the management channel | 0008 | B3.9, A1.8 |
| D13 | Unsupported requests refused | No negative acknowledgement; radio follows the host ([P2]) | Unoffered DDC rate or size, format, time stamp, VITA-49, wideband parameters or DUC rate/bits: stream does not run, reason in `STREAM_STATUS`; never clamped | 0004 | B6.3, B6.6, B6.7, B6.10, B10.6, B11.1 |
| D14 | Wideband defaults | Zero means 512 / 16 bit / 20 ms / 32 packets ([P2] General bytes 24–28) | From M2, fixed 512 / 16 bit / 50 ms / 8 packets; zero means these values; other values refused | 0004 | B6.10 |
| D15 | Session refused below 100 Mbit/s | No link-speed rule ([P2]) | Discovery answered, no stream started, reason in `LINK_STATUS` | 0004 | B5.8 |
| D16 | PTT1–PTT3 never key | Table lists PTT1–PTT3 in byte 4 bits [2]–[4] ([P2]) | Bits [2]–[7] ignored | 0007 | B5.9; X2 C5 |
| D17 | TUNE bit does not tune | Client control bit [0] TUNE for accessory hardware ([P2]) | Information only; internal ATU via `ATU_TUNE` | 0007, 0005 | B7, B10.9 |
| D18 | Open-collector outputs ignored | High Priority byte 1401 drives outputs ([P2]) | Ignored (no such outputs) | 0007 | B7 |
| D19 | Power fields filled without Alex | Status bytes 14–15, 22–23 "Set to zero if Alex not selected" ([P2]) | Always filled from the PA coupler | 0006 | B9.2 |
| D20 | Conversion constants per unit | Constants per board type in Appendix A ([P2]) | Constants of this unit (per band where needed) from the capability record; words stay raw ADC values | 0006 | B9.3 |
| D21 | No port relocation onto the management port | Host may move ports with General bytes 5–32 ([P2]) | A P2 port is not moved onto the management port; default kept, conflict logged | 0008 | B2.3, A1.3 |

Not deviations, but G7250 choices within [P2]: board type 200 (0002); short discovery reply
only, bytes 14–19 and 24–59 zero (0003); one DDC (0004; HIS-02); a contiguous subset of the
[P2] DDC rates (0004); byte 22 = 0x00, Big-Endian 3-byte only (0004); time stamps not offered,
bytes 4–11 zero (0004); DUC 192 ksps 24-bit as current [P2] practice (0004); microphone data
only if HIS-17 allows (0004); raw ADC words in the status fields (0006); P2 Set IP accepted as
[P2] specifies, with logging that is not visible on the wire (0008); the [P2] 1 s watchdog
(0007).

## Annex X2 — Clarifications of [P2]

| Id | [P2] text | G7250 reading |
|----|-----------|---------------|
| C1 | "Hardware to Host Protocol": "Byte order shall be MSB first (little Endian)" | MSB first (big-endian), consistent with "Host to Hardware Protocol" and with General byte 39 = 0 meaning Big-Endian (B2.5) |
| C2 | General, DDC-specific and High Priority packets: sequence number "set to 0x00000000"; DDC, DUC I&Q and memory-mapped packets: per-port counter; reset at "power on" (DDC packet) or "program start" (other packets) | G7250 sends per-port counters on all outgoing streams, reset at power-on and on stop; discovery reply always 0; incoming sequence numbers are not checked (B2.7) |
| C3 | Discovery reply byte 4: "0xFE (0xFF if running)" means a hardware configuration follows, "Appendix A"; Appendix C instead uses byte 4 = 0x02/0x03 and byte 11 = 255 | The G7250 uses neither: byte 4 is only 0x02 or 0x03, never board type 254/255, no Appendix C reply (0003 §1; B3.3, B3.4) |
| C4 | General byte 37: DSP clock "as part of the Discovery response as specified in Appendix B"; Appendix B is "To be written"; Appendix C bytes 27–30 carry the DSP clock | DSP clock for board type 200 is in record field `dsp_clock_hz`, same meaning as Appendix C bytes 27–30 (0003 §3; B3.8) |
| C5 | High Priority packet table: byte 4 "[1] = PTT0…[4] = PTT3"; text: "Bit [1] enables transmit … Bits [2] to [7] are reserved for future use" | Inconsistent in [P2]. The G7250 has one transmitter [G7250-MAN]: bit [1] is the transmit bit; bits [2]–[7] are ignored under either reading and never key (0007 rule 4; Resolved 11; B5.9) |
| C6 | "Detailed operation": "any C&C packet" feeds the watchdog; the term is not listed in one place | C&C packets are the four packets headed "Control Elements": General, DDC-specific, DUC-specific, High Priority. Memory-mapped packets ("Memory Mapped") are not C&C (0007 sub-decision 2.1; 0003 §2; B5.6) |
| C7 | Discovery reply byte 4: 0x03 if "connected to a different Host"; takeover by "the PC sending the C&C commands" | A host is identified by source IP address and UDP port; the owner's IP on another port is a different host (0007, Resolved 4; B3.4, B5.7) |
| C8 | Discovery reply byte 4: 0x03 when "running and already connected to a different Host" | While level 2 is active the RF chain is in use by another controller; the G7250 answers 0x03 (0003, Resolved; B3.4) |
| C9 | General byte 39: 0 selects Big-Endian 3-byte; bits [0] Big-Endian and [2] 3-byte select options "if indicated in the Discovery reply" | Provisional (no decision): 0x00, and values with only bits [0] and/or [2] set, select the offered format; any other bit refuses (B6.3) |
| C10 | General bytes 29–30 "memory mapped data from the PC will be sent to", bytes 31–32 "to the PC will be sent to" | Bytes 29–30 name the G7250's receive port, bytes 31–32 the host's destination port; the G7250 sends from the same local port it receives on (0005, Consequences; B8.1) |
| C11 | Set IP Address packet: success "can be verified by sending a Discovery Command"; Command reply packet: "Following a successful Set IP command, the hardware will respond with a Discovery reply packet" | Both hold: the G7250 sends a Discovery reply after a Set IP, and answers later discoveries with the new address (0008 point 6; B3.9) |

## Annex X3 — Conformance tests

To be implemented in g7250-testbench, first against the reference model, then on the radio
(0001 item 5; design note §5 principle 6). Test ids are stable; descriptions are one line.

### Management channel, ownership, safety (A1–A3)

| Id | Description |
|----|-------------|
| T-A1-01 | The management port answers identification at both levels, also to a broadcast request. |
| T-A1-02 | No management request changes `TX_STATE`, the arm or any RF output. |
| T-A1-03 | A write without a valid HMAC response is refused and logged; a replayed exchange is refused. |
| T-A1-04 | The first-secret window opens only in factory state, closes after its time and after a secret is set. |
| T-A1-05 | An update is refused while armed or transmitting. |
| T-A1-06 | An older image is refused without the downgrade flag and accepted, logged, with it. |
| T-A1-07 | A block with a bad CRC-32 is rejected and requested again; an image for other hardware is refused before writing. |
| T-A1-08 | Power loss at each update step leaves a bootable image (reference model). |
| T-A1-09 | A trial boot without confirmation rolls back and logs it. |
| T-A1-10 | A bad network configuration or an address conflict falls back to the previous one. |
| T-A1-11 | A General packet that moves a P2 port onto the management port leaves the management socket in place and logs the conflict. |
| T-A1-12 | Requests from outside the subnet are not answered, except identification. |
| T-A2-01 | Identification and record `level` report the active level and the owner (IP and port). |
| T-A2-02 | A level change drops the arm with `LEVEL_CHANGE` (after G6). |
| T-A3-01 | Each drop event of Table A3-1 unkeys, disarms, issues a new token and reports its reason (one test per row). |
| T-A3-02 | Each limit row of Table A3-2 gives its action and recovery (one test per row, reference model). |
| T-A3-03 | A looser `LIMIT_<name>` write is rejected, a stricter one accepted, and both revert at session end. |
| T-A3-04 | A class 1 fault clears only with the current code and only when the condition is gone; a clear does not re-arm. |
| T-A3-05 | A class 2 fault clears only by reset and is detected again at start-up if the cause persists. |
| T-A3-06 | After power-on and after every session end the state of A3.6 holds. |
| T-A3-07 | Controller PTT and KEY inputs are reported and never key the radio without arm. |

### Discovery (B3)

| Id | Description |
|----|-------------|
| T-B3-01 | Broadcast discovery to 255.255.255.255:1024 yields exactly one reply. |
| T-B3-02 | Directed discovery to the unit's IP:1024 yields exactly one reply. |
| T-B3-03 | Discovery to the subnet broadcast address yields exactly one reply. |
| T-B3-04 | Reply comes from port 1024 to the host's IP and source port. |
| T-B3-05 | Reply payload is 60 bytes; bytes 0–3 are zero. |
| T-B3-06 | Byte 4 is 0x02 when idle. |
| T-B3-07 | Byte 4 is 0x03 when running for host A and discovery comes from host B. |
| T-B3-08 | Byte 4 is 0x02 when running for host A and discovery comes from host A on the same port. |
| T-B3-09 | Bytes 5–10 equal the unit's link MAC address and are stable across power cycles. |
| T-B3-10 | Byte 11 is 200 (0xC8). |
| T-B3-11 | Byte 12 is 44 and equals `p2_version`. |
| T-B3-12 | Byte 13 equals major × 10 + minor of `fw_version`. |
| T-B3-13 | Bytes 14–19 and 24–59 are zero. |
| T-B3-14 | Byte 20 equals `num_ddc` and the number of DDCs that can be enabled and streamed. |
| T-B3-15 | Byte 21 matches the frequency encoding the unit accepts in High Priority bytes 9–12. |
| T-B3-16 | Byte 22 is 0x00. |
| T-B3-17 | Discovery is answered in Big-Endian format after any General packet. |
| T-B3-18 | Discovery with non-zero bytes 5–59 is still answered. |
| T-B3-19 | Discovery from a non-owner is answered while streaming, without interrupting the stream. |
| T-B3-20 | Erase and Program packets get no reply and change neither firmware nor stored state. |
| T-B3-21 | No UDP port outside Table B2-1 answers or is open; port 1028 is closed. |
| T-B3-22 | Byte 4 is 0x03 when running for host A and discovery comes from host A's IP on another port. |
| T-B3-23 | Byte 4 is 0x03 while level 2 is active (after G6). |
| T-B3-24 | Byte 4 is never 0xFE or 0xFF, and byte 11 never 254 or 255. |
| T-B3-25 | Set IP with the unit's MAC sets and stores the address (0.0.0.0 selects DHCP), is answered with a Discovery reply, works while running and while armed, and is logged with its source. |
| T-B3-26 | Set IP with another MAC changes nothing. |
| T-B3-27 | A discovery from the owner while armed drops the arm with `REDISCOVERY`. |

### Capability record (B4)

| Id | Description |
|----|-------------|
| T-B4-01 | A `CAP_REQUEST` write is answered with one memory-mapped packet holding the echo and the whole record. |
| T-B4-02 | `cap_magic` is 0x47373235, `cap_version` 1.0, `cap_length` equals the number of record registers sent. |
| T-B4-03 | `product_name` reads "G7250-P2". |
| T-B4-04 | A `CAP_REQUEST`-only packet from a host without a session starts no session, takes nothing over, does not feed the watchdog, and is answered to its source IP and port. |
| T-B4-05 | A `CAP_REQUEST` from host B while host A runs does not disturb A's session or arm. |
| T-B4-06 | Writes to the record range are ignored and answered with the current values. |
| T-B4-07 | The record is sent once, unasked, after the first General packet of a session. |
| T-B4-08 | The record does not change during a session. |
| T-B4-09 | `ddc_rates`, `num_ddc`, `streams`, `duc_format`, `wb_format`, `wb_frame`, `link` and `tx` match the behaviour tested in B5, B6 and B10. |
| T-B4-10 | Unused bits and unused range, band and calibration entries are zero. |

### Session, ownership, watchdog (B5)

| Id | Description |
|----|-------------|
| T-B5-01 | Without C&C from the owner for more than one second in RUN, the unit goes to standby, stops streaming and drops the arm. |
| T-B5-02 | Memory-mapped packets alone do not keep the session alive past one second. |
| T-B5-03 | C&C packets from a non-owner do not feed the owner's watchdog; the first one is a takeover. |
| T-B5-04 | Takeover while armed and keyed unkeys, drops the arm with `TAKEOVER`, sends a last `TX_ARM_STATE` to the old owner, and serves the new host unarmed. |
| T-B5-05 | A C&C packet from the owner's IP on a new source port is a takeover. |
| T-B5-06 | General byte 38 bit [0] clear disables the watchdog while not armed; it is ignored while armed; `WATCHDOG_STATE` reports both values. |
| T-B5-07 | An arm with General byte 38 bit [0] clear is rejected with `WATCHDOG_DISABLED`. |
| T-B5-08 | Clearing the run bit stops all streams, resets sequence counters and drops the arm with `RUN_CLEARED`. |
| T-B5-09 | On a 10 Mbit/s link discovery is answered, no stream starts, and `LINK_STATUS` gives the reason. |

### Streams (B6)

| Id | Description |
|----|-------------|
| T-B6-01 | No DDC0 data before a High Priority packet with run set. |
| T-B6-02 | After General, DDC-specific and run, DDC0 packets arrive from port 1035 to the host's discovery source port. |
| T-B6-03 | Every DDC0 payload is 1444 bytes with 24-bit samples. |
| T-B6-04 | Bytes 12–13 are 24 and bytes 14–15 are 238. |
| T-B6-05 | Sequence numbers start at 0 and increase by one per packet, without gaps on a clean link. |
| T-B6-06 | Sequence counter restarts at 0 after stop and run. |
| T-B6-07 | Sequence number rolls over from 0xFFFFFFFF to 0 (reference model; forced counter). |
| T-B6-08 | Packet rate matches the selected sample rate (rate / 238 per second) within tolerance, per offered rate. |
| T-B6-09 | Each offered rate (48, 96, 192, and 384 if offered) streams without loss for a set duration, with and without TX IQ. |
| T-B6-10 | A DDC0 rate outside `ddc_rates` (including 768 and 1536) stops DDC0, is not clamped, and is reported in `STREAM_STATUS`; a valid rate resumes it. |
| T-B6-11 | A known test tone at a set offset from the DDC0 frequency appears at the right frequency and sign (I before Q). |
| T-B6-12 | Samples are signed two's complement, MSB first (full-scale positive and negative test signals). |
| T-B6-13 | Clearing DDC-specific byte 7 bit [0] stops DDC0 data; setting it resumes. |
| T-B6-14 | Clearing the run bit stops all streams within a defined time. |
| T-B6-15 | Changing between offered rates while running takes effect without a stop. |
| T-B6-16 | Fields listed as ignored in Table B6-2 have no effect on the stream. |
| T-B6-17 | A host that does not know board type 200 and never writes the register map still receives DDC0 data (0015). |
| T-B6-18 | A sample size other than 0 or 24 stops DDC0 with a reason. |
| T-B6-19 | General byte 39 asking for little-endian, float or double stops DDC0 with a reason. |
| T-B6-20 | General byte 37 bit [0] or [1] set stops DDC0 with a reason; time stamp bytes 4–11 are otherwise zero. |
| T-B6-21 | Before M2, a wideband enable sends nothing; from M2, ADC0 wideband gives 8 packets of 1028 bytes every 50 ms. |
| T-B6-22 | From M2, wideband parameters other than 0 or the fixed values stop wideband with a reason. |
| T-B6-23 | No microphone packets are sent unless `streams` bit 3 is set. |

### Field table and register map (B7, B8)

| Id | Description |
|----|-------------|
| T-B7-01 | Every field marked "ignored" in Tables B7-1, B7-2 and B10-1 has no effect. |
| T-B7-02 | High Priority byte 4 bits [2]–[7], the TUNE bit and byte 1401 never key or switch anything. |
| T-B8-01 | All registers of Table B8-1 marked "on change" or "event" are pushed within 1 ms of a change. |
| T-B8-02 | `TX_ARM` from a non-owner is rejected; `CAP_REQUEST` from any host is answered. |
| T-B8-03 | `TX_ARM_TOKEN` is never 0 or 0xFFFFFFFF and changes on every drop and every new session. |

### Telemetry (B9)

| Id | Description |
|----|-------------|
| T-B9-01 | High Priority status arrives every 50 ms, every 1 ms while transmitting, and immediately (at most one per ms) on an input change. |
| T-B9-02 | Bytes listed as 0 in Table B9-1 are zero. |
| T-B9-03 | Known supply and power inputs, converted with the record constants and the Appendix A formulas, match within the stated accuracy. |
| T-B9-04 | Event registers arrive before or with the next status packet after a change. |
| T-B9-05 | Fast registers arrive every 10 ms during TX; a snapshot of all telemetry registers arrives every 1 s. |
| T-B9-06 | An absent sensor is flagged absent in the record and has no register. |

### Transmit (B10)

| Id | Description |
|----|-------------|
| T-B10-01 | With `tx` bit 1 = 0, no arm is accepted and nothing keys. |
| T-B10-02 | An arm with the correct `token XOR ARM_MAGIC` is confirmed by `TX_ARM_STATE` with a new generation; any other value is rejected. |
| T-B10-03 | Each arm precondition of B10.2 item 3, when violated, rejects the arm with its reason. |
| T-B10-04 | A PTT bit already 1 at confirmation does not key; a later 0→1 edge does. |
| T-B10-05 | A stale token from an earlier arm or session does not arm. |
| T-B10-06 | An arm without `TX_MODE_CLASS` is rejected with `NO_MODE_CLASS`; with class AM, power is limited to 25 W. |
| T-B10-07 | While keyed, no High Priority packet for 500 ms (or the written shorter value) unkeys and keeps the arm. |
| T-B10-08 | `KEYED_TIMEOUT` values above 500 ms or below 100 ms are not accepted. |
| T-B10-09 | Continuous TX for 5 min (or the stricter value) unkeys and keeps the arm. |
| T-B10-10 | A DUC rate other than 192 or bits other than 24 refuses TX IQ and keeps the PA off, with a reason. |
| T-B10-11 | A DUC underflow longer than the set time in non-CW TX unkeys and keeps the arm. |
| T-B10-12 | A TX request with DUC0 outside the transmit ranges does not key. |
| T-B10-13 | SEND is asserted only while armed and keyed, before RF, and released on every drop event, standby and fault. |
| T-B10-14 | `ATU_TUNE` without arm does not tune; with arm it tunes within its time limit. |
| T-B10-15 | KEY keys hardware CW only when armed and CW is selected. |

---

## Sources

- [P2] openHPSDR Ethernet Protocol V4.4: "Detailed operation" (session, watchdog, standby,
  restart, NOTE2); "openHPSDR Host to Hardware Protocol"; "openHPSDR Hardware to Host
  Protocol"; Discovery packet; Erase, Program, Set IP Address packets; General packet bytes
  4–59; DDC specific packet bytes 4–1443; DUC specific packet bytes 4–59; High Priority data
  packet bytes 4–1443; DUC I&Q Data packet; Microphone Data packet; Wideband Data packet;
  Memory mapped registers from PC / from hardware; Discovery reply bytes 0–59; Command reply
  packet (including "Set IP"); DDC packet bytes 0–1443; High Priority Status packet bytes
  0–59; Appendices A, B, C; revision history (V2.7, V3.8).
- [CH394] WCH CH394 manual 1, V1.2: sections 1–3, 7.1.2–7.1.7, 7.2, 12.2.4.
- [G7250-MAN] Xiegu G7250 Operation Manual rev 0.1; [G7250-PUDX], [G7250-RIGPIX] (50 MHz
  power, secondary).
- [TCI] Transceiver Control Interface 2.1 (read in part).
- [FIPS-180-4] NIST FIPS 180-4 (SHA-256); [RFC2104] HMAC. Public standards cited by 0008, not
  yet listed in `sources.md`.
- `analysis/ch394-network-budget.md`; `open-questions-his.md` (HIS-01 to HIS-20).
- Decisions 0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0011, 0012, 0014, 0015,
  0016, 0017, 0018; design note §6.
- RFC 2119, RFC 8174 (BCP 14).

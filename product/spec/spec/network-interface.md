# G7250 network interface specification

- Version: draft 4 (rc1 candidate), 2026-11-19
- Status: draft. Brings the text in line with decisions 0003, 0004, 0006, 0007 and 0008, all
  accepted by ON8ST on 2026-11-19, and applies the detail choices of 0020 (proposed, for
  ON8ST review at rc1), the points of 0021 that concern parts A and B, and the review fixes
  of 0022 (proposed, for ON8ST review at rc1). Focus: milestone M1
  (discovery, capability block, RX IQ on G7250-P2); sections for M2–M5 are complete except for
  values that depend on the hardware.
- © 2026 ON8ST, CC BY 4.0 (see `LICENSE.md`).
- Structure: decision 0001, "(2) Network-interface spec", as revised by 0016, split into parts
  A, B and C by 0011.

Sources are cited by key (see `sources.md`) or by decision number (see `decisions/`).
Citations of [P2] give the packet name and byte number of [P2] V4.4. A value that depends on
an open hardware question is marked "TBD" together with its HIS id, for example HIS-14 (see
`open-questions-his.md`). Every other value is fixed by a decision; detail choices are cited
as "0020 §n" and "0022 §n". Register names in `CODE` style have their addresses in B8 (Table B8-2).

The key words of B1.2 apply to the whole document, parts A, B and C.

---

## Part A — Common to both levels

Part A holds what applies to every level (0011, Consequences): the management channel, level
selection and ownership, and the safety behaviour that a host can see on the network.

### A1 Management channel

This section fixes the requirements of the management channel: port, framing, commands,
status codes and timeouts (0008, Consequences; 0020 §2, §24, §27). Payload layouts of the
individual commands are fixed with the reference model (0019) before M5 and do not change the
framing (0020 §27).

A1.1 **Purpose.** The management channel carries identification, configuration, logs and
firmware update, on a connection separate from G7250-P2 and TCI (0001 spec section 10; 0008).

A1.2 **Transport.** The management channel MUST use its own UDP port, served by the eighth
socket of the CH394Q (0008, Decision, Transport 1; 0017). That socket is reserved at both
levels, MUST be open whenever the network is up, and MUST NOT be closed to make room for
another level (0008, Transport 1; Socket budget).

A1.3 **Port number.** The management channel uses local UDP port **7251** (0020 §2). This
lies outside 1024–1029, outside the wideband default ports 1027–1034 and outside the DDC
range 1035–1114 ([P2] General packet bytes 17–22; 0008, Transport 2), and differs from the
TCI port 50001 (0021 §2). If a General packet asks to move a P2 port onto the management
port, the G7250 MUST NOT give the management socket away; it MUST keep the default for that
P2 port and log the conflict (0008, Transport 2; B2.3; Annex X1, D21, D22). The port is
announced in the capability record field `mgmt` (B4, 0003).

A1.4 **Framing.** The channel is request/response. Every request MUST carry a request id;
every reply MUST echo it and carry a status code. Large transfers MUST be split into numbered
blocks, each acknowledged; the host retransmits on a timeout (0008, Transport 3). The channel
has its own protocol version, reported in identification, independent of the P2 version and
of the capability-record version (0008, Transport 4). Every message is one UDP datagram,
big-endian, with the header of Table A1-1 (0020 §27).

Table A1-1 — Management message header (0020 §27)

| Bytes | Field |
|-------|-------|
| 0–3 | magic 0x47374D47 ("G7MG") |
| 4, 5 | protocol version major, minor; 1, 0 in this version |
| 6 | type: 1 request, 2 reply |
| 7 | flags: bit 0 authenticated (HMAC trailer present); bit 1 more blocks follow |
| 8–11 | request id, chosen by the host, echoed in the reply |
| 12–13 | command (Table A1-2) |
| 14–15 | status (Table A1-3); 0 in requests |
| 16–17 | payload length *N* |
| 18 … 17 + *N* | payload |
| next 32 bytes | HMAC-SHA256 [RFC2104], [FIPS180-4] over the challenge and bytes 0 … 17 + *N*; present only if flag bit 0 is set |

- A request MUST NOT exceed 1000 bytes, so that it fits a 1 KB socket receive buffer with the
  8-byte CH394Q receive header ([CH394] section 12.2.4); a reply MUST NOT exceed 1400 bytes;
  an update block carries 512 data bytes (0020 §27).
- A repeated request id from the same host (IP address and port) MUST be answered with the
  stored reply and MUST NOT be executed again (0020 §27). The G7250 keeps the last reply per
  host for 5 s, for up to 4 hosts (IP address and port), evicting the least recently used;
  after expiry a repeated authenticated request fails with status 33, because its challenge
  is spent (0022 §11).
- A host SHOULD retransmit after 500 ms without a reply, at most 5 times (0020 §24).
- A datagram with another magic MUST be dropped without reply. A datagram with the right
  magic but shorter than 18 bytes, or whose length does not match *N*, MUST be answered with
  status 17 if bytes 8–11 are present (12 bytes or more), else dropped (0022 §20). A request with an unknown major version
  MUST be answered with status 18, the G7250's own version in bytes 4–5 (0020 §27; B11.13).

Table A1-2 — Management commands (0020 §27)

| Code | Command | Auth | Function |
|------|---------|------|----------|
| 0x0001 | `IDENTIFY` | no | A1.5 |
| 0x0002 | `GET_STATS` | no | packet, error and gap counters (B11) |
| 0x0010 | `GET_CHALLENGE` | no | fresh challenge for one authenticated request (A1.10) |
| 0x0011 | `SET_FIRST_SECRET` | no (window only) | A1.10 |
| 0x0012 | `CHANGE_SECRET` | yes | A1.10 |
| 0x0013 | `END_WRITE_SESSION` | yes | releases the write session (A1.10) |
| 0x0020, 0x0021 | `GET_CONFIG`, `SET_CONFIG` | no, yes | A1.6 |
| 0x0022 | `FACTORY_RESET` | yes | A1.6 C-5 |
| 0x0023 | `SWITCH_LEVEL` | yes | A1.6 C-2; procedure A2.5 |
| 0x0024 | `RESTART` | yes | unkey and disarm first (A1.9), then reset; also clears class 2 faults (A3.5) |
| 0x0030, 0x0031 | `READ_LOG`, `CLEAR_LOG` | no, yes | A1.7 |
| 0x0040–0x0046 | `UPDATE_BEGIN`, `UPDATE_BLOCK`, `UPDATE_VERIFY`, `UPDATE_ACTIVATE`, `UPDATE_ABORT`, `UPDATE_STATUS`, `ROLLBACK` | yes (`UPDATE_STATUS` no) | A1.8 |

Table A1-3 — Management status codes (0020 §27)

| Code | Meaning | Code | Meaning |
|------|---------|------|---------|
| 0 | OK | 48 | invalid configuration |
| 1 | accepted, in progress | 49 | not allowed (would loosen a limit or touch TX) |
| 16 | unknown command | 50 | refused while armed or transmitting |
| 17 | malformed | 51 | wrong hardware |
| 18 | unsupported protocol version | 52 | older image without downgrade flag |
| 19 | too large | 53 | bad block CRC |
| 32 | authentication required | 54 | block out of order |
| 33 | authentication failed | 55 | verification failed |
| 34 | rate-limited | 56 | not supported in this firmware |
| 35 | busy (another writer) | 57 | refused while a P2 session runs |
| 36 | first-secret window closed or secret already set | | |

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

Identification MUST also be answered to a broadcast request (0008, I-6).

A1.6 **Configuration** (write needs authentication, A1.10) (0008, Functions):

- network: static or DHCP; address, netmask, gateway (C-1; [CH394] sections 7.1.2–7.1.5);
- level selection: default level at power-on, and a request to switch level now; level 2 is
  selectable only once it exists, after gate G6 (C-2; 0011 point 4);
- safety settings that MAY only be made stricter than the built-in limits: maximum TX time,
  power limit per band, SWR and temperature limits; built-in limits and the TX band edges per
  region MUST NOT be writable (C-3; 0011 point 3; 0007 sub-decision 4 rule 1). These are the
  persistent tier of A3.4; a change while armed drops the arm (`MAINTENANCE`, Table A3-1
  event 11) and then applies at once (0022 §6);
- configuration MUST be validated as a whole before it is applied, stored in non-volatile
  memory with a version and a check value, and survive a restart; a network change is applied
  after the reply is sent; if the new network configuration cannot be brought up, or an
  address conflict is detected ([CH394] section 7.1.7, GINT IP_CONFLI), the G7250 MUST fall
  back to the previous configuration and log it (C-4);
- a factory reset of network configuration and secrets MUST be possible over this channel
  (authenticated) and MUST also be possible locally without the network; the local path is
  TBD (HIS-17, HIS-19) (C-5);
- the region whose transmit ranges apply (C-6): factory default is the intersection of the
  transmit ranges of all regions in [G7250-MAN]; a change MUST be refused with status 57
  while a P2 session runs, so that the record stays constant within a session (0020 §23;
  B4.7), and with status 50 while TX is armed or keyed on any level; on level 2, unarmed, it
  applies at once (0022 §9);
- an optional TCI client allow-list (C-7) of 0 to 8 entries, each an IPv4 address with a
  prefix length 0–32; empty (the factory default) means any address in the radio's own
  subnet. It applies to TCI connections only; when a new list is applied, open TCI
  connections it no longer allows MUST be closed and logged (0021 §10; 0020 §31). TCI
  connections are accepted only from the radio's own subnet in any case (0021 §10).

A1.7 **Logs** (read without authentication; clearing needs authentication) (0008, Functions):
a ring buffer of events with an uptime timestamp in ms, wall-clock time only if the main unit
knows it (HIS-17) (L-1). The log MUST record at least: resets and their cause, safety-core
trips and faults, TX arm and disarm, host takeover, level changes, configuration changes with
the source address (including P2 Set IP, B3.9), every update step, authentication failures and
port conflicts (L-2; 0007, Consequences). It is read in pages by sequence number (L-3). Size
and persistence across reset: TBD (HIS-18). Packet, error and sequence-gap counters are read
with `GET_STATS` (0020 §19, §28).

A1.8 **Firmware update** (authenticated) (0008, Functions, U-1 to U-10):

- An update MUST be refused while TX is armed or the radio is transmitting. Once an update
  starts, the G7250 MUST leave RUN, refuse any new P2 RUN or arm, and stay in the receive-safe
  state of 0015 until it restarts (U-1; 0007 drop event 11, `MAINTENANCE`). In detail
  (0022 §10): from `UPDATE_BEGIN` on, the P2 session ends and all RX streams stop; a High
  Priority packet with run set is answered, at most once per 100 ms, with `STREAM_STATUS`
  reason 10; register writes are rejected with `BUSY`, which takes precedence over
  `NOT_OWNER`; `CAP_REQUEST` is still answered. The state lasts until a restart, also after
  `UPDATE_ABORT` (which discards the staging area and says in its reply that a `RESTART` is
  needed) and after an abandoned transfer.
- One package per update, with a header: magic, target hardware id and revision, component
  list, versions, length, SHA-256 [FIPS180-4] per component, and a signature field that is
  reserved and empty in this version. An image for other hardware MUST be refused before
  anything is written (U-2; 0008 option I1).
- Transfer in numbered blocks with a CRC-32 each, into a staging area that is not the running
  image; resumable; abandonable without effect on the running image (U-3).
- The staged image MUST be hashed and compared with the header before activation. No
  signature is checked in this version (U-4; 0008, Resolved 5).
- Activation MUST be atomic; power loss before the switch leaves the old image running (U-5).
- The first boot of a new image is a trial; without self-confirmation within 60 s of start,
  the boot loader MUST return to the previous image and log the rollback (U-6; 0020 §24).
  Until the image has confirmed itself, RX works but an arm MUST be rejected with
  `MAINTENANCE` (0022 §10).
  Feasibility of two slots and atomic boot choice: TBD (HIS-18, HIS-19) (U-10).
- The boot loader is not updated through this channel (U-7).
- An image older than the running one MUST be refused unless the request carries an explicit
  "downgrade" flag; a downgrade is logged; configuration the older image does not understand
  is kept but not used, and the reply says so (U-8; 0008, Resolved 3).
- A recovery path that does not depend on this firmware MUST exist; which one: TBD (HIS-19,
  HIS-17) (U-9).
- The G7250 MUST NOT program itself through P2 Erase and Program packets (B3.9).

A1.9 **Management never keys the radio or loosens a limit.** No request on this channel MAY
key the radio, set PTT, arm TX, set the drive level, switch an RF-path relay or loosen a
safety limit (0008 S1; 0011 point 3; 0015; 0007). Management MAY unkey and disarm, and then
always in the order of A3.2 (0022 §8):

- `RESTART` and `FACTORY_RESET` are accepted while armed or keyed; they unkey and disarm
  first, then reset (`FACTORY_RESET` drops with `MAINTENANCE`; the reset is Table A3-1
  event 5);
- `SWITCH_LEVEL` unkeys and disarms first (`LEVEL_CHANGE`; A2.5);
- `SET_CONFIG` with C-3 limits drops the arm (`MAINTENANCE`); a region change is refused
  while armed or keyed (A1.6 C-6);
- a firmware update is refused while armed or transmitting (A1.8);
- every other command leaves the TX state unchanged.

0008 U-1 ("the management channel cannot disarm … for them") is read as: an update does not
disarm; the owner disarms first (0022 §8).

A1.10 **Security on a LAN** (0008, Security):

- Writes (configuration, level switch, log clear, update, rollback) MUST require a per-radio
  secret, proven by challenge and response: a fresh random challenge from the radio, answered
  with HMAC-SHA256 [RFC2104], [FIPS180-4] over the challenge and the request. Reads need no
  authentication (S2). A challenge is valid for one request and 10 s (0020 §24). Source of
  randomness: TBD (HIS-20).
- **Challenge per host** (0022 §11). The G7250 MUST keep one outstanding challenge per host,
  keyed by source IP address and UDP port, for up to 4 hosts; a fifth host evicts the least
  recently used. A new `GET_CHALLENGE` replaces that host's challenge. The challenge is used
  by the next authenticated request from the same IP address and port, and only once.
- **Secrets on the wire** (0022 §11). The secret is 32 bytes. `SET_FIRST_SECRET` carries it
  in the clear (known risk; S3, S6). `CHANGE_SECRET` MUST be authenticated with the old
  secret and carries the new secret masked as new secret XOR HMAC-SHA256(old secret, "G7NS"
  ‖ challenge) [RFC2104], so it does not cross the network in the clear. Apart from
  `SET_FIRST_SECRET`, the secret never crosses the network.
- **Replies are not authenticated** (known limit, 0022 §11): a host on the LAN can forge a
  reply. A tool SHOULD verify a write by reading the value back.
- **First secret.** In factory state, during a one-time window after the first power-on or
  after a factory reset, the first host that sends a "set first secret" request sets it,
  without confirmation on the controller. The window lasts 300 s of uptime from the moment
  the network is up; it is used up when it has run to its end or a secret is set, and a
  restart before that opens a fresh 300 s window (0020 §24; 0008 S3, "a few minutes"). The
  window MUST open only while no secret is set, MUST NOT reopen once used up without a
  factory reset, and the claim MUST be logged with its source address (S3; 0008, Resolved 1).
  Risk, stated by 0008: anyone on the LAN during the window can claim the radio.
- Requests MUST be answered only from the radio's own subnet and never from a broadcast
  source, except identification; authentication failures MUST be rate-limited and logged
  (S4). Replies MUST NOT exceed 20 per second per source IP address and port; requests above
  that are dropped and counted (`GET_STATS`) (0022 §16).
- One writer at a time: a write session is held by one host (address and port), opened by its
  first authenticated write and ended by `END_WRITE_SESSION` or after 60 s without a request
  (0020 §24); others get status 35 ("busy") for writes and normal answers for reads (S5).
- No confidentiality in this version (S6).
- P2 Set IP on port 1024 is the one unauthenticated write (B3.9; S7).

A1.11 **DHCP.** Provisional (0008, Socket budget, "Proposed … to be fixed in spec part A;
depends on HIS-14"): the DHCP exchange at power-on runs before the P2 sockets are opened;
lease renewals borrow the management socket for the few seconds the exchange takes; final
rule TBD (HIS-14).

### A2 Ownership and level selection

A2.1 **Single owner.** Only one level controls the RF chain at a time, and only that level's
owner MAY transmit (0011 point 2).

A2.2 **Owner identity.** On level 1 the owner is the host of the current session, identified
by its source IP address and UDP port together (0007, Terms; Resolved 4). A host MUST send all
its C&C packets of one session from one UDP source port (0007, Consequences, "keep one UDP
socket and port per session"). A host that reopens its socket on a new port is a different
host; its first C&C packet is a takeover (A2.4; B5.7).

A2.3 **Session.** A session starts when a host sets RUN (High Priority byte 4 bit [0]) from 0
to 1 while the radio is not in a session, or when a host takes over a running session
(A2.4). It ends when RUN is cleared, the P2 watchdog sends the radio to standby, another host
takes over, the link goes down or below 100 Mbit/s (B5.8), a firmware update starts (A1.8),
the level changes (A2.5), or the radio resets (0007, Terms; 0022 §3, §10, §16). Ownership
starts only in these two ways; no memory-mapped packet makes a host the owner (B4.5).

A2.4 **Takeover.** Takeover by another host MUST be allowed at any time (0007, Decision 3;
Resolved 1). A takeover is the first C&C packet (B5.6) from a host that is not the owner
while a level-1 session runs. The G7250 MUST handle it in this order (0022 §3):

1. End the old session with the actions of A3.2 in their order: unkey, drop the arm
   (`TAKEOVER`), issue a new token, send a last `TX_ARM_STATE` to the old owner. Then the
   TX-side state of A3.6 applies: PA off, SEND and TUNER released, ATU tuning aborted,
   session limits back to the persistent values (A3.4), `TX_MODE_CLASS` = 0,
   `KEYED_TIMEOUT` = 500 ms, hardware-timer value "no General packet yet" (B5.6). Nothing
   more is sent to the old owner.
2. Make the new host the owner and start its session at once. RUN stays set, so the new
   owner's watchdog runs from this packet.
3. Send every stream of the session (B2.4) to the new owner's source IP address and port from
   the next packet on; all outgoing sequence counters restart at 0 (B2.7).
4. Keep the RX-side settings (DDC0 frequency, rate and enable; front end) until the new owner
   writes them. The capability record is sent once, unasked, at the new owner's first General
   packet (B4.4).
5. Process the takeover packet itself.

The new owner starts unarmed. Two hosts that both send C&C take the radio from each other at
every packet ("ping-pong"); each takeover unkeys and disarms, so neither can transmit. The
G7250 counts takeovers (`GET_STATS`) and logs them, at most one log entry per second per pair
of hosts, with a count (0022 §3). Hosts SHOULD warn the user before taking over a radio that
reports 0x03 in discovery byte 4 ([P2] Discovery reply byte 4 NOTE; 0007, Resolved 5). There
is no radio-side protection against an auto-connecting host on level 1 (0007, Resolved 5).

A2.5 **Active level.** The active level MUST be visible in management identification (A1.5,
I-4) and, on level 1, in the capability record field `level` (B4; 0003) (0011 point 2). While
level 2 is active port 7250 has no socket, so the record cannot be read; a P2 host learns that
the radio is in use from discovery byte 4 = 0x03 (0003, Resolved) and the active level from
management identification (0022 §18). The default level at power-on and a level switch are
set over the management channel (A1.6, C-2). A change of active level MUST drop the arm
(`LEVEL_CHANGE`, 0007 drop event 10), and an arm is accepted only while level 1 is active
(0007 rule 1). While level 2 is active a P2 host MUST NOT be able to take the RF chain: the
P2 C&C ports have no socket on level 2, a P2 C&C packet starts no session and no takeover,
and the level changes only through the management channel (0021 §16; 0020 §25; 0008, Socket
budget; Annex X1, D23).

A2.5a **Level switch procedure.** `SWITCH_LEVEL` MUST be carried out in this order (0022 §9):

1. Validate: unknown target, status 48; level 2 not in this firmware (before G6), status 56;
   target already active, status 0 and no change; firmware update in progress, status 35.
2. Reply with status 1 (accepted, in progress).
3. If TX is armed or keyed: unkey, disarm (`LEVEL_CHANGE`), new token, push `TX_ARM_STATE`
   to the owner (level 1: from port 7250, before it closes; level 2: part C).
4. Stop all streams of the old level and end its session with the state of A3.6.
5. Log the change with the source address (A1.7).
6. Close the old level's sockets: on 1→2 the P2 sockets 1025, 1026, 1027, 1029, 1035 and 7250;
   on 2→1 the TCI listener and its connections. Ports 1024 and 7251 stay open (B3.1; A1.2).
7. Open the new level's sockets. The new level is active with no session; identification
   (I-4) shows it, and on level 1 the record field `level`.

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
| 8 | Ethernet link down, or renegotiated below 100 Mbit/s, if the CH394Q reports it (HIS-14; B5.8; 0022 §16) | `LINK_DOWN` |
| 9 | Loss of the socket or port set-up the session uses (for example a new address by Set IP, B3.9; General packet port moves are not honoured, B2.3) | `SESSION_CHANGED` |
| 10 | Change of active level (A2.5) | `LEVEL_CHANGE` |
| 11 | Start of a firmware update or of a configuration change of limits over the management channel (A1.8) | `MAINTENANCE` |
| 12 | New Discovery from the owner while armed | `REDISCOVERY` |
| 13 | A TX path that must be blocked is found not blocked (A3.7) | `FAULT` |

The numeric reason codes are in B8.7, Table B8-3 (0020 §8).

Not drop events (they end the transmission but keep the arm): the keyed timeout and TX IQ
underrun (B10.5), maximum continuous TX time and other `UNKEY`-level limit trips, a retune
while keyed that needs an RF-path change (A3.9), and General byte 58 bit [0] cleared while
keyed (B10.10); changes of frequency, antenna, filters or drive while not keyed (0007 rule 5;
0022 §1, §14).

A3.3 **Limit actions**, in increasing order (0007, Decision 4):

- `WARN`: flag in `TX_STATE`, no effect on TX;
- `REDUCE`: the radio lowers drive below the host's drive level; TX continues; the host's
  value is not changed (0007 rule 4). For forward power and supply voltage, drive is lowered
  until the value is back inside the limit; for SWR and PA temperature, forward power is
  capped at a fixed value (A3.4a) (0022 §7);
- `UNKEY`: ends the current transmission; a new 0→1 TX request is needed; arm kept;
- `DISARM`: unkey and drop the arm;
- `FAULT`: unkey, drop the arm, enter the fault state (A3.5).

A3.4 **Limits.** Each limit has a built-in value, an action and a recovery rule (Table A3-2).
Rules (0007, Decision 4, rules 1–5):

1. **Tiers.** Each limit has a built-in value (firmware, HIS-12; never writable), a
   persistent value (management configuration C-3, A1.6; equal to the built-in value unless
   tightened) and a session value (P2 `LIMIT_<name>` register, B8; or its TCI equivalent,
   part C). Each tier is at least as strict as the one above it. The **limit in force** is
   the strictest of the three; it is the only value that acts (0022 §6; 0007 rules 1–2; 0008
   C-3).
2. A limit that a host may change has a `LIMIT_<name>` register (B8, Table B8-2). A session
   write MUST be accepted only if it is equal to or stricter than the persistent value; a
   looser write MUST be rejected (not clamped) with `LOOSER_LIMIT`. Writing 0 and the end of
   the session return the session value to the persistent value. A persistent change (C-3)
   while armed drops the arm (`MAINTENANCE`) and then applies at once; a session value looser
   than the new persistent value is replaced by it (0022 §6). Built-in values are not
   writable over P2; over the management channel they may only be tightened, never beyond
   the hardware rating (A1.6; HIS-12).
3. The host MUST declare a TX mode class before arming (B10.3).
4. The mapping of P2 drive level 0–255 ([P2] High Priority byte 345) to power is TBD (HIS-12).
5. All limits apply on both levels (0011). ATU tuning uses its own SWR and power profile,
   values TBD (HIS-08, HIS-12).
6. Per-session limit registers, their units and codes are in B8 (0020 §8, §10).

Table A3-2 — TX limits (0007, Decision 4; open thresholds carry their HIS id; timing values from 0020 §29)

| Limit | Measured by | Threshold(s) | Action | Recovery |
|-------|-------------|--------------|--------|----------|
| TX frequency | DUC0 frequency ([P2] High Priority bytes 329–332); carrier only (A3.4b) | outside the transmit ranges of [G7250-MAN] for the configured region (A1.6 C-6; 0020 §23) | not keyed: TX request ignored (no key); keyed: `UNKEY` before the new frequency applies (A3.9; 0022 §1) | inside a range again; next TX request |
| SWR | forward and reflected power (HIS-11) | above S1: `REDUCE` (cap `P_swr`, A3.4a); above S2: `UNKEY`; both evaluated only above the minimum forward power `P_min`; S1, S2, `P_min` TBD (HIS-11, HIS-12) | as listed | cap held until unkey; `UNKEY`: next TX request; 3 `UNKEY` trips within 10 s → `FAULT` `SWR_REPEATED`, class 1 (0020 §29; 0022 §5) |
| PA temperature | PA sensor (HIS-11), filtered (A3.4a) | T1 `WARN`, T2 `REDUCE` (cap `P_temp`, A3.4a), T3 `UNKEY` with inhibit, T4 `FAULT` `PA_OVERTEMP`; all TBD (HIS-11, HIS-12) | as listed | cap lifts below T2 minus hysteresis; inhibit lifts below T3 minus hysteresis; hysteresis TBD (HIS-11, HIS-12) |
| Forward power | forward power (HIS-11): PEP and 100 ms mean (A3.4c), vs band and TX mode class | 100 W PEP SSB/CW/NFM; AM 25 W carrier (100 ms mean) and 100 W PEP [G7250-MAN]; 50 MHz TBD (90 W in [G7250-PUDX], [G7250-RIGPIX]; HIS-12); margin TBD (HIS-12) | `REDUCE`; if still over 200 ms after `REDUCE` started, `UNKEY` (0020 §29) | next TX request |
| Supply voltage | supply sensor (HIS-11) | starting values 13.8 V ±15 % (11.73–15.87 V) [G7250-MAN]; final HIS-11, HIS-12 | under-voltage while keyed: `REDUCE`, below a lower value (HIS-12) `UNKEY`; over-voltage: `UNKEY` with inhibit | inside range for 2 s (0020 §29) |
| Supply / PA current | current sensor, if any (HIS-11) | above 23 A [G7250-MAN]; final HIS-12 | `UNKEY` | next TX request |
| Maximum continuous TX time | firmware timer, any TX source | 5 min built-in (0007, Resolved 3); may be set stricter, never looser; to be checked against the thermal rating (HIS-12) | `UNKEY` (arm kept) | next TX request |
| ATU tune time | firmware timer | initial tuning ≤ 10 s [G7250-MAN] plus margin TBD (HIS-08) | `UNKEY`, tune reported failed | next tune command |
| Sensor plausibility | all of the above | sensor missing, stuck or out of range (HIS-11) | `FAULT` | A3.5 |
| RF while not keyed | forward power (HIS-11) | above a threshold TBD (HIS-11) with no TX active | `FAULT` | A3.5 |

The limit ids and their symbolic names (`LIMIT_TX_FREQ` … `LIMIT_RF_NOT_KEYED`) are in Table
B8-3. Only maximum continuous TX time, forward power, SWR and PA temperature are host-tunable
(Table B8-2); the others have no `LIMIT_<name>` register (0022 §19).

A3.4a **Fold-back caps** (0022 §7). For SWR above S1 the safety core MUST cap forward power at
a fixed value `P_swr`, TBD (HIS-12), and hold the cap until the unkey, even if SWR falls below
S1 again; the next transmission starts uncapped. `P_swr` MUST be above `P_min`, so that SWR
stays measurable while capped (HIS-11, HIS-12). For PA temperature at or above T2 the safety
core MUST cap forward power at a fixed value `P_temp`, TBD (HIS-12), and lift the cap below T2
minus the hysteresis; the temperature is filtered with a time constant of seconds,
TBD (HIS-11, HIS-12), and the cap may change during a transmission.

A3.4b **TX range check is on the carrier** (known limit, 0022 §20). The range check uses the
DUC0 frequency only. The occupied bandwidth of the signal can extend beyond a range edge;
keeping the signal inside the band is the host's and the operator's duty.

A3.4c **Forward power measurement** (0022 §17). The safety core measures forward power at the
PA coupler (HIS-11) as the mean over a sliding 100 ms window and as the peak envelope power
(PEP) over the same window. The 100 W limit of SSB, CW and FM applies to PEP; the 25 W AM
limit [G7250-MAN] is carrier power and applies to the 100 ms mean, with PEP also held to
100 W. If the detector cannot give PEP (HIS-11), the mean is used for every class.

A3.5 **Fault state** (0007, Decision 5):

- **Classes.** Class 1, host-clearable: limit faults with a measurable condition (temperature
  T4, repeated SWR trips) and a processor watchdog reset seen at start-up. Class 2, latched
  until reset: sensor failure, RF while not keyed, a TX path not blocked, a failed start-up
  self-test, internal consistency errors. The class of every fault code is in Table B8-3
  (0022 §5).
- **Entry.** Any `FAULT` action of Table A3-2, 3 SWR `UNKEY` trips within 10 s (the only
  repeated-trip rule; 0020 §29), drop event 13, a processor watchdog reset seen at start-up
  (HIS-13), a failed start-up self-test, or an internal error (0022 §5).
- **Effect.** Unkey, drop the arm (`FAULT`), release SEND and the TUNER trigger, refuse arm
  requests. RX MUST continue, so that the host can still see the radio and the fault.
- **Reporting.** `SAFETY_STATE`, `FAULT_CODE` (first cause), `FAULT_FLAGS` (latched bitmask
  since the last clear), `FAULT_CLASS` (the highest class among the codes set in
  `FAULT_FLAGS`, 0022 §5) and `TRIP_COUNT`, pushed on change (B8; codes 0020 §8) and logged
  (A1.7). The P2 High Priority status packet stays standard (0005; B9.2).
- **Clearing.** The owner writes the current fault code to `FAULT_CLEAR`. The clear MUST
  succeed only if every code set in `FAULT_FLAGS` is class 1 and its condition is gone; it
  then clears all flags. Otherwise it MUST be rejected with `WRITE_STATUS` reason
  `NOT_CLEARABLE` and nothing is cleared (0022 §5). "Condition gone": for `SWR_REPEATED` the
  radio is unkeyed; for `PA_OVERTEMP` the temperature is below T4 minus the hysteresis,
  TBD (HIS-11, HIS-12); for `WDT_RESET_AT_START` always (the clear acknowledges a past event).
  Class 2: only by a reset (power cycle, or `RESTART` over the management channel). The G7250
  MUST NOT reset itself to clear a fault. A clear MUST NOT re-arm. A class 2 fault is not
  stored across a reset; the start-up self-check detects a persistent cause again and keeps
  the radio in fault, RX only, and the fault is logged (0007, Resolved 9; 0022 §5).

A3.6 **State after power-on, any reset, and every session end** (0007, Decision 5): PA and
its bias off, TX path disabled, SEND and TUNER trigger released (HIS-09, HIS-10, HIS-13); not
armed, new token, session limits back to the persistent values (A3.4; after a reset the
persistent values are read from the stored configuration), `TX_MODE_CLASS` = 0,
`KEYED_TIMEOUT` = 500 ms, watchdog counted as enabled; ATU not tuning, ATU in or out
as stored per band, or out until the HIS says otherwise (HIS-08); antenna default TBD
(HIS-06); filters for the default RX frequency, preamplifier off, attenuation TBD (HIS-07).
At a takeover only the TX-side part applies; RX-side settings are kept for the new owner
(A2.4; 0022 §3).
What the hardware does between reset and the moment the firmware drives these pins is
HIS-13; if the PA can key from floating lines, M4 waits for a mitigation (0007).

A3.7 **Other TX paths.** "While level 1 runs" means: level 1 is the active level, with or
without a P2 session (0022 §15). Local inputs (controller microphone PTT, KEY) MUST be
reported and MUST NOT key the radio by themselves on level 1; the controller has no
standalone operation while level 1 runs (0007, Decision 6; Resolved 6). A controller request
that reaches the main unit (HIS-17) is not a TX request for the arm, does not start a session
and does not block an arm (0022 §15). SEND, the TUNER trigger and internal ATU tuning are
under the arm (B10.9). Controller TX functions (ATU key, SWR scan) are refused while level 1
runs unless they reach the main unit as reportable requests (HIS-17). If a path cannot be
blocked, M4 is blocked for that path until ON8ST decides (HIS-10, HIS-17; 0007, Decision 6).

A3.8 **Management** never keys the radio, arms it or loosens a limit; it may unkey and
disarm in the order of A3.2 (A1.9; 0022 §8).

A3.9 **Changes while keyed** (level-independent; 0022 §1, §2).

- **TX frequency.** While keyed, the G7250 MUST evaluate every new DUC0 frequency before
  applying it. If it lies outside the transmit ranges in force, or needs another TX filter,
  band or relay state than the one in use, the G7250 MUST unkey first (`UNKEY`, arm kept;
  `TX_STATE` unkey reason 6, or reason 4 with limit id `LIMIT_TX_FREQ` when the cause is the
  range), then apply the frequency and switch relays while unkeyed; keying again needs a new
  0→1 TX request. A retune inside the same transmit range that needs no change of filter,
  band or relay state MUST be followed while keyed, without unkey. Which frequencies share
  one RF-path state is the filter plan: TBD (HIS-07); until it is known, each `tx_band` entry
  of the record (B4.8) counts as its own state.
- **RF-path relays** (antenna, ATU in/out, TX and RX filters, preamplifier, attenuator) MUST
  NOT change while keyed, whatever the source. A change requested through a P2 state field
  that the host resends (High Priority and DUC-specific packets) is deferred: the latest
  value is applied right after the unkey, before any new key. A change requested by a
  command is refused: a register write is answered with the value in force and
  `WRITE_STATUS` reason `KEYED`; a TCI command as in part C (0021 §8); a controller ANT or ATU
  button press that reaches the main unit ([G7250-MAN]; HIS-17) is ignored and logged.
  Management switches no relay (A1.9). The only exception is internal ATU tuning inside its
  own tune profile (0007 Decision 4 rule 5). A controller that switches relays by itself is a
  finding for HIS-10 and HIS-17.

A3.10 **Safety timing is independent of load** (0022 §16). The watchdog, the keyed timeout,
limit actions and arm drops MUST meet their timing under any received packet load the link
can carry. Load MAY cause the owner's packets to be lost and so an unkey or a watchdog stop
(the safe direction); it MUST NOT delay an unkey.

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

B1.8 **Scope of this draft.** B1–B6 cover M1. B7–B11 are complete; the only open values
depend on the hardware and carry their HIS id (0020, Context). Wideband data is M2 (0004
point 4); transmit (B10) is M4 and only after M3 (design note §6; 0007, header).

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
| 7 | 7250 | G7250 register map (memory-mapped registers from PC) | G7250 register map (memory-mapped registers from hardware) | MUST be open | [P2] General bytes 29–32; 0005; 0020 §1 |
| 8 | 7251 | Management channel | Management channel | MUST be open, at both levels | 0008, Transport 1; 0020 §2 |

- Ports 1036 and up (DDC1 and further, [P2] General bytes 17–18) are not opened while the
  G7250 implements one DDC (0004 point 1). Number of DDCs: TBD (HIS-02).
- **Memory-mapped register port.** [P2] gives the default of General bytes 29–30 and 31–32 as
  "xxxx", so it is undefined; this document defines it (0005; 0003, "left to spec part B").
  The port number is 7250 (0020 §1). The G7250 MUST use one and the same local port for both
  directions (0005, Consequences; 0017). Using a defined default is a deviation (Annex X1, D2).
- **Port 1028.** The G7250 opens no socket on port 1028 (0017). A host SHOULD NOT send DDC
  audio packets. The G7250 accepts General packet bytes 13–14 and ignores them (0017). How
  the CH394Q reacts to a datagram for a closed port is not stated in [CH394]; the firmware
  rule and the host rule are in B11.9 (0020 §28). This is a deviation (Annex X1, D1).
- **Non-default ports.** [P2] lets the host set every port in General bytes 5–22 and 29–32,
  zero meaning the default. Bytes 5–12, 15–22 and 29–30 name G7250 local ports ([P2] General
  packet). For these, zero and the default value MUST be honoured; any other value MUST NOT be
  honoured: the G7250 keeps the default port, logs the request and sets `LINK_STATUS` bit 17
  (0020 §13; Annex X1, D22). Reason: the default set shares sockets between pairs of fields,
  so a single relocation would need a ninth socket (0020 §13;
  `analysis/ch394-network-budget.md`). In particular no P2 port is ever moved onto the
  management port (A1.3; 0008, Transport 2). Bytes 31–32 name the host's destination port and
  are honoured when non-zero; zero means the owner's source port (B8.1; 0020 §13). A host
  SHOULD send zero in bytes 5–30 (0020 §13).
- **Socket budget.** Table B2-1 uses all 8 CH394Q sockets: 7 for G7250-P2, one for the
  management channel (0008, Socket budget; 0017; [CH394]). The division of the 16 + 16 KB
  socket buffers: TBD (HIS-14); indicative split in 0004, Consequences, "CH394Q buffer split".

B2.4 **Remote endpoint.** The G7250 MUST reply to the discovery from local port 1024 to the
IP address and source port of the host's discovery packet ([P2] "Detailed operation";
Discovery reply, "Source Port", "Destination Port"). The G7250 MUST send every stream of a
session (DDC0 I&Q, High Priority status, microphone, wideband and register pushes) to the
owner's source IP address and UDP port (A2.2), fixed when the session starts (at a takeover:
the new owner's, A2.4). This is the one destination rule; register packets go to General
bytes 31–32 at the owner's IP address when those are non-zero (B8.1; 0020 §13; 0022 §12).
[P2] sends the status, microphone and wideband streams to "the Source Port of the Host that
initiated the Discovery Packet" and DDC I&Q to "the Source Port of the Host that initiated
the Discovery Command", and has the host send its General packet from that same port ([P2]
High Priority Status, Microphone, Wideband and DDC packets, "Destination Port"; General
packet, "Source Port"), so for a P2 host both are one port; where they differ, the owner's
port is used (0020 §14; Annex X2, C12). Answers to a non-owner's register request go to that
request's source address and port (B8.5).

B2.4a **Local source ports.** So that a host can demultiplex by sender port, the G7250 MUST
send: discovery replies from 1024, High Priority status from 1025, microphone data from 1026,
wideband data from 1027, DDC0 I&Q from 1035, register-map packets from 7250 and management
replies from 7251 (Table B2-1; 0020 §14).

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
"Sequence Number"). The counter MUST be reset to zero at power-on, whenever a stop is
received (B5.4), and at a takeover (A2.4) ([P2] DDC packet, "Sequence Number"; 0022 §3).
Exception, as [P2] specifies: the wideband counter restarts at 0 for every frame, so the 8
packets of a frame carry 0–7 ([P2] Wideband Data packet, pp. 52–53: "set to zero … whenever a
block of raw samples has been sent"; B6.10; Annex X2, C16; 0022 §21). The discovery reply
always carries sequence number 0 ([P2] Discovery reply bytes 0–3). On the receive side the
G7250 SHOULD NOT reject or reorder a packet because of its sequence number ([P2] Discovery,
Erase, Set IP, General, DDC-specific, DUC-specific and High Priority packets give the host's
sequence number as 0x00000000, Annex X2, C2; 0020 §19; 0022 §21). A DDC0 rate change, a
resume after a refusal, or a resume after DDC-specific byte 7 bit [0] was cleared MUST NOT
restart an outgoing counter (0020 §19). Gaps are handled in B11.6.

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
- SHOULD NOT require bytes 0–3 or 5–59 to be zero, nor the packet to be longer than 5
  bytes, to answer (B11.3; 0020 §28);
- MUST answer every request with exactly one reply, within the rate limit of B11.14: at
  most 10 replies per second per source IP address and port and 50 per second in total;
  requests above it are dropped and counted (0022 §16).

A discovery from the owner (same IP address and UDP port, A2.2) while TX is armed drops the
arm (`REDISCOVERY`, Table A3-1 event 12). A discovery from any other host has no effect on the
session. This includes a discovery from the owner's IP address on another UDP port, for
example a host's separate discovery socket: it is answered with 0x03 while the session runs
(B3.4) and MUST NOT drop the arm (0020 §14; 0007, Resolved 4; [AETHER-SRC]
`AnanDiscovery.cpp:240–263`).

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
  is in `fw_version` (B4). G7250 releases are numbered major.minor with minor 0–9 (after x.9
  comes (x+1).0) plus a 16-bit build number; byte 13 = major × 10 + minor, capped at 255
  (0020 §15). Byte 23 is non-zero for a beta build ([P2] byte 23).

B3.6 **MAC address.** Bytes 5–10 MUST hold the MAC address the G7250 uses on the link, MSB
first ([P2] Discovery reply, "MAC"). The MAC address MUST be unique per unit, because the
host uses it to tell radios apart and to address Set IP packets ([P2] Set IP Address packet).
The record carries no serial number; the MAC suffices (0003, Resolved). Where it is stored
and whether it is unique per unit: TBD (HIS-15).

B3.7 **Endian modes and DDC data format (byte 22).** The G7250 offers only Big-Endian with
3-byte I&Q: no little-endian, float or double format (0004 point 1, option 2A). Byte 22 MUST
therefore be 0x00, which [P2] defines as "Big-Endian and I&Q data is in 3 Byte format" ([P2]
Discovery reply byte 22). A General packet byte 39 that asks for another format is refused
(B6.3; B11.2).

B3.8 **Frequency or phase word (byte 21).** The value MUST match what the G7250 accepts in the
High Priority frequency fields ([P2] High Priority packet bytes 9–12, 329–332) and in General
packet byte 37 bit [3]. If the G7250 reports phase (1), the host computes
`phase_word = 2^32 × f(Hz) / DSP clock (Hz)` ([P2] General packet byte 37); the DSP clock is
given in record field `dsp_clock_hz` (0003 §3; Annex X2, C4). Value and DSP clock: TBD (HIS-04).

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
  ([P2] Set IP Address packet, "MAC Address"). A Set IP sent to the unit's unicast address or
  to the subnet's directed broadcast address MUST be accepted under the same rules (0020 §21;
  Annex X2, C13). Risk stated in 0008 S7: any host on the LAN that knows the MAC can change
  the address and so cut a running session; it cannot key the radio.

### B4 Capability block

B4.1 **Form.** The capability block is a **capability record**: a read-only range of the
G7250 register map (B8), sent by the G7250 in standard [P2] "Memory mapped registers from
hardware" packets (0003, Decision option A). It is not in the discovery reply (0003 §1).

B4.2 **Place.** The record occupies `CAP_BASE` to `CAP_BASE + CAP_LENGTH − 1`, at most 239
registers, so that one memory-mapped packet (240 pairs [P2]) carries the request echo plus the
whole record and a host always sees one consistent copy (0003 §2). `CAP_BASE` = 0x0000
(0003 §2; 0020 §3): the version 1.1 record occupies 0x0000–0x00CE, and the block
0x0000–0x00FF is reserved for it (B8.3).

B4.3 **Encoding.** One field per 32-bit register, big-endian ([P2] memory-mapped packets, Data
[31:0]; 0003 §2). Text is ASCII, 4 characters per register, first character in bits [31:24],
padded with 0x00. Frequencies in Hz. Power in units of 0.1 W. Bit numbers: 0 = LSB (0003 §2,
§3).

B4.4 **When the record is sent** (0003 §2):

1. **On request.** The host writes 0x00000001 to the register `CAP_REQUEST` (0x0100, B8;
   0020 §3, §5). The G7250 MUST answer with one memory-mapped packet that holds the echo of
   the `CAP_REQUEST` pair and the whole record. Any other value MUST be rejected with
   `WRITE_STATUS` reason `BAD_VALUE` and no record (B8.4; 0020 §5).
2. **Unasked, once,** when a host starts a session, which 0003 places at the host's first
   General packet.
3. **Destination.** To the source IP address and UDP port of the request when the requesting
   host is not the owner (has no session); otherwise to the owner's memory-mapped port set in
   General packet bytes 31–32, or to the owner's source port (A2.2) if those bytes are zero
   ([P2] General packet bytes 31–32; 0003 §2; 0020 §13). Answers to a host that is not the
   owner are rate-limited: at most once per 1 s per source IP address and port and 10 per
   second in total; requests above that are dropped and counted (B11.14; 0022 §16).

B4.5 **Request-only packet is not C&C.** A memory-mapped packet that contains only a write to
`CAP_REQUEST` MUST NOT take over a session, MUST NOT start one, and MUST NOT feed the watchdog
(0003 §2; Resolved). More generally, no memory-mapped packet is C&C on the G7250 (B5.6; 0007
sub-decision 2.1). This holds also when a host sends the request from its future session
socket before its first General packet: the answer goes to that socket, and the port does not
become the owner; only the run bit (while no session runs) or a takeover by a C&C packet makes
a host the owner (A2.3, A2.4; 0020 §14; 0022 §3). Listed in Annex X1, D11.

B4.6 **Read-only.** Writes to any address in the record range MUST be ignored, and the G7250
MUST answer with the current values of the addresses written, so that the host sees that the
write had no effect (0003 §2), plus `WRITE_STATUS` reason `READ_ONLY` (B8.4; 0020 §11). The
pair (0x0000, 0x00000000) is padding and is not answered (B8.1; 0020 §4).

B4.7 **Stability.** Record values MUST be constant for the duration of a session. They MAY
change only between sessions: after a firmware update, a region change of the TX bands, a
change of the active level, a new per-unit calibration, or a change of link speed (0003 §2).
Dynamic state is not in the record: TX armed, fault state and limits in force, telemetry
values, current link speed and session refusal reason are separate status registers (B8;
0003 §2).

B4.8 **Fields, record version 1.1.** Offsets are relative to `CAP_BASE`. "HIS-nn" means the
value is not known yet; the value shown is the current assumption (0003 §3). Offsets
0x00–0xB8 are version 1.0 (0003 §3); offsets 0xB9–0xCE are added by version 1.1 (B4.9; 0020
§26). The G7250 sends version 1.1.

Table B4-1 — Capability record, version 1.1 (0003 §3; 0020 §26)

| Offset | Name | Content | Value / source |
|--------|------|---------|----------------|
| 0x00 | `cap_magic` | ASCII "G725" = 0x47373235; never changes | 0003 §3, §4 rule 5 |
| 0x01 | `cap_version` | [31:16] major, [15:0] minor of the record format | 0x00010001 (1.1) (0020 §26) |
| 0x02 | `cap_length` | number of registers in the record, header included | 0xCF (207) for version 1.1; 0xB9 (185) was version 1.0 (0003 §3, notes; 0020 §26) |
| 0x03 | `regmap_version` | [31:16] major, [15:0] minor of the G7250 register map | 0x00010000 (1.0) (0020 §6) |
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
| 0x52 | `mgmt` | bit 0 management channel present; [31:16] its port | 0x1C530001: bit 0 = 1 (0008), port 7251 (A1.3; 0020 §2) |
| 0x53 | `regmap_groups` | bit mask of register groups present in the G7250 map | bit *n* = group *n* of Table B8-1: bits 0, 1 = 1; bit 2 from M3; bit 3 per HIS-11; bit 4 per HIS-08; bit 5 per HIS-06; bits 6, 7 = 0 until HIS-07, HIS-09 (B8.3; 0020 §3) |
| 0x54 | `link` | [15:0] minimum link speed in Mbit/s for a session | 100 (0004 point 9; [CH394]) |
| 0x55 | `wb_format` | wideband: [31:16] samples per packet, [15:8] bits per sample, [7:0] update rate in ms; 0 when `streams` bit 4 = 0 | from M2: 0x02001032 (512, 16, 50 ms; 0004 point 4) |
| 0x56 | `wb_frame` | wideband: [7:0] packets per frame; 0 when `streams` bit 4 = 0 | from M2: 8 (0004 point 4) |
| 0x57 | `cal_info` | bit 0 power constants per band (set *i* applies to `tx_band[i]`; else set 0 applies to all bands); bits 1–4 forward power, reverse power, exciter power, supply volts filled; [15:8] number of power constant sets (1, or `tx_band_count`); [31:16] ADC full-scale divisor *N* | 0006; per unit and per band HIS-11; *N* = 4095 in [P2] Appendix A |
| 0x58 | `cal_supply_c` | supply constant *c* in units of 10⁻⁶, for `V = x / N × c` | this unit's calibration (0006; HIS-11) |
| 0x59–0xB8 | `cal_power[0..15]` | 6 registers per set, units of 10⁻⁶: forward *c1*, *c2*; reverse *c1*, *c2*; exciter *c1*, *c2*, for `W = (x / N × c1)² / c2` | this unit's calibration (0006; HIS-11); unused sets 0 |
| 0xB9 | `status_fill` | High Priority status fields filled: bit 0 byte 4 [0]; bit 1 byte 4 [1]–[2]; bit 2 byte 4 [4]; bit 3 byte 5; bit 4 bytes 6–7; bit 5 bytes 14–15; bit 6 bytes 22–23; bit 7 byte 30; bit 8 bytes 31–36; bit 9 bytes 39–40; bit 10 bytes 49–50 | per Table B9-1 (0006; 0020 §26); HIS-11, HIS-17 |
| 0xBA | `clock_ref` | bit 0 reference PLL present; 0 means "no reference PLL" and status byte 4 [4] is always 0 | HIS-05 (0020 §26) |
| 0xBB | `coupler` | [3:0] coupler position: 0 not reported, 1 between PA and ATU, 2 antenna side of the ATU | HIS-08, HIS-11 (0006; 0020 §26) |
| 0xBC | `tlm_rates` | [31:16] snapshot period, ms; [15:8] fast period during TX, ms; [7:0] minimum spacing of event pushes, ms | 1000, 10, 1 (B9.4; 0006; 0020 §26) |
| 0xBD | `status_rates` | [31:16] High Priority status period when not transmitting, ms; [15:0] while transmitting, ms | 50, 1 (B9.4; 0020 §26) |
| 0xBE | `tlm_count` | number of valid telemetry descriptors (max 8) | HIS-11 (0020 §26) |
| 0xBF–0xCE | `tlm_desc[0..7]` | 2 registers each: [31:16] telemetry register address, [15:0] sensor update period in ms; [31:16] resolution, [15:0] hysteresis, both in the register's milli-units; a register is present when it has a descriptor | HIS-11 (0006; 0020 §26); unused entries 0 |

Notes (0003 §3):

- Transmit-power values are the nominal maxima in the configured region, not the limits in
  force; limits in force are status (B8; A3.4).
- Fields with an Appendix C counterpart (`num_adc` byte 36, `num_ddc` byte 39, `dsp_clock_hz`
  bytes 27–30, DDC audio byte 59, microphone byte 72, DUC rate and format bytes 79–80) have the
  same meaning as there ([P2] Appendix C).
- `streams` bit 2 and `num_ddc` MUST agree with what the radio does: no socket on port 1028
  (0017), and only as many DDC I&Q ports as `num_ddc`.
- The record carries no serial number (0003, Resolved).

B4.9 **Fields added in version 1.1.** 0006 ("What the host learns from the capability block")
asks the record to also state: for each standard status field whether it is filled
(`status_fill`); the coupler position relative to the ATU (`coupler`); for each telemetry
register presence, resolution, sensor update rate and hysteresis (`tlm_count`, `tlm_desc`);
the telemetry rates in use (`tlm_rates`, `status_rates`); and "no reference PLL"
(`clock_ref`; B9.2, byte 4 bit [4]). Version 1.0 (0003 §3) covered only part of this
(`telemetry`, `cal_info`). Version 1.1 adds these fields at the end of the record (0003 §4
rule 1; 0020 §26); a version 1.0 host ignores them (B4.10 rule 1).

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
HIS-07). A discovery is not a precondition: a run bit from a host that sent no discovery
starts the session normally, and the streams go to that host's source address and port
(B2.4; [P2] "Detailed operation", restart path; 0020 §14).

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

- **C&C packets.** C&C packets are the four packets headed "Control Elements - PC to
  Hardware" in [P2]: General, DDC-specific, DUC-specific and High Priority (0007 sub-decision
  2.1; Annex X2, C6; 0022 §21).
  Memory-mapped register packets are not C&C: they MUST NOT feed the watchdog (0007 sub-decision
  2.1 and Resolved 8; 0003, Resolved) and MUST NOT cause a takeover (B5.7). Packets from hosts
  other than the owner MUST NOT feed the watchdog (0007 sub-decision 2.1).
- **Timeout.** In RUN, if no C&C packet from the owner arrives for 1 s, the G7250 MUST go to
  standby: unkey, drop the arm (`WATCHDOG`), release SEND and the TUNER trigger, and stop the
  RX streams by leaving RUN ([P2] "Detailed operation": "switch out of the RUN state into
  standby"; High Priority byte 4 bit [0]; 0007 sub-decision 2.1; 0022 §21). The host
  SHOULD send a C&C packet every 100 ms ([P2] "Detailed operation"). Tolerance: the G7250
  MUST NOT go to standby while the last C&C packet from the owner is less than 1000 ms old,
  and MUST be in standby no later than 1100 ms after it (0020 §16).
- **Hardware-timer bit** (General packet byte 38 bit [0]) (0007 Decision 2.3, option 2F):
  - the G7250 MUST store the value last written; the effective timer is
    `written OR armed`;
  - while not armed, the bit MUST be honoured as [P2] specifies ([P2] General packet byte 38);
  - while armed, a clear MUST NOT disable the timer; the clear takes effect again after
    disarm (0015; Annex X1, D4);
  - an arm request while the written bit is clear MUST be rejected (`WATCHDOG_DISABLED`,
    B10.2);
  - before any General packet the timer counts as enabled, but an arm is rejected with
    `WATCHDOG_DISABLED` until the owner has sent, in this session, a General packet that the
    G7250 acted on (not discarded as short, B11.3) with bit [0] set; a General packet with
    refused fields (for example byte 39) still counts for byte 38 (0022 §13);
  - `WATCHDOG_STATE` reports the value written and the effective state (B8; 0020 §8).
- **Keyed timeout** while transmitting: B10.5.

Note: a session with the timer disabled (allowed only while not armed) holds the radio "in
use" after its host has gone and keeps sending RX IQ to it; the next host takes over (0007,
option 2F "Against").

B5.7 **Takeover.** Takeover is always allowed and follows the ordered procedure of A2.4
(0007, Decision 3; 0022 §3): the old session ends with the A3.2 actions and a last
`TX_ARM_STATE` to the old owner; the new host becomes owner at once, RUN stays set, the
streams go to the new owner with sequence counters restarted at 0, and the new owner starts
unarmed with `TX_MODE_CLASS` = 0 and session limits at the persistent values. A host that
reopens its socket on a new UDP port takes over from itself (0007, Resolved 4). Only the arm
part deviates from [P2] ([P2] Discovery reply byte 4 NOTE; Annex X1, D5, D6).

B5.8 **Link below 100 Mbit/s.** On a link slower than 100 Mbit/s the G7250 MUST refuse the
session: it answers discovery but starts no stream (no DDC0, DUC0, microphone or wideband data),
and reports the reason ("link speed below 100 Mbit/s") in a status register (`LINK_STATUS`,
B8) (0004 point 9; Resolved). The record field `link` gives the minimum speed (B4.8; 0003 §3).
On such a link a run bit makes no owner and starts no stream, and no High Priority status
packet is sent. The G7250 MUST answer each High Priority packet with the run bit set, and each
`CAP_REQUEST`, with a register packet holding `LINK_STATUS` (refusal reason 1) and
`STREAM_STATUS` (reason 8), to the sender, at most once per 100 ms (0020 §20). The speed is
read from the CH394Q PHY configuration register PHY_CFG, bits SPDS (speed) and LINKS (link
up) ([CH394] section 7.1.15); whether the existing design leaves that register
usable: TBD (HIS-14). Annex X1, D15. If the link goes down or renegotiates below 100 Mbit/s
during a session, the session MUST end: unkey, disarm (`LINK_DOWN`, Table A3-1 event 8),
streams stop, and `LINK_STATUS` gives the speed and refusal reason 1. A later return to
100 Mbit/s allows a new session; nothing restarts by itself (0022 §16).

B5.9 **Transmit bit.** High Priority byte 4 bit [1] has no effect unless TX is armed (0015;
B10). Bits [2]–[7] never key the G7250 (0007 sub-decision 1 rule 4; Annex X2, C5).

### B6 Streams from the radio: RX IQ, wideband, microphone

B6.1 **Port and endpoint.** DDC0 I&Q MUST be sent from local port 1035 ([P2] General packet
bytes 17–18; DDC packet, "Source Port") to the owner's source IP address and UDP port (B2.4;
0022 §12). One DDC is
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
| 18–19 | Sampling rate DDC0, in ksps (48, 96, 192, 384) | offered rates honoured (B6.7); any other value: refused, DDC0 does not run (B6.7) | [P2] bytes 18–19; 0004 points 1, 7; unit as written by [AETHER-SRC] `P2Protocol.cpp:123–125` and [PIHPSDR] `new_protocol.c:1403–1404` (0020 §30) |
| 20–21 | CIC1, CIC2 DDC0 | ignored ("For future use" in [P2]) | [P2] bytes 20–21 |
| 22 | Sample size DDC0 | 24 honoured; 0 read as the default 24; any other value: refused, DDC0 does not run | [P2] byte 22; 0004 point 7 |
| 23–496 | ADC, rate, CIC, size DDC1–79 | ignored | [P2] bytes 23–496; 0004 point 7 |
| 1363–1442 | Sync DDC0–79 | ignored; synchronous DDCs not supported unless HIS-03 shows a second ADC | [P2] bytes 1363–1442; HIS-03 |
| 1443 | Currently not used | ignored | [P2] byte 1443 |

A change of DDC0 sampling rate to another offered rate while running SHOULD take effect
without a stop, since [P2] sends the DDC-specific packet "when a parameter changes" ([P2] DDC
specific packet, introduction). The sequence counter does not restart on a rate change, nor
when DDC0 resumes after a refusal (B2.7; 0020 §19).

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
`rx_range` (B4.8). Outside the range the G7250 MUST tune as requested, without refusal or
clamping; receiver performance there is not specified (B11.8; 0020 §28).

B6.9 **Pacing.** The G7250 SHOULD send a DDC0 packet as soon as 238 samples are available, to
keep latency low (provisional, no decision; by analogy with [P2] "Detailed operation", which
gives this advice for DUC data; the CH394Q has no flow control in UDP mode, [CH394] section
12.2.4). Overrun behaviour: B11.7 (0020 §28).

B6.10 **Wideband data (milestone M2).** (0004 point 4; option 5C; Resolved.)

- Not offered before M2: a General packet byte 23 enable MUST NOT be followed and no wideband
  packets are sent (0004 point 7). Record `streams` bit 4 = 0, `wb_format` = `wb_frame` = 0.
- From M2, for ADC0 only, out from local port 1027 ([P2] General bytes 21–22): fixed
  parameters 512 samples per packet, 16-bit samples, 8 packets per frame, one frame every 50 ms
  (4096 samples per frame, 20 frames per second), in [P2] Wideband Data packets of 1028 bytes
  (bytes 0–3 sequence number, 512 samples of 16 bits) ([P2] Wideband Data packet; General
  bytes 24–28; 0004 point 4). Stated in `wb_format` and `wb_frame` (B4.8). The sequence number
  is 0 in the first packet of every frame and 7 in the last, as [P2] specifies ([P2] Wideband
  Data packet, pp. 52–53; B2.7; 0022 §21).
- From M2, an enable for ADC0 (General byte 23 bit [0]) MUST be followed only while bytes
  24–28 are 0 or equal to the fixed values (512, 16, 50, 8). Any other value: wideband does not
  run until the request is valid, reason in `STREAM_STATUS`. Enables for other ADCs are not
  followed (0004 point 7). [P2] gives the defaults 512 samples, 16 bits, 20 ms and 32 packets,
  and lets zero select the default only for byte 26 ("If set to zero the default of 16 bits
  will be used"); byte 27 has the range "0 to 255mS" ([P2] General packet bytes 24–28). The
  G7250 reads zero in bytes 24–25, 27 and 28 as its fixed values; zero in byte 26 is the [P2]
  default 16 (Annex X1, D14; 0022 §21).
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

Per standard P2 field of the host-to-radio packets: honoured, ignored, refused, or open on a
hardware question with its HIS id (0005, Consequences). "Honoured" means as [P2] specifies (B1.4). "Ignored" means accepted with no
effect. "Refused" means the request is not followed and the stream concerned does not run,
with the reason in `STREAM_STATUS` (0004 point 7). The DDC-specific packet is in Table B6-2,
the DUC-specific packet in Table B10-1, the High Priority status packet (radio to host) in
Table B9-1.

Table B7-1 — General packet ([P2] General packet to SDR)

| Byte | Field | G7250 behaviour | Source |
|------|-------|-----------------|--------|
| 4 | Command 0x00 | honoured | [P2] byte 4 |
| 5–12, 15–22 | Port numbers | zero or the default value honoured; any other value not honoured: default kept, logged, `LINK_STATUS` bit 17 (never onto the management port) | B2.3; 0008 Transport 2; 0020 §13; Annex X1, D22 |
| 13–14 | DDC audio port | ignored | 0017 |
| 23 | Wideband enable | before M2: not followed; from M2: bit [0] per B6.10; other bits not followed | 0004 point 7 |
| 24–28 | Wideband parameters | from M2: 0 or the fixed values; otherwise refused | 0004 point 7; B6.10 |
| 29–30 | Memory-mapped port of the G7250 | zero or 7250 honoured; any other value not honoured, as bytes 5–22 | 0005; B2.3; 0020 §1, §13 |
| 31–32 | Memory-mapped destination port of the host | non-zero honoured; zero = the owner's source port | B8.1; 0020 §13 |
| 33–36 | Envelope PWM | ignored ("Reserved for future use" in [P2]) | [P2] bytes 33–36; 0005 rule 3 |
| 37 [0], [1] | Time stamp, VITA-49 | set: refused (DDC0 does not run while it stands) | 0004 point 7 |
| 37 [2] | VNA mode | set: refused (VNA not offered; DDC0 does not run while it stands; `STREAM_STATUS` reason 11) | [P2] byte 37; 0004 point 7; 0020 §22 |
| 37 [3] | Frequency or phase word | must match discovery byte 21; TBD (HIS-04) | B3.8 |
| 38 [0] | Hardware timer enable | honoured while not armed; forced on while armed; must be set to arm | 0007 Decision 2.3; B5.6 |
| 39 | Endian and I&Q format | Big-Endian 3-byte honoured; anything else refused | 0004 points 1, 7; B6.3 |
| 40–55 | Reserved | ignored | [P2]; 0005 rule 3 |
| 56, 57 | Atlas bus configuration, 10 MHz reference source | ignored (byte 56 "Atlas bus configuration"; byte 57 "For Atlas based systems this selects the source of the 10MHz reference clock" in [P2]) | [P2] bytes 56–57; 0022 §21 |
| 58 [0] | PA enable | honoured as an extra TX condition: while 0, a TX request does not key; cleared while keyed: unkey, arm kept (B10.10); `TX_STATE` bit 4; no exciter-only output | [P2] byte 58; 0005 rule 1; 0020 §22; 0022 §14 |
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
| 329–332 | DUC0 frequency / phase word | honoured; outside the TX ranges a TX request does not key; while keyed, a change that leaves the range or needs an RF-path change unkeys first (A3.9) | [P2] bytes 329–332; A3.4; 0022 §1 |
| 333–344 | DUC1–DUC3 frequency | ignored (reserved) | [P2]; 0005 rule 3 |
| 345 | DUC0 drive level 0–255 | honoured; mapping to power TBD (HIS-12); `REDUCE` acts radio-side | [P2] byte 345; 0007 rule 4 |
| 346–348 | DUC1–DUC3 drive | ignored (reserved) | [P2]; 0005 rule 3 |
| 1396–1397 | Client control word | bit [0] TUNE accepted as information; does not start the internal ATU; other bits ignored | 0007 Decision 6; 0005 rule 1 |
| 1398–1399 | CAT over TCP port | ignored; CAT stays on the host side | 0011 point 5 |
| 1400 | Transverter and audio enable | ignored (no transverter output, no audio on the main unit) | [P2] byte 1400; 0017; 0020 §22 |
| 1401 | Open-collector outputs | ignored; no such outputs [G7250-MAN] | 0007 Decision 6 |
| 1402, 1403 | Metis user outputs, Mercury attenuator | ignored (Atlas only in [P2]) | [P2] bytes 1402–1403 |
| 1404–1427 | Alex 2–7 | ignored (reserved) | [P2]; 0005 rule 3 |
| 1428–1435 | Alex 0, Alex 1 words | TBD; ignored unless HIS-06/HIS-07 show identical meaning | 0005 option D, rule 1 |
| 1436–1441 | Step attenuators 2–7 | ignored (reserved) | [P2]; 0005 rule 3 |
| 1442 | Step attenuator ADC1 | ignored unless a second ADC exists (HIS-03) | [P2] byte 1442 |
| 1443 | Step attenuator ADC0 | TBD (HIS-07; identical-meaning check, 0005 rule 1) | [P2] byte 1443 |

Fields of Tables B7-2 and B10-1 that switch an RF-path relay (Alex words, step attenuators)
are deferred while keyed and applied after the unkey (A3.9; 0022 §2).

Other host-to-radio packets: DUC I&Q (B10.7); memory-mapped registers from PC (B8); Erase,
Program, Set IP (B3.9); DDC audio (not received, B2.3).

The P2 field table is complete. Rows that still depend on the hardware carry their HIS id
and are closed when the HIS answers (0005, Consequences; 0020, Context).

### B8 G7250 register map

B8.1 **Port and packets.** The G7250 register map is carried by [P2] "Memory mapped registers
from PC" and "Memory mapped registers from hardware" packets: pairs of a 16-bit address and a
32-bit data word, bytes 4–1443 ([P2]; 0005). The G7250 uses local UDP port **7250** for both
directions (B2.3; 0005, Consequences; 0020 §1). It sends register packets to the owner's
source port, or to General packet bytes 31–32 when these are non-zero, and answers a
non-owner's request to the request's source address and port (B2.4; 0020 §13, §14).

- A packet carries *n* pairs, 1 ≤ *n* ≤ 240, and is 4 + 6*n* bytes long. The G7250 MUST send
  only the pairs it has (0020 §4). [P2] shows 240 pairs and has no count field; the shorter
  packet is the G7250 reading of [P2] (Annex X2, C15; 0022 §21).
- The G7250 MUST accept any length of at least 10 bytes and MUST ignore a trailing incomplete
  pair. Pairs with address 0xFFFF, and the pair (0x0000, 0x00000000), are padding: they MUST
  be ignored and are not answered (0020 §4).
- Incoming sequence numbers are not checked (B2.7).

B8.2 **Sending.** The G7250 sends a memory-mapped packet whenever data changes and optionally
periodically ([P2] Memory mapped registers from hardware); B9.4 gives the telemetry rates.
Register packets and High Priority status packets are not synchronised; a host MUST NOT
assume they describe the same instant (0006, Consequences).

B8.3 **Groups and addresses.** Addresses are grouped in blocks of 256; group *n* is present
when bit *n* of the record field `regmap_groups` is set (B4.8; 0003 §4 rule 6; 0020 §3).
Table B8-1 lists the groups, Table B8-2 the registers. Registers for antenna selection,
filter and front-end control and external interfaces are reserved in their blocks until the
HIS answers (HIS-06, HIS-07, HIS-09; 0005, Consequences). Addresses not listed are reserved;
a write to one is rejected (`UNKNOWN_ADDRESS`, B8.4).

Table B8-1 — Register groups (0020 §3)

| Bit in `regmap_groups` | Block | Group | Present |
|---|---|---|---|
| 0 | 0x0000–0x00FF | capability record (`CAP_BASE` = 0x0000; 0x0000–0x00EE usable, 239 registers; 0x00EF–0x00FF reserved) | always (0003 §2) |
| 1 | 0x0100–0x01FF | session and stream status, requests | always |
| 2 | 0x0200–0x02FF | TX arm, TX state, limits, faults | from M3; arm accepted only when record `tx` bit 1 = 1 (B10) |
| 3 | 0x0300–0x03FF | telemetry | when at least one sensor exists (HIS-11) |
| 4 | 0x0400–0x04FF | internal ATU | per HIS-08 |
| 5 | 0x0500–0x05FF | antenna | per HIS-06 |
| 6 | 0x0600–0x06FF | front end and filters (reserved) | 0 until HIS-07 |
| 7 | 0x0700–0x07FF | external interfaces, SEND and TUNER (reserved) | 0 until HIS-09 |
| 8–31 | 0x0800–0x1FFF | reserved for later groups | 0 |
| — | 0x2000–0xFFFE | reserved | — |
| — | 0xFFFF | padding (no operation) | — |

B8.4 **Write confirmation, rejection and ordering** (0020 §11; 0005, Consequences).

- The G7250 MUST process the pairs of a host packet in order. For each written address it
  MUST answer with the pair (address, value now in force), in one or more packets sent within
  5 ms of receipt. For `TX_ARM` the answer is `TX_ARM_STATE`; keying needs a TX-request edge
  after it (B10.2; 0007 rule 2).
- A rejected write MUST leave the value unchanged. The answer MUST carry the value in force
  and a `WRITE_STATUS` pair: [31:16] the address, [15:8] a rejection counter (wraps at 255),
  [7:0] the reason: 1 `UNKNOWN_ADDRESS` (including an address of an absent group),
  2 `READ_ONLY`, 3 `NOT_OWNER`, 4 `BAD_VALUE`, 5 `LOOSER_LIMIT`, 6 `BUSY` (update in
  progress), 7 `NOT_CLEARABLE` (fault not clearable, A3.5), 8 `KEYED` (RF-path change while
  keyed, A3.9), 9 `NOT_ARMED` (`ATU_TUNE` without arm, B10.9) (0020 §11; 0022 §5, §2, §14; also
  in Table B8-3).
- `BUSY` takes precedence over every other reason; then `NOT_OWNER` (0022 §10).
- A rejected arm precondition is reported only in `TX_ARM_STATE`, not in `WRITE_STATUS`. A
  `TX_ARM` write rejected as such (`NOT_OWNER`, `BUSY`) is reported in `WRITE_STATUS` to the
  writer only and changes nothing in `TX_ARM_STATE`, so a non-owner cannot overwrite the
  owner's last reject reason (0022 §13).
- The value MUST take effect before the answer is sent. [P2] orders nothing between ports: a
  host that needs a write in force before a High Priority action MUST wait for the answer
  (0020 §11; 0007 rule 2). A host MAY repeat a write after 100 ms without an answer; repeated
  writes are harmless (a correct `TX_ARM` while armed with the same token is a no-op, a
  `FAULT_CLEAR` without a fault is rejected, an `ATU_TUNE` start while tuning is a no-op)
  (0020 §7, §11).
- Writes to the capability record and to other read-only registers are answered with the
  current values and `READ_ONLY` (B4.6).

B8.5 **Writes from a host that is not the owner.** `CAP_REQUEST` MUST be accepted from any
host (B4.4). Every other write from a host that is not the owner, or while there is no
session, MUST be rejected with `NOT_OWNER` and answered to the writer's source address and
port; it MUST have no other effect: no takeover, no watchdog feed (0020 §12; 0007 rule 1 and
Decision 5). `NOT_OWNER` answers MUST NOT exceed one per 100 ms per source IP address and
port; further rejected writes are dropped without answer and counted (B11.14; 0022 §16).

B8.6 **Units.** Analogue registers are signed 32-bit integers in milli-units of an SI unit
(mV, mA, mW, m°C, ms; SWR as 1000 × SWR). Status registers are enumerations or bit fields;
bit 0 is the LSB, unused bits are 0, and codes not listed are reserved (0006 option 3A;
0003 §2; 0020 §8, §10).

Table B8-2 — G7250 registers ("RO" = read-only, radio → host; "W" = written by the host and
echoed with the value in force, B8.4)

| Name | Address | Access | Content, units | Sent | Source |
|------|---------|--------|----------------|------|--------|
| capability record (Table B4-1) | 0x0000–0x00CE | RO | Table B4-1 | on `CAP_REQUEST`; once per session | 0003 §2, §3; 0020 §26 |
| `CAP_REQUEST` | 0x0100 | W, any host | 0x00000001 requests the record; other values `BAD_VALUE` | answer | 0003 §2; 0020 §5 |
| `STREAM_STATUS` | 0x0101 | RO | one byte per stream: [7:0] DDC0, [15:8] DUC0, [23:16] microphone, [31:24] wideband; bit 7 running, [6:0] reason (Table B8-3) | on change | 0004 point 7; 0020 §8 |
| `LINK_STATUS` | 0x0102 | RO | [15:0] speed in Mbit/s (0 = link down); bit 16 full duplex; bit 17 non-default P2 port not honoured (latched until the next session); [31:24] session refusal reason: 0 none, 1 link below 100 Mbit/s | on change; B5.8 | 0003 §2; 0004 point 9; 0020 §8, §13, §20 |
| `WRITE_STATUS` | 0x0103 | RO | last rejected write, B8.4 | on every rejection, to the writer | 0020 §11 |
| `TX_ARM_TOKEN` | 0x0200 | RO | 32-bit token; never 0, 0xFFFFFFFF or `ARM_MAGIC`; differs from the previous token | at session start and on every change | 0007 Decision 1; 0020 §7 |
| `TX_ARM` | 0x0201 | W, owner | `token XOR ARM_MAGIC` arms; 0 disarms; any other value rejected (`BAD_TOKEN` in `TX_ARM_STATE`) | answer is `TX_ARM_STATE` | 0007 Decision 1; 0020 §7 |
| `TX_ARM_STATE` | 0x0202 | RO | [3:0] state 0 disarmed, 1 armed, 2 inhibited (armed, but a limit inhibit is active so TX requests do not key; entered from 1 when an inhibit starts, back to 1 when it lifts, no new generation); [15:8] last reject reason of the owner; [23:16] last drop reason; [31:24] arm generation (+1 per arm, wraps) (Table B8-3) | on every change | 0007 Decision 1; 0006; 0020 §8; 0022 §13 |
| `TX_STATE` | 0x0203 | RO | bit 0 keyed (PA actually keyed); bit 1 `WARN` active; bit 2 `REDUCE` active; bit 3 last TX request outside the TX ranges; bit 4 PA disabled by the host (General byte 58 bit [0]); bit 5 inhibit active; [11:8] TX source 0 none, 1 PTT, 2 CWX, 3 KEY, 4 ATU; [23:16] last unkey reason 0 none, 1 TX request released, 2 keyed timeout, 3 TX IQ underrun, 4 limit, 5 arm dropped, 6 retune needs RF-path change (A3.9), 7 PA disabled by the host while keyed (B10.10); [31:24] limit id when reason 4 | on every change (event) | 0007 Decisions 1, 2, 4; 0006; 0020 §8, §22; 0022 §1, §14 |
| `TX_MODE_CLASS` | 0x0204 | W, owner | 0 none declared (not writable); 1 SSB (including data modes sent as SSB), 2 CW, 3 AM, 4 FM; other values `BAD_VALUE`; power class 100 W PEP for 1, 2, 4 and 25 W carrier for 3 [G7250-MAN] (A3.4c); back to 0 at session end and at a takeover; a change while keyed applies at once | answer | 0007 Decision 4 rule 3; 0020 §9; 0022 §3, §17 |
| `KEYED_TIMEOUT` | 0x0205 | W, owner | ms; default 500; 100–500 accepted, other values `BAD_VALUE`; back to 500 at session end | answer | 0007 Decision 2; Resolved 2; 0020 §17 |
| `WATCHDOG_STATE` | 0x0206 | RO | bit 0 General byte 38 bit [0] as last written; bit 1 effective state; bit 2 no General packet yet (counts as enabled) | on change | 0007 Decision 2.3; 0020 §8 |
| `SAFETY_STATE` | 0x0210 | RO | 0 normal, 1 fault | event | 0007 Decision 5; 0020 §8 |
| `FAULT_CODE` | 0x0211 | RO | first cause, Table B8-3; 0 = none | event | 0007 Decision 5; 0006; 0020 §8 |
| `FAULT_FLAGS` | 0x0212 | RO | bit *c* set for every fault code *c* (1–31) since the last clear | event | 0007 Decision 5; 0020 §8 |
| `FAULT_CLASS` | 0x0213 | RO | 0 none, 1 host-clearable, 2 latched until reset; the highest class among the codes set in `FAULT_FLAGS` (classes per code in Table B8-3) | event | 0007 Decision 5; 0022 §5 |
| `TRIP_COUNT` | 0x0214 | RO | limit trips with action `UNKEY` or stronger since power-on; saturates at 0xFFFFFFFF; not cleared over P2 | event | 0007 Decision 5; 0020 §8 |
| `FAULT_CLEAR` | 0x0215 | W, owner | write the current `FAULT_CODE`; clears all flags if every flagged code is class 1 and its condition is gone (A3.5), else `NOT_CLEARABLE`; other values `BAD_VALUE` | answer | 0007 Decision 5; 0022 §5 |
| `LIMIT_STATUS` | 0x0220 | RO | bit *n*: limit *n* limiting (`WARN` or `REDUCE`); bit 16 + *n*: limit *n* tripped (`UNKEY` or stronger) since the last TX request; limit ids in Table B8-3 | event | 0006; 0007; 0020 §8 |
| `LIMIT_TX_TIME` | 0x0230 | W, owner | maximum continuous TX time, ms; built-in 300 000 | answer | 0007 Resolved 3; 0020 §10 |
| `LIMIT_FWD_POWER` | 0x0231 | W, owner | upper bound on forward power (PEP, A3.4c), mW, all bands and classes | answer | 0007 Decision 4; 0020 §10; 0022 §17 |
| `LIMIT_SWR` | 0x0232 | W, owner | 1000 × SWR; replaces S2 when stricter, S1 becomes the lower of S1 and this value | answer | 0007 Decision 4; 0020 §10 |
| `LIMIT_PA_TEMP` | 0x0233 | W, owner | m°C; replaces T3 when stricter | answer | 0007 Decision 4; 0020 §10 |
| `TLM_PA_TEMP` | 0x0300–0x0303 | RO | m°C, signed; sensors 0–3 | slow | 0006; HIS-11 |
| `TLM_PA_CURRENT` | 0x0304 | RO | mA | fast | 0006; HIS-11 |
| `TLM_SUPPLY_CURRENT` | 0x0305 | RO | mA (if separate from PA current) | fast | 0006; HIS-11 |
| `TLM_SWR` | 0x0306 | RO | 1000 × SWR as used by the safety core; 0 = not valid | fast | 0006; 0007 |
| `SENSOR_VALID` | 0x0307 | RO | bit *n* as record `telemetry` bit *n*; bit 7 PA temperature sensors 1–3 | event | 0006; HIS-11; 0020 §8 |
| `ATU_TUNE` | 0x0400 | W, owner | 1 starts internal ATU tuning (a TX request under the arm), 0 aborts; 1 while not armed: `NOT_ARMED`, not latched; other values `BAD_VALUE` | answer | 0007 Decision 6; HIS-08; 0020 §8; 0022 §14 |
| `ATU_STATE` | 0x0401 | RO | 0 off or bypassed, 1 in line, 2 tuning, 3 tuned, 4 failed | event | 0006; HIS-08; 0020 §8 |
| `ANT_STATE` | 0x0500 | RO | [7:0] connector actually selected, from 1; 0 unknown | event | 0006; HIS-06; 0020 §8 |

A `LIMIT_<name>` register holds the session value. A write is checked against the
persistent value (management C-3); a looser value is rejected with `LOOSER_LIMIT`. Writing 0,
and the end of the session, return the session value to the persistent value. The answer
carries the limit in force, the strictest of built-in, persistent and session value (A3.4;
0007 rules 1–2; 0020 §10; 0022 §6).

Constant `ARM_MAGIC` = 0x47375458 (ASCII "G7TX") (0020 §7).

B8.7 **Codes.** Table B8-3 gives the enumerations used in Table B8-2 (0020 §8). It is the
single authoritative list of symbolic code names of the G7250; part C uses these names
verbatim, in lower case where part C uses lower-case enumerations (0021 §14; 0022 §19). A
limit id name is also the name of that limit's `LIMIT_<name>` register where the limit is
host-tunable (Table B8-2); the other limit ids have no register.

Table B8-3 — Reason and fault codes (0020 §8; 0022 §5, §19)

| Set | Codes |
|-----|-------|
| Arm reject reason (`TX_ARM_STATE` [15:8]) | 0 none; 1 `NOT_OWNER` (reserved, not set since 0022 §13; a non-owner gets `WRITE_STATUS`); 2 `NOT_RUNNING`; 3 `WATCHDOG_DISABLED`; 4 `IN_FAULT`; 5 `INHIBITED`; 6 `PTT_ACTIVE`; 7 `LEVEL_NOT_ACTIVE`; 8 `MAINTENANCE`; 9 `NO_MODE_CLASS`; 10 `BAD_TOKEN`; 11 `TX_NOT_IMPLEMENTED` |
| Drop reason (`TX_ARM_STATE` [23:16]; Table A3-1) | 0 none; 1 `HOST_DISARM`; 2 `RUN_CLEARED`; 3 `WATCHDOG`; 4 `TAKEOVER`; 5 `RESET`; 6 `FAULT` (events 6 and 13); 8 `LINK_DOWN`; 9 `SESSION_CHANGED`; 10 `LEVEL_CHANGE`; 11 `MAINTENANCE`; 12 `REDISCOVERY`; 0x40 + limit id `LIMIT_<name>` (event 7) |
| Limit id (`TX_STATE` [31:24]; `LIMIT_STATUS` bit *n*; drop reason 0x40 + id) | 1 `LIMIT_TX_FREQ` (TX frequency); 2 `LIMIT_SWR` (SWR; host-tunable); 3 `LIMIT_PA_TEMP` (PA temperature; host-tunable); 4 `LIMIT_FWD_POWER` (forward power; host-tunable); 5 `LIMIT_SUPPLY_VOLTAGE` (supply voltage); 6 `LIMIT_CURRENT` (supply or PA current); 7 `LIMIT_TX_TIME` (maximum continuous TX time; host-tunable); 8 `LIMIT_ATU_TIME` (ATU tune time); 9 `LIMIT_SENSOR` (sensor plausibility); 10 `LIMIT_RF_NOT_KEYED` (RF while not keyed) |
| Fault code (`FAULT_CODE`, `FAULT_FLAGS` bit) and class | 0 none; 2 `SWR_REPEATED` (3 SWR trips in 10 s), class 1; 3 `PA_OVERTEMP` (PA temperature above T4), class 1; 9 `SENSOR_IMPLAUSIBLE` (sensor missing, stuck or out of range), class 2; 10 `RF_NOT_KEYED` (RF while not keyed), class 2; 16 `TX_PATH_NOT_BLOCKED` (drop event 13), class 2; 17 `WDT_RESET_AT_START` (processor watchdog reset seen at start-up, HIS-13), class 1; 18 `SELFTEST_FAILED` (start-up self-test failed), class 2; 19 `INTERNAL_ERROR` (internal consistency error), class 2; codes 1 and 4–8 reserved (those limits have no `FAULT` action) |
| Stream reason (`STREAM_STATUS` [6:0] per byte) | 0 none or running; 1 not enabled by the host; 2 not offered by this firmware; 3 sample rate not offered; 4 sample size not offered; 5 data format not offered (General byte 39); 6 time stamp or VITA-49 requested; 7 wideband parameters not offered; 8 link below 100 Mbit/s; 9 run bit clear; 10 update in progress; 11 VNA mode requested; 12 EER requested |
| Write reject reason (`WRITE_STATUS` [7:0]) | 1 `UNKNOWN_ADDRESS`; 2 `READ_ONLY`; 3 `NOT_OWNER`; 4 `BAD_VALUE`; 5 `LOOSER_LIMIT`; 6 `BUSY`; 7 `NOT_CLEARABLE`; 8 `KEYED`; 9 `NOT_ARMED` (B8.4) |

Names introduced in this part and not in the decisions 0003–0008 (`STREAM_STATUS`,
`LINK_STATUS`, `WRITE_STATUS`, `LIMIT_STATUS`, `TRIP_COUNT`, the four `LIMIT_<name>`
registers, `ATU_STATE`, `ANT_STATE`, `TLM_*`, `SENSOR_VALID`) label registers that 0003, 0004,
0006 and 0007 describe without a name, or that 0020 adds (0020 §3). The limit id, fault code
and the write reject reasons 7–9 names are added by 0022 §19. 0006 "TX state: PA
actually keyed" and "TX arm state, and reason of the last disarm" are carried by `TX_STATE`
and `TX_ARM_STATE` of 0007. Every telemetry register exists only if the HIS confirms the
sensor or state; absent sensors are flagged absent in the capability record, not reported as
0 (0006, Decision; B4.8 `tlm_desc`).

### B9 Telemetry

B9.1 **Split.** Telemetry that a standard High Priority status field describes with identical
meaning is sent there; everything else is in the G7250 register map (0006 option 1A; 0005).

B9.2 **High Priority status packet** (radio → host, always from local port 1025, the default
of General bytes 11–12, since non-default ports are not honoured, B2.3) ([P2] High Priority
Status packet; 0006, Decision; 0020 §13; 0022 §20).

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
| 39–40 | ADC0 max magnitude in the message period, 0–32767 (bit 15 = 0), if the DDC chain can provide it; else 0; [P2]'s note "Max ADC1 magnitude" is read as ADC0 (Annex X2, C14) | HIS-01, HIS-18; 0022 §21 |
| 41–42 | 0 unless a second ADC exists | HIS-03 |
| 49–50 | supply voltage at the power input, raw ADC word | HIS-11 |
| 51–58 | 0 (general purpose analogue inputs, "user specific" in [P2]) | 0006 option 1B rejected; 0022 §21 |
| 59 | 0 (general purpose digital inputs in [P2]; none on the G7250) | [P2] byte 59; 0022 §21 |

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
forward and reverse values describe is stated in record field `coupler`; its value:
TBD (HIS-08, HIS-11; B4.9). A generic P2 host has no
constants for this unit and may show wrong power and supply values (0006, Consequences).

B9.4 **Rates.**

- "Immediately" in this section means within 5 ms of the change, the bound of B8.4 (0020
  §11; 0022 §20).
- High Priority status: every 50 ms, every 1 ms while transmitting, and immediately when an
  input bit (bytes 4, 5) changes; immediate sends are limited to one per 1 ms ([P2] High
  Priority Status packet; 0006, Decision). If 1 ms is too costly (HIS-14, HIS-18), this is
  revisited and listed as a deviation (0006, Consequences).
- Register map (placeholders until HIS-11, HIS-14, HIS-18; 0006, Decision; Resolved): event
  registers immediately on change, at most one packet per 1 ms; fast registers every 10 ms
  while transmitting, otherwise with the periodic snapshot; a periodic snapshot of all
  telemetry registers every 1 s in one memory-mapped packet; analogue registers also on change
  beyond the hysteresis stated per register in record field `tlm_desc` (B4.8, B4.9; 0020 §26).
  The rates in use are stated in `tlm_rates` and `status_rates`.

B9.5 **G7250 telemetry registers.** The registers of B8 marked slow, fast or event in Table
B8-2, in the units of B8.6. The firmware computes SWR itself; the `TLM_SWR` register is the
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
   a reason in `TX_ARM_STATE`: it comes from the owner (else `WRITE_STATUS` `NOT_OWNER`,
   B8.4); RUN is set; the watchdog is effectively on and General byte 38 bit [0] was written
   as set in a General packet of this session (else `WATCHDOG_DISABLED`; B5.6; 0022 §13);
   the radio is not in fault; no limit inhibit is active; High Priority byte 4 bit [1] is 0 at
   that moment; level 1 is the active level; no firmware update is in progress and the running
   image is not an unconfirmed trial boot (else `MAINTENANCE`; A1.8; 0022 §10); a TX mode class
   has been declared in `TX_MODE_CLASS` for this session (else `NO_MODE_CLASS`) (0007 rule 1);
   and TX is implemented in this firmware, record `tx` bit 1 (else `TX_NOT_IMPLEMENTED`)
   (B4.8; 0020 §8). Reason codes: Table B8-3.
4. The arm takes effect when the G7250 pushes `TX_ARM_STATE` = armed with a new generation
   number. The host MUST wait for it. After arming, the G7250 MUST key only on a 0→1 edge of a
   TX request that arrives after the confirmation; a PTT bit that was already 1 does not key
   (0007 rule 2; [P2] does not order memory-mapped and High Priority packets).
5. The token MUST differ from the previous one and MUST NOT be 0, 0xFFFFFFFF or `ARM_MAGIC`
   (with the token equal to `ARM_MAGIC` the arm value would be 0, which disarms); it need not
   be unpredictable (0007 rule 3; 0020 §7; generation: HIS-18, HIS-20). A correct arm write
   while already armed with the same token is a no-op: it is answered and does not raise the
   generation (0020 §7).
6. The arm is dropped by the events of Table A3-1.

B10.3 **TX mode class.** Values: 1 SSB (including data modes sent as SSB), 2 CW, 3 AM, 4 FM
(B8, Table B8-2; 0020 §9). The host MUST declare the class in `TX_MODE_CLASS` before arming and
MUST update it whenever its TX mode changes. The AM limit (25 W carrier [G7250-MAN], measured
as in A3.4c) applies whenever the declared class is AM (0022 §17). The power measurement applies whatever the host declares. A missing
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
  Resolved 2). A value outside 100–500 ms is rejected with `WRITE_STATUS` reason `BAD_VALUE`
  and the value in force stays (B8.4); `KEYED_TIMEOUT` returns to 500 ms at session end
  (0020 §17). Tolerance: the G7250 MUST NOT unkey before `KEYED_TIMEOUT` and MUST have unkeyed
  no later than `KEYED_TIMEOUT` + 10 ms (0020 §16). Annex X1, D7.
- The keyed timeout also applies during internal ATU tuning; it ends the tune, reported as
  failed (`ATU_STATE` = 4) (0022 §14).
- In a non-CW TX, a DUC FIFO underflow ([P2] High Priority status byte 30 bit [2]) lasting
  longer than TBD ms (HIS-18) MUST unkey, arm kept (0007 Decision 2). Annex X1, D8. "Non-CW
  TX" means keyed with `TX_MODE_CLASS` other than 2 (CW) (0022 §14).
- After an unkey the host needs a new 0→1 TX request (A3.3).

B10.6 **DUC-specific packet.** Accepted on port 1026 ([P2] DUC specific packet).

Table B10-1 — DUC-specific packet ([P2] DUC specific packet)

| Byte | Field | G7250 behaviour | Source |
|------|-------|-----------------|--------|
| 4 | Number of DACs | ignored ("Presently unused" in [P2]) | [P2] byte 4 |
| 5 [1] | CW | honoured: selects hardware CW from KEY | [P2] byte 5; 0007 Decision 6 |
| 5 [2]–[6] | Reverse keys, iambic, sidetone, mode B, strict spacing | honoured for the hardware keyer; sidetone TBD (no speaker on the main unit, HIS-17) | [P2] byte 5; 0007 Decision 6 |
| 5 [7] | Break-in | honoured | [P2] byte 5; 0007 Decision 6 |
| 5 [0] | EER | set: refused (EER not offered): DUC I&Q not accepted and transmit refused until cleared; `STREAM_STATUS` reason 12 | [P2] byte 5, DUC I&Q NOTE; 0004 point 7; 0020 §22 |
| 6–8 | Sidetone level, frequency | TBD (HIS-17) | [P2] bytes 6–8 |
| 9, 10 | Keyer speed, weight | honoured | [P2] bytes 9–10; 0007 Decision 6 |
| 11–12 | Hang delay, ms | honoured | [P2] bytes 11–12; 0007 Decision 6 |
| 13 | RF delay, ms | honoured; SEND asserted before RF | [P2] byte 13; 0007 Decision 6 |
| 14–15 | DUC0 sampling rate | 192 honoured; any other value refused: DUC I&Q not accepted and transmit refused (PA off) until a valid packet; 0 read as 192 | [P2] bytes 14–15; 0004 points 2, 7; 0020 §18 |
| 16 | DUC0 bits | 24 honoured; 0 read as 24; any other value refused, as bytes 14–15 | [P2] byte 16; 0004 points 2, 7; 0020 §18 |
| 17 | CW ramp period | 5–10 ms honoured; 0 and any other value: G7250 default 8 ms; whether the hardware CW path can shape the ramp: HIS-12 | [P2] byte 17; 0020 §22 |
| 18–49 | Reserved | ignored | [P2]; 0005 rule 3 |
| 50, 51 | Line in, mic boost, Orion mic; line-in gain | TBD (HIS-17) | [P2] bytes 50–51 |
| 52–56 | Reserved | ignored | [P2]; 0005 rule 3 |
| 57–59 | RX step attenuator during TX | byte 59 (ADC0) TBD (HIS-07); bytes 57–58 ignored unless more ADCs (HIS-03) | [P2] bytes 57–59 |

B10.7 **TX IQ (DUC0).** In on port 1029, 192 ksps, 24-bit I and Q, 240 samples per packet,
1444-byte packets as [P2] DUC I&Q Data packet ([P2] DUC I&Q Data packet; "Detailed operation"
NOTE2; 0004 point 2). Record `duc_format` (B4.8). TX IQ is accepted only while no refusal of
B10.6 stands; the PA keys only under B10.2. A DUC I&Q packet whose source IP address and UDP
port are not the owner's (A2.2), or that arrives while there is no session, MUST be discarded
whole, MUST NOT enter the DUC FIFO and MUST have no other effect; it is counted per source in
`GET_STATS` (B11.1). A host MUST therefore send DUC I&Q from its session socket (0022 §4;
Annex X1, D24).

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
| Internal ATU tuning | a TX request: needs arm, owner, frequency in a range, limits, own profile and time limit; started by `ATU_TUNE` (HIS-08); tune power TBD (HIS-08, HIS-12); `ATU_TUNE` while not armed is rejected with `NOT_ARMED` and not latched; a PTT or CWX edge during the tune neither keys nor ends it, and a new 0→1 TX request is needed after it; the keyed timeout applies (0022 §14) |
| P2 TUNE bit (High Priority 1396–1397 bit [0]) | information only; does not start the internal ATU |
| Controller ATU key, SWR scan, other controller TX functions | refused while level 1 runs (A3.7), unless they reach the main unit as reportable requests (HIS-17) |
| Controller ANT and ATU in/out buttons | while keyed: ignored and logged, if they reach the main unit (A3.9; HIS-17) |
| Open-collector outputs (High Priority byte 1401) | ignored |

On level 1, controller inputs never key the radio (0007, Resolved 6).

B10.10 **PA enable while keyed.** General byte 58 bit [0] cleared while keyed MUST unkey
(`UNKEY`, arm kept, `TX_STATE` unkey reason 7); setting it again MUST NOT key without a new
0→1 TX request ([P2] General packet byte 58; 0020 §22; 0022 §14).

### B11 Error handling and robustness

This section gives the complete error handling of G7250-P2 (0001 spec section 11; 0004
point 7; 0020 §28). Values and reason codes are in B8 (Tables B8-2, B8-3).

B11.1 **Principle.** A packet the G7250 does not act on MUST have no effect at all: it MUST NOT
feed the watchdog, cause a takeover, start a session or change any state (0020 §28). Every
discarded packet is counted per port and reason and can be read with `GET_STATS` over the
management channel (A1.4, Table A1-2; 0020 §19, §28). Where a host can be told, the reason is
reported in a status register.

B11.2 **Requests not offered.** The G7250 MUST NOT clamp a request to an offered value and
MUST NOT silently keep a previous setting. It refuses: the stream concerned does not run until
a valid request arrives, and the reason is reported in `STREAM_STATUS` (0004 point 7; options
6A–6C rejected). Cases: B6.3, B6.6, B6.7, B6.10, B10.6, and VNA mode and EER (Table B7-1,
Table B10-1; 0020 §22). Annex X1, D13.

B11.3 **Malformed and short packets.** A packet shorter than the minimum of Table B11-1 MUST be
discarded whole; bytes beyond the [P2] length of the packet MUST be ignored (0020 §28).

Table B11-1 — Minimum UDP payload length accepted (0020 §4, §28)

| Port | Packet | Minimum length (bytes) | Source |
|------|--------|------------------------|--------|
| 1024 | Discovery (byte 4 = 0x02) | 5 | [P2] Discovery packet; B3.2 |
| 1024 | Set IP Address (0x03) | 15 | [P2] Set IP Address packet bytes 0–14 |
| 1024 | General (0x00) | 60 | [P2] General packet bytes 0–59 |
| 1025 | DDC-specific | 1444 | [P2] DDC specific packet bytes 0–1443 |
| 1026 | DUC-specific | 60 | [P2] DUC specific packet bytes 0–59 |
| 1027 | High Priority | 1444 | [P2] High Priority packet bytes 0–1443 |
| 1029 | DUC I&Q | 1444 | [P2] DUC I&Q Data packet |
| 7250 | Memory-mapped from PC | 10 (one pair) | [P2] Memory mapped registers from PC; B8.1 |
| 7251 | Management | 18 to be executed; 12–17 bytes with the right magic are answered with status 17; below 12 bytes dropped | A1.4, Table A1-1; 0022 §20 |

A truncated High Priority packet is never acted on in part, because PTT and drive would then be
read from missing bytes (0020 §28).

B11.4 **Port 1024 commands.** Erase (0x04) and Program (0x05) are ignored without a reply
(B3.9). A packet whose byte 4 is not 0x00, 0x02, 0x03, 0x04 or 0x05 MUST be ignored without a
reply (0020 §28).

B11.5 **Register writes** (B8.4, B8.5; 0020 §11, §12):

- a write to an address not in Table B8-2, or in a group that is not present, is rejected with
  `UNKNOWN_ADDRESS`;
- a write to a read-only register, including the capability record, is ignored and answered
  with the current value and `READ_ONLY` (B4.6);
- a write from a host that is not the owner, other than `CAP_REQUEST`, is rejected with
  `NOT_OWNER` and has no other effect;
- a value outside the allowed set is rejected with `BAD_VALUE`; a looser limit with
  `LOOSER_LIMIT` (A3.4); any write during a firmware update with `BUSY` (A1.8);
- a `FAULT_CLEAR` that cannot clear with `NOT_CLEARABLE` (A3.5); an RF-path write while keyed
  with `KEYED` (A3.9); `ATU_TUNE` while not armed with `NOT_ARMED` (B10.9) (0022 §19);
- arm writes that fail a precondition are rejected with a reason in `TX_ARM_STATE` (B10.2);
- padding pairs and a trailing incomplete pair are ignored (B8.1).

B11.6 **Sequence numbers and gaps.** The G7250 MUST NOT reject or reorder an incoming packet
because of its sequence number (B2.7). It counts gaps in the sequence numbers received on
ports 1027 and 1029 per session; the counts are read with `GET_STATS` (0020 §19). Outgoing:
a packet the G7250 drops (B11.7) still uses its sequence number, so that the host sees the
loss as a gap (0020 §19).

B11.7 **Overruns.**

- **RX.** When a DDC0 packet cannot be handed to the CH394Q in time (socket transmit buffer
  full), the G7250 MUST drop the whole packet, MUST NOT send a partial packet, and MUST set
  High Priority status byte 30 bit [0] ([P2] High Priority Status packet; 0020 §28). The same
  applies to wideband and microphone packets.
- **TX.** A DUC I&Q packet that finds the DUC FIFO full MUST be discarded whole; the CH394Q has
  no flow control in UDP mode ([CH394] section 12.2.4; 0020 §28). Underflow: B10.5. DUC I&Q
  from a source other than the owner never reaches the FIFO (B10.7; 0022 §4).

B11.8 **Frequencies outside the ranges.** A DDC0 frequency outside `rx_range` is tuned as
requested, without refusal or clamping; receiver performance there is not specified (B6.8;
0020 §28). A DUC0 frequency outside the transmit ranges is accepted, but a TX request then
does not key (Table A3-2; `TX_STATE` bit 3).

B11.9 **Packets to closed ports, including 1028.** [CH394] describes only how the CH394Q
reports a received ICMP "port unreachable" (GINT bit UNREACH, registers UNIP and UNPORT,
sections 7.1.7, 7.1.13 and 7.1.14); it does not state whether the chip sends one for a
datagram to a port that has no open socket. Firmware rule: nothing for such a port reaches the
firmware, and the firmware MUST NOT send any reply. A host MUST NOT depend on either silence or
an ICMP message (0020 §28; 0017). Test T-B11-08 records what the chip does.

B11.10 **Stale sessions and hosts.**

- The 1 s watchdog ends a session whose host is gone (B5.6).
- With the hardware timer disabled (allowed only while not armed) the session stays until a
  takeover, as [P2] allows ([P2] General packet byte 38; 0007, option 2F "Against"). An ICMP
  "port unreachable" for the owner's port ([CH394] section 7.1.7) MUST be logged and counted
  and MUST NOT end the session (0020 §28).
- A management write session ends after 60 s without a request (A1.10; 0020 §24).

B11.11 **Session refusal** on a link below 100 Mbit/s, with the reason in `LINK_STATUS` (B5.8).

B11.12 **Non-default ports.** A non-default radio-side port in a General packet is not
honoured; the default is kept and `LINK_STATUS` bit 17 is set (B2.3; 0020 §13).

B11.13 **Management channel errors.** A1.4 and Table A1-3 (0020 §27).

B11.14 **Rate limits and flood resistance** (0022 §16). So that the G7250 is no amplifier for
spoofed requests, answers to sources other than the owner MUST be limited per source IP
address and UDP port: `CAP_REQUEST` answers at most once per 1 s per source and 10 per second
in total (B4.4); `NOT_OWNER` answers at most once per 100 ms per source (B8.5); discovery
replies at most 10 per second per source and 50 per second in total (B3.2); management
replies at most 20 per second per source (A1.10). Requests above a limit are dropped and
counted (`GET_STATS`). The owner's own traffic is not limited. Safety timing does not depend on
the load (A3.10).

---

## Part C — Level 2: TCI

Part C, the single G7250 TCI profile followed by both AetherSDR on level 1 and the firmware's
TCI server on level 2 (0014), is in `spec/part-c-tci-profile.md`, with its choices in 0021. Base: [TCI] Transceiver Control Interface,
protocol 2.1 (`sources.md`, read 2026-11-19 in part). Level 2 is built only after gate G6
(0011 point 4). Level 2 sockets share the CH394Q with the management socket, which stays open
(0008, Socket budget; A1.2).

---

## Annex X1 — Differences from standard P2

Every deviation of G7250-P2 from [P2] (B1.5). Decisions 0003–0008 and 0017 are accepted; 0020
and 0022 are proposed for ON8ST review at rc1. Only hardware-dependent values (with their HIS id) remain
open in the sections concerned.

| Id | Deviation | [P2] behaviour | G7250 behaviour | Decision | Spec section |
|----|-----------|----------------|-----------------|----------|--------------|
| D1 | No DDC audio stream | Host may send DDC audio to port 1028 ([P2] DDC Audio packet; General bytes 13–14) | No socket on port 1028; General bytes 13–14 ignored; record `streams` bit 2 = 0 | 0017 | B2.3, B4 |
| D2 | Memory-mapped register port defined | Default port "xxxx", undefined ([P2] General bytes 29–32) | Default port 7250, one port for both directions; destination default (bytes 31–32 = 0) is the owner's source port; carries the G7250 register map | 0005, 0003, 0020 | B2.3, B8.1 |
| D3 | TX needs an explicit token arm | High Priority byte 4 bit [1] enables transmit ([P2]) | No TX request (PTT, CWX, KEY, ATU) keys unless armed by token handshake; keying only on an edge after confirmation; arm dropped by the events of Table A3-1 | 0015, 0007 | B10.1, B10.2, A3.2 |
| D4 | Hardware timer forced on while armed | Host may clear General byte 38 bit [0] ([P2]) | Clear honoured only while not armed; arming requires the bit set | 0015, 0007 | B5.6 |
| D5 | Takeover drops the arm | Second host's C&C takes over ([P2] Discovery reply byte 4 NOTE) | Takeover always allowed, but unkeys and drops the arm first; new owner starts unarmed, with mode class and session limits reset; RUN and RX settings kept | 0007, 0022 §3 | B5.7, A2.4 |
| D6 | Owner is IP address and UDP port | "different Host" not defined ([P2]) | A C&C packet from the owner's IP on another source port is a takeover; host must use one source port per session | 0007 | B5.5, A2.2; X2 C7 |
| D7 | Keyed timeout | Only the 1 s watchdog ([P2] "Detailed operation") | While keyed, High Priority at least every 100 ms; none within `KEYED_TIMEOUT` (500 ms) unkeys, arm kept | 0007 | B10.5 |
| D8 | TX IQ underrun unkeys | No such rule ([P2]) | DUC underflow longer than a time TBD (HIS-18) in non-CW TX unkeys | 0007 | B10.5 |
| D9 | TX mode class required | No such field ([P2]) | Arm refused without `TX_MODE_CLASS` | 0007 | B10.3 |
| D10 | Safety core overrides PTT | Bit [1] enables transmit ([P2]) | Limits may reduce drive or unkey while PTT is set; 5 min maximum continuous TX; no key outside the TX ranges; a retune while keyed that needs an RF-path change, or PA enable cleared while keyed, unkeys; RF-path fields are deferred while keyed | 0007, 0011, 0022 §1, §2, §14 | A3.4, A3.9, B10.4, B10.10 |
| D11 | Memory-mapped packets are not C&C | "any C&C packet" feeds the watchdog; not stated for memory-mapped packets ([P2]) | No memory-mapped packet feeds the watchdog or takes over; a `CAP_REQUEST`-only packet does not start a session; its answer goes to the request's source when the host is not the owner | 0003, 0007 | B4.4, B4.5, B5.6; X2 C6 |
| D12 | Erase and Program ignored | Erase/Program reprogram the EEPROM; Command Reply ([P2]) | Ignored without reply; V3.8 checksum not claimed; update only via the management channel | 0008 | B3.9, A1.8 |
| D13 | Unsupported requests refused | No negative acknowledgement; radio follows the host ([P2]) | Unoffered DDC rate or size, format, time stamp, VITA-49, VNA mode, wideband parameters, DUC rate/bits or EER: stream does not run, reason in `STREAM_STATUS`; never clamped | 0004, 0020 | B6.3, B6.6, B6.7, B6.10, B7, B10.6, B11.2 |
| D14 | Wideband parameters | Defaults 512 / 16 bit / 20 ms / 32 packets; zero selects the default only for byte 26; byte 27 range 0–255 ms ([P2] General bytes 24–28) | From M2, fixed 512 / 16 bit / 50 ms / 8 packets; zero in bytes 24–25, 27, 28 means these values; other values refused | 0004, 0022 §21 | B6.10 |
| D15 | Session refused below 100 Mbit/s | No link-speed rule ([P2]) | Discovery answered, no stream started, reason in `LINK_STATUS` | 0004 | B5.8 |
| D16 | PTT1–PTT3 never key | Table lists PTT1–PTT3 in byte 4 bits [2]–[4] ([P2]) | Bits [2]–[7] ignored | 0007 | B5.9; X2 C5 |
| D17 | TUNE bit does not tune | Client control bit [0] TUNE for accessory hardware ([P2]) | Information only; internal ATU via `ATU_TUNE` | 0007, 0005 | B7, B10.9 |
| D18 | Open-collector outputs ignored | High Priority byte 1401 drives outputs ([P2]) | Ignored (no such outputs) | 0007 | B7 |
| D19 | Power fields filled without Alex | Status bytes 14–15, 22–23 "Set to zero if Alex not selected" ([P2]) | Always filled from the PA coupler | 0006 | B9.2 |
| D20 | Conversion constants per unit | Constants per board type in Appendix A ([P2]) | Constants of this unit (per band where needed) from the capability record; words stay raw ADC values | 0006 | B9.3 |
| D21 | No port relocation onto the management port | Host may move ports with General bytes 5–32 ([P2]) | A P2 port is not moved onto the management port; default kept, conflict logged | 0008 | B2.3, A1.3 |
| D22 | Non-default radio-side ports not honoured | Host may move every radio-side port with General bytes 5–22, 29–30 ([P2]) | Zero or the default value honoured; any other value: default kept, logged, `LINK_STATUS` bit 17; bytes 31–32 (host side) honoured | 0020 §13 | B2.3, B7, B11.12 |
| D23 | No P2 session while level 2 is active | C&C from another host takes over ([P2] Discovery reply byte 4 NOTE) | While level 2 is active, P2 C&C starts no session and no takeover; discovery answers 0x03; level changes only over management | 0021 §16, 0020 §25 | A2.5 |
| D24 | DUC I&Q only from the owner | No source rule for DUC I&Q ([P2] DUC I&Q Data packet) | DUC I&Q from any source other than the owner's IP address and port is discarded and counted; the host sends it from its session socket | 0022 §4 | B10.7, B11.7 |
| D25 | Answer rate limits | Every discovery is answered ([P2] Discovery packet) | Discovery, `CAP_REQUEST`, `NOT_OWNER` and management answers are rate-limited per source; excess requests dropped and counted | 0022 §16 | B11.14, B3.2 |

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
| C2 | Discovery, Erase, Set IP, General, DDC-specific, DUC-specific and High Priority packets: sequence number "set to 0x00000000"; other packets: per-port counter, reset at "power on" (DDC, High Priority status, microphone, wideband packets) or "program start" (DDC audio, DUC I&Q, both memory-mapped packets); the High Priority status text says both "set to 0x00000000" and "rolls over after exceeding 0xFFFFFFFF" | G7250 sends per-port counters on all outgoing streams, the status packet included, reset at power-on, on stop and at a takeover (wideband: per frame, C16); discovery reply always 0; incoming sequence numbers are not checked (B2.7; 0022 §21) |
| C3 | Discovery reply byte 4: "0xFE (0xFF if running)" means a hardware configuration follows, "Appendix A"; Appendix C instead uses byte 4 = 0x02/0x03 and byte 11 = 255 | The G7250 uses neither: byte 4 is only 0x02 or 0x03, never board type 254/255, no Appendix C reply (0003 §1; B3.3, B3.4) |
| C4 | General byte 37: DSP clock "as part of the Discovery response as specified in Appendix B"; Appendix B is "To be written"; Appendix C bytes 27–30 carry the DSP clock | DSP clock for board type 200 is in record field `dsp_clock_hz`, same meaning as Appendix C bytes 27–30 (0003 §3; B3.8) |
| C5 | High Priority packet table: byte 4 "[1] = PTT0…[4] = PTT3"; text: "Bit [1] enables transmit … Bits [2] to [7] are reserved for future use" | Inconsistent in [P2]. The G7250 has one transmitter [G7250-MAN]: bit [1] is the transmit bit; bits [2]–[7] are ignored under either reading and never key (0007 rule 4; Resolved 11; B5.9) |
| C6 | "Detailed operation": "any C&C packet" feeds the watchdog; the term is not listed in one place | C&C packets are the four packets headed "Control Elements - PC to Hardware": General, DDC-specific, DUC-specific, High Priority (0022 §21). Memory-mapped packets ("Memory Mapped") are not C&C (0007 sub-decision 2.1; 0003 §2; B5.6) |
| C7 | Discovery reply byte 4: 0x03 if "connected to a different Host"; takeover by "the PC sending the C&C commands" | A host is identified by source IP address and UDP port; the owner's IP on another port is a different host (0007, Resolved 4; B3.4, B5.7) |
| C8 | Discovery reply byte 4: 0x03 when "running and already connected to a different Host" | While level 2 is active the RF chain is in use by another controller; the G7250 answers 0x03 (0003, Resolved; B3.4) |
| C9 | General byte 39: 0 selects Big-Endian 3-byte; bits [0] Big-Endian and [2] 3-byte select options "if indicated in the Discovery reply" | Provisional (no decision): 0x00, and values with only bits [0] and/or [2] set, select the offered format; any other bit refuses (B6.3) |
| C10 | General bytes 29–30 "memory mapped data from the PC will be sent to", bytes 31–32 "to the PC will be sent to" | Bytes 29–30 name the G7250's receive port, bytes 31–32 the host's destination port; the G7250 sends from the same local port it receives on (0005, Consequences; B8.1) |
| C11 | Set IP Address packet: success "can be verified by sending a Discovery Command"; Command reply packet: "Following a successful Set IP command, the hardware will respond with a Discovery reply packet" | Both hold: the G7250 sends a Discovery reply after a Set IP, and answers later discoveries with the new address (0008 point 6; B3.9) |
| C12 | Streams go to "the Source Port of the Host that initiated the Discovery Packet" (status, microphone, wideband "Destination Port") or "… the Discovery Command" (DDC packet "Destination Port"); the General packet is sent from that same port (General packet "Source Port") | The destination is the owner's source IP address and port (A2.2), fixed at session start or takeover (0022 §3, §12); for a P2 host this is the discovery port. A discovery from another socket of the same host does not move the streams, and a run bit without a discovery starts the session normally (0020 §14; B2.4, B5.2) |
| C13 | Set IP Address packet: "Broadcast to Port 1024", destination 255.255.255.255 | Also accepted when sent to the unit's unicast or the subnet's directed broadcast address; the MAC in bytes 5–10 identifies the unit (0020 §21; B3.9) |
| C14 | High Priority Status bytes 39–40 headed "ADC0 max magnitude" with the note "Max ADC1 magnitude"; text: "for each of ADC0 and ADC1 … up to 32768" | Bytes 39–40 carry ADC0, 0–32767, bit 15 = 0; the "ADC1" note is read as ADC0 (0022 §21; B9.2) |
| C15 | Memory-mapped packets shown with 240 address/data pairs, no count field | A packet carries 1 to 240 pairs and is 4 + 6*n* bytes long; the length is the count (0020 §4; 0022 §21; B8.1) |
| C16 | Wideband Data packet "Sequence Number": "set to zero at power on or whenever a block of raw samples has been sent" and "incremented in each sequential packet until the number of samples set in the General packet has been sent" (pp. 52–53) | The wideband counter is 0–7 within each 8-packet frame and restarts at 0 for every frame, not a continuous counter (0022 §21; B2.7, B6.10) |

## Annex X3 — Conformance tests

To be implemented in g7250-testbench, first against the reference model, then on the radio
(0001 item 5; design note §5 principle 6). Test ids are stable; descriptions are one line.

### Management channel, ownership, safety (A1–A3)

| Id | Description |
|----|-------------|
| T-A1-01 | The management port answers identification at both levels, also to a broadcast request. |
| T-A1-02 | No management request keys the radio, arms it, loosens a limit or switches an RF-path relay; `RESTART`, `FACTORY_RESET`, `SWITCH_LEVEL` and a C-3 change while armed and keyed unkey and disarm in the order of A3.2 before acting; every other request leaves `TX_STATE` and `TX_ARM_STATE` unchanged. |
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
| T-A1-13 | Wrong magic is dropped; a short or length-mismatched request gets status 17; an unknown major version gets status 18; an unknown command gets status 16. |
| T-A1-14 | A repeated request id gets the stored reply and is not executed twice. |
| T-A1-15 | A second host gets status 35 for writes while a write session is held; the session ends after 60 s idle. |
| T-A1-16 | The first-secret window closes 300 s after network up; a restart inside the window reopens it for 300 s. |
| T-A1-17 | A region change (C-6) is refused with status 57 while a P2 session runs; the factory default allows TX only in the intersection of all regions. |
| T-A1-18 | With a non-empty TCI allow-list, a TCI connection from an address outside it is refused and logged; the management port stays reachable. |
| T-A1-19 | A request with the right magic and 12–17 bytes gets status 17; one below 12 bytes gets no reply. |
| T-A1-20 | Two hosts (same IP, different ports) each get their own challenge; a request authenticated with the other host's challenge fails with status 33; a challenge works once. |
| T-A1-21 | A repeated request id within 5 s gets the cached reply; after 5 s a replayed authenticated request fails with status 33. |
| T-A1-22 | `CHANGE_SECRET` carries the masked new secret; the captured datagram does not contain the new secret; the new secret works afterwards. |
| T-A1-23 | After `UPDATE_BEGIN` the session ends and RX stops; a run request gets `STREAM_STATUS` reason 10 at most every 100 ms; register writes get `BUSY`; after `UPDATE_ABORT` the state lasts until `RESTART`. |
| T-A1-24 | During an unconfirmed trial boot RX works and an arm is rejected with `MAINTENANCE`; after confirmation it is accepted. |
| T-A1-25 | A region change is refused with status 50 while armed or keyed on either level and with status 57 while a P2 session runs. |
| T-A1-26 | More than 20 management requests per second from one source are answered at most 20 times per second; the excess is counted in `GET_STATS`. |
| T-A2-01 | Identification and record `level` report the active level and the owner (IP and port). |
| T-A2-02 | A level change drops the arm with `LEVEL_CHANGE` (after G6). |
| T-A2-03 | While level 2 is active, P2 C&C starts no session and no takeover (after G6). |
| T-A2-04 | `SWITCH_LEVEL` while armed and keyed follows A2.5a in order: reply status 1, unkey, `TX_ARM_STATE` with `LEVEL_CHANGE` from port 7250 before it closes, streams stop, change logged, P2 sockets closed, ports 1024 and 7251 open (after G6). |
| T-A2-05 | `SWITCH_LEVEL` to the active level returns status 0 and changes nothing; to level 2 before G6, status 56. |
| T-A2-06 | While level 2 is active, discovery answers 0x03, port 7250 is closed, and management identification gives level 2 (after G6). |
| T-A2-07 | Takeover by a General packet while host A runs: host B becomes owner at once, DDC0 continues to B from the next packet with sequence 0, nothing more goes to A after its last `TX_ARM_STATE`, B's watchdog runs, and the record is sent once to B. |
| T-A2-08 | After a takeover `TX_MODE_CLASS` is 0, `KEYED_TIMEOUT` 500 ms, session limits are the persistent values, and the RX settings of A are kept until B writes its own. |
| T-A2-09 | Two hosts alternating C&C every 50 ms: neither can stay armed, every takeover is counted, and the log has at most one takeover entry per second for the pair. |
| T-A3-01 | Each drop event of Table A3-1 unkeys, disarms, issues a new token and reports its reason (one test per row). |
| T-A3-02 | Each limit row of Table A3-2 gives its action and recovery (one test per row, reference model). |
| T-A3-03 | A `LIMIT_<name>` write looser than the persistent value (C-3) is rejected with `LOOSER_LIMIT`, a stricter one accepted; writing 0 and the session end return to the persistent value; the answer carries the limit in force. |
| T-A3-04 | A class 1 fault clears only with the current code and only when the condition is gone; a clear does not re-arm. |
| T-A3-14 | With a class 1 and a class 2 code flagged, `FAULT_CLASS` is 2 and `FAULT_CLEAR` is rejected with `NOT_CLEARABLE`, clearing nothing; with only class 1 codes whose conditions are gone, all flags clear. |
| T-A3-15 | A processor watchdog reset seen at start-up gives `WDT_RESET_AT_START`, class 1, clearable by `FAULT_CLEAR` without another reset; the radio never resets itself to clear a fault. |
| T-A3-05 | A class 2 fault clears only by reset and is detected again at start-up if the cause persists. |
| T-A3-06 | After power-on and after every session end the state of A3.6 holds. |
| T-A3-07 | Controller PTT and KEY inputs are reported and never key the radio without arm, with and without a P2 session while level 1 is active. |
| T-A3-08 | While keyed, a DUC0 retune inside the same transmit range and RF-path state is followed without unkey. |
| T-A3-09 | While keyed, a DUC0 change to another `tx_band` entry, or out of all ranges, unkeys before the frequency applies (`TX_STATE` reason 6, or 4 with `LIMIT_TX_FREQ`), keeps the arm, and switches relays only after the unkey; keying again needs a new 0→1 edge. |
| T-A3-10 | While keyed, an Alex word or step-attenuator change in the High Priority packet is applied only after the unkey; a register write that would switch an RF-path relay is rejected with `KEYED`; a controller ANT or ATU press is ignored and logged. |
| T-A3-11 | SWR above S1 caps forward power at `P_swr` until the unkey even if SWR falls back; the next transmission starts uncapped (reference model). |
| T-A3-12 | PA temperature above T2 caps power at `P_temp`; the cap lifts below T2 minus the hysteresis; a short temperature spike below the filter time constant does not cap (reference model). |
| T-A3-13 | Under a received flood at line rate to every open port, the watchdog, keyed timeout and limit actions keep their timing (the unkey may come earlier, never later). |

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
| T-B3-28 | A discovery from the owner's IP on another port while armed is answered with 0x03 and does not drop the arm or move the streams. |
| T-B3-29 | Set IP with the unit's MAC sent to the unicast or directed broadcast address is accepted with the same effects as a broadcast Set IP. |
| T-B3-30 | Byte 13 equals major × 10 + minor of `fw_version`, capped at 255; byte 23 is non-zero only on a beta build. |
| T-B3-31 | 100 discoveries per second from one source get at most 10 replies per second; the excess is counted in `GET_STATS`. |

### Capability record (B4)

| Id | Description |
|----|-------------|
| T-B4-01 | A `CAP_REQUEST` write is answered with one memory-mapped packet holding the echo and the whole record. |
| T-B4-02 | `cap_magic` is 0x47373235 and `cap_length` equals the number of record registers sent (their values are checked with the version 1.1 fields, below). |
| T-B4-03 | `product_name` reads "G7250-P2". |
| T-B4-04 | A `CAP_REQUEST`-only packet from a host without a session starts no session, takes nothing over, does not feed the watchdog, and is answered to its source IP and port. |
| T-B4-05 | A `CAP_REQUEST` from host B while host A runs does not disturb A's session or arm. |
| T-B4-06 | Writes to the record range are ignored and answered with the current values. |
| T-B4-07 | The record is sent once, unasked, after the first General packet of a session. |
| T-B4-08 | The record does not change during a session. |
| T-B4-09 | `ddc_rates`, `num_ddc`, `streams`, `duc_format`, `wb_format`, `wb_frame`, `link` and `tx` match the behaviour tested in B5, B6 and B10. |
| T-B4-10 | Unused bits and unused range, band and calibration entries are zero. |
| T-B4-11 | `CAP_REQUEST` with a value other than 1 is rejected with `BAD_VALUE` and sends no record. |
| T-B4-12 | `cap_version` is 1.1, `cap_length` is 207, `mgmt` is 0x1C530001, `regmap_version` is 1.0, and the version 1.1 fields match the behaviour tested in B9. |
| T-B4-13 | A `CAP_REQUEST` from the future session socket before the first General packet is answered to that socket and does not make it the owner. |
| T-B4-14 | `CAP_REQUEST`s from a non-owner source at 10 per second are answered at most once per second; from 20 sources, at most 10 answers per second in total. |

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
| T-B5-10 | With C&C every 900 ms the session stays; after the last C&C the unit is in standby within 1100 ms. |
| T-B5-11 | A run bit without a preceding discovery starts the streams to the sender's source port. |
| T-B5-12 | On a 10 Mbit/s link no High Priority status is sent; each run request and `CAP_REQUEST` is answered with `LINK_STATUS` and `STREAM_STATUS`, at most once per 100 ms. |
| T-B5-13 | A link renegotiation from 100 to 10 Mbit/s while armed and keyed unkeys, disarms with `LINK_DOWN`, stops the streams and sets `LINK_STATUS` refusal reason 1; back at 100 Mbit/s nothing restarts until a new run. |
| T-B5-14 | An arm before any General packet of the session is rejected with `WATCHDOG_DISABLED`; after a General packet with byte 38 bit [0] set (even with a refused byte 39) it is accepted. |

### Streams (B6)

| Id | Description |
|----|-------------|
| T-B6-01 | No DDC0 data before a High Priority packet with run set. |
| T-B6-02 | After General, DDC-specific and run, DDC0 packets arrive from port 1035 to the owner's source IP address and port, also when the host's discovery came from another port. |
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
| T-B6-21 | Before M2, a wideband enable sends nothing; from M2, ADC0 wideband gives 8 packets of 1028 bytes every 50 ms, with sequence numbers 0–7 in every frame. |
| T-B6-22 | From M2, wideband parameters other than 0 or the fixed values stop wideband with a reason. |
| T-B6-23 | No microphone packets are sent unless `streams` bit 3 is set. |
| T-B6-24 | The DDC0 sequence counter does not restart on a rate change, nor on a resume after a refusal or after DDC-specific byte 7 bit [0] was cleared. |
| T-B6-25 | Each stream comes from its local port of B2.4a. |

### Field table and register map (B7, B8)

| Id | Description |
|----|-------------|
| T-B7-01 | Every field marked "ignored" in Tables B7-1, B7-2 and B10-1 has no effect. |
| T-B7-02 | High Priority byte 4 bits [2]–[7], the TUNE bit and byte 1401 never key or switch anything. |
| T-B7-03 | A non-default radio-side port in General bytes 5–22 or 29–30 is not honoured: the default stays, `LINK_STATUS` bit 17 is set and the request is logged; non-zero bytes 31–32 redirect register packets. |
| T-B7-04 | General byte 37 bit [2] set stops DDC0 with reason 11. |
| T-B7-05 | General byte 58 bit [0] = 0 keeps a TX request from keying and sets `TX_STATE` bit 4. |
| T-B8-01 | All registers of Table B8-2 marked "on change" or "event" are pushed within 5 ms of a change. |
| T-B8-02 | `TX_ARM` from a non-owner is rejected; `CAP_REQUEST` from any host is answered. |
| T-B8-03 | `TX_ARM_TOKEN` is never 0, 0xFFFFFFFF or `ARM_MAGIC` and changes on every drop and every new session. |
| T-B8-04 | Every written pair is answered with the value in force within 5 ms, in write order. |
| T-B8-05 | Writes to an unknown address, a read-only register, with a bad value or a looser limit are answered with the value in force and `WRITE_STATUS` with the reason of B8.4. |
| T-B8-06 | Writes from a non-owner, other than `CAP_REQUEST`, are rejected with `NOT_OWNER`, answered to the source, and cause no takeover or watchdog feed. |
| T-B8-07 | Padding pairs (0xFFFF, and 0x0000 with data 0) and a trailing incomplete pair are ignored and not answered. |
| T-B8-08 | Register packets come from port 7250 and go to the owner's source port, or to General bytes 31–32 when non-zero. |
| T-B8-09 | A non-owner's `TX_ARM` write gets `WRITE_STATUS` `NOT_OWNER` to the writer and leaves the owner's `TX_ARM_STATE` (last reject reason included) unchanged; an owner's failed arm precondition is reported in `TX_ARM_STATE` only. |
| T-B8-10 | During a firmware update a non-owner's write gets `BUSY`, not `NOT_OWNER`. |
| T-B8-11 | `NOT_OWNER` answers to one source are at most one per 100 ms. |
| T-B8-12 | With an inhibit active while armed, `TX_ARM_STATE` shows state 2 without a new generation and returns to 1 when it lifts; while disarmed an arm is rejected with `INHIBITED`. |

### Telemetry (B9)

| Id | Description |
|----|-------------|
| T-B9-01 | High Priority status arrives every 50 ms, every 1 ms while transmitting, and immediately (at most one per ms) on an input change. |
| T-B9-02 | Bytes listed as 0 in Table B9-1 are zero; bytes 39–40 never exceed 32767. |
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
| T-B10-06 | An arm without `TX_MODE_CLASS` is rejected with `NO_MODE_CLASS`; with class AM and an unmodulated carrier at full drive, the 100 ms mean forward power settles at or below 25 W plus the margin within 200 ms, or the radio unkeys (A3.4c). |
| T-B10-07 | While keyed, no High Priority packet for 500 ms (or the written shorter value) unkeys and keeps the arm. |
| T-B10-08 | `KEYED_TIMEOUT` values above 500 ms or below 100 ms are not accepted. |
| T-B10-09 | Continuous TX for 5 min (or the stricter value) unkeys and keeps the arm. |
| T-B10-10 | A DUC rate other than 192 or bits other than 24 refuses TX IQ and keeps the PA off, with a reason. |
| T-B10-11 | A DUC underflow longer than the set time in non-CW TX unkeys and keeps the arm. |
| T-B10-12 | A TX request with DUC0 outside the transmit ranges does not key. |
| T-B10-13 | SEND is asserted only while armed and keyed, before RF, and released on every drop event, standby and fault. |
| T-B10-14 | `ATU_TUNE` without arm does not tune; with arm it tunes within its time limit. |
| T-B10-15 | KEY keys hardware CW only when armed and CW is selected. |
| T-B10-16 | A `KEYED_TIMEOUT` write outside 100–500 is rejected with `BAD_VALUE`; the value returns to 500 at session end; unkey happens between T and T + 10 ms. |
| T-B10-17 | DUC-specific byte 5 bit [0] (EER) set refuses TX IQ with reason 12. |
| T-B10-18 | DUC-specific bytes 14–15 = 0 and byte 16 = 0 are read as 192 ksps and 24 bits. |
| T-B10-19 | `TX_MODE_CLASS` values 0 and above 4 are rejected; the class returns to 0 at session end. |
| T-B10-20 | A repeated correct arm write while armed is answered and does not raise the generation. |
| T-B10-21 | DUC I&Q from a source other than the owner's IP address and port (including the owner's IP on another port) is discarded, never fills the FIFO, has no effect on an armed owner's transmission, and is counted in `GET_STATS`. |
| T-B10-22 | `ATU_TUNE` = 1 while not armed is rejected with `NOT_ARMED` and does not start after a later arm. |
| T-B10-23 | During ATU tuning a PTT edge neither keys nor ends the tune; no High Priority packet for `KEYED_TIMEOUT` ends the tune with `ATU_STATE` = 4. |
| T-B10-24 | With `TX_MODE_CLASS` = 2 (CW) a DUC underflow does not unkey; with any other class it does after the set time. |
| T-B10-25 | General byte 58 bit [0] cleared while keyed unkeys with `TX_STATE` reason 7, arm kept; setting it again does not key without a new 0→1 edge. |

### Error handling (B11)

| Id | Description |
|----|-------------|
| T-B11-01 | Each packet type shorter than Table B11-1 is discarded with no effect (no watchdog feed, no takeover). |
| T-B11-02 | A truncated High Priority packet with PTT set does not key. |
| T-B11-03 | Unknown command bytes on port 1024 get no reply and change nothing. |
| T-B11-04 | Packets with arbitrary or repeated sequence numbers are accepted; gaps on ports 1027 and 1029 are counted in `GET_STATS`. |
| T-B11-05 | Under forced RX overrun only whole DDC0 packets are lost, the gap shows in the sequence numbers, and status byte 30 bit [0] is set. |
| T-B11-06 | DUC I&Q arriving faster than 192 ksps loses whole packets only. |
| T-B11-07 | A DDC0 frequency outside `rx_range` is tuned without refusal. |
| T-B11-08 | Datagrams to port 1028 and other closed ports get no reply from the firmware; whether the CH394Q sends ICMP is recorded. |
| T-B11-09 | With the hardware timer disabled and the owner gone, the session stays until a takeover; an ICMP port unreachable is logged and does not end it. |

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
- [CH394] WCH CH394 manual 1, V1.2: sections 1–3, 7.1.2–7.1.7, 7.1.13–7.1.15 (UNIP, UNPORT,
  PHY_CFG), 7.2, 12.2.4.
- [G7250-MAN] Xiegu G7250 Operation Manual rev 0.1; [G7250-PUDX], [G7250-RIGPIX] (50 MHz
  power, secondary).
- [TCI] Transceiver Control Interface 2.1 (read in part).
- [FIPS180-4] NIST FIPS 180-4 (SHA-256); [RFC2104] HMAC (`sources.md`).
- [AETHER-SRC] AetherSDR source, commit 9f7cbeb; [PIHPSDR] piHPSDR source, commit 422bec5
  (`sources.md`; used for the DDC rate unit and host behaviour, B3.2, B6.5, 0020).
- `analysis/ch394-network-budget.md`; `open-questions-his.md` (HIS-01 to HIS-20).
- Decisions 0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0011, 0012, 0014, 0015,
  0016, 0017, 0018, 0019, 0020 (proposed), 0021 (§2, §8, §10, §14, §16), 0022 (proposed);
  design note §6.
- RFC 2119, RFC 8174 (BCP 14).

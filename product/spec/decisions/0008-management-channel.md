# 0008 — Management channel: own UDP port on the free socket; boundaries and requirements

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19
- Scope: spec part A (common to both levels, 0011). This version fixes the shape of the
  channel and its requirements, not the packet formats (0001, spec section 10).

## Context

0001 (spec section 10) asks for a management channel separate from the radio protocol, with
its own port and protocol, for firmware update, configuration, logs and identification. In
this version only its boundaries and requirements are written. 0011 (point 2) adds that the
active level and its owner are visible in the management channel. Milestone M5 asks for an
update with recovery after failure and a configuration that survives a restart
(`design-note.md`, section 6).

What constrains the choice:

- **Sockets.** The Ethernet controller is a WCH CH394Q with 8 sockets (ON8ST, hardware
  inspection, 2026-11-19; to be confirmed, HIS-14) [CH394]. G7250-P2 with one receiver and
  the G7250 register map uses 7 of them; one is free because DDC audio is not offered (0017,
  `analysis/ch394-network-budget.md`).
- **TCP on the CH394Q.** A socket in TCP mode is put in LISTEN; when a client connects, that
  same socket goes to ESTABLISHED [CH394] (section 7.2.2, table 7-9, LISTEN command; section
  7.2.4, table 7-11). So one socket serves one TCP connection, and while it is connected
  there is no listener on that port. A TCP socket has a KeepAlive timer register
  (Sn_KEEPALIVE, 0x002F) and a SEND_KEEP command [CH394] (section 6.1; table 7-9).
- **MACRAW** is possible on socket 0 only [CH394] (section 7.2.1, table 7-8), and would put
  the whole IP stack on the processor (`analysis/ch394-network-budget.md`).
- **No DHCP in the chip.** The CH394 lists IP, ARP, ICMP, IGMP, UDP and TCP as its built-in
  protocols [CH394] (sections 1 and 2); DHCP is not among them. A DHCP client therefore runs
  on the processor and needs a UDP socket of its own while it talks (each socket has one
  source port, Sn_PORT [CH394] section 7.2.5). The chip does signal an IP address conflict
  (GINT bit 7, IP_CONFLI) [CH394] (section 7.1.7).
- **What P2 already offers on port 1024** [P2]:
  - Erase (byte 4 = 0x04) and Program (byte 4 = 0x05) packets to "the EEPROM". A Program
    packet carries the total number of 256-byte blocks in bytes 5–8 and 256 bytes of data in
    bytes 9–264. The radio answers each block with a Command Reply (byte 4 = 0x04) that
    echoes the last sequence number and asks for the next block; an erase is acknowledged
    with byte 4 = 0x03, once on receipt and once when done ("may take 10's of seconds"; "up to
    15 seconds").
  - Since V3.8 (27 Mar 2019) the Command Reply carries a 16-bit "Firmware Checksum" in bytes
    13–14, "the sum of all bytes received", including 0xFF filler in the last block. The
    host compares it with the checksum of the file. V3.8 says boards "may include this
    feature".
  - In the Command Reply, byte 11 is the firmware code version and byte 12 the board type;
    in the Discovery reply, byte 11 is the board type and byte 13 the firmware code version.
  - Set IP Address (byte 4 = 0x03), broadcast to 255.255.255.255:1024, target MAC in bytes
    5–10, new address in bytes 11–14; 0.0.0.0 selects DHCP; the radio stores it in EEPROM
    and answers with a Discovery reply.
  - None of these packets has any authentication, and the program sequence has no
    integrity check stronger than the 16-bit byte sum, no signature, and no rollback.
  - P2 states no preconditions for Set IP Address (no check on RUN state or anything
    else) [P2].
  - The host can move most radio-side P2 ports with the General packet (bytes 5–32), and the
    DDC I&Q ports run from a base (default 1035) up to base + 79.
- **The radio.** The controller has a TF card slot (FAT32) and a USB port; the main unit has
  only the LAN port for data [G7250-MAN]. The controller's System Information page lists
  separate versions for the controller ("APP"), the main unit ("FIRMWARE"), the "FPGA" and
  the "HARDWARE" [G7250-MAN]. The controller also has a NETWORK settings page and a
  factory reset [G7250-MAN]. Whether the main unit can reach the TF card, USB or the
  controller's screen is not known (HIS-17). How firmware gets into the main unit and
  whether a boot loader survives a failed update is not known (HIS-19). Processor, RAM and
  flash are not known (HIS-18).
- **Safety.** The radio has a 100 W PA [G7250-MAN]. TX needs an explicit arm in the G7250
  register map (0015), and the safety core sits below every level (0011 point 3;
  `design-note.md` section 4). Watchdog and safety details are in 0007.
- **Licence.** The firmware is GPL-3.0-or-later (0018), which requires installation
  information for consumer devices: the owner must be able to install a modified build.

## Options considered

### Transport and port

#### T1. Own UDP port on the one free socket (chosen)

A dedicated port, served by the eighth socket, with a small request/response protocol of
its own.

- For: fits the budget exactly (0017) without touching any P2 port.
- For: UDP needs no connection state in the chip. Any host on the LAN can ask, and a host
  that vanishes leaves nothing behind. With TCP on a single socket, a half-open connection
  would lock management out until a keep-alive or retransmission timeout closes it
  [CH394] (section 7.2.2).
- For: same transport style as P2 [P2], so the host side (AetherSDR backend, test tools)
  already has a UDP path.
- Against: reliability for the firmware transfer (sequence numbers, acknowledgement,
  retransmission, integrity) has to be in our own protocol.
- Against: without a session concept, two tools could interleave writes. A session lock is
  needed (requirement S5).

#### T2. Own TCP port on the free socket

- For: reliable byte stream; a firmware image is a natural stream.
- Against: one connection at a time, no listener while connected, and a stale connection
  blocks management until a timeout [CH394] (sections 7.2.2, 7.2.4). Reopening a listener
  after every connection is extra state in the firmware.
- Against: TCP's own retransmission does not remove the need for an end-to-end image check;
  the application-level work is about the same as T1.

#### T3. Reuse port 1024 with P2's own Erase, Program and Set IP packets

- For: no socket at all; existing P2 tooling that knows the program sequence could flash the
  radio.
- Against: the P2 sequence assumes "the EEPROM" is erased and written in place [P2]. There is
  no staging, no rollback, and only a 16-bit byte sum, which V3.8 makes optional [P2].
  A failed or forged update on a 100 W radio must not be possible this easily.
- Against: no authentication. Any host on the LAN can erase the radio with one 60-byte
  packet [P2].
- Against: configuration, logs and level selection do not exist in P2. Adding them as new
  byte-4 command values on 1024 would be our own extension inside a standard packet, which
  0009 and 0005 rule out.
- Against: the same byte-4 value 0x03 means "erase acknowledged" in a Command Reply and
  "busy, connected to another host" in a Discovery reply, and the version and board-type
  bytes swap places between the two replies [P2]. That is room for host confusion, not a
  base to build on.
- Against: 0001 asks for a channel separate from the radio protocol.
- Outcome: rejected as the management channel. Only P2 Set IP Address is kept on 1024,
  exactly as P2 specifies (Decision, point 6; ON8ST, 2026-11-19).

#### T4. HTTP/REST (built-in web page)

- For: no tool needed; a browser is enough.
- Against: browsers open several TCP connections in parallel; with one socket and one
  connection per socket [CH394] (section 7.2.2) a page with more than one resource stalls
  or fails.
- Against: a browser on the LAN is reachable by any web page the user visits. A web
  management interface without strong protection is open to cross-site requests (a page
  making the browser post to the radio). This needs authentication, origin checks and care
  that a small HTTP server on an unknown processor (HIS-18) may not have room for.
- Against: an HTTP server and parser in the firmware are a large attack surface for a
  device that can transmit.
- Outcome: not in the firmware. If a browser interface is ever made, it is a PC tool that
  speaks the UDP channel (ON8ST, 2026-11-19).

#### T5. WebSocket

- For: the WebSocket layer is needed anyway for TCI at level 2 [TCI], so code could be
  shared.
- Against: same socket and browser problems as T4, and the WebSocket layer only exists after
  gate G6 (0011). Management is needed at M5, before level 2.

#### T6. Nothing over the network: TF card or USB only

- For: no network attack surface for updates; physical access is the authorisation.
- Against: the TF slot and USB port are on the controller, not on the main unit
  [G7250-MAN]. Whether the main unit can read them over the CTRL cable is unknown (HIS-17).
- Against: a main unit operated remotely (the main unit "can be deployed independently"
  [G7250-MAN]) could not be updated or configured remotely.
- Kept as a recovery path, not as the main channel (requirement U-9).

#### T7. MACRAW on socket 0, many ports

- Against: only socket 0 can do MACRAW [CH394] (section 7.2.1), and the processor then
  carries the IP stack with all traffic as full frames over SPI
  (`analysis/ch394-network-budget.md`). Too costly for one extra port.

### Firmware integrity and authenticity

#### I1. Integrity only, room for a signature later (chosen; ON8ST, 2026-11-19)

Every image carries a SHA-256 [FIPS-180-4] over each component, checked before activation,
and every transfer block a CRC-32. No signature is produced or checked in this version. The
package header reserves a signature field (empty for now), so signing can be added later
without a new package format.

- For: catches corrupted transfers and wrong files every time.
- For: keeps the owner able to install their own GPL build (0018), with no key to manage.
- Against: no authenticity. Anyone who has the owner's secret (S2) can install any image
  that passes the hash. That is the same trust as the owner; the protection against
  strangers on the LAN is the authentication of S2, not the image.
- Against: a hash only proves the image matches its own header; it does not prove who made
  it.

#### I2. Signature enforced, only ON8ST builds boot

- Against: conflicts with GPL-3.0 installation information (0018), and locks owners out of
  their own radio.

#### I3. P2-style 16-bit byte sum only

- Against: does not detect reordered blocks or many multi-byte errors, and gives no
  authenticity [P2].

#### I4. Integrity plus an optional signature, reported but not enforced (not now; possible later)

Official builds would carry a signature; the radio would verify it, report whether the
running image is officially signed, and accept an unsigned or differently signed image only
with an explicit owner flag.

- For: lets an owner see whether an image is an official build.
- Against: needs a signing key, its custody and a verifier in the boot path; not wanted for
  now (ON8ST, 2026-11-19). The reserved signature field in I1 keeps this open.

### First secret in factory state

#### F1. Network window, first come, first served (chosen; ON8ST, 2026-11-19)

In factory state (no secret set), the radio accepts a request that sets the first secret
over the network during a one-time window of a few minutes after the first power-on, or
after a factory reset. There is no confirmation on the controller.

- For: works without knowing whether the main unit can use the controller's screen or
  buttons (HIS-17), and works for a main unit deployed on its own [G7250-MAN].
- Against: anyone on the LAN during the window can claim the radio first.

#### F2. Set or confirm the first secret on the controller (rejected for now; possible later)

- For: physical presence is the authorisation; a LAN attacker cannot claim the radio.
- Against: needs the main unit to show a prompt on, or receive a button press from, the
  controller, which is unknown (HIS-17). Can be added later as an extra confirmation if
  HIS-17 allows it.

#### F3. Secret printed per unit and set at production (rejected)

- Against: not possible for an open firmware that the owner flashes onto a unit already
  sold.

## Decision

### Transport

1. The management channel uses **its own UDP port**, served by the **eighth socket** of the
   CH394Q, the one left free by 0017. The socket is **reserved at both levels** and is open
   whenever the network is up.
2. The port number is fixed in spec part A. It MUST lie outside every range a P2 host can
   place radio-side ports in by default: 1024–1029 and the DDC range 1035–1114 [P2] (General
   packet bytes 17–18). If a General packet moves a P2 port onto the management port, the
   radio MUST NOT give the management socket away; it keeps the default for that P2 port and
   logs the conflict (spec part B).
3. The channel is request/response. Every request carries a request id; every reply
   echoes it and carries a status code. Large transfers are split into numbered blocks,
   each acknowledged; the host retransmits on a timeout. Exact formats go into spec part A.
4. The channel has its own protocol version, reported in identification, independent of the
   P2 version and the capability-block version (0003).
5. **P2 port 1024 does not program the radio.** Erase (0x04) and Program (0x05) packets are
   ignored without a reply; a P2 host then hits its own timeout [P2]. Firmware is updated
   only through the management channel. The G7250 does not claim the V3.8 checksum feature.
   Spec part B states this. This is a deliberate, documented deviation: P2 defines the two
   packets but gives them no authentication and no rollback [P2], and an unauthenticated
   erase is not acceptable on a 100 W radio (T3). It does not conflict with point 6: Set IP
   Address is a separate command [P2], and accepting it does not require accepting Erase or
   Program.
6. **P2 Set IP Address** (0x03) on port 1024 is **accepted exactly as P2 specifies** (ON8ST,
   2026-11-19): a broadcast to 255.255.255.255:1024 with the radio's MAC in bytes 5–10 sets
   the address in bytes 11–14 (0.0.0.0 selects DHCP), the radio stores it and answers with a
   Discovery reply [P2]. P2 sets no preconditions [P2], so the radio adds none (no refusal
   while armed or while a P2 session runs, no option to disable it); any such refusal would
   be a deviation from P2. The only addition is not visible on the wire: the change is logged
   with its source address (L-2). The stored value is the same network configuration as C-1,
   applied after the reply as in C-4, including the fallback on an address conflict. See S7.

### Functions

#### Identification (read, no authentication)

- I-1. Model ("G7250"), MAC address (HIS-15), serial number if the hardware has one (HIS-15).
- I-2. Versions: main-unit firmware (running image and the other slot), boot loader, FPGA if
  present, hardware version. [G7250-MAN] shows that the stock product tracks FIRMWARE, FPGA
  and HARDWARE versions separately; which of these exist for our firmware is HIS-18.
- I-3. The result of the integrity check of the running and the other image (I1), and the
  update state (normal, trial boot, rolled back).
- I-3a. Whether a secret is set, and whether the first-secret window (S3) is open and for how
  long.
- I-4. Active level, owner of the RF chain (host IP and port, or none), and TX arm state
  (0011 point 2, 0015). Read-only here; arm is never set through this channel (S1).
- I-5. Uptime, last reset cause (HIS-13), and the protocol versions (management, P2,
  capability block 0003).
- I-6. Identification is also answered to a broadcast request, so a tool can find radios
  without P2 discovery.

#### Configuration (write needs authentication)

- C-1. Network: static or DHCP; address, netmask, gateway. The CH394Q holds these in its
  general registers (GWIP, SMIP, IP) [CH394] (sections 7.1.2, 7.1.3, 7.1.5).
- C-2. Level selection: default level at power-on, and a request to switch level now
  (0011). Level 2 is only selectable once it exists (after G6).
- C-3. Safety settings that may only be made stricter than the built-in limits: maximum TX
  time, power limit per band, SWR and temperature limits (0011 point 3, 0007). The built-in
  limits and the TX band edges per region [G7250-MAN] are not writable here.
- C-4. Configuration is validated as a whole before it is applied, stored in non-volatile
  memory with a version and a check value, and survives a restart (M5). A network change is
  applied after the reply is sent. If the radio cannot bring the new network configuration
  up, or detects an address conflict (GINT IP_CONFLI [CH394] section 7.1.7), it falls back
  to the previous configuration and logs it.
- C-5. A factory reset of the network configuration and secrets is possible over this
  channel (authenticated) and must also be possible locally without the network (HIS-17,
  HIS-19). Without a local path, a forgotten secret means the radio can only be reset by
  reflashing.

#### Logs (read; clear needs authentication)

- L-1. A ring buffer of events with an uptime timestamp in milliseconds, and wall-clock time
  only if the main unit knows it (the controller has a clock and a time server setting
  [G7250-MAN]; whether the main unit gets that time is HIS-17).
- L-2. At least: resets and their cause, safety-core trips and faults (0007), TX arm and
  disarm, host takeover (0007, 0015), level changes, configuration changes with the source
  address, every step of an update, authentication failures, port conflicts (point 2).
- L-3. Read in pages by sequence number, so a tool can fetch only new entries. Size and
  whether the log survives a reset depend on RAM and flash (HIS-18).

#### Firmware update (authenticated)

- U-1. **Preconditions.** An update is refused while the TX arm is set or the radio is
  transmitting. The owner disarms first; the management channel cannot disarm or key the
  radio for them (S1). Once an update starts, the radio leaves RUN state, refuses any new
  P2 RUN or arm, and stays in the receive-safe state of 0015 until it restarts.
- U-2. **Image.** One package per update with a header: magic, target hardware id and
  revision, component list (main firmware, FPGA image if any), versions, length, SHA-256
  [FIPS-180-4] over each component, and a signature field that is reserved and empty in this
  version (I1, I4). An image for other hardware is refused before anything is written.
- U-3. **Transfer.** In numbered blocks with a CRC-32 each, written to a staging area that
  is not the running image. A block out of order or with a bad CRC is rejected and asked for
  again. The transfer can be resumed after a break, and abandoned without effect on the
  running image.
- U-4. **Verification before activation.** The whole staged image is hashed and compared
  with the header (I1). No signature is checked in this version. Only then can the host ask
  for activation.
- U-5. **Activation.** Atomic: one write switches the boot choice to the new image. Power
  loss at any moment before that switch leaves the old image running; power loss after it
  leaves either the new image or, through U-6, the old one.
- U-6. **Trial boot and rollback.** The first boot of a new image is a trial. The image must
  confirm itself (safety-core self-test passed, network up, management channel answering)
  within a time to be set in spec part A. If it does not, or resets before confirming, the
  boot loader returns to the previous image and the log records the rollback. The host may
  also roll back on request.
- U-7. The boot loader is not updated through this channel in this version.
- U-8. Downgrades are allowed (owner control, 0018) only with an explicit "downgrade" flag in
  the request; without it, an image older than the running one is refused. A downgrade is
  logged (L-2). Configuration that the older image does not understand is kept but not used,
  and the reply says so (ON8ST, 2026-11-19).
- U-9. **Recovery.** There MUST be a way to load firmware when no working image is left, that
  does not depend on our firmware running: a boot loader that receives an image over the
  network, from the TF card, over USB, or over a debug port. Which one is HIS-19 (and
  HIS-17 for the TF card and USB on the controller).
- U-10. U-5 and U-6 need two image slots (or one slot plus a staging area large enough for
  a full image, and a boot loader that copies it safely). Whether the flash allows that is
  HIS-18 and HIS-19. If it does not, this decision is revisited: the fallback is a
  single-slot update with recovery only through U-9.

### Security on a LAN

- S1. **Management never keys the radio.** No request on this channel sets PTT, the TX arm,
  drive level or any RF output, and none loosens a safety limit (0011 point 3, 0015, 0007).
  The channel sits beside the levels, not above the safety core (`design-note.md`
  section 4). A conformance test in g7250-testbench checks that no management request
  changes the TX state (0001 item 5).
- S2. **Authentication for writes.** Configuration changes, level switches, log clearing,
  updates and rollbacks require a per-radio secret, proven by challenge and response: the
  radio issues a fresh random challenge, the host answers with HMAC-SHA256 [RFC2104],
  [FIPS-180-4] over the challenge and the request. The secret never crosses the network and
  a recorded exchange cannot be replayed. Reads (identification, logs, status) need no
  authentication.
- S3. **First secret** (F1; ON8ST, 2026-11-19). In factory state no secret is set. For a
  one-time window of a few minutes after the first power-on, or after a factory reset (C-5),
  the first host that sends a "set first secret" request sets it, first come, first served,
  without confirmation on the controller. The exact window length is fixed in spec part A.
  **Risk:** anyone on the LAN during that window can claim the radio and lock the owner out
  of every authenticated function. What remains to limit it:
  - the window is short and opens only once per factory state;
  - it opens only while no secret is set; once a secret is set, it never reopens without a
    factory reset;
  - the claim is logged with its source address (L-2);
  - identification shows whether a secret is set and whether the window is open (I-3a), so
    the owner sees whether the radio was claimed, and by whom in the log;
  - a factory reset (C-5) clears the secret and opens a new window, so an owner who was
    pre-empted can start over.
  Confirmation on the controller (F2) may be added later if HIS-17 allows it.
- S4. **Reach.** Requests are answered only from the radio's own subnet (source address
  within the configured netmask) and never from a broadcast source, except identification
  (I-6). Authentication failures are rate-limited and logged.
- S5. **One writer at a time.** A write session is held by one host (address and port) with
  an idle timeout. Other hosts get "busy" for writes and normal answers for reads.
- S6. Confidentiality is not provided in this version: traffic is in the clear on the LAN.
  Whether the processor can carry more (for example an encrypted session) is HIS-18.
- S7. P2 Set IP on port 1024 (point 6) is the one unauthenticated write, accepted exactly as
  P2 specifies. The risk is stated plainly: any host on the LAN that knows the radio's MAC
  (which the Discovery reply gives) can change its address, and so cut a running session.
  It cannot key the radio or change anything else (S1), and the change is logged.

### Socket budget

| Situation | Sockets |
|-----------|---------|
| Level 1 active, one receiver | 1024, 1025, 1026, 1027, 1029, 1035, register map (0005), management = 8 of 8 (0017) |
| Level 2 active (after G6) | management, plus whatever part C needs: TCI listener and clients, and port 1024 if P2 discovery stays answerable. With one connection per TCP socket [CH394] (section 7.2.2), the number of TCI clients is at most 8 − management − 1024 (if kept) − 1 free listener |
| Update in progress | management; other sockets may stay open but carry no RUN or TX (U-1) |

- The management socket is never closed to make room for another level.
- **DHCP.** A DHCP client needs a UDP socket while it talks, and none is free at level 1.
  Proposed: the DHCP exchange at power-on runs before the P2 sockets are opened; lease
  renewals borrow the management socket for the few seconds the exchange takes, during
  which management requests go unanswered and hosts retry (point 3). Static addressing
  needs no socket. To be fixed in spec part A; depends on HIS-14 (socket mode of the
  existing design).

## Consequences

- Spec part A gets a section "Management channel" with: the port number, the packet
  framing, request ids and status codes, the session and challenge/response, the four
  function groups, the update state machine (idle, receiving, staged, verified, activating,
  trial, confirmed, rolled back), and the timeouts.
- Spec part B states: Erase and Program on 1024 are ignored; the V3.8 checksum is not
  claimed; P2 Set IP is accepted exactly as P2 specifies (point 6); the guard against P2
  port relocation onto the management port (point 2).
- The capability block (0003) points to the management channel (port and protocol version),
  so a P2 host finds it.
- The watchdog and safety decision (0007) gets the rule that an update start drops the
  stream to the receive-safe state and that no management request changes TX state.
- The level-selection rules (0011, spec part A) are carried by C-2 and I-4.
- g7250-testbench gets conformance tests for: no TX change from any management request,
  update refused while armed, downgrade refused without the flag, first-secret window
  closing after its time and after a secret is set, rejected corrupt block, rejected
  wrong-hardware image, power
  loss at each update step (in the reference model), trial boot without confirmation leading
  to rollback, network fallback after a bad configuration.
- The AetherSDR backend does not need the management channel for M1–M4. A small separate
  tool (or a page in AetherSDR, needing a go from ON8ST) does updates and configuration. A
  browser interface, if ever made, is such a PC tool, not part of the firmware (T4).
- If signing is added later (I4), it uses the reserved signature field in the package
  header (U-2) and needs a new decision.
- M5 depends on HIS-17, HIS-18 and HIS-19 for U-9, U-10 and C-5.

## Open questions

For the HIS: the coordinator has added these to `open-questions-his.md`, including the new
HIS-20 (source of randomness); this file does not edit it.

- HIS-19 (existing): boot loader, recovery path, network loading. Also: can the boot choice
  be switched atomically, and can the boot loader detect an unconfirmed trial boot?
- HIS-18 (existing): flash size and layout (room for two images or one plus staging), RAM
  for a log buffer, whether an FPGA image is loaded by the main-unit firmware.
- HIS-17 (existing): can the main unit read the controller's TF card or USB, show a
  confirmation on the controller's screen, or receive a button press from it (F2 later,
  local factory reset)? Does the controller's own NETWORK page still write the main unit's
  network settings?
- HIS-15 (existing): a unique serial number besides the MAC address.
- HIS-14 (existing): does the existing design use socket mode, and is a DHCP client present?
- HIS-13 (existing): can the firmware read the cause of the last reset?
- HIS-20 (new): is there a source of randomness for challenges (S2) (hardware random
  generator or equivalent)?

## Resolved (ON8ST, 2026-11-19)

1. First secret in factory state: network window only, first come, first served, a few
  minutes after the first power-on or a factory reset, no confirmation on the controller
  (F1, S3). Controller confirmation (F2) is possible later, tied to HIS-17.
2. P2 Set IP on port 1024: accepted exactly as P2 specifies, no added conditions (point 6,
  S7). P2 Erase and Program stay ignored (point 5).
3. Downgrades: allowed with an explicit "downgrade" flag in the request, logged (U-8).
4. Browser interface: if ever, as a PC tool that speaks the UDP channel, not in the firmware
  (T4).
5. Firmware signing: none for now; integrity by SHA-256 per component and CRC-32 per block
  (I1). The package header reserves a signature field so signing can be added later (I4).

No questions for ON8ST remain open in this decision.

## Sources

- [P2] openHPSDR Ethernet Protocol V4.4: Discovery packet; Erase packet (byte 4 = 0x04, up
  to 15 s); Program packet (byte 4 = 0x05, bytes 5–8 number of blocks, bytes 9–264 data);
  Set IP Address packet (byte 4 = 0x03, bytes 5–10 MAC, bytes 11–14 address, 0.0.0.0 =
  DHCP); General packet bytes 5–32 (port settings, DDC0 base + 79); Discovery reply
  (byte 4 0x02/0x03, byte 11 board type, byte 13 firmware version); Command Reply packet
  (erase 0x03, program 0x04, byte 11 firmware version, byte 12 board type, bytes 13–14
  firmware checksum); revision history V3.8 (27 Mar 2019, 16-bit checksum); one-second C&C
  watchdog.
- [CH394] WCH CH394 manual 1, V1.2: sections 1–2 (protocols, 8 sockets, MACRAW), 6.1
  (Sn_KEEPALIVE), 7.1.2–7.1.5 (GWIP, SMIP, MAC, IP), 7.1.7 (GINT IP_CONFLI), 7.2.1 (Sn_MODE,
  MACRAW socket 0 only), 7.2.2 (Sn_CTRL: OPEN, LISTEN, CONNECT, CLOSE, SEND_KEEP), 7.2.4
  (Sn_STA), 7.2.5 (Sn_PORT).
- [G7250-MAN] Xiegu G7250 Operation Manual rev 0.1: controller interfaces (TF card slot,
  FAT32; USB), main-unit interfaces (LAN), System Information (APP, FIRMWARE, FPGA,
  HARDWARE), Time Setting, NETWORK Settings, Factory Reset, independent deployment of the
  main unit.
- [TCI] TCI protocol 2.1 (WebSocket over TCP), README.
- [FIPS-180-4] NIST FIPS 180-4, Secure Hash Standard (SHA-256). Public standard; not yet in
  `sources.md`.
- [RFC2104] HMAC: Keyed-Hashing for Message Authentication. Public; not yet in
  `sources.md`.
- Decisions 0001, 0003, 0005, 0007, 0009, 0011, 0015, 0016, 0017, 0018;
  `design-note.md`; `analysis/ch394-network-budget.md`; `open-questions-his.md` (HIS-13 to
  HIS-20).

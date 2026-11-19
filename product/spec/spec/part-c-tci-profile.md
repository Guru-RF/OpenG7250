# Part C — Level 2 and the G7250 TCI profile

- Version: draft 4 (rc1 candidate), 2026-11-19
- Status: draft 4 for review by ON8ST at rc1; the choices it applies are proposed in 0021
  (§18–§26 added for draft 3) and follow 0022 (proposed; §22–§32 applied in draft 4). Not yet merged into
  `spec/network-interface.md`.
- © 2026 ON8ST, CC BY 4.0 (see `LICENSE.md`); quoted TCI material © Expert Group LLC under its
  MIT notice.
- Builds on: 0011 (two levels, single owner, shared safety core, level 2 only after G6), 0012
  (full functionality), 0013 (AetherSDR), 0014 (one G7250 TCI profile), 0004 (rates), 0006
  (telemetry), 0007 (watchdog and safety), 0008 (management channel, socket budget), 0015 (TX
  arm), 0017 (no audio on the main unit), 0019 (reference model), 0021 (profile choices,
  proposed), 0022 (rc1 review fixes, proposed), and `spec/network-interface.md` draft 5
  (parts A and B; Table B8-3 is the single list of code names, 0022 §19).

Sources are cited by key (see `sources.md`) or by decision number (see `decisions/`).
Citations of [TCI] give the section of TCI Protocol 2.1 and the command name, for example
"[TCI] §4.2 DDS". Values that depend on an open question for the HIS or on gate G6 are
written with the HIS id or "G6" and are listed in Annex C-A. Design choices are recorded in
0021 and cited as "0021 §n". Statements marked **[unverified]** rest on an assumption that has
not been checked against a public source; the profile rule stands meanwhile, and they are
listed in Annex C-D.

**Notice for quoted material.** Short quotations from [TCI] in this part are taken from "TCI
Protocol, Ver. 2.1", September 2026, which carries this notice: "Copyright (c) 2023 "Expert
Group" LLC, Taganrog. Permission is hereby granted, free of charge, to any person obtaining a
copy of this software (the "Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to
do so, subject to the following conditions: The above copyright notice and this permission
notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE
IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."
Whether the notice must accompany short quotations is not settled; it is kept here to be safe
(`sources.md`, [TCI], Terms).

---

## C1 Scope and conformance language

C1.1 This part defines the **G7250 TCI profile**: the TCI version, the commands, arguments and
streams used, and the G7250 extensions (0014). It applies to two implementations (0014,
Decision):

- (a) **Level 1:** the TCI server of AetherSDR, when AetherSDR controls a G7250 over G7250-P2
  (0013, 0016). AetherSDR's TCI server announces protocol 2.1 [AETHER].
- (b) **Level 2:** the TCI server in the G7250 main-unit firmware, with DSP on board (0011
  point 1).

C1.2 Level 2 is built only after feasibility gate G6 (HIS answers on compute, memory and
network stack; 0011 point 4; design note §6). Milestone M6 covers receive, M7 transmit. Until
G6, every requirement in this part that is marked **(L2)** is a target, not a commitment.
Requirements marked **(L1)** apply to AetherSDR only. Unmarked requirements apply to both.

C1.3 "The server" means a conforming TCI server of either level. "A client" means a TCI client
connected to it. "The profile" means this part. "The safety core" means the watchdog, TX arm,
TX limits and fault state of 0007, which sit below both levels (0011 point 3).

C1.4 The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD
NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY" and "OPTIONAL" in this part are to be interpreted
as described in BCP 14 (RFC 2119, RFC 8174) when, and only when, they appear in all capitals,
as shown here (as in part B, B1.2).

C1.5 **Normative reference.** [TCI] Transceiver Control Interface, protocol 2.1, September
2026 (`sources.md`). The server MUST behave as [TCI] specifies for every command it supports,
unless this part states a deviation (C1.7). [TCI] describes the behaviour of ExpertSDR3; where
it names ExpertSDR3 as the server, the profile reads "the server".

C1.6 **Extensions.** [TCI] states that it "uses an extensible architecture and can be
supplemented with new functions and commands, while keeping the old ones operational", and
that "the extensibility of the TCI interface allows you to create an individual set of
commands and functions for each device model, while maintaining the basic command set inherent
to all transceivers" ([TCI] §1.4). G7250 functions that no TCI 2.1 command describes with
identical meaning are carried by G7250 extension commands (C5), all with the prefix `G7250_`.
A standard TCI command MUST NOT be given a G7250 meaning that differs from [TCI] (the same rule
as 0005 for P2). The reserved commands of [TCI] §4.6 MUST NOT be used for G7250 functions.

C1.7 **Deviations and clarifications.** Every deviation from [TCI] is stated where it applies
and listed in Annex C-B. Where [TCI] is silent or ambiguous, the reading the profile follows is
listed in Annex C-C.

C1.8 **Profile version.** This draft defines profile version `1`. The version is reported by
`G7250_PROFILE` (C5.3).

---

## C2 Transport

C2.1 The server MUST offer TCI as "a full duplex web socket protocol that runs on top of a TCP
connection", with the transceiver as the server ([TCI] §1.4). WebSocket is [RFC6455].

C2.2 Commands are ASCII strings ([TCI] §3.1) and MUST be sent in WebSocket text frames; stream
blocks ([TCI] §3.4) MUST be sent in WebSocket binary frames ([TCI] §3.4: "commands are
transmitted as strings and audio streams are transmitted as byte streams"). Clarification
(Annex C-C, C-C1): the server MAY put several complete commands in one text frame and MUST
accept several complete commands in one frame from a client; a command MUST NOT be split over
frames.

C2.3 No TLS and no WebSocket subprotocol are used. [TCI] defines neither. The server MUST
accept the HTTP upgrade on any request path and gives the path no meaning (0021 §17.1; Annex
C-C, C-C2).

C2.4 **Port.** [TCI] does not state a default TCP port (`sources.md`, [TCI]). The port MUST be
configurable. The default is **50001** on both levels (0021 §2). This is a profile choice,
not a TCI standard; it is the default of AetherSDR's TCI server ([AETHER-SRC], per
`annex-aethersdr.md` §2.4), so an application finds both levels on the same port. **(L2)** On
level 2 the port is set through the management channel configuration (0008). The port MUST NOT
collide with the management port or with port 1024 (0008, Transport point 2). **(L1)** On
level 1 the port is set in AetherSDR.

C2.4.1 **Reach (L2).** The server MUST accept TCI connections only from source addresses
inside the radio's own subnet (as 0008 S4), and, when the TCI allow-list is not empty, only
from addresses that match it. The allow-list holds up to 8 IPv4 addresses or prefixes and is
set through the management channel as an authenticated configuration write (0008 S2; 0021
§10). A refused connection MUST be closed without the WebSocket handshake and logged with its
source address (0008 L-2). **(L1)** AetherSDR SHOULD offer an equivalent restriction (0021
§10).

C2.5 **Number of clients, level 2.** The CH394Q has 8 hardware sockets [CH394], and each TCP
connection takes one socket (0008, Socket budget, [CH394] §7.2.2; `analysis/ch394-network-budget.md`,
Addendum, "TCI (level 2)"). While level 2 is active:

| Socket use | Sockets | Source |
|------------|---------|--------|
| Management channel, always reserved | 1 | 0008, Transport point 1 |
| P2 port 1024; discovery stays answerable on level 2 | 1 | 0003 (discovery reply byte 4); part B B3.1; 0021 §3 |
| Spare TCI listener, so that a further client can always be accepted and refused cleanly | 1 | 0008, Socket budget |
| TCI client connections | 5 | 8 − 3 |

- C2.5.1 **(L2)** The server MUST serve **5** simultaneous clients (`clients_max` = 5; 0021
  §3), on the assumption of C2.5.3; if HIS-14 shows otherwise, the number is recomputed from
  the same table. The number MUST be reported in `G7250_PROFILE` (C5.3).
- C2.5.2 **(L2)** When all client sockets are in use, the server MUST accept the next
  connection on the spare listener, complete the WebSocket handshake, send
  `G7250_REFUSED:busy;` in a text frame, close with WebSocket status 1008 (RFC 6455 §7.4.1),
  and return the socket to listening. The extension command is sent before the opt-in of C5.2
  on purpose, because the connection ends at once.
- C2.5.3 **[unverified]** That a CH394Q socket in TCP server mode turns into the connected
  socket on accept, so that a new listener needs another socket, is assumed from how such
  socket chips generally work; [CH394] does not spell it out (`analysis/ch394-network-budget.md`,
  Addendum). To be checked in the full CH394 documentation (HIS-14).
- C2.5.4 DHCP lease renewal borrows the management socket (0008, Socket budget) and does not
  reduce the number of TCI clients.
- C2.5.5 **(L1)** AetherSDR runs on the host and is not bound by the CH394Q socket budget. It
  MAY serve any number of clients.

C2.6 **Throughput, level 2.** All TCI traffic crosses the same SPI link as level 1 traffic, so
the SPI design target of at most 60 % busy in the worst case applies (0004, Decision point 6;
`analysis/ch394-network-budget.md`, Addendum). The WebSocket framing and the TCI commands run
on the G7250 processor, not in the CH394Q; client frames are masked (RFC 6455 §5.3) and must be
unmasked by the processor (`analysis/ch394-network-budget.md`, Addendum; HIS-18, G6). Stream
budgets are in C6.4.

C2.7 **Level change.** **(L2)** The TCI server listens only while level 2 is the active level
(0011 point 2). Level selection is done through the management channel and part A (0011;
0008, C-2 and I-4; A2.5a), not over TCI. On a switch from level 2 to level 1, after step 2 of
A2.5a, the server MUST send, in this order (0021 §25; 0022 §9):

1. if keyed: unkey, and the unkey broadcast of C7.7 (`TRX:0,false;`, `TUNE:0,false;`);
2. if armed: disarm with reason `LEVEL_CHANGE` (0007, drop event 10), then
   `G7250_TX_ARM_STATE` and the new `G7250_TX_ARM_TOKEN` to opted-in clients, and
   `TX_ENABLE:0,false;` to all clients (A2.5a step 3);
3. no further stream blocks; `G7250_STREAM_STATE` `stopped`, reason `level_change`, for each
   stream that was running, to the client that had it (A2.5a step 4);
4. `G7250_PROFILE` with `active` false to opted-in clients (C5.3);
5. a WebSocket close with status 1001 "going away" on every connection (RFC 6455 §7.4.1);
   then the listener closes (A2.5a step 6).

**(L1)** On a switch from level 1 to level 2, AetherSDR receives the P2 drop `LEVEL_CHANGE`
before port 7250 closes (A2.5a step 3), sends items 1–4 to its TCI clients, and keeps its TCI
connections open (0021 §25).

---

## C3 Initialization

C3.1 On every new connection the server MUST send the initialization commands of [TCI] §4.1,
then `READY;`, and then the current state of every supported bidirectional parameter ([TCI]
§3.1: "the client receives the current status ... first sending initialization commands, then
parameters to set the status"; [TCI] §4.1 READY: "Sent after the initialization commands").

C3.2 Initialization commands and their G7250 values, in this order:

| # | Command | G7250 value | Status | Source / reason |
|---|---------|-------------|--------|-----------------|
| 1 | `PROTOCOL:ExpertSDR3,2.1;` | the same on both levels; arg1 is a compatibility value, not an identification of the G7250 | MUST | [TCI] §4.1 PROTOCOL ("arg1 — program name", "arg2 — version of the protocol"); [AETHER-SRC] (AetherSDR sends this value, `annex-aethersdr.md` §2.4); 0021 §4 |
| 2 | `DEVICE:<name>;` | (L2) `G7250` MUST; (L1) `G7250` SHOULD, AetherSDR MAY keep `AetherSDR` where a client needs it | MUST | [TCI] §4.1 DEVICE; [TCI] §1.4 ("maintaining the device model designation"); [AETHER-SRC] (`device:AetherSDR` for WSJT-X behaviour, `annex-aethersdr.md` G-13); 0021 §5. Clients recognise the profile by `G7250_EXT` (C5.1.3), not by `DEVICE`. |
| 3 | `RECEIVE_ONLY:<bool>;` | `false` when transmit is implemented and enabled; `true` on level 2 before M7, and on level 1 if AetherSDR's G7250 backend cannot transmit yet | MUST | [TCI] §4.1 RECEIVE_ONLY; design note §6 (M6/M7, M4); 0012 (RX-only only as an intermediate milestone) |
| 4 | `TRX_COUNT:1;` | 1 | MUST | [TCI] §4.1 TRX_COUNT; one transmitter [G7250-MAN] (0007, rule 4); one receiver per the start brief, TBD (HIS-02) |
| 5 | `CHANNELS_COUNT:2;` | 2 (channel A and B in receiver 0) | MUST | [TCI] §4.1 CHANNELS_COUNT. Channel B is needed as the split TX frequency (C4, SPLIT_ENABLE). Whether channel B can also be demodulated is separate (C4, RX_CHANNEL_ENABLE). The old name `CHANNEL_COUNT` MUST NOT be sent ([TCI] §4.1 note). |
| 6 | `VFO_LIMITS:500000,54000000;` | 0.5–54 MHz | MUST | [TCI] §4.1 VFO_LIMITS; receive range 0.5–30 MHz and 50–54 MHz [G7250-MAN]. VFO_LIMITS has a single range, so 30–50 MHz is inside it but not receivable; see C3.3. |
| 7 | `IF_LIMITS:<-f>,<+f>;` | ± half the receiver bandwidth in use, TBD (L2: G6, HIS-01; L1: AetherSDR's DSP) | MUST | [TCI] §4.1 IF_LIMITS ("for VFOA only"; "Sent when you connect a device or change the sample rate") |
| 8 | `MODULATIONS_LIST:...;` | see C3.4 | MUST | [TCI] §4.1 MODULATIONS_LIST; modes [G7250-MAN] |
| 9 | `READY;` | — | MUST | [TCI] §4.1 READY |

C3.3 **Frequencies outside the receive range.** A `VFO` or `DDS` set request whose frequency
lies in 30–50 MHz (outside the receive range of [G7250-MAN]) or outside `VFO_LIMITS` MUST be
treated as not applicable: the server MUST NOT tune there and MUST reply with the current value
(the same pattern [TCI] uses for unsupported values, for example §4.3 IQ_SAMPLERATE note).
Listed as a clarification (Annex C-C, C-C3).

C3.4 **Modulation list.** [TCI] does not give a complete list of mode names; the names below are
those that appear in [TCI] (§4.1 MODULATIONS_LIST example "AM,LSB,USB,FM", §4.2 MODULATION
example "NFM", §4.2 RX_BIN_ENABLE note "AM, LSB, USB, CW and NFM", §4.2 DIGL_OFFSET/DIGU_OFFSET,
§3.4 "DIGL/DIGU"). The G7250 modes are CW, AM, SSB, FM, WFM [G7250-MAN].

| TCI name | G7250 mode [G7250-MAN] | RX | TX | TX mode class (C5.6) | Status |
|----------|-------------------------|----|----|----------------------|--------|
| `AM` | AM | yes | yes, 25 W max [G7250-MAN] | `am` | MUST (0021 §6) |
| `LSB`, `USB` | SSB | yes | yes, 100 W [G7250-MAN] | `ssb` | MUST (0021 §6) |
| `CW` | CW | yes | yes, 100 W [G7250-MAN] | `cw` | MUST (0021 §6) |
| `NFM` | FM (narrow) | yes | yes, 100 W ("NFM" in [G7250-MAN] TX power) | `fm` | MUST (0021 §6, §13) |
| `WFM` | WFM | yes | **no**: no WFM transmit power is given in [G7250-MAN] | `none` (arm and TX refused) | SHOULD (L2: G6, compute; 0021 §6) |
| `DIGL`, `DIGU` | SSB used for data modes | yes | yes, 100 W [G7250-MAN] | `ssb` | SHOULD ([TCI] §4.2 DIGL_OFFSET; 0021 §6) |

The narrow FM mode is announced as `NFM`; a set request with `FM` (the name in the [TCI] §4.1
example) MUST be accepted as `NFM`, and the reply is `NFM` (0021 §13). Mode names are sent in
upper case; set requests are case-insensitive ([TCI] §3.1).

C3.5 **G7250 extension state.** Extension commands are not part of initialization. They are
sent only to a client that has opted in (C5.2), so that generic clients see only standard
TCI 2.1 traffic.

---

## C4 Command subset

C4.1 The table lists every TCI 2.1 command of [TCI] §4 and its status in the profile.
"Supported" commands MUST behave as [TCI] specifies, with the G7250 notes given. For a command
marked NOT SUPPORTED, the server MUST ignore it without a reply, as [TCI] does for an unknown
command ([TCI] §4.7 note 5), and MUST NOT send it. For a MAY or SHOULD command that a server
does not implement, the same rule applies, and the server MUST list what it implements in
`G7250_FEATURES` (C5.4), so a client can discover it (0014, Consequences).

C4.2 "trx" is the transceiver number, always 0 (`TRX_COUNT:1`); "ch" is the channel, 0 (A) or
1 (B). Commands with a trx or receiver number out of range are ignored ([TCI] §4.7 note 5).

### Device and frequency

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `START` | MUST | Starts receive. On level 1, AetherSDR maps it to its P2 session start. | §4.2 START |
| `STOP` | MUST | Stops the device. Unkeys and drops the arm, reason `STOP` (analogue of P2 RUN cleared, 0007 drop event 2; Table B8-3 drop reason 13). (L1) AetherSDR clears the P2 run bit (High Priority byte 4 bit [0] [P2]); the radio's drop `RUN_CLEARED` unkeys first (A3.2), and AetherSDR reports `STOP`, not `RUN_CLEARED`, to its TCI clients (0022 §32). | §4.2 STOP |
| `DDS` | MUST | Receiver centre frequency. Range C3.3. Moves the effective TX frequency when the channel frequency follows it; changes while keyed: C7.6. | §4.2 DDS |
| `IF` | MUST | Offset of channel A/B within the receiver passband, inside `IF_LIMITS`. For the TX channel it moves the effective TX frequency; changes while keyed: C7.6. | §4.2 IF |
| `VFO` | MUST | Channel frequency (= DDS + IF). Range C3.3. Changes while keyed: C7.6. | §4.2 VFO |
| `RX_ENABLE` | MUST | Only trx 0, always `true`; "The first transceiver is always enabled". | §4.5 RX_ENABLE |
| `RX_CHANNEL_ENABLE` | MUST for ch 0; MAY for ch 1 | Ch 0 is always enabled. Demodulating ch 1 at the same time needs a second demodulator (L2: G6). If not implemented, a set to `true` for ch 1 is refused with a reply `RX_CHANNEL_ENABLE:0,1,false;`. | §4.2 RX_CHANNEL_ENABLE |
| `LOCK` | MAY | Tuning lock; synchronised state only. | §4.2 LOCK |
| `VFO_LOCK` | MAY | Notification, server to client. | §4.4 VFO_LOCK |
| `TX_FREQUENCY` | MUST | Sent on every change of the effective TX frequency (channel A, or channel B with split, plus the XIT offset when XIT is on; the commands that move it are listed in C7.6.1). | §4.4 TX_FREQUENCY |

### Mode and filters

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `MODULATION` | MUST | Names of C3.4; one mode per receiver, shared by channels A and B ([TCI] §4.2 MODULATION arg1). Sets the TX mode class (C5.6). Refused while keyed (C7.6). | §4.2 MODULATION |
| `RX_FILTER_BAND` | MUST | Demodulator passband. | §4.2 RX_FILTER_BAND |
| `DIGL_OFFSET`, `DIGU_OFFSET` | SHOULD | Required if `DIGL`/`DIGU` are in the modulation list. | §4.2 DIGL_OFFSET, DIGU_OFFSET |
| `AGC_MODE` | SHOULD | At least `normal` and `off`; `fast` MAY. Unknown modes ignored. | §4.2 AGC_MODE |
| `AGC_GAIN` | MAY | -20…120 dB. | §4.2 AGC_GAIN |
| `RX_NB_ENABLE`, `RX_NB_PARAM` | MAY | L2: G6 (compute). | §4.2 |
| `RX_NR_ENABLE`, `RX_ANC_ENABLE`, `RX_ANF_ENABLE`, `RX_APF_ENABLE`, `RX_DSE_ENABLE`, `RX_NF_ENABLE`, `RX_BIN_ENABLE` | MAY | L2: G6. Mode restrictions as in [TCI]. | §4.2 |
| `SQL_ENABLE`, `SQL_LEVEL` | SHOULD | Squelch; applies to the RX audio stream (C6). | §4.2 SQL_ENABLE, SQL_LEVEL |

### Split, RIT, XIT

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `SPLIT_ENABLE` | SHOULD | TX on channel B frequency. The TX frequency limit (`LIMIT_TX_FREQ`, Table A3-2) applies to the effective TX frequency. Changes while keyed: C7.6. | §4.2 SPLIT_ENABLE |
| `RIT_ENABLE`, `RIT_OFFSET` | SHOULD | RX only; no TX effect. | §4.2 RIT_ENABLE, RIT_OFFSET |
| `XIT_ENABLE`, `XIT_OFFSET` | SHOULD | The XIT offset is part of the effective TX frequency for the TX frequency limit (`LIMIT_TX_FREQ`, Table A3-2). Changes while keyed: C7.6. | §4.2 XIT_ENABLE, XIT_OFFSET |

### Transmit

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `TX_ENABLE` | MUST | Server-controlled; `true` only if C5.5.6 holds. A client set is ignored and the current state is replied ([TCI] §4.3 note). | §4.3 TX_ENABLE |
| `TRX` | MUST (M7 on L2) | `TRX:0,true,tci;` keys with TX audio from the client's TCI stream. `TRX:0,true;` (microphone) and `mic1`/`mic2`/`micpc`/`ecoder2`: refused unless a microphone path exists (HIS-17); refused means the server replies `TRX:0,false;`. Every key needs the arm (C5.5) and follows the key rule of A3.1a: a refused `TRX` is not latched (0022 §24). Keyed liveness: C8.2 (in `CW`, a client that has not opted in is bound by the 1 s generic keyed window). | §4.2 TRX |
| `TUNE` | MUST (M7 on L2) | Tune carrier at `TUNE_DRIVE`, under the arm. It does **not** start the internal ATU: the meaning is not identical (as P2 TUNE, 0007 Sub-decision 6). ATU tuning is `G7250_ATU_TUNE` (C5.7). A client that has not opted in is bound by the 1 s generic keyed window unless it sends application frames (C8.2; 0021 §18). | §4.2 TUNE |
| `DRIVE` | MUST | 0–100. Mapping to power TBD (HIS-12). A `REDUCE` limit action lowers power on the radio side (A3.3, A3.4a: drive lowered for forward power and supply, fixed caps `P_swr` and `P_temp` for SWR and PA temperature) and does not change the `DRIVE` or `TUNE_DRIVE` value (0007, Sub-decision 4 rule 4; 0021 §21). | §4.2 DRIVE |
| `TUNE_DRIVE` | MUST | 0–100, as `DRIVE`. | §4.2 TUNE_DRIVE |
| `TX_FOOTSWITCH` | SHOULD | Reports a PTT input that reaches the main unit (controller microphone PTT, HIS-17). It never keys by itself, on either level (0007, Sub-decision 6; 0021 §9; C7.3). | §4.4 TX_FOOTSWITCH |
| `MON_ENABLE`, `MON_VOLUME` | MAY | TX monitor in the RX audio stream. | §4.2 MON_ENABLE, MON_VOLUME |

### Streams

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `IQ_START`, `IQ_STOP` | MUST | Receiver 0 only. Budget C6.4. | §4.3 IQ_START, IQ_STOP |
| `IQ_SAMPLERATE` | MUST | 48000, 96000, 192000, 384000 as [TCI] lists; 384000 only where 0004 point 6 allows it. Unsupported value: ignored, current rate replied ([TCI] §4.3 note). | §4.3 IQ_SAMPLERATE |
| `AUDIO_START`, `AUDIO_STOP` | MUST | RX audio of receiver 0. | §4.3 AUDIO_START, AUDIO_STOP |
| `AUDIO_SAMPLERATE` | MUST | 48000 MUST; 8000, 12000, 24000 MUST on L1, SHOULD on L2 (G6). Applies to RX and TX audio of this client ([TCI] §4.3 note). | §4.3 AUDIO_SAMPLERATE |
| `AUDIO_STREAM_SAMPLE_TYPE` | MUST | int16, int24, int32, float32; default float32 ([TCI] §4.3 note). | §4.3 AUDIO_STREAM_SAMPLE_TYPE |
| `AUDIO_STREAM_CHANNELS` | MUST | 1 or 2; default 2. | §4.3 AUDIO_STREAM_CHANNELS |
| `AUDIO_STREAM_SAMPLES` | MUST | 100…2048; defaults per rate as [TCI]. | §4.3 AUDIO_STREAM_SAMPLES |
| `TX_STREAM_AUDIO_BUFFERING` | MUST (M7 on L2) | 50…500 ms; default 50 ms. | §4.3 TX_STREAM_AUDIO_BUFFERING |
| `LINE_OUT_START`, `LINE_OUT_STOP` | MAY | Duplicate of the RX audio stream ([TCI] §3.4). L2: budget C6.4. | §4.3 LINE_OUT_START, LINE_OUT_STOP |
| `LINE_OUT_RECORDER_START`, `_SAVE`, `_BREAK` | NOT SUPPORTED on L2; MAY on L1 | Needs a file system on the server; the main unit has none that is known (HIS-18). | §4.3 |
| `VOLUME`, `MUTE`, `RX_MUTE`, `RX_VOLUME`, `RX_BALANCE` | MAY | L2: the main unit cannot play audio (0017); if supported, the values are synchronised and MUST NOT change the level of the TCI RX audio stream (0021 §17.2; [TCI] does not say whether ExpertSDR3 applies them to the stream). | §4.2 |

### Sensors

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `RX_SENSORS_ENABLE` | MUST | Interval 30–1000 ms. | §4.4 RX_SENSORS_ENABLE |
| `RX_SENSORS`, `RX_CHANNEL_SENSORS` | MUST, MAY for ch 1 | Signal level in dBm in the RX filter. L2: calibration TBD (HIS-11). | §4.4 RX_SENSORS, RX_CHANNEL_SENSORS |
| `TX_SENSORS_ENABLE` | MUST (M7 on L2) | Interval 30–1000 ms. | §4.4 TX_SENSORS_ENABLE |
| `TX_SENSORS` | MUST (M7 on L2) | arg2 "microphone signal level, dBm": RMS level of the TX audio in use in dB relative to full scale of the TCI TX audio stream, `-140` without TX audio (no microphone on the main unit, 0017; 0021 §15). arg3 RMS output power in W: the forward power averaged over the sliding 100 ms window of A3.4c; arg4 peak output power in W: the PEP over the same window, or the mean if the detector gives no PEP (HIS-11); arg5 SWR: the value the safety core uses (`TLM_SWR`). All are the safety core's own values (A3.4c; 0006; 0022 §17; 0021 §21). | §4.4 TX_SENSORS |
| `HW_SENSORS_ENABLE`, `HW_SENSORS` | SHOULD | Supply voltage V, current A, temperature °C from the 0006 telemetry (supply voltage, PA or supply current, PA temperature), HIS-11. A sensor that does not exist is reported as `0` and flagged absent in `G7250_FEATURES` (C5.4). | §4.5 HW_SENSORS_ENABLE, HW_SENSORS |

### CW

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `CW_MACROS`, `CW_MSG` | SHOULD | Text to CW, generated in the server. Each start of transmission is a TX request under the arm (C5.5). Text received while it cannot key (unarmed, inhibited, refused) is discarded, not queued (A3.1a; 0022 §24). While the text is sent, the CW text liveness of C8.2 applies (0022 §25). | §3.2, §4.5 CW_MACROS, CW_MSG |
| `CW_MACROS_STOP` | MUST | Accepted from any client; unkeys at once. | §4.5 CW_MACROS_STOP |
| `CW_TERMINAL` | SHOULD | Terminal mode keeps TX keyed after the macro; still bound by the maximum TX time and the keyed liveness of C8.2 (keyed timeout for an opted-in client, 1 s generic keyed window otherwise; 0021 §18). | §3.2.1, §4.5 CW_TERMINAL |
| `CW_MACROS_EMPTY`, `CALLSIGN_SEND`, `CW_MON` | SHOULD | Notifications, as [TCI]. | §4.5 |
| `CW_MACROS_SPEED`, `CW_MACROS_SPEED_UP`, `CW_MACROS_SPEED_DOWN`, `CW_MACROS_DELAY` | SHOULD | As [TCI]. | §4.2, §4.3 |
| `CW_KEYER_SPEED` | SHOULD | Keyer for the KEY input on the controller, if it reaches the main unit (HIS-17). | §4.2 CW_KEYER_SPEED |
| `KEYER` | MAY | Client-timed CW key. First press is a TX request under the arm. Every `KEYER` command is an application frame (C8.2); a key-down from a client that has not opted in ends after the 1 s generic keyed window without a further frame (0021 §18). A key-down held for more than 1 s without a key-up ends from every client, opted in or not, whatever frames it sends (key-down cap, C8.2; part B B10.5a; `unkey` 9; 0022 §25). Jitter over TCP/WebSocket on level 2: TBD (G6). | §4.4 KEYER |

### Spots, focus, panels, reserved

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `SPOT`, `SPOT_DELETE`, `SPOT_CLEAR` | MAY on L2, SHOULD on L1 | L2 has no panorama of its own; spots MAY be stored and relayed. AetherSDR has a panorama. | §4.3 SPOT, SPOT_DELETE, SPOT_CLEAR |
| `CLICKED_ON_SPOT`, `RX_CLICKED_ON_SPOT` | MAY on L1; NOT SUPPORTED on L2 | No panorama on L2. | §4.4 |
| `APP_FOCUS`, `SET_IN_FOCUS` | MAY on L1; NOT SUPPORTED on L2 | No application window on L2. | §4.4 APP_FOCUS, SET_IN_FOCUS |
| `ECODER_SWITCH_RX`, `ECODER_SWITCH_CHANNEL` | NOT SUPPORTED | No E-Coder panel. | §4.5 |
| `PREAMP`, `PREAMP_PARAM`, `CTCSS_*`, `RX_NF_PARAM`, `RX_SMETER`, `TX_POWER`, `TX_SWR` | MUST NOT be sent or accepted | Reserved: "the TCI server does not accept or send them" ([TCI] §4.6). Front-end control: `G7250_PREAMP`, `G7250_ATT` (C5.9). | §4.6 |

C4.3 **Parameter monopoly and tick.** The server MUST apply the 200 ms monopoly (500 ms for CW
speed and delay) and the 30 ms notification tick of [TCI] §4.7 notes 6 and 7. The safety core
is never subject to the monopoly: a disarm, an unkey or a `CW_MACROS_STOP` takes effect
immediately (C7.4).

---

## C5 G7250-specific mapping and extension commands

### C5.1 Rules for extensions

C5.1.1 An extension command has the form of [TCI] §3.1 (`NAME:arg1,arg2;`, reserved characters
`:`, `,`, `;`, case-insensitive), with a name that starts with `G7250_`. Logical arguments
follow [TCI] §4.7 note 3; enumerations are lower-case words; hexadecimal values are exactly 8
hex digits, case-insensitive.

C5.1.2 Extension commands follow the four TCI command types of [TCI] §3.3. For each one, the
type is given. Bidirectional extension state is synchronised to all opted-in clients, as [TCI]
§3.1 does for standard commands.

C5.1.3 A client that talks to a server without the profile gets no reply to an extension
command, because "an unknown command" is "ignored without a reply" ([TCI] §4.7 note 5). A
client recognises a profile server by the reply to `G7250_EXT` (C5.2), not by `DEVICE` or
`PROTOCOL` (0021 §4, §5).

C5.1.4 Every extension MUST have the same meaning on both levels (0014), and MUST be
implemented on both levels, except: an extension whose hardware is not yet known MAY be
absent until the HIS answers (`G7250_ANT` HIS-06, `G7250_ATU` selection HIS-08,
`G7250_PREAMP` and `G7250_ATT` HIS-07) and, on level 1, until a part B register or field
carries it (part B B7, B8.3: group 5 has only the read-only `ANT_STATE`, group 6 is reserved,
the Alex words and step attenuator are ignored until HIS-06 and HIS-07). The server MUST
announce what is present through `G7250_FEATURES` (C5.4); an absent extension command is
ignored without a reply, as an unknown command ([TCI] §4.7 note 5) (0021 §23). Where level 1
maps an extension onto G7250-P2, the mapping is given.

### C5.2 Opt-in: `G7250_EXT`

- Type: bidirectional, but per client (the only bidirectional extension that is not
  synchronised).
- Set: `G7250_EXT:<bool>;`. Reply: `G7250_EXT:<bool>;`.
- After `G7250_EXT:true;` the server MUST send to that client, in this order:
  `G7250_PROFILE`, `G7250_FEATURES`, and the current state of every extension it implements,
  and from then on every extension notification. Before the opt-in, and after
  `G7250_EXT:false;`, the server MUST NOT send extension commands to that client, except
  `G7250_REFUSED` (C2.5.2).
- Reason: [TCI] does not say how a client treats an unknown command from the server
  **[unverified for existing clients; Annex C-D]**; the opt-in keeps generic clients on pure
  TCI 2.1.
- Extension set requests from a client that has not opted in MUST still be accepted.

### C5.3 Identification and active level: `G7250_PROFILE`

- Type: notification. `G7250_PROFILE:<profile>,<level>,<active>,<clients_max>;`
- `profile`: profile version, `1` for this draft (C1.8). `level`: `1` (AetherSDR over
  G7250-P2) or `2` (firmware). `active`: `true` if this level currently owns the RF chain
  (0011 point 2). `clients_max`: C2.5 (L1: `0` = no fixed limit).
- (L1) `active` is `true` while AetherSDR has a running G7250-P2 session; it becomes `false`
  when the radio changes to level 2 or the session is taken over (0007, drop events 4 and 10).
- (L2) While the server is listening, level 2 is active; `active:false` is sent only just
  before closing on a level change (C2.7).
- The level is also reported in the capability block and the management channel (0011 point 2;
  part B B4).

### C5.4 Discovery of optional functions: `G7250_FEATURES`

- Type: notification. `G7250_FEATURES:<token>,<token>,...;` lists what this server implements
  (0014, Consequences: "a way for the application to discover which ones are available").
- Tokens (profile 1): `tx`, `iq`, `audio`, `audio_rates_all`, `line_out`, `ch_b_rx`, `split`,
  `rit`, `xit`, `cw_text`, `cw_keyer`, `keyer`, `agc`, `nb`, `nr`, `anc`, `anf`, `apf`, `dse`,
  `nf`, `bin`, `sql`, `wfm`, `dig`, `spots`, `atu` (ATU tune and `G7250_ATU_STATE`),
  `atu_select` (`G7250_ATU` settable), `ant` (`G7250_ANT` settable), `ant_state` (`G7250_ANT`
  reported only), `preamp`, `att`, `hw_sensors`, and
  `absent_<sensor>` for each `HW_SENSORS` field without a sensor (`absent_voltage`,
  `absent_current`, `absent_temperature`).
- A token appears only if the function works now; for example `tx` is absent on level 2
  before M7, and on level 1 `ant`, `atu_select`, `preamp` and `att` are absent until HIS-06,
  HIS-07, HIS-08 and a part B register exist (C5.1.4; 0021 §23).

### C5.5 TX arm on TCI

C5.5.1 **Same safety core.** The arm, its preconditions, its drop events and the limits are
those of 0007, which sits below both levels (0011 point 3). TCI changes only how the arm is
requested and reported. A TCI client is never the P2 owner: on level 1 the P2 owner is
AetherSDR, which becomes the owner by its run bit or by a takeover (A2.3, A2.4; 0022 §3); on
level 2 the owner of the RF chain is the firmware's TCI level itself (0011 point 2), and the
TCI clients share control of it as [TCI] §3.1 describes. Code names on TCI are the Table B8-3
names, verbatim and in upper case as Table B8-3 writes them; part C's own enumerations, which
have no Table B8-3 name (states, TX sources, mode classes, stream reasons), are lower case
(part B B8.7; 0021 §22; 0022 §19, §32).

C5.5.2 **Why an arm on TCI at all.** [TCI] has no arm: `TX_ENABLE` is server-controlled
information ([TCI] §4.3 TX_ENABLE). Without an arm, any TCI client on the LAN could key 100 W.
The profile keeps the rule of 0015: only software that knows the G7250 can enable transmit.
Once armed, generic TCI clients may key with the standard commands (`TRX`, `TUNE`, CW), which
is what full functionality for third-party applications needs (0012), unless the TX policy
restricts keying to the arm holder (C5.5.8). This matches level 1, where AetherSDR arms over
P2 and its TCI clients key through AetherSDR (0021 §1).

C5.5.3 **Commands.**

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_TX_ARM_TOKEN` | notification | `G7250_TX_ARM_TOKEN:0,<hex8>;` | Current token; never `00000000`, `FFFFFFFF` or `ARM_MAGIC` (with the token equal to `ARM_MAGIC` the arm value would be `00000000`, which disarms), different from the previous one (0007 Decision 1; part B B10.2 item 5). Sent on opt-in and whenever it changes. |
| `G7250_TX_ARM` | unidirectional control | `G7250_TX_ARM:0,<hex8>;` | `token XOR ARM_MAGIC` arms; `00000000` disarms. Any other value is rejected with `BAD_TOKEN`. `ARM_MAGIC` = `47375458` is the constant of part B (B8.6; 0007 Decision 1). A correct arm while already armed is a no-op (C5.5.5.1). |
| `G7250_TX_ARM_STATE` | notification | `G7250_TX_ARM_STATE:0,<state>,<generation>,<reject>,<drop>,<holder>;` | `state`: `disarmed`, `armed`, `inhibited` (armed, but a limit inhibit is active so TX requests do not key; no new generation; 0022 §13; part B `TX_ARM_STATE`). `generation`: +1 on every arm, 0–255, wraps. `reject`: last arm reject reason (Table B8-3, C5.5.6), `none` if none. `drop`: last drop reason (Table B8-3 or the TCI additions of C5.5.5), `none` if none. `holder`: `true` if this connection is the arm holder. Sent per client on every change. |
| `G7250_TX_STATE` | notification | `G7250_TX_STATE:0,<keyed>,<source>,<mine>,<inhibits>,<unkey>,<limit>;` | `keyed`: bool (PA actually keyed). `source`: `none`, `trx`, `tune`, `cw`, `keyer`, `atu`. `mine`: `true` if this connection made the current TX request. `inhibits`: hex8, bit *n* set while the limit with limit id *n* of Table B8-3 holds an inhibit (`LIMIT_PA_TEMP` above T3, `LIMIT_SUPPLY_VOLTAGE` over-voltage; Table A3-2), the bit numbering of `LIMIT_STATUS` bits 0–15. `unkey`: last unkey reason, the number of part B `TX_STATE` [23:16] (0 none, 1 TX request released, 2 keyed timeout, 3 TX IQ underrun, 4 limit, 5 arm dropped, 6 retune needs RF-path change, 7 PA disabled by the host, 8 keying client lost, 9 CW key-down longer than 1 s, 10 TX mode class changed while keyed), with the TCI causes of C8.2 (0022 §32). (L1) `inhibits` is the P2 `LIMIT_INHIBIT` register (Table B8-2; 0022 §32). `limit`: the limit id name (Table B8-3) when `unkey` is 4, else `none`. Sent per client on every change. |
| `G7250_KEEPALIVE` | unidirectional control | `G7250_KEEPALIVE;` | An application frame with no other effect and no reply (C8.2; 0021 §18). MUST be implemented. |

C5.5.4 **Procedure.** (1) The client opts in (C5.2) and receives the token. (2) It sends
`G7250_TX_ARM:0,<token XOR ARM_MAGIC>;`. (3) The server checks the value (else `BAD_TOKEN`)
and the preconditions (C5.5.6 items 1–7), and either pushes `G7250_TX_ARM_STATE` = `armed`
with a new generation or pushes the reject reason. (4) **After the confirmation, the radio keys only on a TX request that arrives
after it** (0007 Decision 1 rule 2); a `TRX` state that was already `true` does not key. Every
TX request follows the key rule of A3.1a: a 0→1 request at a moment when every key condition
holds; a request refused for any reason is not latched (0022 §24). (5) The
server sends `TX_ENABLE:0,true;` to all clients when C5.5.6 holds.

C5.5.5 **Arm holder and drop events.** The connection that armed is the **arm holder**. Each
drop unkeys first, then disarms, then issues a new token, then pushes `G7250_TX_ARM_STATE`
with the reason and `TX_ENABLE:0,false;` (0007 Decision 1 rule 5). Drop events on TCI:

| # | Event | Reason | 0007 drop event |
|---|-------|--------|-----------------|
| 1 | Any client sends `G7250_TX_ARM:0,00000000;` | `HOST_DISARM` | 1 |
| 2 | Any client sends `STOP;` | `STOP` (Table B8-3 drop reason 13); (L1) the P2 drop is `RUN_CLEARED` (C4, `STOP`) | 2 (RUN cleared) |
| 3 | The arm holder's connection closes (TCP close or reset, WebSocket close) | `HOLDER_LOST` (Table B8-3 drop reason 14) | 3 (analogue of the watchdog) |
| 4 | Connection watchdog: no frame of any kind, Pong included, from the arm holder for 1 s while armed (C8.2) | `WATCHDOG` | 3 |
| 5 | (L1) Any drop of the P2 arm between AetherSDR and the radio, with the P2 reason passed on unchanged | P2 reason | 1–13 |
| 6 | Any reset | `RESET` (state after reset: disarmed) | 5 |
| 7 | Entry into the fault state | `FAULT` | 6 |
| 8 | A limit trip with action `DISARM` or `FAULT` | `LIMIT_<name>` (limit id of Table B8-3) | 7 |
| 9 | Ethernet link down (HIS-14) | `LINK_DOWN` | 8 |
| 10 | Change of active level | `LEVEL_CHANGE` | 10 |
| 11 | Start of a firmware update, or a change of the persistent limits over the management channel (C-3; built-in limits are never writable, A3.4 rule 2; 0008; 0022 §6, §31) | `MAINTENANCE` | 11 |
| 12 | A TX path that must be blocked is found not blocked | `FAULT` | 13 |
| 13 | The arm holder sends `G7250_EXT:false;` | `HOST_DISARM` | 1 |

0007 drop events 4 (takeover), 9 (session change) and 12 (rediscovery) have no TCI equivalent on
level 2, because TCI has no session takeover; on level 1 they reach TCI through row 5 (C7.2.1).
The drop reasons `STOP` (13) and `HOLDER_LOST` (14) are listed in Table B8-3 as TCI-only drop
reasons, never set over P2 (0021 §22; 0022 §30); part C adds no code name of its own.

C5.5.5.1 **Holder rules** (0021 §24).

1. A valid `G7250_TX_ARM` from a client while another client holds the arm MUST be a no-op: no
   new generation, the holder stays the same, and the requester receives
   `G7250_TX_ARM_STATE` with `holder` false (as part B B10.2 item 5). A client can become the
   holder only after the arm has been dropped.
2. (L1) AetherSDR's own user interface and at most one TCI client can hold the arm at the same
   time; both map onto AetherSDR's single P2 arm. Rows 3, 4 and 13 end only the TCI client's
   holding, and unkey any transmission that client keyed; AetherSDR MUST write `TX_ARM` = 0
   over P2 only when no other holder remains, and otherwise the arm stays, with no new
   generation. Rows 1 and 2, AetherSDR's own disarm and
   every drop of row 5 end the arm for all holders.
3. After every drop, and every unkey that no client requested, the server sends the unkey
   broadcast of C7.7.

C5.5.6 **Conditions.** An arm request is accepted only if items 1–7 hold; `TX_ENABLE` is `true`
only if items 1–9 hold:

1. The device is started (`START`), (L1) AetherSDR has a running P2 session with the watchdog
   effectively on (0007 Decision 2.3; part B B10.2 item 3).
2. Not in fault (0007 Sub-decision 5; A3.5); no limit inhibit active (0007 Sub-decision 4;
   Table A3-2).
3. Not keyed, and the TCI `TRX` and `TUNE` states are `false` (0007 Decision 1 rule 1).
4. This level is the active level (0011 point 2): (L2) level 2; (L1) level 1.
5. No firmware update in progress (0008).
6. The TX mode class is defined (C5.6): the modulation of the TX channel is not `WFM`. Reject
   reason `NO_MODE_CLASS` (0007 Decision 1 rule 1).
7. Transmit is implemented (L2: M7; L1: M4).
8. Armed.
9. The effective TX frequency (C4, split and XIT) lies inside a transmit range of [G7250-MAN]
   for the configured region (`LIMIT_TX_FREQ`, Table A3-2; A1.6 C-6).

Reject reasons, the Table B8-3 names verbatim (0021 §22; 0022 §19):
`BAD_TOKEN` (wrong value, C5.5.3); `NOT_RUNNING` (item 1); `IN_FAULT` (item 2, fault);
`INHIBITED` (item 2, a limit inhibit while disarmed; 0022 §13); `PTT_ACTIVE` (item 3);
`LEVEL_NOT_ACTIVE` (item 4); `MAINTENANCE` (item 5, also during an unconfirmed trial boot,
0022 §10); `NO_MODE_CLASS` (item 6); `TX_NOT_IMPLEMENTED` (item 7). (L1) Any P2 reject reason
is passed on unchanged, including `WATCHDOG_DISABLED` (part B B10.2 item 3); on level 2 the
connection watchdog of C8.2 is always on, so `WATCHDOG_DISABLED` is not used. `NOT_OWNER` is
not used on TCI (Table B8-3: reserved).

C5.5.7 **(L1) Mapping.** AetherSDR generates its own TCI token and keeps its own TCI arm
state. A valid `G7250_TX_ARM` from a TCI client makes AetherSDR perform the P2 arm handshake
(0007 Decision 1) and confirm on TCI only after the radio has confirmed on P2. AetherSDR MAY
also arm from its own user interface; that counts as an arm by a holder that never disconnects
while AetherSDR runs. Several arm sources follow C5.5.5.1 item 2 (0021 §24). Listed for the
annex "Changes needed in AetherSDR" (0014, Consequences; `annex-aethersdr.md` G-13).

C5.5.8 **TX policy: `G7250_TX_POLICY`** (0021 §1).

- Type: bidirectional, synchronised to opted-in clients. `G7250_TX_POLICY:<any|holder>;` (set,
  reply), `G7250_TX_POLICY;` (read). Default `any`.
- `any`: while armed, every client MAY send a TX request (C7.4). `holder`: only the arm holder
  MAY; a TX request from another client is refused as in C7.5 item 2.
- Any opted-in client MAY set `holder`. Only the arm holder MAY set `any`; a set to `any` from
  another client is ignored and the current value is replied (tighten only, as 0007
  Sub-decision 4 rule 1).
- The policy returns to `any` when the last client disconnects, on a level change and on reset,
  as tightened limits do (C5.10.1), and whenever no arm holder remains: at every drop or disarm
  (C5.5.5; 0021 §24). A new arm therefore always starts with policy `any`.
- Stop requests (C7.4) are accepted from every client under either policy.
- (L1) AetherSDR implements the policy in its own TCI server. When AetherSDR armed from its own
  user interface, it is the arm holder, so `holder` means that only AetherSDR's user interface
  keys.

### C5.6 TX mode class: `G7250_TX_MODE_CLASS`

- Type: notification. `G7250_TX_MODE_CLASS:0,<class>;`, `class` one of `cw`, `ssb`, `am`, `fm`,
  `none`: the lower-case form of the `TX_MODE_CLASS` values of part B (B10.3: 1 SSB, 2 CW,
  3 AM, 4 FM; `none` for 0), a part C enumeration, since Table B8-3 gives these values no code
  names (0007, Sub-decision 4 rule 3; 0021 §14, §22).
- On TCI the class is **derived by the server** from `MODULATION` of receiver 0 by the table
  of C3.4, never declared by a client (0021 §6).
- With class `none` (`WFM`), an arm request is rejected with `NO_MODE_CLASS` (C5.5.6 item 6).
  If `MODULATION` changes to `WFM` while armed and not keyed, the arm is kept, TX requests are
  refused (`TRX:0,false;`, `TUNE:0,false;`) and `TX_ENABLE` becomes `false` (0021 §6). On level 2 the DSP is on board, so the radio knows the mode
  (0011 point 1); the reason for a declared class on level 1, that the radio does not know the
  host's mode (0007, Sub-decision 4 rule 3), does not apply.
- (L1) AetherSDR MUST write the derived class to `TX_MODE_CLASS` over P2 before arming and on
  every change of the TX modulation (0007, Sub-decision 4 rule 3).
- The 25 W AM limit applies whenever the class is `am` ([G7250-MAN]; 0007); it is carrier
  power, measured as the 100 ms mean, with PEP also held to 100 W (A3.4c; 0022 §17). The 100 W
  limit of the other classes applies to PEP. The power measurement applies whatever the class
  (part B B10.3).

### C5.7 ATU

TCI 2.1 has no ATU command; `TUNE` is a tune carrier ([TCI] §4.2 TUNE: "Switching between
receive and Tune modes"), not an ATU tune cycle.

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_ATU` | bidirectional | `G7250_ATU:0,<bypass\|inline>;` (set, reply), `G7250_ATU:0;` (read) | Internal ATU out of or in line ([G7250-MAN], ATU: short press switches the tuner in). Present only with token `atu_select` (C5.1.4); without it a set is answered with the value in force and `G7250_WRITE_STATUS` `READ_ONLY` when token `atu` is present, and ignored otherwise (0021 §23). Refused while keyed with `KEYED` (C7.6). |
| `G7250_ATU_TUNE` | unidirectional control | `G7250_ATU_TUNE:0;` | Starts a tune cycle (A3.9b; 0022 §22). A TX request under the arm, with its own tune profile and time limit (`LIMIT_ATU_TIME`; 0007 Sub-decision 4 rule 5, Sub-decision 6, "Internal ATU tuning"). Without the arm it is rejected with `G7250_WRITE_STATUS` `NOT_ARMED`; while keyed by any other source, from any client including the keying client, with `KEYED`; neither is latched (A3.1a). A repeated start while the cycle runs is a no-op. The tune power is set before RF and before any ATU relay moves; while tuning, a further `TRX`, `TUNE` or CW request neither keys nor ends the tune; the keyed liveness of C8.2 applies and ends the tune as `failed`; the cycle always ends unkeyed (part B B10.9; 0022 §14, §22). Refused (no key) if C5.5.6 does not hold. |
| `G7250_ATU_STATE` | notification | `G7250_ATU_STATE:0,<state>;` | `bypass`, `inline`, `tuning`, `tuned`, `failed`: part B `ATU_STATE` 0–4 (0006, "ATU state"). |

(L1) Mapped to the `ATU_TUNE` and `ATU_STATE` registers of group 4 (Table B8-2; token `atu`
when group 4 is present, HIS-08). Part B has no register for ATU selection, so `atu_select`
is absent on level 1 until one exists (0021 §23). Tune power TBD (HIS-08, HIS-12).

### C5.8 Antenna

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_ANT` | bidirectional | `G7250_ANT:0,<1\|2>;` (set, reply), `G7250_ANT:0;` (read) | ANT1 or ANT2 ([G7250-MAN], "ANT SELECT"). The reply reports the antenna actually selected (0006; part B `ANT_STATE`). Settable only with token `ant`; with token `ant_state` only, it is a notification and a set is answered with the value in force and `G7250_WRITE_STATUS` `READ_ONLY`; with neither, absent (C5.1.4; 0021 §23). Refused while keyed with `KEYED` (C7.6). Default after reset TBD (HIS-06; 0007 Decision 5). |

(L1) Part B group 5 has only the read-only `ANT_STATE` (Table B8-2) and the P2 Alex words
are ignored until HIS-06 (part B B7), so AetherSDR announces at most `ant_state` until a
writable register exists (0021 §23).

### C5.9 Front end (optional)

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_PREAMP` | bidirectional | `G7250_PREAMP:0,<bool>;` | Preamplifier, if it exists (HIS-07). The TCI `PREAMP` command is reserved ([TCI] §4.6) and so not used. Present only with token `preamp`. Refused while keyed with `KEYED` (C7.6). |
| `G7250_ATT` | bidirectional | `G7250_ATT:0,<dB>;` | Attenuation in dB, steps TBD (HIS-07). Present only with token `att`. Refused while keyed with `KEYED` (C7.6). |

Both are absent on both levels until HIS-07 is answered and, on level 1, a part B register
exists (group 6 is reserved, the step attenuator byte 1443 is TBD (HIS-07), part B B7, B8.3) (C5.1.4;
0021 §23).

### C5.10 Safety and fault state

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_SAFETY` | notification | `G7250_SAFETY:<state>,<fault_code>,<fault_class>,<fault_flags>,<trips>;` | The part B fault registers (Table B8-2; A3.5; 0021 §22). `state`: `normal` or `fault` (`SAFETY_STATE` 0, 1). `fault_code`: first cause, the Table B8-3 name (`SWR_REPEATED`, `PA_OVERTEMP`, `SENSOR_IMPLAUSIBLE`, `RF_NOT_KEYED`, `TX_PATH_NOT_BLOCKED`, `WDT_RESET_AT_START`, `SELFTEST_FAILED`, `INTERNAL_ERROR`), `none` if none (`FAULT_CODE`). `fault_class`: `0` none, `1` host-clearable, `2` latched until reset, the highest class among the flagged codes (`FAULT_CLASS`; 0022 §5). `fault_flags`: hex8, bit *c* set for every fault code *c* since the last clear (`FAULT_FLAGS`). `trips`: decimal, limit trips with action `UNKEY` or stronger since power-on, saturating (`TRIP_COUNT`). Sent on every change. |
| `G7250_FAULT_CLEAR` | unidirectional control | `G7250_FAULT_CLEAR:<fault_code>;` | `fault_code`: the Table B8-3 name of the current `fault_code` of `G7250_SAFETY`, as part B `FAULT_CLEAR` takes the current code (0022 §32); another name, or none, is rejected with `G7250_WRITE_STATUS` `BAD_VALUE`. Clears all flags only if every flagged code is class 1 (not escalated), its condition is gone and at least 10 s have passed since the latest fault entry (A3.5; 0022 §5, §27); otherwise nothing is cleared and the requester receives `G7250_WRITE_STATUS` `NOT_CLEARABLE`. A clear does not re-arm (0007 Decision 5, option 5D). |
| `G7250_LIMIT` | bidirectional | `G7250_LIMIT:<id>,<value>;` (set, reply), `G7250_LIMIT:<id>;` (read) | TCI session value of a host-tunable limit. `id`: `LIMIT_TX_TIME` (ms), `LIMIT_FWD_POWER` (mW, PEP), `LIMIT_SWR` (1000 × SWR), `LIMIT_PA_TEMP` (m°C): the Table B8-3 limit ids, in the units of their part B registers (Table B8-2; B8.6). Another id: `BAD_VALUE`. Rules C5.10.1. The reply always carries the limit in force. |
| `G7250_KEYED_TIMEOUT` | bidirectional | `G7250_KEYED_TIMEOUT:<ms>;` (set, reply), `G7250_KEYED_TIMEOUT;` (read) | Keyed timeout of C8.2 for opted-in and TX-audio keying clients. Not a limit (0021 §20). 100–500 ms, other values `BAD_VALUE`; default 500 ms (0007 Resolved 2; part B `KEYED_TIMEOUT`). A lower value is accepted from any client; a higher one only as C5.10.1 item 3. Back to 500 ms at TCI session end, on a level change and on reset. (L1) AetherSDR applies it to its TCI-side timer and MAY write it to the P2 `KEYED_TIMEOUT` register. |
| `G7250_LIMIT_STATUS` | notification | `G7250_LIMIT_STATUS:<hex8>;` | The part B `LIMIT_STATUS` layout: bit *n* limit id *n* limiting (`WARN` or `REDUCE`); bit 16 + *n* limit id *n* tripped (`UNKEY` or stronger) since the last TX request; limit ids of Table B8-3 (0006, "limit status"; 0021 §22). |

C5.10.1 **Limit tiers on TCI** (0021 §20; 0022 §6; A3.4 rules 1–2).

1. The TCI session value is the third tier of A3.4 rule 1. The **limit in force** is the
   strictest of the built-in value, the persistent value (management C-3, 0008) and the TCI
   session value; it is the only value that acts and the only value a reply carries.
2. A `G7250_LIMIT` write MUST be accepted only if it is equal to or stricter than the
   persistent value; a looser write MUST be rejected (not clamped) with `LOOSER_LIMIT`, and
   the reply carries the limit in force.
3. Writing 0 returns the TCI session value to the persistent value. Because the session value
   is shared by all clients, a write of 0, or of a value looser than the current session
   value, MUST be accepted only from the arm holder, or from any client while no client holds
   the arm; otherwise it is rejected with `LOOSER_LIMIT`.
4. The TCI session ends when the last client disconnects, on a level change and on reset; the
   session values then return to the persistent values (after a reset, the stored ones, A3.6).
5. A change of the persistent values (C-3) while armed drops the arm with `MAINTENANCE`
   (C5.5.5 row 11) and then applies at once; a session value looser than the new persistent
   value is replaced by it.
6. (L1) AetherSDR writes the strictest TCI session value to the P2 `LIMIT_<name>` register of
   the same name (Table B8-2) and passes the P2 answer (the limit in force, or
   `LOOSER_LIMIT`) on to TCI.
7. The 1 s generic keyed window, the 1 s key-down cap and the 30 s CW text liveness of C8.2
   are built in and have no command (0022 §25).

### C5.11 Stream state: `G7250_STREAM_STATE`

- Type: notification, per client. `G7250_STREAM_STATE:0,<stream>,<state>,<reason>;`,
  `stream` one of `iq`, `audio`, `line_out`, `tx_audio`; `state` `running`, `stopped`,
  `refused`; `reason` `none`, `budget`, `rate`, `not_supported`, `level_change` (C2.7),
  `takeover` (L1, C7.2.1). These are part C enumerations: the stream reasons of Table B8-3
  have numbers but no symbolic names.

### C5.12 Write rejections: `G7250_WRITE_STATUS`

- Type: notification, per client, sent only to the opted-in client whose request was
  rejected. `G7250_WRITE_STATUS:<command>,<reason>;`, `command` the name of the rejected
  command, `reason` a write reject reason of Table B8-3, verbatim: `READ_ONLY`, `BAD_VALUE`,
  `LOOSER_LIMIT`, `BUSY` (firmware update in progress), `NOT_CLEARABLE`, `KEYED` (RF-path
  change, `MODULATION` or `G7250_ATU_TUNE` while keyed), `NOT_ARMED` (0021 §22; part B B8.4;
  0022 §22).
- The TCI counterpart of the P2 `WRITE_STATUS` register. It is sent for rejected extension set
  requests and for standard commands that a profile rule refuses (C7.6: `MODULATION` while
  keyed). The reply with the value in force is sent as
  well, to all clients as usual.
- `UNKNOWN_ADDRESS` and `NOT_OWNER` are not used on TCI: an unknown command is ignored without
  a reply ([TCI] §4.7 note 5), and TCI clients have no owner (C5.5.1).
- Arm rejections are reported only in `G7250_TX_ARM_STATE` (as part B B8.4; 0022 §13).
- [TCI] has no reply to `IQ_START` or `AUDIO_START` ([TCI] §4.3), so a client cannot see that a
  stream was refused. This notification is that report, the TCI counterpart of the stream
  status register of 0004 (Consequences).

---

## C6 Streams

C6.1 **Block format.** Every stream block MUST use the 64-byte header of [TCI] §3.4
(`receiver`, `sample_rate`, `format`, `codec` = 0, `crc` = 0, `length`, `type`, `channels`,
`count`, `reserv[7]` = 0), followed by `length` samples. Clarifications (Annex C-C):

- C-C4 **Byte order.** [TCI] does not state it. The header fields and the samples MUST be
  little-endian (0021 §12) **[unverified: assumed from the C structure on common PC
  platforms; Annex C-D]**.
- C-C5 **Block size.** The binary frame MUST carry the header and `length` samples only, not
  the full `data[16384]` (0021 §12) **[unverified; Annex C-D]**; the data part MUST NOT exceed
  16384 bytes ([TCI] §3.4).
- C-C6 **count.** Incremented per block within a stream; kept separately for RX audio and
  TX_CHRONO and reset on each switch between TX and RX ([TCI] §3.4). The profile also keeps it
  per stream for IQ and line-out.

C6.2 **IQ stream** (`type` = 0, IQ_STREAM).

| Item | Value | Source |
|------|-------|--------|
| Receiver | 0 | `TRX_COUNT:1` (C3.2); HIS-02 |
| Rates | 48, 96, 192, 384 kHz | [TCI] §4.3 IQ_SAMPLERATE; 0004 Decision point 1 (the same four rates on level 1); 384 kHz only where 0004 point 6 allows it |
| Channels | 2 (I and Q); complex samples = `length` / `channels` | [TCI] §3.4 |
| Format | `FLOAT32` (3) on both levels; no `INT24` IQ in profile 1; `format` MUST state it | [TCI] §3.4 SampleType; 0021 §11. [TCI] has no command to choose the IQ format, and its audio default is float32 ([TCI] §4.3 AUDIO_STREAM_SAMPLE_TYPE). |
| Samples per block | at most 16384 bytes of data: 2048 complex samples at FLOAT32 | [TCI] §3.4 |
| Rate per client | [TCI] says "The rate is individual for each client" ([TCI] §4.3 IQ_SAMPLERATE). (L2) With one DDC the server MAY offer only one IQ rate at a time; a different rate requested while another client streams IQ is "ignored, the server replies with the current rate" ([TCI] §4.3), and `G7250_STREAM_STATE` reports `rate`. | 0004 (one DDC); HIS-02 |

(L2) IQ comes from the on-board DDC, the same chain as level 1 (0004 Decision point 1); the
conversion from the 24-bit DDC output to FLOAT32 runs on the processor (HIS-18, G6).

C6.3 **Audio streams.**

| Stream | `type` | Direction | Rates | Format, channels, samples | Notes |
|--------|--------|-----------|-------|---------------------------|-------|
| RX audio | 1 | server → client | `AUDIO_SAMPLERATE` (C4) | `AUDIO_STREAM_SAMPLE_TYPE`, `_CHANNELS`, `_SAMPLES` (C4) | (L2) Demodulated **on board** (0011 point 1). The main unit has no speaker or audio output (0017), so TCI is the only audio output on level 2. (L1) Demodulated in AetherSDR. |
| TX audio | 2 | client → server | as RX audio of this client ([TCI] §4.3 AUDIO_SAMPLERATE note) | as RX audio | Sent by the client in answer to TX_CHRONO, with the number of samples in TX_CHRONO's `length` ([TCI] §3.4); an answer is required while keyed (C8.2.1). (L2) Modulated on board. |
| TX_CHRONO | 3 | server → client | — | header only, `length` = samples requested | Sent "without waiting for a response from the client" ([TCI] §3.4). Sent to the keying client while it keys with source `tci` (C7.5). |
| Line out | 4 | server → client | as RX audio | fixed ("you cannot change its parameters", [TCI] §3.4) | MAY (C4). |

C6.3.1 There is no microphone stream from the radio: the microphone is on the controller and
reaches the main unit only if HIS-17 shows a path (0004 Decision point 3; 0017).

C6.3.2 With `DIGL`/`DIGU` and 2 channels the RX audio stream is complex; with 1 channel it is
real ([TCI] §3.4).

C6.4 **Stream budget, level 2.** Payload rates, from sample rate × channels × bytes per
sample × 8 (64-byte header and WebSocket framing per block left out, under 1 % at 2048-sample
blocks):

| Stream | Payload (Mbit/s) |
|--------|------------------|
| IQ 384 kHz, FLOAT32 | 24.6 |
| IQ 192 kHz, FLOAT32 | 12.3 |
| IQ 48 kHz, FLOAT32 | 3.1 |
| RX audio 48 kHz, 2 channels, float32 | 3.1 |
| RX audio 48 kHz, 1 channel, float32 | 1.5 |
| TX audio 48 kHz, 1 channel, float32 | 1.5 |

For comparison, DDC0 at 384 ksps on level 1 is 18.6 Mbit/s payload and 32.9 % SPI busy at
62 MHz, and DUC0 is 9.2 Mbit/s (0004, "Per stream"). Level 2 has no DUC IQ, but FLOAT32 IQ is
a third larger than 24-bit IQ.

- C6.4.1 **(L2)** The server MUST keep the aggregate of all streams to all clients within the
  SPI design target of 0004 Decision point 6, with the WebSocket and TCP overhead included
  (TBD, G6, HIS-14, HIS-18). A stream start that would exceed it MUST NOT be followed, and
  `G7250_STREAM_STATE` reports `budget`. Streams already running are never stopped to make
  room.
- C6.4.2 **(L2)** Proposed provisional limit, until G6 gives numbers: at most one IQ stream at
  a time, and RX audio to all clients. On these numbers a 384 kHz IQ stream (24.6) plus five
  stereo float32 RX audio streams (15.4) plus TX audio (1.5) is 41.5 Mbit/s of payload, about
  72 % of the 57.5 Mbit/s effective SPI rate at 62 MHz (`analysis/ch394-network-budget.md`;
  0004, "Assumptions") before register accesses: over the target. So at 384 kHz the server
  needs either fewer audio clients, mono or int16 audio, or a lower IQ rate. The IQ format
  stays FLOAT32; if the budget is short, the IQ rate offered is reduced (0021 §11). Numbers to
  be settled at G6.
- C6.4.3 **(L1)** AetherSDR is not bound by C6.4.1; its own P2 stream to the radio is bound by
  0004.

C6.5 **CH394Q buffers.** In TCP mode the CH394Q handles retransmission, so the 0004 buffer
split for UDP no longer applies on level 2; a level-2 split is TBD (HIS-14, G6).

---

## C7 Multiple clients and ownership

C7.1 **Synchronisation.** The server synchronises all clients: a parameter change from one
client is applied and sent to all ([TCI] §3.1; §3.3: "the server will synchronize the
parameters of all connected clients"). Unidirectional commands are per client ([TCI] §3.3),
including stream starts and rates (C6).

C7.2 **Single owner, levels.** Only one level controls the RF chain at a time, and only that
owner may transmit (0011 point 2). TCI clients do not compete with the level owner: on level 1
they control the radio through AetherSDR, the P2 owner; on level 2 they share the firmware's TCI
level. No TCI command changes the active level (C2.7).

C7.2.1 **(L1) P2 ownership and takeover** (0021 §26; 0022 §3; A2.3, A2.4). AetherSDR becomes
the P2 owner by setting the run bit while no session runs, or by a takeover. When another P2
host takes over, AetherSDR receives a last `TX_ARM_STATE` with `TAKEOVER`, three times about
10 ms apart, and nothing more (A2.4 step 1; 0022 §29). AetherSDR SHOULD also treat ownership as
lost when, while it believes it owns the radio, it receives neither DDC0 data nor High
Priority status packets for more than 200 ms (A2.4, host guidance; 0022 §29); it then stops
sending C&C and acts as below. AetherSDR MUST then send its TCI clients, in this order: the unkey broadcast
of C7.7 if keyed; `G7250_TX_ARM_STATE` (disarmed, `TAKEOVER`), a new `G7250_TX_ARM_TOKEN` and
`TX_ENABLE:0,false;` if armed; `G7250_STREAM_STATE` `stopped`, reason `takeover`, for each
running stream; `G7250_PROFILE` with `active` false. It keeps the TCI connections open.
AetherSDR MUST NOT take the radio back by itself (no ping-pong, 0022 §3 point 6); a new session
is started by the user. At a new session AetherSDR MUST write `TX_MODE_CLASS`, the TCI session
limits (C5.10.1) and the keyed timeout to P2 again before arming, because the takeover
returned them to the persistent values and defaults (A2.4 step 1).

C7.3 **Priority.** [TCI] gives "the highest priority" to the server's own operator and, among
clients, priority to the first one ([TCI] §3.5). In the profile, the safety core has the highest
priority, above any client and above the server's own user interface (0011 point 3).

C7.3.1 **Controller on level 2** (0021 §9). In profile version 1 the controller (head) has no
control on level 2, as on level 1: inputs that reach the main unit (HIS-17) are reported
(`TX_FOOTSWITCH`) and MUST NOT key the radio (0007 Sub-decision 6, Resolved 6). The priority
[TCI] §3.5 gives to the server's own operator is not given to the controller. Any change needs
answers to HIS-10 and HIS-17, M7, a new decision and a new profile version.

C7.3.2 **P2 while level 2 is active** (0021 §16). A P2 host cannot take the RF chain from level
2: the P2 C&C ports have no socket on level 2 (0008, Socket budget), discovery answers byte 4 =
0x03 (0003; part B B3.1), and the level changes only through the management channel (0008
C-2; C2.7).

C7.4 **Who may transmit.** While armed, any connected client MAY send a TX request (`TRX`
true, `TUNE` true, `KEYER` press, `CW_MACROS`, `CW_MSG`, `G7250_ATU_TUNE`), unless
`G7250_TX_POLICY` is `holder`, in which case only the arm holder MAY (C5.5.8; 0021 §1). The client whose
request keys the radio is the **keying client** (`G7250_TX_STATE` `mine` = `true`). Any client
MAY end a transmission (`TRX` false, `TUNE` false, `CW_MACROS_STOP`, `G7250_TX_ARM:0,00000000;`,
`STOP`); these are never blocked by the 200 ms monopoly ([TCI] §4.7 note 6) and take effect
immediately. Making TX stop is always allowed, as tightening is always allowed (0011 point 3).

C7.5 **Two clients key.** Only one TX request can be active, because there is one transmitter
([G7250-MAN]; `TRX_COUNT:1`):

1. The first TX request that the server processes keys the radio, following [TCI] §3.5 ("the
   priority is behind the first one").
2. A TX request from another client while keyed MUST NOT change the TX source or the TX audio.
   For `TRX` and `TUNE` the server replies with the current state; `G7250_ATU_TUNE` while
   keyed is rejected with `KEYED` from every client, the keying client included (C5.7;
   A3.9b); `CW_MACROS` and `CW_MSG` from another client are ignored; `KEYER` from another
   client is ignored.
3. CW queueing of [TCI] §3.5 (a `CW_MACROS` added in line, a `CW_MSG` that replaces a macro)
   applies only to requests from the keying client.
4. TX audio from any client other than the keying client is discarded, and TX_CHRONO is sent
   only to the keying client.
5. Because `TRX` is synchronised, every client sees `TRX:0,true;`; a client finds out whether
   the transmission is its own from `G7250_TX_STATE` (C5.5.3). A generic client cannot tell,
   which is a known limit of [TCI]; the profile proposes no fix for generic clients.
6. When the keying client's connection closes, the server unkeys (C8.3) and sends the unkey
   broadcast of C7.7.

C7.6 **Changes while keyed** (A3.9; 0022 §1, §2; 0021 §8, §19). While keyed:

C7.6.1 **Effective TX frequency.** The commands that move the effective TX frequency are:
`VFO` of the TX channel (channel A, or channel B with split on); `IF` of the TX channel;
`DDS` of receiver 0 when the channel frequency follows it (`VFO` = `DDS` + `IF`; **[unverified]**
whether [TCI] keeps `IF` or `VFO` on a `DDS` change; Annex C-D); `SPLIT_ENABLE`; `XIT_ENABLE`;
`XIT_OFFSET` while XIT is on; and (L1) any server action that sets one of these, such as a
click on a spot ([TCI] §4.4 RX_CLICKED_ON_SPOT). `RIT_ENABLE` and `RIT_OFFSET` do not move it.
Before applying such a change the server MUST evaluate the new effective TX frequency:

1. If it lies outside the transmit ranges in force, or needs another TX filter, band or relay
   state than the one in use, an ATU memory recall included (A3.9; 0022 §28), the server MUST
   unkey first (`UNKEY`, arm kept; `G7250_TX_STATE`
   `unkey` 6 "retune needs RF-path change", or `unkey` 4 with `LIMIT_TX_FREQ` when the cause
   is the range), then apply the change and switch relays while unkeyed, then send the unkey
   broadcast of C7.7. Keying again needs a new TX request.
2. Otherwise the change MUST be followed while keyed, without unkey.
3. Which frequencies share one RF-path state is the filter plan, TBD (HIS-07); until it is
   known, each transmit range of the `tx_band` list (part B B4.8) counts as its own state, on
   both levels.

C7.6.2 **Other frequency changes.** A change that does not move the effective TX frequency
(channel A with split on, channel B with split off, `RIT_OFFSET`) is followed; if it needs
another receive filter or relay state, the relay change is deferred until the unkey, before
any new key, as A3.9 defers resent P2 state fields (0021 §19).

C7.6.3 **Refused while keyed.** The server MUST refuse, from any client, changes of
`MODULATION` (0021 §8: the TX mode class must not change under a transmission; the TCI form of
A3.9c, 0022 §26), of the RF-path relays `G7250_ANT`, `G7250_ATU`, `G7250_PREAMP` and
`G7250_ATT` (A3.9; 0022 §2), and `G7250_ATU_TUNE` (A3.9b; 0022 §22). It replies with the
value in force and sends the opted-in requester `G7250_WRITE_STATUS` with `KEYED` (C5.12).
(L1) A mode change in AetherSDR's own user interface while keyed is a `TX_MODE_CLASS` change
on P2, which unkeys first (A3.9c).

C7.6.4 **Followed while keyed.** `DRIVE`, `TUNE_DRIVE`, `RX_FILTER_BAND` and other settings
that switch no relay and do not move the effective TX frequency.

C7.6.5 **Relay sequence** (A3.9a; 0022 §23). The guard and settle times of A3.9a apply on
both levels: after an unkey no relay moves until RF is gone, and the radio keys only after the
relays have settled. A frame that carries a frequency or relay command together with
`TRX:0,true` (or `TUNE:0,true`) is applied in the order of A3.9a item 3: relays, settle, then
key if the request still stands. (L1) AetherSDR sends both in one High Priority packet or in
any order; the radio applies A3.9a.

C7.7 **Unkey broadcast** (0021 §24). When the server unkeys without a request from a client
(keyed timeout or generic keyed window, TX audio underrun, a limit, the maximum TX time, a
retune of C7.6.1, a drop of C5.5.5, a level change, a takeover, the keying client's
connection closing, the key-down cap, a mode class change), it MUST send `TRX:0,false;` if
`TRX` was `true` and `TUNE:0,false;` if `TUNE` was `true`, to all clients, as the
synchronisation of [TCI] §3.1 requires for every change of state, and MUST discard queued CW
text. At every unkey, requested or not, the server MUST discard buffered TX audio, as part B
empties the DUC FIFO (B10.7; 0022 §32). Opted-in clients also receive
`G7250_TX_STATE` with the unkey reason. A client that sends `TRX:0,true;` afterwards makes a
new TX request.

---

## C8 Safety: limits and timeouts

C8.1 **Limits.** All limits of 0007 Sub-decision 4 apply on both levels with the same built-in
values, actions (WARN, REDUCE, UNKEY, DISARM, FAULT) and recovery (0007 rule 5; 0011 point 3).
They are reported over TCI by `G7250_LIMIT_STATUS`, `G7250_TX_STATE` and `G7250_SAFETY`, and
tightened by `G7250_LIMIT` (C5.10). `REDUCE` and the power measurement are those of part A
(A3.3, A3.4a, A3.4c; 0022 §7, §17; 0021 §21); TCI only reports them. The maximum continuous TX
time (`LIMIT_TX_TIME`) is 5 min built in, `UNKEY` only, arm kept (0007, Resolved item 3); it
applies to every TX source, including `CW_TERMINAL` and `TUNE`.

C8.2 **What replaces the P2 watchdog** (0021 §18). The P2 watchdog is "no C&C packet for 1 s"
[P2] (0007 Decision 2.1), and the keyed timeout is fed only by the High Priority packet, which
carries PTT, so that a host whose High Priority packets stop while other C&C continues is
unkeyed (0007 Decision 2, option 2C; option 2B rejected). The keyed timeout does not catch a
host whose I/O thread keeps sending a cached PTT or CWX bit while its TX logic has hung; on P2
the backstops for that case are the DUC underrun check, the CWX key-down cap and the maximum
TX time (part B B10.5, B10.5a; 0022 §25). On TCI the same role is played by the TX audio
underrun, the key-down cap and the CW text liveness below. TCI has no keep-alive of its own.
The profile separates the two timers:

- **Application frame.** A WebSocket text frame that carries at least one complete TCI command
  ([TCI] §3.1), or a binary frame that carries a TX_AUDIO_STREAM block ([TCI] §3.4). WebSocket
  control frames (Ping, Pong, Close; RFC 6455 §5.5) are never application frames.
- **Connection watchdog.** Fed by any frame, Pong included (RFC 6455 §5.5.2: an endpoint that
  receives a Ping "MUST send a Pong frame in response"), so that an arm holder needs no
  traffic of its own to stay connected while it is idle (0022 §32). It only drops the arm; it
  never keeps the radio keyed.
- **Keyed liveness.** Fed only by application frames from the keying client. A Pong MUST NOT
  feed it.

| Timer | Applies to | Server duty | Timeout and action | 0007 counterpart |
|-------|------------|-------------|--------------------|------------------|
| Connection watchdog | the arm holder, while armed | send a WebSocket Ping at least every 250 ms | no frame of any kind (Pong included) from the arm holder for **1 s** → drop the arm, `WATCHDOG` | Decision 2.1, base watchdog 1 s; drop event 3 |
| Keyed timeout | the keying client while keyed, if it has opted in (C5.2), or if it keys with `TRX:0,true,tci;` in a mode other than `CW` | — | no application frame from the keying client within the keyed timeout in force (`G7250_KEYED_TIMEOUT`, default **500 ms**, floor 100 ms) → `UNKEY`, arm kept; `unkey` 2 | Decision 2, option 2C, `KEYED_TIMEOUT`; Resolved item 2 |
| Generic keyed window | the keying client while keyed, if it has not opted in and keys with `TUNE`, `KEYER` key-down, `CW_TERMINAL` after its text has been sent, or `TRX` in `CW` | — | no application frame from the keying client for **1 s** (built in, not writable) → `UNKEY`, arm kept; `unkey` 2 | Decision 2.1 (the same 1 s) |
| TX audio underrun | the keying client, while keyed with source `tci` in a mode other than `CW` | send TX_CHRONO ([TCI] §3.4) | no TX_AUDIO_STREAM block for longer than `TX_STREAM_AUDIO_BUFFERING` + **500 ms** → `UNKEY`, arm kept; `unkey` 3 (0021 §7) | analogue of Decision 2, TX IQ underrun; fixed in the profile, independent of a hardware FIFO |
| Key-down cap | the keying client while keyed with `KEYER` key-down, opted in or not | — | key-down held for more than **1 s** without a key-up, whatever other frames arrive → `UNKEY`, arm kept; `unkey` 9 | part B B10.5a (CWX cap); 0022 §25 |
| CW text liveness | the keying client while the server sends its CW text (`CW_MACROS`, `CW_MSG`), opted in or not | — | no application frame from the keying client for **30 s** while text is sent → `UNKEY`, queued text discarded; `unkey` 2 | 0022 §25 (no P2 counterpart: P2 has no server-generated text) |
| Connection loss | arm holder / keying client | — | TCP close, reset or WebSocket close: holder → drop the arm (`HOLDER_LOST`); keying client → `UNKEY`; `unkey` 8 (keying client lost) | drop event 3; 0022 §32 |

Every unkey of this table is followed by the unkey broadcast of C7.7.

C8.2.1 **Deviation (Annex C-B, C-B1; 0021 §7).** [TCI] allows a client that is not ready to
"not send a response" to TX_CHRONO, and calls a block of zero samples "preferable" ([TCI]
§3.4). The profile requires the keying client to answer every TX_CHRONO while keyed with
source `tci`, with zero samples if it has no signal; no TX audio for longer than
`TX_STREAM_AUDIO_BUFFERING` + 500 ms unkeys and keeps the arm. The 500 ms equals the default
`KEYED_TIMEOUT` (0007, Resolved 2). **[unverified whether existing clients always answer;
Annex C-D]**; the 500 ms is the tolerance for late blocks.

C8.2.2 **Duty of an opted-in keying client.** While keyed, an opted-in keying client MUST send
an application frame at least every 100 ms, as the P2 host sends High Priority (0007 Decision
2; part B B10.5); `G7250_KEEPALIVE;` (C5.5.3) serves when it has nothing else to send. The
server MUST NOT unkey before the keyed timeout in force and MUST have unkeyed no later than
10 ms after it, as on P2 (part B B10.5). The 1 s and the keyed timeout are the same values as
on level 1 so that both levels behave alike (0014).

C8.2.3 **Generic keyed window** (0021 §18; Annex C-B, C-B9). Any application frame from the
keying client restarts the 1 s, for example a repeated `TUNE:0,true;`, a `KEYER` change or a
`CW_MSG`. While the server itself sends CW text (`CW_MACROS`, `CW_MSG`), the transmission
ends with the text and the window does not run; it starts when the text has been sent and the
radio stays keyed (terminal mode). 1 s equals the P2 base watchdog (0007 2.1), and a dash at 5
words per minute (720 ms) fits in it. **[unverified]** whether existing clients resend a
command during a long `TUNE`; a generic `TUNE` therefore ends after 1 s unless the client
sends frames (Annex C-D, D7). Long tune carriers need an opted-in client; ATU tuning is
`G7250_ATU_TUNE` (C5.7).

C8.2.4 **(L1)** AetherSDR's P2 keep-alive (High Priority every 100 ms from its I/O thread;
[AETHER-SRC] `P2Client.h:238–241`, per `annex-aethersdr.md` G-08c) does not depend on its TCI
clients, so the radio's keyed timeout protects only against AetherSDR itself stopping. AetherSDR
MUST apply C8.2 to its TCI clients, MUST NOT set the P2 PTT bit (High Priority byte 4 bit [1]
[P2]) for a TCI keying client whose keyed liveness has run out, and MUST clear it when the
TCI-side rule unkeys, before it forwards any further TX to P2 (0021 §18 point 6).
Independently, the radio applies the P2 watchdog and keyed timeout to AetherSDR (0007 Decision
2), so a crash of AetherSDR unkeys the radio even if AetherSDR's TCI side cannot act.

C8.3 **Keying client gone, holder still there.** If the keying client disconnects while the arm
holder stays, the server unkeys and keeps the arm (UNKEY, analogue of the keyed timeout;
`unkey` 8, 0022 §32) and sends the unkey broadcast of C7.7. (L1) AetherSDR clears the P2 PTT
bit; the radio reports P2 `TX_STATE` reason 1, AetherSDR reports `unkey` 8 on TCI.

C8.4 **Fault state.** Entry, effect, classes, clearing (with the 10 s hold-off), escalation
after the third entry of a code and the counters as A3.5 (0007 Decision 5; 0022 §5, §27).
In fault, RX and RX streams continue, so clients can still see the radio and the fault (0007
Decision 5, "Effect"). `TX_ENABLE` is `false`, arm requests are rejected with `IN_FAULT`, and
the fault is reported by `G7250_SAFETY` (C5.10).

C8.5 **State after reset** is that of A3.6 (0007 Decision 5): not armed, new token, limits at the
persistent values read from the stored configuration, keyed timeout 500 ms, policy `any`.
(L2) After a reset the TCI server starts with `TRX` and `TUNE` `false`, `RECEIVE_ONLY` and
`TX_ENABLE` as C3.2 and C5.5.6.

C8.6 **LAN security** (0021 §10). The arm prevents accidental transmission by software that does
not know the G7250; it is not security ("this is not security", 0007 Decision 1 rule 3). TCI
has no authentication [TCI], and the profile adds none to the TCI connection, so that generic
clients keep working (0012). Any accepted client can opt in and read the token. Level 2 is
meant for a trusted LAN; the mitigations are the reach rule and the optional allow-list of
C2.4.1, and the optional TX policy of C5.5.8. Traffic is in the clear, as on the management
channel (0008 S6).

---

## C9 Conformance tests

One line per test; tests run against the reference model on the product side (0019; 0021
§17.3) and against both implementations (0014, Consequences; 0001 item 5). Ids are stable.

| Id | Test |
|----|------|
| T-C2-01 | A WebSocket client connects on the configured port; commands arrive in text frames, streams in binary frames. |
| T-C2-02 | Several complete commands in one text frame are all executed. |
| T-C2-03 | (L2) `clients_max` clients connect; the next one receives `G7250_REFUSED:busy;` and close 1008; the listener accepts again afterwards. |
| T-C2-04 | (L2) A level change while keyed and armed sends, in this order, `TRX:0,false;`, `G7250_TX_ARM_STATE` with `LEVEL_CHANGE`, a new token, `TX_ENABLE:0,false;`, `G7250_STREAM_STATE` `stopped` `level_change`, `G7250_PROFILE` with `active` false, and then closes every connection with 1001 (C2.7). |
| T-C2-05 | Without configuration the server listens on TCP port 50001; after a port change through the management channel (L2) it listens on the new port only. |
| T-C2-06 | The WebSocket upgrade succeeds on `/` and on an arbitrary other path. |
| T-C2-07 | (L2) A connection from outside the radio's subnet is closed without handshake and logged. |
| T-C2-08 | (L2) With a non-empty allow-list, a connection from a non-listed address in the subnet is closed without handshake; a listed address connects. Setting the list without authentication fails. |
| T-C2-09 | (L2) `clients_max` in `G7250_PROFILE` is 5 while port 1024 still answers discovery with byte 4 = 0x03. |
| T-C3-01 | Initialization order is PROTOCOL, DEVICE, RECEIVE_ONLY, TRX_COUNT, CHANNELS_COUNT, VFO_LIMITS, IF_LIMITS, MODULATIONS_LIST, READY, then state. |
| T-C3-02 | Values match C3.2; `CHANNEL_COUNT` is never sent. |
| T-C3-03 | `IF_LIMITS` is resent after a receiver sample-rate change. |
| T-C3-04 | A `VFO` or `DDS` set to 40 MHz or outside VFO_LIMITS is not followed; the current value is replied. |
| T-C3-05 | No `G7250_` command reaches a client that has not opted in. |
| T-C3-06 | `PROTOCOL:ExpertSDR3,2.1;` is sent on both levels; (L2) `DEVICE:G7250;` is sent. |
| T-C3-07 | `MODULATION:0,FM;` selects narrow FM and is replied as `MODULATION:0,NFM;`; `MODULATIONS_LIST` contains `NFM` and not `FM`. |
| T-C4-01 | Each MUST command of C4 is accepted and its state replied and synchronised to a second client. |
| T-C4-02 | NOT SUPPORTED and reserved commands are ignored without a reply and never sent. |
| T-C4-03 | Commands with trx 1 or a channel number above 1 are ignored without a reply. |
| T-C4-04 | `TX_ENABLE` set by a client is ignored and the current state is replied. |
| T-C4-05 | `TRX:0,true;` without `tci` is refused when no microphone path exists. |
| T-C4-06 | `TUNE` produces a carrier at `TUNE_DRIVE` and never starts the ATU. |
| T-C4-07 | Unsupported IQ or audio rates are ignored and the current rate replied. |
| T-C4-08 | 200 ms monopoly and 30 ms tick behave as [TCI] §4.7 notes 6 and 7, except for stop commands. |
| T-C5-01 | `G7250_EXT:true;` yields PROFILE, FEATURES and full extension state in order. |
| T-C5-02 | `G7250_FEATURES` lists exactly the functions that work. |
| T-C5-03 | A correct `G7250_TX_ARM` arms with a new generation; a wrong value is rejected with `BAD_TOKEN`; the token is never `00000000`, `FFFFFFFF` or `ARM_MAGIC`. |
| T-C5-04 | Each precondition of C5.5.6 items 1–7, when false, rejects the arm with its Table B8-3 reason (`NOT_RUNNING`, `IN_FAULT`, `INHIBITED`, `PTT_ACTIVE`, `LEVEL_NOT_ACTIVE`, `MAINTENANCE`, `NO_MODE_CLASS`, `TX_NOT_IMPLEMENTED`). |
| T-C5-05 | After arming, a `TRX` state already `true` does not key; a new 0→1 request does. |
| T-C5-06 | Each drop event of C5.5.5 unkeys, disarms, issues a new token and reports the reason, with the Table B8-3 names, `STOP` and `HOLDER_LOST`. |
| T-C5-07 | `TX_ENABLE` is `true` exactly when C5.5.6 items 1–9 hold, and is resent on every change. |
| T-C5-08 | `G7250_TX_MODE_CLASS` follows `MODULATION` by the table of C3.4 (`DIGL`/`DIGU` give `ssb`); `WFM` gives `none` and blocks arming with `NO_MODE_CLASS`. |
| T-C5-16 | Armed and not keyed, a change to `WFM` keeps the arm, sets `TX_ENABLE` false and refuses `TRX` and `TUNE`; a change back re-enables TX without a new arm. |
| T-C5-17 | `G7250_TX_POLICY` defaults to `any`; any opted-in client can set `holder`; only the arm holder can set `any`; it returns to `any` after the last client leaves, on a level change and on reset. |
| T-C5-18 | With policy `holder`, `TRX`, `TUNE`, CW and `G7250_ATU_TUNE` from a non-holder are refused, while its `TRX` false, `CW_MACROS_STOP`, disarm and `STOP` still take effect. |
| T-C5-19 | A valid `G7250_TX_ARM` from client B while client A holds the arm leaves the generation and the holder unchanged; B receives `holder` false. |
| T-C5-20 | With policy `holder`, a drop or disarm returns the policy to `any`; the next arm starts with `any`. |
| T-C5-21 | A `G7250_LIMIT` write of 0 or a looser session value from a client that is not the arm holder, while a holder exists, is rejected with `LOOSER_LIMIT`; from the holder it is accepted. |
| T-C5-22 | `G7250_LIMIT` takes only `LIMIT_TX_TIME`, `LIMIT_FWD_POWER`, `LIMIT_SWR`, `LIMIT_PA_TEMP` in part B units; another id is rejected with `BAD_VALUE`. |
| T-C5-23 | `G7250_KEYED_TIMEOUT` accepts 100–500 ms, rejects other values with `BAD_VALUE`, and returns to 500 ms after the last client leaves. |
| T-C5-24 | `G7250_SAFETY` carries the Table B8-3 fault code name, the highest class among the flagged codes and the `FAULT_FLAGS` bit layout; `G7250_FAULT_CLEAR:<current code>;` with a class-2 code flagged is rejected with `NOT_CLEARABLE` and clears nothing. |
| T-C5-25 | `G7250_ATU_TUNE` without the arm is rejected with `NOT_ARMED` and does not start later when the radio is armed. |
| T-C5-26 | An extension whose `G7250_FEATURES` token is absent is ignored without a reply; with `ant_state` only, a `G7250_ANT` set is answered with the value in force and `READ_ONLY`. |
| T-C5-27 | (L1) With AetherSDR's interface and a TCI client both holding the arm, the TCI client's disconnect leaves the P2 arm set; with the TCI client as the only holder, it writes `TX_ARM` = 0 over P2. |
| T-C5-28 | `G7250_ATU_TUNE` while keyed with `TRX`, `TUNE` or CW, from the keying client and from another client, is rejected with `KEYED`, does not start after the unkey and does not end the transmission; a repeated `G7250_ATU_TUNE` during a tune cycle is a no-op; every cycle ends unkeyed. |
| T-C5-29 | `TRX:0,true;` refused while unarmed, inhibited, outside the ranges or in `WFM` does not key when the condition clears; a new `TRX:0,false;` then `TRX:0,true;` keys. `CW_MACROS` sent while unarmed is discarded and not sent after a later arm. |
| T-C5-30 | `G7250_TX_STATE` `unkey` reports 8 after the keying client's connection closes, 9 after the key-down cap, and never 10 as the result of a TCI command (`MODULATION` is refused while keyed); (L1) `inhibits` equals the P2 `LIMIT_INHIBIT` register. |
| T-C5-31 | Drop reasons on TCI are `STOP` for `STOP;` and `HOLDER_LOST` for the holder's connection loss, as Table B8-3 drop reasons 13 and 14; (L1) a TCI `STOP` makes AetherSDR clear the P2 run bit and its TCI clients see `STOP`. |
| T-C5-09 | In class `am`, the 100 ms mean output power stays within the 25 W AM carrier limit at `DRIVE:0,100` (A3.4c). |
| T-C5-10 | `G7250_ATU_TUNE` needs the arm, follows the tune time limit and reports `tuned` or `failed`. |
| T-C5-11 | `G7250_ANT`, `G7250_ATU`, `G7250_PREAMP`, `G7250_ATT` (where present) and `MODULATION` are refused while keyed, from any client, with the value in force and `G7250_WRITE_STATUS` `KEYED` to an opted-in requester; `DRIVE` while keyed is followed. |
| T-C5-12 | With a persistent value stricter than the built-in one, `G7250_LIMIT` accepts a value equal to or stricter than the persistent value, rejects a value between persistent and built-in with `LOOSER_LIMIT`, always replies the limit in force, returns to the persistent value on a write of 0 and after the last client leaves. |
| T-C5-13 | `G7250_FAULT_CLEAR` with the current code clears a class-1 fault only when the condition is gone and 10 s have passed since the latest entry, and never re-arms; a wrong or missing code is rejected with `BAD_VALUE`; the third entry of the same code since power-on is not clearable (A3.5). |
| T-C5-14 | (L1) A TCI arm causes a P2 arm handshake and is confirmed only after the radio confirms. |
| T-C5-15 | (L1) Every P2 drop event is reported on TCI with the P2 reason. |
| T-C6-01 | Stream headers are 64 bytes, little-endian, with correct receiver, rate, format, length, type, channels and count; each frame is header plus `length` samples. |
| T-C6-07 | IQ blocks carry `format` = 3 (FLOAT32) at every offered rate. |
| T-C6-02 | IQ streams at each offered rate without loss for a set duration; a test tone appears at the right offset and sign. |
| T-C6-03 | RX audio honours sample type, channels and samples per block. |
| T-C6-04 | TX_CHRONO goes only to the keying client; its TX audio is transmitted; others' TX audio is discarded. |
| T-C6-05 | (L2) A stream start over the budget is not followed and is reported as `budget`. |
| T-C6-06 | (L2) A second IQ rate requested while another client streams IQ is refused with the current rate. |
| T-C7-01 | A parameter set by one client is reported to all others. |
| T-C7-02 | With two clients, the first TX request keys; the second's `TRX`, `TUNE`, CW and KEYER are refused or ignored. |
| T-C7-03 | Any client can unkey with `TRX` false, `TUNE` false, `CW_MACROS_STOP`, disarm or `STOP`, immediately. |
| T-C7-04 | `G7250_TX_STATE` `mine` is true only for the keying client. |
| T-C7-05 | While keyed, each command of C7.6.1 (`VFO`, `IF`, `DDS`, `SPLIT_ENABLE`, `XIT_ENABLE`, `XIT_OFFSET`, channel B with split) that moves TX outside a transmit range, or into another `tx_band` entry, unkeys before the change applies (arm kept, `unkey` 4 with `LIMIT_TX_FREQ` or `unkey` 6); a small retune inside the same entry is followed without unkey. |
| T-C7-06 | Every server-side unkey of C7.7 sends `TRX:0,false;` (or `TUNE:0,false;`) to all clients, including clients that have not opted in. |
| T-C7-07 | While keyed with split on, a channel A change that needs another receive filter is followed and the relay switches only after the unkey. |
| T-C7-08 | (L1) After a P2 takeover of AetherSDR, its TCI clients receive the C7.2.1 sequence with `TAKEOVER`, the connections stay open, and AetherSDR does not retake the radio by itself. |
| T-C7-09 | A frame with `VFO` into another `tx_band` entry and `TRX:0,true;`, sent while unkeyed, switches relays, waits the settle time and then keys; after any unkey no relay moves until RF is gone (A3.9a; reference model). |
| T-C7-10 | While keyed, a frequency change inside one `tx_band` entry that would recall another ATU state unkeys with `unkey` 6 before the recall (A3.9; HIS-08). |
| T-C7-11 | After every unkey, buffered TX audio is discarded: the first TX audio transmitted at the next key is from blocks received after the new key. |
| T-C7-12 | (L1) When DDC0 data and High Priority status stop for more than 200 ms while AetherSDR is the P2 owner, AetherSDR stops sending C&C and sends its TCI clients the C7.2.1 sequence. |
| T-C8-01 | Arm holder silent for 1 s (Pong suppressed) → arm dropped with `WATCHDOG`; an arm holder that answers only Pings keeps the arm. |
| T-C8-02 | Opted-in keying client that sends no application frame for the keyed timeout in force, while its WebSocket stack still answers every Ping, → unkey (not before the timeout, not later than 10 ms after it), arm kept. `G7250_KEEPALIVE` every 100 ms keeps it keyed. |
| T-C8-10 | A generic client keyed with `TUNE` that sends no application frame, while answering Pings, is unkeyed after 1 s, arm kept; one that resends `TUNE:0,true;` every 500 ms stays keyed. |
| T-C8-11 | A generic `KEYER` key-down of 720 ms is not cut; a key-down held for 1 s without a frame is unkeyed; an opted-in client's key-down held for more than 1 s is unkeyed with `unkey` 9 although it sends `G7250_KEEPALIVE` every 100 ms. |
| T-C8-12 | A generic client keyed with `TRX:0,true,tci;` in `USB` that stops sending TX audio blocks but answers Pings is unkeyed within the keyed timeout. |
| T-C8-13 | (L1) When the TCI-side keyed liveness of a TCI client runs out, AetherSDR's next P2 High Priority packet carries PTT = 0, although its P2 keep-alive continues. |
| T-C8-14 | `TX_SENSORS` arg3 is the 100 ms mean forward power and arg4 the PEP; in class `am` with an unmodulated carrier at full drive arg3 settles at or below 25 W plus the margin of Table A3-2. |
| T-C8-15 | A `REDUCE` for SWR above S1 caps forward power at `P_swr` until the unkey, while `DRIVE` keeps the client's value. |
| T-C8-03 | TX audio stops answering TX_CHRONO → unkey after `TX_STREAM_AUDIO_BUFFERING` + 500 ms (not before), arm kept; zero-sample answers keep the radio keyed. |
| T-C8-04 | Arm holder TCP reset → arm dropped with `HOLDER_LOST`; keying client TCP reset → unkey with `unkey` 8. |
| T-C8-16 | While the server sends CW text for a keying client that sends no application frame, the radio unkeys after 30 s, discards the queued text and reports `unkey` 2; a `CW_MACROS` every 20 s keeps it sending. |
| T-C8-05 | Maximum TX time (5 min built in, also with `CW_TERMINAL` and `TUNE`) unkeys and keeps the arm. |
| T-C8-06 | In fault, RX streams continue, `TX_ENABLE` is false and arm requests are rejected. |
| T-C8-07 | After reset, the server is disarmed with a new token, limits at the stored persistent values (C8.5), and `TRX`/`TUNE` false. |
| T-C8-08 | (L2) A controller PTT input (if HIS-17 gives a path) is reported by `TX_FOOTSWITCH` and never keys, armed or not. |
| T-C8-09 | `TX_SENSORS` arg2 reports the TX audio level in dB full scale while keyed with source `tci`, and `-140` without TX audio. |

---

## Annex C-A — Open points (HIS and G6 only)

Every other open point of draft 1 is decided in 0021 (proposed for ON8ST review at rc1).

| # | Point | Depends on |
|---|-------|------------|
| A1 | Whether level 2 can be built at all: compute for DSP, WebSocket and TCI; memory; network stack. All (L2) requirements wait for it. | G6, HIS-18, HIS-14 |
| A2 | Number of receivers; whether `TRX_COUNT` stays 1 and whether channel B can be demodulated. | HIS-02, G6 |
| A3 | `IF_LIMITS` on level 2 (receiver bandwidth). | G6, HIS-01 |
| A4 | CH394Q TCP server behaviour: does the listening socket become the connection (C2.5.3), which sets `clients_max`? Socket buffer split in TCP mode (C6.5). | HIS-14 |
| A5 | Stream budget on level 2 (C6.4): number of IQ streams, maximum IQ rate, audio formats, aggregate with TCP and WebSocket overhead. | G6, HIS-14, HIS-18 |
| A6 | Calibration of `RX_SENSORS` dBm on level 2. | HIS-11, G6 |
| A7 | `DRIVE` 0–100 to power mapping; tune power. | HIS-12, HIS-08 |
| A8 | Microphone, PTT and KEY from the controller (C4, C7.3.1); a microphone path for `TRX` without `tci`. | HIS-17, HIS-10 |
| A9 | Preamplifier and attenuator steps (C5.9); until answered, and on level 1 until a part B register exists, `G7250_PREAMP` and `G7250_ATT` are absent (C5.1.4). | HIS-07 |
| A10 | Default antenna after reset (C5.8); antenna switching, until answered and on level 1 until a writable part B register exists `G7250_ANT` is at most reported (`ant_state`, C5.1.4). | HIS-06 |
| A11 | `KEYER` timing jitter over TCP and WebSocket on level 2 (C4). | G6 |
| A12 | Which optional DSP functions (NB, NR, ANC, ANF, APF, DSE, NF, BIN, second demodulator, `WFM` receive, audio rates below 48 kHz) level 2 can carry. | G6, HIS-18 |
| A13 | ATU selection in or out of line (`G7250_ATU`, token `atu_select`); absent until answered and, on level 1, until a part B register exists (C5.7). | HIS-08 |
| A14 | Filter plan: which TX frequencies share one RF-path state (C7.6.1); until answered, each `tx_band` entry is its own state. | HIS-07 |

## Annex C-B — Deviations from [TCI]

| # | Deviation | Section |
|---|-----------|---------|
| C-B1 | The keying client must answer every TX_CHRONO while keyed with source `tci`; no TX audio for `TX_STREAM_AUDIO_BUFFERING` + 500 ms unkeys (0021 §7). [TCI] §3.4 allows no answer. | C8.2.1 |
| C-B2 | Transmit needs a G7250 arm; `TRX`, `TUNE`, `KEYER` and CW text do not key without it. [TCI] has no arm. | C5.5 |
| C-B3 | A TX request from a second client while keyed does not change the TX source; stop requests are never held by the 200 ms monopoly. | C7.4, C7.5 |
| C-B4 | (L2) Only one IQ rate at a time may be offered, although [TCI] makes the rate individual per client; the refusal uses [TCI]'s own "ignored, current rate replied" rule. | C6.2 |
| C-B5 | `TRX` without the `tci` source is refused when there is no microphone path, instead of taking a microphone signal. | C4 |
| C-B6 | Changes of modulation, antenna, ATU selection, preamplifier and attenuator are refused while keyed (0021 §8, §19; A3.9). | C7.6.3 |
| C-B7 | (L2) TCI connections are accepted only from the radio's subnet and, if set, an allow-list (0021 §10). [TCI] has no such rule. | C2.4.1 |
| C-B8 | `G7250_TX_POLICY:holder` lets only the arm holder key (0021 §1). | C5.5.8 |
| C-B9 | While keyed, the keying client must send application frames: within the keyed timeout (500 ms) if it has opted in or keys with TCI audio, within 1 s otherwise; a WebSocket Pong does not count. A generic `TUNE`, `KEYER` key-down, `CW_TERMINAL` or `TRX` in `CW` without frames ends after 1 s (0021 §18). [TCI] has no such timeout. | C8.2, C8.2.3 |
| C-B10 | While keyed, a change of the effective TX frequency that leaves the transmit range or needs another RF-path state unkeys before it applies (arm kept); [TCI] follows frequency changes without condition (0021 §19; A3.9). | C7.6.1 |
| C-B11 | A `KEYER` key-down held for more than 1 s ends from every client (0022 §25). [TCI] has no such limit. | C8.2 |
| C-B12 | While the server sends CW text, the keying client must send an application frame at least every 30 s, else the text ends (0022 §25). [TCI] has no such duty. | C8.2 |
| C-B13 | A TX request that arrives with a band or relay change keys only after the relays have settled; `G7250_ATU_TUNE` while keyed is refused (0022 §22, §23; A3.9a, A3.9b). | C7.6.5, C5.7 |

## Annex C-C — Clarifications of [TCI]

| # | Clarification | Section |
|---|---------------|---------|
| C-C1 | Commands are in text frames, several complete commands per frame allowed, never split over frames. | C2.2 |
| C-C2 | The WebSocket upgrade is accepted on any path (0021 §17.1). | C2.3 |
| C-C3 | A frequency inside `VFO_LIMITS` but outside the receive range is not followed; the current value is replied. | C3.3 |
| C-C4 | Stream header and samples are little-endian **[unverified]**. | C6.1 |
| C-C5 | A stream frame carries the header and `length` samples only **[unverified]**. | C6.1 |
| C-C6 | `count` is kept per stream also for IQ and line-out. | C6.1 |
| C-C7 | [TCI] lists `TX_ENABLE` under §4.3 "Unidirectional Control Commands" but gives its type as "Bidirectional control"; the profile treats it as server-controlled state, synchronised to all clients, with client sets ignored, as its note says. | C4 |
| C-C8 | [TCI] lists `KEYER` under §4.4 "Notification Commands" but gives its type as "Unidirectional control", "Sent only by the TCI client"; the profile treats it as a client command. | C4 |
| C-C9 | `FM` in a `MODULATION` set request is read as `NFM` (0021 §13). | C3.4 |
| C-C10 | `TX_SENSORS` arg2 ("microphone signal level, dBm") carries the TX audio level in dB full scale, because the main unit has no microphone (0021 §15). | C4 |
| C-C11 | `PROTOCOL` arg1 is sent as `ExpertSDR3` as a compatibility value on both levels; it does not identify the G7250 (0021 §4). | C3.2 |
| C-C12 | `TX_SENSORS` arg3 ("RMS" power) is the 100 ms mean forward power and arg4 (peak power) the PEP over the same window, as the safety core measures them (A3.4c; 0021 §21). | C4 |
| C-C13 | An unkey that no client requested is reported to all clients as `TRX:0,false;` or `TUNE:0,false;`, as the synchronisation of [TCI] §3.1 implies (0021 §24). | C7.7 |
| C-C14 | The effective TX frequency is moved by `VFO`, `IF` and `DDS` of the TX channel, `SPLIT_ENABLE`, `XIT_ENABLE` and `XIT_OFFSET`; not by RIT (0021 §19). | C7.6.1 |
| C-C15 | A TX request that cannot key is not kept: a refused `TRX` or `TUNE` does not key later, and CW text received while unarmed is discarded ([TCI] is silent; 0022 §24). | C5.5.4, C4 |
| C-C16 | (L1) `STOP` ("Stops the device") clears AetherSDR's P2 run bit; the TCI drop reason is `STOP` (0022 §32). | C4 |

## Annex C-D — Assumptions to verify against public sources

The profile rule stands meanwhile; none of these is a HIS question.

| # | Assumption | Rule meanwhile | Check against |
|---|------------|----------------|---------------|
| D1 | Stream header and samples are little-endian. | C-C4 (0021 §12) | a public TCI client implementation |
| D2 | A stream frame carries the header and `length` samples only. | C-C5 (0021 §12) | a public TCI client implementation |
| D3 | Existing clients tolerate, or at least do not need, the absence of unknown server commands. | opt-in, C5.2 | public client sources |
| D4 | Existing clients answer every TX_CHRONO while transmitting TCI audio. | C8.2.1 (0021 §7) | public client sources; AetherSDR conformance run |
| D5 | Clients accept FLOAT32 IQ. | C6.2 (0021 §11) | public client sources |
| D6 | Some clients expect `PROTOCOL:ExpertSDR3`; `device:AetherSDR` matters to WSJT-X. | C3.2 (0021 §4, §5) | [AETHER-SRC] comments; WSJT-X source |
| D7 | Generic clients send no command during a long `TUNE` or a held key, so the 1 s generic keyed window ends them. | C8.2.3 (0021 §18) | public client sources; AetherSDR conformance run |
| D8 | On a `DDS` change [TCI] keeps `IF`, so the channel frequency (`VFO`) moves with it. | C7.6.1 (0021 §19): checked as a TX-frequency change either way | [TCI] §4.2 DDS, IF; public client sources |

## Sources

- [TCI] TCI Protocol, Ver. 2.1, September 2026, "Expert Group" LLC: §1.4, §2, §3.1–3.5, §4.1–4.7
  (`sources.md`). Read in full for this part, 2026-11-19, from the text extraction of the PDF.
- [AETHER] AetherSDR README (TCI server, protocol 2.1).
- [AETHER-SRC] AetherSDR source, commit 9f7cbeb (2026-11-18), through `annex-aethersdr.md`
  §2.4 and G-13 (TCI port, `PROTOCOL`, `DEVICE`).
- [G7250-MAN] Xiegu G7250 Operation Manual: receive and transmit ranges, modes, TX power, ATU,
  antennas, interfaces.
- [CH394] WCH CH394 manual 1, V1.2 (8 sockets), through `analysis/ch394-network-budget.md` and
  0008.
- [P2] openHPSDR Ethernet Protocol V4.4, through 0007 (watchdog) and part B (High Priority byte
  4 bit [1], PTT).
- [RFC6455] The WebSocket Protocol (§4.2.1, §5.2, §5.3, §5.5, §5.5.2, §7.4.1).
- RFC 2119, RFC 8174 (BCP 14).
- Decisions 0001, 0003, 0004, 0006, 0007, 0008, 0011, 0012, 0013, 0014, 0015, 0017, 0019,
  0021, 0022.
- `spec/network-interface.md` draft 5: A2.3–A2.5a, A3.1a, A3.2–A3.6, A3.9–A3.9c, B4.8, B7,
  B8.3, B8.4, B8.6, B8.7, Tables B8-2 and B8-3, B10.2, B10.3, B10.5, B10.5a, B10.7, B10.9.
- `analysis/ch394-network-budget.md` (Addendum, "TCI (level 2)"); `open-questions-his.md`
  (HIS-02, -06, -07, -08, -10, -11, -12, -14, -17, -18); design note §6 (milestones, G6).
- [AETHER-SRC] also `P2Client.h:238–241` (P2 keep-alive), through `annex-aethersdr.md` G-08c.

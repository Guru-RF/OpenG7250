# Part C — Level 2 and the G7250 TCI profile

- Version: draft 1, 2026-11-19
- Status: draft for review by ON8ST. Not yet merged into `spec/network-interface.md`.
- © 2026 ON8ST, CC BY 4.0 (see `LICENSE.md`); quoted TCI material © Expert Group LLC under its
  MIT notice.
- Builds on: 0011 (two levels, single owner, shared safety core, level 2 only after G6), 0012
  (full functionality), 0013 (AetherSDR), 0014 (one G7250 TCI profile), 0004 (rates), 0006
  (telemetry), 0007 (watchdog and safety), 0008 (management channel, socket budget), 0015 (TX
  arm), 0017 (no audio on the main unit).

Sources are cited by key (see `sources.md`) or by decision number (see `decisions/`).
Citations of [TCI] give the section of TCI Protocol 2.1 and the command name, for example
"[TCI] §4.2 DDS". Values that depend on an open question are written "TBD (HIS-xx)" or
"TBD (G6)". Statements marked **[unverified]** rest on an assumption that has not been checked
against a public source; they are listed again in Annex C-A.

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
connection", with the transceiver as the server ([TCI] §1.4). WebSocket is RFC 6455
**[RFC 6455 not yet in `sources.md`]**.

C2.2 Commands are ASCII strings ([TCI] §3.1) and MUST be sent in WebSocket text frames; stream
blocks ([TCI] §3.4) MUST be sent in WebSocket binary frames ([TCI] §3.4: "commands are
transmitted as strings and audio streams are transmitted as byte streams"). Clarification
(Annex C-C, C-C1): the server MAY put several complete commands in one text frame and MUST
accept several complete commands in one frame from a client; a command MUST NOT be split over
frames.

C2.3 No TLS and no WebSocket subprotocol are used. [TCI] defines neither. **[unverified]**
which request path existing clients use in the HTTP upgrade; the server MUST accept the upgrade
on path `/` and SHOULD accept it on any path (Annex C-C, C-C2).

C2.4 **Port.** [TCI] does not state a default TCP port (`sources.md`, [TCI]). The port MUST be
configurable. **(L2)** On level 2 the port is set through the management channel
configuration (0008), default **TBD**. Candidate: 40001, which is believed to be the port
commonly used by TCI clients **[unverified: no public source read; to be checked and listed in
`sources.md` before it is adopted]**. The port MUST NOT collide with the management port or
with port 1024 (0008, Transport point 2). **(L1)** AetherSDR's port is its own configuration.

C2.5 **Number of clients, level 2.** The CH394Q has 8 hardware sockets [CH394], and each TCP
connection takes one socket (0008, Socket budget, [CH394] §7.2.2; `analysis/ch394-network-budget.md`,
Addendum, "TCI (level 2)"). While level 2 is active:

| Socket use | Sockets | Source |
|------------|---------|--------|
| Management channel, always reserved | 1 | 0008, Transport point 1 |
| P2 port 1024, if discovery stays answerable on level 2 | 1 | 0008, Socket budget; part B B3 (open) |
| Spare TCI listener, so that a further client can always be accepted and refused cleanly | 1 | 0008, Socket budget |
| TCI client connections | 5 | 8 − 3 |

- C2.5.1 **(L2)** The server MUST serve at least **4** simultaneous clients and SHOULD serve
  **5**. The number in use MUST be reported in `G7250_PROFILE` (C5.3). If port 1024 is not
  kept on level 2 (decision pending, Annex C-A), the server MAY serve 6.
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
(0011 point 2). On a change of active level the server MUST unkey, drop the arm with reason
`LEVEL_CHANGE` (0007, drop event 10), send `G7250_PROFILE` with the new state to opted-in
clients, and then close every TCI connection with WebSocket status 1001 "going away"
(RFC 6455 §7.4.1). Level selection itself is done through the management channel and part A
(0011; 0008, C-2 and I-4), not over TCI.

---

## C3 Initialization

C3.1 On every new connection the server MUST send the initialization commands of [TCI] §4.1,
then `READY;`, and then the current state of every supported bidirectional parameter ([TCI]
§3.1: "the client receives the current status ... first sending initialization commands, then
parameters to set the status"; [TCI] §4.1 READY: "Sent after the initialization commands").

C3.2 Initialization commands and their G7250 values, in this order:

| # | Command | G7250 value | Status | Source / reason |
|---|---------|-------------|--------|-----------------|
| 1 | `PROTOCOL:<program>,2.1;` | (L2) `PROTOCOL:G7250-FW,2.1;` (L1) `PROTOCOL:AetherSDR,2.1;` or the program name AetherSDR already sends | MUST | [TCI] §4.1 PROTOCOL ("arg1 — program name", "arg2 — version of the protocol"); [AETHER] (2.1). Program name for the firmware is a profile choice. |
| 2 | `DEVICE:G7250;` | `G7250` on both levels | MUST | [TCI] §4.1 DEVICE; [TCI] §1.4 ("maintaining the device model designation"). The same name on both levels lets a client recognise the radio regardless of level (0014). |
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
| `AM` | AM | yes | yes, 25 W max [G7250-MAN] | AM | MUST |
| `LSB`, `USB` | SSB | yes | yes, 100 W | SSB | MUST |
| `CW` | CW | yes | yes, 100 W | CW | MUST |
| `NFM` | FM (narrow) | yes | yes, 100 W ("NFM" in [G7250-MAN] TX power) | FM | MUST |
| `WFM` | WFM | yes | **no**: no WFM transmit power is given in [G7250-MAN] | none (TX refused) | SHOULD (L2: G6, compute) |
| `DIGL`, `DIGU` | SSB used for data modes | yes | yes, 100 W | SSB | SHOULD |

`FM` from the [TCI] example is not used; the G7250 mode is announced as `NFM`
**[unverified: which name existing clients expect for narrow FM]**. Mode names are sent in
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
| `STOP` | MUST | Stops the device. Unkeys and drops the arm, reason `STOP` (analogue of P2 RUN cleared, 0007 drop event 2). | §4.2 STOP |
| `DDS` | MUST | Receiver centre frequency. Range C3.3. | §4.2 DDS |
| `IF` | MUST | Offset of channel A/B within the receiver passband, inside `IF_LIMITS`. | §4.2 IF |
| `VFO` | MUST | Channel frequency (= DDS + IF). Range C3.3. Changes while keyed: C7.6. | §4.2 VFO |
| `RX_ENABLE` | MUST | Only trx 0, always `true`; "The first transceiver is always enabled". | §4.5 RX_ENABLE |
| `RX_CHANNEL_ENABLE` | MUST for ch 0; MAY for ch 1 | Ch 0 is always enabled. Demodulating ch 1 at the same time needs a second demodulator (L2: G6). If not implemented, a set to `true` for ch 1 is refused with a reply `RX_CHANNEL_ENABLE:0,1,false;`. | §4.2 RX_CHANNEL_ENABLE |
| `LOCK` | MAY | Tuning lock; synchronised state only. | §4.2 LOCK |
| `VFO_LOCK` | MAY | Notification, server to client. | §4.4 VFO_LOCK |
| `TX_FREQUENCY` | MUST | Sent on every change of the effective TX frequency (VFO A, or B with split, plus XIT). | §4.4 TX_FREQUENCY |

### Mode and filters

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `MODULATION` | MUST | Names of C3.4. Sets the TX mode class (C5.6). Change while keyed: C7.6. | §4.2 MODULATION |
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
| `SPLIT_ENABLE` | SHOULD | TX on channel B frequency. The TX frequency limit (0007, Sub-decision 4, "TX frequency") applies to the effective TX frequency. | §4.2 SPLIT_ENABLE |
| `RIT_ENABLE`, `RIT_OFFSET` | SHOULD | RX only; no TX effect. | §4.2 RIT_ENABLE, RIT_OFFSET |
| `XIT_ENABLE`, `XIT_OFFSET` | SHOULD | The XIT offset is part of the effective TX frequency for the TX frequency limit (0007). | §4.2 XIT_ENABLE, XIT_OFFSET |

### Transmit

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `TX_ENABLE` | MUST | Server-controlled; `true` only if C5.5.6 holds. A client set is ignored and the current state is replied ([TCI] §4.3 note). | §4.3 TX_ENABLE |
| `TRX` | MUST (M7 on L2) | `TRX:0,true,tci;` keys with TX audio from the client's TCI stream. `TRX:0,true;` (microphone) and `mic1`/`mic2`/`micpc`/`ecoder2`: refused unless a microphone path exists (HIS-17); refused means the server replies `TRX:0,false;`. Every key needs the arm (C5.5). | §4.2 TRX |
| `TUNE` | MUST (M7 on L2) | Tune carrier at `TUNE_DRIVE`, under the arm. It does **not** start the internal ATU: the meaning is not identical (as P2 TUNE, 0007 Sub-decision 6). ATU tuning is `G7250_ATU_TUNE` (C5.7). | §4.2 TUNE |
| `DRIVE` | MUST | 0–100. Mapping to power TBD (HIS-12). A `REDUCE` limit action lowers power on the radio side and does not change the `DRIVE` value (0007, Sub-decision 4 rule 4). | §4.2 DRIVE |
| `TUNE_DRIVE` | MUST | 0–100, as `DRIVE`. | §4.2 TUNE_DRIVE |
| `TX_FOOTSWITCH` | SHOULD | Reports a PTT input that reaches the main unit (controller microphone PTT, HIS-17). It never keys by itself (0007, Sub-decision 6; revisit for level 2, Annex C-A). | §4.4 TX_FOOTSWITCH |
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
| `VOLUME`, `MUTE`, `RX_MUTE`, `RX_VOLUME`, `RX_BALANCE` | MAY | L2: the main unit cannot play audio (0017); if supported, the values are synchronised and SHOULD NOT change the level of the TCI RX audio stream **[unverified: whether ExpertSDR3 applies VOLUME to the TCI stream; [TCI] does not say]**. | §4.2 |

### Sensors

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `RX_SENSORS_ENABLE` | MUST | Interval 30–1000 ms. | §4.4 RX_SENSORS_ENABLE |
| `RX_SENSORS`, `RX_CHANNEL_SENSORS` | MUST, MAY for ch 1 | Signal level in dBm in the RX filter. L2: calibration TBD (HIS-11). | §4.4 RX_SENSORS, RX_CHANNEL_SENSORS |
| `TX_SENSORS_ENABLE` | MUST (M7 on L2) | Interval 30–1000 ms. | §4.4 TX_SENSORS_ENABLE |
| `TX_SENSORS` | MUST (M7 on L2) | arg2 "microphone signal level, dBm": level of the TX audio input in use, unit TBD (no microphone on the main unit, 0017). arg3, arg4 RMS and peak output power in W, arg5 SWR: the calibrated values the safety core uses (0006, G7250 telemetry registers; 0007). | §4.4 TX_SENSORS |
| `HW_SENSORS_ENABLE`, `HW_SENSORS` | SHOULD | Supply voltage V, current A, temperature °C from the 0006 telemetry (supply voltage, PA or supply current, PA temperature), HIS-11. A sensor that does not exist is reported as `0` and flagged absent in `G7250_FEATURES` (C5.4). | §4.5 HW_SENSORS_ENABLE, HW_SENSORS |

### CW

| Command | Status | G7250 note | [TCI] |
|---------|--------|------------|-------|
| `CW_MACROS`, `CW_MSG` | SHOULD | Text to CW, generated in the server. Each start of transmission is a TX request under the arm (C5.5). | §3.2, §4.5 CW_MACROS, CW_MSG |
| `CW_MACROS_STOP` | MUST | Accepted from any client; unkeys at once. | §4.5 CW_MACROS_STOP |
| `CW_TERMINAL` | SHOULD | Terminal mode keeps TX keyed after the macro; still bound by the maximum TX time and the keyed timeout (C8). | §3.2.1, §4.5 CW_TERMINAL |
| `CW_MACROS_EMPTY`, `CALLSIGN_SEND`, `CW_MON` | SHOULD | Notifications, as [TCI]. | §4.5 |
| `CW_MACROS_SPEED`, `CW_MACROS_SPEED_UP`, `CW_MACROS_SPEED_DOWN`, `CW_MACROS_DELAY` | SHOULD | As [TCI]. | §4.2, §4.3 |
| `CW_KEYER_SPEED` | SHOULD | Keyer for the KEY input on the controller, if it reaches the main unit (HIS-17). | §4.2 CW_KEYER_SPEED |
| `KEYER` | MAY | Client-timed CW key. First press is a TX request under the arm. Jitter over TCP/WebSocket on level 2: TBD (G6). | §4.4 KEYER |

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
client recognises a profile server by `DEVICE:G7250;` and the reply to `G7250_EXT` (C5.2).

C5.1.4 Every extension MUST be implemented on both levels with the same meaning (0014). Where
level 1 maps an extension onto G7250-P2, the mapping is given.

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
  **[unverified for existing clients]**; the opt-in keeps generic clients on pure TCI 2.1.
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
  `nf`, `bin`, `sql`, `wfm`, `dig`, `spots`, `atu`, `ant`, `preamp`, `att`, `hw_sensors`, and
  `absent_<sensor>` for each `HW_SENSORS` field without a sensor (`absent_voltage`,
  `absent_current`, `absent_temperature`).
- A token appears only if the function works now; for example `tx` is absent on level 2
  before M7.

### C5.5 TX arm on TCI

C5.5.1 **Same safety core.** The arm, its preconditions, its drop events and the limits are
those of 0007, which sits below both levels (0011 point 3). TCI changes only how the arm is
requested and reported. A TCI client is never the P2 owner: on level 1 the P2 owner is
AetherSDR (0007, "Owner"); on level 2 the owner of the RF chain is the firmware's TCI level
itself (0011 point 2), and the TCI clients share control of it as [TCI] §3.1 describes.

C5.5.2 **Why an arm on TCI at all.** [TCI] has no arm: `TX_ENABLE` is server-controlled
information ([TCI] §4.3 TX_ENABLE). Without an arm, any TCI client on the LAN could key 100 W.
The profile keeps the rule of 0015: only software that knows the G7250 can enable transmit.
Once armed, generic TCI clients may key with the standard commands (`TRX`, `TUNE`, CW), which
is what full functionality for third-party applications needs (0012). This matches level 1,
where AetherSDR arms over P2 and its TCI clients key through AetherSDR.

C5.5.3 **Commands.**

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_TX_ARM_TOKEN` | notification | `G7250_TX_ARM_TOKEN:0,<hex8>;` | Current token; never `00000000` or `FFFFFFFF`, different from the previous one (0007 Decision 1). Sent on opt-in and whenever it changes. |
| `G7250_TX_ARM` | unidirectional control | `G7250_TX_ARM:0,<hex8>;` | `token XOR ARM_MAGIC` arms; `00000000` disarms. Any other value is rejected. `ARM_MAGIC` is the constant of part B (0007 Decision 1). |
| `G7250_TX_ARM_STATE` | notification | `G7250_TX_ARM_STATE:0,<state>,<generation>,<reject>,<drop>;` | `state`: `disarmed`, `armed`, `inhibited`. `generation`: +1 on every arm. `reject`, `drop`: last reason codes (C5.5.5), `none` if none. Sent on every change. |
| `G7250_TX_STATE` | notification | `G7250_TX_STATE:0,<keyed>,<source>,<mine>,<inhibits>;` | `keyed`: bool. `source`: `none`, `trx`, `tune`, `cw`, `keyer`, `atu`. `mine`: `true` if this connection made the current TX request. `inhibits`: hex8 bit field of active inhibits (layout as the limit status in 0006, part B). Sent per client on every change. |

C5.5.4 **Procedure.** (1) The client opts in (C5.2) and receives the token. (2) It sends
`G7250_TX_ARM:0,<token XOR ARM_MAGIC>;`. (3) The server checks the preconditions (C5.5.6
items 1–7), and either pushes `G7250_TX_ARM_STATE` = `armed` with a new generation or pushes the
reject reason. (4) **After the confirmation, the radio keys only on a TX request that arrives
after it** (0007 Decision 1 rule 2); a `TRX` state that was already `true` does not key. (5) The
server sends `TX_ENABLE:0,true;` to all clients when C5.5.6 holds.

C5.5.5 **Arm holder and drop events.** The connection that armed is the **arm holder**. Each
drop unkeys first, then disarms, then issues a new token, then pushes `G7250_TX_ARM_STATE`
with the reason and `TX_ENABLE:0,false;` (0007 Decision 1 rule 5). Drop events on TCI:

| # | Event | Reason | 0007 drop event |
|---|-------|--------|-----------------|
| 1 | Any client sends `G7250_TX_ARM:0,00000000;` | `HOST_DISARM` | 1 |
| 2 | Any client sends `STOP;` | `STOP` | 2 (RUN cleared) |
| 3 | The arm holder's connection closes (TCP close or reset, WebSocket close) | `HOLDER_LOST` | 3 (analogue of the watchdog) |
| 4 | The arm holder sends no frame for 1 s while armed (C8.2) | `WATCHDOG` | 3 |
| 5 | (L1) Any drop of the P2 arm between AetherSDR and the radio, with the P2 reason passed on unchanged | P2 reason | 1–13 |
| 6 | Any reset | (after reset: disarmed) | 5 |
| 7 | Entry into the fault state | `FAULT` | 6 |
| 8 | A limit trip with action DISARM or FAULT | `LIMIT_<name>` | 7 |
| 9 | Ethernet link down (HIS-14) | `LINK_DOWN` | 8 |
| 10 | Change of active level | `LEVEL_CHANGE` | 10 |
| 11 | Start of a firmware update or of a change of built-in limits (0008) | `MAINTENANCE` | 11 |
| 12 | A TX path that must be blocked is found not blocked | `FAULT` | 13 |
| 13 | The arm holder sends `G7250_EXT:false;` | `HOST_DISARM` | 1 |

0007 drop events 4 (takeover), 9 (session change) and 12 (rediscovery) have no TCI equivalent on
level 2, because TCI has no session takeover; on level 1 they reach TCI through row 5.

C5.5.6 **Conditions.** An arm request is accepted only if items 1–7 hold; `TX_ENABLE` is `true`
only if items 1–9 hold:

1. The device is started (`START`), (L1) AetherSDR has a running P2 session with the watchdog
   effectively on (0007 Decision 2.3).
2. Not in fault (0007 Sub-decision 5); no limit inhibit active (0007 Sub-decision 4).
3. Not keyed, and the TCI `TRX` and `TUNE` states are `false` (0007 Decision 1 rule 1).
4. This level is the active level (0011 point 2): (L2) level 2; (L1) level 1.
5. No firmware update in progress (0008).
6. The TX mode class is defined (C5.6): the modulation of the TX channel is not `WFM`. Reject
   reason `NO_MODE_CLASS` (0007 Decision 1 rule 1).
7. Transmit is implemented (L2: M7; L1: M4).
8. Armed.
9. The effective TX frequency (C4, split and XIT) lies inside a transmit range of [G7250-MAN]
   for the configured region (0007, limit "TX frequency").

Reject reasons: `NOT_STARTED`, `FAULT`, `INHIBIT`, `TX_ACTIVE`, `NOT_ACTIVE_LEVEL`,
`MAINTENANCE`, `NO_MODE_CLASS`, `NO_TX`, `BAD_VALUE` (wrong token value), plus, on level 1,
any P2 reject reason passed on unchanged. Final names are aligned with part B.

C5.5.7 **(L1) Mapping.** AetherSDR generates its own TCI token and keeps its own TCI arm
state. A valid `G7250_TX_ARM` from a TCI client makes AetherSDR perform the P2 arm handshake
(0007 Decision 1) and confirm on TCI only after the radio has confirmed on P2. AetherSDR MAY
also arm from its own user interface; that counts as an arm by a holder that never disconnects
while AetherSDR runs. Listed for the annex "Changes needed in AetherSDR" (0014, Consequences).

### C5.6 TX mode class: `G7250_TX_MODE_CLASS`

- Type: notification. `G7250_TX_MODE_CLASS:0,<class>;`, `class` one of `cw`, `ssb`, `am`, `fm`,
  `none`; names to be aligned with `TX_MODE_CLASS` in part B (0007, Sub-decision 4 rule 3).
- On TCI the class is **derived by the server** from `MODULATION` of the TX channel (C3.4),
  never declared by a client. On level 2 the DSP is on board, so the radio knows the mode
  (0011 point 1); the reason for a declared class on level 1, that the radio does not know the
  host's mode (0007, Sub-decision 4 rule 3), does not apply.
- (L1) AetherSDR MUST write the derived class to `TX_MODE_CLASS` over P2 before arming and on
  every change of the TX modulation (0007, Sub-decision 4 rule 3).
- The 25 W AM limit applies whenever the class is `am` ([G7250-MAN]; 0007). The power
  measurement applies whatever the class.

### C5.7 ATU

TCI 2.1 has no ATU command; `TUNE` is a tune carrier ([TCI] §4.2 TUNE: "Switching between
receive and Tune modes"), not an ATU tune cycle.

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_ATU` | bidirectional | `G7250_ATU:0,<bypass\|inline>;` (set, reply), `G7250_ATU:0;` (read) | Internal ATU out of or in line ([G7250-MAN], ATU: short press switches the tuner in). Refused while keyed (C7.6). |
| `G7250_ATU_TUNE` | unidirectional control | `G7250_ATU_TUNE:0;` | Starts a tune cycle. A TX request under the arm, with its own tune profile and time limit (0007 Sub-decision 4 rule 5, Sub-decision 6, "Internal ATU tuning"). Refused (no key) if C5.5.6 does not hold. |
| `G7250_ATU_STATE` | notification | `G7250_ATU_STATE:0,<state>;` | `bypass`, `inline`, `tuning`, `tuned`, `failed` (0006, "ATU state"). |

(L1) Mapped to the `ATU_TUNE` register and ATU state of the G7250 register map (0007; 0006;
part B). Tune power TBD (HIS-08, HIS-12).

### C5.8 Antenna

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_ANT` | bidirectional | `G7250_ANT:0,<1\|2>;` (set, reply), `G7250_ANT:0;` (read) | ANT1 or ANT2 ([G7250-MAN], "ANT SELECT"). The reply reports the antenna actually selected (0006). Refused while keyed (C7.6). Default after reset TBD (HIS-06; 0007 Decision 5). |

### C5.9 Front end (optional)

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_PREAMP` | bidirectional | `G7250_PREAMP:0,<bool>;` | Preamplifier, if it exists (HIS-07). The TCI `PREAMP` command is reserved ([TCI] §4.6) and so not used. |
| `G7250_ATT` | bidirectional | `G7250_ATT:0,<dB>;` | Attenuation in dB, steps TBD (HIS-07). |

### C5.10 Safety and fault state

| Command | Type | Form | Meaning |
|---------|------|------|---------|
| `G7250_SAFETY` | notification | `G7250_SAFETY:<state>,<fault_code>,<fault_class>,<fault_flags>,<trips>;` | `state`: `normal` or `fault`; `fault_code`: first cause, `none` if none; `fault_class`: `1` (clearable) or `2` (latched until reset); `fault_flags`: hex8; `trips`: counter (0007 Decision 5). |
| `G7250_FAULT_CLEAR` | unidirectional control | `G7250_FAULT_CLEAR;` | Clears a class-1 fault when the condition is gone (0007 Decision 5, option 5D). A clear does not re-arm. |
| `G7250_LIMIT` | bidirectional | `G7250_LIMIT:<name>,<value>;` (set, reply), `G7250_LIMIT:<name>;` (read) | Per-limit value, tighten only: a looser value is rejected (not clamped), the server replies with the current value (0007 Sub-decision 4 rule 1). Names and units as `LIMIT_<name>` in part B, including `MAX_TX_TIME` and `KEYED_TIMEOUT`. |
| `G7250_LIMIT_STATUS` | notification | `G7250_LIMIT_STATUS:<limiting>,<tripped>;` | Two hex8 bit fields, one bit per limit (0006, "limit status"). |

C5.10.1 Tightened limits are shared by all clients (synchronised as any bidirectional command,
[TCI] §3.3) and return to the built-in values when the last client disconnects, the level
changes, or the radio resets. This is the TCI equivalent of "per session" in 0007 Sub-decision
4 rule 2. (L1) AetherSDR writes the strictest value set by any of its clients to the P2
`LIMIT_<name>` registers.

### C5.11 Stream state: `G7250_STREAM_STATE`

- Type: notification, per client. `G7250_STREAM_STATE:0,<stream>,<state>,<reason>;`,
  `stream` one of `iq`, `audio`, `line_out`, `tx_audio`; `state` `running`, `stopped`,
  `refused`; `reason` `none`, `budget`, `rate`, `not_supported`.
- [TCI] has no reply to `IQ_START` or `AUDIO_START` ([TCI] §4.3), so a client cannot see that a
  stream was refused. This notification is that report, the TCI counterpart of the stream
  status register of 0004 (Consequences).

---

## C6 Streams

C6.1 **Block format.** Every stream block MUST use the 64-byte header of [TCI] §3.4
(`receiver`, `sample_rate`, `format`, `codec` = 0, `crc` = 0, `length`, `type`, `channels`,
`count`, `reserv[7]` = 0), followed by `length` samples. Clarifications (Annex C-C):

- C-C4 **Byte order.** [TCI] does not state it. The header fields and the samples are
  little-endian **[unverified: assumed from the C structure on common PC platforms; to be
  checked against a public client implementation]**.
- C-C5 **Block size.** The binary frame carries the header and `length` samples only, not the
  full `data[16384]` **[unverified]**; the data part MUST NOT exceed 16384 bytes ([TCI] §3.4).
- C-C6 **count.** Incremented per block within a stream; kept separately for RX audio and
  TX_CHRONO and reset on each switch between TX and RX ([TCI] §3.4). The profile also keeps it
  per stream for IQ and line-out.

C6.2 **IQ stream** (`type` = 0, IQ_STREAM).

| Item | Value | Source |
|------|-------|--------|
| Receiver | 0 | `TRX_COUNT:1` (C3.2); HIS-02 |
| Rates | 48, 96, 192, 384 kHz | [TCI] §4.3 IQ_SAMPLERATE; 0004 Decision point 1 (the same four rates on level 1); 384 kHz only where 0004 point 6 allows it |
| Channels | 2 (I and Q); complex samples = `length` / `channels` | [TCI] §3.4 |
| Format | `FLOAT32` (3) **proposed**; `format` MUST state the format in use | [TCI] §3.4 SampleType. [TCI] does not fix the IQ format **[unverified which formats clients accept]**. |
| Samples per block | at most 16384 bytes of data: 2048 complex samples at FLOAT32 | [TCI] §3.4 |
| Rate per client | [TCI] says "The rate is individual for each client" ([TCI] §4.3 IQ_SAMPLERATE). (L2) With one DDC the server MAY offer only one IQ rate at a time; a different rate requested while another client streams IQ is "ignored, the server replies with the current rate" ([TCI] §4.3), and `G7250_STREAM_STATE` reports `rate`. | 0004 (one DDC); HIS-02 |

(L2) IQ comes from the on-board DDC, the same chain as level 1 (0004 Decision point 1); the
conversion from the 24-bit DDC output to FLOAT32 runs on the processor (HIS-18, G6).

C6.3 **Audio streams.**

| Stream | `type` | Direction | Rates | Format, channels, samples | Notes |
|--------|--------|-----------|-------|---------------------------|-------|
| RX audio | 1 | server → client | `AUDIO_SAMPLERATE` (C4) | `AUDIO_STREAM_SAMPLE_TYPE`, `_CHANNELS`, `_SAMPLES` (C4) | (L2) Demodulated **on board** (0011 point 1). The main unit has no speaker or audio output (0017), so TCI is the only audio output on level 2. (L1) Demodulated in AetherSDR. |
| TX audio | 2 | client → server | as RX audio of this client ([TCI] §4.3 AUDIO_SAMPLERATE note) | as RX audio | Sent by the client in answer to TX_CHRONO, with the number of samples in TX_CHRONO's `length` ([TCI] §3.4). (L2) Modulated on board. |
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
  needs either fewer audio clients, mono or int16 audio, or a lower IQ rate. To be settled at G6.
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

C7.3 **Priority.** [TCI] gives "the highest priority" to the server's own operator and, among
clients, priority to the first one ([TCI] §3.5). In the profile, the safety core has the highest
priority, above any client and above the server's own user interface (0011 point 3). Whether
the controller (head) may operate the radio on level 2, and at what priority, is open (0007,
Resolved item 6: "Revisit for level 2"; HIS-17). Until decided, controller inputs on level 2
are reported (`TX_FOOTSWITCH`) and never key the radio, as on level 1 (0007 Sub-decision 6).

C7.4 **Who may transmit.** While armed, any connected client MAY send a TX request (`TRX`
true, `TUNE` true, `KEYER` press, `CW_MACROS`, `CW_MSG`, `G7250_ATU_TUNE`). The client whose
request keys the radio is the **keying client** (`G7250_TX_STATE` `mine` = `true`). Any client
MAY end a transmission (`TRX` false, `TUNE` false, `CW_MACROS_STOP`, `G7250_TX_ARM:0,00000000;`,
`STOP`); these are never blocked by the 200 ms monopoly ([TCI] §4.7 note 6) and take effect
immediately. Making TX stop is always allowed, as tightening is always allowed (0011 point 3).

C7.5 **Two clients key.** Only one TX request can be active, because there is one transmitter
([G7250-MAN]; `TRX_COUNT:1`):

1. The first TX request that the server processes keys the radio, following [TCI] §3.5 ("the
   priority is behind the first one").
2. A TX request from another client while keyed MUST NOT change the TX source or the TX audio.
   For `TRX`, `TUNE` and `G7250_ATU_TUNE` the server replies with the current state; `CW_MACROS`
   and `CW_MSG` from another client are ignored; `KEYER` from another client is ignored.
3. CW queueing of [TCI] §3.5 (a `CW_MACROS` added in line, a `CW_MSG` that replaces a macro)
   applies only to requests from the keying client.
4. TX audio from any client other than the keying client is discarded, and TX_CHRONO is sent
   only to the keying client.
5. Because `TRX` is synchronised, every client sees `TRX:0,true;`; a client finds out whether
   the transmission is its own from `G7250_TX_STATE` (C5.5.3). A generic client cannot tell,
   which is a known limit of [TCI] (Annex C-A).
6. When the keying client's connection closes, the server unkeys (C8.3).

C7.6 **Changes while keyed.** While keyed, the server MUST refuse (reply with the current value)
changes of `MODULATION` of the TX channel, `G7250_ANT` and `G7250_ATU`, from any client
**(profile choice; 0007 lists such changes as harmless only "while not keyed")**. A change of
`VFO`, `SPLIT_ENABLE` or `XIT_OFFSET` that moves the effective TX frequency outside a transmit
range MUST unkey (0007, limit "TX frequency"); inside a range it is followed.

---

## C8 Safety: limits and timeouts

C8.1 **Limits.** All limits of 0007 Sub-decision 4 apply on both levels with the same built-in
values, actions (WARN, REDUCE, UNKEY, DISARM, FAULT) and recovery (0007 rule 5; 0011 point 3).
They are reported over TCI by `G7250_LIMIT_STATUS`, `G7250_TX_STATE` and `G7250_SAFETY`, and
tightened by `G7250_LIMIT` (C5.10). The maximum continuous TX time is 5 min built in, UNKEY
only, arm kept (0007, Resolved item 3); it applies to every TX source, including
`CW_TERMINAL` and `TUNE`.

C8.2 **What replaces the P2 watchdog.** The P2 watchdog is "no C&C packet for 1 s" [P2] (0007
Decision 2). TCI has no keep-alive of its own. The profile uses the WebSocket ping (RFC 6455
§5.5.2: an endpoint that receives a Ping "MUST send a Pong frame in response"), so that
generic clients keep the connection alive without knowing the profile:

| Timer | Applies to | Server duty | Timeout and action | 0007 counterpart |
|-------|------------|-------------|--------------------|------------------|
| Holder watchdog | the arm holder, while armed | send a WebSocket Ping at least every 250 ms | no frame of any kind (including Pong) from the arm holder for **1 s** → drop the arm, `WATCHDOG` | Decision 2, base watchdog 1 s; drop event 3 |
| Keyed timeout | the keying client, while keyed | send a WebSocket Ping at least every 100 ms | no frame from the keying client within `KEYED_TIMEOUT` (default **500 ms**, tighten only, floor 100 ms) → UNKEY, arm kept | Decision 2, `KEYED_TIMEOUT`; Resolved item 2 |
| TX audio underrun | the keying client, while keyed with source `tci` | send TX_CHRONO ([TCI] §3.4) | no TX_AUDIO_STREAM block for longer than `TX_STREAM_AUDIO_BUFFERING` + TBD ms → UNKEY, arm kept | Decision 2, TX IQ underrun (TBD, HIS-18) |
| Connection loss | arm holder / keying client | — | TCP close, reset or WebSocket close: holder → drop the arm (`HOLDER_LOST`); keying client → UNKEY | drop event 3 |

C8.2.1 **Deviation (Annex C-B, C-B1).** [TCI] allows a client that is not ready to "not send a
response" to TX_CHRONO, and calls a block of zero samples "preferable" ([TCI] §3.4). The profile
requires the keying client to answer every TX_CHRONO while keyed with source `tci`, with zero
samples if it has no signal; a missing answer for longer than the underrun time unkeys.
**[unverified whether existing clients always answer]**; if not, the underrun time is the only
tolerance.

C8.2.2 The Ping duty is a minimum; the server MAY treat any frame from the client as a sign of
life. The 1 s and `KEYED_TIMEOUT` values are the same as level 1 so that both levels behave
alike (0014).

C8.2.3 **(L1)** AetherSDR MUST apply C8.2 to its TCI clients. Independently, the radio applies
the P2 watchdog and keyed timeout to AetherSDR (0007 Decision 2), so a crash of AetherSDR
unkeys the radio even if AetherSDR's TCI side cannot act.

C8.3 **Keying client gone, holder still there.** If the keying client disconnects while the arm
holder stays, the server unkeys and keeps the arm (UNKEY, analogue of the keyed timeout).

C8.4 **Fault state.** Entry, effect and clearing as 0007 Decision 5. In fault, RX and RX streams
continue, so clients can still see the radio and the fault (0007 Decision 5, "Effect").
`TX_ENABLE` is `false`, arm requests are rejected with `FAULT`.

C8.5 **State after reset** is that of 0007 Decision 5: not armed, new token, built-in limits.
(L2) After a reset the TCI server starts with `TRX` and `TUNE` `false`, `RECEIVE_ONLY` and
`TX_ENABLE` as C3.2 and C5.5.6.

C8.6 **No security.** The arm prevents accidental transmission by software that does not know
the G7250; it is not security ("this is not security", 0007 Decision 1 rule 3). TCI has no
authentication [TCI], and any client on the LAN can opt in and read the token. LAN security for
TCI is an open point (Annex C-A; compare 0008, "Security on a LAN").

---

## C9 Conformance tests

One line per test; tests run against the reference model in g7250-testbench and against both
implementations (0014, Consequences; 0001 item 5). Ids are stable.

| Id | Test |
|----|------|
| T-C2-01 | A WebSocket client connects on the configured port; commands arrive in text frames, streams in binary frames. |
| T-C2-02 | Several complete commands in one text frame are all executed. |
| T-C2-03 | (L2) `clients_max` clients connect; the next one receives `G7250_REFUSED:busy;` and close 1008; the listener accepts again afterwards. |
| T-C2-04 | (L2) A level change closes all connections with 1001 after `LEVEL_CHANGE`. |
| T-C3-01 | Initialization order is PROTOCOL, DEVICE, RECEIVE_ONLY, TRX_COUNT, CHANNELS_COUNT, VFO_LIMITS, IF_LIMITS, MODULATIONS_LIST, READY, then state. |
| T-C3-02 | Values match C3.2; `CHANNEL_COUNT` is never sent. |
| T-C3-03 | `IF_LIMITS` is resent after a receiver sample-rate change. |
| T-C3-04 | A `VFO` or `DDS` set to 40 MHz or outside VFO_LIMITS is not followed; the current value is replied. |
| T-C3-05 | No `G7250_` command reaches a client that has not opted in. |
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
| T-C5-03 | A correct `G7250_TX_ARM` arms with a new generation; a wrong value is rejected with `BAD_VALUE`. |
| T-C5-04 | Each precondition of C5.5.6 items 1–7, when false, rejects the arm with its reason. |
| T-C5-05 | After arming, a `TRX` state already `true` does not key; a new 0→1 request does. |
| T-C5-06 | Each drop event of C5.5.5 unkeys, disarms, issues a new token and reports the reason. |
| T-C5-07 | `TX_ENABLE` is `true` exactly when C5.5.6 items 1–9 hold, and is resent on every change. |
| T-C5-08 | `G7250_TX_MODE_CLASS` follows `MODULATION`; `WFM` gives `none` and blocks arming. |
| T-C5-09 | In class `am`, output power stays within the AM limit at `DRIVE:0,100`. |
| T-C5-10 | `G7250_ATU_TUNE` needs the arm, follows the tune time limit and reports `tuned` or `failed`. |
| T-C5-11 | `G7250_ANT` and `G7250_ATU` are refused while keyed. |
| T-C5-12 | `G7250_LIMIT` accepts stricter values, rejects looser values, and resets after the last client leaves. |
| T-C5-13 | `G7250_FAULT_CLEAR` clears a class-1 fault only when the condition is gone and never re-arms. |
| T-C5-14 | (L1) A TCI arm causes a P2 arm handshake and is confirmed only after the radio confirms. |
| T-C5-15 | (L1) Every P2 drop event is reported on TCI with the P2 reason. |
| T-C6-01 | Stream headers are 64 bytes with correct receiver, rate, format, length, type, channels and count. |
| T-C6-02 | IQ streams at each offered rate without loss for a set duration; a test tone appears at the right offset and sign. |
| T-C6-03 | RX audio honours sample type, channels and samples per block. |
| T-C6-04 | TX_CHRONO goes only to the keying client; its TX audio is transmitted; others' TX audio is discarded. |
| T-C6-05 | (L2) A stream start over the budget is not followed and is reported as `budget`. |
| T-C6-06 | (L2) A second IQ rate requested while another client streams IQ is refused with the current rate. |
| T-C7-01 | A parameter set by one client is reported to all others. |
| T-C7-02 | With two clients, the first TX request keys; the second's `TRX`, `TUNE`, CW and KEYER are refused or ignored. |
| T-C7-03 | Any client can unkey with `TRX` false, `TUNE` false, `CW_MACROS_STOP`, disarm or `STOP`, immediately. |
| T-C7-04 | `G7250_TX_STATE` `mine` is true only for the keying client. |
| T-C7-05 | A VFO, split or XIT change that moves TX outside a transmit range unkeys. |
| T-C8-01 | Arm holder silent for 1 s (Pong suppressed) → arm dropped with `WATCHDOG`. |
| T-C8-02 | Keying client silent for `KEYED_TIMEOUT` → unkey, arm kept. |
| T-C8-03 | TX audio stops answering TX_CHRONO → unkey after the underrun time, arm kept. |
| T-C8-04 | Arm holder TCP reset → arm dropped with `HOLDER_LOST`; keying client TCP reset → unkey. |
| T-C8-05 | Maximum TX time (5 min built in, also with `CW_TERMINAL` and `TUNE`) unkeys and keeps the arm. |
| T-C8-06 | In fault, RX streams continue, `TX_ENABLE` is false and arm requests are rejected. |
| T-C8-07 | After reset, the server is disarmed with a new token, built-in limits, and `TRX`/`TUNE` false. |

---

## Annex C-A — Open points and TBDs

| # | Point | Depends on |
|---|-------|------------|
| A1 | Whether level 2 can be built at all: compute for DSP, WebSocket and TCI; memory; network stack. All (L2) requirements wait for it. | G6, HIS-18, HIS-14 |
| A2 | Number of receivers; whether `TRX_COUNT` stays 1 and whether channel B can be demodulated. | HIS-02, G6 |
| A3 | Default TCP port (C2.4); candidate 40001 to be checked against a public source. | ON8ST, `sources.md` |
| A4 | Whether port 1024 (P2 discovery) stays open on level 2; sets `clients_max` 5 or 6 (C2.5). | part A / B3, 0008 |
| A5 | CH394Q TCP server behaviour: does the listening socket become the connection (C2.5.3)? Socket buffer split in TCP mode (C6.5). | HIS-14, [CH394] |
| A6 | IQ sample format (FLOAT32 proposed), byte order (little-endian assumed) and frame size of stream blocks: to be checked against a public TCI client. | public client source |
| A7 | Whether existing clients tolerate unknown server commands (motivates the opt-in, C5.2), and whether they always answer TX_CHRONO (C8.2.1). | public client sources |
| A8 | `NFM` vs `FM` as the narrow FM mode name; full list of TCI mode names, which [TCI] does not give. | public client sources |
| A9 | Stream budget on level 2 (C6.4): number of IQ streams, audio formats, aggregate with TCP and WebSocket overhead. | G6, HIS-14, HIS-18 |
| A10 | TX audio underrun time (C8.2). | HIS-18, 0007 (TBD) |
| A11 | Calibration of `RX_SENSORS` dBm on level 2. | HIS-11, G6 |
| A12 | `DRIVE` 0–100 to power mapping; tune power. | HIS-12, HIS-08 |
| A13 | Microphone, PTT and KEY from the controller; whether the controller may operate the radio on level 2 (0007 Resolved item 6). | HIS-17, HIS-10, ON8ST |
| A14 | Preamplifier and attenuator steps (C5.9). | HIS-07 |
| A15 | Default antenna after reset. | HIS-06 |
| A16 | Mode-class names, reason codes, limit names and `ARM_MAGIC`: to be aligned with part B. | part B |
| A17 | LAN security for TCI (no authentication in [TCI]); whether TX on TCI should be restricted to the arm holder (stricter than C7.4) as an option. | ON8ST, 0008 |
| A18 | A generic client cannot tell whether a synchronised `TRX:0,true;` is its own transmission (C7.5 item 5). Known limit; no fix proposed. | — |
| A19 | `sources.md` corrections found while reading [TCI]: `CHANNELS_COUNT` (not `TRX_COUNT`) is the renamed `CHANNEL_COUNT` ([TCI] §2.2, §4.1); the document control table puts the rename under 2.0, section 2.2 under 2.1. RFC 6455 to be added as a source. | coordinator |
| A20 | Annex "Changes needed in AetherSDR", TCI section (0014): DEVICE `G7250`, CHANNELS_COUNT 2, opt-in and all extensions, TCI arm mapped to the P2 arm (C5.5.7), derived mode class written to P2, C8.2 timers, limit tightening passed to P2. | AetherSDR, ON8ST go |

## Annex C-B — Deviations from [TCI]

| # | Deviation | Section |
|---|-----------|---------|
| C-B1 | The keying client must answer every TX_CHRONO while keyed with source `tci`; a missing answer unkeys after the underrun time. [TCI] §3.4 allows no answer. | C8.2.1 |
| C-B2 | Transmit needs a G7250 arm; `TRX`, `TUNE`, `KEYER` and CW text do not key without it. [TCI] has no arm. | C5.5 |
| C-B3 | A TX request from a second client while keyed does not change the TX source; stop requests are never held by the 200 ms monopoly. | C7.4, C7.5 |
| C-B4 | (L2) Only one IQ rate at a time may be offered, although [TCI] makes the rate individual per client; the refusal uses [TCI]'s own "ignored, current rate replied" rule. | C6.2 |
| C-B5 | `TRX` without the `tci` source is refused when there is no microphone path, instead of taking a microphone signal. | C4 |
| C-B6 | Changes of TX modulation, antenna and ATU are refused while keyed. | C7.6 |

## Annex C-C — Clarifications of [TCI]

| # | Clarification | Section |
|---|---------------|---------|
| C-C1 | Commands are in text frames, several complete commands per frame allowed, never split over frames. | C2.2 |
| C-C2 | The WebSocket upgrade is accepted on `/` and should be on any path. | C2.3 |
| C-C3 | A frequency inside `VFO_LIMITS` but outside the receive range is not followed; the current value is replied. | C3.3 |
| C-C4 | Stream header and samples are little-endian **[unverified]**. | C6.1 |
| C-C5 | A stream frame carries the header and `length` samples only **[unverified]**. | C6.1 |
| C-C6 | `count` is kept per stream also for IQ and line-out. | C6.1 |
| C-C7 | [TCI] lists `TX_ENABLE` under §4.3 "Unidirectional Control Commands" but gives its type as "Bidirectional control"; the profile treats it as server-controlled state, synchronised to all clients, with client sets ignored, as its note says. | C4 |
| C-C8 | [TCI] lists `KEYER` under §4.4 "Notification Commands" but gives its type as "Unidirectional control", "Sent only by the TCI client"; the profile treats it as a client command. | C4 |

## Sources

- [TCI] TCI Protocol, Ver. 2.1, September 2026, "Expert Group" LLC: §1.4, §2, §3.1–3.5, §4.1–4.7
  (`sources.md`). Read in full for this part, 2026-11-19, from the text extraction of the PDF.
- [AETHER] AetherSDR README (TCI server, protocol 2.1).
- [G7250-MAN] Xiegu G7250 Operation Manual: receive and transmit ranges, modes, TX power, ATU,
  antennas, interfaces.
- [CH394] WCH CH394 manual 1, V1.2 (8 sockets), through `analysis/ch394-network-budget.md` and
  0008.
- [P2] openHPSDR Ethernet Protocol V4.4, through 0007 (watchdog).
- RFC 6455, The WebSocket Protocol (§5.2, §5.3, §5.5.2, §7.4.1) — **not yet listed in
  `sources.md`**.
- RFC 2119, RFC 8174 (BCP 14).
- Decisions 0001, 0004, 0006, 0007, 0008, 0011, 0012, 0013, 0014, 0015, 0017.
- `analysis/ch394-network-budget.md` (Addendum, "TCI (level 2)"); `open-questions-his.md`
  (HIS-02, -06, -07, -08, -10, -11, -12, -14, -17, -18); design note §6 (milestones, G6).

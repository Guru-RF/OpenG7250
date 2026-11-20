# 0021 — Choices in the G7250 TCI profile (spec part C)

- Status: under review by ON8ST (2026-11-20); review of rc4 in progress. His first two remarks, the controller and returning to the stock firmware, are handled in 0023 and 0024. Section-level status lines below are superseded by this line.
- Date: 2026-11-19
- Builds on: 0003 (discovery reply byte 4), 0004 (rates, SPI target), 0007 (watchdog and
  safety), 0008 (management channel, socket budget, LAN security), 0011 (two levels), 0012
  (full functionality), 0013 (AetherSDR), 0014 (one TCI profile), 0017 (no audio on the main
  unit), 0019 (reference model), 0022 (rc1 review fixes, proposed; §18–§26).

## Context

Spec part C, draft 1, left a number of points open that no HIS answer and no gate G6 result
will settle: they are design choices. Release candidate rc1 requires that every remaining
"TBD" carries a HIS id or "G6"; everything else is decided here. Each sub-section below
gives the chosen behaviour, the alternatives considered and the reason. Sources: [TCI]
(protocol 2.1, read in full 2026-11-19), [AETHER-SRC] (AetherSDR source, commit 9f7cbeb of
2026-11-18, as described in `spec/annex-aethersdr.md` §2.4 and G-13), [RFC6455],
[G7250-MAN], [CH394], and the decisions listed above.

## 1. Who may key once armed

**Chosen.** Once the radio is armed, any connected client MAY send a TX request (as draft 1,
C7.4). In addition, a new extension `G7250_TX_POLICY:<any|holder>;` lets the user restrict
keying to the arm holder. Default `any`. Any opted-in client may set `holder` (tightening);
only the arm holder may set `any` (loosening). The policy returns to `any` at the same points
as tightened limits: when the last client disconnects, on a level change and on reset (part C
C5.10.1). Stop requests are always accepted from every client, whatever the policy.

Alternatives:

- **B. Only the arm holder may key, always.** For: one TX authority per arm, closest to the P2
  owner model (0007 Decision 1 rule 1). Against: generic TCI clients (logging, digital-mode
  and contest programs) could never transmit on level 2, because they do not know the arm;
  this breaks full functionality (0012). Against: differs from level 1, where AetherSDR arms
  over P2 and its TCI clients key through it (0013, 0014).
- **C. The arm holder names the clients that may key.** For: fine-grained. Against: TCI has no
  client identity apart from the connection [TCI] §3.1; a list of connections is fragile and
  needs a user interface in the holder.
- **D. Policy set only through the management channel.** For: authenticated (0008 S2).
  Against: a per-operation choice would need a management write each time; the arm is not
  security anyway (0007 Decision 1 rule 3).

Reason: the arm's purpose is to stop software that does not know the G7250 from enabling
transmit (0015; 0007 Decision 1 rule 3), not to decide which application keys. A
G7250-aware arm holder must stay connected and alive for the arm to persist (part C C5.5.5
rows 3 and 4), so a generic client can key only while such a holder is present, and every
transmission stays under the shared safety core (0011 point 3). The tighten-only policy gives
users who want a single TX authority that option, with the same "tighten only" pattern as
the limits (0007 Sub-decision 4 rule 1). On level 1, when AetherSDR armed from its own user
interface, the holder is AetherSDR itself; `holder` then means only AetherSDR's own user
interface keys.

## 2. Default TCP port

**Chosen.** Default TCP port **50001** on both levels. This is our choice; it is not a
standard: [TCI] states no default port (`sources.md`, [TCI]). It is the port AetherSDR's TCI
server listens on by default ([AETHER-SRC], `src/core/TciServer.h:92`, per
`spec/annex-aethersdr.md` §2.4). The port stays configurable: on level 2 through the
management channel configuration (0008), on level 1 in AetherSDR. The management port (part
A, A1.3) MUST NOT be 50001.

Alternatives:

- **B. 40001.** For: draft 1 believed it to be common among TCI clients. Against: no public
  source was read for it, and it differs from AetherSDR, so a user would have to change the
  client's port when moving between levels.
- **C. No default; the port must be configured.** Against: every client needs set-up before
  first use; nothing is gained.

Reason: one default on both levels lets an application move between level 1 and level 2
without reconfiguration (0014, Option A "For").

## 3. Port 1024 on level 2 and the number of clients

**Chosen.** Port 1024 (P2 discovery) stays answerable on level 2. This is already required
elsewhere: while level 2 is active the radio answers discovery with byte 4 = 0x03 (0003,
discovery reply row 4; part B B3.1, A2.5). With management (1), port 1024 (1) and one spare
listener (1), **5** sockets are left for TCI clients ([CH394] 8 sockets; 0008, Socket budget).
`clients_max` is 5, on the assumption of part C C2.5.3 (to be checked, HIS-14).

Alternatives:

- **B. Close port 1024 on level 2; 6 clients.** Against: contradicts 0003 and part B B3.1; a
  P2 host could no longer see that the radio exists and is in use, and a user would not find
  the radio to switch it back to level 1 from a P2 application.
- **C. No spare listener; 6 clients.** Against: a seventh client would get no answer at all
  instead of a clean `G7250_REFUSED:busy;` (part C C2.5.2).

Reason: the decisions on discovery are accepted; one TCI client fewer is the cost.

## 4. `PROTOCOL` program name

**Chosen.** Both levels send `PROTOCOL:ExpertSDR3,2.1;`. The first argument is treated as a
compatibility value, not as an identification of the G7250: clients identify the radio by the
reply to `G7250_EXT` (part C C5.2) and by `G7250_PROFILE`, never by `PROTOCOL`.

Alternatives:

- **B. `G7250-FW` on level 2, AetherSDR's own value on level 1.** For: honest program name;
  [TCI] §4.1 PROTOCOL calls arg1 the "program name". Against: the two levels would differ,
  against 0014; and AetherSDR, the one TCI server already used with real clients, sends
  `ExpertSDR3` ([AETHER-SRC] `TciProtocol.cpp:380`, per `spec/annex-aethersdr.md` §2.4),
  which suggests that some clients expect it **[unverified: the reason is not stated in what
  we read]**.
- **C. Leave arg1 free per implementation.** Against: same as B; behaviour of clients that
  look at it would differ per level.

Reason: one value on both levels, and the value already in use with existing clients carries
the least compatibility risk. Because no G7250 behaviour depends on it, the choice can be
changed in a later profile version without touching the safety core. ON8ST to confirm that
using the name "ExpertSDR3" as a compatibility value is acceptable.

## 5. `DEVICE` name

**Chosen.** Level 2 sends `DEVICE:G7250;`. Level 1 (AetherSDR) SHOULD send `DEVICE:G7250;`
and MAY keep its current value `AetherSDR` where a client needs it; AetherSDR chose that value
for WSJT-X behaviour ([AETHER-SRC] `TciProtocol.cpp:370–377`, per `spec/annex-aethersdr.md`
G-13 and Q-O5). A client MUST NOT rely on `DEVICE` to recognise a profile server; it uses the
reply to `G7250_EXT` (part C C5.1.3).

Alternatives:

- **B. `DEVICE:G7250;` required on both levels.** For: [TCI] §1.4 speaks of "maintaining the
  device model designation". Against: may change WSJT-X behaviour on level 1 for reasons we
  have not read; forcing it risks a regression in AetherSDR's existing users.
- **C. Leave `DEVICE` to each implementation.** Against: level 2 would then have no defined
  value.

Reason: keeps AetherSDR free to protect a known client behaviour, while recognition of the
profile no longer depends on the device name.

## 6. TX mode class on TCI

**Chosen.** On TCI the TX mode class is derived by the server from `MODULATION` of receiver 0
([TCI] §4.2 MODULATION: arg1 is the receiver number, so channels A and B share one mode):
`LSB`, `USB`, `DIGL`, `DIGU` → `ssb`; `CW` → `cw`; `AM` → `am`; `NFM` → `fm`; `WFM` →
`none`. A client cannot declare a class. With class `none`, an arm request is rejected with
`NO_MODE_CLASS` and `TX_ENABLE` is `false`; if `MODULATION` changes to `WFM` while armed and
not keyed, the arm is kept, TX requests are refused and `TX_ENABLE` becomes `false`. On level
1, AetherSDR writes the derived class to the P2 `TX_MODE_CLASS` register before arming and on
every change (0007 Sub-decision 4 rule 3).

Alternatives:

- **B. Client-declared class (as P2).** For: same as level 1 on P2. Against: on level 2 the
  DSP is on board, so the radio knows the mode (0011 point 1); a declared class could
  disagree with the mode actually modulated. Generic clients do not know the extension.
- **C. Derived, and a declared class must match.** Against: adds a failure path with no gain.
- **D. WFM transmits under a class of its own.** Against: [G7250-MAN] gives no WFM transmit
  power, so there is no built-in limit for it (0007 Sub-decision 4).

Reason: the server knows the mode; deriving it removes a way to arm with a wrong power class.

## 7. TX_CHRONO answers and the TX audio underrun time

**Chosen.** While keyed with source `tci` in a mode other than `CW`, the keying client MUST
answer every TX_CHRONO with a TX_AUDIO_STREAM block (zero samples if it has no signal). If no
TX audio block arrives for longer than `TX_STREAM_AUDIO_BUFFERING` + 500 ms, the server
unkeys and keeps the arm. This is a deviation from [TCI] §3.4, which allows no answer; it is
listed in part C Annex C-B. The 500 ms equals the default `KEYED_TIMEOUT` (0007, Resolved 2)
and is a fixed value of the profile, so it does not depend on a hardware FIFO (the level-1 TX
IQ underrun of 0007 Decision 2 does, HIS-18).

Alternatives:

- **B. Follow [TCI]: no answer required; rely on the keyed timeout and maximum TX time.**
  Against: a client whose audio path hangs while its WebSocket stack still answers Pings keeps
  the radio keyed for up to 5 minutes (0007, Resolved 3).
- **C. Unkey on the first missing answer.** Against: one late block on a busy LAN would end a
  transmission; the buffer of `TX_STREAM_AUDIO_BUFFERING` exists for that ([TCI] §4.3).

Reason: [TCI] itself calls a zero-sample answer "preferable" ([TCI] §3.4), so a well-behaved
client already answers; the deviation only acts on a client that has stopped.

## 8. Changes while keyed

**Chosen.** While keyed, the server refuses (replies with the current value) changes of
`MODULATION`, `G7250_ANT` and `G7250_ATU` from any client. `DRIVE`, `TUNE_DRIVE`, filter,
receive-side and front-end settings are followed. A change of `VFO`, `SPLIT_ENABLE` or the
XIT offset that moves the effective TX frequency outside a transmit range unkeys (0007, limit
"TX frequency"); inside a range it is followed.

Alternatives:

- **B. Unkey, then follow the change.** For: the user gets what was asked. Against: a client
  that changes mode by accident ends another client's transmission; switching antenna relays
  must not happen under RF either way.
- **C. Follow all changes while keyed.** Against: antenna and ATU switching under RF (hot
  switching) risks the relays and the PA; a mode change while keyed changes the power class
  under a running transmission.

Reason: 0007 lists such changes as harmless only "while not keyed" (Decision 1 rule 5);
refusal keeps the transmission and the power class stable and is visible to the client.

## 9. The controller on level 2

**Chosen.** In profile version 1 the controller (head) has no control on level 2, as on level
1: inputs that reach the main unit (HIS-17) are reported (`TX_FOOTSWITCH`) and never key the
radio (0007 Sub-decision 6, Resolved 6). The priority that [TCI] §3.5 gives to the server's
own operator is not given to the controller. Rule for revisiting: only after HIS-10 and
HIS-17 are answered and M7 is reached, by a new decision and a new profile version; any
controller TX path would then be a TX request under the same arm and limits.

Alternatives:

- **B. Controller as the server's own operator, with the highest priority ([TCI] §3.5).** For:
  standalone use. Against: depends on HIS-17 (whether the controller's inputs and display
  reach the main unit) and HIS-10 (whether the firmware can block the controller's own TX
  path); a second TX authority needs its own arm rules (0007 Sub-decision 6, option 6C).
- **C. Controller keys only when no TCI client is connected.** Against: as B, plus behaviour
  that changes with the number of connected clients.

Reason: nothing is known yet about the CTRL link; adding control later is a tightening-free,
backwards-compatible extension of the profile.

## 10. LAN security on TCI

**Chosen.** TCI has no authentication [TCI]; the profile does not add any to the TCI
connection, so generic clients keep working. Position: level 2 is meant for a trusted LAN,
and the arm is not security (0007 Decision 1 rule 3). Mitigations on level 2:

1. **Reach.** TCI connections are accepted only from source addresses inside the radio's own
   subnet, as the management channel does (0008 S4).
2. **Allow-list.** An optional list of up to 8 IPv4 addresses or prefixes, set through the
   management channel as an authenticated configuration write (0008 S2, C-1 to C-4). When the
   list is not empty, only matching addresses are accepted.
3. A refused connection is closed without the WebSocket handshake and logged with its source
   address (0008 L-2).

On level 1, AetherSDR's listener is its own configuration (0013); it SHOULD offer an
equivalent restriction. This adds a configuration item to the management channel (part A,
A1.6).

Alternatives:

- **B. Add authentication to TCI (for example a token in the upgrade request).** Against:
  generic TCI clients cannot send it, so no third-party application would work (0012).
- **C. TLS (wss).** Against: [TCI] defines no TLS; clients would not connect; the processor
  cost is unknown (HIS-18).
- **D. No mitigation.** Against: any device on any routed network could reach the TCI port.

Reason: the reach rule costs nothing and matches 0008; the allow-list lets an owner narrow it
further without breaking standard clients.

## 11. IQ sample format

**Chosen.** IQ streams use `FLOAT32` (SampleType 3, [TCI] §3.4) on both levels, and the
`format` field states it. There is no `INT24` IQ in profile version 1. On level 2, if the SPI
budget (0004 Decision point 6) does not allow FLOAT32 IQ at 384 kHz with the other streams,
the IQ rate offered is reduced (part C C6.4), not the format.

Alternatives:

- **B. `INT24` IQ.** For: 25 % less payload: 18.4 instead of 24.6 Mbit/s at 384 kHz
  (part C C6.4), and the DDC output is already 24-bit (0004 Decision point 1), so no
  conversion. Against: [TCI] has no command for a client to choose the IQ format
  (`AUDIO_STREAM_SAMPLE_TYPE` covers audio only, [TCI] §4.3), so a client that expects float
  could not ask for it; [TCI]'s audio default is float32 ([TCI] §4.3
  AUDIO_STREAM_SAMPLE_TYPE note).
- **C. FLOAT32 by default, INT24 through an opt-in extension.** For: G7250-aware clients save
  budget. Against: one more mode to implement and test; can be added in a later profile
  version if G6 shows it is needed.

Reason: compatibility with generic clients first; the budget is protected by the rate limit.

## 12. Stream byte order and block size

**Chosen.** Header fields and samples are little-endian. A binary frame carries the 64-byte
header and `length` samples only, never the full `data[16384]` field.

Alternatives: big-endian (against: [TCI] gives the header as a C structure of `uint32_t`
fields, and the PC platforms TCI runs on are little-endian); always the full 16 448 bytes
(against: wastes SPI budget for small blocks).

Reason: most likely reading of [TCI] §3.4. Both are to be checked against a public client
implementation; they are listed as assumptions in part C Annex C-D.

## 13. Narrow-FM mode name

**Chosen.** The server announces `NFM` in `MODULATIONS_LIST` ([TCI] §4.2 MODULATION example
"NFM") and accepts `FM` in a set request as a synonym for `NFM`, replying with `NFM`.

Alternatives: announce `FM` ([TCI] §4.1 MODULATIONS_LIST example "AM,LSB,USB,FM"); announce
both (against: two names for one mode in the list confuse a client's mode menu).

Reason: [TCI] uses both names; accepting both costs nothing.

## 14. Names shared with part B

**Chosen.** TCI mode-class names, reject and drop reasons and limit names are the part B
symbolic names (`TX_MODE_CLASS` enumeration, reason codes, `LIMIT_<name>`), written in lower
case where part C uses lower-case enumerations. Part B is authoritative; part C adds only the
TCI-specific reasons `STOP`, `HOLDER_LOST` and `BAD_VALUE`. `ARM_MAGIC` is the constant of
part B; part C does not define its own.

Alternative: independent TCI names (against: two names per reason across levels, against
0014).

## 15. `TX_SENSORS` microphone level

**Chosen.** arg2 of `TX_SENSORS` ("microphone signal level, dBm", [TCI] §4.4) carries the RMS
level of the TX audio in use, in dB relative to full scale of the TCI TX audio stream, and
`-140` when there is no TX audio. There is no microphone on the main unit (0017).

Alternatives: always `0` (against: a client cannot see whether its audio arrives); a dBm value
(against: there is no analogue input to calibrate).

## 16. P2 commands while level 2 is active

**Chosen.** While level 2 is active, a P2 host cannot take the RF chain: P2 C&C ports have no
socket on level 2 (0008, Socket budget), discovery answers byte 4 = 0x03 (0003), and the level
changes only through the management channel (0008 C-2). This answers the open point of part A
A2.5.

Alternative: a P2 C&C packet ends level 2, as a takeover (0007 Decision 3). Against: there is
no socket for it, and an automatic level switch by any P2 host on the LAN would end every TCI
client's session.

## 17. Smaller clarifications

1. **Upgrade path.** The server MUST accept the WebSocket upgrade on any request path
   ([RFC6455] §4.2.1: the request names a resource that the server interprets; the profile
   gives no meaning to it). For: no client fails on its path.
   Alternative: only `/` (against: unknown which path clients use).
2. **`VOLUME`, `MUTE` and related on level 2.** If supported, the values are synchronised and
   do not change the level of the TCI RX audio stream, because the main unit has no audio
   output of its own (0017). Alternative: apply them to the stream (against: [TCI] does not
   say ExpertSDR3 does so, and a client's own volume control would then fight the stream).
3. **Reference model.** Part C conformance tests run against the reference model on the
   product side (0019), not one in g7250-testbench.

## 18. Keyed liveness on TCI (review H4)

**Problem.** Part C draft 2 (C8.2) fed the keyed timeout with "any frame" from the keying
client, including the WebSocket Pong that the client's WebSocket stack sends by itself
([RFC6455] §5.5.2). A client whose network thread still answers Pings while its TX logic has
hung would keep the radio keyed until the maximum TX time. That is option 2B of 0007
(Sub-decision 2.2: "still fed by any C&C packet, so the 'network thread alive, TX logic dead'
case remains"), which 0007 rejected in favour of 2C. Generic clients do not know any keep-alive
command, and some TX sources (`TUNE`, `KEYER` key-down, `CW_TERMINAL`, `TRX` in `CW`) produce
no frames at all while keyed.

**Chosen rule.**

1. **Application frames.** An application frame is a WebSocket text frame that carries at
   least one complete TCI command ([TCI] §3.1), or a binary frame that carries a
   TX_AUDIO_STREAM block ([TCI] §3.4). WebSocket control frames (Ping, Pong, Close;
   [RFC6455] §5.5) are never application frames.
2. **Keyed timeout, opted-in keying client.** While keyed, a keying client that has opted in
   (part C C5.2) MUST send an application frame at least every 100 ms (the P2 duty of 0007
   Decision 2). If no application frame from it arrives within the keyed timeout in force
   (default 500 ms, floor 100 ms, §20), the server unkeys and keeps the arm. A new extension
   `G7250_KEEPALIVE;` exists for this purpose; it has no other effect and no reply.
3. **Keyed timeout, generic keying client with TX audio.** A keying client that has not opted
   in and keys with `TRX:0,true,tci;` in a mode other than `CW` answers TX_CHRONO with
   TX_AUDIO_STREAM blocks (§7); those blocks are application frames, so the same keyed timeout
   (500 ms in force by default) applies.
4. **Generic keyed window.** A keying client that has not opted in and keys with a source that
   produces no application frames by itself (`TUNE`, `KEYER` key-down, `CW_TERMINAL` after the
   text has been sent, `TRX` in `CW`) is unkeyed, arm kept, when no application frame from it
   has arrived for **1 s**. Any application frame from that client (for example a repeated
   `TUNE:0,true;`, a `KEYER` change, a `CW_MSG`) restarts the 1 s. The value is built in and
   not writable. While the server itself sends CW text (`CW_MACROS`, `CW_MSG`), the
   transmission ends with the text and no window applies to it; the window starts when the
   text is sent and the radio stays keyed (terminal mode).
5. **Connection watchdog.** Pong frames feed only the 1 s connection watchdog of the arm holder
   (part C C8.2), which drops the arm. This is the analogue of the 1 s base P2 watchdog, which
   0007 (2.1) also lets any C&C packet feed.
6. **Level 1.** AetherSDR's P2 keep-alive (the High Priority packet every 100 ms from its I/O
   thread; [AETHER-SRC] `P2Client.h:238–241`, per `spec/annex-aethersdr.md` G-08c)
   is independent of its TCI clients. The radio's keyed timeout therefore protects only
   against AetherSDR itself stopping, not against a TCI client that stops. AetherSDR MUST
   apply points 1–4 to its TCI keying client and MUST clear the P2 PTT bit (High Priority byte
   4 bit [1] [P2]) when the TCI-side rule unkeys, before it forwards any further TX to P2.

Value of the generic keyed window, 1 s:

- It equals the base watchdog of P2 (0007 2.1) and the TCI connection watchdog, so the longest
  unintended carrier after a generic client stops is the bound 0007 accepted for the
  unkeyed-in-time case of a host crash on level 1.
- A slow hand-sent dash fits: at 5 words per minute a dot lasts 240 ms (1.2 s / WPM, PARIS
  timing) and a dash 720 ms, so a `KEYER` key-down held for one dash, with no frame in between,
  does not trip it.
- A longer value buys little: real tune cycles last seconds (the internal ATU takes up to 10 s
  for initial tuning [G7250-MAN]), so even 2 s would not cover a generic `TUNE` used for an
  external tuner, while it doubles the unintended carrier.

Alternatives:

- **A. Keep "any frame including Pong" (draft 2).** For: generic clients keep `TUNE` as long
  as they like. Against: recreates 0007 option 2B, which 0007 rejected.
- **B. Keyed timeout of 500 ms for every client, any source.** For: one rule, as P2. Against:
  a generic `TUNE` or `TRX` in `CW` would end after 0.5 s, and a slow `KEYER` dash (720 ms)
  would be cut.
- **C. No cap for generic clients, only the 5 min maximum TX time.** Against: up to 5 minutes
  of carrier from a client whose TX logic has hung (0007 2A, "Against").

**Reason.** Only frames that the client's TCI layer itself produces prove that the client
still wants to transmit, which is the reason 0007 chose 2C. Opted-in clients get the same
timing as P2; generic clients keep working for audio-based TX, and frame-less TX is bounded
by the same 1 s as host loss on P2.

## 19. TX frequency and RF-path changes on TCI while keyed (review H1, H2)

**Problem.** §8 named only `VFO`, `SPLIT_ENABLE` and the XIT offset, checked only the
transmit range, and let front-end settings follow while keyed. Part A now requires an unkey
before any retune that needs another RF-path state and forbids relay changes under RF from
any source (A3.9; 0022 §1, §2).

**Chosen rule.** This section replaces the frequency and front-end parts of §8; the refusal
of `MODULATION` while keyed stays.

1. **Commands that move the effective TX frequency.** The effective TX frequency is the
   frequency of channel A of receiver 0, or of channel B when split is on, plus the XIT offset
   when XIT is on (part C C4). It is moved by: `VFO` for the TX channel; `IF` for the TX
   channel; `DDS` of receiver 0, when the server keeps `IF` and so moves the channel frequency
   (`VFO` = `DDS` + `IF`); `SPLIT_ENABLE` (moves TX between channels A and B); `VFO` or `IF`
   of channel B while split is on; `XIT_ENABLE`; `XIT_OFFSET` while XIT is on; and a change
   of `RX_CLICKED_ON_SPOT` or another server action that sets one of these (level 1).
   `RIT_ENABLE` and `RIT_OFFSET` do not move it ([TCI] §4.2: RIT is a receive offset).
2. **A3.9 applies.** Before applying such a change while keyed, the server evaluates the new
   effective TX frequency. If it lies outside the transmit ranges in force, or needs another
   TX filter, band or relay state, the server MUST unkey first (`UNKEY`, arm kept; unkey
   reason 6 "retune needs RF-path change", or reason 4 with limit id `LIMIT_TX_FREQ` for the
   range), then apply the change, then broadcast the unkey (§24). Otherwise the change is
   followed while keyed. Until HIS-07 gives the filter plan, every transmit range of the
   capability record `tx_band` list (part B B4.8) counts as its own RF-path state; on level 2
   the same list is used.
3. **Frequency changes that do not move the TX frequency** (channel A while split is on,
   channel B while split is off, `RIT_OFFSET`) are followed; if they need another receive
   filter or relay state, the relay change is deferred until the unkey, as part A defers
   resent P2 state fields (A3.9), because the TCI value is synchronised state and the client
   expects it to be taken.
4. **RF-path relays.** While keyed, a change of `G7250_ANT`, `G7250_ATU` (in or out of line),
   `G7250_PREAMP` and `G7250_ATT` MUST be refused from any client: the server replies with the
   value in force and, to an opted-in requester, `G7250_WRITE_STATUS` with `KEYED` (§22).

Alternatives:

- **A. Refuse every frequency change while keyed.** For: no RF-path decision while keyed.
  Against: breaks normal tuning during CW and SSB (0022 §1, alternative B), and a refused
  `VFO` on a synchronised parameter leaves other clients' displays inconsistent.
- **B. Follow front-end changes while keyed (§8 as drafted).** Against: preamplifier and
  attenuator are relays (A3.9); switching them under RF is what 0022 §2 forbids.

**Reason.** The TCI side gets exactly the safety-core rule of part A, so both levels behave
the same (0014; 0011 point 3).

## 20. Limit tiers and the keyed timeout on TCI (review H7)

**Problem.** Draft 2 (C5.10) checked `G7250_LIMIT` against the built-in values, reverted to
them, used names (`MAX_TX_TIME`) that part B does not have, and treated `KEYED_TIMEOUT` as a
limit.

**Chosen rule.**

1. The TCI session value is the third tier of part A A3.4 rule 1. The **limit in force** is
   the strictest of built-in, persistent (management C-3, 0008) and TCI session value.
2. `G7250_LIMIT:<id>,<value>;` takes one of the host-tunable limit ids of Table B8-3 verbatim:
   `LIMIT_TX_TIME`, `LIMIT_FWD_POWER`, `LIMIT_SWR`, `LIMIT_PA_TEMP`, in the units of their
   part B registers (ms, mW, 1000 × SWR, m°C; part B B8.6). Another id is rejected with
   `BAD_VALUE`.
3. A write is accepted only if it is equal to or stricter than the persistent value; a looser
   one is rejected with `LOOSER_LIMIT`, not clamped. The reply always carries the limit in
   force.
4. Writing 0 returns the TCI session value to the persistent value. Because the value is
   shared by all clients, a write of 0, or of a value looser than the current session value,
   is accepted only from the arm holder, and from any client while no client holds the arm;
   otherwise it is rejected with `LOOSER_LIMIT` (as `G7250_TX_POLICY`, §1).
5. The TCI session ends, and session values return to the persistent values, when the last
   client disconnects, on a level change and on reset. A C-3 change is a `MAINTENANCE` drop
   while armed and then applies at once; a session value looser than the new persistent
   value is replaced by it (0022 §6).
6. The keyed timeout is not a limit. It has its own command
   `G7250_KEYED_TIMEOUT:<ms>;` (set, reply) and `G7250_KEYED_TIMEOUT;` (read), synchronised to
   opted-in clients. Values 100–500 ms; others rejected with `BAD_VALUE`. Default 500 ms; the
   loosening rule of point 4 applies (a higher value only from the arm holder, or while no
   client holds the arm); back to 500 ms at TCI session end, level change and reset. (L1)
   AetherSDR applies it to its TCI-side keyed timeout (§18) and MAY write it to the P2
   `KEYED_TIMEOUT` register.
7. (L1) AetherSDR writes the strictest TCI session value to the P2 `LIMIT_<name>` register of
   the same name; P2 checks it against the persistent value, and AetherSDR passes the P2
   answer (the limit in force, or `LOOSER_LIMIT`) on to TCI.

Alternatives:

- **A. Check against the built-in value (draft 2).** Against: a client could set a value
  between built-in and persistent and believe it in force (0022 §6, alternative A).
- **B. Any client may write 0 or loosen.** For: as P2, where the single owner may. Against:
  on TCI several clients share one value; one client could undo another's tightening.

**Reason.** One tier model and one set of names across both levels (0014; 0022 §6, §19).

## 21. REDUCE and power measurement on TCI (review H8, M13)

**Chosen rule.** Part C has no REDUCE or measurement of its own; it follows part A. `REDUCE`
is as A3.3: for forward power and supply voltage drive is lowered until the value is back
inside the limit; for SWR above S1 forward power is capped at `P_swr` until the unkey; for PA
temperature at or above T2 it is capped at `P_temp`, lifted below T2 minus the hysteresis
(A3.4a; 0022 §7). The `DRIVE` and `TUNE_DRIVE` values that clients see never change (0007
rule 4). Forward power is measured as in A3.4c (0022 §17): the 100 W limits apply to PEP, the 25 W AM limit to the 100 ms mean. *(Superseded in this
point by 0022 §17, §43 and §52: the 25 W AM limit applies to the carrier power, measured by the
carrier estimate of A3.4c, or by the conservative mean limits of Table A3-3 when the detector
gives no envelope samples, with PEP also held to 100 W; part C C5.6, C5.10 and C8.1 follow
0022. Noted at rc3, 0021 §41 item 11.)* `TX_SENSORS` ([TCI] §4.4) reports arg3, "RMS" power, as that
100 ms mean and arg4, peak power, as the PEP over the same window; arg5 SWR is the value the
safety core uses (`TLM_SWR`). If the detector gives no PEP (HIS-11), arg4 carries the mean.

Alternatives:

- **A. Show REDUCE by lowering the TCI `DRIVE` value.** For: generic clients see it. Against:
  0007 rule 4 keeps the host value; the client's value would fight the radio.
- **B. Own TCI measurement windows.** Against: the safety core measures once for both levels
  (0011 point 3).

**Reason.** One safety core; TCI only reports it.

## 22. Symbol names on TCI (review M4)

**Chosen rule.** Every code name on TCI is the Table B8-3 name, verbatim and in upper case:
arm reject reasons (`NOT_RUNNING`, `WATCHDOG_DISABLED`, `IN_FAULT`, `INHIBITED`,
`PTT_ACTIVE`, `LEVEL_NOT_ACTIVE`, `MAINTENANCE`, `NO_MODE_CLASS`, `BAD_TOKEN`,
`TX_NOT_IMPLEMENTED`), drop reasons (`HOST_DISARM`, `RUN_CLEARED`, `WATCHDOG`, `TAKEOVER`,
`RESET`, `FAULT`, `LINK_DOWN`, `SESSION_CHANGED`, `LEVEL_CHANGE`, `MAINTENANCE`,
`REDISCOVERY`, `LIMIT_<name>`), limit ids (`LIMIT_TX_FREQ` … `LIMIT_RF_NOT_KEYED`), fault
codes (`SWR_REPEATED`, `PA_OVERTEMP`, `SENSOR_IMPLAUSIBLE`, `RF_NOT_KEYED`,
`TX_PATH_NOT_BLOCKED`, `WDT_RESET_AT_START`, `SELFTEST_FAILED`, `INTERNAL_ERROR`) and write
reject reasons (`READ_ONLY`, `BAD_VALUE`, `LOOSER_LIMIT`, `BUSY`, `NOT_CLEARABLE`, `KEYED`,
`NOT_ARMED`). This replaces the lower-case reading of §14 for codes; lower case stays for part
C's own enumerations (states, TX sources, mode classes, stream reasons). The draft-2 renames
(`NOT_STARTED`, `FAULT` as a reject reason, `INHIBIT`, `TX_ACTIVE`, `NOT_ACTIVE_LEVEL`,
`NO_TX`, `BAD_VALUE` for a wrong token, `MAX_TX_TIME`) are removed. The only TCI-specific code
names are the drop reasons `STOP` and `HOLDER_LOST`; `BAD_VALUE` is in Table B8-3 already
(write reject reason 4) and is no longer a TCI addition. Write rejections of extension set
requests, and of standard commands refused by a profile rule, are reported to the opted-in
requester by a new per-client notification `G7250_WRITE_STATUS:<command>,<reason>;`, the
counterpart of the P2 `WRITE_STATUS` register; `UNKNOWN_ADDRESS` and `NOT_OWNER` are not used
on TCI (an unknown command is ignored, [TCI] §4.7 note 5; TCI clients have no owner).
`G7250_SAFETY`, `G7250_TX_STATE` and `G7250_LIMIT_STATUS` carry the part B fields and bit
layouts (`SAFETY_STATE`, `FAULT_CODE`, `FAULT_CLASS`, `FAULT_FLAGS`, `TRIP_COUNT`;
`TX_STATE` unkey reasons and limit id; `LIMIT_STATUS`).

Alternative: keep lower-case renames on TCI. Against: two names per code across the levels
(0014), and 0022 §19 makes Table B8-3 the single list.

## 23. Antenna, ATU selection and front end where no register exists (review M5)

**Problem.** C5.1.4 required every extension on both levels, but on level 1 part B has no
writable antenna, ATU-selection, preamplifier or attenuator control: group 5 has only the
read-only `ANT_STATE`, group 6 is reserved, and the P2 Alex words and step attenuator are
"TBD; ignored" until HIS-06 and HIS-07 (part B B7, B8.3).

**Chosen rule.** An extension MAY be absent on a level until the hardware is known (HIS-06,
HIS-07, HIS-08) and, on level 1, a part B register or field carries it. Absence is announced
by the `G7250_FEATURES` tokens; an absent extension command is ignored without a reply, as an
unknown command ([TCI] §4.7 note 5). Meanwhile:

- `G7250_ANT`: settable only with token `ant`; with token `ant_state` only (level 1 with group
  5, `ANT_STATE`), it is a notification, and a set is answered with the value in force and
  `G7250_WRITE_STATUS` `READ_ONLY`; with neither, absent.
- `G7250_ATU` (in or out of line): settable only with token `atu_select`; the state stays
  visible through `G7250_ATU_STATE` (token `atu`, `ATU_STATE`); a set without `atu_select` is
  answered as for `G7250_ANT`.
- `G7250_PREAMP`, `G7250_ATT`: absent until HIS-07 and (L1) a part B register exist.
- The same applies on level 2 until the HIS answers.

Alternative: keep the MUST and let level 1 accept and ignore the writes. Against: a client
would believe it switched an antenna.

**Reason.** The meaning stays the same on both levels where the function exists; where it does
not, a client can see that.

## 24. Arm holder, several arm sources and server-side unkeys (review M6)

**Chosen rule.**

1. **Second arm.** A valid `G7250_TX_ARM` from client B while client A holds the arm is a
   no-op, as a correct arm write while armed is on P2 (part B B10.2 item 5): no new
   generation, A stays the holder, and B receives `G7250_TX_ARM_STATE` with `holder` false.
   B can become the holder only after the arm has been dropped.
2. **Level 1, several sources.** AetherSDR's own user interface and at most one TCI client can
   hold the arm; both map onto the one P2 arm of AetherSDR. A TCI-side end of holding (the
   holder's `HOLDER_LOST`, `WATCHDOG`, or `G7250_EXT:false;`) removes that holder; AetherSDR
   writes `TX_ARM` = 0 over P2 only if no other holder remains. An explicit disarm
   (`G7250_TX_ARM:0,00000000;` from any client, or from AetherSDR's interface) and every drop
   that comes from the radio end the arm for all.
3. **Broadcast of a server-side unkey.** When the server unkeys without a client request
   (keyed timeout, generic keyed window, TX audio underrun, a limit, the maximum TX time, a
   retune that needs an RF-path change, a drop, a level change), it MUST send `TRX:0,false;`
   if `TRX` was true and `TUNE:0,false;` if `TUNE` was true, to all clients, as the
   synchronisation of [TCI] §3.1 requires for any change of state; queued CW text is
   discarded. A generic client so learns that it no longer transmits.
4. **Policy without holder.** `G7250_TX_POLICY` returns to `any` whenever no holder remains:
   at every drop or disarm, besides the points of §1.

Alternatives:

- **A. Transfer the holder role to B.** For: the latest G7250-aware program holds. Against: B
  could then set the policy back to `any` and lift A's restriction (§1).
- **B. Reject B with a new reason.** Against: a new code outside Table B8-3; the `holder`
  field already tells B.

**Reason.** One holder per arm on TCI, as one owner on P2; generic clients see every unkey.

## 25. Level switch seen from TCI (review M2)

**Chosen rule.** On `SWITCH_LEVEL` (A2.5a; 0022 §9), a level-2 server sends, in this order,
after the validation of A2.5a step 1 and before the management reply of A2.5a step 3 (as part
C C2.7; corrected at rc3, 0021 §41 item 11; 0022 §61): (1) if keyed, the unkey broadcast of §24; (2) if armed,
`G7250_TX_ARM_STATE` (disarmed, `LEVEL_CHANGE`) and the new `G7250_TX_ARM_TOKEN` to opted-in
clients and `TX_ENABLE:0,false;` to all; (3) no further stream blocks, and
`G7250_STREAM_STATE` `stopped`, reason `level_change`, for each running stream; (4)
`G7250_PROFILE` with `active` false to opted-in clients; (5) a WebSocket close with status
1001 on every connection ([RFC6455] §7.4.1); then the listener closes (A2.5a step 6). On
level 1, AetherSDR receives the P2 drop `LEVEL_CHANGE` before port 7250 closes (A2.5a step
2), sends (1)–(4) to its TCI clients, and keeps its TCI connections open.

Alternative: close the connections at once. Against: clients would not learn why.

## 26. P2 ownership seen from TCI on level 1 (0022 §3)

**Chosen rule.** AetherSDR is the P2 owner from its run bit or a takeover (A2.3, A2.4). When
another P2 host takes over, AetherSDR receives the last `TX_ARM_STATE` (`TAKEOVER`) and
nothing more (A2.4 step 1); it then sends its TCI clients the sequence of §25 (1)–(4) with
reason `TAKEOVER` and stream reason `takeover`, and keeps the connections. AetherSDR MUST NOT
take the radio back by itself (no ping-pong, 0022 §3 point 6); a new session is started by the
user. At a new session AetherSDR writes `TX_MODE_CLASS`, the TCI session limits and the keyed
timeout to P2 again, because the takeover returned them to the persistent values and defaults
(A2.4 step 1).

Alternative: AetherSDR retakes automatically. Against: ping-pong, during which neither host
can transmit (0022 §3).

## 27. A total keyed-liveness table (rc3 review H1)

**Problem.** Part C rc2 C8.2 chose the keyed-liveness rule by listing sources per row: the
keyed timeout for opted-in clients and for `TRX:0,true,tci;` outside `CW`, the generic keyed
window for generic `TUNE`, `KEYER`, `CW_TERMINAL` and `TRX` in `CW`. A generic client keyed
with a microphone source (`TRX:0,true;`, `mic1`, `mic2`, `micpc`, `ecoder2`; [TCI] §4.2 TRX)
in a mode other than `CW` matched no row, so no keyed-liveness rule bound it; only the 5 min
maximum TX time did.

**Chosen rule.** Part C C8.2 has one table, Table C8-1, keyed by TX source × opted-in, with a
rule in every cell: opted-in keying clients are always bound by the keyed timeout (CW text
excepted, §29); a generic keying client is bound by the keyed timeout when it keys with TCI
audio outside `CW` (its audio blocks are application frames, §18 point 3) and by the 1 s
generic keyed window for every other source, a microphone `TRX` in any mode included. Other
timers (TX audio underrun, key-down cap, CW text liveness, `LIMIT_ATU_TIME`) are named in the
same row where they act. A microphone `TRX` exists only where a microphone path exists
(HIS-17).

Alternatives:

- **A. Keyed timeout of 500 ms for a generic microphone `TRX`.** For: the same value as voice
  over TCI audio. Against: a generic microphone client sends nothing by itself while keyed;
  500 ms would cut every voice over at once, 1 s at least equals the P2 base watchdog (§18).
- **B. No liveness rule for a microphone `TRX`; rely on the maximum TX time.** For: generic
  voice clients that hold PTT keep working. Against: up to 5 min of carrier from a client whose
  TX logic hung (0007 Decision 2, option 2A, "Against"); §18 rejected this as alternative C.

**Reason.** Every TX source needs a bound that does not depend on the 5 min maximum TX time;
a table with no empty cell makes that checkable. Compatibility cost (part C Annex C-D, D7): a
generic voice client holding PTT with a microphone `TRX` is cut after 1 s unless it restates;
on the G7250 this arises only with a microphone path (HIS-17).

## 28. What feeds the generic keyed window (rc3 review M3)

**Problem.** §18 point 4 let any application frame restart the generic keyed window. A generic
client whose polling loop (for example `VFO:0,0;` reads) runs on while its TX logic has hung
would then keep `TUNE` or `TRX` in `CW` keyed until the maximum TX time, the case 0007 option
2B leaves open. Part C rc2 also said the backstops cover "each TX source" (0022 §25 Reason),
which did not hold for that case.

**Chosen rule.** Only a restatement of the TX request restarts the generic keyed window:
`TUNE:0,true;` while keyed by `TUNE`; `TRX:0,true` with the same source while keyed by `TRX`;
any `KEYER` while keyed by `KEYER`; a `CW_MACROS` or `CW_MSG` in terminal mode. A restatement
while keyed is not a new 0→1 request. The keyed timeout of opted-in clients stays fed by any
application frame, as the P2 keyed timeout is fed by any High Priority packet (0007 Decision
2). Part C states the known limit: an opted-in client whose I/O thread keeps sending frames
while its TX logic hangs is caught, for `TUNE`, `TRX` in `CW`, a microphone `TRX` and
`CW_TERMINAL`, only by the maximum TX time, as a P2 host with cached PTT and I&Q (0022 §25
point 5); part C narrows the 0022 §25 statement accordingly (part C C8.2.3a).

Alternatives:

- **A. Any application frame feeds the window (rc2).** For: a generic client that polls keeps
  its `TUNE`. Against: the hung-TX-logic case stays open; the reason for 0007 option 2C.
- **B. Restatement only, also for opted-in clients.** For: closes the case for every client.
  Against: opted-in clients would need a different duty from P2, where any High Priority
  packet feeds the keyed timeout, and `G7250_KEEPALIVE` would lose its purpose (§18 point 2).

**Reason.** A restatement is produced by the client's TX logic itself, so it proves that the
client still wants to transmit; a read poll does not.

## 29. Overlaps between the liveness rules (rc3 review M2)

**Problem.** Four cases had two candidate rules or none: (1) an opted-in client's CW text
(keyed timeout of 500 ms, or the 30 s CW text liveness?); (2) `G7250_ATU_TUNE` from a client
that has not opted in (no keyed timeout, no window); (3) `G7250_EXT:false;` (or `true`) from
the keying client while keyed; (4) the keying client is also the holder and its connection
drops (`unkey` 5 "arm dropped" or 8 "keying client lost"?).

**Chosen rule.**

1. **CW text.** While the server sends CW text, the 30 s CW text liveness applies to every
   keying client, opted in or not; the keyed timeout and the generic keyed window do not run.
   The keyed timeout applies to client keying commands (`TRX`, `TUNE`, `KEYER`,
   `CW_TERMINAL` after the text, ATU tune).
2. **`G7250_ATU_TUNE` from a client that has not opted in** is ignored without a reply and not
   latched; it is the one exception to "extension set requests from a client that has not
   opted in are accepted" (part C C5.2).
3. **Opt-in change while keyed.** The keyed-liveness rule is fixed at the key and changes only
   from the next key; the messages the client receives change at once. A `G7250_EXT:false;`
   from the holder is drop event 13, which unkeys.
4. **Holder and keying client in one connection.** The unkey is reported as `unkey` 8 and the
   drop as `HOLDER_LOST`; `unkey` 5 is not used for it.

Alternatives:

- **A for 1: keyed timeout also during an opted-in client's text.** For: one rule for opted-in
  clients. Against: a client would have to send frames every 100 ms during text the server
  generates, though its TX logic has no part in it; 0022 §25 point 4 chose 30 s for that
  reason.
- **A for 2: generic keyed window for a non-opted-in ATU tune.** For: no exception to C5.2.
  Against: a client that does not see `G7250_ATU_STATE` cannot know when to restate, and an
  ATU tune can last 10 s [G7250-MAN]; such a client would always end as `failed`.
- **A for 3: an opt-in change while keyed unkeys.** For: no mixed state. Against: an unkey
  that no stop request asked for; keeping the rule from the key is never looser, because the
  keyed timeout (≤ 500 ms) is stricter than the 1 s window for every row where they differ.
- **A for 4: `unkey` 5.** For: drops unkey "first" (C5.5.5). Against: `drop` already carries
  `HOLDER_LOST`; 8 adds that the transmission ended because its client went, the same report
  as without the arm.

**Reason.** Each case gets exactly one rule, and in no case a looser one than before.

## 30. Who triggers an AetherSDR arm (rc3 review H2)

**Problem.** `annex-aethersdr.md` Q-O3 asked whether AetherSDR may arm automatically when the
user first keys. A level-1 auto-arm on a TCI, CAT or rigctl TX request would let software that
does not know the G7250 enable transmit, which 0015 forbids.

**Chosen rule.** An AetherSDR arm, and so a P2 arm handshake, MUST be triggered only by an
explicit arm action in AetherSDR's own user interface or by a valid `G7250_TX_ARM` from a TCI
client; never by a TX request from TCI, CAT, rigctl or AetherSDR's own user interface. While
nothing is armed such a request is refused and causes no P2 `TX_ARM` write (part C C5.5.7).

Alternatives:

- **A. Arm on the first key from AetherSDR's own user interface only.** For: one click less
  for the local operator. Against: the arm would follow from a PTT, so a stuck PTT or a key
  mapped to PTT arms; the explicit action is the safer default named in Q-O3.
- **B. Arm on any first key, TCI included.** Against: any TCI client on the LAN could enable
  100 W, which 0015 and part C C5.5.2 exclude.

**Reason.** Only software or an operator that knows the G7250 may enable transmit (0015).

## 31. Source of the mode class on level 1 (rc3 review H3)

**Problem.** Part C C5.6 said AetherSDR writes "the derived class" of TCI `MODULATION`. When
AetherSDR's user interface changes the mode of its TX slice, or the TX slice is not the slice
TCI receiver 0 shows, the P2 class could differ from the signal on the air, and the 25 W AM
limit would not act.

**Chosen rule.** On level 1 the class follows the mode of the signal AetherSDR actually
transmits, from any source (user interface or TCI), and is rewritten on every TX-mode change;
while keyed a change unkeys first (A3.9c). TCI receiver 0 is AetherSDR's TX slice
(`TRX_COUNT:1`; `annex-aethersdr.md` G-13), so `MODULATION` of receiver 0 and the TX mode are
one value.

Alternatives:

- **A. Class from TCI `MODULATION` only.** For: one source. Against: a mode change in the user
  interface leaves P2 with a wrong class; AM could then run under the 100 W class.
- **B. Map TCI receiver 0 to the slice the user selects, the TX slice elsewhere.** For:
  flexible. Against: `MODULATION` and the TX class would then describe different slices, and
  a generic client would set a mode that is not transmitted.

**Reason.** The per-mode limit must describe the signal on the air (0007 Sub-decision 4 rule
3).

## 32. Aborting an ATU tune on TCI (rc3 review M4)

**Problem.** Part C C5.7 said a further `TRX`, `TUNE` or CW request "neither keys nor ends the
tune", while C7.4 says every stop request takes effect at once. Part B has an abort
(`ATU_TUNE` = 0, Table B8-2), TCI had none.

**Chosen rule.** TX requests (`TRX` true, `TUNE` true, `KEYER` press, CW text) neither key nor
end a cycle (A3.9b item 4). Every stop request of C7.4 from any client, and a new
`G7250_ATU_TUNE:0,abort;`, aborts the cycle at once: unkey, `G7250_ATU_STATE` `failed`, ATU
back to the stored state or bypass after RF gone (A3.9b items 6–7). On level 1 an abort writes
`ATU_TUNE` = 0.

Alternatives:

- **A. Only `G7250_ATU_TUNE:0,abort;` aborts.** For: a generic client's stray `TRX:0,false;`
  cannot end a tune. Against: a generic client could not stop a tune carrier, against "making
  TX stop is always allowed" (C7.4; 0011 point 3).
- **B. No abort; the cycle ends by itself within `LIMIT_ATU_TIME`.** Against: up to 10 s of
  carrier [G7250-MAN] that no client can stop.

**Reason.** Stopping RF is always allowed; the explicit abort gives opted-in clients the P2
command.

## 33. `KEYER` semantics (rc3 review M5)

**Problem.** [TCI] §4.4 KEYER says it "Works in CW mode only" and that the device "plays each
state for the given duration"; part C did not say what happens outside `CW`, how long arg3 may
be, or from when the 1 s key-down cap counts.

**Chosen rule.** Outside `CW` every `KEYER` command is ignored and not latched (A3.1a). arg3
above 1000 ms is clamped to 1000 ms. The key-down cap counts the key-down as played, from the
start of its playback, not from the arrival of the command; a key-down played for more than 1 s
without its release being played unkeys (`unkey` 9).

Alternatives:

- **A. Cap from the arrival of the press.** For: simple. Against: the device plays with a delay
  of the pause before the press (arg3), so a legal key-down could be cut early, and a delayed
  one held longer than 1 s on the air.
- **B. Refuse arg3 above 1000 ms.** For: no silent change. Against: `KEYER` has no reply
  ([TCI] §4.4), so the client cannot learn of a refusal, and its key state would be lost.

**Reason.** The cap must bound what is on the air; a played key-down longer than 1 s is cut in
any case, so the clamp changes nothing that would reach RF.

## 34. `DIGL`/`DIGU` offsets and the TX frequency (rc3 review M6)

**Problem.** [TCI] §4.2 DIGL_OFFSET and DIGU_OFFSET give the offset in Hz (0–4 kHz) but not its
effect; part C did not say whether it moves the effective TX frequency, `TX_FREQUENCY` and the
TX frequency limit.

**Chosen rule.** In `DIGL`/`DIGU` the suppressed carrier is at the channel frequency, as in
`LSB`/`USB`; the offset shifts only the audio passband of demodulator and modulator. It moves
neither the effective TX frequency nor `TX_FREQUENCY`, is followed while keyed, and the TX
frequency limit acts on the channel frequency as in SSB. Marked **[unverified]** against
ExpertSDR3 (part C Annex C-D, D9).

Alternatives:

- **A. Carrier = channel frequency ± offset.** For: the TX frequency would match the centre of a
  data signal. Against: a TCI client sets `VFO` for the carrier in SSB data work; moving the
  carrier by the offset would put the signal 1.5 kHz away from where the client believes it,
  and the offset would become an RF-path change while keyed.
- **B. Leave it open until checked.** Against: rc3 needs a rule for C7.6.1; an open point here
  is not a HIS question.

**Reason.** The same carrier rule as SSB keeps the band-edge check and the C7.6.1 list
unchanged; the assumption is listed for checking.

## 35. Commanded reset and configuration changes on level 2 (rc3 review M7)

**Problem.** Part C covered the firmware update (C2.8) but not `RESTART`, `FACTORY_RESET`,
the status 59 case, an allow-list change (C-7) that removes an open connection, or a TCI port
change with connections open (A1.6, A1.6a, A1.9).

**Chosen rule.** Part C C2.10: (1) `RESTART` and `FACTORY_RESET` unkey and disarm before the
management reply (drop `RESET` for `RESTART`, `MAINTENANCE` for `FACTORY_RESET`, new C5.5.5
row 15), then, after RF gone and the reply, close every connection with 1001 and reset;
(2) with status 59 the connections stay open, TX stays disarmed and the fault is reported;
(3) an allow-list change closes the connections it no longer allows with 1008 (drop
`HOLDER_LOST` for the holder, `unkey` 8 for the keying client); (4) a TCI port change moves
the listeners after the reply and keeps open connections until they close.

Alternatives:

- **A for 4: close all connections on a port change.** For: one port in use at a time.
  Against: a transmission would end without a safety reason, and clients would reconnect to
  the old port and fail.
- **A for 3: close the removed connections with 1001.** For: the status used elsewhere.
  Against: 1008 "policy violation" (RFC 6455 §7.4.1) tells the client that it is no longer
  allowed, so it does not retry at once.

**Reason.** Every path that ends a session on level 2 now unkeys and disarms first and tells
the clients why, as A1.9 does for the management side.

## 36. TCI CW onto P2 on level 1 (rc3 review M8)

**Problem.** Part C did not say how AetherSDR carries TCI `KEYER` and CW text to the radio. The
CWX paddle bits (B10.5a) drive the radio's keyer at its own speed and weight, so they cannot
play client-timed straight-key elements, and a paddle bit held for a string longer than 1 s is
cut; DUC I&Q with PTT has the underrun check instead. Which caps act on level 1 was open.

**Chosen rule.** AetherSDR sends the CW of TCI `KEYER` and of TCI CW text as DUC I&Q with
PTT, shaped in its own TX chain; CWX is not used for TCI CW. The caps on level 1 are then the
TCI-side rules applied by AetherSDR (Table C8-1, key-down cap, CW text liveness) and the P2
rules applied by the radio (watchdog, keyed timeout, DUC underrun with I&Q running during
key-up, maximum TX time); the CWX cap does not act (part C C8.2.5).

Alternatives:

- **A. CWX paddle bits.** For: no TX DSP needed for CW; the radio shapes the elements.
  Against: no straight-key timing ([TCI] §4.4 KEYER), and long strings are cut at 1 s unless
  the bits are released per element (B10.5a host note), which turns text sending into paddle
  emulation.
- **B. CWX for `KEYER`, DUC I&Q for text.** Against: two TX paths and two sets of caps for one
  mode; a change between them inside one over would need an unkey.

**Reason.** One TX path whose timing AetherSDR controls, with a radio-side bound (the underrun
check) that does not cut legitimate long elements.

## 37. AetherSDR keying paths besides TCI (rc3 review M9)

**Problem.** AetherSDR's P2 keep-alive feeds the radio's keyed timeout whatever its remote
clients do (C8.2.4). The rc3 review reports remote keying paths besides TCI (CAT, rigctl and
AetherSDR's own TCI extensions `aethersdr_ext`); part C binds only TCI clients.

**Chosen rule.** The annex states that each such keying interface SHOULD apply a rule
equivalent to part C C8.2 (unkey and clear P2 PTT when the remote client stops restating for
1 s, or sending for the keyed timeout where the client can be told of one), and lists as known
limit that, where it does not, a hung remote client is bounded on the radio only by the maximum
TX time. None of these paths may arm (§30).

Alternatives:

- **A. MUST for every keying interface.** For: closes the case. Against: those interfaces are
  outside the G7250 profile and not surveyed in `annex-aethersdr.md` §2; a MUST there would
  bind protocols this project does not define.
- **B. Say nothing.** Against: the gap would be invisible to an implementer.

**Reason.** The profile states what it cannot enforce, and the arm rule (§30) still prevents a
non-G7250 client from enabling transmit.

## 38. Monopoly and tick against safety messages (rc3 review L13)

**Problem.** [TCI] §4.7 note 6 drops a set request within 200 ms of another client's change,
and note 7 sends state on a 30 ms tick and merges fast changes. Applied literally, a stricter
`G7250_LIMIT` could be dropped, and an unkey followed by a new key within 30 ms could be merged
away, so a generic client would never see the unkey.

**Chosen rule.** Stop requests and tightening extension writes (stricter `G7250_LIMIT`, lower
`G7250_KEYED_TIMEOUT`, `G7250_TX_POLICY:holder`) are never dropped by the monopoly; loosening
extension writes are subject to it. The unkey broadcast, `TX_ENABLE:0,false;`,
`G7250_TX_STATE`, `G7250_TX_ARM_STATE` and `G7250_SAFETY` are sent at once and never merged
(part C C4.3).

Alternatives:

- **A. Apply notes 6 and 7 to everything.** For: [TCI] as written. Against: a tightening could
  be lost and an unkey hidden, against 0011 point 3.
- **B. Exempt all extension commands.** For: simple. Against: two clients loosening a limit in
  turn would race without the protection the monopoly gives standard parameters.

**Reason.** Tightening and stopping are always allowed at once (0011 point 3); every state
change that matters for safety must be seen.

## 39. TX audio block period against the keyed timeout (rc3 review L15)

**Problem.** `AUDIO_STREAM_SAMPLES` may be up to 2048 ([TCI] §4.3); at 8 kHz a block lasts
256 ms. With a keyed timeout of 100–500 ms, fewer than two blocks could fall in one timeout, so
normal jitter would unkey.

**Chosen rule.** The server sends TX_CHRONO with `length` = the keying client's
`AUDIO_STREAM_SAMPLES`. A `TRX:0,true,tci;` is refused when that block period exceeds half the
keyed timeout in force (part C C6.3.3); a lowered keyed timeout applies at once and is checked
at the next key.

Alternatives:

- **A. Request shorter TX_CHRONO blocks than `AUDIO_STREAM_SAMPLES`.** For: no refusal.
  Against: [TCI] applies the sample amount "to every sample rate"; whether clients honour a
  shorter TX_CHRONO `length` is not known.
- **B. No check.** Against: the unkey would come from the configuration, not from a client
  that stopped.

**Reason.** The refusal comes at the key, where the client can act on it, not as a random unkey
during the transmission.

## 40. WebSocket messages and fragmentation (rc3 review L9)

**Problem.** Part C said "frame" for what RFC 6455 calls a message, and "a command MUST NOT
be split over frames", which forbids fragmentation that RFC 6455 §5.4 allows.

**Chosen rule.** Commands travel in text messages and are not split over messages; a message
MAY be fragmented and counts, for every rule of part C, when its last fragment arrives. In part
C "frame" in "application frame", "text frame" and "binary frame" means a complete data
message (part C C2.2).

Alternative: forbid fragmentation. For: simpler parser. Against: a conforming WebSocket stack
may fragment; RFC 6455 requires an endpoint to accept it.

**Reason.** Follow RFC 6455; a timer fed by the first fragment could be kept alive by a stalled
message.

## 41. Smaller rc3 choices (rc3 review L2–L8, L10–L12, L14)

Each item: chosen rule; alternative; reason.

1. **Reject reason per client (L2).** `reject` in `G7250_TX_ARM_STATE` is the reason of the
   connection's own last rejected arm request. Alternative: one shared field. Against: a
   non-holder's `BAD_TOKEN` would overwrite what the holder sees. Reason: each client sees its
   own outcome.
2. **Drop message order (L3).** Unkey broadcast, `G7250_TX_ARM_STATE`, `G7250_TX_ARM_TOKEN`,
   `TX_ENABLE:0,false;`, the same in C2.7, C5.5.5, C7.2.1 and T-C2-04. Alternative: token
   first. Against: C2.7, C7.2.1 and T-C2-04 already send the state first. Reason: one order.
3. **`IF` into 30–50 MHz (L4).** An `IF` set that would move the channel there is not followed,
   as a `VFO` or `DDS` set. Alternative: follow `IF` within `IF_LIMITS`. Against: `IF` would be
   a way around C3.3. Reason: the receive range binds the channel frequency, however set.
4. **`STOP` broadcast (L5).** When the device stops without a client `STOP` (link below
   100 Mbit/s, `UPDATE_BEGIN`, on level 1 the end of the P2 session), the server sends
   `STOP;` to all clients; C2.8 item 2 no longer sends a `TX_ENABLE` that cannot be `true`
   (L11). Alternative: only `G7250_STREAM_STATE`. Against: generic clients would believe the
   device still runs. Reason: `START`/`STOP` is synchronised state ([TCI] §3.1, §4.2).
5. **Arm reject precedence (L7).** `BAD_TOKEN` first, then C5.5.6 items 1–7 in their order.
   Alternative: report all failing conditions. Against: one field, one Table B8-3 code. Reason:
   deterministic tests.
6. **Extensions (L6).** `G7250_FEATURES` is resent whenever the token set changes;
   `G7250_REFUSED` is defined in part C C5.13; `G7250_ANT` reports `0` when the antenna is not
   known (`ANT_STATE` 0); any client, opted in or not, may set `G7250_TX_POLICY:holder`.
   Alternative for the policy: opted-in clients only. Against: C5.2 accepts extension sets
   from every client, and `holder` only tightens. Reason: tightening is always allowed
   (0011 point 3).
7. **Timer tolerances (L7).** Every TCI timer acts not before its time and by 10 ms after it,
   as P2 (part B B10.5); Ping gaps never exceed 250 ms. Alternative: no stated tolerance.
   Against: untestable. Reason: the same tolerance as level 1 (0014).
8. **Level 1, last TCI client leaves (L8).** AetherSDR writes the P2 `LIMIT_<name>` registers
   and `KEYED_TIMEOUT` it had written for TCI back to its user interface's values.
   Alternative: leave them. Against: a TCI session value would stay in force on P2 after the
   TCI session ended (C5.10.1 item 4). Reason: the session end means the same on both levels.
9. **Level 1, 1→2 switch while unarmed (L12).** The radio sends no drop; AetherSDR checks the
   active level (A2.5a step 7) and reports `level_change`, not `takeover`. Alternative: report
   every unexplained end as `takeover`. Against: the user would be told another host took the
   radio. Reason: the cause is visible on the management channel.
10. **`TRX:0,true,tci;` without `AUDIO_START` (L14).** A microphone request, as [TCI] §4.2 TRX
    note says ("otherwise the microphone signal is taken"); `VOLUME` and `MUTE` do not change
    the TCI RX audio stream (§17.2), listed in Annex C-C. Alternative: accept TX audio without
    `AUDIO_START`. Against: deviates from [TCI] without need. Reason: follow [TCI] where it is
    clear.
11. **Stale text (L10, L11).** §21 is marked as superseded in its AM point by 0022 §17, §43,
    §52; §25 cites the A2.5a steps as part C C2.7 does; the annex G-13 blocks are in the order
    of the reviews and the C9 test ids are in numeric order. No rule changes.

## 42. Part C after the rc2 review of part B (0022 §62–§73)

**Problem.** Part B changed the power bound without a PEP detector (0022 §62), the TX settings
at a session end and takeover (§64), the ATU tune cycle (§66), the SWR cap (§67), the wait for
RF gone (§68) and several details (§73 items 2, 9, 10, 18). Most of this part C follows by
reference; three points need a TCI choice: what `TX_SENSORS` arg4 reports without a PEP
detector, which TX settings end with a TCI session, and the stale text of §21 and §35.

**Chosen rule.**

1. **`TX_SENSORS` arg4 without a PEP detector.** arg4 carries the PEP estimate of A3.4c
   (measured mean × digital crest factor), the value the safety core enforces, not the mean
   (part C C4, C-C12). Amends §21 ("arg4 carries the mean"). Alternative: keep the mean.
   Against: the client would see a peak power below the value the radio limits, and for SSB
   voice the reported peak would be about 12 dB low.
2. **TX settings on level 2.** The settings of Table A3-4 have no TCI command; on level 2 the
   firmware sets them, and at every level switch they return to the Table A3-4 values, so
   neither level inherits the other's (part C C8.5a item 1; A2.5a step 4, A3.6a). The standard
   TCI TX parameters (`DRIVE`, `TUNE_DRIVE`, split, XIT, monitor, CW speed and delay) are kept
   across a TCI session end, as RX settings are (C8.5a item 2); the TX-side session state of
   part C (limits, keyed timeout, policy, queued CW text) already ends with it. Alternative:
   reset `DRIVE` and `TUNE_DRIVE` to 0 at every TCI session end. For: a new client starts at
   no power. Against: [TCI] has no session and no defaults; every client receives the current
   values at connection ([TCI] §3.1, part C C3.1), so nothing is hidden, which was the problem
   0022 §64 solves on P2; power stays bounded by the limit in force and the arm.
3. **Stale text.** §21's "capped at `P_swr` until the unkey" is superseded by 0022 §67 (the cap
   holds to the end of the continuous transmission, part C C8.1), and its AM point by 0022
   §62 as well (the class-based mean bounds are not conservative; part C C5.6). §35's drop
   reason `RESET` for `RESTART` is superseded by 0022 §73 item 2 (`MAINTENANCE`; part C C2.10
   item 1). No other change.

**Reason.** Follow part B by reference wherever the behaviour is level-independent; decide on
TCI only what TCI shows to clients.

## 43. Part C rc3: review fixes and the hang-delay meaning of "keyed" (rc3 review M1–M9, L2–L18)

**Problem.** The review of the part C rc3 draft found an arm reject order that contradicts the
update state, an unstated sample count in TX audio blocks, a level-1 limit tier that ignored
AetherSDR's own user interface, TX source and audio changes while keyed left open, `TRX`/`TUNE`
undefined for most TX sources, the hang delay not covered by "keyed" on TCI (part B now defines
it, 0022 §74), an overstated known limit, a power test for only one detector model, no START
state on level 2, and a set of smaller gaps.

**Chosen rule.**

1. **Arm reject order (M1, L12).** `BAD_TOKEN`; the no-op of a valid arm while armed (also while
   keyed, so never `PTT_ACTIVE` for an armed radio); C5.5.6 item 5 (`MAINTENANCE`, also during an
   unconfirmed trial boot); then items 1, 2 (`IN_FAULT` before `INHIBITED`), 3, 4, 6, 7 (part C
   C5.5.3, C5.5.6). Amends §41 item 5. Alternative: keep items 1–7 in numeric order. For: one
   simple rule. Against: during an update the device is stopped (C2.8 item 2), so every arm
   would read `NOT_RUNNING`, contradicting C2.8 item 3 and hiding the cause.
2. **TX audio blocks (M2).**
   - **2a.** `Stream.length` and `AUDIO_STREAM_SAMPLES` count samples summed over all channels; a
      block holds `length` / `channels` frames; the block period is `AUDIO_STREAM_SAMPLES` /
      (`AUDIO_STREAM_CHANNELS` × `AUDIO_SAMPLERATE`); TX_CHRONO carries the client's sample
      amount and channel count (part C C6.3.3, C-C25, Annex C-D D10). Alternative: count frames
      per channel. For: [TCI] §4.3 recommends 512 samples at 48 kHz for 10 ms, which fits
      frames. Against: [TCI] §3.4 states for IQ that `length` is "the number of real samples" and
      complex samples are "Stream.length/Stream.channels", and AUDIO_STREAM_SAMPLES is the
      amount "indicated in a Stream.length field"; one reading for every stream. To be checked
      against a public client (D10).
   - **2b.** `G7250_EXT` replies (L2): `G7250_EXT:true;` is answered first, before `G7250_PROFILE`;
      `G7250_EXT:false;` is answered as the last extension message (C5.2). Alternative: no reply
      to `false`. Against: [TCI] answers every set; the client could not tell that the opt-out
      took effect.
3. **Level-1 limits and drop field (M3, L3).** AetherSDR writes to P2 the strictest of its user
   interface's value and the TCI session value; a TCI write looser than the user interface's
   value is rejected with `LOOSER_LIMIT`; the reply carries the limit in force (C5.10.1 item 6).
   Alternative: accept the TCI value and let P2 report the stricter one. Against: the client
   would believe a value acts that does not. The `drop` field names Table B8-3 drop reasons only
   (`STOP` and `HOLDER_LOST` are Table B8-3 names, 0022 §30).
4. **TX source and TCI audio while keyed (M4, L4).** While keyed, the hang delay included, the TX
   source never changes; a TX request of another source from the keying client is refused and
   not latched; the row of Table C8-1 is fixed at the key. `AUDIO_STOP` or a change of
   `AUDIO_SAMPLERATE`, `AUDIO_STREAM_SAMPLES` or `AUDIO_STREAM_CHANNELS` from a client keyed with
   source `tci` and a running `AUDIO_START` unkeys (`unkey` 1), then applies (C7.5 items 7, 8).
   Alternatives: (A) switch source on request. Against: the keyed-liveness row and the
   TX_CHRONO duty would change under a transmission. (B) defer the audio change to the unkey.
   For: no unkey. Against: the block period checked at the key (C6.3.3) would no longer hold,
   and the client would send blocks in a format the server no longer expects; unkeying is the
   safe side. `G7250_TX_ARM` accepts `00000000` and the single digit `0` as disarm, and rejects
   any other malformed value with `BAD_TOKEN` (C5.5.3): a disarm is a tightening and must not
   fail on form.
5. **`TRX`/`TUNE` per TX source (M5).** `TRX` is `true` for `TRX`, `KEYER` (from the first key-down
   that keys to the end of the hang delay, [TCI] §4.4 "The first press switches the transceiver
   to transmission") and CW text (until the queue and terminal mode have ended, [TCI] §3.2.1);
   `TUNE` is `true` for `TUNE` and for an ATU tune cycle; a server-side unkey is reported with the
   same command set to `false`; `TRX:0,false;` and `TUNE:0,false;` stop every source (C7.4.1).
   Alternative for the ATU cycle: leave `TRX` and `TUNE` `false`. Against: a generic client would
   show receive while a tune carrier is on air, and its tune button could not stop it.
6. **"Keyed" includes the hang delay (M6).** C7.6 and C5.7 use the part B meaning (A3.1a, A3.4d,
   A3.9; 0022 §74); CW text counts as keyed until its queue is empty. In a gap: a TX-frequency
   change that needs another RF-path state ends the hang delay (unkey, RF gone, SEND released,
   T/R returned, then applied), and its reply and synchronisation are sent only once applied, as
   part B answers such a write (0022 §74); `MODULATION`, front-end changes and `G7250_ATU_TUNE`
   are refused, as while RF is on; a receive-only change stays deferred; a controller ANT or ATU
   press stays ignored. A refused mode change keeps the queued CW text; an accepted one can only
   come after the transmission, when no text is queued. A keyer element whose condition fails
   stops the keyer (C7.6.7). Alternative: end the hang delay on a `MODULATION` or front-end
   command, as P2 does for owner changes. For: the same as P2. Against: on TCI these are commands
   from any client, refused while keyed since §8; A3.9 refuses command-driven changes ("a change
   requested by a command is refused"), so refusing in the gap keeps one TCI rule and does not
   let any client end another's transmission by a side effect.
7. **Known limit and ATU on level 1 (M7, L7).** The known limit of C8.2.3a covers row 1: a client
   that keeps answering TX_CHRONO, with zero samples or cached audio, is caught only by the
   maximum TX time; in `AM` and `NFM` zero audio is the full carrier. No further bound in profile
   1. Alternative: in `AM` and `NFM` unkey after a run of all-zero TX audio blocks longer than
   30 s. For: bounds a hung client's carrier well below 5 min. Against: [TCI] §3.4 calls zero
   blocks "no signal" and "preferable", so applications that hold PTT in silence (a voice keyer
   between messages, a digital-mode application idling) would be cut; P2 has the same limit for
   cached I&Q, and both levels should behave alike (0014); a client can set a stricter
   `LIMIT_TX_TIME`. (L1) AetherSDR writes `ATU_TUNE` = 0 also on the requester's keyed-liveness
   expiry and connection loss (C5.7), as every other end of the cycle.
8. **`TRX:0,true,tci;` in `CW` (L8).** Keys a CW carrier at `DRIVE`; no TX_CHRONO, TX audio
   discarded, `TX_SENSORS` arg2 `-140` (C6.3.4). Alternative: modulate the TX audio as in `USB`.
   Against: the mode class is CW, whose bounds assume a constant envelope (Table A3-3), and Table
   C8-1 row 2 has no TX audio underrun.
9. **START on level 2 and `STOP` on level 1 (M9, L9).** (L2) The device starts by itself at
   power-on, at every switch to level 2 and at the end of a TCI session (and, with no client
   connected, when the link returns to 100 Mbit/s), if the link and update state allow it; a
   client `STOP` lasts until a client `START` or the session end (C4 `START`); target until G6.
   Alternative: start only on a client `START`. Against: generic clients do not send `START`
   ([TCI] §4.2: the server's own operator starts ExpertSDR3), so they would see no RX. (L1) A
   `RUN_CLEARED` caused by a TCI `STOP` is reported as `STOP` (C5.5.5 row 5), as C4 `STOP` says.
10. **Power test (M8).** T-C5-09 states expected values for each detector model of Table A3-3.
    No rule change.
11. **`G7250_WRITE_STATUS` coverage (L11).** Every refusal by a part C rule of a request from an
    opted-in client is reported, TX requests included (`NOT_ARMED`, `KEYED`, `NOT_KEYABLE`,
    `BAD_VALUE`), except arm requests, stream starts and commands ignored without a reply
    (C5.12). Alternative: only extension sets and `MODULATION`. Against: an opted-in client
    could not tell why its `TRX` did not key.
12. **Fault before inhibit; second arm (L12).** `IN_FAULT` is reported before `INHIBITED`
    (the fault is the stronger state, A3.5); a valid arm while armed, also while keyed, is the
    no-op of C5.5.5.1, not `PTT_ACTIVE` (C5.5.3). No alternative was weighed: both follow from
    item 1.
13. **`G7250_ATU` from `ATU_STATE` (L13).** 0 `bypass`; 1, 2 and 3 `inline`; 4 the in/out state
    the server knows (L2), else the value before the cycle, until HIS-08 (C5.7). Alternative:
    report `failed` in `G7250_ATU`. Against: `G7250_ATU` is the in/out state; the cycle result is
    `G7250_ATU_STATE`.
14. **`CW_TERMINAL` per client (L14).** As a unidirectional command ([TCI] §3.3, §4.5
    "Unidirectional control") it applies to the CW text of the client that set it and ends with
    its connection (C4). Alternative: synchronised device state. Against: [TCI] gives it the
    unidirectional type, and another client could keep a transmission keyed it did not start.
15. **Glossary and small fixes (L15, L5, L6, L10).** Glossary: new entries: key-down cap, CW text liveness, TX audio underrun, unkey
    broadcast, effective TX frequency; "generic keyed window" corrected (it names Table C8-1
    rows, not "sources that produce no frames"); "keyed" in TCI terms and including the hang
    delay for RF-path purposes. C5.1.1 states the case of part C enumerations (lower case)
    and Table B8-3 names (upper case), both case-insensitive in sets; `G7250_PREAMP` is listed in
    C7.6.5; T-C2-13 cites C2.10 item 2. No rule change.
16. **Annex (L16).** §3.1 row 2 says which bytes are compatible and lists PA enable as a gap;
    G-09 re-arms also on a valid `G7250_TX_ARM`; G-13 bases `RECEIVE_ONLY` on the backend's
    transmit capability, because the capability record is not available before a P2 session.
17. **Annex C-B (L17).** C-B19 (budget refusal of stream starts), C-B20 (one block per binary
    message; other messages discarded), C-B21, C-B22.
18. **Header and C2.7 (L18).** Part C cites `network-interface.md` rc3 and 0022 §62–§74; in C2.7
    AetherSDR MUST check the active level before reporting a loss of ownership, so that the MUST
    on the report rests on a MUST. Alternative: SHOULD on both. Against: a wrong `takeover`
    report would tell the user another host took the radio.

**Reason.** Follow [TCI] where it speaks, part B where the behaviour is level-independent (0022
§74), and choose the safe side (unkey, refuse) where a transmission's basis would change under
it (0011 point 3).

## 44. Part C rc4 draft: review fixes of rc3 (rc3 review M1–M8, L1–L12)

Status: proposed.

**Problem.** The review of part C rc3 found `TX_ENABLE` tied to the key state, no rule for a
TX audio block of another length than TX_CHRONO asked, the level-1 DUC0 frequency not tied to
the effective TX frequency, a reject reason (`LEVEL_NOT_ACTIVE`) that the reject order made
unreachable, no rule for `G7250_TX_POLICY:holder` set under a non-holder's transmission, an
incomplete feature token list, a "row fixed at the key" rule that contradicts terminal mode,
a TX audio underrun test that the keyed timeout would pre-empt, and twelve smaller gaps. In
parallel part B changes the restart (0022 §78) and the frequency encoding (0022 §81).

**Chosen rule.**

1. **`TX_ENABLE` is a permission (M1).** `TX_ENABLE` is `true` exactly when C5.5.6 items 1, 2
   and 4–9 hold; item 3 (not keyed) applies only to the arm request, so `TX_ENABLE` stays
   `true` while keyed (part C C4, C5.5.4, C5.5.6, C-C31; T-C5-07). C2.8 item 2 rests on item
   8 (unarmed), not item 3. Alternative: keep item 3, so `TX_ENABLE` goes `false` while keyed.
   Against: [TCI] §4.3 defines it as "transmission allowed / transmission denied", a
   permission; a generic client would grey out its PTT button during its own transmission and
   see a toggle on every CW element.
2. **TX audio block of another length (M2).** A TX_AUDIO_STREAM block whose `length` differs
   from TX_CHRONO's is accepted when `length` is a multiple of `channels` and the data part is
   at most 16384 bytes; it is played in full and feeds both the TX audio underrun and the
   keyed timeout; a block that fails either condition is discarded and feeds neither (part C
   C6.3.5, C-C30, D11; T-C6-10). Alternative: discard every block of another length, feeding
   neither timer. For: the server sees exactly the period it planned. Against: [TCI] §3.4 does
   not forbid it, a client that rounds its block size would be unkeyed by the underrun after
   `TX_STREAM_AUDIO_BUFFERING` + 500 ms with no error visible to a generic client, and the
   bounds kept (whole frames, [TCI]'s 16384-byte data limit) are what the server needs to
   play the block safely.
3. **DUC0 = effective TX frequency on level 1 (M3).** AetherSDR's P2 DUC0 frequency MUST always
   be the effective TX frequency (channel A, or channel B with split, plus XIT); no TX offset
   in the baseband DUC I&Q (part C C7.6.1 item 5; annex G-08a, G-13; T-C7-24). Alternative:
   allow small offsets in the baseband. Against: the radio checks `LIMIT_TX_FREQ` and chooses
   the RF-path state on DUC0 (A3.1b, Table A3-2), so a baseband XIT near a band edge would
   transmit outside the range the radio checked.
4. **`LEVEL_NOT_ACTIVE` reachable (M4).** (L1) When AetherSDR knows from management
   identification I-4 that level 2 is active, item 4 is checked before item 1 (part C C5.5.3,
   C5.5.6); on level 2 item 4 always holds, so the reason is level-1 only (T-C5-04). The
   update case of `MAINTENANCE` in T-C5-44 is marked (L2): on level 1 the P2 session ends at
   `UPDATE_BEGIN` (A1.8) and P2 shows no update state; AetherSDR MAY report `NOT_RUNNING`; a
   trial boot reaches TCI as the P2 reject reason. Alternative: drop `LEVEL_NOT_ACTIVE` from
   T-C5-04. Against: C2.7 already requires AetherSDR to read I-4, and the reason tells the
   user why TX is unavailable.
5. **`holder` set while a non-holder keys (M5).** The server unkeys that transmission (`unkey`
   1, arm kept, unkey broadcast; an ATU tune cycle ends `failed`) (part C C5.5.8, C-B8;
   T-C5-56). Alternative: let the transmission run to its end. Against: the point of the
   tightening is to stop other clients keying; an untimed `TUNE` or terminal-mode CW of a
   non-holder could run on for up to the maximum TX time.
6. **Feature tokens complete (M6).** Table C5-1 lists one token, with one line of meaning, for
   every MAY or SHOULD command or group of C4, every MAY part of a MUST command and every
   optional extension; `cw_keyer` is the radio's keyer for the controller's KEY input with
   `CW_KEYER_SPEED`, `keyer` the client-timed `KEYER` command; new tokens `recorder`, `volume`,
   `lock`, `agc_fast`, `agc_gain`, `mon`, `footswitch`, `cw_terminal`, `spot_click`, `focus`
   (part C C4.1, C5.4; T-C5-61). Alternative: narrow C4.1 to commands with tokens and let a
   client discover the rest by "no reply". Against: a notification (`VFO_LOCK`,
   `CW_MACROS_EMPTY`, `TX_FOOTSWITCH`) and a value such as `AGC_MODE` `fast` cannot be
   discovered by the absence of a reply.
7. **Row fixed except terminal mode (M7).** The opt-in state (the column of Table C8-1) is
   fixed at the key; the row is fixed too, except the moves between rows 6 and 7 of CW text in
   terminal mode (C8.2.3), which are one TX source (part C C5.2, C7.5 item 7; T-C8-26). No
   alternative weighed: C8.2.3 already defines the moves.
8. **T-C8-03 (M8).** The client keeps sending other application frames (`G7250_KEEPALIVE`
   every 100 ms), so only the underrun acts; the expected unkey is 3. Test fix only.
9. **One listening socket (L1).** C2.10 item 4 speaks of the one listening socket, which is the
   spare listener once all client sockets are in use (C2.5). Wording only.
10. **`active` false on level 1 (L2).** `G7250_PROFILE` `active` becomes `false` at every end of
    AetherSDR's P2 session: also a TCI or user-interface `STOP`, a P2 watchdog expiry, a
    firmware update and a link below 100 Mbit/s (part C C5.3; T-C5-62). Alternative: only level
    change and takeover. Against: `active` means "owns the RF chain now" (0011 point 2).
11. **Restart on level 1 (L3; 0022 §78, §81).** After a stop, a watchdog standby or a link
    loss the radio keeps the RX-side settings for the same IP address and port; the TX
    settings are reset at every session end; a run = 1 from that host restarts the session.
    AetherSDR resends the General packet (for the arm and PA enable) and the DUC-specific
    packet after every session end; the DDC-specific packet also after a takeover, reset,
    update, level or address change (part C C7.2.1, C8.5a item 3; annex G-08b; T-C8-28).
    Frequency encoding: discovery byte 21 = 1 always, scale 122 880 000 Hz (0022 §81), so
    annex G-11 is compatible. No part C alternative: part C follows part B here.
12. **Write reject names (L4).** C5.12 states that part B owns Table B8-3 and that the TCI use of
    `KEYED`, `NOT_ARMED` and `NOT_KEYABLE` is defined in C5.12. Wording only; Table B8-3 is
    not edited here.
13. **Discarded binary message (L5).** A binary message discarded for its form (C2.2, C6.3.5)
    is not an application frame; a well-formed block whose audio is not used (C6.3.4, C7.5 item
    4) still is (part C C2.2, C8.2). Alternative: every binary message counts. Against: a
    client sending garbage would hold the keyed timeout with no usable audio.
14. **`TRX:0,true;` restates `TRX:0,true,tci;` without `AUDIO_START` (L6).** Both are
    microphone requests (C-C21), so they are one source and restate each other for the
    generic keyed window (part C C8.2.3, C-C33; T-C8-27). Alternative: distinct sources.
    Against: C4 `TRX` already gives them the same meaning, and refusing one as a source change
    would unkey a client that only drops the `tci` argument.
15. **CW text outside `CW` (L7).** Refused as `KEYER` is: ignored without a reply, not queued,
    not latched (part C C4, C5.12, C-C32; T-C4-16). Alternative: switch the mode to `CW` or
    send the text in the current mode. Against: [TCI] §3.2 places CW text under "Working in CW
    mode"; a mode change by a side effect would change the mode class under the arm.
16. **`G7250_KEYED_TIMEOUT` raised by a non-holder (L8).** Rejected with `LOOSER_LIMIT`, the
    value in force replied (part C C5.10, C5.12; T-C5-59). No alternative weighed: the same
    rule as `G7250_LIMIT` (C5.10.1 item 3).
17. **`holder` while disarmed (L9).** Refused: `any` replied, `NOT_ARMED` to an opted-in
    requester (part C C5.5.8; T-C5-58, T-C5-17, T-C5-48 amended). Alternative: accept.
    Against: the policy returns to `any` whenever no holder remains and every arm starts with
    `any`, so the accepted value could never act.
18. **User-interface holder on level 1 (L10).** AetherSDR's user interface counts as an arm
    holder for C5.10.1 item 3: while it alone holds the arm, a TCI client's write of 0 or of a
    looser value is rejected (part C C5.10.1 item 3; T-C5-60). Follows from C5.5.5.1 item 2.
19. **Level-1 keyed timeout (L11).** AetherSDR SHOULD NOT write a P2 `KEYED_TIMEOUT` below
    twice its High Priority keep-alive period (200 ms) (part C C5.10). Alternative: no advice.
    Against: at 100 ms one late keep-alive unkeys a healthy transmission.
20. **Arm from a client that has not opted in (L12).** A `G7250_TX_ARM` with an arm value from
    such a client is ignored without a reply and not latched; the disarm value is accepted
    from every client (part C C5.2, C5.5.3, C5.12; T-C5-57). Alternative: accept. For: a
    client that knows the derivation could arm without the extension traffic. Against: it
    would hold an arm whose `G7250_TX_ARM_STATE` and token changes it cannot see; the safe
    side is to require the opt-in (0015).
21. **Glossary and labels.** "Session" lists an address change (Set IP, C-1, DHCP) as an end
    cause and the run = 1 restart (0022 §44, §78); "Effective TX frequency" names the level-1 DUC0
    rule. Part C, the annex and the glossary carry "rc4 draft, 2026-11-19".

**Reason.** Follow [TCI] where it speaks (`TX_ENABLE`, CW mode), accept what the server can
play safely (block length), and choose the side that stops a transmission or refuses an arm
where a rule would otherwise let a client key without the state it needs to see (0011 point
3; 0015).

## 45. Part C rc4: review fixes of the rc4 draft (rc4 draft review H1, M1, M2, L1–L10)

Status: proposed.

**Problem.** The review of the part C rc4 draft found that after a P2 session end without a
takeover (a stop, a watchdog standby, a link loss) AetherSDR was not required to write the
TX-side P2 registers again, although part B resets them at every session end (0022 §78); no
bound on buffered TX audio and no rule for a TX audio header that differs from the client's
settings; a feature test that expected every missing part of a command to be ignored without
a reply; and ten smaller gaps. In parallel part B defines CW break-in clear and RF in element
gaps (0022); part C refers to part B for those and does not restate them.

**Chosen rule.**

1. **TX-side P2 state after every session end (H1).** After every end of its P2 session, with
   or without a takeover, AetherSDR MUST write `TX_MODE_CLASS`, every P2 `LIMIT_<name>` as
   C5.10.1 item 6 sets it and `KEYED_TIMEOUT` if it uses it, before it arms (part C C5.10.1
   item 6, C7.2.1, C8.5a item 3; annex G-08b, G-13; T-C8-28). C5.10.1 item 6 states that the
   value is written at every change of either input and at every session start. Alternative:
   rely on the restart keeping them. Against: part B keeps only the RX-side settings and returns
   `TX_MODE_CLASS`, `KEYED_TIMEOUT` and the session limits at every session end (B5.4 restart
   item 2; A3.6; 0022 §78), so a TCI session limit would silently stop acting on P2.
2. **TX audio buffer bound and header mismatch (M1).** Buffered TX audio of the keying client
   is bounded to `TX_STREAM_AUDIO_BUFFERING` plus one block of the TX_CHRONO length; frames
   beyond are dropped, and the block still counts as an application frame and feeds the TX
   audio underrun. A block whose `channels`, `sample_rate` or `receiver` differs from the
   client's settings is discarded and feeds neither timer. A block of `length` 0 is accepted
   and feeds both timers (part C C6.3.5, C-C30; T-C6-10). Alternatives: (a) unbounded buffer.
   Against: audio could lag the client without limit, and a later unkey would still find
   seconds of audio queued. (b) Discard the whole block at the bound and not count it. Against:
   a client that sends slightly fast would be unkeyed by the underrun although it is alive.
   (c) Refuse `length` 0. Against: [TCI] §3.4 calls a zero-sample block "preferable" for no
   signal, and C8.2.1 and T-C8-03 rely on it.
3. **Missing parts of a command (M2).** "Ignored without a reply" holds only for whole
   commands; a missing part of a command is refused as its C4 row states: `RX_CHANNEL_ENABLE`
   ch 1 `true` answered with `false`, `AGC_MODE` `fast` ignored, an unsupported
   `AUDIO_SAMPLERATE` or `IQ_SAMPLERATE` answered with the rate in force, a microphone `TRX`
   answered with `TRX:0,false;` (part C C4, C4.1; T-C5-61). No alternative weighed: the
   command rows already state these refusals, except the `AUDIO_SAMPLERATE` reply, which is
   given the form [TCI] §4.3 gives `IQ_SAMPLERATE`.
4. **Restart after a server stop (L1).** C2.9a points to C4 `START`: on level 2 the automatic
   start where its conditions hold, otherwise a client `START` (part C C2.9a; T-C2-21).
   Wording; follows §43 item 9.
5. **Inferred ownership loss (L2).** A loss that AetherSDR only infers (200 ms without DDC0
   and status, or a sequence restart) is reported as an outage, drop reason `LINK_DOWN` and
   stream reason `link`, not `TAKEOVER`; recovery needs a restart by the user, and AetherSDR
   does not set the run bit again by itself (part C C7.2.1; T-C7-12, T-C7-15). Alternatives:
   (a) report `TAKEOVER`. Against: the client would be told of a takeover that may be a cable
   fault. (b) Let AetherSDR retry run = 1 within a few seconds. Against: if another host owns
   the radio, a run = 1 is a takeover, the ping-pong that 0022 §3 point 6 forbids; the safe
   side is the user restart, which after an outage still finds the RX-side settings kept
   (B5.4).
6. **Policy unkey in C7.7 (L3).** The unkey of §44 item 5 is listed among the server-side
   unkeys of C7.7; its reason stays `unkey` 1, defined as "the policy has withdrawn the
   non-holder's TX request, which counts as released" (part C C5.5.8, C7.7; T-C5-56).
   Alternative: a new reason number. Against: the number is part B `TX_STATE` [23:16], owned by
   part B, which has no policy cause on P2.
7. **Annex wording (L4).** The annex G-13 rc4 bullet ignores an arm value only "from a client
   that has not opted in" (§44 item 20). Wording only.
8. **Session and RX-side settings (L5).** The glossary "Session" needs no 0→1 edge of the
   host's run bit (A2.3; B5.4), and the RX-side settings kept are every General packet field
   except byte 38 bit [0] and byte 58 bit [0], the DDC-specific packet and the receive state of
   High Priority, as B5.4 lists them (part C C8.5a item 3; annex G-08b; glossary). Follows part
   B.
9. **Application frame (L6).** The glossary counts only binary messages with one block that
   C2.2 and C6.3.5 accept (§44 item 13). Wording only.
10. **Tokens for optional parts (L7).** `AGC_MODE` is SHOULD, so `fast` is a MAY part of a
    SHOULD command; C4.1 speaks of every optional part of a command. New tokens `iq_384`
    (`IQ_SAMPLERATE` 384000 where 0004 point 6 allows it) and `mic` (the microphone sources of
    `TRX`, HIS-17) (part C C4, C4.1, C5.4, Table C5-1; T-C5-61). Alternative: let a client
    discover them from the reply with the value in force. Against: §44 item 6 requires a token
    for every optional part, and the refusal comes only after the client has tried.
11. **T-C7-24 and the reject order of a TX request (L8).** The test keys with
    `TRX:0,true,tci;` and a running `AUDIO_START`, so that no microphone path is needed; where
    several reasons apply to one TX request, the order is `BUSY`, `NOT_ARMED`, `KEYED`,
    `BAD_VALUE`, `NOT_KEYABLE` (part C C5.12; T-C7-24). Alternative: `NOT_KEYABLE` before
    `BAD_VALUE`. Against: a malformed request is wrong whatever the radio's state, and C5.7 already
    puts the request's own faults before the key conditions for `G7250_ATU_TUNE`.
12. **Row-3 restatement after `AUDIO_START` (L9).** A `TRX:0,true,tci;` from a client keyed in
    row 3 that has since started `AUDIO_START` is a restatement of the row-3 request: the row
    is fixed at the key (§44 item 7), the transmission stays a microphone one (part C C8.2.3;
    T-C8-29). Alternative: a source change, refused. Against: the client sends the same command
    that keyed it, and a refusal would not restart the generic window, so a live client would
    be unkeyed after 1 s.
13. **`G7250_TX_STATE` per CW element (L10).** `keyed` follows each element and toggles per
    element; in a gap `source` keeps the transmission's source and `mine` stays `true` for the
    keying client until the transmission ends (part C C5.5.3; T-C5-63). Alternative: hold
    `keyed` `true` over the gaps, as `TRX`. Against: `keyed` means "PA actually keyed"; `TRX`
    already gives the transmission view (C7.4.1). Whether RF may be present in a gap is part B's
    break-in rule (0022), cited, not restated.
14. **Labels.** Part C, the annex and the glossary carry "rc4, 2026-11-19".

**Reason.** Follow part B where it resets or keeps state (0022 §78), bound what the server
holds for a client, and choose the side that tells a client the truth (outage, not takeover)
and never retakes the radio by itself (0022 §3 point 6; 0011 point 3).

## 46. Part C rc4: review fixes of rc4 (rc4 review M1, L1–L9)

Status: proposed.

**Problem.** The review of part C rc4 found that on level 1 AetherSDR sends TCI CW as DUC I&Q
with PTT, but nothing said how break-in and the hang delay work then, that the radio's gap
check (0022 §84) cannot run inside such a PTT transmission, and that TCI CW with hardware CW
selected would be dropped by the radio (0022 §85); and nine smaller gaps.

**Chosen rule.**

1. **Level-1 hang delay of TCI CW (M1).** AetherSDR implements break-in and the hang delay
   by holding PTT, with DUC I&Q at zero, until its hang delay has run out without a new
   element; the hang delay is the value it writes to DUC-specific bytes 11–12, clamped to
   2000 ms as part B A3.4d; with hang delay 0, PTT is per element (part C C8.2.5 item 1; annex
   G-13; T-C8-30). Alternative: clear PTT in every gap. Against: the T/R relay and an external
   amplifier would switch at every element, which the hang delay exists to avoid (0022 §73
   item 9).
2. **Gap check on level 1 (L1).** Part B A3.9a item 6 applies the per-element check where the
   radio forms the elements (level 2, and P2 KEY and CWX); on level 1 the check does not run
   inside AetherSDR's PTT transmission. Known limit, bounded by item 1's 2000 ms (part C
   C8.2.5 item 2; 0022 §87 item 7). Alternative: P2 CWX for TCI CW. Against: §36 (the paddle
   bits cannot play a client's straight-key timing, and the 1 s cap cuts strings).
   *Corrected by §47 item 1:* the 2000 ms bound did not hold (the PTT does not clear while
   gaps are shorter than the hang delay); the radio now checks zero-sample gaps inside the
   PTT transmission (0022 §88 item 1).
3. **TCI CW with hardware CW selected (L2).** AetherSDR refuses TCI CW with `NOT_KEYABLE`
   while the user has hardware CW (byte 5 bit [1]) selected, and does not clear the bit itself
   (part C C8.2.5 item 3; T-C8-22). Alternative: send a DUC-specific packet with bit [1] clear
   before the PTT edge. Against: it overrides the user's choice of the radio's keyer silently
   and adds a change of a state field before every TCI CW key.
4. **Write echo before PTT (L3).** AetherSDR waits for the P2 write echo (B8.4) of
   `TX_MODE_CLASS` and the `LIMIT_<name>` writes before its PTT edge (part C C5.10.1 item 6,
   C8.5a item 3; T-C8-31).
5. **`STOP;` at every session end without a client `STOP` (L4).** Also after a watchdog
   standby, a link loss and an inferred loss (part C C2.9a, C7.2.1; T-C8-31).
6. **C5.12 rationale (L5).** `BAD_VALUE` comes "before the key conditions of A3.1a". Wording.
7. **`keyed` on level 1 (L6).** AetherSDR derives `G7250_TX_STATE` `keyed` from its own
   element timing, because P2 `TX_STATE` shows the PTT transmission (part C C5.5.3; T-C5-64).
8. **Policy unkey of a tune cycle (L8).** It makes AetherSDR write `ATU_TUNE` = 0 (part C
   C5.7; T-C5-64).
9. **`MAINTENANCE` before `LEVEL_NOT_ACTIVE` (L8).** With level 2 active, where I-3 shows an
   update or trial boot, `MAINTENANCE` comes first, because the update dominates (part C
   C5.5.3; T-C5-64). Alternative: `LEVEL_NOT_ACTIVE` first. Against: the client would retry on
   level 2, which the update also ends.
10. **C5.4 (L9).** A command without a token is MUST, except a command marked NOT SUPPORTED on
    that level, which has no token and is never implemented. Wording.
11. **Buffer bound (L7).** A block is "played in full within the buffer bound"; at the bound
    the oldest buffered frames not yet played are dropped (part C C6.3.5; T-C6-10).
    Alternative: drop the newest frames. Against: the lag would stay at the bound for as long
    as the client sends fast, while dropping the oldest keeps the newest audio on the air.
12. **Labels and cross-references (L9).** The part C header cites 0022 §84–§87; the glossary
    "Keyed" counts CW text as keyed until its queue is empty and the hang delay after its last
    element has run out (part C C7.4.1); T-C5-61 also checks that `iq_384` and `mic` are
    present where implemented. Labels stay "rc4, 2026-11-19".

**Reason.** Make level 1 behave as part B does where the radio forms the CW, state the one
case where it cannot, and keep the user's keyer choice and the safety order of part B.

## 47. Part C rc4: second review round of rc4 (rc4 review M1, L7)

Status: proposed.

**Problem.** §46 item 2 bounded the level-1 gap-check limit by the hang delay of at most
2000 ms. With gaps shorter than the hang delay AetherSDR never clears the P2 PTT, so the
bound was the maximum continuous TX time instead (part B Table A3-2). And C8.2.5 item 1 did
not say what a hang delay of 0 costs on level 1.

**Chosen rule.**

1. **Gap check on level 1 (M1; corrects §46 item 2).** Part B now treats a run of all-zero
   DUC samples longer than `t_blank` inside a PTT transmission with DUC I&Q as no RF
   commanded (0022 §88 item 1), so the check "RF while not keyed" runs in every gap of TCI CW
   on level 1 and detects RF there within `t_blank` + 10 ms. AetherSDR MUST send exact zeros
   (I = Q = 0) in gaps and the hang delay. Remaining known limit: non-zero samples in a gap
   hide that gap from the check (part C C8.2.5 item 2; annex G-13; T-C8-32). Alternative: P2
   CWX for TCI CW. Against: §36, as in §46 item 2.
2. **Hang delay 0 on level 1 (L7).** With a hang delay of 0 each element is a PTT
   transmission: it costs the key latency (`t_settle` plus the RF delay, part B A3.9a items 2,
   4) and a T/R cycle per element, the first samples survive only within the 25 ms unkeyed
   FIFO (part B B10.7), and the 10 ms edge rule of part B B11.6a (Annex X1 D28) applies. A
   hang delay above 0 is RECOMMENDED for break-in CW (part C C8.2.5 item 1 note).
   Alternative: forbid a hang delay of 0 on level 1. Against: [P2] allows it (DUC-specific
   bytes 11–12), and a user may accept the cost.

Labels stay "rc4, 2026-11-19".

**Reason.** The radio sees every DUC sample, so it can find the gaps itself instead of
relying on a bound that does not hold.

## Consequences

- Part C draft 2 applies these choices and cites them as "0021 §n".
- Part A (owned elsewhere) gets: the management port MUST NOT be 50001 (§2); a configuration
  item for the TCI allow-list (§10); the answer to A2.5 (§16).
- `spec/annex-aethersdr.md` G-13 gets: default port 50001 kept, `PROTOCOL:ExpertSDR3,2.1;`
  kept, `DEVICE` SHOULD become `G7250` (§4, §5), `G7250_TX_POLICY` (§1), the TX_CHRONO rule
  (§7), the reach restriction (§10).
- Remaining open items in part C depend only on the HIS or G6.
- Part C draft 3 applies §18–§26. §19 replaces the frequency and front-end parts of §8, §22
  replaces the lower-case reading of §14 for code names, and §24 point 4 adds return points to
  §1.
- `spec/annex-aethersdr.md` G-13 later gets (not edited here): the TCI-side keyed liveness and
  PTT gating of §18 point 6, `G7250_KEEPALIVE`, `G7250_KEYED_TIMEOUT`, `G7250_WRITE_STATUS`,
  the several-sources arm of §24, the takeover behaviour of §26, and the absent extensions of
  §23.
- Part C rc3 draft applies §27–§41 (status: proposed, for ON8ST review). `spec/annex-aethersdr.md`
  G-13 and Q-O3 get the level-1 consequences of §27–§41; the glossary gets the TCI terms. Part
  B is not changed: where part C needs a part B rule (A1.6, A1.6a, A1.9, A2.5a, A3.9b, A3.9c,
  B10.5, B10.5a, Table B8-2) it cites it.
- Part C rc3 draft applies §42 and follows 0022 §62, §64, §66–§68 and §73 items 2, 9, 10, 18 by
  reference (C2.10, C4, C5.5.5, C5.6, C5.7, C5.10, C5.10.1, C7.2.1, C7.6.5–C7.6.7, C8.1,
  C8.5a, C9); `spec/annex-aethersdr.md` G-08a, G-08b, G-10, G-11 and G-13 get the level-1
  consequences.
- Part C rc3 applies §43 and follows 0022 §74 (part B A3.1a "Keyer elements", A3.4d, A3.9) by
  reference (C2.2, C2.7, C4, C5.1.1, C5.2, C5.5.3–C5.5.6, C5.7, C5.10.1, C5.12, C6.3, C7.4.1,
  C7.5, C7.6, C7.7, C8.2.3a, C9, Annexes C-B, C-C, C-D); `spec/annex-aethersdr.md` §3.1, G-09
  and G-13 and the glossary get the consequences. §41 item 5 is amended by §43 item 1.
- Part C rc4 draft applies §44 and follows 0022 §78 (restart with RX-side settings kept) and
  §81 (discovery byte 21 = 1) by reference (C2.2, C2.8, C2.10, C4, C5.2–C5.5.8, C5.10, C5.10.1,
  C5.12, C6.3.5, C7.2.1, C7.5, C7.6.1, C8.2, C8.2.3, C8.5a, C9, Annexes C-B, C-C, C-D);
  `spec/annex-aethersdr.md` (§3.1, G-02, G-08a, G-08b, G-11, G-13, §3.3, §6) and the glossary
  get the consequences. Part B and Table B8-3 are not changed by §44.
- Part C rc4 applies §45 (C2.9a, C4, C4.1, C5.4, Table C5-1, C5.5.3, C5.5.8, C5.10.1, C5.12,
  C6.3.5, C7.2.1, C7.7, C8.2.3, C8.5a, C9, C-C30); `spec/annex-aethersdr.md` (G-08b, G-13) and
  the glossary ("Session", "Application frame") get the consequences. Part B is not changed by
  §45; CW break-in clear and RF in element gaps are part B rules (0022), cited by reference.
- Part C rc4 applies §46 (C2.9a, C5.4, C5.5.3, C5.7, C5.10.1, C5.12, C6.3.5, C7.2.1, C8.2.5,
  C8.5a, C9) and follows 0022 §84–§87 by reference; part B A3.9a item 6 is qualified by 0022
  §87 item 7; `spec/annex-aethersdr.md` (G-13) and the glossary ("Keyed", "Break-in") get the
  consequences.
- Part C rc4 applies §47 (C8.2.5 items 1 and 2, T-C8-32) and follows 0022 §88 by reference;
  §47 item 1 corrects §46 item 2; `spec/annex-aethersdr.md` (G-13) and the glossary ("Keyed")
  get the consequences.

## Sources

- [TCI] TCI Protocol 2.1: §1.4, §3.1, §3.4, §3.5, §4.1 PROTOCOL, DEVICE, MODULATIONS_LIST,
  §4.2 MODULATION, §4.3 AUDIO_STREAM_SAMPLE_TYPE, TX_STREAM_AUDIO_BUFFERING, §4.4 TX_SENSORS.
- [AETHER-SRC] AetherSDR source, commit 9f7cbeb (2026-11-18), through
  `spec/annex-aethersdr.md` §2.4, G-13, Q-O5.
- [TCI] also §4.2 VFO, DDS, IF, SPLIT_ENABLE, XIT_ENABLE, XIT_OFFSET, RIT_ENABLE, §4.4 KEYER,
  §4.5 CW_TERMINAL, §4.7 note 5 (§18–§24).
- [RFC6455] §4.2.1, §5.4, §5.5, §5.5.2, §7.4.1. [CH394] (8 sockets). [G7250-MAN] (TX power per mode;
  ATU initial tuning ≤ 10 s). [P2] High Priority byte 4 bit [1] (PTT).
- `spec/network-interface.md` draft 4: A2.3–A2.5a, A3.3, A3.4, A3.4a, A3.4c, A3.9, B4.8, B7,
  B8.3, B8.4, Table B8-2, Table B8-3, B10.2 (§18–§26).
- [TCI] also §4.2 TRX note, START, STOP, DIGL_OFFSET, DIGU_OFFSET, §4.3 AUDIO_STREAM_SAMPLES,
  §4.4 KEYER, §4.7 notes 6 and 7 (§27–§41). `spec/network-interface.md` rc2: A1.6, A1.6a,
  A1.9, A2.5a, A3.9b, A3.9c, B10.5, B10.5a, Table B8-2 (§27–§41).
- [TCI] also §3.2.1, §3.4 (`Stream.length`), §4.2 START, §4.3 AUDIO_STREAM_SAMPLES, §4.4 KEYER,
  §4.5 CW_TERMINAL (§43). `spec/network-interface.md` rc3: A1.8, A3.1a, A3.4d, A3.9, A3.9a item
  4, A3.9b item 1, Table A3-3 (§43).
- [TCI] also §3.2 ("Working in CW mode"), §3.4 (TX_CHRONO and the TX audio answer), §4.3
  TX_ENABLE (§44). `spec/network-interface.md` rc4 draft: A1.5 (I-3, I-4), A1.8, A3.1b, Table
  A3-2, B5.4, B3.8, B10.2 item 3, B10.5 (§44).
- [TCI] also §3.4 (zero-sample block), §4.2 AGC_MODE, RX_CHANNEL_ENABLE, TRX, §4.3
  IQ_SAMPLERATE, AUDIO_SAMPLERATE, TX_STREAM_AUDIO_BUFFERING (§45). `spec/network-interface.md`
  rc4 draft: A2.3, A3.6, B5.4 (restart items 1–3) (§45).
- Decisions 0003, 0004, 0007, 0008, 0011, 0012, 0013, 0014, 0015, 0017, 0019, 0022.

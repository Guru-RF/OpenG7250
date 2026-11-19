# 0021 — Choices in the G7250 TCI profile (spec part C)

- Status: proposed (for ON8ST review at rc1), 2026-11-19
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
rule 4). Forward power is measured as in A3.4c (0022 §17): the 100 W limits apply to PEP, the
25 W AM limit to the 100 ms mean. `TX_SENSORS` ([TCI] §4.4) reports arg3, "RMS" power, as that
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
after step 2 of A2.5a: (1) if keyed, the unkey broadcast of §24; (2) if armed,
`G7250_TX_ARM_STATE` (disarmed, `LEVEL_CHANGE`) and the new `G7250_TX_ARM_TOKEN` to opted-in
clients and `TX_ENABLE:0,false;` to all; (3) no further stream blocks, and
`G7250_STREAM_STATE` `stopped`, reason `level_change`, for each running stream; (4)
`G7250_PROFILE` with `active` false to opted-in clients; (5) a WebSocket close with status
1001 on every connection ([RFC6455] §7.4.1); then the listener closes (A2.5a step 6). On
level 1, AetherSDR receives the P2 drop `LEVEL_CHANGE` before port 7250 closes (A2.5a step
3), sends (1)–(4) to its TCI clients, and keeps its TCI connections open.

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

## Sources

- [TCI] TCI Protocol 2.1: §1.4, §3.1, §3.4, §3.5, §4.1 PROTOCOL, DEVICE, MODULATIONS_LIST,
  §4.2 MODULATION, §4.3 AUDIO_STREAM_SAMPLE_TYPE, TX_STREAM_AUDIO_BUFFERING, §4.4 TX_SENSORS.
- [AETHER-SRC] AetherSDR source, commit 9f7cbeb (2026-11-18), through
  `spec/annex-aethersdr.md` §2.4, G-13, Q-O5.
- [TCI] also §4.2 VFO, DDS, IF, SPLIT_ENABLE, XIT_ENABLE, XIT_OFFSET, RIT_ENABLE, §4.4 KEYER,
  §4.5 CW_TERMINAL, §4.7 note 5 (§18–§24).
- [RFC6455] §4.2.1, §5.5, §5.5.2, §7.4.1. [CH394] (8 sockets). [G7250-MAN] (TX power per mode;
  ATU initial tuning ≤ 10 s). [P2] High Priority byte 4 bit [1] (PTT).
- `spec/network-interface.md` draft 4: A2.3–A2.5a, A3.3, A3.4, A3.4a, A3.4c, A3.9, B4.8, B7,
  B8.3, B8.4, Table B8-2, Table B8-3, B10.2 (§18–§26).
- Decisions 0003, 0004, 0007, 0008, 0011, 0012, 0013, 0014, 0015, 0017, 0019, 0022.

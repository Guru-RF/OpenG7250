# 0021 — Choices in the G7250 TCI profile (spec part C)

- Status: proposed (for ON8ST review at rc1), 2026-11-19
- Date: 2026-11-19
- Builds on: 0003 (discovery reply byte 4), 0004 (rates, SPI target), 0007 (watchdog and
  safety), 0008 (management channel, socket budget, LAN security), 0011 (two levels), 0012
  (full functionality), 0013 (AetherSDR), 0014 (one TCI profile), 0017 (no audio on the main
  unit), 0019 (reference model).

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

## Consequences

- Part C draft 2 applies these choices and cites them as "0021 §n".
- Part A (owned elsewhere) gets: the management port MUST NOT be 50001 (§2); a configuration
  item for the TCI allow-list (§10); the answer to A2.5 (§16).
- `spec/annex-aethersdr.md` G-13 gets: default port 50001 kept, `PROTOCOL:ExpertSDR3,2.1;`
  kept, `DEVICE` SHOULD become `G7250` (§4, §5), `G7250_TX_POLICY` (§1), the TX_CHRONO rule
  (§7), the reach restriction (§10).
- Remaining open items in part C depend only on the HIS or G6.

## Sources

- [TCI] TCI Protocol 2.1: §1.4, §3.1, §3.4, §3.5, §4.1 PROTOCOL, DEVICE, MODULATIONS_LIST,
  §4.2 MODULATION, §4.3 AUDIO_STREAM_SAMPLE_TYPE, TX_STREAM_AUDIO_BUFFERING, §4.4 TX_SENSORS.
- [AETHER-SRC] AetherSDR source, commit 9f7cbeb (2026-11-18), through
  `spec/annex-aethersdr.md` §2.4, G-13, Q-O5.
- [RFC6455] §4.2.1. [CH394] (8 sockets). [G7250-MAN] (TX power per mode).
- Decisions 0003, 0004, 0007, 0008, 0011, 0012, 0013, 0014, 0015, 0017, 0019.

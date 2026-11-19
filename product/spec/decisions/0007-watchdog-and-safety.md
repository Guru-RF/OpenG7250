# 0007 — Watchdog and safety core as seen on the network

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19
- Gate for: M3 (watchdog and safety, specified and tested) and M4 (transmit, only after M3)
  (design note section 6; 0001 item 6, spec section 9).
- Builds on: 0005 (G7250 register map), 0011 (single owner, shared safety core), 0015 (TX arm),
  0016 (Protocol 2), 0017 (no DDC audio).

## Context

0001 makes spec section 9, "Watchdog and safety", normative and the gate for transmit: host
timeout leads to RX stop and TX off, a maximum TX time, SWR, temperature and power limits, and
a defined state after reset or fault. 0011 puts a shared safety core below both levels: one
owner at a time, only the owner may transmit, and a level may make limits stricter, never
looser. 0015 decided that TX needs an explicit arm in the G7250 register map and left to this
decision: the arm register and value, the confirmation, the complete list of events that drop
the arm, whether takeover is allowed while armed, and the behaviour of the P2 "hardware timer"
bit. 0005 puts everything to do with TX safety into the G7250 register map, never into
reserved bytes of standard packets.

### What standard P2 gives [P2]

- **Watchdog** ("Detailed operation"). "A Command & Control packet (i.e. any C&C packet) must
  be sent from the host to the hardware at least every second (every 100 mS is recommended).
  Should a C&C packet not be received, and the hardware is in the RUN state, then the hardware
  will switch out of the RUN state into standby." In standby "the PTT output and Open
  Collector outputs will be deactivated. This is to ensure the system can't be let in a
  Transmit state following a network interruption."
- **Restart** ("Detailed operation"). The session restarts with a High Priority packet with
  RUN set "if the same network session is still active", or with a Discovery exchange, all C&C
  settings again, and then RUN.
- **What a C&C packet is.** P2 does not list it in one place. The four host-to-hardware
  packets headed "Control Elements" are the General packet, the DDC-specific packet, the
  DUC-specific packet and the High Priority packet (port 1027 by default). The memory-mapped
  register packets are headed "Memory Mapped", not "Control Elements".
- **Hardware timer bit.** General packet byte 38, "Bit [0] set = enable hardware timer";
  "Bit[0] when set enables the hardware reset timer. This should normally be set but can be
  clear to assist with software testing." "The automatic hardware reset on network or PC
  software failure may be disabled for debugging purposes" ("Detailed operation"). Added in
  V2.7, 20 Mar 2016 (revision history). Note the polarity: a host that leaves byte 38 at zero
  has disabled the watchdog.
- **Run and transmit.** High Priority packet byte 4: "Bit [0] when set enables the associated
  SDR hardware and when clear disables. Bit [1] enables transmit". The byte table lists
  "[0] = run, [1] = PTT0…[4] = PTT3"; the text says "Bits [2] to [7] are reserved for future
  use". Byte 5 bit [0] selects CW from the host (CWX), with bits [1] and [2] as dot and dash.
- **Hardware CW.** "RF and sidetone generation for CW is done in the SDR Hardware", with an
  iambic keyer ("Detailed operation"). DUC-specific packet byte 5 selects CW ([1]), break-in
  ([7]) and other keyer options; bytes 11–12 are the CW hang delay and byte 13 the RF delay,
  both in ms.
- **TUNE.** High Priority bytes 1396–1397, client control word, bit [0] = "TUNE (1 when a
  TUNE TX operation is in progress)", for accessory hardware (added in V4.4).
- **Open-collector outputs.** High Priority byte 1401, bits [1]–[7].
- **Takeover.** Discovery reply byte 4: "Normally 0x02 but if the hardware is running and
  already connected to a different Host it will be 0x03." The note under it: if the user
  ignores the "in use" message "and proceeds to send appropriate C&C commands, then the
  hardware will disconnect from the existing connection and connect to the PC sending the C&C
  commands."
- **Status from the radio.** High Priority status packet (port 1025 by default): sent at
  50 ms normally and "every mS when transmitting", inputs "immediately the data changes".
  Byte 4 bit [0] = PTT, [1] = dot, [2] = dash ("the status of an attached PTT button or CW
  key"); bytes 14–15 forward power and 22–23 reverse power (Alex 0); byte 30 bit [2] DUC FIFO
  underflow; bytes 49–50 supply volts.
- **Memory-mapped registers.** Up to 240 pairs of 16-bit address and 32-bit data in each
  direction. From the hardware they are sent "whenever data changes and optionally
  periodically". P2 defines no address map and no read request; the default ports are "xxxx".

### What the public G7250 information says [G7250-MAN]

- TX power: SSB/CW/NFM 100 W ±1 dB, AM 25 W ±1 dB (13.8 V, max). No 50 MHz value in the
  manual; secondary sources give 90 W [G7250-PUDX], [G7250-RIGPIX].
- Transmit ranges: 1.8–2.0, 3.5–3.9, 7.0–7.2, 10.1–10.15, 14.0–14.35, 18.068–18.168,
  21.0–21.45, 24.89–24.99, 28.0–29.7 and 50.00–54.00 MHz; "set according to local regulatory
  requirements" per region.
- Supply: 13.8 V DC ±15 %; TX current 23 A max. Operating temperature 0 to +50 °C.
- ATU: short press [ATU] switches the tuner in; a long press starts tuning; "After tuning is
  complete, it automatically returns to receive status", so tuning transmits. Initial tuning
  ≤ 10 s, memory recall ≤ 0.1 s, data stored per band.
- SWR scan: an [APP] function on the controller ("SWR SCAN", with START and STOP). Measuring
  SWR needs a transmitted signal, so we assume it transmits; not stated in the manual.
- TX controls outside the network: microphone PTT (H-22) and KEY (Morse key, manual or
  keyer, with QSK) on the controller; SEND ("Transmit control signal", RCA), TUNER (13.8 V
  out, return, trigger) and ALC (output) on the main unit.

What the hardware actually allows (which sensors exist, which TX paths the firmware can
block, what happens at reset) is unknown and asked in HIS-06 to HIS-13 and HIS-17
(`open-questions-his.md`).

## Terms used below

- **Session.** Starts when a host sets RUN (High Priority byte 4 bit [0]) from 0 to 1 while
  the radio is not in a session. Ends when RUN is cleared, the P2 watchdog sends the radio to
  standby, another host takes over, or the radio resets.
- **Owner.** The host of the current session, identified by its source IP address and UDP
  port together (resolved item 4). A host that reopens its socket on a new port is a different
  host: its first C&C packet is a takeover (sub-decision 3), which unkeys and drops the arm.
- **Armed.** The owner has completed the arm handshake (sub-decision 1) and the radio has
  confirmed it. Only an armed radio can key.
- **Keyed.** The PA is transmitting, for any reason (PTT, CWX, KEY, ATU tuning).
- **TX request.** Anything that asks the radio to key: High Priority byte 4 bit [1], byte 5
  bit [0] (CWX), a KEY closure in hardware CW, an ATU tune command, a controller request.

## Sub-decision 1 — TX arm: register, value, confirmation

### Options considered

#### 1A. A single arm bit (write 1 to arm, 0 to disarm)

- For: simplest for host and firmware, and simple to test.
- Against: one flipped or mis-addressed write arms a 100 W transmitter. A host bug that
  writes a wrong address, a tool that writes test patterns, or a corrupted packet with a
  valid-looking sequence is enough.
- Against: a value written in an earlier session is as good as a new one. A host that
  restores "the last register state" after a restart would re-arm without the user asking.

#### 1B. A fixed magic value (for example a 32-bit constant)

- For: an accidental write of 1, 0xFFFFFFFF or a counter value does not arm. Still one write.
- Against: the value is the same in every session, so a stored or replayed register image
  still re-arms after a restart, a takeover or a reset.
- Against: once the constant is in a host's code, every path in that code that writes it
  arms; nothing ties the arm to the moment the user asked for it.

#### 1C. A per-session token from the radio, combined with a fixed constant (chosen)

The radio publishes a token in a read-only register. To arm, the host writes
`token XOR ARM_MAGIC` to the arm register. The token changes every time the arm is dropped and
at every new session, so a value from an earlier arm is never valid again.

- For: protects against random writes (as 1B) and against stale or replayed values (unlike
  1B): a host can only arm with a value it computed from what the radio sent in this
  session.
- For: a host that echoes registers back does not arm by accident: the token register is
  read-only, and the arm register needs a value that differs from the token.
- For: still one write after the token is known, and P2 already pushes register changes to
  the host ("whenever data changes" [P2]), so no read request has to be invented for it.
- Against: a little more host code. AetherSDR's G7250 backend (0016) must handle it.
- Against: it is not security. Anyone on the LAN who sees the token can arm; P2 has no
  authentication [P2]. The aim is to stop accidents, and the spec must say so.

#### 1D. An arm lease that must be refreshed

The arm expires unless the host rewrites it every N seconds.

- For: an arm cannot outlive a host that has lost track of it.
- Against: the P2 watchdog and the keyed timeout (sub-decision 2) already cover a host that
  stops talking. A host that keeps talking would keep refreshing, so the lease adds traffic
  without covering a new case.
- Against: one more timer that can expire in the middle of a transmission.

#### 1E. Two-phase request and challenge

The host writes an arm request, the radio answers with a challenge, the host writes the
challenge back.

- For: the challenge is fresh at the moment of arming.
- Against: one more round trip with the same protection as 1C, because the 1C token is
  already fresh per arm.

### Decision 1

Option 1C. The G7250 register map (0005) gets these registers (symbolic names; addresses,
the value of `ARM_MAGIC` and the bit layout go into the register-map table in spec part B):

| Register | Direction | Content |
|----------|-----------|---------|
| `TX_ARM_TOKEN` | radio → host, read-only | 32-bit token, never 0 and never 0xFFFFFFFF, different from the previous token. Pushed at session start and whenever it changes. |
| `TX_ARM` | host → radio | `token XOR ARM_MAGIC` arms; 0 disarms. Any other value is rejected. |
| `TX_ARM_STATE` | radio → host, read-only | state (disarmed / armed / inhibited), arm generation counter (+1 on every arm), last reject reason, last drop reason. Pushed on every change. |
| `TX_STATE` | radio → host, read-only | keyed or not, the source of the current TX (PTT, CWX, KEY, ATU), active inhibits. Pushed on every change. |

Rules:

1. **Preconditions.** An arm write is accepted only if all of these hold, otherwise it is
   rejected with a reason in `TX_ARM_STATE`: it comes from the owner; RUN is set; the
   watchdog is effectively on (sub-decision 2); the radio is not in fault (sub-decision 5);
   no limit inhibit is active (sub-decision 4); High Priority byte 4 bit [1] is 0 at that
   moment; level 1 is the active level (0011); no firmware update is in progress (0008); a TX
   mode class has been declared in `TX_MODE_CLASS` for this session (sub-decision 4, rule 3;
   reject reason `NO_MODE_CLASS`).
2. **Confirmation.** The arm takes effect when the radio pushes `TX_ARM_STATE` = armed with a
   new generation number. The host must wait for it. P2 does not order memory-mapped and High
   Priority packets [P2], so: **after arming, the radio keys only on a 0→1 edge of a TX
   request that arrives after the confirmation.** A PTT bit that was already 1 does not key.
3. **Token.** It need not be unpredictable (this is not security); it must differ from the
   previous one. How it is generated depends on the processor (HIS-18).
4. **Every TX request needs the arm.** PTT (byte 4 bit [1]), CWX (byte 5 bit [0]), hardware CW
   from KEY, ATU tuning and any controller request (sub-decision 6). Bits [2]–[7] of byte 4
   (PTT1–PTT3 in the table, reserved in the text [P2]) never key the G7250; it has one
   transmitter [G7250-MAN].
5. **Events that drop the arm.** Each drop unkeys first, then disarms, then issues a new token
   and pushes `TX_ARM_STATE` with the reason. The complete list:

| # | Event | Reason code (symbolic) |
|---|-------|------------------------|
| 1 | Owner writes 0 to `TX_ARM` | `HOST_DISARM` |
| 2 | RUN cleared (High Priority byte 4 bit [0] = 0) — this is P2's "stop" | `RUN_CLEARED` |
| 3 | P2 watchdog: no C&C packet from the owner for 1 s (sub-decision 2) | `WATCHDOG` |
| 4 | Takeover: C&C from another host, including the owner's IP address on a different UDP port (sub-decision 3) | `TAKEOVER` |
| 5 | Any reset: power-on, brown-out, processor watchdog, software reset (HIS-13) | (state after reset: disarmed; logged, 0008) |
| 6 | Entry into the fault state (sub-decision 5) | `FAULT` |
| 7 | A limit trip whose action is DISARM or FAULT (sub-decision 4). Maximum continuous TX time is not one of them: its action is UNKEY, arm kept (Resolved 3, ON8ST 2026-11-19) | `LIMIT_<name>` |
| 8 | Ethernet link down, if the CH394Q reports PHY link status (to be checked in [CH394]; HIS-14) | `LINK_DOWN` |
| 9 | Loss of the socket or port set-up that the session uses (for example the General packet moves the High Priority or DUC ports) | `SESSION_CHANGED` |
| 10 | Change of active level (0011) | `LEVEL_CHANGE` |
| 11 | Start of a firmware update or of a configuration change of built-in limits (0008; P2 program packets on port 1024 [P2]) | `MAINTENANCE` |
| 12 | A new Discovery from the owner while armed (P2's restart path starts with a Discovery [P2]) | `REDISCOVERY` |
| 13 | A TX path that must be blocked is found not blocked (sub-decision 6) | `FAULT` (via 6) |

   Not on the list, on purpose: the keyed timeout and TX IQ underrun (sub-decision 2),
   maximum continuous TX time and other UNKEY-level limit trips end the current transmission
   but keep the arm; changes of
   frequency, antenna, filters or drive while not keyed.

## Sub-decision 2 — Watchdog

### 2.1 Base timeout

The G7250 adopts P2's rule as written: in RUN, if no C&C packet from the owner arrives for
1 s, the radio goes to standby, unkeys, drops the arm (`WATCHDOG`) and releases SEND and the
TUNER trigger, P2's "PTT output" (sub-decision 6). RX streams stop, as in P2 standby. C&C
packets are the four "Control Elements" packets (General, DDC-specific, DUC-specific, High
Priority) [P2]. Packets from other hosts do not feed the watchdog. No real alternative was
considered: this is the standard and 0016 chose P2 partly for it.

Memory-mapped register packets do not feed the watchdog, because P2 does not head them
"Control Elements" [P2] (accepted, ON8ST, 2026-11-19).

### 2.2 A shorter timeout while keyed?

#### 2A. 1 s in all states

- For: pure P2; nothing new for hosts.
- Against: 1 s of unintended carrier at 100 W after a host crash, and a host whose network
  thread keeps sending General packets while its TX logic has hung keeps the radio keyed
  indefinitely (until maximum TX time).

#### 2B. A fixed shorter timeout while keyed, on any C&C packet

- For: less carrier after host loss.
- Against: still fed by any C&C packet, so the "network thread alive, TX logic dead" case
  remains.

#### 2C. A keyed timeout on the High Priority packet, with a host duty to refresh it (chosen)

While keyed, the owner must send a High Priority packet at least every 100 ms (P2's
recommended interval [P2]); if none arrives for `KEYED_TIMEOUT`, the radio unkeys.

- For: the High Priority packet carries PTT [P2], so its refresh means "the host still wants
  to transmit", not just "the host is alive".
- For: only G7250-aware hosts can key (0015), so a new host duty bothers no generic host.
- For: P2 already allows High Priority to be "sent periodically" [P2]; the duty uses that,
  not a new packet.
- Against: a deviation from P2 that must be in the annex "Differences from standard P2".
- Against: on a bad network (Wi-Fi bridge) short gaps unkey the radio. That is why the action
  is UNKEY, not DISARM: the host sends a new PTT edge and continues.

#### 2D. TX IQ stream as the keep-alive

Unkey if DUC I&Q (port 1029) stops while keyed.

- For: covers a host whose DSP has stopped.
- Against: CW is generated in the radio and needs no TX IQ [P2], so it cannot be the only
  rule. Useful as an extra check, not as the watchdog.

### Decision 2

- Base watchdog 1 s as P2 (2.1).
- Option 2C, plus 2D as an extra check for non-CW TX:
  - While keyed, the owner sends a High Priority packet at least every 100 ms (P2's
    recommended rate [P2]). `KEYED_TIMEOUT` register: default 500 ms (ON8ST, 2026-11-19);
    if no High Priority packet from the owner arrives within it, the radio unkeys. The host
    may write a shorter value, floor 100 ms; it cannot write a longer value than the default
    (0011). Action: UNKEY, reason in `TX_STATE`; arm kept.
  - TX IQ underrun: when keyed in a non-CW TX, a DUC FIFO underflow (reported in High Priority
    status byte 30 bit [2] [P2]) that lasts longer than TBD ms unkeys. The value depends on
    the DUC FIFO size (HIS-18).

### 2.3 The P2 hardware-timer bit (General byte 38 bit [0])

0015 already decided that the bit cannot disable the watchdog while armed. Open: what it does
when not armed.

#### 2E. Ignore the bit always; the watchdog is always on

- For: simplest and safest. One behaviour to test.
- Against: departs from P2 also where it costs nothing in safety: an unarmed radio cannot
  key.
- Against: RX-only debugging tools (and our own testbench) lose a P2 feature.

#### 2F. Honour the bit when not armed; force it on while armed; arming needs the bit set (chosen)

The radio stores what the host last wrote. The effective timer is `written OR armed`. An arm
request with the bit clear is rejected (`WATCHDOG_DISABLED`).

- For: standard P2 behaviour for any session that cannot transmit; the deviation is limited
  to the armed state, as 0015 asked.
- For: a host cannot arm and then switch the timer off: the clear is ignored while armed and
  takes effect again after disarm.
- For: the "rejected" reason makes host bugs visible: a G7250 host that forgot byte 38 learns
  it at the first arm, not after a network failure.
- Against: an unarmed session with the timer off holds the radio "in use" after its host has
  gone (discovery byte 4 = 0x03 [P2]) and keeps sending RX IQ to it. Not a TX risk; the next
  host takes over (sub-decision 3).
- Against: two behaviours to test instead of one.

#### 2G. Honour the bit fully, also while armed (pure P2)

- Rejected by 0015.

### Decision 2.3

Option 2F. `WATCHDOG_STATE` (radio → host, read-only) reports the value the host wrote and the
effective state. Before any General packet the timer counts as enabled.

## Sub-decision 3 — Takeover by a second host

P2 lets a second host take over a running radio by sending C&C [P2]. 0011 says only one owner,
and only the owner transmits. 0015 says a takeover never carries the arm.

### Options considered

#### 3A. Refuse takeover while armed; allow it when not armed

Packets from other hosts are ignored while the owner is armed; the discovery reply says 0x03.

- For: an armed operator is never interrupted by another PC on the LAN starting SDR software
  by mistake.
- For: the owner of a transmission stays clearly identified until it disarms.
- Against: it removes a way to stop a runaway transmission from another machine. If the
  owning host hangs but keeps its network thread alive, only the keyed timeout, the limits,
  maximum TX time or power can stop it.
- Against: a deviation from P2 that a generic host cannot see: it believes it took over and
  gets nothing. P2 has no "refused" reply [P2].

#### 3B. Allow takeover at any time; it always unkeys and drops the arm (chosen)

On the first C&C packet from a host that is not the owner, the radio unkeys, drops the arm
(`TAKEOVER`), issues a new token, sends a last `TX_ARM_STATE` to the old owner, and only then
processes the new host's packet. The new owner starts unarmed and must arm itself.

- For: closest to P2: takeover works as documented; the only deviation is the one 0015
  already made (the arm does not move).
- For: any machine on the LAN can stop a transmission. A second host becomes an emergency
  stop, which a safety core should welcome.
- For: single owner (0011) still holds: there is never more than one owner, and only an armed
  owner transmits.
- Against: an accidental takeover breaks a QSO. P2 asks the host to warn the user first
  (discovery byte 4 = 0x03 [P2]); the G7250 depends on hosts doing that.
- Against: on a network with an aggressive auto-connecting host the operator may lose the
  radio repeatedly. Mitigation is a host matter, or a later option (resolved item 5).

#### 3C. Refuse takeover always

Another host can only get the radio after the session has ended (RUN cleared or watchdog).

- For: strictest single owner.
- Against: a host that has hung with its timer off (allowed when unarmed, 2F) holds the radio
  until power-off.
- Against: the largest deviation from P2, and no emergency stop from another machine.

#### 3D. Require explicit release by the owner

The owner must write a release register before another host can take over.

- For: no surprises for the owner.
- Against: same dead-host problem as 3C. Needs a new handshake no P2 host knows.

### Decision 3

Option 3B. Takeover is allowed at any time, never carries the arm, and always unkeys before the
new host is served. The discovery reply reports 0x03 while a session is active [P2]. Listed as
a deviation in the annex (only the arm part deviates). Since the owner is IP address and UDP
port, a host that reopens its socket on a new port takes over from itself: unkey and disarm.
Accepted risk (ON8ST, 2026-11-19): an accidental takeover by an auto-connecting host may break
a transmission; hosts should warn before taking over a radio that reports 0x03 [P2].

## Sub-decision 4 — TX limits

### Options considered

#### 4A. Fixed limits in firmware, no network interface

- For: nothing a host can get wrong.
- Against: a level cannot tighten limits, which 0011 allows; no way to report which limit
  tripped.

#### 4B. A limit table with built-in values, per-session tightening, actions and recovery (chosen)

Each limit has a built-in value (from the HIS and the manual), an action and a recovery rule.
The owner may write a stricter value for its session.

- For: matches 0011 (stricter, never looser) and makes every trip visible.
- For: a reference model in g7250-testbench can test each row (0001 item 5).
- Against: more registers and more tests.

#### 4C. All limits host-configurable

- Rejected by 0011: a host could loosen them.

#### 4D. Rely on hardware fold-back only

- For: if the PA has SWR and temperature fold-back (HIS-12), it works without firmware.
- Against: unknown whether it exists; it does not cover TX time, band edges or the AM limit;
  nothing is reported on the network. Hardware fold-back, if any, sits below 4B, not instead
  of it.

### Decision 4

Option 4B.

**Actions**, in increasing order:

- `WARN` — flag in `TX_STATE`, no effect on TX.
- `REDUCE` — the radio lowers drive below the host's drive level (High Priority byte 345 [P2])
  until the value is back inside the limit; TX continues.
- `UNKEY` — ends the current transmission; a new 0→1 TX request is needed; arm kept.
- `DISARM` — unkey and drop the arm.
- `FAULT` — unkey, drop the arm, enter the fault state (sub-decision 5).

**Limits.** All numbers are TBD unless a public source gives them; hardware-dependent values
carry the HIS id.

| Limit | Measured by | Threshold(s) | Action | Recovery |
|-------|-------------|--------------|--------|----------|
| TX frequency | DUC0 frequency (High Priority bytes 329–332 [P2]) | outside the transmit ranges of [G7250-MAN] for the configured region | TX request ignored (no key) | inside a range again |
| SWR | forward and reflected power (HIS-11) | above S1: `REDUCE`; above S2: `UNKEY`; only evaluated above a minimum forward power. S1, S2, minimum TBD (HIS-11, HIS-12) | as listed | `UNKEY`: next TX request; N trips in T s → `FAULT` (N, T TBD) |
| PA temperature | PA sensor (HIS-11) | T1 `WARN`, T2 `REDUCE`, T3 `UNKEY` with inhibit, T4 `FAULT`; all TBD (HIS-11, HIS-12) | as listed | inhibit lifts below T3 minus hysteresis (TBD) |
| Forward power | forward power (HIS-11) vs band and TX mode class | built-in maxima: 100 W SSB/CW/NFM, 25 W AM [G7250-MAN]; 50 MHz TBD (90 W in [G7250-PUDX], [G7250-RIGPIX]; HIS-12); margin TBD | `REDUCE`; if still over after TBD ms, `UNKEY` | next TX request |
| Supply voltage | supply sensor (HIS-11) | outside 13.8 V ±15 % (11.73–15.87 V) per [G7250-MAN] as starting values; final values HIS-11, HIS-12 | under-voltage while keyed: `REDUCE`, below a lower value `UNKEY`; over-voltage: `UNKEY` with inhibit | inside range for TBD s |
| Supply / PA current | current sensor, if any (HIS-11) | above 23 A (TX max in [G7250-MAN]); final value HIS-12 | `UNKEY` | next TX request |
| Maximum continuous TX time | firmware timer, any TX source | 5 min built-in default (ON8ST, 2026-11-19); host or owner may set it stricter, never looser; to be checked against the thermal rating (HIS-12) | `UNKEY` (arm kept) | next TX request |
| ATU tune time | firmware timer | above initial tuning time ≤ 10 s [G7250-MAN] plus margin, TBD (HIS-08) | `UNKEY`, tune reported as failed | next tune command |
| Sensor plausibility | all of the above | sensor missing, stuck or out of range (HIS-11) | `FAULT` | sub-decision 5 |
| RF while not keyed | forward power (HIS-11) | above TBD with no TX active | `FAULT` | sub-decision 5 |

Rules:

1. **Tighten only.** Each limit that a host may change has a `LIMIT_<name>` register. A write
   is accepted only if it is equal to or stricter than the built-in value; a looser write is
   rejected (not clamped) and reported. Built-in values are not writable over P2; whether the
   management channel may change them is for 0008, and never beyond the hardware rating
   (HIS-12).
2. **Per session.** Tightened values return to the built-in values when the session ends.
   Persistent tightening belongs to the management channel configuration (0008).
3. **TX mode class.** On level 1 the DSP is in the host (0011), so the radio does not know
   whether the host sends AM or SSB, except CW selected in DUC-specific byte 5 bit [1] [P2].
   The host must declare the class in `TX_MODE_CLASS` before arming: an arm attempt without a
   declared class is refused (`NO_MODE_CLASS`, sub-decision 1 rule 1). The host must update
   the class whenever its TX mode changes. The AM limit (25 W [G7250-MAN]) applies whenever
   the declared class is AM. The power measurement still applies whatever the host declares.
   Rejected option (ON8ST, 2026-11-19): no class declared means the strictest class (AM,
   25 W) applies; rejected because a silent default hides a missing declaration, while a
   refused arm makes it visible at once.
4. **Drive mapping.** How the P2 drive level 0–255 (byte 345 [P2]) maps to power is for spec
   part B and HIS-12; `REDUCE` acts on the radio side, so the host's value is not changed.
5. All limits apply on both levels (0011). ATU tuning uses its own SWR and power profile,
   because high SWR is expected while tuning (HIS-08, HIS-12).

## Sub-decision 5 — Fault state

### Options for clearing a fault

#### 5A. Clear automatically when the condition is gone

- For: no host action.
- Against: an intermittent fault (loose connector, failing sensor) toggles the radio in and
  out of fault without anyone noticing.

#### 5B. Clear by the host, only when the condition is gone

- For: a person or host acknowledges every fault.
- Against: some faults (RF while not keyed, a TX path that cannot be blocked) mean the
  hardware is not under control; a host clearing them makes no sense.

#### 5C. Clear only by power cycle

- For: strictest.
- Against: a temperature or supply fault on a remote radio needs someone at the radio.

#### 5D. Two classes: host-clearable and latched until reset (chosen)

- Class 1, host-clearable: limit faults with a measurable condition (temperature T4, repeated
  SWR trips, supply). Cleared by the owner writing the current fault code to `FAULT_CLEAR`,
  accepted only if the condition is gone.
- Class 2, latched until reset: sensor failure, RF while not keyed, a TX path not blocked,
  internal consistency errors. Cleared only by a reset (power cycle, or a reset over the
  management channel, 0008).
- For: remote recovery where it is safe, a person at the radio where it is not.
- Against: two classes to specify and test.

### Decision 5

Option 5D, with:

- **Entry.** Any `FAULT` action in sub-decision 4, N repeated trips (sub-decision 4), item 13
  of the drop list, a watchdog-reset of the processor seen at start-up (HIS-13), or an
  internal error.
- **Effect.** Unkey, drop the arm (`FAULT`), release SEND and the TUNER trigger, refuse arm
  requests. RX continues, so the host can still see the radio and the fault.
- **Reporting.** `SAFETY_STATE` (normal / fault), `FAULT_CODE` (first cause), `FAULT_FLAGS`
  (latched bitmask of all causes since the last clear), `FAULT_CLASS`, a trip counter; all
  pushed on change in the memory-mapped packet to the host [P2] and logged (0008). The P2
  High Priority status stays standard (0005): forward/reverse power and supply in their usual
  bytes [P2].
- **Clearing.** As 5D. A clear does not re-arm.
- **State after power-on or any reset** (before the network stack starts, and again at every
  session end):
  - PA off and its bias off, TX path disabled, SEND and TUNER trigger released (HIS-09,
    HIS-10, HIS-13);
  - not armed, new token, built-in limits, watchdog counted as enabled;
  - ATU not tuning; ATU in or out as stored per band, or out until the HIS says otherwise
    (HIS-08);
  - antenna: a defined default, TBD (HIS-06);
  - filters for the default RX frequency, preamplifier off, attenuation TBD (HIS-07);
  - what the hardware does between reset and the moment the firmware drives these pins
    (whether the PA can key from floating lines) is HIS-13. If it can, it is a hardware
    finding, and M4 waits for a mitigation.
  - A class 2 fault is not kept across a reset in flash, so the radio cannot brick itself; it
    is logged (0008) and the self-check at start-up detects a persistent cause again.

## Sub-decision 6 — Other TX paths

The arm only works if the firmware is the only path to the PA or can block every other path
(HIS-10). The P2 model is that the radio reports local PTT and key inputs in the status packet
(byte 4 bits [0]–[2] [P2]) and the host decides, except hardware CW from the key [P2].

### Options considered

#### 6A. Local inputs key the radio directly, as on the stock radio

- For: the controller keeps working as a radio head.
- Against: TX without the network owner and without arm, against 0011 and 0015.

#### 6B. Local inputs are reported, never key by themselves; the owner decides (chosen)

- For: one TX authority, the armed owner; matches the P2 status model.
- For: mic PTT on the controller still works with a host that keys on the reported PTT bit.
- Against: if the controller has a path to the PA that the firmware cannot block (HIS-10,
  HIS-17), this option cannot be built as stated.
- Against: no standalone use of the controller as a radio while this firmware runs (resolved
  item 6: accepted for level 1, revisit for level 2).

#### 6C. Local inputs key only when no network session exists

- For: standalone use without a PC.
- Against: the main unit has no audio and no DSP path on level 1 (0017, 0011), so a
  standalone SSB transmission needs level 2; out of scope before M6. A second TX authority
  also needs its own arm and limit rules.

### Decision 6

Option 6B, with per-path rules. On level 1 the controller has no standalone operation:
its inputs are reported and never key the radio (accepted, ON8ST, 2026-11-19; revisit for
level 2). All depend on HIS-10 and HIS-17; if a path cannot be blocked, M4 is blocked for that
path until ON8ST decides.

| Path | Rule |
|------|------|
| Controller mic PTT | Reported in High Priority status byte 4 bit [0] [P2], if the controller passes it to the main unit (HIS-17). Never keys by itself. |
| KEY (Morse) | Reported as dot/dash, byte 4 bits [1]–[2] [P2]. Keys hardware CW only when armed, CW selected by the owner (DUC-specific byte 5 bit [1] [P2]), and all limits pass; break-in, hang and RF delays as P2 (DUC-specific bytes 5, 11–13). Depends on HIS-17. |
| Host CWX | High Priority byte 5 [P2]; a TX request under the arm, as PTT. |
| SEND output | Follows the actual keyed state: asserted only while armed and keyed, before RF (RF delay, DUC-specific byte 13 [P2]) and released after RF. Released on every drop event, on standby (P2 "PTT output" [P2]) and in fault. Whether firmware controls SEND, and its direction, is HIS-09. |
| TUNER (external tuner trigger) | Under the arm, as ATU tuning. HIS-09. |
| Internal ATU tuning | Transmits [G7250-MAN], so it is a TX request: needs arm, owner, frequency inside a range, limits, and its own tune profile and time limit (sub-decision 4). Started by a G7250 register (`ATU_TUNE`, 0005, HIS-08); tune power TBD (HIS-08, HIS-12). |
| P2 TUNE bit (High Priority bytes 1396–1397 bit [0]) | Accepted as information that the host is sending a tune carrier [P2]. It does not start the internal ATU: the meaning is not identical (0005). |
| Controller ATU key, SWR scan, other controller TX functions | Refused while level 1 firmware runs, unless they reach the main unit as reportable requests (HIS-17). A controller that keys on its own is a finding for HIS-10. |
| Open-collector outputs (High Priority byte 1401 [P2]) | No such outputs are documented [G7250-MAN]; ignored, to be listed in the P2 field table. |

## Decision (summary)

1. TX arm by per-session token: write `TX_ARM_TOKEN XOR ARM_MAGIC` to `TX_ARM`; confirmed by
   `TX_ARM_STATE`; keying only on a TX-request edge after the confirmation; 13 drop events.
2. P2 1 s watchdog as written; while keyed, a High Priority refresh duty (at least every
   100 ms) with a 500 ms `KEYED_TIMEOUT` (UNKEY, arm kept), and a TX IQ underrun check.
   Memory-mapped packets do not feed the watchdog. General byte 38 bit [0] is
   honoured when not armed, forced on while armed, and must be set to arm.
3. Takeover is allowed at any time, always unkeys and drops the arm first. The owner is IP
   address and UDP port; a new port is a takeover.
4. Limit table with built-in values, actions WARN/REDUCE/UNKEY/DISARM/FAULT and recovery;
   hosts may only tighten, per session. Maximum continuous TX time 5 min, UNKEY only. Arming
   requires a declared TX mode class.
5. Fault state in two classes (host-clearable, latched until reset); safe state after any
   reset.
6. Local TX paths are reported, never key by themselves; SEND, TUNER and ATU tuning are under
   the arm.

## Consequences

- Spec part A (common, 0011) gets the safety behaviour: drop list, limit table, fault state,
  state after reset. Spec part B gets the registers in the G7250 register map (0005):
  `TX_ARM`, `TX_ARM_TOKEN`, `TX_ARM_STATE`, `TX_STATE`, `TX_MODE_CLASS`, `KEYED_TIMEOUT`,
  `WATCHDOG_STATE`, `LIMIT_<name>`, `SAFETY_STATE`, `FAULT_CODE`, `FAULT_FLAGS`,
  `FAULT_CLASS`, `FAULT_CLEAR`, `ATU_TUNE`, plus `ARM_MAGIC` and the reason codes.
- Annex "Differences from standard P2": arm needed for every TX request; byte 38 forced on
  while armed and required for arming; keyed timeout and the High Priority refresh duty;
  takeover drops the arm; PTT1–PTT3 ignored; TUNE bit does not tune; open-collector outputs
  ignored.
- Annex "Changes needed in AetherSDR": arm handshake with token, wait for confirmation, High
  Priority every ≤ 100 ms while keyed, byte 38 bit [0] set, `TX_MODE_CLASS` declared before
  arming and updated on every mode change, keep one UDP socket and port per session, show arm state,
  fault and drop reasons, warn before takeover (P2 note on byte 4 [P2]).
- g7250-testbench: one conformance test per drop event, per limit row, per fault class, and
  for the reset state (M3 exit criterion).
- 0006 (telemetry) must give sensor rates that are fast enough for these limits; P2 gives 1 ms
  status during TX [P2], HIS-11 gives the sensor side.
- 0008 (management channel): logging of drops and faults, reset command, persistent
  tightening of limits, firmware update as a drop event.
- M3 cannot be closed without answers to HIS-10, HIS-11 and HIS-13; M4 not without HIS-12 and
  HIS-17 as well.
- HIS questions extended: HIS-09 direction of SEND; HIS-10 whether the controller can key
  the PA on its own; HIS-11 a plausibility check per sensor; HIS-14 whether the CH394Q reports
  link status. These were added to `open-questions-his.md` by the coordinator.

## Resolved (ON8ST, 2026-11-19)

1. **TX arm and takeover.** Takeover is always allowed; every takeover unkeys and drops the
   arm (option 3B as drafted).
2. **Keyed timeout.** `KEYED_TIMEOUT` = 500 ms, not the proposed 300 ms. While keyed the host
   sends a High Priority packet at least every 100 ms (recommended rate [P2]); if none
   arrives within 500 ms the radio unkeys and keeps the arm.
3. **Maximum continuous TX time.** Default 5 minutes. Reaching it unkeys only; the arm stays
   (changed from the draft, which had `DISARM`). A host or the owner may set it stricter,
   never looser.
4. **Owner identity.** IP address and UDP port. A host that reopens its socket on a new port
   counts as a takeover (unkey and disarm).
5. **Accidental takeover.** Accepted: an auto-connecting host may break a transmission; hosts
   should warn before taking over (discovery byte 4 = 0x03 [P2]). No radio-side mitigation
   on level 1.
6. **Standalone controller.** No standalone operation from the controller on level 1:
   controller inputs are reported and never key the radio. Revisit for level 2.
7. **TX mode class.** Arming requires a declared class; an arm without one is refused
   (`NO_MODE_CLASS`); the host updates the class when the mode changes; the 25 W AM limit
   applies whenever the declared class is AM. "No class means AM limit" is rejected.
8. **Watchdog feed.** Memory-mapped register packets do not count for the watchdog.
9. **Class-2 faults.** Not stored across a reset; the start-up self-check detects a
   persistent cause again, and the fault is logged (0008).
10. **Manual revision.** Settled: the file name says rev0.1, the title page says Rev.1.01;
    both refer to the same document [G7250-MAN].
11. **PTT1–PTT3 vs reserved.** P2 High Priority byte 4 lists PTT1–PTT3 in the byte table but
    calls bits [2]–[7] reserved in the text [P2]. This inconsistency is to be noted as a
    clarification in spec Annex X2; the G7250 ignores these bits either way (sub-decision 1,
    rule 4).

Still open: the TBD values in the limit table and the TX IQ underrun time (HIS-08, HIS-11,
HIS-12, HIS-18); the register addresses, `ARM_MAGIC` value and bit layouts (spec part B).

## Sources

- Discussion with ON8ST, 2026-11-19 (0015, 0011); decisions by ON8ST, 2026-11-19 (section
  "Resolved").
- Decisions 0001 (spec section 9), 0005, 0006 (reserved), 0008 (reserved), 0011, 0012, 0015,
  0016, 0017.
- `open-questions-his.md`: HIS-06 to HIS-14, HIS-17, HIS-18.
- [P2] openHPSDR Ethernet Protocol V4.4: "Detailed operation" (watchdog, standby, restart,
  hardware CW, disabling the timer); General packet byte 38; DUC-specific packet bytes 5,
  11–13; High Priority packet bytes 4, 5, 329–332, 345, 1396–1397, 1401; memory-mapped
  register packets; discovery reply byte 4 and the note on connecting to running hardware;
  High Priority status packet bytes 4, 14–15, 22–23, 30, 49–50 and its update rates;
  revision history V2.7.
- [G7250-MAN] Xiegu G7250 Operation Manual: specifications (TX power, transmit ranges,
  supply, current, temperature), ATU section and ATU parameters, SWR scan, interface
  definitions (microphone, KEY, SEND, TUNER, ALC). File name rev0.1, title page "Rev.1.01"
  (settled, resolved item 10).
- [G7250-PUDX], [G7250-RIGPIX] for the 50 MHz power (see `sources.md`).
- [CH394] WCH CH394 manual 1, V1.2 (link status not yet checked).

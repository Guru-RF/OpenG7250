# 0022 — rc1 review fixes (network interface, parts A and B)

- Status: proposed (for ON8ST review at rc1), 2026-11-19
- Date: 2026-11-19
- Applies to: `spec/network-interface.md` draft 4 (rc1 candidate), parts A and B, and the
  annexes X1–X3.
- Builds on: 0003, 0004, 0005, 0006, 0007, 0008 (accepted), 0011, 0015, 0017, 0020 and 0021
  (proposed). Where this decision reads an accepted decision more narrowly or adds to it, the
  section says so.

## Context

An independent review of draft 3 and a byte-by-byte check against [P2] V4.4 found gaps in
the safety behaviour (changes while keyed, takeover, fault classes, limit tiers), in the
management channel, and a number of small inconsistencies. This decision records one choice
per finding. The spec cites the sections as "0022 §n". Priorities: safety first; stay close
to [P2] and to the accepted decisions 0003–0008, 0015, 0017 and to 0020, 0021.

Sources used throughout: [P2] openHPSDR Ethernet Protocol V4.4 (page numbers are those of
the page footers "Page | N"); [CH394] WCH CH394 manual 1, V1.2; [G7250-MAN]; decisions listed
above. Values that depend on the hardware stay "TBD" with their HIS id.

---

## 1. TX frequency change while keyed (review H1)

**Problem.** Draft 3 checks the TX range only when a TX request arrives (Table A3-2, "TX
request ignored"). A host that moves DUC0 (High Priority bytes 329–332 [P2]) while keyed could
leave a transmit range, or need another low-pass filter or band relay, under RF. 0007
(Decision 1 rule 5) calls frequency changes harmless only "while not keyed".

**Chosen rule.** A safety-core rule, the same on every level:

1. While keyed, the G7250 evaluates every new DUC0 frequency before it is applied.
2. If the new frequency lies outside the transmit ranges in force, or needs another TX filter,
   band or relay state than the one in use, the G7250 MUST unkey first (`UNKEY`, arm kept,
   `TX_STATE` unkey reason 6 "retune needs RF-path change", limit id `LIMIT_TX_FREQ` when the
   cause is the range), then apply the frequency and switch the relays while unkeyed. A new
   0→1 TX request is needed to key again.
3. A retune that stays inside the same transmit range and needs no change of filter, band or
   relay state is followed while keyed, without unkey (small retunes, for example a CW or
   SSB tuning step).
4. Which frequencies share one RF-path state is the filter plan of the hardware: TBD
   (HIS-07). Until the HIS gives it, every `tx_band` entry of the capability record counts as
   its own state, so any move from one `tx_band` entry to another, or out of all of them,
   unkeys.

- Alternative A: refuse (ignore) the frequency change while keyed and keep transmitting on
  the old frequency. For: the transmission is not broken. Against: the host believes it moved;
  the RF frequency no longer matches what the host displays and modulates; [P2] has no refusal
  for High Priority fields.
- Alternative B: unkey on every DUC0 change while keyed. For: simplest. Against: breaks normal
  tuning during CW and SSB, which needs no relay change.

**Reason.** Relays are never switched under RF, and no RF leaves a transmit range, whatever
the host does; small retunes keep working as on any transceiver.

## 2. RF-path relays while keyed (review H2)

**Problem.** Antenna, ATU in/out, filters and preamplifier/attenuator can be changed through
P2 fields (High Priority bytes 1428–1435 and 1443, DUC-specific byte 59 [P2]), G7250
registers, the controller head's ANT and ATU buttons [G7250-MAN], TCI commands (0021 §8) and
management. Draft 3 does not say what happens while keyed.

**Chosen rule.** RF-path relays (antenna, ATU in/out, TX and RX filters, preamplifier and
attenuator relays) MUST NOT change while keyed, whatever the source. The rule depends on the
kind of request:

- **State fields that the host resends** (P2 High Priority and DUC-specific fields): the
  change is **deferred**: the latest requested value is stored and applied right after the
  unkey, before any new key.
- **Commands** (G7250 register writes, TCI commands as 0021 §8 already says, controller ANT
  and ATU buttons if they reach the main unit, HIS-17): the change is **refused**: a register
  write is answered with the value in force and `WRITE_STATUS` reason `KEYED`; a controller
  button press is ignored and logged.
- **Management** never switches a relay; commands that end TX (§8) unkey first.
- The only relay movement while RF is present is internal ATU tuning, inside its own tune
  profile (0007 Decision 4 rule 5).
- If the controller switches relays on its own, without the main unit, that is a finding for
  HIS-10 and HIS-17.

- Alternative A: refuse everything while keyed. For: one rule. Against: a P2 host resends its
  state every 100 ms; a refused field would come back as a change at the next packet anyway,
  and the host has no way to learn of a refusal.
- Alternative B: defer everything, including commands. For: one rule. Against: a TCI client
  or register writer expects an answer now; 0021 §8 already chose refusal for TCI.

**Reason.** No hot switching from any source; each protocol keeps its own semantics.

## 3. Takeover as a state machine (review H3)

**Problem.** A2.3, A2.4, B2.4, B4.5 and B5.7 describe takeover in pieces and partly
disagree (B4.5: "only the run bit makes a host the owner"). What happens to RUN, streams,
sequence counters, session limits and `TX_MODE_CLASS` is not stated.

**Chosen rule.** A takeover is the first C&C packet (General, DDC-specific, DUC-specific or
High Priority) from a host that is not the owner while a level-1 session runs. In this order:

1. The old session ends with the actions of A3.2 in their order: unkey, disarm (`TAKEOVER`),
   new token, last `TX_ARM_STATE` to the old owner. Then the TX-side state of A3.6 applies:
   PA off, SEND and TUNER released, ATU tuning aborted, session limits back to the
   persistent values (§6), `TX_MODE_CLASS` = 0, `KEYED_TIMEOUT` = 500 ms, hardware-timer
   value "no General packet yet". Nothing more is sent to the old owner.
2. The new host becomes the owner at once, and its session starts at once. RUN stays set (the
   radio stays in the RUN state, as [P2] "takeover by the PC sending the C&C commands"
   implies), so the new owner's watchdog runs from this packet.
3. Every stream of the session (B2.4) goes to the new owner's source IP address and port from
   the next packet on; all outgoing sequence counters restart at 0, as on a stop (B2.7).
4. RX-side settings (DDC0 frequency, rate and enable; front end) are kept until the new owner
   writes them, so RX does not stop. The capability record is sent once, unasked, at the new
   owner's first General packet (B4.4).
5. Then the takeover packet itself is processed.
6. **Ping-pong.** Two hosts that both send C&C take the radio from each other at every packet.
   Each takeover unkeys and disarms, so neither can transmit; RX goes to whichever sent last.
   The G7250 does not prevent it (0007 Resolved 5). It counts takeovers (`GET_STATS`) and
   logs them, coalescing repeated takeovers between the same two hosts into at most one log
   entry per second with a count, so the log is not flooded.

A memory-mapped packet, including a `CAP_REQUEST`, is never C&C and never a takeover (B4.5).
Ownership starts either with the run bit while no session runs (A2.3) or with a takeover.

- Alternative A: on takeover, clear RUN and wait for the new host's run bit. For: a clean
  start. Against: RX stops for a host that, following [P2], expects the running radio to
  serve it; a takeover by a General packet would leave an owner without a session.
- Alternative B: keep the old session's TX settings (limits, mode class). Against: a new
  host would inherit limits and a declared class it never set; 0007 Decision 3 says the new
  owner starts unarmed, and the same applies to everything that feeds the arm.

**Reason.** Closest to [P2] (the radio keeps running, the new host is served) with nothing
TX-related carried over.

## 4. DUC I&Q from a host that is not the owner (review H5)

**Problem.** Draft 3 does not say whose DUC I&Q (port 1029) the G7250 accepts. Any host on
the LAN could fill the TX FIFO of an armed owner.

**Chosen rule.** A DUC I&Q packet whose source IP address and UDP port are not the owner's
(A2.2), or that arrives while there is no session, MUST be discarded whole, MUST NOT enter
the DUC FIFO and MUST have no other effect (B11.1). It is counted per source in `GET_STATS`.
Hence a host MUST send DUC I&Q from its session socket. This is a deviation (Annex X1, D24).

- Alternative A: accept DUC I&Q from the owner's IP address on any port. For: hosts that use
  a separate TX socket keep working. Against: owner identity is IP address and port (0007
  Resolved 4); a second program on the same PC could inject TX audio.
- Alternative B: accept from anyone, as [P2] does not restrict it. Against: injection of TX
  signal into another host's transmission.

**Reason.** One owner identity for everything that reaches the PA. AetherSDR already uses
one socket per session (`spec/annex-aethersdr.md`, "Socket model").

## 5. Fault classes per code (review H6)

**Problem.** Draft 3 gives classes only in words, `FAULT_CLASS` is undefined when several
causes are flagged, the class of codes 17–19 is not stated, "N repeated trips" has no N and T
except for SWR, and a start-up fault cleared "only by reset" could loop.

**Chosen rule.**

1. Every fault code has a symbolic name and a class (Table B8-3):
   2 `SWR_REPEATED` class 1; 3 `PA_OVERTEMP` (T4) class 1; 9 `SENSOR_IMPLAUSIBLE` class 2;
   10 `RF_NOT_KEYED` class 2; 16 `TX_PATH_NOT_BLOCKED` class 2; 17 `WDT_RESET_AT_START`
   class 1; 18 `SELFTEST_FAILED` class 2; 19 `INTERNAL_ERROR` class 2. Codes 1 and 4–8 are
   reserved: those limits have no `FAULT` action.
2. `FAULT_CLASS` is the highest class among the codes set in `FAULT_FLAGS`.
3. `FAULT_CLEAR` succeeds only if every code set in `FAULT_FLAGS` is class 1 and its
   condition is gone; it then clears all flags. Otherwise it is rejected with
   `WRITE_STATUS` reason `NOT_CLEARABLE` and nothing is cleared. "Condition gone": SWR — the
   radio is unkeyed (the next transmission re-measures it); PA temperature — below T4 minus
   the hysteresis of the temperature limit, TBD (HIS-11, HIS-12); code 17 — always (it is a
   past event, the clear is an acknowledgement).
4. "Repeated trips" exists only for SWR: 3 `UNKEY` trips within 10 s (0020 §29). No other
   limit escalates by repetition; the generic "N repeated trips" of 0007 Decision 5 is read as
   this single case.
5. Code 17 is class 1, not class 2, so that a processor watchdog reset seen at start-up does
   not need yet another reset to clear. The G7250 MUST NOT reset itself to clear a fault;
   class 2 is cleared by a reset that the user or the management channel orders (A3.5). A
   persistent class 2 cause (18) is detected again at start-up and keeps the radio in fault,
   RX only, without resetting (0007 Resolved 9).

- Alternative A: class 2 for code 17. Against: a radio that once had a watchdog reset could be
  cleared only by another reset; a remote host could never acknowledge it.
- Alternative B: N and T for every limit. Against: no limit except SWR has a physical reason
  for escalation; temperature and supply already have their own thresholds.

**Reason.** One deterministic rule a host and a test can follow; no reset loop.

## 6. Limit tiers and "limit in force" (review H7)

**Problem.** Draft 3 checks host writes against the built-in value and reverts to the
built-in value at session end, ignoring the persistent tightening of management C-3 (0008).

**Chosen rule.** Three tiers, each at least as strict as the one above it:

1. **built-in** value (firmware and HIS-12; never writable);
2. **persistent** value (management configuration C-3; equal to the built-in value unless
   tightened);
3. **session** value (`LIMIT_<name>` register, P2; or the TCI equivalent, part C).

The **limit in force** is the strictest of the three. A session write is accepted only if it
is equal to or stricter than the persistent value; a looser one is rejected with
`LOOSER_LIMIT`. Writing 0 and the end of a session return the session value to the
persistent value. A C-3 change is a `MAINTENANCE` drop while armed (0007 drop event 11) and
then applies at once; a session value that is now looser than the new persistent value is
replaced by it. "Limit in force" is the only term used for the value that acts.

- Alternative A: check session writes against the built-in value only. Against: a host could
  write a value between built-in and persistent and believe it is in force.

**Reason.** Follows 0007 rules 1–2 and 0008 C-3 together.

## 7. `REDUCE` for SWR and temperature (review H8)

**Problem.** `REDUCE` is defined only as "lower drive until the value is back inside the
limit". For SWR, lowering power does not lower SWR, so the loop has no end point; for
temperature the response is slow.

**Chosen rule.**

- **SWR above S1:** the radio caps forward power at a fixed fold-back value `P_swr`, TBD
  (HIS-12). The cap is held until the unkey, even if SWR falls below S1 again (no
  oscillation, so no hysteresis is needed). The next transmission starts uncapped and is
  measured again. SWR is evaluated only above a minimum forward power `P_min` (Table A3-2);
  `P_swr` MUST be above `P_min`, so that SWR stays measurable while capped (HIS-11, HIS-12).
  SWR above S2 unkeys as before; the S2 check uses the same `P_min` gate.
- **PA temperature between T2 and T3:** the radio caps forward power at a fixed value
  `P_temp`, TBD (HIS-12), applied while the filtered temperature is at or above T2 and lifted
  when it falls below T2 minus a hysteresis, TBD (HIS-11, HIS-12). The temperature used is
  filtered with a long time constant, TBD (HIS-11, HIS-12), of seconds, not milliseconds. The
  cap may change during a transmission.
- Forward power and supply `REDUCE` stay as in draft 3 (0020 §29).

- Alternative A: proportional control on SWR. Against: SWR does not respond to power; the loop
  would drive power to zero or oscillate.
- Alternative B: no `REDUCE` for SWR, `UNKEY` at S1. Against: drops a QSO for a moderate
  mismatch that a reduced power handles safely.

**Reason.** Deterministic, testable caps; the PA is protected and the operator keeps a
reduced carrier.

## 8. Management and TX (review M1)

**Problem.** A1.9 says management never sets "the TX arm". 0007 drop events 10 and 11 and
the restart command do disarm. T-A1-02 says no request changes the arm. 0008 U-1 says
management "cannot disarm".

**Chosen rule.** Management can never key the radio, set the arm or loosen a limit. It MAY
unkey and disarm, always in the order of A3.2 (unkey, disarm, new token, push). Per command:

- `RESTART` and `FACTORY_RESET`: accepted while armed or keyed; they unkey and disarm first
  (A3.2), then reset. `FACTORY_RESET` drops with `MAINTENANCE`; the reset itself is drop
  event 5.
- `SWITCH_LEVEL`: unkey and disarm first (`LEVEL_CHANGE`), procedure §9.
- `SET_CONFIG` with C-3 limits: `MAINTENANCE` (0007 event 11); with a region change C-6:
  refused, §9.
- Firmware update: refused while armed or transmitting (0008 U-1, unchanged).
- Every other command leaves the TX state alone.

This amends 0008 U-1 ("cannot disarm … for them"): management MAY unkey and disarm through
the commands above; an update itself never disarms, the owner disarms first (stated so in A1.9;
§51 item 8).

- Alternative: refuse `RESTART` and `FACTORY_RESET` with status 50 while keyed. For: a
  management tool cannot cut a QSO. Against: a remote restart is the last way to stop a radio
  whose host has hung while keyed and keeps its socket alive; any P2 host can already cut the
  QSO by a takeover.

**Reason.** Management stays below no TX authority: it can only make the radio safer.

## 9. Level switch and region change (review M2)

**Problem.** A2.5 has no ordered procedure for a level switch, and it is unclear what happens
to a running P2 session, its arm, the push of `TX_ARM_STATE` before port 7250 closes, the
streams, sockets, the TCI listener, and to a region change on level 2.

**Chosen rule.** `SWITCH_LEVEL` (authenticated) runs in this order:

1. Validate: unknown target, status 48; level 2 not in this firmware (before G6), status 56;
   target already active, status 0 and nothing changes; an update in progress, status 35.
2. Reply status 1 (accepted, in progress).
3. If a session is armed or keyed: unkey, disarm (`LEVEL_CHANGE`), new token, push
   `TX_ARM_STATE` to the owner (level 1: port 7250; level 2: part C).
4. Stop all streams of the old level; end its session with the state of A3.6.
5. Log the change with the source address.
6. Close the old level's sockets: on 1→2 the P2 sockets 1025, 1026, 1027, 1029, 1035 and 7250;
   on 2→1 the TCI listener and connections. Port 1024 (discovery) and 7251 stay open.
7. Open the new level's sockets. The new level is then active with no session; identification
   (I-4) and the record field `level` show it.

A region change (C-6) is refused with status 57 while a P2 session runs (0020 §23) and with
status 50 while TX is armed or keyed on any level; on level 2, unarmed, it applies at once.

- Alternative: refuse `SWITCH_LEVEL` while a session runs. Against: a radio stuck with a
  dead session (hardware timer off, B11.10) could not be switched; 0007 event 10 already
  covers a switch while armed.

**Reason.** The old owner learns why it lost the arm before its socket closes; one fixed
order is testable.

## 10. Firmware update state (review M3)

**Problem.** Draft 3 leaves open whether RX streams run during an update, whether
`UPDATE_ABORT` needs a restart, arming during an unconfirmed trial boot, and whether `BUSY` or
`NOT_OWNER` is reported.

**Chosen rule.**

1. From `UPDATE_BEGIN` on, the P2 session ends (`MAINTENANCE` if armed — refused anyway, 0008
   U-1) and all RX streams stop; a High Priority packet with run set is answered, at most once
   per 100 ms, with `STREAM_STATUS` reason 10 (as B5.8 for the slow link).
2. The radio stays in this state until a restart, also after `UPDATE_ABORT` and after an
   abandoned transfer (0008 U-1 "until it restarts"). `UPDATE_ABORT` discards the staging area
   and its reply says that a `RESTART` is needed.
3. During an unconfirmed trial boot (0008 U-6), RX works but an arm is rejected with
   `MAINTENANCE`, until the image has confirmed itself.
4. Register writes during an update are rejected with `BUSY`; `BUSY` takes precedence over
   `NOT_OWNER` (there is no owner then). `CAP_REQUEST` is still answered.

- Alternative A: keep RX running during an update. For: the user still hears the band.
  Against: CPU and SPI time go to flash writes; 0008 U-1 says the radio leaves RUN.
- Alternative B: `UPDATE_ABORT` returns to normal operation without a restart. Against: a
  firmware that has erased and written flash should restart from a known state; differs from
  0008 U-1.

**Reason.** Follows 0008 U-1 literally and adds the trial-boot safeguard.

## 11. Management security details (review M7)

**Problem.** Draft 3 does not say whose challenge an authenticated request uses, how many
replies are cached and for how long, and implies that no secret crosses the network, which
`SET_FIRST_SECRET` contradicts. Replies are not authenticated.

**Chosen rule.**

1. **Challenge per host.** The radio keeps one outstanding challenge per host, keyed by source
   IP address and UDP port, for up to 4 hosts; a fifth host evicts the least recently used. A
   new `GET_CHALLENGE` from a host replaces its challenge. A challenge is used once, by the
   next authenticated request from the same IP address and port, within 10 s (0020 §24). No
   header field is added.
2. **Reply cache.** The last reply per host, for the same 4 hosts, kept 5 s (longer than the
   retry span of 5 × 500 ms, 0020 §24). A repeat of the cached request id gets the cached
   reply; after expiry the challenge is spent and a replay fails with status 33.
3. **Secrets on the wire.** The secret is 32 bytes. `SET_FIRST_SECRET` carries it in the
   clear; this is stated as a known risk (0008 S3, S6). `CHANGE_SECRET` is authenticated with
   the old secret and carries the new one masked: new secret XOR
   HMAC-SHA256(old secret, "G7NS" ‖ challenge) [RFC2104], [FIPS180-4], so it does not cross
   the network in the clear.
4. **Replies are not authenticated** (known limit): a host on the LAN can forge a reply.
   Tools SHOULD verify the result of a write by reading it back.

- Alternative A: a challenge id in the header. For: explicit. Against: changes the framing of
  0020 §27 for no gain over keying by IP address and port.
- Alternative B: send the new secret of `CHANGE_SECRET` in the clear. Against: anyone who
  records one change owns the radio; masking costs one HMAC.

**Reason.** Small, deterministic tables (RAM, HIS-18) and the smallest protection that
removes a cleartext secret where a key exists.

## 12. Stream destination (review M8)

**Problem.** B6.1 and T-B6-02 say "the host's discovery source port", B2.4 says the owner's
source port.

**Chosen rule.** One rule: every stream of a session goes to the owner's source IP address and
UDP port (B2.4; Annex X2, C12); register packets go to General bytes 31–32 at the owner's IP
address when those are non-zero (0020 §13). B6.1 and T-B6-02 follow it.

- Alternative: the discovery source port. Against: a discovery is not required (B5.2), and a
  discovery from another socket must not move the streams (0020 §14).

## 13. Arm details (review M9)

**Problem.** Arming before any General packet, the "inhibited" state of `TX_ARM_STATE`,
`WRITE_STATUS` on a rejected arm, and a non-owner's failed arm are not specified.

**Chosen rule.**

1. An arm requires that the owner has sent at least one General packet in this session that
   the G7250 acted on (long enough, B11.3), with byte 38 bit [0] set. Before that the arm is
   rejected with `WATCHDOG_DISABLED`, although the timer counts as enabled (B5.6). A General
   packet with refused fields (for example byte 39) still counts for byte 38.
2. `TX_ARM_STATE` state 2 "inhibited" means: armed, but a limit inhibit (temperature T3,
   over-voltage) is active, so TX requests do not key. It is entered from state 1 when an
   inhibit starts and returns to 1 when it lifts; no new generation. While disarmed the state
   stays 0 and an arm is rejected with `INHIBITED`.
3. A rejected arm precondition is reported only in `TX_ARM_STATE` (answer and push), not in
   `WRITE_STATUS`. A rejection of the write itself (`NOT_OWNER`, `BUSY`) is reported in
   `WRITE_STATUS` to the writer only.
4. A non-owner's `TX_ARM` write changes nothing in `TX_ARM_STATE`, so it cannot overwrite the
   owner's last reject reason. Arm reject reason 1 `NOT_OWNER` is therefore not used; it stays
   reserved.

- Alternative: report every arm rejection in both registers. Against: a non-owner's write
  would push a state change to the owner.

## 14. ATU tune, CW, PA enable (review M10)

**Chosen rule.**

1. `ATU_TUNE` = 1 while not armed is rejected with `WRITE_STATUS` reason `NOT_ARMED`; it is not
   latched and does not start later.
2. During internal ATU tuning a PTT or CWX edge does not key and does not end the tune; after
   the tune a new 0→1 TX request is needed.
3. Tuning is a keyed state: the keyed timeout (B10.5) applies and ends the tune, which is
   reported as failed (`ATU_STATE` = 4).
4. The TX IQ underrun rule (0007 Decision 2) applies while keyed with `TX_MODE_CLASS` other
   than 2 (CW); "non-CW TX" means exactly that.
5. General byte 58 bit [0] cleared while keyed unkeys (`UNKEY`, arm kept, `TX_STATE` unkey
   reason 7); setting it again does not key without a new 0→1 TX request.

- Alternative for 2: PTT aborts the tune and keys. Against: two TX sources at once; the tune
  power profile would switch to normal power with the ATU half-tuned.

## 15. "While level 1 runs" (review M11)

**Chosen rule.** "While level 1 runs" means: level 1 is the active level, with or without a P2
session. Controller inputs are reported and never key at any time; a controller request
that reaches the main unit (HIS-17) is not a TX request for the arm, does not start a session
and does not block an arm. Controller TX functions (ATU key, SWR scan) are refused while
level 1 is active.

- Alternative: only while a P2 session runs. Against: between sessions the controller would
  be a TX authority without an arm (0007 Decision 6, option 6C rejected).

## 16. Link speed change and flood resistance (review M12)

**Chosen rule.**

1. If the link goes down, or renegotiates below 100 Mbit/s, during a session, the session
   ends: unkey, disarm (`LINK_DOWN`), streams stop, `LINK_STATUS` gives the speed and refusal
   reason 1. A later rise to 100 Mbit/s allows a new session; nothing restarts by itself.
2. **Rate limits per source** (IP address and port), so the radio is no amplifier for spoofed
   requests: a `CAP_REQUEST` from a host that is not the owner is answered at most once per
   1 s per source and at most 10 times per second in total; `NOT_OWNER` answers at most once
   per 100 ms per source; discovery replies at most 10 per second per source and 50 per second
   in total; management replies at most 20 per second per source. Requests above a limit are
   dropped and counted (`GET_STATS`). The owner's own traffic is not limited.
3. **Safety timing does not depend on load.** The watchdog, the keyed timeout, limit actions
   and arm drops MUST meet their timing under any received packet load the link can carry. A
   load that the firmware cannot process may cause the owner's packets to be lost, and so an
   unkey or a watchdog stop (the safe direction); it MUST NOT delay an unkey.

- Alternative for 2: answer `CAP_REQUEST` only to a request at least as long as the record.
  For: no amplification at all. Against: existing hosts send a one-pair request (B4.4); every
  host would need a change.

## 17. AM 25 W limit: what is measured (review M13)

**Chosen rule.** Forward power is measured by the safety core from the PA coupler (HIS-11) in
two forms: the mean over a sliding 100 ms window, and the peak envelope power (PEP) over the
same window. The 100 W limit of SSB, CW and FM applies to PEP. The 25 W AM limit [G7250-MAN]
is read as **carrier power** and applies to the 100 ms mean; PEP in AM is also held to 100 W.
If the detector cannot give PEP (HIS-11), the mean is used for every class. Test T-B10-06:
with class AM and an unmodulated carrier at full drive, the 100 ms mean settles at or below
25 W plus the margin of Table A3-2 within 200 ms, or the radio unkeys.

- Alternative: 25 W PEP in AM. Against: allows only about 6 W carrier at full modulation; not
  what an AM rating of a 100 W transceiver means.

## 18. How a P2 host learns that level 2 is active (review M14)

**Chosen rule.** On level 2 port 7250 is closed, so the record (and its `level` field) cannot
be read. A P2 host learns the active level from discovery byte 4 = 0x03 (radio in use) and,
for the reason, from management identification (I-4). A2.5 says so.

## 19. Part B symbol table (review M4)

**Chosen rule.** Table B8-3 is the single authoritative list of symbolic names for codes:
arm reject reasons, drop reasons, limit ids, fault codes (with class), stream reasons and
write reject reasons. New names: limit ids `LIMIT_TX_FREQ`, `LIMIT_SWR`, `LIMIT_PA_TEMP`,
`LIMIT_FWD_POWER`, `LIMIT_SUPPLY_VOLTAGE`, `LIMIT_CURRENT`, `LIMIT_TX_TIME`,
`LIMIT_ATU_TIME`, `LIMIT_SENSOR`, `LIMIT_RF_NOT_KEYED`; the limit id name equals the name of
its `LIMIT_<name>` register where the limit is host-tunable (TX time, forward power, SWR, PA
temperature, Table B8-2), and no register exists for the others (they are not host-tunable);
fault codes of §5; write reject reasons `NOT_CLEARABLE` (7), `KEYED` (8), `NOT_ARMED` (9).
Existing part B names are not renamed. Part C uses these names verbatim (0021 §14), in lower
case where part C uses lower-case enumerations.

- Alternative: a separate symbol file. Against: two sources to keep in step; the register map
  YAML is generated from Table B8-3 anyway.

## 20. Small fixes (review LOW)

1. **Short management datagrams.** Table B11-1 follows A1.4: a datagram with the right magic
   and 12–17 bytes is answered with status 17; below 12 bytes it is dropped.
2. **Tests.** T-B4-02 checks `cap_magic` only (version and length are T-B4-12); T-B5-10 uses
   C&C every 900 ms; T-B8-01 uses 5 ms, the bound of 0020 §11, and B9.4 "immediately" means
   within 5 ms.
3. **High Priority status port.** Always 1025, since non-default ports are not honoured
   (B2.3, 0020 §13).
4. **TX range check is on the carrier.** The range check uses the DUC0 frequency only; the
   occupied bandwidth of the signal can extend beyond a range edge. Keeping the signal inside
   the band is the host's and operator's duty. Known limit.

## 21. [P2] byte check

1. **Wideband sequence number.** [P2] Wideband Data packet (pp. 52–53): the sequence number
   "is set to zero at power on or whenever a block of raw samples has been sent", and
   "incremented in each sequential packet until the number of samples set in the General
   packet has been sent". The G7250 follows [P2]: 0–7 within each 8-packet frame, 0 again at
   the start of every frame. Draft 3's continuous counter was a deviation without a decision.
2. **Reset points (X2 C2).** [P2] says "power on" for the DDC, High Priority status,
   microphone and wideband packets, and "program start" for DDC audio, DUC I&Q and both
   memory-mapped packets. The High Priority status text says both "set to 0x00000000" and
   "rolls over after exceeding 0xFFFFFFFF" (p. 48). The G7250 resets every outgoing counter at
   power-on and on stop, and keeps a counter on the status packet.
3. **Host packets with sequence 0x00000000.** [P2]: Discovery, Erase, Set IP, General,
   DDC-specific, DUC-specific and High Priority.
4. **C&C.** The four packets headed "Control Elements - PC to Hardware" in [P2]: General,
   DDC-specific, DUC-specific, High Priority.
5. **Wideband defaults (D14).** [P2] General bytes 24–28: defaults 512 samples, 16 bits,
   20 ms, 32 packets; zero selects the default only for byte 26 ("If set to zero the default
   of 16 bits will be used"); byte 27 has the range "0 to 255mS". The G7250 reads zero in bytes
   24–25, 27 and 28 as its fixed values; that part is the deviation.
6. **ADC max magnitude.** [P2] High Priority status bytes 39–40 are headed "ADC0 max
   magnitude" with the note "Max ADC1 magnitude", and the text says "for each of ADC0 and
   ADC1 … up to 32768". The G7250 reports ADC0 in bytes 39–40 as 0–32767, bit 15 = 0, and reads
   the "ADC1" note as ADC0 (Annex X2).
7. **Status bytes 51–59.** [P2]: bytes 51–58 are "general purpose analogue voltage inputs …
   user specific"; byte 59 the "general purpose digital input" bits. The G7250 has neither and
   sends 0.
8. **Watchdog citation.** The stream stop on watchdog is "leaving RUN" ([P2] "Detailed
   operation": "switch out of the RUN state into standby"; High Priority byte 4 bit [0]).
9. **DDC packet quote.** [P2] DDC packet "Destination Port": "the Source Port of the Host that
   initiated the Discovery Command"; the other stream packets say "Discovery Packet".
10. **Memory-mapped packet length.** [P2] shows 240 pairs and no count field; sending only the
    pairs present (4 + 6*n* bytes, 0020 §4) is the G7250 reading (Annex X2).
11. **General bytes 56–57.** [P2] heads byte 56 "Atlas bus configuration" and says of byte 57
    "For Atlas based systems this selects the source of the 10MHz reference clock"; the
    quote is limited to byte 57.

---

**Second review of the transmit side.** A second independent review of the transmit side of
draft 4 (parts A and B) and part C draft 3 found the points below (review ids N-H*, N-M*,
L*). §22–§32 record one choice per point; each rule is stated once in part A or B and
referenced from part C where it applies to TCI. Applied in `spec/network-interface.md`
draft 5 and `spec/part-c-tci-profile.md` draft 4.

## 22. ATU tune cycle (review N-H1)

**Problem.** `ATU_TUNE` (B10.9) and `G7250_ATU_TUNE` (C5.7) were refused only without the
arm. A tune started while already keyed (by PTT, CWX, KEY, `TRX`, `TUNE` or CW text, from the
keying client itself or another) would move ATU relays under normal drive, because the A3.9
exception for ATU tuning had no boundary.

**Chosen rule.** A **tune cycle** is a TX request of its own, the same on both levels:

1. It starts only from unkeyed. `ATU_TUNE` = 1 or `G7250_ATU_TUNE` while keyed by any other
   source, including a transmission of the owner or of the requesting client itself, MUST be
   rejected with `KEYED` (`WRITE_STATUS` on P2, `G7250_WRITE_STATUS` on TCI) and is not
   latched (§24). A repeated start while the cycle itself runs stays a no-op (B8.4, 0020 §11).
2. All key conditions of §24 hold at the start; RF-path changes that are pending are applied
   and settled first (§23).
3. The radio sets the drive to the tune power of the ATU profile (TBD HIS-08, HIS-12) before
   RF starts and before the ATU moves any relay.
4. The cycle owns the key for its whole duration: TX source 4 (ATU), `ATU_STATE` 2. Other TX
   requests neither key nor end it (0022 §14).
5. ATU relays (in/out and the L/C network) move under RF only inside the cycle and only at the
   tune power; this is the only exception to A3.9.
6. The cycle ends unkeyed in every case (tuned, failed, aborted, `LIMIT_ATU_TIME`, keyed
   timeout, any limit unkey or drop). The tune carrier is never handed over to another TX
   source; keying again needs a new 0→1 edge.

- Alternative A: allow a tune start while keyed by the same client and switch to the tune
  profile on the fly. For: one fewer step for the operator. Against: the drive change and the
  first relay move race each other; relays could move at full power.
- Alternative B: let a tune start while keyed unkey first and then tune. For: no rejection.
  Against: a tune press would end another client's transmission; contradicts C7.5.

**Reason.** Relays move under RF only at a known low power, inside a cycle with a defined
start and end; nothing hands RF from one source to another.

## 23. Relay switching guard and settle times (review N-H2, L3)

**Problem.** A3.9 says relays do not change "while keyed", but an unkey takes time to take RF
away, and a relay takes time to settle. Draft 4 allowed a relay to move at the instant of the
unkey and a key at the instant after a relay change, including the case of a band change and
a PTT 0→1 edge in the same High Priority packet. The class-2 fault "RF while not keyed"
(Table A3-2) could trip on the decaying RF of a normal unkey.

**Chosen rule.** A3.9a, level-independent:

1. **RF gone.** After an unkey, no RF-path relay (antenna, ATU, TX and RX filters,
   preamplifier, attenuator, T/R relay, RX attenuator during TX) moves until RF is gone:
   forward power below a threshold `P_rf_off`, or a fixed guard time `t_rf_off` after the
   unkey, whichever the hardware design uses; values TBD (HIS-07, HIS-12).
2. **Settle.** The radio keys only after the settle time `t_settle` has elapsed since the last
   relay change; TBD (HIS-07).
3. **Same packet or frame.** RF-path changes that arrive together with a TX request (a High
   Priority packet with a new DUC0 frequency or Alex word and PTT 0→1; a TCI frame with `VFO`
   and `TRX:0,true`) are applied first, then settled, and then the radio keys, provided the
   request is still asserted and every key condition of §24 holds at that moment. This
   bounded wait is the only case in which a TX request is deferred rather than refused.
4. **T/R and RX attenuator during TX.** At a key: T/R relay and the RX attenuator during TX
   (DUC-specific byte 59 [P2]) to their TX position, settle, SEND, RF delay (DUC-specific
   byte 13), RF. At an unkey: RF off, RF gone, SEND released, then both back to their RX
   position and deferred changes applied. With CW break-in they return after the hang delay
   (DUC-specific bytes 11–12).
5. **Session end.** The relay set of A3.6 (at session end, takeover, standby, fault) is
   applied only after the unkey and RF gone.
6. **Blanking (L3).** The check "RF while not keyed" runs only while not keyed and after a
   blanking time `t_blank` since the last unkey; `t_blank` is at least the time of item 1;
   TBD (HIS-11, HIS-12).

- Alternative A: refuse a TX request that arrives during a relay change or settle. For: no
  deferred state. Against: a host that sends the new band and PTT in one packet (allowed by
  [P2], which orders nothing inside a packet) would never key on the first try.
- Alternative B: no guard times; rely on the hardware. For: simplest. Against: hot switching
  is the failure that A3.9 exists to prevent; the HIS gives the times, the rule does not
  depend on their values.

**Reason.** "Not under RF" needs the RF to be gone, not only the key released; a short,
bounded wait keeps the common "band and PTT together" case working.

## 24. One key rule; refused requests are not latched (review N-M1)

**Problem.** Draft 4 stated "keying needs a 0→1 edge" in several places (B10.2 item 4,
B10.10, A3.3 `UNKEY`), but not as one rule. It was open whether a PTT held at 1 while PA
enable is 0, while a DUC-specific refusal or EER stands, outside the TX ranges or while
unarmed keys once the condition clears, and whether CW text sent while unarmed is queued.

**Chosen rule.** A3.1a, both levels: the radio keys only on a 0→1 edge of a TX request at a
moment when every key condition holds (armed and not inhibited, not in fault, TX frequency in
range, PA enabled, no DUC-specific refusal or EER for PTT with DUC I&Q, a mode class defined,
the requester allowed by the TX policy on TCI, not keyed by another source, relays settled).
A request refused for any reason is not pending or latched: it does not key when the
condition clears; a new 0→1 edge is needed. The one deferral is §23 item 3. CW text
(`CW_MACROS`, `CW_MSG`) received while it cannot key is discarded, not queued.

- Alternative: latch a refused request and key when the condition clears. For: fewer edges
  for the host. Against: the radio would key at a moment the operator did not choose, for
  example when a fault clears or an arm completes.

**Reason.** The operator's action and the key coincide in time; this is the rule of 0007
Decision 1 rule 2 applied to every condition.

## 25. Backstops for hung TX logic (review N-M2, L10)

**Problem.** Part C C8.2 said the P2 keyed timeout unkeys "a host whose network thread is
alive but whose TX logic has hung". That is not so: a host whose I/O thread keeps sending
High Priority packets with a cached PTT or CWX bit feeds the keyed timeout. On P2 the DUC
underrun check applied only outside class CW, and its time was open; CWX had no bound.
Server-generated CW text on TCI had no bound but the 5 min maximum TX time.

**Chosen rule.**

1. The C8.2 rationale is corrected: the keyed timeout catches a host whose High Priority
   packets stop; it does not catch a cached PTT or CWX bit.
2. **P2 CWX cap (B10.5a).** High Priority byte 5 bit [0] held at 1 continuously for more than
   1 s unkeys (`UNKEY`, arm kept, `TX_STATE` unkey reason 9); keying again needs a new 0→1
   edge. The same 1 s cap applies to a TCI `KEYER` key-down from any client, opted in or not
   (C8.2). 1 s equals the TCI generic keyed window and the P2 base watchdog; a dash at 5 words
   per minute (720 ms) fits. The KEY input (hardware CW, HIS-17) is not capped: no network is
   involved.
3. **DUC underrun.** The check applies whenever the TX source is PTT (DUC I&Q), whatever the
   mode class; the underrun time is at most the `KEYED_TIMEOUT` in force (so at most 500 ms);
   exact value TBD (HIS-18). Hosts that send CW as I&Q keep the I&Q stream running during
   key-up, as they must for a continuous DUC stream.
4. **TCI CW text (L10).** While the server sends CW text for a keying client, that client
   MUST send an application frame at least every 30 s; otherwise the server unkeys, discards
   the queued text and reports `unkey` 2. Each `CW_MACROS` or `CW_MSG` is an application
   frame.
5. Known limit: a host whose I/O thread also keeps sending cached I&Q is caught only by the
   maximum TX time.

- Alternative A for 2: no CWX cap; rely on the 5 min maximum TX time. For: no new rule.
  Against: up to 5 min of carrier from a hung host; TCI already caps `KEYER` at 1 s.
- Alternative B for 4: a cap on the total duration of queued text. For: no client duty.
  Against: `CW_TERMINAL` and appended macros make the total unbounded and speed-dependent.

**Reason.** Each TX source that a cached bit or a queue can hold on now has a bound well
below the maximum TX time.

## 26. Mode class change while keyed (review N-M3)

**Problem.** Table B8-2 said a `TX_MODE_CLASS` change while keyed "applies at once", while
TCI refuses `MODULATION` while keyed (C7.6.3). A class change under RF moves the power limit
(25 W AM carrier against 100 W PEP) during a transmission.

**Chosen rule.** One principle, A3.9c: the TX mode class never changes under a transmission.
On P2 a `TX_MODE_CLASS` write with another value while keyed unkeys first (`UNKEY`, arm kept,
`TX_STATE` unkey reason 10), then applies; the same value is a no-op. On TCI a `MODULATION`
change while keyed stays refused with `KEYED` (C7.6.3).

- Alternative: refuse the P2 write with `KEYED`. For: same form as TCI. Against: on P2 the
  host's mode has already changed (the radio does not know the host's mode, 0007 Sub-decision
  4 rule 3); a refused class would let an AM carrier run under the SSB limit.

**Reason.** On P2 the declared class must follow the host's signal; on TCI the server makes
the signal, so refusing the mode keeps both in step. In both, no RF runs under a class other
than the one in force.

## 27. Class-1 fault clear hold-off and escalation (review N-M4)

**Problem.** A host could clear a class-1 fault at once and re-arm in a loop (for example
repeated `SWR_REPEATED` into a broken antenna), so a class-1 fault limited nothing in time.

**Chosen rule.** A3.5:

1. `FAULT_CLEAR` (and `G7250_FAULT_CLEAR`) MUST be rejected with `NOT_CLEARABLE` until 10 s
   have passed since the latest fault entry.
2. The third entry of the same class-1 code since power-on is handled as class 2: latched
   until reset, `FAULT_CLASS` 2.
3. The per-code fault entry counters, a reset counter (by cause) and `TRIP_COUNT` count since
   power-on: they survive `RESTART` and every other reset without loss of power, and are
   cleared only at power-on; whether the hardware keeps them across a processor reset is
   HIS-13. They are read with `GET_STATS` and logged. After an escalation the operator has to
   be at the radio (power cycle).

- Alternative A: no hold-off, escalation only. For: quick recovery. Against: three fast
  clear-arm loops still go by in seconds.
- Alternative B: counters cleared by `RESTART`. For: a remote restart recovers fully.
  Against: a remote loop of fault, restart, fault would never escalate.

**Reason.** A real fault cannot be cleared away faster than its cause can be seen, and a
repeating one needs someone at the radio.

## 28. ATU memory recall (review N-M5)

**Problem.** An internal ATU may recall a stored L/C state per frequency (whether the G7250
ATU does: HIS-08). A retune
while keyed could make the ATU switch its network under RF, outside a tune cycle.

**Chosen rule.** Every change of the ATU L/C network or in/out state is an RF-path state
change (A3.9). No recall happens while keyed. A retune while keyed that would recall another
ATU state unkeys first (`TX_STATE` unkey reason 6, as §1), then the recall is applied after RF
gone and settle (§23). Which frequencies share an ATU state: HIS-08.

- Alternative: keep transmitting and defer the recall to the unkey. For: no broken
  transmission. Against: the ATU stays matched for the old frequency, SWR rises under RF; the
  same case as §1 Alternative A.

**Reason.** The same rule as every other relay; the ATU network is a relay set.

## 29. Takeover notice and host guidance (review N-M6)

**Problem.** The old owner receives one `TX_ARM_STATE` (`TAKEOVER`) and nothing more (A2.4).
One UDP datagram can be lost; the old owner then keeps sending C&C and takes the radio back
(ping-pong).

**Chosen rule.** The G7250 sends the final `TX_ARM_STATE` (`TAKEOVER`) three times, about
10 ms apart, identical, and nothing else. Host guidance: a host that receives neither DDC0
data nor High Priority status packets for more than 200 ms while it believes it owns the radio
SHOULD treat ownership as lost, stop sending C&C and tell the user; it starts a new session
only on user action. For AetherSDR this is C7.2.1.

- Alternative: a takeover notice with acknowledgement. For: reliable. Against: the radio would
  keep state for a host that is no longer the owner; [P2] has no such packet.

**Reason.** Repetition covers a single loss of the notice. Corrected by §48: the 200 ms rule
does not prevent a retake by C&C that the old owner sent before it saw the notice; §48 adds the
repeated notice, the stop-at-once rule and the sequence-0 sign, and states the remaining race as
a known limit.

## 30. TCI drop reasons in Table B8-3 (review N-M7)

**Chosen rule.** Table B8-3 gets drop reasons 13 `STOP` and 14 `HOLDER_LOST`, used on TCI
only (C5.5.5 rows 2 and 3); never set over P2. 7 stays unused. Table B8-3 is then complete for
every code name in part C.

- Alternative: keep them as part C additions. Against: two lists; the register map YAML is
  generated from Table B8-3 (§19).

## 31. Built-in limits never writable; recovery of a persistent limit (review N-M8, L8)

**Problem.** A3.4 rule 1 says built-in values are never writable; rule 2 said they "may only
be tightened" over management; C5.5.5 row 11 spoke of "built-in limits over the management
channel". A persistent limit tightened by mistake could not be undone except by a firmware
change.

**Chosen rule.** Built-in values are never writable, over any channel. Management C-3 writes
only the persistent tier. An authenticated `SET_CONFIG` MAY set a persistent value anywhere
between the strictest value and the built-in value, so it may also loosen it back toward the
built-in value; such a loosening is accepted with status 0 and logged with the old value, the
new value and the source; a value looser than the built-in value is refused with status 49.
Any C-3 change while armed drops the arm (`MAINTENANCE`). `FACTORY_RESET` does not touch
limits. 0008 C-3 ("MAY only be made stricter than the built-in limits") is read against the
built-in value.

- Alternative: include the limits in `FACTORY_RESET`. For: no loosening path at all.
  Against: losing the network configuration and the secret to fix one limit.

**Reason.** The safety bound is the built-in value; the persistent tier is a user choice
below it and can be corrected by the same authenticated path that set it.

## 32. Second-review small fixes (review LOW)

1. **`ROLLBACK` while armed or keyed (L1).** Refused with status 50, like every update step
   (A1.8 U-1; §8). Alternative: unkey and disarm first, like `RESTART`. For: rollback always
   works. Against: switches firmware under an active transmission without the owner;
   `RESTART` stays the unconditional stop.
2. **DUC FIFO flush (L2).** The DUC FIFO is emptied at every unkey, session end and takeover,
   so no stale I&Q is sent at the next key; on TCI the buffered TX audio is discarded at every
   unkey (C7.7).
3. **`G7250_FAULT_CLEAR` takes the code (L4).** `G7250_FAULT_CLEAR:<fault_code>;` with the
   Table B8-3 name of the current `FAULT_CODE`; another name is `BAD_VALUE`. Same as P2, so
   that a clear acknowledges the fault the client has seen. Alternative: no argument. Against:
   a client could clear a fault it never displayed.
4. **Case rule (L5).** One wording: Table B8-3 names appear on TCI verbatim, in upper case;
   part C's own enumerations, which have no Table B8-3 name, are lower case.
5. **Unkey reasons (L6).** `TX_STATE` [23:16] gets 8 keying client lost (TCI only), 9 CW
   key-down longer than 1 s (§25), 10 TX mode class changed while keyed (§26). (L1) A TCI
   `STOP` makes AetherSDR clear the P2 run bit (P2 drop `RUN_CLEARED`, which unkeys first);
   its TCI clients get drop reason `STOP`.
6. **Per-limit inhibit (L7).** `LIMIT_STATUS` has no free bits for a third field (bits 0–15
   and 16–31 are per limit id), so a new register `LIMIT_INHIBIT` at 0x0221 in group 2: bit
   *n* set while limit id *n* holds an inhibit. `G7250_TX_STATE` `inhibits` is derived from
   it on level 1. Alternative: inhibit bits in `TX_STATE`. Against: no free per-limit field
   there either.
7. **Glossary and C8.2 wording (L9).** "Session" follows A2.3 (run bit; discovery not
   required). C8.2 no longer speaks of a "generic arm holder": the holder has opted in.

## 33. RF-path state for the TX frequency at every key (final review H1)

**Problem.** A3.1a lists no condition on the RF path. A3.9 only acts on a TX-frequency change
*while keyed*. With split or cross-band operation (DDC0 at 7.1 MHz, DUC0 at 14.2 MHz [P2] High
Priority bytes 9–12, 329–332; TCI channel A and B with split, [TCI] §4.2 SPLIT_ENABLE) the radio
could key into the low-pass filter, band relays, ATU network or antenna set for the receive
frequency.

**Chosen rule.** A3.1a gets a key condition: the RF-path state (TX low-pass filter, band
relays, ATU in/out and network, antenna where it depends on the band) is the one required for
the effective TX frequency in force (DUC0; the TCI TX frequency). A3.1b: while unkeyed the
state follows the receive frequency (DDC0; `DDS`); at every key, if the state differs, the
radio switches unkeyed, waits until settled (A3.9a item 2) and then keys, with the bounded
wait of A3.9a item 3; at the unkey it returns to the receive state once RF is gone. If HIS-07
shows a TX low-pass filter outside the receive path, it MAY stay set for the TX frequency
while unkeyed. Part C C7.6.1 item 4 and C7.6.2 apply the same on TCI.

- Alternative A: while unkeyed the state follows the TX frequency. For: no relay movement and
  no settle delay at each key in split. Against: the radio receives through the filter and ATU
  network of another band, which degrades receive, the use that runs all the time.
- Alternative B: refuse a key whose TX frequency needs another state than the one in use. For:
  no relay timing at the key. Against: split cross-band would never key; the host cannot tell
  why.

**Reason.** Receive is the continuous state; the extra `t_settle` (HIS-07) at a cross-band key
is the price of never keying into a wrong filter.

## 34. Set-up phase: packets before the run bit count for the session (final review H2)

**Problem.** B5.6 and B10.2 item 3 accept an arm only after a General packet "in this session"
with byte 38 bit [0] set, and the session starts with the run bit (A2.3). [P2] has the host send
General, DDC-specific and DUC-specific packets before the High Priority packet with run ([P2]
"Detailed operation"; packet introductions; B5.1), and AetherSDR sends the General packet only
at set-up (`annex-aethersdr.md` §2.2: the keepalive is the High Priority packet). A standard host
could never arm; General byte 58 bit [0] (PA enable) and byte 39 would also be lost.

**Chosen rule.** B5.1a: while no session runs, the G7250 keeps the latest General, DDC-specific
and DUC-specific packet of each source (IP address and port) since the last session end, for up
to 4 sources (least recently heard evicted). When a host starts a session with its run bit, its
kept packets count for that session, in order, before the run packet. Kept packets of other
sources are discarded at that moment. At every session end the set is emptied. Nothing is kept
on level 2 or from outside the subnet (§49). B5.2, B5.6, B10.2 item 3, T-B5-14 (extended to the
B5.1 order) and T-B5-15 follow; Annex X2 C18.

- Alternative A: keep only the latest set-up packets, from any source. For: one slot. Against:
  set-up from another host (or a spoofed one) would count for the owner.
- Alternative B: keep the set-up across a session end for the same host. For: a restart with
  the run bit only ([P2] "Detailed operation", restart path) could arm at once. Against: state
  from an ended session carries over; the host is told by `WATCHDOG_DISABLED` and resends one
  General packet.

**Reason.** It makes the [P2] order work as written and binds the set-up to the host that then
owns the session.

## 35. Reordered or duplicated High Priority packets (final review M1)

**Problem.** B2.7 and B11.6 never reject a packet for its sequence number. A reordered or
duplicated High Priority packet (PTT 1 arriving after a newer PTT 0) makes a false 0→1 edge and
keys the radio. [P2] gives the host's High Priority sequence number as 0x00000000.

**Chosen rule.** B11.6a: once the owner's High Priority packets carry a non-zero sequence number
in a session, a packet that is not newer than the last accepted one, in 32-bit serial-number
arithmetic (RFC 1982), is discarded and counted; the comparison restarts at each session start
and takeover. Hosts SHOULD number from 1. With numbers 0 (as [P2]), a PTT or CWX 0→1 edge counts
only after the bit has read 0 for at least 10 ms; the remaining risk (a packet more than 10 ms
late) is stated as a known limit. Annex X1 D28.

- Alternative A: no check; rely on the LAN. For: [P2] as written. Against: one duplicated
  packet keys 100 W.
- Alternative B: a longer minimum PTT-off time (for example 50 ms) in both cases. For: covers
  later packets. Against: cuts fast PTT-keyed CW (a dot gap at 60 wpm is 20 ms) and is not
  needed for numbered hosts.

**Reason.** Numbered hosts get an exact check; unnumbered hosts get a guard that costs nothing
at normal keying speeds.

## 36. CWX bits of High Priority byte 5 (final review M2)

**Problem.** Table B7-2, B10.1, B10.5a and D26 treat byte 5 bit [0] as the key. [P2] (High
Priority packet byte 5, p. 34) defines bit [0] as "CWX", which selects CW from the host, and bits
[1] and [2] as dot and dash, sent at the keyer speed. The key-down cap was put on the wrong
bit.

**Chosen rule.** With bit [0] set, bits [1] and [2] are the paddle inputs of the radio's keyer,
which forms the elements at the keyer speed and weight (DUC-specific bytes 9–10). The TX request
is asserted while bit [0] and bit [1] or [2] are 1; its 0→1 edge is the key edge. With bit [0]
clear, bits [1] and [2] are ignored. The 1 s cap applies to the time either paddle bit is held,
whichever bit, also while the keyer is between elements. Annex X2 C19; Table B7-2 rows 5, B10.1,
B10.5a, B10.9, D26.

- Alternative: treat bit [0] alone as a straight key. For: simple. Against: not what [P2]
  says; a host that sets bit [0] to select CW would key the carrier.

**Reason.** Follow [P2]; the cap guards against a cached paddle bit, which is the hung-host
case of §25.

## 37. TX edge while relays move or settle from an earlier change (final review M3)

**Problem.** A3.9a item 3 waits only for changes in the *same* packet. A host that moves DUC0 in
one High Priority packet and sets PTT in the next (10 ms later [P2] "Detailed operation",
100 ms rate) finds the relays still settling; A3.1a then refuses the edge, which is not latched,
and the host's PTT is lost.

**Chosen rule.** The bounded wait covers every edge that arrives while an RF-path change is
pending, moving or settling, whatever the cause: same packet, earlier packet, the key-time
switch of §33, or right after an unkey. Bound: `t_rf_off` + `t_settle` from the edge (HIS-07,
HIS-12). A further RF-path change during the wait, or reaching the bound, refuses the request
(not latched). Part C C7.6.5.

- Alternative: refuse every edge while relays move, and say so. For: no deferred request.
  Against: ordinary hosts lose PTT presses after a band change, with no way to see why.

**Reason.** The wait is short and bounded and keeps the one rule of A3.1a: keying happens only
when every condition holds.

## 38. ATU state after a tune that did not end tuned (final review M4)

**Problem.** After a failed, aborted or time-limited tune cycle, or a takeover during it, the
ATU network is undefined; nothing says whether `ATU_STATE` = 4 blocks keying.

**Chosen rule.** Once RF is gone the ATU returns to the stored state for the TX frequency if one
exists (HIS-08), else to bypass. `ATU_STATE` = 4 means "the last tune did not end tuned; ATU at
the stored state or bypassed" and stays until the next tune cycle or an in/out change. It does
not block keying. A3.9b item 7; Table B8-2; part C C5.7.

- Alternative: block keying until a new tune or a bypass. For: no TX into an unknown match.
  Against: the network is no longer unknown after the restore; the SWR limits of Table A3-2
  protect the PA; an operator with a good antenna would be stopped for nothing.

**Reason.** A defined network plus the SWR limits is safe; blocking adds no protection.

## 39. `ATU_TUNE` retries (final review M5)

**Problem.** B8.4 lets a host repeat a write after 100 ms without an answer and calls repeated
writes harmless. A retried `ATU_TUNE` = 1 that arrives after a short cycle has ended starts a
second tune carrier.

**Chosen rule.** A start within 2 s after the end of the previous cycle is a no-op, answered
with the value in force and `ATU_STATE`; the same on TCI (`G7250_ATU_TUNE`). B8.4 is reworded.

- Alternative: require the host to read `ATU_STATE` before a retry. For: no timer. Against:
  relies on every host; the radio cannot enforce it.

**Reason.** 2 s covers several 100 ms retries; a deliberate second tune waits 2 s.

## 40. Commanded resets wait until RF is gone (final review M6)

**Problem.** `RESTART` and `FACTORY_RESET` unkey and reset (A1.9), but nothing makes the reset
wait for RF to decay; during a reset the state of the PA, SEND and relay lines is not known
(HIS-13), so relays could move under RF.

**Chosen rule.** Every commanded reset (`RESTART`, `FACTORY_RESET`, `UPDATE_ACTIVATE`,
`ROLLBACK`, the abandoned-update restart of §51) runs: reply, unkey, RF gone (`P_rf_off` or
`t_rf_off`, A3.9a item 1), disarm and push, relays to the A3.6 state only after RF is gone,
then reset. A1.9, A3.6, Table A1-2.

- Alternative: reset at once and rely on the hardware reset state. For: simplest. Against:
  HIS-13 is open; the relay sequence of §23 would not hold.

**Reason.** The same relay rule as every other unkey.

## 41. One drop reason for a limit trip with action `FAULT` (final review M7)

**Problem.** A limit trip with action `FAULT` was both Table A3-1 event 6 (`FAULT`) and event 7
(`LIMIT_<name>`); Table B8-3 and C5.5.5 gave two reasons.

**Chosen rule.** Event 7 covers only the action `DISARM` (no limit of Table A3-2 has it in this
version); a trip with action `FAULT` is event 6, drop reason 6 `FAULT`, with the cause in
`FAULT_CODE`. Table A3-1, Table B8-3, C5.5.5 rows 7 and 8.

- Alternative: drop reason 0x40 + limit id and the fault code in `FAULT_CODE`. For: the limit
  is visible in the drop reason. Against: the same fault (`PA_OVERTEMP`) would give different
  drop reasons depending on the path; `FAULT_CODE` already names the cause.

**Reason.** One reason per event; the fault registers carry the detail.

## 42. Under-voltage recovery (final review M8)

**Problem.** Table A3-2 gives "inside range for 2 s" as recovery for the supply, but only the
over-voltage `UNKEY` held an inhibit, so after an under-voltage `UNKEY` a new TX request could
key at once on a sagging supply.

**Chosen rule.** An under-voltage `UNKEY` also holds an inhibit until the supply has been inside
the range for 2 s; `LIMIT_INHIBIT` bit 5 covers both. An under-voltage `REDUCE` holds none.

- Alternative: no inhibit after under-voltage. For: the operator can retry at once. Against:
  the supply recovers as soon as the load is gone, so keying again trips again and the radio
  oscillates between key and unkey.

**Reason.** The 2 s recovery already in Table A3-2 needs the inhibit to mean anything.

## 43. Power measurement for AM and for a mean-only detector (final review M9)

**Problem.** A3.4c applied the 25 W AM limit [G7250-MAN] to the 100 ms mean. A 25 W carrier with
100 % sine modulation has a mean of 37.5 W (carrier × (1 + m²/2)) and a PEP of 100 W, so a
correct AM signal was reduced. And "the mean is used for every class" when the detector gives no
PEP lets SSB peaks far above 100 W. T-B10-06 tested only an unmodulated carrier.

**Chosen rule.** Where the detector gives envelope samples (HIS-11), AM uses a carrier estimate,
the square of the mean envelope amplitude over 100 ms, at most 25 W, plus PEP at most 100 W.
Without envelope samples AM uses mean at most 25 W. Without PEP: CW and FM mean at most 100 W,
SSB mean at most `P_ssb_mean`, starting value 25 W (6 dB PEP-to-mean), final HIS-11, HIS-12.
T-B10-06, T-A3-32, T-A3-33, part C C5.6, T-C5-09, T-C8-14.

- Alternative A: mean at most 37.5 W together with PEP at most 100 W. For: needs only mean and
  PEP. Against: an unmodulated carrier could reach 37.5 W, 50 % over the 25 W rating.
- Alternative B: carrier from the envelope minimum or a longer window. For: simple hardware.
  Against: the minimum is 0 at 100 % modulation; a longer window delays the limit.

**Reason.** The mean envelope amplitude is the carrier amplitude for any modulation that
averages to zero; the fallbacks err on the low side.

## 44. Network configuration change while armed (final review M10)

**Problem.** A `SET_CONFIG` C-1 change of the radio's address is applied after the reply (A1.6)
but was not listed in A1.9 or Table A3-1, unlike P2 Set IP (drop event 9).

**Chosen rule.** A C-1 change of address or netmask ends a running session (A2.3) and, while
armed, is drop event 9 (`SESSION_CHANGED`); it is applied after the reply and after RF is gone.
On TCI it is C5.5.5 row 14.

- Alternative: refuse C-1 while armed (status 50). For: no session cut by management.
  Against: P2 Set IP cannot be refused (0008 point 6), so the radio can lose its address while
  armed anyway; two rules for one effect.

**Reason.** Same handling as Set IP; management only makes the radio safer (§8).

## 45. Firmware update while level 2 is active (final review M11)

**Problem.** A1.8 states the update state for P2 (session ends, `BUSY`, `STREAM_STATUS`
reason 10); part C had no counterpart for streams, connections and replies on level 2.

**Chosen rule.** Part C C2.8: from `UPDATE_BEGIN` the server stops every stream
(`G7250_STREAM_STATE` `stopped`, reason `update`), sends `TX_ENABLE:0,false;`, keeps the
connections open, answers set requests with the value in force and `BUSY`, rejects arm requests
with `MAINTENANCE` and stream starts with `refused` `update`, and closes every connection with
1001 just before the commanded reset. On level 1 AetherSDR passes items 1 and 2 on.

- Alternative: close all TCI connections at `UPDATE_BEGIN`. For: simple. Against: clients lose
  the progress and safety notifications for the whole update and reconnect into a refused
  state.

**Reason.** The TCI form of the P2 rule: nothing changes, everything is still visible.

## 46. Level-1 holder rules (final review M12)

**Problem.** C5.5.5.1 item 1 (a second valid arm is a no-op; a client becomes holder only after
a drop) contradicted item 2 and C5.5.7 (AetherSDR's interface and one TCI client both hold);
how a TCI client becomes holder while the interface holds the arm, and who may lift
`G7250_TX_POLICY:holder`, were open (0021 §24; T-C5-27).

**Chosen rule.** Item 1 applies between TCI clients. On level 1 the one P2 arm can have two
holders, the interface and one TCI client; this is the only exception. A TCI client becomes
holder by a valid `G7250_TX_ARM` while no TCI client holds the arm: with no P2 arm, AetherSDR
performs the handshake; with the interface holding, the client joins without a P2 write or a
new generation. The interface joins the same way. Under `holder` both holders key. The **policy
owner**, the holder that set `holder` (or the remaining holder once it stops), alone may set
`any`. This refines 0021 §24 items 1 and 2.

- Alternative: one holder only; a TCI arm while the interface holds is refused. For: one rule
  for both levels. Against: an application such as a logger could never arm while the user has
  armed in AetherSDR, which 0021 §24 wanted to allow.

**Reason.** Two holders of one P2 arm match how AetherSDR works; the policy owner keeps the
restriction from being lifted by the other holder (0021 §1).

## 47. TCI `START` on level 1 while the radio is in use (final review M13)

**Problem.** On level 1 AetherSDR maps `START` to its P2 session start (C4). If the radio
reports 0x03 in discovery byte 4, a TCI client's `START` would take the radio over from another
host without anyone deciding to.

**Chosen rule.** While discovery answers 0x03, AetherSDR MUST NOT start a session on a TCI
`START` without confirmation by its own user (C4; C7.2.1; C-C17).

- Alternative: allow it, since [P2] allows any takeover. For: [P2] as written. Against: any
  TCI client on the LAN could then cut another operator's QSO; A2.4 already asks hosts to warn.

**Reason.** A takeover is a user decision; a TCI command is not a user.

## 48. Takeover race (final review M14)

**Problem.** §29 said that the three repeated notices and the 200 ms host rule "cover the rest".
They do not: C&C that the old owner sent before it saw the notice is itself a takeover ([P2]
Discovery reply byte 4 NOTE), so the old owner can take the radio back within one keepalive
(100 ms), before the 200 ms rule can act.

**Chosen rule.** (1) For 5 s after a takeover, every non-C&C packet from the old owner (DUC I&Q,
memory-mapped) is answered with one copy of the `TAKEOVER` notice, at most once per 100 ms.
(2) Host guidance: stop C&C at once on a `TAKEOVER` notice; treat a stream of the session that
restarts at sequence number 0 without its own stop and run as a sign of a takeover (counters
restart at every takeover, B2.7), stop C&C and tell the user. (3) Known limit: the exchange ends
after at most one bounce, possibly with both hosts stopped; neither transmits, because every
takeover disarms. §29's reason is corrected accordingly.

- Alternative: a hold-off of a few hundred ms in which the previous owner's C&C is not a
  takeover. For: ends the race in the radio. Against: deviates from 0007 Decision 3 ("takeover
  … at any time", accepted); a host whose notice was lost would be locked out silently.

**Reason.** Within [P2] and 0007 the race cannot be removed in the radio; it can be made short,
visible and safe.

## 49. Unasked record and spoofed sources (final review M15)

**Problem.** The capability record (about 1250 bytes) was sent unasked at a host's first
General packet (B4.4; 0003 §2), not rate-limited: a spoofed 60-byte General packet made the
radio send it to a victim. A spoofed run bit starts DDC0 to the spoofed address. B11.14 claimed
the G7250 is "no amplifier".

**Chosen rule.** The unasked record is sent once per session: at the session start if the
owner's set-up phase holds a General packet (§34), else at its first General packet in the
session; to the owner's register destination; counted against the `CAP_REQUEST` limit of that
destination. A General packet outside a session gets no record. P2 C&C, DUC I&Q and
memory-mapped packets from outside the radio's subnet are discarded (B11.15; D29). B11.14 states
the in-subnet reflection by a spoofed run bit as a known limit inherent in [P2]. This reads
0003 §2 ("at the host's first General packet") as "the first General packet of the session".

- Alternative: no subnet rule; state the reflection as a known limit only. For: hosts behind a
  router keep working. Against: a radio on a forwarded port could be made to stream 18 Mbit/s
  to any address on the Internet, and could be keyed from there by anyone who sees the token.

**Reason.** The management channel already answers only its own subnet (0008 S4); P2 carries
the transmitter and gets the same reach.

## 50. AetherSDR annex: PA enable (final review M16)

**Chosen rule.** The annex lists General byte 58 bit [0] (PA enable) as required in G-08a and
G-08b and marks it in the §3.1 table as not yet set by AetherSDR (taken as 0 until checked),
since no TX request keys while it is 0 (B10.10; A3.1a). No alternative: this is a statement of
fact about the spec, not a choice.

## 51. Final-review small fixes (review LOW)

1. **Status for `SWITCH_LEVEL` during an update (L1).** New status 58 "refused while a firmware
   update is in progress" instead of 35 (another writer). Alternative: 50. Against: 50 means
   armed or transmitting; a tool would disarm for nothing.
2. **Register read mechanism (L3).** B8.4a: a register is read from pushes or by writing to it
   (read-only: answered with the value and `READ_ONLY`); a non-owner can read every register,
   `TX_ARM_TOKEN` included, through the `NOT_OWNER` echo. Accepted: the token is not a secret
   (A3.1; 0007 option 1C). Alternative: suppress the value in `NOT_OWNER` answers. Against:
   the token is visible on the wire to the same host anyway.
3. **After a takeover (L4).** "Nothing more is sent to the old owner" is limited to stream
   packets and register pushes; answers to its own requests follow their usual rules.
4. **General packet on level 2 (L5).** Ignored and counted; no set-up phase on level 2.
5. **Precedence 57 before 50 (L6).** A region change while a P2 session runs and armed gets 57:
   ending the session also ends the arm. Alternative: 50 first. Against: after a disarm the
   tool would still get 57.
6. **`UPDATE_STATUS` (L7).** A read, answered at any time, also while armed.
7. **TCI reason codes (L8).** A refused `G7250_ATU_TUNE` gets `NOT_ARMED`, `KEYED`, `BUSY` or the
   new write reject reason 10 `NOT_KEYABLE` (another key condition of A3.1a fails), also on P2
   for `ATU_TUNE`. `G7250_FAULT_CLEAR` gets `BAD_VALUE`, `NOT_CLEARABLE` or `BUSY`; any client
   may send it, because in fault nobody holds the arm. Alternative for `NOT_KEYABLE`: reuse
   `NOT_ARMED`. Against: misleading while armed.
8. **0008 U-1 (L9).** §8 is an explicit amendment of 0008 U-1, stated in §8 and A1.9.
9. **Abandoned update (L10).** After 10 min without an update command (`UPDATE_STATUS`
   excluded) the update is aborted, logged, and the radio restarts into the running image as a
   commanded reset (§40). Alternative: stay in the update state until a visit to the radio.
   Against: a remote radio would stay RX-dead.
10. **Underrun tolerance (L11).** B10.5 states it: not before the underrun time, unkeyed by the
    underrun time + 10 ms, which T-B10-11 tests.
11. **Level 2 below 100 Mbit/s (L12).** Part C C2.9: connections accepted, device not
    started, streams refused (`link`), arm `NOT_RUNNING`; as level 1 (B5.8). Alternative: allow
    control and TX audio. Against: two rules for one link; IQ does not fit 10 Mbit/s.
12. **Continuous TX (L13).** A3.4d: from a key to the unkey after which the T/R path returns to
    receive; CW gaps shorter than the hang delay do not end it; the key-down cap measures how
    long one key bit is held.
13. **"Relays settled" (L14).** The condition excludes the T/R relay and the RX attenuator
    during TX, which move inside the key sequence of A3.9a item 4.

## 52. Host power limits with a mean-only detector (rc2-draft review H1)

Status: proposed.

**Problem.** §43 gave conservative mean bounds for the built-in 100 W PEP limit only. A
persistent (C-3) or session limit (`LIMIT_FWD_POWER`, `G7250_LIMIT`) is a PEP value; with a
detector that gives only the mean, comparing it with the mean lets an SSB signal of 10 W mean
reach about 40 W PEP under a 10 W host limit.

**Chosen rule.** Every limit in force, whichever tier and level sets it, is a PEP value *L* and
acts through one table (A3.4c, Table A3-3). With mean only: SSB mean ≤ *L* × `P_ssb_mean` /
100 W; AM mean ≤ min(*L* / 4, 25 W), which bounds PEP to *L* and the carrier to the AM carrier
limit; CW and FM mean ≤ *L*. With PEP the bound is PEP ≤ *L*, plus the AM carrier bound of §43.
Table B8-2 `LIMIT_FWD_POWER`, part C `G7250_LIMIT`, `DRIVE`, C5.10.1 item 5, C8.1, C-C18;
tests T-A3-36, T-C5-36.

- Alternative A: allow host limits only on a PEP detector. For: no scaling rule. Against: the
  host could not limit power at all on a mean-only radio, and the tier rule of 0007 rule 1
  would depend on the detector.
- Alternative B: compare host limits with the mean and keep the scaling for the built-in limit
  only. For: simple to state. Against: a host limit would then be up to 6 dB looser than it
  reads, the unsafe direction.

**Reason.** One mapping for every tier keeps "the limit in force acts" (§6) true on every
detector, and errs on the low side like §43.

Note (§62): the class-based mean bounds do not err on the low side for a signal outside the
assumption of its class (crest factor above 6 dB, a mis-declared class, AM beyond 100 %). §62
adds the PEP estimate from the digital crest factor as the bound for every class without a PEP
detector; the mapping of this section stays as an additional bound.

## 53. Tune power never above the limit in force (rc2-draft review M1)

Status: proposed.

**Problem.** A3.4 rule 5 gives the ATU its own power profile (0007 Decision 4 rule 5), and
A3.9b item 3 set the drive to that profile's tune power. A host or persistent limit below the
profile's tune power was not applied to the tune carrier.

**Chosen rule.** The tune power is the lower of the profile's tune power and the forward-power
bound in force for the TX mode class in force (Table A3-3); the profile may only be stricter
than the limit in force. A3.4 rule 5, A3.9b item 3, B10.9, part C C5.7; T-A3-37, T-C5-37.

- Alternative: refuse `ATU_TUNE` with `NOT_KEYABLE` when the limit is below the profile power.
  For: the ATU always tunes at its design power. Against: a user who set a low limit to protect
  an amplifier or antenna could not tune at all.

**Reason.** A limit in force acts on every TX source (0007 rule 1; §6); tuning at less power is
safe, only slower or less accurate.

## 54. Address change by DHCP during a session (rc2-draft review M2)

Status: proposed.

**Problem.** §44 handled a C-1 change and P2 Set IP. A DHCP renewal with another address or
netmask, the end of a lease or a DHCPNAK (RFC 2131 sections 4.4, 4.4.5), or an address
conflict found while the address is in use ([CH394] section 7.1.7) also change the radio's
address, but no rule covered them.

**Chosen rule.** Each is a change of the radio's own address: it ends a running session (A2.3),
is drop event 9 (`SESSION_CHANGED`) while armed, and the new address, or giving up the old one,
applies only after the unkey and RF gone. A renewal with the same address changes nothing.
A1.11a, Table A3-1 event 9, A2.3, part C C2.5.4 and C5.5.5 row 14; T-A1-35, T-C5-38.

- Alternative: keep the old address until the session ends. For: no session cut. Against:
  after a lease ends or a NAK, RFC 2131 lets the client no longer use the address, and a
  conflict means another host has it; streams would go out under an address that is not ours.

**Reason.** The same handling as Set IP and C-1 (§44); the delay until RF is gone is at most
`t_reset_wait` and keeps relays from moving under RF.

## 55. Exact edge filter for unnumbered hosts (rc2-draft review M3)

Status: proposed.

**Problem.** §35 said "the bit has read 0 for at least 10 ms" without saying from which packet
the 10 ms run, which left the test open.

**Chosen rule.** A 0→1 edge is accepted only if `t_edge` − `t_ref` ≥ 10 ms: `t_edge` the
arrival of the packet with the bit at 1 after a packet with it at 0, `t_ref` the arrival of the
latest earlier packet of the session with that bit at 1 (whether or not it keyed), else the
latest arm confirmation. Times at receipt, 1 ms resolution; the radio ignores 9 ms or less and
accepts 11 ms or more; the reference model applies the rule exactly. B11.6a with a test
vector; Annex X1 D28; T-B11-11, T-B11-13.

- Alternative: measure from the arrival of the first packet with the bit at 0. For: closer to
  "read 0 for 10 ms". Against: a stale 0 packet itself can then shorten or lengthen the
  window; the latest 1 is the packet a stale copy duplicates.

**Reason.** A stale packet is a delayed copy of an earlier 1; measuring from the latest 1 is the
direct test for it, and one time difference is easy to test.

## 56. Numbered-host mode without lockout (rc2-draft review M4)

Status: proposed.

**Problem.** In §35 one packet with a non-zero number switched the session to numbered mode.
A single corrupt or spoofed packet with a high number, or a host that restarts its numbering,
then had every later packet discarded until the session ended: the host loses control,
including PTT release.

**Chosen rule.** Numbered mode engages with the third of three consecutive packets with
non-zero numbers, each newer than the one before (RFC 1982); until then the unnumbered rule
(§55) applies. In numbered mode a packet not newer than the last accepted one is discarded
and counted; number 0 is never newer. The fifth such packet in a row, or a packet older than
the last accepted one by more than 2¹⁶, resynchronises: the radio returns to unnumbered mode,
logs and counts it, and acts on that packet except that a 0→1 edge in it is ignored and not
latched. A 0→1 edge in a discarded packet is never accepted. B11.6a; Annex X1 D28;
T-B11-14, T-B11-15.

- Alternative A: never resynchronise within a session. For: a stale packet can never key.
  Against: the lockout described above, which keeps a keyed host from unkeying except through
  the keyed timeout.
- Alternative B: resynchronise on the first packet that is not newer. For: no lockout at all.
  Against: every duplicated packet would end the protection.

**Reason.** Three good packets show a numbering host; five bad ones in a row (about 500 ms at
the recommended 100 ms rate) or a large jump show a restart, not reordering. No edge from the
packet that resynchronises keeps a stale packet from keying through the resynchronisation.

## 57. Start and bounds of the DUC underrun timer (rc2-draft review M5)

Status: proposed.

**Problem.** B10.5 did not say when an underflow starts (at the key, at the first sample, or at
an empty FIFO), what the DUC sends while the FIFO is empty, or a lower bound for the underrun
time; a too-short value would cut a host that starts its I&Q with the PTT edge.

**Chosen rule.** The underflow starts at the key if the FIFO is empty then, else when the FIFO
runs empty while keyed; each sample ends it. While the FIFO is empty the DUC gets zeros. The
underrun time is at least the key latency (`t_rf_off` + `t_settle`, the bound of A3.9a item 3)
plus one DUC packet period (240 samples at 192 ksps = 1.25 ms, B10.7) and at most the
`KEYED_TIMEOUT` in force. B10.5; Annex X1 D8; Annex X2 C20; T-B10-32.

- Alternative: start the timer at the first sample after the key. For: a host that starts I&Q
  late is never cut. Against: a host that keys and never sends I&Q would hold the key until the
  keyed timeout or the maximum TX time, and the underrun check would not catch a TX chain that
  hangs before its first packet.

**Reason.** Timing from the key catches a TX chain that never starts; the lower bound keeps a
correct host from being cut; zeros give no RF and no stale signal.

## 58. Destination of the takeover notices (rc2-draft review M6)

Status: proposed.

**Problem.** §29 and §48 said the final `TX_ARM_STATE` goes to the old owner but not to which
port, nor whether the notices share the `NOT_OWNER` answer limit of B8.5.

**Chosen rule.** The three copies and the repeated notice are register packets from local port
7250 to the old owner's IP address and the register destination its session had at the
takeover: General bytes 31–32 if non-zero, else its source port (B8.1; [P2] General packet
bytes 31–32). They are not `NOT_OWNER` answers and do not count against that limit, nor it
against them. A2.4, B8.5; T-A2-13.

- Alternative: send the notices to the packet's source port. For: reaches the socket that just
  sent. Against: a host that set bytes 31–32 listens for register packets on that port, as for
  every other push of its session (B8.1).

**Reason.** The notice is the last register push of the old session and goes where all of them
went; separate limits keep a write flood from suppressing the notice and the other way round.

## 59. Commanded reset with RF present (rc2-draft review M7)

Status: proposed.

**Problem.** §40 waits until RF is gone before a commanded reset, without a bound. With a
power-measuring design and RF that does not go (a stuck PA), the command would hang, or a
reset would start with RF present, the case §40 forbids.

**Chosen rule.** The wait is bounded by `t_reset_wait` = 2 s from the unkey (or from the
command if not keyed), longer than `t_rf_off` (HIS-12). If RF is not gone by then, the radio
does not reset: it logs, enters or stays in the fault state (`RF_NOT_KEYED`, class 2), keeps RX
and replies with the new status 59 "reset refused: RF present". The same holds for every
commanded reset, including the restart after an abandoned update, which then stays in the
update state. A1.9, Table A1-3, A1.8, part C C2.8; T-A1-36, T-A1-37, T-C2-13.

- Alternative A: reset after the bound anyway. For: the radio always restarts. Against: the
  state of the PA, SEND and relay lines during a reset is unknown (HIS-13), and RF is already
  present.
- Alternative B: reply with status 50 (refused while armed or transmitting). For: no new code.
  Against: the radio is neither armed nor keyed at that point; a tool would wait for a disarm
  that has happened.

**Reason.** Never reset with RF present; a distinct status tells the tool that the radio needs
a visit (power cycle), not a retry.

## 60. What a factory reset restores (rc2-draft review M8)

Status: proposed.

**Problem.** 0008 C-5 resets "network configuration and secrets" and §31 keeps the limits; the
other configuration items (C-2, C-6, C-7, the TCI port), the log and the counters were not
listed.

**Chosen rule.** Table A1-4 (A1.6a): C-1 network, C-2 default level (level 1), C-5 secret (new
first-secret window), C-6 region (the intersection of all regions, 0020 §23), C-7 allow-list
(empty) and the TCI port (50001) return to their factory defaults; C-3 persistent limits, the
log, the fault and reset counters, `TRIP_COUNT` and the firmware images are kept; write session,
challenges and stored replies are discarded as at every reset. T-A1-39.

- Alternative A: keep the region. For: a radio set for its region stays usable after a reset.
  Against: a radio given away or moved keeps the TX ranges of another region; the factory
  default is the narrowest set and so the safe one (0020 §23).
- Alternative B: also return the C-3 limits to the built-in values. For: a true factory state.
  Against: §31: a factory reset is a recovery path for a lost secret and should not loosen the
  safety settings of an installation.

**Reason.** A factory reset restores reachability (network, secret, allow-list, port) and
the safe defaults (region, level), and loosens nothing that protects the station; logs and
counters are evidence and are kept.

## 61. rc2-draft review small fixes (review LOW)

Status: proposed.

1. **Inhibits on TCI (L1).** The `inhibits` text of `G7250_TX_STATE` (part C C5.5.3) names
   both inhibits of `LIMIT_INHIBIT`: bit 3 `LIMIT_PA_TEMP` and bit 5 `LIMIT_SUPPLY_VOLTAGE`
   after an over-voltage or under-voltage `UNKEY` (§42). T-C5-39.
2. **Row 5 of C5.5.5 (L2).** "The P2 drop reasons of Table B8-3" instead of "1–13", which left
   out the limit drops 0x40 + id.
3. **Drop reason after a reset (L3).** After any reset `TX_ARM_STATE` [23:16] reads 5 `RESET`
   until the next drop (Table A3-1 event 5, Table B8-2). T-A3-38.
4. **Reply after the unkey (L4).** `RESTART`, `FACTORY_RESET` and `SWITCH_LEVEL` unkey and
   disarm first, then reply (A1.9, A2.5a); a repeat during the wait for RF gone gets status 1.
   This amends the order of §40 (reply, unkey, RF gone, disarm) to: unkey and disarm, RF gone
   (bounded by §59), reply, relays, reset; and the step order of §9 for `SWITCH_LEVEL`.
   Alternative: reply first. For: the fastest answer. Against: the host would see "OK" while
   the radio still transmits, and the reply cannot carry status 59 (§59). T-A1-38, T-A2-04.
5. **CWX host note (L5).** B10.5a: an iambic string or run of dots longer than 1 s per held
   paddle is cut; hosts release the paddle bits between characters or use DUC I&Q or TCI CW
   text.
6. **Arm and `UPDATE_BEGIN` (L6).** The arm acceptance and `UPDATE_BEGIN` are one atomic
   decision; one wins, the other is refused (arm `MAINTENANCE`, update status 50) (A1.8,
   B10.2, part C C2.8). Alternative: allow both and let the update disarm. Against: §8, an
   update never disarms. T-A1-40, T-C2-12.

## 62. PEP estimate from the digital crest factor (rc2 review H1)

Status: proposed.

**Problem.** §43 and §52 bound forward power with a mean-only detector by class-based mean
bounds (SSB mean ≤ *L* × `P_ssb_mean` / 100 W, CW and FM mean ≤ *L*, AM mean ≤ min(*L* / 4,
25 W)). These hold PEP ≤ *L* only for a signal within the assumption of its class. SSB voice
with a 12 dB crest factor reaches about 4 × *L* PEP under the SSB bound; SSB I&Q sent under a
declared class CW reaches about 4 × *L*; AM modulated beyond 100 % exceeds *L* under *L* / 4.
The rc2 text called the bounds conservative ("may reduce more than needed, never less"),
which is false.

**Chosen rule.** The firmware feeds every sample to the DUC, so it knows the envelope before
the PA. Over the same sliding 100 ms window as the coupler, aligned by the DUC-to-coupler delay
(HIS-18), the safety core computes the digital crest factor *CF* = max(I² + Q²) / mean(I² +
Q²) of the samples fed to the DUC, for every TX source (host I&Q after drive scaling, keyer
waveform, tune carrier). PEP estimate = measured mean × *CF*. Without a PEP detector the
safety core enforces PEP estimate ≤ *L* for every class; the class-based mean bounds of Table
A3-3 stay as additional bounds, never instead. The AM carrier bound with mean only (mean ≤
25 W) is kept: the mean of AM is never below its carrier. A TX path whose RF does not come
from DUC samples cannot key without a PEP detector (HIS-18). The estimate assumes the analogue
chain does not raise the crest factor (compression lowers it, so the estimate errs high);
filter overshoot and inter-sample peaks go into the margin (HIS-11, HIS-12). A3.4c, Table A3-2,
Table A3-3 and its notes, Table B8-2 `LIMIT_FWD_POWER`, Annex X1 D10; tests T-A3-39 (12 dB
voice), T-A3-40 (CW declared, SSB I&Q), T-A3-41 (AM at 150 %); T-A3-33 qualified. Amends the
"conservative" statement of §43 and §52.

- Alternative A: require a PEP detector for M4 (HIS-11). For: measures the real PEP, also
  after the analogue chain. Against: depends on the hardware; if the existing design has a
  mean-only detector, M4 would be blocked although a firmware-side bound exists.
- Alternative B: keep the class mapping and lower `P_ssb_mean` to cover 12 dB voice. For:
  simple. Against: still wrong for a mis-declared class or overmodulated AM, and costs 6 dB on
  every normal SSB signal.

**Reason.** The crest factor is known exactly on the digital side at no hardware cost, and
mean × *CF* is the PEP of the signal actually sent, whatever the declared class. Keeping the
class bounds as an extra can only lower power, so nothing becomes looser than rc2.

## 63. DUC FIFO while unkeyed (rc2 review M1)

Status: proposed.

**Problem.** §32 empties the DUC FIFO at every unkey, but nothing bounded what a host that
streams DUC I&Q continuously fills it with while unkeyed. At the next key the radio could
transmit audio seconds old, and the FIFO depth while unkeyed was undefined.

**Chosen rule.** While unkeyed the G7250 keeps only the owner's most recent DUC I&Q: at most
4800 samples (25 ms at 192 ksps, 20 packets), and only samples received within the last
25 ms; older samples are dropped, oldest first, and counted. The first sample transmitted at
a key is at most 25 ms old. While keyed the capacity is HIS-18 and a full FIFO discards whole
packets (B11.7). B10.7, B11.7, Annex X2 C20; T-A3-26 extended to a continuously streaming
host.

- Alternative A: drop all DUC I&Q while unkeyed. For: the simplest bound, age 0. Against: the
  first samples of every over, sent with or just before the PTT edge, are lost; the underrun
  timer then starts at every key.
- Alternative B: keep up to the FIFO capacity. For: no extra rule. Against: the age at the key
  depends on the capacity (HIS-18) and can be long.

**Reason.** 25 ms keeps a host's lead with its PTT edge and bounds staleness to a value a
listener does not notice; dropping oldest keeps the newest audio.

## 64. TX settings at session end and takeover (rc2 review M2)

Status: proposed.

**Problem.** A2.4 and A3.6 reset the arm, mode class, limits and `KEYED_TIMEOUT`, but not
the TX settings of the General and DUC-specific packets: PA enable (General byte 58), CW
select, break-in, hang delay, RF delay, keyer settings, EER, the DUC-rate refusal and the RX
step attenuator during TX. A new owner inherited them without knowing.

**Chosen rule.** At every session end and takeover, after the unkey, these return to their
session-start values, the same as at power-on: PA enable 0, and every DUC-specific field as a
packet of zeros read through Table B10-1 (CW select, keyer bits, break-in and EER 0; hang
and RF delay 0 ms; speed and weight 0, so CWX forms no element; rate and bits read as 192 and
24; ramp 8 ms; step attenuator during TX the A3.6 value, HIS-07). The new owner sets its own
values in its takeover packet, set-up phase or later packets. A2.4 step 1, A3.6, new A3.6a with Table A3-4,
B5.7, Tables B7-1 and B10-1, B10.9, B10.10, Annex X1 D5, D30; T-A2-14.

- Alternative: keep the old owner's settings, as RX settings are kept. For: a host that
  takes over from itself keeps working without resending. Against: a new host may key with
  another host's break-in, RF delay for an external amplifier, or PA enable it never set.

**Reason.** Reset is the safe default (0007 Decision 5), and a host must send a General
packet in its session before it can arm anyway (§13, §34).

## 65. Allowed requesters on level 1 (rc2 review M3)

Status: proposed.

**Problem.** A3.1a named "the owner" as the requester on level 1, but KEY is a local input,
and B10.1 listed "any controller request" as a TX request, against A3.7 and 0007 Resolved 6.

**Chosen rule.** On level 1 the allowed requesters are the owner's PTT and CWX bits, the
owner's `ATU_TUNE`, and one local source: KEY, only while the owner has set DUC-specific
byte 5 bit [1] in this session, under its arm. No controller request keys on level 1; B10.1
no longer lists one. A3.1a, A3.7, B10.1, B10.9; T-A3-42.

- Alternative: treat KEY as a controller request and refuse it on level 1. For: no local
  source at all. Against: removes hardware CW, which [P2] DUC-specific byte 5 bit [1] offers
  and 0007 Decision 6 keeps.

**Reason.** Names the one local exception explicitly and ties it to an owner setting that is
reset at every session end (§64).

## 66. ATU tune cycle and the TX RF-path state (rc2 review M4)

Status: proposed.

**Problem.** A3.9b started the tune carrier without the A3.1b switch to the TX state, so with
split or cross-band the carrier went through the receive-frequency state; item 7 returned the
ATU to the state for the TX frequency, against A3.1b's unkeyed rule.

**Chosen rule.** The cycle first switches the RF path to the A3.1b TX state for the effective
TX frequency and waits for the relays to settle. At every end, once RF is gone, the RF path
returns to the unkeyed state for the receive frequency; a tuned result is stored for the TX
frequency (HIS-08) and recalled by the next key under A3.1b; a cycle that did not end tuned
stores nothing. A3.9b items 2 and 7, B10.9; T-A3-43, T-B10-30 adjusted. Amends §38.

- Alternative: let the cycle tune in whatever state is in use. For: no relay movement before
  the carrier. Against: tunes the ATU for the wrong filter and band with split.

**Reason.** The tune cycle is a key like any other (§22), so A3.1b applies to it.

## 67. SWR cap and CW break-in (rc2 review M5)

Status: proposed.

**Problem.** A3.4a held `P_swr` "until the unkey". With CW break-in every element ends with an
unkey, so the cap lifted at every element and the next element started at full power into the
bad load.

**Chosen rule.** The cap holds to the end of the continuous transmission of A3.4d, until an
unkey after which the T/R path returns to receive (after the hang delay). A3.4a, Table A3-2;
T-A3-11 extended.

- Alternative: hold the cap for a fixed minimum time, for example 2 s. For: independent of
  the hang delay. Against: a new constant, and a hang delay longer than it still lifts the cap
  between elements.

**Reason.** Uses the definition of continuity already used for the TX time limit (§51).

## 68. Bound on every wait for RF gone (rc2 review M6)

Status: proposed.

**Problem.** §59 bounded the RF-gone wait only for commanded resets. After a normal unkey, a
session end or a fault, a detector that kept reading RF at or above `P_rf_off` but below the
"RF while not keyed" threshold would hold relays and pending actions for ever, without a fault.

**Chosen rule.** Both. Every RF-gone wait is bounded by `t_reset_wait` = 2 s from the unkey;
at the bound the G7250 enters fault `RF_NOT_KEYED` (class 2) or stays in it and logs; relays
still do not move while RF is present; actions that move no relay proceed (session end, address
change, level switch); a commanded reset gets 59. In addition the "RF while not keyed"
threshold is not above `P_rf_off` and `t_blank` is shorter than `t_reset_wait`. A3.9a item 1a,
A1.9 step 2, Table A3-2; T-A3-44.

- Alternative A: only the threshold rule. For: no new timer. Against: leaves the timing to two
  TBD values.
- Alternative B: only the timer. For: one rule. Against: RF between the thresholds would be
  tolerated for 2 s without a reason.

**Reason.** Two independent guards; each alone closes the gap.

## 69. Factory reset atomicity (rc2 review M7)

Status: proposed.

**Problem.** A1.6a did not say when the items of Table A1-4 are written. With a reset refused
by status 59 (§59), a secret cleared before the refusal would open a first-secret window on a
radio that stays up.

**Chosen rule.** The items are written only as part of a reset that starts, after RF gone,
between steps 4 and 5 of the commanded reset. A refusal with 59 changes nothing of Table A1-4;
only the log entry and the unkey and disarm of step 1 remain. A1.6a; T-A1-41.

- Alternative: write first, then reset. For: simple. Against: the refusal case leaves the
  radio claimable by anyone on the LAN.

**Reason.** All or nothing; the refusal case is the one where the radio stays reachable.

## 70. Set IP from outside the subnet (rc2 review M8)

Status: proposed.

**Problem.** B11.15 kept Set IP "as before" from any source, and C13 accepts unicast and
directed broadcast; a host behind a router could change the address and cut a session,
although no P2 session can come from there.

**Chosen rule.** Unicast and directed-broadcast Set IP is accepted only from a source inside
the radio's subnet; the limited broadcast is accepted from any source, because routers do not
forward it (RFC 1812 section 5.3.5.1) and a host with a wrong address set-up needs it. B3.9,
B11.15, A1.10, Annex X1 D29, Annex X2 C13; narrows the risk of 0008 S7 to the link and the
subnet. T-B3-32.

- Alternative: accept Set IP only from inside the subnet, broadcast included. For: one rule.
  Against: [P2]'s recovery path for a radio on the wrong subnet would no longer work.

**Reason.** Keeps [P2]'s broadcast use (0008 point 6) and removes the routed case only.

## 71. Total caps on management replies (rc2 review M9)

Status: proposed.

**Problem.** Identification is answered to any source, also off-subnet and broadcast, with up
to 1400 bytes for an 18-byte request; the limit of §16 was per source only, so spoofed sources
multiplied it.

**Chosen rule.** In addition to 20 per second per source: at most 100 management replies per
second in total, of these at most 50 identification replies, and of those at most 10 to sources
outside the subnet; excess dropped and counted. A1.10, B11.14, Annex X1 D25; T-A1-42.

- Alternative: answer identification only inside the subnet. For: no amplification beyond the
  subnet. Against: 0008 I-6 answers broadcast identification, and a tool on another subnet
  could no longer find the radio.

**Reason.** Bounds the amplification to about 1.1 Mbit/s worst case (100 × 1400 bytes per
second), without dropping a function; management is not safety-relevant (A1.9).

## 72. Wrap-around and releases in discarded High Priority packets (rc2 review M10)

Status: proposed.

**Problem.** B11.6a says 0 is never newer, but T-B11-10 accepted 0xFFFFFFFF → 0 as newer.
And a PTT 1→0 in a discarded packet was not followed, so a real release in a packet discarded
during the run-up to a resynchronisation was ignored until the keyed timeout.

**Chosen rule.** 0 stays never newer; a numbering host skips 0 at the wrap (0xFFFFFFFF → 1).
A PTT bit or CWX request at 0 in a discarded packet while keyed by it unkeys (reason 1, arm
kept); after that the bit counts as 1 until an accepted packet reads 0, so a stale release
never re-keys. B11.6a, Annex X1 D28; T-B11-10 fixed, T-B11-16.

- Alternative A: make 0 newer than 0xFFFFFFFF. For: hosts may wrap naturally. Against: 0 is
  also [P2]'s "unnumbered" value; it would make an unnumbered packet newer in numbered mode.
- Alternative B: unkey only from the next accepted packet. For: a stale 0 cannot cut a
  transmission. Against: a real release can be delayed up to the keyed timeout (500 ms).

**Reason.** The unkey is the safe direction; the result matches unnumbered mode, where a
stale 0 also ends the transmission and the following 1 fails the 10 ms test.

## 73. rc2 review small fixes (review LOW)

Status: proposed.

1. **Order for C-1 and C-3 (L1).** Unkey and disarm first, then reply; C-1 applies the address
   after RF gone, C-3 applies the limit before the reply (A1.6, A1.9; as §61). T-A1-30.
   Alternative: reply first. Against: the host sees "OK" while the radio still transmits.
2. **Drop reason of a commanded reset (L2).** `RESTART` and `FACTORY_RESET` while armed drop
   with `MAINTENANCE` (Table A3-1 event 11), also when refused with 59; after the reset
   `RESET`. Alternative: `RESET` before the reset. Against: the reset may not happen (59).
   T-A3-38.
3. **Drop events while unarmed (L3).** No change to `TX_ARM_STATE`, no new token; exceptions:
   `RESET` after any reset and a new token per session. A processor watchdog reset reads 5
   `RESET`; its fault shows in `SAFETY_STATE` and `FAULT_CODE`. T-A3-38, T-A3-47.
4. **Token across resets (L4).** A boot counter in non-volatile memory, incremented once per
   start, forms part of every token; a random part may be added (HIS-20). B10.2 item 5, Table
   B8-2; T-B8-17. Alternative: a random token only. Against: no guarantee without a source
   (HIS-20), and still only probable.
5. **`LIMIT_<name>` = 0 (L5).** Kept as "back to the persistent value"; documented in Table
   B8-2 and after it. Alternative: a distinct reset value (0xFFFFFFFF). Against: changes the
   meaning of an accepted register (0020 §10). T-B8-20.
6. **`LIMIT_SWR` and `ATU_TUNE` precedence (L6).** `LIMIT_SWR` is checked against the
   persistent S2; `ATU_TUNE` rejects in the order `BUSY`, `NOT_OWNER`, `BAD_VALUE`,
   `NOT_ARMED`, no-op, `KEYED`, `NOT_KEYABLE`. A3.9b item 1, Table B8-2; T-B8-18.
7. **`CAP_REQUEST` on a slow link (L7).** Yes, the record is answered as on a fast link, plus
   the `LINK_STATUS`/`STREAM_STATUS` answer, at most once per 100 ms per source and 10 per
   second in total. B5.8; T-B4-16.
8. **Unasked record vs `CAP_REQUEST` limit (L8).** Separate limits: the unasked record is left
   out only after another unasked record to the same destination within 1 s; a `CAP_REQUEST`
   answer never suppresses it. B4.4 item 2; T-B4-07.
9. **SEND during the CW hang delay (L9).** SEND, T/R relay and RX attenuator during TX stay in
   TX position during the hang delay; released after it. A3.9a item 4, B10.9; T-A3-46.
   Alternative: release SEND at every element. Against: an external amplifier would switch at
   every element.
10. **DDC0 change during the bounded wait (L10).** Deferred to the next unkey; does not refuse
    the key. A3.9a item 3; T-A3-45.
11. **TX low-pass filter while unkeyed (L11).** Where HIS-07 allows keeping it set for the TX
    frequency, that filter follows DUC0 while unkeyed; no other relay does. A3.1b; T-A3-28.
12. **Frequency encoding mismatch (L12).** General byte 37 bit [3] ≠ discovery byte 21: DDC0
    does not run, no TX request keys, `STREAM_STATUS` reason 13 (new), logged. B3.8, A3.1a,
    Tables B7-1 and B8-3; T-B7-06. Alternative: ignore bit [3]. Against: the host would
    compute every frequency in the wrong encoding, TX included.
13. **DDC0 without a DDC-specific packet (L13).** Not enabled, reason 1; status packets run.
    Also lowers the spoofed-run amplification of B11.14. B5.2; T-B6-26, T-B5-11.
    Alternative: stream at 48 ksps. Against: data to a host that never asked.
14. **Set-up phase fields (L14).** B5.1a item 2 covers every field acted on, among them
    General bytes 31–32 and 37.
15. **PA disabled blocks all RF (L15).** Listed as Annex X1 D30.
16. **Management and relays (L16).** The only relay movement a management command causes is
    the return to the A3.6 set after RF gone. A1.9, A3.9.
17. **Management socket and DHCP (L17).** A1.2 names the borrowing of A1.11 as the exception.
18. **C-7 and the TX state (L18).** A C-7 list that closes the arm holder's TCI connection
    unkeys and drops with `HOLDER_LOST` before the reply. A1.9; T-A1-45.
19. **Link speed and the record (L19).** B4.7 no longer lists a change of link speed.
20. **Reflection loops (L20).** No answer to management datagrams with type ≠ 1, to datagrams
    to port 1024 from source port 1024, or to non-owner register packets from source port
    7250. A1.4, B3.2, B8.5, B11.14, Annex X1 D25; T-A1-43, T-B3-33, T-B8-19. Alternative: rate
    limits only. Against: a loop at the rate limit runs for ever.
21. **Status 34 (L21).** Sent only for the authentication-failure limit (5 failures in 10 s
    per address, 10 s hold); requests above reply limits get no reply. A1.10; T-A1-44.
22. **Takeover notice copies (L22).** Identical register pairs; each copy has its own sequence
    number. A2.4; T-A2-10.
23. **Editorial (L23).** A1.8 no longer says "receive-safe" for a state in which RX stops;
    Annex X3 ids in order (T-A1-28, T-A3-14, T-A3-15 moved).

## 74. CW keyer elements and the break-in hang delay (rc3-draft review M1)

Status: proposed.

**Problem.** A3.1a made the key rule apply to an edge of a TX request, but a keyer (CWX
paddles, the hardware keyer behind KEY, TCI `KEYER` and CW text) forms many elements from one
request; it was open whether every element is checked, and whether a failed check is held
until it clears. A3.4d counted the hang delay as part of one continuous transmission for the
time limit, and §73 item 9 kept SEND and the T/R relay in TX position during it, but A3.9,
A3.9a and A3.9c spoke of "keyed" as the PA being keyed. In a gap between elements the radio
was therefore unkeyed for the relay rules while SEND and the T/R relay were still in TX
position: a deferred RF-path change could be applied, or an `ATU_TUNE` start, under an
asserted SEND.

**Rule.** Every keyer-generated element (CWX paddles, hardware keyer from KEY, and on TCI
`KEYER` and CW text) is a key subject to every A3.1a condition; a failed condition stops the
keyer and a new request edge is needed (not latched). For RF-path purposes (A3.9, A3.9a,
A3.9c and the tune-cycle start) "keyed" means the A3.4d continuous transmission including the
hang delay: a change that needs another TX RF-path state, a mode-class change or an RF-path
relay change arriving in a gap ends the hang (unkey reason 6 or 10 as applicable), waits for
RF gone, releases SEND and returns T/R, and only then moves relays or applies the change;
receive-frequency-only changes stay deferred until the hang ends; PA enable cleared in a gap
ends the hang (reason 7). Detail choices: an owner's register write that ends the hang is
answered once the change is applied; a controller ANT or ATU button press stays ignored
during the hang delay, as while keyed (A3.7: the controller is not a requester on level 1).
The same rule is used in part C. Applied in A3.1a, A3.1b, A3.4d, A3.9, A3.9a items 1 and 4,
A3.9b, A3.9c, B10.5a, B10.9 (KEY, SEND, internal ATU), B10.10, Annex X1 D31; T-A3-48,
T-A3-49.

**Alternatives.**

- Defer every RF-path change in a gap until the hang delay ends, as while the PA is keyed.
  For: no extra unkey; the operator's CW flows on. Against: a host that retunes during fast
  break-in waits up to the hang delay with no sign of why; with a long hang delay the retune
  appears lost; the mode class could not change at all during a CW over.
- Treat the gap as unkeyed (apply changes at once). For: simplest firmware. Against: relays
  and the mode class would change while SEND is asserted and an external amplifier is still
  switched to transmit; the opposite of §73 item 9.

**Reason.** The hang delay is the time an external amplifier and the T/R path stay in TX; it
must be protected exactly like the keyed state, but a host change must not wait silently.
Ending the hang delay with a visible unkey reason gives the change at once in the safe order
(A3.9a item 4). Checking every element closes the gap in which a keyer could keep sending
after PA enable is cleared or an inhibit is set.

## 75. Management write session idle timer (rc3-draft review M2)

Status: proposed.

**Problem.** A1.10 ended the write session "after 60 s without a request". Any request
counted, so an unauthenticated read, or a forged datagram with the holder's address and port,
could keep the session open and lock other writers out with status 35 for as long as it
continued.

**Rule.** Only an authenticated request from the holder whose HMAC verifies refreshes the 60 s
idle timer. Reads (`GET_STATS`, `IDENTIFY`, other unauthenticated commands), `GET_CHALLENGE`,
any unauthenticated request and any request that fails authentication never do. A1.10,
B11.10; T-A1-15.

**Alternatives.**

- Any request from the holder's address and port refreshes it. For: a monitoring tool of the
  holder keeps its session alive with reads. Against: the address and port can be spoofed
  without the secret; a read is no evidence that the writer is still there.
- No idle timer, only `END_WRITE_SESSION`. For: no timer. Against: a crashed writer locks out
  every other writer until a reset (0020 §24).

**Reason.** The timer guards the lock that only an authenticated writer can take; only the
same proof should extend it.

## 76. Restart with the run bit only (rc3-draft review M3)

Status: proposed; partly reversed by §78 (the carry-over of RX-side settings).

**Problem.** B5.4 allowed a restart "by a new High Priority packet with run set". B5.1a
empties the set-up at every session end and B5.2 treats DDC0 as not enabled without a
DDC-specific packet, so a host that restarts with the run bit only gets a session with
`STREAM_STATUS` DDC0 reason 1, PA disabled and the TX settings of Table A3-4, with nothing in
B5.4 telling it why.

**Rule.** After any session end a host MUST resend its General, DDC-specific and DUC-specific
packets, in its set-up phase (B5.1a, which counts only packets received since the session
end) or in the session. A run bit alone gives the [P2] defaults: DDC0 not enabled
(`STREAM_STATUS` reason 1), Table A3-4, and `WATCHDOG_DISABLED` for an arm until a General
packet arrives. The takeover remains the one carry-over of RX-side settings (A2.4 step 4).
B5.4, B5.1a item 3, Annex X2 C21; T-B5-16.

Correction (§78). The rule above cited [P2] "Detailed operation" as describing the restart
as a re-initiation of all C&C settings. That misquotes it: [P2] gives two restart paths, a
High Priority packet with the RUN bit set "if the same network session is still active", or
a Discovery exchange followed by re-initiation of all C&C settings. §78 replaces the part of
this rule that drops the RX-side settings; the reset of the TX settings (Table A3-4) and the
need for a new General packet before an arm stand.

**Alternatives.**

- Keep the DDC-side RX settings of an ended session for a later session of the same host
  (address and port). For: a host that only toggles run gets its stream back as before.
  Against: the radio would have to keep a second, per-host copy of state that A3.6 resets at
  every session end; a different program on the same port would inherit settings it never
  sent; it contradicts the re-initiation of [P2].
- Keep every setting, TX included. Against: undoes §64.

**Reason.** One rule for every session start: what counts is what the host sent since the
last session end. The status reason 1 already tells a host what is missing. (Superseded for
the RX side by §78: the reason rested on the misquotation corrected there.)

## 77. rc3-draft review small fixes (review LOW)

Status: proposed.

1. **Abandonment after abort or verify (L1).** The 10-minute rule of A1.8 also runs after
   `UPDATE_ABORT` and after `UPDATE_VERIFY` without `UPDATE_ACTIVATE`; the radio restarts into
   the running image as a commanded reset. T-A1-46. Alternative: stay in the update state
   until `RESTART`. Against: RX stays unavailable until someone visits the radio or the
   management channel, which §51 removed for an unfinished transfer.
2. **Takeover notice copies asynchronous (L2).** The three copies of A2.4 step 1 are sent in
   the background; steps 2–5 do not wait for the second and third. T-A2-15. Alternative: send
   all three first. Against: 20 ms without streams for the new owner, and a PTT edge in the
   takeover packet delayed by it.
3. **Citation (L3).** Table A3-1 event 11 cites A1.6 C-3 for the change of limits, A1.8 for
   the update.
4. **Cache churn (L4).** Known limit in B11.14: the per-host caches (challenges, stored
   replies, set-up; 4 entries each, LRU) can be churned by a source inside the subnet. No
   safety effect. Alternative: larger caches. Against: RAM, and any finite cache can be
   churned; the subnet rule of B11.15 and A1.10 S4 already bounds who can do it.
5. **`ATU_TUNE` = 0 (L5).** From the owner always accepted, also while the cycle keys and
   whatever the arm state; a no-op when no cycle runs. A3.9b item 1, B10.9; T-A3-50.
   Alternative: reject 0 while unarmed with `NOT_ARMED`. Against: an abort must never be
   refused.
6. **Oversize management request (L6).** A request whose header declares more than 1000
   bytes (18 + *N*, plus 32 with the HMAC flag) gets status 19, decided from the header before
   the length check, because the 1 KB receive buffer may truncate the datagram; a datagram
   above 1000 bytes with a smaller *N* gets 17 from the length check. A1.4 and the precedence
   order of Table A1-3; T-A1-47. Alternative: status 17 for every oversize datagram. Against:
   the host cannot tell "too large" from "corrupted", and status 19 exists for this case.

## 78. Restart by the run bit keeps the RX side (rc3 review H1)

Status: proposed. Reverses part of §76.

**Problem.** §76 made every session end drop all settings and justified this with [P2]
"Detailed operation", read as describing the restart as a re-initiation of all C&C settings.
[P2] says instead: "The session can be re-started either by sending a High Priority Packet
with the RUN bit set, if the same network session is still active, or a Discovery exchange
followed by re-initiation of all C&C settings and thence a High Priority Packet with the RUN
bit set" ([P2] "Detailed operation"). The first path presumes that the settings of the
session survive. A host that recovers from a network outage by its unchanged run = 1
keepalive, as [P2] intends ("In order to recover from a network interruption …"), got a
session without DDC0 under §76. A2.3 also spoke of RUN "from 0 to 1" without saying whose
edge counts, so a host that never cleared its run bit could read itself as unable to restart.

**Rule.**

1. A2.3: a session starts at a High Priority packet with run = 1 while no session runs; "0
   to 1" is the radio's RUN state; no 0→1 edge in the host's own run bit is needed.
2. B5.4: after a stop, a watchdog standby or a link loss (also a slow link), the RX-side
   settings stay in force for the same source IP address and UDP port: every General field
   of Table B7-1 other than byte 38 bit [0] and byte 58 bit [0], the DDC-specific packet,
   and the receive state of the High Priority packet (DDC0 frequency, front end), as at a
   takeover. The next High Priority packet with run = 1 from that host restarts the session
   with them; set-up packets kept since the end apply on top.
3. Not carried over: the TX settings of Table A3-4 (§64), `TX_MODE_CLASS`, `KEYED_TIMEOUT`,
   the session limits, and General byte 38: an arm needs a General packet of the new
   session or its set-up phase with byte 38 bit [0] set (B10.2 item 3; §13, §34).
4. "The same network session" ends at a reset, a firmware update, a level change and a
   change of the radio's address or netmask; after these, and for any other host, a run bit
   alone gives the [P2] defaults of B5.2 (DDC0 not enabled, `STREAM_STATUS` reason 1) and the
   host takes the second path of [P2].
5. A3.6 applies only its TX-side part at the session ends of item 2; its RX-side part
   applies when another host starts the next session.

Applied in A2.3, A3.6, A3.6a, B5.1a item 3, B5.2, B5.4, B5.6, B5.8, Annex X1 D32 (the reset
of the TX side and the arm condition at a restart are the deviation), Annex X2 C21 (what
"the same network session" means); T-B5-13, T-B5-16, T-B5-17, T-B5-18.

**Alternatives.**

- Keep §76 (nothing survives). For: one rule, no per-host state. Against: contradicts the
  first restart path of [P2]; a standard host recovering from an outage gets no RX data
  without knowing why.
- Keep the TX settings too. For: the closest reading of [P2]. Against: undoes §64; a host
  that lost the link for over 1 s should not find PA enable, break-in and CW select still
  set; the arm, which is reset anyway, protects TX, but the TX settings are the ones a host
  most needs to re-check after an outage.
- Carry the RX side over to any host, as at a takeover. For: simplest state. Against: a
  session start after an end is not a takeover; another host would get DDC0 data on settings
  it never sent, against B5.2 (§73 item 13); the register destination of General bytes 31–32
  belongs to the old host.
- Require a 0→1 edge of the host's run bit. Against: the host that recovers by its
  keepalive never sends one; [P2] asks only for "a High Priority Packet with the RUN bit set".

**Reason.** [P2] gives the run-bit restart for the case where the network session is still
active; that is exactly the outage the watchdog guards against. Receive is not a safety
function, so keeping its settings costs nothing; transmit is, so its settings and the arm
start afresh, as they do at a takeover.

## 79. Takeover of an unarmed owner; token at session end (rc3 review M1)

Status: proposed.

**Problem.** A3.2 said a drop event while not armed changes no field of `TX_ARM_STATE`,
issues no token and pushes nothing. A takeover of an unarmed owner therefore sent no notice,
so the host guidance of A2.4 (stop on a `TAKEOVER` notice) failed for exactly the host that
most often loses the radio: one that only receives. A3.6 at the same time gave every session
end a new token, while T-A3-47 required "no new token" for the watchdog stop.

**Rule.**

1. A takeover always runs A2.4 step 1 in full: `TX_ARM_STATE` reads disarmed with drop
   reason 4 `TAKEOVER`, a new token, three copies and the repeated notice, armed or not. An
   explicit exception in A3.2.
2. Token: a new token at every session end, armed or not (A3.6), pushed at the next session
   start (B10.2 item 1). A drop event while not armed that does not end the session (`TX_ARM`
   = 0, a C-3 change, a fault entry) issues none.

Applied in A2.4 step 1, A3.2 (drop events while not armed, exceptions 1–3), Annex X1 D5;
T-A2-16, T-A3-47.

**Alternatives.**

- Notice only while armed (as before). Against: a receive-only host does not learn that it
  lost the radio until its stream stops; the ping-pong of A2.4 lasts longer.
- A new token only at drop events while armed. For: fewer token changes. Against: two rules
  for one state; A3.6 and B10.2 item 1 already give every session its own token, which keeps
  a stale arm write of the previous session from arming (B10.2 item 5).

**Reason.** The notice tells a host that it is no longer the owner, which is independent of
the arm. One token rule tied to the session end is simpler to implement and test.

## 80. Limit reaction times (rc3 review M2)

Status: proposed. Values are design values; the end-to-end check is HIS-11 and HIS-12.

**Problem.** Table A3-2 gave thresholds and actions but no time within which an action must
take effect, so T-A3-02 could not fail on a slow reaction.

**Rule.** Table A3-2 gets a column "Maximum time from threshold to action", measured from the
first measurement beyond the threshold that the safety core has to the action taking effect
(drive lowered, or RF stopped):

- TX frequency: checked at every key, so 0; keyed, the unkey precedes the new frequency;
- SWR: `REDUCE` and `UNKEY` ≤ 10 ms;
- PA temperature: ≤ 100 ms after the filtered value crosses (the value is filtered over
  seconds, A3.4a);
- forward power: `REDUCE` ≤ 10 ms after the window value exceeds its bound; `UNKEY` 200–210 ms
  after `REDUCE` started (0020 §29 with the tolerance of 0020 §16);
- supply voltage, current, RF while not keyed: ≤ 10 ms;
- maximum continuous TX time, ATU tune time: not before the limit, by the limit + 10 ms
  (0020 §16);
- sensor plausibility: ≤ 10 ms after detection; the detection time is HIS-11.

Detector and sensor response before the first sample are hardware (HIS-11); whether the sum
protects the PA is HIS-12. Applied in Table A3-2 and the note below it; T-A3-02.

**Alternatives.**

- All values TBD until the HIS. For: nothing fixed without hardware data. Against: the
  firmware part of the reaction is a design choice the testbench can check now against the
  reference model; the HIS only adds the sensor side.
- 1 ms for SWR. For: faster PA protection. Against: needs a dedicated fast path whose
  feasibility depends on the detector (HIS-11); 10 ms equals the tolerance used for every
  other safety timer (0020 §16); a PA that needs faster protection needs it in hardware
  (HIS-12).

**Reason.** A limit without a reaction time is not testable; 10 ms matches the existing
tolerance of the safety timers and is reachable in firmware under the load rule of A3.10.

## 81. Frequency encoding as a firmware convention (rc3 review M3)

Status: proposed.

**Problem.** Discovery byte 21 and the phase-word scale were TBD (HIS-04), so the wire format
depended on a hardware clock not yet known, and a host that does not read the record could
not know the scale.

**Rule.** Discovery byte 21 = 1 (phase word), always. The phase word uses a fixed virtual DSP
clock of 122 880 000 Hz, `phase_word = 2^32 × f / 122 880 000`, whatever the hardware clock;
the firmware converts to its own tuning word. Record field `dsp_clock_hz` reports
122 880 000. General byte 37 bit [3] must be 1; 0 is the mismatch of §73 item 12. HIS-04
stays open for the internal clock only. Applied in B3.8, Table B3-1 byte 21, Table B4-1
`dsp_clock_hz`, B4.11, B6.8, Table B7-1 byte 37 [3], Annex X2 C4; T-B3-15, T-B6-17.

Sources: [P2] General packet byte 37 NOTE, "Currently ALL openHPSDR FGPA code requires
transmit and receive phase words"; [P2] Appendix A, Boards 1–4: DSP clock 122.88 MHz
(122,880,000 Hz) and "DDC Frequency or Phase Word … Phase"; [P2] Discovery reply byte 21 and
General packet byte 37 for the formula.

**Alternatives.**

- Frequency in Hz (byte 21 = 0). For: no conversion; independent of any clock. Against:
  [P2] says all openHPSDR FPGA code uses phase words, so hosts are most tested with them; a
  host that ignores byte 21 sends phase words.
- Phase word on the real clock (HIS-04). For: no conversion in the firmware. Against: the
  wire format waits for the HIS and differs from the 122.88 MHz that hosts assume for an
  unknown board.

**Reason.** A fixed convention makes the wire format independent of the hardware and equal to
what the [P2] boards use. The conversion costs one multiplication per frequency change.

## 82. CWX keyer mode (rc3 review M4)

Status: proposed.

**Problem.** B10.5a made CWX bits the paddles of the radio's keyer, but did not say which
DUC-specific keyer bits ([P2] DUC specific packet byte 5: reverse, iambic, mode B, strict
spacing) apply to CWX, nor what iambic = 0 means for CWX.

**Rule.** For CWX, iambic (bit [3]), mode B (bit [5]) and strict character spacing (bit [6])
apply; reverse CW keys (bit [2]) does not, because the CWX bits are named dot and dash in
[P2] High Priority packet byte 5 and reversing concerns a physical paddle. With iambic clear
the keyer works as a straight key: key-down for as long as a dot or dash bit is held, under
the 1 s cap (§25, §36); keyer speed 0 keeps CWX from keying in both modes (§64). [P2]
describes the radio's keyer as "Straight, simulated Bug and Iambic A or B" ([P2]
DUC description before "Detailed operation", p. 6). Applied in B10.5a, Table B10-1 byte 5 [2]–[6], Annex X2 C19;
T-B10-33.

**Alternatives.**

- Apply all keyer bits, reverse included. For: one rule for KEY and CWX. Against: a host
  sending "dot" would get dashes; [P2] notes that reverse "does not alter the actual key
  closures reported", which places it at the paddle input.
- With iambic clear, form one element per bit edge. For: closer to "a set bit will send a
  dot or dash" ([P2] p. 34). Against: no way to send a straight-key character from CWX;
  the iambic bit would then mean nothing for CWX.

**Reason.** Iambic and its modes shape elements, which is what CWX feeds; reverse is about
wiring. A straight-key reading for iambic = 0 matches "Straight" in [P2]'s description of
the keyer.

## 83. rc3 review small fixes (review LOW)

Status: proposed.

1. **Hang delay bound (L1).** The hang delay in force is at most 2000 ms; a larger value in
   DUC-specific bytes 11–12 is clamped, logged and counted. The keyed timeout runs during the
   hang delay and ends it (unkey reason 2). A3.4d, B10.5, Table B10-1, Annex X1 D31; T-A3-51.
   Alternative: refuse a larger value. Against: there is no answer to a DUC-specific packet;
   a refusal would have to block CW altogether. Alternative: no bound. Against: SEND and the
   T/R relay would stay in TX for up to 65 s after the last element.
2. **Bounded wait in split (L2).** A key edge that waits while the return to the receive
   state is pending, moving or settling skips the return and goes straight to the TX state,
   one `t_settle` from the last relay command; receive-only deferred changes stay deferred.
   A3.1b, A3.9a item 3a; T-A3-52. Alternative: extend the bound to `t_rf_off` + 2 ×
   `t_settle`. Against: longer key latency in every split over, and the underrun bound of
   §57 would need to grow with it.
3. **Duplicate-request cache key (L3).** A request is a repeat only with the same request
   id, command and SHA-256 hash of the payload [FIPS180-4]; otherwise it is new, executed,
   and replaces the stored reply. A1.4; T-A1-14. Alternative: id only. Against: a host that
   restarts its id counter gets a stale reply for another command.
4. **Sequence counters across session ends (L4).** Reset at power-on and every reset, at a
   stop, at a takeover and at a session start by another host; continued across a watchdog
   standby, a link loss, an address or level change, so that a restart by the same host does
   not look like a takeover (A2.4 host guidance). B2.7, B5.4, Annex X2 C2; T-B5-17, T-B5-18.
5. **`RESTART` and the write session (L6).** An authenticated, verified `RESTART` is
   accepted from any host while another holds the write session; it neither needs, opens nor
   refreshes one. A1.10; T-A1-48. Alternative: keep the lock. Against: a radio whose writer
   tool hangs while refreshing its session cannot be restarted from another tool;
   `RESTART` changes no setting and every authenticated host already shares the secret.
6. **`CAP_REQUEST` retry (L7).** A host without a record 1 s after its request SHOULD repeat
   it, at most once per second, and tell the user after 5 tries. B4.4 item 4; T-B4-17.

(L5, the glossary, is handled with part C.)

## 84. "RF while not keyed" in CW gaps (rc4 draft review M1)

Status: proposed.

**Problem.** §74 made the CW hang delay count as keyed for RF-path purposes. The check "RF
while not keyed" (Table A3-2) ran "while not keyed and after `t_blank` since the last unkey",
so with break-in it never ran between elements: RF that stays on in a gap (a stuck keyer
path, a DUC that does not ramp down) would not be seen until the hang delay ended, up to
2000 ms (§83 item 1), with SEND and the T/R relay in TX.

**Rule.** For that check alone, "keyed" means RF commanded: with PTT and DUC I&Q the whole PTT
transmission; with CW from any source each element from the start of its leading ramp to the
end of its trailing ramp ([P2] DUC specific packet byte 17, CW ramp period); in an ATU tune
cycle the tune carrier. `t_blank` runs from the end of each RF-commanded interval, so the
check runs in every gap between elements longer than `t_blank`, in the hang delay and inside
a PTT transmission with break-in clear (§85). For RF-path purposes keyed stays as §74.
Applied in A3.1a (keyer elements), Table A3-2 last row, A3.4d, A3.9a item 6; T-A3-53.

**Alternatives.**

- Keep the check off during the hang delay. For: one meaning of "keyed". Against: RF in a gap
  goes unseen for up to 2 s, the case the check exists for.
- A separate gap check with its own threshold. For: could be tuned to the keyer. Against: a
  second threshold to find in HIS-11 for the same physical condition.

**Reason.** The check is about RF that the firmware did not command; between elements no RF
is commanded, whatever SEND and the relays do.

## 85. Break-in clear and CW with PTT (rc4 draft review M2)

Status: proposed.

**Problem.** [P2] lists DUC-specific byte 5 bit [7] "Break_in" among the CW options with no
stated meaning ([P2] DUC specific packet byte 5), and says nothing on CW together with PTT
([P2] High Priority packet bytes 4, 5). Table B10-1 said "honoured" without a behaviour, and
break-in is 0 after every session end (§64), so what KEY and CWX do then was undefined, as was
a PTT edge during a CW transmission or a CW element during a PTT transmission.

**Rule.**

1. Break-in set: KEY and CWX key by themselves, as before (B10.5a, B10.9), with the hang
   delay. PTT and CW never share a transmission; the first source keeps it: a PTT edge while
   a CW transmission is keyed (hang delay included) is refused, and a KEY or CWX element while
   a PTT transmission is keyed is refused for the element and the keyer stops; neither is
   latched nor ends the transmission in progress (A3.1a, "not keyed by another source").
2. Break-in clear: KEY and CWX form RF only inside the owner's PTT transmission. The
   transmission is the PTT transmission: it keys at the PTT edge under A3.1a, T/R relay, RX
   attenuator during TX and SEND follow the PTT, the hang delay is not used, `TX_STATE` shows
   TX source 1. An element is not a key of its own; it needs the A3.1a conditions that the PTT
   transmission met, and a failed condition ends the PTT transmission by its own rule. An
   element needs a closure or paddle edge after the PTT key (not latched). With CW selected
   (bit [1]) the keyer alone forms the RF: DUC I&Q is not transmitted (dropped and counted)
   and the underrun check is waived; with CW not selected, CWX forms no RF in a PTT
   transmission and KEY keys nothing. The CWX 1 s cap ends the PTT transmission (reason 9).
   Without PTT, KEY and CWX key nothing and nothing is latched.
3. A change of bit [7] or bit [1] while keyed is deferred to the unkey, as other state
   fields (A3.9).

Applied in A3.1a, A3.4d, Table A3-4, A3.9a items 1 and 4, B10.1, B10.5, B10.5a, new B10.5b,
Table B10-1 byte 5 [7] and bytes 11–12, B10.9 KEY, Host CWX and SEND rows, Annex X1 D8,
Annex X2 C22; T-B10-34 to T-B10-36; the conformance-test note of Annex X3 (tests of KEY and
CWX keying run with break-in set unless stated).

**Alternatives.**

- Break-in clear has no effect (KEY and CWX always key by themselves). For: no change to
  earlier text. Against: the bit would be "honoured" in name only, and a host that keys with
  PTT and CW selected would get two competing transmissions.
- Precedence instead of refusal with break-in set (a PTT edge ends a CW transmission, or a
  CW element ends a PTT transmission). For: the operator's newest action wins. Against: a
  takeover of the key by another source in the middle of a transmission is an unkey plus a
  new key without an edge of its own source, which A3.1a avoids; refusal is simpler to test.
- With break-in clear and CW selected, transmit DUC I&Q and keyer RF together. Against: two
  RF sources summed in the DUC; the PEP estimate and the mode class lose their meaning.

**Reason.** A host that keys the transmitter with PTT (MOX) and has CW selected expects the
radio's keyer to form the RF while the PTT is held; break-in is the CW option that lets the
key alone switch the transmitter. One transmission at a time keeps A3.1a and the relay rules
unchanged.

## 86. rc4 draft review small fixes (review LOW)

Status: proposed.

1. **Takeover notice only to register-map hosts (L1).** The three copies and the repeated
   notice of A2.4 go only to an old owner that used the register map: it sent a
   memory-mapped packet to port 7250 in its session or before its run bit since the last
   session end, or its session had non-zero General bytes 31–32; a memory-mapped packet from
   it within the 5 s makes it one from then on. Other old owners get no notice; `TX_ARM_STATE`
   and the token change as before. A2.4, A3.2 exception 2, Annex X1 D5, Annex X3 note;
   T-A2-17. Alternative: notice to every old owner (§79). Against: a standard [P2] host gets
   an unknown packet on its C&C socket, which it may log as an error or misread; an armed
   host has always used the register map, so nothing changes for it.
2. **Range exit in a gap (L2).** A3.4d and A3.9a item 4 name unkey reason 4 with limit id
   `LIMIT_TX_FREQ` for a DUC0 frequency outside the ranges in a gap, as A3.9 does while
   keyed; reason 6 for an RF-path change, 10 for the mode class. T-A3-55.
3. **Receive-only deferred changes at an edge after an unkey (L3).** A3.9a item 3 now applies
   only the deferred changes that concern the TX RF-path state; receive-only deferred changes
   stay deferred, as item 3a says. T-A3-54.
4. **Relay that cannot be re-commanded before it settles (L4).** A3.9a item 3a: the radio
   waits until the relay has settled, then commands it to the TX state and keys one
   `t_settle` later; if the item 3 bound is reached first, the request is refused, not
   latched. HIS-07 says which case holds. T-A3-54. Alternative: extend the bound. Against:
   the underrun bound of §57 depends on it.
5. **One commanded reset at a time (L5).** From the acceptance of a commanded reset until the
   reset or its refusal with status 59, a further `RESTART` (from any host, a repeat
   included) gets status 1 and any other commanded reset (`FACTORY_RESET`, `UPDATE_ACTIVATE`,
   `ROLLBACK`) status 35, not executed; only the first runs. A1.9; T-A1-49. Alternative:
   status 1 for all. Against: a `FACTORY_RESET` host would believe its reset ran, while the
   secret and configuration (Table A1-4) stay. Alternative: status 35 for all. Against: a
   second `RESTART` gets the reset it asked for.
6. **Unasked record at a run-bit restart (L6).** The General fields carried over at a restart
   by the same host (B5.4 item 1) count as a General packet of the set-up phase, so the
   unasked record goes out at the session start, to the carried-over register destination,
   within the 1 s limit. B4.4 item 2, B5.4; T-B5-19. Alternative: wait for a General packet
   of the new session. Against: a host whose keepalive is the High Priority packet alone
   (`annex-aethersdr.md` §2.2) would not get it.
7. **Stored reply and the write session (L7).** A repeated authenticated request answered
   from the stored reply (A1.4) does not refresh the write-session timer; only the first
   execution counts. A1.4, A1.10; T-A1-50. Against refreshing: a host that retransmits would
   keep the lock longer than its last write warrants.
8. **When a state-field change arrives (L8).** A change through a resent state field arrives
   with the first packet whose value differs from the value in force; repeats are the same
   change. A deferred change pending from before a gap does not end the hang delay by
   itself; it is applied at the end of the hang delay or with a change that arrives in the
   gap. A3.4d, A3.9; T-A3-55.
9. **CWX as a straight key (L9).** Annex X1 gets D33: with iambic clear a CWX bit is key-down
   while held (§82), a deviation from [P2] High Priority packet byte 5, p. 34 ("A set bit
   will send a dot or dash at the speed selected by the DUC Specific packet"). Known limit:
   bit [3] is shared by KEY and CWX. B10.5a.
10. **B2.7 (L10).** "A firmware update without a reset" is dropped from the session ends that
    keep the counters: a firmware update ends in a reset (A1.8), which resets them.

## 87. rc4 review fixes (rc4 review M1, L1–L9)

Status: proposed.

**Problem.** The review of rc4 found that "the PTT key" of §85 was not fixed in time, so a
KEY closure or paddle edge during the T/R settle or the RF delay could form RF before the
key sequence was complete; that §86 item 1 made the takeover notice the only register push
that a standard host does not get; and eight smaller gaps.

**Rule.**

1. **The PTT key (M1).** With break-in clear, "the PTT key" is the moment RF is enabled at
   the end of the key sequence of A3.9a item 4: after any wait of A3.9a item 3, the T/R relay
   and the RX attenuator during TX settled, SEND, and the RF delay of DUC-specific byte 13.
   Inside the PTT transmission keyer RF is allowed only from that moment. A KEY closure or
   paddle edge between the PTT 0→1 edge and that moment counts as held at the PTT key and
   needs a new closure or edge (not latched). A3.1a "Keyer elements", A3.9a item 4, B10.5b
   items 2.1, 2.2, Annex X2 C22; T-B10-34. Alternative: the PTT 0→1 edge as the PTT key, with
   keyer RF delayed until the sequence ends. Against: an element that rose during the RF
   delay would start cut or late, and the RF delay exists so that an external amplifier has
   switched before any RF.
2. **Takeover notice to every old owner (L1; replaces §86 item 1).** The three copies and
   the repeated notice of A2.4 go to every old owner, armed or not. The other register
   pushes (the unasked capability record, B4.4; `TX_ARM_TOKEN` at the session start, B10.2
   item 1; the telemetry snapshot, B9) already reach every owner from port 7250, so the
   exception gave no protection. Host guidance: a standard host ignores packets from source
   port 7250 by source-port demultiplexing ([P2] uses one port per packet kind; Table B2-1).
   A session carried over at a restart by the run bit (B5.4 item 1) counts as the old owner's
   session for the notice destination. A2.4, A3.2 exception 2, Annex X1 D5, Annex X3 note;
   T-A2-17. Alternative: keep §86 item 1 and extend it to the other pushes. Against: a host
   that has not used the register map would then not get its token or record at all, and
   the rule adds a per-host state for no safety gain.
3. **Commanded-reset answers (L2).** A repeat of the accepted request is answered with
   status 1 during steps 1–2 of A1.9 and with the stored reply after step 3, where the reply
   is stored. A `RESTART` of a second host gets status 1 and that answer is not stored, nor is
   a status 35 answer. After a refusal with status 59, every request answered with status 1
   is answered with status 59 on retry: the repeat from the stored reply, the other host's
   `RESTART` as a new commanded reset under "RF not gone". A1.4, A1.9; T-A1-51.
   Alternative: store the status 1 answer. Against: the host would keep getting "in
   progress" after the reset had been refused.
4. **A waiting request holds the transmission (L3).** A request waiting under A3.9a item 3
   holds the transmission for its source: an edge of another source during the wait is
   refused as "keyed by another source", not latched. A3.1a, A3.9a item 3; T-A3-56.
   Alternative: latch the other edge until the wait ends. Against: A3.1a forbids latching,
   and two waiting sources would need an order.
5. **KEY and CWX are one source (L4).** KEY and CWX drive the same keyer and count as one
   source, "the keyer": with break-in set a KEY element in a CWX transmission's hang delay,
   or the reverse, is allowed and continues the transmission; while both are active the
   keyer's dot and dash inputs are the OR of the two. A3.1a, B10.5b item 1; T-B10-37.
   Alternative: two sources, the second refused. Against: an operator who switches from the
   paddle at the radio to host CW within the hang delay would get a refusal that ends the
   keyer for no RF-path reason; both reach the same keyer and the same RF path.
6. **Silent PTT transmission (L5).** With CW selected and break-in clear, DUC I&Q under PTT
   is dropped, so a PTT transmission without elements is silent. B10.5b item 2.3 host note,
   Annex X2 C22.
7. **Gap check where the radio forms the elements (part C review L1).** A3.9a item 6
   applies the per-element meaning of "RF commanded" where the radio forms the elements (on
   level 1 KEY and CWX, on level 2 TCI `KEYER` and CW text). CW that the host forms as DUC
   I&Q with PTT is RF commanded throughout; part C C8.2.5 bounds that known limit by its hang
   delay of at most 2000 ms (0021 §46 item 2). *Corrected by §88 item 1:* the 2000 ms bound
   did not hold, and the check now runs inside such a PTT transmission in every run of
   all-zero DUC samples longer than `t_blank`.
8. **Refusal arriving while keyed (L7).** EER set or an invalid DUC0 rate or bit width that
   arrives while keyed is deferred to the unkey, as every DUC-specific state field (A3.9):
   the transmission continues with the settings in force; the refusal stands from the unkey,
   so the next key is refused. B10.6; T-B10-38. Alternative: unkey at once (reason 7 or a new
   reason). Against: the refusal changes no RF-path state and no limit, the settings in force
   are valid, and one rule for every DUC-specific field while keyed is simpler to test; a new
   reason number would change Table B8-3.
9. **Wording (L6, L8, L9).** T-B10-11, T-B10-24 and T-B10-32 state "CW select clear". The
   glossary "Keyed" and "Continuous TX" name the PTT transmission with break-in clear, and a
   "Break-in" entry is added. A3.9 "RF-path relays" lists the resent state fields of High
   Priority, DUC-specific and General packets, as A3.4d.

## 88. rc4 review fixes, second round (rc4 review M1, L1–L7)

Status: proposed.

**Problem.** The known limit of §87 item 7 claimed that RF in a gap of host-formed CW on
level 1 is seen at most 2000 ms late. That bound does not hold: TCI CW on level 1 is a PTT
transmission with DUC I&Q (part C C8.2.5), and with gaps shorter than the hang delay the PTT
never clears, so the check "RF while not keyed" would run only at the end of the PTT
transmission, up to the maximum continuous TX time (Table A3-2) after the RF appeared. The
review also found seven smaller gaps.

**Rule.**

1. **Zero-sample gaps inside a PTT transmission (M1; corrects §87 item 7).** Inside a PTT
   transmission with DUC I&Q, RF is commanded only up to the last sample fed to the DUC with
   I or Q non-zero (after the drive scaling, A3.4c; zero samples fed during an underflow,
   B10.5, count as zero). A run of all-zero samples longer than `t_blank`, counted from the
   key or from the last non-zero sample, is "no RF commanded" for the check "RF while not
   keyed", which then runs as in any other gap. The firmware feeds every DUC sample (A3.4c),
   so the rule needs nothing from the host and covers AetherSDR's TCI CW on level 1 and every
   P2 host that sends CW as I&Q with PTT. For this case `t_blank` also covers the
   DUC-to-coupler delay (HIS-18), and the threshold lies above the forward power with
   all-zero samples (carrier leakage). Threshold and `t_blank` stay TBD (HIS-11, HIS-12).
   Remaining known limit: non-zero samples in a gap (noise, dither, a DC offset) command RF,
   so that gap is not checked; such RF is seen at the next all-zero run longer than `t_blank`
   or after the unkey. Host guidance: send exact zeros in gaps. Table A3-2 "RF while not
   keyed", A3.1a "Keyer elements", A3.4d, A3.9a item 6, B10.5; part C C8.2.5 item 2 (0021 §47
   item 1); annex G-13; T-A3-57, T-C8-32. Alternative: keep the known limit and bound it by
   the maximum TX time. Against: up to 5 min of RF in the gaps without a fault, while the
   firmware already has the samples that show the gaps. Alternative: a power threshold on the
   samples instead of exact zero. Against: the threshold would need its own value per drive
   level and filter; exact zero is what a host sends for key-up and is testable bit for bit.
2. **Which key starts what (L1).** With break-in clear, the T/R relay, the RX attenuator
   during TX and SEND go to TX at the PTT 0→1 edge accepted under A3.1a, as the first steps of
   the key sequence of A3.9a item 4, not "at the PTT key", which is the later moment RF is
   enabled (§87 item 1). The maximum continuous TX time counts from the key of A3.1a. A3.4d,
   A3.9a item 4, glossary "Continuous TX"; T-B10-40.
3. **CWX with break-in clear (L2, L3).** With CW not selected, a CWX paddle edge in the PTT
   transmission is refused because CWX needs CW selected with break-in clear, not "as from
   another source". After the PTT key a CWX element needs a request-level edge: the CWX
   request of B10.5a goes to 0, both paddle bits at 0, and rises again; a change from one held
   bit to the other is not an edge. B10.5b items 2.2, 2.3; T-B10-39.
4. **Cached PTT with break-in clear and CW selected (L4).** The underrun check is waived
   there (B10.5b item 2.3), so a host whose I/O thread keeps sending a cached PTT bit holds
   SEND, the T/R relay and an external amplifier in TX without RF until the maximum
   continuous TX time. Added to the known limits of B10.5; T-B10-40.
5. **DUC rate while keyed (L5).** A host SHOULD NOT change the DUC0 sampling rate or bit
   width while keyed: the change is deferred (§87 item 8), so I&Q sent at the new rate is
   played at the old rate until the unkey. B10.6 host note.
6. **Takeover notice wording (L6).** Annex X1 D5: a standard host "is expected to ignore"
   packets from port 7250 (a host SHOULD), not a statement of fact; [P2] does not require it.
7. **Hang delay 0 on level 1 (L7).** Part C C8.2.5 item 1 notes the cost of PTT per element:
   the key latency (`t_settle` plus the RF delay) per element, a T/R cycle per element, the
   25 ms unkeyed FIFO of B10.7 for the first samples, and the 10 ms edge rule of B11.6a
   (Annex X1 D28); a hang delay above 0 is recommended for break-in CW (0021 §47 item 2).

---

## Consequences

- `spec/network-interface.md` draft 4 applies §1–§21 and cites them as "0022 §n"; Annex X1
  gets D24 (DUC I&Q only from the owner) and D25 (answer rate limits of §16, B11.14); Annex X2 gets C14 (ADC max magnitude), C15
  (memory-mapped packet length) and C16 (wideband sequence number per frame); Annex X3 gets
  tests for the new rules.
- `spec/register-map.yaml` is regenerated by the coordinator for the new names of §19 and the
  new `TX_STATE` unkey reasons 6 and 7.
- Part C (`spec/part-c-tci-profile.md`) follows the names of §19 and the rules of §1, §2, §6
  and §7 in a later step.
- §22–§32 (second review of the transmit side) are applied in `spec/network-interface.md`
  draft 5 (A1.6, A1.8, A1.9, A2.4, A3.1a, A3.2, A3.4, A3.5, A3.6, A3.9–A3.9c, B8, B10, Annex
  X1 D8, D10, D26, D27, Annex X2 C17, Annex X3) and `spec/part-c-tci-profile.md` draft 4. New
  names for the register map YAML: register `LIMIT_INHIBIT` (0x0221); drop reasons 13 `STOP`
  and 14 `HOLDER_LOST`; `TX_STATE` unkey reasons 8, 9 and 10. Values `P_rf_off`, `t_rf_off`,
  `t_settle`, `t_blank` and the tune power belong to HIS-07, HIS-08, HIS-11 and HIS-12; the
  survival of counters across a reset to HIS-13.
- §33–§51 (final review of rc1) are applied in `spec/network-interface.md` rc2 draft (A1.6,
  A1.8, A1.9, Table A1-3, A2.3–A2.5a, A3.1a, A3.1b, Tables A3-1 and A3-2, A3.4c, A3.4d, A3.6,
  A3.9a, A3.9b, B2.7, B4.4, B5.1a, B5.2, B5.6, B7, B8.4, B8.4a, Tables B8-2 and B8-3, B10.1,
  B10.2, B10.5, B10.5a, B10.9, B11.6a, B11.14, B11.15, Annex X1 D10, D26–D29, Annex X2 C18,
  C19, Annex X3), in `spec/part-c-tci-profile.md` rc2 draft (C2.8, C2.9, C4, C5.5.5,
  C5.5.5.1, C5.5.8, C5.6, C5.7, C5.10–C5.12, C7.2.1, C7.6, C8.1, C9, C-B13–C-B15, C-C17), in
  `spec/annex-aethersdr.md` and `spec/glossary.md`. New names for the register map YAML:
  write reject reason 10 `NOT_KEYABLE`; management status 58; stream-state reasons `update`
  and `link` (part C enumerations). `P_ssb_mean` belongs to HIS-11 and HIS-12; the filter plan
  for the receive state (§33) to HIS-07; envelope samples of the detector (§43) to HIS-11.
- §52–§61 (review of the rc2 draft) are applied in `spec/network-interface.md` rc2 (A1.4
  Tables A1-2 and A1-3, A1.6, A1.6a with Table A1-4, A1.8, A1.9, A1.11a, A2.3, A2.4, A2.5a,
  Table A3-1, A3.4, A3.4c with Table A3-3, Table A3-2, A3.9b, Table B8-2, B8.5, B10.2, B10.5,
  B10.5a, B10.9, B11.6a, Annex X1 D8, D28, Annex X2 C20, Annex X3), in
  `spec/part-c-tci-profile.md` rc2 (C2.5.4, C2.8, C4, C5.5.3, C5.5.5, C5.7, C5.10, C5.10.1,
  C8.1, C9, C-C18), in `spec/annex-aethersdr.md` and `spec/glossary.md`. New names: management
  status 59; constant `t_reset_wait` (2 s); Table A1-4 and Table A3-3. `spec/register-map.yaml`
  needs regenerating by the coordinator for the changed `TX_ARM_STATE` and `LIMIT_FWD_POWER`
  texts. `t_reset_wait` must exceed `t_rf_off` (HIS-12); `t_rf_off` + `t_settle` ≤ 98.75 ms is
  needed for the underrun bounds of §57 (HIS-07, HIS-12); the factory default of C-1 is HIS-14.
  `sources.md` could add RFC 2131 (DHCP), cited directly in A1.11a.
- §62–§73 (review of rc2) are applied in `spec/network-interface.md` rc3 draft (A1.2, A1.4,
  A1.6, A1.6a, A1.8–A1.10, A2.4, A3.1a, A3.1b, Table A3-1, A3.2, Table A3-2, A3.4a, A3.4c with
  Table A3-3, A3.6, A3.6a, A3.7, A3.9, A3.9a, A3.9b, B3.2, B3.8, B3.9, B4.4, B4.7, B5.1a, B5.2,
  B5.7, B5.8, Tables B7-1, B8-2, B8-3, B10-1, B8.5, B10.1, B10.2, B10.7, B10.9, B10.10, B11.6a,
  B11.7, B11.14, B11.15, Annex X1 D5, D10, D25, D28, D29, D30, Annex X2 C13, C20, Annex X3).
  New names: `STREAM_STATUS` reason 13 (frequency encoding mismatch); Table A3-4; A3.9a item
  1a. `spec/register-map.yaml` needs regenerating by the coordinator for the changed
  `TX_ARM_TOKEN`, `LIMIT_*` texts and stream reason 13. `sources.md` could add RFC 1812
  (§70). Part C follows §62 (PEP estimate), §64 where TCI has session TX settings, §66, §67,
  §68 and §73 items 9, 10, 18 in a later step. HIS-18 gets the DUC-to-coupler delay and the
  keyed FIFO capacity (§62, §63); HIS-11 and HIS-12 the crest-factor margin and the ordering of
  the "RF while not keyed" threshold, `P_rf_off`, `t_blank` and `t_reset_wait` (§62, §68).
- §74–§77 (review of the rc3 draft) are applied in `spec/network-interface.md` rc3 (A1.4,
  Table A1-3 precedence, A1.8, A1.10, A2.4, A3.1a, A3.1b, Table A3-1, A3.4d, A3.9, A3.9a,
  A3.9b, A3.9c, B5.1a, B5.4, B10.5a, B10.9, B10.10, B11.10, B11.14, Annex X1 D31, Annex X2
  C21, Annex X3 T-A1-15, T-A1-46, T-A1-47, T-A2-15, T-A3-48 to T-A3-50, T-B5-16). Table B8-2
  is unchanged, so `spec/register-map.yaml` needs no regeneration for them. Part C applies
  §74 in its keyer, CW text and break-in rules.
- §78–§83 (review of rc3) are applied in `spec/network-interface.md` rc4 draft (A1.4, A1.10,
  A2.3, A2.4, A3.1b, A3.2, Table A3-2, A3.4d, A3.6, A3.6a, A3.9a item 3a, B2.7, B3.8, Tables
  B3-1, B4-1, B7-1, B10-1, B4.4, B4.11, B5.1a, B5.2, B5.4, B5.6, B5.8, B6.8, B10.5, B10.5a,
  Annex X1 D5, D31, D32, Annex X2 C2, C4, C19, C21, Annex X3 T-A1-14, T-A1-48, T-A2-16,
  T-A3-02, T-A3-47, T-A3-51, T-A3-52, T-B3-15, T-B4-17, T-B5-13, T-B5-16 to T-B5-18,
  T-B6-17, T-B10-33). `spec/register-map.yaml` needs regenerating by the coordinator for the
  changed `dsp_clock_hz` text. HIS-04 keeps only the internal DSP clock; HIS-07 gets whether a
  relay may be commanded again before it has settled (§83 item 2); HIS-11 and HIS-12 get the
  detector and sensor response times that add to the reaction times of §80.
- §84–§86 (review of the rc4 draft) are applied in `spec/network-interface.md` rc4 (A1.4, A1.9,
  A1.10, A2.4, A3.1a, A3.2, Table A3-2, A3.4d, Table A3-4, A3.9, A3.9a items 1, 3, 3a, 4, 6,
  B2.7, B4.4, B5.4, B10.1, B10.5, B10.5a, B10.5b, Table B10-1, B10.9, Annex X1 D5, D8, D33,
  Annex X2 C22, Annex X3 note, T-A1-49, T-A1-50, T-A2-17, T-A3-53 to T-A3-55, T-B5-19,
  T-B10-34 to T-B10-36). Table B8-2 is unchanged, so `spec/register-map.yaml` needs no
  regeneration for them. HIS-07 gets whether a relay can be commanded again before it
  settles (§86 item 4, as §83 item 2); HIS-11 the gap length below which `t_blank` hides RF
  between CW elements (§84). Part C follows §84 and §85 where TCI has CW with PTT.
- §87 (review of rc4) is applied in `spec/network-interface.md` rc4 (A1.4, A1.9, A2.4, A3.1a,
  A3.2, A3.9, A3.9a items 3, 4, 6, B10.5b, B10.6, Annex X1 D5, Annex X2 C22, Annex X3 note,
  T-A1-51, T-A2-17, T-A3-56, T-B10-11, T-B10-24, T-B10-32, T-B10-34, T-B10-37, T-B10-38) and
  `spec/glossary.md`. §87 item 2 replaces §86 item 1. Table B8-2 is unchanged, so
  `spec/register-map.yaml` needs no regeneration for it. Part C follows §87 item 7 in C8.2.5
  (0021 §46).
- §88 (second review round of rc4) is applied in `spec/network-interface.md` rc4 (A3.1a,
  Table A3-2, A3.4d, A3.9a items 4 and 6, B10.5, B10.5b items 2.2 and 2.3, B10.6, Annex X1
  D5, T-A3-57, T-B10-39, T-B10-40), `spec/part-c-tci-profile.md` rc4 (C8.2.5 items 1 and 2,
  T-C8-32; 0021 §47), `spec/annex-aethersdr.md` (G-13) and `spec/glossary.md` ("Keyed",
  "Continuous TX"). §88 item 1 corrects §87 item 7. Table B8-2 is unchanged, so
  `spec/register-map.yaml` needs no regeneration for it. HIS-11 gets the forward power with
  all-zero DUC samples (carrier leakage), which the "RF while not keyed" threshold must
  exceed; HIS-18 the DUC-to-coupler delay that `t_blank` must cover in a zero-sample gap.
- `open-questions-his.md`: HIS-07 (filter plan, which frequencies share an RF-path state),
  HIS-11 (PEP detector, temperature filter), HIS-12 (`P_swr`, `P_temp`, hysteresis) are
  extended by the coordinator; this file does not edit it.

## Sources

- [P2] openHPSDR Ethernet Protocol V4.4: "Detailed operation" (standby, RUN); General packet
  bytes 24–28, 38, 56–59; DDC, DUC-specific, High Priority packets ("Sequence Number");
  High Priority Status packet bytes 0–3, 39–42, 51–59 (pp. 48–49); Wideband Data packet
  (pp. 52–53); DDC packet "Destination Port"; Memory mapped registers from PC / from hardware.
- [G7250-MAN] Xiegu G7250 Operation Manual: TX power per mode, ANT and ATU keys of the
  controller.
- [CH394] WCH CH394 manual 1, V1.2: section 7.1.15 (PHY_CFG).
- [RFC2104], [FIPS180-4].
- Decisions 0003, 0004, 0005, 0006, 0007, 0008, 0011, 0015, 0017, 0020, 0021;
  `spec/annex-aethersdr.md`.

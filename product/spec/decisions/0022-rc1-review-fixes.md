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

0008 U-1 "cannot disarm … for them" is read as: an update does not disarm; the owner
disarms first.

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

**Reason.** Repetition covers a single loss; the 200 ms rule covers the rest, since the
status packet comes every 50 ms (B9.4).

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

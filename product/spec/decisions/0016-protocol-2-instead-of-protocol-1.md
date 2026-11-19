# 0016 — Level 1 uses openHPSDR Protocol 2 instead of Protocol 1

- Status: accepted (ON8ST, 2026-11-19: "P2 is in any case the better choice")
- Date: 2026-11-19
- Revises: 0001 (item 1 of the design note, out-of-scope list), 0009, 0011 (point 5 and the
  name of level 1). Makes 0005 and 0015 to be rewritten for P2 (see Consequences).

## Context

The start brief (ON8ST, 2026-11-19) defined level 1 as native openHPSDR Protocol 1. 0001 and
0011 put Protocol 2 out of scope. ON8ST then asked for a side-by-side analysis regardless of
earlier decisions: `analysis/p1-vs-p2.md`.

The main findings of that analysis, with its sources:

- P2 has a mandatory host-loss watchdog that switches off PTT and the open-collector
  outputs when no C&C packet arrives for one second [P2]. Standard P1 has none
  [P1-USB], [P1-METIS]. HL2 added one as an extension [HL2].
- P2 sends status (forward and reverse power, PTT, ADC overload, supply) every 1 ms during
  TX and immediately when an input changes [P2]. In P1 telemetry is spread over the
  round-robin C&C returns [P1-USB].
- P2 has a standard self-description in the discovery reply (board type 255) [P2]. P1 has
  none [P1-METIS].
- P2 control is event-driven, in separate packets, instead of a round-robin cycle [P2].
- P2 is more work to implement (several ports and packet types) [P2], and most of its
  extra capacity (up to 80 DDCs, synchronous DDCs, VITA-49) is of no use to a radio with one
  receiver [G7250].

What AetherSDR supports, from its README on GitHub (github.com/aethersdr/AetherSDR, read
2026-11-19, latest release v26.11.3 of 2026-11-16) [AETHER]:

- FlexRadio (SmartSDR protocol) is the primary target.
- Hermes-Lite 2 is supported in the desktop application over openHPSDR Protocol 1 (board
  id 6), including transmit.
- ANAN-G2 over openHPSDR Protocol 2 is experimental and receive-only. "Transmit is a future
  phase."
- AetherSDR has a vendor-neutral `IRadioBackend` seam, with six backends on it.
- AetherSDR is licensed GPL-3.0.

ON8ST: if needed, we implement P2 support for the G7250 in AetherSDR ourselves (2026-11-19).

## Options considered

### A. Protocol 2 only (chosen)

Level 1 is the openHPSDR Protocol 2 with a G7250 board type.

- For: watchdog, fast TX telemetry and self-description are part of the standard, not our
  own extensions. Those are the parts that matter most for a 100 W radio.
- For: P2 is actively maintained [P2], and its structure leaves room for extra fields
  "in the middle of the packet" without disturbing existing settings [P2].
- For: AetherSDR already has a P2 receive path (ANAN-G2), so the G7250 work starts from
  existing code rather than from nothing [AETHER].
- Against: AetherSDR has no P2 transmit yet [AETHER]. We have to build it, in a project we
  do not own.
- Against: more work in the firmware than P1, while the compute budget is still unknown
  (HIS).
- Against: HL2 support in AetherSDR, which already covers P1 TX, cannot be reused as
  directly.

### B. Protocol 1 only (the earlier course)

Keep P1 as in 0009, with watchdog, telemetry and capability block as G7250 extensions.

- For: AetherSDR already supports P1 including TX, through its HL2 backend [AETHER].
- For: simplest firmware [P1-METIS], [P1-USB].
- Against: the safety-relevant parts (watchdog, TX telemetry rate) are our own extensions
  that no other P1 host knows. P2 has them in the standard.
- Against: the protocol is not maintained further. Our extensions stay ours alone.

### C. Both P1 and P2 in the firmware

The firmware answers both protocols, and the host chooses.

- For: the widest host support, and P1 TX in AetherSDR is available on day one.
- Against: two protocol stacks to specify, implement and test, on hardware with an unknown
  budget.
- Against: the safety behaviour must be the same on both. Without a watchdog in standard
  P1, the P1 side needs the extensions of option B anyway, so this costs the work of A and
  B together.

### D. P1 first, P2 later

Start with P1 because AetherSDR already supports it, move to P2 in a later milestone.

- For: a working TX path in AetherSDR sooner.
- Against: everything specified for P1 (C&C map, arm, capability block) is thrown away
  later. Hosts and users would see a protocol change between versions.

## Decision

Option A. Level 1 is openHPSDR Protocol 2, followed as closely as possible, with a G7250
board type. Protocol 1 is out of scope. If AetherSDR does not have the needed P2 support
(in particular transmit) by then, we implement it ourselves.

## Consequences

- **Name of level 1.** "G7250-P1" no longer fits. Level 1 is called "G7250-P2" (ON8ST,
  2026-11-19).
- **0009** now reads: stay as close to standard Protocol 2 as possible. G7250 extensions only
  on bytes that P2 leaves free or reserved, each marked as an extension.
- **0001**: item 1 of the design note and the out-of-scope list change ("Protocol 2" leaves
  the list, "Protocol 1" enters it). Spec section 2 (transport) becomes the P2 port set;
  sections 3, 4 and 7 follow P2's discovery, self-description and packet structure.
- **0011 point 5**: "Protocol 2 stays out of scope" is replaced by this decision.
- **0005 (C&C)** has to be rewritten. Its rule "HL2 addresses only with identical meaning"
  was about P1 C&C addresses. On P2 the base is the P2 packets; the question becomes which
  P2 fields fit the G7250 as they are, and where G7250 fields go (reserved bytes, or a
  G7250-specific packet).
- **0015 (unknown board type)** keeps its intent (RX for any host, TX only after an
  explicit G7250 arm), but the arm moves from a P1 C&C address to a register in the G7250 register map (0005,
  0015 as rewritten). P2's own
  watchdog [P2] covers part of 0007.
- **Board type value (0002).** P2 assigns 0–6 and 10, reserves 7–9, and uses 254 and 255 for
  descriptions [P2]. A G7250 value should not collide with future openHPSDR assignments.
  Coordinating a value with the openHPSDR maintainers is an outward action and needs a go
  from ON8ST.
- **Capability block (0003).** First check whether P2's board type 255 full description
  [P2] covers what we need, before defining anything of our own.
- **Several hosts.** P2 lets a second host take over by sending C&C [P2]. That conflicts with
  the single owner in 0011, so the G7250 must restrict it. This is a documented deviation
  from P2.
- **AetherSDR.** The annex "Changes needed in AetherSDR" grows: a G7250 backend on P2,
  including transmit, on the `IRadioBackend` seam [AETHER]. Any contribution upstream (pull
  request, issue) needs a go from ON8ST (AGENTS.md rule 6). AetherSDR is GPL-3.0, so code we
  contribute there is GPL-3.0 [AETHER].
- **Socket budget (CH394Q).** ON8ST found a WCH CH394Q Ethernet controller (hardware
  inspection, 2026-11-19): 10/100 Mbit/s, 8 sockets, SPI up to 62 MHz [CH394]. Standard P2
  with one receiver plus the G7250 register map needs 8 sockets
  (`analysis/ch394-network-budget.md`). ON8ST confirmed that P2 stays (2026-11-19). The
  management channel (0008) cannot have its own socket unless another port is freed, for
  example by sharing port 1024 or by leaving out DDC audio. Sample rates are limited by SPI
  throughput (0004).
- **Update after 0017.** DDC audio (port 1028) is not offered, so standard P2 plus the register
  map uses 7 of 8 sockets and one socket is free for the management channel (0008).
- **HIS.** The compute and network budget becomes more pressing, because P2 is the heavier
  protocol (several UDP ports, 24-bit TX path at 192 ksps [P2]).

## Sources

- Discussion with ON8ST, 2026-11-19.
- `analysis/p1-vs-p2.md` and the sources listed there: [P1-USB], [P1-METIS], [P2], [HL2],
  [G7250].
- [AETHER] AetherSDR README, github.com/aethersdr/AetherSDR, read 2026-11-19 (latest
  release v26.11.3, 2026-11-16).
- Decisions 0001, 0005, 0009, 0011, 0013, 0015.

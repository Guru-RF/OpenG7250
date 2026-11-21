# 0015 — Host that does not know the G7250 board type: RX only; TX needs an explicit arm

- Status: accepted (ON8ST, 2026-11-19; rewritten for Protocol 2 after 0016)
- Date: 2026-11-19

## Context

G7250-P2 reports its own board type in the discovery reply (0016; [P2], byte 11). A generic
P2 application that does not know that value may refuse the radio, or may treat it as a
generic P2 device. Which applications do which has not been checked.

In P2, transmit is enabled by bit [1] of byte 4 of the High Priority packet [P2]. Any host
that sends High Priority packets can set it. Nothing a host sends in standard P2 shows that
it knows the G7250.

What standard P2 already gives [P2]:

- A host-loss watchdog. If no C&C packet arrives for a second while in RUN, the radio goes to
  standby, and PTT and open-collector outputs are switched off. The host can disable this
  timer in the General packet (byte 38 bit [0]) "for debugging purposes".
- When a second host sends C&C to a radio that is already in use, the radio disconnects the
  first host and follows the second.

The G7250 has a 100 W PA [G7250]. The safety core (watchdog, TX limits, fault state) sits
below both levels and applies to every host (0011). Full functionality including TX is
delivered through AetherSDR (0012, 0013, 0016). G7250-specific control lives in a G7250
register map carried by the P2 memory-mapped register packets (0005).

## Options considered

### A. RX for any host; TX only after an arm in the G7250 register map (chosen)

Any host that starts a P2 session receives RX-IQ in a safe default state. The transmit bit in
the High Priority packet has no effect until the host has written an arm value to a G7250
register (0005). A generic P2 host never writes to that register, so it can never transmit.

- For: TX safety does not depend on the host being well-behaved. Only software that knows
  the G7250 can key the PA.
- For: receiving works in any P2 application that accepts the board type. That is useful for
  testing and first acceptance of the hardware, and costs almost nothing in the firmware.
- For: it uses the extension mechanism of P2 itself (memory-mapped registers) and touches no
  standard field.
- Against: the arm travels in a different packet from the transmit bit. The spec has to
  define the order and how the radio confirms the arm.
- Against: how useful the RX fallback is depends on how existing P2 applications treat an
  unknown board type, which is not known yet.

### B. Nothing without the board type: streams start only after a G7250 handshake

The firmware starts no streams until the host has written a G7250 register.

- For: the strictest option. No traffic at all to software that does not know the radio.
- Against: no use in any existing P2 application, not even for receiving or testing.
- Against: it adds a step that standard P2 does not have (0009). Option A already gives the
  same TX safety.

### C. Full generic P2, including TX on the standard transmit bit

The radio behaves like a generic P2 device for every host.

- For: the most compatible. Any P2 application that accepts the board type can transmit.
- Against: a generic host does not know the state of the PA, the internal ATU or the antenna
  switching, so it can key 100 W into a wrong antenna or an untuned ATU.
- Against: a generic host does not implement the G7250 safety behaviour (0007).

### D. Generic P2 TX, protected only by the P2 watchdog and the safety core

Like option C, but relying on the P2 watchdog [P2] and the safety-core limits (0011).

- For: no extra mechanism. The P2 watchdog already covers a host that disappears.
- Against: the watchdog covers a host that stops talking, not a host that talks and keys the
  radio when it should not. The safety core stops a bad transmission after the fact; it does
  not prevent it.
- Against: the host can switch the P2 watchdog off [P2].

### E. Arm in a reserved bit of High Priority byte 4

Put the arm in one of bits [2]–[7] of byte 4, which P2 marks reserved [P2], next to the
transmit bit.

- For: arm and transmit travel in the same packet and change at the same moment.
- Against: reserved bits get a meaning in later P2 revisions (see 0005). A host following a
  later revision could set the bit for another purpose and arm the G7250 by accident.
- Rejected by the rule in 0005: reserved bytes are not used.

### F. Arm over the management channel

Arm the radio over the management channel (0001, spec section 10).

- For: P2 stays fully untouched.
- Against: arming then lives on a different connection from the transmit bit. Both have to
  stay in step when the session stops or the watchdog fires.
- Against: every host that wants to transmit needs a second connection.

## Decision

Option A. Any host that starts a P2 session may receive RX-IQ. TX is possible only after the
host has written the arm value to a G7250 register (0005). Without that arm, the transmit bit
in the High Priority packet is ignored and the PA stays off.

## Consequences

- The arm register, its value and its exact behaviour are specified in 0007 (watchdog and
  safety) and placed in the G7250 register map (0005).
- The arm is lost on every event that ends or interrupts control: the run bit cleared, the P2
  watchdog firing [P2], a takeover by another host, reset and fault. The host has to arm
  again afterwards. The exact list belongs in 0007.
- **Takeover by another host.** Standard P2 lets a second host take over by sending C&C [P2].
  On the G7250 a takeover never carries the arm with it. Whether takeover is allowed at all
  while armed is part of the single-owner rule (0011) and is decided in 0007. Either way it
  is listed as a deviation from P2.
- **P2 watchdog.** While TX is armed, the G7250 does not let the host disable the P2 watchdog
  (General packet byte 38 bit [0]). This is a deviation from P2, to be specified in 0007.
- The radio reports whether TX is armed, in a G7250 register sent to the host, so the host
  can show it.
- The RX default state for a host that has not armed (antenna, filters, attenuation) needs
  HIS input on antenna and filter switching.
- The design note describes this behaviour for P2 clients that see an unknown board type.
  Which existing P2 applications accept the value is to be checked against public sources
  per application.

## Sources

- Discussion with ON8ST, 2026-11-19.
- Start brief, ON8ST, 2026-11-19.
- Decisions 0001, 0005, 0007 (reserved), 0009, 0011, 0012, 0013, 0016.
- [P2] openHPSDR Ethernet Protocol V4.4, github.com/TAPR/OpenHPSDR-Firmware, `Protocol 2/Documentation/`:
  "Detailed operation" (watchdog, standby), General packet byte 38, High Priority packet
  byte 4, discovery reply byte 11 and the note on connecting to running hardware.
- [G7250] Public G7250 product specifications (Radioddity) — to be listed in `sources.md`.

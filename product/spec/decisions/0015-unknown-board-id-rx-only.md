# 0015 — Host that does not know the board id: RX only; TX needs an explicit arm

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19

## Context

G7250-P1 reports its own board id in the discovery reply (start brief, ON8ST, 2026-11-19;
0001, spec section 3). A generic P1 application that does not know that id may refuse the
radio, or may treat it as a generic P1 device. Which applications do what has not been
checked.

In standard P1, the host never tells the radio which board ids it knows. The firmware
therefore cannot tell a G7250-aware host from a generic one by anything the host says in
standard P1. A generic host can still set MOX, the standard TX bit, and so key the radio.
The G7250 has a 100 W PA (public product specifications, Radioddity).

The safety core (watchdog, TX limits, fault state) sits below both levels and applies to
every host (0011). Full functionality including TX is delivered through the integration
route, AetherSDR (0012, 0013).

## Options considered

### A. RX for any host; TX only after an explicit G7250 arm (chosen)

Any host that starts a P1 session receives RX-IQ in a safe default state. MOX has no effect
until the host has written an arm command to a G7250 C&C address. A generic P1 host never
writes to that address, so it can never transmit.

- For: TX safety does not depend on the host being well-behaved. A host has to show, by an
  action that only G7250-aware software takes, that it knows the radio before the PA can be
  keyed.
- For: receiving works in any P1 application that accepts the board id. That is useful for
  testing, debugging and first acceptance of the hardware, and it costs almost nothing in
  the firmware.
- For: does not weaken 0012. Generic RX is a fallback, not an integration. Full
  functionality still goes through AetherSDR.
- Against: a generic host can use the receiver without the user having chosen to allow it.
  On the local network this is the normal P1 situation and is not seen as a risk.
- Against: how useful the fallback is depends on how existing applications treat an unknown
  board id, and that is not known yet.

### B. Nothing without the board id: streams start only after a G7250 handshake

The firmware starts no streams until the host has written a G7250-specific command. A
generic host gets the discovery reply and nothing else.

- For: the strictest option. No traffic at all to software that does not know the radio.
- Against: no use in existing P1 applications at all, not even for receiving or testing.
- Against: it adds a step before RX that standard P1 does not have, which works against 0009
  (stay as close to standard P1 as possible). The same safety for TX is already available
  with option A.

### C. Full generic P1, including TX on MOX

The radio behaves like a generic P1 device for every host, and MOX keys the PA directly.

- For: the most compatible. Any P1 application that accepts the board id can also
  transmit.
- Against: a generic host does not know the state of the PA, the ATU or the antenna
  switching, so it can key 100 W into a wrong antenna or an untuned ATU. The safety core
  limits damage but does not prevent an unintended transmission.
- Against: a generic host does not implement the G7250 safety behaviour (0007), so the user
  gets TX without the protections the spec promises.

### D. RX for any host, TX on MOX, protected only by the safety core

Like option C, but relying on the safety core (SWR, temperature, power, maximum TX time) to
stop anything harmful.

- For: no extra command. TX works in any host, with the limits from 0011 always active.
- Against: the safety core reacts after the fact. It stops a bad transmission, it does not
  prevent it. An unintended transmission at 100 W is a problem in itself, even if it ends
  in time.
- Against: limits such as maximum TX time are set conservatively for unknown hosts, so they
  would also restrict AetherSDR, or the firmware would still have to tell hosts apart.

### E. Arm through the management channel instead of C&C

Same as option A, but the arm command goes over the management channel (0001, spec section
10) instead of over a C&C address.

- For: P1 C&C stays free of a safety-specific extension.
- Against: arming then lives on a different channel from MOX. The two have to stay in step,
  for example when the P1 session stops or the watchdog fires, which adds failure cases.
- Against: every host that wants to transmit needs a second connection.
- This option stays possible if 0007 or 0008 show a reason for it.

## Decision

Option A. Any host that starts a P1 session may receive RX-IQ. TX is possible only after the
host has armed it with a command on a G7250 C&C address. Without that arm, MOX is ignored and
the PA stays off.

## Consequences

- The arm command, its address and its exact behaviour are specified in 0007 (watchdog and
  safety) and placed in the C&C map as a G7250 extension (0005).
- The arm is lost on every event that ends or interrupts control: session stop, watchdog
  timeout, reset and fault. The host has to arm again afterwards. The exact list belongs in
  0007.
- The capability block and the C&C returns report whether TX is armed, so a host can show it.
- The RX default state for a host that has not armed (antenna, filters, attenuation) needs
  HIS input on antenna and filter switching.
- The design note (0001, item 2) describes this behaviour for P1 clients that see an unknown
  board id. Which existing applications accept the id is to be checked against public
  sources per application.

## Sources

- Discussion with ON8ST, 2026-11-19.
- Start brief, ON8ST, 2026-11-19.
- Decisions 0001, 0005, 0007 (reserved), 0009, 0011, 0012, 0013.
- Public G7250 product specifications (Radioddity) — to be listed in `sources.md`.
- Protocol 1 documentation (MOX bit, discovery) — to be listed in `sources.md` as [P1]; not
  yet checked.

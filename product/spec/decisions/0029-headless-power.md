# 0029 — Headless product: power hold kept, no power-off command, a quiet idle state

- Status: accepted (ON8ST, 2026-11-20, answers to the HIS impact analysis §4, relayed by the openg7250 session and confirmed in this session)
- Date: 2026-11-20

## Context

The product is the main unit alone, headless; the controller is not part of it (0023). HIS 20
(`2a38b7f`): PH9 is the Main's own power-hold output (high keeps the unit powered, HYPOTHESIS),
PH5 is most likely the panel's power key over CTRL (HYPOTHESIS) and reads high with no panel.
Power-up without the controller is open (HIS 20 "Open").

ON8ST (2026-11-20): no `POWER_OFF`. A soft power-off that can only be undone by removing power
is unwanted behaviour. A "sleep" that the network can wake may be useful, but only once the
power draw is measured.

## Decision

1. The firmware keeps the power hold (PH9) high while it runs (HIS 20). This is a firmware
   rule; the network spec has no command that drops it.
2. PH5 (panel power key) is ignored in v1.0.
3. No management command switches the radio off. The radio is switched off by removing power.
4. **Quiet idle.** While no session runs on either level, the radio is as quiet as it can be
   without losing reachability: RF section in the safe state (HIS 85), no streams, the
   management channel, discovery and TCI listening as usual.
5. An explicit standby (`STANDBY`/`WAKE`) is a later option, decided after the power draw is
   measured; it is listed in the "pending hardware" annex.
6. Power-up without the controller is "pending hardware" (HIS 20 H1/H2).

## Consequences

- Spec part A scope: headless, switched off by removing power, quiet idle.
- Pending-hardware annex: standby, power-up path.

## Sources

- [HIS] HIS 20, HIS 85 (`2a38b7f`); ON8ST, 2026-11-20; decision 0023.

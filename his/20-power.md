# HIS 20 — Power bring-up

**Evidence:** g7250-emu Main boot console + PowerModel (R0) + g7250-base docs.

- The Main drives **PH9 high** (GPIOH bit9) as a power-hold early in boot and
  keeps it high; releasing it drops power (the stock shutdown path).
- **PH5** is the power-key input (pull-up). Held low >100 samples requests
  shutdown. Headless with no panel, PH5 stays high → the unit powers on and
  stays up (confirmed: PW-1 "H2/auto-start, PH5 high").
- **PWR ready:** the boot polls a PWR ready flag (offset 0x08 on the H72x Main)
  and must see it set before raising clocks. A clean-room firmware provides/awaits
  the real ready semantics; the emulator models it as "ready".
- **AXP223 PMIC** on I²C1 0x34 programs the rails ("Init PSU"): DCDC1 3.3V,
  DCDC2 1.2V, DCDC3 1.8V, DCDC5 2.5V, ALDO1 3.3V, DLDO1 1.8V. Errors are logged
  and boot continues.

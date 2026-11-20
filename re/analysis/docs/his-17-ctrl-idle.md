# HIS-17: the stock Control with an idle CTRL link

RE answer to HIS-17 for option A (decision 0023, ON8ST 2026-11-20): new firmware
replaces only the Main, the Control keeps its stock firmware, and the Main sends
nothing over CTRL. Two questions from the RE session:
(a) what the stock Control does when the Main stays silent on USART2;
(b) whether switching the radio on and off depends on the Control, and what a
silent Main must do so the radio can still be switched off.

Hardware facts and constraints from this note go into `his/20-power.md` and
`his/70-interlink.md`; the stock behaviour stays here.

## (a) Control with a silent Main

**Emulator (re/emu, 2026-11-20; option added on emu/integrate in 5a5a356).**
`control_run.py --usart2-tx` runs the stock
Control V1.0.1 alone, which is exactly a silent Main: nothing arrives on its
USART2. Result over 90 s host time:
- The Control boots through its full bring-up into its GUI service loop
  (verdict "running"; no dead poll, no fault, no hang). Its console shows no link
  error or retry message.
- On USART2 it sends one SLIP frame, a 0x01 settings image of 429 bytes (all
  zeros at that point, as expected for the first frames), and then nothing more.
- The single frame is very likely an emulator gap, not stock behaviour: the TC
  flag in the USART2 status register stays clear, so the TX-complete callback
  that frees the Control's TX lock never runs (`re/emu` follow-up). The firmware
  analysis below expects a 0x01 frame every 20 ms.

**Firmware analysis (g7250-base `docs/protocol.md`, "Link state machine",
VERIFIED unless noted).**
- The Control starts its 20 ms SLIP client early in boot and sends a full 0x01
  state image every 20 ms while its TX lock is free; there is no acknowledge.
- Requests (0x06) are repeated every 100 ms until a reply arrives.
- The Control has **no link timeout**; its display freezes on the last data
  until frames return (MEDIUM). There is no error screen in the analysis.
- Recovery needs no handshake.

**Conclusion.** A silent Main leaves the stock Control running in its GUI loop,
transmitting its periodic frames into the void, with a frozen display and no
error state. Nothing on the Control needs an answer from the Main to stay
healthy. Hardware observation of the panel with a silent Main is still open.

## (b) Power on/off and the Control

**Firmware analysis (g7250-base `main_unit/docs/flow.md` "Power-on and power-off",
`docs/protocol.md` 0x03, `control_unit/docs/peripherals.md` PCA9557,
`control_unit/docs/storage.md`; VERIFIED unless noted).**
- The **power key is read by the Main** on PH5. The Main decides on power-off
  (key held low), sets a power-off flag in its 0x03 frames, waits 100 ms, runs
  its shutdown and drops power with PH9.
- The **Control only reacts** to that flag: it saves its configuration file (the
  only time it does so) and holds PCA9557 bit 5 high during its own shutdown
  (role of bit 5 HYPOTHESIS: power hold or amplifier mute). It has no power
  control of its own over the Main.
- The Main powers the Control through the CTRL cable (owner; HIGH), so dropping
  PH9 removes the Control's supply as well.
- Power-on: the key starts the supply in hardware and the MCU holds it with PH9
  (hypothesis H1), or the MCU is on standby power and waits for PH5 (H2); see
  `re/emu/docs/M8c-R0-report.md`. Either way the Control is not in the path.

**Consequences for a silent Main.**
- The radio can be switched off without the Control: the new Main watches PH5
  and, on a key press, brings the radio to a safe state and drops PH9.
- The Control never sees a power-off flag, so it never rewrites its
  configuration file. Panel settings changed while the new Main runs are lost at
  power-off, as after a power cut in stock. No file write can be interrupted,
  which is the safe side.
- PCA9557 bit 5 is never set; since its role is unknown, this is an open point
  for a hardware check (does anything on the panel depend on it at power-off?).

## Open

- Hardware: panel behaviour with a silent Main (frozen screen expected).
- Hardware: role of PCA9557 bit 5.
- Emulator: model the USART TC flag so the Control's periodic frames run.

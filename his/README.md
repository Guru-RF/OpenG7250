# g7250-his — G7250 hardware-interface specification (clean-room)

This repository is the **clean-room hardware-interface specification (HIS)** for
the native-SDR G7250-P1 firmware. It is the **only** hardware source the new
firmware (`g7250-fw`) is allowed to read.

## Role in the project

```
g7250-base   RE documentation of the stock firmware/hardware   (RE side)
g7250-emu    emulator + harness; proves hardware BEHAVIOUR      (RE side)
     │  (behaviour, reviewed) ▼
g7250-his    THIS repo — behaviour-only interface spec          (the wall)
     │  (the firmware reads only this) ▼
g7250-fw     clean-room native-SDR firmware                     (clean side)
```

The HIS records **what the hardware does** (registers, sequences, timings,
protocols) as observed/derived through the emulator — never stock firmware
source. Each fact enters only after a clean-room review that confirms it is a
behavioural interface fact, not copied implementation.

## Status

Scaffold started once the emulator proved a stock Main boot to its service loop
and a Control boot to its GUI service loop (g7250-emu milestones M1 / M2).
Sections below are outlined; each is populated under the clean-room process.

## Sections (outline)

- `his/00-overview.md`      — scope, part classes, domains, conventions
- `his/10-reset-clock.md`   — reset vectors, clock tree, SysTick/HAL tick
- `his/20-power.md`         — PWR/PMIC bring-up, ready semantics, PH5/PH9
- `his/30-i2c-devices.md`   — I²C bus map, device bring-up order + handshakes
- `his/40-ethernet.md`      — CH394/LAN interface, default addressing
- `his/50-audio.md`         — codec + I²S audio path
- `his/60-display-input.md` — LTDC/DMA2D, GT911 touch, encoders, keypad
- `his/70-interlink.md`     — Main↔Control SLIP protocol
- `his/80-rf-fpga.md`       — FPGA/RF data path (later)

## Clean-room rules

No stock firmware source, no decompiler output, no copied code. Behaviour only,
each fact traceable to an emulator observation or a public datasheet. Local
commits on a branch; no push until the project's IP review clears it.

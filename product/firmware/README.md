# G7250 main-unit firmware

New firmware for the main unit of the Xiegu G7250. It implements the network interface
G7250-P2 (level 1) and later TCI with on-board DSP (level 2), as specified in `product/spec/`.

- Status: **planned. No code yet.** The project is in the spec phase; code starts in the build
  phase (decision 0028, Decision 4).
- Only the main unit is reflashed. The controller keeps its stock firmware, and CTRL stays idle
  (decision 0023).

## Language and toolchain (decision 0033, proposed)

Rust, `no_std`, on Embassy (`embassy-stm32`). Hardware drivers are written against
`embedded-hal` traits, so that protocol and state code also builds and is tested on the host
(`cargo test`, against `testbench/` and `product/refmodel/`).

## Inputs

| Input | What it gives |
|---|---|
| `product/spec/spec/network-interface.md` | the network interface: parts A (management, safety core) and B (G7250-P2) |
| `product/spec/spec/part-c-tci-profile.md` | the TCI profile (level 2) |
| `product/spec/spec/register-map.yaml` | the G7250 register map (generated from the spec) |
| `his/` in the umbrella repository, cleared commits only | hardware facts: parts, pins, buses, safe states |
| `product/spec/decisions/` | design choices, one file each |

Clean room: the firmware is built only from these inputs and public datasheets. Never from
the reverse-engineering side (`re/`), from disassembly or from stock firmware.

## Platform rules from the HIS

Every rule below is a MUST from the HIS at `2a38b7f`. They are listed so that nobody starts
without them; the HIS section is the authority.

- **Image placement** (HIS 10): the image starts at 0x08020000 with its vector table there.
- **Leave the vendor path intact** (HIS 15): never write sector 0 (0x08000000–0x0801FFFF), never
  change the option bytes, treat the EEPROM at I²C1 0x50 as read-only, do not use the Backup
  SRAM or the RTC backup registers.
- **FPGA** (HIS 15): it configures itself; never touch its configuration flash.
- **Safe state first** (HIS 85): set the RF control pins to their safe state before anything else
  in the RF section, and return to it whenever not transmitting. Bias DAC channels 2, 7, 8 at 0
  when not transmitting.
- **CTRL idle** (HIS 70): never transmit on USART2; keep PD5 high or high-impedance, never low.
- **Power** (HIS 20): switching off is the Main's job (power key PH5, power hold PH9; both
  HYPOTHESIS). Never enable a PMIC rail the HIS lists as off, never raise a listed rail.
- **FPGA bus** (HIS 80): never send commands 0x05/0x06, 0x09/0x0A.

## Planned structure (build phase)

From decision 0028 and spec A1.8:

- a **boot stage** at 0x08020000 that picks one of two image slots, runs the trial boot and
  the rollback, and is never updated over the network;
- two **image slots** and a configuration area in the application area (sectors 1–7);
- a **streaming installer** that runs from RAM and writes an owner-supplied stock image over
  the network (spec A1.8a item 3).

The exact flash layout is a firmware design document, to be written at the start of the build
phase.

## Before the first flash

Every image is first tested in full on the RE side's emulator, as a black box: the product side
delivers the ELF and the spec-based tests and gets back pass or fail and the image's own
console and network output only (decision 0034, proposed).

The rollback drill F1 on the real radio (HIS 15) must show that the vendor path through the
controller can install both a stock image and an image of this firmware.

## Licence

GPL-3.0-or-later, © 2026 ON8ST; Apache-2.0 only if a vendor SDK forbids GPL (decision 0018).

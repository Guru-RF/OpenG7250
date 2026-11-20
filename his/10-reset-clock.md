# HIS 10 — Reset and clock

**Evidence:** the application load base and the bootloader region come from the
vendor image layout as analysed in g7250-base (**rests on image analysis /
disassembly**). Emulator observation (re/emu M1/M2): both stock images run when
loaded at 0x08020000 with the vector table there.

## Units
| Unit | MCU class |
| --- | --- |
| Main | STM32H72x |
| Control | STM32H743 |

## Debug and random-number hardware

- **SWD:** PA13 (SWDIO) and PA14 (SWCLK), per the ST datasheet. The factory
  application does not reconfigure these pins (HIGH: absent from the pin map),
  so SWD stays available. Whether pads or a header are reachable on the Main
  board is not known (`90-needs-hardware.md`).
- **RNG:** both candidate parts for the Main (STM32H725xG and H735xG) have a
  true random-number generator, per the ST datasheet (HIGH for "present", since
  the exact part is MEDIUM; confirm with DBGMCU_IDCODE and the part marking).

## Image placement (platform constraint)
- The bootloader occupies 0x08000000–0x0801FFFF and is not part of the
  application image.
- The application image is loaded at **0x08020000**, with its vector table at
  that address. Any replacement image must follow this placement.

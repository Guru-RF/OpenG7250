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

## Image placement (platform constraint)
- The bootloader occupies 0x08000000–0x0801FFFF and is not part of the
  application image.
- The application image is loaded at **0x08020000**, with its vector table at
  that address. Any replacement image must follow this placement.

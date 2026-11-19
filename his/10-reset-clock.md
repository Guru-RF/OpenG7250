# HIS 10 — Reset and clock

**Evidence:** g7250-emu boot runs (M1/M2) + g7250-base reset disassembly (data).

## Reset entry
| Unit | Load base | Initial MSP | Reset handler |
| --- | --- | --- | --- |
| Main (H72x) | 0x08020000 | 0x24050000 | 0x08024554 |
| Control (H743) | 0x08020000 | 0x24080000 | 0x080235AC |

Vector table at the load base (SCB->VTOR = 0x08020000). The bootloader region
0x08000000–0x0801FFFF is not part of the application image.

## Clock / HAL tick
- Main HCLK 275 MHz; Control HCLK 240 MHz (timer clock), both from their PLLs.
- The 1 ms HAL tick is driven by SysTick off the processor clock. **Interface
  fact (emulator-confirmed):** every HAL timeout and HAL_Delay depends on this
  tick; the I2C-wait and 1000 ms boot delays only progress once SysTick runs.
  A clean-room firmware must start SysTick before any HAL_Delay / bus-wait.

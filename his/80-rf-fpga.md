# HIS 80 — RF front-end / FPGA interface

**Evidence:** signals and command codes from g7250-base peripherals doc
(VERIFIED in the firmware analysis, i.e. **rests on disassembly**). Emulator
observation (re/emu D2): with a fused GPIOE+FPGA model that implements this
bus, the stock Main completes its FPGA bus check with zero bus errors and reads
version 1.0.0 and DRDY-paced RX I/Q. The NCO clock and the absolute sample rate
are not measured.

The RF I/Q front end is an **FPGA reached over an 8-bit parallel bus on GPIOE**
(no FMC), driven by the MCU in software.

## Signals
| Signal | Pin | Use |
| --- | --- | --- |
| D0–D7 | PE0–PE7 | bidirectional data; the MCU switches the pin direction |
| CMD | PE8 (with PE9) | pulsed together to latch a command byte |
| STB | PE9 | per-byte strobe |
| DRDY | PE10 | rising edge signals sample data ready; PE10 can raise EXTI10 |

## Commands
| Code | Function |
| --- | --- |
| 0x00 | loopback/test register: a written byte reads back |
| 0x01 | 24-byte config frame: status flags, three big-endian 32-bit NCO words, per-rate calibration, rate index |
| 0x02 | status read (flag bits + three 16-bit values incl. ADC peak) |
| 0x03 | TX I/Q write — two signed 24-bit values per sample |
| 0x04 | RX I/Q read — two signed 24-bit values per sample, 8/4/2/1 per DRDY for rate index 0–3 |
| 0x08 | 3-byte FPGA version read |

## Timing / data
- **NCO:** 32-bit phase words for a 122.88 MHz clock (f × 2³² / 122.88 MHz),
  frequency folded into 0–61.44 MHz with a spectral-inversion flag.
- **Sample rate:** rate index 0–3 → 384/192/96/48 kS/s I/Q; DRDY (PE10) at
  ~48 kHz. (Absolute rate unmeasured.)

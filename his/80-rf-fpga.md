# HIS 80 — RF front-end / FPGA interface

**Evidence:** g7250-base peripherals doc (FPGA bus, VERIFIED) + g7250-emu Main
boot (the FPGA bus-test errors locate the interface). Behaviour-only.

The RF I/Q front end is an **FPGA reached over an 8-bit bit-banged parallel bus
on GPIOE** (no FMC). A clean-room firmware must drive exactly this interface.

## Signals
| Signal | Pin | Use |
| --- | --- | --- |
| D0–D7 | PE0–PE7 | bidirectional data; direction switched via GPIOE_MODER |
| CMD | PE8 (with PE9) | pulsed together to latch a command byte |
| STB | PE9 | per-byte strobe |
| DRDY | PE10 | rising-edge interrupt (EXTI15_10); runs the sample routine |

## Commands
| Code | Function |
| --- | --- |
| 0x00 | loopback/test register (boot bus-check writes/reads 0–255) |
| 0x01 | 24-byte config frame: status flags, three big-endian 32-bit NCO words, per-rate calibration, rate index |
| 0x02 | status read (flag bits + three 16-bit values incl. ADC peak) |
| 0x03 | TX I/Q write — two signed 24-bit values per sample |
| 0x04 | RX I/Q read — two signed 24-bit values per sample, 8/4/2/1 per IRQ for rate index 0–3, 192-sample blocks |
| 0x08 | 3-byte FPGA version read |

## Timing / data
- **NCO:** 32-bit phase words for a 122.88 MHz clock (f × 2³² / 122.88 MHz),
  frequency folded into 0–61.44 MHz with a spectral-inversion flag.
- **Sample rate:** rate index 0–3 → 384/192/96/48 kS/s I/Q, decimated to the
  48 kHz chain; DRDY (PE10) at ~48 kHz. (Absolute rate unmeasured.)
- **Errors are log-only** in stock: a bus-test mismatch or an unchanging first
  RX sample is logged, with no re-init or reset.

## Emulator status (g7250-emu)
Not yet modelled: the base GPIOE absorbs the Main's init bit-bang, so the stock
Main boots to its service loop but logs "[ERR] FPGA BUS Error" (the read-back
loopback has no FPGA driving the data lines) and no live I/Q flows. A **fused
GPIOE+FPGA model** (M3) must: (a) echo the 0x00 loopback for the bus test, (b)
return the 3-byte version, (c) drive PE0–7 on reads and PE10/DRDY at the rate
index, and (d) source/sink 24-bit I/Q. This needs a C# peripheral wired to the
GPIOE pins (both the MCU-output→FPGA and FPGA→MCU-input directions) plus the
exact STB/CMD handshake — the clean-room firmware target for the RF path.

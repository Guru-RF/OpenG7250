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

## Emulator status (g7250-emu) — MODELLED (2026-11-19)

A fused GPIOE+FPGA port (g7250-emu models/csharp/G7250Gpioe.cs) now implements
this interface: the loopback test register (0x00), the 3-byte version (0x08 ->
1.0.0), and DRDY (PE10) pulsing a changing 24-bit RX I/Q. The stock Main boots
to "Check FPGA BUS... Check complete!" with no FPGA errors (m1_run --fpga). The
remaining realism (true 48 kHz NCO-accurate I/Q, TX path) can build on this.

### Original note
Not yet modelled: the base GPIOE absorbs the Main's init bit-bang, so the stock
Main boots to its service loop but logs "[ERR] FPGA BUS Error" (the read-back
loopback has no FPGA driving the data lines) and no live I/Q flows. A **fused
GPIOE+FPGA model** (M3) must: (a) echo the 0x00 loopback for the bus test, (b)
return the 3-byte version, (c) drive PE0–7 on reads and PE10/DRDY at the rate
index, and (d) source/sink 24-bit I/Q. This needs a C# peripheral wired to the
GPIOE pins (both the MCU-output→FPGA and FPGA→MCU-input directions) plus the
exact STB/CMD handshake — the clean-room firmware target for the RF path.

**M3 attempt finding (g7250-emu):** a C# `G7250Fpga` model (loopback 0x00 +
version 0x08 + DRDY output) is written and compiles, but naively wiring all of
PE0–PE10 to it breaks the boot right after "System started." — GPIOE is heavily
multiplexed (EXTI lines, RF band switching), so an FPGA driving those pins
outside a bus transaction triggers spurious EXTI/behaviour. The correct model
must drive the data lines only during an active FPGA read strobe and must not
disturb the other GPIOE uses (EXTI-aware, transaction-scoped). That is the M3
work; the stock boot is unaffected because the errors are log-only.

**M3 approach pinned (g7250-emu, 6 attempts):** (1) wiring a separate C# FPGA to
the GPIOE pins breaks the boot — Renode GPIO is unidirectional and never
high-impedance, so the FPGA forces pins that are also EXTI lines (PE3/4/6/10).
(2) Subclassing Renode's STM32_GPIOPort to intercept IDR fails: its
ReadDoubleWord/WriteDoubleWord are not virtual. (3) The viable path is a
from-scratch FUSED GPIOE+FPGA port (one C# peripheral that is the GPIO port and
computes IDR itself, returning FPGA data on reads with MODER giving direction).
A first such port (`G7250GpioeFpga`, models/csharp/G7250Gpioe.cs) compiles and
replaces gpioPortE, but stalls the boot just after PH9 — reimplementing the
STM32H7 GPIO-port semantics the firmware's early init depends on must be exact
(MODER/IDR/ODR/BSRR/AFR/PUPDR + the AF-timer and EXTI/syscfg routing). Finishing
that, plus the STB/CMD read/write handshake and DRDY-paced 24-bit I/Q, is the M3
deliverable.

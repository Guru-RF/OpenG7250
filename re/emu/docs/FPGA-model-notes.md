# FPGA model notes (D2 / M3)

Moved from the HIS (`his/80-rf-fpga.md`, tag `his-draft0`) at gate review 1:
these notes describe the emulator, not the hardware. Text unchanged below;
paths are relative to `re/emu/`. Current state: `docs/EMU-JOB-STATUS.md` (D2)
and `docs/D2-action-plan.md`.

## Emulator status (g7250-emu, now `re/emu/`) — MODELLED (2026-11-19)

> `g7250-emu` and `g7250-base` below are historical names; see `docs/REPO_LAYOUT.md`, "Historical names".

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

# D2 — FPGA fused model: action plan (M3)

> **STATUS: DONE (2026-11-19).** The fused GPIOE+FPGA port
> (models/csharp/G7250Gpioe.cs) is implemented and wired as `m1_run.py --fpga`.
> The stock Main boots to "Check FPGA BUS... Check complete!" with zero FPGA bus
> errors, version read 1.0.0, and DRDY-paced RX I/Q. Keys to the fix: (1) BSRR
> set-wins ordering (a data byte is written as reset-0xFF + set-bits, and my
> handler had reset clobbering set); (2) classify_tail treating the DRDY EXTI
> servicing as a poll-hang. The notes below are the (now-completed) plan.

Everything else in the A–E emulator job is done (A, B1, B2, C/C2, D1, E1–E4).
D2 — the fused GPIOE+FPGA model for live RF I/Q — is the one open item. This is
the concrete plan to finish it, based on what the in-session attempts established.

## What is already in place
- Interface fully specified: `his/80-rf-fpga.md` (then in the separate `g7250-his` repo, historical) (D0–7/CMD/STB/DRDY,
  command set, NCO/rate, 24-bit I/Q).
- A first fused port `models/csharp/G7250Gpioe.cs` (`G7250GpioeFpga`) that
  compiles, replaces `gpioPortE`, computes IDR itself and handles the 0x00
  loopback + 0x08 version. Left UNWIRED.
- Ruled out: wiring a separate FPGA to the GPIOE pins (Renode GPIO is
  unidirectional / never high-Z → forces EXTI pins PE3/4/6/10, breaks the boot),
  and subclassing `STM32_GPIOPort` (its Read/WriteDoubleWord are not virtual).

## Current blocker (diagnosed)
With `G7250GpioeFpga` in place the boot PROGRESSES but ~40× too slowly: the HAL
tick advances (961→966 over ~75 s wall) while the CPU sits in the clock/tick
init `FUN_08027774` (~PC 0x08027810), so AXP223 is never reached in practical
wall time. Cause: the port's GPIOE semantics are not yet an exact match, so the
firmware's early clock/calibration loop polls GPIOE in a hot path against a
slow, managed, not-quite-right port.

## Action plan
1. **Make the fused port an exact STM32H7 GPIO port.** Model every register the
   firmware uses with correct semantics: MODER, OTYPER, OSPEEDR, PUPDR, IDR
   (input = pull resistor when unconnected, output = ODR), ODR, BSRR (set/reset,
   incl. the reset-wins rule), LCKR (lock), AFRL/AFRH. Validate by diffing a
   boot trace against the stock `gpioPortE` up to "System started" — they must
   read/write identically.
2. **Find the hot GPIOE read at FUN_08027774.** From the diff, identify which
   GPIOE register/pin the clock-init loop reads and what value the stock port
   returns there; make the fused port return the same. (Likely a pin level or an
   AF/IDR read whose wrong value lengthens the loop.)
3. **Confirm the boot reaches the service loop** with the fused port at normal
   speed (same milestone as plain `gpioPortE`: AXP → EEPROM → … → service loop),
   with FPGA bus errors GONE (the 0x00 loopback now echoes).
4. **Add the read/write bit-bang handshake** using MODER for direction: write
   strobe stores the byte, read strobe presents the next byte on D0–7. Cover the
   command set (0x00/0x01/0x02/0x03/0x04/0x08).
5. **Wire EXTI + DRDY.** Re-add `[0-15] -> syscfg#4@[0-15]`; drive PE10 (DRDY) as
   a ~48 kHz interrupt source (a `LimitTimer`) so the sample routine runs.
6. **Source/sink 24-bit I/Q** on cmd 0x04/0x03: feed a synthetic RX signal
   (changing, so the TIM6 health check is happy) and accept TX writes; scale per
   the rate index and NCO words.
7. **Verify:** boot clean (no FPGA errors), DRDY firing, RX I/Q flowing; add a
   boot-milestone assertion ("no FPGA BUS Error") and wire the port into m1_run
   behind a flag.

## Effort / risk
A multi-iteration M3 task: step 1–3 (exact GPIO port) is the hard, fiddly part
and needs iterating the diff against the stock port; steps 4–7 build on the
already-written bit-bang logic. The RF sample timing is "unmeasured" in the RE,
so the I/Q rate is modelled, not asserted. Best done as its own focused session.

## Decisive finding (performance, not correctness)
The stock boot does NOT read GPIOE around the clock-init, so the earlier
"wrong clock strap" theory is out. With the fused `G7250GpioeFpga` the Renode CPU
thread nearly stops (executed +1M over 55 s ≈ 18k instr/s, vs. millions normally)
once GPIOE is driven hard — a **runtime-compiled (`i @...cs`) peripheral in the
hot GPIOE path throttles the emulation**. Implication for step 1: the fused GPIO
port must be built as a **compiled Renode plugin assembly** (a .dll added to the
build / `--plugin`), not loaded with `i @file.cs`, so the per-access path is
native. That is an infrastructure step (set up a Renode plugin project) and is
the real precondition before the 7 steps above are worth iterating.

# HIS 00 — Overview

**Scope.** The hardware interface of the G7250 as new firmware must drive it:
parts, buses, addresses, pins, wiring, electrical values and the FPGA's bus
interface. Two MCUs: Main (STM32H72x class) and Control (STM32H743 class),
linked by a serial line over the CTRL cable.

**Conventions.** Confidence tags (VERIFIED/HIGH/HYPOTHESIS) mirror the source.
Every section states its evidence: an emulator observation (`re/emu`), a public
datasheet, or, where that is all there is, that the fact rests on disassembly
(`re/analysis`, g7250-base). Never stock firmware code or behaviour.

**Process.** Candidate facts come from the RE side (`re/analysis`, `re/emu`),
pass the gate review (`GATE-REVIEW.md`: hardware fact, not stock behaviour),
then land here. `product/firmware` reads this spec for hardware facts.

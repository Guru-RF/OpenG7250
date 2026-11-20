# M0 — platform spike: Renode go/no-go

**Decision: GO.** Renode 1.17.0 (pinned, native arm64) is the emulation
platform for g7250-emu (historical name of `re/emu/`). All Cortex-M7 features the stock G7250 firmware relies
on are present in Renode's own `cortex-m7` model, and emulation speed clears the
§2.3 no-go threshold even on a loaded host. One concrete design constraint falls
out for M1 (the FPGA MMIO path — see below).

This is the M0 exit per spec §14 (go/no-go + measurement report). Raw numbers
are regenerated into `.private/m0/m0_report.md` by the harness.

## Setup

| Item | Value |
| --- | --- |
| Emulator | Renode **1.17.0** `osx-arm64-portable` (native Apple Silicon; no mono/dotnet install) — pinned in `tools/` |
| Platform | Renode's own `platforms/cpus/stm32h743.repl` (cortex-m7, 16 MPU regions, DWT, flash @0x08000000, AXI SRAM 512 KiB @0x24000000) |
| Toolchain | `arm-none-eabi-gcc` 16.2.0, `-mcpu=cortex-m7 -mfpu=fpv5-d16 -mfloat-abi=hard` |
| Test firmware | `firmware-tests/m0/` (clean-room; 688 B) |
| Harness | `harness/g7250emu/m0_run.py` — two one-shot PC hooks on the loop markers; no watchpoints, no RunFor |
| Host at measurement | 12-core Apple Silicon, load average ~5.5 (an iOS-simulator AetherApp held ~1 core) |

## Feature checks — all PASS

| Cortex-M7 feature | Result | Note |
| --- | --- | --- |
| **double-precision FPU** (VDIV.F64 / VADD.F64) | **PASS** | `sum_{1..100000} 1/i` computed in `double`; result in range; no undefined-instruction fault |
| single-precision FPU | PASS | |
| **MPU** enable/disable (16 regions) | **PASS** | region configured + enabled + read back + disabled, no fault |
| **DWT CYCCNT** | **PASS** | monotonic, non-zero (2.5e8 cycles over the loop) |
| cache-maintenance writes (ICIALLU/DCCIMVAC/DCCISW) | **PASS** | accepted as no-ops, no BusFault — stock cache sequences will not crash the model |
| fault during run | none | the fault handlers (which would write 0xFA17) never fired |

The §2.3 no-go conditions — dp-FPU or MPU going wrong — did **not** occur.

## Host throughput (best of 3 runs, load ~5.5)

| Metric | Value | Meaning |
| --- | --- | --- |
| host wall time | 10.76 s | for 20,000,000 MMIO stores + boot |
| guest instructions | 1.0e8 | ~5 instr per GPIO iteration |
| **MMIO rate** | **~1.86e6 MMIO/s** | each store dispatched to the C# GPIO model |
| host speed | ~9.3 guest-MIPS | **on this 100%-MMIO workload** (worst case) |
| emulation speed | **~0.093× realtime** (at PerformanceInMips=100) | pure-MMIO worst case |

Runs were within ±2% (1.82–1.86e6 MMIO/s). Numbers are **pessimistic**: the host
was loaded (~5.5), and the workload is 100% MMIO — the slowest possible path,
since every iteration crosses into a peripheral model. Real firmware is mostly
RAM/compute and will run several× faster per instruction. A pure-CPU rate was
not isolated in M0 (no boot-phase marker); bracket it in M1.

## Reading against the budgets (§8.7)

- The §2.3 no-go line is **< 0.05× realtime for Main boot without the FPGA
  stream**. The measured **0.093×** is already above that **on the worst-case
  pure-MMIO stress under load** — real boot will sit well above 0.05×. **GO.**
- The §4 derivation wanted **≥ 7e6 MMIO/s**. We see **~1.86e6 MMIO/s** for
  literal per-access MMIO on Renode's generic model under load. This does **not**
  fail M0, but it is the key quantitative finding (see below).

## Finding that feeds M1 (confirms risk R3)

Literal, per-access MMIO tops out around **~2e6 accesses/s** here. The stock FPGA
interface is bit-banged on GPIOE with a 48 kHz DRDY; modelling that one GPIO bit
at a time would cost millions of MMIO/s and blow the budget. **Conclusion:** the
FPGA/GPIOE path **must** be a *fused / behavioural* model (one access per sample
or per transfer, not per bit), exactly as spec risk **R3** anticipates. Ordinary
register peripherals (RCC, PWR, UART, SPI, timers) are far below that access
rate and are fine at register level. This is a concrete input to the M1 model
inventory, not a blocker.

## Method notes (reusable for later milestones)

- **No watchpoints for timing**: a sysbus watchpoint forces Renode's slow
  memory path and made a 20M-store run hang at 0% CPU. Replaced by one-shot
  **PC hooks** on marker functions.
- **No `RunFor` for termination**: after the firmware sets `done` it idles in
  `WFI`; with no scheduled interrupt the virtual clock cannot advance, so
  `RunFor` stalls. The **done PC hook pauses the CPU** instead, ending the
  measurement exactly at `done` (idle instructions never pollute the counts).
- Renode quits on stdin EOF; the harness keeps stdin open until the done event
  is observed, then terminates the process.
- Bus reads inside a CPU hook use `self.Bus.ReadDoubleWord(addr)`
  (`ReadDoubleWordFromBus` is protected; `self.Machine` does not exist).

## Reproduce

```
python3 harness/g7250emu/m0_run.py --runs 3 --mips 100
```

Needs `arm-none-eabi-gcc` and the pinned Renode in `tools/`. Output (ELF, run
script, events, generated report) lands in the git-ignored `.private/m0/`.
Re-run on a quiescent host for a cleaner throughput figure.

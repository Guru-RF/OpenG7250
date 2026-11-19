# M0 test firmware (clean-room)

Our own tiny Cortex-M7 program for milestone **M0** (platform spike). It is not
derived from any vendor image; it exists only to prove that Renode's cortex-m7
model supports what the stock G7250 firmware needs, and to measure host speed.

It exercises, and reports to a fixed result block at the top of AXI SRAM
(0x2407F000):

| Feature | Why it matters |
| --- | --- |
| double-precision FPU (VDIV.F64/VADD.F64) | the stock DSP uses it; a missing dp-FPU would fault |
| single-precision FPU | RX/TX math |
| MPU enable/disable (16 regions on the H7) | stock configures MPU regions at boot |
| DWT CYCCNT | cycle timing |
| cache-maintenance register writes | must be accepted as no-ops, not fault |
| GPIO bit-bang loop | MMIO throughput (host MMIO/s) |

Two marker functions, `m0_mark_loop_start` and `m0_mark_done`, bound the GPIO
loop; the Renode harness puts one-shot PC hooks on them to timestamp the loop
without watchpoints (which force the slow memory path) and without RunFor
(which stalls on the post-done WFI idle).

## Build & run

```
make                                   # -> ../../.private/m0/m0_test.elf
python3 ../../harness/g7250emu/m0_run.py --runs 3   # build + measure + report
```

Requires `arm-none-eabi-gcc` (cortex-m7, fpv5-d16) and the pinned Renode in
`tools/`. All output goes to the git-ignored `.private/m0/`.

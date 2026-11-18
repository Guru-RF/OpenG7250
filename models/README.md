# models/ — peripheral and device models

Clean-room models for the G7250 emulator (spec §13 `models/`). Everything here
is written from public datasheets, the ST reference manual (RM0468, used as
DATA), and the RE facts in `g7250-base` — never from stock firmware code. Each
model carries source + confidence tags that mirror the RE docs
(VERIFIED / HIGH / MEDIUM / HYPOTHESIS).

## Layout

| path | contents |
| --- | --- |
| `devices/` | board devices hanging off the MCU (CH394, codec, PMIC, FPGA, …) |
| `system/`  | MCU-internal blocks not covered by Renode's STM32H7 base |
| `python/`  | Renode `PythonPeripheral` scripts (IronPython 2.7) wired from the `.repl` |

**Runtime split — important.** Renode `PythonPeripheral` scripts run in
**IronPython 2.7**, so files loaded *into Renode* (via `filename:` in a `.repl`)
must be 2.7-clean (no f-strings, no type annotations). Model *logic* that we
also unit-test on the host (e.g. `devices/ch394.py`) is written for **CPython 3**
and kept transport-agnostic, so the same logic can later be driven by a Renode
shim without being rewritten. The two never import each other across the
version boundary.

## What exists now (M1 scaffolding)

| model | status | topology | verified how |
| --- | --- | --- | --- |
| `devices/ch394.py` | register-file logic + A1.12 check | **SPI6** slave, INT on PC13 (VERIFIED). Not yet wired as an SPI slave — needs the image to drive SPI6 frames. The class is transport-agnostic so the wiring lands without a rewrite. | `python3 models/devices/ch394.py` (self-test: forced default IP 192.168.3.199 → `a1_12_ok`) |

## Deliberately *not* modelled as sysbus peripherals yet

These are commonly misfiled as memory-mapped peripherals; on the G7250 they are
not, so a sysbus stub would be wrong and is deferred to the milestone that can
drive them from the real access path:

- **FPGA** — reached by **GPIOE bit-bang** (SPI-like over GPIO), not the memory
  bus; a 48 kHz DRDY sample stream. M0 finding **R3**: when the stream matters
  (M3+) it must be a *fused / behavioural* model (one access per sample, not per
  bit). For M1 "boot to main loop" the stream is not running; the base GPIOE
  model absorbs the init pin-wiggles without faulting, so no FPGA sysbus
  peripheral is added here.
- **I²C1 devices** (EEPROM 24C, AXP223 PMIC, VC6, AIC3204 codec) — I²C slaves
  behind the STM32 I²C1 controller, addressed by the firmware's I²C transfers.
  They attach to the controller, not the sysbus, and are driven by the image.
- **CH394** — SPI6 slave (see above).

The boot-time power/clock/flash readiness that the firmware *polls* (RCC/PWR/
FLASH ready & lock bits, the AXP223 bring-up) is handled at the register level
and is the first polling-loop work of the M1 boot runner — see
`harness/g7250emu/m1_run.py` and the observe layer below.

## Observe layer (harness-side, not a model)

Strict mode, the hang detector, and the MMIO heatmap live in
`harness/g7250emu/observe.py` (host CPython 3), because they instrument the run
rather than model hardware. They are driven from monitor commands + `cpu PC`
sampling (no watchpoints, no `RunFor` — M0 method notes) and self-test on
synthetic and real captured logs: `python3 harness/g7250emu/observe.py
--selftest`.

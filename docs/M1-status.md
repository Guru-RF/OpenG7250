# M1 — stock Main boot: status

Milestone M1 (spec §14): *stock Main boot to the main loop*. This records what
is built and verified **without** the decrypted image, and the exact steps that
light up **when** the image is supplied locally.

Branch: `m1-main-boot` (local only — no push; see `SECURITY.md` and the
clean-room/legal rules). Regression gate: `bash tests/baseline/m1_smoke.sh`
(**11 checks, ALL PASS**).

## Done and verified (image-independent)

| Area | Deliverable | Verified |
| --- | --- | --- |
| Platform | `platforms/g7250_main.repl`: H72x deltas on Renode's H7 base — 320 KiB AXI SRAM (`0x24000000..0x2404FFFF`), SPI1/2/3/6 added (base had only spi4) | loads on pinned Renode; map + SPI confirmed |
| Image intake | `harness/g7250emu/imagemap.py`: hash-verified local image-map, refuses in-worktree / blank hash / absent — **never decrypts** | refusal path tested |
| Observe | `harness/g7250emu/observe.py`: strict mode + hang detector (poll- vs idle-hang) + MMIO heatmap; parser matches the real Renode log format | self-test + real captured log |
| Boot runner | `harness/g7250emu/m1_run.py`: loads platform, applies tags, enables observe, resolves image, PC-samples for the hang verdict; refuses cleanly with no image | refusal path tested |
| Map extras | `harness/g7250emu/platform_extras.py`: Tags for H72x-only blocks (TIM23/24, UART9, USART10) and unmodelled blocks (DAC1, MDMA) | Tags accepted by Renode |
| CH394 | `models/devices/ch394.py`: register-file logic + **A1.12** default-IP check (192.168.3.199) | self-test |
| I²C1 slaves | `models/devices/i2c_devices.py`: EEPROM24C, AXP223, VC6, AIC3204 | self-test |
| Power | `models/system/power_model.py`: PH5/PH9 state machine, H1/H2, the no-panel pitfall + P-1 fix (R0 / M8c) | self-test |
| Bias trim | `models/devices/bias_trim_plant.py`: ADC1+DAC closed-loop plant | self-test incl. trim loop |
| SPI sinks | `models/devices/spi_sink.py`: generic SPI1/SPI2 write-mostly sink | self-test |

**Model runtime split:** device/plant logic is CPython-3 and transport-agnostic
(host-tested now); Renode `PythonPeripheral` shims (IronPython 2.7) wrap them
when the image drives the buses. The two never import across that boundary.

## Deliberately deferred (needs the image / a later milestone)

- **FPGA**: GPIOE bit-bang, not a sysbus peripheral; the fused model (M0 R3) is
  M3 work when the 48 kHz stream matters. The base GPIOE absorbs M1 init wiggles.
- **DAC1 / MDMA**: no STM32 model in this Renode build — tagged for now; wire a
  Python shim (DAC1 → `bias_trim_plant`) if the boot actually uses them.
- **SPI/I²C slave attachment**: controllers are present; attaching the CH394 and
  I²C/SPI device logic as actual bus slaves is driven by the firmware's frames.

## When the decrypted Main image arrives

1. Put it outside any git work tree; set `image_map = /abs/dir` in `local.config`
   (git-ignored) and fill `images/manifest.yaml` `image_sha256` for `main`.
2. `python3 harness/g7250emu/m1_run.py` — it loads at `0x08020000`, MSP
   `0x24050000`, reset `0x08024554` (VERIFIED), applies the tags + observe, and
   reports the hang verdict + MMIO heatmap to `.private/m1/`.
3. Iterate the boot: the heatmap + poll-hang verdict point at each never-ready
   register (RCC/PWR/FLASH ready & lock, AXP223 bring-up); feed it from the
   matching model until the boot reaches the main loop.
4. Attach CH394 to spi6 and confirm **A1.12** (default IP in the chip); target
   **60 s virtual time without a hang** for the M1 exit (A1.1–A1.3, A1.7–A1.10,
   A1.12 for Main solo).

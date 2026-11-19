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

## First real boot (decrypted Main image supplied) — 2026-11-19

Image wired via the local image-map (`local.config` + `images/manifest.yaml`
hashes, both kept local/untracked). `python3 harness/g7250emu/m1_run.py`.

**Result: the Main runs its full early init and then gets stuck crawling through
the I2C1 device bring-up — every I2C byte burns a 100 ms HAL timeout because
I2C1 has no slaves attached.**

What runs (PC climbs 0x08023BD4 → 0x08041C52): FPU enable, FLASH ACR, RCC/PLL1-3
config, FMC `0x30D2` tweak, VTOR, DWT, the full MPU region set, ADC, USART1,
GPIO A..K, "System started", PH9 high — as `startup.md`/`flow.md` describe.
**SysTick ticks** (the HAL tick at RAM `0x24005A74` advances; `m1_run` sets
`nvic Frequency 275000000` so the 1 ms rate is correct).

The bottleneck (identified by the OpenG7250 RE, static analysis): the loop at
`0x0802B14E` is HAL `I2C_WaitOnTXISFlagUntilTimeout`. With no slave, Renode's
I2C1 ISR stays `0x1` (TXE only) — never TXIS (bit1) or NACKF (bit4) — so the
wait exits **only via its timeout** (AXP leg 100 ms). The boot does inch forward
(tick advances, PC reaches the EEPROM/service-loop region), but each I2C byte
costs 100 ms of virtual time, so the AXP/EEPROM/VersaClock/codec bring-up would
take minutes of virtual time. `observe` flags the dominant `i2c1 +0x18
(InterruptAndStatus)` poll. The first stalled transfer is `CR2=0x1012068` →
SADD `0x68` → **7-bit 0x34 = AXP223 PMIC** (first device in the `flow.md` order).

**Main I2C1 slave map + bring-up (public `main_unit/docs` + OpenG7250 RE,
VERIFIED unless noted):**

| 7-bit | device | driver | notes |
| --- | --- | --- | --- |
| 0x34 | AXP223 PMIC | `FUN_0804A8E8` | "Init PSU"; write seq 0x10=02,0x12=00,0x13=01,0x21=11,0x22=1E,0x23=3C,0x25=1E,0x28=1A,0x15=0B,(10 ms),0x10=6E,0x12=08; then a 256-byte dump read. Errors logged, init continues |
| 0x50 | 24Cxx EEPROM | `FUN_0803C5E4` | settings block @0x0000 (0x1A8 B) valid iff bytes 0x000,0x1A3,0x1A4 == 'd' (0x64); reads Backup SRAM `0x38800000` first, then EEPROM; on mismatch logs "[ERR] EEPROM Settings data incorrect" and continues. Loader called with force-reset 1 → a blank EEPROM does NOT block |
| 0x18 | TLV320AIC3204 codec | `FUN_0804A65C` | init/enable errors logged |
| 0x68→0x6A | VersaClock 6 (5P49V6) | `FUN_0804ABBC` | 0x70-byte table from flash `0x0807F840` from reg 0; tries 0x68, after 100 ms 0x6A, logs, continues |

Bus: I2C1 @0x40005400, init `FUN_080218B4`, TIMINGR `0x00D049FB` (~400 kHz),
one handle `0x24004F38`. Init order in `main` `0x0802239C`: I2C-init → "System
started" → PH9 → 1000 ms → AXP223 → 1000 ms → CRC → EEPROM (3 blocks) → network
defaults → VersaClock 6 → AIC3204. **Every device's error path continues**, so
functional-but-minimal slaves are enough to reach the main loop.

### Next step (milestone item: I2C1 slave shims)

Attach ACKing I2C1 slaves so transfers complete at full speed instead of each
byte timing out. The device *logic* is done and host-tested
(`models/devices/i2c_devices.py`: AXP223 0x34, EEPROM24C 0x50, AIC3204 0x18, VC6
0x68/0x6A); this is the Renode transport glue — wrap them as `II2CPeripheral`
slaves on `i2c1`. Minimum to boot: each ACKs its address and returns plausible
bytes (AXP a 256-byte dump; EEPROM the 424 B NVPARAM block with the three 'd'
markers, or rely on force-reset 1; VC6 accepts the table write; codec accepts
writes). A faster-to-build alternative is a missing-slave NACKF+STOPF behaviour
(real-HW AUTOEND), which lets each wait fail immediately and the firmware fall
back to defaults. Then re-run and chase the next never-ready register from the
heatmap toward the main loop.

Tooling note: `observe.classify_tail` currently flags this as a flat poll-hang;
it should be refined to recognise slow-but-forward progress (HAL tick advancing
/ new I2C target addresses appearing) vs a truly dead spin.

## Update — I2C1 slave shims done; next blocker is PWR (2026-11-19)

`platforms/g7250_main_i2c1_mock.repl` adds minimal ACKing `Mocks.DummyI2CSlave`
slaves on `i2c1` at 0x34 (AXP223), 0x1A/0x0D (AXP dump companions), 0x50
(EEPROM), 0x18 (AIC3204), 0x68/0x6A (VersaClock 6); `m1_run.py` loads it as an
overlay after the Main platform. **Confirmed:** with the slaves present Renode's
STM32F7_I2C drives TXIS/TC/STOPF, every transfer completes at full speed, and
the I2C poll-hang is gone (i2c1 accesses drop from ~1.4M to a few hundred). Mock
bytes are sufficient because every device's init error path continues
(force-reset 1 on the EEPROM loader); swap one address for a functional slave
(models/devices/i2c_devices.py logic) only when a test needs real device data.

The boot now advances past the whole I2C1 bring-up and **poll-hangs on the next
never-ready register: `pwr +0x8` reading 0x0** (tight 1-instruction wait, PC
0x0802C2A0). This is the known `TODO(M1)` "model PWR SMPS/VOS0 ready" work: the
base H7 `pwr` Python stub returns a curated ready value for 0x0/0xC/0x18 but 0x0
for 0x8, and the H72x Main polls a ready bit there. Next step: give the Main a
PWR stub (or overlay) that returns the awaited ready bit at offset 0x8, then
re-run and chase the next register toward the main loop.

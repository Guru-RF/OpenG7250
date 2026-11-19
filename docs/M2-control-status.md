# M2 — stock Control boot: status

Milestone M2: boot the stock Control (touchscreen front panel, STM32H743-class)
under the same harness as the Main. Runner: `harness/g7250emu/control_run.py`
(sibling of `m1_run.py`, both on the shared `bootcore.py`). Image resolved via
the local image-map (`control`), hash-verified, never decrypted.

## Result — boots through full peripheral init to the LTDC VSYNC wait (2026-11-19)

Reset facts (control_unit/docs, VERIFIED): load `0x08020000`, MSP `0x24080000`,
reset `0x080235AC`; `nvic Frequency 240000000` (HCLK) for the HAL tick. I2C
slave shims (`platforms/g7250_control_i2c_mock.repl`): GT911 0x14/0x5D (I2C1),
AIC3204 0x18 + PCA9557 0x19 (I2C2).

Reconstructed Control console (USART1, `.private/control/control_console.txt`):
```
[DBG] Start TIM13 (SLIP Client)
[OK] System started.
[OK] aic3204 (0x30) ready.
[DBG] Start TIM5 (Audio Service)
[INF] SPI fatfs init
[ERR] Mount spi-flash failed, 3          <- W25Qxx on SPI1 not modelled (expected)
[DBG] Start TIM8 (hm133)
[DBG] Start TIM14 (InputDev Service)
[INF] GT911 reset done ... addr should be 0x14
[INF] GT911 detected at 0x14
[INF] Config checksum OK (calc=0x00)
[INF] GT911 init complete (EXTI rising-edge, addr=0x14)
[DBG] Start TIM3 (GT911 CTP Service)
[DBG] Start TIM2 (Encoder Service)
```
So the Control runs its whole bring-up — SLIP client, audio codec (AIC3204),
FatFS SPI-flash mount attempt, H-22 mic (TIM8), InputDev, **GT911 capacitive
touch fully initialised at 0x14**, GT911/encoder services — and then poll-hangs
on **`ltdc +0x48` (CDSR) reading 0x0**: the GUI framebuffer-swap waits for the
LTDC VSYNC status bit, which Renode's STM32LTDC does not toggle headless (no
display sink; the repainter does not run even with `FramesPerVirtualSecond`
set). This is the Control's analogue of the Main's PWR/FPGA never-ready poll.

## Done / deferred

- **Done:** `control_run.py` + `bootcore.py` (shared with M1) + the Control I2C
  mock overlay. Boots to the display VSYNC wait with full non-display init.
- **Next blocker (M2 exit):** make LTDC CDSR VSYNC toggle headless — either a
  Renode video sink that starts the repainter, or an LTDC CDSR shim. Then chase
  the next register toward the GUI service loop.
- **Deferred:** W25Qxx SPI1 flash slave (FatFS mount), functional GT911/codec
  data, the LTDC framebuffer content, SDRAM/DMA2D exercise — later milestones.

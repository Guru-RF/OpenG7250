# Control platform skeleton — status

> Sources cited as "g7250-base `<path>`" refer to the former data pin
> (historical name; see `docs/REPO_LAYOUT.md`, "Historical names").

The Control unit is the touchscreen front panel (STM32H743-class, Cortex-M7).
`platforms/g7250_control.repl` is its clean-room Renode platform, built the same
way as the Main platform: start from Renode's STM32H7 base, override only the
Control-specific facts traced to `g7250-base/control_unit/docs/*` (VERIFIED) or
to RM0433 (used as data). The image is loaded by the harness from the local
image-map, never from the repl.

Regression gate: `bash tests/baseline/m1_smoke.sh` (step `[3c]`, part of the
14-check gate, ALL PASS).

## Done and verified (image-independent)

| Area | Deliverable | Verified |
| --- | --- | --- |
| Part class | H743-class: initial MSP `0x24080000` = top of 512 KiB AXI SRAM. Base default already 512 KiB, so (unlike Main's 320 KiB H72x) **no AXI override needed** | loads on pinned Renode; AXI `0x24000000..0x2407FFFF` |
| SDRAM | `sdramBank1` narrowed from the base 256 MiB to the real **32 MiB** FMC window so out-of-range framebuffer access is caught | range `0xC0000000..0xC1FFFFFF` confirmed |
| SPI1 | W25Qxx SPI NOR flash controller @ `0x40013000` (base has only spi4) | registers on Renode |
| SPI2 | I²S2 audio controller @ `0x40003800` | registers on Renode |
| Inventory | LTDC, DMA2D, SDMMC, USB OTG-FS (`usb2`), I2C1/2/3, DMA1/2, RTC, IWDG, CRC all come from the H743 base — no H72x-only tags needed (contrast Main) | present in `peripherals` |

Reset facts (control_unit/docs/startup.md, VERIFIED): load base `0x08020000`,
image 781 328 B → `0x080DEC10`, VTOR `0x08020000`, reset handler `0x080235AC`
(Thumb `0x080235AD`), MSP `0x24080000`.

## Deliberately deferred (needs the image / a later milestone)

- **I²C / SPI device logic** — W25Qxx (SPI1), AIC3204 codec + PCA9557 expander
  (I2C2), GT911 touch (I2C1). Controllers are present; attaching slave logic is
  driven by the firmware's frames. The AIC3204 can reuse a Control-side peer of
  the stub in `models/devices/i2c_devices.py` (different init than the Main).
- **Front panel** — button matrix, 8 GPIO encoders, TIM2 main dial, H-22 mic
  keypad on TIM8/PI5. Needs the image's scan frames.
- **SLIP inter-MCU link** — USART2 ↔ Main USART2 (460 800 8N1). A later
  multi-machine milestone (two Renode machines on one SLIP channel).
- **Display bring-up** — LTDC panel power sequence (PE6/PI3/PF9) and TIM4
  backlight are GPIO/timer wiggles the base absorbs for the skeleton.

## When the decrypted Control image arrives

Same intake as Main (docs/M1-status.md): put it outside any git tree, set the
image-map + the `control` `image_sha256` in `images/manifest.yaml`, then run the
boot under observe (load at `0x08020000`, MSP `0x24080000`, reset `0x080235AC`),
iterate the polling loops from the heatmap/hang verdicts, and target a hang-free
run to the main loop.

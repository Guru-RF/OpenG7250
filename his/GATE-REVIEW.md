# HIS gate review 1 (his-draft0)

Review of the HIS as imported from `g7250-his` (tag `his-draft0`), against the
gate rule in the root README: only **hardware facts** pass to the product side,
never how the stock firmware does things.

Status: **not yet cleared.** The product side does not read `his/` until the
items below are resolved and the review is marked cleared.

Reviewer: OpenG7250 RE session. This is a first pass by the RE side; a second,
independent read is recommended before clearing.

## Classification used

- **Keep**: hardware fact (part, bus, address, pin, wiring, electrical value,
  datasheet behaviour, the FPGA's bus interface).
- **Remove**: stock firmware behaviour or configuration (boot order, timeouts,
  register values the stock code chose, log messages, data formats of stock
  software, stock defaults).
- **Decide**: borderline; needs a decision by the project.
- **Move**: emulator or RE notes; belong in `re/emu/docs/` or `re/analysis/docs/`.

## Findings per section

### README.md
- Outdated: names `G7250-P1`, `g7250-fw`, `g7250-base`/`g7250-emu` as repos,
  and a condition "no push until the project's IP review". **Rewrite** for the
  umbrella (`product/firmware`, `re/emu`, `re/analysis`); drop the IP-review
  condition (dropped project-wide).

### 10 Reset and clock
- Keep: two MCUs and their classes; bootloader region 0x08000000-0x0801FFFF and
  application load base 0x08020000 (platform constraint for any replacement
  image).
- Remove: initial MSP and reset-handler addresses of the stock images; HCLK
  values chosen by stock; the HAL tick/HAL_Delay paragraph (stock software).
- Decide: whether crystal/oscillator frequencies are known from hardware; if so,
  record those instead of stock PLL results.

### 20 Power
- Keep: PH9 power-hold output (high keeps power, low drops it); PH5 power-key
  input with pull-up; AXP223 at I2C1 0x34; the rail voltages (DCDC1 3.3 V,
  DCDC2 1.2 V, DCDC3 1.8 V, DCDC5 2.5 V, ALDO1 3.3 V, DLDO1 1.8 V) as hardware
  requirements.
- Remove: ">100 samples requests shutdown" (stock debounce); "the boot polls a
  PWR ready flag"; "errors are logged and boot continues".

### 30 I2C devices
- Keep: bus and 7-bit addresses per device (AXP223 0x34, 24Cxx 0x50 with 16-bit
  addressing, AIC3204 0x18, VersaClock 6 at 0x68 or 0x6A, GT911 0x14/0x5D with
  the INT-at-reset address select, PCA9557 0x19); PCA9557 bit wiring (bit4 BT
  power, bit5 shutdown pulse, bit6 TX, bit7 RX); bus speeds as hardware limits.
- Remove: TIMINGR value; bring-up order; "settings loader runs with
  force-reset"; HAL I2C polling paragraph; PCA9557 boot value 0x8B.
- Decide: EEPROM layout (settings block, 'd' markers, calibration at 0x0800,
  NVPARAM at 0x1800). This is a stock data format. Keep only if the new firmware
  must read existing factory calibration; then limit it to the calibration area
  and describe it as data on the device.
- Decide: the VersaClock 6 0x70-byte init table is stock configuration. The
  required output frequencies (a hardware need) can be recorded instead.

### 40 Ethernet
- Keep: CH394 (W5500-register-compatible) on SPI6 of the Main.
- Remove: default IP, gateway, mask and ports; network modes (HDSDR, wfview);
  "programmed unconditionally". These are stock behaviour; the product spec
  defines its own network behaviour.

### 50 Audio
- Keep: AIC3204 on Main I2C1 0x18 and on Control I2C2 0x18 (reset PH2); MCLK
  12.288 MHz; Control codec as I2S master is a wiring fact if the clock lines are
  wired that way; Main-Control audio crosses the CTRL cable as analog.
- Remove: PLL settings and the PLL burst-write quirk (stock configuration).
- Decide: 32-bit 48 kHz I2S format (stock choice unless the wiring forces it).

### 60 Display and input
- Keep: 1024x600 parallel RGB TFT on LTDC; SDRAM on FMC bank 1 at 0xC0000000,
  32 MiB; GT911 INT PE2, RST PG14; 5x5 key matrix plus direct key; 8 quadrature
  encoders plus the main dial on TIM2; H-22 mic keypad on PI5.
- Remove: RGB565 and double buffering on VSYNC as requirements (stock choices);
  DMA2D waterfall use; TIM14 1 kHz scan; TIM8 decoding method.
- Decide: the H-22 "ratio-coded serial" signal format is a property of the
  microphone (hardware), so it may stay, described as the signal, not as the
  stock decoder.

### 70 Inter-link
- Keep: Main USART2 wired to Control USART2 over the CTRL cable.
- Decide: SLIP framing, 460800 8N1, message types 0x01-0x03 and the 20 ms client
  tick are the stock protocol between the two MCUs. Needed only if new firmware
  on one MCU must talk to stock firmware on the other (interoperability). If the
  first product is a headless Main without a stock Control, remove it from the
  HIS and keep it on the RE side.

### 80 RF / FPGA
- Keep: the FPGA bus on GPIOE (D0-D7 on PE0-PE7, CMD PE8 with PE9, STB PE9,
  DRDY PE10 rising edge); command codes 0x00-0x04 and 0x08 with their frame
  layouts; NCO as 32-bit phase word on a 122.88 MHz clock; rate index 0-3 to
  384/192/96/48 kS/s; samples per DRDY. This is the interface of the FPGA, which
  the new firmware must drive.
- Remove: "errors are log-only in stock"; EXTI15_10 as interrupt choice is a
  stock detail but follows from the pin, so it may stay as "PE10 can raise
  EXTI10".
- Move: the sections "Emulator status", "Original note", "M3 attempt finding"
  and "M3 approach pinned" to `re/emu/docs/`. They describe the emulator, not
  the hardware.

### Evidence lines
- Sources such as "g7250-base reset disassembly" and "OpenG7250 RE" may stay as
  provenance, but each kept fact should cite an observation or datasheet, not
  disassembly, wherever possible.

## Next steps

1. Apply the Remove and Move items, and rewrite the README (RE side).
2. Decide the Decide items (ON8ST).
3. Second, independent read; then mark this review **cleared** and update the
   root README status for `his/`.

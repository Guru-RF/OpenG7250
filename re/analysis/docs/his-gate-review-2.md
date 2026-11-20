# HIS gate review 2 (independent second read)

**Scope.** `his/*.md` at `da50bd6` (branch `gate/review-2`, a copy of
`his/integrate`). Reviewer: an RE-side session started by the OpenG7250 RE
session on ON8ST's request. Sections 1–3 were written **before** reading
[review 1](his-gate-review-1.md); section 4 compares the two afterwards.

**Sources checked.** g7250-base `main_unit/docs/{peripherals,memory_map,flow,startup}.md`,
`control_unit/docs/peripherals.md` (read only); emulator docs in
`openg7250-emu/re/emu/docs/` (M1-status, M2-control-status, M8c-R0-report,
test spec v0.5 §F1, §O2); `re/analysis/docs/` in this tree
(headless-startup-analysis, memory-map). Decisions 0023 and 0025 are not on
disk in `decisions/` of either tree (the index is empty); their content is
taken from the review brief: 0023 — only the Main is replaced, CTRL stays
idle, the stock Control stays in the radio; 0025 — stock and new firmware are
installed the same way from the Main, without the Control.

**Gate rule applied.** Pass: parts, buses, addresses, pins, wiring,
electrical values, datasheet behaviour, the FPGA's bus interface, safety
constraints. Block: how stock does things (sequence, timing, chosen register
values, stock data formats/locations, defaults, protocols the product does not
need).

Labels used below: **LEAK** (stock behaviour or configuration in the text),
**TAG** (confidence tag missing or stronger than the source), **SRC**
(statement not supported by the cited source), **CIRC** (emulator evidence
that only shows the model matches the stock code, not the hardware),
**GAP** (a hardware fact the product side needs, missing), **SAFETY** (a gap
that can damage hardware, transmit unintentionally or break recovery).
**R** = required change, **A** = advisory.

---

## 1. Per-section findings (independent)

### README.md and 00-overview.md

- 00 Conventions lists the tags as "VERIFIED/HIGH/HYPOTHESIS"; the sections
  also use MEDIUM (30). **A:** list MEDIUM too.
- 00 says "Never stock firmware code or behaviour", but `15-stock-recovery.md`
  necessarily states where stock keeps data. **A:** name the exception once:
  safety constraints that protect the factory firmware are allowed and are
  phrased as "MUST NOT touch X", without the stock layout.
- No section states which unit the first product drives. Under 0023 the
  product only drives the Main; the Control content (in 30, 50, 60) is never
  driven by it. **A:** mark Control material "informative — not driven by the
  first product (0023)"; better, move it to an appendix or drop it, because
  every Control item is stock-derived and gives the product nothing.
- README status line is correct ("not yet cleared").

### 10-reset-clock.md

- Image placement 0x08020000, bootloader 0x08000000–0x0801FFFF: platform
  constraint, traceable (g7250-base memory_map: bytes for the bootloader
  region absent from the image; emu M1 loads at 0x08020000). OK. No tag given;
  **A:** tag HIGH (image analysis + emulator run).
- "MCU class STM32H72x" for the Main: source says "likely H725/H735" and
  "on a 1 MiB part" for flash. **TAG/A:** give the class as HIGH and the flash
  size (1 MiB, 128 KiB sectors) as MEDIUM, because the product's flash layout
  (rule 5 of HIS 15) depends on it.
- **GAP:** the section is called "Reset and clock" but has no clock fact.
  The product needs the HSE frequency. The source has one only as "the
  25 MHz HSE the firmware is built for" (g7250-base peripherals, SPI6 table),
  i.e. derived from stock clock settings. *Written before reading review 1 as
  a required change; withdrawn after the comparison, because decision D1 says
  not to derive HSE/LSE from stock PLL settings (see §4).* What remains:
  **A:** add an explicit "Open: HSE and LSE frequencies not yet established
  (D1); read from the crystal marking" so the product side knows the gap
  exists, and add that the 550 MHz CPU-frequency-boost setting is an option
  byte set outside the application (flow.md, VERIFIED absence of option-byte
  code in the application), so the product must not rely on changing it
  (ties to HIS 15 rule 2).

### 15-stock-recovery.md

Fit for purpose as a safety section; the rules themselves are right and match
ON8ST's constraint. Problems are in the justifications and in one leak.

- Rule 3, "It holds the factory calibration (at 0x0800)": the offset is the
  stock data layout (g7250-base memory_map EEPROM table). The product treats
  the whole EEPROM as read-only and must not use stock data formats, so it
  has no use for the offset. **LEAK (R):** drop "(at 0x0800)" here and in 30.
  Keep "holds factory calibration and other factory-firmware data".
- Rule 4, "the factory firmware keeps state there": **SRC (R).** The Main
  application never writes the backup SRAM and never enables its clock
  (memory_map, "Read-only in V1.0.1", VERIFIED/HIGH); it only reads a settings
  mirror and then boots on defaults. Whether the bootloader uses the backup
  domain is unknown. The rule stays (ON8ST constraint), but the reason must
  become: "contents are read by the factory firmware at boot, and the
  bootloader's use of the backup domain is unknown (HYPOTHESIS)". Also extend
  it to the RTC backup registers, for the same unknown-bootloader reason.
- Evidence line, "option bytes ... set in production or by the bootloader
  (VERIFIED)": what is VERIFIED in the source is the *absence* of option-byte
  code in the application; who sets them is an inference. **TAG (R):**
  "the application contains no option-byte code (VERIFIED); they are set in
  production or by the bootloader (inference)".
- "updates are done by the bootloader in sector 0 after a reset (HIGH)":
  matches source for the Main (HIGH); for the Control the source says
  VERIFIED absence of update code, mechanism HYPOTHESIS. OK.
- "The update transport of the Main is not yet known (HYPOTHESIS: a serial
  bootloader)": the sources name **two** candidates — the Main console USART1,
  or the Control's MSC disk via the Control bootloader over USART2 (g7250-base
  peripherals "Update transport", HYPOTHESIS; emu spec O2). **SAFETY (R) with
  0025:** 0025 assumes installation from the Main without the Control. If the
  real path is the second one, 0025 cannot hold and the CTRL USART2 link plus
  the stock Control are part of the recovery path. HIS 15 must list both
  candidates and say that until F1 settles it, new firmware must leave both
  the CTRL cable path and the Control untouched (already true under 0023), and
  that 0025 rests on an unproven transport.
- **SAFETY (R):** add "The bootloader's entry condition (what makes it enter
  update mode instead of starting the application) is unknown." A rollback
  that needs the application's cooperation (a flag, a jump) would fail once
  the stock application is gone. The stock application's jump to the
  bootloader is dead code (peripherals "Bootloader jump", HIGH), which points
  to entry from reset without application help — say that as HIGH, but keep
  F1 as the gate.
- Rule 5 ("own persistent data only in own application flash from
  0x08020000") **A:** add: persistent data must not use flash sector 6
  (0x080C0000 on a 1 MiB part) only if F1 shows the bootloader uses it as a
  staging area — currently a HYPOTHESIS from orphan strings; record as an
  open check, not a rule.
- Last paragraph ("only the Main is reflashed; the Control keeps its factory
  firmware") matches 0023. OK.

### 20-power.md

- PH9 "high keeps the unit powered, low drops power": **TAG/SRC (R).** The
  source is HYPOTHESIS ("power enable? HYPOTHESIS", g7250-base GPIO map;
  M8c PowerModel is a model, not a measurement). The emulator cannot show
  power dropping; it only shows stock driving PH9 high. Tag HYPOTHESIS.
- PH5 "power-key input, read with a pull-up. With no panel connected it reads
  high": the reading with no panel is a consequence of the *internal* pull-up
  stock enables (the text says so). OK as written, but **TAG (A):** HIGH for
  "input", HYPOTHESIS for "power key" wiring. M8c and headless-startup
  analysis show PH5 is also the signal whose low level shuts the stock Main
  down — that is stock behaviour and correctly absent.
- Evidence line: "the stock Main drives PH9 high and stays up with PH5 high
  (M8c PW-1 confirmation)" — **LEAK (R, minor):** "stays up with PH5 high"
  tells the product how stock's power-key logic behaves. Replace with "the
  emulator run confirms PH9 is an output and PH5 an input with pull-up".
  Same for "the stock boot addresses I²C1 0x34 (M1)" → "a device at 0x34 is
  addressed on I²C1 (M1)".
- AXP223 at 0x34: VERIFIED in source (strings + driver). OK.
- Rail list "Rails the hardware needs: DCDC1 3.3 V ...": these are the
  register values stock writes (M1 even lists the write sequence). The
  voltages are legitimate electrical requirements, but "the hardware needs"
  overstates: the consumers are MEDIUM (DCDC1 = MCU 3.3 V) and HYPOTHESIS (all
  others). **TAG (R):** "Rail voltages (values as programmed by stock, decoded
  with the AXP22x datasheet; HIGH); consumers: DCDC1 likely the MCU supply
  (MEDIUM), others unknown (HYPOTHESIS)."
- **SAFETY (R):** add "Rails not in this list (DCDC4, DC5LDO, ALDO2/3,
  ELDO1–3, DLDO2–4, DC1SW) are off; their consumers, if any, are unknown —
  do not enable them" and "never set a listed rail above the stated value;
  never switch DCDC1 off while running (likely the MCU supply)". These are
  hardware-protection constraints, not stock behaviour. The stock power-on
  sequence (safe state first, 10 ms wait, single enable write) must **not** be
  copied in; it is correctly absent.
- **GAP (A):** the AXP223 power-on default state (which rails are on before
  any I²C write) comes from the AXP223 datasheet / its OTP and should be
  stated or marked unknown, because the MCU must already be running before it
  can program the rest.
- **GAP/SAFETY (R) with 0023/0025:** how the Main powers up without the
  Control is not stated. M8c lists two hardware hypotheses (H1/H2) and
  headless-startup-analysis says it is not established. Add an "Open:
  power-up path without the Control (key switch in hardware vs. bootloader
  waits for PH5) — HYPOTHESIS, to be measured (T0-P2)". 0025 depends on it.

### 30-i2c-devices.md

- Main I²C1 map (0x34, 0x50, 0x18, 0x68/0x6A): VERIFIED in source. OK.
- "Bus speeds are the rates the stock code uses": the sentence is honest,
  but a bus rate is stock configuration; what the product needs is the device
  limit. **A:** keep "~400 kHz" only as "known to work", and state the
  device maximum per datasheet (24Cxx/AIC3204/5P49V6965 support 400 kHz;
  AXP223 per its datasheet).
- 0x50 EEPROM "16-bit addressing": hardware property (array size), HIGH from
  the transfer helper's address size. OK. "factory calibration is stored at
  0x0800": **LEAK (R)** as under 15.
- 0x68 **or** 0x6A: correct (the source probes both; which the board strap
  selects is unknown). **A:** say "strap unknown".
- VersaClock 6 table: presents derived hardware properties (OUT1 enabled,
  LVDS 3.3 V; OUT2–4 off), not the register table. HIGH/MEDIUM tags match
  source. The frequency is tagged HYPOTHESIS where the source says MEDIUM —
  conservative, acceptable. The FOD/feedback divider values are correctly
  absent. OK.
  - **A:** "OUT2–OUT4 off" is a stock choice; the hardware fact is
    "nothing known to be connected to OUT2–OUT4". Reword.
  - **SAFETY (A):** OUT1 is LVDS into (probably) the FPGA; programming it as
    CMOS or at another frequency is a risk for the receiver. Say "OUT1 must be
    LVDS 3.3 V".
- Control: GT911 0x14/0x5D with the INT strap rule — datasheet fact; OK.
  "I²C2 (~100 kHz)" — stock rate, see above.
- PCA9557 "bit4 BT power, bit5 shutdown pulse, bit6 TX, bit7 RX": roles
  inferred from stock use; tags missing (source: VERIFIED for bits written,
  roles HIGH/MEDIUM). "shutdown pulse" describes stock behaviour (a pulse).
  **LEAK (A)** + **TAG (A)**. Under 0023 the product never drives the Control,
  so this whole block is informative only.

### 40-ethernet.md

- CH394 on SPI6, CS PG15: VERIFIED. OK.
- Evidence line: "the stock Main programs the chip's source-IP register" —
  **LEAK (R, minor)** and **CIRC**: the emulator's W5500-compatible model was
  chosen from the disassembly, so this shows the model fits the stock code,
  not that the chip is a W5500-compatible part. Replace with "the emulator's
  W5500-register-compatible model on SPI6, CS PG15, is accepted by the image"
  and cite the CH394 datasheet (CH394DS1) for register compatibility.
- **GAP (R):** this is the product's only host interface (headless Main),
  and the section omits the facts needed to bring the chip up:
  - SPI6 pins PG12 MISO / PG13 SCK / PG14 MOSI (AF5) — VERIFIED;
  - SPI mode 0, 8-bit, MSB first — VERIFIED (and CH394 datasheet);
    max SCK per CH394 datasheet (≈17 MHz known to work — stock setting, A);
  - RST# on **PB5** (active low) — VERIFIED;
  - INT# on **PC13** (active low, needs pull-up) — VERIFIED;
  - "LAN connector is on the Main Unit" (manual) and "exclusive bus" — HIGH.
  The reset pulse length and the 100 ms wait the stock uses must not be
  copied (stock timing); the product takes reset timing from the CH394
  datasheet.

### 50-audio.md

- Main codec at I²C1 0x18: OK.
- "MCLK 12.288 MHz, 48 kHz": 12.288 MHz is an external board clock on PC9
  (I2S_CKIN), value from the constant stock records (HIGH, not measured).
  "48 kHz" is the sample rate stock configures — **LEAK (R)**: replace with
  "12.288 MHz (= 256 × 48 kHz) external clock on PC9/I2S_CKIN, also the codec
  MCLK; source of the clock likely the FPGA (HYPOTHESIS)".
- **GAP (A):** Main I²S3 pins PA15 WS / PC10 CK / PC11 SDI / PC12 SDO (AF6)
  and codec reset **PB10** — VERIFIED. Whether the product needs the Main
  codec at all under 0023 (audio over the network) is a product decision; the
  pins are still hardware facts it may need, and PB10 is needed to hold the
  codec in reset safely.
- "Control AIC3204 ... is the **I²S master** at 48 kHz": the master/slave
  role and the rate are stock **register values** (control peripherals:
  "I²S master (VERIFIED register values)"), i.e. configuration, not hardware.
  Under 0023 irrelevant to the product. **LEAK (R):** remove, or reduce to
  "Control codec: AIC3204 at I²C2 0x18, reset PH2 (informative)".
- "Main↔Control audio crosses the CTRL cable as analog": source? The
  control docs say the Control routes speaker/mic and that 460 800 Bd SLIP
  cannot carry 48 kHz audio and has no audio message type (control
  peripherals) — an inference. **TAG (R):** HIGH (inference from the link
  capacity and the absent message type), not measured.

### 60-display-input.md

Entirely Control-side; under 0023 not driven by the product.

- 1024×600 RGB, SDRAM FMC bank 1 0xC0000000 32 MiB, GT911 INT PE2 / RST PG14:
  traceable (control peripherals, memory_map). Tags missing (VERIFIED/HIGH in
  source). **TAG (A).**
- Evidence "GT911 detected at 0x14": **CIRC (R, minor).** The emulator mock
  answers at 0x14 by construction; the source says which address the fitted
  panel answers "cannot be told from code". Remove the "detected at 0x14"
  claim or say "the mock answers 0x14".
- "the stock Control reaches its GUI loop" — stock behaviour in an evidence
  line; harmless but **A:** drop.
- Key matrix "5×5 plus a direct key": MEDIUM in one source paragraph,
  stated without tag. **TAG (A).** Encoders: HIGH. H-22 on PI5 "ratio-coded":
  the coding is derived from the stock decoder (TIM8 capture), but it is a
  property of the microphone's signal; acceptable with a HIGH tag.

### 70-interlink.md

- "Main USART2 is wired to Control USART2 over the CTRL cable": VERIFIED in
  both unit docs (pins PD5/PD6 AF7 on both). OK. No tag given; **A:** VERIFIED
  for the pins, HIGH for the wiring (not traced).
- Evidence "carry traffic" (D1): CIRC — the two-machine run connects the
  ports by construction. Harmless; **A:** say "the emulator connects them".
- **GAP (R):** pins PD5 (TX) / PD6 (RX) are missing. Under 0023 the product
  keeps CTRL idle; to keep it idle it must know which pins those are, and
  must leave PD5 at the UART idle level (high) or high-impedance, never
  driven low (a sustained low is a UART break to the stock Control).
- Correctly absent: baud rate 460 800, SLIP framing, message types (stock
  protocol the product does not need under 0023).

### 80-rf-fpga.md

- Signals PE0–PE7, PE8, PE9, PE10: VERIFIED in source. OK.
- Commands 0x00–0x04, 0x08: FPGA bus interface; allowed. The 0x01 frame
  field list ("status flags ... per-rate calibration, rate index") gives no
  byte offsets, which the product would need; that is a completeness gap,
  not a leak. "per-rate calibration" values live in the stock EEPROM
  calibration block (stock data format) — **GAP (A):** state that the
  meaning and safe values of the calibration bytes are unknown.
- **GAP/SAFETY (R):** codes 0x05/0x06 and 0x09/0x0A exist (two pulse
  commands, roles unknown, HIGH). Omitting them hides that the FPGA has
  commands whose effect is unknown; the product must not send them. Add them
  as "exist; role unknown; do not send".
- Evidence: "reads version 1.0.0": **CIRC (R).** The emulator's FPGA model
  returns what the model author chose; the real FPGA version is unknown (the
  1.0.0 the stock reports to the Control is a compiled-in string). Remove the
  version value. More generally, "zero bus errors" with a model built from
  the same disassembly is consistency, not hardware evidence; say so.
- Strobe polarity, setup/hold timing, and who drives D0–D7 when: missing.
  **GAP (A)**, unknown until measured; bus contention is a hardware risk.
  Add "Open: strobe polarity and timing, bus turnaround — not measured".
- NCO: "32-bit phase words for a 122.88 MHz clock (f × 2³² / 122.88 MHz)":
  VERIFIED for the formula in the code; the clock value is MEDIUM (half of
  OUT1 if OUT1 = 245.76 MHz). **TAG (R):** MEDIUM for 122.88 MHz.
  "frequency folded into 0–61.44 MHz with a spectral-inversion flag" is the
  host-side algorithm stock uses; the hardware fact is that the FPGA takes a
  phase word in 0–2³¹ (first Nyquist zone) plus an inversion flag in the
  frame. **A:** reword as an interface requirement.
- Sample rate: "rate index 0–3 → 384/192/96/48 kS/s; DRDY at ~48 kHz" —
  source is MEDIUM; HIS gives no tag. **TAG (R):** MEDIUM.
- DRDY "rising edge signals sample data ready": source GPIO map MEDIUM ("FPGA
  event line"), FPGA section VERIFIED (EXTI rising edge). OK as HIGH.

---

## 2. Missing content the product side needs for safety (0023/0025)

The first product *is* the Main firmware, and the Main is the RF controller:
the stock Main, not the Control, drives T/R switching, the PA bias DAC and the
filter relays (g7250-base main peripherals, SPI1/SPI2/GPIO/ADC sections). The
HIS covers none of it. A product that leaves these pins at reset defaults, or
drives them by accident, can key the PA or bias it without drive, with no SWR
or temperature protection. Even an RX-only build (emu spec H-G2) must hold
them in a known safe state. These are hardware facts (pins, parts, wiring,
safe levels), not stock behaviour. **All R.**

1. **T/R lines** (VERIFIED levels): RX = PF4 high, PF6/PC7/PH11 low; TX the
   reverse. Function per line HYPOTHESIS. Safe state = RX levels.
2. **SPI1 shift-register chains** (HIGH): chain A (PA11 latch, PA10 output
   enable) — bits 0–6 TX low-pass bank, **bit 7 T/R relay or PA enable**;
   chain B (PH12 latch, PH10 output enable) — RX band-pass, preamp,
   attenuator. Output-enable lines must be held inactive until a known-safe
   frame (bit 7 clear) has been latched. Chip type (74HC595 kind) HYPOTHESIS;
   OE polarity to be stated or marked unknown.
3. **ATU latches** on SPI1: CS/latch PD13, PG2, PG5 (HIGH). Leave unwritten
   or document a safe value as unknown.
4. **SPI2 PA DAC** (VERIFIED): BU2506FV-type 8-channel 10-bit DAC, SCK PB13,
   MOSI PB15, LD PB12, RESET PB14 (active low, forces all outputs to VrefL).
   Channel map: 1 drive, 2 driver bias, 3 fan, 6 power reference, 7/8 final
   bias. **Safe state: bias channels 2/7/8 at 0 whenever not transmitting**;
   holding PB14 low is the hardware way to force all outputs low. The stock
   bias-trim targets, power curves and fan law are stock behaviour and must
   stay out.
5. **DAC1 OUT1 (PA4)** RF-gain control voltage (VERIFIED pin; scaling is
   stock); PA5 unused.
6. **PTT/key inputs:** PH6 PTT in, PH3/PH4 key/paddle (HIGH). The product must
   know these exist so that it does not transmit on a stray input in an
   RX-only build.
7. **ADC1 metering pins** (VERIFIED): PF11 forward, PA6 reflected, PC4 Idd,
   PB1 PA temperature (NTC), PA1_C Vext, PC5/PA2 ALC. The pin→quantity map is
   a hardware fact; the conversion constants and SWR algorithm are stock and
   stay out. Needed for any protection before TX is ever enabled.
8. **PD12** (TIM4 PWM, role unknown, low in stock): state as "unknown output,
   keep low".
9. **CH394 RST#/INT#** (see 40) and **codec reset PB10** (see 50): parts held
   in reset is the safe state.
10. **USART2 idle** (see 70) and the **power-up path** (see 20) for 0023/0025.
11. **Recovery** (see 15): both update-transport candidates, the unknown
    bootloader entry condition, backup-domain justification.

Suggested placement: a new `his/85-rf-control.md` (T/R lines, SPI1 chains,
ATU latches, SPI2 DAC, DAC1, PTT/key inputs, ADC1 pins) with a "Safe state at
reset" table, and a pointer to it from 15.

---

## 3. Indirect leaks — summary

| Where | Text | Why |
| --- | --- | --- |
| 15 rule 3, 30 | "calibration at 0x0800" | stock EEPROM layout |
| 20 evidence | "stays up with PH5 high" | stock power-key logic |
| 40 evidence | "programs the chip's source-IP register" | stock behaviour; CIRC |
| 50 | "48 kHz" (Main), "I²S master at 48 kHz" (Control) | stock codec configuration |
| 30 | PCA9557 "shutdown pulse" | stock use pattern |
| 80 evidence | "reads version 1.0.0" | model value, not hardware; looks like a fact |
| 60 evidence | "GT911 detected at 0x14", "reaches its GUI loop" | CIRC; stock behaviour |
| 80 | "frequency folded into 0–61.44 MHz" | host algorithm phrasing (advisory) |

Nothing in his/ contains code, decompiler output, function addresses,
RAM addresses, register-init tables, timeouts or log strings. That part of
review 1's clean-up holds.

---
## 4. Comparison with review 1

Review 1 was read only after sections 1–3 were written.

**Agreement.**
- The classification of what review 1 removed (stock MSP/reset addresses,
  HCLK, timeouts, TIMINGR, init tables, network defaults, SLIP protocol, log
  behaviour) holds: none of it is left in `his/`.
- Keep-list for 10, 20 (pins, PMIC address, rail voltages), 30 (address map,
  VersaClock as output properties instead of the table, D3), 40 (CH394 on
  SPI6), 60, 70 (wiring only, D6) and 80 (bus interface).
- 15-stock-recovery: the four rules are right.

**Differences.**

| # | Topic | Review 1 | Review 2 |
| --- | --- | --- | --- |
| C1 | Scope | Judged the text present (keep/remove). | Also judged completeness against 0023/0025. Finds the whole Main RF-control block missing: T/R lines, SPI1 filter/T-R chains with output-enable, ATU latches, SPI2 PA bias DAC, DAC1 RF gain, PTT/key inputs, ADC1 protection inputs (§2). The first product *is* the RF controller; this is the largest finding of this review. |
| C2 | Emulator evidence | Accepted as confirmation of address, pin or bus. | Several emulator lines are circular: the models were built from the same disassembly (FPGA model "version 1.0.0", "zero bus errors"; GT911 mock "detected at 0x14"; W5500 model accepted; USART2 ports connected by construction). They confirm consistency with the stock code, not hardware. Must be worded as such. |
| C3 | PH9 | Keep "high keeps power, low drops it" as fact. | Source is HYPOTHESIS (g7250-base GPIO map; M8c is a model). Keep the statement, tag it HYPOTHESIS. |
| C4 | D1 (HSE) | Do not derive from stock. | Agreed after reading; my first draft asked for HSE 25 MHz and is withdrawn. Asks only for an explicit "open" note. |
| C5 | D2 (EEPROM 0x0800) | Keep the offset *if* the first product must reuse factory calibration. | The condition is not recorded anywhere, and the content format stays on the RE side, so the product cannot use the offset. Either record that condition as met (and why the product needs the location without the format), or drop the offset. |
| C6 | D4 (I²S format) | Drop 32-bit/48 kHz as a requirement; keep "the Control codec is the I²S master" as a wiring fact if the clock lines are wired that way. | D4 is applied incompletely: "48 kHz" remains for both codecs in 50. "Control codec is master" is a stock register setting, not shown to be forced by wiring, and irrelevant under 0023. Remove both. |
| C7 | D6 / USART2 pins | Pins not added, because "the headless Main does not use the link" and the product was "a headless Main without a stock Control". | 0023 changed the premise: the stock Control stays in the radio and CTRL stays idle. To keep it idle safely, the product needs PD5/PD6 and the rule "PD5 at idle level, never held low". Add them. Also `re/analysis/docs/main-control-interlink.md` line 5 still says "without a stock Control" (RE side, advisory). |
| C8 | Recovery path | "The path does not depend on the application"; transport HYPOTHESIS: serial bootloader. | The sources give two transport candidates, one of them through the Control and USART2, which would contradict 0025. Also the bootloader entry condition is unknown. 15 must say both. |
| C9 | Backup SRAM | "Not used", justified as "the factory firmware keeps state there". | The rule stays; the reason is wrong for the Main application (it never writes the backup SRAM). Reason must be "read by stock at boot; bootloader use unknown". |
| C10 | Rails | Keep the voltages as hardware requirements. | Keep, but tag them (values HIGH, consumers MEDIUM/HYPOTHESIS) and add the hardware-protection rules (do not enable other rails, do not exceed, do not drop DCDC1). |
| C11 | Tags | Not reviewed. | Missing or too strong in 10, 20, 50, 60, 80 (NCO clock, sample rates MEDIUM). |

---

## 5. Verdict

**NOT CLEARED.**

The text in `his/` is clean of code, addresses of stock code, tables, timings
and protocols, and review 1's removals hold. It does not clear because (a) the
HIS is missing the hardware facts the product needs to keep the Main's RF
section safe, (b) the recovery section rests on an unproven transport that may
contradict 0025, and (c) a handful of leaks, wrong justifications and tags
remain.

### Required changes (to be applied by the emu session)

| # | File | Change |
| --- | --- | --- |
| R1 | new `his/85-rf-control.md` | Add the Main RF-control hardware with a "safe state at reset" table: T/R lines PF4/PF6/PC7/PH11 with RX levels (VERIFIED levels, role HYPOTHESIS); SPI1 chain A (PA11 latch, PA10 OE; bits 0–6 TX LPF, bit 7 T/R or PA enable) and chain B (PH12 latch, PH10 OE; RX BPF, preamp, attenuator) (HIGH), OE polarity stated or "unknown"; ATU latches PD13/PG2/PG5 (HIGH); SPI2 DAC BU2506FV-type on PB13/PB15, LD PB12, RESET PB14 (active low → all outputs at VrefL), channel map 1 drive / 2 driver bias / 3 fan / 6 power ref / 7, 8 final bias, safe state bias = 0 (VERIFIED); DAC1 OUT1 PA4 RF-gain voltage; PTT PH6, key PH3/PH4 (HIGH); ADC1 inputs PF11 fwd, PA6 refl, PC4 Idd, PB1 PA NTC, PA1_C Vext, PC5/PA2 ALC (VERIFIED pins); PD12 unknown, keep low. No stock bias-trim targets, power curves, fan law, SWR algorithm or conversion constants. |
| R2 | 15 | Pointer to 85 for the safe state. |
| R3 | 15 | List both update-transport candidates (Main console USART1; Control MSC disk → Control bootloader → USART2) as HYPOTHESIS; state that 0025 rests on the first one until F1 proves it. |
| R4 | 15 | Add: the bootloader's entry condition is unknown; the stock application's bootloader jump is dead code (HIGH), so entry is expected from reset without application help; F1 remains the gate. |
| R5 | 15 | Rule 4: replace "the factory firmware keeps state there" with "stock reads it at boot; the bootloader's use of the backup domain is unknown (HYPOTHESIS)"; extend the rule to the RTC backup registers. |
| R6 | 15 | Evidence: "no option-byte code in the application (VERIFIED); set in production or by the bootloader (inference)". |
| R7 | 15, 30 | Resolve D2's condition: drop "(at 0x0800)", or record why the product needs the location. |
| R8 | 20 | Tag PH9 power hold HYPOTHESIS. Reword the evidence line without "stays up with PH5 high" and "the stock boot addresses". |
| R9 | 20 | Tag the rails (values HIGH; DCDC1 consumer MEDIUM; others HYPOTHESIS); add: rails not listed are off with unknown consumers, do not enable; do not exceed the listed values; do not switch DCDC1 off while running. |
| R10 | 20 | Add "Open: power-up path without the Control (H1/H2), to be measured (T0-P2)". |
| R11 | 40 | Add SPI6 pins PG12/PG13/PG14 (AF5), SPI mode 0 MSB first, RST# PB5 (active low), INT# PC13 (active low). Reword the evidence line (no "programs the source-IP register"; the model's acceptance is consistency, not hardware evidence; cite the CH394 datasheet for register compatibility). |
| R12 | 50 | Remove "48 kHz" (Main) and "I²S master at 48 kHz" (Control) per D4; give MCLK as a 12.288 MHz external clock on PC9/I2S_CKIN (HIGH, not measured). Tag "audio crosses the CTRL cable as analog" HIGH (inference). |
| R13 | 70 | Add PD5 TX / PD6 RX (AF7) on both MCUs; add: under 0023 the Main holds PD5 at the idle (high) level or high-impedance, never low. |
| R14 | 80 | Remove "reads version 1.0.0" and word the D2 emulator evidence as consistency with a model built from the disassembly. Add codes 0x05/0x06 and 0x09/0x0A as "exist, role unknown, do not send". Tag the 122.88 MHz NCO clock and the sample rates MEDIUM. Add "Open: strobe polarity/timing and bus turnaround not measured". |
| R15 | 60 | Remove "GT911 detected at 0x14" from the evidence (the mock answers 0x14 by construction). |

### Advisory (not blocking)

A1 list MEDIUM in 00 conventions; A2 name the safety-constraint exception in 00; A3 mark the Control material (30 Control part, 50 Control, 60) informative under 0023, or move it out; A4 open note for HSE/LSE and the boost option byte in 10; flash size MEDIUM; A5 VersaClock: "OUT1 must be LVDS 3.3 V", "nothing known on OUT2–4", "strap unknown" for 0x68/0x6A; A6 bus speeds as device limits per datasheet; A7 PCA9557 tags and "shutdown pulse" wording; A8 NCO folding reworded as an interface requirement; A9 0x01 frame offsets and calibration-byte meaning as open; A10 AXP223 power-on default per datasheet; A11 update `main-control-interlink.md` for 0023.

After R1–R15 are applied, a short re-check of the diff (not a full third
read) is enough to clear.

---

## Changes for review 2

Applied by the openg7250-emu session on `his/integrate`. The review was read
against `da50bd6`; commit `5f7679c` (HIS-17/18/19 additions) came in between and
is covered by the same changes. Review brought in as `81a8623` (cherry-pick of
`c22cbba`).

| # | Commit | Where | Change |
| --- | --- | --- | --- |
| R1 | c3c40a3 | new `his/85-rf-control.md` | Main RF control with a safe-state table: T/R lines PF4/PF6/PC7/PH11 (RX levels VERIFIED, roles HYPOTHESIS); SPI1 chain A (PA11 latch, PA10 OE, bit 7 T/R or PA enable) and chain B (PH12, PH10), OE active low (from the power-off path); ATU latches PD13/PG2/PG5; SPI2 BU2506FV-type DAC on PB13/PB15, LD PB12, RESET PB14, channel map, bias 2/7/8 at 0; DAC1 PA4; PTT PH6, key PH3/PH4; ADC1 pins; PD12 keep low. No trim targets, curves, fan law or conversion constants. |
| R2 | c3c40a3 | 15 | Pointer to 85 for the safe state. |
| R3 | c3c40a3 | 15 | "The only documented update path of the Main runs through the Control (VERIFIED, vendor guide); another entry unknown"; both transport candidates (Control → USART2; Main USART1) as HYPOTHESIS; 0025 rests on an unproven transport; CTRL and Control stay untouched until F1. |
| R4 | c3c40a3 | 15 | Bootloader entry condition unknown; the application's jump is dead code (HIGH), so entry from reset is expected; F1 remains the gate. |
| R5 | c3c40a3 | 15 | Rule 4 reason: read by the factory firmware at boot, bootloader use unknown (HYPOTHESIS); extended to the RTC backup registers. |
| R6 | c3c40a3 | 15 | Evidence: no option-byte code in the application (VERIFIED); set in production or by the bootloader (inference). |
| R7 | c3c40a3 | 15, 30 | "(at 0x0800)" dropped; "factory calibration and other factory-firmware data". |
| R8 | c3c40a3 | 20 | PH9 power hold HYPOTHESIS; PH5 input HIGH, power-key wiring HYPOTHESIS; evidence reworded as model consistency, no stock power-key logic. |
| R9 | c3c40a3 | 20 | Rail table: voltages HIGH, DCDC1 consumer MEDIUM, others HYPOTHESIS; rules: do not enable unlisted rails, do not exceed, do not switch DCDC1 off. |
| R10 | c3c40a3 | 20 | Open: power-up path without the Control (H1/H2), to be measured (T0-P2). |
| R11 | c3c40a3 | 40 | SPI6 pins PG12/PG13/PG14 (AF5), mode 0 MSB first, CS PG15, RST# PB5, INT# PC13; evidence as model consistency; CH394 datasheet cited. |
| R12 | c3c40a3 | 50 | "48 kHz" and "I²S master at 48 kHz" removed; MCLK 12.288 MHz on PC9/I2S_CKIN (HIGH, not measured); also Main I²S3 pins and codec reset PB10 (A); analog audio over CTRL tagged HIGH (inference). |
| R13 | c3c40a3 | 70 | PD5 TX / PD6 RX (AF7) on both MCUs; PD5 at idle level or high-impedance, never low. |
| R14 | c3c40a3 | 80 | "version 1.0.0" removed; D2 evidence as consistency; 0x05/0x06, 0x09/0x0A "exist, role unknown, MUST NOT be sent"; NCO clock 122.88 MHz and sample rates MEDIUM; open: strobe polarity/timing, turnaround, 0x01 offsets and calibration bytes (A9); NCO folding as an interface requirement (A8). |
| R15 | c3c40a3 | 60 (and 30) | "GT911 detected at 0x14" removed; the mock answers 0x14 by construction. |

Also corrected (RE side, same commit): `his-18-19-update-path.md` and
`his-gate-review-1.md` no longer say "the Main is updated only through the
Control"; `main-control-interlink.md` updated for 0023 (A11).

Advisories not applied (open for the gate): A1, A2, A3 (Control material only
marked informative in 50 and 60), A4, A5, A6, A7, A10.

Status: **not yet cleared**; ready for the diff re-check.

---

## Re-check (diff da50bd6..b960c0a, his/)

Checked `git diff da50bd6 his/integrate -- his` against the sources, plus the
new RE notes `his-17-ctrl-idle.md` and `his-18-19-update-path.md`. Commit
5f7679c (HIS-17/18/19) was read in full as new material.

### R1–R15

| # | Result | Note |
| --- | --- | --- |
| R1 | applied | `85-rf-control.md`: every pin checked against g7250-base peripherals (SPI1 PG11/PD7 AF5, chains A/B, ATU PD13/PG2/PG5, SPI2 PB13/PB15/PB12/PB14, channel map, PH6/PH3/PH4, ADC1 pins, PD12). No trim targets, power curves, fan law or conversion constants. The OE polarity (active low) comes from flow.md's power-off step; that the Open list says so is enough. |
| R2 | applied | 15, first paragraph. |
| R3 | applied | Both candidates, HYPOTHESIS; the vendor guide's documented path through the Control is added (VERIFIED, public guide). |
| R4 | applied | |
| R5 | applied | Includes the RTC backup registers. |
| R6 | applied | |
| R7 | applied | Offset removed in 15 and 30. |
| R8 | applied | |
| R9 | applied | |
| R10 | applied | Plus the AXP223 default state as an open item (A10 is in effect done). |
| R11 | applied | Pins match the source (PG12 MISO, PG13 SCK, PG14 MOSI). |
| R12 | applied | "= 256 × 48 kHz" is arithmetic on the clock, not a rate requirement: acceptable. |
| R13 | applied | |
| R14 | applied | |
| R15 | applied | Also removed from the 30 evidence line. |

### New material (5f7679c) and side effects

No code, stock addresses, timings, log text or protocol content leaked. The
stock behaviour from the RE notes (20 ms frames, settings-file save at
power-off, 100 ms power-off wait, the `.bbf` encryption) stayed on the RE side.
The vendor update procedure in 15 comes from the public user guide and is
needed for recovery, so it may stay. Three statements are tagged too strongly
or not at all:

- **N1 (required) — 70, rule 3 and the evidence line.** "With a silent Main the
  stock Control keeps running without an error state" has no tag. Its sources
  are weak: the emulator run is incomplete (the RE note says the USART TC flag
  is not modelled, so the Control's periodic TX never ran), and the firmware
  analysis gives "no link timeout" as MEDIUM. Tag it MEDIUM (firmware analysis;
  the emulator run does not cover the normal TX loop) and add "panel behaviour
  with a silent Main: to be confirmed on hardware".
- **N2 (required) — 20, "Switching off is the Main's job".** "The Control has
  no power control over the Main" has no tag; the source is firmware analysis
  only, and PCA9557 bit 5 on the Control (role HYPOTHESIS, "power hold" is one
  reading) is not excluded. Tag it HIGH (firmware analysis; wiring not traced).
  The MUST that follows rests on PH5 = power key and PH9 = power hold, both
  HYPOTHESIS. State that, and say what "a key press" is at the pin: PH5 low,
  pulled down by the key against the pull-up (HYPOTHESIS). Give no stock
  debounce or hold time.
- **N3 (required) — 15, installer item 4.** "Leaves the vendor path usable as
  the fallback if a transfer breaks" reads as a guarantee. With a broken
  application area, the vendor path works only if the Main bootloader enters
  update mode without a valid application. That is the unknown entry condition
  of the "Update path" subsection. Change it to: "never touches sector 0, so the
  vendor path stays available, provided the bootloader accepts an image with
  no valid application (unknown; F1)".

Advisory, not blocking:
- **A12** — 15, "RAM (320 KiB AXI SRAM) is smaller than the image". On the
  H72x the AXI SRAM size depends on the TCM/AXI shared-RAM option bytes (320 KiB
  matches the stack top seen, i.e. the setting as shipped). The product must not
  change it (rule 2). Total RAM including DTCM and D2 SRAM is larger than the
  image, but not contiguous. Streaming is still the right design; say "no single
  RAM region holds the image".
- **A13** — 85. Between reset and the product's GPIO init (and while the
  bootloader runs), the MCU pins are high-impedance. Whether board pull-ups hold
  PA10/PH10 inactive and the T/R lines in RX is not known. Add this to Open, and
  ask the product to set these pins first in its startup.
- **A14** — 85. PA12 is an output of unknown role that is set high in the
  power-off path (flow.md); list it next to PD12 as unknown.
- **A15** — 85 says the OE polarity is "VERIFIED from the power-off path". HIGH
  would match the evidence better (an interpretation of the power-off writes).
- A1, A2, A3 (beyond marking the material informative), A4, A5, A6 and A7
  remain open, as the emu session recorded.

### Verdict (re-check)

**NOT CLEARED**, because three tag/wording items remain: N1, N2, N3. R1–R15 are
all applied correctly, and nothing new leaks stock behaviour. N1–N3 are small
and local (70, 20, 15). Once they are applied, a check of that diff alone is
enough to mark the HIS **CLEARED**; no further full read is needed.

## Changes for the re-check

| # | Commit | Where | Change |
| --- | --- | --- | --- |
| N1 | 89f5b5d | 70 | Rule 3 tagged MEDIUM; emulator run marked incomplete (no periodic TX); panel behaviour to be confirmed on hardware. |
| N2 | 89f5b5d | 20 | "No power control over the Main" HIGH (firmware analysis; PCA9557 bit 5 not excluded); the MUST rests on two hypotheses; key press = PH5 low against the pull-up (HYPOTHESIS), no stock timing. |
| N3 | 89f5b5d | 15 | Installer item 4 conditional: vendor path after a broken transfer only if the bootloader accepts an image without a valid application (unknown; F1). |
| A12 | 89f5b5d | 15 | "No single RAM region holds the image"; AXI SRAM size depends on the TCM/AXI option bytes (rule 2). |
| A13 | 89f5b5d | 85 | Open: pin state between reset and init, board pull-ups unknown; set these pins first. |
| A14 | 89f5b5d | 85 | PA12 listed as an unknown output. |
| A15 | 89f5b5d | 85 | OE polarity HIGH (interpretation of the power-off writes). |

Re-check brought in as `7a9bc6f` (cherry-pick of `12bb91d`). Status: **not
yet cleared**; ready for the check of this diff.

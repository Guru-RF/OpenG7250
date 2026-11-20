# HIS 50 — Audio

**Evidence:** g7250-base peripherals docs (**rests on disassembly**). Emulator
(re/emu M1, M2): a codec is addressed at 0x18 on Main I²C1 and on Control I²C2
(consistency with models built from the same disassembly). Clock value: **rests
on disassembly**; not measured.

## Main

- AIC3204 codec on I²C1 0x18; reset PB10 (VERIFIED).
- MCLK: a 12.288 MHz (= 256 × 48 kHz) external clock on PC9 (I2S_CKIN), also
  the codec's MCLK (HIGH, not measured); its source is likely the FPGA
  (HYPOTHESIS).
- I²S3 pins: PA15 WS, PC10 CK, PC11 SDI, PC12 SDO (AF6) (VERIFIED).

## Control (informative; not driven under decision 0023)

- AIC3204 codec on I²C2 0x18, reset PH2.

## Audio between the units

- Main↔Control audio crosses the CTRL cable as analog, not over the serial link
  (HIGH: inference from the link capacity and the absence of an audio message
  type; not measured).

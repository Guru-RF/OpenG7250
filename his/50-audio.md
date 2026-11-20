# HIS 50 — Audio

**Evidence:** g7250-base peripherals/dsp docs (**rests on disassembly**).
Emulator observations (re/emu): codec addressed at 0x18 on Main I²C1 (M1) and on
Control I²C2 (M2). MCLK value: **rests on disassembly**; not measured.

- **Main** AIC3204 (I²C1 0x18); MCLK 12.288 MHz, 48 kHz.
- **Control** AIC3204 (I²C2 0x18, reset PH2); the Control codec is the **I²S
  master** at 48 kHz.
- The Control routes speaker/mic/line through the codec. Word length and sample
  rate are not fixed by the hardware; the codec's supported formats are in its
  datasheet. Main↔Control audio crosses the CTRL cable
  as analog (not over the serial link).

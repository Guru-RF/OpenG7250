# HIS 50 — Audio interface

**Evidence:** g7250-emu boot (codec init) + g7250-base peripherals/dsp docs.

- **Main** AIC3204 (I²C1 0x18): the Main codec; MCLK 12.288 MHz, 48 kHz.
- **Control** AIC3204 (I²C2 0x18, reset PH2): the Control codec is the **I²S
  master** at 48 kHz (PLL P=1/R=1/J=8 → 98.304 MHz, NDAC2/MDAC8/DOSR128); a
  documented PLL burst-write quirk leaves fs ≈ 48.005 kHz.
- I²S audio is 32-bit, 48 kHz; the Control routes speaker/mic/line through the
  codec. Main↔Control audio crosses the CTRL cable as analog (not over SLIP).

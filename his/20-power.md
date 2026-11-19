# HIS 20 — Power

**Evidence:** pins and the PMIC address from g7250-base `main_unit/docs`
(**rests on disassembly**). Emulator observations (re/emu): the stock Main drives
PH9 high and stays up with PH5 high (M8c PW-1 confirmation); the stock boot
addresses I²C1 7-bit 0x34 (M1). Rail voltages: the values the stock code writes
(**rest on disassembly**), decoded with the AXP223 datasheet; not measured.

- **PH9** is the power-hold output of the Main: high keeps the unit powered, low
  drops power.
- **PH5** is the power-key input, read with a pull-up. With no panel connected it
  reads high. (Whether an external pull-up exists on the board is not measured;
  the pull-up seen so far is the MCU's internal one.)
- **AXP223 PMIC** on I²C1, 7-bit address 0x34. Rails the hardware needs: DCDC1
  3.3 V, DCDC2 1.2 V, DCDC3 1.8 V, DCDC5 2.5 V, ALDO1 3.3 V, DLDO1 1.8 V.

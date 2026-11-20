# HIS 20 — Power

**Evidence:** pins and the PMIC address from g7250-base `main_unit/docs`
(**rests on disassembly**). Emulator observations (re/emu): the stock Main drives
PH9 high and stays up with PH5 high (M8c PW-1 confirmation); the stock boot
addresses I²C1 7-bit 0x34 (M1). CTRL power wiring: owner (HIGH); the power-key
route to PH5: HYPOTHESIS (re/emu M8c, H1/H2). Rail voltages: the values the stock code writes
(**rest on disassembly**), decoded with the AXP223 datasheet; not measured.

- **PH9** is the power-hold output of the Main: high keeps the unit powered, low
  drops power.
- **PH5** is the power-key input, read with a pull-up. With no panel connected it
  reads high. (Whether an external pull-up exists on the board is not measured;
  the pull-up seen so far is the MCU's internal one.)
- The Main powers the Control through the CTRL cable; PH9 low therefore also
  removes the Control's supply. The panel's power key reaches the Main's PH5
  over the CTRL cable.
- **Switching off is the Main's job.** The Control has no power control over
  the Main. With the CTRL link idle (`70-interlink.md`), new Main firmware MUST
  watch PH5 itself and, on a power-key press, bring the radio to a safe state
  and drop PH9.
- **AXP223 PMIC** on I²C1, 7-bit address 0x34. Rails the hardware needs: DCDC1
  3.3 V, DCDC2 1.2 V, DCDC3 1.8 V, DCDC5 2.5 V, ALDO1 3.3 V, DLDO1 1.8 V.

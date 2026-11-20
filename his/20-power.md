# HIS 20 — Power

**Evidence:** pins and the PMIC address from g7250-base `main_unit/docs`
(**rests on disassembly**). Emulator (re/emu M1, M8c), consistency with models
built from the same disassembly, not hardware evidence: PH9 is configured as an
output and PH5 as an input with pull-up; a device at 0x34 is addressed on
I²C1. CTRL power wiring: owner (HIGH). Rail voltages: the values as programmed
by the factory firmware (**rest on disassembly**), decoded with the AXP22x
datasheet; not measured.

- **PH9** is the power-hold output of the Main: high keeps the unit powered, low
  drops power (HYPOTHESIS).
- **PH5** is an input (HIGH) read with a pull-up, most likely the power key
  (wiring HYPOTHESIS). With no panel connected it reads high. (Whether an
  external pull-up exists on the board is not measured; the pull-up seen so far
  is the MCU's internal one.)
- The Main powers the Control through the CTRL cable (HIGH); PH9 low therefore
  also removes the Control's supply. The panel's power key most likely reaches
  PH5 over the CTRL cable (HYPOTHESIS).
- **Switching off is the Main's job.** The Control has no power control over
  the Main (HIGH: firmware analysis only, wiring not traced; a power-hold role of
  the Control's PCA9557 bit 5 is not excluded). With the CTRL link idle
  (`70-interlink.md`), new Main firmware MUST watch PH5 itself and, on a
  power-key press, bring the radio to the safe state (`85-rf-control.md`) and
  drop PH9. A key press is PH5 low, pulled down by the key against the pull-up
  (HYPOTHESIS); debounce and hold time are the product's choice. This rule rests
  on two hypotheses: PH5 is the power key and PH9 is the power hold.

## AXP223 PMIC (I²C1, 7-bit 0x34)

| Rail | Voltage (HIGH) | Consumer |
| --- | --- | --- |
| DCDC1 | 3.3 V | likely the MCU supply (MEDIUM) |
| DCDC2 | 1.2 V | unknown (HYPOTHESIS) |
| DCDC3 | 1.8 V | unknown (HYPOTHESIS) |
| DCDC5 | 2.5 V | unknown (HYPOTHESIS) |
| ALDO1 | 3.3 V | unknown (HYPOTHESIS) |
| DLDO1 | 1.8 V | unknown (HYPOTHESIS) |

Hardware-protection constraints for new firmware:
- Rails not in this table (DCDC4, DC5LDO, ALDO2/3, ELDO1–3, DLDO2–4, DC1SW) are
  off; their consumers, if any, are unknown. **MUST NOT** enable them.
- **MUST NOT** set a listed rail above its stated value.
- **MUST NOT** switch DCDC1 off while running (likely the MCU supply).

## Open

- Power-up path without the Control: the key switches the supply on in
  hardware and the MCU holds it with PH9 (H1), or the MCU runs on standby power
  and waits for PH5 (H2). HYPOTHESIS, to be measured (T0-P2 in the emulator
  spec). Decision 0025 depends on it. Needs hardware (`90-needs-hardware.md`).
- The AXP223's power-on default state (which rails are on before any I²C write)
  per its datasheet/OTP: not yet stated.

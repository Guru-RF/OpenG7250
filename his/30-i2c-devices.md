# HIS 30 — I²C devices

**Evidence:** bus and address map from g7250-base peripherals docs and
OpenG7250 RE (**rests on disassembly**). Emulator observations (re/emu): the
stock Main addresses 0x34, 0x50, 0x68/0x6A and 0x18 on I²C1 (M1); the stock
Control detects GT911 at 0x14 on I²C1 and addresses 0x18 and 0x19 on I²C2 (M2).
Addressing modes and register paging: device datasheets (24Cxx, TLV320AIC3204,
5P49V6965, GT911, PCA9557). VersaClock 6 outputs: the divider values the stock
code writes (**rest on disassembly**), decoded with the 5P49V6965 datasheet; the
crystal is not read from the board, so the frequencies are HYPOTHESIS. Bus speeds are the rates the stock code uses
(**rest on disassembly**); device limits per datasheet.

## Main — I²C1 (~400 kHz)

| 7-bit | Device | Interface |
| --- | --- | --- |
| 0x34 | AXP223 PMIC | register interface (datasheet) |
| 0x50 | 24Cxx EEPROM | 16-bit addressing; factory calibration is stored at 0x0800. Read-only for new firmware (see `15-stock-recovery.md`) |
| 0x18 | AIC3204 codec | paged registers (datasheet) |
| 0x68 or 0x6A | VersaClock 6 (5P49V6965) | crystal reference; see the output table below |

### VersaClock 6 outputs

| Output | State | Frequency | Feeds |
| --- | --- | --- | --- |
| OUT1 | enabled, LVDS 3.3 V (HIGH) | ≈ 245.76 MHz with a 26 MHz crystal (HYPOTHESIS; 122.88 MHz not excluded) | most likely the FPGA clock behind the 122.88 MHz NCO (`80-rf-fpga.md`) (HYPOTHESIS) |
| OUT2–OUT4 | off (MEDIUM) | — | — |

The crystal frequency and where OUT1 goes are to be confirmed on the board
(crystal marking, a frequency measurement on OUT1).

## Control
- I²C1: GT911 capacitive touch at 0x14 or 0x5D; the INT level at reset selects
  the address (INT high → 0x14), per the GT911 datasheet.
- I²C2 (~100 kHz): AIC3204 codec 0x18, PCA9557 I/O expander 0x19, used as
  outputs: bit4 BT power, bit5 shutdown pulse, bit6 TX, bit7 RX.

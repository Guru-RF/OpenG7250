# HIS 30 — I²C devices

**Evidence:** bus and address map from g7250-base peripherals docs and
OpenG7250 RE (**rests on disassembly**). Emulator observations (re/emu): the
stock Main addresses 0x34, 0x50, 0x68/0x6A and 0x18 on I²C1 (M1); the stock
Control detects GT911 at 0x14 on I²C1 and addresses 0x18 and 0x19 on I²C2 (M2).
Addressing modes and register paging: device datasheets (24Cxx, TLV320AIC3204,
5P49V6965, GT911, PCA9557). Bus speeds are the rates the stock code uses
(**rest on disassembly**); device limits per datasheet.

## Main — I²C1 (~400 kHz)

| 7-bit | Device | Interface |
| --- | --- | --- |
| 0x34 | AXP223 PMIC | register interface (datasheet) |
| 0x50 | 24Cxx EEPROM | 16-bit addressing; settings block @0x0000 (0x1A8 B) valid iff bytes 0x000/0x1A3/0x1A4 = 'd' (0x64); calibration @0x0800; NVPARAM @0x1800 *(Decide, see GATE-REVIEW)* |
| 0x18 | AIC3204 codec | paged registers (datasheet) |
| 0x68 or 0x6A | VersaClock 6 | 0x70-byte init table from reg 0 *(Decide, see GATE-REVIEW)* |

## Control
- I²C1: GT911 capacitive touch at 0x14 or 0x5D; the INT level at reset selects
  the address (INT high → 0x14), per the GT911 datasheet.
- I²C2 (~100 kHz): AIC3204 codec 0x18, PCA9557 I/O expander 0x19, used as
  outputs: bit4 BT power, bit5 shutdown pulse, bit6 TX, bit7 RX.

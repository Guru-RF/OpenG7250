# HIS 30 — I²C device interface

**Evidence:** g7250-emu I2C bring-up (poll-hang analysis + functional EEPROM) +
g7250-base peripherals doc + OpenG7250 RE.

## Main — I²C1 (~400 kHz, TIMINGR 0x00D049FB)
Bring-up order: AXP223 → EEPROM → VersaClock 6 → AIC3204. Each device's error
path continues (the settings loader runs with force-reset).

| 7-bit | Device | Interface behaviour |
| --- | --- | --- |
| 0x34 | AXP223 PMIC | register writes (rail setup), then a 256-byte dump read |
| 0x50 | 24Cxx EEPROM | 16-bit addressing; settings block @0x0000 (0x1A8 B) valid iff bytes 0x000/0x1A3/0x1A4 = 'd' (0x64); calibration @0x0800; NVPARAM @0x1800 |
| 0x18 | AIC3204 codec | paged register writes (audio) |
| 0x68→0x6A | VersaClock 6 | 0x70-byte init table from reg 0; tries 0x68 then 0x6A |

**Interface fact:** the HAL I²C driver polls the status register (TXIS/TC/STOPF);
a device must ACK and complete transfers or the firmware stalls per-byte on a
100 ms timeout.

## Control
- I²C1: GT911 capacitive touch at 0x14 (INT-high-at-reset selects 0x14; fallback
  0x5D); reads a 186-byte config block + checksum.
- I²C2 (~100 kHz): AIC3204 codec 0x18, PCA9557 I/O expander 0x19 (all-outputs,
  boot value 0x8B; bit4 BT power, bit5 shutdown pulse, bit6 TX, bit7 RX).

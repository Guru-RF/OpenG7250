# HIS 40 — Ethernet / LAN

**Evidence:** pins and SPI settings from g7250-base `main_unit/docs/peripherals.md`
(SPI6 section, VERIFIED in the firmware analysis, **rests on disassembly**);
register compatibility per the CH394 datasheet (WCH CH394DS1). Emulator (re/emu
B2): a W5500-register-compatible model on SPI6 with CS on PG15 is accepted by the
factory image; this shows consistency with a model built from the disassembly,
not hardware evidence.

- The Main's LAN controller is a **CH394** (W5500-register-compatible, per its
  datasheet) on **SPI6**, used by nothing else on that bus (HIGH). The LAN
  connector is on the Main unit (HIGH).

| Signal | Pin | Notes | Tag |
| --- | --- | --- | --- |
| SCK / MISO / MOSI | PG13 / PG12 / PG14 (AF5) | SPI mode 0, 8-bit, MSB first | VERIFIED |
| CS# | PG15 | GPIO, active low | VERIFIED |
| RST# | PB5 | active low | VERIFIED |
| INT# | PC13 | active low, needs a pull-up | VERIFIED |

- Reset timing and the maximum SCK come from the CH394 datasheet (about 17 MHz
  is known to work).
- Network behaviour (addressing, ports, protocols) is defined by the product
  spec, not here.

# HIS 15 — Keeping the factory firmware reinstallable

**Requirement (ON8ST).** It must always be possible to reinstall the original
factory firmware. New firmware therefore leaves the update path and the
persistent storage the factory firmware depends on untouched.

**Evidence:** g7250-base `main_unit/docs/peripherals.md`, `main_unit/docs/flow.md`
and `control_unit/docs/peripherals.md` (**rest on disassembly**): updates are
done by the bootloader in flash sector 0 after a reset, not by the application
(HIGH); the option bytes are set in production or by the bootloader, not by the
application (VERIFIED). The update transport of the Main is not yet known
(HYPOTHESIS: a serial bootloader); the rollback drill on the real radio (F1 in
the emulator spec) has to prove the path before the first flash of new firmware.

New firmware:

1. **MUST NOT** write the bootloader region 0x08000000–0x0801FFFF.
2. **MUST NOT** change the option bytes (RDP, WRP, BOOT_ADD and the others); a
   wrong value can lock or erase the MCU.
3. **MUST** treat the 24Cxx EEPROM (I²C1 0x50) as read-only. It holds the
   factory calibration (at 0x0800) and data of the factory firmware.
4. **MUST NOT** use the Backup SRAM; the factory firmware keeps state there.
5. Keeps its own persistent data only in its own application flash, from
   0x08020000 (`10-reset-clock.md`).

With the first product (a headless Main with the stock Control), only the Main
is reflashed; the Control keeps its factory firmware.

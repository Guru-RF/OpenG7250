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

## Main flash

**Evidence:** part STM32H725xG/H735xG (MEDIUM, **rests on disassembly**: HAL and
clock evidence); flash organisation per the ST datasheet. Image extent: the
factory image V1.0.1 file (VERIFIED: base plus file size).

| Range | Sectors (128 KiB) | Content |
| --- | --- | --- |
| 0x08000000–0x0801FFFF | 0 | bootloader (never written, rule 1) |
| 0x08020000–0x080FFFFF | 1–7 (896 KiB) | application area |

- The factory Main image V1.0.1 is a flat image for 0x08020000 of 453 152 bytes
  (sectors 1–4). Two such images do not fit in the application area.
- RAM (320 KiB AXI SRAM) is smaller than the image.

## Installing the factory firmware from the new firmware

New firmware MAY include an installer that writes an owner-supplied factory
Main image (a flat image for 0x08020000) without the Control. Such an installer:

1. runs from RAM while it rewrites the application area;
2. writes only sectors 1–7, never sector 0 and never the option bytes (rules 1
   and 2);
3. receives the image in parts (for example one sector at a time over
   Ethernet), since it does not fit in RAM;
4. leaves the vendor update path through the Control usable as the fallback if
   a transfer breaks.

Not yet known, to be proven on the radio before relying on it: whether the
vendor bootloader starts an application it did not write itself.

## The vendor update path

The vendor path updates the Main only through the Control unit: files on the
Control's USB drive, then the Control's update menu ([BL] held with [POWER])
(vendor update guide V1.0.1, public). It depends on sector 0 of both MCUs and
on the CTRL cable. New Main firmware MUST NOT disable it; rules 1 and 2 keep it
intact. How the Main's bootloader is entered and fed is not known.

## FPGA

The FPGA configures itself from its own configuration flash; the Main firmware
does not load it (HIGH, **rests on disassembly**). Switching Main firmware does
not change the FPGA image. New firmware has no reason to access that flash and
MUST NOT try.

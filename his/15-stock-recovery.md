# HIS 15 — Keeping the factory firmware reinstallable

**Requirement (ON8ST).** It must always be possible to reinstall the original
factory firmware. New firmware therefore leaves the update path and the
persistent storage the factory firmware depends on untouched. For the safe
state of the RF section see `85-rf-control.md`.

**Evidence:** g7250-base `main_unit/docs/peripherals.md`, `main_unit/docs/flow.md`,
`main_unit/docs/memory_map.md` and `control_unit/docs/peripherals.md` (**rest on
disassembly**):
- updates are done by the bootloader in flash sector 0 after a reset, not by
  the application (HIGH for the Main; for the Control the absence of update
  code is VERIFIED, the mechanism HYPOTHESIS);
- the application contains no option-byte code (VERIFIED); the option bytes
  are set in production or by the bootloader (inference);
- the rollback drill on the real radio (F1 in the emulator spec) has to prove
  the path before the first flash of new firmware.

New firmware:

1. **MUST NOT** write the bootloader region 0x08000000–0x0801FFFF.
2. **MUST NOT** change the option bytes (RDP, WRP, BOOT_ADD and the others); a
   wrong value can lock or erase the MCU.
3. **MUST** treat the 24Cxx EEPROM (I²C1 0x50) as read-only. It holds factory
   calibration and other factory-firmware data.
4. **MUST NOT** use the Backup SRAM or the RTC backup registers. The factory
   firmware reads the Backup SRAM at boot, and the bootloader's use of the
   backup domain is unknown (HYPOTHESIS).
5. Keeps its own persistent data only in its own application flash, from
   0x08020000 (`10-reset-clock.md`). Open check (not a rule): whether the
   bootloader uses flash sector 6 as a staging area (HYPOTHESIS from unused
   strings in the application); F1 settles it.

Under decision 0023 only the Main is reflashed; the Control keeps its factory
firmware.

## Update path of the Main

- **Documented path (VERIFIED, vendor update guide V1.0.1, public):** the only
  documented update path of the Main runs through the Control: files on the
  Control's USB drive, then the Control's update menu ([BL] held with
  [POWER]). Whether the Main bootloader has another entry is unknown (the
  bootloaders are not analysed).
- **Transport, two candidates (HYPOTHESIS):**
  1. the Control bootloader sends the image from its USB drive over the CTRL
     link (USART2) to the Main bootloader;
  2. the Main bootloader takes the image on the Main console USART1.
- **Entry condition unknown.** What makes the Main bootloader enter update mode
  instead of starting the application is not known. The application's own jump
  to the bootloader is dead code (HIGH), so entry is expected from reset without
  help from the application. F1 remains the gate.
- **Consequence for decision 0025** (install stock and new firmware the same
  way, from the Main, without the Control): it rests on an unproven transport.
  If candidate 1 is the real path, the CTRL cable and the stock Control are part
  of the recovery path. Until F1 settles it, new firmware MUST leave both the
  CTRL link and the Control untouched (already required by 0023,
  `70-interlink.md`) and MUST NOT disable the vendor path (rules 1 and 2 keep
  sector 0 intact).

## Main flash

**Evidence:** part STM32H725xG/H735xG (MEDIUM, **rests on disassembly**: HAL and
clock evidence); flash organisation per the ST datasheet (so MEDIUM as well).
Image extent: the factory image V1.0.1 file (VERIFIED: base plus file size).

| Range | Sectors (128 KiB) | Content |
| --- | --- | --- |
| 0x08000000–0x0801FFFF | 0 | bootloader (never written, rule 1) |
| 0x08020000–0x080FFFFF | 1–7 (896 KiB) | application area |

- The factory Main image V1.0.1 is a flat image for 0x08020000 of 453 152 bytes
  (sectors 1–4). Two such images do not fit in the application area.
- No single RAM region holds the image. The AXI SRAM is 320 KiB as shipped
  (stack top seen); on the H72x its size depends on the TCM/AXI shared-RAM option
  bytes, which new firmware MUST NOT change (rule 2). DTCM and D2 SRAM add RAM,
  but not contiguously.

## Installing the factory firmware from the new firmware

New firmware MAY include an installer that writes an owner-supplied factory
Main image (a flat image for 0x08020000) without the Control. Such an installer:

1. runs from RAM while it rewrites the application area;
2. writes only sectors 1–7, never sector 0 and never the option bytes (rules 1
   and 2);
3. receives the image in parts (for example one sector at a time over
   Ethernet), since it does not fit in RAM;
4. never touches sector 0, so the vendor path stays available after a broken
   transfer, provided the Main bootloader accepts an image when there is no
   valid application (unknown: the entry condition above; F1).

Not yet known, to be proven on the radio before relying on it: whether the
vendor bootloader starts an application it did not write itself.

## FPGA

The FPGA configures itself from its own configuration flash; the Main firmware
does not load it (HIGH, **rests on disassembly**). Switching Main firmware does
not change the FPGA image. New firmware has no reason to access that flash and
MUST NOT try.

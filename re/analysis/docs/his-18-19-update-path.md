# HIS-18 / HIS-19: update path, flash room and the FPGA image

RE answers for HIS-18 and HIS-19, with ON8ST's requirement of 2026-11-20: the
factory firmware must be installable **in the same way as the new firmware,
from the Main side and without the Control**. Sources: the vendor update guide
in the release package (`re/analysis/firmware/…/2026-11-09_Xiegu_G7250_update_V1.0.1.pdf`,
public), g7250-base (snapshot 18c9164) and the emulator. The bootloaders are not
part of the analysed images, so everything about them is inferred.

Hardware facts and constraints from this note go into `his/15-stock-recovery.md`.

## 1. How the stock path updates the Main today

**Through the Control (VERIFIED, vendor guide steps 3–15).**
1. Connect a PC to the rear USB port of the Control unit; the radio shows a
   USB drive of about 16 MB (the Control's W25Qxx SPI flash, exposed as mass
   storage by the Control application).
2. Copy `G7250_ControlUnit_Fw_V1.0.1.ctl` and `G7250_MainUnit_Fw_V1.0.1.bbf`
   to that drive.
3. Power off, wait, hold **[BL]** and press **[POWER]** until the screen shows
   the update menu (the Control's bootloader).
4. Choose "Baseband Board Firmware Update" (Main) or "Control board Firmware
   Update"; it erases and writes in about 30 s. After a Main update the radio
   shuts down and restarts.

**Transport to the Main (HYPOTHESIS).** Neither application contains update or
forwarding code (g7250-base `main_unit/docs/peripherals.md` "Update transport",
HIGH): no file name, no SLIP type, no Main reset or boot line. The transfer is
therefore done by the two sector-0 bootloaders, most likely the Control
bootloader sending the `.bbf` over the CTRL link (USART2) to the Main
bootloader. A USART1 console path is the alternative. The Main has no USB
connector; the Main application has no LAN update code, and nothing suggests the
bootloader uses the CH394.

**Answer.** Today the Main is updated **only through the Control**.

## 2. Entering and feeding the Main bootloader without the Control

Not known; nothing in the applications shows it.
- The Main application has a jump to the bootloader (VTOR = 0x08000000), but
  nothing arms it in V1.0.1 (dead code, HIGH). The bootloader runs from reset.
- How the Main bootloader decides to wait for an image (a level on a CTRL line,
  a command on USART2, a timeout) is outside the images. Settling it needs a
  sector-0 dump or a bus capture during a vendor update.
- Independent of the vendor bootloader: the STM32H7 ROM system bootloader
  (BOOT0 pin or BOOT_ADD option bytes) and SWD. Whether BOOT0 and SWD are
  reachable on the Main board is not known (g7250-base `docs/hardware_test_plan.md`
  T1, headers and pads). Changing option bytes is excluded by
  `his/15-stock-recovery.md`.

**Consequence for ON8ST's requirement.**
- **New firmware → stock, from the Main side:** possible with an installer in
  the new firmware itself (see 4). It needs no Control and no vendor bootloader.
- **Stock → new firmware, without the Control:** the stock Main application has
  no transfer path, so the first install of new firmware cannot be done from the
  Main side through the stock application. Options: the vendor path through the
  Control (needs an image the vendor bootloader accepts, see 3), SWD, or the ROM
  bootloader if BOOT0 is reachable. Every option has to be proven on the radio.

## 3. What the bootloader expects

- The vendor path consumes the encrypted `.bbf` file (AES-256-ECB per
  g7250-base README). Which bootloader decrypts it (Control or Main) is not
  known.
- Checks (signature, CRC, version) are not known. Orphan strings in the Main
  application mention a checksum check for a new **bootloader** (dead code), not
  for the application.
- The decrypted Main image is a flat image for 0x08020000 (VERIFIED: base plus
  file size cover the whole image; the emulator runs it loaded there).
- Open: whether the Main bootloader starts an application it did not write
  itself (a validity flag or checksum kept elsewhere). This decides whether an
  own installer can restore stock; it has to be tested on the radio (F1 drill).

## 4. Flash layout of the Main and room for a second image

- Part: STM32H725xG or H735xG (MEDIUM, g7250-base `docs/mcu_identification.md`):
  1 MiB flash in eight 128 KiB sectors (ST datasheet).
- Sector 0 (0x08000000–0x0801FFFF): bootloader.
- Application area 0x08020000–0x080FFFFF: 896 KiB, sectors 1–7.
- The stock V1.0.1 image occupies 0x08020000–0x0808EA20 (453 152 bytes),
  i.e. sectors 1–4; its last 21 852 bytes are fill (VERIFIED, g7250-base
  `main_unit/docs/memory_map.md`). Sectors 5–7 (384 KiB) are not referenced by
  the image.
- A retained second copy of the stock image does **not** fit next to an
  application of similar size: two images need 8 sectors, the application area
  has 7. A copy in sectors 5–7 would have to be compressed below 384 KiB.
- RAM (320 KiB AXI SRAM, stack top 0x24050000) is smaller than the image, so a
  RAM-resident installer has to stream: receive one 128 KiB sector at a time
  (over Ethernet), erase and write it, never touching sector 0 or the option
  bytes. If a transfer breaks, the Main has no valid application, but sector 0
  is intact and the vendor path through the Control can still restore it.

## 5. The FPGA image

**Fixed in the FPGA's own configuration flash (HIGH).** The Main firmware never
loads or reprograms the FPGA: the command set has no flash command, and the
strings about a missing FPGA or FPGA-flash verification are unreferenced
(g7250-base `main_unit/docs/peripherals.md` "Bitstream and version"). A SOIC-8
part next to the FPGA on the board is the likely configuration flash
(HYPOTHESIS, `docs/hardware.md`). Switching Main firmware does not change the
FPGA image.

## Open, to be proven on the radio

- Transport and entry of the Main bootloader (bus capture during a vendor update).
- Whether the Main bootloader starts an application written by an own installer.
- Whether SWD and BOOT0 are reachable on the Main board.
- The F1 rollback drill: vendor path restores stock after new firmware.

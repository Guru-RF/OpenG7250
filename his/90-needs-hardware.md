# HIS 90 — Open points that need the real radio

Questions from the product side that the sources and the emulator cannot
settle. Each needs a measurement or a test on the radio. Until then the
statements in the other sections stay as tagged there.

| Question | What is known now | What is needed |
| --- | --- | --- |
| HIS-02: the three NCO words in the FPGA 0x01 frame | Two of the three follow the operating frequencies: one the main VFO (including RIT), one the other VFO (MEDIUM). The role of the third word and the order of the words in the frame are unknown (`80-rf-fpga.md`). | A bus capture of 0x01 frames while changing frequency, or the same in the emulator with the fused FPGA model logging 0x01 frames (not yet done). |
| HIS-07, HIS-11, HIS-12: timing and calibration values | Not in this spec on purpose: stock timing and stock calibration are not hardware facts. | Measurement on the radio. |
| HIS-17: power-up without the Control | Two hypotheses H1/H2 (`20-power.md`, Open). | Observation T0-P2: Main with the CTRL cable disconnected, DC on; does the Ethernet link come up? |
| HIS-19: does the vendor bootloader start an image it did not write; is there a bootloader entry without the Control | Unknown; the bootloaders are not analysed (`15-stock-recovery.md`). | The F1 drill, after the steps below. |

## Safe order of the hardware steps for HIS-19 / F1

Radio in RX, dummy load on the antenna port, for every step. Nothing below
writes or erases unless the step says so.

1. **Locate SWD on the Main board.** The Main's SWD pins are PA13 (SWDIO) and
   PA14 (SWCLK) (ST datasheet). The factory application does not reconfigure
   them (HIGH: absent from the pin map), so SWD stays available while it runs.
   Whether pads or a header are reachable on the board is **not known**; look
   for them on board photos first (no wiring with power on).
2. **Read the option bytes via SWD, read only.** ST-LINK in "hot plug" mode (no
   reset, no halt; halting the Main can freeze the PA state). Read RDP,
   BOOT_ADD0/1, WRP/PCROP, BOR, IWDG settings, DBGMCU_IDCODE (Main expected
   DEV_ID 0x483) and the flash-size register. Never write, never press
   "Apply": changing RDP from level 1 to 0 erases the flash, level 2 is
   permanent.
3. **Only if RDP is level 0: back up the full flash** of the Main and the
   Control, including the bootloader sectors. Keep the backups locally,
   outside any repository; they are firmware. If RDP is level 1, stop here and decide
   with ON8ST: no backup is possible, so a failed F1 could only be recovered
   through the vendor path.
4. **Only then try F1** with a minimal test image (for example one that only
   holds the safe state of `85-rf-control.md` and blinks a known output),
   written to 0x08020000 only (never sector 0), by SWD if RDP is level 0. The
   vendor path needs a package its bootloader accepts, which is open
   (`15-stock-recovery.md`). Check whether the vendor bootloader starts it, then restore the factory firmware through the vendor
   update path (`15-stock-recovery.md`) and confirm stock works.

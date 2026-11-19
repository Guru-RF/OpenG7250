# Emulator job — action-list status (A–E)

Status of the A–E action list after the C#-peripheral unlock (runtime-compiled
custom slaves register when referenced by fully-qualified type name; inherited
C# models can be swapped via `sysbus Unregister`). ✅ done · ◐ partial · ⏳ later.

## A. Main boot to the service loop — ✅ DONE (M1)
Boots `System started` → AXP PSU → EEPROM → VersaClock → LAN default IP
192.168.3.199:50001 → codec → TRX RX-mode → service loop; 60 s VT, no hang.
A1 PWR 0x08 ready ✅ · A2 chain chased ✅ · A3 FPGA errors tolerated (→ D2) ·
A4 60 s no hang ✅ · A5 A1.12 default IP ✅. (docs/M1-status.md,
tests/baseline/boot_milestone.sh.)

## B. Realistic I/O — B1 ✅ · B2 ◐
- B1 ✅ functional EEPROM (models/csharp/G7250Slaves.cs `G7250Eeprom24C`,
  compiled in at runtime): the Main logs "[OK] Settings data successfully loaded
  from EEPROM". Wired by default (g7250_main_i2c1_func.repl).
- B2 ◐ functional CH394 (`G7250Ch394`, ISPIPeripheral) compiles + registers on
  spi6; the W5500 SPI-frame decode / SIPR read-back log still needs validating.
  A1.12 is already confirmed firmware-side (E2), so this is a nicety.

## C. Control boot — ✅ DONE (M2/C2)
Boots through SLIP client, AIC3204 codec, FatFS mount attempt, **GT911 touch at
0x14**, all service timers, then — via the `G7250LtdcStub` CDSR VSYNC shim
swapped in for the headless-silent C# LTDC — PAST the display wait into its
**GUI service loop** (DMA2D rendering + panel GPIO + SDMMC + input). Next minor
register: sdmmc IntStatus (no SD card modelled). (docs/M2-control-status.md.)

## D. Two machines — D1 ✅ · D2 ⏳ (M3)
- D1 ✅ harness: harness/g7250emu/slip_run.py boots both MCUs in one emulation,
  wires USART2↔USART2 through a UART hub, and SLIP bytes (0xC0-delimited) are
  transmitted over the link. (RX is circular-DMA, not register-visible; full
  bidirectional confirmation would watch DMA1 S3.)
- D2 ⏳ FPGA fused model (48 kHz I/Q over the GPIOE bit-bang) — explicitly M3;
  needs the bit-bang bus protocol modelled. The Main's FPGA bus errors are
  logged and tolerated, so the boot is unaffected.

## E. Finishing / hardening
- E1 ✅ dual-signal hang verdict (MMIO poll-hang + executed-frozen WFI idle).
- E2 ✅ PW-1 emulator confirmation (r0_confirm.py): Main matches the prediction.
- E3 ✅ boot-milestone regression (tests/baseline/boot_milestone.sh).
- E4 ◐ g7250-his repo scaffolded (~/Repos/on8st/g7250-his): role, clean-room
  process and section outline in place; sections are populated per fact under
  the clean-room review (ongoing, M8b).

## Not in scope (policy)
No decryption; no push/PR/mail without Stan's "verstuur"; no shared GitHub org
until the Belgian IP advice. Decrypted images stay outside any repo; the
manifest hash stays local/untracked.

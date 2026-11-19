# Emulator job — action-list status (A–E)

Snapshot of the A–E action list. ✅ done · ◐ partial (blocker noted) · ⏳ scoped.

## A. Main boot to the service loop — ✅ DONE (M1)
- A1 ✅ PWR `+0x08` ready override (g7250_main.repl).
- A2 ✅ never-ready chain chased (SysTick clock → I2C1 shims → PWR) to the loop.
- A3 ◐ FPGA GPIOE bit-bang: 24 bus errors logged and tolerated; the fused FPGA
  model is M3 (D2). Not blocking.
- A4 ✅ 60 s virtual time, no dead hang ("running — candidate main loop").
- A5 ✅ A1.12: forced default IP 192.168.3.199 / port 50001 programmed
  (console + r0_confirm.py). Reading it back from the chip needs a functional
  CH394 (B2).
Evidence: docs/M1-status.md, tests/baseline/boot_milestone.sh (ALL PASS).

## B. Realistic I/O where needed — ⏳ SCOPED (optional, not needed to boot)
- B1 functional EEPROM (24Cxx NVPARAM with the three 'd' markers), B2 functional
  CH394 (store SIPR, read the IP back). Renode's built-in `Mocks.DummyI2CSlave`
  ACKs but cannot return crafted bytes, and this portable build has no scriptable
  I2C/SPI *slave* base (the STM32F7_I2C controller drives the HAL flags; a
  functional slave needs an `II2CPeripheral`/`ISPIPeripheral`, i.e. a C#
  peripheral compiled in). The clean-room device *logic* is host-tested in
  models/devices/ (i2c_devices.py, ch394.py) ready to back such a slave. The
  boot reaches the service loop without it (every device error path continues),
  so B is a later refinement, pursued when a test depends on real device data.
  Capability check (2026-11-19): runtime C# peripheral compile (`i @file.cs`
  then register a custom `II2CPeripheral`) did NOT resolve the type in this
  portable build ("Error E04: Could not resolve type"), so a functional slave
  needs either a prebuilt Renode plugin assembly or sorting out the runtime
  compile path — tracked, not a quick win.

## C. Control boot — ◐ PARTIAL (M2)
- C1 ✅ control_run.py (+ shared bootcore.py) and the Control I2C overlay.
- C2 ◐ boots through all non-display init — SLIP client, AIC3204 codec, FatFS
  SPI-flash mount attempt, H-22/InputDev, **GT911 touch init at 0x14**, all
  service timers — then poll-hangs on `ltdc +0x48` (CDSR) waiting for VSYNC,
  which Renode's STM32LTDC does not toggle headless (`FramesPerVirtualSecond`
  set but the repainter needs a video sink that headless `--disable-xwt` does
  not start). Next = a video sink that starts the repainter, or a CDSR shim
  (same C#-peripheral limitation as B). Evidence: docs/M2-control-status.md.

## D. Two machines together — ◐ SKELETON / ⏳ SCOPED
- D1 ◐ SLIP link skeleton: platforms/g7250_slip_link.resc boots both MCUs in one
  emulation and wires USART2↔USART2 through a UART hub (verified to load). A full
  SLIP exchange also needs the Control past its LTDC wait (C2).
- D2 ⏳ FPGA fused model (48 kHz I/Q over the GPIOE bit-bang) — M3 work.

## E. Finishing / hardening
- E1 ✅ observe hang verdict refined: dual signal (MMIO poll-hang + executed-
  frozen WFI idle), so a HAL_Delay busy-wait is no longer a false idle-hang.
- E2 ✅ PW-1 emulator confirmation (r0_confirm.py): the stock Main matches the
  "H2/auto-start, PH5 high" prediction. docs/M8c-R0-report.md updated.
- E3 ✅ boot-milestone regression (tests/baseline/boot_milestone.sh).
- E4 ⏳ g7250-his: ready to start (M8b). Proven behaviours to seed the clean-room
  hardware-interface spec: H72x reset/clock (HCLK 275 MHz, SysTick), the I2C1
  device map + bring-up order, PWR ready semantics, the forced-default-IP LAN
  bring-up, the TRX RX-mode init, and the Control's GT911/codec/LTDC path.

## Not in scope (policy)
No decryption; no push/PR/mail without Stan's "verstuur"; no shared GitHub org
until the Belgian IP advice. Decrypted images stay outside any repo; the
manifest hash stays local/untracked.

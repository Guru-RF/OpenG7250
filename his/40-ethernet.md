# HIS 40 — Ethernet / LAN interface

**Evidence:** g7250-emu Main boot console (LAN init) + CH394 model + g7250-base.

- The Main's LAN controller is a **CH394** (W5500-register-compatible) on SPI6.
- **Forced default addressing (emulator-confirmed, A1.12):** IP 192.168.3.199,
  gateway 192.168.3.1, mask 255.255.255.0, base port 50001. The firmware
  programs these into the chip at boot without waiting for any host packet.
- Network mode 0 = HDSDR (UDP 50002 fixed), mode 1 = wfview (ports 50001/2/3 =
  control / CI-V / audio). The LAN link comes up a few seconds after power.
- **Interface fact:** a clean-room firmware owns the socket/IP configuration; the
  default IP being programmed unconditionally is what makes headless operation
  reachable over LAN.

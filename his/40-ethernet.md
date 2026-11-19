# HIS 40 — Ethernet / LAN

**Evidence:** g7250-base docs (**rests on disassembly**). Emulator observation
(re/emu B2): the stock Main programs the chip's source-IP register through a
W5500-register-compatible model on SPI6 with its chip select on PG15.

- The Main's LAN controller is a **CH394** (W5500-register-compatible) on
  **SPI6**, chip select PG15.
- Network behaviour (addressing, ports, protocols) is defined by the product
  spec, not here.

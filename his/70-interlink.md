# HIS 70 — Main↔Control inter-link (SLIP)

**Evidence:** g7250-emu two-machine SLIP run + g7250-base docs.

- The two MCUs are linked by **SLIP over USART2↔USART2 at 460 800 8N1**
  (Control = client on a 20 ms TIM13 tick; Main = server). RX uses circular DMA.
- SLIP message types seen: 0x01 settings/status block, 0x02 calibration, 0x03
  power-off/TX-status flags. Audio does NOT travel over SLIP (too slow).
- **Interface fact:** a clean-room firmware on either MCU must speak this SLIP
  framing (0xC0 delimiters) to interoperate with a stock peer during bring-up.

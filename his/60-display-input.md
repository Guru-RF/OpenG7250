# HIS 60 — Display and input interface

**Evidence:** g7250-emu Control boot (GUI service loop) + g7250-base docs.

- **LTDC** drives a 1024×600 RGB565 parallel TFT; framebuffers in external
  **SDRAM** (FMC bank 1, 0xC0000000, 32 MiB). **DMA2D** (Chrom-ART) does fills,
  copies and the waterfall scroll. The GUI swaps double buffers on **VSYNC**
  (LTDC CDSR) — a clean-room firmware must honour the VSYNC handshake.
- **GT911** capacitive touch (I²C1, INT PE2/EXTI2, RST PG14).
- **Inputs:** 5×5 key matrix + direct key (TIM14 1 kHz scan), 8 GPIO quadrature
  encoders + the TIM2 main dial, and the **H-22 mic keypad** (ratio-coded serial
  decoded by TIM8 on PI5).

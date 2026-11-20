# HIS 60 — Display and input

**Evidence:** g7250-base control_unit docs (**rests on disassembly**). Emulator
observations (re/emu M2): GT911 detected at 0x14 with INT on PE2; the stock
Control reaches its GUI loop with LTDC and SDRAM mapped. Panel size and the
input wiring are not yet measured on hardware.

- **LTDC** drives a 1024×600 parallel RGB TFT.
- External **SDRAM** on FMC bank 1 at 0xC0000000, 32 MiB.
- **GT911** capacitive touch on I²C1: INT PE2, RST PG14.
- **Inputs:** a 5×5 key matrix plus a direct key; 8 GPIO quadrature encoders
  plus the main dial on TIM2's encoder inputs; the **H-22 mic keypad** on PI5,
  a ratio-coded serial signal (a property of the microphone; levels and bit
  timing not yet measured).

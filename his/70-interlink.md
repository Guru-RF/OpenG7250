# HIS 70 — Main↔Control link

**Evidence:** g7250-base peripherals docs for both units (**rests on
disassembly**): USART2 on PD5/PD6 AF7 on both MCUs (VERIFIED); the wiring
between them over the CTRL cable (HIGH, not traced). Emulator (re/emu, consistency
only): the two-machine run connects the ports by construction; the stock
Control alone, i.e. with a silent Main, runs into its GUI loop with no hang or
fault (2026-11-20); the run does not cover the Control's normal periodic
transmission (the emulator's USART TX-complete flag is not modelled).

- **Main USART2** is wired to **Control USART2** over the CTRL cable; on both
  units USART2 is on **PD5 (TX) / PD6 (RX)**, alternate function 7.

## Idle link (decision 0023: only the Main is replaced)

The Control keeps its factory firmware. New Main firmware:

1. **MUST NOT** transmit on USART2: nothing goes over CTRL that could change or
   damage the Control, until this spec says what is safe.
2. **MUST** keep PD5 at the UART idle level (high) or high-impedance, and
   **MUST NOT** drive it low: a sustained low is a break condition for the
   Control.
3. Needs no answer from the Control: with a silent Main the stock Control keeps
   running without an error state (MEDIUM: firmware analysis gives no link
   timeout at MEDIUM; the emulator run above is incomplete). Panel behaviour
   with a silent Main: to be confirmed on hardware.

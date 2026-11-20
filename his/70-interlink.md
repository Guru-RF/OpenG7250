# HIS 70 — Main↔Control link

**Evidence:** g7250-base peripherals docs (**rests on disassembly**). Emulator
observations (re/emu): the Main and Control USART2 ports, connected in a
two-machine run, carry traffic (D1); the stock Control alone, i.e. with a
silent Main, runs into its GUI loop with no hang or fault (2026-11-20).

- **Main USART2** is wired to **Control USART2** over the CTRL cable; on both
  units USART2 is on PD5 (TX) / PD6 (RX), alternate function 7.

## Idle link (only the Main is replaced)

The Control keeps its factory firmware. New Main firmware:

1. **MUST NOT** transmit on USART2: nothing goes over CTRL that could change or
   damage the Control, until this spec says what is safe.
2. **SHOULD** hold its USART2 TX line (PD5) at the UART idle level (high), so
   the Control does not receive break conditions or noise.
3. Needs no answer from the Control: with a silent Main the stock Control keeps
   running without an error state (emulator observation above).

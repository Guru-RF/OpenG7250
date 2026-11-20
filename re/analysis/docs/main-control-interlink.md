# Main↔Control inter-link (stock protocol)

RE-side record of the stock protocol between the Main and Control MCUs. Moved
out of the HIS at gate review 1 (decision D6, ON8ST, 2026-11-20): the first
product is a headless Main without a stock Control, so new firmware does not
need to speak this protocol. The HIS keeps only the wiring (`his/70-interlink.md`:
Main USART2 ↔ Control USART2 over the CTRL cable).

Full analysis: `docs/protocol.md` in fventuri/g7250-base (snapshot 18c9164),
which this summary follows.

## Physical layer (VERIFIED, firmware analysis)

- Both units use USART2 on PD5 (TX) / PD6 (RX), alternate function 7.
- 460 800 baud, 8N1, no hardware flow control.
- Sources: g7250-base `docs/protocol.md` (Physical layer),
  `main_unit/docs/peripherals.md` and `control_unit/docs/peripherals.md`
  (USART2 rows).

## Transport (VERIFIED / HIGH, firmware analysis)

- Both units receive through a circular DMA buffer (1 KiB on the Main, 4 KiB on
  the Control) and transmit with normal-mode DMA.
- The Control is the client: its link service runs from a 20 ms (50 Hz) TIM13
  tick. The Main is the server and handles the link from its main loop.
- Source: g7250-base `docs/protocol.md` (Transport), `control_unit/docs/peripherals.md`
  (timer table).

## Framing (VERIFIED, firmware analysis)

- SLIP (RFC 1055): frames end with 0xC0; 0xC0 and 0xDB inside a frame are
  escaped as 0xDB 0xDC and 0xDB 0xDD. No leading END byte; empty frames are
  skipped.
- A trailing CRC-16/ARC protects each packet.
- Source: g7250-base `docs/protocol.md` (SLIP framing, packet layout).

## Message types (HIGH, firmware analysis)

| Type | Content |
| --- | --- |
| 0x01 | settings/status block (sent by the Control every 20 ms) |
| 0x02 | calibration |
| 0x03 | power-off and TX-status flags |

Audio does not travel over this link (460 800 baud is too slow for 48 kHz
audio); Main↔Control audio crosses the CTRL cable as analog.

## Emulator observation

re/emu D1: a two-machine run (Main and Control, USART2 connected through a
UART hub) carries 0xC0-delimited frames in both directions
(`re/emu/harness/g7250emu/slip_run.py`, on branch emu/integrate).

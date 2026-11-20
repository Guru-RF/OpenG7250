# USART2 RX shim (Main)

`models/csharp/G7250Usart2RxShim.cs`, used by `harness/g7250emu/fpga_nco_probe.py`
(registered at 0xA0000000, a free bus address; it has only three debug words).

## Why

The Main receives the Control link on USART2 through circular DMA1 Stream 2
into a 1 KiB ring in D2 SRAM, and drains it using the DMA counter (position =
size − NDTR). Renode 1.17's DMA keeps no circular mode and delivers no USART2
RX byte to the stream: in the emulator DMA1 S2 CR read 0x411 (no CIRC) and NDTR
stayed at 0x400. So the Main never applied a settings image sent by a Control
or by the probe.

## From the analysis (g7250-base, used as data)

`docs/protocol.md` "Transport" and `docs/dma.md` (VERIFIED): Main USART2 RX by
DMA1 Stream 2, circular, 1024 B ring; the RX handler is polled from the
superloop and computes the position from the DMA counter, with wraparound.

## What the shim does

It is the UART endpoint for a terminal (`connector Connect sysbus.u2rx <term>`).
For each received byte it writes the byte into the ring at the current position
(ring base read from DMA1 S2 M0AR, size from the first NDTR value) and writes
NDTR = size − position, as a circular DMA counts down and wraps. The Main's own
USART2 still transmits. Not modelled: half/complete-transfer interrupts (unused
for RX by the firmware), overrun and line errors. Bytes that arrive before the
stream is set up are dropped.

## Result (2026-11-20)

With the shim, the stock Main applies every settings image the probe sends
(the 0x01 FPGA frames change step by step). Used for HIS-02; see
`re/analysis/docs/his-02-nco-probe.md` (on the HIS branch).

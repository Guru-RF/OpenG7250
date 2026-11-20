# MDMA model (Main)

> Sources cited as "g7250-base `<path>`" refer to the former data pin
> (historical name; see `docs/REPO_LAYOUT.md`, "Historical names").

`models/csharp/G7250Mdma.cs`, registered at 0x52000000 by `m1_run.py` for every
Main boot (it replaces the earlier `MDMA_NO_MODEL_TODO` tag).

## Why

With the fused FPGA model, RX sample blocks reach the Main's DSP. The DSP clears
and copies buffers with the MDMA and polls for completion. With only a tag at
0x52000000, every poll read 0 and ran into its timeout, so the boot crawled after
the FPGA bus check and never reached the superloop (diagnosed 2026-11-20: PC
held in the tick-wait helper `FUN_0803AD78`, called through `FUN_0803AAA8` from
the MDMA fill helper `FUN_0803AEE8`, read from the stack in the emulator).

## What the firmware does (from the analysis)

g7250-base `docs/dma.md` and `main_unit/docs/memory_map.md` (VERIFIED):
- five channels configured, all with software request, full-transfer trigger,
  packing and a 32-byte buffer length; no MDMA interrupt (the vector is the
  default handler, never enabled); the helpers start a transfer and poll;
- channel 0–2: word-to-word copies, both sides incrementing (RX/TX DSP, the wfview
  TX-audio ring);
- channel 4: fill, fixed source, incrementing word destination (buffer clears);
- the copy helper falls back to a CPU copy when the MDMA is busy and does its own
  D-cache maintenance.

## What the model does

Register layout per ST RM0468 (public): channel x at 0x40 + 0x40·x with CISR,
CIFCR, CESR, CCR, CTCR, CBNDTR, CSAR, CDAR, CBRUR, CLAR, CTBR, CMAR, CMDR; GISR0
at 0x00.

- Writing CCR with EN and SWRQ set performs the whole transfer at once: BNDT
  bytes per block, BRC + 1 blocks, element sizes and increments from CTCR
  (SINC/DINC, SSIZE/DSIZE, SINCOS/DINCOS).
- Then it sets CTCIF, BRTIF, BTIF and TCIF, clears EN and BNDT. CIFCR clears flags.
- Element sizes that differ between source and destination fall back to a
  byte-wise copy.

## Not modelled (assumptions)

Hardware triggers, linked lists (CLAR), repeated-block address updates (CBRUR),
exact packing semantics, transfer timing (the transfer is instantaneous in
virtual time), interrupts and bus errors. None of these is used by the stock Main
according to the analysis; if one is, the model will be wrong there.

# HIS-02: emulator probe of the FPGA 0x01 frame

RE-side record for HIS-02 ("what are the three NCO words in the 0x01 frame").
Only the interface facts go into `his/80-rf-fpga.md`; the stock settings and
VFO detail stay here.

## Method

Tooling on branch emu/integrate (59d5a78, 02fd2b6):
- `re/emu/models/csharp/G7250Gpioe.cs`: the fused GPIOE+FPGA model logs every
  0x01 frame the MCU writes (all bytes after the command latch), and every latch
  of the pulse commands 0x05/0x06/0x09/0x0A.
- `re/emu/harness/g7250emu/fpga_nco_probe.py`: boots the stock Main V1.0.1 with
  that model and plays the Control on USART2 through a socket, sending SLIP 0x01
  settings images (layout from g7250-base `cmd01_fields.csv`, used as data). It
  then changes VFO A, VFO B, the selected VFO, RIT and split in seven steps and
  matches the logged frames against the expected words
  (f × 2³² / 122.88 MHz).

Three runs, 2026-11-20; the last one waited 3300 s host time for the Main to
log anything after its FPGA bus check before starting the steps.

## Result

**The Main does not reach its superloop in the emulator.** In every run the
console ends at the FPGA bus check ("Check complete!"), and no settings image
sent over USART2 is ever applied. So no frame reflects a settings change, and
the roles of the words cannot be told apart from the steps. Most likely cause
(HYPOTHESIS): the boot-time PA bias trim that follows the FPGA init. It has no
iteration cap and waits for the Idd reading (ADC1, PC4) to respond to the bias
DAC (SPI2), which the emulator does not model. The MMIO heatmap is dominated by
GPIOE (the DRDY sample routine) and DWT cycle-counter delays, so the CPU runs
but makes slow or no progress. Follow-up for re/emu: feed ADC1 PC4 from the
existing `models/devices/bias_trim_plant.py` logic.

**What the boot frames show.** During FPGA init the Main writes six identical
0x01 frames (24 bytes) within about 0.2 s, plus the pulse-command latches
(two, consistent with the "off" codes 0x06 and 0x0A that g7250-base reports for
init):

```
C1 | 0ECAAAAB | 1D7AAAAB | 16 04 04 00 00 00 02 00 02 12 | 0ECAAAAB | 03
```

Byte by byte: `C1 0E CA AA AB 1D 7A AA AB 16 04 04 00 00 00 02 00 02 12 0E CA AA AB 03`.

| Bytes | Content | Reading |
| --- | --- | --- |
| 0 | 0xC1 | status flags |
| 1–4 | 0x0ECAAAAB, big-endian | NCO word = 7.100000 MHz |
| 5–8 | 0x1D7AAAAB, big-endian | NCO word = 14.150000 MHz |
| 9–18 | 16 04 04 00 00 00 02 00 02 12 | other fields (per g7250-base: per-rate calibration bytes; meanings unknown) |
| 19–22 | 0x0ECAAAAB, big-endian | NCO word = 7.100000 MHz |
| 23 | 0x03 | most likely the rate index (3 = 48 kS/s per g7250-base) |

- The three NCO words are at byte offsets 1, 5 and 19, big-endian, which matches
  g7250-base ("three big-endian 32-bit NCO words"). This is observed output of
  the stock code, not a model choice: the model only records the bytes.
- At boot, words 1 and 19 are equal and word 5 differs. The values come from the
  Main's own boot-time settings (the emulator's EEPROM model holds erased bytes
  apart from the validity markers), not from the probe; their source was not
  traced.
- RE-side reading, with g7250-base `main_unit/docs/peripherals.md` (TRX+0x208 =
  main VFO plus RIT, TRX+0x204 = other VFO, TRX+0x200 unknown; the words are
  taken from TRX+0x200–0x208): consistent with word 5 being the other VFO and
  words 1 and 19 following the main VFO at boot (HYPOTHESIS: the source of the
  boot values was not traced). Which word carries
  RIT, split or TX cannot be told from equal values.

## For the HIS

Interface facts only, in `his/80-rf-fpga.md`: the frame is 24 bytes; the NCO
words are big-endian at byte offsets 1, 5 and 19; byte 0 holds status flags;
byte 23 most likely the rate index. The roles of the words stay open until the
emulator reaches the superloop or a bus capture on the radio is made.

## Run 4 (2026-11-20, emu/integrate c0ab490 + 1b7a473)

With the MDMA model and the PA bias plant (`re/emu/docs/MDMA-model.md`,
`PA-plant-model.md`), the stock Main now completes its bias trim and reaches its
superloop ("Init Radio Server", IWDG refreshed). The probe then sent the seven
steps, but **the Main still applies none of them**: it receives no byte on
USART2. DMA1 Stream 2 (USART2 RX) stays at NDTR = 0x400 with the CIRC bit absent
in CR (0x411). This is the same Renode 1.17 DMA gap that the metering feed works
around. The frames stay at
`81 1DBAAAAB 1D7AAAAB 16 04 04 00 00 00 02 00 02 12 1DBAAAAB 03` (words 1 and
19 = 14.270000 MHz, word 5 = 14.150000 MHz, from the Main's own boot settings).

So the roles of the three words are still open, and the HIS stays as cleared.
Next step on the emulator side: deliver USART2 RX to the Main (a circular-DMA
shim for DMA1 Stream 2, like the metering feed), then rerun the probe.

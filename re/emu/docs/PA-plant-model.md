# PA bias plant and metering feed (Main)

> Sources cited as "g7250-base `<path>`" refer to the former data pin
> (historical name; see `docs/REPO_LAYOUT.md`, "Historical names").

`models/csharp/G7250PaPlant.cs` with `platforms/g7250_main_pa_plant.repl`,
loaded by `m1_run.py` for every Main boot. It lets the stock boot-time PA bias
trim converge, so the Main reaches its superloop (test A,
`harness/g7250emu/superloop_run.py`).

## Why

After the FPGA bus check the Main trims three PA bias stages in a closed loop:
it raises one stage's bias DAC code step by step and reads the drain current Idd
until it is within 0.1 A of its target. Before this model, Idd always read 0, so
every stage failed after stepping through its whole range (minutes of virtual
time per stage).

## Parts

1. **SPI2 slave (bias DAC).** Decodes the DAC words the Main writes on SPI2 and
   keeps the eight channel codes.
2. **PA plant.** Computes Idd from the bias codes: static current plus, per
   stage, gain × (code − dead zone) above the dead zone. Monotonic and zero
   extra current at code 0 (the shape of `models/devices/bias_trim_plant.py`).
3. **Metering feed.** Stands in for ADC1 and its circular DMA: writes the seven
   scan results into the DMA buffer and pulses the DMA1 Stream 7 interrupt.
   Renode 1.17's DMA model does not keep the CIRC bit (after one transfer NDTR
   is 0 and CR reads 0x2C01 without CIRC), and its ADC returned wrong raw values
   (DR = 2), so the firmware's meters stayed at 0. Both were seen in the
   emulator on 2026-11-20.

## From the analysis (g7250-base, used as data)

| Fact | Source | Tag |
| --- | --- | --- |
| DAC word: 4-bit address (bit-reversed channel) << 2 \| value bits 9..8, then bits 7..0; LD high on PB12 latches; RESET low on PB14 forces all outputs to VrefL | `main_unit/docs/peripherals.md` SPI2; Rohm BU2505FV/BU2506FV datasheet | VERIFIED (format), HIGH (part family) |
| Bias channels: 2 driver, 8 final 1, 7 final 2; value clamped to 10 bit (0x3FF) | `main_unit/docs/peripherals.md` SPI2 | VERIFIED |
| Trim targets: static Idd + 0.5 A (driver), + 0.9 A (each final); tolerance 0.1 A; static Idd must be ≤ 0.1 A | `main_unit/docs/peripherals.md`, `analysis/flow/protections.csv` | VERIFIED |
| ADC1 rank order: INP1 Vext (PA1_C), INP2 forward (PF11), INP3 reflected (PA6), INP4 Idd (PC4), INP5 PA NTC (PB1), INP8 EALC (PC5), INP14 ALC (PA2); 12 bit | `main_unit/docs/peripherals.md` ADC1 | VERIFIED |
| Scales: Idd 0.008059 A/LSB; Vext 0.004835 V/LSB (steady state); NTC raw 2047 = 25 °C | same | VERIFIED |
| DMA1 Stream 7: ADC1, 16/16-bit, circular, into 0x30003740, IRQ 47; the vector filters the buffer before the HAL handler | `docs/dma.md` | VERIFIED |

Decoding checked in the emulator: the first words are channel 2, 8 and 7 at 0
and channel 1 (drive) at 300, as the analysis describes.

## Assumed (HYPOTHESIS, placeholders, not measured)

| Parameter | Value | Note |
| --- | --- | --- |
| Static Idd | 0.05 A | below the 0.1 A boot check |
| Driver dead zone / gain | 450 codes / 0.5 A per 150 codes | target reached near code 600 |
| Final dead zones / gains | 800 codes / 0.9 A per 150 codes | must keep the target below the 10-bit clamp (with 900 the finals saturated at about 0.74 A and failed) |
| Vext | 13.8 V | nominal supply |
| PA temperature | 25 °C | |
| Forward, reflected, EALC, ALC | 0 | no RF |
| Feed rate | 1 kHz virtual time | the real ADC scan rate was not derived |

The plant is shaped for the trim loop to converge, not to predict real bias
codes. Real values need measurements on the radio.

## Result (2026-11-20)

With the MDMA model and this plant, the stock Main trims all three stages
("Success!"), prints "Init Radio Server" and refreshes the IWDG in its
superloop (459 refreshes within 28 s host time). Without the two models the same
test fails (no console mark, no refreshes in 150 s).

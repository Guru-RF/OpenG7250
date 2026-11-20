# HIS 80 — RF front-end / FPGA interface

**Evidence:** signals and command codes from g7250-base peripherals doc
(VERIFIED in the firmware analysis, i.e. **rests on disassembly**). Emulator
(re/emu D2): a fused GPIOE+FPGA model of this bus, built from the same
disassembly, is accepted by the factory image; this is consistency, not hardware
evidence, and the real FPGA version is unknown. The NCO clock and the absolute
sample rate are not measured.

The RF I/Q front end is an **FPGA reached over an 8-bit parallel bus on GPIOE**
(no FMC), driven by the MCU in software.

## Signals
| Signal | Pin | Use |
| --- | --- | --- |
| D0–D7 | PE0–PE7 | bidirectional data; the MCU switches the pin direction |
| CMD | PE8 (with PE9) | pulsed together to latch a command byte |
| STB | PE9 | per-byte strobe |
| DRDY | PE10 | rising edge signals sample data ready; PE10 can raise EXTI10 |

## Commands
| Code | Function |
| --- | --- |
| 0x00 | loopback/test register: a written byte reads back |
| 0x01 | 24-byte config frame: status flags, three big-endian 32-bit NCO words, per-rate calibration, rate index |
| 0x02 | status read (flag bits + three 16-bit values incl. ADC peak) |
| 0x03 | TX I/Q write — two signed 24-bit values per sample |
| 0x04 | RX I/Q read — two signed 24-bit values per sample, 8/4/2/1 per DRDY for rate index 0–3 |
| 0x05/0x06, 0x09/0x0A | exist (two pulse commands); role unknown. **MUST NOT** be sent |
| 0x08 | 3-byte FPGA version read |

## Timing / data
- **NCO:** 32-bit phase words, f × 2³² / f_clk (formula VERIFIED), with
  f_clk = 122.88 MHz (MEDIUM). The FPGA takes a phase word for the first Nyquist
  zone (0 to f_clk/2) plus a spectral-inversion flag in the frame.
- **Sample rate:** rate index 0–3 → 384/192/96/48 kS/s I/Q; DRDY (PE10) at
  ~48 kHz (MEDIUM; absolute rate unmeasured).

## Open

- Strobe polarity and timing, and bus turnaround (who drives D0–D7 when): not
  measured. Bus contention is a hardware risk.
- Byte offsets of the 0x01 frame, and the meaning and safe values of its
  per-rate calibration bytes: unknown.
- The three NCO words: two of them set tuning frequencies of the receive path
  (MEDIUM); the role of the third word and the word order are unknown. Needs a
  bus capture (`90-needs-hardware.md`).

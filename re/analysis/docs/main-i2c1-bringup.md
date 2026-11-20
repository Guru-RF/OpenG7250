# Main-unit I2C1 bring-up

Static analysis of the official G7250 main firmware V1.0.1 (load address
`0x08020000`), 2026-11-19. Prompted by a question from the emulator, where the
stock Main stalls in an I2C1 polling loop. No hardware was tested. Addresses are
MCU addresses; function names are inferred unless they appear in a log string.

## Summary

The early init does not wait for any I2C device. Every I2C call has a finite
timeout derived from the HAL millisecond tick, and every device error is only
logged. A permanent stall in the I2C wait loop therefore means that the tick does
not advance, or that the I2C model never reports either an acknowledge or a NACK.

## Bus and devices

I2C1 (`0x40005400`) is initialised in `0x080218B4` with TIMINGR `0x00D049FB` and
7-bit addressing. All devices below use the same handle at `0x24004F38`.

| Order | Device | 7-bit address | Init function | Confidence |
|---|---|---|---|---|
| 1 | AXP223 power-management IC | `0x34` | `0x0804A8E8` ("[OK] Init PSU") | High: log strings; address matches the X-Powers AXP223 datasheet |
| 2 | 24Cxx EEPROM, 16-bit memory address | `0x50` | `0x0803C08C`, `0x0803C5E4`, `0x0803C448` | High |
| 3 | VersaClock 6 clock generator ("vc6clkgen") | `0x68`, retried at `0x6A` | `0x0804AE68` → `0x0804ABBC` | High: log strings; both addresses are the Renesas 5P49V6 selectable addresses |
| 4 | TLV320AIC3204 codec | `0x18` (initialised data at `0x2400487C`) | `0x0804A65C` | High: log strings; address matches the TI datasheet |

Hardware facts suitable for the hardware-interface spec, after review: the four
devices and their 7-bit addresses on I2C1; an EEPROM of at least 16 KiB (see
below); rails reported by the log strings as DCDC2 1.2 V, DCDC3 1.8 V, DCDC5 2.5 V
and DLDO1 1.8 V. The remaining sections describe stock-firmware behaviour and are
for the emulator only.

## Bring-up order in the main application

The main entry `0x0802239C` runs, in this order: I2C1 init; "System started.";
PH9 driven high; 1000 ms delay; AXP223 configuration; 1000 ms delay; a CRC table
setup (no I2C); EEPROM settings load (three blocks); network defaults; VC6
configuration; AIC3204 configuration.

## The wait loop at 0x0802B14E

The loop belongs to `0x0802B140`, whose structure matches the STM32Cube HAL
routine that waits for `TXIS` with a timeout, with the HAL error check inlined.
It reads I2C1 `ISR` (offset `0x18`), using the STM32H7 bit layout (ST RM0468):

- `TXIS` (bit 1) set: success.
- `NACKF` (bit 4) set: waits for `STOPF` (bit 5), clears the flags and returns an
  error. `BERR`, `ARLO` and `OVR` (bits 8–10) are treated as errors as well.
- Otherwise: checks the timeout and loops.

`ISR = 0x1` (only `TXE`) leaves the routine only through the timeout. The timeout
is computed from the HAL tick at `0x24005A74` (read by `0x080277EC`), which is
incremented only in the SysTick handler `0x08023574` (vector offset `0x3C`), by
the step stored at `0x24000008`. The AXP223 writes pass a 100 ms timeout.

Consequences for the emulator, either of which unblocks the init:

- SysTick must run and its interrupt must be delivered, so the tick advances.
- When no slave answers at an address, the I2C1 model should set `NACKF` and then
  `STOPF`, as real hardware does with automatic end mode.

## Device behaviour during init

**AXP223.** Writes, in order: `0x10`←`0x02`, `0x12`←`0x00`, `0x13`←`0x01`,
`0x21`←`0x11` (DCDC1), `0x22`←`0x1E` (DCDC2), `0x23`←`0x3C` (DCDC3),
`0x25`←`0x1E` (DCDC5), `0x28`←`0x1A` (ALDO1), `0x15`←`0x0B` (DLDO1); after 10 ms,
`0x10`←`0x6E` and `0x12`←`0x08`. Each failure is logged and init continues. It
then reads 256 bytes for a hex dump, trying 7-bit addresses `0x1A`, `0x34` and
`0x0D` in turn. No value is checked.

**EEPROM.** Blocks read at memory addresses `0x0000` (0x1A8 bytes, settings),
`0x0800` (0x166 bytes) and `0x1000` (3 bytes); a block at `0x1800` (0xCA8 bytes) is
read elsewhere (`0x080411D8`). The highest address used, `0x24A8`, implies at
least a 24C128 (16 KiB); this is an inference. Ghidra dropped the timeout argument
from some of these calls in its output.

The settings block is valid when bytes `0x000`, `0x1A3` and `0x1A4` all equal
`'d'` (`0x64`). Backup SRAM at `0x38800000` is checked first; on a mismatch the
EEPROM is read; if that also mismatches, "[ERR] EEPROM Settings data incorrect" is
logged and init continues. Main calls the loader with its force-reset argument
`1`, so an empty EEPROM does not block startup. What happens with the loaded
values afterwards was not fully traced.

**VC6.** Writes a 0x70-byte table from flash `0x0807F840`, starting at register 0,
to `0x68`; on failure it retries once at `0x6A` after 100 ms. It then reads
256 bytes back for a hex dump. No value is checked, and no lock status is polled.

**AIC3204.** Init, deinit and enable failures are logged. Whether anything after
that blocks on the codec was not checked.

## Not established

- The tick step at `0x24000008` and the SysTick reload value, and thus the real
  duration of the timeouts.
- Whether later code depends on AXP223 or AIC3204 state read back during init.
- The physical EEPROM part and any other devices on I2C1 that are not addressed
  during init.

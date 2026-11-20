# G7250 firmware memory map

Static analysis of the supplied V1.0.1 updates, 2026-11-13. Chip families are
identified from firmware/vector layouts; physical part markings and fitted
external-memory capacities have not been read from a radio. KiB and MiB mean
1024 bytes and 1024 KiB respectively.

## Internal flash and image sizes

| Item | Main radio | Control head |
|---|---|---|
| Inferred MCU | STM32H723/H725 family | STM32H743 |
| Internal flash | **1 MiB**, strong inference within the identified family | **2 MiB**, inferred within the H743 family; physical part unverified |
| Application load base | `0x08020000` | `0x08020000` |
| Complete decrypted update | 453,152 bytes / 442.53 KiB | 781,328 bytes / 763.02 KiB |
| Image end, exclusive | `0x0808ea20` | `0x080dec10` |
| Space below application | 128 KiB; main boot vector explicitly referenced | 128 KiB preceding the application |

ST lists 512 KiB/1 MiB flash variants for H723/H725. The main image extends
beyond the 512 KiB boundary at `0x08080000`; its required initialized-data source
also crosses that boundary. Consequently, a supported main unit is strongly
consistent with the 1 MiB variant. The head's initialized-data source at
`0x080dd568` requires the larger bank-1 span of an H743xI. The H743xG's 1 MiB is
split into 512 KiB banks at `0x08000000` and `0x08100000`, leaving a gap above
`0x0807ffff`; it is not a contiguous first MiB. Within the H743 family, this
supports the 2 MiB xI variant. This corrects our earlier assumption that either
density could accommodate the head image; chip markings remain unverified.
See [ST RM0433, flash organization tables](https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf).
The gap after either image is **not established as free patch space**: other
stored data, bootloader policy or reservations could occupy it.

Source capacities: [ST H723](https://www.st.com/en/microcontrollers-microprocessors/stm32h723-733.html),
[ST H725](https://www.st.com/en/microcontrollers-microprocessors/stm32h725ig.html),
[ST H743](https://www.st.com/en/microcontrollers-microprocessors/stm32h743-753.html).
Exact image sizes and hashes: [analysis metadata](../analysis/generated/metadata.json).

## Internal RAM banks

| Bank / base address | Main radio | Control head |
|---|---:|---:|
| AXI SRAM, `0x24000000` | 320 KiB | 512 KiB |
| DTCM, `0x20000000` | 128 KiB | 128 KiB |
| ITCM, `0x00000000` | 64 KiB | 64 KiB |
| D2 SRAM, `0x30000000` | 32 KiB | 288 KiB |
| D3 SRAM, `0x38000000` | 16 KiB | 64 KiB |
| Backup SRAM, `0x38800000` | 4 KiB | 4 KiB |
| Bank sum including backup | **564 KiB** | **1060 KiB**, approximately 1 MiB |

These capacities combine the inferred MCU specifications with the firmware's
memory layout. The main unit's 320 KiB AXI figure already includes the shared
192 KiB pool; adding that pool again would double-count it. ST describes the
H743 as a 1 MB RAM device; the listed banks sum to 1056 KiB plus 4 KiB backup.
These totals exclude CPU caches and external memory, and do not measure free RAM.

The initial stack pointers are `0x24050000` on the main unit and `0x24080000` on
the head, matching the respective AXI-bank upper boundaries. Our Ghidra memory
blocks are analysis mappings, not independent measurements of board capacity.

## Main firmware allocation evidence

Reset `0x08024554` copies 19,544 bytes (`0x4c58`) of initialized data from
`0x0808486c` to AXI RAM, then clears 200,648 bytes of BSS through `0x24035c20`.
That is **220,192 bytes / 215.03 KiB of static AXI data**.

The allocator at `0x08023b88` permits the general heap to grow from `0x24035c20`
to `0x2404fc00`, a maximum range of about **103.97 KiB**. The ceiling is 1 KiB
below the initial stack pointer; this is not a measured stack bound or a claim
that the entire range is currently free. A separate allocator at `0x0803b3c8`
uses a 64 KiB arena starting at DTCM address `0x20000000`.

The main MPU also describes a 1 MiB external window at `0x60000000`. No recovered
SDRAM initialization or convincing memory-device accesses establish that this is
fitted external RAM. A configured MPU window alone is insufficient evidence.

## External nonvolatile storage

The main unit uses I2C EEPROM at 7-bit address `0x50` (HAL shifted address `0xa0`)
with 16-bit memory offsets. Observed records include settings at `0`, calibration
at `0x800`, NV parameters at `0x1000`, and ATU records through `0x24a7`. The
accessed address span is 9,384 bytes; the fitted EEPROM's exact capacity and part
number remain unknown. FPGA-flash strings do not establish a fitted flash size.

The head mounts a W25Qxx-style SPI NOR filesystem and supports an SD card. This
storage is distinct from internal MCU program flash and volatile display RAM.
An SD-card capacity string in the UI is not evidence of a fixed fitted card size.

The head's SPI driver (`0x08036dc0`, switch at `0x08036e38`) detects JEDEC IDs
at runtime: `EF4014` → 1 MiB, `EF4015` → 2 MiB, `EF4017` → 8 MiB, `EF4018` →
16 MiB. The missing `EF4016` case is rejected in the actual jump table; this is
not a claim that every W25Qxx density is supported. The detected capacity is
stored at `0x24000244`, whose startup value is zero, so the image does not reveal
which chip is fitted.

USB mass-storage capacity callback `0x0803dbd4` reports that SPI flash as
`capacity / 512` sectors of 512 bytes. If this mass-storage interface is active,
its physical device capacity can reveal the fitted flash size; filesystem free
space is a different quantity. FatFs registration at `0x08036ec0` assigns SD to
`0:/` and internal SPI storage to `1:/`. The removable SD card's size is queried
dynamically, not fixed by the firmware.

## Head external display RAM

The head configures **32 MiB of external SDRAM** at `0xc0000000`. This follows
from the actual FMC geometry, not only the MPU window: initialization
`0x08020ecc` sets 9 column bits, 13 row bits, 4 banks and a 16-bit bus.
`512 × 8192 × 4 × 2 = 33,554,432 bytes`. The register writer at `0x0803023c`
applies these fields to FMC SDCR1; the MPU independently covers a 32 MiB window.
[ST FMC field definitions](https://github.com/STMicroelectronics/stm32h7xx-hal-driver/blob/master/Inc/stm32h7xx_ll_fmc.h)

This is the firmware's intended configuration, not a chip-marking identification
or a full memory test. Confirmed use includes two display buffers alternating
between `0xc0000000` and `0xc012c000` (`0x080365a0`), with a stride of
1,228,800 bytes, matching 1024 × 600 × 2 bytes. Another configured pool at
`0xc0800000` has size `0x258000` (`0x08039b9c`).

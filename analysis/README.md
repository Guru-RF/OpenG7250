# G7250 firmware analysis

Reference research is credited in [Acknowledgments](../ACKNOWLEDGMENTS.md).
For the owner's authorization to share new findings as upstream issues, and the
code-free reporting workflow, see [shared findings](../docs/fventuri-findings.md).

This repository now has a reproducible static-analysis workflow for the supplied
**2026-11-09 V1.0.1** control and main-unit updates. It decrypts the files and uses
Ghidra to reconstruct C-like pseudocode. It does not execute or flash the radio's
firmware. The generated C is a research aid, not recovered buildable source.

## Run it

Requirements: Python 3 with `cryptography`, an extracted [Ghidra 12.2
distribution](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.2_build),
and Java 25 or newer. This run used OpenJDK 27. Ghidra was downloaded to
`/tmp/g7250-tools/ghidra_12.2_PUBLIC`; that temporary installation will not survive
cleanup or reboot. The official archive SHA-256 was verified as
`2c2cd776db3c1f6a097ba418922378ac3649cadd5e844a6f5f088ae628a7be67`.

From the repository root:

```sh
python3 scripts/prepare_firmware.py
python3 scripts/decompile_firmware.py --ghidra-dir /path/to/ghidra_12.2_PUBLIC
```

Use `--unit main` or `--unit control` to analyze one unit. The per-function
decompiler limit defaults to 10 seconds; `--function-timeout 30` allows longer
attempts. Re-running replaces the generated program and exports for that unit.
Use `--export-only --unit control --function-timeout 30` to retry an export from
an existing saved project without repeating the analysis.
The import setup is specific to these V1.0.1 images: other firmware needs its
startup addresses, RAM copy, and callback tables checked first.

## Outputs

All generated files live under `analysis/generated/`, which is ignored by Git:

- `control.bin`, `main.bin`: decrypted application images, with original padding.
- `metadata.json`: encrypted/decrypted hashes, sizes, core vectors, and load base.
- `control.strings.tsv`, `main.strings.tsv`: printable byte runs, including noise
  from machine code; each has a file offset and runtime address.
- `control/decompiled.c`, `main/decompiled.c`: pseudocode with function addresses.
- Per-unit `functions.tsv`, `decompile_errors.tsv`, `strings.tsv`, and
  `string_xrefs.tsv`: function status and recognized string references.
- Per-unit `export_summary.txt`: completion state and counts. An export can
  finish even when individual functions time out; inspect those counts.
- `projects/g7250_control.gpr` and `projects/g7250_main.gpr`: projects to open in
  Ghidra for assembly, references, data types, and further naming.

The initial function and variable names are mostly generated. Names ending in
`_inferred` are our interpretations, not original debug symbols. String references
can lead to diagnostics, command dispatchers, and hardware drivers. Some indirect
references and function boundaries remain undiscovered or incorrectly inferred.

Verified results on 2026-11-13: **723/723 recognized main-unit functions** and
**1,654/1,656 recognized control-unit functions** produced pseudocode. Control
functions `0x0804dbdc` and `0x080508d0` still timed out with a 30-second limit;
their disassembly remains available in the saved project. Counts describe
Ghidra's discovered functions, not proof of complete code coverage. Original and
decrypted file hashes were checked, and the key startup/controller/network paths
were inspected against their disassembly.

## Platform and entry points

Both images contain little-endian Cortex-M7 Thumb code loaded at `0x08020000`.
The vector layout targets STM32H743 for the controller and STM32H723/H725 for the
main unit; physical packages are unverified. Startup code and repeated service
loops strongly support bare-metal applications. These files do not contain an
identified Linux kernel or root filesystem.
For flash capacities, internal RAM banks, the head's configured 32 MiB SDRAM,
and external storage, see the [memory map](../docs/memory-map.md).

| Unit | Runtime address | Meaning |
|---|---|---|
| Control | `0x080235ac` | Reset handler; copies initialized data and clears BSS |
| Control | `0x08021e74` | Application initialization and main service loop |
| Main | `0x08024554` | Reset handler |
| Main | `0x0802239c` | Application initialization and main service loop |
| Main | `0x08041ef4` | Controller-link service and offline handling |
| Main | `0x080504e8` | Network CI-V command parser/dispatcher |
| Main | `0x0804eb84` | wfview receive-audio capture callback |
| Main | `0x0804ec5c` | wfview transmit-audio consumption callback |
| Main | `0x08021edc` | Hardware shutdown path, inferred from GPIO/power calls |

Addresses in this table have the Thumb flag cleared. Convert a runtime address
to a file offset by subtracting `0x08020000`.

## What the code already tells us

The main startup initializes the audio codec, FPGA, radio parameters, timers,
ADC, and networking, then repeatedly services the radio and watchdog.
It does not wait for a head packet before entering this operational loop. The
supplied application starts at `0x08020000`; the separate bootloader at
`0x08000000` is absent. Consequently, this does not establish whether applying
DC without a head reaches the application.

Controller-link loss clears the built-in PTT, serial CW key, and pending tuner
request flags and marks the controller offline. That branch returns to the
service loop; it does not call shutdown. Its countdown is in service iterations;
we have not established a duration in milliseconds.

The network CI-V PTT path writes the shared CI-V PTT state at `0x24013e47`.
This connects the protocol to native transmit-control state, but does not prove
successful RF transmission or correct audio with the head disconnected.
The network power-command branch around `0x08050a96` logs ON/OFF and sends a
response; that branch does not invoke the hardware shutdown path. A protocol
response alone therefore does not establish working remote power control.

The legacy HDSDR interface exposes receiver IQ and tuning. The separate wfview
interface reaches substantially more controls and DSP receive/transmit audio,
but some of its CI-V commands only echo or cache values. Consult the detailed
[IP coverage](../docs/ip-protocol-coverage.md) before treating a successful
protocol response as an implemented radio function. For power sequencing,
headless startup, and the limits of an application-only patch, see the
[startup analysis](../docs/headless-startup-analysis.md).
The user-supplied browser-control project is assessed separately in the
[open-control comparison](../docs/open-control-comparison.md), including its USB
dependencies and differences from this firmware's legacy packet format.

The control image contains SEGGER emWin and FatFs identifiers. The main image
contains CH394 Ethernet, AIC3204 codec, FPGA-interface, and network audio/control
diagnostics. The FPGA bitstream and separate bootloader are not identified as
separate images in this package, so this analysis does not reconstruct them.

## Interpretation limits

Types, structures, function boundaries, floating-point arguments, callbacks,
and optimized control flow need checking against disassembly. RAM/peripheral
blocks provide address context, not hardware emulation. The controller's external
RAM window follows its MPU configuration; it is not a measurement of fitted RAM.
No hardware tests were performed by these scripts.

The encryption format is AES-256-ECB. The public key is documented in this
[firsthand Xiegu tutorial](https://forum.hamcq.cn/d/6412), and the format is also
implemented in [G90Tools](https://github.com/OpenHamradioFirmware/G90Tools/blob/master/encryption/encryption.py).
For radio specifications and the separate headless-operation research, see
[radio overview](../docs/radio-overview.md).

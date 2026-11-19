# G7250 V1.0.1 IP protocol coverage

Static analysis, 2026-11-13. Scope: the main-unit firmware in the bundled
2026-11-09 V1.0.1 release, decrypted and imported at `0x08020000`. This is
implemented code coverage, not a successful hardware or wfview interoperability
test. Addresses below are main-unit flash addresses; names are inferred unless
they appear in a firmware log string.

The firmware contains **two different LAN services**. Legacy HDSDR supports
receive I/Q and tuning. The `WFV` service implements an Icom-style network server,
CI-V control, receive audio, transmit audio and spectrum frames. WFV contains
substantial radio functionality, but several commands merely remember a value or
echo a request. It is not a complete IC-7300 implementation despite advertising
that model.

## Routing and defaults

`0x0804905c` selects services using byte `0x24013d8e`: value `1` selects WFV;
other values select HDSDR. Changing mode closes the previous sockets and
initializes the new service. Startup `0x0802239c` explicitly sets mode `0`, radio
IP `192.168.3.199`, mask `255.255.255.0`, gateway `192.168.3.1`, and configured
port `50001`. Controller/head packets can replace these settings. This means
merely finding WFV code does not make it the boot default.

The initialized peer-IP value at `0x24004874` is `192.168.3.244`; LAN setup
`0x08048e20` uses it with port 50001. HDSDR discovery subsequently learns and
applies the PC's advertised IP/port, so this initial peer is not a requirement
that every client use `.244`.

| Service | Main-unit listener | Initialization and polling |
|---|---|---|
| HDSDR | UDP **50002**, fixed, socket 0 | `0x0804aed8`, `0x0804af68`, `0x0804b184` |
| WFV | UDP configured port, port+1, port+2; initially **50001/50002/50003** for control/CI-V/audio, sockets 1/2/3 | `0x0804db5c`, `0x0804bc90`, `0x0804de38` |

WFV initialization copies the configured 16-byte username/password fields and
advertises `IC-7300`. Startup initializes these to `g7250` / `beta_tester`;
head configuration may replace them. The control service implements login checks,
connection negotiation, heartbeat and reconnection handling. CI-V processing is
gated on the streaming/session-active flag, set by state callback `0x0804f604`
when state becomes `6`. Sending a raw CI-V frame directly to a UDP port without
the network session framing is therefore insufficient.

## Legacy HDSDR / bundled ExtIO

Every application datagram begins `AA 55 55 AA`, followed by two command bytes.
The CH394 driver's eight-byte source-IP/port/length prefix is internal metadata,
not part of the UDP payload.

| Wire bytes | Direction | Payload size | Effect |
|---|---|---:|---|
| `01 01` | PC → radio | 12 | Discovery/start: advertised IPv4 at offset 6 and big-endian receive port at offset 10; zero IP selects sender IP. |
| `01 02` | PC → radio | ≥6 | Heartbeat from the learned client; session times out after 10 seconds. |
| `01 03` | PC → radio | 14 | Tune current VFO via `0x0803ebb0`. Big-endian 64-bit Hz at offset 6, although only the lower 32 bits are used; accepts 500,000–108,000,000 Hz. |
| `02 01` | Radio → PC | 16 | Discovery response: IPv4, port 50002 and identifier `G725`. |
| `02 02` | Radio → PC | 774 | Six-byte header plus 192 interleaved pairs of signed 16-bit little-endian I/Q samples. |

These are the complete command branches in `0x0804af68`. There is no legacy
HDSDR handler for transmit audio, PTT, mode, ATU, gains or power. The PC derives
its spectrum from I/Q rather than receiving a separate scope protocol.

The bundled `ExtIO_G7250.dll` confirms 48,000 samples/s (`GetHWSR`, VA
`0x10002960`), a preferred PC receive port of 50001 with an ephemeral fallback,
and discovery broadcast to 50002. Its LO setter caps requests at **54 MHz**
(`0x10002851`), narrower than the firmware's accepted range. I/Q packing is in
the main DSP routine `0x08033610`, around `0x08033718`, using buffers
`0x38001000` and `0x38001300`. Sample polarity/order has not been calibrated on
hardware.

## WFV CI-V command coverage

Dispatcher: `0x080504e8`. Frames have the form
`FE FE destination source command [parameters] FD`; destination `A0` or broadcast
`00` is accepted. Replies use source `A0`. Frequency fields are five-byte,
least-significant-pair-first packed BCD. Many setters reply by echoing their
command body through `0x0804f534`, **including ignored or cached-only settings**.
An echo does not prove that hardware changed.

All opcodes in the following tables are **raw hexadecimal wire bytes**.
Assembly at `0x08050588` loads the opcode, subtracts `7` into the jump-table
index, and branches separately for opcodes below `7`. Thus decompiler outer
`case 0x15` means wire opcode `1C`, not `15`. The nested `16` function switch
similarly subtracts `22` from the subcommand. These normalizations were checked
against the binary and assembly.

| Command | Read behavior | Write behavior / limitation |
|---|---|---|
| `00` | None | Five-byte BCD sets **VFO A**, 500 kHz–108 MHz. It does not follow the active-VFO selector. |
| `01` | Returns cached mode | Writes ignored. |
| `03` | Returns cached active A/B frequency | Writes ignored. |
| `04` | Returns cached mode/filter | Writes ignored. |
| `05` | Returns actual active-VFO number | **Nonstandard:** parameter 0/1 selects VFO using `0x0804f148`; this branch is not a frequency setter. |
| `06` | No getter here | Updates active mode; remembers optional filter (defaults to 1). This branch does not itself apply the filter preset helper. |
| `07 00/01` | — | Select A/B; helper refuses a switch during several transmit/keying states. |
| `07 A0/B0/B1` | — | A→B copy / A↔B swap / active→other copy, including frequency and mode. Unknown subcommands are logged as ignored and echoed. |
| `0C` | Cached five-byte offset | Cache only (`0x2402a220`); no tuning effect found. |
| `0F` | Actual split state | `00`, `01`, `10` accepted; only `01` enables split. Other duplex modes are ignored but still return success. |
| `11` | Actual attenuator state, 00/20 | Sets active-VFO attenuation boolean; any nonzero byte enables. |
| `12` | Cached antenna and RX-antenna flag | Antenna selection changes actual boolean `0x24013cab` and calls `0x08044ea4`; separate RX-antenna flag is cache only. |
| `14 ss` | Level values, mostly cached | See level table below. |
| `15 ss` | Meter data | Read only; see meter table below. |
| `16 ss` | Function values, mostly cached | See function table below. |
| `18 00/01` | — | **Power is log-and-echo only.** No standby, shutdown, or wake action. Branch `0x08050a96`. |
| `19 00` | Device ID `A0` | — |
| `1A ss` | Extended settings | Handler `0x0804fdcc`; details below. |
| `1B 00/01/02` | Cached tone / tone-squelch / DTCS bytes | Three-byte values stored only in WFV cache. No actual tone encoder/decoder change found. |
| `1C 00` | Cached network PTT request | Writes real `TRX_ptt_civ` byte `0x24013e47`; consumed by the main transmit state logic. |
| `1C 01` | ATU busy=2, otherwise cached state | 2 starts real ATU tuning (`0x240176e9=1`, `0x08044d38(0)`); 0 bypasses, other nonzero values enable ATU. |
| `21 00/01` | Cached RIT offset / enable | Sets actual signed RIT offset or enable and calls `0x0803d658` as appropriate. No XIT subcommand found. |
| `25 00/01` | Cached A/B frequency | Sets actual A/B frequency, with 500 kHz–108 MHz validation. Selector is absolute A/B in this code. |
| `26 00/01` | Same cached mode/data/filter for either selector | Accepts both selectors but applies mode/data/filter to the **currently active** VFO; no independent B-mode state in this handler. Filter preset helper `0x0804ef6c` is called. |
| `27 ss` | Scope settings | Handler `0x0804f774`; details below. |
| `29 selector inner-command…` | Depends on inner command | Strips two bytes and redispatches; selector is not applied to a second receiver. |

Other outer opcodes take the ignore path. In particular, this dispatcher has no
CW-text/keyer-message command handler. Supported operation still depends on the
radio's normal band/mode/TX-enable checks; writing the PTT request is not proof of
RF output.

### Level commands (`14`)

Get: `14 ss`; set: `14 ss hundreds tens/units` representing 0–255 in two-byte
BCD. Invalid encodings are not comprehensively validated. Writes generally echo.

| Subcommand | Actual effect |
|---|---|
| `01` AF | Scales WFV receive-audio capture gain 0–1 at `0x24004a8c`; not the head's speaker volume. |
| `02` RF gain | Actual RF gain 0–100. |
| `03` squelch | Actual active-mode threshold and squelch enable; FM and other modes use different mappings. |
| `06` NR level | Actual DNR setting 0–100. |
| `07`, `08` | Cache only; no IF-shift/filter change found. |
| `09` CW pitch | Actual 300–900 Hz. |
| `0A` RF power | Actual requested power 5–100 W; invokes mode-dependent power helper `0x0803d3b0`. |
| `0B` mic gain | Actual 0–30; calls `0x0804a790`. |
| `0C` key speed | Actual 6–48 WPM. |
| `0E` compression | Actual four-level setting 0–3. |
| `0F` break-in delay | Actual 0–13 dot units. |
| `12` NB level | Actual 1–20. |
| `15` monitor | Actual 0–100. |
| `16` VOX threshold | Actual −100–0 dBFS. |
| `17` anti-VOX | Cache only. |

Unknown level getters return zero; unknown setters may still echo. Readback
usually reflects the WFV cache initialized by `0x0804f1ec`, not a fresh read of
every live setting.

### Function commands (`16`)

Get `16 ss`, set `16 ss value`.

| Subcommand | Effect |
|---|---|
| `02` preamp | Actual active-VFO preamp byte. |
| `22` NB | Actual global NB enable. |
| `40` NR | Actual active-VFO NR enable. |
| `41` auto-notch | Actual active-VFO ANF and filter-update flag. |
| `42` tone, `43` tone squelch | Cache only. |
| `44` compressor | Actual enable. |
| `45` monitor | Actual level set to cached monitor value, or zero when disabled. |
| `46` VOX | Actual enable. |
| `47` break-in | Actual boolean; distinct nonzero break-in modes collapse to one. |
| `5D` repeater access | Cache only. |

Unknown function getters return zero; unsupported writes can still echo.

### Meter commands (`15`)

`02` reads signal strength from `0x24017f00`; `11` reads forward power
(`0x24017f04`); `12` reads SWR (`0x24017f08`); `13` reads the ALC-style value
at `0x24017f14`; `15` reads supply voltage (`0x24017f0c`); `16` reads current
(`0x24017f10`). Firmware maps these to Icom-style 0–255 BCD meter values with
linear/piecewise conversion. Subcommand `04` returns **constant 128**. Other
meter requests return zero. Meter names other than the explicitly logged
settings are inferred from data sources and scaling, not hardware calibration.

### Extended commands (`1A`)

| Subcommand | Effect |
|---|---|
| `01 band register` | Reads/writes 12 cached band-stacking entries at `0x24004a28`; the register-selector byte is echoed but not used to select separate stacks. No immediate tuning or persistence is established. |
| `03` filter width | Reads/writes calculated bandwidth in a WFV cache table. A write does **not** call the real filter-application function. |
| `04` AGC | Actual active-VFO AGC enable/speed mapping. |
| `05 00 66` modulation input | Read/write cached input, also sets `0x2402a264`; **value 3 enables network TX audio consumption**. |
| `05 00 67` data-mode modulation input | Cache only; does not set the TX-consumer selector. |
| `06` data mode + filter | Actual mode conversion and filter preset application via `0x0804ef6c`. |

The filter preset helper uses fixed firmware tables to change real DSP filter
parameters. Custom widths stored through `1A 03` are not what that helper reads.
Unknown extended settings may merely echo, so returned bytes alone are weak
evidence of support.

### Scope commands (`27`)

| Subcommand | Effect |
|---|---|
| `10` display | Cached flag only; does not gate spectrum sending. |
| `11` data output | Actual spectrum-stream enable/disable (`0x2402fa54`). |
| `14 00 mode` | `FF` disables output; every other mode becomes mode 0 and enables output. Not independent implementations of all scope modes. |
| `15 receiver span` | Five-byte BCD span; changes actual main sample-rate selection: ≤48 kHz→3, ≤96 kHz→2, ≤192 kHz→1, otherwise→0. Reloads DSP/FFT and pauses scope sending for 500 ms. |
| `16` edge selection | Cached only. |
| `19 00` reference level | Cached signed value only; no spectrum adjustment found. |

`0x08052b78` sends up to roughly 20 frames/s when streaming and enabled, with
512 waveform bytes from `0x24017d00`. It supplies cached active frequency,
cached mode and half the configured span to encoder `0x0804d800`. Thus a received
spectrum frame is real, while several presentation controls remain partial.

## Audio, PTT and remaining verification

The network layer explicitly accepts mono **LPCM16 (`04`) or LPCM8 (`02`)** and
negotiates 16 or 48 kHz. Other codec values are parsed but produce an unsupported
codec warning; this is not evidence of working Opus/other compressed audio.

Receive path: DSP callback `0x0804eb84` captures audio into an 8192-sample ring;
`0x0804edf0` supplies 20 ms frames, including decimation from 48 to 16 kHz.
Transmit path: `0x0804f094` accepts decoded PCM, interpolates 16 kHz to 48 kHz,
and queues it via `0x0804ea5c` into the 2048-sample ring at `0x2402a2b8`.
DSP callback `0x0804ec5c` drains that ring into float audio only while the session
is active **and modulation input is 3**. Initialization `0x08052930` registers
both DSP callbacks via `0x0803331c` / `0x08033328`. This establishes an actual
TX audio path, not just unused packet parsing. RF transmission itself has not
been tested.

Session-close callback `0x0804f604` (states 0 and 7) resets stream and buffer
state but does **not** clear the separate `TRX_ptt_civ` request at `0x24013e47`.
The periodic transmit logic at `0x08037c10` continues to include that request
without checking the network-session flag. No network-loss timeout clearing this
request was found in the recovered write paths. The TX DSP routine at
`0x08034b88` also falls back to codec-derived samples when the network audio
callback returns zero, as it does for an inactive session. These are static
findings, not an observed RF incident, but they identify a concrete requirement
for a headless TX patch: release network PTT on disconnect/heartbeat expiry and
verify the audio-source behavior when a session is lost.

The normal radio logic can clear CI-V PTT on TX-inhibit/CW conditions. A changed
packed PTT/key/tune byte from the head can also overwrite it; an unchanged head
packet does not overwrite it on every iteration. Other settings, such as RF gain,
can be restored to the head's value by subsequent head packets. Many readbacks
and scope-center values use a cache synchronized at session activation/first
CI-V dispatch; continuous synchronization after independent head changes is not
established. Simultaneous head/PC control therefore needs separate verification.

The earlier receive/tuning demonstration with the powered-up head unplugged is
documented in [radio-overview.md](radio-overview.md). These code paths strengthen
the case for substantial LAN control, but do not establish headless cold boot,
remote power-on, or complete feature parity with the head.

For comparison with the user-supplied browser/USB-CAT project, see
[open-control-comparison.md](open-control-comparison.md). Its legacy LAN framing
differs from this bundle, and its serial CI-V profile cannot be applied unchanged
to the network dispatcher above.

## Reproduction sources

- Firmware inputs and release notes: [V1.0.1 bundle](../firmware/2026-11-09_Xiegu_G7250_V1.0.1/).
- [Generated main decompilation](../analysis/generated/main/decompiled.c),
  [function inventory](../analysis/generated/main/functions.tsv), and
  [decryption metadata](../analysis/generated/metadata.json).
- Raw main image: `analysis/generated/main.bin`, base `0x08020000`. Confirmed
  command jump table is at `0x080505a0`; unsupported entries point to
  `0x0805056c`. Key branch addresses: `14`→`0x08050c74`, `16`→`0x08050b10`,
  `18`→`0x08050a96`, `1C`→`0x080509b6`, `25`→`0x0805085e`.
- Bundled `ExtIO_G7250.dll`: x86 addresses above use its PE image base
  `0x10000000`. Decompiler argument counts and function-pointer references need
  assembly confirmation; no firmware was modified or executed for this report.

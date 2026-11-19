# Open questions for the hardware-interface spec (HIS)

Questions that only the hardware-interface spec (`g7250-his`) can answer. This repository
does not look for the answers itself (AGENTS.md rules 1 and 7). Each question says why we
need it, which decision or milestone waits for it, and what public sources already say.

Hardware observations by ON8ST are noted where he gave them. They count as provisional until
the HIS confirms them.

Priority: **M1** = needed for milestone M1 (discovery, capability block, RX-IQ);
**M2–M5** = needed for that milestone; **G6** = needed for the level-2 feasibility gate.

## Receiver and sampling

### HIS-01 — ADC and sample clock (M1)

- Question: which ADC is used, at what sample clock, and which decimated IQ sample rates can
  the main unit produce?
- Why: P2 DDC sample rates are 48/96/192/384/768/1536 ksps [P2]. The network side limits
  realistic rates to 384 ksps or lower (`analysis/ch394-network-budget.md`). Decision 0004
  (streams and sample rates) needs the hardware side.
- Known: "RF direct sampling" [G7250-MAN]. No ADC type or rate is published.
- Added by 0006: can the ADC chain give a peak magnitude per period (for P2 ADC max
  magnitude)?

### HIS-02 — Number of receivers (M1)

- Question: how many independent receive channels (DDCs) can the main unit run at the same
  time?
- Why: P2 reports the number of DDCs in the discovery reply [P2]. Each DDC adds one I&Q
  socket and its bandwidth (`analysis/ch394-network-budget.md`).
- Known: "one receiver" comes from the start brief (0001) and is not stated in
  [G7250-MAN].

### HIS-03 — Second ADC or TX feedback path (M4)

- Question: is there a second ADC, or a path that feeds the transmitted signal back to the
  receiver?
- Why: only then are P2 features such as synchronous DDCs and PureSignal of any use
  (`analysis/p1-vs-p2.md`).

### HIS-04 — DSP clock and frequency word (M1)

- Question: what is the DSP clock from which receive and transmit frequencies are derived,
  and can the hardware take a frequency in Hz or does it need a phase word?
- Why: P2 lets the radio declare "frequency or phase word" and its DSP clock in the
  discovery reply [P2].

### HIS-05 — Frequency reference (M2)

- Question: what is the reference oscillator, and can it be calibrated or locked to an
  external reference?
- Why: P2 has a "10 MHz reference PLL locked" status bit and reference-source settings [P2].
- Known: ±1.5 ppm 10 minutes after power-on, 1 ppm/hour at 25 °C [G7250-MAN].

## RF control

### HIS-06 — Antenna switching (M2)

- Question: how are ANT1 and ANT2 selected, and what is the state after power-on and after
  a fault?
- Why: G7250 register map (0005); safe receive default state for a host that has not armed
  TX (0015).
- Known: ANT1 and ANT2 on the main unit, selectable in the menu "ANT SELECT"
  [G7250-MAN].

### HIS-07 — Filter switching and front end (M2)

- Question: which band-pass and low-pass filters, preamplifier and attenuator exist, how are
  they switched, and what does the main unit do automatically per frequency?
- Why: G7250 register map (0005); which standard P2 fields (step attenuator, Alex words)
  might fit with identical meaning (0005); safe RX default (0015).

### HIS-08 — Internal ATU (M2)

- Question: how is the internal tuner switched in and out, how is tuning started, what does
  it report (busy, success, failure, SWR), and where is the per-band tuning data stored?
- Why: G7250 register map (0005); interaction with TX arm and PTT (0015, 0007).
- Known: 20–150 Ω, initial tuning ≤ 10 s, memory recall ≤ 0.1 s, data stored per band;
  after tuning the radio "automatically returns to receive status", so tuning transmits
  [G7250-MAN].

### HIS-09 — External interfaces on the main unit (M2)

- Question: can the firmware control or read the TUNER (13.8 V out, return, trigger), SEND
  (transmit control) and ALC (output) interfaces, and how?
- Why: candidates for the G7250 register map (0005) and the safety core (0007): SEND keys
  external equipment, so it belongs under the TX arm.
- Known: these connectors and their pins [G7250-MAN].

## Transmit and safety
- Added by 0007: is SEND an output only (keying external equipment) or also an input?

### HIS-10 — PTT and TX interlock (M3, M4)

- Question: where do PTT and the TX interlock sit in hardware, which sources can key the
  transmitter (network, controller microphone PTT, KEY input, SEND), and can the firmware
  block each of them?
- Why: TX arm (0015), watchdog and safety (0007), single owner (0011). The arm only works if
  the firmware is the only path to the PA, or can block every other path.
- Added by 0007: can the controller key the PA on its own, without the main-unit firmware?

### HIS-11 — Sensors (M2, M3)

- Question: which sensors exist and how are they read: forward and reflected power, SWR,
  PA temperature, supply voltage and current, PA current? With what resolution and update
  rate?
- Why: P2 High Priority status carries forward/reverse power and supply voltage, sent every
  1 ms during TX [P2]; telemetry (0006) and SWR/temperature limits (0007).
- Known: supply 13.8 V ±15 %, TX current ≤ 23 A [G7250-MAN].
- Added by 0006: where does the power coupler sit relative to the ATU; is there a separate
  exciter detector; does per-unit calibration data exist in the radio, and where; what is the
  fastest rate at which each sensor can be read?
- Added by 0007: what plausibility check is possible per sensor (to detect a failed sensor)?

### HIS-12 — Power control and limits (M4)

- Question: how is output power set (drive level, PA bias), what are the limits per band and
  per mode, and is there a hardware power or SWR fold-back?
- Why: P2 drive level 0–255 [P2]; limits in the safety core (0011, 0007).
- Known: SSB/CW/NFM 100 W, AM 25 W [G7250-MAN]; 50 MHz power not stated in the manual.

### HIS-13 — Fault and reset behaviour (M3)

- Question: what does the hardware do on a processor reset, brown-out or watchdog reset:
  does the PA drop out by itself, and in which state do relays and switches come up?
- Why: safe state after reset or fault (0001 spec section 9, 0007).

## Network
- Added by 0008: can the firmware read the cause of the last reset?

### HIS-14 — Ethernet controller and its connection (M1)

- Question: please confirm the WCH CH394Q. Which interface connects it to the processor
  (SPI), at what clock, and does the existing design use the chip's sockets or MACRAW mode?
- Why: the SPI clock caps all network throughput (at most 62 MHz [CH394]); the socket mode
  decides the 8-socket budget (`analysis/ch394-network-budget.md`, 0016, 0017).
- Known: LAN port on the main unit [G7250-MAN]; ON8ST saw a CH394Q during his own hardware
  inspection (2026-11-19).
- Added by 0007: does the CH394Q report link status (cable unplugged) to the processor?
- Added by 0008: is a DHCP client present in the current design? (The CH394 has none built
  in, per 0008.)

### HIS-15 — MAC address (M1)

- Question: where is the MAC address stored, and is it unique per unit?
- Why: the P2 discovery reply carries the MAC address [P2].
- Added by 0008: is there a unique serial number besides the MAC address?

### HIS-16 — Public sources on the network interface (M1)

- Question: which public sources document the network interface of the G7250? ON8ST
  mentions a video by the YouTube channel "Temporarily Offline", and [G7250-MAN] refers to a
  "G7250 HDSDR Network Reception Tutorial". Links, please.
- Why: to cite them in `sources.md` ([G7250-TOFF]).

## Main unit and controller

### HIS-17 — The CTRL link (M2, M4)

- Question: what does the 15-pin CTRL cable between main unit and controller carry? In
  particular: can the main unit send audio to the controller's speaker, and can it receive
  microphone audio, PTT and Morse key from the controller? What happens on the main unit when
  the controller is disconnected?
- Why: P2 microphone data (port 1026) for TX from the host, a possible audio path later
  (0017), PTT sources (HIS-10), and whether the firmware must keep the controller working.
- Known: speaker, microphone, key, USB and Bluetooth are all on the controller; the main unit
  has no audio connector [G7250-MAN], (ON8ST, 0017).

## Compute and firmware
- Added by 0008: can the main unit read the controller's TF card or USB, show a confirmation
  on the controller's screen, or receive a button press from it (first-secret set-up,
  physical-presence confirmation, local factory reset)? Does the controller's NETWORK page
  write the main unit's network settings?

### HIS-18 — Processor, memory and logic (G6, M1)

- Question: which processor(s), DSP or FPGA are in the main unit, at what clock, with how
  much RAM and flash?
- Why: P2 is the heavier protocol (several ports, 24-bit TX IQ at 192 ksps [P2]); the
  WebSocket layer and TCI commands for level 2 run on the processor, not in the CH394Q
  (`analysis/ch394-network-budget.md`); gate G6 (0011).
- Added by 0008: flash size and layout (room for two images, or one plus staging), RAM for a
  log buffer, and whether an FPGA image is loaded by the main-unit firmware.

### HIS-19 — Firmware loading and recovery (M5)

- Question: how is firmware loaded into the main unit, is there a boot loader that survives
  a failed update, and can an update be done over the network?
- Why: firmware update over the management channel (0001 spec section 10, 0008); P2 also has
  program packets on port 1024 [P2].
- Added by 0008: can the boot choice be switched atomically, and can the boot loader detect
  an unconfirmed trial boot?

### HIS-20 — Source of randomness (M5)

- Question: is there a hardware random-number generator or an equivalent entropy source?
- Why: challenges for the management channel (0008) and the per-session TX arm token (0007).

## Sources

- [P2], [CH394], [G7250-MAN] and the other keys: see `sources.md`.
- Decisions 0001, 0004–0008 (reserved where not yet written), 0011, 0015, 0016, 0017.
- `analysis/p1-vs-p2.md`, `analysis/ch394-network-budget.md`.

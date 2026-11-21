# 0006 — Telemetry: standard High Priority status where the meaning fits, G7250 telemetry in the register map

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19

## Context

Telemetry is what the radio reports to the host about its own state: power levels, supply,
sensor values, inputs and the state of the safety core. Milestone M2 needs it ("forward/
reflected power, temperature, supply ... telemetry at the specified rates", design note §6),
and the safety core (0011, 0007) needs the same values to enforce its limits.

### What standard P2 offers

The **High Priority Status packet** (hardware to PC, default port 1025) [P2, pp. 47–50]:

- Timing: "Data representing inputs is sent immediately the data changes, other data is sent
  periodically. The normal periodic update rate is every 50mS. This is increased to every mS
  when transmitting in order that the host receives Forward and Reflected Power levels fast
  enough to display SWR with low latency." Status changes are sent "as a priority". The
  format "will vary between different SDR hardware".
- Fields (byte numbers as in [P2]):

| Bytes | Field | Note in [P2] |
|-------|-------|--------------|
| 0–3 | sequence number | per port, reset at power-on and on stop |
| 4 | bit [0] PTT, [1] dot, [2] dash, [4] PLL locked, [5] FIFO almost empty, [6] FIFO almost full | bits [0]–[2]: "attached PTT button or CW key"; [4]: PLL that locks the master VCXO to the 10 MHz reference; [5], [6]: "no longer supported" |
| 5 | ADC overload, bit [n] = ADC n | |
| 6–7 | Exciter Power 0 | forward power from the exciter (Penelope/Penny Lane); Appendix A |
| 8–13 | Exciter Power 1–3 | reserved |
| 14–15 | Forward Power – Alex 0 | forward power from the PA; "Set to zero if Alex not selected"; Appendix A |
| 16–21 | Forward Power – Alex 1–3 | reserved |
| 22–23 | Reverse Power – Alex 0 | reverse power from the PA; same note; Appendix A |
| 24–29 | Reverse Power – Alex 1–3 | reserved |
| 30 | FIFO overflow/underflow bits [3:0]: DDC, Mic, DUC, speaker | "G2 specific" |
| 31–38 | DDC, Mic, DUC, Speaker FIFO depth (samples) | "if the FIFOs are present in the firmware" |
| 39–42 | ADC0, ADC1 max magnitude in this message period | unsigned, up to about 32768 on overload |
| 43–48 | 0 | "Presently unused" |
| 49–50 | Supply Volts | Appendix A |
| 51–58 | User ADC3 … ADC0 | "presently undefined since they are user specific" |
| 59 | User logic inputs | IO mapping as listed in [P2] |

**Scales: Appendix A.** P2 sends power and supply as raw 16-bit ADC words. The host converts
them with per-board constants listed in Appendix A [P2, pp. 62–70], for example:

- Hermes (board 1): supply `V = ADC/4095 × 3.3`; power `W = (ADC/4095 × c1)² / c2` with
  c1 = 3.3, c2 = 0.09 (ANAN-10, 0–20 W) or 0.095 (ANAN-100, 0–150 W); exciter scaled
  0–1000 mW.
- Orion (board 4): supply constant 5.0; power c1 = 5.0, c2 = 0.108 (ANAN-100, 0–150 W).

The constants exist only per board type, in the document. The full hardware description
(board type 255, Appendix C) has no field for them: it ends at byte 96, "Number of General
Purpose ADCs", and bytes 97–1439 are "For future use" [P2, pp. 72–78]. Board type 200 (0002)
has no Appendix A entry.

**Memory-mapped registers from hardware** [P2, "Memory mapped registers from hardware"]:
pairs of a 16-bit address and a 32-bit data word, "sent whenever data changes and optionally
periodically". 0005 puts every G7250 function and all TX-safety state there.

### What the G7250 has, from public sources

- The controller shows "the voltage input to the radio power port", an SWR meter and a Po
  (transmit power) meter [G7250-MAN, display areas 6, 14, 15, p. 16]. So supply voltage,
  forward and reflected power are measured somewhere in the radio. Where (main unit or
  controller), how, and with what resolution is not public (HIS-11).
- Supply 13.8 V DC ±15 %, TX current ≤ 23 A, operating temperature 0 to +50 °C, 100 W
  SSB/CW/NFM, 25 W AM [G7250-MAN, p. 47].
- Internal ATU; tuning transmits and "automatically returns to receive status"; a failed
  tune shows as a high SWR on the meter [G7250-MAN, pp. 21–22]. What the ATU reports to the
  processor is not public (HIS-08).
- No sensor list, no PA temperature or PA current sensor, no reference PLL is published
  (HIS-05, HIS-11).

### Network budget

From `analysis/ch394-network-budget.md` and [P2]:

- The High Priority status payload is 60 bytes (bytes 0–59). With 8 bytes UDP and 20 bytes
  IPv4 header that is 88 bytes per packet over SPI, and 126 bytes on the wire including
  Ethernet header, FCS, preamble and inter-frame gap. At 1 packet/ms during TX: about
  0.70 Mbit/s over SPI (about 1.1 % of the 62 Mbit/s SPI ceiling [CH394]) and about
  1.0 Mbit/s on the 100 Mbit/s link. At 50 ms: negligible.
- A memory-mapped packet with n pairs is 4 + 6n bytes [P2]. A 16-register snapshot is
  100 bytes payload.
- Bandwidth is not the constraint. Packet rate may be: during TX the radio already handles
  TX IQ in (192 ksps / 240 samples per packet [P2, Appendix A, board 2] = 800 packets/s) and
  RX IQ out (at 384 ksps and 238 samples per packet [P2, Appendix A, board 1], about 1,600
  packets/s; the G7250 values are set in 0004). 1 ms status adds 1,000 packets/s. The SPI
  command overhead per packet is not in the part of [CH394] that was read, and the processor
  cost per packet depends on HIS-14 and HIS-18.
- Telemetry registers share the register-map socket (0005). No extra socket is needed.

## Options considered

### 1. Where G7250 telemetry goes

#### 1A. Standard High Priority fields where the meaning is identical; everything else in the G7250 register map (chosen)

Same rule as 0005, applied to the hardware-to-PC direction.

- For: a P2 host that knows board type 200 reads power, SWR inputs and supply where it
  already reads them for every other P2 board, at the 1 ms TX rate P2 defines for exactly
  this purpose [P2, p. 47].
- For: G7250-only values (temperature, PA current, ATU, arm, faults) get a defined meaning
  and unit in our own map, with no risk of collision with later P2 revisions (0005).
- For: no new port, no new socket.
- Against: telemetry is split over two packet types on two ports, which are not
  synchronised. A host that wants SWR and the safety-core state at the same instant cannot
  get them from one packet.

#### 1B. Everything G7250-only in the User ADC fields (bytes 51–58) and user inputs (byte 59)

- For: everything in one packet at the 1 ms TX rate.
- Against: [P2] calls these fields "presently undefined since they are user specific". There
  is no meaning to be identical to (0005 rule 1); a generic host may display them with any
  label or scale.
- Against: only four 16-bit words and 8 bits: not enough for temperature, PA current, SWR,
  ATU, arm, fault and limit state.

#### 1C. Everything in the G7250 register map, standard status fields all 0

- For: one place, one unit convention, our own rates.
- Against: throws away the one telemetry mechanism P2 defines for TX power and SWR, which was
  a main reason for choosing P2 (0016).
- Against: every host needs G7250-specific code just to show a power meter.

#### 1D. Reserved status bytes (8–13, 16–21, 24–29, 43–48)

- Against: rejected by 0005 rule 3. Reserved bytes have gained meanings in later revisions
  [P2, revision history].

### 2. Units and scales in the standard fields

#### 2A. Raw ADC counts, with the unit's own constants in Appendix A form (chosen, ON8ST, 2026-11-19; includes 2D)

The firmware copies the sensor ADC reading into the field, as [P2] does. The capability block
(0003) gives the constants for `V = x/4095 × c` and `W = (x/4095 × c1)² / c2` [P2,
Appendix A]. As in 2D, the constants are those of this unit (per-unit calibration), and per
band if the hardware needs it (HIS-11), not fixed constants for board type 200.

- For: exactly what [P2] does for every listed board; the field keeps its P2 meaning (raw ADC
  word), so no deviation has to be listed for the encoding.
- For: per-unit calibration (and per-band correction, if needed) can be expressed, because
  the constants come from the radio at connect time, not from a table in the document.
- For: raw readings are available to the host for calibration and debugging without extra
  registers.
- Against: the Appendix A formula assumes a 12-bit linear ADC with a square-law power
  relation. The G7250 sensor chain is unknown (HIS-11); if it does not fit that form, the
  constants only approximate the calibration.
- Against: the host, not the radio, converts the standard fields. The safety core uses its
  own calibrated values (0007), so host display and firmware limits can differ where the
  formula does not fit exactly. The SWR register (option 3A) is the value the limits act on.
- Against: a per-band constant set means the host must pick the constants for the current TX
  frequency; a host with only per-board constant tables cannot.

#### 2B. Engineering units in the standard fields (for example 0.1 W, 10 mV)

- For: simplest for a host.
- Against: changes the meaning of the field from "ADC word converted per Appendix A" to a
  different encoding. A host that applies the Appendix A formula would get nonsense. Not
  identical meaning (0005).

#### 2C. Calibrated values, encoded so that the Appendix A formula is exact with fixed board-200 constants (proposed in draft, not chosen)

The firmware applies the full calibration (per unit, per band, linearisation; HIS-11) and
then encodes the result so that the standard Appendix A formula, with constants fixed for
board type 200, gives the calibrated value. The draft proposed supply `x = supply in mV`
with c = 4.095, and power `x = 1000 × √(P in W)` with c1 = 4.095, c2 = 1.

- For: the host sees the same calibrated values the safety core acts on.
- For: constants fixed per board type, as in Appendix A.
- Against: the word is no longer a raw ADC reading; a deviation from [P2] to be listed in the
  annex "Differences from standard P2". A host that uses the word for something other than
  the Appendix A formula would see a different curve than on other boards.
- Against: raw readings for calibration and debugging would need extra G7250 registers.

#### 2D. Constants per unit in the capability block, raw counts in the fields (merged into 2A)

- For: closer to raw P2 practice than 2C, and per-unit calibration possible.
- Against: the host, not the radio, applies calibration, so the safety core and the host can
  still disagree. The draft also listed "no per-band correction"; ON8ST's choice allows
  per-band constants where the hardware needs them, so that point no longer applies.

### 3. Units in the G7250 register map

#### 3A. Signed 32-bit integers in milli-units of an SI unit (chosen)

Every analogue telemetry register is a signed 32-bit integer: mV, mA, mW, m°C; SWR as
1000 × SWR. Status registers are enumerations or bit fields.

- For: one rule for all registers, no per-register constants for the host to learn. The
  32-bit data word [P2] holds ±2.1 × 10⁹, which covers every range above (23 A = 23,000 mA
  [G7250-MAN]).
- For: values are calibrated and are the values the safety core uses (0007).
- Against: more bits than any sensor resolves; resolution must be stated separately (in the
  capability block).

#### 3B. Raw ADC plus constants per register

- Against: the reason for raw words in the standard fields (2A) is the P2 field meaning.
  G7250-only registers have no P2 meaning to keep (0005), so that reason does not apply.
- Against: the registers that matter (SWR, limit and fault state) report what the safety
  core acts on; a raw word plus host-side formula could differ from it.

### 4. How the host learns scales and which sensors exist

#### 4A. In the spec only (as Appendix A does)

- For: as P2 does it.
- Against: a firmware update that adds a sensor or changes a scale cannot tell the host.

#### 4B. In the capability block (0003), with the spec giving the values the current firmware reports (chosen)

- For: the host reads it at connect time and does not hard-code anything; firmware versions
  can add sensors.
- For: needed anyway, since the P2 full description has no field for constants [P2,
  Appendix C].
- Against: one more thing the capability block must carry and the testbench must check.

### 5. Rates

#### 5A. P2 rates for the standard status; event-driven plus periodic for registers (chosen)

- For: follows [P2] where P2 defines rates, and its "sent whenever data changes and
  optionally periodically" for memory-mapped registers.
- Against: if the sensors cannot be read every 1 ms (HIS-11), the radio sends repeated
  values; the host cannot tell fresh from stale without the capability block stating the
  sensor update rate.

#### 5B. Slower status during TX (for example 10 ms)

- For: fewer packets per second on the CH394Q and the processor.
- Against: a deviation from the 1 ms P2 defines for SWR display latency [P2, p. 47]. Kept as
  a fallback only if HIS-14/HIS-18 show 1 ms is not affordable.

## Decision

### Standard High Priority status (port 1025)

Sent at the P2 rates: every 50 ms, every 1 ms while transmitting, and immediately when an
input bit (bytes 4, 5) changes [P2, p. 47]. Immediate sends are limited to one per 1 ms.

| Bytes | G7250 use | Depends on |
|-------|-----------|------------|
| 0–3 | sequence number, per [P2] | — |
| 4 [0] | PTT input that reaches the main unit (for example the controller microphone PTT) — reports the input, never keys TX by itself (0015) | HIS-10, HIS-17 |
| 4 [1], [2] | dot, dash of the KEY input, if it reaches the main unit; else 0 | HIS-17 |
| 4 [4] | 1 only if the hardware has a reference PLL that is locked; otherwise 0, and the capability block says "no reference PLL" | HIS-05 |
| 4 [5], [6], [3], [7] | 0 ([5], [6] "no longer supported"; [3], [7] not defined) | — |
| 5 | bit [0] = ADC0 overload; other bits 0 unless more ADCs exist | HIS-01, HIS-03 |
| 6–7 | exciter forward power, raw ADC word (2A), only if a separate exciter detector exists; else 0 | HIS-11 |
| 8–13, 16–21, 24–29, 43–48 | 0 (reserved/unused) | — |
| 14–15 | PA forward power, raw ADC word (2A), always filled; the "Alex not selected" note does not apply because the G7250 has no Alex (listed as a difference) | HIS-11 |
| 22–23 | PA reverse power, raw ADC word (2A), same | HIS-11 |
| 30 | [0] DDC FIFO overflow, [2] DUC FIFO underflow: filled from the firmware's own buffers; [1] mic overflow only if microphone data exists; [3] 0 (no speaker, 0017) | 0004, HIS-17 |
| 31–32, 35–36 | DDC and DUC buffer depth in samples, from the firmware's own buffers | 0004 |
| 33–34 | mic FIFO depth if microphone data exists; else 0 | HIS-17 |
| 37–38 | 0 (0017) | — |
| 39–40 | ADC0 max magnitude in the message period, scaled to 15 bits as [P2] describes, if the DDC chain can provide it; else 0 | HIS-01, HIS-18 |
| 41–42 | 0 unless a second ADC exists | HIS-03 |
| 49–50 | supply voltage at the power input, raw ADC word (2A) | HIS-11 |
| 51–59 | 0 (user-specific in [P2]; option 1B rejected) | — |

The standard fields carry raw ADC words exactly as [P2] does; the encoding is not a
deviation. The conversion constants (supply c; power c1, c2, in the Appendix A formulas) are
those of this unit, from its own calibration, and per band if the hardware needs it
(HIS-11). They are published in the capability block (0003); there are no fixed constants
for board type 200. A host converts the fields with the Appendix A style formula and the
unit's own constants.

The safety core does not use these words through the host formula. It uses its own
calibrated values internally for its limits (0007); the network encoding does not change
that.

Which coupler position the forward and reverse values describe (transceiver side or
antenna side of the internal ATU) is stated in the capability block (HIS-08, HIS-11).

### G7250 telemetry registers (register map, 0005)

Read-only registers, hardware to PC, units per option 3A. Addresses are assigned in the
register map (0005, spec part B). Every register exists only if the HIS confirms the sensor or
state; absent sensors are flagged absent in the capability block, not reported as 0.

| Register | Unit / encoding | Class | Depends on |
|----------|-----------------|-------|------------|
| PA temperature (one or more sensors) | m°C, signed | slow | HIS-11 |
| PA current | mA | fast | HIS-11 |
| supply current (if separate from PA current) | mA | fast | HIS-11 |
| SWR as used by the safety core | 1000 × SWR; 0 = not valid (no TX or power below the measurement threshold) | fast | HIS-11, 0007 |
| TX state: PA actually keyed | 0/1 | event | HIS-10 |
| TX arm state, and reason of the last disarm | enumeration (0015, 0007) | event | 0007 |
| fault code | enumeration, 0 = none (0007) | event | 0007, HIS-13 |
| limit status | bit field, one bit per limit (SWR, temperature, power, max TX time, supply), "limiting" and "tripped" | event | 0007, HIS-12 |
| ATU state | enumeration: off/bypassed, in line, tuning, tuned, failed | event | HIS-08 |
| antenna actually selected | enumeration | event | HIS-06 |
| sensor validity | bit field, one bit per sensor | event | HIS-11 |

These registers stay in engineering units (3A), unlike the standard fields: they are
G7250-only registers with no P2 meaning to keep (0005), and they report the calibrated values
the safety core acts on. This does not conflict with 2A, which applies only to standard P2
fields.

The firmware computes SWR itself, because the safety core needs it (0011, 0007). The host
may compute its own SWR from bytes 14–15 and 22–23; the register is the value the limits act
on. Forward and reverse power are not duplicated in registers.

Rates (accepted by ON8ST, 2026-11-19, as placeholders until HIS-11 sensor rates and the
HIS-14/HIS-18 budget are known):

- **event** registers: sent immediately on change, at most one packet per 1 ms.
- **fast** registers: every 10 ms while transmitting; with the periodic snapshot otherwise.
- **periodic snapshot** of all telemetry registers: every 1 s, in one memory-mapped packet.
- Analogue registers also send on change beyond a hysteresis stated in the capability block.

### What the host learns from the capability block (0003)

For each standard status field: filled or always 0. The unit's conversion constants for
supply, exciter, forward and reverse power (per band where needed). The coupler position. For each telemetry register: present or absent, resolution, sensor update rate.
The telemetry rates in use.

## Consequences

- Spec part B gets a High Priority status table (per byte: filled, 0, source) and a
  telemetry block in the register map, both derived from this decision.
- The annex "Differences from standard P2" lists: bytes 14–15 and 22–23 are filled without
  Alex; conversion constants come from the capability block, per unit (and per band where
  needed), instead of from Appendix A per board type. The power and supply words themselves
  are raw ADC words as in [P2] and are not a difference.
- 0003 must carry the unit's conversion constants (per band where needed), the field list and
  the sensor list (4B).
- 0007 defines the fault codes, the limit bits and the disarm reasons used here.
- Calibration (per unit, per band) lives in the radio: the firmware uses it internally for
  the safety-core limits (0007) and publishes the matching constants in the capability block
  (0003). Where calibration data comes from and how it is stored and changed is part of
  HIS-11 and of the management channel (0008).
- Raw readings for the standard fields need nothing extra: the fields are raw. Calibration
  access for the G7250 telemetry registers (raw readings behind the engineering-unit values,
  writing calibration data) goes via the management channel (0008), not via extra register
  map entries.
- The testbench checks the 50 ms / 1 ms / on-change timing, that the published constants
  convert known input values within the stated accuracy, and that event registers arrive before or with the next status packet after a
  change.
- Status and register packets are not synchronised. Spec part B states that a host must not
  assume they describe the same instant.
- If 1 ms status turns out too costly for the CH394Q or the processor (HIS-14, HIS-18),
  this decision is revisited (option 5B) and the change listed as a deviation.
- A generic P2 host (RX only, 0015) receives the status packets but does not read the
  capability block, so it has no constants for this unit; it may show wrong power and supply
  values. Harmless, since it cannot transmit.
- Appendix C byte 96 ("Number of General Purpose ADCs") is set in 0003; with 51–58 at 0, the
  proposal is 0.
- The HIS sub-questions raised here (under HIS-11: coupler position relative to the ATU,
  separate exciter detector, per-unit calibration data in the radio and where, fastest read
  rate per sensor; under HIS-01: peak magnitude per period) have been added to
  `open-questions-his.md` by the coordinator.

## Resolved (ON8ST, 2026-11-19)

- Scales in the standard fields: raw ADC words plus the unit's constants (2A with 2D), not
  the calibrated formula-compatible encoding (2C) the draft proposed.
- Board-200 constants: no fixed constants for the board type; per-unit (and per-band where
  needed) constants in the capability block (0003).
- Register rates: accepted as proposed (event immediately on change, fast group every 10 ms
  during TX, 1 s snapshot), as placeholders until the HIS answers.
- Raw sensor readings for calibration: moot for the standard fields; for G7250 registers via
  the management channel (0008).

Still open (not answered by ON8ST; depends on the HIS):

- Whether the G7250 sensor chain fits the Appendix A formula form well enough, and whether
  per-band constants are needed (HIS-11).
- Whether 1 ms status during TX is affordable, or option 5B applies (HIS-14, HIS-18).
- Appendix C byte 96 ("Number of General Purpose ADCs"): proposed 0, set in 0003.

## Sources

- [P2] openHPSDR Ethernet Protocol V4.4: High Priority Status packet, bytes 0–59 and notes
  (pp. 47–50); Memory mapped registers from hardware; Appendix A, boards 1–4, calibration
  constants for supply, exciter, forward and reverse power, DUC/DDC samples per packet
  (pp. 62–70); Appendix C, bytes 59, 94–96 and "97…1439 For future use" (pp. 72–78);
  revision history.
- [G7250-MAN] Xiegu G7250 Operation Manual rev 0.1: display areas 6 (input voltage),
  14 (SWR meter), 15 (S/Po meter) (p. 16); automatic antenna tuner (pp. 21–22); parameters
  (pp. 47–48).
- [CH394] WCH CH394 manual 1, V1.2: SPI up to 62 MHz, 10/100 Mbit/s.
- `analysis/ch394-network-budget.md`; design note §6 (M2).
- ON8ST decision, 2026-11-19.
- Decisions 0002, 0003, 0004, 0005, 0007, 0008, 0011, 0015, 0016, 0017.
- Open questions HIS-01, HIS-03, HIS-05, HIS-06, HIS-08, HIS-10, HIS-11, HIS-12, HIS-13,
  HIS-14, HIS-17, HIS-18.

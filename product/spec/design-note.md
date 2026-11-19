# G7250 network firmware — design note

- Version: draft 1, 2026-11-19
- Status: draft for review by ON8ST
- Structure: as agreed in 0001, amended by decisions 0002–0017.
- © 2026 ON8ST. Licensed under CC BY 4.0 (see `LICENSE.md`, decision 0018).
- The normative interface is in `spec/network-interface.md` (not yet written). This note
  describes the product; it does not define the protocol.

Sources are cited by key (see `sources.md`) or by decision number (see `decisions/`).

## 1. Purpose

New firmware for the main unit of the Xiegu G7250 that makes the radio a network SDR:

- **Level 1, SDR (G7250-P2).** The main unit speaks openHPSDR Protocol 2 [P2] with its own
  board type, 200 (0002, 0016). It delivers raw receive IQ, takes transmit IQ, and offers
  control and telemetry. The DSP runs on the host. (0011, 0016)
- **Level 2, Radio (TCI).** A TCI server in the main unit with DSP on board [TCI]. Only after
  feasibility gate G6. (0011)

Only one level controls the RF chain at a time, and only that level may transmit. A shared
safety core sits below both levels. (0011)

## 2. Users and host

- Users: owners of a G7250 who want to operate it as an SDR from a computer on the local
  network, with full functionality including transmit (0012).
- Primary host: AetherSDR [AETHER], the integration route for level 1 (0013). AetherSDR
  offers TCI, CAT, rigctl and audio to other applications; that is not part of the firmware.
- What AetherSDR needs (0016, [AETHER]): it supports P2 today only receive-only and only for
  the ANAN-G2; "Transmit is a future phase". A G7250 backend on P2, including transmit, is
  part of this project and is built by us if needed (0016). It goes on AetherSDR's
  `IRadioBackend` seam [AETHER]. Contributions upstream need a go from ON8ST.
- The TCI that AetherSDR offers on level 1 and the TCI server on level 2 follow one G7250 TCI
  profile, spec part C (0014).
- Other P2 hosts that do not know board type 200 may receive, but can never transmit: TX
  needs an explicit arm in the G7250 register map (0015). Which P2 hosts accept an unknown
  board type has not been checked.

## 3. The radio, from public sources

From the operation manual [G7250-MAN] unless noted.

- **Construction.** A main unit and a controller (head with a touch screen; 7" per
  [G7250-RIGPIX]), joined by a
  dedicated 15-pin cable on their CTRL interfaces. The firmware described here runs in the
  main unit.
- **Main unit interfaces.** DC power, ground, ANT1 and ANT2 (50 Ω), TUNER (external tuner:
  13.8 V out, return, trigger), ALC (RCA, output), SEND (RCA, transmit control), CTRL, and a
  LAN wired network port.
- **Controller interfaces.** Microphone (H-22, with PTT), SPK (external passive speaker,
  2 W into 4 Ω), KEY (Morse key), USB (to a PC), TF card slot; Bluetooth. The main unit has
  no audio connector and cannot play audio (ON8ST, 0017).
- **RF.** Receive 0.5–30 MHz and 50–54 MHz; transmit in the amateur bands 1.8–54 MHz.
  SSB/CW/NFM 100 W, AM 25 W. 50 MHz power is not given in the manual; secondary sources give
  90 W [G7250-PUDX], [G7250-RIGPIX]. RF direct sampling, MDS −138 dBm.
- **ATU.** Internal automatic tuner, 20–150 Ω, data stored per band.
- **Supply.** 13.8 V DC ±15 %, TX current up to 23 A.
- **Network hardware.** WCH CH394Q Ethernet controller (ON8ST, own hardware inspection,
  2026-11-19; to be confirmed by the HIS): 10/100 Mbit/s, built-in TCP/IP, 8 sockets, SPI up
  to 62 MHz [CH394].
- **Stock firmware.** Can send the digital baseband signal over the network to HDSDR on a
  PC [G7250-MAN]. Our firmware replaces it; its network protocol is not used or studied.

Not known from public sources and asked from the HIS (`open-questions-his.md`): number of
receivers, ADC and sample rates, processor and memory, sensors, ATU and antenna control,
PTT paths, what the CTRL cable carries.

## 4. Architecture

```
                    host (AetherSDR, other P2 hosts)
                                 |
                      Ethernet 10/100 (CH394Q)
                                 |
       +-------------------------+--------------------------+
       |  level 1: G7250-P2       |  level 2: TCI server      |   management
       |  IQ path (P2 streams)    |  DSP path (after G6)      |   channel
       +-------------------------+--------------------------+
       |              RF control core (frequency, antenna,                |
       |              filters, ATU, drive; G7250 register map)            |
       +------------------------------------------------------------------+
       |              safety core: watchdog, TX arm, TX limits            |
       |              (SWR, temperature, power, max TX time), fault state |
       +------------------------------------------------------------------+
                                 |
                       main unit hardware (HIS)
```

- **Firmware**: the protocol of the active level, the RF control core, the safety core, the
  management channel. (0001 item 4, 0011)
- **Host**: DSP on level 1, TCI/CAT/rigctl/audio to other applications (0013).
- **Safety core** applies to every host and both levels. A level may make limits stricter,
  never looser (0011).
- **Network budget.** The CH394Q has 8 sockets. G7250-P2 with one receiver uses 7: ports 1024,
  1025, 1026, 1027, 1029, 1035 and the G7250 register map. DDC audio (1028) is not offered
  (0017). One socket is left, for the management channel (0008). SPI at most 62 MHz limits
  receive IQ to about 384 ksps in practice (`analysis/ch394-network-budget.md`; 0004).

## 5. Principles

1. **Stay close to the standard.** P2 fields keep their P2 meaning. G7250 functions go into
   a G7250 register map carried by the P2 memory-mapped register packets; reserved bytes in
   the standard packets are not used (0009, 0005).
2. **No impersonation.** The radio identifies as G7250-P2 with board type 200, never as
   another board. No HL2 or ANAN compatibility mode (0010, 0002).
3. **Safety first for transmit.** TX needs an explicit arm, the P2 watchdog cannot be turned
   off while armed, and a takeover by another host never carries the arm (0015, 0007).
4. **Full functionality.** Every integration we deliver supports everything, including
   transmit. RX-only only as an intermediate milestone (0012).
5. **Clean room.** The product side uses only the HIS, public documents and datasheets, the
   public product information, and decisions recorded here (AGENTS.md).
6. **Spec first.** Every part of the spec gets a reference model and conformance tests in
   g7250-testbench before it is built in firmware (0001 item 5).

## 6. Milestones

Each milestone has testable exit criteria, first against the reference model in
g7250-testbench, then on the radio. (0001 item 6, 0011)

| Milestone | Content | Exit criterion (outline) | Depends on |
|-----------|---------|--------------------------|------------|
| **M1** | Discovery, capability block, RX-IQ on G7250-P2 | a P2 host finds the radio as board type 200, reads its capabilities and receives IQ at the supported rates | 0003, 0004; HIS-01, -02, -04, -14, -15, -18 |
| **M2** | Control and telemetry: frequency, antenna, filters, ATU; forward/reflected power, temperature, supply; wideband data (4096 samples, 20 frames/s, 0004) | every control in the P2 field table and the G7250 register map works and is confirmed; telemetry at the specified rates | 0005, 0006; HIS-05 to -09, -11 |
| **M3** | Watchdog and safety, specified and tested | host loss, takeover, reset and every limit lead to the specified safe state, without TX hardware active | 0007; HIS-10, -13 |
| **M4** | Transmit (only after M3) | TX via arm and P2 transmit bit, TX IQ, drive level, within all limits; AetherSDR G7250 backend transmits | 0007, 0012, 0015; HIS-03, -10, -12, -17 |
| **M5** | Management channel: firmware update, configuration, logs, identification | update with recovery after failure; configuration survives restart | 0008; HIS-19 |
| **G6** | Feasibility gate for level 2 | HIS answers on processor, memory and network stack show that on-board DSP and a TCI server fit | HIS-18 |
| **M6** | Level 2: TCI receive | a TCI client following the G7250 TCI profile receives and controls the radio | 0014, part C |
| **M7** | Level 2: TCI transmit | TCI transmit within the same safety core | 0014, M6 |

AetherSDR work runs alongside: the G7250 backend receives from M1 and transmits from M4.

## 7. Out of scope

- Protocol 1 (0016), and so the earlier name G7250-P1.
- Compatibility modes: HL2 (no 100 W amplifier, no ATU) and, for now, ANAN (0010).
- CAT and rigctl in the firmware; they stay on the host (0011).
- TCI in the firmware and DSP in the radio **before M6 and without passing G6** (0011).
- A SoapySDR module (0012).
- DDC audio playback on the main unit (0017).
- More receivers than the hardware has (0001).
- The stock firmware's network protocol (clean room).

## 8. Dependencies and open questions

- **HIS.** All hardware questions are in `open-questions-his.md` (HIS-01 to HIS-19). M1 needs
  at least HIS-01, -02, -04, -14, -15, and part of -18.
- **AetherSDR.** A G7250 backend on P2, including transmit (0016). Upstream contributions
  need a go from ON8ST.
- **g7250-testbench.** Reference model and conformance tests per spec section (0001).
- **openHPSDR.** Board type 200 was proposed in TAPR/OpenHPSDR-Firmware#6; we use another
  value if they prefer one (0002).
- **Sources still to read.** The TCI 2.1 PDF and its terms of use (before part C), the
  Radioddity product page, the HDSDR network tutorial and the Temporarily Offline video
  (`sources.md`).
- **Decisions still to write.** 0003 capability block, 0004 streams and sample rates, 0006
  telemetry, 0007 watchdog and safety, 0008 management channel.

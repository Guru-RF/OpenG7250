# Sources

Public sources used in this repository, with the short keys used for citations
(AGENTS.md rules 2 and 3). Only public documents are listed here. Nothing from the
reverse-engineering side may be added (AGENTS.md rule 1).

For each source: what it is, where it is, which version was read, when, and what it is used
for. "Read" means the document itself was read for this repository; "not yet read" means
the source has been found but not checked.

## Protocols

### [P2] openHPSDR Ethernet Protocol, V4.4

- What: the specification of openHPSDR Protocol 2. The base of level 1, G7250-P2 (0016).
- Where: github.com/TAPR/OpenHPSDR-Firmware, `Protocol 2/Documentation/openHPSDR Ethernet Protocol v4.4.pdf`
  (also as `.docx`; older versions 2.9–4.3 in the same folder).
- Version: V4.4. Revision history up to 7 Mar 2026 (G8NJJ); document © March 2019, Phil
  Harman VK6PH. Last change to the documentation folder: 2026-03-24.
- Read: 2026-11-19.
- Used for: 0002, 0005, 0015, 0016, `analysis/p1-vs-p2.md`.
- Terms: no licence statement in the document. The repository has a LICENSE file; its
  terms for the documentation have not been checked yet.
- Note: Appendix B (XML hardware description) is "To be written". The default port for
  memory-mapped registers is given as "xxxx", so it is not defined.

### [P1-USB] HPSDR – USB Data Protocol, V1.60

- What: the frame and C&C format of openHPSDR Protocol 1.
- Where: github.com/TAPR/OpenHPSDR-SVN, `Documentation/USB_protocol_V1.60.doc` (V1.58 and
  V1.59 in the same folder).
- Version: V1.60, 23 Jan 2019, VK6PH. Repository unchanged since 2019-05-11.
- Read: 2026-11-19.
- Used for: `analysis/p1-vs-p2.md`; reference only, since P1 is out of scope (0016).

### [P1-METIS] Metis – How it works, V1.33

- What: Protocol 1 over Ethernet (discovery, start/stop, UDP framing, firmware update).
- Where: github.com/TAPR/OpenHPSDR-Firmware, `Protocol 1/Documentation/Metis- How it works_V1.33.pdf`.
- Version: V1.33, 28 Feb 2015, VK6PH.
- Read: 2026-11-19.
- Used for: `analysis/p1-vs-p2.md`; reference only (0016).

### [HL2] Hermes-Lite 2 wiki, "Protocol"

- What: the Hermes-Lite 2 extensions to Protocol 1 (extended discovery reply, C&C map,
  watchdog).
- Where: github.com/softerhardware/Hermes-Lite2/wiki/Protocol.
- Version: wiki page, no version number.
- Read: 2026-11-19, through a summarising fetch, not line by line. To be read in full if it
  is used for anything normative.
- Used for: `analysis/p1-vs-p2.md`; reference only (0016).

### [TCI] Transceiver Control Interface, protocol 2.1

- What: the TCI protocol of Expert Electronics. A WebSocket protocol over TCP with ASCII
  commands; the transceiver is the server. Base of the TCI profile in spec part C (0011,
  0014).
- Where: github.com/ExpertSDR3/TCI, `TCI Protocol 2.1.pdf` (Russian version
  `TCI Protocol_RU 2.1.pdf`). Repository last changed 2026-10-22.
- Version: 2.1.
- Read: README only, 2026-11-19. The PDF itself has not been read yet.
- Terms: the repository is under the MIT licence ("Copyright (c) 2021 EE"). Whether that
  licence also covers implementing the protocol, and whether there are other terms of use,
  is still to be checked before part C is written (0011).
- Note: AetherSDR's TCI server announces protocol 2.1 [AETHER], the same version.

## Datasheets

### [CH394] WCH CH394 manual 1 (以太网协议栈芯片 CH394 手册 1), version 1.2

- What: datasheet of the WCH CH394 Ethernet protocol-stack chip (10/100 MAC+PHY, built-in
  TCP/IP, 8 sockets on CH394Q / 4 on CH394L, 32 KB RAM, SPI up to 62 MHz).
- Where: wch.cn; copy read from atta.szlcsc.com,
  `/upload/public/pdf/source/20251203/9EC0C6F644C6D345895781592F6A1E96.pdf`.
- Version: 1.2. Chinese, 3 pages; mainly the CH394Q. The CH394L manual (CH394DS2) has not been
  read.
- Read: 2026-11-19.
- Used for: `analysis/ch394-network-budget.md`.

## Host software

### [AETHER] AetherSDR README

- What: the open-source host application that is the integration route for level 1 (0013).
- Where: github.com/aethersdr/AetherSDR, `README.md`.
- Version: as of 2026-11-19; latest release v26.11.3 (2026-11-16).
- Read: 2026-11-19.
- Used for: 0016, `analysis/p1-vs-p2.md`.
- Facts used: FlexRadio (SmartSDR) is the primary target. Hermes-Lite 2 is supported over
  Protocol 1, including TX. ANAN-G2 over Protocol 2 is experimental and receive-only
  ("Transmit is a future phase"). Backends use an `IRadioBackend` seam. TCI server
  announcing protocol 2.1. Licence GPL-3.0.

## The radio

### [G7250] Public G7250 product information

- **[G7250-MAN] Xiegu G7250 Operation Manual, English, rev 0.1.** Primary source.
  radioddity.s3.amazonaws.com/Xiegu_G7250_Operation_Manual_EN_rev0.1_20261008.pdf
  (file dated 2026-10-08; back cover "Edition Jul 2026", XDT-B00; © WeiSheng Communication).
  49 pages. Read 2026-11-19 (link from ON8ST). The manual states that specifications may
  change with software upgrades.
- **[G7250-RDY] Radioddity product page.** radioddity.com/products/xiegu-g7250. Not read:
  HTTP 429 on 2026-11-19.
- **[G7250-RIGPIX] RigPix database entry.** rigpix.com/xiegu/g7250.htm, last modified
  2026-08-31. Read 2026-11-19. Secondary; many fields still "?".
- **[G7250-PUDX] PileupDX announcement.** pileupdx.com, SM0MDG, 22 Jul 2026, updated 29 Jul
  2026. Read 2026-11-19. Secondary; pre-release, "Specifications are subject to change".
- **[G7250-TOFF] YouTube channel "Temporarily Offline".** A video in which the Ethernet
  interface is tested and documented (ON8ST, 2026-11-19). Not yet identified.
- **"G7250 HDSDR Network Reception Tutorial".** Referred to by [G7250-MAN] (NETWORK
  Settings). Not found or read.

Facts. [G7250-MAN] wins where sources differ; differences are noted.

| Fact | Value | Source |
|------|-------|--------|
| Construction | main unit and controller (head) as separate units, joined by a dedicated cable on the CTRL interfaces (15-pin cable L2001) | [G7250-MAN] |
| Receive range | 0.5–30 MHz and 50.00–54.00 MHz | [G7250-MAN] |
| Transmit ranges | 1.8–2.0, 3.5–3.9, 7.0–7.2, 10.1–10.15, 14.0–14.35, 18.068–18.168, 21.0–21.45, 24.89–24.99, 28.0–29.7, 50.00–54.00 MHz (set per region) | [G7250-MAN] |
| Modes | CW, AM, SSB, FM, WFM | [G7250-MAN] |
| TX power | SSB/CW/NFM 100 W ±1 dB, AM 25 W ±1 dB (13.8 V, max). No separate 50 MHz value in the manual; [G7250-PUDX] and [G7250-RIGPIX] give 90 W on 50 MHz | [G7250-MAN] |
| Receiver | RF direct sampling; MDS −138 dBm (CW, 500 Hz) | [G7250-MAN] |
| Frequency stability | ±1.5 ppm 10 minutes after power-on; 1 ppm/hour at 25 °C | [G7250-MAN] |
| Antennas | ANT1 and ANT2 on the main unit, 50 Ω, selectable (menu "ANT SELECT"). Connector type not stated; [G7250-RIGPIX] says SO-239 | [G7250-MAN] |
| ATU | internal automatic tuner, 20–150 Ω, initial tuning ≤ 10 s, memory recall ≤ 0.1 s, tuning data stored per band | [G7250-MAN] |
| External tuner | TUNER interface on the main unit: +13.8 V out, tuner return, tuner trigger | [G7250-MAN] |
| Other main-unit interfaces | DC power, ground, ALC (RCA, ALC output), SEND (RCA, transmit control), CTRL, LAN | [G7250-MAN] |
| Network | LAN wired network port on the main unit. Stock firmware: HDSDR on a PC can receive the digital baseband signal over the network and "perform demodulation and control" | [G7250-MAN] |
| Ethernet controller | WCH CH394Q (8 sockets, SPI) | ON8ST, own hardware inspection, 2026-11-19; to be confirmed by the HIS |
| Controller interfaces | microphone (H-22, with PTT), SPK (external passive speaker 4–8 Ω), KEY (Morse key), USB (to PC, "control and audio transmission", CH342 driver), TF card slot | [G7250-MAN] |
| Audio output | 2 W into 4 Ω (≤ 10 % THD), 4–16 Ω | [G7250-MAN] |
| Bluetooth | two-way audio and control channel with a phone (device "XG-BT-G7250") | [G7250-MAN] |
| Supply | 13.8 V DC ±15 %, negative ground; RX ≤ 1.2 A, TX ≤ 23 A. [G7250-PUDX] and [G7250-RIGPIX] give 9–15 V | [G7250-MAN] |
| Operating temperature | 0 to +50 °C (storage/use warning: −10 to +50 °C) | [G7250-MAN] |

Not stated in [G7250-MAN]: the number of receivers, ADC type, sample rates, Ethernet speed.
"One receiver" (0001) comes from the start brief and is still to be confirmed (HIS).

## Discussion with ON8ST

Decisions taken in discussion with ON8ST are cited as "Discussion with ON8ST, <date>" and
recorded in `decisions/`. The start brief is cited as "Start brief, ON8ST, 2026-11-19".

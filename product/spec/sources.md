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

There is no free, public G7250 user manual yet. According to search results, Radioddity
offers an "Extended Manual" as a digital guide to first-batch preorders; this has not been
checked. Until a manufacturer document is available, the sources below are secondary.

- **[G7250-RDY] Radioddity product page.** radioddity.com/products/xiegu-g7250. Not yet
  read: the site answered HTTP 429 (too many requests) on 2026-11-19. To be read and to
  replace the secondary sources below where they agree.
- **[G7250-RIGPIX] RigPix database entry.** rigpix.com/xiegu/g7250.htm, last modified
  2026-08-31. Read 2026-11-19. Many fields are still "?".
- **[G7250-PUDX] PileupDX announcement.** pileupdx.com, "NEW Xiegu G7250 100W HF/50 MHz SDR
  Transceiver", SM0MDG, 22 Jul 2026, updated 29 Jul 2026. Read 2026-11-19. States
  "Specifications are subject to change" and does not say where the specifications come from.

- **[G7250-TOFF] YouTube channel "Temporarily Offline".** A video in which the Ethernet
  interface of the G7250 is tested and documented (ON8ST, 2026-11-19). Not yet identified:
  a web search on 2026-11-19 did not find it. Link to be added.

Facts from these secondary sources (to be confirmed against [G7250-RDY] or a manual):

| Fact | Value | Source |
|------|-------|--------|
| Frequency coverage | 0.5–30 MHz and 50–54 MHz | [G7250-PUDX], [G7250-RIGPIX] |
| Modes | SSB, CW, AM, FM, digital | [G7250-PUDX], [G7250-RIGPIX] |
| TX power | 100 W HF, 90 W on 50 MHz (±1 dB) | [G7250-PUDX], [G7250-RIGPIX] |
| Receiver | direct RF sampling | [G7250-PUDX], [G7250-RIGPIX] |
| Antenna connectors | two SO-239, 50 Ω | [G7250-RIGPIX] |
| ATU | automatic, 20–150 Ω matching range; first tune ≤ 10 s, memory tune ≤ 0.1 s, settings per band | [G7250-PUDX] (range also [G7250-RIGPIX]) |
| Supply | 9–15 V DC (Anderson Powerpole) | [G7250-PUDX], [G7250-RIGPIX] |
| Construction | separate RF deck (main unit) and controller with 7" touch screen | [G7250-PUDX], [G7250-RIGPIX] |
| Network | "remote baseband signal transmission over a network"; the type of connection (Ethernet, Wi-Fi) is not stated | [G7250-PUDX], [G7250-RIGPIX] |
| Ethernet | present on the main unit; tested and documented in a video by the YouTube channel "Temporarily Offline" | ON8ST, 2026-11-19; video [G7250-TOFF] not yet identified |
| USB | present | [G7250-RIGPIX] |

Note: neither written secondary source says that the main unit has an Ethernet port. ON8ST
confirmed it on 2026-11-19, citing the video [G7250-TOFF]. Link speed (100/1000 Mbit/s) and
the network stack remain questions for the HIS.

## Discussion with ON8ST

Decisions taken in discussion with ON8ST are cited as "Discussion with ON8ST, <date>" and
recorded in `decisions/`. The start brief is cited as "Start brief, ON8ST, 2026-11-19".

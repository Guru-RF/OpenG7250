# Analysis — Protocol 1 vs Protocol 2 for the G7250

- Date: 2026-11-19
- Requested by: ON8ST, 2026-11-19 ("side-by-side analysis of P1 and P2 for this application,
  regardless of what was decided earlier").
- Status: analysis, not a decision. Earlier decisions are discussed only in the last section.

## Sources

All protocol statements below come from these public documents. They were read on
2026-11-19 from the TAPR repositories on GitHub. The keys are to be moved into `sources.md`.

| Key | Document | Location |
|-----|----------|----------|
| [P1-USB] | HPSDR – USB Data Protocol, V1.60 (23 Jan 2019, VK6PH) | github.com/TAPR/OpenHPSDR-SVN, `Documentation/USB_protocol_V1.60.doc` |
| [P1-METIS] | Metis – How it works, V1.33 (28 Feb 2015, VK6PH) | github.com/TAPR/OpenHPSDR-Firmware, `Protocol 1/Documentation/Metis- How it works_V1.33.pdf` |
| [P2] | openHPSDR Ethernet Protocol, V4.4 (latest revision 7 Mar 2026, G8NJJ; document © March 2019, VK6PH) | github.com/TAPR/OpenHPSDR-Firmware, `Protocol 2/Documentation/openHPSDR Ethernet Protocol v4.4.pdf` |
| [HL2] | Hermes-Lite 2 wiki, "Protocol" page | github.com/softerhardware/Hermes-Lite2/wiki/Protocol |
| [G7250] | Public G7250 product specifications (Radioddity) and user manual | not yet collected; the radio facts used here are those already quoted in 0001 (one receiver, 100 W HF, 90 W on 6 m, internal ATU, two antenna connectors) |

Protocol 1 on Ethernet is the USB frame protocol [P1-USB] carried in UDP packets
[P1-METIS]. Both documents are needed to describe it.

Not checked, and marked "unverified" below: which host applications support which
protocol, and in particular what AetherSDR supports.

## What the G7250 needs from the protocol

From [G7250] as quoted in 0001, plus the open HIS questions:

- One receiver. Sample rates depend on the ADC and clock (open HIS question).
- Transmit at up to 100 W, so a host that disappears must not leave the radio transmitting,
  and SWR must be visible quickly during TX.
- Control of an internal ATU and of two antenna connectors.
- Telemetry: forward and reflected power, temperature, supply voltage (which sensors exist
  is an open HIS question).
- Firmware update over the network.
- Unknown compute budget (DSP/FPGA/MCU, network stack; open HIS question). A protocol that
  is cheap to implement keeps more options open.

## Side by side

| Topic | Protocol 1 | Protocol 2 | Meaning for the G7250 |
|-------|-----------|-----------|------------------------|
| Status of the documents | Metis V1.33 (2015) and USB V1.60 (2019) [P1-METIS], [P1-USB]. Few changes in recent years. | V4.4, revisions up to 7 Mar 2026; SATURN board added in V4.0 (2023) [P2]. Actively maintained. | P1 is stable and will not change under us. P2 still changes, so we would have to follow its revisions. |
| Transport | One UDP port, 1024, in both directions. Data packets have an 8-byte header (`0xEFFE 0x01`, end point, 32-bit sequence number) and two 512-byte USB frames [P1-METIS]. | Several UDP ports: 1024 discovery and general; defaults 1025–1029 for DDC-specific, DUC-specific, high priority, audio and DUC I&Q; 1035 upwards for DDC I&Q. Ports can be set by the host. Every packet starts with a 32-bit sequence number [P2]. | P1 is one socket and one packet layout. P2 needs more sockets and packet types in the firmware. |
| Discovery and identification | Request `<0xEFFE><0x02><60 × 0x00>`. Reply has status (0x02 idle, 0x03 sending), MAC, code version and a Board_ID byte (0x00 Metis … 0x06 Hermes Lite) [P1-METIS]. HL2 extends the reply with number of receivers, gateware version and telemetry [HL2]. | Reply has board type (0–10 assigned, 254 XML, 255 full description), protocol version, firmware version, number of DDCs, frequency-or-phase-word, endian modes [P2]. | Both need a new board-id value for the G7250. P1 has no standard place for capabilities; the HL2 shows that the reply can be extended. |
| Self-description of capabilities | None in the standard [P1-METIS]. | Board type 255: a standard "full hardware description" in the discovery reply (Appendix C), with numbers of ADCs and DDCs, attenuator, wideband, firmware update supported and more. Board type 254 (XML): "To be written" [P2]. | P2 already has a standard place for what 0001 calls the capability block. In P1 we have to define one ourselves. |
| Control (C&C) | In-band: five C&C bytes in every 512-byte frame. Bits 7–1 of C0 select the register; addresses are sent round-robin [P1-USB]. MOX is bit 0 of C0 [P1-USB]. | Separate packets: General (rarely changes), DDC-specific, DUC-specific, and High Priority (run, PTT, frequencies, drive, filters, attenuators), each sent when a value changes [P2]. | P1: a change waits for its turn in the round-robin cycle. P2: a change is sent immediately and in its own packet. P2 is easier to reason about; P1 is simpler to implement. |
| Receive IQ | 48/96/192/384 kHz, 24-bit I and Q; up to 8 receivers (3-bit field) [P1-USB]. | 48/96/192/384/768/1536 ksps per DDC; up to 80 DDCs and 8 ADCs; phase-coherent synchronous DDCs; optional VITA-49 timestamps [P2]. | The G7250 has one receiver. The rate limit depends on the HIS. Multi-DDC, sync and VITA-49 are not useful unless the HIS shows a second ADC or a TX feedback path. |
| Transmit IQ | 48 kHz, 16-bit I and Q in the host-to-radio frames. Output level set by drive level 0–255 [P1-USB]. | DUC I&Q 24-bit at 192 ksps on its own port; drive level 0–255 [P2]. | P1 TX bandwidth is limited by 48 kHz; enough for voice and data modes. P2 gives more resolution and bandwidth. |
| CW | Dot/dash/PTT reported in C&C; keyer bits added in later revisions [P1-USB]. | Keyer, sidetone and RF envelope shaping in the hardware, to avoid host latency [P2]. | Depends on whether the G7250 has a key input and compute for a keyer (HIS). |
| Audio and microphone | Mic 48 kHz 16-bit inside the RX frames; RX audio to the radio 48 kHz 16-bit inside the TX frames [P1-USB]. | Separate mic and audio ports, 64 samples per packet for low latency [P2]. | Whether the G7250 has a usable codec path is a HIS question. The HL2 ignores audio [HL2]. |
| Telemetry | Forward power, reverse power, AIN3, AIN4, supply (AIN6), 12-bit values, spread over the round-robin C&C returns [P1-USB]. | High Priority Status packet: PTT/keys, ADC overload, exciter power, forward and reverse power, supply voltage, inputs. Sent every 50 ms, every 1 ms during TX, and immediately when an input changes [P2]. | For a 100 W radio, P2 gives SWR during TX much faster, by design. In P1 the update rate depends on the cycle; it would have to be specified by us. |
| Host-loss watchdog | Not in the standard: [P1-USB] and [P1-METIS] describe none. Metis stops sending only on "Destination Unreachable" [P1-METIS]. HL2 adds a watchdog as an extension, disable-able from the start command [HL2]. | Mandatory: the host must send a C&C packet at least every second (100 ms recommended). Otherwise the radio goes to standby and PTT and open-collector outputs are switched off. Can be disabled for debugging [P2]. | P2 has the watchdog the G7250 needs, as part of the standard. In P1 we have to add it as an extension, as HL2 did. |
| ATU and filters | Apollo ATU enable and auto-tune bits; Alex HPF/LPF bits [P1-USB]. | Apollo ATU enable bit; Alex filter registers for up to 8 Alex boards [P2]. | Both describe external TAPR/Apache accessories. Neither fits the internal G7250 ATU or its antenna switching without checking against the HIS. Probably G7250 fields in both. |
| Several hosts | Status 0x03 in the discovery reply when already sending [P1-METIS]. | Same status, and a second host that sends C&C takes over the radio [P2]. | P2's takeover is a risk for TX ownership (0011, single owner) and would need restricting. |
| Firmware update | Erase and program commands over port 1024, 256-byte blocks [P1-METIS]. | Program packets, with a 16-bit checksum since V3.8 [P2]. | Both have something. 0001 puts update on a separate management channel anyway. |
| Implementation cost in the firmware | Low: one socket, fixed 1032-byte packets, fixed frame layout [P1-METIS], [P1-USB]. | Higher: several sockets and packet types, variable configuration, 24-bit TX path [P2]. | Matters if the HIS shows a small MCU and a limited network stack. |
| Host support | Unverified. The HL2 uses P1 [HL2]; which applications support P1 has not been checked. | Unverified. [P2] describes ANAN and SATURN hardware; which applications support P2 has not been checked. | The deciding question is what AetherSDR supports. Unverified. |

## Summary

For the G7250 specifically:

**Points for P2**
- A host-loss watchdog that switches off PTT is part of the standard [P2]. For a 100 W radio
  this is the most important difference.
- Fast telemetry during TX (every 1 ms) by design, useful for SWR protection [P2].
- A standard place for self-description (board type 255) [P2], which covers part of what we
  would otherwise define as a capability block.
- Event-driven control instead of a round-robin cycle [P2].
- The document is actively maintained [P2].

**Points for P1**
- Much simpler to implement: one port, one packet format [P1-METIS], [P1-USB]. This matters
  while the compute budget of the G7250 is unknown.
- Most of what P2 adds (80 DDCs, synchronous DDCs, VITA-49, 1536 ksps) is of no use to a
  radio with one receiver [G7250].
- There is a precedent for a small single-receiver radio on P1 with its own extensions,
  including a watchdog: the HL2 [HL2].
- The protocol is stable and will not change under us [P1-METIS], [P1-USB].

**What P1 lacks, and what that costs**
- A watchdog, fast TX telemetry and a capability block are not in P1. With P1 we have to
  specify them ourselves as extensions. These are exactly decisions 0003, 0006 and 0007.
  With P2 they partly exist already.

**What would decide it**
1. What AetherSDR supports, P1, P2 or both (unverified).
2. The compute and network budget of the G7250 (HIS, gate G6).
3. Whether the G7250 has a second ADC or a TX feedback path (HIS). Only then do P2
   multi-DDC and PureSignal features matter.

## Relation to earlier decisions

ON8ST asked for this analysis regardless of earlier decisions. For completeness:

- 0001 puts Protocol 2 out of scope, and 0011 (point 5) keeps it there.
- 0009 (stay close to standard P1), 0005 (C&C on P1 addresses) and 0015 (arm on a P1 C&C
  address) assume P1.
- Choosing P2, or adding it, would need a new decision that revises these. 0005 and 0015
  would have to be rewritten for P2's packet structure. 0014 (TCI profile) and 0012 are not
  affected.

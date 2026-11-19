# Glossary — G7250-P2 network interface

- Version: rc1 working draft, 2026-11-19
- © 2026 ON8ST, CC BY 4.0 (see `LICENSE.md`)

Terms as used in `network-interface.md`, part C and the annexes. Where a term comes from
openHPSDR Protocol 2 it keeps the P2 meaning [P2]; G7250 terms are defined by the decision
named.

| Term | Meaning | Source |
|------|---------|--------|
| **Level 1** | The SDR level: G7250-P2, raw IQ, DSP on the host. | 0011, 0016 |
| **Level 2** | The radio level: TCI server in the radio with DSP on board; only after gate G6. | 0011 |
| **G7250-P2** | The level-1 interface: openHPSDR Protocol 2 V4.4 with board type 200 and the deviations in Annex X1. | 0002, 0016 |
| **Board type** | Byte 11 of the P2 discovery reply; 200 (0xC8) for G7250-P2. | [P2], 0002 |
| **Host** | Software on the network that talks to the radio (for example AetherSDR). | [P2] |
| **Session** | The period from the first control packet a host sends after discovery until stop, watchdog expiry, takeover or reset. | [P2] "Detailed operation", 0007 |
| **Owner** | The host whose control packets the radio follows, identified by IP address and UDP port. At most one owner at a time. | 0007, 0011 |
| **Takeover** | A different host (other IP address or other port) sending control packets while another host is owner. Always allowed; always unkeys and disarms. | [P2], 0007 |
| **C&C / control packets** | The four P2 host-to-radio "Control Elements" packets: General, DDC-specific, DUC-specific, High Priority. They feed the watchdog. Register-map packets are not C&C. | [P2], 0003, 0007 |
| **Watchdog** | The P2 rule that the radio leaves RUN if no control packet arrives for 1 s. Cannot be disabled while armed. | [P2], 0007 |
| **Run** | High Priority packet byte 4 bit [0]; enables the radio's streams. | [P2] |
| **Transmit bit** | High Priority packet byte 4 bit [1] (PTT0). Has effect only while armed. | [P2], 0015 |
| **Armed** | State in which the radio may transmit. Reached only through the arm handshake in the G7250 register map. | 0015, 0007 |
| **Arm handshake** | Host declares a mode class, reads the per-session arm token, writes the derived value; the radio confirms. | 0007 |
| **Mode class** | Host-declared class of the transmitted signal (for example AM vs. SSB/CW/FM), used to apply per-mode limits. Required before arming. | 0007 |
| **Keyed** | Armed and transmitting (transmit bit set and accepted). | 0007 |
| **Keyed timeout** | 500 ms without a High Priority packet while keyed: the radio unkeys, the arm stays. | 0007 |
| **Maximum continuous TX time** | 5 min default: the radio unkeys, the arm stays. A host may set it stricter. | 0007 |
| **Disarm** | Leaving the armed state; the host must arm again. Each disarm has a reason code. | 0007 |
| **Fault (class 1 / class 2)** | Class 1: cleared by the host once the condition is gone. Class 2: cleared only by reset. RX continues during a fault. | 0007 |
| **Safety core** | Firmware layer below both levels with watchdog, arm, limits and fault state. A level may tighten limits, never loosen them. | 0011, 0007 |
| **G7250 register map** | G7250-specific registers (16-bit address, 32-bit data) carried by the P2 memory-mapped register packets on one local UDP port. | [P2], 0005 |
| **Capability record** | Read-only block in the register map describing what this radio offers, including per-unit conversion constants. Read with one request after discovery. | 0003 |
| **DDC / DUC** | Digital down-converter (receive channel) / digital up-converter (transmit channel), P2 terms. G7250-P2 has one DDC (HIS-02) and one DUC. | [P2], 0004 |
| **Wideband** | Raw ADC sample blocks for a full-band display; G7250-P2 from M2: 4096 samples per frame, a frame every 50 ms. | [P2], 0004 |
| **Raw ADC word** | Telemetry value as sampled, converted by the host with the unit's constants from the capability record. | [P2] Appendix A, 0006 |
| **Management channel** | Separate UDP port for identification, configuration, logs and firmware update; never keys the radio. | 0008 |
| **First-secret window** | Short window after first power-on or factory reset in which the management secret can be set over the network. | 0008 |
| **Socket budget** | The 8 sockets of the WCH CH394Q Ethernet controller: 7 for G7250-P2, 1 for the management channel. | [CH394], 0017, 0008 |
| **HIS** | Hardware-interface spec, the clean source of hardware facts; questions in `open-questions-his.md`. | AGENTS.md |
| **G6** | Feasibility gate for level 2 (compute, memory, network stack). | 0011 |
| **TCI profile** | The subset and extensions of TCI 2.1 that both AetherSDR (level 1) and the firmware (level 2) follow; part C. | 0014, [TCI] |

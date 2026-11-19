# G7250 network interface specification

- Version: draft 1, 2026-11-19
- Status: draft. Focus: milestone M1 (discovery, capability block, RX IQ on G7250-P2).
- © 2026 ON8ST, CC BY 4.0 (see `LICENSE.md`).
- Structure: decision 0001, "(2) Network-interface spec", as revised by 0016, split into parts
  A, B and C by 0011.

Sources are cited by key (see `sources.md`) or by decision number (see `decisions/`).
Citations of [P2] give the packet name and byte number of [P2] V4.4. Values that depend on
an open question are written "TBD (HIS-xx)" (see `open-questions-his.md`) or "pending NNNN"
for a decision that has not been written yet.

---

## Part A — Common to both levels (placeholder)

Part A will hold what applies to every level (0011, Consequences):

- **A1 Management channel**: firmware update, configuration, logs and identification, on a
  connection separate from G7250-P2 and TCI (0001 spec section 10). Pending 0008. The CH394Q
  socket budget leaves one socket for it (0017; `analysis/ch394-network-budget.md`).
- **A2 Level selection and ownership**: only one level controls the RF chain at a time, and
  only that owner may transmit; the active level is visible in the capability block and in the
  management channel (0011, points 2 and 3). Pending 0007 and 0008.
- **A3 Safety behaviour visible on the network**: watchdog, TX arm, TX limits (SWR,
  temperature, power, maximum TX time), fault state and state after reset, as seen by a host
  (0011 point 3, 0015). Pending 0007.

---

## Part B — Level 1: G7250-P2

### B1 Scope and conformance language

B1.1 This part specifies the network interface of level 1 of the G7250 main-unit firmware,
called **G7250-P2**: openHPSDR Protocol 2 with a G7250 board type (0016, 0002).

B1.2 The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD
NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY" and "OPTIONAL" in this document are to be
interpreted as described in BCP 14 (RFC 2119, RFC 8174) when, and only when, they appear in all
capitals, as shown here. "The G7250" means the G7250 main unit running firmware that
conforms to this part. "The host" means a P2 host application.

B1.3 **Normative reference.** [P2] openHPSDR Ethernet Protocol V4.4 (see `sources.md`). Where
this document says "[P2]" without a version, V4.4 is meant.

B1.4 **Default rule.** The G7250 MUST behave as [P2] specifies, for every packet, field and
procedure, unless this document states a deviation (0009 as revised by 0016).

B1.5 **Deviations.** Every deviation from [P2] MUST be stated in the section concerned and
listed in Annex X1 (0009, Consequences; 0005, Consequences). A behaviour that is not in
Annex X1 is not a deviation.

B1.6 **Clarifications.** Where [P2] is ambiguous or contradicts itself, this document states
the reading the G7250 follows and lists it in Annex X2. A clarification is not a deviation:
it picks one of the readings [P2] allows.

B1.7 **Extensions.** G7250 functions that no standard P2 field describes with identical
meaning are carried in the G7250 register map on the P2 memory-mapped register packets
(0005). Reserved bytes in the standard P2 packets MUST NOT be given a G7250 meaning (0005,
rule 3).

B1.8 **Scope of this draft.** Sections B1–B6 are written for M1. Sections B7–B11 are
placeholders. Transmit is out of scope for M1 (design note §6).

### B2 Transport

B2.1 **UDP over IPv4.** All G7250-P2 packets are UDP datagrams; IP and UDP headers are as per
the UDP/IP standards ([P2], "openHPSDR Host to Hardware Protocol" and "openHPSDR Hardware to
Host Protocol"). Diagrams in this document show the UDP payload only, starting at byte 0
([P2], same sections).

B2.2 **Link.** The Ethernet interface is 10/100 Mbit/s; Gigabit is not available. Source:
WCH CH394Q, 10/100 MAC and PHY [CH394] (ON8ST hardware inspection, 2026-11-19; to be
confirmed, HIS-14). A host MUST NOT assume Gigabit throughput. The throughput towards the
host is further limited by the SPI link between processor and CH394Q, at most 62 MHz [CH394]
(`analysis/ch394-network-budget.md` §2; HIS-14).

B2.3 **Local ports.** The G7250 MUST open exactly the local UDP ports in Table B2-1, and no
other port for level 1. Sources: [P2] General packet bytes 5–32 (defaults); socket
analysis (`analysis/ch394-network-budget.md`, addendum); 0005; 0017.

Table B2-1 — Local UDP ports of the G7250 (level 1)

| # | Local port | In (host → G7250) | Out (G7250 → host) | Status in G7250-P2 | Source |
|---|-----------|-------------------|--------------------|--------------------|--------|
| 1 | 1024 | Discovery, General packet, Erase/Program/Set IP | Discovery reply, command replies | MUST be open | [P2] "Detailed operation"; General packet; Discovery reply |
| 2 | 1025 | DDC-specific packet | High Priority status | MUST be open | [P2] General bytes 5–6, 11–12 |
| 3 | 1026 | DUC-specific packet | Microphone samples (TBD, HIS-17) | MUST be open | [P2] General bytes 7–8, 19–20 |
| 4 | 1027 | High Priority packet | Wideband ADC0 data (pending 0004) | MUST be open | [P2] General bytes 9–10, 21–22 |
| – | 1028 | DDC audio | – | MUST NOT be opened | 0017 |
| 5 | 1029 | DUC0 I&Q | – | MUST be open (used from M4) | [P2] General bytes 15–16; 0012 |
| 6 | 1035 | – | DDC0 I&Q | MUST be open | [P2] General bytes 17–18 |
| 7 | TBD (0005) | G7250 register map (memory-mapped registers from PC) | G7250 register map (memory-mapped registers from hardware) | MUST be open | [P2] General bytes 29–32; 0005 |

- Ports 1036 and up (DDC1 and further, [P2] General bytes 17–18) are not opened while the
  G7250 implements one DDC. Number of DDCs: TBD (HIS-02).
- **Memory-mapped register port.** [P2] gives the default of General bytes 29–30 and 31–32 as
  "xxxx", so it is undefined; this document defines it (0005). The port number is TBD
  (0005). The G7250 MUST use one and the same local port for both directions, because the
  socket budget has one socket for the register map (0017, Consequences: 7 of 8 sockets;
  `analysis/ch394-network-budget.md`). Using a defined default here is a deviation (Annex X1,
  D2).
- **Port 1028.** The G7250 opens no socket on port 1028 (0017). A host SHOULD NOT send DDC
  audio packets. The G7250 accepts General packet bytes 13–14 and ignores them (0017). How
  the CH394Q reacts to a datagram for a closed port (silent drop or ICMP port unreachable) is
  TBD (0017, Consequences; [CH394] does not say). This is a deviation (Annex X1, D1).
- **Non-default ports.** [P2] lets the host set every port in General bytes 5–22 and 29–32,
  zero meaning the default. Whether the G7250 honours non-default values is TBD (no decision
  yet). The G7250 MUST NOT use more sockets than Table B2-1 in any case
  (`analysis/ch394-network-budget.md`). Until this is decided, a host SHOULD send zero in
  these bytes.
- **Socket budget.** Table B2-1 uses 7 of the 8 CH394Q sockets; the eighth is reserved for
  the management channel (0017; 0008 pending; [CH394]).

B2.4 **Remote endpoint.** The G7250 MUST reply to the discovery from local port 1024 to the
IP address and source port of the host's discovery packet ([P2] "Detailed operation";
Discovery reply, "Source Port", "Destination Port"). The G7250 MUST send DDC I&Q data to the
source port of the host that initiated the discovery ([P2] DDC packet, "Destination Port").

B2.5 **Byte order and integer interpretation.** Multi-byte fields MUST be sent and read MSB
first (network byte order, big-endian), and all values are unsigned integers unless stated
otherwise ([P2] "openHPSDR Host to Hardware Protocol"; General packet byte 39: zero selects
Big-Endian). The same applies from the G7250 to the host; [P2] "openHPSDR Hardware to Host
Protocol" writes "MSB first (little Endian)", which the G7250 reads as MSB first (Annex X2,
C1). Other endian modes: see B3.7.

B2.6 **Packet length.** No G7250-P2 UDP payload exceeds 1444 bytes (byte 0 to byte 1443),
the largest payload in [P2] (High Priority packet, DDC-specific packet, memory-mapped
register packets, DDC I&Q packet, all ending at byte 1443).

B2.7 **Sequence numbers.** Every packet starts with a 4-byte sequence number, bytes 0–3,
MSB first ([P2] "Detailed operation"). For each local port and direction the G7250 sends on,
it MUST keep its own counter that starts at 0x00000000, increments by one per packet and
rolls over after 0xFFFFFFFF ([P2] DDC packet, Memory mapped registers from hardware,
"Sequence Number"). The counter MUST be reset to zero at power-on and whenever a stop is
received (B5.4) ([P2] DDC packet, "Sequence Number"). The discovery reply always carries
sequence number 0 ([P2] Discovery reply bytes 0–3). On the receive side the G7250 SHOULD NOT
reject a packet because of its sequence number (provisional, pending B11; [P2] General,
DDC-specific and High Priority packets give the host's sequence number as 0x00000000, Annex
X2, C2), except where [P2] requires it (programming,
[P2] Command reply packet). Detection and reporting of gaps: pending (B11). Clarification
of the conflicting [P2] statements on sequence numbers: Annex X2, C2.

### B3 Discovery

B3.1 **Listening.** The G7250 MUST listen on UDP port 1024 for discovery packets at all
times while level 1 is reachable, including while running ([P2] "Detailed operation";
Discovery reply byte 4, value 0x03). Whether discovery is answered while level 2 is active
is part A (pending 0007, 0008).

B3.2 **Discovery request.** A discovery request is a UDP payload to port 1024 with byte 4 =
0x02 ([P2] Discovery packet). Bytes 0–3 are the sequence number, set to 0x00000000 by the
host; bytes 5–59 are zero ([P2] Discovery packet). The G7250:

- MUST answer a request sent to its own unicast address, to the limited broadcast
  255.255.255.255, and to the directed broadcast address of its subnet ([P2] Discovery packet,
  "Destination Address");
- MUST answer regardless of the endian mode selected by an earlier General packet ([P2]
  Discovery packet, NOTE; Discovery reply byte 22, NOTE);
- SHOULD NOT require bytes 0–3 or 5–59 to be zero to answer (provisional, pending B11);
- MUST answer every request with exactly one reply.

B3.3 **Discovery reply.** The G7250 MUST reply with a 60-byte payload (bytes 0–59), from
local port 1024 to the host's IP address and source port ([P2] Discovery reply, "Source
Port", "Destination Port"). The reply always uses the format below, irrespective of the
selected endian mode ([P2] Discovery reply byte 22, NOTE).

Table B3-1 — G7250 discovery reply ([P2] Discovery reply, option 1)

| Byte | [P2] field | G7250 value | Source |
|------|-----------|-------------|--------|
| 0–3 | Seq # | 0x00000000 | [P2] Discovery reply bytes 0–3 |
| 4 | Response to discovery | 0x02 or 0x03, see B3.4 | [P2] byte 4 |
| 5–10 | Board MAC, MSB first | the G7250's MAC address; TBD (HIS-15) | [P2] bytes 5–10 |
| 11 | Board type | 200 (0xC8) | 0002; [P2] byte 11 |
| 12 | openHPSDR protocol version supported | 44 (V4.4), see B3.5 | [P2] byte 12; B1.3 |
| 13 | Firmware code version | G7250 firmware version, see B3.5; TBD | [P2] byte 13 |
| 14–19 | Mercury 0–3, Penny, Metis code versions | 0x00 | [P2] bytes 14–19 (Atlas only; zero = not present) |
| 20 | Number of DDCs implemented | TBD (HIS-02); provisional 1 (0001, start brief) | [P2] byte 20 |
| 21 | Frequency or phase word | TBD (HIS-04); 0 = frequency, 1 = phase | [P2] byte 21 |
| 22 | Available endian modes | see B3.7; provisional 0x00 | [P2] byte 22 |
| 23 | Beta version | 0x00 for a release; non-zero for a beta build | [P2] byte 23 |
| 24 | Reserved for future use (AD0ES) | 0x00 | [P2] byte 24; 0005 rule 3 |
| 25–59 | (unassigned) | 0x00 | [P2] Discovery reply; 0005 rule 3 |

B3.4 **Status byte (byte 4).**

- The G7250 MUST send 0x02 when it is not running, or when it is running for the host that
  sends the discovery ([P2] Discovery reply byte 4).
- The G7250 MUST send 0x03 when it is running and connected to a different host ([P2]
  Discovery reply byte 4). "Running" means the run bit is set (B5.3); "connected host" is the
  host whose High Priority packet set the run bit (B5). The precise definition of ownership
  is pending 0007.
- Whether the G7250 ever uses 0xFE/0xFF in byte 4 or board type 255 (full description,
  [P2] Appendix C) is pending 0003 (see B4 and Annex X2, C3).

B3.5 **Version encoding.** [P2] bytes 12 and 13 are single bytes that the host reads as a
decimal number with one implied decimal place: 104 is version 10.4 ([P2] Discovery reply
"Byte 12", "Byte 13").

- Byte 12 MUST be 44, since the normative reference is V4.4 (B1.3). If this specification
  moves to another [P2] version, byte 12 changes with it.
- Byte 13 MUST carry the G7250 firmware version in the same encoding: major × 10 + minor, at
  most 25.5. The numbering scheme of G7250 firmware releases is TBD (pending 0008); a richer
  version is carried in the capability block (pending 0003).

B3.6 **MAC address.** Bytes 5–10 MUST hold the MAC address the G7250 uses on the link, MSB
first ([P2] Discovery reply, "MAC"). The MAC address MUST be unique per unit, because the
host uses it to tell radios apart and to address Set IP packets ([P2] Set IP Address packet).
Where it is stored and whether it is unique per unit: TBD (HIS-15).

B3.7 **Endian modes and DDC data format (byte 22).** [P2] Discovery reply byte 22 lists the
formats supported; zero means Big-Endian with 3-byte I&Q only. The host selects one in the
first General packet, byte 39 ([P2] General packet byte 39). The set of formats the G7250
offers is pending 0004; until then the G7250 SHOULD report 0x00 (Big-Endian, 3-byte I&Q),
which is the [P2] default for FPGA-based hardware ([P2] "Detailed operation", NOTE3).

B3.8 **Frequency or phase word (byte 21).** The value MUST match what the G7250 accepts in the
High Priority frequency fields ([P2] High Priority packet bytes 9–12, 329–332) and in General
packet byte 37 bit [3]. If the G7250 reports phase (1), the host computes
`phase_word = 2^32 × f(Hz) / DSP clock (Hz)` ([P2] General packet byte 37); the DSP clock of
the G7250 is then made known to the host in the capability block (pending 0003), since board
type 200 has no entry in [P2] Appendix A. Value and DSP clock: TBD (HIS-04).

B3.9 **Other port-1024 commands.** Erase (0x04), Program and Set IP (0x03) on port 1024 ([P2]
Erase, Program, Set IP Address packets) are part of firmware update and configuration. Whether
the G7250 supports them, or answers them with a defined refusal, is pending 0008 (management
channel). Until then the G7250 MUST NOT change its firmware or IP configuration in response
to these packets.

### B4 Capability block (placeholder, pending 0003)

The format and location of the capability block are pending decision 0003, which is being
written in parallel. This section only lists the requirements it MUST meet:

- It MUST name the interface "G7250-P2" (0002, Consequences; 0016).
- It MUST carry the G7250 firmware version in a form richer than discovery byte 13 (B3.5),
  and the version of this specification it conforms to.
- It MUST say whether level 2 exists in this firmware and whether it is active (0011,
  Consequences; 0011 point 2).
- It MUST state that DDC audio is not supported (0017); if [P2] Appendix C is used, byte 59
  "DDC Audio CODEC supported" = 0 (0017, Consequences).
- It MUST carry the version of the G7250 register map (0005, option A "For").
- If [P2] Appendix C is used, byte 23 "Memory mapped registers supported" MUST be set (0005,
  Consequences).
- It SHOULD give what a host needs that board type 200 does not imply through [P2]
  Appendix A: number of DDCs, supported sample rates, frequency or phase word and DSP clock
  (B3.8). Content beyond this list: 0003.
- It MUST be compatible with board type 200 in discovery byte 11 (0002, Consequences: "0003
  has to solve that").

### B5 Session start and stop

B5.1 **Order of a session start.** The host establishes a session as follows ([P2]
"Detailed operation"; General packet introduction; DDC specific packet introduction; High
Priority data packet introduction):

1. discovery request and reply on port 1024 (B3);
2. General packet to port 1024; the first General packet after a discovery reply MUST be
   Big-Endian and its byte 39 selects the data format for all later packets ([P2] General
   packet byte 39);
3. DDC-specific packet to port 1025 (B6.5), and DUC-specific packet to port 1026 (TX set-up,
   M4);
4. High Priority packet to port 1027 with byte 4 bit [0] (run) set.

B5.2 The G7250 MUST NOT send DDC I&Q data before it has received a High Priority packet with
the run bit set ([P2] "Detailed operation": run "in order to start data from the Hardware").
If the run bit arrives before any General or DDC-specific packet, the G7250 MUST use the [P2]
defaults and the G7250 safe RX state (0015, Consequences; RX default state TBD, HIS-06,
HIS-07). Behaviour for a run bit received without any preceding discovery from that host:
pending 0007.

B5.3 **Run.** High Priority byte 4 bit [0] set enables the G7250, clear disables it ([P2] High
Priority packet, "Byte 4"). While run is set and DDC0 is enabled (B6.5), the G7250 MUST send
DDC0 I&Q (B6).

B5.4 **Stop.** A High Priority packet with byte 4 bit [0] clear stops the session: the G7250
MUST stop all outgoing streams and reset its outgoing sequence counters (B2.7) ([P2] High
Priority packet byte 4; DDC packet, "Sequence Number"). A stop also clears the TX arm (0015,
Consequences). The G7250 MUST keep answering discovery on port 1024 (B3.1). Restart: by a new
High Priority packet with run set, or by a new discovery and full set-up ([P2] "Detailed
operation").

B5.5 **Transmit bit.** High Priority byte 4 bit [1] (transmit / PTT0, [P2] High Priority
packet) MUST have no effect unless TX is armed in the G7250 register map (0015). In M1 TX is
never armed. Arm register and its behaviour: pending 0007, 0005.

B5.6 **Watchdog.** The G7250 MUST implement the [P2] host-loss watchdog: if no C&C packet
arrives for one second while in RUN, the G7250 leaves RUN for standby and deactivates PTT and
outputs ([P2] "Detailed operation"; General packet byte 38). The host SHOULD send a C&C
packet every 100 ms ([P2] "Detailed operation"). [P2] lets the host disable the timer with
General packet byte 38 bit [0] clear; the G7250 MUST NOT allow that while TX is armed (0015;
Annex X1, D4). Which packets count as C&C, the timing tolerance, and the full safe state:
pending 0007.

B5.7 **Second host.** In [P2] a host that sends C&C to hardware connected to another host
takes over the hardware ([P2] Discovery reply, byte 4 NOTE). On the G7250 a takeover never
carries the TX arm (0015). Whether takeover is allowed at all, and under what conditions:
pending 0007 (single owner, 0011). Any restriction is a deviation (Annex X1, D5).

### B6 RX IQ stream

B6.1 **Port and endpoint.** DDC0 I&Q MUST be sent from local port 1035 ([P2] General packet
bytes 17–18; DDC packet, "Source Port") to the host's discovery source port (B2.4). Further
DDCs (port 1036 and up) only if the G7250 implements them: TBD (HIS-02).

B6.2 **Packet format.** With 24-bit samples (the only size this draft allows, B6.3) each
packet MUST have the layout of Table B6-1 ([P2] DDC packet, "DDC I&Q Data (DDC0 default port
1035)"), 1444 bytes in total.

Table B6-1 — DDC0 I&Q packet, 24-bit samples ([P2] DDC packet)

| Byte | Field | G7250 value | Source |
|------|-------|-------------|--------|
| 0–3 | Seq # [31:0] | per-port counter, B2.7 | [P2] DDC packet bytes 0–3 |
| 4–11 | Time stamp [63:0] | see B6.6 | [P2] bytes 4–11 |
| 12–13 | Bits per sample [15:0] | 24 (0x0018) | [P2] bytes 12–13; DDC-specific byte 22 |
| 14–15 | I&Q samples per frame [15:0] | 238 (0x00EE) | [P2] bytes 14–15; B6.4 |
| 16–18 | I sample 0 [23:0] | signed two's complement | [P2] bytes 16–18 |
| 19–21 | Q sample 0 [23:0] | signed two's complement | [P2] bytes 19–21 |
| 22–1437 | I and Q samples 1–236 | same layout, 6 bytes per sample | [P2] DDC packet |
| 1438–1440 | I sample 237 | | [P2] (follows from layout) |
| 1441–1443 | Q sample 237 [23:0] | | [P2] bytes 1441–1443 |

B6.3 **Samples.** Each I and Q value MUST be a 24-bit signed two's-complement integer, MSB
first, I before Q, samples in time order from first to last ([P2] DDC packet, "DDC I/Q
Samples"; NOTE on I and Q order). The G7250 MUST support 24 bits per sample, the [P2] default
([P2] DDC-specific packet byte 22; DDC packet, "Bits per sample"). Other sizes and the float
and double formats: pending 0004 (B3.7).

B6.4 **Samples per packet.** With 24-bit samples and one DDC, each packet MUST carry 238 I&Q
samples: 16 + 238 × 6 = 1444 bytes ([P2] DDC packet table, last sample "Q Sample 237" at bytes
1441–1443). Bytes 14–15 MUST state the number of samples that follow ([P2] DDC packet, "I&Q
Samples per frame"). A host MUST read bytes 14–15 rather than assume 238 ([P2], same field:
"indicates the number of samples that follow"). Informative: at 384 ksps this is about
1613 packets per second and 18.4 Mbit/s payload (`analysis/ch394-network-budget.md` §2).

B6.5 **DDC-specific packet.** The G7250 MUST accept the DDC-specific packet on port 1025
([P2] DDC specific packet) and treat its fields as in Table B6-2. Fields not listed are
ignored. This table is the M1 part of the P2 field table (0005, Consequences); it becomes
final with that table (B7).

Table B6-2 — DDC-specific packet fields ([P2] DDC specific packet)

| Byte | Field | G7250 behaviour | Source |
|------|-------|-----------------|--------|
| 4 | Number of ADCs | accepted; the G7250 uses its own ADC count, TBD (HIS-01) | [P2] byte 4 |
| 5 | Dither ADC0–7 | bit [0]: honoured if the ADC supports dither, else ignored; TBD (HIS-01) | [P2] byte 5 |
| 6 | Random ADC0–7 | bit [0]: as byte 5; TBD (HIS-01) | [P2] byte 6 |
| 7 | DDC enable DDC0–7 | bit [0] honoured: DDC0 sends I&Q only while set and run is set; other bits per HIS-02 | [P2] byte 7; B5.3 |
| 8–16 | DDC enable DDC8–79 | ignored while number of DDCs ≤ 8 (HIS-02) | [P2] bytes 8–16 |
| 17 | ADC for DDC0 | 0 (ADC0) honoured; other values TBD (HIS-01, HIS-03) | [P2] byte 17 |
| 18–19 | Sampling rate DDC0, ksps | honoured for supported rates, pending 0004 (provisional 48, 96, 192, 384 ksps); unsupported value: pending B11 | [P2] bytes 18–19; `analysis/ch394-network-budget.md` |
| 20–21 | CIC1, CIC2 DDC0 | ignored ("For future use" in [P2]) | [P2] bytes 20–21 |
| 22 | Sample size DDC0 | 24 honoured; 0 read as the default 24; other values pending 0004 | [P2] byte 22 |
| 23–496 | ADC, rate, CIC, size DDC1–79 | ignored for DDCs not implemented (HIS-02) | [P2] bytes 23–496 |
| 1363–1442 | Sync DDC0–79 | ignored; synchronous DDCs not supported unless HIS-03 shows a second ADC | [P2] bytes 1363–1442; HIS-03 |
| 1443 | Currently not used | ignored | [P2] byte 1443 |

A change of DDC0 sampling rate while running SHOULD take effect without a stop, since [P2]
sends the DDC-specific packet "when a parameter changes" ([P2] DDC specific packet,
introduction); whether the G7250 restarts the sequence counter on a rate change is pending
0004.

B6.6 **Time stamp.** [P2] defines bytes 4–11 as a 64-bit sample count at the ADC sample rate,
enabled by General packet byte 37 bit [0] ([P2] DDC packet, "Time stamp"; General packet byte
37). Whether the G7250 supports time stamping, and the value of bytes 4–11 when it is not
enabled, is pending 0004. VITA-49 format (General byte 37 bit [1]) is pending 0004.

B6.7 **Sample rates.** The set of DDC0 sample rates is pending 0004; provisional 48–384 ksps
(48, 96, 192, 384, from the [P2] list in DDC-specific bytes 18–19). 768 and 1536 ksps are not
expected, because of the SPI limit (`analysis/ch394-network-budget.md` §2; HIS-01, HIS-14).

B6.8 **Receive frequency.** DDC0 frequency is set by High Priority bytes 9–12, in Hz or as a
phase word as declared in discovery byte 21 ([P2] High Priority packet bytes 9–12; General
packet byte 37 bit [3]; B3.8). Range: 0.5–30 MHz and 50–54 MHz [G7250-MAN]; behaviour outside
the range: pending B7, B11.

B6.9 **Pacing.** The G7250 SHOULD send a DDC0 packet as soon as 238 samples are available,
to keep latency low (provisional, pending 0004; by analogy with [P2] "Detailed operation",
which gives this advice for DUC data; the CH394Q has 32 KB of buffer shared over all sockets
[CH394]). Overrun behaviour: pending B11.

### B7 P2 field table (placeholder, pending 0005 per-field check and HIS)

Per standard P2 field of the General, DDC-specific, DUC-specific and High Priority packets:
used, ignored or rejected by the G7250, with source (0005, Consequences). Waits for the
per-field check against [P2] (0005) and HIS-05 to HIS-09. Includes the High Priority status
packet, where the speaker FIFO fields are 0 and speaker FIFO underflow is never set (0017,
Consequences).

### B8 G7250 register map (placeholder, pending 0005, 0007)

Address, name, data layout, direction, access and source for each G7250 register on the
memory-mapped register packets ([P2] Memory mapped registers from PC / from hardware), the
port (B2.3), write confirmation and ordering against High Priority packets (0005,
Consequences). Includes TX arm and TX-armed status (0015). Waits for 0007 and HIS-06 to
HIS-12.

### B9 Telemetry (placeholder, pending 0006)

Fields, scale, unit and update rate, in the High Priority status packet ([P2]: every 50 ms,
every 1 ms during TX) and the register map. Waits for 0006 and HIS-11.

### B10 Transmit (placeholder, pending 0007; milestone M4)

DUC-specific packet, DUC0 I&Q on port 1029 (24-bit, 192 ksps in current [P2] implementations,
[P2] "Detailed operation" NOTE2), drive level, arm, limits. Waits for 0007, 0012, 0015 and
HIS-03, -10, -12, -17.

### B11 Error handling and robustness (placeholder, no decision yet)

Malformed or short packets, unknown command bytes, unsupported field values (for example an
unsupported sample rate), sequence gaps, overruns, packets on closed ports (0017). To be
decided; no decision number reserved yet (0001 spec section 11).

---

## Part C — Level 2: TCI (placeholder)

Part C will define the single G7250 TCI profile, followed by both AetherSDR on level 1 and
the firmware's TCI server on level 2 (0014). Base: [TCI] Transceiver Control Interface,
protocol 2.1 (`sources.md`). The PDF and its terms of use have not been read yet; that is a
precondition for writing part C (0011, Consequences; `sources.md`). Level 2 is built only
after gate G6 (0011 point 4).

---

## Annex X1 — Differences from standard P2

Every deviation of G7250-P2 from [P2] (B1.5). Status "decided" means the decision is
accepted; the exact specification may still be pending.

| Id | Deviation | [P2] behaviour | G7250 behaviour | Decision | Spec section |
|----|-----------|----------------|-----------------|----------|--------------|
| D1 | No DDC audio stream | Host may send DDC audio to port 1028 (default) for the hardware DAC ([P2] DDC Audio packet; General bytes 13–14) | No socket on port 1028; General bytes 13–14 accepted and ignored; DDC audio reported as unsupported | 0017 | B2.3, B4 |
| D2 | Memory-mapped register port defined | Default port "xxxx", undefined ([P2] General bytes 29–32) | Defined default port (TBD, 0005), one port for both directions; carries the G7250 register map | 0005 | B2.3, B8 |
| D3 | TX needs an explicit arm | High Priority byte 4 bit [1] enables transmit ([P2]) | Bit has no effect unless TX is armed in the G7250 register map | 0015 | B5.5, B10 |
| D4 | Watchdog cannot be disabled while armed | Host may clear General byte 38 bit [0] to disable the reset timer ([P2]) | Clearing is not honoured while TX is armed | 0015 (detail pending 0007) | B5.6 |
| D5 | Takeover restricted | A host sending C&C takes over from the connected host ([P2] Discovery reply byte 4 NOTE) | A takeover never carries the TX arm; whether takeover is allowed at all is pending | 0015, 0007 (pending) | B5.7 |

Not deviations, but G7250 choices within [P2]: board type 200 (0002); one DDC, provisional
(HIS-02); sample rates limited to a subset of the [P2] list (pending 0004).

## Annex X2 — Clarifications of [P2]

| Id | [P2] text | G7250 reading |
|----|-----------|---------------|
| C1 | "Hardware to Host Protocol": "Byte order shall be MSB first (little Endian)" | MSB first (big-endian), consistent with "Host to Hardware Protocol" and with General byte 39 = 0 meaning Big-Endian (B2.5) |
| C2 | General, DDC-specific and High Priority packets: sequence number "set to 0x00000000"; DDC, DUC I&Q and memory-mapped packets: per-port counter; reset at "power on" (DDC packet) or "program start" (other packets) | G7250 sends per-port counters on all outgoing streams, reset at power-on and on stop; discovery reply always 0; incoming sequence numbers are not checked (B2.7) |
| C3 | Discovery reply byte 4: "0xFE (0xFF if running)" means a hardware configuration follows, "Appendix A"; Appendix C instead uses byte 4 = 0x02/0x03 and byte 11 = 255 | Not resolved; pending 0003. Until then the G7250 uses 0x02/0x03 only (B3.4) |
| C4 | General byte 37: DSP clock "as part of the Discovery response as specified in Appendix B"; Appendix B is "To be written"; Appendix C bytes 27–30 carry the DSP clock | DSP clock for board type 200 is given in the capability block (B3.8, pending 0003) |
| C5 | High Priority packet table: byte 4 "[1] = PTT0…[4] = PTT3"; text: "Bit [1] enables transmit … Bits [2] to [7] are reserved" | G7250 has one DUC: bit [1] is the transmit bit; bits [2]–[7] are not used (B5.5; 0005 rule 3) |

## Annex X3 — Conformance tests for B3 and B6

To be implemented in g7250-testbench, first against the reference model, then on the radio
(0001 item 5; design note §5 principle 6). Test ids are stable; descriptions are one line.

### Discovery (B3)

| Id | Description |
|----|-------------|
| T-B3-01 | Broadcast discovery to 255.255.255.255:1024 yields exactly one reply. |
| T-B3-02 | Directed discovery to the unit's IP:1024 yields exactly one reply. |
| T-B3-03 | Discovery to the subnet broadcast address yields exactly one reply. |
| T-B3-04 | Reply comes from port 1024 to the host's IP and source port. |
| T-B3-05 | Reply payload is 60 bytes; bytes 0–3 are zero. |
| T-B3-06 | Byte 4 is 0x02 when idle. |
| T-B3-07 | Byte 4 is 0x03 when running for host A and discovery comes from host B. |
| T-B3-08 | Byte 4 is 0x02 when running for host A and discovery comes from host A. |
| T-B3-09 | Bytes 5–10 equal the unit's link MAC address and are stable across power cycles. |
| T-B3-10 | Byte 11 is 200 (0xC8). |
| T-B3-11 | Byte 12 is 44. |
| T-B3-12 | Byte 13 matches the firmware version reported in the capability block (once 0003 exists). |
| T-B3-13 | Bytes 14–19, 24 and 25–59 are zero. |
| T-B3-14 | Byte 20 equals the number of DDCs that can be enabled and streamed. |
| T-B3-15 | Byte 21 matches the frequency encoding the unit accepts in High Priority bytes 9–12. |
| T-B3-16 | Byte 22 lists only formats that General byte 39 can select and that work. |
| T-B3-17 | Discovery is answered in Big-Endian format after a General packet selected another endian mode. |
| T-B3-18 | Discovery with non-zero bytes 5–59 is still answered. |
| T-B3-19 | Discovery is answered while streaming, without interrupting the stream. |
| T-B3-20 | Erase, Program and Set IP packets do not change firmware or IP configuration (until 0008). |
| T-B3-21 | No UDP port outside Table B2-1 answers or is open; port 1028 is closed. |

### RX IQ (B6)

| Id | Description |
|----|-------------|
| T-B6-01 | No DDC0 data before a High Priority packet with run set. |
| T-B6-02 | After General, DDC-specific and run, DDC0 packets arrive from port 1035 to the host's discovery source port. |
| T-B6-03 | Every DDC0 payload is 1444 bytes with 24-bit samples. |
| T-B6-04 | Bytes 12–13 are 24 and bytes 14–15 are 238. |
| T-B6-05 | Sequence numbers start at 0 and increase by one per packet, without gaps on a clean link. |
| T-B6-06 | Sequence counter restarts at 0 after stop and run. |
| T-B6-07 | Sequence number rolls over from 0xFFFFFFFF to 0 (reference model; forced counter). |
| T-B6-08 | Packet rate matches the selected sample rate (rate / 238 per second) within tolerance, per supported rate. |
| T-B6-09 | Each supported rate from 0004 (provisional 48, 96, 192, 384 ksps) streams without loss for a set duration. |
| T-B6-10 | An unsupported rate value in bytes 18–19 gives the behaviour defined in B11. |
| T-B6-11 | A known test tone at a set offset from the DDC0 frequency appears at the right frequency and sign (I before Q). |
| T-B6-12 | Samples are signed two's complement, MSB first (full-scale positive and negative test signals). |
| T-B6-13 | Clearing DDC-specific byte 7 bit [0] stops DDC0 data; setting it resumes. |
| T-B6-14 | Clearing the run bit stops all streams within a defined time. |
| T-B6-15 | Without C&C for more than one second in RUN, the unit goes to standby and stops streaming. |
| T-B6-16 | Changing the sample rate while running takes effect without a stop. |
| T-B6-17 | Fields listed as ignored in Table B6-2 have no effect on the stream. |
| T-B6-18 | A host that does not know board type 200 and never writes the register map still receives DDC0 data (0015). |

---

## Sources

- [P2] openHPSDR Ethernet Protocol V4.4: "Detailed operation"; "openHPSDR Host to Hardware
  Protocol"; "openHPSDR Hardware to Host Protocol"; Discovery packet; Erase, Program, Set IP
  Address packets; General packet bytes 5–39, 56–59; DDC specific packet bytes 4–1443; High
  Priority data packet bytes 4, 9–12, 329–332; Memory mapped registers from PC / from hardware;
  Discovery reply bytes 0–59; Command reply packet; DDC packet bytes 0–1443; Appendices A, B, C.
- [CH394] WCH CH394 manual 1, V1.2.
- [G7250-MAN] Xiegu G7250 Operation Manual rev 0.1.
- [TCI] Transceiver Control Interface 2.1 (not yet read).
- `analysis/ch394-network-budget.md`; `open-questions-his.md` (HIS-01, -02, -03, -04, -06,
  -07, -14, -15, -17).
- Decisions 0001, 0002, 0005, 0009, 0011, 0012, 0014, 0015, 0016, 0017, 0018; 0003, 0004,
  0006, 0007, 0008 pending.
- RFC 2119, RFC 8174 (BCP 14).

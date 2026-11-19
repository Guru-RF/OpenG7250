# Analysis — Network budget with a WCH CH394 Ethernet controller

- Date: 2026-11-19
- Trigger: ON8ST reports a WCH CH394 Ethernet chip in the G7250, from his own hardware
  inspection (2026-11-19). Not yet confirmed by the HIS. Which variant (CH394Q or CH394L) is
  not known.
- Status: analysis, not a decision.
- Outcome (ON8ST, 2026-11-19): the chip is a **CH394Q** (8 sockets, SPI), from his hardware
  inspection. P2 stays (0016). The socket budget is 8 of 8; see "Ways out" for how the
  management channel and any further ports fit.

## Sources

- [CH394] WCH, 以太网协议栈芯片 CH394 手册 1 (CH394 manual 1), version 1.2, wch.cn. Copy read
  from atta.szlcsc.com (`/upload/public/pdf/source/20251203/9EC0C6F644C6D345895781592F6A1E96.pdf`),
  2026-11-19. Chinese; 3 pages. Mainly about the CH394Q; the CH394L is described in a
  separate manual (CH394DS2), not read.
- [P2] openHPSDR Ethernet Protocol V4.4 (see `sources.md`).
- [P1-METIS] Metis – How it works V1.33 (see `sources.md`).

## What the CH394 is [CH394]

- An Ethernet "protocol stack" chip for microcontroller systems: built-in 10/100 Mbit/s MAC
  and PHY, IEEE 802.3, full/half duplex, auto MDI/MDIX.
- Built-in TCP/IP stack: IPv4, ARP, ICMP, IGMP, UDP, TCP. The CH394Q also has an IPv6 mode.
- **Sockets: 8 on the CH394Q, 4 on the CH394L**, usable at the same time. MACRAW and IPRAW
  modes are also supported.
- 32 KB internal RAM for transmit and receive, freely divided over the sockets.
- Host interface: SPI device interface up to **62 MHz** (mode 0 or 3, MSB first). The CH394L
  also has an 8-bit passive parallel interface.
- Wake-on-LAN, power-down mode, status LEDs, LQFP48.

## Consequences for the network interface

### 1. Link speed: 100 Mbit/s at most

The CH394 is 10/100 only [CH394]. Gigabit, which P2 hardware usually has, is not available.

### 2. Throughput: limited by SPI, not by the link

With SPI at 62 MHz at most [CH394], the raw data rate between the processor and the CH394 is
at most 62 Mbit/s, in both directions together, before command overhead. Whether the G7250
processor drives SPI that fast is a question for the HIS.

Payload of receive IQ in P2, 24-bit I and 24-bit Q (6 bytes per sample) [P2], for one DDC,
without UDP/IP overhead:

| Sample rate | Payload |
|-------------|---------|
| 48 ksps | 2.3 Mbit/s |
| 96 ksps | 4.6 Mbit/s |
| 192 ksps | 9.2 Mbit/s |
| 384 ksps | 18.4 Mbit/s |
| 768 ksps | 36.9 Mbit/s |
| 1536 ksps | 73.7 Mbit/s |

Transmit IQ in P2 is 24-bit at 192 ksps [P2]: 9.2 Mbit/s towards the radio.

So 1536 ksps is impossible (above both the SPI ceiling and close to the link speed).
768 ksps would use most of the SPI budget. 384 ksps or lower is realistic. The final limit
also depends on the ADC and clock (HIS) and goes into 0004.

### 3. Sockets: P2 needs close to 8

Each local UDP port on the radio needs its own socket in the CH394, unless MACRAW mode is
used. P2 ports on the radio side [P2]:

| Local port | Use |
|------------|-----|
| 1024 | discovery, General packet, programming, command replies |
| 1025 | DDC-specific packets in; High Priority status out |
| 1026 | DUC-specific packets in; microphone data out |
| 1027 | High Priority packets in; wideband data out |
| 1028 | DDC audio in |
| 1029 | DUC I&Q (TX IQ) in |
| 1035 | DDC0 I&Q out (one more port per extra DDC) |
| to be defined | memory-mapped registers in and out (0005); P2 gives the default as "xxxx" |

That is 7 sockets for standard P2 with one receiver, plus at least 1 for the G7250 register
map (0005): **8 in total**. That fits a CH394Q exactly, with nothing left for the management
channel (0001, spec section 10) or anything else. A CH394L, with 4 sockets, cannot carry P2
this way.

Protocol 1 uses a single port, 1024, for everything [P1-METIS]: 1 socket.

### Ways out, if P2 stays (0016)

- **Leave out ports the G7250 does not need.** If the G7250 has no audio codec path, port 1028
  (DDC audio) may not need a socket: incoming packets would then be dropped. Whether that is
  acceptable P2 behaviour must be checked against [P2] and against AetherSDR.
- **Put the memory-mapped registers on a port that already has a socket.** Not possible as
  such: P2 tells packet types apart by port, not by a type byte [P2]. It would be a deviation
  from P2.
- **Management channel on port 1024.** P2 already uses 1024 for programming [P2]. The
  management channel could reuse it instead of having its own port (0008).
- **MACRAW mode** [CH394]: one socket receives and sends raw Ethernet frames, and the
  firmware does IP and UDP itself. No socket limit, but the processor then carries the
  network stack, and all traffic goes over SPI as full frames.

## Open questions

For the HIS:

- Is it a CH394Q (8 sockets, SPI) or a CH394L (4 sockets, SPI or 8-bit parallel)?
- Which interface connects it to the processor (SPI or parallel), and at what clock?
- Which processor drives it, and does the current design use socket mode or MACRAW mode?

For ON8ST:

- Does this change the choice for P2 (0016)? With a CH394Q, P2 just fits (8 of 8 sockets).
  With a CH394L, it only works in MACRAW mode. P1 needs 1 socket.

## Addendum (2026-11-19): required and optional P2 streams, and TCI

Asked by ON8ST: which of the 8 sockets are required, which are optional, and is the socket
count also a problem for TCI (level 2)?

### The 8 sockets for G7250-P2

| # | Local port | Carries | For the G7250 |
|---|-----------|---------|---------------|
| 1 | 1024 | discovery, General packet, programming, command replies [P2] | required |
| 2 | 1025 | in: DDC-specific packets; out: High Priority status [P2] | required (receiver set-up; status incl. forward/reverse power) |
| 3 | 1026 | in: DUC-specific packets; out: microphone data [P2] | required for TX set-up; the microphone stream on it is optional |
| 4 | 1027 | in: High Priority packets (run, PTT, frequencies, drive); out: wideband data [P2] | required; the wideband stream on it is optional (enabled per ADC, General packet byte 23 [P2]) |
| 5 | 1028 | in: DDC audio (audio for the radio's own DAC/speaker) [P2] | **not offered**: the G7250 cannot play audio (ON8ST, 0017) |
| 6 | 1029 | in: DUC I&Q (TX IQ) [P2] | required for TX (0012) |
| 7 | 1035 | out: DDC0 I&Q (RX IQ) [P2] | required |
| 8 | to be defined | in/out: memory-mapped registers, the G7250 register map (0005) | required for the G7250 (ATU, antenna, TX arm, 0015) |

Optional streams: microphone (on socket 3), wideband (on socket 4) and DDC audio (socket 5).
Only DDC audio has a socket of its own, so it is the only one whose omission frees a
socket, for example for the management channel (0008). Whether the G7250 needs DDC audio
depends on whether it has a usable audio path for host audio (HIS).

### TCI (level 2)

TCI is a WebSocket protocol over TCP, with the transceiver as the server and several clients
at the same time [TCI] (README). With a socket chip such as the CH394Q, each open TCP
connection takes a socket of its own. That is how TCP sockets on such chips generally work;
[CH394] lists 8 sockets "usable at the same time" but does not spell out the TCP server
behaviour, so this is to be checked in the full CH394 documentation.

Consequences, as far as known now:

- TCI needs one socket per connected client, plus a listening socket if new clients must be
  able to connect while others are connected. TCI itself uses one port, so per client it is
  cheaper than P2.
- The number of TCI clients the G7250 can serve is limited by the 8 sockets minus whatever
  else runs at the same time (discovery, management channel).
- With a single owner (0011), level 1 and level 2 do not run at the same time. If both must
  still be reachable while one is active (for example for discovery or level selection),
  their sockets add up. That belongs in spec part A and in 0008.
- The CH394Q carries TCP but not WebSocket: framing, the HTTP upgrade and the TCI commands run
  on the G7250 processor. Part of the G6 question (compute, network stack).
- Audio and IQ over TCI also pass the SPI link, so the throughput limit of section 2 applies
  to level 2 as well.

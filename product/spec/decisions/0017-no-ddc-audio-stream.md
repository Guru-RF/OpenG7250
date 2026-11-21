# 0017 — G7250-P2 does not offer the P2 DDC audio stream (port 1028)

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19

## Context

In P2 the host can send left and right audio to the radio on port 1028 (DDC Audio packet),
"to be presented to the hardware audio DAC": 16-bit, 48 ksps, 64 samples per packet [P2].
The radio reports its speaker FIFO depth and speaker FIFO underflow in the High Priority
status packet, and declares "DDC Audio CODEC supported" in its full hardware description
(Appendix C, byte 59) [P2].

ON8ST: the G7250 main unit cannot play audio (2026-11-19). The firmware runs in the main
unit (0001). According to [G7250-MAN], the speaker output (SPK, 2 W into 4 Ω), microphone,
Morse key, USB and Bluetooth are all on the controller (head); the main unit has no audio
connector. On level 1 the DSP runs on the host (0011), so audio exists only on the host.

The Ethernet controller is a WCH CH394Q with 8 sockets [CH394] (ON8ST, hardware inspection,
2026-11-19). Standard P2 with one receiver plus the G7250 register map uses all 8, one of
them for port 1028 (`analysis/ch394-network-budget.md`).

## Options considered

### A. Do not offer DDC audio; no socket for port 1028 (chosen)

- For: the main unit has nothing to play the audio on, so the stream has no use.
- For: frees one of the 8 sockets, for example for the management channel (0008).
- Against: a host that sends DDC audio anyway sends packets to a port where nothing listens.
  How the CH394Q reacts to that (silently dropped, or an ICMP "port unreachable") is not
  described in [CH394] and has to be checked.

### B. Open a socket on port 1028 and discard what arrives

- For: a host that sends audio anyway gets standard behaviour from the network side.
- Against: spends one of the 8 sockets on nothing.

### C. Accept the audio and pass it on elsewhere (for example to the controller)

- Against: the speaker is on the controller [G7250-MAN]. Whether the main unit can send
  audio to the controller over the CTRL cable is not known (HIS). Rejected for now; to be
  revisited only if the HIS shows such a path.

## Decision

Option A. G7250-P2 does not offer the DDC audio stream. It opens no socket on port 1028 and
says so in its capability description.

## Consequences

- The G7250 reports no DDC audio support: in the full hardware description, if used, "DDC
  Audio CODEC supported" = 0 (Appendix C, byte 59) [P2], and in the capability block (0003).
- The speaker FIFO fields in the High Priority status packet [P2] are reported as 0, and
  speaker FIFO underflow is never set. To be fixed in spec part B.
- The AetherSDR G7250 backend must not send DDC audio. AetherSDR does send it to the ANAN-G2
  ("receive audio also plays through the radio's own speaker") [AETHER], so this is an
  explicit point in the annex "Changes needed in AetherSDR".
- Socket budget: 7 of 8 sockets for standard P2 plus the register map. One socket is free;
  its use is decided in 0008 (management channel).
- The P2 General packet lets the host set the DDC audio port (bytes 13–14) [P2]. The G7250
  accepts the field and ignores it.
- Microphone data (out on port 1026) is a separate question. The microphone is on the
  controller [G7250-MAN], so microphone data for the host is only possible if the controller
  passes it to the main unit over the CTRL cable (HIS).
- Spec part B lists the CH394Q's reaction to packets on a closed port, once checked.

## Sources

- Discussion with ON8ST, 2026-11-19.
- [P2] openHPSDR Ethernet Protocol V4.4: DDC Audio packet, General packet bytes 13–14, High
  Priority status (speaker FIFO depth and underflow), Appendix C byte 59.
- [CH394] WCH CH394 manual 1, V1.2.
- [AETHER] AetherSDR README, read 2026-11-19.
- [G7250-MAN] Xiegu G7250 Operation Manual rev 0.1: controller and main-unit interfaces,
  audio output.
- `analysis/ch394-network-budget.md`; decisions 0003, 0008 (reserved), 0011, 0016.

# Draft — notice to the openHPSDR project: board type 200

- Status: sent 2026-11-19 with a go from ON8ST, as
  https://github.com/TAPR/OpenHPSDR-Firmware/issues/6 (account on8st). Text below, with
  paragraphs unwrapped for GitHub.
  Edited the same day on ON8ST's request: 200 is now a proposal, and we use another value if
  openHPSDR prefers one. The text below is the current version.
- Decision: 0002.
- Proposed channel: an issue in github.com/TAPR/OpenHPSDR-Firmware. That repository holds
  the Protocol 2 documentation and is active (last commit 2026-11-13; 4 open issues, checked
  2026-11-19). Alternative: a message to the maintainer of the P2 document (N1GP / G8NJJ per
  the V4.x revision history), channel to be chosen by ON8ST.
- Account: the forge account of persona `on8st`.

---

**Title:** Proposed Protocol 2 board type 200 (0xC8) for third-party firmware (G7250-P2)

Hello,

We are writing new, independent firmware for the Xiegu G7250 transceiver. It speaks openHPSDR Protocol 2, following the openHPSDR Ethernet Protocol V4.4 document as closely as we can. Its interface is called G7250-P2.

So that hosts can tell it apart from existing boards, G7250-P2 needs its own board type in byte 11 of the discovery reply. We propose **board type 200 (0xC8)**, a value well away from the assigned range (0–6, 10), the reserved values (7–9) and the description markers (254, 255).

If you prefer a different number, for example the next value in your own sequence, we will gladly use that instead. Either way, we would be grateful if the value could be kept free of other boards in future revisions of the document, or listed in the board type table if you think that is useful.

Thank you for maintaining the protocol and its documentation.

73,
ON8ST

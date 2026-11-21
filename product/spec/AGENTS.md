# Agent instructions (g7250-spec)

This repository is on the **product side** of the G7250 project and is a clean
room. It defines the network interface of the new G7250 firmware.

1. Never read, search or list anything from the reverse-engineering side:
   `OpenG7250` (in particular `re/`), `g7250-emu`, `g7250-base`, `xiegu-g7250`,
   `G90tools`, or any decrypted stock firmware, disassembly or decompiler output.
   `.claude/settings.json` blocks these paths; do not work around it.
2. Allowed sources: the hardware-interface spec (`g7250-his`, once it exists),
   public protocol documents, public datasheets, the public G7250 product
   specifications and manual, and decisions recorded in this repository.
3. Cite the source of every technical statement.
4. Record design choices in `decisions/`, one file per decision.
5. The working language of the repository is English.
6. Local commits on branches only. No push, pull request or issue without an
   explicit go from ON8ST.
7. If a question can only be answered from the RE side, write it down as an open
   question for the HIS. Do not look for the answer yourself.

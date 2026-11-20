# 0028 — Installation, return to stock and updates, after the HIS

- Status: accepted (ON8ST, 2026-11-20, after the HIS impact analysis)
- Date: 2026-11-20
- Amends: 0024 (Decisions 1, 3, 4; R6), 0025 (R1, R3, R4; settles R5), 0008 (U-9, U-10).
- Applies to: `spec/network-interface.md` part A scope, A1.5, A1.8, A1.8a, Table A1-2, Annex X3;
  `design-note.md` §7, §8.
- Builds on: [HIS] `2a38b7f` sections 10 and 15; `analysis/his-2a38b7f-impact.md` §3.

## Context

The cleared HIS (HIS 10, HIS 15) gives these facts:

- The vendor bootloader occupies sector 0 (0x08000000–0x0801FFFF) and MUST NOT be written,
  nor the option bytes. An application image starts at 0x08020000 with its vector table there.
- The application area is sectors 1–7, 896 KiB, erased in 128 KiB sectors. The stock Main
  image V1.0.1 is 453 152 bytes (sectors 1–4). Two such images do not fit, and no RAM region
  holds a whole image.
- The only documented update path of the Main runs through the Control: files on the Control's
  USB drive, then the Control's update menu (VERIFIED, public vendor update guide V1.0.1). No
  other bootloader entry is known; the transport and the entry condition are unknown; whether
  the vendor bootloader starts an application it did not write is unknown. The rollback drill
  F1 on the real radio must prove the path before the first flash.
- New firmware MAY include an installer that writes an owner-supplied stock Main image from
  RAM, block by block, into sectors 1–7, without the Control.
- The FPGA configures itself from its own flash; the Main does not load it and MUST NOT touch
  that flash.

This makes 0025 R5 real for the first install, rules out a retained stock image beside our own
firmware, and rules out staging a stock image. ON8ST chose on 2026-11-20 among the options of
the impact analysis §3.3.

## Decision

1. **First install (stock → new): once through the vendor path** (option (a)). The first
   install, and a re-install after a return to stock, use the vendor's documented path
   through the Control (USB drive and update menu), with an image of this firmware in the form
   that path accepts. This is the only step that needs the Control. From then on, updates and
   the return to stock go through the Main. It depends on F1 showing that the vendor
   bootloader starts our image. If F1 finds a bootloader entry without the Control, a later
   decision may use it. Settles 0025 R5; replaces 0025 R4 and 0024 R6.
2. **Return to stock (new → stock): streaming installer, with the vendor path as recovery**
   (option (iii)).
   - Main way: the foreign-image upload of A1.8a becomes a streaming installation. The running
     firmware hands over to an installer that runs from RAM and writes the owner-supplied stock
     image block by block into sectors 1–7, without the Control (HIS 15).
   - This way is one-way and has no staging: once the first sector is erased, there is no
     return to this firmware. A transfer that breaks off, or a power loss, leaves no valid
     application; recovery is then the vendor path through the Control.
   - Recovery path (U-9): the vendor path through the Control. The G7250 never disables it
     (sector 0 and the option bytes untouched).
   - `RETURN_TO_STOCK` (retained image) and `ENTER_VENDOR_RECOVERY` are not supported: there is
     no room for a retained image, and no software entry into the vendor path is known. The
     command codes stay reserved; both commands get status 56.
3. **Own updates (new → new): A/B slots with our own boot stage.**
   - A small boot stage of this firmware sits at 0x08020000, where the vendor bootloader starts
     an application. It picks one of two image slots in the application area, runs the trial
     boot and the rollback (U-5, U-6), and is never updated over the network (U-7 applies to it).
   - The slot sizes, the location of configuration and log, and the boot record format are
     firmware design. The application area gives roughly 256 KiB per slot (impact analysis
     §3.2 item 4).
   - U-10 (feasibility of two slots and an atomic boot choice) is answered: feasible with this
     boot stage.
4. **No code in the spec phase.** The reference model and `g7250ctl` stay documented
   (READMEs, documentation) until the build phase. Their folders may be created with READMEs
   and documentation (ON8ST, 2026-11-20).

## Consequences

- Part A scope: "no installation step needs the controller" becomes "only the first install
  needs the controller".
- A1.5 I-2a: no retained stock image; `ENTER_VENDOR_RECOVERY` not supported.
- A1.8: staging is the other slot; boot stage; U-9 and U-10 answered; the FPGA component is
  dropped (the Main does not load the FPGA).
- A1.8a: "One installation path" rewritten; items 2, 3, 4, 8, 9 rewritten.
- Table A1-2: 0x0050 and 0x0051 always answer status 56.
- Annex X3: T-A1-54, T-A1-55, T-A1-58, T-A1-59 rewritten; T-A1-60 added (broken streaming
  transfer).
- `design-note.md` §7, §8.

## Sources

- [HIS] `2a38b7f`: HIS 10 (image placement), HIS 15 (stock recovery, update path, Main flash,
  installer, FPGA).
- `analysis/his-2a38b7f-impact.md` §3.
- ON8ST, 2026-11-20, answers to the questions on R5, the way back, updates and code.
- Decisions 0008, 0019, 0023, 0024, 0025, 0026.

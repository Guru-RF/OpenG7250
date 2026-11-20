# 0023 — The controller (head) is out of scope: it keeps its stock firmware

- Status: accepted (ON8ST, 2026-11-20: "Akkoord met alles", after his review of rc4). Section-level status lines below are superseded by this line.
  "clearly out of scope, but it must be stated"); detail choices (Decision, items 2–7)
  proposed, for ON8ST review.
- Date: 2026-11-20
- Applies to: `spec/network-interface.md` (part A introduction, A1.5, A3.7, B1.9),
  `design-note.md` §7, `open-questions-his.md` HIS-17.
- Builds on: 0001 (the firmware runs in the main unit), 0007 Decision 6, 0008 (C-5, U-9),
  0011, 0017.

## Context

ON8ST's review of rc4 (2026-11-20): nothing in the spec says what is done with the
controller unit (the head), although it is clearly out of scope. That has to be stated.

What public sources say:

- The G7250 is a main unit and a controller, separate units joined by a dedicated 15-pin
  cable on their CTRL interfaces [G7250-MAN]. The manual describes a main unit that can "be
  deployed independently" [G7250-MAN].
- The controller's System Information page lists separate versions: "APP: Controller
  firmware version", "FIRMWARE: Main unit firmware version", "FPGA: FPGA firmware version",
  "HARDWARE: Hardware version" [G7250-MAN]. So controller, main unit and FPGA carry separate
  firmware.
- Microphone, SPK, KEY, USB, the TF card slot and Bluetooth are on the controller; the main
  unit has no audio connector [G7250-MAN] (0017).
- The controller has a Factory Reset page that restores the factory settings
  [G7250-MAN]. The manual does not describe how firmware is updated.

What the spec already says: the firmware described is the main-unit firmware (0001; design
note §3); on level 1, controller inputs are reported and never key, and the controller has
no standalone operation while level 1 runs (spec A3.7; 0007 Decision 6, Resolved 6). What the
CTRL cable carries, and whether the main unit must keep the controller working, is HIS-17.
Whether the FPGA image is loaded by the main-unit firmware is HIS-18 (added by 0008).

## Options considered

### A. Controller untouched; the main unit treats it on a best-effort basis (chosen)

The project writes main-unit firmware only. The controller keeps its stock firmware. What the
new main-unit firmware does towards the controller depends on HIS-17.

- For: matches the scope of 0001 and ON8ST's statement.
- For: the controller is never put at risk by this project; a return to the stock main-unit
  firmware (0024) gives back the full stock radio, controller included.
- For: needs no knowledge of the controller's firmware or of the CTRL protocol beyond what
  the HIS gives (clean room, AGENTS.md rule 1).
- Against: the controller may show an error, or not work at all, with the new main-unit
  firmware. Then the radio is operated only over the network while our firmware runs.

### B. Also write or reflash controller firmware

- For: a controller that matches the new main unit.
- Against: a second firmware project, on hardware about which nothing beyond the manual is
  known; the controller has its own processor, display and audio path [G7250-MAN].
- Against: outside the scope ON8ST stated. Rejected.

### C. Require full controller functionality with the new main-unit firmware

- For: the radio keeps its front panel.
- Against: impossible to promise before HIS-17 says what the CTRL cable carries and what the
  controller expects. A requirement that cannot be met or tested is not a requirement.
  Rejected; revisited when HIS-17 is answered.

## Decision

Option A.

1. **Scope (accepted, ON8ST 2026-11-20).** The project replaces only the main-unit
   firmware. The controller (head) keeps its stock firmware and is not modified, reflashed or
   replaced by this project. The FPGA image is replaced only if HIS-18 shows that the
   main-unit firmware loads it; that is open.
2. **No writes to the controller's firmware (proposed).** The main-unit firmware MUST NOT
   send anything over CTRL that is meant to change, erase or update the controller's
   firmware, and MUST NOT forward such a request from the network.
3. **Do no harm on CTRL (proposed).** The main unit MUST NOT send anything over CTRL that
   could damage the controller or leave it unable to start with the stock main-unit
   firmware. Until HIS-17 says which signals and messages on CTRL are safe, the main unit
   drives on CTRL only what HIS-17 identifies as safe and otherwise leaves CTRL idle.
4. **Network operation does not depend on the controller (proposed).** Levels 1 and 2 MUST
   work with the controller disconnected, and with a controller that shows an error or does
   not respond (the main unit "can be deployed independently" [G7250-MAN]).
5. **"Not supported" is acceptable (proposed).** If HIS-17 shows that the stock controller
   cannot work with a different main-unit firmware, a controller that shows an error or an
   unknown state while our firmware runs is accepted. The owner regains the controller by
   returning to the stock firmware (0024). Identification reports the controller state as
   "unknown", "not detected" or "detected"; "unknown" until HIS-17 tells how the main unit
   can detect it (spec A1.5, I-6).
6. **What the main unit does towards the controller is level-dependent (proposed).** Display,
   buttons, audio and PTT over CTRL depend on HIS-17. Level 1: controller inputs that reach
   the main unit are reported and never key; controller TX functions are refused (spec A3.7;
   0007 Decision 6). Level 2: revisited at gate G6, with the HIS-17 answer (0011).
7. **Controller-dependent functions stay open (proposed).** The local factory reset (0008
   C-5) and a recovery path through the controller's TF card or USB (0008 U-9) depend on
   HIS-17; until then they are not counted on.

## Consequences

- Spec part A introduction and B1.9 state the scope; A1.5 gains the controller state (I-6);
  A3.7 is unchanged and points here.
- `design-note.md` §7 lists the controller firmware as out of scope.
- HIS-17 gets two questions: does the stock controller work with a different main-unit
  firmware, and what must the main unit do (or not do) on CTRL so the controller is not left
  in an error state or damaged.
- The owner may still update the controller with whatever the vendor offers for it; that a
  newer controller firmware works with our main-unit firmware is not guaranteed.
- No controller firmware, image or protocol knowledge is ever needed on the product side.

## Sources

- ON8ST, review of rc4, 2026-11-20.
- [G7250-MAN] Xiegu G7250 Operation Manual: construction (main unit and controller, CTRL
  cable), controller interfaces, System Information (APP, FIRMWARE, FPGA, HARDWARE), Factory
  Reset, independent deployment of the main unit.
- Decisions 0001, 0007, 0008, 0011, 0017, 0024; spec A3.7; HIS-17, HIS-18.

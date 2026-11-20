# 0024 — Switching between the stock firmware and the new firmware

- Status: accepted (ON8ST, 2026-11-20: "Akkoord met alles", after his review of rc4). Section-level status lines below are superseded by this line.
- Date: 2026-11-20
- Applies to: `spec/network-interface.md` A1.5, A1.8, new A1.8a, A1.9, A1.10, Table A1-2,
  Annex X3; `design-note.md` §7, §8; `open-questions-his.md` HIS-18, HIS-19.
- Builds on: 0008 (accepted; U-1 to U-10), 0018 (accepted; licences, owner control), 0022
  §10, §32, §40, §59, §61, §69, §86 (proposed), 0023.

## Context

ON8ST's review of rc4 (2026-11-20): not addressed is how the owner switches back and forth
between the factory (stock) firmware and the new firmware; from our own firmware it must also
be possible to upload the factory firmware again.

What is known:

- The controller's System Information page shows separate versions for the controller
  ("APP"), the main unit ("FIRMWARE"), the "FPGA" and the "HARDWARE" [G7250-MAN]. The manual
  does not describe how any of them is updated [G7250-MAN].
- The management channel already has a firmware update with integrity checks, a staging
  area, atomic activation, a trial boot with rollback, a downgrade flag, and the rule that a
  recovery path independent of our firmware must exist (spec A1.8; 0008 U-1 to U-10). It
  updates only images in our own package format; the boot loader is not updated through it
  (U-7).
- How the stock firmware is loaded, whether a vendor boot loader or update tool exists, and
  whether it survives our firmware, is not public. It is asked from the HIS (HIS-19); this
  project does not look for it (AGENTS.md rules 1 and 7). Flash size and layout, and whether
  the FPGA image is separate and loaded by the main-unit firmware, are HIS-18.
- 0018: the firmware is GPL-3.0-or-later and the owner keeps control (downgrades are
  allowed, 0008 U-8). The stock firmware is the vendor's; this project has no right to
  redistribute it.
- A stock image cannot confirm itself to our boot logic: the trial boot of A1.8 (U-6) would
  roll it back. A switch to stock therefore cannot be a trial boot.

## Requirements

- **R1 Reversible.** Installing the new firmware MUST be reversible: the owner can always
  return the main unit, and the FPGA image if our firmware replaced it (0023 item 1), to the
  stock firmware.
- **R2 Vendor path left intact.** The new firmware MUST NOT erase, overwrite or disable the
  vendor's own update or recovery path (vendor boot loader, the path the vendor's update tool
  uses), as far as HIS-19 shows one exists. Our update (A1.8) writes only our own image slots
  and staging area, and never the boot loader (U-7).
- **R3 A way back from our firmware.** The management channel offers a way back to stock,
  chosen below.
- **R4 Safety.** Every switch is a commanded reset (spec A1.9) under the same rules as a
  firmware update: refused while armed or keyed (status 50), refused during an update (status
  58), the P2 session and TCI connections end first, RF gone before the reset.
- **R5 Our secrets stay ours.** The management secret of our firmware MUST be erased before
  the switch, so that the stock firmware, or anyone reading the flash later, cannot recover
  it.
- **R6 Stock to new.** Switching from stock to the new firmware (the first install, and every
  re-install after a return) uses the path the owner uses for the first install. That path
  does not depend on the stock firmware's network protocol, is out of scope of the network
  spec and is documented separately, once HIS-19 shows it.
- **R7 Licence.** This project never redistributes a vendor image: no release, repository,
  reference model or test contains one. The owner supplies it (0018).

## Options considered for R3

### (a) `RETURN_TO_STOCK`: activate a retained stock image

The first install keeps the stock image (main unit, and FPGA if replaced) in a slot of its
own that our updates never touch; a management command makes it the boot choice.

- For: no image needs to be supplied; works without the vendor's tool and without opening
  the radio; the switch is as atomic as our own activation (U-5).
- For: the retained image is exactly what was on the radio, so no version or hardware
  mismatch.
- Against: needs flash room for the stock image beside our two slots or slot plus staging
  (U-10); unknown (HIS-18). Needs a boot choice that can select a non-G7250 image (HIS-19).

### (b) Foreign image through the update path

`UPDATE_BEGIN` with an explicit "foreign image" flag accepts an owner-supplied stock image as
an opaque component. The G7250 checks only what our wrapper says: target hardware id, length,
and the SHA-256 supplied by the owner. It never parses or checks the vendor format (clean
room).

- For: exactly what ON8ST asked: from our own firmware, the factory firmware can be uploaded
  again; also a newer stock version than the one the radio left the factory with.
- For: reuses the transfer, block CRC, staging and hashing of A1.8.
- Against: where a stock image must be written and how it is started is HIS-19; the G7250
  cannot check that the blob is a valid stock image, only that it is the one the owner meant.
  A wrong image leaves the radio without a working firmware; then only the vendor path (R2)
  or U-9 helps.
- Against: the owner needs a stock image; whether the vendor publishes one is not known.

### (c) `ENTER_VENDOR_RECOVERY`: reboot into the vendor's update or recovery mode

A management command restarts the main unit into the vendor's own update or recovery mode,
from which the vendor's tool reinstalls stock.

- For: the vendor's own path does the vendor's own format; nothing of it is in our code.
- Against: exists only if HIS-19 shows such a mode and a way to select it from software.

### (d) Only the vendor's own path, no help from our firmware

- For: nothing to build.
- Against: does not meet ON8ST's remark ("from our own firmware it must also be possible to
  upload the factory firmware again"). Kept as the fallback that R2 protects.

### Layering considered and not chosen

"(c) or (d) MUST, (a) SHOULD, (b) MAY": rejected because it does not give ON8ST's upload from
our firmware as a requirement.

## Decision (proposed)

A layered choice, all subject to HIS-18 and HIS-19:

1. **(b) MUST**: the update path accepts an owner-supplied stock image as a foreign image
   (spec A1.8a item 3). If HIS-19 shows that our firmware cannot write a stock image that the
   radio then starts, this item is revisited, as 0008 U-10 is for two slots.
2. **(d) MUST stay intact** (R2): the vendor's own path remains usable whatever our
   firmware does.
3. **(a) SHOULD**: if the flash has room (HIS-18), the first install retains the stock image
   and `RETURN_TO_STOCK` activates it.
4. **(c) MAY**: if HIS-19 shows a vendor recovery mode that software can select,
   `ENTER_VENDOR_RECOVERY` restarts into it.
5. Unsupported commands are answered with status 56 ("not supported in this firmware").

Details:

- **Activation is permanent, not a trial.** A stock image (retained or uploaded) is
  activated without trial boot and without rollback to our image (U-6 does not apply), since
  it cannot confirm itself. The request MUST carry an explicit confirmation: for (a) the
  SHA-256 of the retained image as reported by identification, for (b) the foreign-image flag
  in `UPDATE_BEGIN` and in `UPDATE_ACTIVATE`. A mismatch gets status 55 and changes nothing.
- **No downgrade check for a foreign image.** The G7250 cannot read a vendor version; the
  downgrade flag (U-8) does not apply. The hardware id in our wrapper MUST match (status 51).
- **Order** (A1.9, R4): status 50 while armed or keyed, 58 during an update; when accepted,
  the P2 session ends and all streams stop as for `UPDATE_BEGIN` (A1.8; 0022 §10), TCI
  connections are closed, then commanded-reset steps 2–5. The boot choice and the erasure of
  the secret are done only between steps 4 and 5, as for a factory reset (0022 §69); a refusal
  with status 59 changes neither.
- **Log.** The switch is logged with its source and the target (retained, foreign, vendor
  recovery) before the reset.
- **Identification** reports whether a retained stock image exists (its length and SHA-256,
  no vendor version) and whether `ENTER_VENDOR_RECOVERY` is supported (spec A1.5, I-2a).
- **Our configuration** other than the secret MAY stay in our own storage; the stock firmware
  does not use it. Where HIS-18 identifies the stock firmware's own settings area, our
  firmware SHOULD leave it untouched, so that the stock settings are still there after a
  return.

## Consequences

- Spec: new A1.8a "Return to stock firmware"; Table A1-2 rows 0x0050 `RETURN_TO_STOCK`
  and 0x0051 `ENTER_VENDOR_RECOVERY`; A1.5 I-2a; A1.8 U-9 points to A1.8a; A1.9 commanded
  reset and "one commanded reset at a time" list the new commands; A1.10 lists the switch as
  a write; tests T-A1-52 to T-A1-57. `spec/register-map.yaml` has to be regenerated
  (`tools/regmap.py`) for the two new commands.
- Design note §7 (vendor images not redistributed, controller firmware) and §8
  (reversibility).
- HIS-18 and HIS-19 get the questions below.
- A separate install guide (outside the network spec) describes the first install and the
  re-install once HIS-19 answers.
- After a return to stock, the controller works as with the factory radio, and its System
  Information page shows the stock FIRMWARE (and FPGA) version again [G7250-MAN]; the owner
  can check it there.

## Questions for the HIS

- HIS-18: flash room for a retained stock image beside our slots or staging; is the FPGA image
  separate, and loaded by the main-unit firmware.
- HIS-19: does a vendor update or recovery path exist, how is it entered, and does it survive
  our firmware; how are the first install and the return done; can the boot choice select a
  stock image; where must a stock image be written to be started.

## Sources

- ON8ST, review of rc4, 2026-11-20.
- [G7250-MAN] Xiegu G7250 Operation Manual: System Information (APP, FIRMWARE, FPGA,
  HARDWARE), Factory Reset; no firmware update procedure described.
- [FIPS180-4] (SHA-256).
- Decisions 0008, 0018, 0022, 0023; spec A1.8, A1.9; HIS-18, HIS-19.

# 0025 — One installation path on the main unit, in both directions, without the controller

- Status: proposed (for ON8ST review), 2026-11-20
- Date: 2026-11-20
- Amends: 0024 (accepted). Where this decision and 0024 differ, this decision applies once
  accepted.
- Applies to: `spec/network-interface.md` A1.8, A1.8a, Annex X3; `design-note.md` §7, §8;
  `open-questions-his.md` HIS-18, HIS-19.
- Builds on: 0008 (U-1 to U-10), 0018, 0023 (with its note of 2026-11-20), 0024.

## Context

ON8ST's decisions of 2026-11-20 (relayed by the openg7250 session on his request):

1. Option A of 0023 stands: the new main-unit firmware leaves the controller alone, CTRL
   stays idle, and the controller is not used as a front panel (recorded as a note in 0023).
2. New requirement: installing the factory (stock) firmware must be handled from the
   main-unit side. It must be possible to install the factory firmware in the same way as the
   new firmware, without the control unit. Both directions (stock → new and new → stock) use
   one installation path on the main unit, with no step that needs the controller.

What 0024 already has: a foreign-image upload through the update path of A1.8 (0024 option
(b), MUST), the vendor's own path left intact (option (d), MUST), a retained stock image
(option (a), SHOULD) and a reboot into a vendor recovery mode (option (c), MAY). Stock → new
was left to "the path the owner uses for the first install", documented outside the network
spec (0024 R6).

What is known and what is not:

- The TF card slot and USB are on the controller, not on the main unit
  [G7250-MAN]. A path through either needs the controller.
- The manual does not describe how any firmware is updated [G7250-MAN].
- Which interface the stock firmware or a stock boot loader uses to update the main unit,
  and whether that needs the controller, is not public. It is asked from the HIS (HIS-19);
  this project does not look for it (AGENTS.md rules 1 and 7). Flash room is HIS-18.
- While the stock firmware runs, our management channel does not exist. A stock → new path
  can therefore only be a path that exists under the stock firmware: the vendor's own boot or
  update path of the main unit, or a boot-loader path of the main unit (HIS-19).

## Requirements

- **R1 One path.** There MUST be one installation path on the main unit that is used for both
  directions: stock → new (the first install, and every re-install after a return) and
  new → stock.
- **R2 No controller step.** No step of that path MAY need the controller: no TF card, no
  USB, no display and no button on the controller. The path MUST work with the controller
  disconnected (consistent with 0023 item 4).
- **R3 Same way for both images.** While the new firmware runs, the path is the same for an
  image of the new firmware and for an owner-supplied stock image: the same transport (the
  management channel, A1.8), the same block transfer and staging, the same integrity checks
  (hardware id, block CRC-32, SHA-256 of the staged image), and the same commanded-reset
  order (A1.9). The only differences are those 0024 already sets and that follow from a
  stock image not being ours: the "foreign image" flag, no trial boot and no rollback, no
  downgrade check, and the erasure of the management secret before the switch.
- **R4 First install on the same path.** The stock → new direction MUST use that same
  main-unit path. Because the path must exist while the stock firmware runs, it can only be
  the vendor's own boot or update path of the main unit, or a boot-loader path of the main
  unit; which one exists, and whether it needs the controller, is TBD (HIS-19). This replaces
  0024 R6 ("first install documented outside the network spec").
- **R5 Open risk.** If the HIS shows that the only stock update path needs the controller,
  this requirement cannot be met as stated, and it comes back to ON8ST. Possible outcomes,
  listed without choosing:
  - a one-time first install through the vendor path (with the controller), and from then on
    the main-unit path for both directions; this holds for a re-install after a return to
    stock only if something of the main-unit path survives the return;
  - a project-provided main-unit boot loader, installed once, that offers the path under
    either firmware, only if HIS-18 and HIS-19 show that this is possible and reversible
    (the vendor's own boot loader can be put back); this conflicts with 0008 U-7 and 0024 R2
    as they stand and would need its own decision;
  - ON8ST relaxes R2 or R4 for the first install;
  - another outcome that the HIS answer makes possible.

## Options considered

### A. One main-unit path, both directions (chosen)

The management-channel update (A1.8) carries both image kinds (0024 option (b) becomes the
main mechanism); the stock → new direction uses the main-unit path that exists under the stock
firmware (HIS-19); nothing needs the controller.

- For: what ON8ST asked: the factory firmware is installed in the same way as the new
  firmware, from the main-unit side, without the controller.
- For: one set of checks and one safety order to specify and test; fewer paths that can
  brick the radio.
- For: works with a controller that is disconnected, absent or in an error state (0023
  item 5).
- Against: depends on HIS-19 for the stock → new direction; may not be achievable (R5).
- Against: the G7250 still cannot check that a stock image is valid, only that it is the one
  the owner meant (0024 option (b)).

### B. Keep 0024's layered set, including a vendor path through the controller

- For: nothing new to build; the vendor's own tooling does the vendor's format.
- Against: a step on the controller (TF card, USB, display, button) is exactly what ON8ST
  ruled out; two different ways for the two directions. Rejected by ON8ST (2026-11-20).

### C. A separate path per direction

For example: new → stock through the management channel, stock → new through whatever the
vendor provides.

- For: each direction uses what is easiest for it.
- Against: not "in the same way"; two paths to document, test and keep safe; the stock → new
  path may still need the controller. Rejected.

## Decision (proposed)

Option A.

1. **Main mechanism.** The foreign-image upload of 0024 option (b) (spec A1.8a item 3) is
   the main mechanism for new → stock. It uses the same commands, staging, checks and
   commanded-reset order as an update to a new image (R3).
2. **0024 options (c) and (d)** remain only where they need no controller step. (d), the
   vendor's own path, stays protected by 0024 R2 (never erased or disabled), but is counted
   as the installation path only if it meets R2 here. (c) `ENTER_VENDOR_RECOVERY` is offered
   only if the vendor recovery mode needs no controller step.
3. **0024 option (a)** (retained stock image, `RETURN_TO_STOCK`) is unchanged: it needs no
   controller and remains SHOULD where the flash has room (HIS-18).
4. **Stock → new** uses the main-unit path of R4, pending HIS-19; 0024 R6 is replaced.
5. **R5** is an explicit open risk; if it materialises, ON8ST decides among the outcomes.

## Clean room

The spec defines only our side: the transport (management channel), staging, integrity
checks and the safety order. The vendor image format and the behaviour of the stock boot
loader are HIS facts and are never specified in this repository; the open question is only
"what does the main unit need to accept a stock image" (HIS-19). No vendor image is ever
included (0024 R7; 0018).

## Consequences

- Spec A1.8a: the single path, no controller step, both directions; item 9 rewritten (first
  install pending HIS-19); items 1 and 4 qualified by R2. A1.8 points to the single path.
- Annex X3: T-A1-58 (new image and stock image installed through the same management path
  with the controller disconnected) and T-A1-59 (same checks and refusals for both kinds).
- Design note §7: the first install is no longer "outside" the spec; §8 reversibility line
  updated.
- HIS-19 gets the questions below; HIS-18 (flash room) is already asked.
- No new management command; `spec/register-map.yaml` is unchanged.

## Questions for the HIS

- HIS-19: which interface does the stock boot loader or the vendor update use to update the
  main unit? Does that path need the controller (TF card, USB, display, button)? What does
  the main unit need to accept a stock image (asked only as that; no format detail is recorded
  in this repository)?
- HIS-18 (already asked, 0008 and 0024): flash room for two images, staging and a retained
  stock image.

## Sources

- ON8ST, decisions of 2026-11-20, relayed by the openg7250 session.
- [G7250-MAN] Xiegu G7250 Operation Manual: controller interfaces (TF card, USB), no
  firmware update procedure described.
- Decisions 0008, 0018, 0023, 0024; spec A1.8, A1.8a, A1.9; HIS-18, HIS-19.

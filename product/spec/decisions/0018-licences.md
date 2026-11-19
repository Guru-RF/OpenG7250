# 0018 — Licences: CC BY 4.0 for documents, GPL-3.0-or-later for firmware, GPL-3.0 for the AetherSDR backend

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19
- Copyright holder: ON8ST.

This decision records a licence choice. The firmware licence is checked for compatibility
with the vendor SDK once that SDK is known (see Consequences).

## Context

The project has three kinds of output:

1. **Documents**: design note, network-interface spec, decisions, analyses, sources, HIS
   questions. Their purpose is an open network interface that others can implement
   (0001, 0016).
2. **Firmware** for the G7250 main unit.
3. **A G7250 backend for AetherSDR** (0013, 0016).

Known constraints:

- AetherSDR is licensed GPL-3.0 [AETHER]. Code we contribute there is GPL-3.0 (0016).
- The TCI repository is under the MIT licence [TCI]; whether that covers implementing the
  protocol is still to be checked (`sources.md`).
- The firmware will probably need vendor code for the processor and for the WCH CH394Q
  (SDK, drivers, examples). Their licences are not known until the processor is known
  (HIS-18).
- ON8ST asked that all copyright is held by ON8ST (2026-11-19).

For comparison, ON8ST pointed to the RF.Guru repositories (github.com/Guru-RF, checked
2026-11-19 through the GitHub API). Of 127 public repositories, 86 have no licence file. Among
the rest, MIT is the most common (21), used for the project's own firmware and apps (for
example SmartCW, SmartVFO, SmartFOX). GPL-3.0 (6) and GPL-2.0 (3) appear where a project builds
on GPL software (SVXLink, WM8960 drivers, Si5351Arduino). There are single cases of
CERN-OHL-S-2.0, LGPL-2.1, BSD-2-Clause and Apache-2.0. So RF.Guru has no single rule: MIT for
its own code, GPL where it inherits it.

## Options considered

### Documents

#### D1. CC BY 4.0 (chosen)

- For: anyone may copy, adapt and implement the spec, including commercially, with
  attribution to ON8ST. That fits the purpose of an open interface.
- For: widely understood, and compatible with publishing the spec next to code under any
  licence.
- Against: a third party may publish a changed spec without sharing the changes.

#### D2. CC BY-SA 4.0

- For: changed versions of the spec must stay open.
- Against: share-alike on a protocol document is unusual, and it makes reusing text in other
  people's documentation harder.

#### D3. All rights reserved

- Against: blocks exactly what the spec is for: other implementations and host support.

### Firmware

#### F1. GPL-3.0-or-later (chosen, subject to the SDK check)

- For: the same licence family as AetherSDR, and common in amateur-radio software.
- For: modified firmware that is distributed must come with its source. Nobody can close off
  an improved version.
- For: GPL-3.0 requires installation information for consumer devices. For open firmware on
  a radio that is a feature, not a cost.
- Against: vendor SDKs and drivers often come under licences that do not allow combination
  with GPL code. If that is the case for the G7250 processor or the CH394Q, F1 is not
  possible.
- Against: differs from RF.Guru's usual MIT for its own firmware.

#### F2. Apache-2.0

- For: permissive, with an explicit patent licence. Combines with most vendor SDK licences.
- Against: anyone, including a manufacturer, may ship closed modified versions.

#### F3. MIT

- For: the simplest permissive licence, and RF.Guru's usual choice for its own firmware.
- Against: as F2, and without the patent clause.

### AetherSDR backend

#### A1. GPL-3.0 (fixed)

- AetherSDR is GPL-3.0 [AETHER]. There is no other option for code inside it.

## Decision

- Documents in this repository: **CC BY 4.0**, © ON8ST.
- Firmware: **GPL-3.0-or-later**, © ON8ST. If the vendor SDK or drivers needed for the main
  unit cannot be combined with GPL code, the firmware uses **Apache-2.0** instead (F2), and
  this decision is revised.
- AetherSDR G7250 backend: **GPL-3.0**, as AetherSDR, with ON8ST as copyright holder of the
  contributed code.

## Consequences

- `LICENSE.md` in this repository states CC BY 4.0 and the copyright holder.
- Published pages derived from these documents (such as the illustrated design note) carry
  "© ON8ST" and the CC BY 4.0 notice.
- When the processor and its SDK are known (HIS-18), the SDK and CH394Q driver licences are
  checked against GPL-3.0 before any firmware code is written. Result recorded here.
- Third-party code in the firmware keeps its own licence and is listed.
- Contributions to AetherSDR still need a go from ON8ST (AGENTS.md rule 6).
- If ON8ST later wants to align the firmware with RF.Guru's usual MIT, that is a revision
  of this decision.

## Sources

- Discussion with ON8ST, 2026-11-19.
- [AETHER] AetherSDR README (GPL-3.0); [TCI] ExpertSDR3/TCI repository (MIT). See
  `sources.md`.
- github.com/Guru-RF, licence metadata of the public repositories via the GitHub API,
  2026-11-19.
- Decisions 0001, 0013, 0016.

# 0014 — One TCI profile for AetherSDR (level 1) and the firmware (level 2)

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19

## Context

Level 2 is a TCI server in the radio with on-board DSP (0011). Spec part C describes it.
On level 1, AetherSDR is the integration route, and what it offers to third-party
applications (TCI, CAT, rigctl, audio) is AetherSDR's own responsibility (0013). 0013 left
open whether AetherSDR's host-side TCI has to match spec part C (handover, open question 1).

TCI is a published protocol with its own versions and terms of use. Which version we follow
has not been checked yet (0011, Consequences). It will be recorded in `sources.md` as [TCI].

## Options considered

### A. One TCI profile, followed by both (chosen)

Part C defines one "G7250 TCI profile": the TCI version, the commands and parameters it
uses, and how G7250-specific functions (ATU, antenna, safety state, active level) map onto
TCI. AetherSDR on level 1 and the firmware on level 2 both implement that profile.

- For: an application written against the profile works on both levels without change. A
  user can move from level 1 to level 2, or back, without reconfiguring applications.
- For: the profile can be specified and tested on level 1 now, long before gate G6 decides
  whether level 2 can be built. Part C then stops being a placeholder (0011) and becomes the
  test target of AetherSDR.
- For: the conformance tests for part C (0001, spec section 12) serve both implementations.
- Against: AetherSDR is bound to a spec it does not own. Every change to the profile also
  becomes work for AetherSDR.
- Against: level 2 may not be able to support everything AetherSDR can do on the host,
  because of limited compute. The profile then has to stay at what level 2 can carry, or
  mark parts as optional.

### B. Independent: part C covers only the firmware

Part C only covers the TCI server in the firmware. AetherSDR offers whatever TCI it
already offers or chooses to offer.

- For: no coordination between the spec and AetherSDR, and no constraint on AetherSDR.
- Against: two TCI dialects for the same radio. Applications may behave differently per
  level, and users would have to find that out for themselves.
- Against: part C stays untestable until after G6, because there is no implementation to
  test against before then.

### C. Decide after gate G6

Leave the question open until level 2 is known to be feasible.

- For: no work spent on part C if G6 shows that level 2 cannot be built.
- Against: AetherSDR's TCI behaviour becomes fixed in the meantime without our input. Making
  it match afterwards costs more than agreeing a profile up front.

### D. Part C copies what AetherSDR already does

Treat AetherSDR's existing TCI behaviour as the reference, and write part C as a description
of it.

- For: no extra work for AetherSDR.
- Against: AetherSDR's behaviour is not a public specification we can cite (AGENTS.md
  rules 2 and 3). The spec would follow an implementation instead of the other way round,
  against the "spec first" principle (0001, design note item 5).
- Against: AetherSDR's TCI behaviour has not been checked against public sources. It is not
  known yet how far it matches the published TCI protocol.

## Decision

Option A. Spec part C defines one G7250 TCI profile. AetherSDR's host-side TCI on level 1
and the firmware's TCI server on level 2 both conform to it.

## Consequences

- Part C is written before G6, as the TCI profile for level 1. Requirements that only make
  sense on level 2 (on-board DSP limits, ownership by the firmware) are marked as such.
- The profile is based on a published TCI version. That version and its terms of use must
  be checked in `sources.md` before part C is written (0011).
- Functions that level 2 may not be able to carry are marked optional in the profile, with a
  way for the application to discover which ones are available.
- The annex "Changes needed in AetherSDR" (0001, spec section 13) gets a section on the TCI
  profile.
- What AetherSDR offers outside TCI (CAT, rigctl, audio) is still not part of this spec
  (0013).

## Sources

- Discussion with ON8ST, 2026-11-19.
- Decisions 0001, 0011, 0013.
- TCI protocol — version and terms of use to be listed in `sources.md` as [TCI].

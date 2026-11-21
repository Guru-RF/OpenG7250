# 0032 — Own control of the internal ATU; bypass until its parameters are measured

- Status: accepted (ON8ST, 2026-11-20, answers to the HIS impact analysis §4, relayed by the openg7250 session and confirmed in this session)
- Date: 2026-11-20

## Context

HIS 85 (`2a38b7f`): the internal ATU is three 8-bit latches driven by the Main (network style
and bypass, two reactance banks); no safe value is known. There is no ATU controller: tuning,
memory and reporting are the firmware's job. The spec already defines the ATU tune cycle
(A3.9b) and `ATU_TUNE`/`ATU_STATE`.

## Decision

1. The firmware controls the ATU itself (not bypass-only). The tune cycle of A3.9b stands.
2. The ATU parameters (latch meanings and safe values, tune power, tune algorithm limits,
   relay timing) depend on HIS-08 measurements and are listed in the "pending hardware" annex.
3. Until they are set, the ATU stays in bypass (latches unwritten, HIS 85), `ATU_STATE` reads
   0, and `ATU_TUNE` = 1 is rejected with the new write reject reason 11 `NOT_CALIBRATED`; this
   matches transmit staying disabled until calibrated.

## Consequences

- A3.9b, `ATU_TUNE` in the register map, Table B8-3 (write reject reason 11), part C
  `G7250_ATU_TUNE`.
- Pending-hardware annex: ATU parameters.

## Amendment

- 0035 (amendment after the review of 2026-11-21): while the latches are unwritten the ATU
  state is not known, so `ATU_STATE` reads 5 (unknown), not 0 as item 3 says.

## Sources

- [HIS] HIS 85 (`2a38b7f`); ON8ST, 2026-11-20; decisions 0005, 0007, 0022 §22.

# HIS gate review 4 (his/next 2419c70)

**Scope.** `git diff his/integrate his/next -- his` (his/integrate at 54381c5,
his/next at 2419c70): review-3 nits, the README status, and HIS-02 frame offsets
from the emulator probe. RE detail checked: `re/analysis/docs/his-02-nco-probe.md`.
Reviewer: the gate session (as reviews 2 and 3).

## Findings

### 80 — the 0x01 frame (HIS-02)
- Only interface facts are added: a 24-byte frame, status flags in byte 0,
  three big-endian 32-bit NCO words at byte offsets 1, 5 and 19, bytes 9–18
  other fields including per-rate calibration (meanings unknown), and byte 23
  most likely the rate index.
- **Sources and tags.** The offsets are the bytes the stock image writes on the
  bus in the emulator. The model only records them, so this is observed output
  of the stock code, not a model choice, and it agrees with the disassembly
  (g7250-base: "three big-endian 32-bit NCO words"). HIGH is justified. "Byte 23
  most likely the rate index" (MEDIUM) rests on one observed value (0x03) and
  the g7250-base field order, so MEDIUM fits.
- **No leak.** `his/` contains no VFO/RIT reading, no boot NCO values
  (7.100/14.150 MHz), no raw frame bytes and no 0xC1 flag value (checked by
  grep). The roles per offset are marked unknown. The stock values, the VFO
  reading and the boot-hang hypothesis stay in the RE note, where they belong.
- The evidence line says the offsets come from the emulator probe and agree
  with the disassembly. OK.
- **Stale text (required, H1).** The Open list in 80 still says "Byte offsets of
  the 0x01 frame, and the meaning and safe values of its per-rate calibration
  bytes: unknown". That now contradicts the HIGH offsets in the command table.
  Change it to: "The meaning of bytes 9–18 and the safe values of the per-rate
  calibration bytes: unknown; the meaning of the individual flag bits in byte
  0: unknown."
- **Advisory.** "Timing / data" says the FPGA takes "a spectral-inversion flag
  in the frame", but its byte and bit are not located. Add "(position in the
  frame unknown)".

### 90
- The HIS-02 row matches 80 (offsets HIGH, roles unknown). OK.
- The IWDG row is now part of the table; PB6/PB7 are tagged VERIFIED
  (g7250-base peripherals). The review-3 nits are done.

### README
- The status "Cleared at d0a39b0 (review 3) … later changes go through the
  gate first" is correct for what has been cleared so far. Once this review
  clears, the status must name the newly cleared commit and review 4.

## Verdict

**NOT CLEARED**: one required item, H1 (the stale Open line in 80), plus the
README status update when the HIS is cleared. Everything else in the diff is
clean: interface facts only, sourced and tagged. A check of the H1 diff alone
is enough to clear.

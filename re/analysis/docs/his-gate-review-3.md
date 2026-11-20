# HIS gate review 3 (f7c4d7d)

**Scope.** `git diff 2a38b7f f7c4d7d -- his`: answers to the product side's
questions HIS-02/06/07/11/12/15/16/17/19/20, and the new `his/90-needs-hardware.md`
with a hardware step order. Read as new material. Reviewer: the gate session
(same as review 2).

**Sources checked.** g7250-base `main_unit/docs/{peripherals,network}.md`,
`main_unit/analysis/peripherals/gpio_map.csv`, `docs/atu.md`,
`docs/hardware_test_plan.md` (Tier 3); `re/analysis/docs/his-18-19-update-path.md`.

## Per-section findings

### 10 — SWD and RNG
- SWD on PA13/PA14 is from the ST datasheet. "The factory application does not
  reconfigure them" checks out: neither pin is in `gpio_map.csv`. A HIGH tag is
  fair, since a MODER write outside HAL init cannot be fully excluded. OK.
- RNG present on both candidate parts (ST datasheet), HIGH with the part MEDIUM.
  OK.
- **A (advisory):** the IWDG is not mentioned anywhere in the HIS. If the
  IWDG1_SW option byte selects a hardware-started watchdog, new firmware must
  service it from reset. The source rates the setting MEDIUM/unknown (test plan
  T3.1). Add an "Open: IWDG start mode (option byte), read in step 2" to 10 and
  90.

### 15 — vendor guide citation, pointer to 90
- Citing the public vendor guide and its public download page is provenance and
  is needed for recovery. OK.

### 20 — pointer to 90
- OK.

### 40 — MAC address
- "The CH394 provides the MAC in its own register set; the factory firmware does
  not store one in the EEPROM" (HIGH): matches g7250-base `network.md` ("the MAC
  is read from the CH394, not from the EEPROM"). The negative statement about
  stock storage tells the product only that the EEPROM holds no MAC it might
  need. That is acceptable, and the EEPROM is read-only anyway. Checking
  uniqueness is correctly left open. OK.

### 80 and 90 — NCO words (HIS-02)
- **LEAK (required, G1).** "one the main VFO (including RIT) and one the other
  VFO" describes what the stock firmware puts into the words: its VFO model and
  RIT feature (g7250-base: TRX+0x208 = main VFO + RIT + transverter offset).
  That is stock behaviour, not the FPGA's interface. The hardware-side fact is
  only that the frame carries three NCO phase words, of which two set tuning
  frequencies of the receive path (MEDIUM), with the third word's role and the
  word order unknown. Remove "main VFO", "other VFO" and "RIT" from 80 and from
  the HIS-02 row in 90.

### 85 — antennas
- Two rear ports ANT1/ANT2, SO-239, 50 Ω: public manual/teardown, VERIFIED. OK.
- Antenna select on PD13 bits 4–5 (MEDIUM): matches g7250-base `docs/atu.md`
  (MEDIUM). "Leave the latch unwritten" is consistent with the rest of 85. OK.
- Consequence for 90, see G6.

### 90 — open points
- The table of open points is fine. The HIS-07/11/12 row correctly keeps stock
  timing and calibration out.

### 90 — safe order of the hardware steps

The order is right (locate → read option bytes → back up → only then F1), and
the key rules are present: SWD read-only in hot-plug mode without halt, never
"Apply", the RDP 1→0 erase and the permanence of level 2, and never sector 0. It
also matches the g7250-base Tier 3 plan. Gaps that can still cost the unit or
the clean room:

- **G2 (required) — mass erase.** Step 4 writes "to 0x08020000 only (never
  sector 0)". Programming tools offer, and some default to, a full-chip / mass
  erase before programming, which wipes sector 0 regardless of the target
  address. State explicitly: no full-chip or mass erase; erase only the sectors
  the image needs (1…n) by sector erase; before and after, read back sector 0
  and compare it with the step-3 backup.
- **G3 (required) — test image.** "Blinks a known output" — no output of the
  Main is known to be safe to toggle (85 lists PD12/PA12 and the T/R lines as
  unknown or RF-relevant). Instead: the test image toggles nothing outside the
  safe state of 85. It reports that it runs through the Main debug console
  (USART1 TX, PB6/PB7 AF7, VERIFIED in g7250-base) or through a RAM counter read
  by SWD. It also drives PH9 high from reset, because under H1 the unit
  otherwise drops power (20).
- **G4 (required) — Control and clean room.** Step 3 backs up "the Main and the
  Control", but step 2 reads only the Main's option bytes. Reading the Control's
  RDP needs its own step 2 (expected DEV_ID 0x450), and its SWD access point is
  unknown too. Either add the Control to steps 1–2 or limit step 3 to the Main.
  Also state that the dumps are RE-side material: they are kept locally, outside
  any repository, never given to the product side, and analysed (for the
  bootloader entry) only on the RE side under CLEANROOM.
- **G5 (required) — fallback.** Step 4 restores through the vendor path, which
  is the thing F1 is testing. State the safety net: if the vendor path fails,
  restore the application sectors 1–7 from the step-3 backup by SWD. That
  backup exists only at RDP 0, which is why step 4 by SWD is allowed only
  there.
- **G6 (required) — dummy loads.** "Dummy load on the antenna port": the radio
  has two ports, and which one is selected (PD13 bits 4–5) is unknown, as is the
  latch state after reset. Put a dummy load on both ANT1 and ANT2.
- **A (advisory):** step 2 should also read CPUFREQ_BOOST and the IWDG
  freeze-in-debug bits (the Tier 3 plan does). A connection that fails because
  of RDP level 2 should be recorded as such, without retrying under reset.

## Leak check (summary)

No code, stock addresses, register values, timing or protocol content was
added. The one leak is G1 (VFO/RIT semantics of the NCO words).

## Verdict

**NOT CLEARED.** Required: G1 (80, 90) and G2–G6 (90). The sections already
cleared stay cleared; the items are limited to the NCO wording and the step
order in 90. A check of the diff of those changes is enough to clear.

## Changes for review 3

All in `d0a39b0` on his/integrate (review brought in as `bc1bba7`, cherry-pick
of `684797c`).

| # | Where | Change |
| --- | --- | --- |
| G1 | 80, 90 | "main VFO (including RIT) / other VFO" removed; two of the three NCO words set receive-path tuning frequencies (MEDIUM); third word and order unknown. |
| G2 | 90 step 4 | No full-chip or mass erase; sector erase of 1…n only; sector 0 read back before and after and compared with the backup. |
| G3 | 90 step 4 | Test image toggles no pin beyond the safe state of 85, drives PH9 high from reset, reports via USART1 (PB6/PB7) or a RAM counter over SWD. |
| G4 | 90 step 3 | Control backup only after its own SWD location and option-byte read (DEV_ID 0x450), else Main only; dumps are RE-side material, never for the product side. |
| G5 | 90 step 4 | Fallback: restore sectors 1–7 from the step-3 backup by SWD if the vendor path fails. |
| G6 | 90 | Dummy loads on both ANT1 and ANT2. |
| A | 10, 90 | IWDG start mode as an open point; step 2 also reads CPUFREQ_BOOST and the IWDG freeze bits; no retry under reset at RDP 2. |

Status: ready for the check of this diff.

---

## Final check (diff bc1bba7..d0a39b0, his/)

| Item | Result |
| --- | --- |
| G1 (80, 90) | applied: no VFO/RIT semantics are left; "two of them set tuning frequencies of the receive path (MEDIUM)". The emulator alternative was dropped from the HIS-02 row. |
| G2 (90 step 4) | applied: no full-chip or mass erase; sector erase 1…n only; sector 0 read back before and after and compared with the backup. |
| G3 (90 step 4) | applied: the test image holds the 85 safe state, drives PH9 high from reset, toggles no other pin, and reports through USART1 or a RAM counter read over SWD. |
| G4 (90 step 3) | applied: the Control is backed up only after its own steps 1–2, otherwise the backup covers the Main only; the dumps are RE-side material under the clean-room rules. |
| G5 (90 step 4) | applied: the step-3 SWD backup is the fallback. |
| G6 (90) | applied: dummy loads on both ANT1 and ANT2. |
| Advisories | applied: IWDG start mode is open in 10 and 90; step 2 also reads CPUFREQ_BOOST and the IWDG freeze bits; no retry under reset at RDP 2. |

Nothing in the diff adds stock behaviour, and every step stays read-only except
the guarded sector writes in step 4.

Nits (non-blocking, fix in passing):
- 90: the "IWDG start mode" row sits after a blank line, so it renders as a
  stray line rather than as a row of the table above; remove the blank line.
- 90 step 4: give the USART1 pins (PB6/PB7 AF7) their tag (VERIFIED, g7250-base
  peripherals).

### Verdict (final)

**CLEARED** at d0a39b0. The announced HIS-02 interface addition to 80 from the
emulator probe is not covered by this check and needs its own.

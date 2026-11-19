# M8c — R0 report: can the Main power on headless?

**Risk R0** (spec §3.8, §14.2) is the largest risk on the critical path: if the
Main only switches on via the panel power key, and that key runs over the CTRL
cable, then headless operation (EH) without a panel is impossible as-is. This
report operationalises the two power hypotheses with the PowerModel, predicts
what the owner will observe in a few safe tier-0 cold-start checks, and hands
the owner a ready-to-run observation protocol.

Scope follows §3.8.7 steps 1–3. Step 1 (emulator) is done here as a **model
prediction**; the stock-image confirmation is the one remaining piece and waits
for the decrypted Main image (see "Status" below). Steps 2 (docs) and 3 (owner
observations) are summarised with the protocol attached.

## The two hypotheses (§3.8.2)

| | **H1 — hardware latch on the Main** | **H2 — MCU always powered on a standby rail** |
| --- | --- | --- |
| Power-up | The key switches the regulator on in hardware; the MCU starts and holds power with PH9. The system reset at the end of shutdown releases PH9 and power drops. | The MCU (or a standby part) is powered whenever 13.8 V is present. The firmware (likely the bootloader) waits for PH5; PH9 switches the rails for the rest of the radio. |
| No panel at DC-on | Nothing happens unless (a) a hardware **auto-start on DC-on** exists, or (b) as a last resort a key-emulation contact on the CTRL connector (owner decision). | All in firmware: the NF can decide (always-on). |

Both are HYPOTHESIS and are not fully mutually exclusive. The emulator cannot
settle H1 vs H2 — that lives in hardware/the bootloader, outside the images —
but it predicts each one's behaviour so a tiny set of real-radio observations
can decide.

## PW-1 — PowerModel predictions (§3.8.6 test PW-1)

Driven by `models/system/power_model.py` via `harness/g7250emu/r0_sim.py`
(`python3 harness/g7250emu/r0_sim.py`). Panel removed, no Control, stock
behaviour (PH5 not ignored). CH394 link/ping timing is HYPOTHESIS (the link
comes up a few seconds after DC-on, after PH9+1s / AXP+1s / EEPROM / VC6 /
CH394).

| Scenario | Predicted outcome |
| --- | --- |
| **H2, PH5 high** (pull-up, no panel) | Boots fully; LAN link comes up; **pings** on the forced default IP; stays up. |
| **H2, PH5 pulled low after boot** | Boots, link + ping, then after ~1 s low a **power-off request**: safe state, CH394 back in reset (link drops, no ping), waits for PH5 high — with no panel it **stays off**. The stock pitfall. |
| **H1 without auto-start**, no panel | **Never powers** — no link, ever. |
| **H1 with auto-start**, PH5 high | Boots fully; link + ping; stays up (same as H2). |
| **H1 with auto-start**, PH5 low after boot | Same pitfall as H2. |

**Reading:** a LAN link that comes up and then drops after a few seconds (and
stays down until DC off/on) is an *expected* pattern (the pitfall), not a
failure. A link that never appears points to **H1 without auto-start**. A link
that comes up and *stays*, answering ping, is consistent with **H2** or **H1
with auto-start** — i.e. headless operation is feasible.

## What a tier-0 observation proves (§3.8.3)

- **"LAN link comes up"** only proves the CH394 is out of reset.
- **A ping answer to 192.168.3.199** from a host on 192.168.3.x/24 proves the
  application is running (the CH394 answers ping itself, but only after the app
  has given it the IP). After a stock power-off the CH394 is in reset — no ping.
- The forced defaults (IP 192.168.3.199, gw .1, mask /24, base port 50001) come
  from public upstream issue #1 (HYPOTHESIS/MEDIUM); an ARP capture confirms them.

## Owner protocol — tier-0 cold-start observations (ready to run)

**Fixed procedural rules for every headless stock test (normative):**
1. **Dummy load** (50 Ω, ≥ 100 W) on every antenna port the radio can select,
   before DC-on.
2. **No wfview and no other CI-V/LAN client that can assert PTT** connected or
   active while the test runs (upstream #2: network PTT may not release on
   session loss; documented network hold up to 60 s). Passive captures, ping and
   ARP only.
3. **Never connect/disconnect the CTRL cable with DC on.**
4. **Never press Enter on a Main console** (service menu).
5. **Logbook**: date, versions, setup, every observation.

| # | Observation | Outcome → hypothesis |
| --- | --- | --- |
| **T0-P1** | Supply current with DC on and the radio "off" (normally switched off via the panel key, panel connected). Read the bench-supply display only. | ≈ 0 mA → **H1**. Tens of mA → **H2**. (The display must be able to show tens of mA.) |
| **T0-P2** | **CTRL disconnected, DC on:** does the Main's Ethernet link come up on the switch (LED/port status)? | No link → H1 without auto-start, or H2 waiting on PH5. Link up → CH394 out of reset (Main started). Link up then gone after a few seconds → the stock pitfall. |
| **T0-P3** | With a link at T0-P2: a host on 192.168.3.x/24 pings 192.168.3.199; passive ARP/broadcast capture. | Ping answer → the application runs. No answer with a link up → app not that far yet, or already switched off (pitfall); repeat with a timeline from DC-on. |
| **T0-P4** | Repeat T0-P1 with CTRL disconnected. | Compare: panel consumption vs the Main's standby. |

**Closing:** DC off, CTRL cable back, DC on, verify normal operation.

**Decision mapping (§3.8.7 step 3):**
- **H2, or H1 with auto-start** → EH is feasible on hardware; the NF-Main
  implements always-on and sleep/wake (§3.8.4, P-1..P-11).
- **H1 without auto-start** → the stock panel stays physically connected during
  HIL purely to switch on, under the ES rules; a key-emulation contact on the
  CTRL connector is the last resort (owner decision).

## Status

- **Done (model):** PW-1 predictions for H1/H2 × PH5 variants, the T0 mapping,
  and this protocol — all from the PowerModel, self-tested
  (`r0_sim.py --selftest`, in the M1 smoke gate).
- **Pending (image):** the PW-1 *emulator confirmation* — boot the decrypted
  stock Main under the PowerModel and check it matches these predictions (does
  it reach A1, drive PH9, bring the CH394 up, write the default IP, and react to
  a PH5-low as predicted). This is wired and waits only for the image
  (docs/M1-status.md).
- **Owner:** T0-P1–T0-P4 can be run on the real radio at any time; the results
  are the HIL facts that decide R0 and set gate F0 (§10.3).

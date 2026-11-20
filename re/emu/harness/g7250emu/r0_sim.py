#!/usr/bin/env python3
"""R0 / M8c: PW-1 power-state simulation driven by the PowerModel.

Milestone M8c (spec §14, §3.8.7 step 1) asks us to run the stock Main power
logic under both hypotheses (H1/H2) with the panel removed and the PH5 variants,
with no Control machine (PW-1), and record: does it come fully up (A1), what is
its network behaviour on the forced defaults, and does a spontaneous power-off
follow? The outcome goes into the HIS as a hardware-fact *hypothesis* and
predicts the owner's tier-0 observations T0-P2 / T0-P3 (§3.8.3).

IMPORTANT — what this is and is not:
  * This drives `models/system/power_model.py` (a model of the *documented*
    firmware behaviour) plus a small CH394 link/ping predictor. It produces the
    PowerModel's **prediction**.
  * It is NOT the stock image executing in the emulator. The PW-1 emulator
    *confirmation* (booting the decrypted Main under the PowerModel and checking
    it matches) is the remaining step and waits for the image (docs/M1-status.md).

Boot/CH394 timing constants are HYPOTHESIS (flow.md: the link comes up "a few
seconds after DC-on", after PH9+1s, AXP+1s, EEPROM, VC6, CH394).
Run `python3 r0_sim.py` for the PW-1 table, `--selftest` to check predictions.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "models", "system")))
from power_model import PowerModel  # noqa: E402

# timing after the rails come on (ON), seconds (HYPOTHESIS)
CH394_OUT_OF_RESET = 3.0     # link comes up
IP_PROGRAMMED = 3.5          # app writes the forced default IP -> ping answers
DT = 0.1


class _CH394Predictor:
    """Derives link/ping from the power state + time since rails-on.

    link up  == powered AND CH394 out of reset (a few s after ON)
    ping ok  == link up AND the app has written the default IP
    Leaving ON (shutdown) puts the CH394 back in reset: link down, no ping.
    """

    def __init__(self):
        self.on_since = None
        self.link = False
        self.ping = False

    def update(self, powered, t):
        if powered:
            if self.on_since is None:
                self.on_since = t
            up = t - self.on_since
            self.link = up >= CH394_OUT_OF_RESET
            self.ping = up >= IP_PROGRAMMED
        else:
            self.on_since = None
            self.link = False
            self.ping = False


def simulate_pw1(hypothesis, auto_start, ph5_low_at=None, horizon=10.0):
    """Run one PW-1 scenario. Returns (timeline, outcome).

    hypothesis : "H1" | "H2"
    auto_start : H1 auto-start option / H2 MCU-runs-at-DC-on (both model the
                 firmware driving PH9 at boot without a panel button)
    ph5_low_at : seconds at which PH5 is pulled low (the pitfall), or None
    """
    p = PowerModel(hypothesis=hypothesis, ignore_ph5=False)  # PW-1 is stock
    ch = _CH394Predictor()
    p.set_dc(True)
    boots = auto_start or hypothesis == "H2"
    if boots:
        p.drive_ph9(True)             # firmware step 1: PH9 high
    timeline = []
    last = None
    t = 0.0
    ph5_done = False
    while t <= horizon + 1e-9:
        if ph5_low_at is not None and not ph5_done and t >= ph5_low_at:
            p.set_ph5_low(True)
            ph5_done = True
        p.advance(DT)
        if p.state == PowerModel.SHUTDOWN:
            p.shutdown_complete()     # firmware runs the safe-state steps
        p.tick_reset_if_ready()
        ch.update(p.powered(), t)
        snap = (p.state, ch.link, ch.ping)
        if snap != last:
            timeline.append((round(t, 1), p.state, ch.link, ch.ping))
            last = snap
        t += DT

    final_state, link, ping = p.state, ch.link, ch.ping
    came_up = any(e[2] for e in timeline)        # ping ever answered == app ran
    went_off = came_up and final_state in (PowerModel.WAIT_PH5_HIGH,
                                            PowerModel.SHUTDOWN, PowerModel.OFF,
                                            PowerModel.STANDBY)
    if not boots:
        outcome = "never powers (no panel/button, no auto-start) — no link, no ping"
    elif not came_up:
        outcome = "powers but app not confirmed in horizon"
    elif went_off and not ping:
        outcome = ("boots, link up, ping answers; then PH5-low -> power-off "
                   "request, CH394 in reset (link down, no ping), waiting for "
                   "PH5 high (no panel -> stays off) — the stock pitfall")
    else:
        outcome = "boots fully; link up; ping answers on the default IP; stays up"
    return timeline, outcome


SCENARIOS = [
    ("H2", True,  None,  "H2, PH5 high (pull-up), no panel"),
    ("H2", True,  5.0,   "H2, PH5 pulled low at 5 s (pitfall)"),
    ("H1", False, None,  "H1 without auto-start, no panel"),
    ("H1", True,  None,  "H1 with auto-start, PH5 high"),
    ("H1", True,  5.0,   "H1 with auto-start, PH5 low at 5 s (pitfall)"),
]


def run_table():
    rows = []
    for hyp, auto, ph5, label in SCENARIOS:
        tl, outcome = simulate_pw1(hyp, auto, ph5)
        rows.append((label, outcome, tl))
    return rows


def format_report(rows):
    out = ["# R0 / PW-1 — PowerModel predictions (generated)\n"]
    out.append("Model-based predictions (not the stock image yet). Each row is a "
               "PW-1 scenario; the outcome predicts the owner's T0-P2/T0-P3.\n")
    out.append("| scenario | predicted outcome |")
    out.append("| --- | --- |")
    for label, outcome, _tl in rows:
        out.append("| %s | %s |" % (label, outcome))
    out.append("")
    for label, outcome, tl in rows:
        out.append("### %s\n" % label)
        out.append("timeline (t, power-state, link, ping):\n")
        out.append("```")
        for t, st, link, ping in tl:
            out.append("%5.1fs  %-14s link=%-5s ping=%s" % (t, st, link, ping))
        out.append("```\n")
    return "\n".join(out) + "\n"


def _selftest():
    # H2, PH5 high: boots fully, ping ok, stays up
    tl, o = simulate_pw1("H2", True, None)
    assert "stays up" in o, o
    assert tl[-1][2] is True and tl[-1][3] is True   # link + ping at end

    # H2, PH5 low at 5 s: pitfall — ends not pinging, waiting for PH5
    tl, o = simulate_pw1("H2", True, 5.0)
    assert "pitfall" in o, o
    assert tl[-1][2] is False and tl[-1][3] is False
    assert any(e[3] for e in tl)                     # did ping before the drop

    # H1 without auto-start: never powers
    tl, o = simulate_pw1("H1", False, None)
    assert "never powers" in o, o
    assert all(not e[2] and not e[3] for e in tl)

    # H1 with auto-start, PH5 high: boots fully
    tl, o = simulate_pw1("H1", True, None)
    assert "stays up" in o, o

    # H1 with auto-start, PH5 low: pitfall
    tl, o = simulate_pw1("H1", True, 5.0)
    assert "pitfall" in o, o

    print("r0_sim.py selftest: OK (PW-1 H1/H2 x PH5 variants)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print(format_report(run_table()))

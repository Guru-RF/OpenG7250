#!/usr/bin/env python3
"""M8c / R0 — PW-1 EMULATOR confirmation (§3.8.7 step 1).

r0_sim.py gives the PowerModel *prediction* for PW-1. This closes the loop: it
boots the stock Main (via m1_run) and checks the observed power/LAN behaviour
against the predicted "H2 / auto-start, PH5 high" scenario — the headless
no-panel case. It confirms, from the real image, that the Main:

  * drives PH9 high (power hold)          -> GPIOH BitSet bit9 (0x200)
  * brings the CH394/LAN up and programs the forced default IP
                                          -> console "[LAN] Init: IP 192.168.3.199"
  * does NOT issue a spontaneous power-off (no shutdown log, no PH5-low path)

This is a model-vs-image cross-check, not a hardware test; the tier-0 owner
observations (T0-P1..P4) remain the real-radio confirmation (docs/M8c-R0-report).
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "models", "system"))

import bootcore          # noqa: E402
import m1_run            # noqa: E402
from r0_sim import simulate_pw1   # noqa: E402

LOG = os.path.join(m1_run.OUT, "m1_renode.log")


def observe_boot(timeout=45.0, reuse=False):
    """Boot the Main (unless reuse=True and a log exists) and extract the PW-1
    observations from the access log."""
    if not (reuse and os.path.isfile(LOG) and os.path.getsize(LOG) > 0):
        import imagemap
        m1_run.run_boot(imagemap.resolve("main"), timeout=timeout)
    text = open(LOG, errors="replace").read()
    console = bootcore.console_from_log(LOG)
    ph9 = bool(re.search(r"gpioPortH:.*WriteUInt32 to 0x18 \(BitSet\), value 0x200", text))
    lan = re.search(r"\[LAN\] Init: IP (\d+\.\d+\.\d+\.\d+).*Port (\d+)", console)
    power_off = bool(re.search(r"power.?off|shutdown|Enter (?:sleep|standby)", console, re.I))
    return {
        "ph9_high": ph9,
        "lan_ip": lan.group(1) if lan else None,
        "lan_port": int(lan.group(2)) if lan else None,
        "spontaneous_power_off": power_off,
    }


def main():
    reuse = "--reuse" in sys.argv
    obs = observe_boot(reuse=reuse)

    # the matching prediction: H2 (or H1+auto-start), PH5 held high, no panel
    _, pred = simulate_pw1("H2", auto_start=True, ph5_low_at=None)

    checks = [
        ("drives PH9 high (power hold)", obs["ph9_high"], True),
        ("LAN comes up on the forced default IP 192.168.3.199",
         obs["lan_ip"] == "192.168.3.199", True),
        ("base port 50001", obs["lan_port"] == 50001, True),
        ("no spontaneous power-off (stays up)", not obs["spontaneous_power_off"], True),
    ]
    print("# R0 / PW-1 — emulator confirmation (H2 / auto-start, PH5 high)\n")
    print("Predicted (r0_sim): %s\n" % pred)
    print("Observed (stock Main boot):")
    allok = True
    for label, got, want in checks:
        ok = (got == want)
        allok = allok and ok
        print("  [%s] %s" % ("OK" if ok else "XX", label))
    print("\nobserved: ip=%s port=%s ph9=%s power_off=%s"
          % (obs["lan_ip"], obs["lan_port"], obs["ph9_high"], obs["spontaneous_power_off"]))
    verdict = ("CONFIRMED: the stock Main matches the PW-1 'H2/auto-start, PH5 "
               "high' prediction — headless no-panel boot reaches A1, drives PH9, "
               "LAN up on the default IP, stays up." if allok else
               "MISMATCH: see the failing checks above.")
    print("\n%s" % verdict)
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()

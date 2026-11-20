#!/usr/bin/env python3
"""Superloop test (acceptance item A): does the stock Main reach its superloop?

Boots the stock Main with the full Main model set (m1_run --fpga: fused
GPIOE+FPGA, MDMA, PA bias plant with the ADC1 metering feed) without the
per-access log, so the boot is fast. The console comes from a USART1 file
backend; the access log of Renode's IWDG model (`watchdog`) shows the watchdog
refreshes (key 0xAAAA) the superloop does once per iteration (g7250-base
main_unit/docs/flow.md, "Superloop", VERIFIED).

PASS needs both, within the budget:
  - the console line "Init Radio Server" (printed right before the superloop);
  - at least 128 IWDG refreshes logged after that line appeared (counted with
    Renode's "(N)" repeat suffix).
Anything else is FAIL (exit 1). No image-map: exit 2.

--hold S keeps the Main running S more seconds (host time) after a PASS, so the
console also covers some superloop runtime (acceptance item D2b counts the FPGA
runtime-health errors there).

Output in .private/superloop/: renode.log, console.txt, boot.resc.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bootcore  # noqa: E402
import m1_run    # noqa: E402

REPO = m1_run.REPO
OUT = os.path.join(REPO, ".private", "superloop")
MIN_REFRESH = 128
CONSOLE_MARK = "Init Radio Server"


def build_resc(image, log_path, console_path):
    """m1_run --fpga without the per-access log, plus console file and IWDG log."""
    lines = [ln for ln in m1_run.build_resc(image, log_path, fpga=True).splitlines()
             if "LogAllPeripheralsAccess" not in ln and not ln.startswith("logLevel -1")
             and ln.strip() != "start"]
    lines += [
        "logLevel 3",
        "sysbus LogPeripheralAccess sysbus.watchdog true",
        "logLevel 1 sysbus.watchdog",
        "sysbus.usart1 CreateFileBackend @%s true" % console_path,
        "start",
    ]
    return "\n".join(lines) + "\n"


def run(timeout, hold=0.0):
    import imagemap
    image = imagemap.resolve("main")
    os.makedirs(OUT, exist_ok=True)
    log_path = os.path.join(OUT, "renode.log")
    console = os.path.join(OUT, "console.txt")
    for p in (log_path, console):
        open(p, "w").close()
    resc = os.path.join(OUT, "boot.resc")
    open(resc, "w").write(build_resc(image, log_path, console))
    proc = subprocess.Popen([bootcore.RENODE, "--disable-xwt", "--console",
                             "-e", "path add @%s" % REPO, "-e", "include @%s" % resc],
                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, text=True)
    t0 = time.time()
    seen_console, refreshes, log_mark = False, 0, None
    try:
        while time.time() - t0 < timeout and not (seen_console and refreshes >= MIN_REFRESH):
            time.sleep(2)
            if not seen_console and CONSOLE_MARK in open(console, errors="replace").read():
                seen_console = True
                log_mark = os.path.getsize(log_path)   # count only refreshes after this
            if seen_console:
                refreshes = count_refreshes(log_path, log_mark)
        if seen_console and refreshes >= MIN_REFRESH and hold > 0:
            time.sleep(hold)
    finally:
        try:
            proc.stdin.write("pause\nquit\n"); proc.stdin.flush()
        except Exception:
            pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
    return seen_console, refreshes, time.time() - t0


def count_refreshes(log_path, start):
    n = 0
    with open(log_path, errors="replace") as f:
        f.seek(start or 0)
        for ln in f:
            if "watchdog" in ln and "value 0xAAAA" in ln:
                m = re.search(r"\((\d+)\)\s*$", ln)
                n += int(m.group(1)) if m else 1
    return n


def main():
    timeout = float(sys.argv[sys.argv.index("--timeout") + 1]) if "--timeout" in sys.argv else 240.0
    try:
        import imagemap
        imagemap.resolve("main")
    except Exception as e:
        print("superloop: no runnable Main image.\n  %s" % e)
        sys.exit(2)
    hold = float(sys.argv[sys.argv.index("--hold") + 1]) if "--hold" in sys.argv else 0.0
    c, n, t = run(timeout, hold)
    print("console '%s': %s; IWDG refreshes after it: %d (need %d) (%.0f s host time)"
          % (CONSOLE_MARK, "yes" if c else "NO", n, MIN_REFRESH, t))
    ok = c and n >= MIN_REFRESH
    print("superloop: %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

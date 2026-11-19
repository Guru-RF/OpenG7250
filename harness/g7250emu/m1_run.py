#!/usr/bin/env python3
"""M1 boot runner for g7250-emu: stock Main boot to the main loop.

Loads the Main platform (platforms/g7250_main.repl) into the pinned Renode,
turns on the observe layer (strict mode + MMIO heatmap via the peripheral log),
starts the decrypted stock Main image, and samples (PC, executedInstructions)
on a wall-clock cadence to drive the hang detector (observe.detect_hang). It
stops at the main loop, at a detected hang, or at a timeout, and writes an
observe report to the git-ignored .private/m1/.

Image policy (SECURITY.md): the decrypted image is resolved only through the
local image-map (imagemap.resolve) and verified against images/manifest.yaml.
This runner NEVER decrypts and refuses to run an unverified or absent image.
With no image-map configured it prints what to do and exits 2 — that is the
expected state until the decrypted Main image is supplied locally.

M0 method constraints carried here (docs/M0-report.md):
  * no sysbus watchpoints (slow-path hang); the heatmap comes from the log.
  * no RunFor (WFI idle stalls the virtual clock); we `start`, then sample over
    the monitor and `pause` from Python.
  * Renode quits on stdin EOF; stdin is kept open for the whole sampling loop.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RENODE = os.path.join(REPO, "tools", "renode-1.17.0",
                      "Renode.app", "Contents", "MacOS", "renode")
REPL = os.path.join(REPO, "platforms", "g7250_main.repl")
OUT = os.path.join(REPO, ".private", "m1")

sys.path.insert(0, HERE)
import observe  # noqa: E402
import platform_extras  # noqa: E402

# Verified Main reset facts (main_unit/docs/startup.md, memory_map.md):
LOAD_BASE = 0x08020000      # app vector table / load base
INIT_MSP = 0x24050000       # initial stack pointer (top of 320 KiB AXI SRAM)
RESET_PC = 0x08024554       # reset handler

# Core clock (flow.md SystemClock_Config, VERIFIED: HCLK 275 MHz). The firmware
# runs SysTick off the processor clock for its 1 ms HAL tick; Renode's NVIC only
# advances SysTick when it is given that input frequency. Without it the HAL
# tick never increments, so every HAL_Delay / I2C-wait timeout spins forever
# (the AXP223 I2C wait is the first such spin). See docs/M1-status.md.
CORE_HZ = 275000000


def build_resc(image_path, log_path):
    """Renode script: load platform + image, enable observe logging, start."""
    lines = [
        'mach create "main"',
        'machine LoadPlatformDescription @%s' % REPL,
        # give the NVIC the SysTick input clock so the 1 ms HAL tick advances
        'nvic Frequency %d' % CORE_HZ,
    ]
    # Blocks absent from the H743 base (H72x-only) and blocks with no STM32
    # model in this build (DAC1, MDMA): tag them so a touch is named and logged
    # ("not modelled") rather than faulting as a non-existing peripheral.
    lines += platform_extras.all_tag_commands()
    # observe: strict logging + per-access log mirrored to a file the parser reads
    lines += observe.strict_logging_commands("machine", log_file=log_path)
    lines += [
        # decrypted app blob loaded at the verified load base (no ELF headers)
        'sysbus LoadBinary @%s 0x%08X' % (image_path, LOAD_BASE),
        'cpu VectorTableOffset 0x%08X' % LOAD_BASE,
        'cpu SP 0x%08X' % INIT_MSP,
        'cpu PC 0x%08X' % RESET_PC,
        'start',
    ]
    return "\n".join(lines) + "\n"


def _feed_tail(tail, text):
    """Parse newly-appended log text; append (register-key, pc) to the tail.
    Returns how many access lines were seen."""
    n = 0
    for line in text.splitlines():
        m = observe._ACCESS_RE.search(line)
        if not m:
            continue
        peri = m.group("peri")
        off = int(m.group("off"), 16)
        reg = m.group("reg") or ""
        key = "%s +0x%X%s" % (peri, off, (" (%s)" % reg) if reg else "")
        pc = int(m.group("pc"), 16) if m.group("pc") else None
        tail.append((key, pc))
        n += 1
    return n


def run_boot(image_path, timeout=60.0, cadence=0.5, pc_span=0x80, idle_hold=3.0):
    """Boot the stock Main and classify the result by tailing the access log.

    The verdict comes from the log file (observe.classify_tail), not from polling
    the monitor: at boot the access log floods the console, so Renode's stdout is
    sent to /dev/null and we read the flushed `logFile` instead. stdin stays open
    (Renode quits on EOF). Stops at the first poll-hang, at an idle gap after real
    init, or at the timeout.
    """
    os.makedirs(OUT, exist_ok=True)
    log_path = os.path.join(OUT, "m1_renode.log")
    open(log_path, "w").close()  # truncate; Renode appends
    resc = os.path.join(OUT, "m1_boot.resc")
    with open(resc, "w") as f:
        f.write(build_resc(image_path, log_path))

    proc = subprocess.Popen(
        [RENODE, "--disable-xwt", "--console",
         "-e", "path add @%s" % REPO,
         "-e", "include @%s" % resc],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        text=True)

    tail = deque(maxlen=observe.TAIL_WINDOW)
    verdict = None
    t_start = time.time()
    last_growth = t_start
    offset = 0
    try:
        while time.time() - t_start < timeout:
            time.sleep(cadence)
            # Re-open by PATH each cadence: Renode's `logFile` recreates the log
            # on a fresh inode, so a handle opened before it started would read
            # the stale empty inode forever. Binary + byte-offset so seeking into
            # the growing file is well-defined.
            try:
                size = os.path.getsize(log_path)
            except OSError:
                size = 0
            chunk = ""
            if size > offset:
                with open(log_path, "rb") as lf:
                    lf.seek(offset)
                    data = lf.read()
                offset += len(data)
                chunk = data.decode("utf-8", "replace")
            new = _feed_tail(tail, chunk)
            v = observe.classify_tail(tail, pc_span=pc_span)
            if v is not None:
                verdict = v
                break
            if new:
                last_growth = time.time()
            elif tail and (time.time() - last_growth) >= idle_hold:
                verdict = observe.HangVerdict(
                    "idle-hang",
                    detail="no new MMIO for %.1fs after init — WFI / reached a wait "
                           "(no IRQ source wired yet)" % (time.time() - last_growth))
                break
        if verdict is None:
            verdict = observe.HangVerdict(
                "running", detail="timeout %.0fs reached, still making varied accesses" % timeout)
    finally:
        try:
            proc.stdin.write("pause\nquit\n")
            proc.stdin.flush()
        except Exception:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    rep = observe.parse_log(open(log_path, errors="replace"))
    report = observe.format_report(rep, verdict)
    report_path = os.path.join(OUT, "m1_observe_report.md")
    with open(report_path, "w") as f:
        f.write(report)
    return report_path, verdict, rep.accesses


def main():
    ap = argparse.ArgumentParser(description="M1 stock Main boot runner")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--cadence", type=float, default=0.5)
    args = ap.parse_args()

    if not os.path.isfile(RENODE):
        sys.exit("Renode not found at %s (install the pinned portable in tools/)" % RENODE)

    try:
        import imagemap
        image = imagemap.resolve("main")
    except Exception as e:
        print("M1 boot: no runnable Main image yet.\n  %s\n" % e)
        print("Supply the decrypted Main image locally, outside any repo, then set")
        print("  image_map = /abs/path   in local.config (git-ignored),")
        print("and fill images/manifest.yaml image_sha256 for 'main'. See SECURITY.md.")
        sys.exit(2)

    print("M1 boot: image %s" % image)
    report, verdict, n = run_boot(image, timeout=args.timeout, cadence=args.cadence)
    print("MMIO accesses: %d   verdict: %s" % (n, verdict.kind if verdict else "?"))
    if verdict and verdict.detail:
        print("  %s" % verdict.detail)
    print("report: %s" % report)


if __name__ == "__main__":
    main()

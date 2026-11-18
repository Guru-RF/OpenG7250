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

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RENODE = os.path.join(REPO, "tools", "renode-1.17.0",
                      "Renode.app", "Contents", "MacOS", "renode")
REPL = os.path.join(REPO, "platforms", "g7250_main.repl")
OUT = os.path.join(REPO, ".private", "m1")

sys.path.insert(0, HERE)
import observe  # noqa: E402

# Verified Main reset facts (main_unit/docs/startup.md, memory_map.md):
LOAD_BASE = 0x08020000      # app vector table / load base
INIT_MSP = 0x24050000       # initial stack pointer (top of 320 KiB AXI SRAM)
RESET_PC = 0x08024554       # reset handler


def build_resc(image_path, log_path):
    """Renode script: load platform + image, enable observe logging, start."""
    lines = [
        'mach create "main"',
        'machine LoadPlatformDescription @%s' % REPL,
    ]
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


def _ask(proc, cmd):
    """Send a monitor command and return the first numeric/text reply line."""
    proc.stdin.write(cmd + "\n")
    proc.stdin.flush()
    # Replies are interleaved with the banner; the caller filters.
    return None


def run_boot(image_path, timeout=60.0, cadence=0.5, pc_span=0x80, hang_hold=3.0):
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
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1)

    samples = []            # (wall_t, pc, executed)
    verdict = None
    t_start = time.time()
    try:
        while True:
            dt = time.time() - t_start
            if dt > timeout:
                verdict = observe.HangVerdict("running", detail="timeout %.0fs reached" % timeout)
                break
            # sample PC + executed via the monitor; replies land on stdout and
            # are matched by the reader below.
            proc.stdin.write("cpu PC\n")
            proc.stdin.write("cpu ExecutedInstructions\n")
            proc.stdin.flush()
            pc, ex = _read_sample(proc, deadline=time.time() + cadence)
            if pc is not None and ex is not None:
                samples.append((time.time() - t_start, pc, ex))
                v = observe.detect_hang(samples, window_s=hang_hold, pc_span=pc_span)
                if v.kind in ("poll-hang", "idle-hang"):
                    verdict = v
                    break
            time.sleep(cadence)
    finally:
        try:
            proc.stdin.write("pause\n")
            proc.stdin.write("quit\n")
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
    return report_path, verdict, len(samples)


_INT_RE = __import__("re").compile(r"^\s*(0x[0-9A-Fa-f]+|\d+)\s*$")


def _read_sample(proc, deadline):
    """Read back one PC and one ExecutedInstructions value from stdout."""
    pc = ex = None
    while time.time() < deadline and (pc is None or ex is None):
        line = proc.stdout.readline()
        if not line:
            break
        m = _INT_RE.match(line)
        if not m:
            continue
        val = int(m.group(1), 0)
        if pc is None:
            pc = val
        elif ex is None:
            ex = val
    return pc, ex


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
    print("samples: %d   verdict: %s" % (n, verdict.kind if verdict else "?"))
    if verdict and verdict.detail:
        print("  %s" % verdict.detail)
    print("report: %s" % report)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""M0 platform-spike runner for g7250-emu.

Builds the clean-room M0 test firmware, runs it on the pinned Renode
(tools/renode-1.17.0), and measures host throughput (MIPS and MMIO/s) plus the
feature checks (dp-FPU, sp-FPU, MPU, DWT CYCCNT, cache-maintenance no-op). It
produces the M0 go/no-go numbers for spec §8.7 and §14 (M0 exit).

Measurement method (no watchpoints — those force the slow memory path; no
RunFor — that stalls on the post-done WFI idle): two one-shot PC hooks on the
marker functions m0_mark_loop_start and m0_mark_done record host wall time and
cpu.ExecutedInstructions at the exact start and end of the GPIO bit-bang loop;
the done hook also reads the result block and pauses the CPU, so idle
instructions never pollute the counts.

Output goes to .private/m0/ (git-ignored). Nothing is pushed.

Usage:  python3 harness/g7250emu/m0_run.py [--runs N] [--mips M]
"""
from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RENODE = os.path.join(REPO, "tools", "renode-1.17.0",
                      "Renode.app", "Contents", "MacOS", "renode")
FW_DIR = os.path.join(REPO, "firmware-tests", "m0")
OUT = os.path.join(REPO, ".private", "m0")
ELF = os.path.join(OUT, "m0_test.elf")
PLATFORM = "@platforms/cpus/stm32h743.repl"   # pinned Renode's own H743 model

RESULT_ADDRS = {  # fixed block at top of AXI SRAM (see m0.ld / m0_test.c)
    "done": 0x2407F008, "iters": 0x2407F00C, "cyc": 0x2407F010,
    "dp": 0x2407F014, "sp": 0x2407F018, "mpu": 0x2407F01C,
    "cache": 0x2407F024, "flt": 0x2407F028,
}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def build():
    os.makedirs(OUT, exist_ok=True)
    r = sh(["make", "-C", FW_DIR])
    if r.returncode != 0:
        sys.exit("build failed:\n" + r.stdout + r.stderr)


def marker_addrs():
    r = sh(["arm-none-eabi-nm", ELF])
    addrs = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] in ("m0_mark_loop_start", "m0_mark_done"):
            addrs[parts[2]] = int(parts[0], 16)
    if len(addrs) != 2:
        sys.exit("could not find marker symbols in ELF")
    return addrs


def write_resc(ev_path, mips, addrs):
    resc = os.path.join(OUT, "m0_measure.resc")
    reads = ", ".join("a(0x%08X)" % RESULT_ADDRS[k] for k in
                      ["done", "iters", "cyc", "dp", "sp", "mpu", "cache", "flt"])
    keys = " ".join("%s=%%d" % k for k in
                    ["done", "iters", "cyc", "dp", "sp", "mpu", "cache", "flt"])
    with open(resc, "w") as f:
        f.write('mach create "m0"\n')
        f.write("machine LoadPlatformDescription %s\n" % PLATFORM)
        f.write("sysbus LoadELF @%s\n" % ELF)
        f.write("cpu PerformanceInMips %d\n" % mips)
        f.write("cpu AddHook 0x%08X \"import time; f=open('%s','a'); "
                "f.write('start %%.6f %%d\\n' %% (time.time(), self.ExecutedInstructions)); "
                "f.close()\"\n" % (addrs["m0_mark_loop_start"], ev_path))
        f.write("cpu AddHook 0x%08X \"import time; a=self.Bus.ReadDoubleWord; "
                "f=open('%s','a'); f.write('done %%.6f %%d %s\\n' %% "
                "(time.time(), self.ExecutedInstructions, %s)); f.close(); self.Pause()\"\n"
                % (addrs["m0_mark_done"], ev_path, keys, reads))
        f.write("start\n")
    return resc


def run_once(resc, ev_path, timeout=90):
    open(ev_path, "w").close()
    # Keep stdin open (PIPE, never closed) so Renode does not quit on EOF
    # while the async 'start' is still running.
    p = subprocess.Popen([RENODE, "--disable-xwt", "--console",
                           "-e", "include @%s" % resc],
                          stdin=subprocess.PIPE,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    try:
        while time.time() - t0 < timeout:
            txt = open(ev_path).read()
            if "done " in txt:
                break
            if p.poll() is not None:
                break
            time.sleep(0.2)
    finally:
        p.terminate()
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
    return open(ev_path).read()


def parse(txt):
    start = re.search(r"start ([\d.]+) (\d+)", txt)
    done = re.search(r"done ([\d.]+) (\d+) (.+)", txt)
    if not start or not done:
        return None
    fields = dict(re.findall(r"(\w+)=(\d+)", done.group(3)))
    return {
        "t0": float(start.group(1)), "instr0": int(start.group(2)),
        "t1": float(done.group(1)), "instr1": int(done.group(2)),
        "fields": {k: int(v) for k, v in fields.items()},
    }


def load_avg():
    try:
        return os.getloadavg()
    except OSError:
        return (0.0, 0.0, 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--mips", type=int, default=100)
    args = ap.parse_args()

    if not os.path.isfile(RENODE):
        sys.exit("Renode not found at %s" % RENODE)
    build()
    addrs = marker_addrs()
    ev = os.path.join(OUT, "m0_events.txt")
    resc = write_resc(ev, args.mips, addrs)

    runs = []
    for i in range(args.runs):
        la = load_avg()
        r = parse(run_once(resc, ev))
        if not r:
            print("run %d: no measurement" % (i + 1))
            continue
        host = r["t1"] - r["t0"]
        instr = r["instr1"] - r["instr0"]
        iters = r["fields"]["iters"]
        r.update(host=host, instr=instr, iters=iters,
                 mmio_s=iters / host, mips_host=instr / host / 1e6,
                 realtime=(instr / (args.mips * 1e6)) / host, load=la[0])
        runs.append(r)
        print("run %d: host=%.3fs instr=%d  %.2f MMIO/s  %.1f host-MIPS  %.3fx RT  load=%.1f"
              % (i + 1, host, instr, r["mmio_s"], r["mips_host"], r["realtime"], la[0]))

    if not runs:
        sys.exit("no successful runs")

    best = min(runs, key=lambda r: r["host"])   # least load-affected
    f = best["fields"]
    report = os.path.join(OUT, "m0_report.md")
    with open(report, "w") as rp:
        rp.write(render_report(best, runs, args, addrs, f))
    print("\nreport -> %s" % report)
    return 0


def render_report(best, runs, args, addrs, f):
    ok = lambda v: "PASS" if v else "FAIL"
    lines = [
        "# M0 platform-spike measurement (generated)", "",
        "Renode 1.17.0 (osx-arm64), cortex-m7 @ PerformanceInMips=%d, %d run(s)." % (args.mips, len(runs)),
        "GPIO loop = %d MMIO stores. Best (least-loaded) run reported; see all runs below." % best["iters"],
        "",
        "## Feature checks", "",
        "| Check | Result |", "| --- | --- |",
        "| done marker (0xD09E=%d) | %s |" % (0xD09E, "PASS" if f["done"] == 0xD09E else "FAIL"),
        "| double-precision FPU | %s |" % ok(f["dp"]),
        "| single-precision FPU | %s |" % ok(f["sp"]),
        "| MPU enable/disable | %s |" % ok(f["mpu"]),
        "| cache-maintenance no-op | %s |" % ok(f["cache"]),
        "| DWT CYCCNT delta | %d cycles (%s) |" % (f["cyc"], "nonzero" if f["cyc"] else "ZERO"),
        "| fault during run | %s |" % ("none" if f["flt"] == 0 else "exc %d" % f["flt"]),
        "",
        "## Host throughput (best run)", "",
        "- host wall time: %.3f s" % best["host"],
        "- guest instructions: %d" % best["instr"],
        "- MMIO rate: %.3g MMIO/s" % best["mmio_s"],
        "- host speed: %.1f guest-MIPS" % best["mips_host"],
        "- emulation speed: %.3fx realtime (at %d guest-MIPS)" % (best["realtime"], args.mips),
        "",
        "## All runs", "",
        "| run | host s | MMIO/s | host-MIPS | xRT | loadavg |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for i, r in enumerate(runs, 1):
        lines.append("| %d | %.3f | %.3g | %.1f | %.3f | %.1f |" %
                      (i, r["host"], r["mmio_s"], r["mips_host"], r["realtime"], r["load"]))
    lines += ["", "_Load average affects host timing; compare MMIO/s against the "
              "spec §8.7 target (>=7e6 MMIO/s) with that caveat._", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""M1 observe layer for g7250-emu: strict mode, hang detector, MMIO heatmap.

This is the diagnostic instrumentation the M1 milestone needs around a stock
Main boot (spec §14 M1). It is *image-independent*: it generates the Renode
monitor commands that turn observation on, and it parses whatever Renode prints
(plus an optional PC/instruction sample trace) into three products:

  * strict mode  — unhandled/unimplemented MMIO accesses and CPU faults are
                   collected as violations; a strict run fails on the first one.
  * hang detector — distinguishes a *poll-hang* (PC spinning in a tight window
                   while the instruction count keeps climbing — the classic
                   RCC/PWR/FLASH/I2C "wait for ready" loop that never completes)
                   from an *idle-hang* (instruction count frozen in WFI with no
                   interrupt scheduled). Both are reported with the stuck PC
                   range so the next boot iteration knows which register to feed.
  * MMIO heatmap  — per-peripheral / per-address access counts, so we can see
                   where the firmware spends its boot polling the bus.

Design constraints carried from M0 (docs/M0-report.md, "Method notes"):
  * NO sysbus watchpoints — they force Renode's slow memory path and hang a
    long run. The heatmap is built from the peripheral-access *log* instead,
    which is fine for a boot (modest access volume), not for a throughput run.
  * NO `RunFor` to terminate — a post-boot WFI idle stalls the virtual clock.
    The hang detector samples (PC, executedInstructions) from the monitor on a
    wall-clock cadence and decides when to stop; the runner pauses the CPU.
  * Renode quits on stdin EOF — the runner keeps stdin open (see m0_run.py).

The module is pure parsing/orchestration logic and self-tests on synthetic
input (`python3 observe.py --selftest`), so it is verifiable before any
decrypted image exists. Output lands in the git-ignored `.private/`.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# Renode-side: generate the monitor commands that turn observation on.
# --------------------------------------------------------------------------

def strict_logging_commands(machine="machine", log_file=None):
    """Monitor commands to surface unhandled MMIO + faults.

    Renode logs an unimplemented/unhandled peripheral access at WARNING. We set
    the whole sysbus to log at that level and (optionally) mirror the log to a
    file the parser reads back. Peripherals that are *meant* to be silent are
    quieted individually by the platform, not here.
    """
    # Access lines log at INFO, violations at WARNING/ERROR; -1 (NOISY) captures
    # both so the heatmap sees every access and strict mode sees every warning.
    # (Verified against the platform: LogAllPeripheralsAccess emits [INFO] lines.)
    cmds = [
        "logLevel -1 sysbus",
        "sysbus LogAllPeripheralsAccess true",
    ]
    if log_file:
        # `logFile` appends; the runner truncates the path first.
        cmds.append('logFile @%s' % log_file)
    return cmds


# Renode's per-access log line (LogAllPeripheralsAccess, verified format), e.g.:
#   [22:47:41.3515]  [INFO] rcc: ReadUInt32 from 0x0 (ClockControl), returned 0x25
#   [22:47:41.3546]  [INFO] rcc: WriteUInt32 to 0x0 (ClockControl), value 0x1
# The peripheral name is the `src:` token; the 0x.. is the *offset within the
# peripheral*; the parens hold the *register* name; there is no PC in the line
# (PC sampling for the hang detector comes from `cpu PC` polling, not the log).
_ACCESS_RE = re.compile(
    r"\[(?P<level>\w+)\]\s+(?P<peri>[\w.\-]+):\s+"
    r"(?P<op>Read|Write)\w*\s+(?:from|to)\s+"
    r"(?P<off>0x[0-9A-Fa-f]+)"
    r"(?:\s*\((?P<reg>[^)]*)\))?"
    r"(?:,\s+(?:returned|value)\s+(?P<val>0x[0-9A-Fa-f]+))?"
)

_UNHANDLED_RE = re.compile(
    r"\[(?P<level>WARNING|ERROR)\]\s+(?P<src>[\w.]+):\s*(?P<msg>.*"
    r"(?:unimplemented|unhandled|non[- ]?existing|tried to (?:read|write)).*)",
    re.IGNORECASE,
)

_FAULT_RE = re.compile(
    r"(HardFault|BusFault|UsageFault|MemManage|escalat|lockup|CPU halted)",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# Parsing products.
# --------------------------------------------------------------------------

@dataclass
class Access:
    op: str
    addr: int
    name: str
    pc: int | None
    level: str


@dataclass
class ObserveReport:
    accesses: int = 0
    heatmap_reg: Counter = field(default_factory=Counter)        # "peri+0xoff (reg)" -> count
    heatmap_peri: Counter = field(default_factory=Counter)       # peripheral -> count
    violations: list = field(default_factory=list)               # strict-mode hits
    faults: list = field(default_factory=list)

    def is_clean(self):
        return not self.violations and not self.faults


def parse_log(lines):
    """Parse Renode log lines into an ObserveReport (heatmap + strict violations)."""
    rep = ObserveReport()
    for line in lines:
        # strict first: an unhandled-access WARNING also contains Read/Write, so
        # classify it as a violation and do not also count it as a clean access.
        u = _UNHANDLED_RE.search(line)
        if u:
            rep.violations.append(u.group("msg").strip())
        elif _ACCESS_RE.search(line):
            m = _ACCESS_RE.search(line)
            rep.accesses += 1
            peri = m.group("peri")
            off = int(m.group("off"), 16)
            reg = m.group("reg") or ""
            key = "%s +0x%X%s" % (peri, off, (" (%s)" % reg) if reg else "")
            rep.heatmap_peri[peri] += 1
            rep.heatmap_reg[key] += 1
        if _FAULT_RE.search(line):
            rep.faults.append(line.strip())
    return rep


# Coarse address->peripheral buckets for the Main (STM32H72x map; VERIFIED
# ranges from main_unit/docs/memory_map.md, names are ours). Used only when a
# log line carries no peripheral name.
_BUCKETS = [
    (0x40004400, 0x40004800, "usart2"),
    (0x40004800, 0x40004C00, "usart3"),
    (0x40005400, 0x40005800, "i2c1"),
    (0x40011000, 0x40011400, "usart1"),
    (0x40013000, 0x40013400, "spi1"),
    (0x40013400, 0x40013800, "spi2"),
    (0x58020000, 0x58020400, "gpioa"),
    (0x58021000, 0x58021400, "gpioe"),   # FPGA bit-bang side (M0 finding R3)
    (0x58022000, 0x58022400, "gpioh"),   # PH5/PH9 power (§3.8)
    (0x58024400, 0x58024800, "rcc"),
    (0x58024800, 0x58024C00, "pwr"),
    (0x52002000, 0x52002400, "flash"),
    (0x40015000, 0x40015400, "spi6"),    # CH394 (A1.12)
    (0x40003C00, 0x40004000, "spi3_i2s3"),
]


def _peri_for(addr):
    for lo, hi, name in _BUCKETS:
        if lo <= addr < hi:
            return name
    return "0x%08X" % (addr & ~0x3FF)


# --------------------------------------------------------------------------
# Hang detector: operates on (wall_t, pc, executed) samples.
# --------------------------------------------------------------------------

@dataclass
class HangVerdict:
    kind: str          # "running" | "poll-hang" | "idle-hang" | "progress"
    pc_lo: int = 0
    pc_hi: int = 0
    detail: str = ""


def detect_hang(samples, window_s=3.0, pc_span=0x80):
    """Classify a tail of (wall_t, pc, executed) samples.

    * executed climbing + PC confined to a small window  -> poll-hang
    * executed frozen                                     -> idle-hang (WFI)
    * executed climbing + PC roaming                      -> progress (running)

    `window_s` is how long the condition must hold; `pc_span` is how tight the
    PC window must be to count as "confined".
    """
    if len(samples) < 2:
        return HangVerdict("running", detail="too few samples")
    t0 = samples[-1][0] - window_s
    tail = [s for s in samples if s[0] >= t0]
    if len(tail) < 2:
        tail = samples[-2:]
    pcs = [s[1] for s in tail]
    exec_lo, exec_hi = tail[0][2], tail[-1][2]
    pc_lo, pc_hi = min(pcs), max(pcs)
    climbing = exec_hi > exec_lo
    confined = (pc_hi - pc_lo) <= pc_span
    held = (tail[-1][0] - tail[0][0]) >= window_s * 0.9
    if not held:
        return HangVerdict("running", pc_lo, pc_hi, "window not yet filled")
    if not climbing:
        return HangVerdict("idle-hang", pc_lo, pc_hi,
                           "executed frozen at %d (WFI, no IRQ scheduled)" % exec_hi)
    if confined:
        return HangVerdict("poll-hang", pc_lo, pc_hi,
                           "PC spinning in [0x%X..0x%X], executed +%d — a never-ready "
                           "poll (feed the awaited register)" % (pc_lo, pc_hi, exec_hi - exec_lo))
    return HangVerdict("progress", pc_lo, pc_hi, "executed +%d, PC roaming" % (exec_hi - exec_lo))


# --------------------------------------------------------------------------
# Reporting.
# --------------------------------------------------------------------------

def format_report(rep, hang=None, top=20):
    out = ["# M1 observe report (generated)\n"]
    out.append("MMIO accesses logged: %d\n" % rep.accesses)
    out.append("## MMIO heatmap (top %d peripherals)\n" % top)
    out.append("| peripheral | accesses |")
    out.append("| --- | --- |")
    for name, n in rep.heatmap_peri.most_common(top):
        out.append("| %s | %d |" % (name, n))
    out.append("")
    out.append("## Hottest registers\n")
    out.append("| register | accesses |")
    out.append("| --- | --- |")
    for key, n in rep.heatmap_reg.most_common(top):
        out.append("| %s | %d |" % (key, n))
    out.append("")
    out.append("## Strict mode\n")
    if rep.is_clean():
        out.append("CLEAN — no unhandled accesses, no faults.")
    else:
        if rep.violations:
            out.append("**%d unhandled/unimplemented access violation(s):**" % len(rep.violations))
            for v in rep.violations[:top]:
                out.append("- %s" % v)
        if rep.faults:
            out.append("\n**%d fault line(s):**" % len(rep.faults))
            for f in rep.faults[:top]:
                out.append("- %s" % f)
    out.append("")
    if hang is not None:
        out.append("## Hang detector\n")
        out.append("verdict: **%s**" % hang.kind)
        if hang.detail:
            out.append("\n%s" % hang.detail)
        if hang.pc_hi:
            out.append("\nPC window: 0x%X .. 0x%X" % (hang.pc_lo, hang.pc_hi))
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# Self-test (verifiable without any image or Renode).
# --------------------------------------------------------------------------

def _selftest():
    # real Renode LogAllPeripheralsAccess format (verified against the platform)
    log = [
        "[12:00:00.0001]  [INFO] rcc: ReadUInt32 from 0x0 (ClockControl), returned 0x25",
        "[12:00:00.0002]  [INFO] rcc: WriteUInt32 to 0x0 (ClockControl), value 0x1",
        "[12:00:00.0003]  [INFO] pwr: ReadUInt32 from 0x0 (unknown), returned 0xF000C100",
        "[12:00:00.0004]  [WARNING] sysbus: Tried to read from a non-existing peripheral at 0x40006000",
        "[12:00:00.0005]  [INFO] rcc: ReadUInt32 from 0x0 (ClockControl), returned 0x25",
    ]
    rep = parse_log(log)
    assert rep.accesses == 4, rep.accesses
    assert rep.heatmap_peri["rcc"] == 3, rep.heatmap_peri
    assert rep.heatmap_peri["pwr"] == 1, rep.heatmap_peri
    assert rep.heatmap_reg["rcc +0x0 (ClockControl)"] == 3, rep.heatmap_reg
    assert len(rep.violations) == 1, rep.violations
    assert not rep.is_clean()

    # fault detection
    frep = parse_log(["[12:00:01] [ERROR] cpu: HardFault escalation, CPU halted"])
    assert frep.faults, "fault not caught"

    # poll-hang: executed climbing, PC pinned
    poll = [(0.0, 0x8024500, 1000), (1.0, 0x8024508, 2000),
            (2.0, 0x8024500, 3000), (3.0, 0x8024510, 4000)]
    v = detect_hang(poll)
    assert v.kind == "poll-hang", v

    # idle-hang: executed frozen
    idle = [(0.0, 0x8030000, 50000), (1.0, 0x8030000, 50000),
            (2.0, 0x8030000, 50000), (3.0, 0x8030000, 50000)]
    v = detect_hang(idle)
    assert v.kind == "idle-hang", v

    # progress: executed climbing, PC roaming
    prog = [(0.0, 0x8024000, 1000), (1.0, 0x8030000, 9000),
            (2.0, 0x8038000, 40000), (3.0, 0x8041000, 90000)]
    v = detect_hang(prog)
    assert v.kind == "progress", v

    # _peri_for buckets
    assert _peri_for(0x58021020) == "gpioe"
    assert _peri_for(0x40015010) == "spi6"

    print(format_report(rep, detect_hang(poll)))
    print("observe.py selftest: OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    elif len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            rep = parse_log(f)
        print(format_report(rep))
    else:
        print("usage: observe.py <renode-log-file> | --selftest")
        sys.exit(2)

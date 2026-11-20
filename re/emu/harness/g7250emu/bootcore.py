#!/usr/bin/env python3
"""Shared boot-runner core for re/emu (Main and Control).

Given a Renode .resc (built by a unit-specific runner), this launches the pinned
Renode, drives the observe layer, and classifies the result from two live
signals:

  * MMIO heatmap + poll-hang: tailed from the flushed `logFile` (the console log
    backend is silenced by observe.strict_logging_commands so stdout stays
    usable for monitor replies).
  * progress vs. dead: `cpu PC` + `cpu ExecutedInstructions` sampled over the
    monitor each cadence.

Verdicts (observe.HangVerdict):
  poll-hang  — one register dominates the recent MMIO (observe.classify_tail)
  idle-hang  — executed instructions frozen for idle_hold (true WFI, no IRQ)
  running    — still executing at timeout; a HAL_Delay busy-wait (MMIO paused
               but executed still climbing) is NOT called a hang.

M0 method constraints (docs/M0-report.md): no watchpoints, no RunFor, keep stdin
open (Renode quits on EOF). Output lands in the git-ignored `.private/`.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RENODE = os.path.join(REPO, "tools", "renode-1.17.0",
                      "Renode.app", "Contents", "MacOS", "renode")

sys.path.insert(0, HERE)
import observe  # noqa: E402

_NUM_RE = re.compile(r"^(0x[0-9A-Fa-f]+|\d+)$")


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


def _drain(stream, replies):
    """Background: keep stdout drained; stash numeric-only lines (monitor
    replies to `cpu PC` / `cpu ExecutedInstructions`)."""
    try:
        for line in stream:
            s = line.strip()
            if _NUM_RE.match(s):
                replies.append(s)
    except Exception:
        pass


def execute(resc_text, log_path, report_path,
            timeout=60.0, cadence=0.5, pc_span=0x80, idle_hold=3.0):
    """Run one boot and return (verdict, accesses). Writes the observe report."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    open(log_path, "w").close()  # truncate; Renode appends
    resc = os.path.join(os.path.dirname(log_path), "boot.resc")
    with open(resc, "w") as f:
        f.write(resc_text)

    proc = subprocess.Popen(
        [RENODE, "--disable-xwt", "--console",
         "-e", "path add @%s" % REPO,
         "-e", "include @%s" % resc],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1)
    replies = deque(maxlen=64)
    threading.Thread(target=_drain, args=(proc.stdout, replies), daemon=True).start()

    def sample():
        replies.clear()
        try:
            proc.stdin.write("cpu PC\ncpu ExecutedInstructions\n")
            proc.stdin.flush()
        except Exception:
            return None, None
        time.sleep(0.15)
        vals = list(replies)
        if len(vals) < 2:
            return None, None
        try:
            return int(vals[-2], 0), int(vals[-1], 0)
        except ValueError:
            return None, None

    tail = deque(maxlen=observe.TAIL_WINDOW)
    verdict = None
    t_start = time.time()
    offset = 0
    last_exec = None
    exec_frozen_since = None
    try:
        while time.time() - t_start < timeout:
            time.sleep(cadence)
            try:
                size = os.path.getsize(log_path)
            except OSError:
                size = 0
            if size > offset:
                with open(log_path, "rb") as lf:
                    lf.seek(offset)
                    data = lf.read()
                offset += len(data)
                _feed_tail(tail, data.decode("utf-8", "replace"))

            v = observe.classify_tail(tail, pc_span=pc_span)
            if v is not None:
                verdict = v
                break

            pc, ex = sample()
            now = time.time()
            if ex is not None:
                if last_exec is not None and ex <= last_exec:
                    if exec_frozen_since is None:
                        exec_frozen_since = now
                    elif now - exec_frozen_since >= idle_hold:
                        verdict = observe.HangVerdict(
                            "idle-hang", pc_lo=(pc or 0), pc_hi=(pc or 0),
                            detail="executed frozen at %d for %.1fs (WFI, no IRQ "
                                   "scheduled)" % (ex, now - exec_frozen_since))
                        break
                else:
                    exec_frozen_since = None
                last_exec = ex
        if verdict is None:
            verdict = observe.HangVerdict(
                "running",
                detail="timeout %.0fs reached, CPU still executing (no dead poll, "
                       "no frozen WFI) — candidate main loop" % timeout)
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
    with open(report_path, "w") as f:
        f.write(observe.format_report(rep, verdict))
    return verdict, rep.accesses


def console_from_log(log_path, usart="usart1", txreg=0x28):
    """Reconstruct a UART console from the access log's TransmitData writes."""
    pat = re.compile(r"%s:.*WriteUInt32 to 0x%X \([^)]*\), value (0x[0-9A-Fa-f]+)"
                     % (usart, txreg))
    out = []
    for ln in open(log_path, errors="replace"):
        m = pat.search(ln)
        if m:
            v = int(m.group(1), 16) & 0xFF
            out.append(chr(v) if 9 <= v < 127 else ("\n" if v == 10 else "."))
    return "".join(out)

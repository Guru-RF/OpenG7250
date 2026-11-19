#!/usr/bin/env python3
"""M1 boot runner for g7250-emu: stock Main boot to the main loop.

Builds the Main Renode script (platform + I2C1 slave shims + SysTick clock +
observe logging + the decrypted image at its verified reset vector) and hands it
to bootcore.execute, which runs it and classifies the result (poll-hang /
idle-hang / running). See docs/M1-status.md.

Image policy (SECURITY.md): the decrypted image is resolved only through the
local image-map (imagemap.resolve), hash-verified against images/manifest.yaml.
This runner NEVER decrypts and refuses an unverified/absent image (exit 2).
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
REPL = os.path.join(REPO, "platforms", "g7250_main.repl")
REPL_I2C1_MOCK = os.path.join(REPO, "platforms", "g7250_main_i2c1_mock.repl")
OUT = os.path.join(REPO, ".private", "m1")

sys.path.insert(0, HERE)
import bootcore   # noqa: E402
import observe    # noqa: E402
import platform_extras  # noqa: E402

# Verified Main reset facts (main_unit/docs/startup.md, memory_map.md):
LOAD_BASE = 0x08020000      # app vector table / load base
INIT_MSP = 0x24050000       # initial stack pointer (top of 320 KiB AXI SRAM)
RESET_PC = 0x08024554       # reset handler
CORE_HZ = 275000000         # HCLK (flow.md); SysTick input clock for the HAL tick


def build_resc(image_path, log_path):
    lines = [
        'mach create "main"',
        'machine LoadPlatformDescription @%s' % REPL,
        # minimal ACKing I2C1 slaves so the device bring-up completes instead of
        # each byte burning a 100 ms HAL timeout (docs/M1-status.md)
        'machine LoadPlatformDescription @%s' % REPL_I2C1_MOCK,
        # give the NVIC the SysTick input clock so the 1 ms HAL tick advances
        'nvic Frequency %d' % CORE_HZ,
    ]
    # H72x-only + unmodelled (DAC1/MDMA) blocks: tag so a touch is named/logged
    lines += platform_extras.all_tag_commands()
    lines += observe.strict_logging_commands("machine", log_file=log_path)
    lines += [
        'sysbus LoadBinary @%s 0x%08X' % (image_path, LOAD_BASE),
        'cpu VectorTableOffset 0x%08X' % LOAD_BASE,
        'cpu SP 0x%08X' % INIT_MSP,
        'cpu PC 0x%08X' % RESET_PC,
        'start',
    ]
    return "\n".join(lines) + "\n"


def run_boot(image_path, timeout=60.0, cadence=0.5):
    os.makedirs(OUT, exist_ok=True)
    log_path = os.path.join(OUT, "m1_renode.log")
    report_path = os.path.join(OUT, "m1_observe_report.md")
    verdict, n = bootcore.execute(build_resc(image_path, log_path), log_path,
                                  report_path, timeout=timeout, cadence=cadence)
    return report_path, verdict, n


def main():
    ap = argparse.ArgumentParser(description="M1 stock Main boot runner")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--cadence", type=float, default=0.5)
    args = ap.parse_args()

    if not os.path.isfile(bootcore.RENODE):
        sys.exit("Renode not found at %s (install the pinned portable in tools/)" % bootcore.RENODE)

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
    print("console: %s" % os.path.join(OUT, "main_console.txt"))
    open(os.path.join(OUT, "main_console.txt"), "w").write(
        bootcore.console_from_log(os.path.join(OUT, "m1_renode.log")))


if __name__ == "__main__":
    main()

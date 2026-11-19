#!/usr/bin/env python3
"""Control boot runner for g7250-emu: stock Control (touchscreen) boot.

Sibling of m1_run.py for the Control unit (STM32H743-class). Builds the Control
Renode script (platform + I2C slave shims + SysTick clock + observe + the
decrypted image at its verified reset vector) and hands it to bootcore.execute.

Image policy (SECURITY.md): resolved only through the local image-map
(imagemap.resolve 'control'), hash-verified; never decrypts; exit 2 if absent.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
REPL = os.path.join(REPO, "platforms", "g7250_control.repl")
REPL_I2C_MOCK = os.path.join(REPO, "platforms", "g7250_control_i2c_mock.repl")
CS_SLAVES = os.path.join(REPO, "models", "csharp", "G7250Slaves.cs")
OUT = os.path.join(REPO, ".private", "control")

sys.path.insert(0, HERE)
import bootcore   # noqa: E402
import observe    # noqa: E402

# Verified Control reset facts (control_unit/docs/startup.md, memory_map.md):
LOAD_BASE = 0x08020000      # app vector table / load base
INIT_MSP = 0x24080000       # initial stack pointer (top of 512 KiB AXI SRAM)
RESET_PC = 0x080235AC       # reset handler (Thumb 0x080235AD, bit0 cleared)
CORE_HZ = 240000000         # HCLK (control docs: timer clock 240 MHz, SDCLK 240/2)


def build_resc(image_path, log_path):
    lines = [
        'mach create "control"',
        'machine LoadPlatformDescription @%s' % REPL,
        'machine LoadPlatformDescription @%s' % REPL_I2C_MOCK,
        # swap the C# Video.STM32LTDC (no CDSR; never toggles VSYNC headless) for
        # a stub whose CDSR VSYNCS toggles, so the GUI framebuffer-swap proceeds.
        'i @%s' % CS_SLAVES,
        'sysbus Unregister sysbus.ltdc',
        'machine LoadPlatformDescriptionFromString "ltdc2: Antmicro.Renode.Peripherals.Miscellaneous.G7250LtdcStub @ sysbus 0x50001000"',
        'nvic Frequency %d' % CORE_HZ,
    ]
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
    log_path = os.path.join(OUT, "control_renode.log")
    report_path = os.path.join(OUT, "control_observe_report.md")
    verdict, n = bootcore.execute(build_resc(image_path, log_path), log_path,
                                  report_path, timeout=timeout, cadence=cadence)
    return report_path, verdict, n


def main():
    ap = argparse.ArgumentParser(description="Control stock boot runner")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--cadence", type=float, default=0.5)
    args = ap.parse_args()

    if not os.path.isfile(bootcore.RENODE):
        sys.exit("Renode not found at %s" % bootcore.RENODE)

    try:
        import imagemap
        image = imagemap.resolve("control")
    except Exception as e:
        print("Control boot: no runnable Control image yet.\n  %s\n" % e)
        print("Set image_map in local.config and fill images/manifest.yaml "
              "image_sha256 for 'control'. See SECURITY.md.")
        sys.exit(2)

    print("Control boot: image %s" % image)
    report, verdict, n = run_boot(image, timeout=args.timeout, cadence=args.cadence)
    print("MMIO accesses: %d   verdict: %s" % (n, verdict.kind if verdict else "?"))
    if verdict and verdict.detail:
        print("  %s" % verdict.detail)
    # the Control console/stdout is on USART1 too (Bluetooth AT + C-lib stdout)
    open(os.path.join(OUT, "control_console.txt"), "w").write(
        bootcore.console_from_log(os.path.join(OUT, "control_renode.log")))
    print("report: %s   console: %s/control_console.txt" % (report, OUT))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""H72x-only platform extras for the Main (spec §14 M1: "length-correct vector
table + Tag regions" for the H72x blocks absent from Renode's H743 base).

Renode's STM32H7 base is modelled on the H743; the Main MCU is H72x-derived and
has a few peripheral blocks the H743 does not: TIM23, TIM24, UART9, USART10.
When the stock firmware touches one of these, we want the observe/strict layer
to say "known H72x block, not yet modelled" rather than "non-existing
peripheral". `Tag` (with no fixed value) does exactly that: the access is named
and logged, not faulted and not silently faked.

Addresses are from ST RM0468 (H723/725/730/733/735) APB maps — confidence
MEDIUM (the reference manual is public DATA; not cross-checked against the image
yet). If the image reveals a different base, fix it here.

Returns Renode monitor commands; `m1_run.py` applies them after loading the
platform. `python3 platform_extras.py` prints them.
"""
from __future__ import annotations

# name -> (base, size) ; RM0468 APB register boundary addresses (MEDIUM)
H72X_ONLY = {
    "TIM23":   (0x4000E000, 0x400),   # APB1
    "TIM24":   (0x4000E400, 0x400),   # APB1
    "UART9":   (0x40011800, 0x400),   # APB2
    "USART10": (0x40011C00, 0x400),   # APB2
}

# Blocks with no STM32 model in this Renode build, so they cannot be registered
# as peripherals; tag them instead. DAC1 (RM0468 0x40007400 APB1) and MDMA
# (0x52000000 AHB). A firmware touch is then named/logged, not faulted. The Main
# runners register their own MDMA model (docs/MDMA-model.md) and exclude MDMA
# here; the PA bias plant is in models/csharp/G7250PaPlant.cs
# (docs/PA-plant-model.md). Confidence MEDIUM.
UNMODELLED = {
    "DAC1": (0x40007400, 0x400),
    "MDMA": (0x52000000, 0x1000),
}


def _tag_cmds(table, suffix):
    cmds = []
    for name, (base, size) in sorted(table.items(), key=lambda kv: kv[1][0]):
        cmds.append('sysbus Tag <0x%08X 0x%X> "%s_%s"' % (base, size, name, suffix))
    return cmds


def h72x_tag_commands():
    """Monitor commands tagging the H72x-only blocks (named, unvalued)."""
    return _tag_cmds(H72X_ONLY, "H72X_TODO")


def unmodelled_tag_commands(exclude=()):
    """Monitor commands tagging blocks with no STM32 model in this build.
    `exclude` names blocks a runner models itself (e.g. MDMA with --fpga)."""
    return _tag_cmds({k: v for k, v in UNMODELLED.items() if k not in exclude},
                     "NO_MODEL_TODO")


def all_tag_commands(exclude=()):
    return h72x_tag_commands() + unmodelled_tag_commands(exclude)


if __name__ == "__main__":
    print("\n".join(all_tag_commands()))

# OpenG7250

Umbrella repository for all Xiegu G7250 work: reverse engineering of the stock
firmware, an emulator and test harness, a clean-room hardware-interface spec, and
independent new firmware.

Read [CLEANROOM.md](CLEANROOM.md) before working in any part of this project.

## Layout

| Path | Side | Content | Status |
|---|---|---|---|
| [`re/analysis/`](re/analysis/) | RE | Own RE work: decryption and Ghidra tooling, findings, memory map, protocol coverage | Present |
| `re/emu/` | RE | Emulator, harness, tests, hash-only image manifest (`g7250-emu`) | Planned submodule; integrated later |
| `his/` | Gate | Reviewed hardware-interface spec, hardware facts only (`g7250-his`) | Planned submodule |
| `fw/` | Clean room | New firmware "G7250-P1" (`g7250-fw`) | Planned; never checked out in an RE work tree |

## How knowledge flows

```
stock images ──► re/analysis ──► re/analysis/docs ──► his ──► fw
                     │                 │
                     └──► re/emu ◄─────┘ (models cite RE docs and HIS paragraphs)
```

- Findings from the stock firmware become documents in `re/analysis/docs/`.
- Only reviewed hardware facts pass to `his/`. Nothing else reaches `fw/`.
- `fw/` is developed from `his/` and public datasheets only.

## External references

- [`fventuri/g7250-base`](https://github.com/fventuri/g7250-base) (Franco Venturi)
  is a separate project with its own methodology. It is a comparison source, not
  a part of this repository. Findings are shared with it through issues only; see
  [shared findings](re/analysis/docs/fventuri-findings.md) and
  [acknowledgments](re/analysis/ACKNOWLEDGMENTS.md).

## Getting started (RE side)

See [re/analysis/analysis/README.md](re/analysis/analysis/README.md) for the
decryption and decompilation workflow.

# Repository layout

This repo follows the structure defined in spec §13
(`G7250-emulator-test-spec-v0.5.md`). Generated artifacts go in `/.private/`
(git-ignored); locally installed tooling in `/tools/` (git-ignored); decrypted
images never enter the repo (see `SECURITY.md`).

## No shared organisation (for now)

The projects are kept as **separate local repositories under `~/Repos/on8st/`**.
No `OpenG7250` GitHub organisation is created yet.

| Repo | Status | Role |
| --- | --- | --- |
| `g7250-base` | exists | RE documentation (fork of fventuri/g7250-base) |
| `g7250-emu` | exists (**this repo**) | RE-side tooling: emulator, harness, tests, hash manifest |
| `g7250-his` | later (M8b) | clean-room hardware-interface spec — the only hardware source for the firmware |
| `g7250-fw` | later | clean-room firmware (NF-Main first); holds the NF-link and P1 specs |

## Target structure (§13.1)

```
g7250-emu/
├── README.md CLEANROOM.md SECURITY.md LICENSE AGENTS.md
├── deps/g7250-base.lock         pinned g7250-base commit (consumed as data)
├── images/                      manifest.yaml (hashes/provenance) + verify.py
├── platforms/                   .resc / .repl (two machines, headless Main, profiles)
├── models/                      C# peripherals: stm32h7/, devices/, system/, python/
├── harness/g7250emu/            Python: core io inject observe protocols targets report
├── firmware-tests/              our own small clean-room test firmwares (incl. M0)
├── tests/                       unit integration baseline conformance brick fault fuzz perf hil
├── matrix/version_matrix.yaml
├── ci/                          pipeline definitions
├── docs/                        design docs, this spec, model docs (sourced)
└── .private/  (git-ignored)     golden sets, recordings, heatmaps, runs, build output
```

## What exists now (milestone M0 — platform spike)

```
├── docs/G7250-emulator-test-spec-v0.5.md   the study
├── docs/REPO_LAYOUT.md                      this file
├── docs/M0-report.md                        M0 go/no-go + measurements
├── images/manifest.yaml  images/verify.py
├── deps/g7250-base.lock
├── firmware-tests/m0/      m0_test.c  m0.ld  Makefile   (clean-room M0 test firmware)
├── platforms/m0_probe.resc                             (generic STM32H743 spike script)
├── harness/g7250emu/m0_run.py                           (runs Renode, measures, reports)
└── tools/   (git-ignored)  renode-1.17.0/   pinned Renode portable (arm64)
```

Directories from §13 not yet populated (`models/`, `tests/`, `matrix/`, `ci/`)
are created as the milestones that need them begin (see spec §14).

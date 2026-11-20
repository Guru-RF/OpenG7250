# G7250 architecture document

Clean-room (RE-side) architecture document for the Xiegu G7250, focused on the
**emulation + test solution** that delivers a tested alternative firmware
platform. Three parts: (1) hardware context, (2) the emulation+test component
architecture — the heart, (3) the RE→firmware pipeline and release gating.

## Sources (committed)

- `G7250-architecture.html` — the document (prose + A4 CSS + `<!--INCLUDE:…-->` placeholders).
- `svg/fig1-system.svg` … `svg/fig6-pipeline.svg` — hand-authored inline SVG figures.
- `build.py` — inlines the SVGs and renders the PDF with headless Google Chrome.

## Build

```sh
python3 docs/architecture/build.py
```

Output (git-ignored): `.private/arch/G7250-architecture.pdf` (A4 portrait).
Fallback renderer if Chrome is absent: `weasyprint .private/arch/G7250-architecture.build.html out.pdf`.

## Clean-room

Hardware facts come from the `g7250-base` RE docs and the emulator study v0.5;
confidence tags (VERIFIED/HIGH/HYPOTHESIS) are carried over. No stock firmware
code, no image bytes, no decryption. Owner ON8ST. Not for distribution.

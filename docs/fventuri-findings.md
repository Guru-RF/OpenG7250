# Findings shared with fventuri/g7250-base

Reference reviewed: `d5eab7fbd19c55c000b4430a044278f9c52aa584`.

Franco Venturi and ON8ST are credited in [Acknowledgments](../ACKNOWLEDGMENTS.md).

## Sharing workflow

The project owner has authorized sharing relevant new findings through GitHub
issues on `fventuri/g7250-base`. Check current upstream documentation and existing
issues before reporting; update an existing discussion for the same finding.
Share our conclusions, firmware version/hash, function/data addresses, confidence,
limitations and suggested verification. Do not publish firmware, source code,
decompiler/disassembler output, raw firmware bytes or private research artifacts.
Keep static-analysis conclusions distinct from demonstrated hardware behavior.
Credit reference research where it contributed. Their project-specific methodology
does not govern OpenG7250's research workflow.

This authorization covers issue reports; it does not authorize publishing the
private repository or implementation. Working implementations can be considered
for release when ready, as requested by the project owner.

## Reports

- [#1 — Forced startup defaults versus restored settings](https://github.com/fventuri/g7250-base/issues/1):
  reconcile the protocol startup description with the loader and explicit startup
  assignments already identified in our analysis.
- [#2 — Network CI-V PTT retained across session teardown](https://github.com/fventuri/g7250-base/issues/2):
  distinguish Main network PTT from Control CI-V inactivity handling; investigate
  release and audio-source behavior on network loss. Static finding, not an RF test.
- [#3 — Live network TX audio selector](https://github.com/fventuri/g7250-base/issues/3):
  distinguish extended setting `0066`, which updates the live selector, from cached
  setting `0067`; document selector value 3 for network TX audio consumption.

All reports use the Main V1.0.1 SHA-256
`6e9e65198dd12bcdf1286f7ab3986cc53230530d9283c9a73976c84fb23b237e`
and contain no OEM code, decompiler/disassembler listings or firmware attachments.

## Correction retained locally

Our initial comparison incorrectly challenged the reference's 2 MiB flash
inference for an H743-based head. STM32H743xG's nominal 1 MiB is split across
512 KiB banks at `0x08000000` and `0x08100000`; it is not a continuous first MiB.
The control application's initialized-data source at `0x080dd568` lies beyond
the xG bank-1 boundary. Within the supported H743-family variants, that supports
the 2 MiB xI inference. See ST RM0433, flash organization tables. No upstream
correction issue is warranted for that inference; chip markings remain unverified.

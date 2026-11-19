# Agent instructions (re/emu)

These rules apply **in addition to** the umbrella [`AGENTS.md`](../../AGENTS.md)
and [`CLEANROOM.md`](../../CLEANROOM.md). This component is on the **RE side**.
Product agents do **not** work here; they work only in a separate sparse clone
with `product/` (and `his/`), from the HIS and public specs.

Agents working in `re/emu/` MUST:

1. Follow the umbrella `CLEANROOM.md`, this component's `CLEANROOM.md` and
   `SECURITY.md` without exception. Never read or touch `product/`.
2. Never decrypt, never fetch, never request a decryption key. The emulator
   runs on user-supplied decrypted images from the local image-map only, and
   never calls the decryption tooling in `re/analysis/`.
3. Never commit, log or transmit image bytes, decrypted-image hashes or local
   paths. Image hashes and paths go only in the git-ignored `local.config`.
4. Put every generated artifact in `re/emu/.private/` (git-ignored), never in
   the session scratchpad, never tracked. Locally installed tools go in
   `re/emu/tools/`.
5. Make local commits on branches only. **No push, no PR, no issue, no mail
   without an explicit go from the owner.** Contributors commit under their own
   identity (here ON8ST).
6. Treat `re/analysis/` as pinned read-only data (`deps/re-analysis.lock`); a
   bump is a deliberate change with a regression run
   (`tests/baseline/acceptance_ae.sh`).
7. Refer to contributors by call sign (ON8ST), not by name.

Findings about the stock firmware belong in `re/analysis/docs/` as conclusions
with addresses and sources, without code or listings, not here. Hardware facts
meant for the product side go through the HIS (`his/`, for now the separate
`g7250-his` repo) after review at the gate.

# Agent instructions (g7250-emu)

This is the **RE-side** repository. Clean-room firmware agents do **not** work
here; firmware agents work only in `g7250-fw` from the HIS and public specs.

Agents working in this repo MUST:

1. Follow `CLEANROOM.md` and `SECURITY.md` without exception.
2. Never decrypt, never fetch, never request a decryption key. The emulator
   runs on user-supplied decrypted images from the local image-map only.
3. Never commit, log or transmit image bytes or hashes outside
   `images/manifest.yaml`. Never write image paths into tracked files.
4. Put every generated artifact in `/.private/` (git-ignored) — never in the
   session scratchpad, never tracked. Locally installed tools go in `/tools/`.
5. Make local commits on branches only. **No push, no PR, no mail without an
   explicit go from the owner.** Author is ON8ST.
6. Treat `g7250-base` as pinned read-only data (`deps/g7250-base.lock`); a bump
   is a deliberate change with a regression run.
7. Refer to the owner by call sign (ON8ST), not by name.

Findings about the stock firmware belong in `g7250-base` as RE docs, submitted
upstream only after the owner's go — not here.

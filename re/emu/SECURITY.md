# Security & image policy (re/emu)

## Firmware images: local only, hashes only

- **Decrypted application images are never committed, never pushed, never
  logged, never attached to an issue or mail.**
- They live in a **local image-map directory outside any git work tree**, at a
  path given by local configuration (`local.config*`, git-ignored).
- The tracked `images/manifest.yaml` holds only load addresses and the
  **provenance** of the vendor package (hashes of the encrypted `.bbf`/`.ctl`
  and the release zip). The decrypted-image hashes are user-supplied and kept
  only in the git-ignored `local.config` (`image_sha256.main`/`.control`);
  they are never committed.
- `images/verify.py` checks the local image-map against the manifest and
  **refuses to run if the image-map resolves inside a git work tree**, or if a
  hash does not match.

## No decryption

The emulator never decrypts anything. There is no decryption key, loader or
routine anywhere in `re/emu/` or its imported history, and the emulator never
calls the RE decryption tooling that lives elsewhere in the umbrella
(`re/analysis/`).

## Pre-commit / CI scans

Before a commit and in CI, scans reject:
- any file whose hash matches a known image hash in the manifest;
- binary blobs with vendor extensions (`*.bbf`, `*.ctl`, `*.bin`);
- a `.private/` or `tools/` path that slipped out of `.gitignore`.

## Reporting a leak or a vulnerability

If an image, a package or a key is found in git history, an artifact or a log:
stop, do not push, and notify the owner privately. Treat it as an incident:
rotate/rewrite history only in coordination with the owner.

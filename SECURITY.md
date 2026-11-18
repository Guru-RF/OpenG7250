# Security & image policy (g7250-emu)

## Firmware images: local only, hashes only

- **Decrypted application images are never committed, never pushed, never
  logged, never attached to an issue or mail.**
- They live in a **local image-map directory outside any git work tree**, at a
  path given by local configuration (`local.config*`, git-ignored).
- The repo contains only `images/manifest.yaml`: SHA-256 hashes (filled in
  locally by the user), sizes, load addresses and the **provenance** of the
  vendor package (hashes of the encrypted `.bbf`/`.ctl` and the release zip).
- `images/verify.py` checks the local image-map against the manifest and
  **refuses to run if the image-map resolves inside a git work tree**, or if a
  hash does not match.

## No decryption

This tooling never decrypts anything. There is no decryption key, loader or
routine anywhere in this repository or its history.

## Pre-commit / CI scans

Before a commit and in CI, scans reject:
- any file whose hash matches a known image hash in the manifest;
- binary blobs with vendor extensions (`*.bbf`, `*.ctl`, `*.bin`);
- a `.private/` or `tools/` path that slipped out of `.gitignore`.

## Reporting a leak or a vulnerability

If an image, a package or a key is found in git history, an artifact or a log:
stop, do not push, and notify the owner privately. Treat it as an incident:
rotate/rewrite history only in coordination with the owner.

#!/usr/bin/env python3
"""Verify decrypted G7250 images in the local image-map against the manifest.

This tool performs NO decryption. It only hashes the user-supplied decrypted
images and compares them to images/manifest.yaml. It REFUSES to run if the
image-map resolves inside a git work tree (images must never live in a repo).

Usage:
    python3 images/verify.py --release V1.0.1 --image-map /path/outside/repo
    # or set the image-map path in local.config (git-ignored).

Exit codes: 0 = all present images match; 1 = mismatch / missing; 2 = policy
refusal (image-map inside a work tree, or empty expected hashes).
"""
from __future__ import annotations
import argparse
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "manifest.yaml")


def load_manifest(path):
    try:
        import yaml  # optional
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception:
        # Minimal fallback parser is intentionally not provided: require pyyaml.
        sys.exit("verify.py: needs pyyaml (pip install pyyaml) to read the manifest")


def inside_git_worktree(path):
    try:
        r = subprocess.run(
            ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True,
        )
        return r.returncode == 0 and r.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True)
    ap.add_argument("--image-map", required=True,
                    help="directory holding the decrypted images (OUTSIDE any repo)")
    ap.add_argument("--main", default="main.bin")
    ap.add_argument("--control", default="control.bin")
    args = ap.parse_args()

    image_map = os.path.abspath(args.image_map)
    if not os.path.isdir(image_map):
        sys.exit(f"verify.py: image-map not found: {image_map}")

    # Policy: the image-map must NOT be inside a git work tree.
    if inside_git_worktree(image_map):
        print(f"REFUSED: image-map {image_map} is inside a git work tree.",
              file=sys.stderr)
        print("Move the decrypted images outside any repo (see SECURITY.md).",
              file=sys.stderr)
        return 2

    man = load_manifest(MANIFEST)
    rel = man.get("releases", {}).get(args.release)
    if not rel:
        sys.exit(f"verify.py: release {args.release} not in manifest")

    expected = rel["images"]
    targets = {"main": (args.main, expected["main"]["image_sha256"]),
               "control": (args.control, expected["control"]["image_sha256"])}

    any_empty = any(not exp for _, exp in targets.values())
    if any_empty:
        print("REFUSED: expected image_sha256 is empty in the manifest.",
              file=sys.stderr)
        print("Fill in the decrypted-image hashes locally first.", file=sys.stderr)
        return 2

    rc = 0
    for unit, (fname, exp) in targets.items():
        p = os.path.join(image_map, fname)
        if not os.path.isfile(p):
            print(f"MISSING  {unit}: {p}")
            rc = 1
            continue
        got = sha256_file(p)
        if got.lower() == exp.lower():
            print(f"OK       {unit}: {fname}")
        else:
            print(f"MISMATCH {unit}: {fname}\n  expected {exp}\n  got      {got}")
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

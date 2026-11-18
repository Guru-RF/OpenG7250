#!/usr/bin/env python3
"""Local image-map loader for g7250-emu (no decryption, ever).

Resolves the already-decrypted stock images from a local image-map directory
that lives OUTSIDE any git work tree, verifies them against images/manifest.yaml
(hashes only), and hands the runner a path to load into Renode. If the image-map
is missing, inside a work tree, or a hash does not match (or is still blank in
the manifest), it refuses — the emulator never runs an unverified image.

The image-map path comes from local configuration, never from a tracked file:
  1. env  G7250_IMAGE_MAP
  2. repo-root `local.config` (git-ignored), line  image_map = /abs/path
"""
from __future__ import annotations
import hashlib
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MANIFEST = os.path.join(REPO, "images", "manifest.yaml")


class ImageMapError(RuntimeError):
    pass


def _read_local_config():
    cfg = {}
    path = os.path.join(REPO, "local.config")
    if os.path.isfile(path):
        for line in open(path):
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg


def image_map_dir():
    d = os.environ.get("G7250_IMAGE_MAP") or _read_local_config().get("image_map")
    if not d:
        raise ImageMapError(
            "no image-map configured. Set env G7250_IMAGE_MAP or add\n"
            "  image_map = /abs/path/outside/any/repo\n"
            "to local.config (git-ignored).")
    d = os.path.abspath(os.path.expanduser(d))
    if not os.path.isdir(d):
        raise ImageMapError("image-map not found: %s" % d)
    if _inside_git_worktree(d):
        raise ImageMapError(
            "REFUSED: image-map %s is inside a git work tree. "
            "Move the decrypted images outside any repo (SECURITY.md)." % d)
    return d


def _inside_git_worktree(path):
    try:
        r = subprocess.run(["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True)
        return r.returncode == 0 and r.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def _manifest_images(release):
    try:
        import yaml
    except ImportError:
        raise ImageMapError("needs pyyaml (pip install pyyaml) to read the manifest")
    man = yaml.safe_load(open(MANIFEST))
    rel = man.get("releases", {}).get(release)
    if not rel:
        raise ImageMapError("release %s not in manifest" % release)
    return rel["images"]


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(unit, release="V1.0.1", filename=None):
    """Return the verified absolute path to the decrypted image for `unit`
    ('main' or 'control'). Raises ImageMapError on any policy/hash failure."""
    d = image_map_dir()
    filename = filename or {"main": "main.bin", "control": "control.bin"}[unit]
    path = os.path.join(d, filename)
    if not os.path.isfile(path):
        raise ImageMapError("image not in image-map: %s" % path)
    expected = _manifest_images(release)[unit]["image_sha256"]
    if not expected:
        raise ImageMapError(
            "manifest image_sha256 for %s is blank — fill it in locally first "
            "(the decrypted-image hash is user-supplied)." % unit)
    got = _sha256(path)
    if got.lower() != expected.lower():
        raise ImageMapError("hash mismatch for %s:\n  expected %s\n  got      %s"
                            % (unit, expected, got))
    return path


if __name__ == "__main__":
    import sys
    unit = sys.argv[1] if len(sys.argv) > 1 else "main"
    try:
        print(resolve(unit))
    except ImageMapError as e:
        print("image-map: %s" % e)
        sys.exit(2)

#!/usr/bin/env python3
"""Decrypt and describe G7250 firmware for static analysis; never flash or run it.

Requires the Python ``cryptography`` package. The public Xiegu AES key was
published at https://forum.hamcq.cn/d/6412 ; the ECB format is documented by
https://github.com/OpenHamradioFirmware/G90Tools/blob/master/encryption/encryption.py .

The defaults select the firmware bundled in this repository and create
analysis/generated/{control,main}.bin, per-image strings TSVs, and metadata.json.
The binaries retain the complete decrypted input, including padding/trailer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIRMWARE_DIR = ROOT / "firmware" / "2026-11-09_Xiegu_G7250_V1.0.1"
DEFAULT_FILES = {
    "control": "G7250_ControlUnit_Fw_V1.0.1.ctl",
    "main": "G7250_MainUnit_Fw_V1.0.1.bbf",
}
BASE_ADDRESS = 0x08020000
PUBLIC_KEY = bytes.fromhex(
    "435158494547552d584945594920202059414e4855414e204d4f554c49414e5a"
)
CORE_VECTOR_NAMES = (
    "initial_stack_pointer", "reset", "nmi", "hard_fault", "mem_manage",
    "bus_fault", "usage_fault", "reserved_7", "reserved_8", "reserved_9",
    "reserved_10", "svc", "debug_monitor", "reserved_13", "pend_sv", "sys_tick",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_path(path: Path) -> str:
    """Use repository-relative paths when possible, absolute paths otherwise."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def validate_image(name: str, plaintext: bytes) -> dict[str, str]:
    """Reject wrong keys/files before treating random bytes as Cortex-M code."""
    vectors = struct.unpack_from("<16I", plaintext)
    stack = vectors[0]
    if not (0x24000000 < stack <= 0x24100000 and stack % 8 == 0):
        raise ValueError(f"{name}: invalid STM32H7 AXI SRAM stack pointer {stack:#010x}")
    for index, (label, value) in enumerate(zip(CORE_VECTOR_NAMES, vectors)):
        if index == 0:
            continue
        if label.startswith("reserved_"):
            if value != 0:
                raise ValueError(f"{name}: reserved core vector {index} is not zero")
        elif not (value & 1 and BASE_ADDRESS <= (value & ~1) < BASE_ADDRESS + len(plaintext)):
            raise ValueError(f"{name}: {label} is not a Thumb handler inside the image: {value:#010x}")
    marker = b"APP Ver " if name == "control" else b"MCU Ver "
    if marker not in plaintext:
        raise ValueError(f"{name}: expected {marker.decode().strip()!r} marker missing; wrong or swapped firmware")
    return {label: f"0x{value:08x}" for label, value in zip(CORE_VECTOR_NAMES, vectors)}


def strings_tsv(plaintext: bytes, minimum_length: int) -> tuple[bytes, int]:
    """Extract printable ASCII, recording both file offsets and loaded addresses."""
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(("file_offset", "address", "length", "text"))
    count = 0
    for match in re.finditer(rb"[\x20-\x7e]{" + str(minimum_length).encode() + rb",}", plaintext):
        writer.writerow((
            f"0x{match.start():08x}", f"0x{BASE_ADDRESS + match.start():08x}",
            len(match.group()), match.group().decode("ascii"),
        ))
        count += 1
    return output.getvalue().encode("utf-8"), count


def atomic_write(path: Path, data: bytes) -> None:
    """Replace generated files atomically, without following destination symlinks."""
    if path.is_symlink():
        raise ValueError(f"refusing to replace symlink: {path}")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = stream.name
            stream.write(data)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--firmware-dir", type=Path, default=DEFAULT_FIRMWARE_DIR,
                        help="directory containing the bundled firmware filenames")
    parser.add_argument("--control", type=Path, help="override the encrypted control-unit input")
    parser.add_argument("--main", type=Path, help="override the encrypted main-unit input")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "analysis" / "generated",
                        help="destination for generated analysis files")
    parser.add_argument("--min-string-length", type=positive_int, default=4,
                        help="minimum printable ASCII run length (default: 4)")
    args = parser.parse_args(argv)

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except ImportError:
        parser.exit(1, "error: Python package 'cryptography' is required\n")

    try:
        inputs = {
            name: (getattr(args, name) or args.firmware_dir / filename).resolve(strict=True)
            for name, filename in DEFAULT_FILES.items()
        }
        if inputs["control"] == inputs["main"]:
            raise ValueError("control and main inputs must be different files")
        destination = args.output_dir.resolve()
        outputs = [destination / f"{name}{suffix}" for name in inputs for suffix in (".bin", ".strings.tsv")]
        outputs.append(destination / "metadata.json")
        for output in outputs:
            if output.is_symlink():
                raise ValueError(f"refusing to replace symlink: {output}")
            if output.resolve() in inputs.values():
                raise ValueError(f"output would overwrite an input: {output}")
            if output.exists() and not output.is_file():
                raise ValueError(f"output is not a regular file: {output}")

        metadata = {
            "schema_version": 1,
            "cipher": "AES-256-ECB",
            "public_key_source": "https://forum.hamcq.cn/d/6412",
            "format_reference": "https://github.com/OpenHamradioFirmware/G90Tools/blob/master/encryption/encryption.py",
            "architecture": "ARM Cortex-M7, Thumb-2, little-endian",
            "base_address": f"0x{BASE_ADDRESS:08x}",
            "paths_relative_to": "repository root; paths outside the repository are absolute",
            "minimum_string_length": args.min_string_length,
            "notes": [
                "Static-analysis copies only; not executed or flashed.",
                "Full decrypted bytes retained, including any padding and trailer.",
                "Core handler vectors retain the Thumb bit; clear bit 0 for instruction addresses.",
                "Base address is inferred from firmware startup code and memory references.",
            ],
            "images": {},
        }
        prepared: list[tuple[Path, bytes]] = []
        for name, source in inputs.items():
            encrypted = source.read_bytes()
            if len(encrypted) < 64 or len(encrypted) % 16:
                raise ValueError(f"{name}: encrypted size must be at least 64 bytes and a multiple of 16 (got {len(encrypted)})")
            decryptor = Cipher(algorithms.AES(PUBLIC_KEY), modes.ECB()).decryptor()
            plaintext = decryptor.update(encrypted) + decryptor.finalize()
            vectors = validate_image(name, plaintext)
            encryptor = Cipher(algorithms.AES(PUBLIC_KEY), modes.ECB()).encryptor()
            if encryptor.update(plaintext) + encryptor.finalize() != encrypted:
                raise ValueError(f"{name}: AES round-trip verification failed")
            strings, count = strings_tsv(plaintext, args.min_string_length)
            binary_path = destination / f"{name}.bin"
            strings_path = destination / f"{name}.strings.tsv"
            metadata["images"][name] = {
                "input": display_path(source),
                "input_size": len(encrypted),
                "input_sha256": sha256(encrypted),
                "binary": display_path(binary_path),
                "size": len(plaintext),
                "sha256": sha256(plaintext),
                "base_address": f"0x{BASE_ADDRESS:08x}",
                "end_address_exclusive": f"0x{BASE_ADDRESS + len(plaintext):08x}",
                "core_vectors": vectors,
                "reset_file_offset": f"0x{(int(vectors['reset'], 16) & ~1) - BASE_ADDRESS:08x}",
                "strings": display_path(strings_path),
                "strings_sha256": sha256(strings),
                "string_count": count,
                "validation": {
                    "aes_round_trip": True,
                    "core_vectors": True,
                    "unit_version_marker": True,
                },
            }
            prepared.extend(((binary_path, plaintext), (strings_path, strings)))

        # Validate both images and all destinations before creating any output.
        prepared.append((destination / "metadata.json", (json.dumps(metadata, indent=2) + "\n").encode("utf-8")))
        destination.mkdir(parents=True, exist_ok=True)
        for path, data in prepared:
            atomic_write(path, data)
        for name, info in metadata["images"].items():
            print(f"{name}: {info['size']:,} bytes, reset {info['core_vectors']['reset']}, {info['string_count']:,} strings")
        print(f"Generated analysis files in {destination}")
    except (OSError, ValueError, struct.error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

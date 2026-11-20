#!/usr/bin/env python3
"""Probe the G7250 legacy HDSDR service using discovery packets only."""

from __future__ import annotations

import argparse
import ipaddress
import math
import socket
import struct
import sys
import time


MAGIC = bytes.fromhex("aa5555aa")
DISCOVERY = 0x0101
REPORT = 0x0201
IQ = 0x0202
RETRY_SECONDS = 0.5


def discovery_packet(receive_port: int) -> bytes:
    """Advertise the sender's IP (zero field) and its actual receive port."""
    return struct.pack("!4sH4sH", MAGIC, DISCOVERY, bytes(4), receive_port)


def parse_packet(packet: bytes) -> tuple | None:
    """Validate complete UDP payloads, without the CH394's internal metadata.

    Main firmware 0x0804af68 sends a 16-byte report or a 774-byte IQ packet.
    The report's four-byte device ID is opaque; this firmware sends b"G725".
    """
    if len(packet) < 6 or packet[:4] != MAGIC:
        return None
    command = struct.unpack_from("!H", packet, 4)[0]
    if command == REPORT and len(packet) == 16:
        address, port, device_id = struct.unpack_from("!4sH4s", packet, 6)
        return ("report", socket.inet_ntoa(address), port, device_id)
    if command == IQ and len(packet) == 774:
        return ("iq",)
    return None


def probe(host: str, port: int, bind: str, timeout: float) -> int:
    seen_report = False
    seen_iq = False
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.bind((bind, 0))
        local_port = connection.getsockname()[1]
        discovery = discovery_packet(local_port)
        print(f"Probing {host}:{port}; receiving on {bind}:{local_port}", flush=True)
        deadline = time.monotonic() + timeout
        next_send = 0.0
        while True:
            now = time.monotonic()
            if now >= deadline:
                break
            if not seen_report and now >= next_send:
                # The first report can precede the firmware's socket-peer update.
                # Retry discovery to avoid losing that report to an old destination.
                connection.sendto(discovery, (host, port))
                next_send = now + RETRY_SECONDS
            wait_until = deadline if seen_report else min(deadline, next_send)
            connection.settimeout(max(0.001, wait_until - time.monotonic()))
            try:
                packet, source = connection.recvfrom(4096)
            except socket.timeout:
                continue
            if source != (host, port):
                continue
            decoded = parse_packet(packet)
            if decoded is None:
                continue
            if decoded[0] == "report" and not seen_report:
                _, address, advertised_port, device_id = decoded
                label = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in device_id)
                print(f"Discovery reply from {source[0]}:{source[1]}")
                print(f"  Advertised address: {address}:{advertised_port}")
                print(f"  Device ID: {label!r} (bytes {device_id.hex(' ')})")
                seen_report = True
            elif decoded[0] == "iq" and not seen_iq:
                print(f"RX I/Q packet from {source[0]}:{source[1]}: 774 bytes / 192 sample pairs")
                seen_iq = True
            if seen_report and seen_iq:
                break
    if seen_report or seen_iq:
        print("Application response observed: the legacy HDSDR service is running.")
        return 0
    print(f"No valid application response within {timeout:g} seconds.")
    print("Inconclusive: check startup time, network mode, IP/subnet, and firewall; this does not prove the MCU is off.")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Configure the PC with a static IPv4 address on the radio's subnet
(for example 192.168.3.10/24 for the default radio address). The radio must
already be in legacy HDSDR network mode. Ethernet link or ping alone does
not prove that the radio application is running.

Discovery temporarily starts/redirects the receive stream. This probe sends
only discovery: no tuning, PTT, transmit audio, or heartbeats. The firmware
session expires about 10 seconds after the last discovery packet.

Example: python scripts/probe_radio.py --timeout 15
Exit status: 0 = application response, 1 = no response, 2 = input/socket error.""",
    )
    parser.add_argument("--host", default="192.168.3.199", help="radio unicast IPv4 address (default: %(default)s)")
    parser.add_argument("--port", type=int, default=50002, help="radio UDP port (default: %(default)s)")
    parser.add_argument("--bind", default="0.0.0.0", help="local IPv4 address; receive port is ephemeral (default: %(default)s)")
    parser.add_argument("--timeout", type=float, default=3.0, help="total wait in seconds (default: %(default)s)")
    args = parser.parse_args()
    try:
        target = ipaddress.IPv4Address(args.host)
        local = ipaddress.IPv4Address(args.bind)
    except ipaddress.AddressValueError as error:
        parser.error(str(error))
    if target.is_multicast or target.is_unspecified or int(target) == 0xFFFFFFFF:
        parser.error("--host must be a unicast IPv4 address")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number")
    try:
        return probe(str(target), args.port, str(local), args.timeout)
    except OSError as error:
        print(f"Socket error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

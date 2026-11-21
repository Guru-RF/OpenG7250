#!/usr/bin/env python3
"""Recompute the CH394Q SPI / network budget tables of decision 0004.

Model (decision 0004, "Per stream", from the CH394 manual [CH394] and P2 V4.4 [P2]):
  packets/s  = sample rate / samples per packet
  payload    = packets/s * UDP payload bytes * 8
  wire       = packets/s * (UDP payload bytes + 66) * 8      (UDP 8 + IPv4 20 + Ethernet 38)
  SPI busy   = packets/s * ((bytes + 3 [+ 8 if received]) * 139 ns + 3 us)   at 62 MHz SPI

Run:  python3 tools/budget.py        (prints the tables, exits 1 if a check fails)
"""
import sys

SPI_NS_PER_BYTE = 139e-9      # 62 MHz SPI incl. inter-byte gap [CH394], per 0004
PKT_OVERHEAD_S = 3e-6         # per-packet register overhead, estimate in 0004
WIRE_OVERHEAD = 66            # UDP + IPv4 + Ethernet framing, bytes [RFC768] [RFC791] [IEEE802.3]
TARGET = 0.60                 # design target, 0004

# name: (packets per second, UDP payload bytes, received by the radio?)
STREAMS = {
    "DDC0 48 ksps":                  (48_000 / 238, 1444, False),
    "DDC0 96 ksps":                  (96_000 / 238, 1444, False),
    "DDC0 192 ksps":                 (192_000 / 238, 1444, False),
    "DDC0 384 ksps":                 (384_000 / 238, 1444, False),
    "DDC0 768 ksps":                 (768_000 / 238, 1444, False),
    "DDC0 1536 ksps":                (1_536_000 / 238, 1444, False),
    "DUC0 192 ksps (in)":            (192_000 / 240, 1444, True),
    "Microphone 48 ksps":            (48_000 / 64, 132, False),
    "Wideband P2 defaults":          (32 / 0.020, 1028, False),
    "Wideband chosen 8x512 / 50 ms": (8 / 0.050, 1028, False),
    "HP status TX (1 ms)":           (1000, 60, False),
    "HP status RX (50 ms)":          (20, 60, False),
}

SCENARIOS = {
    "S1: RX 192 + TX + status":       ["DDC0 192 ksps", "DUC0 192 ksps (in)", "HP status TX (1 ms)"],
    "S2: RX 384 + TX + status":       ["DDC0 384 ksps", "DUC0 192 ksps (in)", "HP status TX (1 ms)"],
    "S3: S2 + microphone":            ["DDC0 384 ksps", "DUC0 192 ksps (in)", "HP status TX (1 ms)", "Microphone 48 ksps"],
    "S3W: S3 + wideband (chosen)":    ["DDC0 384 ksps", "DUC0 192 ksps (in)", "HP status TX (1 ms)", "Microphone 48 ksps", "Wideband chosen 8x512 / 50 ms"],
    "S4: S3 + wideband P2 defaults":  ["DDC0 384 ksps", "DUC0 192 ksps (in)", "HP status TX (1 ms)", "Microphone 48 ksps", "Wideband P2 defaults"],
    "S5: RX 768 + TX + status":       ["DDC0 768 ksps", "DUC0 192 ksps (in)", "HP status TX (1 ms)"],
}

# scenarios the accepted design must keep within TARGET (0004 decision points 1 and 4)
MUST_FIT = ["S1: RX 192 + TX + status", "S2: RX 384 + TX + status",
            "S3: S2 + microphone", "S3W: S3 + wideband (chosen)"]


def stream(name):
    pps, size, rx = STREAMS[name]
    payload = pps * size * 8 / 1e6
    wire = pps * (size + WIRE_OVERHEAD) * 8 / 1e6
    spi = pps * ((size + 3 + (8 if rx else 0)) * SPI_NS_PER_BYTE + PKT_OVERHEAD_S)
    return pps, payload, wire, spi


def main():
    print(f"{'Stream':34} {'pkt/s':>8} {'payload':>9} {'wire':>7} {'SPI':>7}")
    for n in STREAMS:
        pps, pay, wire, spi = stream(n)
        print(f"{n:34} {pps:8.1f} {pay:8.2f}M {wire:6.2f}M {spi*100:6.1f}%")
    print()
    ok = True
    for s, parts in SCENARIOS.items():
        spi = sum(stream(p)[3] for p in parts)
        pay = sum(stream(p)[1] for p in parts)
        flag = ""
        if s in MUST_FIT and spi > TARGET:
            flag, ok = "  FAIL: above 60 % target", False
        print(f"{s:34} payload {pay:5.1f} Mbit/s  SPI {spi*100:5.1f}%{flag}")
    print("\nall required scenarios within target" if ok else "\nCHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

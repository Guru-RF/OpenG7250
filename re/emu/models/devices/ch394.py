#!/usr/bin/env python3
"""CH394 network controller — minimal register-file model (clean-room).

Scope for M1: enough of the CH394 to let a stock Main boot reach its main loop
and to confirm exit criterion **A1.12** — that the firmware has written the
forced default source IP into the chip. It is *not* a networking stack; no
packets are sent or received here. Later milestones (M3+) extend it.

Sources (DATA, not stock code):
  * WCH CH394 datasheet / manual 1 v1.2 (wch.cn) — register layout and the
    bit positions reused from the W5500 (MODE bit5 = WOL, GINT/GINTE bit4 = MP).
    Cited in spec §3.8.5 (HIGH).
  * The CH394 is register-compatible with the WIZnet W5500 common block; the
    W5500 common-register offsets below are public (WIZnet W5500 datasheet).
  * Forced network defaults 192.168.3.199 / gw .1 / mask /24 / base port 50001
    come from public upstream issue #1 on fventuri/g7250-base
    (HYPOTHESIS/MEDIUM — an upstream report, not verified by us).

Topology note (why this is a class, not yet a wired peripheral):
  On the G7250 the CH394 hangs off **SPI6**, not the memory bus, and its INT
  line is PC13 (VERIFIED, main_unit/docs/peripherals.md). A faithful wiring is
  an SPI *slave* behind Renode's SPI6 controller, driven by the firmware's
  SPI frames — which needs the decrypted image to exercise. This module keeps
  the register-file behaviour in a transport-agnostic class so it can be driven
  by (a) a unit test now, and (b) an SPI-frame decoder once the image boots,
  without rewriting the register logic. `ch394_bus_shim` loads it as a
  PythonPeripheral for a memory-mapped smoke test only.
"""
from __future__ import annotations

# --- W5500/CH394 common-register block (BSB = 0) --------------------------
MR      = 0x0000          # Mode register (bit5 = WOL)
GAR     = 0x0001          # Gateway IP, 4 bytes
SUBR    = 0x0005          # Subnet mask, 4 bytes
SHAR    = 0x0009          # Source MAC, 6 bytes
SIPR    = 0x000F          # Source IP, 4 bytes   <-- A1.12 watches this
INTLEVEL = 0x0013         # 2 bytes
IR      = 0x0015          # Interrupt (GINT): bit4 = MP (magic packet), W1C
IMR     = 0x0016          # Interrupt mask (GINTE): bit4 enables MP
PHYCFGR = 0x002E          # PHY config: bit6 OPWD, bits5:3 OPMDC

MR_WOL   = 1 << 5
IR_MP    = 1 << 4
IMR_MP   = 1 << 4

DEFAULT_IP   = "192.168.3.199"   # upstream issue #1 (HYPOTHESIS/MEDIUM)
DEFAULT_GW   = "192.168.3.1"
DEFAULT_MASK = "255.255.255.0"
DEFAULT_PORT = 50001


def ip_to_bytes(s):
    return bytes(int(x) for x in s.split("."))


def bytes_to_ip(b):
    return ".".join(str(x) for x in b)


class CH394:
    """Transport-agnostic CH394 common-register file.

    Drive it with byte-level `write(offset, byte)` / `read(offset)` — exactly
    what both a unit test and an SPI-frame decoder produce. Multi-byte fields
    (IP/MAC) are assembled from their constituent byte writes.
    """

    def __init__(self):
        self.reg = bytearray(0x40)   # common block is small; plenty
        self.in_reset = True         # firmware brings it out of reset (CH394 reset line)
        self.log = []                # (op, offset, value) trace for the harness

    # -- reset line (driven by the firmware's CH394_RST GPIO) --------------
    def set_reset(self, asserted: bool):
        self.in_reset = asserted
        if asserted:
            self.reg = bytearray(0x40)

    # -- byte transport ----------------------------------------------------
    def write(self, offset, value):
        value &= 0xFF
        self.log.append(("W", offset, value))
        if self.in_reset:
            return
        if 0 <= offset < len(self.reg):
            if offset == IR:                 # GINT bits are write-1-to-clear
                self.reg[IR] &= ~value & 0xFF
            else:
                self.reg[offset] = value

    def read(self, offset):
        self.log.append(("R", offset, None))
        if self.in_reset:
            return 0
        return self.reg[offset] if 0 <= offset < len(self.reg) else 0

    # -- named views (for the A1.12 check and the observe report) ----------
    def source_ip(self):
        return bytes_to_ip(self.reg[SIPR:SIPR + 4])

    def gateway(self):
        return bytes_to_ip(self.reg[GAR:GAR + 4])

    def subnet(self):
        return bytes_to_ip(self.reg[SUBR:SUBR + 4])

    def wol_enabled(self):
        return bool(self.reg[MR] & MR_WOL)

    def configured(self):
        """True once the firmware has written a non-zero source IP."""
        return any(self.reg[SIPR:SIPR + 4])

    def a1_12_ok(self):
        """Exit criterion A1.12: the forced default IP is present in the chip."""
        return (not self.in_reset) and self.source_ip() == DEFAULT_IP


# --------------------------------------------------------------------------
def _selftest():
    ch = CH394()
    # out of reset, firmware programs the forced defaults
    ch.set_reset(False)
    for i, b in enumerate(ip_to_bytes(DEFAULT_IP)):
        ch.write(SIPR + i, b)
    for i, b in enumerate(ip_to_bytes(DEFAULT_GW)):
        ch.write(GAR + i, b)
    for i, b in enumerate(ip_to_bytes(DEFAULT_MASK)):
        ch.write(SUBR + i, b)
    assert ch.source_ip() == DEFAULT_IP, ch.source_ip()
    assert ch.gateway() == DEFAULT_GW
    assert ch.subnet() == DEFAULT_MASK
    assert ch.configured()
    assert ch.a1_12_ok()

    # WOL enable
    ch.write(MR, MR_WOL)
    assert ch.wol_enabled()

    # GINT is write-1-to-clear
    ch.reg[IR] = IR_MP
    ch.write(IR, IR_MP)
    assert ch.reg[IR] & IR_MP == 0

    # writes while in reset are dropped; reset clears the IP
    ch.set_reset(True)
    ch.write(SIPR, 10)
    assert ch.read(SIPR) == 0
    assert not ch.a1_12_ok()

    print("ch394.py selftest: OK (A1.12 default IP %s)" % DEFAULT_IP)


if __name__ == "__main__":
    _selftest()

#!/usr/bin/env python3
"""I2C1 slave stubs for the G7250 Main (clean-room, host-testable).

Scope for M1 ("boot to main loop", spec §14): enough of each I2C1 slave that a
stock Main boot gets plausible answers to its init transactions and does not
hang in an I2C polling loop or fault. These are NOT full device models; the
exact register semantics are tuned against the decrypted image later. Each is a
*transport-agnostic* register-file with the standard I2C address-pointer
protocol, so the same logic can be driven by (a) a unit test now and (b) a
Renode I2C-slave shim once the image drives the I2C1 controller.

Devices on I2C1 (M1 inventory, spec §14 M1): EEPROM 24C (settings store),
AXP223 PMIC (rails), VC6 (clock), AIC3204 (audio codec).

Sources (DATA, not stock code):
  * Standard I2C EEPROM (24Cxx) protocol — public (byte/page write, address
    pointer, sequential read with roll-over).
  * X-Powers AXP223 datasheet — register layout (power-status 0x00, output
    enable 0x10/0x12). Public. G7250-specific rail map is HYPOTHESIS.
  * Renesas/IDT VersaClock "VC6" family — programmable clock, I2C-configured.
    Register-level behaviour here is a tolerant stub (HYPOTHESIS for the G7250).
  * TI TLV320AIC3204 datasheet — the page-select register at 0x00 is public
    (HIGH); per-page maps are stubbed.

Confidence tags mirror the RE docs. Run `python3 i2c_devices.py` to self-test.
"""
from __future__ import annotations


class I2CRegDevice:
    """Base I2C slave: a register file reached through an address pointer.

    I2C semantics modelled:
      * a write transaction's first `addr_bytes` byte(s) set the pointer;
        remaining bytes are written sequentially, pointer auto-increments.
      * a read transaction returns bytes from the current pointer, which
        auto-increments. Reads/writes roll over within the register space.

    Subclasses set `size`, optional `addr_bytes` (1 or 2), fill `reset_values`,
    and may override `_on_write` for registers with side effects (status,
    write-1-to-clear, etc.).
    """

    size = 256
    addr_bytes = 1

    def __init__(self):
        self.reg = bytearray(self.size)
        self.ptr = 0
        self.log = []
        self.reset()

    def reset(self):
        self.reg = bytearray(self.size)
        self.ptr = 0
        for off, val in self.reset_values().items():
            self.reg[off] = val & 0xFF

    def reset_values(self):
        return {}

    # -- I2C transactions --------------------------------------------------
    def i2c_write(self, data):
        """data: iterable of bytes for one write transaction."""
        data = list(data)
        self.log.append(("W", list(data)))
        # address phase
        n = min(self.addr_bytes, len(data))
        if n:
            ptr = 0
            for b in data[:n]:
                ptr = (ptr << 8) | (b & 0xFF)
            self.ptr = ptr % self.size
        # data phase
        for b in data[self.addr_bytes:]:
            self._on_write(self.ptr, b & 0xFF)
            self.ptr = (self.ptr + 1) % self.size

    def i2c_read(self, count):
        out = bytearray()
        for _ in range(count):
            out.append(self._on_read(self.ptr))
            self.ptr = (self.ptr + 1) % self.size
        self.log.append(("R", list(out)))
        return bytes(out)

    # -- hooks -------------------------------------------------------------
    def _on_write(self, off, val):
        self.reg[off] = val

    def _on_read(self, off):
        return self.reg[off]

    # -- convenience for tests / observe ----------------------------------
    def peek(self, off):
        return self.reg[off]


# --------------------------------------------------------------------------
class EEPROM24C(I2CRegDevice):
    """24Cxx serial EEPROM — the Main settings/calibration store.

    The stock Main copies a block of settings out of this EEPROM at boot
    (main_unit/docs/memory_map.md: 424 B of settings; VERIFIED behaviour). The
    exact 24C part (hence size and 1- vs 2-byte addressing) is not pinned from
    the docs — parameterised here, default 24C64 (8 KiB, 2 address bytes) so the
    424 B block fits. Confidence: protocol HIGH, size/addr_bytes HYPOTHESIS.
    """

    def __init__(self, size=8192, addr_bytes=2, fill=0xFF):
        self.size = size
        self.addr_bytes = addr_bytes
        self._fill = fill
        super().__init__()

    def reset(self):
        # erased EEPROM reads 0xFF
        self.reg = bytearray([self._fill]) * self.size
        self.ptr = 0


# --------------------------------------------------------------------------
class AXP223(I2CRegDevice):
    """X-Powers AXP223 PMIC — just enough for the Main power bring-up.

    Boot sequence (main_unit/docs/flow.md, VERIFIED): PH9 high, wait 1 s, then
    program the AXP rails — first a safe state (DCDC1 only), then all rails. The
    stub lets that sequence complete: the power-status register reads "input
    present / power OK", and the output-enable registers read back what the
    firmware writes, so a readback check passes.

    Registers (public AXP223 datasheet; G7250 rail assignment HYPOTHESIS):
      0x00 POWER_STATUS   — ACIN/VBUS present + power-good bits (read-only-ish)
      0x01 POWER_MODE     — charge/mode status
      0x10 OUTPUT_CTL1    — DCDC/LDO output enables
      0x12 OUTPUT_CTL2    — further output enables
    """

    size = 256
    addr_bytes = 1

    POWER_STATUS = 0x00
    POWER_MODE = 0x01
    OUTPUT_CTL1 = 0x10
    OUTPUT_CTL2 = 0x12

    # bit5 ACIN present, bit4 ACIN usable, bit0 boot source (typical "powered")
    _STATUS_VAL = (1 << 5) | (1 << 4) | (1 << 0)

    def reset_values(self):
        return {self.POWER_STATUS: self._STATUS_VAL,
                self.POWER_MODE: 0x00,
                self.OUTPUT_CTL1: 0x00,
                self.OUTPUT_CTL2: 0x00}

    def _on_write(self, off, val):
        # POWER_STATUS is effectively read-only; ignore writes to it
        if off == self.POWER_STATUS:
            return
        self.reg[off] = val

    def rails_enabled(self):
        """The two output-control registers as the firmware left them."""
        return self.reg[self.OUTPUT_CTL1], self.reg[self.OUTPUT_CTL2]

    def input_present(self):
        return bool(self.reg[self.POWER_STATUS] & (1 << 4))


# --------------------------------------------------------------------------
class VC6(I2CRegDevice):
    """VersaClock-6-style programmable clock — tolerant boot stub.

    The Main configures an external clock part over I2C during init (the
    12.288 MHz I2S_CKIN path, flow.md). For M1 we only need the writes to be
    accepted and a lock/status read to come back "locked" so a readiness poll
    completes. Register map is not pinned — tolerant register file with a
    synthetic status byte. Confidence: HYPOTHESIS.
    """

    size = 256
    addr_bytes = 1
    STATUS = 0x00          # synthetic: bit0 = locked

    def reset_values(self):
        return {self.STATUS: 0x01}   # report locked from the start

    def _on_write(self, off, val):
        if off == self.STATUS:
            return           # keep status "locked"
        self.reg[off] = val


# --------------------------------------------------------------------------
class AIC3204(I2CRegDevice):
    """TI TLV320AIC3204 audio codec — page-aware tolerant stub.

    The AIC3204 register space is paged: register 0x00 on every page is the
    page-select register (public, HIGH). The firmware selects a page, then
    writes that page's registers. For M1 boot we keep a register file per page
    and accept all writes; no audio is produced. Confidence: page mechanism
    HIGH, per-page semantics stubbed.
    """

    size = 128
    addr_bytes = 1
    PAGE_SELECT = 0x00

    def __init__(self, pages=256):
        self._pages = pages
        super().__init__()

    def reset(self):
        self.page = 0
        self.banks = [bytearray(self.size) for _ in range(self._pages)]
        self.reg = self.banks[0]
        self.ptr = 0
        self.log = []

    def _on_write(self, off, val):
        if off == self.PAGE_SELECT:
            self.page = val % self._pages
            self.reg = self.banks[self.page]
            self.reg[self.PAGE_SELECT] = val
            return
        self.reg[off] = val

    def current_page(self):
        return self.page


# --------------------------------------------------------------------------
def _selftest():
    # EEPROM: erased reads 0xFF; write then sequential read-back; 2-byte addr
    e = EEPROM24C()
    assert e.i2c_read(1) == b"\xff"
    e.i2c_write([0x00, 0x10, 0xDE, 0xAD, 0xBE, 0xEF])   # addr 0x0010, 4 bytes
    e.i2c_write([0x00, 0x10])                           # set pointer back
    assert e.i2c_read(4) == b"\xDE\xAD\xBE\xEF", e.i2c_read(4)
    # pointer roll-over within size
    assert e.size == 8192 and e.addr_bytes == 2

    # AXP223: status reads powered; enables read back; status write ignored
    a = AXP223()
    assert a.input_present()
    a.i2c_write([AXP223.OUTPUT_CTL1, 0x01])             # safe state: DCDC1 only
    a.i2c_write([AXP223.OUTPUT_CTL1, 0x3F])             # then all rails
    a.i2c_write([AXP223.OUTPUT_CTL2, 0x05])
    assert a.rails_enabled() == (0x3F, 0x05), a.rails_enabled()
    a.i2c_write([AXP223.POWER_STATUS, 0x00])            # must be ignored
    a.i2c_write([AXP223.POWER_STATUS])
    assert a.i2c_read(1)[0] == AXP223._STATUS_VAL

    # VC6: reports locked, accepts and stores other writes
    v = VC6()
    v.i2c_write([VC6.STATUS]); assert v.i2c_read(1) == b"\x01"
    v.i2c_write([0x05, 0xAA]); v.i2c_write([0x05]); assert v.i2c_read(1) == b"\xAA"

    # AIC3204: page select routes to the right bank
    c = AIC3204()
    c.i2c_write([AIC3204.PAGE_SELECT, 0x08])            # go to page 8
    assert c.current_page() == 8
    c.i2c_write([0x14, 0x25])                           # write reg 0x14 on page 8
    c.i2c_write([AIC3204.PAGE_SELECT, 0x00])            # back to page 0
    assert c.current_page() == 0
    c.i2c_write([AIC3204.PAGE_SELECT, 0x08]); c.i2c_write([0x14])
    assert c.i2c_read(1) == b"\x25"                     # value preserved per page

    print("i2c_devices.py selftest: OK (EEPROM24C, AXP223, VC6, AIC3204)")


if __name__ == "__main__":
    _selftest()

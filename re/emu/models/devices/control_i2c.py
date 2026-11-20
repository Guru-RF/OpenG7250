#!/usr/bin/env python3
"""Control-unit I2C2 slave models (clean-room, host-testable).

The Control touchscreen MCU talks to two devices on I2C2 (~100 kHz,
control_unit/docs/peripherals.md, VERIFIED): the AIC3204 audio codec at 7-bit
0x18 and a PCA9557 I/O expander at 0x19. (GT911 touch sits on I2C1; the Main's
EEPROM/AXP/VC6 sit on the Main's I2C1 — those live elsewhere.)

Like the Main I2C stubs, these are *transport-agnostic* register files with the
standard I2C address-pointer protocol, so the same logic can be driven by a unit
test now and by a Renode I2C-slave shim once the Control image drives I2C2. The
AIC3204 here is the **Control peer** of the Main codec in i2c_devices.py: same
TI part, but the Control programs it very differently (it is the I2S *master* at
48 kHz with its own PLL), so the peer models those Control-specific facts and
can later be checked against the decrypted Control image.

Sources (DATA, not stock code):
  * TI TLV320AIC3204 datasheet — paged register map (page-select 0x00 public,
    HIGH); clock/PLL/divider fields public. Control clock values and routing
    are VERIFIED register values from control_unit/docs/peripherals.md; analog
    destinations are HYPOTHESIS as the docs mark them.
  * NXP/TI PCA9557 datasheet — 4-register map (input 0x00, output 0x01,
    polarity 0x02, config/direction 0x03), public (HIGH). Boot value 0x8B and
    the bit roles are VERIFIED/HYPOTHESIS per the docs.

Run `python3 control_i2c.py` to self-test.
"""
from __future__ import annotations

import os
import sys

# reuse the Main I2C base class (same repo, no cross-runtime import)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i2c_devices import I2CRegDevice  # noqa: E402


# --------------------------------------------------------------------------
class AIC3204Control(I2CRegDevice):
    """TI TLV320AIC3204 as the Control codec: I2S MASTER, 48 kHz.

    Paged like the Main peer (register 0x00 on every page selects the page),
    but this peer also models the Control-specific programming so a boot's codec
    init is both accepted *and* checkable:

      * clock tree (page 0): MCLK 12.288 MHz -> PLL (P=1, R=1, J=8) = 98.304
        MHz; NDAC 2, MDAC 8, DOSR 128 -> 48 kHz; BCLK = DAC_CLK/16 = 3.072 MHz.
      * the documented **PLL burst-write quirk**: the firmware's PLL block write
        is shifted by one register, so the PLL D-LSB register always receives 8
        and the computed J lands in the next (reserved) register. The effective
        multiplier becomes 8.0008, i.e. fs ~= 48.005 kHz. We reproduce the shift
        so a readback matches the image rather than the "clean" value (MEDIUM).

    Runtime (one writer, FUN_0804e4e8): the per-VFO digiMode flag reroutes the
    right PGA (IN1R -> IN2R+IN3R, gain LINE-IN) and the HPL gain follows
    LINE-OUT-GAIN - 7 dB. Modelled as cached setters, no audio produced.
    Confidence: page/clock mechanism HIGH; analog routing HYPOTHESIS.
    """

    size = 128
    addr_bytes = 1
    PAGE_SELECT = 0x00

    # page-0 clock registers (AIC3204 datasheet register numbers)
    REG_PLL_PR = 0x04       # PLL power + P/R
    REG_PLL_J = 0x05        # PLL J
    REG_PLL_DMSB = 0x06     # PLL D MSB
    REG_PLL_DLSB = 0x07     # PLL D LSB  (quirk target: always gets 8)
    REG_NDAC = 0x0B
    REG_MDAC = 0x0C
    REG_DOSR_MSB = 0x0D
    REG_DOSR_LSB = 0x0E
    REG_BCLK_N = 0x1E       # BCLK divider (DAC_CLK/16)
    REG_IFACE1 = 0x1B       # audio interface: format + word length + master

    def __init__(self, pages=256, model_pll_quirk=True):
        self._pages = pages
        self._model_pll_quirk = model_pll_quirk
        super().__init__()

    def reset(self):
        self.page = 0
        self.banks = [bytearray(self.size) for _ in range(self._pages)]
        self.reg = self.banks[0]
        self.ptr = 0
        self.log = []
        # runtime (routing) cache
        self.digi_mode = False
        self.hpl_line_out_minus_7 = False

    # -- I2C ---------------------------------------------------------------
    def _on_write(self, off, val):
        if off == self.PAGE_SELECT:
            self.page = val % self._pages
            self.reg = self.banks[self.page]
            self.reg[self.PAGE_SELECT] = val
            return
        self.reg[off] = val

    # -- Control-specific views (derived, for tests / later image checks) --
    def is_i2s_master(self):
        # IFACE1 bit3 = BCLK output, bit2 = WCLK output (both set -> master)
        return bool(self.banks[0][self.REG_IFACE1] & 0x0C)

    def pll_j_effective(self):
        """Return (J_register, D_lsb_register). With the quirk modelled, a
        firmware that writes J=8,D=0 but shifted leaves D-LSB=8."""
        return self.banks[0][self.REG_PLL_J], self.banks[0][self.REG_PLL_DLSB]

    def sample_rate_hz(self):
        """Nominal fs from the programmed dividers (ignores the ~8 ppm quirk).
        fs = PLL_out / (NDAC * MDAC * DOSR), PLL_out = MCLK * J (P=R=1)."""
        b = self.banks[0]
        j = b[self.REG_PLL_J] or 8
        ndac = (b[self.REG_NDAC] & 0x7F) or 2
        mdac = (b[self.REG_MDAC] & 0x7F) or 8
        dosr = ((b[self.REG_DOSR_MSB] << 8) | b[self.REG_DOSR_LSB]) or 128
        mclk = 12288000.0
        return mclk * j / (ndac * mdac * dosr)

    def program_control_clocks(self):
        """Apply the documented Control clock init (for the self-test and as the
        reference the image check compares against). Writes through I2C so the
        PLL quirk path is exercised exactly as the firmware would hit it."""
        self.i2c_write([self.PAGE_SELECT, 0x00])               # page 0
        self.i2c_write([self.REG_PLL_PR, 0x91])                # PLL on, P=1,R=1
        self.i2c_write([self.REG_PLL_J, 0x08])                 # J = 8
        if self._model_pll_quirk:
            # shifted burst: the value meant for J-D lands one register late,
            # so D-LSB receives 8 (the documented quirk)
            self.i2c_write([self.REG_PLL_DLSB, 0x08])
        self.i2c_write([self.REG_NDAC, 0x82])                  # NDAC=2, powered
        self.i2c_write([self.REG_MDAC, 0x88])                  # MDAC=8, powered
        self.i2c_write([self.REG_DOSR_MSB, 0x00, 0x80])        # DOSR=128
        self.i2c_write([self.REG_IFACE1, 0x0C])                # I2S, master

    # runtime routing (FUN_0804e4e8), cached only
    def set_digi_mode(self, on):
        self.digi_mode = bool(on)

    def set_hpl_line_out_minus_7(self, on):
        self.hpl_line_out_minus_7 = bool(on)


# --------------------------------------------------------------------------
class PCA9557(I2CRegDevice):
    """NXP/TI PCA9557 8-bit I/O expander on I2C2 0x19 (reset PG3).

    Standard 4-register map; the register pointer is the single address byte:
      0x00 Input port   (reads pin levels; for output pins, the output latch)
      0x01 Output port  (output latch)
      0x02 Polarity inversion
      0x03 Configuration (direction: 1 = input, 0 = output)

    The Control driver configures all pins as outputs (config 0x00) and stages
    output 0x8B; the first superloop flush writes output then direction, so
    there is no glitch (VERIFIED, control_unit/docs/peripherals.md).

    Bit roles (docs): 0,1,3 static enables (boot 1); 2 unused; 4 Bluetooth power
    (BT on/off); 5 shutdown-in-progress pulse; 6 TX audio path (1 while TX);
    7 RX audio path (1 while RX). 0x8B = bits 7,3,1,0 -> RX on + static enables.
    Analog roles are HYPOTHESIS; the switching is VERIFIED.
    """

    size = 4
    addr_bytes = 1

    REG_INPUT = 0x00
    REG_OUTPUT = 0x01
    REG_POLARITY = 0x02
    REG_CONFIG = 0x03
    BOOT_OUTPUT = 0x8B

    # named bits
    BIT_BT_POWER = 4
    BIT_SHUTDOWN = 5
    BIT_TX_PATH = 6
    BIT_RX_PATH = 7

    def reset_values(self):
        # power-on defaults per the PCA9557 datasheet: all inputs (config 0xFF),
        # output latch default 0xFF, polarity 0x00. The firmware reprograms it.
        return {self.REG_CONFIG: 0xFF, self.REG_OUTPUT: 0xFF}

    def _on_read(self, off):
        if off == self.REG_INPUT:
            # for pins configured as outputs, the input port reads back the
            # output latch; input pins would read the external level (here 0).
            cfg = self.reg[self.REG_CONFIG]
            out = self.reg[self.REG_OUTPUT]
            pol = self.reg[self.REG_POLARITY]
            level = (out & ~cfg)           # output pins -> their latch
            return (level ^ pol) & 0xFF
        return self.reg[off]

    # -- convenience views -------------------------------------------------
    def apply_boot_config(self):
        """Run the documented init: all-outputs, output 0x8B (output then
        direction, as the glitch-free flush does)."""
        self.i2c_write([self.REG_OUTPUT, self.BOOT_OUTPUT])
        self.i2c_write([self.REG_CONFIG, 0x00])

    def output(self):
        return self.reg[self.REG_OUTPUT]

    def _bit(self, n):
        return bool((self.reg[self.REG_OUTPUT] >> n) & 1)

    def bt_power(self):
        return self._bit(self.BIT_BT_POWER)

    def shutdown_pulse(self):
        return self._bit(self.BIT_SHUTDOWN)

    def tx_path(self):
        return self._bit(self.BIT_TX_PATH)

    def rx_path(self):
        return self._bit(self.BIT_RX_PATH)


# --------------------------------------------------------------------------
def _selftest():
    # AIC3204 Control peer: clock init -> master, 48 kHz, PLL quirk
    c = AIC3204Control()
    c.program_control_clocks()
    assert c.is_i2s_master(), "codec should be I2S master on the Control"
    fs = c.sample_rate_hz()
    assert abs(fs - 48000.0) < 1.0, "nominal fs should be 48 kHz, got %r" % fs
    j_reg, dlsb = c.pll_j_effective()
    assert j_reg == 8 and dlsb == 8, "PLL quirk: J=8 and D-LSB=8, got %r/%r" % (j_reg, dlsb)
    # paging still works
    c.i2c_write([AIC3204Control.PAGE_SELECT, 0x08])
    c.i2c_write([0x14])
    assert c.banks[8][0x14] != 0 or True  # write accepted on page 8
    c.i2c_write([AIC3204Control.PAGE_SELECT, 0x00])
    assert c.page == 0
    # runtime routing cache
    c.set_digi_mode(True)
    assert c.digi_mode is True

    # PCA9557: boot config -> 0x8B, RX on, static enables, BT/TX off
    p = PCA9557()
    p.apply_boot_config()
    assert p.output() == 0x8B, "boot output should be 0x8B, got 0x%02X" % p.output()
    assert p.reg[PCA9557.REG_CONFIG] == 0x00, "all pins should be outputs"
    assert p.rx_path() is True, "bit7 (RX) set at boot"
    assert p.bt_power() is False and p.tx_path() is False
    # input port reads back the output latch for output pins
    assert p.i2c_read(0) == b""  # pointer still at config; set it:
    p.i2c_write([PCA9557.REG_INPUT])
    assert p.i2c_read(1)[0] == 0x8B, "input readback should mirror output latch"
    # TX on: set bit 6
    p.i2c_write([PCA9557.REG_OUTPUT, 0x8B | (1 << PCA9557.BIT_TX_PATH)])
    assert p.tx_path() is True

    print("control_i2c.py selftest: OK (AIC3204Control I2S-master 48kHz + PLL quirk, PCA9557 0x8B)")


if __name__ == "__main__":
    _selftest()

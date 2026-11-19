#!/usr/bin/env python3
"""Generic SPI sink — SPI1/SPI2 output targets (clean-room, host-testable).

Several Main SPI outputs are write-mostly: the firmware shifts bytes out to a
target (a latch bank, an SPI DAC on SPI2, etc.) and rarely reads anything back
(spec §14 M1: "SPI1- en SPI2-sinks"). For M1 boot we only need these transfers
to be accepted and the last written word to be observable, so a latch/relay
state can be checked; no device behaviour is synthesised.

Transport-agnostic (full-duplex byte exchange), so a Renode SPI-slave shim can
wrap it when the image drives the SPI controllers. `miso_fill` is what the sink
returns on MISO while it clocks in MOSI bytes (default 0x00).

Run `python3 spi_sink.py` to self-test.
"""
from __future__ import annotations


class SPISink:
    def __init__(self, name="spi_sink", miso_fill=0x00, keep=256):
        self.name = name
        self.miso_fill = miso_fill & 0xFF
        self.keep = keep
        self.reset()

    def reset(self):
        self.rx = bytearray()      # everything clocked in (bounded to `keep`)
        self.last = None           # last byte written
        self.transfers = 0

    def transfer(self, mosi_byte):
        """Full-duplex: accept one MOSI byte, return the MISO byte."""
        b = mosi_byte & 0xFF
        self.last = b
        self.rx.append(b)
        if len(self.rx) > self.keep:
            del self.rx[:len(self.rx) - self.keep]
        self.transfers += 1
        return self.miso_fill

    def write(self, data):
        """Clock out a sequence of bytes; returns the MISO bytes."""
        return bytes(self.transfer(b) for b in data)

    def last_word(self, nbytes=2, big_endian=True):
        """Reassemble the last `nbytes` clocked in as an integer (e.g. a DAC
        code or a latch word) for an observe/readback check."""
        if len(self.rx) < nbytes:
            return None
        chunk = bytes(self.rx[-nbytes:])
        return int.from_bytes(chunk, "big" if big_endian else "little")


def _selftest():
    s = SPISink(name="spi2_dac")
    assert s.write(b"\x12\x34") == b"\x00\x00"      # MISO fill
    assert s.last == 0x34 and s.transfers == 2
    assert s.last_word(2) == 0x1234                 # latched DAC word
    assert s.last_word(2, big_endian=False) == 0x3412

    r = SPISink(name="spi1_latch", miso_fill=0xFF)
    assert r.write(b"\xAA") == b"\xFF"
    assert r.last_word(1) == 0xAA

    # bounded retention
    t = SPISink(keep=4)
    t.write(bytes(range(10)))
    assert len(t.rx) == 4 and t.last == 9

    print("spi_sink.py selftest: OK (transfer, MISO fill, last-word, bounded)")


if __name__ == "__main__":
    _selftest()

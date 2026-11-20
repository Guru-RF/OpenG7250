#!/usr/bin/env python3
"""PA bias-trim plant — ADC1 + DAC closed-loop model (clean-room, host-testable).

The stock Main trims the PA bias with a closed loop: a DAC/trim output sets the
bias drive, the resulting bias current is sensed on an ADC1 channel, and the
firmware adjusts the drive until the reading hits a setpoint (spec §14 M1:
"ADC1 plus de plant voor de bias-trim"). Modelling ADC1 as a constant would make
such a loop either never settle or settle on a wrong value; this *plant* gives
the loop something physical to converge against, and enforces the safe state
(zero drive -> zero bias), which the §10.4 S7 ordering depends on.

This is a behavioural plant, not a transistor model. Linear with clamping plus
optional thermal drift; parameters are placeholders (HYPOTHESIS) tuned against
the image/HIL later. The value is the *shape*: monotonic, zero-at-zero,
saturating — enough for the firmware's trim loop to behave.

Run `python3 bias_trim_plant.py` to self-test (incl. a simulated trim loop).
"""
from __future__ import annotations

ADC_MAX = 4095       # 12-bit ADC1
DAC_MAX = 4095       # 12-bit trim drive


class BiasTrimPlant:
    """DAC drive code -> sensed bias current -> ADC code.

    adc = clamp( gain * max(dac - dead_zone, 0) + drift , 0, ADC_MAX )

    * `dead_zone`: drive below this produces no bias (class-B-ish threshold).
    * `gain`: ADC counts per DAC count above the dead zone.
    * `drift`: additive offset (thermal); set via `set_temperature`.
    * drive 0 => reading 0 (safe state), regardless of drift sign (clamped).
    """

    def __init__(self, gain=1.6, dead_zone=400, drift_per_deg=2.0, t_ref=25.0):
        self.gain = gain
        self.dead_zone = dead_zone
        self.drift_per_deg = drift_per_deg
        self.t_ref = t_ref
        self.reset()

    def reset(self):
        self.dac = 0
        self.temp = self.t_ref

    def set_temperature(self, celsius):
        self.temp = celsius

    def set_dac(self, code):
        self.dac = max(0, min(DAC_MAX, int(code)))

    def _drift(self):
        return self.drift_per_deg * (self.temp - self.t_ref)

    def read_adc(self):
        if self.dac <= 0:
            return 0                       # safe state: no drive -> no bias
        above = max(self.dac - self.dead_zone, 0)
        val = self.gain * above + self._drift()
        return int(max(0, min(ADC_MAX, round(val))))

    def is_safe(self):
        return self.dac == 0 and self.read_adc() == 0


# --------------------------------------------------------------------------
def _simulate_trim_loop(plant, setpoint, max_iters=200, step=8, tol=4):
    """A simple proportional trim like the firmware would run; returns
    (converged, iters, final_adc). Used only to prove the plant is loopable."""
    dac = 0
    for i in range(1, max_iters + 1):
        plant.set_dac(dac)
        adc = plant.read_adc()
        err = setpoint - adc
        if abs(err) <= tol:
            return True, i, adc
        dac += step if err > 0 else -step
        dac = max(0, min(DAC_MAX, dac))
    return False, max_iters, plant.read_adc()


def _selftest():
    p = BiasTrimPlant()
    # safe state
    p.set_dac(0); assert p.read_adc() == 0 and p.is_safe()
    # monotonic above the dead zone
    p.set_dac(500); a1 = p.read_adc()
    p.set_dac(1000); a2 = p.read_adc()
    assert 0 < a1 < a2, (a1, a2)
    # below dead zone -> still ~0
    p.set_dac(300); assert p.read_adc() == 0
    # saturation clamps to ADC_MAX
    p.set_dac(DAC_MAX); assert p.read_adc() == ADC_MAX
    # thermal drift raises the reading at fixed drive, but safe state holds
    p.set_dac(800); base = p.read_adc()
    p.set_temperature(55.0); assert p.read_adc() > base
    p.set_dac(0); assert p.read_adc() == 0 and p.is_safe()

    # a proportional trim loop converges on a mid-scale setpoint
    p.reset()
    ok, iters, final = _simulate_trim_loop(p, setpoint=1200)
    assert ok, (ok, iters, final)
    assert abs(final - 1200) <= 8

    print("bias_trim_plant.py selftest: OK (safe-at-zero, monotonic, "
          "saturating, drift; trim loop converged in %d iters)" % iters)


if __name__ == "__main__":
    _selftest()

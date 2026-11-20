#!/usr/bin/env python3
"""PowerModel — G7250 Main power/reset state machine (clean-room, host-testable).

Models the power-on / power-off / reset behaviour of the Main unit as described
in the RE docs (spec §3.8), so the emulator can drive PH5/PH9 and the DC rail
and observe how the firmware sequences power. This is the model behind risk R0
(the critical-path power question) and milestone M8c; it is also the reference
for the NF-Main power requirements P-1..P-11 (§3.8.4).

Facts modelled (main_unit/docs/flow.md, gpio_map.csv):
  * Power-on: the firmware sets **PH9 high** as its first step, waits ~1 s, then
    programs the AXP223 rails (safe state first, then all). VERIFIED.
  * **PH5** is an input with an internal pull-up — the power-button sense. HIGH.
  * The power-button logic (TIM6, 100 Hz) arms only after PH5 has been seen high
    once; PH5 held low > 1 s is a power-off request. VERIFIED.
  * Shutdown: safe state, save cal/ATU if dirty, AXP to safe, IRQs off, then
    **wait until PH5 is high again**, then a system reset. VERIFIED.
  * PH9 is never explicitly driven low; a power-hold line that the reset releases
    is a HYPOTHESIS (role). Two hypotheses H1/H2 (§3.8.2) are HYPOTHESIS.

The "stock pitfall" (§3.8.2): with no panel, PH5's pull-up first reads high and
arms the logic; if something then pulls PH5 low, stock sees a power-off request
after ~1 s, goes safe, and waits for PH5 high forever. The NF-Main fix is P-1:
ignore PH5 by default (`ignore_ph5=True`). This model reproduces both.

Timing is virtual: call `advance(dt_seconds)`. No wall clock.
Run `python3 power_model.py` to self-test.
"""
from __future__ import annotations

PH9_HOLD_FOR_RAILS = 1.0     # s: PH9 high this long -> program/enable rails
PH5_OFF_HOLD = 1.0           # s: PH5 low this long -> power-off request


class PowerModel:
    # states
    OFF = "off"               # unpowered (H1 at DC-on; after H1 reset)
    STANDBY = "standby"       # MCU/standby rail alive, main rails off (H2 at DC-on)
    ON = "on"                 # all rails on, application powered
    SHUTDOWN = "shutdown"     # firmware running the shutdown sequence
    WAIT_PH5_HIGH = "wait_ph5_high"   # shutdown done, waiting for PH5 high before reset

    def __init__(self, hypothesis="H2", ignore_ph5=False):
        assert hypothesis in ("H1", "H2")
        self.hypothesis = hypothesis
        self.ignore_ph5 = ignore_ph5      # NF-Main P-1: ignore the power-button off-path
        self.reset()

    def reset(self):
        self.dc = False
        self.state = self.OFF
        self.ph9 = False                  # firmware-driven power-hold
        self._ph5_pulled_low = False      # external: button pressed or line pulled low
        self.armed = False                # power-button logic armed (saw PH5 high once)
        self._ph9_high_t = 0.0            # time PH9 has been continuously high
        self._ph5_low_t = 0.0             # time PH5 has been continuously low
        self.off_request = False          # a power-off request was latched
        self.events = []                  # trace for the harness/observe

    # -- environment & firmware drives -------------------------------------
    def set_dc(self, on):
        on = bool(on)
        if on == self.dc:
            return
        self.dc = on
        if on:
            # DC applied: H2 keeps a standby rail alive; H1 stays fully off until
            # a hardware latch (modelled as the first PH9 hold) brings it up.
            self.state = self.STANDBY if self.hypothesis == "H2" else self.OFF
            self._log("dc_on -> %s" % self.state)
        else:
            self.state = self.OFF
            self.ph9 = False
            self._ph9_high_t = 0.0
            self._log("dc_off -> off")

    def drive_ph9(self, level):
        """Firmware drives PH9 (power-hold). Rising edge starts the ~1 s timer."""
        level = bool(level)
        if level and not self.ph9:
            self._ph9_high_t = 0.0
        self.ph9 = level
        if not level:
            # PH9 released: in both hypotheses this drops the main rails / power.
            if self.state in (self.ON, self.SHUTDOWN, self.WAIT_PH5_HIGH):
                self._log("ph9 low -> power drop")
            self.state = self.OFF if self.hypothesis == "H1" else self.STANDBY
            self._ph9_high_t = 0.0

    def set_ph5_low(self, low):
        """External: True = PH5 pulled low (button pressed, or line pulled low
        with no panel). False = released (pull-up takes it high)."""
        low = bool(low)
        if not low:
            self._ph5_low_t = 0.0
        self._ph5_pulled_low = low

    # convenience
    def press_button(self):
        self.set_ph5_low(True)

    def release_button(self):
        self.set_ph5_low(False)

    # -- what the firmware reads -------------------------------------------
    def ph5_level(self):
        """1 = high (pull-up, released), 0 = low (pressed / pulled low)."""
        return 0 if self._ph5_pulled_low else 1

    # -- time --------------------------------------------------------------
    def advance(self, dt):
        if dt <= 0:
            return
        # arm once PH5 seen high (only meaningful while powered)
        if self.state in (self.STANDBY, self.ON) and self.ph5_level() == 1:
            if not self.armed:
                self.armed = True
                self._log("power-button armed (PH5 high seen)")

        # PH9 hold -> rails on
        if self.ph9 and self.state in (self.STANDBY, self.OFF):
            self._ph9_high_t += dt
            if self._ph9_high_t >= PH9_HOLD_FOR_RAILS:
                self.state = self.ON
                self._log("ph9 held %.2fs -> rails on (ON)" % self._ph9_high_t)
        elif self.ph9 and self.state == self.ON:
            self._ph9_high_t += dt

        # PH5 low -> power-off request (unless ignored, and only once armed)
        if self.ph5_level() == 0:
            self._ph5_low_t += dt
            if (self._ph5_low_t >= PH5_OFF_HOLD and self.armed
                    and not self.ignore_ph5 and self.state == self.ON
                    and not self.off_request):
                self.off_request = True
                self.state = self.SHUTDOWN
                self._log("PH5 low %.2fs -> power-off request (SHUTDOWN)" % self._ph5_low_t)
        else:
            self._ph5_low_t = 0.0

    # -- firmware shutdown sequence ----------------------------------------
    def shutdown_complete(self):
        """Firmware finished the safe-state/save steps; now it waits for PH5
        high before the final system reset (flow.md shutdown 1-11)."""
        if self.state == self.SHUTDOWN:
            self.state = self.WAIT_PH5_HIGH
            self._log("shutdown steps done -> wait for PH5 high")

    def tick_reset_if_ready(self):
        """When waiting and PH5 is high, perform the final system reset: H1 drops
        power (PH9 released -> off), H2 returns to standby (ready to power on)."""
        if self.state == self.WAIT_PH5_HIGH and self.ph5_level() == 1:
            self.ph9 = False
            self._ph9_high_t = 0.0
            self.off_request = False
            self.armed = False
            self.state = self.OFF if self.hypothesis == "H1" else self.STANDBY
            self._log("system reset -> %s" % self.state)
            return True
        return False

    # -- queries -----------------------------------------------------------
    def powered(self):
        """True when the main rails are on (application can run)."""
        return self.state == self.ON

    def _log(self, msg):
        self.events.append(msg)


# --------------------------------------------------------------------------
def _selftest():
    # --- H2 normal power-on: DC -> standby, firmware holds PH9 -> ON --------
    p = PowerModel(hypothesis="H2")
    p.set_dc(True)
    assert p.state == PowerModel.STANDBY
    p.advance(0.1)                 # PH5 high -> arm
    assert p.armed
    p.drive_ph9(True)
    p.advance(0.5); assert p.state == PowerModel.STANDBY   # not yet 1 s
    p.advance(0.6); assert p.powered(), p.state            # >= 1 s -> ON

    # --- stock power-off: long PH5 low while ON ---------------------------
    p.press_button()
    p.advance(0.5); assert p.state == PowerModel.ON        # <1 s, no request
    p.advance(0.6); assert p.state == PowerModel.SHUTDOWN  # >=1 s -> request
    assert p.off_request
    p.shutdown_complete()
    assert p.state == PowerModel.WAIT_PH5_HIGH
    assert not p.tick_reset_if_ready()                     # PH5 still low
    p.release_button()
    assert p.tick_reset_if_ready()                         # PH5 high -> reset
    assert p.state == PowerModel.STANDBY                   # H2 returns to standby

    # --- NF-Main P-1: ignore_ph5 suppresses the off-request (the pitfall) --
    q = PowerModel(hypothesis="H2", ignore_ph5=True)
    q.set_dc(True); q.advance(0.1); q.drive_ph9(True); q.advance(1.1)
    assert q.powered()
    q.press_button(); q.advance(5.0)                       # long low, no panel
    assert q.powered() and not q.off_request               # stays ON (P-1)

    # --- H1: DC-on alone does nothing; PH9 hold powers; reset drops power --
    h = PowerModel(hypothesis="H1")
    h.set_dc(True); assert h.state == PowerModel.OFF
    h.drive_ph9(True); h.advance(1.1); assert h.powered()
    h.drive_ph9(False); assert h.state == PowerModel.OFF   # PH9 release -> off

    print("power_model.py selftest: OK (H1/H2, PH9 hold, PH5 off-request, P-1)")


if __name__ == "__main__":
    _selftest()

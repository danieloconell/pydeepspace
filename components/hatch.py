import math

import wpilib

from pyswervedrive.chassis import SwerveChassis


class Hatch:

    chassis: SwerveChassis

    hatch_bottom_puncher: wpilib.Solenoid
    hatch_left_puncher: wpilib.Solenoid
    hatch_right_puncher: wpilib.Solenoid
    release_piston: wpilib.DoubleSolenoid

    left_limit_switch: wpilib.DigitalInput
    right_limit_switch: wpilib.DigitalInput

    def setup(self):
        self.has_hatch = False

    def on_enable(self):
        self._punch_on = False
        self._release = False
        self.clear_to_retract = False
        self.fired_position = 0, 0
        self.loop_counter = 0
        self.fire_align_piston()

    def execute(self):
        """Run at the end of every control loop iteration."""
        delay = -1
        self.hatch_bottom_puncher.set(self._punch_on)
        self.hatch_left_puncher.set(self._punch_on and self.loop_counter > delay)
        self.hatch_right_puncher.set(self._punch_on and self.loop_counter > delay)
        if self._punch_on and self.loop_counter > delay:
            self.has_hatch = False
        self.loop_counter += 1
        if self.is_contained() and self.clear_to_retract:
            self.has_hatch = True
        if self.clear_to_retract:
            self._retract()
        if (
            math.hypot(
                self.fired_position[0] - self.chassis.position[0],
                self.fired_position[1] - self.chassis.position[1],
            )
            > 0.5
        ):
            self.clear_to_retract = True

    def punch(self):
        self.loop_counter = 0
        self._punch_on = True
        self.clear_to_retract = False
        self.fired_position = self.chassis.position

    def release(self):
        self._release = True

    def _retract(self):
        self._punch_on = False
        self.clear_to_retract = False

    def is_contained(self):
        return any(
            [not self.left_limit_switch.get(), not self.right_limit_switch.get()]
        )

    def on_disable(self):
        self.retract_align_piston()

    def fire_align_piston(self):
        self.release_piston.set(self.release_piston.Value.kForward)

    def retract_align_piston(self):
        self.release_piston.set(self.release_piston.Value.kReverse)

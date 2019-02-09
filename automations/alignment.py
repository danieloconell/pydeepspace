import math

from magicbot import tunable
from magicbot.state_machine import StateMachine, state

from components.hatch import Hatch
from components.cargo import Intake
from components.vision import Vision
from pyswervedrive.chassis import SwerveChassis


class Aligner(StateMachine):
    """
    A state machine for alignment using vision systems.

    The robot will use two methods of alignment, targets above
    objectives from longer range and fine adjustment using the ground
    tape once we are able to see it.
    """

    VERBOSE_LOGGING = True

    chassis: SwerveChassis
    vision: Vision

    def setup(self):
        self.successful = False
        self.last_vision = 0

    alignment_speed = tunable(1.0)  # m/s
    target_tape_kP_x = tunable(0.75)  # forwards
    target_tape_kP_y = tunable(1.2)  # m/s

    @state(first=True)
    def wait_for_vision(self):
        if self.vision.fiducial_in_sight:
            self.next_state("target_tape_align")

    @state(must_finish=True)
    def target_tape_align(self, initial_call, state_tm):
        """
        Align with the objective using the vision tape above the objective.

        The robot will try to correct errors untill they are within tolerance
        by strafing and moving in a hyberbolic curve towards the target.
        """
        if initial_call:
            self.successful = False
            self.last_vision = state_tm
        if not self.vision.fiducial_in_sight:
            self.chassis.set_inputs(self.alignment_speed, 0, 0, field_oriented=False)
            if state_tm - self.last_vision > 0.5:
                self.chassis.set_inputs(0, 0, 0)
                self.next_state("success")
        else:
            self.last_vision = state_tm
            fiducial_x, fiducial_y, delta_heading = self.vision.get_fiducial_position()
            # Aim for a point in front of the fiducial
            fiducial_x = fiducial_x / 3
            norm = math.hypot(fiducial_x, fiducial_y)
            vx = self.alignment_speed * fiducial_x / norm
            vy = self.alignment_speed * fiducial_y / norm
            self.chassis.set_inputs(vx, vy, 0, field_oriented=False)

    @state(must_finish=True)
    def success(self):
        self.done()


class HatchDepositAligner(Aligner):

    VERBOSE_LOGGING = True
    hatch: Hatch

    @state(must_finish=True)
    def success(self, state_tm, initial_call):
        if initial_call:
            self.hatch.punch()
        if state_tm > 1:
            self.done()


class CargoDepositAligner(Aligner):

    VERBOSE_LOGGING = True
    intake: Intake

    @state(must_finish=True)
    def success(self):
        self.intake.deposit()
        self.done()


class HatchIntakeAligner(Aligner):

    VERBOSE_LOGGING = True
    hatch: Hatch
    # TODO delete this once limit switches are working

    @state(must_finish=True)
    def success(self):
        self.hatch.has_hatch = True
        self.done()

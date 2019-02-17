#!/usr/bin/env python3
import enum
import math

import ctre
import rev
import magicbot
import wpilib
from networktables import NetworkTables

from automations.cargo import CargoManager
from components.cargo import CargoManipulator, Height
from utilities.functions import constrain_angle, rescale_js

ROCKET_ANGLE = 0.52  # measured field angle


class FieldAngle(enum.Enum):
    CARGO_FRONT = 0
    CARGO_RIGHT = math.pi / 2
    CARGO_LEFT = -math.pi / 2
    LOADING_STATION = math.pi
    ROCKET_LEFT_FRONT = ROCKET_ANGLE
    ROCKET_RIGHT_FRONT = -ROCKET_ANGLE
    ROCKET_LEFT_BACK = math.pi - ROCKET_ANGLE
    ROCKET_RIGHT_BACK = -math.pi + ROCKET_ANGLE

    @classmethod
    def closest(cls, robot_heading: float) -> "FieldAngle":
        return min(cls, key=lambda a: abs(constrain_angle(robot_heading - a.value)))


class Robot(magicbot.MagicRobot):
    # Declare magicbot components here using variable annotations.
    # NOTE: ORDER IS IMPORTANT.
    # Any components that actuate objects should be declared after
    # any higher-level components (automations) that depend on them.

    # Automations
    cargo: CargoManager

    # Actuators
    cargo_component: CargoManipulator

    offset_rotation_rate = 20

    field_angles = {
        "cargo front": 0,
        "cargo right": math.pi / 2,
        "cargo left": -math.pi / 2,
        "loading station": math.pi,
        "rocket left front": 0.52,  # measured field angle
        "rocket right front": -0.52,
        "rocket left back": math.pi - 0.52,
        "rocket right back": -math.pi + 0.52,
    }

    def createObjects(self):
        """Create motors and stuff here."""

        # cargo related objects
        self.intake_motor = ctre.VictorSPX(9)
        self.intake_switch = wpilib.DigitalInput(0)
        self.arm_motor = rev.CANSparkMax(2, rev.MotorType.kBrushless)
        self.intake_servo = wpilib.Servo(9)

        self.sd = NetworkTables.getTable("SmartDashboard")
        
        # boilerplate setup for the joystick
        self.joystick = wpilib.Joystick(0)
        self.gamepad = wpilib.XboxController(1)

        self.spin_rate = 2.5

    def teleopPeriodic(self):
        """Allow the drivers to control the robot."""
        # self.chassis.heading_hold_off()

        throttle = (1 - self.joystick.getThrottle()) / 2
        self.sd.putNumber("joy_throttle", throttle)

        # this is where the joystick inputs get converted to numbers that are sent
        # to the chassis component. we rescale them using the rescale_js function,
        # in order to make their response exponential, and to set a dead zone -
        # which just means if it is under a certain value a 0 will be sent
        # TODO: Tune these constants for whatever robot they are on
        joystick_vx = -rescale_js(
            self.joystick.getY(), deadzone=0.1, exponential=1.5, rate=4 * throttle
        )
        joystick_vy = -rescale_js(
            self.joystick.getX(), deadzone=0.1, exponential=1.5, rate=4 * throttle
        )
        joystick_vz = -rescale_js(
            self.joystick.getZ(), deadzone=0.2, exponential=20.0, rate=self.spin_rate
        )
        joystick_hat = self.joystick.getPOV()

        self.sd.putNumber("joy_vx", joystick_vx)
        self.sd.putNumber("joy_vy", joystick_vy)
        self.sd.putNumber("joy_vz", joystick_vz)

        if self.gamepad.getTriggerAxis(self.gamepad.Hand.kLeft) > 0.1:
            self.cargo.outake_cargo_ship(force=True)

        if self.gamepad.getTriggerAxis(self.gamepad.Hand.kRight) > 0.1:
            self.cargo.outake_rocket(force=True)

        if self.joystick.getRawButton(3):
            self.cargo_component.setpoint = 30
            # self.cargo_component.arm_motor.set(0.4)
            # self.cargo_component.arm_motor.set(0.2)
            # self.cargo.intake_floor(force=True)
        if self.joystick.getRawButton(4):
            self.cargo_component.setpoint = 0
            # self.cargo_component.arm_motor.set(-0.4)
        #     # self.cargo_component.arm_motor.set(-0.2)
        # else:
        #     self.cargo_component.arm_motor.set(0)
            # self.cargo.intake_loading(force=True)

        if self.joystick.getRawButtonPressed(1):
            # self.cargo_component.pid_controller.setReference(
            #     self.cargo_component.counts_per_rad(math.radians(105))
            # )
            # self.cargo_component.pid_controller.setReference(
            #     self.cargo_component.counts_per_rad(math.radians(105))
            # )
            # self.cargo.intake_floor(force=True)
            self.cargo_component.ratchet()
        if self.joystick.getRawButtonPressed(2):
            self.cargo_component.unratchet()
            # self.cargo_component.pid_controller.setReference(
            #     self.cargo_component.counts_per_rad(math.radians(105))
            # )
            # self.cargo_component.pid_controller.setReference(
            #     self.cargo_component.counts_per_rad(math.radians(0))
            # )
            # self.cargo.intake_loading(force=True)

        # if self.gamepad.getAButtonPressed():
        #     self.cargo.engage(initial_state="intaking_cargo", force=True)
        # if self.gamepad.getBButtonPressed():
        #     self.cargo.outtake(force=True)

        # if self.gamepad.getXButtonPressed():
        #     self.cargo.engage(initial_state="intaking_cargo", force=True)
        # if self.gamepad.getYButtonPressed():
        #     self.cargo.outtake(force=True)
        # if self.gamepad.getYButtonPressed():
        #     self.cargo_component.cargo_component_down()

        if self.gamepad.getStartButtonPressed():
            self.cargo_component.ratchet()
        if self.gamepad.getBackButtonPressed():
            self.cargo_component.unratchet()

        if self.gamepad.getXButton():
            self.cargo_component.arm_motor.set(-0.5)
        if self.gamepad.getYButton():
            self.cargo_component.arm_motor.set(0.5)

    def robotPeriodic(self):
        super().robotPeriodic()
        self.sd.putNumber("cargo_encoder", self.cargo_component.encoder.getPosition())

    #     for module in self.chassis.modules:
    #         self.sd.putNumber(
    #             module.name + "_pos_steer",
    #             module.steer_motor.getSelectedSensorPosition(0),
    #         )
    #         self.sd.putNumber(
    #             module.name + "_pos_drive",
    #             module.drive_motor.getSelectedSensorPosition(0),
    #         )
    #         self.sd.putNumber(
    #             module.name + "_drive_motor_reading",
    #             module.drive_motor.getSelectedSensorVelocity(0)
    #             * 10  # convert to seconds
    #             / module.drive_counts_per_metre,
    #         )
    #     self.sd.putBoolean("heading_hold", self.chassis.hold_heading)


    def closest_field_angle(self, robot_heading):
        lowest_distance = 2 * math.pi
        lowest_label = None
        for label, angle in self.field_angles.items():
            diff = constrain_angle(constrain_angle(robot_heading) - angle)
            if abs(diff) < lowest_distance:
                lowest_distance = abs(diff)
                lowest_label = label
        return lowest_label


if __name__ == "__main__":
    wpilib.run(Robot)

import enum
import math

import ctre
import wpilib


class Intake:

    motor: ctre.TalonSRX
    intake_switch: wpilib.DigitalInput

    def __init__(self):
        self.motor_output = 0
        self.has_cargo = False

    def execute(self):
        self.motor.set(ctre.ControlMode.PercentOutput, self.motor_output)
        if not self.intake_switch.get():
            self.has_cargo = True

    def intake(self):
        self.motor_output = -1

    def outtake(self):
        self.motor_output = 1
        self.has_cargo = False

    def stop(self):
        self.motor_output = 0


class Height(enum.Enum):
    FLOOR = 0
    ROCKET_SHIP = 0.630
    CARGO_SHIP = 0.880
    LOADING_STATION = 0.940


class Arm:

    motor: ctre.TalonSRX
    servo: wpilib.Servo
    bottom_switch: wpilib.DigitalInput
    top_switch: wpilib.DigitalInput

    ARM_LENGTH = 42
    FREE_SPEED = 42
    COUNTS_PER_REV = 1024
    COUNTS_PER_RADIAN = math.tau / COUNTS_PER_REV

    def setup(self):
        self.motor.setNeutralMode(ctre.NeutralMode.Brake)
        # Current limiting
        self.motor.configContinuousCurrentLimit(
            20, 10
        )  # TODO: change current limiting values to be more appropriate value
        self.motor.configPeakCurrentLimit(20, 10)
        self.motor.configPeakCurrentDuration(2, 10)
        # Limit swtiches
        self.motor.overrideLimitSwitchesEnable(False)
        self.motor.configForwardLimitSwitchSource(
            ctre.LimitSwitchSource.FeedbackConnector,
            ctre.LimitSwitchNormal.NormallyOpen,
            timeoutMs=10,
        )
        # self.motor.configForwardSoftLimitThreshold(
        #     self.counts_per_meter(Height.LOADING_STATION.value), timeoutMs=10
        # )
        # self.motor.configForwardSoftLimitEnable(True, timeoutMs=10)
        self.motor.configForwardSoftLimitEnable(True, 10)
        self.motor.configReverseLimitSwitchSource(
            ctre.LimitSwitchSource.FeedbackConnector,
            ctre.LimitSwitchNormal.NormallyOpen,
            timeoutMs=10,
        )
        # self.motor.configReverseSoftLimitThreshold(
        #     self.counts_per_meter(Height.FLOOR.value), timeoutMs=10
        # )
        # self.motor.configReverseSoftLimitEnable(True, timeoutMs=10)
        self.motor.configReverseSoftLimitEnable(True, 10)
        # Current height
        self.current_height = Height.LOADING_STATION

    def counts_per_meter(self, meters: int):
        angle = math.asin(meters / self.ARM_LENGTH)
        return int(angle * self.COUNTS_PER_RADIAN)

    def execute(self):
        pass

    def move_to(self, height: Height):
        if height == Height.FLOOR and self.current_height != height:
            self.motor.set(ctre.ControlMode.PercentOutput, -1)
            self.current_height = height
        elif height == Height.LOADING_STATION and self.current_height != height:
            self.motor.set(ctre.ControlMode.PercentOutput, 1)
            self.current_height = height
        # self.motor.set(ctre.ControlMode.Position, self.counts_per_meter(height.value))

    # def lift(self):
    #     if self.current_height != Height.LOADING_STATION:
    #         if self.current_height == Height.CARGO_SHIP:
    #             self.move_to(Height.LOADING_STATION)
    #         elif self.current_height == Height.ROCKET_SHIP:
    #             self.move_to(Height.CARGO_SHIP)
    #         elif self.current_height == Height.FLOOR:
    #             self.move_to(Height.CARGO_SHIP)

    # def lower(self):
    #     if self.current_height != Height.FLOOR:
    #         if self.current_height == Height.LOADING_STATION:
    #             self.move_to(Height.CARGO_SHIP)
    #         elif self.current_height == Height.CARGO_SHIP:
    #             self.move_to(Height.ROCKET_SHIP)
    #         elif self.current_height == Height.ROCKET_SHIP:
    #             self.move_to(Height.FLOOR)

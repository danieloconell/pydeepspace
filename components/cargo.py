import enum

import ctre
import math
import rev
import wpilib


class CargoIntake:

    motor: ctre.VictorSPX
    intake_switch: wpilib.DigitalInput

    INTAKE_SPEED = 1
    OUTTAKE_SPEED = 0.75

    def __init__(self) -> None:
        self.motor_output = 0

    def setup(self):
        wpilib.SmartDashboard.putData(self.intake_switch)

    def execute(self) -> None:
        wpilib.SmartDashboard.putBoolean("intake_switch", self.intake_switch.get())
        self.motor.set(ctre.ControlMode.PercentOutput, self.motor_output)

    def intake(self) -> None:
        self.motor_output = self.INTAKE_SPEED

    def outtake(self) -> None:
        self.motor_output = self.OUTTAKE_SPEED

    def stop(self) -> None:
        self.motor_output = 0

    def is_contained(self) -> bool:
        return self.intake_switch.get()


class Height(enum.Enum):
    FLOOR = 0
    ROCKET_SHIP = 0.630
    CARGO_SHIP = 0.880
    LOADING_STATION = 0.940


class Arm:

    motor: rev.CANSparkMax
    servo: wpilib.Servo

    RATCHET_ANGLE = 0
    UNRATCHET_ANGLE = 180

    ARM_LENGTH = 0
    FREE_SPEED = 5600
    COUNTS_PER_REV = 42
    COUNTS_PER_RADIAN = math.tau / COUNTS_PER_REV

    def setup(self) -> None:
        self.motor.setIdleMode(rev.IdleMode.kBrake)
        self.motor.setSecondaryCurrentLimit(60, limitCycles=200)  # check limitCycles
        self.motor.setInverted(False)

        self.encoder = self.motor.getEncoder()
        self.pid_controller = self.motor.getPIDController()
        self.pid_controller.setP(2)
        self.pid_controller.setI(0)
        self.pid_controller.setD(0)

        self.top_limit_switch = self.motor.getForwardLimitSwitch(rev.LimitSwitchPolarity.kNormallyOpen)
        self.top_limit_switch.enableLimitSwitch(True)
        self.bottom_limit_switch = self.motor.getForwardLimitSwitch(rev.LimitSwitchPolarity.kNormallyOpen)
        self.top_limit_switch.enableLimitSwitch(True)

        # Arm starts at max height to remain within frame perimeter
        self.current_height = Height.FLOOR

    def execute(self) -> None:
        wpilib.SmartDashboard.putBoolean("top_switch", self.top_limit_switch.get())
        wpilib.SmartDashboard.putBoolean("bottom_switch", self.bottom_limit_switch.get())

    def at_height(self) -> bool:
        return self.current_height(self.current_height.value) < self.encoder.getPosition()

    def ratchet(self) -> None:
        self.servo.setAngle(self.RATCHET_ANGLE)

    def unratchet(self) -> None:
        self.servo.setAngle(self.UNRATCHET_ANGLE)

    def counts_per_meter(self, meters: int):
        angle = math.asin(meters / self.ARM_LENGTH)
        return int(angle * self.COUNTS_PER_RADIAN)

    def move_to(self, height: Height) -> None:
        """Move arm to specified height.

        Args:
            height (Height): Height to move arm to
        """
        self.pid_controller.setReference(self.counts_per_meter(height.value), rev.ControlType.kPosition)

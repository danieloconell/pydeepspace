import enum

import ctre
import wpilib


class CargoIntake:

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
    LOADING_STATION = 0.940


class Ratchet(enum.Enum):
    STOPPED = 0
    RATCHETING = 1
    UNRATCHETING = 2


class Arm:

    motor: ctre.TalonSRX
    servo: wpilib.Servo
    bottom_switch: wpilib.DigitalInput
    top_switch: wpilib.DigitalInput

    def setup(self) -> None:
        self.motor.setNeutralMode(ctre.NeutralMode.Brake)
        # Current limiting
        self.motor.configContinuousCurrentLimit(
            20, 10
        )  # TODO: change current limiting values to be more appropriate value
        self.motor.configPeakCurrentLimit(20, 10)
        self.motor.configPeakCurrentDuration(2, 10)
        # Limit switches
        self.motor.overrideLimitSwitchesEnable(False)
        self.motor.configForwardLimitSwitchSource(
            ctre.LimitSwitchSource.FeedbackConnector,
            ctre.LimitSwitchNormal.NormallyOpen,
            timeoutMs=10,
        )
        self.motor.configReverseLimitSwitchSource(
            ctre.LimitSwitchSource.FeedbackConnector,
            ctre.LimitSwitchNormal.NormallyOpen,
            timeoutMs=10,
        )

        # Arm starts at max height to remain within frame perimeter
        self.current_height = Height.LOADING_STATION
        self.servo_state = Ratchet.STOPPED

    def execute(self) -> None:
        if self.at_height():
            self.motor.set(ctre.ControlMode.PercentOutput, 0)

    def at_height(self) -> bool:
        if self.current_height == Height.LOADING_STATION and hasattr(
            self.motor.getFaults(), "forwardLimitSwitch"
        ):
            return True
        elif self.current_height == Height.FLOOR and hasattr(
            self.motor.getFaults(), "reverseLimitSwitch"
        ):
            return True
        else:
            return False
        # if self.current_height == Height.LOADING_STATION:
        #     return self.motor.isFwdLimitSwitchClosed()
        # else:
        #     return self.motor.isRevLimitSwitchClosed()

    def ratchet(self) -> None:
        # this is hoping that this is half speed to the left
        if self.servo_state != Ratchet.RATCHETING:
            self.servo.set(0.25)
            self.servo_state = Ratchet.RATCHETING

    def unratchet(self) -> None:
        # this is hoping that this is half speed to the right
        if self.servo_state != Ratchet.UNRATCHETING:
            self.servo.set(0.75)
            self.servo_state = Ratchet.UNRATCHETING

    def stop_ratchet(self) -> None:
        self.servo.set(0)
        self.servo_state = Ratchet.STOPPED

    def move_to(self, height: Height) -> None:
        """Move arm to specified height.

        Only support two heights (Floor, Loading Station), due to
        only having limit switches and hard stops to find the position
        of the arm.

        Args:
            height (Height): Height to move arm to
        """
        if height == Height.FLOOR and self.current_height != height:
            self.motor.set(ctre.ControlMode.PercentOutput, -1)
            self.current_height = height
        elif height == Height.LOADING_STATION and self.current_height != height:
            self.motor.set(ctre.ControlMode.PercentOutput, 1)
            self.current_height = height

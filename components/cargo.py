import enum

import ctre
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
    LOADING_STATION = 0.940


class Arm:

    motor: ctre.TalonSRX
    servo: wpilib.Servo

    MOTOR_SPEED = 0.2
    RATCHET_ANGLE = 0
    UNRATCHET_ANGLE = 180

    def __init__(self) -> None:
        self.output = 0

    def setup(self) -> None:
        self.motor.setNeutralMode(ctre.NeutralMode.Brake)
        # Current limiting
        self.motor.configContinuousCurrentLimit(
            40, timeoutMs=10
        )  # TODO: change current limiting values to be more appropriate value
        self.motor.configPeakCurrentLimit(50, timeoutMs=10)
        self.motor.configPeakCurrentDuration(500, timeoutMs=10)
        self.motor.enableCurrentLimit(True)
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
        self.motor.setInverted(True)

        # Arm starts at max height to remain within frame perimeter
        self.current_height = Height.FLOOR

    def execute(self) -> None:
        self.motor.set(ctre.ControlMode.PercentOutput, self.output)
        wpilib.SmartDashboard.putBoolean("top_switch", self.motor.isFwdLimitSwitchClosed())
        wpilib.SmartDashboard.putBoolean("bottom_switch", self.motor.isRevLimitSwitchClosed())

        self.output = 0

    def at_height(self) -> bool:
        if self.current_height == Height.LOADING_STATION and self.motor.getFaults().forwardLimitSwitch:
            return True
        elif self.current_height == Height.FLOOR and self.motor.getFaults().reverseLimitSwitch:
            return True
        else:
            return False

        # if self.current_height == Height.LOADING_STATION:
        #     return self.motor.isFwdLimitSwitchClosed()
        # if self.current_height == Height.FLOOR:
        #     return self.motor.isRevLimitSwitchClosed()

    def ratchet(self) -> None:
        # this is hoping that this is half speed to the left
        self.servo.setAngle(self.RATCHET_ANGLE)

    def unratchet(self) -> None:
        # this is hoping that this is half speed to the right
        self.servo.setAngle(self.UNRATCHET_ANGLE)

    def move_to(self, height: Height) -> None:
        """Move arm to specified height.

        Only support two heights (Floor, Loading Station), due to
        only having limit switches and hard stops to find the position
        of the arm.

        Args:
            height (Height): Height to move arm to
        """
        if height == Height.FLOOR and self.current_height != height:
            self.motor.set(ctre.ControlMode.PercentOutput, -self.MOTOR_SPEED)
            self.current_height = height
        elif height == Height.LOADING_STATION and self.current_height != height:
            self.motor.set(ctre.ControlMode.PercentOutput, self.MOTOR_SPEED)
            self.current_height = height

    def arm_up(self) -> None:
        self.output = 0.8

    def arm_down(self) -> None:
        self.output = -self.MOTOR_SPEED

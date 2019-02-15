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
    FLOOR = math.radians(105)
    ROCKET_SHIP = math.radians(46)
    # 0.630 TODO placeholde, fix
    CARGO_SHIP = math.pi/4
    # 0.880 TODO placeholder fix
    LOADING_STATION = 0
    # 0.940


class Arm:

    motor: rev.CANSparkMax
    servo: wpilib.Servo

    RATCHET_ANGLE = 0
    UNRATCHET_ANGLE = 180

    FREE_SPEED = 5600
    GEAR_RATIO = 49*84/50
    COUNTS_PER_REV = 1
    COUNTS_PER_RADIAN = math.tau / COUNTS_PER_REV

    def setup(self) -> None:
        self.motor.setIdleMode(rev.IdleMode.kBrake)
        self.motor.setSecondaryCurrentLimit(60, limitCycles=200)  # check limitCycles
        self.motor.setInverted(False)

        self.encoder = self.motor.getEncoder()
        self.pid_controller = self.motor.getPIDController()
        self.pid_controller.setP(0.05)
        self.pid_controller.setI(0)
        self.pid_controller.setD(0)

        self.top_limit_switch = self.motor.getReverseLimitSwitch(rev.LimitSwitchPolarity.kNormallyOpen)
        self.bottom_limit_switch = self.motor.getForwardLimitSwitch(rev.LimitSwitchPolarity.kNormallyOpen)

        # Arm starts at max height to remain within frame perimeter
        self.current_height = Height.FLOOR

        self.setpoint = None

    def execute(self) -> None:
        wpilib.SmartDashboard.putBoolean("top_switch", self.top_limit_switch.get())
        wpilib.SmartDashboard.putBoolean("bottom_switch", self.bottom_limit_switch.get())

    def at_height(self) -> bool:
        return self.current_height(self.current_height.value) < self.encoder.getPosition()

    def ratchet(self) -> None:
        self.servo.setAngle(self.RATCHET_ANGLE)

    def unratchet(self) -> None:
        self.servo.setAngle(self.UNRATCHET_ANGLE)

    @classmethod
    def counts_per_rad(cls, angle) -> float:
        return angle * cls.COUNTS_PER_RADIAN * cls.GEAR_RATIO

    def move_to(self, height: Height) -> None:
        """Move arm to specified height.

        Args:
            height: Height to move arm to
        """
        self.pid_controller.setReference(self.counts_per_rad(height.value), rev.ControlType.kPosition)
    
    def set_motor(self, speed: float) -> None:
        self.motor.set(speed)

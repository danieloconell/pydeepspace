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

    def on_disable(self):
        self.motor.set(ctre.ControlMode.PercentOutput, 0)

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
    COUNTS_PER_RADIAN = 20 / math.radians(105)  # measured counts

    def setup(self) -> None:
        self.motor.setIdleMode(rev.IdleMode.kBrake)
        self.motor.setSecondaryCurrentLimit(60, limitCycles=200)  # check limitCycles
        self.motor.setInverted(False)

        self.encoder = self.motor.getEncoder()
        self.pid_controller = self.motor.getPIDController()
        # self.pid_controller.setP(0.1)
        # self.pid_controller.setI(0)
        # self.pid_controller.setD(0)

        self.pid_controller.setP(0.1, 1)
        self.pid_controller.setI(0, 1)
        self.pid_controller.setD(0, 1)
        self.pid_controller.setOutputRange(-1, 1)

        self.top_limit_switch = self.motor.getReverseLimitSwitch(rev.LimitSwitchPolarity.kNormallyOpen)
        self.bottom_limit_switch = self.motor.getForwardLimitSwitch(rev.LimitSwitchPolarity.kNormallyOpen)

        # Arm starts at max height to remain within frame perimeter
        self.setpoint = Height.LOADING_STATION
        self.tolerance = 0

        self.ratchet_engaged = True

    def execute(self) -> None:
        wpilib.SmartDashboard.putBoolean("top_switch", self.top_limit_switch.get())
        wpilib.SmartDashboard.putBoolean("bottom_switch", self.bottom_limit_switch.get())
        wpilib.SmartDashboard.putNumber("cargo_setpoint", self.setpoint.value)
        wpilib.SmartDashboard.putNumber("cargo_setpoint_counts", self.counts_per_rad(self.setpoint.value))
        # if self.setpoint.value > self.counts_per_rad(self.encoder.getPosition()):
            # we are going up
        self.pid_controller.setReference(int(self.counts_per_rad(self.setpoint.value)), rev.ControlType.kPosition, pidSlot=1)
        # else:
        #     self.pid_controller.setReference(self.counts_per_rad(self.setpoint.value), rev.ControlType.kPosition, pidSlot=0)
        if self.ratchet_engaged:
            self.servo.setAngle(self.RATCHET_ANGLE)
        else:
            self.servo.setAngle(self.UNRATCHET_ANGLE)

    def at_height(self) -> bool:
        return False
        return abs(self.counts_per_rad(self.setpoint.value) - self.encoder.getPosition()) <= self.tolerance

    def ratchet(self) -> None:
        self.ratchet_engaged = True

    def unratchet(self) -> None:
        self.ratchet_engaged = False

    @classmethod
    def counts_per_rad(cls, angle) -> float:
        return angle * cls.COUNTS_PER_RADIAN

    def move_to(self, height: Height) -> None:
        """Move arm to specified height.

        Args:
            height: Height to move arm to
        """
        self.setpoint = height

    def set_motor(self, speed: float) -> None:
        self.motor.set(speed)

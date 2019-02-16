import enum

import ctre
import math
import rev
import wpilib
import wpilib_controller


class Height(enum.Enum):
    FLOOR = math.radians(105)
    ROCKET_SHIP = math.radians(46)
    # 0.630 TODO placeholde, fix
    CARGO_SHIP = math.pi/4
    # 0.880 TODO placeholder fix
    LOADING_STATION = 0
    # 0.940

    @classmethod
    def closest(cls, current_height):
        return min(cls, key=lambda a: abs(a.value - current_height))


class CargoManipulator:

    arm_motor: rev.CANSparkMax
    intake_motor: ctre.VictorSPX
    servo: wpilib.Servo

    intake_switch: wpilib.DigitalInput

    RATCHET_ANGLE = 0
    UNRATCHET_ANGLE = 180

    FREE_SPEED = 5600
    GEAR_RATIO = 49*84/50

    COUNTS_PER_REV = 1
    COUNTS_PER_RADIAN = 20 / math.radians(105)  # measured counts

    INTAKE_SPEED = 1
    OUTTAKE_SPEED = 0.75

    def __init__(self):
        self.intake_motor_output = 0

    def setup(self) -> None:
        self.arm_motor.setIdleMode(rev.IdleMode.kBrake)
        self.arm_motor.setSecondaryCurrentLimit(60, limitCycles=200)  # check limitCycles
        self.arm_motor.setInverted(False)

        self.encoder = self.arm_motor.getEncoder()
        self.pid_controller = wpilib_controller.PIDController(Kp=0.1, Ki=0.0, Kd=0.0, measurement_source=self.encoder.getPosition, period=1/50)
        self.pid_controller.setInputRange(Height.LOADING_STATION.value, Height.FLOOR.value)
        self.pid_controller.setOutputRange(-1, 1)

        self.top_limit_switch = self.arm_motor.getReverseLimitSwitch(rev.LimitSwitchPolarity.kNormallyOpen)
        self.bottom_limit_switch = self.arm_motor.getForwardLimitSwitch(rev.LimitSwitchPolarity.kNormallyOpen)

        # Arm starts at max height to remain within frame perimeter
        self.setpoint = Height.LOADING_STATION.value
        self.tolerance = 0

        self.ratchet_engaged = True

        self.has_cargo = False

        wpilib.SmartDashboard.putData(self.intake_switch)

    def execute(self) -> None:
        wpilib.SmartDashboard.putBoolean("top_switch", self.top_limit_switch.get())
        wpilib.SmartDashboard.putBoolean("bottom_switch", self.bottom_limit_switch.get())
        wpilib.SmartDashboard.putNumber("cargo_setpoint", self.setpoint)
        wpilib.SmartDashboard.putNumber("cargo_setpoint_counts", self.counts_per_rad(self.setpoint))
        wpilib.SmartDashboard.putBoolean("intake_switch", self.intake_switch.get())

        self.intake_motor.set(ctre.ControlMode.PercentOutput, self.intake_motor_output)

        # if self.setpoint.value > self.counts_per_rad(self.encoder.getPosition()):
        # we are going up
        self.pid_controller.setReference(self.setpoint)
        output = self.pid_controller.update()
        self.arm_motor.set(output)
        # else:
        #     self.pid_controller.setReference(self.counts_per_rad(self.setpoint.value), rev.ControlType.kPosition, pidSlot=0)
        if self.ratchet_engaged:
            self.servo.setAngle(self.RATCHET_ANGLE)
        else:
            self.servo.setAngle(self.UNRATCHET_ANGLE)

        if self.is_contained():
            self.has_cargo = True

    def at_height(self, desired_height) -> bool:
        return abs(self.counts_per_rad(desired_height.value) - self.encoder.getPosition()) <= self.tolerance

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
        self.setpoint = height.value

    def on_disable(self):
        self.intake_motor.set(ctre.ControlMode.PercentOutput, 0)
        self.arm_motor.set(0)

    def intake(self) -> None:
        self.intake_motor_output = self.INTAKE_SPEED

    def outtake(self) -> None:
        self.has_cargo = False
        self.intake_motor_output = self.OUTTAKE_SPEED

    def stop(self) -> None:
        self.intake_motor_output = 0

    def is_contained(self) -> bool:
        return self.intake_switch.get()

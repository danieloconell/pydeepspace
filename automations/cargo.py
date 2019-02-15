from magicbot import StateMachine, state, tunable

from components.cargo import Arm, CargoIntake, Height


class CargoManager(StateMachine):

    arm: Arm
    intake: CargoIntake

    def __init__(self):
        super().__init__()
        self.override = False

    def intake_floor(self, force=False):
        self.engage(initial_state="move_to_floor", force=force)

    @state(first=True, must_finish=True)
    def move_to_floor(self, initial_call, state_tm):
        if initial_call:
            self.arm.ratchet()
        if self.release_pressure(Height.FLOOR.value):
            self.arm.move_to(Height.FLOOR)
        if self.arm.at_height():
            self.arm.unratchet()
            self.next_state("intaking_cargo")

    def intake_loading(self, force=False):
        self.engage(initial_state="move_to_loading_station", force=force)

    @state(must_finish=True)
    def move_to_loading_station(self, initial_call, state_tm):
        if initial_call:
            self.arm.unratchet()
        if self.release_pressure(Height.LOADING_STATION.value):
            self.arm.move_to(Height.LOADING_STATION)
        if self.arm.at_height():
            self.arm.ratchet()
            self.next_state("intaking_cargo")

    @state(must_finish=True)
    def intaking_cargo(self):
        if self.intake.is_contained():
            self.intake.stop()
            self.done()
        else:
            self.intake.intake()

    def outtake(self, force=False):
        self.engage(initial_state="outtaking_cargo", force=force)

    @state(must_finish=True)
    def outtaking_cargo(self, initial_call):
        if initial_call:
            self.intake.outtake()

        if not self.intake.is_contained():
            self.intake.stop()
            self.done()

    def release_pressure(self, target: float) -> bool:
        if target < self.arm.encoder.getPosition():
                self.arm.motor.set(-0.05)
                return False
        else:
            return True

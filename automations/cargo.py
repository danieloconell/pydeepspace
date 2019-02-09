from magicbot import StateMachine, state

from components.cargo import Arm, CargoIntake, Height


class CargoManager(StateMachine):

    arm: Arm
    intake: CargoIntake

    RATCH_TIME = 0.1

    def __init__(self):
        super().__init__()
        self.override = False

    def intake_floor(self, force=False):
        self.engage(initial_state="move_to_floor", force=force)

    @state(first=True, must_finish=True)
    def move_to_floor(self, initial_call, state_tm):
        if initial_call:
            self.arm.ratchet()
        elif state_tm > self.RATCH_TIME:
            self.arm.stop_ratchet()
            self.arm.move_to(Height.FLOOR)
            if self.arm.at_height():
                self.next_state("intaking_cargo")

    def intake_loading(self, force=False):
        self.engage(initial_state="move_to_loading_station", force=force)

    @state(must_finish=True)
    def move_to_loading_station(self, initial_call, state_tm):
        if initial_call:
            self.arm.unratchet()
        elif state_tm > self.RATCH_TIME:
            self.arm.stop_ratchet()
            self.arm.move_to(Height.LOADING_STATION)
            if self.arm.at_height():
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

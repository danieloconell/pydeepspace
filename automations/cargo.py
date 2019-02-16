from magicbot import StateMachine, state, tunable, timed_state

from components.cargo import CargoManipulator, Height
from components.vision import Vision


class CargoManager(StateMachine):

    cargo_component: CargoManipulator
    vision: Vision

    def __init__(self):
        super().__init__()
        self.override = False

    def intake_floor(self, force=False):
        self.engage(initial_state="move_to_floor", force=force)

    @state(first=True, must_finish=True)
    def move_to_floor(self, initial_call, state_tm):
        if state_tm < 0.2:
            self.release_pressure(Height.FLOOR.value)
        else:
            self.cargo_component.move_to(Height.FLOOR)
        if self.cargo_component.at_height(Height.FLOOR):
            self.next_state("intaking_cargo")

    @state(must_finish=True)
    def move_to_rocket(self, initial_call, state_tm):
        if state_tm < 0.2:
            self.release_pressure(Height.ROCKET_SHIP.value)
        else:
            self.cargo_component.move_to(Height.ROCKET_SHIP)
        if self.cargo_component.at_height(Height.ROCKET_SHIP):
            self.next_state("outaking_cargo")

    @state(must_finish=True)
    def move_to_cargo_ship(self, initial_call, state_tm):
        if state_tm < 0.2:
            self.release_pressure(Height.CARGO_SHIP.value)
        else:
            self.cargo_component.move_to(Height.CARGO_SHIP)
        if self.cargo_component.at_height(Height.CARGO_SHIP):
            self.next_state("outaking_cargo")

    def outake_cargo_ship(self, force=False):
        self.engage(initial_state="move_to_cargo_ship", force=force)

    def outake_rocket(self, force=False):
        self.engage(initial_state="move_to_rocket", force=force)

    def intake_loading(self, force=False):
        self.engage(initial_state="move_to_loading_station", force=force)

    @state(must_finish=True)
    def move_to_loading_station(self, initial_call, state_tm):
        self.cargo_component.move_to(Height.LOADING_STATION)
        if self.cargo_component.at_height(Height.LOADING_STATION):
            self.cargo_component.ratchet()
            self.next_state("intaking_cargo")

    @state(must_finish=True)
    def intaking_cargo(self):
        if self.cargo_component.is_contained():
            self.cargo_component.stop()
            self.done()
        else:
            self.vision.mode = Vision.CARGO_MODE
            self.cargo_component.intake()

    def outtake(self, force=False):
        self.engage(initial_state="outtaking_cargo", force=force)

    @state(must_finish=True)
    def outtaking_cargo(self, initial_call, state_tm):
        if initial_call:
            self.cargo_component.outtake()

        if state_tm > 0.5:
            self.cargo_component.stop()
            self.done()

    def release_pressure(self, target: float) -> bool:
        if target > self.cargo_component.encoder.getPosition():
            self.cargo_component.move_to(Height.LOADING_STATION)
            self.cargo_component.unratchet()

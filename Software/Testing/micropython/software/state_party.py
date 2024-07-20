import time
from animations import AnimationChilePulse
from ili9341 import color565
from setup import button, display, neopixels, unispace
from state import State


class PartyState(State):
    @property
    def name(self):
        return "party"

    def __init__(self):
        self.counter = 0
        self.bounce = 0
        self.green = True
        self.chilePulse = AnimationChilePulse()

    def enter(self, machine):
        display.clear()
        display.draw_text(0, 0, "Party Mode", unispace, color565(255, 255, 255))
        for value in range(0, 18):
            neopixels[value] = [0, 0, 0]
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:
            machine.go_to_state("menu")
        self.chilePulse.animate()
        time.sleep_ms(50)

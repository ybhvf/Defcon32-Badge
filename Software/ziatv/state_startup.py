from lib.ili9341 import color565
from setup import display, neopixels, unispace
from state import State
import time

class StartupState(State):
    color = (0, 0, 0)
    timer = 0
    stage = 0

    @property
    def name(self):
        return "startup"

    def enter(self, machine):
        display.clear()
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        # Display Test
        display.draw_image("dczia.raw")
        time.sleep(4)
        display.draw_text(0, 0, 'DCZia SSTV Badge Test', unispace,
                          color565(255, 255, 255))

        # Neopixel Test
        for value in range(0,18):
            neopixels[value] = [25, 0, 0]
        neopixels.write()
        time.sleep(1)

        for value in range(0,18):
            neopixels[value] = [0, 25, 0]
        neopixels.write()
        time.sleep(1)

        for value in range(0,18):
            neopixels[value] = [0, 0, 25]
        neopixels.write()
        machine.go_to_state("menu")


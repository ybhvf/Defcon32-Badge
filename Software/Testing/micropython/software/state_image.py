from setup import display, button
from state import State

class ImageDisplayState(State):
    @property
    def name(self):
        return "image_display"

    def enter(self, machine):
        display.clear()
        display.draw_image("dczia.raw")
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:
            machine.go_to_state("menu")

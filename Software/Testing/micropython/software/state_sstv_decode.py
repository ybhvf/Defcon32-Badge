from ili9341 import color565
from setup import button, display, unispace
from state import State

class SSTVDecoderState(State):
    @property
    def name(self):
        return "sstv_decoder"

    def enter(self, machine):
        display.clear()
        display.draw_text(0, 0, 'SSTV Decoder', unispace,
                          color565(255, 255, 255))
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:
            machine.go_to_state("menu")
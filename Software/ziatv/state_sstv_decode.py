from machine import freq
from setup import button, display
from state import State

from sstv import Decoder


class SSTVDecoderState(State):
    @property
    def name(self):
        return "sstv_decoder"

    def __init__(self):
        super().__init__()
        self.in_image = False

    def enter(self, core_machine):
        self.run_decoder()
        super().enter(core_machine)

    def update(self, core_machine):
        # clear image when button is pressed
        if self.in_image:
            if button.value() == 0:
                self.in_image = False
                display.clear()
                core_machine.go_to_state("menu")

    def run_decoder(self):
        display.clear()

        freq(200000000)

        with open("/sd/decoded.raw", "wb") as f:
            dc = Decoder(f.write)
            dc.run()

        freq(125000000)

        self.in_image = True

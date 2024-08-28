import gc
from setup import button, display
from state import State

import sstv_decode

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

            dc = sstv_decode.SSTVDecoder()
            dc.run()
            gc.collect()

            self.in_image = True

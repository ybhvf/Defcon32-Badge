from lib.ili9341 import color565
from setup import button, display, unispace, rotary_enc
from state import State
from menu import menu_select, show_menu, show_select

import sstv_decode

class SSTVDecoderState(State):
    menu_items = [
        {
            "name": "run_decode",
            "pretty": "Decode SSTV (Long)",
        },
        {
            "name": "menu",
            "pretty": "Main Menu",
        },
    ]

    @property
    def name(self):
        return "sstv_decoder"

    def __init__(self):
        super().__init__()
        self.last_position = 0
        self.shift = 0
        self.in_image = False

    def enter(self, core_machine):
        self.run_decoder()
        super().enter(core_machine)

    def update(self, core_machine):
        position = rotary_enc.value() % len(self.menu_items)

        # clear image when button is pressed
        if self.in_image:
            if button.value() == 0:
                display.clear()
                self.in_image = False
                self.last_position = 0
                self.shift = 0
                rotary_enc.reset()
                show_menu(self.menu_items, self.last_position, self.shift)
                show_select(self.menu_items, self.last_position, self.shift)
            return True

        # handle rotary update
        if self.last_position != position:
            show_select(self.menu_items, position - self.shift, self.shift)
            self.last_position = position

        # handle button press
        if button.value() == 0:
            selection = self.menu_items[position + self.shift]["name"]
            if selection == "menu":
                core_machine.go_to_state("menu")
            else:
                self.run_decoder()

        return True

    def run_decoder(self):
            display.clear()

            dc = sstv_decode.SSTVDecoder()
            dc.run()

            self.in_image = True

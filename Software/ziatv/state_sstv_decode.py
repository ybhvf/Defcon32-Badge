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
        self.total_lines = 10
        self.list_length = len(self.menu_items)
        self.shift = 0

    def enter(self, machine):
        display.clear()
        self.last_position = 0
        self.shift = 0
        rotary_enc.reset()
        show_menu(self.menu_items, self.last_position, self.shift)
        show_select(self.menu_items, self.last_position, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        position = rotary_enc.value()

        # Don't move decoder past the end of the list
        if position >= self.list_length:
            position = self.last_position
            rotary_enc.set(value=position)

        if self.last_position != position:
            show_select(self.menu_items, position - self.shift, self.shift)
            self.last_position = position

        if button.value() is 0:
            if self.menu_items[position + self.shift]["name"] == "menu":
                machine.go_to_state("menu")
            else:
                self.select(self.menu_items[position + self.shift]["name"], machine)

    def select(self, selection, machine):
        if selection == "run_decode":
            self.run_decoder(machine)

    def run_decoder(self, machine):
            dc = sstv_decode.SSTVDecoder()
            dc.run()

            machine.go_to_state("sstv_decoder")

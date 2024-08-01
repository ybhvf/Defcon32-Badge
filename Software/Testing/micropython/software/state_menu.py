import time
from ili9341 import color565
from setup import button, display, rotary_enc, unispace
from state import State
from menu import menu_select, show_menu, show_select


class MenuState(State):
    menu_items = [
        {
            "name": "party",
            "pretty": "Party",
        },
        {
            "name": "rave",
            "pretty": "Rave",
        },
        {
            "name": "sstv_encoder",
            "pretty": "SSTV Encoder",
        },
        {
            "name": "sstv_decoder",
            "pretty": "SSTV Decoder",
        },
        {
            "name": "image_display",
            "pretty": "Display Image",
        },
        {
            "name": "startup",
            "pretty": "Startup State (test)",
        },
    ]

    @property
    def name(self):
        return "menu"

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
        rotary_enc.reset()
        State.exit(self, machine)

    def update(self, machine):
        # Some code here to use an encoder to scroll through menu options, press to select one
        position = rotary_enc.value()

        # Don't move encoder past the end of the list
        if position >= self.list_length:
            position = self.last_position
            rotary_enc.set(value=position)

        # UNNEEDED FOR MENUS UNDER 10
        ## Allow for more than screen length number of options
        # if position > (self.total_lines - 1 + self.shift):
        #    self.shift = self.total_lines * int(position / self.total_lines)
        #    display.clear()
        #    show_menu(self.menu_items, position - self.shift, self.shift)
        # if position < self.shift:
        #    self.shift = self.total_lines * int(position / self.total_lines)
        #    display.clear()
        #    show_menu(self.menu_items, position - self.shift, self.shift)

        if self.last_position != position:
            show_select(self.menu_items, position - self.shift, self.shift)
            self.last_position = position

        if button.value() is 0:
            machine.go_to_state(self.menu_items[self.last_position]["name"])

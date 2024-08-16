import time
from animations import (
    AnimationChilePulse,
    AnimationRainbow,
    AnimationRainbowChase,
    AnimationRainbowPulse,
)
from lib.ili9341 import color565
from setup import button, display, neopixels, rotary_enc, unispace
from state import State
from menu import menu_select, show_menu, show_select


class PartyState(State):
    menu_items = [
        {
            "name": "chile",
            "pretty": "Chile",
        },
        {
            "name": "rainbow",
            "pretty": "Rainbow",
        },
        {
            "name": "rainbowchase",
            "pretty": "Chase",
        },
        {
            "name": "menu",
            "pretty": "Main Menu",
        },
    ]

    @property
    def name(self):
        return "party"

    def __init__(self):
        self.total_lines = 10
        self.list_length = len(self.menu_items)
        self.shift = 0
        self.animation = AnimationChilePulse()

    def enter(self, machine):
        display.clear()
        self.last_position = 0
        self.shift = 0
        rotary_enc.reset()
        show_menu(self.menu_items, self.last_position, self.shift)
        show_select(self.menu_items, self.last_position, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        for value in range(0, 18):
            neopixels[value] = [0, 0, 0]
        neopixels.write()
        State.exit(self, machine)

    def update(self, machine):
        self.animation.animate()
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
            if self.menu_items[position + self.shift]["name"] == "menu":
                machine.go_to_state("menu")
            else:
                self.select(self.menu_items[position + self.shift]["name"])

    def select(self, selection):
        if selection == "chile":
            self.animation = AnimationChilePulse()

        if selection == "rainbow":
            self.animation = AnimationRainbow()

        if selection == "rainbowchase":
            self.animation = AnimationRainbowChase()

import time
from ili9341 import color565
from setup import button, display, rotary_enc, unispace
from state import State


class MenuState(State):
    menu_items = [
        {
            "name": "party",
            "pretty": "Party",
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
            print(position)
            print(self.shift)

        if button.value() is 0:
            machine.go_to_state(self.menu_items[position + self.shift]["name"])


def menu_select(last_position, menu_items):
    # Force last_position to not equal rotary_enc.value() and be % = 0
    last_position = -len(menu_items)
    rotary_enc.reset()
    item_selected = False
    while item_selected is False:
        current_position = rotary_enc.value()

        # Generate a valid index from the position
        if current_position != last_position:
            index = current_position % len(menu_items)
            # Display item
            pretty_name = menu_items[index]["pretty"]
            text = str.format("{}: {}", index, pretty_name)
            display.draw_text(
                0,
                108,
                text,
                unispace,
                color565(0, 0, 0),
                background=color565(255, 255, 255),
            )
            last_position = current_position


def show_menu(menu, highlight, shift):
    """Shows the menu on the screen"""

    # menu variables
    item = 1
    line = 0
    line_height = 24
    offset = 5
    total_lines = 10

    # Shift the list of files so that it shows on the display
    short_list = []
    for index in range(shift, shift + total_lines):
        try:
            short_list.append(menu[index]["pretty"])
        except IndexError:
            print("show_menu: Bad Index")
    for item in short_list:
        display.draw_text(
            0,
            line * line_height,
            "  " + item,
            unispace,
            color565(255, 255, 255),
            background=color565(0, 0, 0),
        )
        line += 1


def show_select(menu, highlight, shift):
    """Current selection icon"""

    # menu variables
    item = 1
    line = 0
    line_height = 24
    offset = 5
    total_lines = 10

    # Shift the list of files so that it shows on the display
    short_list = []
    for index in range(shift, shift + total_lines):
        try:
            short_list.append(menu[index]["pretty"])
        except IndexError:
            print("show_menu: Bad Index")
    for item in short_list:
        if highlight == line:
            display.draw_text(
                0,
                line * line_height,
                ">",
                unispace,
                color565(255, 255, 255),
                background=color565(0, 0, 0),
            )
        else:
            display.draw_text(
                0,
                line * line_height,
                "  ",
                unispace,
                color565(255, 255, 255),
                background=color565(0, 0, 0),
            )
        line += 1

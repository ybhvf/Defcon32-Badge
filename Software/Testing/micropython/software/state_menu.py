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
        self.highlight = 1
        self.shift = 0

    def enter(self, machine):
        display.clear()
        self.last_position = 0
        self.button_position = 1
        show_menu(self.menu_items, self.highlight, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        rotary_enc.reset()
        State.exit(self, machine)

    def update(self, machine):
        # Some code here to use an encoder to scroll through menu options, press to select one
        position = rotary_enc.value()
        list_length = len(self.menu_items)  # TODO: Doesn't change every frame

        if self.last_position != position:
            if position < self.last_position:
                if self.highlight > 1:
                    self.highlight -= 1
                else:
                    if self.shift > 0:
                        self.shift -= 1
            else:
                if self.highlight < self.total_lines:
                    self.highlight += 1
                else:
                    if self.shift + self.total_lines < list_length:
                        self.shift += 1
            show_menu(self.menu_items, self.highlight, self.shift)
        self.last_position = position
        if button.value() is 0:
            machine.go_to_state(
                self.menu_items[self.highlight - 1 + self.shift]["name"]
            )

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
            display.draw_text(0, 108, text, unispace,
                  color565(0, 0, 0), background = color565(255,255,255))
            last_position = current_position

        # Select item
        #enc_buttons_event = enc_buttons.events.get()
        #if enc_buttons_event and enc_buttons_event.pressed:
        #    index = current_position % len(menu_items)
        #    return menu_items[index]["name"]

def show_menu(menu, highlight, shift):
    """Shows the menu on the screen"""

    # menu variables
    item = 1
    line = 1
    line_height = 24
    offset = 5
    total_lines = 5

    # Shift the list of files so that it shows on the display
    short_list = []
    for index in range(shift, shift + total_lines):
        try:
            short_list.append(menu[index]["pretty"])
        except IndexError:
            print("show_menu: Bad Index")
    for item in short_list:
        if highlight == line:
            display.draw_text(0, (line-1) * line_height, item, unispace,
                  color565(0, 0, 0), background = color565(255,255,255))

        else:
            display.draw_text(0, (line-1) * line_height, item, unispace,
                  color565(255, 255, 255), background = color565(0, 0, 0))
        line += 1


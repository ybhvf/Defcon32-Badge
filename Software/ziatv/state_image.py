import time
from setup import button, display, rotary_enc
from state import State
from os import listdir
from menu import menu_select, show_menu, show_select


class ImageDisplayState(State):
    @property
    def name(self):
        return "image_display"

    def __init__(self):
        raw_files = []
        for dir in ('/', '/sd', '/sd/images'):
            try:
                files = listdir(dir)
            except Exception as _:
                continue

            for file in files:
                if file.endswith(".raw") and (not file.startswith(".")):
                    raw_files.append({"name": f"{dir}/{file}", "pretty": file})

        raw_files.append({"name": "menu", "pretty": "Return To Menu"})

        self.menu_items = raw_files
        self.menu = False
        self.last_position = 0
        self.shift = 0
        self.total_lines = 10
        self.list_length = len(raw_files)

    def enter(self, machine):
        display.clear()
        display.draw_image("dczia.raw")
        rotary_enc.reset()
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:  # Button Press
            display.clear()
            self.menu = not self.menu
            if self.menu:
                show_menu(self.menu_items, self.last_position, self.shift)
                show_select(self.menu_items, self.last_position, self.shift)
                time.sleep_ms(100)
                return
            else:
                print(self.last_position)
                print(self.shift)
                selection = self.menu_items[self.last_position]["name"]
                if selection == "menu":
                    machine.go_to_state("menu")
                    return
                display.draw_image(selection)

        if self.menu:
            self.selectImage()

    def selectImage(self):
        # Some code here to use an encoder to scroll through menu options, press to select one
        position = rotary_enc.value()

        # Don't move encoder past the end of the list
        if position >= self.list_length:
            position = self.last_position
            rotary_enc.set(value=position)

        if position > (self.total_lines - 1 + self.shift):
            self.shift = self.total_lines * int(position / self.total_lines)
            display.clear()
            show_menu(self.menu_items, position - self.shift, self.shift)
        if position < self.shift:
            self.shift = self.total_lines * int(position / self.total_lines)
            display.clear()
            show_menu(self.menu_items, position - self.shift, self.shift)

        if self.last_position != position:
            show_select(self.menu_items, position - self.shift, self.shift)
            self.last_position = position

        return

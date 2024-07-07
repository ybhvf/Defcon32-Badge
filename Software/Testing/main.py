from setup import (
    neopixels,
    enc_buttons,
    display,
    encoder,
)

# from os import listdir
import displayio
import terminalio
from adafruit_display_text import label
import time

# from supervisor import ticks_ms
import board
import audiobusio

# import audiocore
import audiomixer
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.animation.sparklepulse import SparklePulse


# Setup audio
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)
mixer = audiomixer.Mixer(
    voice_count=1,
    sample_rate=16000,
    channel_count=1,
    bits_per_sample=16,
    samples_signed=True,
)


# Menu code from DC31 Badge

# Function to scroll through a list of menu items and return a selection on encoder press
def menu_select(last_position, menu_items):
    # Force last_position to not equal encoder.position and be % = 0
    last_position = -len(menu_items)
    encoder.position = 0
    item_selected = False
    while item_selected is False:
        current_position = encoder.position

        # Generate a valid index from the position
        if current_position != last_position:
            index = current_position % len(menu_items)
            # Display item
            pretty_name = menu_items[index]["pretty"]
            text = str.format("{}: {}", index, pretty_name)
            text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
            display.show(text_area)
            last_position = current_position

        # Select item
        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            index = current_position % len(menu_items)
            return menu_items[index]["name"]


def show_menu(menu, highlight, shift):
    """Shows the menu on the screen"""

    display_group = displayio.Group()
    # bring in the global variables

    # menu variables
    item = 1
    line = 1
    line_height = 10
    offset = 5
    total_lines = 3

    color_bitmap = displayio.Bitmap(display.width, line_height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    # Shift the list of files so that it shows on the display
    short_list = []
    for index in range(shift, shift + total_lines):
        try:
            short_list.append(menu[index]["pretty"])
        except IndexError:
            print("show_menu: Bad Index")
    for item in short_list:
        if highlight == line:
            white_rectangle = displayio.TileGrid(
                color_bitmap,
                pixel_shader=color_palette,
                x=0,
                y=((line - 1) * line_height),
            )
            display_group.append(white_rectangle)
            text_arrow = ">"
            text_arrow = label.Label(
                terminalio.FONT,
                text=text_arrow,
                color=0x000000,
                x=0,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_arrow)
            text_item = label.Label(
                terminalio.FONT,
                text=item,
                color=0x000000,
                x=10,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_item)
        else:
            text_item = label.Label(
                terminalio.FONT,
                text=item,
                x=10,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_item)
        line += 1
    display.show(display_group)


# State machine setup


class State(object):
    def __init__(self):
        pass

    @property
    def name(self):
        return ""

    def enter(self, machine):
        pass

    def exit(self, machine):
        pass

    def update(self, machine):
        # if switch.fell:
        #    machine.paused_state = machine.state.name
        #    machine.pause()
        #    return False
        return True


class StateMachine(object):
    def __init__(self):
        self.state = None
        self.states = {}
        self.last_enc1_pos = encoder.position
        self.paused_state = None
        self.ticks_ms = 0
        self.animation = None

    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]
        self.state.enter(self)

    def update(self):
        if self.state:
            self.state.update(self)
            if self.ticks_ms > 0:
                time.sleep(self.ticks_ms / 1000)

    # When pausing, don't exit the state
    def pause(self):
        self.state = self.states["paused"]
        self.state.enter(self)

    # When resuming, don't re-enter the state
    def resume_state(self, state_name):
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]


class SSTV_Encode_State(State):
    @property
    def name(self):
        return "paused"

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.resume_state(machine.paused_state)


class StartupState(State):
    color = (0, 0, 0)
    timer = 0
    stage = 0

    @property
    def name(self):
        return "startup"

    def enter(self, machine):
        neopixels.fill((0, 0, 0))
        State.enter(self, machine)

    def exit(self, machine):
        neopixels.fill((255, 0, 0))
        self.color = (0, 0, 0)
        self.timer = 0
        self.stage = 0
        State.exit(self, machine)

    def update(self, machine):
        self.timer = self.timer + 1
        if self.stage == 0:
            text = "       DCZia\n  SSTV Tool"
            if len(text) > self.timer:
                text = text[0 : self.timer]
            text_area = label.Label(terminalio.FONT, text=text, x=2, y=5)
            display.show(text_area)
            self.color = (self.timer, self.timer, 0)
            if self.timer > (len(text) * 1.5):
                self.timer = 0
                self.stage = 1
        elif self.stage == 1:
            text = "Fueled by Green Chile\n     and Solder"
            if len(text) > self.timer:
                text = text[0 : self.timer]
            text_area = label.Label(terminalio.FONT, text=text, x=2, y=10)
            display.show(text_area)
            if self.timer > (len(text) * 1.5):
                self.timer = 0
                self.stage = 2
        else:
            if self.timer < (255 * 8):
                color = (0, self.timer % 255, 0)
                neopixels[self.timer // 255] = color
                neopixels.show()
                self.timer = self.timer + 1  # make it faster
            else:
                time.sleep(0.1)
                machine.go_to_state("menu")
        # Skip to menu if encoder is pressed
        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.go_to_state("menu")


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
            "name": "startup",
            "pretty": "Startup State (test)",
        },
    ]

    @property
    def name(self):
        return "menu"

    def __init__(self):
        self.total_lines = 3
        self.list_length = len(self.menu_items)
        self.highlight = 1
        self.shift = 0

    def enter(self, machine):
        self.last_position = 0
        if machine.animation is None:
            machine.animation = Rainbow(neopixels, speed=0.1)
        show_menu(self.menu_items, self.highlight, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        encoder.position = 0
        State.exit(self, machine)

    def update(self, machine):
        # Code for moving through menu and selecting mode
        if machine.animation:
            machine.animation.animate()
        # Some code here to use an encoder to scroll through menu options, press to select one
        position = encoder.position
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

        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.go_to_state(
                self.menu_items[self.highlight - 1 + self.shift]["name"]
            )


class SSTVEncoderState(State):
    @property
    def name(self):
        return "sstv_encoder"

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        # SSTV Encoder code
        text = "SSTV Encoder"
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
        display.show(text_area)
        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.go_to_state("menu")


class SSTVDecoderState(State):
    @property
    def name(self):
        return "sstv_decoder"

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        # SSTV Encoder code
        text = "SSTV Decoder"
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
        display.show(text_area)
        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.go_to_state("menu")


class PartyState(State):
    menu_items = [
        {
            "function": "rainbow",
            "pretty": "Rainbow",
        },
        {
            "function": "rainbow_chase",
            "pretty": "Rainbow Chase",
        },
        {
            "function": "rainbow_comet",
            "pretty": "Rainbow Comet",
        },
        {
            "function": "rainbow_sparkle",
            "pretty": "Rainbow Sparkle",
        },
        {
            "function": "sparkle_pulse",
            "pretty": "Sparkle Pulse",
        },
    ]

    @property
    def name(self):
        return "party"

    def __init__(self):
        self.total_lines = 3
        self.list_length = len(self.menu_items)
        self.highlight = 1
        self.shift = 0

    def enter(self, machine):
        self.last_position = 0
        show_menu(self.menu_items, self.highlight, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        neopixels.fill((255, 0, 0))
        neopixels.show()
        encoder.position = 0
        State.exit(self, machine)

    def update(self, machine):
        position = encoder.position
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
            selection = self.menu_items[self.highlight - 1 + self.shift]["function"]
            self.animation_selector(machine, selection)
        if machine.animation:
            machine.animation.animate()
        self.last_position = position
        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.go_to_state("menu")

    def animation_selector(self, machine, name):
        if name == "rainbow":
            machine.animation = Rainbow(neopixels, speed=0.1)
        elif name == "rainbow_chase":
            machine.animation = RainbowChase(neopixels, speed=0.1)
        elif name == "rainbow_comet":
            machine.animation = RainbowComet(neopixels, speed=0.1, tail_length=10)
        elif name == "rainbow_sparkle":
            machine.animation = RainbowSparkle(
                neopixels, speed=0.1, period=5, num_sparkles=None, step=1
            )
        elif name == "sparkle_pulse":
            machine.animation = SparklePulse(
                neopixels,
                speed=0.1,
                color=(0, 255, 0),
                period=5,
                max_intensity=1,
                min_intensity=0,
            )


machine = StateMachine()
machine.add_state(StartupState())
machine.add_state(MenuState())
machine.add_state(SSTVEncoderState())
machine.add_state(SSTVDecoderState())
machine.add_state(PartyState())
sequencer = run_sequencer()

machine.go_to_state("startup")

while True:
    machine.update()

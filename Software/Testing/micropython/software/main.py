# The MIT License (MIT)
# Copyright (c) 2019 Michael Shi
# Copyright (c) 2020 Mike Teachman
# https://opensource.org/licenses/MIT

# Purpose:
# - read 32-bit audio samples from the left channel of an I2S microphone
# - snip upper 16-bits from each 32-bit microphone sample
# - write 16-bit samples to a SD card file using WAV format
#
# Recorded WAV file is named:
#   "mic_left_channel_16bits.wav"
#
# Hardware tested:
# - INMP441 microphone module 
# - MSM261S4030H0 microphone module

import os
from machine import Pin
from sdcard import SDCard
from machine import I2S
from machine import SPI
import time
from ili9341 import color565
from xglcd_font import XglcdFont
from setup import sd_spi, display, sd, rotary_enc, neopixels, button


# Load font
unispace = XglcdFont('fonts/Unispace12x24.c', 12, 24)

# Function to scroll through a list of menu items and return a selection on encoder press
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


class State(object):
    def __init__(self):
        pass

    @property
    def name(self):
        return ""

    def enter(self, core_machine):
        pass

    def exit(self, core_machine):
        pass

    def update(self, core_machine):
        return True


class StateMachine(object):
    def __init__(self):
        self.state = None
        self.states = {}
        self.last_enc1_pos = rotary_enc.value()
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


class StartupState(State):
    color = (0, 0, 0)
    timer = 0
    stage = 0

    @property
    def name(self):
        return "startup"

    def enter(self, machine):
        display.clear()
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        # Display Test
        display.draw_image("dczia.raw")
        time.sleep(4)
        display.draw_text(0, 0, 'DCZia SSTV Badge Test', unispace,
                          color565(255, 255, 255))

        # Neopixel Test
        for value in range(0,18):
            neopixels[value] = [25, 0, 0]
        neopixels.write()
        time.sleep(1)

        for value in range(0,18):
            neopixels[value] = [0, 25, 0]
        neopixels.write()
        time.sleep(1)

        for value in range(0,18):
            neopixels[value] = [0, 0, 25]
        neopixels.write()
        core_machine.go_to_state("menu")

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

class PartyState(State):
    @property
    def name(self):
        return "party"

    def enter(self, machine):
        display.clear()
        display.draw_text(0, 0, 'Party Mode', unispace,
                          color565(255, 255, 255))
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:
            machine.go_to_state("menu")

class SSTVEncoderState(State):
    @property
    def name(self):
        return "sstv_encoder"

    def enter(self, machine):
        display.clear()
        display.draw_text(0, 0, 'SSTV Encoder', unispace,
                          color565(255, 255, 255))
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:
            machine.go_to_state("menu")

class SSTVDecoderState(State):
    @property
    def name(self):
        return "sstv_decoder"

    def enter(self, machine):
        display.clear()
        display.draw_text(0, 0, 'SSTV Decoder', unispace,
                          color565(255, 255, 255))
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:
            machine.go_to_state("menu")

class ImageDisplayState(State):
    @property
    def name(self):
        return "image_display"

    def enter(self, machine):
        display.clear()
        display.draw_image("dczia.raw")
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:
            machine.go_to_state("menu")


core_machine = StateMachine()
core_machine.add_state(StartupState())
core_machine.add_state(MenuState())
core_machine.add_state(SSTVEncoderState())
core_machine.add_state(SSTVDecoderState())
core_machine.add_state(PartyState())
core_machine.add_state(ImageDisplayState())

core_machine.go_to_state("startup")

while True:
    core_machine.update()

# Record Audio Test
#--------------------------------------------------------------------------------------------
# ======= I2S CONFIGURATION =======
SCK_PIN = 0
WS_PIN = 1
SD_PIN = 3
I2S_ID = 0
BUFFER_LENGTH_IN_BYTES = 60000  # larger buffer to accommodate slow SD card driver
# ======= I2S CONFIGURATION =======


# ======= AUDIO CONFIGURATION =======
WAV_FILE = "mic.wav"
RECORD_TIME_IN_SECONDS = 5
WAV_SAMPLE_SIZE_IN_BITS = 16
FORMAT = I2S.MONO
SAMPLE_RATE_IN_HZ = 22050
# ======= AUDIO CONFIGURATION =======

format_to_channels = {I2S.MONO: 1, I2S.STEREO: 2}
NUM_CHANNELS = format_to_channels[FORMAT]
WAV_SAMPLE_SIZE_IN_BYTES = WAV_SAMPLE_SIZE_IN_BITS // 8
RECORDING_SIZE_IN_BYTES = (
    RECORD_TIME_IN_SECONDS * SAMPLE_RATE_IN_HZ * WAV_SAMPLE_SIZE_IN_BYTES * NUM_CHANNELS
)


def create_wav_header(sampleRate, bitsPerSample, num_channels, num_samples):
    datasize = num_samples * num_channels * bitsPerSample // 8
    o = bytes("RIFF", "ascii")  # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(
        4, "little"
    )  # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE", "ascii")  # (4byte) File type
    o += bytes("fmt ", "ascii")  # (4byte) Format Chunk Marker
    o += (16).to_bytes(4, "little")  # (4byte) Length of above format data
    o += (1).to_bytes(2, "little")  # (2byte) Format type (1 - PCM)
    o += (num_channels).to_bytes(2, "little")  # (2byte)
    o += (sampleRate).to_bytes(4, "little")  # (4byte)
    o += (sampleRate * num_channels * bitsPerSample // 8).to_bytes(4, "little")  # (4byte)
    o += (num_channels * bitsPerSample // 8).to_bytes(2, "little")  # (2byte)
    o += (bitsPerSample).to_bytes(2, "little")  # (2byte)
    o += bytes("data", "ascii")  # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4, "little")  # (4byte) Data size in bytes
    return o


wav = open("/sd/{}".format(WAV_FILE), "wb")

# create header for WAV file and write to SD card
wav_header = create_wav_header(
    SAMPLE_RATE_IN_HZ,
    WAV_SAMPLE_SIZE_IN_BITS,
    NUM_CHANNELS,
    SAMPLE_RATE_IN_HZ * RECORD_TIME_IN_SECONDS,
)
num_bytes_written = wav.write(wav_header)

audio_in = I2S(
    I2S_ID,
    sck=Pin(SCK_PIN),
    ws=Pin(WS_PIN),
    sd=Pin(SD_PIN),
    mode=I2S.RX,
    bits=WAV_SAMPLE_SIZE_IN_BITS,
    format=FORMAT,
    rate=SAMPLE_RATE_IN_HZ,
    ibuf=BUFFER_LENGTH_IN_BYTES,
)

# allocate sample arrays
# memoryview used to reduce heap allocation in while loop
mic_samples = bytearray(10000)
mic_samples_mv = memoryview(mic_samples)

num_sample_bytes_written_to_wav = 0

print("Recording size: {} bytes".format(RECORDING_SIZE_IN_BYTES))
print("==========  START RECORDING ==========")
try:
    while num_sample_bytes_written_to_wav < RECORDING_SIZE_IN_BYTES:
        # read a block of samples from the I2S microphone
        num_bytes_read_from_mic = audio_in.readinto(mic_samples_mv)
        if num_bytes_read_from_mic > 0:
            num_bytes_to_write = min(
                num_bytes_read_from_mic, RECORDING_SIZE_IN_BYTES - num_sample_bytes_written_to_wav
            )
            # write samples to WAV file
            I2S.shift(buf = mic_samples_mv, bits = 16, shift = 4)
            num_bytes_written = wav.write(mic_samples_mv[:num_bytes_to_write])
            num_sample_bytes_written_to_wav += num_bytes_written

    print("==========  DONE RECORDING ==========")
except (KeyboardInterrupt, Exception) as e:
    print("caught exception {} {}".format(type(e).__name__, e))
# ---------------------------------------------------------------------------------------------

# cleanup
wav.close()
os.umount("/sd")
sd_spi.deinit()
audio_in.deinit()
print('Done')
print('%d sample bytes written to WAV file' % num_sample_bytes_written_to_wav)
import time
import struct
from animations import AnimationRainbowPulse
from ili9341 import color565
from setup import button, display, neopixels, rotary_enc, unispace
from state import State
from machine import Pin, I2S
import math


class RaveState(State):
    @property
    def name(self):
        return "rave"

    def __init__(self):
        self.counter = 0
        self.previous_intensity = 0
        self.max_intensity = 0
        self.knob = 0
        self.volume = 1
        self.green = True
        self.animation = AnimationRainbowPulse()
        self.mic_samples = bytearray(4)
        self.mic_samples_mv = memoryview(self.mic_samples)

    def enter(self, machine):
        display.clear()
        display.draw_text(0, 0, "Rave Mode", unispace, color565(255, 255, 255))
        display.draw_text(
            0,
            30,
            "Volume: {}   ".format(self.knob),
            unispace,
            color565(255, 255, 255),
        )
        for value in range(0, 18):
            neopixels[value] = [4, 0, 0]
        neopixels.write()
        I2S_ID = 0
        self.audio_in = I2S(
            I2S_ID,
            sck=Pin(0),
            ws=Pin(1),
            sd=Pin(3),
            mode=I2S.RX,
            bits=16,
            format=I2S.MONO,
            rate=22000,
            ibuf=150,
        )
        State.enter(self, machine)

    def exit(self, machine):
        self.audio_in.deinit()
        State.exit(self, machine)

    def update(self, machine):
        self.counter = self.counter + 1
        if button.value() is 0:
            machine.go_to_state("menu")
            return

        num_bytes_read_from_mic = self.audio_in.readinto(self.mic_samples_mv)
        total = struct.unpack("<h", self.mic_samples)
        new_knob = rotary_enc.value()
        if new_knob < 0:
            new_knob = 0
        if new_knob != self.knob:
            self.knob = new_knob
            self.volume = math.pow(2, self.knob)
            # print(self.volume)
            display.draw_text(
                0,
                30,
                "Volume: {}   ".format(new_knob),
                unispace,
                color565(255, 255, 255),
            )
        intensity = int(abs(total[0]) / self.volume)
        if intensity > 200:
            intensity = 200
        if (intensity > 0) and (intensity != self.previous_intensity):
            self.previous_intensity = intensity
            self.animation.animate(intensity)

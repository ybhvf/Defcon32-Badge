import time
from animations import AnimationChilePulse, AnimationRainbow, AnimationRainbowChase
from ili9341 import color565
from setup import button, display, neopixels, unispace
from state import State
from machine import Pin, I2S


class RaveState(State):
    @property
    def name(self):
        return "rave"

    def __init__(self):
        self.counter = 0
        self.bounce = 0
        self.green = True
        self.animation = AnimationRainbow()
        self.mic_samples = bytearray(2)
        self.mic_samples_mv = memoryview(self.mic_samples)

    def enter(self, machine):
        display.clear()
        display.draw_text(0, 0, "Rave Mode", unispace, color565(255, 255, 255))
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
            rate=8000,
            ibuf=600,
        )
        State.enter(self, machine)

    def exit(self, machine):
        self.audio_in.deinit()
        State.exit(self, machine)

    def update(self, machine):
        if button.value() is 0:
            machine.go_to_state("menu")

        num_bytes_read_from_mic = self.audio_in.readinto(self.mic_samples_mv)
        # if num_bytes_read_from_mic > 0:
        #    print(self.mic_samples)
        for value in range(0, 18):
            neopixels[value] = [0, self.mic_samples[0], 0]
        neopixels.write()
        time.sleep_ms(10)

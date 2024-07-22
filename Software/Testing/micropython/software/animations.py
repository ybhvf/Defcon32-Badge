import time
from setup import neopixels
from colorwheel import colorwheel

max_brightness = 20


class AnimationChilePulse:
    def __init__(self):
        self.counter = 0
        self.bounce = 0
        self.green = True

    def animate(self):
        timer = (time.ticks_ms() / 20) % 255
        if timer < self.counter:
            self.green = not self.green
        self.counter = timer

        intensity = timer
        if intensity > 127:
            intensity = 127 - (intensity - 127)

        intensity = int((intensity / 127) * max_brightness)

        if self.green:
            for value in range(0, 18):
                neopixels[value] = [intensity, 0, 0]
        else:
            for value in range(0, 18):
                neopixels[value] = [0, intensity, 0]
        neopixels.write()


class AnimationRainbow:
    def __init__(self):
        self.counter = 0

    def animate(self):
        self.counter = (time.ticks_ms() / 20) % 255

        temp = colorwheel(self.counter, max_brightness)
        for value in range(0, 18):
            neopixels[value] = temp

        neopixels.write()


class AnimationRainbowPulse:
    def __init__(self):
        self.counter = 0

    def animate(self, intensity):
        self.counter = (time.ticks_ms() / 20) % 255

        temp = colorwheel(self.counter, intensity)
        for value in range(0, 18):
            neopixels[value] = temp

        neopixels.write()


class AnimationRainbowChase:
    def __init__(self):
        self.counter = 0

    def animate(self):
        timer = time.ticks_ms()
        color = (timer / 20) % 255

        temp = colorwheel(color, max_brightness)
        for value in range(0, 18):
            if value == (int(timer / 20) % 18):
                neopixels[value] = temp
            else:
                neopixels[value] = [0, 0, 0]

        neopixels.write()
        self.counter += 1

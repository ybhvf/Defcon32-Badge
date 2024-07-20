from setup import neopixels


class AnimationChilePulse:
    def __init__(self):
        self.counter = 0
        self.bounce = 0
        self.green = True

    def animate(self):
        if self.counter > 20:
            self.bounce = 1
        elif self.counter <= 1:
            self.bounce = 0
            self.green = self.green ^ True

        if self.bounce is 0:
            self.counter += 1
        else:
            self.counter -= 1

        if self.green:
            for value in range(0, 18):
                neopixels[value] = [self.counter, 0, 0]
        else:
            for value in range(0, 18):
                neopixels[value] = [0, self.counter, 0]
        neopixels.write()

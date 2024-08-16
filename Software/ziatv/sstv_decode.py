import math
from machine import Pin, I2S
from setup import display, unispace
from lib.ili9341 import color565

from ulab import numpy as np
from ulab import scipy

# Audio Configuration
SAMPLE_RATE = 32000
TIME_STEP = 1 / SAMPLE_RATE
FRAMES = 20000

# Other Constants
MS = 1. / 1000.

def bandpass(stream):
    # generated via utils/gen_sosfilt.py
    filt = np.array([[ 1.3385296846046354e-07,  2.6770593692092708e-07,
                       1.3385296846046354e-07,  1.0000000000000000e+00,
                      -1.6712602580720473e+00,  7.9145739306059126e-01],
                     [ 1.0000000000000000e+00,  2.0000000000000000e+00,
                       1.0000000000000000e+00,  1.0000000000000000e+00,
                      -1.7111299093331693e+00,  7.9853753589465892e-01],
                     [ 1.0000000000000000e+00,  2.0000000000000000e+00,
                       1.0000000000000000e+00,  1.0000000000000000e+00,
                      -1.6828762763295724e+00,  8.3870661060177676e-01],
                     [ 1.0000000000000000e+00,  0.0000000000000000e+00,
                      -1.0000000000000000e+00,  1.0000000000000000e+00,
                      -1.7787587501803395e+00,  8.4348301397040448e-01],
                     [ 1.0000000000000000e+00, -2.0000000000000000e+00,
                       1.0000000000000000e+00,  1.0000000000000000e+00,
                      -1.8506161354617696e+00,  9.0323355088684287e-01],
                     [ 1.0000000000000000e+00, -2.0000000000000000e+00,
                       1.0000000000000000e+00,  1.0000000000000000e+00,
                      -1.7525704868602121e+00,  9.3707910665413174e-01],
                     [ 1.0000000000000000e+00, -2.0000000000000000e+00,
                       1.0000000000000000e+00,  1.0000000000000000e+00,
                      -1.9188013677690570e+00,  9.6699787238406743e-01]])

    zi = np.array([[ 4.3205949174469995e-06, -3.3916527428441191e-06],
                   [ 1.9939265613190259e-04, -1.5832511625573682e-04],
                   [ 5.0286926314544872e-03, -4.1847185623592777e-03],
                   [-5.2325397354722877e-03, -5.2325397354723059e-03],
                   [-0.0000000000000000e+00,  0.0000000000000000e+00],
                   [-0.0000000000000000e+00,  0.0000000000000000e+00],
                   [-0.0000000000000000e+00,  0.0000000000000000e+00]])

    for chunk in stream:
        data, zi = scipy.signal.sosfilt(filt, chunk, zi=zi)
        for x in data:
            yield x


def bin_freq(freq):
    bins = [1100, 1200, 1300, 1500, 1900, 2300]
    mids = [1150, 1250, 1400, 1700, 2100]

    for i in range(len(mids)):
        if freq < mids[i]:
            return bins[i]

    return bins[-1]


def freq_to_lum(x):
    x = (x - 1500.) / 3.1372549
    return min(max(round(x), 0.), 255.)


def zcr(stream, sample_rate):
    idx = 0
    last_amp = 0
    last_idx = 0

    for amp in stream:
        period = (idx - last_idx)

        # if zero is crossed, or freq < 10hz
        if (last_amp * amp < 0) or (period > sample_rate / 10):
            freq = 0.5 * sample_rate / period
            last_idx = idx
            last_amp = amp

            for _ in range(period):
                yield freq

        # since this is long-running, keep the indices small
        if idx > (1 << 31):
            last_idx = idx - last_idx
            idx = 0

        idx += 1


def goertzel(signal, freqs, sample_rate):
    power = sum(x**2 for x in signal)

    results = []
    for freq in freqs:
        kt = freq / sample_rate
        omega = 2. * math.pi * kt
        coeff = 2. * math.cos(omega)

        prev_0 = 0.
        prev_1 = 0.
        for x in signal:
            val = x + coeff * prev_0 - prev_1
            prev_1 = prev_0
            prev_0 = val

        mag = prev_0**2 + prev_1**2 - (coeff * prev_0 * prev_1)
        results.append(mag / (power * len(signal)))

    return results


class Microphone:
    def __init__(self, sample_rate, frames):
        self.sample_rate = sample_rate
        self.frames = frames

        self.buffer = bytearray(frames * 2)
        self.buf_mv = memoryview(self.buffer)

        self.audio_in = I2S(
            1,
            sck=Pin(0),
            ws=Pin(1),
            sd=Pin(3),
            mode=I2S.RX,
            bits=16,
            format=I2S.MONO,
            rate=self.sample_rate,
            ibuf=self.frames,
        )

    def read(self):
        num_bytes = self.audio_in.readinto(self.buf_mv)
        return np.frombuffer(self.buffer, dtype=np.int16, count=num_bytes // 2)

    def __iter__(self):
        return self

    def __next__(self):
        return self.read()


class SSTVDecoder:
    def __init__(self, sample_rate=SAMPLE_RATE, frames=FRAMES):
        self.sample_rate = sample_rate
        self.time_step = 1 / sample_rate
        self.frames = frames

        self.line = np.zeros((320, 3), dtype=np.uint8)
        self.mic = Microphone(self.sample_rate, self.frames)
        self.stream = zcr(bandpass(self.mic), self.sample_rate)
        self.ts_err = 0.

    def sync_tone(self, tone, length, tone_err=101, length_err=0.1):
        lerr = length * length_err

        ctr = 0
        while True:
            freq = bin_freq(next(self.stream))

            if (freq > tone - tone_err) and (freq < tone + tone_err):
                ctr += self.time_step
            elif (ctr > length - lerr) and (ctr < length + lerr):
                self.ts_err = 0
                return True
            else:
                ctr = 0

    def read_tone(self, length):
        chunk = round((self.ts_err + length) / self.time_step)
        self.ts_err += length - chunk * self.time_step

        buf_iter = (next(self.stream) for _ in range(chunk))
        return np.mean(buf_iter)

    def expect_tone(self, tone, length):
        freq = bin_freq(self.read_tone(length))
        return tone == freq

    def read_s1(self):
        self.expect_tone(1200, 9*MS) # SYNC

        for x in range(256):
            self.read_tone(1.5*MS) # 1500hz
            for y in range(320):
                self.line[y,1] = freq_to_lum(self.read_tone(0.432*MS))

            self.read_tone(1.5*MS) # 1500hz
            for y in range(320):
                self.line[y,2] = freq_to_lum(self.read_tone(0.432*MS))
            self.expect_tone(1200, 9*MS) # SYNC

            self.read_tone(1.5*MS) # 1500hz
            for y in range(320):
                self.line[y,0] = freq_to_lum(self.read_tone(0.432*MS))

            for y in range(320):
                color = color565(self.line[y,0], self.line[y,0], self.line[y,0])
                display.draw_pixel(x, y, color)

    def run(self):
        self.ts_err = 0.

        print("listening for sstv")

        # read calibration header
        self.sync_tone(1900, 300*MS)
        self.expect_tone(1200, 10*MS)
        self.expect_tone(1900, 300*MS)

        print("heard calibration header")

        # read VIS code
        self.expect_tone(1200, 30*MS) # start bit
        vis = [bin_freq(self.read_tone(30*MS)) for _ in range(10)]
        self.expect_tone(1200, 30*MS) # stop bit

        print("vis:", vis)

        display.clear()

        self.read_s1()

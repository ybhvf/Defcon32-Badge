import micropython
import _thread
from collections import deque
from setup import display, unispace
import sstv


def color565(r, g, b):
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3


class SSTVDecoder:
    def __init__(self):
        self.dem = sstv.Dem()
        self.pixbuf = bytearray(320 * 2)
        self.actions = deque([], 10)
        self.active = False

    def read_scottie(self, lines, columns, pix_dt):
        green = bytearray(columns)
        blue = bytearray(columns)
        red = bytearray(columns)

        self.dem.read(0.009)  # SYNC @ 1200hz (ignore)

        for x in range(lines):
            # green
            self.dem.read(0.0015)  # 1500hz ref
            self.dem.read_line(green, pix_dt)

            # blue
            self.dem.read(0.0015)  # 1500hz ref
            self.dem.read_line(blue, pix_dt)
            self.dem.read(0.009)  # SYNC @ 1200hz (ignore)

            # red
            self.dem.read(0.0015)  # 1500hz ref
            self.dem.read_line(red, pix_dt)

            for y in range(columns):
                idx = 2 * y
                self.pixbuf[idx : idx + 2] = color565(
                    red[y], green[y], blue[y]
                ).to_bytes(2, "big")

            self.actions.append(x)

    def read_martin(self, lines, columns, pix_dt):
        green = bytearray(columns)
        blue = bytearray(columns)
        red = bytearray(columns)

        for x in range(lines):
            self.dem.read(0.004862)  # SYNC @ 1200hz (ignore)
            self.dem.read(0.000572)  # 1500hz ref

            # green
            self.dem.read_line(green, pix_dt)
            self.dem.read(0.000572)  # 1500hz ref

            # blue
            self.dem.read_line(blue, pix_dt)
            self.dem.read(0.000572)  # 1500hz ref

            # red
            self.dem.read_line(red, pix_dt)
            self.dem.read(0.000572)  # 1500hz ref

            for y in range(columns):
                idx = 2 * y
                self.pixbuf[idx : idx + 2] = color565(
                    red[y], green[y], blue[y]
                ).to_bytes(2, "big")

            self.actions.append(x)

    def draw(self):
        log_line = 0
        white = color565(255, 255, 255)
        while self.active:
            if self.actions:
                msg = self.actions.popleft()
                if isinstance(msg, str):
                    print(msg)
                    display.draw_text(0, log_line, msg, unispace, white)
                    log_line += 24
                else:
                    display.block(0, msg, 319, msg, self.pixbuf)

    def log(self, msg):
        self.actions.append(msg)

    def _benchmark(self, length=0.25, count=20):
        import time

        for _ in range(count):
            now = time.ticks_ms()
            freq = self.dem.read(length)
            print(time.ticks_ms() - now, freq)

    def run(self):
        self.active = True
        try:
            self.thread = _thread.start_new_thread(self.draw, ())
            self.log("listening for sstv")

            # read calibration header
            self.dem.sync(1900, 0.3)
            self.dem.expect(1200, 0.01)
            self.dem.expect(1900, 0.3)

            self.log("heard calibration header")

            # read VIS code
            self.dem.read(0.03)  # start bit (1200hz)
            vis = 0
            for idx in range(7):
                bit = self.dem.read(0.03) <= 1200
                vis |= bit << idx
            _ = self.dem.read(0.03) <= 1200  # ignore parity bit for the moment
            self.dem.read(0.03)  # stop bit (1200hz)

            # SCOTTIE MODES
            if vis == 60:
                self.log("decoding scottie 1")
                self.read_scottie(256, 320, 0.0004320)
            elif vis == 56:
                self.log("decoding scottie 2")
                self.read_scottie(256, 320, 0.0002752)
            elif vis == 52:
                self.log("decoding scottie 3")
                self.read_scottie(128, 320, 0.0004320)
            elif vis == 48:
                self.log("decoding scottie 4")
                self.read_scottie(128, 320, 0.0002752)
            # MARTIN MODES
            elif vis == 44:
                self.log("decoding martin 1")
                self.read_martin(256, 320, 0.0004576)
            elif vis == 40:
                self.log("decoding martin 2")
                self.read_martin(256, 320, 0.0002288)
            elif vis == 36:
                self.log("decoding martin 3")
                self.read_martin(128, 320, 0.0004576)
            elif vis == 32:
                self.log("decoding martin 4")
                self.read_martin(128, 320, 0.0002288)
            # FAILURE
            else:
                self.log(f"unknown vis: {vis}")
                self.log("decode failed!")
        finally:
            self.active = False

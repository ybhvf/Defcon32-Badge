import array
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
        self.actions = deque([],10)
        self.active = False

    def read_s1(self):
        green = array.array("B", range(320))
        blue = array.array("B", range(320))

        self.dem.expect(1200, 0.009)  # SYNC

        for x in range(256):
            # green
            self.dem.read(0.0015)  # 1500hz
            for y in range(320):
                green[y] = sstv.decode_color(self.dem.read(0.000432))

            # blue
            self.dem.read(0.0015)  # 1500hz
            for y in range(320):
                blue[y] = sstv.decode_color(self.dem.read(0.000432))
            self.dem.expect(1200, 0.009)  # SYNC

            # red
            self.dem.read(0.0015)  # 1500hz
            for y in range(320):
                red = sstv.decode_color(self.dem.read(0.000432))
                idx = 2 * y
                self.pixbuf[idx : idx + 2] = color565(red, green[y], blue[y]).to_bytes(
                    2, "big"
                )

            self.actions.append(x)

    def draw(self):
        log_line = 0
        while self.active:
            if self.actions:
                msg = self.actions.popleft()
                if isinstance(msg, str):
                    print(msg)
                    display.draw_text(0, log_line, msg, unispace, color565(255, 255, 255))
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
            vis = [sstv.bin_freq(self.dem.read(0.03)) for _ in range(8)]
            self.dem.read(0.03)  # stop bit (1200hz)

            self.log(f"vis: {vis}")

            self.read_s1()
        finally:
            self.active = False

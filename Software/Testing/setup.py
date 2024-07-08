import board
import busio as io
import digitalio
import storage
import adafruit_sdcard
import time

# import microcontroller
# import audiocore
import audiobusio
import rotaryio
import neopixel
import keypad

# Display imports
import displayio
import terminalio
import adafruit_ili9341
from adafruit_display_text import label

# Setup I/O

# Screen
cs_pin, reset_pin, dc_pin, mosi_pin, clk_pin = (
    board.GP13,
    board.GP9,
    board.GP8,
    board.GP11,
    board.GP10,
)
displayio.release_displays()
spi = io.SPI(clock=clk_pin, MOSI=mosi_pin)
display_bus = displayio.FourWire(
    spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin
)
display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240, rotation=90)

# Neopixels
pixel_pin = board.GP14
num_pixels = 18
neopixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=True)

# Board LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Encoder buttons
enc_pins = [board.GP19]
enc_buttons = keypad.Keys(enc_pins, value_when_pressed=False, pull=True)

# Setup rotary encoders
encoder = rotaryio.IncrementalEncoder(board.GP16, board.GP17)

# Setup the SD card and mount it as /sd
try:
    spi = io.SPI(board.GP10, board.GP11, board.GP12)
    cs = digitalio.DigitalInOut(board.GP13)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
except:
    text = "No SD Card Found!"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
    display.root_group = text_area
    time.sleep(2)

# Setup audio
# This may need to get moved into main.py, had issues with this in setup.py on DC31 badge
# audio_out = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)
# audio_in = audiobusio.PDMIn(
#     board.GP21, board.GP20, sample_rate=16000, bit_depth=16
# )

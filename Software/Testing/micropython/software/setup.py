import os
import neopixel
from machine import Pin
from machine import SPI
from time import sleep
from sdcard import SDCard
from ili9341 import Display, color565
from rotary_irq_rp2 import RotaryIRQ
from xglcd_font import XglcdFont

# Setup neopixels
neopixels = neopixel.NeoPixel(Pin(14), 18)

# Load font
unispace = XglcdFont('fonts/Unispace12x24.c', 12, 24)

# Setup display
disp_spi = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11))
display = Display(disp_spi, dc=Pin(8), cs=Pin(13), rst=Pin(9), width=320, height=240, rotation=0, mirror=True)

# Setup encoder button
button = Pin(19, Pin.IN, Pin.PULL_UP)

# Setup rotary encoder
rotary_enc = RotaryIRQ(pin_num_clk=16,
              pin_num_dt=17,
              min_val=0,
              max_val=64,
              reverse=True,
              pull_up=True,
              range_mode=RotaryIRQ.RANGE_WRAP)
# Setup SD Card
cs = Pin(5, Pin.OUT)
sd_spi = SPI(
    0,
    baudrate=1_000_000,  # this has no effect on spi bus speed to SD Card
    polarity=0,
    phase=0,
    bits=8,
    firstbit=SPI.MSB,
    sck=Pin(6),
    mosi=Pin(7),
    miso=Pin(4),
)
try:
    sd = SDCard(sd_spi, cs)
    sd.init_spi(25_000_000)  # increase SPI bus speed to SD card
    os.mount(sd, "/sd")
    sd_state = True
except:
    display.clear()
    display.draw_text(0, 0, 'No SD card found!', unispace,
                  color565(255, 255, 255))
    display.draw_text(0, 48, 'Some functionality will be', unispace,
                  color565(255, 255, 255))
    display.draw_text(0, 72, 'borked.', unispace,
                  color565(255, 255, 255))
    sd_state = False
    sleep(4)
    
    

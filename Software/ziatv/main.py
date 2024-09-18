from lib.ili9341 import color565
from machine import Pin, I2S, SPI
from setup import display, sd_state, rotary_enc, neopixels, button, unispace

if sd_state is True:
    from setup import sd_spi, sd
    from lib.sdcard import SDCard
from state import State, StateMachine
from state_image import ImageDisplayState
from state_menu import MenuState
from state_party import PartyState
from state_rave import RaveState
from state_sstv_decode import SSTVDecoderState
from state_sstv_encode import SSTVEncoderState
from state_startup import StartupState

core_machine = StateMachine()
core_machine.add_state(StartupState())
core_machine.add_state(MenuState())
core_machine.add_state(SSTVEncoderState())
core_machine.add_state(SSTVDecoderState())
core_machine.add_state(PartyState())
core_machine.add_state(ImageDisplayState())
core_machine.add_state(RaveState())

core_machine.go_to_state("menu")

while True:
    core_machine.update()

from lib.ili9341 import color565
from setup import button, display, unispace, rotary_enc
from menu import menu_select, show_menu, show_select
from state import State
import sstv_encode

class SSTVEncoderState(State):
    menu_items = [
        {
            "name": "run_encode",
            "pretty": "Encode SSTV (Long)",
        },
        {
            "name": "menu",
            "pretty": "Main Menu",
        },
    ]
    
    @property
    def name(self):
        return "sstv_encoder"

    def __init__(self):
        self.total_lines = 10
        self.list_length = len(self.menu_items)
        self.shift = 0

    def enter(self, machine):
        display.clear()
        self.last_position = 0
        self.shift = 0
        rotary_enc.reset()
        show_menu(self.menu_items, self.last_position, self.shift)
        show_select(self.menu_items, self.last_position, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        position = rotary_enc.value()

        # Don't move encoder past the end of the list
        if position >= self.list_length:
            position = self.last_position
            rotary_enc.set(value=position)

        # UNNEEDED FOR MENUS UNDER 10
        ## Allow for more than screen length number of options
        # if position > (self.total_lines - 1 + self.shift):
        #    self.shift = self.total_lines * int(position / self.total_lines)
        #    display.clear()
        #    show_menu(self.menu_items, position - self.shift, self.shift)
        # if position < self.shift:
        #    self.shift = self.total_lines * int(position / self.total_lines)
        #    display.clear()
        #    show_menu(self.menu_items, position - self.shift, self.shift)

        if self.last_position != position:
            show_select(self.menu_items, position - self.shift, self.shift)
            self.last_position = position

        if button.value() is 0:
            if self.menu_items[position + self.shift]["name"] == "menu":
                machine.go_to_state("menu")
            else:
                self.select(self.menu_items[position + self.shift]["name"], machine)

    def select(self, selection, machine):
        if selection == "run_encode":
            self.run_encoder(machine)
        
    def run_encoder(self, machine):
        display.clear()
        
        # Output file name
        wav_file = 'test.wav'

        # Initialize encoder
        s = sstv_encode.Encode_SSTV('dczia.raw', 320, 20, 44100, 16)
        
        # Initalize wav file and write header
        wav = open("/sd/{}".format(wav_file), "w")
        s.target = wav
        s.write_wav_header(wav)

        # Start encoding
        display.draw_text(0, 0, 'Writing Vox...', unispace,
                  color565(255, 255, 255))
        s.write_vox()
        display.draw_text(0, 24, 'Writing Header...', unispace,
                  color565(255, 255, 255))
        s.write_calibration_header()
        display.draw_text(0, 48, 'Writing VIS...', unispace,
                  color565(255, 255, 255))
        s.write_vis()
        display.draw_text(0, 72, 'Writing Data...', unispace,
                  color565(255, 255, 255))
        display.draw_text(0, 96, 'Line: ', unispace,
          color565(255, 255, 255))

        with open(s.image, "rb") as f:
            for value in range(0, s.height):
                s.write_line(s.width, f)
                display.draw_text(60, 96, str(value), unispace,
                  color565(255, 255, 255))
                
        wav.close()
        display.draw_text(0, 96, 'Done!', unispace,
                  color565(255, 255, 255))
        machine.go_to_state("sstv_encoder")
    

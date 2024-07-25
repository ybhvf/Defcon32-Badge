import os
import sys
from machine import Pin, SPI
from sdcard import SDCard
import time
import math

import struct
from array import array

from setup import sd


def create_wav_header(sampleRate, bitsPerSample, num_channels, num_samples):
    datasize = num_samples * num_channels * bitsPerSample // 8
    o = bytes("RIFF", "ascii")  # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(
        4, "little"
    )  # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE", "ascii")  # (4byte) File type
    o += bytes("fmt ", "ascii")  # (4byte) Format Chunk Marker
    o += (16).to_bytes(4, "little")  # (4byte) Length of above format data
    o += (1).to_bytes(2, "little")  # (2byte) Format type (1 - PCM)
    o += (num_channels).to_bytes(2, "little")  # (2byte)
    o += (sampleRate).to_bytes(4, "little")  # (4byte)
    o += (sampleRate * num_channels * bitsPerSample // 8).to_bytes(4, "little")  # (4byte)
    o += (num_channels * bitsPerSample // 8).to_bytes(2, "little")  # (2byte)
    o += (bitsPerSample).to_bytes(2, "little")  # (2byte)
    o += bytes("data", "ascii")  # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4, "little")  # (4byte) Data size in bytes
    return o

def color565toRGB(pixel):
    colorvalue = int.from_bytes(pixel, 'big')
    red = round(float(colorvalue >> 11) / 31 * 255)
    green = round(float(colorvalue >> 5 & 0x3f) / 63 * 255)
    blue = round(float(colorvalue & 0x1f) / 31 * 255)
    return(red, green, blue)

class Encode_SSTV():
    
    def __init__(self, image, width, height, sample_rate, bits):
        self.image = image
        self.width = width
        self.height = height
        self.sample_rate = sample_rate
        self.sample_length = 1 / sample_rate
        self.bits = bits
        self.vox_enabled = False
        self.fskid_payload = ''
        self.nchannels = 1
        # Define frequencies
        self.calibration_header_freq = 1900
        self.black_tone_freq = 1500
        self.vis_lo_freq = 1300
        self.vis_hi_freq = 1100
        self.sync_freq = 1200
        self.segment_time = 0
        self.phase_shift =0
        self.sample_size_in_bytes = bits // 8
        self.format = "<h"
        self.target = ''
        self.accumulated_error = 0.0


    # Write the header for a wav file
    # Need to improve by pre-calculating an appropriate length
    def write_wav_header(self, wav_file):
        wav_header = create_wav_header(self.sample_rate, self.bits, 1, 220500000)
        wav_file.write(wav_header)


    # Calculate a point on a sine wave accounting for accumulated phase shift
    def calc_point(self, frequency, amplitude):
        sine = int(amplitude * math.sin(2 * math.pi * (frequency * self.segment_time + self.phase_shift )))
        self.segment_time = self.segment_time + self.sample_length
        return sine


    # Function to write a signal
    # Accumulated error deals with stackup of error that occurs from running this for
    # each pixel and is used to throw in an extra sample when accumulated error exceeds
    # the sample length
    
    def write_signal(self, frequency, duration):
        # calculate the number of samples accounting for accumulated error
        num_samples = duration // self.sample_length
        if self.accumulated_error > self.sample_length:
            additional_samples = self.accumulated_error // self.sample_length
            num_samples += additional_samples
            self.accumulated_error = self.accumulated_error - additional_samples * self.sample_length
        
        # create byte array, calculate samples, and write samples
        samples = bytearray(int(num_samples) * self.sample_size_in_bytes)
        for i in range (0, num_samples):
            sample = self.calc_point(frequency, 16000)
            struct.pack_into(self.format, samples, i * 2, sample)
        self.target.write(samples)
        
        # calculate new accumulated error
        self.accumulated_error = self.accumulated_error + (duration - self.sample_length * num_samples)
 
        # save phase shift point and reset segment_time
        self.phase_shift = math.modf(frequency * self.segment_time + self.phase_shift)[0]
        self.segment_time = 0


    # Brute force vox, header, calibration, and sync
    # Plan to make this more elegant, but it works for now
    def write_vox(self):
        # Vox
        print("Writing vox")
        self.write_signal(1900, 0.100);
        self.write_signal(1500, 0.100);
        self.write_signal(1900, 0.100);
        self.write_signal(1500, 0.100);
        self.write_signal(2300, 0.100);
        self.write_signal(1500, 0.100);
        self.write_signal(2300, 0.100);
        self.write_signal(1500, 0.100);

    def write_calibration_header(self):
        # Calibration
        print("Writing header")
        self.write_signal(1900, .300)
        self.write_signal(1200, .010)
        self.write_signal(1900, .300)

    def write_vis(self):
        # VIS
        print("Writing vis")
        self.write_signal(1200, .030)
        self.write_signal(1300, .030)
        self.write_signal(1300, .030)
        self.write_signal(1100, .030)
        self.write_signal(1100, .030)
        self.write_signal(1100, .030)
        self.write_signal(1100, .030)
        self.write_signal(1300, .030)
        self.write_signal(1300, .030)
        self.write_signal(1200, .030)
        
        # sync pulse
        self.write_signal(1200, .009)

    def write_line(self, width, f):
                red = []
                blue = []
                green = []
                for line in range(0,width):
                    pixel = f.read(2)
                    r, b, g = color565toRGB(pixel)
                    red.append(r)
                    blue.append(b)
                    green.append(g)
                # Black reference tone for 1.5 ms
                self.write_signal(1500, 0.0015)

                # Green component: 138.240 ms
                for pixel in green:
                    self.write_signal(1500 + (pixel*3.1372549), 0.000432)

                # Black reference tone for 1.5 ms
                self.write_signal(1500, 0.0015)

                # Blue component: 138.240 ms
                for pixel in blue:
                    self.write_signal(1500 + (pixel*3.1372549), 0.000432)

                # Horizontal sync for 9.0 ms
                self.write_signal(1200, 0.009)

                # Black reference tone for 1.5 ms
                self.write_signal(1500, 0.0015)

                # Red component: 138.240 ms
                for pixel in red:
                    self.write_signal(1500 + (pixel*3.1372549), 0.000432)
        




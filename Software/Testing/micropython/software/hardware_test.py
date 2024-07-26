import os
from time import sleep
from ili9341 import color565
from machine import Pin, I2S, SPI
from setup import display, sd_state, rotary_enc, neopixels, button, unispace
if sd_state is True:
    from setup import sd_spi, sd
    from sdcard import SDCard
from wav_utils import create_wav_header  


def screen_test(sleep_time):
    # Display white
    sleep(sleep_time)
    display.clear(color=65535)
    # Display red
    display.clear(color=63488)
    sleep(sleep_time)
    # Display green
    display.clear(color=2016)
    sleep(sleep_time)
    # Display blue
    display.clear(color=31)
    sleep(sleep_time)
    display.clear()


def led_test(sleep_time):
    display.clear()
    display.draw_text(0, 0, 'LED Test', unispace,
        color565(255, 255, 255))
    for value in range(0, 18):
        neopixels[value] = [100, 100, 100]
    neopixels.write()
    sleep(sleep_time)
    for value in range(0, 18):
        neopixels[value] = [0, 0, 0]
    neopixels.write()
    sleep(sleep_time)
    for value in range(0, 18):
        neopixels[value] = [100, 0, 0]
    neopixels.write()
    sleep(sleep_time)
    for value in range(0, 18):
        neopixels[value] = [0, 100, 0]
    neopixels.write()
    sleep(sleep_time)
    for value in range(0, 18):
        neopixels[value] = [0, 0, 100]
    neopixels.write()
    sleep(sleep_time)
    for value in range(0, 18):
        neopixels[value] = [0, 0, 0]
    neopixels.write()



def mic_test():
    display.clear()
    display.draw_text(0, 0, 'Mic Test: Recording', unispace,
        color565(255, 255, 255))
    # Record Audio Test
    #--------------------------------------------------------------------------------------------
    # ======= I2S CONFIGURATION =======
    SCK_PIN = 0
    WS_PIN = 1
    SD_PIN = 3
    I2S_ID = 0
    BUFFER_LENGTH_IN_BYTES = 60000  # larger buffer to accommodate slow SD card driver
    # ======= I2S CONFIGURATION =======


    # ======= AUDIO CONFIGURATION =======
    WAV_FILE = "mic.wav"
    RECORD_TIME_IN_SECONDS = 5
    WAV_SAMPLE_SIZE_IN_BITS = 16
    FORMAT = I2S.MONO
    SAMPLE_RATE_IN_HZ = 44100
    # ======= AUDIO CONFIGURATION =======

    format_to_channels = {I2S.MONO: 1, I2S.STEREO: 2}
    NUM_CHANNELS = format_to_channels[FORMAT]
    WAV_SAMPLE_SIZE_IN_BYTES = WAV_SAMPLE_SIZE_IN_BITS // 8
    RECORDING_SIZE_IN_BYTES = (
        RECORD_TIME_IN_SECONDS * SAMPLE_RATE_IN_HZ * WAV_SAMPLE_SIZE_IN_BYTES * NUM_CHANNELS
    )


    wav = open("/sd/{}".format(WAV_FILE), "wb")

    # create header for WAV file and write to SD card
    wav_header = create_wav_header(
        SAMPLE_RATE_IN_HZ,
        WAV_SAMPLE_SIZE_IN_BITS,
        NUM_CHANNELS,
        SAMPLE_RATE_IN_HZ * RECORD_TIME_IN_SECONDS,
    )
    num_bytes_written = wav.write(wav_header)

    audio_in = I2S(
        I2S_ID,
        sck=Pin(SCK_PIN),
        ws=Pin(WS_PIN),
        sd=Pin(SD_PIN),
        mode=I2S.RX,
        bits=WAV_SAMPLE_SIZE_IN_BITS,
        format=FORMAT,
        rate=SAMPLE_RATE_IN_HZ,
        ibuf=BUFFER_LENGTH_IN_BYTES,
    )

    # allocate sample arrays
    # memoryview used to reduce heap allocation in while loop
    mic_samples = bytearray(10000)
    mic_samples_mv = memoryview(mic_samples)

    num_sample_bytes_written_to_wav = 0

    print("Recording size: {} bytes".format(RECORDING_SIZE_IN_BYTES))
    print("==========  START RECORDING ==========")

    while num_sample_bytes_written_to_wav < RECORDING_SIZE_IN_BYTES:
        # read a block of samples from the I2S microphone
        num_bytes_read_from_mic = audio_in.readinto(mic_samples_mv)
        if num_bytes_read_from_mic > 0:
            num_bytes_to_write = min(
                num_bytes_read_from_mic, RECORDING_SIZE_IN_BYTES - num_sample_bytes_written_to_wav
            )
            # write samples to WAV file
            I2S.shift(buf = mic_samples_mv, bits = 16, shift = 4)
            num_bytes_written = wav.write(mic_samples_mv[:num_bytes_to_write])
            num_sample_bytes_written_to_wav += num_bytes_written

    print("==========  DONE RECORDING ==========")
    wav.close()
    audio_in.deinit()


def speaker_test():
    display.clear()
    display.draw_text(0, 0, 'Speaker Test', unispace,
        color565(255, 255, 255))
    # ======= I2S CONFIGURATION =======
    SCK_PIN = 0
    WS_PIN = 1
    SD_PIN = 2
    I2S_ID = 0
    BUFFER_LENGTH_IN_BYTES = 40000
    # ======= I2S CONFIGURATION =======

 
    # ======= AUDIO CONFIGURATION =======
    WAV_FILE = "mic.wav" 
    WAV_SAMPLE_SIZE_IN_BITS = 16
    FORMAT = I2S.MONO
    SAMPLE_RATE_IN_HZ = 44100
    # ======= AUDIO CONFIGURATION =======

    audio_out = I2S(
        I2S_ID,
        sck=Pin(SCK_PIN),
        ws=Pin(WS_PIN),
        sd=Pin(SD_PIN),
        mode=I2S.TX,
        bits=WAV_SAMPLE_SIZE_IN_BITS,
        format=FORMAT,
        rate=SAMPLE_RATE_IN_HZ,
        ibuf=BUFFER_LENGTH_IN_BYTES,
    )

    wav = open("/sd/{}".format(WAV_FILE), "rb")
    _ = wav.seek(44)  # advance to first byte of Data section in WAV file

    # allocate sample array
    # memoryview used to reduce heap allocation
    wav_samples = bytearray(10000)
    wav_samples_mv = memoryview(wav_samples)

    # continuously read audio samples from the WAV file
    # and write them to an I2S DAC
    print("==========  START PLAYBACK ==========")
    num_read = 0
    
    while True:
        num_read = wav.readinto(wav_samples_mv)
        # end of WAV file?
        if num_read == 0:
            # end-of-file, advance to first byte of Data section
            break
            #num_read = wav.seek(44)
        else:
            num_read += audio_out.write(wav_samples_mv[:num_read])


    # cleanup
    wav.close()
    audio_out.deinit()
    print("Done")
    
    
# Run tests
screen_test(1)
led_test(1)
mic_test()
speaker_test()

display.clear()
display.draw_text(0, 0, 'Test Complete', unispace,
    color565(255, 255, 255))
# cleanup
os.umount("/sd")
sd_spi.deinit()
print('Test Complete')
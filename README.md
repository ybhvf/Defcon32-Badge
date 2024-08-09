```
 ______      _____
|__  (_) __ |_   _| __ ___  _ __
  / /| |/ _` || || '__/ _ \| '_ \
 / /_| | (_| || || | | (_) | | | |
/____|_|\__,_||_||_|  \___/|_| |_|
----------------------------------
D C Z I A  --------------  2 0 2 4
```

# About
Introducing the 2024 DCZia Badge - The Ziatron
1.9" of full-color LCD goodness. One knob to rule them all. A mic, _and_ a speaker! Full color dye sub panel art. Up to 18 full color LEDs! Software that does stuff, and or things*!

\* please note things may not be avaliable in all markerts, subject to avalibility, not valid in New Jersey, may contain traces of nuts, please consult your doctor before using any DCZia product.

# Specs
LCD Screen

Raspberry Pi Pico W, now with added WiFi!

One rotary encoder, with click function. Spared no expsense!

Micro Mechanical Microphone, by TDK!

0.3"? Speaker!

Powered by not one, not two, but three, _three_ AAA batteries! Endless Power! (\* please note power is not infact endless.)


# Build Guide
If you need to teardown the badge, please see the full BuildGuide.md in the repo. For defcon badges, you will need to add the rotary encoder, battery pack, and flash the firmware.

First put the rotary encoder through the hole on the front of they board. Solder on all the pins and stabilization tabs on the back of the board. Then remove the double sticky tape and secure the battery pack to the board. Next solder the black wire of the battery pack to the negative pad on the back of the board, and the red to the positive.

If you start up the badge with the shipped firmware you should get a test mode to see if everything works. To flash our initial full fimrware, use a non conductive tool to push the white button on the board of the Raspberry pi Pico, and plug it into your computer. A USB Mass storage device should appear. Download the single u2f file from the release section of our github, and drag it onto the drive. The board should then reboot when the transfer is done and you should have a badge!

The initial firmware has a mode with light patterns, a sound reactive "rave" light mode (the knob will control the sensitivity of the microphone), and can show raw formatted images off a SD card. We wanted to implement a SSTV encode and decode, but did not finish in time for con. If you wish to hack on this and submit a PR go for it! 

# Recommended IDEs
A commodore 64 with a serial to micro USB adapter. If not avaliable, we recommend Visual Studio Code with the MicroPico extension, or the Thonny IDE.

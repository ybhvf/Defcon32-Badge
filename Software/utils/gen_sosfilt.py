#!/usr/bin/env python3
import numpy as np
from scipy.signal import butter, buttord, sosfilt_zi

RATE = 32000

# b_ord, b_wn = buttord([1100, 2300], [1000, 2400], 3, 4, fs=RATE)
b_ord, b_wn = buttord([1100, 2300], [1000, 2400], 3, 5, fs=RATE)
filt = butter(b_ord, b_wn, fs=RATE, output='sos', btype='bandpass')
zi = sosfilt_zi(filt)

# filt = scipy.signal.iirfilter(1, [1100, 2300], fs=32000, output='sos')
# zi = []

# def py2c(string):
#     return (repr(string)
#             .replace('[','{')
#             .replace(']','}')
#             .replace('array(','')
#             .replace(', dtype=int16)',''))

with np.printoptions(floatmode='maxprec'):
    print('filt =', repr(filt))
    print('zi =', repr(zi))

#!/usr/bin/env python3
import numpy as np
from scipy.signal import butter, buttord, sosfilt_zi

RATE = 32000

b_ord, b_wn = buttord([1100, 2300], [1000, 2400], 3, 4, fs=RATE)
# b_ord, b_wn = buttord([1100, 2300], [1000, 2400], 5, 10, fs=RATE)
filt = butter(b_ord, b_wn, fs=RATE, output='sos', btype='bandpass')
zi = sosfilt_zi(filt)

scale = 1 << 14
filt *= scale

filt = filt.astype(np.int16)
zi = zi.astype(np.int16)

# def py2c(string):
#     return (repr(string)
#             .replace('[','{')
#             .replace(']','}')
#             .replace('array(','')
#             .replace(', dtype=int16)',''))

with np.printoptions(floatmode='maxprec'):
    print('filt =', repr(filt))
    print('zi =', repr(zi))

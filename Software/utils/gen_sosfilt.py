#!/usr/bin/env python3
import numpy as np
from scipy.signal import butter, buttord, sosfilt_zi

RATE = 32000

b_ord, b_wn = buttord([1100, 2300], [1000, 2400], 5, 10, fs=RATE)
filt = butter(b_ord, b_wn, fs=RATE, output='sos', btype='bandpass')
zi = sosfilt_zi(filt)

with np.printoptions(floatmode='unique'):
    print('filt =', repr(filt))
    print('zi =', repr(zi))

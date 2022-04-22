import numpy as np
import pyxdf
import matplotlib.pyplot as plt
from scipy import signal, fftpack

data, header=  pyxdf.load_xdf('P01-with-tacs-R1.xdf')
print(data[0]['info'])
for stream in data:
    y = stream['time_series']

    if isinstance(y, list):
        # list of strings, draw one vertical line for each marker
        for timestamp, marker in zip(stream['time_stamps'], y):
            plt.axvline(x=timestamp)
            print(f'Marker "{marker[0]}" @ {timestamp:.2f}s')
    elif isinstance(y, np.ndarray):
        # numeric data, draw as lines
        plt.figure(figsize=(13,8))
        plt.plot(stream['time_stamps'][:], y[:])
        plt.show()
    else:
        raise RuntimeError('Unknown stream format')


fieldline_data = data[0]['time_series']
stim_adc = fieldline_data[:, 11]
plt.figure(figsize=(13,8))
plt.plot(stim_adc)
plt.show()
# import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
import time
from scipy import signal

sfreq = 1000

target_freq = 10 # 10hz
carrier_freq = 200 # 40hz

amplitude = 2
duration = 10 # 10 s
t_samples = np.arange(duration*sfreq)
carrier = np.sin(2 * np.pi * carrier_freq * t_samples/sfreq) * amplitude
modulator = np.sin(2 * np.pi * target_freq * t_samples/sfreq) 
# am_stim = amplitude * 0.5 * (carrier * modulator / 2 ) #1mA p2p
am_stim = (amplitude + modulator * amplitude) * carrier /2 #100 % modulation index
# am_stim = (amplitude + modulator * amplitude*100)  #90 % modulation index




plt.figure()
plt.plot(am_stim[:1000])
plt.show()

plt.figure()
f, pxx = signal.welch(am_stim, sfreq, nperseg=sfreq)
plt.plot(f, pxx)
plt.xlim(0, 230)
plt.show()

# plt.figure()
# sp = np.fft.fft(am_stim)
# trange = np.linspace(0, sfreq, len(am_stim))
# plt.plot(trange, np.abs(sp))
# plt.xlim(0,80)
# plt.show()



# output = np.vstack((am_stim+2.5, am_stim))
# task = nidaqmx.Task()
# task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao0')  # note: tACS
# task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao1')  # note: tACS

# task.timing.cfg_samp_clk_timing(rate=sfreq, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=len(am_stim))
# task.write(output)
# task.start()

# time.sleep(30)



# task.close()


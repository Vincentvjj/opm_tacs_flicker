import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
import time

sfreq = 24000

target_freq = 10 # 10hz
carrier_freq = 40 # 40hz

amplitude = 1
duration = 30 # 10 s
t_samples = np.arange(duration*sfreq)
carrier = np.sin(2 * np.pi * carrier_freq * t_samples/sfreq)
modulator = np.sin(2 * np.pi * target_freq * t_samples/sfreq)
# env = amplitude * (0.5 + 1 *  modulator)
am_stim = amplitude * 0.5 * (carrier * (modulator / 2))
# am_stim = env * carrier


# plt.figure()
# plt.plot(am_stim)
# plt.show()


output = np.vstack((am_stim+2.5, am_stim))
task = nidaqmx.Task()
task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao0')  # note: tACS
task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao1')  # note: tACS

task.timing.cfg_samp_clk_timing(rate=sfreq, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=len(am_stim))
task.write(output)
task.start()

time.sleep(30)



task.close()


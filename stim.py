import numpy as np
from numpy.random import permutation
from psychopy import visual, event, core
from platform import system
import nidaqmx
import serial
import random
from scipy.signal import find_peaks
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.stats import zscore

# TO DO
# Add mandatory break
# Different tone sequence

# Set to False for debugging without trigger box and daq card
use_trigger_and_daq_card = False
use_fullscreen = True

### CHANGE PERSONAL DETECTION THRESHOLD HERE ###
jnd = 17


def make_audio(peaks, times, pulse, oddball, sfreq, volume):
    """Generates the audio sequence
    audio_play = To be played to the subject
    audio_trigger = To be sent to the EEG
    given
    peaks = Indices of the peaks
    times = Times in sec of one trial
    pulse = One tone with the standard pitch
    oddball = One tone with the slightly higher pitch
    sfreq = Sampling frequency
    volume = Volume of the played tone sequence"""
    # Initialize the arrays storing the audio tone and triggers
    audio_play = np.zeros_like(times)
    audio_trigger = np.zeros_like(times)
    n_total = len(peaks)
    n_standard = int(n_total * 0.9)
    n_oddball = n_total - n_standard
    mask_oddball = permutation(np.array([0] * n_standard + [1] * n_oddball).astype(bool))
    ix_last = 0
    for ix in range(len(mask_oddball)):
        if mask_oddball[ix]:
            if ix - ix_last < 6:
                mask_oddball[ix] = 0
            ix_last = ix
    lastpeak = 0
    for peak, is_oddball in zip(peaks, mask_oddball):
        # Place the tones at the peaks and make sure that the frequency is not too high
        if peak > lastpeak+sfreq/target_freq*0.5:
            try:
                if is_oddball:
                    audio_play[peak:peak+pulse_duration_samp] = oddball
                    audio_trigger[peak:peak+int(sfreq/12)] = 0.30
                else:
                    audio_play[peak:peak+pulse_duration_samp] = pulse
                    audio_trigger[peak:peak+int(sfreq/12)] = 0.15

                lastpeak = peak
            except:
                continue

    return volume*audio_play, audio_trigger

def send_trigger(trigger):
    ser.write(str.encode(chr(0)))
    ser.write(str.encode(chr(trigger)))
    ser.flush()
    ser.reset_output_buffer()

def quit_and_store():
    core.quit()
event.globalKeys.add(key='escape', func=quit_and_store)


# general settings
system = system()
if use_trigger_and_daq_card:
    ser = serial.Serial('COM11')

# experimental parameters
trial_duration = 20  # seconds
n_trials_per_cond = 10
conds = [1,2,3,4,5,6] # Phase shift conditions
trial_conds = permutation(conds*n_trials_per_cond)  # in_phase, anti_phase
target_freq = 6
pitch = 800  # Hz
sfreq = 24000
samps_trial = sfreq*trial_duration
break_sec = 5

# import data to generate the audio stream and stimulation
envelope = np.load('tones/envelope.npy')
len_env = len(envelope)
times = np.load('tones/times.npy')
times = times[:samps_trial]

# audio: Generate one tone
pulse_duration_sec = 0.028
pulse_duration_samp = int(pulse_duration_sec * sfreq)
pulse_t = np.arange(0, pulse_duration_sec, 1 / sfreq)
win_hanning = np.hanning(len(pulse_t))  # make pulse smooth
pulse = np.sin(2 * np.pi * pitch * pulse_t) * win_hanning
oddball = np.sin(2 * np.pi * (pitch + jnd) * pulse_t) * win_hanning # Odball with slightly higher pitch
volume = 0.05

# tACS
amplitude = 1
carrier = np.sin(2 * np.pi * 40 * times)

# presentation parameters
win = visual.Window(allowGUI=True, monitor='testMonitor', fullscr=use_fullscreen,
                    units='deg', color="black", waitBlanking=False)
fixation = visual.TextStim(win, text='+', color="white", height=10)
rest = visual.TextStim(win, text='rest\n\nHit any key to start', color="white", height=10)

### experiment ###
# Loop through the trials which have a specific condition
for trial_ix,cond in enumerate(trial_conds):
    # Get a trial-long section of the envelope
    i = random.randint(0,len_env-samps_trial)  # start index
    envelope_tmp = envelope[i:i+samps_trial]
    # Generate the stimulation signal
    am_stim = amplitude * 0.5 * (carrier * (envelope_tmp + 1) / 2)
    # am_stim = 0.5*envelope_tmp
    # Shift the stimulation signal according to the condition
    n_roll = int(((cond - 1) / len(conds)) * sfreq/6)
    am_stim = np.roll(am_stim, n_roll)
    # Extract the peaks
    peaks = find_peaks(envelope_tmp)[0]
    # Generate a sequence of tones centered on the peaks
    audio_play, audio_trigger = make_audio(peaks, times, pulse, oddball, sfreq, volume)
    # Stack the signals that will be send to the DAQ card
    output = np.vstack((audio_play, audio_trigger, am_stim))
    sd.play(audio_play, samplerate=24000)
    sd.wait()

    # Wait for the subject to start the trial
    rest.text = 'Trial {:d}/{:d}'.format(trial_ix+1,len(trial_conds))
    rest.draw()
    win.flip()
    core.wait(1)
    fixation.draw()
    win.flip()

    if use_trigger_and_daq_card:
        # Send the condition trigger
        send_trigger(cond)

        # Send the audio sequence and stimulation to the DAQ card
        task = nidaqmx.Task()
        task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao1')  # note: audio_play
        task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao5')  # note: audio_trigger
        task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao4')  # note: tACS
        task.timing.cfg_samp_clk_timing(rate=sfreq, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=len(am_stim))
        task.write(output)
        task.start()

    # Get the task response
    timer = core.CountdownTimer(trial_duration)
    while timer.getTime() > 0:
        event.clearEvents()
        core.wait(0.1)
        keys = event.getKeys(['space'])
        if 'space' in keys:
            if use_trigger_and_daq_card:
                send_trigger(8)
            print('space')

    # Mandatory break
    for r in range(break_sec):
        rest_time = break_sec - r
        rest.text = rest_time
        rest.draw()
        win.flip()
        core.wait(1)
        r = r + 1
    rest.text = "Hit any key to start"

    if use_trigger_and_daq_card:
        task.close()

win.close()
print('done')
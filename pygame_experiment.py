# Main experiment module that deals with experiment flow, visual cues, LSL, and recording


from turtle import delay
import numpy as np 
from datetime import datetime
import time
import sys 
from random import randrange, randint

# visual stuff
import pygame
from pygame.locals import *

# LSL for recroding 
from pylsl import StreamOutlet, StreamInfo, local_clock

# stimulation 
import nidaqmx 

########## Exerpiment flow paramters ######## 
flicker_dur = 2000 # 2 seconds
num_trials_total = 20
total_time = flicker_dur * num_trials_total # ~30 seconds + ITI

flicker_freq = 10 # SSVEP for 10Hz
num_flick_total_trial = int(flicker_freq * (flicker_dur/1000)) # how many times it should flicker during each trial

with_stimulation = True # turn to True for stimulation 

print("Total run time without ITI: ~", total_time)

######### Pygame parameters ##############

pygame.init()
 
fps = 10 ## refresh rate. 
fpsClock = pygame.time.Clock()
 
screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
# screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_w, screen_h = pygame.display.get_surface().get_size()



######### stimulation parameter
sfreq = 24000

target_freq = 10 # 10hz
carrier_freq = 40 # 40hz

amplitude = 1 #final resulting current in stimulator in mA p2p (+- amplitude/2 mA)
duration = int(total_time/1000) + 100 
print(duration)
t_samples = np.arange(duration*sfreq)
carrier = np.sin(2 * np.pi * carrier_freq * t_samples/sfreq)
modulator = np.sin(2 * np.pi * target_freq * t_samples/sfreq)
am_stim = amplitude * 0.5 * (carrier * modulator / 2 ) #1mA p2p
output = np.vstack((am_stim+2.5, am_stim)) #first output to the adc chassis must be positive voltage, so offset 2.5V
if with_stimulation: 
    task = nidaqmx.Task()
    task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao0')  # note: Analog signal chassis
    task.ao_channels.add_ao_voltage_chan('cDAQ1Mod1/ao1')  # note: tACS
    task.timing.cfg_samp_clk_timing(rate=sfreq, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=len(am_stim))
    task.write(output)
    



########## Setup LSL streams ###########
# Sets up another LSL stream and these can be recorded with Labrecorder
marker_id_start = [7]
marker_id_end = [9]
marker_id_blink_on = [2]
marker_id_blink_off = [1]
stream_name = "ExperimentMarkers"

lsl_stream_info = StreamInfo(
    stream_name,
    'Markers',
    1,
    0, # irregular sampling rate? 
    'int32',
    stream_name + str(randint(100000, 999999))
    )

lsl_outlet = StreamOutlet(lsl_stream_info)


########### ###############
display = True
run_experiment = False
num_flick = 0
num_trial = 0
iti_delaying = False
delaying = 1

#draw intro text
screen.fill((128, 128, 128))
font = pygame.font.Font(None, 50)
text = font.render("Welcome to the experiment. Please wait until the experiment starts!", True, (255,255,255))
text_rect = text.get_rect(center=( int(screen_w/2), int(screen_h/2)))
screen.blit(text, text_rect)

## draw fixation cross 
start_pos_h = (int(screen_w/2) - 50, int(screen_h/2))
end_pos_h = (int(screen_w/2) + 50, int(screen_h/2))
start_pos_v = (int(screen_w/2), int(screen_h/2) - 50)
end_pos_v = (int(screen_w/2), int(screen_h/2) + 50)
def draw_fixation_cross(): 
    pygame.draw.line(screen, (255,0,0), start_pos_h, end_pos_h)
    pygame.draw.line(screen, (255,0,0), start_pos_v, end_pos_v)



# Game loop.
while True:
    # quit condition
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if with_stimulation:
                task.close() # closes/stops stimulation
            pygame.quit()
            sys.exit()

    # starting the experiment run with space bar
    if not run_experiment:
        ## wait for a keypress ('Space') to start the experiment
        event = pygame.event.wait() 
        if event.type == pygame.KEYDOWN and event.key==pygame.K_SPACE:
            print("Experiment starts!")
            # print(datetime.now().strftime("%H:%M:%S.%f")) # print timestamps
            lsl_outlet.push_sample(marker_id_start, local_clock())
            if with_stimulation:
                task.start()

            screen.blit(text, text_rect)
            run_experiment = True

    # controlling the experiment flow
    else:
        # Run finishes
        if num_trial > num_trials_total:
            #ends the experiment
            # print(datetime.now().strftime("%H:%M:%S.%f")) # print timestamps
            lsl_outlet.push_sample(marker_id_end, local_clock())
            if with_stimulation:
                task.close()
            run_experiment = False
            
            pygame.quit()
            sys.exit()

        # Introduce intertrial delay 
        if num_flick  == num_flick_total_trial: 
            # add some random ITI 
            iti = randrange(400, 900, 1)/1000  #500ms to 1000ms, but since before this line is called there is already 100ms delay from fps
            print("random iti ", iti + 0.1)
            num_flick = 0
            iti_delaying = False
            time_bef = local_clock()
            time_now = local_clock()
            while(time_now - time_bef < iti):
                time_now = local_clock()
            

        ## Blinking mechansim

        # if it's not in intertrial, do the blinking
        if not iti_delaying:

            # print('blink blink')
            # print(datetime.now().strftime("%H:%M:%S.%f")) # print timestamps
            timestamp = local_clock()

            if display:
                lsl_outlet.push_sample(marker_id_blink_off, timestamp)
                screen.fill((0, 0, 0))
                draw_fixation_cross()
            else:
                lsl_outlet.push_sample(marker_id_blink_on, timestamp)
                screen.fill((255, 255, 255))
                draw_fixation_cross()

            num_flick += 1

            if num_flick == num_flick_total_trial:
                num_trial += 1

            display = not display
            fpsClock.tick()

        # # If it's in intertrial, don't do anything 
        # else: 
        #     # Count how many more to let this loop pass
        #     # Since pygame runs at 10hz, 500ms delay will equal to 5 empty loops.

        #     # print("delaying ", delaying )
        #     # print(datetime.now().strftime("%H:%M:%S.%f")) # print timestamps
        #     if delaying == iti-1: 
        #         iti_delaying = False
        #         delaying = 1
        #     else:
        #         delaying +=1
           
    # updates
    pygame.display.flip()
    fpsClock.tick(fps)



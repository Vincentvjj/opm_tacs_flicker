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
num_trials_total = 5 #20 usually
total_time = flicker_dur * num_trials_total # ~30 seconds + ITI

flicker_freq = 10 # SSVEP for 10Hz

# how many times it should flicker during each trial. Times two, for on and off
num_flick_total_trial = int(flicker_freq * (flicker_dur/1000)) 


with_stimulation = False # turn to True for stimulation 

print("Total run time without ITI: ~", total_time)

######### Pygame parameters ##############

pygame.init()

# full cycle of on and off will be 100ms (for 10hz), so for each on and off we need 50ms (20hz)
fps = int(flicker_freq*2)

fpsClock = pygame.time.Clock()
 
screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
# screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_w, screen_h = pygame.display.get_surface().get_size()



######### stimulation parameter
sfreq = 24000

target_freq = 10 # 10hz
carrier_freq = 220 # 220hz

amplitude = 0.5 #V p2p, +-0.25v, and tACS will multiply 2 to current, so 1mA p2p
duration = int(total_time/1000) + 100 

t_samples = np.arange(duration*sfreq)
carrier = np.sin(2 * np.pi * carrier_freq * t_samples/sfreq) * amplitude
modulator = np.sin(2 * np.pi * target_freq * t_samples/sfreq)
am_stim = (amplitude + modulator * amplitude) * carrier /2 # 100% modulation depth

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
marker_id_trial_start = [1]
marker_id_trial_end = [2]
# I don't think we need to have the blink on and off marker.. I think a marker for trial start and end is nicer. 
# marker_id_blink_on = [2]
# marker_id_blink_off = [1]
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
display = False
run_experiment = False
num_flick = 0
num_trial = 1
iti_delaying = False

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
            timestamp = local_clock()

           
            lsl_outlet.push_sample(marker_id_trial_end, timestamp)
            # add some random ITI 
            iti = randrange(450, 451, 1)/1000  #500ms to 1000ms, but since before this line is called there is already 50ms delay from fps
            print("random iti ", iti + 0.05)
            num_flick = 0
            iti_delaying = False
            time_bef = local_clock()
            time_now = local_clock()
            while(time_now - time_bef < iti):
                time_now = local_clock()
            
            

        ## Blinking mechansim

        # if it's not in intertrial, do the blinking

        if not iti_delaying:
            timestamp = local_clock()

            

            # print('blink blink')
            # print(datetime.now().strftime("%H:%M:%S.%f")) # print timestamps

            if display:
                # print('off')
                # lsl_outlet.push_sample(marker_id_blink_off, timestamp)
                screen.fill((0, 0, 0))
                draw_fixation_cross()
                num_flick += 1 #full cycle
                if num_flick  == num_flick_total_trial: 
                    # a trial ended
                    print('trial ends')
                    print(datetime.now().strftime("%H:%M:%S.%f")) # print timestamps

            else:
                # a trial starts
                if num_flick == 0:
                    print('trial starts')
                    print(datetime.now().strftime("%H:%M:%S.%f")) # print timestamps
                    lsl_outlet.push_sample(marker_id_trial_start, timestamp)
                # print('on')
                # lsl_outlet.push_sample(marker_id_blink_on, timestamp)
                screen.fill((255, 255, 255))
                draw_fixation_cross()


            if num_flick == num_flick_total_trial:
                num_trial += 1

            display = not display
            fpsClock.tick()

           
    # updates
    pygame.display.flip()
    fpsClock.tick(fps)



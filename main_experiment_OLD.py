# Main experiment module that deals with experiment flow, visual cues, LSL, and recording

from socket import timeout
import numpy as np 
import time
import sys 
from random import randrange

# visual stuff
import PyQt5 as Qt
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, QRect
from PyQt5.QtGui import QPainter, QPen, QPalette

# LSL for recroding 
from pylsl import StreamInlet, StreamOutlet, StreamInfo, resolve_byprop



########## Exerpiment flow paramters ######## 
flicker_dur = 2000 # 2 seconds
num_trials = 10
total_time = flicker_dur * num_trials # ~30 seconds + ITI

flicker_freq = 10 # SSVEP for 10Hz
num_flick_total_trial = int(flicker_freq * (flicker_dur/1000)) # how many times it should flicker during each trial

frameless = False # Make True during experiment

print("Total run time without ITI: ~", total_time)

######### Drawing experiment paradigm ##############

class FlickerExp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flicker experiment")
        layout = QVBoxLayout(self)

        ### intro label ###
        self.label_intro = QLabel("Welcome to the experiment \n Please wait until the experiment starts", self)
        self.label_intro.setStyleSheet('font-size: 40px;')
        self.label_intro.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label_intro)

        ### draw a fixation cross
        rect = QRect(51, 122, 131, 185)



        if frameless: 
            self.showFullScreen() 
        else:
            self.showMaximized()


        ### wait for keyboard  ###
        input("Press any key when participant is ready")

        ## remove label and start flicker
        self.label_intro.clear()

        self.run_flicker()

    # ## overloading paint event method when QWdiget is drawn
    def paintEvent(self, event):
       

        # self.setStyleSheet('background-color: white')

        painter = QPainter(self)
        
        painter.setRenderHint(QPainter.Antialiasing)
        # painter.begin(self)
        painter.setPen(QtCore.Qt.red)
        painter.drawLine(200, 100, 10, 100)



    def run_flicker(self):
        print("Run starts")
        print(time.strftime("%H:%M:%S", time.localtime()))
        # TODO: Send LSL marker run starts

        self.trial_counter = 1
        self.flicker_counter = 1
        self.flag = True

        self.interval = int(1000 / flicker_freq) #1 second / freq

        QTimer.singleShot(0, self.flicker)


    def flicker(self):  

        if self.trial_counter > num_trials:
            print("Run ends")
            print(time.strftime("%H:%M:%S", time.localtime()))
            # TODO: Send LSL marker run ends
            return #ends the run
        if self.flicker_counter == num_flick_total_trial:
            
            # add some random ITI 
            iti = (randrange(6) + 5) * 100 #500ms to 1000ms
            print("random iti ", iti)
            self.flicker_counter = 1
            self.trial_counter += 1
            QTimer.singleShot(iti, self.flicker)
        else: 

            ## visual flickering changes 
            # TODO: Send LSL marker for "stimulation (1 and 0) - white:1 and black:0?"

            if self.flag: 
                self.setStyleSheet('background-color: black')
            else: 
                self.setStyleSheet('background-color: white')
            self.flag = not self.flag
            self.flicker_counter += 1
            QTimer.singleShot(self.interval, self.flicker)
    


app = QApplication([])

window = QWidget()
exp = FlickerExp()

sys.exit(app.exec())

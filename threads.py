# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 17:29:54 2019

@author: Amin Saberi
"""

import os, sys
from PyQt5 import QtCore
from playsound import playsound
import time

def resource_path(relative_path):
    """
    Needed for PyInstaller to find the audio files
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class PlayNumbersThread(QtCore.QThread):
    """
    When "Start" is clicked, this QThread class runs a thread
    simultaneous to the main program. The only argument for this
    class is a NUMBERS_PER_TRIAL length list of random numbers 
    from 1 to 10, which has been constructed in Window.__init__.
    The main objective of this class is to play the sound of each
    number, wait for INTERVAL seconds, and do the same for all the
    numbers in random_numbers list.
    """
    # Define the event of playing a new_number, which will
    # emit two variables: the number played and the time it was played
    # (which is used to claculate reaction time)
    new_number = QtCore.pyqtSignal(int, float)
    finished = QtCore.pyqtSignal()
    def __init__(self, random_numbers, interval, language, parent=None):
        """
        Initializes the PlayNumbersThread with random_numbers (list), interval (int)
        and language ("en"/"fa") as its arguments 
        """
        super().__init__()
        self.random_numbers = random_numbers
        self.language = language
        self.interval = interval
        self.paused = False
    def run(self):
        """
        Overwrites QThread.run function which executes the thread. It loops
        through the random_numbers list, tells Window._start about the number
        that is playing and the time it was played, plays the sound of each number 
        , (using playsound package, TODO: Use QSound), waits for 3 seconds 
        (after adjusting for the length of the sound played) and then does 
        the same for the next number on the list.
        """
        for number in self.random_numbers:
            # Record the time that number has started playing, to calculate
            # its length, and also to calculate reaction time
            time_before_playsound = time.time()
            self.new_number.emit(number, time_before_playsound)
            playsound(resource_path(os.path.join("audio", self.language, "{:d}.wav".format(number))))
            length = time.time() - time_before_playsound
            for i in range(round(100*(self.interval-length))):
                while self.paused:
                    pass
                time.sleep(0.01)
           
        self.stop()
    
    def stop(self):
        # This 0 serves as a right-padding and is necessary for the last interval
        # to be calculated when the input is via keyboard 
        self.new_number.emit(0, time.time())
        self.finished.emit()
        self.terminate()

class PlayDemoThread(QtCore.QThread):
    """
    When "Start" is clicked, this QThread class runs a thread
    simultaneous to the main program. The only argument for this
    class is a NUMBERS_PER_TRIAL length list of random numbers 
    from 1 to 10, which has been constructed in Window.__init__.
    The main objective of this class is to play the sound of each
    number, wait for INTERVAL seconds, and do the same for all the
    numbers in random_numbers list.
    """
    # Define the event of playing a new_number, which will
    # emit two variables: the number played and the time it was played
    # (which is used to claculate reaction time)
    new_pair = QtCore.pyqtSignal(tuple, float)
    finished = QtCore.pyqtSignal()
    def __init__(self, demo_pairs, interval, parent=None):
        """
        Initializes the PlayNumbersThread with random_numbers (list), interval (int)
        and language ("en"/"fa") as its arguments 
        """
        super().__init__()
        self.demo_pairs = demo_pairs
        self.interval = interval
        self.paused = False
    def run(self):
        """
        Overwrites QThread.run function which executes the thread. It loops
        through the random_numbers list, tells Window._start about the number
        that is playing and the time it was played, plays the sound of each number 
        , (using playsound package, TODO: Use QSound), waits for 3 seconds 
        (after adjusting for the length of the sound played) and then does 
        the same for the next number on the list.
        """
        for pair in self.demo_pairs:
            # Record the time that number has started playing, to calculate
            # its length, and also to calculate reaction time
            time_before_playsound = time.time()
            self.new_pair.emit(pair, time_before_playsound)
            for i in range(self.interval*100):
                while self.paused:
                    pass
                time.sleep(0.01)
        # This 0 serves as a right-padding and is necessary for the last interval
        # to be calculated when the input is via keyboard 
        self.stop()

    def stop(self):
        self.new_pair.emit((0,0), time.time())
        self.finished.emit()
        self.terminate()        

            
class TimerThread(QtCore.QThread):
    """
    When "Start" is clicked, this QThread class runs a thread
    simultaneous to the main program. Its only job is to update
    the Window.timer_label via Window._update_timer, and has
    nothing to do with reaction times and dynamics of the program.
    In fact, it has no communication means with PlayNumbersThread.
    QTimer was an alternative, but counting time in a thread is more
    accurate (is it?!).
    """
    # Each 0.1 seconds, TimeThread emits the time_step signal,
    # which carries the total_time passed to be shown on Window.timer_label
    time_step = QtCore.pyqtSignal(float)
    def __init__(self, duration, parent=None):
        """
        Initializes the TimerThread with duration  as its only argument
        """
        super().__init__()
        self.duration = duration

    def run(self):
        """
        Runs the TimerThread. Until reaching the TRIAL_LENGTH, every 0.01 seconds
        sends a signal to Window._start carrying the total time spent. Which is
        then used by Window._update_timer to draw it on the screen.
        """
        total_time = 0
        while total_time <= self.duration-0.1:
            time.sleep(0.1)
            total_time+=0.1
            self.time_step.emit(total_time)
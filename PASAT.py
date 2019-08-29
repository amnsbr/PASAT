# -*- coding: utf-8 -*-
"""
Paced Auditory Serial Addition Test 
with PyQt5 on Python3.7 (developed and tested under Anaconda 2019.7)
Created on Wed Aug 28 15:56:33 2019

@author: Amin Saberi
"""

from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QHBoxLayout,\
 QGroupBox, QVBoxLayout, QLabel, QGridLayout, QWidget, QLineEdit, QMessageBox,\
 QMainWindow, QAction
import sys, os
from PyQt5 import QtGui
from PyQt5 import QtCore
from playsound import playsound
import random, time
import gettext

#TODO: Define sessions, and inside each session record the data in a csv file
#TODO: Measure the first 1/3 and the last 1/3 stats separately
#BUG: There's a delay in showing the numbers on the screen
#TODO: On keyPressEvent, fix the problem with Key_Enter, Key_Q is not user friendly
#TODO: Used globals for the language change, it works but isn't a good practice!

NUMBERS_PER_TRIAL = 3
INTERVAL = 3 #seconds
TRIAL_LENGTH = NUMBERS_PER_TRIAL * INTERVAL #seconds
LANGUAGE = "en"

EXIT_CODE_REBOOT = -123

### Helper Functions ####
def en_to_ar_num(number_str):
    """
    Converts English string numbers to Arabic string numbers
    """
    dic = { 
        '0':'۰', 
        '1':'١', 
        '2':'٢', 
        '3':'۳', 
        '4':'۴', 
        '5':'۵', 
        '6':'۶', 
        '7':'۷', 
        '8':'۸', 
        '9':'۹',
        '.':'.',
    }
    arnum = ''
    for digit in str(number_str):
        arnum += dic[digit]    
    return arnum
def redefine_gettext():
    if LANGUAGE == "fa":
        fa = gettext.translation('PASAT', localedir = 'locale', languages=['fa'])
        fa.install()
        _ = fa.gettext
        _n = en_to_ar_num
    else:
        _ = gettext.gettext
        # if language is not "fa", instead of english to arabic number translator function
        # pass the gettext.gettext as _n, that does nothing.
        _n = gettext.gettext
    return _, _n
_, _n = redefine_gettext()
def non_zero_mean(lst):
    """
    Returns the mean of non-zero numbers of a list
    """
    summation = 0
    count = 0
    for num in lst:
        if num:
            summation += num
            count += 1
    return summation/count
            

### Threads ####
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
    def __init__(self, random_numbers, parent=None):
        """
        Initializes the PlayNumbersThread with random_numbers list as its 
        only argument
        """
        super().__init__()
        self.random_numbers = random_numbers
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
            playsound(os.path.join("audio",LANGUAGE, "{:d}.wav".format(number)))
            length = time.time() - time_before_playsound
            time.sleep(INTERVAL-length)
        self.finished.emit()
            
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
    def run(self):
        """
        Runs the TimerThread. Until reaching the TRIAL_LENGTH, every 0.01 seconds
        sends a signal to Window._start carrying the total time spent. Which is
        then used by Window._update_timer to draw it on the screen.
        """
        total_time = 0
        while total_time <= TRIAL_LENGTH:
            time.sleep(0.1)
            total_time+=0.1
            self.time_step.emit(total_time)
        
#### Main Window ####
class Window(QMainWindow):
    """
    The main Window of the program. See the documentation on each function for
    more detail.
    """
    def __init__(self):
        """
        With the help of InitWindow(), initializes the window and draws the initial
        objects on the screen. Also, random_numbers list are defined here, which will
        be later passed on to PlayNumbersThread via self._start. Also, baseline states
        of the program (answerButton_clicked and current_typed_answer) are initialized
        here, as well as self.played_numbers which will store the numbers that had been
        played so far.
        """
        # Using super() initilize an empty window, and then populate it
        # using self.InitWindow()
        super().__init__()
        self.title = "PASAT"
        self.top = 100 #TODO: Make the coordinates better
        self.left = 100
        self.width = 600
        self.height = 600
        global _, _n
        _, _n = redefine_gettext()

        # Set the title and geometry of the window
        ##self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self._center()

        self.CreateMenu()
        self.InitWindow()
        
        # Create a list of random_numbers with the length of NUMBERS_PER_TRIAL. The range
        # of random numbers is [1, 10], so the possible answers are [2, 20]
        self.random_numbers = []
        for dummy in range(NUMBERS_PER_TRIAL):
            self.random_numbers.append(random.randint(1,10))
        
        self.player_name = ''
        # Initilize answerButton_clicked, so that when during an INTERVAL that
        # a number has been played, user cannot click on more than one answers,
        # and also cannot use keyboard to type the answer
        self.answerButton_clicked = False
        # Initialize allow_answer. Do not allow_answer (inside _on_click_answer and 
        # keyboard handler), until more than one numbers have been presented
        self.allow_answer = False
        # Initialize the current_typed_answer (which is the value for self.answer_label).
        # This will record the typed answer, and is reset after each interval
        # TODO: make it a _ that blips!
        self.current_typed_answer = ''
        # Record if the trial has been started, so clicking start afterwards wouldn't
        # do anything.
        self.trial_started = False
        # Create a list to store the numbers that have been played so far
        self.played_numbers = []
        # Keep track of reaction_times and "C" (correct)/"I" (incorrect)/"N" (not answered)
        self.reaction_times = []
        self.results = []
        # Initialize time_presented. This is not the time_presented for the first
        # number, it's only here to prevent undefined error.
        self.time_presented = time.time()
        
    def _center(self, widget=None):
        if not widget:
            widget = self
        frameGm = widget.frameGeometry()
        screen = App.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = App.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        widget.move(frameGm.topLeft())
 
    def CreateMenu(self):
        mainMenu = self.menuBar()
        sessionMenu = mainMenu.addMenu(_('Session'))
        #runMenu = mainMenu.addMenu(_('Run'))
        optionsMenu = mainMenu.addMenu(_('Options'))
        helpMenu = mainMenu.addMenu(_('Help'))
        
#        newSessionAction = QAction(_('New Session'), self)
#        sessionMenu.addAction(newSessionAction)
#        saveSessionAction = QAction(_('Save Session'), self)
#        sessionMenu.addAction(saveSessionAction)
#        showSessionResultsAction = QAction(_("Show Results"), self)
#        sessionMenu.addAction(showSessionResultsAction)
        exitAction = QAction(_("Exit"), self)
        exitAction.triggered.connect(self._exit)
        sessionMenu.addAction(exitAction)
        
#        startRunAction = QAction(_("Start"), self)
#        runMenu.addAction(startRunAction)
#        stopRunAction = QAction(_("Stop"), self)
#        runMenu.addAction(stopRunAction)
#        pauseRunAction = QAction(_("Pause"), self)
#        runMenu.addAction(pauseRunAction)
        
#        preferencesAction = QAction(_("Preferences"), self)
#        optionsMenu.addAction(preferencesAction)
        languagesMenu = optionsMenu.addMenu(_("Languages"))
        faAction = QAction(_("Farsi"), self)
        if LANGUAGE == "fa":
            faAction.setEnabled(False)
        faAction.triggered.connect(self._change_language)
        languagesMenu.addAction(faAction)
        enAction = QAction(_("English"), self)
        if LANGUAGE == "en":
            enAction.setEnabled(False)
        enAction.triggered.connect(self._change_language)
        languagesMenu.addAction(enAction)
        
        aboutAction = QAction(_("About"), self)
        helpMenu.addAction(aboutAction)
#        helpAction = QAction(_("How it woks"), self)
#        helpMenu.addAction(helpAction)
         
    def InitWindow(self):
        """
        Adds elements to the Window. Inside the Window is the vbox. And each
        row of widgets are added one by one to vbox, including registerForm, number_label,
        timer_label, answerButtons, answer_label and actionButtons. All widgets except
        registerForm are hidden before that the registration is completed. They are .show n
        inside _on_click_register. TODO: There might be a better solution to this.
        """        
        # Initialize the vertical layout container vbox
        self.mainBox = QGroupBox()
        vbox = QVBoxLayout()
        
        self.CreateRegisterForm()
        vbox.addWidget(self.registerForm)
        
        # Add the played number label at the top and aligned at center
        self.number_label = QLabel()
        self.number_label.setAlignment(QtCore.Qt.AlignCenter)
        self.number_label.setFont(QtGui.QFont("Sanserif", 20)) #TODO: Change to Farsi fonts and embedd it to the .exe file
        self.number_label.hide()
        vbox.addWidget(self.number_label)
        
        # Add the timer_label below the played number label TODO: maybe change its position
        self.timer_label = QLabel()
        self.timer_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_label.hide()
        vbox.addWidget(self.timer_label)
        
        # Add the answerButtons which are QPushButtons from [1 to 20], and
        # serve as one way of entering the answer
        self.CreateAnswerButtons()
        self.answerButtons.hide()
        vbox.addWidget(self.answerButtons)
        
        # Add the answer_label which prints the self.current_typed_answer
        # and serves as another way of entering the answer. Could've used text-input,
        # but this seems more suitable for my purpose.
        self.answer_label = QLabel()
        self.answer_label.setAlignment(QtCore.Qt.AlignCenter)
        self.answer_label.hide()
        ##self.answer_label.setFont(QtGui.QFont("Sanserif", 20))
        vbox.addWidget(self.answer_label)

        # Add the Start and Exit buttons TODO: Move exit and other functionalities to Menubar
        self.CreateActionButtons()
        self.actionButtons.hide()
        vbox.addWidget(self.actionButtons)

        # Assign vbox as the primary layout of the Window (and parent to all other
        # widgets and groups of widgets)
        self.mainBox.setLayout(vbox)
        self.setCentralWidget(self.mainBox)
        
        # Display the Window
        self.show()

    def CreateRegisterForm(self):
        """
        Shows a registration form at the top of the window. Handles the
        form data with the help of _on_click_register. 
        """
        self.registerForm = QGroupBox()
        hbox = QHBoxLayout()
        self.name_input = QLineEdit(self)
#        self.lineedit.setFont(QtGui.QFont("Sanserif", 15))
        name_label = QLabel(_("Name"))
#        self.label.setFont(QtGui.QFont("Sanserif", 15))
        self.code_input = QLineEdit(self)
        code_label = QLabel(_("Code"))
        submit_btn = QPushButton(_("Register"))
        submit_btn.clicked.connect(self._on_click_register)
        hbox.addWidget(name_label)
        hbox.addWidget(self.name_input)
        hbox.addWidget(code_label)
        hbox.addWidget(self.code_input)
        hbox.addWidget(submit_btn)
        self.registerForm.setLayout(hbox)
        
    def _on_click_register(self):
        """
        Handles the registration form data. Checks if a name
        is provided (and shows a message if none is provided),
        assigns self.player_name, deletes the registration form
        and shows other elements that were hidden.
        """
        if self.name_input.text():
            self.player_name = self.name_input.text()
            self.number_label.show()
            self.timer_label.show()
            self.answer_label.show()
            self.answerButtons.show()
            self.actionButtons.show()
            self.registerForm.deleteLater()
        else:
            QMessageBox.about(self, "!", _("Please provide name"))

    def CreateAnswerButtons(self):
        """
        Creates a 2x10 grid of numbers from [1-20] which are QPushButtons and
        activate _on_click_answer when clicked.
        """
        self.answerButtons = QGroupBox()
        gridLayout = QGridLayout()
        self.btns = []
        for i in range(2):
            for j in range(10):
                btn = QPushButton(_n(str(10*i + j + 1)))
                btn.setMaximumWidth(30)
                btn.clicked.connect(self._on_click_answer)
                gridLayout.addWidget(btn, i, j)
                self.btns.append(btn)
        self.answerButtons.setLayout(gridLayout)


    def CreateActionButtons(self):
        """
        Creates a QHBoxLayout with Start and Exit buttons. Start activates
        self._start and Exit activates self._exit.
        """
        self.actionButtons = QGroupBox()
        hboxLayout = QHBoxLayout()

        self.start_btn = QPushButton(_("Start"), self)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self._start)
        hboxLayout.addWidget(self.start_btn)

        self.exit_btn = QPushButton(_("Exit"), self)
        self.exit_btn.setMinimumHeight(40)
        self.exit_btn.clicked.connect(self._exit)
        hboxLayout.addWidget(self.exit_btn)        
        
        self.actionButtons.setLayout(hboxLayout)
        
    def _start(self):
        """
        By clicking start, if it has not already started, the task begins. 
        This functions initializes, runs and talks with two simultaneous 
        (and independent) threads: PlayNumbersThread which shows and reads aloud 
        the random_numbers one by one, and TimerThread which updates the timer_label.
        """
        if not self.trial_started:
            self.audio_thread = PlayNumbersThread(self.random_numbers)
            self.audio_thread.start()
            self.audio_thread.new_number.connect(self._update_number)
            self.audio_thread.finished.connect(self._finished)
            
            self.timer_thread = TimerThread()
            self.timer_thread.start()
            self.timer_thread.time_step.connect(self._update_timer)
            
            self.trial_started = True
        
    def _submit_answer(self,user_answer):
        """
        This is where answers are recorded and scored. TODO: Allow answer only if at least
        two numbers have been presented.
        """
        # Reaction time is calulated as the time elapsed since the number was
        # presented till the user clicked or typed an answer
        reaction_time = time.time()-self.time_presented
        if user_answer:
            # answer is a string, whether it comes from mouse or keyboard input
            user_answer = int(user_answer)
            correct_answer = self.played_numbers[-1] + self.played_numbers[-2]
            if user_answer == correct_answer:
                self.number_label.setText(_("Correct"))
                self.results.append('C')
                self.reaction_times.append(reaction_time)
            else:
                self.number_label.setText(_("Incorrect"))
                self.results.append('I')
                self.reaction_times.append(0)
        else:
            self.results.append('N')
            self.reaction_times.append(0)

        
    def _on_click_answer(self):
        """
        When a button from answerButtons is clicked, this function is activated,
        which simply passes on the number that has been clicked to _submit_answer.
        """
        # Do not change answer_label if allow_answer is False (i.e. only one number
        # has been presented)
        if not self.allow_answer:
            return
        # Identify the button clicked using self.sender() and then _submit_answer
        if not self.answerButton_clicked:
            btn = self.sender()
            self.answerButton_clicked = True
            self._submit_answer(btn.text())
        
    def keyPressEvent(self, e):
        """
        This handles the editing of answer_label value and correspondingly updating
        current_typed_answer. It allows only numbers to be entered, and using 
        Key_Backspace will remove the last digit. When the INTERVAL is finished, 
        the value in current_typed_answer is saved in the _update_number. Enter and
        Space for entering the answer before the INTERVAL is not working probably because
        they interact with the actionButtons! So used Q instead!
        """
        # Do not change answer_label if allow_answer is False (i.e. only one number
        # has been presented)
        if not self.allow_answer:
            return
        # Backspace will remove the last digit
        if e.key() == QtCore.Qt.Key_Backspace:
            self.current_typed_answer = self.current_typed_answer[:-1]
            self.answer_label.setText(self.current_typed_answer)
        elif e.key() == QtCore.Qt.Key_Q and (self.current_typed_answer) \
             and (not self.answerButton_clicked):
            self._submit_answer(self.current_typed_answer)
            self.answerButton_clicked = True
        else:
            try:
                key_str = chr(e.key())
            except:
                pass
            else:
                if key_str in ['0','1','2','3','4','5','6','7','8','9'] and\
                len(self.current_typed_answer) < 2:
                    self.current_typed_answer += _n(key_str)
                    self.answer_label.setText(self.current_typed_answer)
                
    def _update_number(self,number, time_presented):
        """
        This function is called whenever a new number is presented by
        PlayNumbersThread (message is ralayed in the _start). First,
        if a answerButton has not already been clicked, or Key_Q has not
        been pressed, the number currently in the current_typed_answer is
        saved as the answer for the previous interval. Then the state variables
        are reinitialized, and finally the new number is shown on number_label,
        the time it was presented is recorded and it is added to the played_numbers
        list.
        """
        # If the answer has not been already entered, use the current value of
        # current_typed_answer as the answer for previous interval. If no answer
        # is provided, pass "" to the _submit_answer, which indicates not answered
        if self.allow_answer and not self.answerButton_clicked:
            self._submit_answer(self.current_typed_answer)

        # Reinitialize state variables and answer_label
        self.current_typed_answer = ''
        self.answerButton_clicked = False
        self.answer_label.setText('')

        # Record the time that the new number was presented
        self.time_presented = time_presented
        # Add the new number to the played_numbers list
        self.played_numbers.append(number)
        if len(self.played_numbers) >= 2:
            self.allow_answer = True
        # Update the number_label text
        self.number_label.setText(_n('%d'%number))
    def _update_timer(self, total_time):
        """
        This function simply shows the total_time elapsed since
        the start of the trial. TimerThread takes care of measuring
        the time
        """
        self.timer_label.setText(_n('%.1f' % total_time))
        
    def _finished(self):
        """
        When all numbers have been shown, shows the results in a modal called
        results_dialog, which has a title, and a grid showing the stats, plus a button
        for saving the results as cvs (TODO)
        """
        # When only two numbers are shown, there's no results and this code can lead
        # to errors. Just is here to prevent this error.
        if not self.results:
            return
        # Calculate correct_percent and mean_reaction_time (for correct answers that are nonzero)
        correct_percent = 100 * (self.results.count('C')/len(self.results))
        mean_reaction_time = non_zero_mean(self.reaction_times)
        # Define stats to be shown in the statsgrid
        self.stats = [(_('Correct Answers'), self.results.count('C')),
                         (_('Incorrect Answers'), self.results.count('I')),
                         (_('Not Answered'), self.results.count('N')),
                         (_('Correct %'), correct_percent),
                         (_('Results List'), self.results),
                         (_('Reaction Times'), self.reaction_times),
                         (_('Mean Reaction Time'),mean_reaction_time)]
        
        # Initiate the dialog
        results_dialog = QDialog(self)
        results_dialog.setWindowTitle(_("Results"))
        results_dialog.setGeometry(self.left, self.top, self.width, self.height)
        self._center(results_dialog)
        
        # Initialize the vertical layout container vbox and add the title
        vbox = QVBoxLayout()
        title = QLabel(_("Results"))
        title.setAlignment(QtCore.Qt.AlignTop)
        title.setFont(QtGui.QFont("Sanserif", 20)) #TODO: Change to Farsi fonts and embedd it to the .exe file
        vbox.addWidget(title)
        
        # Add the stats in a statsgrid
        statsbox = QGroupBox()
        statsgrid = QGridLayout()
        self.btns = []
        for i in range(len(self.stats)):
            for j in range(2):
                label = QLabel(str(self.stats[i][j]))
                statsgrid.addWidget(label, i, j)
        statsbox.setLayout(statsgrid)
        vbox.addWidget(statsbox)        

        results_dialog.setLayout(vbox)        
        
        # Make it RTL if the language is fa
        if LANGUAGE == "fa":
            results_dialog.setLayoutDirection(QtCore.Qt.RightToLeft)
        # Show the dialog #TODO: add exit button
        results_dialog.show()
    
    def _change_language(self):
        global LANGUAGE
        selected_language = self.sender().text()
        if selected_language == "Farsi":
            LANGUAGE = "fa"
        elif selected_language == "English":
            LANGUAGE = "en"
        App.exit(EXIT_CODE_REBOOT)
    
    def _exit(self):
        """
        Exits the program
        """
        sys.exit()
    
if __name__ == '__main__':
    currentExitCode = EXIT_CODE_REBOOT
    while currentExitCode == EXIT_CODE_REBOOT:
        App = QApplication(sys.argv)
        if LANGUAGE == "fa":
            App.setLayoutDirection(QtCore.Qt.RightToLeft)
        window = Window()
        currentExitCode = App.exec_()
        App = None


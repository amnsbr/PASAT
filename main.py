# -*- coding: utf-8 -*-
"""
Paced Auditory Serial Addition Test 
with PyQt5 on Python3.7 (developed and tested under Anaconda 2019.7)
Created on Wed Aug 28 15:56:33 2019

@author: Amin Saberi
"""

from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QHBoxLayout,\
 QGroupBox, QVBoxLayout, QLabel, QGridLayout, QLineEdit, QMessageBox,\
 QMainWindow, QAction, QFormLayout, QSpinBox, QCheckBox
from PyQt5 import QtGui
from PyQt5 import QtCore
import sys, random, time
import helpers
from threads import PlayNumbersThread, PlayDemoThread, TimerThread, resource_path

#TODO: Define sessions and trials
#TODO: Used globals for the language change, it works but isn't a good practice!
#TODO: Show results in table
#TODO: Add test description text

NUMBERS_PER_TRIAL = 10
PAIRS_IN_DEMO = 2
INTERVAL = 3 #seconds
TRIAL_LENGTH = NUMBERS_PER_TRIAL * INTERVAL #seconds
AUTOSAVE = True
LANGUAGE = "en"
_, _n = helpers.redefine_gettext(LANGUAGE)

EXIT_CODE_REBOOT = -123
        
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
        self.title = "Paced Auditoy Serial Addition Test"
        self.top = 100
        self.left = 100
        self.width = 800
        self.height = 600
        # this is necessary for changing the language from the menu. every time
        # language is changed, __init__ is called again, and _ and _n need to be
        # redefined
        global _, _n
        _, _n = helpers.redefine_gettext(LANGUAGE)

        # Set the title and geometry of the window
        self.setWindowIcon(QtGui.QIcon(resource_path("icon.ico")))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        helpers.center_widget(App, self)

        self.CreateMenu()
        self.InitWindow()
                
        self.player_name = ''
        self.player_code = ''
        # Initilize answerButton_clicked, so that when during an INTERVAL that
        # a number has been played, user cannot click on more than one answers,
        # and also cannot use keyboard to type the answer
        self.answerButton_clicked = False
        # Initialize allow_answer. Do not allow_answer (inside _on_click_answer and 
        # keyboard handler), until more than one numbers have been presented
        self.allow_answer = False
        # Initialize the current_typed_answer (which is the value for self.answer_input).
        # This will record the typed answer, and is reset after each interval
        self.current_typed_answer = ''
        # Record if the trial has been started, so clicking start afterwards wouldn't
        # do anything.
        self.trial_started = False
        self.demo_started = False
        self.mode = ''
        # By default, show the demo. Can change it in the preferences.
        self.show_demo_on = True
        # Initialize time_presented. This is not the time_presented for the first
        # number, it's only here to prevent undefined error.
        self.show_timer_on = False
        self.time_presented = time.time()
        self.csv_filepath = 'results.csv' #TODO
        
 
    def CreateMenu(self):
        mainMenu = self.menuBar()
        sessionMenu = mainMenu.addMenu(_('Session'))
        runMenu = mainMenu.addMenu(_('Run'))
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
        
        self.startRunAction = QAction(_("Start"), self)
        self.startRunAction.triggered.connect(self._start)
        runMenu.addAction(self.startRunAction)
        self.demoRunAction = QAction(_("Demo"), self)
        self.demoRunAction.triggered.connect(self._start_demo)
        runMenu.addAction(self.demoRunAction)
        self.stopRunAction = QAction(_("Stop"), self)
        self.stopRunAction.setEnabled(False)
        self.stopRunAction.triggered.connect(self._stop)
        runMenu.addAction(self.stopRunAction)
        self.pauseRunAction = QAction(_("Pause"), self)
        self.pauseRunAction.setEnabled(False)
        self.pauseRunAction.triggered.connect(self._pause)
        runMenu.addAction(self.pauseRunAction)
        self.resumeRunAction = QAction(_("Resume"), self)
        self.resumeRunAction.setEnabled(False)
        self.resumeRunAction.triggered.connect(self._resume)
        runMenu.addAction(self.resumeRunAction)
        
        preferencesAction = QAction(_("Preferences"), self)
        preferencesAction.triggered.connect(self.ShowPreferences)
        optionsMenu.addAction(preferencesAction)
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
        aboutAction.triggered.connect(self._show_about)
        helpMenu.addAction(aboutAction)
#        helpAction = QAction(_("How it woks"), self)
#        helpMenu.addAction(helpAction)

### Registration view and Test view ###         
    def InitWindow(self):
        """
        Adds elements to the Window. Inside the Window is the vbox. And each
        row of widgets are added one by one to vbox, including registerForm, number_label,
        timer_label, answerButtons, answer_input and actionButtons. All widgets except
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
        
        # Add the answer_input which prints the self.current_typed_answer
        # and serves as another way of entering the answer. Could've used text-input,
        # but this seems more suitable for my purpose.
        self.answer_input = QLineEdit()
        answer_reg_ex = QtCore.QRegExp("[0-9]+")
        answer_input_validator = QtGui.QRegExpValidator(answer_reg_ex, self.answer_input)
        self.answer_input.setValidator(answer_input_validator)
        # self.answer_input.returnPressed.connect(self._answer_input_return_pressed)
        self.answer_input.setStyleSheet("""
                                        .QLineEdit {
                                        border: 0;
                                        background: transparent;
                                        }                                
                                        """)
        self.answer_input.setAlignment(QtCore.Qt.AlignCenter)
        self.answer_input.hide()
        ##self.answer_input.setFont(QtGui.QFont("Sanserif", 20))
        vbox.addWidget(self.answer_input)

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
        self.submit_btn = QPushButton(_("Register"))
        self.submit_btn.clicked.connect(self._on_click_register)
        hbox.addWidget(name_label)
        hbox.addWidget(self.name_input)
        hbox.addWidget(code_label)
        hbox.addWidget(self.code_input)
        hbox.addWidget(self.submit_btn)
        hbox.setAlignment(QtCore.Qt.AlignTop)
        self.registerForm.setLayout(hbox)
        
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
                btn.setMaximumWidth(self.width/12)
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
        
        self.demo_btn = QPushButton(_("Demo"), self)
        self.demo_btn.setMinimumHeight(40)
        self.demo_btn.clicked.connect(self._start_demo)
        hboxLayout.addWidget(self.demo_btn)

        self.exit_btn = QPushButton(_("Exit"), self)
        self.exit_btn.setMinimumHeight(40)
        self.exit_btn.clicked.connect(self._exit)
        hboxLayout.addWidget(self.exit_btn)        
        
        self.actionButtons.setLayout(hboxLayout)

### Results view ####    
    def ShowResultsDialog(self):
        """
        Shows the results of PASAT or demo in a new dialog. Triggered by 
        _finished or _demo_finished event handlers.
        """
        # Initiate the dialog
        self.results_dialog = QDialog(self)
        if self.mode == 'PASAT':
            self.results_dialog.setWindowTitle(_("Results"))
        elif self.mode == 'Demo':
            self.results_dialog.setWindowTitle(_("Demo Results"))            
        self.results_dialog.setGeometry(self.left, self.top, self.width*0.75, self.height*0.75)
        helpers.center_widget(App, self.results_dialog)
        
        # Initialize the vertical layout container vbox and add the title
        vbox = QVBoxLayout()
        if self.mode == 'PASAT':
            title = QLabel(_("Results"))
        elif self.mode == 'Demo':
            title = QLabel(_("Demo Results"))
        title.setAlignment(QtCore.Qt.AlignTop)
        title.setFont(QtGui.QFont("Sanserif", 20)) #TODO: Change to Farsi fonts and embedd it to the .exe file
        vbox.addWidget(title)
        
        # Add the stats in a statsgrid
        statsbox = QGroupBox()
        statsgrid = QGridLayout()
        for i in range(len(self.stats)):
            for j in range(2):
                label = QLabel(str(self.stats[i][j]))
                statsgrid.addWidget(label, i, j)
        statsbox.setLayout(statsgrid)
        vbox.addWidget(statsbox)        
        
        if AUTOSAVE:
            vbox.addWidget(QLabel(_("Results were automatically saved")))
        else:
            cancel_btn = QPushButton(_("Discard"))
            cancel_btn.clicked.connect(self.results_dialog.close)
            save_btn = QPushButton(_("Save"))
            save_btn.clicked.connect(self._save_results)   
            vbox.addWidget(cancel_btn)
            vbox.addWidget(save_btn)
        
        self.results_dialog.setLayout(vbox)        
        
        # Make it RTL if the language is fa
        if LANGUAGE == "fa":
            self.results_dialog.setLayoutDirection(QtCore.Qt.RightToLeft)
        # Show the dialog #TODO: add exit button
        self.results_dialog.show()

### Preferences view ####
    def ShowPreferences(self):
        """
        Shows the preferences dialog. Triggered by 'Options -> Preferences'
        """
        self.preferences_dialog = QDialog(self)
        self.preferences_dialog.setWindowTitle(_("Preferences"))
        self.preferences_dialog.setGeometry(self.left, self.top, self.width*0.75, self.height*0.75)
        helpers.center_widget(App, self.preferences_dialog)
        
        vbox = QVBoxLayout()
        
        preferencesForm = QGroupBox(self)
        form = QFormLayout()
        self.numbers_per_trial_input = QSpinBox(self)
        self.numbers_per_trial_input.setValue(NUMBERS_PER_TRIAL)
        self.numbers_per_trial_input.setMinimum(2)
        numbers_per_trial_label = QLabel(_("Numbers per trial"))
        self.interval_input = QSpinBox(self)
        self.interval_input.setValue(INTERVAL)
        self.interval_input.setMinimum(2)
        interval_label = QLabel(_("Interval between numbers (seconds)"))
        self.show_timer_input = QCheckBox()
        self.show_timer_input.setChecked(self.show_timer_on)
        show_timer_label = QLabel(_("Show timer"))
        self.show_demo_input = QCheckBox()
        self.show_demo_input.setChecked(self.show_demo_on)
        show_demo_label = QLabel(_("Show demo"))
        self.pairs_in_demo_input = QSpinBox(self)
        self.pairs_in_demo_input.setValue(PAIRS_IN_DEMO)
        self.pairs_in_demo_input.setMinimum(2)
        pairs_in_demo_label = QLabel(_("Number of pairs in demo"))
        form.addRow(numbers_per_trial_label, self.numbers_per_trial_input)
        form.addRow(interval_label, self.interval_input)
        form.addRow(show_timer_label, self.show_timer_input)
        form.addRow(show_demo_label, self.show_demo_input)
        form.addRow(pairs_in_demo_label, self.pairs_in_demo_input)
        preferencesForm.setLayout(form)
        
        cancel_btn = QPushButton(_("Cancel"))
        cancel_btn.clicked.connect(self.preferences_dialog.close)
        save_btn = QPushButton(_("Save"))
        save_btn.clicked.connect(self._save_preferences)
        
        vbox.addWidget(preferencesForm)
        vbox.addWidget(cancel_btn)
        vbox.addWidget(save_btn)
        self.preferences_dialog.setLayout(vbox)        
        self.preferences_dialog.show()

### User Input Event Handles ###
# Sorted by appearance
    def _on_click_register(self):
        """
        Handles the registration form data. Checks if a name
        is provided (and shows a message if none is provided),
        assigns self.player_name, deletes the registration form
        and shows other elements that were hidden.
        """
        if self.code_input.text():
            self.player_name = self.name_input.text()
            self.player_code = self.code_input.text()
            self.number_label.show()
            self.timer_label.show()
            self.answer_input.show()
            self.answerButtons.show()
            self.actionButtons.show()
            #self.registerForm.deleteLater()
            self.name_input.setEnabled(False)
            self.code_input.setEnabled(False)
            self.submit_btn.hide()
        else:
            QMessageBox.about(self, "!", _("Please provide the code"))

    def _start_demo(self):
        """
        By clicking demo button, if it has not already started, the task begins. 
        This functions initializes, runs and talks with two simultaneous 
        (and independent) threads: PlayPairsThread which shows the pairs of 
        random_numbers one by one (e.g. 2 + 5), and TimerThread which updates 
        the timer_label.
        """
        if not (self.trial_started | self.demo_started):
            # Create pairs (n = PAIRS_IN_DEMO) to be used in PlayDemoThread
            self.current_pair = ()
            # Keep track of reaction_times and "C" (correct)/"I" (incorrect)/"N" (not answered)
            self.demo_reaction_times = []
            self.demo_results = []
            
            self.demo_pairs = []
            for dummy in range(PAIRS_IN_DEMO):
                self.demo_pairs.append((random.randint(1,10), random.randint(1,10)))
            # Initialize and start the self.demo_thread
            self.demo_thread = PlayDemoThread(self.demo_pairs, INTERVAL)
            self.demo_thread.start()
            # self.demo_thread will signal self._update_demo_pair when a new_pair is up
            self.demo_thread.new_pair.connect(self._update_demo_pair)
            # self.demo_thread will signal self._demo_finished when all pairs have been read
            self.demo_thread.finished.connect(self._finished)
            
            # Initialize and start the self.timer_thread
            if self.show_timer_on:
                self.timer_thread = TimerThread(PAIRS_IN_DEMO * INTERVAL)
                self.timer_thread.start()
                self.timer_thread.time_step.connect(self._update_timer)
            
            # Change the state of the program
            self.demo_started = True
            self.allow_answer = False
            self.answerButton_clicked = False
            self.mode = 'Demo'
            self.demo_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.stopRunAction.setEnabled(True)
            self.pauseRunAction.setEnabled(True)

    def _start(self):
        """
        By clicking start, if it has not already started, the task begins. 
        This functions initializes, runs and talks with two simultaneous 
        (and independent) threads: PlayNumbersThread which shows and reads aloud 
        the random_numbers one by one, and TimerThread which updates the timer_label.
        """
        if not self.trial_started:
            self.reaction_times = []
            self.results = []
            self.played_numbers = []
            # Create a list of random_numbers with the length of NUMBERS_PER_TRIAL. The range
            # of random numbers is [1, 10], so the possible answers are [2, 20]
            self.random_numbers = []
            for dummy in range(NUMBERS_PER_TRIAL):
                self.random_numbers.append(random.randint(1,10))
            self.audio_thread = PlayNumbersThread(self.random_numbers, INTERVAL, LANGUAGE)
            self.audio_thread.start()
            self.audio_thread.new_number.connect(self._update_number)
            self.audio_thread.finished.connect(self._finished)
            
            if self.show_timer_on:
                self.timer_thread = TimerThread(TRIAL_LENGTH)
                self.timer_thread.start()
                self.timer_thread.time_step.connect(self._update_timer)
            
            self.trial_started = True
            self.allow_answer = False
            self.answerButton_clicked = False
            self.mode = 'PASAT'
            self.demo_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.stopRunAction.setEnabled(True)
            self.pauseRunAction.setEnabled(True)
        
    def _on_click_answer(self):
        """
        When a button from answerButtons is clicked, this function is activated,
        which simply passes on the number that has been clicked to _submit_answer.
        """
        # Do not change answer_input if allow_answer is False (i.e. only one number
        # has been presented)
        if not self.allow_answer:
            return
        # Identify the button clicked using self.sender() and then _submit_answer
        if not self.answerButton_clicked:
            btn = self.sender()
            self.answerButton_clicked = True
            # Based on the state of program, decide which scorer function to use
            if self.mode == 'PASAT':
                self._submit_answer(btn.text())
            elif self.mode == 'Demo':
                self._submit_demo_answer(btn.text())
        
    def _answer_input_return_pressed(self):
        """
        When Key_Return or Key_Enter is pressed while focus is on answer_input
        (which is always, since keyPressEvent sets focus to answer_input), relays
        current text of answer_input to _submit_answer or _submit_demo_answer
        depending on self.mode
        """
        if not self.allow_answer:
            return
        if not self.answerButton_clicked:
            self.answerButton_clicked = True
            if self.mode == 'PASAT':
                self._submit_answer(self.answer_input.text())
            elif self.mode == 'Demo':
                self._submit_demo_answer(self.answer_input.text())

    def keyPressEvent(self, e):
        """
        This function sets focus to the answer_input when any key is pressed, and
        if the focus is not already on the answer_input, catches the key pressed
        and if it's a number enters it in the answer_input
        """
        # Do not change answer_input if allow_answer is False (i.e. only one number
        # has been presented)
        if not self.allow_answer:
            return
        # Backspace will remove the last digit
        # self.answer_input.setFocus()
        if e.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            self._answer_input_return_pressed() 
        try:
            key_str = chr(e.key())
        except:
            pass
        else:
            if key_str in ['0','1','2','3','4','5','6','7','8','9']:
                self.current_typed_answer += key_str
                self.answer_input.setText(self.current_typed_answer)
                
### Threads event handlers ###
    def _update_demo_pair(self, pair, time_presented):
        """
        This function is called whenever a new pair of numbers is presented by
        PlayDemoThread (message is ralayed in the _start_demo). First,
        if a answerButton has not already been clicked, or Key_Q has not
        been pressed, the number currently in the current_typed_answer is
        saved as the answer for the previous interval. Then the state variables
        are reinitialized, and finally the new pair is shown on number_label,
        the time it was presented is recorded and the current_pair is recorded
        to be scored by _submit_demo_answer.
        """
        # If the answer has not been already entered, use the current value of
        # current_typed_answer as the answer for previous interval. If no answer
        # is provided, pass "" to the _submit_answer, which indicates not answered
        if ((self.allow_answer) and (not self.answerButton_clicked)):
            self._submit_demo_answer(self.current_typed_answer)
        
        self.answerButton_clicked = False
        self.current_typed_answer = ''
        self.answer_input.setText('')

        self.time_presented = time_presented

        self.number_label.setText(_n(str(pair[0])) + ' + ' + _n(str(pair[1])))
        self.current_pair = pair
        self.allow_answer = True
                    
    def _update_number(self, number, time_presented):
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
        if ((self.allow_answer) and (not self.answerButton_clicked)):
            self._submit_answer(self.current_typed_answer)

        # Reinitialize state variables and answer_input
        self.answerButton_clicked = False
        self.current_typed_answer = ''
        self.answer_input.setText('')

        # Record the time that the new number was presented
        self.time_presented = time_presented
        # Add the new number to the played_numbers list
        # Update the number_label text
        self.number_label.setText(_n('%d'%number))
        self.played_numbers.append(number)
        if len(self.played_numbers) >= 2:
            self.allow_answer = True

    def _update_timer(self, total_time):
        """
        This function simply shows the total_time elapsed since
        the start of the trial. TimerThread takes care of measuring
        the time
        """
        self.timer_label.setText(_n('%.1f' % total_time))

### Test dynamics event handlers ###
    def _submit_demo_answer(self, user_answer):
        """
        This is where demo answers are scored.
        """
        # Reaction time is calulated as the time elapsed since the number was
        # presented till the user clicked or typed an answer
        reaction_time = round(time.time()-self.time_presented, 1)
        if user_answer:
            # answer is a string, whether it comes from mouse or keyboard input
            user_answer = int(user_answer)
            correct_answer = self.current_pair[0] + self.current_pair[1]
            if user_answer == correct_answer:
                self.number_label.setText(_("Correct"))
                self.demo_results.append('C')
                self.demo_reaction_times.append(reaction_time)
            else:
                self.number_label.setText(_("Incorrect"))
                self.demo_results.append('I')
                self.demo_reaction_times.append(0)
        else:
            self.demo_results.append('N')
            self.demo_reaction_times.append(0)

        
    def _submit_answer(self,user_answer):
        """
        This is where answers are recorded and scored.
        """
        # Reaction time is calulated as the time elapsed since the number was
        # presented till the user clicked or typed an answer
        reaction_time = round(time.time()-self.time_presented, 1)
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
        
    def _finished(self):
        """
        When PlayDemoThread or PlayNumbersThread have shown all the numbers/pairs, 
        calculates the stats, shows the results using ShowResultsDialog and
        restates the program so a new game can be started.
        """
        # When only two numbers are shown, there's no results and this code can lead
        # to errors. Just is here to prevent this error.
        if type(self.sender()) == PlayNumbersThread:
            results = self.results
            reaction_times = self.reaction_times
            self.number_label.setText(_("Finished"))
        elif type(self.sender()) == PlayDemoThread:
            results = self.demo_results
            reaction_times = self.demo_reaction_times
            self.number_label.setText(_("Demo Finished"))

        if results:
            # Calculate correct_percent and mean_reaction_time (for correct answers that are nonzero)
            correct_percent = 100 * (results.count('C')/len(results))
            mean_reaction_time = helpers.non_zero_mean(reaction_times)
            # Define stats to be shown in the statsgrid
            self.stats = [(_('Correct Answers'), results.count('C')),
                             (_('Incorrect Answers'), results.count('I')),
                             (_('Not Answered'), results.count('N')),
                             (_('Correct %'), correct_percent),
                             (_('Results List'), results),
                             (_('Reaction Times'), reaction_times),
                             (_('Mean Reaction Time'),mean_reaction_time),
                             (_('Last third correct - First third correct'), helpers.get_fatigability(results)),
                             (_('Percent decrease in the last third'), helpers.get_fatigability(results, as_percent=True))]
            if AUTOSAVE:
                self._save_results()
            self.ShowResultsDialog()
        
        self.trial_started = False
        self.demo_started = False
        self.allow_answer = False
        self.start_btn.setEnabled(True)
        self.demo_btn.setEnabled(True)

    def _save_results(self):
        """
        Prepares the data for helpers.update_csv and calls it. Called if AUTOSAVE is enabled, 
        or when Save button from results_dialog is
        clicked. 
        """
        all_results = {'Addition':[], 'PASAT':[]} #TODO inconsistent variable names
        all_reaction_times = {'Addition':[], 'PASAT':[]}
        modes = []
        session_ids = {'Addition':1, 'PASAT':1} #TOOD
        if hasattr(self, 'demo_results'):
            all_results['Addition'] = self.demo_results
            all_reaction_times['Addition'] = self.demo_reaction_times
            modes.append('Addition')
        if hasattr(self, 'results'):
            all_results['PASAT'] = self.results
            all_reaction_times['PASAT'] = self.reaction_times
            modes.append('PASAT')
        helpers.update_csv(self.csv_filepath, self.player_name, self.player_code,\
                           all_results, all_reaction_times, modes, session_ids)
        try:
            self.results_dialog.close()
        except:
            pass


### Menu actions event handlers (except views) ###
    def _stop(self):
        """
        When stopRunAction is pressed from the Run menu, this function is called.
        It simply calls the .stop() function of the currently running thread and 
        disables pause and stop menu actions.
        """
        if self.mode == 'PASAT':
            self.audio_thread.stop()
        elif self.mode == 'Demo':
            self.demo_thread.stop()
        # Disable pause and stop within the Run menu    
        self.pauseRunAction.setEnabled(False)
        self.stopRunAction.setEnabled(False)
    
    def _pause(self):
        """
        When pauseRunAction is pressed from the Run menu, this function is called.
        It sets currently running thread status to .paused = True (which is taken
        care of within the thread run() function). Also, disables pause and enables
        resume menu actions.
        """
        if self.mode == 'PASAT':
            self.audio_thread.paused = True
        elif self.mode == 'Demo':
            self.demo_thread.paused = True
        if self.show_timer_on:
            self.timer_thread.paused = True
        # TODO: this does not work appropriately
        self.allow_answer = False
        # Disable pause action and enable resume action within Run menu
        self.pauseRunAction.setEnabled(False)
        self.resumeRunAction.setEnabled(True)
        
    def _resume(self):
        """
        When resumeRunAction is pressed from the Run menu, this function is called.
        It sets currently running thread status to .paused = False (which is taken
        care of within the thread run() function). Also, disables resume and enables
        pause menu actions.
        """
        if self.mode == 'PASAT':
            self.audio_thread.paused = False
        elif self.mode == 'Demo':
            self.demo_thread.paused = False
        if self.show_timer_on:
            self.timer_thread.paused = False
        # TODO: this does not work appropriately
        self.allow_answer = True
        # Disable pause action and enable resume action within Run menu
        self.pauseRunAction.setEnabled(True)
        self.resumeRunAction.setEnabled(False)
        
    def _change_language(self):
        """
        Changes the global variable LANGUAGE to the user selected languaged and
        restarts the application.
        """
        #TODO: do not use global
        global LANGUAGE
        selected_language = self.sender().text()
        if selected_language == _("Farsi"):
            LANGUAGE = "fa"
        elif selected_language == _("English"):
            LANGUAGE = "en"
        App.exit(EXIT_CODE_REBOOT)
            
    def _save_preferences(self):
        """
        Saves the preferences entered in the ShowPreferences dialog, and is
        called when .save_btn is clicked.
        """
        #TODO: Do not use global
        global NUMBERS_PER_TRIAL, INTERVAL, TRIAL_LENGTH, PAIRS_IN_DEMO
        NUMBERS_PER_TRIAL = int(self.numbers_per_trial_input.text())
        INTERVAL = int(self.interval_input.text())
        PAIRS_IN_DEMO = int(self.pairs_in_demo_input.text())
        TRIAL_LENGTH = NUMBERS_PER_TRIAL * INTERVAL
        # Show/hide the demo button based on the show_demo_input 
        if self.show_demo_input.isChecked():
            self.demo_btn.show()
            self.show_demo_on = True
        else:
            self.demo_btn.hide()
            self.show_demo_on = False
        # Show/hide the timer label based on the show_timer_input 
        if self.show_timer_input.isChecked():
            self.timer_label.show()
            self.show_timer_on = True
        else:
            self.timer_label.hide()
            self.show_timer_on = False
        self.preferences_dialog.close()
        
    def _show_about(self):
        """
        Shows the About message. Tirggered by About from Help menu.
        """
        QMessageBox.about(self, "About", _("""
        <h2>Paced Auditory Serial Adition Test (PASAT)</h2>
        Developed by Amin Saberi (amnsbr@gmail.com)
        2019.08"""))
            
    def _exit(self):
        """
        Exits the program
        """
        sys.exit()
    
if __name__ == '__main__':
    # currentExitCode is necessary for changing languages in Gui, do not know the dynamics
    currentExitCode = EXIT_CODE_REBOOT
    while currentExitCode == EXIT_CODE_REBOOT:
        App = QApplication(sys.argv)
        if LANGUAGE == "fa":
            App.setLayoutDirection(QtCore.Qt.RightToLeft)
        window = Window()
        currentExitCode = App.exec_()
        App = None


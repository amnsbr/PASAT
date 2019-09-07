# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 17:25:33 2019

@author: Amin Saberi
"""
from PyQt5.QtWidgets import QApplication
import gettext
from threads import resource_path
import csv, datetime, os
from collections import OrderedDict

### General Helpers
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
def redefine_gettext(language):
    if language == "fa":
        fa = gettext.translation('PASAT', localedir = resource_path('locale'), languages=['fa'])
        fa.install()
        _ = fa.gettext
        _n = en_to_ar_num
    else:
        _ = gettext.gettext
        # if language is not "fa", instead of english to arabic number translator function
        # pass the gettext.gettext as _n, that does nothing.
        _n = gettext.gettext
    return _, _n
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
    if count:
        return summation/count
    else:
        return 0
    
### Gui Helpers
def center_widget(app, widget):
    """
    Moves the widget belonging to the app to the center of screen 
    (not its parent). Use it for QMainWindow, QDialog and QWidget.
    """
    frameGm = widget.frameGeometry()
    screen = app.desktop().screenNumber(QApplication.desktop().cursor().pos())
    centerPoint = app.desktop().screenGeometry(screen).center()
    frameGm.moveCenter(centerPoint)
    widget.move(frameGm.topLeft())        


### CSV File Handlers
def update_csv(csv_filepath, player_name, player_code, all_results, all_reaction_times, modes, session_ids):
    """
    Each of the arguments (except csv_filename) are dicts with 'Addition' and
    'PASAT' keys. For example to get the demo results we would use results['Addition']
    """
    PREFIXES = ("Addition", "PASAT")#, "PASAT first half", "PASAT last half")
    RESULTS_FORMULAS = (("correct count", lambda results: results.count('C')), 
                        ("incorrect count", lambda results: results.count('I')),
                        ("not answered count", lambda results: results.count('N')),
                        ("correct %", lambda results: 100 * (results.count('C')/len(results))),
                        ("results list", lambda results: results))
    REACTION_TIME_FORMULAS = (("reaction times", lambda reaction_times: reaction_times), 
                              ("mean reaction time", lambda reaction_times: non_zero_mean(reaction_times)))
    
    fieldnames = ['Player Code', 'Player Name', 'Date', 'Time']
    for prefix in PREFIXES:
        for (stat_name, formula) in RESULTS_FORMULAS + REACTION_TIME_FORMULAS:
            fieldnames.append(prefix+" "+stat_name)
    
    current_row_data = OrderedDict()
    if os.path.isfile(csv_filepath):
        csvfile = open('results.csv','r')
        reader = csv.DictReader(csvfile, fieldnames, dialect='excel')
        rows = list(reader) #exclude header
        csvfile.close()
        for row in rows:
            if row['Player Code'] == player_code: #TODO and session is the same
                current_row_data = row

    else: #if no existing file, create a new rows list and add header to it
        rows = []
        rows.append(OrderedDict())
        for fieldname in fieldnames:
            rows[0][fieldname] = fieldname
    #if there is no row for the current player_code and session_id, add one at the end of rows    
    if not current_row_data: 
        rows.append(current_row_data)
        
    csvfile = open("results.csv", "w", newline='')
    writer = csv.DictWriter(csvfile, fieldnames, dialect = 'excel')

    current_row_data['Player Code'] = player_code
    current_row_data['Player Name'] = player_name
    current_row_data['Date'] = datetime.datetime.now().strftime("%Y %B %d")
    current_row_data['Time'] = datetime.datetime.now().strftime("%I:%M:%S %p")

    for mode in modes: # Addition or PASAT
        for (stat_name, formula) in RESULTS_FORMULAS:
            current_row_data[mode+" "+stat_name] = formula(all_results[mode])
        for (stat_name, formula) in REACTION_TIME_FORMULAS:
            current_row_data[mode+" "+stat_name] = formula(all_reaction_times[mode])
    
    writer.writerows(rows)
    csvfile.close()

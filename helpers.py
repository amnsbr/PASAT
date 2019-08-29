# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 17:25:33 2019

@author: Amin Saberi
"""
from PyQt5.QtWidgets import QApplication
import gettext

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

__author__ = 'ian.collins'

currentcolor = True # true=day, false=night

lightthreshold = 50
lightchecktime = 10.0
gpsrefreshtime = 15.0
netrefreshtime = 30.0
crvincidentmain = None
# The actualt status bar
statusbar = None
# Where the statusbar fields are kept
statusbarbox = None
# An alternate statusbar - primarily for drop down hints (first char of dropdown list)
altstatusbarbox = None     # used by dropdown for hints
# When button in alstatusbarbox is clicked, value it put here.
alstatusbarclick = ''
# The altstatusbarbox parent (used to test if caller is still active)
alstatusbarparent = None

lastdopopup = None # to try and stop too many error popups

data = None
msgbox = None
mycurl = None

tmpxloc = None

gridheight = 40
default_font_size = '20sp'
default_large_font_size = '30sp'
default_medium_font_size = '15sp'
default_small_font_size = '14sp'
default_tiny_font_size = '10sp'
default_menu_font_size = '18sp'





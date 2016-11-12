import os
#os.environ['KIVY_TEXT'] = 'pil'
import kivy

#kivy.require('1.9.0')
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.vkeyboard import VKeyboard
from kivy.config import Config
from kivy.core.window import Window

import datetime
from modlogging import clsLog

Logger=clsLog()
Logger.info("CRV: MAIN: App started")


Logger.info("CRV: config file.. " + Config.filename)
x = Config.get("kivy", "keyboard_mode")
Logger.info("CRV: keyboard at start is " + x)
if x != "dock":
    Logger.info("CRV: setting dock")
    Config.set('kivy', 'keyboard_mode', 'dock')
    Window.allow_vkeyboard = True
    Window.single_vkeyboard = True
    Window.docked_vkeyboard = True


from kivy.config import ConfigParser
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.dropdown import DropDown
from kivy.uix.settings import Settings
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
#from kivy.uix.modalview import ModalView
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
#from kivy.animation import Animation
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout, GridLayoutException
from kivy.uix.progressbar import ProgressBar
#from kivy.uix.listview import ListView
#from kivy.uix.listview import ListItemLabel
#from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
#from kivy.uix.switch import Switch
#from kivy.uix.popup import Popup
from kivy.lang import Builder
#from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.graphics import Color, Rectangle, Canvas, Line
from kivy.properties import ListProperty, ObjectProperty, StringProperty, NumericProperty, BooleanProperty, VariableListProperty
from kivy.clock import Clock, mainthread
from kivy.uix.settings import SettingsWithTabbedPanel
#from kivy.uix.camera import Camera
from kivy.utils import get_color_from_hex as rgb
from kivy.utils import platform

if platform == 'linux':
    import cProfile

# from kivy.logger import Logger

from crvgraph import Graph, MeshLinePlot, SmoothLinePlot, ContourPlot

#from os.path import join
#import json
#import time
import re
#import csv
import math
import threading

import modglobal

from functools import partial
#from email.utils import parseaddr

from settingsjson import settings_vesslog_json, settings_email_json, settings_crvapp_json

from crvdata import CrvData, CrvIncData
#from crvftp import CrvFtp
from crvURL import CrvURL
from crvprofile import CrvProfile
from crvgps import CrvGPS
from crvMessage import MessageBox

global lightSensor
global simlightSensor

#
# Handle light sensor on device - may need to do something else for ios
#
if platform == 'android':
    import android
    Logger.info('CRV:ANDROID: import lightsensor')
    from lightSensor import AndroidLightSensor
    lightSensor = AndroidLightSensor()
    simlightSensor = False

else:
    lightSensor = None
    simlightSensor = False  # debug

if lightSensor:
    Logger.info('CRV:Light sensor enabled')
else:
    Logger.info('CRV:No Light sensor')

# Config.getint('kivy', log_level)

kv = """

# My inherited checkbox (sets background correctly for a white canvas)
<CCheckBox>:
    canvas:
        Clear:
        Color:
            rgba: 0,0,0,0
        Rectangle:
            size: 48, 48
#           right justify checkbox
            pos: int(self.x+self.width-48), int(self.center_y - 24)
#           center checkbox
#            pos: int(self.center_x - 16), int(self.center_y - 16)
        Color:
            rgba: 0,0,0,1
        Rectangle:
            source: 'atlas://data/images/defaulttheme/checkbox%s_%s' % (('_radio' if self.group else ''), ('on' if self.active else 'off'))
            size: 48, 48
            pos: int(self.x+self.width-48), int(self.center_y - 24)
#            pos: int(self.center_x - 16), int(self.center_y - 24)

# put a border round a widget (boxlayout in this case)
<MyBoundBox>:
    background_normal: ''
    background_color: self.background_color

    canvas.after:
        Color:
            rgba: root.color
        Line:
            rectangle: self.x+1,self.y+1,self.width-1,self.height-1

<MyFilledBox>:
    canvas.before:
        Color:
            rgba: 0, 1, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size

# Align text input to the middle (you may want to change the 10 to zero
# (10 means inset x coord by 10 pixels)
<MyTextInput>:
    multiline:True
    write_tab: False
    input_type: 'text'
    background_color: root.background_color
    color:root.color
    use_bubble: False
    use_handles: False
    font_size: root.font_size

<CTextInput>:
    # multiline: self.multiline
    padding:  [10, 0.5 * (self.height - self.line_height)]
    write_tab: False
    input_type: 'text'
    background_color: root.background_color
    color:root.color
    use_bubble: False
    use_handles: False
    font_size: root.font_size

<CNumInput>:
    multiline: False
    padding: [10, 0.5 * (self.height - self.line_height)]
    input_type: 'number'
    input_filter: 'int'
    write_tab: False
    background_color: root.background_color
    color:root.color
    use_bubble: False
    use_handles: False
    font_size: root.font_size

<CFloatInput>:
    multiline: False
    padding: [10, 0.5 * (self.height - self.line_height)]
    input_type: 'number'
    input_filter: 'float'
    write_tab: False
    background_color: root.background_color
    color:root.color
    use_bubble: False
    use_handles: False
    font_size: root.font_size

<CTimeInput>:
    multiline: False
    padding: [10, 0.5 * (self.height - self.line_height)]
    input_type: 'datetime'
    write_tab: False
    background_color: root.background_color
    color:root.color
    use_bubble: False
    use_handles: False
    font_size: root.font_size

# Align a label at the top
<MyLabel>:
    #font_size: default_font_size
    font_size:root.font_size
    #halign:'center'
    #valign:'top'
    disabled_color: root.dimcol
    color: root.color
    #canvas.after:
    #    Color:
    #        #rgba: root.color # the color of the surrounding box
    #        rgba: root.background_color # the color of the surrounding box
    #    Line:
    #        rectangle: self.x+1,self.y+1,self.width-1,self.height-1

<CustomDropDown>:
    background_normal: ''
    background_color: self.background_color
    font_size:root.font_size

<MyButton>
    background_normal: ''
    background_color: root.background_color
    color: root.color
    disabled_color: root.dimcol
    font_size:root.font_size
    canvas.after:
        Color:
            rgba: root.color   # the color of the surrounding box
        Line:
            rectangle: self.x+1,self.y+1,self.width-1,self.height-1

<CustomButton@Button>:
    dim: self.dim
    wid: self.wid
    image: self.image
    label: self.label
    background_normal: ''
    background_color: self.background_color
    canvas.after:
        Color:
            rgba: root.color   # the color of the surrounding box
        Line:
            rectangle: self.x+1,self.y+1,self.width-1,self.height-1
    BoxLayout:
        orientation: 'vertical'
        size: self.parent.size
        pos: self.parent.pos        # match the button's position

        Image:
            source: root.image
            allow_stretch: True
            valign: "middle"
        Label:
            text: root.label
            halign:'center'
            valign:'top'
            #color: root.col
            color: root.color
            #disabled_color: [.5,.5,.5,1]
            disabled_color: root.dimcol
            font_size:root.font_size

<MyVKeyboardQwerty>
    layout: 'qwerty'

<MyVKeyboardNumeric>
    layout: 'numeric.json'
"""

class MyVKeyboardQwerty(VKeyboard):
    def __init__(self, **kwargs):
        super(MyVKeyboardQwerty, self).__init__(**kwargs)
        self.setup_mode(False)

    def setup_mode_dock(self, *largs):
        '''Override from VKeyboard

        Dock mode will reset the rotation, disable translation, rotation and
        scale. Scale and position will be automatically adjusted to attach the
        keyboard to the bottom of the screen.

        .. note::
            Don't call this method directly, use :meth:`setup_mode` instead.
        '''


        self.do_translation = False
        self.do_rotation = False
        self.do_scale = False
        self.rotation = 0
        win = self.get_parent_window()
        scale = max(win.width / float(self.width), 1.5)
#        scale = win.width / float(self.width)
        #scale = 1.0
        self.scale = scale
#        print "setup scale " + str(scale)
#        print "win.height " + str(win.height)
#        print "self.height " + str(self.height)
        ty = win.height - (self.height * self.scale) - 30.0
        Logger.info('CRV: setup mode dock qwerty keyboard ' + str(ty))

        if ty >= self.target.top:
            self.pos = 0.0, ty  # (30.0) How do you get windows titlebar height
        else:
            self.pos = 0, 30.0

#        print "setup pos " + str(self.pos)

        win.bind(on_resize=self._update_dock_mode)

    def _update_dock_mode(self, win, *largs):
        ty = win.height - (self.height * self.scale) - 30.0
        Logger.info('CRV: update mode dock qwerty keyboard ' + str(ty))

        if ty >= self.target.top:
            self.pos = 0.0, ty  # top
        else:
            self.pos = 0, 30.0 #bottom
#        print "update pos " + str(self.pos)
#        print "update scale " + str(self.scale)


class MyVKeyboardNumeric(VKeyboard):
    def __init__(self, **kwargs):
        super(MyVKeyboardNumeric, self).__init__(**kwargs)
        self.setup_mode(False)

    def setup_mode_dock(self, *largs):
        ''' Override from VKeyboard.

        Dock mode will reset the rotation, disable translation, rotation and
        scale. Scale and position will be automatically adjusted to attach the
        keyboard to the bottom of the screen.

        .. note::
            Don't call this method directly, use :meth:`setup_mode` instead.
        '''

        self.do_translation = False
        self.do_rotation = False
        self.do_scale = False
        self.rotation = 0
        win = self.get_parent_window()
        scale = max(win.width / float(self.width), 1.5)

        self.scale = scale
#        print "setup scale " + str(scale)
        ty = win.height - (self.height * self.scale) - 30.0

        Logger.info('CRV: setup mode dock qwerty keyboard')

        if ty >= self.target.top:
            self.pos = 0.0, ty
        else:
            self.pos = 0, 30.0

#        print "setup pos " + str(self.pos)

        win.bind(on_resize=self._update_dock_mode)

    def _update_dock_mode(self, win, *largs):
        ty = win.height - (self.height * self.scale) - 30.0
        Logger.info('CRV: update mode dock num keyboard ' + str(ty))

        if ty >= self.target.top:
            self.pos = 0.0, win.height - self.height - 30.0
        else:
            self.pos = 0, 30.0
#        print "setup pos " + str(self.pos)

class ImageButton(ButtonBehavior, Image):
    pass

class SigWidget(Widget):
    def __init__(self, **kwargs):
        super(SigWidget, self).__init__(**kwargs)
        self.doclear = False
        self.filename = ''

    def clearsig(self):
        if self.doclear:
            self.canvas.clear()

    def on_touch_down(self, touch):
        with self.canvas:
            if self.collide_point(touch.x, touch.y):
                self.clearsig()

                if not self.disabled:
                    touch.grab(self)
                    Color(0, 0, 1)
                    touch.ud['line'] = Line(points=(touch.x, touch.y))

    def on_touch_move(self, touch):
        if self.collide_point(touch.x, touch.y):
            if not self.disabled:
                touch.ud['line'].points += [touch.x, touch.y]

    def on_touch_up(self, touch):
        if not self.disabled:
            touch.ungrab(self)

    def savesignature(self):
        ok = False
        if not self.disabled:
            if self.filename != '':
                try:
                    Logger.info('CRV: Saving signature to ' +
                                self.filename)
                    self.export_to_png(self.filename)
                    ok = True
                    self.doclear = True
                except:
                    ok = False
        return ok

    def setfile(self, name):
        self.filename = name + '.png'

    def getfile(self):
        return self.filename

class CrvColor:

    # hint: http://www.rapidtables.com/web/color/RGB_Color.htm
    # then convert hext using, e.g.
    # c = kivy.utils.get_color_from_hex('#808000')

    white = [1, 1, 1, 1]
    gray = [.5, .5, .5, 1]
    darkgray = [.3, .3, .3, 1]
    black = [0, 0, 0, 1]
    red = [1, 0, 0, 1]
    green = [0, 1, 0, 1]
    blue = [0, 0, 1, 1]
    purple = [1, 0, 1, 1]
    olive = [0.50, 0.50, 0, 1]

    colors = { 'white': white, 'black': black, 'red': red, 'green': green, 'blue': blue, 'purple': purple,
               'darkgray':darkgray, 'olive':olive }
    daycolors = { 'bg': white, 'fg': blue, 'bold': red, 'dim': gray, 'butbg': darkgray, 'butfg': white,
                  'gridheader': olive  }
    nightcolors = { 'bg': gray, 'fg': red, 'bold': blue, 'dim': black, 'butbg': darkgray, 'butfg': white,
                  'gridheader': olive  }

    def __init__(self):
        # h = '#808000'
        # c = kivy.utils.get_color_from_hex(h)
        pass

    def getcolor(self, index):
        if index in self.colors:
            c = self.colors[index]
        else:
            c = self.colors['black']
        return c

    def getbgcolor(self):
        s = 'bg'
        if modglobal.currentcolor:
            c = self.daycolors[s]
        else:
            c = self.nightcolors[s]
        return c

    def getfgcolor(self):
        s = 'fg'
        if modglobal.currentcolor:
            c = self.daycolors[s]
        else:
            c = self.nightcolors[s]
        return c

    def getdimcolor(self):
        s = 'dim'
        if modglobal.currentcolor:
            c = self.daycolors[s]
        else:
            c = self.nightcolors[s]
        return c

    def getboldcolor(self):
        s = 'bold'
        if modglobal.currentcolor:
            c = self.daycolors[s]
        else:
            c = self.nightcolors[s]
        return c

    def getbutfgcolor(self):
        s = 'butfg'
        if modglobal.currentcolor:
            c = self.daycolors[s]
        else:
            c = self.nightcolors[s]
        return c

    def getbutbgcolor(self):
        s = 'butbg'
        if modglobal.currentcolor:
            c = self.daycolors[s]
        else:
            c = self.nightcolors[s]
        return c

    def getgridheadbgcolor(self):
        s = 'gridheader'
        if modglobal.currentcolor:
            c = self.daycolors[s]
        else:
            c = self.nightcolors[s]
        return c

    @staticmethod
    def getschema():
        return modglobal.currentcolor

    def setschema(self, s):  # True for Day, False for night
        if s:
            Logger.info('CRV:COLOR:DAY SCHEMA')
        else:
            Logger.info('CRV:COLOR:NIGHT SCHEMA')

        modglobal.currentcolor = s

class CustomDropDown(DropDown):
    crvcolor = CrvColor()
    c = crvcolor.getbgcolor()
    background_color = ListProperty(c)
    #background_color = ListProperty(c)
    def __init__(self, **kwargs):
        super(CustomDropDown, self).__init__(**kwargs)
        App.get_running_app().bind(daynight = self.switchDayNight)
        self.color = []
        self.background_color = []
        self.dimcol = []
        self.boldcol = []
        self.setcolors()
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

    def _reposition(self, *largs):
        #Logger.debug('CRV:_reposition')
        # calculate the coordinate of the attached widget in the window
        # coordinate system
        win = self._win
        widget = self.attach_to
        if not widget or not win:
            return
        wx, wy = widget.to_window(*widget.pos)
        wright, wtop = widget.to_window(widget.right, widget.top)

        # set width and x
        if self.auto_width:
            self.width = wright - wx

        # ensure the dropdown list doesn't get out on the X axis, with a
        # preference to 0 in case the list is too wide.
        x = wx
        if x + self.width > win.width:
            x = win.width - self.width
        if x < 0:
            x = 0
        self.x = x

        # determine if we display the dropdown upper or lower to the widget
        h_bottom = wy - self.height
        h_top = win.height - (wtop + self.height)
        #Logger.debug('CRV:ht, hb..' + str(h_bottom) + ' ' + str(h_top))

        if h_bottom > 0:
            self.top = wy
        elif h_top > 0:
            self.y = wtop
        else:
            #Logger.debug('CRV:else')
            # none of both top/bottom have enough place to display the
            # widget at the current size. Take the best side, and fit to
            # it.
            if modglobal.statusbar is not None:
                hsb = modglobal.statusbar.height
            height = max(h_bottom, h_top)
            if height == h_bottom:
                self.top = wy
                self.height = wy - hsb
            else:
                self.y = wtop
                self.height = win.height - wtop

class CustomButton(Button):
    """
    Defines a button that contains an image and a label
    (Widget defined in kv string)
    """
    #crvcolor = CrvColor()
    #
    dim = NumericProperty(0)
    wid = StringProperty('')
    image = StringProperty('')
    title = StringProperty('')
    label = StringProperty('')
    labcol = NumericProperty(1)
    #white = [1, 1, 1, 1]
    # black = [0, 0, 0, 1]
    # gray = [.5, .5, .5, 1]

    #col = ListProperty(black)

    #mycolor = gray
    #currentcolor = black

    crvcolor = CrvColor()

    color = ListProperty(crvcolor.getfgcolor())
    background_color = ListProperty(crvcolor.getbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())

    def __init__(self, **kwargs):
        super(CustomButton, self).__init__(**kwargs)
        self.setcolors()
        App.get_running_app().bind(daynight = self.switchDayNight)
        self.col = []
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            self.font_size = modglobal.default_font_size

        # self.crvcolor = CrvColor()
        #
        # self.color = ListProperty(self.crvcolor.getfgcolor())
        # self.background_color = ListProperty(self.crvcolor.getbgcolor())
        # self.dimcol = ListProperty(self.crvcolor.getdimcolor())
        # self.boldcol = ListProperty(self.crvself.color.getboldcolor())

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

    def newcol(self, c):
        self.col = c

    def clickdown(self):
        self.background_color = self.crvcolor.getboldcolor()
    def clickup(self):
        self.background_color = self.crvcolor.getbgcolor()

    def click(self):
        # global app
        # app.clearSelection()
        self.background_color = (0, 160, 66, .9)
        # Logger.info(self.title + ": wid=" + self.wid)


class MyLabel(Label):
    """
    A label with text orientated to the top
    (Widget defined in kv string)
    """

    crvcolor = CrvColor()
    color = ListProperty(crvcolor.getfgcolor())
    background_color = ListProperty(crvcolor.getbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())

    def __init__(self, **kwargs):
        super(MyLabel, self).__init__(**kwargs)
        self.setcolors()
        App.get_running_app().bind(daynight = self.switchDayNight)
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

        if kwargs.has_key('padding_y'):
            self.padding_y= kwargs['padding_y']
        else:
            self.padding_y = 12

        pass

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def highlight(self, dohighlight):
        # strange logic = False=bold, True=normal
        if dohighlight:
            self.color = self.crvcolor.getfgcolor()
        else:
            self.color = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

class MyButton(Button):
    crvcolor = CrvColor()
    color = ListProperty(crvcolor.getbutfgcolor())
    background_color = ListProperty(crvcolor.getbutbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())
    #fontsize = StringProperty(modglobal.default_font_size)
    #fontsize = StringProperty('20sp')

    def __init__(self, **kwargs):
        super(MyButton, self).__init__(**kwargs)
        self.setcolors()
        App.get_running_app().bind(daynight = self.switchDayNight)
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            self.font_size = modglobal.default_font_size
            #font_size = StringProperty(modglobal.default_font_size)

    def setcolors(self):
        self.color = self.crvcolor.getbutfgcolor()
        self.background_color = self.crvcolor.getbutbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def clickdown(self):
        self.background_color = self.crvcolor.getboldcolor()
    def clickup(self):
        self.background_color = self.crvcolor.getbutbgcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

class MyScroll(ScrollView):
    pass

class AutoLabel(Label):
    def __init__(self, **kwargs):
        """ Initialise the widget """
        super(AutoLabel, self).__init__(**kwargs)
        self.size_hint_x = None
        self.bind(on_texture_size=self.on_texture_size)
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size



    def on_texture_size(self, *args):
        if self.texture:
            self.width = self.texture.width

class MultiLineLabel(CustomButton):
    def __init__(self, **kwargs):
        super(MultiLineLabel, self).__init__( **kwargs)
        self.text_size = self.size
        self.bind(size= self.on_size)
        self.bind(text= self.on_text_changed)
        self.size_hint_y = None # Not needed here
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

    def on_size(self, widget, size):
        self.text_size = size[0], None
        self.texture_update()
        if self.size_hint_y is None and self.size_hint_x is not None:
            self.height = max(self.texture_size[1], self.line_height)
        elif self.size_hint_x is None and self.size_hint_y is not None:
            self.width  = self.texture_size[0]

    def on_text_changed(self, widget, text):
        self.on_size(self, self.size)

class CCheckBox(CheckBox):
    """
    A checkbox with a border
    (Widget defined in kv string)
    """
    pass

class MyBoundBox(BoxLayout):
    """
    A boxlayout surrounded by a border
    (Widget defined in kv string)
    """
    crvcolor = CrvColor()
    color = ListProperty(crvcolor.getfgcolor())
    background_color = ListProperty(crvcolor.getbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())
    #fontsize = StringProperty(modglobal.default_font_size)
    #fontsize = StringProperty('20sp')

    def __init__(self, **kwargs):
        super(MyBoundBox, self).__init__(**kwargs)
        self.setcolors()
        App.get_running_app().bind(daynight = self.switchDayNight)

        # if kwargs.has_key('padding_y'):
        #     self.padding_y= kwargs['padding_y']
        # else:
        #     self.padding_y = 12

        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            self.font_size = modglobal.default_font_size
            #font_size = StringProperty(modglobal.default_font_size)

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

class MyFilledBox(BoxLayout):
    """
    A boxlayout surrounded by a border
    (Widget defined in kv string)
    """
    pass

class MyTextInput(TextInput):
    """
    A text input widget with text aligned to the middle (vertically)
    (Widget defined in kv string)
    """
    crvcolor = CrvColor()
    color = ListProperty(crvcolor.getfgcolor())
    background_color = ListProperty(crvcolor.getbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())
    #fontsize = StringProperty(modglobal.default_font_size)
    #fontsize = StringProperty('20sp')
    multiline = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(MyTextInput, self).__init__(**kwargs)
        self.setcolors()
        App.get_running_app().bind(daynight = self.switchDayNight)

        self.wx = self.x
        self.wy = self.y
        self.wpos = self.pos

        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()


    def on_focus(self, instance, value, *largs):
        win = self.get_root_window()

        if win:
            win.release_all_keyboards()
            win._keyboards = {}

            if value:  # User focus; use special keyboard
                if self.input_type == 'number':
                    win.set_vkeyboard_class(MyVKeyboardNumeric)
                else:
                    win.set_vkeyboard_class(MyVKeyboardQwerty)

                print "VKeyboard true:", win._vkeyboard_cls, VKeyboard.layout_path
            else:  # User defocus; switch back to standard keyboard
                win.set_vkeyboard_class(VKeyboard)
                print "VKeyboard false:", win._vkeyboard_cls, VKeyboard.layout_path

class CTextInput(MyTextInput):
    """
    A text input widget with text aligned to the middle (vertically)
    (Widget defined in kv string)
    """
    crvcolor = CrvColor()
    color = ListProperty(crvcolor.getfgcolor())
    background_color = ListProperty(crvcolor.getbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())
    #fontsize = StringProperty(modglobal.default_font_size)
    #fontsize = StringProperty('20sp')
    multiline = BooleanProperty()

    def __init__(self, **kwargs):
        super(CTextInput, self).__init__(**kwargs)
        self.setcolors()
        App.get_running_app().bind(daynight = self.switchDayNight)
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

class CNumInput(MyTextInput):
    """
    A text input widget with text aligned to the middle (vertically)
    Only accepts numerics
    (Widget defined in kv string)
    """
    max_chars = NumericProperty(-1)
    crvcolor = CrvColor()
    color = ListProperty(crvcolor.getfgcolor())
    background_color = ListProperty(crvcolor.getbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())
    #fontsize = StringProperty(modglobal.default_font_size)
    #fontsize = StringProperty('20sp')
    multiline = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(CNumInput, self).__init__(**kwargs)
        self.setcolors()
        App.get_running_app().bind(daynight = self.switchDayNight)
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

    def insert_text(self, substring, from_undo=False):
        if not from_undo:
            tryit = False
            if self.max_chars > 0:
                if len(self.text)+len(substring) <= self.max_chars:
                    tryit = True
            else:
                tryit = True

            if tryit:
                try:
                    int(substring)
                except ValueError:
                    return
            else:
                return
        super(CNumInput, self).insert_text(substring, from_undo)

class CFloatInput(MyTextInput):

    crvcolor = CrvColor()
    color = ListProperty(crvcolor.getfgcolor())
    background_color = ListProperty(crvcolor.getbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())
    #fontsize = StringProperty(modglobal.default_font_size)
    #fontsize = StringProperty('20sp')
    multiline = BooleanProperty(False)

    pat = re.compile('[^0-9]')

    def __init__(self, **kwargs):
        super(CFloatInput, self).__init__(**kwargs)
        self.setcolors()

        App.get_running_app().bind(daynight = self.switchDayNight)
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(CFloatInput, self).insert_text(s, from_undo=from_undo)

class CTimeInput(MyTextInput):
    """
    A text input widget with text aligned to the middle (vertically)
    Only accepts time formats - i.e. numerics and a :
    Has a few smarts to allow 0 = 00:00, 01=00:01, :10=00:10, etc
    (Widget defined in kv string) - NOT DONE
    """
    pat = re.compile('[^0-9]')

    crvcolor = CrvColor()
    color = ListProperty(crvcolor.getfgcolor())
    background_color = ListProperty(crvcolor.getbgcolor())
    dimcol = ListProperty(crvcolor.getdimcolor())
    boldcol = ListProperty(crvcolor.getboldcolor())
    #fontsize = StringProperty(modglobal.default_font_size)
    #fontsize = StringProperty('20sp')
    padding =  VariableListProperty(['24dp', '48dp'])

    # NOT DONE...
    # 012345678901234567
    # DDD dd-mm-yy hh-mm
    # if cursor position ...
    #   3 goes to 4
    #   6 goes to 7
    #   9 goes to 10
    #  12 goes to 13
    #  15 goes to 16
    # if - or / entered then
    #   if cursor position
    #       [4,5]
    #            len is 0
    #                cursor to 4
    #            int < 10
    #                zero fill
    #                cursor to 7
    #            int > 31
    #                error
    #            int >= 10
    #                cursor to 7
    #       [
    #       then date
    def __init__(self, **kwargs):
        super(CTimeInput, self).__init__(**kwargs)
        self.setcolors()
        App.get_running_app().bind(daynight = self.switchDayNight)
        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

    # def insert_text(self, substring, from_undo=False):
    #     pat = self.pat
    #     if '-' in self.text:
    #         s = re.sub(pat, '', substring)
    #     else:
    #         s = '-'.join([re.sub(pat, '', s) for s in substring.split('-', 1)])
    #     return super(CTimeInput, self).insert_text(s, from_undo=from_undo)


# noinspection PyIncorrectDocstring
class BTextInput(CTextInput):
    """
    A ctextinput widget with a border and dropdown
    (Widget defined in kv string)
    """
    #data = None
    crvcolor = CrvColor()

    def __init__(self, **kwargs):
        super(BTextInput, self).__init__(**kwargs)

        self.blayout = kwargs['blayout']
        self.data = kwargs['data']

        self.readonly = kwargs['readonly']
        self.defreadonly = self.readonly
        if self.readonly:
            self.is_focusable = False
        self.togreadonlyvalue = True  # initially set readonly
        self.disabledropdown = False

        if kwargs.has_key('font_size'):
            self.font_size = kwargs['font_size']
        else:
            #font_size = StringProperty(modglobal.default_font_size)
            self.font_size = modglobal.default_font_size

        ###if not self.readonly: self.keyboard_mode = 'managed'

        self.dropdown = None
        self.myid = ''
        self.dropoptions = None
        self.lastdropoptions = []
        self.blocknext = False
        #self.blockdropdown = False # this is set in parent - have to think of a way of getting it.
        self.usedynamic = True
        self.postcall = None
        self.havesettext = False
        self.dosave = False
        self.deletebutton = None

        self.bind(focus=self.on_focus)

        self.justdismissed = False
        self.keyboard_up = False

        self.setcolors()
        self.dropdown = CustomDropDown(auto_dismiss=True, dismiss_on_select=True)
        self.dropdown.bind(on_dismiss=self.callbackdropdowndismiss)

        self.drophints = []
        App.get_running_app().bind(daynight = self.switchDayNight)

        #self.dropdown = DropDown(auto_dismiss=True, dismiss_on_select=True)

    # def dropdown_on_dismiss(self, instance):
    #     Logger.debug('CRV: dropdown_on_dismiss..', self.text)
    #     self.closehints()
    #     return True

    def on_focus(self, w, value):
        #ret=True
        if value:
            Logger.debug('CRV: User focused')
            #self.readonly = True
            #ret=False
        else:
            Logger.debug('CRV: User defocused')
            self.readonly = self.defreadonly
            self.disabledropdown = False
        #return ret

    def on_double_tap(self):
        Logger.debug('CRV: double tap')
        self.disabledropdown = not self.disabledropdown
        self.dismissdropdown(self)
        self.readonly = self.defreadonly
        if not self.readonly: super(BTextInput, self)._ensure_keyboard()

    def settext(self, t, block=True):
        # set text on a dropdown - as this will trigger a dropdown
        # to happen (even during initialisation), we try to block it
        # with the block variable. However, only do this if
        # self.data.sm is None or self.data.sm.current is not screen_main
        #
        Logger.debug('CRV: settext ')
        doblock = False
        if block:
            if self.data is not None:
                if self.data.sm is not None:
                    if self.data.sm.current != 'screen_main': doblock=True

        if doblock: self.blocknext = block
        self.text = t

    def settextanddrop(self, instance, t):
        Logger.debug('CRV: settextanddrop ')
        self.text = t
        instance.focused = True
        self.bdynamicdropdowncallbacktext(instance, t)

    def setcolors(self):
        self.color = self.crvcolor.getfgcolor()
        self.background_color = self.crvcolor.getbgcolor()
        self.dimcol = self.crvcolor.getdimcolor()
        self.boldcol = self.crvcolor.getboldcolor()

    def switchDayNight(self,inst,daynight):
        self.setcolors()

    def hintpress(self, value):
        Logger.debug('CRV: hintpress.. ' + value)
        self.focus = True
        modglobal.alstatusbarclick = value
        self.bdynamicdropdowncallbacktext(self, value)
        #self.selectanddismiss(value)

    def dropopen(self, instance):
        Logger.debug('CRV: dropopen. mode..' + str(self.keyboard_mode))
        if self.keyboard_mode == 'managed' and self.justdismissed:
            Logger.debug('CRV: showkeyboard')
            if not self.readonly:
                self.show_keyboard() ## raise the keyboard on android
                self.keyboard_up = True
        self.justdismissed = False

        # _win = instance.get_parent_window()
        # if _win is not None and instance.focused:
            # set dropdown hints in alternate statusbar
        self.data.openhints(self, self.drophints, self.hintpress)
        instance.dropdown.open(instance)

    def callbackdropdowndismiss(self, instance):
        self.justdismissed = True
        Logger.debug('CRV: callbackdropdowndismiss')

    def dismissdropdown(self, instance):
        _win = self.get_parent_window()
        #if _win is not None and instance.focused:
        if _win is not None:
            Logger.debug('CRV: dismissdropdown')
            self.data.closehints()
            instance.dropdown.dismiss()

    def selectanddismiss(self, value, blank=False):
        # sets the selected value from the dropdown
        Logger.debug('CRV... selectanddismiss')
        if blank: value = ''
        self.dropdown.select(value)
        self.data.closehints()
        self.dropdown.dismiss(self)

    def dcallbackfocus(self, instance, value):
        if instance.collide_point(*value.pos):
            Logger.debug('CRV: dcallbackfocus ' + str(value) + ' ' + instance.parent.children[1].text)
            v = instance.text
            self.bdynamicdropdowncallbacktext(instance, v)
            #self.dropopen(instance)
        else:
            pass
            #Logger.debug('CRV: POS: No Collide')
            #self.closehints()

        _win = instance.get_parent_window()
        if _win is not None and (instance.focused or self.readonly):
            if self.dosave:
                self.data.shelf_save_current()

        return True

    def dcallbackvalidate(self, instance):
        Logger.debug('CRV: dcallbackvalidate ' + instance.text)
        _win = instance.get_parent_window()
        if _win is not None and (instance.focused or self.readonly):
            instance.dismissdropdown(instance)
        if self.keyboard_up:
            self.hide_keyboard()
            self.keyboard_up = False

        return True

    def dcallbackunfocus(self, instance):
        Logger.debug('CRV: dcallbackunfocus ' + instance.text)
        #_win = instance.get_parent_window()
        #if _win is None:
        #    instance.dismissdropdown()
        #return True

    def dcallbacktext(self, instance, value):
        Logger.debug('CRV: ===== dcallbacktext:' + value + ':')
        #_win = instance.get_parent_window()
        #if _win is not None:
        #    instance.dismissdropdown()
        #return True

    def bdynamicdropdowncallbacktext(self, instance, value):
        """
        Called from a dropdown - can dynamically alter dropdown list based on input.
        """
        Logger.debug('CRV: db.... ')
        _win = instance.get_parent_window()
        if _win is None or self.disabledropdown:
            return True

        if self.blocknext:
            self.blocknext = False
            return True

        l = len(value)
        #Logger.info('CRV: value is ' + value)
        if l > 0:
            Logger.debug('CRV: dynamicdropdowncallbacktext ' + value)
            if self.readonly:
                if len(modglobal.alstatusbarclick) == 0:
                    l = 0
            else:
                if self.deletebutton is None and self.blayout is not None:
                    self.deletebutton = MyButton(text='X', height=self.height, size_hint_x=None, width=40)
                    self.blayout.add_widget(self.deletebutton)
                    self.deletebutton.bind(on_release=lambda dbtn:self.settextanddrop(instance, ''))
        else:
            if self.deletebutton is not None and self.blayout is not None: # !a & !b = !(a|b)
                self.blayout.remove_widget(self.deletebutton)
                self.deletebutton = None

        modglobal.alstatusbarclick = ''

        # if something has been typed, try to create a submenu based on the input.
        dopts = instance.dropoptions
        if l > 0:
            d1 = []
            lvalue = value.lower()
            for o in dopts:
                if o.lower().find(lvalue) == 0:
                    d1.append(o)
            #Logger.debug('CRV... custom dopts...' + str(d1))
            n = instance.setdropoptions(d1, instance=instance, full=False)
        else:
            # otherwise use all the options.
            n = instance.setdropoptions(dopts, instance=instance, full=True)

        #if not self.blockdropdown:
        #Logger.info('CRV: n is ' + str(n))
        try:
            if n > 0:
                # if not ((not self.data.haveopenedlog) or self.blockdropdown):
                if not self.data.openingLog:
                    #Logger.info('CRV: openinglog is false')
                    _win = instance.get_parent_window()
                    if _win is not None:
                        if instance.focused or instance.readonly:
                            #Logger.info('CRV... trying to dropdown open')
                            self.dropopen(instance)
            else:
                instance.dismissdropdown(instance)
        except:
            Logger.info('CRV: dropdown exception')

        if self.postcall is not None:
            if len(value) > 0:
                Logger.debug('CRV: postcall. value ' + value)

                #self.data.closehints()
                self.postcall(value)

        return True

    def setid(self, i):
        self.myid = i

    def setcallbacks(self):
        self.bind(on_touch_up=self.dcallbackfocus)
        if self.usedynamic:
            self.bind(text=self.bdynamicdropdowncallbacktext)
        self.bind(on_text_validate=self.dcallbackvalidate)

    def setdropdefaults(self, droptext):
        #Logger.debug('CRV: setdropdef ')
        self.dropoptions = droptext
        #Logger.debug('CRV: end setdropdef ')

    def setdropoptions(self, droptext, instance=None, full=True):
        #
        # Add dropdown options based on droptext args.
        # Return number of matches (i.e. length of dropdown)
        #
        # This is creating the menu to show in the dropdown.
        # If its readonly (and full is true) then we it wont
        # change, so dont bother recreating it.
        #
        if len(droptext) == 0:
            return
        #Logger.debug('CRV: setdropopts ')
        if instance is not None:
            if not self.readonly:
                _win = instance.get_parent_window()
                if _win is not None:
                    if not instance.focused:
                        #Logger.debug('CRV: setdropopts not focused')
                        return

        #Logger.debug('CRV: setdropopts focused')
        lenlast = len(self.lastdropoptions)
        lenthis = len(droptext)

        doit = False
        if lenthis > 0:
            if lenlast == 0:  # if we havent created menu before then do it now
                doit = True
            else:  # compare droptext and self.lastdropoptions. If they are the same then dont rebuild
                if droptext != self.lastdropoptions:
                    doit = True

        if full and doit:
            self.drophints = []

        #if lenthis > 0:
        if doit:
            if self.dropdown:
                _win = self.get_parent_window()
                #if _win is not None and (self.focused or self.readonly):
                if _win is not None:
                    #Logger.debug('CRV... clear drop')
                    #if not self.readonly and full:
                    #    self.dropdown.clear_widgets()
                    self.dropdown.clear_widgets()

                    for o in droptext:
                        if lenthis == -1:   # -1 to just stop it going into the code
                            b = BoxLayout(orientation='horizontal')
                            btn = MyButton(text=o, size_hint_y=None, font_size=modglobal.default_menu_font_size)
                            b.add_widget(btn)
                            btn.bind(on_release=lambda dbtn: self.selectanddismiss(dbtn.text))
                            btnx = MyButton(text='X', size_hint_y=None, font_size=modglobal.default_menu_font_size)
                            b.add_widget(btnx)
                            btnx.bind(on_release=lambda dbtn: self.selectanddismiss(dbtn.text, True))
                            self.dropdown.add_widget(b)
                        else:
                            btn = MyButton(text=o, size_hint_y=None, font_size=modglobal.default_menu_font_size)
                            btn.bind(on_release=lambda dbtn: self.selectanddismiss(dbtn.text))
                            self.dropdown.add_widget(btn)
                        if full:
                            self.drophints.append(o[0])
                    self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))
                    self.lastdropoptions = droptext
        #Logger.debug('CRV: length of hint: ' + str(len(self.drophints)))
        return lenthis

class CrewGridEntry(CTextInput):
    coords = ListProperty()

class CrewGridCheck(CCheckBox):
    coords = ListProperty()

class ActGridEntry(MyTextInput):
    coords = ListProperty()

class ButtonGridEntry(Button):
    coords = ListProperty()

#
# ==================================================================
# CLASS... CrvLogBook
# ==================================================================
#
class CrvLogBook:
    """
    The logbook is essentially putting displaying the correct log in the scrollable grid.
    There are a number of different log types (see below),
    Each log has in common, "time", "type", "from" and "to"
    Type is one of L(og), (I)ncident, (F)ault, (M)aint
    However, there it diverges, and each type have different fields.

    Boat log:     "Activity", "notess"

    Examples: (blank means no entry). | just to separate fields. Last field consists of items seperated by ;
    11:09 |L| howick   | matiatia | launch       | helm:al; nav:john
    11:42 |L| matiatia  |          | on station   | train: john,radio

    Incident log: "Arrived", "Activity (or Reason)", "inc#", "notes"

    Examples: (blank means no entry). | just to separate fields. Last field consists of items seperated by ;
    Note: notess will be taken from incident sheet
    12:06 |I| matiatia  | bean rock| boat sinking | pob:2;a:2;c:0;vessel:haynes,22ft
    12:20 |I| bean rock |          | on scene
    12:22 |I|           |          | pumping
    12:30 |I|           | hmb      | under tow


    Fault log: Same as boat log - activity is the fault

    Examples: (blank means no entry). | just to separate fields. Last field consists of items seperated by ;
    11:42 |F| matiatia  |          | Radar broken | action:restarted electrics

    Maintenance log: Again similiar to boat log

    Examples: (blank means no entry). | just to separate fields. Last field consists of items seperated by ;
    11:42 |M| 36 12.33  |          | Swing compass | result: needs more work

    """

    activity = {}

    def __init__(self, indata, increw, ingps):
        self.data = indata
        self.crew = increw
        self.gps = ingps

        self.layout = None
        self.scrollroot = None
        self.currentrow = -1
        self.savecolor = None
        self.lenactivity = 0
        self.testvar = 0
        self.savewdth = 0
        self.data.initcurrentlog()
        self.doneread = False
        #self.logindex = ['logtime', 'logtype', 'logfrom', 'logto', 'LOG']
        self.logindex = ['logtime', 'logtype', 'loglocation', 'loghelm', 'lognav', 'LOG']
        self.logindexlog = ['logarrived', 'logincident', 'loghelm', 'lognav', 'logtype', 'logaction', 'logresult']

        self.head = {0: 'Time', 1: 'Type', 2: 'Location', 3: 'Helm', 4: 'Nav', 5: 'LOG'}
        self.lenactivity = len(self.logindex)

        self.locations = []
        self.lenlocations = 0

        self.changelogbytype = None
        self.changeactionbytype = None

        self.logviewtoggle = False

        # store locations... see readlocations below
        # used for fast input of locations

    def setchangetypes(self, cl, ca):
        self.changelogbytype = cl
        self.changeactionbytype = ca

    def readlocations(self):
        """
        Look for file locations.txt
        If it exists, then read into self.locations

        This list is dynamic - new locations are appended, sorted and
        saved.
        """

        if self.doneread:
            return
        self.doneread = True

        self.locations = []
        afile = os.path.join(self.data.datadir, 'locations.txt')
        try:
            with open(afile) as f:
                self.locations = f.read().splitlines()
            f.close()

            Logger.info('CRV: Read locations file ' + afile)
        except IOError as e:
            Logger.info("CRV: Failed to read locations.txt".format(e.errno, e.strerror))

        self.lenlocations = len(self.locations)
        if self.lenlocations > 0:
            self.locations.sort()

    def savelocations(self):
        if self.lenlocations > 0:
            afile = os.path.join(self.data.datadir, 'locations.txt')
            try:
                with open(afile, 'w') as f:
                    for l in self.locations:
                        if len(l) > 0:
                            f.write(l + '\n')
                f.close()

                Logger.info('CRV: Wrote locations file ' + afile)
            except IOError as e:
                Logger.info("CRV: Failed to write locations.txt".format(e.errno, e.strerror))

    def doclear(self):
        self.layout.rows = 1
        self.layout.clear_widgets()
        self.data.initcurrentlog()
        self.data.logrecord.logvalues = []

    def log_grid_recover(self):
        """
        Recover grid from logvalues
        """
        if len(self.data.logrecord.logvalues) > 0:
            # to stop logs being duplicated in self.data.setsinglelogvalue
            #  - called in log_add_gridentry
            self.data.openingLog = True
            self.data.logrecord.haveopenedlog = False
            cnt = 0
            for n in self.data.logrecord.logvalues:
                self.do_add_boatlog(n)
            self.data.openingLog = False
            self.data.logrecord.haveopenedlog = True

    def grid_click(self, instance, touch):
        if instance.collide_point(*touch.pos):
            #
            # If you click on an activity row - and it isn't empty, then
            # that row becomes the active row - and the current data is populated
            # from the grid data.
            #
            row = instance.coords[0]
            Logger.debug('CRV: GRID: Click: row: '+ str(row))
            if row > 0:
                row -= 1  # for some reason - first row is always zero - then further rows start from 2

            if row > 0:  # ignore first row - it's a title row
                empty = True
                tmp = self.data.getcurrentlog(row)
                if tmp is not None:
                    for n in range(self.lenactivity-1):
                        if len(tmp[n].text) > 0:
                            empty = False
                            self.currentrow = row
                            break

                    if not empty:
                        for n in range(self.lenactivity-1):
                            self.data.logrecord.setobjecttext(self.logindex[n], tmp[n].text)
                        ltype = self.data.logrecord.getobjecttext(self.logindex[1])
                        self.parse_log_column(ltype, tmp[self.lenactivity-1].text)
                    else:
                        pass

        return True  # Indicates you have handled the event

    def log_add_gridentry(self, inrow, in_t, updlogval=True):
        Logger.debug("CRV: log_add_gridentry: row=%s", str(inrow))

        row = inrow
        grid_line = [None] * self.lenactivity  # the whole row

        grid_text = {}

        # adding a new row - add it to end
        if row < 0:
            row = self.layout.rows
            self.layout.rows += 1
        # adding header
        elif row == 0:
            self.layout.rows += 1
        # changing an existing row
        else:
            pass

        addtherow = True

        try:
            for column in range(self.lenactivity):
                # the toggle code has ben abandoned for now
                # however, we will probably need a second grid layout and just toggle between them
                # thiscol = -1
                # if self.logviewtoggle:
                #     if column in [0,5]:
                #         if column == 0:
                #             thiscol = 0
                #         else:
                #             thiscol = 1
                #     else:
                #         thiscol = -1
                # else:
                #     thiscol = column
                thiscol = column

                if row == 0:
                    grid_entry = ActGridEntry(coords=(row, thiscol), size_hint_y=None, height=modglobal.gridheight,
                                              readonly=True)
                else:
                    grid_entry = ActGridEntry(coords=(row, thiscol), size_hint_y=None, height=modglobal.gridheight*2, readonly=True)

                # this is forming the gridline
                # grid_entry is the actual grid cell that is added to the grid
                # grid_line is an array for the whole grid row (containing the widgets)
                # grid_text is just the text of each cell

                # grid_line and grid_text must contain the whole row - as it's used elsewhere.
                # however, based on the value of logviewtoggle, we either want to display the whole row
                # or just the time and the comment
                #
                grid_entry.bind(on_touch_up=self.grid_click)
                grid_entry.is_focusable = False
                grid_entry.readonly = True

                grid_line[column] = grid_entry
                grid_line[column].text = in_t[column]
                grid_text[column] = in_t[column]
                grid_entry.text = in_t[column]
                grid_entry.cursor = tuple([0,0])

                # the toggle code has been abandoned for now
                # if self.logviewtoggle:
                #     if column in [0,5]:
                #         self.layout.add_widget(grid_entry)
                # else:
                #     self.layout.add_widget(grid_entry)
                self.layout.add_widget(grid_entry)

                if self.scrollroot is not None: self.scrollroot.scroll_y = 0
        except GridLayoutException:
            Logger.info('CRV: GRID:LOG..Layout exception: rows, current..'+str(self.layout.rows) + ' ' + str(self.currentrow))

        # update the logvalues (text)
        if updlogval:
            self.data.setsinglelogvalue(-1, grid_text)

        # update matrix of grid widgets (as I cant figure out how to iterate a grid)
        self.data.appendcurrentlog(grid_line)

    def scrollwidget(self, wdth):
        self.create(wdth)
        self.scrollroot = ScrollView(size_hint=(1, 1), size=(wdth, 500), bar_width=14, scroll_type=['bars','content'])
        self.scrollroot.add_widget(self.layout)
        return self.scrollroot

    # def toggle_logview(self, instance):
    #     self.logviewtoggle = not self.logviewtoggle
    #     self.log_grid_recover()
    #     if instance is not None: instance.clickup()

    def add_head(self):
        addhead = True
        if len(self.data.logrecord.logvalues) > 0:
            if  self.data.logrecord.logvalues[0][0] == self.head[0]:
                addhead = False
        self.log_add_gridentry(0, self.head)

    def create(self, wdth):
        self.currentrow = -1
        self.layout = GridLayout(cols=self.lenactivity, rows=1, padding=0, size_hint_x=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # adding a header. The header may be already there if a log is restoring, so check.
        self.add_head()
        self.savewdth = wdth

    def render_log_column(self, infolog=None):
        """
        Renders the LOG column from data
        Find current log type and get all the columns for the group of that logtype.
        For each one, extract the 'defvalue' text and build up a log using,

        defvalue=value; defvalue=value

        Note: an info log just forces it's way through and adds an info= line
        plus gps. Used, e.g. when incident is closed

        :return
        rendered string, dict of values, filled
        where filled is a boolean - True - there was something in the rendered log, False else
        (doesnt incude gps)
        """
        global thisindex
        tmplog = ''
        filled = False
        thisindex = ''

        rendereddict = {}

        if infolog is not None:
            thislog = 'dummy'
        else:
            thislog = self.data.logrecord.getobjecttext('logtype')

        if thislog is not None and thislog != '':
            if infolog is None:
                inctypes = []
                if thislog == 'Incident':
                    for n in self.data.logrecord.loggroup['logtypesincdisp']:
                        inctypes.append(n)
                inctype = ''

                if self.data.logrecord.loggroup['logtypesdisp'].has_key(thislog):
                    thisindex = self.data.logrecord.loggroup['logtypesdisp'][thislog]
                    for index in self.data.logrecord.getloggroup(thisindex):
                        t = self.data.logrecord.getobjecttext(index)
                        if t in inctypes:
                            inctype=t.lower()
                        k = self.data.logrecord.getvaluekey(index)

                        if len(t) > 0:
                            filled = True
                            if tmplog != '': tmplog += ';'
                            t = t.replace(';', ':')  # to make life easier
                            t = t.replace('=', '-')  # to make life easier
                            tmplog += k+'='+t
                            rendereddict[k] = t

                # If log type is Incident, then we have more to display.
                # The type of incident log will be stored in inctype (above)
                # The list of variables used in that type will be in the index
                # logtypeinc+logtype
                if inctype != '':
                    l = 'logtypeinc'+inctype
                    thisindexinc = self.data.logrecord.loggroup[l]
                    if thisindexinc is not None:
                        if len(thisindexinc) > 0:
                            for index in thisindexinc:
                                t = self.data.logrecord.getobjecttext(index)
                                k = self.data.logrecord.getvaluekey(index)

                                # If we have a dictionary index on the logrecord
                                # called 'act' then it will point to an incident record.
                                # If it exists, update it.

                                try:
                                    if self.data.logrecord.record[index].has_key('inc'):
                                        incindex = self.data.logrecord.record[index]['inc']
                                        if modglobal.crvincidentmain is not None:
                                            if modglobal.crvincidentmain.numincidents > 0:
                                                incnumber = modglobal.crvincidentmain.currentincident
                                                increc = modglobal.crvincidentmain.currentincidents[incnumber]['record']
                                                if incindex in increc.record:
                                                    increc.setobjecttext(incindex, t)
                                except:
                                    Logger.info('CRV: renderlog: Failed to render boat log to incident log for index ' + str(index))

                                if len(t) > 0:
                                    filled = True
                                    if tmplog != '': tmplog += ';'
                                    t = t.replace(';', ':')  # to make life easier
                                    t = t.replace('=', '-')  # to make life easier
                                    tmplog += k+'='+t
                                    rendereddict[k] = t
            else:   # an info log
                if tmplog != '': tmplog += ';'
                t = infolog.replace(';', ':')  # to make life easier
                t = t.replace('=', '-')  # to make life easier
                tmplog += 'info='+t

            #
            # add gps position to tmplog with keys lat and long

            latlong = self.gps.gps_location
            if len(latlong) > 0:
                [lat, lon] = latlong.split(':', 2)
                if self.logviewtoggle:
                    if tmplog != '': tmplog += ';'
                    tmplog += 'lat='+lat
                    tmplog += ';long='+lon
                rendereddict['lat'] = lat
                rendereddict['long'] = lon

            # why doesnt python have a case statement
            # If index is logtypecrew then we are adding a crew member.
            # in this case, tmplog will be:
            # name=aname;IMSAFE=true|false
            # we also have to add this new crew to the crew list.
            # Probably not the best way of doing it - but we need to reparse the string
            # to get values.

            if thisindex == 'logtypecrew':
                newcrew = []
                n = ''
                i = ''
                for x in tmplog.split(';'):
                    filled = True
                    t = x.split('=')
                    if t[0] in ['name', 'IMSAFE']:
                        if t[0] == 'name':
                            n = t[1]
                        else:
                            i = t[1]
                newcrew = [ n, i]

                self.crew.do_save_crew(newcrew)
        return tmplog, rendereddict, filled

    def parse_log_column(self, ltype, logstr):
        """
        Parses the current row and writes to data record
        Opposite of the render code.
        We have a string act=boo; comm=oops
        and have to parse it back to the appropriate fields in the log record
        """
        tmplog = ''

        if ltype is not None:
            try:
                logs = []
                for x in logstr.split(';'):
                    logs.append(x.split('='))
            except:
                Logger.info('CRV: Error splitting log in parse_log_column')
                return

            # All the relevant items for this log are now in logs.
            # If it is an incident log, then treat it separately.

            inctypes = []
            if ltype == 'Incident':
                try:
                    sexc = 'filling from logtypesincdisp'
                    # get the incident fields to fill in.
                    for n in self.data.logrecord.loggroup['logtypesincdisp']:
                        inctypes.append(n)

                    # look for 'act' in log (should be element 0). This
                    # defines the type of incident.

                    sexc = 'getting inctype'
                    inctype = ''
                    for i in logs:
                        if i[0] == 'act':
                            inctype = i[1].lower()

                    # if inctype is empty, then not much we can do
                    if inctype != '':
                        # we want to load the correct incident type
                        sexc = 'changing logtype'
                        self.changelogbytype('Incident')
                        sexc = 'changing actiontype'
                        self.changeactionbytype(inctype)

                        l = 'logtypeinc'+inctype
                        sexc = 'parsing logtypeinc ' + l
                        thisindexinc = self.data.logrecord.loggroup[l]
                        if thisindexinc is not None:
                            if len(thisindexinc) > 0:
                                for index in thisindexinc:
                                    k = self.data.logrecord.getvaluekey(index)

                                    sexc = 'looping logs for key ' + k
                                    for index1 in logs:
                                        if k == index1[0]:
                                            obj = self.data.logrecord.getobject(index)
                                            if type(obj).__name__ == 'list':
                                                # will be a CCheckBox. We want to set the
                                                # .active part of element 0
                                                if index1[1] in [ 'True', 'true' ]:
                                                    obj[0].active = True
                                                else:
                                                    obj[0].active = False
                                            else:
                                                obj.text = index1[1]
                except:
                    Logger.info('CRV: parse_log_column: handling Incident' + sexc)
                    return
            else:
                try:
                    thisindex = self.data.logrecord.loggroup['logtypesdisp'][ltype]

                    for index in self.data.logrecord.getloggroup(thisindex):
                        # get the key for the index
                        k = self.data.logrecord.getvaluekey(index)

                        for index1 in logs:
                            if k == index1[0]:
                                obj = self.data.logrecord.getobject(index)
                                if type(obj).__name__ == 'list':
                                    # will be a CCheckBox. We want to set the
                                    # .active part of element 0
                                    if index1[1] in [ 'True', 'true' ]:
                                        obj[0].active = True
                                    else:
                                        obj[0].active = False
                                else:
                                    obj.text = index1[1]
                except:
                    Logger.info('CRV: parse_log_column: handling log')

    def setdefaultsbytype(self, value=None):
        #
        # Depending on the type of log, set some sensible
        # defaults.
        # e.g. If there are entries in the grid,
        # logtype is set to last logtype
        # logfrom is set to last logto
        # logboatactivity is set to last boatactivity
        #
        # If we are in an incident then set activity to Incident
        #
        # get last logtype
        # Returns the type of log.
        #
        if len(self.data.logrecord.logvalues) > 0:
            # get last logvalue
            # 0: date
            # 1: type
            # 2: location
            # 3: helm
            # 4: nav
            # 5: log
            logd = self.data.logrecord.logvalues[-1]
            dtime = logd[self.data.logrecord.commonlogtime]
            dtype = logd[self.data.logrecord.commonlogtype]     # logtype
            w = self.data.logrecord.getobject('logtype')
            if dtype == 'Launch': # log not empty and already launched, so set it to 'Log'
                dtype = 'Log'

            w.settext(dtype)
            dlocation = logd[self.data.logrecord.commonlogloc] # loglocation
            w = self.data.logrecord.getobject('loglocation')
            w.settext(dlocation, False)
            dhelm   = logd[self.data.logrecord.commonloghelm]   # loghelm
            w = self.data.logrecord.getobject('loghelm')
            w.settext(dhelm, False)
            dnav   = logd[self.data.logrecord.commonlognav]    # lognav
            w = self.data.logrecord.getobject('lognav')
            w.settext(dnav, False)

            # this was a bad idea
            # if dtype == 'Fuel':
            #     # get the log string and parse it to create a dictionary
            #     # of keys and values. This is similiar to what the function
            #     # render_log_column does - we can then pass the dictionary to handlelogfuel
            #     # to setup fuel defaults. Bit long winded, but thems the breaks.
            #     #
            #     tmplog = logd[5]
            #     rendereddict = {}
            #     for x in tmplog.split(';'):
            #         t = x.split('=')
            #         rendereddict[t[0]] = t[1]
            #     self.handlelogfuel(rendereddict)

            #dlog  = logd[5]

            #logs = []
            #dact=''

            # Set dtype, dlocation, dhelm and dnav values

            # if len(dlog) > 0:
            #     for x in dlog.split(';'):
            #         l = x.split('=')
            #         if l[0] == 'act':
            #             dact = l[1]
            #             break
            #
            #     #w = self.data.logrecord.getobject('logfrom')
            #     #w.text = dto
            #     #w = self.data.logrecord.getobject('logtype')
            #     #w.text = dtype
            #     #w = self.data.logrecord.getobject('logboatactivity')
            #     #w.text = dact
            # else: # empty log - must be launching. Set logboatactivity to Launch
            #     w = self.data.logrecord.getobject('logtype')
            #     w.text = 'Launch'
        else: # empty log - must be launching. Set logboatactivity to Launch
            w = self.data.logrecord.getobject('logtype')
            w.settext('Launch')
            #w.text = 'Launch'

        if modglobal.crvincidentmain is not None and modglobal.crvincidentmain.numincidents > 0:
            #w = self.data.logrecord.getobject('logtype')
            #w.text = 'Incident'
            self.changelogbytype('Incident')

        return True

    def handlelogfuel(self, rendereddict):
        vesselfuel = self.data.currvessel[self.data.datarecord.managevesselfueltype]
        if rendereddict.has_key('type'):
            if rendereddict['type'] == vesselfuel:
                sadded = 'fueladded'
                sprice = 'fuelprice'
            else:
                sadded = 'fuelsuppliedadded'
                sprice = 'fuelsuppliedprice'

            added = self.data.to_number(self.data.datarecord.getobjecttext(sadded))
            if self.data.is_number(added):
                if rendereddict.has_key('added'):
                    logadded = rendereddict['added']
                    if self.data.is_number(logadded):
                        toadd = float(added) + float(logadded)
                        self.data.datarecord.setobjecttext(sadded, str(toadd))
            # if 'fuelprice' is empty, then copy logfuelprice to fuelprice
            price = self.data.to_number(self.data.datarecord.getobjecttext(sprice))
            if price > 10:
                price /= 100.0
                self.data.datarecord.setobjecttext(sprice, str(price))

            if price == 0.0:
                if rendereddict.has_key('price'):
                    logprice = rendereddict['price']
                    if self.data.is_number(logprice):
                        self.data.datarecord.setobjecttext(sprice, logprice)

    def doinfolog(self, infomsg):
        try:
            logtosave = [''] * self.lenactivity
            n = self.lenactivity - 1
            logtosave[1] = 'Log'
            logtosave[n], rendereddict, filled = self.render_log_column(infolog=infomsg)
            self.do_add_boatlog(logtosave, isinfo=True)
        except:
            Logger.info('CRV: infolog. Failed to log: ' + infomsg)

        try:
            self.data.audit.writeaudit(infomsg)
        except:
            Logger.info('CRV: Failed to audit infolog: ' + infomsg)

    def callback_save_boatlog(self, instance):
        #
        # save everything in activity to grid
        # if currentrow not set (-1) - then add a new one
        # else save to that row
        #
        if self.data.currvessel is None:
            self.data.crv_populate_vessel()

        logtosave = [None] * self.lenactivity
        for n in range(self.lenactivity-1):
            logtosave[n] = self.data.logrecord.getobjecttext(self.logindex[n])

        n+=1
        logtosave[n], rendereddict, filled = self.render_log_column()

        # If log type is 'fuel'.. logtosave[1]
        # added the 'logfueladded' field to the close log
        # 'fueladded' column (if fuel type is same as vessel).

        if logtosave[1] == 'Fuel':
            self.handlelogfuel(rendereddict)

        self.do_add_boatlog(logtosave, filled)
        self.data.shelf_save_current()
        self.setdefaultsbytype()
        if instance is not None: instance.clickup()

    def do_add_boatlog(self, logtosave, filled=True, isinfo=False):
        # logttosave[0] = 'time', 1='type', 2='from', 3='to'

        # make sure you arent adding a blank row.
        # if time is blank - add it in
        if logtosave[0] == '':
            logtosave[0] = self.data.getnow()
            #logtosave[0] = datetime.datetime.now().strftime("%a %y-%m-%d %H-%M")

        if not isinfo:
            # its empty if entries apart from logtime, logtype and logboatactivity are empty
            empty = True
            # for n in range(self.lenactivity):
            for n in [ self.data.logrecord.commonlogloc, self.data.logrecord.commonloghelm,self.data.logrecord.commonlognav ]:
                if len(logtosave[n]) > 0:
                    empty = False
                    break

            if empty:
                empty = not filled   # got some data from render_log_column
        else:
            empty = False
            self.currentrow = -1

        if not empty:
            if self.currentrow == -1:
                #
                # we are adding data to an empty grid row or adding a new grid row.
                #
                r = -1
                self.log_add_gridentry(r, logtosave)
            else:
                # we are updating an existing row
                Logger.debug("CRV: update activity on row " + str(self.currentrow))
                for i in range(self.lenactivity):
                    self.data.setcurrentlog(self.currentrow, i, logtosave[i])

                ttext = {}
                for c in range(len(logtosave)):
                    ttext[c] = logtosave[c]

                self.data.setsinglelogvalue(self.currentrow, ttext)
                self.currentrow = -1

        if not isinfo:
            # if from field or to field not in locations, then add it and sort
            # (there is probably a more efficient way of doing this)

            oldl = self.lenlocations
            if len(logtosave[self.data.logrecord.commonlogloc]) > 0:
                if logtosave[self.data.logrecord.commonlogloc] not in self.locations:
                    self.locations.append(logtosave[self.data.logrecord.commonlogloc])
                    self.lenlocations += 1
            if oldl != self.lenlocations:
                self.locations.sort()


            # empty log entry fields

            self.currentrow = -1
            self.data.clearcurrentlog(False)

    def callback_cancel(self, instance):
        self.currentrow = -1
        self.data.clearcurrentlog(False)
        self.setdefaultsbytype()
        if instance is not None: instance.clickup()

#
# ==================================================================
# CLASS... CrvLogArchive
# ==================================================================
#
class CrvLogArchive:
    def __init__(self, indata):
        self.data = indata
        self.layout = None
        self.selectedfile = ''
        self.currentrow = -1
        #self.msgbox = None

    @staticmethod
    def grid_click(instance, touch):
        if instance.collide_point(*touch.pos):
            #
            # If you click on an activity row - and it isn't empty, then
            # that row becomes the active row - and the current data is populated
            # from the grid data.
            #
            row = instance.coords[0]
            if row > 0:
                row -= 1  # for some reason - first row is always zero - then further rows start from 2

        return True  # Indicates you have handled the event

    def confirm_no(self, instance):
        Logger.debug('CRV: NO')
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()

    def confirm_delete(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        if self.selectedfile != '':
            dfile = os.path.join(self.data.datadir, self.selectedfile) + '.JSON'
            self.data.shelf_delete(dfile)
            self.populate()

    def grid_delete(self, afile):
        self.selectedfile = afile
        modglobal.msgbox = MessageBox(self, titleheader="Confirm delete\n" + self.selectedfile,
                   message="Deleting log.\n" + afile + "\nARE YOU SURE??",
                   options={"YES": self.confirm_delete, "NO": self.confirm_no})

    def grid_check(self, afile):
        dfile = os.path.join(self.data.datadir, afile)

    def add_gridentry(self, row,  in_t):

        try:
            candelete = True
            if in_t[0][0:3] == 'INC' or (in_t[0][0:11] == 'CURRENTLOG.' and self.data.getlogactive()):
                candelete = False
            if in_t[2] == '' and in_t[0][0:11] != 'CURRENTLOG.':
                candelete = False

            for column in range(len(in_t)):
                grid_entry = ActGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = in_t[column]
                self.layout.add_widget(grid_entry)
            if row == 0:
                grid_entry = ButtonGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete Log'
                self.layout.add_widget(grid_entry)
            else:
                grid_entry = ButtonGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete'
                f = in_t[0]
                grid_entry.bind(on_press=lambda dbtn: self.grid_delete(f))
                self.layout.add_widget(grid_entry)
                if not candelete: grid_entry.disabled = True
        except GridLayoutException:
            Logger.info('CRV: GRID:ARCHIVE..Layout exception: rows, current..'+str(self.layout.rows) + ' ' + str(row))

    def scrollwidget(self, wdth):
        self.create(wdth)
        root = ScrollView(size_hint=(1, 1), size=(wdth, 500), bar_width=14, scroll_type=['bars','content'])
        root.add_widget(self.layout)
        return root

    def create(self, wdth):

        self.currentrow = -1
        self.layout = GridLayout(cols=4, rows=100, padding=0, size_hint_x=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

    def callback_save_boatlog(self, instance):
        pass

    # def do_add_boatlog(self, logtosave):
    #     pass

    def callback_cancel(self, instance):
        pass

    def populate(self):
        """
        Look for a CURRENTLOG.JSON, parse and display it.
        Then look for all other JSON files
        """
        self.layout.clear_widgets()

        head = ['Filename', 'Log Time', 'Sent Status']
        self.add_gridentry(0, head)

        row = 1
        t = [None, None, None]
        (filename, logtime, senttime) = self.data.shelf_parse(self.data.shelf_file)
        if filename is not None:
            if logtime is not None:
                t[0] = filename
                t[1] = logtime
                t[2] = senttime
                if logtime is None:
                    t[1] = 'BAD FILE'
                else:
                    v = t[1]
                    try:
                        [value,col] = v.split('!', 2)
                    except:
                        value = v
                    t[1] = value
                self.add_gridentry(row, t)

        flist = []
        for afile in os.listdir(self.data.datadir):
            if afile.startswith('LOG') and afile.endswith(".JSON"):
                flist.append(afile)
        flist.reverse()
        for afile in flist:
            thefile = os.path.join(self.data.datadir, afile)
            if thefile != self.data.shelf_file:
                row += 1
                # (filename, logtimepluscolor) = self.data.shelf_parse(thefile)
                (filename, logtime, senttime) = self.data.shelf_parse(thefile)

                # if logtime is None:
                #     logtime = None
                #     col = None
                # else:
                #     pass
                try:
                    [value,ext] = filename.split('.', 2)
                except:
                    value = filename
                t[0] = value
                t[1] = logtime
                t[2] = senttime
                if logtime is None:
                    t[1] = 'BAD FILE'
                else:
                    v = t[1]
                    try:
                        [value,col] = v.split('!', 2)
                    except:
                        value = v
                    t[1] = value
                self.add_gridentry(row, t)

#
# ==================================================================
# CLASS... CRVInncidentMain
# ==================================================================
#
class CrvIncidentMain:
    def __init__(self, inparent, indata, imageinstance=None):
        self.parent = inparent
        self.data = indata
        self.layout = None
        #self.msgbox = None

        # Each incident consists of 3 items,
        # { 'screen': screenobject, 'name': screenname, 'record': thedata }

        # So the screen is a list with each element containing the above dict
        #test.. self.parent.gps.gpsdistance('036 54.583S 174 55.616E', '036 54.783S 174 56.616E')

        self.currentincidents = []
        self.currentincident = -1
        self.numincidents = 0

        self.currentrow = -1

        self.simulationspeed = -1
        self.haveincidents = False

        # We now have to see if there are any unsaved incidents.
        # Look for INCTMP*.JSON
        foundfiles=[]
        for afile in os.listdir(self.data.datadir):
            if afile.startswith('INCTMP'):
                foundfiles.append(afile)
        foundfiles.sort()

        for recover in foundfiles:
            # recover will be in format INCTMPn.JSON
            # extract the n from it and create the
            # incident using that
            s1=recover[6:]
            x=s1.find('.')
            idnum = s1[0:x]
            self.newincident(idnum, imageinstance=imageinstance)

    def inc_shelf_archive(self, incnum, inalerttime):
        '''
        When an incident is closed, it must be archived. (The N is there to stop it being
        recovered in the future)
        '''
        increc = self.currentincidents[incnum]['record']
        increc.inc_shelf_save()

        # The INCTMPn.JSON file will be moved to
        # INCaltertime.JSON

        alerttime = 'INC' + inalerttime + '.JSON'
        alerttime = alerttime.replace(":", "-")
        archivefile = os.path.join(self.data.datadir, alerttime)
        # altertime will have a time format hh:mm which you cant write to a file.
        # so we need to change : to -
        ok = self.data.dorename(False, increc.shelf_file, archivefile)
        if ok:
            self.data.Logger.info('CRV: Archived Incident to ' + archivefile)
        else:
            self.data.Logger.info('CRV: Failed to archive incident ' + self.shelf_file + ' to ' + archivefile)

        return ok, archivefile

    def copydatarec(self, recfrom, recto, value=None):
        # from from datarec to incident.
        # If value not None, then copy value into recto
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']
        if value is None:
            if recfrom != '' and recfrom in self.data.datarecord.record:
                if recto in increc.record:
                    t = self.data.datarecord.getobjecttext(recfrom)
                    increc.setobjecttext(recto, t)
        else:
            increc.setobjecttext(recto, value)

    def inc_checkconclusion(self, instance, *args):
        Logger.debug('CRV:inc_checkconclusion: instance: ' + str(instance))
        ok = True
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        if not increc.haveopenedlog:
            return
        if instance.id == 'success':
            increc.conradio[0].color = self.data.crvcolor.getboldcolor()
            increc.conradio[1].color = self.data.crvcolor.getdimcolor()
            increc.conradio[2].color = self.data.crvcolor.getdimcolor()
            increc.conradio[3].color = self.data.crvcolor.getdimcolor()
            increc.setobjecttext('incresultsuccess', instance.id)
            increc.setobjecttext('incresultsuspended', '')
            increc.setobjecttext('incresultstooddown', '')
            increc.setobjecttext('incresultfatality', '')
            increc.setobjecttext('incstatus', instance.id)
        elif instance.id == 'stooddown':
            increc.conradio[0].color = self.data.crvcolor.getdimcolor()
            increc.conradio[1].color = self.data.crvcolor.getboldcolor()
            increc.conradio[2].color = self.data.crvcolor.getdimcolor()
            increc.conradio[3].color = self.data.crvcolor.getdimcolor()
            increc.setobjecttext('incresultsuccess', '')
            increc.setobjecttext('incresultsuspended', instance.id)
            increc.setobjecttext('incresultstooddown', '')
            increc.setobjecttext('incresultfatality', '')
            increc.setobjecttext('incstatus', instance.id)
        elif instance.id == 'suspended':
            increc.conradio[0].color = self.data.crvcolor.getdimcolor()
            increc.conradio[1].color = self.data.crvcolor.getdimcolor()
            increc.conradio[2].color = self.data.crvcolor.getboldcolor()
            increc.conradio[3].color = self.data.crvcolor.getdimcolor()
            increc.setobjecttext('incresultsuccess', '')
            increc.setobjecttext('incresultsuspended', '')
            increc.setobjecttext('incresultstooddown', instance.id)
            increc.setobjecttext('incresultfatality', '')
            increc.setobjecttext('incstatus', instance.id)
        elif instance.id == 'fatality':
            increc.conradio[0].color = self.data.crvcolor.getdimcolor()
            increc.conradio[1].color = self.data.crvcolor.getdimcolor()
            increc.conradio[2].color = self.data.crvcolor.getdimcolor()
            increc.conradio[3].color = self.data.crvcolor.getboldcolor()
            increc.setobjecttext('incresultsuccess', '')
            increc.setobjecttext('incresultsuspended', '')
            increc.setobjecttext('incresultstooddown', '')
            increc.setobjecttext('incresultfatality', instance.id)
            increc.setobjecttext('incstatus', instance.id)
        elif instance.id == 'inctimearrive':
            t = increc.getobject('inctimearrive')
            if t.text == '':
                t.text = self.data.getnow()

            # calculate total time from start to end
            st = increc.getobjecttext('inctimeunderway')
            st = self.data.doparsedatetime(st)
            en = self.data.doparsedatetime(t.text)
            if not (st is None or en is None):
                try:
                    df = en - st
                except:
                    df = None
                if df is not None:
                    # df will be a datetime, so we have to convert this to seconds
                    seconds   = df.total_seconds()
                    hours = seconds // 3600
                    minutes = (seconds % 3600) // 60
                    seconds %= 60
                    df = '{} Hours, {} Mins'.format(hours, minutes)
                    increc.setobjecttext('inctimetotal', df)
        elif 'fuel' in instance.id:
            if 'fuelsupplied' in instance.id:
                # handle fuel calculations for supplied fuel
                fused = self.data.to_number(increc.getobjecttext('incfuelsupplied'))
                fprice = self.data.to_number(increc.getobjecttext('incfuelsuppliedprice'))
                if fprice > 10:
                    fprice /= 100.0
                    increc.setobjecttext('incfuelsuppliedprice', str(fprice))
                fcost = fused * fprice
                increc.setobjecttext('incfuelsuppliedcost', str(fcost))

            else:
                # handle fuel calculations for crv fuel
                fstart = self.data.to_number(increc.getobjecttext('inccrvfuelstart'))
                fend = self.data.to_number(increc.getobjecttext('inccrvfuelatend'))
                fused = fstart - fend
                increc.setobjecttext('inccrvfuelused', fused)
                fprice = self.data.to_number(increc.getobjecttext('inccrvfuelprice'))
                if fprice > 10:
                    fprice /= 100.0
                    increc.setobjecttext('inccrvfuelprice', str(fprice))
                fcost = fused * fprice
                increc.setobjecttext('inccrvfuelcost', str(fcost))

    def inc_checkadministration(self, instance, *args):
        Logger.debug('CRV:inc_checkadministration: instance: ' + str(instance))
        ok = True
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        if not increc.haveopenedlog:
            return
        increc.inc_shelf_save()

    def inc_checkpayment(self, instance, *args):
        Logger.debug('CRV:inc_checkpayment: instance: ' + str(instance))
        ok = True
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        if not increc.haveopenedlog:
            return
        increc.inc_shelf_save()

    def inc_checkdebrief(self, instance, *args):
        Logger.debug('CRV:inc_checkdebrief: instance: ' + str(instance))
        ok = True
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        if not increc.haveopenedlog:
            return
        increc.inc_shelf_save()

    def inc_checkactivation(self, instance, *args):
        Logger.debug('CRV:inc_checkactivation: instance: ' + str(instance))
        ok = True
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        if not increc.haveopenedlog:
            return

        t = increc.getobject('incalerttime')
        if t.text == '':
            t.text = self.data.getnow()

        if 'incpob' in instance.id:
            a = increc.getobjecttext('incpoba')
            c = increc.getobjecttext('incpobc')
            d = increc.getobjecttext('incpobd')
            try:
                iap = int(a)
            except:
                iap = 0
            try:
                icp = int(c)
            except:
                icp = 0
            try:
                idp = int(d)
            except:
                idp = 0
            pob = iap + icp
            increc.setobjecttext('incpob', str(pob))

        elif instance.id == 'inccrvfuelstart':
            # check fuel start is less than
            # 'fuelstart' + any added
            t = self.data.to_number(increc.getobjecttext('inccrvfuelstart'))
            fuelstart = self.data.to_number(self.data.datarecord.getobjecttext('fuelstart'))
            fueladded = self.data.to_number(self.data.datarecord.getobjecttext('fueladded'))
            cfuel = fuelstart+fueladded
            if cfuel > 0: # if its not then all if ok
                if t > cfuel:
                    colr = self.data.crvcolor.getboldcolor()
                    self.data.dopopup('Warning: You have specified more fuel than should be available (' +
                                      str(t) + '). Max is ' + str(cfuel), bindto=instance)
                    instance.text = str(cfuel)
                else:
                    colr = self.data.crvcolor.getbgcolor()
                increc.getobject('inccrvfuelstart').background_color = colr

        elif instance.id == 'incvesselname':
            t = increc.getobjecttext('incvesselname')
            if t != '':
                # if vessel starts with @nn then use that for speed (for simulation purposes)
                if t[0:1] == '@':
                    try:
                        self.simulationspeed = int(t[1:3])
                        t = t[3:]
                        increc.setobjecttext('incvesselname', t)
                    except:
                        pass # ignore

        elif instance.id == 'inctimeunderway':
            t = increc.getobject('inctimeunderway')
            if t.text == '':
                t.text = self.data.getnow()

        elif 'inclat' in instance.id or 'inclong' in instance.id:
            ilatd = increc.getobjecttext('inclatd')
            ilatm = increc.getobjecttext('inclatm')
            ilongd = increc.getobjecttext('inclongd')
            ilongm = increc.getobjecttext('inclongm')

            if len(str(ilatd)) > 0 and len(str(ilatm)) > 0 and len(str(ilongd)) > 0 and len(str(ilongm)) > 0:
                latlong = str(ilatd) + ' ' + str(ilatm) + 'S:' + str(ilongd) + ' ' + str(ilongm) + 'E'
                increc.setobjectvariable('inclatlong', 'text', latlong)
                Logger.debug('CRV: LATLONG: ' + latlong)

        increc.inc_shelf_save()

    def inc_callback_inchome(self, instance, *args):
        self.inc_checkactivation(instance)
        if self.data.getlogactive():
            self.parent.crv_callback_boatlog(instance)
        else:
            self.parent.crv_callback_home(instance)

    def confirm_closeinc_yes(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        self.cancelincident()
        self.parent.crv_callback_lastscreen(None)

    def confirm_no(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()

    def inc_callback_inccancel(self, instance):
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        t = increc.getobject('incalerttime')
        s = '\nStarted at: ' + t.text
        modglobal.msgbox = MessageBox(self, titleheader="Confirm Cancel This Incident",
                   message="ARE YOU SURE YOU WANT TO CANCEL THIS INCIDENT?" + s,
                   options={"YES": self.confirm_closeinc_yes, "NO": self.confirm_no})

    def inc_callback_checklatlong(self, instance, *args):
        # 36 47.234  174 36.234
        Logger.debug('CRV:checklatlong: instance: ' + str(instance))

        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        if not increc.haveopenedlog:
            return

        thisid = instance.id
        if thisid == 'inclatd':
            ilatd = increc.getobjecttext('inclatd')
            ilatm = increc.getobject('inclatm')
            if len(ilatd) >= 2:
                ilatm.focus = True
                ilatm.select_all()
        elif thisid == 'inclongd':
            ilongd = increc.getobjecttext('inclongd')
            ilongm = increc.getobject('inclongm')
            if len(ilongd) >= 3:
                ilongm.focus = True
                ilongm.select_all()

        ok = True

    def setup_main_screen(self):
        Logger.info('CRV:SETUP:incident main')
        screen_crvincident_main = Screen(name='screen_crvincident_main')

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        header = self.parent.screencreateheader('screen_crvincident_main')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        wdth = box.width
        scrollincmain = self.scrollwidget(wdth)

        middle.add_widget(scrollincmain)

        button1 = MyButton(text='Home')
        button1.bind(on_press=self.parent.crv_callback_home)

        buttonnew = MyButton(text='New Incident')
        buttonnew.bind(on_press=lambda dbtn: self.newincident())

        footer.add_widget(button1)
        footer.add_widget(buttonnew)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_crvincident_main.add_widget(box)
        screen_crvincident_main.bind(on_enter=self.screenincident_callback_onenter)

        return screen_crvincident_main

    def screenincident_callback_onenter(self, instance):
        dopop = True

        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        hact = increc.getobject('inchomebuttonact')
        #hcon = increc.getobject('inchomebuttoncon')
        hadm = increc.getobject('inchomebuttonadm')
        hpay = increc.getobject('inchomebuttonpay')
        hdeb = increc.getobject('inchomebuttondeb')
        if self.data.getlogactive():
            hact.text = 'Go to Log'
#            hexe.text = 'Go to Log'
            hadm.text = 'Go to Log'
            hpay.text = 'Go to Log'
            hdeb.text = 'Go to Log'
        else:
            hact.text = 'Home'
#            hexe.text = 'Home'
            hadm.text = 'Home'
            hpay.text = 'Home'
            hdeb.text = 'Home'

        if not self.haveincidents:
            if self.numincidents > 0:
                self.haveincidents = True
            else:
                dpop = False
            if self.numincidents == 1:
                dopop = False
                self.inc_set_screen('act')
        if dopop:
            self.incpopulate()

    def cancelincident(self):
        # cancel current incident.
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']
        incscreen = self.currentincidents[incnumber]['screen']
        try:
            for s in incscreen:
                sc = incscreen[s]
                self.data.sm.remove_widget(sc)
        except:
            pass
        del increc
        self.currentincidents.pop(self.currentincident)
        self.currentincident -= 1
        self.numincidents -= 1
        if self.numincidents <= 0:
            self.haveincidents = False

    def newincident(self, inidnum=None, imageinstance=None):
        """
        Need to create new incident then
        incpopulate it with essential information
        # Each incident consists of 3 items,
        # { 'screen': screenobject, 'name': screenname, 'record': thedata }

        # So the screen is a list with each element containing the above dict
        """
        #self.numincidents = len(self.currentincidents)
        #self.currentincident = self.numincidents - 1

        increc = CrvIncData(self.data)
        incdict = { 'screen':{}, 'record': increc}
        self.currentincidents.append(incdict)
        self.numincidents = len(self.currentincidents)
        self.currentincident = self.numincidents - 1

        increc.haveopenedlog = False

        # used to identify incident
        if inidnum != None:
            # we are recovering an unsaved log
            increc.inc_shelf_restore(inidnum)
            increc.setobjectvariable('incid', 'text', inidnum)
        else:
            increc.setobjectvariable('incid', 'text', str(self.currentincident))

        # create the activation screen for this incident (self.currentincident)
        crvact = self.setup_incident_activation(self.currentincident)
        self.data.sm.add_widget(crvact)

        self.currentincidents[self.currentincident]['screen']['act'] = crvact

        crvcon = self.setup_incident_conclusion(self.currentincident)
        self.data.sm.add_widget(crvcon)
        self.currentincidents[self.currentincident]['screen']['con'] = crvcon

        crvadm = self.setup_incident_administration(self.currentincident)
        self.data.sm.add_widget(crvadm)
        self.currentincidents[self.currentincident]['screen']['adm'] = crvadm

        crvpay = self.setup_incident_payment(self.currentincident)
        self.data.sm.add_widget(crvpay)
        self.currentincidents[self.currentincident]['screen']['pay'] = crvpay

        crvdeb = self.setup_incident_debrief(self.currentincident)
        self.data.sm.add_widget(crvdeb)
        self.currentincidents[self.currentincident]['screen']['deb'] = crvdeb

        if imageinstance is not None:
            imageinstance.opacity = 10.0

        self.incsreencurrent = 0 # will be activation screen

        # set defaults and recover values (if there is a saved file)

        #increc.setobjecttext('incemailtime', 'UNSENT')
        increc.setobjecttext('incactions', '')
        increc.setobjecttext('incaddress', '')
        t = self.data.getnow()
        increc.setobjecttext('incalerttime', t)
        increc.setobjecttext('incassistactivity', '')
        increc.setobjecttext('incassistauthorise', '')
        increc.setobjecttext('incassistcallsign', '')
        increc.setobjecttext('incassistcolorh', '')
        increc.setobjecttext('incassistcoloro', '')
        increc.setobjecttext('incassistcommstype', '')
        increc.setobjecttext('incassistlength', '')
        increc.setobjecttext('incassistnumengines', '')
        increc.setobjecttext('incassistother', '')
        increc.setobjecttext('incassistpropulsion', '')
        increc.setobjecttext('incassistsignature', '')
        increc.setobjecttext('incassisttype', '')
        increc.setobjecttext('inccardcsv', '')
        increc.setobjecttext('inccardexpiry', '')
        increc.setobjecttext('inccardname', '')
        increc.setobjecttext('inccardnumber', '')
        increc.setobjecttext('inccardtype', '')
        increc.setobjecttext('inccrvto', '')
        increc.setobjecttext('incdepartscene', '')
        increc.setobjecttext('incdirection', '')
        increc.setobjecttext('incemail', '')
        increc.setobjecttext('incexitstrategies', '')

        increc.setobjecttext('inccrvfuelstart', '')
        increc.setobjecttext('inccrvfuelused', '')
        increc.setobjecttext('inccrvfuelprice', '')
        increc.setobjecttext('inccrvfuelcost', '')

        increc.setobjecttext('incfuelsupplied', '')
        increc.setobjecttext('incfuelsuppliedprice', '')
        increc.setobjecttext('incfuelsuppliedtype', '')
        increc.setobjecttext('incfuelsuppliedcost', '')
        increc.setobjecttext('incfueltotalcost', '')

        increc.setobjecttext('inchomephone', '')
        increc.setobjecttext('incisincident', '')
        increc.setobjecttext('incispositioning', '')
        increc.setobjecttext('inclatd', '')
        increc.setobjecttext('inclatm', '')
        increc.setobjecttext('inclatlong', '')
        increc.setobjecttext('inclocationunderway', '')     # calculated
        increc.setobjecttext('inclongd', '')
        increc.setobjecttext('inclongm', '')
        increc.setobjecttext('incmember', '')
        increc.setobjecttext('incmembernum', '')
        increc.setobjecttext('incmission', '')
        increc.setobjecttext('incmnznum', '')
        increc.setobjecttext('incmobile', '')
        increc.setobjecttext('incname', '')
        increc.setobjecttext('incnumber', '')
        increc.setobjecttext('incfemale0010', '')
        increc.setobjecttext('incfemale1120', '')
        increc.setobjecttext('incfemale2130', '')
        increc.setobjecttext('incfemale3140', '')
        increc.setobjecttext('incfemale4150', '')
        increc.setobjecttext('incfemale50plus', '')
        increc.setobjecttext('incmale0010', '')
        increc.setobjecttext('incmale1120', '')
        increc.setobjecttext('incmale2130', '')
        increc.setobjecttext('incmale3140', '')
        increc.setobjecttext('incmale4150', '')
        increc.setobjecttext('incmale50plus', '')
        increc.setobjecttext('incpob', '')
        increc.setobjecttext('incpoba', '')
        increc.setobjecttext('incpobc', '')
        increc.setobjecttext('incpobd', '')
        increc.setobjecttext('incposition', '')
        increc.setobjecttext('incproblem', '')
        increc.setobjecttext('inctimeonscene', '')
        increc.setobjecttext('incstatus', '')
        increc.setobjecttext('incpoliceevent', '')
        increc.setobjecttext('incquotedprice', '')
        increc.setobjecttext('incrccnznumber', '')
        increc.setobjecttext('incresultfatality', '')
        increc.setobjecttext('incresultstooddown', '')
        increc.setobjecttext('incresultsuccess', '')
        increc.setobjecttext('incresultsuspended', '')
        increc.setobjecttext('incsap100a', '')
        increc.setobjecttext('incsap100b', '')
        increc.setobjecttext('incseastate', '')             # calculated
        increc.setobjecttext('inctakento', '')
        increc.setobjecttext('inctakentotime', '')
        increc.setobjecttext('inctide', '')                 # calculated
        increc.setobjecttext('inctimearrive', '')
        increc.setobjecttext('inctimetotal', '')
        increc.setobjecttext('inctimeunderway', '')
        increc.setobjecttext('incvesselcallsign', '')       # calculated
        increc.setobjecttext('incvesselname', '')
        increc.setobjecttext('incvesselskipper', '')        # calculated
        increc.setobjecttext('incvisibility', '')           # calculated
        increc.setobjecttext('incwindspeed', '')            # calculated
        increc.setobjecttext('incworkphone', '')

        increc.haveopenedlog = True
        self.inc_set_screen('act')
        #self.screenincident_callback_onenter(None)

    def inc_set_screen(self, insname):
        #sname = 'screen_crvincident_' + insname + str(self.currentincident)
        incscreen = self.currentincidents[self.currentincident]['screen']
        sname = incscreen[insname]
        self.data.sm.current = sname.name

    def setup_incident_activation(self, incnumber):
        sincnumber = str(incnumber)
        sname = 'screen_crvincident_activation' + sincnumber
        Logger.info('CRV:SETUP:incident activation for incident ' + sincnumber)
        screen_crvincident_activation = Screen(name=sname)

        increc = self.currentincidents[incnumber]['record']

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        header = self.parent.screencreateheader(sname, 'Activation screen for incident ' + sincnumber)

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        middletop = BoxLayout(orientation='vertical')
        middlebottom = BoxLayout(orientation='horizontal')

        row1 = BoxLayout(orientation='horizontal')
        szh = [1,.25]
        b, inctime = self.parent.boxtimebox('Time Activated', szh, orientation='vertical')
        inctime.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incalerttime', b, inctime, row1, 'text')

        b, incvess, boxlab = self.parent.boxtextbox('Vessel Name', szh, multiline=False, orientation='vertical')
        incvess.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incvesselname', b, incvess, row1, 'text')

        b, incvesscs, boxlab = self.parent.boxtextbox('Callsign', szh, multiline=False, orientation='vertical')
        incvesscs.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incassistcallsign', b, incvesscs, row1, 'text')

        # a droplist of common comms sources - but you can always type one in anyway.
        commmssources = ['VHF', 'Mobile', 'UHF', '80', '81', '82', '83', '84', '85', '86', 'Aviation']
        b, incvessct, boxlab = self.parent.boxdropdown('Comms', commmssources, [1,.20], nodelete=True, multiline=True, orientation='vertical')
        incvesscs.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incassistcommstype', b, incvessct, row1, 'text')

        b, inctu = self.parent.boxtimebox('Time Underway', szh=szh, orientation='vertical')
        inctu.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('inctimeunderway', b, inctu, row1, 'text')

        b, inccrvfuel, boxlab = self.parent.boxtextbox('CRV Fuel', szh=szh, orientation='vertical')
        inccrvfuel.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('inccrvfuelstart', b, inccrvfuel, row1, 'text')

        szh = [.20, 1]
        row2 = BoxLayout(orientation='horizontal')
        b, incpos, boxlab = self.parent.boxtextbox('Position', szh, multiline=True)
        incpos.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incposition', b, incpos, row2, 'text')

        row3 = BoxLayout(orientation='horizontal')

        #szh = [6, 1]
        wlatlong = MyBoundBox(orientation='horizontal')

        # creates a label, a numeric input and a float input and a label
        # e.g. position 36 27.234 S 174 37.234 E
        # completing an input focuses the next

        l = MyLabel(text='Lat/Long', color=self.parent.crvcolor.getfgcolor(), size_hint=szh, halign='left')
        wlatlong.add_widget(l)

        wlatlong1 = BoxLayout(orientation='horizontal')
        ilatdegrees = CNumInput(max_chars=2)   # degrees
        increc.setobjectplus('inclatd', ilatdegrees, ilatdegrees, wlatlong1, 'text')
        ilatdegrees.bind(text=self.inc_callback_checklatlong)

        ilatmin = CFloatInput()  # decimal minutes
        increc.setobjectplus('inclatm', ilatmin, ilatmin, wlatlong1, 'text')
        ilatmin.bind(focus=self.inc_checkactivation)

        wlatlong1.add_widget(MyLabel(text='S'))

        ilongdegrees = CNumInput(max_chars=3) # degrees
        increc.setobjectplus('inclongd', ilongdegrees, ilongdegrees, wlatlong1, 'text')
        ilongdegrees.bind(text=self.inc_callback_checklatlong)

        ilongmin = CFloatInput()
        increc.setobjectplus('inclongm', ilongmin, ilongmin, wlatlong1, 'text')
        ilongmin.bind(focus=self.inc_checkactivation)

        wlatlong1.add_widget(MyLabel(text='E'))
        wlatlong.add_widget(wlatlong1)
        row3.add_widget(wlatlong)

        middletop.add_widget(row1)
        middletop.add_widget(row2)
        middletop.add_widget(row3)

        bleft = MyBoundBox(orientation='vertical', padding=10)
        bright = MyBoundBox(orientation='vertical', padding=10)

        bleft1 = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.2)

        # a droplist of common problems - but you can always type one in anyway.
        problems = ['Sinking', 'Grounded', 'Medical', 'Broken Down', 'Fuel Problem', 'Electrical',
                    'Anchor stuck', 'Fire', 'Broken Rudder', 'Hit Rocks', 'Distress', 'Urgency', 'Missing Person', 'Steering']
        b, problem, boxlab = self.parent.boxdropdown('Problem', problems, [1,.20], nodelete=True, multiline=True, orientation='vertical')
        #b, problem, boxlab = self.parent.boxtextbox('Problem', [1,.20], multiline=True, orientation='vertical')
        problem.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incproblem', b, problem, bleft1, 'text')

        b, mission, boxlab = self.parent.boxtextbox('Mission', [1,.20], multiline=True, orientation='vertical')
        mission.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incmission', b, mission, bleft1, 'text')
        bleft.add_widget(bleft1)

#        bright1 = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.1)
        bright1 = MyBoundBox(orientation='vertical')
#        brightpob = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.4)
        lpob = MyLabel(text='POB (Adult/Child/Dog)', size_hint=(1,.40))
        bright1.add_widget(lpob)

        brightpob = BoxLayout(orientation='horizontal')
        bright1.add_widget(brightpob)

        ba,pobadult = self.parent.boxnumbox('A', szh=[1,1])
        increc.setobjectplus('incpoba', ba, pobadult, brightpob, 'text')
        pobadult.bind(focus=self.inc_checkactivation)

        bc,pobchildren = self.parent.boxnumbox('C', szh=[1,1])
        pobchildren.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incpobc', bc, pobchildren, brightpob, 'text')

        bd,pobdogs = self.parent.boxnumbox('D', szh=[1, 1])
        pobdogs.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incpobd', bd, pobdogs, brightpob, 'text')

        brightves = BoxLayout(orientation='horizontal')
        brightveslen = BoxLayout(orientation='horizontal')
        brightves.add_widget(brightveslen)
        brightvesunits = BoxLayout(orientation='vertical', size_hint_x=.2)
        bl,vessellength = self.parent.boxnumbox('Length', szh=[1,1])
        vessellength.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incassistlength', bl, vessellength, brightveslen, 'text')

        # nothing to do with a radio - its a radio button
        increc.unitradio[0] = ToggleButton(text='M', group='unit')
        increc.unitradio[0].id = 'M'
        increc.unitradio[0].bind(on_press=self.inc_checkconclusion)
        brightvesunits.add_widget(increc.unitradio[0])
        increc.unitradio[1] = ToggleButton(text='Ft', group='unit')
        increc.unitradio[1].id = 'FT'
        increc.unitradio[1].bind(on_press=self.inc_checkconclusion)
        brightvesunits.add_widget(increc.unitradio[1])
        brightveslen.add_widget(brightvesunits)

        #bm,vesselmodel,l = self.parent.boxtextbox('Type', [1,1])
        #vesselmodel.bind(focus=self.inc_checkactivation)
        #increc.setobjectplus('incassisttype', bm, vesselmodel, brightves, 'text')
        self.data.readvesseltypes()
        bm, vesselmodel, l = self.parent.boxdropdown('Type', self.data.vesseltypes, [.5, 1])
        increc.setobjectplus('incassisttype', bm, vesselmodel, brightves, 'text')
        vesselmodel.bind(focus=self.inc_checkactivation)

        brightcol = BoxLayout(orientation='horizontal')
        bcolh,vesselcolorh,l = self.parent.boxtextbox('Color (Hull)', [1, 1])
        vesselcolorh.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incassistcolorh', bcolh, vesselcolorh, brightcol, 'text')

        bcolo,vesselcoloro,l = self.parent.boxtextbox('Color (Other)', [1, 1])
        vesselcoloro.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incassistcoloro', bcolo, vesselcoloro, brightcol, 'text')

        #bright1.add_widget(bl)
        bright1.add_widget(brightves)
        bright1.add_widget(brightcol)

        bright.add_widget(bright1)
        #bright.add_widget(bright2)

        middlebottom.add_widget(bleft)
        middlebottom.add_widget(bright)

        middle.add_widget(middletop)
        middle.add_widget(middlebottom)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        buttonhome = MyButton(text='Home')
        buttonhome.bind(on_press=self.inc_callback_inchome)
        footer.add_widget(buttonhome)
        increc.setobject('inchomebuttonact', buttonhome, 'text')

        buttonact = MyButton(text='Activation')
        buttonact.bind(on_press=lambda dbtn: self.inc_set_screen('activation'))
        buttonact.disabled = True
        footer.add_widget(buttonact)

        buttonadm = MyButton(text='Administration')
        buttonadm.bind(on_press=lambda dbtn: self.inc_set_screen('adm'))
        footer.add_widget(buttonadm)

        buttonpay = MyButton(text='Payment')
        buttonpay.bind(on_press=lambda dbtn: self.inc_set_screen('pay'))
        footer.add_widget(buttonpay)

        buttoncom = MyButton(text='Conclusion')
        buttoncom.bind(on_press=lambda dbtn: self.inc_set_screen('con'))
        footer.add_widget(buttoncom)

        buttondeb = MyButton(text='Debrief')
        buttondeb.bind(on_press=lambda dbtn: self.inc_set_screen('deb'))
        footer.add_widget(buttondeb)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_crvincident_activation.add_widget(box)
        screen_crvincident_activation.bind(on_enter=self.screenincident_callback_onenter)

        return screen_crvincident_activation

    def setup_incident_administration(self, incnumber):
        Logger.info('CRV:SETUP:incident administration')

        sincnumber = str(incnumber)
        sname = 'screen_crvincident_administration' + sincnumber
        Logger.info('CRV:SETUP:incident administration for incident ' + sincnumber)
        screen_crvincident_administration = Screen(name=sname)

        increc = self.currentincidents[incnumber]['record']

        szh = [.5, 1]

        box = BoxLayout(orientation='vertical', padding=10)

        header = self.parent.screencreateheader(sname, 'Administration screen for incident ' + sincnumber)

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        row1  = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)

        ba,mnznum = self.parent.boxnumbox('MNZ Number', szh=[1,1], boxhint=[1,1])
        increc.setobjectplus('incmnznum', ba, mnznum, row1, 'text')
        mnznum.bind(focus=self.inc_checkadministration)

        s2, cgmember, l1 = self.parent.boxcheckbox('Coastguard\nMember?', szh=[1.5, 1], boxhint=[1,1])
        increc.setobjectlist('incmember', s2, [cgmember, l1], row1, 'checkbox')
        cgmember.bind(active=self.inc_checkadministration)

        ba,cnznum = self.parent.boxnumbox('CNZ Mem#', szh=[1,1])
        increc.setobjectplus('incmembernum', ba, cnznum, row1, 'text')
        cnznum.bind(focus=self.inc_checkadministration)

        row2 = BoxLayout(orientation='horizontal', pos_hint_x=0, size_hint_y=.6)

        bleft2 = BoxLayout(orientation='vertical', pos_hint_x=0, size_hint_x=.5)
        bright2 = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_x=.5)

        row2.add_widget(bleft2)
        row2.add_widget(bright2)

        i, x, boxlab = self.parent.boxtextbox('Owners Name', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('incname', i, x, bleft2, 'text')
        x.bind(focus=self.inc_checkadministration)

        i, x, boxlab = self.parent.boxtextbox('Owners Address', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('incaddress', i, x, bleft2, 'text')
        x.bind(text=self.inc_checkadministration)

        #bright1 = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.1)
        #bright2.add_widget(bright1)

        b, totalpob, boxlab = self.parent.boxtextbox('Total POB', szh)
        totalpob.bind(focus=self.inc_checkactivation)
        increc.setobjectplus('incpob', b, totalpob, bright2, 'text')

        #bgenderhead = MyLabel(text='Gender', color=self.data.crvcolor.getfgcolor())

        bgender0 = MyBoundBox(orientation='horizontal', pos_hint_x=0)
        bgenderageshead = MyLabel(text='Ages', color=self.data.crvcolor.getfgcolor())
        bgender0.add_widget(bgenderageshead)
        bgendermhead = MyLabel(text='M', color=self.data.crvcolor.getfgcolor())
        bgender0.add_widget(bgendermhead)
        bgenderfhead = MyLabel(text='F', color=self.data.crvcolor.getfgcolor())
        bgender0.add_widget(bgenderfhead)

        #bright2.add_widget(bgenderhead)
        bright2.add_widget(bgender0)

        bgender0010 = MyBoundBox(orientation='horizontal', pos_hint_x=0)
        bgender0010head = CTextInput(text='0-10')
        bgender0010head.disabled = True
        bgender0010.add_widget(bgender0010head)
        bgender0010m = CTextInput()
        increc.setobject('incmale0010', bgender0010m, 'text')
        bgender0010.add_widget(bgender0010m)
        bgender0010f = CTextInput()
        increc.setobject('incfemale0010', bgender0010f, 'text')
        bgender0010.add_widget(bgender0010f)

        bright2.add_widget(bgender0010)

        bgender1120 = MyBoundBox(orientation='horizontal', pos_hint_x=0)
        bgender1120head = CTextInput(text='11-20')
        bgender1120head.disabled = True
        bgender1120.add_widget(bgender1120head)
        bgender1120m = CTextInput()
        increc.setobject('incmale1120', bgender1120m, 'text')
        bgender1120.add_widget(bgender1120m)
        bgender1120f = CTextInput()
        increc.setobject('incfemale1120', bgender1120f, 'text')
        bgender1120.add_widget(bgender1120f)

        bright2.add_widget(bgender1120)

        bgender2130 = MyBoundBox(orientation='horizontal', pos_hint_x=0)
        bgender2130head = CTextInput(text='21-30')
        bgender2130head.disabled = True
        bgender2130.add_widget(bgender2130head)
        bgender2130m = CTextInput()
        increc.setobject('incmale2130', bgender2130m, 'text')
        bgender2130.add_widget(bgender2130m)
        bgender2130f = CTextInput()
        increc.setobject('incfemale2130', bgender2130f, 'text')
        bgender2130.add_widget(bgender2130f)

        bright2.add_widget(bgender2130)

        bgender3140 = MyBoundBox(orientation='horizontal', pos_hint_x=0)
        bgender3140head = CTextInput(text='31-40')
        bgender3140head.disabled = True
        bgender3140.add_widget(bgender3140head)
        bgender3140m = CTextInput()
        increc.setobject('incmale3140', bgender3140m, 'text')
        bgender3140.add_widget(bgender3140m)
        bgender3140f = CTextInput()
        increc.setobject('incfemale3140', bgender3140f, 'text')
        bgender3140.add_widget(bgender3140f)

        bright2.add_widget(bgender3140)

        bgender4150 = MyBoundBox(orientation='horizontal', pos_hint_x=0)
        bgender4150head = CTextInput(text='41-50')
        bgender4150head.disabled = True
        bgender4150.add_widget(bgender4150head)
        bgender4150m = CTextInput()
        increc.setobject('incmale4150', bgender4150m, 'text')
        bgender4150.add_widget(bgender4150m)
        bgender4150f = CTextInput()
        increc.setobject('incfemale4150', bgender4150f, 'text')
        bgender4150.add_widget(bgender4150f)

        bright2.add_widget(bgender4150)

        bgender50 = MyBoundBox(orientation='horizontal', pos_hint_x=0)
        bgender50head = CTextInput(text='50+')
        bgender50head.disabled = True
        bgender50.add_widget(bgender50head)
        bgender50m = CTextInput()
        increc.setobject('incmale50plus', bgender50m, 'text')
        bgender50.add_widget(bgender50m)
        bgender50f = CTextInput()
        increc.setobject('incfemale50plus', bgender50f, 'text')
        bgender50.add_widget(bgender50f)

        bright2.add_widget(bgender50)

        #row4  = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)

        i, x, boxlab = self.parent.boxtextbox('Home Phone', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('inchomephone', i, x, bleft2, 'text')
        x.bind(focus=self.inc_checkadministration)

        row5  = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)

        i, x, boxlab = self.parent.boxtextbox('Email', szh=[.2, 1], boxhint=[1,1])
        increc.setobjectplus('incemail', i, x, row5, 'text')
        x.bind(focus=self.inc_checkadministration)

        i, x, boxlab = self.parent.boxtextbox('Mobile Phone', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('incmobile', i, x, row5, 'text')
        x.bind(focus=self.inc_checkadministration)

        i, x, boxlab = self.parent.boxtextbox('Work Phone', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('incworkphone', i, x, row5, 'text')
        x.bind(focus=self.inc_checkadministration)

        middle.add_widget(row1)
        middle.add_widget(row2)
        #middle.add_widget(row3)
        #middle.add_widget(row4)
        middle.add_widget(row5)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        buttonhome = MyButton(text='Home')
        buttonhome.bind(on_press=self.inc_callback_inchome)
        footer.add_widget(buttonhome)
        increc.setobject('inchomebuttonadm', buttonhome, 'text')

        buttonact = MyButton(text='Activation')
        buttonact.bind(on_press=lambda dbtn: self.inc_set_screen('act'))
        footer.add_widget(buttonact)

        buttonadm = MyButton(text='Administration')
        buttonadm.bind(on_press=lambda dbtn: self.inc_set_screen('adm'))
        buttonadm.disabled = True
        footer.add_widget(buttonadm)

        buttonpay = MyButton(text='Payment')
        buttonpay.bind(on_press=lambda dbtn: self.inc_set_screen('pay'))
        footer.add_widget(buttonpay)

        buttoncom = MyButton(text='Conclusion')
        buttoncom.bind(on_press=lambda dbtn: self.inc_set_screen('con'))
        footer.add_widget(buttoncom)

        buttondeb = MyButton(text='Debrief')
        buttondeb.bind(on_press=lambda dbtn: self.inc_set_screen('deb'))
        footer.add_widget(buttondeb)

        # buttoncancel = MyButton(text='Cancel')
        # buttoncancel.bind(on_press=self.inc_callback_inccancel)
        # footer.add_widget(buttoncancel)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_crvincident_administration.add_widget(box)
        screen_crvincident_administration.bind(on_enter=self.screenincident_callback_onenter)

        return screen_crvincident_administration

    def setup_incident_debrief(self, incnumber):
        Logger.info('CRV:SETUP:incident debrief')

        sincnumber = str(incnumber)
        sname = 'screen_crvincident_debrief' + sincnumber
        Logger.info('CRV:SETUP:incident debrief for incident ' + sincnumber)
        screen_crvincident_debrief = Screen(name=sname)

        increc = self.currentincidents[incnumber]['record']

        szh = [.5, 1]

        box = BoxLayout(orientation='vertical', padding=10)

        header = self.parent.screencreateheader(sname, 'Debrief screen for incident ' + sincnumber)

        middle = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        buttonhome = MyButton(text='Home')
        buttonhome.bind(on_press=self.inc_callback_inchome)
        footer.add_widget(buttonhome)
        increc.setobject('inchomebuttondeb', buttonhome, 'text')

        buttonact = MyButton(text='Activation')
        buttonact.bind(on_press=lambda dbtn: self.inc_set_screen('act'))
        footer.add_widget(buttonact)

        buttonadm = MyButton(text='Administration')
        buttonadm.bind(on_press=lambda dbtn: self.inc_set_screen('adm'))
        footer.add_widget(buttonadm)

        buttonpay = MyButton(text='Payment')
        buttonpay.bind(on_press=lambda dbtn: self.inc_set_screen('pay'))
        footer.add_widget(buttonpay)

        buttoncom = MyButton(text='Conclusion')
        buttoncom.bind(on_press=lambda dbtn: self.inc_set_screen('con'))
        footer.add_widget(buttoncom)

        buttondeb = MyButton(text='Debrief')
        buttondeb.bind(on_press=lambda dbtn: self.inc_set_screen('deb'))
        buttondeb.disabled = True
        footer.add_widget(buttondeb)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_crvincident_debrief.add_widget(box)
        screen_crvincident_debrief.bind(on_enter=self.screenincident_callback_onenter)

        return screen_crvincident_debrief

    def setup_incident_payment(self, incnumber):
        Logger.info('CRV:SETUP:incident payment')

        sincnumber = str(incnumber)
        sname = 'screen_crvincident_payment' + sincnumber
        Logger.info('CRV:SETUP:incident payment for incident ' + sincnumber)
        screen_crvincident_payment = Screen(name=sname)

        increc = self.currentincidents[incnumber]['record']

        box = BoxLayout(orientation='vertical', padding=10)

        header = self.parent.screencreateheader(sname, 'Payment screen for incident ' + sincnumber)

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        i, x, boxlab = self.parent.boxtextbox('Agreed price for assistance ($)', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('incquotedprice', i, x, middle, 'text')
        x.bind(focus=self.inc_checkpayment)

        i, x, boxlab = self.parent.boxtextbox('Name on card', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('inccardname', i, x, middle, 'text')
        x.bind(focus=self.inc_checkpayment)

        i, x, boxlab = self.parent.boxtextbox('Card Number', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('inccardnumber', i, x, middle, 'text')
        x.bind(focus=self.inc_checkpayment)

        i, x, boxlab = self.parent.boxtextbox('Card Expiry', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('inccardexpiry', i, x, middle, 'text')
        x.bind(focus=self.inc_checkpayment)

        i, x, boxlab = self.parent.boxtextbox('Card CSV', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('inccardcsv', i, x, middle, 'text')
        x.bind(focus=self.inc_checkpayment)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        buttonhome = MyButton(text='Home')
        buttonhome.bind(on_press=self.inc_callback_inchome)
        footer.add_widget(buttonhome)
        increc.setobject('inchomebuttonpay', buttonhome, 'text')

        buttonact = MyButton(text='Activation')
        buttonact.bind(on_press=lambda dbtn: self.inc_set_screen('act'))
        footer.add_widget(buttonact)

        buttonadm = MyButton(text='Administration')
        buttonadm.bind(on_press=lambda dbtn: self.inc_set_screen('adm'))
        footer.add_widget(buttonadm)

        buttonpay = MyButton(text='Payment')
        buttonpay.bind(on_press=lambda dbtn: self.inc_set_screen('pay'))
        buttonpay.disabled = True
        footer.add_widget(buttonpay)

        buttoncom = MyButton(text='Conclusion')
        buttoncom.bind(on_press=lambda dbtn: self.inc_set_screen('con'))
        footer.add_widget(buttoncom)

        buttondeb = MyButton(text='Debrief')
        buttondeb.bind(on_press=lambda dbtn: self.inc_set_screen('deb'))
        footer.add_widget(buttondeb)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_crvincident_payment.add_widget(box)
        screen_crvincident_payment.bind(on_enter=self.screenincident_callback_onenter)

        return screen_crvincident_payment

    def setup_incident_conclusion(self, incnumber):
        Logger.info('CRV:SETUP:incident conclusion')

        sincnumber = str(incnumber)
        sname = 'screen_crvincident_conclusion' + sincnumber
        Logger.info('CRV:SETUP:incident conclusion for incident ' + sincnumber)
        screen_crvincident_conclusion = Screen(name=sname)

        increc = self.currentincidents[incnumber]['record']

        box = BoxLayout(orientation='vertical', padding=10)

        header = self.parent.screencreateheader(sname, 'conclusion screen for incident ' + sincnumber)

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        conclusionrow  = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)
        increc.conradio[0] = ToggleButton(text='Success', group='con')
        increc.conradio[0].id = 'success'
        increc.conradio[0].bind(on_press=self.inc_checkconclusion)
        conclusionrow.add_widget(increc.conradio[0])
        increc.conradio[1] = ToggleButton(text='Stood Down', group='con')
        increc.conradio[1].id = 'stooddown'
        increc.conradio[1].bind(on_press=self.inc_checkconclusion)
        conclusionrow.add_widget(increc.conradio[1])
        increc.conradio[2] = ToggleButton(text='Suspended', group='con')
        increc.conradio[2].id = 'suspended'
        increc.conradio[2].bind(on_press=self.inc_checkconclusion)
        conclusionrow.add_widget(increc.conradio[2])
        increc.conradio[3] = ToggleButton(text='Fatality', group='con')
        increc.conradio[3].id = 'fatality'
        increc.conradio[3].bind(on_press=self.inc_checkconclusion)
        conclusionrow.add_widget(increc.conradio[3])

        i, x, boxlab = self.parent.boxtextbox('Incident Number', szh=[1, 1], boxhint=[1,1], orientation='vertical')
        increc.setobjectplus('incnumber', i, x, conclusionrow, 'text')
        x.bind(focus=self.inc_checkconclusion)

        middle.add_widget(conclusionrow)

        crvb  = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)
        i, x, boxlab = self.parent.boxtextbox('CRV\nRet To', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('inccrvto', i, x, crvb, 'text')
        x.bind(focus=self.inc_checkconclusion)

        i, x = self.parent.boxtimebox('CRV Time\nArrive', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('inctimearrive', i, x, crvb, 'text')
        x.bind(focus=self.inc_checkconclusion)

        i, x = self.parent.boxtimebox('Inc\nTotal Time', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('inctimetotal', i, x, crvb, 'text')
        # x.bind(focus=self.inc_checkconclusion)

        middle.add_widget(crvb)

        cfuel  = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)

        i, x, boxlab = self.parent.boxtextbox('CRV Fuel\nat Inc End', szh=[1, 1], boxhint=[1,1])
        x.bind(focus=self.inc_checkconclusion)
        increc.setobjectplus('inccrvfuelatend', i, x, cfuel, 'text')

        i, x, boxlab = self.parent.boxtextbox('CRV Fuel\nUsed', szh=[1, 1], boxhint=[1,1])
        x.bind(focus=self.inc_checkconclusion)
        increc.setobjectplus('inccrvfuelused', i, x, cfuel, 'text')

        i, x, boxlab = self.parent.boxtextbox('@ $/lt', szh=[1, 1], boxhint=[1,1])
        x.bind(focus=self.inc_checkconclusion)
        increc.setobjectplus('inccrvfuelprice', i, x, cfuel, 'text')

        i, x, boxlab = self.parent.boxtextbox('= ($)', szh=[1, 1], boxhint=[1,1])
        x.bind(focus=self.inc_checkconclusion)
        increc.setobjectplus('inccrvfuelcost', i, x, cfuel, 'text')

        csupp  = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)

        i, x, boxlab = self.parent.boxtextbox('Fuel\nSupplied', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('incfuelsupplied', i, x, csupp, 'text')
        x.bind(focus=self.inc_checkconclusion)
        i, x, boxlab = self.parent.boxtextbox('@ $/lt', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('incfuelsuppliedprice', i, x, csupp, 'text')
        x.bind(focus=self.inc_checkconclusion)
        i, x, boxlab = self.parent.boxtextbox('= ($)', szh=[1, 1], boxhint=[1,1])
        increc.setobjectplus('incfuelsuppliedcost', i, x, csupp, 'text')
        x.bind(focus=self.inc_checkconclusion)

        middle.add_widget(cfuel)
        middle.add_widget(csupp)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        buttonhome = MyButton(text='Home')
        buttonhome.bind(on_press=self.inc_callback_inchome)
        footer.add_widget(buttonhome)
        increc.setobject('inchomebuttoncon', buttonhome, 'text')

        buttonact = MyButton(text='Activation')
        buttonact.bind(on_press=lambda dbtn: self.inc_set_screen('act'))
        footer.add_widget(buttonact)

        buttonadm = MyButton(text='Administration')
        buttonadm.bind(on_press=lambda dbtn: self.inc_set_screen('adm'))
        footer.add_widget(buttonadm)

        buttonpay = MyButton(text='Payment')
        buttonpay.bind(on_press=lambda dbtn: self.inc_set_screen('pay'))
        footer.add_widget(buttonpay)

        buttondeb = MyButton(text='Debrief')
        buttondeb.bind(on_press=lambda dbtn: self.inc_set_screen('deb'))
        footer.add_widget(buttondeb)

        buttonconfirm = MyButton(text='Confirm Inc\nConclusion')
        buttonconfirm.bind(on_press=self.inc_confirm_conclusion)
        footer.add_widget(buttonconfirm)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_crvincident_conclusion.add_widget(box)
        screen_crvincident_conclusion.bind(on_enter=self.screenincident_callback_onenter)

        return screen_crvincident_conclusion

    def inc_grid_click(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.currentincident = int(instance.id)
            self.inc_set_screen('act')


            # row = instance.coords[0] - 1
            # Logger.debug('CRV: INCIDENT GRID: Click: row: '+ str(row))
            #
            # #if row > 0:  # ignore first row - it's a title row
            #
            # increc = self.currentincidents[row]['record']
            # id = increc.getobjectvariable('incid', 'text', '0')
            # self.currentincident = int(id)
            #
            # self.inc_set_screen('act')

        return True  # Indicates you have handled the event

    def inc_add_gridentry(self, row, in_t):
        try:
            if row > self.layout.rows:
                self.layout.rows += 5

            for column in range(len(in_t)):
                szx = 1.0
                if column == 0: szx = 0.2
                elif column == 1: szx = 1.1
                elif column == 6: szx = 0.7
                elif column == 7: szx = 0.7

                if row == 0:
                    grid_entry = ActGridEntry(coords=(row, column), size_hint_x=szx, size_hint_y=None, height=modglobal.gridheight, readonly=True)
                else:
                    grid_entry = ActGridEntry(coords=(row, column), size_hint_x=szx, size_hint_y=None, height=modglobal.gridheight, readonly=True)
                    grid_entry.id = in_t[0]
                    grid_entry.bind(on_touch_up=self.inc_grid_click)
                #grid_entry.is_focusable = False
                grid_entry.readonly = True
                grid_entry.text = in_t[column]
                self.layout.add_widget(grid_entry)
        except GridLayoutException:
            Logger.info('CRV: GRID:INCIDENTMAIN.Layout exception: rows, current..'+str(self.layout.rows) + ' ' + str(row))

    def scrollwidget(self, wdth):
        self.create(wdth)
        root = ScrollView(size_hint=(1, 1), size=(wdth, 500), bar_width=14, scroll_type=['bars','content'])
        root.add_widget(self.layout)
        return root

    def create(self, wdth):
        #self.currentrow = -1
        self.layout = GridLayout(cols=8, rows=10, padding=0, size_hint_x=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

    def inc_close_incident(self, instance):
        '''
        End an incident

        Try to fill in some values
        '''
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        if self.data.datarecord is not None:
            if self.data.datarecord.haveopenedlog:
                self.copydatarec('visibility', 'incvisibility')
                self.copydatarec('', 'inctakentotime') # set automatically
                #self.copydatarec('', 'incassistcoloro')
                #self.copydatarec('', 'incassistcolorh')
                #self.copydatarec('', 'incid')
                self.copydatarec('', 'incfueltotal')
                s = self.data.datarecord.getskippername()
                self.copydatarec('', 'incvesselskipper', s)
                #self.copydatarec('', 'incpobd')
                #self.copydatarec('', 'incpoliceevent')
                #self.copydatarec('', 'incpobc')
                #self.copydatarec('', 'incpoba')
                #self.copydatarec('', 'inclatlong')
                #self.copydatarec('', 'inctakento')
                self.copydatarec('', 'inclocationunderway')
                #self.copydatarec('', 'incfemale2130')
                #self.copydatarec('', 'incresultfatality')
                self.copydatarec('', 'incfuelsuppliedtype')
                #self.copydatarec('', 'inctimearrive') # set automatically
                #self.copydatarec('', 'incemail')
                #self.copydatarec('', 'incfuelusedtype')
                #self.copydatarec('', 'incassistcommstype')
                #self.copydatarec('', 'incassistactivity')
                #self.copydatarec('', 'inccrvto')
                #self.copydatarec('', 'incvesselcallsign')
                #self.copydatarec('', 'inclongm')
                #self.copydatarec('', 'incfuelsuppliedcost')
                #self.copydatarec('', 'inctimeunderway')
                #self.copydatarec('', 'inclongd')
                #self.copydatarec('', 'incmale3140')
                #self.copydatarec('', 'incmembernum')
                #self.copydatarec('', 'incsap100a') # set automatically
                #self.copydatarec('', 'incsap100b')
                self.copydatarec('wind', 'incwindspeed')
                #self.copydatarec('', 'incisincident')
                #self.copydatarec('', 'incmnznum')
                #self.copydatarec('', 'inccardexpiry')
                #self.copydatarec('', 'inctide')
                #self.copydatarec('', 'incfuelusedcostp')
                #self.copydatarec('', 'incassistother')
                #self.copydatarec('', 'incstatus')
                #self.copydatarec('', 'incfuelusedcostd')
                #self.copydatarec('', 'incexitstrategies') # set automatically
                #self.copydatarec('', 'inchomephone')
                #self.copydatarec('', 'incfemale3140')
                #self.copydatarec('', 'incassistnumengines')
                #self.copydatarec('', 'incfuelsupplied')
                #self.copydatarec('', 'incfuelusedd')
                #self.copydatarec('', 'incassistlength')
                #self.copydatarec('', 'incactions')
                #self.copydatarec('', 'incfuelusedp')
                #self.copydatarec('', 'incworkphone')
                #self.copydatarec('', 'incresultsuccess')
                #self.copydatarec('', 'incassistauthorise')
                #self.copydatarec('', 'incfemale4150')
                #self.copydatarec('', 'incfemale50plus')
                #self.copydatarec('', 'inctimeonscene')
                #self.copydatarec('', 'incassistsignature')
                #self.copydatarec('', 'incresultsuspended')
                self.copydatarec('seastate', 'incseastate')
                #self.copydatarec('', 'incassistcallsign')
                #self.copydatarec('', 'incpob')
                #self.copydatarec('', 'incmale0010')
                #self.copydatarec('', 'inccardcsv')
                #self.copydatarec('', 'incproblem')
                #self.copydatarec('', 'incmale1120')
                #self.copydatarec('', 'incdirection')
                #self.copydatarec('', 'incquotedprice')
                #self.copydatarec('', 'incassistname')
                #self.copydatarec('', 'inccardname')
                #self.copydatarec('', 'incaddress')
                #self.copydatarec('', 'inclatm')
                #self.copydatarec('', 'inclatd')
                #self.copydatarec('', 'inctimetotal')
                #self.copydatarec('', 'incfemale1120')
                #self.copydatarec('', 'incnumber')
                #self.copydatarec('', 'incmale2130')
                #self.copydatarec('', 'incispositioning')
                #self.copydatarec('', 'incassisttype')
                #self.copydatarec('', 'inccardtype')
                #self.copydatarec('', 'incmission')
                #self.copydatarec('', 'incname')
                #self.copydatarec('', 'inccardnumber')
                #self.copydatarec('', 'incdepartscene')
                #self.copydatarec('', 'incfemale0010')
                #self.copydatarec('', 'incmember')
                #self.copydatarec('', 'incmale4150')
                #self.copydatarec('', 'incvesselname')
                #self.copydatarec('', 'incresultstooddown')
                #self.copydatarec('', 'incmale50plus')
                #self.copydatarec('', 'incfueltotalcost')
                #self.copydatarec('', 'incmobile')
                #self.copydatarec('', 'incrccnznumber')
                #self.copydatarec('', 'incassistpropulsion')
                #self.copydatarec('', 'incposition')
                #self.copydatarec('', 'incalerttime')
        # so lets close it. Do a final save.
        incnumber = self.currentincident
        increc = self.currentincidents[incnumber]['record']

        svvessel = increc.getobjecttext('incvesselname')
        svalerttime = increc.getobjecttext('incalerttime')
        alerttime = svalerttime.replace(' ', '-')

        ok, afile = self.inc_shelf_archive(incnumber, alerttime)

        if not ok:
            MessageBox(self, titleheader="ERROR CLOSING CURRENT INCIDENT",
                   message="Unable to move the incident file from \n" +
                       increc.shelf_file + '\nto \n' + afile + '\n' +
                       'Please attempt to manually move the above file\nand then manually email it.')
        else:
            # close the incident
            self.cancelincident()

            # We have renamed the file - add a general boat log and
            # an audit log

            self.parent.boatlog.doinfolog('Incident CLOSED for vessel ' + svvessel + ' at time ' + svalerttime)

            # The incident is no longer open, the current screen is
            # no longer available.
            # Notify operational log that file is available to send.

            v = 'savedinc' + str(incnumber)
            self.data.datarecord.setobjectvariable(v, 'text', afile)
            Logger.info('CRV:close incident:bound incident to boatlog ' + v + ' ' + afile)
            self.data.shelf_save_current()

        self.parent.crv_callback_lastscreen(None)

    def inc_cancel_conclusion(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()

    def inc_confirm_conclusion(self, instance):
        modglobal.msgbox = MessageBox(self, titleheader="About to close current incident",
                   message="ARE YOU REALLY SURE YOU WANT\nTO CLOSE THE CURRENT INCIDENT?",
                   options={"YES": self.inc_close_incident, "NO": self.inc_cancel_conclusion})

    def etedistance(self, ininc=-1):
        if ininc < 0:
            inc = self.currentincident
        else:
            inc = ininc
        increc = self.currentincidents[inc]['record']

        ete = ''
        dist = ''

        try:
            curp = self.parent.gps.gps_location
            inclatlong = increc.getobjectvariable('inclatlong', 'text', '')
            idist = self.parent.gps.gpsdistance(curp, inclatlong)
            if idist > 0:
                idist = str(format(idist, '.2f'))
                dist = str(idist)

            sp = 0
            if self.simulationspeed > 0:
                sp = self.simulationspeed
            if self.parent.gps.gps_speed > 0:
                sp = self.parent.gps.gps_speed

            # time (hours) = distance (nm) / speed (knots)
            iete = -1
            if sp > 0:
                iete = int((60.0 * float(idist)) / float(sp))
            if iete > 0:
                ete = str(iete)
        except:
            ete = ''
            dist = ''

        return ete, dist

    def incpopulaterec(self, inc):
        t = [''] * 8
        increc = self.currentincidents[inc]['record']
        t[0] = increc.getobjectvariable('incid', 'text', '0')
        t[1] = increc.getobjecttext('incalerttime')
        t[2] = increc.getobjecttext('incvesselname')
        t[3] = increc.getobjecttext('incposition')
        td = increc.getobjectvariable('inclatd', 'text', '')
        tm = increc.getobjectvariable('inclatm', 'text', '')
        t[4] = td + ' ' + tm
        td = increc.getobjectvariable('inclongd', 'text', '')
        tm = increc.getobjectvariable('inclongm', 'text', '')
        t[5] = td + ' ' + tm

        try:
            ete, dist = self.etedistance(inc)

            t[6] = ete
            t[7] = dist
        except:
            t[6] = ''
            t[7] = ''

        return t

    def incpopulate(self):
        # delete the grid and repopulate based on incidents.
        self.layout.clear_widgets()

        head = ['ID', 'Time', 'Vessel', 'Position', 'Lat', 'Long', 'ETE (min)', 'Dist (NM)']
        self.inc_add_gridentry(0, head)

        row = 1
        try:
            t = [''] * 8
            inc = self.currentincident
            t = self.incpopulaterec(inc)
            self.inc_add_gridentry(row, t)
            row += 1
            for inc in range(self.numincidents):
                if inc != self.currentincident:
                    t = self.incpopulaterec(inc)
                    self.inc_add_gridentry(row, t)
                    row += 1
        except:
            pass

#
# ==================================================================
# CLASS... CrvLogAudit
# ==================================================================
#
class CrvLogAudit:
    def __init__(self, indata):
        self.data = indata
        #self.datadir = indatadir
        self.layout = None
        self.auditfile = ''
        self.currentrow = -1

    def add_gridentry(self, row, in_t):
        try:
            if row > self.layout.rows:
                self.layout.rows += 100

            for column in range(len(in_t)):
                grid_entry = ActGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = in_t[column]
                self.layout.add_widget(grid_entry)
        except GridLayoutException:
            Logger.info('CRV: GRID:AUDIT..Layout exception: rows, current..'+str(self.layout.rows) + ' ' + str(row))

    def scrollwidget(self, wdth):
        self.create(wdth)
        root = ScrollView(size_hint=(1, 1), size=(wdth, 500), bar_width=14, scroll_type=['bars','content'])
        root.add_widget(self.layout)
        return root

    def create(self, wdth):
        self.currentrow = -1
        self.layout = GridLayout(cols=2, rows=100, padding=0, size_hint_x=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

        if self.auditfile == '':
            self.auditfile = os.path.join(self.data.datadir, 'audit.txt')

    def writeaudit(self, message):
        if self.auditfile == '':
            self.auditfile = os.path.join(self.data.datadir, 'audit.txt')

        tmstamp = self.data.getnow()
        line = tmstamp + '!' + message + '\n'

        try:
            with open(self.auditfile, 'a') as a:
                a.write(line)
                a.close()
            Logger.info('CRV: Wrote audit log: ' + line)
        except:
            Logger.info('CRV: Unable to write audit log: ' + line)

    def populate(self):
        """
        The audit log will be audit.txt - read it and display it.
        Only last 30 days though
        """
        self.layout.clear_widgets()

        head = ['Time', 'Log']
        self.add_gridentry(0, head)

        row = 1
        try:
            with open(self.auditfile, 'r') as afile:
                while True:
                    line=afile.readline()
                    if not line: break

                    [t, l] = line.split('!', 2)
                    self.add_gridentry(row, [t, l])
                    row += 1
                afile.close()
        except IOError as e:
            pass

#
# ==================================================================
# CLASS... CrvManageLocations
# ==================================================================
#
class CrvManageLocations:
    def __init__(self, inboatlog):
        self.boatlog = inboatlog
        self.layout = None
        self.selectedname = ''
        self.currentrows = 0
        #modglobal.msgbox = None

    def confirm_no(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()

    def confirm_delete(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        if self.selectedname != '':
            row = 0
            drow = -1
            for loc in self.boatlog.locations:
                if loc == self.selectedname:
                    drow = row
                    break
                row += 1

            if drow >= 0:
                self.boatlog.locations.pop(drow)
                self.populategrid()

    def grid_delete(self, cname):
        self.selectedname = cname
        modglobal.msgbox = MessageBox(self, titleheader="Confirm delete",
                   message="ARE YOU SURE??\nNote: will require an application restart\nto see changes.",
                   options={"YES": self.confirm_delete, "NO": self.confirm_no})

    def add_header(self):
        self.currentrows = 0
        self.add_gridentry(self.currentrows, 'Location')

    def add_gridentry(self, row,  loc):
        if row >= self.layout.rows:
            self.layout.rows += 1

        if row == 0:
            self.layout.clear_widgets()

        try:
            column = 0
            grid_entry = ActGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
            grid_entry.text = loc
            grid_entry.disabled = True
            self.layout.add_widget(grid_entry)
            if row == 0:
                grid_entry = ButtonGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete Entry'
                self.layout.add_widget(grid_entry)
            else:
                grid_entry = ButtonGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete'
                grid_entry.bind(on_press=lambda dbtn: self.grid_delete(loc))
                self.layout.add_widget(grid_entry)
        except GridLayoutException:
            Logger.info('CRV: GRID:LOC..Layout exception: rows, current..'+str(self.layout.rows) + ' ' + str(row))

    def scrollwidget(self, wdth):
        self.create()
        root = ScrollView(size_hint=(1, 1), size=(wdth, 500), bar_width=14, scroll_type=['bars','content'])
        root.add_widget(self.layout)
        return root

    def create(self):
        self.layout = GridLayout(cols=2, rows=1, padding=0, size_hint_x=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

        self.add_header()
        self.populatelocations()

    def populatelocations(self):
        # make sure location list is populated

        self.boatlog.readlocations()

        self.populategrid()

    def populategrid(self):

        self.layout.clear_widgets()
        self.add_header()

        #self.create()
        for loc in self.boatlog.locations:
            self.currentrows += 1
            self.add_gridentry(self.currentrows, loc)

#
# ==================================================================
# CLASS... CrvManageVessels
# ==================================================================
#
class CrvManageVessels:
    def __init__(self, indata):
        self.data = indata
        self.layout = None
        self.selectedname = ''
        self.currentrows = 0
        self.head = ['Name', 'Callsign', 'Fuelrate', 'Fueltype', 'Hide', 'Phone', 'MSA', 'Engine']
        self.scrollvessel = None
        modglobal.msgbox = None
        self.data.readvessels()

    def callback_savevessel(self, instance):
        self.currentrows += 1
        t = [None] * 8

        xname = self.data.datarecord.getobjecttext('managevesselname')
        xcallsign = self.data.datarecord.getobjecttext('managevesselcallsign')
        xfuelrate = self.data.datarecord.getobjecttext('managevesselfuelrate')
        xfuel = self.data.datarecord.getobjecttext('managevesselfueltype')

        xenabled = self.data.datarecord.getobjectcheckastext('manageveselhide')
        if xenabled is not None:
            if xenabled in [ 'True', 'true']:
                xenabled = 'True'
            else:
                xenabled = ''

        xphone = self.data.datarecord.getobjecttext('managevesselphone')
        xmsa = self.data.datarecord.getobjecttext('managevesselmsanum')
        xengine = self.data.datarecord.getobjecttext('managevesselengine')

        t = [xname, xcallsign, xfuelrate, xfuel, xenabled, xphone, xmsa, xengine]

        if len(xname) > 0:
            self.data.allvessels.append(t)
            self.add_gridentry(self.currentrows, t)
            self.data.allvessels = sorted(self.data.allvessels, key=lambda x: x[0].lower())
            self.populategrid()

            self.scrollvessel.update_from_scroll()

        self.data.datarecord.setobjecttext('managevesselname', '')
        self.data.datarecord.setobjecttext('managevesselcallsign', '')
        self.data.datarecord.setobjecttext('managevesselfuelrate', '')
        self.data.datarecord.setobjecttext('managevesselfueltype', '')
        self.data.datarecord.setobjectcheck('managevesselhide', False)
        self.data.datarecord.setobjecttext('managevesselphone', '')
        self.data.datarecord.setobjecttext('managevesselmsanum', '')
        self.data.datarecord.setobjecttext('managevesselengine', '')

        vessobj = self.data.datarecord.getobject('reqvessname')

        v = self.getvesslist()
        vessobj.setdropdefaults(v)
        vessobj.setdropoptions(v)
        if instance is not None: instance.clickup()

    def getvesslist(self):
        v=[]
        for i in self.data.allvessels:
            v.append(i[0])
        return v

    def confirm_no(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()

    def confirm_delete(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        if self.selectedname != '':
            row = 0
            drow = -1
            for v in self.data.allvessels:
                if v[0] == self.selectedname:
                    drow = row
                    break
                row += 1

            if drow >= 0:
                self.data.allvessels.pop(drow)
                self.populategrid()

    def grid_delete(self, cname):
        self.selectedname = cname
        modglobal.msgbox = MessageBox(self, titleheader="Confirm delete",
                   message="ARE YOU SURE??",
                   options={"YES": self.confirm_delete, "NO": self.confirm_no})

    def add_header(self):
        self.currentrows = 0
        self.add_gridentry(self.currentrows, self.head)

    def add_gridentry(self, row,  ves):
        if row >= self.layout.rows:
            self.layout.rows += 1

        if row == 0:
            self.layout.clear_widgets()

        column = 0
        t = [None] * (len(ves)+1)

        try:
            for column in range(len(ves)):
                grid_entry = ActGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = ves[column]
                self.layout.add_widget(grid_entry)

            if row == 0:
                grid_entry = ButtonGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete Entry'
                self.layout.add_widget(grid_entry)
            else:
                grid_entry = ButtonGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete'
                if self.data.getlogactive():
                    grid_entry.disabled = True
                grid_entry.readonly = True
                grid_entry.bind(on_press=lambda dbtn: self.grid_delete(ves[0]))
                self.layout.add_widget(grid_entry)
        except GridLayoutException:
            Logger.info('CRV: GRID:VESS..Layout exception: rows, current..'+str(self.layout.rows) + ' ' + str(row))

    def scrollwidget(self, wdth):
        self.create()
        self.scrollvessel = ScrollView(size_hint=(1, 1), size=(wdth, 500), bar_width=14, scroll_type=['bars','content'])
        self.scrollvessel.add_widget(self.layout)
        return self.scrollvessel

    def create(self):
        self.layout = GridLayout(cols=len(self.head)+1, rows=1, padding=0, size_hint_x=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # self.populatevessels()

    def populatevessels(self):
        try:
            self.data.readvessels()

            self.populategrid()
        except:
            Logger.info('CRV: Failed to incpopulate vessels')

    def populategrid(self):

        self.layout.clear_widgets()
        self.add_header()

        for ves in self.data.allvessels:
            self.currentrows += 1
            self.add_gridentry(self.currentrows, ves)

#
# ==================================================================
# CLASS... CrvManageCrew
# ==================================================================
#
class CrvManageCrew:
    def __init__(self, increw):
        self.crew = increw
        self.layout = None
        self.selectedname = ''
        self.currentrows = 0
        self.crewgridlist = []
        self.scrollmanage = None
        self.changed = False
        modglobal.msgbox = None

    def confirm_no(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()

    def confirm_delete(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        if self.selectedname != '':
            row = 0
            drow = -1
            for n in self.crewgridlist:
                if n[0] == self.selectedname:
                    drow = row
                    break
                row += 1

            if drow >= 0:
                self.changed = True
                self.crewgridlist.pop(drow)
                self.populategrid()

    def grid_delete(self, cname):
        self.selectedname = cname
        modglobal.msgbox = MessageBox(self, titleheader="Confirm delete",
                   message="ARE YOU SURE??\nNote: will require an application restart\nto see changes.",
                   options={"YES": self.confirm_delete, "NO": self.confirm_no})

    def add_header(self):
        self.currentrows = 0
        head = ['First Name', 'Last Name', 'Skipper', 'Identifier']
        self.add_gridentry(self.currentrows, head)

    def add_gridentry(self, row,  in_t):
        if row >= self.layout.rows:
            self.layout.rows += 1

        if row == 0:
            self.layout.clear_widgets()

        try:
            for column in range(len(in_t)):
                grid_entry = ActGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = in_t[column]
                grid_entry.disabled = True
                self.layout.add_widget(grid_entry)
            if row == 0:
                grid_entry = ButtonGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete'
            else:
                grid_entry = ButtonGridEntry(coords=(row, column), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete'
                grid_entry.bind(on_press=lambda dbtn: self.grid_delete(in_t[0]))
            self.layout.add_widget(grid_entry)
        except GridLayoutException:
            Logger.info('CRV: GRID:MNGCREW..Layout exception: rows, current..'+str(self.layout.rows) + ' ' + str(row))

        return grid_entry

    def scrollwidgetmanage(self, wdth):
        self.create()
        self.scrollmanage = ScrollView(size_hint=(1, 1), size=(wdth, 500), bar_width=14, scroll_type=['bars','content'])
        self.scrollmanage.add_widget(self.layout)
        return self.scrollmanage

    def create(self):
        self.layout = GridLayout(cols=5, rows=1, padding=0, size_hint_x=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

        self.crew.setup()

        self.add_header()
        self.populatecrew()

    def populatecrew(self):
        # add the existing crew and skippers to list
        ltmp = []
        self.crewgridlist[:] = []
        for c in self.crew.data.completecrewlist:
            xtype = c[0]
            xfirst = c[1]
            xlast = c[2]
            xid = c[3]

            if xtype in ['S', 's']:
                xtype = 'True'
            else:
                xtype = ''

            ltmp.append([xfirst, xlast, xtype, xid])

        # sort on last name
        self.crewgridlist = sorted(ltmp, key=lambda x: x[1].lower())
        self.populategrid()

    def populategrid(self, scrollto=''):

        self.layout.clear_widgets()
        self.currentrows = 0
        self.add_header()

        #self.create()
        scrollpos = -1
        for c in self.crewgridlist:
            if len(scrollto) > 0:
                if c[1] == scrollto:
                    scrollpos = self.currentrows
            self.currentrows += 1
            g = self.add_gridentry(self.currentrows, c)

        if scrollpos >= 0:
            if self.scrollmanage is not None:
                itemsonscreen = self.scrollmanage.height / g.height
                halfscreen = itemsonscreen / 2 # to center screen

                # if itemnum on first screen, then just go to top
                if scrollpos < itemsonscreen:
                    normalisedpos = 0
                else:
                    normalisedpos = (scrollpos+halfscreen) / len(self.crewgridlist)
                y = 1 - normalisedpos  # as 0 is bottom and 1 is top
                self.scrollmanage.scroll_y = y

    def crewgridsave(self):
        ok = False
        try:
            #if not self.changed:
            #    Logger.info('CRV: CREW:Cowardly refusing to save an unchanged crewlist')
            #    return

            listtosave = []
            for c in self.crewgridlist:
                xfirst = c[0]
                xlast = c[1]
                xtype = c[2]
                xid = c[3]
                if xtype:
                    xtype='s'
                else:
                    xtype='c'

                line = xtype + ':' + xfirst + ':' + xlast + ':' + xid
                line += '\n'
                listtosave.append(line.lower())

            if len(listtosave) > 0:
                s1 = sorted(set(listtosave),key=listtosave.index)
                #sl = sorted(listtosave, key=lambda s: s.lower())
                ok = True
        except:
            Logger.info('CRV: cannot process new crew list to save')
            ok = False

        if ok:
            try:
                self.crew.data.dorename(False, self.crew.posscrewfile)

                with open(self.crew.posscrewfile, 'w') as cfile:
                    if len(listtosave) > 0:
                        cfile.writelines (s1)

                    cfile.close()
                    Logger.info('CRV: Written crew list')
            except IOError as e:
                Logger.info('CRV: Error writing crew list')
                self.crew.data.dorename(True, self.crew.posscrewfile)
        return

    def doscrolltop(self, instance):
        self.scrollmanage.scroll_y = 1
        if instance is not None: instance.clickup()

    def doscrollbottom(self, instance):
        self.scrollmanage.scroll_y = 0
        if instance is not None: instance.clickup()

    def callback_savenewcrew(self, instance):
        #self.layout.clear_widgets()

        self.currentrows += 1
        # type (c|s), first, last, id
        t = [None, None, None, None]

        xtype = self.crew.data.datarecord.getobjectcheckastext('managecrewtype')
        if xtype is not None:
            if xtype in [ 'True', 'true']:
                xtype = 'True'
            else:
                xtype = ''

        xfirst = self.crew.data.datarecord.getobjecttext('managecrewfirstname')
        xlast = self.crew.data.datarecord.getobjecttext('managecrewlastname')

        fullname = xfirst + ' ' + xlast

        xid = self.crew.data.datarecord.getobjecttext('managecrewid')

        t = [xfirst, xlast, xtype, xid]

        if len(fullname) > 0:
            self.crewgridlist.append(t)
            g = self.add_gridentry(self.currentrows, t)
            self.crewgridlist = sorted(self.crewgridlist, key=lambda x: x[1].lower())
            self.populategrid(scrollto=xlast)
            self.changed = True
            self.scrollmanage.update_from_scroll()

        self.crew.data.datarecord.setobjecttext('managecrewfirstname', '')
        self.crew.data.datarecord.setobjecttext('managecrewlastname', '')
        self.crew.data.datarecord.setobjectcheck('managecrewtype', False)
        self.crew.data.datarecord.setobjecttext('managecrewid', '')
        if instance is not None: instance.clickup()

#
# ==================================================================
# CLASS... CrvCrew
# ==================================================================
#
class CrvCrew:
    #
    # This is current activity
    # These are widgets
    #
    #crew = {'name': None, 'IMSAFE': None}

    def __init__(self, indata):
        self.data = indata
        #self.vesselname = ''
        self.posscrewfile = ''
        self.crewlistsent = False
        self.oldcrewitem = []
        self.crewscroll = None
        self.selectedname = ''

        self.layout = None
        self.currentrow = -1

        self.reinit()

    def reinit(self):
        self.posscrewlist = []
        self.possskipperlist = []
        self.donesetup = False

    def getposscrewfile(self):
        v = self.data.vesselname
        self.posscrewfile = os.path.join(self.data.datadir, str(v)+'.crew')
        Logger.info('CRV: Crew file: ' + self.posscrewfile)
        return self.posscrewfile

    def crv_crew_head(self):
        head = {0: 'Crew member', 1: 'IMSAFE'}

        # create a row
        self.crew_add_gridentry(0, head)

    def crv_add_crew(self, wdth):
        self.currentrow = -1
        self.layout = GridLayout(cols=3, rows=1, padding=0, size_hint_x=1, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

        self.crv_crew_head()
        self.crewscroll = ScrollView(size_hint=(1, 1), size=(wdth, 500), bar_width=14, scroll_type=['bars','content'])
        self.crewscroll.add_widget(self.layout)
        return self.crewscroll

    def doclear(self):
        self.layout.rows = 1
        self.layout.clear_widgets()
        self.data.crewvalues = []
        self.data.crewlist = []
        self.crv_crew_head()

    def setup(self):
        '''
        Reads crew file.
        '''

        #
        # Check to see if vessel has changed - if so force a reread of the crew file.
        #
        svcrewfile = self.posscrewfile
        self.getposscrewfile()
        if svcrewfile != self.posscrewfile:  # its changed - presumably by changing vessel in settings.
            self.reinit()

        if not self.donesetup:
            self.donesetup = True
            tmplist = []
            #
            # read possible crew and skippers from current boat list (if it exists)
            #
            if len(self.posscrewfile) > 0:
                try:
                    with open(self.posscrewfile, 'r') as cfile:
                        while True:
                            t = cfile.readline()
                            if not t: break

                            tmplist.append(t.strip())
                        cfile.close()
                        Logger.debug('CRV:managecrew: read number of poss crew: ' + str(len(tmplist)))
                except IOError as e:
                    #
                    # It doesnt exist, so ignore it.
                    #
                    Logger.info('CRV:managecrew: cannot read crew file: ' + self.posscrewfile)
                    pass

            try:
                for tmp in tmplist:
                    x = tmp.split(':')
                    #            Logger.debug("type is %s name is ", x[0], x[1])

                    xtype = x[0]
                    xfirst = x[1]
                    xlast = x[2]
                    xid = x[3]
                    xfull = xfirst + ' ' + xlast

                    if len(xfull) > 0:
                        self.data.completecrewlist.append(x)

                        if xtype in ['S', 's', 'C', 'c']:
                            if xtype in ['S', 's']:
                                self.possskipperlist.append(xfull)
                                self.posscrewlist.append(xfull)  # a skipper can be a crew member as well
                            else:
                                self.posscrewlist.append(xfull)
                Logger.info('CRV: managecrew. poss crew numbers: ' + str(len(self.posscrewlist)))
                Logger.info('CRV: managecrew. poss skipper numbers: ' + str(len(self.possskipperlist)))
            except:
                Logger.info('CRV: managecrew. Error processing poss crew')

            self.possskipperlist.sort()
            self.posscrewlist.sort()
        return

    def crew_grid_recover(self):
        """
        Recover grid from crewvalues
        """
        if len(self.data.crewvalues) > 0:
            # to stop logs being duplicated in self.data.setsinglelogvalue
            #  - called in crew_add_gridentry
            self.data.openingLog = True
            row = 1
            for n in self.data.crewvalues:
                self.crew_add_gridentry(row, n)
                row += 1
            self.data.openingLog = False


    def crew_callback_save(self, instance):
        #
        # save everything in activity to grid
        # if currentrow not set (-1) - then add a new one
        # else save to that row
        #

        crewtosave = {0: self.data.getcurrentcrewname(), 1: self.data.getcurrentcrewimsafe()}    # gets it from self.unsavedcrew

        self.do_save_crew(crewtosave)

        self.data.shelf_save_current()
        return

    def do_save_crew(self, crewtosave):

        # dont allow an empty crew to be added.
        empty = True
        doit = False
        if len(crewtosave[0]) > 0:
            empty = False

        if not empty:
            # check not adding skipper.
            doit = True
            s = self.data.datarecord.getskippername()
            if crewtosave[0] == s:
                doit = False

            # check to see if already there
            if doit:
                if self.currentrow >= 0:
                    lc = len(self.data.crewlist)
                    for n in range(lc):
                        if n != self.currentrow:
                            if self.data.crewlist[n][0].text == crewtosave[0]:
                                doit = False
                                break
                else:
                    for n in self.data.getallcrew():
                        if len(n[0].text) > 0:
                            if n[0].text == crewtosave[0]:
                                doit = False
                                break

        if doit:
            if self.currentrow == -1:
                #
                # we are adding data to an empty grid row or adding a new grid row.
                #
                r = self.layout.rows
                self.crew_add_gridentry(r, crewtosave)

            else:
                # the grid is being updated after a crew change

                self.data.setcrew(self.currentrow, 0, crewtosave[0])
                self.data.setcrew(self.currentrow, 1, crewtosave[1])
                self.currentrow = -1

                # update the crew values (used for persistance)
                self.data.setsinglecrewvalue(-1, crewtosave, self.oldcrewitem)


        self.currentrow = -1
        # empty the crew values - for another to be added.
        self.data.setcurrentcrew('focus', False)
        self.data.setcurrentcrew('name', '')
        self.data.setcurrentcrew('IMSAFE', False)

    def crew_callback_cancel(self, instance):
        self.currentrow = -1
        self.data.setcurrentcrew('name', '')
        self.data.setcurrentcrew('IMSAFE', False)
        if instance is not None: instance.clickup()

    def crew_grid_delete(self, cname):
        self.selectedname = cname
        if self.selectedname != '':

            # delete from text list and repopulate (easiest way of doing it)
            drow = -1
            row = 0
            for n in self.data.crewvalues:
                if n[0] == self.selectedname:
                    drow = row
                    break
                row += 1
            row = 0
            for n in self.data.crewlist:
                if n[0] == self.selectedname:
                    drow = row
                    break
                row += 1

            if drow >= 0:

                self.data.crewvalues.pop(drow)
                self.layout.clear_widgets()
                self.data.crewlist[:] = []
                self.crv_crew_head()

                self.crew_grid_recover()
                self.data.shelf_save_current()

    def crew_grid_click(self, instance, touch):
        if instance.collide_point(*touch.pos):
            #
            # If you click on an activity row - and it isn't empty, then
            # that row becomes the active row - and the current data is populated
            # from the grid data.
            #
            r = instance.coords[0]
            #if r > 0:
            #    r -= 1  # for some reason - first row is always zero - then further rows start from 2

            if r > 0:  # ignore first row - it's a title row
                empty = True
                tmp = self.data.getcrew(r)
                if len(tmp[0]) > 0:
                    empty = False
                    self.currentrow = r

                if not empty:
                    self.oldcrewitem = tmp
                    self.data.setcurrentcrew('name', tmp[0])
                    self.data.setcurrentcrew('IMSAFE', tmp[1])
                else:
                    pass

        return True  # Indicates you have handled the event

    def crew_add_gridentry(self, row, in_t, updcrewval = True):
        Logger.debug("CRV: crew_add_gridentry: row=%s", str(row))
        t = [None, None]
        r = self.layout.rows
        self.layout.rows += 1

        # in_t will be a 2 item list - name and IMSAFE
        # name is displayed as is. IMSAFE will be a boolean - convert to 'True'/'False'

        try:
            # process in_t[0] (name)
            grid_entry = CrewGridEntry(coords=(row, 1), size_hint_y=None, height=modglobal.gridheight, readonly=True)
            t[0] = grid_entry
            t[0].text = in_t[0]
            grid_entry.bind(on_touch_up=self.crew_grid_click)
            self.layout.add_widget(grid_entry)

            # if first row, then display second column as text (title)
            # Otherwise display it as a True/False
            grid_entry = CrewGridEntry(coords=(row, 1), size_hint_y=None, height=modglobal.gridheight, readonly=True)
            grid_entry.bind(on_touch_up=self.crew_grid_click)
            t[1] = grid_entry
            if row == 0:
                t[1].text = in_t[1]
            else:
                if in_t[1] in [ 'True', 'true', 'IMSAFE', True]:
                    t[1].text = 'IMSAFE'
                else:
                    t[1].text = ''
            self.layout.add_widget(grid_entry)

            if row == 0:
                grid_entry = ButtonGridEntry(coords=(row, 2), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete'
            else:
                grid_entry = ButtonGridEntry(coords=(row, 2), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = 'Delete'
                grid_entry.bind(on_press=lambda dbtn: self.crew_grid_delete(in_t[0]))

            self.layout.add_widget(grid_entry)

        except GridLayoutException:
            Logger.info('CRV: GRID:CREW..Layout exception: rows, current..'+str(self.layout.rows) + ' ' + str(row))

        # update the crewvalues
        if updcrewval:
            self.data.setsinglecrewvalue(-1, in_t)

        # add an empty crew row
        self.addcrew(t, 0)
        return


    #
    # Add a row to the crew grid.
    #
    # returns:
    # 0 found an empty slot and added ok
    # 1 nothing to add (empty crew list)
    # 2 need new grid row.
    #
    def addcrew(self, crewtoadd, forceadd=1):
        Logger.debug("CRV: addcrew. forceadd=%s", str(forceadd))

        self.data.appendcrew(crewtoadd)

        #
        # if empty input list, do nothing
        #
        empty = True
        if len(crewtoadd[0].text) > 0:
            empty = False
        if empty:
            return 1

        count = -1
        for n in self.data.getallcrew():
            count += 1
            if len(n[0].text) == 0:
                #
                # found empty - set row to data from a
                #
                n[0].text = crewtoadd[0].text
                n[1].active = crewtoadd[1].active

    def setobjectplus(self, index, obj, chld, par=None):
        #if index in self.data.getallcurrentcrew():
        if index in ['name', 'IMSAFE']:
            self.data.setcurrentcrewobject(index, chld)
            # this is just a convenience (think it also complicates things) wierd arg order too.
            if par is not None:
                par.add_widget(obj)

#
# ==================================================================
# CLASS... CRV
# ==================================================================
#
class CRV(App):
    Logger.info("CRV: Class CRV: INIT")

    if __name__ in '__main__':
        if platform != 'android':
            Window.size=(1280,697)
            #Window.size=(1920,1200)
            #Window.fullscreen = True   # yuk!
        #else:
            #Window.softinput_mode = 'below_target'
            #Window.softinput_mode = 'pan'   yuk

    approot = None
    keyboard_mode = 'dock'
    sm = None
    crvcolor = CrvColor()
    gps = CrvGPS(Logger)
    data = CrvData(Logger, crvcolor, App)
    logaudit = None
    modglobal.data = data

    crew = CrvCrew(data)
    #ftp = CrvFtp(data, data.linzhost, data.linzuser, data.linzpass)
    mycurl = CrvURL(data)
    boatlog = CrvLogBook(data, crew, gps)
    logarchive = CrvLogArchive(data)
    managecrew = CrvManageCrew(crew)
    managelocations = CrvManageLocations(boatlog)

    # set in config below
    managevessels = None

    gpsrefreshfunc = None
    netrefreshfunc = None

    # #
    #dummy = BTextInput
    #dummy.data = data

    sensoron_resume = False

    # control when to exit if escape or back is hit
    exitnext = False

    # #
    # camera = crvCamera()
    blockdropdown = False
    # donebuild = True   # dont think this is needed anymore - an experiment

    daynight = BooleanProperty(None)
    threshold = NumericProperty(modglobal.lightthreshold) #adapt this value according to your hardware
    daynightInterval = modglobal.lightchecktime

    #def __init__(self):
        # self.approot = None
        # self.sm = None
        # self.crvcolor = CrvColor()
        # self.gps = CrvGPS(Logger)
        # self.data = CrvData(Logger, self.crvcolor, App)
        # self.logaudit = None
        #
        # self.crvincidentmain = None
        #
        # self.crew = CrvCrew(self.data)
        # self.ftp = CrvFtp(self.data, self.data.linzhost, self.data.linzuser, self.data.linzpass)
        # self.boatlog = CrvLogBook(self.data, self.crew, self.gps)
        # self.logarchive = CrvLogArchive(self.data)
        # self.managecrew = CrvManageCrew(self.crew)
        # self.managelocations = CrvManageLocations(self.boatlog)
        #
        # # set in config below
        # self.managevessels = None
        #
        # self.gpsrefreshfunc = None
        # self.netrefreshfunc = None
        #
        # # #
        # self.dummy = BTextInput
        # self.dummy.data = self.data
        #
        # self.sensoron_resume = False
        #
        # # control when to exit if escape or back is hit
        # self.exitnext = False
        #
        # # #
        # # camera = crvCamera()
        # self.blockdropdown = False
        # # donebuild = True   # dont think this is needed anymore - an experiment
        #
        # self.daynight = BooleanProperty(None)
        # self.threshold = NumericProperty(modglobal.lightthreshold) #adapt this value according to your hardware
        # self.daynightInterval = modglobal.lightchecktime

    def autoDayNight(self, active):
        # if not active then turn off check for auto light sensor
        # otherwise check every lightchecktime seconds

        if lightSensor:
            if self.daynightInterval > 0:
                if active:
                    Logger.info('CRV: Light sensor enabled')
                    lightSensor.enable()
                    Clock.schedule_interval(self._isDay, self.daynightInterval)
                else:
                    Logger.info('CRV: Light sensor disabled')
                    lightSensor.disable()
                    Clock.unschedule(self._isDay)
                    self.daynightInterval = modglobal.lightchecktime

        if simlightSensor:
            if self.daynightInterval > 0:
                if active:
                    Logger.info('CRV: Sim Light sensor enabled')
                    Clock.schedule_interval(self._isDay, self.daynightInterval)
                else:
                    Logger.info('CRV: Sim Light sensor disabled')
                    Clock.unschedule(self._isDay)
                    self.daynightInterval = modglobal.lightchecktime

    def _isDay(self,dt):
        try:
            old = self.crvcolor.getschema()
            changed = False
            if simlightSensor:
                lightlevel = self.threshold - 1
            else:
                lightlevel = lightSensor.getLight()
            if lightlevel < self.threshold:
                if old:   # only change it if its not already there
                    Logger.info('CRV:ANDROID:Night Mode. Light level ' + str(lightlevel) )
                    self.do_dayswitch(False, False) # if value (2nd arg) True then Day else Night
                    self.daynight = False
                    changed = True
            else:
                if not old:
                    Logger.info('CRV:ANDROID:Day Mode. Light level ' + str(lightlevel) )
                    self.do_dayswitch(False, True) # if value (2nd arg) True then Day else Night
                    self.daynight = True
                    changed = True

            if changed:
                # we've transitioned, wait 5 minutes before trying again
                # (as light might fluctuate) - note: only do if check time less than 200 seconds
                if self.daynightInterval < 200:
                    if self.daynightInterval == 300:
                        self.daynightInterval = modglobal.lightchecktime
                    else:
                        self.daynightInterval = 300
                else:
                    self.daynightInterval = modglobal.lightchecktime

                Clock.unschedule(self._isDay)
                Clock.schedule_interval(self._isDay, self.daynightInterval)
        except:  # dont stress if you cant change day/night
            Logger.info('CRV:ANDROID:Day Mode. Exception changing day/night')

    @staticmethod
    def relativeFontHeight(perc):
        return perc * Window.height

    def on_resize(self, window, w, h):
        pass

    def on_start(self):
        if platform == 'linux':
            self.profile = cProfile.Profile()
            self.profile.enable()

    def on_stop(self):
        if platform == 'linux':
            self.profile.disable()
            self.profile.dump_stats('crv.profile')

    def on_close(self, instance):
        if self.data.getlogactive():
            self.data.datarecord.setvalue('screen', self.data.sm.current)
            self.data.shelf_save_current()
        self.boatlog.savelocations()

    def on_pause(self):
        Logger.info("CRV:on_pause")
        self.sensoron_resume = lightSensor.getenable()
        self.autoDayNight(False)
        self.gps.stopgps()

        return True

    def on_resume(self):
        Logger.info("CRV: on_resume")
        if self.sensoron_resume:
            self.autoDayNight(True)
        self.gps.startgps()


    # def boxpad(self, szy, colr=None):
    #     print "Debug: in def boxpad"
    #     b = BoxLayout(size_hint_y=szy)
    #     with b.canvas.before:
    #         Color(colr)
    #     self.rect = Rectangle(size=layout_instance.size,
    #     #                  pos=layout_instance.pos)
    #     b.add_widget(Label())
    #     return b

    def setupsettings(self):
        #
        # Set options. If required options are not set return False. Else True
        #

        # disable multitouch
        kivy.config.Config.set ( 'input', 'mouse', 'mouse,disable_multitouch' )

        self.data.setdatadir(str(self.config.get('VesselLog', 'datadir')))
        if self.managevessels is None:
            self.managevessels = CrvManageVessels(self.data)

        ret = True
        if not self.data.settidestation(str(self.config.get('crvapp', 'tidestation'))): ret = False
        if not self.data.setvesselname(str(self.config.get('crvapp', 'vesselname'))): ret = False
        if not self.data.setemaillog(str(self.config.get('Email', 'emaillog'))): ret = False

        c = str(self.config.get('VesselLog', 'cnzvessel'))   # eh??
        callsign = str(self.config.get('crvapp', 'vesselcallsign'))
        #callsign = str(self.config.get('VesselLog', 'vesselcallsign'))
        #self.data.datarecord.setobjectvariable('callsign', 'text', callsign)
        modglobal.lightthreshold = float(self.config.get('VesselLog', 'lightthreshold'))
        modglobal.lightchecktime = float(self.config.get('VesselLog', 'lightchecktime'))
        modglobal.gpsrefreshtime = float(self.config.get('VesselLog', 'gpsrefreshtime'))
        modglobal.netrefreshtime = float(self.config.get('VesselLog', 'netrefreshtime'))
        self.data.setmincrew(int(self.config.get('VesselLog', 'mincrew')))
        self.data.setmaxcrew(int(self.config.get('VesselLog', 'maxcrew')))
        #self.data.setenginetype(str(self.config.get('VesselLog', 'enginetype')))
        self.data.setshowkivy(str(self.config.get('VesselLog', 'showkivy')))
        self.data.setdoemaillog(str(self.config.get('Email', 'doemaillog')))
        self.data.setemailcrew(str(self.config.get('Email', 'emailcrew')))
        self.data.setemailtraining(str(self.config.get('Email', 'emailtraining')))
        self.data.sendemail.setemailserver(str(self.config.get('Email', 'emailserver')))
        self.data.sendemail.setemailuser(str(self.config.get('Email', 'emailuser')))
        self.data.sendemail.setemailpass(str(self.config.get('Email', 'emailpass')))

        self.use_kivy_settings = False
        if self.data.getshowkivy() == '1':
            self.use_kivy_settings = True

        self.title = self.data.getvesselname()

        return ret

    def animate(self, instance):
        # # create an animation object. This object could be stored
        # # and reused each call or reused across different widgets.
        # # += is a sequential step, while &= is in parallel
        # animation = Animation(pos=(100, 100), t='out_bounce')
        # animation += Animation(pos=(200, 100), t='out_bounce')
        # animation &= Animation(size=(500, 500))
        # animation += Animation(size=(100, 50))
        #
        # # apply the animation on the button, passed in the "instance" argument
        # # Notice that default 'click' animation (changing the button
        # # color while the mouse is down) is unchanged.
        # animation.start(instance)
        pass

    def build(self):

        crvcp = CrvProfile(Logger, 'build')

        #self.setwindowstuff()

        self.icon = 'coastguard.png'

        config = ConfigParser()

        self.settings_cls = SettingsWithTabbedPanel

        Builder.load_string(kv)
        self.approot = MyBoundBox(orientation='vertical')
        self.data.sm = ScreenManager(transition=NoTransition())
        self.approot.add_widget(self.data.sm)

        modglobal.statusbar = MyBoundBox(orientation='horizontal', size_hint_y=.05)

        modglobal.statusbarbox = BoxLayout(orientation='horizontal')
        modglobal.statusbar.add_widget(modglobal.statusbarbox)
        self.approot.add_widget(modglobal.statusbar)

        self.setupstatusbar(modglobal.statusbarbox)

        self.setupprimary()

        #self.crv_callbackdayswitch(None)
        self.do_dayswitch(False, True)

        #        Window.softinput_mode='pan'
        #        Window.softinput_mode='resize'
        Window.bind(on_close=self.on_close)
        Window.bind(on_resize=self.on_resize)

        # self.donebuild = True

        self.autoDayNight(True)  # set the auto scheduler going for screen sensor

        self.bind(on_start=self.post_build_init)  # setup key maps for special chars

        crvcp.eprof()

        self.boatlog.setchangetypes(self.changelogbytype, self.changeactionbytype)
        #return self.data.sm
        return self.approot

    def post_build_init(self, *args):
        if platform == 'android':
            import android
            Logger.debug('CRV: Android.. Mapping back Key')
            android.map_key(android.KEYCODE_BACK, 1001)

            modglobal.gridheight *= 2
        win = Window
        win.bind(on_keyboard=self.crv_key_handler)

    def crv_key_handler(self, window, keycode1, keycode2, text, modifiers):
        Logger.debug('CRV: Key: ' + str(keycode1))
        if keycode1 in [27, 1001]:
            self.hide_kbd_or_exit()
            return True
        return False

    def hide_kbd_or_exit(self, *args):
        if not self.exitnext:
            #if platform == "android":    ??????
            #    android.hide_keyboard()
            if self.data.sm.current == 'screen_main':
                self.exitnext = True
                Clock.schedule_once(lambda *args: setattr(self, "exitnext", False), 2)
        else:
            if self.data.sm.current == 'screen_main':
                Logger.debug('CRV: Key: STOP')
                self.stop()

    def updatestatusbar(self, doforce):
        # setup clock for every second
        if not self.data.statusbarclocktime:
            self.data.statusbarclocktime = True
            # Clock.schedule_interval(self.logtimer, 1.0)
            Clock.schedule_interval(partial(self.logtimer, 0), 1.0)

        # setup clock to update rest of statusbar ever 15 seconds (except network)
        # (run it now as well)
        self.logtimer(1)
        if doforce or not self.data.statusbarclockupd:
            if doforce:
                if self.gpsrefreshfunc is not None:
                    Clock.unschedule(self.gpsrefreshfunc)
            self.data.statusbarclockupd = True
            if modglobal.gpsrefreshtime > 0:
                self.gpsrefreshfunc = partial(self.logtimer, 1)
                Clock.schedule_interval(self.gpsrefreshfunc, modglobal.gpsrefreshtime)

        # setup clock to update network part of statusbar ever 30 seconds
        # (run it now as well)
        self.logtimer(2)
        if doforce or not self.data.statusbarclocknet:
            if doforce:
                if self.netrefreshfunc is not None:
                    Clock.unschedule(self.netrefreshfunc)
            self.data.statusbarclocknet = True
            if modglobal.netrefreshtime > 0:
                self.netrefreshfunc = partial(self.logtimer, 2)
                Clock.schedule_interval(self.netrefreshfunc, modglobal.netrefreshtime)

    def logtimer(self, dotime, *largs):
        """
        Update statusbar values from a timer.
        :param dotime:
            0 = do clock (called every second)
            1 = do rest - except for network (called every 15 seconds)
            2 = do network (every 30 seconds)
        """
        #if self.data.statusbarclockspaused:
        #    return True

        #if modglobal.alstatusbarparent is not None and not modglobal.alstatusbarparent.focused:
        if modglobal.alstatusbarparent is not None:
            if modglobal.alstatusbarparent.dropdown is not None and \
                            modglobal.alstatusbarparent.dropdown.attach_to is None:
                self.data.closehints()

        if dotime == 0:
            s = self.data.getnow(retlist=True)
            sday = s[1]
            sdate = s[2]
            stime = s[3]
            #sday = datetime.datetime.now().strftime("%A")
            #sdate = datetime.datetime.now().strftime("%x")
            #stime = datetime.datetime.now().strftime("%X")
            oday = self.data.datarecord.getobject('statusbarday')
            odate = self.data.datarecord.getobject('statusbardate')
            otime = self.data.datarecord.getobject('statusbartime')

            oday.text = sday
            odate.text = sdate
            otime.text = stime

            #n = self.gps.getgps()

        elif dotime == 1:
            ogps = self.data.datarecord.getobject('statusbargps')

            try:

                self.screenupdateheader(None)

                g = self.gps.gps_location
                if len(g) > 0:
                    [lat, lon] = g.split(':', 2)
                    g = lat + ' ' + lon
                    ogps.text = g
                else:
                    ogps.text = ''
            except:
                ogps = ''

            # we need to work out how to count background threads.
            # we arent actually using any at the moment, so thats cool.

        elif dotime == 2:
            t = self.data.datarecord.getobject('statusbarnet')
            if self.data.have_internet():
                t.text = 'Network Alive'
            else:
                t.text = 'No Network'
        else:
            pass

        return True

    def callbackstatusbar(self, instance):
        Logger.info('CRV:click')
        for w in self.approot.walk():
            wtype = w.__class__.__name__
            aid = ''
            if w.id is not None:
                aid = w.id
            Logger.debug('CRV:WALK:APPROOT ' + wtype + ' id=' + str(aid))

        for s in self.data.sm.screens:
            for w in s:
                wtype = w.__class__.__name__
                aid = ''
                if w.id is not None:
                    aid = w.id
                Logger.debug('CRV:WALK:SM ' + s + ' ' + wtype + ' id=' + str(aid))

    def do_dayswitch(self, manual, value):
        self.crvcolor.setschema(value)
        self.daynight = value
        Window.clearcolor = self.crvcolor.getbgcolor()

        w = self.data.datarecord.getobject('statusbarsensor')
        if w:
            if value:
                w.text = 'Day'
            else:
                w.text = ''

        # if called manually then turn off auto sensor (have to restart app to get it back)
        if manual:
            self.autoDayNight(False)

    def crv_callbackdayswitch(self, instance):
        v = not self.daynight
        self.do_dayswitch(True, v)

    def setupstatusbar(self, statusbar):
        # statusbar is
        # |day|date|time| Log Active (or not)     ....      |GPS Satellites|Network conn|numthreads|

        b0 = BoxLayout(size_hint_x=.4)
        sbox, sday = self.boxlabel(font='small')
        self.data.datarecord.setobjectplus('statusbarday', sbox, sday, b0, 'text')
        sbox, sdate = self.boxlabel(font='small')
        self.data.datarecord.setobjectplus('statusbardate', sbox, sdate, b0, 'text')
        sbox, stime = self.boxlabel(font='small')
        self.data.datarecord.setobjectplus('statusbartime', sbox, stime, b0, 'text')

        b1 = BoxLayout(size_hint_x=.6)
        b11 = BoxLayout(size_hint_x=.5)
        b12 = BoxLayout(size_hint_x=.5)
        sbox, sgps = self.boxlabel(font='small')
        self.data.datarecord.setobjectplus('statusbargps', sbox, sgps, b11, 'text')
        #sbox, sactive = self.boxlabel(font='small')
        #self.data.datarecord.setobjectplus('statusbaractive', sbox, sactive, b12, 'text')
        sbox, snet = self.boxlabel(font='small')
        self.data.datarecord.setobjectplus('statusbarnet', sbox, snet, b12, 'text')

        dayswitch = Button(font=modglobal.default_tiny_font_size, size_hint=(.3,1))
        dayswitch.bind(on_press=self.crv_callbackdayswitch)
        self.data.datarecord.setobject('statusbarsensor', dayswitch, 'button')
        b12.add_widget(dayswitch)

        b1.add_widget(b11)
        b1.add_widget(b12)
        statusbar.add_widget(b0)
        statusbar.add_widget(b1)

    def setupprimary(self):
        self.data.sm.clear_widgets()

        # check for some missing settings and enter settings screen if required

        allsettingsok = self.setupsettings()  # check to see if we need to force settings.

        if not allsettingsok:
            # a new install - or some bad settings.
            # create the settings screen.

            if not self.data.sm.has_screen('screen_settings2'):
                settings2 = self.crv_setup_settings_required()
                self.crv_settings_set_text(True)
                self.data.sm.add_widget(settings2)
            self.data.sm.current = 'screen_settings2'

        self.setupall(0)

    def setupall(self, n):
        self.data.clearcurrentlog(False)

        if not self.data.sm.has_screen('screen_main'):
            screen_main = self.crv_setup_main_screen()
            self.data.sm.add_widget(screen_main)

        self.data.dotides(self)

        if not self.data.sm.has_screen('screen_crvweather'):
            crvweather = self.crv_setup_weather_screen()
            self.data.sm.add_widget(crvweather)

        if not self.data.sm.has_screen('screen_crvoperational'):
            crvoperational = self.crv_setup_operational_screen()
            self.data.sm.add_widget(crvoperational)

        if not self.data.sm.has_screen('screen_plcheck'):
            screen_plcheck = self.crv_setup_plcheck()
            self.data.sm.add_widget(screen_plcheck)

        if not self.data.sm.has_screen('screen_ptcheck'):
            screen_ptcheck = self.crv_setup_ptcheck()
            self.data.sm.add_widget(screen_ptcheck)

        if not self.data.sm.has_screen('screen_reccheck'):
            screen_reccheck = self.crv_setup_reccheck()
            self.data.sm.add_widget(screen_reccheck)

        if not self.data.sm.has_screen('screen_crvclose'):
            crvclose = self.crv_setup_closelog_screen()
            self.data.sm.add_widget(crvclose)

        if not self.data.sm.has_screen('screen_boatlog'):
            sboatlog = self.crv_setup_boatlog_screen()
            self.data.sm.add_widget(sboatlog)

        # if its not none, then it's probably set to the screen settings
        if self.data.sm.current is None:
            self.data.sm.current = 'screen_main'

        return


    def close_settings(self, *args):
        super(CRV, self).close_settings()

        # before heading back to main screen, ensure required
        self.data.sm.current = 'screen_settings2'


    #
    # Setup config screen
    #
    def build_config(self, config):
        ddir = self.user_data_dir
        self.data.setdatadir(ddir)

        self.logaudit = CrvLogAudit(self.data)
        self.data.setlogaudit(self.logaudit)

        config.setdefaults('crvapp', {
            'vesselname': '',
            'vesselcallsign': '',
            'tidestation': '',
            'enginetype': 'Outboard',
        })
        config.setdefaults('VesselLog', {
            'cnzvessel': True,
            'mincrew': 3,
            'maxcrew': 7,
            'lightthreshold': 50.0,
            'lightchecktime': 10.0,
            'gpsrefreshtime': 15.0,
            'netrefreshtime': 30.0,
            'showkivy': False,
            'posscrew': ddir,
            'datadir': ddir,
        })
        config.setdefaults('Email', {
            'doemaillog': True,
            'emailcrew': '',
            'emaillog': '',
            'emailtraining': '',
            'emailserver': '',
            'emailuser': '',
            'emailpass': '',
        })

    def build_settings(self, settings):
        settings.add_json_panel('Vessel Log',
                                self.config,
                                data=settings_vesslog_json)
        settings.add_json_panel('Email',
                                self.config,
                                data=settings_email_json)

    def on_config_change(self, config, section,
                         key, value):
        ustatbar = False
        if key == 'showkivy':
            self.use_kivy_settings = False
            if value == '1':
                self.use_kivy_settings = True
        elif key == 'cnzvessel':
            self.data.cnzvessel = bool(value)
        elif key == 'lightthreshold':
            modglobal.lightthreshold = float(value)
        elif key == 'lightchecktime':
            modglobal.lightchecktime = float(value)
        elif key == 'gpsrefreshtime':
            ustatbar = True
            modglobal.gpsrefreshtime = float(value)
        elif key == 'netrefreshtime':
            ustatbar = True
            modglobal.netrefreshtime = float(value)
        elif key == 'mincrew':
            self.data.setmincrew(value)
        elif key == 'maxcrew':
            self.data.setmaxcrew(value)
        elif key == 'enginetype':
            self.data.setenginetype(value)
        #elif key == 'enablecamera':
        #    if value == '1':
        #        self.data.setenablecamera(True)
        #    else:
        #        self.data.setenablecamera(False)
        elif key == 'doemaillog':
            if value == '1':
                self.data.setdoemaillog(True)
            else:
                self.data.setdoemaillog(False)
        elif key == 'datadir':
            self.data.setdatadir(value)
        elif key == 'emaillog':
            self.data.setemaillog(value)
        elif key == 'emailserver':
            self.data.sendemail.setemailserver(value)
        elif key == 'emailuser':
            self.data.sendemail.setemailuser(value)
        elif key == 'emailpass':
            self.data.sendemail.setemailpass(value)

        self.updatestatusbar(True)

    def timecallbackfocus(self, instance, value):
        if not value:  # unfocused
            #
            # a :11  = 00:11
            # b 11:  = 11:00
            # c 1:   = 01:00
            # d 1:00 = 01:00
            # e 1:1  = 01:01
            # so get pos of :
            good = 1
            [h, m] = instance.text.split(':', 2)
            lh = len(h)
            lm = len(m)
            if lh > 2:
                good = 0
            elif lh == 0:
                h = '00'
            elif lh == 1:
                h = '0' + h

            if lm > 2:
                good = 0
            elif lm == 0:
                m = '00'
            elif lm == 1:
                m = '0' + m

            if good == 1:
                instance.text = h + ':' + m
                instance.background_color = self.crvcolor.getbgcolor()
            else:
                instance.background_color = self.crvcolor.getboldcolor()

        return True

    def tidehightimecallbackfocus(self, instance, value):
        #print 'tidehigh callback focus... ' + str(value)
        pass

    def tidehighheightcallbackfocus(self, instance, value):
        #print 'tidehighheight callback focus... ' + str(value)
        pass

    def tidelowtimecallbackfocus(self, instance, value):
        #print 'tidelow callback focus... ' + str(value)
        pass

    def tidelowheightcallbackfocus(self, instance, value):
        #print 'tidelowheight callback focus... ' + str(value)
        pass

    def portcallbackfocus(self, instance, value):
        if not value:  # unfocused
            col = self.crvcolor.getbgcolor()
            try:
                fin = float(self.data.datarecord.getobjecttext('portehoursfin'))
                stt = float(self.data.datarecord.getobjecttext('portehoursstart'))
                duration = float(fin-stt)

                self.data.datarecord.setobjecttext('portehoursdur', str(duration))
            except:
                col = self.crvcolor.getbgcolor()
            self.data.datarecord.getobject('portehoursdur').background_color=col

        return True

    def sbcallbackfocus(self, instance, value):
        if not value:  # unfocused
            col = self.crvcolor.getbgcolor()
            try:
                fin = int(self.data.datarecord.getobjecttext('sbehoursfin'))
                stt = int(self.data.datarecord.getobjecttext('sbehoursstart'))
                duration = int(fin) - int(stt)

                self.data.datarecord.setobjecttext('sbehoursdur', str(duration))
            except:
                col = self.crvcolor.getbgcolor()
            self.data.datarecord.getobject('sbehoursdur').background_color=col

        return True

    def fuelcallbackfocus(self, instance, value):
        used = 0
        added = 0
        fin = 0
        stt = 0
        #if not value:  # unfocused
        vesselfuel = self.data.currvessel[self.data.datarecord.managevesselfueltype]
        w = self.data.datarecord.getobject('fuellabel')
        if w is not None:
            if w.text == '':
                w.text = "CRV Fuel Type " + vesselfuel

        col = self.crvcolor.getbgcolor()
        try:
            stt = float(self.data.datarecord.getobjecttext('fuelstart'))
            sfin = self.data.datarecord.getobjecttext('fuelfin')
            if sfin == '':
                used = 0
            else:
                fin = float(sfin)
                used =  float(stt - fin)
            self.data.datarecord.setobjecttext('fuelused', str(used))
        except:
            col = self.crvcolor.getboldcolor()

        self.data.datarecord.getobject('fuelfin').background_color = col

        col = self.crvcolor.getbgcolor()
        try:
            added = float(self.data.datarecord.getobjecttext('fueladded'))
            fuelatend = stt - fin + added
            self.data.datarecord.setobjecttext('fuelatend', str(fuelatend))
        except:
            col = self.crvcolor.getboldcolor()

        self.data.datarecord.getobject('fuelatend').background_color = col

        try:
            cost = added * float(self.data.datarecord.getobjecttext('fuelprice'))
            self.data.datarecord.setobjecttext('fuelcost', str(cost))
        except:
            pass

        try:
            cost = added * float(self.data.datarecord.getobjecttext('fuelsuppliedprice'))
            self.data.datarecord.setobjecttext('fuelsuppliedcost', str(cost))
        except:
            pass
        return True

    # def dynamicdropdowncallbacktext(self, instance, value):
    #     """
    #     Called from a dropdown - can dynamically alter dropdown list based on input.
    #     """
    #     l = len(value)
    #     instance.dismissdropdown()
    #     dopts = instance.dropoptions
    #     if l > 0:
    #         d1 = []
    #         lvalue = value.lower()
    #         for o in dopts:
    #             if o.lower().find(lvalue) == 0:
    #                 d1.append(o)
    #         # if len(d1) == 1:
    #         #     value = d1[0]
    #         # else:
    #         #     showdrop = True
    #         #     instance.setdropoptions(d1)
    #         showdrop = True
    #         instance.setdropoptions(d1)
    #     else:
    #         showdrop = True
    #         instance.setdropoptions(dopts)
    #
    #     if showdrop:
    #         if not self.blockdropdown:
    #             try:
    #                 # if not ((not self.data.haveopenedlog) or self.blockdropdown):
    #                 if not (self.data.openingLog or self.blockdropdown):
    #                     instance.dropdown.open(instance)
    #             except:
    #                 pass
    #
    #     return True

    # @staticmethod
    # def staticdropdowncallbacktext(self, instance, value):
    #     """
    #     Called from a dropdown - just selects the value entered
    #     """
    #     Logger.info("CRV:staticdropdowncallbacktext")
    #
    #     if self.data.openingLog:
    #     #if not self.data.haveopenedlog:
    #         Logger.info("CRV:staticdropdowncallbacktext: refusing during initialisation")
    #         return True
    #
    #     l = len(value)
    #     instance.dismissdropdown()
    #     dopts = instance.dropoptions
    #     if l > 0:
    #         showdrop = False
    #     else:
    #         showdrop = True
    #         instance.setdropoptions(dopts)
    #
    #     if showdrop:
    #         try:
    #             instance.dropdown.open(instance)
    #         except:
    #             pass
    #
    #     return True
    #
    # def logcallbacktext(self, instance, value):
    #     Logger.info("CRV:logcallbacktext")
    #
    #     if self.data.openingLog:
    #     #if not self.data.haveopenedlog:
    #         Logger.info("CRV:logcallbacktext: refusing during initialisation")
    #         return True
    #
    #     self.dynamicdropdowncallbacktext(instance, value)
    #     self.changelogbytype(value)

    def changelogbytype(self, value):
        try:
            if len(value) == 0:
                value = 'Launch'

            sexc = 'len ' + value
            if value == 'Incident':
                if modglobal.crvincidentmain is None:   # no incident - create it
                    # modglobal.crvincidentmain = CrvIncidentMain(self, self.data)
                    # crvincident = modglobal.crvincidentmain.setup_main_screen()
                    # self.data.sm.add_widget(crvincident)
                    sexc = 'initialising incident'
                    self.crv_new_incident(None)
                    return

            sexc = 'getting loggroup of ' + value
            index = self.data.logrecord.loggroup['logtypesdisp'][value]
            # get the top level object for 'logentrybox'
            # It should have 2 children - 'logcommonlog' and something else.
            # Delete the something else and replace it with the object pointed to by
            # index.

            sexc = 'getting widgets'
            toplevel = self.data.logrecord.getobject('logentrybox')
            #currenttype = self.data.logrecord.getobject('logcurrenttype')
            commonlog = self.data.logrecord.getobject('logcommonlog')
            sexc = 'getting req ' + index
            reqtype = self.data.logrecord.getobject(index)

            # if currenttype is not None:
            #     toplevel.clear_widgets(currenttype)
            sexc = 'clear'
            toplevel.clear_widgets()
            toplevel.add_widget(commonlog)
            sexc = 'add'
            toplevel.add_widget(reqtype)
        except:
            Logger.info('CRV:LogType exception at ' + sexc)
        return True

    def changeactionbytype(self, invalue):
        try:
            sexc = 'len ' + invalue
            if len(invalue) > 0:
                value = invalue[:1].upper() + invalue[1:]

                sexc = 'getting index of ' + invalue
                index = self.data.logrecord.loggroup['logtypesincdisp'][value]
                # get the top level object for 'logentrybox'
                # It should have 2 children - 'logcommonlog' and something else.
                # Delete the something else and replace it with the object pointed to by
                # index.

                sexc = 'getting widgets'
                toplevel = self.data.logrecord.getobject('logentrybox')
                commonlog = self.data.logrecord.getobject('logcommonlog')

                sexc = 'getting req from ' + index
                reqtype = self.data.logrecord.getobject(index)

                # if currenttype is not None:
                #     toplevel.clear_widgets(currenttype)
                sexc = 'clear widget'
                toplevel.clear_widgets()
                sexc = 'add widget'
                toplevel.add_widget(commonlog)
                toplevel.add_widget(reqtype)
        except:
            Logger.info('CRV:INC:ActionType exception at ' + sexc)
        return True

    # def eactionbytype(self, value):
    #     if len(value) > 0:
    #         index = self.data.logrecord.loggroup['logtypesincdisp'][value]
    #         # get the top level object for 'logentrybox'
    #         # It should have 2 children - 'logcommonlog' and something else.
    #         # Delete the something else and replace it with the object pointed to by
    #         # index.
    #
    #         toplevel = self.data.logrecord.getobject('logentrybox')
    #         commonlog = self.data.logrecord.getobject('logcommonlog')
    #         reqtype = self.data.logrecord.getobject(index)
    #
    #         # if currenttype is not None:
    #         #     toplevel.clear_widgets(currenttype)
    #         toplevel.clear_widgets()
    #         toplevel.add_widget(commonlog)
    #         toplevel.add_widget(reqtype)
    #     return True

    # @staticmethod
    # def dticallbackfocus(self, instance, value):
    #     #Logger.debug('POS: focus ' + str(value))
    #     if instance.collide_point(*value.pos):
    #         Logger.debug('CRV: dti collide')
    #         instance.dropdown.open(instance)
    #     self.data.shelf_save_current()
    #
    #     return True
    #
    # #@staticmethod
    # @staticmethod
    # def dticallbackunfocus(instance):
    #     instance.dismissdropdown()
    #     return True
    #
    def screenupdateheader(self, inindex):
        # index comes in as screen name (screen_...)
        # the timestamp label is index by time_...
        # i.e. change ^screen_ to time_

        if inindex is None:
            index = self.data.sm.current
        else:
            index = inindex

        #tact = self.data.datarecord.getobject('activitylabel')

        tmstamp = self.data.datarecord.getobjectvariable('time', 'text', '')

        timeindex = index.replace('screen_', 'time_')

        if timeindex in self.data.datarecord.record:
            try:
                #
                # If an Incident or Incidents are active, then this takes Precedance.
                # In this case - instead of the Log time being displayed, display:
                # Incident (n of n) - TimeStarted Vesselname
                #
                # Otherwise - if no incident, display eith log time or inactive.
                #
                [tlab, tdat, tinfo] = self.data.datarecord.getobject(timeindex)

                if modglobal.crvincidentmain is not None and modglobal.crvincidentmain.numincidents > 0:
                    tlab.text = 'Incident Active (' + str(modglobal.crvincidentmain.currentincident+1) + ' of ' +\
                                str(modglobal.crvincidentmain.numincidents) + ')'
                    tdat.text = modglobal.crvincidentmain.currentincidents[modglobal.crvincidentmain.currentincident]['record'].getobjecttext('incalerttime')
                    ete, dist = modglobal.crvincidentmain.etedistance()

                    tmp = ''
                    if len(ete) > 0:
                        tmp = 'ete ' + ete + ' (mins) '
                    if len(dist) > 0:
                        tmp += 'distance ' + dist + ' (nm)'
                    if len(tmp) > 0: tinfo.text = tmp
                else:
                    if len(tmstamp) > 0:
                        tlab.text = '[b]Log Start:[/b]'
                        tdat.text = tmstamp
                    else:
                        tlab.text = '[b]Boatlog not open[/b]'
                        tdat.text = ''
            except:
                pass
        return

    def crv_image_click(self, instance):
        """
        Clicked on the image to open incident screen.
        If its not created then create it.
        If number of incidents is 0 then create new incident
        If number of incidents is 1 then view incident
        """

        if instance.last_touch.is_double_tap:
            if not self.data.getlogactive():
                self.data.dopopup('Log must be opened before an incident can be started', bindto=instance)
            else:
                instance.opacity = 1.0
                self.crv_new_incident(instance)

        return True

    def crv_new_incident(self, instance):
        """
        Clicked on the image to open incident screen.
        If its not created then create it.
        If number of incidents is 0 then create new incident
        If number of incidents is 1 then view incident
        """

        if not self.data.sm.has_screen('screen_crvincident_main'):
            modglobal.crvincidentmain = CrvIncidentMain(self, self.data, imageinstance=instance)
            crvincident = modglobal.crvincidentmain.setup_main_screen()
            self.data.sm.add_widget(crvincident)

        try:
            if instance is not None: instance.clickup()
        except:
            pass

        self.data.lastscreen = self.data.sm.current
        if modglobal.crvincidentmain.numincidents == 0:
            # create new incident - note this will create the screen for each incident
            # This could be quite heavy - but most of the time it will be 1
            modglobal.crvincidentmain.newincident(imageinstance=instance)

        # let the screenmanager_callback_onenter handle where the incident screen goes
        self.data.sm.current = 'screen_crvincident_main'

        return True

    def screencreateheader(self, index, forceheader=None, alttext=None, notime=False):
        # Creates a standard screen header.
        # if alttext is set, dont put image at top left - put text instead

        #szh = [4, 1]
        szy = .1

        b = BoxLayout(pos_hint_x=0, size_hint_y=szy)
        if 'screen_crvincident' in index:
            # dont display image for any incidents
            if index == 'screen_crvincident_main':
                ilab = MyLabel(text='[b]CURRENT INCIDENTS (the top one is always the active incident)[/b]', color=self.crvcolor.getfgcolor(), size_hint=[1, 1], halign='left', markup=True,
                       font_size=modglobal.default_large_font_size)
            else:
                if forceheader is not None:
                    s = '[b]Incident ' + forceheader + '[/b]'
                else:
                    s = '[b]Current Incident[/b]'

                ilab = MyLabel(text=s, color=self.crvcolor.getfgcolor(), size_hint=[1, 1], halign='left', markup=True,
                       font_size=modglobal.default_large_font_size)
            b.add_widget(ilab)
        else:
            if alttext is not None:
                b.add_widget(MyLabel(text='[b]'+alttext+'[/b]', color=self.crvcolor.getfgcolor(), size_hint=[.75, 1], halign='left', markup=True,
                       font_size=modglobal.default_large_font_size))
            else:
                image1 = ImageButton(source='cg.png', allow_stretch='true', opacity=10)
                image1.bind(on_release=self.crv_image_click)
                b.add_widget(image1)

            b1 = MyBoundBox(orientation='horizontal')
            timeindex = index.replace('screen_', 'time_')

            if timeindex not in self.data.datarecord.record:
                Logger.debug("CRV: logcreateheader: TIME INDEX DOES NOT EXIST: " + timeindex)
            else:
                if notime:
                    pass # we dont want a time field at top right
                else:
                    b2 = MyBoundBox(orientation='vertical')
                    b3 = MyBoundBox(orientation='horizontal')
                    tlab = MyLabel(color=self.crvcolor.getfgcolor(), size_hint=[4, 1], halign='left', markup=True)
                    b3.add_widget(tlab)

                    tdate = MyLabel(color=self.crvcolor.getfgcolor(), size_hint=[4, 1], halign='left', markup=True)

                    b3.add_widget(tdate)
                    b2.add_widget(b3)

                    tinfo = MyLabel(color=self.crvcolor.getfgcolor())
                    b2.add_widget(tinfo)
                    self.data.datarecord.setobject(timeindex, (tlab, tdate, tinfo), 'list')

                    b1.add_widget(b2)
                    b.add_widget(b1)
        return b

    # Checkbox with a label in a bordered boxlayout
    # returns layout, checkbox, label
    def boxcheckbox(self, cstr, szh=None, boxhint=None):
        if not szh:
            szh = [26, 1]
        if boxhint is None:
            b = MyBoundBox(orientation='horizontal')
        else:
            b = MyBoundBox(orientation='horizontal', size_hint=boxhint)
        l = MyLabel(text=cstr, size_hint=szh, halign='left')
        b.add_widget(l)
        c = CCheckBox()
        b.add_widget(c)
        return b, c, l

    # Checkbox with a label and a textbox in a bordered boxlayout
    # returns layout, checkbox, label, textbox
    def boxchecktextbox(self, cstr, szh=None, boxhint=None, infilter=''):
        if not szh:
            szh = [26, 1]
        if boxhint is None:
            b = MyBoundBox(orientation='horizontal')
        else:
            b = MyBoundBox(orientation='horizontal', size_hint=boxhint)
        bl = BoxLayout(orientation='horizontal', size_hint_x=.8)
        br = BoxLayout(orientation='horizontal', size_hint_x=.2)
        b.add_widget(bl)
        b.add_widget(br)
        halign='left'
        l = MyLabel(text=cstr, size_hint=szh, halign=halign)
        bl.add_widget(l)
        c = CCheckBox()
        bl.add_widget(c)
        t = MyTextInput()
        br.add_widget(t)
        return b, c, l, t

    # Textinput with a label in a bordered boxlayout
    # If no text in label, then make input readonly and color it.
    # Returns: layout, widget, label

    def boxtextbox(self, tstr, szh=None, boxhint=None, nolabel=False, nobox=False, infilter='', multiline=False, orientation='horizontal'):
        if not szh:
            szh = [6, 1]
        if nobox:
            if boxhint is None:
                b = BoxLayout(orientation=orientation)
            else:
                b = BoxLayout(orientation=orientation, size_hint=boxhint)
        else:
            if boxhint is None:
                b = MyBoundBox(orientation=orientation)
            else:
                b = MyBoundBox(orientation=orientation, size_hint=boxhint)

        if nolabel:
            l = None
        else:
            l = MyLabel(text=tstr, color=self.crvcolor.getfgcolor(), size_hint=szh, halign='left')
            b.add_widget(l)
        if len(tstr) == 0:
            w = MyLabel()
        else:
            if infilter != '':
                if infilter == 'float':
                    w = CFloatInput()
                else:
                    w = CTextInput(input_filter=infilter)
            else:
                # you cant use ctextinput for multiline as
                # the C means center - and it wont wrap.
                if multiline:
                    w = MyTextInput(multiline=multiline)
                else:
                    w = CTextInput(multiline=multiline)
        b.add_widget(w)

        # Returns the bounding widget followed by active widget, followed by label
        return b, w, l

    # Textinput with a label in a bordered boxlayout
    # If no text in label, then make input readonly and color it.
    # Returns: layout, widget, label
    def boxlabel(self, tstr='', szh=None, nobox=False, font=None):
        if not szh:
            szh = [6, 1]


        fs = ''
        if font == 'small':
            fs = modglobal.default_small_font_size
        # fonts need more work - as we've overrriden the default widget text size, it
        # takes precedence. WIP.

        if nobox:
            b = BoxLayout(orientation='horizontal')
        else:
            b = MyBoundBox(orientation='horizontal')

        if fs == '':
            l = MyLabel(text=tstr, color=self.crvcolor.getfgcolor(), size_hint=szh, halign='left')
        else:
            l = MyLabel(text=tstr, color=self.crvcolor.getfgcolor(), font_size=fs, halign='left')
        b.add_widget(l)

        # Returns the bounding widget followed by label
        return b, l

    # Textinput with a label in a bordered boxlayout- to input numerics
    # If no text in label, then make input readonly and color it.
    def boxnumbox(self, nstr, szh=None, boxhint=None, nobox=False):
        if not szh:
            szh = [6, 1]
        if nobox:
            if boxhint is None:
                b = BoxLayout(orientation='horizontal')
            else:
                b = BoxLayout(orientation='horizontal', size_hint=boxhint)
        else:
            if boxhint is None:
                b = MyBoundBox(orientation='horizontal')
            else:
                b = MyBoundBox(orientation='horizontal', size_hint=boxhint)

        b.add_widget(MyLabel(text=nstr, color=self.crvcolor.getfgcolor(), size_hint=szh, halign='left'))
        if len(nstr) == 0:
            w = MyLabel()
        else:
            w = CNumInput()
        b.add_widget(w)

        # Returns the bounding widget followed by active widget
        return b, w

    def timeinputfilter(self, s, fromundo):
        i = 5
        return s

    # Textinput with a label in a bordered boxlayout- to input numerics
    # If no text in label, then make input readonly and color it.
    def boxtimebox(self, tstr, szh=None, nobox=False, boxhint=None, orientation='horizontal'):
        if not szh:
            szh = [6, 1]
        if nobox:
            if boxhint is None:
                b = BoxLayout(orientation=orientation)
            else:
                b = BoxLayout(orientation=orientation, size_hint=boxhint)
        else:
            if boxhint is None:
                b = MyBoundBox(orientation=orientation)
            else:
                b = MyBoundBox(orientation=orientation, size_hint=boxhint)

        b.add_widget(MyLabel(text=tstr, color=self.crvcolor.getfgcolor(), size_hint=szh, halign='left'))
        if len(tstr) == 0:
            w = MyLabel()
        else:
            w = CTimeInput()
        b.add_widget(w)

        # Returns the bounding widget followed by active widget
        return b, w
    #
    # boxdropdown  with a label in a bordered boxlayout with dropdown
    # If no text in label, then make input readonly and color it.
    #def boxdropdown(self, dstr, dopts, callback_focus, callback_unfocus, callback_text, szh=None, nobox=False):
    def boxdropdown(self, dstr, dopts, szh=None, nodelete=False, readonly=False, multiline=False, orientation='horizontal', nobox=False, deftext=''):
        if not szh:
            szh = [6, 1]
        if nobox:
            b = BoxLayout(orientation=orientation)
        else:
            b = MyBoundBox(orientation=orientation)

        l = MyLabel(text=dstr, color=self.crvcolor.getfgcolor(), size_hint=szh, halign='left')
        b.add_widget(l)
        if len(dstr) == 0:
            w = MyLabel()
            b.add_widget(w)
        else:
            if nodelete:
                w = BTextInput(data=self.data, blayout=None, text=deftext, readonly=readonly, use_bubble=False, multiline=multiline)
            else:
                w = BTextInput(data=self.data, blayout=b, text=deftext, readonly=readonly, use_bubble=False, multiline=multiline)
            w.setcallbacks()
            w.setdropdefaults(dopts) # the default ones
            w.setdropoptions(dopts)
            w.setid(dstr)

            b.add_widget(w)

        # Returns the bounding widget followed by active widget
        return b, w, l

    def tidegraph(self):
        box0 = BoxLayout(orientation='vertical')
        box1 = BoxLayout(orientation='horizontal') 

        l = len(self.data.tides.tideplot)

        if l <= 0:
            box1.add_widget(MyLabel(text='Please restart the application\nif you see this.'))
        else:
            self.data.datarecord.getobject('tidetitle').text += ' (Height now is ' + str(round(self.data.tides.tideheightnow, 2)) + ' meters)'
            graph_theme = {
                    'label_options': {
                        'color': rgb('444444'),  # color of tick labels and titles
                        'bold': True},
                    #'background_color': rgb('f8f8f2'),  # back ground color of canvas
                    'tick_color': rgb('808080'),  # ticks and grid
                    'border_color': rgb('808080')}  # border drawn around each graph

            graph = Graph(size_hint=[1,1],  xlabel='Time', ylabel='Height',
                          y_grid_label=True, x_grid_label=True, padding=5,
                          x_grid=True, y_grid=False, y_ticks_minor=5, y_ticks_major=1,
                          xmin=math.ceil(self.data.tides.tideplot[0][0]), xmax=math.ceil(self.data.tides.tideplot[l-2][0]),
                          ymin=0, ymax=self.data.tides.maxheight, **graph_theme)
    #        plot = SmoothLinePlot(color=[1, 0, 0, 1])
            if len(self.data.tides.nowplot) > 0:
                self.data.tides.nowplot.append((self.data.tides.nowplot[0][0], self.data.tides.maxheight))
                plotnow = MeshLinePlot(color=self.crvcolor.getcolor('green'))
                #plotnow = SmoothLinePlot(color=self.crvcolor.getcolor('green'))
                plotnow.points = self.data.tides.nowplot
                graph.add_plot(plotnow)

            plot = SmoothLinePlot(color=self.crvcolor.getboldcolor())
            plot.points = self.data.tides.tideplot
            graph.add_plot(plot)
            box1.add_widget(graph)

        box0.add_widget(box1)
        return box0

    def tidegraph2(self):
         graph = Graph(xlabel='Time', ylabel='Height', x_ticks_minor=5,
                  x_ticks_major=25, y_ticks_major=1, background_color=self.crvcolor.getbgcolor(),
                  y_grid_label=True, x_grid_label=True, padding=5,
                  x_grid=True, y_grid=True, xmin=-0, xmax=100, ymin=-1, ymax=1)
         plot = MeshLinePlot(color=[1, 0, 0, 1])
         plot.points = [(x, math.sin(x / 10.)) for x in range(0, 101)]
         graph.add_plot(plot)

         return graph

    def settings_callback_onenter(self, instance):
        self.crv_callback_settings(instance)
        pass

    #
    # Called whenever a screen manager screen is displayed. 
    # instance.name is the name of the screen
    #
    def screenmanager_callback_onenter(self, instance):
        if instance is None:
            n = 'screen_main'
        else:
            n = instance.name
        Logger.debug('CRV: #### SMOnEnter.. ' + n)

        #if not self.donebuild:
        #    return True

        self.crew.setup()

        #
        # Depending on which screen we are entering, we can enable buttons
        # based on data entered.
        #
        self.data.lastscreen = n

        if n != 'screen_main':
            if n == 'screen_crvweather':
                self.crv_callback_checkoperationalstatus(None, None)
            elif n == 'screen_crvoperational':
                self.crv_callback_checkoperationalstatus(None, None)
            elif n == 'screen_crvclose':
                self.crv_callback_checkcloselogstatus(None, None)
            elif n == 'screen_boatlog':
                self.crv_callback_checkboatlogstatus(None, None)
            elif n == 'screen_settings2':
                self.crv_callback_checksettingsstatus(self, None)
            elif 'screen_crvincident' in n:
                self.crv_callback_checkincidentstatus(None, None)
            else:
                pass
        else:
            # Logger.debug('Clock: schedule')
            # Clock.schedule_interval(partial(self.logtimer, n), 1.0)
            self.screenupdateheader('screen_main')

            # if the log is active, then enable the following...
            # it's a kind of reverse logic in the def - could be made simpler.

            l = self.data.getlogactive()
            self.data.enablewidget('closing', l, False)
            self.data.enablewidget('butactivity', l, False)

            newlogtitle, canrecover = self.crv_setup_button_text()
            obj = self.data.datarecord.getobject('newlog')
            obj.label = newlogtitle
            txt = ''
            if canrecover:
                txt = 'Click on Recover to continue opening a boatlog that may have failed'

            else:
                if self.data.getlogactive():
                    txt = \
                        'A boatlog is active. You may view the settings, start logging activities' + \
                        ' or end the boatlog.\nThe log was started at ' + \
                        self.data.datarecord.getobjectvariable('time', 'text', '')
                    txt += '.\nYou may also double tap on the coastguard logo to start/view incidents.'
                else:
                    txt = \
                        'To start a new boatlog, tap on the open boatlog button.'
            self.data.datarecord.getobject('mainstatus').text = txt

        # lastly, update statusbar

        self.updatestatusbar(False)
        return True

    def crv_setup_plcheck(self):
        Logger.info('CRV:SETUP:prelaunch check')
        """
        Screen definition and setup for the pre launch check
        :return:
        """
        screen_plcheck = Screen(name='screen_plcheck')

        box = BoxLayout(orientation='vertical', padding=10)

        header = self.screencreateheader('screen_plcheck', alttext="PRE LAUNCH CHECKLIST")

        middle = BoxLayout(orientation='horizontal', size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        boxleft = MyBoundBox(orientation='vertical', pos_hint_x=0)
        boxright = MyBoundBox(orientation='vertical', pos_hint_x=0)
        middle.add_widget(boxleft)
        middle.add_widget(boxright)

        szh = [15, 1]
        x, c, l, t = self.boxchecktextbox('Visual Check of Tubes and Inflation', szh)
        self.data.datarecord.setobjectlist('plcvisual', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdefvisual', t, 'text')

        x, c, l, t = self.boxchecktextbox('Turn on Batteries', szh)
        self.data.datarecord.setobjectlist('plcbatteries', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdefbatteries', t, 'text')

        x, c, l, t = self.boxchecktextbox('Engine Oil and Water Checked', szh)
        self.data.datarecord.setobjectlist('plcoilandwater', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdefoilandwater', t, 'text')

        x, c, l, t = self.boxchecktextbox('Flushing Valves (X3) Closed', szh)
        self.data.datarecord.setobjectlist('plcflushvalves', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdefflushvalves', t, 'text')

        x, c, l, t = self.boxchecktextbox('Engine Cover Down and Locked', szh)
        self.data.datarecord.setobjectlist('plccoverdown', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdefcoverdown', t, 'text')

        x, c, l, t = self.boxchecktextbox('Salvage Pump Locked Closed', szh)
        self.data.datarecord.setobjectlist('plcpumplocker', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdefpumplocker', t, 'text')

        x, c, l, t = self.boxchecktextbox('Dehumidifier Removed', szh)
        self.data.datarecord.setobjectlist('plcdehumidifier', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdefdehumidifier', t, 'text')

        x, c, l, t = self.boxchecktextbox('Shore Power Disconnected', szh)
        self.data.datarecord.setobjectlist('plcshorepower', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdefshorepower', t, 'text')

        x, c, l, t = self.boxchecktextbox('Front Hatch Closed and Secure', szh)
        self.data.datarecord.setobjectlist('plcfronthatch', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('plcdeffronthatch', t, 'text')

        x, c, l, t = self.boxchecktextbox('Bow and Stern Lines Secure', szh)
        self.data.datarecord.setobjectlist('plcbowsternlines', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdefbowsternlines', t, 'text')

        x, c, l, t = self.boxchecktextbox('Transom Hatches Secure', szh)
        self.data.datarecord.setobjectlist('plctransomhatches', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdeftransomhatches', t, 'text')

        x, c, l, t = self.boxchecktextbox('Radios on (3)', szh)
        self.data.datarecord.setobjectlist('plcradioson', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdefradioson', t, 'text')

        x, c, l, t = self.boxchecktextbox('Nav Lights Operational', szh)
        self.data.datarecord.setobjectlist('plcnavlights', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdefnavlights', t, 'text')

        x, c, l, t = self.boxchecktextbox('Brief Crew to include IMSAFE', szh)
        self.data.datarecord.setobjectlist('plcbriefing', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdefbriefing', t, 'text')

        x, c, l, t = self.boxchecktextbox('Check Personal Protective Equipment', szh)
        self.data.datarecord.setobjectlist('plcpersonal', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdefpersonal', t, 'text')

        x, c, l, t = self.boxchecktextbox('Aerials Up (outside shed)', szh)
        self.data.datarecord.setobjectlist('plcaerials', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdefaerials', t, 'text')

        x, c, l, t = self.boxchecktextbox('Nav Units On (outside shed)', szh)
        self.data.datarecord.setobjectlist('plcnavunits', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdefnavunits', t, 'text')

        x, c, l, t = self.boxchecktextbox('Nav Check', szh)
        self.data.datarecord.setobjectlist('plcnavcheck', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('plcdefnavcheck', t, 'text')

        footer.add_widget(MyLabel(text='Note any pre voyage defects in\nboxes provided and click Back when complete'))
        button1 = MyButton(text='Back')
        button1.bind(on_release=self.crv_callback_lastscreen)

        footer.add_widget(button1)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_plcheck.add_widget(box)
        return screen_plcheck

    def crv_setup_ptcheck(self):
        Logger.info('CRV:SETUP:prelaunch tractor check')
        """
        Screen definition and setup for the pre launch tractor check
        :return:
        """
        screen_ptcheck = Screen(name='screen_ptcheck')

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        header = self.screencreateheader('screen_ptcheck', alttext="TRACTOR LAUNCH CHECKLIST")

        middle = BoxLayout(orientation='horizontal', size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        boxleft = MyBoundBox(orientation='vertical', pos_hint_x=0)
        middle.add_widget(boxleft)

        s1, x, l = self.boxdropdown('Tractor (in)', self.crew.posscrewlist, szh)
        x1 = None
        self.data.datarecord.settractorin(x, x1)
        boxleft.add_widget(s1)

        boxleft.add_widget(Label(text=''))

        x, c, l, t = self.boxchecktextbox('Tractor Connected', [1, 1])
        self.data.datarecord.setobjectlist('pltconnected', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('pltdefconnected', t, 'text')

        x, c, l, t = self.boxchecktextbox('Drawbar Lock Pin engaged', [1, 1])
        self.data.datarecord.setobjectlist('pltlockpin', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('pltdeflockpin', t, 'text')

        x, c, l, t = self.boxchecktextbox('Wheel Chocks Removed', [1, 1])
        self.data.datarecord.setobjectlist('pltchocks', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('pltdefchocks', t, 'text')

        footer.add_widget(MyLabel(text='Note any pre voyage tractor defects in\nboxes provided and click Back when complete'))
        button1 = MyButton(text='Back')
        button1.bind(on_release=self.crv_callback_lastscreen)

        footer.add_widget(button1)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_ptcheck.add_widget(box)
        return screen_ptcheck

    def crv_setup_reccheck(self):
        Logger.info('CRV:SETUP:recovery check')
        """
        Screen definition and setup for the recovery check
        :return:
        """
        screen_reccheck = Screen(name='screen_reccheck')

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        header = self.screencreateheader('screen_reccheck', alttext="RECOVERY CHECKLIST", notime=True)
        extraheader = BoxLayout(orientation='horizontal')
        header.add_widget(extraheader)

        middle = BoxLayout(orientation='horizontal', size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        boxleft = MyBoundBox(orientation='vertical', pos_hint_x=0)
        boxmiddle = MyBoundBox(orientation='vertical', pos_hint_x=0)
        boxright = MyBoundBox(orientation='vertical', pos_hint_x=0)
        middle.add_widget(boxleft)
        middle.add_widget(boxmiddle)
        middle.add_widget(boxright)

        #==============================================
        s1, x, l = self.boxdropdown('Tractor\n(out)', self.crew.posscrewlist, szh)
        x1 = None
        self.data.datarecord.settractorout(x, x1)
        extraheader.add_widget(s1)

        w, x = self.boxtimebox('Time Out', szh=[1,1])
        self.data.datarecord.setobjectplus('rectimeout', w, x, extraheader, 'text')

        x, c, l, t = self.boxchecktextbox('Vessel Washed\nand Cleaned', szh)
        self.data.datarecord.setobjectlist('recwashed', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('recdefwashed', t, 'text')

        x, c, l, t = self.boxchecktextbox('Visual Check of\nTubes and Inflation', szh)
        self.data.datarecord.setobjectlist('rectubes', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('recdeftubes', t, 'text')

        x, c, l, t = self.boxchecktextbox('Lift Engine Cover', szh)
        self.data.datarecord.setobjectlist('recengineoil', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('recdefengineoil', t, 'text')

        x, c, l, t = self.boxchecktextbox('Check Bilge for\nWater/Oil', szh)
        self.data.datarecord.setobjectlist('recbilge', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('recdefbilge', t, 'text')

        x, c, l, t = self.boxchecktextbox('Check and Clean\nSand Trap', szh)
        self.data.datarecord.setobjectlist('recsandtrap', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('recdefsandtrap', t, 'text')

        x, c, l, t = self.boxchecktextbox('Engine Flushed', szh)
        self.data.datarecord.setobjectlist('recflushed', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('recdefflushed', t, 'text')

        x, c, l, t = self.boxchecktextbox('(Re)Stow Gear and\nCheck for Damage', szh)
        self.data.datarecord.setobjectlist('recstowgear', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('recdefstowgear', t, 'text')

        x, c, l, t = self.boxchecktextbox('Tow Ropes and\nLines Stowed', szh)
        self.data.datarecord.setobjectlist('recstowropes', x, [c, l], boxleft, 'checkbox')
        self.data.datarecord.setobject('recdefstowropes', t, 'text')

        x, c, l, t = self.boxchecktextbox('Fuel Tank Refilled\n(Full)', szh)
        self.data.datarecord.setobjectlist('recfuel', x, [c, l], boxmiddle, 'checkbox')
        self.data.datarecord.setobject('recdeffuel', t, 'text')
        #--------
        x, c, l, t = self.boxchecktextbox('Fuel Computer Reset\nif just Filled', szh)
        self.data.datarecord.setobjectlist('recfuelreset', x, [c, l], boxmiddle, 'checkbox')
        self.data.datarecord.setobject('recdeffuelreset', t, 'text')

        x, c, l, t = self.boxchecktextbox('Check Windscreen\nWasher', szh)
        self.data.datarecord.setobjectlist('recwindscreen', x, [c, l], boxmiddle, 'checkbox')
        self.data.datarecord.setobject('recdefwindscreen', t, 'text')

        x, c, l, t = self.boxchecktextbox('Open Salvage\nPump Cover', szh)
        self.data.datarecord.setobjectlist('recpumpcover', x, [c, l], boxmiddle, 'checkbox')
        self.data.datarecord.setobject('recdefpumpcover', t, 'text')

        x, c, l, t = self.boxchecktextbox('Wash Pump if Used', szh)
        self.data.datarecord.setobjectlist('recpump', x, [c, l], boxmiddle, 'checkbox')
        self.data.datarecord.setobject('recdefpump', t, 'text')

        x, c, l, t = self.boxchecktextbox('Refuel Salvage\nPump and Tank', szh)
        self.data.datarecord.setobjectlist('recpumpfuel', x, [c, l], boxmiddle, 'checkbox')
        self.data.datarecord.setobject('recdefpumpfuel', t, 'text')

        x, c, l, t = self.boxchecktextbox('Check Lifejackets\nand Hang to Dry', szh)
        self.data.datarecord.setobjectlist('recpfds', x, [c, l], boxmiddle, 'checkbox')
        self.data.datarecord.setobject('recdefpfds', t, 'text')

        x, c, l, t = self.boxchecktextbox('Check Survival Suits\n(and Hang)', szh)
        self.data.datarecord.setobjectlist('recsuits', x, [c, l], boxmiddle, 'checkbox')
        self.data.datarecord.setobject('recdefsuits', t, 'text')

        x, c, l, t = self.boxchecktextbox('Check VHF\nHandhelds (X2)', szh)
        self.data.datarecord.setobjectlist('rechandhelds', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('recdefhandhelds', t, 'text')

        x, c, l, t = self.boxchecktextbox('Replenish Provisions', szh)
        self.data.datarecord.setobjectlist('recprovs', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('recdefprovs', t, 'text')
        #-------
        x, c, l, t = self.boxchecktextbox('Any Damage\nRecorded/Reported', szh)
        self.data.datarecord.setobjectlist('recdamage', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('recdefdamage', t, 'text')

        x, c, l, t = self.boxchecktextbox('Dehumidifier\nConnected', szh)
        self.data.datarecord.setobjectlist('recdehumidifier', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('recdefdehumidifier', t, 'text')

        x, c, l, t = self.boxchecktextbox('Turn off Batteries', szh)
        self.data.datarecord.setobjectlist('recbatteries', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('recdefbatteries', t, 'text')

        x, c, l, t = self.boxchecktextbox('Shore Power\nConnected', szh)
        self.data.datarecord.setobjectlist('recshorepower', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('recdefshorepower', t, 'text')

        x, c, l, t = self.boxchecktextbox('Report Vessel\nReady', szh)
        self.data.datarecord.setobjectlist('recready', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('recdefready', t, 'text')

        x, c, l, t = self.boxchecktextbox('Tractor Cleaned', szh)
        self.data.datarecord.setobjectlist('reccleaned', x, [c, l], boxright, 'checkbox')
        self.data.datarecord.setobject('recdefcleaned', t, 'text')

        footer.add_widget(MyLabel(text='Note any pre voyage tractor defects in\nboxes provided and click Back when complete'))
        button1 = MyButton(text='Back')
        button1.bind(on_release=self.crv_callback_lastscreen)
        footer.add_widget(button1)

        x, c, l = self.boxdropdown('Completed by', self.crew.posscrewlist, szh)
        self.data.datarecord.setobjectplus('reccompletedby', x, c, footer, 'drop')

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_reccheck.add_widget(box)
        return screen_reccheck

    def crv_callback_plcheck(self, instance):
        '''
        This will display the pre launch checklist.
        This should probably be softcoded - as different vessels may have
        different checklists.
        '''
        self.data.sm.current = 'screen_plcheck'
        if instance is not None: instance.clickup()
        return True

    def crv_callback_ptcheck(self, instance):
        # tractor launch checklist

        self.data.sm.current = 'screen_ptcheck'
        if instance is not None: instance.clickup()
        return True

    def crv_callback_reccheck(self, instance):
        # tractor launch checklist

        self.data.sm.current = 'screen_reccheck'
        if instance is not None:
            instance.clickup()

        return True

    def crv_callback_newlog(self, instance):
        #self.animate(instance)
        activechanged = False
        b = self.data.datarecord.getobject('weathercancel')
        if not self.data.getlogactive():
            b.text = 'Cancel'
            self.data.dotides(self)

            # log active may change in here if there is a saved file.
            # if it does change, then this will return true.
            # This is used below in the selection for the screen.

            activechanged = self.data.openlog(self.boatlog, self.crew)
            self.screenmanager_callback_onenter(None)

        if self.data.getlogactive():
            # if the log is active - you don't want to be able to cancel it
            # so cancel becomes Home - to return to home screen
            b.text = 'Home'

        self.screenupdateheader('screen_crvweather')
        # we also have to enable/disable a few widgets
        self.data.datarecord.getobjectcheckobject('prelaunch').disabled = self.data.getlogactive()
        self.data.datarecord.getobjectcheckobject('crewmeetsops').disabled = self.data.getlogactive()
        self.data.datarecord.getobjectcheckobject('vesseloperational').disabled = self.data.getlogactive()
        self.data.datarecord.getobject('homeoperational').disabled = self.data.getlogactive()

        self.crv_callback_checkoperationalstatus(None, None)

        if not self.data.sm.has_screen('screen_crvincident_main'):
            modglobal.crvincidentmain = CrvIncidentMain(self, self.data, imageinstance=instance)
            crvincident = modglobal.crvincidentmain.setup_main_screen()
            self.data.sm.add_widget(crvincident)

        if activechanged:
            self.data.sm.current = 'screen_main'
        else:
            self.data.sm.current = 'screen_crvweather'

        if instance is not None: instance.clickup()
        return True

    #
    # If here - then the log has just been opened
    #
    def crv_callback_openthelog(self, instance):
        self.data.setlogactive(True)
        self.logaudit.writeaudit('Opened new boat log')
        self.data.sm.current = 'screen_main'
        self.screenupdateheader('screen_main')

        self.data.shelf_save_current()   # to save logactive

        if instance is not None: instance.clickup()

    def crv_send_logs(self, instance):
        if modglobal.msgbox is not None:
            try:
                modglobal.msgbox.popup.dismiss()
            except:
                pass

        w = self.data.datarecord.getobject('closelogbutton')
        if w is not None:
            try:
                w.clickup()
            except:
                pass

        if not self.data.sm.has_screen('screen_display_update'):
            settings_display_update = self.crv_setup_display_update()
            self.data.sm.add_widget(settings_display_update)

        if not self.data.have_internet():
            MessageBox(self, titleheader="No Internet Connection",
                   message=".")
            return

        # Set a process in place to try to send old unsent logs
        self.data.retrylogsend()

        self.crv_callback_home(instance)
        return

    def crv_close_home(self, instance):
        if modglobal.msgbox is not None:
            try:
                modglobal.msgbox.popup.dismiss()
            except:
                pass

        w = self.data.datarecord.getobject('closelogbutton')
        if w is not None:
            try:
                w.clickup()
            except:
                pass

        self.crv_callback_home(instance)

    #
    # If here - then the open log has just been closed
    #
    def crv_really_closethelog(self, instance):
        if modglobal.msgbox is not None:
            try:
                modglobal.msgbox.popup.dismiss()
            except:
                pass

        w = self.data.datarecord.getobject('closelogbutton')
        if w is not None:
            try:
                w.clickup()
            except:
                pass

        self.data.save_engineinfo()

        # archive the logs
        self.data.resetlog()

        # logrecord is the boat log
        # datarecord is the operational log
        #self.data.formatandsendlog(self.data.logrecord, self.data.datarecord)

        self.logaudit.writeaudit('Closed boat log')
        Logger.info('CRV: Closed boat log')

        self.crew.doclear()
        self.boatlog.doclear()

        modglobal.msgbox = MessageBox(self, titleheader="Mail logs now?",
                      message="Would you like to email the log now?\n"+
                              "This will attempt to send all unsent logs.\n"+
                              "(please note: this can also be done in the\n" +
                              "Log Archive screen located in the Home screen).",
                      options={"YES": self.crv_send_logs, "NO": self.crv_close_home})

    def crv_callback_closethelog(self, instance):
        if modglobal.msgbox is not None:
            try:
                modglobal.msgbox.popup.dismiss()
            except:
                pass

        #if not self.data.sm.has_screen('screen_display_update'):
        #    settings_display_update = self.crv_setup_display_update()
        #    self.data.sm.add_widget(settings_display_update)

        #self.data.lastscreen = 'screen_main'

        #
        # Check to see if an incident is open - and if so, warn.
        #
        if modglobal.crvincidentmain is not None:
            if modglobal.crvincidentmain.numincidents > 0:
                modglobal.msgbox = MessageBox(self, titleheader="Incident Active",
                                         message="WARNING: An incident is currently active\n"+
                                                 "Are you sure you want to close the log?\n"+
                                                 "(please note: if you say yes then the active incident(s)\n" +
                                                 "will NOT be attached to this log and will remain active).",
                                         options={"YES": self.crv_really_closethelog, "NO": self.crv_close_home})
            else:
                self.crv_really_closethelog(instance)
        else:
            self.crv_really_closethelog(instance)
        return

    @staticmethod
    def doscreenshot(*largs):
        try:
            Window.screenshot(name='screenshot%(counter)04d.jpg')
            rstat = True
        except:
            rstat = False
        return rstat

    # def dotoggle(self, instance):
    #     if instance.text == 'Stop Camera':
    #         self.cam.play = False
    #         instance.text = 'Start Camera'
    #     else:
    #         self.cam.play = True
    #         instance.text = 'Stop Camera'

    # def crv_setup_camera_screen(self):
    #     smcamera = Screen(name='screen_crvcamera')
    #     try:
    #         box0 = BoxLayout(orientation='vertical')
    #         box1 = BoxLayout(orientation='horizontal')
    #         self.camwidget = Widget()
    #         self.cam = Camera()  # Get the camera
    #         # self.cam=Camera(resolution=(640,480), size=(500,500))
    #         # self.cam=Camera(resolution=(640,480))
    #
    #         button1 = MyButton(text='Snap', size_hint=(0.12, 0.12))
    #         button1.bind(on_press=self.doscreenshot)
    #         button2 = MyButton(text='Stop Camera', size_hint=(0.12, 0.12))
    #         button2.bind(on_press=self.dotoggle)
    #         box1.add_widget(button1)  # Add button to Camera Widget
    #         box1.add_widget(button2)  # Add button to Camera Widget
    #         self.camwidget.add_widget(self.cam)
    #         box0.add_widget(self.camwidget)
    #         smcamera.add_widget(box0)
    #         smcamera.add_widget(box1)
    #         print "created camera"
    #     except:
    #         print "camera exception"
    #
    #     smcamera.bind(on_enter=self.screenmanager_callback_onenter)
    #     return smcamera
    #
    # def crv_callback_camera(self, instance):
    #     print "in callback...Camera"
    #     if not self.data.sm.has_screen('screen_crvcamera'):
    #         #            crvcamera = self.camera.create()
    #         crvcamera = self.crv_setup_camera_screen()
    #         self.data.sm.add_widget(crvcamera)
    #
    #     self.data.sm.current = 'screen_crvcamera'
    #
    # #        self.camera.view()
    # #        self.data.sm.current = savecurrent
    #
    def crv_settings_set_text(self, labfirst):
        w = self.data.datarecord.getobject('settingshead')
        if w is not None:
            if labfirst:
                initialtext = 'It appears this is the first time this application has been used\n on this device.\n\n The following settings are required'
            else:
                initialtext = ''
            w.text = initialtext

    def crv_callback_settings(self, instance):
        #self.animate(instance)
        if self.data.sm.current in ['screen_crvweather', 'screen_crvoperational']:
            self.data.fromopenlog = self.data.sm.current

        if not self.data.sm.has_screen('screen_settings2'):
            settings2 = self.crv_setup_settings_required()
            self.crv_settings_set_text(False)
            self.data.sm.add_widget(settings2)

        if len(self.data.lastscreen) > 0:
            if self.data.lastscreen == 'screen_main':
                self.data.sm.current = 'screen_settings2'
            else:
                self.data.sm.current = self.data.lastscreen
            self.data.lastscreen = ''
        else:
            self.data.sm.current = 'screen_settings2'

        self.screenupdateheader('screen_settings2')
        #self.blockdropdown = True # yuk. couldnt think of another way to stop event firing

        #
        v = self.data.getvesselname()
        self.data.datarecord.setobjecttext('reqvessname', v)
        self.data.datarecord.setobjecttext('reqtidestation', self.data.gettidestation())
        self.data.datarecord.setobjecttext('reqemaillog', self.data.getemaillog())

        self.crew.getposscrewfile()

        if self.data.gettidestation() != '':

            self.data.dotides(self)

        #self.blockdropdown = False
        if instance is not None: instance.clickup()

        return True

    def confirm_newlog_yes(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        self.data.resetlog()
        self.crew.doclear()
        self.boatlog.doclear()
        self.crv_callback_home(None)

    def confirm_closelog_yes(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        w = self.data.datarecord.getobject('closingtime')
        w.text = ''
        self.data.shelf_save_current()
        self.crv_callback_home(None)

    def confirm_no(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()

    #
    # Selecting this cancel button will destroy all child widgets and start again.
    # We also have to destroy activity widgets, etc
    # (Actually - all this def does is open a popup to get confirmation -
    #  look in confirm_newlog_yes above - that does the actual work)
    #
    def crv_callback_cancel(self, instance):
        if self.data.getlogactive():
            self.crv_callback_home(instance)
        else:
            modglobal.msgbox = MessageBox(self, titleheader="Confirm Cancel", message="Cancel Open Log. ARE YOU SURE??",
                   options={"YES": self.confirm_newlog_yes, "NO": self.confirm_no})

        if instance is not None: instance.clickup()
    #
    # Cancel closing a log. Make sure closing time not set.
    #
    def crv_callback_closelogcancel(self, instance):
        modglobal.msgbox = MessageBox(self, titleheader="Confirm Cancel Close Log", message="Cancel Close Log. ARE YOU SURE??",
                   options={"YES": self.confirm_closelog_yes, "NO": self.confirm_no})
        if instance is not None: instance.clickup()

    def crv_callback_incident_cancel(self, instance):
        self.data.sm.current = self.data.lastscreen
        if instance is not None: instance.clickup()

    def crv_callback_sendcrewlist(self, instance):
        if not self.data.sm.has_screen('screen_display_update'):
            settings_display_update = self.crv_setup_display_update()
            self.data.sm.add_widget(settings_display_update)

        self.data.lastscreen = 'screen_crvoperational'

        ok = self.data.sendcrewlist()

        self.data.datarecord.setobjectvariable('crewlistsent', 'bool', True)
        self.crv_callback_checkoperationalstatus(instance)
        if instance is not None: instance.clickup()

    # def crv_callback_sendcrewlistdone(self, instance):
    #     self.data.datarecord.setobjectvariable('crewlistsent', 'bool', True)
    #     #self.data.setobjectmanual('crewlistsent', True)
    #     self.crv_callback_checkoperationalstatus(instance)

    def crv_callback_addsavecrew(self, instance):
        self.crv_callback_checkoperationalstatus(instance)
        if instance is not None: instance.clickup()

    #
    # Go back to home screen
    #
    def crv_callback_home(self, instance):
        if modglobal.msgbox is not None:
            try:
                modglobal.msgbox.popup.dismiss()
            except:
                pass

        # if instance is not None:
        #     try:
        #         instance.clickup()
        #     except:
        #         pass

        if self.data.fromopenlog != '':
            self.data.sm.current = self.data.fromopenlog
            self.data.fromopenlog = ''
        else:
            self.data.sm.current = 'screen_main'

    def setrequiredsettings(self):
        self.config.set('crvapp', 'vesselname', self.data.datarecord.getobjecttext('reqvessname'))
        self.config.set('crvapp', 'tidestation', self.data.datarecord.getobjecttext('reqtidestation'))
        self.config.set('Email', 'emaillog', self.data.datarecord.getobjecttext('reqemaillog'))

        self.config.write()

        self.setupsettings()

    def crv_callback_reqhomebutton(self, instance):
        """
        Called in required settings screen. We have all the required settngs, so we have
        to make them persistent. Then call home.
        """
        self.setrequiredsettings()

        self.data.dotides(self)
        self.crv_callback_home(instance)
        if instance is not None: instance.clickup()

    def location_callback_back(self, instance):
        """
        Go back to req settings screen (from whence you came)
        """
        self.boatlog.savelocations()
        self.crv_callback_settings(instance)
        if instance is not None: instance.clickup()

    def vessel_confirm_exit(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        self.stop()

    def vessel_confirm_tryagain(self, instance):
        if modglobal.msgbox is not None: modglobal.msgbox.popup.dismiss()
        self.crv_callback_managevessels(None)

    def vessel_callback_back(self, instance):
        """
        Go back to req settings screen (from whence you came)
        """
        if len(self.data.allvessels) == 0:
            modglobal.msgbox = MessageBox(self, titleheader="No Vessel Defined",
                   message="You must define a vessel\nin order to continue",
                   options={"Add vessel": self.vessel_confirm_tryagain,
                            "Exit Application": self.vessel_confirm_exit})
        else:
            self.data.savevessels()
            self.crv_callback_settings(instance)
        if instance is not None: instance.clickup()

    def audit_callback_back(self, instance):
        self.crv_callback_logarchive(instance)
        if instance is not None: instance.clickup()

    def crv_callback_settings_back(self, instance):
        """
        Go back to req settings screen (from whence you came)
        """
        self.managecrew.crewgridsave()
        self.crv_callback_settings(instance)
        if instance is not None: instance.clickup()

    @mainthread
    def displayaction(self, mess, icol='blue', cleargrid = False, enablebutton=False, progressval=-1, progressmax=-1):
        try:
            Logger.debug('CRV:ACTION..IN: mess:clear:enable:progval:progmax..:' + str(mess) + ':' + str(cleargrid) + ':' +
            str(enablebutton) + ':' + str(progressval) + ':' + str(progressmax))
            obj = self.data.datarecord.getobject('upddispgrid')
            pb = self.data.datarecord.getobject('upddisppb')
            if progressmax > 0:
                pb.max = progressmax
            if progressval > 0:
                pb.value = progressval
            else:
                if progressval == -3:
                    pb.value = 0
                if progressval == -2:
                    pb.value = pb.max
                else:
                    if pb.value+1 < pb.max:
                        pb.value += 1
                    else:
                        pb.value = pb.max

            if enablebutton:
                but = self.data.datarecord.getobject('upddispback')
                but.disabled = False
            if cleargrid:
                obj.clear_widgets()
                lab = self.data.datarecord.getobject('upddisplab')
                lab.color = self.crvcolor.getcolor(icol)
                lab.text = mess
                but = self.data.datarecord.getobject('upddispback')
                #but.disabled = True
                return None
        except:
            Logger.info('CRV:updatedisplay unknown exception')

        grid_entry = None
        try:
            if len(mess) > 0:
                row = obj.rows

                grid_entry = ActGridEntry(coords=(row, 0), size_hint_y=None, height=modglobal.gridheight, readonly=True)
                grid_entry.text = mess
                grid_entry.foreground_color = self.crvcolor.getcolor(icol)
                obj.rows += 1
                obj.add_widget(grid_entry)
                Logger.info('CRV: ACTION: ' + mess)
        except:
            Logger.info('CRV:updatedisplay grid exception')

        return grid_entry

    def crv_callback_logaudit(self, instance):

        if not self.data.sm.has_screen('screen_logaudit'):
            screen_logaudit = self.crv_setup_logaudit()
            self.data.sm.add_widget(screen_logaudit)

        self.logaudit.populate()
        self.data.sm.current = 'screen_logaudit'
        if instance is not None: instance.clickup()
        return True

    def crv_callback_requpdatetides(self, instance):

        if not self.data.sm.has_screen('screen_display_update'):
            settings_display_update = self.crv_setup_display_update()
            self.data.sm.add_widget(settings_display_update)

        mess = "Get latest tide tables"
        if instance is not None:
            if type(instance).__name__ == 'bool':
                # if type is boolean then we are updating the tide tables
                # (called from self.data.dotides). (probably because it doesn't exist.
                # The text is the first text to display in the action display
                mess = "Tide tables out of tide or not downloaded. Downloading Now. Press Back when complete"
        self.displayaction(mess, cleargrid=True, progressmax=-1, progressval=0)
        self.data.sm.current = 'screen_display_update'

        try:
            #self.data.statusbarclockspaused = True
            #self.crv_do_updatetides()
            mythread = threading.Thread(target=self.crv_do_updatetides_from_url)
            mythread.start()
        except:
            Logger.info('CRV: Unable to create thread to update tides')
            button = self.data.datarecord.getobject('upddispback')
            button.disabled = False

        if instance is not None and type(instance).__name__ != 'bool':
            instance.clickup()
        return True

    def crv_do_updatetides(self):
        button = self.data.datarecord.getobject('upddispback')
        button.disabled = False
        currentYear = datetime.datetime.now().year
        ts = self.data.gettidestation()
        fromfile = ts + ' ' + str(currentYear) + '.csv'
        tofile = os.path.join(self.data.datadir, ts + str(currentYear) + '.csv')

        # so update the tides. You need to use a thread as the ftp download
        # is blocking
        if not self.data.have_internet():
            MessageBox(self, titleheader="Cannot update tides",
                   message="Please ensure the network is connected and try again.")
            return

        g = self.displayaction("Connecting to " + self.data.linzhost)
        if self.ftp.connect():

            g = self.displayaction("Getting availability of tide information for " + ts)
            sz = self.ftp.getsize(fromfile)
            if sz > 0:
                g = self.displayaction('... ' + str(sz) + ' (bytes)')

                self.displayaction('', progressmax=sz, progressval=0)

                g = self.displayaction("Retrieving tide information for " + str(currentYear) + ' from ' + self.data.linzhost)

                ok = self.ftp.getfile(fromfile, tofile, self.displayaction, button)

                if not ok:
                    g.foreground_color = self.crvcolor.getboldcolor()

            else:
                g.foreground_color = self.crvcolor.getboldcolor()
                g = self.displayaction("tide information does not exist for " + str(currentYear), 'red')

            self.ftp.quit()
        else:
            g.foreground_color = self.crvcolor.getboldcolor()
            g = self.displayaction("Error connecting to " + self.data.linzhost, 'red')

        self.displayaction('', enablebutton=True, progressval=-2)
        #self.data.statusbarclockspaused = False

    def crv_do_updatetides_from_url(self):
        button = self.data.datarecord.getobject('upddispback')
        button.disabled = False
        currentYear = datetime.datetime.now().year
        ts = self.data.gettidestation()
        baseURL="http://www.linz.govt.nz/sites/default/files/docs/hydro/tidal-info/tide-tables/maj-ports/csv/"
        #v="http://www.linz.govt.nz/sites/default/files/docs/hydro/tidal-info/tide-tables/maj-ports/csv/Auckland%202016.csv"
        fromurl = baseURL + ts + '%20' + str(currentYear) + '.csv'
        tofile = os.path.join(self.data.datadir, ts + str(currentYear) + '.csv')

        # so update the tides. You need to use a thread as the ftp download
        # is blocking
        if not self.data.have_internet():
            MessageBox(self, titleheader="Cannot update tides",
                   message="Please ensure the network is connected and try again.")
            return

        g = self.displayaction("Getting " + fromurl)
        sz = 30000
        g = self.displayaction('... ' + str(sz) + ' (bytes - approx)')

        self.displayaction('', progressmax=sz, progressval=0)

        g = self.displayaction("Retrieving tide information for " + str(currentYear) + ' from ' + self.data.linzhost)

        self.mycurl.getfile(fromurl, tofile, sz, self.displayaction, button)

        self.displayaction('', enablebutton=True, progressval=-2)
        #self.data.statusbarclockspaused = False

    def crv_callback_moresettingsbutton(self, instance):
        self.open_settings()
        if instance is not None: instance.clickup()

    def crv_callback_crvweather(self, instance):
        self.data.sm.current = 'screen_crvweather'
        self.data.shelf_save_current()
        if instance is not None: instance.clickup()

    def crv_callback_crvoperational(self, instance):
        self.data.shelf_save_current()
        self.data.sm.current = 'screen_crvoperational'
        if instance is not None: instance.clickup()

    def crv_callback_boatlog(self, instance):
        self.data.shelf_save_current()
        if not self.data.sm.has_screen('screen_boatlog'):
            boatlog = self.crv_setup_boatlog_screen()
            self.data.sm.add_widget(boatlog)
            self.boatlog.log_grid_recover()
        self.data.sm.current = 'screen_boatlog'
        if instance is not None: instance.clickup()
        Window.softinput_mode = ''

    def crv_callback_logarchive(self, instance):
        if not self.data.sm.has_screen('screen_logarchive'):
            logarchive = self.crv_setup_logarchive()
            self.data.sm.add_widget(logarchive)
        self.data.sm.current = 'screen_logarchive'
        self.logarchive.populate()
        Window.softinput_mode = ''
        if instance is not None: instance.clickup()

    def crv_callback_click(self, instance):
        instance.clickdown()

    def crv_callback_managecrew(self, instance):
        self.setrequiredsettings()
        if not self.data.sm.has_screen('screen_managecrew'):
            manage = self.crv_setup_managecrew()
            self.data.sm.add_widget(manage)
        self.data.sm.current = 'screen_managecrew'
        self.managecrew.populatecrew()
        Window.softinput_mode = ''
        if instance is not None: instance.clickup()

    def crv_callback_managelocations(self, instance):
        self.setrequiredsettings()
        if not self.data.sm.has_screen('screen_managelocations'):
            manage = self.crv_setup_managelocations()
            self.data.sm.add_widget(manage)
        self.data.sm.current = 'screen_managelocations'
        self.managelocations.populatelocations()
        Window.softinput_mode = ''
        if instance is not None: instance.clickup()

    def crv_callback_managevessels(self, instance):
        self.setrequiredsettings()
        if not self.data.sm.has_screen('screen_managevessels'):
            vess = self.crv_setup_managevessels()
            self.data.sm.add_widget(vess)
        self.data.sm.current = 'screen_managevessels'
        self.managevessels.populatevessels()
        Window.softinput_mode = ''
        if instance is not None: instance.clickup()

    def crv_callback_crvclose(self, instance):
        # close log pressed  (we havent closed it yet though)
        self.animate(instance)

        if not self.data.sm.has_screen('screen_crvclose'):
            crvclose = self.crv_setup_closelog_screen()
            self.data.sm.add_widget(crvclose)
        self.data.sm.current = 'screen_crvclose'
        self.data.shelf_save_current()
        if instance is not None: instance.clickup()

    def crv_setup_button_text(self):
        # returns the text to be displayed on the "openlog" button
        # on the main screen.
        # also returns a true/false for recover status

        ret = False
        if self.data.shelf_check() and not self.data.getlogactive():
            newlogtitle = "Recover Unsaved Boatlog"
            ret = True
        else:
            oper = self.data.datarecord.getobjecttext('homeoperational')
            if oper == 'Continue':
                self.data.setlogactive(True)
            if self.data.getlogactive():
                newlogtitle = "View Boatlog "
            else:
                newlogtitle = "Open Boatlog"
        w = self.data.datarecord.getobject('butactivity')
        if w:
            w.setcolors()
        w = self.data.datarecord.getobject('closing')
        if w:
            w.setcolors()

        return newlogtitle, ret

    #####################################################################
    # define the main screen
    #
    def crv_setup_main_screen(self):
        if self.data.sm.has_screen('screen_main'):
            return self.screen_main

        crvcp = CrvProfile(Logger, 'crv_setup_main_screen')

        # this is returned
        screen_main = Screen(name='screen_main')

        boxmain = BoxLayout(orientation='vertical', padding=10)

        #header = self.logstart(3, 'screen_main')  # showtime or logtime
        header = self.screencreateheader('screen_main')

        middle = BoxLayout(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint=[1, .1])

        boxrow1 = BoxLayout(orientation='horizontal', size_hint=[1, .1], padding=10)
        boxrow2 = BoxLayout(orientation='horizontal', size_hint=[1, .1], padding=10)
        boxrow3 = BoxLayout(orientation='horizontal', size_hint=[1, .1], padding=10)

        middle.add_widget(boxrow1)
        middle.add_widget(boxrow2)
        middle.add_widget(boxrow3)


        #
        # Look at the settings. If vesselname and tidestation are not set then prompt for
        # them in a temproary screen.
        #

        newlogtitle, dumbool = self.crv_setup_button_text()

        bnewlog = CustomButton(wid="newlog", image=self.data.getimagepath("newlog.png"), title=newlogtitle,
                               label=newlogtitle)
        self.data.datarecord.setobject('newlog', bnewlog, 'button')
        bnewlog.bind(on_press=self.crv_callback_click)
        bnewlog.bind(on_release=self.crv_callback_newlog)

        bclosing = CustomButton(wid="End Log", image=self.data.getimagepath("closing.png"), title="End Log",
                                label="End Log")
        bclosing.bind(on_press=self.crv_callback_click)
        bclosing.bind(on_release=self.crv_callback_crvclose)
        bclosing.disabled = True
        bclosing.color = self.crvcolor.getfgcolor()
        self.data.datarecord.setobject('closing', bclosing, 'button')

        bboatlog = CustomButton(wid="Activity Log", image=self.data.getimagepath('activity.png'),
                                    title="Activity Log", label="Activity Log")
        self.data.datarecord.setobject('butactivity', bboatlog, 'button')
        bboatlog.bind(on_press=self.crv_callback_click)
        bboatlog.bind(on_release=self.crv_callback_boatlog)
        bboatlog.disabled = True
        bboatlog.color = self.crvcolor.getfgcolor()

        bsettings = CustomButton(wid="Settings", image=self.data.getimagepath("settings.png"),
                                 title="Settings", label="Settings")
        bsettings.bind(on_press=self.crv_callback_click)
        bsettings.bind(on_release=self.crv_callback_settings)

        barchive = CustomButton(wid="Log Archive", image=self.data.getimagepath("archive.png"), title="Log Archive",
                                  label="Log Archive")
        self.data.datarecord.setobject('logarchive', barchive, 'button')
        barchive.disabled = False
        barchive.bind(on_press=self.crv_callback_click)
        barchive.bind(on_release=self.crv_callback_logarchive)

        boxrow1.add_widget(bnewlog)
        boxrow1.add_widget(bclosing)

        boxrow2.add_widget(bboatlog)

        boxrow3.add_widget(barchive)
        boxrow3.add_widget(bsettings)


        # Add a status bar - just help mainly
        # Maybe later we'll split it to add, e.g. gps

        statuslabel = MyLabel(color=self.crvcolor.getfgcolor(), font_size=modglobal.default_medium_font_size)
        self.data.datarecord.setobject('mainstatus', statuslabel, 'text')
        footer.add_widget(statuslabel)

        boxmain.add_widget(header)
        boxmain.add_widget(middle)
        boxmain.add_widget(footer)

        screen_main.add_widget(boxmain)
        screen_main.bind(on_enter=self.screenmanager_callback_onenter)

        crvcp.eprof()

        return screen_main

    def crv_setup_weather_screen(self):
        Logger.info('CRV:SETUP:weather')
        crvcp = CrvProfile(Logger, 'crv_setup_weather_screen')

        screen_crvweather = Screen(name='screen_crvweather')

        box = BoxLayout(orientation='vertical', padding=10)

        header = self.screencreateheader('screen_crvweather')

        middle = BoxLayout(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint=[1, .1])

        weather = self.weatherbox()
        tide = self.tidebox()

        middle.add_widget(weather)
        middle.add_widget(tide)

        button1 = MyButton(text='Next')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.crv_callback_crvoperational)

        bsettings = MyButton(text='Settings')
        bsettings.bind(on_press=self.crv_callback_click)
        bsettings.bind(on_release=self.crv_callback_settings)

        button2 = MyButton(text='Cancel')
        button2.bind(on_press=self.crv_callback_click)
        button2.bind(on_release=self.crv_callback_cancel)
        self.data.datarecord.setobject('weathercancel', button2, 'button')

        footer.add_widget(button1)
        footer.add_widget(bsettings)
        footer.add_widget(button2)

        box.add_widget(header) # .1
        box.add_widget(middle) # .8
        box.add_widget(footer) # .1

        screen_crvweather.add_widget(box)
        screen_crvweather.bind(on_enter=self.screenmanager_callback_onenter)

        crvcp.eprof()
        return screen_crvweather

    def weatherbox(self, top_szh=None):
        #crvcp = CrvProfile(Logger, 'weatherbox')

        if not top_szh:
            top_szh = [1, 1]
        b = BoxLayout(orientation='vertical')
        btop = BoxLayout(orientation='horizontal')
        b.add_widget(btop)

        bleft = BoxLayout(orientation='vertical')
        bright = BoxLayout(orientation='vertical')
        btop.add_widget(bleft)
        btop.add_widget(bright)

        # === following are all widget at top left
        # These options mist match the log selection records in data
        # (commented as "the different types of logs")

        """ set wind dropdown """
        wwind, xwind, lwind = self.boxdropdown('Wind', ['Calm', 'Light (10)', 'Moderate (15)', 'Fresh (20)', 'Strong (25)',
                                             'Near Gale (30)', 'Gale (38)', 'Strong Gale (45)', 'Storm (50+)'], top_szh, readonly=True)
        #xwind.readonly = True
        self.data.datarecord.setobjectplus('wind', wwind, xwind, bleft, 'drop')

        """ set seastate dropdown """
        wseastate, xseastate, lseastate = self.boxdropdown('Sea State',
                                        ['Calm', 'Smooth', 'Slight', 'Moderate', 'Rough', 'Very Rough', 'High',
                                         'Very High'], top_szh, readonly=True)
        #xseastate.readonly = True
        self.data.datarecord.setobjectplus('seastate', wseastate, xseastate, bleft, 'drop')

        """ set winddirection dropdown """
        wwinddirection, xwinddirection, lwinddirection = self.boxdropdown('Wind Direction',
                                             ['Variable', 'North', 'NorthEast', 'East', 'SouthEast', 'Southerly',
                                              'SouthWest', 'West', 'NorthWest'], top_szh, readonly=True)
        self.data.datarecord.setobjectplus('winddirection', wwinddirection, xwinddirection, bleft, 'drop')

        """ set visibility dropdown """
        wvisibility, xvisibility, lvisibility = self.boxdropdown('Visibility', ['Clear', 'Squalls', 'Rain', 'Haze', 'Fog'],
                                                                 top_szh, readonly=True)
        #xvisibility.readonly = True
        self.data.datarecord.setobjectplus('visibility', wvisibility, xvisibility, bleft, 'drop')

        """ set cloud cover dropdown """
        wcloudcover, xcloudcover, lcloudcover = self.boxdropdown('Cloud Cover', ['Nil', 'Slightly Cloudy', 'Mostly Cloudy', 'Overcast'],
                                                                 top_szh, readonly=True)
        #xcloudcover.readonly = True
        self.data.datarecord.setobjectplus('cloudcover', wcloudcover, xcloudcover, bleft, 'drop')

        # === following are all widget at top right

        disptypes=[]

        for n in self.data.logrecord.loggroup['logtypesinitreason']:
            disptypes.append(n)
        disptypes.sort()

        wtype, x, l = self.boxdropdown('Initial Reason\nFor Launch', disptypes, [.5, 1], readonly=True)
        #x.readonly = True
        self.data.datarecord.setobjectplus('initialreason', wtype, x, bright, 'drop')
        self.data.datarecord.setlabobject('initialreason', l)
        x.postcall = self.crv_callback_checkoperationalstatus

        bchecklists = BoxLayout(orientation='horizontal')
        bright.add_widget(bchecklists)

        # button for "Pre launch checklist and defects noted"
        buttonplc = MyButton(text='Pre Launch\nChecklist')
        buttonplc.bind(on_press=self.crv_callback_click)
        buttonplc.bind(on_release=self.crv_callback_plcheck)
        # button for "Tractor launch checklist and defects noted"
        buttonptc = MyButton(text='Tractor Launch\nChecklist')
        buttonptc.bind(on_press=self.crv_callback_click)
        buttonptc.bind(on_release=self.crv_callback_ptcheck)

        bchecklists.add_widget(buttonplc)
        bchecklists.add_widget(buttonptc)

        x, c, l = self.boxcheckbox('Prelaunch Checks\nComplete', [1.3, 1])
        self.data.datarecord.setobjectlist('prelaunch', x, [c, l], bright, 'checkbox')
        c.bind(active=self.crv_callback_checkoperationalstatus)

        bfuel = BoxLayout(orientation='horizontal')
        bright.add_widget(bfuel)
        w, x, l = self.boxtextbox('Fuel Start\n(CRV)', top_szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        self.data.datarecord.setobjectplus('fuelstart', w, x, bfuel, 'text')

        w, x, l = self.boxtextbox('Fuel Start\n(non CRV)', top_szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        self.data.datarecord.setobjectplus('fuelsuppliedstart', w, x, bfuel, 'text')

        brightlab = BoxLayout(orientation='horizontal')
        bright.add_widget(brightlab)

        brighteh = BoxLayout(orientation='horizontal')  # layout to hold enginehours in operational screen
        brighteh.id = ''  # this is set in event to signify it's been handled
        brightehp = BoxLayout(orientation='horizontal')  # layout to hold port enginehours in operational screen
        brightehsb = BoxLayout(orientation='horizontal')  # layout to hold starboard enginehours in operational screen

        w, c, l = self.boxtextbox('Port', orientation='vertical', nolabel=True, szh=top_szh, infilter='float')
        c.bind(focus=self.portcallbackfocus)
        brightehp.add_widget(w)
        self.data.datarecord.setobject('portehoursstart', c, 'text')

        w, c, l = self.boxtextbox('Starboard', orientation='vertical', nolabel=True, szh=top_szh, infilter='float')
        c.bind(focus=self.portcallbackfocus)
        brightehsb.add_widget(w)
        self.data.datarecord.setobject('sbehoursstart', c, 'text')

        bright.add_widget(brighteh)
        # we will determine what type of engine to start later - but it will be created in this layout
        self.data.datarecord.setobject('enginehourslabel', brightlab, 'layout')
        self.data.datarecord.setobject('enginehoursstart', brighteh, 'layout')
        self.data.datarecord.setobject('enginehoursstartp', brightehp, 'layout')
        self.data.datarecord.setobject('enginehoursstartsb', brightehsb, 'layout')

        #crvcp.eprof()

        return b

    def tidebox(self, top_szh=None):

        crvcp = CrvProfile(Logger, 'tidebox')
        if not top_szh:
            top_szh = [1, 1]
        b = MyBoundBox(orientation='vertical', size_hint_y=.4)   # this is returned

        btitle = MyBoundBox(orientation='horizontal', size_hint_y=.2)   # tide title line
        tidetitle = MyLabel(text='[b]' + 'Tides' + '[/b]', color=self.crvcolor.getfgcolor(), halign='left', markup=True)

        btitle.add_widget(tidetitle)
        self.data.datarecord.setobject('tidetitle', tidetitle, 'label')

        btideinfo = BoxLayout(orientation='horizontal')

        bgraphbox = BoxLayout(orientation='horizontal', size_hint=top_szh)
        bgraph = self.tidegraph()
        bgraphbox.add_widget(bgraph)

        btides = MyBoundBox(orientation='vertical')

        bhigh = MyBoundBox(orientation='horizontal')

        # i,x = layout widget, actual widget
        i, x = self.boxtimebox('Next High', top_szh)
        x.bind(focus=self.tidehightimecallbackfocus)
        self.data.datarecord.setobjectplus('tidehightime', i, x, bhigh, 'text')

        i, x, boxlab = self.boxtextbox('Height', top_szh, infilter='float')
        x.bind(focus=self.tidehighheightcallbackfocus)
        self.data.datarecord.setobjectplus('tidehighheight', i, x, bhigh, 'text')

        blow = MyBoundBox(orientation='horizontal')

        i, x = self.boxtimebox('Next Low', top_szh)
        x.bind(focus=self.tidelowtimecallbackfocus)
        self.data.datarecord.setobjectplus('tidelowtime', i, x, blow, 'text')

        i, x, boxlab = self.boxtextbox('Height', top_szh, infilter='float')
        x.bind(focus=self.tidelowheightcallbackfocus)
        self.data.datarecord.setobjectplus('tidelowheight', i, x, blow, 'text')

#        btides.add_widget(self.boxpad(.1))
        btides.add_widget(bhigh)
        btides.add_widget(blow)

        btideinfo.add_widget(bgraphbox)
        btideinfo.add_widget(btides)

        b.add_widget(btitle)
        b.add_widget(btideinfo)

        crvcp.eprof()
        return b

    def crv_set_screen(self, reqscreen):
        self.data.sm.current = reqscreen

    def crv_setup_operational_screen(self):
        Logger.info('CRV:SETUP:operational')
        screen_crvoperational = Screen(name='screen_crvoperational')

        # skipper... input.... imsafe
        # crew   ... input.... imsafe

        self.crew.setup()

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        #header = self.logstart(1, 'screen_crvoperational')  # 1=showtime
        header = self.screencreateheader('screen_crvoperational')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        # A skipper is a name and an imsafe
        # It's stored in the data record as a list

        skipper = MyBoundBox(orientation='horizontal', size_hint_y=.2)
        middle.add_widget(skipper)

        skipperl = BoxLayout(orientation='horizontal', size_hint_x=.6)
        skipperr = BoxLayout(orientation='horizontal', size_hint_x=.4)
        skipper.add_widget(skipperl)
        skipper.add_widget(skipperr)

        s1, x, l = self.boxdropdown('Skipper\nName/ID', self.crew.possskipperlist, szh)
        s2, x1, l1 = self.boxcheckbox('IMSAFE', [1, 1])
        self.data.datarecord.setskipper(x, x1)
        skipperl.add_widget(s1)
        skipperl.add_widget(s2)

        addcrew = MyBoundBox(orientation='horizontal', size_hint_y=.2)
        middle.add_widget(addcrew)

        addcrewl = BoxLayout(orientation='horizontal', size_hint_x=.6)
        addcrewr = BoxLayout(orientation='horizontal', size_hint_x=.4)
        addcrew.add_widget(addcrewl)
        addcrew.add_widget(addcrewr)

        c00 = MyBoundBox(orientation='horizontal')
        addcrewl.add_widget(c00)

        c1, x, l = self.boxdropdown('Crew\nName/ID', self.crew.posscrewlist, szh)
        self.crew.setobjectplus('name', c1, x, c00)
        c2, x1, l = self.boxcheckbox('IMSAFE', [1, 1])
        self.crew.setobjectplus('IMSAFE', c2, x1, c00)

        #c01 = MyBoundBox(orientation='horizontal')
        button1 = MyButton(text='Add/Save Crew')
        self.data.datarecord.setobject('addsavecrew', button1, 'button')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.crv_callback_addsavecrew)
        button2 = MyButton(text='Clear')
        button2.bind(on_press=self.crv_callback_click)
        button2.bind(on_release=self.crew.crew_callback_cancel)
        addcrewr.add_widget(button1)
        addcrewr.add_widget(button2)

        #addcrew.add_widget(c01)

        cr = self.crew.crv_add_crew(button1.width)
        middle.add_widget(cr)

        sops = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)
        x, c, l = self.boxcheckbox('Crew meets\nregional SOPS', [1, 1])
        self.data.datarecord.setobjectlist('crewmeetsops', x, [c, l], sops, 'checkbox')
        c.bind(active=self.crv_callback_checkoperationalstatus)

        x, c, l = self.boxcheckbox('Vessel Operational', [1, 1])
        self.data.datarecord.setobjectlist('vesseloperational', x, [c, l], sops, 'checkbox')
        c.bind(active=self.crv_callback_checkoperationalstatus)

        sendcrew = BoxLayout(orientation='horizontal')
        crewlabel = BoxLayout(orientation='horizontal')
        crewbuttons = BoxLayout(orientation='horizontal')

        screw = MyBoundBox(orientation='horizontal', pos_hint_x=0, size_hint_y=.2)

        buttonsendnow = MyButton(text='Send Crew List')
        buttonsendnow.bind(on_press=self.crv_callback_click)
        buttonsendnow.bind(on_release=self.crv_callback_sendcrewlist)
        self.data.datarecord.setobject('crewlistsendbut', buttonsendnow, 'button')
        buttonsendnow.disabled = True
        crewbuttons.add_widget(buttonsendnow)

        x, c, l = self.boxcheckbox('Crew List Sent', [1, 1])
        self.data.datarecord.setobjectlist('crewlistsendcheck', x, [c, l], crewbuttons, 'checkbox')
        c.bind(active=self.crv_callback_checkoperationalstatus)
        c.disabled = True
        self.data.datarecord.setobjectvariable('crewlistsent', 'bool', False)

        sendcrew.add_widget(crewbuttons)
        screw.add_widget(sendcrew)

        middle.add_widget(sops)
        middle.add_widget(screw)

        buttonop = MyButton(text='Open Log')
        buttonop.bind(on_press=self.crv_callback_click)
        buttonop.bind(on_release=self.crv_callback_openthelog)
        self.data.datarecord.setobject('homeoperational', buttonop, 'button')
        buttonop.disabled = True

        button2 = MyButton(text='Previous')
        button2.bind(on_press=self.crv_callback_click)
        button2.bind(on_release=self.crv_callback_crvweather)

        bsettings = MyButton(text='Settings')
        bsettings.bind(on_press=self.crv_callback_click)
        bsettings.bind(on_release=self.crv_callback_settings)

        button3 = MyButton(text='Cancel')
        button3.bind(on_press=self.crv_callback_click)
        button3.bind(on_release=self.crv_callback_cancel)

        footer.add_widget(buttonop)
        footer.add_widget(button2)
        footer.add_widget(bsettings)
        footer.add_widget(button3)

        box.add_widget(header)  # .1
        box.add_widget(middle)  # .8
        box.add_widget(footer)  # .1

        screen_crvoperational.add_widget(box)
        screen_crvoperational.bind(on_enter=self.screenmanager_callback_onenter)
        return screen_crvoperational

    def act_callback_timefocus(self, instance, value):
        if len(instance.text) == 0:
            instance.text = self.data.getnow()

    def crv_callback_closingtimefocus(self, instance, value):
        if len(instance.text) == 0:
            instance.text = self.data.getnow()
        self.data.shelf_save_current()

    def crv_callback_logfueltype(self, instance, *args):
        # set cost based on fuel type
        if instance in ['Diesel', 'Petrol']:
            vesselfuel = self.data.currvessel[self.data.datarecord.managevesselfueltype]
            cost = self.data.logrecord.getobjecttext('logfuelprice')
            if cost == '':
                if instance == vesselfuel:
                    # if logfuelprice is empty then set it from the 'fuelcost' in boatlog
                    cost = self.data.datarecord.getobjecttext('fuelcost')
                else:
                    cost = self.data.datarecord.getobjecttext('fuelsuppliedcost')
                self.data.logrecord.setobjecttext('logfuelprice', cost)
        return True

    def crv_callback_checkoperationalstatus(self, instance, *args):
        if self.data.openingLog:
            return True

        if instance is not None:
            # if called from add/save crew then add crew before continuing
            if hasattr(instance, 'id'):
                if instance.id is not None:
                    if instance.id == 'addsavecrew':
                        self.crew.crew_callback_save(instance)

        self.screenupdateheader(self.data.sm.current)

        # Determine and create what is displayed in widget enginehoursstart
        w = self.data.datarecord.getobject('enginehoursstart')
        if w.id != '': # we only need to do this once
            w.id = ''
            # Engine type can be, 'Outboard', 'Twin outboard', 'Jet', 'Twin jet'
            if self.data.currvessel is None:
                self.data.crv_populate_vessel()
            vesselengine = self.data.currvessel[self.data.datarecord.managevesselenginetype]
            vlabel = self.data.datarecord.getobject('enginehourslabel')
            wport = self.data.datarecord.getobject('enginehoursstartp')
            w.add_widget(wport)
            if vesselengine[0:4] == 'Twin':
                wstarboard = self.data.datarecord.getobject('enginehoursstartsb')
                w.add_widget(wstarboard)
                vlabel.add_widget(MyLabel(text='Port', valign='middle'))
                vlabel.add_widget(MyLabel(text='[b]Engine Hours[/b]', valign='middle', markup=True))
                vlabel.add_widget(MyLabel(text='Starboard', valign='middle'))
            else:
                vlabel.add_widget(MyLabel(text='Engine Hours', valign='middle'))

        if self.data.getlogactive():
            w = self.data.datarecord.getobject('homeoperational')
            if w is not None:
                w.disabled = False
                w.text = 'Continue'
            w = self.data.datarecord.getobject('crewlistsendbut')
            if w is not None:
                if len(self.data.datarecord.getskippername()) > 0 and len(self.data.getallcrew()) > 1:
                    w.disabled = False
                else:
                    w.disabled = True

        else:
            if self.data.openingLog:
            #if not self.data.haveopenedlog:
                # not available.. if instance is not None: instance.clickup()
                return True

            Logger.info("CRV:crv_callback_checkoperationalstatus")

            # if self.data.openingLog:
            #     Logger.info("CRV:crv_callback_checkoperationalstatus: refusing during initialisation")
            #     return

            # non operational stuff - fill out tides if available.
            if self.data.datarecord.getobject('tidehightime').text == '':
                self.data.datarecord.getobject('tidehightime').text = str(self.data.tides.nexthigh[0])
                if self.data.tides.nexthigh[0] > 0: self.data.datarecord.getobject('tidehightime').disabled = True
            if self.data.datarecord.getobject('tidehighheight').text == '':
                self.data.datarecord.getobject('tidehighheight').text = str(self.data.tides.nexthigh[1])
                if self.data.tides.nexthigh[1] > 0: self.data.datarecord.getobject('tidehighheight').disabled = True
            if self.data.datarecord.getobject('tidelowtime').text == '':
                self.data.datarecord.getobject('tidelowtime').text = str(self.data.tides.nextlow[0])
                if self.data.tides.nextlow[0] > 0: self.data.datarecord.getobject('tidelowtime').disabled = True
            if self.data.datarecord.getobject('tidelowheight').text == '':
                self.data.datarecord.getobject('tidelowheight').text = str(self.data.tides.nextlow[1])
                if self.data.tides.nextlow[1] > 0: self.data.datarecord.getobject('tidelowheight').disabled = True

            #
            # Before allowing the vessel to be operational, we have to check:
            # Prelaunch checks complete
            # Crew has skipper and crew within limits and all safe
            #
            ok = True  # assume ok
            if self.data.datarecord.getobjectcheckastext('prelaunch') == 'false':
                ok = False
                colr = self.crvcolor.getboldcolor()
            else:
                colr = self.crvcolor.getfgcolor()
            self.data.datarecord.setobjectcolor('prelaunch', colr)

            ok = True  # assume ok
            if self.data.datarecord.getobjecttext('initialreason') == '':
                ok = False
                colr = self.crvcolor.getboldcolor()
            else:
                colr = self.crvcolor.getfgcolor()
            self.data.datarecord.setlabobjectcolor('initialreason', colr)

            # They didnt want this to stop log open
            # if self.data.datarecord.getobjectcheckastext('vesseloperational') == 'false':
            #     ok = False
            #     colr = self.crvcolor.getboldcolor()
            # else:
            #     colr = self.crvcolor.getfgcolor()
            # self.data.datarecord.setobjectcolor('vesseloperational', colr)

            if self.data.datarecord.getobjectcheckastext('crewmeetsops') == 'false':
                ok = False
                colr = self.crvcolor.getboldcolor()
            else:
                colr = self.crvcolor.getfgcolor()
            self.data.datarecord.setobjectcolor('crewmeetsops', colr)

            # I dont think not sending crew list should affect operational status.
            # Just advisory.
            if not self.data.datarecord.getobjectvariable('crewlistsent', 'bool', False):
                #ok = False
                colr = self.crvcolor.getboldcolor()
                self.data.datarecord.setobjectcheck('crewlistsendcheck', False)
            else:
                colr = self.crvcolor.getfgcolor()
                self.data.datarecord.setobjectcheck('crewlistsendcheck', True)
            #self.data.datarecord.setobjectcolor('crewlistsentlabel', colr)
            self.data.datarecord.setobjectcolor('crewlistsendcheck', colr)

            # check the skipper, tractor and crew - enable send if we have
            # skipper and crew (we dont necessarily need a tractor driver to send
            # a crew list.

            w = self.data.datarecord.getobject('crewlistsendbut')
            if w is not None:
                if len(self.data.datarecord.getskippername()) > 0 and len(self.data.getallcrew()) > 1:
                    w.disabled = False
                else:
                    w.disabled = True

            # If everything ok, then enable Home/Open Log button
            w = self.data.datarecord.getobject('homeoperational')
            if w is not None:
                if ok:
                    w.disabled = False
                    # self.data.setlogactive(True)
                else:
                    w.disabled = True
                    # self.data.setlogactive(False)
            if instance is not None:
                self.data.shelf_save_current()

        return True

    def crv_callback_checkboatlogstatus(self, instance, invalue):
        self.screenupdateheader('screen_boatlog')

        w = self.data.logrecord.getobject('logtype')
        if w is not None:
            #thislog = self.data.logrecord.getobjecttext('logtype')
            thislog = w.text
            self.changelogbytype(thislog)
            self.boatlog.setdefaultsbytype(thislog)

        thiscrew = self.data.getcrewname()  # gets list of current crew
        thiscrew.append(self.data.datarecord.getskippername())
        l = len(thiscrew)
        if l > 0:
            if len(thiscrew[0]) > 0:
                for l in [ 'loghelm', 'lognav']:
                    d = self.data.logrecord.getobject(l)
                    d.setdropdefaults(thiscrew)
                    d.setdropoptions(thiscrew)
        return True

    def crv_callback_checksettingsstatus(self, instance, invalue):
        self.screenupdateheader('screen_settings2')

        # if there is only 1 vessel defined, then use that.
        v = self.managevessels.getvesslist()
        if len(v) == 1:
            self.data.datarecord.getobject('reqvessname').text = v[0]
        elif len(v) < 1:
            self.crv_callback_managevessels(None)
        return True

    def crv_callback_checkreccheck(self, instance, value=None):
            # check if recsigned is set and if so, enable the signature widget
            sig = self.data.datarecord.getobject('recsignature')

            w = self.data.datarecord.getobject('recsigned')
            if len(w.text) == 0:
                sig.disabled = True
            else:
                sig.disabled = False
                afile = os.path.join(self.data.datadir, w.text)
                sig.setfile(afile)

            if instance is not None:
                if instance.id == 'savesignature':
                    if sig.savesignature():
                        afile = sig.getfile()
                        self.data.datarecord.setvalue('recsignature', afile)

    def crv_callback_checkcloselogstatus(self, instance, value):
        if self.data.openingLog:
            return

        self.screenupdateheader('screen_crvclose')

        # if using a single engine vessel, then disable startboard side of screen and
        # change label.
        if instance is None: # from screenmanager
            if self.data.currvessel is None:
                self.data.crv_populate_vessel()

        # if self.data.currvessel is not None:
        #     if self.data.currvessel[7] == 'Jet' or self.data.currvessel[7] == 'Outboard':
        #         w = self.data.datarecord.getobject('closingsbside')
        #         w.disabled = True
        #
        #         w = self.data.datarecord.getobject('closingportsidelabel')
        #         w.text = 'Single ' + self.data.currvessel[7]
        #

        # Determine and create what is displayed in widget enginehoursstart
        w = self.data.datarecord.getobject('enginehoursclose')
        if w.id != '': # we only need to do this once
            w.id = ''
            # Engine type can be, 'Outboard', 'Twin outboard', 'Jet', 'Twin jet'
            if self.data.currvessel is None:
                self.data.crv_populate_vessel()
            vesselengine = self.data.currvessel[self.data.datarecord.managevesselenginetype]
            vlabel = self.data.datarecord.getobject('closelablayout')
            wfin = self.data.datarecord.getobject('enginehoursclosefin') # row2
            wfinp = self.data.datarecord.getobject('enginehoursclosefinp')
            wdur = self.data.datarecord.getobject('enginehoursclosedur') # row3
            wdurp = self.data.datarecord.getobject('enginehoursclosedurp') # row3
            wfin.add_widget(wfinp)
            wdur.add_widget(wdurp)
            if vesselengine[0:4] == 'Twin':
                wfinsb = self.data.datarecord.getobject('enginehoursclosefinsb')
                wdursb = self.data.datarecord.getobject('enginehoursclosedursb')
                wfin.add_widget(wfinsb)
                wdur.add_widget(wdursb)
                vlabel.add_widget(MyLabel(text='Port')) #, valign='middle'))
                vlabel.add_widget(MyLabel(text='[b]Engine Hours[/b]', markup=True)) # valign='middle', markup=True))
                vlabel.add_widget(MyLabel(text='Starboard')) # , valign='middle'))
            else:
                vlabel.add_widget(MyLabel(text='Engine Hours')) #, valign='middle'))


        #
        # Before allowing the log to close
        # Prelaunch checks complete
        # Crew has skipper and crew within limits and all safe
        #
        self.fuelcallbackfocus(instance, True)
        self.portcallbackfocus(instance, True)
        self.sbcallbackfocus(instance, True)

        ok = True  # assume ok
        if self.data.datarecord.getobjectcheckastext('closingchecks') == 'false':
            ok = False
            colr = self.crvcolor.getboldcolor()
        else:
            if self.data.getlogactive():
                # if closingtime not set then incpopulate it now (call it anyway - it checks
                self.crv_callback_closingtimefocus(self.data.datarecord.getobject('closingtime'), None)
            colr = self.crvcolor.getfgcolor()

        self.data.datarecord.setobjectcolor('closingchecks', colr)

        # If everything ok, then enable Home button
        w = self.data.datarecord.getobject('closelogbutton')
        if w is not None:
            if ok:
                w.disabled = False
            else:
                w.disabled = True
                # self.data.setlogactive(True)

    def crv_callback_checkrequiredsettings(self, instance, value):
        ok = True  # assume ok

        # if vesselname has changed, then instance.id will be reqvessname
        if instance is not None:
            if instance.id == 'reqvessname':
                # we want to save the vessel name details - but first we
                # need to determine them.
                rec = 0

                self.data.crv_populate_vessel(value)

        v = self.data.datarecord.getobjecttext('reqvessname')
        if v == '':
            ok = False
            colr = self.crvcolor.getboldcolor()
        else:
            colr = self.crvcolor.getfgcolor()
            # So a vessel has been selected from the allowed vessels dropdown.
            # We have to find out which one.

        self.data.datarecord.setobjectcolor('labvessname', colr)

        b = self.data.datarecord.getobject('requpdtidesbutton')
        v = self.data.datarecord.getobjecttext('reqtidestation')
        if v == '':
            ok = False
            b.disabled = True
            colr = self.crvcolor.getboldcolor()
        else:
            b.disabled = False
            colr = self.crvcolor.getfgcolor()
            self.data.settidestation(v)
        self.data.datarecord.setobjectcolor('labtidestation', colr)

        v = self.data.datarecord.getobjecttext('reqemaillog')
        if v == '':
            ok = False
            colr = self.crvcolor.getboldcolor()
        else:
            colr = self.crvcolor.getfgcolor()

        self.data.datarecord.setobjectcolor('labemaillog', colr)

        # set the Home button depending on required data
        b = self.data.datarecord.getobject('reqhomebutton')
        b.disabled = not ok

        # set the Process crews and tides button is both
        # reqvessname and reqtidestation are set
        b = self.data.datarecord.getobject('reqmanagecrewbutton')
        b.disabled = not ok

        return True


    def crv_setup_logarchive(self):
        Logger.info('CRV:SETUP:archive')
        """
        Screen definition and setup for logarchive
        :return:
        """
        screen_logarchive = Screen(name='screen_logarchive')

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        #header = self.logstart(3, 'screen_logarchive')
        header = self.screencreateheader('screen_logarchive')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        b = MyBoundBox(orientation='vertical', size_hint_y=.1)
        b.add_widget(MyLabel(text='You cannot delete active log or any log not marked as sent', size_hint_y=.1))

        wdth = box.width
        scrollarchive = self.logarchive.scrollwidget(wdth)

        b.add_widget(scrollarchive)
        middle.add_widget(b)

        button1 = MyButton(text='Home')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.crv_callback_home)

        button2 = MyButton(text='Send Unsent Logs')
        button2.bind(on_press=self.crv_callback_click)
        button2.bind(on_release=self.crv_send_logs)

        button3 = MyButton(text='Audit Log')
        button3.bind(on_press=self.crv_callback_click)
        button3.bind(on_release=self.crv_callback_logaudit)

        footer.add_widget(button1)
        footer.add_widget(button2)
        footer.add_widget(button3)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_logarchive.add_widget(box)
        return screen_logarchive

    def crv_setup_logaudit(self):
        Logger.info('CRV:SETUP:incident audit')
        """
        Screen definition and setup for the audit trail
        :return:
        """
        screen_logaudit = Screen(name='screen_logaudit')

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        #header = self.logstart(3, 'screen_logaudit')
        header = self.screencreateheader('screen_logaudit')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        wdth = box.width
        scrollaudit = self.logaudit.scrollwidget(wdth)

        middle.add_widget(scrollaudit)

        button1 = MyButton(text='Back')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.audit_callback_back)

        footer.add_widget(button1)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_logaudit.add_widget(box)
        return screen_logaudit

    def crv_setup_managelocations(self):
        Logger.info('CRV:SETUP:manage locations')
        """
        Screen definition and setup for manage locations

        uses the managelocations instance of CrvManagelocations for all it's callbacks
        """

        screen_managelocations = Screen(name='screen_managelocations')

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        # header = self.logstart(3, 'screen_managelocations')
        header = self.screencreateheader('screen_managelocations')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        wdth = box.width
        scrollarchive = self.managelocations.scrollwidget(wdth)

        middle.add_widget(scrollarchive)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        button1 = MyButton(text='Back')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.location_callback_back)

        footer.add_widget(button1)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_managelocations.add_widget(box)

        return screen_managelocations

    def crv_setup_managevessels(self):
        Logger.info('CRV:SETUP:manage vessels')
        screen_managevessels = Screen(name='screen_managevessels')

        box = BoxLayout(orientation='vertical', padding=10)

        header = self.screencreateheader('screen_managevessels')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        c00 = MyBoundBox(orientation='vertical', size_hint_y=.4)

        c01 = MyBoundBox(orientation='vertical')
        c0top = MyBoundBox(orientation='horizontal')
        c0bot = MyBoundBox(orientation='horizontal')

        c01.add_widget(c0top)
        c01.add_widget(c0bot)

        szh = [.5, 1]
        w, x, l = self.boxtextbox('Name', szh)
        self.data.datarecord.setobjectplus('managevesselname', w, x, c0top, 'text')

        w, x, l = self.boxtextbox('Callsign', szh)
        self.data.datarecord.setobjectplus('managevesselcallsign', w, x, c0top, 'text')

        w, x, l = self.boxtextbox('Fuelrate', szh)
        self.data.datarecord.setobjectplus('managevesselfuelrate', w, x, c0top, 'text')

        wtyp, xtyp, ltyp = self.boxdropdown('Fuel', ['Diesel', 'Petrol'], szh, readonly=True)
        #xtyp.readonly = True
        self.data.datarecord.setobjectplus('managevesselfueltype', wtyp, xtyp, c0top, 'drop')

        w, x, l = self.boxcheckbox('Enabled', szh)
        self.data.datarecord.setobjectlist('managevesselhide', w, [x,l], c0bot, 'checkbox')

        w, x, l = self.boxtextbox('Phone', szh)
        self.data.datarecord.setobjectplus('managevesselphone', w, x, c0bot, 'text')

        w, x, l = self.boxtextbox('MSANum', szh)
        self.data.datarecord.setobjectplus('managevesselmsanum', w, x, c0bot, 'text')

        weng, xeng, leng = self.boxdropdown('Engine', self.data.logrecord.loggroup['enginetypes'], szh, readonly=True)
        #xeng.readonly = True
        self.data.datarecord.setobjectplus('managevesselengine', weng, xeng, c0bot, 'drop')

        c02 = MyBoundBox(orientation='horizontal')
        buttonadd = MyButton(text='Add')
        buttonadd.bind(on_press=self.crv_callback_click)
        buttonadd.bind(on_release=self.managevessels.callback_savevessel)
        c02.add_widget(buttonadd)

        c00.add_widget(c01)
        c00.add_widget(c02)

        middle.add_widget(c00)

        wdth = box.width
        scrollarchive = self.managevessels.scrollwidget(wdth)

        middle.add_widget(scrollarchive)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        button1 = MyButton(text='Back')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.vessel_callback_back)

        footer.add_widget(button1)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_managevessels.add_widget(box)

        return screen_managevessels

    def crv_setup_managecrew(self):
        Logger.info('CRV:SETUP:manage crew')
        """
        Screen definition and setup for manage crew

        uses the managecrew instance of CrvManagecrew for all it's callbacks
        """

        screen_managecrew = Screen(name='screen_managecrew')

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        #header = self.logstart(3, 'screen_managecrew')
        header = self.screencreateheader('screen_managecrew')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        c00 = MyBoundBox(orientation='vertical', size_hint_y=.4)

        c01 = MyBoundBox(orientation='horizontal')
        c0left = MyBoundBox(orientation='horizontal')
        c0right = MyBoundBox(orientation='horizontal')

        c01.add_widget(c0left)
        c01.add_widget(c0right)

        w, x, l = self.boxtextbox('First Name', [.5, 1])
        self.data.datarecord.setobjectplus('managecrewfirstname', w, x, c0left, 'text')

        w, x, l = self.boxtextbox('Last Name', [.5, 1])
        self.data.datarecord.setobjectplus('managecrewlastname', w, x, c0left, 'text')

        w, x, l = self.boxcheckbox('Skipper', [.5, 1])
        self.data.datarecord.setobjectlist('managecrewtype', w, [x, l], c0right, 'checkbox')

        w, x, l = self.boxtextbox('ID', [.5, 1])
        self.data.datarecord.setobjectplus('managecrewid', w, x, c0right, 'text')

        c02 = MyBoundBox(orientation='horizontal')
        c02left = BoxLayout(orientation='horizontal', size_hint_x=.8)
        c02right = BoxLayout(orientation='horizontal', size_hint_x=.2)
        buttonadd = MyButton(text='Add')
        buttonadd.bind(on_press=self.crv_callback_click)
        buttonadd.bind(on_release=self.managecrew.callback_savenewcrew)
        c02left.add_widget(buttonadd)
        buttontop = MyButton(text='Top')
        buttontop.bind(on_press=self.crv_callback_click)
        buttontop.bind(on_release=self.managecrew.doscrolltop)
        c02right.add_widget(buttontop)
        buttonbot = MyButton(text='Bottom')
        buttonbot.bind(on_press=self.crv_callback_click)
        buttonbot.bind(on_release=self.managecrew.doscrollbottom)
        c02right.add_widget(buttonbot)
        c02.add_widget(c02left)
        c02.add_widget(c02right)

        c00.add_widget(c01)
        c00.add_widget(c02)

        middle.add_widget(c00)

        wdth = box.width
        scrollarchive = self.managecrew.scrollwidgetmanage(wdth)

        middle.add_widget(scrollarchive)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        button1 = MyButton(text='Back')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.crv_callback_settings_back)

        footer.add_widget(button1)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)
        #
        screen_managecrew.add_widget(box)

        return screen_managecrew

    def crv_setup_settings_required(self):
        Logger.info('CRV:SETUP:required')
        """
        Screen definition and setup for required settings
        """

        # read list of tidestations
        tidestations = self.data.gettidestations()

        screen_setting2 = Screen(name='screen_settings2')
        screen_setting2.bind(on_enter=self.settings_callback_onenter)

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        # header = self.logstart(3, 'screen_settings2')
        header = self.screencreateheader('screen_settings2')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        labinitial = MyLabel(halign = 'center',
                text='', color=self.crvcolor.getfgcolor())

        self.data.datarecord.setobject('settingshead', labinitial, 'label')

        middle.add_widget(labinitial)

        em0 = BoxLayout(orientation='horizontal')
        em0.add_widget(MyLabel(text='This is used to distribute logs. Other email addresses are available in the More Settings screen', color=self.crvcolor.getfgcolor(), size_hint=[.5, 1]))
        em = BoxLayout(orientation='horizontal')
        x, emt, lab = self.boxtextbox('Default Email Address (required)', szh)
        self.data.datarecord.setobjectplus('reqemaillog', x, emt, em, 'text')
        self.data.datarecord.getobject('reqemaillog').text = self.data.getemaillog()
        emt.bind(text=self.crv_callback_checkrequiredsettings)
        self.data.datarecord.setobjectplus('labemaillog', None, lab, em, 'label')

        middle.add_widget(em0)
        middle.add_widget(em)

        vn0 = BoxLayout(orientation='horizontal')
        vn0.add_widget(MyLabel(text='The vessel name is used for identifying the vessel and for crew lists', color=self.crvcolor.getfgcolor(), size_hint=[1, 1]))

        vn = BoxLayout(orientation='horizontal')
        top_szh = [.7, 1]
        #x, vnt, lab = self.boxtextbox('Vessel Name (required)', top_szh)
        v = self.managevessels.getvesslist()
        x, vnt, lab = self.boxdropdown('Vessel Name (required)', v, top_szh, readonly=True)
        #vnt.readonly = True
        self.data.datarecord.setobjectplus('reqvessname', x, vnt, vn, 'drop')
        vnt.bind(text=self.crv_callback_checkrequiredsettings)
        self.data.datarecord.setobjectplus('labvessname', None, lab, vn, 'label')
        vbut = MyButton(text='Manage Vessels', size_hint=[.3,1])
        vbut.bind(on_press=self.crv_callback_click)
        vbut.bind(on_release=self.crv_callback_managevessels)
        vn.add_widget(vbut)

        middle.add_widget(vn0)
        middle.add_widget(vn)

        td0 = BoxLayout(orientation='horizontal')
        td0.add_widget(MyLabel(text='The tide station is used for tide automation', color=self.crvcolor.getfgcolor(), size_hint=[1, 1]))

        td = BoxLayout(orientation='horizontal')
        x, tdt, lab = self.boxdropdown('Tide Station (required)', tidestations, szh, readonly=True)
        #tdt.readonly = True
        self.data.datarecord.setobjectplus('reqtidestation', x, tdt, td, 'drop')
        tdt.bind(text=self.crv_callback_checkrequiredsettings)
        self.data.datarecord.setobjectplus('labtidestation', None, lab, td, 'label')
        tbut = MyButton(text='Get Tide Data', size_hint=[.3,1])
        self.data.datarecord.setobject('requpdtidesbutton', tbut, 'button')
        tbut.disabled = True
        tbut.bind(on_press=self.crv_callback_click)
        tbut.bind(on_release=self.crv_callback_requpdatetides)
        td.add_widget(tbut)

        middle.add_widget(td0)
        middle.add_widget(td)

        button1 = MyButton(text='Home')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.crv_callback_reqhomebutton)
        self.data.datarecord.setobject('reqhomebutton', button1, 'button')
        button1.disabled = True

        button2 = MyButton(text='Manage Crew')
        button2.bind(on_release=self.crv_callback_managecrew)
        button2.bind(on_press=self.crv_callback_click)
        self.data.datarecord.setobject('reqmanagecrewbutton', button2, 'button')
        button2.disabled = True

        button3 = MyButton(text='Manage Locations')
        button3.bind(on_press=self.crv_callback_click)
        button3.bind(on_release=self.crv_callback_managelocations)
        # dont need a disable here - as locations are always available
        # also dont need an object as locations are simple

        buttonmore = MyButton(text='More Settings')
        buttonmore.bind(on_press=self.crv_callback_click)
        buttonmore.bind(on_release=self.crv_callback_moresettingsbutton)

        footer.add_widget(button1)
        footer.add_widget(button2)
        footer.add_widget(button3)
        footer.add_widget(buttonmore)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)

        screen_setting2.add_widget(box)
        screen_setting2.bind(on_enter=self.screenmanager_callback_onenter)

        return screen_setting2

    def crv_callback_lastscreen(self, instance):
        if self.data.lastscreen == '':
            self.data.lastscreen = 'screen_main'
        if not self.data.sm.has_screen(self.data.lastscreen):
            self.data.lastscreen = 'screen_main'
        self.data.sm.current = self.data.lastscreen

    def crv_setup_display_update(self):
        Logger.info('CRV:SETUP:update')
        '''
        This should be a generic screen that is written to when something is happening.
        The back button has to be able to return from whence it came.
        (i.e. the last screen).
        '''
        crv_setup_display_update = Screen(name='screen_display_update')

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        # header = self.logstart(3, 'screen_display_update')
        header = self.screencreateheader('screen_display_update')

        middle = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        middlecontents = BoxLayout(orientation='vertical')
        middletitle = MyLabel(size_hint_y=.2)
        self.data.datarecord.setobject('upddisplab', middletitle, 'label')

        middlecontents.add_widget(middletitle)

        gridlist = GridLayout(cols=1, rows=1, size_hint_x=1, size_hint_y=None)
        gridlist.bind(minimum_height=gridlist.setter('height'))
        self.data.datarecord.setobject('upddispgrid', gridlist, 'grid')

        wdth = box.width
        #sv = ScrollView(size_hint=(None,None), size=(400,400))
        sv = ScrollView()
        sv.add_widget(gridlist)

        box1 = BoxLayout(orientation='horizontal')
        pb = ProgressBar()

        box1.add_widget(pb)
        self.data.datarecord.setobject('upddisppb', pb, 'progressbar')

        middlecontents.add_widget(sv)
        middlecontents.add_widget(box1)

        middle.add_widget(middlecontents)
        footer = BoxLayout(orientation='horizontal', size_hint_y=.1)

        button1 = MyButton(text='Back')
        button1.bind(on_release=self.crv_callback_lastscreen)
        self.data.datarecord.setobject('upddispback', button1, 'button')

        footer.add_widget(button1)

        box.add_widget(header)
        box.add_widget(middle)
        box.add_widget(footer)

        crv_setup_display_update.add_widget(box)

        # used to display progress when sending emails
        self.data.setdisplayaction(self.displayaction)
        return crv_setup_display_update

    def crv_setup_boatlog_screen(self):
        Logger.info('CRV:SETUP:boatlog')
        self.boatlog.readlocations()

        screen_boatlog = Screen(name='screen_boatlog')
        screen_boatlog.bind(on_enter=self.screenmanager_callback_onenter)


        # logdict = {'time', 'type', 'from', 'to', 'arrived', 'incident', 'helm', 'nav', 'activity', 'action', 'result'}
        # logkeys = ['time', 'type', 'from', 'to', 'LOG']
        # loghead = {0: 'Time', 1: 'Type', 2: 'From', 3: 'To', 4: 'LOG'}

        szh = [.5, 1]
        box = BoxLayout(orientation='vertical', padding=10)

        # header = self.logstart(1, 'screen_boatlog')  # 1=showtime
        header = self.screencreateheader('screen_boatlog')

        middle = BoxLayout(orientation='vertical', size_hint_y=.8)

        footer = BoxLayout(orientation='horizontal', size_hint=[1, .1])

        activity = MyBoundBox(orientation='vertical', size_hint_y=.8)
        entrybox = MyBoundBox(orientation='horizontal')
        self.data.logrecord.setobject('logentrybox', entrybox, 'box')

        entrycommonlog = MyBoundBox(orientation='vertical', size_hint_x=.6)
        self.data.logrecord.setobject('logcommonlog', entrycommonlog, 'box')
        topentrycommon = MyBoundBox(orientation='horizontal')
        botentrycommon = MyBoundBox(orientation='horizontal')

        # entryboatlog = MyBoundBox(orientation='vertical')
        # self.data.logrecord.setobject('logtypeboat', entryboatlog, 'box')
        # topentryboat = MyBoundBox(orientation='horizontal')
        # botentryboat = MyBoundBox(orientation='horizontal')

        entryincidentlog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypeincident', entryincidentlog, 'box')
        topentryincident = MyBoundBox(orientation='horizontal')
        botentryincident = MyBoundBox(orientation='horizontal')

        entrytraininglog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypetraining', entrytraininglog, 'box')
        topentrytraining = MyBoundBox(orientation='horizontal')
        botentrytraining = MyBoundBox(orientation='horizontal')

        # entrymaintlog = MyBoundBox(orientation='vertical')
        # self.data.logrecord.setobject('logtypemaintenance', entrymaintlog, 'box')
        # topentrymaint = MyBoundBox(orientation='horizontal')
        # botentrymaint = MyBoundBox(orientation='horizontal')

        # entryprlog = MyBoundBox(orientation='vertical')
        # self.data.logrecord.setobject('logtypepr', entryprlog, 'box')
        # topentrypr = MyBoundBox(orientation='horizontal')
        # botentrypr = MyBoundBox(orientation='horizontal')

        # entryfundlog = MyBoundBox(orientation='vertical')
        # self.data.logrecord.setobject('logtypefund', entryfundlog, 'box')
        # topentryfund = MyBoundBox(orientation='horizontal')
        # botentryfund = MyBoundBox(orientation='horizontal')

        # entryprevalog = MyBoundBox(orientation='vertical')
        # self.data.logrecord.setobject('logtypeprevaction', entryprevalog, 'box')
        # topentrypreva = MyBoundBox(orientation='horizontal')
        # botentrypreva = MyBoundBox(orientation='horizontal')

        # entryeducationlog = MyBoundBox(orientation='vertical')
        # self.data.logrecord.setobject('logtypeeducation', entryeducationlog, 'box')
        # topentryeducation = MyBoundBox(orientation='horizontal')
        # botentryeducation = MyBoundBox(orientation='horizontal')

        entryfaultlog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypefault', entryfaultlog, 'box')
        topentryfault = MyBoundBox(orientation='horizontal')
        botentryfault = MyBoundBox(orientation='horizontal')

        entrystanddownlog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypestanddown', entrystanddownlog, 'box')
        topentrystanddown = MyBoundBox(orientation='horizontal')
        botentrystanddown = MyBoundBox(orientation='horizontal')

        entrylaunchlog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypelaunch', entrylaunchlog, 'box')
        topentrylaunch = MyBoundBox(orientation='horizontal')
        #botentrylaunch = MyBoundBox(orientation='horizontal')

        entryloglog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypelog', entryloglog, 'box')
        topentrylog = MyBoundBox(orientation='horizontal')
        #botentrylog = MyBoundBox(orientation='horizontal')

        entryfuellog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypefuel', entryfuellog, 'box')
        topentryfuel = MyBoundBox(orientation='horizontal')
        botentryfuel = MyBoundBox(orientation='horizontal')

        entryonstationlog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypeonstation', entryonstationlog, 'box')
        topentryonstation = MyBoundBox(orientation='horizontal')
        #botentryonstation = MyBoundBox(orientation='horizontal')

        entrycrewlog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypecrew', entrycrewlog, 'box')
        topentryaddcrew = MyBoundBox(orientation='horizontal')
        botentryaddcrew = MyBoundBox(orientation='horizontal')

        entryarrivelog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypearrive', entryarrivelog, 'box')
        topentryarrive = MyBoundBox(orientation='horizontal')

        entrydepartlog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypedepart', entrydepartlog, 'box')
        topentrydepart = MyBoundBox(orientation='horizontal')

        entryguestlog = MyBoundBox(orientation='vertical', size_hint_x=.4)
        self.data.logrecord.setobject('logtypeguest', entryguestlog, 'box')
        topentryguest = MyBoundBox(orientation='horizontal')
        botentryguest = MyBoundBox(orientation='horizontal')

        buttonbox1 = MyBoundBox(orientation='horizontal', size_hint_y=.4)

        entrybox.add_widget(entrycommonlog)

        # its just this single line that has to be changed when log type changed (default logtype is boat
        # that means we have to save this entryboatlog, entryincidentlog, etc widgets
        #entrybox.add_widget(entryboatlog)

        entrycommonlog.add_widget(topentrycommon)
        entrycommonlog.add_widget(botentrycommon)

        # entryboatlog.add_widget(topentryboat)
        # entryboatlog.add_widget(botentryboat)

        # entryincidentlog.add_widget(topentryincident)
        # entryincidentlog.add_widget(botentryincident)

        entrytraininglog.add_widget(topentrytraining)
        entrytraininglog.add_widget(botentrytraining)

        entryfaultlog.add_widget(topentryfault)
        entryfaultlog.add_widget(botentryfault)

        # entrymaintlog.add_widget(topentrymaint)
        # entrymaintlog.add_widget(botentrymaint)

        # entryprlog.add_widget(topentrypr)
        # entryprlog.add_widget(botentrypr)

        # entryfundlog.add_widget(topentryfund)
        # entryfundlog.add_widget(botentryfund)

        # entryprevalog.add_widget(topentrypreva)
        # entryprevalog.add_widget(botentrypreva)

        entrystanddownlog.add_widget(topentrystanddown)
        entrystanddownlog.add_widget(botentrystanddown)

        # entryeducationlog.add_widget(topentryeducation)
        # entryeducationlog.add_widget(botentryeducation)

        entrycrewlog.add_widget(topentryaddcrew)
        entrycrewlog.add_widget(botentryaddcrew)

        entrylaunchlog.add_widget(topentrylaunch)

        entryloglog.add_widget(topentrylog)

        entryfuellog.add_widget(topentryfuel)
        entryfuellog.add_widget(botentryfuel)

        entryonstationlog.add_widget(topentryonstation)

        entryarrivelog.add_widget(topentryarrive)

        entrydepartlog.add_widget(topentrydepart)

        entryguestlog.add_widget(topentryguest)
        entryguestlog.add_widget(botentryguest)

        # =========================================================
        # Create widgets for common log

        # When you select the time widget, set it to current time ONLY if empty
        w, x, l = self.boxtextbox('Time', szh, orientation='horizontal')
        x.bind(focus=self.act_callback_timefocus)
        self.data.logrecord.setobjectplus('logtime', w, x, topentrycommon, 'text')

        wloc, xloc, l = self.boxdropdown('Loc', self.boatlog.locations, [.5, 1])
        self.data.logrecord.setobjectplus('loglocation', wloc, xloc, topentrycommon, 'drop')

        # These options mist match the log selection records in data
        # (commented as "the different types of logs")

        whelm, xhelm, l = self.boxdropdown('Helm', self.crew.posscrewlist, [.5, 1])
        self.data.logrecord.setobjectplus('loghelm', whelm, xhelm, botentrycommon, 'drop')
        #
        wnav, xnav, l = self.boxdropdown('Nav', self.crew.posscrewlist, [.5, 1])
        self.data.logrecord.setobjectplus('lognav', wnav, xnav, botentrycommon, 'drop')

        disptypes=[]

        for n in self.data.logrecord.loggroup['logtypesdisp']:
            disptypes.append(n)
        disptypes.sort()

        wtype, x, l = self.boxdropdown('Type', disptypes, [.5, 1], readonly=True)
        #x.readonly = True
        x.postcall = self.changelogbytype

        self.data.logrecord.setobjectplus('logtype', wtype, x, botentrycommon, 'drop')

        # =========================================================
        # =========================================================
        # create widgets specific to incident log
        incdisptypes=[]

        for n in self.data.logrecord.loggroup['logtypesincdisp']:
            incdisptypes.append(n)
        incdisptypes.sort()

        wactivity, x, l = self.boxdropdown('Activity', incdisptypes, szh, readonly=True)
        #x.readonly = True
        x.postcall = self.changeactionbytype
        self.data.logrecord.setobjectplus('logincidentactivity', wactivity, x, topentryincident, 'drop')
        #w, x, l = self.boxtextbox('Notes', szh)
        #self.data.logrecord.setobjectplus('logincidentnotes', w, x, botentryincident, 'text')

        # --------------- create specific for incident action onscene
        # 1. checkbox: SAP, checkbox ExitStrategy
        # 2. text: notes
        entryincactonscene = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeinconscene', entryincactonscene, 'box')
        topentryinconscene = MyBoundBox(orientation='horizontal')
        botentryinconscene = MyBoundBox(orientation='horizontal')
        entryincactonscene.add_widget(topentryinconscene)
        entryincactonscene.add_widget(botentryinconscene)
        w, c, l = self.boxcheckbox('SAP', [1.2, 1])
        self.data.logrecord.setobjectlist('loginconssap', w, [c, l], topentryinconscene, 'checkbox')
        w, c, l = self.boxcheckbox('Exit Strategy', [1.2, 1])
        self.data.logrecord.setobjectlist('loginconsexits', w, [c, l], topentryinconscene, 'checkbox')
        w, x, l = self.boxtextbox('Notes', [.2, 1])
        self.data.logrecord.setobjectplus('loginconsnotes', w, x, botentryinconscene, 'text')


        # --------------- create specific for incident action tow
        # 1. text: taken to  time: arrived
        # 2. text: notes  check:dropped
        entryincacttow = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeinctow', entryincacttow, 'box')
        topentryinctow = MyBoundBox(orientation='horizontal')
        botentryinctow = MyBoundBox(orientation='horizontal')
        entryincacttow.add_widget(topentryinctow)
        entryincacttow.add_widget(botentryinctow)
        w, x, l = self.boxtextbox('Taken to', [.4, 1])
        self.data.logrecord.setobjectplus('loginctowtakento', w, x, topentryinctow, 'text')
        w, x = self.boxtimebox('Arrived', [.4, 1])
        x.bind(focus=self.data.settimeonobject)
        self.data.logrecord.setobjectplus('loginctowarrived', w, x, topentryinctow, 'text')
        w, x, l = self.boxtextbox('Notes', [.4, 1])
        self.data.logrecord.setobjectplus('loginctownotes', w, x, botentryinctow, 'text')
        w, c, l = self.boxcheckbox('Tow Dropped', [1.2, 1])
        self.data.logrecord.setobjectlist('loginctowdropped', w, [c, l], botentryinctow, 'checkbox')

        # --------------- create specific for incident action shadow
        # 1. text: shadow to  time:stopped shadow
        # 2. text: notes
        entryincactshadow = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeincshadow', entryincactshadow, 'box')
        topentryincshadow = MyBoundBox(orientation='horizontal')
        botentryincshadow = MyBoundBox(orientation='horizontal')
        entryincactshadow.add_widget(topentryincshadow)
        entryincactshadow.add_widget(botentryincshadow)
        w, x, l = self.boxtextbox('Shadow to', [.5, 1])
        self.data.logrecord.setobjectplus('logincshadowto', w, x, topentryincshadow, 'text')
        w, x = self.boxtimebox('Abandoned', [.5, 1])
        self.data.logrecord.setobjectplus('logincshadowleft', w, x, topentryincshadow, 'text')
        w, x, l = self.boxtextbox('Notes', [.5, 1])
        self.data.logrecord.setobjectplus('logincshadownotes', w, x, botentryincshadow, 'text')

        # --------------- create specific for incident action finish
        # 1. text: taken to
        # 2. text: notes
        entryincactfinish = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeincfinish', entryincactfinish, 'box')
        topentryincfinish = MyBoundBox(orientation='horizontal')
        botentryincfinish = MyBoundBox(orientation='horizontal')
        entryincactfinish.add_widget(topentryincfinish)
        entryincactfinish.add_widget(botentryincfinish)

        # --------------- create specific for incident action medical
        # 1. status
        # 2. text: notes
        entryincactmedical = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeincmedical', entryincactmedical, 'box')
        topentryincmedical = MyBoundBox(orientation='horizontal')
        botentryincmedical = MyBoundBox(orientation='horizontal')
        entryincactmedical.add_widget(topentryincmedical)
        entryincactmedical.add_widget(botentryincmedical)
        w, x, l = self.boxdropdown('Status',
                                        ['0', '1.Critical', '2.Serious', '3:Moderate', '4.Minor'], szh=[.5,1], readonly=True)
        #w.readonly = True
        self.data.logrecord.setobjectplus('logincmedicalstatus', w, x, topentryincmedical, 'drop')
        w, x, l = self.boxtextbox('Treatment/Notes', szh=[.5, 1])
        self.data.logrecord.setobjectplus('logincmedicalnotes', w, x, botentryincmedical, 'text')

        # --------------- create specific for incident action mechanical
        # 1. drop:Battery|Motor|Oil|Fuel|Other   checkbox: started
        # 2. notes
        entryincactmechanical = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeincmechanical', entryincactmechanical, 'box')
        topentryincmechanical = MyBoundBox(orientation='horizontal')
        botentryincmechanical = MyBoundBox(orientation='horizontal')
        entryincactmechanical.add_widget(topentryincmechanical)
        entryincactmechanical.add_widget(botentryincmechanical)
        w, x, l = self.boxdropdown('Reason',
                                        ['Battery', 'Motor', 'Fuel', 'Hull', 'Other'], szh, readonly=True)
        #w.readonly = True
        self.data.logrecord.setobjectplus('logincmechanicalreason', w, x, topentryincmechanical, 'drop')
        w, c, l = self.boxcheckbox('Started', [.5, 1])
        self.data.logrecord.setobjectlist('logincmechanicalstarted', w, [c, l], topentryincmechanical, 'checkbox')
        w, x, l = self.boxtextbox('Notes', [.2, 1])
        self.data.logrecord.setobjectplus('logincmechanicalnotes', w, x, botentryincmechanical, 'text')

        # --------------- create specific for incident action sinking
        # 1. notes
        entryincactsinking = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeincsinking', entryincactsinking, 'box')
        topentryincsinking = MyBoundBox(orientation='horizontal')
        botentryincsinking = MyBoundBox(orientation='horizontal')
        entryincactsinking.add_widget(topentryincsinking)
        #entryincactsinking.add_widget(botentryincsinking)
        w, x, l = self.boxtextbox('Notes', szh=[1,.3], multiline=True, orientation='vertical')
        self.data.logrecord.setobjectplus('logincsinkingnotes', w, x, topentryincsinking, 'text')

        # --------------- create specific for incident action aground
        # 1. notes
        entryincactaground = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeincaground', entryincactaground, 'box')
        topentryincaground = MyBoundBox(orientation='horizontal')
        #botentryincaground = MyBoundBox(orientation='horizontal')
        entryincactaground.add_widget(topentryincaground)
        #entryincactaground.add_widget(botentryincaground)
        w, x, l = self.boxtextbox('Notes', szh=[1,.3], multiline=True, orientation='vertical')
        self.data.logrecord.setobjectplus('logincagroundnotes', w, x, topentryincaground, 'text')

        # --------------- create specific for incident action search
        # 1. notes
        entryincactsearch = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeincsearch', entryincactsearch, 'box')
        topentryincsearch = MyBoundBox(orientation='horizontal')
        #botentryincsearch = MyBoundBox(orientation='horizontal')
        entryincactsearch.add_widget(topentryincsearch)
        #entryincactsearch.add_widget(botentryincsearch)
        w, x, l = self.boxtextbox('Notes', szh=[1,.3], multiline=True, orientation='vertical')
        self.data.logrecord.setobjectplus('logincsearchnotes', w, x, topentryincsearch, 'text')

        # --------------- create specific for incident action other
        # 1. notes
        entryincactother = MyBoundBox(orientation='vertical')
        self.data.logrecord.setobject('logtypeincother', entryincactother, 'box')
        topentryincother = MyBoundBox(orientation='horizontal')
        #botentryincother = MyBoundBox(orientation='horizontal')
        entryincactother.add_widget(topentryincother)
        #entryincactother.add_widget(botentryincother)
        w, x, l = self.boxtextbox('Notes', szh=[1,.3], multiline=True, orientation='vertical')
        self.data.logrecord.setobjectplus('logincothernotes', w, x, topentryincother, 'text')

        # =========================================================
        # =========================================================
        # =========================================================
        # create widgets specific to boat log (duty boat)
        # wactivity, x, l = self.boxdropdown('Activity',
        #                                 ['Launch', 'Log', 'Fuel', 'OnStation'], szh)
        # #lact = len(l.text)
        # wactivity.readonly = False
        # self.data.logrecord.setobjectplus('logactivity', wactivity, x, topentryboat, 'drop')

        #whelm, x, l = self.boxdropdown('Helm', self.crew.posscrewlist, szh)
        #self.data.logrecord.setobjectplus('loghelm', whelm, x, topentryboat, 'drop')
        # w, x, l = self.boxtextbox('Notes', [.2, 1])
        # self.data.logrecord.setobjectplus('logboatnotes', w, x, botentryboat, 'text')
        #botentryboat.add_widget(MyFilledBox())

        # =========================================================
        # create widgets specific to training log
        #whelm, x, l = self.boxdropdown('On Helm', self.crew.posscrewlist, szh)
        #self.data.logrecord.setobjectplus('logtraininghelm', whelm, x, topentrytraining, 'drop')
        #wnav, x, l = self.boxdropdown('On Nav', self.crew.posscrewlist, szh)
        #self.data.logrecord.setobjectplus('logtrainingnav', wnav, x, topentrytraining, 'drop')

        w, x, l = self.boxtextbox('Activity', szh)
        self.data.logrecord.setobjectplus('logtrainingactivity', w, x, topentrytraining, 'text')
        w, x, l = self.boxtextbox('Notes', szh)
        self.data.logrecord.setobjectplus('logtrainingnotes', w, x, botentrytraining, 'text')

        # =========================================================
        # create widgets specific to fault log
        w, x, l = self.boxtextbox('Fault', szh)
        self.data.logrecord.setobjectplus('logfaultaction', w, x, topentryfault, 'text')
        w, x, l = self.boxtextbox('Outcome', szh)
        self.data.logrecord.setobjectplus('logfaultresult', w, x, botentryfault, 'text')

        # # =========================================================
        # # create widgets specific to maintenance log
        # w, x, l = self.boxtextbox('Action', szh)
        # self.data.logrecord.setobjectplus('logmaintaction', w, x, topentrymaint, 'text')
        # w, x, l = self.boxtextbox('Outcome', szh)
        # self.data.logrecord.setobjectplus('logmaintresult', w, x, botentrymaint, 'text')

        # # =========================================================
        # # create widgets specific to pr log
        # w, x, l = self.boxtextbox('Action', szh)
        # self.data.logrecord.setobjectplus('logpraction', w, x, topentrypr, 'text')
        # w, x, l = self.boxtextbox('Outcome', szh)
        # self.data.logrecord.setobjectplus('logprresult', w, x, botentrypr, 'text')

        # # =========================================================
        # # create widgets specific to fund log
        # w, x, l = self.boxtextbox('Action', szh)
        # self.data.logrecord.setobjectplus('logfundaction', w, x, topentryfund, 'text')
        # w, x, l = self.boxtextbox('Outcome', szh)
        # self.data.logrecord.setobjectplus('logfundresult', w, x, botentryfund, 'text')

        # # =========================================================
        # # create widgets specific to preventative action log
        # w, x, l = self.boxtextbox('Action', szh)
        # self.data.logrecord.setobjectplus('logprevactionaction', w, x, topentrypreva, 'text')
        # w, x, l = self.boxtextbox('Outcome', szh)
        # self.data.logrecord.setobjectplus('logprevactionresult', w, x, botentrypreva, 'text')

        # =========================================================
        # create widgets specific to stand down log
        w, x, l = self.boxtextbox('Action', szh)
        self.data.logrecord.setobjectplus('logstanddownaction', w, x, topentrystanddown, 'text')
        w, x, l = self.boxtextbox('Outcome', szh)
        self.data.logrecord.setobjectplus('logstanddownresult', w, x, botentrystanddown, 'text')

        # # =========================================================
        # # create widgets specific to education log
        # w, x, l = self.boxtextbox('Action', szh)
        # self.data.logrecord.setobjectplus('logeducationaction', w, x, topentryeducation, 'text')
        # w, x, l = self.boxtextbox('Outcome', szh)
        # self.data.logrecord.setobjectplus('logeducationresult', w, x, botentryeducation, 'text')

        # =========================================================
        # create widgets specific to additional crew log
        w, x, l = self.boxdropdown('Crew\nName/ID', self.crew.posscrewlist, szh)
        self.data.logrecord.setobjectplus('logcrewaddname', w, x, topentryaddcrew, 'drop')
        w, c, l = self.boxcheckbox('IMSAFE', [.5, 1])
        self.data.logrecord.setobjectlist('logcrewaddimsafe', w, [c, l], botentryaddcrew, 'checkbox')

        # =========================================================
        # create widgets specific to launch log
        w, x, l = self.boxtextbox('Notes', szh)
        self.data.logrecord.setobjectplus('loglaunchnotes', w, x, topentrylaunch, 'text')

        # =========================================================
        # create widgets specific to log log
        w, x, l = self.boxtextbox('Notes', szh)
        self.data.logrecord.setobjectplus('loglognotes', w, x, topentrylog, 'text')

        # =========================================================
        # create widgets specific to fuel log
        w, x, l = self.boxdropdown('Fuel\nType', ['Diesel', 'Petrol'], szh, readonly=True)
        #x.readonly = True
        x.postcall = self.crv_callback_logfueltype
        self.data.logrecord.setobjectplus('logfueltype', w, x, topentryfuel, 'drop')
        w, x = self.boxnumbox('Added\n(l)', szh=szh)
        self.data.logrecord.setobjectplus('logfueladded', w, x, topentryfuel, 'text')
        w, x, l = self.boxtextbox('Price ($)', szh=szh, infilter='float')
        self.data.logrecord.setobjectplus('logfuelprice', w, x, botentryfuel, 'text')
        w, x, l = self.boxtextbox('Notes', szh)
        self.data.logrecord.setobjectplus('logfuelnotes', w, x, botentryfuel, 'text')

        # =========================================================
        # create widgets specific to arrival log
        w, x, l = self.boxtextbox('Notes', szh)
        self.data.logrecord.setobjectplus('logarrivenotes', w, x, topentryarrive, 'text')

        # =========================================================
        # create widgets specific to departure log
        w, x, l = self.boxtextbox('Notes', szh)
        self.data.logrecord.setobjectplus('logdepartnotes', w, x, topentrydepart, 'text')

        # =========================================================
        # create widgets specific to guest log
        w, x, l = self.boxtextbox('Guest\nName', szh)
        self.data.logrecord.setobjectplus('logguestname', w, x, topentryguest, 'text')

        wact, x, l = self.boxdropdown('Add/Remove', ['Add', 'Remove'], szh, readonly=True)
        #wact.readonly = True
        self.data.logrecord.setobjectplus('logguestaction', wact, x, botentryguest, 'drop')

        buttonsave = MyButton(text='Save Log Entry')
        buttonsave.bind(on_press=self.crv_callback_click)
        buttonsave.bind(on_release=self.boatlog.callback_save_boatlog)
        buttonclear = MyButton(text='Cancel/Clear')
        buttonclear.bind(on_press=self.crv_callback_click)
        buttonclear.bind(on_release=self.boatlog.callback_cancel)
        buttonbox1.add_widget(buttonsave)
        buttonbox1.add_widget(buttonclear)

        activity.add_widget(entrybox)
        activity.add_widget(buttonbox1)

        middle.add_widget(activity)

        actscroll = self.boatlog.scrollwidget(entrycommonlog.width)
        middle.add_widget(actscroll)

        button1 = MyButton(text='Home')
        button1.bind(on_press=self.crv_callback_click)
        button1.bind(on_release=self.crv_callback_home)
        self.data.datarecord.setobject('homeboatlog', button1, 'button')
        footer.add_widget(button1)

        buttonincident = MyButton(text='NEW/OPEN INCIDENT!!\n(double tap)')
        buttonincident.bind(on_press=self.crv_callback_click)
        buttonincident.bind(on_release=self.crv_image_click)
        footer.add_widget(buttonincident)

        # buttontogview = MyButton(text='Toggle View')
        # buttontogview.bind(on_press=self.crv_callback_click)
        # buttontogview.bind(on_release=self.boatlog.toggle_logview)
        # #buttontogview.bind(on_release=lambda dbtn:self.boatlog.toggle_logview())
        # footer.add_widget(buttontogview)

        box.add_widget(header)  # .1
        box.add_widget(middle)  # .8
        box.add_widget(footer)  # .1

        screen_boatlog.add_widget(box)

        return screen_boatlog

    def crv_setup_closelog_screen(self):
        Logger.info('CRV:SETUP:closelog')
        # we create a screen
        #    under this we create a grid
        #       under this we create 3 boxlayouts
        #           box0 contains a logo and date
        #           box1 contains a scrollview with the data to change
        #           box2 contains the 2 buttons that navigate
        #
        screen_crvclose = Screen(name='screen_crvclose')
        szh = [.5, 1]

        box_logclose = BoxLayout(orientation='vertical', padding=10)

        # header_close = self.logstart(1, 'screen_crvclose')  # 1=showtime
        header_close = self.screencreateheader('screen_crvclose')

        b = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.8)

        box_prices = MyBoundBox(orientation='vertical', pos_hint_x=0, size_hint_y=.1)
        prices = MyBoundBox(orientation='horizontal')

        buttonrec = MyButton(text='Recovery Checklist and Signoff')
        buttonrec.bind(on_press=self.crv_callback_click)
        buttonrec.bind(on_release=self.crv_callback_reccheck)
        prices.add_widget(buttonrec)

        w, x, l = self.boxtextbox('CRV Fuel\nPrice ($/l)', orientation='horizontal', szh=szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        self.data.datarecord.setobjectplus('fuelprice', w, x, prices, 'text')

        w, x, l = self.boxtextbox('Supplied Fuel\nPrice ($/l)', orientation='horizontal', szh=szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        self.data.datarecord.setobjectplus('fuelsuppliedprice', w, x, prices, 'text')

        box_prices.add_widget(prices)

        b0 = MyBoundBox(orientation='horizontal', size_hint_y=.4) # holds both engine and fuel

        enginecloselayout = MyBoundBox(orientation='vertical', size_hint_x=.9) # the whole engine box
        enginecloselayout.id = ''

        fuelcloselayout = MyBoundBox(orientation='vertical')

        b0.add_widget(enginecloselayout)
        b0.add_widget(fuelcloselayout)

        lrow1 = MyBoundBox(orientation='horizontal', size_hint_y=.2)
        lrow23 = MyBoundBox(orientation='vertical') #, size_hint_y=.2)

        lrow2 = MyBoundBox(orientation='horizontal')
        lrow3 = MyBoundBox(orientation='horizontal')
        lrow23.add_widget(lrow2)
        lrow23.add_widget(lrow3)

        lrow4 = MyBoundBox(orientation='vertical') #, size_hint_y=.2)

        enginecloselayout.add_widget(lrow1)
        enginecloselayout.add_widget(lrow23)
        enginecloselayout.add_widget(lrow4)

        lrow1.add_widget(MyLabel(text=''))
        lrow2.add_widget(MyLabel(text='Engine Hours\nFinish', color=self.crvcolor.getfgcolor()))
        lrow3.add_widget(MyLabel(text='Engine Hours\nDuration', color=self.crvcolor.getfgcolor()))

        enginecloselablayout = BoxLayout(orientation='horizontal')
        lrow1.add_widget(enginecloselablayout)

        fin = MyBoundBox(orientation='horizontal')
        dur = MyBoundBox(orientation='horizontal')

        lrow2.add_widget(fin)
        lrow3.add_widget(dur)
        self.data.datarecord.setobject('closelablayout', enginecloselablayout, 'layout')
        self.data.datarecord.setobject('enginehoursclose', enginecloselayout, 'layout')
        self.data.datarecord.setobject('enginehoursclosefin', fin, 'layout')
        self.data.datarecord.setobject('enginehoursclosedur', dur, 'layout')

        w, c, l = self.boxtextbox('portfin', orientation='vertical', nolabel=True, szh=szh, infilter='float')
        c.bind(focus=self.portcallbackfocus)
        self.data.datarecord.setobject('portehoursfin', c, 'text')
        self.data.datarecord.setobject('enginehoursclosefinp', w, 'layout')

        w, c, l = self.boxtextbox('sbfin', orientation='vertical', nolabel=True, szh=szh, infilter='float')
        c.bind(focus=self.sbcallbackfocus)
        self.data.datarecord.setobject('sbehoursfin', c, 'text')
        self.data.datarecord.setobject('enginehoursclosefinsb', w, 'layout')

        w, c, l = self.boxtextbox('portdur', orientation='vertical', nolabel=True, szh=szh, infilter='float')
        c.bind(focus=self.portcallbackfocus)
        self.data.datarecord.setobject('portehoursdur', c, 'text')
        self.data.datarecord.setobject('enginehoursclosedurp', w, 'layout')

        w, c, l = self.boxtextbox('Starboard', orientation='vertical', nolabel=True, szh=szh, infilter='float')
        c.bind(focus=self.sbcallbackfocus)
        self.data.datarecord.setobject('sbehoursdur', c, 'text')
        self.data.datarecord.setobject('enginehoursclosedursb', w, 'layout')

        boxclosing = MyBoundBox(orientation='horizontal')
        lrow4.add_widget(boxclosing)
        x, c, l = self.boxcheckbox('Closing Checks\nComplete', [1, 1])
        self.data.datarecord.setobjectlist('closingchecks', x, [c, l], boxclosing, 'checkbox')
        c.bind(active=self.crv_callback_checkcloselogstatus)

        w, x, l = self.boxtextbox('Closing\nTime', szh=[1,1])
        x.bind(focus=self.crv_callback_closingtimefocus)
        self.data.datarecord.setobjectplus('closingtime', w, x, boxclosing, 'text')

        #============= Signature ======================
        signed = BoxLayout(orientation='horizontal')
        lrow4.add_widget(signed)

        w, x, l = self.boxdropdown('Signed\nby', self.crew.posscrewlist, szh)
        self.data.datarecord.setobjectplus('recsigned', w, x, signed, 'text')
        x.bind(text=self.crv_callback_checkreccheck)

        paint = SigWidget()
        paint.disabled = True
        self.data.datarecord.setobject('recsignature', paint, 'SigWidget')
        signed.add_widget(paint)

        buttonsv = MyButton(text='Save\nSignature', size_hint_x=.4)
        buttonsv.id = 'savesignature'
        signed.add_widget(buttonsv)
        buttonsv.bind(on_release=self.crv_callback_checkreccheck)
        #==============================================

        #szh = [.7, 1]

        rrow1 = MyBoundBox(orientation='horizontal', size_hint_y=.2)
        rrow23 = MyBoundBox(orientation='vertical') #, size_hint_y=.2)

        rrow2 = MyBoundBox(orientation='horizontal')
        rrow3 = MyBoundBox(orientation='horizontal')
        rrow4 = MyBoundBox(orientation='vertical') #, size_hint_y=.2)

        fuelcloselayout.add_widget(rrow1)
        fuelcloselayout.add_widget(rrow23)
        rrow23.add_widget(rrow2)
        rrow23.add_widget(rrow3)
        fuelcloselayout.add_widget(rrow4)

        fuellabel = MyLabel(text='')
        self.data.datarecord.setobject('fuellabel', fuellabel, 'label')

        fuelcloselablayout = BoxLayout(orientation='horizontal')
        fuelcloselablayout.add_widget(fuellabel)
        rrow1.add_widget(fuelcloselablayout)

        w, x, l = self.boxtextbox('Fuel Finish', szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        self.data.datarecord.setobjectplus('fuelfin', w, x, rrow2, 'text')

        w, x, l = self.boxtextbox('Fuel Used', szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        x.readonly = True
        self.data.datarecord.setobjectplus('fuelused', w, x, rrow2, 'text')

        w, x, l = self.boxtextbox('Fuel Added', szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        self.data.datarecord.setobjectplus('fueladded', w, x, rrow3, 'text')

        w, x, l = self.boxtextbox('Fuel Now', szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        x.readonly = True
        self.data.datarecord.setobjectplus('fuelatend', w, x, rrow3, 'text')

        boxclosing2 = MyBoundBox(orientation='horizontal')
        rrow4.add_widget(boxclosing2)

        w, x, l = self.boxtextbox('CRV Fuel\nCost ($)', szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        x.readonly = True
        self.data.datarecord.setobjectplus('fuelcost', w, x, boxclosing2, 'text')

        wtyp, xtyp, ltyp = self.boxdropdown('Supp Fuel\nType', ['Diesel', 'Petrol'], szh, readonly=True)
        #xtyp.readonly = True
        self.data.datarecord.setobjectplus('fuelsuppliedtype', wtyp, xtyp, boxclosing2, 'drop')

        fuelsupplied = MyBoundBox(orientation='horizontal')
        rrow4.add_widget(fuelsupplied)

        #fuelsuppliedline2 = BoxLayout(orientation='horizontal')
        #fuelsupplied.add_widget(fuelsuppliedline2)

        w, x, l = self.boxtextbox('Supp Fuel\nAdded', szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        x.readonly = True
        self.data.datarecord.setobjectplus('fuelsuppliedadded', w, x, fuelsupplied, 'text')

        w, x, l = self.boxtextbox('Fuel Supp\nCost ($)', szh, infilter='float')
        x.bind(focus=self.fuelcallbackfocus)
        x.readonly = True
        self.data.datarecord.setobjectplus('fuelsuppliedcost', w, x, fuelsupplied, 'text')

        b.add_widget(box_prices)
        b.add_widget(b0)

        footer_close = BoxLayout(orientation='horizontal', size_hint=[1, .1])

        button2 = MyButton(text='Close and Send Log')
        button2.bind(on_press=self.crv_callback_click)
        button2.bind(on_release=self.crv_callback_closethelog)
        button2.disabled = True
        self.data.datarecord.setobject('closelogbutton', button2, 'button')

        button3 = MyButton(text='Home')
        button3.bind(on_press=self.crv_callback_click)
        button3.bind(on_release=self.crv_callback_home)
        #button3.bind(on_release=self.crv_callback_closelogcancel)

        footer_close.add_widget(button2)
        footer_close.add_widget(button3)

        box_logclose.add_widget(header_close)
        box_logclose.add_widget(b)
        box_logclose.add_widget(footer_close)

        screen_crvclose.add_widget(box_logclose)
        screen_crvclose.bind(on_enter=self.screenmanager_callback_onenter)

        return screen_crvclose

#
#       Top level
#

if __name__ == '__main__':
    CRV().run()

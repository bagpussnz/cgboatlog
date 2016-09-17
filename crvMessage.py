__author__ = 'ian.collins'

import kivy

kivy.require('1.9.0')
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
import sys

class MessageBox():
    white = [1, 1, 1, 0]
    black = [0, 0, 0, 1]

    def popup_callback(self, instance):
        """callback for button press"""
        self.retvalue = instance.text
        self.popup.dismiss()
        if self.exitondismiss: sys.exit()

    def __init__(self, parent, titleheader="Title", doexit=False, message="Message", options=None, **kwargs):
#        super(MessageBox, self).__init__(**kwargs)
        if not options:
            options = {"OK": ""}

        self.parent = parent
        self.retvalue = None
        self.exitondismiss=doexit
        self.titleheader = titleheader
        self.message = message
        self.options = options
        #self.size = size
        box = GridLayout(orientation='vertical', cols=1)
        box.add_widget(Label(text=self.message, font_size=16))
        b_list = []
        buttonbox = BoxLayout(orientation='horizontal')
        for b in self.options:
            b_list.append(Button(text=b, size_hint=(1, .35), font_size=20))
            if self.options[b] is not None and self.options[b] != '':
                b_list[-1].bind(on_press=self.options[b])
            else:
                b_list[-1].bind(on_press=self.popup_callback)
            buttonbox.add_widget(b_list[-1])
        box.add_widget(buttonbox)
        self.popup = ModalView(auto_dismiss=True, size_hint=(1, 1))
        #self.popup = ModalView(auto_dismiss=False, size_hint=(None, None), size=(800, 800))
        self.popup.add_widget(box)
        #self.popup = Popup(title=titleheader, color=self.black, background_color=self.white, content=box, size_hint=(.9,.9))
        self.popup.bind(on_dismiss=self.onclose)
        self.popup.open()

    def onclose(self, event):
        self.popup.unbind(on_dismiss=self.onclose)
        self.popup.dismiss()
        if self.retvalue is not None and self.options[self.retvalue] != "":
            command = "self.parent." + self.options[self.retvalue]
            exec command

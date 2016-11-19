from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup

class CrvPopup():
    def __init__(self, mess='', bindto=None, progress=False, buttontext='Dismiss'):
        self.popup = None

        self.popuptitle = mess
        self.popupbuttontext = buttontext
        self.popuproot = None
        self.popuplabel = None
        self.popupbutton = None
        self.popupprogress = None
        self.doprogress = progress

    def popup_text(self, mess='', iserror=False):
        self.popuplabel = mess
        if iserror: self.popup_error()

    def popup_error(self):
        self.popupbutton.disabled = False

    def popup_end(self):
        self.popupbutton.disabled = False

    def popup_progress(self, value=None, pmax=None):
        if self.popupprogress is not None:
            if value is not None: self.popupprogress.value = value
            if pmax is not None: self.popupprogress.max = pmax
            if self.popupprogress.value > self.popupprogress.max:
                if self.popupbutton is not None:
                    self.popupbutton.disabled = False

    def popup_show(self):
        self.popuproot = BoxLayout()
        self.popuplabel = Label()
        self.popupbutton = Button(text=self.popupbuttontext)

        if self.doprogress:
            self.popupprogress = ProgressBar()
            self.popuproot.add_widget(self.popupprogress)
            self.popupbutton.disabled = True   # enabled on error or progress bar full

        self.popuproot.add_widget(self.popupbutton)

        #popup = Popup(title=mess, content=content, auto_dismiss=True, size_hint=(None, None), size=(400, 100))
        self.popup = Popup(title=self.popuptitle, content=self.popuproot, auto_dismiss=False)
        self.popupbutton.bind(on_press=self.popup.dismiss)
        self.popup.open()
        return True
        #if bindto is not None: bindto.focus = True

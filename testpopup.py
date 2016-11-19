from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock, mainthread

from kivy.clock import Clock

import time, threading

kv = """
<PopupBox>:
    pop_up_text: _pop_up_text
    pop_up_pb: _pop_up_pb
    size_hint: .5, .5
    auto_dismiss: True
    title: 'Status'

    BoxLayout:
        orientation: "vertical"
        Label:
            id: _pop_up_text
            text: ''
        ProgressBar:
            id: _pop_up_pb
            max: 100
            value: 0
"""

class PopupBox(Popup):
    pop_up_text = ObjectProperty()

    def update_pop_up_text(self, p_message):
        self.pop_up_text.text = p_message

    def update_val(self, v):
        self.pop_up_pb.value = v
        print "pb val.. " + str(v)

class ExampleApp(App):


    def build(self):
        Builder.load_string(kv)
        root = BoxLayout()


        b = Button(text="click")
        root.add_widget(b)

        b.bind(on_press=self.show_popup)
        return root

    def dopopup(self, mess, bindto=None, progress=None):
        content = Button(text='Dismiss')
        popup = Popup(title=mess, content=content, auto_dismiss=True)
        content.bind(on_press=popup.dismiss)
        popup.open()
        return popup
        # if bindto is not None: bindto.focus = True

    def show_popup(self, instance):
        # self.pop_up = Factory.PopupBox()
        # self.pop_up.update_pop_up_text('Running some task...')
        # self.pop_up.update_val(10)
        # self.pop_up.open()
        self.show_popup = self.dopopup("test")
        # Call some method that may take a while to run.
        # I'm using a thread to simulate this
        print 'start thread'
        mythread = threading.Thread(target=self.something_that_takes_10_seconds_to_run)
        mythread.start()

    def something_that_takes_10_seconds_to_run(self):
        thistime = time.time()
        n = 0
        while thistime + 10 > time.time(): # 5 seconds
            self.pop_up.update_pop_up_text(str(time.time()))
            self.pop_up.update_val(n)
            n = n + 10
            print str(time.time())
            time.sleep(1)

        # Once the long running task is done, close the pop up.
        self.pop_up.dismiss()

if __name__ == "__main__":
    ExampleApp().run()

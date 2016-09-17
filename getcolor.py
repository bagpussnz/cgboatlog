import kivy

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class getcolor(App):
    def __init__(self):
        pass

    def build(self):
        b = BoxLayout()
        t1 = TextInput()
        t2 = TextInput()
        b.add_widget(t1)
        b.add_widget(t2)

        t1.add_widget(focus=self.tfocus)
        t2.add_widget(focus=self.tfocus)
        return b

if __name__ == '__main__':
    getcolor().run()

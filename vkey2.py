import kivy

from kivy.app import App
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

class vTest(VKeyboard):
    player = VKeyboard()
    player.docked = False

class VkeyboardApp(App):
    def tfocus(self, instance):
        pass

    def __init__(self):
        self.vk = vTest()

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
    VkeyboardApp().run()

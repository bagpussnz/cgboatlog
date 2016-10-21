from kivy.config import Config
#Config.set('graphics', 'borderless', '0')
Config.set('kivy', 'keyboard_mode', 'systemandmulti')
#Config.set('graphics', 'width', '1920')
#Config.set('graphics', 'height', '1080')
#onfig.set('graphics', 'fullscreen', 'auto')
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard
from kivy.base import runTouchApp

kv="""<Widgets>:
    Button:
        size: 100,100
        pos: 100,100
        text: 'test'
        on_press: app.testy()

    Button:
        size: 100,100
        pos: 200,100
        text: 'quit'
        on_press: app.quitme()
"""
Builder.load_string(kv)

class Widgets(Widget):
    pass


class MyKeyboardListener(Widget):

    def __init__(self, **kwargs):
        super(MyKeyboardListener, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self, 'text')
        if self._keyboard.widget:
            # If it exists, this widget is a VKeyboard object which you can use
            # to change the keyboard layout.
            pass
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print('The key', keycode, 'have been pressed')
        print(' - text is %r' % text)
        print(' - modifiers are %r' % modifiers)

        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[1] == 'escape':
            keyboard.release()

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True



class myApp(App):

    def build(self):
        global w
        w = Widgets()
        return w

    def testy(self):
        runTouchApp(MyKeyboardListener())

    def quitme(self):
        quit()



if __name__ == "__main__":
    myApp().run()


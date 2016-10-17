from kivy.config import Config
#Config.set('graphics', 'borderless', '0')
#Config.set('kivy', 'keyboard_mode', 'systemandmulti')
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
from kivy.uix.textinput import TextInput
from kivy.uix.textinput import TextInput
from kivy.animation import Animation
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout, GridLayoutException
from kivy.uix.progressbar import ProgressBar
from kivy.uix.listview import ListView
from kivy.uix.listview import ListItemLabel
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout

kv="""<MyVKeyboard>:
    layout: "qwerty"
    #size: (700,70)"""

class MyVKeyboard(VKeyboard):
    def __init__(self, **kwargs):
        super(MyVKeyboard, self).__init__(**kwargs)
        self.setup_mode(False)


    def setup_mode_dock(self, *largs):
        '''Setup the keyboard in docked mode.

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
        scale = win.width / float(self.width)
        self.scale = scale
        self.pos = 0.0, win.height - self.height
        win.bind(on_resize=self._update_dock_mode)


    def _update_dock_mode(self, win, *largs):
        scale = win.width / float(self.width)
        self.scale = scale
        self.pos = 0, win.height - self.height


class MyTextInput(TextInput):
    def __init__(self, **kwargs):
        super(MyTextInput, self).__init__(**kwargs)

    def on_focus(self, instance, value, *largs):
        win = self.get_root_window()

        if win:
            win.release_all_keyboards()
            win._keyboards = {}

            if value: #User focus; use special keyboard
                win.set_vkeyboard_class(MyVKeyboard)
                print "NumericVKeyboard:", win._vkeyboard_cls, VKeyboard.layout_path
            else: #User defocus; switch back to standard keyboard
                win.set_vkeyboard_class(VKeyboard)
                print "VKeyboard:", win._vkeyboard_cls, VKeyboard.layout_path

        #return TextInput.on_focus(self, instance, value, *largs)
##########

class myApp(App):

    def build(self):
        Builder.load_string(kv)

        self.approot = BoxLayout(orientation='vertical')

        t1 = MyTextInput()
        self.approot.add_widget(t1)
        t2 = MyTextInput()
        self.approot.add_widget(t2)

        return self.approot



if __name__ == "__main__":
    myApp().run()


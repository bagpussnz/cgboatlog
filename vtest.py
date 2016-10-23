from kivy.app import App
from kivy.lang import Builder
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from kivy.logger import Logger
import time
import datetime

kv="""
<MyVKeyboardQwerty>:
    layout: 'qwerty'

<MyVKeyboardNumeric>:
    layout: 'numeric.json'
"""

'''
#Contents of file numeric.json in app directory

{
"title" : "Numeric",
"description" : "A numeric keypad",
"cols" : 3,
"rows": 4,
"normal_1": [
["7", "7", "7", 1],
["8", "8", "8", 1],
["9", "9", "9", 1]],
"normal_2": [
["4", "4", "4", 1],
["5", "5", "5", 1],
["6", "6", "6", 1]],
"normal_3": [
["1", "1", "1", 1],
["2", "2", "2", 1],
["3", "3", "3", 1]],
"normal_4": [
["0", "0", "0", 1],
[".", ".", ".", 1],
["\u232b", null, "backspace", 1]],
"shift_1": [
["7", "7", "7", 1],
["8", "8", "8", 1],
["9", "9", "9", 1]],
"shift_2": [
["4", "4", "4", 1],
["5", "5", "5", 1],
["6", "6", "6", 1]],
"shift_3": [
["1", "1", "1", 1],
["2", "2", "2", 1],
["3", "3", "3", 1]],
"shift_4": [
["0", "0", "0", 1],
[".", ".", ".", 1],
["\u232b", null, "backspace", 1]]
}
'''

class clsLog():
    def __init__(self):
        self.lasttime = -1
        Logger.setLevel('DEBUG')


    def tm(self):
        millis = int(round(time.time() * 1000))
        if self.lasttime == -1:
            m = ' [' + datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S") + ']'
        else:
            m = ' [' + str(millis - self.lasttime) + ' ms]'
        self.lasttime = millis

        return m

    def info(self, *args):
        m = self.tm()
        Logger.info(args[0] + m)

    def debug(self, *args):
        m = self.tm()
        Logger.debug(args[0] + m)


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
        scale = win.width / float(self.width)
        #scale = 1.0
        self.do_scale
        self.scale = scale
        Logger.info("vtest: setup scale " + str(scale))

        print "setup scale " + str(scale)
        print "win.height " + str(win.height)
        print "self.height " + str(self.height)
        #ty = win.height - ((self.height * scale) - 30.0)
        #ty = win.height - ((self.height-30) * scale)
        ty = win.height - (self.height * self.scale) - 30.0


        #ty = win.height - self.height - 30.0
        if ty >= self.target.top:
            self.pos = 0.0, ty  # (30.0) How do you get windows titlebar height
        else:
            self.pos = 0, 30

        print "setup pos " + str(self.pos)

        win.bind(on_resize=self._update_dock_mode)

    def _update_dock_mode(self, win, *largs):
        #ty = win.height - ((self.height * self.scale) - 30.0)
        #ty = win.height - (self.height * self.scale) - 30.0
        ty = win.height - self.height - 30.0
        if ty >= self.target.top:
            self.pos = 0.0, ty  # top
        else:
            self.pos = 0, 30 #botton
        print "update pos " + str(self.pos)
        print "update scale " + str(self.scale)


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
        scale = win.width / float(self.width)
        self.scale = scale
        Logger.info("vtest: setup scale " + str(scale))
        ty = win.height - (self.height * self.scale) - 30.0
        if ty >= self.target.top:
            self.pos = 0.0, ty
        else:
            self.pos = 0, 30

        print "setup pos " + str(self.pos)

        win.bind(on_resize=self._update_dock_mode)

    def _update_dock_mode(self, win, *largs):
        ty = win.height - (self.height * self.scale) - 30.0
#        ty = win.height - self.height - 30.0
        if ty >= self.target.top:
            self.pos = 0.0, win.height - self.height - 30.0
        else:
            self.pos = 0, 30
        print "setup pos " + str(self.pos)


class MyTextInput(TextInput):
    def __init__(self, **kwargs):
        super(MyTextInput, self).__init__(**kwargs)
        self.wx = self.x
        self.wy = self.y
        self.wpos = self.pos


    def on_focus(self, instance, value, *largs):
        win = self.get_root_window()

        if win:
            win.release_all_keyboards()
            win._keyboards = {}

            Logger.info("vtest: input type " + str(value))

            if value: #User focus; use special keyboard
                if self.input_type == 'number':
                    win.set_vkeyboard_class(MyVKeyboardNumeric)
                else:
                    win.set_vkeyboard_class(MyVKeyboardQwerty)

                print "VKeyboard true:", win._vkeyboard_cls, VKeyboard.layout_path
            else: #User defocus; switch back to standard keyboard
                win.set_vkeyboard_class(VKeyboard)
                print "VKeyboard false:", win._vkeyboard_cls, VKeyboard.layout_path


##########

class vtest(App):

    def build(self):
        Logger = clsLog()

        Builder.load_string(kv)

        self.approot = BoxLayout(orientation='vertical')
        self.keyboard_mode = Config.get("kivy", "keyboard_mode")

        Logger.info("vtest: keyboardmode " + str(self.keyboard_mode))
        b1 = BoxLayout(orientation='horizontal')
        t11 = MyTextInput(text="mode is " + self.keyboard_mode)
        b1.add_widget(t11)
        t12 = MyTextInput()
        b1.add_widget(t12)
        t13 = MyTextInput(text="12", input_type='number', input_filter='int')
        b1.add_widget(t13)

        b2 = BoxLayout(orientation='horizontal')
        t21 = MyTextInput()
        b2.add_widget(t21)
        t22 = MyTextInput()
        b2.add_widget(t22)
        t23 = MyTextInput()
        b2.add_widget(t23)

        b3 = BoxLayout(orientation='horizontal')
        t31 = MyTextInput()
        b3.add_widget(t31)
        t32 = MyTextInput()
        b3.add_widget(t32)
        t33 = MyTextInput()
        b3.add_widget(t33)

        b4 = BoxLayout(orientation='horizontal')
        t41 = MyTextInput()
        b4.add_widget(t41)
        t42 = MyTextInput()
        b4.add_widget(t42)
        t43 = MyTextInput()
        b4.add_widget(t43)

        b5 = BoxLayout(orientation='horizontal')
        t51 = MyTextInput()
        b5.add_widget(t51)
        t52 = MyTextInput()
        b5.add_widget(t52)
        t53 = MyTextInput()
        b5.add_widget(t53)

        b6 = BoxLayout(orientation='horizontal')
        t61 = MyTextInput()
        b6.add_widget(t61)
        t62 = MyTextInput()
        b6.add_widget(t62)
        t63 = MyTextInput(text="12", input_type='number', input_filter='float')
        b6.add_widget(t63)

        b7 = BoxLayout(orientation='horizontal')
        t71 = MyTextInput()
        b7.add_widget(t71)
        t72 = MyTextInput()
        b7.add_widget(t72)
        t73 = MyTextInput(input_type='number')
        b7.add_widget(t73)

        self.approot.add_widget(b1)
        self.approot.add_widget(b2)
        self.approot.add_widget(b3)
        self.approot.add_widget(b4)
        self.approot.add_widget(b5)
        self.approot.add_widget(b6)
        self.approot.add_widget(b7)


        return self.approot



if __name__ == "__main__":
    VKeyboard.docked = True
    vtest().run()


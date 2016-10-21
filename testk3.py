from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window


kv = '''
FloatLayout:
    TextInput:
        id: text_input
        pos_hint: {'top': 1}
        size_hint: 1, None
        height: 32
    ToggleButton:
        text: 'dock'
        on_state: app.switch(self)
        size_hint: 1, None
        top: text_input.y
'''


class MyApp(App):
    def build(self):
        return Builder.load_string(kv)

    def switch(self, button):
        if button.state == 'down':
            Window.allow_vkeyboard = True
            Window.single_vkeyboard = True
            Window.docked_vkeyboard = True
            print "activated dock"
        else:
            Window.allow_vkeyboard = False
            Window.single_vkeyboard = True
            Window.docked_vkeyboard = False
            print "unactivated dock"


MyApp().run()
from kivy.app import App
from kivy.lang import Builder

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.settings import SettingsWithSidebar
from settingsjson import settings_json
import json


class CRVSettingsaaaaa(App):
    def press(self, instance):
        self.open_settings()

#     def build(self):
#         b = BoxLayout()
#         self.settings_cls = SettingsWithSidebar
#         self.use_kivy_settings = True
#         setting = self.config.get('example', 'boolexample')
#
#         b.add_widget(Button(text='click', on_press=self.press))
#
#         return b
#
#     def build_config(self, config):
#         config.setdefaults('example', {
#             'boolexample': True,
#             'numericexample': 10,
#             'optionsexample': 'option2',
#             'stringexample': 'some_string',
#             'pathexample': '/some/path'})
#
#     def build_settings(self, settings):
#         settings.add_json_panel('Panel Name',
#                                 self.config,
#                                 data=settings_json)
#
#     def on_config_change(self, config, section,
#                          key, value):
#         print config, section, key, value
#
#
# CRVSettings().run()

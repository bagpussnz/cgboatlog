import kivy
kivy.require('1.9.0')
from kivy.app import App
from kivy.config import Config
from kivy.config import ConfigParser
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.settings import Settings
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.graphics import Color, Rectangle, Canvas, Line
from kivy.properties import ListProperty
from kivy.logger import Logger
from os.path import join 
from kivy.uix.settings import SettingsWithTabbedPanel
from settingsjson import settings_json
from tideinfo import CRVTideInfo
import json
import os
import datetime
import time
import re
import csv

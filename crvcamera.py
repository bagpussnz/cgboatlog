import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen

 
class CrvCamera(Screen):
    cam = None
    camwidget = None

    def view(self):
        self.cam.play = True         # Start the camera

    # Function to take a screenshot
    @staticmethod
    def doscreenshot(*largs):
        try:
            Window.screenshot(name='screenshot%(counter)04d.jpg')
            rstat = True
        except:
            rstat = False
        return rstat

    def dotoggle(self, instance):
        if instance.text == 'Stop Camera':
            self.cam.play = False
            instance.text = 'Start Camera'
        else:
            self.cam.play = True
            instance.text = 'Stop Camera'
        
    def create(self):
        smcamera = Screen(name='screen_crvcamera')
        try:
            self.camwidget = BoxLayout()

            self.cam = Camera()        # Get the camera
            self.cam = Camera(resolution=(640, 480), size=(500, 500))
        
            button1 = Button(text='Snap', size_hint=(0.12, 0.12))
            button1.bind(on_press=self.doscreenshot)
            button2 = Button(text='Stop Camera', size_hint=(0.12, 0.12))
            button2.bind(on_press=self.dotoggle)
            self.camwidget.add_widget(button1)    # Add button to Camera Widget
            self.camwidget.add_widget(button2)    # Add button to Camera Widget
            self.camwidget.add_widget(self.cam)
            smcamera.add_widget(self.camwidget)
        except:
            rstat = False

        return smcamera

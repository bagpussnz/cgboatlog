__author__ = 'ian.collins'
from kivy.logger import Logger
import time
import datetime

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


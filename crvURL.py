__author__ = 'ian.collins'

import threading
import os
from kivy.network.urlrequest import UrlRequest

class CrvURL:
    def __init__(self, indata):
        self.data = indata
        self.sourceurl = ''
        self.destfile = ''
        self.estimatedsize = 0

        self.working = 0   # 0=not working; 1=working; -1=error
        self.rbytes = 0
        self.cumrbytes = 0

        self.dspact = None
        self.abutton = None
        self.ian = "check git"

    #def set_property(value, *largs):
    #    self.data.getobject('upddisppb').value = value

    def on_success(self, req, result, *args):
        try:
            s = str(result).replace("\r", "")
            self.fp.write(s)
            self.fp.close()
            self.dspact('Retrieved tide information', 'green')
        except:
            self.data.Logger.info('URL: exception writing tide data')

    def on_progress(self, req, result, *args):
        self.data.Logger.info("CRV: url progress " + str(result))
        try:
            self.rbytes += len(result)
            self.cumrbytes += len(result)
            if self.cumrbytes > 1000:
                self.dspact('', progressval=self.rbytes)  # update progressbar
                self.cumrbytes = 0
        except:
            self.data.Logger.info('URL: exception progress')

    def on_failure(self, req, result, *args):
        self.fp = None
        try:
            os.remove(self.destfile)
        except:
            self.data.Logger.info("URL: FAILED to remove " + self.destfile)
            self.dspact('Error getting tide information', 'red')

        self.data.Logger.info("URL: FAILED to get " + self.destfile + ". Error " + result)

    def getfile(self, inurl, infile, inestimatedsize, indspaction, abutton):
        self.sourceurl = inurl
        self.destfile = infile
        self.estimatedsize = inestimatedsize
        self.dspact = indspaction
        self.abutton = abutton

        try:
            self.fp = open(self.destfile,'w')
            self.data.Logger.info("URL: Opened " + self.destfile)
        except:
            self.data.Logger.info("URL: FAILED to open " + self.destfile)
            self.fp = None
            return False

        self.working = 1
        UrlRequest(self.sourceurl, on_success=self.on_success, on_progress=self.on_progress,
                   on_failure=self.on_failure)
        return True




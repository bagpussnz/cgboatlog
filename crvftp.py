__author__ = 'ian.collins'

import threading
import localftp

class CrvFtp:
    def __init__(self, indata, inhost, inuser, inpass):
        self.data = indata
        self.linzhost = inhost
        self.linzuser = inuser
        self.linzpass = inpass

        # self.ftp = ftplib.FTP()
        self.ftp = localftp.FTP()
        self.connected = False

        self.ftpsourcefile = ''
        self.ftpdestfile = ''

        self.working = 0   # 0=not working; 1=working; -1=error
        self.rbytes = 0
        self.cumrbytes = 0

        self.dspact = None
        self.abutton = None

    #def set_property(value, *largs):
    #    self.data.getobject('upddisppb').value = value

    def connect(self):
        if self.connected:
            self.data.Logger.info("FTP: Alreaady connected")
        else:
            try:
                self.ftp.connect(self.linzhost,port=21,timeout=10)
                self.ftp.login(self.linzuser, self.linzpass)
                self.connected = True
                self.data.Logger.info("FTP:Connected to ftp host")
            except:
                self.data.Logger.info("FTP:Connect: Failed to connect to " + self.linzhost)
                self.connected = False

        return self.connected

    def getsize(self, filename):
        sz = 0
        if self.connected:
            try:
                self.ftp.sendcmd("TYPE i")
                sz = self.ftp.size(filename)
            except:
                sz = -1
        return sz

    def getfile(self, fromfile, tofile, indspaction, abutton):
        '''
        Get a file.

        As this is a blocking function has to be threaded to allow the kivy clock to continue
        '''
        self.ftpsourcefile = fromfile
        self.ftpdestfile = tofile
        self.dspact = indspaction
        self.abutton = abutton
        ret = False
        try:
            self.fp = open(self.ftpdestfile,'w')
            self.data.Logger.info("FTP: Opened " + self.ftpdestfile)
            ret = True
        except:
            self.data.Logger.info("FTP: FAILED to open " + self.ftpdestfile)
            self.fp = None

        if self.connected and self.fp is not None:
            self.working = 1
            ret = self.doretrlines()
        return ret

    def doretrlines(self):
        try:
            self.data.Logger.info('FTP (thread): retrieve')
            self.abutton.disabled = True
            self.data.Logger.info('FTP (thread): retrieve1')
            self.ftp.retrlines("RETR " + self.ftpsourcefile, callback = self.ftpprogress)
            ret = True
        except:
            self.data.Logger.info("FTP: Exception raised getting file")
            ret = False

        try:
            self.fp.close()

            if ret:
                self.data.Logger.info('FTP: Completed getfile')
                self.dspact('Completed retrieval', progressval=-2) # set it to max
            else:
                self.dspact('Error getting tide information', 'red')

        except:
            pass

        if self.abutton is not None:
            self.abutton.disabled = False
            self.working = False

        return ret

    def ftpprogress(self, dt):
        try:
            #self.data.Logger.info('FTP: in progress')
            #Clock.tick()
            self.fp.write(dt+'\n')

            self.rbytes += len(dt)
            self.cumrbytes += len(dt)
            # self.data.Logger.info('FTP: in progress3')
            if self.cumrbytes > 1000:
                #self.data.Logger.debug('FTP: rbytes ' + str(self.rbytes))
                self.dspact('', progressval=self.rbytes) # update progressbar
                self.cumrbytes = 0
        except:
            self.data.Logger.info('FTP: exception ftpprogress')

        #self.data.Logger.info('FTP: out progress')


    def nlst(self):
        tnlst = []

        if self.connected:
            try:
                tnlst = self.ftp.nlst()
            except:
                self.data.Logger.info("FTP:Failed to get nlst")
        return tnlst

    def quit(self):
        if self.connected:
            try:
                self.ftp.quit()
            except:
                pass
            self.connected = False



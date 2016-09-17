__author__ = 'ian.collins'

import time

class CrvProfile:
    disable = False
    '''
    Simple profiler
    '''
    def __init__(self, inlogger, s):
        if not self.disable:
            self.Logger = inlogger
            self.mess = s
            self.pstart = int(round(time.time() * 1000))

    def eprof(self):
        if not self.disable:
            pend = int(round(time.time() * 1000))
            pend -= self.pstart

            self.Logger.debug('CRV: PROF: ' + self.mess + ' ' + str(pend) + ' ms')


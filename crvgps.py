__author__ = 'ian.collins'

from kivy.utils import platform
from kivy.properties import StringProperty
from kivy.clock import Clock, mainthread

from math import radians, cos, sin, asin, sqrt
import re

class CrvGPS:
    #gps_location = StringProperty()
    #gps_status = StringProperty()

    def __init__(self, inLogger):
        self.Logger = inLogger

        self.gps_location = ''
        self.gps_status = ''
        self.gps_speed = 0

        self.isstarted = False

        if platform == 'android':
            from plyer import gps
            self.Logger.info('CRV:ANDROID: import gps')
            self.gps = gps
        else:
            #self.gps_location = 'testlattest:testlontest'
            self.gps_location = '036 54.583S:174 55.616E'   # simulation
            self.gps_status = ''
            self.gps = None

        if self.gps:
            try:
                self.gps.configure(on_location=self.on_location, on_status=self.on_status)

                self.startgps()

            except NotImplementedError:
                import traceback
                traceback.print_exc()
                self.gps_status = 'GPS is not implemented for your platform'

    def stopgps(self):
        if self.isstarted:
            try:
                self.Logger.info('CRV:ANDROID: trying to stop gps')
                self.gps.stop()
                self.isstarted = False
            except:
                pass
        else:
            self.Logger.info('CRV:ANDROID: gps already stopped')

    def startgps(self):
        if not self.isstarted:
            try:
                self.Logger.info('CRV:ANDROID: trying to start gps')
                self.gps.start()
                self.isstarted = True
            except:
                pass
        else:
            self.Logger.info('CRV:ANDROID: gps already started')

    @mainthread
    def on_location(self, **kwargs):
        # Nice description of decimal places in gps locations (we are using 3)....

        # The sign tells us whether we are north or south, east or west on the globe.
        # A nonzero hundreds digit tells us we're using longitude, not latitude!
        # The tens digit gives a position to about 1,000 kilometers.
        #    It gives us useful information about what continent or ocean we are on.
        # The units digit (one decimal degree) gives a position up to 111 kilometers (60 nautical miles, about 69 miles).
        # The first decimal place is worth up to 11.1 km
        # The second decimal place is worth up to 1.1 km
        # The third decimal place is worth up to 110 m
        # The fourth decimal place is worth up to 11 m
        # The fifth decimal place is worth up to 1.1 m
        # The sixth decimal place is worth up to 0.11 m
        # The seventh decimal place is worth up to 11 mm
        # The eighth decimal place is worth up to 1.1 mm
        # The ninth decimal place is worth up to 110 microns

        self.gps_location = ''

        try:
            self.Logger.debug('CRV:GPS:on_location1..' + str(kwargs))
            glat = kwargs['lat']
            if glat < 0.0: glat = abs(glat)
            # will be in format: 36.234
            # convert it to 36 54.234
            sglat = self.decdeg2dm(glat) + 'S'
            #glat = str(format(glat, '.3f')) + 'S'
            glon = kwargs['lon']
            sglon = self.decdeg2dm(glon) + 'E'
            #glon = str(format(glon, '.3f')) + 'E'
            self.gps_location = sglat + ':' + sglon

            self.gps_speed = kwargs['speed']

            self.Logger.debug('CRV:GPS:on_location..' + self.gps_location)
        except:
            self.Logger.info('CRV:GPS:on_location..EXCEPTION')

    @mainthread
    def on_status(self, stype, status):
        try:
            self.Logger.info('CRV:GPS:on_status1..' + str(stype) + ',' + str(status))
            #self.gps_status = 'type={}\n{}'.format(stype, status)
        except:
            self.Logger.info('CRV:GPS:on_status..EXCEPTION')

    def decdeg2dm(self, dd):
        '''
        Convert decimal degrees to degrees decimal minutes
        '''
        dd = abs(dd)
        minutes,seconds = divmod(dd*3600,60)
        degrees,minutes = divmod(minutes,60)
        minutes = float(minutes) + float(seconds)/60.0
        loc = str(int(degrees)).zfill(3) + ' ' + str(format(minutes, '.3f'))
        return loc

    def dm2decdeg(self, latlong):
        """
        latlong is ddd mm.dddS ddd mm.dddE
        e.g.       036 22.234S 174 33.456E

        Convert to decimal degrees:
        036 22 .234*60  174 33 .456*60
        036 + 22/60 + (.234*60)/3600   174 + 33/60 + (.456*60)/3600
        """
        latlong2 = re.findall('(\d+) (\d+)\.(\d+)..(\d+) (\d+)\.(\d+).', latlong)

        latdd = int(latlong2[0][0]) + (float(latlong2[0][1])/60.0) + int(float(latlong2[0][2])/3600.0)
        londd = int(latlong2[0][3]) + (float(latlong2[0][4])/60.0) + int(float(latlong2[0][5])/3600.0)

        return latdd, londd

    def gpsdistance(self, gpsfrom, gpsto):
        try:
            latddfrom, londdfrom = self.dm2decdeg(gpsfrom)
            latddto, londdto = self.dm2decdeg(gpsto)

            nm = self.haversine(londdfrom, latddfrom, londdto, latddto)
        except:
            nm = 0.0

        return nm

    def haversine(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        nm = 3437.905 * c
        #km = 6367 * c
        #nm = 0.539957 * km
        return nm
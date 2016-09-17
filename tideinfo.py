import kivy
from kivy.app import App
import csv
import os
from os.path import join, isfile
from datetime import date, time, datetime

import math

class Tides:
   def __init__(self):
       self.tidefile=''
       self.readok = True
       self.rawtides = []
       self.tideplot=[]       # contains points suitable for graph
       self.nowplot=[]       # contains points suitable for graph
       self.tides=[]
       self.nextlow=[0,0]
       self.nexthigh=[0,0]
       self.epoch = datetime(1970,1,1)
       self.epochhours = 0
       self.epochtimenow = None
       self.tideheightnow = 0
       self.maxheight = 0
       self.tidestations = []
       self.tidestation = ''

   def datehours(self, dt):
       delta_time = (dt - self.epoch).total_seconds()/3600
       return delta_time

   def dechours(self, yr, mn, d, t):
       """
       convert time to decimal hours
       """
       dt = datetime(int(yr), int(mn), int(d))
       if self.epochhours == 0:
           self.epochhours = self.datehours(dt)

       e = self.datehours(dt)
       result=-1.0
       if len(t) > 0:
           (h, m) = t.split(':')
           fh = float(h)
           fm = float(m)
           r = fh + fm/60.0
           result = e + round(r, 2)

       # print "dechours: " + str(result) + " yr=" + str(yr) + " mn=" + str(mn) + " d=" + str(d) + " " + t
       return result

   def dedechours(self, tm):
       """
       convert decimal hours back to time
       """
       pass

   def convert_decimal_to_time(self, decimal):
       """
       Converts decimal time to displayable time: e.g. 03:14
       (this program is not actually interested in seconds, so just round)
       """
       values_in_seconds = [('days', 60*60*24), ('hours', 60*60), ('minutes', 60), ('seconds', 1)]
       output_dict = {}
       num_seconds = int(decimal * 3600)
       for unit, worth in values_in_seconds:
           output_dict[unit] = num_seconds // worth
           num_seconds = num_seconds % worth

       if output_dict['seconds'] >  30:
           output_dict['seconds'] = 0
           output_dict['minutes'] += 1
       if output_dict['minutes'] == 59:
           output_dict['minutes'] = 0
           output_dict['hours'] += 1
       if output_dict['hours'] == 23:
           output_dict['hours'] = 0
           output_dict['days'] += 1

       fmt = str(output_dict['hours']).rjust(2, '0') + ':' + str(output_dict['minutes']).rjust(2, '0')

       return output_dict, fmt

   def setport(self, port):
       self.tidefile = port

       ex = os.path.isfile(self.tidefile)

       return ex

   def readport(self):
        if self.tidefile != '':
            try:
                with open(self.tidefile, 'rb') as csvfile:
                    intides = csv.reader(csvfile)
                    self.rawtides = list(intides)
                csvfile.close()
                self.readok = True

            except IOError as e:
                print "Failed to read csv({0}): {1}".format(e.errno, e.strerror)
                print "Failed to read csv " + self.tidefile

        return self.readok

   def tideheight(self, timetofindheightat, timeofprevioustide, timeofnexttide, heightofprevioustide, heightofnexttide):

        A = math.pi * ( ( timetofindheightat - timeofprevioustide ) / ( timeofnexttide - timeofprevioustide ) + 1 )

        height = heightofprevioustide + (heightofnexttide - heightofprevioustide) * ((math.cos(A) +1 ) / 2)

        return height

   def gettides(self, ndays=3):

        if self.readok:
            count = -1
            #
            d = int(datetime.now().strftime("%d"))
            m = int(datetime.now().strftime("%m"))
            y = int(datetime.now().strftime("%Y"))
            ddate = date(y, m, d)

            timenow = datetime.now().strftime("%H:%M")
            self.epochtimenow = self.dechours(y, m, d, timenow)

            doneit = False
            for n in self.rawtides:
                # print n
                count += 1
                if count > 2:
                    dm = int (n[0])
                    mn = int (n[2])
                    yr = int (n[3])

                    dmdate = date(yr, mn, dm)

                    delta = dmdate - ddate
                    deltadays = delta.days
                    doit = False
                    if deltadays >= 0:
                        doit = True
                        if ndays > 0:
                            if deltadays >= ndays:
                                doit = False
                                if doneit:
                                    break   # already done what we want

                    if doit:
                        decimalhours = self.dechours(yr, mn, dm, n[4])
                        if decimalhours > 0:
                            self.tides.append([ decimalhours, float(n[5])])
                        decimalhours = self.dechours(yr, mn, dm, n[6])
                        if decimalhours > 0:
                            self.tides.append([ decimalhours, float(n[7])])
                        decimalhours = self.dechours(yr, mn, dm, n[8])
                        if decimalhours > 0:
                            self.tides.append([ decimalhours, float(n[9])])
                        decimalhours = self.dechours(yr, mn, dm, n[10])
                        if decimalhours > 0:
                            self.tides.append([ decimalhours, float(n[11])])

        # create tide plot points  - iteration one every 15 minutes
        #granularity = .25   # 15 minutes is .25 of an hour
        granularity = 1.0   # every hour

        """
        data.tides.tides is a list of tides and heights 
        we plot each tide as is and then calculate iterations between those known tides.
        The number of iterations is t(n+1)-t(n) / granularity

        We dont want to deal with the first and last tide - as they are fixed
        """
#        e = self.data.tides.epochhours    # hours to subtract from epoch decimal hours
        e = 0

        self.maxheight = 0
        maxcount = len(self.tides)
        count = 0
        ok = True
        while ok:

            if count >= maxcount:
                break
            if count == 0 or count >= maxcount - 1:      # at first or last element

                self.tideplot.append((self.tides[count][0]-e, self.tides[count][1]))  # the actual tides

            else:

                niter = int((self.tides[count+1][0] - self.tides[count][0]) / granularity)
                t = self.tides[count-1][0]

                t1 = self.tides[count-1][0]
                h1 = self.tides[count-1][1]
                t2 = self.tides[count][0]
                h2 = self.tides[count][1]

                if t1 < self.epochtimenow < t2:  # if now is between the tides
                    # nexthigh and nextlow will be converted below and added to the self.nexthigh[0] and
                    # self.nextlow[0] (as displayable strings)

                    nexthigh = t2
                    self.nexthigh[1] = h2
                    nextlow = self.tides[count+1][0]
                    self.nextlow[1] = self.tides[count+1][1]
                    if self.nexthigh[1] < self.nextlow[1]:
                        nextlow  = t2
                        self.nextlow[1]  = self.tides[count][1]
                        nexthigh = self.tides[count+1][0]
                        self.nexthigh[1] = self.tides[count+1][1]
                    nexthigh -= self.epochhours
                    nextlow -= self.epochhours

                    junk, fmt = self.convert_decimal_to_time(nexthigh)
                    self.nexthigh[0] = fmt
                    junk, fmt = self.convert_decimal_to_time(nextlow)
                    self.nextlow[0] = fmt

                    if len(self.nowplot) == 0:
                        self.nowplot.append((self.epochtimenow-e, 0))
                        self.tideheightnow = self.tideheight(self.epochtimenow, t1, t2, h1, h2)


                for p in range(niter):

                    t += granularity
                    h = self.tideheight(t, t1, t2, h1, h2)

                    self.tideplot.append((t-e, h))
                    self.maxheight = max(self.maxheight, h)

                self.tideplot.append((self.tides[count][0]-e, self.tides[count][1]))  # the actual tides

            count += 1

        return count


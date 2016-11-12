__author__ = 'ian.collins'

import kivy
kivy.require('1.9.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.bubble import Bubble
#from kivy.logger import Logger
#from tideinfo import CRVTideInfo
from tideinfo import Tides
from crvemail import CrvEmail
from crvprofile import CrvProfile
from crvMessage import MessageBox

import modglobal

import os
import datetime
import sys, traceback
import shelve
#import ftplib
import localftp
import csv
import json
import threading
import httplib

#
# ==================================================================
# CLASS... crvData
# ==================================================================
#
class CrvData:
    #datawidget = {}
    #enablecamera = False

    fromopenlog = ''

    statusbarclocktime = False  # every second
    statusbarclockupd = False   # every 15 seconds
    statusbarclocknet = False   # every 30 seconds
    statusbarclockspaused = False

    dirappdata = 'appdata'
    dirtmp = 'tmp'
    dirarchive = 'archive'

    shelf_file = ''
    shelf_fd = None
    shelf_restored_files = []

    # logActive = False    # set when a log is fully opened - controls what widgets are available
    openingLog = False   # set when a log is being opened - so no data saves happen during initialisation
    # haveopenedlog = False

    displayaction = None
    audit = None

    currentlog = []

    def __init__(self, inLogger, inColor, inmessagebox, parentapp=None):
        self.Logger = inLogger
        self.crvcolor = inColor
        self.messagebox = inmessagebox
        self.sendemail = CrvEmail(self.Logger)
        self.tides = Tides()

        # the main screen manager... inoocuously called sm - used mainly by parent.
        self.sm = None
        self.showkivy = False
        self.doemaillog = False

        self.emaillog = ''
        self.emailtraining = ''
        self.emailcrew = ''
        self.datadir = ''
        self.enginetype = ''

        self.vesseltypes = []
        self.vesseltypesdoneread = False

        self.fromopenlog = ''

        self.statusbarclocktime = False  # every second
        self.statusbarclockupd = False   # every 15 seconds
        self.statusbarclocknet = False   # every 30 seconds
        self.statusbarclockspaused = False

        self.Logger.info("CRV: Data: Init")

        #
        # =============
        # Instantiate instance of clsRecord
        #
        # This is used to get/set values of operational/boatlog
        self.datarecord = CrvOpdata(self)

        self.logrecord = CrvLogdata(self)

        if parentapp is not None:
            self.thisapp = parentapp

        self.availcgunits = []
        self.availtidestations = []

        self.linzhost = "linzfile.linz.govt.nz"
        self.linzuser = "NZ_Coastguard"
        self.linzpass = "galitireerne73"

        self.allvessels = []
        self.vesseldoneread = False
        self.vesselname = ''
        self.currvessel = None
        self.cnzvessel = False

        self.tidefile = ''
        self.lastscreen = ''

        # list of crew values.
        self.crewvalues = []

        # this is the crew entries before the save crew button is clicked. They then get copied to crewlist
        self.unsavedcrew = {'name': None, 'IMSAFE': None}

        # the list of selected crew (as widgets).
        self.crewlist = []

        # the complete list of crew as read from file - format
        # type, firstname, lastname, id
        # where type is 'c' or 's' (crew or skipper)

        self.completecrewlist = []

        self.mincrew = 0
        self.maxcrew = 0

        # a list of all indexes we want to shelve for persistence. Note: only for boat log - not incidents.
        # These have their own save
        self.shelf_keys = []
        append = self.shelf_keys.append
        for key in self.datarecord.oprecord.keys():
            #self.Logger.debug("KEY: " + str(key))
            if self.datarecord.oprecord[key]['shelf'] == 1 and self.datarecord.oprecord[key]['logtype'] == 'boat':
                append(key)
        self.shelf_keys.sort()
        #self.Logger.info('CRV: shelf keys...')
        #self.Logger.info('CRV..' + str(self.shelf_keys))

    def setrecordvalues(self):
        """
        Save required record values for persistence
        Doesnt do save - just builds dictionary to save.
        If nothing has changed return False - else True

        It has a number of stages. ...
        1. process self.record and put items to save in self.values
        2. process self.logvalues (not sure what needs to be done here yet
        ...
        n. return a dict containing,

        { 'record': vales, 'log': values }
        """
        toreturn = {}

        # done like this as each key can throw an exception on error and at least we get some saved
        # (instead of losing all after the exception)

        setrec = self.datarecord.setrecordsinglevalue
        for key in self.shelf_keys:
            self.Logger.debug('CRV:'+key)
            setrec(key)

        toreturn['RECORD'] = self.datarecord.values

        # done record bit. now logvalues
        toreturn['LOG'] = self.logrecord.logvalues

        # save crew
        toreturn['CREW'] = self.crewvalues

        return toreturn

    def setsinglelogvalue(self, row, values):
        """
        Save the text in the log and shelve it to disk.
        """
        if not self.openingLog:
            if values[0] != 'Time':   # dont save header
                if row != 0:
                    if row == -1:
                        self.logrecord.logvalues.append(values)
                    else:
                        self.logrecord.logvalues[row-1] = values

                if row >= 0:
                   self.shelf_save_current()

    def setsinglecrewvalue(self, row, invalues, oldcrew=[]):
        """
        Save the text in the log and shelve it to disk.
        If oldcrew is not [] then delete oldcrew from the crewvalues list
        (this happens when an existing crew item is changed)
        """
        if not self.openingLog:
            if invalues[0] != 'Name' and invalues[1] != 'IMSAFE':   # dont save header
                if len(oldcrew) > 0:
                    todel=-1
                    cnt = 0
                    for c in self.crewvalues:
                        if c[0] == oldcrew[0]:
                            todel = cnt
                            break
                        cnt += 1
                    if todel >= 0:
                        del self.crewvalues[todel]


                values = ['', '']
                values[0] = invalues[0]
                if invalues[1]:
                    values[1] = 'true'
                else:
                    values[1] = 'false'

                if row != 0:
                    if row == -1:
                        self.crewvalues.append(values)
                    else:
                        self.crewvalues[row-1] = values

                if row >= 0:
                   self.shelf_save_current()

    def read_engineinfo(self):
        ret = False
        lines = []
        file = os.path.join(self.datadir, 'engineinfo.txt')
        try:
            with open(file) as f:
                lines = f.read().splitlines()
            f.close()

            self.Logger.info('CRV: Read engine info file ' + file)
            ret = True
        except IOError as e:
            self.Logger.info("CRV: read_engineinfo Failed to read engine info file".format(e.errno, e.strerror))

        if ret:
            try:
                setobj = self.datarecord.setobjecttext
                for e in lines:
                    [everb, evalue] = e.split('!', 2)
                    if everb in self.datarecord.oprecord:
                        # see save_engineinfo for the values written.
                        # also see openlog.
                        #self.datarecord.setobjecttext(everb, evalue)
                        setobj(everb, evalue)
                    else:
                        ok = False

            except:
                ok = False
                self.Logger.info('CRV: read_engineinfo: failed to restore data')

        return ret

    def readvesseltypes(self):
        """
        Look for file vesseltypes.txt
        If it exists, then read into self.vesseltypes

        This list is dynamic - new vessels are appended, sorted and
        saved. This is used in an incident for a vesseltype dropdown.

        We always have a predefined list as well
        """

        if self.vesseltypesdoneread:
            return
        self.vesseltypesdoneread = True

        self.vesseltypes = ['Bayliner', 'Beneteau', 'New Senator', 'Bertram', 'Bluefin', 'Bucanneer', 'Carver',
                            'Dinghy', 'Farr', 'Fi Glass', 'Four Winns', 'Fyran', 'Haines', 'Huntsman',
                            'Jetki', 'Kayak', 'McLay', 'Other', 'Pelin', 'Power', 'Rayglass', 'Stabicraft', 'Yacht']

        v = []
        afile = os.path.join(self.datadir, 'vesseltypes.txt')
        try:
            with open(afile) as f:
                v = f.read().splitlines()
            f.close()

            self.Logger.info('CRV: Read vesseltypes file ' + afile)
        except IOError as e:
            self.Logger.info("CRV: Failed to read vesseltypes.txt".format(e.errno, e.strerror))

        if len(v) > 0:
            self.vesseltypes += v

        self.vesseltypes.sort()

    def savevesseltypes(self):
        if len(self.vesseltypes) > 0:
            afile = os.path.join(self.data.datadir, 'vesseltypes.txt')
            try:
                with open(afile, 'w') as f:
                    for l in self.vesseltypes:
                        if len(l) > 0:
                            f.write(l + '\n')
                f.close()

                self.Logger.info('CRV: Wrote vesseltypes file ' + afile)
            except IOError as e:
                self.Logger.info("CRV: Failed to write vesseltypes.txt".format(e.errno, e.strerror))
                
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def to_number(self, s):
        try:
            return float(s)
        except:
            return 0.0

    def dopopup(self, mess, bindto=None):
        if bindto is not None:
            if modglobal.lastdopopup is not None:
                if modglobal.lastdopopup == bindto:
                    modglobal.lastdopopup = None
                    self.Logger.debug('CRV:Ignore popup')
                    return
            modglobal.lastdopopup = bindto

        content = Button(text='Dismiss')
        popup = Popup(title=mess, content=content, auto_dismiss=True, size_hint=(None, None), size=(400, 100))
        content.bind(on_press=popup.dismiss)
        popup.open()
        #if bindto is not None: bindto.focus = True

    def doparsedatetime(self, tstr):
        rdt = None
        if tstr is not None:
            try:
                rdt = datetime.datetime.strptime(tstr, "%a %y-%m-%d %H:%M")
            except:
                self.Logger.info('CRV: parse time.. invalid time format ' + tstr)
                rdt = None
        return rdt

    def settimeonobject(self, instance, value):
        instance.text = self.getnow()

    def getnow(self, inusedatetime=None, retlist=False, forfile=False, ddir=None, prefix=None, ext=None):
        # return string from datetime
        ret = ''
        if inusedatetime is not None:
            try:
                usedatetime = datetime.datetime.strptime(inusedatetime, '%a %d-%m-%y %H:%M')
            except:
                return  ''
        else:
            usedatetime = datetime.datetime.now()

        try:
            if forfile:
                if prefix is None:
                    tmpitis = usedatetime.strftime('%y%m%d-%H%M')
                else:
                    tmpitis = prefix + usedatetime.strftime('%y%m%d-%H%M')

                if ext is not None:
                    tmpitis += ext

                if ddir is not None:
                    d = os.path.join(self.datadir, ddir)
                else:
                    d = self.datadir

                itis = os.path.join(d, tmpitis)
                retlist = False
            else:
                itis = usedatetime.strftime('%a %d-%m-%y %H:%M')
            if retlist:
                [dow, dt, tm] = itis.split(' ', 3)
                ret = [itis, dow, dt, tm]
        except:
            self.Logger.info('CRV: getnow.. invalid datetime')
            ret = ['', '', '', '']
            itis = ''

        if retlist:
            return ret
        else:
            return itis

    def openhints(self, parent, dh, clickevent):
        self.Logger.debug('CRV: openhints')
        try:
            modglobal.statusbar.clear_widgets()
            if modglobal.altstatusbarbox is None:
                modglobal.altstatusbarbox = BoxLayout(orientation='horizontal')
            modglobal.statusbar.add_widget(modglobal.altstatusbarbox)

            modglobal.alstatusbarparent = parent
            modglobal.altstatusbarbox.clear_widgets()
            d = sorted(set(dh),key=dh.index)

            for v in d:
                modglobal.altstatusbarbox.add_widget(Button(text=v,
                                                on_release=lambda dbtn: clickevent(dbtn.text)))
#                                                on_release=lambda dbtn: self.hintpress(dbtn.text)))

        except:
            self.Logger.info('CRV:drop statusbar exception:openhints')

    def closehints(self):
        self.Logger.debug('CRV: closehints')
        try:
            if modglobal.altstatusbarbox is not None:
                modglobal.altstatusbarbox.clear_widgets()
            if modglobal.statusbarbox is not None:
                modglobal.statusbar.clear_widgets()
                modglobal.statusbar.add_widget(modglobal.statusbarbox)
            modglobal.alstatusbarclick = ''
            modglobal.alstatusbarparent = None
        except:
            self.Logger.info('CRV:drop statusbar exception:closehints')

    def save_engineinfo(self):
        # save the required engine info for the next run.
        # e.g. fuelatend becomes fuelstart

        file = os.path.join(self.datadir, 'engineinfo.txt')

        try:
            self.dorename(False, file)

            lines = []
            fuelstart = self.str2float(self.datarecord.getobjecttext('fuelstart'))
            fuelend = self.str2float(self.datarecord.getobjecttext('fuelatend'))
            if int(fuelend) < 0:
                if int(fuelstart) < 0: fuelstart = 0
                fuelend = fuelstart
            else:
                pass

            if int(fuelend) > 0:
                fuelstart = fuelend
                lines.append('fuelstart!' + str(fuelstart) + '\n')

            portstart = self.str2float(self.datarecord.getobjecttext('portehoursstart'))
            portfin = self.str2float(self.datarecord.getobjecttext('portehoursfin'))

            if int(portfin) < 0:
                if int(portstart) < 0: portstart = 0
                portfin = portstart

            if int(portfin) > 0:
                portstart = portfin
                lines.append('portehoursstart!' + str(portstart) + '\n')

            sbstart = self.str2float(self.datarecord.getobjecttext('sbehoursstart'))
            sbfin = self.str2float(self.datarecord.getobjecttext('sbehoursfin'))

            if int(sbfin) < 0:
                if int(sbstart) < 0: sbstart = 0
                sbfin = sbstart

            if int(sbfin) > 0:
                sbstart = sbfin
                lines.append('sbehoursstart!' + str(sbstart) + '\n')

            with open(file, 'w') as f:
                f.writelines(lines)
                f.close()

                self.Logger.info('CRV: save_engineinfo: Wrote engine info ' + file)
        except IOError as e:
            self.dorename(True, file)

            self.Logger.info('CRV: save_engineinfo: Failed to write exgine info..'.format(e.errno, e.strerror))

    def dotides(self, parent):
        crvcp = CrvProfile(self.Logger, 'dotides')
        # try to read tides from port
        t = self.gettidestation()
        if len(t) > 0 and len(self.tides.tides) == 0:
            yr = datetime.datetime.now().strftime('%Y')
            t = t + yr + '.csv'
            #self.datadir = self.user_data_dir
            self.tidefile = os.path.join(self.datadir, t)

            ok = self.tides.setport(self.tidefile)
            if not ok:  # no tide file - try to retrieve
                parent.crv_callback_requpdatetides(True)
            ok = self.tides.readport()
            if ok:
                count = self.tides.gettides(2)  # get 2 days of tides (should softcode this)
        crvcp.eprof()
    #
    # initialise data
    def openlog(self, boatlog, crew):
        self.Logger.info('CRV: data: openlog')
        self.openingLog = True

        inshelf, dumm, dumm2 = self.shelf_restore()
        # it wont necessarily use this timestamp - it depends on whether we are
        # recovering a log - in whih case we'll use the log time.

        tmstamp = self.getnow()
        renginfo =  self.read_engineinfo()

        # default for email sent status is UNSENT
        # Values for this are in [ 'NONET', 'MAILERROR', 'UNSENT' ] or a time (the sent time!).
        self.datarecord.setobjectvariable('emailtime', 'text', 'UNSENT')

        # dont set the 'screen' variable yet - its a bit soon - just set the data
        self.datarecord.setobjectvariable('screen', 'text', 'screen_main')

        # 'butactivity' shelved - but handled in callback
        self.datarecord.setobjectcheck('closingchecks', False)
        self.datarecord.setobjecttext('closingtime', '')
        # 'closing' shelved - but handled in callback
        # 'closelogbutton' shelved - but handled in callback
        #self.datarecord.setobjecttext('currenttype', '')

        self.datarecord.setobjecttext('cloudcover', '')
        # 'crewlistsendcheck' ??
        self.datarecord.setobjectvariable('crewlistsent', 'bool', False)
        self.datarecord.setobjectcheck('crewmeetsops', False)

        self.datarecord.setobjecttext('fueladded', '')
        self.datarecord.setobjecttext('fuelatend', '')
        self.datarecord.setobjecttext('fuelfin', '')
        if not renginfo: self.datarecord.setobjecttext('fuelstart', '')
        self.datarecord.setobjecttext('fuelused', '0')

        self.datarecord.setobjecttext('fuelsuppliedadded', '')
        self.datarecord.setobjecttext('fuelsuppliedprice', '')
        self.datarecord.setobjecttext('fuelsuppliedstart', '')
        self.datarecord.setobjecttext('fuelsuppliedtype', '')

        # 'homeboatlog' ??
        self.datarecord.setobjecttext('initialreason', '')
        # this may need to be at top. ??
        self.datarecord.setobjectvariable('logactive', 'bool', False)
        # 'logarchive' ??
        # 'managecrew' ??
        # 'newlog' ??
        #self.datarecord.setobjecttext('nowcasting', 0)

        self.datarecord.setobjectcheck('plcaerials', False)
        self.datarecord.setobjectcheck('plcbatteries', False)
        self.datarecord.setobjectcheck('plcbowsternlines', False)
        self.datarecord.setobjectcheck('plcbriefing', False)
        self.datarecord.setobjectcheck('plccoverdown', False)
        self.datarecord.setobjecttext('plcdefaerials', '')
        self.datarecord.setobjecttext('plcdefbatteries', '')
        self.datarecord.setobjecttext('plcdefbowsternlines', '')
        self.datarecord.setobjecttext('plcdefbriefing', '')
        self.datarecord.setobjecttext('plcdefcoverdown', '')
        self.datarecord.setobjecttext('plcdefdehumidifier', '')
        self.datarecord.setobjecttext('plcdefflushvalves', '')
        self.datarecord.setobjecttext('plcdeffronthatch', '')
        self.datarecord.setobjecttext('plcdefnavcheck', '')
        self.datarecord.setobjecttext('plcdefnavlights', '')
        self.datarecord.setobjecttext('plcdefnavunits', '')
        self.datarecord.setobjecttext('plcdefoilandwater', '')
        self.datarecord.setobjecttext('plcdefpersonal', '')
        self.datarecord.setobjecttext('plcdefpumplocker', '')
        self.datarecord.setobjecttext('plcdefradioson', '')
        self.datarecord.setobjecttext('plcdefshorepower', '')
        self.datarecord.setobjecttext('plcdeftransomhatches', '')
        self.datarecord.setobjecttext('plcdefvisual', '')
        self.datarecord.setobjectcheck('plcdehumidifier', False)
        self.datarecord.setobjectcheck('plcflushvalves', False)
        self.datarecord.setobjectcheck('plcfronthatch', False)
        self.datarecord.setobjectcheck('plcnavcheck', False)
        self.datarecord.setobjectcheck('plcnavlights', False)
        self.datarecord.setobjectcheck('plcnavunits', False)
        self.datarecord.setobjectcheck('plcoilandwater', False)
        self.datarecord.setobjectcheck('plcpersonal', False)
        self.datarecord.setobjectcheck('plcpumplocker', False)
        self.datarecord.setobjectcheck('plcradioson', False)
        self.datarecord.setobjectcheck('plcshorepower', False)
        self.datarecord.setobjectcheck('plctransomhatches', False)
        self.datarecord.setobjectcheck('plcvisual', False)

        self.datarecord.setobjectcheck('pltchocks', False)
        self.datarecord.setobjectcheck('pltconnected', False)
        self.datarecord.setobjectcheck('pltlockpin', False)
        self.datarecord.setobjecttext('pltdefchocks', '')
        self.datarecord.setobjecttext('pltdefconnected', '')
        self.datarecord.setobjecttext('pltdeflockpin', '')

        if not renginfo: self.datarecord.setobjecttext('portehoursstart', '')
        self.datarecord.setobjecttext('portehoursfin', '')
        self.datarecord.setobjecttext('portehoursdur', '')

        self.datarecord.setobjectcheck('prelaunch', False)

        self.datarecord.setobjectcheck('recbatteries', False)
        self.datarecord.setobjectcheck('recbilge', False)
        self.datarecord.setobjectcheck('reccleaned', False)

        self.datarecord.setobjecttext('reccompletedby', '')

        self.datarecord.setobjectcheck('reccover', False)
        self.datarecord.setobjectcheck('recdamage', False)
        self.datarecord.setobjectcheck('recdehumidifier', False)
        self.datarecord.setobjectcheck('recengineoil', False)
        self.datarecord.setobjectcheck('recflushed', False)
        self.datarecord.setobjectcheck('recfuel', False)
        self.datarecord.setobjectcheck('recfuelreset', False)
        self.datarecord.setobjectcheck('rechandhelds', False)
        self.datarecord.setobjectcheck('recpfds', False)
        self.datarecord.setobjectcheck('recprovs', False)
        self.datarecord.setobjectcheck('recpump', False)
        self.datarecord.setobjectcheck('recpumpcover', False)
        self.datarecord.setobjectcheck('recpumpfuel', False)
        self.datarecord.setobjectcheck('recready', False)
        self.datarecord.setobjectcheck('recsandtrap', False)
        self.datarecord.setobjectcheck('recshorepower', False)

        self.datarecord.setobjecttext('recsignature', '')
        self.datarecord.setobjecttext('recsigned', '')

        self.datarecord.setobjectcheck('recstowgear', False)
        self.datarecord.setobjectcheck('recstowropes', False)
        self.datarecord.setobjectcheck('recsuits', False)

        self.datarecord.setobjecttext('rectimeout', '')

        self.datarecord.setobjectcheck('rectubes', False)
        self.datarecord.setobjectcheck('recwashed', False)
        self.datarecord.setobjectcheck('recwindscreen', False)

        self.datarecord.setobjecttext('recdefbatteries', '')
        self.datarecord.setobjecttext('recdefbilge', '')
        self.datarecord.setobjecttext('recdefcleaned', '')
        self.datarecord.setobjecttext('recdefcover', '')
        self.datarecord.setobjecttext('recdefdamage', '')
        self.datarecord.setobjecttext('recdefdehumidifier', '')
        self.datarecord.setobjecttext('recdefengineoil', '')
        self.datarecord.setobjecttext('recdefflushed', '')
        self.datarecord.setobjecttext('recdeffuel', '')
        self.datarecord.setobjecttext('recdeffuelreset', '')
        self.datarecord.setobjecttext('recdefhandhelds', '')
        self.datarecord.setobjecttext('recdefpfds', '')
        self.datarecord.setobjecttext('recdefprovs', '')
        self.datarecord.setobjecttext('recdefpump', '')
        self.datarecord.setobjecttext('recdefpumpcover', '')
        self.datarecord.setobjecttext('recdefpumpfuel', '')
        self.datarecord.setobjecttext('recdefready', '')
        self.datarecord.setobjecttext('recdefsandtrap', '')
        self.datarecord.setobjecttext('recdefshorepower', '')
        self.datarecord.setobjecttext('recdefstowgear', '')
        self.datarecord.setobjecttext('recdefstowropes', '')
        self.datarecord.setobjecttext('recdefsuits', '')
        self.datarecord.setobjecttext('recdeftubes', '')
        self.datarecord.setobjecttext('recdefwashed', '')
        self.datarecord.setobjecttext('recdefwindscreen', '')

        if not renginfo: self.datarecord.setobjecttext('sbehoursstart', '')
        self.datarecord.setobjecttext('sbehoursfin', '')
        self.datarecord.setobjecttext('sbehoursdur', '')

        self.datarecord.setobjecttext('savedinc0', '')
        self.datarecord.setobjecttext('savedinc1', '')
        self.datarecord.setobjecttext('savedinc2', '')
        self.datarecord.setobjecttext('savedinc3', '')
        self.datarecord.setobjecttext('savedinc4', '')
        self.datarecord.setobjecttext('savedinc5', '')
        self.datarecord.setobjecttext('savedinc6', '')
        self.datarecord.setobjecttext('savedinc7', '')
        self.datarecord.setobjecttext('savedinc8', '')
        self.datarecord.setobjecttext('savedinc9', '')

        self.datarecord.setobjecttext('sentinc0', 'UNSENT')
        self.datarecord.setobjecttext('sentinc1', 'UNSENT')
        self.datarecord.setobjecttext('sentinc2', 'UNSENT')
        self.datarecord.setobjecttext('sentinc3', 'UNSENT')
        self.datarecord.setobjecttext('sentinc4', 'UNSENT')
        self.datarecord.setobjecttext('sentinc5', 'UNSENT')
        self.datarecord.setobjecttext('sentinc6', 'UNSENT')
        self.datarecord.setobjecttext('sentinc7', 'UNSENT')
        self.datarecord.setobjecttext('sentinc8', 'UNSENT')
        self.datarecord.setobjecttext('sentinc9', 'UNSENT')

        if not renginfo: self.datarecord.setobjecttext('sbehoursstart', '')
        self.datarecord.setobjecttext('sbehoursfin', '')
        self.datarecord.setobjecttext('sbehoursdur', '')

        # 'screen' ??

        self.datarecord.setobjecttext('seastate', '')

        # 'settingshead' ??

        self.datarecord.setobjectcrew('skipper', '', False)

        if self.tides.nexthigh is not None:
            self.datarecord.setobjecttext('tidehighheight', self.tides.nexthigh[1])
            self.datarecord.setobjecttext('tidehightime', self.tides.nexthigh[0])

        self.datarecord.setobjecttext('tidelowtime', self.tides.nextlow[0])
        self.datarecord.setobjecttext('tidelowheight', self.tides.nextlow[1])

        # This is the boatlog start time
        # If recovering a log - we recover the saved time.

        self.datarecord.setobjectvariable('time', 'text', tmstamp)

        self.datarecord.setobjectcrew('tractorin', '', False)
        self.datarecord.setobjectcrew('tractorout', '', False)

        self.datarecord.setobjectcheck('vesseloperational', False)

        self.datarecord.setobjecttext('visibility', '')
        self.datarecord.setobjecttext('wind', '')
        self.datarecord.setobjecttext('winddirection', '')

        self.clearcurrentlog(True)

        boatlog.log_grid_recover()
        crew.crew_grid_recover()

        self.openingLog = False

        # see if log is active (from recover)

        l = self.getlogactive()
        self.datarecord.haveopenedlog = True

        return l

    def resetlog(self):
        # We no longer need this. Archive the shelf_file
        # if its there
        self.shelf_archive()
        # unset log time
        self.datarecord.setobjectvariable('time', 'text', '')
        w = self.datarecord.getobject('homeoperational')
        w.text = 'Open Log'
        self.setlogactive(False)

    def retrylogsend(self):
        """
        Try to send old unset logs - dont attempt if no network
        """
        if not self.have_internet():
            return

        # For each archived boat log
        flist = []
        for afile in os.listdir(self.datadir):
             if afile.startswith('LOG') and afile.endswith('.JSON'):
                 flist.append(afile)

        flist.sort()
        self.Logger.info('CRV: Logs to send ' + str(len(flist)))
        n = 0
        for afile in flist:
            thefile = os.path.join(self.datadir, afile)
            (ok, tcrew, tlog, topdata) = self.shelf_extract(thefile)
            if ok:
                self.Logger.debug('CRV: ================')
                self.Logger.info('CRV: Process (' + str(n) + ') and Send ' + afile)
                ok = self.formatlogs(tlog, topdata)
                if ok:
                    d = os.path.join(self.datadir, 'archive')
                    tofile = os.path.join(d, 'SENT'+afile)
                    self.Logger.info('CRV: Email rename ' + thefile + ' to ' + tofile)
                    try:
                        os.rename(thefile, tofile)
                    except:
                        self.Logger.info('CRV: FAILED TO RENAME ' + thefile + ' to ' + tofile)
                n += 1
            else:
                pass
        pass

    def ensuredir(self, inpath):
        ok = True
        path = os.path.join(self.datadir, inpath)
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                ok = False
        return ok

    def formatlogs(self, theboatlog, inoplog):
        # The boat log is the boat or activity log
        # The values is the operational log

        theoplog = []
        theoplog.append(inoplog)

        # This will be the filename for the operational log and boatlog
        try:
            tmstamp = theoplog[0]['time']
            if len(tmstamp) == 0:
                return False
        except:
            return False

        # Process and format the incident files.
        # On completion, these will be saved in the list below.
        theincidents = []
        for inc in range(10):
            v = 'savedinc' + str(inc)
            savedincfile = theoplog[0][v]
            if len(savedincfile) > 0:
                try:
                    inf = open(savedincfile)
                    incinfo = json.load(inf)
                    ununicoded = dict([(str(k), str(v)) for k, v in incinfo['INCIDENT'].items()])
                    t = []
                    t.append(ununicoded)  # convertjsonttocsv requires a list of dict
                    theincidents.append(t)
                    inf.close()
                except:
                    self.Logger.info('CRV:SENDING INCIDENT: Unable to format incident {} in file {}'.format(inc, savedincfile))
                    return False

        # We now have a number of lists to email off.

        # The operational log in theoplog
        # The boatlog in theboatlog
        # The crewlog in thecrewlog
        # up to 10 incidents in theincidents[n]

        # a list of atatchments to send.
        allattach = []

        #1. Send the operational, boatlog, crewlog and all incidents to the emaillog address.
        try:
            optmpfile = self.getnow(inusedatetime=tmstamp, forfile=True, ddir='tmp', prefix='oplog', ext='.csv')
            ok = self.convertjsontocsv(theoplog, optmpfile)
            if ok:
                allattach.append(optmpfile)
                self.Logger.debug('CRV: closelog.. add attach ' + optmpfile)
            else:
                return False
        except:
            self.Logger.info('CRV: closelog.. cannot format the operation log.')
            return False

        # The boat log is of format,
        # 0:...
        # 1:...
        # 2:...
        # 3:...
        # 4: key=value,[key=value,...]
        # We need to extract those keys..
        if len(theboatlog) > 0:
            try:
                allkeys = []
                #append = allkeys.append

                # this is reading static data from the record definition
                for n in self.logrecord.logrecord.keys():
                    r = self.logrecord.logrecord[n]
                    if r.has_key('key'):
                        #allkeys.append(self.logrecord.logrecord[n]['key'])
                        allkeys.append(r['key'])
                allkeys = list(set(allkeys))
                allkeys.sort()

                # Now we can create a dictionary with those keys for
                # each logrecord element 4.
                # 0:time, 1:type, 2:location, 3:helm, 4:nav  - 5:log
                for p, k in enumerate(theboatlog):
                    bl4 = k[5]
                    del k[5]
                    for l in allkeys:
                        k[l] = ''
                    # there will be an 'info' key not stored in global record
                    # (this is used for an information message from an incident)
                    k['info'] = ''
                    k['time'] = k[0]
                    del k[0]
                    k['type'] = k[1]
                    del k[1]
                    k['loc'] = k[2]
                    del k[2]
                    k['helm'] = k[3]
                    del k[3]
                    k['nav'] = k[4]
                    del k[4]
                    if bl4 != '':
                        for x in bl4.split(';'):
                            n = x.split('=')
                            try:
                                k[n[0]] = n[1]
                            except:
                                self.Logger.info('CRV: closelog.. cannot enumerate boatlog keys. ')
                                return False

            except:
                self.Logger.info('CRV: closelog.. cannot format boatlog keys. ')
                return False

            try:
                bttmpfile = self.getnow(inusedatetime=tmstamp, forfile=True, ddir='tmp', prefix='boatlog', ext='.csv')
                ok = self.convertjsontocsv(theboatlog, bttmpfile)
                if ok:
                    allattach.append(bttmpfile)
                    self.Logger.debug('CRV: closelog.. add attach ' + bttmpfile)
                else:
                    self.Logger.debug('CRV: closelog.. cannot convert boatlog ' + bttmpfile)
                    return False

            except:
                self.Logger.info('CRV: closelog.. cannot format the boatlog log.')
                return False

        for inc in range(10):
            if inc >= len(theincidents):
                break
            else:
                try:
                    # maybe this should be named based on incident start
                    inctmpfile = self.getnow(forfile=True, ddir='tmp', prefix='inc' + str(inc) + '-', ext='.csv')
                    #inct = 'inc' + str(inc) + '-' + datetime.datetime.now().strftime('%y-%m-%d-%H-%M.csv')
                    #inctmpfile = os.path.join(self.datadir, inct)
                    ok = self.convertjsontocsv(theincidents[inc], inctmpfile)
                    if ok:
                        allattach.append(inctmpfile)
                    else:
                        self.Logger.debug('CRV: closelog.. cannot convert incident ' + inctmpfile)
                        return False

                    self.Logger.debug('CRV: closelog.. add attach ' + inctmpfile)
                except:
                    self.Logger.info('CRV: closelog.. cannot format the incident log ' + str(inc))

        emailaddress = self.getemaillog()

        # # email the archive file
        sentok, value = self.sendboatlog(emailaddress, allattach)
        if not sentok:
            self.Logger.info('CRV: closelog.. cannot send boatlog')
            return False

        #
        # if sentok:
        #     #theoplog[0]['emailtime'] = value
        #     inoplog.record['emailtime'] = value
        #     for inc in range(10):
        #         if inc < len(theincidents):
        #             inoplog.record['sentinc'+str(inc)] = value

        emailtrainingaddress = self.getemailtraining()

        if emailtrainingaddress is not None and len(theboatlog) > 0:
            #emailtrainingaddress = ''  # temp
            if len(emailtrainingaddress) > 0:
                if emailtrainingaddress != emailaddress:
                    # extract just training logs from boatlog
                    # and send to the emailtrainingaddress
                    traininglog=[]
                    for t in theboatlog:
                        if t['type'] == 'Training':
                            traininglog.append(t)

                    if len(traininglog) > 0:
                        trainattach = []
                        try:
                            bttmpfile = self.getnow(forfile=True, ddir='tmp', prefix='train', ext='.csv')
                            #bttmpfile = os.path.join(self.datadir, datetime.datetime.now().strftime('train%y-%m-%d-%H-%M.csv'))
                            ok = self.convertjsontocsv(traininglog, bttmpfile)
                            if ok: trainattach.append(bttmpfile)
                        except:
                            self.Logger.info('CRV: closelog.. cannot format the training boatlog log.')
                            return False

                        sentok, value = self.sendboatlog(emailtrainingaddress, trainattach)
                        if not sentok:
                            self.Logger.info('CRV: closelog.. cannot send traininglog')
                            return False

        return True

    # def formatandsendlog(self, theboatlog, inoplog):
    #     # The boat log is the boat or activity log
    #     # The values is the operational log
    #
    #     theoplog = []
    #     theoplog.append(inoplog.values)
    #
    #     # This will be the filename for the operational log and boatlog
    #     try:
    #         #tmstamp = theoplog[0]['time']
    #         tmstamp = theoplog[0]['time']
    #     except:
    #         tmstamp = self.getnow()
    #
    #     # Process and format the incident files.
    #     # On completion, these will be saved in the list below.
    #     theincidents = []
    #     for inc in range(10):
    #         v = 'savedinc' + str(inc)
    #         savedincfile = theoplog[0][v]
    #         #savedincfile = self.datarecord.getobjectvariable(v, 'text', '', inoplog.record)
    #         if len(savedincfile) > 0:
    #             try:
    #                 inf = open(savedincfile)
    #                 incinfo = json.load(inf)
    #                 ununicoded = dict([(str(k), str(v)) for k, v in incinfo['INCIDENT'].items()])
    #                 t = []
    #                 t.append(ununicoded)  # convertjsonttocsv requires a list of dict
    #                 theincidents.append(t)
    #                 inf.close()
    #             except:
    #                 self.Logger.info('CRV:SENDING INCIDENT: Unable to send incident {} in file {}'.format(inc, savedincfile))
    #
    #     # We now have a number of lists to email off.
    #
    #     # The operational log in theoplog
    #     # The boatlog in theboatlog
    #     # The crewlog in thecrewlog
    #     # up to 10 incidents in theincidents[n]
    #
    #     # a list of atatchments to send.
    #     allattach = []
    #
    #     #1. Send the operational, boatlog, crewlog and all incidents to the emaillog address.
    #     try:
    #         optmpfile = self.getnow(inusedatetime=tmstamp, forfile=True, prefix='oplog', ext='.csv')
    #         #optmpfile = os.path.join(self.datadir, datetime.datetime.now().strftime('oplog%y-%m-%d-%H-%M.csv'))
    #         ok = self.convertjsontocsv(theoplog, optmpfile)
    #         if ok:
    #             allattach.append(optmpfile)
    #             self.Logger.debug('CRV: closelog.. add attach ' + optmpfile)
    #
    #     except:
    #         self.Logger.info('CRV: closelog.. cannot format the operation log. Not sent')
    #
    #     # The boat log is of format,
    #     # 0:...
    #     # 1:...
    #     # 2:...
    #     # 3:...
    #     # 4: key=value,[key=value,...]
    #     # We need to extract those keys..
    #     try:
    #         allkeys = []
    #         append = allkeys.append
    #
    #         # this is reading static data from the record definition
    #         for n in self.logrecord.logrecord.keys():
    #             r = self.logrecord[n]
    #             if r.has_key('key'):
    #                 #allkeys.append(self.logrecord.logrecord[n]['key'])
    #                 append(r['key'])
    #         allkeys = list(set(allkeys))
    #         allkeys.sort()
    #
    #         # Now we can create a dictionary with those keys for
    #         # each logrecord element 4.
    #         #
    #         for p, k in enumerate(theboatlog.logvalues):
    #             bl4 = k[4]
    #             del k[4]
    #             for l in allkeys:
    #                 k[l] = ''
    #             # there will be an 'info' key not stored in global record
    #             # (this is used for an information message from an incident)
    #             k['info'] = ''
    #             k['time'] = k[0]
    #             del k[0]
    #             k['type'] = k[1]
    #             del k[1]
    #             k['from'] = k[2]
    #             del k[2]
    #             k['to'] = k[3]
    #             del k[3]
    #             if bl4 != '':
    #                 for x in bl4.split(';'):
    #                     n = x.split('=')
    #                     try:
    #                         k[n[0]] = n[1]
    #                     except:
    #                         pass
    #
    #     except:
    #         self.Logger.info('CRV: closelog.. cannot format boatlog keys. ')
    #
    #     try:
    #         bttmpfile = self.getnow(inusedatetime=tmstamp, forfile=True, prefix='boatlog', ext='.csv')
    #         #bttmpfile = os.path.join(self.datadir, datetime.datetime.now().strftime('boatlog%y-%m-%d-%H-%M.csv'))
    #         ok = self.convertjsontocsv(theboatlog.logvalues, bttmpfile)
    #         if ok:
    #             allattach.append(bttmpfile)
    #             self.Logger.debug('CRV: closelog.. add attach ' + bttmpfile)
    #     except:
    #         self.Logger.info('CRV: closelog.. cannot format the boatlog log. Not sent')
    #
    #     for inc in range(10):
    #         if inc >= len(theincidents):
    #             break
    #         else:
    #             try:
    #                 # maybe this should be named based on incident start
    #                 inctmpfile = self.getnow(forfile=True, prefix='inc' + str(inc) + '-', ext='.csv')
    #                 #inct = 'inc' + str(inc) + '-' + datetime.datetime.now().strftime('%y-%m-%d-%H-%M.csv')
    #                 #inctmpfile = os.path.join(self.datadir, inct)
    #                 ok = self.convertjsontocsv(theincidents[inc], inctmpfile)
    #                 if ok:
    #                     allattach.append(inctmpfile)
    #                 self.Logger.debug('CRV: closelog.. add attach ' + inctmpfile)
    #             except:
    #                 self.Logger.info('CRV: closelog.. cannot format the incident log. Not sent ' + str(inc))
    #
    #     emailaddress = self.getemaillog()
    #
    #     # email the archive file
    #     sentok, value = self.sendboatlog(emailaddress, allattach)
    #
    #     if sentok:
    #         #theoplog[0]['emailtime'] = value
    #         inoplog.record['emailtime'] = value
    #         for inc in range(10):
    #             if inc < len(theincidents):
    #                 inoplog.record['sentinc'+str(inc)] = value
    #
    #     emailtrainingaddress = self.getemailtraining()
    #     if emailtrainingaddress is not None:
    #         #emailtrainingaddress = ''  # temp
    #         if len(emailtrainingaddress) > 0:
    #             if emailtrainingaddress != emailaddress:
    #                 # extract just training logs from boatlog
    #                 # and send to the emailtrainingaddress
    #                 traininglog=[]
    #                 for t in theboatlog.logvalues:
    #                     if t[1] == 'Training':
    #                         traininglog.append(t)
    #
    #                 if len(traininglog) > 0:
    #                     trainattach = []
    #                     try:
    #                         bttmpfile = self.getnow(forfile=True, prefix='train', ext='.csv')
    #                         #bttmpfile = os.path.join(self.datadir, datetime.datetime.now().strftime('train%y-%m-%d-%H-%M.csv'))
    #                         ok = self.convertjsontocsv(traininglog, bttmpfile)
    #                         if ok: trainattach.append(bttmpfile)
    #                     except:
    #                         self.Logger.info('CRV: closelog.. cannot format the training boatlog log. Not sent')
    #
    #                     sentok, value = self.sendboatlog(emailtrainingaddress, trainattach)
    #
    #     return

    def email_process_oplog(self, thelog):
        pass

    def email_process_boatlog(self, thelog):
        pass

    def email_process_crelog(self, thelog):
        pass

    def email_process_inclog(self, thelog):
        pass

    def shelf_archive(self):
        archivefile = ''
        if 'CURRENTLOG.JSON' in self.shelf_file:
            archivefile = self.getnow(forfile=True, prefix='LOG', ext='.JSON')
            #archivefile = os.path.join(self.datadir, datetime.datetime.now().strftime('LOG%y%m-%d-%H-%M.JSON'))

            self.shelf_save_current()

            ok = self.dorename(False, self.shelf_file, archivefile)
            if ok:
                self.Logger.info('CRV: Archived log to ' + archivefile)
            else:
                self.Logger.info('CRV: Failed to archive file ' + self.shelf_file + ' ' + archivefile)
                archivefile = None
            self.shelf_delete()
        return archivefile

    def shelf_save_current(self):
        """
        saves CURRENT log and info to disk. Do not attempt to save current if it already exists.
        (you dont want to overwrite it)
        """
        doit = False

        if not self.datarecord.haveopenedlog:
            self.Logger.info('CRV: Persistance: shelf_save_current: refusing to save during initialisation')
        elif self.shelf_fd is not None:
            self.Logger.info('CRV: Persistance: shelf_save_current: already open. refusing to report')
        else:
            doit = True
            if len(self.shelf_file) == 0:
                self.shelf_file = os.path.join(self.datadir, 'CURRENTLOG.JSON')

                if os.path.exists(self.shelf_file):  # only on first check
                    doit = False
        if doit:
            try:
                # collate all the data to save
                emess = 'setrecordvalues'
                tosave = self.setrecordvalues()
                if len(tosave) > 0:
                    self.Logger.info('CRV: Persistance: save.. dumping ' + self.shelf_file)
                    emess = 'open'
                    self.shelf_fd = open(self.shelf_file, 'w')

                    # add here all keys to be saved for persistence
                    #json.dump(self.values, self.shelf_fd)
                    emess = 'dump'
                    json.dump(tosave, self.shelf_fd)
            except:
                self.Logger.info('CRV: Persistance: save.. exception (' + emess + ') ' + self.shelf_file)
                doit = False

        self.shelf_close()

        return doit

    def shelf_close(self):
        if self.shelf_fd is not None:
            self.Logger.info('CRV: Persistance: close')
            self.shelf_fd.close()
            self.shelf_fd = None

    def shelf_check(self, file=None):
        """
        Returns true if a shelf file exists - else false
        Note: if log is active, then returns false.
        """
        ret = False
        if not self.getlogactive():
            ok, dum, dum2 = self.shelf_restore(file, True)
            if ok:
                self.shelf_close()
                ret = True
        self.Logger.info("CRV: Persistance: check returns " + str(ret))
        return ret

    def shelf_extract(self, file):
        # This should be merged into shelf_restore - but not now.
        topdata = {}
        tlog = []
        tcrew = []
        ok = False

        efail = ''
        try:
            efail = 'load'
            fd = open(file)
            toget = json.load(fd)

            if toget.has_key('RECORD'):
                efail = 'RECORD'
                topdata = dict([(str(k), str(v)) for k, v in toget['RECORD'].items()])

                # The log is a dictionary and will be stored in a random order.
                # this ensures the items are recovered in the correct order.
                efail = 'LOG'
                for l in toget['LOG']:
                    d = dict([(int(str(k)), str(v)) for k, v in l.items()])
                    tlog.append(d)

                efail = 'CREW'
                for l in toget['CREW']:
                    d = [ str(l[0]), str(l[1])]
                    tcrew.append(d)

            toget.clear()
            fd.close()
            ok = True
        except:
            self.Logger.info('CRV: FAILED TO EXTRACT DATA from ' + file + ' at ' + efail)
            ok = False

        return ok, tcrew, tlog, topdata

    def shelf_restore(self, file=None, fullrestore=True):
        """
        If file is None, then look for a CURRENTLOG.JSON file (restore after a crash).
        Otherwise restore contents of specified file. In this case - no changes are allowed.
        Tries to either do a full or partial restore of a saved incident file.
        :param
        :return:
        """
        if len(self.shelf_file) == 0:
            self.shelf_file = os.path.join(self.datadir, 'CURRENTLOG.JSON')

        if file is None:
            usefile = self.shelf_file

        else:
            # usefile = os.path.join(self.datadir, file)
            usefile = file

        # only do restore once for a file (this may change if files are deleted and re-added - but in general
        alreadydone = False
        incalerttime = ''
        typeisrecord = False
        outtime = ''
        senttime = ''
        ret = False

        for srf in self.shelf_restored_files:
            if usefile in srf[0]:
                if not os.path.exists(usefile):
                    ret = False
                else:
                    ret = srf[1]
                    outtime = srf[2]
                    senttime = srf[3]
                alreadydone = True
        if not alreadydone:
            ret = False
            self.Logger.info("CRV: Persistance: restore.. check file " + usefile)
            if os.path.exists(usefile):
                #self.shelf_fd = shelve.open(usefile)
                efail = ''
                try:
                    efail = 'load'
                    self.shelf_fd = open(usefile)
                    toget = json.load(self.shelf_fd)

                    # toget is either going to have a 'RECORD' key or an 'INCIDENT' key.
                    # If 'INCIDENT' then force fullrestore to be False (it will be anyway)
                    # as this implies it's from the log archive screen and parsing all files.
                    #
                    if toget.has_key('RECORD'):
                        typeisrecord = True
                        efail = 'RECORD'
                        self.datarecord.values = dict([(str(k), str(v)) for k, v in toget['RECORD'].items()])
                        self.datarecord.valueslast = self.datarecord.values.copy()
                    elif toget.has_key('INCIDENT'):
                        typeisrecord = False
                        efail = 'INCIDENT'
                        # we are only after incalerttime
                        tmpv = dict([(str(k), str(v)) for k, v in toget['INCIDENT'].items()])
                        if tmpv.has_key('incalerttime'):
                            incalerttime = tmpv['incalerttime']

                        fullrestore = False

                    if fullrestore:

                        # The log is a dictionary and will be stored in a random order.
                        # this ensures the items are recovered in the correct order.
                        efail = 'LOG'
                        for l in toget['LOG']:
                            d = dict([(int(str(k)), str(v)) for k, v in l.items()])
                            self.logrecord.logvalues.append(d)

                        efail = 'CREW'
                        for l in toget['CREW']:
                            d = [ str(l[0]), str(l[1])]
                            self.crewvalues.append(d)

                    toget.clear()

                    ret = True
                except:
                    self.Logger.info('CRV: FAILED TO RECOVER DATA at ' + efail)
                    ret = False

                if ret:
                    if typeisrecord:
                        if self.datarecord.values.has_key('time'):
                            outtime = self.datarecord.values['time']
                        if self.datarecord.values.has_key('emailtime'):
                            senttime = self.datarecord.values['emailtime']
                    else:
                        outtime = incalerttime

                    if len(outtime) == 0:
                        self.datarecord.values['time'] = self.getnow()
                    else:
                        v = outtime
                        try:
                            [outtime,col] = v.split('!', 2)
                        except:
                            outtime = v

                else:
                    outtime = ''

                if not incalerttime:
                    self.shelf_restored_files.append([usefile, ret, outtime, senttime])

                if not fullrestore:
                    if typeisrecord:
                        # empty the arrays - we dont need them
                        self.datarecord.values.clear()
                        self.datarecord.valueslast.clear()

            self.shelf_close()
            self.Logger.info("CRV: Persistance: restore.. returns (nvalues, return value) " +
                             str(len(self.datarecord.values)) + " " + str(ret))
            if not fullrestore:
                return ret, outtime, senttime
            else:
                return ret, '', ''
        else:
            return ret, outtime, senttime

    def shelf_delete(self, file=None):
        if len(self.shelf_file) == 0:
            self.shelf_file = os.path.join(self.datadir, 'CURRENTLOG.JSON')

        if file is None:
            usefile = self.shelf_file

        else:
            usefile = file

        ret = False
        if os.path.exists(usefile):
            os.remove(usefile)
            ret = True

        if 'CURRENTLOG' in usefile:
            self.datarecord.values.clear()
            self.datarecord.valueslast.clear()
            self.logrecord.logvalues = []
            self.crewvalues = []
            self.setlogactive(False)

        todel = -1
        cnt = 0
        for f in self.shelf_restored_files:
            if usefile in f[0]:
                todel = cnt
                break
            cnt += 1
        if todel >= 0:
            del self.shelf_restored_files[todel]

        self.Logger.info("CRV: Persistance: delete.. returns " + str(usefile) + " " + str(ret))
        return ret

    def shelf_parse(self, file):
        outfile = None
        outlogtime = None
        senttime = None
        if os.path.exists(file):
            outfile = os.path.basename(file)
            (ret, outlogtime, senttime) = self.shelf_restore(file, fullrestore=False)
            self.shelf_close()
        return outfile,outlogtime, senttime

    # @staticmethod
    # def popup_callback(instance):
    #     sys.exit()

    def errormessage(self, message):
        #MessageBox(self, titleheader='INTERNAL ERROR', doexit=True, message=message)

        self.Logger.info('CRV: ERROR: ' + message)
        sys.exit(2)

    def setdisplayaction(self, d):
        if self.displayaction is None:
            self.displayaction = d

    def setlogaudit(self, a):
        if self.audit is None:
            self.audit = a

    def setlogactive(self, value):
        #self.logActive = value
        self.datarecord.setobjectvariable('logactive', 'bool', value)

    def getlogactive(self):
        l = self.datarecord.getobjectvariable('logactive', 'bool', False)
        return l

    def initcurrentlog(self):
        self.currentlog = []

    def getcurrentlog(self, row):
        if row < 0:
            return self.currentlog

        if row < len(self.currentlog):
            return self.currentlog[row]
        else:
            return None

    def setcurrentlog(self, row, index, value):
        self.currentlog[row][index].text = value

    def appendcurrentlog(self, item):
        self.currentlog.append(item)

    def clearcurrentlog(self, cleartype):
        """
        Initialise the log columns
        If cleartype is true then clear all log type columns, otherwise
        just clear current log (but leave type there)
        """

        if cleartype:
            for thisindex in self.logrecord.getloggroup('logtypes'):
                for index in self.logrecord.getloggroup(thisindex):
                    self.logrecord.setobjecttext(index, '')
            pass
        else:
            self.logrecord.setobjecttext('logtime', '')
            # note: logtype not emptied as we want to keep same logtype
            # lastdest = self.datarecord.getobjecttext('logto')
            # self.logrecord.setobjecttext('logfrom', lastdest)
            # self.logrecord.setobjecttext('logto', '')

            thislog = self.logrecord.getobjecttext('logtype')
            if thislog is None or thislog == '':
                thislog = 'Log Arrival'

            if self.logrecord.loggroup['logtypesdisp'].has_key(thislog):
                thisindex = self.logrecord.loggroup['logtypesdisp'][thislog]
                for index in self.logrecord.getloggroup(thisindex):
                    self.logrecord.setobjecttext(index, '')

    def getcolorastext(self, color):
        ret = 'black'
        for c in self.colors:
            if self.colors[c] == color:
                ret = c
        return ret

    # enable widget specified by index based on value of value. if negate is true, then switch values
    def enablewidget(self, index, value, negate):
        w = self.datarecord.getobject(index)
        if w is not None:
            if value:
                w.disabled = False
            else:
                w.disabled = True
            if negate:
                w.disabled = not w.disabled
            if w.disabled:
                w.color = self.crvcolor.getcolor('black')
            else:
                w.color = self.crvcolor.getcolor('white')

    ##########
    #RECORD PROCESSING
    ##########
    def str2bool(self, v):
        return v in ('True', 'true', True)

    def str2float(self, v):
        f = -1.0
        try:
            f = float(v)
        except:
            f = -1.0
        return f

    def getimagepath(self, imagefile):
        #return os.path.join(self.datadir, imagefile)
        return imagefile

    # -------------------

    # -------------------

    # get crew name at row of list. If row is None, then return a list of all crew names.
    def getcrewname(self, row=None):
        if row is None:

            ac = []
            r = -1
            for n in self.getallcrew():
                r += 1
                if r > 0:
                    if len(n[0].text) > 0:
                        c = self.getcrewname(r)
                        ac.append(c)
            return ac
        else:
            return self.crewlist[row][0].text

    def getcrewimsafe(self, row):
        if self.crewlist[row][1].text == 'IMSAFE':
            ret = 'true'
        else:
            ret = 'false'

        return ret

    def getcrew(self, row):
        c = ''
        i = ''
        if 0 < row < len(self.crewlist):
            c = self.crewlist[row][0].text
            if self.crewlist[row][1].text in [ 'IMSAFE', 'True', 'true']:
                #i = self.crewlist[row][1].active
                i = True
        return c, i

    def setcrew(self, row, index, value):
        if index == 0:
            self.crewlist[row][0].text = value
        elif index == 1:
            if value in [ 'True', 'true', 'IMSAFE', True]:
                self.crewlist[row][1].text = 'IMSAFE'
            else:
                self.crewlist[row][1].text = ''
        else:
            pass

    def getcurrentcrewname(self):
        return self.unsavedcrew['name'].text
        #return self.unsavedcrew['name']

    def getcurrentcrewimsafe(self):
        return self.unsavedcrew['IMSAFE'].active
        #return self.unsavedcrew['IMSAFE']

    def setcurrentcrew(self, index, value):
        if index == 'name':
            a=self.unsavedcrew['name']
            a.text = value
            #self.unsavedcrew['name'] = value
        elif index == 'IMSAFE':
            self.unsavedcrew['IMSAFE'].active = value
            #self.unsavedcrew['IMSAFE'] = value
        else:
            pass
        return True

    def setcurrentcrewobject(self, index, value):
        if index == 'name':
            self.unsavedcrew['name'] = value
        elif index == 'IMSAFE':
            self.unsavedcrew['IMSAFE'] = value
        else:
            pass

    def getallcrew(self):
        return self.crewlist

    # def getallcurrentcrew(self):
    #     return self.unsavedcrew

    def getmaxcrew(self):
        return self.maxcrew

    def getnumcrew(self):
        return len(self.crewlist)

    def appendcrew(self, item):
        self.crewlist.append(item)

    def settidestation(self, value):
        """
        Required Setting
        If value of tidestation is None or empty return False else True
        """
        ret = False
        if value is not None:
            if value != '':
                self.tides.tidestation = value
                ret = True
        return ret

    def gettidestation(self):
        return self.tides.tidestation

    def setvesselname(self, value):
        """
        Required Setting
        If value of vesselname is None or empty return False else True
        """
        ret = False
        if value is not None:
            if value != '':
                self.vesselname = value
                ret = True
        return ret

    def crv_populate_vessel(self, invesselname=None):
        self.readvessels()
        if self.allvessels is not None:
            if invesselname is not None:
                self.vesselname = invesselname

            for n in self.allvessels:
                if n[0] == self.vesselname:
                    self.currvessel = n
                    break

        return True

    def getvesselname(self):
        v = ''
        if self.vesselname is not None:
            v = self.vesselname
        return v

    def setmincrew(self, value):
        """
        Optional Setting
        The minimum nnumber of crew for an operational vessel.
        If not set, then use 2
        """
        defset = 2
        if value is not None:
            if value != '':
                defset = value
        self.mincrew = defset

        return True

    def getmincrew(self):
        return self.mincrew

    def setmaxcrew(self, value):
        """
        Optional Setting
        The maximum nnumber of crew for an operational vessel. Is this needed?
        If not set, then use 8
        """
        defset = 8
        if value is not None:
            if value != '':
                defset = value
        self.maxcrew = defset

        return True

    def getmaxcrew(self):
        return self.maxcrew

    def setenginetype(self, value):
        """
        Optional Setting
        The default type of engine. See settingsjson.py for options
        If not set, then use Jet
        """
        defset = 'Jet'
        if value is not None:
            if value != '':
                defset = value
        self.enginetype = defset

        return True

    def getenginetype(self):
        return self.enginetype

    def setshowkivy(self, value):
        """
        Optional Setting
        Whether to show kivy settings
        If not set, then use False
        """
        defset = False
        if value is not None:
            if value != '':
                defset = value
        self.showkivy = defset

        return True

    def getshowkivy(self):
        return self.showkivy

    # def setenablecamera(self, value):
    #     self.enablecamera = value
    #
    # def getenablecamera(self):
    #     return self.enablecamera
    #
    def setdatadir(self, value):
        """
        Required Setting (hardcoded by system)
        The location of the data files for program.
        """
        self.datadir = value

        self.ensuredir(self.dirtmp)
        self.ensuredir(self.dirappdata)
        self.ensuredir(self.dirarchive)

        return True

    def getdatadir(self):
        return self.datadir

    def setdoemaillog(self, value):
        """
        Optional - but default to true
        Whether to send emails
        """
        defset = True
        if value is not None:
            if value != '':
                defset = value
        self.doemaillog = defset

        return True

    def getdoemaillog(self):
        return self.doemaillog

    def setemaillog(self, value):
        """
        Required Setting
        Default email address.
        """
        ret = False
        if value is not None:
            if value != '':
                self.emaillog = value
                ret = True
        return ret

    def getemaillog(self):
        return self.emaillog

    def setemailcrew(self, value):
        """
        Optional - No default.
        Where to send crew emails to.
        """
        defset = ''
        if value is not None:
            if value != '':
                defset = value
        self.emailcrew = defset

        return True

    def getemailcrew(self):
        em = self.getemaillog()
        if self.emailcrew is not None:
            if self.emailcrew != '':
                em = self.emailcrew
        return em

    def setemailtraining(self, value):
        """
        Optional - No default.
        Where to send training emails to.
        """
        defset = ''
        if value is not None:
            if value != '':
                defset = value
        self.emailtraining = value

        return True

    def getemailtraining(self):
        return self.emailtraining

    # def gettidefile(self):
    #     return os.path.join()

    def getcgunits(self):
        """
        Look for file cgunits.txt
        If it exists, then read into self.availcgunits
        """
        if len(self.availcgunits) == 0:
            file = os.path.join(self.datadir, 'cgunits.csv')
            try:
                with open(file, 'r') as f:
                    reader = csv.reader(f)
                    cglist = list(reader)
                f.close()
                self.availcgunits = cglist

            except IOError as e:
                self.Logger.info("CRV: Failed to read cgunits.txt".format(e.errno, e.strerror))

        return self.availcgunits

    def gettidestations(self):
        """
        Look for file cgtidestations.txt
        If found use it - if not found, try to get tidestations from linz
        """
        crvpr = CrvProfile(self.Logger, 'gettidestations')
        tss = []
        ok = False
        if len(self.tides.tidestations) == 0:
            file = os.path.join(self.datadir, 'cgtidestations.csv')
            try:
                self.Logger.info('CRV: gettidestations: before open of ' + file)
                with open(file, 'r') as f:
                    reader = csv.reader(f)
                    tslist = list(reader)
                f.close()
                self.tides.tidestations = tslist
                self.Logger.info("CRV: Read tidestations from file %s", file)
                ok = True
            except (IOError, csv.Error):
                # file didnt exist, try to ftp it.
                self.Logger.info("CRV: Failed to read tidestations from file " + file)
                ok = self.settidestations(file)

        else:
            tss = self.tides.tidestations

        if ok:
            ts = []
            for n in self.tides.tidestations:
                ts.append(n[0])
            tss = list(set(ts))
            tss.sort()

        self.Logger.info('CRV: gettidestations. found ' + str(len(tss)))
        crvpr.eprof()
        return tss

    def settidestations(self, file):
        ok = True
        try:
            ftp = localftp.FTP(self.linzhost)
            ftp.login(self.linzuser, self.linzpass)

            data = []

            data = ftp.nlst()

            ftp.quit()
            self.Logger.info("CRV: Downloaded tidestations from " + self.linzhost)
        #except ftplib.all_errors:
        except localftp.all_errors:
            self.Logger.info("CRV: failed to get tidestations from " + self.linzhost)
            return False

        # example line: Ben Gunn 2017.csv
        # we want to create tidestations list with each element containing eg.
        # [ 'Ben Gunn', '2017', 'csv' ]
        self.tides.tidestations = []
        for line in data:
            station = line[:-9]
            year = line[-8:-4]
            ext = line[-3:]
            self.tides.tidestations.append([station, year, ext])

        if len(self.tides.tidestations) > 0:
            try:
                with open(file, "wb") as f:
                    writer = csv.writer(f)
                    writer.writerows(self.tides.tidestations)
                f.close()
                self.Logger.info("CRV: Wrote tidestations to file " + file)
            except csv.Error:
                ok = False


        return ok


    def sendcrewlist(self):
        self.displayaction('Send Crew List', cleargrid=True, progressmax=5, progressval=-3)
        self.sm.current = 'screen_display_update'
        ok = False
        emailaddress = ''
        try:
            emailaddress = self.getemailcrew()
            vessel=self.getvesselname()
            logtime=self.datarecord.getvalue('time')
            skipper=self.datarecord.getskippername()
            imsafe=self.datarecord.getskipperimsafe(True)
            if imsafe == 'true':
                imsafe = '(IMSAFE)'
            else:
                imsafe = ''

            crewreport = '''\
<html>
  <head></head>
  <body>
    <p>Crew List for vessel {vessel} for boatlog started at {logtime}<br><br>
       Skipper: {skipper} {imsafe}<br>
       Crew...<br>
'''.format(vessel=vessel, logtime=logtime,skipper=skipper,imsafe=imsafe)

            row = -1
            for n in self.getallcrew():
                row += 1
                if row > 0:
                    if len(n[0].text) > 0:
                        c = self.getcrewname(row)
                        i=self.getcrewimsafe(row)
                        if i == 'true':
                            i = '(IMSAFE)'
                        else:
                            i = ''
                        #i = '(IMSAFE='+str(i)+')'
                        crewreport += '''{crew} {imsafe}<br>'''.format(crew=c, imsafe=i)

            crewreport += '</p></body></html>'

            subject = "Crew List for vessel " + self.getvesselname()

            print crewreport

            # built report - now send.
            self.emailwrapper(emailaddress, subject, 'send crew list', crewreport, None)
            ok = True
        except:
            self.displayaction('Failed to send crew list (internal error)', enablebutton=True, progressval=-2)

        return ok

    def flattenjson(self, b, delim):
        val = {}
        for i in b.keys():
            if isinstance( b[i], dict ):
                get = self.flattenjson( b[i], delim )
                for j in get.keys():
                    val[ i + delim + j ] = get[j]
            else:
                val[i] = b[i]
        return val

    def convertjsontocsv(self, thelog, outfile):
        '''
        converts thelog (list) to csv - output file ends in csv - overwritten if it exists
        '''
        ok = False
        keys = None
        try:
            keys = thelog[0].keys()
        except:
            keys = None
        if keys is None:
            try:
                keys = thelog.keys()
            except:
                self.Logger.info('CRV:Convert CSV Failed on key extract. Outfile is ' + outfile)
                keys = None

        if keys is not None:
            try:
                with open(outfile, 'wb') as f:
                    w = csv.DictWriter(f, keys)
                    w.writeheader()
                    w.writerows(thelog)
                ok = True
            except:
                self.Logger.info('CRV:Convert CSV Failed on convert. Outfile is ' + outfile)
        return ok

    def sendboatlog(self, eto, allattach):
        """
        :return: boolean, value
         boolean true if sent ok
         value one of UNSENT, NONET, MAILERROR or time sent (i.e. now)
        """

        ok = False
        value = "UNSENT"

        self.displayaction('Send Boat Log', cleargrid=True, progressmax=5, progressval=-3)
        self.sm.current = 'screen_display_update'

        self.sendemail.clearattachments()
        for a in allattach:
            self.sendemail.addattachment(a)
            self.Logger.debug('CRV: sendemail.. add attach ' + a)

        emailaddress = eto
        try:
            vessel=self.getvesselname()
            logtime=self.datarecord.getvalue('time')
            skipper=self.datarecord.getskippername()
            imsafe=self.datarecord.getskipperimsafe(True)
            if imsafe == 'true':
                imsafe = '(IMSAFE)'
            else:
                imsafe = ''

            report = '''\
<html>
  <head></head>
  <body>
    <p>Boat log for vessel {vessel} for boatlog started at {logtime}<br><br>
       Skipper: {skipper} {imsafe}<br>
'''.format(vessel=vessel, logtime=logtime,skipper=skipper,imsafe=imsafe)

            subject = "Boat log for vessel " + self.getvesselname()

            #print report

            # built report - now send.

            ok  = self.emailwrapper(emailaddress, subject, 'send boat log', report)
            if not ok:
                if not self.have_internet():
                    value = "NONET"
            else:
                value = self.getnow()
        except:
            self.displayaction('Failed to send boat log (internal error)', enablebutton=True, progressval=-2)

        # if ok:
        #     # if here, then we can set the sent flag in all the attachments
        #     for a in allattach:
        #         self.Logger.debug('CRV: sendemail.. setting sent status of ' + a)

        return ok, value

#     def oldsendboatlog(self, thelog, afile):
#         # convert the list t a csv file (base of afile + .csv) and mail it.
#         # The boatlog has a few recipients
#         self.displayaction('Send Boat Log', cleargrid=True, progressmax=5, progressval=-3)
#         self.sm.current = 'screen_display_update'
#
#         if len(thelog) == 0:
#             MessageBox(self, titleheader='No log items to send',
#                        message='Please note the log email will have\n' +
#                                'no attachment as there are no logs to send.')
#
#         ok = False
#         emailaddress = ''
#         try:
#             outfile = afile.rsplit( ".", 1 )[ 0 ] + '.csv'
#             ok = self.convertjsontocsv(thelog, outfile)
#             emailaddress = self.getemaillog()
#             emailtrainingaddress = self.getemailtraining() # to be done
#             vessel=self.getvesselname()
#             logtime=self.datarecord.getvalue('time')
#             skipper=self.datarecord.getskippername()
#             imsafe=self.datarecord.getskipperimsafe(True)
#             if imsafe == 'true':
#                 imsafe = '(IMSAFE)'
#             else:
#                 imsafe = ''
#
#             report = '''\
# <html>
#   <head></head>
#   <body>
#     <p>Boat log for vessel {vessel} for boatlog started at {logtime}<br><br>
#        Skipper: {skipper} {imsafe}<br>
# '''.format(vessel=vessel, logtime=logtime,skipper=skipper,imsafe=imsafe)
#
#             subject = "Boat log for vessel " + self.getvesselname()
#
#             print report
#
#             # built report - now send.
#
#             self.emailwrapper(emailaddress, subject, 'send boat log', report, outfile)
#             ok = True
#         except:
#             self.displayaction('Failed to send boat log (internal error)', enablebutton=True, progressval=-2)
#
#         return ok

    def emailwrapper(self, eto, subject, logtitle, message, attachfile=None):

        # do not try if the network is down.

        if not self.have_internet():
            self.displayaction('Failed to send boat log (no connection to network)', enablebutton=True, progressval=-2)
            return False

        self.sendemail.eto = eto
        self.sendemail.esubject = subject
        self.sendemail.emessage = message


        if attachfile is not None:
            if attachfile != '':
                self.sendemail.attachfile = attachfile

        try:
            mythread = threading.Thread(target=self.do_sendmail)
            mythread.start()
        except:
            self.Logger.info('CRV: Unable to send email for ' + logtitle)

        return True

    def do_sendmail(self):
        ok = self.sendemail.sendemail(self.displayaction)

        if ok:
            self.displayaction('Email sent to ' + self.sendemail.eto, enablebutton=True, progressval=-2)
            self.audit.writeaudit('Email sent to ' + self.sendemail.eto)
        else:
            self.displayaction('Failed to send email to ' + self.sendemail.eto, enablebutton=True, progressval=-2)
            self.audit.writeaudit('Failed to email to ' + self.sendemail.eto)

    def have_internet(self):
        conn = httplib.HTTPConnection("www.google.com")
        try:
            conn.request("HEAD", "/")
            return True
        except:
            return False

    def readvessels(self):
        if self.vesseldoneread:
            return
        self.vesseldoneread = True

        # format of vessel file..
        # description!callsign!fuelrate!fueltype!hide!mobilephone!msanum!enginetype
        self.allvessels = []
        file = os.path.join(self.datadir, 'vessels.txt')
        try:
            with open(file) as f:
                while True:
                    aline=f.readline()
                    if not aline: break
                    line = aline.strip()
                    vlist = []
                    vlist = line.split('!', 7)
                    # vdesc = vlist[0]
                    # vcs = vlist[1]
                    # vfr = vlist[2]
                    # vft = vlist[3]
                    # vmob = vlist[4]
                    # vmsa = vlist[5]

                    if len(vlist) < 6:
                        continue  # ignore it.

                    if len(vlist) > 7:   # has enginetype
                        #vengine = vlist[6]
                        pass
                    else:                 # does not have enginetype
                        vlist.apppend('')
                        #engine = ''

                    self.allvessels.append(vlist)
            f.close()

            self.Logger.info('CRV: Read vessels file ' + file)
        except IOError as e:
            self.Logger.info("CRV:Failed to read vessels file".format(e.errno, e.strerror))

    def savevessels(self):
        if len(self.allvessels) > 0:
            file = os.path.join(self.datadir, 'vessels.txt')
            try:
                with open(file, 'w') as f:
                    for avessel in self.allvessels:
                        if len(avessel) > 0:
                            towrite = "!".join(avessel)
                            f.write(towrite + '\n')
                f.close()

                self.Logger.info('CRV: Wrote vessels file ' + file)
            except IOError as e:
                self.Logger.info("CRV: Failed to write vessels.txt".format(e.errno, e.strerror))

    def dorename(self, inreverse, inffrom, infto=None):
        # does a rename - deleting fto if it exists
        try:
            if infto is None:
                f = os.path.splitext(inffrom)[0]
                fto = f + '.bu'
                ffrom = inffrom
            else:
                ffrom = inffrom
                fto = infto

            if inreverse:
                n = fto
                fto = ffrom
                ffrom = n
            if os.path.isfile(fto):
                self.Logger.info("CRV: remove ", fto)
                os.remove(fto)
            self.Logger.info("CRV: rename ", ffrom, " ", fto)
            os.rename(ffrom, fto)
            ret = True
        except:
            ret = False
        return ret

class CrvRecord:
    def __init__(self, indata, inrecord, invalues, invalueslast):
        self.data = indata
        self.record = inrecord
        self.values = invalues
        self.valueslast = invalueslast

    def setrecordsinglevalue(self, key):
        value = None
        try:
            type = self.record[key]['type']
            # self.Logger.debug('Persistance: setrecordvalues: process key and type ' + key + " " + type)
            if type == 'checkbox':
                value = self.getobjectcheckastext(key)  # will return 'true' or 'false'
            elif type == 'label':
                value = self.getobjecttext(key)
            elif type == 'box':
                pass
            elif type == 'bool':
                value = self.getobjectvariable(key, 'bool', False)
            elif type == 'text':
                value = self.getobjectvariable(key, 'text', '')
            elif type == 'crew':
                # a crew is a name plus a checkbox
                # make value name!true|false
                o = self.record[key]['object']
                t = 'false'
                if o is not None:
                    if o[1] is not None:
                        if o[1].active:
                            t = 'true'
                    if o[0] is not None:
                        value = o[0].text + '!' + t
            else:
                value = self.getobjecttext(key)

            if value is not None:
                # we have a value for key. Populate the lists to persist
                if self.valueslast.has_key(key):
                    if value != self.valueslast[key]:
                        self.values[key] = value
                        self.valueslast[key] = value
                else:
                    #self.Logger.debug('Persistance: no last key ' + key)
                    self.values[key] = value
                    self.valueslast[key] = value

        except:
            self.Logger.info("CRV; crvdata: setsinglevalue: exception at key " + key)

        return True

    def getobjecttext(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        t = ''
        if index in inrecord:
            if inrecord[index]['object'] is not None:
                typ = type(inrecord[index]['object']).__name__
                if typ == 'list':
                    # if item 0 is a checkbox, then return active
                    if type(inrecord[index]['object'][0]).__name__ == 'CCheckBox':
                        t = inrecord[index]['object'][0].active
                        if t:
                            t = 'true'
                        else:
                            t = 'false'
                    else:
                        t = inrecord[index]['object'][0].text
                elif typ == 'SigWidget':
                    t = ''
                else:
                    t = inrecord[index]['object'].text
                if t == '':
                    t = inrecord[index]['defvalue']
        return t

    # def getobjectvariable(self, index, type, defaultvalue):
    #     t = defaultvalue
    #     if index in self.record:
    #         if type == 'text':
    #             if self.record[index]['object'] is not None:
    #                 t = self.record[index]['object'].text
    #             else:
    #                 t = str(self.record[index]['defvalue'])
    #         elif type == 'bool':
    #             t = self.data.str2bool(self.record[index]['defvalue'])
    #         else:
    #             t = str(self.record[index]['defvalue'])
    #     return t

    def getobjectvariable(self, index, type, defaultvalue, inrecord=None):
        if inrecord is None: inrecord=self.record
        t = defaultvalue
        if index in inrecord:
            if type == 'text':
                if inrecord[index]['object'] is not None:
                    t = inrecord[index]['object'].text
                else:
                    t = str(inrecord[index]['defvalue'])
            elif type == 'bool':
                t = self.data.str2bool(inrecord[index]['defvalue'])
            else:
                t = str(inrecord[index]['defvalue'])
        return t

    def getobjectcheck(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        t = None
        if index in inrecord:
            if inrecord[index]['object'] is not None:
                # a checkbox also has a label with it. hence [0]
                t = inrecord[index]['object'][0].active
        return t

    def getobjectcheckobject(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        t = None
        if index in inrecord:
            if inrecord[index]['object'] is not None:
                # a checkbox also has a label with it. hence [0]
                t = inrecord[index]['object'][0]
        return t

    def getobjectcheckastext(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        t = ''
        if index in inrecord:
            if inrecord[index]['object'] is not None:
                t = 'false'
                # a checkbox also has a label with it. hence [0]
                if inrecord[index]['object'][0].active:
                    t = 'true'

        return t

    def getvalue(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        t = ''
        if index in inrecord:
            t = inrecord[index]['defvalue']
        return t

    def getvaluekey(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        k = ''
        if index in inrecord:
            k = inrecord[index]['key']
        return k

    def getcheckboxlabel(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        o = None
        if index in inrecord:
            if inrecord[index]['object'] is not None:
                if inrecord[index]['type'] == 'checkbox':
                    o = inrecord[index]['object'][1]
        return o

    def getobject(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        if index in inrecord:
            return inrecord[index]['object']
        else:
            self.data.errormessage("GetObject: INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: getobject: INDEX DOES NOT EXIST: " + index)

    def getlabobject(self, index, inrecord=None):
        if inrecord is None: inrecord=self.record
        lobj = None
        if index in inrecord:
            if inrecord[index].has_key('labobj'):
                lobj = inrecord[index]['labobj']
        else:
            self.data.errormessage("GetObject: INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: getlabobject: INDEX DOES NOT EXIST: " + index)
        return lobj

    def setvalue(self, index, value):
        if index in self.record:
            self.record[index]['defvalue'] = value

    def setobjectcolor(self, index, colr):
        if index in self.record:
            if self.record[index]['object'] is not None:
                if self.record[index]['type'] == 'checkbox':
                    self.record[index]['object'][1].color = colr
                else:
                    self.record[index]['object'].color = colr

    def setlabobjectcolor(self, index, colr):
        if index in self.record:
            if self.record[index]['object'] is not None:
                if self.record[index].has_key('labobj'):
                    self.record[index]['labobj'].color = colr

    def setobject(self, index, obj, type):
        if index in self.record:
            if type != 'list':
                obj.id = index
            self.record[index]['object'] = obj
            self.record[index]['type'] = type
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setobject: INDEX DOES NOT EXIST: " + index)

    def setlabobject(self, index, obj):
        if index in self.record:
            if self.record[index].has_key('labobj'):
                self.record[index]['labobj'] = obj
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setlabobject: INDEX DOES NOT EXIST: " + index)

    def setobjectvariable(self, index, type, invalue):
        """
        As it says, set the value on a variable
        """
        value = invalue
        if index in self.record:
            if not self.haveopenedlog:
                if self.values is not None:
                    if self.values.has_key(index):
                        value = self.values[index]

                        v = value
                        try:
                            [value,col] = v.split('!', 2)
                        except:
                            value = v

            self.record[index]['type'] = type
            if type == 'text':
                self.record[index]['defvalue'] = str(value)
            elif type == 'bool':
                self.record[index]['defvalue'] = self.data.str2bool(value)
            else:
                self.record[index]['defvalue'] = str(value)
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setobjectvariable: INDEX DOES NOT EXIST: " + index)

    def setobjecttext(self, index, invalue):
        """
        As it says, set the text on an object.
        If the shelf file descriptor is open, then
        set the text to the shelved value
        """
        # if index == 'logtype':
        #     i = 2
        #     pass
        value = invalue
        if index in self.record:
            if not self.haveopenedlog:
                if self.values is not None:
                    if self.values.has_key(index):
                        value = self.values[index]

            if self.record[index]['object'] is not None:
                nm = type(self.record[index]['object']).__name__
                if nm == 'list':
                    if value == '' or value == 'false':
                        self.record[index]['object'][0].active = False
                    else:
                        self.record[index]['object'][0].active = True
                elif nm == 'BTextInput':
                    self.record[index]['object'].settext(str(value))
                else:
                    self.record[index]['object'].text = str(value)
            self.record[index]['defvalue'] = value
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setobjecttext: INDEX DOES NOT EXIST: " + index)

    def setobjectcheck(self, index, invalue, type='checkbox'):

        value = ''
        if index in self.record:
            if self.values is not None:
                if not self.haveopenedlog:
                    if self.values.has_key(index):
                        if self.values[index] is not None:
                            value = self.values[index]

            if value == 'true':
                vbool = True
            elif value == 'false':
                vbool = False
            else:
                vbool = invalue

            if self.record[index]['object'] is not None:
                self.record[index]['type'] = type
                self.record[index]['object'][0].active = vbool

            self.record[index]['defvalue'] = vbool
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setobjectcheck: INDEX DOES NOT EXIST: " + index)

    def setobjectlabel(self, index, invalue, incolor, type='label'):
        value = invalue
        col = incolor
        if index in self.record:
            # not sure about this - needs more digging.
            # Do we need a special case just for 'time'
            # We always want to use the saved data for the boatlog time.
            if index != 'time':
                if value == '':
                    value = self.record[index]['object'].text
            if self.values is not None:
                if not self.haveopenedlog:
                    if self.values.has_key(index):
                        if self.values[index] is not None:
                            v = self.values[index]
                            try:
                                [value,col] = v.split('!', 2)
                            except:
                                value = v

            if self.record[index]['object'] is not None:
                self.record[index]['type'] = type
                self.record[index]['object'].text = value
                c = self.crvcolor.getcolor(col)
                self.record[index]['object'].color = c

            self.record[index]['defvalue'] = value
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setobjectcheck: INDEX DOES NOT EXIST: " + index)

    def setobjectplus(self, index, obj, chld, par, type):
        """
        same as setobject - but also adds the obj widget to a parent
        """
        if index in self.record:
            chld.id = index
            self.record[index]['object'] = chld
            self.record[index]['type'] = type
            if par is not None:
                if obj is not None:
                    par.add_widget(obj)
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setobjectplus: INDEX DOES NOT EXIST: " + index)

    def setobjectlist(self, index, obj, chld, par, type):
        """
        same as setobject - but also adds the obj widget to a parent.
        Also - the child is a list, so we set the id to the first element.
        (If you can figure out how to determine a widget is a list, then this
        would be same as setobjectplus)
        """
        if index in self.record:
            chld[0].id = index
            self.record[index]['object'] = chld
            self.record[index]['type'] = type
            if par is not None:
                if obj is not None:
                    par.add_widget(obj)
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setobjectlist: INDEX DOES NOT EXIST: " + index)

    def setobjectcrew(self, index, inname, inimsafe):
        name = inname
        imsafe = inimsafe

        if index in self.record:
            if self.values is not None:
                if not self.haveopenedlog:
                    if self.values.has_key(index):
                        value = self.values[index]
                        # this will be in form name!true|false
                        [name,imsafe] = value.split('!', 2)

            if self.record[index]['object'] is not None:
                if self.record[index]['object'][0] is not None:
                    self.record[index]['object'][0].text = str(name)
                if self.record[index]['object'][1] is not None:
                    self.record[index]['object'][1].active = self.data.str2bool(imsafe)
            self.record[index]['defvalue'] = ''
        else:
            self.data.errormessage("INDEX DOES NOT EXIST: " + index)
            self.data.Logger.info("CRV: data: setobjecttext: INDEX DOES NOT EXIST: " + index)

    # functions for skipper
    # ==================
    def getskippername(self, inrecord=None):
        if inrecord is None: inrecord=self.record
        #return self.skipper[0].text
        skipper = ''
        if inrecord['skipper']['object'] is not None:
            if inrecord['skipper']['object'][0] is not None:
                skipper = inrecord['skipper']['object'][0].text
        return skipper

    def getskipperimsafe(self, astext=False, inrecord=None):
        if inrecord is None: inrecord=self.record
        if inrecord['skipper']['object'] is not None:
            if inrecord['skipper']['object'][1] is not None:
                imsafe = inrecord['skipper']['object'][1].active
                if astext:
                    if imsafe:
                        ret = 'true'
                    else:
                        ret = 'false'
                else:
                    ret = imsafe
        return ret

    def getskipper(self, inrecord=None):
        if inrecord is None: inrecord=self.record
        #return self.skipper
        return inrecord['skipper']['object']

    def setskipper(self, s, imsafe):
        self.record['skipper']['object'] = [s, imsafe]

    # functions for tractorin
    # ==================
    def gettractorinname(self, inrecord=None):
        if inrecord is None: inrecord=self.record
        name = ''
        if inrecord['tractorin']['object'] is not None:
            if inrecord['tractorin']['object'][0] is not None:
                name = inrecord['tractorin']['object'][0].text
        return name

    def gettractorinimsafe(self, inrecord=None):
        if inrecord is None: inrecord=self.record
        imsafe = ''
        if inrecord['tractorin']['object'] is not None:
            if inrecord['tractorin']['object'][1] is not None:
                imsafe= inrecord['tractorin']['object'][1].active
        return imsafe

    def gettractorin(self, inrecord=None):
        if inrecord is None: inrecord=self.record
        return inrecord['tractorin']['object']

    def settractorin(self, s, imsafe=None):
        self.record['tractorin']['object'] = [s, imsafe]

    # -------------------

    # functions for tractorout
    # ==================
    def gettractoroutname(self, inrecord=None):
        if inrecord is None: inrecord=self.record
        name = ''
        if inrecord['tractorout']['object'] is not None:
            if inrecord['tractorout']['object'][0] is not None:
                name = inrecord['tractorout']['object'][0].text
        return name

    def gettractoroutimsafe(self, inrecord=None):
        if inrecord is None: inrecord=self.record
        imsafe = ''
        if inrecord['tractorout']['object'] is not None:
            if inrecord['tractorout']['object'][1] is not None:
                imsafe= inrecord['tractorout']['object'][1].active
        return imsafe

    def gettractorout(self, inrecord=None):
        if inrecord is None: inrecord=self.record
        return inrecord['tractorout']['object']

    def settractorout(self, s, imsafe):
        self.record['tractorout']['object'] = [s, imsafe]

class CrvOpdata(CrvRecord):
    def __init__(self, indata):
        self.data = indata
        self.haveopenedlog = False

        # record structure
        # Its a dictionary of dictionaries
        # The primary index (e.g 'time') below is used as a top level reference.
        # The embedded disctionary consists of,
        # 'defvalue' : this is meant to be a default value, but tends to be used for different purposes
        # 'object': this is usually a widget that can be modified as required
        # 'type': the type of the record, used in different ways. Can be e.g. 'button', 'label', etc
        # 'shelf': whether to maintain persistance for that record value (persists between program runs)
        #
        # The main record - holds all relevant data
        #
        self.oprecord = {}

        # dict of self.record values (written to persistance)
        self.values = {}
        self.valueslast = {}

        # log time
        self.oprecord['time'] = {'dbpos': 0, 'dbname': 'LDate', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1, 'noinit':1}

        # time log was sucessfully sent
        # Values for this are in [ 'NONET', 'MAILERROR', 'UNSENT' ] or a time (the sent time!).
        # The default is UNSENT - i.e. it assume it hasnt been sent.
        self.oprecord['emailtime'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}

        # these are records that just hold a value. 'object' will be None - the value of the
        # variable will be stored in 'defvalue'. These records are typically persisted (otherwise
        # there isn't much benefit to using them).

        self.oprecord['logactive'] = {'defvalue': False, 'logtype': 'boat', 'object': None, 'type': 'bool', 'shelf':1}
        self.oprecord['screen'] = {'defvalue': 'screen_main', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':1}

        # the screen definitions

        self.oprecord['screen_crvweather'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_crvoperational'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_logaudit'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_logarchive'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_managecrew'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_managelocations'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_managevessels'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_settings2'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_display_update'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_boatlog'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_crvclose'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_crvincident_main'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_crvincident_activation'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_crvincident_onscene'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_crvincident_termination'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_crvincident_assistdetails'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_plcheck'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_ptcheck'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_reccheck'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['screen_main'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}

        # these just hold the label widgets to update time. ('time')
        self.oprecord['time_crvweather'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_crvoperational'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_logaudit'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_logarchive'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_managecrew'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_managelocations'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_managevessels'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_settings2'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_display_update'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_boatlog'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_crvclose'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_crvincident_main'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_crvincident_activation'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_crvincident_onscene'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_crvincident_termination'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_crvincident_assistdetails'] = {'defvalue': '', 'logtype': 'incident', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_main'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_plcheck'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_ptcheck'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['time_reccheck'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}

        # these are all the guts of the program
        self.oprecord['mainstatus'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['activitylabel'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}

        #self.oprecord['nowcasting'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'object': None, 'type': '', 'shelf':1}
        self.oprecord['wind'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':1}
        self.oprecord['winddirection'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':1}
        self.oprecord['cloudcover'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':1}
        self.oprecord['seastate'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':1}
        self.oprecord['visibility'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':1}
        self.oprecord['initialreason'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'labobj': None, 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['prelaunch'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'checkbox', 'shelf':1}
        #self.oprecord['callsign'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':1}
        self.oprecord['tidehightime'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':0}
        self.oprecord['tidehighheight'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':0}
        self.oprecord['tidelowtime'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':0}
        self.oprecord['tidelowheight'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':0}
        self.oprecord['crewmeetsops'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': 'checkbox', 'shelf':1}
        self.oprecord['crewlistsent'] = {'dbpos': 0, 'dbname': '', 'defvalue': False, 'logtype': 'boat', 'object': None, 'type': 'checkbox', 'shelf':1}
        self.oprecord['crewlistsendcheck'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': 'checkbox', 'shelf':1}
        self.oprecord['crewlistsendbut'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': 'button', 'shelf':0}
        self.oprecord['vesseloperational'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': 'checkbox', 'shelf':1}
        self.oprecord['homeoperational'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'button', 'shelf':0}
        self.oprecord['homeincident'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':0}
        self.oprecord['addsavecrew'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'text', 'shelf':0}

        # used to change labels and disable widgets when single engine vessels are in use
        self.oprecord['closelablayout'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursclose'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursclosefin'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursclosefinp'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursclosefinsb'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursclosedurp'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursclosedursb'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursclosedur'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}

        self.oprecord['enginehourslabel'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursstart'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursstartp'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['enginehoursstartsb'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}

        self.oprecord['portehoursstart'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['portehoursfin'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['portehoursdur'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['sbehoursstart'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['sbehoursfin'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['sbehoursdur'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['fuelprice'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['fuelcost'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['fuelstart'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['fuelfin'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0} # calc
        self.oprecord['fuelused'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0} # calc
        self.oprecord['fueladded'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['fuelatend'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0} # calc
        self.oprecord['fuellabel'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['fuelsuppliedtype'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['fuelsuppliedprice'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['fuelsuppliedcost'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['fuelsuppliedstart'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['fuelsuppliedfin'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0} # calc
        self.oprecord['fuelsuppliedused'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0} # calc
        self.oprecord['fuelsuppliedadded'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['fuelsuppliedlabel'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['closingchecks'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['closingtime'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['closelogbutton'] = {'dbpos': 0, 'dbname': '', 'defvalue': 0, 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['tidetitle'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['settingshead'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['newlog'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['homeboatlog'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['closing'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['butactivity'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['managecrew'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        self.oprecord['logarchive'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}
        #self.oprecord['currenttype'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1}

        # In weather screen, Cancel button may be Back (depending on entry)
        self.oprecord['weathercancel'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}

        #crew stuff
        self.oprecord['skipper'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'crew', 'shelf':1}
        self.oprecord['tractorin'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'crew', 'shelf':1}
        self.oprecord['tractorout'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': 'crew', 'shelf':1}

        #required settings
        self.oprecord['reqvessdefn'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['reqvessname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['reqtidestation'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['reqemaillog'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['labvessname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['labtidestation'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['labemaillog'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['reqhomebutton'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['reqmanagecrewbutton'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['requpdtidesbutton'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}

        self.oprecord['upddisplab'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['upddispgrid'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['upddispback'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['upddisppb'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':0}

        # for manage vessels screen.
        self.oprecord['managevesselname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managevesselcallsign'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managevesselfuelrate'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managevesselfueltype'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managevesselhide'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managevesselphone'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managevesselmsanum'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managevesselengine'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.managevesselname=0
        self.managevesselcallsign=1
        self.managevesselfuelrate=2
        self.managevesselfueltype=3
        self.managevesselenginetype=7

        #statusbar widgets
        self.oprecord['statusbarday'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'status', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['statusbardate'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'status', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['statusbartime'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'status', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['statusbaractive'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'status', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['statusbargps'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'status', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['statusbarnet'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'status', 'object': None, 'type': '', 'shelf':0}
        self.oprecord['statusbarsensor'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'status', 'object': None, 'type': '', 'shelf':0}

        # for manage crew screen. Name is the crew name and type is true for a skipper
        self.oprecord['managecrewfirstname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managecrewlastname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managecrewnfullame'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managecrewtype'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.oprecord['managecrewid'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}

        # save any incidents that have been associated with this boatlog. We allow up to 10 incidents
        # (dont know why - but seemed like a good number that will never be reached - it will probably
        # never exceed 2.
        # The value of these will be the filename on disk.
        self.oprecord['savedinc0'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc1'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc2'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc3'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc4'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc5'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc6'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc7'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc8'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['savedinc9'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}

        # The following are the sent statuses of the incidents.
        self.oprecord['sentinc0'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc1'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc2'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc3'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc4'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc5'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc6'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc7'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc8'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['sentinc9'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}

        # save the pre launch check required values
        self.oprecord['plcvisual'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcbatteries'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcoilandwater'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcflushvalves'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plccoverdown'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcpumplocker'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdehumidifier'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcshorepower'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcfronthatch'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcbowsternlines'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plctransomhatches'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcradioson'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcnavlights'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcbriefing'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcpersonal'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcaerials'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcnavunits'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcnavcheck'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}

        # save the pre launch check defect values
        self.oprecord['plcdefvisual'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefbatteries'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefoilandwater'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefflushvalves'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefcoverdown'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefpumplocker'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefdehumidifier'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefshorepower'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdeffronthatch'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefbowsternlines'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdeftransomhatches'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefradioson'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefnavlights'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefbriefing'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefpersonal'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefaerials'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefnavunits'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['plcdefnavcheck'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}

        self.oprecord['pltconnected'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['pltlockpin'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['pltchocks'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}

        self.oprecord['pltdefconnected'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['pltdeflockpin'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['pltdefchocks'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}

        self.oprecord['rectimeout'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recwashed'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['rectubes'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['reccover'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recengineoil'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recbilge'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recsandtrap'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recflushed'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recstowgear'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recstowropes'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recfuel'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recfuelreset'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recwindscreen'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recpumpcover'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recpump'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recpumpfuel'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recpfds'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recsuits'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['rechandhelds'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recprovs'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdamage'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdehumidifier'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recbatteries'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recshorepower'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recready'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['reccompletedby'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['reccleaned'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}

        self.oprecord['recsigned'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recsignature'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}

        self.oprecord['recdefwashed'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdeftubes'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefcover'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefengineoil'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefbilge'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefsandtrap'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefflushed'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefstowgear'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefstowropes'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdeffuel'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdeffuelreset'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefwindscreen'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefpumpcover'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefpump'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefpumpfuel'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefpfds'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefsuits'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefhandhelds'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefprovs'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefdamage'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefdehumidifier'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefbatteries'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefshorepower'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefready'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}
        self.oprecord['recdefcleaned'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'text', 'shelf':1}


        CrvRecord.__init__(self, self.data, self.oprecord, self.values, self.valueslast)

class CrvLogdata(CrvRecord):
    def __init__(self, indata):
        self.data = indata
        self.haveopenedlog = False

        self.logrecord = {}

        self.loggroup = {}

        self.values = {}
        self.valueslast = []

        # list of boatlog values. Each one is a dict (written to persistance)
        self.logvalues = []

        #the different types of boat logs
        self.logrecord['logtypeboat'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincident'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypetraining'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypefault'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypemaintenance'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypepr'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypefund'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeprevaction'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypestanddown'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeeducation'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypecrew'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypearrive'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypedepart'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeguest'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypelaunch'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypelog'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypefuel'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeonscene'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeonstation'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['enginetypes'] = ['Outboard', 'Twin outboard', 'Jet', 'Twin jet']

        # Incident action logs
        self.logrecord['logtypeinconscene'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeinctow'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincshadow'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincfinish'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincmedical'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincmechanical'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincsinking'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincaground'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincsearch'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtypeincother'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}

        self.loggroup['logtypes'] =     ['logcommonlog',
                                         'logtypefault',
                                         'logtypestanddown',
                                         'logtypecrew']

        # This provides a mapping between the displayed log value and the index value
        self.loggroup['logtypesinitreason'] = {'Duty Boat':'logtypeboat', 'Incident':'logtypeincident',
                                         'Training':'logtypetraining', 'Repairs and Maint': 'logtypemaintenance',
                                         'Public Relations':'logtypepr', 'Fund Raising':'logtypefund',
                                         'Preventative Action':'logtypeprevaction', 'Education':'logtypeeducation'}

        self.loggroup['logtypesdisp'] = {'Log Arrival':'logtypearrive', 'Log Departure':'logtypedepart',
                                         'Log Fault':'logtypefault', 'Training':'logtypetraining','Stand Down':'logtypestanddown',
                                         'Add Crew':'logtypecrew', 'Add/Remove\nGuest':'logtypeguest',
                                         'Launch':'logtypelaunch', 'Log':'logtypelog', 'Fuel':'logtypefuel',
                                         'OnStation':'logtypeonstation'}

        self.loggroup['logtypesinc'] =     ['logtypeinconscene', 'logtypeinctow',
                                         'logtypeincshadow', 'logtypeincfinish',
                                         'logtypeincmedical', 'logtypeincmechanical',
                                         'logtypeincsinking', 'logtypeincaground',
                                         'logtypeincsearch', 'logtypeincother']

        # This provides a mapping between incident action values and index values
        self.loggroup['logtypesincdisp'] = {'OnScene': 'logtypeinconscene', 'Tow': 'logtypeinctow',
                                         'Shadow': 'logtypeincshadow',
                                         'Medical':'logtypeincmedical', 'Mechanical' :'logtypeincmechanical',
                                         'Sinking': 'logtypeincsinking', 'Aground' :'logtypeincaground',
                                         'Search': 'logtypeincsearch', 'Other': 'logtypeincother'}

        #
        # The following definitions are for the logbook class and the index starts with 'log'
        #common for all logs
        self.logrecord['logtime'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logtype'] = {'defvalue': '', 'logtype': 'boat', 'key': 'act', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['loglocation'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['loghelm'] = {'defvalue': '', 'logtype': 'boat', 'key':'helm', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['lognav'] = {'defvalue': '', 'logtype': 'boat', 'key':'nav', 'object': None, 'type':'', 'shelf':0}

        self.commonlogtime = 0
        self.commonlogtype = 1
        self.commonlogloc = 2
        self.commonloghelm = 3
        self.commonlognav = 4

        #
        self.logrecord['logcommonlog'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        #self.loggroup['logcommonlog'] = ['logtime', 'logtype', 'logfrom', 'logto']
        self.loggroup['logcommonlog'] = ['logtime', 'logtype', 'loglocation', 'loghelm', 'lognav']

        #specific to boat boat)
        #self.logrecord['logboatactivity'] = {'defvalue': '', 'logtype': 'boat', 'key': 'act', 'object': None, 'type':'t', 'shelf':0}
        #self.logrecord['logactivity'] = {'defvalue': '', 'logtype': 'boat', 'key': 'act', 'object': None, 'type':'t', 'shelf':0}
        #self.logrecord['logboathelm'] = {'defvalue': '', 'logtype': 'boat', 'key':'helm', 'object': None, 'type':'', 'shelf':0}
        #self.logrecord['logboatnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        #self.loggroup['logtypeboat'] = ['logactivity', 'logboatnotes']

        self.logrecord['logincidentactivity'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        #self.logrecord['logincidentnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        #self.loggroup['logtypeincident'] = ['logincidentactivity', 'logincidentnotes']
        self.loggroup['logtypeincident'] = ['logincidentactivity']

        # ======================== DEFINE INCIDENT ACTIONS
        #specific to incident action onscene
        self.logrecord['loginconssap'] = {'defvalue': '', 'inc': 'incsap100a', 'logtype': 'boat', 'key': 'SAP', 'object': None, 'type':'t', 'shelf':0}
        self.logrecord['loginconsexits'] = {'defvalue': '', 'inc': 'incexitstrategies', 'logtype': 'boat', 'key':'exitstrategy', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['loginconsnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeinconscene'] = ['loginconssap', 'loginconsexits', 'loginconsnotes']

        #specific to incident action tow
        self.logrecord['loginctowtakento'] = {'defvalue': '', 'inc': 'inctakento', 'logtype': 'boat', 'key': 'takento', 'object': None, 'type':'t', 'shelf':0}
        self.logrecord['loginctowarrived'] = {'defvalue': '', 'inc': 'inctakentotime', 'logtype': 'boat', 'key':'timearrived', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['loginctownotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['loginctowdropped'] = {'defvalue': '', 'logtype': 'boat', 'key':'dropped', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeinctow'] = ['loginctowtakento', 'loginctowarrived', 'loginctownotes', 'loginctowdropped']

        #specific to incident action shadow
        self.logrecord['logincshadowto'] = {'defvalue': '', 'inc': 'inctakento', 'logtype': 'boat', 'key': 'shadowto', 'object': None, 'type':'t', 'shelf':0}
        self.logrecord['logincshadowleft'] = {'defvalue': '', 'logtype': 'boat', 'key':'leftat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logincshadownotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeincshadow'] = ['logincshadowto', 'logincshadowleft', 'logincshadownotes']

        #specific to incident action mechanical
        self.logrecord['logincmechanicalreason'] = {'defvalue': '', 'logtype': 'boat', 'key': 'reason', 'object': None, 'type':'t', 'shelf':0}
        self.logrecord['logincmechanicalstarted'] = {'defvalue': '', 'logtype': 'boat', 'key':'started', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logincmechanicalnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeincmechanical'] = ['logincmechanicalreason', 'logincmechanicalstarted', 'logincmechanicalnotes']

        #specific to incident action medical
        self.logrecord['logincmedicalstatus'] = {'defvalue': '', 'logtype': 'boat', 'key': 'status', 'object': None, 'type':'t', 'shelf':0}
        self.logrecord['logincmedicalnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeincmedical'] = ['logincmedicalstatus', 'logincmedicalnotes']

        #specific to incident action sinking
        self.logrecord['logincsinkingnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeincsinking'] = ['logincsinkingnotes']

        #specific to incident action aground
        self.logrecord['logincagroundnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeincaground'] = ['logincagroundnotes']

        #specific to incident action other
        self.logrecord['logincothernotes'] = {'defvalue': '', 'logtype': 'boat', 'key': 'reason', 'object': None, 'type':'t', 'shelf':0}
        #
        self.loggroup['logtypeincother'] = ['logincothernotes']

        #specific to incident action search
        self.logrecord['logincsearchnotes'] = {'defvalue': '', 'logtype': 'boat', 'key': 'reason', 'object': None, 'type':'t', 'shelf':0}
        #
        self.loggroup['logtypeincsearch'] = ['logincsearchnotes']

        # ======================== END OF DEFINE INCIDENT ACTIONS

        #specific to training log
        self.logrecord['logtrainingactivity'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'t', 'shelf':0}
        self.logrecord['logtrainingnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypetraining'] = ['logtrainingactivity', 'logtrainingnotes']

        # -------------------

        #specific to fault log
        self.logrecord['logfaultaction'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logfaultresult'] = {'defvalue': '', 'logtype': 'boat', 'key':'res', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypefault'] = ['logfaultaction', 'logfaultresult']

        # -------------------

        #specific to launch log
        self.logrecord['loglaunchnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypelaunch'] = ['loglaunchnotes']

        # -------------------

        #specific to log log
        self.logrecord['loglognotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypelog'] = ['loglognotes']

        # -------------------

        #specific to fuel log
        self.logrecord['logfueltype'] = {'defvalue': '', 'logtype': 'boat', 'key':'type', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logfueladded'] = {'defvalue': '', 'logtype': 'boat', 'key':'added', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logfuelprice'] = {'defvalue': '', 'logtype': 'boat', 'key':'price', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logfuelnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypefuel'] = ['logfueltype', 'logfueladded', 'logfuelprice', 'logfuelnotes']

        # -------------------

        #specific to onstation log
        self.logrecord['logonstationnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeonstation'] = ['logonstationnotes']

        # -------------------

        #specific to arrive log
        self.logrecord['logarrivenotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypearrive'] = ['logarrivenotes']

        # -------------------

        #specific to depart log
        self.logrecord['logdepartnotes'] = {'defvalue': '', 'logtype': 'boat', 'key':'notes', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypedepart'] = ['logdepartnotes']

        # -------------------

        #specific to guest log
        self.logrecord['logguestname'] = {'defvalue': '', 'logtype': 'boat', 'key':'name', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logguestaction'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypeguest'] = ['logguestname', 'logguestaction']

        # -------------------

        # #specific to maintenance log
        # self.logrecord['logmaintaction'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        # self.logrecord['logmaintresult'] = {'defvalue': '', 'logtype': 'boat', 'key':'res', 'object': None, 'type':'', 'shelf':0}
        # #
        # self.loggroup['logtypemaintenance'] = ['logmaintaction', 'logmaintresult']
        #
        # -------------------

        # #specific to public relations log
        # self.logrecord['logpraction'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        # self.logrecord['logprresult'] = {'defvalue': '', 'logtype': 'boat', 'key':'res', 'object': None, 'type':'', 'shelf':0}
        # #
        # self.loggroup['logtypepr'] = ['logpraction', 'logprresult']
        #
        # -------------------

        # #specific to fund raising log
        # self.logrecord['logfundaction'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        # self.logrecord['logfundresult'] = {'defvalue': '', 'logtype': 'boat', 'key':'res', 'object': None, 'type':'', 'shelf':0}
        # #
        # self.loggroup['logtypefund'] = ['logfundaction', 'logfundresult']
        #
        # -------------------

        #specific to preventative action log
        # self.logrecord['logprevactionaction'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        # self.logrecord['logprevactionresult'] = {'defvalue': '', 'logtype': 'boat', 'key':'res', 'object': None, 'type':'', 'shelf':0}
        # #
        # self.loggroup['logtypeprevaction'] = ['logprevactionaction', 'logprevactionresult']

        # -------------------

        #specific to stand down log
        self.logrecord['logstanddownaction'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logstanddownresult'] = {'defvalue': '', 'logtype': 'boat', 'key':'res', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypestanddown'] = ['logstanddownaction', 'logstanddownresult']

        # -------------------

        #specific to education log
        # self.logrecord['logeducationaction'] = {'defvalue': '', 'logtype': 'boat', 'key':'act', 'object': None, 'type':'', 'shelf':0}
        # self.logrecord['logeducationresult'] = {'defvalue': '', 'logtype': 'boat', 'key':'res', 'object': None, 'type':'', 'shelf':0}
        # #
        # self.loggroup['logtypeeducation'] = ['logeducationaction', 'logeducationresult']

        # -------------------

        #specific to additional crew log
        self.logrecord['logcrewaddname'] = {'defvalue': '', 'logtype': 'boat', 'key':'name', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logcrewaddimsafe'] = {'defvalue': '', 'logtype': 'boat', 'key':'IMSAFE', 'object': None, 'type':'', 'shelf':0}
        #
        self.loggroup['logtypecrew'] = ['logcrewaddname', 'logcrewaddimsafe']

        # -------------------

        self.logrecord['logentrybox'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}
        self.logrecord['logcurrenttype'] = {'defvalue': '', 'logtype': 'boat', 'object': None, 'type':'', 'shelf':0}

        CrvRecord.__init__(self, self.data, self.logrecord, self.values, self.valueslast)

    def getloggroup(self, index):
        if self.loggroup.has_key(index):
            ret = self.loggroup[index]
        else:
            ret = []
        return ret

class CrvIncData(CrvRecord):
    def __init__(self, indata):
        self.data = indata

        self.haveopenedlog = False
        self.shelf_file = ''
        self.shelf_fd = None

        self.increcord = {}

        self.values = {}
        self.valueslast = {}

        self.conradio = [None, None, None, None]
        self.unitradio = [None, None]

        # the following define an incident
        self.increcord['incid'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The identity of the incident'}
        self.increcord['incalerttime'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The time the incident was started'}
        # Not used ..
        # default for incident email sent status is UNSENT
        # Values for this are in [ 'NONET', 'MAILERROR', 'UNSENT' ] or a time (the sent time!).
        # self.increcord['incemailtime'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype': 'boat', 'object': None, 'type': '', 'shelf':1,
        #                            'doc': 'The time the incident was emailed'}
        self.increcord['incvesselname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The incident vessel name'}
        self.increcord['incposition'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The location of the vessel'}
        self.increcord['inclatd'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The vessel latitude degrees'}
        self.increcord['inclatm'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The vessel latitude decimal minutes'}
        self.increcord['inclongd'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The vessel longitude degrees'}
        self.increcord['inclongm'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The vessel longitude decimal degrees'}
        self.increcord['inclatlong'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Vessel formatted lat/long'}
        self.increcord['incvesselcallsign'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The vessel callsign'}
        self.increcord['incvesselskipper'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incnumber'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incisincident'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incispositioning'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incrccnznumber'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incpoliceevent'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Presumably to indicate a police event. Not captured anywhere'}
        self.increcord['inclocationunderway'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inctimeunderway'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incposition'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incstatus'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inctimeonscene'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incpob'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incpoba'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Number of adults on board'}
        self.increcord['incpobc'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Number of children on board'}
        self.increcord['incpobd'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Number of dogs onboard'}
        self.increcord['incproblem'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmission'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incactions'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inctakento'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inctakentotime'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmale0010'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmale1120'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmale2130'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmale3140'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmale4150'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmale50plus'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incfemale0010'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incfemale1120'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incfemale2130'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incfemale3140'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incfemale4150'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incfemale50plus'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inccrvto'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inctimearrive'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Time CRV arrives back from whence it came'}
        self.increcord['inctimetotal'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Total time for incident'}

        self.increcord['inccrvfuelstart'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The crv fuel at incident start'}
        self.increcord['inccrvfuelatend'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The crv fuel at incident close'}
        self.increcord['inccrvfuelused'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The amount of fuel used for the incident (calculated)'}
        self.increcord['inccrvfuelprice'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The price for the crv fuel'}
        self.increcord['inccrvfuelcost'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The total cost of crv fuel for the incident'}

        self.increcord['incfuelsupplied'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The amount of extra fuel supplied for the incident'}
        self.increcord['incfuelsuppliedprice'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The price of the extra fuel'}
        self.increcord['incfuelsuppliedtype'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The type of fuel classified as extra'}
        self.increcord['incfuelsuppliedcost'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incfueltotalcost'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'The total cost of crv and supplied fuel for the incident'}

        self.increcord['incresultsuccess'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incresultsuspended'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incresultstooddown'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incresultfatality'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistcallsign'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistlength'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistcolorh'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistcoloro'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassisttype'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistpropulsion'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistnumengines'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmnznum'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistcommstype'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistactivity'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistother'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incaddress'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inchomephone'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmobile'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incworkphone'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incemail'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmember'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incmembernum'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incquotedprice'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inccardname'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inccardexpiry'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inccardcsv'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inccardtype'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inccardnumber'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,     # crypt????
                                   'doc': ''}
        self.increcord['incassistauthorise'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incassistsignature'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,  # help!!!!
                                   'doc': ''}
        self.increcord['inctide'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incseastate'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incvisibility'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Weather visibility (from op log)'}
        self.increcord['incwindspeed'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incdirection'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['inchomebuttonact'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':0,
                                   'doc': 'Button to get to Home or Log depending on whether log is open'}
        self.increcord['inchomebuttoncon'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': 'Button to get to Home or Log depending on whether log is open'}
        self.increcord['inchomebuttonadm'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':0,
                                   'doc': 'Button to get to Home or Log depending on whether log is open'}
        self.increcord['inchomebuttonpay'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':0,
                                   'doc': 'Button to get to Home or Log depending on whether log is open'}
        self.increcord['inchomebuttondeb'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':0,
                                   'doc': 'Button to get to Home or Log depending on whether log is open'}
        self.increcord['incsap100a'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incsap100b'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incexitstrategies'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}
        self.increcord['incdepartscene'] = {'dbpos': 0, 'dbname': '', 'defvalue': '', 'logtype':'incident', 'object': None, 'type': '', 'shelf':1,
                                   'doc': ''}

        CrvRecord.__init__(self, self.data, self.increcord, self.values, self.valueslast)

        # a list of all indexes we want to shelve for persistence. Note: only for boat log - not incidents.
        # These have their own save
        self.shelf_keys = []
        for key in self.increcord.keys():
            if self.increcord[key]['shelf'] == 1 and self.increcord[key]['logtype'] == 'incident':
                self.shelf_keys.append(key)

    def inc_shelf_save(self):
        '''
        Save the current incident to disk.
        Name of incident is INCTMPid.JSON
        e.g. INCTMP0.JSON
        '''
        doit = False

        if not self.haveopenedlog:
            self.data.Logger.info("CRV: INC Persistance: inc_shelf_save: refusing to save during initialisation")
        elif self.shelf_fd is not None:
            self.data.Logger.info("CRV: INC Persistance: inc_shelf_save: already open. refusing to report")
        else:
            doit = True
            if len(self.shelf_file) == 0:
                incid = self.getobjectvariable('incid', 'text', '0')
                infile = 'INCTMP' + str(incid) + '.JSON'
                self.shelf_file = os.path.join(self.data.datadir, infile)

                if os.path.exists(self.shelf_file):  # only on first check
                    doit = False
        if doit:
            try:
                emess = "setincidentvalues"
                # collate all the data to save
                tosave = self.setincidentvalues()
                if len(tosave) > 0:
                    self.data.Logger.info("CRV: Persistance: save.. dumping " + self.shelf_file)
                    emess = "Open"
                    self.shelf_fd = open(self.shelf_file, 'w')

                    # add here all keys to be saved for persistence
                    #json.dump(self.values, self.shelf_fd)
                    emess = "Dump"
                    json.dump(tosave, self.shelf_fd)
            except:
                self.data.Logger.info("CRV: Persistance: save.. exception (" + emess + ") " + self.shelf_file)
                doit = False

        self.shelf_close()

        return doit

    def shelf_close(self):
        if self.shelf_fd is not None:
            self.data.Logger.info("CRV: Persistance: close")
            self.shelf_fd.close()
            self.shelf_fd = None

    def setincidentvalues(self):
        """
        Save required record values for persistence
        Doesnt do save - just builds dictionary to save.
        If nothing has changed return False - else True

        It has a number of stages. ...
        1. process self.record and put items to save in self.values
        2. process self.logvalues (not sure what needs to be done here yet
        ...
        n. return a dict containing,

        { 'record': vales, 'log': values }
        """
        toreturn = {}

        # done like this as each key can throw an exception on error and at least we get some saved
        # (instead of losing all after the exception)

        for key in self.shelf_keys:
            self.data.Logger.debug('CRV:INCSAVE: ' + key)
            try:
                self.setrecordsinglevalue(key)
            except:
                self.data.Logger.debug('CRV:Exception on save: ' + key)

        toreturn['INCIDENT'] = self.values

        return toreturn

    def inc_shelf_restore(self, incid):
        '''
        Tries to either do a full or partial restore of a saved incident file.
        :param incid:
        :return:
        '''
        infile = 'INCTMP' + str(incid) + '.JSON'
        infile = os.path.join(self.data.datadir, infile)

        if os.path.exists(infile):
            efail = ''
            try:
                efail = 'load'
                self.shelf_fd = open(infile)
                toget = json.load(self.shelf_fd)

                efail = 'RECORD'
                self.values = dict([(str(k), str(v)) for k, v in toget['INCIDENT'].items()])
                self.valueslast = self.values.copy()
                ret = True
            except:
                self.data.Logger.info('CRV: INC FAILED TO RECOVER INCIDENT DATA at ' + efail)
                self.data.Logger.info('CRV: filename ' + infile)
                ret = False

            self.shelf_close()
            self.data.Logger.info("CRV: Persistance: restore.. returns (nvalues, return value) " +
                             str(len(self.values)) + " " + str(ret))

            return ret

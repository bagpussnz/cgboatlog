__author__ = 'ian.collins'

import threading
import smtplib
import os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import parseaddr
from email import Encoders

class CrvEmail:
    def __init__(self, inlogger):
        self.Logger = inlogger

        self.emailserver = ''
        self.emailuser = ''
        self.emailpass = ''
        self.attachfile = []

        self.eto = ''
        self.esubject = ''
        self.emessage = ''

    def setemailserver(self, value):
        """
        Optional - No default.
        Default email server
        """
        defset = 'smtp.gmail.com'
        if value is not None:
            if value != '':
                defset = value
        self.emailserver = defset

        return True

    def getemailserver(self):
        return self.emailserver

    def setemailuser(self, value):
        """
        Optional - No default.
        Default email user
        """
        defset = 'nzboatlog@gmail.com'
        if value is not None:
            if value != '':
                defset = value
        self.emailuser = defset

        return True

    def getemailuser(self):
        return self.emailuser

    def setemailpass(self, value):
        """
        Optional - No default.
        Default email password (maybe change this to a crypt.
        """
        defset = 'udMx#8der~55'
        if value is not None:
            if value != '':
                defset = value
        self.emailpass = defset

        return True

    def getemailpass(self):
        return self.emailpass

    def addattachment(self, f):
        self.attachfile.append(f)

    def clearattachments(self):
        self.attachfile[:] = []

    def verifyemail(self, testemail):
        ret = True
        try:
            (name, addr) = parseaddr(testemail)

            if addr != '': ret = False
        except:
            ret = False

        return ret

    #def sendsimple(self, to, subject, message, displayaction):
    def sendemail(self, displayaction):
        rstat = False
        self.Logger.debug('CRV:sendmail:enter')
        try:
            msg = MIMEMultipart('alternative')
            self.Logger.debug('CRV:sendmail:enter1')
            msg['Subject'] = self.esubject
            self.Logger.debug('CRV:sendmail:enter2')
            msg['From'] = self.emailuser
            self.Logger.debug('CRV:sendmail:enter3')
            msg['To'] = self.eto

            self.Logger.debug('CRV:sendmail:subject, from, to..' + self.esubject + ' ' + self.emailuser + self.eto)
            text = ''
            html = self.emessage

            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')

            msg.attach(part1)
            msg.attach(part2)

            for f in self.attachfile:
                if len(f):
                    if os.path.exists(f):
                        self.Logger.debug('CRV:sendemail attach exists.. ' + f)

                        part3 = MIMEBase('application', "octet-stream")
                        part3.set_payload(open(f, "rb").read())
                        Encoders.encode_base64(part3)

                        #part3.add_header('Content-Disposition', 'attachment; filename='+f)
                        fb = os.path.basename(f)
                        part3.add_header('Content-Disposition', 'attachment', filename=fb)

                        self.Logger.debug('CRV:sendemail adding mime attach.. ')

                        msg.attach(part3)
                    else:
                        self.Logger.debug('CRV:sendemail attach does not exist.. ' + f)

            displayaction('Opening connection to mail server')
            self.Logger.debug('CRV:sendmail:server.. ' + self.emailserver)
            session = smtplib.SMTP(self.emailserver, 587)
            session.set_debuglevel(1)
            self.Logger.debug('CRV:sendmail:ehlo')
            session.ehlo()
            self.Logger.debug('CRV:sendmail:starttls')
            session.starttls()
            #session.ehlo()
            displayaction('Logging in')
            self.Logger.debug('CRV:sendmail:user, pass.. ' + self.emailuser + ' ' + self.emailpass)
            session.login(self.emailuser, self.emailpass)

            displayaction('Sending email')
            session.sendmail(self.emailuser, self.eto, msg.as_string())
            rstat = True
        except smtplib.socket.gaierror:
            displayaction('Cannot contact mail server')
        except smtplib.SMTPAuthenticationError:
            displayaction('Cannot authenticate mail server')
        #except SomeSendMailError:
        #    pass # Couldn't send mail
        except:
            displayaction('Unknown mail error')
        finally:

            if session:
                session.quit()
        return rstat



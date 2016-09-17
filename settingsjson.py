import json

settings_crvapp_json = json.dumps([
    {'type': 'string',
     'title': 'Vessel Name',
     'desc': 'Enter vessel name',
     'section': 'crvapp',
     'key': 'vesselname'},                 # required
    {'type': 'string',
     'title': 'Vessel Callsign',
     'desc': 'Enter vessel callsign',
     'section': 'crvapp',
     'key': 'vesselcallsign'},                 # required
    {'type': 'string',
     'title': 'Tide Station',
     'desc': 'This will be used to incpopulate tide info',
     'section': 'crvapp',
     'key': 'tidestation'},                # required
    {'type': 'options',
     'title': 'Vessel engine type',
     'desc': 'Please specify engine type and configuration',
     'section': 'crvapp',
     'key': 'enginetype',                  # optional. default Jet
     'options': ['Outboard', 'Twin outboard', 'Jet', 'Twin jet']},
])

settings_vesslog_json = json.dumps([
    {'type': 'title',
     'title': 'Please enter your vessel preferences'},

    {'type': 'bool',
     'title': 'Coastguard NZ Vessel?',
     'desc': 'Is this vessel a Coastguard NZ resource?',
     'section': 'VesselLog',
     'key': 'cnzvessel'},                  # optional. default True

    {'type': 'numeric',
     'title': 'Minimum number of crew',
     'desc': 'Minimum operational crew',
     'section': 'VesselLog',
     'key': 'mincrew'},                    # optional. default 2

    {'type': 'numeric',
     'title': 'Maximum number of crew',
     'desc': 'Maximum operational crew',
     'section': 'VesselLog',
     'key': 'maxcrew'},                    # optional. default 6

    {'type': 'numeric',
     'title': 'Light Threshold',
     'desc': 'The light threshold for day/night switch (%)',
     'section': 'VesselLog',
     'key': 'lightthreshold'},

    {'type': 'numeric',
     'title': 'Check Light Sensor',
     'desc': 'Check for light level (seconds  - set to 0 to disable)',
     'section': 'VesselLog',
     'key': 'lightchecktime'},

    {'type': 'numeric',
     'title': 'GPS Check Time',
     'desc': 'How often we check for GPS update (may affect battery)',
     'section': 'VesselLog',
     'key': 'gpsrefreshtime'},

    {'type': 'numeric',
     'title': 'Network Check Time',
     'desc': 'How often network uptime is checked',
     'section': 'VesselLog',
     'key': 'netrefreshtime'},

    {'type': 'bool',
     'title': 'Show system settings',
     'desc': 'Set to True to show programming framework (kivy) settings',
     'section': 'VesselLog',
     'key': 'showkivy'},                   # optional. default False

    {'type': 'path',
     'title': 'Location of crew list',
     'desc': 'A file containing possible crew and skipper. Format: one name per line. \n'
             'Skippers: s:skippername one per line',
     'section': 'VesselLog',
     'key': 'posscrew'},                   # optional

    {'type': 'path',
     'title': 'Data Directory',
     'desc': 'The directory where files used by this application are stored.',
     'disabled': 'true',
     'section': 'VesselLog',
     'key': 'datadir'},                    # disabled - info only
])
# settings_vesslog_json = json.dumps([
#     {'type': 'title',
#      'title': 'Please enter your vessel preferences'},
#     {'type': 'string',
#      'title': 'Vessel Name',
#      'desc': 'Enter vessel name',
#      'section': 'VesselLog',
#      'key': 'vesselname'},                 # required
#     {'type': 'string',
#      'title': 'Vessel Callsign',
#      'desc': 'Enter vessel callsign',
#      'section': 'VesselLog',
#      'key': 'vesselcallsign'},                 # required
#     {'type': 'string',
#      'title': 'Tide Station',
#      'desc': 'This will be used to incpopulate tide info',
#      'section': 'VesselLog',
#      'key': 'tidestation'},                # required
#     {'type': 'bool',
#      'title': 'Coastguard NZ Vessel?',
#      'desc': 'Is this vessel a Coastguard NZ resource?',
#      'section': 'VesselLog',
#      'key': 'cnzvessel'},                  # optional. default True
#     {'type': 'numeric',
#      'title': 'Minimum number of crew',
#      'desc': 'Minimum operational crew',
#      'section': 'VesselLog',
#      'key': 'mincrew'},                    # optional. default 2
#     {'type': 'numeric',
#      'title': 'Maximum number of crew',
#      'desc': 'Maximum operational crew',
#      'section': 'VesselLog',
#      'key': 'maxcrew'},                    # optional. default 6
#     {'type': 'options',
#      'title': 'Vessel engine type',
#      'desc': 'Please specify engine type and configuration',
#      'section': 'VesselLog',
#      'key': 'enginetype',                  # optional. default Jet
#      'options': ['Outboard', 'Twin outboard', 'Jet', 'Twin jet']},
#     {'type': 'bool',
#      'title': 'Show system settings',
#      'desc': 'Set to True to show programming framework (kivy) settings',
#      'section': 'VesselLog',
#      'key': 'showkivy'},                   # optional. default False
#     {'type': 'path',
#      'title': 'Location of crew list',
#      'desc': 'A file containing possible crew and skipper. Format: one name per line. \n'
#              'Skippers: s:skippername one per line',
#      'section': 'VesselLog',
#      'key': 'posscrew'},                   # optional
#     {'type': 'path',
#      'title': 'Data Directory',
#      'desc': 'The directory where files used by this application are stored.',
#      'disabled': 'true',
#      'section': 'VesselLog',
#      'key': 'datadir'},                    # disabled - info only
# ])
settings_email_json = json.dumps([
    {'type': 'bool',
     'title': 'Email log files',
     'desc': 'Set to True to email completed logs',
     'section': 'Email',                   # optional. default True
     'key': 'doemaillog'},
    {'type': 'string',
     'title': 'Email address',
     'desc': 'Address to send logs to',
     'section': 'Email',
     'key': 'emaillog'},                   # required.
    {'type': 'string',
     'title': 'Email for crew lists',
     'desc': 'Address to send crew lists to',
     'section': 'Email',
     'key': 'emailcrew'},                  # optional. default emaillog
    {'type': 'string',
     'title': 'Email for training logs',
     'desc': 'Address to send training logs to',
     'section': 'Email',
     'key': 'emailtraining'},              # optional. default emaillog
    {'type': 'string',
     'title': 'Email Server',
     'desc': 'Server to send email through',
     'section': 'Email',
     'key': 'emailserver'},                # optional. default smtp.gmail.com
    {'type': 'string',
     'title': 'Email User',
     'desc': 'Email user name',
     'section': 'Email',
     'key': 'emailuser'},                  # optional. default is hardcoded
    {'type': 'string',
     'title': 'Email Password',
     'desc': 'Password for email user',
     'password': 'true',
     'section': 'Email',
     'key': 'emailpass'},                 # optional. default is hardcoded
])

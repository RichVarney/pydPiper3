#!/usr/bin/python.pydPiper3
# coding: UTF-8


# Page Definitions
# See Page Format.txt for instructions and examples on how to modify your display settings

# Load the fonts needed for this system
FONTS = {
	'small': { 'default': False, 'file':'latin1_5x8_fixed.fnt','size':(5,8) },
	'large': { 'default': True, 'file':'BigFont_10x16_fixed.fnt', 'size':(10,16) },
	'tiny': { 'file':'upperasciiwide_3x5_fixed.fnt', 'size':(5,5) },
}
#new_font = 'DejaVuSans'
new_font = 'DejaVuSans-Bold'
#new_font = 'DejaVuSansMono'
#new_font = 'ProggyTiny'  # not working
#new_font = 'BetecknaLowerCaseBold.ttf'  # not working
#new_font = 'FreePixel'  # not working

TRUETYPE_FONTS = {
	'ttsmall': {'file': new_font, 'size': 10},
	'ttlarge': {'file': new_font, 'size': 16},
        'ttxlarge': {'file': new_font, 'size': 20},
        'ttxxlarge': {'file': new_font, 'size': 28}
}

height = TRUETYPE_FONTS['ttlarge']['size']
xl_height = TRUETYPE_FONTS['ttxlarge']['size']
xxl_height = TRUETYPE_FONTS['ttxxlarge']['size']
width = 20
space = 2
screen_width = 132
screen_height = 64

IMAGES = {
	'progbar': {'file':'progressbar_100x8.png' },
	'splash': {'file':'moode_background.png'}
}

# Load the Widgets that will be used to produce the display pages
WIDGETS = {
        'splash': { 'type':'image', 'image':'splash'},
	'nowplaying': { 'type':'ttext', 'format':'{0}', 'variables':['actPlayer|upper'], 'font':'ttlarge', 'varwidth':True},
	'nowplayingdata': { 'type':'ttext', 'format':'{0} OF {1}', 'variables':['playlist_position', 'playlist_length'], 'font':'ttsmall', 'just':'right','size':(80,16),'varwidth':True},
	'title': { 'type':'ttext', 'format':'{0}', 'variables':['title'], 'font':'ttxlarge','varwidth':True, 'effect':('scroll','left',2,1,20,'onstart',3,screen_width)},
	'artist': { 'type':'ttext', 'format':'{0}', 'variables':['artist'], 'font':'ttxlarge','varwidth':True, 'effect':('scroll','left',2,1,20,'onstart',3,screen_width) },
	'album': { 'type':'ttext', 'format':'{0}', 'variables':['album'], 'font':'ttxlarge','varwidth':True },
	'position': { 'type':'ttext', 'format':'{0}', 'variables':['position'], 'font':'ttxxlarge', 'just': 'center', 'varwidth':True },
	'metadata': { 'type':'ttext', 'format':'{0} {1}', 'variables':['bitrate', 'type'], 'font':'ttlarge','varwidth':True },
	'playlist_display': { 'type':'ttext', 'format':'{0}', 'variables':['playlist_display'], 'font':'ttlarge', 'varwidth':True },
	'elapsed': { 'type':'ttext', 'format':'{0}', 'variables':['elapsed_formatted'], 'font':'ttxlarge', 'just':'right', 'varwidth':True },
	'time': { 'type':'ttext', 'format':'{0}', 'variables':['utc|timezone+Europe/London|strftime+%H:%M'], 'font':'ttxxlarge', 'just':'center', 'varwidth':True, 'size':(screen_width, screen_height) },
	'volume': { 'type':'ttext', 'format':'Volume', 'variables':['volume'], 'font':'ttxlarge', 'varwidth':True, 'just':'left', 'size':(screen_width, xl_height)},
	'volume_num': {'type': 'ttext', 'format': '{0}', 'variables': ['volume'], 'font': 'ttxlarge', 'size': (screen_width, xl_height)},
	'volumebar': { 'type':'progressimagebar', 'image':'progbar','value':'volume', 'rangeval':(0,100) },
	'songprogress': { 'type':'progressbar', 'value':'elapsed', 'rangeval':(0,'length'), 'size':(80,4) },
	'showplay': { 'type':'ttext', 'format':'\u25B6PLAY', 'font':'ttxxlarge', 'varwidth':True, 'just':'center', 'size':(screen_width, screen_height) },
	'showstop': { 'type':'ttext', 'format':'\u25FCSTOP', 'font':'ttxxlarge', 'varwidth':True, 'just':'center', 'size':(screen_width, screen_height) },
	'temptoohigh': { 'type':'text', 'format':'\ue005 Warning System Too Hot ({0})', 'variables':['system_temp_formatted'], 'font':'large', 'varwidth':True, 'effect':('scroll','left',1,1,20,'onstart',3,80) },
	'systemvars': { 'type':'ttext', 'format':'{0}c  Disk {1}%\n{2}', 'variables':['current_tempc', 'disk_availp','utc|timezone+Europe/London|strftime+%H:%M'], 'font':'ttlarge', 'varwidth':True, 'just':'center', 'effect':('scroll','left',1,20,'onstart',3,80), 'size':(screen_width, screen_height) },
	'ip': { 'type':'ttext', 'format':'{0}\n{1}', 'variables':['ip','utc|timezone+Europe/London|strftime+%H:%M'], 'font':'ttlarge', 'just':'center', 'varwidth':True, 'size':(screen_width, screen_height) }
}

# Assemble the widgets into canvases.  Only needed if you need to combine multiple widgets together so you can produce effects on them as a group.
CANVASES = {
	'playartist': { 'widgets': [ ('artist',0,0), ('elapsed',0,xxl_height+space), ('nowplayingdata', 0, screen_height-10) ], 'size':(screen_width,screen_height) },
	'playtitle': { 'widgets':  [ ('title',0,0), ('elapsed',0,xxl_height+space), ('nowplayingdata', 0, screen_height-10)], 'size':(screen_width,screen_height) },
	'playmeta': { 'widgets': [ ('metadata',0,0), ('elapsed',0,xxl_height+space), ('nowplayingdata', 0, screen_height-10)], 'size':(screen_width,screen_height) },
	'blank': { 'widgets': [ ('elapsed',0,xxl_height+space), ('nowplayingdata', 0, screen_height-10)], 'size':(screen_width,screen_height)},
	'stoptime': { 'widgets': [ ('time',0,2)], 'size':(screen_width,screen_height) },
	'volume_changed': { 'widgets': [ ('volume',0,0), ('volume_num', 0, xl_height+space), ('volumebar',0,screen_height-8) ], 'size':(screen_width, screen_height) },
}

# Place the canvases into sequences to display when their condition is met
# More than one sequence can be active at the same time to allow for alert messages
# You are allowed to include a widget in the sequence without placing it on a canvas

# Note about Conditionals
# Conditionals must evaluate to a True or False resulting
# To access system variables, refer to them within the db dictionary (e.g. db['title'])
# To access the most recent previous state of a variable, refer to them within the dbp dictionary (e.g. dbp['title'])
SEQUENCES = [
	{	'name': 'seqSplash', 'canvases': [ { 'name':'splash', 'duration':4 } ], 'conditional': "db['state']=='starting'" },
	{
		'name': 'seqPlay',
		'canvases': [
			{ 'name':'playartist', 'duration':15, 'conditional':"not db['stream']=='webradio'" },
			{ 'name':'blank', 'duration':0.5, 'conditional':"not db['stream']=='webradio'" },
			{ 'name':'playtitle', 'duration':15, 'conditional':"not db['stream']=='webradio'" },
			{ 'name':'blank', 'duration':0.5, 'conditional':"not db['stream']=='webradio'" },
		],
		'conditional': "db['state']=='play'"
	},
	{
		'name': 'seqStop',
		'canvases': [
			{ 'name':'stoptime', 'duration':8, 'conditional':"True" }
		],
		'conditional': "db['state']=='stop'"
	},
	{
		'name':'seqVolume',
		'coordinates':(0,0),
		'canvases': [ { 'name':'volume_changed', 'duration':3 } ],
		'conditional': "db['volume'] != dbp['volume']",
		'minimum':2,
	},
	{
		'name': 'seqAnnouncePlay',
		'canvases': [ { 'name':'showplay', 'duration':3 } ],
		'conditional': "db['state'] != dbp['state'] and db['state']=='play'",
		'minimum':2,
	},
	{
		'name': 'seqAnnounceStop',
		'canvases': [ { 'name':'showstop', 'duration':3 } ],
		'conditional': "db['state'] != dbp['state'] and db['state']=='stop'",
		'minimum':2,
	},
	{
		'name':'seqAnnounceTooHot',
		'canvases': [ { 'name':'temptoohigh', 'duration':5 } ],
		'conditional': "db['system_tempc'] > 85",
		'minimum':5,
		'coolingperiod':30
	}
]

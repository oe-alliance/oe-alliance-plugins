# -*- coding: utf-8 -*-#
#
# LCD4linux - Pearl DPF LCD Display, Samsung SPF-Line, Grautec-TFT, WLAN-LCDs, internes LCD über Skin
#
# written by joergm6 @ IHAD
# (Meteo-Station @ compilator)
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#  Advertise with this Plugin is not allowed.
#  For other uses, permission from the author is necessary.
#
Version = "V3.8-r0"
from __init__ import _
from enigma import eConsoleAppContainer, eActionMap, iServiceInformation, iFrontendInformation, eDVBResourceManager, eDVBVolumecontrol
from enigma import getDesktop, getEnigmaVersionString
from enigma import ePicLoad, ePixmap, getBoxType

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Language import language
from Components.Network import iNetwork
from Components.Input import Input
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.SystemInfo import SystemInfo
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar
from Screens import Standby 
from Screens.Standby import TryQuitMainloop
# imports
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from PIL import ImageColor
import colorsys
import xml.dom.minidom
import email
from email.header import decode_header
import urllib
import calendar
import math
import gc

url2 = False
try:
	import urllib2
	url2 = True
except:
	pass
import os
import textwrap
import codecs
try:
	import cStringIO
except:
	import StringIO as cStringIO
import ctypes.util
import glob
import random
import struct
import string
from time import gmtime, strftime, localtime, mktime, time, sleep, timezone, altzone
from datetime import datetime, timedelta, date
dummy = datetime.strptime('2000-01-01', '%Y-%m-%d').date()

from Components.ServiceEventTracker import ServiceEventTracker
from enigma import eTimer, eEPGCache, eServiceReference, eServiceCenter, iPlayableService
from RecordTimer import RecordTimer, RecordTimerEntry, parseEvent
from threading import Thread, Lock
import Queue
import ping

from Components.config import configfile, getConfigListEntry, ConfigEnableDisable, ConfigPassword, \
	ConfigYesNo, ConfigText, ConfigClock, ConfigNumber, ConfigSelectionNumber, ConfigSelection, \
	config, Config, ConfigSubsection, ConfigSubList, ConfigSubDict, ConfigIP, ConfigSlider, ConfigDirectory
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.NimManager import nimmanager
 
from Tools.BoundFunction import boundFunction
from twisted.internet import reactor, defer
from twisted.web import client
from twisted.web.client import getPage, HTTPClientFactory, downloadPage
from xml.dom.minidom import parse, parseString
from xml.etree.cElementTree import parse as parseE
from urllib import urlencode, quote
import xml.etree.cElementTree
from myFileList import FileList as myFileList
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
import icalendar
from module import L4Lelement,L4LVtest

L4LElist = L4Lelement()

try:
	from fcntl import ioctl
	from pngutil import png_util
	pngutil = png_util.PNGUtil()
	pngutilconnect = pngutil.connect()
	PNGutilOK = True
except:
	PNGutilOK = False

# globals
L4LdoThread = True
LCD4config = "/etc/enigma2/lcd4config"
LCD4plugin ="/usr/lib/enigma2/python/Plugins/Extensions/LCD4linux/"
Data = LCD4plugin+"data/"
if getBoxType().startswith("gb"):
	LCD4default = Data+"default.gigablue"
else:	
	LCD4default = Data+"default.lcd"
WetterPath = LCD4plugin+"wetter/"
MeteoPath = LCD4plugin+"meteo/"
FONTdefault="/usr/share/fonts/nmsbd.ttf"
FONT=FONTdefault
ClockBack = Data+"PAclock2.png"
Clock = Data+"Clock"
RecPic = Data+"rec.png"
xmlPIC ="/tmp/l4ldisplay.png"
xmlPICtmp ="/tmp/l4ldisplaytmp.png"
if os.path.islink(LCD4plugin+"tmp") == True:
	TMP = os.path.realpath(LCD4plugin+"tmp")+"/"
else:
	TMP = "/tmp/"
TMPL=TMP+"lcd4linux/"
Fritz="%sfritz.txt" % TMPL
FritzFrame = Data+"fritzcallframe.png"
FritzRing = Data+"fritzcallring.png"
FritzPic = Data+"fritzpic.png"
CrashFile="/tmp/L4Lcrash.txt"
PIC="%sdpf" % TMPL
PICtmp="%sdpftmp" % TMPL
PIC2="%sdpf2" % TMPL
PIC2tmp="%sdpf2tmp" % TMPL
PIC3="%sdpf3" % TMPL
PIC3tmp="%sdpf3tmp" % TMPL
PICcal="%sdpfcal.png" % TMPL
PICwetter="%sdpfwetter%%s.png" % TMPL
PICmeteo="%sdpfmeteo.png" % TMPL
PICfritz="%sdpffritz.png" % TMPL
HTTPpic="%sdpfhttp.jpg" % TMPL
HTTPpictmp="%sdpfhttptmp.jpg" % TMPL
TXTdemo="%slcd4linux.demo" % TMPL
MP3tmp="%sid3coverart.jpg" % TMPL
GoogleCover="%sgcover.jpg" % TMPL
WWWpic="%swww%%s.jpg" % TMPL
LCDon = True
ConfigMode = False
ConfigStandby = False
ShellRunning = False
OSDon = 0
OSDtimer = -5
OSDdontshow = ["LCD4linux Settings","Virtual Zap","InfoBar","Infobar","SecondInfoBar","FanControl2","Mute","LCD Text","UnhandledKey","QuickZap","Volume","PVRState"]
OSDdontskin = ["LCDdisplayFile","VirtualZap","InfoBar","Infobar","InfoBarSummary","PictureInPicture","SimpleSummary","TimeshiftState","InfoScreen","Standby","EMCMediaCenter","InfoBarMoviePlayerSummary","PVRState","ResolutionLabel","WidgetBackground","camodogFSScreen2","camodogFSmini"]
wwwWetter = ["",""]
WetterType = ""
WetterZoom = ""
CalType = ""
CalZoom = ""
CalColor = ""
wwwMeteo = ""
MeteoType = ""
MeteoZoom = ""
PopText = ["",""]
ScreenActive = ["1","","",""]
ScreenTime= 0
isVideoPlaying = 0
AktHelligkeit = [-1,-1,-1,-1,-1,-1]
AktTFT = ""
PopMail = [[],[],[],[],[],""]
PopMailUid = [["","",""],["","",""],["","",""],["","",""],["","",""]]
Bilder = ["","",""]
BilderIndex = [0,0,0]
BilderTime = 0
FritzTime = 0
FritzList = []
xmlList = []
ThreadRunning = 0
DeviceRemove = []
QuickList = [[],[],[]]
QuickIM = [None,None,None]
SaveEventList = ["","",""]
SaveEventListChanged = False
ICS = {}
ICSlist = []
ICSrunning = False
ICSdownrun = False
SAT = {}
TunerCount = 0
TunerMask = 0
SamsungDevice = None
SamsungDevice2 = None
SamsungDevice3 = None
isMediaPlayer = ""
GrabRunning = False
GrabTVRunning = False
TVrunning = False
BriefLCD = Queue.Queue()
Briefkasten = Queue.Queue()
Brief1 = Queue.Queue()
Brief2 = Queue.Queue()
Brief3 = Queue.Queue()
CPUtotal = 0
CPUidle = 0
L4LSun = (7,0)
L4LMoon = (19,0)
INFO = ""
draw,draw2,draw3 = None,None,None
im,im2,im3 = None,None,None

USBok = False
if ctypes.util.find_library("usb-0.1") is not None:
	print "[LCD4linux] libusb found :-)",getEnigmaVersionString()
#	getEnigmaVersionString().split("-")[-1] > "3.2" # /model=dm800
	import Photoframe
	import dpf
	import usb.util
	USBok = True

Farbe = [("black", _("black")), ("white", _("white")), 
 ("gray", _("gray")), ("silver", _("silver")), ("slategray", _("slategray")),
 ("aquamarine", _("aquamarine")),
 ("yellow", _("yellow")), ("greenyellow", _("greenyellow")), ("gold", _("gold")),
 ("red", _("red")), ("tomato", _("tomato")), ("darkred", _("darkred")), ("indianred", _("indianred")), ("orange", _("orange")), ("darkorange", _("darkorange")), ("orangered", _("orangered")),
 ("green", _("green")), ("lawngreen", _("lawngreen")), ("darkgreen", _("darkgreen")), ("lime", _("lime")), ("lightgreen", _("lightgreen")),
 ("blue", _("blue")), ("blueviolet", _("blueviolet")), ("indigo", _("indigo")), ("darkblue", _("darkblue")), ("cadetblue", _("cadetblue")), ("cornflowerblue", _("cornflowerblue")), ("lightblue", _("lightblue")),
 ("magenta", _("magenta")), ("violet", _("violet")), ("darkorchid", _("darkorchid")), ("deeppink", _("deeppink")), ("cyan", _("cyan")),
 ("brown", _("brown")), ("sandybrown", _("sandybrown")), ("moccasin", _("moccasin")), ("rosybrown", _("rosybrown")), ("olive", _("olive")),
]
ScreenSelect = [("0", _("off")), ("1", _("Screen 1")), ("2", _("Screen 2")), ("3", _("Screen 3")), ("12", _("Screen 1+2")), ("13", _("Screen 1+3")), ("23", _("Screen 2+3")), ("123", _("Screen 1+2+3")), ("4", _("Screen 4")), ("14", _("Screen 1+4")), ("24", _("Screen 2+4")), ("34", _("Screen 3+4")), ("124", _("Screen 1+2+4")), ("134", _("Screen 1+3+4")), ("234", _("Screen 2+3+4")), ("1234", _("Screen 1+2+3+4")), ("5", _("Screen 5")), ("6", _("Screen 6")), ("7", _("Screen 7")), ("8", _("Screen 8")), ("9", _("Screen 9")), ("12345", _("Screen 1-5")), ("123456", _("Screen 1-6")), ("1234567", _("Screen 1-7")), ("12345678", _("Screen 1-8")), ("123456789", _("Screen 1-9")), ("56789", _("Screen 5-9")), ("13579", _("Screen 1+3+5+7+9")), ("2468", _("Screen 2+4+6+8"))]
ScreenUse = [("1", _("Screen 1")), ("2", _("Screen 1-2")), ("3", _("Screen 1-3")), ("4", _("Screen 1-4")), ("5", _("Screen 1-5")), ("6", _("Screen 1-6")), ("7", _("Screen 1-7")), ("8", _("Screen 1-8")), ("9", _("Screen 1-9"))]
ScreenSet = [("1", _("Screen 1")), ("2", _("Screen 2")), ("3", _("Screen 3")), ("4", _("Screen 4")), ("5", _("Screen 5")), ("6", _("Screen 6")), ("7", _("Screen 7")), ("8", _("Screen 8")), ("9", _("Screen 9"))]
OnOffSelect = [("0", _("off")), ("1", _("on"))]
TimeSelect = [("1", _("5s")), ("2", _("10s")), ("3", _("15s")), ("4", _("20s")), ("6", _("30s")), ("8", _("40s")), ("10", _("50s")), ("12", _("1min")), ("24", _("2min")), ("36", _("3min")), ("48", _("4min")), ("60", _("5min")), ("120", _("10min"))]
LCDSelect = [("1", _("LCD 1")), ("2", _("LCD 2")), ("12", _("LCD 1+2")), ("3", _("LCD 3")), ("13", _("LCD 1+3")), ("23", _("LCD 2+3")), ("123", _("LCD 1+2+3"))]
LCDType = [("11", _("Pearl (or compatible LCD) 320x240")), ("12", _("Pearl (or compatible LCD) 240x320")),
 ("210", _("Samsung SPF-72H 800x480")), ("23", _("Samsung SPF-75H/76H 800x480")), ("24", _("Samsung SPF-87H 800x480")), ("25", _("Samsung SPF-87H old 800x480")), ("26", _("Samsung SPF-83H 800x600")),
 ("29", _("Samsung SPF-85H/86H 800x600")), ("212", _("Samsung SPF-85P/86P 800x600")), ("28", _("Samsung SPF-105P 1024x600")), ("27", _("Samsung SPF-107H 1024x600")), ("213", _("Samsung SPF-107H old 1024x600")),
 ("211", _("Samsung SPF-700T 800x600")),
 ("430", _("Internal TFT-LCD 400x240")),
 ("50", _("Internal Box-Skin-LCD")),
 ("31", _("only Picture 320x240")), ("33", _("only Picture 800x480")), ("36", _("only Picture 800x600")), ("37", _("only Picture 1024x600")), ("320", _("only Picture Custom Size"))]
if PNGutilOK:
	LCDType.insert(14,("930", _("Internal Vu+ Duo2 LCD 400x240")))
xmlLCDType = [("96x64", _("96x64")), ("132x64", _("132x64")), ("220x176", _("220x176")), ("255x64", _("255x64")), ("400x240", _("400x240"))]
WetterType =  [("12", _("2 Days 1 Line")), ("22", _("2 Days 2 Line")), ("1", _("4 Days 1 Line")), ("2", _("4 Days 2 Lines")), ("11", _("5 Days 1 Line")), ("21", _("5 Days 2 Lines")), ("3", _("Current")), ("4", _("Current Temperature (+C)")), ("41", _("Current Temperature (-C)")), ("5", _("4 Days Vertical View")), ("51", _("5 Days Vertical View"))]
MeteoType = [("1", _("Current")), ("2", _("Current Temperature"))]
NetatmoType = [("THCPN", _("All")), ("T", _("Temperature")), ("TC", _("Temperature+Co2")), ("TCP", _("Temperature+Co2+Pressure"))]
CO2Type = [("0", _("Bar")), ("09", _("Bar+Value")), ("1", _("Knob")), ("19", _("Knob+Value"))]
ClockType = [("12", _("Time")), ("112", _("Date+Time")), ("1123", _("Date+Time+Weekday")), ("11", _("Date")), ("123", _("Time+Weekday")), ("13", _("Weekday")), ("4", _("Flaps Design")), ("51", _("Analog")), ("52", _("Analog+Date")), ("521", _("Analog+Date+Weekday")), ("521+", _("Analog+Date+Weekday 2"))]
AlignType = [("0", _("left")), ("1", _("center")), ("2", _("right")), ("0500", _("5%")), ("1000", _("10%")), ("1500", _("15%")), ("2000", _("20%")), ("2500", _("25%")), ("3000", _("30%")), ("3500", _("35%")), ("4000", _("40%")), ("4500", _("45%")), ("5000", _("50%")), ("5500", _("55%")), ("6000", _("60%")), ("6500", _("65%")), ("7000", _("70%")), ("7500", _("75%")), ("8000", _("80%")), ("8500", _("85%")), ("9000", _("90%")), ("9500", _("95%"))]
DescriptionType = [("10", _("Short")), ("12", _("Short (Extended)")),("01", _("Extended")), ("21", _("Extended (Short)")),("11", _("Short+Extended"))]
CalType = [("9", _("no Calendar")),("0", _("Month")), ("0A", _("Month+Header")), ("1", _("Week")), ("1A", _("Week+Header"))]
CalTypeE = [("0", _("no Dates")), ("D2", _("Dates compact 2 Lines")), ("D3", _("Dates compact 3 Lines")), ("C1", _("Dates 1 Line")), ("C3", _("Dates 3 Lines")), ("C5", _("Dates 5 Lines")), ("C9", _("Dates 9 Lines"))]
CalLayout = [("0", _("Frame")), ("1", _("Underline")), ("2", _("Underline 2"))]
CalListType = [("D", _("Dates compact")), ("D-", _("Dates compact no Icon")), ("C", _("Dates")), ("C-", _("Dates no Icon"))]
FritzType = [("L", _("with Icon")), ("L-", _("no Icon")), ("TL", _("with Icon & Targetnumber")), ("TL-", _("no Icon, with Targetnumber"))]
InfoSensor = [("0", _("no")), ("R", _("rpm/2")), ("r", _("rpm")), ("T", _("C")), ("RT", _("C + rmp/2")), ("rT", _("C + rmp"))]
InfoCPU = [("0", _("no")), ("P", _("%")), ("L0", _("Load@1min")), ("L1", _("Load@5min")), ("PL0", _("% + Load@1min")), ("PL1", _("% + Load@5min"))]
HddType = [("0", _("show run+sleep")), ("1", _("show run"))]
MailType = [("A1", _("Always All")), ("A2", _("Always New")), ("B2", _("Only New"))]
MailProzent = [("30", _("30%")), ("40", _("40%")), ("50", _("50%")), ("60", _("60%")), ("70", _("70%")), ("80", _("80%")), ("90", _("90%")), ("100", _("100%"))]
MailKonto = [("1", _("1")), ("2", _("1-2")), ("3", _("1-3")), ("4", _("1-4")), ("5", _("1-5"))]
MailConnect = [("0", _("Pop3-SSL")), ("1", _("Pop3")), ("2", _("IMAP-SSL")), ("3", _("IMAP"))]
Split = [("false", _("no")), ("true", _("yes")), ("true25", _("yes +25%"))]
DirType = [("0", _("horizontally")), ("2", _("vertically"))]
FontType = [("0", _("Global")), ("1", _("1")), ("2", _("2")), ("3", _("3"))]
ProgressType = [("1", _("only Progress Bar")),
("2", _("with Remaining Minutes")), ("21", _("with Remaining Minutes (Size 1.5)")), ("22", _("with Remaining Minutes (Size 2)")),
("3", _("with Percent")), ("31", _("with Percent (Size 1.5)")), ("32", _("with Percent (Size 2)")),
("4", _("with Remaining Minutes (above)")), ("41", _("with Remaining Minutes (above/Size 1.5)")), ("42", _("with Remaining Minutes (above/Size 2)")),
("5", _("with Percent (above)")), ("51", _("with Percent (above/Size 1.5)")), ("52", _("with Percent (above/Size 2)")),
("6", _("with Remaining Minutes (below)")), ("61", _("with Remaining Minutes (below/Size 1.5)")), ("62", _("with Remaining Minutes (below/Size 2)")),
("7", _("with Percent (below)")), ("71", _("with Percent (below/Size 1.5)")), ("72", _("with Percent (below/Size 2)")),
("8", _("with Current 00:00")), ("81", _("with Current 00:00 (Size 1.5)")), ("82", _("with Current 00:00 (Size 2)")),
("9", _("with Current 00:00 (above)")), ("91", _("with Current 00:00 (above/Size 1.5)")), ("92", _("with Current 00:00 (above/Size 2)")),
("A", _("with Current 00:00 (below)")), ("A1", _("with Current 00:00 (below/Size 1.5)")), ("A2", _("with Current 00:00 (below/Size 2)"))
]
now = localtime()
begin = mktime((
	now.tm_year, now.tm_mon, now.tm_mday, 06, 00, \
	0, now.tm_wday, now.tm_yday, now.tm_isdst)
)

LCD4linux = Config()
LCD4linux.Enable = ConfigYesNo(default = True)
LCD4linux.FastMode = ConfigSelection(choices = [("5", _("Normal (5s)")), ("2", _("Fastmode (2s)"))], default="5")
LCD4linux.ScreenActive = ConfigSelection(choices = ScreenSet, default="1")
LCD4linux.ScreenMax = ConfigSelection(choices = ScreenUse, default="1")
LCD4linux.ScreenTime = ConfigSelection(choices = [("0", _("off"))] + TimeSelect, default="0")
LCD4linux.ScreenTime2 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.ScreenTime3 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.ScreenTime4 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.ScreenTime5 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.ScreenTime6 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.ScreenTime7 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.ScreenTime8 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.ScreenTime9 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.BilderTime = ConfigSelection(choices =  [("0", _("off"))] + TimeSelect, default="0")
LCD4linux.BilderSort = ConfigSelection(choices =  [("0", _("off")), ("1", _("alphabetic")), ("2", _("random"))], default="1")
LCD4linux.BilderQuality = ConfigSelection(choices =  [("0", _("low/fast (all)")), ("1", _("low/fast (Picture only)")), ("2", _("better/slow"))], default="1")
LCD4linux.BilderRecursiv = ConfigYesNo(default = False)
LCD4linux.BilderQuick = ConfigSelection(choices =  [("500", _("0.5")), ("1000", _("1")), ("2000", _("2")), ("3000", _("3")), ("5000", _("5")), ("10000", _("10")), ("20000", _("20")), ("30000", _("30"))], default="10000")
LCD4linux.BilderJPEG = ConfigSelectionNumber(20, 100, 5, default = 75)
LCD4linux.BilderJPEGQuick = ConfigSelectionNumber(20, 100, 5, default = 60)
LCD4linux.Helligkeit = ConfigSelectionNumber(0, 10, 1, default = 5)
LCD4linux.Helligkeit2 = ConfigSelectionNumber(0, 10, 1, default = 5)
LCD4linux.Helligkeit3 = ConfigSelectionNumber(0, 10, 1, default = 5)
LCD4linux.LCDoff = ConfigClock(default = int(begin) ) # ((5 * 60 + 0) * 60)
LCD4linux.LCDon = ConfigClock(default = int(begin) )
LCD4linux.LCDWEoff = ConfigClock(default = int(begin) ) # ((5 * 60 + 0) * 60)
LCD4linux.LCDWEon = ConfigClock(default = int(begin) )
LCD4linux.Delay = ConfigSlider(default = 400,  increment = 50, limits = (50, 2000))
LCD4linux.ElementThreads = ConfigSelectionNumber(1, 2, 1, default = 2)
LCD4linux.DevForceRead = ConfigYesNo(default = True)
LCD4linux.ShowNoMsg = ConfigYesNo(default = True)
LCD4linux.SavePicture = ConfigSelection(choices =  [("0", _("no"))] + LCDSelect, default="123")
LCD4linux.WebIfRefresh = ConfigSelectionNumber(1, 60, 1, default = 3)
LCD4linux.WebIfType = ConfigSelection(choices = [("0", _("Javascript")), ("1", _("Reload"))], default="0")
LCD4linux.WebIfInitDelay = ConfigYesNo(default = False)
LCD4linux.WebIfAllow = ConfigText(default="127. 192.168. 172. 10.", fixed_size=False)
LCD4linux.WebIfDeny = ConfigText(default="", fixed_size=False)
LCD4linux.WebIfDesign = ConfigSelection(choices = [("1", _("1 - normal")), ("2", _("2 - side by side"))], default = "2")
LCD4linux.WetterCity = ConfigText(default="London", fixed_size=False)
LCD4linux.Wetter2City = ConfigText(default="Berlin", fixed_size=False)
LCD4linux.WetterPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.WetterLowColor = ConfigSelection(choices = Farbe, default="aquamarine")
LCD4linux.WetterHighColor = ConfigSelection(choices = Farbe, default="violet")
LCD4linux.WetterTransparenz = ConfigSelection(choices = [("false", _("no")), ("crop", _("alternative Copy-Mode/DM800hd (24bit)")), ("true", _("yes (32bit)"))], default = "false")
LCD4linux.WetterIconZoom = ConfigSelectionNumber(30, 70, 1, default = 40)
LCD4linux.WetterRain = ConfigSelection(choices = [("false", _("no")), ("true", _("yes")), ("true2", _("yes + %"))], default = "true")
LCD4linux.WetterRainZoom = ConfigSlider(default = 100,  increment = 1, limits = (90, 200))
LCD4linux.WetterRainColor = ConfigSelection(choices = Farbe, default="silver")
LCD4linux.WetterRainColor2use = ConfigSelectionNumber(10, 100, 10, default = 80)
LCD4linux.WetterRainColor2 = ConfigSelection(choices = Farbe, default="cyan")
LCD4linux.WetterLine = ConfigSelection(choices = [("false", _("no")), ("true", _("yes, short")), ("trueLong", _("yes, long"))], default = "trueLong")
LCD4linux.WetterExtra = ConfigYesNo(default = True)
LCD4linux.WetterExtraZoom = ConfigSlider(default = 100,  increment = 1, limits = (90, 200))
LCD4linux.WetterExtraFeel = ConfigSelectionNumber(0, 5, 1, default = 3)
LCD4linux.WetterExtraColorCity = ConfigSelection(choices = Farbe, default="silver")
LCD4linux.WetterExtraColorFeel = ConfigSelection(choices = Farbe, default="silver")
LCD4linux.WetterWind = ConfigSelection(choices = [("0", _("km/h")), ("1", _("m/s"))], default = "0")
LCD4linux.MeteoURL = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.MoonPath = ConfigText(default="", fixed_size=False, visible_width=50)
if PNGutilOK:
	LCD4linux.LCDType1 = ConfigSelection(choices = LCDType, default="930")
else:
	LCD4linux.LCDType1 = ConfigSelection(choices = LCDType, default="11")
LCD4linux.LCDType2 = ConfigSelection(choices = [("00", _("off"))] + LCDType, default="00")
LCD4linux.LCDType3 = ConfigSelection(choices = [("00", _("off"))] + LCDType, default="00")
LCD4linux.LCDRotate1 = ConfigSelection(choices = [("0", _("0")), ("90", _("90")), ("180", _("180")), ("270", _("270"))], default="0")
LCD4linux.LCDRotate2 = ConfigSelection(choices = [("0", _("0")), ("90", _("90")), ("180", _("180")), ("270", _("270"))], default="0")
LCD4linux.LCDRotate3 = ConfigSelection(choices = [("0", _("0")), ("90", _("90")), ("180", _("180")), ("270", _("270"))], default="0")
LCD4linux.LCDBild1 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.LCDBild2 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.LCDBild3 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.LCDColor1 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.LCDColor2 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.LCDColor3 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.LCDTFT = ConfigSelection(choices =  [("ABC", _("On+Media+Standby")), ("A", _("On")), ("B", _("Media")), ("C", _("Standby"))], default="ABC")
LCD4linux.xmlLCDType = ConfigSelection(choices = xmlLCDType, default="132x64")
LCD4linux.xmlLCDColor = ConfigSelection(choices = [("8", _("8bit - grayscale/color")), ("32", _("32bit - color"))], default="8")
LCD4linux.xmlType01 = ConfigYesNo(default = False)
LCD4linux.xmlType02 = ConfigYesNo(default = False)
LCD4linux.xmlType03 = ConfigYesNo(default = False)
LCD4linux.SizeW = ConfigSlider(default = 800,  increment = 1, limits = (100, 2000))
LCD4linux.SizeH = ConfigSlider(default = 600,  increment = 1, limits = (100, 1000))
LCD4linux.KeySwitch = ConfigYesNo(default = True)
LCD4linux.KeyScreen = ConfigSelection(choices =  [("163", _("2 x FastForwardKey")),("208", _("2 x FastForwardKey Type 2")),("163l", _("Long FastForwardKey")),("2081", _("Long FastForwardKey Type 2")),("358", _("2 x InfoKey")),("3581", _("Long InfoKey"))], default="163")
LCD4linux.KeyOff = ConfigSelection(choices =  [("165", _("2 x FastBackwardKey")),("165l", _("Long FastBackwardKey")),("358", _("2 x InfoKey")),("3581", _("Long InfoKey"))], default="1651")
LCD4linux.Mail1Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail1Connect = ConfigSelection(choices = MailConnect, default="0")
LCD4linux.Mail1User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail1Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail2Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail2Connect = ConfigSelection(choices = MailConnect, default="0")
LCD4linux.Mail2User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail2Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail3Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail3Connect = ConfigSelection(choices = MailConnect, default="0")
LCD4linux.Mail3User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail3Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail4Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail4Connect = ConfigSelection(choices = MailConnect, default="0")
LCD4linux.Mail4User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail4Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail5Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail5Connect = ConfigSelection(choices = MailConnect, default="0")
LCD4linux.Mail5User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail5Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.MailTime = ConfigSelection(choices = [("01", _("60min")), ("01,31", _("30min")), ("01,21,41", _("20min")), ("01,16,31,46", _("15min")), ("01,11,21,31,41,51", _("10min"))], default="01")
LCD4linux.MailShow0 = ConfigYesNo(default = False)
LCD4linux.Recording = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.RecordingLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.RecordingType = ConfigSelection(choices = [("1", _("Corner")), ("2", _("Picon"))], default="1")
LCD4linux.RecordingSize = ConfigSlider(default = 25,  increment = 1, limits = (10, 100))
LCD4linux.RecordingPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.RecordingAlign = ConfigSelection(choices = AlignType, default="2")
LCD4linux.RecordingSplit = ConfigYesNo(default = False)
LCD4linux.RecordingPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Crash = ConfigYesNo(default = True)
LCD4linux.ConfigPath = ConfigText(default="/tmp/", fixed_size=False, visible_width=50)
LCD4linux.Events = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.EventsLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.EventsSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.EventsPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.EventsAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.EventsSplit = ConfigYesNo(default = False)
LCD4linux.EventsType = ConfigSelection(choices = DirType, default="0")
LCD4linux.FritzPath = ConfigText(default="/tmp/", fixed_size=False, visible_width=50)
LCD4linux.FritzFrame = ConfigText(default="", fixed_size=False, visible_width=40)
LCD4linux.FritzLines = ConfigSelectionNumber(0, 20, 1, default = 2)
LCD4linux.FritzPictures = ConfigSelectionNumber(0, 20, 1, default = 0)
LCD4linux.FritzPictureSearch = ConfigSelection(choices = [("0", _("no")), ("1", _("yes")), ("12", _("yes, extended"))], default="1")
LCD4linux.FritzPictureType = ConfigSelection(choices = DirType, default="0")
LCD4linux.FritzRemove = ConfigSelectionNumber(1, 48, 1, default = 12)
LCD4linux.FritzTime = ConfigSelection(choices = TimeSelect, default="3")
LCD4linux.FritzPopupLCD = ConfigSelection(choices = [("0", _("no"))] + LCDSelect, default="1")
LCD4linux.FritzPopupColor = ConfigSelection(choices = Farbe, default="yellow")
LCD4linux.CalPath = ConfigText(default="/tmp/", fixed_size=False, visible_width=40)
LCD4linux.CalPathColor = ConfigSelection(choices = Farbe, default="green")
LCD4linux.CalHttp = ConfigText(default="http...", fixed_size=False, visible_width=50)
LCD4linux.CalHttpColor = ConfigSelection(choices = Farbe, default="lime")
LCD4linux.CalHttp2 = ConfigText(default="http...", fixed_size=False, visible_width=50)
LCD4linux.CalHttp2Color = ConfigSelection(choices = Farbe, default="greenyellow")
LCD4linux.CalHttp3 = ConfigText(default="http...", fixed_size=False, visible_width=50)
LCD4linux.CalHttp3Color = ConfigSelection(choices = Farbe, default="yellow")
LCD4linux.CalPlanerFS = ConfigYesNo(default = False)
LCD4linux.CalPlanerFSColor = ConfigSelection(choices = Farbe, default="orange")
LCD4linux.CalLine = ConfigSelectionNumber(1, 2, 1, default = 1)
LCD4linux.CalDays = ConfigSelection(choices = [("0", "0"), ("3", "3"), ("7", "7"), ("14", "14"), ("21", "21"), ("31", "31")], default="7")
LCD4linux.CalTime = ConfigSelection(choices = [("03", _("60min")), ("03,33", _("30min")), ("03,23,43", _("20min")), ("03,18,33,48", _("15min"))], default="03")
LCD4linux.CalTransparenz = ConfigSelection(choices = [("false", _("no")), ("crop", _("alternative Copy-Mode/DM800hd (24bit)")), ("true", _("yes (32bit)"))], default = "false")
LCD4linux.Cal = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.CalLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.CalPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.CalAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.CalSplit = ConfigYesNo(default = False)
LCD4linux.CalZoom = ConfigSlider(default = 10,  increment = 1, limits = (3, 50))
LCD4linux.CalType = ConfigSelection(choices = CalType, default="0A")
LCD4linux.CalTypeE = ConfigSelection(choices = CalTypeE, default="D2")
LCD4linux.CalLayout = ConfigSelection(choices = CalLayout, default="0")
LCD4linux.CalColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.CalBackColor = ConfigSelection(choices = Farbe, default="gray")
LCD4linux.CalCaptionColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.CalShadow = ConfigYesNo(default = False)
LCD4linux.CalFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.CalList = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.CalListLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.CalListSize = ConfigSlider(default = 12,  increment = 1, limits = (5, 150))
LCD4linux.CalListPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.CalListAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.CalListSplit = ConfigYesNo(default = False)
LCD4linux.CalListLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.CalListProzent = ConfigSelection(choices = MailProzent, default="50")
LCD4linux.CalListType = ConfigSelection(choices = CalListType, default="C")
LCD4linux.CalListColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.CalListShadow = ConfigYesNo(default = False)
LCD4linux.CalListFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Font = ConfigText(default=FONTdefault, fixed_size=False, visible_width=50)
LCD4linux.Font1 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Font2 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Font3 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.EnableEventLog = ConfigSelection(choices = [("0", _("off")), ("1", _("Logfile normal")), ("2", _("Logfile extensive")), ("3", _("Console normal"))], default = "0")
LCD4linux.TunerColor = ConfigSelection(choices = Farbe, default="slategray")
LCD4linux.TunerColorActive = ConfigSelection(choices = Farbe, default="lime")
LCD4linux.TunerColorOn = ConfigSelection(choices = Farbe, default="yellow")
LCD4linux.OSD = ConfigSelection(choices =  [("0", _("disabled"))] + TimeSelect + [("9999", _("always"))], default="0")
LCD4linux.OSDLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.OSDsize = ConfigSlider(default = 425,  increment = 5, limits = (320, 1280))
LCD4linux.OSDshow = ConfigSelection(choices = [("TRM", _("TV+Radio+Media")), ("TR", _("TV+Radio")), ("RM", _("Radio+Media")), ("T", _("TV")), ("R", _("Radio")), ("M", _("Media"))], default = "TRM")
LCD4linux.OSDTransparenz = ConfigSelection(choices = [("0", _("normal (full)")), ("1", _("trimmed (transparent)")), ("2", _("trimmed (black)"))], default = "1")
LCD4linux.OSDfast = ConfigYesNo(default = False)
LCD4linux.Popup = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.PopupLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.PopupSize = ConfigSlider(default = 30,  increment = 1, limits = (10, 150))
LCD4linux.PopupPos = ConfigSlider(default = 30,  increment = 2, limits = (0, 1024))
LCD4linux.PopupAlign = ConfigSelection(choices = [("0", _("left")), ("1", _("center")), ("2", _("right"))], default="0")
LCD4linux.PopupColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.PopupBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="brown")
LCD4linux.Mail = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MailLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MailSize = ConfigSlider(default = 12,  increment = 1, limits = (5, 150))
LCD4linux.MailPos = ConfigSlider(default = 30,  increment = 2, limits = (0, 1024))
LCD4linux.MailAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MailSplit = ConfigYesNo(default = False)
LCD4linux.MailColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MailBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.MailKonto = ConfigSelection(choices = MailKonto, default="1")
LCD4linux.MailLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.MailType = ConfigSelection(choices = MailType, default="A1")
LCD4linux.MailProzent = ConfigSelection(choices = MailProzent, default="50")
LCD4linux.MailShadow = ConfigYesNo(default = False)
LCD4linux.MailFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.IconBar = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.IconBarLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.IconBarSize = ConfigSlider(default = 20,  increment = 1, limits = (10, 150))
LCD4linux.IconBarPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.IconBarAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.IconBarSplit = ConfigYesNo(default = False)
LCD4linux.IconBarType = ConfigSelection(choices = DirType, default="0")
LCD4linux.IconBarPopup = ConfigSelection(choices = [("0", _("off"))] + ScreenSet, default="0")
LCD4linux.IconBarPopupLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Sun = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.SunLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.SunSize = ConfigSlider(default = 20,  increment = 1, limits = (5, 150))
LCD4linux.SunPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.SunAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.SunSplit = ConfigYesNo(default = False)
LCD4linux.SunColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.SunBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.SunShadow = ConfigYesNo(default = False)
LCD4linux.SunFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.SunType = ConfigSelection(choices = DirType, default="2")
LCD4linux.Fritz = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.FritzLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.FritzSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.FritzPos = ConfigSlider(default = 130,  increment = 2, limits = (0, 1024))
LCD4linux.FritzAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.FritzColor = ConfigSelection(choices = Farbe, default="yellow")
LCD4linux.FritzBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.FritzType = ConfigSelection(choices = FritzType, default="TL")
LCD4linux.FritzPicSize = ConfigSlider(default = 100,  increment = 1, limits = (10, 1024))
LCD4linux.FritzPicPos = ConfigSlider(default = 30,  increment = 2, limits = (0, 1024))
LCD4linux.FritzPicAlign = ConfigSlider(default = 0,  increment = 10, limits = (0, 1024))
LCD4linux.FritzShadow = ConfigYesNo(default = False)
LCD4linux.FritzFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Picon = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.PiconLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.PiconPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.PiconSize = ConfigSlider(default = 200,  increment = 10, limits = (10, 1024))
LCD4linux.PiconFullScreen = ConfigYesNo(default = False)
LCD4linux.PiconAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.PiconSplit = ConfigYesNo(default = False)
LCD4linux.PiconTextSize = ConfigSlider(default = 30,  increment = 2, limits = (10, 150))
LCD4linux.PiconPath = ConfigText(default="/picon/", fixed_size=False, visible_width=50)
LCD4linux.PiconPathAlt = ConfigText(default="/media/hdd/picon/", fixed_size=False, visible_width=50)
LCD4linux.PiconTransparenz = ConfigSelection(choices = [("0", _("no")), ("2", _("yes (32bit)"))], default="2")
LCD4linux.PiconCache = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Picon2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Picon2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Picon2Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.Picon2Size = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.Picon2FullScreen = ConfigYesNo(default = False)
LCD4linux.Picon2Align = ConfigSelection(choices = AlignType, default="1")
LCD4linux.Picon2Split = ConfigYesNo(default = False)
LCD4linux.Picon2TextSize = ConfigSlider(default = 30,  increment = 2, limits = (10, 150))
LCD4linux.Picon2Path = ConfigText(default="/usr/share/enigma2/picon/", fixed_size=False, visible_width=50)
LCD4linux.Picon2PathAlt = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Picon2Cache = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Clock = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.ClockLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.ClockType = ConfigSelection(choices = ClockType, default="12")
LCD4linux.ClockSpacing = ConfigSelectionNumber(0, 3, 1, default = 2)
LCD4linux.ClockAnalog = ConfigSelectionNumber(1, 6, 1, default = 1)
LCD4linux.ClockSize = ConfigSlider(default = 70,  increment = 2, limits = (10, 400))
LCD4linux.ClockPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.ClockAlign = ConfigSelection(choices = AlignType, default="2")
LCD4linux.ClockSplit = ConfigYesNo(default = False)
LCD4linux.ClockColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.ClockShadow = ConfigYesNo(default = False)
LCD4linux.ClockFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Clock2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Clock2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Clock2Type = ConfigSelection(choices = ClockType, default="12")
LCD4linux.Clock2Spacing = ConfigSelectionNumber(0, 3, 1, default = 0)
LCD4linux.Clock2Analog = ConfigSelectionNumber(1, 6, 1, default = 1)
LCD4linux.Clock2Size = ConfigSlider(default = 70,  increment = 2, limits = (10, 400))
LCD4linux.Clock2Pos = ConfigSlider(default = 150,  increment = 2, limits = (0, 1024))
LCD4linux.Clock2Align = ConfigSelection(choices = AlignType, default="1")
LCD4linux.Clock2Split = ConfigYesNo(default = False)
LCD4linux.Clock2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.Clock2Shadow = ConfigYesNo(default = False)
LCD4linux.Clock2Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.Channel = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.ChannelLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.ChannelSize = ConfigSlider(default = 50,  increment = 2, limits = (10, 300))
LCD4linux.ChannelPos = ConfigSlider(default = 10,  increment = 2, limits = (0, 1024))
LCD4linux.ChannelLines = ConfigSelectionNumber(1, 9, 1, default = 1)
LCD4linux.ChannelAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.ChannelSplit = ConfigYesNo(default = False)
LCD4linux.ChannelColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.ChannelShadow = ConfigYesNo(default = False)
LCD4linux.ChannelFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.ChannelNum = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.ChannelNumLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.ChannelNumSize = ConfigSlider(default = 60,  increment = 2, limits = (10, 300))
LCD4linux.ChannelNumPos = ConfigSlider(default = 10,  increment = 2, limits = (0, 1024))
LCD4linux.ChannelNumAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.ChannelNumShadow = ConfigYesNo(default = False)
LCD4linux.ChannelNumColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.ChannelNumBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.ChannelNumFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Desc = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.DescLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.DescType = ConfigSelection(choices = DescriptionType, default="01")
LCD4linux.DescSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.DescLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.DescPos = ConfigSlider(default = 130,  increment = 2, limits = (0, 1024))
LCD4linux.DescAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.DescSplit = ConfigYesNo(default = False)
LCD4linux.DescColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.DescShadow = ConfigYesNo(default = False)
LCD4linux.DescFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Prog = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.ProgLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.ProgType = ConfigSelection(choices = [("1", _("Time+Info")), ("2", _("Info")), ("3", _("Time+Duration+Info"))], default="2")
LCD4linux.ProgSize = ConfigSlider(default = 43,  increment = 1, limits = (10, 150))
LCD4linux.ProgLines = ConfigSelectionNumber(1, 9, 1, default = 1)
LCD4linux.ProgPos = ConfigSlider(default = 150,  increment = 2, limits = (0, 1024))
LCD4linux.ProgAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.ProgSplit = ConfigYesNo(default = False)
LCD4linux.ProgColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.ProgShadow = ConfigYesNo(default = False)
LCD4linux.ProgFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.ProgNext = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.ProgNextLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.ProgNextType = ConfigSelection(choices = [("1", _("Time+Info")), ("2", _("Info")), ("3", _("Time+Length+Info")), ("4", _("Mini-EPG"))], default="1")
LCD4linux.ProgNextSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.ProgNextLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.ProgNextPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.ProgNextAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.ProgNextSplit = ConfigYesNo(default = False)
LCD4linux.ProgNextColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.ProgNextShadow = ConfigYesNo(default = False)
LCD4linux.ProgNextFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Progress = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.ProgressLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.ProgressType = ConfigSelection(choices = ProgressType, default="21")
LCD4linux.ProgressSize = ConfigSlider(default = 25,  increment = 1, limits = (5, 100))
LCD4linux.ProgressAlign = ConfigSelection(choices = [("0", _("half left")), ("1", _("center")), ("2", _("half right"))], default="1")
LCD4linux.ProgressPos = ConfigSlider(default = 210,  increment = 2, limits = (0, 1024))
LCD4linux.ProgressColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.ProgressShadow = ConfigYesNo(default = False)
LCD4linux.ProgressShadow2 = ConfigYesNo(default = False)
LCD4linux.Sat = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.SatLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.SatSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.SatPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.SatAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.SatSplit = ConfigYesNo(default = False)
LCD4linux.SatColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.SatType = ConfigSelection(choices = [("0", _("Position")), ("1", _("Name")), ("2", _("Picon")), ("2A", _("Picon+Position left")), ("2B", _("Picon+Position below")), ("2C", _("Picon+Position right"))], default="1")
LCD4linux.SatPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.SatShadow = ConfigYesNo(default = False)
LCD4linux.SatFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Prov = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.ProvLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.ProvSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.ProvPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.ProvAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.ProvSplit = ConfigYesNo(default = False)
LCD4linux.ProvColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.ProvType = ConfigSelection(choices = [("1", _("Name")), ("2", _("Picon"))], default="1")
LCD4linux.ProvPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.ProvShadow = ConfigYesNo(default = False)
LCD4linux.ProvFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Info = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.InfoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.InfoTuner = ConfigSelection(choices = [("0", _("no")), ("A", _("db")), ("B", _("%")), ("AB", _("db + %")), ("ABC", _("db + % + BER")), ("AC", _("db + BER")), ("BC", _("% + BER"))], default="0")
LCD4linux.InfoSensor = ConfigSelection(choices = InfoSensor, default="0")
LCD4linux.InfoCPU = ConfigSelection(choices = InfoCPU, default="0")
LCD4linux.InfoSize = ConfigSlider(default = 20,  increment = 1, limits = (10, 150))
LCD4linux.InfoPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.InfoAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.InfoSplit = ConfigYesNo(default = False)
LCD4linux.InfoLines = ConfigSelectionNumber(1, 9, 1, default = 1)
LCD4linux.InfoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.InfoShadow = ConfigYesNo(default = False)
LCD4linux.InfoFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Signal = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.SignalLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.SignalSize = ConfigSlider(default = 15,  increment = 1, limits = (5, 150))
LCD4linux.SignalPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.SignalAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.SignalSplit = ConfigYesNo(default = False)
LCD4linux.SignalColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.SignalGradient = ConfigYesNo(default = False)
LCD4linux.SignalMin = ConfigSlider(default = 40,  increment = 5, limits = (0, 50))
LCD4linux.SignalMax = ConfigSlider(default = 90,  increment = 5, limits = (50, 100))
LCD4linux.Tuner = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.TunerLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.TunerSize = ConfigSlider(default = 48,  increment = 1, limits = (10, 150))
LCD4linux.TunerPos = ConfigSlider(default = 70,  increment = 2, limits = (0, 1024))
LCD4linux.TunerAlign = ConfigSelection(choices = AlignType, default="2")
LCD4linux.TunerSplit = ConfigYesNo(default = False)
LCD4linux.TunerType = ConfigSelection(choices = DirType, default="0")
LCD4linux.TunerActive = ConfigYesNo(default = False)
LCD4linux.TunerFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Vol = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.VolLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.VolSize = ConfigSlider(default = 22,  increment = 1, limits = (5, 150))
LCD4linux.VolPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.VolAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.VolSplit = ConfigYesNo(default = False)
LCD4linux.VolColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.VolShadow = ConfigYesNo(default = False)
LCD4linux.Ping = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.PingLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.PingSize = ConfigSlider(default = 15,  increment = 2, limits = (10, 100))
LCD4linux.PingPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.PingAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.PingSplit = ConfigYesNo(default = False)
LCD4linux.PingColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.PingShadow = ConfigYesNo(default = False)
LCD4linux.PingFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.PingShow = ConfigSelection(choices = [("0", _("Online+Offline")), ("1", _("Online")), ("2", _("Offline"))], default="0")
LCD4linux.PingType = ConfigSelection(choices = DirType, default="0")
LCD4linux.PingTimeout = ConfigSlider(default = 50,  increment = 5, limits = (5, 1000))
LCD4linux.PingName1 = ConfigText(default="Internet:www.google.de", fixed_size=False)
LCD4linux.PingName2 = ConfigText(default="", fixed_size=False)
LCD4linux.PingName3 = ConfigText(default="", fixed_size=False)
LCD4linux.PingName4 = ConfigText(default="", fixed_size=False)
LCD4linux.PingName5 = ConfigText(default="", fixed_size=False)
LCD4linux.AV = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.AVLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.AVSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.AVPos = ConfigSlider(default = 100,  increment = 2, limits = (0, 1024))
LCD4linux.AVAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.AVSplit = ConfigYesNo(default = False)
LCD4linux.AVColor = ConfigSelection(choices = Farbe, default="gold")
LCD4linux.AVShadow = ConfigYesNo(default = False)
LCD4linux.AVType = ConfigSelection(choices = [("1", _("one line")), ("2", _("two lines"))], default="1")
LCD4linux.AVFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Bitrate = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.BitrateLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.BitrateSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.BitratePos = ConfigSlider(default = 100,  increment = 2, limits = (0, 1024))
LCD4linux.BitrateAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.BitrateSplit = ConfigYesNo(default = False)
LCD4linux.BitrateColor = ConfigSelection(choices = Farbe, default="gold")
LCD4linux.BitrateShadow = ConfigYesNo(default = False)
LCD4linux.BitrateFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Dev = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.DevLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.DevSize = ConfigSlider(default = 15,  increment = 2, limits = (10, 300))
LCD4linux.DevPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.DevAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.DevSplit = ConfigYesNo(default = False)
LCD4linux.DevColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.DevShadow = ConfigYesNo(default = False)
LCD4linux.DevFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.DevType = ConfigSelection(choices = DirType, default="0")
LCD4linux.DevExtra = ConfigSelection(choices = [("0", _("no")), ("RAM", _("Memory"))], default="RAM")
LCD4linux.DevName1 = ConfigText(default="/media/hdd", fixed_size=False)
LCD4linux.DevName2 = ConfigText(default="", fixed_size=False)
LCD4linux.DevName3 = ConfigText(default="", fixed_size=False)
LCD4linux.DevName4 = ConfigText(default="", fixed_size=False)
LCD4linux.DevName5 = ConfigText(default="", fixed_size=False)
LCD4linux.Hdd = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.HddLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.HddSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.HddPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.HddAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.HddSplit = ConfigYesNo(default = False)
LCD4linux.HddType = ConfigSelection(choices = HddType, default="0")
LCD4linux.Timer = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.TimerLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.TimerSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.TimerLines = ConfigSelectionNumber(1, 20, 1, default = 1)
LCD4linux.TimerType = ConfigSelection(choices = [("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.TimerPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.TimerAlign = ConfigSelection(choices = [("0", _("left")), ("2", _("half right"))], default="0")
LCD4linux.TimerSplit = ConfigYesNo(default = False)
LCD4linux.TimerColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.TimerShadow = ConfigYesNo(default = False)
LCD4linux.TimerFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Wetter = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.WetterLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.WetterPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.WetterAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.WetterSplit = ConfigYesNo(default = False)
LCD4linux.WetterZoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.WetterType = ConfigSelection(choices = WetterType, default="1")
LCD4linux.WetterColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.WetterShadow = ConfigYesNo(default = False)
LCD4linux.WetterFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.Wetter2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Wetter2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Wetter2Pos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.Wetter2Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.Wetter2Split = ConfigYesNo(default = False)
LCD4linux.Wetter2Zoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.Wetter2Type = ConfigSelection(choices = WetterType, default="1")
LCD4linux.Wetter2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.Wetter2Shadow = ConfigYesNo(default = False)
LCD4linux.Wetter2Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.Meteo = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MeteoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MeteoPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.MeteoAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MeteoSplit = ConfigYesNo(default = False)
LCD4linux.MeteoZoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.MeteoType = ConfigSelection(choices = MeteoType, default="1")
LCD4linux.MeteoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.Moon = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MoonLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MoonSize = ConfigSlider(default = 60,  increment = 2, limits = (10, 300))
LCD4linux.MoonPos = ConfigSlider(default = 10,  increment = 2, limits = (0, 1024))
LCD4linux.MoonAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MoonSplit = ConfigYesNo(default = False)
LCD4linux.MoonColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="white")
LCD4linux.MoonShadow = ConfigYesNo(default = False)
LCD4linux.MoonFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.NetAtmoCO2Min = ConfigSlider(default = 200,  increment = 100, limits = (0, 1000))
LCD4linux.NetAtmoCO2Max = ConfigSlider(default = 1500,  increment = 100, limits = (500, 10000))
LCD4linux.NetAtmo = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.NetAtmoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.NetAtmoPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.NetAtmoAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.NetAtmoSplit = ConfigYesNo(default = False)
LCD4linux.NetAtmoType = ConfigSelection(choices = NetatmoType, default="THCPN")
LCD4linux.NetAtmoType2 = ConfigSelection(choices = DirType, default="0")
LCD4linux.NetAtmoSize = ConfigSlider(default = 30,  increment = 1, limits = (10, 100))
LCD4linux.NetAtmoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.NetAtmoShadow = ConfigYesNo(default = False)
LCD4linux.NetAtmoFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.NetAtmoCO2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.NetAtmoCO2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.NetAtmoCO2Size = ConfigSlider(default = 30,  increment = 1, limits = (5, 500))
LCD4linux.NetAtmoCO2Len = ConfigSlider(default = 200,  increment = 5, limits = (100, 1024))
LCD4linux.NetAtmoCO2Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.NetAtmoCO2Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.NetAtmoCO2Split = ConfigYesNo(default = False)
LCD4linux.NetAtmoCO2Type = ConfigSelection(choices = CO2Type, default="1")
LCD4linux.NetAtmoIDX = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.NetAtmoIDXLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.NetAtmoIDXSize = ConfigSlider(default = 30,  increment = 1, limits = (5, 500))
LCD4linux.NetAtmoIDXLen = ConfigSlider(default = 200,  increment = 5, limits = (100, 1024))
LCD4linux.NetAtmoIDXPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.NetAtmoIDXAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.NetAtmoIDXSplit = ConfigYesNo(default = False)
LCD4linux.NetAtmoIDXType = ConfigSelection(choices = CO2Type, default="1")
LCD4linux.OSCAM = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.OSCAMLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.OSCAMFile = ConfigText(default="/tmp/.oscam/oscam.lcd", fixed_size=False)
LCD4linux.OSCAMSize = ConfigSlider(default = 10,  increment = 1, limits = (9, 50))
LCD4linux.OSCAMPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.OSCAMAlign = ConfigSelection(choices = [("0", _("left")), ("2", _("right"))], default="0")
LCD4linux.OSCAMSplit = ConfigYesNo(default = False)
LCD4linux.OSCAMColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.OSCAMBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="black")
LCD4linux.ECM = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.ECMLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.ECMSize = ConfigSlider(default = 10,  increment = 1, limits = (9, 50))
LCD4linux.ECMPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.ECMAlign = ConfigSelection(choices = [("0", _("left")), ("2", _("right"))], default="0")
LCD4linux.ECMSplit = ConfigYesNo(default = False)
LCD4linux.ECMColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.ECMBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="black")
LCD4linux.Text = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.TextLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.TextFile = ConfigText(default="/tmp/lcd4linux.txt", fixed_size=False, visible_width=50)
LCD4linux.TextSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 300))
LCD4linux.TextFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.TextPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.TextAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.TextShadow = ConfigYesNo(default = False)
LCD4linux.TextColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.TextBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.Text2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Text2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Text2File = ConfigText(default="/tmp/lcd4linux.txt", fixed_size=False, visible_width=50)
LCD4linux.Text2Size = ConfigSlider(default = 32,  increment = 1, limits = (10, 300))
LCD4linux.Text2Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.Text2Pos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.Text2Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.Text2Shadow = ConfigYesNo(default = False)
LCD4linux.Text2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.Text2BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.Text3 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Text3LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Text3File = ConfigText(default="/tmp/lcd4linux.txt", fixed_size=False, visible_width=50)
LCD4linux.Text3Size = ConfigSlider(default = 32,  increment = 1, limits = (10, 300))
LCD4linux.Text3Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.Text3Pos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.Text3Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.Text3Shadow = ConfigYesNo(default = False)
LCD4linux.Text3Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.Text3BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.HTTP = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.HTTPLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.HTTPURL = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.HTTPSize = ConfigSlider(default = 20,  increment = 1, limits = (10, 300))
LCD4linux.HTTPPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.HTTPAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.HTTPColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.HTTPBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.HTTPShadow = ConfigYesNo(default = False)
LCD4linux.HTTPFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.WWWTime = ConfigSelection(choices = [("10", _("60min")), ("10,40", _("30min"))], default="10")
LCD4linux.WWW1 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.WWW1LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.WWW1Size = ConfigSlider(default = 200,  increment = 1, limits = (50, 1024))
LCD4linux.WWW1Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.WWW1Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.WWW1url = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.WWW1w = ConfigSlider(default = 800,  increment = 50, limits = (600, 2000))
LCD4linux.WWW1h = ConfigSlider(default = 600,  increment = 50, limits = (100, 2000))
LCD4linux.WWW1CutX = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.WWW1CutY = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.WWW1CutW = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.WWW1CutH = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.Bild = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.BildLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.BildFile = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.BildSize = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.BildPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.BildAlign = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.BildQuick = ConfigYesNo(default = False)
LCD4linux.BildTransp = ConfigYesNo(default = False)
LCD4linux.Bild2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Bild2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Bild2File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.Bild2Size = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.Bild2Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.Bild2Align = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.Bild2Quick = ConfigYesNo(default = False)
LCD4linux.Bild2Transp = ConfigYesNo(default = False)
LCD4linux.Bild3 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Bild3LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Bild3File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.Bild3Size = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.Bild3Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.Bild3Align = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.Bild3Quick = ConfigYesNo(default = False)
LCD4linux.Bild3Transp = ConfigYesNo(default = False)
LCD4linux.Bild4 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Bild4LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Bild4File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.Bild4Size = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.Bild4Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.Bild4Align = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.Bild4Quick = ConfigYesNo(default = False)
LCD4linux.Bild4Transp = ConfigYesNo(default = False)
LCD4linux.TV = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.TVLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.TVType = ConfigSelection(choices = [("0", _("TV")), ("1", _("TV+OSD"))], default="0")
LCD4linux.Box1 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Box1LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Box1x1 = ConfigSlider(default = 10,  increment = 1, limits = (0, 1024))
LCD4linux.Box1y1 = ConfigSlider(default = 10,  increment = 1, limits = (0, 1024))
LCD4linux.Box1x2 = ConfigSlider(default = 200,  increment = 1, limits = (0, 1024))
LCD4linux.Box1y2 = ConfigSlider(default = 1,  increment = 1, limits = (0, 1024))
LCD4linux.Box1Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.Box1BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.Box2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.Box2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.Box2x1 = ConfigSlider(default = 20,  increment = 1, limits = (0, 1024))
LCD4linux.Box2y1 = ConfigSlider(default = 20,  increment = 1, limits = (0, 1024))
LCD4linux.Box2x2 = ConfigSlider(default = 200,  increment = 1, limits = (0, 1024))
LCD4linux.Box2y2 = ConfigSlider(default = 1,  increment = 1, limits = (0, 1024))
LCD4linux.Box2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.Box2BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.MPHelligkeit = ConfigSelectionNumber(0, 10, 1, default = 5)
LCD4linux.MPHelligkeit2 = ConfigSelectionNumber(0, 10, 1, default = 5)
LCD4linux.MPHelligkeit3 = ConfigSelectionNumber(0, 10, 1, default = 5)
LCD4linux.MPScreenMax = ConfigSelection(choices = ScreenUse, default="1")
LCD4linux.MPLCDBild1 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.MPLCDBild2 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.MPLCDBild3 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.MPLCDColor1 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.MPLCDColor2 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.MPLCDColor3 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.MPDesc = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.MPDescLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPDescType = ConfigSelection(choices = DescriptionType, default="12")
LCD4linux.MPDescSize = ConfigSlider(default = 31,  increment = 1, limits = (10, 150))
LCD4linux.MPDescLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.MPDescPos = ConfigSlider(default = 130,  increment = 2, limits = (0, 1024))
LCD4linux.MPDescAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.MPDescSplit = ConfigYesNo(default = False)
LCD4linux.MPDescColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPDescShadow = ConfigYesNo(default = False)
LCD4linux.MPDescFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPTitle = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPTitleLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPTitleSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.MPTitleLines = ConfigSelectionNumber(1, 9, 1, default = 2)
LCD4linux.MPTitlePos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPTitleAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPTitleSplit = ConfigYesNo(default = False)
LCD4linux.MPTitleColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPTitleShadow = ConfigYesNo(default = False)
LCD4linux.MPTitleFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPComm = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPCommLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPCommSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.MPCommLines = ConfigSelectionNumber(1, 9, 1, default = 3)
LCD4linux.MPCommPos = ConfigSlider(default = 130,  increment = 2, limits = (0, 1024))
LCD4linux.MPCommAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.MPCommSplit = ConfigYesNo(default = False)
LCD4linux.MPCommColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPCommShadow = ConfigYesNo(default = False)
LCD4linux.MPCommFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPChannel = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPChannelLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPChannelSize = ConfigSlider(default = 50,  increment = 2, limits = (10, 300))
LCD4linux.MPChannelPos = ConfigSlider(default = 10,  increment = 2, limits = (0, 1024))
LCD4linux.MPChannelLines = ConfigSelectionNumber(1, 9, 1, default = 1)
LCD4linux.MPChannelAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.MPChannelSplit = ConfigYesNo(default = False)
LCD4linux.MPChannelColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPChannelShadow = ConfigYesNo(default = False)
LCD4linux.MPChannelFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPProgress = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.MPProgressLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPProgressType = ConfigSelection(choices = ProgressType, default="61")
LCD4linux.MPProgressSize = ConfigSlider(default = 23,  increment = 1, limits = (5, 100))
LCD4linux.MPProgressPos = ConfigSlider(default = 6,  increment = 2, limits = (0, 1024))
LCD4linux.MPProgressAlign = ConfigSelection(choices = [("0", _("half left")), ("1", _("center")), ("2", _("half right"))], default="0")
LCD4linux.MPProgressColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPProgressShadow = ConfigYesNo(default = False)
LCD4linux.MPProgressShadow2 = ConfigYesNo(default = False)
LCD4linux.MPVol = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPVolLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPVolSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.MPVolPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPVolAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPVolSplit = ConfigYesNo(default = False)
LCD4linux.MPVolColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPVolShadow = ConfigYesNo(default = False)
LCD4linux.MPPing = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPPingLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPPingSize = ConfigSlider(default = 15,  increment = 2, limits = (10, 100))
LCD4linux.MPPingPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.MPPingAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPPingSplit = ConfigYesNo(default = False)
LCD4linux.MPPingColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPPingShadow = ConfigYesNo(default = False)
LCD4linux.MPPingFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPPingShow = ConfigSelection(choices = [("0", _("Online+Offline")), ("1", _("Online")), ("2", _("Offline"))], default="0")
LCD4linux.MPPingType = ConfigSelection(choices = DirType, default="0")
LCD4linux.MPPingTimeout = ConfigSlider(default = 50,  increment = 5, limits = (5, 1000))
LCD4linux.MPPingName1 = ConfigText(default="Internet:www.google.de", fixed_size=False)
LCD4linux.MPPingName2 = ConfigText(default="", fixed_size=False)
LCD4linux.MPPingName3 = ConfigText(default="", fixed_size=False)
LCD4linux.MPPingName4 = ConfigText(default="", fixed_size=False)
LCD4linux.MPPingName5 = ConfigText(default="", fixed_size=False)
LCD4linux.MPClock = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.MPClockLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPClockType = ConfigSelection(choices = ClockType, default="12")
LCD4linux.MPClockSpacing = ConfigSelectionNumber(0, 3, 1, default = 0)
LCD4linux.MPClockAnalog = ConfigSelectionNumber(1, 6, 1, default = 1)
LCD4linux.MPClockSize = ConfigSlider(default = 70,  increment = 2, limits = (10, 400))
LCD4linux.MPClockPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPClockAlign = ConfigSelection(choices = AlignType, default="2")
LCD4linux.MPClockSplit = ConfigYesNo(default = False)
LCD4linux.MPClockColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPClockShadow = ConfigYesNo(default = False)
LCD4linux.MPClockFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPClock2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPClock2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPClock2Type = ConfigSelection(choices = ClockType, default="12")
LCD4linux.MPClock2Spacing = ConfigSelectionNumber(0, 3, 1, default = 0)
LCD4linux.MPClock2Analog = ConfigSelectionNumber(1, 6, 1, default = 1)
LCD4linux.MPClock2Size = ConfigSlider(default = 70,  increment = 2, limits = (10, 400))
LCD4linux.MPClock2Pos = ConfigSlider(default = 150,  increment = 2, limits = (0, 1024))
LCD4linux.MPClock2Align = ConfigSelection(choices = AlignType, default="1")
LCD4linux.MPClock2Split = ConfigYesNo(default = False)
LCD4linux.MPClock2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPClock2Shadow = ConfigYesNo(default = False)
LCD4linux.MPClock2Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPTuner = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.MPTunerLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPTunerSize = ConfigSlider(default = 48,  increment = 1, limits = (10, 150))
LCD4linux.MPTunerPos = ConfigSlider(default = 70,  increment = 2, limits = (0, 1024))
LCD4linux.MPTunerAlign = ConfigSelection(choices = AlignType, default="2")
LCD4linux.MPTunerSplit = ConfigYesNo(default = False)
LCD4linux.MPTunerType = ConfigSelection(choices = DirType, default="0")
LCD4linux.MPTunerActive = ConfigYesNo(default = False)
LCD4linux.MPTunerFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPInfo = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPInfoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPInfoSensor = ConfigSelection(choices = InfoSensor, default="0")
LCD4linux.MPInfoCPU = ConfigSelection(choices = InfoCPU, default="0")
LCD4linux.MPInfoSize = ConfigSlider(default = 20,  increment = 1, limits = (10, 150))
LCD4linux.MPInfoPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPInfoAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.MPInfoSplit = ConfigYesNo(default = False)
LCD4linux.MPInfoLines = ConfigSelectionNumber(1, 9, 1, default = 1)
LCD4linux.MPInfoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPInfoShadow = ConfigYesNo(default = False)
LCD4linux.MPInfoFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPAV = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPAVLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPAVSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.MPAVPos = ConfigSlider(default = 100,  increment = 2, limits = (0, 1024))
LCD4linux.MPAVAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPAVSplit = ConfigYesNo(default = False)
LCD4linux.MPAVColor = ConfigSelection(choices = Farbe, default="gold")
LCD4linux.MPAVShadow = ConfigYesNo(default = False)
LCD4linux.MPAVType = ConfigSelection(choices = [("1", _("one line")), ("2", _("two lines"))], default="1")
LCD4linux.MPAVFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPBitrate = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPBitrateLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPBitrateSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.MPBitratePos = ConfigSlider(default = 100,  increment = 2, limits = (0, 1024))
LCD4linux.MPBitrateAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPBitrateSplit = ConfigYesNo(default = False)
LCD4linux.MPBitrateColor = ConfigSelection(choices = Farbe, default="gold")
LCD4linux.MPBitrateShadow = ConfigYesNo(default = False)
LCD4linux.MPBitrateFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPDev = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPDevLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPDevSize = ConfigSlider(default = 15,  increment = 2, limits = (10, 300))
LCD4linux.MPDevPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.MPDevAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPDevSplit = ConfigYesNo(default = False)
LCD4linux.MPDevColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPDevShadow = ConfigYesNo(default = False)
LCD4linux.MPDevFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPDevType = ConfigSelection(choices = DirType, default="0")
LCD4linux.MPDevExtra = ConfigSelection(choices = [("0", _("no")), ("RAM", _("Memory"))], default="RAM")
LCD4linux.MPDevName1 = ConfigText(default="/media/hdd", fixed_size=False)
LCD4linux.MPDevName2 = ConfigText(default="", fixed_size=False)
LCD4linux.MPDevName3 = ConfigText(default="", fixed_size=False)
LCD4linux.MPDevName4 = ConfigText(default="", fixed_size=False)
LCD4linux.MPDevName5 = ConfigText(default="", fixed_size=False)
LCD4linux.MPHdd = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPHddLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPHddSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.MPHddPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.MPHddAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.MPHddSplit = ConfigYesNo(default = False)
LCD4linux.MPHddType = ConfigSelection(choices = HddType, default="0")
LCD4linux.MPTimer = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPTimerLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPTimerSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.MPTimerLines = ConfigSelectionNumber(1, 20, 1, default = 1)
LCD4linux.MPTimerType = ConfigSelection(choices = [("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.MPTimerPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPTimerAlign = ConfigSelection(choices = [("0", _("left")), ("2", _("half right"))], default="0")
LCD4linux.MPTimerSplit = ConfigYesNo(default = False)
LCD4linux.MPTimerColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPTimerShadow = ConfigYesNo(default = False)
LCD4linux.MPTimerFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPWetter = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPWetterLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPWetterPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.MPWetterAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPWetterSplit = ConfigYesNo(default = False)
LCD4linux.MPWetterZoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.MPWetterType = ConfigSelection(choices = WetterType, default="1")
LCD4linux.MPWetterColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPWetterShadow = ConfigYesNo(default = False)
LCD4linux.MPWetterFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPWetter2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPWetter2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPWetter2Pos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.MPWetter2Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPWetter2Split = ConfigYesNo(default = False)
LCD4linux.MPWetter2Zoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.MPWetter2Type = ConfigSelection(choices = WetterType, default="1")
LCD4linux.MPWetter2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPWetter2Shadow = ConfigYesNo(default = False)
LCD4linux.MPWetter2Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPMeteo = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPMeteoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPMeteoPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.MPMeteoAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPMeteoSplit = ConfigYesNo(default = False)
LCD4linux.MPMeteoZoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.MPMeteoType = ConfigSelection(choices = MeteoType, default="1")
LCD4linux.MPMeteoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPMoon = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPMoonLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPMoonSize = ConfigSlider(default = 60,  increment = 2, limits = (10, 300))
LCD4linux.MPMoonPos = ConfigSlider(default = 10,  increment = 2, limits = (0, 1024))
LCD4linux.MPMoonAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPMoonSplit = ConfigYesNo(default = False)
LCD4linux.MPMoonColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="white")
LCD4linux.MPMoonShadow = ConfigYesNo(default = False)
LCD4linux.MPMoonFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPNetAtmo = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPNetAtmoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPNetAtmoPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.MPNetAtmoAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPNetAtmoSplit = ConfigYesNo(default = False)
LCD4linux.MPNetAtmoType = ConfigSelection(choices = NetatmoType, default="THCPN")
LCD4linux.MPNetAtmoType2 = ConfigSelection(choices = DirType, default="0")
LCD4linux.MPNetAtmoSize = ConfigSlider(default = 30,  increment = 1, limits = (10, 100))
LCD4linux.MPNetAtmoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPNetAtmoShadow = ConfigYesNo(default = False)
LCD4linux.MPNetAtmoFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPNetAtmoCO2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPNetAtmoCO2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPNetAtmoCO2Size = ConfigSlider(default = 30,  increment = 1, limits = (5, 500))
LCD4linux.MPNetAtmoCO2Len = ConfigSlider(default = 200,  increment = 5, limits = (100, 1024))
LCD4linux.MPNetAtmoCO2Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPNetAtmoCO2Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPNetAtmoCO2Split = ConfigYesNo(default = False)
LCD4linux.MPNetAtmoCO2Type = ConfigSelection(choices = CO2Type, default="1")
LCD4linux.MPNetAtmoIDX = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPNetAtmoIDXLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPNetAtmoIDXSize = ConfigSlider(default = 30,  increment = 1, limits = (5, 500))
LCD4linux.MPNetAtmoIDXLen = ConfigSlider(default = 200,  increment = 5, limits = (100, 1024))
LCD4linux.MPNetAtmoIDXPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPNetAtmoIDXAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPNetAtmoIDXSplit = ConfigYesNo(default = False)
LCD4linux.MPNetAtmoIDXType = ConfigSelection(choices = CO2Type, default="1")
LCD4linux.MPBild = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPBildLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPBildFile = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.MPBildSize = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.MPBildPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPBildAlign = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.MPBildQuick = ConfigYesNo(default = False)
LCD4linux.MPBildTransp = ConfigYesNo(default = False)
LCD4linux.MPBild2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPBild2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPBild2File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.MPBild2Size = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.MPBild2Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPBild2Align = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.MPBild2Quick = ConfigYesNo(default = False)
LCD4linux.MPBild2Transp = ConfigYesNo(default = False)
LCD4linux.MPText = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPTextLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPTextFile = ConfigText(default="/tmp/lcd4linux.txt", fixed_size=False, visible_width=50)
LCD4linux.MPTextSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 300))
LCD4linux.MPTextFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPTextPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.MPTextAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPTextShadow = ConfigYesNo(default = False)
LCD4linux.MPTextColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPTextBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.MPCover = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPCoverLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPCoverPath1 = ConfigText(default="/tmp", fixed_size=False, visible_width=50)
LCD4linux.MPCoverPath2 = ConfigText(default="/tmp", fixed_size=False, visible_width=50)
LCD4linux.MPCoverFile = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.MPCoverSize = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.MPCoverSizeH = ConfigSlider(default = 400,  increment = 10, limits = (10, 800))
LCD4linux.MPCoverPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPCoverAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPCoverGoogle = ConfigSelection(choices = [("0", _("no")), ("1", _("yes")), ("2", _("yes except records"))], default="1")
LCD4linux.MPCoverTransp = ConfigYesNo(default = False)
LCD4linux.MPCoverPiconFirst = ConfigYesNo(default = True)
LCD4linux.MPOSCAM = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPOSCAMLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPOSCAMSize = ConfigSlider(default = 10,  increment = 1, limits = (9, 50))
LCD4linux.MPOSCAMPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.MPOSCAMAlign = ConfigSelection(choices = [("0", _("left")), ("2", _("right"))], default="0")
LCD4linux.MPOSCAMSplit = ConfigYesNo(default = False)
LCD4linux.MPOSCAMColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPOSCAMBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="black")
LCD4linux.MPMail = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPMailLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPMailSize = ConfigSlider(default = 12,  increment = 1, limits = (5, 150))
LCD4linux.MPMailPos = ConfigSlider(default = 30,  increment = 2, limits = (0, 1024))
LCD4linux.MPMailAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPMailSplit = ConfigYesNo(default = False)
LCD4linux.MPMailColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPMailBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.MPMailKonto = ConfigSelection(choices = MailKonto, default="1")
LCD4linux.MPMailLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.MPMailType = ConfigSelection(choices = MailType, default="A1")
LCD4linux.MPMailProzent = ConfigSelection(choices = MailProzent, default="50")
LCD4linux.MPMailShadow = ConfigYesNo(default = False)
LCD4linux.MPMailFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPIconBar = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPIconBarLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPIconBarSize = ConfigSlider(default = 20,  increment = 1, limits = (10, 150))
LCD4linux.MPIconBarPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.MPIconBarAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.MPIconBarSplit = ConfigYesNo(default = False)
LCD4linux.MPIconBarType = ConfigSelection(choices = DirType, default="0")
LCD4linux.MPIconBarPopup = ConfigSelection(choices = [("0", _("off"))] + ScreenSet, default="0")
LCD4linux.MPIconBarPopupLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPSun = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPSunLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPSunSize = ConfigSlider(default = 20,  increment = 1, limits = (5, 150))
LCD4linux.MPSunPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.MPSunAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPSunSplit = ConfigYesNo(default = False)
LCD4linux.MPSunColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPSunBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.MPSunShadow = ConfigYesNo(default = False)
LCD4linux.MPSunFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPSunType = ConfigSelection(choices = DirType, default="2")
LCD4linux.MPFritz = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPFritzLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPFritzSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.MPFritzPos = ConfigSlider(default = 130,  increment = 2, limits = (0, 1024))
LCD4linux.MPFritzAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPFritzColor = ConfigSelection(choices = Farbe, default="yellow")
LCD4linux.MPFritzBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.MPFritzType = ConfigSelection(choices = FritzType, default="TL")
LCD4linux.MPFritzPicSize = ConfigSlider(default = 100,  increment = 1, limits = (10, 800))
LCD4linux.MPFritzPicPos = ConfigSlider(default = 30,  increment = 2, limits = (0, 1024))
LCD4linux.MPFritzPicAlign = ConfigSlider(default = 0,  increment = 10, limits = (0, 1024))
LCD4linux.MPFritzShadow = ConfigYesNo(default = False)
LCD4linux.MPFritzFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPCal = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPCalLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPCalPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.MPCalAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPCalSplit = ConfigYesNo(default = False)
LCD4linux.MPCalZoom = ConfigSlider(default = 10,  increment = 1, limits = (3, 50))
LCD4linux.MPCalType = ConfigSelection(choices = CalType, default="0A")
LCD4linux.MPCalTypeE = ConfigSelection(choices = CalTypeE, default="D2")
LCD4linux.MPCalColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPCalBackColor = ConfigSelection(choices = Farbe, default="gray")
LCD4linux.MPCalCaptionColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPCalLayout = ConfigSelection(choices = CalLayout, default="0")
LCD4linux.MPCalShadow = ConfigYesNo(default = False)
LCD4linux.MPCalFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPCalList = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPCalListLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPCalListSize = ConfigSlider(default = 12,  increment = 1, limits = (5, 150))
LCD4linux.MPCalListPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.MPCalListAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.MPCalListSplit = ConfigYesNo(default = False)
LCD4linux.MPCalListLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.MPCalListProzent = ConfigSelection(choices = MailProzent, default="50")
LCD4linux.MPCalListType = ConfigSelection(choices = CalListType, default="C")
LCD4linux.MPCalListColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPCalListShadow = ConfigYesNo(default = False)
LCD4linux.MPCalListFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.MPBox1 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPBox1LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPBox1x1 = ConfigSlider(default = 10,  increment = 1, limits = (0, 1024))
LCD4linux.MPBox1y1 = ConfigSlider(default = 10,  increment = 1, limits = (0, 1024))
LCD4linux.MPBox1x2 = ConfigSlider(default = 200,  increment = 1, limits = (0, 1024))
LCD4linux.MPBox1y2 = ConfigSlider(default = 1,  increment = 1, limits = (0, 1024))
LCD4linux.MPBox1Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPBox1BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.MPBox2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPBox2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPBox2x1 = ConfigSlider(default = 20,  increment = 1, limits = (0, 1024))
LCD4linux.MPBox2y1 = ConfigSlider(default = 20,  increment = 1, limits = (0, 1024))
LCD4linux.MPBox2x2 = ConfigSlider(default = 200,  increment = 1, limits = (0, 1024))
LCD4linux.MPBox2y2 = ConfigSlider(default = 1,  increment = 1, limits = (0, 1024))
LCD4linux.MPBox2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.MPBox2BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.MPRecording = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.MPRecordingLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.MPRecordingType = ConfigSelection(choices = [("1", _("Corner")), ("2", _("Picon"))], default="1")
LCD4linux.MPRecordingSize = ConfigSlider(default = 25,  increment = 1, limits = (10, 100))
LCD4linux.MPRecordingPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.MPRecordingAlign = ConfigSelection(choices = AlignType, default="2")
LCD4linux.MPRecordingSplit = ConfigYesNo(default = False)
LCD4linux.Standby = ConfigSelection(choices = [("0", _("off")), ("1", _("on"))], default="1")
LCD4linux.StandbyScreenMax = ConfigSelection(choices = ScreenUse, default="1")
LCD4linux.StandbyHelligkeit = ConfigSelectionNumber(0, 10, 1, default = 1)
LCD4linux.StandbyHelligkeit2 = ConfigSelectionNumber(0, 10, 1, default = 1)
LCD4linux.StandbyHelligkeit3 = ConfigSelectionNumber(0, 10, 1, default = 1)
LCD4linux.StandbyLCDoff = ConfigClock(default = int(begin) )
LCD4linux.StandbyLCDon = ConfigClock(default = int(begin) )
LCD4linux.StandbyLCDWEoff = ConfigClock(default = int(begin) )
LCD4linux.StandbyLCDWEon = ConfigClock(default = int(begin) )
LCD4linux.StandbyLCDBild1 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.StandbyLCDBild2 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.StandbyLCDBild3 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.StandbyLCDColor1 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.StandbyLCDColor2 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.StandbyLCDColor3 = ConfigSelection(choices = Farbe, default="black")
LCD4linux.StandbyScreenTime = ConfigSelection(choices = [("0", _("off"))] + TimeSelect, default="0")
LCD4linux.StandbyScreenTime2 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.StandbyScreenTime3 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.StandbyScreenTime4 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.StandbyScreenTime5 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.StandbyScreenTime6 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.StandbyScreenTime7 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.StandbyScreenTime8 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.StandbyScreenTime9 = ConfigSelection(choices = TimeSelect, default="1")
LCD4linux.StandbyClock = ConfigSelection(choices = ScreenSelect, default="1")
LCD4linux.StandbyClockLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyClockType = ConfigSelection(choices = ClockType, default="12")
LCD4linux.StandbyClockSpacing = ConfigSelectionNumber(0, 3, 1, default = 0)
LCD4linux.StandbyClockAnalog = ConfigSelectionNumber(1, 6, 1, default = 1)
LCD4linux.StandbyClockSize = ConfigSlider(default = 110,  increment = 2, limits = (10, 400))
LCD4linux.StandbyClockPos = ConfigSlider(default = 100,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyClockAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.StandbyClockSplit = ConfigYesNo(default = False)
LCD4linux.StandbyClockColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyClockShadow = ConfigYesNo(default = False)
LCD4linux.StandbyClockFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyClock2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyClock2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyClock2Type = ConfigSelection(choices = ClockType, default="12")
LCD4linux.StandbyClock2Spacing = ConfigSelectionNumber(0, 3, 1, default = 0)
LCD4linux.StandbyClock2Analog = ConfigSelectionNumber(1, 6, 1, default = 1)
LCD4linux.StandbyClock2Size = ConfigSlider(default = 110,  increment = 2, limits = (10, 400))
LCD4linux.StandbyClock2Pos = ConfigSlider(default = 100,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyClock2Align = ConfigSelection(choices = AlignType, default="1")
LCD4linux.StandbyClock2Split = ConfigYesNo(default = False)
LCD4linux.StandbyClock2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyClock2Shadow = ConfigYesNo(default = False)
LCD4linux.StandbyClock2Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyTimer = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyTimerLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyTimerSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.StandbyTimerLines = ConfigSelectionNumber(1, 20, 1, default = 1)
LCD4linux.StandbyTimerType = ConfigSelection(choices = [("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.StandbyTimerPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyTimerAlign = ConfigSelection(choices = [("0", _("left")), ("2", _("half right"))], default="0")
LCD4linux.StandbyTimerSplit = ConfigYesNo(default = False)
LCD4linux.StandbyTimerColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyTimerShadow = ConfigYesNo(default = False)
LCD4linux.StandbyTimerFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyTuner = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyTunerLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyTunerSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.StandbyTunerPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyTunerAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyTunerSplit = ConfigYesNo(default = False)
LCD4linux.StandbyTunerType = ConfigSelection(choices = DirType, default="0")
LCD4linux.StandbyTunerActive = ConfigYesNo(default = False)
LCD4linux.StandbyTunerFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyInfo = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyInfoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyInfoSensor = ConfigSelection(choices = InfoSensor, default="0")
LCD4linux.StandbyInfoCPU = ConfigSelection(choices = InfoCPU, default="0")
LCD4linux.StandbyInfoSize = ConfigSlider(default = 20,  increment = 1, limits = (10, 150))
LCD4linux.StandbyInfoPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyInfoAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.StandbyInfoSplit = ConfigYesNo(default = False)
LCD4linux.StandbyInfoLines = ConfigSelectionNumber(1, 9, 1, default = 1)
LCD4linux.StandbyInfoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyInfoShadow = ConfigYesNo(default = False)
LCD4linux.StandbyInfoFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyPing = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyPingLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyPingSize = ConfigSlider(default = 15,  increment = 2, limits = (10, 100))
LCD4linux.StandbyPingPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyPingAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyPingSplit = ConfigYesNo(default = False)
LCD4linux.StandbyPingColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyPingShadow = ConfigYesNo(default = False)
LCD4linux.StandbyPingFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyPingShow = ConfigSelection(choices = [("0", _("Online+Offline")), ("1", _("Online")), ("2", _("Offline"))], default="0")
LCD4linux.StandbyPingType = ConfigSelection(choices = DirType, default="0")
LCD4linux.StandbyPingTimeout = ConfigSlider(default = 50,  increment = 5, limits = (5, 1000))
LCD4linux.StandbyPingName1 = ConfigText(default="Internet:www.google.de", fixed_size=False)
LCD4linux.StandbyPingName2 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyPingName3 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyPingName4 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyPingName5 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyDev = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyDevLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyDevSize = ConfigSlider(default = 15,  increment = 2, limits = (10, 300))
LCD4linux.StandbyDevPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyDevAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyDevSplit = ConfigYesNo(default = False)
LCD4linux.StandbyDevColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyDevShadow = ConfigYesNo(default = False)
LCD4linux.StandbyDevFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyDevType = ConfigSelection(choices = DirType, default="0")
LCD4linux.StandbyDevExtra = ConfigSelection(choices = [("0", _("no")), ("RAM", _("Memory"))], default="RAM")
LCD4linux.StandbyDevName1 = ConfigText(default="/media/hdd", fixed_size=False)
LCD4linux.StandbyDevName2 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyDevName3 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyDevName4 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyDevName5 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyHdd = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyHddLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyHddSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 150))
LCD4linux.StandbyHddPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyHddAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.StandbyHddSplit = ConfigYesNo(default = False)
LCD4linux.StandbyHddType = ConfigSelection(choices = HddType, default="0")
LCD4linux.StandbyWetter = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyWetterLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyWetterPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyWetterAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyWetterSplit = ConfigYesNo(default = False)
LCD4linux.StandbyWetterZoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.StandbyWetterType = ConfigSelection(choices = WetterType, default="1")
LCD4linux.StandbyWetterColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyWetterShadow = ConfigYesNo(default = False)
LCD4linux.StandbyWetterFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyWetter2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyWetter2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyWetter2Pos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyWetter2Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyWetter2Split = ConfigYesNo(default = False)
LCD4linux.StandbyWetter2Zoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.StandbyWetter2Type = ConfigSelection(choices = WetterType, default="1")
LCD4linux.StandbyWetter2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyWetter2Shadow = ConfigYesNo(default = False)
LCD4linux.StandbyWetter2Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyMeteo = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyMeteoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyMeteoPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyMeteoAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyMeteoSplit = ConfigYesNo(default = False)
LCD4linux.StandbyMeteoZoom = ConfigSlider(default = 10,  increment = 1, limits = (7, 60))
LCD4linux.StandbyMeteoType = ConfigSelection(choices = MeteoType, default="1")
LCD4linux.StandbyMeteoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyMoon = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyMoonLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyMoonSize = ConfigSlider(default = 60,  increment = 2, limits = (10, 300))
LCD4linux.StandbyMoonPos = ConfigSlider(default = 10,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyMoonAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyMoonSplit = ConfigYesNo(default = False)
LCD4linux.StandbyMoonColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="white")
LCD4linux.StandbyMoonShadow = ConfigYesNo(default = False)
LCD4linux.StandbyMoonFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyNetAtmo = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyNetAtmoLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyNetAtmoPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyNetAtmoAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyNetAtmoSplit = ConfigYesNo(default = False)
LCD4linux.StandbyNetAtmoType = ConfigSelection(choices = NetatmoType, default="THCPN")
LCD4linux.StandbyNetAtmoType2 = ConfigSelection(choices = DirType, default="0")
LCD4linux.StandbyNetAtmoSize = ConfigSlider(default = 30,  increment = 1, limits = (10, 100))
LCD4linux.StandbyNetAtmoColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyNetAtmoShadow = ConfigYesNo(default = False)
LCD4linux.StandbyNetAtmoFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyNetAtmoCO2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyNetAtmoCO2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyNetAtmoCO2Size = ConfigSlider(default = 30,  increment = 1, limits = (5, 500))
LCD4linux.StandbyNetAtmoCO2Len = ConfigSlider(default = 200,  increment = 5, limits = (100, 1024))
LCD4linux.StandbyNetAtmoCO2Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyNetAtmoCO2Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyNetAtmoCO2Split = ConfigYesNo(default = False)
LCD4linux.StandbyNetAtmoCO2Type = ConfigSelection(choices = CO2Type, default="1")
LCD4linux.StandbyNetAtmoIDX = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyNetAtmoIDXLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyNetAtmoIDXSize = ConfigSlider(default = 30,  increment = 1, limits = (5, 500))
LCD4linux.StandbyNetAtmoIDXLen = ConfigSlider(default = 200,  increment = 5, limits = (100, 1024))
LCD4linux.StandbyNetAtmoIDXPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyNetAtmoIDXAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyNetAtmoIDXSplit = ConfigYesNo(default = False)
LCD4linux.StandbyNetAtmoIDXType = ConfigSelection(choices = CO2Type, default="1")
LCD4linux.StandbyOSCAM = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyOSCAMLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyOSCAMSize = ConfigSlider(default = 10,  increment = 1, limits = (9, 50))
LCD4linux.StandbyOSCAMPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyOSCAMAlign = ConfigSelection(choices = [("0", _("left")), ("2", _("right"))], default="0")
LCD4linux.StandbyOSCAMSplit = ConfigYesNo(default = False)
LCD4linux.StandbyOSCAMColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyOSCAMBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="black")
LCD4linux.StandbyText = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyTextLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyTextFile = ConfigText(default="/tmp/lcd4linux.txt", fixed_size=False, visible_width=50)
LCD4linux.StandbyTextSize = ConfigSlider(default = 32,  increment = 1, limits = (10, 300))
LCD4linux.StandbyTextFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyTextAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyTextPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyTextShadow = ConfigYesNo(default = False)
LCD4linux.StandbyTextColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyTextBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyText2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyText2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyText2File = ConfigText(default="/tmp/lcd4linux.txt", fixed_size=False, visible_width=50)
LCD4linux.StandbyText2Size = ConfigSlider(default = 32,  increment = 1, limits = (10, 300))
LCD4linux.StandbyText2Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyText2Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyText2Pos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyText2Shadow = ConfigYesNo(default = False)
LCD4linux.StandbyText2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyText2BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyText3 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyText3LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyText3File = ConfigText(default="/tmp/lcd4linux.txt", fixed_size=False, visible_width=50)
LCD4linux.StandbyText3Size = ConfigSlider(default = 32,  increment = 1, limits = (10, 300))
LCD4linux.StandbyText3Font = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyText3Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyText3Pos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyText3Shadow = ConfigYesNo(default = False)
LCD4linux.StandbyText3Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyText3BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyHTTP = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyHTTPLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyHTTPURL = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.StandbyHTTPSize = ConfigSlider(default = 20,  increment = 1, limits = (10, 300))
LCD4linux.StandbyHTTPPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyHTTPAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyHTTPColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyHTTPBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyHTTPShadow = ConfigYesNo(default = False)
LCD4linux.StandbyHTTPFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyWWW1 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyWWW1LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyWWW1Size = ConfigSlider(default = 200,  increment = 1, limits = (50, 1024))
LCD4linux.StandbyWWW1Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyWWW1Align = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyWWW1url = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.StandbyWWW1w = ConfigSlider(default = 800,  increment = 50, limits = (600, 2000))
LCD4linux.StandbyWWW1h = ConfigSlider(default = 600,  increment = 50, limits = (100, 2000))
LCD4linux.StandbyWWW1CutX = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyWWW1CutY = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyWWW1CutW = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyWWW1CutH = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyBild = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyBildLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyBildFile = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.StandbyBildSize = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.StandbyBildPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyBildAlign = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.StandbyBildQuick = ConfigYesNo(default = False)
LCD4linux.StandbyBildTransp = ConfigYesNo(default = False)
LCD4linux.StandbyBild2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyBild2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyBild2File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.StandbyBild2Size = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.StandbyBild2Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyBild2Align = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.StandbyBild2Quick = ConfigYesNo(default = False)
LCD4linux.StandbyBild2Transp = ConfigYesNo(default = False)
LCD4linux.StandbyBild3 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyBild3LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyBild3File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.StandbyBild3Size = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.StandbyBild3Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyBild3Align = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.StandbyBild3Quick = ConfigYesNo(default = False)
LCD4linux.StandbyBild3Transp = ConfigYesNo(default = False)
LCD4linux.StandbyBild4 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyBild4LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyBild4File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.StandbyBild4Size = ConfigSlider(default = 240,  increment = 10, limits = (10, 1024))
LCD4linux.StandbyBild4Pos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyBild4Align = ConfigSelection(choices = AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.StandbyBild4Quick = ConfigYesNo(default = False)
LCD4linux.StandbyBild4Transp = ConfigYesNo(default = False)
LCD4linux.StandbyMail = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyMailLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyMailSize = ConfigSlider(default = 12,  increment = 1, limits = (5, 150))
LCD4linux.StandbyMailPos = ConfigSlider(default = 30,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyMailAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyMailSplit = ConfigYesNo(default = False)
LCD4linux.StandbyMailColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyMailBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyMailKonto = ConfigSelection(choices = MailKonto, default="1")
LCD4linux.StandbyMailLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.StandbyMailType = ConfigSelection(choices = MailType, default="A1")
LCD4linux.StandbyMailProzent = ConfigSelection(choices = MailProzent, default="50")
LCD4linux.StandbyMailShadow = ConfigYesNo(default = False)
LCD4linux.StandbyMailFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyIconBar = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyIconBarLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyIconBarSize = ConfigSlider(default = 20,  increment = 1, limits = (10, 150))
LCD4linux.StandbyIconBarPos = ConfigSlider(default = 120,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyIconBarAlign = ConfigSelection(choices = AlignType, default="1")
LCD4linux.StandbyIconBarSplit = ConfigYesNo(default = False)
LCD4linux.StandbyIconBarType = ConfigSelection(choices = DirType, default="0")
LCD4linux.StandbyIconBarPopup = ConfigSelection(choices = [("0", _("off"))] + ScreenSet, default="0")
LCD4linux.StandbyIconBarPopupLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbySun = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbySunLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbySunSize = ConfigSlider(default = 20,  increment = 1, limits = (5, 150))
LCD4linux.StandbySunPos = ConfigSlider(default = 20,  increment = 2, limits = (0, 1024))
LCD4linux.StandbySunAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbySunSplit = ConfigYesNo(default = False)
LCD4linux.StandbySunColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbySunBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbySunShadow = ConfigYesNo(default = False)
LCD4linux.StandbySunFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbySunType = ConfigSelection(choices = DirType, default="2")
LCD4linux.StandbyFritz = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyFritzLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyFritzSize = ConfigSlider(default = 22,  increment = 1, limits = (10, 150))
LCD4linux.StandbyFritzPos = ConfigSlider(default = 130,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyFritzAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyFritzColor = ConfigSelection(choices = Farbe, default="yellow")
LCD4linux.StandbyFritzBackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyFritzType = ConfigSelection(choices = FritzType, default="TL")
LCD4linux.StandbyFritzPicSize = ConfigSlider(default = 100,  increment = 1, limits = (10, 800))
LCD4linux.StandbyFritzPicPos = ConfigSlider(default = 30,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyFritzPicAlign = ConfigSlider(default = 0,  increment = 10, limits = (0, 1024))
LCD4linux.StandbyFritzShadow = ConfigYesNo(default = False)
LCD4linux.StandbyFritzFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyCal = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyCalLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyCalPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyCalAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyCalSplit = ConfigYesNo(default = False)
LCD4linux.StandbyCalZoom = ConfigSlider(default = 10,  increment = 1, limits = (3, 50))
LCD4linux.StandbyCalType = ConfigSelection(choices = CalType, default="0A")
LCD4linux.StandbyCalTypeE = ConfigSelection(choices = CalTypeE, default="D2")
LCD4linux.StandbyCalLayout = ConfigSelection(choices = CalLayout, default="0")
LCD4linux.StandbyCalColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyCalBackColor = ConfigSelection(choices = Farbe, default="gray")
LCD4linux.StandbyCalCaptionColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyCalShadow = ConfigYesNo(default = False)
LCD4linux.StandbyCalFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyCalList = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyCalListLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyCalListSize = ConfigSlider(default = 12,  increment = 1, limits = (5, 150))
LCD4linux.StandbyCalListPos = ConfigSlider(default = 50,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyCalListAlign = ConfigSelection(choices = AlignType, default="0")
LCD4linux.StandbyCalListSplit = ConfigYesNo(default = False)
LCD4linux.StandbyCalListLines = ConfigSelectionNumber(1, 20, 1, default = 3)
LCD4linux.StandbyCalListProzent = ConfigSelection(choices = MailProzent, default="50")
LCD4linux.StandbyCalListType = ConfigSelection(choices = CalListType, default="C")
LCD4linux.StandbyCalListColor = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyCalListShadow = ConfigYesNo(default = False)
LCD4linux.StandbyCalListFont = ConfigSelection(choices = FontType, default="0")
LCD4linux.StandbyBox1 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyBox1LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyBox1x1 = ConfigSlider(default = 10,  increment = 1, limits = (0, 1024))
LCD4linux.StandbyBox1y1 = ConfigSlider(default = 10,  increment = 1, limits = (0, 1024))
LCD4linux.StandbyBox1x2 = ConfigSlider(default = 200,  increment = 1, limits = (0, 1024))
LCD4linux.StandbyBox1y2 = ConfigSlider(default = 1,  increment = 1, limits = (0, 1024))
LCD4linux.StandbyBox1Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyBox1BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyBox2 = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyBox2LCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyBox2x1 = ConfigSlider(default = 20,  increment = 1, limits = (0, 1024))
LCD4linux.StandbyBox2y1 = ConfigSlider(default = 20,  increment = 1, limits = (0, 1024))
LCD4linux.StandbyBox2x2 = ConfigSlider(default = 200,  increment = 1, limits = (0, 1024))
LCD4linux.StandbyBox2y2 = ConfigSlider(default = 1,  increment = 1, limits = (0, 1024))
LCD4linux.StandbyBox2Color = ConfigSelection(choices = Farbe, default="white")
LCD4linux.StandbyBox2BackColor = ConfigSelection(choices = [("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyRecording = ConfigSelection(choices = ScreenSelect, default="0")
LCD4linux.StandbyRecordingLCD = ConfigSelection(choices = LCDSelect, default="1")
LCD4linux.StandbyRecordingType = ConfigSelection(choices = [("1", _("Corner")), ("2", _("Picon"))], default="1")
LCD4linux.StandbyRecordingSize = ConfigSlider(default = 25,  increment = 1, limits = (10, 100))
LCD4linux.StandbyRecordingPos = ConfigSlider(default = 0,  increment = 2, limits = (0, 1024))
LCD4linux.StandbyRecordingAlign = ConfigSelection(choices = AlignType, default="2")
LCD4linux.StandbyRecordingSplit = ConfigYesNo(default = False)

class MyTimer: # only for debug
	import traceback
	def __init__(self):
		print "L4L create timer at:"
		traceback.print_stack(limit=2)
		self.timer = eTimer()
		print "L4L created timer", self.timer
	def __del__(self):
		print "L4L destruct timer", self.timer
		traceback.print_stack(limit=2)
		del self.timer
	def start(self, msecs, singleShot=False):
		print "L4L start timer", msecs, singleShot, self.timer
		traceback.print_stack(limit=2)
		self.timer.start(msecs, singleShot)
	def	startLongTimer(self, secs):
		print "L4L start longtimer", secs, self.timer
		traceback.print_stack(limit=2)
		self.timer.startLongTimer(secs)
	def stop(self):
		print "L4L stopped timer", self.timer
		traceback.print_stack(limit=2)
		self.timer.stop()
	def getCallback(self):
		return self.timer.callback
	callback = property(getCallback)

def Code_utf8(wert):
	wert = wert.replace('\xc2\x86', '').replace('\xc2\x87', '').decode("utf-8", "ignore").encode("utf-8") or ""
	return codecs.decode(wert, 'UTF-8')

def L4log(nfo,wert=""):
	if LCD4linux.EnableEventLog.value != "0":
		print "[LCD4linux]",nfo,wert
		if LCD4linux.EnableEventLog.value != "3":
			try:
				f = open("/tmp/L4log.txt","a")
				try:
					f.write(strftime("%H:%M:%S") + " %s %s\r\n" % (str(nfo), str(wert)))
				finally:
					f.close()
			except IOError:
				print "[LCD4linux]",strftime("%H:%M:%S"),"Logging-Error"

def L4logE(nfo,wert=""):
	if LCD4linux.EnableEventLog.value == "2":
		L4log(nfo,wert)

def GetBox():
	B = ""
	if os.path.exists("/proc/stb/info/model"):
		f = open("/proc/stb/info/model")
		B = f.readline()
		f.close()
		L4logE("Boxtype",B)
	return B

def setConfigMode(w):
	global ConfigMode
	ConfigMode = w
def setConfigStandby(w):
	global ConfigStandby
	ConfigStandby = w
def setisMediaPlayer(w):
	global isMediaPlayer
	isMediaPlayer = w
def setScreenActive(w,lcd=""):
	global ScreenActive
	global ScreenTime
	if lcd=="":
		if w=="0":
			ScreenActive[-3:]=["","",""]
			L4LElist.setHold(False)
		else:
			ScreenActive[0] = w
	else:
		if w=="0":
			w=""
		ScreenActive[int(lcd)] = w
	LCD4linux.ScreenActive.value = ScreenActive[0]
	ScreenTime=0
def setLCDon(w):
	global LCDon
	LCDon = w
def setSaveEventListChanged(w):
	global SaveEventListChanged
	SaveEventListChanged = w
def execexec(w):
	exec(w)
def getScreenActive(All=False):
	if All:
		return ScreenActive
	else:
		return ScreenActive[0]
def getConfigStandby():
	return ConfigStandby
def getConfigMode():
	return ConfigMode
def getisMediaPlayer():
	return isMediaPlayer
def getTMP():
	return TMP
def getTMPL():
	return TMPL
def getINFO():
	return INFO
def getSaveEventListChanged():
	return SaveEventListChanged
def setPopText(w):
	global PopText
	PopText[0] = Code_utf8(_(strftime("%A"))) + strftime(" %H:%M")
	PopText[1] = w
def resetWetter():
	global wwwWetter
	wwwWetter = ["",""]

def getSA(w):
	return ScreenActive[0] if ScreenActive[w]=="" else ScreenActive[w]
#	return ScreenActive[0] in w or (ScreenActive[-3:].strip() != "" and ScreenActive[-3:].strip() in w)

def rmFile(fn):
	if os.path.isfile(fn):
		try:
			L4logE("delete",fn)
			os.remove(fn)
		except:
			L4logE("Error delete",fn)

def rmFiles(fn):
	try:
		fl=glob.glob(fn)
		L4logE("delete*",fn)
		for f in fl:
			os.remove(f)
	except:
		L4logE("Error delete*",fn)

def getTimeDiff():
	offset = timezone if (localtime().tm_isdst == 0) else altzone
	return offset / -3600                                                   

def getTimeDiffUTC():
	t=datetime.now() - datetime.utcnow()
	return int(t.days*24+round(t.seconds/3600.0))

def ConfTime(F,W):
	try:
		if os.path.exists(LCD4config) and W != [6,0]:
			fconfig = open(LCD4config,"r")
			if f.read().find("config."+F) == -1:
				L4log("write alternate TimeConfig "+F,W)
				f = open(LCD4config,"a")
				f.write("config.%s=%d:%d\n" % (F,W[0],W[1]))
				f.close()
			fconfig.close()
	except:
		L4log("Errot: write alternate TimeConfig "+F,W)

def ScaleGtoR(PROZ):
	if PROZ < 50:
		R=max((255*PROZ)/50,0)
		G=255
	else:
		R=255
		G=max((255*(100-PROZ))/50,0)
	B=0
	return "#%02x%02x%02x" % (R,G,B)

def ICSdownloads():
	global ICS
	global ICSlist
	global ICSdownrun
	L4logE("ICSdownloads...",len(ICSlist))
	if len(ICSlist)==0:
		return
	ICSdownrun = True
	ICS.clear()
	if LCD4linux.CalPlanerFS.value == True:
		try:
			from Plugins.Extensions.PlanerFS.PFSl4l import l4l_export
			liste=l4l_export("50").planerfs_liste
			PlanerFSok = True
			L4logE("PlanerFS registered")
		except:
			PlanerFSok = False
			L4log("PlanerFS not registered")

		if PlanerFSok == True:
			L4log(liste)
			for Icomp in liste:
				DT=Icomp[0]
				L4logE(Icomp)
				D = "%04d-%02d-%02d"  % (DT.year,DT.month,DT.day)
				if Icomp[4] == (0,0):
					dateT = date(DT.year,DT.month,DT.day)
				else:
					dateT = DT
				if Icomp[6] == 0:
					dateS = Code_utf8(Icomp[1])
				else:
					dateS = "%s (%d)" % (Code_utf8(Icomp[1]),Icomp[6])
				inew=[dateS,dateT,4]
				Doppel = False
				if ICS.get(D,None) is None:
					ICS[D]=[]
				else:
					for ii in ICS[D]:
						if ii[:2] == inew[:2]:
							Doppel = True
							L4logE("ICS ignore",inew)
				L4log(Doppel)
				if Doppel == False:
					ICS[D].append(inew)
					L4logE(D,inew)

	for name in ICSlist:
		L4log("ICS read Col",name[1])
		try:
			gcal = icalendar.Calendar().from_string(name[0])
		except:
			L4log("Error: ICS not readable!",name[1])
			continue
		try:
			for Icomp in gcal.walk():
				if Icomp.name == "VEVENT":
					L4logE(Icomp["dtstart"],Icomp.get('summary'))
					rrule=str(Icomp.get("rrule",""))
					if "YEARLY" in rrule:
						dt=str(Icomp["dtstart"])
						Icomp.set('dtstart', date(datetime.now().year,int(dt[4:6]),int(dt[6:8])))
					today=date.today()
					nextmonth=today + timedelta(calendar.mdays[today.month]) # 2012-01-23
					nextmonth2=today + timedelta(calendar.mdays[today.month]-3) # save Month+1 if days to long
					DTstart = str(Icomp.decoded("dtstart"))
					if strftime("%Y-%m") == DTstart[:7] or nextmonth.strftime("%Y-%m") == DTstart[:7] or nextmonth2.strftime("%Y-%m") == DTstart[:7]:
						D = DTstart[:10]
						inew=[Code_utf8(Icomp.get('summary')),Icomp.decoded("dtstart"),name[1]]
						Doppel = False
						if ICS.get(D,None) is None:
							ICS[D]=[]
						else:
							for ii in ICS[D]:
								if ii[:2] == inew[:2]:
									Doppel = True
									L4log("ICS ignore",inew)
						if Doppel == False:
							ICS[D].append(inew)
							L4log(D,inew)
		except:
			from traceback import format_exc
			L4log("Error ICS",name)
			L4log("Error:",format_exc() )
			try:
				open(CrashFile,"w").write(format_exc())
			except:
				pass
	ICSlist = []
	L4logE("ICS laenge",len(ICS))
	ICSdownrun = False

def getResolution(t,r):
	if t[:1] == "5":
		ttt = LCD4linux.xmlLCDType.value.split("x")
		MAX_W,MAX_H = int(ttt[0]),int(ttt[1])
	elif t[1:] == "1":
		MAX_W,MAX_H = 320,240
	elif t[1:] == "2":
		MAX_W,MAX_H = 240,320
	elif t[1:] in ["3","4","5","10"]:
		MAX_W,MAX_H = 800,480
	elif t[1:] in ["6","9","11","12"]:
		MAX_W,MAX_H = 800,600
	elif t[1:] in ["7","8","13"]:
		MAX_W,MAX_H = 1024,600
	elif t[1:] == "17":
		MAX_W,MAX_H = 220,176
	elif t[1:] == "18":
		MAX_W,MAX_H = 255,64
	elif t[1:] == "30":
		MAX_W,MAX_H = 400,240
	elif t[1:] == "20":
		MAX_W,MAX_H = LCD4linux.SizeW.value,LCD4linux.SizeH.value 
	if r in ["90","270"]:
		MAX_W,MAX_H = MAX_H,MAX_W
	return MAX_W,MAX_H

def OSDclose():
	global OSDon
	OSDon = 0
	L4log("Screen close")
	rmFile("%sdpfgrab.jpg" % TMPL)
	return

def replacement_Screen_show(self):
	global OSDon
	global OSDtimer
	if LCD4linux.OSD.value != "0":
		L4log("Skin", self.skinName)
		doSkinOpen = True
		if len(self.skinName[0])>1:
			for s in self.skinName:
				if s in OSDdontskin:
					doSkinOpen = False
		else:
			if self.skinName in OSDdontskin:
				doSkinOpen = False	
		if doSkinOpen and OSDtimer >= 0:
			if "Title" in self:
				ib = self["Title"].getText()
				L4log("Screen", ib)
#			print "[LCD4linux] Screen", ib
				if ib not in OSDdontshow:
					L4log("Open Screen:"+ str(ib), "Skin:"+ str(self.skinName))
					OSDon = 3
					self.onClose.append(OSDclose)
				else:
					if OSDon != 1:
						OSDon = 0
			else:
				L4log("Open Screen no Title, Skin:", self.skinName)
				OSDon = 3
				self.onClose.append(OSDclose)
		else:
			if OSDon != 1:
				OSDon = 0
	Screen.show_old(self)

Screen.show_old = Screen.show
Screen.show = replacement_Screen_show

def find_dev(Anzahl, idVendor, idProduct):
	gefunden = False
	if os.path.isfile("/proc/bus/usb/devices"):
		i = open("/proc/bus/usb/devices", "r").read().lower()
		pos = i.find("vendor=%04x prodid=%04x" % (idVendor,idProduct))
#		print "[LCD4linux] find",pos, Anzahl
		if pos > 0:
			if Anzahl == 2:
				pos = i.find("vendor=%04x prodid=%04x" % (idVendor,idProduct),pos+10)
#				print "[LCD4linux] find2",pos
				if pos > 0:
					gefunden = True
			else:
				gefunden = True
	elif USBok == True:
		try:
			if len(usb.core.find(idVendor=idVendor, idProduct=idProduct, find_all=True)) >= Anzahl:
				L4logE("usb.core find")
				gefunden = True
		except:
			L4log("Error usb.core find")
	L4log("%d. Vendor=%04x ProdID=%04x" % (Anzahl,idVendor,idProduct), gefunden)
	return gefunden
	
def find_dev2(idVendor, idProduct, idVendor2, idProduct2):
	gefunden = False
	if find_dev(2,idVendor, idProduct) or find_dev(2,idVendor2, idProduct2) or (find_dev(1,idVendor, idProduct) and find_dev(1,idVendor2, idProduct2)):
		gefunden = True
	L4log("Vendor=%04x ProdID=%04x or Vendor=%04x ProdID=%04x" % (idVendor,idProduct,idVendor2,idProduct2), gefunden)
	return gefunden

# get picon path
def getpiconres(x, y, full, picon, P2, P2A, P2C):
	if len(P2C) < 3:
		return ""
	L4logE("get Picon",os.path.join(P2C,picon))
	if os.path.isdir(P2C):
		if not os.path.isfile(os.path.join(P2C,picon)):
			L4log("Resize Picon")
			PD = ""
			if os.path.isfile(os.path.join(P2,picon)):
				PD = os.path.join(P2,picon)
			elif os.path.isfile(os.path.join(P2A,picon)) and len(P2A) > 3:
				PD = os.path.join(P2A,picon)
			L4logE("read Picon",PD)
			if PD != "":
				try:
					file_in = PD
					pil_image = Image.open(file_in)
					if LCD4linux.PiconTransparenz.value == "2":
						pil_image = pil_image.convert("RGBA")
					xx,yy = pil_image.size
					if full == False:
						y=int(float(x)/xx*yy)
					if LCD4linux.BilderQuality.value == "0":
						image_new = pil_image.resize((x, y))
					else:
						image_new = pil_image.resize((x, y), Image.ANTIALIAS)
					file_out = os.path.join(P2C,picon)
					s = os.statvfs(P2C)
					if (s.f_bsize * s.f_bavail / 1024) < 100:
						L4log("Error: Cache Directory near full")
						return ""			
					image_new.save(file_out)
				except:
					L4log("Error: create Cache-Picon")
					return ""
			else:
				L4logE("no Picon found")
				return ""
		return os.path.join(P2C,picon)
	else:
		L4logE("no Cache")
		# no picon for channel
		if not os.path.exists(P2C):
			L4logE("no Picon-Cachedir",P2C)
			try:
				os.mkdir(P2C)
			except:
				L4log("Error: create Picon-Cache-Dir")
		return ""

def writeHelligkeit(hell,hell2,hell3,STOP = False):
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	global AktHelligkeit
	def BRI(w1,w2):
		return int(w1) if L4LElist.getBrightness(w2,False)==-1 else L4LElist.getBrightness(w2,False)
	R=""
	if BRI(hell,1) == 0:
		R += "1"
	if BRI(hell2,2) == 0:
		R += "2"
	if BRI(hell3,3) == 0:
		R += "3"
	if AktHelligkeit == [hell,hell2,hell3]+L4LElist.getBrightness(0,False) and OSDtimer >= 0:
		return R
	AktHelligkeit = [hell,hell2,hell3]+L4LElist.getBrightness(0,False)
	L4LElist.resetBrightness([hell,hell2,hell3])
	L4logE("write Bright",AktHelligkeit)
	if SamsungDevice is not None and LCD4linux.LCDType1.value[0] == "1":
		if dpf.setBacklight(SamsungDevice,BRI(hell,1) if BRI(hell,1) < 8 else 7) == False:
			dpf.close(SamsungDevice)
			SamsungDevice = None
	if SamsungDevice2 is not None and LCD4linux.LCDType2.value[0] == "1":
		if dpf.setBacklight(SamsungDevice2,BRI(hell2,2) if BRI(hell2,2) < 8 else 7) == False:
			dpf.close(SamsungDevice2)
			SamsungDevice2 = None
	if SamsungDevice3 is not None and LCD4linux.LCDType3.value[0] == "1":
		if dpf.setBacklight(SamsungDevice3,BRI(hell3,3) if BRI(hell3,3) < 8 else 7) == False:
			dpf.close(SamsungDevice3)
			SamsungDevice3 = None
	if os.path.isfile("/etc/grautec/settings/takeownership") and STOP == False:
		try:
			if LCD4linux.LCDType1.value[0] == "4":
				if os.path.isfile("/tmp/usbtft-brightness"):
					open("/tmp/usbtft-brightness","w").write(str(int(BRI(hell,1)*6.3)))
				elif os.path.isfile("/proc/stb/lcd/oled_brightness"):
					open("/proc/stb/lcd/oled_brightness","w").write(str(int(int(hell)*25.5)))
			if LCD4linux.LCDType2.value[0] == "4":
				if os.path.isfile("/tmp/usbtft-brightness"):
					open("/tmp/usbtft-brightness","w").write(str(int(BRI(hell2,2)*6.3)))
				elif os.path.isfile("/proc/stb/lcd/oled_brightness"):
					open("/proc/stb/lcd/oled_brightness","w").write(str(int(int(hell2)*25.5)))
			if LCD4linux.LCDType3.value[0] == "4":
				if os.path.isfile("/tmp/usbtft-brightness"):
					open("/tmp/usbtft-brightness","w").write(str(int(BRI(hell3,3)*6.3)))
				elif os.path.isfile("/proc/stb/lcd/oled_brightness"):
					open("/proc/stb/lcd/oled_brightness","w").write(str(int(int(hell3)*25.5)))
		except:
			pass
	H = -1
	if LCD4linux.LCDType1.value[0] == "9":
		H = BRI(hell,1)
	elif LCD4linux.LCDType2.value[0] == "9":
		H = BRI(hell2,2)
	elif LCD4linux.LCDType3.value[0] == "9":
		H = BRI(hell3,3)
	if H != -1:
		H = int(H) * 25
		if H >= 250:
			H = 255
		led_fd = open("/dev/lcd2",'w')
		ioctl(led_fd, 0x10, H)
		led_fd.close()
	return R

def doDPF(dev,im):
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if dev == 1:
		if dpf.showImage(SamsungDevice,im) == False:
			L4log("Error writing DPF Device")
			dpf.close(SamsungDevice)
			SamsungDevice = None
	elif dev == 2:
		if dpf.showImage(SamsungDevice2,im) == False:
			L4log("Error writing DPF2 Device")
			dpf.close(SamsungDevice2)
			SamsungDevice2 = None
	elif dev == 3:
		if dpf.showImage(SamsungDevice3,im) == False:
			L4log("Error writing DPF3 Device")
			dpf.close(SamsungDevice3)
			SamsungDevice3 = None

def writeLCD1(im,quality,SAVE=True):
	global SamsungDevice
	if LCD4linux.LCDType1.value[0] == "1":
		if SamsungDevice is not None and not (TVrunning == True and "1" in LCD4linux.TVLCD.value):
			L4log("writing to DPF Device")
			doDPF(1,im)
		if "1" in LCD4linux.SavePicture.value and SAVE==True:
			if LCD4linux.LCDRotate1.value != "0":
				im=im.rotate(-int(LCD4linux.LCDRotate1.value))
			try:
				im.save(PICtmp+".png", "PNG")
				if os.path.isfile(PICtmp+".png"):
					os.rename(PICtmp+".png",PIC+".png")
			except:
				L4log("Error write Picture")
	elif LCD4linux.LCDType1.value[0] == "3":
		L4log("writing Picture")
		try:
			im.save(PICtmp+".png", "PNG")
			if os.path.isfile(PICtmp+".png"):
				os.rename(PICtmp+".png",PIC+".png")
		except:
			L4log("Error write Picture")
	elif LCD4linux.LCDType1.value[0] == "4":
		L4log("writing TFT-LCD")
		try:
			im.save("/tmp/usbtft-bmp", "BMP")
			if "1" in LCD4linux.SavePicture.value and SAVE==True:
				if LCD4linux.LCDRotate1.value != "0":
					im=im.rotate(-int(LCD4linux.LCDRotate1.value))
				im.save(PICtmp+".png", "PNG")
				if os.path.isfile(PICtmp+".png"):
					os.rename(PICtmp+".png",PIC+".png")
		except:
			L4log("Error write Picture")
	elif LCD4linux.LCDType1.value[0] == "5":
		L4log("writing Internal-LCD")
		try:
			if LCD4linux.xmlLCDColor.value=="8":
				im.convert("P", colors= 254).save(xmlPICtmp, "PNG")
			else:
				im.save(xmlPICtmp, "PNG")
			if os.path.isfile(xmlPICtmp):
				os.rename(xmlPICtmp,xmlPIC)
			if "1" in LCD4linux.SavePicture.value and SAVE==True:
				if LCD4linux.LCDRotate1.value != "0":
					im=im.rotate(-int(LCD4linux.LCDRotate1.value))
				im.save(PICtmp+".png", "PNG")
				if os.path.isfile(PICtmp+".png"):
					os.rename(PICtmp+".png",PIC+".png")
		except:
			L4log("Error write Picture")
	elif LCD4linux.LCDType1.value[0] == "9":
		L4log("writing to Vu+ LCD")
		try:
			im.save(PICtmp+".png", "PNG")
			if os.path.isfile(PICtmp+".png"):
				os.rename(PICtmp+".png",PIC+".png")
		except:
			L4log("Error write Picture")
		if pngutilconnect != 0:
			pngutil.send(PIC+".png")
	else:
		if SamsungDevice is not None and not (TVrunning == True and "1" in LCD4linux.TVLCD.value):
			L4log("writing to Samsung Device")
			output = cStringIO.StringIO()
			im.save(output, "JPEG") # ,quality=int(quality)
			pic = output.getvalue()
			output.close()
			try:
				Photoframe.write_jpg2frame(SamsungDevice, pic)
			except:
				SamsungDevice = None
				L4log("Samsung 1 write error")
		if "1" in LCD4linux.SavePicture.value and SAVE==True:
			try:
				if LCD4linux.LCDRotate1.value != "0":
					im=im.rotate(-int(LCD4linux.LCDRotate1.value))
					im.save(PICtmp+".jpg", "JPEG")
				else:
					open(PICtmp+".jpg","wb").write(pic)
				if os.path.isfile(PICtmp+".jpg"):
					os.rename(PICtmp+".jpg",PIC+".jpg")
			except:
				L4log("Error write Picture")

def writeLCD2(im2,quality,SAVE=True):
	global SamsungDevice2
	if LCD4linux.LCDType2.value[0] == "1":
		if SamsungDevice2 is not None and not (TVrunning == True and "2" in LCD4linux.TVLCD.value):
			L4log("writing to DPF2 Device")
			doDPF(2,im2)
		if "2" in LCD4linux.SavePicture.value and SAVE==True:
			if LCD4linux.LCDRotate2.value != "0":
				im2=im2.rotate(-int(LCD4linux.LCDRotate2.value))
			try:
				im2.save(PIC2tmp+".png", "PNG")
				if os.path.isfile(PIC2tmp+".png"):
					os.rename(PIC2tmp+".png",PIC2+".png")
			except:
				L4log("Error write Picture2")
	elif LCD4linux.LCDType2.value[0] == "3":
		L4log("writing Picture2")
		try:
			im2.save(PIC2tmp+".png", "PNG")
			if os.path.isfile(PIC2tmp+".png"):
				os.rename(PIC2tmp+".png",PIC2+".png")
		except:
			L4log("Error write Picture2")
	elif LCD4linux.LCDType2.value[0] == "4":
		L4log("writing TFT-LCD2")
		try:
			im2.save("/tmp/usbtft-bmp", "BMP")
			if "2" in LCD4linux.SavePicture.value and SAVE==True:
				if LCD4linux.LCDRotate2.value != "0":
					im2=im2.rotate(-int(LCD4linux.LCDRotate2.value))
				im2.save(PIC2tmp+".png", "PNG")
				if os.path.isfile(PIC2tmp+".png"):
					os.rename(PIC2tmp+".png",PIC2+".png")
		except:
			L4log("Error write Picture2")
	elif LCD4linux.LCDType2.value[0] == "5":
		L4log("writing Internal-LCD2")
		try:
			if LCD4linux.xmlLCDColor.value=="8":
				im2.convert("P", colors= 254).save(xmlPICtmp, "PNG")
			else:
				im2.save(xmlPICtmp, "PNG")
			if os.path.isfile(xmlPICtmp):
				os.rename(xmlPICtmp,xmlPIC)
			if "2" in LCD4linux.SavePicture.value and SAVE==True:
				if LCD4linux.LCDRotate2.value != "0":
					im2=im2.rotate(-int(LCD4linux.LCDRotate2.value))
				im2.save(PIC2tmp+".png", "PNG")
				if os.path.isfile(PIC2tmp+".png"):
					os.rename(PIC2tmp+".png",PIC2+".png")
		except:
			L4log("Error write Picture2")
	elif LCD4linux.LCDType2.value[0] == "9":
		L4log("writing to Vu+ LCD2")
		try:
			im2.save(PIC2tmp+".png", "PNG")
			if os.path.isfile(PIC2tmp+".png"):
				os.rename(PIC2tmp+".png",PIC2+".png")
		except:
			L4log("Error write Picture")
		if pngutilconnect != 0:
			pngutil.send(PIC2+".png")
	else:
		if SamsungDevice2 is not None and not (TVrunning == True and "2" in LCD4linux.TVLCD.value):
			L4log("writing to Samsung2 Device")
			output = cStringIO.StringIO()
			im2.save(output, "JPEG") # ,quality=int(quality)
			pic = output.getvalue()
			output.close()
			try:
				Photoframe.write_jpg2frame(SamsungDevice2, pic)       
			except:
				SamsungDevice2 = None
				L4log("Samsung 2 write error")
		if "2" in LCD4linux.SavePicture.value and SAVE==True:
			try:
				if LCD4linux.LCDRotate2.value != "0":
					im2=im2.rotate(-int(LCD4linux.LCDRotate2.value))
					im2.save(PIC2tmp+".jpg", "JPEG")
				else:
					open(PIC2tmp+".jpg","wb").write(pic)
				if os.path.isfile(PIC2tmp+".jpg"):
					os.rename(PIC2tmp+".jpg",PIC2+".jpg")
			except:
				L4log("Error write Picture2")

def writeLCD3(im3,quality,SAVE=True):
	global SamsungDevice3
	if LCD4linux.LCDType3.value[0] == "1":
		if SamsungDevice3 is not None and not (TVrunning == True and "3" in LCD4linux.TVLCD.value):
			L4log("writing to DPF3 Device")
			doDPF(3,im3)
		if "3" in LCD4linux.SavePicture.value and SAVE==True:
			if LCD4linux.LCDRotate3.value != "0":
				im3=im3.rotate(-int(LCD4linux.LCDRotate3.value))
			try:
				im3.save(PIC3tmp+".png", "PNG")
				if os.path.isfile(PIC3tmp+".png"):
					os.rename(PIC3tmp+".png",PIC3+".png")
			except:
				L4log("Error write Picture3")
	elif LCD4linux.LCDType3.value[0] == "3":
		L4log("writing Picture3")
		try:
			im3.save(PIC3tmp+".png", "PNG")
			if os.path.isfile(PIC3tmp+".png"):
				os.rename(PIC3tmp+".png",PIC3+".png")
		except:
			L4log("Error write Picture3")
	elif LCD4linux.LCDType3.value[0] == "4":
		L4log("writing TFT-LCD3")
		try:
			im3.save("/tmp/usbtft-bmp", "BMP")
			if "3" in LCD4linux.SavePicture.value and SAVE==True:
				if LCD4linux.LCDRotate3.value != "0":
					im3=im3.rotate(-int(LCD4linux.LCDRotate3.value))
				im3.save(PIC3tmp+".png", "PNG")
				if os.path.isfile(PIC3tmp+".png"):
					os.rename(PIC3tmp+".png",PIC3+".png")
		except:
			L4log("Error write Picture3")
	elif LCD4linux.LCDType3.value[0] == "5":
		L4log("writing Internal-LCD3")
		try:
			if LCD4linux.xmlLCDColor.value=="8":
				im3.convert("P", colors= 254).save(xmlPICtmp, "PNG")
			else:
				im3.save(xmlPICtmp, "PNG")
			if os.path.isfile(xmlPICtmp):
				os.rename(xmlPICtmp,xmlPIC)
			if "3" in LCD4linux.SavePicture.value and SAVE==True:
				if LCD4linux.LCDRotate3.value != "0":
					im3=im3.rotate(-int(LCD4linux.LCDRotate3.value))
				im3.save(PIC3tmp+".png", "PNG")
				if os.path.isfile(PIC3tmp+".png"):
					os.rename(PIC3tmp+".png",PIC3+".png")
		except:
			L4log("Error write Picture3")
	elif LCD4linux.LCDType3.value[0] == "9":
		L4log("writing to Vu+ LCD3")
		try:
			im3.save(PIC3tmp+".png", "PNG")
			if os.path.isfile(PIC3tmp+".png"):
				os.rename(PIC3tmp+".png",PIC3+".png")
		except:
			L4log("Error write Picture3")
		if pngutilconnect != 0:
			pngutil.send(PIC3+".png")
	else:
		if SamsungDevice3 is not None and not (TVrunning == True and "3" in LCD4linux.TVLCD.value):
			L4log("writing to Samsung3 Device")
			output = cStringIO.StringIO()
			im3.save(output, "JPEG") # ,quality=int(quality)
			pic = output.getvalue()
			output.close()
			try:
				Photoframe.write_jpg2frame(SamsungDevice3, pic)       
			except:
				SamsungDevice3 = None
				L4log("Samsung 3 write error")
		if "3" in LCD4linux.SavePicture.value and SAVE==True:
			try:
				if LCD4linux.LCDRotate3.value != "0":
					im3=im3.rotate(-int(LCD4linux.LCDRotate3.value))
					im3.save(PIC3tmp+".jpg", "JPEG")
				else:
					open(PIC3tmp+".jpg","wb").write(pic)
				if os.path.isfile(PIC3tmp+".jpg"):
					os.rename(PIC3tmp+".jpg",PIC3+".jpg")
			except:
				L4log("Error write Picture3")

def NextScreen(PRESS):
	global ScreenActive
	global ScreenTime
	if SaveEventListChanged == True:
		L4log("Event Change Aktive")
		return
	if Standby.inStandby or ConfigStandby:
		if ScreenActive[0] == "1":
			ST = LCD4linux.StandbyScreenTime.value
		elif ScreenActive[0] == "2":
			ST = LCD4linux.StandbyScreenTime2.value
		elif ScreenActive[0] == "3":
			ST = LCD4linux.StandbyScreenTime3.value
		elif ScreenActive[0] == "4":
			ST = LCD4linux.StandbyScreenTime4.value
		elif ScreenActive[0] == "5":
			ST = LCD4linux.StandbyScreenTime5.value
		elif ScreenActive[0] == "6":
			ST = LCD4linux.StandbyScreenTime6.value
		elif ScreenActive[0] == "7":
			ST = LCD4linux.StandbyScreenTime7.value
		elif ScreenActive[0] == "8":
			ST = LCD4linux.StandbyScreenTime8.value
		elif ScreenActive[0] == "9":
			ST = LCD4linux.StandbyScreenTime9.value
		else:
			ST = "1"
	else:
		if ScreenActive[0] == "1":
			ST = LCD4linux.ScreenTime.value
		elif ScreenActive[0] == "2":
			ST = LCD4linux.ScreenTime2.value
		elif ScreenActive[0] == "3":
			ST = LCD4linux.ScreenTime3.value
		elif ScreenActive[0] == "4":
			ST = LCD4linux.ScreenTime4.value
		elif ScreenActive[0] == "5":
			ST = LCD4linux.ScreenTime5.value
		elif ScreenActive[0] == "6":
			ST = LCD4linux.ScreenTime6.value
		elif ScreenActive[0] == "7":
			ST = LCD4linux.ScreenTime7.value
		elif ScreenActive[0] == "8":
			ST = LCD4linux.ScreenTime8.value
		elif ScreenActive[0] == "9":
			ST = LCD4linux.ScreenTime9.value
		else:
			ST = "1"
	if ScreenTime >= int(ST) and int(ST) > 0 or PRESS == True:
		ScreenTime=0
		ScreenActive[0] = str(int(ScreenActive[0])+1)
		if Standby.inStandby or ConfigStandby:
			if int(ScreenActive[0]) > int(LCD4linux.StandbyScreenMax.value):
				ScreenActive[0] = "1"
		elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
			if int(ScreenActive[0]) > int(LCD4linux.MPScreenMax.value):
				ScreenActive[0] = "1"
		else:
			if int(ScreenActive[0]) > int(LCD4linux.ScreenMax.value):
				ScreenActive[0] = "1"
	if LCD4linux.StandbyScreenTime.value > 0 or LCD4linux.ScreenTime.value > 0:
		ScreenTime += 1

def _getDirs(base):
	return [x for x in glob.iglob(os.path.join( base, '*')) if os.path.isdir(x) ]

def rglob(base, pattern):
	list = []
	list.extend(glob.glob(os.path.join(base,pattern)))
	dirs = _getDirs(base)
	L4logE("Picturedirectorys", dirs)
	if len(dirs):
		for d in dirs:
			list.extend(rglob(os.path.join(base,d), pattern))
	return list

def getBilder():
	global Bilder
	global BilderIndex
	BilderOrt = ["","",""]
	Bilder = [[],[],[]]
	SuchExt = ["*.png","*.PNG","*.jpg","*.JPG"]
	if Standby.inStandby or ConfigStandby:
		if LCD4linux.StandbyBild.value !=0:
			BilderOrt[0] = LCD4linux.StandbyBildFile.value
		if LCD4linux.StandbyBild2.value !=0:
			BilderOrt[1] = LCD4linux.StandbyBild2File.value
		if LCD4linux.StandbyBild3.value !=0:
			BilderOrt[2] = LCD4linux.StandbyBild3File.value
	elif isMediaPlayer == "" or isMediaPlayer == "radio":
		if LCD4linux.Bild.value !=0:
			BilderOrt[0] = LCD4linux.BildFile.value
		if LCD4linux.Bild2.value !=0:
			BilderOrt[1] = LCD4linux.Bild2File.value
		if LCD4linux.Bild3.value !=0:
			BilderOrt[2] = LCD4linux.Bild3File.value
	else:
		if LCD4linux.MPBild.value !=0:
			BilderOrt[0] = LCD4linux.MPBildFile.value
		if LCD4linux.MPBild2.value !=0:
			BilderOrt[1] = LCD4linux.MPBild2File.value
		BilderOrt[2]=""
	L4logE("BilderOrt",BilderOrt)
	if os.path.isdir(BilderOrt[0]):
		L4log("read Pictures0")
		BilderIndex[0] = 0
		if LCD4linux.BilderRecursiv.value == False:
			for EXT in SuchExt:
				Bilder[0] += glob.glob(os.path.normpath(BilderOrt[0])+"/"+EXT)
		else:
			for EXT in SuchExt:
				Bilder[0] += rglob(os.path.normpath(BilderOrt[0]),EXT)
		if LCD4linux.BilderSort.value == "2":
			random.shuffle(Bilder[0])
		elif LCD4linux.BilderSort.value == "1":
			Bilder[0].sort()
		L4logE("Pictures",Bilder[0])
	if os.path.isdir(BilderOrt[1]):
		L4log("read Pictures1")
		BilderIndex[1] = 0
		if LCD4linux.BilderRecursiv.value == False:
			for EXT in SuchExt:
				Bilder[1] += glob.glob(os.path.normpath(BilderOrt[1])+"/"+EXT)
		else:
			for EXT in SuchExt:
				Bilder[1] += rglob(os.path.normpath(BilderOrt[1]),EXT)
		if LCD4linux.BilderSort.value == "2":
			random.shuffle(Bilder[1])
		elif LCD4linux.BilderSort.value == "1":
			Bilder[1].sort()
		L4logE("Pictures",Bilder[1])
	if os.path.isdir(BilderOrt[2]):
		L4log("read Pictures2")
		BilderIndex[2] = 0
		if LCD4linux.BilderRecursiv.value == False:
			for EXT in SuchExt:
				Bilder[2] += glob.glob(os.path.normpath(BilderOrt[2])+"/"+EXT)
		else:
			for EXT in SuchExt:
				Bilder[2] += rglob(os.path.normpath(BilderOrt[2]),EXT)
		if LCD4linux.BilderSort.value == "2":
			random.shuffle(Bilder[2])
		elif LCD4linux.BilderSort.value == "1":
			Bilder[2].sort()
		L4logE("Pictures",Bilder[2])

def getWWW():
#	print LCD4linux.WWW1.value , LCD4linux.WWW1url.value , Standby.inStandby, not Standby.inStandby
	if (LCD4linux.WWW1.value != "0" and len(LCD4linux.WWW1url.value)>10) and not Standby.inStandby:
		L4log("WWW Converter check on")
		getHTMLwww(1,LCD4linux.WWW1url.value,LCD4linux.WWW1w.value,LCD4linux.WWW1h.value)
	elif (LCD4linux.StandbyWWW1.value != "0" and len(LCD4linux.StandbyWWW1url.value)>10) and Standby.inStandby:
		L4log("WWW Converter check stb")
		getHTMLwww(1,LCD4linux.StandbyWWW1url.value,LCD4linux.StandbyWWW1w.value,LCD4linux.StandbyWWW1h.value)

def HTMLwwwDownloadFailed(result):
	L4log("HTMLwww download failed:",result)

def HTMLwwwDownloadFinished(filename, result):
	if os.path.isfile(filename):
		L4log("HTMLwww download finished")
		rmFile(WWWpic % "1p")
	else:
		L4log("HTMLwww download finished, no file found")

def getHTMLwww(fn,www,pw,ph):
	filename=WWWpic % str(fn)
	url="http://do.convertapi.com/web2image?curl=%s&PageWidth=%d&PageHight=%d&outputformat=jpg" % (www,pw,ph)
	L4log("downloading HTMLwww from",url)
	downloadPage(url , filename).addCallback(boundFunction(HTMLwwwDownloadFinished, filename)).addErrback(HTMLwwwDownloadFailed)

def xmlFind(Num):
	for i in xmlList:
		if i.startswith("<!--L4L%02d" % Num):
			return i
	return -1

def xmlScreens(Lis2):
	sl = []
	for i in Lis2:
		if i.find("<screen ") != -1:
			b = i.replace("\"","").split("name=")
			sl.append(b[1].split()[0])
	return sl

def xmlInsert(Lis2):
	global xmlList
	if len(Lis2) == 0:
		L4log("insert no Skindata")
		return
	xl = xmlScreens(Lis2)
	for i in range(0,len(xmlList)):
		if xmlList[i].find("<screen ") != -1:
			for i2 in range(0,len(xl)):
				if xmlList[i].find("\"%s\"" % xl[i2]) != -1:
					L4log("disable Screen",xl[i2])
					xmlList[i]=xmlList[i].replace("\"%s\"" % xl[i2],"\"L4L%s\"" % xl[i2])
	L4log("insert Skindata")
	for i in Lis2:
		ttt = LCD4linux.xmlLCDType.value.split("x")
		if LCD4linux.xmlLCDType.value == "96x64":
			i = i.replace("\">","\" id=\"2\">")
		xmlList.insert(-1,i.replace("$w$",ttt[0]).replace("$h$",ttt[1]))

def xmlDelete(Num):
	global xmlList
	delON = False
	isDelete = False
	sli = xmlReadData()
	xl = xmlScreens(sli[Num])
	for i in range(0,len(xmlList)):
		if xmlList[i].find("<screen ") != -1:
			for i2 in range(0,len(xl)):
				if xmlList[i].find("\"L4L%s\"" % xl[i2]) != -1:
					L4log("enable Screen",xl[i2])
					xmlList[i]=xmlList[i].replace("\"L4L%s\"" % xl[i2],"\"%s\"" % xl[i2])
	L4log("remove Skindata",Num)
	i = 0
	aa = 0
	while i<len(xmlList):
		if xmlList[i].startswith("<!--L4L%02d " % Num):
			delON = True
			isDelete = True
		if delON==True:
			if xmlList[i].startswith("<!--L4L%02d-" % Num):
				delON = False
			del xmlList[i]
		else:
			i+=1
	return isDelete

def xmlClear():
	global xmlList
	xmlList = []

def xmlRead():
	global xmlList
	xmlList = []
	if os.path.isfile("/etc/enigma2/skin_user.xml"):
		for i in open("/etc/enigma2/skin_user.xml").read().splitlines():
			xmlList.append(i)
		if len(xmlList)>1:
			while len(xmlList[-1]) < 2 and len(xmlList)>1:
				del xmlList[-1]
	else:
		xmlList=["<skin>","</skin>"]

def xmlReadData():
	sld=[[],[],[],[]]
	if os.path.isfile(Data+"skin_data.xml"):
		aa = 0
		for i in open(Data+"skin_data.xml").read().splitlines():
			if i.startswith("###"):
				break
			if i.startswith("<!--L4L"):
				aa=int(i[7:9])
			sld[aa].append(i)
	return sld

def xmlWrite():
	if len(xmlList)>1:
		L4log("write SkinData")
		fw = open("/etc/enigma2/skin_user.xml","w")
		for i in xmlList:
			fw.write(i+"\n")
		fw.close()

def xmlSkin():
	change=False
	xmlRead()
	if xmlList[-1].find("/skin") == -1:
		L4log("Error xmlSkin")
		return False
	sli=xmlReadData()
	xf = xmlFind(1)
	if xf == -1 and LCD4linux.xmlType01.value == True:
		change=True
		xmlInsert(sli[1])
	elif xf >= 0 and LCD4linux.xmlType01.value == False:
		change=True
		ok=xmlDelete(1)
	xf = xmlFind(2)
	if xf == -1 and LCD4linux.xmlType02.value == True:
		change=True
		xmlInsert(sli[2])
	elif xf >= 0 and LCD4linux.xmlType02.value == False:
		change=True
		ok=xmlDelete(2)
	xf = xmlFind(3)
	if xf == -1 and LCD4linux.xmlType03.value == True:
		change=True
		xmlInsert(sli[3])
	elif xf >= 0 and LCD4linux.xmlType03.value == False:
		change=True
		ok=xmlDelete(3)
	return change
		
class RunShell:
	def __init__(self, cmd):
		global ShellRunning
		ShellRunning = True
		L4log("Shell",cmd)
		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.cmdFinished)
		self.container.dataAvail.append(self.dataAvail)
		self.container.execute(cmd)

	def cmdFinished(self, data):
		global ShellRunning
		ShellRunning = False
		L4log("Shell Stop")

	def dataAvail(self, data):
		global ShellRunning
		ShellRunning = False
		L4log("Shell Data")

def TFTCheck(Force,SetMode=""):
	global AktTFT
	if os.path.isfile("/usr/bin/tft-bmp-mode.sh") == True and os.path.isfile("/usr/bin/tft-dream-mode.sh") == True:
		CurTFT = os.path.isfile("/etc/grautec/settings/takeownership")
		L4logE("TFT mode...",CurTFT)
		if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4" or LCD4linux.LCDType3.value[0] == "4" and SetMode != "DREAM":
			L4logE("TFT enabled")
			if AktTFT != "BMP" or Force == True or SetMode == "BMP":
				i=10
				while ShellRunning == True and i > 0:
					sleep(0.5)
					i -= 1
				RunShell("/usr/bin/tft-bmp-mode.sh")
				AktTFT = "BMP"
		else:
			L4logE("TFT not")
			if (AktTFT != "DREAM" and CurTFT == True) or Force == True or SetMode == "DREAM":
				i=10
				while ShellRunning == True and i > 0:
					sleep(0.5)
					i -= 1
				RunShell("/usr/bin/tft-dream-mode.sh")
				AktTFT = "DREAM"

def SamsungCheck():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if USBok == False:
		return True
	if LCD4linux.LCDType1.value[0] == "2":
		known_devices_list = Photoframe.get_known_devices()
		device0 = known_devices_list[(int(LCD4linux.LCDType1.value[1:])-3)*2]
		if find_dev(1,device0["idVendor"],device0["idProduct"]) == False:
			L4log("Samsung 1 Stat failed")
			SamsungDevice = None
			return True
		if Photoframe.name(SamsungDevice) is None:
			L4log("Samsung 1 no answer")
			SamsungDevice = None
			return True
	if LCD4linux.LCDType2.value[0] == "2":
		known_devices_list = Photoframe.get_known_devices()
		device0 = known_devices_list[(int(LCD4linux.LCDType2.value[1:])-3)*2]
		Anz=2 if LCD4linux.LCDType1.value == LCD4linux.LCDType2.value else 1
		if find_dev(Anz,device0["idVendor"],device0["idProduct"]) == False:
			L4log("Samsung 2 Stat failed")
			SamsungDevice2 = None
			return True
		if Photoframe.name(SamsungDevice2) is None:
			L4log("Samsung 2 no answer")
			SamsungDevice2 = None
			return True
	if LCD4linux.LCDType3.value[0] == "2":
		known_devices_list = Photoframe.get_known_devices()
		device0 = known_devices_list[(int(LCD4linux.LCDType3.value[1:])-3)*2]
		Anz=2 if LCD4linux.LCDType1.value == LCD4linux.LCDType3.value else 1
		if find_dev(Anz,device0["idVendor"],device0["idProduct"]) == False:
			L4log("Samsung 3 Stat failed")
			SamsungDevice3 = None
			return True
		if Photoframe.name(SamsungDevice3) is None:
			L4log("Samsung 3 no answer")
			SamsungDevice3 = None
			return True
	return False

def getSamsungDevice():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if USBok == True:
		if LCD4linux.LCDType1.value[0] == "2":
			if SamsungDevice is None:
				L4log("get Samsung Device...")
				known_devices_list = Photoframe.get_known_devices()
				device0 = known_devices_list[(int(LCD4linux.LCDType1.value[1:])-3)*2]
				device1 = known_devices_list[(int(LCD4linux.LCDType1.value[1:])-3)*2+1]
				if find_dev(1,device0["idVendor"],device0["idProduct"]) == True or find_dev(1,device1["idVendor"],device1["idProduct"]) == True:
					try:
						SamsungDevice = Photoframe.init_device(1, device0, device1)
					except:
						pass
		if LCD4linux.LCDType2.value[0] == "2":
			if SamsungDevice2 is None:
				L4log("get Samsung2 Device...")
				known_devices_list = Photoframe.get_known_devices()
				device0 = known_devices_list[(int(LCD4linux.LCDType2.value[1:])-3)*2]
				device1 = known_devices_list[(int(LCD4linux.LCDType2.value[1:])-3)*2+1]
				Anz=2 if LCD4linux.LCDType1.value == LCD4linux.LCDType2.value else 1
				if Anz == 2:
					if find_dev2(device0["idVendor"],device0["idProduct"],device1["idVendor"],device1["idProduct"]) == True:
						try:
							SamsungDevice2 = Photoframe.init_device(Anz, device0, device1)
						except:
							pass
				else:
					if find_dev(Anz,device0["idVendor"],device0["idProduct"]) == True or find_dev(Anz,device1["idVendor"],device1["idProduct"]) == True:
						try:
							SamsungDevice2 = Photoframe.init_device(Anz, device0, device1)
						except:
							pass
		if LCD4linux.LCDType3.value[0] == "2":
			if SamsungDevice3 is None:
				L4log("get Samsung3 Device...")
				known_devices_list = Photoframe.get_known_devices()
				device0 = known_devices_list[(int(LCD4linux.LCDType3.value[1:])-3)*2]
				device1 = known_devices_list[(int(LCD4linux.LCDType3.value[1:])-3)*2+1]
				Anz=2 if LCD4linux.LCDType1.value == LCD4linux.LCDType3.value else 1
				if Anz == 2:
					if find_dev2(device0["idVendor"],device0["idProduct"],device1["idVendor"],device1["idProduct"]) == True:
						try:
							SamsungDevice3 = Photoframe.init_device(Anz, device0, device1)
						except:
							pass
				else:
					if find_dev(Anz,device0["idVendor"],device0["idProduct"]) == True or find_dev(Anz,device1["idVendor"],device1["idProduct"]) == True:
						try:
							SamsungDevice3 = Photoframe.init_device(Anz, device0, device1)
						except:
							pass

def DpfCheck():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if USBok == False:
		return True
	if LCD4linux.LCDType1.value[0] == "1":
		if find_dev(1,0x1908,0x0102) == False or SamsungDevice is None:
			L4log("DPF 1 Stat failed")
			dpf.close(SamsungDevice)
			SamsungDevice = None
			return True
	if LCD4linux.LCDType2.value[0] == "1":
		Anz=2 if LCD4linux.LCDType1.value == LCD4linux.LCDType2.value else 1
		if find_dev(Anz,0x1908,0x0102) == False or SamsungDevice2 is None:
			L4log("DPF 2 Stat failed")
			dpf.close(SamsungDevice2)
			SamsungDevice2 = None
			return True
	if LCD4linux.LCDType3.value[0] == "1":
		Anz=2 if LCD4linux.LCDType1.value == LCD4linux.LCDType3.value else 1
		if find_dev(Anz,0x1908,0x0102) == False or SamsungDevice3 is None:
			L4log("DPF 3 Stat failed")
			dpf.close(SamsungDevice3)
			SamsungDevice3 = None
			return True
	return False

def getDpfDevice():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if USBok == False:
		return
	if LCD4linux.LCDType1.value[0] == "1":
		if SamsungDevice is None:
			L4log("get DPF Device...")
			if find_dev(1,0x1908,0x0102) == True:
				try:
					L4log("open DPF Device0...")
					SamsungDevice = dpf.open("usb0")
				except:
					L4log("open Error DPF1 Device0")
					SamsungDevice = None
			else:
				L4log("DPF1 Device0 not found")
	if LCD4linux.LCDType2.value[0] == "1":
		if SamsungDevice2 is None:
			L4log("get DPF2 Device...")
			Anz=2 if LCD4linux.LCDType1.value == LCD4linux.LCDType2.value else 1
			if Anz == 2:
				if find_dev(2,0x1908,0x0102) == True:
					try:
						L4log("open DPF2 Device1...")
						SamsungDevice2 =  dpf.open("usb1")
					except:
						L4log("open Error DPF2 Device1")
						SamsungDevice2 = None
				else:
					L4log("DPF2 Device1 not found")
			else:
				if find_dev(1,0x1908,0x0102) == True:
					try:
						L4log("open DPF2 Device0...")
						SamsungDevice2 = dpf.open("usb0")
					except:
						L4log("open Error DPF2 Device0")
						SamsungDevice2 = None
				else:
					L4log("DPF2 Device0 not found")
	if LCD4linux.LCDType3.value[0] == "1":
		if SamsungDevice3 is None:
			L4log("get DPF3 Device...")
			Anz=2 if LCD4linux.LCDType1.value == LCD4linux.LCDType3.value else 1
			if Anz == 2:
				if find_dev(2,0x1908,0x0102) == True:
					try:
						L4log("open DPF3 Device1...")
						SamsungDevice3 =  dpf.open("usb1")
					except:
						L4log("open Error DPF3 Device1")
						SamsungDevice3 = None
				else:
					L4log("DPF2 Device1 not found")
			else:
				if find_dev(1,0x1908,0x0102) == True:
					try:
						L4log("open DPF3 Device0...")
						SamsungDevice3 = dpf.open("usb0")
					except:
						L4log("open Error DPF3 Device0")
						SamsungDevice3 = None
				else:
					L4log("DPF3 Device0 not found")

def DpfCheckSerial():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if LCD4linux.LCDType1.value[0] == "1" and LCD4linux.LCDType1.value == LCD4linux.LCDType2.value:
		if SamsungDevice is not None and SamsungDevice2 is not None:
			s1,s2 = "",""
			try:
				s1 = "".join(struct.unpack("sxsxsx",SamsungDevice.readFlash(0x180ED3,6)))
			except:
				dpf.close(SamsungDevice)
				SamsungDevice = None
				L4log("Error Read DPF Device")
				return
			try:
				s2 = "".join(struct.unpack("sxsxsx",SamsungDevice2.readFlash(0x180ED3,6)))
			except:
				dpf.close(SamsungDevice2)
				SamsungDevice2 = None
				L4log("Error Read DPF2 Device")
				return
			L4log(s1,s2)
			if s1.startswith("0.") and s2.startswith("0."):
				if s1 > s2:
					Exchange()
	
def Exchange():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if LCD4linux.LCDType1.value == LCD4linux.LCDType2.value:
		SamsungDevice, SamsungDevice2 = SamsungDevice2, SamsungDevice

def CheckFstab():
	if os.path.isfile("/etc/fstab"):
		f = open("/etc/fstab","r")
		if f.read().lower().find("usbfs") == -1:
			L4log("Info: no usbfs-Line in fstab")
		f.close()

def FritzCallLCD4Linux(event,Date,number,caller,phone):
	global FritzTime
	if (LCD4linux.Fritz.value != "0" or LCD4linux.MPFritz.value != "0" or LCD4linux.StandbyFritz.value != "0"):
		L4log("FritzCall",[event,Date,number,caller,phone])
		if len(FritzList)>0:
			if Date==FritzList[-1][1]:
				L4log("FritzCall ignore")
				return
		rmFile(PICfritz)
		FritzList.append([event,Date,number,caller,phone])
		FritzTime = int(LCD4linux.FritzTime.value) + 2
		while len(FritzList) > 20:
			del FritzList[0]
		if BriefLCD.qsize()<=2:
			BriefLCD.put(1) 

def NcidLCD4Linux(Date,number,caller):
	global FritzTime
	if (LCD4linux.Fritz.value != "0" or LCD4linux.MPFritz.value != "0" or LCD4linux.StandbyFritz.value != "0"):
		L4log("Ncid",[Date,number,caller])
		rmFile(PICfritz)
		dt = datetime.strptime(Date, "%d.%m.%Y - %H:%M")
		Date = dt.strftime("%d.%m.%y %H:%M:%S")
		FritzList.append(["RING",Date,number,caller,""])
		FritzTime = int(LCD4linux.FritzTime.value) + 2
		while len(FritzList) > 20:
			del FritzList[0]
		if BriefLCD.qsize()<=2:
			BriefLCD.put(1) 

# Load Config
if os.path.isfile(LCD4config):
	f=open(LCD4config,"r")
	L = f.read()
	f.close()
	if "Netatmo" in L:
		L=L.replace("Netatmo","NetAtmo")
		w = open(LCD4config,"w")
		w.write(L)
		w.close()
	LCD4linux.loadFromFile(LCD4config)
	LCD4linux.load()
else:
	L4log("no config found!")

try:
	from Plugins.Extensions.FritzCall.plugin import registerUserAction as FritzCallRegisterUserAction
	FritzCallRegisterUserAction(FritzCallLCD4Linux)
	L4log("Register FritzCall ok")
except:
	L4log("FritCall not registered")

try:
	from Plugins.Extensions.NcidClient.plugin import registerUserAction as NcidClientRegisterUserAction
	NcidClientRegisterUserAction(NcidLCD4Linux)
	L4log("Register NcidClient ok")
except:
	L4log("NcidClient not registered")

try:
	from Plugins.Extensions.BitrateViewer.bitratecalc import eBitrateCalculator
	BitrateRegistred = True
	L4log("Register Bitrate ok")
except:
	BitrateRegistred = False
	L4log("Bitrate not registered")

try:
	from Plugins.Extensions.webradioFS.ext import ext_l4l
	WebRadioFS = ext_l4l()
	WebRadioFSok = True
	L4log("Register WebRadioFS ok")
except:
	WebRadioFSok = False
	L4log("WebRadioFS not registered")

try:
	from Plugins.Extensions.Netatmo.Netatmo import netatmo
	from Plugins.Extensions.Netatmo.NetatmoCore import NetatmoUnit
	NetatmoOK = True
	L4log("Register Netatmo ok")
except:
	NetatmoOK = False
	L4log("Netatmo not registered")

class GrabOSD:
	def __init__(self, cmd):
		global GrabRunning
		GrabRunning = True
		L4logE("Grab Run")

#		self.container = eConsoleAppContainer()
#		self.container.appClosed.append(self.cmdFinished)
#		self.container.dataAvail.append(self.dataAvail)

#		self.container.execute(cmd)
		os.system(cmd + " >/dev/null 2>&1")
		self.cmdFinished("")

	def cmdFinished(self, data):
		global GrabRunning
		L4logE("Grab Stop")
		GrabRunning = False

	def dataAvail(self, data):
		pass


# Grab
def doGrab(i,ConfigFast,ConfigSize):
	CF = "" if ConfigFast == True else "-b"
	GrabOSD("/usr/bin/grab -o -p -j 95 %s -r %d %sdpfgrab.jpg" % (CF,ConfigSize,TMPL) ) 

def InitWebIF():
	L4log("WebIf-Init...")
	i=20
	if LCD4linux.WebIfInitDelay.value == True:
		while len(glob.glob("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/__init__.py*")) == 0 and i > 0:
			sleep(0.5)
			i-=1
	if i > 0 and len(glob.glob("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/__init__.py*")) > 0:
		if i<20:
			L4log("WebIf-Wait %d s" % int((20-i)/2))
			sleep(5)
		from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
		from twisted.web import static
		from WebSite import LCD4linuxweb
		from WebConfigSite import LCD4linuxConfigweb
		L4log("Child to WebIf...")
		root = static.File("%slcd4linux" % TMP)
		root.putChild("", LCD4linuxweb())
		root.putChild("config", LCD4linuxConfigweb())
		root.putChild("data",static.File(Data[:-1]))
		if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web/external.xml"):
			try:
				addExternalChild( ("lcd4linux", root, "LCD4linux", Version, True) )
				L4log("use new WebIf")
			except:
				addExternalChild( ("lcd4linux", root) )
				L4log("Error, fall back to old WebIf")
		else:
			addExternalChild( ("lcd4linux", root) )
			L4log("use old WebIf")
		if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/OpenWebif/pluginshook.src"):
			try:
				addExternalChild( ("lcd4linux", root, "LCD4linux", Version) )
				L4log("use OpenWebIf")
			except:
				pass
	else:
		L4log("no WebIf found")

class L4LWorker1(Thread): 
	def __init__(self,index,s,session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s
 
	def run(self): 
		while True:
			try:
				para = Brief1.get()
#				print "1:",para[0]
				if len(para) == 2:
					para[0](para[1])
				elif len(para) == 4:
					para[0](para[1],para[2],para[3])
				elif len(para) == 5:
					para[0](para[1],para[2],para[3],para[4])
				elif len(para) == 3:
					para[0](para[1],para[2])
				elif len(para) == 7:
					para[0](para[1],para[2],para[3],para[4],para[5],para[6])
			except:
				from traceback import format_exc
				L4log("Error1:",format_exc() )
				try:
					open(CrashFile,"w").write(format_exc())
				except:
					pass
			Brief1.task_done() 

class L4LWorker2(Thread): 
	def __init__(self,index,s,session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s
 
	def run(self): 
		while True:
			try:
				para = Brief2.get()
#				print "2:",para[0]
				if len(para) == 2:
					para[0](para[1])
				elif len(para) == 4:
					para[0](para[1],para[2],para[3])
				elif len(para) == 5:
					para[0](para[1],para[2],para[3],para[4])
				elif len(para) == 3:
					para[0](para[1],para[2])
				elif len(para) == 7:
					para[0](para[1],para[2],para[3],para[4],para[5],para[6])
			except:
				from traceback import format_exc
				L4log("Error2:",format_exc() )
				try:
					open(CrashFile,"w").write(format_exc())
				except:
					pass
			Brief2.task_done() 

class L4LWorker3(Thread): 
	def __init__(self,index,s,session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s
 
	def run(self): 
		while True:
			try:
				para = Brief3.get()
#				print "2:",para[0]
				if len(para) == 2:
					para[0](para[1])
				elif len(para) == 4:
					para[0](para[1],para[2],para[3])
				elif len(para) == 5:
					para[0](para[1],para[2],para[3],para[4])
				elif len(para) == 3:
					para[0](para[1],para[2])
				elif len(para) == 7:
					para[0](para[1],para[2],para[3],para[4],para[5],para[6])
			except:
				from traceback import format_exc
				L4log("Error3:",format_exc() )
				try:
					open(CrashFile,"w").write(format_exc())
				except:
					pass
			Brief3.task_done() 

class L4LWorkerLCD(Thread): 
	def __init__(self,index,s,session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s
 
	def run(self): 
		global FritzTime
		while True:
			zahl = BriefLCD.get()
			if zahl == 1:
				ergebnis = self.GeneratePicture(self.index)
 
			BriefLCD.task_done() 
 
	def GeneratePicture(self,i): 
		L4logE("Run Worker Pic",i)
		gc.disable()
		LCD4linuxPICThread(self.s,self.session)
		gc.enable()
		L4logE("Done Worker Pic",i)
		return "ok"

class L4LWorker(Thread): 
	QuickRunning = False
	def __init__(self,index,s,session):
		Thread.__init__(self)
#			self.Ergebnis = {} 
#			self.ErgebnisLock = Lock() 
		self.index = index
		self.session = session
		self.s = s
#		self.QuickRunning = False
#			self.Briefkasten = Queue.Queue() 
 
	def run(self): 
		global FritzTime
		while True:
#			print "worker a", self.index
			zahl = Briefkasten.get()
#			print "Briefkasten",zahl
			if zahl == 1:
				pass
			elif zahl == 2:
				doGrab(self.index,LCD4linux.OSDfast.value, LCD4linux.OSDsize.value)
			elif zahl == 3:
				if (LCD4linux.Fritz.value != "0" or LCD4linux.MPFritz.value != "0" or LCD4linux.StandbyFritz.value != "0"):
					if os.path.isfile(Fritz):
						FritzList.append(open(Fritz,"r").read().split(";"))
						rmFile(Fritz)
						rmFile(PICfritz)
						FritzTime = int(LCD4linux.FritzTime.value) + 2
						while len(FritzList) > 20:
							del FritzList[0]
						ergebnis = self.GeneratePicture(self.index)
			elif zahl == 4:
				self.runICS()
			elif zahl == 5:
				self.hookWebif()
			elif zahl == 6:
				self.runMail()
			elif zahl == 7:
				if QuickList != [[],[],[]] and L4LWorker.QuickRunning == False and ThreadRunning == 0 and OSDon == 0 and FritzTime == 0:
					self.QuickBild()
			elif zahl == 8:
				ICSdownloads()
#				self.ErgebnisLock.acquire() 
#				self.Ergebnis[zahl] = ergebnis 
#				self.ErgebnisLock.release() 
 
			Briefkasten.task_done() 
#			print "worker e", self.index

	def getICS(self,name,col):
		global ICS
		global ICSlist
		if len(name)<3 or "..." in name:
			L4logE("ignore ICS",name)
			return
		try:
			r=None
			rs=""
			try:
				if name.startswith("http") and len(name) > 10:
					r=urllib2.urlopen(name, timeout = 10)
				elif os.path.isfile(name):
					r=open(name,"rb")
				else:
					L4log("Error: no ICS found",name)
					return
			except:
				L4log("Error: ICS Open",name)
				return
			if r is not None:
				L4log("Read ICS",name)
				try:
					rs = r.read()
					r.close()
					ICSlist.append([rs,col])
					return
				except:
					L4log("Error: ICS not readable!",name)
					return
			else:
				L4logE("Error Read ICS",name)

		except:
			from traceback import format_exc
			L4log("Error ICS",name)
			L4log("Error:",format_exc() )
			try:
				open(CrashFile,"w").write(format_exc())
			except:
				pass

	def runICS(self):
		global ICSrunning
		if ICSrunning == True:
			L4log("Block ICS...")
			return
		ICSrunning = True
		L4log("Reading ICS...")
		for dics in glob.glob(os.path.join(LCD4linux.CalPath.value,"*.ics")):
			self.getICS(dics,0)
		self.getICS(LCD4linux.CalHttp.value,1)
		self.getICS(LCD4linux.CalHttp2.value,2)
		self.getICS(LCD4linux.CalHttp3.value,3)
		ICSdownloads()
		rmFile(PICcal)
		ICSrunning = False
	
	def hookWebif(self):
		InitWebIF()
	
	def runMail(self):
		global PopMail
		global PopMailUid
		import poplib
		import imaplib
		
		def MailDecode(Sdecode):
			try:
				H = decode_header(Sdecode)
				W = ""
				for HH in H:
					if HH[1] == None:
						W += HH[0]
					else:
						W += HH[0].decode(HH[1])
			except:
				L4logE("Info, can not decode:",Sdecode)
				W = Sdecode
			return W

		S = [LCD4linux.Mail1Pop.value,LCD4linux.Mail2Pop.value,LCD4linux.Mail3Pop.value,LCD4linux.Mail4Pop.value,LCD4linux.Mail5Pop.value]
		U = [LCD4linux.Mail1User.value,LCD4linux.Mail2User.value,LCD4linux.Mail3User.value,LCD4linux.Mail4User.value,LCD4linux.Mail5User.value]
		P = [LCD4linux.Mail1Pass.value,LCD4linux.Mail2Pass.value,LCD4linux.Mail3Pass.value,LCD4linux.Mail4Pass.value,LCD4linux.Mail5Pass.value]
		C = [LCD4linux.Mail1Connect.value,LCD4linux.Mail2Connect.value,LCD4linux.Mail3Connect.value,LCD4linux.Mail4Connect.value,LCD4linux.Mail5Connect.value]
		if P == ["","","","",""]:
			return
		if int(strftime("%H")) == 0:
			PopMailUid = [["","",""],["","",""],["","",""],["","",""],["","",""]]
		for i in range(0,5):
			if len(PopMail[i]) > 0 and PopMail[i][0][2]<>"":
				PopMailUid[i][1] = PopMail[i][0][2]
		PopMail = [[],[],[],[],[],"Run"]
		for i in range(0,5):
			if S[i].find(".")<S[i].rfind("."):
				L4log("Mailserver",S[i])
				if C[i] in ["0","1"]:
					try:
						if C[i] == "0":
							mailserver = poplib.POP3_SSL(S[i])
						elif C[i] == "1":
							mailserver = poplib.POP3(S[i])
					except:
						L4log("Error:",S[i])
						PopMail[i].append(["Server Error","",""])
						continue
					try:
						ret=mailserver.user(U[i].split(":")[-1])
						L4log(ret)
						if ret.upper().find("OK")>=0:
							ret=mailserver.pass_(P[i])
							L4log(ret)
						PopMailUid[i][2] = ret
					except:
						L4log("Error:",U[i])
						PopMail[i].append(["User Error","",""])
						continue
					try:
						L4logE(mailserver.stat())
						for M in range(1,int(mailserver.stat()[0])+1):
							From = ""
							Subj = ""
	#						L4logE("M",M)
							for R in mailserver.retr(M)[1]:
	#							L4logE("R",R)
								if R.upper().startswith("FROM:"):
									From = R[R.find(" "):].strip()
								elif R.upper().startswith("SUBJECT:"):
									Subj = R[R.find(" "):].strip()
								if From != "" and Subj != "":
									break
							Subj = MailDecode(Subj)
							From = MailDecode(From)
							L4logE([From,Subj,mailserver.uidl()[1][M-1].split()[1]])
							PopMail[i].append([From,Subj,mailserver.uidl()[1][M-1].split()[1]])
					except:
						L4log("Mail Error:",U[i])
						PopMail[i].append(["Mail Error","",""])
						from traceback import format_exc
						L4log("Error:",format_exc() )
						try:
							open(CrashFile,"w").write(format_exc())
						except:
							pass
						continue
					try:
						mailserver.quit()
						del mailserver
					except:
						L4Log("Mail-Error Quit")
				elif C[i] in ["2","3"]:
					try:
						if C[i] == "2":
							mailserver = imaplib.IMAP4_SSL(S[i])
						elif C[i] == "3":
							mailserver = imaplib.IMAP4(S[i])
					except:
						L4log("Error:",S[i])
						PopMail[i].append(["Server Error","",""])
						continue
					try:
						ret = mailserver.login(U[i].split(":")[-1], P[i])
						L4log(ret)
						PopMailUid[i][2] = ret
					except:
						L4log("Error:",U[i])
						PopMail[i].append(["User Error","",""])
						continue
					try:
						mailserver.select('inbox')
						typ, data = mailserver.search(None, 'ALL')
						ids = data[0]
						id_list = ids.split()
						if len(id_list)>0:
							latest_email_id = int( id_list[-1] )
							L4logE(typ, data)
							for M in range(1,int(latest_email_id)+1):
								From = ""
								Subj = ""
								ID = ""
								typ, data = mailserver.fetch( str(M), '(RFC822)' )
								for response_part in data:
									if isinstance(response_part, tuple):
										msg = email.message_from_string(response_part[1])
										Subj = msg['subject']
										From = msg['from']
										ID = msg["Message-ID"]
								Subj = MailDecode(Subj)
								From = MailDecode(From)
								L4logE([From,Subj,ID])
								PopMail[i].append([From,Subj,ID])
					except:
						L4log("Mail Error:",U[i])
						PopMail[i].append(["Mail Error","",""])
						from traceback import format_exc
						L4log("Error:",format_exc() )
						try:
							open(CrashFile,"w").write(format_exc())
						except:
							pass
						continue
					try:
						mailserver.close()
						del mailserver
					except:
						L4Log("Mail-Error Close")

				if len(PopMail[i]) > 0:
					PopMail[i] = list(reversed(PopMail[i]))
					L4logE("currend ID",PopMailUid[i][0])
					if PopMailUid[i][0] == "" or not (PopMailUid[i][0] in (e[2] for e in PopMail[i]) ):
						if len(PopMail[i]) > 1 or PopMailUid[i][0] != "-":
							PopMailUid[i][0] = PopMail[i][0][2]
							L4logE("new ID",PopMailUid[i][0])
				else:
					PopMailUid[i][0] = "-"
		PopMail[5]=""

	def QuickLoad(self,Pim,P0,P1,P2,P3,P4):
		ShowPicture = getShowPicture(P0,0)
		if os.path.isfile(ShowPicture):
			try:
				Pimg = Image.open(ShowPicture)
				Pimg = Pimg.resize((P3, P4))
				Pim.paste(Pimg,(P1,P2))
			except:
				L4log("Error Quick Pic")

	def QuickBild(self):
		pt = time()
		L4LWorker.QuickRunning = True
		try:
			if len(QuickList[0]) > 0:
				if QuickIM[0] != None:
					for P in QuickList[0]:
						Brief1.put([self.QuickLoad,QuickIM[0],P[0],P[1],P[2],P[3],P[4]])
					Brief1.join()
					Brief1.put([writeLCD1,QuickIM[0],LCD4linux.BilderJPEGQuick.value,False])
			if len(QuickList[1]) > 0:
				if QuickIM[1] != None:
					for P in QuickList[1]:
						Brief2.put([self.QuickLoad,QuickIM[1],P[0],P[1],P[2],P[3],P[4]])
					Brief2.join()
					Brief2.put([writeLCD2,QuickIM[1],LCD4linux.BilderJPEGQuick.value,False])
			if len(QuickList[2]) > 0:
				if QuickIM[2] != None:
					for P in QuickList[2]:
						Brief2.put([self.QuickLoad,QuickIM[2],P[0],P[1],P[2],P[3],P[4]])
					Brief3.join()
					Brief3.put([writeLCD3,QuickIM[2],LCD4linux.BilderJPEGQuick.value,False])
			Brief1.join()
			Brief2.join()
			Brief3.join()
			L4LWorker.QuickRunning = False
			L4log("QuickTime: %.3f " % (time()-pt))
		except:
			L4LWorker.QuickRunning = False
			from traceback import format_exc
			L4log("QuickPic Error:",format_exc() )
			try:
				open(CrashFile,"w").write(format_exc())
			except:
				pass

class LCDdisplayMenu(Screen):
	skin = """
		<screen position="center,center" size="600,380" title="LCD4linux - Config" >
			<widget name="menu" position="10,20" size="580,350" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session

		self.list = []
		self.SetList()
		self["menu"] = MenuList(self.list)
		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], 
		{
			"ok": self.keyOK,
			"cancel": self.cancel,
			"red": self.entfernen
		}, -1)

	def SetList(self):
		self.list = []
		self.list.append((_("Load Active Config-File"), "LoadConfig", ""))
		self.list.append((_("Load Defaults"), "LoadDefault", ""))
		self.list.append((_("Save Config to File... (%s)") % LCD4linux.ConfigPath.value, "SaveToConfig", ""))
		Cdir = glob.glob(os.path.join(LCD4linux.ConfigPath.value,"*.lcd"))
		Cdir.sort()
		xx = 3
		for ii in Cdir:
			self.list.append((_("Load File : %s") % os.path.basename(ii), "LoadFile %d" % xx, ii))
			xx += 1

	def entfernen(self):
		current = self["menu"].getCurrent()
		if current:
			currentEntry = current[1]
			if currentEntry.startswith("LoadFile") and current[0].find(" : ")>0:
				if os.path.isfile(current[2]):
					self.session.openWithCallback(self.askForDelete, MessageBox, _("Delete File?"),type = MessageBox.TYPE_YESNO,timeout = 60)

	def keyOK(self):
		current = self["menu"].getCurrent()
		if current:
			currentEntry = current[1]
			L4log(currentEntry) 
			if currentEntry == "LoadConfig":
				if os.path.isfile(LCD4config):
					L4log("Config-Load",LCD4config) 
					LCD4linux.loadFromFile(LCD4default)
					LCD4linux.loadFromFile(LCD4config)
					LCD4linux.load()
			elif currentEntry == "SaveToConfig":
				self.session.openWithCallback(self.askForConfigName,InputBox, title="Save Filename", text="LCD4linux-%s" % (strftime("%Y%m%d_%H%M")), type=Input.TEXT)
			elif currentEntry.startswith("LoadFile"):
				if os.path.isfile(current[2]):
					P1=LCD4linux.ConfigPath.value
					P2=LCD4linux.PiconPath.value
					P3=LCD4linux.PiconPathAlt.value
					P4=LCD4linux.PiconCache.value
					P5=LCD4linux.WetterPath.value
					if os.path.isfile(LCD4default):
						LCD4linux.loadFromFile(LCD4default)
					L4log("Config-Load",current[2]) 
					LCD4linux.loadFromFile(current[2])
					LCD4linux.load()
					LCD4linux.ConfigPath.value=P1
					LCD4linux.PiconPath.value=P2
					LCD4linux.PiconPathAlt.value=P3
					LCD4linux.PiconCache.value=P4
					LCD4linux.WetterPath.value=P5
			elif currentEntry == "LoadDefault":
				if os.path.isfile(LCD4default):
					L4log("Config-Load",LCD4default) 
					LCD4linux.loadFromFile(LCD4default)
					LCD4linux.load()

	def askForConfigName(self,name):
		if name is not None and os.path.isdir(LCD4linux.ConfigPath.value):
			LCD4linux.save()
			LCD4linux.saveToFile(os.path.join(LCD4linux.ConfigPath.value,name + ".lcd"))
			self.list.append((_("Load File : %s") % (name+".lcd"), "LoadFile", os.path.join(LCD4linux.ConfigPath.value,name + ".lcd")))


	def askForDelete(self,retval):
		if (retval):
			current = self["menu"].getCurrent()
			if current:
				if os.path.isfile(current[2]):
					currentEntry = current[1]
					i = int(currentEntry.split()[1])
					self.list[i] = (_("deleted"),) + self.list[i][1:]
					rmFile(current[2])

	def cancel(self):
		self.close(False,self.session)

	def selectionChanged(self):
		a=0

class LCDdisplayFile(Screen):
	skin = """
		<screen position="center,center" size="620,460" title="Select File/Dir...">
			<widget source="File" render="Label" font="Regular;20" halign="center" position="5,0" size="610,100" transparent="1" valign="center" zPosition="4"/>
			<widget name="LCDfile" position="5,100" scrollbarMode="showOnDemand" size="610,312" zPosition="4"/>
			<eLabel backgroundColor="#555555" position="5,420" size="610,2" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="skin_default/buttons/green.png" position="0,425" size="140,40" zPosition="5"/>
			<eLabel font="Regular;18" halign="center" position="0,425" size="140,40" text="Select" transparent="1" valign="center" zPosition="6"/>
		</screen>"""

	def __init__(self, session, FileName = "/tmp/none", showFiles = True, text = "Text", matchingPattern = None):
		Screen.__init__(self, session)
		self.sesion = session
		if not FileName.startswith("/"):
			FileName = "/"+FileName
		self["File"] = StaticText(_("currently set : %s") % FileName)
		self["LCDfile"] = myFileList(FileName, showDirectories = True, showFiles = showFiles, useServiceRef = False, matchingPattern = matchingPattern)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.ok,
			"back": self.NothingToDo,
			"green": self.SelectFile,
			"yellow": self.SelectFile
		}, -1)
		self.onLayoutFinish.append(self.OneDescent)

	def OneDescent(self):
		if self["LCDfile"].canDescent():
			self["LCDfile"].descent()
	
	def ok(self):
		if self["LCDfile"].canDescent():
			self["LCDfile"].descent()

	def NothingToDo(self):
		self.close("","")

	def SelectFile(self):
		dest = ""
		dest1 = ""
		if self["LCDfile"].getSelectionIndex()!=0:
#			dest = self["LCDfile"].getSelection()[0]
			dest = self["LCDfile"].getCurrentDirectory()
			dest1 = self["LCDfile"].getFilename()
		self.close(dest,dest1)

class LCDdisplayConfig(ConfigListScreen,Screen):
	skin = ""
		
	def __init__(self, session, args = 0):
		global ConfigMode
		global OSDon
		size_w = getDesktop(0).size().width()-100
		size_h = getDesktop(0).size().height()-100 #870x400 conf 600x328 (25*Lines)
		if size_w<700:
			size_w = 600
		self.ConfLines = (size_h-72)//25 
		conf_h = self.ConfLines*25
		int_y = size_h-65
		key_y = size_h-40
		pic_w = size_w-600
		if LCD4linux.LCDType3.value != "00":
			pic_h = int(size_h/3)
		else:
			pic_h = int(size_h/2)
		pic_h2 = pic_h*2
		skin = """
			<screen position="center,%d" size="%d,%d" title="LCD4linux Settings" >
			<widget name="config" position="0,0" size="600,%d" scrollbarMode="showOnDemand" enableWrapAround="1" />
			<widget source="introduction" render="Label" position="5,%d" size="580,30" zPosition="10" font="Regular;21" halign="center" valign="center" backgroundColor="#25062748" transparent="1" />
			
			<widget name="key_red" position="0,%d" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/> 
			<widget name="key_green" position="140,%d" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/> 
			<widget name="key_yellow" position="280,%d" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/> 
			<widget name="key_blue" position="420,%d" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/> 

			<ePixmap name="red"    position="0,%d"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,%d" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,%d" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,%d" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/key_menu.png" position="560,%d" zPosition="4" size="35,25"  transparent="1" alphatest="on" />

			<widget source="Version" render="Label" position="500,%d" size="100,20" zPosition="1" font="Regular;11" halign="right" valign="center" backgroundColor="#25062748" transparent="1" />
			<widget source="LibUSB" render="Label" position="500,%d" size="100,20" zPosition="1" font="Regular;11" halign="right" valign="center" foregroundColor="red" backgroundColor="#25062748" transparent="1" />
			<widget source="About" render="Label" position="500,%d" size="100,20" zPosition="1" font="Regular;10" halign="right" valign="center" backgroundColor="#25062748" transparent="1" />

			<widget name="LCD1" position="600,0" zPosition="1" size="%d,%d" transparent="1" alphatest="on" />
			<widget name="LCD2" position="600,%d" zPosition="1" size="%d,%d" transparent="1" alphatest="on" />
			<widget name="LCD3" position="600,%d" zPosition="1" size="%d,%d" transparent="1" alphatest="on" />
			<widget source="LCD1text" render="Label" position="600,5" size="200,20" zPosition="1" font="Regular;11" halign="left" valign="center" backgroundColor="#25062748" transparent="1" />
			<widget source="LCD2text" render="Label" position="600,%d" size="200,20" zPosition="1" font="Regular;11" halign="left" valign="center" backgroundColor="#25062748" transparent="1" />
			<widget source="LCD3text" render="Label" position="600,%d" size="200,20" zPosition="1" font="Regular;11" halign="left" valign="center" backgroundColor="#25062748" transparent="1" />
			
			</screen>""" % (75, size_w,size_h, conf_h, int_y, key_y,key_y,key_y,key_y, key_y,key_y,key_y,key_y,
			key_y+15, key_y-10,key_y-30,key_y-30,  pic_w,pic_h, pic_h,pic_w,pic_h, pic_h2,pic_w,pic_h, pic_h+5, pic_h2+5 )
		self.skin = skin
		self.session = session
		Screen.__init__(self, session)
		L4log("init Start")
		ConfigMode = True
		OSDon = 0
		getBilder()
		self.SavePiconSize = LCD4linux.PiconSize.value
		self.SavePiconFullScreen = LCD4linux.PiconFullScreen.value
		self.SavePiconTransparenz = LCD4linux.PiconTransparenz.value
		self.SaveWetter = LCD4linux.WetterCity.value
		self.SaveWetter2 = LCD4linux.Wetter2City.value
		self.SaveMeteo = LCD4linux.MeteoURL.value
		self.SaveMeteoType = LCD4linux.MeteoType.value
		self.SaveMeteoZoom = LCD4linux.MeteoZoom.value
		self.SaveStandbyMeteoType = LCD4linux.StandbyMeteoType.value
		self.SaveStandbyMeteoZoom = LCD4linux.StandbyMeteoZoom.value
		self.SaveScreenActive = LCD4linux.ScreenActive.value
		self.SavePicture = LCD4linux.SavePicture.value
		self.WWWischanged = False
		self.Aktuell = " "
		self.LastSelect = "   "
		self.LastSelectT = ""
		self.SaveisMediaPlayer = isMediaPlayer
		self.list = []
		self.mtime1 = 0.0
		self.mtime2 = 0.0
		self.mtime3 = 0.0
		if os.path.isfile("/etc/enigma2/skin_user.xml"):
			xmlRead()
			LCD4linux.xmlType01.value = False if xmlFind(1) == -1 else True
			LCD4linux.xmlType02.value = False if xmlFind(2) == -1 else True
			LCD4linux.xmlType03.value = False if xmlFind(3) == -1 else True
			xmlClear()

		self.toggle = time()
	
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.setPictureCB)		
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((pic_w, pic_h, sc[0], sc[1], False, 1, '#00000000'))
		
		self.picload2 = ePicLoad()
		self.picload2.PictureData.get().append(self.setPictureCB2)		
		sc = AVSwitch().getFramebufferScale()
		self.picload2.setPara((pic_w, pic_h, sc[0], sc[1], False, 1, '#00000000'))

		self.picload3 = ePicLoad()
		self.picload3.PictureData.get().append(self.setPictureCB3)		
		sc = AVSwitch().getFramebufferScale()
		self.picload3.setPara((pic_w, pic_h, sc[0], sc[1], False, 1, '#00000000'))

		ConfigListScreen.__init__(self, self.list, on_change = self.selectionChanged)

		self.PicTimer = eTimer()
		self.PicTimer.callback.append(self.showpic)

		self["introduction"] = StaticText()
		self["Version"] = StaticText(Version if L4LVtest(Version)==True else Version+"?")
		self["LibUSB"] = StaticText()
		self["About"] = StaticText()
		self["LCD1"] = Pixmap()
		self["LCD2"] = Pixmap()
		self["LCD3"] = Pixmap()
		self["LCD1text"] = StaticText()
		self["LCD2text"] = StaticText()
		self["LCD3text"] = StaticText()

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Restart Displays"))
		self["key_blue"] = Button("")
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions", "EPGSelectActions", "HelpActions","InfobarSeekActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"yellow": self.LCDrestart,
			"blue": self.Page,
			"nextBouquet": self.KeyUp,
			"prevBouquet": self.KeyDown,
 			"save": self.save,
			"cancel": self.cancel,
			"menu": self.SetupMenu,
			"displayHelp": self.Exchange,
			"ok": self.keyOK,
			"seekFwd": self.NextScreenKey,
			"info": self.ResetInfos
		}, -1)
		self.mode = "On"
		self.LastSelect="1"
		self.SetList()
		self.mode = "Media"
		self.LastSelect="2"
		self.SetList()
		self.mode = "Idle"
		self.LastSelect="3"
		self.SetList()
		self.mode = "Global"
		self.LastSelect="4"
		self.SetList()
		self.mode = "Idle"
		self.LastSelect="5"
		self.Page()
		self.selectionChanged()
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		if LCD4linux.LCDType3.value == "00":
			self["LCD3"].hide()
		if getDesktop(0).size().width() < 1000:
			self["LCD1"].hide()
			self["LCD2"].hide()
			self["LCD3"].hide()
		else:
			self.onLayoutFinish.append(self.showpic)
		self.onLayoutFinish.append(self.layoutFinished)
		L4log("init Ende")

	def layoutFinished(self):
		self["config"].l.setSeperation(int(self["config"].l.getItemSize().width()*.7)) # use 30% of list width for sliders

	def NextScreenKey(self):
		NextScreen(True)

	def ResetInfos(self):
		global FritzList
		global PopMailUid
		FritzList = []
		PopMailUid = [["","",""],["","",""],["","",""],["","",""],["","",""]]
		if Briefkasten.qsize()<=3:
			Briefkasten.put(6) 

	def showpic(self):
		self.PicTimer.stop()
		ff=False
		fn=PIC+".jpg"
		try:
			if os.path.isfile(fn):
				ft=os.stat(fn).st_mtime
				ff=True
				if ft != self.mtime1:
					self.picload.startDecode(fn)
					self.mtime1=ft
			else:
				fn=PIC+".png"
				ft=0.0
				if os.path.isfile(fn):
					ft=os.stat(fn).st_mtime
					ff=True
					if ft != self.mtime1:
						self.picload.startDecode(fn)
						self.mtime1=ft
		except:
			L4log("Error Pic1 not found")
		if ff==False:
			self["LCD1text"].setText(_("no LCD1 Picture-File"))
			self["LCD1"].hide()
		else:
			self["LCD1text"].setText("")
		ff=False
		fn=PIC2+".jpg"
		try:
			if os.path.isfile(fn):
				ft=os.stat(fn).st_mtime
				ff=True
				if ft != self.mtime2:
					self.picload2.startDecode(fn)
					self.mtime2=ft
			else:
				fn=PIC2+".png"
				ft=0.0
				if os.path.isfile(fn):
					ft=os.stat(fn).st_mtime
					ff=True
					if ft != self.mtime2:
						self.picload2.startDecode(fn)
						self.mtime2=ft
		except:
			L4log("Error Pic2 not found")
		if ff==False:
			self["LCD2text"].setText(_("no LCD2 Picture-File"))
			self["LCD2"].hide()
		else:
			self["LCD2text"].setText("")
		if LCD4linux.LCDType3.value != "00":
			ff=False
			fn=PIC3+".jpg"
			try:
				if os.path.isfile(fn):
					ft=os.stat(fn).st_mtime
					ff=True
					if ft != self.mtime3:
						self.picload3.startDecode(fn)
						self.mtime3=ft
				else:
					fn=PIC3+".png"
					ft=0.0
					if os.path.isfile(fn):
						ft=os.stat(fn).st_mtime
						ff=True
						if ft != self.mtime3:
							self.picload3.startDecode(fn)
							self.mtime3=ft
			except:
				L4log("Error Pic3 not found")
			if ff==False:
				self["LCD3text"].setText(_("no LCD3 Picture-File"))
				self["LCD3"].hide()
			else:
				self["LCD3text"].setText("")
		self.PicTimer.start(500,True)

	def setPictureCB(self, picInfo = None):
		ptr = self.picload.getData()
		if ptr is not None:
			self["LCD1"].instance.setPixmap(ptr)
			self["LCD1"].show()

	def setPictureCB2(self, picInfo = None):
		ptr = self.picload2.getData()
		if ptr is not None:
			self["LCD2"].instance.setPixmap(ptr)
			self["LCD2"].show()
 
	def setPictureCB3(self, picInfo = None):
		ptr = self.picload3.getData()
		if ptr is not None:
			self["LCD3"].instance.setPixmap(ptr)
			self["LCD3"].show()

	def SetupMenu(self):
		self.session.open(LCDdisplayMenu)

	def Exchange(self):
		Exchange()
		
	def SetList(self):
		L4log("SetList",self.mode)
#		L4log("Aktuell",self.Aktuell)
#		L4log("Last",self.LastSelect)
		if (self.Aktuell.startswith("-") or self.LastSelectT == self.LastSelect) and not self.Aktuell.startswith("-  "):
			return
		self.LastSelectT = self.LastSelect
		if self.mode == "Global":
			self.list1 = []
			self.list1.append(getConfigListEntry(_("LCD4linux enabled"), LCD4linux.Enable))
			self.list1.append(getConfigListEntry(_("LCD 1 Type"), LCD4linux.LCDType1))
			self.list1.append(getConfigListEntry(_("- LCD 1 Rotate"), LCD4linux.LCDRotate1))
			self.list1.append(getConfigListEntry(_("- LCD 1 Background Color"), LCD4linux.LCDColor1))
			self.list1.append(getConfigListEntry(_("- LCD 1 Background-Picture [ok]>"), LCD4linux.LCDBild1))
			self.list1.append(getConfigListEntry(_("- LCD 1 Brightness [no SPF]"), LCD4linux.Helligkeit))
			self.list1.append(getConfigListEntry(_("LCD 2 Type"), LCD4linux.LCDType2))
			if LCD4linux.LCDType2.value != "00":
				self.list1.append(getConfigListEntry(_("- LCD 2 Rotate"), LCD4linux.LCDRotate2))
				self.list1.append(getConfigListEntry(_("- LCD 2 Background Color"), LCD4linux.LCDColor2))
				self.list1.append(getConfigListEntry(_("- LCD 2 Background-Picture [ok]>"), LCD4linux.LCDBild2))
				self.list1.append(getConfigListEntry(_("- LCD 2 Brightness [no SPF]"), LCD4linux.Helligkeit2))
			self.list1.append(getConfigListEntry(_("LCD 3 Type"), LCD4linux.LCDType3))
			if LCD4linux.LCDType3.value != "00":
				self.list1.append(getConfigListEntry(_("- LCD 3 Rotate"), LCD4linux.LCDRotate3))
				self.list1.append(getConfigListEntry(_("- LCD 3 Background Color"), LCD4linux.LCDColor3))
				self.list1.append(getConfigListEntry(_("- LCD 3 Background-Picture [ok]>"), LCD4linux.LCDBild3))
				self.list1.append(getConfigListEntry(_("- LCD 3 Brightness [no SPF]"), LCD4linux.Helligkeit3))
			if LCD4linux.LCDType1.value[0] == "5" or LCD4linux.LCDType2.value[0] == "5" or LCD4linux.LCDType3.value[0] == "5":
				self.list1.append(getConfigListEntry(_("Box-Skin-LCD Dimension"), LCD4linux.xmlLCDType))
				self.list1.append(getConfigListEntry(_("Box-Skin-LCD Color"), LCD4linux.xmlLCDColor))
				self.list1.append(getConfigListEntry(_("Box-Skin-LCD Enable On-Mode"), LCD4linux.xmlType01))
				self.list1.append(getConfigListEntry(_("Box-Skin-LCD Enable Media-Mode"), LCD4linux.xmlType02))
				self.list1.append(getConfigListEntry(_("Box-Skin-LCD Enable Idle-Mode"), LCD4linux.xmlType03))
			self.list1.append(getConfigListEntry(_("OSD [display time]"), LCD4linux.OSD))
			if LCD4linux.OSD.value != "0":
				self.list1.append(getConfigListEntry(_("- which LCD"), LCD4linux.OSDLCD))
				self.list1.append(getConfigListEntry(_("- Show in Mode"), LCD4linux.OSDshow))
				self.list1.append(getConfigListEntry(_("- OSD Size"), LCD4linux.OSDsize))
				self.list1.append(getConfigListEntry(_("- Background/Transparency"), LCD4linux.OSDTransparenz))
				self.list1.append(getConfigListEntry(_("- Fast Grab lower quality"), LCD4linux.OSDfast))
			self.list1.append(getConfigListEntry(_("Popup Text"), LCD4linux.Popup))
			if LCD4linux.Popup.value != "0":
				self.list1.append(getConfigListEntry(_("- which LCD"), LCD4linux.PopupLCD))
				self.list1.append(getConfigListEntry(_("- Font Size"), LCD4linux.PopupSize))
				self.list1.append(getConfigListEntry(_("- Position"), LCD4linux.PopupPos))
				self.list1.append(getConfigListEntry(_("- Alignment"), LCD4linux.PopupAlign))
				self.list1.append(getConfigListEntry(_("- Color"), LCD4linux.PopupColor))
				self.list1.append(getConfigListEntry(_("- Background Color"), LCD4linux.PopupBackColor))
#			if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4":
#				self.list1.append(getConfigListEntry(_("Internal TFT Active"), LCD4linux.LCDTFT))
			self.list1.append(getConfigListEntry(_("Active Screen"), LCD4linux.ScreenActive))
			self.list1.append(getConfigListEntry(_("Screens used for Changing"), LCD4linux.ScreenMax))
			self.list1.append(getConfigListEntry(_("Screen 1 Changing Time"), LCD4linux.ScreenTime))
			if LCD4linux.ScreenTime.value != "0":
				self.list1.append(getConfigListEntry(_("- Screen 2 Changing Time"), LCD4linux.ScreenTime2))
				self.list1.append(getConfigListEntry(_("- Screen 3 Changing Time"), LCD4linux.ScreenTime3))
				self.list1.append(getConfigListEntry(_("- Screen 4 Changing Time"), LCD4linux.ScreenTime4))
				self.list1.append(getConfigListEntry(_("- Screen 5 Changing Time"), LCD4linux.ScreenTime5))
				self.list1.append(getConfigListEntry(_("- Screen 6 Changing Time"), LCD4linux.ScreenTime6))
				self.list1.append(getConfigListEntry(_("- Screen 7 Changing Time"), LCD4linux.ScreenTime7))
				self.list1.append(getConfigListEntry(_("- Screen 8 Changing Time"), LCD4linux.ScreenTime8))
				self.list1.append(getConfigListEntry(_("- Screen 9 Changing Time"), LCD4linux.ScreenTime9))
			self.list1.append(getConfigListEntry(_("Picture Changing Time"), LCD4linux.BilderTime))
			self.list1.append(getConfigListEntry(_("Picture Sort"), LCD4linux.BilderSort))
			self.list1.append(getConfigListEntry(_("Picture Directory Recursive"), LCD4linux.BilderRecursiv))
			self.list1.append(getConfigListEntry(_("Picture Quality for Resizing"), LCD4linux.BilderQuality))
#			self.list1.append(getConfigListEntry(_("Picture JPEG-Quality [%]"), LCD4linux.BilderJPEG))
			self.list1.append(getConfigListEntry(_("Picture Quick Update Time [s]"), LCD4linux.BilderQuick))
#			self.list1.append(getConfigListEntry(_("Picture Quick JPEG-Quality [%]"), LCD4linux.BilderJPEGQuick))
			self.list1.append(getConfigListEntry(_("Weather City"), LCD4linux.WetterCity))
			self.list1.append(getConfigListEntry(_("Weather City 2"), LCD4linux.Wetter2City))
			self.list1.append(getConfigListEntry(_("Weather-Icon-Path [ok]>"), LCD4linux.WetterPath))
			self.list1.append(getConfigListEntry(_("Weather-Icon Zoom"), LCD4linux.WetterIconZoom))
			self.list1.append(getConfigListEntry(_("Weather Low Temperature Color"), LCD4linux.WetterLowColor))
			self.list1.append(getConfigListEntry(_("Weather High Temperature Color"), LCD4linux.WetterHighColor))
			self.list1.append(getConfigListEntry(_("Weather Transparency"), LCD4linux.WetterTransparenz))
			self.list1.append(getConfigListEntry(_("Weather Rain Chance"), LCD4linux.WetterRain))
			self.list1.append(getConfigListEntry(_("Weather Wind speed unit"), LCD4linux.WetterWind))
			if LCD4linux.WetterRain.value != "false":
				self.list1.append(getConfigListEntry(_("- Rain Zoom"), LCD4linux.WetterRainZoom))
				self.list1.append(getConfigListEntry(_("- Rain Color"), LCD4linux.WetterRainColor))
				self.list1.append(getConfigListEntry(_("- Rain use Color 2 from"), LCD4linux.WetterRainColor2use))
				self.list1.append(getConfigListEntry(_("- Rain Color 2"), LCD4linux.WetterRainColor2))
			self.list1.append(getConfigListEntry(_("Weather Lines"), LCD4linux.WetterLine))
			self.list1.append(getConfigListEntry(_("Weather Extra Infos"), LCD4linux.WetterExtra))
			if LCD4linux.WetterExtra.value == True:
				self.list1.append(getConfigListEntry(_("- Extra Zoom"), LCD4linux.WetterExtraZoom))
				self.list1.append(getConfigListEntry(_("- Show chill temperature from difference"), LCD4linux.WetterExtraFeel))
				self.list1.append(getConfigListEntry(_("- Extra Color City"), LCD4linux.WetterExtraColorCity))
				self.list1.append(getConfigListEntry(_("- Extra Color Chill"), LCD4linux.WetterExtraColorFeel))
			self.list1.append(getConfigListEntry(_("Netatmo CO2 Min Range"), LCD4linux.NetAtmoCO2Min))
			self.list1.append(getConfigListEntry(_("Netatmo CO2 Max Range"), LCD4linux.NetAtmoCO2Max))
			self.list1.append(getConfigListEntry(_("Meteo URL"), LCD4linux.MeteoURL))
			self.list1.append(getConfigListEntry(_("Moon-Icon-Path [ok]>"), LCD4linux.MoonPath))
			self.list1.append(getConfigListEntry(_("Recording Picture [ok]>"), LCD4linux.RecordingPath))
			self.list1.append(getConfigListEntry(_("Double-button switches"), LCD4linux.KeySwitch))
			self.list1.append(getConfigListEntry(_("Key for Screen Change"), LCD4linux.KeyScreen))
			self.list1.append(getConfigListEntry(_("Key for Screen On/Off"), LCD4linux.KeyOff))
			self.list1.append(getConfigListEntry(_("FritzCall Picture Path [ok]>"), LCD4linux.FritzPath))
			self.list1.append(getConfigListEntry(_("FritzCall Number of List Entries"), LCD4linux.FritzLines))
			self.list1.append(getConfigListEntry(_("FritzCall Number of Pictures"), LCD4linux.FritzPictures))
			self.list1.append(getConfigListEntry(_("FritzCall Picture Orientation"), LCD4linux.FritzPictureType))
			self.list1.append(getConfigListEntry(_("FritzCall Pictures Search"), LCD4linux.FritzPictureSearch))
			self.list1.append(getConfigListEntry(_("FritzCall remove Calls after hours"), LCD4linux.FritzRemove))
			self.list1.append(getConfigListEntry(_("FritzCall Popup-Time"), LCD4linux.FritzTime))
			self.list1.append(getConfigListEntry(_("FritzCall Popup LCD"), LCD4linux.FritzPopupLCD))
			self.list1.append(getConfigListEntry(_("FritzCall Popup Color"), LCD4linux.FritzPopupColor))
			self.list1.append(getConfigListEntry(_("FritzCall Frame Picture [ok]>"), LCD4linux.FritzFrame))
			self.list1.append(getConfigListEntry(_("Calendar ics-Path [ok]>"), LCD4linux.CalPath))
			self.list1.append(getConfigListEntry(_("- Color"), LCD4linux.CalPathColor))
			self.list1.append(getConfigListEntry(_("Calendar ics-URL"), LCD4linux.CalHttp))
			self.list1.append(getConfigListEntry(_("- Color"), LCD4linux.CalHttpColor))
			self.list1.append(getConfigListEntry(_("Calendar ics-URL"), LCD4linux.CalHttp2))
			self.list1.append(getConfigListEntry(_("- Color"), LCD4linux.CalHttp2Color))
			self.list1.append(getConfigListEntry(_("Calendar ics-URL"), LCD4linux.CalHttp3))
			self.list1.append(getConfigListEntry(_("- Color"), LCD4linux.CalHttp3Color))
			self.list1.append(getConfigListEntry(_("Calendar planerFS"), LCD4linux.CalPlanerFS))
			self.list1.append(getConfigListEntry(_("- Color"), LCD4linux.CalPlanerFSColor))
			self.list1.append(getConfigListEntry(_("Calendar Line Thickness"), LCD4linux.CalLine))
			self.list1.append(getConfigListEntry(_("Calendar Day Event Preview"), LCD4linux.CalDays))
			self.list1.append(getConfigListEntry(_("Calendar Transparency"), LCD4linux.CalTransparenz))
			self.list1.append(getConfigListEntry(_("Calendar Poll Interval"), LCD4linux.CalTime))
			self.list1.append(getConfigListEntry(_("Tuner Color"), LCD4linux.TunerColor))
			self.list1.append(getConfigListEntry(_("Tuner Color Active"), LCD4linux.TunerColorActive))
			self.list1.append(getConfigListEntry(_("Tuner Color On"), LCD4linux.TunerColorOn))
			self.list1.append(getConfigListEntry(_("Font global [ok]>"), LCD4linux.Font))
			self.list1.append(getConfigListEntry(_("Font 1 [ok]>"), LCD4linux.Font1))
			self.list1.append(getConfigListEntry(_("Font 2 [ok]>"), LCD4linux.Font2))
			self.list1.append(getConfigListEntry(_("Font 3 [ok]>"), LCD4linux.Font3))
			self.list1.append(getConfigListEntry(_("Mail 1 Connect"), LCD4linux.Mail1Connect))
			self.list1.append(getConfigListEntry(_("Mail 1 Server"), LCD4linux.Mail1Pop))
			self.list1.append(getConfigListEntry(_("Mail 1 [Displayname:]Username"), LCD4linux.Mail1User))
			self.list1.append(getConfigListEntry(_("Mail 1 Password"), LCD4linux.Mail1Pass))
			self.list1.append(getConfigListEntry(_("Mail 2 Connect"), LCD4linux.Mail2Connect))
			self.list1.append(getConfigListEntry(_("Mail 2 Server"), LCD4linux.Mail2Pop))
			self.list1.append(getConfigListEntry(_("Mail 2 [Displayname:]Username"), LCD4linux.Mail2User))
			self.list1.append(getConfigListEntry(_("Mail 2 Password"), LCD4linux.Mail2Pass))
			self.list1.append(getConfigListEntry(_("Mail 3 Connect"), LCD4linux.Mail3Connect))
			self.list1.append(getConfigListEntry(_("Mail 3 Server"), LCD4linux.Mail3Pop))
			self.list1.append(getConfigListEntry(_("Mail 3 [Displayname:]Username"), LCD4linux.Mail3User))
			self.list1.append(getConfigListEntry(_("Mail 3 Password"), LCD4linux.Mail3Pass))
			self.list1.append(getConfigListEntry(_("Mail 4 Connect"), LCD4linux.Mail4Connect))
			self.list1.append(getConfigListEntry(_("Mail 4 Server"), LCD4linux.Mail4Pop))
			self.list1.append(getConfigListEntry(_("Mail 4 [Displayname:]Username"), LCD4linux.Mail4User))
			self.list1.append(getConfigListEntry(_("Mail 4 Password"), LCD4linux.Mail4Pass))
			self.list1.append(getConfigListEntry(_("Mail 5 Connect"), LCD4linux.Mail5Connect))
			self.list1.append(getConfigListEntry(_("Mail 5 Server"), LCD4linux.Mail5Pop))
			self.list1.append(getConfigListEntry(_("Mail 5 [Displayname:]Username"), LCD4linux.Mail5User))
			self.list1.append(getConfigListEntry(_("Mail 5 Password"), LCD4linux.Mail5Pass))
			self.list1.append(getConfigListEntry(_("Mail Poll Interval"), LCD4linux.MailTime))
			self.list1.append(getConfigListEntry(_("Mail Show Empty Mailboxes"), LCD4linux.MailShow0))
			self.list1.append(getConfigListEntry(_("WWW Converter Poll Interval"), LCD4linux.WWWTime))
			self.list1.append(getConfigListEntry(_("WebIF Refresh [s]"), LCD4linux.WebIfRefresh))
			self.list1.append(getConfigListEntry(_("WebIF Refresh Type"), LCD4linux.WebIfType))
			self.list1.append(getConfigListEntry(_("WebIF Init Delay"), LCD4linux.WebIfInitDelay))
			self.list1.append(getConfigListEntry(_("WebIF IP Allow"), LCD4linux.WebIfAllow))
			self.list1.append(getConfigListEntry(_("WebIF IP Deny"), LCD4linux.WebIfDeny))
			self.list1.append(getConfigListEntry(_("WebIF Design"), LCD4linux.WebIfDesign))
			self.list1.append(getConfigListEntry(_("Save as Picture for WebIF"), LCD4linux.SavePicture))
			self.list1.append(getConfigListEntry(_("LCD Custom Width"), LCD4linux.SizeW))
			self.list1.append(getConfigListEntry(_("LCD Custom Height"), LCD4linux.SizeH))
			self.list1.append(getConfigListEntry(_("Timing ! calc all Times to Time/5*2 in Fastmode"), LCD4linux.FastMode))
			self.list1.append(getConfigListEntry(_("Display Delay [ms]"), LCD4linux.Delay))
			self.list1.append(getConfigListEntry(_("Threads per LCD"), LCD4linux.ElementThreads))
			self.list1.append(getConfigListEntry(_("Show Crash Corner"), LCD4linux.Crash))
			self.list1.append(getConfigListEntry(_("Show 'no ....' Messages"), LCD4linux.ShowNoMsg))
			self.list1.append(getConfigListEntry(_("Storage-Devices: Force Read"), LCD4linux.DevForceRead))
			self.list1.append(getConfigListEntry(_("Config Backup Path [ok]>"), LCD4linux.ConfigPath))
			self.list1.append(getConfigListEntry(_("Debug-Logging > /tmp/L4log.txt"), LCD4linux.EnableEventLog))
			self["config"].setList(self.list1)
		elif self.mode == "On":
			self.list2 = []
			self.list2.append(getConfigListEntry(_("- Backlight Off [disable set Off=On]"), LCD4linux.LCDoff))
			self.list2.append(getConfigListEntry(_("- Backlight On"), LCD4linux.LCDon))
			self.list2.append(getConfigListEntry(_("- Backlight Weekend Off [disable set Off=On]"), LCD4linux.LCDWEoff))
			self.list2.append(getConfigListEntry(_("- Backlight Weekend On"), LCD4linux.LCDWEon))
			self.list2.append(getConfigListEntry(_("Picon"), LCD4linux.Picon))
			if LCD4linux.Picon.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.PiconLCD))
				self.list2.append(getConfigListEntry(_("- Picon Size"), LCD4linux.PiconSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.PiconPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.PiconAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.PiconSplit))
				self.list2.append(getConfigListEntry(_("- Full Screen"), LCD4linux.PiconFullScreen))
				self.list2.append(getConfigListEntry(_("- Text Size"), LCD4linux.PiconTextSize))
				self.list2.append(getConfigListEntry(_("- Transparency"), LCD4linux.PiconTransparenz))
				self.list2.append(getConfigListEntry(_("- Picon Path [ok]>"), LCD4linux.PiconPath))
				self.list2.append(getConfigListEntry(_("- Picon Path 2 [ok]>"), LCD4linux.PiconPathAlt))
				self.list2.append(getConfigListEntry(_("- Picon Cache Path [ok]>"), LCD4linux.PiconCache))
			self.list2.append(getConfigListEntry(_("Picon 2"), LCD4linux.Picon2))
			if LCD4linux.Picon2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Picon2LCD))
				self.list2.append(getConfigListEntry(_("- Picon Size"), LCD4linux.Picon2Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Picon2Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Picon2Align))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.Picon2Split))
				self.list2.append(getConfigListEntry(_("- Full Screen"), LCD4linux.Picon2FullScreen))
				self.list2.append(getConfigListEntry(_("- Text Size"), LCD4linux.Picon2TextSize))
				self.list2.append(getConfigListEntry(_("- Picon Path [ok]>"), LCD4linux.Picon2Path))
				self.list2.append(getConfigListEntry(_("- Picon Path 2 [ok]>"), LCD4linux.Picon2PathAlt))
				self.list2.append(getConfigListEntry(_("- Picon Cache Path [ok]>"), LCD4linux.Picon2Cache))
			self.list2.append(getConfigListEntry(_("Clock"), LCD4linux.Clock))
			if LCD4linux.Clock.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ClockLCD))
				self.list2.append(getConfigListEntry(_("-  Type"), LCD4linux.ClockType))
				if LCD4linux.ClockType.value[0] == "5":
					self.list2.append(getConfigListEntry(_("- Analog Clock"), LCD4linux.ClockAnalog))
				elif LCD4linux.ClockType.value[0] == "1":
					self.list2.append(getConfigListEntry(_("- Spacing"), LCD4linux.ClockSpacing))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.ClockSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ClockPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ClockAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.ClockSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ClockColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ClockShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ClockFont))
			self.list2.append(getConfigListEntry(_("Clock 2"), LCD4linux.Clock2))
			if LCD4linux.Clock2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Clock2LCD))
				self.list2.append(getConfigListEntry(_("-  Type"), LCD4linux.Clock2Type))
				if LCD4linux.Clock2Type.value[0] == "5":
					self.list2.append(getConfigListEntry(_("- Analog Clock"), LCD4linux.Clock2Analog))
				elif LCD4linux.Clock2Type.value[0] == "1":
					self.list2.append(getConfigListEntry(_("- Spacing"), LCD4linux.Clock2Spacing))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.Clock2Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Clock2Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Clock2Align))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.Clock2Split))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Clock2Color))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.Clock2Shadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.Clock2Font))
			self.list2.append(getConfigListEntry(_("Program Name"), LCD4linux.Channel))
			if LCD4linux.Channel.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ChannelLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.ChannelSize))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.ChannelLines))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ChannelPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ChannelAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.ChannelSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ChannelColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ChannelShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ChannelFont))
			self.list2.append(getConfigListEntry(_("Program Number"), LCD4linux.ChannelNum))
			if LCD4linux.ChannelNum.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ChannelNumLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.ChannelNumSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ChannelNumPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ChannelNumAlign))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ChannelNumColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.ChannelNumBackColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ChannelNumShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ChannelNumFont))
			self.list2.append(getConfigListEntry(_("Program Info"), LCD4linux.Prog))
			if LCD4linux.Prog.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ProgLCD))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.ProgType))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.ProgSize))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.ProgLines))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ProgPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ProgAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.ProgSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ProgColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ProgShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ProgFont))
			self.list2.append(getConfigListEntry(_("Next Program Info"), LCD4linux.ProgNext))
			if LCD4linux.ProgNext.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ProgNextLCD))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.ProgNextType))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.ProgNextSize))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.ProgNextLines))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ProgNextPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ProgNextAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.ProgNextSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ProgNextColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ProgNextShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ProgNextFont))
			self.list2.append(getConfigListEntry(_("Extended Description"), LCD4linux.Desc))
			if LCD4linux.Desc.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.DescLCD))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.DescType))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.DescSize))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.DescLines))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.DescPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.DescAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.DescSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.DescColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.DescShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.DescFont))
			self.list2.append(getConfigListEntry(_("Progress Bar"), LCD4linux.Progress))
			if LCD4linux.Progress.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ProgressLCD))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.ProgressType))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.ProgressSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ProgressPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ProgressAlign))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ProgressColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ProgressShadow2))
				self.list2.append(getConfigListEntry(_("- Shaded"), LCD4linux.ProgressShadow))
			self.list2.append(getConfigListEntry(_("Informations"), LCD4linux.Info))
			if LCD4linux.Info.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.InfoLCD))
				self.list2.append(getConfigListEntry(_("- Tunerinfo"), LCD4linux.InfoTuner))
				self.list2.append(getConfigListEntry(_("- Sensors"), LCD4linux.InfoSensor))
				self.list2.append(getConfigListEntry(_("- CPU"), LCD4linux.InfoCPU))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.InfoSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.InfoPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.InfoAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.InfoSplit))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.InfoLines))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.InfoColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.InfoShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.InfoFont))
			self.list2.append(getConfigListEntry(_("Signal Quality Bar"), LCD4linux.Signal))
			if LCD4linux.Signal.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.SignalLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.SignalSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.SignalPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.SignalAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.SignalSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.SignalColor))
				self.list2.append(getConfigListEntry(_("- Gradient"), LCD4linux.SignalGradient))
				self.list2.append(getConfigListEntry(_("- Bar Range Min"), LCD4linux.SignalMin))
				self.list2.append(getConfigListEntry(_("- Bar Range Max"), LCD4linux.SignalMax))
			self.list2.append(getConfigListEntry(_("Satellite"), LCD4linux.Sat))
			if LCD4linux.Sat.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.SatLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.SatSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.SatPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.SatAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.SatSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.SatColor))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.SatType))
				self.list2.append(getConfigListEntry(_("- Picon Path [ok]>"), LCD4linux.SatPath))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.SatShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.SatFont))
			self.list2.append(getConfigListEntry(_("Provider"), LCD4linux.Prov))
			if LCD4linux.Prov.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ProvLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.ProvSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ProvPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ProvAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.ProvSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ProvColor))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.ProvType))
				self.list2.append(getConfigListEntry(_("- Picon Path [ok]>"), LCD4linux.ProvPath))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ProvShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ProvFont))
			self.list2.append(getConfigListEntry(_("Used Tuner"), LCD4linux.Tuner))
			if LCD4linux.Tuner.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.TunerLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.TunerSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.TunerPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.TunerAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.TunerSplit))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.TunerType))
				self.list2.append(getConfigListEntry(_("- only active Tuner"), LCD4linux.TunerActive))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.TunerFont))
			self.list2.append(getConfigListEntry(_("Next Timer Event"), LCD4linux.Timer))
			if LCD4linux.Timer.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.TimerLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.TimerSize))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.TimerLines))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.TimerType))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.TimerPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.TimerAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.TimerSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.TimerColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.TimerShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.TimerFont))
			self.list2.append(getConfigListEntry(_("Volume"), LCD4linux.Vol))
			if LCD4linux.Vol.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.VolLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.VolSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.VolPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.VolAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.VolSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.VolColor))
				self.list2.append(getConfigListEntry(_("- Shaded"), LCD4linux.VolShadow))
			self.list2.append(getConfigListEntry(_("Audio/Video"), LCD4linux.AV))
			if LCD4linux.AV.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.AVLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.AVSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.AVPos))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.AVType))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.AVAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.AVSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.AVColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.AVShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.AVFont))
			self.list2.append(getConfigListEntry(_("Bitrate"), LCD4linux.Bitrate))
			if LCD4linux.Bitrate.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.BitrateLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.BitrateSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.BitratePos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.BitrateAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.BitrateSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.BitrateColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.BitrateShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.BitrateFont))
			self.list2.append(getConfigListEntry(_("Online [Ping]"), LCD4linux.Ping))
			if LCD4linux.Ping.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.PingLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.PingSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.PingPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.PingAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.PingSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.PingColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.PingShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.PingFont))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.PingType))
				self.list2.append(getConfigListEntry(_("- Show State"), LCD4linux.PingShow))
				self.list2.append(getConfigListEntry(_("- Timeout"), LCD4linux.PingTimeout))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName1))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName2))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName3))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName4))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName5))
			self.list2.append(getConfigListEntry(_("Storage-Devices"), LCD4linux.Dev))
			if LCD4linux.Dev.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.DevLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.DevSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.DevPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.DevAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.DevSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.DevColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.DevShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.DevFont))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.DevType))
				self.list2.append(getConfigListEntry(_("- extra Info"), LCD4linux.DevExtra))
				self.list2.append(getConfigListEntry(_("- Device Name"), LCD4linux.DevName1))
				self.list2.append(getConfigListEntry(_("- Device Name"), LCD4linux.DevName2))
				self.list2.append(getConfigListEntry(_("- Device Name"), LCD4linux.DevName3))
				self.list2.append(getConfigListEntry(_("- Device Name"), LCD4linux.DevName4))
				self.list2.append(getConfigListEntry(_("- Device Name"), LCD4linux.DevName5))
			self.list2.append(getConfigListEntry(_("HDD"), LCD4linux.Hdd))
			if LCD4linux.Hdd.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.HddLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.HddSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.HddPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.HddAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.HddSplit))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.HddType))
			self.list2.append(getConfigListEntry(_("Weather"), LCD4linux.Wetter))
			if LCD4linux.Wetter.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.WetterLCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.WetterPos))
				self.list2.append(getConfigListEntry(_("- Zoom"), LCD4linux.WetterZoom))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.WetterAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.WetterSplit))
				self.list2.append(getConfigListEntry(_("- Weather Type"), LCD4linux.WetterType))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.WetterColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.WetterShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.WetterFont))
			self.list2.append(getConfigListEntry(_("Weather 2"), LCD4linux.Wetter2))
			if LCD4linux.Wetter2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Wetter2LCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Wetter2Pos))
				self.list2.append(getConfigListEntry(_("- Zoom"), LCD4linux.Wetter2Zoom))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Wetter2Align))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.Wetter2Split))
				self.list2.append(getConfigListEntry(_("- Weather Type"), LCD4linux.Wetter2Type))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Wetter2Color))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.Wetter2Shadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.Wetter2Font))
			self.list2.append(getConfigListEntry(_("Meteo-Weather Station"), LCD4linux.Meteo))
			if LCD4linux.Meteo.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.MeteoLCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.MeteoPos))
				self.list2.append(getConfigListEntry(_("- Zoom"), LCD4linux.MeteoZoom))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.MeteoAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MeteoSplit))
				self.list2.append(getConfigListEntry(_("- Weather Type"), LCD4linux.MeteoType))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.MeteoColor))
			self.list2.append(getConfigListEntry(_("Netatmo"), LCD4linux.NetAtmo))
			if LCD4linux.NetAtmo.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.NetAtmoLCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.NetAtmoPos))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.NetAtmoSize))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.NetAtmoAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.NetAtmoSplit))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmoType))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmoType2))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.NetAtmoColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.NetAtmoShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.NetAtmoFont))
			self.list2.append(getConfigListEntry(_("Netatmo CO2 Indicator"), LCD4linux.NetAtmoCO2))
			if LCD4linux.NetAtmoCO2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.NetAtmoCO2LCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.NetAtmoCO2Pos))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.NetAtmoCO2Size))
				self.list2.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.NetAtmoCO2Len))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.NetAtmoCO2Align))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.NetAtmoCO2Split))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmoCO2Type))
			self.list2.append(getConfigListEntry(_("Netatmo Comfort Indicator"), LCD4linux.NetAtmoIDX))
			if LCD4linux.NetAtmoIDX.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.NetAtmoIDXLCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.NetAtmoIDXPos))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.NetAtmoIDXSize))
				self.list2.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.NetAtmoIDXLen))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.NetAtmoIDXAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.NetAtmoIDXSplit))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmoIDXType))
			self.list2.append(getConfigListEntry(_("Moonphase"), LCD4linux.Moon))
			if LCD4linux.Moon.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.MoonLCD))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.MoonSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.MoonPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.MoonAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MoonSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.MoonColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MoonShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.MoonFont))
			self.list2.append(getConfigListEntry(_("Sunrise"), LCD4linux.Sun))
			if LCD4linux.Sun.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.SunLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.SunSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.SunPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.SunAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.SunSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.SunColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.SunBackColor))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.SunType))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.SunShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.SunFont))
			self.list2.append(getConfigListEntry(_("Show oscam.lcd"), LCD4linux.OSCAM))
			if LCD4linux.OSCAM.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.OSCAMLCD))
				self.list2.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.OSCAMFile))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.OSCAMSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.OSCAMPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.OSCAMAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.OSCAMSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.OSCAMColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.OSCAMBackColor))
			self.list2.append(getConfigListEntry(_("Show ecm.info"), LCD4linux.ECM))
			if LCD4linux.ECM.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ECMLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.ECMSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ECMPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ECMAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.ECMSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ECMColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.ECMBackColor))
			self.list2.append(getConfigListEntry(_("Show Textfile"), LCD4linux.Text))
			if LCD4linux.Text.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.TextLCD))
				self.list2.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.TextFile))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.TextSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.TextPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.TextAlign))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.TextColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.TextBackColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.TextShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.TextFont))
			self.list2.append(getConfigListEntry(_("Show Textfile 2"), LCD4linux.Text2))
			if LCD4linux.Text2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Text2LCD))
				self.list2.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.Text2File))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.Text2Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Text2Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Text2Align))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Text2Color))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.Text2BackColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.Text2Shadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.Text2Font))
			self.list2.append(getConfigListEntry(_("Show Textfile 3"), LCD4linux.Text3))
			if LCD4linux.Text3.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Text3LCD))
				self.list2.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.Text3File))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.Text3Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Text3Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Text3Align))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Text3Color))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.Text3BackColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.Text3Shadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.Text3Font))
			self.list2.append(getConfigListEntry(_("Show HTTP Text"), LCD4linux.HTTP))
			if LCD4linux.HTTP.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.HTTPLCD))
				self.list2.append(getConfigListEntry(_("- URL"), LCD4linux.HTTPURL))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.HTTPSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.HTTPPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.HTTPAlign))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.HTTPColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.HTTPBackColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.HTTPShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.HTTPFont))
			self.list2.append(getConfigListEntry(_("WWW-Internet Converter"), LCD4linux.WWW1))
			if LCD4linux.WWW1.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.WWW1LCD))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.WWW1Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.WWW1Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.WWW1Align))
				self.list2.append(getConfigListEntry(_("- URL"), LCD4linux.WWW1url))
				self.list2.append(getConfigListEntry(_("- HTTP Width"), LCD4linux.WWW1w))
				self.list2.append(getConfigListEntry(_("- HTTP Height"), LCD4linux.WWW1h))
				self.list2.append(getConfigListEntry(_("- Cut from X"), LCD4linux.WWW1CutX))
				self.list2.append(getConfigListEntry(_("- Cut from Y"), LCD4linux.WWW1CutY))
				self.list2.append(getConfigListEntry(_("- Cut Width [disable = 0]"), LCD4linux.WWW1CutW))
				self.list2.append(getConfigListEntry(_("- Cut Height [disable = 0]"), LCD4linux.WWW1CutH))
			self.list2.append(getConfigListEntry(_("Show Picture"), LCD4linux.Bild))
			if LCD4linux.Bild.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.BildLCD))
				self.list2.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.BildFile))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.BildSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.BildPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.BildAlign))
				self.list2.append(getConfigListEntry(_("- Quick Update"), LCD4linux.BildQuick))
				self.list2.append(getConfigListEntry(_("- Transparency"), LCD4linux.BildTransp))
			self.list2.append(getConfigListEntry(_("Show Picture 2"), LCD4linux.Bild2))
			if LCD4linux.Bild2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Bild2LCD))
				self.list2.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.Bild2File))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.Bild2Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Bild2Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Bild2Align))
				self.list2.append(getConfigListEntry(_("- Quick Update"), LCD4linux.Bild2Quick))
				self.list2.append(getConfigListEntry(_("- Transparency"), LCD4linux.Bild2Transp))
			self.list2.append(getConfigListEntry(_("Show Picture 3"), LCD4linux.Bild3))
			if LCD4linux.Bild3.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Bild3LCD))
				self.list2.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.Bild3File))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.Bild3Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Bild3Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Bild3Align))
				self.list2.append(getConfigListEntry(_("- Quick Update"), LCD4linux.Bild3Quick))
				self.list2.append(getConfigListEntry(_("- Transparency"), LCD4linux.Bild3Transp))
			self.list2.append(getConfigListEntry(_("Show Picture 4"), LCD4linux.Bild4))
			if LCD4linux.Bild4.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Bild4LCD))
				self.list2.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.Bild4File))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.Bild4Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Bild4Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Bild4Align))
				self.list2.append(getConfigListEntry(_("- Quick Update"), LCD4linux.Bild4Quick))
				self.list2.append(getConfigListEntry(_("- Transparency"), LCD4linux.Bild4Transp))
			self.list2.append(getConfigListEntry(_("Mail"), LCD4linux.Mail))
			if LCD4linux.Mail.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.MailLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.MailSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.MailPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.MailAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MailSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.MailColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.MailBackColor))
				self.list2.append(getConfigListEntry(_("- Lines"), LCD4linux.MailLines))
				self.list2.append(getConfigListEntry(_("- Mail Konto"), LCD4linux.MailKonto))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.MailType))
				self.list2.append(getConfigListEntry(_("- max Width"), LCD4linux.MailProzent))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MailShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.MailFont))
			self.list2.append(getConfigListEntry(_("FritzCall"), LCD4linux.Fritz))
			if LCD4linux.Fritz.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.FritzLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.FritzSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.FritzPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.FritzAlign))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.FritzColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.FritzBackColor))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.FritzType))
				self.list2.append(getConfigListEntry(_("- Picture Size"), LCD4linux.FritzPicSize))
				self.list2.append(getConfigListEntry(_("- Picture Position"), LCD4linux.FritzPicPos))
				self.list2.append(getConfigListEntry(_("- Picture Alignment"), LCD4linux.FritzPicAlign))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.FritzShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.FritzFont))
			self.list2.append(getConfigListEntry(_("Calendar"), LCD4linux.Cal))
			if LCD4linux.Cal.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.CalLCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.CalPos))
				self.list2.append(getConfigListEntry(_("- Zoom"), LCD4linux.CalZoom))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.CalAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.CalSplit))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.CalType))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.CalTypeE))
				self.list2.append(getConfigListEntry(_("- Layout"), LCD4linux.CalLayout))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.CalColor))
				self.list2.append(getConfigListEntry(_("- Current Day Background Color"), LCD4linux.CalBackColor))
				self.list2.append(getConfigListEntry(_("- Caption Color"), LCD4linux.CalCaptionColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.CalShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.CalFont))
			self.list2.append(getConfigListEntry(_("Dates List"), LCD4linux.CalList))
			if LCD4linux.CalList.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.CalListLCD))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.CalListSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.CalListPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.CalListAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.CalListSplit))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.CalListLines))
				self.list2.append(getConfigListEntry(_("- max Width"), LCD4linux.CalListProzent))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.CalListType))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.CalListColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.CalListShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.CalListFont))
			self.list2.append(getConfigListEntry(_("Event Icon Bar"), LCD4linux.IconBar))
			if LCD4linux.IconBar.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.IconBarLCD))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.IconBarSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.IconBarPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.IconBarAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.IconBarSplit))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.IconBarType))
				self.list2.append(getConfigListEntry(_("- Popup Screen"), LCD4linux.IconBarPopup))
				self.list2.append(getConfigListEntry(_("- Popup LCD"), LCD4linux.IconBarPopupLCD))
			self.list2.append(getConfigListEntry(_("Rectangle 1"), LCD4linux.Box1))
			if LCD4linux.Box1.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Box1LCD))
				self.list2.append(getConfigListEntry(_("- Position x"), LCD4linux.Box1x1))
				self.list2.append(getConfigListEntry(_("- Position y"), LCD4linux.Box1y1))
				self.list2.append(getConfigListEntry(_("- Size x"), LCD4linux.Box1x2))
				self.list2.append(getConfigListEntry(_("- Size y"), LCD4linux.Box1y2))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Box1Color))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.Box1BackColor))
			self.list2.append(getConfigListEntry(_("Rectangle 2"), LCD4linux.Box2))
			if LCD4linux.Box2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Box2LCD))
				self.list2.append(getConfigListEntry(_("- Position x"), LCD4linux.Box2x1))
				self.list2.append(getConfigListEntry(_("- Position y"), LCD4linux.Box2y1))
				self.list2.append(getConfigListEntry(_("- Size x"), LCD4linux.Box2x2))
				self.list2.append(getConfigListEntry(_("- Size y"), LCD4linux.Box2y2))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Box2Color))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.Box2BackColor))
			self.list2.append(getConfigListEntry(_("Recording"), LCD4linux.Recording))
			if LCD4linux.Recording.value != "0":
				self.list2.append(getConfigListEntry(_("-  Type"), LCD4linux.RecordingType))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.RecordingSize))
				if LCD4linux.RecordingType.value == "2":
					self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.RecordingPos))
					self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.RecordingAlign))
					self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.RecordingSplit))
			self.list2.append(getConfigListEntry(_("Stutter TV"), LCD4linux.TV))
			if LCD4linux.TV.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.TVLCD))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.TVType))
			self["config"].setList(self.list2)
		elif self.mode == "Media":
			self.list3 = []
			self.list3.append(getConfigListEntry(_("- LCD 1 Background Color"), LCD4linux.MPLCDColor1))
			self.list3.append(getConfigListEntry(_("- LCD 1 Background-Picture [ok]>"), LCD4linux.MPLCDBild1))
			self.list3.append(getConfigListEntry(_("- LCD 1 Brightness [no SPF]"), LCD4linux.MPHelligkeit))
			self.list3.append(getConfigListEntry(_("- LCD 2 Background Color"), LCD4linux.MPLCDColor2))
			self.list3.append(getConfigListEntry(_("- LCD 2 Background-Picture [ok]>"), LCD4linux.MPLCDBild2))
			self.list3.append(getConfigListEntry(_("- LCD 2 Brightness [no SPF]"), LCD4linux.MPHelligkeit2))
			self.list3.append(getConfigListEntry(_("- LCD 3 Background Color"), LCD4linux.MPLCDColor3))
			self.list3.append(getConfigListEntry(_("- LCD 3 Background-Picture [ok]>"), LCD4linux.MPLCDBild3))
			self.list3.append(getConfigListEntry(_("- LCD 3 Brightness [no SPF]"), LCD4linux.MPHelligkeit3))
			self.list3.append(getConfigListEntry(_("- Screens used for Changing"), LCD4linux.MPScreenMax))
			self.list3.append(getConfigListEntry(_("Title"), LCD4linux.MPTitle))
			if LCD4linux.MPTitle.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPTitleLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPTitleSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPTitleLines))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPTitlePos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPTitleAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPTitleSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPTitleColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPTitleShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPTitleFont))
			self.list3.append(getConfigListEntry(_("Infos"), LCD4linux.MPComm))
			if LCD4linux.MPComm.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPCommLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPCommSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPCommLines))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPCommPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPCommAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPCommSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPCommColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPCommShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPCommFont))
			self.list3.append(getConfigListEntry(_("Extended Description"), LCD4linux.MPDesc))
			if LCD4linux.MPDesc.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPDescLCD))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPDescType))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPDescSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPDescLines))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPDescPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPDescAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPDescSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPDescColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPDescShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPDescFont))
			self.list3.append(getConfigListEntry(_("Program Name"), LCD4linux.MPChannel))
			if LCD4linux.MPChannel.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPChannelLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPChannelSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPChannelLines))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPChannelPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPChannelAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPChannelSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPChannelColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPChannelShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPChannelFont))
			self.list3.append(getConfigListEntry(_("Progress Bar"), LCD4linux.MPProgress))
			if LCD4linux.MPProgress.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPProgressLCD))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPProgressType))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPProgressSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPProgressPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPProgressAlign))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPProgressColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPProgressShadow2))
				self.list3.append(getConfigListEntry(_("- Shaded"), LCD4linux.MPProgressShadow))
			self.list3.append(getConfigListEntry(_("Volume"), LCD4linux.MPVol))
			if LCD4linux.MPVol.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPVolLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPVolSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPVolPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPVolAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPVolSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPVolColor))
				self.list3.append(getConfigListEntry(_("- Shaded"), LCD4linux.MPVolShadow))
			self.list3.append(getConfigListEntry(_("Clock"), LCD4linux.MPClock))
			if LCD4linux.MPClock.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPClockLCD))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPClockType))
				if LCD4linux.MPClockType.value[0] == "5":
					self.list3.append(getConfigListEntry(_("- Analog Clock"), LCD4linux.MPClockAnalog))
				elif LCD4linux.MPClockType.value[0] == "1":
					self.list3.append(getConfigListEntry(_("- Spacing"), LCD4linux.MPClockSpacing))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPClockSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPClockPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPClockAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPClockSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPClockColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPClockShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPClockFont))
			self.list3.append(getConfigListEntry(_("Clock 2"), LCD4linux.MPClock2))
			if LCD4linux.MPClock2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPClock2LCD))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPClock2Type))
				if LCD4linux.MPClock2Type.value[0] == "5":
					self.list3.append(getConfigListEntry(_("- Analog Clock"), LCD4linux.MPClock2Analog))
				elif LCD4linux.MPClock2Type.value[0] == "1":
					self.list3.append(getConfigListEntry(_("- Spacing"), LCD4linux.MPClock2Spacing))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPClock2Size))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPClock2Pos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPClock2Align))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPClock2Split))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPClock2Color))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPClock2Shadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPClock2Font))
			self.list3.append(getConfigListEntry(_("Informations"), LCD4linux.MPInfo))
			if LCD4linux.MPInfo.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPInfoLCD))
				self.list3.append(getConfigListEntry(_("- Sensors"), LCD4linux.MPInfoSensor))
				self.list3.append(getConfigListEntry(_("- CPU"), LCD4linux.MPInfoCPU))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPInfoSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPInfoPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPInfoAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPInfoSplit))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPInfoLines))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPInfoColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPInfoShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPInfoFont))
			self.list3.append(getConfigListEntry(_("Used Tuner"), LCD4linux.MPTuner))
			if LCD4linux.MPTuner.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPTunerLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPTunerSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPTunerPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPTunerAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPTunerSplit))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPTunerType))
				self.list3.append(getConfigListEntry(_("- only active Tuner"), LCD4linux.MPTunerActive))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPTunerFont))
			self.list3.append(getConfigListEntry(_("Next Timer Event"), LCD4linux.MPTimer))
			if LCD4linux.MPTimer.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPTimerLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPTimerSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPTimerLines))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPTimerType))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPTimerPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPTimerAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPTimerSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPTimerColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPTimerShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPTimerFont))
			self.list3.append(getConfigListEntry(_("Audio/Video"), LCD4linux.MPAV))
			if LCD4linux.MPAV.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPAVLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPAVSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPAVPos))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPAVType))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPAVAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPAVSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPAVColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPAVShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPAVFont))
			self.list3.append(getConfigListEntry(_("Bitrate"), LCD4linux.MPBitrate))
			if LCD4linux.MPBitrate.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPBitrateLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPBitrateSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPBitratePos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPBitrateAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPBitrateSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPBitrateColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPBitrateShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPBitrateFont))
			self.list3.append(getConfigListEntry(_("Online [Ping]"), LCD4linux.MPPing))
			if LCD4linux.MPPing.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPPingLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPPingSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPPingPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPPingAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPPingSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPPingColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPPingShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPPingFont))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPPingType))
				self.list3.append(getConfigListEntry(_("- Show State"), LCD4linux.MPPingShow))
				self.list3.append(getConfigListEntry(_("- Timeout"), LCD4linux.MPPingTimeout))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName1))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName2))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName3))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName4))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName5))
			self.list3.append(getConfigListEntry(_("Storage-Devices"), LCD4linux.MPDev))
			if LCD4linux.MPDev.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPDevLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPDevSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPDevPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPDevAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPDevSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPDevColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPDevShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPDevFont))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPDevType))
				self.list3.append(getConfigListEntry(_("- extra Info"), LCD4linux.MPDevExtra))
				self.list3.append(getConfigListEntry(_("- Device Name"), LCD4linux.MPDevName1))
				self.list3.append(getConfigListEntry(_("- Device Name"), LCD4linux.MPDevName2))
				self.list3.append(getConfigListEntry(_("- Device Name"), LCD4linux.MPDevName3))
				self.list3.append(getConfigListEntry(_("- Device Name"), LCD4linux.MPDevName4))
				self.list3.append(getConfigListEntry(_("- Device Name"), LCD4linux.MPDevName5))
			self.list3.append(getConfigListEntry(_("HDD"), LCD4linux.MPHdd))
			if LCD4linux.MPHdd.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPHddLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPHddSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPHddPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPHddAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPHddSplit))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPHddType))
			self.list3.append(getConfigListEntry(_("Weather"), LCD4linux.MPWetter))
			if LCD4linux.MPWetter.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPWetterLCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPWetterPos))
				self.list3.append(getConfigListEntry(_("- Zoom"), LCD4linux.MPWetterZoom))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPWetterAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPWetterSplit))
				self.list3.append(getConfigListEntry(_("- Weather Type"), LCD4linux.MPWetterType))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPWetterColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPWetterShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPWetterFont))
			self.list3.append(getConfigListEntry(_("Weather 2"), LCD4linux.MPWetter2))
			if LCD4linux.MPWetter2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPWetter2LCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPWetter2Pos))
				self.list3.append(getConfigListEntry(_("- Zoom"), LCD4linux.MPWetter2Zoom))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPWetter2Align))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPWetter2Split))
				self.list3.append(getConfigListEntry(_("- Weather Type"), LCD4linux.MPWetter2Type))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPWetter2Color))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPWetter2Shadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPWetter2Font))
			self.list3.append(getConfigListEntry(_("Meteo-Weather Station"), LCD4linux.MPMeteo))
			if LCD4linux.MPMeteo.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPMeteoLCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPMeteoPos))
				self.list3.append(getConfigListEntry(_("- Zoom"), LCD4linux.MPMeteoZoom))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPMeteoAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPMeteoSplit))
				self.list3.append(getConfigListEntry(_("- Weather Type"), LCD4linux.MPMeteoType))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPMeteoColor))
			self.list3.append(getConfigListEntry(_("Netatmo"), LCD4linux.MPNetAtmo))
			if LCD4linux.MPNetAtmo.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPNetAtmoLCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPNetAtmoPos))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPNetAtmoSize))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPNetAtmoAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPNetAtmoSplit))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmoType))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmoType2))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPNetAtmoColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPNetAtmoShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPNetAtmoFont))
			self.list3.append(getConfigListEntry(_("Netatmo CO2 Indicator"), LCD4linux.MPNetAtmoCO2))
			if LCD4linux.MPNetAtmoCO2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPNetAtmoCO2LCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPNetAtmoCO2Pos))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPNetAtmoCO2Size))
				self.list3.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.MPNetAtmoCO2Len))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPNetAtmoCO2Align))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPNetAtmoCO2Split))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmoCO2Type))
			self.list3.append(getConfigListEntry(_("Netatmo Comfort Indicator"), LCD4linux.MPNetAtmoIDX))
			if LCD4linux.MPNetAtmoIDX.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPNetAtmoIDXLCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPNetAtmoIDXPos))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPNetAtmoIDXSize))
				self.list3.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.MPNetAtmoIDXLen))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPNetAtmoIDXAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPNetAtmoIDXSplit))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmoIDXType))
			self.list3.append(getConfigListEntry(_("Moonphase"), LCD4linux.MPMoon))
			if LCD4linux.MPMoon.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPMoonLCD))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPMoonSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPMoonPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPMoonAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPMoonSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPMoonColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPMoonShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPMoonFont))
			self.list3.append(getConfigListEntry(_("Sunrise"), LCD4linux.MPSun))
			if LCD4linux.MPSun.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPSunLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPSunSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPSunPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPSunAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPSunSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPSunColor))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPSunBackColor))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPSunType))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPSunShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPSunFont))
			self.list3.append(getConfigListEntry(_("Show Textfile"), LCD4linux.MPText))
			if LCD4linux.MPText.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPTextLCD))
				self.list3.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.MPTextFile))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPTextSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPTextPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPTextAlign))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPTextColor))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPTextBackColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPTextShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPTextFont))
			self.list3.append(getConfigListEntry(_("Show Picture"), LCD4linux.MPBild))
			if LCD4linux.MPBild.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPBildLCD))
				self.list3.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.MPBildFile))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPBildSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPBildPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPBildAlign))
				self.list3.append(getConfigListEntry(_("- Quick Update"), LCD4linux.MPBildQuick))
				self.list3.append(getConfigListEntry(_("- Transparency"), LCD4linux.MPBildTransp))
			self.list3.append(getConfigListEntry(_("Show Picture 2"), LCD4linux.MPBild2))
			if LCD4linux.MPBild2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPBild2LCD))
				self.list3.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.MPBild2File))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPBild2Size))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPBild2Pos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPBild2Align))
				self.list3.append(getConfigListEntry(_("- Quick Update"), LCD4linux.MPBild2Quick))
				self.list3.append(getConfigListEntry(_("- Transparency"), LCD4linux.MPBild2Transp))
			self.list3.append(getConfigListEntry(_("Show Cover"), LCD4linux.MPCover))
			if LCD4linux.MPCover.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPCoverLCD))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPCoverSize))
				self.list3.append(getConfigListEntry(_("- Size max Height"), LCD4linux.MPCoverSizeH))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPCoverPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPCoverAlign))
				self.list3.append(getConfigListEntry(_("- Search Path [ok]>"), LCD4linux.MPCoverPath1))
				self.list3.append(getConfigListEntry(_("- Search Path [ok]>"), LCD4linux.MPCoverPath2))
				self.list3.append(getConfigListEntry(_("- Default Cover [ok]>"), LCD4linux.MPCoverFile))
				self.list3.append(getConfigListEntry(_("- Download Cover from Google"), LCD4linux.MPCoverGoogle))
				self.list3.append(getConfigListEntry(_("- Picon First"), LCD4linux.MPCoverPiconFirst))
				self.list3.append(getConfigListEntry(_("- Transparency"), LCD4linux.MPCoverTransp))
			self.list3.append(getConfigListEntry(_("Show oscam.lcd"), LCD4linux.MPOSCAM))
			if LCD4linux.MPOSCAM.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPOSCAMLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPOSCAMSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPOSCAMPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPOSCAMAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPOSCAMSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPOSCAMColor))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPOSCAMBackColor))
			self.list3.append(getConfigListEntry(_("Mail"), LCD4linux.MPMail))
			if LCD4linux.MPMail.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPMailLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPMailSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPMailPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPMailAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPMailSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPMailColor))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPMailBackColor))
				self.list3.append(getConfigListEntry(_("- Lines"), LCD4linux.MPMailLines))
				self.list3.append(getConfigListEntry(_("- Mail Konto"), LCD4linux.MPMailKonto))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPMailType))
				self.list3.append(getConfigListEntry(_("- max Width"), LCD4linux.MPMailProzent))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPMailShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPMailFont))
			self.list3.append(getConfigListEntry(_("FritzCall"), LCD4linux.MPFritz))
			if LCD4linux.MPFritz.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPFritzLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPFritzSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPFritzPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPFritzAlign))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPFritzColor))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPFritzBackColor))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPFritzType))
				self.list3.append(getConfigListEntry(_("- Picture Size"), LCD4linux.MPFritzPicSize))
				self.list3.append(getConfigListEntry(_("- Picture Position"), LCD4linux.MPFritzPicPos))
				self.list3.append(getConfigListEntry(_("- Picture Alignment"), LCD4linux.MPFritzPicAlign))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPFritzShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPFritzFont))
			self.list3.append(getConfigListEntry(_("Calendar"), LCD4linux.MPCal))
			if LCD4linux.MPCal.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPCalLCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPCalPos))
				self.list3.append(getConfigListEntry(_("- Zoom"), LCD4linux.MPCalZoom))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPCalAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPCalSplit))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPCalType))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPCalTypeE))
				self.list3.append(getConfigListEntry(_("- Layout"), LCD4linux.MPCalLayout))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPCalColor))
				self.list3.append(getConfigListEntry(_("- Current Day Background Color"), LCD4linux.MPCalBackColor))
				self.list3.append(getConfigListEntry(_("- Caption Color"), LCD4linux.MPCalCaptionColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPCalShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPCalFont))
			self.list3.append(getConfigListEntry(_("Dates List"), LCD4linux.MPCalList))
			if LCD4linux.MPCalList.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPCalListLCD))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPCalListSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPCalListPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPCalListAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPCalListSplit))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPCalListLines))
				self.list3.append(getConfigListEntry(_("- max Width"), LCD4linux.MPCalListProzent))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPCalListType))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPCalListColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPCalListShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPCalListFont))
			self.list3.append(getConfigListEntry(_("Event Icon Bar"), LCD4linux.MPIconBar))
			if LCD4linux.MPIconBar.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPIconBarLCD))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPIconBarSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPIconBarPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPIconBarAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPIconBarSplit))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPIconBarType))
				self.list3.append(getConfigListEntry(_("- Popup Screen"), LCD4linux.MPIconBarPopup))
				self.list3.append(getConfigListEntry(_("- Popup LCD"), LCD4linux.MPIconBarPopupLCD))
			self.list3.append(getConfigListEntry(_("Rectangle 1"), LCD4linux.MPBox1))
			if LCD4linux.MPBox1.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPBox1LCD))
				self.list3.append(getConfigListEntry(_("- Position x"), LCD4linux.MPBox1x1))
				self.list3.append(getConfigListEntry(_("- Position y"), LCD4linux.MPBox1y1))
				self.list3.append(getConfigListEntry(_("- Size x"), LCD4linux.MPBox1x2))
				self.list3.append(getConfigListEntry(_("- Size y"), LCD4linux.MPBox1y2))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPBox1Color))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPBox1BackColor))
			self.list3.append(getConfigListEntry(_("Rectangle 2"), LCD4linux.MPBox2))
			if LCD4linux.MPBox2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPBox2LCD))
				self.list3.append(getConfigListEntry(_("- Position x"), LCD4linux.MPBox2x1))
				self.list3.append(getConfigListEntry(_("- Position y"), LCD4linux.MPBox2y1))
				self.list3.append(getConfigListEntry(_("- Size x"), LCD4linux.MPBox2x2))
				self.list3.append(getConfigListEntry(_("- Size y"), LCD4linux.MPBox2y2))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPBox2Color))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPBox2BackColor))
			self.list3.append(getConfigListEntry(_("Recording"), LCD4linux.MPRecording))
			if LCD4linux.MPRecording.value != "0":
				self.list3.append(getConfigListEntry(_("-  Type"), LCD4linux.MPRecordingType))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPRecordingSize))
				if LCD4linux.MPRecordingType.value == "2":
					self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPRecordingPos))
					self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPRecordingAlign))
					self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPRecordingSplit))
			self["config"].setList(self.list3)
		elif self.mode == "Idle":
			self.list4 = []
			self.list4.append(getConfigListEntry(_("LCD Display"), LCD4linux.Standby))
			self.list4.append(getConfigListEntry(_("- Backlight Off [disable set Off=On]"), LCD4linux.StandbyLCDoff))
			self.list4.append(getConfigListEntry(_("- Backlight On"), LCD4linux.StandbyLCDon))
			self.list4.append(getConfigListEntry(_("- Backlight Weekend Off [disable set Off=On]"), LCD4linux.StandbyLCDWEoff))
			self.list4.append(getConfigListEntry(_("- Backlight Weekend On"), LCD4linux.StandbyLCDWEon))
			self.list4.append(getConfigListEntry(_("- LCD 1 Background Color"), LCD4linux.StandbyLCDColor1))
			self.list4.append(getConfigListEntry(_("- LCD 1 Background-Picture [ok]>"), LCD4linux.StandbyLCDBild1))
			self.list4.append(getConfigListEntry(_("- LCD 1 Brightness [no SPF]"), LCD4linux.StandbyHelligkeit))
			self.list4.append(getConfigListEntry(_("- LCD 2 Background Color"), LCD4linux.StandbyLCDColor2))
			self.list4.append(getConfigListEntry(_("- LCD 2 Background-Picture [ok]>"), LCD4linux.StandbyLCDBild2))
			self.list4.append(getConfigListEntry(_("- LCD 2 Brightness [no SPF]"), LCD4linux.StandbyHelligkeit2))
			self.list4.append(getConfigListEntry(_("- LCD 3 Background Color"), LCD4linux.StandbyLCDColor3))
			self.list4.append(getConfigListEntry(_("- LCD 3 Background-Picture [ok]>"), LCD4linux.StandbyLCDBild3))
			self.list4.append(getConfigListEntry(_("- LCD 3 Brightness [no SPF]"), LCD4linux.StandbyHelligkeit3))
			self.list4.append(getConfigListEntry(_("- Screens used for Changing"), LCD4linux.StandbyScreenMax))
			self.list4.append(getConfigListEntry(_("Screen 1 Changing Time"), LCD4linux.StandbyScreenTime))
			if LCD4linux.StandbyScreenTime.value != "0":
				self.list4.append(getConfigListEntry(_("- Screen 2 Changing Time"), LCD4linux.StandbyScreenTime2))
				self.list4.append(getConfigListEntry(_("- Screen 3 Changing Time"), LCD4linux.StandbyScreenTime3))
				self.list4.append(getConfigListEntry(_("- Screen 4 Changing Time"), LCD4linux.StandbyScreenTime4))
				self.list4.append(getConfigListEntry(_("- Screen 5 Changing Time"), LCD4linux.StandbyScreenTime5))
				self.list4.append(getConfigListEntry(_("- Screen 6 Changing Time"), LCD4linux.StandbyScreenTime6))
				self.list4.append(getConfigListEntry(_("- Screen 7 Changing Time"), LCD4linux.StandbyScreenTime7))
				self.list4.append(getConfigListEntry(_("- Screen 8 Changing Time"), LCD4linux.StandbyScreenTime8))
				self.list4.append(getConfigListEntry(_("- Screen 9 Changing Time"), LCD4linux.StandbyScreenTime9))
			self.list4.append(getConfigListEntry(_("Clock"), LCD4linux.StandbyClock))
			if LCD4linux.StandbyClock.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyClockLCD))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyClockType))
				if LCD4linux.StandbyClockType.value[0] == "5":
					self.list4.append(getConfigListEntry(_("- Analog Clock"), LCD4linux.StandbyClockAnalog))
				elif LCD4linux.StandbyClockType.value[0] == "1":
					self.list4.append(getConfigListEntry(_("- Spacing"), LCD4linux.StandbyClockSpacing))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyClockSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyClockPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyClockAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyClockSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyClockColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyClockShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyClockFont))
			self.list4.append(getConfigListEntry(_("Clock 2"), LCD4linux.StandbyClock2))
			if LCD4linux.StandbyClock2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyClock2LCD))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyClock2Type))
				if LCD4linux.StandbyClock2Type.value[0] == "5":
					self.list4.append(getConfigListEntry(_("- Analog Clock"), LCD4linux.StandbyClock2Analog))
				elif LCD4linux.StandbyClock2Type.value[0] == "1":
					self.list4.append(getConfigListEntry(_("- Spacing"), LCD4linux.StandbyClock2Spacing))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyClock2Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyClock2Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyClock2Align))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyClock2Split))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyClock2Color))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyClock2Shadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyClock2Font))
			self.list4.append(getConfigListEntry(_("Next Timer Event"), LCD4linux.StandbyTimer))
			if LCD4linux.StandbyTimer.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyTimerLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyTimerSize))
				self.list4.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.StandbyTimerLines))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyTimerType))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyTimerPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyTimerAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyTimerSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyTimerColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyTimerShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyTimerFont))
			self.list4.append(getConfigListEntry(_("Informations"), LCD4linux.StandbyInfo))
			if LCD4linux.StandbyInfo.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyInfoLCD))
				self.list4.append(getConfigListEntry(_("- Sensors"), LCD4linux.StandbyInfoSensor))
				self.list4.append(getConfigListEntry(_("- CPU"), LCD4linux.StandbyInfoCPU))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyInfoSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyInfoPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyInfoAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyInfoSplit))
				self.list4.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.StandbyInfoLines))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyInfoColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyInfoShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyInfoFont))
			self.list4.append(getConfigListEntry(_("Used Tuner"), LCD4linux.StandbyTuner))
			if LCD4linux.StandbyTuner.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyTunerLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyTunerSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyTunerPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyTunerAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyTunerSplit))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyTunerType))
				self.list4.append(getConfigListEntry(_("- only active Tuner"), LCD4linux.StandbyTunerActive))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyTunerFont))
			self.list4.append(getConfigListEntry(_("Online [Ping]"), LCD4linux.StandbyPing))
			if LCD4linux.StandbyPing.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyPingLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyPingSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyPingPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyPingAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyPingSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyPingColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyPingShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyPingFont))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyPingType))
				self.list4.append(getConfigListEntry(_("- Show State"), LCD4linux.StandbyPingShow))
				self.list4.append(getConfigListEntry(_("- Timeout"), LCD4linux.StandbyPingTimeout))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName1))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName2))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName3))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName4))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName5))
			self.list4.append(getConfigListEntry(_("Storage-Devices"), LCD4linux.StandbyDev))
			if LCD4linux.StandbyDev.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyDevLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyDevSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyDevPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyDevAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyDevSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyDevColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyDevShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyDevFont))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyDevType))
				self.list4.append(getConfigListEntry(_("- extra Info"), LCD4linux.StandbyDevExtra))
				self.list4.append(getConfigListEntry(_("- Device Name"), LCD4linux.StandbyDevName1))
				self.list4.append(getConfigListEntry(_("- Device Name"), LCD4linux.StandbyDevName2))
				self.list4.append(getConfigListEntry(_("- Device Name"), LCD4linux.StandbyDevName3))
				self.list4.append(getConfigListEntry(_("- Device Name"), LCD4linux.StandbyDevName4))
				self.list4.append(getConfigListEntry(_("- Device Name"), LCD4linux.StandbyDevName5))
			self.list4.append(getConfigListEntry(_("HDD"), LCD4linux.StandbyHdd))
			if LCD4linux.StandbyHdd.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyHddLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyHddSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyHddPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyHddAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyHddSplit))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyHddType))
			self.list4.append(getConfigListEntry(_("Weather"), LCD4linux.StandbyWetter))
			if LCD4linux.StandbyWetter.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyWetterLCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyWetterPos))
				self.list4.append(getConfigListEntry(_("- Zoom"), LCD4linux.StandbyWetterZoom))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyWetterAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyWetterSplit))
				self.list4.append(getConfigListEntry(_("- Weather Type"), LCD4linux.StandbyWetterType))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyWetterColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyWetterShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyWetterFont))
			self.list4.append(getConfigListEntry(_("Weather 2"), LCD4linux.StandbyWetter2))
			if LCD4linux.StandbyWetter2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyWetter2LCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyWetter2Pos))
				self.list4.append(getConfigListEntry(_("- Zoom"), LCD4linux.StandbyWetter2Zoom))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyWetter2Align))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyWetter2Split))
				self.list4.append(getConfigListEntry(_("- Weather Type"), LCD4linux.StandbyWetter2Type))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyWetter2Color))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyWetter2Shadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyWetter2Font))
			self.list4.append(getConfigListEntry(_("Meteo-Weather Station"), LCD4linux.StandbyMeteo))
			if LCD4linux.StandbyMeteo.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyMeteoLCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyMeteoPos))
				self.list4.append(getConfigListEntry(_("- Zoom"), LCD4linux.StandbyMeteoZoom))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyMeteoAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyMeteoSplit))
				self.list4.append(getConfigListEntry(_("- Weather Type"), LCD4linux.StandbyMeteoType))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyMeteoColor))
			self.list4.append(getConfigListEntry(_("Netatmo"), LCD4linux.StandbyNetAtmo))
			if LCD4linux.StandbyNetAtmo.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyNetAtmoLCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyNetAtmoPos))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyNetAtmoSize))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyNetAtmoAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyNetAtmoSplit))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmoType))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmoType2))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyNetAtmoColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyNetAtmoShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyNetAtmoFont))
			self.list4.append(getConfigListEntry(_("Netatmo CO2 Indicator"), LCD4linux.StandbyNetAtmoCO2))
			if LCD4linux.StandbyNetAtmoCO2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyNetAtmoCO2LCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyNetAtmoCO2Pos))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyNetAtmoCO2Size))
				self.list4.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.StandbyNetAtmoCO2Len))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyNetAtmoCO2Align))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyNetAtmoCO2Split))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmoCO2Type))
			self.list4.append(getConfigListEntry(_("Netatmo Comfort Indicator"), LCD4linux.StandbyNetAtmoIDX))
			if LCD4linux.StandbyNetAtmoIDX.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyNetAtmoIDXLCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyNetAtmoIDXPos))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyNetAtmoIDXSize))
				self.list4.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.StandbyNetAtmoIDXLen))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyNetAtmoIDXAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyNetAtmoIDXSplit))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmoIDXType))
			self.list4.append(getConfigListEntry(_("Moonphase"), LCD4linux.StandbyMoon))
			if LCD4linux.StandbyMoon.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyMoonLCD))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyMoonSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyMoonPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyMoonAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyMoonSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyMoonColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyMoonShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyMoonFont))
			self.list4.append(getConfigListEntry(_("Sunrise"), LCD4linux.StandbySun))
			if LCD4linux.StandbySun.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbySunLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbySunSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbySunPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbySunAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbySunSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbySunColor))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbySunBackColor))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbySunType))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbySunShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbySunFont))
			self.list4.append(getConfigListEntry(_("Show oscam.lcd"), LCD4linux.StandbyOSCAM))
			if LCD4linux.StandbyOSCAM.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyOSCAMLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyOSCAMSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyOSCAMPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyOSCAMAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyOSCAMSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyOSCAMColor))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyOSCAMBackColor))
			self.list4.append(getConfigListEntry(_("Show Textfile"), LCD4linux.StandbyText))
			if LCD4linux.StandbyText.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyTextLCD))
				self.list4.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.StandbyTextFile))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyTextSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyTextPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyTextAlign))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyTextColor))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyTextBackColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyTextShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyTextFont))
			self.list4.append(getConfigListEntry(_("Show Textfile 2"), LCD4linux.StandbyText2))
			if LCD4linux.StandbyText2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyText2LCD))
				self.list4.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.StandbyText2File))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyText2Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyText2Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyText2Align))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyText2Color))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyText2BackColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyText2Shadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyText2Font))
			self.list4.append(getConfigListEntry(_("Show Textfile 3"), LCD4linux.StandbyText3))
			if LCD4linux.StandbyText3.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyText3LCD))
				self.list4.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.StandbyText3File))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyText3Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyText3Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyText3Align))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyText3Color))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyText3BackColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyText3Shadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyText3Font))
			self.list4.append(getConfigListEntry(_("Show HTTP Text"), LCD4linux.StandbyHTTP))
			if LCD4linux.StandbyHTTP.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyHTTPLCD))
				self.list4.append(getConfigListEntry(_("- URL"), LCD4linux.StandbyHTTPURL))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyHTTPSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyHTTPPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyHTTPAlign))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyHTTPColor))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyHTTPBackColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyHTTPShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyHTTPFont))
			self.list4.append(getConfigListEntry(_("WWW-Internet Converter"), LCD4linux.StandbyWWW1))
			if LCD4linux.StandbyWWW1.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyWWW1LCD))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyWWW1Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyWWW1Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyWWW1Align))
				self.list4.append(getConfigListEntry(_("- URL"), LCD4linux.StandbyWWW1url))
				self.list4.append(getConfigListEntry(_("- HTTP Width"), LCD4linux.StandbyWWW1w))
				self.list4.append(getConfigListEntry(_("- HTTP Height"), LCD4linux.StandbyWWW1h))
				self.list4.append(getConfigListEntry(_("- Cut from X"), LCD4linux.StandbyWWW1CutX))
				self.list4.append(getConfigListEntry(_("- Cut from Y"), LCD4linux.StandbyWWW1CutY))
				self.list4.append(getConfigListEntry(_("- Cut Width [disable = 0]"), LCD4linux.StandbyWWW1CutW))
				self.list4.append(getConfigListEntry(_("- Cut Height [disable = 0]"), LCD4linux.StandbyWWW1CutH))
			self.list4.append(getConfigListEntry(_("Show Picture"), LCD4linux.StandbyBild))
			if LCD4linux.StandbyBild.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBildLCD))
				self.list4.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.StandbyBildFile))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyBildSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyBildPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyBildAlign))
				self.list4.append(getConfigListEntry(_("- Quick Update"), LCD4linux.StandbyBildQuick))
				self.list4.append(getConfigListEntry(_("- Transparency"), LCD4linux.StandbyBildTransp))
			self.list4.append(getConfigListEntry(_("Show Picture 2"), LCD4linux.StandbyBild2))
			if LCD4linux.StandbyBild2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBild2LCD))
				self.list4.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.StandbyBild2File))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyBild2Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyBild2Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyBild2Align))
				self.list4.append(getConfigListEntry(_("- Quick Update"), LCD4linux.StandbyBild2Quick))
				self.list4.append(getConfigListEntry(_("- Transparency"), LCD4linux.StandbyBild2Transp))
			self.list4.append(getConfigListEntry(_("Show Picture 3"), LCD4linux.StandbyBild3))
			if LCD4linux.StandbyBild3.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBild3LCD))
				self.list4.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.StandbyBild3File))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyBild3Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyBild3Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyBild3Align))
				self.list4.append(getConfigListEntry(_("- Quick Update"), LCD4linux.StandbyBild3Quick))
				self.list4.append(getConfigListEntry(_("- Transparency"), LCD4linux.StandbyBild3Transp))
			self.list4.append(getConfigListEntry(_("Show Picture 4"), LCD4linux.StandbyBild4))
			if LCD4linux.StandbyBild4.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBild4LCD))
				self.list4.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.StandbyBild4File))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyBild4Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyBild4Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyBild4Align))
				self.list4.append(getConfigListEntry(_("- Quick Update"), LCD4linux.StandbyBild4Quick))
				self.list4.append(getConfigListEntry(_("- Transparency"), LCD4linux.StandbyBild4Transp))
			self.list4.append(getConfigListEntry(_("Mail"), LCD4linux.StandbyMail))
			if LCD4linux.StandbyMail.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyMailLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyMailSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyMailPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyMailAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyMailSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyMailColor))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyMailBackColor))
				self.list4.append(getConfigListEntry(_("- Lines"), LCD4linux.StandbyMailLines))
				self.list4.append(getConfigListEntry(_("- Mail Konto"), LCD4linux.StandbyMailKonto))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyMailType))
				self.list4.append(getConfigListEntry(_("- max Width"), LCD4linux.StandbyMailProzent))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyMailShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyMailFont))
			self.list4.append(getConfigListEntry(_("FritzCall"), LCD4linux.StandbyFritz))
			if LCD4linux.StandbyFritz.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyFritzLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyFritzSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyFritzPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyFritzAlign))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyFritzColor))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyFritzBackColor))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyFritzType))
				self.list4.append(getConfigListEntry(_("- Picture Size"), LCD4linux.StandbyFritzPicSize))
				self.list4.append(getConfigListEntry(_("- Picture Position"), LCD4linux.StandbyFritzPicPos))
				self.list4.append(getConfigListEntry(_("- Picture Alignment"), LCD4linux.StandbyFritzPicAlign))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyFritzShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyFritzFont))
			self.list4.append(getConfigListEntry(_("Calendar"), LCD4linux.StandbyCal))
			if LCD4linux.StandbyCal.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyCalLCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyCalPos))
				self.list4.append(getConfigListEntry(_("- Zoom"), LCD4linux.StandbyCalZoom))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyCalAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyCalSplit))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyCalType))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyCalTypeE))
				self.list4.append(getConfigListEntry(_("- Layout"), LCD4linux.StandbyCalLayout))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyCalColor))
				self.list4.append(getConfigListEntry(_("- Current Day Background Color"), LCD4linux.StandbyCalBackColor))
				self.list4.append(getConfigListEntry(_("- Caption Color"), LCD4linux.StandbyCalCaptionColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyCalShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyCalFont))
			self.list4.append(getConfigListEntry(_("Dates List"), LCD4linux.StandbyCalList))
			if LCD4linux.StandbyCalList.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyCalListLCD))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyCalListSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyCalListPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyCalListAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyCalListSplit))
				self.list4.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.StandbyCalListLines))
				self.list4.append(getConfigListEntry(_("- max Width"), LCD4linux.StandbyCalListProzent))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyCalListType))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyCalListColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyCalListShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyCalListFont))
			self.list4.append(getConfigListEntry(_("Event Icon Bar"), LCD4linux.StandbyIconBar))
			if LCD4linux.StandbyIconBar.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyIconBarLCD))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyIconBarSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyIconBarPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyIconBarAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyIconBarSplit))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyIconBarType))
				self.list4.append(getConfigListEntry(_("- Popup Screen"), LCD4linux.StandbyIconBarPopup))
				self.list4.append(getConfigListEntry(_("- Popup LCD"), LCD4linux.StandbyIconBarPopupLCD))
			self.list4.append(getConfigListEntry(_("Rectangle 1"), LCD4linux.StandbyBox1))
			if LCD4linux.StandbyBox1.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBox1LCD))
				self.list4.append(getConfigListEntry(_("- Position x"), LCD4linux.StandbyBox1x1))
				self.list4.append(getConfigListEntry(_("- Position y"), LCD4linux.StandbyBox1y1))
				self.list4.append(getConfigListEntry(_("- Size x"), LCD4linux.StandbyBox1x2))
				self.list4.append(getConfigListEntry(_("- Size y"), LCD4linux.StandbyBox1y2))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyBox1Color))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyBox1BackColor))
			self.list4.append(getConfigListEntry(_("Rectangle 2"), LCD4linux.StandbyBox2))
			if LCD4linux.StandbyBox2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBox2LCD))
				self.list4.append(getConfigListEntry(_("- Position x"), LCD4linux.StandbyBox2x1))
				self.list4.append(getConfigListEntry(_("- Position y"), LCD4linux.StandbyBox2y1))
				self.list4.append(getConfigListEntry(_("- Size x"), LCD4linux.StandbyBox2x2))
				self.list4.append(getConfigListEntry(_("- Size y"), LCD4linux.StandbyBox2y2))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyBox2Color))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyBox2BackColor))
			self.list4.append(getConfigListEntry(_("Recording"), LCD4linux.StandbyRecording))
			if LCD4linux.StandbyRecording.value != "0":
				self.list4.append(getConfigListEntry(_("-  Type"), LCD4linux.StandbyRecordingType))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyRecordingSize))
				if LCD4linux.StandbyRecordingType.value == "2":
					self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyRecordingPos))
					self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyRecordingAlign))
					self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyRecordingSplit))
			self["config"].setList(self.list4)

	def Page(self):
		if time()-self.toggle < 0.5:
			L4log("to fast")
			return
		L4log("Page",self.mode)
		self.LastSelect=self.mode
		self.Aktuell=" "
		if self.mode == "Global":
			self.mode = "On"
			self.setTitle("LCD4linux Display-Mode On")
			self["key_blue"].setText("Set Media >>")
			self.SetList()
		elif self.mode == "On":
			self.mode = "Media"
			self.setTitle("LCD4linux Display-Mode MediaPlayer")
			self["key_blue"].setText("Set Idle >>")
			self.SetList()
		elif self.mode == "Media":
			self.mode = "Idle"
			self.setTitle("LCD4linux Display-Mode Idle")
			self["key_blue"].setText("Set Global >>")
			self.SetList()
		elif self.mode == "Idle":
			self.mode = "Global"
			self.setTitle("LCD4linux Settings")
			self["key_blue"].setText("Set On >>")
			self.SetList()
		getBilder()
		self.toggle = time()

	def keyOK(self):
		ConfigListScreen.keyOK(self)
		sel = self["config"].getCurrent()[1]
		try:
			if sel.value.lower().startswith("http"):
				return
			if sel in [LCD4linux.PiconPath, LCD4linux.Picon2Path, LCD4linux.PiconCache, LCD4linux.Picon2Cache, LCD4linux.PiconPathAlt, LCD4linux.Picon2PathAlt, LCD4linux.ConfigPath, LCD4linux.WetterPath, LCD4linux.MPCoverPath1, LCD4linux.MPCoverPath2, LCD4linux.FritzPath, LCD4linux.CalPath, LCD4linux.SatPath, LCD4linux.ProvPath, LCD4linux.MoonPath]:
				L4log("select Dir 1")
				self.session.openWithCallback(self.dirSelected, LCDdisplayFile, text = _("Choose dir"), FileName = self["config"].getCurrent()[1].value, showFiles = False)
			elif sel in [LCD4linux.LCDBild1, LCD4linux.LCDBild2, LCD4linux.MPLCDBild1, LCD4linux.MPLCDBild2, LCD4linux.StandbyLCDBild1, LCD4linux.StandbyLCDBild2, LCD4linux.FritzFrame]:
				L4log("select File 1")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, text = _("Choose file"), FileName = self["config"].getCurrent()[1].value, showFiles = True)
			elif sel in [LCD4linux.OSCAMFile, LCD4linux.TextFile, LCD4linux.Text2File, LCD4linux.Text3File, LCD4linux.MPTextFile, LCD4linux.MPCoverFile, LCD4linux.BildFile, LCD4linux.Bild2File, LCD4linux.Bild3File, LCD4linux.Bild4File, LCD4linux.RecordingPath]:
				L4log("select File 2")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, text = _("Choose file"), FileName = self["config"].getCurrent()[1].value, showFiles = True)
			elif sel in [LCD4linux.Font, LCD4linux.Font1, LCD4linux.Font2, LCD4linux.Font3]:
				L4log("select File 3")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, matchingPattern = "ttf", text = _("Choose font"), FileName = self["config"].getCurrent()[1].value, showFiles = True)
			elif sel in [LCD4linux.MPBildFile, LCD4linux.MPBild2File, LCD4linux.StandbyBildFile, LCD4linux.StandbyBild2File, LCD4linux.StandbyBild3File, LCD4linux.StandbyBild4File, LCD4linux.StandbyTextFile, LCD4linux.StandbyText2File, LCD4linux.StandbyText3File]:
				L4log("select File 4")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, text = _("Choose file"), FileName = self["config"].getCurrent()[1].value, showFiles = True)
		except Exception, e:
			L4log("Key-OK Config Fehler")
#			self.session.open(MessageBox, "This is not possible") 
#			self.session.open(MessageBox, "Error:\n" + str(e), MessageBox.TYPE_ERROR)

	def dirSelected(self, dir, dir1):
		if dir is None or dir1 is None:
			return
		if dir+dir1 != "" and dir1.endswith("/"):
			sel = self["config"].getCurrent()[1]
#		if dir is not None and dir != "?":
			if dir1[-1:] != "/":
				dir1 += "/"
			if sel == LCD4linux.PiconPath:
				LCD4linux.PiconPath.value = dir1
			elif sel == LCD4linux.Picon2Path:
				LCD4linux.Picon2Path.value = dir1
			elif sel == LCD4linux.PiconCache:
				LCD4linux.PiconCache.value = dir1
			elif sel == LCD4linux.Picon2Cache:
				LCD4linux.Picon2Cache.value = dir1
			elif sel == LCD4linux.PiconPathAlt:
				LCD4linux.PiconPathAlt.value = dir1
			elif sel == LCD4linux.Picon2PathAlt:
				LCD4linux.Picon2PathAlt.value = dir1
			elif sel == LCD4linux.ConfigPath:
				LCD4linux.ConfigPath.value = dir1
			elif sel == LCD4linux.WetterPath:
				LCD4linux.WetterPath.value = dir1
			elif sel == LCD4linux.MPCoverPath1:
				LCD4linux.MPCoverPath1.value = dir1
			elif sel == LCD4linux.MPCoverPath2:
				LCD4linux.MPCoverPath2.value = dir1
			elif sel == LCD4linux.FritzPath:
				LCD4linux.FritzPath.value = dir1
			elif sel == LCD4linux.CalPath:
				LCD4linux.CalPath.value = dir1
			elif sel == LCD4linux.SatPath:
				LCD4linux.SatPath.value = dir1
			elif sel == LCD4linux.ProvPath:
				LCD4linux.ProvPath.value = dir1
			elif sel == LCD4linux.MoonPath:
				LCD4linux.MoonPath.value = dir1

	def fileSelected(self, dir, dir1):
		global FONT
		if dir is None or dir1 is None:
			return
		sel = self["config"].getCurrent()[1]
		if dir+dir1 != "" and not dir1.endswith("/"):
			dirdir = os.path.join(dir,dir1)
			if sel == LCD4linux.LCDBild1:
				LCD4linux.LCDBild1.value = dirdir
			elif sel == LCD4linux.LCDBild2:
				LCD4linux.LCDBild2.value = dirdir
			elif sel == LCD4linux.MPLCDBild1:
				LCD4linux.MPLCDBild1.value = dirdir
			elif sel == LCD4linux.MPLCDBild2:
				LCD4linux.MPLCDBild2.value = dirdir
			elif sel == LCD4linux.StandbyLCDBild1:
				LCD4linux.StandbyLCDBild1.value = dirdir
			elif sel == LCD4linux.StandbyLCDBild2:
				LCD4linux.StandbyLCDBild2.value = dirdir
			elif sel == LCD4linux.OSCAMFile:
				LCD4linux.OSCAMFile.value = dirdir
			elif sel == LCD4linux.TextFile:
				LCD4linux.TextFile.value = dirdir
			elif sel == LCD4linux.Text2File:
				LCD4linux.Text2File.value = dirdir
			elif sel == LCD4linux.Text3File:
				LCD4linux.Text3File.value = dirdir
			elif sel == LCD4linux.MPTextFile:
				LCD4linux.MPTextFile.value = dirdir
			elif sel == LCD4linux.MPCoverFile:
				LCD4linux.MPCoverFile.value = dirdir
			elif sel == LCD4linux.BildFile:
				LCD4linux.BildFile.value = dirdir
			elif sel == LCD4linux.Bild2File:
				LCD4linux.Bild2File.value = dirdir
			elif sel == LCD4linux.Bild3File:
				LCD4linux.Bild3File.value = dirdir
			elif sel == LCD4linux.Bild4File:
				LCD4linux.Bild4File.value = dirdir
			elif sel == LCD4linux.MPBildFile:
				LCD4linux.MPBildFile.value = dirdir
			elif sel == LCD4linux.MPBild2File:
				LCD4linux.MPBild2File.value = dirdir
			elif sel == LCD4linux.StandbyBildFile:
				LCD4linux.StandbyBildFile.value = dirdir
			elif sel == LCD4linux.StandbyBild2File:
				LCD4linux.StandbyBild2File.value = dirdir
			elif sel == LCD4linux.StandbyBild3File:
				LCD4linux.StandbyBild3File.value = dirdir
			elif sel == LCD4linux.StandbyBild4File:
				LCD4linux.StandbyBild4File.value = dirdir
			elif sel == LCD4linux.StandbyTextFile:
				LCD4linux.StandbyTextFile.value = dirdir
			elif sel == LCD4linux.StandbyText2File:
				LCD4linux.StandbyText2File.value = dirdir
			elif sel == LCD4linux.StandbyText3File:
				LCD4linux.StandbyText3File.value = dirdir
			elif sel == LCD4linux.FritzFrame:
				LCD4linux.FritzFrame.value = dirdir
			elif sel == LCD4linux.RecordingPath:
				LCD4linux.RecordingPath.value = dirdir
			elif sel == LCD4linux.Font:
				if dirdir.endswith(".ttf") and os.path.isfile(dirdir):
					LCD4linux.Font.value = dirdir
					FONT = dirdir
			elif sel == LCD4linux.Font1:
				if dirdir.endswith(".ttf") and os.path.isfile(dirdir):
					LCD4linux.Font1.value = dirdir
			elif sel == LCD4linux.Font2:
				if dirdir.endswith(".ttf") and os.path.isfile(dirdir):
					LCD4linux.Font2.value = dirdir
			elif sel == LCD4linux.Font3:
				if dirdir.endswith(".ttf") and os.path.isfile(dirdir):
					LCD4linux.Font3.value = dirdir
		if dir+dir1 != "" and dir1.endswith("/"):
			dir1 = dir1[:-1]
			if sel == LCD4linux.BildFile:
				LCD4linux.BildFile.value = dir1
			elif sel == LCD4linux.MPBildFile:
				LCD4linux.MPBildFile.value = dir1
			elif sel == LCD4linux.StandbyBildFile:
				LCD4linux.StandbyBildFile.value = dir1
			elif sel == LCD4linux.Bild2File:
				LCD4linux.Bild2File.value = dir1
			elif sel == LCD4linux.MPBild2File:
				LCD4linux.MPBild2File.value = dir1
			elif sel == LCD4linux.StandbyBild2File:
				LCD4linux.StandbyBild2File.value = dir1
			elif sel == LCD4linux.Bild3File:
				LCD4linux.Bild3File.value = dir1
			elif sel == LCD4linux.StandbyBild3File:
				LCD4linux.StandbyBild3File.value = dir1

	def selectionChanged(self):
		global ConfigStandby
		global wwwWetter
		global wwwMeteo
		global ScreenActive
		global isMediaPlayer
		global TVrunning
		L4log("select",self["config"].getCurrent()[0])
#		self.showpic()
#		print "--------", self.getCurrentValue()
#		print "--------", self["config"].getCurrent()[0]
#		sel = self["config"].getCurrent()[1]
		self.Aktuell = self["config"].getCurrent()[0]
		self.LastSelect = str(self["config"].getCurrentIndex()) + self.getCurrentValue()[:3]
		self["introduction"].setText(_("%s - Current value: %s") % (self.mode,self.getCurrentValue()))
		if USBok == False:
			self["LibUSB"].setText("libusb!")
		else:
			self["LibUSB"].setText("")
			self["About"].setText("joergm6@IHAD") # it is not allowed to change/remove
		if self.mode == "Idle":
			ConfigStandby = True
		elif self.mode == "Media":
			isMediaPlayer = "config"
		else:
			ConfigStandby = False
			isMediaPlayer = ""
		if LCD4linux.PiconPath.value == LCD4linux.PiconCache.value:
			LCD4linux.PiconCache.value = ""
		if LCD4linux.Picon2Path.value == LCD4linux.Picon2Cache.value:
			LCD4linux.Picon2Cache.value = ""
		if self.SavePiconSize != LCD4linux.PiconSize.value or self.SavePiconFullScreen != LCD4linux.PiconFullScreen.value or self.SavePiconTransparenz != LCD4linux.PiconTransparenz.value:
			self.SavePiconSize = LCD4linux.PiconSize.value
			self.SavePiconFullScreen = LCD4linux.PiconFullScreen.value
			self.SavePiconTransparenz = LCD4linux.PiconTransparenz.value
			if len(LCD4linux.PiconCache.value)>2:
				rmFiles(LCD4linux.PiconCache.value + "*.png")
		if LCD4linux.Picon2Size.isChanged() or LCD4linux.Picon2FullScreen.isChanged() or LCD4linux.PiconTransparenz.isChanged():
			if len(LCD4linux.Picon2Cache.value)>2:
				rmFiles(LCD4linux.Picon2Cache.value + "*.png")
		if self.SaveWetter != LCD4linux.WetterCity.value or self.SaveWetter2 != LCD4linux.Wetter2City.value:
			self.SaveWetter = LCD4linux.WetterCity.value
			self.SaveWetter2 = LCD4linux.Wetter2City.value
			resetWetter()
		if LCD4linux.WetterIconZoom.isChanged() or LCD4linux.WetterRain.isChanged() or LCD4linux.WetterRainZoom.isChanged() or LCD4linux.WetterRainColor.isChanged() or LCD4linux.WetterRainColor2.isChanged() or LCD4linux.WetterRainColor2use.isChanged() or LCD4linux.WetterLine.isChanged() or LCD4linux.WetterExtra.isChanged() or LCD4linux.WetterExtraColorFeel.isChanged() or LCD4linux.WetterExtraColorCity.isChanged() or LCD4linux.WetterExtraZoom.isChanged() or LCD4linux.WetterExtraFeel.isChanged() or LCD4linux.WetterLowColor.isChanged() or LCD4linux.WetterHighColor.isChanged() or LCD4linux.WetterTransparenz.isChanged():
			rmFile(PICwetter % "0")
			rmFile(PICwetter % "1")
		if LCD4linux.WetterZoom.isChanged() or LCD4linux.StandbyWetterZoom.isChanged() or LCD4linux.MPWetterZoom.isChanged() or LCD4linux.WetterType.isChanged() or LCD4linux.StandbyWetterType.isChanged() or LCD4linux.MPWetterType.isChanged() or LCD4linux.WetterColor.isChanged() or LCD4linux.StandbyWetterColor.isChanged() or LCD4linux.MPWetterColor.isChanged() or LCD4linux.WetterFont.isChanged() or LCD4linux.MPWetterFont.isChanged() or LCD4linux.StandbyWetterFont.isChanged() or LCD4linux.WetterShadow.isChanged() or LCD4linux.StandbyWetterShadow.isChanged() or LCD4linux.MPWetterShadow.isChanged():
			rmFile(PICwetter % "0")
		if LCD4linux.Wetter2Zoom.isChanged() or LCD4linux.StandbyWetter2Zoom.isChanged() or LCD4linux.MPWetter2Zoom.isChanged() or LCD4linux.Wetter2Type.isChanged() or LCD4linux.StandbyWetter2Type.isChanged() or LCD4linux.MPWetter2Type.isChanged() or LCD4linux.Wetter2Color.isChanged() or LCD4linux.StandbyWetter2Color.isChanged() or LCD4linux.MPWetterColor.isChanged() or LCD4linux.Wetter2Font.isChanged() or LCD4linux.MPWetter2Font.isChanged() or LCD4linux.StandbyWetter2Font.isChanged() or LCD4linux.Wetter2Shadow.isChanged() or LCD4linux.StandbyWetter2Shadow.isChanged() or LCD4linux.MPWetter2Shadow.isChanged():
			rmFile(PICwetter % "1")
		if self.SaveMeteo != LCD4linux.MeteoURL.value:
			self.SaveMeteo = LCD4linux.MeteoURL.value
			wwwMeteo = ""
		if self.SaveMeteoZoom != LCD4linux.MeteoZoom.value or self.SaveStandbyMeteoZoom != LCD4linux.StandbyMeteoZoom.value or self.SaveMeteoType != LCD4linux.MeteoType.value or self.SaveStandbyMeteoType != LCD4linux.StandbyMeteoType.value:
			self.SaveMeteoType = LCD4linux.MeteoType.value
			self.SaveMeteoZoom = LCD4linux.MeteoZoom.value
			self.SaveStandbyMeteoType = LCD4linux.StandbyMeteoType.value
			self.SaveStandbyMeteoZoom = LCD4linux.StandbyMeteoZoom.value
			rmFile(PICmeteo)
		if self.SaveScreenActive != LCD4linux.ScreenActive.value:
			self.SaveScreenActive = LCD4linux.ScreenActive.value
			ScreenActive[0] = self.SaveScreenActive
		if LCD4linux.BildFile.isChanged() or LCD4linux.StandbyBildFile.isChanged() or LCD4linux.Bild2File.isChanged() or LCD4linux.StandbyBild2File.isChanged() or LCD4linux.Bild3File.isChanged() or LCD4linux.StandbyBild3File.isChanged() or LCD4linux.MPBildFile.isChanged() or LCD4linux.MPBild2File.isChanged():
			getBilder()
		if LCD4linux.FritzPictures.isChanged() or LCD4linux.FritzPictureType.isChanged() or LCD4linux.FritzPicSize.isChanged() or LCD4linux.MPFritzPicSize.isChanged() or LCD4linux.StandbyFritzPicSize.isChanged():
			rmFile(PICfritz)
		if LCD4linux.CalLayout.isChanged() or LCD4linux.CalColor.isChanged() or LCD4linux.CalBackColor.isChanged() or LCD4linux.CalCaptionColor.isChanged() or LCD4linux.CalPathColor.isChanged() or LCD4linux.CalHttpColor.isChanged() or LCD4linux.CalHttp2Color.isChanged() or LCD4linux.CalHttp3Color.isChanged() or LCD4linux.CalLine.isChanged() or LCD4linux.CalDays.isChanged():
			rmFile(PICcal)
		if LCD4linux.MPCalLayout.isChanged() or LCD4linux.MPCalColor.isChanged() or LCD4linux.MPCalBackColor.isChanged() or LCD4linux.MPCalCaptionColor.isChanged() or LCD4linux.StandbyCalLayout.isChanged() or LCD4linux.StandbyCalColor.isChanged() or LCD4linux.StandbyCalBackColor.isChanged() or LCD4linux.StandbyCalCaptionColor.isChanged() or LCD4linux.CalShadow.isChanged() or LCD4linux.StandbyCalShadow.isChanged() or LCD4linux.MPCalShadow.isChanged():
			rmFile(PICcal)
		if LCD4linux.WWW1url.isChanged() or LCD4linux.StandbyWWW1url.isChanged():
			self.WWWischanged = True
		if self.SavePicture != LCD4linux.SavePicture.value:
			rmFiles(PIC + "*.*")
			self.SavePicture = LCD4linux.SavePicture.value
#		if LCD4linux.CalPath.isChanged() or LCD4linux.CalHttp.isChanged() or LCD4linux.CalHttp2.isChanged() or LCD4linux.CalHttp3.isChanged():
#			if Briefkasten.qsize()<=3:
#				Briefkasten.put(4) 
#			else:
#				L4log("Queue full, Thread hanging?")
		if LCD4linux.TV.value == False:
			TVrunning == False
		if LCD4linux.xmlLCDType.isChanged():
			xmlRead()
			if xmlDelete(1) or xmlDelete(2) or xmlDelete(3):
				L4log("removed old Skindata")
				xmlWrite()
			xmlClear()
#		if LCD4linux.LCDType1.isChanged() or LCD4linux.LCDType2.isChanged():
#			TFTCheck(False)
		return

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def LCDrestart(self):
		global SamsungDevice
		global SamsungDevice2
		global SamsungDevice3
		if USBok == True:
			dpf.close(SamsungDevice)
			dpf.close(SamsungDevice2)
			dpf.close(SamsungDevice3)
		SamsungDevice = None
		SamsungDevice2 = None
		SamsungDevice3 = None
		getDpfDevice()
		getSamsungDevice()
		TFTCheck(True)
		rmFile(CrashFile)
		rmFile(PICwetter % "0")
		rmFile(PICwetter % "1")
		rmFile("%stft.bmp" % TMPL)
		rmFiles(PIC + "*.*")
		if Briefkasten.qsize()<=3:
			Briefkasten.put(4) 
		else:
			L4log("Queue full, Thread hanging?")
		if Briefkasten.qsize()<=3:
			Briefkasten.put(6) 
		else:
			L4log("Queue full, Thread hanging?")

	def save(self):
		global ConfigMode
		global ConfigStandby
		global isMediaPlayer
		global DeviceRemove
		DeviceRemove = []

		self["config"].setList(self.list1)
		for x in self["config"].list:
			x[1].save()
		self["config"].setList(self.list2)
		for x in self["config"].list:
			x[1].save()
		self["config"].setList(self.list3)
		for x in self["config"].list:
			x[1].save()
		self["config"].setList(self.list4)
		for x in self["config"].list:
			x[1].save()
		ConfigMode = False
		ConfigStandby = False
		isMediaPlayer = self.SaveisMediaPlayer
#		config.saveToFile("/tmp/lcd4linux.txt")
		LCD4linux.save()
		LCD4linux.saveToFile(LCD4config)
		getBilder()
		ConfTime("LCDoff",LCD4linux.LCDoff.value)
		ConfTime("LCDon",LCD4linux.LCDon.value)
		ConfTime("StandbyLCDoff",LCD4linux.StandbyLCDoff.value)
		ConfTime("StandbyLCDon",LCD4linux.StandbyLCDon.value)
		ConfTime("LCDWEoff",LCD4linux.LCDWEoff.value)
		ConfTime("LCDWEon",LCD4linux.LCDWEon.value)
		ConfTime("StandbyLCDWEoff",LCD4linux.StandbyLCDWEoff.value)
		ConfTime("StandbyLCDWEon",LCD4linux.StandbyLCDWEon.value)
		TFTCheck(False)
		if LCD4linux.LCDType1.value[0] == "5" or LCD4linux.LCDType2.value[0] == "5" or LCD4linux.LCDType3.value[0] == "5":
			if xmlSkin():
				configfile.save()
				xmlWrite()
				restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply the changes.\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO, default = False)
				restartbox.setTitle(_("Restart GUI now?"))
			else:
				self.close(True,self.session)
			xmlClear()
		else:
			self.close(True,self.session)
		Briefkasten.put(4)
		if self.WWWischanged == True:
			getWWW()

	def cancel(self):
		global ConfigMode
		global ConfigStandby
		global isMediaPlayer
		self["config"].setList(self.list1)
		for x in self["config"].list:
			x[1].cancel()
		self["config"].setList(self.list2)
		for x in self["config"].list:
			x[1].cancel()
		self["config"].setList(self.list3)
		for x in self["config"].list:
			x[1].cancel()
		self["config"].setList(self.list4)
		for x in self["config"].list:
			x[1].cancel()
		self.close(True,self.session)
		ConfigMode = False
		ConfigStandby = False
		isMediaPlayer = self.SaveisMediaPlayer
		TFTCheck(False)

	def keyLeft(self):
		L4logE("key L")
		self.LastSelect = str(self["config"].getCurrentIndex()) + self.getCurrentValue()[:3]
		ConfigListScreen.keyLeft(self)
		self.SetList()

	def keyRight(self):
		L4logE("key R")
		self.LastSelect = str(self["config"].getCurrentIndex()) + self.getCurrentValue()[:3]
		ConfigListScreen.keyRight(self)
		self.SetList()

	def KeyUp(self):
		self.LastSelect=str(self["config"].getCurrentIndex())
		L4logE("key U")
		if self["config"].getCurrentIndex() - self.ConfLines > 0:
			self["config"].setCurrentIndex(self["config"].getCurrentIndex() - self.ConfLines)
		else:
			self["config"].setCurrentIndex(0)

	def KeyDown(self):
		self.LastSelect=str(self["config"].getCurrentIndex())
		L4logE("key D")
		if self["config"].getCurrentIndex() + self.ConfLines <= (len(self["config"].getList()) - 1):
			self["config"].setCurrentIndex(self["config"].getCurrentIndex() + self.ConfLines)
		else:
			self["config"].setCurrentIndex((len(self["config"].getList()) - 1))

	def restartGUI(self, answer):
		if answer is True:
			L4log("GUI Restart")
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close(True,self.session)
#			self.close()

class UpdateStatus(Screen):

	def __init__(self, session):
		global ScreenActive
		Screen.__init__(self, session)

		ScreenActive[0] = LCD4linux.ScreenActive.value
		self.ServiceChangeRunning = False
		self.SaveTXTfile = 0
		self.SaveMPTXTfile = 0
		self.SaveBildfile = 0
		self.SaveStandbyBildfile = 0
		self.SaveStandbyTXTfile = 0
		self.KeyDoppel = 0
		self.KeyTime = 0
		self.StandbyChanged = False
		self.DataMinute = ""
		self.l4l_info = {}
		self.Ltimer_list = []
		self.LgetGoogleCover = None
		self.LisRecording = None
		self.LEventsNext = None
		self.LEventsDesc = None
		self.Ltuner_number = None
		self.Lvol = None
		self.ref = None
		self.LsreftoString = None
		self.Lchannel_name = None
		self.Lpath = None
		self.Lchannel_num = ""
		self.Llength = None
		self.Lposition = None
		self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0 =0,0,0,""
		self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1 =0,0,0,""
		self.Lprovider = None
		self.LtransponderData = None
		self.LsVideoWidth = None
		self.LsVideoHeight = None
		self.LsIsCrypted = None
		self.LsAspect = None
		self.LsTagAlbum = None
		self.LsTagTitle = None
		self.LsTagArtist = None
		self.LsTagGenre = None
		self.LaudioTracks = None
		self.LaudioCurrentTrack = None
		self.Laudiodescription = None
		self.LsignalQuality = None
		self.LsignalQualitydB = None
		self.LbitErrorRate = None
		self.LShortDescription = None
		self.LExtendedDescription = None
		self.LgetName = None
		self.LvideoBitrate = ""
		self.LaudioBitrate = ""
		self.videoBitrate = None
		self.audioBitrate = None
		self.iT="0.0"
		self.iH="0"
		self.iP="0"
		self.iN="0"
		self.iC="0"
		self.iIDX="0"
		self.oM=[]
		self.TEMPERATURE="C"
		self.HUMIDITY="%"
		self.CO2="ppm"
		self.PRESSURE="mbar"
		self.NOISE="db"
		self.oldTitle = ""
		self.CoverCount = 0
		self.TunerCallBack=False
		self.WetterOK=False
		self.TimeZone = "0"
		self.Long = ""
		self.Lat = "0"
		self.WDay=[{},{}]
		self.WWeek=[[],[]]

		self.NetworkConnectionAvailable = False
		try:
			iNetwork.checkNetworkState(self.checkNetworkCB)
		except:
			self.NetworkConnectionAvailable = None
			L4log("iNetwork-Error, Check disable")

		self.StatusTimer = eTimer()
		self.StatusTimer.callback.append(self.updateStatus)
		
		self.ServiceTimer = eTimer()
		self.ServiceTimer.callback.append(self.ServiceChange)

		self.SamsungTimer = eTimer()
		self.SamsungTimer.callback.append(self.SamsungStart)

		self.DpfTimer = eTimer()
		self.DpfTimer.callback.append(self.DpfStart)

		self.QuickTimer = eTimer()
		self.QuickTimer.callback.append(self.QuickBildTimer)

		self.CheckRefresh = eTimer()
		self.CheckRefresh.callback.append(self.CallCheckRefresh)

		if BitrateRegistred == True:
			self.BitrateTimer = eTimer()
			self.BitrateTimer.callback.append(self.runBitrateTimer)
			self.BitrateTimer.startLongTimer(30)

		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evUpdatedInfo: self.restartTimer,
				iPlayableService.evUpdatedEventInfo: self.restartTimer
#				iPlayableService.evSeekableStatusChanged: self.restartTimer,
#				iPlayableService.evVideoProgressiveChanged: self.restartTimer,
#				iPlayableService.evUser: self.restartTimer
			})

		eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.rcKeyPressed)
		self.recordtimer = session.nav.RecordTimer
		self.LastTimerlistUpdate = 0
		if LCD4linux.StandbyWetter.value != "0" or LCD4linux.Wetter.value != "0" or LCD4linux.MPWetter.value != "0":
			self.downloadWetter(LCD4linux.WetterCity.value,0)
		if LCD4linux.StandbyWetter2.value != "0" or LCD4linux.Wetter2.value != "0" or LCD4linux.MPWetter2.value != "0":
			self.downloadWetter(LCD4linux.Wetter2City.value,1)
		if LCD4linux.StandbyMeteo.value != "0" or LCD4linux.Meteo.value != "0":
			self.downloadMeteo()
		self.timerlist = ""
		self.pluginlist = ""

#####		self.onShow.append(self.ServiceChange)
#		config.misc.standbyCounter.addNotifier(self.restartTimer(self), initial_call = False)
		getBilder()
		self.StatusTimer.startLongTimer(int(LCD4linux.FastMode.value))
		self.QuickTimer.start(int(LCD4linux.BilderQuick.value),True)
		self.CheckRefresh.start(500,True)
		self.SamsungStart()
		self.DpfStart()
		self.onTunerCount()
		L4LthreadsLCD = [L4LWorkerLCD(i,self,session) for i in range(1)] 
		for thread in L4LthreadsLCD: 
			thread.setDaemon(True) 
			thread.start() 
		L4Lthreads = [L4LWorker(i,self,session) for i in range(1)] 
		for thread in L4Lthreads: 
			thread.setDaemon(True) 
			thread.start() 
		L4Lthreads1 = [L4LWorker1(i,self,session) for i in range(int(LCD4linux.ElementThreads.value))] 
		for thread in L4Lthreads1: 
			thread.setDaemon(True) 
			thread.start() 
		L4Lthreads2 = [L4LWorker2(i,self,session) for i in range(int(LCD4linux.ElementThreads.value))] 
		for thread in L4Lthreads2: 
			thread.setDaemon(True) 
			thread.start() 
		L4Lthreads3 = [L4LWorker3(i,self,session) for i in range(int(LCD4linux.ElementThreads.value))] 
		for thread in L4Lthreads3: 
			thread.setDaemon(True) 
			thread.start() 
		if LCD4linux.WebIfInitDelay.value == True:
			Briefkasten.put(5)

	def onTunerCount(self):
		global TunerCount
		TunerCount = 0
		for slot in range(nimmanager.getSlotCount()):
			if nimmanager.getNimType(slot) is not None:
				TunerCount += 1
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.TunerCallBack=True
			res_mgr.frontendUseMaskChanged.get().append(self.tunerUseMaskChanged)
		else:
			print "[ERROR]no res_mgr!!"
			
	def offTunerCount(self):
		if self.TunerCallBack:
			res_mgr = eDVBResourceManager.getInstance()
			if res_mgr:
				self.TunerCallBack=False
				res_mgr.frontendUseMaskChanged.get().remove(self.tunerUseMaskChanged)
			else:
				print "[ERROR]no res_mgr!!"
			
	def tunerUseMaskChanged(self, mask):
		global TunerMask
		TunerMask = mask
	
	def QuickBildTimer(self):
		self.QuickTimer.stop()
		if Briefkasten.qsize()<=3:
			Briefkasten.put(7) 
		else:
			L4log("Queue full, Thread hanging?")
		self.QuickTimer.start(int(LCD4linux.BilderQuick.value),True)

	def CallCheckRefresh(self):
		global SaveEventListChanged
		self.CheckRefresh.stop()
		if L4LElist.getRefresh() == True:
			L4logE("external Refresh")
			if L4LElist.getScreen() != "":
				SaveEventListChanged = L4LElist.getHold()
				setScreenActive(str(L4LElist.getScreen()),str(L4LElist.getLcd()))
				L4LElist.setScreen("")
				L4LElist.setHold(False)
			L4LElist.resetRefresh()
			self.restartTimer()
		self.CheckRefresh.start(500,True)

	def getNetatmo(self):
		if NetatmoOK==True:
			if len(netatmo.stations)>0:
				L4log("getNetatmo")
				self.iT=str(netatmo.stations[0].indoor.temperature)+".0"
				if len(self.iT.split(".")[0])<2:
					self.iT = " " + self.iT
				self.iH=str(netatmo.stations[0].indoor.humidity)
				self.iP=str(netatmo.stations[0].indoor.pressure)
				self.iN=str(netatmo.stations[0].indoor.noise)
				self.iC=str(netatmo.stations[0].indoor.co2)
				try:
					self.iIDX = str(netatmo.stations[0].indoor.idx_total)
				except:
					L4log("please use newer Netatmo-Plugin")
				self.oM=[]
				for Mod in netatmo.stations[0].modules:
					oT=str(Mod.outdoor.temperature)+".0"
					if len(oT.split(".")[0])<2:
						oT = " " + oT
					self.oM.append([oT,str(Mod.outdoor.humidity)])

				self.TEMPERATURE=netatmo.getUint(NetatmoUnit.TEMPERATURE)
				self.HUMIDITY=netatmo.getUint(NetatmoUnit.HUMIDITY)
				self.CO2=netatmo.getUint(NetatmoUnit.CO2)
				self.PRESSURE=netatmo.getUint(NetatmoUnit.PRESSURE)
				self.NOISE=netatmo.getUint(NetatmoUnit.NOISE)

	def updateStatus(self):
#		print "[LCD4linux] update"
		global DeviceRemove
		global BilderTime
		global OSDtimer
		global OSDon
		global isVideoPlaying
		global ScreenActive
		global ScreenTime
		global ThreadRunning
		global FritzTime
		self.StatusTimer.stop()
		if not LCD4linux.Enable.value or ThreadRunning > 0:
			if ThreadRunning > 0:
				ThreadRunning+= 1
				if ThreadRunning > 40:
					ThreadRunning = 0
				L4log("Thread already running.....")
			self.StatusTimer.startLongTimer(int(LCD4linux.FastMode.value))
			return
		tt = time()
		L4logE("Update...Qlen=",Briefkasten.qsize())
		if self.LgetGoogleCover is not None:
			self.getGoogleCover(self.LgetGoogleCover[0],self.LgetGoogleCover[1],self.LgetGoogleCover[2])
		if FritzTime > 0:
			FritzTime-=1
		SaveScreenActive = ScreenActive[0]
#		print "Desktop",getDesktop(0).size().width()
		if LCD4linux.Text.value != "0":
			if os.path.isfile(LCD4linux.TextFile.value):
				try:
					if self.SaveTXTfile != os.path.getmtime(LCD4linux.TextFile.value):
						self.SaveTXTfile = os.path.getmtime(LCD4linux.TextFile.value)
						self.restartTimer()
				except:
					pass
		if LCD4linux.StandbyText.value != "0":
			if os.path.isfile(LCD4linux.StandbyTextFile.value):
				try:
					if self.SaveStandbyTXTfile != os.path.getmtime(LCD4linux.StandbyTextFile.value):
						self.SaveStandbyTXTfile = os.path.getmtime(LCD4linux.StandbyTextFile.value)
						self.restartTimer()
				except:
					pass
		if LCD4linux.MPText.value != "0":
			if os.path.isfile(LCD4linux.MPTextFile.value):
				try:
					if self.SaveMPTXTfile != os.path.getmtime(LCD4linux.MPTextFile.value):
						self.SaveMPTXTfile = os.path.getmtime(LCD4linux.MPTextFile.value)
						self.restartTimer()
				except:
					pass
		if LCD4linux.Bild.value != "0":
			if os.path.isfile(LCD4linux.BildFile.value):
				try:
					if self.SaveBildfile != os.path.getmtime(LCD4linux.BildFile.value):
						self.SaveBildfile = os.path.getmtime(LCD4linux.BildFile.value)
						self.restartTimer()
				except:
					pass
			else:
				if self.SaveBildfile != 0:
					self.SaveBildfile = 0
					self.restartTimer()
		if LCD4linux.StandbyBild.value != "0":
			if os.path.isfile(LCD4linux.StandbyBildFile.value):
				try:
					if self.SaveStandbyBildfile != os.path.getmtime(LCD4linux.StandbyBildFile.value):
						self.SaveStandbyBildfile = os.path.getmtime(LCD4linux.StandbyBildFile.value)
						self.restartTimer()
				except:
					pass
			else:
				if self.SaveStandbyBildfile != 0:
					self.SaveStandbyBildfile = 0
					self.restartTimer()
		if (LCD4linux.ScreenTime.value != "0" and not Standby.inStandby) or (LCD4linux.StandbyScreenTime.value != "0" and Standby.inStandby):
			NextScreen(False)
		elif SaveEventListChanged == False:
			ScreenActive[0] = LCD4linux.ScreenActive.value

		if LCD4linux.BilderTime.value != "0":
			if BilderTime >= int(LCD4linux.BilderTime.value):
				BilderTime=0
			BilderTime += 1
		if OSDtimer < 0:
			OSDon = 0
			OSDtimer += 1
			if OSDtimer == 0:
				if Briefkasten.qsize()<=3:
					Briefkasten.put(6) 
				else:
					L4log("Queue full, Thread hanging?")
				if LCD4linux.Cal.value != "0" or LCD4linux.StandbyCal.value != "0" or LCD4linux.MPCal.value != "0" or LCD4linux.CalList.value != "0" or LCD4linux.MPCalList.value != "0" or LCD4linux.StandbyCalList.value != "0":
					if Briefkasten.qsize()<=3:
						Briefkasten.put(4) 
					else:
						L4log("Queue full, Thread hanging?")
				self.getNetatmo()
				getWWW()
		if LCD4linux.OSD.value != "0":
			if OSDon >= 2:
				if OSDtimer >= int(LCD4linux.OSD.value):
					OSDtimer = 0
					OSDon = 1
				OSDtimer += 1
		if isVideoPlaying !=0:
			isVideoPlaying+=1
#		print "----",LCD4linuxPIC.TimeZone, LCD4linuxPIC.Long, LCD4linuxPIC.Lat
#		print "--------",isVideoPlaying, isMediaPlayer, ConfigMode, ScreenActive[0]
#		print "[LCD4linux]",strftime("%M"),BilderTime,ConfigMode,"#",ScreenActive[0],SaveScreenActive,"#",isVideoPlaying,OSDon,FritzTime
		if strftime("%M")!=self.DataMinute or BilderTime == 1 or self.StandbyChanged != Standby.inStandby or ConfigMode or (ScreenActive[0] != SaveScreenActive) or isVideoPlaying > 3 or OSDon == 3 or FritzTime > 0:
			L4log("Data-Build")
			isVideoPlaying = 0
			if strftime("%M")!=self.DataMinute:
				if int(strftime("%M")) % 10 == 0:
					self.getNetatmo()
				if LCD4linux.StandbyWetter.value != "0" or LCD4linux.Wetter.value != "0" or LCD4linux.MPWetter.value != "0":
					if strftime("%M") in ("35","40","55") or wwwWetter[0].find("forecast") < 1:
						self.downloadWetter(LCD4linux.WetterCity.value,0)
					if self.Long == "" and wwwWetter[0].find("forecast") > 1:
						self.downloadSunrise()
				if LCD4linux.StandbyWetter2.value != "0" or LCD4linux.Wetter2.value != "0" or LCD4linux.MPWetter2.value != "0":
					if strftime("%M") in ("35","40","55") or wwwWetter[1].find("forecast") < 1:
						self.downloadWetter(LCD4linux.Wetter2City.value,1)
				if strftime("%M") in LCD4linux.MailTime.value:
					if Briefkasten.qsize()<=3:
						Briefkasten.put(6) 
					else:
						L4log("Queue full, Thread hanging?")
				if strftime("%M") in LCD4linux.CalTime.value:
					if LCD4linux.Cal.value != "0" or LCD4linux.StandbyCal.value != "0" or LCD4linux.MPCal.value != "0" or LCD4linux.CalList.value != "0" or LCD4linux.MPCalList.value != "0" or LCD4linux.StandbyCalList.value != "0":
						if Briefkasten.qsize()<=3:
							Briefkasten.put(4) 
						else:
							L4log("Queue full, Thread hanging?")
				if strftime("%M") == "30":
					DeviceRemove = []
					try:
						if len(FritzList)>0:
							for x in range(len(FritzList)):
								if len(FritzList[0][1])>1:
									td = datetime.now() - datetime.strptime(FritzList[0][1], "%d.%m.%y %H:%M:%S")
									if td > timedelta(hours=int(LCD4linux.FritzRemove.value)):
										L4log("Remove FritzCall", FritzList[0])
										del FritzList[0]
										rmFile(PICfritz)
					except:
						L4log("Error: Remove FritzCall", FritzList)
					if self.NetworkConnectionAvailable is not None:
						L4log("check Network...")
						iNetwork.checkNetworkState(self.checkNetworkCB)
				if LCD4linux.StandbyMeteo.value != "0" or LCD4linux.Meteo.value != "0":
					if divmod(int(strftime("%M")),5)[1] == 0 or wwwMeteo.find("current_conditions") < 1:
						self.downloadMeteo()
				if LCD4linux.LCDType1.value[0] == "1" or LCD4linux.LCDType2.value[0] == "1" or LCD4linux.LCDType3.value[0] == "1":
					if DpfCheck():
						self.DpfStart()
					else:
						DpfCheckSerial()
				if LCD4linux.LCDType1.value[0] == "2" or LCD4linux.LCDType2.value[0] == "2" or LCD4linux.LCDType3.value[0] == "2":
					if SamsungCheck():
						self.SamsungStart()
				if strftime("%M") in LCD4linux.WWWTime.value:
					getWWW()
			self.DataMinute = strftime("%M")
			if self.StandbyChanged != Standby.inStandby:
				ScreenActive = ["1","","",""]
				LCD4linux.ScreenActive.value = ScreenActive[0]
				ScreenTime = 0
				getBilder()
				rmFile(PICfritz)
				getWWW()
			self.StandbyChanged = Standby.inStandby 
			self.restartTimer()
		if ConfigMode == True:
			self.StatusTimer.startLongTimer(2)
		else:
			self.StatusTimer.startLongTimer(int(LCD4linux.FastMode.value))
		L4logE("UpdateTime:", time() - tt)

	def restartTimer(self):
		global OSDon
		if not LCD4linux.Enable.value:
			return
		self.ServiceTimer.stop()
		if (OSDon == 2 and LCD4linux.OSDfast.value == False) or ThreadRunning > 0:
			self.ServiceTimer.start(LCD4linux.Delay.value+500, True)
		else:
			self.ServiceTimer.start(LCD4linux.Delay.value, True)

	def ServiceChange(self):
		global ThreadRunning
		if self.ServiceChangeRunning == True:
			L4logE("Service Change running....")
			self.restartTimer()
			return
		self.ServiceChangeRunning = True
		tt = time()
		L4logE("Event Service Change")
		volctrl = eDVBVolumecontrol.getInstance()
		if volctrl:
			self.Lvol = volctrl.getVolume()
		else:
			self.Lvol = None
		self.Ltimer_list = self.recordtimer.timer_list
		self.LisRecording = self.session.nav.RecordTimer.isRecording()
#		print("E2DataTime 1:", time() - tt)
		sref = self.session.nav.getCurrentlyPlayingServiceReference()
		if sref is not None:
			self.LsreftoString = sref.toString()
			ref = eServiceReference(self.LsreftoString)
			self.Lpath = sref.getPath()
			if not self.Lpath:
				self.Lchannel_num = str(getNumber(ref))
			elif WebRadioFSok == True:
				self.l4l_info = WebRadioFS.get_l4l_info()
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(ref)
			if info is not None:
				self.Lchannel_name = info and Code_utf8(info.getName(ref))
			self.Lprovider = None
			self.LtransponderData = None
			self.LsVideoWidth = None
			self.LsVideoHeight = None
			self.LsIsCrypted = None
			self.LsAspect = None
			self.LsTagAlbum = None
			self.LsTagTitle = None
			self.LsTagArtist = None
			self.LsTagGenre = None
			self.LsignalQuality = None
			self.LsignalQualitydB = None
			self.LbitErrorRate = None
			self.LShortDescription = None
			self.LExtendedDescription = None
			self.Ltuner_number = None
			self.LaudioTracks = None
			self.LaudioCurrentTrack = None
			self.Laudiodescription = None
			self.LgetName = None
			service = self.session.nav.getCurrentService()
			if service is not None:
				if self.Lpath: # Movie
					seek = service and service.seek()
					if seek:
						self.Llength = seek.getLength()
						self.Lposition = seek.getPlayPosition()
					else:
						self.Llength = None
						self.Lposition = None

				info = service and service.info()
				if info is not None:
					if BitrateRegistred == True and (LCD4linux.Bitrate.value != "0" or LCD4linux.MPBitrate.value != "0"):
						if self.ref != self.LsreftoString:
							self.startBitrateData()
					self.LgetName = info.getName()
					if self.LsreftoString.startswith("1:"):
						self.Lprovider = info.getInfoString(iServiceInformation.sProvider)
						self.LtransponderData = info.getInfoObject(iServiceInformation.sTransponderData)
					self.LsVideoWidth = info.getInfo(iServiceInformation.sVideoWidth)
					self.LsVideoHeight = info.getInfo(iServiceInformation.sVideoHeight)
					self.LsIsCrypted = info.getInfo(iServiceInformation.sIsCrypted) 
					self.LsAspect = info.getInfo(iServiceInformation.sAspect)
					self.LsTagAlbum = info.getInfoString(iServiceInformation.sTagAlbum)
					self.LsTagTitle = info.getInfoString(iServiceInformation.sTagTitle)
					self.LsTagArtist = info.getInfoString(iServiceInformation.sTagArtist)
					self.LsTagGenre = info.getInfoString(iServiceInformation.sTagGenre)
					event = info and info.getEvent(0)
					if event:
						self.LShortDescription = event.getShortDescription()
						self.LExtendedDescription = event.getExtendedDescription()
				feinfo = service.frontendInfo()
				if feinfo is not None:
					self.LsignalQuality = feinfo.getFrontendInfo(iFrontendInformation.signalQuality)
					self.LsignalQualitydB = feinfo.getFrontendInfo(iFrontendInformation.signalQualitydB)
					if self.LsignalQualitydB > 50000:
#						status = feinfo.getFrontendStatus()
#						if status is not None:
#							self.LsignalQualitydB = status.get("tuner_signal_quality_db")
						self.LsignalQualitydB = 0
					self.LbitErrorRate = feinfo.getFrontendInfo(iFrontendInformation.bitErrorRate)
					data = feinfo and feinfo.getAll(False)
					if data:
						self.Ltuner_number = data.get("tuner_number", -1)
				audio = service.audioTracks()
				if audio:
					self.LaudioTracks = audio.getNumberOfTracks()
					self.LaudioCurrentTrack = audio.getCurrentTrack()
					if self.LaudioCurrentTrack>=0 and self.LaudioCurrentTrack is not None:	
						i = audio.getTrackInfo(self.LaudioCurrentTrack)
						self.Laudiodescription = i.getDescription()
						L4logE("Audio activ %d" % self.LaudioCurrentTrack, self.Laudiodescription)
					else:
						idx = 0
						while idx < self.LaudioTracks:
							i = audio.getTrackInfo(idx)
							self.Laudiodescription = i.getDescription()
							L4logE("Audio %d" % idx, self.Laudiodescription)
			self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0 = getServiceInfo(self,0)
			self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1 = getServiceInfo(self,1)

#			self.LEventsNext = None
			self.LEventsDesc = None
			if self.LsreftoString.startswith("4097:0") == False:
				epgcache = eEPGCache.getInstance()
				if epgcache is not None:
					self.LEventsNext = epgcache.lookupEvent(['RIBDT', (self.LsreftoString, 0, -1, 1440)])
					self.LEventsDesc = epgcache.lookupEvent(['IBDCTSERNX', (self.LsreftoString, 0, -1)])

		else:
			self.LsreftoString = None
			self.Lchannel_name = None
			self.Lpath = None
			self.Llength = None
			self.Lposition = None
			self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0 =0,0,0,""
			self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1 =0,0,0,""
			self.Lchannel_num = ""
	
#			service = self.session.nav.getCurrentService()
#			if service is not None:
##				info = self.getServiceInterface("info")
##				if info:
##					print info.getInfo(iServiceInformation.sCurrentTitle)
##					print info.getInfo(iServiceInformation.sTotalTitles)
#				info = service.info()
#				if info:
#					print "0", info.getName()
##				print service.info()
#					print self.session.nav.getCurrentlyPlayingServiceReference().toString()
#					print "1", info.getInfoString(iServiceInformation.sTagTitle)
#					print "2", info.getInfoString(iServiceInformation.sTagAlbum)
#					print "3", info.getInfoString(iServiceInformation.sTagArtist)
#					print "4", info.getInfoString(iServiceInformation.sTagGenre)
#					print "5", info.getInfoString(iServiceInformation.sTagDate)
#					print "6", info.getInfoString(iServiceInformation.sTagComment)
#					print "7", info.getInfoString(iServiceInformation.sDescription)
#					print "8", info.getInfoString(iServiceInformation.sCurrentTitle)
#					print "9", info.getInfoString(iServiceInformation.sNamespace)
#					print "A", info.getInfoString(iServiceInformation.sProvider)
#					print "B", info.getInfo(iServiceInformation.sTagTrackNumber)
#					print "b", info.getInfo(iServiceInformation.sTagTrackCount)
#					print "C", info.getInfo(iServiceInformation.sCurrentChapter)
#					print "c", info.getInfo(iServiceInformation.sTotalChapters)
#					print "D", info.getInfoString(iServiceInformation.sTagExtendedComment)
##	if servicerefstr.find("0:0:0:0:0:0:0:0:0:") is not -1 and not servicerefstr.startswith("4369:") and not servicerefstr.startswith("4097:") and not servicerefstr.startswith("4114:") and not servicerefstr.startswith("1:0:19:") and servicerefstr.startswith("1:0:") is False and not servicerefstr.endswith(".mpg") and not servicerefstr.endswith(".vob") and not servicerefstr.endswith(".avi") and not servicerefstr.endswith(".divx") and not servicerefstr.endswith(".mv4") and not servicerefstr.endswith(".mkv") and not servicerefstr.endswith(".mp4") and not servicerefstr.endswith(".ts"):

#		print("E2DataTime X:", time() - tt)
		self.ServiceChangeRunning = False
		L4logE("Service Change Time:", time() - tt)
		if L4LdoThread == True:
			if ThreadRunning > 0:
				ThreadRunning+= 1
				if ThreadRunning > 40:
					ThreadRunning = 0
				self.restartTimer()
				L4log("Thread already running")
				return
			if BriefLCD.qsize()<=2:
				BriefLCD.put(1) 
			else:
				L4log("LCD-Queue full, Thread hanging?")
		else:
			LCD4linuxPIC(self,session)

	def runBitrateTimer(self):
		self.BitrateTimer.stop()
		if BitrateRegistred == True and (LCD4linux.Bitrate.value != "0" or LCD4linux.MPBitrate.value != "0"):
			self.startBitrateData()
		self.BitrateTimer.startLongTimer(30)

	def stopBitrateData(self,TYP):
		L4logE("Bitrate Stop",TYP)
		if "V" in TYP and self.videoBitrate is not None:
			self.videoBitrate.callback.remove(self.getVideoBitrateData)
			self.videoBitrate = None
		if "A" in TYP and self.audioBitrate is not None:
			self.audioBitrate.callback.remove(self.getAudioBitrateData)
			self.audioBitrate = None

	def startBitrateData(self):
		self.stopBitrateData("AV")
		service = self.session.nav.getCurrentService()
		if service is not None:
			info = service and service.info()
			sref = self.session.nav.getCurrentlyPlayingServiceReference()
			ref = sref.toString()
			if info is not None and ref.startswith("1:0:"):
				L4logE("Bitrate Start")
				vpid = apid = -1
				vpid = info.getInfo(iServiceInformation.sVideoPID)
				apid = info.getInfo(iServiceInformation.sAudioPID)
				if vpid:
					self.videoBitrate = eBitrateCalculator(vpid, ref, 3000, 1024*1024)
					self.videoBitrate.callback.append(self.getVideoBitrateData)
				else:
					self.LvideoBitrate = ""
				if apid:
					self.audioBitrate = eBitrateCalculator(apid, ref, 3000, 64*1024)
					self.audioBitrate.callback.append(self.getAudioBitrateData)
				else:
					self.LaudioBitrate = ""
			else:
				self.LvideoBitrate = ""
				self.LaudioBitrate = ""
		else:
			self.LvideoBitrate = ""
			self.LaudioBitrate = ""

	def getVideoBitrateData(self,value, status):
		if status:
			self.LvideoBitrate = value
		else:
			self.videoBitrate = None
			self.LvideoBitrate = ""
		self.stopBitrateData("V")

	def getAudioBitrateData(self,value, status): 
		if status:
			self.LaudioBitrate = value
		else:
			self.audioBitrate = None
			self.LaudioBitrate = ""
		self.stopBitrateData("A")

	def rcKeyPressed(self, key, flag):
		global OSDon
		global OSDtimer
		global LCDon
		global ScreenTime
		global ScreenActive
		global SaveEventListChanged
		if (SaveEventListChanged == True or ScreenActive[-3:] != ["","",""]) and L4LElist.getHoldKey() == False:
			L4log("Reset Event Changed")
			SaveEventListChanged = False
			ScreenActive = ["1","","",""]
			LCD4linux.ScreenActive.value = ScreenActive[0]
			ScreenTime = 0
			self.restartTimer()
		L4logE("Key", str(key)+" "+str(flag)) # Long: flag=3 
		self.k = int(LCD4linux.KeyScreen.value[:3])
		self.ko = int(LCD4linux.KeyOff.value[:3])
		if key == 113: # MUTE
			if len(PopText[1])>2:
				setPopText("")
				self.restartTimer()
		if LCD4linux.KeySwitch.value == True:
			if flag == 3:
				if LCD4linux.KeyScreen.value[-1:] == "l" and key == self.k:
					ScreenTime = 9999
					L4logE("Restart at Scr-longkey")
					NextScreen(True)
					LCD4linux.ScreenActive.value = ScreenActive[0]
					self.restartTimer()
				elif LCD4linux.KeyOff.value[-1:] == "l" and key == self.ko:
					L4logE("Restart at Off-longkey")
					LCDon = True if LCDon == False else False
					self.restartTimer()
			else:
				if time()-self.KeyTime > 2 or (isMediaPlayer != "" and isMediaPlayer != "radio"):
					self.KeyDoppel = 0
				self.KeyTime = time()
				if self.KeyDoppel == key and flag == 0:
					self.KeyDoppel = 0
					if LCD4linux.KeyOff.value[-1:] != "l" and key == self.ko: # PREVIOUS
						LCDon = True if LCDon == False else False
						L4logE("Restart at Off-doublekey",key)
						self.restartTimer()
					elif LCD4linux.KeyScreen.value[-1:] != "l" and key == self.k: # FORWARD / INFO
						ScreenTime = 9999
						NextScreen(True)
						LCD4linux.ScreenActive.value = ScreenActive[0]
						L4logE("Restart at Scr-doublekey",key)
						self.restartTimer()
				elif flag == 0:
					self.KeyDoppel = key
					if OSDon == 2 and key == self.k:
						OSDon = 1
						OSDtimer = 1
						L4logE("Restart at key and OSD=2")
						self.restartTimer()
				if key == self.ko or key == self.k:
					if len(PopText[1])>2:
						setPopText("")
						self.restartTimer()
					return 0
		if OSDon != 0:
			L4logE("Restart at key and OSD")
			self.restartTimer()
			OSDon = 2
			OSDtimer = 0
		if ScreenActive[0] in LCD4linux.Vol.value or ScreenActive[0] in LCD4linux.MPVol.value:
			if key in [114,115]:
				L4logE("Restart at volume")
				self.restartTimer()
		return 0

	def SamsungStart(self):
		getSamsungDevice()
		if LCD4linux.LCDType1.value[0] == "2":
			if SamsungDevice is None:
				L4log("Samsung Device not found")
				self.SamsungTimer.startLongTimer(15)
			else:
				L4log("Samsung Device ok", str(SamsungDevice._ctx.backend)[13:21])
		if LCD4linux.LCDType2.value[0] == "2":
			if SamsungDevice2 is None:
				L4log("Samsung2 Device not found")
				self.SamsungTimer.startLongTimer(15)
			else:
				L4log("Samsung2 Device ok", str(SamsungDevice2._ctx.backend)[13:21])
		if LCD4linux.LCDType3.value[0] == "2":
			if SamsungDevice3 is None:
				L4log("Samsung3 Device not found")
				self.SamsungTimer.startLongTimer(15)
			else:
				L4log("Samsung3 Device ok", str(SamsungDevice3._ctx.backend)[13:21])

	def DpfStart(self):
		getDpfDevice()
		if LCD4linux.LCDType1.value[0] == "1":
			if SamsungDevice is None:
				L4log("DPF Device not found")
				self.DpfTimer.startLongTimer(15)
			else:
				L4log("DPF Device ok")
		if LCD4linux.LCDType2.value[0] == "1":
			if SamsungDevice2 is None:
				L4log("DPF2 Device not found")
				self.DpfTimer.startLongTimer(15)
			else:
				L4log("DPF2 Device ok")
		if LCD4linux.LCDType3.value[0] == "1":
			if SamsungDevice3 is None:
				L4log("DPF3 Device not found")
				self.DpfTimer.startLongTimer(15)
			else:
				L4log("DPF3 Device ok")

	def checkNetworkCB(self, data):
		if data is not None:
			if data <= 2:
				self.NetworkConnectionAvailable = True
				L4log("Network True")
			else:
				self.NetworkConnectionAvailable = False
				L4log("Network False")

	def downloadWetter(self,ort,wetter):
		if self.NetworkConnectionAvailable or self.NetworkConnectionAvailable == None:
			la = language.getLanguage().replace("_","-")
			if la.upper() in ["NO-NO","CA-AD","SR-YU","EN-EN"]:
				la = "en-us"
			if ort.startswith("wc:"):
				city=ort
				self.feedurl = "http://weather.service.msn.com/data.aspx?src=vista&weadegreetype=C&culture=%s&wealocations=%s" %(la,city) 
			else:
				city=quote(ort)
				self.feedurl = "http://weather.service.msn.com/data.aspx?src=vista&weadegreetype=C&culture=%s&weasearchstr=%s" %(la,city) 
			L4log("Wetterdownloadstart:"+city,language.getLanguage()+" "+la)
#			self.feedurl = "http://www.google.com/ig/api?weather=%s&oe=utf-8&hl=%s" % (LCD4linux.WetterCity.value,language.getLanguage()[:2])
			getPage(self.feedurl).addCallback(boundFunction(self.downloadListCallback,wetter)).addErrback(self.downloadListError)
		else:
			if self.NetworkConnectionAvailable is not None:
				L4log("Wetter check Network...")
				iNetwork.checkNetworkState(self.checkNetworkCB)

	def downloadMeteo(self):
		global wwwMeteo
		L4log("Meteodownloadstart")
		self.feedurl = LCD4linux.MeteoURL.value
		try:
			opener = urllib.FancyURLopener({})
			f = opener.open(self.feedurl)
			wwwMeteo = f.read()
		except Exception, e:
			self.session.open(MessageBox, "Error:\n" + str(e), MessageBox.TYPE_ERROR)
		rmFile(PICmeteo)

	def downloadListError(self, error=""):
		if error=="":
			L4log("Wetterdownload Error ?")
		else:
			L4log("Wetterdownload Error",str(error.getErrorMessage()))
		self.WetterOK=False
#		self.session.open(MessageBox, "Error downloading Feed:\n%s" % str(error), type=MessageBox.TYPE_ERROR)

	def downloadListCallback(self, ConfigWWW, page=""):
		global wwwWetter
		if page.find("forecast") > 1 and (page.find("skycode=\"44\"") == -1 or page.find("skycode=\"44\"") > 900 or wwwWetter[ConfigWWW]==""):
#		if page.find("forecast") > 1:
			self.WetterOK=True
			L4log("Wetter%sdownload OK" % ConfigWWW)
			wwwWetter[ConfigWWW] = page.replace('\n','')
			wwwWetter[ConfigWWW] = Code_utf8(wwwWetter[ConfigWWW])

			L4log("parse Wetter %s" % ConfigWWW)
			dom = parseString(wwwWetter[ConfigWWW])
			self.WWeek[ConfigWWW]=[]
			for curr in dom.getElementsByTagName('forecast'):
				High = curr.getAttribute("high")
				Low = curr.getAttribute("low")
				Day = curr.getAttribute("shortday")
				Icon = curr.getAttribute("skycodeday") + ".png"
				Cond = curr.getAttribute("skytextday")
				Regen = curr.getAttribute("precip")
				self.WWeek[ConfigWWW].append({"High":High,"Low":Low,"Day":Day,"Icon":Icon,"Cond":Cond,"Regen":Regen})
			self.WDay[ConfigWWW]={}
			curr=dom.getElementsByTagName("weather")
			if len(curr) != 0:
				self.WDay[ConfigWWW]["Locname"] = curr[0].getAttribute("weatherlocationname")
			curr=dom.getElementsByTagName("current")
			if len(curr) != 0:
				self.WDay[ConfigWWW]["Temp_c"] = curr[0].getAttribute("temperature") + "\xc2\xb0"
				self.WDay[ConfigWWW]["Hum"] = curr[0].getAttribute("humidity") + "%"
				self.WDay[ConfigWWW]["Wind"] = curr[0].getAttribute("winddisplay")
				if LCD4linux.WetterWind.value == "1":
					x=self.WDay[ConfigWWW]["Wind"].split()
					if len(x) == 3:
						self.WDay[ConfigWWW]["Wind"]="%.1f m/s %s" % (float(int(x[0])/3.6),x[2])
				self.WDay[ConfigWWW]["Cond"] = curr[0].getAttribute("skytext")
				self.WDay[ConfigWWW]["Icon"] = curr[0].getAttribute("skycode") + ".png"
				self.WDay[ConfigWWW]["Feel"] = curr[0].getAttribute("feelslike")
				self.WDay[ConfigWWW]["Wtime"] = curr[0].getAttribute("observationtime")[:5]
#			print self.WDay[ConfigWWW]
#			print self.WWeek[ConfigWWW]

			rmFile(PICwetter % ConfigWWW)
			if strftime("%M") in ("55"):
				self.Long = ""
		else:
			self.WetterOK=False
			L4log("Wetter%sdownload Error" % ConfigWWW)
			if page.find("skycode=\"44\"") > 0:
				L4log("Wetterdownload unavailable Current Data")

	def downloadSunrise(self):
		L4log("Sunrise...")
		dom = parseString(wwwWetter[0])
		curr=dom.getElementsByTagName("weather")
		if len(curr) != 0:
			self.TimeZone = curr[0].getAttribute("timezone")
			self.Long = curr[0].getAttribute("long")
			self.Lat = curr[0].getAttribute("lat") # LCD4linuxPIC.TimeZone
#			self.feedurl = str("http://www.earthtools.org/sun/%s/%s/%d/%d/%s/%d" % (self.Lat,self.Long,datetime.now().day,datetime.now().month,"99",localtime().tm_isdst))
			self.feedurl = str("http://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&mode=xml&cnt=1" % (self.Lat,self.Long))
			L4log("Sunrise downloadstart:",self.feedurl)
			getPage(self.feedurl).addCallback(self.downloadSunriseCallback).addErrback(self.downloadSunriseError)

	def downloadSunriseError(self, error=""):
		if error=="":
			L4log("Sunrise download Error ?")
		else:
			L4log("Sunrise download Error",str(error.getErrorMessage()))

	def downloadSunriseCallback(self, page=""):
		global L4LSun
		global L4LMoon
		L4log("Sunrise download ok")
		try:
			dom = parseString(page)
#			u = dom.getElementsByTagName("lastupdate")
#			if len(u)>0:
#				DIFF = int(strftime("%H"))-int(u[0].getAttribute("value")[-8:-6])
#			else:
#				DIFF = 0
			DIFF = getTimeDiffUTC()
			s = dom.getElementsByTagName("sun")
			if len(s)>0:
				h=int(int(s[0].getAttribute("rise")[-8:-6])+DIFF)
				m=int(s[0].getAttribute("rise")[-5:-3])
				if int(s[0].getAttribute("rise")[-2:])>=30 and m < 59:
					m += 1
				L4LSun = (h,m)
				h=int(int(s[0].getAttribute("set")[-8:-6])+DIFF)
				m=int(s[0].getAttribute("set")[-5:-3])
				if int(s[0].getAttribute("set")[-2:])>=30 and m < 59:
					m += 1
				L4LMoon = (h,m)
		except:
			L4log("Error Sunrise processing")
			from traceback import format_exc
			L4log("Error:",format_exc() )
#		d = dom.getElementsByTagName("morning")
#		if len(d) > 0:
#			c = d[0].getElementsByTagName("civil")
#			if len(c) > 0:
#				L4LSun=tuple(map(int,str(c[0].childNodes[0].data)[:5].split(":")))
#		d = dom.getElementsByTagName("evening")
#		if len(d) > 0:
#			c = d[0].getElementsByTagName("civil")
#			if len(c) > 0:
#				L4LMoon=tuple(map(int,str(c[0].childNodes[0].data)[:5].split(":")))
		L4log(L4LSun,L4LMoon)
		
	def coverDownloadFailed(self,result):
		self.CoverCount += 1
		L4log("cover download failed:",result)

	def coverDownloadFinished(self,filename, result):
		if os.path.isfile(GoogleCover):
			self.CoverCount = 0
			self.restartTimer()
			L4log("cover download finished")
		else:
			L4log("cover download finished, no file found")

	def getGoogleCover(self,artist,album,isVid):
		if artist != "" and album != "":
			if isVid==False:
				quad = ",iar:s"
				album = "cd "+album
			else:
				quad = ""
				album = "dvd "+album
			try:
				url = "http://images.google.de/images?q=%s+%s&btnG=Bilder-Suchee&tbs=isz:m%s" % (quote(Code_utf8(album).encode("latin","ignore")),quote(Code_utf8(artist).encode("latin","ignore")),quad)
				L4log("Cover Search",url)
				sendUrlCommand(url, None,10).addCallback(self.googleImageCallback).addErrback(self.coverDownloadFailed)
			except:
				L4log("Google Cover Error")
			self.LgetGoogleCover = None

	def googleImageCallback(self,result):
		foundPos = result.find("imgres?imgurl=")
		foundPos2 = result.find("&amp;imgrefurl=")
		if foundPos != -1 and foundPos2 != -1:
			url = result[foundPos+14:foundPos2]
			url = url.replace("%25","%")
			parts = url.split("/")
			filename=GoogleCover
			L4log("downloading cover from",url)
			downloadPage(url , filename).addCallback(boundFunction(self.coverDownloadFinished, filename)).addErrback(self.coverDownloadFailed)
		else:
			self.CoverCount += 1
			L4log("no downloads found")

def LCD4linuxPICThread(self,session):
	global ThreadRunning
	ThreadRunning = 1
	try:
		LCD4linuxPIC(self,session)
	except Exception:
		from traceback import format_exc
		L4log("Thread Error:",format_exc() )
		try:
			open(CrashFile,"w").write(format_exc())
		except:
			pass
	ThreadRunning = 0

def getNumber(actservice):
	# actservice must be an instance of eServiceReference
	Servicelist = None
	if InfoBar and InfoBar.instance:
		Servicelist = InfoBar.instance.servicelist
	mask = (eServiceReference.isMarker | eServiceReference.isDirectory)
	number = 0
	bouquets = Servicelist and Servicelist.getBouquetList()
	if bouquets:
		actbouquet = Servicelist.getRoot()
		serviceHandler = eServiceCenter.getInstance()
		for name, bouquet in bouquets:
			if not bouquet.valid(): #check end of list
				break
			if bouquet.flags & eServiceReference.isDirectory:
				servicelist = serviceHandler.list(bouquet)
				if not servicelist is None:
					while True:
						service = servicelist.getNext()
						if not service.valid(): #check end of list
							break
						playable = not (service.flags & mask)
						if playable:
							number += 1
						if actbouquet:
							if actbouquet == bouquet and actservice == service:
								return number
						else:
							if actservice == service:
								return number
	L4logE("no Channel - Count:", number)
	return None

def getServiceInfo(self,NowNext):
	epgcache = eEPGCache.getInstance()
	event_begin = 0
	event_end = 0
	duration = 0
	event_name = ""
	if epgcache is not None:
		sref = self.session.nav.getCurrentlyPlayingServiceReference()
		if sref is not None:
			event = epgcache.lookupEvent(['IBDCTSERNX', (sref.toString(), NowNext, -1)])
			event_begin = 0
			if event:
				if event[0][4]:
					t = event[0][1]
					duration = event[0][2]
					event_name = event[0][4]
					event_begin = t
					event_end = event_begin + duration
	if event_name == "":
		service = self.session.nav.getCurrentService()
		if service is not None:
			info = service and service.info()
			event = info and info.getEvent(NowNext)
			if event:
				event_name = event.getEventName()
				event_begin = event.getBeginTime()
				duration = event.getDuration()
				event_end = event_begin + duration
	return event_begin, event_end, duration, event_name

def getSplit(ConfigSplit,ConfigAlign,MAX_W,w):
	if int(ConfigAlign) > 9 and len(str(ConfigAlign)) < 4:
		POSX = int(ConfigAlign)
	else:
		POSX = int((MAX_W-w)/2)
		if ConfigSplit == False:
			if w > MAX_W or ConfigAlign in ["0","3"]:
				POSX = 0
			elif ConfigAlign in ["2","4"]:
				POSX = (MAX_W-w)
			elif len(str(ConfigAlign)) == 4:
				POSX = int(MAX_W*int(ConfigAlign)/10000)
		else:
			if ConfigAlign == "1":
				POSX = POSX+int(MAX_W/2)
			elif ConfigAlign == "2":
				POSX = MAX_W+POSX
			elif ConfigAlign == "3":
				POSX = 0
			elif ConfigAlign == "4":
				POSX = int(MAX_W/2)
			elif len(str(ConfigAlign)) == 4:
				POSX = int(MAX_W*int(ConfigAlign)/10000)
	return POSX

def ShadowText(draw,tx,ty,TXT,font,tCol,SHADOW):
	if SHADOW == True:
		w,h = draw.textsize(TXT, font=font)
		D = round(h/20.)
		if D == 0:
			D = 1
		elif D > 3:
			D = 3
		tx1=tx+D
		tx0=tx-D
		ty1=ty+D
		ty0=ty-D
		COL = ImageColor.colormap[tCol]
		if isinstance(COL,tuple):
			RGB = COL
		else:
			if (COL[0] == '#'):
				COL = COL[1:]
			RGB = (int(COL[:2], 16), int(COL[2:4], 16), int(COL[4:6], 16))
		ColO = draw.draw.draw_ink(RGB, "RGB")
		HLS = list(colorsys.rgb_to_hls(RGB[0]/255.,RGB[1]/255.,RGB[2]/255.))
		if HLS[1]<0.5:
			HLS[1] += 0.5
		else:
			HLS[1] -= 0.5
			if HLS[1]<0.1:
				HLS[1]=0.1
		RGB = tuple(map(lambda x: int(x*255),colorsys.hls_to_rgb(HLS[0],HLS[1],HLS[2])))
		Col = draw.draw.draw_ink(RGB, "RGB")
		mask = font.getmask(TXT, "1")
		draw.draw.draw_bitmap((tx0,ty0), mask, Col)
		draw.draw.draw_bitmap((tx1,ty1), mask, Col)
		draw.draw.draw_bitmap((tx0,ty1), mask, Col)
		draw.draw.draw_bitmap((tx1,ty0), mask, Col)
		draw.draw.draw_bitmap((tx,ty), mask, ColO)
	else:
		draw.text((tx,ty),TXT, font=font, fill=tCol)

def writeMultiline(sts,ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigAlign,ConfigSplit,draw,im,utf=True,ConfigBackColor="0",ConfigFont=FONT,Shadow=False,Width=0,PosX=-1):
	MAX_W,MAX_H = im.size
	if ConfigSplit == True:
		MAX_W = int(MAX_W/2)
	if utf == True:
		astr = Code_utf8(sts)
	else:
		astr = sts
	if astr.find(" ") > 25 or (astr.find(" ") == -1 and len(astr) > 25):
		astr = astr.replace("."," ").replace(",",", ")
	
	lines = astr.split("\n")
	if Width==0:
		W = MAX_W
	else:
		W = Width
	lists = (textwrap.TextWrapper(width=int(W*2/ConfigSize), break_long_words=False).wrap(line) for line in lines)
	body  = "\n".join("\n".join(list) for list in lists)
	para = string.split(body, '\n')
	current_h=ConfigPos
	while len(para) > int(ConfigLines):
		del para[len(para)-1]
	for line in para:
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		w,h = draw.textsize(line, font=font)
		TextSize = ConfigSize
		while w > MAX_W:
			TextSize -= 1
			font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
			w,h = draw.textsize(line, font=font)
		if PosX == -1:
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,w)
		else:
			POSX = PosX
		if ConfigBackColor != "0":
			draw.rectangle((POSX, current_h,POSX+w, current_h+h),fill=ConfigBackColor)
		ShadowText(draw,POSX,current_h,line,font,ConfigColor,Shadow)
		current_h+=h

def writeMultiline2(sts,ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigX,MAX_W,draw,im,ConfigFont=FONT,Shadow=False):
	para = sts.split("\n")

	current_h=ConfigPos
	while len(para) > int(ConfigLines):
		del para[len(para)-1]
	for line in para:
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		line=Code_utf8(line)
		w,h = draw.textsize(line, font=font)
		TextSize = ConfigSize
		while w > MAX_W:
			TextSize -= 1
			font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
			w,h = draw.textsize(line, font=font)
		POSX = getSplit(False,"1",MAX_W,w)
		ShadowText(draw,POSX+ConfigX,current_h,line,font,ConfigColor,Shadow)
		current_h+=h

def cutText(tt, draw, font, max):
	w,h = draw.textsize(tt, font=font)
	while w > max:
		tt = tt[:-1]
		w,h = draw.textsize(tt, font=font)
	return tt

def getFont(num):
	ff = [FONT,LCD4linux.Font1.value,LCD4linux.Font2.value,LCD4linux.Font3.value]
	if ff[int(num)].endswith(".ttf") and os.path.isfile(ff[int(num)]):
		return ff[int(num)]
	else:
		return FONT

def getMem():
	tot = 0
	fre = 0
	if os.path.isfile("/proc/meminfo"):
		try:
			f = open("/proc/meminfo","r")
			tot = int(f.readline().split()[1]) * 1024
			fre = int(f.readline().split()[1]) * 1024
			f.close()
		except:
			pass
	return tot,fre

class myHTTPClientFactory(HTTPClientFactory):
	def __init__(self, url, method='GET', postdata=None, headers=None,
	agent="SHOUTcast", timeout=0, cookies=None,
	followRedirect=1, lastModified=None, etag=None):
		HTTPClientFactory.__init__(self, url, method=method, postdata=postdata,
		headers=headers, agent=agent, timeout=timeout, cookies=cookies,followRedirect=followRedirect)

def sendUrlCommand(url, contextFactory=None, timeout=60, *args, **kwargs):
	scheme, host, port, path = client._parse(url)
	factory = myHTTPClientFactory(url, *args, **kwargs)
	reactor.connectTCP(host, port, factory, timeout=timeout)
	return factory.deferred

def getShowPicture(BildFile,idx):
	global OSDon
	global Bilder
	global BilderIndex
	global BilderTime
	ShowPicture = ""
	L4logE("Picturefile",BildFile)
	if "://" in BildFile:
		try:
			if "@" in BildFile:
				r = urllib.urlretrieve(BildFile, HTTPpictmp)
				L4logE("Content-Type",r[1]["content-type"])
				if r[1]["content-type"].find("image/") >=0:
					if os.path.isfile(HTTPpictmp):
						os.rename(HTTPpictmp,HTTPpic)
				r.close()
			else:
				if url2 == True:
					r = urllib2.urlopen(BildFile, timeout = 5)
				else:
					r = urllib.urlopen(BildFile)
				L4logE("Content-Type",r.info().get("content-type"))
				if r.info().get("content-type").find("image/") >=0:
					f = open(HTTPpictmp,'wb') 
					f.write(r.read()) 
					f.close() 
					if os.path.isfile(HTTPpictmp):
						os.rename(HTTPpictmp,HTTPpic)
				else:
					L4logE("Content-Type not image",BildFile)
				r.close()
		except: 
			L4log("HTTP Error",BildFile)
		finally:
			ShowPicture = HTTPpic
	else:
		if os.path.isdir(BildFile):
			if len(Bilder[idx]) > 0:
				ShowPicture = Bilder[idx][BilderIndex[idx]]
				L4log("current Picture " + ShowPicture, BilderIndex[idx])
				if BilderTime == 1: 
					BilderIndex[idx] += 1
					if BilderIndex[idx] >= len(Bilder[idx]):
						BilderIndex[idx] = 0
		else:
			ShowPicture = BildFile
			if ShowPicture.find("fritz") >= 0:
				OSDon = 1
	return ShowPicture

"""
Author: Sean B. Palmer, inamidst.com
http://inamidst.com/code/moonphase.py
"""
def MoonPosition(now=None): 
	if now is None: 
		now = datetime.now()
	diff = now - datetime(2001, 1, 1)
	days = float(diff.days) + (float(diff.seconds) / float(86400))
	lunations = float("0.20439731") + (days * float("0.03386319269"))
	return lunations % float(1)
def MoonPhase(pos): 
	index = (pos * float(8)) + float("0.5")
	index = math.floor(index)
#	print "moonphase",index
	return {
		0: _("New Moon"), 
		1: _("First Quarter"), 
		2: _("Waxing Crescent"), 
		3: _("Waxing Gibbous"), 
		4: _("Full Moon"), 
		5: _("Waning Gibbous"), 
		6: _("Waning Crescent"),
		7: _("Last Quarter")
		}[int(index) & 7]

################################################################
################################################################

def LCD4linuxPIC(self,session):
	global wwwWetter
	global wwwMeteo
	global OSDon
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	global TVrunning
	global LastService
	global ScreenActive
	global ScreenTime
	global isMediaPlayer
	global QuickList
	global QuickIM
	global INFO
	global draw,draw2,draw3
	global im,im2,im3

	def getShowCover(BildFile):
		cover = ""
		MP3title=""
		MP3artist=""
		MP3album=""
		if self.LsreftoString is not None and self.LgetName is not None:
			Title = self.LgetName
			sref = self.LsreftoString
			L4logE("Ref",sref)
			Title = os.path.splitext(Title)[0]
			Title = Title.replace("/","_").replace("&"," ").replace("+","_").replace(":","_").replace("?","_").replace("*","_")
			L4logE("Title",Title)
			sreffile = sref[sref.rfind(":")+1:]
			L4logE("sreffile",sreffile)
			if sreffile[:1]!="/":
				tsref=sref[:-len(sreffile)-1]
				tsref=tsref[tsref.rfind(":")+1:] 
				if tsref[:1]=="/":
					sreffile = tsref
					L4logE("sreffile 2.",sreffile)
			sreffile2 = os.path.splitext(sreffile)[0]
			srefdir = os.path.dirname(sreffile)
			audio = None
			if sreffile.lower().endswith(".mp3") or sreffile.lower().endswith(".flac"):
				if not os.path.isfile(MP3tmp):
					if sreffile.lower().endswith(".mp3"):
						try:
							audio = ID3(sreffile)
						except:
							audio = None
						if audio:
							apicframes = audio.getall("APIC")
							if len(apicframes) >= 1:
								coverArtFile = file(MP3tmp, 'wb')
								coverArtFile.write(apicframes[0].data)
								coverArtFile.close()
								L4logE("MP3-Inline-Cover")
						try:
							audio = MP3(sreffile, ID3 = EasyID3)
						except:
							audio = None
						if audio:
							MP3title = audio.get('title', [''])[0]
							MP3artist = audio.get('artist', [''])[0]
							MP3album = audio.get('album', [''])[0]
#							print audio.keys()
#							print audio.values()
					if sreffile.lower().endswith(".flac"):
						try:
							audio = FLAC(sreffile)
						except:
							audio = None
						if audio:
							apicframes = audio.pictures
							if len(apicframes) >= 1:
								coverArtFile = file(MP3tmp, 'wb')
								coverArtFile.write(apicframes[0].data)
								coverArtFile.close()
				if os.path.isfile(MP3tmp):
					cover = MP3tmp
				else:
					Album = self.LsTagAlbum
					if Album is not None and Album != "":
						if os.path.isfile(os.path.join(srefdir,Album+".jpg")):
							cover = os.path.join(srefdir,Album+".jpg")
					if cover == "":
						tmp = glob.glob(os.path.join(srefdir,"[Cc]over.jpg"))
						if len(tmp)>0:
							cover = tmp[0]
						else:
							tmp = glob.glob(os.path.join(srefdir,"[Ff]older.jpg"))
							if len(tmp)>0:
								cover = tmp[0]
							else:
								tmp = glob.glob(os.path.join(srefdir,"[Ff]ront.jpg"))
								if len(tmp)>0:
									cover = tmp[0]
			elif cover == "" and os.path.isdir(srefdir):
				if os.path.isfile(os.path.join(srefdir,Title+".jpg")):
					cover = os.path.join(srefdir,Title+".jpg")
				elif os.path.isfile(os.path.join(srefdir,"cover",Title+".jpg")):
					cover = os.path.join(srefdir,"cover",Title+".jpg")
				elif os.path.isfile(os.path.join(srefdir,sreffile2+".jpg")):
					cover = os.path.join(srefdir,sreffile2+".jpg")
				elif os.path.isfile(os.path.join(BildFile[0],Title+".jpg")):
					cover = os.path.join(BildFile[0],Title+".jpg")
				elif os.path.isfile(os.path.join(BildFile[1],Title+".jpg")):
					cover = os.path.join(BildFile[1],Title+".jpg")
				elif os.path.isfile(os.path.join(srefdir,sreffile+".jpg")):
					cover = os.path.join(srefdir,sreffile+".jpg")
			if cover=="" and os.path.isfile("/tmp/.cover"):
				cover = "/tmp/.cover"
			if LCD4linux.MPCoverPiconFirst.value == True:
				if cover=="" and WebRadioFSok == True and os.path.isfile(self.l4l_info.get("Logo","")):
					cover = self.l4l_info.get("Logo","")
			if cover=="" and os.path.isfile("/tmp/.wbrfs_pic"):
				cover = "/tmp/.wbrfs_pic"
			if LCD4linux.MPCoverPiconFirst.value == False:
				if cover=="" and WebRadioFSok == True and os.path.isfile(self.l4l_info.get("Logo","")):
					cover = self.l4l_info.get("Logo","")
			if cover=="" and isMediaPlayer=="record":
				if os.path.isfile(sreffile+".meta") and LCD4linux.MPCoverGoogle.value != "1":
					try:
#						fd = open(sreffile+".meta", "r")
#						ref = fd.readline().strip()
#						fd.close()
						ref = open(sreffile+".meta", "r").readline().strip()
						rr=str(""+ref)
						rr=rr.split("::")[0]
						if rr[-1] != ":":
							rr+=":"
						picon = str(rr.replace(":", "_")[:-1]) + ".png"
						L4logE("Picon",picon)
						cover = os.path.join(LCD4linux.PiconPath.value,picon)
					except:
						pass
			Title = ""
			if self.LsTagTitle is not None:
				Title = self.LsTagTitle
			Video = Title.endswith(".mpg") or Title.endswith(".vob") or Title.endswith(".avi") or Title.endswith(".divx") or Title.endswith(".mv4") or Title.endswith(".mkv") or Title.endswith(".mp4") or Title.endswith(".ts")
			isVid = sreffile.endswith(".mpg") or sreffile.endswith(".vob") or sreffile.endswith(".avi") or sreffile.endswith(".divx") or sreffile.endswith(".mv4") or sreffile.endswith(".mkv") or sreffile.endswith(".mp4") or sreffile.endswith(".ts")
			if Title == "" or Video == True:
				Title = self.LgetName
				Title = Title.replace(".mpg","").replace(".vob","").replace(".avi","").replace(".divx","").replace(".mv4","").replace(".mkv","").replace(".mp4","").replace(".ts","")
			if cover=="" and os.path.isfile(GoogleCover):
				cover = GoogleCover
			if (cover=="" or (cover==GoogleCover and self.oldTitle != Title)) and LCD4linux.MPCoverGoogle.value != "0":
				rmFile(GoogleCover)
#				print "[L4L] start Download",Title
				self.oldTitle=Title
				a1=Title.find("(")
				a2=Title.rfind(")")+1
				if a1>10 and (a2>a1 or a2==0):
					if len(Title)>50 or a2==0:
						Title=Title[:a1]
					else:
						Title=Title.replace(Title[a1:a2]," ")
				if Title.find("LC")>10:
					Title=Title[:Title.find("LC")]
				if len(MP3title+MP3artist+MP3album) > 10:
					Title = " "
					if self.CoverCount > 0:
						MP3album = " "
				if (self.NetworkConnectionAvailable or self.NetworkConnectionAvailable == None) and ConfigMode == False:
					if self.CoverCount > 0:
						Ts = Title.split(" ")
						if len(Ts) > self.CoverCount:
							Title = " ".join(Ts[:-self.CoverCount])
					self.LgetGoogleCover = [Title.replace("."," ").replace("-"," ") , "%s %s %s" % (MP3title,MP3artist,MP3album),isVid]
			L4log("Cover",cover)
			if cover=="" and os.path.isfile(LCD4linux.MPCoverFile.value):
				cover = LCD4linux.MPCoverFile.value
		return cover

# MSN Wetter
	def putWetter((ConfigPos, ConfigZoom, ConfigAlign, ConfigSplit, ConfigType, ConfigColor, ConfigShadow, ConfigWWW, ConfigFont), draw, im):
		global WetterType
		global WetterZoom
		MAX_Wi,MAX_Hi = im.size
		if ConfigSplit == True:
			MAX_Wi = int(MAX_Wi/2)
		if os.path.isfile(PICwetter % ConfigWWW) and ConfigType == WetterType and ConfigZoom == WetterZoom:
			try:
				pil_image = Image.open(PICwetter % ConfigWWW)
				x,y = pil_image.size
				POSX = getSplit(ConfigSplit,ConfigAlign,MAX_Wi,x)
				if LCD4linux.WetterTransparenz.value == "true":
					im.paste(pil_image,(POSX,ConfigPos),pil_image)
				else:
					im.paste(pil_image,(POSX,ConfigPos))
			except:
				pass
		else:
			UseWetterPath = WetterPath
			if len(LCD4linux.WetterPath.value) > 2 and len(glob.glob(os.path.join(LCD4linux.WetterPath.value,"10.*")))>0:
				UseWetterPath = LCD4linux.WetterPath.value
			UseExt = "png"
			if len(glob.glob(UseWetterPath + "*.gif"))> 5:
				UseExt = "gif"
			L4log("Wetter Picon used:",UseWetterPath + " " + UseExt)
			WetterType=ConfigType
			WetterZoom=ConfigZoom
			POSX, POSY = 1,0
			Wmulti = ConfigZoom/10.0
			if ConfigType[0] == "2":
				MAX_H = int(175*Wmulti)
			elif ConfigType[0] == "4":
				MAX_H = int(25*Wmulti)
			elif ConfigType == "5":
				MAX_H = int(54*6*Wmulti)
			elif ConfigType == "51":
				MAX_H = int(54*7*Wmulti)
			else:
				MAX_H = int(80*Wmulti)
			MAX_H += 2
			if ConfigType == "1":
				MAX_W = int(55*4*Wmulti)+ int(48*2*Wmulti)
			elif ConfigType == "11":
				MAX_W = int(55*5*Wmulti)+ int(48*2*Wmulti)
			elif ConfigType == "12":
				MAX_W = int(55*2*Wmulti)+ int(48*2*Wmulti)
			elif ConfigType == "22":
				MAX_W = int(55*2*Wmulti)
			elif ConfigType == "2":
				MAX_W = int(55*4*Wmulti)
			elif ConfigType == "21":
				MAX_W = int(55*5*Wmulti)
			elif ConfigType == "3":
				MAX_W = int(49*2*Wmulti)
			elif ConfigType[0] == "4":
				MAX_W = int(55*Wmulti)
			elif ConfigType[0] == "5":
				MAX_W = int(54*3*Wmulti)
				POSX = int(54*2*Wmulti)
				POSY = int(54*2*Wmulti)
			
			if LCD4linux.WetterTransparenz.value == "true":
				imW = Image.new('RGBA', (MAX_W, MAX_H), (0, 0, 0, 0))
			else:
				imW = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				if LCD4linux.WetterTransparenz.value == "crop":
					POSXs = getSplit(ConfigSplit,ConfigAlign,MAX_Wi,MAX_W)
					image_Back = im.crop((POSXs, ConfigPos, POSXs+MAX_W, ConfigPos+MAX_H))
					imW.paste(image_Back,(0,0))
			drawW = ImageDraw.Draw(imW)
			if ConfigType != "3" and ConfigType[0] != "4":
				i=0
				for curr in self.WWeek[ConfigWWW]:
					if (i<4 and ConfigType in ["1","2","5"]) or (i<5 and ConfigType in ["11","21","51"]) or (i<2 and ConfigType in ["12","22"]):
						i+=1
						High = curr.get("High","0")
						Low = curr.get("Low","0")
						Day = curr.get("Day","")
						Icon = curr.get("Icon","0")
						Cond = curr.get("Cond","")
						Regen = curr.get("Regen","0")
						Regen += "%" if LCD4linux.WetterRain.value == "true2" else ""
						if ConfigType[0] == "5":
							font = ImageFont.truetype(ConfigFont,int(14*Wmulti), encoding='unic')
							fontD = ImageFont.truetype(ConfigFont,int(14*Wmulti), encoding='unic')
						else:
							fontD = ImageFont.truetype(ConfigFont,int(18*Wmulti), encoding='unic')
							if len(High)>2 or len(Low)>2:
								font = ImageFont.truetype(ConfigFont,int(18*Wmulti), encoding='unic')
							else:
								font = ImageFont.truetype(ConfigFont,int(20*Wmulti), encoding='unic')
#						print "WetterData", Day, Low, High, Icon
						if UseExt == "gif":
							Icon = Icon.replace(".png",".gif")
						if isOffTime(L4LMoon,L4LSun,L4LMoon,L4LSun):
							if os.path.isfile(UseWetterPath + Icon.replace("."+UseExt,"_night."+UseExt)) and Icon.find(UseExt) > 1:
								Icon = Icon.replace("."+UseExt,"_night."+UseExt)
						if os.path.isfile(UseWetterPath + Icon) and Icon.find(UseExt) > 1:
							pil_image = Image.open(UseWetterPath + Icon)
							xx,yy = pil_image.size
							y=int(float(int(LCD4linux.WetterIconZoom.value)*Wmulti)/xx*yy)
							if LCD4linux.BilderQuality.value == "0":
								pil_image = pil_image.resize((int(int(LCD4linux.WetterIconZoom.value)*Wmulti), y))
							else:
								pil_image = pil_image.resize((int(int(LCD4linux.WetterIconZoom.value)*Wmulti), y), Image.ANTIALIAS)
							if ConfigType[0] == "5":
								PY = POSY-int(20*Wmulti)
							else:
								PY = int(POSY +(int(40*Wmulti)-y)/2)
							PX = POSX + int((27*Wmulti)-int(int(LCD4linux.WetterIconZoom.value)*Wmulti)/2)
							if UseExt == "png":
								try:
									imW.paste(pil_image,(PX,PY+int(20*Wmulti)),pil_image)
								except:
									pass
							else:
								imW.paste(pil_image,(PX,PY+int(20*Wmulti)))
						if ConfigType[0] == "5":
							Dayw,h = drawW.textsize(Day, font=fontD)
							if LCD4linux.WetterLine.value.startswith("true"):
								drawW.line((10,POSY,MAX_W-10,POSY),fill=ConfigColor)
							PX = int(POSX-Dayw-(3*Wmulti))
							ShadowText(drawW,PX, POSY, Day, fontD, ConfigColor, ConfigShadow)
							w,h = drawW.textsize(High + "\xc2\xb0", font=font)
							PX = int(POSX-w-(3*Wmulti))
							ShadowText(drawW,PX, POSY+h, High + "\xc2\xb0", font, LCD4linux.WetterHighColor.value, ConfigShadow)
							w,h = drawW.textsize(Low + "\xc2\xb0  "+High + "\xc2\xb0", font=font)
							PX = int(POSX-w-(3*Wmulti))
							ShadowText(drawW,PX, POSY+h, Low + "\xc2\xb0", font, LCD4linux.WetterLowColor.value, ConfigShadow)
							w,h = drawW.textsize(Cond, font=font)
							PX = int(POSX-w-(3*Wmulti))
							if PX<0:
								PX = 0
							ShadowText(drawW,PX, POSY+2*h, Cond, font, ConfigColor, ConfigShadow)
							if LCD4linux.WetterRain.value != "false":
								font = ImageFont.truetype(ConfigFont,int(int(LCD4linux.WetterRainZoom.value)*Wmulti/10.0), encoding='unic')
								w,h = drawW.textsize(Regen, font=font)
#								drawW.rectangle((MAX_W-w, POSY+2, MAX_W, POSY+h-2),fill="black")
								ShadowText(drawW,MAX_W-w, POSY, Regen, font, LCD4linux.WetterRainColor.value if Regen < LCD4linux.WetterRainColor2use.value else LCD4linux.WetterRainColor2.value, ConfigShadow)
						else:
							Leer,h = drawW.textsize(" ", font=font)
							w,Dayh = drawW.textsize(Day, font=fontD)
							PX = POSX + int((27*Wmulti)-w/2)
							ShadowText(drawW,PX, POSY, Day, fontD, ConfigColor, ConfigShadow)
							w,h = drawW.textsize(Low, font=font)
							PX = POSX + int((27*Wmulti))-w-int(Leer/2)
							if len(High)>2 or len(Low)>2:
								PY = int(h/10)
							else:
								PY = 0
							ShadowText(drawW,PX, POSY+PY+int(60*Wmulti), Low, font, LCD4linux.WetterLowColor.value, ConfigShadow)
							w,h = drawW.textsize(High, font=font)
							PX = POSX + int((27*Wmulti))+int(Leer/2)
							ShadowText(drawW,PX, POSY+PY+int(60*Wmulti), High, font, LCD4linux.WetterHighColor.value, ConfigShadow)

							if LCD4linux.WetterRain.value != "false":
								font = ImageFont.truetype(ConfigFont,int(int(LCD4linux.WetterRainZoom.value)*Wmulti/10.0), encoding='unic')
								w,h = drawW.textsize(Regen, font=font)
#								drawW.rectangle((POSX+int(54*Wmulti)-w-2, POSY+Dayh-int(h/2)+2, POSX+int(54*Wmulti)-2, POSY+Dayh-int(h/2)+h-2),fill="black")
								ShadowText(drawW,POSX+int(54*Wmulti)-w-2, POSY+Dayh-int(h/2), Regen, font, LCD4linux.WetterRainColor.value if Regen < LCD4linux.WetterRainColor2use.value else LCD4linux.WetterRainColor2.value, ConfigShadow)
							if LCD4linux.WetterLine.value == "true":
								drawW.line((POSX,1,POSX,POSY+int(60*Wmulti)),fill=ConfigColor)
							elif LCD4linux.WetterLine.value == "trueLong":
								drawW.line((POSX,1,POSX,POSY+int(80*Wmulti)),fill=ConfigColor)
				
						if ConfigType[0] == "5":
							POSX = int(54*2*Wmulti)
							POSY += int(54*Wmulti)
						else:
							POSX += int(54*Wmulti)
				if ConfigType[0] != "5":
					if LCD4linux.WetterLine.value == "true":
						drawW.line((POSX,1,POSX,POSY+int(60*Wmulti)),fill=ConfigColor)
					elif LCD4linux.WetterLine.value == "trueLong":
						drawW.line((POSX,1,POSX,POSY+int(80*Wmulti)),fill=ConfigColor)
					POSX += 1
				if ConfigType[0] == "2":
					POSX = 1
					POSY += int(80*Wmulti)
				
			Hum = "?"
			Wind = "?"
			Temp_c = "?"
			Icon=""
			Locname=""
			Feel=""
			Wtime=""
			if ConfigType == "3":
#				POSY = int(-20*Wmulti)
				POSY = int(-20*Wmulti)
			elif ConfigType[0] == "5":
				POSX = int(54*Wmulti)
				POSY = 1
			if len(self.WDay[ConfigWWW]) != 0 and LCD4linux.WetterExtra.value == True:
				Locname = self.WDay[ConfigWWW].get("Locname","")
			if len(self.WDay[ConfigWWW]) != 0:
				Temp_c = self.WDay[ConfigWWW].get("Temp_c","0")
				Hum = self.WDay[ConfigWWW].get("Hum","0")
				Wind = self.WDay[ConfigWWW].get("Wind","0")
				Cond = self.WDay[ConfigWWW].get("Cond","0")
				Icon = self.WDay[ConfigWWW].get("Icon","0")
				Feel = self.WDay[ConfigWWW].get("Feel","0")
				if self.WetterOK==False:
					Wtime = self.WDay[ConfigWWW].get("Wtime","00:00")
				if Feel=="" or abs(int(Feel or "0")-int(Temp_c[:-1])) < int(LCD4linux.WetterExtraFeel.value) or LCD4linux.WetterExtra.value == False:
					Feel = ""
				else:
					Feel += "\xc2\xb0"
#				print "Temp, Hum", Temp_c, Hum, Wind, Icon
				if ConfigType[0] == "4":
					if ConfigType == "4":
						Temp_c += "C"
					TextSize = int(25*Wmulti)
					font = ImageFont.truetype(ConfigFont,TextSize, encoding='unic')
					w,h = drawW.textsize(Temp_c, font=font)
					while w > MAX_W:
						TextSize -= 1
						font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
						w,h = drawW.textsize(Temp_c, font=font)
					ShadowText(drawW,POSX, POSY, Temp_c, font, ConfigColor, ConfigShadow)
				else:
					if UseExt == "gif":
						Icon = Icon.replace(".png",".gif")
					if isOffTime(L4LMoon,L4LSun,L4LMoon,L4LSun):
						if os.path.isfile(UseWetterPath + Icon.replace("."+UseExt,"_night."+UseExt)) and Icon.find(UseExt) > 1:
							Icon = Icon.replace("."+UseExt,"_night."+UseExt)
					if os.path.isfile(UseWetterPath + Icon) and Icon.find(UseExt) > 1:
						pil_image = Image.open(UseWetterPath + Icon)
						xx,yy = pil_image.size
						if ConfigType[0] == "5":
							y=int(float((int(LCD4linux.WetterIconZoom.value)+30)*Wmulti)/xx*yy)
							if LCD4linux.BilderQuality.value == "0":
								pil_image = pil_image.resize((int((int(LCD4linux.WetterIconZoom.value)+30)*Wmulti), y))
							else:
								pil_image = pil_image.resize((int((int(LCD4linux.WetterIconZoom.value)+30)*Wmulti), y), Image.ANTIALIAS)
#							x=int(float(70*Wmulti)/yy*xx)
#							pil_image = pil_image.resize((x,int(70*Wmulti)), Image.ANTIALIAS) #BILINEAR)
							xx,yy = pil_image.size
							PY = 1-int(20*Wmulti)
							POSX = MAX_W - xx
						else:
							y=int(float(int(LCD4linux.WetterIconZoom.value)*Wmulti)/xx*yy)
							if LCD4linux.BilderQuality.value == "0":
								pil_image = pil_image.resize((int(int(LCD4linux.WetterIconZoom.value)*Wmulti)+2, y))
							else:
								pil_image = pil_image.resize((int(int(LCD4linux.WetterIconZoom.value)*Wmulti)+2, y), Image.ANTIALIAS)
							PY = int(POSY +(int(40*Wmulti)-y)/2)
						if UseExt == "png":
							if PY+int(20*Wmulti)<0:
								PY=-int(20*Wmulti)
							try:
								imW.paste(pil_image,(POSX,PY+int(20*Wmulti)),pil_image)
							except:
								pass
						else:
							imW.paste(pil_image,(POSX,PY+int(20*Wmulti)))
#				if LCD4linux.WetterRain.value == True:
					if ConfigType == "3":
						POSXs,POSYs = POSX,POSY+int(89*Wmulti)
					else:
						POSXs,POSYs = POSX,POSY
					fontS = ImageFont.truetype(ConfigFont,int(((int(LCD4linux.WetterExtraZoom.value)-100)/20.0+8)*Wmulti), encoding='unic')
					ShadowText(drawW,POSXs, POSYs, Locname+" "+Wtime, fontS, LCD4linux.WetterExtraColorCity.value, ConfigShadow)

					font = ImageFont.truetype(ConfigFont,int(15*Wmulti), encoding='unic')
					if ConfigType[0] == "5":
						w,h = drawW.textsize(Cond, font=font)
						PX = MAX_W-w-int(3*Wmulti)
						if PX<0:
							PX = 0
						ShadowText(drawW,PX, int(70*Wmulti), Cond, font, ConfigColor, ConfigShadow) #silver
						w,h = drawW.textsize(Wind, font=font)
						ShadowText(drawW,MAX_W-w-int(3*Wmulti), int(70*Wmulti)+h, Wind, font, ConfigColor, ConfigShadow) #silver
						font = ImageFont.truetype(ConfigFont,int(35*Wmulti), encoding='unic')
						w,h = drawW.textsize(Temp_c, font=font)
						ShadowText(drawW,POSX-w-int(3*Wmulti), POSY, Temp_c, font, LCD4linux.WetterHighColor.value, ConfigShadow)
						w,h = drawW.textsize(Temp_c[-1:], font=font)
						fontF = ImageFont.truetype(ConfigFont,int((int(LCD4linux.WetterExtraZoom.value)/10.0+4)*Wmulti), encoding='unic')
						wS,hS = drawW.textsize(Feel, font=fontF)
#						drawW.text((POSX-w-int(3*Wmulti), POSY+int(h/1.7)), Feel, font=fontS, fill=ConfigColor)
						ShadowText(drawW,POSX-w-int(3*Wmulti), POSY+h-int(hS*0.8), Feel, fontF, LCD4linux.WetterExtraColorFeel.value, ConfigShadow)
						font = ImageFont.truetype(ConfigFont,int(15*Wmulti), encoding='unic')
						w,h = drawW.textsize(Hum, font=font)
						ShadowText(drawW,POSX-w-int(3*Wmulti), yy-h, Hum, font, ConfigColor, ConfigShadow) #silver
					else:
#						minus5 = 0 if ConfigType[0] != "1" else 0
						minus5 = -3
						font = ImageFont.truetype(ConfigFont,int(13*Wmulti), encoding='unic')
						ShadowText(drawW,POSX-minus5, POSY+int(64*Wmulti), Wind, font, ConfigColor, ConfigShadow) #silver
						font = ImageFont.truetype(ConfigFont,int(25*Wmulti), encoding='unic')
						w,h = drawW.textsize(Temp_c, font=font)
						TextSize = int(25*Wmulti)
						while POSX+int(45*Wmulti)+w > MAX_W:
							TextSize -= 1
							font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
							w,h = drawW.textsize(Temp_c, font=font)
						ShadowText(drawW,POSX+int(45*Wmulti), POSY+int(16*Wmulti), Temp_c, font, LCD4linux.WetterHighColor.value, ConfigShadow)
						w,h = drawW.textsize(Temp_c[:-1], font=font)
						fontF = ImageFont.truetype(ConfigFont,int(int(LCD4linux.WetterExtraZoom.value)/10.0*Wmulti), encoding='unic')
						wS,hS = drawW.textsize(Feel, font=fontF)
						ShadowText(drawW,POSX+int(45*Wmulti)+w, POSY+int(16*Wmulti)+h-int(hS*0.8), Feel, fontF, LCD4linux.WetterExtraColorFeel.value, ConfigShadow)
#						drawW.text((POSX+int(45*Wmulti)+w, POSY+int(16*Wmulti)+int(h/1.7)), Feel, font=fontS, fill=ConfigColor)
						font = ImageFont.truetype(ConfigFont,int(16*Wmulti), encoding='unic')
						wH,hH = drawW.textsize(Hum, font=font)
						TextSize = int(25*Wmulti)
						while POSX+int(45*Wmulti)+wH > MAX_W:
							TextSize -= 1
							font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
							wH,hH = drawW.textsize(Hum, font=font)
						ShadowText(drawW,POSX+int(45*Wmulti), POSY+int(16*Wmulti)+h, Hum, font, ConfigColor, ConfigShadow) #silver
			imW.save(PICwetter % ConfigWWW)
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_Wi,MAX_W)
			try:
				if LCD4linux.WetterTransparenz.value == "true":
					im.paste(imW,(POSX,ConfigPos),imW)
				else:
					im.paste(imW,(POSX,ConfigPos))
			except:
				pass
		return

# Meteo station
	def putMeteo((ConfigPos, ConfigZoom, ConfigAlign, ConfigSplit, ConfigType, ConfigColor), draw, im):
		global MeteoType
		global MeteoZoom
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		if os.path.isfile(PICmeteo) and ConfigType == MeteoType and ConfigZoom == MeteoZoom:
			pil_image = Image.open(PICmeteo)
			x,y = pil_image.size
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
			im.paste(pil_image,(POSX,ConfigPos))
		else:
			MeteoType=ConfigType
			MeteoZoom=ConfigZoom
			POSX, POSY = 1,0
			Wmulti = ConfigZoom/10.0
			if ConfigType == "2":
				MAX_H = int(25*Wmulti)
			else:
				MAX_H = int(80*Wmulti)
			if ConfigType == "1":
				MAX_W = int(57*2*Wmulti)
			elif ConfigType == "2":
				MAX_W = int(55*Wmulti)
			imW = Image.new('RGB', (MAX_W, MAX_H))
			drawW = ImageDraw.Draw(imW)
			dom = parseString(wwwMeteo)
			Hum = "?"
			Wind = "?"
			Temp_c = "?"
			Rain = ""
			Icon=""
			if ConfigType == "1":
				POSY = int(-20*Wmulti)
			for node in dom.getElementsByTagName('current_conditions'):
				for temp_c in node.getElementsByTagName('temp_c'):
					Temp_c = temp_c.getAttribute('data')
				for hum in node.getElementsByTagName('humidity'):
					Hum = hum.getAttribute('data')
				for wind in node.getElementsByTagName('wind_condition'):
					Wind = wind.getAttribute('data')
				for icon in node.getElementsByTagName('icon'):
					Icon = os.path.basename(icon.getAttribute('data'))
				for rain in node.getElementsByTagName('rain'):
					Rain = rain.getAttribute('data')
#				print "Temp, Hum", Temp_c, Hum, Wind, Icon
				if ConfigType == "2":
					font = ImageFont.truetype(FONT,int(25*Wmulti), encoding='unic')
					w,h = drawW.textsize(Temp_c, font=font)
					TextSize = int(25*Wmulti)
					while w > MAX_W:
						TextSize -= 1
						font = ImageFont.truetype(FONT, TextSize, encoding='unic')
						w,h = drawW.textsize(Temp_c, font=font)
					drawW.text((POSX, POSY), Temp_c, font=font, fill=ConfigColor)
				else:
					if os.path.isfile(MeteoPath + Icon):
						pil_image = Image.open(MeteoPath + Icon)
						xx,yy = pil_image.size
						y=int(float(40*Wmulti)/xx*yy)
						if LCD4linux.BilderQuality.value == "0":
							pil_image = pil_image.resize((int(40*Wmulti), y))
						else:
							pil_image = pil_image.resize((int(40*Wmulti), y), Image.ANTIALIAS)
						PY = int(POSY+(int(40*Wmulti)-y)/2)
						imW.paste(pil_image,(POSX,PY+int(15*Wmulti)))
					font = ImageFont.truetype(FONT,int(12*Wmulti), encoding='unic')
					drawW.text((POSX, POSY+int(52*Wmulti)), Rain, font=font, fill="aquamarine")
					drawW.text((POSX, POSY+int(64*Wmulti)), Wind, font=font, fill="silver")
					font = ImageFont.truetype(FONT,int(25*Wmulti), encoding='unic')
					w,h = drawW.textsize(Temp_c, font=font)
					TextSize = int(25*Wmulti)
					while POSX+(45*Wmulti)+w > MAX_W:
						TextSize -= 1
						font = ImageFont.truetype(FONT, TextSize, encoding='unic')
						w,h = drawW.textsize(Temp_c, font=font)
					drawW.text((POSX+int(45*Wmulti), POSY+int(16*Wmulti)), Temp_c, font=font, fill=LCD4linux.WetterHighColor.value)
					font = ImageFont.truetype(FONT,int(22*Wmulti), encoding='unic')
					w,h = drawW.textsize(Hum, font=font)
					TextSize = int(25*Wmulti)
					while POSX+(45*Wmulti)+w > MAX_W:
						TextSize -= 1
						font = ImageFont.truetype(FONT, TextSize, encoding='unic')
						w,h = drawW.textsize(Hum, font=font)
					drawW.text((POSX+int(52*Wmulti), POSY+int(40*Wmulti)), Hum, font=font, fill="silver")
			imW.save(PICmeteo)
			x,y = imW.size
			MAX_W,MAX_H = im.size
			if ConfigSplit == True:
				MAX_W = int(MAX_W/2)
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
			im.paste(imW,(POSX,ConfigPos))
		return

# Mondphase
	def putMoon((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigFont),draw,im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		POS = MoonPosition()
		PHASE = MoonPhase(POS)
		FILE = "moon%04d.gif" % round(POS*100)
#		L4log(POS,PHASE)
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,ConfigSize)
		if os.path.isfile(os.path.join(LCD4linux.MoonPath.value,FILE)):
			try:
				pil_image = Image.open(os.path.join(LCD4linux.MoonPath.value,FILE))
				pil_image = pil_image.resize((ConfigSize, ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					pil_image = pil_image.convert("RGBA")
					im.paste(pil_image,(POSX,ConfigPos),pil_image)
				else:
					im.paste(pil_image,(POSX,ConfigPos))
				ConfigPos += ConfigSize
			except:
				L4log("Error Moon")
		if ConfigColor != "0":
			font = ImageFont.truetype(ConfigFont, int(ConfigSize/5), encoding='unic')
			if len(PHASE) > 10:
				P = PHASE.split(" ")
			else:
				P = [PHASE]
			for Pi in P:
				w,h = draw.textsize(Pi, font=font)
				px = int(POSX+(ConfigSize/2)-w/2)
				if px < 0:
					px = 0
				if px+w > MAX_W:
					px = MAX_W-w
				ShadowText(draw,px,ConfigPos,Pi,font,ConfigColor,ConfigShadow)
				ConfigPos += h

# Text File
	def putTextFile((ConfigPos, ConfigSize, ConfigFont, ConfigAlign, ConfigColor, ConfigBackColor, ConfigShadow, TextFile), draw, im):
		if ConfigMode==True and os.path.isfile(TextFile) == False:
			if os.path.isfile(TXTdemo) == False:
				f = open(TXTdemo,"w")
				f.write("demo line 1\ndemotext")
				f.close()
			TextFile = TXTdemo
		if os.path.isfile(TextFile):
			MAX_W,MAX_H = im.size
			current_h=ConfigPos
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			try:
				for line in open(TextFile,"r").readlines():
					line = Code_utf8(line.replace('\n',''))
					w,h = draw.textsize(line, font=font)
					POSX = getSplit(False,ConfigAlign,MAX_W,w)
					if ConfigBackColor !="0":
						draw.rectangle((POSX, current_h,POSX+w, current_h+h),fill=ConfigBackColor)
					ShadowText(draw,POSX,current_h,line,font,ConfigColor,ConfigShadow)
					current_h+=h
			except:
				L4log("Error reading",TextFile)

# HTTP Text
	def putHTTP((ConfigPos, ConfigSize, ConfigAlign, ConfigColor, ConfigBackColor, HTTPurl, ConfigShadow, ConfigFont), draw, im):
		t = ["not found"]
		try:
			r = urllib.urlopen(HTTPurl)
			t = r.read().split("\n")
			r.close()
		except:
			pass 
		finally:
			MAX_W,MAX_H = im.size
			current_h=ConfigPos
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			for line in t:
				line = Code_utf8(line.replace('\n',''))
				w,h = draw.textsize(line, font=font)
				POSX = getSplit(False,ConfigAlign,MAX_W,w)
				if ConfigBackColor !="0":
					draw.rectangle((POSX, current_h,POSX+w, current_h+h),fill=ConfigBackColor)
				ShadowText(draw,POSX, current_h, line, font, ConfigColor, ConfigShadow)
				current_h+=h

# HTTP WWW Site
	def putWWW((PIC, ConfigPos, ConfigSize, ConfigAlign, ConfigCutX, ConfigCutY, ConfigCutW, ConfigCutH), draw, im):
		MAX_W,MAX_H = im.size
		if os.path.isfile(WWWpic % PIC):
			if os.path.isfile(WWWpic % (str(PIC)+"p")):
				pil_image = Image.open(WWWpic % (str(PIC)+"p"))
				POSX = getSplit(False,ConfigAlign,MAX_W,ConfigSize)
				im.paste(pil_image,(POSX,ConfigPos))
			else:
				pil_image = Image.open(WWWpic % PIC)
				if ConfigCutW != 0 and ConfigCutH != 0:
					try:
						pil_image = pil_image.crop((ConfigCutX,ConfigCutY,ConfigCutX+ConfigCutW,ConfigCutY+ConfigCutH))
					except:
						L4log("Error Crop WWW")
				xx,yy = pil_image.size
				y=int(float(ConfigSize)/xx*yy)
				if LCD4linux.BilderQuality.value == "0":
					pil_image = pil_image.resize((ConfigSize,y))
				else:
					pil_image = pil_image.resize((ConfigSize,y), Image.ANTIALIAS)
				POSX = getSplit(False,ConfigAlign,MAX_W,ConfigSize)
				im.paste(pil_image,(POSX,ConfigPos))
				pil_image.save(WWWpic % (str(PIC)+"p"))

# Clock
	def putClock((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType, ConfigSpacing, ConfigAnalog, ConfigColor, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		pp=ConfigPos
		if ConfigType == "4":
			y = int(ConfigSize*1.8)
			y271 = int(y/2.71)
			if os.path.isfile(ClockBack) == True:
				try:
					pil_image = Image.open(ClockBack)
					xx,yy = pil_image.size
					x=int(float(y)/yy*xx)
					if LCD4linux.BilderQuality.value == "0":
						image_new = pil_image.resize((x, y))
					else:
						image_new = pil_image.resize((x, y), Image.ANTIALIAS)
					POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
					if LCD4linux.WetterTransparenz.value == "true":
						image_new = image_new.convert("RGBA")
						im.paste(image_new,(POSX,ConfigPos),image_new)
					else:
						im.paste(image_new,(POSX,ConfigPos))
					image_line = image_new.crop((0, y271, x, y271+2+int(y/60)))

					now = strftime("%H")
					font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
					w,h = draw.textsize(now, font=font)
					lx = int(((x/2)-w)/2)
					ShadowText(draw,POSX+lx,ConfigPos+int(y271-(h/2)),now,font,ConfigColor,ConfigShadow)
					now = strftime("%M")
					w,h = draw.textsize(now, font=font)
					lx = int(((x/2)-w)/2)
					ShadowText(draw,POSX+int(x/2)+lx,ConfigPos+int(y271-(h/2)),now,font,ConfigColor,ConfigShadow)
					im.paste(image_line,(POSX,ConfigPos+y271))

					now = strftime("%d.%m.%Y")
					font = ImageFont.truetype(ConfigFont, int(ConfigSize/2.6), encoding='unic')
					w,h = draw.textsize(now, font=font)
					lx = (x-w)/2
					ShadowText(draw,POSX+lx,ConfigPos+int((y/1.14)-(h/2)),now,font,ConfigColor,ConfigShadow)
				except:
					pass
		elif ConfigType[0] == "5":
			y = int(ConfigSize*1.8)
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,y)
			if os.path.isfile(Clock+ConfigAnalog+"/Clock.png") == True:
				try:
					pil_image = Image.open(Clock+ConfigAnalog+"/Clock.png")
					if LCD4linux.BilderQuality.value == "0":
						pil_image = pil_image.resize((y, y))
					else:
						pil_image = pil_image.resize((y, y), Image.ANTIALIAS)
					im.paste(pil_image,(POSX,ConfigPos),pil_image)
					
					if ConfigType[:3] == "521":
						if "+" in ConfigType:
							now = Code_utf8(_(strftime("%A")))
							font = ImageFont.truetype(ConfigFont, int(ConfigSize/3), encoding='unic')
						else:
							now = Code_utf8(_(strftime("%a")))
							font = ImageFont.truetype(ConfigFont, int(ConfigSize/5), encoding='unic')
						w,h = draw.textsize(now, font=font)
						if "+" in ConfigType:
							x1 = POSX - w + int(h/2)
							y1 = ConfigPos+y-h
						else:
							x1 = POSX + int(y*3/4)
							y1 = ConfigPos + int(y/2) - int(h/2)
							di = int(h/7)
							draw.rectangle((x1-di, y1+di, x1+w+di, y1+h-di),fill="black")
						ShadowText(draw,x1,y1,now,font,ConfigColor,ConfigShadow)
#						draw.text((x1, y1), now, font=font, fill=ConfigColor)

					pil_image = Image.open(Clock+ConfigAnalog+"/Hour.png")
					if LCD4linux.BilderQuality.value == "0":
						pil_image = pil_image.resize((y, y))
					else:
						pil_image = pil_image.resize((y, y), Image.ANTIALIAS)
					S =int(strftime("%H"))
					if S>12:
						S-=12
					pil_image = pil_image.rotate(360-int(30*S+int(int(strftime("%M"))/2))) #360/12
					pil_image = pil_image.convert("RGBA")
					im.paste(pil_image,(POSX,ConfigPos),pil_image)
					pil_image = Image.open(Clock+ConfigAnalog+"/Minute.png")
					if LCD4linux.BilderQuality.value == "0":
						pil_image = pil_image.resize((y, y))
					else:
						pil_image = pil_image.resize((y, y), Image.ANTIALIAS)
					pil_image = pil_image.rotate(360-int(6*int(strftime("%M")))) #360/60
					pil_image = pil_image.convert("RGBA")
					im.paste(pil_image,(POSX,ConfigPos),pil_image)
					if ConfigType[:2] == "52":
						now = strftime("%d.%m.%Y")
						font = ImageFont.truetype(ConfigFont, int(ConfigSize/3), encoding='unic')
						w,h = draw.textsize(now, font=font)
						if "+" in ConfigType:
							lx = POSX+y-int(h/2)
							pp = ConfigPos+y-h
						else:
							lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,w)
							pp = ConfigPos+y
						ShadowText(draw,lx,pp,now,font,ConfigColor,ConfigShadow)
				except:
					pass
		elif ConfigType[0] == "1":
			now = ""
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			ww,hh = draw.textsize(strftime("%H:%M"), font=font)
			font = ImageFont.truetype(ConfigFont, int(ConfigSize/2), encoding='unic')
			ww2,hh = draw.textsize(strftime("%d.%m.%Y"), font=font)
			if ww2 > ww:
				ww = ww2
			lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,ww)
			ll = int(lx+ww/2)
			for tt in ConfigType[1:]:
				font = ImageFont.truetype(ConfigFont, int(ConfigSize/2), encoding='unic')
				w,h2 = draw.textsize(now, font=font)
				if tt == "1":
					now = strftime("%d.%m.%Y")
				elif tt == "2":
					now = strftime("%H:%M")
					font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				elif tt == "3":
					font = ImageFont.truetype(ConfigFont, int(ConfigSize/2.5), encoding='unic')
					now = Code_utf8(_(strftime("%A")))
				
				w,h = draw.textsize(now, font=font)
				lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,w)
				if (ll+w/2) < MAX_W and (ll-w/2) > 0:
					ShadowText(draw,int(ll-w/2),pp,now,font,ConfigColor,ConfigShadow)
				else:
					ShadowText(draw,lx,pp,now,font,ConfigColor,ConfigShadow)
				if ConfigSpacing == "1":
					pp+=h-int(h2*1/4)
				elif ConfigSpacing == "2":
					pp+=h-int(h2*1/3)
				elif ConfigSpacing == "3":
					pp+=h-int(h2/2)
				else:
					pp+=h

# Bild
	def putBild((ConfigPos, ConfigSize, ConfigSizeH, ConfigAlign, ConfigQuick, ConfigTransp, ConfigFile, ConfigFileOrg), ConfigLCD, draw, im):
		global QuickList
		MAX_W,MAX_H = im.size
		small = ""
		if os.path.isfile(ConfigFile):
			x = ConfigSize
			try:
				pil_image = Image.open(ConfigFile)
				xx,yy = pil_image.size
				y = int(float(x)/xx*yy)
				if ConfigAlign == "9":
					x,y = MAX_W,MAX_H
				if ConfigSizeH>0 and y>ConfigSizeH:
					y = ConfigSizeH
					x = int(float(y)/yy*xx)
				small = ConfigAlign
				POSX = getSplit(False,ConfigAlign,MAX_W,x)
				if small == "2":
					POSX -= int((ConfigSize-x)/2)
				elif small == "0":
					POSX += int((ConfigSize-x)/2)
				if LCD4linux.BilderQuality.value == "2":
					pil_image = pil_image.resize((x, y), Image.ANTIALIAS)
				else:
					pil_image = pil_image.resize((x, y))
				if ConfigSizeH>0:
					ConfigPos = ConfigPos+int((ConfigSizeH-y)/2)
				if ConfigAlign == "9":
					POSX,ConfigPos = 0,0
				if ConfigTransp == True:
					pil_image = pil_image.convert("RGBA")
					im.paste(pil_image,(POSX,ConfigPos),pil_image)
				else:
					im.paste(pil_image,(POSX,ConfigPos))
				if ConfigQuick == True:
					L4logE("add Quick",ConfigFileOrg)
					QuickList[ConfigLCD].append([ConfigFileOrg,POSX,ConfigPos,x,y])
			except:
				pass
		elif ConfigMode == True:
			POSX = getSplit(False,ConfigAlign,MAX_W,ConfigSize)
			if ConfigSizeH>0:
				draw.rectangle((POSX, ConfigPos, POSX+ConfigSize, ConfigPos+ConfigSizeH),fill="red")
			else:
				draw.rectangle((POSX, ConfigPos, POSX+ConfigSize, ConfigPos+(ConfigSize*3/4)),fill="red")
				draw.rectangle((POSX, ConfigPos, POSX+ConfigSize, ConfigPos+ConfigSize),outline="red")

# Grab TV
	def doGrabTV(x,y,lcd,vidosd):
		global TVrunning
		if TVrunning == False:
			TVrunning = True
#			t = Thread(target=doGrabTVthread, args=(x,y,lcd,vidosd))
#			t.start()
			if lcd in ["1","4","7"]:
				Brief1.put([doGrabTVthread,x,y,lcd,vidosd])
			elif lcd in ["2","5","8"]:
				Brief2.put([doGrabTVthread,x,y,lcd,vidosd])

	class GrabTV:
		def __init__(self, cmd):
			global GrabTVRunning
			GrabTVRunning = True
			L4logE("GrabTV Run")

			os.system(cmd + " >/dev/null 2>&1")
#			os.system("/usr/bin/grab -o -p -b -r %d /tmp/dpfgrab.png >/dev/null 2>&1" % ConfigSize ) 
#			self.container = eConsoleAppContainer()
#			self.container.appClosed.append(self.cmdFinished)
#			self.container.dataAvail.append(self.dataAvail)
			self.cmdFinished("")
#			self.container.execute(cmd)

		def cmdFinished(self, data):
			global GrabTVRunning
			L4logE("GrabTV Stop")
			GrabTVRunning = False

		def dataAvail(self, data):
			pass

	def doGrabTVthread(x,y,lcd,vidosd):
		global TVrunning
		global SamsungDevice
		global SamsungDevice2
		global SamsungDevice3
		vt = "-v" if vidosd == "0" else ""
		im = Image.new('RGB', (int(x), int(y)), (0, 0, 0, 0))
#		GrabTV("/usr/bin/grab %s -j 40 -r %s /tmp/lcd4linux/tvgrab.jpg" % (vt,x))
		while TVrunning == True and ScreenActive[0] in LCD4linux.TV.value:
			GrabTV("/usr/bin/grab %s -j 40 -r %s %stvgrab.jpg" % (vt,x,TMPL))
#			if lcd in ["1","3"]:
#				Brief1.put([GrabTV,"/usr/bin/grab %s -j 40 -r %s %stvgrab.jpg" % (vt,x,TMPL)])
#			else:
#				Brief2.put([GrabTV,"/usr/bin/grab %s -j 40 -r %s %stvgrab.jpg" % (vt,x,TMPL)])
			i = 0
			while GrabTVRunning == True and i < 100:
				sleep(0.05)
				i += 1
#			os.system("/usr/bin/grab %s -j 40 -r %s /tmp/lcd4linux/tvgrab.jpg >/dev/null 2>&1" % (vt,x) ) 
			try:
				if lcd in ["1","2","3"]:
					pic = open("%stvgrab.jpg" % TMPL, "rb").read()
				else:
					pic = Image.open("%stvgrab.jpg" % TMPL)
				if TVrunning == True:
					if lcd == "1":
						if SamsungDevice is not None:
							try:
								Brief1.put([Photoframe.write_jpg2frame,SamsungDevice, pic])
							except:
								SamsungDevice = None
								L4log("Samsung 1 write error")
					elif lcd == "2":
						if SamsungDevice2 is not None:
							try:
								Brief2.put([Photoframe.write_jpg2frame,SamsungDevice2, pic])
							except:
								SamsungDevice2 = None
								L4log("Samsung 2 write error")
					elif lcd == "4":
						if SamsungDevice is not None:
							im.paste(pic,(0,0))
							if LCD4linux.LCDRotate1.value != "0":
								im=im.rotate(int(LCD4linux.LCDRotate1.value))
							Brief1.put([doDPF,1,im])
					elif lcd == "5":
						if SamsungDevice2 is not None:
							im.paste(pic,(0,0))
							if LCD4linux.LCDRotate2.value != "0":
								im=im.rotate(int(LCD4linux.LCDRotate2.value))
							Brief2.put([doDPF,2,im])
					elif lcd == "7":
						im.paste(pic,(0,0))
						writeLCD1(im,LCD4linux.BilderJPEG.value)
					elif lcd == "8":
						im.paste(pic,(0,0))
						writeLCD2(im,LCD4linux.BilderJPEG.value)
					elif lcd == "9":
						im.paste(pic,(0,0))
						writeLCD3(im,LCD4linux.BilderJPEG.value)
			except:
				pass
				from traceback import format_exc
				L4log("put Grab Error:",format_exc() )
		TVrunning = False

	def putGrab(ConfigFast,ConfigSize, im, draw):
		global OSDon
		MAX_W,MAX_H = im.size
#		CF = "" if ConfigFast == True else "-b"
##		os.system("/usr/bin/grab -o -p -b -r %d /tmp/lcd4linux/dpfgrab.png >/dev/null 2>&1" % ConfigSize ) 
#		os.system("/usr/bin/grab -o -p -j 95 %s -r %d /tmp/lcd4linux/dpfgrab.jpg >/dev/null 2>&1" % (CF,ConfigSize) ) 
		i = 0
		while GrabRunning == True and i < 100:
			sleep(0.05)
			i += 1
		L4logE("put Grab")
		if os.path.isfile("%sdpfgrab.jpg" % TMPL):
			try:
				pil_image = Image.open("%sdpfgrab.jpg" % TMPL)
				xx,yy = pil_image.size
				if OSDon > 0:
					if LCD4linux.OSDTransparenz.value == "0":
						im.paste(pil_image,((MAX_W-xx)/2, (MAX_H-yy)/2))
					else:
						pix=pil_image.load()
						pcheck = (0,0,0) if pix[0,0] == (0,0,0) else (255,255,255)
						L4logE("Grabpixel", pix[0,0])
						x2=int(xx/2)
						y2=int(yy/2)
						l,o=0,0
						r=xx-1
						u=yy-1
						while pix[l,y2] == pcheck and l<x2:
							l+=1
						l+=1
						while pix[r,y2] == pcheck and r>x2:
							r-=1
						r-=1
						while pix[x2,o] == pcheck and o<y2:
							o+=1
						o+=1
						while pix[x2,u] == pcheck and u>y2:
							u-=1
						u-=1
						if LCD4linux.OSDTransparenz.value == "2":
							draw.rectangle((0,0,MAX_W,MAX_H),fill="black")
						pix_image = pil_image.crop((l,o,r,u))
						xx,yy = pix_image.size
						im.paste(pix_image,((MAX_W-xx)/2, (MAX_H-yy)/2))
			except:
				from traceback import format_exc
				L4log("put Grab Error:",format_exc() )

# next Timer Record
	def putTimer((ConfigPos, ConfigSize, ConfigLines, ConfigType, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigFont), draw, im):
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		MAX_W,MAX_H = im.size
		timercount = 0
		POSY = ConfigPos
		POSX = 0 if ConfigAlign == "0" else int(MAX_W/2)
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		for timerlist in self.Ltimer_list:
			if timerlist.disabled == 0 and timerlist.justplay == 0:
				if timercount < int(ConfigLines):
					a = config.recording.margin_before.value*60 if ConfigType == "0" else 0
					b = config.recording.margin_after.value*60 if ConfigType == "0" else 0
					begin = strftime("%d. %H:%M", localtime(int(timerlist.begin)+a))
					timer_name = Code_utf8(timerlist.name)
					w,h = draw.textsize(begin, font=font)
					if ConfigLines == "1":
						begin += strftime(" - %H:%M", localtime(int(timerlist.end)-b))
						tx=cutText(begin,draw,font,MAX_W-h-5)
						tx2=cutText(timer_name,draw,font,MAX_W-h-5)
						ShadowText(draw,POSX+h+5,POSY,tx,font,ConfigColor,ConfigShadow)
						ShadowText(draw,POSX+h+5,POSY+h,tx2,font,ConfigColor,ConfigShadow)
					else:
						tx=cutText(begin + " " + timer_name,draw,font,MAX_W-h-5)
						ShadowText(draw,POSX+h+5,POSY,tx,font,ConfigColor,ConfigShadow)
					POSY += h
				timercount += 1
		if timercount == 0:
			if LCD4linux.ShowNoMsg.value == True:
				w,h = draw.textsize(_("no Timer"), font=font)
				ShadowText(draw,POSX+h+5,ConfigPos,_("no Timer"),font,ConfigColor,ConfigShadow)
		else:
			draw.ellipse((POSX+2, ConfigPos+2, POSX+h-4, ConfigPos+h-4), fill="red")
			if timercount>99:
				S = int(h/1.4) - 6
			elif timercount > 9:
				S = int(h/1.2) - 6
			else:
				S = h-6
			font = ImageFont.truetype(ConfigFont, S, encoding='unic')
			w1,h1 = draw.textsize(str(timercount), font=font)
			POSX = POSX+1+int(((h-4)-w1)/2)
			POSY = ConfigPos+1+int(((h-4)-h1)/2)
			draw.text((POSX, POSY), str(timercount), font=font, fill="white")

# Picon
	def putPicon((ConfigSize, ConfigPos, ConfigAlign, ConfigFullScreen, ConfigSplit, ConfigTextSize, Picon2), draw, im):
		MAXi_W,MAXi_H = im.size
		if ConfigSplit == True:
			MAXi_W = int(MAXi_W/2)
		if self.LsreftoString is not None:
			if ConfigFullScreen == True:
				MAX_W,MAX_H = MAXi_W,MAXi_H
			else:
				MAX_W,MAX_H = ConfigSize,ConfigSize
			rr=str(""+self.LsreftoString)
			rr=rr.split("::")[0]
			if rr[-1] != ":":
				rr+=":"
			picon = str(rr.replace(":", "_")[:-1]) + ".png"
			if Picon2 == False:
				P2 = LCD4linux.PiconPath.value
				P2A = LCD4linux.PiconPathAlt.value
				P2C = LCD4linux.PiconCache.value
			else:
				P2 = LCD4linux.Picon2Path.value
				P2A = LCD4linux.Picon2PathAlt.value
				P2C = LCD4linux.Picon2Cache.value
			if len(P2C)>2:
				useCache = True
				ret=getpiconres(MAX_W, MAX_H, ConfigFullScreen, picon, P2, P2A, P2C)
			else:
				useCache = False
				fields = picon.split('_', 3)
				if len(fields) > 2 and fields[2] != '2':
					#fallback to 1 for tv services with nonstandard servicetypes
					fields[2] = '1'
					piconnew = '_'.join(fields)
				if os.path.isfile(os.path.join(P2,picon)):
					ret=os.path.join(P2,picon)
				elif os.path.isfile(os.path.join(P2A,picon)) and len(P2A) > 3:
					ret=os.path.join(P2A,picon)
				elif os.path.exists(os.path.join(P2,piconnew)):
					ret=os.path.join(P2,piconnew)
				elif os.path.exists(os.path.join(P2A,piconnew)):
					ret=os.path.join(P2A,piconnew)
				else:
					ret=""
			POSX, POSY = 0,ConfigPos
			POSX = getSplit(ConfigSplit,ConfigAlign,MAXi_W,MAX_W)
			if ret == "":
				if self.Lchannel_name is not None:
					font = ImageFont.truetype(FONT, ConfigTextSize, encoding='unic')
					Channel_list = textwrap.wrap(self.Lchannel_name,width=int((MAX_W*2)/ConfigTextSize), break_long_words=False)
					hadd = 0
					l = 0
					for Channel_line in Channel_list:
						if l < 3:
							w,h = draw.textsize(Channel_line, font=font)
							TextSize = ConfigTextSize
							while w > MAX_W:
								TextSize -= 1
								font = ImageFont.truetype(FONT, TextSize, encoding='unic')
								w,h = draw.textsize(Channel_line, font=font)
							draw.text((((MAX_W-w)/2)+POSX,(POSY+hadd)), Channel_line, font=font, fill="white")
							l+=1
							hadd+=h
			else:
				try:
					pil_image = Image.open(ret)
					if useCache == False:
						if LCD4linux.PiconTransparenz.value == "2":
							pil_image = pil_image.convert("RGBA")
						xx,yy = pil_image.size
						y = MAX_H
						if ConfigFullScreen == False:
							y=int(float(ConfigSize)/xx*yy)
						if LCD4linux.BilderQuality.value == "0":
							pil_image = pil_image.resize((ConfigSize, y))
						else:
							pil_image = pil_image.resize((ConfigSize, y), Image.ANTIALIAS)
					MAX_W,MAX_H = pil_image.size
					POSX = getSplit(ConfigSplit,ConfigAlign,MAXi_W,MAX_W)
					if LCD4linux.PiconTransparenz.value == "2":
						im.paste(pil_image,(POSX,POSY),pil_image)
					else:
						im.paste(pil_image,(POSX,POSY))
				except:
					L4log("Error Picon",ret)

# aktive Sendernummer
	def putChannelNum((ConfigPos, ConfigSize, ConfigAlign, ConfigBackColor, ConfigColor, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		num=self.Lchannel_num
		if num == "None":
			num = ""
#		print "Channel Number", num
		if num != "":
			if len(num) == 1:
				num = " " + num + " "
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			w,h = draw.textsize(num, font=font)
			lx = getSplit(False,ConfigAlign,MAX_W,w)
			if ConfigBackColor !="0":
				draw.rectangle((lx, ConfigPos, lx+w, ConfigPos+h),fill=ConfigBackColor)
			ShadowText(draw,lx,ConfigPos,num,font,ConfigColor,ConfigShadow)

# aktive Sendername
	def putChannel((ConfigPos, ConfigSize, ConfigLines, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		channel_name = ""
		if self.Lchannel_name is not None:
			channel_name = self.Lchannel_name
			ch = self.LsreftoString.split("::")
			if len(ch) > 1:
				channel_name = Code_utf8(ch[1])
		if ConfigLines == "1":
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			w,h = draw.textsize(channel_name, font=font)
			while w > MAX_W:
				ConfigSize -= 1
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				w,h = draw.textsize(channel_name, font=font)
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,w)
			ShadowText(draw,POSX,ConfigPos,channel_name,font,ConfigColor,ConfigShadow)
		else:
			writeMultiline(channel_name,ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigAlign,ConfigSplit,draw,im,ConfigFont=ConfigFont,Shadow=ConfigShadow)

# Progress Bar
	def putProgress((ConfigPos, ConfigSize, ConfigType, ConfigColor, ConfigAlign, ConfigShadowBar, ConfigShadow), draw, im):
		global isVideoPlaying
		MAX_W,MAX_H = im.size
		POSX = 0
		if ConfigAlign != "1":
			MAX_W = int(MAX_W/2)
			if ConfigAlign == "2":
				POSX=MAX_W 
		isVideoPlaying = 0
		isData = False
		event_run=0
		ProgressBar = MAX_W-20
		if self.LsreftoString is not None:
#			print "L4L",self.LsreftoString
			if ConfigType[1:] == "1":
				ms = 1.5
			elif ConfigType[1:] == "2":
				ms = 2
			else:
				ms = 1
			font = ImageFont.truetype(FONT, int(ConfigSize*ms)+8, encoding='unic') #5
			if self.Lpath: # Movie
#				print "L4L Path",self.Lpath
				isVideoPlaying = 1
				if self.Llength is not None:
#					print "L4L Len",self.Llength
					length = self.Llength
					position = self.Lposition
#					print "L4L Len",length,position
					if length and position:
#						print "L4L Len ok"
						if length[1] > 0:
#							print "L4L Len >0"
							if ConfigType[0] in ["2","4","6","8","9","A"]:
								if ConfigType[0] in ["8","9","A"]:
									dur = int(position[1]/90000)
									if dur > 3600:
										remaining = "%02d:%02d:%02d" % (dur/3600,dur%3600/60,dur%3600%60)
									else:
										remaining = "%02d:%02d" % (dur/60,dur%60)
								else:
									rem = int((length[1] - position[1])/90000)
									if length[1]/90000 < 600:
										remaining = "+%02d:%02d" % (rem/60,rem%60)
									else:
										remaining = "%+d min" % (rem/60)
								w,h = draw.textsize(remaining, font=font)
								if ConfigType[0] in ["2","8"]:
									ProgressBar -= (w+10)
									Minus = 0
									MinusProgress = 0
								elif ConfigType[0] in ["6","A"]:
									Minus = -(ConfigSize-2+(h-ConfigSize)/2)
									MinusProgress = (w+10)
								else:
									Minus = int(h/1.5)+2
									MinusProgress = (w+10)
								ShadowText(draw,ProgressBar-MinusProgress+15+POSX, ConfigPos+1-Minus-(h-ConfigSize)/2,remaining,font,ConfigColor,ConfigShadow)
							elif ConfigType[0] in ["3","5","7"]:
								remaining = "%d %%" % int(position[1]*100/length[1])
								w,h = draw.textsize(remaining, font=font)
								if ConfigType[0] == "3":
									ProgressBar -= (w+10)
									Minus = 0
									MinusProgress = 0
								elif ConfigType[0] == "7":
									Minus = -(ConfigSize-2+(h-ConfigSize)/2)
									MinusProgress = (w+10)
								else:
									Minus = int(h/1.5)+2
									MinusProgress = (w+10)
								ShadowText(draw,ProgressBar-MinusProgress+15+POSX, ConfigPos+1-Minus-(h-ConfigSize)/2,remaining,font,ConfigColor,ConfigShadow)
							event_run=int(ProgressBar*position[1]/length[1])
							isData = True
#						if remaining > 0:
#							remaining = remaining / 90000
			else: # DVB 
				event_begin, event_end, duration, event_name = self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0
#				print "L4L DVB",event_begin, event_end, duration, event_name
				if event_begin != 0:
#					print "L4L DVB Begin",event_begin
					now = int(time())
					event_run = now - event_begin
					if ConfigType[0] in ["2","4","6","8","9","A"]:
						dur = int((event_run)/60)
						if ConfigType[0] in ["8","9","A"]:
							if dur > 3600:
								remaining = "%02d:%02d:%02d" % (dur/3600,dur%3600/60,dur%3600%60)
							else:
								remaining = "%02d:%02d" % (dur/60,dur%60)
						else:
							remaining = "%+d min" % int((event_end - now)/60)
						w,h = draw.textsize(remaining, font=font)
						if ConfigType[0] in ["2","8"]:
							ProgressBar -= (w+10)
							Minus = 0
							MinusProgress = 0
						elif ConfigType[0] in ["6","A"]:
							Minus = -(ConfigSize-2+(h-ConfigSize)/2)
							MinusProgress = (w+10)
						else:
							Minus = int(h/1.5)+2
							MinusProgress = (w+10)
						ShadowText(draw,ProgressBar-MinusProgress+15+POSX, ConfigPos+1-Minus-(h-ConfigSize)/2,remaining,font,ConfigColor,ConfigShadow)
					elif ConfigType[0] in ["3","5","7"]:
						remaining = "%d %%" % int(event_run*100/duration)
						w,h = draw.textsize(remaining, font=font)
						if ConfigType[0] == "3":
							ProgressBar -= (w+10)
							Minus = 0
							MinusProgress = 0
						elif ConfigType[0] == "7":
							Minus = -(ConfigSize-2+(h-ConfigSize)/2)
							MinusProgress = (w+10)
						else:
							Minus = int(h/1.5)+2
							MinusProgress = (w+10)
						ShadowText(draw,ProgressBar-MinusProgress+15+POSX, ConfigPos+1-Minus-(h-ConfigSize)/2,remaining,font,ConfigColor,ConfigShadow)
					event_run = int(ProgressBar*event_run/duration)
					isData = True
#					print event_begin, event_end, event.getDuration(), event.getPlayPosition()
			if isData == True:
#				print "L4L isdata"
				if event_run <0:
					event_run = 0
				if event_run > ProgressBar:
					event_run = ProgressBar
				draw.rectangle((POSX+9,ConfigPos,POSX+ProgressBar+11,ConfigPos+ConfigSize),outline=ConfigColor)
				draw.rectangle((POSX+10,ConfigPos,POSX+event_run+10,ConfigPos+ConfigSize),fill=ConfigColor)
				if ConfigShadowBar == True:
					if os.path.isfile(os.path.join(Data,"progress.png")):
						try:
							imW = Image.open(os.path.join(Data,"progress.png"))
							imW = imW.resize((event_run,ConfigSize))
							im.paste(imW,(POSX+10,ConfigPos),imW)
						except:
							L4log("Progress Shade Error")

# Popup Text
	def putPopup((ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign), draw, im):
			writeMultiline(codecs.decode(PopText[1].replace("\r",""),"latin").encode("utf-8"),ConfigSize,ConfigPos,10,ConfigColor,ConfigAlign,False,draw,im,ConfigBackColor=ConfigBackColor)
			writeMultiline(PopText[0],int(ConfigSize/2.5),ConfigPos-int(ConfigSize/2.5),1,ConfigColor,ConfigAlign,False,draw,im,ConfigBackColor=ConfigBackColor)
#			writeMultiline2(FL3,int(MAX_H/8),int(MAX_H/27),3,LCD4linux.FritzPopupColor.value,int(MAX_W/3)-int(MAX_W/30),int(MAX_W/1.5),draw,im)
# Volume
	def putVol((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow), draw, im):
		MAX_W,MAX_H = im.size
		POSX = 0
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
			if ConfigAlign == "1":
				POSX=int(MAX_W/2)
			elif ConfigAlign == "2":
				POSX=MAX_W 
		ProgressBar = MAX_W-20-ConfigSize
		vol = self.Lvol
		if vol is not None:
			font = ImageFont.truetype(FONT, int(ConfigSize*1.4), encoding='unic')
			w,h = draw.textsize(str(vol), font=font)
			ProgressBar -= (w+10)
			draw.text((ProgressBar+15+POSX+ConfigSize, ConfigPos-(h-ConfigSize)/2),str(vol), font=font, fill=ConfigColor)
			draw.rectangle((POSX+9+ConfigSize,ConfigPos,POSX+ConfigSize+ProgressBar+11,ConfigPos+ConfigSize),outline=ConfigColor)
			draw.rectangle((POSX+10+ConfigSize,ConfigPos,POSX+ConfigSize+int(ProgressBar*vol/100)+10,ConfigPos+ConfigSize),fill=ConfigColor)
			if ConfigShadow == True:
				if os.path.isfile(os.path.join(Data,"progress.png")):
					try:
						imW = Image.open(os.path.join(Data,"progress.png"))
						imW = imW.resize((int(ProgressBar*vol/100),ConfigSize))
						im.paste(imW,(POSX+10+ConfigSize,ConfigPos),imW)
					except:
						L4log("Vol Shade Error")
			pil_image = Image.open(Data + "speaker.png")
			pil_image = pil_image.resize((ConfigSize+1, ConfigSize+1))
			if LCD4linux.PiconTransparenz.value == "2":
				pil_image = pil_image.convert("RGBA")
				im.paste(pil_image,(POSX+5,ConfigPos),pil_image)
			else:
				im.paste(pil_image,(POSX+5,ConfigPos))

# Provider
	def putProv((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigType, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		POSX = 0
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		if self.Lprovider is not None:
			provider = self.Lprovider
			L4logE("Provider",provider)
			if ConfigType == "2":
				if os.path.isfile(os.path.join(LCD4linux.ProvPath.value,provider.upper() + ".png")):
					pic = os.path.join(LCD4linux.ProvPath.value,provider.upper() + ".png")
				elif os.path.isfile(os.path.join(LCD4linux.ProvPath.value,"picon_default.png")):
					pic = os.path.join(LCD4linux.ProvPath.value,"picon_default.png")
				else:
					pic = ""
				try:
					if pic != "":
						imW = Image.open(pic)
						xx,yy = imW.size
						CS=int(ConfigSize*1.5)
						x=int(float(CS)/yy*xx)
						imW = imW.resize((x,CS))
						POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
						if LCD4linux.PiconTransparenz.value == "2":
							imW = imW.convert("RGBA")
							im.paste(imW,(POSX,ConfigPos),imW)
						else:
							im.paste(imW,(POSX,ConfigPos))
				except:
					pass
			else:
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				w,h = draw.textsize(provider, font=font)
				lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,w)
				ShadowText(draw,lx,ConfigPos,provider,font,ConfigColor,ConfigShadow)

# Satellit
	def putSat((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigType, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		POSX = 0
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		if self.LtransponderData is not None:
			transponderData = self.LtransponderData
			orbital = 0
			if isinstance(transponderData, float):
				L4logE("Transponder Float?")
				return
			if transponderData.has_key("tuner_type"):
				orbital=""
				if (transponderData["tuner_type"] == "DVB-S") or (transponderData["tuner_type"] == "DVB-S2"):
					orbital = transponderData["orbital_position"]
					orbital = int(orbital)
					if orbital > 1800:
						orbital = str((float(3600 - orbital))/10.0) + "W"
					else:
						orbital = str((float(orbital))/10.0) + "E"
					if ConfigType == "1":
						if len(SAT)==0 and os.path.isfile("/etc/tuxbox/satellites.xml"):
							satXml = parseE("/etc/tuxbox/satellites.xml").getroot()
							if satXml is not None:
								L4log("parsing satellites...")
								for sat in satXml.findall("sat"):
									name = sat.get("name") or None
									position = sat.get("position") or None
									if name is not None and position is not None:
										position = "%s.%s" % (position[:-1], position[-1:])
										if position.startswith("-"):
											position = "%sW" % position[1:]
										else:
											position = "%sE" % position
										if position.startswith("."):
											position = "0%s" % position
										SAT[position]=name
										L4logE(position,name)
						orbital = SAT.get(orbital,orbital)
				else:
					orbital = transponderData["tuner_type"]
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				w,h = draw.textsize(orbital, font=font)
				if ConfigType[0] == "2" and os.path.isfile(os.path.join(LCD4linux.SatPath.value,orbital.replace(".","") + ".png")):
					try:
						imW = Image.open(os.path.join(LCD4linux.SatPath.value,orbital.replace(".","") + ".png"))
						xx,yy = imW.size
						CS=int(ConfigSize*1.5)
						x=int(float(CS)/yy*xx)
						imW = imW.resize((x,CS))
						x1 = x
						if ConfigType[1:] in ["A","C"]:
							x1 += w
						POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
						if ConfigType[1:] == "A":
							ShadowText(draw,POSX,ConfigPos+int(ConfigSize/4),orbital,font,ConfigColor,ConfigShadow)
							POSX += w
						if LCD4linux.PiconTransparenz.value == "2":
							imW = imW.convert("RGBA")
							im.paste(imW,(POSX,ConfigPos),imW)
						else:
							im.paste(imW,(POSX,ConfigPos))
						POSX += x
						if ConfigType[1:] == "C":
							ShadowText(draw,POSX,ConfigPos+int(ConfigSize/4),orbital,font,ConfigColor,ConfigShadow)
						if ConfigType[1:] == "B":
							ShadowText(draw,POSX-int((x-w)/2),ConfigPos+CS,orbital,font,ConfigColor,ConfigShadow)
					except:
						pass
				else:
					lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,w)
					ShadowText(draw,lx,ConfigPos,orbital,font,ConfigColor,ConfigShadow)

# Signalstaerke Balken
	def putSignal((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigGradient), draw, im):
		MAX_W,MAX_H = im.size
		POSX = 0
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
			if ConfigAlign == "1":
				POSX=int(MAX_W/2)
			elif ConfigAlign == "2":
				POSX=MAX_W 
		if self.LsignalQuality is not None:
			ProgressBar = MAX_W-20
			staerkeVal = self.LsignalQuality * 100 / 65536
			staerkeVal2 = staerkeVal
			if staerkeVal2 < int(LCD4linux.SignalMin.value):
				staerkeVal2 = int(LCD4linux.SignalMin.value)
			elif staerkeVal2 > int(LCD4linux.SignalMax.value):
				staerkeVal2 = int(LCD4linux.SignalMax.value)
			staerke = 100*(staerkeVal2-int(LCD4linux.SignalMin.value))/(int(LCD4linux.SignalMax.value)-int(LCD4linux.SignalMin.value))
			S = 2.0 if ConfigSize <= 10 else 1.4
			font = ImageFont.truetype(FONT, int(ConfigSize*S), encoding='unic')
			w,h = draw.textsize(str(staerkeVal), font=font)
			ProgressBar -= (w+10)
			draw.text((ProgressBar+15+POSX, ConfigPos-(h-ConfigSize)/2),str(staerkeVal), font=font, fill=ConfigColor)
			if ConfigGradient == True:
				if os.path.isfile(os.path.join(Data,"gradient.png")):
					try:
						imW = Image.open(os.path.join(Data,"gradient.png"))
						imW = imW.resize((ProgressBar,ConfigSize))
						imW = imW.transpose(Image.FLIP_LEFT_RIGHT)
						imW = imW.crop((0,0,int(ProgressBar*staerke/100),ConfigSize))
						im.paste(imW,(POSX+10,ConfigPos))
					except:
						pass
				draw.rectangle((POSX+9,ConfigPos,POSX+ProgressBar+11,ConfigPos+ConfigSize),outline="yellow")
			else:
				draw.rectangle((POSX+9,ConfigPos,POSX+ProgressBar+11,ConfigPos+ConfigSize),outline=ConfigColor)
				draw.rectangle((POSX+10,ConfigPos,POSX+int(ProgressBar*staerke/100)+10,ConfigPos+ConfigSize),fill=ConfigColor)

# aktive Event
	def putProg((ConfigPos, ConfigSize, ConfigLines, ConfigType, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont), draw, im):
		event_begin, event_end, duration, event_name = self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0
		if event_begin != 0:
			begin = strftime("%H:%M", localtime(event_begin))
			ende = strftime("%H:%M", localtime(event_end))
			sts = ""
			if ConfigType in ["1","3"]:
				sts = begin +" - " + ende
				if ConfigType == "3":
					now = int(time())
					sts += "  (%+d min)" % int((event_end - now)/60)
				sts += "\n"
			sts += event_name
			writeMultiline(sts,ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigAlign,ConfigSplit,draw,im,ConfigFont=ConfigFont,Shadow=ConfigShadow)

# next Event
	def putProgNext((ConfigPos, ConfigSize, ConfigLines, ConfigType, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont), draw, im):
		if ConfigType == "4":
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			MAX_W,MAX_H = im.size
			POSY = ConfigPos
			POSX = 0 
			if ConfigAlign == "0":
				POSX = 0
			elif ConfigAlign == "1":
				POSX = int(MAX_W/4)
			elif ConfigAlign == "2":
				POSX = int(MAX_W/2)
			else:
				POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,int(MAX_W/2))
			sts = ""
			if self.LEventsNext is not None and len(self.LEventsNext)>0:
				L4logE("EPG-Laenge ", len(self.LEventsNext))
				lines = 1
				while lines <= int(ConfigLines) and lines < len(self.LEventsNext):
					if self.LEventsNext[lines][4]:
						t = self.LEventsNext[lines][2]
#								duration = self.LEventsNext[lines][3]
						event_name = Code_utf8(self.LEventsNext[lines][4])
						event_begin = t
#								event_end = event_begin + duration
						begin = strftime("%H:%M", localtime(event_begin))
#								ende = strftime("%H:%M", localtime(event_end))
						sts = begin + " " + event_name
						w,h = draw.textsize(sts, font=font)
						if ConfigSplit == True:
							while w > int(MAX_W/2):
								sts = sts[:-1]
								w,h = draw.textsize(sts, font=font)
						ShadowText(draw,POSX,POSY,sts,font,ConfigColor,ConfigShadow)
						POSY += h
					lines += 1
		else:
			event_begin, event_end, duration, event_name = self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1
			if event_begin != 0:
				begin = strftime("%H:%M", localtime(event_begin))
				ende = strftime("%H:%M", localtime(event_end))
				sts = ""
				if ConfigType in ["1","3"]:
					sts = begin
					if ConfigType == "1":
						sts += " - " + ende
					elif ConfigType == "3":
						sts += " (%d min)" % int((event_end - event_begin)/60)
					sts += "\n"
				sts += event_name
				writeMultiline(sts,ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigAlign,ConfigSplit,draw,im,ConfigFont=ConfigFont,Shadow=ConfigShadow)

# show extended Description
	def putDescription((ConfigPos, ConfigSize, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, ConfigType, ConfigShadow, ConfigFont), draw, im):
		event_name = ""
		if self.LEventsDesc is not None and len(self.LEventsDesc)>0:
			if self.LEventsDesc[0][4]:
				if self.LEventsDesc[0][5] != "" and (ConfigType[0] == "1" or (ConfigType[0] == "2" and self.LEventsDesc[0][6] == "")):
					event_name += self.LEventsDesc[0][5] + "\n"
				if self.LEventsDesc[0][6] != "" and (ConfigType[1] == "1" or (ConfigType[1] == "2" and self.LEventsDesc[0][5] == "")):
					event_name += self.LEventsDesc[0][6]
		if event_name == "":
			if self.LShortDescription is not None and self.LExtendedDescription is not None:
					if self.LShortDescription != "" and (ConfigType[0] == "1" or (ConfigType[0] == "2" and self.LExtendedDescription == "")):
						event_name += self.LShortDescription + "\n"
					if self.LExtendedDescription != "" and (ConfigType[1] == "1" or (ConfigType[1] == "2" and self.LShortDescription == "")):
						event_name += self.LExtendedDescription
		if ConfigMode == True and event_name == "":
			for i in range(1,21): event_name+="Description%d\n" % i 
		writeMultiline(event_name.replace("\x8A","\n"),ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigAlign,ConfigSplit,draw,im,ConfigFont=ConfigFont,Shadow=ConfigShadow)

# Tuner
	def putTuner((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType, ConfigActive, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		number = -1
		if self.Ltuner_number is not None:
			number = self.Ltuner_number
		i = ""
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		w,h = draw.textsize("A ", font=font)
		if ConfigType == "0":
			if ConfigActive == True:
				Tcount = 0
				count = 1
				for x in range(TunerCount):
					if TunerMask & count != 0:
						Tcount += 1
					count *= 2
			else:
				Tcount = TunerCount
			lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,int(w*Tcount))
		else:
			lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,w)
		if ConfigAlign == "0":
			w1,h1 = draw.textsize(" ", font=font)
			lx += w1
		ly = ConfigPos
		count = 1
		for x in range(TunerCount):
			isON = True
			if TunerMask & count != 0:
				if x == number:
					c = LCD4linux.TunerColorActive.value
				else:
					c = LCD4linux.TunerColorOn.value
			else:
				c = LCD4linux.TunerColor.value
				isON = False
			count *= 2
			w1,h1 = draw.textsize("A", font=font)
			if isON:
				draw.rectangle((lx-1,ly,lx+w1,ly+h1), outline=c, fill="black")
			if (ConfigActive == True and isON) or ConfigActive == False:
				draw.text((lx, ly), chr(ord('A') + x), font=font, fill=c)
				if ConfigType == "0":
					lx += w
				else:
					ly += h+1

# TunerInfo + Sensors
	def putInfo((ConfigPos, ConfigSize, ConfigAlign, ConfigLines, ConfigSplit, ConfigColor, ConfigInfo, ConfigShadow, ConfigFont), draw, im):
		def NL(count):
			return "\n" if int(count)>2 else ""
		global CPUtotal
		global CPUidle
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		i = ""
		if self.LsignalQualitydB is not None:
			if "A" in ConfigInfo:
				i += " %3.02fdB%s" % (self.LsignalQualitydB / 100.0,NL(ConfigLines))
			if "B" in ConfigInfo:
				i += " %d%%%s" % (self.LsignalQuality * 100 / 65536,NL(ConfigLines))
			if "C" in ConfigInfo:
				i += " %d%s" % (self.LbitErrorRate,NL(ConfigLines))
#			print "%d" % (feinfo.getFrontendInfo(iFrontendInformation.signalPower))
		if "T" in ConfigInfo:
			m1 = 0
			if os.path.exists("/proc/stb/sensors"):
				for dirname in os.listdir("/proc/stb/sensors"):
					if dirname.find("temp", 0, 4) == 0:
						if os.path.isfile("/proc/stb/sensors/%s/value" % dirname) == True:
							tt = int(open("/proc/stb/sensors/%s/value" % dirname, "r").readline().strip())
							if m1 < tt:
								m1 = tt
			i += " %d\xb0C%s" % (m1,NL(ConfigLines))
		if "R" in ConfigInfo:
			if os.path.isfile("/proc/stb/fp/fan_speed"):
				value = int(open("/proc/stb/fp/fan_speed", "r").readline().strip()[:-4])
				i += " %drpm%s" % (int(value / 2),NL(ConfigLines))
		elif "r" in ConfigInfo:
			if os.path.isfile("/proc/stb/fp/fan_speed"):
				value = int(open("/proc/stb/fp/fan_speed", "r").readline().strip()[:-4])
				i += " %drpm%s" % (int(value),NL(ConfigLines))
		if "P" in ConfigInfo:
			if os.path.isfile("/proc/stat"):
				v = open("/proc/stat", "r").readline().split()
				w = int(v[1])+int(v[2])+int(v[3])+int(v[4])
				wa = w-CPUtotal
				wi = int(v[4])-CPUidle
				if wa*wi > 0:
					x = 100-100.0/wa*wi
				else:
					x = 0
				i += " %.01f%%%s" % (x,NL(ConfigLines))
				CPUtotal = w
				CPUidle = int(v[4])
		if "L" in ConfigInfo:
			if os.path.isfile("/proc/loadavg"):
				v = open("/proc/loadavg", "r").readline().split()
				i += " %s%s" % (v[int(ConfigInfo[ConfigInfo.find("L")+1])],NL(ConfigLines))
		writeMultiline(i,ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigAlign,ConfigSplit,draw,im,False, ConfigFont=ConfigFont, Shadow=ConfigShadow)

# Audio/Video
	def putAV((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigType, ConfigFont), draw, im):
		def getAudio(description):
			if description in ["AC3", "AC-3", "Dolby Digital", "AC-3 audio"]:
				return "dolby.png"
			elif "DTS-HD" in description:
				return "dtsHD.png"
			elif "DTS" in description:
				return "dts.png"
			elif description in ["Dolby Digital+", "AC3+"]:
				return "dolbyplus.png"
			else:
				return "mpeg.png"

		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		if self.LsVideoWidth is not None and self.LsVideoHeight is not None:
			dat = "mpeg.png"
			if self.Laudiodescription is not None:
				dat = getAudio(self.Laudiodescription)
			Video = "%dx%d" % (self.LsVideoWidth,self.LsVideoHeight)
			if len(Video)<6:
				Video = ""
			font = ImageFont.truetype(ConfigFont, ConfigSize-2, encoding='unic')
			w,h = draw.textsize(Video, font=font)
			px = 75.0/ConfigSize
			cl = int(375/px)+15
			if ConfigType == "1":
				cl += w
			lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,cl)
			pil_image = None
			if os.path.isfile(Data+dat):
				pil_image = Image.open(Data+dat)
				pil_image = pil_image.resize((int(200/px), ConfigSize))
				im.paste(pil_image,(lx,ConfigPos))
			if self.LsAspect in (3, 4, 7, 8, 0xB, 0xC, 0xF, 0x10):
				pil_image = Image.open(Data+"widescreen.png")
			else:
				pil_image = Image.open(Data+"letterbox.png")
			pil_image = pil_image.resize((int(100/px), ConfigSize))
			im.paste(pil_image,(lx+int(200/px)+5,ConfigPos))
			try:
				if self.LsIsCrypted == 1:
					pil_image = Image.open(Data+"crypted.png")
				else:
					pil_image = Image.open(Data+"open.png")
				pil_image = pil_image.resize((ConfigSize, ConfigSize))
				im.paste(pil_image,(lx+int(300/px)+10,ConfigPos))
			except:
				L4log("Error Crypted")
			if ConfigType == "1":
				Posx=int(375/px)+15
				Posy=ConfigPos+2
			else:
				Posx=(int(375/px/2)) - int(w/2)
				Posy=ConfigPos+ConfigSize
			ShadowText(draw,lx+Posx,Posy,Video,font,ConfigColor,ConfigShadow)

# Bitrate
	def putBitrate((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		if self.LaudioBitrate != "" and self.LvideoBitrate != "":
			BIT = "%d | %d kbit/s" % (self.LvideoBitrate,self.LaudioBitrate)
			w,h = draw.textsize(BIT, font=font)
			lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,w)
			ShadowText(draw,lx,ConfigPos,BIT,font,ConfigColor,ConfigShadow)
		elif BitrateRegistred == False:
			ShadowText(draw,0,ConfigPos,"no Bitrate-Plugin",font,ConfigColor,ConfigShadow)

# Online-Ping
	def putOnline((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigType, ConfigShow, ConfigTimeout, ConfigList, ConfigShadow, ConfigFont), draw, im):
		if OSDtimer < 0:
			return
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		co = 0
		cl = 0
		cm = 0
		h = 0
		for l in ConfigList:
			if len(l)>1:
				T = (l+":").split(":")
				w,h = draw.textsize(T[0], font=font)
				if cm<w:
					cm=w
				cl += (h+10+w)
				co += 1
		if ConfigType == "2":
			cl = cm+10+h
		ly = ConfigPos
		lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,cl)
		for l in ConfigList:
			if len(l)>1:
				T = (l+":").split(":")
				TT = T[1] if len(T[1])>0 else T[0]
				w,h = draw.textsize(T[0], font=font)
				c = "red"
				r = None
				try:
					r = ping.doOne(TT,ConfigTimeout/1000.0)
					L4logE(TT,r)
					if r != None and r <= ConfigTimeout/1000.0:
						c = "lime"
					if ConfigShow=="0" or (ConfigShow=="1" and c=="lime") or (ConfigShow=="2" and c=="red"):
						draw.ellipse((lx+2, ly+2, lx+h-2, ly+h-2), fill=c) 
						ShadowText(draw,lx+h+5,ly,T[0],font,ConfigColor,ConfigShadow)
						if ConfigType == "2":
							ly += h
					if ConfigType == "0":
						lx += (h+10+w)
				except:
					L4log("Ping-Error",TT)

# Data-Devices
	def putDev((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigList, ConfigShadow, ConfigType, ConfigFont), draw, im):
		global DeviceRemove
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		w,h = draw.textsize("MByte", font=font)
		if ConfigType == "0":
			co = 0
			for l in ConfigList:
				if len(l)>0:
					co += 1
		else:
			co = 1
		ly = ConfigPos
		lx = getSplit(ConfigSplit,ConfigAlign,MAX_W,(w+20)*co)
		for l in ConfigList:
			if l not in DeviceRemove and (os.path.isdir(l) == True or l == "RAM"):
				L4logE("Device",l)
				G = 0
				F = 0
				if l == "RAM":
					G, F = getMem()
				else:
					try:
						s=os.statvfs(l)
						G = s.f_bsize*s.f_blocks
						F = s.f_bsize*s.f_bavail
						if G == 0 and LCD4linux.DevForceRead.value == True:
							L4logE("Device force Reading")
							tmp = glob.glob(os.path.normpath(l)+"/*")
							s=os.statvfs(l)
							G = s.f_bsize*s.f_blocks
							F = s.f_bsize*s.f_bavail
					except:
						L4log("Error Device",l)
				if G > 0:
					Fproz = int(F*100/G) if F > 0 else 0
					Fpixel = ((2*h)*Fproz/100)
					Fe = F
					Einh = ""
					if Fe > 1000:
						Fe /= 1024.0
						Einh = "k"
					if Fe > 1000:
						Fe /= 1024.0
						Einh = "M"
					if Fe > 1000:
						Fe /= 1024.0
						Einh = "G"
					if Fe > 1000:
						Fe /= 1024.0
						Einh = "T"
					ShadowText(draw,lx+20,ly,"%.1f" % Fe,font,ConfigColor,ConfigShadow)
					ShadowText(draw,lx+20,ly+h,"%sByte" % Einh,font,ConfigColor,ConfigShadow)
					draw.rectangle((lx+8,ly,lx+18,ly+(2*h)), outline="lime", fill="lime")
					draw.rectangle((lx+8,ly,lx+18,ly+Fpixel), outline="yellow", fill="yellow")
					if ConfigType == "0":
						lx += w+20
					else:
						ly += 2*h+3
				else:
					L4log("remove Device",l)
					DeviceRemove.append(l)
			else:
				if l not in DeviceRemove:
					L4log("remove Device",l)
					DeviceRemove.append(l)

# HDD
	def putHdd((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		hddsleep = True
		from Components.Harddisk import harddiskmanager
		if harddiskmanager.HDDCount() > 0:
			for hdd in harddiskmanager.HDDList():
#				print hdd[0], hdd[1]
				if hdd[1].model().startswith("ATA"):
					if not hdd[1].isSleeping():
						hddsleep = False
			try:
				if ConfigType == "0" or (ConfigType == "1" and hddsleep == False):
					if hddsleep == True:
						imW = Image.open(os.path.join(Data,"HDDs.png"))
					else:
						imW = Image.open(os.path.join(Data,"HDDa.png"))
					xx,yy = imW.size
					x=int(float(ConfigSize)/yy*xx)
					imW = imW.resize((x,ConfigSize))
					POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
					if LCD4linux.PiconTransparenz.value == "2":
						imW = imW.convert("RGBA")
						im.paste(imW,(POSX,ConfigPos),imW)
					else:
						im.paste(imW,(POSX,ConfigPos))
			except:
				pass

# show OSCAM
	def putOSCAM((ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigSplit), draw, im):
		MAX_W,MAX_H = im.size
		OSCAMrunning = False
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,MAX_W)
		if os.path.isfile(LCD4linux.OSCAMFile.value):
			current_h=ConfigPos
			if time()-os.path.getmtime(LCD4linux.OSCAMFile.value) < 30:
				OSCAMrunning = True
				font = ImageFont.truetype(FONT, ConfigSize, encoding='unic')
				p=[160,12.8,3.2,2,1.78,1.6,1.45,1.33]

				for line in open(LCD4linux.OSCAMFile.value,"r").readlines():
					line = Code_utf8(line.replace('\n',''))
					w,h = draw.textsize(line, font=font)
					if ConfigBackColor !="0":
						if line.find(" Label ") > 0:
							draw.rectangle((POSX, current_h, POSX+MAX_W, current_h+h),fill=ConfigColor)
						else:
							draw.rectangle((POSX, current_h, POSX+MAX_W, current_h+h),fill=ConfigBackColor)
					if "|" in line:
						ll = line.split("|")
						if len(ll)==4:
							p=[160,10.67,2.91,1.14,1.03]
						elif len(ll)==5:
							p=[160,10.67,2.91,1.78,1.14,1.03]
						else:	
							p=[160,10.67,2.91,1.78,1.6,1.45,1.33,1.14,1.03]
						for x in range(len(ll)):
							if line.find(" Label ") > 0 and ConfigBackColor !="0":
								draw.text((POSX+int(MAX_W/p[x]), current_h), ll[x].strip(), font=font, fill=ConfigBackColor)
							else:
								draw.text((POSX+int(MAX_W/p[x]), current_h), ll[x].strip(), font=font, fill=ConfigColor)
						current_h+=h
		if OSCAMrunning == False:
			font = ImageFont.truetype(FONT, ConfigSize+13, encoding='unic')
			w,h = draw.textsize(Code_utf8(_("OSCAM not running")), font=font)
			draw.rectangle((POSX, ConfigPos, POSX+MAX_W, ConfigPos+h),fill=ConfigBackColor)
			draw.text((POSX+(MAX_W-w)/2, ConfigPos), Code_utf8(_("OSCAM not running")), font=font, fill=ConfigColor)

# shoe ecm.info
	def putECM((ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigSplit), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,MAX_W)
		if os.path.isfile("/tmp/ecm.info"):
			info = {}
			for line in open("/tmp/ecm.info", 'r').readlines():
				d = line.split(':', 1)
				if len(d) > 1:
					info[d[0].strip()] = d[1].strip()
			t = "Caid,Pid,Reader,From,Protocol,Hops,Ecm Time"
			tl = t.split(",")
			p=[160,7.11,3.56,2.37,1.68,1.31,1.19,1.01]
			font = ImageFont.truetype(FONT, ConfigSize, encoding='unic')
			w,h = draw.textsize(t, font=font)
			if ConfigBackColor !="0":
				draw.rectangle((POSX, ConfigPos, POSX+MAX_W, ConfigPos+h),fill=ConfigColor)
			for x in range(len(tl)):
				if ConfigBackColor !="0":
					draw.text((POSX+int(MAX_W/p[x]), ConfigPos), tl[x], font=font, fill=ConfigBackColor)
				else:
					draw.text((POSX+int(MAX_W/p[x]), ConfigPos), tl[x], font=font, fill=ConfigColor)
			ConfigPos += h
			if ConfigBackColor !="0":
				draw.rectangle((POSX, ConfigPos, POSX+MAX_W, ConfigPos+h),fill=ConfigBackColor)
			for x in range(len(tl)):
				draw.text((POSX+int(MAX_W/p[x]), ConfigPos), info.get(tl[x].lower(),""), font=font, fill=ConfigColor)

# show Title
	def putTitle((ConfigPos, ConfigSize, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		Title = ""
		if self.LsreftoString is not None:
			sref = self.LsreftoString
			sreffile = sref[sref.rfind(":")+1:]
			audio = None
			if sreffile.lower().endswith(".mp3"):
				MP3title=""
				MP3artist=""
				MP3album=""
				try:
					audio = MP3(sreffile, ID3 = EasyID3)
				except:
					audio = None
				if audio:
					MP3title = audio.get('title', [''])[0]
					MP3artist = audio.get('artist', [''])[0]
					MP3album = audio.get('album', [''])[0]
					Title = "%s - %s" % (MP3artist,MP3title)
					if len(Title) < 5:
						Title = ""
			if Title == "":
				if self.LsTagTitle is not None:
					Title = self.LsTagTitle
					Video = Title.endswith(".mpg") or Title.endswith(".vob") or Title.endswith(".avi") or Title.endswith(".divx") or Title.endswith(".mv4") or Title.endswith(".mkv") or Title.endswith(".mp4") or Title.endswith(".ts")
					if Title == "" or Video == True:
						Title = self.LgetName
						Title = Title.replace(".mpg","").replace(".vob","").replace(".avi","").replace(".divx","").replace(".mv4","").replace(".mkv","").replace(".mp4","").replace(".ts","")
					if Title.find(" ") > 20 or (Title.find(" ") == -1 and len(Title) > 20):
						Title = Title.replace("."," ")
				if ConfigMode == True:
					Title = "Title1\nTitle2 Text\nTitle3"
			writeMultiline(Title,ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigAlign,ConfigSplit,draw,im,ConfigFont=ConfigFont,Shadow=ConfigShadow)

# show Comm_ents
	def putComm((ConfigPos, ConfigSize, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		if self.LsTagArtist is not None:
			Info = ""
			if WebRadioFSok == True and self.l4l_info.get("Station","") != "":
				Info += self.l4l_info.get("Station","") + " - "
				if self.l4l_info.get("Fav","") != "":
					Info += self.l4l_info.get("Fav","") + " - "
			I = self.LsTagArtist
			if I is not None and I != "":
				Info += I + "\n"
			I = self.LsTagGenre
			if I is not None and I != "":
				Info += I + "\n"
			if isMediaPlayer == "record":
				event_begin, event_end, duration, event_name = self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0
#				print event_begin, event_end, duration, event_name
				if event_begin != 0:
					if isMediaPlayer == "record":
						Info += strftime("%d.%m.%G ", localtime(event_begin))
					Info += strftime("%H:%M ", localtime(event_begin))
					if self.Llength is not None:
						length = self.Llength
						if length[1] > 0:
							duration = length[1]/90000
						if duration > 0:
							Info += " (%d min) " % (duration/60)
					Info += event_name + "\n"
				event_begin, event_end, duration, event_name = self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1
				if event_begin != 0:
					Info += strftime("%H:%M ", localtime(event_begin)) + event_name
			if ConfigMode == True:
				Info = "Info1\nInfo2 Text\nInfo3"
			writeMultiline(Info,ConfigSize,ConfigPos,ConfigLines,ConfigColor,ConfigAlign,ConfigSplit,draw,im,ConfigFont=ConfigFont,Shadow=ConfigShadow)

# show Fritz Pictures
	def putFritzPic((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit), draw, im):
		if (len(FritzList) == 0 and ConfigMode == False) or LCD4linux.FritzPictures.value == "0":
			return
		MAX_Wi,MAX_Hi = im.size
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		if os.path.isfile(PICfritz):
			try:
				pil_image = Image.open(PICfritz)
				x,y = pil_image.size
				POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
				im.paste(pil_image,(POSX,ConfigPos))
			except:
				pass
		elif ConfigMode == True and len(FritzList) == 0:
			imW = Image.open(FritzPic)
			xx,yy = imW.size
			x=int(float(ConfigSize)/yy*xx)
			imW = imW.resize((x,ConfigSize))
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
			im.paste(imW,(POSX,ConfigPos))
		else:
			if LCD4linux.FritzPictureType.value == "0":
				imW = Image.new('RGB', (MAX_Wi, ConfigSize), (0, 0, 0, 0))
			else:
				imW = Image.new('RGB', (ConfigSize, MAX_Hi), (0, 0, 0, 0))
			PX=0
			PXmax=0
			x=0
			i=0
			PY=0
			for Fx in reversed(FritzList):
				if i<int(LCD4linux.FritzPictures.value):
					Bildname = ""
					Rufname = Fx[3].split("\n")[0].split(",")[0].strip()
					if "1" in LCD4linux.FritzPictureSearch.value:
						if os.path.isfile(os.path.join(LCD4linux.FritzPath.value,Fx[2] + ".png")):
							Bildname = os.path.join(LCD4linux.FritzPath.value,Fx[2] + ".png")
						elif os.path.isfile(os.path.join(LCD4linux.FritzPath.value,Rufname + ".png")):
							Bildname = os.path.join(LCD4linux.FritzPath.value,Rufname + ".png")
						elif os.path.isfile(os.path.join(LCD4linux.FritzPath.value,Rufname.split("(")[0].strip() + ".png")):
							Bildname = os.path.join(LCD4linux.FritzPath.value,Rufname.split("(")[0].strip() + ".png")
					if Bildname == "" and "2" in LCD4linux.FritzPictureSearch.value:
						for k in range(len(Fx[2]), 0, -1):
							if os.path.isfile(os.path.join(LCD4linux.FritzPath.value, Fx[2][:k] + ".png")):
								Bildname = os.path.join(LCD4linux.FritzPath.value, Fx[2][:k] + ".png")
								break
					if Bildname == "":
						if os.path.isfile(os.path.join(LCD4linux.FritzPath.value,"default.png")):
							pil_image = Image.open(os.path.join(LCD4linux.FritzPath.value,"default.png"))
						else:
							pil_image = Image.open(FritzPic)
					else:
						pil_image = Image.open(Bildname)

					xx,yy = pil_image.size
					x=int(float(ConfigSize)/yy*xx)
					if PXmax<x:
						PXmax=x
					pil_image = pil_image.resize((x,ConfigSize))
					imW.paste(pil_image,(PX, PY))
					if LCD4linux.FritzPictureType.value == "0":
						PX += x
					else:
						PY += ConfigSize
				i+=1
			if LCD4linux.FritzPictureType.value == "0":
				imW = imW.crop((0, 0, PX, ConfigSize))
			else:
				imW = imW.crop((0, 0, PXmax, PY))
			imW.save(PICfritz)
			x,y = imW.size
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_Wi,x)
			im.paste(imW,(POSX,ConfigPos))
		return

# show FritzCall
	def putFritz((ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigType, ConfigPicPos, ConfigPicSize, ConfigPicAlign, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		if FritzTime > 1:
			if len(FritzList) == 0:
				return
			try:
				FL = FritzList[len(FritzList)-1]
				if len(FL) < 5:
					return
				if os.path.isfile(LCD4linux.FritzFrame.value):
					pil_image = Image.open(LCD4linux.FritzFrame.value)
				else:
					pil_image = Image.open(FritzFrame)
				pil_image = pil_image.resize((MAX_W, MAX_H))
				im.paste(pil_image,(0,0))
				Bildname = ""
				Rufname = FL[3].split("\n")[0].split(",")[0].strip() 
				if "1" in LCD4linux.FritzPictureSearch.value:
					if os.path.isfile(os.path.join(LCD4linux.FritzPath.value,FL[2] + ".png")):
						Bildname = os.path.join(LCD4linux.FritzPath.value,FL[2] + ".png")
					elif os.path.isfile(os.path.join(LCD4linux.FritzPath.value,Rufname + ".png")):
						Bildname = os.path.join(LCD4linux.FritzPath.value,Rufname + ".png")
					elif os.path.isfile(os.path.join(LCD4linux.FritzPath.value,Rufname.split("(")[0].strip() + ".png")):
						Bildname = os.path.join(LCD4linux.FritzPath.value,Rufname.split("(")[0].strip() + ".png")
				if Bildname == "" and "2" in LCD4linux.FritzPictureSearch.value:
					for k in range(len(FL[2]), 0, -1):
						if os.path.isfile(os.path.join(LCD4linux.FritzPath.value, FL[2][:k] + ".png")):
							Bildname = os.path.join(LCD4linux.FritzPath.value, FL[2][:k] + ".png")
							break
				if Bildname == "":
					if os.path.isfile(os.path.join(LCD4linux.FritzPath.value,"default.png")):
						pil_image = Image.open(os.path.join(LCD4linux.FritzPath.value,"default.png"))
					else:
						pil_image = Image.open(FritzRing)
				else:
					pil_image = Image.open(Bildname)
				xx,yy = pil_image.size
				x=int(float(MAX_H/1.8)/yy*xx)
				pil_image = pil_image.resize((x, int(MAX_H/1.8)))
				im.paste(pil_image,(int(MAX_W/30), int((MAX_H/2.3)-(MAX_H/27))))
				FL3 = FL[3]
				if len(FL3.split("\n")) == 1:
					FL3 = "\n%s" % FL3
				writeMultiline2(FL3,int(MAX_H/8),int(MAX_H/27),3,LCD4linux.FritzPopupColor.value,int(MAX_W/3)-int(MAX_W/30),int(MAX_W/1.5),draw,im,ConfigFont=ConfigFont)
				writeMultiline2("%s\n%s\n%s" % (FL[2],FL[1],FL[4]),int(MAX_H/11),int(MAX_H*0.6),3,LCD4linux.FritzPopupColor.value,int(MAX_W/2.66)-int(MAX_W/30),int(MAX_W/1.6),draw,im,ConfigFont=ConfigFont)
			except:
				pass		
		else:
			if int(LCD4linux.FritzLines.value) > 0:
				CS=int(ConfigSize*1.8)
				event = []
				if ConfigMode == True and len(FritzList) == 0:
					event.append(["RING","01.01.2000 01:00","0123/4567890","Demo Call 1","123"])
					event.append(["OUT","01.01.2000 02:00","0123/4567890","Demo Call 2","123"])
				POSY = ConfigPos
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				w1,h1 = draw.textsize("8", font=font)
				POSX = getSplit(False,ConfigAlign,MAX_W,(30*w1))
				imW = None
				if os.path.isfile(os.path.join(Data,"fritztel.png")):
					try:
						imW = Image.open(os.path.join(Data,"fritztel.png"))
						xx,yy = imW.size
						x1=int(float(CS)/yy*xx)
						imW = imW.resize((x1,CS))
					except:
						imW = None
				w1,h1 = draw.textsize("A", font=font)
				i = 0
				for FL in reversed(FritzList+event):
					if i < int(LCD4linux.FritzLines.value):
						POSXi = POSX
						if imW is not None and "-" not in ConfigType:
							imW2 = imW
							if FL[0]!="RING":
								imW2 = imW2.transpose(Image.FLIP_LEFT_RIGHT)
							if LCD4linux.WetterTransparenz.value == "true":
								imW2 = imW2.convert("RGBA")
								im.paste(imW2,(POSX,POSY-(int(CS/10))),imW2)
							else:
								im.paste(imW2,(POSX,POSY-(int(CS/10))))
							POSXi += x1+w1
						if "T" in ConfigType: 
							event = "%s %s [%s]\n%s" % (FL[1],FL[2],FL[4].split()[0],Code_utf8(FL[3].split("\n")[0]))
						else:
							event = "%s %s\n%s" % (FL[1],FL[2],Code_utf8(FL[3].split("\n")[0]))
						for x in event.split("\n"):
							w,h = draw.textsize(x, font=font)
							if ConfigBackColor !="0":
								draw.rectangle((POSXi, POSY,POSXi+w, POSY+h),fill=ConfigBackColor)
							ShadowText(draw,POSXi, POSY, x, font, ConfigColor, ConfigShadow)
							POSY += h
					i+=1
			if len(FritzList) == 0 and len(event) == 0 and LCD4linux.ShowNoMsg.value == True:
				ShadowText(draw,POSX, POSY, _("no Calls"), font, ConfigColor, ConfigShadow)
			Para = ConfigPicPos, ConfigPicSize, ConfigPicAlign, False
			putFritzPic(Para, draw, im)

# show Mail
	def putMail((ConfigPos, ConfigSize, ConfigProzent, ConfigColor, ConfigBackColor, ConfigAlign, ConfigSplit, ConfigLines, ConfigType, ConfigProfil, ConfigShadow, ConfigFont), draw, im):
		if PopMail[5]!="":
			L4log("get Mail running")
			return
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		ConfigProfil = int(ConfigProfil)
		ConfigLines = int(ConfigLines)
		POSY = ConfigPos
		CS=int(ConfigSize*1.8)
		CW=int(MAX_W*int(ConfigProzent)/100)
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,CW)
		Konto = [LCD4linux.Mail1User.value,LCD4linux.Mail2User.value,LCD4linux.Mail3User.value,LCD4linux.Mail4User.value,LCD4linux.Mail5User.value]
		for CP in range(0,ConfigProfil):
			if len(PopMail[CP]) > 0 or LCD4linux.MailShow0.value == True:
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				if ConfigType[:1] == "A" or (ConfigType[:1] == "B" and PopMail[CP][0][2] != PopMailUid[CP][0]):
					NM = 0
					for e in PopMail[CP]:
						if e[2] != PopMailUid[CP][0]:
							NM += 1
						else:
							break
					Mtext = _("%d Mails  %d New  %s") % ( len(PopMail[CP]),NM,Code_utf8(Konto[CP].split(":")[0])) 
					POSXi = POSX
					if os.path.isfile(os.path.join(Data,"email.png")):
						try:
							imW = Image.open(os.path.join(Data,"email.png"))
							xx,yy = imW.size
							x=int(float(CS)/yy*xx)
							imW = imW.resize((x,CS))
							if LCD4linux.WetterTransparenz.value == "true":
								imW = imW.convert("RGBA")
								im.paste(imW,(POSX,POSY),imW)
							else:
								im.paste(imW,(POSX,POSY))
							w,h = draw.textsize("A", font=font)
							POSXi += x+w
						except:
							pass
					if ConfigBackColor !="0":
						w,h = draw.textsize(Mtext, font=font)
						draw.rectangle((POSXi, POSY,POSXi+w, POSY+h),fill=ConfigBackColor)
					ShadowText(draw,POSXi,POSY+int(h/5),Mtext,font,ConfigColor,ConfigShadow)
#					font = ImageFont.truetype(ConfigFont, int(ConfigSize/2), encoding='unic')
#					draw.text((POSXi, POSY+h), PopMailUid[CP][2])
					POSY += CS
				i=1
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				c = int(ConfigSize/4)
				for M in PopMail[CP]:
					if i>= int(ConfigLines) or (ConfigType[1:] == "2" and M[2] == PopMailUid[CP][0]):
						break
					i += 1
					draw.ellipse((POSX, POSY+int(ConfigSize/2)-c,POSX+(2*c), POSY+int(ConfigSize/2)+c),fill=ConfigColor)
					tx=cutText(Code_utf8(M[0]),draw,font,CW-ConfigSize)
					if ConfigBackColor !="0":
						w,h = draw.textsize(tx, font=font)
						draw.rectangle((POSX+ConfigSize, POSY,POSX+ConfigSize+w, POSY+h),fill=ConfigBackColor)
					ShadowText(draw,POSX+ConfigSize,POSY,tx,font,ConfigColor,ConfigShadow)
					POSY += ConfigSize
					tx=cutText(Code_utf8(M[1]),draw,font,CW-ConfigSize)
					if ConfigBackColor !="0":
						w,h = draw.textsize(tx, font=font)
						draw.rectangle((POSX+ConfigSize, POSY,POSX+ConfigSize+w, POSY+h),fill=ConfigBackColor)
					ShadowText(draw,POSX+ConfigSize,POSY,tx,font,ConfigColor,ConfigShadow)
					POSY += ConfigSize

# show Ereignis Icon Bar
	def putIconBar((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType, ConfigPopup, ConfigPopupLCD), draw, im):
		global SaveEventList
		global SaveEventListChanged
		MAX_W,MAX_H = im.size
		EVENTLIST = ["","",""]
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		find = ""
		for CP in range(0,5):
			if len(PopMail[CP]) > 0:
				if PopMail[CP][0][2] != PopMailUid[CP][0]:
					for e in PopMail[CP]:
						if e[2] != PopMailUid[CP][0]:
							find += "A"
							break
			if "A" in find:
				break
		EVENTLIST[0]=PopMailUid
		if ConfigMode == True and "A" not in find:
			find += "A"

		if len(FritzList) > 0:
			EVENTLIST[1]=FritzList[-1]
			find += "B"

		icount=0
		for t in sorted(ICS):
			x=datetime.strptime(t,"%Y-%m-%d")
			DTx = date(x.year,x.month,x.day)-date.today()
			if (DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value))) or ConfigMode == True:
				if "C" not in find:
					find += "C"
				icount+=1
		EVENTLIST[2] = icount
		if len(find) == 0:
			return
#		print "-----",ConfigPopup,SaveEventList,EVENTLIST
		if SaveEventList != EVENTLIST and ConfigPopup != "0" and ICSrunning == False and PopMail[5] == "" and OSDtimer >= 0 and ConfigMode == False:
			if SaveEventList != ["","",""]:
				L4log("Set Event Changed",EVENTLIST)
				for L in str(ConfigPopupLCD):
					setScreenActive(str(ConfigPopup),str(L))
#				SaveEventListChanged = True
			SaveEventList = EVENTLIST

		POSY = ConfigPos
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,ConfigSize*len(find) if ConfigType == "0" else ConfigSize)
		if "A" in find:
			if os.path.isfile(os.path.join(Data,"email.png")):
				try:
					imW = Image.open(os.path.join(Data,"email.png"))
					imW = imW.resize((ConfigSize,ConfigSize))
					if LCD4linux.WetterTransparenz.value == "true":
						imW = imW.convert("RGBA")
						im.paste(imW,(POSX,POSY),imW)
					else:
						im.paste(imW,(POSX,POSY))
				except:
					pass
				if ConfigType == "0":
					POSX += ConfigSize
				else:
					POSY += ConfigSize
		if "B" in find:
			if os.path.isfile(os.path.join(Data,"fritztel.png")):
				try:
					imW = Image.open(os.path.join(Data,"fritztel.png"))
					imW = imW.resize((ConfigSize,ConfigSize))
					if LCD4linux.WetterTransparenz.value == "true":
						imW = imW.convert("RGBA")
						im.paste(imW,(POSX,POSY),imW)
					else:
						im.paste(imW,(POSX,POSY))
				except:
					pass
				if ConfigType == "0":
					POSX += ConfigSize
				else:
					POSY += ConfigSize
		if "C" in find:
			if os.path.isfile(os.path.join(Data,"calendar.png")):
				try:
					imW = Image.open(os.path.join(Data,"calendar.png"))
					imW = imW.resize((ConfigSize,ConfigSize))
					if LCD4linux.WetterTransparenz.value == "true":
						imW = imW.convert("RGBA")
						im.paste(imW,(POSX,POSY),imW)
					else:
						im.paste(imW,(POSX,POSY))
				except:
					pass
	
# show Sonnenaufgang
	def putSun((ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigSplit, ConfigType, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		POSY = ConfigPos
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		w,h = draw.textsize("%02d:%02d" % L4LSun, font=font)
		ww = ConfigSize+w+int(ConfigSize/6)
		if ConfigType == "0":
			ww*=2
			ww+=int(ConfigSize/3)
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,ww)
		POSXi = POSX+ConfigSize+int(ConfigSize/6)
		if os.path.isfile(os.path.join(Data,"sun.png")):
			try:
				imW = Image.open(os.path.join(Data,"sun.png"))
				imW = imW.resize((ConfigSize,ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					im.paste(imW,(POSX,POSY),imW)
				else:
					im.paste(imW,(POSX,POSY))
			except:
				pass
			if ConfigBackColor !="0":
				w,h = draw.textsize("%02d:%02d" % L4LSun, font=font)
				draw.rectangle((POSXi, POSY,POSXi+w, POSY+h),fill=ConfigBackColor)
			ShadowText(draw,POSXi,POSY,"%02d:%02d" % L4LSun,font,ConfigColor,ConfigShadow)
		if ConfigType == "2":
			POSY += ConfigSize
		else:
			POSX += ConfigSize+w+int(ConfigSize/3)+int(ConfigSize/6)
			POSXi = POSX+ConfigSize+int(ConfigSize/6)
		if os.path.isfile(os.path.join(Data,"moon.png")):
			try:
				imW = Image.open(os.path.join(Data,"moon.png"))
				imW = imW.resize((ConfigSize,ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					im.paste(imW,(POSX,POSY),imW)
				else:
					im.paste(imW,(POSX,POSY))
			except:
				pass
			if ConfigBackColor !="0":
				w,h = draw.textsize("%02d:%02d" % L4LMoon, font=font)
				draw.rectangle((POSXi, POSY,POSXi+w, POSY+h),fill=ConfigBackColor)
			ShadowText(draw,POSXi,POSY,"%02d:%02d" % L4LMoon,font,ConfigColor,ConfigShadow)

# Netatmo
	def putNetatmo((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType, ConfigType2, ConfigColor, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		font2 = ImageFont.truetype(ConfigFont, int(ConfigSize/2), encoding='unic')
		font3 = ImageFont.truetype(ConfigFont, int(ConfigSize/3), encoding='unic')
		if NetatmoOK == False:
			draw.text((int(MAX_W/4),ConfigPos),_("no Netatmo-Plugin installed"),font=font2,fill=ConfigColor)
			return
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		POSY = ConfigPos
		w1,h1 = draw.textsize("-88", font=font)
		w2,h2 = draw.textsize(".8", font=font2)
		w3,h3 = draw.textsize("88888"+self.PRESSURE,font=font2)
		if ConfigType2 == "0":
			w12 = w1+w2+w2
			w123 = w12+(w12*len(self.oM))
			if "C" in ConfigType:
				w123+=w3
		else:
			w12 = w1+w2
			w123 = w12+w2
			if "H" in ConfigType:
				w4,h4 = draw.textsize("88%",font=font2)
				w123+=w4
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,w123)
		for Mod in self.oM:
			ShadowText(draw,POSX,POSY,Mod[0].split(".")[0],font,ConfigColor,ConfigShadow) 
			w,h = draw.textsize(Mod[0].split(".")[0], font=font)
			ShadowText(draw,POSX+w,POSY+int(h/5*2),"."+Mod[0].split(".")[1],font2,ConfigColor,ConfigShadow) 
			ShadowText(draw,POSX+w,POSY,self.TEMPERATURE.decode(),font2,ConfigColor,ConfigShadow)
			if "H" in ConfigType:
				w,h = draw.textsize(Mod[1], font=font2)
				if ConfigType2 == "0":
					PX=int((w1-w)/2)
					PY=h1
				else:
					PX=w1+w2
					PY=int(h1/5*2)
				ShadowText(draw,POSX+PX,POSY+PY,Mod[1],font2,ConfigColor,ConfigShadow)
				ShadowText(draw,POSX+w+PX,POSY+PY,self.HUMIDITY,font3,ConfigColor,ConfigShadow)
			if ConfigType2 == "0":
				POSX += w12
			else:
				POSY += h1
		ShadowText(draw,POSX,POSY,self.iT.split(".")[0],font,ConfigColor,ConfigShadow) 
		w,h = draw.textsize(self.iT.split(".")[0], font=font)
		ShadowText(draw,POSX+w,POSY+int(h/5*2),"."+self.iT.split(".")[1],font2,ConfigColor,ConfigShadow) 
		ShadowText(draw,POSX+w,POSY,self.TEMPERATURE.decode(),font2,ConfigColor,ConfigShadow) 
		if "H" in ConfigType:
			w,h = draw.textsize(self.iH, font=font2)
			if ConfigType2 == "0":
				PX=int((w1-w)/2)
				PY=h1
			else:
				PX=w1+w2
				PY=int(h1/5*2)
			ShadowText(draw,POSX+PX,POSY+PY,self.iH,font2,ConfigColor,ConfigShadow)
			ShadowText(draw,POSX+w+PX,POSY+PY,self.HUMIDITY,font3,ConfigColor,ConfigShadow)

		if ConfigType2 == "0":
			POSX += w12
		else:
			POSY += h1
		if "C" in ConfigType:
			ShadowText(draw,POSX,POSY,self.iC,font2,ConfigColor,ConfigShadow)
			w,h = draw.textsize(self.iC, font=font2)
			ShadowText(draw,POSX+w,POSY,self.CO2,font3,ConfigColor,ConfigShadow)
		if "P" in ConfigType:
			ShadowText(draw,POSX,POSY+h,self.iP,font2,ConfigColor,ConfigShadow)
			w,h = draw.textsize(self.iP, font=font2)
			ShadowText(draw,POSX+w,POSY+h,self.PRESSURE,font3,ConfigColor,ConfigShadow)
		if "N" in ConfigType:
			ShadowText(draw,POSX,POSY+h+h,self.iN,font2,ConfigColor,ConfigShadow)
			w,h = draw.textsize(self.iN, font=font2)
			ShadowText(draw,POSX+w,POSY+h+h,self.NOISE,font3,ConfigColor,ConfigShadow)

# Netstmo CO2
	def putNetatmoIllu((CW, ConfigPos, ConfigSize, ConfigLen, ConfigAlign, ConfigSplit, ConfigType), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,int(ConfigLen) if ConfigType == "0" else int(ConfigSize))
		if CW == "CO2":
			staerkeVal2 = int(self.iC)
			staerkeValOrg = staerkeVal2
			if staerkeVal2 < int(LCD4linux.NetAtmoCO2Min.value):
				staerkeVal2 = int(LCD4linux.NetAtmoCO2Min.value)
			elif staerkeVal2 > int(LCD4linux.NetAtmoCO2Max.value):
				staerkeVal2 = int(LCD4linux.NetAtmoCO2Max.value)
			staerke = 100*(staerkeVal2-int(LCD4linux.NetAtmoCO2Min.value))/(int(LCD4linux.NetAtmoCO2Max.value)-int(LCD4linux.NetAtmoCO2Min.value))
		elif CW == "IDX":
			staerkeVal2 = int(float(self.iIDX))
			staerkeValOrg = staerkeVal2
			staerke = staerkeVal2
		if ConfigType[0] == "0":
			if ConfigType[1:] == "9":
				S = 1.5 if ConfigSize <= 10 else 1.0
				ZW = str(staerkeValOrg) # Value
				font = ImageFont.truetype(FONT, int(ConfigSize*S), encoding='unic')
				w,h = draw.textsize(ZW, font=font)
				ConfigLen -= (w+10)
				draw.text((ConfigLen+5+POSX, ConfigPos+1-(h-ConfigSize)/2),ZW, font=font, fill="yellow")
			if os.path.isfile(os.path.join(Data,"gradient.png")):
				try:
					imW = Image.open(os.path.join(Data,"gradient.png"))
					imW = imW.resize((ConfigLen,ConfigSize))
					imW = imW.crop((0,0,int(ConfigLen*staerke/100),ConfigSize))
					im.paste(imW,(POSX,ConfigPos))
				except:
					pass
			draw.rectangle((POSX,ConfigPos,POSX+ConfigLen,ConfigPos+ConfigSize),outline="yellow")
		elif ConfigType[0] == "1":
			if os.path.isfile(os.path.join(Data,"pointmask.png")):
				try:
					imM = Image.open(os.path.join(Data,"pointmask.png"))
					imM = imM.resize((ConfigSize,ConfigSize))
					b = Image.new("RGBA",(ConfigSize,ConfigSize),ScaleGtoR(staerke))
					b.putalpha(imM.convert("L"))
					im.paste(b,(POSX,ConfigPos),b)
				except:
					L4log("Error Knob")
					from traceback import format_exc
					L4log("Error:",format_exc() )
			if ConfigType[1:] == "9":
				ZW = str(int(staerkeValOrg))
				font = ImageFont.truetype(FONT, int(ConfigSize/3), encoding='unic')
				w,h = draw.textsize(ZW, font=font)
				draw.text((POSX+1+int((ConfigSize-w)/2), ConfigPos+1+int((ConfigSize-h)/2)),ZW, font=font, fill="black")

# Kalender
	def putCalendar((ConfigPos, ConfigZoom, ConfigAlign, ConfigSplit, ConfigType, ConfigTypeE, ConfigLayout, ConfigColor, ConfigBackColor, ConfigCaptionColor, ConfigShadow, ConfigFont), draw, im):
		global CalType
		global CalZoom
		global CalColor
		MAX_Wi,MAX_Hi = im.size
		if ConfigSplit == True:
			MAX_Wi = int(MAX_Wi/2)
		if os.path.isfile(PICcal) and [ConfigType,ConfigTypeE,LCD4linux.CalDays.value] == CalType and ConfigZoom == CalZoom and [ConfigColor,ConfigBackColor,ConfigCaptionColor] == CalColor:
			try:
				pil_image = Image.open(PICcal)
				x,y = pil_image.size
				POSX = getSplit(ConfigSplit,ConfigAlign,MAX_Wi,x)
				if LCD4linux.CalTransparenz.value == "true":
					im.paste(pil_image,(POSX,ConfigPos),pil_image)
				else:
					im.paste(pil_image,(POSX,ConfigPos))
			except:
				pass
		else:
			POSX=0
			POSY=0
			ConfigSize = int(20*ConfigZoom/10)
			MAX_H=ConfigSize
			MAX_W = ConfigSize*16
			if ConfigType[0] == "0":
				MAX_H = ConfigSize*9
			elif ConfigType[0] == "1":
				MAX_H = ConfigSize*4
			if ConfigTypeE[0] in ["C","D"]:
				if ConfigType[0] == "9":
					MAX_W = ConfigSize*25
				MAX_H += ConfigSize*int(int(ConfigTypeE[1])*0.8)
			MAX_H += int(ConfigSize*0.4)
			CalType=[ConfigType,ConfigTypeE,LCD4linux.CalDays.value]
			CalZoom=ConfigZoom
			CalColor=[ConfigColor,ConfigBackColor,ConfigCaptionColor]
			CC=[LCD4linux.CalPathColor.value,LCD4linux.CalHttpColor.value,LCD4linux.CalHttp2Color.value,LCD4linux.CalHttp3Color.value,LCD4linux.CalPlanerFSColor.value]
			if LCD4linux.CalTransparenz.value == "true":
				imW = Image.new('RGBA', (MAX_W, MAX_H), (0, 0, 0, 0))
			else:
				imW = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				if LCD4linux.CalTransparenz.value == "crop":
					POSXs = getSplit(ConfigSplit,ConfigAlign,MAX_Wi,MAX_W)
					image_Back = im.crop((POSXs, ConfigPos, POSXs+MAX_W, ConfigPos+MAX_H))
					imW.paste(image_Back,(0,0))
			drawW = ImageDraw.Draw(imW)
			font = ImageFont.truetype(ConfigFont, int(ConfigSize*0.8), encoding='unic')
			if "A" in ConfigType:
				M = Code_utf8(_(calendar.month_name[datetime.now().month]) + " " + str(datetime.now().year))
				w,h = drawW.textsize(M, font=font)
				ShadowText(drawW,POSX+int(MAX_W/2)-int(w/2), POSY, M, font, ConfigColor,ConfigShadow)
				POSY += h+int(ConfigSize*0.2)
			if ConfigType[0] in ["0","1"]:
				i = 1
				for Week in calendar.weekheader(3).split():
					w,h = drawW.textsize(Code_utf8(_(Week)), font=font)
					ShadowText(drawW,POSX+int(ConfigSize*2*i)+int(ConfigSize/2)-int(w/2), POSY, Code_utf8(_(Week)), font, ConfigCaptionColor,ConfigShadow)
					i += 1
				POSY += h
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				ThisWeek=date(datetime.now().year,datetime.now().month,datetime.now().day).isocalendar()[1]
				for day in calendar.Calendar().itermonthdays2(datetime.now().year,datetime.now().month):
					if day[1] == 0:
						font = ImageFont.truetype(ConfigFont, int(ConfigSize*0.6), encoding='unic')
						dd = 1 if day[0] == 0 else day[0]
						Week=date(datetime.now().year,datetime.now().month,dd).isocalendar()[1]
						PutWeek = False
						if ConfigType[0] == "0" or (ConfigType[0] == "1" and ThisWeek == Week):
							PutWeek = True
							Week = str(Week)
							w,h = drawW.textsize(Week, font=font)
							w1,h1 = drawW.textsize("8", font=font)
							ShadowText(drawW,POSX+w1-int(w/2), POSY+int(h/3), Week, font, ConfigCaptionColor,ConfigShadow)
					if PutWeek == True:
						font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
						if day[0] > 0:
							Tag = str(day[0])
							w,h = drawW.textsize(Tag, font=font)
							today=date.today()
							ICStag = date(today.year,today.month,int(Tag)).strftime("%Y-%m-%d")
							PX1 = POSX+int(ConfigSize*2*(day[1]+1))+int(ConfigSize/2)
							PX = PX1-int(w/2)
							w1,h1 = drawW.textsize(" 1", font=font)
							if ConfigLayout in ["0","2"]:
								if datetime.now().day == day[0]:
									drawW.rectangle((PX1-w1, POSY,PX1+w1, POSY+h),fill=ConfigBackColor)
								ShadowText(drawW,PX, POSY, Tag, font, ConfigColor if day[1]<5 else "red",ConfigShadow)
							if ConfigLayout in ["0"]:
								if ICS.get(ICStag,None) is not None:
									drawW.rectangle((PX1-w1, POSY,PX1+w1, POSY+h),outline=CC[int(ICS[ICStag][0][2])])
									if int(LCD4linux.CalLine.value) > 1:
										drawW.rectangle((PX1-w1+1, POSY+1,PX1+w1-1, POSY+h-1),outline=CC[int(ICS[ICStag][0][2])])
							w1,h1 = drawW.textsize("1", font=font)
							if ConfigLayout in ["1"]:
								if datetime.now().day == day[0]:
									ShadowText(drawW,PX, POSY, Tag, font, ConfigBackColor,ConfigShadow)
									drawW.rectangle((PX1-w1, POSY+h-1,PX1+w1, POSY+h-1),outline=ConfigBackColor)
									if int(LCD4linux.CalLine.value) > 1:
										drawW.rectangle((PX1-w1, POSY+h,PX1+w1, POSY+h),outline=ConfigBackColor)
								else:
									ShadowText(drawW,PX, POSY, Tag, font, ConfigColor if day[1]<5 else "red",ConfigShadow)
							if ConfigLayout in ["1","2"]:
								if ICS.get(ICStag,None) is not None:
									drawW.rectangle((PX1-w1, POSY+h,PX1+w1, POSY+h),outline=CC[int(ICS[ICStag][0][2])])
									if int(LCD4linux.CalLine.value) > 1:
										drawW.rectangle((PX1-w1, POSY+h+1,PX1+w1, POSY+h+1),outline=CC[int(ICS[ICStag][0][2])])
						if day[1] == 6:
							POSY += h
			POSY += int(ConfigSize*0.2)
			if "C" == ConfigTypeE[0]:
				aa = ""
				al = 1
				font = ImageFont.truetype(ConfigFont, int(ConfigSize*0.8), encoding='unic')
				w1,h1 = drawW.textsize("88. ", font=font)
				for t in sorted(ICS):
#					L4log(t)
					x=datetime.strptime(t,"%Y-%m-%d")
					DTx = date(x.year,x.month,x.day)-date.today()
#					print timedelta(0), DTx, timedelta(int(LCD4linux.CalDays.value))
					if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
						aa = "%02d. " % x.day
						w,h = drawW.textsize(Code_utf8(aa), font=font)
						POSX=w1-w
						ShadowText(drawW,POSX, POSY, Code_utf8(aa), font, ConfigColor,ConfigShadow)
						b=[]
						for a in ICS.get(t,[]):
							x = a[1] + timedelta(hours=getTimeDiff())
							if isinstance(x,datetime):
								Time = x.time().strftime("%H:%M ")
							else:
#							if a[1].time().strftime("%H%M") == "0000":
								Time = ""
#							b.append("%s%s | " %(Time,a[0]))
							b.append("%s%s" %(Time,a[0]))
						for a in sorted(b):
							aa += a
							ShadowText(drawW,POSX+w, POSY, Code_utf8(a), font, ConfigColor,ConfigShadow)
							POSY += h
							al+=1
							if al > int(ConfigTypeE[1]):
								break
#						w,h = drawW.textsize(Code_utf8(aa[:-2]), font=font)
#						drawW.text((POSX, POSY), Code_utf8(aa[:-2]), font=font, fill=ConfigColor)
#						POSY += h
#						al+=1
						if al > int(ConfigTypeE[1]):
							break
			if "D" == ConfigTypeE[0]:
				aa = ""
#				font = ImageFont.truetype(ConfigFont, int(ConfigSize), encoding='unic')
				for t in sorted(ICS):
					x=datetime.strptime(t,"%Y-%m-%d")
					DTx = date(x.year,x.month,x.day)-date.today()
					if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
						if x.day != datetime.now().day:
							aa += "%02d.%02d. " % (x.day,x.month)
						for a in ICS.get(t,[]):
							aa += a[0] + " | "
				writeMultiline(aa[:-2],int(ConfigSize*0.8),POSY,int(ConfigTypeE[1]),ConfigColor,"0",False,drawW,imW,ConfigFont=ConfigFont,Shadow=ConfigShadow)
			imW.save(PICcal)
			POSX = getSplit(ConfigSplit,ConfigAlign,MAX_Wi,MAX_W)
			try:
				if LCD4linux.CalTransparenz.value == "true":
					im.paste(imW,(POSX,ConfigPos),imW)
				else:
					im.paste(imW,(POSX,ConfigPos))
			except:
				pass

# Kalender-Liste
	def putCalendarList((ConfigPos, ConfigSize, ConfigProzent, ConfigAlign, ConfigSplit, ConfigType, ConfigLines, ConfigColor, ConfigShadow, ConfigFont), draw, im):
		MAX_W,MAX_H = im.size
		if ConfigSplit == True:
			MAX_W = int(MAX_W/2)
		CW=int(MAX_W*int(ConfigProzent)/100)
		POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,CW)
		POSY=ConfigPos
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		findICS = False
		for t in sorted(ICS):
			x=datetime.strptime(t,"%Y-%m-%d")
			DTx = date(x.year,x.month,x.day)-date.today()
			if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
				findICS = True
				break
		if findICS == False:
			if LCD4linux.ShowNoMsg.value == True:
				ShadowText(draw,POSX, POSY, _("no Dates"), font, ConfigColor, ConfigShadow)
			return
		CS=int(ConfigSize*1.8)
		w1,h1 = draw.textsize("A", font=font)
		if os.path.isfile(os.path.join(Data,"calendar.png")) and "-" not in ConfigType:
			try:
				imW = Image.open(os.path.join(Data,"calendar.png"))
				xx,yy = imW.size
				x1=int(float(CS)/yy*xx)
				imW = imW.resize((x1,CS))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					im.paste(imW,(POSX,POSY),imW)
				else:
					im.paste(imW,(POSX,POSY))
				POSX += x1+w1
			except:
				pass
		if "C" in ConfigType:
			aa = ""
			al = 1
			w1,h1 = draw.textsize("88.88. ", font=font)
			for t in sorted(ICS):
				x=datetime.strptime(t,"%Y-%m-%d")
				DTx = date(x.year,x.month,x.day)-date.today()
#					print timedelta(0), DTx, timedelta(int(LCD4linux.CalDays.value))
				if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
					aa = "%02d.%02d. " % (x.day,x.month)
					w,h = draw.textsize(Code_utf8(aa), font=font)
					PX=POSX+w1-w
					ShadowText(draw,PX, POSY, Code_utf8(aa), font, ConfigColor, ConfigShadow)
					b=[]
					for a in ICS.get(t,[]):
						x = a[1] + timedelta(hours=getTimeDiff())
						if isinstance(x,datetime):
							Time = x.time().strftime("%H:%M ")
						else:
							Time = ""
						b.append("%s%s" %(Time,a[0]))
					for a in sorted(b):
						aa += a
						tx=cutText(Code_utf8(a),draw,font,CW-w-CS)
						ShadowText(draw,PX+w, POSY, tx, font, ConfigColor, ConfigShadow)
						POSY += h
						al+=1
						if al > int(ConfigLines):
							break
					if al > int(ConfigLines):
						break
		elif "D" in ConfigType:
			aa = ""
			for t in sorted(ICS):
				x=datetime.strptime(t,"%Y-%m-%d")
				DTx = date(x.year,x.month,x.day)-date.today()
				if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
					if x.day != datetime.now().day:
						aa += "%02d.%02d. " % (x.day,x.month)
					for a in ICS.get(t,[]):
						aa += a[0] + " | "
			writeMultiline(aa[:-2],int(ConfigSize),POSY,int(ConfigLines),ConfigColor,ConfigAlign,ConfigSplit,draw,im,ConfigFont=ConfigFont,Shadow=ConfigShadow,Width=CW,PosX=POSX)

# show isRecording
	def putRecording((ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType),draw,im):
		MAX_W,MAX_H = im.size
		if self.LisRecording or ConfigMode == True:
			if ConfigType == "1":
				draw.ellipse((MAX_W-ConfigSize, -ConfigSize, MAX_W+ConfigSize, ConfigSize), fill="red")
			else:
				try:
					if ConfigSplit == True:
						MAX_W = int(MAX_W/2)
					pil_image = Image.open(LCD4linux.RecordingPath.value if os.path.isfile(LCD4linux.RecordingPath.value) else RecPic )
					xx,yy = pil_image.size
					x=int(float(ConfigSize)/yy*xx)
					pil_image = pil_image.resize((x, ConfigSize))
					POSX = getSplit(ConfigSplit,ConfigAlign,MAX_W,x)
					if LCD4linux.WetterTransparenz.value == "true":
						pil_image = pil_image.convert("RGBA")
						im.paste(pil_image,(POSX,ConfigPos),pil_image)
					else:
						im.paste(pil_image,(POSX,ConfigPos))
				except:
					L4log("Error Recording Pic")

# show Box
	def putBox((x1,y1,x2,y2,ConfigColor,ConfigBackColor),draw,im):
		if ConfigBackColor == "0":
			draw.rectangle((x1, y1, x1+x2, y1+y2),outline=ConfigColor)
		else:
			draw.rectangle((x1, y1, x1+x2, y1+y2),fill=ConfigBackColor,outline=ConfigColor)

# show isCrashlog
	def putCrash(draw,im):
#		MAX_W,MAX_H = im.size
		if os.path.isfile(CrashFile):
			draw.ellipse((-25, -25, 25, 25), fill="yellow") 

# externe Elemente
	def putL4LElist(MODE):
		def Sync(L):
			if "1" in L:
				Brief1.join()
			elif "2" in L and LCD4linux.LCDType2.value != "00":
				Brief2.join()
			elif "3" in L and LCD4linux.LCDType3.value != "00":
				Brief3.join()

		L4Lkeys = L4LElist.get().keys()
		L4Lkeys.sort()
		for E in L4Lkeys:
			CUR = L4LElist.get(E)
			L4logE("CUR: %s Active %s" % (CUR,ScreenActive[0]))
			LCD = str(CUR.get("Lcd","1"))
			if getSA(int(LCD)) in str(CUR.get("Screen","1")) and MODE in CUR.get("Mode","On"):
				Typ = CUR.get("Typ",None)
				if "1" in LCD:
					DR,IM = draw,im
				elif "2" in LCD and LCD4linux.LCDType2.value != "00":
					DR,IM = draw2,im2
				elif "3" in LCD and LCD4linux.LCDType3.value != "00":
					DR,IM = draw3,im3
				else:
					DR=IM=None
				if DR is not None and Typ is not None:
					MAX_W,MAX_H = IM.size
					if Typ == "txt":
						L4logE("Text", CUR)
						writeMultiline(str(CUR.get("Text","Text")),int(CUR.get("Size",20)),int(CUR.get("Pos",0)),int(CUR.get("Lines",1)),CUR.get("Color","white"),str(CUR.get("Align","1")),False,DR,IM,ConfigFont=getFont(str(CUR.get("Font","0"))),Shadow=CUR.get("Shadow",False))
					elif Typ == "bar":
						L4logE("Bar", CUR)
						POSX = getSplit(False,str(CUR.get("Align","1")),MAX_W,int(CUR.get("Len",int(MAX_W/2)))+1)
						DR.rectangle((POSX,int(CUR.get("Pos",0)),POSX+int(CUR.get("Len",int(MAX_W/2))),int(CUR.get("Pos",0))+int(CUR.get("Size",20))),outline=CUR.get("Color","white"))
						DR.rectangle((POSX,int(CUR.get("Pos",0)),POSX+int(int(CUR.get("Len",int(MAX_W/2)))*int(CUR.get("Value",50))/100),int(CUR.get("Pos",0))+int(CUR.get("Size",20))),fill=CUR.get("Color","white"))
					elif Typ == "pic":
						L4logE("Pic", CUR)
						ShowPicture = getShowPicture(CUR.get("File",""),0)
						putBild((int(CUR.get("Pos",0)),int(CUR.get("Size",100)),0,str(CUR.get("Align","1")),CUR.get("Quick",False),CUR.get("Transp",False), ShowPicture, ShowPicture),0,DR,IM)
					elif Typ == "box":
						if CUR.get("Fill",True) == False:
							DR.rectangle((int(CUR.get("PosX",0)),int(CUR.get("PosY",0)),int(CUR.get("PosX",0))+int(CUR.get("Width",100)),int(CUR.get("PosY",0))+int(CUR.get("Height",100))),outline=CUR.get("Color","white"))
						else:
							Sync(LCD)
							DR.rectangle((int(CUR.get("PosX",0)),int(CUR.get("PosY",0)),int(CUR.get("PosX",0))+int(CUR.get("Width",100)),int(CUR.get("PosY",0))+int(CUR.get("Height",100))),fill=CUR.get("Color","white"),outline=CUR.get("Color","white"))
							Sync(LCD)
					elif Typ == "wait":
						Sync(LCD)
				else:
					L4log("Elemente-Fehler",CUR)

# Auszeit Hintergrundbeleuchtung 
	def isOffTime(b,e,bw,ew):
		t=localtime()
		tt = time()
		if strftime("%w") in ["6","0"]:
			bT=mktime(datetime(t.tm_year,t.tm_mon,t.tm_mday,bw[0],bw[1]).timetuple()) 
			eT=mktime(datetime(t.tm_year,t.tm_mon,t.tm_mday,ew[0],ew[1]).timetuple())
		else:
			bT=mktime(datetime(t.tm_year,t.tm_mon,t.tm_mday,b[0],b[1]).timetuple()) 
			eT=mktime(datetime(t.tm_year,t.tm_mon,t.tm_mday,e[0],e[1]).timetuple())
		if eT < bT and tt > eT:
			eT += 86400
		if eT < bT and tt < eT:
			bT -= 86400
		return (bT < tt < eT)

	def Lput(LCD,SCR,FUNC,PARA):
		if "1" in LCD and getSA(1) in SCR:
			Brief1.put([FUNC,PARA, draw, im])
		if "2" in LCD and LCD4linux.LCDType2.value != "00" and getSA(2) in SCR:
			Brief2.put([FUNC,PARA, draw2, im2])
		if "3" in LCD and LCD4linux.LCDType3.value != "00" and getSA(3) in SCR:
			Brief3.put([FUNC,PARA, draw3, im3])

	def Lput4(LCD,SCR,FUNC,PARA):
		if "1" in LCD and getSA(1) in SCR:
			Brief1.put([FUNC,PARA,0, draw, im])
		if "2" in LCD and LCD4linux.LCDType2.value != "00" and getSA(2) in SCR:
			Brief2.put([FUNC,PARA,1, draw2, im2])
		if "3" in LCD and LCD4linux.LCDType3.value != "00" and getSA(3) in SCR:
			Brief3.put([FUNC,PARA,2, draw3, im3])

###############
###############
###############
	if not LCD4linux.Enable.value:
		return
	tt = time()
#	L4log("MP-Mode",isMediaPlayer)
	L4log("creating LCD-Picture")
	if os.path.isdir("%slcd4linux" % TMP) == False:
		try:
			os.mkdir("%slcd4linux" % TMP)
		except:
			L4log("%s Error" % TMP)
	if OSDon >= 2 and FritzTime == 0:
#		doGrab(9,LCD4linux.OSDfast.value, LCD4linux.OSDsize.value)
		if Briefkasten.qsize()<=3:
			Briefkasten.put(2)
		else:
			L4log("Queue full, Thread hanging?")

	if self.LsreftoString is not None:
		sref = self.LsreftoString
		L4logE("Service    ", sref)
		L4logE("Service alt", self.ref)
		if self.ref != sref:
			L4log("Service changed")
			self.ref = sref
#			self.LEventsNext = None
			if SaveEventListChanged == False:
				ScreenActive[0] = "1"
				LCD4linux.ScreenActive.value = ScreenActive[0]
				ScreenTime = 0
			SaveisMediaPlayer = isMediaPlayer
			isMediaPlayer = ""
			rmFile(MP3tmp)
			rmFile(GoogleCover)
			if sref.startswith("1:0:2") is True:
				L4log("detected Radio")
				isMediaPlayer = "radio"
			elif sref.startswith("4097:0") is True:
				L4log("detected AudioMedia")
				isMediaPlayer = "mp3"
			elif "0:0:0:0:0:0:0:0:0:" in sref:
				L4log("detected Video")
				isMediaPlayer = "record"
			if isMediaPlayer != "mp3":
				rmFile("/tmp/.cover")
				rmFile("/tmp/.wbrfs_pic")
			if SaveisMediaPlayer != isMediaPlayer:
				getBilder()
				rmFile(PICfritz)

	QuickList = [[],[],[]]
	Dunkel = ""
	MAX_W,MAX_H = getResolution(LCD4linux.LCDType1.value,LCD4linux.LCDRotate1.value)
	L4LElist.setResolution(1,MAX_W,MAX_H)
	pil_open = ""
	col_back = "black"
	if (Standby.inStandby or ConfigStandby):
		pil_open = LCD4linux.StandbyLCDBild1.value
		col_back = LCD4linux.StandbyLCDColor1.value
	elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
		pil_open = LCD4linux.MPLCDBild1.value
		col_back = LCD4linux.MPLCDColor1.value
	elif LCD4linux.LCDBild1.value != "":
		pil_open = LCD4linux.LCDBild1.value
	elif LCD4linux.LCDBild1.value == "":
		col_back = LCD4linux.LCDColor1.value
	im = Image.new('RGB', (MAX_W, MAX_H), col_back)
	draw = ImageDraw.Draw(im)
	im2 = im
	im3 = im
	draw2 = draw
	draw3 = draw
	checkTVrunning = False
	if ScreenActive[0] in LCD4linux.TV.value and "1" in LCD4linux.TVLCD.value:
		checkTVrunning = True
		if TVrunning == False:
			if LCD4linux.LCDType1.value[0] == "1":
				doGrabTV(str(MAX_W),str(MAX_H),"4",LCD4linux.TVType.value)
			elif LCD4linux.LCDType1.value[0] == "2":
				doGrabTV(str(MAX_W),str(MAX_H),"1",LCD4linux.TVType.value)
			else:
				doGrabTV(str(MAX_W),str(MAX_H),"7",LCD4linux.TVType.value)

	try:
		pil_image = None
		if pil_open != "" and os.path.isfile(pil_open):
			if isOffTime(L4LMoon,L4LSun,L4LMoon,L4LSun):
				if os.path.isfile(pil_open.replace(pil_open[-4:],"_night"+pil_open[-4:])):
					pil_open=pil_open.replace(pil_open[-4:],"_night"+pil_open[-4:])
					L4logE("Nightbackground",pil_open)
			pil_image = Image.open(pil_open)
			if pil_image is not None:
				im.paste(pil_image,(0,0))
	except:
		pass
	if LCD4linux.LCDType2.value != "00":
		MAX_W,MAX_H = getResolution(LCD4linux.LCDType2.value,LCD4linux.LCDRotate2.value)
		L4LElist.setResolution(2,MAX_W,MAX_H)
		pil_open = ""
		col_back = "black"
		if (Standby.inStandby or ConfigStandby):
			pil_open = LCD4linux.StandbyLCDBild2.value
			col_back = LCD4linux.StandbyLCDColor2.value
		elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
			pil_open = LCD4linux.MPLCDBild2.value
			col_back = LCD4linux.MPLCDColor2.value
		elif LCD4linux.LCDBild2.value != "":
			pil_open = LCD4linux.LCDBild2.value
		elif LCD4linux.LCDBild2.value == "":
			col_back = LCD4linux.LCDColor2.value
		im2 = Image.new('RGB', (MAX_W, MAX_H), col_back)
		draw2 = ImageDraw.Draw(im2)
		if ScreenActive[0] in LCD4linux.TV.value and "2" in LCD4linux.TVLCD.value:
			checkTVrunning = True
			if TVrunning == False:
				if LCD4linux.LCDType2.value[0] == "1":
					doGrabTV(str(MAX_W),str(MAX_H),"5",LCD4linux.TVType.value)
				elif LCD4linux.LCDType2.value[0] == "2":
					doGrabTV(str(MAX_W),str(MAX_H),"2",LCD4linux.TVType.value)
				else:
					doGrabTV(str(MAX_W),str(MAX_H),"8",LCD4linux.TVType.value)
		try:
			pil_image = None
			if pil_open != "" and os.path.isfile(pil_open):
				if isOffTime(L4LMoon,L4LSun,L4LMoon,L4LSun):
					if os.path.isfile(pil_open.replace(pil_open[-4:],"_night"+pil_open[-4:])):
						pil_open=pil_open.replace(pil_open[-4:],"_night"+pil_open[-4:])
						L4logE("Nightbackground",pil_open)
				pil_image = Image.open(pil_open)
				if pil_image is not None:
					im2.paste(pil_image,(0,0))
		except:
			pass
	if LCD4linux.LCDType3.value != "00":
		MAX_W,MAX_H = getResolution(LCD4linux.LCDType3.value,LCD4linux.LCDRotate3.value)
		L4LElist.setResolution(3,MAX_W,MAX_H)
		pil_open = ""
		col_back = "black"
		if (Standby.inStandby or ConfigStandby):
			pil_open = LCD4linux.StandbyLCDBild3.value
			col_back = LCD4linux.StandbyLCDColor3.value
		elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
			pil_open = LCD4linux.MPLCDBild3.value
			col_back = LCD4linux.MPLCDColor3.value
		elif LCD4linux.LCDBild3.value != "":
			pil_open = LCD4linux.LCDBild3.value
		elif LCD4linux.LCDBild3.value == "":
			col_back = LCD4linux.LCDColor3.value
		im3 = Image.new('RGB', (MAX_W, MAX_H), col_back)
		draw3 = ImageDraw.Draw(im3)
#		if ScreenActive[0] in LCD4linux.TV.value and "3" in LCD4linux.TVLCD.value:
#			checkTVrunning = True
#			if TVrunning == False:
#				if LCD4linux.LCDType3.value[0] == "1":
#					doGrabTV(str(MAX_W),str(MAX_H),"4",LCD4linux.TVType.value)
#				else:
#					doGrabTV(str(MAX_W),str(MAX_H),"2",LCD4linux.TVType.value)
		try:
			pil_image = None
			if pil_open != "" and os.path.isfile(pil_open):
				if isOffTime(L4LMoon,L4LSun,L4LMoon,L4LSun):
					if os.path.isfile(pil_open.replace(pil_open[-4:],"_night"+pil_open[-4:])):
						pil_open=pil_open.replace(pil_open[-4:],"_night"+pil_open[-4:])
						L4logE("Nightbackground",pil_open)
				pil_image = Image.open(pil_open)
				if pil_image is not None:
					im3.paste(pil_image,(0,0))
		except:
			pass
		if TVrunning == True and checkTVrunning == False:
			TVrunning = False
#	DRIM=[[draw,im],[draw1,im1],[draw2,im2]]
####
#### Standby Modus
####
	if Standby.inStandby or ConfigStandby:
		if LCD4linux.Standby.value == "1":
			if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4" or LCD4linux.LCDType3.value[0] == "4":
				if "C" in LCD4linux.LCDTFT.value:
					if AktTFT != "BMP":
						TFTCheck(False,SetMode="BMP")
				else:
					if AktTFT != "DREAM":
						TFTCheck(False,SetMode="DREAM")
			Dunkel=writeHelligkeit(LCD4linux.StandbyHelligkeit.value,LCD4linux.StandbyHelligkeit2.value,LCD4linux.StandbyHelligkeit3.value)
			if LCD4linux.StandbyHelligkeit.value == 0:
				Dunkel=writeHelligkeit(0,0,0)
# LCDoff
			if LCD4linux.StandbyLCDoff.value != LCD4linux.StandbyLCDon.value or LCD4linux.StandbyLCDWEoff.value != LCD4linux.StandbyLCDWEon.value or LCDon == False:
				if isOffTime(LCD4linux.StandbyLCDoff.value,LCD4linux.StandbyLCDon.value,LCD4linux.StandbyLCDWEoff.value,LCD4linux.StandbyLCDWEon.value) or LCDon == False:
					Dunkel=writeHelligkeit(0,0,0)
					L4log("LCD off")
			if LCD4linux.StandbyFritz.value != "0" and LCD4linux.FritzPopupLCD.value != "0" and FritzTime > 1:
# FritzCall
				Para = LCD4linux.StandbyFritzPos.value, LCD4linux.StandbyFritzSize.value, LCD4linux.StandbyFritzColor.value, LCD4linux.StandbyFritzBackColor.value, LCD4linux.StandbyFritzAlign.value, LCD4linux.StandbyFritzType.value, LCD4linux.StandbyFritzPicPos.value, LCD4linux.StandbyFritzPicSize.value, LCD4linux.StandbyFritzPicAlign.value, LCD4linux.StandbyFritzShadow.value, getFont(LCD4linux.StandbyFritzFont.value)
				Lput(LCD4linux.FritzPopupLCD.value,"123456789",putFritz,Para)
			else:
# Bild
				if ScreenActive[0] in LCD4linux.StandbyBild.value or ScreenActive[-3:] != ["","",""]:
					ShowPicture = getShowPicture(LCD4linux.StandbyBildFile.value,0)
					Para = LCD4linux.StandbyBildPos.value, LCD4linux.StandbyBildSize.value, 0, LCD4linux.StandbyBildAlign.value, LCD4linux.StandbyBildQuick.value, LCD4linux.StandbyBildTransp.value, ShowPicture, LCD4linux.StandbyBildFile.value
					Lput4(LCD4linux.StandbyBildLCD.value,LCD4linux.StandbyBild.value,putBild,Para)
# Bild 2
				if ScreenActive[0] in LCD4linux.StandbyBild2.value or ScreenActive[-3:] != ["","",""]:
					ShowPicture = getShowPicture(LCD4linux.StandbyBild2File.value,1)
					Para = LCD4linux.StandbyBild2Pos.value, LCD4linux.StandbyBild2Size.value, 0, LCD4linux.StandbyBild2Align.value, LCD4linux.StandbyBild2Quick.value, LCD4linux.StandbyBild2Transp.value, ShowPicture, LCD4linux.StandbyBild2File.value
					Lput4(LCD4linux.StandbyBild2LCD.value,LCD4linux.StandbyBild2.value,putBild,Para)
# Bild 3
				if ScreenActive[0] in LCD4linux.StandbyBild3.value or ScreenActive[-3:] != ["","",""]:
					ShowPicture = getShowPicture(LCD4linux.StandbyBild3File.value,2)
					Para = LCD4linux.StandbyBild3Pos.value, LCD4linux.StandbyBild3Size.value, 0, LCD4linux.StandbyBild3Align.value, LCD4linux.StandbyBild3Quick.value, LCD4linux.StandbyBild3Transp.value, ShowPicture, LCD4linux.StandbyBild3File.value
					Lput4(LCD4linux.StandbyBild3LCD.value,LCD4linux.StandbyBild3.value,putBild,Para)
# Bild 4
				if ScreenActive[0] in LCD4linux.StandbyBild4.value or ScreenActive[-3:] != ["","",""]:
					ShowPicture = getShowPicture(LCD4linux.StandbyBild4File.value,0)
					Para = LCD4linux.StandbyBild4Pos.value, LCD4linux.StandbyBild4Size.value, 0, LCD4linux.StandbyBild4Align.value, LCD4linux.StandbyBild4Quick.value, LCD4linux.StandbyBild4Transp.value, ShowPicture, LCD4linux.StandbyBild4File.value
					Lput4(LCD4linux.StandbyBild4LCD.value, LCD4linux.StandbyBild4.value,putBild,Para)
				Brief1.join()
				Brief2.join()
				Brief3.join()
# Kalender
				Para = LCD4linux.StandbyCalPos.value,LCD4linux.StandbyCalZoom.value,LCD4linux.StandbyCalAlign.value,LCD4linux.StandbyCalSplit.value,LCD4linux.StandbyCalType.value,LCD4linux.StandbyCalTypeE.value,LCD4linux.StandbyCalLayout.value,LCD4linux.StandbyCalColor.value,LCD4linux.StandbyCalBackColor.value,LCD4linux.StandbyCalCaptionColor.value,LCD4linux.StandbyCalShadow.value,getFont(LCD4linux.StandbyCalFont.value)
				Lput(LCD4linux.StandbyCalLCD.value,LCD4linux.StandbyCal.value,putCalendar,Para)
# Termin-List
				Para = LCD4linux.StandbyCalListPos.value,LCD4linux.StandbyCalListSize.value,LCD4linux.StandbyCalListProzent.value,LCD4linux.StandbyCalListAlign.value,LCD4linux.StandbyCalListSplit.value,LCD4linux.StandbyCalListType.value,LCD4linux.StandbyCalListLines.value,LCD4linux.StandbyCalListColor.value,LCD4linux.StandbyCalListShadow.value,getFont(LCD4linux.StandbyCalListFont.value)
				Lput(LCD4linux.StandbyCalListLCD.value,LCD4linux.StandbyCalList.value,putCalendarList,Para)
# MSN Wetter
				if wwwWetter[0].find("forecast") > 1:
					Para = LCD4linux.StandbyWetterPos.value,LCD4linux.StandbyWetterZoom.value,LCD4linux.StandbyWetterAlign.value,LCD4linux.StandbyWetterSplit.value,LCD4linux.StandbyWetterType.value,LCD4linux.StandbyWetterColor.value,LCD4linux.StandbyWetterShadow.value,0,getFont(LCD4linux.StandbyWetterFont.value)
					Lput(LCD4linux.StandbyWetterLCD.value,LCD4linux.StandbyWetter.value,putWetter,Para)
				if wwwWetter[1].find("forecast") > 1:
					Para = LCD4linux.StandbyWetter2Pos.value,LCD4linux.StandbyWetter2Zoom.value,LCD4linux.StandbyWetter2Align.value,LCD4linux.StandbyWetter2Split.value,LCD4linux.StandbyWetter2Type.value,LCD4linux.StandbyWetter2Color.value,LCD4linux.StandbyWetter2Shadow.value,1,getFont(LCD4linux.StandbyWetter2Font.value)
					Lput(LCD4linux.StandbyWetter2LCD.value,LCD4linux.StandbyWetter2.value,putWetter,Para)
# Netatmo CO2
				Para = "CO2",LCD4linux.StandbyNetAtmoCO2Pos.value,LCD4linux.StandbyNetAtmoCO2Size.value,LCD4linux.StandbyNetAtmoCO2Len.value,LCD4linux.StandbyNetAtmoCO2Align.value,LCD4linux.StandbyNetAtmoCO2Split.value,LCD4linux.StandbyNetAtmoCO2Type.value
				Lput(LCD4linux.StandbyNetAtmoCO2LCD.value,LCD4linux.StandbyNetAtmoCO2.value,putNetatmoIllu,Para)
# Netatmo IDX
				Para = "IDX",LCD4linux.StandbyNetAtmoIDXPos.value,LCD4linux.StandbyNetAtmoIDXSize.value,LCD4linux.StandbyNetAtmoIDXLen.value,LCD4linux.StandbyNetAtmoIDXAlign.value,LCD4linux.StandbyNetAtmoIDXSplit.value,LCD4linux.StandbyNetAtmoIDXType.value
				Lput(LCD4linux.StandbyNetAtmoIDXLCD.value,LCD4linux.StandbyNetAtmoIDX.value,putNetatmoIllu,Para)
# HTTP WWW Site
				Para = 1,LCD4linux.StandbyWWW1Pos.value,LCD4linux.StandbyWWW1Size.value,LCD4linux.StandbyWWW1Align.value,LCD4linux.StandbyWWW1CutX.value,LCD4linux.StandbyWWW1CutY.value,LCD4linux.StandbyWWW1CutW.value,LCD4linux.StandbyWWW1CutH.value
				Lput(LCD4linux.StandbyWWW1LCD.value,LCD4linux.StandbyWWW1.value,putWWW,Para)
				Brief1.join()
				Brief2.join()
				Brief3.join()
# Netatmo
				Para = LCD4linux.StandbyNetAtmoPos.value,LCD4linux.StandbyNetAtmoSize.value,LCD4linux.StandbyNetAtmoAlign.value,LCD4linux.StandbyNetAtmoSplit.value,LCD4linux.StandbyNetAtmoType.value,LCD4linux.StandbyNetAtmoType2.value,LCD4linux.StandbyNetAtmoColor.value,LCD4linux.StandbyNetAtmoShadow.value,getFont(LCD4linux.StandbyNetAtmoFont.value)
				Lput(LCD4linux.StandbyNetAtmoLCD.value,LCD4linux.StandbyNetAtmo.value,putNetatmo,Para)
# Box 1
				Para = LCD4linux.StandbyBox1x1.value,LCD4linux.StandbyBox1y1.value,LCD4linux.StandbyBox1x2.value,LCD4linux.StandbyBox1y2.value,LCD4linux.StandbyBox1Color.value,LCD4linux.StandbyBox1BackColor.value
				Lput(LCD4linux.StandbyBox1LCD.value,LCD4linux.StandbyBox1.value,putBox,Para)
# Box 2
				Para = LCD4linux.StandbyBox2x1.value,LCD4linux.StandbyBox2y1.value,LCD4linux.StandbyBox2x2.value,LCD4linux.StandbyBox2y2.value,LCD4linux.StandbyBox2Color.value,LCD4linux.StandbyBox2BackColor.value
				Lput(LCD4linux.StandbyBox2LCD.value,LCD4linux.StandbyBox2.value,putBox,Para)
# Moonphase
				Para = LCD4linux.StandbyMoonPos.value,LCD4linux.StandbyMoonSize.value,LCD4linux.StandbyMoonAlign.value,LCD4linux.StandbyMoonSplit.value,LCD4linux.StandbyMoonColor.value,LCD4linux.StandbyMoonShadow.value,getFont(LCD4linux.StandbyMoonFont.value)
				Lput(LCD4linux.StandbyMoonLCD.value,LCD4linux.StandbyMoon.value,putMoon,Para)
# Meteo station
				if wwwMeteo.find("current_conditions") > 1:
					Para = LCD4linux.StandbyMeteoPos.value,LCD4linux.StandbyMeteoZoom.value,LCD4linux.StandbyMeteoAlign.value,LCD4linux.StandbyMeteoSplit.value,LCD4linux.StandbyMeteoType.value,LCD4linux.StandbyMeteoColor.value
					Lput(LCD4linux.StandbyMeteoLCD.value,LCD4linux.StandbyMeteo.value,putMeteo,Para)
# get clock
				Para = LCD4linux.StandbyClockPos.value,LCD4linux.StandbyClockSize.value,LCD4linux.StandbyClockAlign.value,LCD4linux.StandbyClockSplit.value,LCD4linux.StandbyClockType.value,LCD4linux.StandbyClockSpacing.value,LCD4linux.StandbyClockAnalog.value,LCD4linux.StandbyClockColor.value,LCD4linux.StandbyClockShadow.value,getFont(LCD4linux.StandbyClockFont.value)
				Lput(LCD4linux.StandbyClockLCD.value,LCD4linux.StandbyClock.value,putClock,Para)
				Para = LCD4linux.StandbyClock2Pos.value,LCD4linux.StandbyClock2Size.value,LCD4linux.StandbyClock2Align.value,LCD4linux.StandbyClock2Split.value,LCD4linux.StandbyClock2Type.value,LCD4linux.StandbyClock2Spacing.value,LCD4linux.StandbyClock2Analog.value,LCD4linux.StandbyClock2Color.value,LCD4linux.StandbyClock2Shadow.value,getFont(LCD4linux.StandbyClock2Font.value)
				Lput(LCD4linux.StandbyClock2LCD.value,LCD4linux.StandbyClock2.value,putClock,Para)
# Informationen
				Para = LCD4linux.StandbyInfoPos.value, LCD4linux.StandbyInfoSize.value,LCD4linux.StandbyInfoAlign.value,LCD4linux.StandbyInfoLines.value,LCD4linux.StandbyInfoSplit.value,LCD4linux.StandbyInfoColor.value,LCD4linux.StandbyInfoSensor.value+LCD4linux.StandbyInfoCPU.value, LCD4linux.StandbyInfoShadow.value, getFont(LCD4linux.StandbyInfoFont.value)
				Lput(LCD4linux.StandbyInfoLCD.value,LCD4linux.StandbyInfo.value,putInfo,Para)
# Tuner
				Para = LCD4linux.StandbyTunerPos.value, LCD4linux.StandbyTunerSize.value, LCD4linux.StandbyTunerAlign.value, LCD4linux.StandbyTunerSplit.value, LCD4linux.StandbyTunerType.value, LCD4linux.StandbyTunerActive.value,getFont(LCD4linux.StandbyTunerFont.value)
				Lput(LCD4linux.StandbyTunerLCD.value,LCD4linux.StandbyTuner.value,putTuner,Para)
# Online-Ping
				Para = LCD4linux.StandbyPingPos.value, LCD4linux.StandbyPingSize.value, LCD4linux.StandbyPingAlign.value, LCD4linux.StandbyPingSplit.value, LCD4linux.StandbyPingColor.value, LCD4linux.StandbyPingType.value, LCD4linux.StandbyPingShow.value, LCD4linux.StandbyPingTimeout.value, (LCD4linux.StandbyPingName1.value,LCD4linux.StandbyPingName2.value,LCD4linux.StandbyPingName3.value,LCD4linux.StandbyPingName4.value,LCD4linux.StandbyPingName5.value), LCD4linux.StandbyPingShadow.value,getFont(LCD4linux.StandbyPingFont.value)
				Lput(LCD4linux.StandbyPingLCD.value,LCD4linux.StandbyPing.value,putOnline,Para)
# next Timer Record
				Para = LCD4linux.StandbyTimerPos.value, LCD4linux.StandbyTimerSize.value, LCD4linux.StandbyTimerLines.value, LCD4linux.StandbyTimerType.value, LCD4linux.StandbyTimerAlign.value, LCD4linux.StandbyTimerSplit.value, LCD4linux.StandbyTimerColor.value, LCD4linux.StandbyTimerShadow.value,getFont(LCD4linux.StandbyTimerFont.value)
				Lput(LCD4linux.StandbyTimerLCD.value,LCD4linux.StandbyTimer.value,putTimer,Para)
# Devices
				Para = LCD4linux.StandbyDevPos.value, LCD4linux.StandbyDevSize.value, LCD4linux.StandbyDevAlign.value, LCD4linux.StandbyDevSplit.value, LCD4linux.StandbyDevColor.value, (LCD4linux.StandbyDevExtra.value,LCD4linux.StandbyDevName1.value,LCD4linux.StandbyDevName2.value,LCD4linux.StandbyDevName3.value,LCD4linux.StandbyDevName4.value,LCD4linux.StandbyDevName5.value), LCD4linux.StandbyDevShadow.value, LCD4linux.StandbyDevType.value,getFont(LCD4linux.StandbyDevFont.value)
				Lput(LCD4linux.StandbyDevLCD.value,LCD4linux.StandbyDev.value,putDev,Para)
# HDD
				Para = LCD4linux.StandbyHddPos.value, LCD4linux.StandbyHddSize.value, LCD4linux.StandbyHddAlign.value, LCD4linux.StandbyHddSplit.value, LCD4linux.StandbyHddType.value
				Lput(LCD4linux.StandbyHddLCD.value,LCD4linux.StandbyHdd.value,putHdd,Para)
# show OSCAM
				Para = LCD4linux.StandbyOSCAMPos.value, LCD4linux.StandbyOSCAMSize.value, LCD4linux.StandbyOSCAMColor.value, LCD4linux.StandbyOSCAMBackColor.value, LCD4linux.StandbyOSCAMAlign.value, LCD4linux.StandbyOSCAMSplit.value
				Lput(LCD4linux.StandbyOSCAMLCD.value,LCD4linux.StandbyOSCAM.value,putOSCAM,Para)
# show Textfile
				Para = LCD4linux.StandbyTextPos.value,LCD4linux.StandbyTextSize.value,getFont(LCD4linux.StandbyTextFont.value),LCD4linux.StandbyTextAlign.value,LCD4linux.StandbyTextColor.value,LCD4linux.StandbyTextBackColor.value,LCD4linux.StandbyTextShadow.value, LCD4linux.StandbyTextFile.value
				Lput(LCD4linux.StandbyTextLCD.value,LCD4linux.StandbyText.value,putTextFile,Para)
# show Textfile 2
				Para = LCD4linux.StandbyText2Pos.value,LCD4linux.StandbyText2Size.value,getFont(LCD4linux.StandbyText2Font.value),LCD4linux.StandbyText2Align.value,LCD4linux.StandbyText2Color.value,LCD4linux.StandbyText2BackColor.value,LCD4linux.StandbyText2Shadow.value, LCD4linux.StandbyText2File.value
				Lput(LCD4linux.StandbyText2LCD.value,LCD4linux.StandbyText2.value,putTextFile,Para)
# show Textfile 3
				Para = LCD4linux.StandbyText3Pos.value,LCD4linux.StandbyText3Size.value,getFont(LCD4linux.StandbyText3Font.value),LCD4linux.StandbyText3Align.value,LCD4linux.StandbyText3Color.value,LCD4linux.StandbyText3BackColor.value,LCD4linux.StandbyText3Shadow.value, LCD4linux.StandbyText3File.value
				Lput(LCD4linux.StandbyText3LCD.value,LCD4linux.StandbyText3.value,putTextFile,Para)
# show HTTP Text
				Para = LCD4linux.StandbyHTTPPos.value,LCD4linux.StandbyHTTPSize.value,LCD4linux.StandbyHTTPAlign.value,LCD4linux.StandbyHTTPColor.value,LCD4linux.StandbyHTTPBackColor.value, LCD4linux.StandbyHTTPURL.value, LCD4linux.StandbyHTTPShadow.value, getFont(LCD4linux.StandbyHTTPFont.value)
				Lput(LCD4linux.StandbyHTTPLCD.value,LCD4linux.StandbyHTTP.value,putHTTP,Para)
# show Mail
				Para = LCD4linux.StandbyMailPos.value,LCD4linux.StandbyMailSize.value,LCD4linux.StandbyMailProzent.value,LCD4linux.StandbyMailColor.value,LCD4linux.StandbyMailBackColor.value,LCD4linux.StandbyMailAlign.value,LCD4linux.StandbyMailSplit.value,LCD4linux.StandbyMailLines.value, LCD4linux.StandbyMailType.value, LCD4linux.StandbyMailKonto.value, LCD4linux.StandbyMailShadow.value, getFont(LCD4linux.StandbyMailFont.value)
				Lput(LCD4linux.StandbyMailLCD.value,LCD4linux.StandbyMail.value,putMail,Para)
# show Ereignis Icon Bar
				Para = LCD4linux.StandbyIconBarPos.value,LCD4linux.StandbyIconBarSize.value,LCD4linux.StandbyIconBarAlign.value,LCD4linux.StandbyIconBarSplit.value,LCD4linux.StandbyIconBarType.value,LCD4linux.StandbyIconBarPopup.value,LCD4linux.StandbyIconBarPopupLCD.value
				Lput(LCD4linux.StandbyIconBarLCD.value,LCD4linux.StandbyIconBar.value,putIconBar,Para)
# show Sonnenaufgang
				Para = LCD4linux.StandbySunPos.value,LCD4linux.StandbySunSize.value,LCD4linux.StandbySunColor.value,LCD4linux.StandbySunBackColor.value,LCD4linux.StandbySunAlign.value,LCD4linux.StandbySunSplit.value,LCD4linux.StandbySunType.value,LCD4linux.StandbySunShadow.value,getFont(LCD4linux.StandbySunFont.value)
				Lput(LCD4linux.StandbySunLCD.value,LCD4linux.StandbySun.value,putSun,Para)

# externe Elementeliste
				putL4LElist("Idle")

# FritzCall
				Para = LCD4linux.StandbyFritzPos.value, LCD4linux.StandbyFritzSize.value, LCD4linux.StandbyFritzColor.value, LCD4linux.StandbyFritzBackColor.value, LCD4linux.StandbyFritzAlign.value, LCD4linux.StandbyFritzType.value, LCD4linux.StandbyFritzPicPos.value, LCD4linux.StandbyFritzPicSize.value, LCD4linux.StandbyFritzPicAlign.value, LCD4linux.StandbyFritzShadow.value, getFont(LCD4linux.StandbyFritzFont.value)
				Lput(LCD4linux.StandbyFritzLCD.value,LCD4linux.StandbyFritz.value,putFritz,Para)
# Recording
				Para = LCD4linux.StandbyRecordingPos.value, LCD4linux.StandbyRecordingSize.value, LCD4linux.StandbyRecordingAlign.value, LCD4linux.StandbyRecordingSplit.value, LCD4linux.StandbyRecordingType.value
				Lput(LCD4linux.StandbyRecordingLCD.value,LCD4linux.StandbyRecording.value,putRecording,Para)
		else:
			Dunkel=writeHelligkeit(0,0,0)

####
#### MediaPlayer
####
	elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
		if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4" or LCD4linux.LCDType3.value[0] == "4":
			if "B" in LCD4linux.LCDTFT.value:
				if AktTFT != "BMP":
					TFTCheck(False,SetMode="BMP")
			else:
				if AktTFT != "DREAM":
					TFTCheck(False,SetMode="DREAM")
		Dunkel=writeHelligkeit(LCD4linux.MPHelligkeit.value,LCD4linux.MPHelligkeit2.value,LCD4linux.MPHelligkeit3.value)
# LCDoff
		if LCD4linux.LCDoff.value != LCD4linux.LCDon.value or LCD4linux.LCDWEoff.value != LCD4linux.LCDWEon.value or LCDon == False:
			if isOffTime(LCD4linux.LCDoff.value,LCD4linux.LCDon.value,LCD4linux.LCDWEoff.value,LCD4linux.LCDWEon.value) or LCDon == False:
				Dunkel=writeHelligkeit(0,0,0)
				L4log("LCD off")
# FritzCall
		if LCD4linux.MPFritz.value != "0" and LCD4linux.FritzPopupLCD.value != "0" and FritzTime > 1:
			Para = LCD4linux.MPFritzPos.value, LCD4linux.MPFritzSize.value, LCD4linux.MPFritzColor.value, LCD4linux.MPFritzBackColor.value, LCD4linux.MPFritzAlign.value, LCD4linux.MPFritzType.value, LCD4linux.MPFritzPicPos.value, LCD4linux.MPFritzPicSize.value, LCD4linux.MPFritzPicAlign.value, LCD4linux.MPFritzShadow.value, getFont(LCD4linux.MPFritzFont.value)
			Lput(LCD4linux.FritzPopupLCD.value,"123456789",putFritz,Para)
		else:
# Bild
			if ScreenActive[0] in LCD4linux.MPBild.value or ScreenActive[-3:] != ["","",""]:
				ShowPicture = getShowPicture(LCD4linux.MPBildFile.value,0)
				Para = LCD4linux.MPBildPos.value, LCD4linux.MPBildSize.value, 0, LCD4linux.MPBildAlign.value, LCD4linux.MPBildQuick.value, LCD4linux.MPBildTransp.value, ShowPicture, LCD4linux.MPBildFile.value
				Lput4(LCD4linux.MPBildLCD.value,LCD4linux.MPBild.value,putBild,Para)
# Bild 2
			if ScreenActive[0] in LCD4linux.MPBild2.value or ScreenActive[-3:] != ["","",""]:
				ShowPicture = getShowPicture(LCD4linux.MPBild2File.value,1)
				Para = LCD4linux.MPBild2Pos.value, LCD4linux.MPBild2Size.value, 0, LCD4linux.MPBild2Align.value, LCD4linux.MPBild2Quick.value, LCD4linux.MPBild2Transp.value, ShowPicture, LCD4linux.MPBild2File.value
				Lput4(LCD4linux.MPBild2LCD.value,LCD4linux.MPBild2.value,putBild,Para)
# Cover
			if ScreenActive[0] in LCD4linux.MPCover.value or ScreenActive[-3:] != ["","",""]:
				ShowPicture = getShowCover((LCD4linux.MPCoverPath1.value,LCD4linux.MPCoverPath2.value))
				Para = LCD4linux.MPCoverPos.value, LCD4linux.MPCoverSize.value, LCD4linux.MPCoverSizeH.value, LCD4linux.MPCoverAlign.value, False, LCD4linux.MPCoverTransp.value, ShowPicture, ""
				Lput4(LCD4linux.MPCoverLCD.value,LCD4linux.MPCover.value,putBild,Para)
# Kalender
			Para = LCD4linux.MPCalPos.value,LCD4linux.MPCalZoom.value,LCD4linux.MPCalAlign.value,LCD4linux.MPCalSplit.value,LCD4linux.MPCalType.value,LCD4linux.MPCalTypeE.value,LCD4linux.MPCalLayout.value,LCD4linux.MPCalColor.value,LCD4linux.MPCalBackColor.value,LCD4linux.MPCalCaptionColor.value,LCD4linux.MPCalShadow.value,getFont(LCD4linux.MPCalFont.value)
			Lput(LCD4linux.MPCalLCD.value,LCD4linux.MPCal.value,putCalendar,Para)
# Termin-List
			Para = LCD4linux.MPCalListPos.value,LCD4linux.MPCalListSize.value,LCD4linux.MPCalListProzent.value,LCD4linux.MPCalListAlign.value,LCD4linux.MPCalListSplit.value,LCD4linux.MPCalListType.value,LCD4linux.MPCalListLines.value,LCD4linux.MPCalListColor.value,LCD4linux.MPCalListShadow.value,getFont(LCD4linux.MPCalFont.value)
			Lput(LCD4linux.MPCalListLCD.value,LCD4linux.MPCalList.value,putCalendarList,Para)
# MSN Wetter
			if wwwWetter[0].find("forecast") > 1:
				Para = LCD4linux.MPWetterPos.value,LCD4linux.MPWetterZoom.value,LCD4linux.MPWetterAlign.value,LCD4linux.MPWetterSplit.value,LCD4linux.MPWetterType.value,LCD4linux.MPWetterColor.value,LCD4linux.MPWetterShadow.value,0,getFont(LCD4linux.MPWetterFont.value)
				Lput(LCD4linux.MPWetterLCD.value,LCD4linux.MPWetter.value,putWetter,Para)
			if wwwWetter[1].find("forecast") > 1:
				Para = LCD4linux.MPWetter2Pos.value,LCD4linux.MPWetter2Zoom.value,LCD4linux.MPWetter2Align.value,LCD4linux.MPWetter2Split.value,LCD4linux.MPWetter2Type.value,LCD4linux.MPWetter2Color.value,LCD4linux.MPWetter2Shadow.value,1,getFont(LCD4linux.MPWetter2Font.value)
				Lput(LCD4linux.MPWetter2LCD.value,LCD4linux.MPWetter2.value,putWetter,Para)
# Netatmo CO2
			Para = "CO2",LCD4linux.MPNetAtmoCO2Pos.value,LCD4linux.MPNetAtmoCO2Size.value,LCD4linux.MPNetAtmoCO2Len.value,LCD4linux.MPNetAtmoCO2Align.value,LCD4linux.MPNetAtmoCO2Split.value,LCD4linux.MPNetAtmoCO2Type.value
			Lput(LCD4linux.MPNetAtmoCO2LCD.value,LCD4linux.MPNetAtmoCO2.value,putNetatmoIllu,Para)
# Netatmo IDX
			Para = "IDX",LCD4linux.MPNetAtmoIDXPos.value,LCD4linux.MPNetAtmoIDXSize.value,LCD4linux.MPNetAtmoIDXLen.value,LCD4linux.MPNetAtmoIDXAlign.value,LCD4linux.MPNetAtmoIDXSplit.value,LCD4linux.MPNetAtmoIDXType.value
			Lput(LCD4linux.MPNetAtmoIDXLCD.value,LCD4linux.MPNetAtmoIDX.value,putNetatmoIllu,Para)
			Brief1.join()
			Brief2.join()
			Brief3.join()
# Netatmo
			Para = LCD4linux.MPNetAtmoPos.value,LCD4linux.MPNetAtmoSize.value,LCD4linux.MPNetAtmoAlign.value,LCD4linux.MPNetAtmoSplit.value,LCD4linux.MPNetAtmoType.value,LCD4linux.MPNetAtmoType2.value,LCD4linux.MPNetAtmoColor.value,LCD4linux.MPNetAtmoShadow.value,getFont(LCD4linux.MPNetAtmoFont.value)
			Lput(LCD4linux.MPNetAtmoLCD.value,LCD4linux.MPNetAtmo.value,putNetatmo,Para)
# Meteo station
			if wwwMeteo.find("current_conditions") > 1:
				Para = LCD4linux.MPMeteoPos.value,LCD4linux.MPMeteoZoom.value,LCD4linux.MPMeteoAlign.value,LCD4linux.MPMeteoSplit.value,LCD4linux.MPMeteoType.value,LCD4linux.MPMeteoColor.value
				Lput(LCD4linux.MPMeteoLCD.value,LCD4linux.MPMeteo.value,putMeteo,Para)
# Box 1
			Para = LCD4linux.MPBox1x1.value,LCD4linux.MPBox1y1.value,LCD4linux.MPBox1x2.value,LCD4linux.MPBox1y2.value,LCD4linux.MPBox1Color.value,LCD4linux.MPBox1BackColor.value
			Lput(LCD4linux.MPBox1LCD.value,LCD4linux.MPBox1.value,putBox,Para)
# Box 2
			Para = LCD4linux.MPBox2x1.value,LCD4linux.MPBox2y1.value,LCD4linux.MPBox2x2.value,LCD4linux.MPBox2y2.value,LCD4linux.MPBox2Color.value,LCD4linux.MPBox2BackColor.value
			Lput(LCD4linux.MPBox2LCD.value,LCD4linux.MPBox2.value,putBox,Para)
# Progress Bar
			Para = LCD4linux.MPProgressPos.value, LCD4linux.MPProgressSize.value, LCD4linux.MPProgressType.value, LCD4linux.MPProgressColor.value, LCD4linux.MPProgressAlign.value, LCD4linux.MPProgressShadow.value, LCD4linux.MPProgressShadow2.value
			Lput(LCD4linux.MPProgressLCD.value,LCD4linux.MPProgress.value,putProgress,Para)
# Volume
			Para = LCD4linux.MPVolPos.value, LCD4linux.MPVolSize.value, LCD4linux.MPVolAlign.value, LCD4linux.MPVolSplit.value, LCD4linux.MPVolColor.value, LCD4linux.MPVolShadow.value
			Lput(LCD4linux.MPVolLCD.value,LCD4linux.MPVol.value,putVol,Para)
# extended Description
			Para = LCD4linux.MPDescPos.value, LCD4linux.MPDescSize.value, LCD4linux.MPDescLines.value, LCD4linux.MPDescColor.value, LCD4linux.MPDescAlign.value, LCD4linux.MPDescSplit.value, LCD4linux.MPDescType.value, LCD4linux.MPDescShadow.value, getFont(LCD4linux.MPDescFont.value)
			Lput(LCD4linux.MPDescLCD.value,LCD4linux.MPDesc.value,putDescription,Para)
# Title
			Para = LCD4linux.MPTitlePos.value, LCD4linux.MPTitleSize.value, LCD4linux.MPTitleLines.value, LCD4linux.MPTitleColor.value, LCD4linux.MPTitleAlign.value, LCD4linux.MPTitleSplit.value, LCD4linux.MPTitleShadow.value, getFont(LCD4linux.MPTitleFont.value)
			Lput(LCD4linux.MPTitleLCD.value,LCD4linux.MPTitle.value,putTitle,Para)
# Comm
			Para = LCD4linux.MPCommPos.value, LCD4linux.MPCommSize.value, LCD4linux.MPCommLines.value, LCD4linux.MPCommColor.value, LCD4linux.MPCommAlign.value, LCD4linux.MPCommSplit.value, LCD4linux.MPCommShadow.value, getFont(LCD4linux.MPCommFont.value)
			Lput(LCD4linux.MPCommLCD.value,LCD4linux.MPComm.value,putComm,Para)
# aktive Sendername
			Para = LCD4linux.MPChannelPos.value, LCD4linux.MPChannelSize.value, LCD4linux.MPChannelLines.value, LCD4linux.MPChannelAlign.value, LCD4linux.MPChannelSplit.value, LCD4linux.MPChannelColor.value, LCD4linux.MPChannelShadow.value ,getFont(LCD4linux.MPChannelFont.value)
			Lput(LCD4linux.MPChannelLCD.value,LCD4linux.MPChannel.value,putChannel,Para)
# get clock
			Para = LCD4linux.MPClockPos.value,LCD4linux.MPClockSize.value,LCD4linux.MPClockAlign.value,LCD4linux.MPClockSplit.value,LCD4linux.MPClockType.value,LCD4linux.MPClockSpacing.value,LCD4linux.MPClockAnalog.value,LCD4linux.MPClockColor.value,LCD4linux.MPClockShadow.value,getFont(LCD4linux.MPClockFont.value)
			Lput(LCD4linux.MPClockLCD.value,LCD4linux.MPClock.value,putClock,Para)
			Para = LCD4linux.MPClock2Pos.value,LCD4linux.MPClock2Size.value,LCD4linux.MPClock2Align.value,LCD4linux.MPClock2Split.value,LCD4linux.MPClock2Type.value,LCD4linux.MPClock2Spacing.value,LCD4linux.MPClock2Analog.value,LCD4linux.MPClock2Color.value,LCD4linux.MPClock2Shadow.value,getFont(LCD4linux.MPClock2Font.value)
			Lput(LCD4linux.MPClock2LCD.value,LCD4linux.MPClock2.value,putClock,Para)
# Informationen
			Para = LCD4linux.MPInfoPos.value, LCD4linux.MPInfoSize.value,LCD4linux.MPInfoAlign.value,LCD4linux.MPInfoLines.value,LCD4linux.MPInfoSplit.value,LCD4linux.MPInfoColor.value,LCD4linux.MPInfoSensor.value+LCD4linux.MPInfoCPU.value, LCD4linux.MPInfoShadow.value, getFont(LCD4linux.MPInfoFont.value)
			Lput(LCD4linux.MPInfoLCD.value,LCD4linux.MPInfo.value,putInfo,Para)
# next Timer Record
			Para = LCD4linux.MPTimerPos.value, LCD4linux.MPTimerSize.value, LCD4linux.MPTimerLines.value, LCD4linux.MPTimerType.value, LCD4linux.MPTimerAlign.value, LCD4linux.MPTimerSplit.value, LCD4linux.MPTimerColor.value, LCD4linux.MPTimerShadow.value, getFont(LCD4linux.MPTimerFont.value)
			Lput(LCD4linux.MPTimerLCD.value,LCD4linux.MPTimer.value,putTimer,Para)
# Tuner
			Para = LCD4linux.MPTunerPos.value, LCD4linux.MPTunerSize.value, LCD4linux.MPTunerAlign.value, LCD4linux.MPTunerSplit.value, LCD4linux.MPTunerType.value, LCD4linux.MPTunerActive.value,getFont(LCD4linux.MPTunerFont.value)
			Lput(LCD4linux.MPTunerLCD.value,LCD4linux.MPTuner.value,putTuner,Para)
# Audio/Video
			Para = LCD4linux.MPAVPos.value, LCD4linux.MPAVSize.value, LCD4linux.MPAVAlign.value, LCD4linux.MPAVSplit.value, LCD4linux.MPAVColor.value, LCD4linux.MPAVShadow.value, LCD4linux.MPAVType.value, getFont(LCD4linux.MPAVFont.value)
			Lput(LCD4linux.MPAVLCD.value,LCD4linux.MPAV.value,putAV,Para)
# Bitrate
			Para = LCD4linux.MPBitratePos.value, LCD4linux.MPBitrateSize.value, LCD4linux.MPBitrateAlign.value, LCD4linux.MPBitrateSplit.value, LCD4linux.MPBitrateColor.value, LCD4linux.MPBitrateShadow.value,getFont(LCD4linux.MPBitrateFont.value)
			Lput(LCD4linux.MPBitrateLCD.value,LCD4linux.MPBitrate.value,putBitrate,Para)
# Moonphase
			Para = LCD4linux.MPMoonPos.value,LCD4linux.MPMoonSize.value,LCD4linux.MPMoonAlign.value,LCD4linux.MPMoonSplit.value,LCD4linux.MPMoonColor.value,LCD4linux.MPMoonShadow.value,getFont(LCD4linux.MPMoonFont.value)
			Lput(LCD4linux.MPMoonLCD.value,LCD4linux.MPMoon.value,putMoon,Para)
# Online-Ping
			Para = LCD4linux.MPPingPos.value, LCD4linux.MPPingSize.value, LCD4linux.MPPingAlign.value, LCD4linux.MPPingSplit.value, LCD4linux.MPPingColor.value, LCD4linux.MPPingType.value, LCD4linux.MPPingShow.value, LCD4linux.MPPingTimeout.value, (LCD4linux.MPPingName1.value,LCD4linux.MPPingName2.value,LCD4linux.MPPingName3.value,LCD4linux.MPPingName4.value,LCD4linux.MPPingName5.value), LCD4linux.MPPingShadow.value,getFont(LCD4linux.MPPingFont.value)
			Lput(LCD4linux.MPPingLCD.value,LCD4linux.MPPing.value,putOnline,Para)
# Devices
			Para = LCD4linux.MPDevPos.value, LCD4linux.MPDevSize.value, LCD4linux.MPDevAlign.value, LCD4linux.MPDevSplit.value, LCD4linux.MPDevColor.value, (LCD4linux.MPDevExtra.value,LCD4linux.MPDevName1.value,LCD4linux.MPDevName2.value,LCD4linux.MPDevName3.value,LCD4linux.MPDevName4.value,LCD4linux.MPDevName5.value), LCD4linux.MPDevShadow.value, LCD4linux.MPDevType.value,getFont(LCD4linux.MPDevFont.value)
			Lput(LCD4linux.MPDevLCD.value,LCD4linux.MPDev.value,putDev,Para)
# HDD
			Para = LCD4linux.MPHddPos.value, LCD4linux.MPHddSize.value, LCD4linux.MPHddAlign.value, LCD4linux.MPHddSplit.value, LCD4linux.MPHddType.value
			Lput(LCD4linux.MPHddLCD.value,LCD4linux.MPHdd.value,putHdd,Para)
# show OSCAM
			Para = LCD4linux.MPOSCAMPos.value, LCD4linux.MPOSCAMSize.value, LCD4linux.MPOSCAMColor.value, LCD4linux.MPOSCAMBackColor.value, LCD4linux.MPOSCAMAlign.value, LCD4linux.MPOSCAMSplit.value
			Lput(LCD4linux.MPOSCAMLCD.value,LCD4linux.MPOSCAM.value,putOSCAM,Para)
# show Textfile
			Para = LCD4linux.MPTextPos.value,LCD4linux.MPTextSize.value,getFont(LCD4linux.MPTextFont.value),LCD4linux.MPTextAlign.value,LCD4linux.MPTextColor.value,LCD4linux.MPTextBackColor.value,LCD4linux.MPTextShadow.value, LCD4linux.MPTextFile.value
			Lput(LCD4linux.MPTextLCD.value,LCD4linux.MPText.value,putTextFile,Para)
# show Mail
			Para = LCD4linux.MPMailPos.value,LCD4linux.MPMailSize.value,LCD4linux.MPMailProzent.value,LCD4linux.MPMailColor.value,LCD4linux.MPMailBackColor.value,LCD4linux.MPMailAlign.value,LCD4linux.MPMailSplit.value,LCD4linux.MPMailLines.value, LCD4linux.MPMailType.value, LCD4linux.MPMailKonto.value, LCD4linux.MPMailShadow.value, getFont(LCD4linux.MPMailFont.value)
			Lput(LCD4linux.MPMailLCD.value,LCD4linux.MPMail.value,putMail,Para)
# show Ereignis Icon Bar
			Para = LCD4linux.MPIconBarPos.value,LCD4linux.MPIconBarSize.value,LCD4linux.MPIconBarAlign.value,LCD4linux.MPIconBarSplit.value,LCD4linux.MPIconBarType.value,LCD4linux.MPIconBarPopup.value,LCD4linux.MPIconBarPopupLCD.value
			Lput(LCD4linux.MPIconBarLCD.value,LCD4linux.MPIconBar.value,putIconBar,Para)
# show Sonnenaufgang
			Para = LCD4linux.MPSunPos.value,LCD4linux.MPSunSize.value,LCD4linux.MPSunColor.value,LCD4linux.MPSunBackColor.value,LCD4linux.MPSunAlign.value,LCD4linux.MPSunSplit.value,LCD4linux.MPSunType.value,LCD4linux.MPSunShadow.value,getFont(LCD4linux.MPSunFont.value)
			Lput(LCD4linux.MPSunLCD.value,LCD4linux.MPSun.value,putSun,Para)

# externe Elementeliste
			putL4LElist("Media")

# FritzCall
			Para = LCD4linux.MPFritzPos.value, LCD4linux.MPFritzSize.value, LCD4linux.MPFritzColor.value, LCD4linux.MPFritzBackColor.value, LCD4linux.MPFritzAlign.value, LCD4linux.MPFritzType.value, LCD4linux.MPFritzPicPos.value, LCD4linux.MPFritzPicSize.value, LCD4linux.MPFritzPicAlign.value, LCD4linux.MPFritzShadow.value, getFont(LCD4linux.MPFritzFont.value)
			Lput(LCD4linux.MPFritzLCD.value,LCD4linux.MPFritz.value,putFritz,Para)
# Recording
			Para = LCD4linux.MPRecordingPos.value, LCD4linux.MPRecordingSize.value, LCD4linux.MPRecordingAlign.value, LCD4linux.MPRecordingSplit.value, LCD4linux.MPRecordingType.value
			Lput(LCD4linux.MPRecordingLCD.value,LCD4linux.MPRecording.value,putRecording,Para)
# show OSD
			if LCD4linux.OSD.value != "0" and ConfigMode == False and FritzTime == 0:
				if OSDon >= 2 and "M" in LCD4linux.OSDshow.value:
					if "1" in LCD4linux.OSDLCD.value:
						Brief1.put([putGrab,LCD4linux.OSDfast.value, LCD4linux.OSDsize.value,im,draw])
					if "2" in LCD4linux.OSDLCD.value and LCD4linux.LCDType2.value != "00":
						Brief2.put([putGrab,LCD4linux.OSDfast.value, LCD4linux.OSDsize.value,im2,draw2])
					if "3" in LCD4linux.OSDLCD.value and LCD4linux.LCDType3.value != "00":
						Brief3.put([putGrab,LCD4linux.OSDfast.value, LCD4linux.OSDsize.value,im3,draw3])
					if OSDon == 3:
						OSDon = 2
	else:
####
#### ON Modus
####
		if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4" or LCD4linux.LCDType3.value[0] == "4":
			if "A" in LCD4linux.LCDTFT.value:
				if AktTFT != "BMP":
					TFTCheck(False,SetMode="BMP")
			else:
				if AktTFT != "DREAM":
					TFTCheck(False,SetMode="DREAM")
		Dunkel=writeHelligkeit(LCD4linux.Helligkeit.value,LCD4linux.Helligkeit2.value,LCD4linux.Helligkeit3.value)
# LCDoff
		if LCD4linux.LCDoff.value != LCD4linux.LCDon.value or LCD4linux.LCDWEoff.value != LCD4linux.LCDWEon.value or LCDon == False:
			if isOffTime(LCD4linux.LCDoff.value,LCD4linux.LCDon.value,LCD4linux.LCDWEoff.value,LCD4linux.LCDWEon.value) or LCDon == False:
				Dunkel=writeHelligkeit(0,0,0)
				L4log("LCD off")
# FritzCall
		if LCD4linux.Fritz.value != "0" and LCD4linux.FritzPopupLCD.value != "0" and FritzTime > 1:
			Para = LCD4linux.FritzPos.value, LCD4linux.FritzSize.value, LCD4linux.FritzColor.value, LCD4linux.FritzBackColor.value, LCD4linux.FritzAlign.value, LCD4linux.FritzType.value, LCD4linux.FritzPicPos.value, LCD4linux.FritzPicSize.value, LCD4linux.FritzPicAlign.value, LCD4linux.FritzShadow.value, getFont(LCD4linux.FritzFont.value)
			Lput(LCD4linux.FritzPopupLCD.value,"123456789",putFritz,Para)
		else:
# Bild
			if ScreenActive[0] in LCD4linux.Bild.value or ScreenActive[-3:] != ["","",""]:
				ShowPicture = getShowPicture(LCD4linux.BildFile.value,0)
				Para = LCD4linux.BildPos.value, LCD4linux.BildSize.value, 0, LCD4linux.BildAlign.value, LCD4linux.BildQuick.value, LCD4linux.BildTransp.value, ShowPicture, LCD4linux.BildFile.value
				Lput4(LCD4linux.BildLCD.value,LCD4linux.Bild.value,putBild,Para)
# Bild 2
			if ScreenActive[0] in LCD4linux.Bild2.value or ScreenActive[-3:] != ["","",""]:
				ShowPicture = getShowPicture(LCD4linux.Bild2File.value,1)
				Para = LCD4linux.Bild2Pos.value, LCD4linux.Bild2Size.value, 0, LCD4linux.Bild2Align.value, LCD4linux.Bild2Quick.value, LCD4linux.Bild2Transp.value, ShowPicture, LCD4linux.Bild2File.value
				Lput4(LCD4linux.Bild2LCD.value,LCD4linux.Bild2.value,putBild,Para)
# Bild 3
			if ScreenActive[0] in LCD4linux.Bild3.value or ScreenActive[-3:] != ["","",""]:
				ShowPicture = getShowPicture(LCD4linux.Bild3File.value,2)
				Para = LCD4linux.Bild3Pos.value, LCD4linux.Bild3Size.value, 0, LCD4linux.Bild3Align.value, LCD4linux.Bild3Quick.value, LCD4linux.Bild3Transp.value, ShowPicture, LCD4linux.Bild3File.value
				Lput4(LCD4linux.Bild3LCD.value,LCD4linux.Bild3.value,putBild,Para)
# Bild 4
			if ScreenActive[0] in LCD4linux.Bild4.value or ScreenActive[-3:] != ["","",""]:
				ShowPicture = getShowPicture(LCD4linux.Bild4File.value,0)
				Para = LCD4linux.Bild4Pos.value, LCD4linux.Bild4Size.value, 0, LCD4linux.Bild4Align.value, LCD4linux.Bild4Quick.value, LCD4linux.Bild4Transp.value, ShowPicture, LCD4linux.Bild4File.value
				Lput4(LCD4linux.Bild4LCD.value,LCD4linux.Bild4.value,putBild,Para)
# Picon
			Para = LCD4linux.PiconSize.value, LCD4linux.PiconPos.value, LCD4linux.PiconAlign.value, LCD4linux.PiconFullScreen.value, LCD4linux.PiconSplit.value, LCD4linux.PiconTextSize.value, False
			Lput(LCD4linux.PiconLCD.value,LCD4linux.Picon.value,putPicon,Para)
# Picon 2
			Para = LCD4linux.Picon2Size.value, LCD4linux.Picon2Pos.value, LCD4linux.Picon2Align.value, LCD4linux.Picon2FullScreen.value, LCD4linux.Picon2Split.value, LCD4linux.Picon2TextSize.value, True
			Lput(LCD4linux.Picon2LCD.value,LCD4linux.Picon2.value,putPicon,Para)
# Kalender
			Para = LCD4linux.CalPos.value,LCD4linux.CalZoom.value,LCD4linux.CalAlign.value,LCD4linux.CalSplit.value,LCD4linux.CalType.value,LCD4linux.CalTypeE.value,LCD4linux.CalLayout.value,LCD4linux.CalColor.value,LCD4linux.CalBackColor.value,LCD4linux.CalCaptionColor.value,LCD4linux.CalShadow.value,getFont(LCD4linux.CalFont.value)
			Lput(LCD4linux.CalLCD.value,LCD4linux.Cal.value,putCalendar,Para)
# Termin-List
			Para = LCD4linux.CalListPos.value,LCD4linux.CalListSize.value,LCD4linux.CalListProzent.value,LCD4linux.CalListAlign.value,LCD4linux.CalListSplit.value,LCD4linux.CalListType.value,LCD4linux.CalListLines.value,LCD4linux.CalListColor.value,LCD4linux.CalListShadow.value,getFont(LCD4linux.CalFont.value)
			Lput(LCD4linux.CalListLCD.value,LCD4linux.CalList.value,putCalendarList,Para)
# MSN Wetter
			if "forecast" in wwwWetter[0]:
				Para = LCD4linux.WetterPos.value,LCD4linux.WetterZoom.value,LCD4linux.WetterAlign.value,LCD4linux.WetterSplit.value,LCD4linux.WetterType.value,LCD4linux.WetterColor.value,LCD4linux.WetterShadow.value,0,getFont(LCD4linux.WetterFont.value)
				Lput(LCD4linux.WetterLCD.value,LCD4linux.Wetter.value,putWetter,Para)
			if "forecast" in wwwWetter[1]:
				Para = LCD4linux.Wetter2Pos.value,LCD4linux.Wetter2Zoom.value,LCD4linux.Wetter2Align.value,LCD4linux.Wetter2Split.value,LCD4linux.Wetter2Type.value,LCD4linux.Wetter2Color.value,LCD4linux.Wetter2Shadow.value,1,getFont(LCD4linux.Wetter2Font.value)
				Lput(LCD4linux.Wetter2LCD.value,LCD4linux.Wetter2.value,putWetter,Para)
# Netatmo CO2
			Para = "CO2",LCD4linux.NetAtmoCO2Pos.value,LCD4linux.NetAtmoCO2Size.value,LCD4linux.NetAtmoCO2Len.value,LCD4linux.NetAtmoCO2Align.value,LCD4linux.NetAtmoCO2Split.value,LCD4linux.NetAtmoCO2Type.value
			Lput(LCD4linux.NetAtmoCO2LCD.value,LCD4linux.NetAtmoCO2.value,putNetatmoIllu,Para)
# Netatmo IDX
			Para = "IDX",LCD4linux.NetAtmoIDXPos.value,LCD4linux.NetAtmoIDXSize.value,LCD4linux.NetAtmoIDXLen.value,LCD4linux.NetAtmoIDXAlign.value,LCD4linux.NetAtmoIDXSplit.value,LCD4linux.NetAtmoIDXType.value
			Lput(LCD4linux.NetAtmoIDXLCD.value,LCD4linux.NetAtmoIDX.value,putNetatmoIllu,Para)
# HTTP WWW Site
			Para = 1,LCD4linux.WWW1Pos.value,LCD4linux.WWW1Size.value,LCD4linux.WWW1Align.value,LCD4linux.WWW1CutX.value,LCD4linux.WWW1CutY.value,LCD4linux.WWW1CutW.value,LCD4linux.WWW1CutH.value
			Lput(LCD4linux.WWW1LCD.value,LCD4linux.WWW1.value,putWWW,Para)
			Brief1.join()
			Brief2.join()
			Brief3.join()
# Box 1
			Para = LCD4linux.Box1x1.value,LCD4linux.Box1y1.value,LCD4linux.Box1x2.value,LCD4linux.Box1y2.value,LCD4linux.Box1Color.value,LCD4linux.Box1BackColor.value
			Lput(LCD4linux.Box1LCD.value,LCD4linux.Box1.value,putBox,Para)
# Box 2
			Para = LCD4linux.Box2x1.value,LCD4linux.Box2y1.value,LCD4linux.Box2x2.value,LCD4linux.Box2y2.value,LCD4linux.Box2Color.value,LCD4linux.Box2BackColor.value
			Lput(LCD4linux.Box2LCD.value,LCD4linux.Box2.value,putBox,Para)
# Moonphase
			Para = LCD4linux.MoonPos.value,LCD4linux.MoonSize.value,LCD4linux.MoonAlign.value,LCD4linux.MoonSplit.value,LCD4linux.MoonColor.value,LCD4linux.MoonShadow.value,getFont(LCD4linux.MoonFont.value)
			Lput(LCD4linux.MoonLCD.value,LCD4linux.Moon.value,putMoon,Para)
# Netatmo
			Para = LCD4linux.NetAtmoPos.value,LCD4linux.NetAtmoSize.value,LCD4linux.NetAtmoAlign.value,LCD4linux.NetAtmoSplit.value,LCD4linux.NetAtmoType.value,LCD4linux.NetAtmoType2.value,LCD4linux.NetAtmoColor.value,LCD4linux.NetAtmoShadow.value,getFont(LCD4linux.NetAtmoFont.value)
			Lput(LCD4linux.NetAtmoLCD.value,LCD4linux.NetAtmo.value,putNetatmo,Para)
# Meteo station
			if wwwMeteo.find("current_conditions") > 1:
				Para = LCD4linux.MeteoPos.value,LCD4linux.MeteoZoom.value,LCD4linux.MeteoAlign.value,LCD4linux.MeteoSplit.value,LCD4linux.MeteoType.value,LCD4linux.MeteoColor.value
				Lput(LCD4linux.MeteoLCD.value,LCD4linux.Meteo.value,putMeteo,Para)
# Signal Quality Bar
			Para = LCD4linux.SignalPos.value, LCD4linux.SignalSize.value, LCD4linux.SignalAlign.value, LCD4linux.SignalSplit.value, LCD4linux.SignalColor.value, LCD4linux.SignalGradient.value
			Lput(LCD4linux.SignalLCD.value,LCD4linux.Signal.value,putSignal,Para)
# get clock
			Para = LCD4linux.ClockPos.value,LCD4linux.ClockSize.value,LCD4linux.ClockAlign.value,LCD4linux.ClockSplit.value,LCD4linux.ClockType.value,LCD4linux.ClockSpacing.value,LCD4linux.ClockAnalog.value,LCD4linux.ClockColor.value,LCD4linux.ClockShadow.value,getFont(LCD4linux.ClockFont.value)
			Lput(LCD4linux.ClockLCD.value,LCD4linux.Clock.value,putClock,Para)
			Para = LCD4linux.Clock2Pos.value,LCD4linux.Clock2Size.value,LCD4linux.Clock2Align.value,LCD4linux.Clock2Split.value,LCD4linux.Clock2Type.value,LCD4linux.Clock2Spacing.value,LCD4linux.Clock2Analog.value,LCD4linux.Clock2Color.value,LCD4linux.Clock2Shadow.value,getFont(LCD4linux.Clock2Font.value)
			Lput(LCD4linux.Clock2LCD.value,LCD4linux.Clock2.value,putClock,Para)
# Informationen
			Para = LCD4linux.InfoPos.value, LCD4linux.InfoSize.value,LCD4linux.InfoAlign.value,LCD4linux.InfoLines.value,LCD4linux.InfoSplit.value,LCD4linux.InfoColor.value,LCD4linux.InfoTuner.value+LCD4linux.InfoSensor.value+LCD4linux.InfoCPU.value, LCD4linux.InfoShadow.value, getFont(LCD4linux.InfoFont.value)
			Lput(LCD4linux.InfoLCD.value,LCD4linux.Info.value,putInfo,Para)
# Satellit
			Para = LCD4linux.SatPos.value, LCD4linux.SatSize.value, LCD4linux.SatAlign.value, LCD4linux.SatSplit.value, LCD4linux.SatColor.value, LCD4linux.SatType.value, LCD4linux.SatShadow.value, getFont(LCD4linux.SatFont.value)
			Lput(LCD4linux.SatLCD.value,LCD4linux.Sat.value,putSat,Para)
# Provider
			Para = LCD4linux.ProvPos.value, LCD4linux.ProvSize.value, LCD4linux.ProvAlign.value, LCD4linux.ProvSplit.value, LCD4linux.ProvColor.value, LCD4linux.ProvType.value, LCD4linux.ProvShadow.value, getFont(LCD4linux.ProvFont.value)
			Lput(LCD4linux.ProvLCD.value,LCD4linux.Prov.value,putProv,Para)
# next Timer Record
			Para = LCD4linux.TimerPos.value, LCD4linux.TimerSize.value, LCD4linux.TimerLines.value, LCD4linux.TimerType.value, LCD4linux.TimerAlign.value, LCD4linux.TimerSplit.value, LCD4linux.TimerColor.value, LCD4linux.TimerShadow.value, getFont(LCD4linux.TimerFont.value)
			Lput(LCD4linux.TimerLCD.value,LCD4linux.Timer.value,putTimer,Para)
# aktive Sendernummer
			Para = LCD4linux.ChannelNumPos.value, LCD4linux.ChannelNumSize.value, LCD4linux.ChannelNumAlign.value, LCD4linux.ChannelNumBackColor.value, LCD4linux.ChannelNumColor.value, LCD4linux.ChannelNumShadow.value ,getFont(LCD4linux.ChannelNumFont.value)
			Lput(LCD4linux.ChannelNumLCD.value,LCD4linux.ChannelNum.value,putChannelNum,Para)
# aktive Sendername
			Para = LCD4linux.ChannelPos.value, LCD4linux.ChannelSize.value, LCD4linux.ChannelLines.value, LCD4linux.ChannelAlign.value, LCD4linux.ChannelSplit.value, LCD4linux.ChannelColor.value, LCD4linux.ChannelShadow.value ,getFont(LCD4linux.ChannelFont.value)
			Lput(LCD4linux.ChannelLCD.value,LCD4linux.Channel.value,putChannel,Para)
# Progress Bar
			Para = LCD4linux.ProgressPos.value, LCD4linux.ProgressSize.value, LCD4linux.ProgressType.value, LCD4linux.ProgressColor.value, LCD4linux.ProgressAlign.value, LCD4linux.ProgressShadow.value, LCD4linux.ProgressShadow2.value
			Lput(LCD4linux.ProgressLCD.value,LCD4linux.Progress.value,putProgress,Para)
# Volume
			Para = LCD4linux.VolPos.value, LCD4linux.VolSize.value, LCD4linux.VolAlign.value, LCD4linux.VolSplit.value, LCD4linux.VolColor.value, LCD4linux.VolShadow.value
			Lput(LCD4linux.VolLCD.value,LCD4linux.Vol.value,putVol,Para)
# extended Description
			Para = LCD4linux.DescPos.value, LCD4linux.DescSize.value, LCD4linux.DescLines.value, LCD4linux.DescColor.value, LCD4linux.DescAlign.value, LCD4linux.DescSplit.value, LCD4linux.DescType.value, LCD4linux.DescShadow.value, getFont(LCD4linux.DescFont.value)
			Lput(LCD4linux.DescLCD.value,LCD4linux.Desc.value,putDescription,Para)
# aktive Event
			Para = LCD4linux.ProgPos.value, LCD4linux.ProgSize.value, LCD4linux.ProgLines.value, LCD4linux.ProgType.value, LCD4linux.ProgColor.value, LCD4linux.ProgAlign.value, LCD4linux.ProgSplit.value, LCD4linux.ProgShadow.value, getFont(LCD4linux.ProgFont.value)
			Lput(LCD4linux.ProgLCD.value,LCD4linux.Prog.value,putProg,Para)
# next Event
			Para = LCD4linux.ProgNextPos.value, LCD4linux.ProgNextSize.value, LCD4linux.ProgNextLines.value, LCD4linux.ProgNextType.value, LCD4linux.ProgNextColor.value, LCD4linux.ProgNextAlign.value, LCD4linux.ProgNextSplit.value, LCD4linux.ProgNextShadow.value, getFont(LCD4linux.ProgNextFont.value)
			Lput(LCD4linux.ProgNextLCD.value,LCD4linux.ProgNext.value,putProgNext,Para)
# Tuner
			Para = LCD4linux.TunerPos.value, LCD4linux.TunerSize.value, LCD4linux.TunerAlign.value, LCD4linux.TunerSplit.value, LCD4linux.TunerType.value, LCD4linux.TunerActive.value,getFont(LCD4linux.TunerFont.value)
			Lput(LCD4linux.TunerLCD.value,LCD4linux.Tuner.value,putTuner,Para)
# Audio/Video
			Para = LCD4linux.AVPos.value, LCD4linux.AVSize.value, LCD4linux.AVAlign.value, LCD4linux.AVSplit.value, LCD4linux.AVColor.value, LCD4linux.AVShadow.value, LCD4linux.AVType.value, getFont(LCD4linux.AVFont.value)
			Lput(LCD4linux.AVLCD.value,LCD4linux.AV.value,putAV,Para)
# Bitrate
			Para = LCD4linux.BitratePos.value, LCD4linux.BitrateSize.value, LCD4linux.BitrateAlign.value, LCD4linux.BitrateSplit.value, LCD4linux.BitrateColor.value, LCD4linux.BitrateShadow.value,getFont(LCD4linux.BitrateFont.value)
			Lput(LCD4linux.BitrateLCD.value,LCD4linux.Bitrate.value,putBitrate,Para)
# Online-Ping
			Para = LCD4linux.PingPos.value, LCD4linux.PingSize.value, LCD4linux.PingAlign.value, LCD4linux.PingSplit.value, LCD4linux.PingColor.value, LCD4linux.PingType.value, LCD4linux.PingShow.value, LCD4linux.PingTimeout.value, (LCD4linux.PingName1.value,LCD4linux.PingName2.value,LCD4linux.PingName3.value,LCD4linux.PingName4.value,LCD4linux.PingName5.value), LCD4linux.PingShadow.value,getFont(LCD4linux.PingFont.value)
			Lput(LCD4linux.PingLCD.value,LCD4linux.Ping.value,putOnline,Para)
# Devices
			Para = LCD4linux.DevPos.value, LCD4linux.DevSize.value, LCD4linux.DevAlign.value, LCD4linux.DevSplit.value, LCD4linux.DevColor.value, (LCD4linux.DevExtra.value,LCD4linux.DevName1.value,LCD4linux.DevName2.value,LCD4linux.DevName3.value,LCD4linux.DevName4.value,LCD4linux.DevName5.value), LCD4linux.DevShadow.value, LCD4linux.DevType.value,getFont(LCD4linux.DevFont.value)
			Lput(LCD4linux.DevLCD.value,LCD4linux.Dev.value,putDev,Para)
# HDD
			Para = LCD4linux.HddPos.value, LCD4linux.HddSize.value, LCD4linux.HddAlign.value, LCD4linux.HddSplit.value, LCD4linux.HddType.value
			Lput(LCD4linux.HddLCD.value,LCD4linux.Hdd.value,putHdd,Para)
# show OSCAM
			Para = LCD4linux.OSCAMPos.value, LCD4linux.OSCAMSize.value, LCD4linux.OSCAMColor.value, LCD4linux.OSCAMBackColor.value, LCD4linux.OSCAMAlign.value, LCD4linux.OSCAMSplit.value
			Lput(LCD4linux.OSCAMLCD.value,LCD4linux.OSCAM.value,putOSCAM,Para)
# show ECM
			Para = LCD4linux.ECMPos.value, LCD4linux.ECMSize.value, LCD4linux.ECMColor.value, LCD4linux.ECMBackColor.value, LCD4linux.ECMAlign.value, LCD4linux.ECMSplit.value
			Lput(LCD4linux.ECMLCD.value,LCD4linux.ECM.value,putECM,Para)
# show Textfile
			Para = LCD4linux.TextPos.value,LCD4linux.TextSize.value,getFont(LCD4linux.TextFont.value),LCD4linux.TextAlign.value,LCD4linux.TextColor.value,LCD4linux.TextBackColor.value,LCD4linux.TextShadow.value, LCD4linux.TextFile.value
			Lput(LCD4linux.TextLCD.value,LCD4linux.Text.value,putTextFile,Para)
# show Textfile 2
			Para = LCD4linux.Text2Pos.value,LCD4linux.Text2Size.value,getFont(LCD4linux.Text2Font.value),LCD4linux.Text2Align.value,LCD4linux.Text2Color.value,LCD4linux.Text2BackColor.value,LCD4linux.Text2Shadow.value, LCD4linux.Text2File.value
			Lput(LCD4linux.Text2LCD.value,LCD4linux.Text2.value,putTextFile,Para)
# show Textfile 3
			Para = LCD4linux.Text3Pos.value,LCD4linux.Text3Size.value,getFont(LCD4linux.Text3Font.value),LCD4linux.Text3Align.value,LCD4linux.Text3Color.value,LCD4linux.Text3BackColor.value,LCD4linux.Text3Shadow.value, LCD4linux.Text3File.value
			Lput(LCD4linux.Text3LCD.value,LCD4linux.Text3.value,putTextFile,Para)
# show HTTP Text
			Para = LCD4linux.HTTPPos.value,LCD4linux.HTTPSize.value,LCD4linux.HTTPAlign.value,LCD4linux.HTTPColor.value,LCD4linux.HTTPBackColor.value, LCD4linux.HTTPURL.value, LCD4linux.HTTPShadow.value, getFont(LCD4linux.HTTPFont.value)
			Lput(LCD4linux.HTTPLCD.value,LCD4linux.HTTP.value,putHTTP,Para)
# show Mail
			Para = LCD4linux.MailPos.value,LCD4linux.MailSize.value,LCD4linux.MailProzent.value,LCD4linux.MailColor.value,LCD4linux.MailBackColor.value,LCD4linux.MailAlign.value,LCD4linux.MailSplit.value,LCD4linux.MailLines.value, LCD4linux.MailType.value, LCD4linux.MailKonto.value, LCD4linux.MailShadow.value, getFont(LCD4linux.MailFont.value)
			Lput(LCD4linux.MailLCD.value,LCD4linux.Mail.value,putMail,Para)
# show Ereignis Icon Bar
			Para = LCD4linux.IconBarPos.value,LCD4linux.IconBarSize.value,LCD4linux.IconBarAlign.value,LCD4linux.IconBarSplit.value,LCD4linux.IconBarType.value,LCD4linux.IconBarPopup.value,LCD4linux.IconBarPopupLCD.value
			Lput(LCD4linux.IconBarLCD.value,LCD4linux.IconBar.value,putIconBar,Para)
# show Sonnenaufgang
			Para = LCD4linux.SunPos.value,LCD4linux.SunSize.value,LCD4linux.SunColor.value,LCD4linux.SunBackColor.value,LCD4linux.SunAlign.value,LCD4linux.SunSplit.value,LCD4linux.SunType.value,LCD4linux.SunShadow.value,getFont(LCD4linux.SunFont.value)
			Lput(LCD4linux.SunLCD.value,LCD4linux.Sun.value,putSun,Para)

# externe Elementeliste
			putL4LElist("On")

# FritzCall
			Para = LCD4linux.FritzPos.value, LCD4linux.FritzSize.value, LCD4linux.FritzColor.value, LCD4linux.FritzBackColor.value, LCD4linux.FritzAlign.value, LCD4linux.FritzType.value, LCD4linux.FritzPicPos.value, LCD4linux.FritzPicSize.value, LCD4linux.FritzPicAlign.value, LCD4linux.FritzShadow.value, getFont(LCD4linux.FritzFont.value)
			Lput(LCD4linux.FritzLCD.value,LCD4linux.Fritz.value,putFritz,Para)
# Recording
			Para = LCD4linux.RecordingPos.value, LCD4linux.RecordingSize.value, LCD4linux.RecordingAlign.value, LCD4linux.RecordingSplit.value, LCD4linux.RecordingType.value
			Lput(LCD4linux.RecordingLCD.value,LCD4linux.Recording.value,putRecording,Para)
# show OSD
			if LCD4linux.OSD.value != "0" and ConfigMode == False and FritzTime == 0:
				if OSDon >= 2 and ((isMediaPlayer == "" and "T" in LCD4linux.OSDshow.value) or (isMediaPlayer == "radio" and "R" in LCD4linux.OSDshow.value)):
					if "1" in LCD4linux.OSDLCD.value:
						Brief1.put([putGrab,LCD4linux.OSDfast.value, LCD4linux.OSDsize.value,im,draw])
					if "2" in LCD4linux.OSDLCD.value and LCD4linux.LCDType2.value != "00":
						Brief2.put([putGrab,LCD4linux.OSDfast.value, LCD4linux.OSDsize.value,im2,draw2])
					if "3" in LCD4linux.OSDLCD.value and LCD4linux.LCDType3.value != "00":
						Brief3.put([putGrab,LCD4linux.OSDfast.value, LCD4linux.OSDsize.value,im3,draw3])
					if OSDon == 3:
						OSDon = 2
# Ende
##################
	q1,q2,q3 = Brief1.qsize(),Brief2.qsize(),Brief3.qsize()
	tw = time()
	tp = tw-tt
	Brief1.join()
	Brief2.join()
	Brief3.join()
	PUSH = "Push: %.3f (%d/%d/%d) Wait: %.3f" % (tp,q1,q2,q3,(time() - tw)) 
	L4log(PUSH)
# PopupText
	if ScreenActive[0] in LCD4linux.Popup.value and len(PopText[1]) > 2:
		Para = LCD4linux.PopupPos.value, LCD4linux.PopupSize.value, LCD4linux.PopupColor.value, LCD4linux.PopupBackColor.value, LCD4linux.PopupAlign.value
		if "1" in LCD4linux.PopupLCD.value:
			Brief1.put([putPopup,Para, draw, im])
		if "2" in LCD4linux.PopupLCD.value and LCD4linux.LCDType2.value != "00":
			Brief2.put([putPopup,Para, draw2, im2])
		if "3" in LCD4linux.PopupLCD.value and LCD4linux.LCDType3.value != "00":
			Brief2.put([putPopup,Para, draw3, im3])
# show isCrashlog
	if LCD4linux.Crash.value == True:
		Brief1.put([putCrash,draw,im])
	Brief1.join()
	Brief2.join()
	Brief3.join()

	if Dunkel and "1" in Dunkel:
		MAX_W,MAX_H = im.size
		draw.rectangle((0, 0, MAX_W, MAX_H),fill="black")
		QuickList = [[],[],[]]
	if LCD4linux.LCDRotate1.value != "0":
		im=im.rotate(int(LCD4linux.LCDRotate1.value))
	TimePicture = time() - tt
	Brief1.put([writeLCD1,im,LCD4linux.BilderJPEG.value])
	if len(QuickList[0]) > 0:
		QuickIM[0] = im
	else:
		QuickIM[0] = None
#	TimeLCD1 = time() - tt - TimePicture
	if LCD4linux.LCDType2.value != "00":
		if Dunkel and "2" in Dunkel:
			MAX_W,MAX_H = im2.size
			draw2.rectangle((0, 0, MAX_W, MAX_H),fill="black")
		if LCD4linux.LCDRotate2.value != "0":
			im2=im2.rotate(int(LCD4linux.LCDRotate2.value))
		Brief2.put([writeLCD2,im2,LCD4linux.BilderJPEG.value])
		if len(QuickList[1]) > 0:
			QuickIM[1] = im2
		else:
			QuickIM[1] = None
	if LCD4linux.LCDType3.value != "00":
		if Dunkel and "3" in Dunkel:
			MAX_W,MAX_H = im3.size
			draw3.rectangle((0, 0, MAX_W, MAX_H),fill="black")
		if LCD4linux.LCDRotate3.value != "0":
			im3=im3.rotate(int(LCD4linux.LCDRotate3.value))
		Brief3.put([writeLCD3,im3,LCD4linux.BilderJPEG.value])
		if len(QuickList[2]) > 0:
			QuickIM[2] = im3
		else:
			QuickIM[2] = None
	Brief1.join()
	Brief2.join()
	Brief3.join()
	TimeEnd = time() - tt
	INFO = "RunTime: %.3f (Picture: %.3f / Write: %.3f)" % (TimeEnd,TimePicture,TimeEnd-TimePicture)
	L4log(INFO) #  (%.3f/%.3f) ,TimeLCD1,TimeLCD2
	INFO = PUSH+"   "+INFO 
	return

def main(session,**kwargs):
	session.open(LCDdisplayConfig)

def autostart(reason, **kwargs):
	global session
	global FONT
	global LCDon
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	global FritzList
	if "session" in kwargs:
		session = kwargs["session"]
		L4log("Start %s (%s), Libusb %s, %s..." % (Version,L4LVtest(Version),USBok,TMP))
		if os.path.isdir("%slcd4linux" % TMP) == False:
			try:
				os.mkdir("%slcd4linux" % TMP)
				L4log("create %s" % TMPL)
			except:
				L4log("Error: create %s" % TMPL)
		rmFiles(PIC + "*.*")
		if LCD4linux.WebIfInitDelay.value == False:
			InitWebIF()
		if os.path.isfile("/usr/lib/libpython2.5.so.1.0") == False:
			try:
				os.symlink("/usr/lib/libpython2.6.so.1.0","/usr/lib/libpython2.5.so.1.0")
				L4log("create Link")
			except:
				L4log("Error create Link")
		if LCD4linux.Font.value.endswith(".ttf") and os.path.isfile(LCD4linux.Font.value):
			FONT = LCD4linux.Font.value
		CheckFstab()
		TFTCheck(False)
		UpdateStatus(session)
		if os.path.isfile("/usr/bin/lcd4linux-start.sh"):
			RunShell("/usr/bin/lcd4linux-start.sh")
		try:
			if os.path.isfile("/etc/enigma2/lcd4fritz"):
				L4logE("read Fritzlist")
				for line in open("/etc/enigma2/lcd4fritz","r").readlines():
					exec("FritzList.append(%s)" % line)
				rmFile("/etc/enigma2/lcd4fritz")
		except:
				L4log("Error load Fritzlist")
		
	if reason == 1:
		L4log("Stop...")
		LCDon = False
		if len(FritzList)>0:
			L4logE("write Fritzlist")
			try:
				f=open("/etc/enigma2/lcd4fritz","w")
				for i in FritzList:
					f.write(str(i)+"\n")
				f.close()
			except:
				L4log("Error save Fritzlist")
		TFTCheck(False,SetMode="DREAM")
		Dunkel=writeHelligkeit(0,0,0,True)
		if SamsungDevice is not None and LCD4linux.LCDType1.value[0] == "2":
			try:
				MAX_W,MAX_H = getResolution(LCD4linux.LCDType1.value,LCD4linux.LCDRotate1.value)
				im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				output = cStringIO.StringIO()
				im.save(output, "JPEG")
				pic = output.getvalue()
				output.close()
				Photoframe.write_jpg2frame(SamsungDevice, pic)
				SamsungDevice = None
			except:
				pass
		if SamsungDevice2 is not None and LCD4linux.LCDType2.value[0] == "2":
			try:
				MAX_W,MAX_H = getResolution(LCD4linux.LCDType2.value,LCD4linux.LCDRotate2.value)
				im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				output = cStringIO.StringIO()
				im.save(output, "JPEG")
				pic = output.getvalue()
				output.close()
				Photoframe.write_jpg2frame(SamsungDevice2, pic)
				SamsungDevice2 = None
			except:
				pass
		if SamsungDevice3 is not None and LCD4linux.LCDType3.value[0] == "2":
			try:
				MAX_W,MAX_H = getResolution(LCD4linux.LCDType3.value,LCD4linux.LCDRotate3.value)
				im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				output = cStringIO.StringIO()
				im.save(output, "JPEG")
				pic = output.getvalue()
				output.close()
				Photoframe.write_jpg2frame(SamsungDevice3, pic)
				SamsungDevice3 = None
			except:
				pass

def getDistro():
	try:
		from enigma import getDistro as e2_getDistro
		return e2_getDistro()
	except:
		try:
			file = open('/etc/image-version', 'r')
			lines = file.readlines()
			file.close()
			for x in lines:
				splitted = x.split('=')
				if splitted[0] == "comment":
					result =  splitted[1].replace('\n','')
		except:
			result = None
		return result

def setup(menuid, **kwargs):
	if getDistro() in ("openvix", "openatv", "ventonsupport", "egami", "openhdf"):
		if menuid == "display" and SystemInfo["Display"]:
			return [("LCD4Linux", main, "lcd4linux", None)]
		elif menuid == "system" and not SystemInfo["Display"]:
			return [("LCD4Linux", main, "lcd4linux", None)]
		else:
			return []
	else:
		if menuid == "setup":
			return [("LCD4Linux", main, "lcd4linux", None)]
		else:
			return []

def Plugins(**kwargs):
	list = [
	PluginDescriptor(name="LCD4Linux", 
	description="LCD4Linux", 
	where = [PluginDescriptor.WHERE_SESSIONSTART, 
	PluginDescriptor.WHERE_AUTOSTART], 
	fnc = autostart)]
	list.append(PluginDescriptor(name="LCD4Linux", 
	description="LCD4Linux", 
	where = PluginDescriptor.WHERE_MENU,
	fnc = setup))
	return list

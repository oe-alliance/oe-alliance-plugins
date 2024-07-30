# -*- coding: utf-8 -*-#
#
#  LCD4linux - Pearl DPF LCD Display, Samsung SPF-Line, Grautec-TFT, WLAN-LCDs, internes LCD über Skin
#
# written by joergm6 @ IHAD
# (Meteo-Station @ compilator)
# (dynamic scaling for rectangle analog clockfaces and -hands and tested by Mr.Servo @ OpenA.TV + Turbohai @ IHAD & OpenA.TV)
# (moon distance and moon illumination-ratio by Mr.Servo @ OpenA.TV)
# (new MSN-Weather and Open-Meteo forecasts by Mr.Servo @ OpenA.TV)
# the Yahoo+ system is uniformly valid for the weather iconssets of all weather services (by Mr.Servo @ OpenA.TV)
#
#  This plugin is licensed under the The Non-Profit Open Software License version 3.0 (NPOSL-3.0)
#  http://opensource.org/licenses/NPOSL-3.0
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#  Advertise with this Plugin is not allowed.
#  For other uses, permission from the author is necessary.

# PYTHON IMPORTS
from __future__ import print_function, absolute_import, division
from base64 import b64encode
from calendar import Calendar, mdays, weekday, weekheader, month_name
from colorsys import rgb_to_hls, hls_to_rgb
from ctypes.util import find_library
from datetime import datetime, timedelta, date
from dateutil.parser import isoparse
from email import message_from_string
from email.header import decode_header
from fcntl import ioctl
from gc import enable, disable
from glob import glob, iglob
from icalendar import vDatetime, Calendar as iCalendar
from imaplib import IMAP4_SSL, IMAP4
from math import pi, floor, cos
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from locale import getlocale, setlocale, LC_ALL
from os import remove, statvfs, mkdir, rename, system, stat, symlink
from os.path import exists, islink, isdir, realpath, isfile, join, normpath, basename, getmtime, dirname, splitext
from PIL import Image, ImageFont, ImageDraw, ImageColor, ImageEnhance
from poplib import POP3_SSL, POP3
from random import shuffle, choice
from re import findall, sub
from requests import post, get, exceptions
from simplejson import loads
from six import BytesIO, ensure_binary, ensure_str, PY3
from six.moves.queue import Queue
from six.moves.socketserver import ThreadingMixIn
from six.moves.urllib.parse import quote, urlparse, urlunparse
from six.moves.urllib.request import urlopen, Request, urlretrieve
from six.moves.BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from socket import setdefaulttimeout
from struct import unpack
from textwrap import TextWrapper, wrap
from threading import Thread
from time import strftime, strptime, localtime, mktime, time, sleep, gmtime, timezone, altzone, daylight
from traceback import format_exc, print_stack
from twisted.internet.reactor import callInThread
from unicodedata import normalize
from usb import core
from usb.backend.libusb1 import get_backend
from xml.dom.minidom import parseString
from xml.etree.cElementTree import parse

# ENIGMA IMPORTS
from enigma import eActionMap, iServiceInformation, iFrontendInformation, eDVBResourceManager, eDVBVolumecontrol, eTimer
from enigma import eEPGCache, eServiceReference, eServiceCenter, getDesktop, getEnigmaVersionString, eEnv, ePicLoad, iPlayableService
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Button import Button
from Components.config import configfile, getConfigListEntry, ConfigPassword, ConfigYesNo, ConfigText, ConfigClock, ConfigSlider
from Components.config import config, Config, ConfigSelectionNumber, ConfigSelection, ConfigText
from Components.ConfigList import ConfigListScreen
from Components.Harddisk import harddiskmanager
from Components.Input import Input
from Components.Language import language
from Components.Lcd import LCD
from Components.MenuList import MenuList
from Components.NimManager import nimmanager
from Components.Network import iNetwork
from Components.Pixmap import Pixmap
from Components.Renderer.Picon import getPiconName
from Components.ServiceEventTracker import ServiceEventTracker
from Components.SystemInfo import SystemInfo
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens import Standby
from Screens.InfoBar import InfoBar
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Tools.BoundFunction import boundFunction
from Tools.Directories import SCOPE_PLUGINS, SCOPE_CONFIG, SCOPE_FONTS, SCOPE_LIBDIR, SCOPE_SYSETC, resolveFilename


try:
	from Components.SystemInfo import BoxInfo
	IMAGEDISTRO = BoxInfo.getItem("distro")
	MODEL = BoxInfo.getItem("machinebuild")
	ARCH = BoxInfo.getItem("architecture")
except:
	from boxbranding import getImageDistro, getBoxType, getImageArch
	IMAGEDISTRO = getImageDistro()
	MODEL = getBoxType()
	ARCH = getImageArch()


# PLUGIN IMPORTS
from . import Photoframe, dpf, _  # for localized messages
from .bluesound import BlueSound
from .module import L4Lelement
from .myFileList import FileList as myFileList
from .ping import quiet_ping
from .utils import getIPTVProvider, getAudio

# DEPENDING IMPORTS & GLOBALS & INITIALIZATION
import ssl
try:
	_create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
	pass
else:
	ssl._create_default_https_context = _create_unverified_https_context

if not PY3:
	from HTMLParser import HTMLParser
	_unescape = HTMLParser().unescape
else:
	from html import unescape as _unescape

try:
	from enigma import iDVBFrontend
	feCable = iDVBFrontend.feCable
	feSatellite = iDVBFrontend.feSatellite
	feTerrestrial = iDVBFrontend.feTerrestrial
	feok = True
except Exception:
	feCable = 2
	feSatellite = 1
	feTerrestrial = 4
	feok = False

CrashFile = "/tmp/L4Lcrash.txt"
pngutil = None
try:
	if exists("/dev/lcd2"):
		from fcntl import ioctl
		from pngutil import png_util
		pngutil = png_util.PNGUtil()
		pngutilconnect = pngutil.connect()
		try:
			with open("/dev/lcd2", 'w') as led_fd:
				ioctl(led_fd, 0x10, 0)
		except Exception:
			print("Error LCD Communication", format_exc())
			try:
				open(CrashFile, "w").write(format_exc())
			except Exception:
				pass
		PNGutilOK = True
	else:
		PNGutilOK = False
except Exception:
	PNGutilOK = False

USBok = False
if find_library("usb-0.1") is not None or find_library("usb-1.0") is not None:
	print("[LCD4linux] libusb found :-)", getEnigmaVersionString())
	USBok = True
elif ARCH in ("aarch64"):
	get_backend(find_library=lambda x: "/lib64/libusb-1.0.so.0")
	print("[LCD4linux] libusb found :-)", getEnigmaVersionString())
	USBok = True
Version = "V5.0-r22"
L4LElist = L4Lelement()
L4LdoThread = True
LCD4enigma2config = resolveFilename(SCOPE_CONFIG)  # /etc/enigma2/
LCD4enigma2plugin = resolveFilename(SCOPE_PLUGINS)  # /usr/lib/enigma2/python/Plugins/
LCD4lib = resolveFilename(SCOPE_LIBDIR)  # /usr/lib/
LCD4etc = resolveFilename(SCOPE_SYSETC)  # /etc/
LCD4bin = "%s/" % eEnv.resolve("${bindir}")  # /usr/bin/
LCD4python = "%s/" % eEnv.resolve("${PYTHONPATH}")  # /usr/lib/enigma2/python/
LCD4share = "%s/" % eEnv.resolve("${datarootdir}")  # /usr/share/
LCD4picon = join(LCD4share, "senigma2/picon/")  # /usr/share/enigma2/picon/
LCD4fonts = resolveFilename(SCOPE_FONTS)  # /usr/share/fonts/
LCD4config = join(LCD4enigma2config, "lcd4config")  # /etc/enigma2/lcd4config
LCD4plugin = join(LCD4enigma2plugin, "Extensions/LCD4linux/")  # /usr/lib/enigma2/python/Plugins/Extensions/LCD4linux/
LCD4data = join(LCD4plugin, "data/")  # /usr/lib/enigma2/python/Plugins/Extensions/LCD4linux/data/
LCD4default = join(LCD4data, "default.lcd")
LCD4text = "/tmp/lcd4linux.txt"
WetterPath = join(LCD4plugin, "wetter/")
MeteoPath = join(LCD4plugin, "meteo/")
FONTdefault = join(LCD4fonts, "nmsbd.ttf")
FONT = FONTdefault
ClockBack = join(LCD4data, "PAclock2.png")
Clock = join(LCD4data, "Clock")
RecPic = join(LCD4data, "rec.png")
TMP = "%s/" % realpath("%stmp" % LCD4plugin) if islink("%stmp" % LCD4plugin) == True else "/tmp/"
TMPL = join(TMP, "lcd4linux/")
xmlPIC = join(TMP, "l4ldisplay.png")
xmlPICtmp = join(TMP, "l4ldisplaytmp.png")
Fritz = join(TMPL, "fritz.txt")
FritzFrame = join(LCD4data, "fritzcallframe.png")
FritzRing = join(LCD4data, "fritzcallring.png")
FritzPic = join(LCD4data, "fritzpic.png")
PIC = join(TMPL, "dpf")
PICtmp = join(TMPL, "dpftmp")
PIC2 = join(TMPL, "dpf2")
PIC2tmp = join(TMPL, "dpf2tmp")
PIC3 = join(TMPL, "dpf3")
PIC3tmp = join(TMPL, "dpf3tmp")
PICcal = None
PICwetter = [None, None]
PICmeteo = join(TMPL, "dpfmeteo.png")
PICfritz = join(TMPL, "dpffritz.png")
HTTPpic = "%sdpfhttp%%d.jpg" % TMPL
HTTPpictmp = "%sdpfhttptmp%%d.jpg" % TMPL
TXTdemo = join(TMPL, "lcd4linux.demo")
MP3tmp = join(TMPL, "id3coverart.jpg")
GoogleCover = join(TMPL, "gcover.jpg")
WWWpic = "%swww%%s.jpg" % TMPL
LCDon = True
ConfigMode = False
ConfigStandby = False
ShellRunning = False
OSDon = 0
OSDtimer = -5
OSDdontshow = ["LCD4linux Settings", "Virtual Zap", "InfoBar", "Infobar", "SecondInfoBar", "FanControl2", "Mute", "LCD Text", "UnhandledKey", "QuickZap", "Volume", "PVRState"]
OSDdontskin = ["LCDdisplayFile", "VirtualZap", "InfoBar", "Infobar", "InfoBarSummary", "PictureInPicture", "SimpleSummary", "ScreenSummary", "TimeshiftState", "InfoScreen", "Standby", "EMCMediaCenter", "InfoBarMoviePlayerSummary", "PVRState", "ResolutionLabel", "WidgetBackground", "camodogFSScreen2", "camodogFSmini"]
wwwWetter = ["", ""]
WetterType = ["", ""]
WetterZoom = [0, 0]
OldTemp_c = -88
OldFeel = -88
OldHum = -88
OldWind = -88
OldMoonDist = -88
Oldillum = -88
CalType = ""
CalZoom = ""
CalColor = ""
wwwMeteo = ""
MeteoType = ""
MeteoZoom = ""
PopText = ["", ""]
ScreenActive = ["1", "", "", ""]
ScreenTime = 0
isVideoPlaying = 0
AktHelligkeit = [-1, -1, -1, -1, -1, -1]
AktNight = [0, 0, 0]
AktTFT = ""
PopMail = [[], [], [], [], [], ""]
PopMailUid = [["", "", ""], ["", "", ""], ["", "", ""], ["", "", ""], ["", "", ""]]
Bilder = ["", "", ""]
BilderIndex = [0, 0, 0]
BilderTime = 0
FritzTime = 0
FritzList = []
xmlList = []
ThreadRunning = 0
DeviceRemove = []
QuickList = [[], [], []]
SaveEventList = ["", "", ""]
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
BriefLCD = Queue()
Briefkasten = Queue()
BriefRes = Queue()
Brief1 = Queue()
Brief2 = Queue()
Brief3 = Queue()
MJPEG = ["0123", Queue(), Queue(), Queue()]
MJPEGserver = [None, None, None, None]
MJPEGreader = [0, 0, 0, 0]
MJPEGrun = [0, 0, 0, 0]
CPUtotal = 0
CPUidle = 0
L4LSun = (7, 0)
L4LMoon = (19, 0)
INFO = ""
WeekDays = [_("Mon"), _("Tue"), _("Wed"), _("Thur"), _("Fri"), _("Sat"), _("Sun")]
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
ScreenSelect = [("0", _("off")), ("1", _("Screen 1")), ("2", _("Screen 2")), ("3", _("Screen 3")), ("12", _("Screen 1+2")), ("13", _("Screen 1+3")), ("23", _("Screen 2+3")), ("123", _("Screen 1+2+3")), ("4", _("Screen 4")), ("14", _("Screen 1+4")), ("24", _("Screen 2+4")), ("34", _("Screen 3+4")), ("124", _("Screen 1+2+4")), ("134", _("Screen 1+3+4")), ("234", _("Screen 2+3+4")), ("1234", _("Screen 1+2+3+4")), ("5", _("Screen 5")), ("6", _("Screen 6")), ("7", _("Screen 7")), ("8", _("Screen 8")), ("9", _("Screen 9")), ("12345", _("Screen 1-5")), ("123456", _("Screen 1-6")), ("1234567", _("Screen 1-7")), ("12345678", _("Screen 1-8")), ("123456789", _("Screen 1-9")), ("5678", _("Screen 5-8")), ("56789", _("Screen 5-9")), ("13579", _("Screen 1+3+5+7+9")), ("2468", _("Screen 2+4+6+8"))]
ScreenUse = [("1", _("Screen 1")), ("2", _("Screen 1-2")), ("3", _("Screen 1-3")), ("4", _("Screen 1-4")), ("5", _("Screen 1-5")), ("6", _("Screen 1-6")), ("7", _("Screen 1-7")), ("8", _("Screen 1-8")), ("9", _("Screen 1-9"))]
ScreenSet = [("1", _("Screen 1")), ("2", _("Screen 2")), ("3", _("Screen 3")), ("4", _("Screen 4")), ("5", _("Screen 5")), ("6", _("Screen 6")), ("7", _("Screen 7")), ("8", _("Screen 8")), ("9", _("Screen 9"))]
OnOffSelect = [("0", _("off")), ("1", _("on"))]
TimeSelect = [("1", _("5s")), ("2", _("10s")), ("3", _("15s")), ("4", _("20s")), ("6", _("30s")), ("8", _("40s")), ("10", _("50s")), ("12", _("1min")), ("24", _("2min")), ("36", _("3min")), ("48", _("4min")), ("60", _("5min")), ("120", _("10min")), ("240", _("20min")), ("360", _("30min")), ("720", _("60min")), ("1440", _("2h")), ("2160", _("3h")), ("3600", _("5h"))]
LCDSelect = [("1", _("LCD 1")), ("2", _("LCD 2")), ("12", _("LCD 1+2")), ("3", _("LCD 3")), ("13", _("LCD 1+3")), ("23", _("LCD 2+3")), ("123", _("LCD 1+2+3"))]
LCDSwitchSelect = [("0", _("LCD 1-3")), ("1", _("LCD 1")), ("2", _("LCD 2")), ("3", _("LCD 3"))]
LCDType = [("11", _("Pearl (or compatible LCD) 320x240")), ("12", _("Pearl (or compatible LCD) 240x320")), ("121", _("Corby@Pearl 128x128")), ("122", _("Pearl (or compatible LCD) 480x320")), ("123", _("Pearl (or compatible LCD) 800x480")),
 ("210", _("Samsung SPF-72H 800x480")), ("23", _("Samsung SPF-75H/76H 800x480")), ("24", _("Samsung SPF-87H 800x480")), ("25", _("Samsung SPF-87H old 800x480")), ("26", _("Samsung SPF-83H 800x600")),
 ("29", _("Samsung SPF-85H/86H 800x600")), ("212", _("Samsung SPF-85P/86P 800x600")), ("28", _("Samsung SPF-105P 1024x600")), ("27", _("Samsung SPF-107H 1024x600")), ("213", _("Samsung SPF-107H old 1024x600")),
 ("211", _("Samsung SPF-700T 800x600")), ("215", _("Samsung SPF-800P 800x480")), ("214", _("Samsung SPF-1000P 1024x600")), ("430", _("Internal TFT-LCD 400x240")), ("50", _("Internal Box-Skin-LCD")),
 ("31", _("only Picture 320x240")), ("33", _("only Picture 800x480")), ("36", _("only Picture 800x600")), ("37", _("only Picture 1024x600")), ("320", _("only Picture Custom Size")), ("420", _("only Picture Custom Size 2"))]
if PNGutilOK:
	LCDType.insert(14, ("930", _("Internal Vu+ Duo2 LCD 400x240")))
xmlLCDType = [("96x64", _("96x64")), ("128x32", _("128x32")), ("128x64", _("128x64")), ("132x64", _("132x64")), ("220x176", _("220x176")), ("255x64", _("255x64")), ("400x240", _("400x240")), ("480x320", _("480x320")), ("700x390", _("720x405")), ("800x480", _("800x480"))]
WetterType = [("12", _("2 Days 1 Line")), ("22", _("2 Days 2 Line")), ("1", _("4 Days 1 Line")), ("2", _("4 Days 2 Lines")), ("11", _("5 Days 1 Line")), ("21", _("5 Days 2 Lines")), ("3", _("Current")), ("4", _("Current Temperature (+C)")), ("41", _("Current Temperature (-C)")), ("5", _("4 Days Vertical View")), ("51", _("5 Days Vertical View"))]
MeteoType = [("1", _("Current")), ("2", _("Current Temperature"))]
NetatmoType = [("THCPN", _("All")), ("T", _("Temperature")), ("TH", _("Temperature+Humidity")), ("TC", _("Temperature+Co2")), ("TCP", _("Temperature+Co2+Pressure"))]
NetatmoSelect = [("0", _("userdefined")), ("1", _("Module 1")), ("2", _("Module 2")), ("3", _("Module 3")), ("12", _("Module 1+2")), ("13", _("Module 1+3")), ("23", _("Module 2+3")), ("123", _("Module 1+2+3")), ("4", _("Module 4")), ("14", _("Module 1+4")), ("24", _("Module 2+4")), ("34", _("Module 3+4")), ("124", _("Module 1+2+4")), ("134", _("Module 1+3+4")), ("234", _("Module 2+3+4")), ("1234", _("Module 1-4")), ("5", _("Module 5")), ("12345", _("Module 1-5")), ("6", _("Module 6")), ("56", _("Module 5-6")), ("456", _("Module 4-6")), ("3456", _("Module 3-6")), ("23456", _("Module 2-6")), ("123456", _("Module 1-6"))]
CO2Type = [("0", _("Bar")), ("09", _("Bar+Value")), ("1", _("Knob")), ("19", _("Knob+Value"))]
ClockType = [("12", _("Time")), ("112", _("Date+Time")), ("1123", _("Date+Time+Weekday")), ("11", _("Date")), ("123", _("Time+Weekday")), ("13", _("Weekday")), ("4", _("Flaps Design Date")), ("41", _("Flaps Design Weekday")), ("51", _("Analog")), ("52", _("Analog+Date")), ("521", _("Analog+Date+Weekday")), ("521+", _("Analog+Date+Weekday 2"))]
AlignType = [("0", _("left")), ("1", _("center")), ("2", _("right")), ("0200", _("2%")), ("0300", _("3%")), ("0500", _("5%")), ("1000", _("10%")), ("1500", _("15%")), ("2000", _("20%")), ("2500", _("25%")), ("3000", _("30%")), ("3500", _("35%")), ("4000", _("40%")), ("4500", _("45%")), ("5000", _("50%")), ("5500", _("55%")), ("6000", _("60%")), ("6500", _("65%")), ("7000", _("70%")), ("7500", _("75%")), ("8000", _("80%")), ("8500", _("85%")), ("9000", _("90%")), ("9500", _("95%")), ("9700", _("97%")), ("9800", _("98%"))]
DescriptionType = [("10", _("Short")), ("12", _("Short (Extended)")), ("01", _("Extended")), ("21", _("Extended (Short)")), ("11", _("Short+Extended"))]
CalType = [("9", _("no Calendar")), ("0", _("Month")), ("0A", _("Month+Header")), ("1", _("Week")), ("1A", _("Week+Header"))]
CalTypeE = [("0", _("no Dates")), ("D2", _("Dates compact 2 Lines")), ("D3", _("Dates compact 3 Lines")), ("C1", _("Dates 1 Line")), ("C3", _("Dates 3 Lines")), ("C5", _("Dates 5 Lines")), ("C9", _("Dates 9 Lines"))]
CalLayout = [("0", _("Frame")), ("1", _("Underline")), ("2", _("Underline 2"))]
CalListType = [("D", _("Dates compact")), ("D-", _("Dates compact no Icon")), ("C", _("Dates")), ("C-", _("Dates no Icon"))]
FritzType = [("L", _("with Icon")), ("L-", _("no Icon")), ("TL", _("with Icon & Targetnumber")), ("TL-", _("no Icon, with Targetnumber"))]
InfoSensor = [("0", _("no")), ("R", _("rpm/2")), ("r", _("rpm")), ("T", _("C")), ("RT", _("C + rpm/2")), ("rT", _("C + rpm"))]
InfoTuner = [("0", _("no")), ("A", _("db")), ("B", _("%")), ("AB", _("db + %")), ("ABC", _("db + % + BER")), ("AC", _("db + BER")), ("BC", _("% + BER"))]
InfoCPU = [("0", _("no")), ("P", _("%")), ("L0", _("Load@1min")), ("L1", _("Load@5min")), ("PL0", _("% + Load@1min")), ("PL1", _("% + Load@5min"))]
HddType = [("0", _("show run+sleep")), ("1", _("show run"))]
MailType = [("A1", _("Always All")), ("A2", _("Always New")), ("B2", _("Only New"))]
MoonInfoSelect = [("000", _("off")), ("001", _("Distance only")), ("010", _("Illumination only")), ("100", _("Moonphase only")), ("011", _("Distance+Illumination")), ("101", _("Distance+Moonphase")), ("110", _("Illumination+Moonphase")), ("111", _("All Informations"))]
ProzentType = [("30", _("30%")), ("35", _("35%")), ("40", _("40%")), ("45", _("45%")), ("50", _("50%")), ("55", _("55%")), ("60", _("60%")), ("65", _("65%")), ("70", _("70%")), ("75", _("75%")), ("80", _("80%")), ("85", _("85%")), ("90", _("90%")), ("95", _("95%")), ("97", _("97%")), ("98", _("98%")), ("100", _("100%"))]
WarningType = [("0", _("off")), ("2", _("2%")), ("3", _("3%")), ("5", _("5%")), ("10", _("10%")), ("15", _("15%")), ("20", _("20%")), ("25", _("25%"))]
MailKonto = [("1", _("1")), ("2", _("1-2")), ("3", _("1-3")), ("4", _("1-4")), ("5", _("1-5"))]
MailConnect = [("0", _("Pop3-SSL")), ("1", _("Pop3")), ("2", _("IMAP-SSL")), ("3", _("IMAP"))]
RBoxType = [("PCT", _("Picon+Channel+Title")), ("PC", _("Picon+Channel")), ("P", _("Picon")), ("CT", _("Channel+Title")), ("C", _("Channel"))]
OffFarbe = [("0", _("same color"))] + Farbe
Split = [("false", _("no")), ("true", _("yes")), ("true25", _("yes +25%"))]
DirType = [("0", _("horizontally")), ("2", _("vertically"))]
FontType = [("0", _("Global")), ("1", _("1")), ("2", _("2")), ("3", _("3")), ("4", _("4")), ("5", _("5"))]
DayType = [("0", _("all")), ("1", _("1")), ("2", _("2")), ("3", _("3")), ("7", _("7")), ("14", _("14")), ("30", _("30"))]
RecordType = [("1", _("Corner")), ("1t", _("Corner+Timeshift")), ("2", _("Picon")), ("2t", _("Picon+Timeshift"))]
ProgressType = [("1", _("only Progress Bar")),
("2", _("with Remaining Minutes")), ("21", _("with Remaining Minutes (Size 1.5)")), ("22", _("with Remaining Minutes (Size 2)")),
("3", _("with Percent")), ("31", _("with Percent (Size 1.5)")), ("32", _("with Percent (Size 2)")),
("4", _("with Remaining Minutes (above)")), ("41", _("with Remaining Minutes (above/Size 1.5)")), ("42", _("with Remaining Minutes (above/Size 2)")),
("5", _("with Percent (above)")), ("51", _("with Percent (above/Size 1.5)")), ("52", _("with Percent (above/Size 2)")),
("6", _("with Remaining Minutes (below)")), ("61", _("with Remaining Minutes (below/Size 1.5)")), ("62", _("with Remaining Minutes (below/Size 2)")),
("7", _("with Percent (below)")), ("71", _("with Percent (below/Size 1.5)")), ("72", _("with Percent (below/Size 2)")),
("8", _("with Current 00:00")), ("81", _("with Current 00:00 (Size 1.5)")), ("82", _("with Current 00:00 (Size 2)")),
("9", _("with Current 00:00 (above)")), ("91", _("with Current 00:00 (above/Size 1.5)")), ("92", _("with Current 00:00 (above/Size 2)")),
("A", _("with Current 00:00 (below)")), ("A1", _("with Current 00:00 (below/Size 1.5)")), ("A2", _("with Current 00:00 (below/Size 2)")),
("B", _("with Percent Minutes / Total (above)")), ("B1", _("with Percent Minutes / Total (above/Size 1.5)")), ("B2", _("with Percent Minutes / Total (above/Size 2)")),
("C", _("with absolute Endtime")), ("C1", _("with absolute Endtime (Size 1.5)")), ("C2", _("with absolute Endtime (Size 2)")),
("D", _("with Minutes Total / Endtime (above)")), ("D1", _("with Minutes Total / Endtime (above/Size 1.5)")), ("D2", _("with Minutes Total / Endtime (above/Size 2)")),
]
now = localtime()
begin = mktime((now.tm_year, now.tm_mon, now.tm_mday, 6, 00, 0, now.tm_wday, now.tm_yday, now.tm_isdst))
# Find all directories "clock*" with result in a list, extract last two chars, extract integers, remove dupes, sort integers and convert it back to a list
FoundClockDir = list(map(str, sorted(set([int(i) for i in findall(r'\d+', str(list(map(lambda found: str(found)[-2:], glob("%s*" % Clock)))))]))))
LCD4linux = Config()
LCD4linux.Enable = ConfigYesNo(default=True)
LCD4linux.L4LVersion = ConfigText(default="0.0r0", fixed_size=False)
LCD4linux.FastMode = ConfigSelection(choices=[("5", _("Normal (5s)")), ("2", _("Fastmode (2s)"))], default="5")
LCD4linux.SwitchToFB2 = ConfigYesNo(default=True)
LCD4linux.ScreenActive = ConfigSelection(choices=ScreenSet, default="1")
LCD4linux.ScreenSwitch = ConfigSelection(choices=ScreenSet, default="2")
LCD4linux.ScreenSwitchLCD = ConfigSelection(choices=LCDSwitchSelect, default="0")
LCD4linux.ScreenMax = ConfigSelection(choices=ScreenUse, default="1")
LCD4linux.ScreenTime = ConfigSelection(choices=[("0", _("off"))] + TimeSelect, default="0")
LCD4linux.ScreenTime2 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.ScreenTime3 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.ScreenTime4 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.ScreenTime5 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.ScreenTime6 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.ScreenTime7 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.ScreenTime8 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.ScreenTime9 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.BilderTime = ConfigSelection(choices=[("0", _("off"))] + TimeSelect, default="0")
LCD4linux.BilderSort = ConfigSelection(choices=[("0", _("off")), ("1", _("alphabetic")), ("2", _("random"))], default="1")
LCD4linux.BilderQuality = ConfigSelection(choices=[("0", _("low/fast (all)")), ("1", _("low/fast (Picture only)")), ("2", _("better/slow"))], default="1")
LCD4linux.BilderRecursiv = ConfigYesNo(default=False)
LCD4linux.BilderQuick = ConfigSelection(choices=[("500", _("0.5")), ("1000", _("1")), ("2000", _("2")), ("3000", _("3")), ("5000", _("5")), ("10000", _("10")), ("20000", _("20")), ("30000", _("30"))], default="10000")
LCD4linux.BilderJPEG = ConfigSelectionNumber(20, 100, 5, default=75)
LCD4linux.BilderJPEGQuick = ConfigSelectionNumber(20, 100, 5, default=60)
LCD4linux.BilderTyp = ConfigSelection(choices=[("png", _("PNG")), ("jpg", _("JPG"))], default="png")
LCD4linux.BilderBackground = ConfigSelection(choices=[("0", _("no cache + no adjustment")), ("1", _("cache + adjustment (high quality, slow)")), ("2", _("cache + adjustment (low quality, fast)"))], default="2")
LCD4linux.Helligkeit = ConfigSelectionNumber(0, 10, 1, default=5)
LCD4linux.Helligkeit2 = ConfigSelectionNumber(0, 10, 1, default=5)
LCD4linux.Helligkeit3 = ConfigSelectionNumber(0, 10, 1, default=5)
LCD4linux.Night = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.Night2 = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.Night3 = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.AutoOFF = ConfigSelection(choices=[("0", _("off"))] + TimeSelect, default="0")
LCD4linux.LCDoff = ConfigClock(default=int(begin))  # ((5 * 60 + 0) * 60)
LCD4linux.LCDon = ConfigClock(default=int(begin))
LCD4linux.LCDWEoff = ConfigClock(default=int(begin))  # ((5 * 60 + 0) * 60)
LCD4linux.LCDWEon = ConfigClock(default=int(begin))
LCD4linux.LCDshutdown = ConfigYesNo(default=True)
LCD4linux.Delay = ConfigSlider(default=400, increment=50, limits=(50, 2000))
LCD4linux.ElementThreads = ConfigSelectionNumber(1, 2, 1, default=2)
LCD4linux.DevForceRead = ConfigYesNo(default=True)
LCD4linux.DevBackColor = ConfigSelection(choices=Farbe, default="yellow")
LCD4linux.DevBarColor = ConfigSelection(choices=Farbe, default="lime")
LCD4linux.DevFullColor = ConfigSelection(choices=Farbe, default="red")
LCD4linux.DVBTCorrection = ConfigSelection(choices=[("0", _("no")), ("reverse", _("Plug Tuner")), ("usb", _("USB Tuner"))], default="0")
LCD4linux.ServiceSearch = ConfigSelection(choices=[("0", _("Now/Next")), ("1", _("EPG"))], default="0")
LCD4linux.ShowNoMsg = ConfigYesNo(default=True)
LCD4linux.SavePicture = ConfigSelection(choices=[("0", _("no"))] + LCDSelect, default="123")
LCD4linux.NETworkCheckEnable = ConfigYesNo(default=False)
LCD4linux.MJPEGenable1 = ConfigYesNo(default=False)
LCD4linux.MJPEGenable2 = ConfigYesNo(default=False)
LCD4linux.MJPEGenable3 = ConfigYesNo(default=False)
LCD4linux.MJPEGport1 = ConfigText(default="8411", fixed_size=False)
LCD4linux.MJPEGport2 = ConfigText(default="8412", fixed_size=False)
LCD4linux.MJPEGport3 = ConfigText(default="8413", fixed_size=False)
LCD4linux.MJPEGvirtbri1 = ConfigYesNo(default=True)
LCD4linux.MJPEGvirtbri2 = ConfigYesNo(default=True)
LCD4linux.MJPEGvirtbri3 = ConfigYesNo(default=True)
LCD4linux.MJPEGMode = ConfigSelection(choices=[("001", "001"), ("011", "011"), ("110", "110"), ("101", "101"), ("111", "111"), ("020", "020"), ("021", "021")], default="101")
LCD4linux.MJPEGHeader = ConfigSelection(choices=[("0", _("normal")), ("1", _("reduced"))], default="1")
LCD4linux.MJPEGCycle = ConfigSelectionNumber(1, 10, 1, default=2)
LCD4linux.MJPEGRestart = ConfigYesNo(default=True)
LCD4linux.Streaming = ConfigSelection(choices=[("0", _("Media")), ("1", _("On"))], default="0")
LCD4linux.WebIfRefresh = ConfigSelectionNumber(1, 60, 1, default=3)
LCD4linux.WebIfType = ConfigSelection(choices=[("0", _("Javascript")), ("01", _("Javascript no Refresh")), ("1", _("Reload"))], default="0")
LCD4linux.WebIfInitDelay = ConfigYesNo(default=False)
LCD4linux.WebIfAllow = ConfigText(default="127. 192.168. 172. 10.", fixed_size=False)
LCD4linux.WebIfDeny = ConfigText(default="", fixed_size=False)
LCD4linux.WebIfDesign = ConfigSelection(choices=[("1", _("1 - normal")), ("2", _("2 - side by side"))], default="2")
LCD4linux.WetterApi = ConfigSelection(choices=[("MSN", _("MSN")), ("OPENMETEO", _("Open-Meteo")), ("OPENWEATHER", _("OpenWeatherMap")), ("WEATHERUNLOCKED", _("WeatherUnlocked"))], default="MSN")
LCD4linux.WetterApiKeyOpenWeatherMap = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.WetterApiKeyWeatherUnlocked = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.WetterCity = ConfigText(default="Berlin", fixed_size=False)
LCD4linux.WetterCoords = ConfigText(default="0,0", fixed_size=False)
LCD4linux.Wetter2City = ConfigText(default="Berlin", fixed_size=False)
LCD4linux.Wetter2Coords = ConfigText(default="0,0", fixed_size=False)
LCD4linux.WetterPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.WetterLowColor = ConfigSelection(choices=Farbe, default="aquamarine")
LCD4linux.WetterHighColor = ConfigSelection(choices=Farbe, default="violet")
LCD4linux.WetterTransparenz = ConfigSelection(choices=[("false", _("no")), ("crop", _("alternative Copy-Mode/DM800hd (24bit)")), ("true", _("yes"))], default="false")
LCD4linux.WetterIconZoom = ConfigSelectionNumber(20, 70, 1, default=40)
LCD4linux.WetterRain = ConfigSelection(choices=[("false", _("no")), ("true", _("yes")), ("true2", _("yes + %"))], default="true")
LCD4linux.WetterRainZoom = ConfigSlider(default=100, increment=1, limits=(90, 200))
LCD4linux.WetterRainColor = ConfigSelection(choices=Farbe, default="silver")
LCD4linux.WetterRainColor2use = ConfigSelectionNumber(10, 100, 10, default=80)
LCD4linux.WetterRainColor2 = ConfigSelection(choices=Farbe, default="cyan")
LCD4linux.WetterHumColor = ConfigSelection(choices=Farbe, default="cyan")
LCD4linux.WetterLine = ConfigSelection(choices=[("false", _("no")), ("true", _("yes, short")), ("trueLong", _("yes, long"))], default="trueLong")
LCD4linux.WetterTrendArrows = ConfigYesNo(default=True)
LCD4linux.WetterExtra = ConfigYesNo(default=True)
LCD4linux.WetterExtraZoom = ConfigSlider(default=100, increment=1, limits=(90, 300))
LCD4linux.WetterExtraFeel = ConfigSelectionNumber(0, 5, 1, default=3)
LCD4linux.WetterExtraColorCity = ConfigSelection(choices=Farbe, default="silver")
LCD4linux.WetterExtraColorFeel = ConfigSelection(choices=Farbe, default="silver")
LCD4linux.WetterWind = ConfigSelection(choices=[("0", _("km/h")), ("1", _("m/s"))], default="0")
LCD4linux.WetterWindLines = ConfigSelection(choices=[("off", _("off")), ("1", _("1")), ("2", _("2"))], default="1")
LCD4linux.MeteoURL = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.MoonPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.BlueIP = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.BlueServerIP = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.BluePingTimeout = ConfigSlider(default=50, increment=5, limits=(0, 2000))
LCD4linux.BlueTimer = ConfigSelection(choices=[("1", _("1")), ("2", _("2")), ("3", _("3")), ("5", _("5")), ("10", _("10")), ("20", _("20")), ("30", _("30")), ("60", _("60"))], default="10")
LCD4linux.BlueCheckTimer = ConfigSelection(choices=[("2", _("10s")), ("3", _("15s")), ("4", _("20s")), ("6", _("30s")), ("12", _("1min")), ("24", _("2min"))], default="12")
LCD4linux.SonosIP = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.SonosON = ConfigYesNo(default=False)
LCD4linux.SonosPingTimeout = ConfigSlider(default=50, increment=5, limits=(0, 2000))
LCD4linux.SonosTimer = ConfigSelection(choices=[("1", _("1")), ("2", _("2")), ("3", _("3")), ("5", _("5")), ("10", _("10")), ("20", _("20")), ("30", _("30")), ("60", _("60"))], default="10")
LCD4linux.SonosCheckTimer = ConfigSelection(choices=[("2", _("10s")), ("3", _("15s")), ("4", _("20s")), ("6", _("30s")), ("12", _("1min")), ("24", _("2min"))], default="12")
LCD4linux.YMCastIP = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.YMCastServerIP = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.YMCastPingTimeout = ConfigSlider(default=50, increment=5, limits=(0, 2000))
LCD4linux.YMCastTimer = ConfigSelection(choices=[("1", _("1")), ("2", _("2")), ("3", _("3")), ("5", _("5")), ("10", _("10")), ("20", _("20")), ("30", _("30")), ("60", _("60"))], default="10")
LCD4linux.YMCastCheckTimer = ConfigSelection(choices=[("2", _("10s")), ("3", _("15s")), ("4", _("20s")), ("6", _("30s")), ("12", _("1min")), ("24", _("2min"))], default="12")
LCD4linux.YMCastCover = ConfigSelection(choices=[("0", _("MusicCast")), ("1", _("Coversearch"))], default="0")
if PNGutilOK:
	LCD4linux.LCDType1 = ConfigSelection(choices=LCDType, default="930")
else:
	LCD4linux.LCDType1 = ConfigSelection(choices=LCDType, default="11")
LCD4linux.LCDType2 = ConfigSelection(choices=[("00", _("off"))] + LCDType, default="00")
LCD4linux.LCDType3 = ConfigSelection(choices=[("00", _("off"))] + LCDType, default="00")
LCD4linux.LCDRotate1 = ConfigSelection(choices=[("0", _("0")), ("90", _("90")), ("180", _("180")), ("270", _("270"))], default="0")
LCD4linux.LCDRotate2 = ConfigSelection(choices=[("0", _("0")), ("90", _("90")), ("180", _("180")), ("270", _("270"))], default="0")
LCD4linux.LCDRotate3 = ConfigSelection(choices=[("0", _("0")), ("90", _("90")), ("180", _("180")), ("270", _("270"))], default="0")
LCD4linux.LCDBild1 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.LCDBild2 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.LCDBild3 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.LCDColor1 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.LCDColor2 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.LCDColor3 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.LCDRefresh1 = ConfigSelection(choices=[("0", _("always")), ("1", _("1 / min"))], default="0")
LCD4linux.LCDRefresh2 = ConfigSelection(choices=[("0", _("always")), ("1", _("1 / min"))], default="0")
LCD4linux.LCDRefresh3 = ConfigSelection(choices=[("0", _("always")), ("1", _("1 / min"))], default="0")
LCD4linux.LCDTFT = ConfigSelection(choices=[("ABC", _("On+Media+Standby")), ("A", _("On")), ("B", _("Media")), ("C", _("Standby"))], default="ABC")
LCD4linux.xmlLCDType = ConfigSelection(choices=xmlLCDType, default="132x64")
LCD4linux.xmlLCDColor = ConfigSelection(choices=[("8", _("8bit - grayscale/color")), ("32", _("32bit - color"))], default="8")
LCD4linux.xmlType01 = ConfigYesNo(default=False)
LCD4linux.xmlType02 = ConfigYesNo(default=False)
LCD4linux.xmlType03 = ConfigYesNo(default=False)
LCD4linux.xmlOffset = ConfigSelectionNumber(0, 20, 1, default=0)
LCD4linux.SizeW = ConfigSlider(default=800, increment=1, limits=(100, 2000))
LCD4linux.SizeH = ConfigSlider(default=600, increment=1, limits=(100, 1100))
LCD4linux.SizeW2 = ConfigSlider(default=800, increment=1, limits=(100, 2000))
LCD4linux.SizeH2 = ConfigSlider(default=600, increment=1, limits=(100, 1100))
LCD4linux.KeySwitch = ConfigYesNo(default=True)
LCD4linux.KeyScreen = ConfigSelection(choices=[("999", _("off")), ("163", _("2 x FastForwardKey")), ("208", _("2 x FastForwardKey Type 2")), ("1631", _("Long FastForwardKey")), ("2081", _("Long FastForwardKey Type 2")), ("358", _("2 x InfoKey")), ("3581", _("Long InfoKey")), ("113", _("2 x Mute"))], default="163")
LCD4linux.KeyOff = ConfigSelection(choices=[("999", _("off")), ("165", _("2 x FastBackwardKey")), ("168", _("2 x FastBackwardKey Type 2")), ("1651", _("Long FastBackwardKey")), ("1681", _("Long FastBackwardKey Type 2")), ("358", _("2 x InfoKey")), ("3581", _("Long InfoKey")), ("113", _("2 x Mute"))], default="165")
LCD4linux.Mail1Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail1Connect = ConfigSelection(choices=MailConnect, default="0")
LCD4linux.Mail1User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail1Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail2Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail2Connect = ConfigSelection(choices=MailConnect, default="0")
LCD4linux.Mail2User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail2Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail3Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail3Connect = ConfigSelection(choices=MailConnect, default="0")
LCD4linux.Mail3User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail3Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail4Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail4Connect = ConfigSelection(choices=MailConnect, default="0")
LCD4linux.Mail4User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail4Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail5Pop = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail5Connect = ConfigSelection(choices=MailConnect, default="0")
LCD4linux.Mail5User = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Mail5Pass = ConfigPassword(default="", fixed_size=False, visible_width=50)
LCD4linux.MailTime = ConfigSelection(choices=[("01", _("60min")), ("01,31", _("30min")), ("01,21,41", _("20min")), ("01,16,31,46", _("15min")), ("01,11,21,31,41,51", _("10min")), ("01,06,11,16,21,26,31,36,41,46,51,56", _("5min"))], default="01")
LCD4linux.MailIMAPDays = ConfigSelection(choices=DayType, default="7")
LCD4linux.MailShow0 = ConfigYesNo(default=False)
LCD4linux.MailShowDate = ConfigYesNo(default=True)
LCD4linux.MailHideMail = ConfigYesNo(default=False)
LCD4linux.Recording = ConfigSelection(choices=ScreenSelect, default="123456789")
LCD4linux.RecordingLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.RecordingType = ConfigSelection(choices=RecordType, default="1t")
LCD4linux.RecordingSize = ConfigSlider(default=25, increment=1, limits=(10, 200))
LCD4linux.RecordingPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.RecordingAlign = ConfigSelection(choices=AlignType, default="2")
LCD4linux.RecordingSplit = ConfigYesNo(default=False)
LCD4linux.RecordingPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Crash = ConfigYesNo(default=True)
LCD4linux.ConfigPath = ConfigText(default="/tmp/", fixed_size=False, visible_width=50)
LCD4linux.ConfigWriteAll = ConfigYesNo(default=True)
LCD4linux.Events = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.EventsLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.EventsSize = ConfigSlider(default=32, increment=1, limits=(8, 150))
LCD4linux.EventsPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.EventsAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.EventsSplit = ConfigYesNo(default=False)
LCD4linux.EventsType = ConfigSelection(choices=DirType, default="0")
LCD4linux.FritzPath = ConfigText(default="/tmp/", fixed_size=False, visible_width=50)
LCD4linux.FritzFrame = ConfigText(default="", fixed_size=False, visible_width=40)
LCD4linux.FritzLines = ConfigSelectionNumber(0, 20, 1, default=2)
LCD4linux.FritzLineType = ConfigSelectionNumber(2, 3, 1, default=2)
LCD4linux.FritzPictures = ConfigSelectionNumber(0, 20, 1, default=0)
LCD4linux.FritzPictureSearch = ConfigSelection(choices=[("0", _("no")), ("1", _("yes")), ("12", _("yes, extended"))], default="1")
LCD4linux.FritzPictureType = ConfigSelection(choices=DirType, default="0")
LCD4linux.FritzPictureTransparenz = ConfigSelection(choices=[("0", _("no")), ("2", _("yes"))], default="0")
LCD4linux.FritzRemove = ConfigSelectionNumber(1, 48, 1, default=12)
LCD4linux.FritzTime = ConfigSelection(choices=TimeSelect, default="3")
LCD4linux.FritzPopupLCD = ConfigSelection(choices=[("0", _("no"))] + LCDSelect, default="1")
LCD4linux.FritzPopupColor = ConfigSelection(choices=Farbe, default="yellow")
LCD4linux.CalPath = ConfigText(default="/tmp/", fixed_size=False, visible_width=40)
LCD4linux.CalPathColor = ConfigSelection(choices=Farbe, default="green")
LCD4linux.CalHttp = ConfigText(default="http...", fixed_size=False, visible_width=50)
LCD4linux.CalHttpColor = ConfigSelection(choices=Farbe, default="lime")
LCD4linux.CalHttp2 = ConfigText(default="http...", fixed_size=False, visible_width=50)
LCD4linux.CalHttp2Color = ConfigSelection(choices=Farbe, default="greenyellow")
LCD4linux.CalHttp3 = ConfigText(default="http...", fixed_size=False, visible_width=50)
LCD4linux.CalHttp3Color = ConfigSelection(choices=Farbe, default="yellow")
LCD4linux.CalPlanerFS = ConfigYesNo(default=False)
LCD4linux.CalPlanerFSColor = ConfigSelection(choices=Farbe, default="orange")
LCD4linux.CalSaColor = ConfigSelection(choices=Farbe, default="red")
LCD4linux.CalSuColor = ConfigSelection(choices=Farbe, default="red")
LCD4linux.CalLine = ConfigSelectionNumber(1, 2, 1, default=1)
LCD4linux.CalDays = ConfigSelection(choices=[("0", "0"), ("3", "3"), ("7", "7"), ("14", "14"), ("21", "21"), ("31", "31")], default="7")
LCD4linux.CalTime = ConfigSelection(choices=[("03", _("60min")), ("03,33", _("30min")), ("03,23,43", _("20min")), ("03,18,33,48", _("15min"))], default="03")
LCD4linux.CalTransparenz = ConfigSelection(choices=[("false", _("no")), ("crop", _("alternative Copy-Mode/DM800hd (24bit)")), ("true", _("yes"))], default="false")
LCD4linux.CalTimeZone = ConfigSelection(choices=[("-3", "-3"), ("-2", "-2"), ("-1", "-1"), ("0", "0"), ("1", "1"), ("2", "2"), ("3", "3")], default="0")
LCD4linux.Cal = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.CalLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.CalPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.CalAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.CalSplit = ConfigYesNo(default=False)
LCD4linux.CalZoom = ConfigSlider(default=10, increment=1, limits=(3, 50))
LCD4linux.CalType = ConfigSelection(choices=CalType, default="0A")
LCD4linux.CalTypeE = ConfigSelection(choices=CalTypeE, default="D2")
LCD4linux.CalLayout = ConfigSelection(choices=CalLayout, default="0")
LCD4linux.CalColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.CalBackColor = ConfigSelection(choices=Farbe, default="gray")
LCD4linux.CalCaptionColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.CalShadow = ConfigYesNo(default=False)
LCD4linux.CalFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.CalList = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.CalListLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.CalListSize = ConfigSlider(default=12, increment=1, limits=(5, 150))
LCD4linux.CalListPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.CalListAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.CalListSplit = ConfigYesNo(default=False)
LCD4linux.CalListLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.CalListProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.CalListType = ConfigSelection(choices=CalListType, default="C")
LCD4linux.CalListColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.CalListShadow = ConfigYesNo(default=False)
LCD4linux.CalListFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Font = ConfigText(default=FONTdefault, fixed_size=False, visible_width=50)
LCD4linux.Font1 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Font2 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Font3 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Font4 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Font5 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.EnableEventLog = ConfigSelection(choices=[("0", _("off")), ("1", _("Logfile normal")), ("2", _("Logfile extensive")), ("3", _("Console normal"))], default="0")
LCD4linux.TunerColor = ConfigSelection(choices=Farbe, default="slategray")
LCD4linux.TunerColorActive = ConfigSelection(choices=Farbe, default="lime")
LCD4linux.TunerColorOn = ConfigSelection(choices=Farbe, default="yellow")
LCD4linux.OSD = ConfigSelection(choices=[("0", _("disabled"))] + TimeSelect + [("9999", _("always"))], default="0")
LCD4linux.OSDLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.OSDsize = ConfigSlider(default=425, increment=5, limits=(320, 1280))
LCD4linux.OSDshow = ConfigSelection(choices=[("TRM", _("TV+Radio+Media")), ("TR", _("TV+Radio")), ("RM", _("Radio+Media")), ("T", _("TV")), ("R", _("Radio")), ("M", _("Media"))], default="TRM")
LCD4linux.OSDTransparenz = ConfigSelection(choices=[("0", _("normal (full)")), ("3", _("TV (full)")), ("1", _("trimmed (transparent)")), ("2", _("trimmed (black)"))], default="1")
LCD4linux.OSDfast = ConfigYesNo(default=False)
LCD4linux.Popup = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.PopupKey = ConfigSelection(choices=[("0", _("MUTE or defined Keys")), ("1", _("any Key"))], default="0")
LCD4linux.PopupLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.PopupSize = ConfigSlider(default=30, increment=1, limits=(10, 150))
LCD4linux.PopupPos = ConfigSlider(default=30, increment=2, limits=(0, 1024))
LCD4linux.PopupAlign = ConfigSelection(choices=[("0", _("left")), ("1", _("center")), ("2", _("right"))], default="0")
LCD4linux.PopupColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.PopupBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="brown")
LCD4linux.PopupFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Mail = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MailLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MailSize = ConfigSlider(default=12, increment=1, limits=(5, 150))
LCD4linux.MailPos = ConfigSlider(default=30, increment=2, limits=(0, 1024))
LCD4linux.MailAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MailSplit = ConfigYesNo(default=False)
LCD4linux.MailColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MailBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MailKonto = ConfigSelection(choices=MailKonto, default="1")
LCD4linux.MailLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.MailType = ConfigSelection(choices=MailType, default="A1")
LCD4linux.MailProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.MailShadow = ConfigYesNo(default=False)
LCD4linux.MailFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.IconBar = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.IconBarLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.IconBarSize = ConfigSlider(default=20, increment=1, limits=(8, 150))
LCD4linux.IconBarPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.IconBarAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.IconBarSplit = ConfigYesNo(default=False)
LCD4linux.IconBarType = ConfigSelection(choices=DirType, default="0")
LCD4linux.IconBarPopup = ConfigSelection(choices=[("0", _("off"))] + ScreenSet, default="0")
LCD4linux.IconBarPopupLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Sun = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.SunLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.SunSize = ConfigSlider(default=20, increment=1, limits=(5, 150))
LCD4linux.SunPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.SunAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.SunSplit = ConfigYesNo(default=False)
LCD4linux.SunColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.SunBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.SunShadow = ConfigYesNo(default=False)
LCD4linux.SunFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.SunType = ConfigSelection(choices=DirType, default="2")
LCD4linux.Fritz = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.FritzLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.FritzSize = ConfigSlider(default=22, increment=1, limits=(8, 150))
LCD4linux.FritzPos = ConfigSlider(default=130, increment=2, limits=(0, 1024))
LCD4linux.FritzAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.FritzColor = ConfigSelection(choices=Farbe, default="yellow")
LCD4linux.FritzBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.FritzType = ConfigSelection(choices=FritzType, default="TL")
LCD4linux.FritzPicSize = ConfigSlider(default=100, increment=1, limits=(10, 1024))
LCD4linux.FritzPicPos = ConfigSlider(default=30, increment=2, limits=(0, 1024))
LCD4linux.FritzPicAlign = ConfigSlider(default=0, increment=10, limits=(0, 1024))
LCD4linux.FritzShadow = ConfigYesNo(default=False)
LCD4linux.FritzFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Picon = ConfigSelection(choices=ScreenSelect, default="1")
LCD4linux.PiconLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.PiconPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.PiconSize = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.PiconFullScreen = ConfigYesNo(default=False)
LCD4linux.PiconAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.PiconSplit = ConfigYesNo(default=False)
LCD4linux.PiconTextSize = ConfigSlider(default=30, increment=2, limits=(8, 150))
LCD4linux.PiconPath = ConfigText(default=LCD4picon, fixed_size=False, visible_width=50)
LCD4linux.PiconPathAlt = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.PiconTransparenz = ConfigSelection(choices=[("0", _("no")), ("2", _("yes"))], default="2")
LCD4linux.PiconCache = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Picon2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Picon2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Picon2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.Picon2Size = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.Picon2FullScreen = ConfigYesNo(default=False)
LCD4linux.Picon2Align = ConfigSelection(choices=AlignType, default="1")
LCD4linux.Picon2Split = ConfigYesNo(default=False)
LCD4linux.Picon2TextSize = ConfigSlider(default=30, increment=2, limits=(10, 150))
LCD4linux.Picon2Path = ConfigText(default=LCD4picon, fixed_size=False, visible_width=50)
LCD4linux.Picon2PathAlt = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Picon2Cache = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Clock = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ClockLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ClockType = ConfigSelection(choices=ClockType, default="12")
LCD4linux.ClockSpacing = ConfigSelectionNumber(0, 3, 1, default=0)
LCD4linux.ClockAnalog = ConfigSelection(choices=FoundClockDir, default=FoundClockDir[0])
LCD4linux.ClockSize = ConfigSlider(default=70, increment=2, limits=(10, 400))
LCD4linux.ClockPos = ConfigSlider(default=150, increment=2, limits=(0, 1024))
LCD4linux.ClockAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.ClockSplit = ConfigYesNo(default=False)
LCD4linux.ClockColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ClockShadow = ConfigYesNo(default=False)
LCD4linux.ClockFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Clock2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Clock2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Clock2Type = ConfigSelection(choices=ClockType, default="12")
LCD4linux.Clock2Spacing = ConfigSelectionNumber(0, 3, 1, default=0)
LCD4linux.Clock2Analog = ConfigSelection(choices=FoundClockDir, default=FoundClockDir[0])
LCD4linux.Clock2Size = ConfigSlider(default=70, increment=2, limits=(10, 400))
LCD4linux.Clock2Pos = ConfigSlider(default=150, increment=2, limits=(0, 1024))
LCD4linux.Clock2Align = ConfigSelection(choices=AlignType, default="1")
LCD4linux.Clock2Split = ConfigYesNo(default=False)
LCD4linux.Clock2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Clock2Shadow = ConfigYesNo(default=False)
LCD4linux.Clock2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.Channel = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ChannelLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ChannelSize = ConfigSlider(default=50, increment=2, limits=(10, 300))
LCD4linux.ChannelLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.ChannelPos = ConfigSlider(default=10, increment=2, limits=(0, 1024))
LCD4linux.ChannelLines = ConfigSelectionNumber(0, 9, 1, default=1)
LCD4linux.ChannelAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.ChannelSplit = ConfigYesNo(default=False)
LCD4linux.ChannelColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ChannelShadow = ConfigYesNo(default=False)
LCD4linux.ChannelFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.ChannelNum = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ChannelNumLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ChannelNumSize = ConfigSlider(default=60, increment=2, limits=(10, 300))
LCD4linux.ChannelNumPos = ConfigSlider(default=10, increment=2, limits=(0, 1024))
LCD4linux.ChannelNumAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.ChannelNumShadow = ConfigYesNo(default=False)
LCD4linux.ChannelNumColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ChannelNumBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.ChannelNumFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Desc = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.DescLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.DescType = ConfigSelection(choices=DescriptionType, default="01")
LCD4linux.DescSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.DescLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.DescPos = ConfigSlider(default=130, increment=2, limits=(0, 1024))
LCD4linux.DescAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.DescLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.DescSplit = ConfigYesNo(default=False)
LCD4linux.DescColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.DescShadow = ConfigYesNo(default=False)
LCD4linux.DescFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.DescUseInfo = ConfigYesNo(default=False)
LCD4linux.Prog = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ProgLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ProgType = ConfigSelection(choices=[("1", _("Time+Info")), ("2", _("Info")), ("3", _("Time+Duration+Info"))], default="1")
LCD4linux.ProgSize = ConfigSlider(default=32, increment=1, limits=(8, 150))
LCD4linux.ProgLines = ConfigSelectionNumber(1, 9, 1, default=3)
LCD4linux.ProgPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.ProgAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.ProgLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.ProgSplit = ConfigYesNo(default=False)
LCD4linux.ProgColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ProgShadow = ConfigYesNo(default=False)
LCD4linux.ProgFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Prog2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Prog2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Prog2Type = ConfigSelection(choices=[("1", _("Time+Info")), ("2", _("Info")), ("3", _("Time+Duration+Info"))], default="1")
LCD4linux.Prog2Size = ConfigSlider(default=32, increment=1, limits=(8, 150))
LCD4linux.Prog2Lines = ConfigSelectionNumber(1, 9, 1, default=3)
LCD4linux.Prog2Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.Prog2Align = ConfigSelection(choices=AlignType, default="1")
LCD4linux.Prog2Len = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.Prog2Split = ConfigYesNo(default=False)
LCD4linux.Prog2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Prog2Shadow = ConfigYesNo(default=False)
LCD4linux.Prog2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.ProgNext = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ProgNextLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ProgNextType = ConfigSelection(choices=[("1", _("Time+Info")), ("2", _("Info")), ("3", _("Time+Length+Info")), ("4", _("Mini-EPG"))], default="1")
LCD4linux.ProgNextSize = ConfigSlider(default=32, increment=1, limits=(8, 150))
LCD4linux.ProgNextLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.ProgNextPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.ProgNextAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.ProgNextLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.ProgNextSplit = ConfigYesNo(default=False)
LCD4linux.ProgNextColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ProgNextShadow = ConfigYesNo(default=False)
LCD4linux.ProgNextFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Progress = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ProgressLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ProgressType = ConfigSelection(choices=ProgressType, default="1")
LCD4linux.ProgressSize = ConfigSlider(default=10, increment=1, limits=(5, 100))
LCD4linux.ProgressLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.ProgressAlign = ConfigSelection(choices=[("5", _("half left")), ("6", _("half right"))] + AlignType, default="1")
LCD4linux.ProgressPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.ProgressColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ProgressColorText = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ProgressMinutes = ConfigYesNo(default=True)
LCD4linux.ProgressBorder = ConfigSelection(choices=[("off", _("no Bar")), ("true", _("Frame")), ("true2", _("Frame x2")), ("false", _("no Frame")), ("line", _("Line"))], default="true")
LCD4linux.ProgressShadow = ConfigYesNo(default=False)
LCD4linux.ProgressShadow2 = ConfigSelection(choices=[("false", _("Normal")), ("true", _("Shadow Edges")), ("gradient", _("Gradient"))], default="false")
LCD4linux.ProgressFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Sat = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.SatLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.SatSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.SatPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.SatAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.SatSplit = ConfigYesNo(default=False)
LCD4linux.SatColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.SatType = ConfigSelection(choices=[("0", _("Position")), ("1", _("Name")), ("2", _("Picon")), ("2A", _("Picon+Position left")), ("2B", _("Picon+Position below")), ("2C", _("Picon+Position right"))], default="1")
LCD4linux.SatPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.SatShadow = ConfigYesNo(default=False)
LCD4linux.SatFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Prov = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ProvLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ProvSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.ProvPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.ProvAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.ProvSplit = ConfigYesNo(default=False)
LCD4linux.ProvColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ProvType = ConfigSelection(choices=[("1", _("Name")), ("2", _("Picon"))], default="1")
LCD4linux.ProvPath = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.ProvShadow = ConfigYesNo(default=False)
LCD4linux.ProvFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Info = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.InfoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.InfoTuner = ConfigSelection(choices=InfoTuner, default="0")
LCD4linux.InfoSensor = ConfigSelection(choices=InfoSensor, default="0")
LCD4linux.InfoCPU = ConfigSelection(choices=InfoCPU, default="0")
LCD4linux.InfoSize = ConfigSlider(default=20, increment=1, limits=(10, 150))
LCD4linux.InfoPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.InfoAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.InfoSplit = ConfigYesNo(default=False)
LCD4linux.InfoLines = ConfigSelectionNumber(1, 9, 1, default=1)
LCD4linux.InfoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.InfoShadow = ConfigYesNo(default=False)
LCD4linux.InfoFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Info2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Info2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Info2Tuner = ConfigSelection(choices=InfoTuner, default="0")
LCD4linux.Info2Sensor = ConfigSelection(choices=InfoSensor, default="0")
LCD4linux.Info2CPU = ConfigSelection(choices=InfoCPU, default="0")
LCD4linux.Info2Size = ConfigSlider(default=20, increment=1, limits=(10, 150))
LCD4linux.Info2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.Info2Align = ConfigSelection(choices=AlignType, default="1")
LCD4linux.Info2Split = ConfigYesNo(default=False)
LCD4linux.Info2Lines = ConfigSelectionNumber(1, 9, 1, default=1)
LCD4linux.Info2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Info2Shadow = ConfigYesNo(default=False)
LCD4linux.Info2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.Signal = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.SignalLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.SignalSize = ConfigSlider(default=15, increment=1, limits=(5, 150))
LCD4linux.SignalPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.SignalLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.SignalAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.SignalSplit = ConfigYesNo(default=False)
LCD4linux.SignalColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.SignalGradient = ConfigYesNo(default=False)
LCD4linux.SignalMin = ConfigSlider(default=40, increment=5, limits=(0, 50))
LCD4linux.SignalMax = ConfigSlider(default=90, increment=5, limits=(50, 100))
LCD4linux.Tuner = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.TunerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.TunerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.TunerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.TunerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.TunerSplit = ConfigYesNo(default=False)
LCD4linux.TunerType = ConfigSelection(choices=DirType + [("1", "%s x2" % _("horizontally"))], default="0")
LCD4linux.TunerActive = ConfigYesNo(default=False)
LCD4linux.TunerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Vol = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.VolLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.VolSize = ConfigSlider(default=22, increment=1, limits=(5, 150))
LCD4linux.VolPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.VolAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.VolLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.VolSplit = ConfigYesNo(default=False)
LCD4linux.VolColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.VolShadow = ConfigYesNo(default=False)
LCD4linux.Ping = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.PingLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.PingSize = ConfigSlider(default=15, increment=2, limits=(10, 100))
LCD4linux.PingPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.PingAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.PingSplit = ConfigYesNo(default=False)
LCD4linux.PingColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.PingShadow = ConfigYesNo(default=False)
LCD4linux.PingFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.PingShow = ConfigSelection(choices=[("0", _("Online+Offline")), ("1", _("Online")), ("2", _("Offline"))], default="0")
LCD4linux.PingType = ConfigSelection(choices=DirType, default="0")
LCD4linux.PingTimeout = ConfigSlider(default=50, increment=5, limits=(5, 2000))
LCD4linux.PingName1 = ConfigText(default="Internet:www.google.de", fixed_size=False)
LCD4linux.PingName2 = ConfigText(default="", fixed_size=False)
LCD4linux.PingName3 = ConfigText(default="", fixed_size=False)
LCD4linux.PingName4 = ConfigText(default="", fixed_size=False)
LCD4linux.PingName5 = ConfigText(default="", fixed_size=False)
LCD4linux.ExternalIp = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ExternalIpLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ExternalIpFile = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.ExternalIpSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.ExternalIpFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.ExternalIpPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.ExternalIpAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.ExternalIpSplit = ConfigYesNo(default=False)
LCD4linux.ExternalIpShadow = ConfigYesNo(default=False)
LCD4linux.ExternalIpColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ExternalIpBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.ExternalIpUrl = ConfigText(default="http://icanhazip.com", fixed_size=False, visible_width=50)
LCD4linux.RBox = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.RBoxLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.RBoxSize = ConfigSlider(default=15, increment=2, limits=(6, 100))
LCD4linux.RBoxPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.RBoxAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.RBoxProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.RBoxColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.RBoxColor2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.RBoxColor3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.RBoxColor4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.RBoxColor5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.RBoxShadow = ConfigYesNo(default=False)
LCD4linux.RBoxFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.RBoxShow = ConfigSelection(choices=RBoxType, default="PCT")
LCD4linux.RBoxName1 = ConfigText(default="Box:localhost", fixed_size=False)
LCD4linux.RBoxName2 = ConfigText(default="", fixed_size=False)
LCD4linux.RBoxName3 = ConfigText(default="", fixed_size=False)
LCD4linux.RBoxName4 = ConfigText(default="", fixed_size=False)
LCD4linux.RBoxName5 = ConfigText(default="", fixed_size=False)
LCD4linux.RBoxRefresh = ConfigSelectionNumber(1, 10, 1, default=1)
LCD4linux.RBoxTimer = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.RBoxTimerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.RBoxTimerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.RBoxTimerLines = ConfigSelectionNumber(1, 20, 1, default=1)
LCD4linux.RBoxTimerType = ConfigSelection(choices=[("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.RBoxTimerType2 = ConfigSelection(choices=[("0", _("no total Timer")), ("1", _("show total Timer"))], default="1")
LCD4linux.RBoxTimerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.RBoxTimerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.RBoxTimerLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.RBoxTimerSplit = ConfigYesNo(default=False)
LCD4linux.RBoxTimerColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.RBoxTimerShadow = ConfigYesNo(default=False)
LCD4linux.RBoxTimerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.RBoxTimerName1 = ConfigText(default="Box:localhost", fixed_size=False)
LCD4linux.RBoxTimerRefresh = ConfigSelectionNumber(5, 60, 5, default=15)
LCD4linux.AV = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.AVLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.AVSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.AVPos = ConfigSlider(default=100, increment=2, limits=(0, 1024))
LCD4linux.AVAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.AVSplit = ConfigYesNo(default=False)
LCD4linux.AVColor = ConfigSelection(choices=Farbe, default="gold")
LCD4linux.AVShadow = ConfigYesNo(default=False)
LCD4linux.AVType = ConfigSelection(choices=[("1", _("one line")), ("2", _("two lines"))], default="1")
LCD4linux.AVFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Bitrate = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.BitrateLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.BitrateSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.BitratePos = ConfigSlider(default=100, increment=2, limits=(0, 1024))
LCD4linux.BitrateAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.BitrateSplit = ConfigYesNo(default=False)
LCD4linux.BitrateColor = ConfigSelection(choices=Farbe, default="gold")
LCD4linux.BitrateShadow = ConfigYesNo(default=False)
LCD4linux.BitrateFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Dev = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.DevLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.DevSize = ConfigSlider(default=15, increment=2, limits=(10, 300))
LCD4linux.DevPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.DevAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.DevSplit = ConfigYesNo(default=False)
LCD4linux.DevColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.DevShadow = ConfigYesNo(default=False)
LCD4linux.DevFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.DevType = ConfigSelection(choices=DirType, default="0")
LCD4linux.DevWarning = ConfigSelection(choices=WarningType, default="10")
LCD4linux.DevExtra = ConfigSelection(choices=[("0", _("no")), ("RAM", _("Memory free")), ("RAM2", _("Memory available"))], default="RAM2")
LCD4linux.DevName1 = ConfigText(default="/media/hdd", fixed_size=False)
LCD4linux.DevName2 = ConfigText(default="", fixed_size=False)
LCD4linux.DevName3 = ConfigText(default="", fixed_size=False)
LCD4linux.DevName4 = ConfigText(default="", fixed_size=False)
LCD4linux.DevName5 = ConfigText(default="", fixed_size=False)
LCD4linux.Hdd = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.HddLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.HddSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.HddPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.HddAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.HddSplit = ConfigYesNo(default=False)
LCD4linux.HddType = ConfigSelection(choices=HddType, default="0")
LCD4linux.Mute = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MuteLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MuteSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.MutePos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MuteAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MuteSplit = ConfigYesNo(default=False)
LCD4linux.Timer = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.TimerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.TimerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.TimerLines = ConfigSelectionNumber(1, 20, 1, default=1)
LCD4linux.TimerType = ConfigSelection(choices=[("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.TimerType2 = ConfigSelection(choices=[("0", _("no total Timer")), ("1", _("show total Timer"))], default="1")
LCD4linux.TimerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.TimerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.TimerLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.TimerSplit = ConfigYesNo(default=False)
LCD4linux.TimerColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.TimerShadow = ConfigYesNo(default=False)
LCD4linux.TimerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Wetter = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.WetterLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.WetterPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.WetterAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.WetterSplit = ConfigYesNo(default=False)
LCD4linux.WetterZoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.WetterType = ConfigSelection(choices=WetterType, default="1")
LCD4linux.WetterColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.WetterShadow = ConfigYesNo(default=False)
LCD4linux.WetterFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.Wetter2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Wetter2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Wetter2Pos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.Wetter2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.Wetter2Split = ConfigYesNo(default=False)
LCD4linux.Wetter2Zoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.Wetter2Type = ConfigSelection(choices=WetterType, default="1")
LCD4linux.Wetter2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Wetter2Shadow = ConfigYesNo(default=False)
LCD4linux.Wetter2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.Meteo = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MeteoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MeteoPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.MeteoAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MeteoSplit = ConfigYesNo(default=False)
LCD4linux.MeteoZoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.MeteoType = ConfigSelection(choices=MeteoType, default="1")
LCD4linux.MeteoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Moon = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MoonLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MoonSize = ConfigSlider(default=60, increment=2, limits=(10, 300))
LCD4linux.MoonFontSize = ConfigSlider(default=30, increment=1, limits=(8, 100))
LCD4linux.MoonPos = ConfigSlider(default=10, increment=2, limits=(0, 1024))
LCD4linux.MoonAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MoonInfos = ConfigSelection(choices=MoonInfoSelect, default="111")
LCD4linux.MoonTrends = ConfigYesNo(default=True)
LCD4linux.MoonSplit = ConfigYesNo(default=False)
LCD4linux.MoonColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="white")
LCD4linux.MoonShadow = ConfigYesNo(default=False)
LCD4linux.MoonFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.NetAtmoCO2Min = ConfigSlider(default=200, increment=100, limits=(0, 1000))
LCD4linux.NetAtmoCO2Max = ConfigSlider(default=1500, increment=100, limits=(500, 10000))
LCD4linux.NetAtmo = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.NetAtmoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.NetAtmoPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.NetAtmoAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.NetAtmoSplit = ConfigYesNo(default=False)
LCD4linux.NetAtmoStation = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.NetAtmoModule = ConfigSelection(choices=NetatmoSelect, default="123456")
LCD4linux.NetAtmoModuleUser = ConfigText(default="123456", fixed_size=False)
LCD4linux.NetAtmoName = ConfigYesNo(default=True)
LCD4linux.NetAtmoBasis = ConfigYesNo(default=True)
LCD4linux.NetAtmoType = ConfigSelection(choices=NetatmoType, default="THCPN")
LCD4linux.NetAtmoType2 = ConfigSelection(choices=DirType, default="0")
LCD4linux.NetAtmoSize = ConfigSlider(default=30, increment=1, limits=(10, 100))
LCD4linux.NetAtmoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.NetAtmoColor2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmoColor3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmoColor4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmoColor5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmoColor6 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmoColor7 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmoShadow = ConfigYesNo(default=False)
LCD4linux.NetAtmoFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.NetAtmo2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.NetAtmo2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.NetAtmo2Pos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.NetAtmo2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.NetAtmo2Split = ConfigYesNo(default=False)
LCD4linux.NetAtmo2Station = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.NetAtmo2Module = ConfigSelection(choices=NetatmoSelect, default="123456")
LCD4linux.NetAtmo2ModuleUser = ConfigText(default="123456", fixed_size=False)
LCD4linux.NetAtmo2Name = ConfigYesNo(default=True)
LCD4linux.NetAtmo2Basis = ConfigYesNo(default=True)
LCD4linux.NetAtmo2Type = ConfigSelection(choices=NetatmoType, default="THCPN")
LCD4linux.NetAtmo2Type2 = ConfigSelection(choices=DirType, default="0")
LCD4linux.NetAtmo2Size = ConfigSlider(default=30, increment=1, limits=(10, 100))
LCD4linux.NetAtmo2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.NetAtmo2Color2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmo2Color3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmo2Color4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmo2Color5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmo2Color6 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmo2Color7 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.NetAtmo2Shadow = ConfigYesNo(default=False)
LCD4linux.NetAtmo2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.NetAtmoCO2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.NetAtmoCO2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.NetAtmoCO2Size = ConfigSlider(default=30, increment=1, limits=(5, 500))
LCD4linux.NetAtmoCO2Len = ConfigSlider(default=200, increment=5, limits=(100, 1024))
LCD4linux.NetAtmoCO2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.NetAtmoCO2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.NetAtmoCO2Split = ConfigYesNo(default=False)
LCD4linux.NetAtmoCO2Station = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.NetAtmoCO2Type = ConfigSelection(choices=CO2Type, default="1")
LCD4linux.NetAtmoIDX = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.NetAtmoIDXLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.NetAtmoIDXSize = ConfigSlider(default=30, increment=1, limits=(5, 500))
LCD4linux.NetAtmoIDXLen = ConfigSlider(default=200, increment=5, limits=(100, 1024))
LCD4linux.NetAtmoIDXPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.NetAtmoIDXAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.NetAtmoIDXSplit = ConfigYesNo(default=False)
LCD4linux.NetAtmoIDXStation = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.NetAtmoIDXType = ConfigSelection(choices=CO2Type, default="1")
LCD4linux.OSCAM = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.OSCAMLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.OSCAMFile = ConfigText(default="/tmp/.oscam/oscam.lcd", fixed_size=False)
LCD4linux.OSCAMSize = ConfigSlider(default=10, increment=1, limits=(9, 50))
LCD4linux.OSCAMPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.OSCAMAlign = ConfigSelection(choices=[("0", _("left")), ("2", _("right"))], default="0")
LCD4linux.OSCAMSplit = ConfigYesNo(default=False)
LCD4linux.OSCAMColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.OSCAMBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="black")
LCD4linux.ECM = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.ECMLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.ECMSize = ConfigSlider(default=10, increment=1, limits=(9, 50))
LCD4linux.ECMPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.ECMAlign = ConfigSelection(choices=[("0", _("left")), ("2", _("right"))], default="0")
LCD4linux.ECMSplit = ConfigYesNo(default=False)
LCD4linux.ECMColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.ECMBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="black")
LCD4linux.String = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StringLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StringText = ConfigText(default="Hello", fixed_size=False, visible_width=50)
LCD4linux.StringSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.StringFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StringPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StringAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StringSplit = ConfigYesNo(default=False)
LCD4linux.StringShadow = ConfigYesNo(default=False)
LCD4linux.StringColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StringBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.String2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.String2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.String2Text = ConfigText(default="Hello", fixed_size=False, visible_width=50)
LCD4linux.String2Size = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.String2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.String2Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.String2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.String2Split = ConfigYesNo(default=False)
LCD4linux.String2Shadow = ConfigYesNo(default=False)
LCD4linux.String2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.String2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.Text = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.TextLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.TextFile = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.TextSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.TextFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.TextPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.TextAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.TextShadow = ConfigYesNo(default=False)
LCD4linux.TextColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.TextBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.Text2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Text2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Text2File = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.Text2Size = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.Text2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.Text2Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.Text2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.Text2Shadow = ConfigYesNo(default=False)
LCD4linux.Text2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Text2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.Text3 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Text3LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Text3File = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.Text3Size = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.Text3Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.Text3Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.Text3Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.Text3Shadow = ConfigYesNo(default=False)
LCD4linux.Text3Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Text3BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.HTTP = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.HTTPLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.HTTPURL = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.HTTPSize = ConfigSlider(default=20, increment=1, limits=(10, 300))
LCD4linux.HTTPPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.HTTPAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.HTTPColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.HTTPBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.HTTPShadow = ConfigYesNo(default=False)
LCD4linux.HTTPFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.WwwTime = ConfigSelection(choices=[("10", _("60min")), ("10,40", _("30min"))], default="10")
LCD4linux.WwwApiUsage = ConfigSelection(choices=[("cloudconvert", _("cloudconvert.org")), ("convertapi", _("convertapi.com"))], default="cloudconvert")
LCD4linux.WwwApiKeyCloudconvert = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.WwwApiKeyConvertapi = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.WWW1 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.WWW1LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.WWW1Size = ConfigSlider(default=200, increment=1, limits=(50, 1024))
LCD4linux.WWW1Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.WWW1Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.WWW1url = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.WWW1w = ConfigSlider(default=800, increment=50, limits=(600, 2000))
LCD4linux.WWW1h = ConfigSlider(default=600, increment=50, limits=(100, 2000))
LCD4linux.WWW1CutX = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.WWW1CutY = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.WWW1CutW = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.WWW1CutH = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.Bild = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.BildLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.BildFile = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.BildSize = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.BildSizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.BildPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.BildAlign = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.BildQuick = ConfigYesNo(default=False)
LCD4linux.BildTransp = ConfigYesNo(default=False)
LCD4linux.Bild2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Bild2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Bild2File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.Bild2Size = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.Bild2SizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.Bild2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.Bild2Align = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.Bild2Quick = ConfigYesNo(default=False)
LCD4linux.Bild2Transp = ConfigYesNo(default=False)
LCD4linux.Bild3 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Bild3LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Bild3File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.Bild3Size = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.Bild3SizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.Bild3Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.Bild3Align = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.Bild3Quick = ConfigYesNo(default=False)
LCD4linux.Bild3Transp = ConfigYesNo(default=False)
LCD4linux.Bild4 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Bild4LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Bild4File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.Bild4Size = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.Bild4SizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.Bild4Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.Bild4Align = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.Bild4Quick = ConfigYesNo(default=False)
LCD4linux.Bild4Transp = ConfigYesNo(default=False)
LCD4linux.TV = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.TVLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.TVType = ConfigSelection(choices=[("0", _("TV")), ("1", _("TV+OSD"))], default="0")
LCD4linux.Box1 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Box1LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Box1x1 = ConfigSlider(default=10, increment=1, limits=(0, 1024))
LCD4linux.Box1y1 = ConfigSlider(default=10, increment=1, limits=(0, 1024))
LCD4linux.Box1x2 = ConfigSlider(default=200, increment=1, limits=(0, 1024))
LCD4linux.Box1y2 = ConfigSlider(default=1, increment=1, limits=(0, 1024))
LCD4linux.Box1Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Box1BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.Box2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Box2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Box2x1 = ConfigSlider(default=20, increment=1, limits=(0, 1024))
LCD4linux.Box2y1 = ConfigSlider(default=20, increment=1, limits=(0, 1024))
LCD4linux.Box2x2 = ConfigSlider(default=200, increment=1, limits=(0, 1024))
LCD4linux.Box2y2 = ConfigSlider(default=1, increment=1, limits=(0, 1024))
LCD4linux.Box2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.Box2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.Background1 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.Background1LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.Background1Color = ConfigSelection(choices=Farbe, default="black")
LCD4linux.Background1Bild = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.MPHelligkeit = ConfigSelectionNumber(0, 10, 1, default=5)
LCD4linux.MPHelligkeit2 = ConfigSelectionNumber(0, 10, 1, default=5)
LCD4linux.MPHelligkeit3 = ConfigSelectionNumber(0, 10, 1, default=5)
LCD4linux.MPNight = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.MPNight2 = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.MPNight3 = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.MPAutoOFF = ConfigSelection(choices=[("0", _("off"))] + TimeSelect, default="0")
LCD4linux.MPScreenMax = ConfigSelection(choices=ScreenUse, default="1")
LCD4linux.MPLCDBild1 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.MPLCDBild2 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.MPLCDBild3 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.MPLCDColor1 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.MPLCDColor2 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.MPLCDColor3 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.MPDesc = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPDescLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPDescType = ConfigSelection(choices=DescriptionType, default="01")
LCD4linux.MPDescSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.MPDescLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.MPDescPos = ConfigSlider(default=130, increment=2, limits=(0, 1024))
LCD4linux.MPDescAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPDescLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPDescSplit = ConfigYesNo(default=False)
LCD4linux.MPDescColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPDescShadow = ConfigYesNo(default=False)
LCD4linux.MPDescFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPDescUseInfo = ConfigYesNo(default=False)
LCD4linux.MPTitle = ConfigSelection(choices=ScreenSelect, default="1")
LCD4linux.MPTitleLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPTitleSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.MPTitleLines = ConfigSelectionNumber(1, 9, 1, default=3)
LCD4linux.MPTitlePos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPTitleAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPTitleLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPTitleSplit = ConfigYesNo(default=False)
LCD4linux.MPTitleColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPTitleShadow = ConfigYesNo(default=False)
LCD4linux.MPTitleFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPComm = ConfigSelection(choices=ScreenSelect, default="1")
LCD4linux.MPCommLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPCommSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.MPCommLines = ConfigSelectionNumber(1, 9, 1, default=3)
LCD4linux.MPCommPos = ConfigSlider(default=130, increment=2, limits=(0, 1024))
LCD4linux.MPCommAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPCommLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPCommSplit = ConfigYesNo(default=False)
LCD4linux.MPCommColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPCommShadow = ConfigYesNo(default=False)
LCD4linux.MPCommFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPChannel = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPChannelLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPChannelSize = ConfigSlider(default=50, increment=2, limits=(10, 300))
LCD4linux.MPChannelPos = ConfigSlider(default=10, increment=2, limits=(0, 1024))
LCD4linux.MPChannelLines = ConfigSelectionNumber(0, 9, 1, default=1)
LCD4linux.MPChannelAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPChannelLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPChannelSplit = ConfigYesNo(default=False)
LCD4linux.MPChannelColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPChannelShadow = ConfigYesNo(default=False)
LCD4linux.MPChannelFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPProg = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPProgLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPProgType = ConfigSelection(choices=[("1", _("Time+Info")), ("2", _("Info")), ("3", _("Time+Duration+Info"))], default="1")
LCD4linux.MPProgSize = ConfigSlider(default=32, increment=1, limits=(8, 150))
LCD4linux.MPProgLines = ConfigSelectionNumber(1, 9, 1, default=3)
LCD4linux.MPProgPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPProgAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPProgLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPProgSplit = ConfigYesNo(default=False)
LCD4linux.MPProgColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPProgShadow = ConfigYesNo(default=False)
LCD4linux.MPProgFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPProgNext = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPProgNextLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPProgNextType = ConfigSelection(choices=[("1", _("Time+Info")), ("2", _("Info")), ("3", _("Time+Length+Info")), ("4", _("Mini-EPG"))], default="1")
LCD4linux.MPProgNextSize = ConfigSlider(default=32, increment=1, limits=(8, 150))
LCD4linux.MPProgNextLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.MPProgNextPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPProgNextAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPProgNextLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPProgNextSplit = ConfigYesNo(default=False)
LCD4linux.MPProgNextColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPProgNextShadow = ConfigYesNo(default=False)
LCD4linux.MPProgNextFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPProgress = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPProgressLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPProgressType = ConfigSelection(choices=ProgressType, default="1")
LCD4linux.MPProgressSize = ConfigSlider(default=10, increment=1, limits=(5, 100))
LCD4linux.MPProgressLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPProgressPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPProgressAlign = ConfigSelection(choices=[("5", _("half left")), ("6", _("half right"))] + AlignType, default="1")
LCD4linux.MPProgressColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPProgressColorText = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPProgressMinutes = ConfigYesNo(default=True)
LCD4linux.MPProgressBorder = ConfigSelection(choices=[("off", _("no Bar")), ("true", _("Frame")), ("true2", _("Frame x2")), ("false", _("no Frame")), ("line", _("Line"))], default="true")
LCD4linux.MPProgressShadow = ConfigYesNo(default=False)
LCD4linux.MPProgressShadow2 = ConfigSelection(choices=[("false", _("Normal")), ("true", _("Shadow Edges")), ("gradient", _("Gradient"))], default="false")
LCD4linux.MPProgressFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPVol = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPVolLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPVolSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.MPVolPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPVolAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPVolLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPVolSplit = ConfigYesNo(default=False)
LCD4linux.MPVolColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPVolShadow = ConfigYesNo(default=False)
LCD4linux.MPPing = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPPingLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPPingSize = ConfigSlider(default=15, increment=2, limits=(10, 100))
LCD4linux.MPPingPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.MPPingAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPPingSplit = ConfigYesNo(default=False)
LCD4linux.MPPingColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPPingShadow = ConfigYesNo(default=False)
LCD4linux.MPPingFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPPingShow = ConfigSelection(choices=[("0", _("Online+Offline")), ("1", _("Online")), ("2", _("Offline"))], default="0")
LCD4linux.MPPingType = ConfigSelection(choices=DirType, default="0")
LCD4linux.MPPingTimeout = ConfigSlider(default=50, increment=5, limits=(5, 2000))
LCD4linux.MPPingName1 = ConfigText(default="Internet:www.google.de", fixed_size=False)
LCD4linux.MPPingName2 = ConfigText(default="", fixed_size=False)
LCD4linux.MPPingName3 = ConfigText(default="", fixed_size=False)
LCD4linux.MPPingName4 = ConfigText(default="", fixed_size=False)
LCD4linux.MPPingName5 = ConfigText(default="", fixed_size=False)
LCD4linux.MPExternalIp = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPExternalIpLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPExternalIpFile = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.MPExternalIpSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.MPExternalIpFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPExternalIpPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPExternalIpAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPExternalIpSplit = ConfigYesNo(default=False)
LCD4linux.MPExternalIpShadow = ConfigYesNo(default=False)
LCD4linux.MPExternalIpColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPExternalIpBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPRBox = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPRBoxLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPRBoxSize = ConfigSlider(default=15, increment=2, limits=(6, 100))
LCD4linux.MPRBoxPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.MPRBoxAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPRBoxProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.MPRBoxColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPRBoxColor2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPRBoxColor3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPRBoxColor4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPRBoxColor5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPRBoxShadow = ConfigYesNo(default=False)
LCD4linux.MPRBoxFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPRBoxShow = ConfigSelection(choices=RBoxType, default="PCT")
LCD4linux.MPRBoxTimer = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPRBoxTimerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPRBoxTimerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.MPRBoxTimerLines = ConfigSelectionNumber(1, 20, 1, default=1)
LCD4linux.MPRBoxTimerType = ConfigSelection(choices=[("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.MPRBoxTimerType2 = ConfigSelection(choices=[("0", _("no total Timer")), ("1", _("show total Timer"))], default="1")
LCD4linux.MPRBoxTimerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPRBoxTimerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPRBoxTimerLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPRBoxTimerSplit = ConfigYesNo(default=False)
LCD4linux.MPRBoxTimerColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPRBoxTimerShadow = ConfigYesNo(default=False)
LCD4linux.MPRBoxTimerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPClock = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPClockLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPClockType = ConfigSelection(choices=ClockType, default="12")
LCD4linux.MPClockSpacing = ConfigSelectionNumber(0, 3, 1, default=0)
LCD4linux.MPClockAnalog = ConfigSelection(choices=FoundClockDir, default=FoundClockDir[0])
LCD4linux.MPClockSize = ConfigSlider(default=70, increment=2, limits=(10, 400))
LCD4linux.MPClockPos = ConfigSlider(default=150, increment=2, limits=(0, 1024))
LCD4linux.MPClockAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPClockSplit = ConfigYesNo(default=False)
LCD4linux.MPClockColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPClockShadow = ConfigYesNo(default=False)
LCD4linux.MPClockFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPClock2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPClock2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPClock2Type = ConfigSelection(choices=ClockType, default="12")
LCD4linux.MPClock2Spacing = ConfigSelectionNumber(0, 3, 1, default=0)
LCD4linux.MPClock2Analog = ConfigSelection(choices=FoundClockDir, default=FoundClockDir[0])
LCD4linux.MPClock2Size = ConfigSlider(default=70, increment=2, limits=(10, 400))
LCD4linux.MPClock2Pos = ConfigSlider(default=150, increment=2, limits=(0, 1024))
LCD4linux.MPClock2Align = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPClock2Split = ConfigYesNo(default=False)
LCD4linux.MPClock2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPClock2Shadow = ConfigYesNo(default=False)
LCD4linux.MPClock2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPTuner = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPTunerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPTunerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.MPTunerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPTunerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPTunerSplit = ConfigYesNo(default=False)
LCD4linux.MPTunerType = ConfigSelection(choices=DirType + [("1", "%s x2" % _("horizontally"))], default="0")
LCD4linux.MPTunerActive = ConfigYesNo(default=False)
LCD4linux.MPTunerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPInfo = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPInfoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPInfoSensor = ConfigSelection(choices=InfoSensor, default="0")
LCD4linux.MPInfoCPU = ConfigSelection(choices=InfoCPU, default="0")
LCD4linux.MPInfoSize = ConfigSlider(default=20, increment=1, limits=(10, 150))
LCD4linux.MPInfoPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPInfoAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPInfoSplit = ConfigYesNo(default=False)
LCD4linux.MPInfoLines = ConfigSelectionNumber(1, 9, 1, default=1)
LCD4linux.MPInfoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPInfoShadow = ConfigYesNo(default=False)
LCD4linux.MPInfoFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPInfo2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPInfo2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPInfo2Sensor = ConfigSelection(choices=InfoSensor, default="0")
LCD4linux.MPInfo2CPU = ConfigSelection(choices=InfoCPU, default="0")
LCD4linux.MPInfo2Size = ConfigSlider(default=20, increment=1, limits=(10, 150))
LCD4linux.MPInfo2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPInfo2Align = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPInfo2Split = ConfigYesNo(default=False)
LCD4linux.MPInfo2Lines = ConfigSelectionNumber(1, 9, 1, default=1)
LCD4linux.MPInfo2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPInfo2Shadow = ConfigYesNo(default=False)
LCD4linux.MPInfo2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPAV = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPAVLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPAVSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.MPAVPos = ConfigSlider(default=100, increment=2, limits=(0, 1024))
LCD4linux.MPAVAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPAVSplit = ConfigYesNo(default=False)
LCD4linux.MPAVColor = ConfigSelection(choices=Farbe, default="gold")
LCD4linux.MPAVShadow = ConfigYesNo(default=False)
LCD4linux.MPAVType = ConfigSelection(choices=[("1", _("one line")), ("2", _("two lines"))], default="1")
LCD4linux.MPAVFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPBitrate = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPBitrateLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPBitrateSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.MPBitratePos = ConfigSlider(default=100, increment=2, limits=(0, 1024))
LCD4linux.MPBitrateAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPBitrateSplit = ConfigYesNo(default=False)
LCD4linux.MPBitrateColor = ConfigSelection(choices=Farbe, default="gold")
LCD4linux.MPBitrateShadow = ConfigYesNo(default=False)
LCD4linux.MPBitrateFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPDev = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPDevLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPDevSize = ConfigSlider(default=15, increment=2, limits=(10, 300))
LCD4linux.MPDevPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.MPDevAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPDevSplit = ConfigYesNo(default=False)
LCD4linux.MPDevColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPDevShadow = ConfigYesNo(default=False)
LCD4linux.MPDevFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPDevType = ConfigSelection(choices=DirType, default="0")
LCD4linux.MPDevWarning = ConfigSelection(choices=WarningType, default="10")
LCD4linux.MPDevExtra = ConfigSelection(choices=[("0", _("no")), ("RAM", _("Memory free")), ("RAM2", _("Memory available"))], default="RAM2")
LCD4linux.MPDevName1 = ConfigText(default="/media/hdd", fixed_size=False)
LCD4linux.MPDevName2 = ConfigText(default="", fixed_size=False)
LCD4linux.MPDevName3 = ConfigText(default="", fixed_size=False)
LCD4linux.MPDevName4 = ConfigText(default="", fixed_size=False)
LCD4linux.MPDevName5 = ConfigText(default="", fixed_size=False)
LCD4linux.MPHdd = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPHddLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPHddSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.MPHddPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPHddAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPHddSplit = ConfigYesNo(default=False)
LCD4linux.MPHddType = ConfigSelection(choices=HddType, default="0")
LCD4linux.MPMute = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPMuteLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPMuteSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.MPMutePos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPMuteAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPMuteSplit = ConfigYesNo(default=False)
LCD4linux.MPTimer = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPTimerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPTimerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.MPTimerLines = ConfigSelectionNumber(1, 20, 1, default=1)
LCD4linux.MPTimerType = ConfigSelection(choices=[("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.MPTimerType2 = ConfigSelection(choices=[("0", _("no total Timer")), ("1", _("show total Timer"))], default="1")
LCD4linux.MPTimerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPTimerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPTimerLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.MPTimerSplit = ConfigYesNo(default=False)
LCD4linux.MPTimerColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPTimerShadow = ConfigYesNo(default=False)
LCD4linux.MPTimerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPWetter = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPWetterLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPWetterPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.MPWetterAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPWetterSplit = ConfigYesNo(default=False)
LCD4linux.MPWetterZoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.MPWetterType = ConfigSelection(choices=WetterType, default="1")
LCD4linux.MPWetterColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPWetterShadow = ConfigYesNo(default=False)
LCD4linux.MPWetterFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPWetter2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPWetter2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPWetter2Pos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.MPWetter2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPWetter2Split = ConfigYesNo(default=False)
LCD4linux.MPWetter2Zoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.MPWetter2Type = ConfigSelection(choices=WetterType, default="1")
LCD4linux.MPWetter2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPWetter2Shadow = ConfigYesNo(default=False)
LCD4linux.MPWetter2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPMeteo = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPMeteoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPMeteoPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.MPMeteoAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPMeteoSplit = ConfigYesNo(default=False)
LCD4linux.MPMeteoZoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.MPMeteoType = ConfigSelection(choices=MeteoType, default="1")
LCD4linux.MPMeteoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPMoon = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPMoonLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPMoonSize = ConfigSlider(default=60, increment=2, limits=(10, 300))
LCD4linux.MPMoonFontSize = ConfigSlider(default=30, increment=1, limits=(8, 100))
LCD4linux.MPMoonPos = ConfigSlider(default=10, increment=2, limits=(0, 1024))
LCD4linux.MPMoonAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPMoonInfos = ConfigSelection(choices=MoonInfoSelect, default="111")
LCD4linux.MPMoonTrends = ConfigYesNo(default=True)
LCD4linux.MPMoonSplit = ConfigYesNo(default=False)
LCD4linux.MPMoonColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="white")
LCD4linux.MPMoonShadow = ConfigYesNo(default=False)
LCD4linux.MPMoonFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPNetAtmo = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPNetAtmoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPNetAtmoPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.MPNetAtmoAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPNetAtmoSplit = ConfigYesNo(default=False)
LCD4linux.MPNetAtmoStation = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.MPNetAtmoModule = ConfigSelection(choices=NetatmoSelect, default="123456")
LCD4linux.MPNetAtmoModuleUser = ConfigText(default="123456", fixed_size=False)
LCD4linux.MPNetAtmoName = ConfigYesNo(default=True)
LCD4linux.MPNetAtmoBasis = ConfigYesNo(default=True)
LCD4linux.MPNetAtmoType = ConfigSelection(choices=NetatmoType, default="THCPN")
LCD4linux.MPNetAtmoType2 = ConfigSelection(choices=DirType, default="0")
LCD4linux.MPNetAtmoSize = ConfigSlider(default=30, increment=1, limits=(10, 100))
LCD4linux.MPNetAtmoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPNetAtmoColor2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmoColor3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmoColor4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmoColor5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmoColor6 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmoColor7 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmoShadow = ConfigYesNo(default=False)
LCD4linux.MPNetAtmoFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPNetAtmo2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPNetAtmo2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPNetAtmo2Pos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.MPNetAtmo2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPNetAtmo2Split = ConfigYesNo(default=False)
LCD4linux.MPNetAtmo2Station = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.MPNetAtmo2Module = ConfigSelection(choices=NetatmoSelect, default="123456")
LCD4linux.MPNetAtmo2ModuleUser = ConfigText(default="123456", fixed_size=False)
LCD4linux.MPNetAtmo2Name = ConfigYesNo(default=True)
LCD4linux.MPNetAtmo2Basis = ConfigYesNo(default=True)
LCD4linux.MPNetAtmo2Type = ConfigSelection(choices=NetatmoType, default="THCPN")
LCD4linux.MPNetAtmo2Type2 = ConfigSelection(choices=DirType, default="0")
LCD4linux.MPNetAtmo2Size = ConfigSlider(default=30, increment=1, limits=(10, 100))
LCD4linux.MPNetAtmo2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPNetAtmo2Color2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmo2Color3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmo2Color4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmo2Color5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmo2Color6 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmo2Color7 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.MPNetAtmo2Shadow = ConfigYesNo(default=False)
LCD4linux.MPNetAtmo2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPNetAtmoCO2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPNetAtmoCO2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPNetAtmoCO2Size = ConfigSlider(default=30, increment=1, limits=(5, 500))
LCD4linux.MPNetAtmoCO2Len = ConfigSlider(default=200, increment=5, limits=(100, 1024))
LCD4linux.MPNetAtmoCO2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPNetAtmoCO2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPNetAtmoCO2Split = ConfigYesNo(default=False)
LCD4linux.MPNetAtmoCO2Station = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.MPNetAtmoCO2Type = ConfigSelection(choices=CO2Type, default="1")
LCD4linux.MPNetAtmoIDX = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPNetAtmoIDXLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPNetAtmoIDXSize = ConfigSlider(default=30, increment=1, limits=(5, 500))
LCD4linux.MPNetAtmoIDXLen = ConfigSlider(default=200, increment=5, limits=(100, 1024))
LCD4linux.MPNetAtmoIDXPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPNetAtmoIDXAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPNetAtmoIDXSplit = ConfigYesNo(default=False)
LCD4linux.MPNetAtmoIDXStation = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.MPNetAtmoIDXType = ConfigSelection(choices=CO2Type, default="1")
LCD4linux.MPBild = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPBildLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPBildFile = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.MPBildSize = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.MPBildSizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.MPBildPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPBildAlign = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.MPBildQuick = ConfigYesNo(default=False)
LCD4linux.MPBildTransp = ConfigYesNo(default=False)
LCD4linux.MPBild2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPBild2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPBild2File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.MPBild2Size = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.MPBild2SizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.MPBild2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPBild2Align = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.MPBild2Quick = ConfigYesNo(default=False)
LCD4linux.MPBild2Transp = ConfigYesNo(default=False)
LCD4linux.MPString = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPStringLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPStringText = ConfigText(default="Hello", fixed_size=False, visible_width=50)
LCD4linux.MPStringSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.MPStringFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPStringPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPStringAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPStringSplit = ConfigYesNo(default=False)
LCD4linux.MPStringShadow = ConfigYesNo(default=False)
LCD4linux.MPStringColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPStringBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPString2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPString2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPString2Text = ConfigText(default="Hello", fixed_size=False, visible_width=50)
LCD4linux.MPString2Size = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.MPString2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPString2Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPString2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPString2Split = ConfigYesNo(default=False)
LCD4linux.MPString2Shadow = ConfigYesNo(default=False)
LCD4linux.MPString2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPString2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPText = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPTextLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPTextFile = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.MPTextSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.MPTextFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPTextPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPTextAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPTextShadow = ConfigYesNo(default=False)
LCD4linux.MPTextColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPTextBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPText2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPText2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPText2File = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.MPText2Size = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.MPText2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPText2Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPText2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPText2Shadow = ConfigYesNo(default=False)
LCD4linux.MPText2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPText2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPCover = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPCoverLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPCoverPath1 = ConfigText(default="/tmp", fixed_size=False, visible_width=50)
LCD4linux.MPCoverPath2 = ConfigText(default="/tmp", fixed_size=False, visible_width=50)
LCD4linux.MPCoverFile = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.MPCoverFile2 = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.MPCoverSize = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.MPCoverSizeH = ConfigSlider(default=400, increment=10, limits=(10, 800))
LCD4linux.MPCoverPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPCoverAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPCoverTransp = ConfigYesNo(default=False)
LCD4linux.MPCoverTrim = ConfigYesNo(default=False)
LCD4linux.MPCoverPiconFirst = ConfigYesNo(default=True)
LCD4linux.MPCoverDownload = ConfigSelection(choices=[("0", _("no")), ("1", _("yes")), ("2", _("yes except records"))], default="1")
LCD4linux.MPCoverType = ConfigSelection(choices=[("0", _("Normal")), ("1", _("Google API"))], default="0")
LCD4linux.MPCoverApiGoogle = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.MPOSCAM = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPOSCAMLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPOSCAMSize = ConfigSlider(default=10, increment=1, limits=(9, 50))
LCD4linux.MPOSCAMPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.MPOSCAMAlign = ConfigSelection(choices=[("0", _("left")), ("2", _("right"))], default="0")
LCD4linux.MPOSCAMSplit = ConfigYesNo(default=False)
LCD4linux.MPOSCAMColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPOSCAMBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="black")
LCD4linux.MPMail = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPMailLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPMailSize = ConfigSlider(default=12, increment=1, limits=(5, 150))
LCD4linux.MPMailPos = ConfigSlider(default=30, increment=2, limits=(0, 1024))
LCD4linux.MPMailAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPMailSplit = ConfigYesNo(default=False)
LCD4linux.MPMailColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPMailBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPMailKonto = ConfigSelection(choices=MailKonto, default="1")
LCD4linux.MPMailLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.MPMailType = ConfigSelection(choices=MailType, default="A1")
LCD4linux.MPMailProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.MPMailShadow = ConfigYesNo(default=False)
LCD4linux.MPMailFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPIconBar = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPIconBarLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPIconBarSize = ConfigSlider(default=20, increment=1, limits=(10, 150))
LCD4linux.MPIconBarPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.MPIconBarAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.MPIconBarSplit = ConfigYesNo(default=False)
LCD4linux.MPIconBarType = ConfigSelection(choices=DirType, default="0")
LCD4linux.MPIconBarPopup = ConfigSelection(choices=[("0", _("off"))] + ScreenSet, default="0")
LCD4linux.MPIconBarPopupLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPSun = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPSunLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPSunSize = ConfigSlider(default=20, increment=1, limits=(5, 150))
LCD4linux.MPSunPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.MPSunAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPSunSplit = ConfigYesNo(default=False)
LCD4linux.MPSunColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPSunBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPSunShadow = ConfigYesNo(default=False)
LCD4linux.MPSunFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPSunType = ConfigSelection(choices=DirType, default="2")
LCD4linux.MPFritz = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPFritzLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPFritzSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.MPFritzPos = ConfigSlider(default=130, increment=2, limits=(0, 1024))
LCD4linux.MPFritzAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPFritzColor = ConfigSelection(choices=Farbe, default="yellow")
LCD4linux.MPFritzBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPFritzType = ConfigSelection(choices=FritzType, default="TL")
LCD4linux.MPFritzPicSize = ConfigSlider(default=100, increment=1, limits=(10, 800))
LCD4linux.MPFritzPicPos = ConfigSlider(default=30, increment=2, limits=(0, 1024))
LCD4linux.MPFritzPicAlign = ConfigSlider(default=0, increment=10, limits=(0, 1024))
LCD4linux.MPFritzShadow = ConfigYesNo(default=False)
LCD4linux.MPFritzFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPCal = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPCalLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPCalPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.MPCalAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPCalSplit = ConfigYesNo(default=False)
LCD4linux.MPCalZoom = ConfigSlider(default=10, increment=1, limits=(3, 50))
LCD4linux.MPCalType = ConfigSelection(choices=CalType, default="0A")
LCD4linux.MPCalTypeE = ConfigSelection(choices=CalTypeE, default="D2")
LCD4linux.MPCalColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPCalBackColor = ConfigSelection(choices=Farbe, default="gray")
LCD4linux.MPCalCaptionColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPCalLayout = ConfigSelection(choices=CalLayout, default="0")
LCD4linux.MPCalShadow = ConfigYesNo(default=False)
LCD4linux.MPCalFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPCalList = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPCalListLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPCalListSize = ConfigSlider(default=12, increment=1, limits=(5, 150))
LCD4linux.MPCalListPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.MPCalListAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.MPCalListSplit = ConfigYesNo(default=False)
LCD4linux.MPCalListLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.MPCalListProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.MPCalListType = ConfigSelection(choices=CalListType, default="C")
LCD4linux.MPCalListColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPCalListShadow = ConfigYesNo(default=False)
LCD4linux.MPCalListFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.MPBox1 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPBox1LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPBox1x1 = ConfigSlider(default=10, increment=1, limits=(0, 1024))
LCD4linux.MPBox1y1 = ConfigSlider(default=10, increment=1, limits=(0, 1024))
LCD4linux.MPBox1x2 = ConfigSlider(default=200, increment=1, limits=(0, 1024))
LCD4linux.MPBox1y2 = ConfigSlider(default=1, increment=1, limits=(0, 1024))
LCD4linux.MPBox1Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPBox1BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPBox2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPBox2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPBox2x1 = ConfigSlider(default=20, increment=1, limits=(0, 1024))
LCD4linux.MPBox2y1 = ConfigSlider(default=20, increment=1, limits=(0, 1024))
LCD4linux.MPBox2x2 = ConfigSlider(default=200, increment=1, limits=(0, 1024))
LCD4linux.MPBox2y2 = ConfigSlider(default=1, increment=1, limits=(0, 1024))
LCD4linux.MPBox2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.MPBox2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.MPRecording = ConfigSelection(choices=ScreenSelect, default="123456789")
LCD4linux.MPRecordingLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPRecordingType = ConfigSelection(choices=RecordType, default="1t")
LCD4linux.MPRecordingSize = ConfigSlider(default=25, increment=1, limits=(10, 200))
LCD4linux.MPRecordingPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.MPRecordingAlign = ConfigSelection(choices=AlignType, default="2")
LCD4linux.MPRecordingSplit = ConfigYesNo(default=False)
LCD4linux.MPBackground1 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.MPBackground1LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.MPBackground1Color = ConfigSelection(choices=Farbe, default="black")
LCD4linux.MPBackground1Bild = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.Standby = ConfigSelection(choices=[("0", _("off")), ("1", _("on"))], default="1")
LCD4linux.StandbyScreenMax = ConfigSelection(choices=ScreenUse, default="1")
LCD4linux.StandbyHelligkeit = ConfigSelectionNumber(0, 10, 1, default=1)
LCD4linux.StandbyHelligkeit2 = ConfigSelectionNumber(0, 10, 1, default=1)
LCD4linux.StandbyHelligkeit3 = ConfigSelectionNumber(0, 10, 1, default=1)
LCD4linux.StandbyNight = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.StandbyNight2 = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.StandbyNight3 = ConfigSelectionNumber(0, 10, 1, default=0)
LCD4linux.StandbyAutoOFF = ConfigSelection(choices=[("0", _("off"))] + TimeSelect, default="0")
LCD4linux.StandbyLCDoff = ConfigClock(default=int(begin))
LCD4linux.StandbyLCDon = ConfigClock(default=int(begin))
LCD4linux.StandbyLCDWEoff = ConfigClock(default=int(begin))
LCD4linux.StandbyLCDWEon = ConfigClock(default=int(begin))
LCD4linux.StandbyLCDBild1 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.StandbyLCDBild2 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.StandbyLCDBild3 = ConfigText(default="", fixed_size=False, visible_width=50)
LCD4linux.StandbyLCDColor1 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.StandbyLCDColor2 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.StandbyLCDColor3 = ConfigSelection(choices=Farbe, default="black")
LCD4linux.StandbyScreenTime = ConfigSelection(choices=[("0", _("off"))] + TimeSelect, default="0")
LCD4linux.StandbyScreenTime2 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.StandbyScreenTime3 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.StandbyScreenTime4 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.StandbyScreenTime5 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.StandbyScreenTime6 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.StandbyScreenTime7 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.StandbyScreenTime8 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.StandbyScreenTime9 = ConfigSelection(choices=TimeSelect, default="1")
LCD4linux.StandbyClock = ConfigSelection(choices=ScreenSelect, default="1")
LCD4linux.StandbyClockLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyClockType = ConfigSelection(choices=ClockType, default="12")
LCD4linux.StandbyClockSpacing = ConfigSelectionNumber(0, 3, 1, default=0)
LCD4linux.StandbyClockAnalog = ConfigSelection(choices=FoundClockDir, default=FoundClockDir[0])
LCD4linux.StandbyClockSize = ConfigSlider(default=110, increment=2, limits=(10, 400))
LCD4linux.StandbyClockPos = ConfigSlider(default=100, increment=2, limits=(0, 1024))
LCD4linux.StandbyClockAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.StandbyClockSplit = ConfigYesNo(default=False)
LCD4linux.StandbyClockColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyClockShadow = ConfigYesNo(default=False)
LCD4linux.StandbyClockFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyClock2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyClock2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyClock2Type = ConfigSelection(choices=ClockType, default="12")
LCD4linux.StandbyClock2Spacing = ConfigSelectionNumber(0, 3, 1, default=0)
LCD4linux.StandbyClock2Analog = ConfigSelection(choices=FoundClockDir, default=FoundClockDir[0])
LCD4linux.StandbyClock2Size = ConfigSlider(default=110, increment=2, limits=(10, 400))
LCD4linux.StandbyClock2Pos = ConfigSlider(default=100, increment=2, limits=(0, 1024))
LCD4linux.StandbyClock2Align = ConfigSelection(choices=AlignType, default="1")
LCD4linux.StandbyClock2Split = ConfigYesNo(default=False)
LCD4linux.StandbyClock2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyClock2Shadow = ConfigYesNo(default=False)
LCD4linux.StandbyClock2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyTimer = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyTimerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyTimerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.StandbyTimerLines = ConfigSelectionNumber(1, 20, 1, default=1)
LCD4linux.StandbyTimerType = ConfigSelection(choices=[("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.StandbyTimerType2 = ConfigSelection(choices=[("0", _("no total Timer")), ("1", _("show total Timer"))], default="1")
LCD4linux.StandbyTimerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyTimerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyTimerLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.StandbyTimerSplit = ConfigYesNo(default=False)
LCD4linux.StandbyTimerColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyTimerShadow = ConfigYesNo(default=False)
LCD4linux.StandbyTimerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyTuner = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyTunerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyTunerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.StandbyTunerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyTunerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyTunerSplit = ConfigYesNo(default=False)
LCD4linux.StandbyTunerType = ConfigSelection(choices=DirType + [("1", "%s x2" % _("horizontally"))], default="0")
LCD4linux.StandbyTunerActive = ConfigYesNo(default=False)
LCD4linux.StandbyTunerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyInfo = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyInfoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyInfoSensor = ConfigSelection(choices=InfoSensor, default="0")
LCD4linux.StandbyInfoCPU = ConfigSelection(choices=InfoCPU, default="0")
LCD4linux.StandbyInfoSize = ConfigSlider(default=20, increment=1, limits=(10, 150))
LCD4linux.StandbyInfoPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyInfoAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.StandbyInfoSplit = ConfigYesNo(default=False)
LCD4linux.StandbyInfoLines = ConfigSelectionNumber(1, 9, 1, default=1)
LCD4linux.StandbyInfoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyInfoShadow = ConfigYesNo(default=False)
LCD4linux.StandbyInfoFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyInfo2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyInfo2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyInfo2Sensor = ConfigSelection(choices=InfoSensor, default="0")
LCD4linux.StandbyInfo2CPU = ConfigSelection(choices=InfoCPU, default="0")
LCD4linux.StandbyInfo2Size = ConfigSlider(default=20, increment=1, limits=(10, 150))
LCD4linux.StandbyInfo2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyInfo2Align = ConfigSelection(choices=AlignType, default="1")
LCD4linux.StandbyInfo2Split = ConfigYesNo(default=False)
LCD4linux.StandbyInfo2Lines = ConfigSelectionNumber(1, 9, 1, default=1)
LCD4linux.StandbyInfo2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyInfo2Shadow = ConfigYesNo(default=False)
LCD4linux.StandbyInfo2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyPing = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyPingLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyPingSize = ConfigSlider(default=15, increment=2, limits=(10, 100))
LCD4linux.StandbyPingPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.StandbyPingAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyPingSplit = ConfigYesNo(default=False)
LCD4linux.StandbyPingColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyPingShadow = ConfigYesNo(default=False)
LCD4linux.StandbyPingFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyPingShow = ConfigSelection(choices=[("0", _("Online+Offline")), ("1", _("Online")), ("2", _("Offline"))], default="0")
LCD4linux.StandbyPingType = ConfigSelection(choices=DirType, default="0")
LCD4linux.StandbyPingTimeout = ConfigSlider(default=50, increment=5, limits=(5, 2000))
LCD4linux.StandbyPingName1 = ConfigText(default="Internet:www.google.de", fixed_size=False)
LCD4linux.StandbyPingName2 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyPingName3 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyPingName4 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyPingName5 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyExternalIp = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyExternalIpLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyExternalIpFile = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.StandbyExternalIpSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.StandbyExternalIpFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyExternalIpPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StandbyExternalIpAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyExternalIpSplit = ConfigYesNo(default=False)
LCD4linux.StandbyExternalIpShadow = ConfigYesNo(default=False)
LCD4linux.StandbyExternalIpColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyExternalIpBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyRBox = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyRBoxLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyRBoxSize = ConfigSlider(default=15, increment=2, limits=(6, 100))
LCD4linux.StandbyRBoxPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.StandbyRBoxAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyRBoxProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.StandbyRBoxColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyRBoxColor2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyRBoxColor3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyRBoxColor4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyRBoxColor5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyRBoxShadow = ConfigYesNo(default=False)
LCD4linux.StandbyRBoxFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyRBoxShow = ConfigSelection(choices=RBoxType, default="PCT")
LCD4linux.StandbyRBoxTimer = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyRBoxTimerLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyRBoxTimerSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.StandbyRBoxTimerLines = ConfigSelectionNumber(1, 20, 1, default=1)
LCD4linux.StandbyRBoxTimerType = ConfigSelection(choices=[("0", _("use lead-time")), ("1", _("only use Timer"))], default="0")
LCD4linux.StandbyRBoxTimerType2 = ConfigSelection(choices=[("0", _("no total Timer")), ("1", _("show total Timer"))], default="1")
LCD4linux.StandbyRBoxTimerPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyRBoxTimerAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyRBoxTimerLen = ConfigSelection(choices=ProzentType, default="100")
LCD4linux.StandbyRBoxTimerSplit = ConfigYesNo(default=False)
LCD4linux.StandbyRBoxTimerColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyRBoxTimerShadow = ConfigYesNo(default=False)
LCD4linux.StandbyRBoxTimerFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyDev = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyDevLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyDevSize = ConfigSlider(default=15, increment=2, limits=(10, 300))
LCD4linux.StandbyDevPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.StandbyDevAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyDevSplit = ConfigYesNo(default=False)
LCD4linux.StandbyDevColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyDevShadow = ConfigYesNo(default=False)
LCD4linux.StandbyDevFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyDevType = ConfigSelection(choices=DirType, default="0")
LCD4linux.StandbyDevWarning = ConfigSelection(choices=WarningType, default="10")
LCD4linux.StandbyDevExtra = ConfigSelection(choices=[("0", _("no")), ("RAM", _("Memory free")), ("RAM2", _("Memory available"))], default="RAM2")
LCD4linux.StandbyDevName1 = ConfigText(default="/media/hdd", fixed_size=False)
LCD4linux.StandbyDevName2 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyDevName3 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyDevName4 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyDevName5 = ConfigText(default="", fixed_size=False)
LCD4linux.StandbyHdd = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyHddLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyHddSize = ConfigSlider(default=32, increment=1, limits=(10, 150))
LCD4linux.StandbyHddPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StandbyHddAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.StandbyHddSplit = ConfigYesNo(default=False)
LCD4linux.StandbyHddType = ConfigSelection(choices=HddType, default="0")
LCD4linux.StandbyWetter = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyWetterLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyWetterPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.StandbyWetterAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyWetterSplit = ConfigYesNo(default=False)
LCD4linux.StandbyWetterZoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.StandbyWetterType = ConfigSelection(choices=WetterType, default="1")
LCD4linux.StandbyWetterColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyWetterShadow = ConfigYesNo(default=False)
LCD4linux.StandbyWetterFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyWetter2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyWetter2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyWetter2Pos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.StandbyWetter2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyWetter2Split = ConfigYesNo(default=False)
LCD4linux.StandbyWetter2Zoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.StandbyWetter2Type = ConfigSelection(choices=WetterType, default="1")
LCD4linux.StandbyWetter2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyWetter2Shadow = ConfigYesNo(default=False)
LCD4linux.StandbyWetter2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyMeteo = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyMeteoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyMeteoPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.StandbyMeteoAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyMeteoSplit = ConfigYesNo(default=False)
LCD4linux.StandbyMeteoZoom = ConfigSlider(default=10, increment=1, limits=(7, 60))
LCD4linux.StandbyMeteoType = ConfigSelection(choices=MeteoType, default="1")
LCD4linux.StandbyMeteoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyMoon = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyMoonLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyMoonSize = ConfigSlider(default=60, increment=2, limits=(10, 300))
LCD4linux.StandbyMoonFontSize = ConfigSlider(default=30, increment=1, limits=(8, 100))
LCD4linux.StandbyMoonPos = ConfigSlider(default=10, increment=2, limits=(0, 1024))
LCD4linux.StandbyMoonAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyMoonInfos = ConfigSelection(choices=MoonInfoSelect, default="111")
LCD4linux.StandbyMoonTrends = ConfigYesNo(default=True)
LCD4linux.StandbyMoonSplit = ConfigYesNo(default=False)
LCD4linux.StandbyMoonColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="white")
LCD4linux.StandbyMoonShadow = ConfigYesNo(default=False)
LCD4linux.StandbyMoonFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyNetAtmo = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyNetAtmoLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyNetAtmoPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.StandbyNetAtmoAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyNetAtmoSplit = ConfigYesNo(default=False)
LCD4linux.StandbyNetAtmoStation = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.StandbyNetAtmoModule = ConfigSelection(choices=NetatmoSelect, default="123456")
LCD4linux.StandbyNetAtmoModuleUser = ConfigText(default="123456", fixed_size=False)
LCD4linux.StandbyNetAtmoName = ConfigYesNo(default=True)
LCD4linux.StandbyNetAtmoBasis = ConfigYesNo(default=True)
LCD4linux.StandbyNetAtmoType = ConfigSelection(choices=NetatmoType, default="THCPN")
LCD4linux.StandbyNetAtmoType2 = ConfigSelection(choices=DirType, default="0")
LCD4linux.StandbyNetAtmoSize = ConfigSlider(default=30, increment=1, limits=(10, 100))
LCD4linux.StandbyNetAtmoColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyNetAtmoColor2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmoColor3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmoColor4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmoColor5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmoColor6 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmoColor7 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmoShadow = ConfigYesNo(default=False)
LCD4linux.StandbyNetAtmoFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyNetAtmo2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyNetAtmo2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyNetAtmo2Pos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.StandbyNetAtmo2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyNetAtmo2Split = ConfigYesNo(default=False)
LCD4linux.StandbyNetAtmo2Station = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.StandbyNetAtmo2Module = ConfigSelection(choices=NetatmoSelect, default="123456")
LCD4linux.StandbyNetAtmo2ModuleUser = ConfigText(default="123456", fixed_size=False)
LCD4linux.StandbyNetAtmo2Name = ConfigYesNo(default=True)
LCD4linux.StandbyNetAtmo2Basis = ConfigYesNo(default=True)
LCD4linux.StandbyNetAtmo2Type = ConfigSelection(choices=NetatmoType, default="THCPN")
LCD4linux.StandbyNetAtmo2Type2 = ConfigSelection(choices=DirType, default="0")
LCD4linux.StandbyNetAtmo2Size = ConfigSlider(default=30, increment=1, limits=(10, 100))
LCD4linux.StandbyNetAtmo2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyNetAtmo2Color2 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmo2Color3 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmo2Color4 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmo2Color5 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmo2Color6 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmo2Color7 = ConfigSelection(choices=OffFarbe, default="0")
LCD4linux.StandbyNetAtmo2Shadow = ConfigYesNo(default=False)
LCD4linux.StandbyNetAtmo2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyNetAtmoCO2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyNetAtmoCO2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyNetAtmoCO2Size = ConfigSlider(default=30, increment=1, limits=(5, 500))
LCD4linux.StandbyNetAtmoCO2Len = ConfigSlider(default=200, increment=5, limits=(100, 1024))
LCD4linux.StandbyNetAtmoCO2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyNetAtmoCO2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyNetAtmoCO2Split = ConfigYesNo(default=False)
LCD4linux.StandbyNetAtmoCO2Station = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.StandbyNetAtmoCO2Type = ConfigSelection(choices=CO2Type, default="1")
LCD4linux.StandbyNetAtmoIDX = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyNetAtmoIDXLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyNetAtmoIDXSize = ConfigSlider(default=30, increment=1, limits=(5, 500))
LCD4linux.StandbyNetAtmoIDXLen = ConfigSlider(default=200, increment=5, limits=(100, 1024))
LCD4linux.StandbyNetAtmoIDXPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyNetAtmoIDXAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyNetAtmoIDXSplit = ConfigYesNo(default=False)
LCD4linux.StandbyNetAtmoIDXStation = ConfigSelectionNumber(1, 5, 1, default=1)
LCD4linux.StandbyNetAtmoIDXType = ConfigSelection(choices=CO2Type, default="1")
LCD4linux.StandbyOSCAM = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyOSCAMLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyOSCAMSize = ConfigSlider(default=10, increment=1, limits=(9, 50))
LCD4linux.StandbyOSCAMPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.StandbyOSCAMAlign = ConfigSelection(choices=[("0", _("left")), ("2", _("right"))], default="0")
LCD4linux.StandbyOSCAMSplit = ConfigYesNo(default=False)
LCD4linux.StandbyOSCAMColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyOSCAMBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="black")
LCD4linux.StandbyString = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyStringLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyStringText = ConfigText(default="Hello", fixed_size=False, visible_width=50)
LCD4linux.StandbyStringSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.StandbyStringFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyStringPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StandbyStringAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyStringSplit = ConfigYesNo(default=False)
LCD4linux.StandbyStringShadow = ConfigYesNo(default=False)
LCD4linux.StandbyStringColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyStringBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyString2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyString2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyString2Text = ConfigText(default="Hello", fixed_size=False, visible_width=50)
LCD4linux.StandbyString2Size = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.StandbyString2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyString2Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StandbyString2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyString2Split = ConfigYesNo(default=False)
LCD4linux.StandbyString2Shadow = ConfigYesNo(default=False)
LCD4linux.StandbyString2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyString2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyText = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyTextLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyTextFile = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.StandbyTextSize = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.StandbyTextFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyTextAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyTextPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StandbyTextShadow = ConfigYesNo(default=False)
LCD4linux.StandbyTextColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyTextBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyText2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyText2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyText2File = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.StandbyText2Size = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.StandbyText2Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyText2Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyText2Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StandbyText2Shadow = ConfigYesNo(default=False)
LCD4linux.StandbyText2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyText2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyText3 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyText3LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyText3File = ConfigText(default=LCD4text, fixed_size=False, visible_width=50)
LCD4linux.StandbyText3Size = ConfigSlider(default=32, increment=1, limits=(10, 300))
LCD4linux.StandbyText3Font = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyText3Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyText3Pos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StandbyText3Shadow = ConfigYesNo(default=False)
LCD4linux.StandbyText3Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyText3BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyHTTP = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyHTTPLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyHTTPURL = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.StandbyHTTPSize = ConfigSlider(default=20, increment=1, limits=(10, 300))
LCD4linux.StandbyHTTPPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyHTTPAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyHTTPColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyHTTPBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyHTTPShadow = ConfigYesNo(default=False)
LCD4linux.StandbyHTTPFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyWWW1 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyWWW1LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyWWW1Size = ConfigSlider(default=200, increment=1, limits=(50, 1024))
LCD4linux.StandbyWWW1Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyWWW1Align = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyWWW1url = ConfigText(default="http://", fixed_size=False, visible_width=50)
LCD4linux.StandbyWWW1w = ConfigSlider(default=800, increment=50, limits=(600, 2000))
LCD4linux.StandbyWWW1h = ConfigSlider(default=600, increment=50, limits=(100, 2000))
LCD4linux.StandbyWWW1CutX = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyWWW1CutY = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyWWW1CutW = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyWWW1CutH = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyBild = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyBildLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyBildFile = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.StandbyBildSize = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.StandbyBildSizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.StandbyBildPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyBildAlign = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.StandbyBildQuick = ConfigYesNo(default=False)
LCD4linux.StandbyBildTransp = ConfigYesNo(default=False)
LCD4linux.StandbyBild2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyBild2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyBild2File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.StandbyBild2Size = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.StandbyBild2SizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.StandbyBild2Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyBild2Align = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.StandbyBild2Quick = ConfigYesNo(default=False)
LCD4linux.StandbyBild2Transp = ConfigYesNo(default=False)
LCD4linux.StandbyBild3 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyBild3LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyBild3File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.StandbyBild3Size = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.StandbyBild3SizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.StandbyBild3Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyBild3Align = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.StandbyBild3Quick = ConfigYesNo(default=False)
LCD4linux.StandbyBild3Transp = ConfigYesNo(default=False)
LCD4linux.StandbyBild4 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyBild4LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyBild4File = ConfigText(default="/tmp/lcd4linux.jpg", fixed_size=False, visible_width=50)
LCD4linux.StandbyBild4Size = ConfigSlider(default=240, increment=10, limits=(10, 1024))
LCD4linux.StandbyBild4SizeH = ConfigSlider(default=0, increment=10, limits=(0, 800))
LCD4linux.StandbyBild4Pos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyBild4Align = ConfigSelection(choices=AlignType + [("9", _("full Screen"))], default="0")
LCD4linux.StandbyBild4Quick = ConfigYesNo(default=False)
LCD4linux.StandbyBild4Transp = ConfigYesNo(default=False)
LCD4linux.StandbyMail = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyMailLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyMailSize = ConfigSlider(default=12, increment=1, limits=(5, 150))
LCD4linux.StandbyMailPos = ConfigSlider(default=30, increment=2, limits=(0, 1024))
LCD4linux.StandbyMailAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyMailSplit = ConfigYesNo(default=False)
LCD4linux.StandbyMailColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyMailBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyMailKonto = ConfigSelection(choices=MailKonto, default="1")
LCD4linux.StandbyMailLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.StandbyMailType = ConfigSelection(choices=MailType, default="A1")
LCD4linux.StandbyMailProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.StandbyMailShadow = ConfigYesNo(default=False)
LCD4linux.StandbyMailFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyIconBar = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyIconBarLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyIconBarSize = ConfigSlider(default=20, increment=1, limits=(10, 150))
LCD4linux.StandbyIconBarPos = ConfigSlider(default=120, increment=2, limits=(0, 1024))
LCD4linux.StandbyIconBarAlign = ConfigSelection(choices=AlignType, default="1")
LCD4linux.StandbyIconBarSplit = ConfigYesNo(default=False)
LCD4linux.StandbyIconBarType = ConfigSelection(choices=DirType, default="0")
LCD4linux.StandbyIconBarPopup = ConfigSelection(choices=[("0", _("off"))] + ScreenSet, default="0")
LCD4linux.StandbyIconBarPopupLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbySun = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbySunLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbySunSize = ConfigSlider(default=20, increment=1, limits=(5, 150))
LCD4linux.StandbySunPos = ConfigSlider(default=20, increment=2, limits=(0, 1024))
LCD4linux.StandbySunAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbySunSplit = ConfigYesNo(default=False)
LCD4linux.StandbySunColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbySunBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbySunShadow = ConfigYesNo(default=False)
LCD4linux.StandbySunFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbySunType = ConfigSelection(choices=DirType, default="2")
LCD4linux.StandbyFritz = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyFritzLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyFritzSize = ConfigSlider(default=22, increment=1, limits=(10, 150))
LCD4linux.StandbyFritzPos = ConfigSlider(default=130, increment=2, limits=(0, 1024))
LCD4linux.StandbyFritzAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyFritzColor = ConfigSelection(choices=Farbe, default="yellow")
LCD4linux.StandbyFritzBackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyFritzType = ConfigSelection(choices=FritzType, default="TL")
LCD4linux.StandbyFritzPicSize = ConfigSlider(default=100, increment=1, limits=(10, 800))
LCD4linux.StandbyFritzPicPos = ConfigSlider(default=30, increment=2, limits=(0, 1024))
LCD4linux.StandbyFritzPicAlign = ConfigSlider(default=0, increment=10, limits=(0, 1024))
LCD4linux.StandbyFritzShadow = ConfigYesNo(default=False)
LCD4linux.StandbyFritzFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyCal = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyCalLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyCalPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.StandbyCalAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyCalSplit = ConfigYesNo(default=False)
LCD4linux.StandbyCalZoom = ConfigSlider(default=10, increment=1, limits=(3, 50))
LCD4linux.StandbyCalType = ConfigSelection(choices=CalType, default="0A")
LCD4linux.StandbyCalTypeE = ConfigSelection(choices=CalTypeE, default="D2")
LCD4linux.StandbyCalLayout = ConfigSelection(choices=CalLayout, default="0")
LCD4linux.StandbyCalColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyCalBackColor = ConfigSelection(choices=Farbe, default="gray")
LCD4linux.StandbyCalCaptionColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyCalShadow = ConfigYesNo(default=False)
LCD4linux.StandbyCalFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyCalList = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyCalListLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyCalListSize = ConfigSlider(default=12, increment=1, limits=(5, 150))
LCD4linux.StandbyCalListPos = ConfigSlider(default=50, increment=2, limits=(0, 1024))
LCD4linux.StandbyCalListAlign = ConfigSelection(choices=AlignType, default="0")
LCD4linux.StandbyCalListSplit = ConfigYesNo(default=False)
LCD4linux.StandbyCalListLines = ConfigSelectionNumber(1, 20, 1, default=3)
LCD4linux.StandbyCalListProzent = ConfigSelection(choices=ProzentType, default="50")
LCD4linux.StandbyCalListType = ConfigSelection(choices=CalListType, default="C")
LCD4linux.StandbyCalListColor = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyCalListShadow = ConfigYesNo(default=False)
LCD4linux.StandbyCalListFont = ConfigSelection(choices=FontType, default="0")
LCD4linux.StandbyBox1 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyBox1LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyBox1x1 = ConfigSlider(default=10, increment=1, limits=(0, 1024))
LCD4linux.StandbyBox1y1 = ConfigSlider(default=10, increment=1, limits=(0, 1024))
LCD4linux.StandbyBox1x2 = ConfigSlider(default=200, increment=1, limits=(0, 1024))
LCD4linux.StandbyBox1y2 = ConfigSlider(default=1, increment=1, limits=(0, 1024))
LCD4linux.StandbyBox1Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyBox1BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyBox2 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyBox2LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyBox2x1 = ConfigSlider(default=20, increment=1, limits=(0, 1024))
LCD4linux.StandbyBox2y1 = ConfigSlider(default=20, increment=1, limits=(0, 1024))
LCD4linux.StandbyBox2x2 = ConfigSlider(default=200, increment=1, limits=(0, 1024))
LCD4linux.StandbyBox2y2 = ConfigSlider(default=1, increment=1, limits=(0, 1024))
LCD4linux.StandbyBox2Color = ConfigSelection(choices=Farbe, default="white")
LCD4linux.StandbyBox2BackColor = ConfigSelection(choices=[("0", _("off"))] + Farbe, default="0")
LCD4linux.StandbyRecording = ConfigSelection(choices=ScreenSelect, default="123456789")
LCD4linux.StandbyRecordingLCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyRecordingType = ConfigSelection(choices=RecordType, default="1t")
LCD4linux.StandbyRecordingSize = ConfigSlider(default=25, increment=1, limits=(10, 200))
LCD4linux.StandbyRecordingPos = ConfigSlider(default=0, increment=2, limits=(0, 1024))
LCD4linux.StandbyRecordingAlign = ConfigSelection(choices=AlignType, default="2")
LCD4linux.StandbyRecordingSplit = ConfigYesNo(default=False)
LCD4linux.StandbyBackground1 = ConfigSelection(choices=ScreenSelect, default="0")
LCD4linux.StandbyBackground1LCD = ConfigSelection(choices=LCDSelect, default="1")
LCD4linux.StandbyBackground1Color = ConfigSelection(choices=Farbe, default="black")
LCD4linux.StandbyBackground1Bild = ConfigText(default="", fixed_size=False, visible_width=50)


class MyTimer:  # only for debug

	def __init__(self):
		print("L4L create timer at:")
		print_stack(limit=2)
		self.timer = eTimer()
		print("L4L created timer", self.timer)

	def __del__(self):
		print("L4L destruct timer", self.timer)
		print_stack(limit=2)
		del self.timer

	def start(self, msecs, singleShot=False):
		print("L4L start timer", msecs, singleShot, self.timer)
		print_stack(limit=2)
		self.timer.start(msecs, singleShot)

	def startLongTimer(self, secs):
		print("L4L start longtimer", secs, self.timer)
		print_stack(limit=2)
		self.timer.startLongTimer(secs)

	def stop(self):
		print("L4L stopped timer", self.timer)
		print_stack(limit=2)
		self.timer.stop()

	def getCallback(self):
		return self.timer.callback
	callback = property(getCallback)


def getFsize(text, f):
	m1, m2 = f.getmetrics()
	(w1, h1), (o1, o2) = f.font.getsize(text)
	h1 = m1 + m2
	h = h1 + int(round(h1 / 33.))
	return w1, h


def Code_utf8(wert):
	wert = "" if wert is None else _unescape(wert)
	return wert.replace('\x86', '').replace('\x87', '') if PY3 else wert.replace('\xc2\x86', '').replace('\xc2\x87', '').decode("utf-8", "ignore")


def L4log(nfo, wert=""):
	if str(LCD4linux.EnableEventLog.value) != "0":
		print("[LCD4linux] %s %s" % (nfo, wert))
		if str(LCD4linux.EnableEventLog.value) != "3":
			try:
				with open("/tmp/L4log.txt", "a") as f:
					f.write("%s %s %s\r\n" % (strftime("%H:%M:%S"), nfo, wert))
			except IOError:
				print("[LCD4linux] %s Logging-Error" % strftime("%H:%M:%S"))


def L4logE(nfo, wert=""):
	if str(LCD4linux.EnableEventLog.value) == "2":
		L4log(nfo, wert)


def GetBox():
	B = ""
	if exists("/proc/stb/info/model"):
		with open("/proc/stb/info/model") as f:
			B = f.readline()
		L4logE("Boxtype", B)
	return B


def getMJPEGrun(lcd):
	return MJPEGrun[lcd]


def setConfigMode(w):
	global ConfigMode
	ConfigMode = w


def setConfigStandby(w):
	global ConfigStandby
	ConfigStandby = w


def setisMediaPlayer(w):
	global isMediaPlayer
	isMediaPlayer = w


def setScreenActive(w, lcd=""):
	global ScreenActive
	global ScreenTime
	if lcd == "":
		if w == "0":
			ScreenActive[-3:] = ["", "", ""]
			L4LElist.setHold(False)
		else:
			ScreenActive[0] = w
	else:
		if w == "0":
			w = ""
		ScreenActive[int(lcd)] = w
	LCD4linux.ScreenActive.value = ScreenActive[0]
	ScreenTime = 0


def setLCDon(w):
	global LCDon
	LCDon = w


def setSaveEventListChanged(w):
	global SaveEventListChanged
	SaveEventListChanged = w


def setFONT(f):
	global FONT
	FONT = f if f.endswith(".ttf") and isfile(f) else FONTdefault
	LCD4linux.Font.value = FONT


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


def getMJPEGreader(w):
	return MJPEGreader[int(w)]


def setPopText(w):
	global PopText
	PopText[0] = "%s%s" % (Code_utf8(_(strftime("%A"))), strftime(" %H:%M"))
	PopText[1] = Code_utf8(w)


def resetWetter(wetter):
	global wwwWetter
	global PICwetter
	wwwWetter = ["", ""]
	PICwetter = [None, None]


def resetCal():
	global PICcal
	PICcal = None


def L4LoadNewConfig(cfg):
	P1 = LCD4linux.ConfigPath.value
	P2 = LCD4linux.PiconPath.value
	P3 = LCD4linux.PiconPathAlt.value
	P4 = LCD4linux.PiconCache.value
	P5 = LCD4linux.WetterPath.value
	if isfile(LCD4default):
		LCD4linux.loadFromFile(LCD4default)
	L4log("Config-Load", cfg)
	if MODEL == 'vuduo2':  # due to 2 displays, LCD4linux is integrated in this boximage
		LCD4linux.loadFromFile("%sdefault.vuduo2" % LCD4data)
	L4log("Config-Load for 'Vu+ duo²'", cfg)
	LCD4linux.loadFromFile(cfg)
	LCD4linux.load()
	if LCD4linux.ConfigWriteAll.value == False:
		LCD4linux.ConfigPath.value = P1
		LCD4linux.PiconPath.value = P2
		LCD4linux.PiconPathAlt.value = P3
		LCD4linux.PiconCache.value = P4
		LCD4linux.WetterPath.value = P5


def getSA(w):
	if w < 0 or w > 3:
		return ScreenActive[0]
	return ScreenActive[0] if ScreenActive[w] == "" else ScreenActive[w]


def rmFile(fn):
	if isfile(fn):
		try:
			L4logE("delete", fn)
			remove(fn)
		except Exception:
			L4logE("Error delete", fn)


def rmFiles(fn):
	try:
		fl = glob(fn)
		L4logE("delete*", fn)
		for f in fl:
			remove(f)
	except Exception:
		L4logE("Error delete*", fn)


def getTimeDiff():
	offset = timezone if (localtime().tm_isdst == 0) else altzone
	return offset / -3600


def getTimeDiffUTC():
	t = datetime.now() - datetime.utcnow()
	return int(t.days * 24 + round(t.seconds / 3600.0))


def getTimeDiffUTC2():
	is_dst = daylight and localtime().tm_isdst > 0
	return -((altzone if is_dst else timezone) / 3600)


def ConfTime(F, W):
	try:
		if exists(LCD4config) and W != [6, 0]:
			if open(LCD4config, "r").read().find("config.%s=%d:%d\n" % (F, W[0], W[1])) == -1:
				L4log("write alternate TimeConfig " + F, W)
				with open(LCD4config, "a") as f:
					f.write("config.%s=%d:%d\n" % (F, W[0], W[1]))
	except Exception:
		L4log("Errot: write alternate TimeConfig " + F, W)


def ConfTimeCheck():
	ConfTime("LCDoff", LCD4linux.LCDoff.value)
	ConfTime("LCDon", LCD4linux.LCDon.value)
	ConfTime("StandbyLCDoff", LCD4linux.StandbyLCDoff.value)
	ConfTime("StandbyLCDon", LCD4linux.StandbyLCDon.value)
	ConfTime("LCDWEoff", LCD4linux.LCDWEoff.value)
	ConfTime("LCDWEon", LCD4linux.LCDWEon.value)
	ConfTime("StandbyLCDWEoff", LCD4linux.StandbyLCDWEoff.value)
	ConfTime("StandbyLCDWEon", LCD4linux.StandbyLCDWEon.value)


def ScaleGtoR(PROZ):
	if PROZ < 50:
		R = max((255 * PROZ) / 50, 0)
		G = 255
	else:
		R = 255
		G = max((255 * (100 - PROZ)) / 50, 0)
	B = 0
	return "#%02x%02x%02x" % (R, G, B)


def getDirection(angle):
	def normalize_angle(angle):
		cycles = angle / 360.
		normalized_cycles = cycles - floor(cycles)
		return normalized_cycles * 360.
	direction_names = [_("N"), _("NNE"), _("NE"), _("ENE"), _("E"), _("ESE"), _("SE"), _("SSE"), _("S"), _("SSW"), _("SW"), _("WSW"), _("W"), _("WNW"), _("NW"), _("NNW")]
	directions_num = len(direction_names)
	directions_step = 360. / directions_num
	index = int(round(normalize_angle(angle) / directions_step))
	index %= directions_num
	return direction_names[index]


def getFeel(T, W):
	return 13.12 + 0.6215 * T - 11.37 * (W**0.16) + 0.3965 * T * (W**0.16)


def getExternalIP():
	try:
		req = Request(LCD4linux.ExternalIpUrl.value, data=None)
		response = urlopen(req, timeout=5)
		return response.read()
	except Exception:
		L4logE("Error: getExternalIP", format_exc())
		return "Error"


def setFB2(value):
	open("/proc/stb/fb/sd_detach", "w").write(value)


def getFB2(check):
	return isfile("/proc/stb/fb/sd_detach") and (LCD4linux.SwitchToFB2.value == True) if check else isfile("/proc/stb/fb/sd_detach")


def BRI(w1, w2):
	gb = L4LElist.getBrightness(w2, False)
	return w1 if gb == -1 else gb


def virtBRI(LCD):
	global AktNight
	vb = BRI(L4LElist.getBrightness(LCD), LCD)
	if vb < 1:
		return 0
	elif vb == 10:
		return 10
	else:
		return ((0.08 * vb) + 0.2)


def SensorRead(dat, isTemp=False):
	T = 0
	if isfile(dat) == True:
		lines = ""
		i = 0
		with open(dat) as f:
			L4log("Sensor-Wait")
			while i < 10:
				i += 1
				sleep(0.01)
				curr = f.readline().strip()
				if len(curr) > 0:
					lines += "%s\n" % curr
				else:
					break
		if lines.find("temperature") >= 0:
			lines = lines[lines.find("temperature"):]
		hisitemp = findall(r"temperature\s*=\s*(\d+)", lines)
		T = float(hisitemp[0]) if hisitemp else float("0" + sub(r"[^0-9^.]", "", lines))
		if isTemp and T > 1000.:
			T /= 1000.
	return round(T)


def GetTempSensor():
	d = []
	d += glob("/proc/stb/sensors/temp*/value")  # e.g. Dreambox
	d += glob("/sys/class/thermal/thermal_zone0/temp")  # e.g. GigaBlue UE4K
	d += glob("/proc/hisi/msp/pm_cpu")  # e.g. Octagon SF8008
	d += glob("/proc/stb/fp/temp_sensor")  # e.g. ZGemma H9Twin
	d += glob("/proc/stb/sensors/temp/value")  # unverified, unknown Boxes
	d += glob("/proc/stb/fp/temp_sensor_avs")  # unverified, unknown Boxes
	d += glob("/proc/stb/power/avs")  # unverified, unknown Boxes
	L4logE("looking for Temp", str(d))
	for ts in d:
		try:
			Temp = SensorRead(ts, True)
			usable = float(Temp) > 10.0 and float(Temp) < 100.0
			L4logE("found Temp: '" + ts + "', raw data: '" + str(Temp) + "', ", "usable: " + str(usable))
			if usable:
				return ts
		except Exception:
			L4logE("Error Temp: ", ts)
	return ""


def ICSdownloads():
	global ICS
	global ICSlist
	global ICSdownrun
	global PICcal

	L4logE("ICSdownloads... %s" % len(ICSlist))
	if (len(ICSlist) == 0 and LCD4linux.CalPlanerFS.value == False) or ICSdownrun == True:
		PICcal = None
		return
	ICSdownrun = True
	ICS.clear()
	if LCD4linux.CalPlanerFS.value == True:
		try:
			from Plugins.Extensions.PlanerFS.PFSl4l import l4l_export
			liste = l4l_export().planerfs_liste
			PlanerFSok = True
			L4logE("PlanerFS registered")
		except Exception:
			liste = []
			PlanerFSok = False
			L4logE("PlanerFS not registered")
		if PlanerFSok == True:
			for Icomp in liste:
				DT = Icomp[0]
				L4logE(Icomp)
				D = "%04d-%02d-%02d" % (DT.year, DT.month, DT.day)
				if Icomp[4] == (0, 0):
					dateT = date(DT.year, DT.month, DT.day)
				else:
					DT = DT - timedelta(hours=getTimeDiffUTC())
					dateT = vDatetime.from_ical("%04d%02d%02dT%02d%02d00Z" % (DT.year, DT.month, DT.day, DT.hour, DT.minute))
				if Icomp[6] == 0:
					dateS = Code_utf8(Icomp[1])
				else:
					dateS = "%s (%d)" % (Code_utf8(Icomp[1]), Icomp[6])
				inew = [dateS, dateT, 4]
				Doppel = False
				if ICS.get(D, None) is None:
					ICS[D] = []
				else:
					for ii in ICS[D]:
						if ii[:2] == inew[:2]:
							Doppel = True
							L4logE("ICS ignore %s" % inew)
				if Doppel == False:
					ICS[D].append(inew)
					L4logE("%s%s" % (D, inew))
	for name in ICSlist:
		L4log("ICS read Col", name[1])
		try:
			gcal = iCalendar().from_ical(name[0])
			L4log("use iCal 3.x")
		except Exception:
			from traceback import format_exc
			L4log("Error: ICS not readable!", format_exc())
			continue
		try:
			for Icomp in gcal.walk("VEVENT"):
				if Icomp.name == "VEVENT":
					rrule = str(Icomp.get("rrule", ""))
					L4logE("%s - %s - %s" % (Icomp["dtstart"], Icomp.get('summary'), rrule))
					if "UNTIL" in rrule or "INTERVAL" in rrule:
						y = {}
						for b in rrule.split(";"):
							if len(b.split("=")) > 1:
								y[b.split("=")[0]] = b.split("=")[1]
						if y.get("UNTIL", "") != "" and y.get("UNTIL", "999999999") < "%4d%02d%02d" % (datetime.now().year, datetime.now().month, datetime.now().day):
							L4logE("Until-Rule ignore", rrule)
							continue
						if int(y.get("INTERVAL", "1")) > 1:
							L4logE("Interval-Rule ignore", rrule)
							continue
					if "YEARLY" in rrule:
						dt = str(Icomp.decoded("dtstart"))
						Year = (datetime.now().year + 1) if int(dt[5:7]) < datetime.now().month else datetime.now().year
						Icomp.add('dtstart', date(Year, int(dt[5:7]), int(dt[8:10])))
					today = date.today()
					WEEKLY = []
					if "WEEKLY" in rrule:
						for i in range(1, 5):
							WEEKLY.append(Icomp.decoded("dtstart") + timedelta(i * 7))
					nextmonth = today + timedelta(mdays[today.month])  # 2012-01-23
					nextmonth2 = today + timedelta(mdays[today.month] - 3)  # save Month+1 if days to long
					DTstart = str(Icomp.decoded("dtstart"))
					if strftime("%Y-%m") == DTstart[:7] or nextmonth.strftime("%Y-%m") == DTstart[:7] or nextmonth2.strftime("%Y-%m") == DTstart[:7]:
						D = DTstart[:10]
						inew = [Code_utf8(Icomp.get('summary')), Icomp.decoded("dtstart"), name[1]]
						Doppel = False
						if ICS.get(D, None) is None:
							ICS[D] = []
						else:
							for ii in ICS[D]:
								if ii[:2] == inew[:2]:
									Doppel = True
									L4log("ICS ignore %s" % inew)
						if Doppel == False:
							ICS[D].append(inew)
							L4log("%s%s" % (D, inew))
							for w in WEEKLY:
								D = str(w)[:10]
								if ICS.get(D, None) is None:
									ICS[D] = []
								ICS[D].append([inew[0], w, inew[2]])
								L4log("weekly", w)
		except Exception:
			from traceback import format_exc
			L4log("Error ICS", name)
			L4log("Error:", format_exc())
			try:
				open(CrashFile, "w").write(format_exc())
			except Exception:
				pass
	ICSlist = []
	L4logE("ICS laenge %s" % len(ICS))
	ICSdownrun = False
	PICcal = None


def getResolution(t, r):
	MAX_H, MAX_W = (0, 0)
	if t.startswith("5"):
		ttt = LCD4linux.xmlLCDType.value.split("x")
		MAX_W, MAX_H = int(ttt[0]), int(ttt[1])
		if int(LCD4linux.xmlOffset.value) != 0:
			MAX_W -= (int(LCD4linux.xmlOffset.value) * 2)
			MAX_H -= (int(LCD4linux.xmlOffset.value) * 2)
	elif t[1:] == "1":
		MAX_W, MAX_H = 320, 240
	elif t[1:] == "2":
		MAX_W, MAX_H = 240, 320
	elif t[1:] in ["3", "4", "5", "10", "15"]:
		MAX_W, MAX_H = 800, 480
	elif t[1:] in ["6", "9", "11", "12"]:
		MAX_W, MAX_H = 800, 600
	elif t[1:] in ["7", "8", "13", "14"]:
		MAX_W, MAX_H = 1024, 600
	elif t[1:] == "17":
		MAX_W, MAX_H = 220, 176
	elif t[1:] == "18":
		MAX_W, MAX_H = 255, 64
	elif t[1:] == "22":
		MAX_W, MAX_H = 480, 320
	elif t[1:] == "23":
		MAX_W, MAX_H = 800, 480
	elif t[1:] == "30":
		MAX_W, MAX_H = 400, 240
	elif t == "320":
		MAX_W, MAX_H = LCD4linux.SizeW.value, LCD4linux.SizeH.value
	elif t == "420":
		MAX_W, MAX_H = LCD4linux.SizeW2.value, LCD4linux.SizeH2.value
	elif t[1:] == "21":
		MAX_W, MAX_H = 128, 128
	else:
		MAX_W, MAX_H = 132, 64
	if r in ["90", "270"]:
		MAX_W, MAX_H = MAX_H, MAX_W
	return MAX_W, MAX_H


def OSDclose():
	global OSDon
	OSDon = 0
	L4log("Screen close")
	rmFile("%sdpfgrab.jpg" % TMPL)
	if getFB2(False):
		setFB2("1")


def Umlaute(wert):
	return wert.replace("Ä", "A").replace("ä", "a").replace("Ö", "O").replace("ö", "o").replace("Ü", "u").replace("ü", "u").replace("ß", "ss")


def L4L_replacement_Screen_show(self):
	global OSDon
	global OSDtimer
	if str(LCD4linux.OSD.value) != "0":
		L4log("Skin", self.skinName)
		doSkinOpen = True
		if len(self.skinName[0]) > 1:
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
				if ib not in OSDdontshow:
					L4log("Open Screen:" + str(ib), "Skin:" + str(self.skinName))
					OSDon = 3
					if getFB2(True):
						setFB2("0")
					self.onClose.append(OSDclose)
				else:
					if OSDon != 1:
						OSDon = 0
						if getFB2(False):
							setFB2("1")
			else:
				L4log("Open Screen no Title, Skin:", self.skinName)
				OSDon = 3
				if getFB2(True):
					setFB2("0")
				self.onClose.append(OSDclose)
		else:
			if OSDon != 1:
				OSDon = 0
				if getFB2(False):
					setFB2("1")
	Screen.L4L_show_old(self)


def find_dev(Anzahl, idVendor, idProduct):
	gefunden = False
	if isfile("/proc/bus/usb/devices"):
		i = open("/proc/bus/usb/devices", "r").read().lower()
		pos = i.find("vendor=%04x prodid=%04x" % (idVendor, idProduct))
		if pos > 0:
			if Anzahl == 2:
				pos = i.find("vendor=%04x prodid=%04x" % (idVendor, idProduct), pos + 10)
				if pos > 0:
					gefunden = True
			else:
				gefunden = True
	elif USBok == True:
		try:
			L4logE("usb.core %s" % list(core.find(idVendor=idVendor, find_all=True)))
			if len(list(core.find(idVendor=idVendor, idProduct=idProduct, find_all=True))) >= Anzahl:
				L4logE("usb.core find")
				gefunden = True
		except Exception:
			L4log("Error usb.core find")
	L4log("%d. Vendor=%04x ProdID=%04x %s" % (Anzahl, idVendor, idProduct, gefunden))
	return gefunden


def find_dev2(idVendor, idProduct, idVendor2, idProduct2):
	gefunden = False
	try:
		if len(list(core.find(idVendor=idVendor, idProduct=idProduct, find_all=True)) + list(core.find(idVendor=idVendor2, idProduct=idProduct2, find_all=True))) >= 2:
			gefunden = True
		L4log("Vendor=%04x ProdID=%04x or Vendor=%04x ProdID=%04x %s" % (idVendor, idProduct, idVendor2, idProduct2, gefunden))
	except Exception:
		L4log("Error usb.core2 find")
	return gefunden

# get picon path


def getpiconres(x, y, full, picon, channelname, channelname2, P2, P2A, P2C):
	if len(P2C) < 3:
		return ""
	PD = join(P2C, picon)
	L4logE("get Picon", PD)
	if isdir(P2C):
		if not isfile(PD):
			L4log("Resize Picon")
			PD = ""
			PIC = []
			PIC.append(join(P2, picon))
			if not PY3:
				name2 = "%s.png" % channelname.decode("utf-8").encode("latin-1", "ignore")
				name4 = "%s.png" % channelname.decode("utf-8").encode("utf-8", "ignore")
				name3 = "%s.png" % channelname2.replace('\xc2\x87', '').replace('\xc2\x86', '').decode("utf-8").encode("utf-8")
				name = normalize('NFKD', unicode(str("" + channelname), 'utf-8', errors='ignore')).encode('ASCII', 'ignore')
			else:
				name2 = "%s.png" % channelname
				name4 = "%s.png" % channelname
				name3 = "%s.png" % channelname2.replace('\x87', '').replace('\x86', '')
				name = normalize('NFKD', str("" + channelname))
			name = "%s.png" % sub(r'[^a-z0-9]', '', str(name).replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
			PIC.append(join(P2, name3))
			PIC.append(join(P2, name2))
			PIC.append(join(P2, name))
			PIC.append(join(P2, name4))
			fields = picon.split("_", 3)
			if fields[0] in ("4097", "5001", "5002", "5003"):
				fields[0] = "1"
				PIC.append(join(P2, "_".join(fields)))
			if len(P2A) > 3:
				PIC.append(join(P2A, picon))
				PIC.append(join(P2A, name3))
				PIC.append(join(P2A, name2))
				PIC.append(join(P2A, name))
				PIC.append(join(P2A, name4))
				fields = picon.split("_", 3)
				if fields[0] in ("4097", "5001", "5002", "5003"):
					fields[0] = "1"
					PIC.append(join(P2A, "_".join(fields)))
			fields = picon.split("_", 3)
			if len(fields) > 2 and fields[2] not in ["1", "2"]:
				fields[2] = "1"
				picon = "_".join(fields)
				PIC.append(join(P2, picon))
				if len(P2A) > 3:
					PIC.append(join(P2A, picon))
			PIC.append(join(P2, "picon_default.png"))
			L4logE("Piconsearch %s" % PIC)
			for Pic in PIC:
				if isfile(Pic):
					PD = Pic
					break
			L4logE("read Picon", PD)
			if PD != "":
				try:
					pil_image = Image.open(PD)
					if str(LCD4linux.PiconTransparenz.value) == "2":
						pil_image = pil_image.convert("RGBA")
					xx, yy = pil_image.size
					if full == False:
						y = int(float(x) / xx * yy)
					if str(LCD4linux.BilderQuality.value) == "0":
						pil_image = pil_image.resize((x, y))
					else:
						pil_image = pil_image.resize((x, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
					s = statvfs(P2C)
					if (s.f_bsize * s.f_bavail / 1024) < 100:
						L4log("Error: Cache Directory near full")
						return ""
					PD = join(P2C, basename(PD))
					L4logE("save Picon", PD)
					pil_image.save(PD)
				except Exception:
					L4log("Error: create Cache-Picon")
					return ""
			else:
				L4logE("no Picon found")
				return ""
		return PD
	else:
		L4logE("no Cache")
		# no picon for channel
		if not exists(P2C):
			L4logE("no Picon-Cachedir", P2C)
			try:
				mkdir(P2C)
			except Exception:
				L4log("Error: create Picon-Cache-Dir")
		return ""


def isOffTime(b, e, bw, ew):
	t = localtime()
	tt = time()
	if strftime("%w") in ["6", "0"]:
		if bw == ew:
			return False
		bT = mktime(datetime(t.tm_year, t.tm_mon, t.tm_mday, bw[0], bw[1]).timetuple())
		eT = mktime(datetime(t.tm_year, t.tm_mon, t.tm_mday, ew[0], ew[1]).timetuple())
	else:
		if b == e:
			return False
		bT = mktime(datetime(t.tm_year, t.tm_mon, t.tm_mday, b[0], b[1]).timetuple())
		eT = mktime(datetime(t.tm_year, t.tm_mon, t.tm_mday, e[0], e[1]).timetuple())
	if eT < bT and tt > eT:
		eT += 86400
	if eT < bT and tt < eT:
		bT -= 86400
	return (bT < tt < eT)


def writeHelligkeit(hell, night, STOP):
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	global AktHelligkeit
	global AktNight
	R = ""
	h1 = BRI(hell[0], 1)
	h2 = BRI(hell[1], 2)
	h3 = BRI(hell[2], 3)
	if isOffTime(L4LMoon, L4LSun, L4LMoon, L4LSun):
		if int(night[0]) != 0:
			h1 = max(h1 - int(night[0]), 0)
		if int(night[1]) != 0:
			h2 = max(h2 - int(night[1]), 0)
		if int(night[2]) != 0:
			h3 = max(h3 - int(night[2]), 0)
	if h1 == 0:
		R += "1"
	if h2 == 0:
		R += "2"
	if h3 == 0:
		R += "3"
	AktNight = night
	if AktHelligkeit == [h1, h2, h3] + L4LElist.getBrightness(0, False) and OSDtimer >= 0:
		return R
	AktHelligkeit = [h1, h2, h3] + L4LElist.getBrightness(0, False)
	L4LElist.resetBrightness([h1, h2, h3])
	L4log("write Bright", AktHelligkeit)
	if SamsungDevice is not None and LCD4linux.LCDType1.value[0] == "1":
		if dpf.setBacklight(SamsungDevice, h1 if h1 < 8 else 7) == False:
			dpf.close(SamsungDevice)
			SamsungDevice = None
	if SamsungDevice2 is not None and LCD4linux.LCDType2.value[0] == "1":
		if dpf.setBacklight(SamsungDevice2, h2 if h2 < 8 else 7) == False:
			dpf.close(SamsungDevice2)
			SamsungDevice2 = None
	if SamsungDevice3 is not None and LCD4linux.LCDType3.value[0] == "1":
		if dpf.setBacklight(SamsungDevice3, h3 if h3 < 8 else 7) == False:
			dpf.close(SamsungDevice3)
			SamsungDevice3 = None
	if isfile("%sgrautec/settings/takeownership" % LCD4etc) and STOP == False:
		try:
			if LCD4linux.LCDType1.value[0] == "4":
				if isfile("/tmp/usbtft-brightness"):
					open("/tmp/usbtft-brightness", "w").write(str(int(h1 * 6.3)))
				elif isfile("/proc/stb/lcd/oled_brightness"):
					open("/proc/stb/lcd/oled_brightness", "w").write(str(int(h1 * 25.5)))
			if LCD4linux.LCDType2.value[0] == "4":
				if isfile("/tmp/usbtft-brightness"):
					open("/tmp/usbtft-brightness", "w").write(str(int(h2 * 6.3)))
				elif isfile("/proc/stb/lcd/oled_brightness"):
					open("/proc/stb/lcd/oled_brightness", "w").write(str(int(h2 * 25.5)))
			if LCD4linux.LCDType3.value[0] == "4":
				if isfile("/tmp/usbtft-brightness"):
					open("/tmp/usbtft-brightness", "w").write(str(int(h3 * 6.3)))
				elif isfile("/proc/stb/lcd/oled_brightness"):
					open("/proc/stb/lcd/oled_brightness", "w").write(str(int(h3 * 25.5)))
		except Exception:
			pass
	try:
		LCDdisplay = LCD()
		if LCD4linux.LCDType1.value[0] == "5":
			LCDdisplay.setBright(h1)
		if LCD4linux.LCDType2.value[0] == "5":
			LCDdisplay.setBright(h2)
		if LCD4linux.LCDType3.value[0] == "5":
			LCDdisplay.setBright(h3)
	except Exception:
		L4logE("Error LCD:", format_exc())
	if PNGutilOK == True:
		H = -1
		if LCD4linux.LCDType1.value[0] == "9":
			H = h1
		elif LCD4linux.LCDType2.value[0] == "9":
			H = h2
		elif LCD4linux.LCDType3.value[0] == "9":
			H = h3
		if H != -1:
			H = int(H) * 25
			if H >= 250:
				H = 255
			try:
				with open("/dev/lcd2", 'w') as led_fd:
					ioctl(led_fd, 0x10, H)
			except Exception as err:
				L4log("Error LCD Communication: %s" % str(err))
	return R


def doDPF(dev, im, s):
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if dev == 1 and dpf.showImage(SamsungDevice, s.im[im]) == False:
		L4log("Error writing DPF Device")
		dpf.close(SamsungDevice)
		SamsungDevice = None
	elif dev == 2 and dpf.showImage(SamsungDevice2, s.im[im]) == False:
		L4log("Error writing DPF2 Device")
		dpf.close(SamsungDevice2)
		SamsungDevice2 = None
	elif dev == 3 and dpf.showImage(SamsungDevice3, s.im[im]) == False:
		L4log("Error writing DPF3 Device")
		dpf.close(SamsungDevice3)
		SamsungDevice3 = None


def writeLCD1(s, im, quality, SAVE=True):
	global SamsungDevice
	global MJPEGreader
	pic = None
	if s.imWrite[im] == True:
		L4log("Ignore ImWrite", im)
		return
	s.imWrite[im] = True
	if LCD4linux.LCDType1.value[0] in ["2", "3"] and virtBRI(1) not in [0, 10] and SAVE == True and LCD4linux.MJPEGvirtbri1.value == True:
		s.tmp[im] = ImageEnhance.Brightness(s.im[im]).enhance(virtBRI(1))
		s.im[im] = s.tmp[im]
	bild = "%s.png" % PICtmp
	if LCD4linux.LCDType1.value[0] == "1":
		if SamsungDevice is not None:
			L4log("writing to DPF Device")
			doDPF(1, im, s)
		if "1" in LCD4linux.SavePicture.value and SAVE == True:
			if str(LCD4linux.LCDRotate1.value) != "0":
				s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate1.value))
			try:
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC)
			except Exception as err:
				L4log("Error write Picture: %s" % str(err))
	elif LCD4linux.LCDType1.value[0] == "3":
		L4log("writing Picture")
		try:
			datei = "%s.%s" % (PICtmp, LCD4linux.BilderTyp.value)
			s.im[im].save(datei, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
			if isfile(datei):
				rename(datei, "%s.%s" % (PIC, LCD4linux.BilderTyp.value))
		except Exception as err:
			L4log("Error write Picture: %s" % str(err))
	elif LCD4linux.LCDType1.value[0] == "4":
		L4log("writing TFT-LCD")
		try:
			s.im[im].save("/tmp/usbtft-bmp", "BMP")
			if "1" in LCD4linux.SavePicture.value and SAVE == True:
				if str(LCD4linux.LCDRotate1.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate1.value))
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC)
		except Exception as err:
			L4log("Error write Picture: %s" % str(err))
	elif LCD4linux.LCDType1.value[0] == "5":
		L4log("writing Internal-LCD")
		try:
			if "1" in LCD4linux.SavePicture.value and SAVE == True:
				if str(LCD4linux.LCDRotate1.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate1.value))
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC)
			if int(LCD4linux.xmlOffset.value) != 0:
				MAX_W, MAX_H = s.im[im].size
				MAX_W += (int(LCD4linux.xmlOffset.value) * 2)
				MAX_H += (int(LCD4linux.xmlOffset.value) * 2)
				imt = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				imt.paste(s.im[im], (int(LCD4linux.xmlOffset.value), int(LCD4linux.xmlOffset.value)))
				s.im[im] = imt
				del imt
			if s.im[im].size == (700, 390):
				s.im[im].convert("P", colors=254).resize((700, 561)).save(xmlPICtmp, "PNG")
			else:
				if str(LCD4linux.xmlLCDColor.value) == "8":
					s.im[im].convert("P", colors=254).save(xmlPICtmp, "PNG")
				else:
					s.im[im].save(xmlPICtmp, "PNG")
			if isfile(xmlPICtmp):
				rename(xmlPICtmp, xmlPIC)
		except Exception as err:
			L4log("Error write Picture: %s" % str(err))
	elif LCD4linux.LCDType1.value[0] == "9":
		L4log("writing to Vu+ LCD")
		try:
			s.im[im].save(bild, "PNG")
			if isfile(bild):
				rename(bild, "%s.png" % PIC)
		except Exception as err:
			L4log("Error write Picture: %s" % str(err))
		if pngutil and pngutilconnect != 0:
			pngutil.send("%s.png" % PIC)
		else:
			L4log("Error no Vu+ connect")
	else:
		if SamsungDevice is not None:
			L4log("writing to Samsung Device")
			output = BytesIO()
			s.im[im].save(output, "JPEG")
			pic = output.getvalue()
			output.close()
			try:
				Photoframe.write_jpg2frame(SamsungDevice, pic)
			except Exception as err:
				SamsungDevice = None
				L4log("Samsung 1 write Error: %s" % str(err))
		if "1" in LCD4linux.SavePicture.value and SAVE == True:
			try:
				datei = "%s.jpg" % PICtmp
				if str(LCD4linux.LCDRotate1.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate1.value))
					s.im[im].save(datei, "JPEG")
				elif pic is not None:
					open(datei, "wb").write(pic)
				if isfile(datei):
					rename(datei, "%s.jpg" % PIC)
			except Exception as err:
				L4log("Error write Picture: %s" % str(err))
	if LCD4linux.MJPEGenable1.value == True:
		if MJPEG[0][1] == "a":
			MJPEG_stop(1)
			sleep(0.5)
			MJPEG_start()
		MJPEG[1].put([im, s])
		MJPEGreader[1] += 1 if MJPEGreader[1] < 100 else 0
	s.imWrite[im] = False


def writeLCD2(s, im, quality, SAVE=True):
	global SamsungDevice2
	global MJPEGreader
	pic = None
	if s.imWrite[im] == True:
		L4log("Ignore ImWrite", im)
		return
	s.imWrite[im] = True
	if LCD4linux.LCDType2.value[0] in ["2", "3"] and virtBRI(2) not in [0, 10] and SAVE == True and LCD4linux.MJPEGvirtbri2.value == True:
		s.tmp[im] = ImageEnhance.Brightness(s.im[im]).enhance(virtBRI(2))
		s.im[im] = s.tmp[im]
	bild = "%s.png" % PIC2tmp
	if LCD4linux.LCDType2.value[0] == "1":
		if SamsungDevice2 is not None:
			L4log("writing to DPF2 Device")
			doDPF(2, im, s)
		if "2" in LCD4linux.SavePicture.value and SAVE == True:
			if str(LCD4linux.LCDRotate2.value) != "0":
				s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate2.value))
			try:
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC2)
			except Exception as err:
				L4log("Error write Picture2: %s" % str(err))
	elif LCD4linux.LCDType2.value[0] == "3":
		L4log("writing Picture2")
		try:
			datei = "%s.%s" % (PIC2tmp, LCD4linux.BilderTyp.value)
			s.im[im].save(datei, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
			if isfile(datei):
				rename(datei, "%s.%s" % (PIC2, LCD4linux.BilderTyp.value))
		except Exception as err:
			L4log("Error write Picture2: %s" % str(err))
	elif LCD4linux.LCDType2.value[0] == "4":
		L4log("writing TFT-LCD2")
		try:
			s.im[im].save("/tmp/usbtft-bmp", "BMP")
			if "2" in LCD4linux.SavePicture.value and SAVE == True:
				if str(LCD4linux.LCDRotate2.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate2.value))
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC2)
		except Exception as err:
			L4log("Error write Picture2: %s" % str(err))
	elif LCD4linux.LCDType2.value[0] == "5":
		L4log("writing Internal-LCD2")
		try:
			if "2" in LCD4linux.SavePicture.value and SAVE == True:
				if str(LCD4linux.LCDRotate2.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate2.value))
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC2)
			if int(LCD4linux.xmlOffset.value) != 0:
				MAX_W, MAX_H = s.im[im].size
				MAX_W += (int(LCD4linux.xmlOffset.value) * 2)
				MAX_H += (int(LCD4linux.xmlOffset.value) * 2)
				imt = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				imt.paste(s.im[im], (int(LCD4linux.xmlOffset.value), int(LCD4linux.xmlOffset.value)))
				s.im[im] = imt
				del imt
			if s.im[im].size == (700, 390):
				s.im[im].convert("P", colors=254).resize((700, 561)).save(xmlPICtmp, "PNG")
			else:
				if str(LCD4linux.xmlLCDColor.value) == "8":
					s.im[im].convert("P", colors=254).save(xmlPICtmp, "PNG")
				else:
					s.im[im].save(xmlPICtmp, "PNG")
			if isfile(xmlPICtmp):
				rename(xmlPICtmp, xmlPIC)
		except Exception as err:
			L4log("Error write Picture2: %s" % str(err))
	elif LCD4linux.LCDType2.value[0] == "9":
		L4log("writing to Vu+ LCD2")
		try:
			s.im[im].save(bild, "PNG")
			if isfile(bild):
				rename(bild, "%s.png" % PIC2)
		except Exception as err:
			L4log("Error write Picture2: %s" % str(err))
		if pngutil and pngutilconnect != 0:
			pngutil.send("%s.png" % PIC2)
		else:
			L4log("Error no Vu+ connect")
	else:
		if SamsungDevice2 is not None:
			L4log("writing to Samsung2 Device")
			output = BytesIO()
			s.im[im].save(output, "JPEG")
			pic = output.getvalue()
			output.close()
			try:
				Photoframe.write_jpg2frame(SamsungDevice2, pic)
			except Exception:
				SamsungDevice2 = None
				L4log("Samsung 2 write Error")
		if "2" in LCD4linux.SavePicture.value and SAVE == True:
			try:
				datei = "%s.jpg" % PIC2tmp
				if str(LCD4linux.LCDRotate2.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate2.value))
					s.im[im].save(datei, "JPEG")
				elif pic is not None:
					open(datei, "wb").write(pic)
				if isfile(datei):
					rename(datei, "%s.jpg" % PIC2)
			except Exception as err:
				L4log("Error write Picture2: %s" % str(err))
	if LCD4linux.MJPEGenable2.value == True:
		if MJPEG[0][1] == "b":
			MJPEG_stop(2)
			sleep(0.5)
			MJPEG_start()
		MJPEG[2].put([im, s])
		MJPEGreader[2] += 1 if MJPEGreader[2] < 100 else 0
	s.imWrite[im] = False


def writeLCD3(s, im, quality, SAVE=True):
	global SamsungDevice3
	global MJPEGreader
	pic = None
	if s.imWrite[im] == True:
		L4log("Ignore ImWrite", im)
		return
	s.imWrite[im] = True
	if LCD4linux.LCDType3.value[0] in ["2", "3"] and virtBRI(3) not in [0, 10] and SAVE == True and LCD4linux.MJPEGvirtbri3.value == True:
		s.tmp[im] = ImageEnhance.Brightness(s.im[im]).enhance(virtBRI(3))
		s.im[im] = s.tmp[im]
	bild = "%s.png" % PIC3tmp
	if LCD4linux.LCDType3.value[0] == "1":
		if SamsungDevice3 is not None:
			L4log("writing to DPF3 Device")
			doDPF(3, im, s)
		if "3" in LCD4linux.SavePicture.value and SAVE == True:
			if str(LCD4linux.LCDRotate3.value) != "0":
				s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate3.value))
			try:
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC3)
			except Exception as err:
				L4log("Error write Picture3: %s" % str(err))
	elif LCD4linux.LCDType3.value[0] == "3":
		L4log("writing Picture3")
		try:
			datei = "%s.%s" % (PIC3tmp, LCD4linux.BilderTyp.value)
			s.im[im].save(datei, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
			if isfile(datei):
				rename(datei, "%s.%s" % (PIC3, LCD4linux.BilderTyp.value))
		except Exception as err:
			L4log("Error write Picture3: %s" % str(err))
	elif LCD4linux.LCDType3.value[0] == "4":
		L4log("writing TFT-LCD3")
		try:
			s.im[im].save("/tmp/usbtft-bmp", "BMP")
			if "3" in LCD4linux.SavePicture.value and SAVE == True:
				if str(LCD4linux.LCDRotate3.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate3.value))
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC3)
		except Exception as err:
			L4log("Error write Picture3: %s" % str(err))
	elif LCD4linux.LCDType3.value[0] == "5":
		L4log("writing Internal-LCD3")
		try:
			if "3" in LCD4linux.SavePicture.value and SAVE == True:
				if str(LCD4linux.LCDRotate3.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate3.value))
				s.im[im].save(bild, "PNG" if LCD4linux.BilderTyp.value == "png" else "JPEG")
				if isfile(bild):
					rename(bild, "%s.png" % PIC3)
			if int(LCD4linux.xmlOffset.value) != 0:
				MAX_W, MAX_H = s.im[im].size
				MAX_W += (int(LCD4linux.xmlOffset.value) * 2)
				MAX_H += (int(LCD4linux.xmlOffset.value) * 2)
				imt = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				imt.paste(s.im[im], (int(LCD4linux.xmlOffset.value), int(LCD4linux.xmlOffset.value)))
				s.im[im] = imt
				del imt
			if s.im[im].size == (700, 390):
				s.im[im].convert("P", colors=254).resize((700, 561)).save(xmlPICtmp, "PNG")
			else:
				if str(LCD4linux.xmlLCDColor.value) == "8":
					s.im[im].convert("P", colors=254).save(xmlPICtmp, "PNG")
				else:
					s.im[im].save(xmlPICtmp, "PNG")
			if isfile(xmlPICtmp):
				rename(xmlPICtmp, xmlPIC)
		except Exception as err:
			L4log("Error write Picture3: %s" % str(err))
	elif LCD4linux.LCDType3.value[0] == "9":
		L4log("writing to Vu+ LCD3")
		try:
			s.im[im].save(bild, "PNG")
			if isfile(bild):
				rename(bild, "%s.png" % PIC3)
		except Exception as err:
			L4log("Error write Picture3: %s" % str(err))
		if pngutil and pngutilconnect != 0:
			pngutil.send("%s.png" % PIC3)
		else:
			L4log("Error no Vu+ connect")
	else:
		if SamsungDevice3 is not None:
			L4log("writing to Samsung3 Device")
			output = BytesIO()
			s.im[im].save(output, "JPEG")
			pic = output.getvalue()
			output.close()
			try:
				Photoframe.write_jpg2frame(SamsungDevice3, pic)
			except Exception:
				SamsungDevice3 = None
				L4log("Samsung 3 write Error")
		if "3" in LCD4linux.SavePicture.value and SAVE == True:
			try:
				datei = "%s.jpg" % PIC3tmp
				if str(LCD4linux.LCDRotate3.value) != "0":
					s.im[im] = s.im[im].rotate(-int(LCD4linux.LCDRotate3.value))
					s.im[im].save(datei, "JPEG")
				elif pic is not None:
					open(datei, "wb").write(pic)
				if isfile(datei):
					rename(datei, "%s.jpg" % PIC3)
			except Exception as err:
				L4log("Error write Picture3: %s" % str(err))
	if LCD4linux.MJPEGenable3.value == True:
		if MJPEG[0][1] == "c":
			MJPEG_stop(3)
			sleep(0.5)
			MJPEG_start()
		MJPEG[3].put([im, s])
		MJPEGreader[3] += 1 if MJPEGreader[3] < 100 else 0
	s.imWrite[im] = False


def isMediaDisplay(player):
	return player in ["sonos", "ymc", "blue"]


def NextScreen(PRESS):
	global ScreenActive
	global ScreenTime
	if SaveEventListChanged == True:
		L4logE("Event Change Aktive")
		return
	if (Standby.inStandby or ConfigStandby) and not isMediaDisplay(isMediaPlayer):
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
		ScreenTime = 0
		ScreenActive[0] = str(int(ScreenActive[0]) + 1)
		if (Standby.inStandby or ConfigStandby) and not isMediaDisplay(isMediaPlayer):
			if int(ScreenActive[0]) > int(LCD4linux.StandbyScreenMax.value):
				ScreenActive[0] = "1"
		elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
			if int(ScreenActive[0]) > int(LCD4linux.MPScreenMax.value):
				ScreenActive[0] = "1"
		else:
			if int(ScreenActive[0]) > int(LCD4linux.ScreenMax.value):
				ScreenActive[0] = "1"
	if int(LCD4linux.StandbyScreenTime.value) > 0 or int(LCD4linux.ScreenTime.value) > 0:
		ScreenTime += 1


def _getDirs(base):
	return [x for x in iglob(join(base, '*')) if isdir(x)]


def rglob(base, pattern):
	liste = []
	liste.extend(glob(join(base, pattern)))
	dirs = _getDirs(base)
	L4logE("Picturedirectorys %s" % dirs)
	if len(dirs):
		for d in dirs:
			liste.extend(rglob(join(base, d), pattern))
	return liste


def getBilder():
	global Bilder
	global BilderIndex
	BilderOrt = ["", "", ""]
	Bilder = [[], [], []]
	SuchExt = ["*.png", "*.PNG", "*.jpg", "*.JPG"]
	if (Standby.inStandby or ConfigStandby) and not isMediaDisplay(isMediaPlayer):
		if str(LCD4linux.StandbyBild.value) != "0":
			BilderOrt[0] = LCD4linux.StandbyBildFile.value
		if str(LCD4linux.StandbyBild2.value) != "0":
			BilderOrt[1] = LCD4linux.StandbyBild2File.value
		if str(LCD4linux.StandbyBild3.value) != "0":
			BilderOrt[2] = LCD4linux.StandbyBild3File.value
	elif isMediaPlayer == "" or isMediaPlayer == "radio":
		if str(LCD4linux.Bild.value) != "0":
			BilderOrt[0] = LCD4linux.BildFile.value
		if str(LCD4linux.Bild2.value) != "0":
			BilderOrt[1] = LCD4linux.Bild2File.value
		if str(LCD4linux.Bild3.value) != "0":
			BilderOrt[2] = LCD4linux.Bild3File.value
	else:
		if str(LCD4linux.MPBild.value) != "0":
			BilderOrt[0] = LCD4linux.MPBildFile.value
		if str(LCD4linux.MPBild2.value) != "0":
			BilderOrt[1] = LCD4linux.MPBild2File.value
		BilderOrt[2] = ""
	L4logE("BilderOrt %s" % BilderOrt)
	if isdir(BilderOrt[0]):
		L4log("read Pictures0")
		BilderIndex[0] = 0
		if LCD4linux.BilderRecursiv.value == False:
			for EXT in SuchExt:
				Bilder[0] += glob(normpath(BilderOrt[0]) + "/" + EXT)
		else:
			for EXT in SuchExt:
				Bilder[0] += rglob(normpath(BilderOrt[0]), EXT)
		if str(LCD4linux.BilderSort.value) == "2":
			shuffle(Bilder[0])
		elif str(LCD4linux.BilderSort.value) == "1":
			Bilder[0].sort()
		L4logE("Pictures %s" % Bilder[0])
	if isdir(BilderOrt[1]):
		L4log("read Pictures1")
		BilderIndex[1] = 0
		if LCD4linux.BilderRecursiv.value == False:
			for EXT in SuchExt:
				Bilder[1] += glob(normpath(BilderOrt[1]) + "/" + EXT)
		else:
			for EXT in SuchExt:
				Bilder[1] += rglob(normpath(BilderOrt[1]), EXT)
		if str(LCD4linux.BilderSort.value) == "2":
			shuffle(Bilder[1])
		elif str(LCD4linux.BilderSort.value) == "1":
			Bilder[1].sort()
		L4logE("Pictures %s" % Bilder[1])
	if isdir(BilderOrt[2]):
		L4log("read Pictures2")
		BilderIndex[2] = 0
		if LCD4linux.BilderRecursiv.value == False:
			for EXT in SuchExt:
				Bilder[2] += glob(normpath(BilderOrt[2]) + "/" + EXT)
		else:
			for EXT in SuchExt:
				Bilder[2] += rglob(normpath(BilderOrt[2]), EXT)
		if str(LCD4linux.BilderSort.value) == "2":
			shuffle(Bilder[2])
		elif str(LCD4linux.BilderSort.value) == "1":
			Bilder[2].sort()
		L4logE("Pictures %s" % Bilder[2])


def request_headers(boundary):
	return {
		'Cache-Control': 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0',
		'Connection': 'close',
		'Content-Type': 'multipart/x-mixed-replace; boundary=%s' % boundary,
		'Expires': 'Mon, 3 Jan 2000 12:34:56 GMT',
		'Pragma': 'no-cache',
	}


def image_headers(size):
	return {'X-Timestamp': time(), 'Content-Type': 'image/jpeg', 'Content-Length': size, } if str(LCD4linux.MJPEGHeader.value) == "0" else {'Content-Type': 'image/jpeg', }


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
	pass


class MJPEGHandler1(BaseHTTPRequestHandler):
	def do_GET(self):
		global MJPEGreader
		boundary = "--avboundary"
		LCD = 1
		try:
			self.send_response(200)
			for k, v in request_headers(boundary).items():
				self.send_header(k, v)
			self.end_headers()
			for x in range(int(LCD4linux.MJPEGMode.value[0])):
				self.wfile.write(boundary.encode('utf-8'))
				self.end_headers()
			while True:
				para = MJPEG[LCD].get()
				if para == [9, 9]:
					return
				MJPEGreader[LCD] = 0
				output = BytesIO()
				if para[0] == 9:
					para[1].save(output, "JPEG")
				else:
					para[1].im[para[0]].save(output, "JPEG")
				pic = output.getvalue()
				output.close()
				for i in range(int(LCD4linux.MJPEGCycle.value)):
					for k, v in image_headers(len(pic)).items():
						self.send_header(k, v)
					self.end_headers()
					for x in range(int(LCD4linux.MJPEGMode.value[1])):
						self.wfile.write(boundary.encode('utf-8'))
						self.end_headers()
					self.wfile.write(pic)
					self.end_headers()
					for x in range(int(LCD4linux.MJPEGMode.value[2])):
						self.wfile.write(boundary.encode('utf-8'))
						self.end_headers()
		except Exception:
			L4log("Error1:", format_exc())
			if LCD4linux.MJPEGRestart.value:
				MJPEG[0] = MJPEG[0].replace("A", "a")

	def log_message(self, format, *args):
		return


def MJPEG_serve1(port):
	global MJPEGserver
	global MJPEGrun
	L4log("start Server 1 Port", port)
	MJPEGserver[1] = ThreadingHTTPServer(("", port), MJPEGHandler1)
	MJPEGserver[1].socket.settimeout(3)
	MJPEGrun[1] = 1
	while getMJPEGrun(1) == 1:
		try:
			MJPEGserver[1].handle_request()
		except Exception:
			L4logE("Error: Server 1 Reg")
	L4log("exit Server 1")


class MJPEGHandler2(BaseHTTPRequestHandler):
	def do_GET(self):
		global MJPEGreader
		boundary = "--avboundary2"
		LCD = 2
		try:
			self.send_response(200)
			for k, v in request_headers(boundary).items():
				self.send_header(k, v)
			self.end_headers()
			for x in range(int(LCD4linux.MJPEGMode.value[0])):
				self.wfile.write(boundary.encode('utf-8'))
				self.end_headers()
			while True:
				para = MJPEG[LCD].get()
				if para == [9, 9]:
					return
				MJPEGreader[LCD] = 0
				output = BytesIO()
				if para[0] == 9:
					para[1].save(output, "JPEG")
				else:
					para[1].im[para[0]].save(output, "JPEG")
				pic = output.getvalue()
				output.close()
				for i in range(int(LCD4linux.MJPEGCycle.value)):
					for k, v in image_headers(len(pic)).items():
						self.send_header(k, v)
					self.end_headers()
					for x in range(int(LCD4linux.MJPEGMode.value[1])):
						self.wfile.write(boundary.encode('utf-8'))
						self.end_headers()
					self.wfile.write(pic)
					self.end_headers()
					for x in range(int(LCD4linux.MJPEGMode.value[2])):
						self.wfile.write(boundary.encode('utf-8'))
						self.end_headers()
		except Exception:
			L4log("Error2:", format_exc())
			if LCD4linux.MJPEGRestart.value:
				MJPEG[0] = MJPEG[0].replace("B", "b")

	def log_message(self, format, *args):
		return


def MJPEG_serve2(port):
	global MJPEGserver
	global MJPEGrun
	L4log("start Server 2 Port", port)
	ThreadingHTTPServer(("", port), MJPEGHandler2)
	MJPEGserver[2] = ThreadingHTTPServer(("", port), MJPEGHandler2)
	MJPEGserver[2].socket.settimeout(3)
	MJPEGrun[2] = 1
	while getMJPEGrun(2) == 1:
		try:
			MJPEGserver[2].handle_request()
		except Exception:
			L4logE("Error: Server 2 Reg")
	L4log("exit Server 2")


class MJPEGHandler3(BaseHTTPRequestHandler):
	def do_GET(self):
		global MJPEGreader
		boundary = "--avboundary3"
		LCD = 3
		try:
			self.send_response(200)
			for k, v in request_headers(boundary).items():
				self.send_header(k, v)
			self.end_headers()
			for x in range(int(LCD4linux.MJPEGMode.value[0])):
				self.wfile.write(boundary.encode('utf-8'))
				self.end_headers()
			while True:
				para = MJPEG[LCD].get()
				if para == [9, 9]:
					return
				MJPEGreader[LCD] = 0
				output = BytesIO()
				if para[0] == 9:
					para[1].save(output, "JPEG")
				else:
					para[1].im[para[0]].save(output, "JPEG")
				pic = output.getvalue()
				output.close()
				for i in range(int(LCD4linux.MJPEGCycle.value)):
					for k, v in image_headers(len(pic)).items():
						self.send_header(k, v)
					self.end_headers()
					for x in range(int(LCD4linux.MJPEGMode.value[1])):
						self.wfile.write(boundary.encode('utf-8'))
						self.end_headers()
					self.wfile.write(pic)
					self.end_headers()
					for x in range(int(LCD4linux.MJPEGMode.value[2])):
						self.wfile.write(boundary.encode('utf-8'))
						self.end_headers()
		except Exception:
			L4log("Error3:", format_exc())
			if LCD4linux.MJPEGRestart.value:
				MJPEG[0] = MJPEG[0].replace("C", "c")

	def log_message(self, format, *args):
		return


def MJPEG_serve3(port):
	global MJPEGserver
	global MJPEGrun
	L4log("start Server 3 Port", port)
	MJPEGserver[3] = ThreadingHTTPServer(("", port), MJPEGHandler3)
	MJPEGserver[3].socket.settimeout(3)
	MJPEGrun[3] = 1
	while getMJPEGrun(3) == 1:
		try:
			MJPEGserver[3].handle_request()
		except Exception:
			L4logE("Error: Server 3 Reg")
	L4log("exit Server 3")


def MJPEG_start():
	global MJPEGreader
	if LCD4linux.MJPEGenable1.value == True and MJPEG[0][1] == "1":
		MJPEG[0] = MJPEG[0].replace("1", "A")
		MJPEGreader[1] = 0
		th1 = Thread(target=MJPEG_serve1, args=[int(LCD4linux.MJPEGport1.value)])
		th1.setDaemon(True)
		th1.start()
	if LCD4linux.MJPEGenable2.value == True and MJPEG[0][2] == "2":
		MJPEG[0] = MJPEG[0].replace("2", "B")
		MJPEGreader[2] = 0
		th2 = Thread(target=MJPEG_serve2, args=[int(LCD4linux.MJPEGport2.value)])
		th2.setDaemon(True)
		th2.start()
	if LCD4linux.MJPEGenable3.value == True and MJPEG[0][3] == "3":
		MJPEG[0] = MJPEG[0].replace("3", "C")
		MJPEGreader[3] = 0
		th3 = Thread(target=MJPEG_serve3, args=[int(LCD4linux.MJPEGport3.value)])
		th3.setDaemon(True)
		th3.start()


def MJPEG_stop(force):
	global MJPEGrun
	stop = False
	if (MJPEG[0][1] == "A") or force == 1:
		L4log("stop Server 1")
		MJPEG[0] = MJPEG[0].replace("a", "A").replace("A", "1")
		try:
			if MJPEGserver[1] is not None:
				MJPEGrun[1] = 0
				if LCD4linux.LCDshutdown.value == True and force == 9:
					MAX_W, MAX_H = getResolution(LCD4linux.LCDType1.value, LCD4linux.LCDRotate1.value)
					MAX_W = int(MAX_W)
					MAX_H = int(MAX_H)
					im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
					for x in range(3):
						MJPEG[1].put([9, im])
				MJPEG[1].put([9, 9])
				MJPEGserver[1].server_close()
				stop = True
		except Exception:
			pass
	if (MJPEG[0][2] == "B") or force == 2:
		L4log("stop Server 2")
		MJPEG[0] = MJPEG[0].replace("b", "B").replace("B", "2")
		try:
			if MJPEGserver[2] is not None:
				MJPEGrun[2] = 0
				if LCD4linux.LCDshutdown.value == True and force == 9:
					MAX_W, MAX_H = getResolution(LCD4linux.LCDType2.value, LCD4linux.LCDRotate2.value)
					MAX_W = int(MAX_W)
					MAX_H = int(MAX_H)
					im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
					for x in range(3):
						MJPEG[2].put([9, im])
				MJPEG[2].put([9, 9])
				MJPEGserver[2].server_close()
				stop = True
		except Exception:
			pass
	if (MJPEG[0][3] == "C") or force == 3:
		L4log("stop Server 3")
		MJPEG[0] = MJPEG[0].replace("c", "C").replace("C", "3")
		try:
			if MJPEGserver[3] is not None:
				MJPEGrun[3] = 0
				if LCD4linux.LCDshutdown.value == True and force == 9:
					MAX_W, MAX_H = getResolution(LCD4linux.LCDType3.value, LCD4linux.LCDRotate3.value)
					MAX_W = int(MAX_W)
					MAX_H = int(MAX_H)
					im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
					for x in range(3):
						MJPEG[3].put([9, im])
				MJPEG[3].put([9, 9])
				MJPEGserver[3].server_close()
				stop = True
		except Exception:
			pass
	if stop:
		sleep(5)


def getWWW():
	if (str(LCD4linux.WWW1.value) != "0" and len(LCD4linux.WWW1url.value) > 10) and (not Standby.inStandby or isMediaDisplay(isMediaPlayer)):
		L4log("WWW Converter check on")
		if LCD4linux.WwwApiUsage == "convertapi":
			getHTMLwwwConvertapi(1, LCD4linux.WWW1url.value, LCD4linux.WWW1w.value, LCD4linux.WWW1h.value)
		else:
			BriefRes.put([getHTMLwwwCloudconvert, 1, LCD4linux.WWW1url.value])
	elif (str(LCD4linux.StandbyWWW1.value) != "0" and len(LCD4linux.StandbyWWW1url.value) > 10) and Standby.inStandby:
		L4log("WWW Converter check stb")
		if LCD4linux.WwwApiUsage == "convertapi":
			getHTMLwwwConvertapi(1, LCD4linux.StandbyWWW1url.value, LCD4linux.StandbyWWW1w.value, LCD4linux.StandbyWWW1h.value)
		else:
			BriefRes.put([getHTMLwwwCloudconvert, 1, LCD4linux.StandbyWWW1url.value])


def HTMLwwwConvertapiDownloadFailed(result):
	L4log("HTMLwww download failed:", result)


def HTMLwwwConvertapiDownloadFinished(filename, result):
	if isfile(filename):
		L4log("HTMLwww download finished")
		rmFile(WWWpic % "1p")
	else:
		L4log("HTMLwww download finished, no file found")


def getHTMLwwwConvertapi(fn, www, pw, ph):
	filename = WWWpic % str(fn)
	url = "http://do.convertapi.com/web2image?curl=%s&PageWidth=%d&PageHight=%d&outputformat=jpg&ApiKex=%s" % (www, pw, ph, LCD4linux.WwwApiKeyConvertapi.value)
	L4log("downloading HTMLwww from", url)
	callInThread(downloadPage, url, filename, boundFunction(HTMLwwwConvertapiDownloadFinished, filename), HTMLwwwConvertapiDownloadFailed)


def HTMLwwwDownloadFailed(result):
	L4log("HTMLwww download failed:", result)


def HTMLwwwDownloadFinished(filename, result):
	if isfile(filename):
		L4log("HTMLwww download finished")
		rmFile(WWWpic % "1p")
	else:
		L4log("HTMLwww download finished, no file found")


def getHTMLwww(fn, url):
	filename = WWWpic % str(fn)
	L4log("downloading HTMLwww from", url)
	callInThread(downloadPage, url, filename, boundFunction(HTMLwwwDownloadFinished, filename), HTMLwwwDownloadFailed)


def Urlget(url, params, method, API):
	headers = {}
	headers["Authorization"] = "Bearer " + API
	if method == 'POST':
		headers["Content-type"] = "application/json"
		f = post(url, headers=headers, params=params)
	else:
		f = get(url, headers=headers, params=params, timeout=(3.05, 6))
	return (f.text, f.status_code)


def getHTMLwwwCloudconvert(fn, www):
	if len(LCD4linux.WwwApiKeyCloudconvert.value.split()) == 0:
		L4log("Error no API-Key")
		return
	API = None
	L4log("downloading HTMLwww from", www)
	content, resp = ("", "")
	try:
		for API in LCD4linux.WwwApiKeyCloudconvert.value.split():
			dataget = {'url': www, 'output_format': 'jpg'}
			content, resp = Urlget('https://api.cloudconvert.com/v2/capture-website', dataget, 'POST', API)
			L4logE(content, "%s" % resp)
			if resp == 201:
				break
		if resp == 201:
			r = loads(content)
			content2, resp2 = Urlget(r['data']['links']['self'], {}, "GET", API)
			L4logE(content2, "%s" % resp2)
			if resp2 == 200:
				content3, resp3 = Urlget(r['data']['links']['self'], {}, "GET", API)
				L4logE(content3, "%s" % resp3)
				r3 = loads(content3)
				i = 0
				while r3['data']['status'] != 'finished' and i < 30:
					sleep(0.5)
					i += 1
					content3, resp3 = Urlget(r3['data']['links']['self'], {}, 'GET', API)
					L4logE(content3, "%s" % resp3)
					r3 = loads(content3)
				if resp3 == 200 and i < 30:
					dataget = {"input": r3['data']['id']}
					content4, resp4 = Urlget('https://api.cloudconvert.com/v2/export/url', dataget, 'POST', API)
					L4logE(content4, "%s" % resp4)
					r4 = loads(content4)
					i = 0
					while r4['data']['status'] != 'finished' and i < 30:
						sleep(0.5)
						i += 1
						content4, resp4 = Urlget(r4['data']['links']['self'], {}, "GET", API)
						L4logE("%s %s" % (content4, resp4))
						r4 = loads(content4)
					if resp4 == 200 and i < 30:
						getHTMLwww(fn, r4['data']['result']['files'][0]['url'])
					else:
						L4log("WWW Error4: %s %s" % (content4, resp4))
				else:
					L4log("WWW Error3: %s %s" % (content3, resp3))
			else:
				L4log("WWW Error2: %s %s" % (content2, resp2))
		else:
			L4log("WWW Error1: %s %s" % (content, resp))
	except Exception:
		L4log("WWW Crash-Error")


def xmlFind(Num):
	for i in xmlList:
		if i.startswith("<!--L4L%02d" % Num):
			return 0
	return -1


def xmlScreens(Lis2):
	sl = []
	for i in Lis2:
		if i.find("<screen ") != -1:
			b = i.replace("\"", "").split("name=")
			sl.append(b[1].split()[0])
	return sl


def xmlInsert(Lis2):
	global xmlList
	if len(Lis2) == 0:
		L4log("insert no Skindata")
		return
	xl = xmlScreens(Lis2)
	for i in range(0, len(xmlList)):
		if xmlList[i].find("<screen ") != -1:
			for i2 in range(0, len(xl)):
				if xmlList[i].find("\"%s\"" % xl[i2]) != -1:
					L4log("disable Screen", xl[i2])
					xmlList[i] = xmlList[i].replace("\"%s\"" % xl[i2], "\"L4L%s\"" % xl[i2])
	L4log("insert Skindata")
	for i in Lis2:
		xmlList.insert(-1, i)


def xmlDelete(Num):
	global xmlList
	delON = False
	isDelete = False
	sli = xmlReadData()
	xl = xmlScreens(sli[Num])
	for i in range(0, len(xmlList)):
		if xmlList[i].find("<screen ") != -1:
			for i2 in range(0, len(xl)):
				if xmlList[i].find("\"L4L%s\"" % xl[i2]) != -1:
					L4log("enable Screen", xl[i2])
					xmlList[i] = xmlList[i].replace("\"L4L%s\"" % xl[i2], "\"%s\"" % xl[i2])
	i = 0
	aa = 0
	while i < len(xmlList):
		if xmlList[i].startswith("<!--L4L%02d " % Num):
			delON = True
			isDelete = True
			L4log("remove Skindata", Num)
		if delON == True:
			if xmlList[i].startswith("<!--L4L%02d-" % Num):
				delON = False
			del xmlList[i]
		else:
			i += 1
	return isDelete


def xmlClear():
	global xmlList
	xmlList = []


def xmlRead():
	global xmlList
	xmlList = []
	xmlfile = join(LCD4enigma2config, "skin_user.xml")
	if isfile(xmlfile):
		for i in open(xmlfile).read().splitlines():
			xmlList.append(i)
		if len(xmlList) > 1:
			while len(xmlList[-1]) < 2 and len(xmlList) > 1:
				del xmlList[-1]
	else:
		sli = xmlReadData()
		aw, ah = 0, 0
		ttt = [0]
		for i in sli[0]:
			ttt = LCD4linux.xmlLCDType.value.split("x")
			aw, ah = 0, 0
			if LCD4linux.xmlLCDType.value == "96x64":
				i = i.replace("\">", "\" id=\"2\">")
			if getFB2(False):
				if "PixmapLcd4linux" in i:
					i = i.replace("0,0", "10,13")
				aw, ah = 10, 171
		xmlList = ["\n".join(sli[0]).replace("$w$", str(int(ttt[0]) + aw)).replace("$h$", str(int(ttt[1]) + ah)), "</skin>"]


def xmlReadData():
	sld = [[], [], [], []]
	if isfile(join(LCD4data, "skin_data.xml")):
		aa = 0
		for i in open(join(LCD4data, "skin_data.xml")).read().splitlines():
			if i.startswith("###"):
				break
			if i.startswith("<!--L4L"):
				aa = int(i[7:9])
			sld[aa].append(i)
	return sld


def xmlWrite():
	if len(xmlList) > 1:
		L4log("write SkinData")
		with open(join(LCD4enigma2config, "skin_user.xml"), "w") as fw:
			for i in xmlList:
				fw.write(i + "\n")


def xmlSkin():
	if LCD4linux.xmlType01.value == False and LCD4linux.xmlType02.value == False and LCD4linux.xmlType03.value == False:
		rmFile(join(LCD4enigma2config, "skin_user.xml"))
		return True
	change = False
	xmlRead()
	if xmlList[-1].find("/skin") == -1:
		L4log("Error xmlSkin")
		return False
	sli = xmlReadData()
	xf = xmlFind(1)
	if xf == -1 and LCD4linux.xmlType01.value == True:
		change = True
		xmlInsert(sli[1])
	elif xf >= 0 and LCD4linux.xmlType01.value == False:
		change = True
		ok = xmlDelete(1)
	xf = xmlFind(2)
	if xf == -1 and LCD4linux.xmlType02.value == True:
		change = True
		xmlInsert(sli[2])
	elif xf >= 0 and LCD4linux.xmlType02.value == False:
		change = True
		ok = xmlDelete(2)
	xf = xmlFind(3)
	if xf == -1 and LCD4linux.xmlType03.value == True:
		change = True
		xmlInsert(sli[3])
	elif xf >= 0 and LCD4linux.xmlType03.value == False:
		change = True
		ok = xmlDelete(3)
	return change


class RunShell:
	def __init__(self, cmd):
		global ShellRunning
		ShellRunning = True
		L4log("Shell", cmd)
		system(cmd + " >/dev/null 2>&1")
		ShellRunning = False

	def cmdFinished(self, data):
		global ShellRunning
		ShellRunning = False
		L4log("Shell Stop")

	def dataAvail(self, data):
		global ShellRunning
		ShellRunning = False
		L4log("Shell Data")


def TFTCheck(Force, SetMode=""):
	global AktTFT
	if isfile("%stft-bmp-mode.sh" % LCD4bin) == True and isfile("%stft-dream-mode.sh" % LCD4bin) == True:
		CurTFT = isfile("%sgrautec/settings/takeownership" % LCD4etc)
		L4logE("TFT mode... %s" % CurTFT)
		if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4" or LCD4linux.LCDType3.value[0] == "4" and SetMode != "DREAM":
			L4logE("TFT enabled")
			if AktTFT != "BMP" or Force == True or SetMode == "BMP":
				i = 10
				while ShellRunning == True and i > 0:
					sleep(0.5)
					i -= 1
				RunShell("%stft-bmp-mode.sh" % LCD4bin)
				AktTFT = "BMP"
		else:
			L4logE("TFT not")
			if (AktTFT != "DREAM" and CurTFT == True) or Force == True or SetMode == "DREAM":
				i = 10
				while ShellRunning == True and i > 0:
					sleep(0.5)
					i -= 1
				RunShell("%stft-dream-mode.sh" % LCD4bin)
				AktTFT = "DREAM"


def SamsungCheck():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if USBok == False:
		return True
	if LCD4linux.LCDType1.value[0] == "2":
		known_devices_list = Photoframe.get_known_devices()
		device0 = known_devices_list[(int(LCD4linux.LCDType1.value[1:]) - 3) * 2]
		if find_dev(1, device0["idVendor"], device0["idProduct"]) == False:
			L4log("Samsung 1 Stat failed")
			SamsungDevice = None
			return True
		if Photoframe.name(SamsungDevice) is None:
			L4log("Samsung 1 no answer")
			SamsungDevice = None
			return True
	if LCD4linux.LCDType2.value[0] == "2":
		known_devices_list = Photoframe.get_known_devices()
		device0 = known_devices_list[(int(LCD4linux.LCDType2.value[1:]) - 3) * 2]
		Anz = 2 if LCD4linux.LCDType1.value == LCD4linux.LCDType2.value else 1
		if find_dev(Anz, device0["idVendor"], device0["idProduct"]) == False:
			L4log("Samsung 2 Stat failed")
			SamsungDevice2 = None
			return True
		if Photoframe.name(SamsungDevice2) is None:
			L4log("Samsung 2 no answer")
			SamsungDevice2 = None
			return True
	if LCD4linux.LCDType3.value[0] == "2":
		known_devices_list = Photoframe.get_known_devices()
		device0 = known_devices_list[(int(LCD4linux.LCDType3.value[1:]) - 3) * 2]
		Anz = 2 if LCD4linux.LCDType1.value == LCD4linux.LCDType3.value else 1
		if find_dev(Anz, device0["idVendor"], device0["idProduct"]) == False:
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
		if LCD4linux.LCDType1.value[0] == "2" and SamsungDevice is None:
			L4log("get Samsung Device...")
			known_devices_list = Photoframe.get_known_devices()
			device0 = known_devices_list[(int(LCD4linux.LCDType1.value[1:]) - 3) * 2]
			device1 = known_devices_list[(int(LCD4linux.LCDType1.value[1:]) - 3) * 2 + 1]
			if find_dev(1, device0["idVendor"], device0["idProduct"]) == True or find_dev(1, device1["idVendor"], device1["idProduct"]) == True:
				try:
					SamsungDevice = Photoframe.init_device(1, device0, device1)
				except Exception:
					pass
		if LCD4linux.LCDType2.value[0] == "2" and SamsungDevice2 is None:
			L4log("get Samsung2 Device...")
			known_devices_list = Photoframe.get_known_devices()
			device0 = known_devices_list[(int(LCD4linux.LCDType2.value[1:]) - 3) * 2]
			device1 = known_devices_list[(int(LCD4linux.LCDType2.value[1:]) - 3) * 2 + 1]
			Anz = 2 if LCD4linux.LCDType1.value == LCD4linux.LCDType2.value else 1
			if Anz == 2:
				if find_dev2(device0["idVendor"], device0["idProduct"], device1["idVendor"], device1["idProduct"]) == True:
					try:
						SamsungDevice2 = Photoframe.init_device(Anz, device0, device1)
					except Exception:
						pass
			else:
				if find_dev(Anz, device0["idVendor"], device0["idProduct"]) == True or find_dev(Anz, device1["idVendor"], device1["idProduct"]) == True:
					try:
						SamsungDevice2 = Photoframe.init_device(Anz, device0, device1)
					except Exception:
						pass
		if LCD4linux.LCDType3.value[0] == "2" and SamsungDevice3 is None:
			L4log("get Samsung3 Device...")
			known_devices_list = Photoframe.get_known_devices()
			device0 = known_devices_list[(int(LCD4linux.LCDType3.value[1:]) - 3) * 2]
			device1 = known_devices_list[(int(LCD4linux.LCDType3.value[1:]) - 3) * 2 + 1]
			Anz = 2 if LCD4linux.LCDType1.value == LCD4linux.LCDType3.value else 1
			if Anz == 2:
				if find_dev2(device0["idVendor"], device0["idProduct"], device1["idVendor"], device1["idProduct"]) == True:
					try:
						SamsungDevice3 = Photoframe.init_device(Anz, device0, device1)
					except Exception:
						pass
			else:
				if find_dev(Anz, device0["idVendor"], device0["idProduct"]) == True or find_dev(Anz, device1["idVendor"], device1["idProduct"]) == True:
					try:
						SamsungDevice3 = Photoframe.init_device(Anz, device0, device1)
					except Exception:
						pass


def DpfCheck():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if USBok == False:
		return True
	if LCD4linux.LCDType1.value[0] == "1":
		if find_dev(1, 0x1908, 0x0102) == False or SamsungDevice is None:
			L4log("DPF 1 Stat failed")
			dpf.close(SamsungDevice)
			SamsungDevice = None
			return True
	if LCD4linux.LCDType2.value[0] == "1":
		Anz = 2 if LCD4linux.LCDType1.value[0] == LCD4linux.LCDType2.value[0] else 1
		if find_dev(Anz, 0x1908, 0x0102) == False or SamsungDevice2 is None:
			L4log("DPF 2 Stat failed")
			dpf.close(SamsungDevice2)
			SamsungDevice2 = None
			return True
	if LCD4linux.LCDType3.value[0] == "1":
		Anz = 2 if LCD4linux.LCDType1.value[0] == LCD4linux.LCDType3.value[0] else 1
		if find_dev(Anz, 0x1908, 0x0102) == False or SamsungDevice3 is None:
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
	if LCD4linux.LCDType1.value[0] == "1" and SamsungDevice is None:
		L4log("get DPF Device...")
		if find_dev(1, 0x1908, 0x0102) == True:
			try:
				L4log("open DPF Device0...")
				SamsungDevice = dpf.open("usb0")
			except Exception:
				L4log("open Error DPF1 Device0")
				SamsungDevice = None
		else:
			L4log("DPF1 Device0 not found")
	if LCD4linux.LCDType2.value[0] == "1" and SamsungDevice2 is None:
		L4log("get DPF2 Device...")
		Anz = 2 if LCD4linux.LCDType1.value[0] == LCD4linux.LCDType2.value[0] else 1
		if Anz == 2:
			if find_dev(2, 0x1908, 0x0102) == True:
				try:
					L4log("open DPF2 Device1...")
					SamsungDevice2 = dpf.open("usb1")
				except Exception:
					L4log("open Error DPF2 Device1")
					SamsungDevice2 = None
			else:
				L4log("DPF2 Device1 not found")
		else:
			if find_dev(1, 0x1908, 0x0102) == True:
				try:
					L4log("open DPF2 Device0...")
					SamsungDevice2 = dpf.open("usb0")
				except Exception:
					L4log("open Error DPF2 Device0")
					SamsungDevice2 = None
			else:
				L4log("DPF2 Device0 not found")
	if LCD4linux.LCDType3.value[0] == "1" and SamsungDevice3 is None:
		L4log("get DPF3 Device...")
		Anz = 2 if LCD4linux.LCDType1.value[0] == LCD4linux.LCDType3.value[0] else 1
		if Anz == 2:
			if find_dev(2, 0x1908, 0x0102) == True:
				try:
					L4log("open DPF3 Device1...")
					SamsungDevice3 = dpf.open("usb1")
				except Exception:
					L4log("open Error DPF3 Device1")
					SamsungDevice3 = None
			else:
				L4log("DPF2 Device1 not found")
		else:
			if find_dev(1, 0x1908, 0x0102) == True:
				try:
					L4log("open DPF3 Device0...")
					SamsungDevice3 = dpf.open("usb0")
				except Exception:
					L4log("open Error DPF3 Device0")
					SamsungDevice3 = None
			else:
				L4log("DPF3 Device0 not found")


def DpfCheckSerial():
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	if LCD4linux.LCDType1.value[0] in ["11", "12"] and LCD4linux.LCDType1.value[0] == LCD4linux.LCDType2.value[0]:
		if SamsungDevice is not None and SamsungDevice2 is not None:
			s1, s2 = "", ""
			try:
				s1 = "".join(unpack("sxsxsx", SamsungDevice.readFlash(0x180ED3, 6)))
			except Exception:
				dpf.close(SamsungDevice)
				SamsungDevice = None
				L4log("Error Read DPF Device")
				return
			try:
				s2 = "".join(unpack("sxsxsx", SamsungDevice2.readFlash(0x180ED3, 6)))
			except Exception:
				dpf.close(SamsungDevice2)
				SamsungDevice2 = None
				L4log("Error Read DPF2 Device")
				return
			L4log(s1, s2)
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
	if isfile("%sfstab" % LCD4etc):
		if open("%sfstab" % LCD4etc, "r").read().lower().find("usbfs") == -1:
			L4log("Info: no usbfs-Line in fstab")


def FritzCallLCD4Linux(event, Date, number, caller, phone):
	global FritzTime
	if (str(LCD4linux.Fritz.value) != "0" or str(LCD4linux.MPFritz.value) != "0" or str(LCD4linux.StandbyFritz.value) != "0"):
		L4log("FritzCall %s" % [event, Date, number, caller, phone])
		if len(FritzList) > 0 and Date == FritzList[-1][1]:
			L4log("FritzCall ignore")
			return
		rmFile(PICfritz)
		FritzList.append([event, Date, number.replace("#", ""), caller, phone])
		FritzTime = int(LCD4linux.FritzTime.value) + 2
		while len(FritzList) > 20:
			del FritzList[0]
		if BriefLCD.qsize() <= 2:
			BriefLCD.put(1)


def NcidLCD4Linux(Date, number, caller):
	global FritzTime
	if (str(LCD4linux.Fritz.value) != "0" or str(LCD4linux.MPFritz.value) != "0" or str(LCD4linux.StandbyFritz.value) != "0"):
		L4log("Ncid %s" % [Date, number, caller])
		rmFile(PICfritz)
		dt = datetime.strptime(Date, _("%d.%m.%Y - %H:%M"))
		Date = dt.strftime(_("%d.%m.%y %H:%M:%S"))
		FritzList.append(["RING", Date, number, caller, ""])
		FritzTime = int(LCD4linux.FritzTime.value) + 2
		while len(FritzList) > 20:
			del FritzList[0]
		if BriefLCD.qsize() <= 2:
			BriefLCD.put(1)


# Load Config
if isfile(LCD4config):
	L = open(LCD4config, "r").read()
	if "Netatmo" in L:
		L = L.replace("Netatmo", "NetAtmo")
		open(LCD4config, "w").write(L)
	LCD4linux.loadFromFile(LCD4config)
	LCD4linux.load()
else:
	L4log("no config found!")
try:
	from Plugins.Extensions.FritzCall.plugin import registerUserAction as FritzCallRegisterUserAction
	FritzCallRegisterUserAction(FritzCallLCD4Linux)
	L4log("Register FritzCall ok")
except Exception:
	L4log("FritzCall not registered")
try:
	from Plugins.Extensions.NcidClient.plugin import registerUserAction as NcidClientRegisterUserAction
	NcidClientRegisterUserAction(NcidLCD4Linux)
	L4log("Register NcidClient ok")
except Exception:
	L4log("NcidClient not registered")
BITRATEVIEWER = "BitrateViewer"
BITRATE = "Bitrate"
PreferredBitrate = BITRATE
RegisteredBitrate = []
try:
	from Plugins.Extensions.BitrateViewer.bitratecalc import eBitrateCalculator
	BitrateRegistred = True
	L4log("Register BitrateViewer ok")
	RegisteredBitrate.append(BITRATEVIEWER)
except Exception:
	BitrateRegistred = False
	L4log("BitrateViewer not registered")
try:
	from Plugins.Extensions.Bitrate.bitrate import Bitrate
	BitrateRegistred = True
	L4log("Register Bitrate ok")
	RegisteredBitrate.append(BITRATE)
except Exception:
	BitrateRegistred = False
	L4log("Bitrate not registered")
try:
	from Plugins.Extensions.webradioFS.ext import ext_l4l
	WebRadioFS = ext_l4l()
	WebRadioFSok = True
	L4log("Register WebRadioFS ok")
except Exception:
	WebRadioFSok = False
	L4log("WebRadioFS not registered")
try:
	from Plugins.Extensions.Netatmo.Netatmo import netatmo
	from Plugins.Extensions.Netatmo.NetatmoCore import NetatmoUnit
	NetatmoOK = True
	L4log("Register Netatmo ok")
	L4log("Error:", format_exc())
except Exception:
	NetatmoOK = False
	L4log("Netatmo not registered")
try:
	from Plugins.Bp.geminimain.Cjukeboxevent import cjukeboxevent, CjukeboxEventNotifier
	GPjukeboxOK = True
	L4log("Register GP3 ok")
except Exception:
	GPjukeboxOK = False
	L4log("GP3 not registered")
try:
	from soco import SoCo
	SonosOK = True
	L4log("Register Sonos ok")
except Exception:
	SonosOK = False
	L4log("Sonos not registered")
from .ymc import YMC
from .bluesound import BlueSound


def getPage(link, success, fail=None, headers=None, timeout=(3.05, 6)):
	agents = [
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
			"Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0"
			"Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)"
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75"
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"
			]
	if headers is None:
		headers = {}
	if "User-Agent" not in headers:
		headers["User-Agent"] = choice(agents)
	link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
	try:
		response = get(link, headers=headers, timeout=timeout)
		response.raise_for_status()
		success(response.content)
	except exceptions.RequestException as error:
		if fail is not None:
			fail(error)


def downloadPage(link, file, success, fail=None):
	link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
	try:
		response = get(link, timeout=(3.05, 6))
		response.raise_for_status()
		with open(file, "wb") as f:
			f.write(response.content)
		success(file)
	except exceptions.RequestException as error:
		if fail is not None:
			fail(error)


class GrabOSD:
	def __init__(self, cmd):
		global GrabRunning
		GrabRunning = True
		L4logE("Grab Run")

		system(cmd + " >/dev/null 2>&1")
		self.cmdFinished("")

	def cmdFinished(self, data):
		global GrabRunning
		L4logE("Grab Stop")
		GrabRunning = False

	def dataAvail(self, data):
		pass

# Grab


def doGrab(i, ConfigFast, ConfigSize):
	if getFB2(True):
		setFB2("0")
	else:
		CF = "" if ConfigFast == True else "-b"
		GrabOSD("%sgrab -o -p -j 95 %s -r %d %sdpfgrab.jpg" % (LCD4bin, CF, ConfigSize, TMPL))


def InitWebIF():
	L4log("WebIf-Init...")
	i = 20
	if LCD4linux.WebIfInitDelay.value == True:
		while len(glob(LCD4enigma2plugin + "Extensions/WebInterface/__init__.py*")) == 0 and i > 0:
			sleep(0.5)
			i -= 1
	if i > 0 and len(glob(LCD4enigma2plugin + "Extensions/WebInterface/__init__.py*")) > 0:
		if i < 20:
			L4log("WebIf-Wait %d s" % int((20 - i) / 2))
			sleep(5)
		from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
		from twisted.web import static
		from .WebSite import LCD4linuxweb, LCD4linuxwebView
		from .WebConfigSite import LCD4linuxConfigweb
		L4log("Child to WebIf...")
		root = static.File(ensure_binary("%slcd4linux" % TMP))
		root.putChild(b"", LCD4linuxweb())
		root.putChild(b"view", LCD4linuxwebView())
		root.putChild(b"config", LCD4linuxConfigweb())
		root.putChild(b"data", static.File(ensure_binary(LCD4data[:-1])))
		if isfile(join(LCD4enigma2plugin, "Extensions/LCD4linux/WebInterface/web/external.xml")):
			try:
				addExternalChild(("lcd4linux", root, "LCD4linux", Version, True))
				L4log("use new WebIf")
			except Exception:
				addExternalChild(("lcd4linux", root))
				L4log("Error, fall back to old WebIf")
		else:
			addExternalChild(("lcd4linux", root))
			L4log("use old WebIf")
		if isfile(join(LCD4enigma2plugin, "Extensions/OpenWebif/pluginshook.src")):
			try:
				addExternalChild(("lcd4linux", root, "LCD4linux", Version))
				L4log("use OpenWebif")
			except Exception:
				pass
	else:
		L4log("no WebIf found")


class L4LWorkerRes(Thread):
	def __init__(self, index, s, session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s

	def run(self):
		while True:
			try:
				para = BriefRes.get()
				if len(para) == 2:
					para[0](para[1])
				elif len(para) == 3:
					para[0](para[1], para[2])
				elif len(para) == 4:
					para[0](para[1], para[2], para[3])
				elif len(para) == 5:
					para[0](para[1], para[2], para[3], para[4])
				elif len(para) == 7:
					para[0](para[1], para[2], para[3], para[4], para[5], para[6])
				elif len(para) == 8:
					para[0](para[1], para[2], para[3], para[4], para[5], para[6], para[7])
			except Exception:
				L4log("Error1:", format_exc())
				try:
					open(CrashFile, "w").write(format_exc())
				except Exception:
					pass
			BriefRes.task_done()


class L4LWorker1(Thread):
	def __init__(self, index, s, session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s

	def run(self):
		while True:
			try:
				para = Brief1.get()
				if len(para) == 2:
					para[0](para[1])
				elif len(para) == 4:
					para[0](para[1], para[2], para[3])
				elif len(para) == 5:
					para[0](para[1], para[2], para[3], para[4])
				elif len(para) == 3:
					para[0](para[1], para[2])
				elif len(para) == 7:
					para[0](para[1], para[2], para[3], para[4], para[5], para[6])
				elif len(para) == 8:
					para[0](para[1], para[2], para[3], para[4], para[5], para[6], para[7])
			except Exception:
				L4log("Error1:", format_exc())
				try:
					open(CrashFile, "w").write(format_exc())
				except Exception:
					pass
			Brief1.task_done()


class L4LWorker2(Thread):
	def __init__(self, index, s, session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s

	def run(self):
		while True:
			try:
				para = Brief2.get()
				if len(para) == 2:
					para[0](para[1])
				elif len(para) == 4:
					para[0](para[1], para[2], para[3])
				elif len(para) == 5:
					para[0](para[1], para[2], para[3], para[4])
				elif len(para) == 3:
					para[0](para[1], para[2])
				elif len(para) == 7:
					para[0](para[1], para[2], para[3], para[4], para[5], para[6])
				elif len(para) == 8:
					para[0](para[1], para[2], para[3], para[4], para[5], para[6], para[7])
			except Exception:
				L4log("Error2:", format_exc())
				try:
					open(CrashFile, "w").write(format_exc())
				except Exception:
					pass
			Brief2.task_done()


class L4LWorker3(Thread):
	def __init__(self, index, s, session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s

	def run(self):
		while True:
			try:
				para = Brief3.get()
				if len(para) == 2:
					para[0](para[1])
				elif len(para) == 4:
					para[0](para[1], para[2], para[3])
				elif len(para) == 5:
					para[0](para[1], para[2], para[3], para[4])
				elif len(para) == 3:
					para[0](para[1], para[2])
				elif len(para) == 7:
					para[0](para[1], para[2], para[3], para[4], para[5], para[6])
				elif len(para) == 8:
					para[0](para[1], para[2], para[3], para[4], para[5], para[6], para[7])
			except Exception:
				L4log("Error3:", format_exc())
				try:
					open(CrashFile, "w").write(format_exc())
				except Exception:
					pass
			Brief3.task_done()


class L4LWorkerLCD(Thread):
	def __init__(self, index, s, session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s

	def run(self):
		global FritzTime
		while True:
			zahl = BriefLCD.get()
			if zahl == 1:
				self.GeneratePicture(self.index)
			BriefLCD.task_done()

	def GeneratePicture(self, i):
		L4logE("Run Worker Pic", i)
		disable()
		LCD4linuxPICThread(self.s, self.session)
		enable()
		L4logE("Done Worker Pic", i)
		return "ok"


class L4LWorker(Thread):
	QuickRunning = False

	def __init__(self, index, s, session):
		Thread.__init__(self)
		self.index = index
		self.session = session
		self.s = s

	def run(self):
		global FritzTime
		while True:
			zahl = Briefkasten.get()
			if zahl == 1:
				pass
			elif zahl == 2:
				doGrab(self.index, LCD4linux.OSDfast.value, LCD4linux.OSDsize.value)
			elif zahl == 3:
				if (str(LCD4linux.Fritz.value) != "0" or str(LCD4linux.MPFritz.value) != "0" or str(LCD4linux.StandbyFritz.value) != "0"):
					if isfile(Fritz):
						FritzList.append(open(Fritz, "r").read().split(";"))
						rmFile(Fritz)
						rmFile(PICfritz)
						FritzTime = int(LCD4linux.FritzTime.value) + 2
						while len(FritzList) > 20:
							del FritzList[0]
						self.GeneratePicture(self.index)
			elif zahl == 4:
				self.runICS()
			elif zahl == 5:
				self.hookWebif()
			elif zahl == 6:
				self.runMail()
			elif zahl == 7:
				if QuickList != [[], [], []] and L4LWorker.QuickRunning == False and ThreadRunning == 0 and OSDon == 0 and FritzTime == 0:
					self.QuickBild(self.s)
			elif zahl == 8:
				ICSdownloads()
			Briefkasten.task_done()

	def GeneratePicture(self, i):
		L4logE("Run Worker Pic", i)
		disable()
		LCD4linuxPICThread(self.s, self.session)
		enable()
		L4logE("Done Worker Pic", i)
		return "ok"

	def getICS(self, name, col):
		global ICS
		global ICSlist
		if len(name) < 3 or "..." in name:
			L4logE("ignore ICS", name)
			return
		try:
			r = None
			rs = ""
			try:
				if name.startswith("http") and len(name) > 10:
					r = urlopen(name, timeout=10)
				elif isfile(name):
					r = open(name, "rb")
				else:
					L4log("Error: no ICS found", name)
					return
			except Exception:
				L4log("Error: ICS Open", name)
				L4log("Error:", format_exc())
				return
			if r is not None:
				L4log("Read ICS", name)
				try:
					rs = r.read()
					r.close()
					ICSlist.append([ensure_str(rs), col])
					return
				except Exception:
					L4log("Error: ICS not readable!", name)
					return
			else:
				L4logE("Error Read ICS", name)
		except Exception:
			L4log("Error ICS", name)
			L4log("Error:", format_exc())
			try:
				open(CrashFile, "w").write(format_exc())
			except Exception:
				pass

	def runICS(self):
		global ICSrunning
		if ICSrunning == True:
			L4log("Block ICS...")
			return
		ICSrunning = True
		L4log("Reading ICS...")
		for dics in glob(join(LCD4linux.CalPath.value, "*.ics")):
			self.getICS(dics, 0)
		self.getICS(LCD4linux.CalHttp.value, 1)
		self.getICS(LCD4linux.CalHttp2.value, 2)
		self.getICS(LCD4linux.CalHttp3.value, 3)
		ICSdownloads()
		ICSrunning = False

	def hookWebif(self):
		InitWebIF()

	def runMail(self):
		global PopMail
		global PopMailUid

		def MailDecode(Sdecode):
			try:
				H = decode_header(Sdecode)
				W = ""
				for HH in H:
					W += HH[0] if HH[1] is None else HH[0].decode(HH[1])
			except Exception:
				L4logE("Info, can not decode:", Sdecode)
				W = Sdecode
			return W
		S = [LCD4linux.Mail1Pop.value, LCD4linux.Mail2Pop.value, LCD4linux.Mail3Pop.value, LCD4linux.Mail4Pop.value, LCD4linux.Mail5Pop.value]
		U = [LCD4linux.Mail1User.value, LCD4linux.Mail2User.value, LCD4linux.Mail3User.value, LCD4linux.Mail4User.value, LCD4linux.Mail5User.value]
		P = [LCD4linux.Mail1Pass.value, LCD4linux.Mail2Pass.value, LCD4linux.Mail3Pass.value, LCD4linux.Mail4Pass.value, LCD4linux.Mail5Pass.value]
		C = [LCD4linux.Mail1Connect.value, LCD4linux.Mail2Connect.value, LCD4linux.Mail3Connect.value, LCD4linux.Mail4Connect.value, LCD4linux.Mail5Connect.value]
		if P == ["", "", "", "", ""]:
			return
		if int(strftime("%H")) == 0:
			PopMailUid = [["", "", ""], ["", "", ""], ["", "", ""], ["", "", ""], ["", "", ""]]
		for i in range(0, 5):
			if len(PopMail[i]) > 0 and PopMail[i][0][2] != "":
				PopMailUid[i][1] = PopMail[i][0][2]
		PopMail = [[], [], [], [], [], "Run"]
		for i in range(0, 5):
			if S[i].find(".") < S[i].rfind("."):
				L4log("Mailserver", S[i])
				if C[i] in ["0", "1"]:
					mailserver = None
					try:
						if C[i] == "0":
							mailserver = POP3_SSL(S[i])
						elif C[i] == "1":
							mailserver = POP3(S[i])
					except Exception:
						L4log("Error:", S[i])
						PopMail[i].append(["Server Error", "", "", ""])
						continue
					try:
						if mailserver is not None:
							ret = mailserver.user(U[i].split(":")[-1])
							L4log(ret)
							if str(ret).upper().find("OK") >= 0:
								ret = mailserver.pass_(P[i])
								L4log(ret)
							PopMailUid[i][2] = str(ret)
					except Exception:
						L4log("Error:", U[i])
						PopMail[i].append(["User Error", "", "", ""])
						continue
					try:
						if mailserver is not None:
							L4logE(mailserver.stat())
							for M in range(1, int(mailserver.stat()[0]) + 1):
								From = ""
								Subj = ""
								Date = ""
								for R in mailserver.retr(M)[1]:
									if str(R).upper().startswith("FROM:"):
										From = R[R.find(" "):].strip()
									elif str(R).upper().startswith("SUBJECT:"):
										Subj = R[R.find(" "):].strip()
									elif str(R).upper().startswith("DATE:") and LCD4linux.MailShowDate.value == True:
										Date = R[R.find(" "):].strip()
										Date = "- %s" % str(Date).split("+")[0].split(",")[-1].strip()
									if From != "" and Subj != "":
										break
								Subj = MailDecode(Subj)
								From = str(MailDecode(From)).replace('"', '')
								L4logE([From, Subj, mailserver.uidl()[1][M - 1].split()[1]])
								if From.rfind("<") > 1 and LCD4linux.MailHideMail.value == True:
									From = From[:From.rfind("<")]
								PopMail[i].append([From, Subj, mailserver.uidl()[1][M - 1].split()[1], Date])
					except Exception:
						L4log("Mail Error:", U[i])
						PopMail[i].append(["Mail Error", "", "", ""])
						L4log("Error:", format_exc())
						continue
					try:
						if mailserver:
							mailserver.quit()
							del mailserver
					except Exception:
						L4log("Mail-Error Quit")
				elif C[i] in ["2", "3"]:
					mailserver = None
					try:
						if C[i] == "2":
							mailserver = IMAP4_SSL(S[i])
						elif C[i] == "3":
							mailserver = IMAP4(S[i])
					except Exception:
						L4log("Error:", S[i])
						PopMail[i].append(["Server Error", "", "", ""])
						continue
					try:
						if mailserver is not None:
							ret = mailserver.login(U[i].split(":")[-1], P[i])
							L4log(ret)
							PopMailUid[i][2] = str(ret)
					except Exception:
						L4log("Error:", U[i])
						PopMail[i].append(["User Error", "", "", ""])
						continue
					try:
						if mailserver is not None:
							mailserver.select("inbox")
#							typ, data = mailserver.search(None, '(SINCE "{date}")'.format(date=Date))
							if str(LCD4linux.MailIMAPDays.value) == "0":
								typ, data = mailserver.search(None, 'ALL')
							else:
								l = getlocale()
								setlocale(LC_ALL, "C")
								Date = (date.today() - timedelta(int(LCD4linux.MailIMAPDays.value))).strftime(_("%d-%b-%Y"))
								typ, data = mailserver.search(None, '(SINCE {date})'.format(date=Date))
								setlocale(LC_ALL, l)
							ids = data[0]
							if ids is not None:
								id_list = ids.split()
								if len(id_list) > 0:
									L4logE("%s %s" % (typ, data))
									for M in id_list:
										Date = ""
										From = ""
										Subj = ""
										ID = ""
										typ, data = mailserver.fetch(str(M), "(RFC822)")
										for response_part in data:
											if isinstance(response_part, tuple):
												msg = message_from_string("%s" % response_part[1])
												if LCD4linux.MailShowDate.value == True and msg["date"] is not None:
													Date = "- " + msg["date"].split("+")[0].split(",")[-1].strip()
												Subj = msg["subject"]
												From = msg["from"]
												ID = msg["Message-ID"]
										Subj = MailDecode(Subj)
										From = MailDecode(From).replace('"', '')
										L4logE([From, Subj, ID])
										if From.rfind("<") > 1 and LCD4linux.MailHideMail.value == True:
											From = From[:From.rfind("<")]
										PopMail[i].append([From, Subj, ID, Date])
					except Exception:
						L4log("Mail Error:", U[i])
						PopMail[i].append(["Mail Error", "", "", ""])
						L4log("Error:", format_exc())
						continue
					try:
						if mailserver is not None:
							mailserver.close()
							del mailserver
					except Exception:
						L4log("Mail-Error Close")

				if len(PopMail[i]) > 0:
					PopMail[i] = list(reversed(PopMail[i]))
					L4logE("currend ID", PopMailUid[i][0])
					if PopMailUid[i][0] == "" or (PopMailUid[i][0] not in (e[2] for e in PopMail[i])):
						if len(PopMail[i]) > 1 or PopMailUid[i][0] != "-":
							PopMailUid[i][0] = PopMail[i][0][2]
							L4logE("new ID", PopMailUid[i][0])
				else:
					PopMailUid[i][0] = "-"
		PopMail[5] = ""

	def QuickLoad(self, s, Pim, P0, P1, P2, P3, P4):
		ShowPicture = getShowPicture(P0, Pim)
		if isfile(ShowPicture):
			try:
				Pimg = Image.open(ShowPicture)
				Pimg = Pimg.resize((P3, P4))
				if Pim == 1:
					Type = LCD4linux.LCDType1.value
				elif Pim == 2:
					Type = LCD4linux.LCDType2.value
				elif Pim == 3:
					Type = LCD4linux.LCDType3.value
				else:
					Type = ""
				if Type[0] in ["2", "3"] and virtBRI(Pim) not in [0, 10]:
					Pimg = ImageEnhance.Brightness(Pimg).enhance(virtBRI(Pim))
				s.im[Pim].paste(Pimg, (P1, P2))
				Pimg = None
			except Exception:
				L4log("Error Quick Pic")

	def QuickBild(self, s):
		pt = time()
		L4LWorker.QuickRunning = True
		try:
			if len(QuickList[0]) > 0 and s.im[1] is not None:
				for P in QuickList[0]:
					Brief1.put([self.QuickLoad, s, 1, P[0], P[1], P[2], P[3], P[4]])
				Brief1.join()
				Brief1.put([writeLCD1, s, 1, LCD4linux.BilderJPEGQuick.value, False])
			if len(QuickList[1]) > 0 and s.im[2] is not None:
				for P in QuickList[1]:
					Brief2.put([self.QuickLoad, s, 2, P[0], P[1], P[2], P[3], P[4]])
				Brief2.join()
				Brief2.put([writeLCD2, s, 2, LCD4linux.BilderJPEGQuick.value, False])
			if len(QuickList[2]) > 0 and s.im[3] is not None:
				for P in QuickList[2]:
					Brief2.put([self.QuickLoad, s, 3, P[0], P[1], P[2], P[3], P[4]])
				Brief3.join()
				Brief3.put([writeLCD3, s, 3, LCD4linux.BilderJPEGQuick.value, False])
			Brief1.join()
			Brief2.join()
			Brief3.join()
			L4LWorker.QuickRunning = False
			L4log("QuickTime: %.3f " % (time() - pt))
		except Exception:
			L4LWorker.QuickRunning = False
			L4log("QuickPic Error:", format_exc())
			try:
				open(CrashFile, "w").write(format_exc())
			except Exception:
				pass


class LCDdisplayMenu(Screen):
	skin = """
		<screen position="center,center" size="600,380" title="LCD4linux - Config" >
			<widget name="menu" position="10,20" size="580,350" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.list = []
		self.SetList()
		self["menu"] = MenuList(self.list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyOK,
			"cancel": self.cancel,
			"red": self.entfernen
		}, -1)

	def SetList(self):
		self.list = []
		self.list.append((_("Load Active Config-File"), "LoadConfig", ""))
		self.list.append((_("Load Defaults / Empty Config"), "LoadDefault", ""))
		self.list.append((_("Save Config to File... (%s)") % LCD4linux.ConfigPath.value, "SaveToConfig", ""))
		Cdir = sorted(glob(join(LCD4linux.ConfigPath.value, "*.lcd")))
		xx = 3
		for ii in Cdir:
			self.list.append((_("Load File : %s") % basename(ii), "LoadFile %d" % xx, ii))
			xx += 1

	def entfernen(self):
		current = self["menu"].getCurrent()
		if current:
			currentEntry = current[1]
			if currentEntry.startswith("LoadFile") and current[0].find(" : ") > 0:
				if isfile(current[2]):
					self.session.openWithCallback(self.askForDelete, MessageBox, _("Delete File?"), type=MessageBox.TYPE_YESNO, timeout=60)

	def keyOK(self):
		current = self["menu"].getCurrent()
		if current:
			currentEntry = current[1]
			L4log(currentEntry)
			if currentEntry == "LoadConfig":
				if isfile(LCD4config):
					L4log("Config-Load", LCD4config)
					LCD4linux.loadFromFile(LCD4default)
					LCD4linux.loadFromFile(LCD4config)
					LCD4linux.load()
			elif currentEntry == "SaveToConfig":
				self.session.openWithCallback(self.askForConfigName, InputBox, title="Save Filename", text="LCD4linux-%s" % (strftime("%Y%m%d_%H%M")), type=Input.TEXT)
			elif currentEntry.startswith("LoadFile"):
				if isfile(current[2]):
					L4LoadNewConfig(current[2])
			elif currentEntry == "LoadDefault" and isfile(LCD4default):
				L4log("Config-Load", LCD4default)
				LCD4linux.loadFromFile(LCD4default)
				LCD4linux.load()

	def askForConfigName(self, name):
		if name is not None and isdir(LCD4linux.ConfigPath.value):
			LCD4linux.save()
			LCD4linux.saveToFile(join(LCD4linux.ConfigPath.value, "%s.lcd" % name))
			self.list.append((_("Load File : %s") % ("%s.lcd" % name), "LoadFile", join(LCD4linux.ConfigPath.value, "%s.lcd" % name)))

	def askForDelete(self, retval):
		if (retval):
			current = self["menu"].getCurrent()
			if current and isfile(current[2]):
				currentEntry = current[1]
				i = int(currentEntry.split()[1])
				self.list[i] = (_("deleted"),) + self.list[i][1:]
				rmFile(current[2])

	def cancel(self):
		self.close(False, self.session)

	def selectionChanged(self):
		pass


class LCDdisplayFile(Screen):
	skin = """
		<screen position="center,center" size="620,460" title="Select File/Dir...">
			<widget source="File" render="Label" font="Regular;20" halign="center" position="5,0" size="610,100" transparent="1" valign="center" zPosition="4"/>
			<widget name="LCDfile" position="5,100" scrollbarMode="showOnDemand" size="610,312" zPosition="4"/>
			<eLabel backgroundColor="#555555" position="5,420" size="610,2" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="skin_default/buttons/green.png" position="0,425" size="140,40" zPosition="5"/>
			<eLabel font="Regular;18" halign="center" position="0,425" size="140,40" text="Select" transparent="1" valign="center" zPosition="6"/>
		</screen>"""

	def __init__(self, session, FileName="/tmp/none", showFiles=True, text="Text", matchingPattern=None):
		Screen.__init__(self, session)
		self.sesion = session
		if not FileName.startswith("/"):
			FileName = "/%s" % FileName
		self["File"] = StaticText(_("currently set : %s") % FileName)
		self["LCDfile"] = myFileList(FileName, showDirectories=True, showFiles=showFiles, useServiceRef=False, matchingPattern=matchingPattern)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.OneDescent,
			"back": self.NothingToDo,
			"green": self.SelectFile,
			"yellow": self.SelectFile
		}, -1)
		self.onLayoutFinish.append(self.OneDescent)

	def OneDescent(self):
		if self["LCDfile"].canDescent():
			self["LCDfile"].descent()

	def NothingToDo(self):
		self.close("", "")

	def SelectFile(self):
		dest = ""
		dest1 = ""
		if self["LCDfile"].getSelectionIndex() != 0:
			dest = self["LCDfile"].getCurrentDirectory()
			dest1 = self["LCDfile"].getFilename()
		self.close(dest, dest1)


class LCDscreenSwitch(Screen):
	skin = ""

	def __init__(self, session, args=0):
		self.session = session
		Screen.__init__(self, session)
		self.onLayoutFinish.append(self.layoutFinished)
		if LCD4linux.ScreenSwitch.value == ScreenActive[0] or ScreenActive[-3:] != ["", "", ""]:
			L4LElist.setScreen(0)
			L4LElist.setHold(False)
			L4LElist.setHoldKey(False)
			setScreenActive("1")
			L4LElist.setRefresh()
		else:
			if str(LCD4linux.ScreenSwitchLCD.value) == "0":
				L4LElist.setScreen(LCD4linux.ScreenSwitch.value)
				L4LElist.setHold(True)
			else:
				L4LElist.setScreen(LCD4linux.ScreenSwitch.value, LCD4linux.ScreenSwitchLCD.value)
			L4LElist.setHoldKey(True)
			L4LElist.setRefresh()

	def layoutFinished(self):
		L4logE("Screen Switch")
		self.close(True, self.session)


class LCDdisplayConfig(ConfigListScreen, Screen):
	skin = ""

	def __init__(self, session, args=0):
		global ConfigMode
		global OSDon
		size_w = getDesktop(0).size().width() - 100
		size_h = getDesktop(0).size().height() - 100  # 870x400 conf 600x328 (25*Lines)
		conf_w = int(size_w / 2)
		if size_w < 700:
			size_w = 600
			conf_w = 600
		self.ConfLines = (size_h - 72) // 25
		conf_h = self.ConfLines * 25
		int_y = size_h - 65
		key_y = size_h - 40
		key_x = int((conf_w - 40) / 4)
		pic_w = size_w - conf_w
		if LCD4linux.LCDType3.value != "00":  # NOSONAR
			pic_h = int(size_h / 2)  # replace 'pic_h = int(size_h / 3)' in case the current skin supports only 2 LCDs in the GUI-preview
		else:
			pic_h = int(size_h / 2)
		pic_h2 = pic_h * 2
		skin = """
			<screen position="center,%d" size="%d,%d" title="LCD4linux Settings" >
			<widget name="config" position="0,0" size="%d,%d" scrollbarMode="showOnDemand" enableWrapAround="1" />
			<widget source="introduction" render="Label" position="5,%d" size="%d,30" zPosition="10" font="Regular;21" halign="center" valign="center" backgroundColor="#25062748" transparent="1" />

			<widget name="key_red" position="%d,%d" size="%d,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_green" position="%d,%d" size="%d,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_yellow" position="%d,%d" size="%d,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_blue" position="%d,%d" size="%d,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/>

			<ePixmap name="red"    position="%d,%d"   zPosition="2" size="%d,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="%d,%d" zPosition="2" size="%d,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="%d,%d" zPosition="2" size="%d,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="%d,%d" zPosition="2" size="%d,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/key_menu.png" position="%d,%d" zPosition="4" size="35,25"  transparent="1" alphatest="on" />

			<widget source="Version" render="Label" position="%d,%d" size="100,20" zPosition="1" font="Regular;11" halign="right" valign="center" backgroundColor="#25062748" transparent="1" />
			<widget source="LibUSB" render="Label" position="%d,%d" size="100,20" zPosition="1" font="Regular;11" halign="right" valign="center" foregroundColor="red" backgroundColor="#25062748" transparent="1" />
			<widget source="About" render="Label" position="%d,%d" size="100,20" zPosition="1" font="Regular;10" halign="right" valign="center" backgroundColor="#25062748" transparent="1" />

			<widget name="LCD1" position="%d,%d" zPosition="1" size="%d,%d" transparent="1" alphatest="on" />
			<widget name="LCD2" position="%d,%d" zPosition="1" size="%d,%d" transparent="1" alphatest="on" />
			<widget name="LCD3" position="%d,%d" zPosition="1" size="%d,%d" transparent="1" alphatest="on" />
			<widget source="LCD1text" render="Label" position="%d,%d" size="200,20" zPosition="1" font="Regular;11" halign="left" valign="center" backgroundColor="#25062748" transparent="1" />
			<widget source="LCD2text" render="Label" position="%d,%d" size="200,20" zPosition="1" font="Regular;11" halign="left" valign="center" backgroundColor="#25062748" transparent="1" />
			<widget source="LCD3text" render="Label" position="%d,%d" size="200,20" zPosition="1" font="Regular;11" halign="left" valign="center" backgroundColor="#25062748" transparent="1" />
			</screen>""" % (75, size_w, size_h, conf_w, conf_h, int_y, conf_w - 10, 0, key_y, key_x, key_x, key_y, key_x, 2 * key_x, key_y, key_x, 3 * key_x, key_y, key_x, 0, key_y, key_x, key_x, key_y, key_x, 2 * key_x, key_y, key_x, 3 * key_x, key_y, key_x,
			4 * key_x, key_y + 15, conf_w - 100, key_y - 10, conf_w - 100, key_y - 30, conf_w - 100, key_y - 30, conf_w, 0, pic_w, pic_h, conf_w, pic_h, pic_w, pic_h, conf_w, pic_h2, pic_w, pic_h, conf_w, 5, conf_w, pic_h + 5, conf_w, pic_h2 + 5)
		self.skin = skin
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("LCD4linux Settings"))
		L4log("init Start")
		ConfigMode = True
		OSDon = 0
		getBilder()
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
		self.toggle = time() - 0.5  # delay in order to avoid GUI-start in mode 'idle'
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
		ConfigListScreen.__init__(self, self.list, on_change=self.selectionChanged)
		self.PicTimer = eTimer()
		self.PicTimer.callback.append(self.showpic)
		self["introduction"] = StaticText()
		self["Version"] = StaticText((Version if L4LElist.getVersion() == True else Version + "") + " (" + _("Mode") + ": Py" + ("3" if PY3 else "2") + ")")
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
		self["key_blue"] = Button(_("Set On >>"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions", "EPGSelectActions", "HelpActions", "InfobarSeekActions"],
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
		self.mode = _("On")
		self.LastSelect = "1"
		self.SetList()
		self.mode = _("Media")
		self.LastSelect = "2"
		self.SetList()
		self.mode = _("Idle")
		self.LastSelect = "3"
		self.SetList()
		self.mode = _("Global")
		self.LastSelect = "4"
		self.SetList()
		if self.selectionChanged not in self["config"].onSelectionChanged:
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
		self["config"].l.setSeperation(int(self["config"].l.getItemSize().width() * .7))  # use 30% of list width for sliders
		self.mode = _("Idle")
		self.LastSelect = "5"
		self.Page()
		self.selectionChanged()

	def NextScreenKey(self):
		NextScreen(True)

	def ResetInfos(self):
		global FritzList
		global PopMailUid
		FritzList = []
		PopMailUid = [["", "", ""], ["", "", ""], ["", "", ""], ["", "", ""], ["", "", ""]]
		if Briefkasten.qsize() <= 3:
			Briefkasten.put(6)

	def showpic(self):
		self.PicTimer.stop()
		ff = False
		fn = "%s.jpg" % PIC
		try:
			if isfile(fn):
				ft = stat(fn).st_mtime
				ff = True
				if ft != self.mtime1:
					self.picload.startDecode(fn)
					self.mtime1 = ft
			else:
				fn = "%s.png" % PIC
				ft = 0.0
				if isfile(fn):
					ft = stat(fn).st_mtime
					ff = True
					if ft != self.mtime1:
						self.picload.startDecode(fn)
						self.mtime1 = ft
		except Exception:
			L4log("Error Pic1 not found")
		if ff == False:
			self["LCD1text"].setText(_("no LCD1 Picture-File"))
			self["LCD1"].hide()
		else:
			self["LCD1text"].setText("")
		ff = False
		fn = "%s.jpg" % PIC2
		try:
			if isfile(fn):
				ft = stat(fn).st_mtime
				ff = True
				if ft != self.mtime2:
					self.picload2.startDecode(fn)
					self.mtime2 = ft
			else:
				fn = "%s.png" % PIC2
				ft = 0.0
				if isfile(fn):
					ft = stat(fn).st_mtime
					ff = True
					if ft != self.mtime2:
						self.picload2.startDecode(fn)
						self.mtime2 = ft
		except Exception:
			L4log("Error Pic2 not found")
		if ff == False:
			self["LCD2text"].setText(_("no LCD2 Picture-File"))
			self["LCD2"].hide()
		else:
			self["LCD2text"].setText("")
		if LCD4linux.LCDType3.value != "00":
			ff = False
			fn = "%s.jpg" % PIC3
			try:
				if isfile(fn):
					ft = stat(fn).st_mtime
					ff = True
					if ft != self.mtime3:
						self.picload3.startDecode(fn)
						self.mtime3 = ft
				else:
					fn = "%s.png" % PIC3
					ft = 0.0
					if isfile(fn):
						ft = stat(fn).st_mtime
						ff = True
						if ft != self.mtime3:
							self.picload3.startDecode(fn)
							self.mtime3 = ft
			except Exception:
				L4log("Error Pic3 not found")
			if ff == False:
				self["LCD3text"].setText(_("no LCD3 Picture-File"))
				self["LCD3"].hide()
			else:
				self["LCD3text"].setText("")
		self.PicTimer.start(500, True)

	def setPictureCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
			self["LCD1"].instance.setPixmap(ptr)
			self["LCD1"].show()

	def setPictureCB2(self, picInfo=None):
		ptr = self.picload2.getData()
		if ptr is not None:
			self["LCD2"].instance.setPixmap(ptr)
			self["LCD2"].show()

	def setPictureCB3(self, picInfo=None):
		ptr = self.picload3.getData()
		if ptr is not None:
			self["LCD3"].instance.setPixmap(ptr)
			self["LCD3"].show()

	def SetupMenu(self):
		self.session.open(LCDdisplayMenu)

	def Exchange(self):
		Exchange()

	def SetList(self):
		L4log("SetList", self.mode)
		if (self.Aktuell.startswith("-") or self.LastSelectT == self.LastSelect) and not self.Aktuell.startswith("-  "):
			return
		self.LastSelectT = self.LastSelect
		if self.mode == _("Global"):
			self.list1 = []
			self.list1.append(getConfigListEntry(_("LCD4linux enabled"), LCD4linux.Enable))
			self.list1.append(getConfigListEntry(_("LCD 1 Type"), LCD4linux.LCDType1))
			self.list1.append(getConfigListEntry(_("- LCD 1 Rotate"), LCD4linux.LCDRotate1))
			self.list1.append(getConfigListEntry(_("- LCD 1 Background Color"), LCD4linux.LCDColor1))
			self.list1.append(getConfigListEntry(_("- LCD 1 Background-Picture [ok]>"), LCD4linux.LCDBild1))
			self.list1.append(getConfigListEntry(_("- LCD 1 Brightness"), LCD4linux.Helligkeit))
			self.list1.append(getConfigListEntry(_("- LCD 1 Night Reduction"), LCD4linux.Night))
			self.list1.append(getConfigListEntry(_("- LCD 1 Refresh"), LCD4linux.LCDRefresh1))
			self.list1.append(getConfigListEntry(_("LCD 2 Type"), LCD4linux.LCDType2))
			if LCD4linux.LCDType2.value != "00":
				self.list1.append(getConfigListEntry(_("- LCD 2 Rotate"), LCD4linux.LCDRotate2))
				self.list1.append(getConfigListEntry(_("- LCD 2 Background Color"), LCD4linux.LCDColor2))
				self.list1.append(getConfigListEntry(_("- LCD 2 Background-Picture [ok]>"), LCD4linux.LCDBild2))
				self.list1.append(getConfigListEntry(_("- LCD 2 Brightness"), LCD4linux.Helligkeit2))
				self.list1.append(getConfigListEntry(_("- LCD 2 Night Reduction"), LCD4linux.Night2))
				self.list1.append(getConfigListEntry(_("- LCD 2 Refresh"), LCD4linux.LCDRefresh2))
			self.list1.append(getConfigListEntry(_("LCD 3 Type"), LCD4linux.LCDType3))
			if LCD4linux.LCDType3.value != "00":
				self.list1.append(getConfigListEntry(_("- LCD 3 Rotate"), LCD4linux.LCDRotate3))
				self.list1.append(getConfigListEntry(_("- LCD 3 Background Color"), LCD4linux.LCDColor3))
				self.list1.append(getConfigListEntry(_("- LCD 3 Background-Picture [ok]>"), LCD4linux.LCDBild3))
				self.list1.append(getConfigListEntry(_("- LCD 3 Brightness"), LCD4linux.Helligkeit3))
				self.list1.append(getConfigListEntry(_("- LCD 3 Night Reduction"), LCD4linux.Night3))
				self.list1.append(getConfigListEntry(_("- LCD 3 Refresh"), LCD4linux.LCDRefresh3))
			if LCD4linux.LCDType1.value[0] == "5" or LCD4linux.LCDType2.value[0] == "5" or LCD4linux.LCDType3.value[0] == "5":
				self.list1.append(getConfigListEntry(_("Box-Skin-LCD Dimension"), LCD4linux.xmlLCDType))
				self.list1.append(getConfigListEntry(_("Box-Skin-LCD Offset"), LCD4linux.xmlOffset))
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
				self.list1.append(getConfigListEntry(_("- Clear Key"), LCD4linux.PopupKey))
				self.list1.append(getConfigListEntry(_("- Font Size"), LCD4linux.PopupSize))
				self.list1.append(getConfigListEntry(_("- Position"), LCD4linux.PopupPos))
				self.list1.append(getConfigListEntry(_("- Alignment"), LCD4linux.PopupAlign))
				self.list1.append(getConfigListEntry(_("- Color"), LCD4linux.PopupColor))
				self.list1.append(getConfigListEntry(_("- Background Color"), LCD4linux.PopupBackColor))
				self.list1.append(getConfigListEntry(_("- Font"), LCD4linux.PopupFont))
#			if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4":
#				self.list1.append(getConfigListEntry(_("Internal TFT Active"), LCD4linux.LCDTFT))
			self.list1.append(getConfigListEntry(_("Active Screen"), LCD4linux.ScreenActive))
			self.list1.append(getConfigListEntry(_("Screen Switch Select - Screen"), LCD4linux.ScreenSwitch))
			self.list1.append(getConfigListEntry(_("Screen Switch Select - LCD"), LCD4linux.ScreenSwitchLCD))
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
			self.list1.append(getConfigListEntry(_("Picture Type [only Picture]"), LCD4linux.BilderTyp))
			self.list1.append(getConfigListEntry(_("Background-Picture Type"), LCD4linux.BilderBackground))
			self.list1.append(getConfigListEntry(_("Weather API"), LCD4linux.WetterApi))
			self.list1.append(getConfigListEntry(_("Weather API-Key OpenWeatherMap"), LCD4linux.WetterApiKeyOpenWeatherMap))
			self.list1.append(getConfigListEntry(_("Weather API-ID Key WeatherUnlocked"), LCD4linux.WetterApiKeyWeatherUnlocked))
			self.list1.append(getConfigListEntry(_("Weather City"), LCD4linux.WetterCity))
			self.list1.append(getConfigListEntry(_("Weather City 2"), LCD4linux.Wetter2City))
			self.list1.append(getConfigListEntry(_("Weather-Icon-Path [ok]>"), LCD4linux.WetterPath))
			self.list1.append(getConfigListEntry(_("Weather-Icon Zoom"), LCD4linux.WetterIconZoom))
			self.list1.append(getConfigListEntry(_("Weather Low Temperature Color"), LCD4linux.WetterLowColor))
			self.list1.append(getConfigListEntry(_("Weather High Temperature Color"), LCD4linux.WetterHighColor))
			self.list1.append(getConfigListEntry(_("Weather Transparency"), LCD4linux.WetterTransparenz))
			self.list1.append(getConfigListEntry(_("Weather Wind speed unit"), LCD4linux.WetterWind))
			self.list1.append(getConfigListEntry(_("Weather Wind Info Lines"), LCD4linux.WetterWindLines))
			self.list1.append(getConfigListEntry(_("Weather Rain Chance"), LCD4linux.WetterRain))
			if LCD4linux.WetterRain.value != "false":
				self.list1.append(getConfigListEntry(_("- Rain Zoom"), LCD4linux.WetterRainZoom))
				self.list1.append(getConfigListEntry(_("- Rain Color"), LCD4linux.WetterRainColor))
				self.list1.append(getConfigListEntry(_("- Rain use Color 2 from"), LCD4linux.WetterRainColor2use))
				self.list1.append(getConfigListEntry(_("- Rain Color 2"), LCD4linux.WetterRainColor2))
			self.list1.append(getConfigListEntry(_("Weather Humidity Color"), LCD4linux.WetterHumColor))
			self.list1.append(getConfigListEntry(_("Weather Lines"), LCD4linux.WetterLine))
			self.list1.append(getConfigListEntry(_("Weather Trendarrows"), LCD4linux.WetterTrendArrows))
			self.list1.append(getConfigListEntry(_("Weather Extra Infos"), LCD4linux.WetterExtra))
			if LCD4linux.WetterExtra.value:
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
			self.list1.append(getConfigListEntry(_("FritzCall Number of Lines per Entry"), LCD4linux.FritzLineType))
			self.list1.append(getConfigListEntry(_("FritzCall Number of List Entries"), LCD4linux.FritzLines))
			self.list1.append(getConfigListEntry(_("FritzCall Number of Pictures"), LCD4linux.FritzPictures))
			self.list1.append(getConfigListEntry(_("FritzCall Picture Orientation"), LCD4linux.FritzPictureType))
			self.list1.append(getConfigListEntry(_("FritzCall Picture Transparency"), LCD4linux.FritzPictureTransparenz))
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
			self.list1.append(getConfigListEntry(_("Calendar Saturday Color"), LCD4linux.CalSaColor))
			self.list1.append(getConfigListEntry(_("Calendar Sunday Color"), LCD4linux.CalSuColor))
			self.list1.append(getConfigListEntry(_("Calendar Line Thickness"), LCD4linux.CalLine))
			self.list1.append(getConfigListEntry(_("Calendar Day Event Preview"), LCD4linux.CalDays))
			self.list1.append(getConfigListEntry(_("Calendar Timezone Correction"), LCD4linux.CalTimeZone))
			self.list1.append(getConfigListEntry(_("Calendar Transparency"), LCD4linux.CalTransparenz))
			self.list1.append(getConfigListEntry(_("Calendar Poll Interval"), LCD4linux.CalTime))
			self.list1.append(getConfigListEntry(_("Tuner Color"), LCD4linux.TunerColor))
			self.list1.append(getConfigListEntry(_("Tuner Color Active"), LCD4linux.TunerColorActive))
			self.list1.append(getConfigListEntry(_("Tuner Color On"), LCD4linux.TunerColorOn))
			self.list1.append(getConfigListEntry(_("Service search first"), LCD4linux.ServiceSearch))
			self.list1.append(getConfigListEntry(_("DVB-T Signal-Quality Correction"), LCD4linux.DVBTCorrection))
			self.list1.append(getConfigListEntry(_("Font global [ok]>"), LCD4linux.Font))
			self.list1.append(getConfigListEntry(_("Font 1 [ok]>"), LCD4linux.Font1))
			self.list1.append(getConfigListEntry(_("Font 2 [ok]>"), LCD4linux.Font2))
			self.list1.append(getConfigListEntry(_("Font 3 [ok]>"), LCD4linux.Font3))
			self.list1.append(getConfigListEntry(_("Font 4 [ok]>"), LCD4linux.Font4))
			self.list1.append(getConfigListEntry(_("Font 5 [ok]>"), LCD4linux.Font5))
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
			self.list1.append(getConfigListEntry(_("Mail IMAP limit to last days"), LCD4linux.MailIMAPDays))
			self.list1.append(getConfigListEntry(_("Mail Show Empty Mailboxes"), LCD4linux.MailShow0))
			self.list1.append(getConfigListEntry(_("Mail Show Date"), LCD4linux.MailShowDate))
			self.list1.append(getConfigListEntry(_("Mail Hide Mailadress"), LCD4linux.MailHideMail))
			self.list1.append(getConfigListEntry(_("Remote Box 1 [Displayname:]IP/Name"), LCD4linux.RBoxName1))
			self.list1.append(getConfigListEntry(_("Remote Box 2 [Displayname:]IP/Name"), LCD4linux.RBoxName2))
			self.list1.append(getConfigListEntry(_("Remote Box 3 [Displayname:]IP/Name"), LCD4linux.RBoxName3))
			self.list1.append(getConfigListEntry(_("Remote Box 4 [Displayname:]IP/Name"), LCD4linux.RBoxName4))
			self.list1.append(getConfigListEntry(_("Remote Box 5 [Displayname:]IP/Name"), LCD4linux.RBoxName5))
			self.list1.append(getConfigListEntry(_("Remote Box Poll every Minutes"), LCD4linux.RBoxRefresh))
			self.list1.append(getConfigListEntry(_("Remote Box Timer [Displayname:]IP/Name"), LCD4linux.RBoxTimerName1))
			self.list1.append(getConfigListEntry(_("Remote Box Timer Poll every Minutes"), LCD4linux.RBoxTimerRefresh))
			self.list1.append(getConfigListEntry(_("WWW Converter Poll Interval"), LCD4linux.WwwTime))
			self.list1.append(getConfigListEntry(_("WWW Converter Usage"), LCD4linux.WwwApiUsage))
			self.list1.append(getConfigListEntry(_("WWW ApiKey from cloudconvert.org"), LCD4linux.WwwApiKeyCloudconvert))
			self.list1.append(getConfigListEntry(_("WWW ApiKey from convertapi.com"), LCD4linux.WwwApiKeyConvertapi))
			self.list1.append(getConfigListEntry(_("WebIF Refresh [s]"), LCD4linux.WebIfRefresh))
			self.list1.append(getConfigListEntry(_("WebIF Refresh Type"), LCD4linux.WebIfType))
			self.list1.append(getConfigListEntry(_("WebIF Init Delay"), LCD4linux.WebIfInitDelay))
			self.list1.append(getConfigListEntry(_("WebIF IP Allow"), LCD4linux.WebIfAllow))
			self.list1.append(getConfigListEntry(_("WebIF IP Deny"), LCD4linux.WebIfDeny))
			self.list1.append(getConfigListEntry(_("WebIF Design"), LCD4linux.WebIfDesign))
			self.list1.append(getConfigListEntry(_("Save as Picture for WebIF"), LCD4linux.SavePicture))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 1 enable"), LCD4linux.MJPEGenable1))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 1 Port"), LCD4linux.MJPEGport1))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 1 Virtual Brightness"), LCD4linux.MJPEGvirtbri1))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 2 enable"), LCD4linux.MJPEGenable2))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 2 Port"), LCD4linux.MJPEGport2))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 2 Virtual Brightness"), LCD4linux.MJPEGvirtbri2))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 3 enable"), LCD4linux.MJPEGenable3))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 3 Port"), LCD4linux.MJPEGport3))
			self.list1.append(getConfigListEntry(_("MJPEG Stream LCD 3 Virtual Brightness"), LCD4linux.MJPEGvirtbri3))
#			self.list1.append(getConfigListEntry(_("MJPEG Boundary Mode"), LCD4linux.MJPEGMode))
			self.list1.append(getConfigListEntry(_("MJPEG Cycle"), LCD4linux.MJPEGCycle))
			self.list1.append(getConfigListEntry(_("MJPEG Restart on Error"), LCD4linux.MJPEGRestart))
			self.list1.append(getConfigListEntry(_("MJPEG Header Mode"), LCD4linux.MJPEGHeader))
			self.list1.append(getConfigListEntry(_("Show Streams '4097; 5001...5003' in Mode"), LCD4linux.Streaming))
			self.list1.append(getConfigListEntry(_("Sonos IP"), LCD4linux.SonosIP))
			self.list1.append(getConfigListEntry(_("Sonos Ping Timeout [ms]"), LCD4linux.SonosPingTimeout))
			self.list1.append(getConfigListEntry(_("Sonos Play Check"), LCD4linux.SonosCheckTimer))
			self.list1.append(getConfigListEntry(_("Sonos Refresh [s]"), LCD4linux.SonosTimer))
			self.list1.append(getConfigListEntry(_("BlueSound IP"), LCD4linux.BlueIP))
			self.list1.append(getConfigListEntry(_("BlueSound Ping Timeout [ms]"), LCD4linux.BluePingTimeout))
			self.list1.append(getConfigListEntry(_("BlueSound Play Check"), LCD4linux.BlueCheckTimer))
			self.list1.append(getConfigListEntry(_("BlueSound Refresh [s]"), LCD4linux.BlueTimer))
			self.list1.append(getConfigListEntry(_("MusicCast IP"), LCD4linux.YMCastIP))
			self.list1.append(getConfigListEntry(_("MusicCast Server IP [optional]"), LCD4linux.YMCastServerIP))
			self.list1.append(getConfigListEntry(_("MusicCast Ping Timeout [ms]"), LCD4linux.YMCastPingTimeout))
			self.list1.append(getConfigListEntry(_("MusicCast Play Check"), LCD4linux.YMCastCheckTimer))
			self.list1.append(getConfigListEntry(_("MusicCast Refresh [s]"), LCD4linux.YMCastTimer))
			self.list1.append(getConfigListEntry(_("MusicCast Cover"), LCD4linux.YMCastCover))
			self.list1.append(getConfigListEntry(_("LCD Custom Width"), LCD4linux.SizeW))
			self.list1.append(getConfigListEntry(_("LCD Custom Height"), LCD4linux.SizeH))
			self.list1.append(getConfigListEntry(_("LCD Custom Width 2"), LCD4linux.SizeW2))
			self.list1.append(getConfigListEntry(_("LCD Custom Height 2"), LCD4linux.SizeH2))
			self.list1.append(getConfigListEntry(_("LCD Off when shutdown"), LCD4linux.LCDshutdown))
			self.list1.append(getConfigListEntry(_("Timing ! calc all Times to Time/5*2 in Fastmode"), LCD4linux.FastMode))
			self.list1.append(getConfigListEntry(_("Display Delay [ms]"), LCD4linux.Delay))
			self.list1.append(getConfigListEntry(_("Threads per LCD"), LCD4linux.ElementThreads))
			self.list1.append(getConfigListEntry(_("Show Crash Corner"), LCD4linux.Crash))
			self.list1.append(getConfigListEntry(_("Show 'no ....' Messages"), LCD4linux.ShowNoMsg))
			self.list1.append(getConfigListEntry(_("Storage-Devices: Force Read"), LCD4linux.DevForceRead))
			self.list1.append(getConfigListEntry(_("Storage-Devices: Color Back"), LCD4linux.DevBackColor))
			self.list1.append(getConfigListEntry(_("Storage-Devices: Color Bar"), LCD4linux.DevBarColor))
			self.list1.append(getConfigListEntry(_("Storage-Devices: Color Full"), LCD4linux.DevFullColor))
			self.list1.append(getConfigListEntry(_("Network Check active"), LCD4linux.NETworkCheckEnable))
			self.list1.append(getConfigListEntry(_("Switch FrameBuffer [if possible]"), LCD4linux.SwitchToFB2))
			self.list1.append(getConfigListEntry(_("Config Backup Path [ok]>"), LCD4linux.ConfigPath))
			self.list1.append(getConfigListEntry(_("Config Restore All Settings"), LCD4linux.ConfigWriteAll))
			self.list1.append(getConfigListEntry(_("Debug-Logging > /tmp/L4log.txt"), LCD4linux.EnableEventLog))
			self["config"].setList(self.list1)
		elif self.mode == _("On"):
			self.list2 = []
			self.list2.append(getConfigListEntry(_("- Backlight Off [disable set Off=On]"), LCD4linux.LCDoff))
			self.list2.append(getConfigListEntry(_("- Backlight On"), LCD4linux.LCDon))
			self.list2.append(getConfigListEntry(_("- Backlight Weekend Off [disable set Off=On]"), LCD4linux.LCDWEoff))
			self.list2.append(getConfigListEntry(_("- Backlight Weekend On"), LCD4linux.LCDWEon))
			self.list2.append(getConfigListEntry(_("- LCD Auto-OFF"), LCD4linux.AutoOFF))
			self.list2.append(getConfigListEntry(_("Background"), LCD4linux.Background1))
			if LCD4linux.Background1.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Background1LCD))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Background1Color))
				self.list2.append(getConfigListEntry(_("- Picture [ok]>"), LCD4linux.Background1Bild))
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
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.ChannelLen))
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
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.ProgLen))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.ProgSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ProgColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ProgShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ProgFont))
			self.list2.append(getConfigListEntry(_("Program Info 2"), LCD4linux.Prog2))
			if LCD4linux.Prog2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Prog2LCD))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.Prog2Type))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.Prog2Size))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.Prog2Lines))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Prog2Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Prog2Align))
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.Prog2Len))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.Prog2Split))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Prog2Color))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.Prog2Shadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.Prog2Font))
			self.list2.append(getConfigListEntry(_("Next Program Info"), LCD4linux.ProgNext))
			if LCD4linux.ProgNext.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ProgNextLCD))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.ProgNextType))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.ProgNextSize))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.ProgNextLines))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ProgNextPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ProgNextAlign))
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.ProgNextLen))
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
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.DescLen))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.DescSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.DescColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.DescShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.DescFont))
				self.list2.append(getConfigListEntry(_("- use Info when empty"), LCD4linux.DescUseInfo))
			self.list2.append(getConfigListEntry(_("Progress Bar"), LCD4linux.Progress))
			if LCD4linux.Progress.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ProgressLCD))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.ProgressType))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.ProgressShadow2))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.ProgressSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ProgressPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ProgressAlign))
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.ProgressLen))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ProgressColor))
				self.list2.append(getConfigListEntry(_("- Color Text"), LCD4linux.ProgressColorText))
				self.list2.append(getConfigListEntry(_("- Border"), LCD4linux.ProgressBorder))
				self.list2.append(getConfigListEntry(_("- Shaded"), LCD4linux.ProgressShadow))
				self.list2.append(getConfigListEntry(_("- Unit min"), LCD4linux.ProgressMinutes))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ProgressFont))
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
			self.list2.append(getConfigListEntry(_("Informations 2"), LCD4linux.Info2))
			if LCD4linux.Info2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Info2LCD))
				self.list2.append(getConfigListEntry(_("- Tunerinfo"), LCD4linux.Info2Tuner))
				self.list2.append(getConfigListEntry(_("- Sensors"), LCD4linux.Info2Sensor))
				self.list2.append(getConfigListEntry(_("- CPU"), LCD4linux.Info2CPU))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.Info2Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Info2Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Info2Align))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.Info2Split))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.Info2Lines))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.Info2Color))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.Info2Shadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.Info2Font))
			self.list2.append(getConfigListEntry(_("Signal Quality Bar"), LCD4linux.Signal))
			if LCD4linux.Signal.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.SignalLCD))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.SignalSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.SignalPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.SignalAlign))
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.SignalLen))
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
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.TimerType2))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.TimerPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.TimerAlign))
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.TimerLen))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.TimerSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.TimerColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.TimerShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.TimerFont))
			self.list2.append(getConfigListEntry(_("Volume"), LCD4linux.Vol))
			if LCD4linux.Vol.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.VolLCD))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.VolSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.VolPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.VolAlign))
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.VolLen))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.VolSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.VolColor))
				self.list2.append(getConfigListEntry(_("- Shaded"), LCD4linux.VolShadow))
			self.list2.append(getConfigListEntry(_("Mute"), LCD4linux.Mute))
			if LCD4linux.Mute.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.MuteLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.MuteSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.MutePos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.MuteAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MuteSplit))
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
				self.list2.append(getConfigListEntry(_("- Timeout [ms]"), LCD4linux.PingTimeout))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName1))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName2))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName3))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName4))
				self.list2.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.PingName5))
			self.list2.append(getConfigListEntry(_("External IP Address"), LCD4linux.ExternalIp))
			if LCD4linux.ExternalIp.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.ExternalIpLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.ExternalIpSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.ExternalIpPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.ExternalIpAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.ExternalIpSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.ExternalIpColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.ExternalIpBackColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.ExternalIpShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.ExternalIpFont))
				self.list2.append(getConfigListEntry(_("- external IP URL"), LCD4linux.ExternalIpUrl))
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
				self.list2.append(getConfigListEntry(_("- free Warning"), LCD4linux.DevWarning))
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
				self.list2.append(getConfigListEntry(_("- Station"), LCD4linux.NetAtmoStation))
				self.list2.append(getConfigListEntry(_("- Module"), LCD4linux.NetAtmoModule))
				self.list2.append(getConfigListEntry(_("- Module userdefined"), LCD4linux.NetAtmoModuleUser))
				self.list2.append(getConfigListEntry(_("- Base"), LCD4linux.NetAtmoBasis))
				self.list2.append(getConfigListEntry(_("- Name"), LCD4linux.NetAtmoName))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmoType))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmoType2))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.NetAtmoColor))
				self.list2.append(getConfigListEntry(_("- Color 1"), LCD4linux.NetAtmoColor2))
				self.list2.append(getConfigListEntry(_("- Color 2"), LCD4linux.NetAtmoColor3))
				self.list2.append(getConfigListEntry(_("- Color 3"), LCD4linux.NetAtmoColor4))
				self.list2.append(getConfigListEntry(_("- Color 4"), LCD4linux.NetAtmoColor5))
				self.list2.append(getConfigListEntry(_("- Color 5"), LCD4linux.NetAtmoColor6))
				self.list2.append(getConfigListEntry(_("- Color 6"), LCD4linux.NetAtmoColor7))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.NetAtmoShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.NetAtmoFont))
			self.list2.append(getConfigListEntry(_("Netatmo 2"), LCD4linux.NetAtmo2))
			if LCD4linux.NetAtmo2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.NetAtmo2LCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.NetAtmo2Pos))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.NetAtmo2Size))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.NetAtmo2Align))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.NetAtmo2Split))
				self.list2.append(getConfigListEntry(_("- Station"), LCD4linux.NetAtmo2Station))
				self.list2.append(getConfigListEntry(_("- Module"), LCD4linux.NetAtmo2Module))
				self.list2.append(getConfigListEntry(_("- Module userdefined"), LCD4linux.NetAtmo2ModuleUser))
				self.list2.append(getConfigListEntry(_("- Base"), LCD4linux.NetAtmo2Basis))
				self.list2.append(getConfigListEntry(_("- Name"), LCD4linux.NetAtmo2Name))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmo2Type))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmo2Type2))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.NetAtmo2Color))
				self.list2.append(getConfigListEntry(_("- Color 1"), LCD4linux.NetAtmo2Color2))
				self.list2.append(getConfigListEntry(_("- Color 2"), LCD4linux.NetAtmo2Color3))
				self.list2.append(getConfigListEntry(_("- Color 3"), LCD4linux.NetAtmo2Color4))
				self.list2.append(getConfigListEntry(_("- Color 4"), LCD4linux.NetAtmo2Color5))
				self.list2.append(getConfigListEntry(_("- Color 5"), LCD4linux.NetAtmo2Color6))
				self.list2.append(getConfigListEntry(_("- Color 6"), LCD4linux.NetAtmo2Color7))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.NetAtmo2Shadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.NetAtmo2Font))
			self.list2.append(getConfigListEntry(_("Netatmo CO2 Indicator"), LCD4linux.NetAtmoCO2))
			if LCD4linux.NetAtmoCO2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.NetAtmoCO2LCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.NetAtmoCO2Pos))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.NetAtmoCO2Size))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.NetAtmoCO2Align))
				self.list2.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.NetAtmoCO2Len))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.NetAtmoCO2Split))
				self.list2.append(getConfigListEntry(_("- Station"), LCD4linux.NetAtmoCO2Station))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmoCO2Type))
			self.list2.append(getConfigListEntry(_("Netatmo Comfort Indicator"), LCD4linux.NetAtmoIDX))
			if LCD4linux.NetAtmoIDX.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.NetAtmoIDXLCD))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.NetAtmoIDXPos))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.NetAtmoIDXSize))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.NetAtmoIDXAlign))
				self.list2.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.NetAtmoIDXLen))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.NetAtmoIDXSplit))
				self.list2.append(getConfigListEntry(_("- Station"), LCD4linux.NetAtmoIDXStation))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.NetAtmoIDXType))
			self.list2.append(getConfigListEntry(_("Moonphase"), LCD4linux.Moon))
			if LCD4linux.Moon.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.MoonLCD))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.MoonSize))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.MoonFontSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.MoonPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.MoonAlign))
				self.list2.append(getConfigListEntry(_("- Infolines"), LCD4linux.MoonInfos))
				self.list2.append(getConfigListEntry(_("- Trendarrows"), LCD4linux.MoonTrends))
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
				self.list2.append(getConfigListEntry(_("- Size max Height"), LCD4linux.BildSizeH))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.BildPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.BildAlign))
				self.list2.append(getConfigListEntry(_("- Quick Update"), LCD4linux.BildQuick))
				self.list2.append(getConfigListEntry(_("- Transparency"), LCD4linux.BildTransp))
			self.list2.append(getConfigListEntry(_("Show Picture 2"), LCD4linux.Bild2))
			if LCD4linux.Bild2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Bild2LCD))
				self.list2.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.Bild2File))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.Bild2Size))
				self.list2.append(getConfigListEntry(_("- Size max Height"), LCD4linux.Bild2SizeH))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Bild2Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Bild2Align))
				self.list2.append(getConfigListEntry(_("- Quick Update"), LCD4linux.Bild2Quick))
				self.list2.append(getConfigListEntry(_("- Transparency"), LCD4linux.Bild2Transp))
			self.list2.append(getConfigListEntry(_("Show Picture 3"), LCD4linux.Bild3))
			if LCD4linux.Bild3.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Bild3LCD))
				self.list2.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.Bild3File))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.Bild3Size))
				self.list2.append(getConfigListEntry(_("- Size max Height"), LCD4linux.Bild3SizeH))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.Bild3Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.Bild3Align))
				self.list2.append(getConfigListEntry(_("- Quick Update"), LCD4linux.Bild3Quick))
				self.list2.append(getConfigListEntry(_("- Transparency"), LCD4linux.Bild3Transp))
			self.list2.append(getConfigListEntry(_("Show Picture 4"), LCD4linux.Bild4))
			if LCD4linux.Bild4.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.Bild4LCD))
				self.list2.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.Bild4File))
				self.list2.append(getConfigListEntry(_("- Size"), LCD4linux.Bild4Size))
				self.list2.append(getConfigListEntry(_("- Size max Height"), LCD4linux.Bild4SizeH))
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
			self.list2.append(getConfigListEntry(_("Remote Box"), LCD4linux.RBox))
			if LCD4linux.RBox.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.RBoxLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.RBoxSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.RBoxPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.RBoxAlign))
				self.list2.append(getConfigListEntry(_("- max Width"), LCD4linux.RBoxProzent))
				self.list2.append(getConfigListEntry(_("- Color 1"), LCD4linux.RBoxColor))
				self.list2.append(getConfigListEntry(_("- Color 2"), LCD4linux.RBoxColor2))
				self.list2.append(getConfigListEntry(_("- Color 3"), LCD4linux.RBoxColor3))
				self.list2.append(getConfigListEntry(_("- Color 4"), LCD4linux.RBoxColor4))
				self.list2.append(getConfigListEntry(_("- Color 5"), LCD4linux.RBoxColor5))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.RBoxShow))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.RBoxShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.RBoxFont))
			self.list2.append(getConfigListEntry(_("Remote Box Timer"), LCD4linux.RBoxTimer))
			if LCD4linux.RBoxTimer.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.RBoxTimerLCD))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.RBoxTimerSize))
				self.list2.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.RBoxTimerLines))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.RBoxTimerType))
				self.list2.append(getConfigListEntry(_("- Type"), LCD4linux.RBoxTimerType2))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.RBoxTimerPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.RBoxTimerAlign))
				self.list2.append(getConfigListEntry(_("- Length"), LCD4linux.RBoxTimerLen))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.RBoxTimerSplit))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.RBoxTimerShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.RBoxTimerFont))
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
			self.list2.append(getConfigListEntry(_("Show Text 1"), LCD4linux.String))
			if LCD4linux.String.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.StringLCD))
				self.list2.append(getConfigListEntry(_("- Text"), LCD4linux.StringText))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.StringSize))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.StringPos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.StringAlign))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StringSplit))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.StringColor))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.StringBackColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StringShadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.StringFont))
			self.list2.append(getConfigListEntry(_("Show Text 2"), LCD4linux.String2))
			if LCD4linux.String2.value != "0":
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.String2LCD))
				self.list2.append(getConfigListEntry(_("- Text"), LCD4linux.String2Text))
				self.list2.append(getConfigListEntry(_("- Font Size"), LCD4linux.String2Size))
				self.list2.append(getConfigListEntry(_("- Position"), LCD4linux.String2Pos))
				self.list2.append(getConfigListEntry(_("- Alignment"), LCD4linux.String2Align))
				self.list2.append(getConfigListEntry(_("- Split Screen"), LCD4linux.String2Split))
				self.list2.append(getConfigListEntry(_("- Color"), LCD4linux.String2Color))
				self.list2.append(getConfigListEntry(_("- Background Color"), LCD4linux.String2BackColor))
				self.list2.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.String2Shadow))
				self.list2.append(getConfigListEntry(_("- Font"), LCD4linux.String2Font))
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
				self.list2.append(getConfigListEntry(_("- which LCD"), LCD4linux.RecordingLCD))
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
		elif self.mode == _("Media"):
			self.list3 = []
			self.list3.append(getConfigListEntry(_("- LCD 1 Background Color"), LCD4linux.MPLCDColor1))
			self.list3.append(getConfigListEntry(_("- LCD 1 Background-Picture [ok]>"), LCD4linux.MPLCDBild1))
			self.list3.append(getConfigListEntry(_("- LCD 1 Brightness"), LCD4linux.MPHelligkeit))
			self.list3.append(getConfigListEntry(_("- LCD 1 Night Reduction"), LCD4linux.MPNight))
			self.list3.append(getConfigListEntry(_("- LCD 2 Background Color"), LCD4linux.MPLCDColor2))
			self.list3.append(getConfigListEntry(_("- LCD 2 Background-Picture [ok]>"), LCD4linux.MPLCDBild2))
			self.list3.append(getConfigListEntry(_("- LCD 2 Brightness"), LCD4linux.MPHelligkeit2))
			self.list3.append(getConfigListEntry(_("- LCD 2 Night Reduction"), LCD4linux.MPNight2))
			self.list3.append(getConfigListEntry(_("- LCD 3 Background Color"), LCD4linux.MPLCDColor3))
			self.list3.append(getConfigListEntry(_("- LCD 3 Background-Picture [ok]>"), LCD4linux.MPLCDBild3))
			self.list3.append(getConfigListEntry(_("- LCD 3 Brightness"), LCD4linux.MPHelligkeit3))
			self.list3.append(getConfigListEntry(_("- LCD 3 Night Reduction"), LCD4linux.MPNight3))
			self.list3.append(getConfigListEntry(_("- LCD Auto-OFF"), LCD4linux.MPAutoOFF))
			self.list3.append(getConfigListEntry(_("- Screens used for Changing"), LCD4linux.MPScreenMax))
			self.list3.append(getConfigListEntry(_("Background"), LCD4linux.MPBackground1))
			if LCD4linux.MPBackground1.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPBackground1LCD))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPBackground1Color))
				self.list3.append(getConfigListEntry(_("- Picture [ok]>"), LCD4linux.MPBackground1Bild))
			self.list3.append(getConfigListEntry(_("Title"), LCD4linux.MPTitle))
			if LCD4linux.MPTitle.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPTitleLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPTitleSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPTitleLines))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPTitlePos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPTitleAlign))
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPTitleLen))
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
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPCommLen))
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
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPDescLen))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPDescSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPDescColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPDescShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPDescFont))
				self.list3.append(getConfigListEntry(_("- use Info when empty"), LCD4linux.MPDescUseInfo))
			self.list3.append(getConfigListEntry(_("Program Name"), LCD4linux.MPChannel))
			if LCD4linux.MPChannel.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPChannelLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPChannelSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPChannelLines))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPChannelPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPChannelAlign))
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPChannelLen))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPChannelSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPChannelColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPChannelShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPChannelFont))
			self.list3.append(getConfigListEntry(_("Program Info"), LCD4linux.MPProg))
			if LCD4linux.MPProg.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPProgLCD))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPProgType))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPProgSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPProgLines))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPProgPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPProgAlign))
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPProgLen))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPProgSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPProgColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPProgShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPProgFont))
			self.list3.append(getConfigListEntry(_("Next Program Info"), LCD4linux.MPProgNext))
			if LCD4linux.MPProgNext.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPProgNextLCD))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPProgNextType))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPProgNextSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPProgNextLines))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPProgNextPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPProgNextAlign))
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPProgNextLen))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPProgNextSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPProgNextColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPProgNextShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPProgNextFont))
			self.list3.append(getConfigListEntry(_("Progress Bar"), LCD4linux.MPProgress))
			if LCD4linux.MPProgress.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPProgressLCD))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPProgressType))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPProgressShadow2))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPProgressSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPProgressPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPProgressAlign))
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPProgressLen))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPProgressColor))
				self.list3.append(getConfigListEntry(_("- Color Text"), LCD4linux.MPProgressColorText))
				self.list3.append(getConfigListEntry(_("- Border"), LCD4linux.MPProgressBorder))
				self.list3.append(getConfigListEntry(_("- Shaded"), LCD4linux.MPProgressShadow))
				self.list3.append(getConfigListEntry(_("- Unit min"), LCD4linux.MPProgressMinutes))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPProgressFont))
			self.list3.append(getConfigListEntry(_("Volume"), LCD4linux.MPVol))
			if LCD4linux.MPVol.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPVolLCD))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPVolSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPVolPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPVolAlign))
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPVolLen))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPVolSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPVolColor))
				self.list3.append(getConfigListEntry(_("- Shaded"), LCD4linux.MPVolShadow))
			self.list3.append(getConfigListEntry(_("Mute"), LCD4linux.MPMute))
			if LCD4linux.MPMute.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPMuteLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPMuteSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPMutePos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPMuteAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPMuteSplit))
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
			self.list3.append(getConfigListEntry(_("Informations 2"), LCD4linux.MPInfo2))
			if LCD4linux.MPInfo2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPInfo2LCD))
				self.list3.append(getConfigListEntry(_("- Sensors"), LCD4linux.MPInfo2Sensor))
				self.list3.append(getConfigListEntry(_("- CPU"), LCD4linux.MPInfo2CPU))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPInfo2Size))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPInfo2Pos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPInfo2Align))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPInfo2Split))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPInfo2Lines))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPInfo2Color))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPInfo2Shadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPInfo2Font))
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
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPTimerType2))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPTimerPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPTimerAlign))
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPTimerLen))
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
				self.list3.append(getConfigListEntry(_("- Timeout [ms]"), LCD4linux.MPPingTimeout))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName1))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName2))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName3))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName4))
				self.list3.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.MPPingName5))
			self.list3.append(getConfigListEntry(_("External IP Address"), LCD4linux.MPExternalIp))
			if LCD4linux.MPExternalIp.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPExternalIpLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPExternalIpSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPExternalIpPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPExternalIpAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPExternalIpSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPExternalIpColor))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPExternalIpBackColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPExternalIpShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPExternalIpFont))
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
				self.list3.append(getConfigListEntry(_("- free Warning"), LCD4linux.MPDevWarning))
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
				self.list3.append(getConfigListEntry(_("- Station"), LCD4linux.MPNetAtmoStation))
				self.list3.append(getConfigListEntry(_("- Module"), LCD4linux.MPNetAtmoModule))
				self.list3.append(getConfigListEntry(_("- Module userdefined"), LCD4linux.MPNetAtmoModuleUser))
				self.list3.append(getConfigListEntry(_("- Base"), LCD4linux.MPNetAtmoBasis))
				self.list3.append(getConfigListEntry(_("- Name"), LCD4linux.MPNetAtmoName))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmoType))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmoType2))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPNetAtmoColor))
				self.list3.append(getConfigListEntry(_("- Color 1"), LCD4linux.MPNetAtmoColor2))
				self.list3.append(getConfigListEntry(_("- Color 2"), LCD4linux.MPNetAtmoColor3))
				self.list3.append(getConfigListEntry(_("- Color 3"), LCD4linux.MPNetAtmoColor4))
				self.list3.append(getConfigListEntry(_("- Color 4"), LCD4linux.MPNetAtmoColor5))
				self.list3.append(getConfigListEntry(_("- Color 5"), LCD4linux.MPNetAtmoColor6))
				self.list3.append(getConfigListEntry(_("- Color 6"), LCD4linux.MPNetAtmoColor7))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPNetAtmoShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPNetAtmoFont))
			self.list3.append(getConfigListEntry(_("Netatmo 2"), LCD4linux.MPNetAtmo2))
			if LCD4linux.MPNetAtmo2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPNetAtmo2LCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPNetAtmo2Pos))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPNetAtmo2Size))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPNetAtmo2Align))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPNetAtmo2Split))
				self.list3.append(getConfigListEntry(_("- Station"), LCD4linux.MPNetAtmo2Station))
				self.list3.append(getConfigListEntry(_("- Module"), LCD4linux.MPNetAtmo2Module))
				self.list3.append(getConfigListEntry(_("- Module userdefined"), LCD4linux.MPNetAtmo2ModuleUser))
				self.list3.append(getConfigListEntry(_("- Base"), LCD4linux.MPNetAtmo2Basis))
				self.list3.append(getConfigListEntry(_("- Name"), LCD4linux.MPNetAtmo2Name))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmo2Type))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmo2Type2))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPNetAtmo2Color))
				self.list3.append(getConfigListEntry(_("- Color 1"), LCD4linux.MPNetAtmo2Color2))
				self.list3.append(getConfigListEntry(_("- Color 2"), LCD4linux.MPNetAtmo2Color3))
				self.list3.append(getConfigListEntry(_("- Color 3"), LCD4linux.MPNetAtmo2Color4))
				self.list3.append(getConfigListEntry(_("- Color 4"), LCD4linux.MPNetAtmo2Color5))
				self.list3.append(getConfigListEntry(_("- Color 5"), LCD4linux.MPNetAtmo2Color6))
				self.list3.append(getConfigListEntry(_("- Color 6"), LCD4linux.MPNetAtmo2Color7))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPNetAtmo2Shadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPNetAtmo2Font))
			self.list3.append(getConfigListEntry(_("Netatmo CO2 Indicator"), LCD4linux.MPNetAtmoCO2))
			if LCD4linux.MPNetAtmoCO2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPNetAtmoCO2LCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPNetAtmoCO2Pos))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPNetAtmoCO2Size))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPNetAtmoCO2Align))
				self.list3.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.MPNetAtmoCO2Len))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPNetAtmoCO2Split))
				self.list3.append(getConfigListEntry(_("- Station"), LCD4linux.MPNetAtmoCO2Station))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmoCO2Type))
			self.list3.append(getConfigListEntry(_("Netatmo Comfort Indicator"), LCD4linux.MPNetAtmoIDX))
			if LCD4linux.MPNetAtmoIDX.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPNetAtmoIDXLCD))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPNetAtmoIDXPos))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPNetAtmoIDXSize))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPNetAtmoIDXAlign))
				self.list3.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.MPNetAtmoIDXLen))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPNetAtmoIDXSplit))
				self.list3.append(getConfigListEntry(_("- Station"), LCD4linux.MPNetAtmoIDXStation))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPNetAtmoIDXType))
			self.list3.append(getConfigListEntry(_("Moonphase"), LCD4linux.MPMoon))
			if LCD4linux.MPMoon.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPMoonLCD))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPMoonSize))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPMoonFontSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPMoonPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPMoonAlign))
				self.list3.append(getConfigListEntry(_("- Infolines"), LCD4linux.MPMoonInfos))
				self.list3.append(getConfigListEntry(_("- Infolines"), LCD4linux.MPMoonTrends))
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
			self.list3.append(getConfigListEntry(_("Show Textfile 2"), LCD4linux.MPText2))
			if LCD4linux.MPText2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPText2LCD))
				self.list3.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.MPText2File))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPText2Size))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPText2Pos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPText2Align))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPText2Color))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPText2BackColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPText2Shadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPText2Font))
			self.list3.append(getConfigListEntry(_("Show Picture"), LCD4linux.MPBild))
			if LCD4linux.MPBild.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPBildLCD))
				self.list3.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.MPBildFile))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPBildSize))
				self.list3.append(getConfigListEntry(_("- Size max Height"), LCD4linux.MPBildSizeH))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPBildPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPBildAlign))
				self.list3.append(getConfigListEntry(_("- Quick Update"), LCD4linux.MPBildQuick))
				self.list3.append(getConfigListEntry(_("- Transparency"), LCD4linux.MPBildTransp))
			self.list3.append(getConfigListEntry(_("Show Picture 2"), LCD4linux.MPBild2))
			if LCD4linux.MPBild2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPBild2LCD))
				self.list3.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.MPBild2File))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPBild2Size))
				self.list2.append(getConfigListEntry(_("- Size max Height"), LCD4linux.Bild2SizeH))
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
				self.list3.append(getConfigListEntry(_("- Find Cover File [ok]>"), LCD4linux.MPCoverFile2))
				self.list3.append(getConfigListEntry(_("- Default Cover [ok]>"), LCD4linux.MPCoverFile))
				self.list3.append(getConfigListEntry(_("- Picon First"), LCD4linux.MPCoverPiconFirst))
				self.list3.append(getConfigListEntry(_("- Transparency"), LCD4linux.MPCoverTransp))
				self.list3.append(getConfigListEntry(_("- Trimmed"), LCD4linux.MPCoverTrim))
				self.list3.append(getConfigListEntry(_("- Download Cover"), LCD4linux.MPCoverDownload))
				self.list3.append(getConfigListEntry(_("- Download Type"), LCD4linux.MPCoverType))
				self.list3.append(getConfigListEntry(_("- Google API-Key console.developers.google.com/apis"), LCD4linux.MPCoverApiGoogle))
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
			self.list3.append(getConfigListEntry(_("Remote Box"), LCD4linux.MPRBox))
			if LCD4linux.MPRBox.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPRBoxLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPRBoxSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPRBoxPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPRBoxAlign))
				self.list3.append(getConfigListEntry(_("- max Width"), LCD4linux.MPRBoxProzent))
				self.list3.append(getConfigListEntry(_("- Color 1"), LCD4linux.MPRBoxColor))
				self.list3.append(getConfigListEntry(_("- Color 2"), LCD4linux.MPRBoxColor2))
				self.list3.append(getConfigListEntry(_("- Color 3"), LCD4linux.MPRBoxColor3))
				self.list3.append(getConfigListEntry(_("- Color 4"), LCD4linux.MPRBoxColor4))
				self.list3.append(getConfigListEntry(_("- Color 5"), LCD4linux.MPRBoxColor5))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPRBoxShow))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPRBoxShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPRBoxFont))
			self.list3.append(getConfigListEntry(_("Remote Box Timer"), LCD4linux.MPRBoxTimer))
			if LCD4linux.MPRBoxTimer.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPRBoxTimerLCD))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPRBoxTimerSize))
				self.list3.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.MPRBoxTimerLines))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPRBoxTimerType))
				self.list3.append(getConfigListEntry(_("- Type"), LCD4linux.MPRBoxTimerType2))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPRBoxTimerPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPRBoxTimerAlign))
				self.list3.append(getConfigListEntry(_("- Length"), LCD4linux.MPRBoxTimerLen))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPRBoxTimerSplit))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPRBoxTimerShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPRBoxTimerFont))
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
			self.list3.append(getConfigListEntry(_("Show Text 1"), LCD4linux.MPString))
			if LCD4linux.MPString.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPStringLCD))
				self.list3.append(getConfigListEntry(_("- Text"), LCD4linux.MPStringText))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPStringSize))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPStringPos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPStringAlign))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPStringSplit))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPStringColor))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPStringBackColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPStringShadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPStringFont))
			self.list3.append(getConfigListEntry(_("Show Text 2"), LCD4linux.MPString2))
			if LCD4linux.MPString2.value != "0":
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPString2LCD))
				self.list3.append(getConfigListEntry(_("- Text"), LCD4linux.MPString2Text))
				self.list3.append(getConfigListEntry(_("- Font Size"), LCD4linux.MPString2Size))
				self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPString2Pos))
				self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPString2Align))
				self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPString2Split))
				self.list3.append(getConfigListEntry(_("- Color"), LCD4linux.MPString2Color))
				self.list3.append(getConfigListEntry(_("- Background Color"), LCD4linux.MPString2BackColor))
				self.list3.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.MPString2Shadow))
				self.list3.append(getConfigListEntry(_("- Font"), LCD4linux.MPString2Font))
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
				self.list3.append(getConfigListEntry(_("- which LCD"), LCD4linux.MPRecordingLCD))
				self.list3.append(getConfigListEntry(_("-  Type"), LCD4linux.MPRecordingType))
				self.list3.append(getConfigListEntry(_("- Size"), LCD4linux.MPRecordingSize))
				if LCD4linux.MPRecordingType.value == "2":
					self.list3.append(getConfigListEntry(_("- Position"), LCD4linux.MPRecordingPos))
					self.list3.append(getConfigListEntry(_("- Alignment"), LCD4linux.MPRecordingAlign))
					self.list3.append(getConfigListEntry(_("- Split Screen"), LCD4linux.MPRecordingSplit))
			self["config"].setList(self.list3)
		elif self.mode == _("Idle"):
			self.list4 = []
			self.list4.append(getConfigListEntry(_("LCD Display"), LCD4linux.Standby))
			self.list4.append(getConfigListEntry(_("- Backlight Off [disable set Off=On]"), LCD4linux.StandbyLCDoff))
			self.list4.append(getConfigListEntry(_("- Backlight On"), LCD4linux.StandbyLCDon))
			self.list4.append(getConfigListEntry(_("- Backlight Weekend Off [disable set Off=On]"), LCD4linux.StandbyLCDWEoff))
			self.list4.append(getConfigListEntry(_("- Backlight Weekend On"), LCD4linux.StandbyLCDWEon))
			self.list4.append(getConfigListEntry(_("- LCD Auto-OFF"), LCD4linux.StandbyAutoOFF))
			self.list4.append(getConfigListEntry(_("- LCD 1 Background Color"), LCD4linux.StandbyLCDColor1))
			self.list4.append(getConfigListEntry(_("- LCD 1 Background-Picture [ok]>"), LCD4linux.StandbyLCDBild1))
			self.list4.append(getConfigListEntry(_("- LCD 1 Brightness"), LCD4linux.StandbyHelligkeit))
			self.list4.append(getConfigListEntry(_("- LCD 1 Night Reduction"), LCD4linux.StandbyNight))
			self.list4.append(getConfigListEntry(_("- LCD 2 Background Color"), LCD4linux.StandbyLCDColor2))
			self.list4.append(getConfigListEntry(_("- LCD 2 Background-Picture [ok]>"), LCD4linux.StandbyLCDBild2))
			self.list4.append(getConfigListEntry(_("- LCD 2 Brightness"), LCD4linux.StandbyHelligkeit2))
			self.list4.append(getConfigListEntry(_("- LCD 2 Night Reduction"), LCD4linux.StandbyNight2))
			self.list4.append(getConfigListEntry(_("- LCD 3 Background Color"), LCD4linux.StandbyLCDColor3))
			self.list4.append(getConfigListEntry(_("- LCD 3 Background-Picture [ok]>"), LCD4linux.StandbyLCDBild3))
			self.list4.append(getConfigListEntry(_("- LCD 3 Brightness"), LCD4linux.StandbyHelligkeit3))
			self.list4.append(getConfigListEntry(_("- LCD 3 Night Reduction"), LCD4linux.StandbyNight3))
			self.list4.append(getConfigListEntry(_("- Screens used for Changing"), LCD4linux.StandbyScreenMax))
			self.list4.append(getConfigListEntry(_("Background"), LCD4linux.StandbyBackground1))
			if LCD4linux.StandbyBackground1.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBackground1LCD))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyBackground1Color))
				self.list4.append(getConfigListEntry(_("- Picture [ok]>"), LCD4linux.StandbyBackground1Bild))
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
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyTimerType2))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyTimerPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyTimerAlign))
				self.list4.append(getConfigListEntry(_("- Length"), LCD4linux.StandbyTimerLen))
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
			self.list4.append(getConfigListEntry(_("Informations 2"), LCD4linux.StandbyInfo2))
			if LCD4linux.StandbyInfo2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyInfo2LCD))
				self.list4.append(getConfigListEntry(_("- Sensors"), LCD4linux.StandbyInfo2Sensor))
				self.list4.append(getConfigListEntry(_("- CPU"), LCD4linux.StandbyInfo2CPU))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyInfo2Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyInfo2Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyInfo2Align))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyInfo2Split))
				self.list4.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.StandbyInfo2Lines))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyInfo2Color))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyInfo2Shadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyInfo2Font))
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
				self.list4.append(getConfigListEntry(_("- Timeout [ms]"), LCD4linux.StandbyPingTimeout))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName1))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName2))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName3))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName4))
				self.list4.append(getConfigListEntry(_("- Online Name:Address"), LCD4linux.StandbyPingName5))
			self.list4.append(getConfigListEntry(_("External IP Address"), LCD4linux.StandbyExternalIp))
			if LCD4linux.StandbyExternalIp.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyExternalIpLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyExternalIpSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyExternalIpPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyExternalIpAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyExternalIpSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyExternalIpColor))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyExternalIpBackColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyExternalIpShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyExternalIpFont))
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
				self.list4.append(getConfigListEntry(_("- free Warning"), LCD4linux.StandbyDevWarning))
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
				self.list4.append(getConfigListEntry(_("- Station"), LCD4linux.StandbyNetAtmoStation))
				self.list4.append(getConfigListEntry(_("- Module"), LCD4linux.StandbyNetAtmoModule))
				self.list4.append(getConfigListEntry(_("- Module userdefined"), LCD4linux.StandbyNetAtmoModuleUser))
				self.list4.append(getConfigListEntry(_("- Base"), LCD4linux.StandbyNetAtmoBasis))
				self.list4.append(getConfigListEntry(_("- Name"), LCD4linux.StandbyNetAtmoName))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmoType))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmoType2))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyNetAtmoColor))
				self.list4.append(getConfigListEntry(_("- Color 1"), LCD4linux.StandbyNetAtmoColor2))
				self.list4.append(getConfigListEntry(_("- Color 2"), LCD4linux.StandbyNetAtmoColor3))
				self.list4.append(getConfigListEntry(_("- Color 3"), LCD4linux.StandbyNetAtmoColor4))
				self.list4.append(getConfigListEntry(_("- Color 4"), LCD4linux.StandbyNetAtmoColor5))
				self.list4.append(getConfigListEntry(_("- Color 5"), LCD4linux.StandbyNetAtmoColor6))
				self.list4.append(getConfigListEntry(_("- Color 6"), LCD4linux.StandbyNetAtmoColor7))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyNetAtmoShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyNetAtmoFont))
			self.list4.append(getConfigListEntry(_("Netatmo 2"), LCD4linux.StandbyNetAtmo2))
			if LCD4linux.StandbyNetAtmo2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyNetAtmo2LCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyNetAtmo2Pos))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyNetAtmo2Size))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyNetAtmo2Align))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyNetAtmo2Split))
				self.list4.append(getConfigListEntry(_("- Station"), LCD4linux.StandbyNetAtmo2Station))
				self.list4.append(getConfigListEntry(_("- Module"), LCD4linux.StandbyNetAtmo2Module))
				self.list4.append(getConfigListEntry(_("- Module userdefined"), LCD4linux.StandbyNetAtmo2ModuleUser))
				self.list4.append(getConfigListEntry(_("- Base"), LCD4linux.StandbyNetAtmo2Basis))
				self.list4.append(getConfigListEntry(_("- Name"), LCD4linux.StandbyNetAtmo2Name))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmo2Type))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmo2Type2))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyNetAtmo2Color))
				self.list4.append(getConfigListEntry(_("- Color 1"), LCD4linux.StandbyNetAtmo2Color2))
				self.list4.append(getConfigListEntry(_("- Color 2"), LCD4linux.StandbyNetAtmo2Color3))
				self.list4.append(getConfigListEntry(_("- Color 3"), LCD4linux.StandbyNetAtmo2Color4))
				self.list4.append(getConfigListEntry(_("- Color 4"), LCD4linux.StandbyNetAtmo2Color5))
				self.list4.append(getConfigListEntry(_("- Color 5"), LCD4linux.StandbyNetAtmo2Color6))
				self.list4.append(getConfigListEntry(_("- Color 6"), LCD4linux.StandbyNetAtmo2Color7))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyNetAtmo2Shadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyNetAtmo2Font))
			self.list4.append(getConfigListEntry(_("Netatmo CO2 Indicator"), LCD4linux.StandbyNetAtmoCO2))
			if LCD4linux.StandbyNetAtmoCO2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyNetAtmoCO2LCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyNetAtmoCO2Pos))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyNetAtmoCO2Size))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyNetAtmoCO2Align))
				self.list4.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.StandbyNetAtmoCO2Len))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyNetAtmoCO2Split))
				self.list4.append(getConfigListEntry(_("- Station"), LCD4linux.StandbyNetAtmoCO2Station))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmoCO2Type))
			self.list4.append(getConfigListEntry(_("Netatmo Comfort Indicator"), LCD4linux.StandbyNetAtmoIDX))
			if LCD4linux.StandbyNetAtmoIDX.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyNetAtmoIDXLCD))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyNetAtmoIDXPos))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyNetAtmoIDXSize))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyNetAtmoIDXAlign))
				self.list4.append(getConfigListEntry(_("- Length [Bar]"), LCD4linux.StandbyNetAtmoIDXLen))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyNetAtmoIDXSplit))
				self.list4.append(getConfigListEntry(_("- Station"), LCD4linux.StandbyNetAtmoIDXStation))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyNetAtmoIDXType))
			self.list4.append(getConfigListEntry(_("Moonphase"), LCD4linux.StandbyMoon))
			if LCD4linux.StandbyMoon.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyMoonLCD))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyMoonSize))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyMoonFontSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyMoonPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyMoonAlign))
				self.list4.append(getConfigListEntry(_("- Infolines"), LCD4linux.StandbyMoonInfos))
				self.list4.append(getConfigListEntry(_("- Trendarrows"), LCD4linux.StandbyMoonTrends))
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
				self.list4.append(getConfigListEntry(_("- Size max Height"), LCD4linux.StandbyBildSizeH))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyBildPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyBildAlign))
				self.list4.append(getConfigListEntry(_("- Quick Update"), LCD4linux.StandbyBildQuick))
				self.list4.append(getConfigListEntry(_("- Transparency"), LCD4linux.StandbyBildTransp))
			self.list4.append(getConfigListEntry(_("Show Picture 2"), LCD4linux.StandbyBild2))
			if LCD4linux.StandbyBild2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBild2LCD))
				self.list4.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.StandbyBild2File))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyBild2Size))
				self.list4.append(getConfigListEntry(_("- Size max Height"), LCD4linux.StandbyBild2SizeH))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyBild2Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyBild2Align))
				self.list4.append(getConfigListEntry(_("- Quick Update"), LCD4linux.StandbyBild2Quick))
				self.list4.append(getConfigListEntry(_("- Transparency"), LCD4linux.StandbyBild2Transp))
			self.list4.append(getConfigListEntry(_("Show Picture 3"), LCD4linux.StandbyBild3))
			if LCD4linux.StandbyBild3.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBild3LCD))
				self.list4.append(getConfigListEntry(_("- File or Path [ok]>"), LCD4linux.StandbyBild3File))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyBild3Size))
				self.list4.append(getConfigListEntry(_("- Size max Height"), LCD4linux.StandbyBild3SizeH))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyBild3Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyBild3Align))
				self.list4.append(getConfigListEntry(_("- Quick Update"), LCD4linux.StandbyBild3Quick))
				self.list4.append(getConfigListEntry(_("- Transparency"), LCD4linux.StandbyBild3Transp))
			self.list4.append(getConfigListEntry(_("Show Picture 4"), LCD4linux.StandbyBild4))
			if LCD4linux.StandbyBild4.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyBild4LCD))
				self.list4.append(getConfigListEntry(_("- File [ok]>"), LCD4linux.StandbyBild4File))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyBild4Size))
				self.list4.append(getConfigListEntry(_("- Size max Height"), LCD4linux.StandbyBild4SizeH))
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
			self.list4.append(getConfigListEntry(_("Remote Box"), LCD4linux.StandbyRBox))
			if LCD4linux.StandbyRBox.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyRBoxLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyRBoxSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyRBoxPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyRBoxAlign))
				self.list4.append(getConfigListEntry(_("- max Width"), LCD4linux.StandbyRBoxProzent))
				self.list4.append(getConfigListEntry(_("- Color 1"), LCD4linux.StandbyRBoxColor))
				self.list4.append(getConfigListEntry(_("- Color 2"), LCD4linux.StandbyRBoxColor2))
				self.list4.append(getConfigListEntry(_("- Color 3"), LCD4linux.StandbyRBoxColor3))
				self.list4.append(getConfigListEntry(_("- Color 4"), LCD4linux.StandbyRBoxColor4))
				self.list4.append(getConfigListEntry(_("- Color 5"), LCD4linux.StandbyRBoxColor5))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyRBoxShow))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyRBoxShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyRBoxFont))
			self.list4.append(getConfigListEntry(_("Remote Box Timer"), LCD4linux.StandbyRBoxTimer))
			if LCD4linux.StandbyRBoxTimer.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyRBoxTimerLCD))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyRBoxTimerSize))
				self.list4.append(getConfigListEntry(_("- maximum Lines"), LCD4linux.StandbyRBoxTimerLines))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyRBoxTimerType))
				self.list4.append(getConfigListEntry(_("- Type"), LCD4linux.StandbyRBoxTimerType2))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyRBoxTimerPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyRBoxTimerAlign))
				self.list4.append(getConfigListEntry(_("- Length"), LCD4linux.StandbyRBoxTimerLen))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyRBoxTimerSplit))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyRBoxTimerShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyRBoxTimerFont))
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
			self.list4.append(getConfigListEntry(_("Show Text 1"), LCD4linux.StandbyString))
			if LCD4linux.StandbyString.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyStringLCD))
				self.list4.append(getConfigListEntry(_("- Text"), LCD4linux.StandbyStringText))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyStringSize))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyStringPos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyStringAlign))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyStringSplit))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyStringColor))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyStringBackColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyStringShadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyStringFont))
			self.list4.append(getConfigListEntry(_("Show Text 2"), LCD4linux.StandbyString2))
			if LCD4linux.StandbyString2.value != "0":
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyString2LCD))
				self.list4.append(getConfigListEntry(_("- Text"), LCD4linux.StandbyString2Text))
				self.list4.append(getConfigListEntry(_("- Font Size"), LCD4linux.StandbyString2Size))
				self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyString2Pos))
				self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyString2Align))
				self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyString2Split))
				self.list4.append(getConfigListEntry(_("- Color"), LCD4linux.StandbyString2Color))
				self.list4.append(getConfigListEntry(_("- Background Color"), LCD4linux.StandbyString2BackColor))
				self.list4.append(getConfigListEntry(_("- Shadow Edges"), LCD4linux.StandbyString2Shadow))
				self.list4.append(getConfigListEntry(_("- Font"), LCD4linux.StandbyString2Font))
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
				self.list4.append(getConfigListEntry(_("- which LCD"), LCD4linux.StandbyRecordingLCD))
				self.list4.append(getConfigListEntry(_("-  Type"), LCD4linux.StandbyRecordingType))
				self.list4.append(getConfigListEntry(_("- Size"), LCD4linux.StandbyRecordingSize))
				if LCD4linux.StandbyRecordingType.value == "2":
					self.list4.append(getConfigListEntry(_("- Position"), LCD4linux.StandbyRecordingPos))
					self.list4.append(getConfigListEntry(_("- Alignment"), LCD4linux.StandbyRecordingAlign))
					self.list4.append(getConfigListEntry(_("- Split Screen"), LCD4linux.StandbyRecordingSplit))
			self["config"].setList(self.list4)

	def Page(self):
		if time() - self.toggle < 0.5:
			L4log("to fast")
			return
		L4log("Page", self.mode)
		self.LastSelect = self.mode
		self.Aktuell = " "
		if self.mode == _("Global"):
			self.mode = _("On")
			self.setTitle(_("LCD4linux Display-Mode On"))
			self["key_blue"].setText(_("Set Media >>"))
			self.SetList()
		elif self.mode == _("On"):
			self.mode = _("Media")
			self.setTitle(_("LCD4linux Display-Mode MediaPlayer"))
			self["key_blue"].setText(_("Set Idle >>"))
			self.SetList()
		elif self.mode == _("Media"):
			self.mode = _("Idle")
			self.setTitle(_("LCD4linux Display-Mode Idle"))
			self["key_blue"].setText(_("Set Global >>"))
			self.SetList()
		elif self.mode == _("Idle"):
			self.mode = _("Global")
			self.setTitle(_("LCD4linux Settings"))
			self["key_blue"].setText(_("Set On >>"))
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
				self.session.openWithCallback(self.dirSelected, LCDdisplayFile, text=_("Choose dir"), FileName=self["config"].getCurrent()[1].value, showFiles=False)
			elif sel in [LCD4linux.LCDBild1, LCD4linux.LCDBild2, LCD4linux.MPLCDBild1, LCD4linux.MPLCDBild2, LCD4linux.StandbyLCDBild1, LCD4linux.StandbyLCDBild2, LCD4linux.FritzFrame]:
				L4log("select File 1")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, text=_("Choose file"), FileName=self["config"].getCurrent()[1].value, showFiles=True)
			elif sel in [LCD4linux.OSCAMFile, LCD4linux.TextFile, LCD4linux.Text2File, LCD4linux.Text3File, LCD4linux.MPTextFile, LCD4linux.MPCoverFile, LCD4linux.MPCoverFile2, LCD4linux.BildFile, LCD4linux.Bild2File, LCD4linux.Bild3File, LCD4linux.Bild4File, LCD4linux.RecordingPath]:
				L4log("select File 2")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, text=_("Choose file"), FileName=self["config"].getCurrent()[1].value, showFiles=True)
			elif sel in [LCD4linux.Font, LCD4linux.Font1, LCD4linux.Font2, LCD4linux.Font3, LCD4linux.Font4, LCD4linux.Font5]:
				L4log("select File 3")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, matchingPattern="ttf", text=_("Choose font"), FileName=self["config"].getCurrent()[1].value, showFiles=True)
			elif sel in [LCD4linux.MPBildFile, LCD4linux.MPBild2File, LCD4linux.StandbyBildFile, LCD4linux.StandbyBild2File, LCD4linux.StandbyBild3File, LCD4linux.StandbyBild4File, LCD4linux.StandbyTextFile, LCD4linux.StandbyText2File, LCD4linux.StandbyText3File]:
				L4log("select File 4")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, text=_("Choose file"), FileName=self["config"].getCurrent()[1].value, showFiles=True)
			elif sel in [LCD4linux.Background1Bild, LCD4linux.LCD4linux.MPBackground1Bild, LCD4linux.StandbyBackground1Bild]:
				L4log("select File 5")
				self.session.openWithCallback(self.fileSelected, LCDdisplayFile, text=_("Choose file"), FileName=self["config"].getCurrent()[1].value, showFiles=True)
		except Exception as err:
			L4log("Key-OK Config Fehler: %s" % str(err))

	def dirSelected(self, dir, dir1):
		if dir is None or dir1 is None:
			return
		if dir + dir1 != "" and dir1.endswith("/"):
			sel = self["config"].getCurrent()[1]
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
		if dir is None or dir1 is None:
			return
		sel = self["config"].getCurrent()[1]
		if dir + dir1 != "" and not dir1.endswith("/"):
			dirdir = join(dir, dir1)
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
#			elif sel == LCD4linux.MPCoverFile2:
#				LCD4linux.MPCoverFile2.value = dirdir
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
			elif sel == LCD4linux.Background1Bild:
				LCD4linux.Background1Bild.value = dirdir
			elif sel == LCD4linux.MPBackground1Bild:
				LCD4linux.MPBackground1Bild.value = dirdir
			elif sel == LCD4linux.StandbyBackground1Bild:
				LCD4linux.StandbyBackground1Bild.value = dirdir
			elif sel == LCD4linux.Font:
				setFONT(dirdir)
			elif sel == LCD4linux.Font1:
				if dirdir.endswith(".ttf") and isfile(dirdir):
					LCD4linux.Font1.value = dirdir
			elif sel == LCD4linux.Font2:
				if dirdir.endswith(".ttf") and isfile(dirdir):
					LCD4linux.Font2.value = dirdir
			elif sel == LCD4linux.Font3:
				if dirdir.endswith(".ttf") and isfile(dirdir):
					LCD4linux.Font3.value = dirdir
			elif sel == LCD4linux.Font4:
				if dirdir.endswith(".ttf") and isfile(dirdir):
					LCD4linux.Font4.value = dirdir
			elif sel == LCD4linux.Font5 and dirdir.endswith(".ttf") and isfile(dirdir):
				LCD4linux.Font5.value = dirdir
		if dir + dir1 != "" and dir1.endswith("/"):
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
		global PICcal
		global PICwetter
		L4log("select", self["config"].getCurrent()[0])
		self.Aktuell = self["config"].getCurrent()[0]
		self.LastSelect = str(self["config"].getCurrentIndex()) + self.getCurrentValue()[:3]
		self["introduction"].setText(_("%s - Current value: %s") % (self.mode, self.getCurrentValue()))
		if USBok == False:
			self["LibUSB"].setText("libusb!")
		else:
			self["LibUSB"].setText("")
			self["About"].setText("joergm6@IHAD")  # it is not allowed to change/remove
		if self.mode == _("Idle"):
			ConfigStandby = True
		elif self.mode == _("Media"):
			isMediaPlayer = "config"
		else:
			ConfigStandby = False
			isMediaPlayer = ""
		if LCD4linux.PiconPath.value == LCD4linux.PiconCache.value:
			LCD4linux.PiconCache.value = ""
		if LCD4linux.Picon2Path.value == LCD4linux.Picon2Cache.value:
			LCD4linux.Picon2Cache.value = ""
		if LCD4linux.PiconSize.isChanged() or LCD4linux.PiconFullScreen.isChanged() or LCD4linux.PiconTransparenz.isChanged():
			if len(LCD4linux.PiconCache.value) > 2:
				rmFiles(join(LCD4linux.PiconCache.value, "*.png"))
		if LCD4linux.Picon2Size.isChanged() or LCD4linux.Picon2FullScreen.isChanged() or LCD4linux.PiconTransparenz.isChanged():
			if len(LCD4linux.Picon2Cache.value) > 2:
				rmFiles(join(LCD4linux.Picon2Cache.value, "*.png"))
		if LCD4linux.WetterApi.isChanged():
			L4log("Weather API was changed to %s" % LCD4linux.WetterApi.value)
			resetWetter(None)
		if self.SaveWetter != LCD4linux.WetterCity.value:
			self.SaveWetter = LCD4linux.WetterCity.value
			LCD4linux.WetterCoords.value = "0,0"
			LCD4linux.WetterCoords.save()
			L4log("Weather city was changed from '%s' to '%s'" % (self.SaveWetter, LCD4linux.WetterCity.value))
			resetWetter(0)
		if self.SaveWetter2 != LCD4linux.Wetter2City.value:
			self.SaveWetter2 = LCD4linux.Wetter2City.value
			LCD4linux.Wetter2Coords.value = "0,0"
			LCD4linux.Wetter2Coords.save()
			L4log("Weather2 city was changed from '%s' to '%s'" % (self.SaveWetter2, LCD4linux.Wetter2City.value))
			resetWetter(1)
		if LCD4linux.WetterIconZoom.isChanged() or LCD4linux.WetterRain.isChanged() or LCD4linux.WetterRainZoom.isChanged() or LCD4linux.WetterRainColor.isChanged() or LCD4linux.WetterRainColor2.isChanged() or LCD4linux.WetterRainColor2use.isChanged() or LCD4linux.WetterLine.isChanged() or LCD4linux.WetterTrendArrows.isChanged() or LCD4linux.WetterExtra.isChanged() or LCD4linux.WetterExtraColorFeel.isChanged() or LCD4linux.WetterExtraColorCity.isChanged() or LCD4linux.WetterExtraZoom.isChanged() or LCD4linux.WetterExtraFeel.isChanged() or LCD4linux.WetterWind.isChanged() or LCD4linux.WetterWindLines.isChanged() or LCD4linux.WetterLowColor.isChanged() or LCD4linux.WetterHighColor.isChanged() or LCD4linux.WetterTransparenz.isChanged() or LCD4linux.WetterHumColor.isChanged() or LCD4linux.WetterExtra.isChanged():
			PICwetter = [None, None]
		if LCD4linux.WetterZoom.isChanged() or LCD4linux.StandbyWetterZoom.isChanged() or LCD4linux.MPWetterZoom.isChanged() or LCD4linux.WetterType.isChanged() or LCD4linux.StandbyWetterType.isChanged() or LCD4linux.MPWetterType.isChanged() or LCD4linux.WetterColor.isChanged() or LCD4linux.StandbyWetterColor.isChanged() or LCD4linux.MPWetterColor.isChanged() or LCD4linux.WetterFont.isChanged() or LCD4linux.MPWetterFont.isChanged() or LCD4linux.StandbyWetterFont.isChanged() or LCD4linux.WetterShadow.isChanged() or LCD4linux.StandbyWetterShadow.isChanged() or LCD4linux.MPWetterShadow.isChanged():
			PICwetter[0] = None
		if LCD4linux.Wetter2Zoom.isChanged() or LCD4linux.StandbyWetter2Zoom.isChanged() or LCD4linux.MPWetter2Zoom.isChanged() or LCD4linux.Wetter2Type.isChanged() or LCD4linux.StandbyWetter2Type.isChanged() or LCD4linux.MPWetter2Type.isChanged() or LCD4linux.Wetter2Color.isChanged() or LCD4linux.StandbyWetter2Color.isChanged() or LCD4linux.MPWetterColor.isChanged() or LCD4linux.Wetter2Font.isChanged() or LCD4linux.MPWetter2Font.isChanged() or LCD4linux.StandbyWetter2Font.isChanged() or LCD4linux.Wetter2Shadow.isChanged() or LCD4linux.StandbyWetter2Shadow.isChanged() or LCD4linux.MPWetter2Shadow.isChanged():
			PICwetter[1] = None
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
			PICcal = None
		if LCD4linux.MPCalLayout.isChanged() or LCD4linux.MPCalColor.isChanged() or LCD4linux.MPCalBackColor.isChanged() or LCD4linux.MPCalCaptionColor.isChanged() or LCD4linux.StandbyCalLayout.isChanged() or LCD4linux.StandbyCalColor.isChanged() or LCD4linux.StandbyCalBackColor.isChanged() or LCD4linux.StandbyCalCaptionColor.isChanged() or LCD4linux.CalShadow.isChanged() or LCD4linux.StandbyCalShadow.isChanged() or LCD4linux.MPCalShadow.isChanged():
			PICcal = None
		if LCD4linux.WWW1url.isChanged() or LCD4linux.StandbyWWW1url.isChanged():
			self.WWWischanged = True
		if self.SavePicture != LCD4linux.SavePicture.value:
			rmFiles(PIC + "*.*")
			self.SavePicture = LCD4linux.SavePicture.value
		if LCD4linux.TV.value == "0":
			TVrunning = False
		if LCD4linux.MJPEGenable1.isChanged() or LCD4linux.MJPEGenable2.isChanged() or LCD4linux.MJPEGenable3.isChanged():
			MJPEG_stop("")
			MJPEG_start()
		if LCD4linux.xmlLCDType.isChanged():
			xmlRead()
			if xmlDelete(1) or xmlDelete(2) or xmlDelete(3):
				L4log("removed old Skindata")
				xmlWrite()
			xmlClear()

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
		PICwetter = [None, None]
		rmFile("%stft.bmp" % TMPL)
		rmFiles(PIC + "*.*")
		if Briefkasten.qsize() <= 3:
			Briefkasten.put(4)
		else:
			L4log("Queue full, Thread hanging?")
		if Briefkasten.qsize() <= 3:
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
		LCD4linux.save()
		LCD4linux.saveToFile(LCD4config)
		ConfTimeCheck()
		getBilder()
		TFTCheck(False)
		if LCD4linux.LCDType1.value[0] == "5" or LCD4linux.LCDType2.value[0] == "5" or LCD4linux.LCDType3.value[0] == "5":
			if xmlSkin():
				configfile.save()
				xmlWrite()
				restartbox = self.session.openWithCallback(self.restartGUI, MessageBox, _("GUI needs a restart to apply the changes.\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO, default=False)
				restartbox.setTitle(_("Restart GUI now?"))
			else:
				self.close(True, self.session)
			xmlClear()
		else:
			self.close(True, self.session)
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
		self.close(True, self.session)
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
		self.LastSelect = str(self["config"].getCurrentIndex())
		L4logE("key U")
		if self["config"].getCurrentIndex() - self.ConfLines > 0:
			self["config"].setCurrentIndex(self["config"].getCurrentIndex() - self.ConfLines)
		else:
			self["config"].setCurrentIndex(0)

	def KeyDown(self):
		self.LastSelect = str(self["config"].getCurrentIndex())
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
			self.close(True, self.session)


class UpdateStatus(Screen):

	def __init__(self, session):
		global ScreenActive
		Screen.__init__(self, session)
		ScreenActive[0] = LCD4linux.ScreenActive.value
		self.NetatmoOK = NetatmoOK
		self.ServiceChangeRunning = False
		self.SaveTXTfile = 0
		self.SaveMPTXTfile = 0
		self.SaveBildfile = 0
		self.SaveStandbyBildfile = 0
		self.SaveStandbyTXTfile = 0
		self.KeyDoppel = 0
		self.KeyTime = 0
		self.AutoOFF = 0
		self.SonosCheckTimer = 0
		self.YMCastCheckTimer = 0
		self.BlueCheckTimer = 0
		self.StandbyChanged = False
		self.DataMinute = ""
		self.l4l_info = {}
		self.isFB2 = False
		self.Ltimer_list = []
		self.LgetGoogleCover = None
		self.CoverError = ""
		self.LisRecording = None
		self.LisTimeshift = None
		self.LEventsNext = None
		self.LEventsDesc = None
		self.Ltuner_number = None
		self.LvolM = False
		self.Lvol = None
		self.ref = None
		self.LsreftoString = None
		self.LsrefFile = ""
		self.Lchannel_name = None
		self.Lchannel_name2 = ""
		self.Lpath = None
		self.Lchannel_num = ""
		self.Llength = None
		self.Lposition = None
		self.GPLlength = [1, 0]
		self.GPLposition = [1, 0]
		self.Lcommand = ""
		self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0 = 0, 0, 0, ""
		self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1 = 0, 0, 0, ""
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
		self.LsTagDate = None
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
		self.bitrate = None
		self.LisRefresh = False
		self.Refresh = "0"
		self.iName = ""
		self.iT = "0.0"
		self.iH = "0"
		self.iP = "0"
		self.iN = "0"
		self.iC = "0"
		self.iIDX = "0"
		self.dis_reason = ""
		self.oM = []
		self.TEMPERATURE = "C"
		self.HUMIDITY = "%"
		self.CO2 = "ppm"
		self.PRESSURE = "mbar"
		self.NOISE = "db"
		self.MM = "mm"
		self.WIND = "m/s"
		self.SonosTrack = {}
		self.SonosInfo = ""
		self.SonosRunning = False
		self.SonosSoCo = None
		self.SonosSoCoSave = ""
		self.YMCastInfo = {}
		self.YMCastRunning = False
		self.YMCastSoCo = None
		self.YMCastSoCoSave = ""
		self.YMCastPlaytime = 0
		self.YMCastoldTitle = ""
		self.BlueInfo = {}
		self.BlueRunning = False
		self.BlueSoCo = None
		self.BlueSoCoSave = ""
		self.BluePlaytime = 0
		self.BlueoldTitle = ""
		self.BlueImage = ""
		self.oldTitle = ""
		self.CoverCount = 0
		self.TunerCallBack = False
		self.WetterOK = False
		self.Long = ["0", "0"]
		self.Lat = ["0", "0"]
		self.ExternalIP = "waiting <1h..."
		self.WDay = [{}, {}]
		self.WWeek = [[], []]
		self.wwwBox = [[""], [""], [""], [""], [""]]
		self.wwwBoxTimer = []
		self.LastwwwBox = ""
		self.LastwwwBoxTimer = ""
		img = Image.new('RGB', (10, 10), "black")
		self.im = [img, img, img, img, img, img, img]  # 0=Grab; 4=Cal; 5+6=Weather
		img = ImageDraw.Draw(self.im[1])
		self.draw = [img, img, img, img, img, img, img]  # 0=Grab; 4=Cal; 5+6=Weather
		self.tmp = [None, None, None, None]
		self.BackIm = [None, None, None]
		self.BackName = ["-", "-", "-"]
		self.PiconIm = [None, None]
		self.PiconName = [["-", "-"], ["-", "-"]]
		self.ClockIm = [None, None]
		self.ClockName = [["-", "-"], ["-", "-"]]
		self.CoverIm = None
		self.CoverName = ["-", "-"]
		self.imWrite = [False, False, False, False]
		self.im[1] = Image.new('RGB', (10, 10), "black")
		self.draw[1] = ImageDraw.Draw(self.im[1])
		self.im[2] = self.im[1]
		self.im[3] = self.im[1]
		self.draw[2] = self.draw[1]
		self.draw[3] = self.draw[1]
		self.Temp = ""
		L4LElist.setFont([FONT, LCD4linux.Font1.value, LCD4linux.Font2.value, LCD4linux.Font3.value, LCD4linux.Font4.value, LCD4linux.Font5.value])
		L4LElist.setVersion(Version)
		if getFB2(False):
			self.isFB2 = True
			if (LCD4linux.xmlType01.value == True or LCD4linux.xmlType02.value == True or LCD4linux.xmlType03.value == True):
				setFB2("1")
		self.NetworkConnectionAvailable = False
		try:
			if LCD4linux.NETworkCheckEnable.value == True:
				iNetwork.checkNetworkState(self.checkNetworkCB)
			else:
				self.NetworkConnectionAvailable = None
		except Exception:
			self.NetworkConnectionAvailable = None
			L4log("iNetwork-Error, Check disable")
		self.StatusTimer = eTimer()
		self.ServiceTimer = eTimer()
		self.SamsungTimer = eTimer()
		self.DpfTimer = eTimer()
		self.QuickTimer = eTimer()
		self.CheckRefresh = eTimer()
		self.Later6Timer = eTimer()
		self.SonosTimer = eTimer()
		self.YMCastTimer = eTimer()
		self.BlueTimer = eTimer()
		self.StatusTimer.callback.append(self.updateStatus)
		self.ServiceTimer.callback.append(self.ServiceChange)
		self.SamsungTimer.callback.append(self.SamsungStart)
		self.DpfTimer.callback.append(self.DpfStart)
		self.QuickTimer.callback.append(self.QuickBildTimer)
		self.CheckRefresh.callback.append(self.CallCheckRefresh)
		self.Later6Timer.callback.append(self.CallLater6)
		self.SonosTimer.callback.append(self.getSonos)
		self.YMCastTimer.callback.append(self.getYMCast)
		self.BlueTimer.callback.append(self.getBlue)
		if GPjukeboxOK == True:
			CjukeboxEventNotifier.append(self.BPPlayerEvent)
		if BitrateRegistred == True:
			self.BitrateTimer = eTimer()
			self.BitrateTimer.callback.append(self.runBitrateTimer)
			self.BitrateTimer.startLongTimer(30)
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUpdatedInfo: self.restartTimer,
				iPlayableService.evUpdatedEventInfo: self.restartTimer,
				iPlayableService.evVideoSizeChanged: self.restartTimer
#				iPlayableService.evSeekableStatusChanged: self.restartTimer,
#				iPlayableService.evVideoProgressiveChanged: self.restartTimer,
#				iPlayableService.evUser: self.restartTimer
			})
		self.InstanceKeyPressed = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.rcKeyPressed)
		self.recordtimer = session.nav.RecordTimer
		self.LastTimerlistUpdate = 0
		if (LCD4linux.StandbyWetter.value != "0" or LCD4linux.Wetter.value != "0" or LCD4linux.MPWetter.value != "0"):
			self.downloadWetter(LCD4linux.WetterCity.value, 0)
		if LCD4linux.StandbyWetter2.value != "0" or LCD4linux.Wetter2.value != "0" or LCD4linux.MPWetter2.value != "0":
			self.downloadWetter(LCD4linux.Wetter2City.value, 1)
		if LCD4linux.StandbyMeteo.value != "0" or LCD4linux.Meteo.value != "0":
			self.downloadMeteo()
		if LCD4linux.ExternalIp.value != "0" or LCD4linux.MPExternalIp.value != "0" or LCD4linux.StandbyExternalIp.value != "0":
			self.ExternalIP = getExternalIP()
		self.timerlist = ""
		self.pluginlist = ""
#		self.onShow.append(self.ServiceChange)
		config.misc.standbyCounter.addNotifier(self.standbyQuery, initial_call=False)
		getBilder()
		self.Temp = GetTempSensor()
		self.StatusTimer.startLongTimer(int(LCD4linux.FastMode.value))
		self.QuickTimer.start(int(LCD4linux.BilderQuick.value), True)
		self.CheckRefresh.start(500, True)
		self.SamsungStart()
		self.DpfStart()
		self.onTunerCount()
		L4LthreadsLCD = [L4LWorkerLCD(i, self, session) for i in range(1)]
		for thread in L4LthreadsLCD:
			thread.setDaemon(True)
			thread.start()
		L4Lthreads = [L4LWorker(i, self, session) for i in range(1)]
		for thread in L4Lthreads:
			thread.setDaemon(True)
			thread.start()
		L4LthreadsRes = [L4LWorkerRes(i, self, session) for i in range(2)]
		for thread in L4LthreadsRes:
			thread.setDaemon(True)
			thread.start()
		L4Lthreads1 = [L4LWorker1(i, self, session) for i in range(int(LCD4linux.ElementThreads.value))]
		for thread in L4Lthreads1:
			thread.setDaemon(True)
			thread.start()
		L4Lthreads2 = [L4LWorker2(i, self, session) for i in range(int(LCD4linux.ElementThreads.value))]
		for thread in L4Lthreads2:
			thread.setDaemon(True)
			thread.start()
		L4Lthreads3 = [L4LWorker3(i, self, session) for i in range(int(LCD4linux.ElementThreads.value))]
		for thread in L4Lthreads3:
			thread.setDaemon(True)
			thread.start()
		if LCD4linux.WebIfInitDelay.value == True:
			Briefkasten.put(5)
		MJPEG_start()

	def standbyQuery(self, configElement):
		Standby.inStandby.onClose.append(self.restartTimer)
		self.Refresh = "1"
		self.restartTimer()

	def onTunerCount(self):
		global TunerCount
		TunerCount = nimmanager.getSlotCount()
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.TunerCallBack = True
			res_mgr.frontendUseMaskChanged.get().append(self.tunerUseMaskChanged)
		else:
			print("[ERROR]no res_mgr!!")

	def offTunerCount(self):
		if self.TunerCallBack:
			res_mgr = eDVBResourceManager.getInstance()
			if res_mgr:
				self.TunerCallBack = False
				res_mgr.frontendUseMaskChanged.get().remove(self.tunerUseMaskChanged)
			else:
				print("[ERROR]no res_mgr!!")

	def tunerUseMaskChanged(self, mask):
		global TunerMask
		TunerMask = mask
		self.restartTimer()

	def QuickBildTimer(self):
		self.QuickTimer.stop()
		if Briefkasten.qsize() <= 3:
			Briefkasten.put(7)
		else:
			L4log("Queue full, Thread hanging?")
		self.QuickTimer.start(int(LCD4linux.BilderQuick.value), True)

	def CallLater6(self):
		self.Later6Timer.stop()
		Briefkasten.put(6)

	def CallCheckRefresh(self):
		global SaveEventListChanged
		global FritzTime
		self.CheckRefresh.stop()
		if L4LElist.getRefresh() == True:
			L4logE("external Refresh")
			FritzTime = 0
			if L4LElist.getScreen() != "":
				SaveEventListChanged = L4LElist.getHold()
				setScreenActive(str(L4LElist.getScreen()), str(L4LElist.getLcd()))
				L4LElist.setScreen("")
				L4LElist.setHold(False)
			L4LElist.resetRefresh()
			self.Refresh = "1"
			self.restartTimer()
		if self.LgetGoogleCover is not None and self.LgetGoogleCover != "wait":
			self.getGoogleCover(self.LgetGoogleCover[0], self.LgetGoogleCover[1])
		self.CheckRefresh.start(500, True)

	def getSonos(self):
		global isMediaPlayer
		if SonosOK == True and LCD4linux.SonosIP.value != "":
			tt = time()
			if self.SonosSoCo is None or self.SonosSoCoSave != LCD4linux.SonosIP.value:
				self.SonosSoCoSave = LCD4linux.SonosIP.value
				L4log("Sonos Connect", LCD4linux.SonosIP.value)
				try:
					self.SonosSoCo = SoCo(LCD4linux.SonosIP.value)
					try:
						self.SonosSoCo = self.SonosSoCo.group.coordinator
						if self.SonosSoCoSave not in str(self.SonosSoCo):
							L4log("Sonos Switched", self.SonosSoCo)
					except Exception:
						L4log("Sonos Group-Coordinator Error")
				except Exception:
					L4log("Sonos Connect Error")
					self.SonosSoCo = None
			try:
				if int(LCD4linux.SonosPingTimeout.value) > 0:
					r = quiet_ping(LCD4linux.SonosIP.value, int(LCD4linux.SonosPingTimeout.value))
					if not r or r[2] == 0.0:
						r = quiet_ping(LCD4linux.SonosIP.value, int(LCD4linux.SonosPingTimeout.value))
					if (not r or r[2] == 0.0) and self.SonosRunning:
						self.SonosTrack = {}
						self.SonosRunning = False
						isMediaPlayer = ""
						getBilder()
						L4log("Sonos Ping Timeout", str(r))
						return
				if self.SonosSoCo is not None:
					cti = self.SonosSoCo.get_current_transport_info()
#					if LCD4linux.SonosON.value == True:
#						cti = {u'current_transport_status': 'OK', u'current_transport_state': 'PLAYING', u'current_transport_speed': '1'}
#					else:
#						cti = {u'current_transport_status': 'OK', u'current_transport_state': 'STOPPED', u'current_transport_speed': '1'}
					self.SonosInfo = cti.get("current_transport_state", "STOPPED")
					if self.SonosInfo != "PLAYING" or self.SonosSoCo.is_playing_tv:
						if self.SonosRunning:
							self.SonosTrack = {}
							self.SonosSoCo = None
							self.SonosRunning = False
							isMediaPlayer = ""
							getBilder()
							L4log("Sonos stopped")
					else:
						self.SonosTrack = self.SonosSoCo.get_current_track_info()
						self.Lvol = self.SonosSoCo.volume
#						self.SonosTrack = {u'album': 'Sehnsucht', u'artist': 'Rammstein', u'title': 'Eifersucht', u'uri': 'x-sonos-spotify:spotify%3atrack%3a4Ugp6Wu4hVXnbEKT3Nrka0?sid=9&flags=8224&sn=3', u'playlist_position': '10', u'duration': '0:03:35', u'position': '0:01:39', u'album_art': u'http://192.168.0.84:1400/getaa?s=1&u=x-sonos-spotify%3aspotify%253atrack%253a4Ugp6Wu4hVXnbEKT3Nrka0%3fsid%3d9%26flags%3d8224%26sn%3d3', u'metadata': '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><res protocolInfo="sonos.com-spotify:*:audio/x-spotify:*" duration="0:03:35">x-sonos-spotify:spotify%3atrack%3a4Ugp6Wu4hVXnbEKT3Nrka0?sid=9&amp;flags=8224&amp;sn=3</res><r:streamContent></r:streamContent><upnp:albumArtURI>/getaa?s=1&amp;u=x-sonos-spotify%3aspotify%253atrack%253a4Ugp6Wu4hVXnbEKT3Nrka0%3fsid%3d9%26flags%3d8224%26sn%3d3</upnp:albumArtURI><dc:title>Eifersucht</dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><dc:creator>Rammstein</dc:creator><upnp:album>Sehnsucht</upnp:album></item></DIDL-Lite>'}
						if self.SonosRunning == False:
							self.SonosSoCo = None
						self.SonosRunning = True
						isMediaPlayer = "sonos"
						L4log("Sonos running", self.SonosTrack)
						self.SonosTimer.startLongTimer(int(LCD4linux.SonosTimer.value))
						self.restartTimer()
			except Exception:
				self.SonosTrack = {}
				self.SonosRunning = False
				L4log("Sonos Communikation Error")
				L4log("Error:", format_exc())
			L4logE("Sonos RunTime: %.3f" % (time() - tt))

	def getYMCast(self):
		global isMediaPlayer
		if LCD4linux.YMCastIP.value != "":
			tt = time()
			if self.YMCastSoCo is None or self.YMCastSoCoSave != LCD4linux.YMCastIP.value:
				self.YMCastSoCoSave = LCD4linux.YMCastIP.value
				L4log("MusicCast Connect", LCD4linux.YMCastIP.value)
				try:
					self.YMCastSoCo = YMC(LCD4linux.YMCastIP.value)
				except Exception:
					L4log("YMCast Connect Error")
					self.YMCastSoCo = None
			try:
				if int(LCD4linux.YMCastPingTimeout.value) > 0:
					r = quiet_ping(LCD4linux.YMCastIP.value, int(LCD4linux.YMCastPingTimeout.value))
					if not r or r[2] == 0.0:
						r = quiet_ping(LCD4linux.YMCastIP.value, int(LCD4linux.YMCastPingTimeout.value))
					if (not r or r[2] == 0.0) and self.YMCastRunning:
						self.YMCastInfo = {}
						self.YMCastRunning = False
						isMediaPlayer = ""
						getBilder()
						L4log("YMCast Ping Timeout", str(r))
						return
				if self.YMCastSoCo is not None:
					self.YMCastInfo = self.YMCastSoCo.getPlayInfo()
					if self.YMCastInfo == {}:
						self.YMCastInfo = self.YMCastSoCo.getPlayInfo()
					if self.YMCastInfo.get("playback", "") != "play":
						if self.YMCastRunning:
							self.YMCastInfo = {}
							self.YMCastSoCo = None
							self.YMCastRunning = False
							isMediaPlayer = ""
							getBilder()
							L4log("YMC stopped")
					else:
						self.Lvol = self.YMCastSoCo.getStatus().get("volume", 0)
						self.LvolM = self.YMCastSoCo.getStatus().get("mute", False)
						if self.YMCastRunning == False:
							self.YMCastSoCo = None
						self.YMCastRunning = True
						isMediaPlayer = "ymc"
						L4log("YMC running %s" % self.YMCastInfo)
						self.YMCastTimer.startLongTimer(int(LCD4linux.YMCastTimer.value))
						self.restartTimer()
			except Exception:
				self.YMCastInfo = {}
				self.YMCastRunning = False
				L4log("YMC Communikation Error")
				L4log("Error:", format_exc())
			L4logE("YMC RunTime: %.3f" % (time() - tt))

	def getBlue(self):
		global isMediaPlayer
		if LCD4linux.BlueIP.value != "":
			tt = time()
			if self.BlueSoCo is None or self.BlueSoCoSave != LCD4linux.BlueIP.value:
				self.BlueSoCoSave = LCD4linux.BlueIP.value
				L4log("BlueSound Connect", LCD4linux.BlueIP.value)
				try:
					self.BlueSoCo = BlueSound(LCD4linux.BlueIP.value)
				except Exception:
					L4log("BlueSound Connect Error")
					self.YBlueSoCo = None
			try:
				if int(LCD4linux.BluePingTimeout.value) > 0:
					r = quiet_ping(LCD4linux.BlueIP.value, int(LCD4linux.BluePingTimeout.value))
					if not r or r[2] == 0.0:
						r = quiet_ping(LCD4linux.BlueIP.value, int(LCD4linux.BluePingTimeout.value))
					if (not r or r[2] == 0.0) and self.BlueRunning:
						self.BlueInfo = {}
						self.BlueRunning = False
						isMediaPlayer = ""
						getBilder()
						L4log("BlueSound Ping Timeout", str(r))
						return
				if self.BlueSoCo is not None:
					self.BlueInfo = self.BlueSoCo.getStatus()
					if self.BlueInfo.get("state", "stop") == "stop":
						if self.BlueRunning:
							self.BlueInfo = {}
							self.BlueSoCo = None
							self.BlueRunning = False
							isMediaPlayer = ""
							getBilder()
							L4log("BlueSound stopped")
					else:
						self.BlueImage = self.BlueInfo.get("image", "")
						if self.BlueImage.startswith("/"):
							self.BlueImage = self.BlueSoCo.baseUrl + self.BlueImage[1:]
						self.Lvol = self.BlueInfo.get("volume", 0)
						self.LvolM = self.BlueInfo.get("mute", False)
						if self.BlueRunning == False:
							self.BlueSoCo = None
						self.BlueRunning = True
						isMediaPlayer = "blue"
						L4log("BlueSound running %s" % self.BlueInfo)
						self.BlueTimer.startLongTimer(int(LCD4linux.BlueTimer.value))
						self.restartTimer()
			except Exception:
				self.BlueInfo = {}
				self.BlueRunning = False
				L4log("BlueSound Communikation Error")
				L4log("Error:", format_exc())
			L4logE("BlueSound RunTime: %.3f" % (time() - tt))

	def getNetatmo(self):
		if self.NetatmoOK == True:
			try:
				if len(netatmo.stations) > 0:
					L4log("get Netatmo")
					self.iName = []
					self.iT = []
					self.iH = []
					self.iP = []
					self.iN = []
					self.iC = []
					self.iIDX = []
					self.dis_reason = []
					self.oM = []
					Modulenames = {'NAModule1': _("Outdoor"), 'NAModule2': _("Wind"), 'NAModule3': _("Rain"), 'NAModule4': _("Indoor")}
					for na in netatmo.stations:
						self.iName.append(na.module_name)
						self.iT.append("%s.0" % str(na.measure.temperature))
						if len(self.iT[len(self.iT) - 1].split(".")[0]) < 2:
							self.iT[len(self.iT) - 1] = " " + self.iT[len(self.iT) - 1]
						self.iH.append(str(na.measure.humidity))
						self.iP.append(str(na.measure.pressure))
						self.iN.append(str(na.measure.noise))
						self.iC.append(str(na.measure.co2))
						try:
							self.iIDX.append(str(na.measure.idx_total))
							self.dis_reason.append(str(na.measure.dis_reason))
						except Exception:
							self.iIDX = ["0", "0", "0", "0", "0", "0"]
							self.dis_reason = ["", "", "", "", "", ""]
							L4log("please use newer Netatmo-Plugin")
						self.oM.append([])  # Wert1,Wert2,Wert3,Wert4,Name,Type,Batt
						# Outdoor , Wind , Rain , Indoor
						BatterylistR = {"NAModule1": 4000, "NAModule2": 4360, "NAModule3": 4000, "NAModule4": 4560}
						BatterylistY = {"NAModule1": 4500, "NAModule2": 4770, "NAModule3": 4500, "NAModule4": 4920}
						for Mod in na.modules:
							Battery = "green"
							if Mod.module_type.startswith("NAModule"):
								L4logE("Battery %s " % Mod.module_type, Mod.battery_vp)
								if Mod.battery_vp > 0 and Mod.battery_vp <= BatterylistR.get(Mod.module_type, 4500):
									L4log("Battery empty", Mod.module_type)
									Battery = "red"
								elif Mod.battery_vp > 0 and Mod.battery_vp <= BatterylistY.get(Mod.module_type, 4500):
									L4log("Battery low", Mod.module_type)
									Battery = "gold"
							oC = oCA = None
							oName = Mod.module_name if na.module_name != "" else Code_utf8(Modulenames.get(Mod.module_type, "?"))
							if Mod.measure.has_co2:
								oC = str(Mod.measure.co2)
							if Mod.module_type == "NAModule3":
								oT = "%s.0" % str(Mod.measure.getSensor("sum_rain_1"))
								if len(oT.split(".")[0]) < 2:
									oT = " " + oT
								self.oM[len(self.oM) - 1].append([oT, str(Mod.measure.getSensor("sum_rain_24")), oC, oCA, oName, Mod.module_type, Battery])
							elif Mod.module_type == "NAModule2":
								oT = str(Mod.measure.wind_strength)
								oTA = str(Mod.measure.wind_angle)
								oC = str(Mod.measure.gust_strength)
								oCA = str(Mod.measure.gust_angle)
								self.oM[len(self.oM) - 1].append([oT, oTA, oC, oCA, oName, Mod.module_type, Battery])
							else:
								oT = "%s.0" % str(Mod.measure.temperature)
								if len(oT.split(".")[0]) < 2:
									oT = " " + oT
								self.oM[len(self.oM) - 1].append([oT, str(Mod.measure.humidity), oC, oCA, oName, Mod.module_type, Battery])
					L4log("iT", "%s" % self.iT)
					L4log("oM", "%s" % self.oM)
					if netatmo.getUint(NetatmoUnit.TEMPERATURE) != "":
						self.TEMPERATURE = netatmo.getUint(NetatmoUnit.TEMPERATURE)
						self.HUMIDITY = netatmo.getUint(NetatmoUnit.HUMIDITY)
						self.CO2 = netatmo.getUint(NetatmoUnit.CO2)
						self.PRESSURE = netatmo.getUint(NetatmoUnit.PRESSURE)
						self.NOISE = netatmo.getUint(NetatmoUnit.NOISE)
						self.MM = netatmo.getUint(NetatmoUnit.MM)
						self.WIND = netatmo.getUint(NetatmoUnit.WIND).replace("beaufort", "Bft")
			except Exception:
				L4logE("Netatmo Error Dataread")
				L4logE("Error:", format_exc())
				try:
					open(CrashFile, "w").write(format_exc())
				except Exception:
					pass

	def BPPlayerEvent(self, func, value):
		if func == 3:
			self.restartTimer()
			if cjukeboxevent.TotalTime == cjukeboxevent.PlayTime and cjukeboxevent.Percent == 100:
				L4logE("GP3", "reset Timer")
				self.GPLlength[1] = 5 * 60 * 90000
				self.GPLposition[1] = 0
		elif func == 2:
			if cjukeboxevent.TotalTime == cjukeboxevent.PlayTime and cjukeboxevent.Percent == 100:
				self.GPLposition[1] += (1 * 90000)
				if self.GPLposition[1] > self.GPLlength[1]:
					self.GPLlength[1] += (60 * 90000)
			else:
				L4logE("use cjukebox")
				self.GPLlength[1] = cjukeboxevent.TotalTime * 90000
				self.GPLposition[1] = cjukeboxevent.PlayTime * 90000
			if (self.GPLposition[1] / 90000) % 10 == 0:
				self.restartTimer()

	def updateStatus(self):
		global DeviceRemove
		global BilderTime
		global OSDtimer
		global OSDon
		global isVideoPlaying
		global ScreenActive
		global AktHelligkeit
		global ScreenTime
		global ThreadRunning
		global FritzTime
		global SamsungDevice
		global SamsungDevice2
		global SamsungDevice3
		self.StatusTimer.stop()
		if not LCD4linux.Enable.value or ThreadRunning > 0:
			if ThreadRunning > 0:
				ThreadRunning += 1
				if ThreadRunning > 40:
					ThreadRunning = 0
				L4log("Thread already running.....")
			self.StatusTimer.startLongTimer(int(LCD4linux.FastMode.value))
			return
		tt = time()
		L4logE("Update...Qlen=", "%s" % Briefkasten.qsize())
		if FritzTime > 0:
			FritzTime -= 1
		if self.AutoOFF != -1:
			self.AutoOFF += 1
			if Standby.inStandby and not self.SonosRunning and not self.YMCastRunning and not self.BlueRunning:
				if LCD4linux.StandbyAutoOFF.value != "0" and self.AutoOFF > int(LCD4linux.StandbyAutoOFF.value):
					self.Refresh = "1"
					self.AutoOFF = -1
					self.restartTimer()
			elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
				if LCD4linux.MPAutoOFF.value != "0" and self.AutoOFF > int(LCD4linux.MPAutoOFF.value):
					self.Refresh = "1"
					self.AutoOFF = -1
					self.restartTimer()
			else:
				if LCD4linux.AutoOFF.value != "0" and self.AutoOFF > int(LCD4linux.AutoOFF.value):
					self.Refresh = "1"
					self.AutoOFF = -1
					self.restartTimer()
		SaveScreenActive = ScreenActive[0]
		if str(LCD4linux.Text.value) != "0" and isfile(LCD4linux.TextFile.value):
			try:
				if self.SaveTXTfile != getmtime(LCD4linux.TextFile.value):
					self.SaveTXTfile = getmtime(LCD4linux.TextFile.value)
					self.Refresh = "1"
					self.restartTimer()
			except Exception:
				pass
		if str(LCD4linux.StandbyText.value) != "0" and isfile(LCD4linux.StandbyTextFile.value):
			try:
				if self.SaveStandbyTXTfile != getmtime(LCD4linux.StandbyTextFile.value):
					self.SaveStandbyTXTfile = getmtime(LCD4linux.StandbyTextFile.value)
					self.Refresh = "1"
					self.restartTimer()
			except Exception:
				pass
		if str(LCD4linux.MPText.value) != "0" and isfile(LCD4linux.MPTextFile.value):
			try:
				if self.SaveMPTXTfile != getmtime(LCD4linux.MPTextFile.value):
					self.SaveMPTXTfile = getmtime(LCD4linux.MPTextFile.value)
					self.Refresh = "1"
					self.restartTimer()
			except Exception:
				pass
		if str(LCD4linux.Bild.value) != "0":
			if isfile(LCD4linux.BildFile.value):
				try:
					if self.SaveBildfile != getmtime(LCD4linux.BildFile.value):
						self.SaveBildfile = getmtime(LCD4linux.BildFile.value)
						self.Refresh = "1"
						self.restartTimer()
				except Exception:
					pass
			else:
				if self.SaveBildfile != 0:
					self.SaveBildfile = 0
					self.Refresh = "1"
					self.restartTimer()
		if str(LCD4linux.StandbyBild.value) != "0":
			if isfile(LCD4linux.StandbyBildFile.value):
				try:
					if self.SaveStandbyBildfile != getmtime(LCD4linux.StandbyBildFile.value):
						self.SaveStandbyBildfile = getmtime(LCD4linux.StandbyBildFile.value)
						self.Refresh = "1"
						self.restartTimer()
				except Exception:
					pass
			else:
				if self.SaveStandbyBildfile != 0:
					self.SaveStandbyBildfile = 0
					self.Refresh = "1"
					self.restartTimer()
		if (str(LCD4linux.ScreenTime.value) != "0" and (not Standby.inStandby or self.SonosRunning or self.YMCastRunning or self.BlueRunning)) or (str(LCD4linux.StandbyScreenTime.value) != "0" and Standby.inStandby):
			NextScreen(False)
		elif SaveEventListChanged == False:
			ScreenActive[0] = LCD4linux.ScreenActive.value

		if str(LCD4linux.BilderTime.value) != "0":
			if BilderTime >= int(LCD4linux.BilderTime.value):
				BilderTime = 0
			BilderTime += 1
		if OSDtimer < 0:
			OSDon = 0
			OSDtimer += 1
			if OSDtimer == 0:
				if Briefkasten.qsize() <= 3:
					Briefkasten.put(6)
				else:
					L4log("Queue full, Thread hanging?")
				if str(LCD4linux.Cal.value) != "0" or str(LCD4linux.StandbyCal.value) != "0" or str(LCD4linux.MPCal.value) != "0" or str(LCD4linux.CalList.value) != "0" or str(LCD4linux.MPCalList.value) != "0" or str(LCD4linux.StandbyCalList.value) != "0":
					if Briefkasten.qsize() <= 3:
						Briefkasten.put(4)
					else:
						L4log("Queue full, Thread hanging?")
				self.getNetatmo()
				getWWW()
		if str(LCD4linux.OSD.value) != "0" and OSDon >= 2:
			if OSDtimer >= int(LCD4linux.OSD.value):
				OSDtimer = 0
				OSDon = 1
				if getFB2(False):
					setFB2("1")
			OSDtimer += 1
		if SonosOK:
			if self.SonosCheckTimer >= int(LCD4linux.SonosCheckTimer.value):
				self.SonosCheckTimer = 0
				self.getSonos()
			else:
				self.SonosCheckTimer += 1
		if self.YMCastCheckTimer >= int(LCD4linux.YMCastCheckTimer.value):
			self.YMCastCheckTimer = 0
			self.getYMCast()
		else:
			self.YMCastCheckTimer += 1
		if self.BlueCheckTimer >= int(LCD4linux.BlueCheckTimer.value):
			self.BlueCheckTimer = 0
			self.getBlue()
		else:
			self.BlueCheckTimer += 1
		if isVideoPlaying != 0:
			isVideoPlaying += 1
		if not self.SonosRunning and not self.YMCastRunning and not self.BlueRunning:
			volctrl = eDVBVolumecontrol.getInstance()
			if volctrl and self.LvolM != volctrl.isMuted():
				self.LisRefresh = True
		if (int(strftime("%M")) % int(LCD4linux.RBoxRefresh.value) == 0 and int(strftime("%S")) > 45 and self.LastwwwBox != strftime("%M")) or self.StandbyChanged != Standby.inStandby:
			self.LastwwwBox = strftime("%M")
			if self.NetworkConnectionAvailable or self.NetworkConnectionAvailable is None:
				if ((str(LCD4linux.RBox.value) != "0" or str(LCD4linux.MPRBox.value) != "0") and (not Standby.inStandby or self.SonosRunning or self.YMCastRunning or self.BlueRunning)) or (str(LCD4linux.StandbyRBox.value) != "0" and Standby.inStandby):
					if "T" in LCD4linux.RBoxShow.value + LCD4linux.MPRBoxShow.value + LCD4linux.StandbyRBoxShow.value:
						CType = 1
					else:
						CType = 0
					self.downloadwwwBox([[LCD4linux.RBoxName1.value, CType], [LCD4linux.RBoxName2.value, CType], [LCD4linux.RBoxName3.value, CType], [LCD4linux.RBoxName4.value, CType], [LCD4linux.RBoxName5.value, CType]])
		if (int(strftime("%M")) % int(LCD4linux.RBoxTimerRefresh.value) == 0 and int(strftime("%S")) > 45 and self.LastwwwBoxTimer != strftime("%M")) or self.StandbyChanged != Standby.inStandby:
			self.LastwwwBoxTimer = strftime("%M")
			if self.NetworkConnectionAvailable or self.NetworkConnectionAvailable is None:
				if ((str(LCD4linux.RBoxTimer.value) != "0" or str(LCD4linux.MPRBoxTimer.value) != "0") and (not Standby.inStandby or self.SonosRunning or self.YMCastRunning or self.BlueRunning)) or (str(LCD4linux.StandbyRBoxTimer.value) != "0" and Standby.inStandby):
					self.downloadwwwBoxTimer([[LCD4linux.RBoxTimerName1.value, 0]])
		if strftime("%M") != self.DataMinute or BilderTime == 1 or self.StandbyChanged != Standby.inStandby or ConfigMode or (ScreenActive[0] != SaveScreenActive) or isVideoPlaying > 2 or OSDon == 3 or FritzTime > 0 or self.LisRecording != self.session.nav.RecordTimer.isRecording() or self.LisRefresh == True:
			L4log("Data-Build")
			self.Refresh = "1"
			self.LisRefresh = False
			isVideoPlaying = 0
			self.LgetGoogleCover = None
			if strftime("%M") != self.DataMinute:
				if int(strftime("%M")) % 3 == 0:
					self.getNetatmo()
				if int(strftime("%M")) % 5 == 0:
					self.SonosSoCo = None
					self.YMCastSoCo = None
					self.BlueSoCo = None
				if LCD4linux.StandbyWetter.value != "0" or LCD4linux.Wetter.value != "0" or LCD4linux.MPWetter.value != "0":
					if strftime("%M") in ("35", "40", "55") or wwwWetter[0] == "":
						self.downloadWetter(LCD4linux.WetterCity.value, 0)
				if LCD4linux.StandbyWetter2.value != "0" or LCD4linux.Wetter2.value != "0" or LCD4linux.MPWetter2.value != "0":
					if strftime("%M") in ("35", "40", "55") or wwwWetter[1] == "":
						self.downloadWetter(LCD4linux.Wetter2City.value, 1)
				if strftime("%M") in LCD4linux.MailTime.value:
					if Briefkasten.qsize() <= 3:
						self.Later6Timer.startLongTimer(15)
					else:
						L4log("Queue full, Thread hanging?")
				if strftime("%M") in LCD4linux.CalTime.value:
					if str(LCD4linux.Cal.value) != "0" or str(LCD4linux.StandbyCal.value) != "0" or str(LCD4linux.MPCal.value) != "0" or str(LCD4linux.CalList.value) != "0" or str(LCD4linux.MPCalList.value) != "0" or str(LCD4linux.StandbyCalList.value) != "0":
						if Briefkasten.qsize() <= 3:
							Briefkasten.put(4)
						else:
							L4log("Queue full, Thread hanging?")
				if strftime("%M") == "30":
					if str(LCD4linux.ExternalIp.value) != "0" or str(LCD4linux.MPExternalIp.value) != "0" or str(LCD4linux.StandbyExternalIp.value) != "0":
						self.ExternalIP = getExternalIP()
					DeviceRemove = []
					try:
						if len(FritzList) > 0:
							for x in range(len(FritzList)):
								if len(FritzList[0][1]) > 1:
									td = datetime.now() - datetime.strptime(FritzList[0][1], "%d.%m.%y %H:%M:%S")
									if td > timedelta(hours=int(LCD4linux.FritzRemove.value)):
										L4log("Remove FritzCall", FritzList[0])
										del FritzList[0]
										rmFile(PICfritz)
					except Exception:
						L4log("Error: Remove FritzCall", "%s" % FritzList)
					if self.NetworkConnectionAvailable is not None:
						L4log("check Network...")
						iNetwork.checkNetworkState(self.checkNetworkCB)
				if str(LCD4linux.StandbyMeteo.value) != "0" or str(LCD4linux.Meteo.value) != "0":
					if divmod(int(strftime("%M")), 5)[1] == 0 or wwwMeteo.find("current_conditions") < 1:
						self.downloadMeteo()
				if LCD4linux.LCDType1.value[0] == "1" or LCD4linux.LCDType2.value[0] == "1" or LCD4linux.LCDType3.value[0] == "1":
					if DpfCheck():
						self.DpfStart()
					else:
						DpfCheckSerial()
				if LCD4linux.LCDType1.value[0] == "2" or LCD4linux.LCDType2.value[0] == "2" or LCD4linux.LCDType3.value[0] == "2":
					if SamsungCheck():
#						SamsungDevice = None
#						SamsungDevice2 = None
#						SamsungDevice3 = None
#						rmFiles(PIC + "*.*")
#						L4log("reset all Samsung LCD!")
						self.SamsungStart()
				if strftime("%M") in LCD4linux.WwwTime.value:
					getWWW()
			self.DataMinute = strftime("%M")
			if self.StandbyChanged != Standby.inStandby:
				self.AutoOFF = 0
				ScreenActive = ["1", "", "", ""]
				AktHelligkeit = [-1, -1, -1, -1, -1, -1]
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
		L4logE("UpdateTime:", "%s" % (time() - tt))

	def restartTimer(self):
		global OSDon
		if not LCD4linux.Enable.value:
			return
		self.ServiceTimer.stop()
		if (OSDon == 2 and LCD4linux.OSDfast.value == False) or ThreadRunning > 0:
			self.ServiceTimer.start(int(LCD4linux.Delay.value) + 500, True)
		else:
			self.ServiceTimer.start(int(LCD4linux.Delay.value), True)

############# Helper functions
	def _getProcVal(self, pathname, base=10):
		val = None
		try:
			with open(pathname, 'r') as f:
				val = int(f.read(), base)
			if val >= 2 ** 31:
				val -= 2 ** 32
		except Exception:
			pass
		return val

	def _getVal(self, pathname, info, infoVal, base=10):
		return self._getProcVal(pathname, base=base) or info.getInfo(infoVal)

	def _getValInt(self, pathname, info, infoVal, base=10, default=-1):
		return self._getVal(pathname, info, infoVal, base) or default

	def _getVideoHeight(self, info):
		return self._getValInt("/proc/stb/vmpeg/0/yres", info, iServiceInformation.sVideoHeight, base=16)

	def _getVideoWidth(self, info):
		return self._getValInt("/proc/stb/vmpeg/0/xres", info, iServiceInformation.sVideoWidth, base=16)

	def _getAspect(self, info):
		return self._getValInt("/proc/stb/vmpeg/0/aspect", info, iServiceInformation.sAspect)
############# End Helper functions

	def ServiceChange(self):
		global ThreadRunning
		if self.ServiceChangeRunning == True:
			L4logE("Service Change running....")
			self.restartTimer()
			return
		self.ServiceChangeRunning = True
		tt = time()
		L4logE("Event Service Change")
		if not self.SonosRunning and not self.YMCastRunning and not self.BlueRunning:
			volctrl = eDVBVolumecontrol.getInstance()
			if volctrl:
				self.LvolM = volctrl.isMuted()
				self.Lvol = volctrl.getVolume()
			else:
				self.LvolM = False
				self.Lvol = None
		self.Ltimer_list = self.recordtimer.timer_list
		self.LisRecording = self.session.nav.RecordTimer.isRecording()
		sref = self.session.nav.getCurrentlyPlayingServiceReference()
		if sref is not None and not self.SonosRunning and not self.YMCastRunning and not self.BlueRunning:
			self.LsreftoString = sref.toString()
			if self.LsreftoString is not None:
				self.LsrefFile = self.LsreftoString[self.LsreftoString.rfind(":") + 1:]
				if self.LsrefFile[:1] != "/":
					tsref = self.LsreftoString[:-len(self.LsrefFile) - 1]
					tsref = tsref[tsref.rfind(":") + 1:]
					if tsref[:1] == "/":
						self.LsrefFile = tsref
			else:
				self.LsrefFile = ""
			ref = eServiceReference(self.LsreftoString)
			self.Lpath = sref.getPath()
			if not self.Lpath or ":0:" in self.Lpath:
				self.Lchannel_num = str(getNumber(ref))
			elif WebRadioFSok == True:
				self.l4l_info = WebRadioFS.get_l4l_info()
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(ref)
			if info is not None:
				self.Lchannel_name = info and Code_utf8(info.getName(ref))
				self.Lchannel_name2 = info and info.getName(ref)
			self.Lcommand = ""
			if self.LsrefFile[:1] == "/" and isfile("%s.meta" % self.LsrefFile):
				try:
					with open("%s.meta" % self.LsrefFile, "r") as f:
						service_name = f.readline().strip()
						self.Lcommand = f.readline().strip()
						self.Lcommand = f.readline().strip()
					ref = eServiceReference(service_name)
					info = serviceHandler.info(ref)
					if info is not None:
						self.Lchannel_name = info and Code_utf8(info.getName(ref))
						self.Lchannel_name2 = info and info.getName(ref)
				except Exception:
					L4logE("Error meta file")
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
			self.LsTagDate = None
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
			self.Llength = None
			service = self.session.nav.getCurrentService()
			self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0 = getServiceInfo(self, 0)
			self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1 = getServiceInfo(self, 1)
			if service is not None:
				self.LisTimeshift = service.timeshift() and service.timeshift().isTimeshiftActive()
				L4logE("Timeshift", self.LisTimeshift)
				if self.Lpath:  # Movie
					seek = service and service.seek()
					if seek:
						self.Llength = seek.getLength()
						self.Lposition = seek.getPlayPosition()
						if self.Llength is not None:
							if self.Llength == [0, 0]:
								self.Llength = [-1, 7776000000]
							if self.Llength[1] >= 7776000000:
								self.Llength[1] = 7776000000
					else:
						self.Llength = None
						self.Lposition = None

				info = service and service.info()
				if info is not None:
					if BitrateRegistred == True and not Standby.inStandby and ((str(LCD4linux.Bitrate.value) != "0" and isMediaPlayer == "") or (str(LCD4linux.MPBitrate.value) != "0" and isMediaPlayer != "")):
						if self.ref != self.LsreftoString:
							self.startBitrateData()
					self.LgetName = info.getName()
					if self.LsreftoString.startswith("1:") and not self.Lpath:
						self.Lprovider = info.getInfoString(iServiceInformation.sProvider)
						self.LtransponderData = info.getInfoObject(iServiceInformation.sTransponderData)
					elif self.Lpath and self.Lpath.startswith("http"):
						self.LtransponderData = {'orbital_position': None, 'tuner_type': 'IPTV'}
						try:
							self.Lprovider = getIPTVProvider(self.Lpath)
						except ImportError as err:
							L4logE("self.Lprovider %s" % err)
					L4logE("self.Transponderdata2 %s" % self.LtransponderData)
					self.LsVideoWidth = self._getVideoWidth(info)
					self.LsVideoHeight = self._getVideoHeight(info)
					self.LsIsCrypted = info.getInfo(iServiceInformation.sIsCrypted)
					self.LsAspect = info.getInfo(iServiceInformation.sAspect)
					if self.LsAspect == 1:
						self.LsAspect = info.getInfo(iServiceInformation.sAspect)
					self.LsTagAlbum = info.getInfoString(iServiceInformation.sTagAlbum)
					self.LsTagTitle = info.getInfoString(iServiceInformation.sTagTitle)
					self.LsTagArtist = info.getInfoString(iServiceInformation.sTagArtist)
					self.LsTagGenre = info.getInfoString(iServiceInformation.sTagGenre)
					self.LsTagDate = info.getInfoString(iServiceInformation.sTagDate)
					event = info and info.getEvent(0)
					if event:
						self.LShortDescription = event.getShortDescription()
						self.LExtendedDescription = event.getExtendedDescription()
				feinfo = service.frontendInfo()
				if feinfo is not None:
					self.LsignalQuality = feinfo.getFrontendInfo(iFrontendInformation.signalQuality)
					if self.LtransponderData is not None and self.LtransponderData.get("tuner_type", "") == "DVB-T":
						if LCD4linux.DVBTCorrection.value == "reverse":
							self.LsignalQuality = abs(65536 - self.LsignalQuality)
						elif LCD4linux.DVBTCorrection.value == "usb":
							self.LsignalQuality = min(self.LsignalQuality * 256, 65536)
					self.LsignalQualitydB = feinfo.getFrontendInfo(iFrontendInformation.signalQualitydB)
					if self.LsignalQualitydB > 50000:
						self.LsignalQualitydB = 0
					self.LbitErrorRate = feinfo.getFrontendInfo(iFrontendInformation.bitErrorRate)
					data = feinfo and feinfo.getAll(False)
					if data:
						self.Ltuner_number = data.get("tuner_number", -1)
				audio = service.audioTracks()
				if audio:
					self.LaudioTracks = audio.getNumberOfTracks()
					self.LaudioCurrentTrack = audio.getCurrentTrack()
					if self.LaudioCurrentTrack is not None and self.LaudioCurrentTrack >= 0:
						i = audio.getTrackInfo(self.LaudioCurrentTrack)
						self.Laudiodescription = i.getDescription()
						L4logE("Audio activ %d" % self.LaudioCurrentTrack, self.Laudiodescription)
					else:
						for idx in range(self.LaudioTracks):
							i = audio.getTrackInfo(idx)
							self.Laudiodescription = i.getDescription()
							L4logE("Audio %d" % idx, self.Laudiodescription)
			self.LEventsDesc = None
			_LsreftoString = None
			if self.LsreftoString.startswith(("4097:0", "5001:0", "5002:0", "5003")):
				_LsreftoString = self.LsreftoString.replace("4097:0", "1:0", 1).replace("5001:0", "1:0", 1).replace("5002:0", "1:0", 1).replace("5003:0", "1:0", 1)
				epgcache = eEPGCache.getInstance()
				if epgcache is not None:
					self.LEventsNext = epgcache.lookupEvent(['RIBDT', (_LsreftoString or self.LsreftoString, 0, -1, 1440)])
					self.LEventsDesc = epgcache.lookupEvent(['IBDCTSERNX', (_LsreftoString or self.LsreftoString, 0, -1)])
		else:
			if GPjukeboxOK == True and cjukeboxevent.LastStatus != "":
				self.LsreftoString = "4097:0:0:0:0:0:0:0:0:0:" + cjukeboxevent.CurrSource
				self.Lchannel_name = cjukeboxevent.CurrSource
				self.LsTagTitle = Code_utf8(cjukeboxevent.PlayTitle)
				self.LgetName = self.LsTagTitle
				self.Llength = self.GPLlength
				self.Lposition = self.GPLposition
				self.Lpath = cjukeboxevent.CurrSource
			elif self.SonosRunning:
				self.LsreftoString = "4097:0:0:0:0:0:0:0:0:0:Sonos"
				self.Lchannel_name = "Sonos"
				self.LsTagAlbum = Code_utf8(self.SonosTrack.get("album", ""))
				self.LsTagArtist = Code_utf8(self.SonosTrack.get("artist", ""))
				self.LsTagTitle = Code_utf8(self.SonosTrack.get("title", ""))
				self.LgetName = self.LsTagTitle
				try:
					dt = datetime.strptime(self.SonosTrack.get("duration", "0:05:00"), "%H:%M:%S")
					self.Llength = [1, (dt.hour * 3600 + dt.minute * 60 + dt.second) * 90000]
					dt = datetime.strptime(self.SonosTrack.get("position", "0:00:00"), "%H:%M:%S")
					self.Lposition = [1, (dt.hour * 3600 + dt.minute * 60 + dt.second) * 90000]
				except Exception:
					self.SonosSoCo = None
					L4log("Sonos Time Error", "%s" % self.SonosTrack)
				self.Lpath = "Sonos"
				self.LShortDescription = ""
				self.LExtendedDescription = ""
				self.LEventsDesc = None
			elif self.YMCastRunning:
				self.LsreftoString = "4097:0:0:0:0:0:0:0:0:0:MusicCast"
				self.Lchannel_name = "MusicCast"
				self.LsTagAlbum = Code_utf8(self.YMCastInfo.get("album", ""))
				self.LsTagArtist = Code_utf8(self.YMCastInfo.get("artist", ""))
				self.LsTagTitle = Code_utf8(self.YMCastInfo.get("track", ""))
				self.LgetName = self.LsTagTitle
				if self.LsTagTitle == "":
					self.LsTagTitle = self.Lchannel_name
				elif self.LsTagArtist is not None and self.LsTagAlbum is not None and self.LsTagArtist != "" and self.LsTagAlbum != "":
					self.LsTagTitle = self.LsTagArtist + " - " + self.LsTagTitle
				pt = int(self.YMCastInfo.get("play_time", 0))
				tt = int(self.YMCastInfo.get("total_time", 0))
				if self.YMCastoldTitle != (self.LsTagTitle + self.LsTagArtist + self.YMCastInfo.get("albumart_url", "")) and self.YMCastSoCo is not None:
					rmFile(GoogleCover)
					self.YMCastPlaytime = pt
					self.YMCastoldTitle = (self.LsTagTitle + self.LsTagArtist + self.YMCastInfo.get("albumart_url", ""))
					if (LCD4linux.YMCastCover.value == "0" or self.LsTagTitle == "MusicCast"):
						if self.YMCastInfo.get("input", "") == "mc_link" and LCD4linux.YMCastServerIP.value != "":
							try:
								YMCastServer = YMC(LCD4linux.YMCastServerIP.value)
								url = "http://%s%s" % (YMCastServer.IP, YMCastServer.getPlayInfo().get("albumart_url", ""))
							except Exception:
								L4logE("YMC Server Error")
								url = ""
						else:
							url = "http://%s%s" % (self.YMCastSoCo.IP, self.YMCastInfo.get("albumart_url", ""))
						L4logE("YMC GetPic:", url)
						self.getSonosPic(GoogleCover, str(url))
				if tt == 0:
					tm = 5 if pt - self.YMCastPlaytime < 5 * 60 else int(pt / 60) + 1
					self.Llength = [1, (tm * 60) * 90000]
					self.Lposition = [1, (pt - self.YMCastPlaytime) * 90000]
				else:
					self.Llength = [1, tt * 90000]
					self.Lposition = [1, pt * 90000]
				self.Lpath = "MusicCast"
				self.LShortDescription = ""
				self.LExtendedDescription = ""
				self.LEventsDesc = None
			elif self.BlueRunning:
				self.LsreftoString = "4097:0:0:0:0:0:0:0:0:0:BlueSound"
				self.Lchannel_name = "BlueSound"
				self.LsTagAlbum = Code_utf8(self.BlueInfo.get("album", ""))
				self.LsTagArtist = Code_utf8(self.BlueInfo.get("artist", ""))
				self.LsTagTitle = Code_utf8(self.BlueInfo.get("name", ""))
				self.LgetName = self.LsTagTitle
				pt = int(self.BlueInfo.get("secs", 0))
				tt = int(self.BlueInfo.get("totlen", 0))
				self.Llength = [1, tt * 90000]
				self.Lposition = [1, pt * 90000]
				self.Lpath = "BlueSound"
				self.LShortDescription = ""
				self.LExtendedDescription = ""
				self.LEventsDesc = None
			else:
				self.LsreftoString = None
				self.Lchannel_name = None
				self.Llength = None
				self.Lposition = None
				self.Lpath = None
			self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0 = 0, 0, 0, ""
			self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1 = 0, 0, 0, ""
			self.Lchannel_num = ""
			self.LsVideoWidth = None
			self.LsVideoHeight = None
			self.LsIsCrypted = None
			self.LsAspect = None
			self.Laudiodescription = None
		self.ServiceChangeRunning = False
		L4logE("Service Change Time:", "%s" % (time() - tt))
		if L4LdoThread == True:
			if ThreadRunning > 0:
				ThreadRunning += 1
				if ThreadRunning > 40:
					ThreadRunning = 0
				self.ServiceTimer.startLongTimer(int(LCD4linux.FastMode.value))
				L4log("Thread already running")
				return
			if BriefLCD.qsize() <= 2:
				BriefLCD.put(1)
			else:
				L4log("LCD-Queue full, Thread hanging?")
		else:
			LCD4linuxPIC(self, session)

	def runBitrateTimer(self):
		self.BitrateTimer.stop()
		if BitrateRegistred == True and not Standby.inStandby and ((str(LCD4linux.Bitrate.value) != "0" and isMediaPlayer == "") or (str(LCD4linux.MPBitrate.value) != "0" and isMediaPlayer != "")):
			self.startBitrateData()
		self.BitrateTimer.startLongTimer(30)

	def stopBitrateData(self, TYP):
		L4logE("Bitrate Stop", TYP)
		if "V" in TYP and self.videoBitrate is not None:
			self.videoBitrate.callback.remove(self.getVideoBitrateData)
			self.videoBitrate = None
		if "A" in TYP and self.audioBitrate is not None:
			self.audioBitrate.callback.remove(self.getAudioBitrateData)
			self.audioBitrate = None

	def startBitrateData(self):
		if BITRATE in RegisteredBitrate and PreferredBitrate == BITRATE:
			if self.bitrate is None:
				self.bitrate = Bitrate(session, self.getBitrateData, None)
			self.bitrate.start()
		if BITRATEVIEWER in RegisteredBitrate and PreferredBitrate == BITRATEVIEWER:
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
						self.videoBitrate = eBitrateCalculator(vpid, ref, 3000, 1024 * 1024)
						self.videoBitrate.callback.append(self.getVideoBitrateData)
					else:
						self.LvideoBitrate = ""
					if apid:
						self.audioBitrate = eBitrateCalculator(apid, ref, 3000, 64 * 1024)
						self.audioBitrate.callback.append(self.getAudioBitrateData)
					else:
						self.LaudioBitrate = ""
				else:
					self.LvideoBitrate = ""
					self.LaudioBitrate = ""
			else:
				self.LvideoBitrate = ""
				self.LaudioBitrate = ""

	def getVideoBitrateData(self, value, status):
		if status:
			self.LvideoBitrate = value
		else:
			self.videoBitrate = None
			self.LvideoBitrate = ""
		self.stopBitrateData("V")

	def getAudioBitrateData(self, value, status):
		if status:
			self.LaudioBitrate = value
		else:
			self.audioBitrate = None
			self.LaudioBitrate = ""
		self.stopBitrateData("A")

	def getBitrateData(self):
		if self.bitrate is not None:
			self.LvideoBitrate = int(self.bitrate.vcur)
			self.LaudioBitrate = int(self.bitrate.acur)
			self.bitrate.stop()

	def rcKeyPressed(self, key, flag):
		global OSDon
		global OSDtimer
		global LCDon
		global ScreenTime
		global ScreenActive
		global SaveEventListChanged
		if (SaveEventListChanged == True or ScreenActive[-3:] != ["", "", ""]) and L4LElist.getHoldKey() == False:
			L4log("Reset Event Changed")
			SaveEventListChanged = False
			ScreenActive = ["1", "", "", ""]
			LCD4linux.ScreenActive.value = ScreenActive[0]
			ScreenTime = 0
			self.Refresh = "1"
			self.restartTimer()
		L4logE("Key", "%s %s" % (key, flag))  # Long: flag=3
		self.k = int(LCD4linux.KeyScreen.value[:3])
		self.ko = int(LCD4linux.KeyOff.value[:3])
		if self.AutoOFF == -1:
			self.Refresh = "1"
			self.restartTimer()
		self.AutoOFF = 0
		if (key == 113 and int(LCD4linux.PopupKey.value) == 0) or int(LCD4linux.PopupKey.value) == 1:  # MUTE
			if len(PopText[1]) > 2:
				setPopText("")
				self.Refresh = "1"
				self.restartTimer()
		if LCD4linux.KeySwitch.value == True:
			if flag == 3:
				if LCD4linux.KeyScreen.value[-1:] == "1" and key == self.k:
					ScreenTime = 9999
					L4logE("Restart at Scr-longkey")
					NextScreen(True)
					LCD4linux.ScreenActive.value = ScreenActive[0]
					self.Refresh = "1"
					self.restartTimer()
				elif LCD4linux.KeyOff.value[-1:] == "1" and key == self.ko:
					LCDon = True if LCDon == False else False
					L4logE("Restart at Off-longkey")
					self.Refresh = "1"
					self.restartTimer()
			else:
				if time() - self.KeyTime > 2 or (isMediaPlayer != "" and isMediaPlayer != "radio"):
					self.KeyDoppel = 0
				self.KeyTime = time()
				if self.KeyDoppel == key and flag == 0:
					self.KeyDoppel = 0
					if LCD4linux.KeyOff.value[-1:] != "1" and key == self.ko:  # PREVIOUS
						LCDon = True if LCDon == False else False
						L4logE("Restart at Off-doublekey", key)
						self.Refresh = "1"
						self.restartTimer()
					elif LCD4linux.KeyScreen.value[-1:] != "1" and key == self.k:  # FORWARD / INFO
						ScreenTime = 9999
						NextScreen(True)
						LCD4linux.ScreenActive.value = ScreenActive[0]
						L4logE("Restart at Scr-doublekey", key)
						self.Refresh = "1"
						self.restartTimer()
				elif flag == 0:
					self.KeyDoppel = key
					if OSDon == 2 and key == self.k:
						OSDon = 1
						OSDtimer = 1
						L4logE("Restart at key and OSD=2")
						self.Refresh = "1"
						self.restartTimer()
				if (key == self.ko or key == self.k) and int(LCD4linux.PopupKey.value) == 0:
					if len(PopText[1]) > 2:
						setPopText("")
						self.Refresh = "1"
						self.restartTimer()
		if OSDon != 0:
			L4logE("Restart at key and OSD")
			self.Refresh = "1"
			self.restartTimer()
			OSDon = 2
			OSDtimer = 0
			if getFB2(True):
				setFB2("0")
		if ScreenActive[0] in LCD4linux.Vol.value or ScreenActive[0] in LCD4linux.MPVol.value:
			if key in [114, 115]:
				L4logE("Restart at volume")
				self.restartTimer()

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

	def downloadwwwBox(self, elements):
		i = 0
		for wwwURL in elements:
			try:
				if len(wwwURL[0]) > 4:
					L4logE("wwwBox %d" % i, wwwURL)
					self.wwwBox[i][0] = wwwURL[0].split(":")[0]
					Auth = wwwURL[0].split("@")
					if Auth[-1].split(":")[-1].isdigit():
						URL = ":".join(Auth[-1].split(":")[-2:])
					else:
						URL = Auth[-1].split(":")[-1]
					Header = None
					if len(Auth) > 1 and len(Auth[0].split(":", 1)[-1].split(":")) == 2:
						username, password = Auth[0].split(":", 1)[-1].split(":")
						up = "%s:%s" % (username, password)
						basicAuth = b64encode(ensure_binary(up))
						if PY3:
							basicAuth = basicAuth.decode()
						Header = {"Authorization": "Basic %s" % basicAuth}
					if wwwURL[1] == 0:
						feedurl = "http://%s/web/subservices" % URL
					else:
						feedurl = "http://%s/web/getcurrent" % URL
					callInThread(getPage, feedurl, boundFunction(self.downloadwwwBoxCallback, i), boundFunction(self.downloadwwwBoxError, i), headers=Header)
					L4log("wwwBox %d" % i, URL)
			except Exception:
				L4log("wwwBox Syntax Error", wwwURL)
				L4log("Error:", format_exc())
			i += 1

	def downloadwwwBoxCallback(self, element, page=""):
		sR = sN = sS = ""
		page = ensure_str(page)
		dom = parseString(page)
		serv = dom.getElementsByTagName("e2servicename")
		if len(serv) > 0 and len(serv[0].childNodes) > 0:
			sN = serv[0].childNodes[0].nodeValue.replace("N/A", "")
			serv = dom.getElementsByTagName("e2servicereference")
			if len(serv) > 0 and len(serv[0].childNodes) > 0:
				sR = serv[0].childNodes[0].nodeValue.replace("N/A", "")
			serv = dom.getElementsByTagName("e2eventname")
			if len(serv) > 0 and len(serv[0].childNodes) > 0:
				sS = serv[0].childNodes[0].nodeValue.replace("N/A", "")
		self.wwwBox[element] = [self.wwwBox[element][0], sR, sN, sS]
		L4logE("wwwBox %d" % element, self.wwwBox[element])

	def downloadwwwBoxError(self, element, error=""):
		self.wwwBox[element] = [[""], [""], [""], [""], [""]]
		if error == "":
			L4log("wwwBox Error %d?" % element)
		else:
			L4log("wwwBox Error %d" % element, str(error))

	def downloadwwwBoxTimer(self, elements):
		i = 0
		for wwwURL in elements:
			L4log("wwwBoxTimerS %d" % i, wwwURL)
			try:
				if len(wwwURL[0]) > 4:
					L4logE("wwwBoxTimer %d" % i, wwwURL)
					self.wwwBox[i][0] = wwwURL[0].split(":")[0]
					Auth = wwwURL[0].split("@")
					if Auth[-1].split(":")[-1].isdigit():
						URL = ":".join(Auth[-1].split(":")[-2:])
					else:
						URL = Auth[-1].split(":")[-1]
					Header = None
					if len(Auth) > 1 and len(Auth[0].split(":", 1)[-1].split(":")) == 2:
						username, password = Auth[0].split(":", 1)[-1].split(":")
						up = "%s:%s" % (username, password)
						basicAuth = b64encode(ensure_binary(up))
						if PY3:
							basicAuth = basicAuth.decode()
						Header = {"Authorization": "Basic %s" % basicAuth}
					feedurl = "http://%s/web/timerlist" % URL
					L4log("wwwBoxTimer %d" % i, feedurl)
					callInThread(getPage, feedurl, boundFunction(self.downloadwwwBoxTimerCallback, i), boundFunction(self.downloadwwwBoxTimerError, i), headers=Header)
					L4log("wwwBoxTimer %d" % i, URL)
			except Exception:
				L4log("wwwBoxTimer Syntax Error", wwwURL)
				L4log("Error:", format_exc())
			i += 1

	def downloadwwwBoxTimerCallback(self, element, page=""):
		L4logE("download BoxTimer", element)
		self.wwwBoxTimer = []
		page = ensure_str(page)
		dom = parseString(page)
		serv = dom.getElementsByTagName("e2timer")
		L4logE("download BoxTimer Count", "%s" % len(serv))
		for e2timer in serv:
			e2t = myE2Timer()
			e2state = 0
			serv = e2timer.getElementsByTagName("e2state")
			if len(serv) > 0 and len(serv[0].childNodes) > 0:
				e2state = int(serv[0].childNodes[0].nodeValue)
			if e2state == 0:
				serv = e2timer.getElementsByTagName("e2name")
				if len(serv) > 0 and len(serv[0].childNodes) > 0:
					e2t.name = serv[0].childNodes[0].nodeValue
				serv = e2timer.getElementsByTagName("e2timebegin")
				if len(serv) > 0 and len(serv[0].childNodes) > 0:
					e2t.begin = int(serv[0].childNodes[0].nodeValue)
				serv = e2timer.getElementsByTagName("e2timeend")
				if len(serv) > 0 and len(serv[0].childNodes) > 0:
					e2t.end = int(serv[0].childNodes[0].nodeValue)
				serv = e2timer.getElementsByTagName("e2disabled")
				if len(serv) > 0 and len(serv[0].childNodes) > 0:
					e2t.disabled = int(serv[0].childNodes[0].nodeValue)
				serv = e2timer.getElementsByTagName("e2justplay")
				if len(serv) > 0 and len(serv[0].childNodes) > 0:
					e2t.justplay = int(serv[0].childNodes[0].nodeValue)
				serv = e2timer.getElementsByTagName("e2servicereference")
				if len(serv) > 0 and len(serv[0].childNodes) > 0:
					e2t.service_ref = serv[0].childNodes[0].nodeValue
				serv = e2timer.getElementsByTagName("e2state")
				if len(serv) > 0 and len(serv[0].childNodes) > 0:
					e2t.state = int(serv[0].childNodes[0].nodeValue)

				self.wwwBoxTimer.append(e2t)
				L4logE("wwwBoxTimer", "%s" % e2t.values())

	def downloadwwwBoxTimerError(self, element, error=""):
		self.wwwBoxTimer = []
		if error == "":
			L4log("wwwBox Error %d?" % element)
		else:
			L4log("wwwBox Error %d" % element, str(error))

	def downloadMeteo(self):
		global wwwMeteo
		L4log("Meteodownloadstart")
		self.feedurl = ensure_str(LCD4linux.MeteoURL.value)
		try:
			wwwMeteo = ensure_str(urlopen(self.feedurl, timeout=5).read())
		except Exception:
			L4log("Error download Meteo!")
		rmFile(PICmeteo)

	def downloadWetter(self, ort, wetter):
		if self.NetworkConnectionAvailable or self.NetworkConnectionAvailable is None:
			la = language.getLanguage().replace("_", "-").lower()
			city = quote(ort)
			coords = LCD4linux.WetterCoords.value.split(",")
			coords2 = LCD4linux.Wetter2Coords.value.split(",")
			self.Long[wetter], self.Lat[wetter] = ("0", "0")
			if wetter == 0 and LCD4linux.WetterCoords.value != "0,0" and len(coords) == 2:
				self.Long[0], self.Lat[0] = (str(coords[0]), str(coords[1]))
				L4log("Wetter0: successfully get coordinates from settings (lon=%s, lat=%s)" % (coords[0], coords[1]))
			if wetter == 1 and LCD4linux.Wetter2Coords.value != "0,0" and len(coords2) == 2:
				self.Long[1], self.Lat[1] = (str(coords2[0]), str(coords2[1]))
				L4log("Wetter1: successfully get coordinates from settings (lon=%s, lat=%s)" % (coords2[0], coords2[1]))

			if LCD4linux.WetterApi.value == "MSN":
				if float(self.Long[wetter]) == 0 and float(self.Lat[wetter]) == 0:
					self.feedurl = "https://geocoding-api.open-meteo.com/v1/search?language=%s&count=10&name=%s" % (la[:2], city)
					L4logE("MSN-citysearch%s: %s" % (wetter, self.feedurl))
					callInThread(getPage, self.feedurl, boundFunction(self.getCityCoords, wetter), self.downloadListError)
				else:
					feed = "68747470733A2F2F6170692E6D736E2E636F6D2F7765617468657266616C636F6E2F776561746865722F6F766572766965773F266C6F6E3D2573266C61743D2573266C6F63616C653D257326756E6974733D25732661707049643D39653231333830632D666631392D346337382D623465612D313935353865393361356433266170694B65793D6A356934674471484C366E47597778357769356B5268586A74663263357167465839667A666B30544F6F26777261704F446174613D66616C73653"
					L4logE("MSN-getweather%s: starting..." % wetter)
					if PY3:
						self.feedurl = bytes.fromhex(feed[:-1]).decode('utf-8') % (float(self.Long[wetter]), float(self.Lat[wetter]), la, "C") if PY3 else bytearray.fromhex(feed[:-1]).decode('utf-8') % (float(self.Long[wetter]), float(self.Lat[wetter]), la, "C")
					else:
						self.feedurl = bytearray.fromhex(feed[:-1]) % (float(self.Long[wetter]), float(self.Lat[wetter]), la, "C") if PY3 else bytearray.fromhex(feed[:-1]).decode('utf-8') % (float(self.Long[wetter]), float(self.Lat[wetter]), la, "C")
					callInThread(getPage, self.feedurl, boundFunction(self.downloadMSNcallback, wetter), self.downloadListError)

			elif LCD4linux.WetterApi.value == "OPENMETEO":
				if float(self.Long[wetter]) == 0 and float(self.Lat[wetter]) == 0:
					self.feedurl = "https://geocoding-api.open-meteo.com/v1/search?language=%s&count=10&name=%s" % (la[:2], city)
					L4logE("OM-citysearch%s: %s" % (wetter, self.feedurl))
					callInThread(getPage, self.feedurl, boundFunction(self.getCityCoords, wetter), self.downloadListError)
				else:
					timezones = {"-06": "America/Anchorage", "-05": "America/Los_Angeles", "-04": "America/Denver", "-03": "America/Chicago", "-02": "America/New_York",
				  				"-01": "America/Sao_Paulo", "+00": "Europe/London", "+01": "Europe/Berlin", "+02": "Europe/Moscow", "+03": "Africa/Cairo",
		  						"+04": "Asia/Bangkok", "+05": "Asia/Singapore", "+06": "Asia/Tokyo", "+07": "Australia/Sydney", "+08": "Pacific/Auckland"}
					currzone = timezones.get(strftime("%z", gmtime())[:3], "Europe/Berlin")
					self.feedurl = "https://api.open-meteo.com/v1/forecast?longitude=%s&latitude=%s&hourly=temperature_2m,relativehumidity_2m,apparent_temperature,weathercode,windspeed_10m,winddirection_10m,precipitation_probability&daily=sunrise,sunset,weathercode,precipitation_probability_max,temperature_2m_max,temperature_2m_min&timezone=%s&windspeed_unit=kmh&temperature_unit=celsius" % (float(self.Long[wetter]), float(self.Lat[wetter]), currzone)
					L4logE("OM-getweather%s: %s" % (wetter, self.feedurl))
					callInThread(getPage, self.feedurl, boundFunction(self.downloadOMcallback, wetter), self.downloadListError)

			elif LCD4linux.WetterApi.value == "OPENWEATHER":
				if float(self.Long[wetter]) == 0 and float(self.Lat[wetter]) == 0:
					self.feedurl = "https://geocoding-api.open-meteo.com/v1/search?language=%s&count=10&name=%s" % (la[:2], city)
					L4logE("OWM-citysearch%s: %s" % (wetter, self.feedurl))
					callInThread(getPage, self.feedurl, boundFunction(self.getCityCoords, wetter), self.downloadListError)
				else:
					apkey = LCD4linux.WetterApiKeyOpenWeatherMap.value if len(LCD4linux.WetterApiKeyOpenWeatherMap.value) > 5 else ""
					self.feedurl = "https://api.openweathermap.org/data/3.0/onecall?&lon=%s&lat=%s&units=metric&exclude=hourly,minutely,current&lang=%s&appid=%s" % (self.Long[wetter], self.Lat[wetter], la[:2], apkey)
					L4logE("OWM-getOneCallWeather%s: %s" % (wetter, self.feedurl))
					callInThread(getPage, self.feedurl, boundFunction(self.downloadOWMcallback, wetter), self.downloadListError)

			elif LCD4linux.WetterApi.value == "WEATHERUNLOCKED":
				apkey = "?app_id=%s&app_key=%s" % (LCD4linux.WetterApiKeyWeatherUnlocked.value.split()[0], LCD4linux.WetterApiKeyWeatherUnlocked.value.split()[1]) if len(LCD4linux.WetterApiKeyWeatherUnlocked.value.split()) == 2 else ""
				lang = "&lang=%s" % ort.split(".")[0] if "." in ort else ""
				city = LCD4linux.WetterCity.value if wetter == 0 else LCD4linux.Wetter2City.value
				if "." in city:  # e.g. 'de.ZIPccode'
					self.feedurl = "http://api.weatherunlocked.com/api/current/%s%s%s" % (city, apkey, lang)
				else:
					self.feedurl = "http://api.weatherunlocked.com/api/current/%s,%s%s%s" % (self.Long[wetter], self.Lat[wetter], apkey, lang)
				L4logE("WU-getcurrentweather%s: %s" % (wetter, self.feedurl))
				callInThread(getPage, self.feedurl, boundFunction(self.downloadWUcallback, wetter), self.downloadListError)
				if "." in city:  #  e.g. 'de.ZIPcode'
					self.feedurl = "http://api.weatherunlocked.com/api/forecast/%s%s%s" % (city, apkey, lang)
				else:
					self.feedurl = "http://api.weatherunlocked.com/api/forecast/%s,%s%s%s" % (self.Long[wetter], self.Lat[wetter], apkey, lang)
				L4logE("WU-getforecastweather%s: %s" % (wetter, self.feedurl))
				callInThread(getPage, self.feedurl, boundFunction(self.downloadWUcallback, wetter), self.downloadListError)
			L4log("Wetter%s: downloadstart %s:%s %s %s" % (wetter, LCD4linux.WetterApi.value, ort, language.getLanguage(), la))
		else:
			if self.NetworkConnectionAvailable is not None:
				L4log("Wetter%s: check Network..." % wetter)
				iNetwork.checkNetworkState(self.checkNetworkCB)

	def downloadListError(self, error=""):
		L4log("Wetterdownload Error: %s" % error)
		self.WetterOK = False

	def saveGeodata(self, wetter, Cityname, Long, Lat):
			self.Long[wetter] = Long
			self.Lat[wetter] = Lat
			if wetter == 0:
				LCD4linux.WetterCity.value = Cityname
				LCD4linux.WetterCity.save()
				LCD4linux.WetterCoords.value = "%s,%s" % (Long, Lat)
				LCD4linux.WetterCoords.save()
			else:
				LCD4linux.Wetter2City.value = Cityname
				LCD4linux.Wetter2City.save()
				LCD4linux.Wetter2Coords.value = "%s,%s" % (Long, Lat)
				LCD4linux.Wetter2Coords.save()
			try:
				LCD4linux.saveToFile(LCD4config)
				L4log("Wetter%s-saveGeodata: successful" % wetter)
			except Exception:
				L4log("Wetter%s-saveGeodata Error: 'lcd4config' is in use by other process, retrying next time..." % wetter)

	def getCityCoords(self, ConfigWWW, jsonData):
		try:
			results = loads(jsonData).get("results", [None])[0]
		except Exception as err:
			self.WetterOK = False
			L4log("Wetter%s-citysearch: invalid json data from MSN-server: %s" % (ConfigWWW, str(err)))
			return
		if results:
			cityname = results["name"] if "name" in results else ""
			country = ", %s" % results["country"].upper() if "country" in results else ""
			admin1 = ", %s" % results["admin1"] if "admin1" in results else ""
			admin2 = ", %s" % results["admin2"] if "admin2" in results else ""
			admin3 = ", %s" % results["admin3"] if "admin3" in results else ""
			self.saveGeodata(ConfigWWW, cityname, results["longitude"], results["latitude"])
			L4log("Wetter%s-citysearch: lon= %s, lat= %s for %s" % (ConfigWWW, self.Long[ConfigWWW], self.Lat[ConfigWWW], "%s%s%s%s%s" % (cityname, admin1, admin2, admin3, country)))
		else:
			L4log("Wetter%s-citysearch Error: no data found." % ConfigWWW)

	def downloadMSNcallback(self, ConfigWWW, jsonData):
		iconmap = {"d000": "32", "d100": "34", "d200": "30", "d210": "12", "d211": "5", "d212": "14", "d220": "11", "d221": "42",
		 			"d222": "16", "d240": "4", "d300": "28", "d310": "11", "d311": "5", "d312": "14", "d320": "39", "d321": "5",
					"d322": "16", "d340": "4", "d400": "26", "d410": "9", "d411": "5", "d412": "14", "d420": "9", "d421": "5",
					"d422": "16", "d430": "12", "d431": "5", "d432": "15", "d440": "4", "d500": "28", "d600": "20", "d603": "10",
					"d605": "17", "d705": "17", "d900": "21", "d905": "17", "d907": "21", "n000": "31", "n100": "33", "n200": "29",
					"n210": "45", "n211": "5", "n212": "46", "n220": "45", "n221": "5", "n222": "46", "n240": "47", "n300": "27",
					"n310": "45", "n311": "11", "n312": "46", "n320": "45", "n321": "5", "n322": "46", "n340": "47", "n400": "26",
					"n410": "9", "n411": "5", "n412": "14", "n420": "9", "n421": "5", "n422": "14", "n430": "12", "n431": "5",
					"n432": "15", "n440": "4", "n500": "29", "n600": "20", "n603": "10", "n605": "17", "n705": "17", "n900": "21",
					"n905": "17", "n907": "21"
					}  # mapping: msn -> yahoo+
		global wwwWetter
		self.WetterOK = False
		wwwWetter[ConfigWWW] = ""
		L4log("MSN-weather%s: download OK" % ConfigWWW)
		r = {}
		try:
			r = loads(jsonData).get("responses", [None])[0]
		except Exception as err:
			L4log("MSN-weather%s: json-download Error: %s" % (ConfigWWW, str(err)))
			return
		L4log("MSN-weather%s data ready" % ConfigWWW)
		L4logE("MSN-weather%s data: {placeholder for a large json-string}" % ConfigWWW)
		if r is not None:
			L4log("MSN-weather%s: analysing current & forecasts..." % ConfigWWW)
			self.WetterOK = True
			wwwWetter[ConfigWWW] = r
			self.WDay[ConfigWWW] = {}
			current = r.get("weather", {})[0].get("current", {})
			forecast = r.get("weather", {})[0].get("forecast", {}).get("days", {})
			datenow = datetime.now().strftime("%Y-%m-%d")
			currdate = datetime.fromisoformat(current.get("created", datenow)) if PY3 else isoparse(current.get("created", datenow))
			self.WDay[ConfigWWW]["Wtime"] = currdate.strftime("%H:%M")
			self.WDay[ConfigWWW]["Locname"] = LCD4linux.WetterCity.value if ConfigWWW == 0 else LCD4linux.Wetter2City.value
			self.WDay[ConfigWWW]["Temp_c"] = "%.0f" % current.get("temp", 0)
			self.WDay[ConfigWWW]["Hum"] = "%.0f%%" % current.get("rh", 0)
			if LCD4linux.WetterWind.value == "0":
				self.WDay[ConfigWWW]["Wind"] = "%.0f km/h %s" % (current.get("windSpd", 0), getDirection(current.get("windDir", "na")))
			else:
				self.WDay[ConfigWWW]["Wind"] = "%.1f m/s %s" % (current.get("windSpd", 0) / 3.6, getDirection(current.get("windDir", "na")))
			self.WDay[ConfigWWW]["Cond"] = current.get("pvdrCap", "")
			self.WDay[ConfigWWW]["Icon"] = "%s.png" % iconmap.get(current.get("symbol", "")[:4], "NA")  # remove 'windy-flag' if present
			self.WDay[ConfigWWW]["Feel"] = "%.0f" % current.get("feels", 0)
			self.WDay[ConfigWWW]["Rain"] = "%.0f" % forecast[0].get("daily", {}).get("day", {}).get("precip", 0)
			self.WWeek[ConfigWWW] = []
			for idx in range(6):
				High = "%.0f" % forecast[idx].get("daily", {}).get("tempHi", 0)
				Low = "%.0f" % forecast[idx].get("daily", {}).get("tempLo", 0)
				date = (currdate + timedelta(days=idx)).strftime("%Y-%m-%d")
				Day = datetime(int(date[:4]), int(date[5:7]), int(date[8:])).strftime("%a")
				Icon = "%s.png" % iconmap.get(forecast[idx].get("daily", {}).get("symbol", "")[:4], "NA")  # remove 'windy-flag' if present
				Cond = forecast[idx].get("daily", {}).get("pvdrCap", "")
				Regen = "%.0f" % forecast[idx].get("daily", {}).get("day", {}).get("precip", 0)
				self.WWeek[ConfigWWW].append({"High": High, "Low": Low, "Day": Day, "Icon": Icon, "Cond": Cond, "Regen": Regen})
			L4log("MSN-weather%s: completed!" % ConfigWWW)
			self.downloadSunrise()
			PICwetter[ConfigWWW] = None
		else:
			L4log("MSN-weather%s download Error: no data found." % ConfigWWW)

	def downloadOMcallback(self, ConfigWWW, jsonData):
		iconmap = {0: "32", 1: "34", 2: "30", 3: "28", 45: "20", 48: "21", 51: "9", 53: "9", 55: "9", 56: "8",
					57: "10", 61: "9", 63: "11", 65: "12", 66: "8", 67: "7", 71: "42", 73: "14", 75: "41",
					77: "35", 80: "9", 81: "11", 82: "12", 85: "42", 86: "43", 95: "38", 96: "4", 99: "4"
					}  # mapping: om -> yahoo+
		global wwwWetter
		self.WetterOK = False
		wwwWetter[ConfigWWW] = ""
		L4log("OM-weather%s: download OK" % ConfigWWW)
		r = {}
		try:
			r = loads(jsonData)
		except Exception as err:
			L4log("OM-weather%s: json-download Error: %s" % (ConfigWWW, str(err)))
			return
		L4log("OM-weather%s data ready" % ConfigWWW)
		L4logE("OM-weather%s data: %s" % (ConfigWWW, r))
		zerolist = [0] * 24
		nalist = ["na"] * 24

		if r.get("hourly", None) is not None and r.get("daily", None) is not None:
			L4log("OM-weather%s: analysing current & forecasts..." % ConfigWWW)
			self.WetterOK = True
			wwwWetter[ConfigWWW] = r
			isotime = datetime.now().strftime("%FT%H:00")
			self.WDay[ConfigWWW] = {}
			self.WDay[ConfigWWW]["Locname"] = LCD4linux.WetterCity.value if ConfigWWW == 0 else LCD4linux.Wetter2City.value
			current = r.get("hourly", {})
			for idx, time in enumerate(current.get("time", [])):  # collect current
				if isotime in time:
					self.WDay[ConfigWWW]["Temp_c"] = "%.0f" % current.get("temperature_2m", zerolist)[idx]
					self.WDay[ConfigWWW]["Hum"] = "%.0f%%" % current.get("relativehumidity_2m", zerolist)[idx]
					if LCD4linux.WetterWind.value == "0":
						self.WDay[ConfigWWW]["Wind"] = "%.0f km/h %s" % (current.get("windspeed_10m", zerolist)[idx], getDirection(current.get("winddirection_10m", nalist)[idx]))
					else:
						self.WDay[ConfigWWW]["Wind"] = "%.1f m/s %s" % (current.get("windspeed_10m", zerolist)[idx] / 3.6, getDirection(current.get("winddirection_10m", nalist)[idx]))
					self.WDay[ConfigWWW]["Icon"] = "%s.png" % iconmap.get(current.get("weathercode", nalist)[idx], "na")
					self.WDay[ConfigWWW]["Feel"] = "%.0f" % current.get("apparent_temperature", zerolist)[idx]
					self.WDay[ConfigWWW]["Rain"] = "%.0f" % current.get("precipitation_probability", zerolist)[idx]
					self.WDay[ConfigWWW]["Wtime"] = datetime.now().strftime("%H:%M")
					break
			forecast = r["daily"]
			self.WWeek[ConfigWWW] = []
			for idx in range(6):  # collect forecast of today and next 5 days
				High = "%.0f" % forecast.get("temperature_2m_min", zerolist)[idx]
				Low = "%.0f" % forecast.get("temperature_2m_max", zerolist)[idx]
				Day = Code_utf8(WeekDays[strptime(forecast.get("time", zerolist)[idx], "%Y-%m-%d").tm_wday])
				Icon = "%s.png" % iconmap.get(forecast.get("weathercode", zerolist)[idx], "NA")
				Cond = ""
				Regen = "%.0f" % forecast.get("precipitation_probability_max", zerolist)[idx]
				self.WWeek[ConfigWWW].append({"High": High, "Low": Low, "Day": Day, "Icon": Icon, "Cond": Cond, "Regen": Regen})
			L4log("OM-weather%s: completed!" % ConfigWWW)
			self.downloadSunrise()
			PICwetter[ConfigWWW] = None
		else:
			L4log("OM-weather%s download Error: no data found." % ConfigWWW)

	def downloadOWMcallback(self, ConfigWWW, jsonData):
		iconmap = {200: "37", 201: "4", 202: "3", 210: "37", 211: "4", 212: "3", 221: "3", 230: "37", 231: "38", 232: "38",
					300: "9", 301: "9", 302: "9", 310: "9", 311: "9", 312: "9", 313: "11", 314: "12", 321: "11", 500: "9",
					501: "11", 502: "11", 503: "12", 504: "12", 511: "10", 520: "11", 521: "11", 522: "12", 531: "40",
					600: "42", 601: "16", 602: "15", 611: "18", 612: "10", 613: "17", 615: "6", 616: "5", 620: "14",
					621: "42", 622: "13", 701: "20", 711: "22", 721: "21", 731: "19", 741: "20", 751: "19", 761: "19",
					762: "22", 771: "23", 781: "0", 800: "32", 801: "34", 802: "30", 803: "26", 804: "28"
					}  # mapping: owm -> yahoo+
		global wwwWetter
		self.WetterOK = False
		wwwWetter[ConfigWWW] = ""
		L4log("OWM-weather%s: download OK" % ConfigWWW)
		r = {}
		try:
			r = loads(jsonData)
		except Exception as err:
			L4log("OWM-weather%s: json-download Error: %s" % (ConfigWWW, str(err)))
			return
		L4log("OMW-weather%s data ready" % ConfigWWW)
		L4logE("OMW-weather%s data: %s" % (ConfigWWW, r))

		if r.get("name", None) is not None:
			L4log("OWM-weather%s: analysing coordinates & current..." % ConfigWWW)
			cityname = LCD4linux.WetterCity.value if ConfigWWW == 0 else LCD4linux.Wetter2City.value
			self.saveGeodata(ConfigWWW, cityname, r.get("coord", {}).get("lon", 0), r.get("coord", {}).get("lat", 0))
			self.WDay[ConfigWWW] = {}
			self.WDay[ConfigWWW]["Locname"] = cityname
			self.WDay[ConfigWWW]["Temp_c"] = "%.0f" % r.get("main", {}).get("temp", 0)
			self.WDay[ConfigWWW]["Hum"] = "%.0f%%" % r.get("main", {}).get("humidity", 0)
			if LCD4linux.WetterWind.value == "0":
				self.WDay[ConfigWWW]["Wind"] = "%.0f km/h %s" % (r.get("wind", {}).get("speed", 0) * 3.6, getDirection(r.get("wind", {}).get("deg", 0)))
			else:
				self.WDay[ConfigWWW]["Wind"] = "%.1f m/s %s" % (r.get("wind", {}).get("speed", 0), getDirection(r.get("wind", {}).get("deg", 0)))
			self.WDay[ConfigWWW]["Cond"] = r.get("weather", [{}])[0].get("description", "")
			self.WDay[ConfigWWW]["Icon"] = "%s.png" % iconmap.get(r.get("weather", [{}])[0].get("id", {}), "NA")
			self.WDay[ConfigWWW]["Feel"] = "%.0f" % r.get("main", {}).get("feels_like", 0)
			self.WDay[ConfigWWW]["Rain"] = "%.0f" % (r.get("pop", 0) * 100)
			self.WDay[ConfigWWW]["Wtime"] = strftime("%H:%M"), localtime(r.get("dt", time()))
			PICwetter[ConfigWWW] = None
		elif r.get("daily", None) is not None:
			self.WetterOK = True
			L4log("OWM-weather%s: analysing forecasts..." % ConfigWWW)
			wwwWetter[ConfigWWW] = r
			self.WWeek[ConfigWWW] = []
			for current in r.get("daily", []):
				High = "%.0f" % current.get("temp", {}).get("max", 0)
				Low = "%.0f" % current.get("temp", {}).get("min", 0)
				Day = Code_utf8(WeekDays[localtime(current.get("dt", time())).tm_wday])
				Icon = "%s.png" % iconmap.get(current.get("weather", [{}])[0].get("id", "NA"), "NA")
				Cond = current.get("weather", [{}])[0].get("description", "")
				Regen = "%.0f" % (current.get("pop", 0) * 100)
				self.WWeek[ConfigWWW].append({"High": High, "Low": Low, "Day": Day, "Icon": Icon, "Cond": Cond, "Regen": Regen})
			PICwetter[ConfigWWW] = None
			L4log("OWM-weather%s: completed!" % ConfigWWW)
			self.downloadSunrise()
		else:
			L4log("OWM-weather%s download Error: no data found." % ConfigWWW)

	def downloadWUcallback(self, ConfigWWW, jsonData):
		iconmap = {0: "32", 1: "34", 2: "30", 3: "28", 10: "21", 21: "40", 22: "42", 23: "18",
					24: "8", 29: "38", 38: "15", 39: "41", 45: "20", 49: "20", 50: "9", 51: "9",
					56: "8", 57: "8", 60: "40", 61: "11", 62: "40", 63: "12", 64: "40", 65: "12",
					66: "10", 67: "10", 68: "6", 69: "18", 70: "14", 71: "14", 72: "16", 73: "16",
					74: "41", 75: "41", 79: "17", 80: "11", 81: "12", 82: "12", 83: "18", 84: "18",
					85: "14", 86: "16", 87: "7", 88: "18", 91: "37", 92: "38", 93: "16", 94: "41"
					}  # mapping: wu -> yahoo+
		global wwwWetter
		self.WetterOK = False
		wwwWetter[ConfigWWW] = ""
		r = {}
		try:
			r = loads(jsonData)
		except Exception:
			L4log("WU-weather%s: json-download Error" % ConfigWWW)
			return
		L4log("WU-weather%s data ready" % ConfigWWW)
		L4logE("WU-weather%s data: %s" % (ConfigWWW, r))
		if r.get("lat", None) is not None:
			self.WetterOK = True
			L4log("WU-weather%s: analysing coordinates & current..." % ConfigWWW)
			cityname = LCD4linux.WetterCity.value if ConfigWWW == 0 else LCD4linux.Wetter2City.value
			self.saveGeodata(ConfigWWW, cityname, r.get("lon", 0), r.get("lat", 0))
			self.WDay[ConfigWWW] = {}
			self.WDay[ConfigWWW]["Locname"] = cityname
			self.WDay[ConfigWWW]["Temp_c"] = "%.0f" % r.get("temp_c", 0)
			self.WDay[ConfigWWW]["Hum"] = "%.0f%%" % r.get("humid_pct", 0)
			if LCD4linux.WetterWind.value == "0":
				self.WDay[ConfigWWW]["Wind"] = "%.0f km/h %s" % (r.get("windspd_kmh", 0), getDirection(r.get("winddir_deg", 0)))
			else:
				self.WDay[ConfigWWW]["Wind"] = "%.1f m/s %s" % (r.get("windspd_kmh", 0) / 3.6, getDirection(r.get("winddir_deg", 0)))
			self.WDay[ConfigWWW]["Icon"] = "%s.png" % iconmap.get(r.get("wx_code", {}), "NA")
			self.WDay[ConfigWWW]["Cond"] = r.get("wx_desc", "")
			self.WDay[ConfigWWW]["Feel"] = "%.0f" % r.get("feelslike_c", 0)
			rain = "%.0f" % r.get("prob_precip_pct", 0)
			self.WDay[ConfigWWW]["Rain"] = rain if rain.isdigit() else "0"  # could be: "< 1"
			self.WDay[ConfigWWW]["Wtime"] = strftime("%H:%M", localtime())
			PICwetter[ConfigWWW] = None
		elif r.get("Days", None) is not None:
			self.WetterOK = True
			L4log("WU-weather%s: analysing forecasts..." % ConfigWWW)
			wwwWetter[ConfigWWW] = r
			self.WWeek[ConfigWWW] = []
			for idx, curr in enumerate(r.get("Days", [])):
				if idx > 5:  # some keys are missing in day 6
					break
				High = "%.0f" % curr.get("temp_max_c", 0)
				Low = "%.0f" % curr.get("temp_min_c", 0)
				date = curr.get("date", "").split("/")
				Day = Code_utf8(WeekDays[weekday(int(date[2]), int(date[1]), int(date[0]))])
				if "Timeframes" in curr:
					Icon = "%s.png" % iconmap.get(curr["Timeframes"][4]["wx_code"], "NA")
					Cond = Code_utf8(curr["Timeframes"][4]["wx_desc"])
					rain = str(curr["Timeframes"][4]["prob_precip_pct"])
					Regen = rain if rain.isdigit() else "0"  # could be: "< 1"
				else:
					Icon, Cond, Regen = ("", "", "")
				self.WWeek[ConfigWWW].append({"High": High, "Low": Low, "Day": Day, "Icon": Icon, "Cond": Cond, "Regen": Regen})
			L4log("WU-weather%s: completed!" % ConfigWWW)
			self.downloadSunrise()
			PICwetter[ConfigWWW] = None
		else:
			wwwWetter[ConfigWWW] = ""
			L4log("WU-weather%s download Error: no data found" % ConfigWWW)

	def downloadSunrise(self):
		L4log("Sunrise...")
		apkey = ""
		if len(LCD4linux.WetterApiKeyOpenWeatherMap.value) > 599:
			apkey = "&appid=%s" % LCD4linux.WetterApiKeyOpenWeatherMap.value
			self.feedurl = "http://api.openweathermap.org/data/2.5/weather?lat=%.2f&lon=%.2f&mode=xml&cnt=1%s" % (float(self.Lat[0].replace(",", ".")), float(self.Long[0].replace(",", ".")), apkey)
			L4log("Sunrise downloadstart:", self.feedurl)
			callInThread(getPage, self.feedurl, self.downloadSunriseCallback, self.downloadSunriseError)
		else:
			self.feedurl = ("http://api.sunrise-sunset.org/json?lat=%s&lng=%s&formatted=0" % (self.Lat[0], self.Long[0])).replace(",", ".")
			L4log("Sunrise2 downloadstart:", self.feedurl)
			callInThread(getPage, self.feedurl, self.downloadSunriseCallback2, self.downloadSunriseError)

	def downloadSunriseError(self, error=""):
		if error == "":
			L4log("Sunrise download Error ?")
		else:
			L4log("Sunrise download Error", str(error))

	def downloadSunriseCallback(self, page=""):
		global L4LSun
		global L4LMoon
		L4log("Sunrise download ok")
		try:
			page = ensure_str(page)
			dom = parseString(page)
			DIFF = getTimeDiffUTC()
			s = dom.getElementsByTagName("sun")
			if len(s) > 0:
				Rise = s[0].getAttribute("rise").split("T")
				if len(Rise) == 2:
					h = int(int(Rise[1].split(":")[0]) + DIFF)
					if h > 23:
						h -= 24
					elif h < 0:
						h += 24
					m = int(Rise[1].split(":")[1])
					if int(Rise[1].split(":")[2]) >= 30 and m < 59:
						m += 1
					if h in range(0, 24) and m in range(0, 60):
						L4LSun = (h, m)
				Rise = s[0].getAttribute("set").split("T")
				if len(Rise) == 2:
					h = int(int(Rise[1].split(":")[0]) + DIFF)
					if h > 23:
						h -= 24
					elif h < 0:
						h += 24
					m = int(Rise[1].split(":")[1])
					if int(Rise[1].split(":")[2]) >= 30 and m < 59:
						m += 1
					if h in range(0, 24) and m in range(0, 60):
						L4LMoon = (h, m)
		except Exception:
			L4log("Error Sunrise processing")
			L4log("Error:", format_exc())
		L4log(L4LSun, "%s" % L4LMoon)

	def downloadSunriseCallback2(self, page=""):
		global L4LSun
		global L4LMoon
		L4log("Sunrise2 download ok")
		try:
			page = ensure_str(page)
			DIFF = getTimeDiffUTC()
			s = loads(page)
			if len(s) > 0:
				Rise = s.get("results", {}).get("sunrise", "T06:00:00").split("T")[1].split("+")[0]
				if len(Rise) == 8:
					h = int(int(Rise.split(":")[0]) + DIFF)
					if h > 23:
						h -= 24
					elif h < 0:
						h += 24
					m = int(Rise.split(":")[1])
					if int(Rise.split(":")[2]) >= 30 and m < 59:
						m += 1
					if h in range(0, 24) and m in range(0, 60):
						L4LSun = (h, m)
				Rise = s.get("results", {}).get("sunset", "T19:00:00").split("T")[1].split("+")[0]
				if len(Rise) == 8:
					h = int(int(Rise.split(":")[0]) + DIFF)
					if h > 23:
						h -= 24
					elif h < 0:
						h += 24
					m = int(Rise.split(":")[1])
					if int(Rise.split(":")[2]) >= 30 and m < 59:
						m += 1
					if h in range(0, 24) and m in range(0, 60):
						L4LMoon = (h, m)
		except Exception:
			L4log("Error Sunrise2 processing")
			L4log("Error:", format_exc())
		L4log("%s %s" % (L4LSun, L4LMoon))

	def coverDownloadFailed(self, result):
		self.LgetGoogleCover = None
		self.CoverIm = None
		self.CoverName = ["-", "-"]
		self.CoverCount += 1
		self.Refresh = "1"
		self.restartTimer()
		L4log("cover download failed:", result)

	def coverDownloadFinished(self, filename, result):
		self.LgetGoogleCover = None
		self.CoverIm = None
		self.CoverName = ["-", "-"]
		if isfile(GoogleCover):
			self.CoverCount = 0
			self.Refresh = "1"
			self.restartTimer()
			L4log("cover download finished")
		else:
			L4log("cover download finished, no file found")

	def getGoogleCover(self, artist, isVid):
		if artist != "":
			self.LgetGoogleCover = "wait"
			self.CoverError = ""
			if LCD4linux.MPCoverType.value == "0":
				hq = "music" if isVid == False else "movie"
				try:
					url = ("https://itunes.apple.com/search?term=%s&limit=2&media=%s" % (quote(Code_utf8(Umlaute(artist)).encode("latin", "ignore")), hq)).replace("%26", "&")
					L4log("Cover Search", url)
					callInThread(getPage, url, self.appleImageCallback, self.coverDownloadFailed)
				except Exception:
					self.LgetGoogleCover = None
					L4log("Apple Cover Error")
					L4log("Error:", format_exc())
			else:
				if len(LCD4linux.MPCoverApiGoogle.value) < 10:
					self.CoverError = "Google API Key is required"
					L4log("Error:", self.CoverError)
				else:
					hq = "cd%20cover" if isVid == False else "dvd%20cover"
					try:
						url = "https://www.googleapis.com/customsearch/v1?q=%s&hq=%s&num=10&searchType=image&fileType=png,jpg&safe=medium&imgSize=large&key=%s&cx=001378528959810143413:qx3tznt9mfa" % (quote(Code_utf8(artist).encode("latin", "ignore")), hq, LCD4linux.MPCoverApiGoogle.value)
						L4log("Cover Search", url)
						callInThread(getPage, url, self.googleImageCallback, self.coverDownloadFailed)
					except Exception:
						self.LgetGoogleCover = None
						L4log("Google Cover Error")
						L4log("Error:", format_exc())
		else:
			self.LgetGoogleCover = None

	def appleImageCallback(self, result):
		filename = GoogleCover
		url = ""
		r = {}
		try:
			r = loads(result.decode("utf-8", "ignore"))
		except Exception:
			L4log("Apple JSON Error")
		count = 0
		rc = int(r.get("resultCount", 0))
		if rc != 0:
			for u in r["results"]:
				L4log("Cover", u)
				count += 1
				if url == "":
					url = u.get("artworkUrl100", "").replace("100x100", "400x400")
			if url == "":
				self.LgetGoogleCover = None
				L4log("no downloads found")
				self.CoverCount += 1
				self.restartTimer()
			else:
				L4log("downloading %d. cover from" % count, url)
				callInThread(downloadPage, url, filename, boundFunction(self.coverDownloadFinished, filename), self.coverDownloadFailed)
		else:
			self.LgetGoogleCover = None
			self.CoverError = "E"
			self.CoverCount += 1

	def googleImageCallback(self, result):
		filename = GoogleCover
		url = ""
		r = {}
		try:
			r = loads(result.decode("utf-8", "ignore"))
		except Exception:
			L4log("Google JSON Error")
		count = 0
		error = r.get("error", {}).get("message", "")
		if error == "":
			for u in r["items"]:
				L4log("Cover", u)
				count += 1
				if url == "":
					url = u.get("link", "")
				w = int(u.get("image", {}).get("width", "0"))
				h = int(u.get("image", {}).get("height", "0"))
				org = u.get("image", {}).get("contextLink", "")
				if (abs(h - w) < (w / 10) or h >= w) and h > 140 and w > 140 and "Karaoke" not in u.get("title", "") and "play.google" not in org and ".ebay." not in org:
					url = u.get("link", "")
					break
			if url == "":
				self.LgetGoogleCover = None
				L4log("no downloads found")
				self.CoverCount += 1
				self.restartTimer()
			else:
				L4log("downloading %d. cover from" % count, url)
				callInThread(downloadPage, url, filename, boundFunction(self.coverDownloadFinished, filename), self.coverDownloadFailed)
		else:
			self.LgetGoogleCover = None
			self.CoverError = error

	def SonosDownloadFailed(self, result):
		L4log("Sonos/YMC/Blue download failed:", result)

	def SonosDownloadFinished(self, filename, result):
		if isfile(filename):
			self.restartTimer()
			L4log("Sonos/YMC/Blue download finished")
		else:
			L4log("Sonos/YMC/Blue download finished, no file found")

	def getSonosPic(self, fn, url):
		filename = fn
		L4log("downloading Sonos/YMC/Blue from", url)
		callInThread(downloadPage, url, filename, boundFunction(self.SonosDownloadFinished, self.SonosDownloadFailed))


def LCD4linuxPICThread(self, session):
	global ThreadRunning
	ThreadRunning = 1
	try:
		LCD4linuxPIC(self, session)
	except Exception:
		L4log("Thread Error:", format_exc())
		try:
			open(CrashFile, "w").write(format_exc())
		except Exception:
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
		actbouquet = None if Servicelist is None else Servicelist.getRoot()
		serviceHandler = eServiceCenter.getInstance()
		for name, bouquet in bouquets:
			if not bouquet.valid():  # check end of list
				break
			if bouquet.flags & eServiceReference.isDirectory:
				servicelist = serviceHandler.list(bouquet)
				if servicelist is not None:
					while True:
						service = servicelist.getNext()
						if not service.valid():  # check end of list
							break
						playable = not (service.flags & mask)
						if playable:
							number += 1
#						L4logE(" ",service.getPath())
						if actbouquet:
							if actbouquet == bouquet and actservice == service:
								return number
						else:
							if actservice == service:
								return number
	L4logE("no Channel - Count:", "%s" % number)
	return None


def getServiceInfo(self, NowNext):
	event_begin = 0
	event_end = 0
	duration = 0
	event_name = ""
	if event_name == "" and str(LCD4linux.ServiceSearch.value) == "0":
		service = self.session.nav.getCurrentService()
		if service is not None:
			info = service and service.info()
			event = info and info.getEvent(NowNext)
			if event:
				event_name = event.getEventName()
				event_begin = event.getBeginTime()
				duration = event.getDuration()
				event_end = event_begin + duration
	if event_name == "":
		epgcache = eEPGCache.getInstance()
		if epgcache is not None:
			sref = self.session.nav.getCurrentlyPlayingServiceReference()
			if sref is not None:
				event = epgcache.lookupEvent(['IBDCTSERNX', (sref.toString(), NowNext, -1)])
				event_begin = 0
				if event:
					L4logE("Service EPG")
					if event[0][4]:
						t = event[0][1]
						duration = event[0][2]
						event_name = event[0][4]
						event_begin = t
						event_end = event_begin + duration
	if event_name == "" and str(LCD4linux.ServiceSearch.value) == "1":
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


def getSplit(ConfigSplit, ConfigAlign, MAX_W, w):
	MAX_W = int(MAX_W)
	if int(ConfigAlign) > 9 and len(str(ConfigAlign)) < 4:
		POSX = int(ConfigAlign)
	else:
		POSX = int((MAX_W - w) / 2)
		if ConfigSplit == False:
			if w > MAX_W or ConfigAlign in ["0", "3"]:
				POSX = 0
			elif ConfigAlign in ["2", "4"]:
				POSX = (MAX_W - w)
			elif len(str(ConfigAlign)) == 4:
				POSX = int(MAX_W * int(ConfigAlign) / 10000)
		else:
			if ConfigAlign == "1":
				POSX = POSX + int(MAX_W / 2)
			elif ConfigAlign == "2":
				POSX = MAX_W + POSX
			elif ConfigAlign == "3":
				POSX = 0
			elif ConfigAlign == "4":
				POSX = int(MAX_W / 2)
			elif len(str(ConfigAlign)) == 4:
				POSX = int(MAX_W * int(ConfigAlign) / 10000)
	return POSX


def getFont(num):
	ff = [FONT, LCD4linux.Font1.value, LCD4linux.Font2.value, LCD4linux.Font3.value, LCD4linux.Font4.value, LCD4linux.Font5.value]
	return ff[int(num)] if ff[int(num)].endswith(".ttf") and isfile(ff[int(num)]) else FONT


def getMem():
	tot = fre = buf = cac = 0
	if isfile("/proc/meminfo"):
		try:
			with open("/proc/meminfo", "r") as f:
				tot = int(f.readline().split()[1]) * 1024
				fre = int(f.readline().split()[1]) * 1024
				line = f.readline()
				buf = int(line.split()[1]) * 1024
				if line.split()[0] == "MemAvailable:":
					buf = buf - fre
				else:
					cac = int(f.readline().split()[1]) * 1024
		except Exception:
			pass
	return tot, fre, buf + cac


class myE2Timer(object):
	def __init__(self):
		self.name = ""
		self.begin = 0
		self.end = 0
		self.disabled = 0
		self.justplay = 0
		self.ice_timer_id = None
		self.service_ref = ""
		self.state = 0

	def values(self):
		return self.name, self.begin, self.end, self.disabled, self.justplay, self.ice_timer_id, self.service_ref, self.state


def url_parse(url, defaultPort=None):
	parsed = urlparse(url)
	scheme = parsed[0]
	path = urlunparse(('', '') + parsed[2:])
	if defaultPort is None:
		if scheme == 'https':
			defaultPort = 443
		else:
			defaultPort = 80
	host, port = parsed[1], defaultPort
	if ':' in host:
		host, port = host.split(':')
		port = int(port)
	return scheme, host, port, path


def getShowPicture(BildFile, idx):
	global OSDon
	global Bilder
	global BilderIndex
	global BilderTime
	ShowPicture = ""
	L4logE("Picturefile", BildFile)
	if "://" in BildFile:
		try:
			if "@" in BildFile:
				setdefaulttimeout(30)
				r = urlretrieve(BildFile, HTTPpictmp % idx)
				L4logE("Content-Type", r[1]["content-type"])
				if r[1]["content-type"].find("image/") >= 0:
					if isfile(HTTPpictmp % idx):
						try:
							rename(HTTPpictmp % idx, HTTPpic % idx)
						except Exception:
							pass
				else:
					L4logE("Content-Type not image", BildFile)
			else:
				r = urlopen(BildFile, timeout=5)
				L4logE("Content-Type", r.info().get("content-type"))
				if r.info().get("content-type").find("image/") >= 0:
					with open(HTTPpictmp % idx, 'wb') as f:
						f.write(r.read())
					if isfile(HTTPpictmp % idx):
						try:
							rename(HTTPpictmp % idx, HTTPpic % idx)
						except Exception:
							pass
				else:
					L4logE("Content-Type not image", BildFile)
				r.close()
		except Exception:
			rmFile(HTTPpic % idx)
			L4log("HTTP Error", BildFile)
		finally:
			ShowPicture = HTTPpic % idx
	else:
		if isdir(BildFile):
			if len(Bilder[idx]) > 0:
				ShowPicture = Bilder[idx][BilderIndex[idx]]
				L4log("current Picture " + ShowPicture, BilderIndex[idx])
				if BilderTime == 1:
					BilderIndex[idx] += 1
					if BilderIndex[idx] >= len(Bilder[idx]):
						BilderIndex[idx] = 0
		else:
			ShowPicture = BildFile
			if not isfile(ShowPicture):
				BildFile = join(dirname(ShowPicture), "default.png")
				if isfile(BildFile):
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
	days = diff.days + diff.seconds / 86400
	lunations = 0.20439731 + days * 0.03386319269
	return lunations % float(1)


def MoonPhase(pos):
	index = (pos * float(8)) + float("0.5")
	index = floor(index)
	return {
		0: _("New Moon"),
		1: _("First Quarter"),
		2: _("Waxing Crescent"),
		3: _("Waxing Moon"),
		4: _("Full Moon"),
		5: _("Waning Moon"),
		6: _("Waning Crescent"),
		7: _("Last Quarter")
		}[int(index) & 7]


"""
series expansion of the moon orbital elements from Chapront und Chapront-Touzé
Quelle: htps://de.wikipedia.org/wiki/Mondbahn
http://articles.adsabs.harvard.edu/full/1994A%26A...282..663S
"""


def MoonDistance(now=None):
	if now is None:
		now = datetime.now()
	diff = now - datetime(2000, 1, 1, 12, 0, 0)
	t = diff.days + diff.seconds / 86400
	GM = (134.96341138 + 13.064992953630 * t) * pi / 180
	DD = (297.85020420 + 12.190749117502 * t) * pi / 90
	return 385000.5584 - 20905.3550 * cos(GM) - 3699.1109 * cos(DD - GM) - 2955.9676 * cos(DD) - 569.9251 * cos(2 * GM)


def LCD4linuxPIC(self, session):
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
	global INFO

	def ShadowText(draw, tx, ty, TXT, font, tCol, SHADOW):
		if SHADOW == True:
			w, h = getFsize(TXT, font)
			D = round(h / 20.)
			if D == 0:
				D = 1
			elif D > 3:
				D = 3
			if PY3:  # for equal results, .draw_bitmap() needs an y-offset under Python 3
				ty += round(h / 7.)  # only estimated & tested value
			tx1 = tx + D
			tx0 = tx - D
			ty1 = ty + D
			ty0 = ty - D
			if tCol[0] == '#':
				COL = tCol
			else:
				COL = ImageColor.colormap[tCol]
			if isinstance(COL, tuple):
				RGB = COL
			else:
				if (COL[0] == '#'):
					COL = COL[1:]
				RGB = (int(COL[:2], 16), int(COL[2:4], 16), int(COL[4:6], 16))
			ColO = self.draw[draw].draw.draw_ink(RGB)
			HLS = list(rgb_to_hls(RGB[0] / 255., RGB[1] / 255., RGB[2] / 255.))
			if HLS[1] < 0.5:
				HLS[1] += 0.5
			else:
				HLS[1] -= 0.5
				if HLS[1] < 0.1:
					HLS[1] = 0.1
			RGB = tuple(map(lambda x: int(x * 255), hls_to_rgb(HLS[0], HLS[1], HLS[2])))
			Col = self.draw[draw].draw.draw_ink(RGB)
			mask = font.getmask(TXT + "  ", "1")
			self.draw[draw].draw.draw_bitmap((tx0, ty0), mask, Col)
			self.draw[draw].draw.draw_bitmap((tx1, ty1), mask, Col)
			self.draw[draw].draw.draw_bitmap((tx0, ty1), mask, Col)
			self.draw[draw].draw.draw_bitmap((tx1, ty0), mask, Col)
			self.draw[draw].draw.draw_bitmap((tx, ty), mask, ColO)
		else:
			self.draw[draw].text((tx, ty), Code_utf8(TXT), font=font, fill=tCol)

	def writeMultiline(sts, ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, draw, im, utf=True, ConfigBackColor="0", ConfigFont=FONT, Shadow=False, Width=0, PosX=-1):
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		if utf == True:
			astr = Code_utf8(sts)
		else:
			astr = sts
		if astr.find(" ") > 25 or (astr.find(" ") == -1 and len(astr) > 25):
			astr = astr.replace(".", " ").replace(",", ", ")
		lines = astr.split("\n")
		if Width == 0:
			W = MAX_W
		else:
			W = Width
		W = int(W * 2 / ConfigSize)
		if W < 1:
			L4log("Multiline Error", "%s" % W)
			W = 100
		lists = (TextWrapper(width=W, break_long_words=False).wrap(line) for line in lines)
		body = "\n".join("\n".join(list) for list in lists)
		para = body.split('\n')
		current_h = ConfigPos
		while len(para) > int(ConfigLines):
			del para[len(para) - 1]
		for line in para:
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			w, h = getFsize(line, font)
			TextSize = ConfigSize
			while w > MAX_W:
				font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
				TextSize -= 1
				w, h = getFsize(line, font)
			if PosX == -1:
				POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
			else:
				POSX = PosX
			if ConfigBackColor != "0":
				self.draw[draw].rectangle((POSX, current_h, POSX + w, current_h + h), fill=ConfigBackColor)
			ShadowText(draw, POSX, current_h, line, font, ConfigColor, Shadow)
			current_h += h

	def writeMultiline2(sts, ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigX, MAX_W, draw, im, ConfigFont=FONT, Shadow=False):
		para = sts.split("\n")
		current_h = ConfigPos
		while len(para) > int(ConfigLines):
			del para[len(para) - 1]
		for line in para:
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			line = Code_utf8(line)
			w, h = getFsize(line, font)
			TextSize = ConfigSize
			while w > MAX_W:
				TextSize -= 1
				font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
				w, h = getFsize(line, font)
			POSX = getSplit(False, "1", MAX_W, w)
			ShadowText(draw, POSX + ConfigX, current_h, line, font, ConfigColor, Shadow)
			current_h += h

	def cutText(tt, draw, font, max):
		w, h = getFsize(tt, font)
		while w > max:
			tt = tt[:-1]
			w, h = getFsize(tt, font)
		return tt

	def getProgess(W, P):
		return int(W * int(P) / 100)

	def getShowCover(BildFile):
		cover = ""
		MP3title = ""
		MP3artist = ""
		MP3album = ""
		if self.SonosRunning and self.SonosTrack.get("album_art", "") != "":
			if self.oldTitle != self.LsTagTitle:
				rmFile(GoogleCover)
				self.oldTitle = self.LsTagTitle
				url = self.SonosTrack.get("album_art", "")
				if url != "":
					self.getSonosPic(GoogleCover, str(url))
			cover = GoogleCover
		elif self.BlueRunning and self.BlueImage != "":
			if self.oldTitle != self.LsTagTitle:
				rmFile(GoogleCover)
				self.oldTitle = self.LsTagTitle
				url = self.BlueImage
				if url != "":
					self.getSonosPic(GoogleCover, str(url))
			cover = GoogleCover
		elif self.YMCastRunning and self.YMCastInfo.get("albumart_url", "") != "" and (LCD4linux.YMCastCover.value == "0" or self.LsTagTitle == "MusicCast"):
			cover = GoogleCover
		elif self.LsreftoString is not None and self.LgetName is not None:
			Title = self.LgetName
			if len(splitext(Title)[1]) == 4:
				Title = splitext(Title)[0]
			Title = Title.replace("/", "_").replace("&", " ").replace("+", "_").replace(":", "_").replace("?", "_").replace("*", "_").replace('\xc2\x86', '').replace('\xc2\x87', '').strip()
			L4logE("Title", Title)
			sreffile = self.LsrefFile
			sreffile2 = splitext(sreffile)[0]
			srefdir = dirname(sreffile)
			audio = None
			if sreffile.lower().endswith(".mp3") or sreffile.lower().endswith(".flac"):
				if not isfile(MP3tmp):
					if sreffile.lower().endswith(".mp3"):
						try:
							audio = ID3(sreffile)
						except Exception:
							audio = None
						if audio:
							apicframes = audio.getall("APIC")
							if len(apicframes) >= 1:
								with open(MP3tmp, 'wb') as coverArtFile:
									coverArtFile.write(apicframes[0].data)
								L4logE("MP3-Inline-Cover")
						try:
							audio = MP3(sreffile, ID3=EasyID3)
						except Exception:
							audio = None
						if audio:
							MP3title = audio.get('title', [''])[0]
							MP3artist = audio.get('artist', [''])[0]
							MP3album = audio.get('album', [''])[0]
					if sreffile.lower().endswith(".flac"):
						try:
							audio = FLAC(sreffile)
						except Exception:
							audio = None
						if audio:
							apicframes = audio.pictures
							if len(apicframes) >= 1:
								with open(MP3tmp, 'wb') as coverArtFile:
									coverArtFile.write(apicframes[0].data)
				if isfile(MP3tmp):
					cover = MP3tmp
				else:
					Album = self.LsTagAlbum
					if Album is not None and Album != "":
						tmp = glob(join(srefdir, "%s.[jp][pn]g" % Album))
						if len(tmp) > 0:
							cover = tmp[0]
						else:
							tmp = glob(join(srefdir, "[Cc]over.[jp][pn]g")) + glob(join(srefdir, "[Ff]older.[jp][pn]g"))
							if len(tmp) > 0:
								cover = tmp[0]
							else:
								tmp = glob(join(dirname(srefdir), "[Cc]over.[jp][pn]g")) + glob(join(dirname(srefdir), "[Ff]older.[jp][pn]g"))
								if len(tmp) > 0:
									cover = tmp[0]
								else:
									tmp = glob(join(srefdir, "[Ff]ront.[jp][pn]g"))
									if len(tmp) > 0:
										cover = tmp[0]
			elif cover == "" and isdir(srefdir):
				try:
					tmp = glob(join(srefdir, Title + ".[jp][pn]g")) + glob(join(srefdir, "cover", Title + ".[jp][pn]g")) + glob(join(srefdir, sreffile2 + ".[jp][pn]g")) + glob(join(srefdir, "[Cc]over.[jp][pn]g")) + glob(join(srefdir, "[Ff]older.[jp][pn]g"))
					if len(tmp) > 0:
						cover = tmp[0]
					else:
						tmp = glob(join(BildFile[0], Title + ".[jp][pn]g")) + glob(join(BildFile[1], Title + ".[jp][pn]g")) + glob(join(dirname(srefdir), "[Cc]over.[jp][pn]g")) + glob(join(dirname(srefdir), "[Ff]older.[jp][pn]g"))
						if len(tmp) > 0:
							cover = tmp[0]
						else:
							tmp = glob(join(srefdir, sreffile + ".[jp][pn]g")) + glob(join(srefdir, srefdir.split("/")[-1] + ".[jp][pn]g"))
							if len(tmp) > 0:
								cover = tmp[0]
				except Exception:
					L4log("Title Error", Title)
			if cover == "" and isfile("/tmp/.cover"):
				cover = "/tmp/.cover"
			for coverfile in LCD4linux.MPCoverFile2.value.split(","):
				covername = coverfile.split(".")[0].strip()
				selection = coverfile.split(".")[1].strip() if coverfile.find(".") != -1 else "*"
				if selection == "*":
					selection = "jpg,png"
				selection = selection.split(",")
				for extension in selection:
					datei = "%s.%s" % (covername, extension)
					if cover == "" and isfile(datei):
						cover = datei
						break
			if cover == "" and LCD4linux.MPCoverPiconFirst.value == True:
				if WebRadioFSok == True and isfile(self.l4l_info.get("Logo", "")):
					cover = self.l4l_info.get("Logo", "")
				L4log("cover", cover)
				L4log("isMediaPlayer", isMediaPlayer)
				if isMediaPlayer == "record":
					datei = "%s.meta" % sreffile
					if isfile(datei):
						try:
							ref = open(datei, "r").readline().strip()
							rr = str(ref).split("::")[0]
							if rr[-1] != ":":
								rr += ":"
							picon = "%s.png" % rr.replace(":", "_")[:-1]
							L4logE("Picon", picon)
							cover = join(LCD4linux.PiconPath.value, picon)
						except Exception:
							pass
				else:
					# Picon
					rr = str(self.LsreftoString)
					if rr.find("::") > 1:
						rr = rr.split("::")[0] + ":"
					rr = ':'.join(rr.split(':')[:11])
					pos = rr.rfind(':')
					if pos != -1:
						rr = rr[:pos]
					picon = "%s.png" % rr.rstrip(":").replace(":", "_")
					P2 = LCD4linux.PiconPath.value
					P2A = LCD4linux.PiconPathAlt.value
					PIC = []
					PIC.append(join(P2, picon))
					if not PY3:
						name2 = "%s.png" % self.Lchannel_name.decode("utf-8").encode("latin-1", "ignore")
						name4 = "%s.png" % self.Lchannel_name.decode("utf-8").encode("utf-8", "ignore")
						name3 = "%s.png" % self.Lchannel_name2.replace('\xc2\x87', '').replace('\xc2\x86', '').decode("utf-8").encode("utf-8")
						name = normalize('NFKD', unicode(str("" + self.Lchannel_name), 'utf-8', errors='ignore')).encode('ASCII', 'ignore')
					else:
						name2 = "%s.png" % self.Lchannel_name
						name4 = "%s.png" % self.Lchannel_name
						name3 = "%s.png" % self.Lchannel_name2.replace('\x87', '').replace('\x86', '')
						name = normalize('NFKD', str("" + self.Lchannel_name))
					name = "%s.png" % sub(r'[^a-z0-9]', '', str(name).replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
					PIC.append(join(P2, name3))
					PIC.append(join(P2, name2))
					PIC.append(join(P2, name))
					PIC.append(join(P2, name4))
					fields = picon.split("_", 3)
					if fields[0] in ("4097", "5001", "5002", "5003"):
						fields[0] = "1"
						PIC.append(join(P2, "_".join(fields)))
					if len(P2A) > 3:
						PIC.append(join(P2A, name3))
						PIC.append(join(P2A, name2))
						PIC.append(join(P2A, name))
						PIC.append(join(P2A, name4))
						fields = picon.split("_", 3)
						if fields[0] in ("4097", "5001", "5002", "5003"):
							fields[0] = "1"
							PIC.append(join(P2, "_".join(fields)))
					fields = picon.split("_", 3)
					if len(fields) > 2 and fields[2] not in ["1", "2"]:
						fields[2] = "1"
						picon = "_".join(fields)
						PIC.append(join(P2, picon))
						if len(P2A) > 3:
							PIC.append(join(P2A, picon))
					L4logE("Piconsearch", "%s" % PIC)
					for Pic in PIC:
						if isfile(Pic):
							cover = Pic
							break
			if cover == "" and isfile("/tmp/.wbrfs_pic"):
				cover = "/tmp/.wbrfs_pic"
			if cover == "" and LCD4linux.MPCoverPiconFirst.value == False:
				if WebRadioFSok == True and isfile(self.l4l_info.get("Logo", "")):
					cover = self.l4l_info.get("Logo", "")
			if self.LsTagTitle is not None:
				Title = "%s " % self.LsTagArtist if self.LsTagArtist is not None and self.LsTagAlbum is not None and self.LsTagArtist != "" and self.LsTagAlbum != "" else ""
				Title += self.LsTagTitle
			Video = Title.endswith(".mpg") or Title.endswith(".vob") or Title.endswith(".avi") or Title.endswith(".divx") or Title.endswith(".mv4") or Title.endswith(".mkv") or Title.endswith(".mp4") or Title.endswith(".ts")
			isVid = sreffile.endswith(".mpg") or sreffile.endswith(".vob") or sreffile.endswith(".avi") or sreffile.endswith(".divx") or sreffile.endswith(".mv4") or sreffile.endswith(".mkv") or sreffile.endswith(".mp4") or sreffile.endswith(".ts")
			if Title == "" or Video == True:
				Title = self.LgetName
				Title = Title.replace(".mpg", "").replace(".vob", "").replace(".avi", "").replace(".divx", "").replace(".mv4", "").replace(".mkv", "").replace(".mp4", "").replace(".ts", "")
			if cover == "" and isfile(GoogleCover):
				cover = GoogleCover
			if ((cover == "" or (cover == GoogleCover and self.oldTitle != Title)) and str(LCD4linux.MPCoverDownload.value) != "0") or self.CoverCount > 0:
				rmFile(GoogleCover)
				self.oldTitle = Title
				a1 = Title.find("(")
				a2 = Title.rfind(")") + 1
				if a1 > 10 and (a2 > a1 or a2 == 0):
					if len(Title) > 50 or a2 == 0:
						Title = Title[:a1]
					else:
						Title = Title.replace(Title[a1:a2], " ")
				if Title.find("LC") > 10:
					Title = Title[:Title.find("LC")]
				if len(MP3title + MP3artist + MP3album) > 10:
					Title = " "
					if self.CoverCount > 0:
						MP3album = " "
				if (self.NetworkConnectionAvailable or self.NetworkConnectionAvailable is None) and ConfigMode == False:
					Title = Title.replace(".", " ").replace("-", " ").replace("_", " ")
					Tt = "%s %s %s %s" % (Title, MP3artist, MP3album, MP3title)
					Tt = Tt.strip()
					Ignore = False
					if self.CoverCount > 0:
						Ts = Tt.split(" ")
						if len(Ts) > self.CoverCount:
							Tt = " ".join(Ts[:-self.CoverCount])
						else:
							self.CoverCount = 0
							self.LgetGoogleCover = None
							Ignore = True
					if self.LgetGoogleCover != "wait":
						if not Ignore:
							self.LgetGoogleCover = [Tt, isVid]
					else:
						L4logE("Cover wait")
			L4log("Cover", cover)
			if self.LgetGoogleCover is not None:
				L4log("Google", "%s" % self.LgetGoogleCover)
			if (cover == "" or not isfile(cover)) and isfile(LCD4linux.MPCoverFile.value):
				cover = LCD4linux.MPCoverFile.value
		return cover

# Wetter
	def putWetter(workaround, draw, im):
		(ConfigPos, ConfigZoom, ConfigAlign, ConfigSplit, ConfigType, ConfigColor, ConfigShadow, ConfigWWW, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigZoom = int(ConfigZoom)
		global WetterType
		global WetterZoom
		global OldTemp_c
		global OldFeel
		global OldHum
		global OldWind
		MAX_W, MAX_H = 0, 0
		MAX_Wi, MAX_Hi = self.im[im].size
		if ConfigSplit == True:
			MAX_Wi = int(MAX_Wi / 2)
		Wim = 5 + int(ConfigWWW)
		if PICwetter[ConfigWWW] is None or ConfigType != WetterType or ConfigZoom != WetterZoom:
			PICwetter[ConfigWWW] = "wait"
			UseWetterPath = WetterPath
			if len(LCD4linux.WetterPath.value) > 2 and isfile(join(LCD4linux.WetterPath.value, "0.png")):
				UseWetterPath = LCD4linux.WetterPath.value
			WetterType[ConfigWWW] = ConfigType
			WetterZoom[ConfigWWW] = ConfigZoom
			POSX, POSY = 1, 0
			Wmulti = ConfigZoom / 10.0
			largesize = ConfigType[0] != "3"
			trendarrows = LCD4linux.WetterTrendArrows.value
			MAX_Wr = 0 if trendarrows else int(12 * Wmulti)  # reduce width of current weather frame when trendarrows are missing
			if ConfigType.startswith("2"):
				MAX_H = int(175 * Wmulti)
			elif ConfigType.startswith("4"):
				MAX_H = int(25 * Wmulti)
			elif ConfigType == "5":
				MAX_H = int(54 * 6 * Wmulti)
			elif ConfigType == "51":
				MAX_H = int(54 * 7 * Wmulti)
			else:
				MAX_H = int(80 * Wmulti)
			MAX_H += 2
			if ConfigType == "1":
				MAX_W = int(54 * 4 * Wmulti) + int(50 * 2 * Wmulti) - MAX_Wr
				MAX_Wc = MAX_W
			elif ConfigType == "11":
				MAX_W = int(54 * 5 * Wmulti) + int(50 * 2 * Wmulti) - MAX_Wr
				MAX_Wc = MAX_W
			elif ConfigType == "12":
				MAX_W = int(54 * 2 * Wmulti) + int(50 * 2 * Wmulti) - MAX_Wr
				MAX_Wc = MAX_W
			elif ConfigType == "2":
				MAX_W = int(55 * 4 * Wmulti)
				MAX_Wc = int(50 * 2 * Wmulti) - MAX_Wr
			elif ConfigType == "21":
				MAX_W = int(55 * 5 * Wmulti)
				MAX_Wc = int(50 * 2 * Wmulti) - MAX_Wr
			elif ConfigType == "22":
				MAX_W = int(554 * 2 * Wmulti)
				MAX_Wc = int(50 * 2 * Wmulti) - MAX_Wr
			elif ConfigType == "3":
				MAX_W = int(48 * 2 * Wmulti) - MAX_Wr
				MAX_Wc = MAX_W
			elif ConfigType.startswith("4"):
				MAX_W = int(55 * Wmulti)
				MAX_Wc = MAX_W
			elif ConfigType.startswith("5"):
				MAX_W = int(54 * 3 * Wmulti)
				MAX_Wc = MAX_W
				POSX = int(54 * 2 * Wmulti)
				POSY = int(40 * 2 * Wmulti)
			imageMode = "RGBA" if LCD4linux.WetterTransparenz.value == "true" else "RGB"
			self.im[Wim] = Image.new(imageMode, (MAX_W, MAX_H), (0, 0, 0, 0))
			if LCD4linux.WetterTransparenz.value == "crop":
				POSXs = getSplit(ConfigSplit, ConfigAlign, MAX_Wi, MAX_W)
				image_Back = self.im[im].crop((POSXs, ConfigPos, POSXs + MAX_W, ConfigPos + MAX_H))
				self.im[Wim].paste(image_Back, (0, 0))
			self.draw[Wim] = ImageDraw.Draw(self.im[Wim])
			if ConfigType != "3" and ConfigType[0] != "4":
				i = 0
				for curr in self.WWeek[ConfigWWW]:
					if (i < 4 and ConfigType in ["1", "2", "5"]) or (i < 5 and ConfigType in ["11", "21", "51"]) or (i < 2 and ConfigType in ["12", "22"]):
						i += 1
						High = curr.get("High", "0")
						Low = curr.get("Low", "0")
						Day = curr.get("Day", "")
						Icon = curr.get("Icon", "0")
						Cond = curr.get("Cond", "")
						Regen = curr.get("Regen", "0")
						if "." in Regen:
							Regen += "mm" if LCD4linux.WetterRain.value == "true2" else ""
						else:
							Regen += "%" if LCD4linux.WetterRain.value == "true2" else ""
						if ConfigType.startswith("5"):
							font = ImageFont.truetype(ConfigFont, int(14 * Wmulti), encoding='unic')
							fontD = ImageFont.truetype(ConfigFont, int(14 * Wmulti), encoding='unic')
						else:
							fontD = ImageFont.truetype(ConfigFont, int(18 * Wmulti), encoding='unic')
							if len(High) > 2 or len(Low) > 2:
								font = ImageFont.truetype(ConfigFont, int(18 * Wmulti), encoding='unic')
							else:
								font = ImageFont.truetype(ConfigFont, int(20 * Wmulti), encoding='unic')
						L4logE("Icon:", Icon)
						if isfile(join(UseWetterPath, Icon)):
							pil_image = Image.open(join(UseWetterPath, Icon))
							xx, yy = pil_image.size
							y = int(float(int(LCD4linux.WetterIconZoom.value) * Wmulti) / xx * yy)
							if LCD4linux.BilderQuality.value == "0":
								pil_image = pil_image.resize((int(int(LCD4linux.WetterIconZoom.value) * Wmulti), y))
							else:
								pil_image = pil_image.resize((int(int(LCD4linux.WetterIconZoom.value) * Wmulti), y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
							PY = POSY - int(20 * Wmulti) if ConfigType.startswith("5") else int(POSY + (int(40 * Wmulti) - y) / 2)
							PX = POSX + int((27 * Wmulti) - int(int(LCD4linux.WetterIconZoom.value) * Wmulti) / 2)
							self.im[Wim].paste(pil_image, (PX, PY + int(20 * Wmulti)))
						if ConfigType.startswith("5"):
							if LCD4linux.WetterLine.value.startswith("true"):
								self.draw[Wim].line((10, POSY, MAX_W - 10, POSY), fill=ConfigColor)
							w, h = getFsize(Day, fontD)
							PX = int(POSX - w - (3 * Wmulti))
							ShadowText(Wim, PX, POSY, Day, fontD, ConfigColor, ConfigShadow)
							w, h = getFsize("%s°" % High, font)
							PX = int(POSX - w - (3 * Wmulti))
							ShadowText(Wim, PX, POSY + h, "%s°" % High, font, LCD4linux.WetterHighColor.value, ConfigShadow)
							w, h = getFsize("%s° %s°" % (Low, High), font)
							PX = int(POSX - w - (3 * Wmulti))
							ShadowText(Wim, PX, POSY + h, "%s°" % Low, font, LCD4linux.WetterLowColor.value, ConfigShadow)
							w, h = getFsize(Cond, font)
							PX = max(int(POSX - w - (3 * Wmulti)), 0)
							ShadowText(Wim, PX, POSY + 2 * h, Cond, font, ConfigColor, ConfigShadow)
							if LCD4linux.WetterRain.value != "false":
								font = ImageFont.truetype(ConfigFont, int(int(LCD4linux.WetterRainZoom.value) * Wmulti / 10.0), encoding='unic')
								w, h = getFsize(Regen, font)
								RColor = LCD4linux.WetterRainColor.value
								if "." in Regen:
									if float(Regen.replace("m", "")) * 10 >= int(LCD4linux.WetterRainColor2use.value):
										RColor = LCD4linux.WetterRainColor2.value
								else:
									if int(Regen.replace("%", "")) >= int(LCD4linux.WetterRainColor2use.value):
										RColor = LCD4linux.WetterRainColor2.value
								if float(Regen.replace("m", "").replace("%", "")) > 0:
									ShadowText(Wim, MAX_W - w, POSY, Regen, font, RColor, ConfigShadow)
						else:
							Leer, h = getFsize(" ", font)
							w, Dayh = getFsize(Day, fontD)
							PX = POSX + int((27 * Wmulti) - w / 2)
							ShadowText(Wim, PX, POSY, Day, fontD, ConfigColor, ConfigShadow)
							w, h = getFsize(Low, font)
							PX = POSX + int((27 * Wmulti)) - w - int(Leer / 2)
							PY = int(h / 10) if (len(High) > 2 or len(Low) > 3) else 0
							ShadowText(Wim, PX, POSY + PY + int(60 * Wmulti), Low, font, LCD4linux.WetterLowColor.value, ConfigShadow)
							w, h = getFsize(High, font)
							PX = POSX + int((27 * Wmulti)) + int(Leer / 2)
							ShadowText(Wim, PX, POSY + PY + int(60 * Wmulti), High, font, LCD4linux.WetterHighColor.value, ConfigShadow)
							if LCD4linux.WetterRain.value != "false":
								font = ImageFont.truetype(ConfigFont, int(int(LCD4linux.WetterRainZoom.value) * Wmulti / 10.0), encoding='unic')
								w, h = getFsize(Regen, font)
								RColor = LCD4linux.WetterRainColor.value
								if "." in Regen:
									if float(Regen.replace("m", "")) * 10 >= int(LCD4linux.WetterRainColor2use.value):
										RColor = LCD4linux.WetterRainColor2.value
								else:
									if int(Regen.replace("%", "")) >= int(LCD4linux.WetterRainColor2use.value):
										RColor = LCD4linux.WetterRainColor2.value
								if float(Regen.replace("m", "").replace("%", "")) > 0:
									ShadowText(Wim, POSX + int(54 * Wmulti) - w - 2, POSY + Dayh - int(h / 2), Regen, font, RColor, ConfigShadow)
							if LCD4linux.WetterLine.value == "true":
								self.draw[Wim].line((POSX, 1, POSX, POSY + int(60 * Wmulti)), fill=ConfigColor)
							elif LCD4linux.WetterLine.value == "trueLong":
								self.draw[Wim].line((POSX, 1, POSX, POSY + int(80 * Wmulti)), fill=ConfigColor)
						if ConfigType.startswith("5"):
							POSX = int(54 * 2 * Wmulti)
							POSY += int(54 * Wmulti)
						else:
							POSX += int(54 * Wmulti)
				if ConfigType[0] != "5":
					if LCD4linux.WetterLine.value == "true":
						self.draw[Wim].line((POSX, 1, POSX, POSY + int(60 * Wmulti)), fill=ConfigColor)
					elif LCD4linux.WetterLine.value == "trueLong":
						self.draw[Wim].line((POSX, 1, POSX, POSY + int(80 * Wmulti)), fill=ConfigColor)
					POSX += 1
				if ConfigType.startswith("2"):
					POSX = 1
					POSY += int(80 * Wmulti)
			Hum = "?"
			Wind = "?"
			Temp_c = "?"
			Icon = ""
			Locname = ""
			Feel = ""
			Wtime = ""
			if ConfigType == "3":
				POSY = int(-19 * Wmulti)
			elif ConfigType.startswith("5"):
				POSX, POSY = (int(54 * Wmulti), 1)
			if len(self.WDay[ConfigWWW]) != 0 and LCD4linux.WetterExtra.value == True:
				Locname = self.WDay[ConfigWWW].get("Locname", "")
			if len(self.WDay[ConfigWWW]) != 0:
				Temp_c = self.WDay[ConfigWWW].get("Temp_c", "0")
				cleanTemp_c = Temp_c
				Hum = self.WDay[ConfigWWW].get("Hum", "0%")
				cleanHum = Hum.replace("%", "").strip()
				Feel = self.WDay[ConfigWWW].get("Feel", "0")
				cleanFeel = Feel
				Wind = self.WDay[ConfigWWW].get("Wind", "0")
				cleanWind = Wind.split(" ", 1)[0].strip()
				Cond = self.WDay[ConfigWWW].get("Cond", "0")
				Icon = self.WDay[ConfigWWW].get("Icon", "0")
				if self.WetterOK == False:
					Wtime = self.WDay[ConfigWWW].get("Wtime", "00:00")
				if Feel == "" or abs(int(round(float(Feel), 0) or "0") - int(round(float(Temp_c), 0) or "0")) < int(LCD4linux.WetterExtraFeel.value) or LCD4linux.WetterExtra.value == False:
					Feel = ""
				else:
					if trendarrows:
						Feelarrow = "●" if OldFeel == -88 else "▲" if OldFeel < float(Feel) else "▼"
						OldFeel = float(cleanFeel)
						Feel = "%s%s" % (Feelarrow, Feel)
					Feel += "°"
				if trendarrows:
					Temparrow = "●" if OldTemp_c == -88 else "▲" if OldTemp_c < float(Temp_c) else "▼"
					OldTemp_c = float(cleanTemp_c)
					Temp_c = "%s%s" % (Temparrow, Temp_c)
				Temp_c += "°"
				if ConfigType.startswith("4"):
					if ConfigType == "4":
						Temp_c += "C"
					TextSize = int(25 * Wmulti)
					font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
					w, h = getFsize(Temp_c, font)
					while w > MAX_W:
						TextSize -= 1
						font = ImageFont.truetype(ConfigFont, TextSize, encoding='unic')
						w, h = getFsize(Temp_c, font)
					ShadowText(Wim, POSX, POSY, Temp_c, font, ConfigColor, ConfigShadow)
				else:
					xx = yy = 20
					if isfile(join(UseWetterPath, Icon)):
						pil_image = Image.open(join(UseWetterPath, Icon)).convert(imageMode)
						xx, yy = pil_image.size
						if ConfigType.startswith("5"):
							y = int((int(LCD4linux.WetterIconZoom.value) + 5) * Wmulti / xx * yy)
							x = int((int(LCD4linux.WetterIconZoom.value) + 5) * Wmulti)
							if str(LCD4linux.BilderQuality.value) == "0":
								pil_image = pil_image.resize((x, y))
							else:
								pil_image = pil_image.resize((x, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
							xx, yy = pil_image.size
							PY = 1 - int(10 * Wmulti)
						else:
							y = int((int(LCD4linux.WetterIconZoom.value) * Wmulti) / xx * yy)
							x = int(int(LCD4linux.WetterIconZoom.value) * Wmulti)
							if str(LCD4linux.BilderQuality.value) == "0":
								pil_image = pil_image.resize((x, y))
							else:
								pil_image = pil_image.resize((x, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
							PY = int(POSY + (int(34 * Wmulti) - y) / 2)
						self.im[Wim].paste(pil_image, (POSX, PY + int(20 * Wmulti)))
					POSYs = POSY + {"2": 79, "1": 67}.get(LCD4linux.WetterWindLines.value, 56) * Wmulti if ConfigType.startswith("3") else POSY
					minus5 = -3
					font = ImageFont.truetype(ConfigFont, int(((int(LCD4linux.WetterExtraZoom.value) - 100) / 20.0 + 8) * Wmulti), encoding='unic')
					ShadowText(Wim, POSX - minus5, POSYs, "%s %s" % (Locname, Wtime), font, LCD4linux.WetterExtraColorCity.value, ConfigShadow)
					if trendarrows:
						Humarrow = "●" if OldHum == -88 else "▲" if OldHum < float(cleanHum) else "▼"
						OldHum = float(cleanHum)
						Hum = "%s%s" % (Humarrow, Hum)
					if trendarrows:
						Windarrow = "●" if OldWind == -88 else "▲" if OldWind < float(cleanWind[0]) else "▼"
						OldWind = float(cleanWind[0])
						Wind = "%s%s" % (Windarrow, Wind)

					font = ImageFont.truetype(ConfigFont, int(13 * Wmulti), encoding='unic')
					if LCD4linux.WetterWindLines.value == "2":
						Wind = (Wind.split(" ", 2))
						for i in range(len(Wind), 3):
							Wind.append("na")
						ShadowText(Wim, POSX - minus5, POSY + int(56 * Wmulti), "%s %s" % (Wind[0], Wind[1]), font, ConfigColor, ConfigShadow)
						ShadowText(Wim, POSX - minus5, POSY + int(67 * Wmulti), Wind[2], font, ConfigColor, ConfigShadow)
					elif LCD4linux.WetterWindLines.value != "off":
						ShadowText(Wim, POSX - minus5, POSY + int(56 * Wmulti), Wind, font, ConfigColor, ConfigShadow)
					font = ImageFont.truetype(ConfigFont, int((24 if largesize else 20) * Wmulti), encoding='unic')
					w, h = getFsize(Temp_c, font)
					if not PY3:  # for equal results, w needs an correction under Python 2
						w = int(w * (0.57 if trendarrows else 0.66))
					PX = MAX_Wc - int(w)
					PY = POSY + int((8 if largesize else 16) * Wmulti)
					ShadowText(Wim, PX, PY, Temp_c, font, LCD4linux.WetterHighColor.value, ConfigShadow)

					if LCD4linux.WetterRain.value != "false" and LCD4linux.WetterExtra.value:
						if not ConfigType.startswith("4") and len(self.WWeek[ConfigWWW]) > 0:
							Regen = self.WWeek[ConfigWWW][0].get("Regen", "0")
							RColor = LCD4linux.WetterRainColor.value
							if "." in Regen:
								if float(Regen) * 10 >= int(LCD4linux.WetterRainColor2use.value):
									RColor = LCD4linux.WetterRainColor2.value
								Regen += "mm" if LCD4linux.WetterRain.value == "true2" else ""
							else:
								if int(Regen) >= int(LCD4linux.WetterRainColor2use.value):
									RColor = LCD4linux.WetterRainColor2.value
								Regen += "%" if LCD4linux.WetterRain.value == "true2" else ""
							if float(Regen.replace("m", "").replace("%", "")) > 0:
								font = ImageFont.truetype(ConfigFont, int(12 * Wmulti), encoding='unic')
								PX = MAX_Wc - int(int(44 if trendarrows else 32) * Wmulti) - (0 if ConfigType.startswith("3") else int(8 * Wmulti))
								PY = POSY + int((34 if ConfigType.startswith("3") else 31) * Wmulti)
								ShadowText(Wim, PX, PY, Regen, font, RColor, ConfigShadow)

						font = ImageFont.truetype(ConfigFont, int((15 if largesize else 12) * Wmulti), encoding='unic')
						w, h = getFsize(Feel, font)
						if not PY3:  # for equal results, w needs an correction under Python 2
							w = int(w * (0.58 if trendarrows else 0.67))
						PX = MAX_Wc - int(w)
						PY = POSY + int((28 if largesize else 34) * Wmulti)
						ShadowText(Wim, PX, PY, Feel, font, LCD4linux.WetterExtraColorFeel.value, ConfigShadow)

					font = ImageFont.truetype(ConfigFont, int((18 if largesize else 14) * Wmulti), encoding='unic')
					w, h = getFsize(Hum, font)
					if not PY3:  # for equal results, w needs an correction under Python 2
						w = int(w * (0.72 if trendarrows else 0.98)) if largesize else int(w * (0.72 if trendarrows else 0.98))
					PX = MAX_Wc - int(w)
					PY = POSY + int((40 if largesize else 44) * Wmulti)
					ShadowText(Wim, PX, PY, Hum, font, LCD4linux.WetterHumColor.value, ConfigShadow)

			PICwetter[ConfigWWW] = 1
		counter = 20
		while PICwetter[ConfigWWW] == "wait" and counter > 0:
			L4logE("Weatherwait")
			sleep(0.03)
			counter -= 1
		try:
			x, y = self.im[Wim].size
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_Wi, x)
			if LCD4linux.WetterTransparenz.value == "true":
				self.im[im].paste(self.im[Wim], (POSX, ConfigPos), self.im[Wim])
			else:
				self.im[im].paste(self.im[Wim], (POSX, ConfigPos))
		except Exception:
			L4log("Error put Weather")

# Meteo station
	def putMeteo(workaround, draw, im):
		(ConfigPos, ConfigZoom, ConfigAlign, ConfigSplit, ConfigType, ConfigColor) = workaround
		ConfigPos = int(ConfigPos)
		ConfigZoom = int(ConfigZoom)
		global MeteoType
		global MeteoZoom
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		if isfile(PICmeteo) and ConfigType == MeteoType and ConfigZoom == MeteoZoom:
			pil_image = Image.open(PICmeteo)
			x, y = pil_image.size
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
			self.im[im].paste(pil_image, (POSX, ConfigPos))
		else:
			MeteoType = ConfigType
			MeteoZoom = ConfigZoom
			POSX, POSY = 1, 0
			Wmulti = ConfigZoom / 10.0
			if ConfigType == "2":
				MAX_H = int(25 * Wmulti)
			else:
				MAX_H = int(80 * Wmulti)
			if ConfigType == "1":
				MAX_W = int(57 * 2 * Wmulti)
			elif ConfigType == "2":
				MAX_W = int(55 * Wmulti)
			imW = Image.new('RGB', (MAX_W, MAX_H))
			self.draw[0] = ImageDraw.Draw(imW)
			dom = parseString(wwwMeteo)
			Hum = "?"
			Wind = "?"
			Temp_c = "?"
			Rain = ""
			Icon = ""
			if ConfigType == "1":
				POSY = int(-20 * Wmulti)
			for node in dom.getElementsByTagName('current_conditions'):
				for temp_c in node.getElementsByTagName('temp_c'):
					Temp_c = temp_c.getAttribute('data')
				for hum in node.getElementsByTagName('humidity'):
					Hum = hum.getAttribute('data')
				for wind in node.getElementsByTagName('wind_condition'):
					Wind = wind.getAttribute('data')
				for icon in node.getElementsByTagName('icon'):
					Icon = basename(icon.getAttribute('data'))
				for rain in node.getElementsByTagName('rain'):
					Rain = rain.getAttribute('data')
				if ConfigType == "2":
					font = ImageFont.truetype(FONT, int(25 * Wmulti), encoding='unic')
					w, h = getFsize(Temp_c, font)
					TextSize = int(25 * Wmulti)
					while w > MAX_W:
						TextSize -= 1
						font = ImageFont.truetype(FONT, TextSize, encoding='unic')
						w, h = getFsize(Temp_c, font)
					self.draw[0].text((POSX, POSY), Temp_c, font=font, fill=ConfigColor)
				else:
					if isfile(MeteoPath + Icon):
						pil_image = Image.open(MeteoPath + Icon)
						xx, yy = pil_image.size
						y = int(float(40 * Wmulti) / xx * yy)
						if str(LCD4linux.BilderQuality.value) == "0":
							pil_image = pil_image.resize((int(40 * Wmulti), y))
						else:
							pil_image = pil_image.resize((int(40 * Wmulti), y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
						PY = int(POSY + (int(40 * Wmulti) - y) / 2)
						imW.paste(pil_image, (POSX, PY + int(15 * Wmulti)))
					font = ImageFont.truetype(FONT, int(12 * Wmulti), encoding='unic')
					self.draw[0].text((POSX, POSY + int(52 * Wmulti)), Rain, font=font, fill="aquamarine")
					self.draw[0].text((POSX, POSY + int(64 * Wmulti)), Wind, font=font, fill="silver")
					font = ImageFont.truetype(FONT, int(25 * Wmulti), encoding='unic')
					w, h = getFsize(Temp_c, font)
					TextSize = int(25 * Wmulti)
					while POSX + (45 * Wmulti) + w > MAX_W:
						TextSize -= 1
						font = ImageFont.truetype(FONT, TextSize, encoding='unic')
						w, h = getFsize(Temp_c, font)
					self.draw[0].text((POSX + int(45 * Wmulti), POSY + int(16 * Wmulti)), Temp_c, font=font, fill=LCD4linux.WetterHighColor.value)
					font = ImageFont.truetype(FONT, int(22 * Wmulti), encoding='unic')
					w, h = getFsize(Hum, font)
					TextSize = int(25 * Wmulti)
					while POSX + (45 * Wmulti) + w > MAX_W:
						TextSize -= 1
						font = ImageFont.truetype(FONT, TextSize, encoding='unic')
						w, h = getFsize(Hum, font)
					self.draw[0].text((POSX + int(52 * Wmulti), POSY + int(40 * Wmulti)), Hum, font=font, fill="silver")
			imW.save(PICmeteo)
			x, y = imW.size
			MAX_W, MAX_H = self.im[im].size
			if ConfigSplit == True:
				MAX_W = int(MAX_W / 2)
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
			self.im[im].paste(imW, (POSX, ConfigPos))

# Mondphase
	def putMoon(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigFontSize, ConfigAlign, ConfigInfo, ConfigTrends, ConfigSplit, ConfigColor, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		global OldMoonDist
		global Oldillum
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		POS = MoonPosition()
		PHASE = MoonPhase(POS)
		FILE = "moon%04d.gif" % round(POS * 100)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, ConfigSize)
		if isfile(join(LCD4linux.MoonPath.value, FILE)):
			try:
				pil_image = Image.open(join(LCD4linux.MoonPath.value, FILE))
				pil_image = pil_image.resize((ConfigSize, ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					pil_image = pil_image.convert("RGBA")
					self.im[im].paste(pil_image, (POSX, ConfigPos), pil_image)
				else:
					self.im[im].paste(pil_image, (POSX, ConfigPos))
				ConfigPos += ConfigSize * 0.95
			except Exception:
				L4log("Error Moon")
		if ConfigColor != "0":
			font = ImageFont.truetype(ConfigFont, int(ConfigFontSize), encoding='unic')
			P = []
			INFOS = ""
			if ConfigInfo[2] == "1":
				MoonDist = MoonDistance()
				if ConfigTrends:
					MoonDistarrow = "●" if OldMoonDist == -88 else "▲" if OldMoonDist < MoonDist else "▼"
					OldMoonDist = MoonDist
					INFOS += "%s%s km" % (MoonDistarrow, round(MoonDist))
			if ConfigInfo[1] == "1":
				illum = 100 - abs((cos(pi * POS) + 0j) ** 1.7 * 100)
				illum = abs(illum - 1) / .99 if illum - 1 > 0 else 0.0
				if ConfigTrends:
					illumarrow = "●" if Oldillum in [-88, 0] else "▲" if float(Oldillum) < illum else "▼"
					Oldillum = illum
					INFOS += "- %s%s %%" % (illumarrow, round(illum, 1))
			if INFOS != "":
				w, h = getFsize(Code_utf8(INFOS), font)
				if w > ConfigSize:
					P.extend(INFOS.split("-"))
				else:
					INFOS = INFOS.replace('-', ' ')
					P.extend([INFOS])
			if ConfigInfo[0] == "1":
				w, h = getFsize(Code_utf8(PHASE), font)
				if w > ConfigSize:
					P.extend(PHASE.split(" "))
				else:
					P.extend([PHASE])
			for Pi in P:
				w, h = getFsize(Code_utf8(Pi), font)
				px = min(max(int(POSX + (ConfigSize / 2) - w / 2), 0), MAX_W - w)
				ShadowText(draw, px, ConfigPos, Code_utf8(Pi), font, ConfigColor, ConfigShadow)
				ConfigPos += h * 0.9

# Text File
	def putTextFile(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigFont, ConfigAlign, ConfigColor, ConfigBackColor, ConfigShadow, TextFile) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		if ConfigMode == True and isfile(TextFile) == False:
			if isfile(TXTdemo) == False:
				with open(TXTdemo, "w") as f:
					f.write("demo line 1\ndemotext")
			TextFile = TXTdemo
		if isfile(TextFile):
			MAX_W, MAX_H = self.im[im].size
			current_h = ConfigPos
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			try:
				for line in open(TextFile, "r").readlines():
					line = Code_utf8(line.replace('\n', ''))
					w, h = getFsize(line, font)
					POSX = getSplit(False, ConfigAlign, MAX_W, w)
					if ConfigBackColor != "0":
						self.draw[draw].rectangle((POSX, current_h, POSX + w, current_h + h), fill=ConfigBackColor)
					ShadowText(draw, POSX, current_h, line, font, ConfigColor, ConfigShadow)
					current_h += h
			except Exception:
				L4log("Error reading", TextFile)

# String-Text
	def putString(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigFont, ConfigAlign, ConfigSplit, ConfigColor, ConfigBackColor, ConfigShadow, ConfigText) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		current_h = ConfigPos
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		line = Code_utf8(ConfigText.replace('\n', ''))
		w, h = getFsize(line, font)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
		if ConfigBackColor != "0":
			self.draw[draw].rectangle((POSX, current_h, POSX + w, current_h + h), fill=ConfigBackColor)
		ShadowText(draw, POSX, current_h, line, font, ConfigColor, ConfigShadow)

# external IP Address
	def putExternalIP(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigFont, ConfigAlign, ConfigSplit, ConfigColor, ConfigBackColor, ConfigShadow, ConfigText) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		ConfigText = ensure_str(ConfigText)
		MAX_W, MAX_H = self.im[im].size
		current_h = ConfigPos
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		line = Code_utf8(ConfigText.replace('\n', ''))
		w, h = getFsize(line, font)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
		if ConfigBackColor != "0":
			self.draw[draw].rectangle((POSX, current_h, POSX + w, current_h + h), fill=ConfigBackColor)
		ShadowText(draw, POSX, current_h, line, font, ConfigColor, ConfigShadow)

# HTTP Text
	def putHTTP(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigColor, ConfigBackColor, HTTPurl, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		t = ["not found"]
		try:
			r = urlopen(HTTPurl)
			t = _unescape(r.read()[:500].decode()).split("\n")
			r.close()
		except Exception:
			pass
		finally:
			MAX_W, MAX_H = self.im[im].size
			current_h = ConfigPos
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			for line in t:
				line = Code_utf8(line.replace('\n', ''))
				w, h = getFsize(line, font)
				POSX = getSplit(False, ConfigAlign, MAX_W, w)
				if ConfigBackColor != "0":
					self.draw[draw].rectangle((POSX, current_h, POSX + w, current_h + h), fill=ConfigBackColor)
				ShadowText(draw, POSX, current_h, line, font, ConfigColor, ConfigShadow)
				current_h += h

# HTTP WWW Site
	def putWWW(workaround, draw, im):
		(PIC, ConfigPos, ConfigSize, ConfigAlign, ConfigCutX, ConfigCutY, ConfigCutW, ConfigCutH) = workaround
		MAX_W, MAX_H = self.im[im].size
		if isfile(WWWpic % PIC):
			if isfile(WWWpic % (str(PIC) + "p")):
				pil_image = Image.open(WWWpic % (str(PIC) + "p"))
				POSX = getSplit(False, ConfigAlign, MAX_W, ConfigSize)
				self.im[im].paste(pil_image, (POSX, ConfigPos))
			else:
				pil_image = Image.open(WWWpic % PIC)
				if ConfigCutW != 0 and ConfigCutH != 0:
					try:
						pil_image = pil_image.crop((ConfigCutX, ConfigCutY, ConfigCutX + ConfigCutW, ConfigCutY + ConfigCutH))
					except Exception:
						L4log("Error Crop WWW")
				xx, yy = pil_image.size
				y = int(float(ConfigSize) / xx * yy)
				try:
					if str(LCD4linux.BilderQuality.value) == "0":
						pil_image = pil_image.resize((ConfigSize, y))
					else:
						pil_image = pil_image.resize((ConfigSize, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
					POSX = getSplit(False, ConfigAlign, MAX_W, ConfigSize)
					self.im[im].paste(pil_image, (POSX, ConfigPos))
					pil_image.save(WWWpic % (str(PIC) + "p"))
				except Exception:
					L4log("Error resize WWW")

# Clock
	def putClock(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType, ConfigSpacing, ConfigAnalog, ConfigColor, ConfigShadow, ConfigNum, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		pp = ConfigPos
		if ConfigType.startswith("4"):
			y = int(ConfigSize * 1.8)
			y271 = int(y / 2.71)
			if isfile(ClockBack) == True:
				try:
					pil_image = Image.open(ClockBack)
					xx, yy = pil_image.size
					x = int(float(y) / yy * xx)
					if str(LCD4linux.BilderQuality.value) == "0":
						pil_image = pil_image.resize((x, y))
					else:
						pil_image = pil_image.resize((x, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
					POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
					if LCD4linux.WetterTransparenz.value == "true":
						pil_image = pil_image.convert("RGBA")
						self.im[im].paste(pil_image, (POSX, ConfigPos), pil_image)
					else:
						self.im[im].paste(pil_image, (POSX, ConfigPos))
					pil_image = pil_image.crop((0, y271, x, y271 + 2 + int(y / 60)))
					now = strftime("%H")
					font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
					w, h = getFsize(now, font)
					lx = int(((x / 2) - w) / 2)
					ShadowText(draw, POSX + lx, ConfigPos + int(y271 - (h / 2)), now, font, ConfigColor, ConfigShadow)
					now = strftime("%M")
					w, h = getFsize(now, font)
					lx = int(((x / 2) - w) / 2)
					ShadowText(draw, POSX + int(x / 2) + lx, ConfigPos + int(y271 - (h / 2)), now, font, ConfigColor, ConfigShadow)
					self.im[im].paste(pil_image, (POSX, ConfigPos + y271))
					if ConfigType == "41":
						now = Code_utf8(_(strftime("%A")))
					else:
						now = strftime(_("%d.%m.%Y"))
					font = ImageFont.truetype(ConfigFont, int(ConfigSize / 3.0), encoding='unic')
					w, h = getFsize(now, font)
					lx = (x - w) / 2
					ShadowText(draw, POSX + lx, ConfigPos + int((y / 1.14) - (h / 2)), now, font, ConfigColor, ConfigShadow)
				except Exception:
					pass
		elif ConfigType[0].startswith("5"):
			y = int(ConfigSize * 1.8)
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, y)
			pil_image = Clock + str(ConfigAnalog) + "/Clock.png"
			if isfile(pil_image) == True:
				ClockfaceIm = Image.open(pil_image)
				x1, y1 = ClockfaceIm.size
				x = int(x1 * y / y1)
				POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
				try:
					if self.ClockName[ConfigNum] != [int(ConfigAnalog), y]:
						self.ClockIm[ConfigNum] = Image.open(pil_image)
						if str(LCD4linux.BilderQuality.value) == "0":
							self.ClockIm[ConfigNum] = self.ClockIm[ConfigNum].resize((x, y))
						else:
							self.ClockIm[ConfigNum] = self.ClockIm[ConfigNum].resize((x, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
						self.ClockName[ConfigNum] = [int(ConfigAnalog), y]
					self.im[im].paste(self.ClockIm[ConfigNum], (POSX, ConfigPos), self.ClockIm[ConfigNum])
					# Weekday in or underneath clockface
					if ConfigType[:3] == "521":
						if "+" in ConfigType:  # means weekday in combination with date
							now = Code_utf8(_(strftime("%A")))
							font = ImageFont.truetype(ConfigFont, int(y / 6), encoding='unic')
						else:                 # means weekday in clockface only
							now = Code_utf8(_(strftime("%a")))
							font = ImageFont.truetype(ConfigFont, int(y / 9), encoding='unic')
						w, h = getFsize(now, font)
						if "+" in ConfigType:  # means weekday in combination with date
							x1 = POSX + int(x / 2) - int(w * 1.1)
							y1 = ConfigPos + y
						else:                 # means weekday in clockface only
							x1 = POSX + int(x * 3 / 4)
							y1 = ConfigPos + int(y / 2) - int(h / 2)
							di = int(h / 7)
							self.draw[draw].rectangle((x1 - di, y1 + di - 1, x1 + w + di, y1 + h - di), fill="black")
						ShadowText(draw, x1, y1, now, font, ConfigColor, ConfigShadow)
					# Hour
					pil_image = Image.open(Clock + str(ConfigAnalog) + "/Hour.png")
					x1, y1 = pil_image.size
					x1 = int(x1 * y / y1)
					y1 = y
					if str(LCD4linux.BilderQuality.value) == "0":
						pil_image = pil_image.resize((x1, y1))
					else:
						pil_image = pil_image.resize((x1, y1), Image.LANCZOS if PY3 else Image.ANTIALIAS)
					S = int(strftime("%H")) % 12
					pil_image = pil_image.rotate(360 - int(30 * S + int(int(strftime("%M")) / 2))).convert("RGBA")  # 360/12
					self.im[im].paste(pil_image, (POSX + int((x - x1) / 2), ConfigPos + int((y - y1) / 2)), pil_image)
					# Minute
					pil_image = Image.open(Clock + str(ConfigAnalog) + "/Minute.png")
					x1, y1 = pil_image.size
					x1 = int(x1 * y / y1)
					y1 = y
					if str(LCD4linux.BilderQuality.value) == "0":
						pil_image = pil_image.resize((x1, y1))
					else:
						pil_image = pil_image.resize((x1, y1), Image.LANCZOS if PY3 else Image.ANTIALIAS)
					pil_image = pil_image.rotate(360 - int(6 * int(strftime("%M")))).convert("RGBA")  # 360/60
					self.im[im].paste(pil_image, (POSX + int((x - x1) / 2), ConfigPos + int((y - y1) / 2)), pil_image)
					# Seconds: Due to the bad refresh rates, the second hand was deliberately not programmed!
					# Date underneath clockface
					if ConfigType[:2] == "52":
						now = strftime(_("%d.%m.%Y"))
						font = ImageFont.truetype(ConfigFont, int(y / 6), encoding='unic')
						w, h = getFsize(now, font)
						if "+" in ConfigType:  # means weekday in combination with date
							x1 = POSX + int(x / 2)
							y1 = ConfigPos + y
						else:                 # means date only
							x1 = POSX + int(x / 2) - int(w / 2)
							y1 = ConfigPos + y
						ShadowText(draw, x1, y1, now, font, ConfigColor, ConfigShadow)
				except Exception:
					pass
		elif ConfigType.startswith("1"):
			now = ""
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			ww, hS = getFsize(strftime("%H:%M"), font)
			font = ImageFont.truetype(ConfigFont, int(ConfigSize / 2), encoding='unic')
			ww2, hS = getFsize(strftime(_("%d.%m.%Y")), font)
			if ww2 > ww:
				ww = ww2
			lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, ww)
			ll = int(lx + ww / 2)
			for tt in ConfigType[1:]:
				font = ImageFont.truetype(ConfigFont, int(ConfigSize / 2), encoding='unic')
				w, h2 = getFsize(now, font)
				if tt == "1":
					now = strftime(_("%d.%m.%Y"))
				elif tt == "2":
					now = strftime("%H:%M")
					font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				elif tt == "3":
					font = ImageFont.truetype(ConfigFont, int(ConfigSize / 2.5), encoding='unic')
					now = Code_utf8(_(strftime("%A")))
				w, h = getFsize(now, font)
				lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
				if (ll + w / 2) < MAX_W and (ll - w / 2) > 0:
					ShadowText(draw, int(ll - w / 2), pp, now, font, ConfigColor, ConfigShadow)
				else:
					ShadowText(draw, lx, pp, now, font, ConfigColor, ConfigShadow)
				pp += h if int(ConfigSpacing) == 0 else h - int(h2 / (5 - int(ConfigSpacing)))

# Cover
	def putCover(workaround, ConfigLCD, draw, im):
		(ConfigPos, ConfigSize, ConfigSizeH, ConfigAlign, ConfigTransp, ConfigTrim) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		ConfigSizeH = int(ConfigSizeH)
		MAX_W, MAX_H = self.im[im].size
		small = ""
		x = ConfigSize
		if ConfigMode == True:
			POSX = int(getSplit(False, ConfigAlign, MAX_W, ConfigSize))
			if ConfigSizeH > 0:
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + ConfigSize, ConfigPos + ConfigSizeH), fill="red")
			else:
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + ConfigSize, ConfigPos + (ConfigSize * 3 / 4)), fill="red")
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + ConfigSize, ConfigPos + ConfigSize), outline="red")
		ShowPicture = getShowCover((LCD4linux.MPCoverPath1.value, LCD4linux.MPCoverPath2.value))
		if isfile(ShowPicture):
			if self.CoverName[0] != [ShowPicture, getmtime(ShowPicture)]:
				self.CoverName[0] = [ShowPicture, getmtime(ShowPicture)]
				self.CoverName[1] = "wait"
				try:
					pil_image = Image.open(ShowPicture)
					if ConfigTrim:
						xx, yy = pil_image.size
						pix = pil_image.load()
						if pix is not None:
							if isinstance(pix[0, 0], int):
								pcheck = 255 if pix[0, 0] == 255 else "x0"
							elif len(pix[0, 0]) == 3:
								pcheck = (255, 255, 255) if pix[0, 0] == (255, 255, 255) else "x(0,0,0)"
							else:
								pcheck = (255, 255, 255, 255) if pix[0, 0] == (255, 255, 255, 255) else "x(0,0,0,0)"
							L4logE("Cover Color 0,0", pix[0, 0])
							L4logE("Cover Check %s" % pcheck)
							x2 = int(xx / 2)
							y2 = int(yy / 2)
							l, o = 0, 0
							r = xx - 1
							u = yy - 1
							while pix[l, y2] == pcheck and l < x2:
								l += 1
							l += 1
							while pix[r, y2] == pcheck and r > x2:
								r -= 1
							r -= 1
							while pix[x2, o] == pcheck and o < y2:
								o += 1
							o += 1
							while pix[x2, u] == pcheck and u > y2:
								u -= 1
							u -= 1
							if l > 1 or o > 1:
								pil_image = pil_image.crop((l, o, r, u))
							L4logE("Cover Trim (%s, %s, %s, %s)" % (l, o, r, u))
					xx, yy = pil_image.size
					L4log("CoverSize (%s, %s)" % pil_image.size)
					y = int(float(x) / xx * yy)
					if ConfigAlign == "9":
						x, y = MAX_W, MAX_H
					if ConfigSizeH > 0 and y > ConfigSizeH:
						y = ConfigSizeH
						x = int(float(y) / yy * xx)
					pil_image = pil_image.resize((x, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
					if ConfigTransp == True:
						self.CoverIm = pil_image.convert("RGBA")
					else:
						self.CoverIm = pil_image.convert("RGB", dither=Image.NONE, palette=Image.ADAPTIVE)
					del pil_image
					self.CoverName[1] = ""
					L4log("change Cover", ShowPicture)
				except Exception:
					self.CoverName[1] = ""
					L4log("Error Coveropen", format_exc())
			counter = 20
			while self.CoverName[1] == "wait" and counter > 0:
				L4logE("Coverwait")
				sleep(0.03)
				counter -= 1
			if self.CoverIm is not None:
				small = ConfigAlign
				x, y = self.CoverIm.size
				POSX = getSplit(False, ConfigAlign, MAX_W, x)
				if small == "2":
					POSX -= int((ConfigSize - x) / 2)
				elif small == "0":
					POSX += int((ConfigSize - x) / 2)
				if ConfigSizeH > 0:
					ConfigPos = ConfigPos + int((ConfigSizeH - int(y)) / 2)
				if ConfigAlign == "9":
					POSX, ConfigPos = 0, 0
				try:
					if ConfigTransp == True and self.CoverIm.mode == "RGBA":
						self.im[im].paste(self.CoverIm, (POSX, ConfigPos), self.CoverIm)
					else:
						self.im[im].paste(self.CoverIm, (POSX, ConfigPos))
				except Exception:
					L4log("Error put Cover")
		if self.CoverError != "":
			POSX = getSplit(False, ConfigAlign, MAX_W, ConfigSize)
			font = ImageFont.truetype(FONT, 13, encoding='unic')
			ShadowText(draw, POSX, ConfigPos, self.CoverError, font, "red", True)

# Bild
	def putBild(workaround, ConfigLCD, draw, im):
		(ConfigPos, ConfigSize, ConfigSizeH, ConfigAlign, ConfigQuick, ConfigTransp, ConfigRotate, ConfigFile, ConfigFileOrg) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		ConfigSizeH = int(ConfigSizeH)
		global QuickList
		MAX_W, MAX_H = self.im[im].size
		if ConfigMode == True:
			POSX = getSplit(False, ConfigAlign, MAX_W, ConfigSize)
			if ConfigSizeH > 0:
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + ConfigSize, ConfigPos + ConfigSizeH), fill="red")
			else:
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + ConfigSize, ConfigPos + (ConfigSize * 3 / 4)), fill="red")
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + ConfigSize, ConfigPos + ConfigSize), outline="red")
		if isfile(ConfigFile):
			x = ConfigSize
			try:
				pil_image = Image.open(ConfigFile)
				xx, yy = pil_image.size
				y = int(float(x) / xx * yy)
				if ConfigAlign == "9":
					x, y = MAX_W, MAX_H
				if ConfigSizeH > 0 and y > ConfigSizeH:
					y = ConfigSizeH
					x = int(float(y) / yy * xx)
				POSX = getSplit(False, ConfigAlign, MAX_W, x)
				if ConfigAlign == "2":
					POSX -= int((ConfigSize - x) / 2)
				elif ConfigAlign == "0":
					POSX += int((ConfigSize - x) / 2)
				elif ConfigAlign == "8":
					x, y = ConfigSize, ConfigSizeH
				if str(LCD4linux.BilderQuality.value) == "2":
					pil_image = pil_image.resize((x, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
				else:
					pil_image = pil_image.resize((x, y))
				if ConfigSizeH > 0:
					ConfigPos = ConfigPos + int((ConfigSizeH - y) / 2)
				if ConfigAlign == "9":
					POSX, ConfigPos = 0, 0
				if ConfigTransp == True:
					pil_image = pil_image.convert("RGBA")
					self.im[im].paste(pil_image, (POSX, ConfigPos), pil_image)
				else:
					self.im[im].paste(pil_image, (POSX, ConfigPos))
				if ConfigQuick == True:
					L4logE("add Quick", ConfigFileOrg)
					QuickList[ConfigLCD].append([ConfigFileOrg, POSX, ConfigPos, x, y])
			except Exception:
				pass
		else:
			if LCD4linux.ShowNoMsg.value == True:
				POSX = getSplit(False, ConfigAlign, MAX_W, ConfigSize)
				font = ImageFont.truetype(FONT, 15, encoding='unic')
				ShadowText(draw, POSX, ConfigPos, Code_utf8("%s %s" % (_("Picture not available"), basename(ConfigFile))), font, "red", True)

# Grab TV
	def doGrabTV(x, y, lcd, vidosd):
		global TVrunning
		L4logE("GrabTV start", lcd)
		if TVrunning == False:
			TVrunning = True
			BriefRes.put([doGrabTVthread, x, y, lcd, vidosd])

	class GrabTV:
		def __init__(self, cmd):
			global GrabTVRunning
			GrabTVRunning = True
			L4logE("GrabTV Run")
			system(cmd + " >/dev/null 2>&1")
			self.cmdFinished("")

		def cmdFinished(self, data):
			global GrabTVRunning
			L4logE("GrabTV Stop")
			GrabTVRunning = False

		def dataAvail(self, data):
			pass

	def doGrabTVthread(x, y, lcd, vidosd):
		global TVrunning
		global SamsungDevice
		global SamsungDevice2
		global SamsungDevice3
		vt = "-v" if vidosd == "0" else ""
		if self.isFB2 and LCD4linux.SwitchToFB2.value == True:
			setFB2("0")
			L4log("TV start")
			while TVrunning == True and getSA(int(lcd)) in LCD4linux.TV.value:
				sleep(0.5)
				L4log("TV ....")
			L4log("TV stop")
			setFB2("1")
		else:
			self.im[0] = Image.new('RGB', (int(x), int(y)), (0, 0, 0, 0))
			while TVrunning == True and getSA(int(lcd)) in LCD4linux.TV.value:
				GrabTV("%sgrab %s -j 40 -r %s %stvgrab.jpg" % (LCD4bin, vt, x, TMPL))
				i = 0
				while GrabTVRunning == True and i < 500:
					sleep(0.01)
					i += 1
				try:
					pic = Image.open("%stvgrab.jpg" % TMPL)
					self.im[0].paste(pic, (0, 0))
					if TVrunning == True:
						if lcd == "1":
							Brief1.put([writeLCD1, self, 0, LCD4linux.BilderJPEG.value, False])
						elif lcd == "2":
							Brief2.put([writeLCD2, self, 0, LCD4linux.BilderJPEG.value, False])
						elif lcd == "3":
							Brief3.put([writeLCD3, self, 0, LCD4linux.BilderJPEG.value, False])
				except Exception:
					L4log("put Grab Error:", format_exc())
		TVrunning = False

	def putGrab(ConfigFast, ConfigSize, im, draw):
		global OSDon
		if ScreenActive[im] != "" or (self.isFB2 and LCD4linux.SwitchToFB2.value == True):
			return
		MAX_W, MAX_H = self.im[im].size
		i = 0
		while GrabRunning == True and i < 100:
			sleep(0.05)
			i += 1
		L4logE("put Grab")
		if isfile("%sdpfgrab.jpg" % TMPL):
			try:
				pil_image = Image.open("%sdpfgrab.jpg" % TMPL)
				xx, yy = pil_image.size
				if OSDon > 0:
					if str(LCD4linux.OSDTransparenz.value) == "0":
						self.im[im].paste(pil_image, (int((MAX_W - xx) / 2), int((MAX_H - yy) / 2)))
					else:
						pix = pil_image.load()
						if pix is not None:
							pcheck = (0, 0, 0) if pix[0, 0] == (0, 0, 0) else (255, 255, 255)
							L4logE("Grabpixel", pix[0, 0])
							x2 = int(xx / 2)
							y2 = int(yy / 2)
							l, o = 0, 0
							r = xx - 1
							u = yy - 1
							while pix[l, y2] == pcheck and l < x2:
								l += 1
							l += 1
							while pix[r, y2] == pcheck and r > x2:
								r -= 1
							r -= 1
							while pix[x2, o] == pcheck and o < y2:
								o += 1
							o += 1
							while pix[x2, u] == pcheck and u > y2:
								u -= 1
							u -= 1
							if str(LCD4linux.OSDTransparenz.value) == "2":
								self.draw[draw].rectangle((0, 0, MAX_W, MAX_H), fill="black")
							pix_image = pil_image.crop((l, o, r, u))
							xx, yy = pix_image.size
							self.im[im].paste(pix_image, ((MAX_W - xx) // 2, (MAX_H - yy) // 2))
			except Exception:
				L4log("put Grab Error:", format_exc())

# Timer Record
	def putTimer(workaround, draw, im):
		(ConfigBox, ConfigPos, ConfigSize, ConfigProzent, ConfigLines, ConfigType, ConfigType2, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigFont) = workaround
		ConfigSize = int(ConfigSize)
		ConfigPos = int(ConfigPos)
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		Progess = getProgess(MAX_W, ConfigProzent)
		POSY = ConfigPos
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, Progess)
		h = 0
		timercount = 0
		TL = self.Ltimer_list if ConfigBox == 0 else self.wwwBoxTimer
		TL = sorted(TL, key=lambda x: x.begin, reverse=False)
		for timerlist in TL:
			if timerlist.disabled == 0 and timerlist.justplay == 0 and str(timerlist.service_ref)[:3] != "-1:":
				if timercount < int(ConfigLines):
					a = int(config.recording.margin_before.value) * 60 if ConfigType == "0" else 0
					b = int(config.recording.margin_after.value) * 60 if ConfigType == "0" else 0
					begin = strftime("%d. %H:%M", localtime(int(timerlist.begin) + a))
					timer_name = Code_utf8(timerlist.name)
					w, h = getFsize(begin, font)
					hk = 0 if ConfigType2 == "0" else h + 5
					if ConfigLines == "1":
						begin += strftime(" - %H:%M", localtime(int(timerlist.end) - b))
						tx = cutText(begin, draw, font, Progess - h - 5)
						tx2 = cutText(timer_name, draw, font, Progess - h - 5)
						ShadowText(draw, POSX + hk, POSY, tx, font, ConfigColor, ConfigShadow)
						ShadowText(draw, POSX + hk, POSY + h, tx2, font, ConfigColor, ConfigShadow)
					else:
						tx = cutText("%s %s" % (begin, timer_name), draw, font, Progess - h - 5)
						if timerlist.state == 2:
							ShadowText(draw, POSX + hk, POSY, tx, font, "red", ConfigShadow)
						else:
							ShadowText(draw, POSX + hk, POSY, tx, font, ConfigColor, ConfigShadow)
					POSY += h
				timercount += 1
		if timercount == 0:
			if LCD4linux.ShowNoMsg.value == True:
				w, h = getFsize(_("no Timer"), font)
				ShadowText(draw, POSX + h + 5, ConfigPos, _("no Timer"), font, ConfigColor, ConfigShadow)
		elif ConfigType2 != "0":
			self.draw[draw].ellipse((POSX + 2, ConfigPos + 2, POSX + h - 2, ConfigPos + h - 2), fill="red")
			if timercount > 99:
				S = int(h / 1.4) - 4
			elif timercount > 9:
				S = int(h / 1.2) - 4
			else:
				S = h - 4
			font = ImageFont.truetype(ConfigFont, S, encoding='unic')
			w1, h1 = getFsize(str(timercount), font)
			POSX = POSX + 1 + int(((h - 2) - w1) / 2)
			POSY = ConfigPos + 1 + int(((h - 2) - h1) / 2)
			self.draw[draw].text((POSX, POSY), str(timercount), font=font, fill="white")

# Picon
	def putPicon(workaround, draw, im):
		(ConfigSize, ConfigPos, ConfigAlign, ConfigFullScreen, ConfigSplit, ConfigTextSize, Picon2) = workaround
		ConfigSize = int(ConfigSize)
		ConfigPos = int(ConfigPos)
		ConfigTextSize = int(ConfigTextSize)
		MAXi_W, MAXi_H = self.im[im].size
		if ConfigSplit == True:
			MAXi_W = int(MAXi_W / 2)
		if self.LsreftoString is not None:
			if ConfigFullScreen == True:
				MAX_W, MAX_H = MAXi_W, MAXi_H
			else:
				MAX_W, MAX_H = ConfigSize, ConfigSize
			rr = str(self.LsreftoString)
			if rr.find("::") > 1:
				rr = rr.split("::")[0] + ":"
			rr = ':'.join(rr.split(':')[:11])
			pos = rr.rfind(':')
			if pos != -1:
				rr = rr[:pos]
			picon = "%s.png" % rr.rstrip(":").replace(":", "_")
			if Picon2 == 0:
				P2 = LCD4linux.PiconPath.value
				P2A = LCD4linux.PiconPathAlt.value
				P2C = LCD4linux.PiconCache.value
			else:
				P2 = LCD4linux.Picon2Path.value
				P2A = LCD4linux.Picon2PathAlt.value
				P2C = LCD4linux.Picon2Cache.value
			ret = ""
			if len(P2C) > 2:
				useCache = True
				ret = getpiconres(ConfigSize, MAX_H, ConfigFullScreen, picon, self.Lchannel_name, self.Lchannel_name2, P2, P2A, P2C)
			else:
				useCache = False
				PIC = []
				PIC.append(join(P2, picon))
				if not PY3:
					name2 = "%s.png" % self.Lchannel_name.decode("utf-8").encode("latin-1", "ignore")
					name4 = "%s.png" % self.Lchannel_name.decode("utf-8").encode("utf-8", "ignore")
					name3 = "%s.png" % self.Lchannel_name2.replace('\xc2\x87', '').replace('\xc2\x86', '').decode("utf-8").encode("utf-8")
					name = normalize('NFKD', self.Lchannel_name.decode('unicode-escape'))
				else:
					name2 = "%s.png" % self.Lchannel_name
					name4 = "%s.png" % self.Lchannel_name
					name3 = "%s.png" % self.Lchannel_name2.replace('\x87', '').replace('\x86', '')
					name = normalize('NFKD', self.Lchannel_name)
				name = "%s.png" % sub(r'[^a-z0-9]', '', str(name).replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
				name5 = getPiconName(self.LsreftoString)
				PIC.append(join(P2, name3))
				PIC.append(join(P2, name2))
				PIC.append(join(P2, name))
				PIC.append(join(P2, name4))
				PIC.append(join(P2, name5))
				fields = picon.split("_", 3)
				if fields[0] in ("4097", "5001", "5002", "5003"):
					fields[0] = "1"
					PIC.append(join(P2, "_".join(fields)))
				if len(P2A) > 3:
					PIC.append(join(P2A, picon))
					PIC.append(join(P2A, name3))
					PIC.append(join(P2A, name2))
					PIC.append(join(P2A, name))
					PIC.append(join(P2A, name4))
					PIC.append(join(P2A, name5))
					fields = picon.split("_", 3)
					if fields[0] in ("4097", "5001", "5002", "5003"):
						fields[0] = "1"
						PIC.append(join(P2, "_".join(fields)))
				fields = picon.split("_", 3)
				if len(fields) > 2 and fields[2] not in ["1", "2"]:
					fields[2] = "1"
					picon = "_".join(fields)
					PIC.append(join(P2, picon))
					if len(P2A) > 3:
						PIC.append(join(P2A, picon))
				PIC.append(join(P2, "picon_default.png"))
				L4logE("Piconsearch", "%s" % PIC)
				for Pic in PIC:
					if isfile(Pic):
						ret = Pic
						break
			POSX, POSY = 0, ConfigPos
			POSX = getSplit(ConfigSplit, ConfigAlign, MAXi_W, MAX_W)
			if ret == "":
				if self.Lchannel_name is not None:
					font = ImageFont.truetype(FONT, int(ConfigTextSize), encoding="unic")
					Channel_list = wrap(self.Lchannel_name, width=int((MAX_W * 2) / int(ConfigTextSize)), break_long_words=False)
					hadd = 0
					l = 0
					for Channel_line in Channel_list:
						if PY3:
							Channel_line = Channel_line.replace('\x87', '').replace('\x86', '')
						if l < 3:
							w, h = getFsize(Channel_line, font)
							TextSize = ConfigTextSize
							while w > MAX_W:
								TextSize -= 1
								font = ImageFont.truetype(FONT, TextSize, encoding='unic')
								w, h = getFsize(Channel_line, font)
							self.draw[draw].text((((MAX_W - w) / 2) + POSX, (POSY + hadd)), Channel_line, font=font, fill="white")
							l += 1
							hadd += h
			else:
				if (ret, ConfigSize) != self.PiconName[Picon2][0] or ConfigMode == True:
					self.PiconName[Picon2][0] = (ret, ConfigSize)
					self.PiconName[Picon2][1] = "wait"
					L4logE("load new Picon", ret)
					try:
						self.PiconIm[Picon2] = Image.open(ret)
						if useCache == False:
							if str(LCD4linux.PiconTransparenz.value) == "2":
								self.PiconIm[Picon2] = self.PiconIm[Picon2].convert("RGBA")
							xx, yy = self.PiconIm[Picon2].size
							if ConfigFullScreen == False:
								y = int(float(ConfigSize) / xx * yy)
							else:
								y = MAX_H - ConfigPos
							if str(LCD4linux.BilderQuality.value) == "0":
								self.PiconIm[Picon2] = self.PiconIm[Picon2].resize((ConfigSize, y))
							else:
								self.PiconIm[Picon2] = self.PiconIm[Picon2].resize((ConfigSize, y), Image.LANCZOS if PY3 else Image.ANTIALIAS)
						self.PiconName[Picon2][1] = ""
					except Exception:
						self.PiconName[Picon2][1] = ""
						self.PiconName[Picon2][0] = "Err"
						L4log("Error Picon", ret)
				try:
					counter = 20
					while self.PiconName[Picon2][1] == "wait" and counter > 0:
						L4logE("Piconwait")
						sleep(0.03)
						counter -= 1
					MAX_W, MAX_H = self.PiconIm[Picon2].size
					POSX = getSplit(ConfigSplit, ConfigAlign, MAXi_W, MAX_W)
					if str(LCD4linux.PiconTransparenz.value) == "2":
						self.im[im].paste(self.PiconIm[Picon2], (POSX, POSY), self.PiconIm[Picon2])
					else:
						self.im[im].paste(self.PiconIm[Picon2], (POSX, POSY))
				except Exception:
					self.PiconName[Picon2][0] = "Err"
					L4log("Error put Picon")

# aktive Sendernummer
	def putChannelNum(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigBackColor, ConfigColor, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		num = self.Lchannel_num
		if num == "None":
			num = ""
		if num != "":
			if len(num) == 1:
				num = " %s " % num
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			w, h = getFsize(num, font)
			lx = getSplit(False, ConfigAlign, MAX_W, w)
			if ConfigBackColor != "0":
				self.draw[draw].rectangle((lx, ConfigPos, lx + w, ConfigPos + h), fill=ConfigBackColor)
			ShadowText(draw, lx, ConfigPos, num, font, ConfigColor, ConfigShadow)

# aktive Sendername
	def putChannel(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigLines, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		channel_name = ""
		Progress = getProgess(MAX_W, ConfigProzent)
		if self.Lchannel_name is not None:
			if not PY3:
				channel_name = self.Lchannel_name
			else:
				channel_name = self.Lchannel_name.replace('\x87', '').replace('\x86', '')
			ch = self.LsreftoString.split("::")
			if len(ch) > 1:
				channel_name = Code_utf8(ch[1])
		if ConfigLines == "1":
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			w, h = getFsize(channel_name, font)
			while w > Progress:
				ConfigSize -= 1
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				w, h = getFsize(channel_name, font)
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
			ShadowText(draw, POSX, ConfigPos, channel_name, font, ConfigColor, ConfigShadow)
		else:
			if ConfigLines == "0":
				ConfigLines = "1"
			writeMultiline(channel_name, ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, draw, im, ConfigFont=ConfigFont, Shadow=ConfigShadow, Width=Progress)

# Progress Bar
	def putProgress(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigType, ConfigColor, ConfigColorText, ConfigAlign, ConfigMinutes, ConfigBorder, ConfigShadow, ConfigShadowBar, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		global isVideoPlaying
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigAlign in ["5", "6"]:
			ConfigSplit = True
			MAX_W = int(MAX_W / 2)
			ConfigAlign = "0" if ConfigAlign == "5" else "2"
			MAX_W -= 10
		else:
			ConfigSplit = False
			MAX_W -= 20
		POSX = 0
		isVideoPlaying = 0
		isData = False
		event_run = 0
		ProgressBar = getProgess(MAX_W, ConfigProzent)
		if len(str(ConfigAlign)) > 1:
			ProgressBar -= getSplit(ConfigSplit, ConfigAlign, MAX_W, ProgressBar)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, ProgressBar)
		if self.LsreftoString is not None:
			if ConfigMinutes:
				Minutes = " min"
				Prozent = " %"
			else:
				Minutes = ""
				Prozent = ""
			if ConfigType[1:] == "1":
				ms = 1.5
			elif ConfigType[1:] == "2":
				ms = 2
			else:
				ms = 1
			font = ImageFont.truetype(ConfigFont, int(ConfigSize * ms) + 8, encoding='unic')  # 5
#			if self.Lpath and ":0:" not in self.Lpath and "//" not in self.Lpath:
			if self.Llength is not None and self.Llength[0] != -1:  # Movie
				isVideoPlaying = 1
				try:
					length = self.Llength
					position = self.Lposition
					if (length and position) and (length[1] > 0):
						if ConfigType[0] in ["2", "4", "6", "8", "9", "A"]:
							if ConfigType[0] in ["8", "9", "A"] or length[0] == 1:
								dur = int(position[1] / 90000)
								remaining = "%02d:%02d:%02d" % (dur / 3600, dur % 3600 / 60, dur % 3600 % 60) if dur > 3600 else "%02d:%02d" % (dur / 60, dur % 60)
							else:
								rem = int((length[1] - position[1]) / 90000)
								remaining = "+%02d:%02d" % (rem / 60, rem % 60) if length[1] / 90000 < 600 else "%+d%s" % ((rem / 60), Minutes)
							w, h = getFsize(remaining, font)
							if ConfigType[0] in ["2", "8"]:
								ProgressBar -= (w + 10)
								Minus = 0
								MinusProgress = 0
							elif ConfigType[0] in ["6", "A"]:
								Minus = -(ConfigSize - 2 + int((h - ConfigSize) / 2))
								MinusProgress = (w + 10)
							else:
								Minus = int(h / 1.5) + 2
								MinusProgress = (w + 10)
							if ConfigBorder == "off":
								ProgressBar = MinusProgress = 0
								POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w + 10)
							ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
						elif ConfigType[0] in ["3", "5", "7"]:
							remaining = "%d%s" % (int(position[1] * 100 / length[1]), Prozent)
							w, h = getFsize(remaining, font)
							if ConfigType.startswith("3"):
								ProgressBar -= (w + 10)
								Minus = 0
								MinusProgress = 0
							elif ConfigType.startswith("7"):
								Minus = -(ConfigSize - 2 + int((h - ConfigSize) / 2))
								MinusProgress = (w + 10)
							else:
								Minus = int(h / 1.5) + 2
								MinusProgress = (w + 10)
							if ConfigBorder == "off":
								ProgressBar = MinusProgress = 0
								POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w + 10)
							ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
						elif ConfigType[0] in ["B"]:
							dur = int(position[1] / 90000)
							remaining = "%02d:%02d" % (dur / 3600, dur % 3600 / 60) if dur > 3600 else "%02d:%02d" % (dur / 60, dur % 60)
							dur = int((length[1]) / 90000)
							remaining += " / %02d:%02d:%02d" % (dur / 3600, dur % 3600 / 60, dur % 3600 % 60) if dur > 3600 else " / %02d:%02d" % (dur / 60, dur % 60)
							w, h = getFsize(remaining, font)
							Minus = int(h / 1.5) + 2
							MinusProgress = (w + 10)
							ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
							remaining = "%d%s" % (int(position[1] * 100 / length[1]), Prozent)
							ShadowText(draw, POSX + 10, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
						elif ConfigType[0] in ["C"]:
							dur = int((length[1] - position[1]) / 90000)
							durtime = datetime.now() + timedelta(seconds=dur)
							remaining = "%02d:%02d" % (durtime.hour, durtime.minute)
							w, h = getFsize(remaining, font)
							ProgressBar -= (w + 10)
							Minus = 0
							MinusProgress = 0
							if ConfigBorder == "off":
								ProgressBar = MinusProgress = 0
								POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w + 10)
							ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
						elif ConfigType[0] in ["D"]:
							dur = int(position[1] / 90000)
							remaining1 = "%02d:%02d%s" % (dur / 60, dur % 60, Minutes)
							dur = int((length[1]) / 90000)
							dur1 = int((length[1] - position[1]) / 90000)
							durtime = datetime.now() + timedelta(seconds=dur1)
							remaining = "%02d:%02d / %02d:%02d" % (dur / 3600, dur % 3600 / 60, durtime.hour, durtime.minute)
							w, h = getFsize(remaining, font)
							Minus = int(h / 1.5) + 2
							MinusProgress = (w + 10)
							ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
							ShadowText(draw, POSX + 10, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining1, font, ConfigColorText, ConfigShadow)
						event_run = int(ProgressBar * position[1] / length[1])
						isData = True
				except Exception:
					L4log("Error put Progress")
			else:  # DVB
				event_begin, event_end, duration, event_name = self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0
				if event_begin != 0:
					now = int(time())
					event_run = now - event_begin
					if ConfigType[0] in ["2", "4", "6", "8", "9", "A"]:
						dur = int(event_run / 60)
						if ConfigType[0] in ["8", "9", "A"]:
							remaining = "%02d:%02d:%02d" % (dur / 3600, dur % 3600 / 60, dur % 3600 % 60) if dur > 3600 else "%02d:%02d" % (dur / 60, dur % 60)
						else:
							remaining = "%+d%s" % (int((event_end - now) / 60), Minutes)
						w, h = getFsize(remaining, font)
						if ConfigType[0] in ["2", "8"]:
							ProgressBar -= (w + 10)
							Minus = 0
							MinusProgress = 0
						elif ConfigType[0] in ["6", "A"]:
							Minus = -(ConfigSize - 2 + int((h - ConfigSize) / 2))
							MinusProgress = (w + 10)
						else:
							Minus = int(h / 1.5) + 2
							MinusProgress = (w + 10)
						if ConfigBorder == "off":
							ProgressBar = MinusProgress = 0
							POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w + 10)
						ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
					elif ConfigType[0] in ["3", "5", "7"]:
						remaining = "%d%s" % (int(event_run * 100 / duration), Prozent)
						w, h = getFsize(remaining, font)
						if ConfigType.startswith("3"):
							ProgressBar -= (w + 10)
							Minus = 0
							MinusProgress = 0
						elif ConfigType.startswith("7"):
							Minus = -(ConfigSize - 2 + int((h - ConfigSize) / 2))
							MinusProgress = (w + 10)
						else:
							Minus = int(h / 1.5) + 2
							MinusProgress = (w + 10)
						if ConfigBorder == "off":
							ProgressBar = MinusProgress = 0
							POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w + 10)
						ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
					elif ConfigType[0] in ["B"]:
						dur = int(event_run / 60)
						remaining = "%02d:%02d:%02d" % (dur / 3600, dur % 3600 / 60, dur % 3600 % 60) if dur > 3600 else "%02d:%02d" % (dur / 60, dur % 60)
						dur = int(duration / 60)
						remaining += " / %02d:%02d:%02d" % (dur / 3600, dur % 3600 / 60, dur % 3600 % 60) if dur > 3600 else " / %02d:%02d" % (dur / 60, dur % 60)
						w, h = getFsize(remaining, font)
						Minus = int(h / 1.5) + 2
						MinusProgress = (w + 10)
						ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
						remaining = "%d%s" % (int(event_run * 100 / duration), Prozent)
						ShadowText(draw, POSX + 10, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
					elif ConfigType[0] in ["C"]:
						dur = int(event_run / 60)
						dur2 = int(duration / 60)
						dur1 = dur2 - dur
						durtime = datetime.now() + timedelta(minutes=dur1)
						remaining = "%02d:%02d" % (durtime.hour, durtime.minute)
						w, h = getFsize(remaining, font)
						ProgressBar -= (w + 10)
						Minus = 0
						MinusProgress = 0
						if ConfigBorder == "off":
							ProgressBar = MinusProgress = 0
							POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w + 10)
						ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
					elif ConfigType[0] in ["D"]:
						dur = int(event_run / 60)
						if dur > 3600:
							remaining1 = "%02d:%02d:%02d%s" % (dur / 3600, dur % 3600 / 60, dur % 3600 % 60, Minutes)
						else:
							remaining1 = "%02d:%02d%s" % (dur / 60, dur % 60, Minutes)
						dur2 = int(duration / 60)
						dur1 = dur2 - dur
						if dur > 3600:
							durtime = datetime.now() + timedelta(seconds=dur1)
							remaining = "%02d:%02d / %02d:%02d" % (dur2 / 3600, dur2 % 3600 / 60, durtime.hour, durtime.minute)
						else:
							durtime = datetime.now() + timedelta(minutes=dur1)
							remaining = "%02d:%02d / %02d:%02d" % (dur2 / 60, dur2 % 60, durtime.hour, durtime.minute)
						w, h = getFsize(remaining, font)
						Minus = int(h / 1.5) + 2
						MinusProgress = (w + 10)
						ShadowText(draw, ProgressBar - MinusProgress + 15 + POSX, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining, font, ConfigColorText, ConfigShadow)
						ShadowText(draw, POSX + 10, ConfigPos + 1 - Minus - int((h - ConfigSize) / 2), remaining1, font, ConfigColorText, ConfigShadow)
					event_run = 0 if duration == 0 else int(ProgressBar * event_run / duration)
					isData = True
			if isData == True and ConfigBorder != "off":
				event_run = min(max(event_run, 0), ProgressBar)
				if ConfigBorder[:4] == "true":
					self.draw[draw].rectangle((POSX + 9, ConfigPos, POSX + ProgressBar + 11, ConfigPos + ConfigSize), outline=ConfigColor)
					if ConfigBorder == "true2":
						self.draw[draw].rectangle((POSX + 10, ConfigPos + 1, POSX + ProgressBar + 10, ConfigPos + ConfigSize - 1), outline=ConfigColor)
				elif ConfigBorder == "line":
					self.draw[draw].rectangle((POSX + 10, ConfigPos + int(ConfigSize / 2) - 1, POSX + ProgressBar + 10, ConfigPos + int(ConfigSize / 2) + 1), outline=ConfigColor, fill=ConfigColor)
				self.draw[draw].rectangle((POSX + 10, ConfigPos, POSX + event_run + 10, ConfigPos + ConfigSize), fill=ConfigColor)
				if ConfigShadowBar == "true":
					if isfile(join(LCD4data, "progress.png")):
						try:
							imW = Image.open(join(LCD4data, "progress.png"))
							imW = imW.resize((event_run, ConfigSize))
							self.im[im].paste(imW, (POSX + 10, ConfigPos), imW)
						except Exception:
							L4log("Progress Shade Error")
				elif ConfigShadowBar == "gradient":
					if isfile(join(LCD4data, "gradient.png")):
						if ConfigBorder == "line":
							self.draw[draw].rectangle((POSX + 10, ConfigPos + int(ConfigSize / 2) - 1, POSX + ProgressBar + 10, ConfigPos + int(ConfigSize / 2) + 1), outline="yellow", fill="yellow")
						try:
							imW = Image.open(join(LCD4data, "gradient.png"))
							imW = imW.resize((ProgressBar, ConfigSize))
							imW = imW.crop((0, 0, event_run, ConfigSize))
							self.im[im].paste(imW, (POSX + 10, ConfigPos))
						except Exception:
							L4log("Progress Gradient Error")
					if ConfigBorder == "true":
						self.draw[draw].rectangle((POSX + 9, ConfigPos, POSX + ProgressBar + 11, ConfigPos + ConfigSize), outline="yellow")

# Popup Text
	def putPopup(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		writeMultiline(PopText[1].replace("\r", ""), ConfigSize, ConfigPos, 10, ConfigColor, ConfigAlign, False, draw, im, ConfigFont=ConfigFont, ConfigBackColor=ConfigBackColor)
		writeMultiline(PopText[0], int(ConfigSize / 2.5), ConfigPos - int(ConfigSize / 2.5), 1, ConfigColor, ConfigAlign, False, draw, im, ConfigFont=ConfigFont, ConfigBackColor=ConfigBackColor)

# Volume
	def putVol(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		else:
			MAX_W -= 20
		ProgressBar = getProgess(MAX_W - ConfigSize, ConfigProzent)
		if len(str(ConfigAlign)) > 1:
			ProgressBar -= getSplit(ConfigSplit, ConfigAlign, MAX_W - ConfigSize, ProgressBar)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W - ConfigSize, ProgressBar)
		vol = self.Lvol
		if vol is not None:
			font = ImageFont.truetype(FONT, int(ConfigSize * 1.4), encoding='unic')
			w, h = getFsize(str(vol), font)
			ProgressBar -= (w + 10)
			self.draw[draw].text((ProgressBar + 15 + POSX + ConfigSize, ConfigPos - (h - ConfigSize) / 2), str(vol), font=font, fill=ConfigColor)
			self.draw[draw].rectangle((POSX + 9 + ConfigSize, ConfigPos, POSX + ConfigSize + ProgressBar + 11, ConfigPos + ConfigSize), outline=ConfigColor)
			self.draw[draw].rectangle((POSX + 10 + ConfigSize, ConfigPos, POSX + ConfigSize + int(ProgressBar * vol / 100) + 10, ConfigPos + ConfigSize), fill=ConfigColor)
			if ConfigShadow == True and isfile(join(LCD4data, "progress.png")):
				try:
					imW = Image.open(join(LCD4data, "progress.png"))
					imW = imW.resize((int(ProgressBar * vol / 100), ConfigSize))
					self.im[im].paste(imW, (POSX + 10 + ConfigSize, ConfigPos), imW)
				except Exception:
					L4log("Vol Shade Error")
			pil_image = Image.open(join(LCD4data, "speaker.png"))
			pil_image = pil_image.resize((ConfigSize + 1, ConfigSize + 1))
			if LCD4linux.PiconTransparenz.value == "2":
				pil_image = pil_image.convert("RGBA")
				self.im[im].paste(pil_image, (POSX + 5, ConfigPos), pil_image)
			else:
				self.im[im].paste(pil_image, (POSX + 5, ConfigPos))

# Provider
	def putProv(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigType, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		POSX = 0
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		if self.Lprovider is not None:
			provider = self.Lprovider
			L4logE("Provider", provider)
			if ConfigType == "2":
				picon = join(LCD4linux.ProvPath.value, "%s.png" % provider.upper())
				if isfile(picon):
					pic = picon
				elif isfile(join(LCD4linux.ProvPath.value, "picon_default.png")):
					pic = join(LCD4linux.ProvPath.value, "picon_default.png")
				else:
					pic = ""
				try:
					if pic != "":
						imW = Image.open(pic)
						xx, yy = imW.size
						CS = int(ConfigSize * 1.5)
						x = int(float(CS) / yy * xx)
						imW = imW.resize((x, CS))
						POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
						if str(LCD4linux.PiconTransparenz.value) == "2":
							imW = imW.convert("RGBA")
							self.im[im].paste(imW, (POSX, ConfigPos), imW)
						else:
							self.im[im].paste(imW, (POSX, ConfigPos))
				except Exception:
					pass
			else:
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				w, h = getFsize(provider, font)
				lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
				ShadowText(draw, lx, ConfigPos, provider, font, ConfigColor, ConfigShadow)

# Satellit
	def putSat(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigType, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		POSX = 0
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		if self.LtransponderData is not None:
			transponderData = self.LtransponderData
			orbital = "0"
			if isinstance(transponderData, float):
				L4logE("Transponder Float?")
				return
			if "tuner_type" in transponderData:
				orbital = ""
				if transponderData["tuner_type"] == "IPTV":
					orbital = transponderData["tuner_type"]
					L4logE("Orbital1", orbital)
				elif (transponderData["tuner_type"] in ("DVB-S", "DVB-S2")) or (transponderData["tuner_type"] == feSatellite):
					orbital = transponderData["orbital_position"]
					L4logE("Orbital2", orbital)
					orbital = int(orbital)
					if orbital > 1800:
						orbital = str((float(3600 - orbital)) / 10.0) + "W"
					else:
						orbital = str((float(orbital)) / 10.0) + "E"
					if ConfigType == "1":
						if len(SAT) == 0 and isfile("%stuxbox/satellites.xml" % LCD4etc):
							satXml = parse("%stuxbox/satellites.xml" % LCD4etc).getroot()
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
									SAT[position] = name
									L4logE(position, name)
						orbital = SAT.get(orbital, orbital)
						L4logE("Orbital2", orbital)
				else:
					if isinstance(transponderData["tuner_type"], int):
						orbital = {feCable: 'DVB-C', feSatellite: 'DVB-S', feTerrestrial: 'DVB-T'}.get(transponderData["tuner_type"], "-")
					else:
						orbital = transponderData["tuner_type"]
					L4logE("Orbital3", orbital)
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				w, h = getFsize(Code_utf8(orbital), font)
				piconfile = join(LCD4linux.SatPath.value, "%s.png" % str(orbital).replace(".", ""))
				if ConfigType.startswith("2") and isfile(piconfile):
					try:
						imW = Image.open(piconfile)
						xx, yy = imW.size
						CS = int(ConfigSize * 1.5)
						x = int(float(CS) / yy * xx)
						imW = imW.resize((x, CS))
						POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
						if ConfigType[1:] == "A":
							ShadowText(draw, POSX, ConfigPos + int(ConfigSize / 4), Code_utf8(orbital), font, ConfigColor, ConfigShadow)
							POSX += w
						if str(LCD4linux.PiconTransparenz.value) == "2":
							imW = imW.convert("RGBA")
							self.im[im].paste(imW, (POSX, ConfigPos), imW)
						else:
							self.im[im].paste(imW, (POSX, ConfigPos))
						if not PY3:  # no correction for PY3
							POSX += x
						if ConfigType[1:] == "C":
							ShadowText(draw, POSX, ConfigPos + int(ConfigSize / 4), Code_utf8(orbital), font, ConfigColor, ConfigShadow)
						if ConfigType[1:] == "B":
							ShadowText(draw, POSX - int((x - w) / 2), ConfigPos + CS, Code_utf8(orbital), font, ConfigColor, ConfigShadow)
					except Exception:
						pass
				else:
					lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
					ShadowText(draw, lx, ConfigPos, Code_utf8(orbital), font, ConfigColor, ConfigShadow)

# Signalstaerke Balken
	def putSignal(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigAlign, ConfigSplit, ConfigColor, ConfigGradient) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		else:
			MAX_W -= 20
		if self.LsignalQuality is not None:
			ProgressBar = getProgess(MAX_W - ConfigSize, ConfigProzent)
			if len(str(ConfigAlign)) > 1:
				ProgressBar -= getSplit(ConfigSplit, ConfigAlign, MAX_W - ConfigSize, ProgressBar)
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W - ConfigSize, ProgressBar)
			staerkeVal = int(self.LsignalQuality * 100 / 65536)
			staerkeVal2 = staerkeVal
			if staerkeVal2 < int(LCD4linux.SignalMin.value):
				staerkeVal2 = int(LCD4linux.SignalMin.value)
			elif staerkeVal2 > int(LCD4linux.SignalMax.value):
				staerkeVal2 = int(LCD4linux.SignalMax.value)
			staerke = 100 * (staerkeVal2 - int(LCD4linux.SignalMin.value)) / (int(LCD4linux.SignalMax.value) - int(LCD4linux.SignalMin.value))
			S = 2.0 if ConfigSize <= 10 else 1.4
			font = ImageFont.truetype(FONT, int(ConfigSize * S), encoding='unic')
			w, h = getFsize(str(staerkeVal), font)
			ProgressBar -= (w + 10)
			self.draw[draw].text((ProgressBar + 15 + POSX, ConfigPos - (h - ConfigSize) / 2), str(staerkeVal), font=font, fill=ConfigColor)
			if ConfigGradient == True:
				if isfile(join(LCD4data, "gradient.png")):
					try:
						imW = Image.open(join(LCD4data, "gradient.png"))
						imW = imW.resize((ProgressBar, ConfigSize))
						imW = imW.transpose(Image.FLIP_LEFT_RIGHT)
						imW = imW.crop((0, 0, int(ProgressBar * staerke / 100), ConfigSize))
						self.im[im].paste(imW, (POSX + 10, ConfigPos))
					except Exception:
						pass
				self.draw[draw].rectangle((POSX + 9, ConfigPos, POSX + ProgressBar + 11, ConfigPos + ConfigSize), outline="yellow")
			else:
				self.draw[draw].rectangle((POSX + 9, ConfigPos, POSX + ProgressBar + 11, ConfigPos + ConfigSize), outline=ConfigColor)
				self.draw[draw].rectangle((POSX + 10, ConfigPos, POSX + int(ProgressBar * staerke / 100) + 10, ConfigPos + ConfigSize), fill=ConfigColor)

# aktive Event
	def putProg(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigLines, ConfigType, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		event_begin, event_end, duration, event_name = self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0
		if event_begin != 0:
			begin = strftime("%H:%M", localtime(event_begin))
			ende = strftime("%H:%M", localtime(event_end))
			sts = ""
			if ConfigType in ["1", "3"]:
				sts = begin + " - " + ende
				if ConfigType == "3":
					now = int(time())
					sts += "  (%+d min)" % int((event_end - now) / 60)
				sts += "\n" if int(ConfigLines) != 1 else " "
			sts += event_name
			writeMultiline(sts, ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, draw, im, ConfigFont=ConfigFont, Shadow=ConfigShadow, Width=getProgess(MAX_W, ConfigProzent))

# next Event
	def putProgNext(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigLines, ConfigType, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		if ConfigType == "4":
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			POSY = ConfigPos
			POSX = 0
			Progess = getProgess(MAX_W, ConfigProzent)
			if ConfigAlign == "0":
				POSX = 0
			elif ConfigAlign == "1":
				POSX = int(MAX_W / 4)
			elif ConfigAlign == "2":
				POSX = int(MAX_W / 2)
			else:
				POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, Progess)
			sts = ""
			if self.LEventsNext is not None and len(self.LEventsNext) > 0:
				L4logE("EPG-Laenge ", "%s" % len(self.LEventsNext))
				lines = 1
				while lines <= int(ConfigLines) and lines < len(self.LEventsNext):
					if self.LEventsNext[lines][4]:
						t = self.LEventsNext[lines][2]
						event_name = Code_utf8(self.LEventsNext[lines][4])
						event_begin = t
						begin = strftime("%H:%M", localtime(event_begin))
						sts = "%s %s" % (begin, event_name)
						w, h = getFsize(sts, font)
						ShadowText(draw, POSX, POSY, cutText(sts, draw, font, Progess), font, ConfigColor, ConfigShadow)
						POSY += h
					lines += 1
		else:
			event_begin, event_end, duration, event_name = self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1
			if event_begin != 0:
				begin = strftime("%H:%M", localtime(event_begin))
				ende = strftime("%H:%M", localtime(event_end))
				sts = ""
				if ConfigType in ["1", "3"]:
					sts = begin
					if ConfigType == "1":
						sts += " - " + ende
					elif ConfigType == "3":
						sts += " (%d min)" % int((event_end - event_begin) / 60)
					sts += "\n" if int(ConfigLines) != 1 else " "
				sts += event_name
				writeMultiline(sts, ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, draw, im, ConfigFont=ConfigFont, Shadow=ConfigShadow, Width=getProgess(MAX_W, ConfigProzent))

# show extended Description
	def putDescription(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, ConfigType, ConfigShadow, ConfigInfo, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		event_name = ""
		if self.LEventsDesc is not None and len(self.LEventsDesc) > 0:
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
		if self.LsreftoString is not None and event_name == "":
			sreffile = self.LsrefFile
			datei = "%s.txt" % splitext(sreffile)[0]
			if sreffile[:1] == "/" and isfile(datei):
				try:
					event_name = open(datei, "r").readline().strip()
				except Exception:
					L4logE("Error Desc txt file")
		if ConfigMode == True and event_name == "":
			for i in range(1, 21):
				event_name += "Description%d\n" % i
		if event_name == "":
			if ConfigInfo:
				putComm((ConfigPos, ConfigSize, ConfigProzent, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont), draw, im)
		else:
			writeMultiline(event_name.replace("\x8A", "\n"), ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, draw, im, ConfigFont=ConfigFont, Shadow=ConfigShadow, Width=getProgess(MAX_W, ConfigProzent))

# Tuner
	def putTuner(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType, ConfigActive, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		number = -1
		if self.Ltuner_number is not None:
			number = self.Ltuner_number
		Tcount = 0
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		w, h = getFsize("A ", font)
		if ConfigType == "2":
			lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
		else:
			if ConfigActive == True:
				count = 1
				for x in range(TunerCount):
					if TunerMask & count != 0:
						Tcount += 1
					count *= 2
			else:
				Tcount = TunerCount
			if ConfigType == "1":
				Tcount = int(round(Tcount / 2.))
			lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, int(w * Tcount))
		if ConfigAlign == "0":
			w1, h1 = getFsize(" ", font)
			lx += w1
		ly = ConfigPos
		lxS = lx
		TcountS = Tcount
		Tcount = 0
		count = 1
		for x in range(TunerCount):
			isON = True
			if TunerMask & count != 0:
				c = LCD4linux.TunerColorActive.value if x == number else LCD4linux.TunerColorOn.value
			else:
				c = LCD4linux.TunerColor.value
				isON = False
			Tcount += 1
			count *= 2
			w1, h1 = getFsize("A", font)
			if isON:
				self.draw[draw].rectangle((lx - 1, ly, lx + w1, ly + h1), outline=c, fill="black")
			if (ConfigActive == True and isON) or ConfigActive == False:
				self.draw[draw].text((lx, ly), chr(ord('A') + x), font=font, fill=c)
				if ConfigType == "1" and TcountS == Tcount:
					ly += h + 1
					lx = lxS
				elif ConfigType == "2":
					ly += h + 1
				else:
					lx += w

# TunerInfo + Sensors
	def putInfo(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigLines, ConfigSplit, ConfigColor, ConfigInfo, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)

		def NL(count):
			return "\n" if int(count) > 2 else ""
		global CPUtotal
		global CPUidle
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		i = ""
		if self.LsignalQualitydB is not None:
			if "A" in ConfigInfo:
				if self.LsignalQualitydB > 0:
					i += " %3.02fdB%s" % (self.LsignalQualitydB / 100.0, NL(ConfigLines))
				else:
					i += " %s" % (NL(ConfigLines))
			if "B" in ConfigInfo:
				i += " %d%%%s" % (self.LsignalQuality * 100 / 65536, NL(ConfigLines))
			if "C" in ConfigInfo:
				i += " %d%s" % (self.LbitErrorRate, NL(ConfigLines))
		if "T" in ConfigInfo and self.Temp != "":
			i += " %d°C%s" % (SensorRead(self.Temp, True), NL(ConfigLines))
		if "R" in ConfigInfo:
			if isfile("/proc/stb/fp/fan_speed"):
				value = SensorRead("/proc/stb/fp/fan_speed")
				i += " %drpm%s" % (int(value / 2), NL(ConfigLines))
		elif "r" in ConfigInfo and isfile("/proc/stb/fp/fan_speed"):
			value = SensorRead("/proc/stb/fp/fan_speed")
			i += " %drpm%s" % (int(value), NL(ConfigLines))
		if "P" in ConfigInfo and isfile("/proc/stat"):
			v = open("/proc/stat", "r").readline().split()
			if len(v) > 4:
				w = int(v[1]) + int(v[2]) + int(v[3]) + int(v[4])
				wa = w - CPUtotal
				wi = int(v[4]) - CPUidle
				x = 100 - 100.0 / wa * wi if wa * wi > 0 else 0
				i += " %d%%%s" % (round(x), NL(ConfigLines))
				CPUtotal = w
				CPUidle = int(v[4])
		if "L" in ConfigInfo and isfile("/proc/loadavg"):
			v = open("/proc/loadavg", "r").readline().split()
			i += " %s%s" % (v[int(ConfigInfo[ConfigInfo.find("L") + 1])], NL(ConfigLines))
		writeMultiline(i, ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, draw, im, False, ConfigFont=ConfigFont, Shadow=ConfigShadow)

# Audio/Video
	def putAV(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigType, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		if self.LsVideoWidth is not None and self.LsVideoHeight is not None:
			dat = "audio/picon_default.png"
			if self.Laudiodescription is not None:
				try:
					dat = getAudio(self.Laudiodescription)
				except ImportError:
					pass
			Video = "%dx%d" % (self.LsVideoWidth, self.LsVideoHeight)
			if len(Video) < 6:
				Video = ""
			font = ImageFont.truetype(ConfigFont, ConfigSize - 2, encoding='unic')
			w, h = getFsize(Video, font)
			px = 75.0 / ConfigSize
			cl = int(375 / px) + 15
			if ConfigType == "1":
				cl += w
			lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, cl)
			pil_image = None
			if isfile(join(LCD4data, dat)):
				pil_image = Image.open(LCD4data + dat)
				pil_image = pil_image.resize((int(200 / px), ConfigSize))
				self.im[im].paste(pil_image, (lx, ConfigPos))
			try:
				if self.LsAspect in (3, 4, 7, 8, 0xB, 0xC, 0xF, 0x10):
					pil_image = Image.open(join(LCD4data, "widescreen.png"))
				else:
					pil_image = Image.open(join(LCD4data, "letterbox.png"))
				pil_image = pil_image.resize((int(100 / px), ConfigSize))
				self.im[im].paste(pil_image, (lx + int(200 / px) + 5, ConfigPos))
			except Exception:
				L4log("Error Aspect")
			try:
				if self.LsIsCrypted == 1:
					pil_image = Image.open(join(LCD4data, "crypted.png"))
				else:
					pil_image = Image.open(join(LCD4data, "open.png"))
				pil_image = pil_image.resize((ConfigSize, ConfigSize))
				self.im[im].paste(pil_image, (lx + int(300 / px) + 10, ConfigPos))
			except Exception:
				L4log("Error Crypted")
			pil_image = None
			if ConfigType == "1":
				Posx = int(375 / px) + 15
				Posy = ConfigPos + 2
			else:
				Posx = (int(375 / px / 2)) - int(w / 2)
				Posy = ConfigPos + ConfigSize
			ShadowText(draw, lx + Posx, Posy, Video, font, ConfigColor, ConfigShadow)

# Bitrate
	def putBitrate(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		if self.LaudioBitrate != "" and self.LvideoBitrate != "":
			BIT = "{: =5d} | {: =5d} kbit/s".format(self.LvideoBitrate, self.LaudioBitrate)
			w, h = getFsize(BIT, font)
			lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, w)
			ShadowText(draw, lx, ConfigPos, BIT, font, ConfigColor, ConfigShadow)
		elif BitrateRegistred == False:
			ShadowText(draw, 0, ConfigPos, "no Bitrate-Plugin", font, ConfigColor, ConfigShadow)

# Online-Ping
	def putOnline(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigType, ConfigShow, ConfigTimeout, ConfigList, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		if self.NetworkConnectionAvailable or self.NetworkConnectionAvailable is None:
			if OSDtimer < 0:
				return
			MAX_W, MAX_H = self.im[im].size
			if ConfigSplit == True:
				MAX_W = int(MAX_W / 2)
			font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
			cl = 0
			cm = 0
			h = 0
			for l in ConfigList:
				if len(l) > 1:
					T = (Code_utf8(l) + ":").split(":")
					w, h = getFsize(T[0], font)
					if cm < w:
						cm = w
					cl += (h + 10 + w)
			if ConfigType == "2":
				cl = cm + 10 + h
			ly = ConfigPos
			lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, cl)
			for l in ConfigList:
				if len(l) > 1:
					T = (Code_utf8(l) + ":").split(":")
					TT = T[1] if len(T[1]) > 0 else T[0]
					w, h = getFsize(T[0], font)
					c = "red"
					r = None
					try:
						r = quiet_ping(TT, int(ConfigTimeout))
						if (r and r[2] > 0.0) and r[2] <= float(ConfigTimeout):
							c = "lime"
						if ConfigShow == "0" or (ConfigShow == "1" and c == "lime") or (ConfigShow == "2" and c == "red"):
							self.draw[draw].ellipse((lx + 2, ly + 2, lx + h - 2, ly + h - 2), fill=c)
							ShadowText(draw, lx + h + 5, ly, T[0], font, ConfigColor, ConfigShadow)
							if ConfigType == "2":
								ly += h
						if ConfigType == "0":
							lx += (h + 10 + w)
					except Exception:
						L4log("Ping-Error", TT)

# www Remote Box
	def putRemoteBox(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigProzent, ConfigShow, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)

		def getColor(c):
			return ConfigColor[0] if ConfigColor[c] == "0" else ConfigColor[c]
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		POSY = ConfigPos
		wwwBcount = 0
		for wwwB in self.wwwBox:
			if len(wwwB) > 1 and (len(wwwB[1]) > 1 or len(wwwB[2]) > 1):
				rr = "_".join(wwwB[1].split(":")[:10])
				POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, int(MAX_W / 2))
				CS = int(ConfigSize * 3)
				x = 0
				if "P" in ConfigShow:
					picon = "%s.png" % str(rr).rstrip(":")
					if isfile(join(LCD4linux.PiconPath.value, picon)):
						piconP = join(LCD4linux.PiconPath.value, picon)
					elif isfile(join(LCD4linux.PiconPathAlt.value, picon)):
						piconP = join(LCD4linux.PiconPathAlt.value, picon)
					elif isfile(join(LCD4linux.PiconPath.value, "picon_default.png")):
						piconP = join(LCD4linux.PiconPath.value, "picon_default.png")
					else:
						piconP = ""
					if piconP != "":
						try:
							imW = Image.open(piconP)
							xx, yy = imW.size
							x = int(float(CS) / yy * xx)
							imW = imW.resize((x, CS))
							POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
							if str(LCD4linux.PiconTransparenz.value) == "2":
								imW = imW.convert("RGBA")
								self.im[im].paste(imW, (POSX, POSY), imW)
							else:
								self.im[im].paste(imW, (POSX, POSY))
						except Exception:
							pass
				y = 0
				MaxLen = int(MAX_W * int(ConfigProzent) / 100) - x
				if len(wwwB[0]) > 0:
					if "P" in ConfigShow:
						ShadowText(draw, POSX + x, POSY, Code_utf8(wwwB[0]), font, getColor(wwwBcount), ConfigShadow)
						y += ConfigSize
					else:
						w, h = getFsize(Code_utf8(wwwB[0]), font)
						self.draw[draw].rectangle((POSX + x, POSY, POSX + x + w, POSY + h), fill=getColor(wwwBcount))
						ShadowText(draw, POSX + x, POSY, Code_utf8(wwwB[0]), font, "black", False)
						y += ConfigSize
				if "C" in ConfigShow:
					ShadowText(draw, POSX + x, POSY + y, cutText(Code_utf8(wwwB[2]), draw, font, MaxLen), font, getColor(wwwBcount), ConfigShadow)
					y += ConfigSize
				if "T" in ConfigShow:
					ShadowText(draw, POSX + x, POSY + y, cutText(Code_utf8(wwwB[3]), draw, font, MaxLen), font, getColor(wwwBcount), ConfigShadow)
					y += ConfigSize
				if "P" in ConfigShow:
					POSY += CS
				else:
					POSY += y
			wwwBcount += 1

# Data-Devices
	def putDev(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigColor, ConfigList, ConfigShadow, ConfigType, ConfigWarning, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		global DeviceRemove
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		w, h = getFsize("MByte", font)
		if ConfigType == "0":
			co = 0
			for l in ConfigList:
				if len(l) > 0:
					co += 1
		else:
			co = 1
		ly = ConfigPos
		lx = getSplit(ConfigSplit, ConfigAlign, MAX_W, (w + 20) * co)
		Bproz = 0
		for l in ConfigList:
			if l not in DeviceRemove and (isdir(l) == True or l[:3] == "RAM"):
				L4logE("Device", l)
				G = F = B = B1pixel = B2pixel = 0
				if l[:3] == "RAM":
					G, F, B = getMem()
					Bproz = int(F * 100 / G) if F > 0 else 0
					B1pixel = ((2 * h) * Bproz / 100)
					Bproz = int(B * 100 / G) if B > 0 else 0
					B2pixel = ((2 * h) * Bproz / 100)
					if l == "RAM2":
						F += B
				else:
					try:
						s = statvfs(l)
						G = s.f_bsize * s.f_blocks
						F = s.f_bsize * s.f_bavail
						if G == 0 and LCD4linux.DevForceRead.value == True:
							L4logE("Device force Reading")
							glob(normpath(l) + "/*")
							s = statvfs(l)
							G = s.f_bsize * s.f_blocks
							F = s.f_bsize * s.f_bavail
					except Exception:
						L4log("Error Device", l)
				if G > 0:
					Fproz = int(F * 100 / G) if F > 0 else 0
					Fpixel = ((2 * h) * Fproz / 100)
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
					ShadowText(draw, lx + 20, ly, "%.1f" % Fe, font, ConfigColor, ConfigShadow)
					ShadowText(draw, lx + 20, ly + h, "%sB" % Einh, font, ConfigColor, ConfigShadow)
					self.draw[draw].rectangle((lx + 8, ly, lx + 18, ly + (2 * h)), outline=LCD4linux.DevBarColor.value, fill=LCD4linux.DevFullColor.value if (Fproz < int(ConfigWarning) and l[:3] != "RAM") else LCD4linux.DevBarColor.value)
					if l[:3] == "RAM":
						self.draw[draw].rectangle((lx + 8, ly, lx + 18, ly + B1pixel), outline=LCD4linux.DevBackColor.value, fill=LCD4linux.DevBackColor.value)
						self.draw[draw].rectangle((lx + 8, ly + B1pixel, lx + 14, ly + B1pixel + B2pixel), outline=LCD4linux.DevBackColor.value, fill=LCD4linux.DevBackColor.value)
					else:
						self.draw[draw].rectangle((lx + 8, ly, lx + 18, ly + Fpixel), outline=LCD4linux.DevBackColor.value, fill=LCD4linux.DevBackColor.value)
					lx += w + 20 if ConfigType == "0" else 2 * h + 3
				else:
					L4log("remove Device", l)
					DeviceRemove.append(l)
			else:
				if l not in DeviceRemove:
					L4log("remove Device", l)
					DeviceRemove.append(l)

# HDD
	def putHdd(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		hddsleep = True
		if harddiskmanager.HDDCount() > 0:
			for hdd in harddiskmanager.HDDList():
				L4logE(hdd[0])
				L4logE(hdd[1].model(), hdd[1].isSleeping())
				hddbus = hdd[1].bus_description() if hasattr(hdd[1], "bus_description") else ""
				if hdd[1].model().startswith("ATA") or hdd[1].model().startswith("SATA") or hddbus == "SATA":
					if not hdd[1].isSleeping():
						hddsleep = False
			try:
				if ConfigType == "0" or (ConfigType == "1" and hddsleep == False):
					imW = Image.open(join(LCD4data, "HDDs.png")) if hddsleep == True else Image.open(join(LCD4data, "HDDa.png"))
					xx, yy = imW.size
					x = int(float(ConfigSize) / yy * xx)
					imW = imW.resize((x, ConfigSize))
					POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
					if str(LCD4linux.PiconTransparenz.value) == "2":
						imW = imW.convert("RGBA")
						self.im[im].paste(imW, (POSX, ConfigPos), imW)
					else:
						self.im[im].paste(imW, (POSX, ConfigPos))
			except Exception:
				pass

# Mute
	def putMute(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		try:
			if self.LvolM == True:
				MAX_W, MAX_H = self.im[im].size
				if ConfigSplit == True:
					MAX_W = int(MAX_W / 2)
				imW = Image.open(join(LCD4data, "audio/audio_off.png"))
				xx, yy = imW.size
				x = int(float(ConfigSize) / yy * xx)
				imW = imW.resize((x, ConfigSize))
				POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
				if str(LCD4linux.PiconTransparenz.value) == "2":
					imW = imW.convert("RGBA")
					self.im[im].paste(imW, (POSX, ConfigPos), imW)
				else:
					self.im[im].paste(imW, (POSX, ConfigPos))
		except Exception:
			pass

# show OSCAM
	def putOSCAM(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigSplit) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		OSCAMrunning = False
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, MAX_W)
		if isfile(LCD4linux.OSCAMFile.value):
			current_h = ConfigPos
			if time() - getmtime(LCD4linux.OSCAMFile.value) < 30:
				OSCAMrunning = True
				font = ImageFont.truetype(FONT, ConfigSize, encoding='unic')
				for line in open(LCD4linux.OSCAMFile.value, "r").readlines():
					line = Code_utf8(line.replace('\n', ''))
					w, h = getFsize(line, font)
					if ConfigBackColor != "0":
						if line.find(" Label ") > 0:
							self.draw[draw].rectangle((POSX, current_h, POSX + MAX_W, current_h + h), fill=ConfigColor)
						else:
							self.draw[draw].rectangle((POSX, current_h, POSX + MAX_W, current_h + h), fill=ConfigBackColor)
					if "|" in line:
						ll = line.split("|")
						if len(ll) == 4:
							p = [160, 10.67, 2.91, 1.14, 1.03]
						elif len(ll) == 5:
							p = [160, 10.67, 2.91, 1.78, 1.14, 1.03]
						else:
							p = [160, 10.67, 2.91, 1.78, 1.6, 1.45, 1.33, 1.14, 1.03]
						for x in range(len(ll)):
							if line.find(" Label ") > 0 and ConfigBackColor != "0":
								self.draw[draw].text((POSX + int(MAX_W / p[x]), current_h), ll[x].strip(), font=font, fill=ConfigBackColor)
							else:
								self.draw[draw].text((POSX + int(MAX_W / p[x]), current_h), ll[x].strip(), font=font, fill=ConfigColor)
						current_h += h
		if OSCAMrunning == False:
			font = ImageFont.truetype(FONT, ConfigSize + 13, encoding='unic')
			w, h = getFsize(Code_utf8(_("OSCAM not running")), font)
			if ConfigBackColor != "0":
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + MAX_W, ConfigPos + h), fill=ConfigBackColor)
			self.draw[draw].text((POSX + (MAX_W - w) / 2, ConfigPos), Code_utf8(_("OSCAM not running")), font=font, fill=ConfigColor)

# show ecm.info
	def putECM(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigSplit) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		h = 0
		t = ""
		p = [[160, 8.60, 4.40, 2.53, 1.45, 1.18, 1.07], [160, 4.00, 2.00, 1.17], [160, 2.60, 1.30], [150]]
		font = None
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, MAX_W)
		if isfile("/tmp/ecm.info"):
			info = {}
			for line in open("/tmp/ecm.info", 'r').readlines():
				d = line.split(':', 1)
				if len(d) > 1:
					info[d[0].strip()] = d[1].strip()
			for idx, t in enumerate(["Caid,Pid,Reader,From,Protocol,Hops,Ecm Time", "Caid,Pid,Protocol,Ecm Time", "Caid,Pid,Ecm Time", "Ecm Time"]):
				font = ImageFont.truetype(FONT, ConfigSize, encoding='unic')
				w, h = getFsize(t.split(" ")[0], font)
				if w < MAX_W * [0.58, 0.71, 0.67, 1.00][idx]:
					p = p[idx]
					break  # font size is small enough for current infoset
			if ConfigBackColor != "0":
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + MAX_W, ConfigPos + h), fill=ConfigColor)
			for idx, text in enumerate(t.split(" ")[0].split(",")):
				if ConfigBackColor != "0" and font is not None:
					self.draw[draw].text((POSX + int(MAX_W / p[idx]), ConfigPos), text, font=font, fill=ConfigBackColor)
				else:
					self.draw[draw].text((POSX + int(MAX_W / p[idx]), ConfigPos), text, font=font, fill=ConfigColor)
			ConfigPos += h
			if ConfigBackColor != "0":
				self.draw[draw].rectangle((POSX, ConfigPos, POSX + MAX_W, ConfigPos + h), fill=ConfigBackColor)
			for idx, data in enumerate(t.split(",")):
				self.draw[draw].text((POSX + int(MAX_W / p[idx]), ConfigPos), info.get(data.lower(), ""), font=font, fill=ConfigColor)

# show Title
	def putTitle(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		Title = ""
		if self.LsreftoString is not None:
			self.LsreftoString
			sreffile = self.LsrefFile
			audio = None
			if sreffile.lower().endswith(".mp3"):
				MP3title = ""
				MP3artist = ""
				try:
					audio = MP3(sreffile, ID3=EasyID3)
				except Exception:
					audio = None
				if audio:
					MP3title = audio.get('title', [''])[0]
					MP3artist = audio.get('artist', [''])[0]
					Title = "%s - %s" % (MP3artist, MP3title)
					if len(Title) < 5:
						Title = ""
			if Title == "":
				Title = self.LgetName
				if self.LsTagTitle is not None:
					Title = self.LsTagTitle
					Video = Title.endswith(".mpg") or Title.endswith(".vob") or Title.endswith(".avi") or Title.endswith(".divx") or Title.endswith(".mv4") or Title.endswith(".mkv") or Title.endswith(".mp4") or Title.endswith(".ts")
					if Title == "" or Video == True:
						Title = self.LgetName
						Title = Title.replace(".mpg", "").replace(".vob", "").replace(".avi", "").replace(".divx", "").replace(".mv4", "").replace(".mkv", "").replace(".mp4", "").replace(".ts", "")
					if Title.find(" ") > 20 or (Title.find(" ") == -1 and len(Title) > 20):
						Title = Title.replace(".", " ")
				if ConfigMode == True:
					Title = "Title1\nTitle2 Text\nTitle3"
			writeMultiline(Title, ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, draw, im, ConfigFont=ConfigFont, Shadow=ConfigShadow, Width=getProgess(MAX_W, ConfigProzent))

# show Comments
	def putComm(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)

		def addNL(w, d):
			r = " " if " " in d else ""
			if "(" in d:
				r += "(%s)" % w if w is not None and w != "" else ""
			else:
				r += "%s" % w if w is not None and w != "" else ""
			return "%s\n" % r if "<" in d and r.strip() != "" else r
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		if self.LsTagArtist is not None:
			Info = ""
			if WebRadioFSok == True and self.l4l_info.get("Station", "") != "":
				Info += self.l4l_info.get("Station", "") + " - "
				if self.l4l_info.get("Fav", "") != "":
					Info += self.l4l_info.get("Fav", "") + " - "
			if isMediaPlayer == "record":
				event_begin, event_end, duration, event_name = self.Levent_begin0, self.Levent_end0, self.Lduration0, self.Levent_name0
				Info += "%s " % self.Lcommand
				if event_begin != 0:
					if isMediaPlayer == "record":
						Info += strftime("%d.%m.%G ", localtime(event_begin))
					Info += strftime("%H:%M ", localtime(event_begin))
					if self.Llength is not None:
						length = self.Llength
						if length[1] > 0:
							duration = length[1] / 90000
						if duration > 0:
							Info += " (%d min) " % (duration / 60)
					if Info.strip() == "":
						Info += event_name + "\n"
				event_begin, event_end, duration, event_name = self.Levent_begin1, self.Levent_end1, self.Lduration1, self.Levent_name1
				if event_begin != 0:
					Info += strftime("%H:%M ", localtime(event_begin)) + event_name
			else:
				Info += addNL(self.LsTagAlbum, "")
				Info += addNL(self.LsTagDate, " (<")
				if self.Llength is not None:
					length = self.Llength
					if length[1] > 0:
						dur = length[1] / 90000
						if dur > 3600:
							Info += "%2d:%02d:%02d h\n" % (dur / 3600, dur % 3600 / 60, dur % 3600 % 60)
						else:
							Info += "%2d:%02d min\n" % (dur / 60, dur % 60)
				Info += addNL(self.LsTagArtist, "<")
			if ConfigMode == True and Info == "":
				Info = "Info1\nInfo2 Text\nInfo3"
			writeMultiline(Info, ConfigSize, ConfigPos, ConfigLines, ConfigColor, ConfigAlign, ConfigSplit, draw, im, ConfigFont=ConfigFont, Shadow=ConfigShadow, Width=getProgess(MAX_W, ConfigProzent))

# show Fritz Pictures
	def putFritzPic(workaround, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		if (len(FritzList) == 0 and ConfigMode == False) or int(LCD4linux.FritzPictures.value) == 0:
			return
		MAX_Wi, MAX_Hi = self.im[im].size
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		if isfile(PICfritz):
			try:
				pil_image = Image.open(PICfritz)
				x, y = pil_image.size
				POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
				if str(LCD4linux.FritzPictureTransparenz.value) == "2":
					pil_image = pil_image.convert("RGBA")
					self.im[im].paste(pil_image, (POSX, ConfigPos), pil_image)
				else:
					self.im[im].paste(pil_image, (POSX, ConfigPos))
			except Exception:
				pass
		elif ConfigMode == True and len(FritzList) == 0:
			imW = Image.open(FritzPic)
			xx, yy = imW.size
			x = int(float(ConfigSize) / yy * xx)
			imW = imW.resize((x, ConfigSize))
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
			if str(LCD4linux.FritzPictureTransparenz.value) == "2":
				imW = imW.convert("RGBA")
				self.im[im].paste(imW, (POSX, ConfigPos), imW)
			else:
				self.im[im].paste(imW, (POSX, ConfigPos))
		else:
			if str(LCD4linux.FritzPictureType.value) == "0":
				imW = Image.new('RGB', (MAX_Wi, ConfigSize), (0, 0, 0, 0))
			else:
				imW = Image.new('RGB', (ConfigSize, MAX_Hi), (0, 0, 0, 0))
			PX = 0
			PXmax = 0
			x = 0
			i = 0
			PY = 0
			for Fx in reversed(FritzList):
				if i < int(LCD4linux.FritzPictures.value):
					Bildname = ""
					Rufname = Fx[3].split("\n")[0].split(",")[0].strip()
					if "1" in str(LCD4linux.FritzPictureSearch.value):
						if isfile(join(LCD4linux.FritzPath.value, "%s.png" % Fx[2])):
							Bildname = join(LCD4linux.FritzPath.value, "%s.png" % Fx[2])
						elif isfile(join(LCD4linux.FritzPath.value, "%s.png" % Rufname)):
							Bildname = join(LCD4linux.FritzPath.value, "%s.png" % Rufname)
						elif isfile(join(LCD4linux.FritzPath.value, "%s.png" % Rufname.split("(")[0].strip())):
							Bildname = join(LCD4linux.FritzPath.value, "%s.png" % Rufname.split("(")[0].strip())
					if Bildname == "" and "2" in LCD4linux.FritzPictureSearch.value:
						for k in range(len(Fx[2]), 0, -1):
							picon = join(LCD4linux.FritzPath.value, "%s.png" % Fx[2][:k])
							if isfile(picon):
								Bildname = picon
								break
					if Bildname == "":
						if isfile(join(LCD4linux.FritzPath.value, "default.png")):
							pil_image = Image.open(join(LCD4linux.FritzPath.value, "default.png"))
						else:
							pil_image = Image.open(FritzPic)
					else:
						pil_image = Image.open(Bildname)
					xx, yy = pil_image.size
					x = int(float(ConfigSize) / yy * xx)
					if PXmax < x:
						PXmax = x
					pil_image = pil_image.resize((x, ConfigSize))
					if str(LCD4linux.FritzPictureTransparenz.value) == "2":
						pil_image = pil_image.convert("RGBA")
						imW.paste(pil_image, (PX, PY), pil_image)
					else:
						imW.paste(pil_image, (PX, PY))
					if str(LCD4linux.FritzPictureType.value) == "0":
						PX += x
					else:
						PY += ConfigSize
				i += 1
			if str(LCD4linux.FritzPictureType.value) == "0":
				imW = imW.crop((0, 0, max(1, min(PX, MAX_Wi)), ConfigSize))
			else:
				imW = imW.crop((0, 0, max(1, min(PXmax, ConfigSize)), max(1, min(PY, MAX_Hi))))
			imW.save(PICfritz)
			x, y = imW.size
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_Wi, x)
			if str(LCD4linux.FritzPictureTransparenz.value) == "2":
				imW = imW.convert("RGBA")
				self.im[im].paste(imW, (POSX, ConfigPos), imW)
			else:
				self.im[im].paste(imW, (POSX, ConfigPos))

# show FritzCall
	def putFritz(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigType, ConfigPicPos, ConfigPicSize, ConfigPicAlign, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if FritzTime > 1:
			if len(FritzList) == 0:
				return
			try:
				FL = FritzList[len(FritzList) - 1]
				if len(FL) < 5:
					return
				if isfile(LCD4linux.FritzFrame.value):
					pil_image = Image.open(LCD4linux.FritzFrame.value)
				else:
					pil_image = Image.open(FritzFrame)
				pil_image = pil_image.resize((MAX_W, MAX_H))
				self.im[im].paste(pil_image, (0, 0))
				Bildname = ""
				Rufname = FL[3].split("\n")[0].split(",")[0].strip()
				if "1" in str(LCD4linux.FritzPictureSearch.value):
					if isfile(join(LCD4linux.FritzPath.value, "%s.png" % FL[2])):
						Bildname = join(LCD4linux.FritzPath.value, "%s.png" % FL[2])
					elif isfile(join(LCD4linux.FritzPath.value, "%s.png" % Rufname)):
						Bildname = join(LCD4linux.FritzPath.value, "%s.png" % Rufname)
					elif isfile(join(LCD4linux.FritzPath.value, "%s.png" % Rufname.split("(")[0].strip())):
						Bildname = join(LCD4linux.FritzPath.value, "%s.png" % Rufname.split("(")[0].strip(), )
				if Bildname == "" and "2" in LCD4linux.FritzPictureSearch.value:
					for k in range(len(FL[2]), 0, -1):
						picon = join(LCD4linux.FritzPath.value, "%s.png" % FL[2][:k])
						if isfile(picon):
							Bildname = picon
							break
				if Bildname == "":
					if isfile(join(LCD4linux.FritzPath.value, "default.png")):
						pil_image = Image.open(join(LCD4linux.FritzPath.value, "default.png"))
					else:
						pil_image = Image.open(FritzRing)
				else:
					pil_image = Image.open(Bildname)
				xx, yy = pil_image.size
				x = int(float(MAX_H / 1.8) / yy * xx)
				pil_image = pil_image.resize((x, int(MAX_H / 1.8)))
				self.im[im].paste(pil_image, (int(MAX_W / 30), int((MAX_H / 2.3) - (MAX_H / 27))))
				FL3 = FL[3]
				if len(FL3.split("\n")) == 1:
					FL3 = "\n%s" % FL3
				writeMultiline2(FL3, int(MAX_H / 8), int(MAX_H / 27), 3, LCD4linux.FritzPopupColor.value, int(MAX_W / 3) - int(MAX_W / 30), int(MAX_W / 1.5), draw, im, ConfigFont=ConfigFont)
				writeMultiline2("%s\n%s\n%s" % (FL[2], FL[1], FL[4]), int(MAX_H / 11), int(MAX_H * 0.6), 3, LCD4linux.FritzPopupColor.value, int(MAX_W / 2.66) - int(MAX_W / 30), int(MAX_W / 1.6), draw, im, ConfigFont=ConfigFont)
			except Exception:
				pass
		else:
			event = []
			if int(LCD4linux.FritzLines.value) > 0:
				CS = int(ConfigSize * 1.8)
				if ConfigMode == True and len(FritzList) == 0:
					event.append(["RING", "01.01.2000 01:00", "0123/4567890", "Demo Call 1", "123"])
					event.append(["OUT", "01.01.2000 02:00", "0123/4567890", "Demo Call 2", "123"])
				POSY = ConfigPos
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				w1, h1 = getFsize("8", font)
				POSX = getSplit(False, ConfigAlign, MAX_W, (30 * w1))
				imW = None
				x1 = 0
				if isfile(join(LCD4data, "fritztelin.png")):
					try:
						imW = Image.open(join(LCD4data, "fritztelin.png"))
						xx, yy = imW.size
						x1 = int(float(CS) / yy * xx)
						imW = imW.resize((x1, CS)).convert("RGBA")
					except Exception:
						imW = None
				imW2 = None
				if isfile(join(LCD4data, "fritztelout.png")):
					try:
						imW2 = Image.open(join(LCD4data, "fritztelout.png"))
						xx, yy = imW2.size
						x1 = int(float(CS) / yy * xx)
						imW2 = imW2.resize((x1, CS)).convert("RGBA")
					except Exception:
						imW2 = None
				w1, h1 = getFsize("A", font)
				i = 0
				for FL in reversed(FritzList + event):
					if i < int(LCD4linux.FritzLines.value):
						POSXi = POSX
						if imW is not None and imW2 is not None and "-" not in ConfigType:
							if LCD4linux.WetterTransparenz.value == "true":
								if FL[0] == "RING":
									self.im[im].paste(imW, (POSX, POSY - (int(CS / 10))), imW)
								else:
									self.im[im].paste(imW2, (POSX, POSY - (int(CS / 10))), imW2)
							else:
								if FL[0] == "RING":
									self.im[im].paste(imW, (POSX, POSY - (int(CS / 10))))
								else:
									self.im[im].paste(imW2, (POSX, POSY - (int(CS / 10))))
							POSXi += x1 + w1
						if int(LCD4linux.FritzLineType.value) == 3:
							LT = "\n"
						else:
							LT = ""
						if "T" in ConfigType:
							event = "%s %s%s [%s]\n%s" % (FL[1], LT, FL[2], FL[4].split()[0], Code_utf8(FL[3].split("\n")[0]))
						else:
							event = "%s %s%s\n%s" % (FL[1], LT, FL[2], Code_utf8(FL[3].split("\n")[0]))
						for x in event.split("\n"):
							w, h = getFsize(x, font)
							if ConfigBackColor != "0":
								self.draw[draw].rectangle((POSXi, POSY, POSXi + w, POSY + h), fill=ConfigBackColor)
							ShadowText(draw, POSXi, POSY, x, font, ConfigColor, ConfigShadow)
							POSY += h
					i += 1
				if len(FritzList) == 0 and len(event) == 0 and LCD4linux.ShowNoMsg.value == True:
					ShadowText(draw, POSX, POSY, _("no Calls"), font, ConfigColor, ConfigShadow)
			Para = ConfigPicPos, ConfigPicSize, ConfigPicAlign, False
			putFritzPic(Para, im)

# show Mail
	def putMail(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigColor, ConfigBackColor, ConfigAlign, ConfigSplit, ConfigLines, ConfigType, ConfigProfil, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		h = 0
		if PopMail[5] != "":
			L4log("get Mail running")
			return
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		ConfigProfil = int(ConfigProfil)
		ConfigLines = int(ConfigLines)
		POSY = ConfigPos
		CS = int(ConfigSize * 1.8)
		CW = int(MAX_W * int(ConfigProzent) / 100)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, CW)
		Konto = [LCD4linux.Mail1User.value, LCD4linux.Mail2User.value, LCD4linux.Mail3User.value, LCD4linux.Mail4User.value, LCD4linux.Mail5User.value]
		for CP in range(0, ConfigProfil):
			if len(PopMail[CP]) > 0 or LCD4linux.MailShow0.value == True:
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				PopCheck = CP
				if len(PopMail[CP]) > 0:
					PopCheck = PopMail[CP][0][2]
				if ConfigType[:1] == "A" or (ConfigType[:1] == "B" and PopCheck != PopMailUid[CP][0]):
					NM = 0
					for e in PopMail[CP]:
						if e[2] != PopMailUid[CP][0]:
							NM += 1
						else:
							break
					Mtext = _("%d Mails  %d New  %s") % (len(PopMail[CP]), NM, Code_utf8(Konto[CP].split(":")[0]))
					POSXi = POSX
					if isfile(join(LCD4data, "email.png")):
						try:
							imW = Image.open(join(LCD4data, "email.png"))
							xx, yy = imW.size
							x = int(float(CS) / yy * xx)
							imW = imW.resize((x, CS))
							if LCD4linux.WetterTransparenz.value == "true":
								imW = imW.convert("RGBA")
								self.im[im].paste(imW, (POSX, POSY), imW)
							else:
								self.im[im].paste(imW, (POSX, POSY))
							w, h = getFsize("A", font)
							POSXi += x + w
						except Exception:
							pass
					if ConfigBackColor != "0":
						w, h = getFsize(Mtext, font)
						self.draw[draw].rectangle((POSXi, POSY, POSXi + w, POSY + h), fill=ConfigBackColor)
					ShadowText(draw, POSXi, POSY + int(h / 5), Mtext, font, ConfigColor, ConfigShadow)
					POSY += CS
				i = 1
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				c = int(ConfigSize / 4)
				for M in PopMail[CP]:
					if i >= int(ConfigLines) or (ConfigType[1:] == "2" and M[2] == PopMailUid[CP][0]):
						break
					i += 1
					self.draw[draw].ellipse((POSX, POSY + int(ConfigSize / 2) - c, POSX + (2 * c), POSY + int(ConfigSize / 2) + c), fill=ConfigColor)
					tx = cutText(Code_utf8("%s %s" % (M[0], M[3])), draw, font, CW - ConfigSize)
					if ConfigBackColor != "0":
						w, h = getFsize(tx, font)
						self.draw[draw].rectangle((POSX + ConfigSize, POSY, POSX + ConfigSize + w, POSY + h), fill=ConfigBackColor)
					ShadowText(draw, POSX + ConfigSize, POSY, tx, font, ConfigColor, ConfigShadow)
					POSY += ConfigSize
					tx = cutText(Code_utf8(M[1]), draw, font, CW - ConfigSize)
					if ConfigBackColor != "0":
						w, h = getFsize(tx, font)
						self.draw[draw].rectangle((POSX + ConfigSize, POSY, POSX + ConfigSize + w, POSY + h), fill=ConfigBackColor)
					ShadowText(draw, POSX + ConfigSize, POSY, tx, font, ConfigColor, ConfigShadow)
					POSY += ConfigSize

# show Ereignis Icon Bar
	def putIconBar(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType, ConfigPopup, ConfigPopupLCD) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		global SaveEventList
		global SaveEventListChanged
		MAX_W, MAX_H = self.im[im].size
		EVENTLIST = [[], 0, 0]
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		find = ""
		for CP in range(0, 5):
			if len(PopMail[CP]) > 0 and PopMail[CP][0][2] != PopMailUid[CP][0]:
				for e in PopMail[CP]:
					if e[2] != PopMailUid[CP][0]:
						find += "A"
						break
			if "A" in find:
				break
		EVENTLIST[0] = PopMailUid
		if ConfigMode == True and "A" not in find:
			find += "A"
		if len(FritzList) > 0:
			EVENTLIST[1] = FritzList[-1]
			find += "B"
		icount = 0
		for t in sorted(ICS):
			x = datetime.strptime(str(t), "%Y-%m-%d")
			DTx = date(x.year, x.month, x.day) - date.today()
			if (DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value))) or ConfigMode == True:
				if "C" not in find:
					find += "C"
				icount += 1
		EVENTLIST[2] = icount
		if len(find) == 0:
			return
		if SaveEventList != EVENTLIST and ConfigPopup != "0" and ICSrunning == False and PopMail[5] == "" and OSDtimer >= 0 and ConfigMode == False:
			if SaveEventList != ["", "", ""]:
				L4log("Set Event Changed", "%s" % EVENTLIST)
				for L in str(ConfigPopupLCD):
					setScreenActive(str(ConfigPopup), str(L))
			SaveEventList = EVENTLIST
		POSY = ConfigPos
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, ConfigSize * len(find) if ConfigType == "0" else ConfigSize)
		if "A" in find and isfile(join(LCD4data, "email.png")):
			try:
				imW = Image.open(join(LCD4data, "email.png"))
				imW = imW.resize((ConfigSize, ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					self.im[im].paste(imW, (POSX, POSY), imW)
				else:
					self.im[im].paste(imW, (POSX, POSY))
			except Exception:
				pass
			if ConfigType == "0":
				POSX += ConfigSize
			else:
				POSY += ConfigSize
		if "B" in find and isfile(join(LCD4data, "fritztelin.png")):
			try:
				imW = Image.open(join(LCD4data, "fritztelin.png"))
				imW = imW.resize((ConfigSize, ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					self.im[im].paste(imW, (POSX, POSY), imW)
				else:
					self.im[im].paste(imW, (POSX, POSY))
			except Exception:
				pass
			if ConfigType == "0":
				POSX += ConfigSize
			else:
				POSY += ConfigSize
		if "C" in find and isfile(join(LCD4data, "calendar.png")):
			try:
				imW = Image.open(join(LCD4data, "calendar.png"))
				imW = imW.resize((ConfigSize, ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					self.im[im].paste(imW, (POSX, POSY), imW)
				else:
					self.im[im].paste(imW, (POSX, POSY))
			except Exception:
				pass

# show Sonnenaufgang
	def putSun(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigColor, ConfigBackColor, ConfigAlign, ConfigSplit, ConfigType, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		POSY = ConfigPos
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		w, h = getFsize("%02d:%02d" % L4LSun, font)
		ww = ConfigSize + w + int(ConfigSize / 6)
		if ConfigType == "0":
			ww *= 2
			ww += int(ConfigSize / 3)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, ww)
		POSXi = POSX + ConfigSize + int(ConfigSize / 6)
		if isfile(join(LCD4data, "sun.png")):
			try:
				imW = Image.open(join(LCD4data, "sun.png"))
				imW = imW.resize((ConfigSize, ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					self.im[im].paste(imW, (POSX, POSY), imW)
				else:
					self.im[im].paste(imW, (POSX, POSY))
			except Exception:
				pass
			if ConfigBackColor != "0":
				w, h = getFsize("%02d:%02d" % L4LSun, font)
				self.draw[draw].rectangle((POSXi, POSY, POSXi + w, POSY + h), fill=ConfigBackColor)
			ShadowText(draw, POSXi, POSY, "%02d:%02d" % L4LSun, font, ConfigColor, ConfigShadow)
		if ConfigType == "2":
			POSY += ConfigSize
		else:
			POSX += ConfigSize + w + int(ConfigSize / 3) + int(ConfigSize / 6)
			POSXi = POSX + ConfigSize + int(ConfigSize / 6)
		if isfile(join(LCD4data, "moon.png")):
			try:
				imW = Image.open(join(LCD4data, "moon.png"))
				imW = imW.resize((ConfigSize, ConfigSize))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					self.im[im].paste(imW, (POSX, POSY), imW)
				else:
					self.im[im].paste(imW, (POSX, POSY))
			except Exception:
				pass
			if ConfigBackColor != "0":
				w, h = getFsize("%02d:%02d" % L4LMoon, font)
				self.draw[draw].rectangle((POSXi, POSY, POSXi + w, POSY + h), fill=ConfigBackColor)
			ShadowText(draw, POSXi, POSY, "%02d:%02d" % L4LMoon, font, ConfigColor, ConfigShadow)

# Netatmo
	def putNetatmo(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigStation, ConfigModule, ConfigModuleUser, ConfigBasis, ConfigName, ConfigType, ConfigType2, ConfigColor, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)

		def getColor(c):
			return ConfigColor[0] if ConfigColor[c] == "0" else ConfigColor[c]
		MAX_W, MAX_H = self.im[im].size
		if ConfigModule == "0":
			ConfigModule = ConfigModuleUser
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
#		font1 = ImageFont.truetype(ConfigFont, int(ConfigSize / 1.5), encoding='unic')
		font2 = ImageFont.truetype(ConfigFont, int(ConfigSize / 2), encoding='unic')
		font3 = ImageFont.truetype(ConfigFont, int(ConfigSize / 3), encoding='unic')
		font4 = ImageFont.truetype(ConfigFont, int(ConfigSize / 5), encoding='unic')
		if self.NetatmoOK == False:
			self.draw[draw].text((int(MAX_W / 4), ConfigPos), _("no Netatmo-Plugin installed"), font=font2, fill=ConfigColor[0])
			return
		ConfigStation = int(ConfigStation) - 1
		if len(self.iT) <= ConfigStation or len(self.oM) <= ConfigStation:
			L4log("Netatmo: no Station", "%s" % ConfigStation)
			return
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		POSY = ConfigPos
		w1, h1 = getFsize("-88", font)
		w2, h2 = getFsize(".8", font2)
		w3, h3 = getFsize("88888" + self.PRESSURE, font2)
		if ConfigType2 == "0":
			oMlen = 0
			i = 0
			for Mod in self.oM[ConfigStation]:
				i += 1
				if str(i) in ConfigModule:
					oMlen += 1
			w12 = w1 + w2 + w2
			w123 = w12 + (w12 * oMlen)
			if ConfigBasis == True:
				if "C" in ConfigType:
					w123 += w3
			else:
				w123 -= w12
		else:
			w12 = w1 + w2
			w123 = w12 + w2
			if "H" in ConfigType:
				w4, h4 = getFsize("88%", font2)
				w123 += w4
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, w123)
		i = 0
		L4logE("Netatmo-Config", ConfigModule)
		L4logE("Netatmo-Mod", self.oM[ConfigStation])
		for IDX in list(ConfigModule):
			L4logE("Netatmo", IDX)
			i = int(IDX)
			if i <= len(self.oM[ConfigStation]):
				Mod = self.oM[ConfigStation][i - 1]
				L4logE("Netatmo", Mod)
				if Mod[6] != "green":
					self.draw[draw].rectangle((POSX, POSY, POSX + w2, POSY + int(w2 / 3)), outline=Mod[6], fill=Mod[6])
				if Mod[5] == "NAModule3":
					E1 = E2 = self.MM
				elif Mod[5] == "NAModule2":
					E1 = E2 = self.WIND
				else:
					E1 = self.TEMPERATURE.decode()
					E2 = self.HUMIDITY
				if Mod[5] == "NAModule2":
					ShadowText(draw, POSX, POSY, Mod[0], font, getColor(i), ConfigShadow)
					w, h = getFsize(Mod[0].split(".")[0], font)
					ShadowText(draw, POSX + w, POSY + int(h / 5 * 2), "  " + getDirection(int(Mod[1])), font2, getColor(i), ConfigShadow)
					ShadowText(draw, POSX + w, POSY, E1, font2, getColor(i), ConfigShadow)
				else:
					ShadowText(draw, POSX, POSY, Mod[0].split(".")[0], font, getColor(i), ConfigShadow)
					w, h = getFsize(Mod[0].split(".")[0], font)
					ShadowText(draw, POSX + w, POSY + int(h / 5 * 2), "." + Mod[0].split(".")[1], font2, getColor(i), ConfigShadow)
					ShadowText(draw, POSX + w, POSY, E1, font2, getColor(i), ConfigShadow)
				if ConfigName == True:
					wn, hn = getFsize(Mod[4], font3)
					ADD = int(hn / 2)
					ShadowText(draw, POSX + int((w1 + w2 - wn) / 2), POSY + h - ADD, Mod[4], font3, getColor(i), ConfigShadow)
				else:
					ADD = 0
				if "H" in ConfigType:
					if Mod[5] == "NAModule2":
						w, h = getFsize(Mod[2], font2)
						if ConfigType2 == "0":
							PX = 0 - int(w / 3)
							PY = h1 + ADD
						else:
							PX = w1 + w2
							PY = 0
						ShadowText(draw, POSX + PX, POSY + PY, Mod[2], font2, getColor(i), ConfigShadow)
						w, h = getFsize(Mod[2], font2)
						ShadowText(draw, POSX + w + PX, POSY + PY, E2, font3, getColor(i), ConfigShadow)
						w, h = getFsize(Mod[3], font2)
						we2, he2 = getFsize(E2, font3)
						if ConfigType2 == "0":
							PX = int((w1 / 2) + (we2 / 1.5))
							PY = h1 + ADD + int(h / 5)
						else:
							PX = w1 + w2
							PY = h
						ShadowText(draw, POSX + PX, POSY + PY, getDirection(int(Mod[3])), font3, getColor(i), ConfigShadow)
					else:
						w, h = getFsize(Mod[1], font2)
						if ConfigType2 == "0":
							if Mod[2] is None or "C" not in ConfigType:
								PX = int((w1 - w) / 2)
							else:
								PX = 0
							PY = h1 + ADD
						else:
							PX = w1 + w2
							PY = int(h1 / 5 * 2)
						ShadowText(draw, POSX + PX, POSY + PY, Mod[1], font2, getColor(i), ConfigShadow)
						ShadowText(draw, POSX + w + PX, POSY + PY, E2, font3, getColor(i), ConfigShadow)
						if Mod[2] is not None and "C" in ConfigType:
							w, h = getFsize(Mod[2], font2)
							we2, he2 = getFsize(E2, font3)
							if ConfigType2 == "0":
								PX = int((w1 / 2) + (we2 / 1.5))
								PY = h1 + ADD + int(h / 5)
							else:
								PX = w1 + w2
								PY = int(h1 / 5 * 2) + h
							ShadowText(draw, POSX + PX, POSY + PY, Mod[2], font3, getColor(i), ConfigShadow)
							w, h = getFsize(Mod[2], font3)
							ShadowText(draw, POSX + w + PX, POSY + PY, self.CO2, font4, getColor(i), ConfigShadow)
				if ConfigType2 == "0":
					POSX += w12
				else:
					POSY += h1 + ADD
		if ConfigBasis == True:
			ShadowText(draw, POSX, POSY, self.iT[ConfigStation].split(".")[0], font, ConfigColor[0], ConfigShadow)
			w, h = getFsize(self.iT[ConfigStation].split(".")[0], font)
			ShadowText(draw, POSX + w, POSY + int(h / 5 * 2), "." + self.iT[ConfigStation].split(".")[1], font2, ConfigColor[0], ConfigShadow)
			ShadowText(draw, POSX + w, POSY, self.TEMPERATURE.decode(), font2, ConfigColor[0], ConfigShadow)
			if ConfigName == True:
				wn, hn = getFsize(self.iName[ConfigStation], font3)
				ADD = int(hn / 2)
				ShadowText(draw, POSX + int((w1 + w2 - wn) / 2), POSY + h - ADD, self.iName[ConfigStation], font3, ConfigColor[0], ConfigShadow)
			else:
				ADD = 0
			if "H" in ConfigType:
				w, h = getFsize(self.iH[ConfigStation], font2)
				if ConfigType2 == "0":
					PX = int((w1 - w) / 2)
					PY = h1 + ADD
				else:
					PX = w1 + w2
					PY = int(h1 / 5 * 2)
				ShadowText(draw, POSX + PX, POSY + PY, self.iH[ConfigStation], font2, ConfigColor[0], ConfigShadow)
				ShadowText(draw, POSX + w + PX, POSY + PY, self.HUMIDITY, font3, ConfigColor[0], ConfigShadow)
			if ConfigType2 == "0":
				POSX += w12
				POSY += int(ADD / 1.5)
			else:
				POSY += h1 + ADD
			if "C" in ConfigType:
				ShadowText(draw, POSX, POSY, self.iC[ConfigStation], font2, ConfigColor[0], ConfigShadow)
				w, h = getFsize(self.iC[ConfigStation], font2)
				ShadowText(draw, POSX + w, POSY, self.CO2, font3, ConfigColor[0], ConfigShadow)
			if "P" in ConfigType:
				ShadowText(draw, POSX, POSY + h, self.iP[ConfigStation], font2, ConfigColor[0], ConfigShadow)
				w, h = getFsize(self.iP[ConfigStation], font2)
				ShadowText(draw, POSX + w, POSY + h, self.PRESSURE, font3, ConfigColor[0], ConfigShadow)
			if "N" in ConfigType:
				ShadowText(draw, POSX, POSY + h + h, self.iN[ConfigStation], font2, ConfigColor[0], ConfigShadow)
				w, h = getFsize(self.iN[ConfigStation], font2)
				ShadowText(draw, POSX + w, POSY + h + h, self.NOISE, font3, ConfigColor[0], ConfigShadow)

# Netstmo CO2
	def putNetatmoIllu(workaround, draw, im):
		(CW, ConfigPos, ConfigSize, ConfigLen, ConfigAlign, ConfigSplit, ConfigStation, ConfigType) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		ConfigLen = int(ConfigLen)
		ConfigStation = int(ConfigStation) - 1
		staerke = 0
		staerkeValOrg = ""
		if len(self.oM) <= ConfigStation:
			L4log("Netatmo: no Station", "%s" % ConfigStation)
			return
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, ConfigLen if ConfigType == "0" else ConfigSize)
		dis_reason = ""
		if CW == "CO2":
			staerkeVal2 = int(self.iC[ConfigStation])
			staerkeValOrg = staerkeVal2
			if staerkeVal2 < int(LCD4linux.NetAtmoCO2Min.value):
				staerkeVal2 = int(LCD4linux.NetAtmoCO2Min.value)
			elif staerkeVal2 > int(LCD4linux.NetAtmoCO2Max.value):
				staerkeVal2 = int(LCD4linux.NetAtmoCO2Max.value)
			staerke = 100 * (staerkeVal2 - int(LCD4linux.NetAtmoCO2Min.value)) / (int(LCD4linux.NetAtmoCO2Max.value) - int(LCD4linux.NetAtmoCO2Min.value))
		elif CW == "IDX":
			staerkeVal2 = int(float(self.iIDX[ConfigStation]))
			staerkeValOrg = staerkeVal2
			staerke = staerkeVal2
			dis_reason = Code_utf8(self.dis_reason[ConfigStation])
		if ConfigType.startswith("0"):
			if ConfigType[1:] == "9":
				S = 1.5 if ConfigSize <= 10 else 1.0
				ZW = str(staerkeValOrg)  # Value
				font = ImageFont.truetype(FONT, int(ConfigSize * S), encoding='unic')
				w, h = getFsize(ZW, font)
				ConfigLen -= (w + 10)
				self.draw[draw].text((ConfigLen + 5 + POSX, ConfigPos + 1 - int((h - ConfigSize) / 2)), ZW, font=font, fill="yellow")
			if isfile(join(LCD4data, "gradient.png")):
				try:
					imW = Image.open(join(LCD4data, "gradient.png"))
					imW = imW.resize((ConfigLen, ConfigSize))
					imW = imW.crop((0, 0, int(ConfigLen * staerke / 100), ConfigSize))
					self.im[im].paste(imW, (POSX, ConfigPos))
				except Exception:
					pass
			self.draw[draw].rectangle((POSX, ConfigPos, POSX + ConfigLen, ConfigPos + ConfigSize), outline="yellow")
		elif ConfigType.startswith("1"):
			if isfile(join(LCD4data, "pointmask.png")):
				try:
					imM = Image.open(join(LCD4data, "pointmask.png"))
					imM = imM.resize((ConfigSize, ConfigSize))
					b = Image.new("RGBA", (ConfigSize, ConfigSize), ScaleGtoR(staerke))
					b.putalpha(imM.convert("L"))
					self.im[im].paste(b, (POSX, ConfigPos), b)
				except Exception:
					L4log("Error Knob")
					L4log("Error:", format_exc())
			if ConfigType[1:] == "9":
				ZW = str(int(staerkeValOrg))
				font = ImageFont.truetype(FONT, int(ConfigSize / 3), encoding='unic')
				w, h = getFsize(ZW, font)
				self.draw[draw].text((POSX + 1 + int((ConfigSize - w) / 2), ConfigPos + 1 + int((ConfigSize - h) / 2)), ZW, font=font, fill="black")
				if dis_reason != "":
					font = ImageFont.truetype(FONT, int(ConfigSize / 4), encoding='unic')
					w1, h1 = getFsize(dis_reason, font)
					ShadowText(draw, min(max(POSX + 1 + int((ConfigSize - w1) / 2), 0), MAX_W - w1), ConfigPos + int((ConfigSize - h) / 2) + h, dis_reason, font, ScaleGtoR(staerke), True)

# Kalender
	def putCalendar(workaround, draw, im):
		(ConfigPos, ConfigZoom, ConfigAlign, ConfigSplit, ConfigType, ConfigTypeE, ConfigLayout, ConfigColor, ConfigBackColor, ConfigCaptionColor, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigZoom = int(ConfigZoom)
		global CalType
		global CalZoom
		global CalColor
		global PICcal
		MAX_Wi, MAX_Hi = self.im[im].size
		h = 0
		PutWeek = False
		if ConfigSplit == True:
			MAX_Wi = int(MAX_Wi / 2)
		if PICcal is not None and [ConfigType, ConfigTypeE, LCD4linux.CalDays.value] == CalType and ConfigZoom == CalZoom and [ConfigColor, ConfigBackColor, ConfigCaptionColor] == CalColor:
			x, y = self.im[4].size
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_Wi, x)
			if LCD4linux.CalTransparenz.value == "true":
				self.im[im].paste(self.im[4], (POSX, ConfigPos), self.im[4])
			else:
				self.im[im].paste(self.im[4], (POSX, ConfigPos))
		else:
			POSX = 0
			POSY = 0
			ConfigSize = int(20 * ConfigZoom / 10)
			MAX_H = ConfigSize
			MAX_W = ConfigSize * 16
			if ConfigType.startswith("0"):
				MAX_H = ConfigSize * 9
			elif ConfigType.startswith("1"):
				MAX_H = ConfigSize * 4
			if ConfigTypeE[0] in ["C", "D"]:
				if ConfigType.startswith("9"):
					MAX_W = ConfigSize * 25
				MAX_H += ConfigSize * int(int(ConfigTypeE[1]) * 0.8)
			MAX_H += int(ConfigSize * 0.4)
			CalType = [ConfigType, ConfigTypeE, LCD4linux.CalDays.value]
			CalZoom = ConfigZoom
			CalColor = [ConfigColor, ConfigBackColor, ConfigCaptionColor]
			CC = [LCD4linux.CalPathColor.value, LCD4linux.CalHttpColor.value, LCD4linux.CalHttp2Color.value, LCD4linux.CalHttp3Color.value, LCD4linux.CalPlanerFSColor.value]
			if LCD4linux.CalTransparenz.value == "true":
				self.im[4] = Image.new('RGBA', (MAX_W, MAX_H), (0, 0, 0, 0))
			else:
				self.im[4] = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
				if LCD4linux.CalTransparenz.value == "crop":
					POSXs = getSplit(ConfigSplit, ConfigAlign, MAX_Wi, MAX_W)
					image_Back = self.im[im].crop((POSXs, ConfigPos, POSXs + MAX_W, ConfigPos + MAX_H))
					self.im[4].paste(image_Back, (0, 0))
			self.draw[4] = ImageDraw.Draw(self.im[4])
			font = ImageFont.truetype(ConfigFont, int(ConfigSize * 0.8), encoding='unic')
			if "A" in ConfigType:
				M = Code_utf8("%s %s" % (_(month_name[datetime.now().month]), datetime.now().year))
				w, h = getFsize(M, font)
				ShadowText(4, POSX + int(MAX_W / 2) - int(w / 2), POSY, M, font, ConfigColor, ConfigShadow)
				POSY += h + int(ConfigSize * 0.2)
			if ConfigType[0] in ["0", "1"]:
				i = 1
				for Week in weekheader(3).split():
					w, h = getFsize(Code_utf8(_(Week)), font)
					ShadowText(4, POSX + int(ConfigSize * 2 * i) + int(ConfigSize / 2) - int(w / 2), POSY, Code_utf8(_(Week)), font, ConfigCaptionColor, ConfigShadow)
					i += 1
				POSY += h
				font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
				ThisWeek = date(datetime.now().year, datetime.now().month, datetime.now().day).isocalendar()[1]
				for day in Calendar().itermonthdays2(datetime.now().year, datetime.now().month):
					if day[1] == 0:
						font = ImageFont.truetype(ConfigFont, int(ConfigSize * 0.6), encoding='unic')
						dd = 1 if day[0] == 0 else day[0]
						Week = date(datetime.now().year, datetime.now().month, dd).isocalendar()[1]
						PutWeek = False
						if ConfigType.startswith("0") or (ConfigType.startswith("1") and ThisWeek == Week):
							PutWeek = True
							Week = str(Week)
							w, h = getFsize(Week, font)
							w1, h1 = getFsize("8", font)
							ShadowText(4, POSX + w1 - int(w / 2), POSY + int(h / 3), Week, font, ConfigCaptionColor, ConfigShadow)
					if PutWeek == True:
						font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
						if day[0] > 0:
							Tag = str(max(min(day[0], 31), 1))
							w, h = getFsize(Tag, font)
							today = date.today()
							ICStag = date(today.year, today.month, int(Tag)).strftime("%Y-%m-%d")
							PX1 = POSX + int(ConfigSize * 2 * (day[1] + 1)) + int(ConfigSize / 2)
							PX = PX1 - int(w / 2)
							w1, h1 = getFsize(" 1", font)
							if ConfigLayout in ["0", "2"]:
								if datetime.now().day == day[0]:
									self.draw[4].rectangle((PX1 - w1, POSY, PX1 + w1, POSY + h), fill=ConfigBackColor)
								ShadowText(4, PX, POSY, Tag, font, ConfigColor if day[1] < 5 else LCD4linux.CalSaColor.value if day[1] == 5 else LCD4linux.CalSuColor.value, ConfigShadow)
							if ConfigLayout in ["0"] and ICS.get(ICStag, None) is not None:
								self.draw[4].rectangle((PX1 - w1, POSY, PX1 + w1, POSY + h), outline=CC[int(ICS[ICStag][0][2])])
								if int(LCD4linux.CalLine.value) > 1:
									self.draw[4].rectangle((PX1 - w1 + 1, POSY + 1, PX1 + w1 - 1, POSY + h - 1), outline=CC[int(ICS[ICStag][0][2])])
							w1, h1 = getFsize("1", font)
							if ConfigLayout in ["1"]:
								if datetime.now().day == day[0]:
									ShadowText(4, PX, POSY, Tag, font, ConfigBackColor, ConfigShadow)
									self.draw[4].rectangle((PX1 - w1, POSY + h - 1, PX1 + w1, POSY + h - 1), outline=ConfigBackColor)
									if int(LCD4linux.CalLine.value) > 1:
										self.draw[4].rectangle((PX1 - w1, POSY + h, PX1 + w1, POSY + h), outline=ConfigBackColor)
								else:
									ShadowText(4, PX, POSY, Tag, font, ConfigColor if day[1] < 5 else LCD4linux.CalSaColor.value if day[1] == 5 else LCD4linux.CalSuColor.value, ConfigShadow)
							if ConfigLayout in ["1", "2"] and ICS.get(ICStag, None) is not None:
								self.draw[4].rectangle((PX1 - w1, POSY + h, PX1 + w1, POSY + h), outline=CC[int(ICS[ICStag][0][2])])
								if int(LCD4linux.CalLine.value) > 1:
									self.draw[4].rectangle((PX1 - w1, POSY + h + 1, PX1 + w1, POSY + h + 1), outline=CC[int(ICS[ICStag][0][2])])
						if day[1] == 6:
							POSY += h
			POSY += int(ConfigSize * 0.2)
			if "C" == ConfigTypeE[0]:
				aa = ""
				al = 1
				font = ImageFont.truetype(ConfigFont, int(ConfigSize * 0.8), encoding='unic')
				w1, h1 = getFsize("88.88. ", font)
				for t in sorted(ICS):
					x = datetime.strptime(str(t), "%Y-%m-%d")
					DTx = date(x.year, x.month, x.day) - date.today()
					if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
						aa = "%02d.%02d. " % (x.day, x.month)
						w, h = getFsize(Code_utf8(aa), font)
						POSX = w1 - w
						ShadowText(4, POSX, POSY, Code_utf8(aa), font, ConfigColor, ConfigShadow)
						b = []
						for a in ICS.get(t, []):
							x = a[1] + timedelta(hours=getTimeDiffUTC() + int(LCD4linux.CalTimeZone.value))
							if isinstance(x, datetime):
								Time = x.time().strftime("%H:%M ")
							else:
								Time = ""
							b.append("%s%s" % (Time, a[0]))
						for a in sorted(b):
							aa += str(a)
							ShadowText(4, POSX + w, POSY, Code_utf8(a), font, ConfigColor, ConfigShadow)
							POSY += h
							al += 1
							if al > int(ConfigTypeE[1]):
								break
						if al > int(ConfigTypeE[1]):
							break
			if "D" == ConfigTypeE[0]:
				aa = ""
				for t in sorted(ICS):
					x = datetime.strptime(str(t), "%Y-%m-%d")
					DTx = date(x.year, x.month, x.day) - date.today()
					if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
						if x.day != datetime.now().day:
							aa += "%02d.%02d. " % (x.day, x.month)
						for a in ICS.get(t, []):
							x = a[1] + timedelta(hours=getTimeDiffUTC() + int(LCD4linux.CalTimeZone.value))
							if isinstance(x, datetime):
								Time = x.time().strftime("%H:%M ")
							else:
								Time = ""
							aa += Time + a[0] + " | "
				writeMultiline(aa[:-2], int(ConfigSize * 0.8), POSY, int(ConfigTypeE[1]), ConfigColor, "0", False, 4, 4, ConfigFont=ConfigFont, Shadow=ConfigShadow)
			PICcal = 1
			POSX = getSplit(ConfigSplit, ConfigAlign, MAX_Wi, MAX_W)
			try:
				if LCD4linux.CalTransparenz.value == "true":
					self.im[im].paste(self.im[4], (POSX, ConfigPos), self.im[4])
				else:
					self.im[im].paste(self.im[4], (POSX, ConfigPos))
			except Exception:
				pass

# Kalender-Liste
	def putCalendarList(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigProzent, ConfigAlign, ConfigSplit, ConfigType, ConfigLines, ConfigColor, ConfigShadow, ConfigFont) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		if ConfigSplit == True:
			MAX_W = int(MAX_W / 2)
		CW = int(MAX_W * int(ConfigProzent) / 100)
		POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, CW)
		POSY = ConfigPos
		font = ImageFont.truetype(ConfigFont, ConfigSize, encoding='unic')
		findICS = False
		for t in sorted(ICS):
			x = datetime.strptime(str(t), "%Y-%m-%d")
			DTx = date(x.year, x.month, x.day) - date.today()
			if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
				findICS = True
				break
		if findICS == False:
			if LCD4linux.ShowNoMsg.value == True:
				ShadowText(draw, POSX, POSY, _("no Dates"), font, ConfigColor, ConfigShadow)
			return
		CS = int(ConfigSize * 1.8)
		w1, h1 = getFsize("A", font)
		if isfile(join(LCD4data, "calendar.png")) and "-" not in ConfigType:
			try:
				imW = Image.open(join(LCD4data, "calendar.png"))
				xx, yy = imW.size
				x1 = int(float(CS) / yy * xx)
				imW = imW.resize((x1, CS))
				if LCD4linux.WetterTransparenz.value == "true":
					imW = imW.convert("RGBA")
					self.im[im].paste(imW, (POSX, POSY), imW)
				else:
					self.im[im].paste(imW, (POSX, POSY))
				POSX += x1 + w1
			except Exception:
				pass
		if "C" in ConfigType:
			aa = ""
			al = 1
			w1, h1 = getFsize("88.88. ", font)
			for t in sorted(ICS):
				x = datetime.strptime(str(t), "%Y-%m-%d")
				DTx = date(x.year, x.month, x.day) - date.today()
				if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
					aa = "%02d.%02d. " % (x.day, x.month)
					w, h = getFsize(Code_utf8(aa), font)
					PX = POSX + w1 - w
					ShadowText(draw, PX, POSY, Code_utf8(aa), font, ConfigColor, ConfigShadow)
					b = []
					for a in ICS.get(t, []):
						x = a[1] + timedelta(hours=getTimeDiffUTC() + int(LCD4linux.CalTimeZone.value))
						if isinstance(x, datetime):
							Time = x.time().strftime("%H:%M ")
						else:
							Time = ""
						b.append("%s%s" % (Time, a[0]))
					for a in sorted(b):
						aa += a
						tx = cutText(Code_utf8(a), draw, font, CW - w - CS)
						ShadowText(draw, PX + w, POSY, tx, font, ConfigColor, ConfigShadow)
						POSY += h
						al += 1
						if al > int(ConfigLines):
							break
					if al > int(ConfigLines):
						break
		elif "D" in ConfigType:
			aa = ""
			for t in sorted(ICS):
				x = datetime.strptime(str(t), "%Y-%m-%d")
				DTx = date(x.year, x.month, x.day) - date.today()
				if DTx >= timedelta(0) and DTx <= timedelta(int(LCD4linux.CalDays.value)):
					if x.day != datetime.now().day:
						aa += "%02d.%02d. " % (x.day, x.month)
					for a in ICS.get(t, []):
						x = a[1] + timedelta(hours=getTimeDiffUTC() + int(LCD4linux.CalTimeZone.value))
						if isinstance(x, datetime):
							Time = x.time().strftime("%H:%M ")
						else:
							Time = ""
						aa += Time + a[0] + " | "
			writeMultiline(aa[:-2], int(ConfigSize), POSY, int(ConfigLines), ConfigColor, ConfigAlign, ConfigSplit, draw, im, ConfigFont=ConfigFont, Shadow=ConfigShadow, Width=CW, PosX=POSX)

# show isRecording
	def putRecording(workaround, draw, im):
		(ConfigPos, ConfigSize, ConfigAlign, ConfigSplit, ConfigType) = workaround
		ConfigPos = int(ConfigPos)
		ConfigSize = int(ConfigSize)
		MAX_W, MAX_H = self.im[im].size
		POSX = None
		if self.LisRecording or ConfigMode == True:
			if ConfigType.startswith("1"):
				self.draw[draw].ellipse((MAX_W - ConfigSize, -ConfigSize, MAX_W + ConfigSize, ConfigSize), fill="red")
			else:
				try:
					if ConfigSplit == True:
						MAX_W = int(MAX_W / 2)
					pil_image = Image.open(LCD4linux.RecordingPath.value if isfile(LCD4linux.RecordingPath.value) else RecPic)
					xx, yy = pil_image.size
					x = int(float(ConfigSize) / yy * xx)
					pil_image = pil_image.resize((x, ConfigSize))
					POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, x)
					if LCD4linux.WetterTransparenz.value == "true":
						pil_image = pil_image.convert("RGBA")
						self.im[im].paste(pil_image, (POSX, ConfigPos), pil_image)
					else:
						self.im[im].paste(pil_image, (POSX, ConfigPos))
				except Exception:
					L4log("Error Recording Pic")
		if self.LisTimeshift and "t" in ConfigType:
			if ConfigType.startswith("1"):
				for i in range(-1, 3):
					self.draw[draw].ellipse((MAX_W - ConfigSize - i, -ConfigSize - i, MAX_W + ConfigSize + i, ConfigSize + i), outline="yellow")
			else:
				if POSX is None:
					POSX = getSplit(ConfigSplit, ConfigAlign, MAX_W, ConfigSize)
				for i in range(-1, 2):
					self.draw[draw].ellipse((POSX - i, ConfigPos - i, POSX + ConfigSize + i, ConfigPos + ConfigSize + i), outline="yellow")

# show Box
	def putBox(workaround, draw, im):
		(x1, y1, x2, y2, ConfigColor, ConfigBackColor) = workaround
		x1 = int(x1)
		y1 = int(y1)
		x2 = int(x2)
		y2 = int(y2)
		if ConfigBackColor == "0":
			self.draw[draw].rectangle((x1, y1, x1 + x2, y1 + y2), outline=ConfigColor)
		else:
			self.draw[draw].rectangle((x1, y1, x1 + x2, y1 + y2), fill=ConfigBackColor, outline=ConfigColor)

# show isCrashlog
	def putCrash(draw, im):
		if isfile(CrashFile):
			self.draw[draw].ellipse((-25, -25, 25, 25), fill="yellow")

# externe Elemente
	def putL4LElist(MODE):
		def Sync(L):
			if "1" in L:
				Brief1.join()
			elif "2" in L and LCD4linux.LCDType2.value != "00":
				Brief2.join()
			elif "3" in L and LCD4linux.LCDType3.value != "00":
				Brief3.join()
		L4Lkeys = sorted(L4LElist.get().keys())
		for E in L4Lkeys:
			CUR = L4LElist.get(E)
#			L4logE("CUR: %s Active %s" % (CUR,ScreenActive[0]))
			LCD = str(CUR.get("Lcd", "1"))
			if getSA(int(LCD)) in str(CUR.get("Screen", "1")) and MODE in CUR.get("Mode", "On"):
				Typ = CUR.get("Typ", None)
				if "1" in LCD:
					DR, IM = 1, 1
				elif "2" in LCD and LCD4linux.LCDType2.value != "00":
					DR, IM = 2, 2
				elif "3" in LCD and LCD4linux.LCDType3.value != "00":
					DR, IM = 3, 3
				else:
					DR = IM = None
				if DR is not None and Typ is not None:
					MAX_W, MAX_H = self.im[IM].size
					if Typ == "txt":
						L4logE("Text", "%s" % CUR)
						writeMultiline(str(CUR.get("Text", "Text")), int(CUR.get("Size", 20)), int(CUR.get("Pos", 0)), int(CUR.get("Lines", 1)), CUR.get("Color", "white"), str(CUR.get("Align", "1")), False, DR, IM, ConfigFont=getFont(str(CUR.get("Font", "0"))), Shadow=CUR.get("Shadow", False), Width=getProgess(MAX_W, int(CUR.get("Len", 100))))
					elif Typ == "bar":
						L4logE("Bar", "%s" % CUR)
						POSX = getSplit(False, str(CUR.get("Align", "1")), MAX_W, int(CUR.get("Len", int(MAX_W / 2))) + 1)
						self.draw[DR].rectangle((POSX, int(CUR.get("Pos", 0)), POSX + int(CUR.get("Len", int(MAX_W / 2))), int(CUR.get("Pos", 0)) + int(CUR.get("Size", 20))), outline=CUR.get("Color", "white"))
						self.draw[DR].rectangle((POSX, int(CUR.get("Pos", 0)), POSX + int(int(CUR.get("Len", int(MAX_W / 2))) * int(CUR.get("Value", 50)) / 100), int(CUR.get("Pos", 0)) + int(CUR.get("Size", 20))), fill=CUR.get("Color", "white"))
					elif Typ == "pic":
						L4logE("Pic", "%s" % CUR)
						ShowPicture = getShowPicture(CUR.get("File", ""), 0)
						if ShowPicture != "":
							putBild((int(CUR.get("Pos", 0)), int(CUR.get("Size", 100)), int(CUR.get("Height", 0)), str(CUR.get("Align", "1")), CUR.get("Quick", False), CUR.get("Transp", False), 0, ShowPicture, ShowPicture), 0, DR, IM)
						else:
							if CUR.get("Text", "") != "":
								L4logE("PicText", "%s" % CUR)
								writeMultiline(str(CUR.get("Text", "Text")), int(CUR.get("TextSize", 20)), int(CUR.get("Pos", 0)), int(CUR.get("Lines", 1)), CUR.get("Color", "white"), str(CUR.get("Align", "1")), False, DR, IM, ConfigFont=getFont(str(CUR.get("Font", "0"))), Shadow=CUR.get("Shadow", False), Width=int(CUR.get("Size", 100)))
					elif Typ == "box":
						L4logE("Box", "%s" % CUR)
						if CUR.get("Fill", True) == False:
							self.draw[DR].rectangle((int(CUR.get("PosX", 0)), int(CUR.get("PosY", 0)), int(CUR.get("PosX", 0)) + int(CUR.get("Width", 100)), int(CUR.get("PosY", 0)) + int(CUR.get("Height", 100))), outline=CUR.get("Color", "white"))
						else:
							Sync(LCD)
							self.draw[DR].rectangle((int(CUR.get("PosX", 0)), int(CUR.get("PosY", 0)), int(CUR.get("PosX", 0)) + int(CUR.get("Width", 100)), int(CUR.get("PosY", 0)) + int(CUR.get("Height", 100))), fill=CUR.get("Color", "white"), outline=CUR.get("Color", "white"))
							Sync(LCD)
					elif Typ == "circle":
						L4logE("Circle", "%s" % CUR)
						px = int(CUR.get("PosX", 0))
						py = int(CUR.get("PosY", 0))
						ps = int(CUR.get("Size", 20))
						pc = CUR.get("Color", "white")
						pt = CUR.get("Text", "")
						pf = getFont(str(CUR.get("Font", "0")))
						self.draw[DR].ellipse((px, py, px + ps, py + ps), fill=pc)
						if pt != "":
							TextSize = int(ps * 0.8)
							font = ImageFont.truetype(pf, TextSize, encoding='unic')
							w, h = getFsize(pt, font)
							while w > int(ps * 0.9):
								TextSize -= 1
								font = ImageFont.truetype(pf, TextSize, encoding='unic')
								w, h = getFsize(pt, font)
							self.draw[DR].text((px + 1 + int((ps - w) / 2), py + 1 + int((ps - h) / 2)), pt, font=font, fill="black")
					elif Typ == "wait":
						L4logE("External-Wait")
						Sync(LCD)
				else:
					L4log("Elemente-Fehler %s" % CUR)

	def Lput(LCD, SCR, FUNC, PARA):
		if "1" in LCD and getSA(1) in SCR and self.Refresh >= LCD4linux.LCDRefresh1.value:
			Brief1.put([FUNC, PARA, 1, 1])
		if "2" in LCD and LCD4linux.LCDType2.value != "00" and getSA(2) in SCR and self.Refresh >= LCD4linux.LCDRefresh2.value:
			Brief2.put([FUNC, PARA, 2, 2])
		if "3" in LCD and LCD4linux.LCDType3.value != "00" and getSA(3) in SCR and self.Refresh >= LCD4linux.LCDRefresh3.value:
			Brief3.put([FUNC, PARA, 3, 3])

	def Lput4(LCD, SCR, FUNC, PARA):
		if "1" in LCD and getSA(1) in SCR and self.Refresh >= LCD4linux.LCDRefresh1.value:
			Brief1.put([FUNC, PARA, 0, 1, 1])
		if "2" in LCD and LCD4linux.LCDType2.value != "00" and getSA(2) in SCR and self.Refresh >= LCD4linux.LCDRefresh2.value:
			Brief2.put([FUNC, PARA, 1, 2, 2])
		if "3" in LCD and LCD4linux.LCDType3.value != "00" and getSA(3) in SCR and self.Refresh >= LCD4linux.LCDRefresh3.value:
			Brief3.put([FUNC, PARA, 2, 3, 3])
	if not LCD4linux.Enable.value:
		return
	tt = time()
#	L4logE("MP-Mode", isMediaPlayer)
	L4log("creating LCD-Picture: %s" % ScreenActive)
	if isdir("%slcd4linux" % TMP) == False:
		try:
			mkdir("%slcd4linux" % TMP)
		except Exception:
			L4log("%s Error" % TMP)
	if OSDon >= 2 and FritzTime == 0:
		if Briefkasten.qsize() <= 3:
			Briefkasten.put(2)
		else:
			L4log("Queue full, Thread hanging?")

	if self.LsreftoString is not None:
		sref = self.LsreftoString
		L4logE("Service    ", sref)
		L4logE("Service alt", self.ref)
		if self.ref != sref or (self.SaveisMediaPlayer != isMediaPlayer and not ConfigMode):
			L4log("Service changed")
			self.ref = sref
			if SaveEventListChanged == False:
				ScreenActive[0] = "1"
				LCD4linux.ScreenActive.value = ScreenActive[0]
				ScreenTime = 0
			self.SaveisMediaPlayer = isMediaPlayer
			isMediaPlayer = ""
			rmFile(MP3tmp)
#			rmFile(GoogleCover)
			if self.SonosRunning:
				L4log("detected Sonos")
				isMediaPlayer = "sonos"
			elif self.YMCastRunning:
				L4log("detected YMC")
				isMediaPlayer = "ymc"
			elif self.BlueRunning:
				L4log("detected BlueSound")
				isMediaPlayer = "blue"
			elif sref.startswith("1:0:2") is True:
				L4log("detected Radio")
				isMediaPlayer = "radio"
				self.CoverIm = None
				self.CoverName = ["-", "-"]
			elif sref.startswith(("4097:0", "5001:0", "5002:0", "5003:0")):
				if self.Lpath and self.Lpath.startswith("http") and self.Llength and self.Llength[0] == -1:
					L4log("detected AudioMedia or IPTV")
					isMediaPlayer = "mp3"
				else:
					L4log("detected VOD Media")
					isMediaPlayer = "mp3"
			elif "0:0:0:0:0:0:0:0:0:" in sref:
				L4log("detected Video")
				isMediaPlayer = "record"
			else:
				self.CoverIm = None
				self.CoverName = ["-", "-"]
			if isMediaPlayer != "mp3" and isMediaPlayer != "record":
				rmFile("/tmp/.cover")
				rmFile("/tmp/.wbrfs_pic")
			if self.SaveisMediaPlayer != isMediaPlayer:
				getBilder()
				rmFile(PICfritz)
			L4logE("MP-Mode", isMediaPlayer)
	QuickList = [[], [], []]
	Dunkel = ""
	MAX_W, MAX_H = getResolution(LCD4linux.LCDType1.value, LCD4linux.LCDRotate1.value)
	MAX_W = int(MAX_W)
	MAX_H = int(MAX_H)
	L4LElist.setResolution(1, MAX_W, MAX_H)
	pil_open = ""
	col_back = "black"
	if (Standby.inStandby or ConfigStandby) and not self.SonosRunning and not self.YMCastRunning and not self.BlueRunning:
		pil_open = LCD4linux.StandbyLCDBild1.value
		col_back = LCD4linux.StandbyLCDColor1.value
		if ScreenActive[0] in LCD4linux.StandbyBackground1.value and "1" in LCD4linux.StandbyBackground1LCD.value:
			pil_open = LCD4linux.StandbyBackground1Bild.value
			col_back = LCD4linux.StandbyBackground1Color.value
	elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
		pil_open = LCD4linux.MPLCDBild1.value
		col_back = LCD4linux.MPLCDColor1.value
		if ScreenActive[0] in LCD4linux.MPBackground1.value and "1" in LCD4linux.MPBackground1LCD.value:
			pil_open = LCD4linux.MPBackground1Bild.value
			col_back = LCD4linux.MPBackground1Color.value
	else:
		pil_open = LCD4linux.LCDBild1.value
		col_back = LCD4linux.LCDColor1.value
		if ScreenActive[0] in LCD4linux.Background1.value and "1" in LCD4linux.Background1LCD.value:
			pil_open = LCD4linux.Background1Bild.value
			col_back = LCD4linux.Background1Color.value
	if not ("1" in LCD4linux.TVLCD.value and ScreenActive[0] in LCD4linux.TV.value):
		self.im[1] = Image.new('RGB', (MAX_W, MAX_H), col_back)
	self.draw[1] = ImageDraw.Draw(self.im[1])
	checkTVrunning = False
	if getSA(1) in LCD4linux.TV.value and "1" in LCD4linux.TVLCD.value and not Standby.inStandby:
		checkTVrunning = True
		if TVrunning == False:
			doGrabTV(str(MAX_W), str(MAX_H), "1", LCD4linux.TVType.value)
	try:
		pil_image = None
		if pil_open != "" and isfile(pil_open) and not (TVrunning and "1" in LCD4linux.TVLCD.value and ScreenActive[0] in LCD4linux.TV.value):
			if isOffTime(L4LMoon, L4LSun, L4LMoon, L4LSun):
				if isfile(pil_open.replace(pil_open[-4:], "_night" + pil_open[-4:])):
					pil_open = pil_open.replace(pil_open[-4:], "_night" + pil_open[-4:])
					L4logE("Nightbackground", pil_open)
			if LCD4linux.BilderBackground.value == "0":
				pil_image = Image.open(pil_open)
				if pil_image is not None:
					self.im[1].paste(pil_image, (0, 0))
			else:
				if self.BackName[0] != [pil_open, getmtime(pil_open), LCD4linux.BilderBackground.value]:
					self.BackName[0] = [pil_open, getmtime(pil_open), LCD4linux.BilderBackground.value]
					if LCD4linux.BilderBackground.value == "1":
						self.BackIm[0] = Image.open(pil_open).resize((MAX_W, MAX_H), Image.LANCZOS if PY3 else Image.ANTIALIAS).convert("RGB", dither=Image.NONE, palette=Image.ADAPTIVE)
					else:
						self.BackIm[0] = Image.open(pil_open).resize((MAX_W, MAX_H)).convert("P")
					L4log("change Background")
				if self.BackIm[0] is not None:
					self.im[1].paste(self.BackIm[0], (0, 0))
		else:
			self.BackIm[0] = None
			self.BackName[0] = "-"
	except Exception:
		L4log("Error Background1")
	if LCD4linux.LCDType2.value != "00":
		MAX_W, MAX_H = getResolution(LCD4linux.LCDType2.value, LCD4linux.LCDRotate2.value)
		MAX_W = int(MAX_W)
		MAX_H = int(MAX_H)
		L4LElist.setResolution(2, MAX_W, MAX_H)
		pil_open = ""
		col_back = "black"
		if (Standby.inStandby or ConfigStandby) and not self.SonosRunning and not self.YMCastRunning and not self.BlueRunning:
			pil_open = LCD4linux.StandbyLCDBild2.value
			col_back = LCD4linux.StandbyLCDColor2.value
			if ScreenActive[0] in LCD4linux.StandbyBackground1.value and "2" in LCD4linux.StandbyBackground1LCD.value:
				pil_open = LCD4linux.StandbyBackground1Bild.value
				col_back = LCD4linux.StandbyBackground1Color.value
		elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
			pil_open = LCD4linux.MPLCDBild2.value
			col_back = LCD4linux.MPLCDColor2.value
			if ScreenActive[0] in LCD4linux.MPBackground1.value and "2" in LCD4linux.MPBackground1LCD.value:
				pil_open = LCD4linux.MPBackground1Bild.value
				col_back = LCD4linux.MPBackground1Color.value
		else:
			pil_open = LCD4linux.LCDBild2.value
			col_back = LCD4linux.LCDColor2.value
			if ScreenActive[0] in LCD4linux.Background1.value and "2" in LCD4linux.Background1LCD.value:
				pil_open = LCD4linux.Background1Bild.value
				col_back = LCD4linux.Background1Color.value
		if not ("2" in LCD4linux.TVLCD.value and ScreenActive[0] in LCD4linux.TV.value):
			self.im[2] = Image.new('RGB', (MAX_W, MAX_H), col_back)
		self.draw[2] = ImageDraw.Draw(self.im[2])
		if getSA(2) in LCD4linux.TV.value and "2" in LCD4linux.TVLCD.value and not Standby.inStandby:
			checkTVrunning = True
			if TVrunning == False:
				doGrabTV(str(MAX_W), str(MAX_H), "2", LCD4linux.TVType.value)
		try:
			pil_image = None
			if pil_open != "" and isfile(pil_open) and not (TVrunning and "2" in LCD4linux.TVLCD.value and ScreenActive[0] in LCD4linux.TV.value):
				if isOffTime(L4LMoon, L4LSun, L4LMoon, L4LSun):
					if isfile(pil_open.replace(pil_open[-4:], "_night" + pil_open[-4:])):
						pil_open = pil_open.replace(pil_open[-4:], "_night" + pil_open[-4:])
						L4logE("Nightbackground", pil_open)
				if LCD4linux.BilderBackground.value == "0":
					pil_image = Image.open(pil_open)
					if pil_image is not None:
						self.im[2].paste(pil_image, (0, 0))
				else:
					if self.BackName[1] != [pil_open, getmtime(pil_open), LCD4linux.BilderBackground.value]:
						self.BackName[1] = [pil_open, getmtime(pil_open), LCD4linux.BilderBackground.value]
						if self.BackName[1] == self.BackName[0]:
							self.BackIm[1] = self.BackIm[0]
						else:
							if LCD4linux.BilderBackground.value == "1":
								self.BackIm[1] = Image.open(pil_open).resize((MAX_W, MAX_H), Image.LANCZOS if PY3 else Image.ANTIALIAS).convert("RGB", dither=Image.NONE, palette=Image.ADAPTIVE)
							else:
								self.BackIm[1] = Image.open(pil_open).resize((MAX_W, MAX_H)).convert("P")
						L4log("change Background")
					if self.BackIm[1] is not None:
						self.im[2].paste(self.BackIm[1], (0, 0))
			else:
				self.BackIm[1] = None
				self.BackName[1] = "-"
		except Exception:
			L4log("Error Background2")
	if LCD4linux.LCDType3.value != "00":
		MAX_W, MAX_H = getResolution(LCD4linux.LCDType3.value, LCD4linux.LCDRotate3.value)
		MAX_W = int(MAX_W)
		MAX_H = int(MAX_H)
		L4LElist.setResolution(3, MAX_W, MAX_H)
		pil_open = ""
		col_back = "black"
		if (Standby.inStandby or ConfigStandby) and not self.SonosRunning and not self.YMCastRunning and not self.BlueRunning:
			pil_open = LCD4linux.StandbyLCDBild3.value
			col_back = LCD4linux.StandbyLCDColor3.value
			if ScreenActive[0] in LCD4linux.StandbyBackground1.value and "3" in LCD4linux.StandbyBackground1LCD.value:
				pil_open = LCD4linux.StandbyBackground1Bild.value
				col_back = LCD4linux.StandbyBackground1Color.value
		elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
			pil_open = LCD4linux.MPLCDBild3.value
			col_back = LCD4linux.MPLCDColor3.value
			if ScreenActive[0] in LCD4linux.MPBackground1.value and "3" in LCD4linux.MPBackground1LCD.value:
				pil_open = LCD4linux.MPBackground1Bild.value
				col_back = LCD4linux.MPBackground1Color.value
		else:
			pil_open = LCD4linux.LCDBild3.value
			col_back = LCD4linux.LCDColor3.value
			if ScreenActive[0] in LCD4linux.Background1.value and "3" in LCD4linux.Background1LCD.value:
				pil_open = LCD4linux.Background1Bild.value
				col_back = LCD4linux.Background1Color.value
		if not ("3" in LCD4linux.TVLCD.value and ScreenActive[0] in LCD4linux.TV.value):
			self.im[3] = Image.new('RGB', (MAX_W, MAX_H), col_back)
		self.draw[3] = ImageDraw.Draw(self.im[3])
		if getSA(3) in LCD4linux.TV.value and "3" in LCD4linux.TVLCD.value and not Standby.inStandby:
			checkTVrunning = True
			if TVrunning == False:
				doGrabTV(str(MAX_W), str(MAX_H), "3", LCD4linux.TVType.value)
		try:
			pil_image = None
			if pil_open != "" and isfile(pil_open) and not (TVrunning and "3" in LCD4linux.TVLCD.value and ScreenActive[0] in LCD4linux.TV.value):
				if isOffTime(L4LMoon, L4LSun, L4LMoon, L4LSun):
					if isfile(pil_open.replace(pil_open[-4:], "_night" + pil_open[-4:])):
						pil_open = pil_open.replace(pil_open[-4:], "_night" + pil_open[-4:])
						L4logE("Nightbackground", pil_open)
				if LCD4linux.BilderBackground.value == "0":
					pil_image = Image.open(pil_open)
					if pil_image is not None:
						self.im[3].paste(pil_image, (0, 0))
				else:
					if self.BackName[2] != [pil_open, getmtime(pil_open), LCD4linux.BilderBackground.value]:
						self.BackName[2] = [pil_open, getmtime(pil_open), LCD4linux.BilderBackground.value]
						if self.BackName[2] == self.BackName[0]:
							self.BackIm[2] = self.BackIm[0]
						else:
							if LCD4linux.BilderBackground.value == "1":
								self.BackIm[2] = Image.open(pil_open).resize((MAX_W, MAX_H), Image.LANCZOS if PY3 else Image.ANTIALIAS).convert("RGB", dither=Image.NONE, palette=Image.ADAPTIVE)
							else:
								self.BackIm[2] = Image.open(pil_open).resize((MAX_W, MAX_H)).convert("P")
						L4log("change Background")
					if self.BackIm[2] is not None:
						self.im[3].paste(self.BackIm[2], (0, 0))
			else:
				self.BackIm[2] = None
				self.BackName[2] = "-"
		except Exception:
			L4log("Error Background3")
		if TVrunning == True and checkTVrunning == False:
			TVrunning = False
####
#### Standby Modus
####
	if (Standby.inStandby or ConfigStandby) and not self.SonosRunning and not self.YMCastRunning and not self.BlueRunning:
		TVrunning = False
		if str(LCD4linux.Standby.value) == "1":
			if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4" or LCD4linux.LCDType3.value[0] == "4":
				if "C" in LCD4linux.LCDTFT.value:
					if AktTFT != "BMP":
						TFTCheck(False, SetMode="BMP")
				else:
					if AktTFT != "DREAM":
						TFTCheck(False, SetMode="DREAM")
			if str(LCD4linux.StandbyFritz.value) != "0" and str(LCD4linux.FritzPopupLCD.value) != "0" and FritzTime > 1:
# FritzCall
				Para = LCD4linux.StandbyFritzPos.value, LCD4linux.StandbyFritzSize.value, LCD4linux.StandbyFritzColor.value, LCD4linux.StandbyFritzBackColor.value, LCD4linux.StandbyFritzAlign.value, LCD4linux.StandbyFritzType.value, LCD4linux.StandbyFritzPicPos.value, LCD4linux.StandbyFritzPicSize.value, LCD4linux.StandbyFritzPicAlign.value, LCD4linux.StandbyFritzShadow.value, getFont(LCD4linux.StandbyFritzFont.value)
				Lput(LCD4linux.FritzPopupLCD.value, "123456789", putFritz, Para)
			else:
# Bild
				if LCD4linux.StandbyBild.value != "0" and (ScreenActive[0] in LCD4linux.StandbyBild.value or ScreenActive[-3:] != ["", "", ""]):
					ShowPicture = getShowPicture(LCD4linux.StandbyBildFile.value, 0)
					Para = LCD4linux.StandbyBildPos.value, LCD4linux.StandbyBildSize.value, LCD4linux.StandbyBildSizeH.value, LCD4linux.StandbyBildAlign.value, LCD4linux.StandbyBildQuick.value, LCD4linux.StandbyBildTransp.value, 0, ShowPicture, LCD4linux.StandbyBildFile.value
					Lput4(LCD4linux.StandbyBildLCD.value, LCD4linux.StandbyBild.value, putBild, Para)
# Bild 2
				if LCD4linux.StandbyBild2.value != "0" and (ScreenActive[0] in LCD4linux.StandbyBild2.value or ScreenActive[-3:] != ["", "", ""]):
					ShowPicture = getShowPicture(LCD4linux.StandbyBild2File.value, 1)
					Para = LCD4linux.StandbyBild2Pos.value, LCD4linux.StandbyBild2Size.value, LCD4linux.StandbyBild2SizeH.value, LCD4linux.StandbyBild2Align.value, LCD4linux.StandbyBild2Quick.value, LCD4linux.StandbyBild2Transp.value, 0, ShowPicture, LCD4linux.StandbyBild2File.value
					Lput4(LCD4linux.StandbyBild2LCD.value, LCD4linux.StandbyBild2.value, putBild, Para)
# Bild 3
				if LCD4linux.StandbyBild3.value != "0" and (ScreenActive[0] in LCD4linux.StandbyBild3.value or ScreenActive[-3:] != ["", "", ""]):
					ShowPicture = getShowPicture(LCD4linux.StandbyBild3File.value, 2)
					Para = LCD4linux.StandbyBild3Pos.value, LCD4linux.StandbyBild3Size.value, LCD4linux.StandbyBild3SizeH.value, LCD4linux.StandbyBild3Align.value, LCD4linux.StandbyBild3Quick.value, LCD4linux.StandbyBild3Transp.value, 0, ShowPicture, LCD4linux.StandbyBild3File.value
					Lput4(LCD4linux.StandbyBild3LCD.value, LCD4linux.StandbyBild3.value, putBild, Para)
# Bild 4
				if LCD4linux.StandbyBild4.value != "0" and (ScreenActive[0] in LCD4linux.StandbyBild4.value or ScreenActive[-3:] != ["", "", ""]):
					ShowPicture = getShowPicture(LCD4linux.StandbyBild4File.value, 0)
					Para = LCD4linux.StandbyBild4Pos.value, LCD4linux.StandbyBild4Size.value, LCD4linux.StandbyBild4SizeH.value, LCD4linux.StandbyBild4Align.value, LCD4linux.StandbyBild4Quick.value, LCD4linux.StandbyBild4Transp.value, 0, ShowPicture, LCD4linux.StandbyBild4File.value
					Lput4(LCD4linux.StandbyBild4LCD.value, LCD4linux.StandbyBild4.value, putBild, Para)
				Brief1.join()
				Brief2.join()
				Brief3.join()
# Kalender
				Para = LCD4linux.StandbyCalPos.value, LCD4linux.StandbyCalZoom.value, LCD4linux.StandbyCalAlign.value, LCD4linux.StandbyCalSplit.value, LCD4linux.StandbyCalType.value, LCD4linux.StandbyCalTypeE.value, LCD4linux.StandbyCalLayout.value, LCD4linux.StandbyCalColor.value, LCD4linux.StandbyCalBackColor.value, LCD4linux.StandbyCalCaptionColor.value, LCD4linux.StandbyCalShadow.value, getFont(LCD4linux.StandbyCalFont.value)
				Lput(LCD4linux.StandbyCalLCD.value, LCD4linux.StandbyCal.value, putCalendar, Para)
# Termin-List
				Para = LCD4linux.StandbyCalListPos.value, LCD4linux.StandbyCalListSize.value, LCD4linux.StandbyCalListProzent.value, LCD4linux.StandbyCalListAlign.value, LCD4linux.StandbyCalListSplit.value, LCD4linux.StandbyCalListType.value, LCD4linux.StandbyCalListLines.value, LCD4linux.StandbyCalListColor.value, LCD4linux.StandbyCalListShadow.value, getFont(LCD4linux.StandbyCalListFont.value)
				Lput(LCD4linux.StandbyCalListLCD.value, LCD4linux.StandbyCalList.value, putCalendarList, Para)
# MSN Wetter
				if wwwWetter[0] != "":
					Para = LCD4linux.StandbyWetterPos.value, LCD4linux.StandbyWetterZoom.value, LCD4linux.StandbyWetterAlign.value, LCD4linux.StandbyWetterSplit.value, LCD4linux.StandbyWetterType.value, LCD4linux.StandbyWetterColor.value, LCD4linux.StandbyWetterShadow.value, 0, getFont(LCD4linux.StandbyWetterFont.value)
					Lput(LCD4linux.StandbyWetterLCD.value, LCD4linux.StandbyWetter.value, putWetter, Para)
				if wwwWetter[1] != "":
					Para = LCD4linux.StandbyWetter2Pos.value, LCD4linux.StandbyWetter2Zoom.value, LCD4linux.StandbyWetter2Align.value, LCD4linux.StandbyWetter2Split.value, LCD4linux.StandbyWetter2Type.value, LCD4linux.StandbyWetter2Color.value, LCD4linux.StandbyWetter2Shadow.value, 1, getFont(LCD4linux.StandbyWetter2Font.value)
					Lput(LCD4linux.StandbyWetter2LCD.value, LCD4linux.StandbyWetter2.value, putWetter, Para)
				if LCD4linux.WetterTransparenz.value != "true":
					Brief1.join()
					Brief2.join()
					Brief3.join()
# Netatmo CO2
				Para = "CO2", LCD4linux.StandbyNetAtmoCO2Pos.value, LCD4linux.StandbyNetAtmoCO2Size.value, LCD4linux.StandbyNetAtmoCO2Len.value, LCD4linux.StandbyNetAtmoCO2Align.value, LCD4linux.StandbyNetAtmoCO2Split.value, LCD4linux.StandbyNetAtmoCO2Station.value, LCD4linux.StandbyNetAtmoCO2Type.value
				Lput(LCD4linux.StandbyNetAtmoCO2LCD.value, LCD4linux.StandbyNetAtmoCO2.value, putNetatmoIllu, Para)
# Netatmo IDX
				Para = "IDX", LCD4linux.StandbyNetAtmoIDXPos.value, LCD4linux.StandbyNetAtmoIDXSize.value, LCD4linux.StandbyNetAtmoIDXLen.value, LCD4linux.StandbyNetAtmoIDXAlign.value, LCD4linux.StandbyNetAtmoIDXSplit.value, LCD4linux.StandbyNetAtmoIDXStation.value, LCD4linux.StandbyNetAtmoIDXType.value
				Lput(LCD4linux.StandbyNetAtmoIDXLCD.value, LCD4linux.StandbyNetAtmoIDX.value, putNetatmoIllu, Para)
# HTTP WWW Site
				Para = 1, LCD4linux.StandbyWWW1Pos.value, LCD4linux.StandbyWWW1Size.value, LCD4linux.StandbyWWW1Align.value, LCD4linux.StandbyWWW1CutX.value, LCD4linux.StandbyWWW1CutY.value, LCD4linux.StandbyWWW1CutW.value, LCD4linux.StandbyWWW1CutH.value
				Lput(LCD4linux.StandbyWWW1LCD.value, LCD4linux.StandbyWWW1.value, putWWW, Para)
				Brief1.join()
				Brief2.join()
				Brief3.join()
# Netatmo
				Para = LCD4linux.StandbyNetAtmoPos.value, LCD4linux.StandbyNetAtmoSize.value, LCD4linux.StandbyNetAtmoAlign.value, LCD4linux.StandbyNetAtmoSplit.value, LCD4linux.StandbyNetAtmoStation.value, LCD4linux.StandbyNetAtmoModule.value, LCD4linux.StandbyNetAtmoModuleUser.value, LCD4linux.StandbyNetAtmoBasis.value, LCD4linux.StandbyNetAtmoName.value, LCD4linux.StandbyNetAtmoType.value, LCD4linux.StandbyNetAtmoType2.value, [LCD4linux.StandbyNetAtmoColor.value, LCD4linux.StandbyNetAtmoColor2.value, LCD4linux.StandbyNetAtmoColor3.value, LCD4linux.StandbyNetAtmoColor4.value, LCD4linux.StandbyNetAtmoColor5.value, LCD4linux.StandbyNetAtmoColor6.value, LCD4linux.StandbyNetAtmoColor7.value], LCD4linux.StandbyNetAtmoShadow.value, getFont(LCD4linux.StandbyNetAtmoFont.value)
				Lput(LCD4linux.StandbyNetAtmoLCD.value, LCD4linux.StandbyNetAtmo.value, putNetatmo, Para)
				Para = LCD4linux.StandbyNetAtmo2Pos.value, LCD4linux.StandbyNetAtmo2Size.value, LCD4linux.StandbyNetAtmo2Align.value, LCD4linux.StandbyNetAtmo2Split.value, LCD4linux.StandbyNetAtmo2Station.value, LCD4linux.StandbyNetAtmo2Module.value, LCD4linux.StandbyNetAtmo2ModuleUser.value, LCD4linux.StandbyNetAtmo2Basis.value, LCD4linux.StandbyNetAtmo2Name.value, LCD4linux.StandbyNetAtmo2Type.value, LCD4linux.StandbyNetAtmo2Type2.value, [LCD4linux.StandbyNetAtmo2Color.value, LCD4linux.StandbyNetAtmo2Color2.value, LCD4linux.StandbyNetAtmo2Color3.value, LCD4linux.StandbyNetAtmo2Color4.value, LCD4linux.StandbyNetAtmo2Color6.value, LCD4linux.StandbyNetAtmo2Color7.value], LCD4linux.StandbyNetAtmo2Shadow.value, getFont(LCD4linux.StandbyNetAtmo2Font.value)
				Lput(LCD4linux.StandbyNetAtmo2LCD.value, LCD4linux.StandbyNetAtmo2.value, putNetatmo, Para)
# Box 1
				Para = LCD4linux.StandbyBox1x1.value, LCD4linux.StandbyBox1y1.value, LCD4linux.StandbyBox1x2.value, LCD4linux.StandbyBox1y2.value, LCD4linux.StandbyBox1Color.value, LCD4linux.StandbyBox1BackColor.value
				Lput(LCD4linux.StandbyBox1LCD.value, LCD4linux.StandbyBox1.value, putBox, Para)
# Box 2
				Para = LCD4linux.StandbyBox2x1.value, LCD4linux.StandbyBox2y1.value, LCD4linux.StandbyBox2x2.value, LCD4linux.StandbyBox2y2.value, LCD4linux.StandbyBox2Color.value, LCD4linux.StandbyBox2BackColor.value
				Lput(LCD4linux.StandbyBox2LCD.value, LCD4linux.StandbyBox2.value, putBox, Para)
# Moonphase
				Para = LCD4linux.StandbyMoonPos.value, LCD4linux.StandbyMoonSize.value, LCD4linux.StandbyMoonFontSize.value, LCD4linux.StandbyMoonAlign.value, LCD4linux.StandbyMoonInfos.value, LCD4linux.StandbyMoonTrends.value, LCD4linux.StandbyMoonSplit.value, LCD4linux.StandbyMoonColor.value, LCD4linux.StandbyMoonShadow.value, getFont(LCD4linux.StandbyMoonFont.value)
				Lput(LCD4linux.StandbyMoonLCD.value, LCD4linux.StandbyMoon.value, putMoon, Para)
# Meteo station
				if wwwMeteo.find("current_conditions") > 1:
					Para = LCD4linux.StandbyMeteoPos.value, LCD4linux.StandbyMeteoZoom.value, LCD4linux.StandbyMeteoAlign.value, LCD4linux.StandbyMeteoSplit.value, LCD4linux.StandbyMeteoType.value, LCD4linux.StandbyMeteoColor.value
					Lput(LCD4linux.StandbyMeteoLCD.value, LCD4linux.StandbyMeteo.value, putMeteo, Para)
# get clock
				Para = LCD4linux.StandbyClockPos.value, LCD4linux.StandbyClockSize.value, LCD4linux.StandbyClockAlign.value, LCD4linux.StandbyClockSplit.value, LCD4linux.StandbyClockType.value, LCD4linux.StandbyClockSpacing.value, LCD4linux.StandbyClockAnalog.value, LCD4linux.StandbyClockColor.value, LCD4linux.StandbyClockShadow.value, 0, getFont(LCD4linux.StandbyClockFont.value)
				Lput(LCD4linux.StandbyClockLCD.value, LCD4linux.StandbyClock.value, putClock, Para)
				Para = LCD4linux.StandbyClock2Pos.value, LCD4linux.StandbyClock2Size.value, LCD4linux.StandbyClock2Align.value, LCD4linux.StandbyClock2Split.value, LCD4linux.StandbyClock2Type.value, LCD4linux.StandbyClock2Spacing.value, LCD4linux.StandbyClock2Analog.value, LCD4linux.StandbyClock2Color.value, LCD4linux.StandbyClock2Shadow.value, 1, getFont(LCD4linux.StandbyClock2Font.value)
				Lput(LCD4linux.StandbyClock2LCD.value, LCD4linux.StandbyClock2.value, putClock, Para)
# Informationen
				Para = LCD4linux.StandbyInfoPos.value, LCD4linux.StandbyInfoSize.value, LCD4linux.StandbyInfoAlign.value, LCD4linux.StandbyInfoLines.value, LCD4linux.StandbyInfoSplit.value, LCD4linux.StandbyInfoColor.value, LCD4linux.StandbyInfoSensor.value + LCD4linux.StandbyInfoCPU.value, LCD4linux.StandbyInfoShadow.value, getFont(LCD4linux.StandbyInfoFont.value)
				Lput(LCD4linux.StandbyInfoLCD.value, LCD4linux.StandbyInfo.value, putInfo, Para)
				Para = LCD4linux.StandbyInfo2Pos.value, LCD4linux.StandbyInfo2Size.value, LCD4linux.StandbyInfo2Align.value, LCD4linux.StandbyInfo2Lines.value, LCD4linux.StandbyInfo2Split.value, LCD4linux.StandbyInfo2Color.value, LCD4linux.StandbyInfo2Sensor.value + LCD4linux.StandbyInfo2CPU.value, LCD4linux.StandbyInfo2Shadow.value, getFont(LCD4linux.StandbyInfo2Font.value)
				Lput(LCD4linux.StandbyInfo2LCD.value, LCD4linux.StandbyInfo2.value, putInfo, Para)
# Tuner
				Para = LCD4linux.StandbyTunerPos.value, LCD4linux.StandbyTunerSize.value, LCD4linux.StandbyTunerAlign.value, LCD4linux.StandbyTunerSplit.value, LCD4linux.StandbyTunerType.value, LCD4linux.StandbyTunerActive.value, getFont(LCD4linux.StandbyTunerFont.value)
				Lput(LCD4linux.StandbyTunerLCD.value, LCD4linux.StandbyTuner.value, putTuner, Para)
# Online-Ping
				Para = LCD4linux.StandbyPingPos.value, LCD4linux.StandbyPingSize.value, LCD4linux.StandbyPingAlign.value, LCD4linux.StandbyPingSplit.value, LCD4linux.StandbyPingColor.value, LCD4linux.StandbyPingType.value, LCD4linux.StandbyPingShow.value, LCD4linux.StandbyPingTimeout.value, (LCD4linux.StandbyPingName1.value, LCD4linux.StandbyPingName2.value, LCD4linux.StandbyPingName3.value, LCD4linux.StandbyPingName4.value, LCD4linux.StandbyPingName5.value), LCD4linux.StandbyPingShadow.value, getFont(LCD4linux.StandbyPingFont.value)
				Lput(LCD4linux.StandbyPingLCD.value, LCD4linux.StandbyPing.value, putOnline, Para)
# external IP
				Para = LCD4linux.StandbyExternalIpPos.value, LCD4linux.StandbyExternalIpSize.value, getFont(LCD4linux.StandbyExternalIpFont.value), LCD4linux.StandbyExternalIpAlign.value, LCD4linux.StandbyExternalIpSplit.value, LCD4linux.StandbyExternalIpColor.value, LCD4linux.StandbyExternalIpBackColor.value, LCD4linux.StandbyExternalIpShadow.value, self.ExternalIP
				Lput(LCD4linux.StandbyExternalIpLCD.value, LCD4linux.StandbyExternalIp.value, putExternalIP, Para)
# www Remote-Box
				Para = LCD4linux.StandbyRBoxPos.value, LCD4linux.StandbyRBoxSize.value, LCD4linux.StandbyRBoxAlign.value, False, [LCD4linux.StandbyRBoxColor.value, LCD4linux.StandbyRBoxColor2.value, LCD4linux.StandbyRBoxColor3.value, LCD4linux.StandbyRBoxColor4.value, LCD4linux.StandbyRBoxColor5.value], LCD4linux.StandbyRBoxProzent.value, LCD4linux.StandbyRBoxShow.value, LCD4linux.StandbyRBoxShadow.value, getFont(LCD4linux.StandbyRBoxFont.value)
				Lput(LCD4linux.StandbyRBoxLCD.value, LCD4linux.StandbyRBox.value, putRemoteBox, Para)
# www Remote-Timer Record
				Para = 1, LCD4linux.StandbyRBoxTimerPos.value, LCD4linux.StandbyRBoxTimerSize.value, LCD4linux.StandbyRBoxTimerLen.value, LCD4linux.StandbyRBoxTimerLines.value, LCD4linux.StandbyRBoxTimerType.value, LCD4linux.StandbyRBoxTimerType2.value, LCD4linux.StandbyRBoxTimerAlign.value, LCD4linux.StandbyRBoxTimerSplit.value, LCD4linux.StandbyRBoxTimerColor.value, LCD4linux.StandbyRBoxTimerShadow.value, getFont(LCD4linux.StandbyRBoxTimerFont.value)
				Lput(LCD4linux.StandbyRBoxTimerLCD.value, LCD4linux.StandbyRBoxTimer.value, putTimer, Para)
# Timer Record
				Para = 0, LCD4linux.StandbyTimerPos.value, LCD4linux.StandbyTimerSize.value, LCD4linux.StandbyTimerLen.value, LCD4linux.StandbyTimerLines.value, LCD4linux.StandbyTimerType.value, LCD4linux.StandbyTimerType2.value, LCD4linux.StandbyTimerAlign.value, LCD4linux.StandbyTimerSplit.value, LCD4linux.StandbyTimerColor.value, LCD4linux.StandbyTimerShadow.value, getFont(LCD4linux.StandbyTimerFont.value)
				Lput(LCD4linux.StandbyTimerLCD.value, LCD4linux.StandbyTimer.value, putTimer, Para)
# Devices
				Para = LCD4linux.StandbyDevPos.value, LCD4linux.StandbyDevSize.value, LCD4linux.StandbyDevAlign.value, LCD4linux.StandbyDevSplit.value, LCD4linux.StandbyDevColor.value, (LCD4linux.StandbyDevExtra.value, LCD4linux.StandbyDevName1.value, LCD4linux.StandbyDevName2.value, LCD4linux.StandbyDevName3.value, LCD4linux.StandbyDevName4.value, LCD4linux.StandbyDevName5.value), LCD4linux.StandbyDevShadow.value, LCD4linux.StandbyDevType.value, LCD4linux.StandbyDevWarning.value, getFont(LCD4linux.StandbyDevFont.value)
				Lput(LCD4linux.StandbyDevLCD.value, LCD4linux.StandbyDev.value, putDev, Para)
# HDD
				Para = LCD4linux.StandbyHddPos.value, LCD4linux.StandbyHddSize.value, LCD4linux.StandbyHddAlign.value, LCD4linux.StandbyHddSplit.value, LCD4linux.StandbyHddType.value
				Lput(LCD4linux.StandbyHddLCD.value, LCD4linux.StandbyHdd.value, putHdd, Para)
# show OSCAM
				Para = LCD4linux.StandbyOSCAMPos.value, LCD4linux.StandbyOSCAMSize.value, LCD4linux.StandbyOSCAMColor.value, LCD4linux.StandbyOSCAMBackColor.value, LCD4linux.StandbyOSCAMAlign.value, LCD4linux.StandbyOSCAMSplit.value
				Lput(LCD4linux.StandbyOSCAMLCD.value, LCD4linux.StandbyOSCAM.value, putOSCAM, Para)
# show String Text
				Para = LCD4linux.StandbyStringPos.value, LCD4linux.StandbyStringSize.value, getFont(LCD4linux.StandbyStringFont.value), LCD4linux.StandbyStringAlign.value, LCD4linux.StandbyStringSplit.value, LCD4linux.StandbyStringColor.value, LCD4linux.StandbyStringBackColor.value, LCD4linux.StandbyStringShadow.value, LCD4linux.StandbyStringText.value
				Lput(LCD4linux.StandbyStringLCD.value, LCD4linux.StandbyString.value, putString, Para)
				Para = LCD4linux.StandbyString2Pos.value, LCD4linux.StandbyString2Size.value, getFont(LCD4linux.StandbyString2Font.value), LCD4linux.StandbyString2Align.value, LCD4linux.StandbyString2Split.value, LCD4linux.StandbyString2Color.value, LCD4linux.StandbyString2BackColor.value, LCD4linux.StandbyString2Shadow.value, LCD4linux.StandbyString2Text.value
				Lput(LCD4linux.StandbyString2LCD.value, LCD4linux.StandbyString2.value, putString, Para)

# show Textfile
				Para = LCD4linux.StandbyTextPos.value, LCD4linux.StandbyTextSize.value, getFont(LCD4linux.StandbyTextFont.value), LCD4linux.StandbyTextAlign.value, LCD4linux.StandbyTextColor.value, LCD4linux.StandbyTextBackColor.value, LCD4linux.StandbyTextShadow.value, LCD4linux.StandbyTextFile.value
				Lput(LCD4linux.StandbyTextLCD.value, LCD4linux.StandbyText.value, putTextFile, Para)
				Para = LCD4linux.StandbyText2Pos.value, LCD4linux.StandbyText2Size.value, getFont(LCD4linux.StandbyText2Font.value), LCD4linux.StandbyText2Align.value, LCD4linux.StandbyText2Color.value, LCD4linux.StandbyText2BackColor.value, LCD4linux.StandbyText2Shadow.value, LCD4linux.StandbyText2File.value
				Lput(LCD4linux.StandbyText2LCD.value, LCD4linux.StandbyText2.value, putTextFile, Para)
				Para = LCD4linux.StandbyText3Pos.value, LCD4linux.StandbyText3Size.value, getFont(LCD4linux.StandbyText3Font.value), LCD4linux.StandbyText3Align.value, LCD4linux.StandbyText3Color.value, LCD4linux.StandbyText3BackColor.value, LCD4linux.StandbyText3Shadow.value, LCD4linux.StandbyText3File.value
				Lput(LCD4linux.StandbyText3LCD.value, LCD4linux.StandbyText3.value, putTextFile, Para)
# show HTTP Text
				Para = LCD4linux.StandbyHTTPPos.value, LCD4linux.StandbyHTTPSize.value, LCD4linux.StandbyHTTPAlign.value, LCD4linux.StandbyHTTPColor.value, LCD4linux.StandbyHTTPBackColor.value, LCD4linux.StandbyHTTPURL.value, LCD4linux.StandbyHTTPShadow.value, getFont(LCD4linux.StandbyHTTPFont.value)
				Lput(LCD4linux.StandbyHTTPLCD.value, LCD4linux.StandbyHTTP.value, putHTTP, Para)
# show Mail
				Para = LCD4linux.StandbyMailPos.value, LCD4linux.StandbyMailSize.value, LCD4linux.StandbyMailProzent.value, LCD4linux.StandbyMailColor.value, LCD4linux.StandbyMailBackColor.value, LCD4linux.StandbyMailAlign.value, LCD4linux.StandbyMailSplit.value, LCD4linux.StandbyMailLines.value, LCD4linux.StandbyMailType.value, LCD4linux.StandbyMailKonto.value, LCD4linux.StandbyMailShadow.value, getFont(LCD4linux.StandbyMailFont.value)
				Lput(LCD4linux.StandbyMailLCD.value, LCD4linux.StandbyMail.value, putMail, Para)
# show Ereignis Icon Bar
				Para = LCD4linux.StandbyIconBarPos.value, LCD4linux.StandbyIconBarSize.value, LCD4linux.StandbyIconBarAlign.value, LCD4linux.StandbyIconBarSplit.value, LCD4linux.StandbyIconBarType.value, LCD4linux.StandbyIconBarPopup.value, LCD4linux.StandbyIconBarPopupLCD.value
				Lput(LCD4linux.StandbyIconBarLCD.value, LCD4linux.StandbyIconBar.value, putIconBar, Para)
# show Sonnenaufgang
				Para = LCD4linux.StandbySunPos.value, LCD4linux.StandbySunSize.value, LCD4linux.StandbySunColor.value, LCD4linux.StandbySunBackColor.value, LCD4linux.StandbySunAlign.value, LCD4linux.StandbySunSplit.value, LCD4linux.StandbySunType.value, LCD4linux.StandbySunShadow.value, getFont(LCD4linux.StandbySunFont.value)
				Lput(LCD4linux.StandbySunLCD.value, LCD4linux.StandbySun.value, putSun, Para)

# externe Elementeliste
				putL4LElist("Idle")

# FritzCall
				Para = LCD4linux.StandbyFritzPos.value, LCD4linux.StandbyFritzSize.value, LCD4linux.StandbyFritzColor.value, LCD4linux.StandbyFritzBackColor.value, LCD4linux.StandbyFritzAlign.value, LCD4linux.StandbyFritzType.value, LCD4linux.StandbyFritzPicPos.value, LCD4linux.StandbyFritzPicSize.value, LCD4linux.StandbyFritzPicAlign.value, LCD4linux.StandbyFritzShadow.value, getFont(LCD4linux.StandbyFritzFont.value)
				Lput(LCD4linux.StandbyFritzLCD.value, LCD4linux.StandbyFritz.value, putFritz, Para)
# Recording
				Para = LCD4linux.StandbyRecordingPos.value, LCD4linux.StandbyRecordingSize.value, LCD4linux.StandbyRecordingAlign.value, LCD4linux.StandbyRecordingSplit.value, LCD4linux.StandbyRecordingType.value
				Lput(LCD4linux.StandbyRecordingLCD.value, LCD4linux.StandbyRecording.value, putRecording, Para)
# LCDoff
			if isOffTime(LCD4linux.StandbyLCDoff.value, LCD4linux.StandbyLCDon.value, LCD4linux.StandbyLCDWEoff.value, LCD4linux.StandbyLCDWEon.value) or LCDon == False or self.AutoOFF == -1:
				Dunkel = writeHelligkeit([0, 0, 0], [0, 0, 0], False)
				L4log("LCD on", "%s" % LCDon)
			else:
				Dunkel = writeHelligkeit([LCD4linux.StandbyHelligkeit.value, LCD4linux.StandbyHelligkeit2.value, LCD4linux.StandbyHelligkeit3.value], [LCD4linux.StandbyNight.value, LCD4linux.StandbyNight2.value, LCD4linux.StandbyNight3.value], False)
		else:
			Dunkel = writeHelligkeit([0, 0, 0], [0, 0, 0], False)

####
#### MediaPlayer
####
	elif (isMediaPlayer != "" and isMediaPlayer != "radio"):
		if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4" or LCD4linux.LCDType3.value[0] == "4":
			if "B" in LCD4linux.LCDTFT.value:
				if AktTFT != "BMP":
					TFTCheck(False, SetMode="BMP")
			else:
				if AktTFT != "DREAM":
					TFTCheck(False, SetMode="DREAM")
# FritzCall
		if LCD4linux.MPFritz.value != "0" and LCD4linux.FritzPopupLCD.value != "0" and FritzTime > 1:
			Para = LCD4linux.MPFritzPos.value, LCD4linux.MPFritzSize.value, LCD4linux.MPFritzColor.value, LCD4linux.MPFritzBackColor.value, LCD4linux.MPFritzAlign.value, LCD4linux.MPFritzType.value, LCD4linux.MPFritzPicPos.value, LCD4linux.MPFritzPicSize.value, LCD4linux.MPFritzPicAlign.value, LCD4linux.MPFritzShadow.value, getFont(LCD4linux.MPFritzFont.value)
			Lput(LCD4linux.FritzPopupLCD.value, "123456789", putFritz, Para)
		else:
# Bild
			if LCD4linux.MPBild.value != "0" and (ScreenActive[0] in LCD4linux.MPBild.value or ScreenActive[-3:] != ["", "", ""]):
				ShowPicture = getShowPicture(LCD4linux.MPBildFile.value, 0)
				Para = LCD4linux.MPBildPos.value, LCD4linux.MPBildSize.value, LCD4linux.MPBildSizeH.value, LCD4linux.MPBildAlign.value, LCD4linux.MPBildQuick.value, LCD4linux.MPBildTransp.value, 0, ShowPicture, LCD4linux.MPBildFile.value
				Lput4(LCD4linux.MPBildLCD.value, LCD4linux.MPBild.value, putBild, Para)
# Bild 2
			if LCD4linux.MPBild2.value != "0" and (ScreenActive[0] in LCD4linux.MPBild2.value or ScreenActive[-3:] != ["", "", ""]):
				ShowPicture = getShowPicture(LCD4linux.MPBild2File.value, 1)
				Para = LCD4linux.MPBild2Pos.value, LCD4linux.MPBild2Size.value, LCD4linux.MPBild2SizeH.value, LCD4linux.MPBild2Align.value, LCD4linux.MPBild2Quick.value, LCD4linux.MPBild2Transp.value, 0, ShowPicture, LCD4linux.MPBild2File.value
				Lput4(LCD4linux.MPBild2LCD.value, LCD4linux.MPBild2.value, putBild, Para)
# Cover
			if LCD4linux.MPCover.value != "0" and (ScreenActive[0] in LCD4linux.MPCover.value or ScreenActive[-3:] != ["", "", ""]):
				Para = LCD4linux.MPCoverPos.value, LCD4linux.MPCoverSize.value, LCD4linux.MPCoverSizeH.value, LCD4linux.MPCoverAlign.value, LCD4linux.MPCoverTransp.value, LCD4linux.MPCoverTrim.value
				Lput4(LCD4linux.MPCoverLCD.value, LCD4linux.MPCover.value, putCover, Para)
			Brief1.join()
			Brief2.join()
			Brief3.join()
# Kalender
			Para = LCD4linux.MPCalPos.value, LCD4linux.MPCalZoom.value, LCD4linux.MPCalAlign.value, LCD4linux.MPCalSplit.value, LCD4linux.MPCalType.value, LCD4linux.MPCalTypeE.value, LCD4linux.MPCalLayout.value, LCD4linux.MPCalColor.value, LCD4linux.MPCalBackColor.value, LCD4linux.MPCalCaptionColor.value, LCD4linux.MPCalShadow.value, getFont(LCD4linux.MPCalFont.value)
			Lput(LCD4linux.MPCalLCD.value, LCD4linux.MPCal.value, putCalendar, Para)
# Termin-List
			Para = LCD4linux.MPCalListPos.value, LCD4linux.MPCalListSize.value, LCD4linux.MPCalListProzent.value, LCD4linux.MPCalListAlign.value, LCD4linux.MPCalListSplit.value, LCD4linux.MPCalListType.value, LCD4linux.MPCalListLines.value, LCD4linux.MPCalListColor.value, LCD4linux.MPCalListShadow.value, getFont(LCD4linux.MPCalFont.value)
			Lput(LCD4linux.MPCalListLCD.value, LCD4linux.MPCalList.value, putCalendarList, Para)
# MSN Wetter
			if wwwWetter[0] != "":
				Para = LCD4linux.MPWetterPos.value, LCD4linux.MPWetterZoom.value, LCD4linux.MPWetterAlign.value, LCD4linux.MPWetterSplit.value, LCD4linux.MPWetterType.value, LCD4linux.MPWetterColor.value, LCD4linux.MPWetterShadow.value, 0, getFont(LCD4linux.MPWetterFont.value)
				Lput(LCD4linux.MPWetterLCD.value, LCD4linux.MPWetter.value, putWetter, Para)
			if wwwWetter[1] != "":
				Para = LCD4linux.MPWetter2Pos.value, LCD4linux.MPWetter2Zoom.value, LCD4linux.MPWetter2Align.value, LCD4linux.MPWetter2Split.value, LCD4linux.MPWetter2Type.value, LCD4linux.MPWetter2Color.value, LCD4linux.MPWetter2Shadow.value, 1, getFont(LCD4linux.MPWetter2Font.value)
				Lput(LCD4linux.MPWetter2LCD.value, LCD4linux.MPWetter2.value, putWetter, Para)
			if LCD4linux.WetterTransparenz.value != "true":
				Brief1.join()
				Brief2.join()
				Brief3.join()
# Netatmo CO2
			Para = "CO2", LCD4linux.MPNetAtmoCO2Pos.value, LCD4linux.MPNetAtmoCO2Size.value, LCD4linux.MPNetAtmoCO2Len.value, LCD4linux.MPNetAtmoCO2Align.value, LCD4linux.MPNetAtmoCO2Split.value, LCD4linux.MPNetAtmoCO2Station.value, LCD4linux.MPNetAtmoCO2Type.value
			Lput(LCD4linux.MPNetAtmoCO2LCD.value, LCD4linux.MPNetAtmoCO2.value, putNetatmoIllu, Para)
# Netatmo IDX
			Para = "IDX", LCD4linux.MPNetAtmoIDXPos.value, LCD4linux.MPNetAtmoIDXSize.value, LCD4linux.MPNetAtmoIDXLen.value, LCD4linux.MPNetAtmoIDXAlign.value, LCD4linux.MPNetAtmoIDXSplit.value, LCD4linux.MPNetAtmoIDXStation.value, LCD4linux.MPNetAtmoIDXType.value
			Lput(LCD4linux.MPNetAtmoIDXLCD.value, LCD4linux.MPNetAtmoIDX.value, putNetatmoIllu, Para)
# Netatmo
			Para = LCD4linux.MPNetAtmoPos.value, LCD4linux.MPNetAtmoSize.value, LCD4linux.MPNetAtmoAlign.value, LCD4linux.MPNetAtmoSplit.value, LCD4linux.MPNetAtmoStation.value, LCD4linux.MPNetAtmoModule.value, LCD4linux.MPNetAtmoModuleUser.value, LCD4linux.MPNetAtmoBasis.value, LCD4linux.MPNetAtmoName.value, LCD4linux.MPNetAtmoType.value, LCD4linux.MPNetAtmoType2.value, [LCD4linux.MPNetAtmoColor.value, LCD4linux.MPNetAtmoColor2.value, LCD4linux.MPNetAtmoColor3.value, LCD4linux.MPNetAtmoColor4.value, LCD4linux.MPNetAtmoColor5.value, LCD4linux.MPNetAtmoColor6.value, LCD4linux.MPNetAtmoColor7.value], LCD4linux.MPNetAtmoShadow.value, getFont(LCD4linux.MPNetAtmoFont.value)
			Lput(LCD4linux.MPNetAtmoLCD.value, LCD4linux.MPNetAtmo.value, putNetatmo, Para)
			Para = LCD4linux.MPNetAtmo2Pos.value, LCD4linux.MPNetAtmo2Size.value, LCD4linux.MPNetAtmo2Align.value, LCD4linux.MPNetAtmo2Split.value, LCD4linux.MPNetAtmo2Station.value, LCD4linux.MPNetAtmo2Module.value, LCD4linux.MPNetAtmo2ModuleUser.value, LCD4linux.MPNetAtmo2Basis.value, LCD4linux.MPNetAtmo2Name.value, LCD4linux.MPNetAtmo2Type.value, LCD4linux.MPNetAtmo2Type2.value, [LCD4linux.MPNetAtmo2Color.value, LCD4linux.MPNetAtmo2Color2.value, LCD4linux.MPNetAtmo2Color3.value, LCD4linux.MPNetAtmo2Color4.value, LCD4linux.MPNetAtmo2Color5.value, LCD4linux.MPNetAtmo2Color6.value, LCD4linux.MPNetAtmo2Color7.value], LCD4linux.MPNetAtmo2Shadow.value, getFont(LCD4linux.MPNetAtmo2Font.value)
			Lput(LCD4linux.MPNetAtmo2LCD.value, LCD4linux.MPNetAtmo2.value, putNetatmo, Para)
# Meteo station
			if wwwMeteo.find("current_conditions") > 1:
				Para = LCD4linux.MPMeteoPos.value, LCD4linux.MPMeteoZoom.value, LCD4linux.MPMeteoAlign.value, LCD4linux.MPMeteoSplit.value, LCD4linux.MPMeteoType.value, LCD4linux.MPMeteoColor.value
				Lput(LCD4linux.MPMeteoLCD.value, LCD4linux.MPMeteo.value, putMeteo, Para)
# Box 1
			Para = LCD4linux.MPBox1x1.value, LCD4linux.MPBox1y1.value, LCD4linux.MPBox1x2.value, LCD4linux.MPBox1y2.value, LCD4linux.MPBox1Color.value, LCD4linux.MPBox1BackColor.value
			Lput(LCD4linux.MPBox1LCD.value, LCD4linux.MPBox1.value, putBox, Para)
# Box 2
			Para = LCD4linux.MPBox2x1.value, LCD4linux.MPBox2y1.value, LCD4linux.MPBox2x2.value, LCD4linux.MPBox2y2.value, LCD4linux.MPBox2Color.value, LCD4linux.MPBox2BackColor.value
			Lput(LCD4linux.MPBox2LCD.value, LCD4linux.MPBox2.value, putBox, Para)
# Progress Bar
			Para = LCD4linux.MPProgressPos.value, LCD4linux.MPProgressSize.value, LCD4linux.MPProgressLen.value, LCD4linux.MPProgressType.value, LCD4linux.MPProgressColor.value, LCD4linux.MPProgressColorText.value, LCD4linux.MPProgressAlign.value, LCD4linux.MPProgressMinutes.value, LCD4linux.MPProgressBorder.value, LCD4linux.MPProgressShadow.value, LCD4linux.MPProgressShadow2.value, getFont(LCD4linux.MPProgressFont.value)
			Lput(LCD4linux.MPProgressLCD.value, LCD4linux.MPProgress.value, putProgress, Para)
# Volume
			Para = LCD4linux.MPVolPos.value, LCD4linux.MPVolSize.value, LCD4linux.MPVolLen.value, LCD4linux.MPVolAlign.value, LCD4linux.MPVolSplit.value, LCD4linux.MPVolColor.value, LCD4linux.MPVolShadow.value
			Lput(LCD4linux.MPVolLCD.value, LCD4linux.MPVol.value, putVol, Para)
# extended Description
			Para = LCD4linux.MPDescPos.value, LCD4linux.MPDescSize.value, LCD4linux.MPDescLen.value, LCD4linux.MPDescLines.value, LCD4linux.MPDescColor.value, LCD4linux.MPDescAlign.value, LCD4linux.MPDescSplit.value, LCD4linux.MPDescType.value, LCD4linux.MPDescShadow.value, LCD4linux.MPDescUseInfo.value, getFont(LCD4linux.MPDescFont.value)
			Lput(LCD4linux.MPDescLCD.value, LCD4linux.MPDesc.value, putDescription, Para)
# Title
			Para = LCD4linux.MPTitlePos.value, LCD4linux.MPTitleSize.value, LCD4linux.MPTitleLen.value, LCD4linux.MPTitleLines.value, LCD4linux.MPTitleColor.value, LCD4linux.MPTitleAlign.value, LCD4linux.MPTitleSplit.value, LCD4linux.MPTitleShadow.value, getFont(LCD4linux.MPTitleFont.value)
			Lput(LCD4linux.MPTitleLCD.value, LCD4linux.MPTitle.value, putTitle, Para)
# Comm
			Para = LCD4linux.MPCommPos.value, LCD4linux.MPCommSize.value, LCD4linux.MPCommLen.value, LCD4linux.MPCommLines.value, LCD4linux.MPCommColor.value, LCD4linux.MPCommAlign.value, LCD4linux.MPCommSplit.value, LCD4linux.MPCommShadow.value, getFont(LCD4linux.MPCommFont.value)
			Lput(LCD4linux.MPCommLCD.value, LCD4linux.MPComm.value, putComm, Para)
# aktive Sendername
			Para = LCD4linux.MPChannelPos.value, LCD4linux.MPChannelSize.value, LCD4linux.MPChannelLen.value, LCD4linux.MPChannelLines.value, LCD4linux.MPChannelAlign.value, LCD4linux.MPChannelSplit.value, LCD4linux.MPChannelColor.value, LCD4linux.MPChannelShadow.value, getFont(LCD4linux.MPChannelFont.value)
			Lput(LCD4linux.MPChannelLCD.value, LCD4linux.MPChannel.value, putChannel, Para)
# aktive Event
			Para = LCD4linux.MPProgPos.value, LCD4linux.MPProgSize.value, LCD4linux.MPProgLen.value, LCD4linux.MPProgLines.value, LCD4linux.MPProgType.value, LCD4linux.MPProgColor.value, LCD4linux.MPProgAlign.value, LCD4linux.MPProgSplit.value, LCD4linux.MPProgShadow.value, getFont(LCD4linux.MPProgFont.value)
			Lput(LCD4linux.MPProgLCD.value, LCD4linux.MPProg.value, putProg, Para)
# next Event
			Para = LCD4linux.MPProgNextPos.value, LCD4linux.MPProgNextSize.value, LCD4linux.MPProgNextLen.value, LCD4linux.MPProgNextLines.value, LCD4linux.MPProgNextType.value, LCD4linux.MPProgNextColor.value, LCD4linux.MPProgNextAlign.value, LCD4linux.MPProgNextSplit.value, LCD4linux.MPProgNextShadow.value, getFont(LCD4linux.MPProgNextFont.value)
			Lput(LCD4linux.MPProgNextLCD.value, LCD4linux.MPProgNext.value, putProgNext, Para)
# get clock
			Para = LCD4linux.MPClockPos.value, LCD4linux.MPClockSize.value, LCD4linux.MPClockAlign.value, LCD4linux.MPClockSplit.value, LCD4linux.MPClockType.value, LCD4linux.MPClockSpacing.value, LCD4linux.MPClockAnalog.value, LCD4linux.MPClockColor.value, LCD4linux.MPClockShadow.value, 0, getFont(LCD4linux.MPClockFont.value)
			Lput(LCD4linux.MPClockLCD.value, LCD4linux.MPClock.value, putClock, Para)
			Para = LCD4linux.MPClock2Pos.value, LCD4linux.MPClock2Size.value, LCD4linux.MPClock2Align.value, LCD4linux.MPClock2Split.value, LCD4linux.MPClock2Type.value, LCD4linux.MPClock2Spacing.value, LCD4linux.MPClock2Analog.value, LCD4linux.MPClock2Color.value, LCD4linux.MPClock2Shadow.value, 1, getFont(LCD4linux.MPClock2Font.value)
			Lput(LCD4linux.MPClock2LCD.value, LCD4linux.MPClock2.value, putClock, Para)
# Informationen
			Para = LCD4linux.MPInfoPos.value, LCD4linux.MPInfoSize.value, LCD4linux.MPInfoAlign.value, LCD4linux.MPInfoLines.value, LCD4linux.MPInfoSplit.value, LCD4linux.MPInfoColor.value, LCD4linux.MPInfoSensor.value + LCD4linux.MPInfoCPU.value, LCD4linux.MPInfoShadow.value, getFont(LCD4linux.MPInfoFont.value)
			Lput(LCD4linux.MPInfoLCD.value, LCD4linux.MPInfo.value, putInfo, Para)
			Para = LCD4linux.MPInfo2Pos.value, LCD4linux.MPInfo2Size.value, LCD4linux.MPInfo2Align.value, LCD4linux.MPInfo2Lines.value, LCD4linux.MPInfo2Split.value, LCD4linux.MPInfo2Color.value, LCD4linux.MPInfo2Sensor.value + LCD4linux.MPInfo2CPU.value, LCD4linux.MPInfo2Shadow.value, getFont(LCD4linux.MPInfo2Font.value)
			Lput(LCD4linux.MPInfo2LCD.value, LCD4linux.MPInfo2.value, putInfo, Para)
# Timer Record
			Para = 0, LCD4linux.MPTimerPos.value, LCD4linux.MPTimerSize.value, LCD4linux.MPTimerLen.value, LCD4linux.MPTimerLines.value, LCD4linux.MPTimerType.value, LCD4linux.MPTimerType2.value, LCD4linux.MPTimerAlign.value, LCD4linux.MPTimerSplit.value, LCD4linux.MPTimerColor.value, LCD4linux.MPTimerShadow.value, getFont(LCD4linux.MPTimerFont.value)
			Lput(LCD4linux.MPTimerLCD.value, LCD4linux.MPTimer.value, putTimer, Para)
# Tuner
			Para = LCD4linux.MPTunerPos.value, LCD4linux.MPTunerSize.value, LCD4linux.MPTunerAlign.value, LCD4linux.MPTunerSplit.value, LCD4linux.MPTunerType.value, LCD4linux.MPTunerActive.value, getFont(LCD4linux.MPTunerFont.value)
			Lput(LCD4linux.MPTunerLCD.value, LCD4linux.MPTuner.value, putTuner, Para)
# Audio/Video
			Para = LCD4linux.MPAVPos.value, LCD4linux.MPAVSize.value, LCD4linux.MPAVAlign.value, LCD4linux.MPAVSplit.value, LCD4linux.MPAVColor.value, LCD4linux.MPAVShadow.value, LCD4linux.MPAVType.value, getFont(LCD4linux.MPAVFont.value)
			Lput(LCD4linux.MPAVLCD.value, LCD4linux.MPAV.value, putAV, Para)
# Bitrate
			Para = LCD4linux.MPBitratePos.value, LCD4linux.MPBitrateSize.value, LCD4linux.MPBitrateAlign.value, LCD4linux.MPBitrateSplit.value, LCD4linux.MPBitrateColor.value, LCD4linux.MPBitrateShadow.value, getFont(LCD4linux.MPBitrateFont.value)
			Lput(LCD4linux.MPBitrateLCD.value, LCD4linux.MPBitrate.value, putBitrate, Para)
# Moonphase
			Para = LCD4linux.MPMoonPos.value, LCD4linux.MPMoonSize.value, LCD4linux.MPMoonFontSize.value, LCD4linux.MPMoonAlign.value, LCD4linux.MPMoonInfos.value, LCD4linux.MPMoonTrends.value, LCD4linux.MPMoonSplit.value, LCD4linux.MPMoonColor.value, LCD4linux.MPMoonShadow.value, getFont(LCD4linux.MPMoonFont.value)
			Lput(LCD4linux.MPMoonLCD.value, LCD4linux.MPMoon.value, putMoon, Para)
# Online-Ping
			Para = LCD4linux.MPPingPos.value, LCD4linux.MPPingSize.value, LCD4linux.MPPingAlign.value, LCD4linux.MPPingSplit.value, LCD4linux.MPPingColor.value, LCD4linux.MPPingType.value, LCD4linux.MPPingShow.value, LCD4linux.MPPingTimeout.value, (LCD4linux.MPPingName1.value, LCD4linux.MPPingName2.value, LCD4linux.MPPingName3.value, LCD4linux.MPPingName4.value, LCD4linux.MPPingName5.value), LCD4linux.MPPingShadow.value, getFont(LCD4linux.MPPingFont.value)
			Lput(LCD4linux.MPPingLCD.value, LCD4linux.MPPing.value, putOnline, Para)
# external IP
			Para = LCD4linux.MPExternalIpPos.value, LCD4linux.MPExternalIpSize.value, getFont(LCD4linux.MPExternalIpFont.value), LCD4linux.MPExternalIpAlign.value, LCD4linux.MPExternalIpSplit.value, LCD4linux.MPExternalIpColor.value, LCD4linux.MPExternalIpBackColor.value, LCD4linux.MPExternalIpShadow.value, self.ExternalIP
			Lput(LCD4linux.MPExternalIpLCD.value, LCD4linux.MPExternalIp.value, putExternalIP, Para)
# www Remote-Box
			Para = LCD4linux.MPRBoxPos.value, LCD4linux.MPRBoxSize.value, LCD4linux.MPRBoxAlign.value, False, [LCD4linux.MPRBoxColor.value, LCD4linux.MPRBoxColor2.value, LCD4linux.MPRBoxColor3.value, LCD4linux.MPRBoxColor4.value, LCD4linux.MPRBoxColor5.value], LCD4linux.MPRBoxProzent.value, LCD4linux.MPRBoxShow.value, LCD4linux.MPRBoxShadow.value, getFont(LCD4linux.MPRBoxFont.value)
			Lput(LCD4linux.MPRBoxLCD.value, LCD4linux.MPRBox.value, putRemoteBox, Para)
# www Remote-Timer Record
			Para = 1, LCD4linux.MPRBoxTimerPos.value, LCD4linux.MPRBoxTimerSize.value, LCD4linux.MPRBoxTimerLen.value, LCD4linux.MPRBoxTimerLines.value, LCD4linux.MPRBoxTimerType.value, LCD4linux.MPRBoxTimerType2.value, LCD4linux.MPRBoxTimerAlign.value, LCD4linux.MPRBoxTimerSplit.value, LCD4linux.MPRBoxTimerColor.value, LCD4linux.MPRBoxTimerShadow.value, getFont(LCD4linux.MPRBoxTimerFont.value)
			Lput(LCD4linux.MPRBoxTimerLCD.value, LCD4linux.MPRBoxTimer.value, putTimer, Para)
# Devices
			Para = LCD4linux.MPDevPos.value, LCD4linux.MPDevSize.value, LCD4linux.MPDevAlign.value, LCD4linux.MPDevSplit.value, LCD4linux.MPDevColor.value, (LCD4linux.MPDevExtra.value, LCD4linux.MPDevName1.value, LCD4linux.MPDevName2.value, LCD4linux.MPDevName3.value, LCD4linux.MPDevName4.value, LCD4linux.MPDevName5.value), LCD4linux.MPDevShadow.value, LCD4linux.MPDevType.value, LCD4linux.MPDevWarning.value, getFont(LCD4linux.MPDevFont.value)
			Lput(LCD4linux.MPDevLCD.value, LCD4linux.MPDev.value, putDev, Para)
# HDD
			Para = LCD4linux.MPHddPos.value, LCD4linux.MPHddSize.value, LCD4linux.MPHddAlign.value, LCD4linux.MPHddSplit.value, LCD4linux.MPHddType.value
			Lput(LCD4linux.MPHddLCD.value, LCD4linux.MPHdd.value, putHdd, Para)
# Mute
			Para = LCD4linux.MPMutePos.value, LCD4linux.MPMuteSize.value, LCD4linux.MPMuteAlign.value, LCD4linux.MPMuteSplit.value
			Lput(LCD4linux.MPMuteLCD.value, LCD4linux.MPMute.value, putMute, Para)
# show OSCAM
			Para = LCD4linux.MPOSCAMPos.value, LCD4linux.MPOSCAMSize.value, LCD4linux.MPOSCAMColor.value, LCD4linux.MPOSCAMBackColor.value, LCD4linux.MPOSCAMAlign.value, LCD4linux.MPOSCAMSplit.value
			Lput(LCD4linux.MPOSCAMLCD.value, LCD4linux.MPOSCAM.value, putOSCAM, Para)
# show String Text
			Para = LCD4linux.MPStringPos.value, LCD4linux.MPStringSize.value, getFont(LCD4linux.MPStringFont.value), LCD4linux.MPStringAlign.value, LCD4linux.MPStringSplit.value, LCD4linux.MPStringColor.value, LCD4linux.MPStringBackColor.value, LCD4linux.MPStringShadow.value, LCD4linux.MPStringText.value
			Lput(LCD4linux.MPStringLCD.value, LCD4linux.MPString.value, putString, Para)
			Para = LCD4linux.MPString2Pos.value, LCD4linux.MPString2Size.value, getFont(LCD4linux.MPString2Font.value), LCD4linux.MPString2Align.value, LCD4linux.MPString2Split.value, LCD4linux.MPString2Color.value, LCD4linux.MPString2BackColor.value, LCD4linux.MPString2Shadow.value, LCD4linux.MPString2Text.value
			Lput(LCD4linux.MPString2LCD.value, LCD4linux.MPString2.value, putString, Para)
# show Textfile
			Para = LCD4linux.MPTextPos.value, LCD4linux.MPTextSize.value, getFont(LCD4linux.MPTextFont.value), LCD4linux.MPTextAlign.value, LCD4linux.MPTextColor.value, LCD4linux.MPTextBackColor.value, LCD4linux.MPTextShadow.value, LCD4linux.MPTextFile.value
			Lput(LCD4linux.MPTextLCD.value, LCD4linux.MPText.value, putTextFile, Para)
			Para = LCD4linux.MPText2Pos.value, LCD4linux.MPText2Size.value, getFont(LCD4linux.MPText2Font.value), LCD4linux.MPText2Align.value, LCD4linux.MPText2Color.value, LCD4linux.MPText2BackColor.value, LCD4linux.MPText2Shadow.value, LCD4linux.MPText2File.value
			Lput(LCD4linux.MPText2LCD.value, LCD4linux.MPText2.value, putTextFile, Para)
# show Mail
			Para = LCD4linux.MPMailPos.value, LCD4linux.MPMailSize.value, LCD4linux.MPMailProzent.value, LCD4linux.MPMailColor.value, LCD4linux.MPMailBackColor.value, LCD4linux.MPMailAlign.value, LCD4linux.MPMailSplit.value, LCD4linux.MPMailLines.value, LCD4linux.MPMailType.value, LCD4linux.MPMailKonto.value, LCD4linux.MPMailShadow.value, getFont(LCD4linux.MPMailFont.value)
			Lput(LCD4linux.MPMailLCD.value, LCD4linux.MPMail.value, putMail, Para)
# show Ereignis Icon Bar
			Para = LCD4linux.MPIconBarPos.value, LCD4linux.MPIconBarSize.value, LCD4linux.MPIconBarAlign.value, LCD4linux.MPIconBarSplit.value, LCD4linux.MPIconBarType.value, LCD4linux.MPIconBarPopup.value, LCD4linux.MPIconBarPopupLCD.value
			Lput(LCD4linux.MPIconBarLCD.value, LCD4linux.MPIconBar.value, putIconBar, Para)
# show Sonnenaufgang
			Para = LCD4linux.MPSunPos.value, LCD4linux.MPSunSize.value, LCD4linux.MPSunColor.value, LCD4linux.MPSunBackColor.value, LCD4linux.MPSunAlign.value, LCD4linux.MPSunSplit.value, LCD4linux.MPSunType.value, LCD4linux.MPSunShadow.value, getFont(LCD4linux.MPSunFont.value)
			Lput(LCD4linux.MPSunLCD.value, LCD4linux.MPSun.value, putSun, Para)

# externe Elementeliste
			putL4LElist("Media")

# FritzCall
			Para = LCD4linux.MPFritzPos.value, LCD4linux.MPFritzSize.value, LCD4linux.MPFritzColor.value, LCD4linux.MPFritzBackColor.value, LCD4linux.MPFritzAlign.value, LCD4linux.MPFritzType.value, LCD4linux.MPFritzPicPos.value, LCD4linux.MPFritzPicSize.value, LCD4linux.MPFritzPicAlign.value, LCD4linux.MPFritzShadow.value, getFont(LCD4linux.MPFritzFont.value)
			Lput(LCD4linux.MPFritzLCD.value, LCD4linux.MPFritz.value, putFritz, Para)
# Recording
			Para = LCD4linux.MPRecordingPos.value, LCD4linux.MPRecordingSize.value, LCD4linux.MPRecordingAlign.value, LCD4linux.MPRecordingSplit.value, LCD4linux.MPRecordingType.value
			Lput(LCD4linux.MPRecordingLCD.value, LCD4linux.MPRecording.value, putRecording, Para)
# show OSD
			if str(LCD4linux.OSD.value) != "0" and ConfigMode == False and FritzTime == 0:
				if OSDon >= 2 and "M" in LCD4linux.OSDshow.value:
					if "1" in LCD4linux.OSDLCD.value:
						Brief1.put([putGrab, LCD4linux.OSDfast.value, LCD4linux.OSDsize.value, 1, 1])
					if "2" in LCD4linux.OSDLCD.value and LCD4linux.LCDType2.value != "00":
						Brief2.put([putGrab, LCD4linux.OSDfast.value, LCD4linux.OSDsize.value, 2, 2])
					if "3" in LCD4linux.OSDLCD.value and LCD4linux.LCDType3.value != "00":
						Brief3.put([putGrab, LCD4linux.OSDfast.value, LCD4linux.OSDsize.value, 3, 3])
					if OSDon == 3:
						OSDon = 2
# LCDoff
		if isOffTime(LCD4linux.LCDoff.value, LCD4linux.LCDon.value, LCD4linux.LCDWEoff.value, LCD4linux.LCDWEon.value) or LCDon == False or self.AutoOFF == -1:
			Dunkel = writeHelligkeit([0, 0, 0], [0, 0, 0], False)
			L4log("LCD on", "%s" % LCDon)
		else:
			Dunkel = writeHelligkeit([LCD4linux.MPHelligkeit.value, LCD4linux.MPHelligkeit2.value, LCD4linux.MPHelligkeit3.value], [LCD4linux.MPNight.value, LCD4linux.MPNight2.value, LCD4linux.MPNight3.value], False)
	else:

####
#### ON Modus
####
		if LCD4linux.LCDType1.value[0] == "4" or LCD4linux.LCDType2.value[0] == "4" or LCD4linux.LCDType3.value[0] == "4":
			if "A" in LCD4linux.LCDTFT.value:
				if AktTFT != "BMP":
					TFTCheck(False, SetMode="BMP")
			else:
				if AktTFT != "DREAM":
					TFTCheck(False, SetMode="DREAM")
# FritzCall
		if LCD4linux.Fritz.value != "0" and LCD4linux.FritzPopupLCD.value != "0" and FritzTime > 1:
			Para = LCD4linux.FritzPos.value, LCD4linux.FritzSize.value, LCD4linux.FritzColor.value, LCD4linux.FritzBackColor.value, LCD4linux.FritzAlign.value, LCD4linux.FritzType.value, LCD4linux.FritzPicPos.value, LCD4linux.FritzPicSize.value, LCD4linux.FritzPicAlign.value, LCD4linux.FritzShadow.value, getFont(LCD4linux.FritzFont.value)
			Lput(LCD4linux.FritzPopupLCD.value, "123456789", putFritz, Para)
		else:
# Bild
			if LCD4linux.Bild.value != "0" and (ScreenActive[0] in LCD4linux.Bild.value or ScreenActive[-3:] != ["", "", ""]):
				ShowPicture = getShowPicture(LCD4linux.BildFile.value, 0)
				Para = LCD4linux.BildPos.value, LCD4linux.BildSize.value, LCD4linux.BildSizeH.value, LCD4linux.BildAlign.value, LCD4linux.BildQuick.value, LCD4linux.BildTransp.value, 0, ShowPicture, LCD4linux.BildFile.value
				Lput4(LCD4linux.BildLCD.value, LCD4linux.Bild.value, putBild, Para)
# Bild 2
			if LCD4linux.Bild2.value != "0" and (ScreenActive[0] in LCD4linux.Bild2.value or ScreenActive[-3:] != ["", "", ""]):
				ShowPicture = getShowPicture(LCD4linux.Bild2File.value, 1)
				Para = LCD4linux.Bild2Pos.value, LCD4linux.Bild2Size.value, LCD4linux.Bild2SizeH.value, LCD4linux.Bild2Align.value, LCD4linux.Bild2Quick.value, LCD4linux.Bild2Transp.value, 0, ShowPicture, LCD4linux.Bild2File.value
				Lput4(LCD4linux.Bild2LCD.value, LCD4linux.Bild2.value, putBild, Para)
# Bild 3
			if LCD4linux.Bild3.value != "0" and (ScreenActive[0] in LCD4linux.Bild3.value or ScreenActive[-3:] != ["", "", ""]):
				ShowPicture = getShowPicture(LCD4linux.Bild3File.value, 2)
				Para = LCD4linux.Bild3Pos.value, LCD4linux.Bild3Size.value, LCD4linux.Bild3SizeH.value, LCD4linux.Bild3Align.value, LCD4linux.Bild3Quick.value, LCD4linux.Bild3Transp.value, 0, ShowPicture, LCD4linux.Bild3File.value
				Lput4(LCD4linux.Bild3LCD.value, LCD4linux.Bild3.value, putBild, Para)
# Bild 4
			if LCD4linux.Bild4.value != "0" and (ScreenActive[0] in LCD4linux.Bild4.value or ScreenActive[-3:] != ["", "", ""]):
				ShowPicture = getShowPicture(LCD4linux.Bild4File.value, 0)
				Para = LCD4linux.Bild4Pos.value, LCD4linux.Bild4Size.value, LCD4linux.Bild4SizeH.value, LCD4linux.Bild4Align.value, LCD4linux.Bild4Quick.value, LCD4linux.Bild4Transp.value, 0, ShowPicture, LCD4linux.Bild4File.value
				Lput4(LCD4linux.Bild4LCD.value, LCD4linux.Bild4.value, putBild, Para)
# HTTP WWW Site
			Para = 1, LCD4linux.WWW1Pos.value, LCD4linux.WWW1Size.value, LCD4linux.WWW1Align.value, LCD4linux.WWW1CutX.value, LCD4linux.WWW1CutY.value, LCD4linux.WWW1CutW.value, LCD4linux.WWW1CutH.value
			Lput(LCD4linux.WWW1LCD.value, LCD4linux.WWW1.value, putWWW, Para)
# Picon
			Para = LCD4linux.PiconSize.value, LCD4linux.PiconPos.value, LCD4linux.PiconAlign.value, LCD4linux.PiconFullScreen.value, LCD4linux.PiconSplit.value, LCD4linux.PiconTextSize.value, 0
			Lput(LCD4linux.PiconLCD.value, LCD4linux.Picon.value, putPicon, Para)
# Picon 2
			Para = LCD4linux.Picon2Size.value, LCD4linux.Picon2Pos.value, LCD4linux.Picon2Align.value, LCD4linux.Picon2FullScreen.value, LCD4linux.Picon2Split.value, LCD4linux.Picon2TextSize.value, 1
			Lput(LCD4linux.Picon2LCD.value, LCD4linux.Picon2.value, putPicon, Para)
			Brief1.join()
			Brief2.join()
			Brief3.join()
# Kalender
			Para = LCD4linux.CalPos.value, LCD4linux.CalZoom.value, LCD4linux.CalAlign.value, LCD4linux.CalSplit.value, LCD4linux.CalType.value, LCD4linux.CalTypeE.value, LCD4linux.CalLayout.value, LCD4linux.CalColor.value, LCD4linux.CalBackColor.value, LCD4linux.CalCaptionColor.value, LCD4linux.CalShadow.value, getFont(LCD4linux.CalFont.value)
			Lput(LCD4linux.CalLCD.value, LCD4linux.Cal.value, putCalendar, Para)
# Termin-List
			Para = LCD4linux.CalListPos.value, LCD4linux.CalListSize.value, LCD4linux.CalListProzent.value, LCD4linux.CalListAlign.value, LCD4linux.CalListSplit.value, LCD4linux.CalListType.value, LCD4linux.CalListLines.value, LCD4linux.CalListColor.value, LCD4linux.CalListShadow.value, getFont(LCD4linux.CalFont.value)
			Lput(LCD4linux.CalListLCD.value, LCD4linux.CalList.value, putCalendarList, Para)
# MSN Wetter
			if wwwWetter[0] != "":
				Para = LCD4linux.WetterPos.value, LCD4linux.WetterZoom.value, LCD4linux.WetterAlign.value, LCD4linux.WetterSplit.value, LCD4linux.WetterType.value, LCD4linux.WetterColor.value, LCD4linux.WetterShadow.value, 0, getFont(LCD4linux.WetterFont.value)
				Lput(LCD4linux.WetterLCD.value, LCD4linux.Wetter.value, putWetter, Para)
			if wwwWetter[1] != "":
				Para = LCD4linux.Wetter2Pos.value, LCD4linux.Wetter2Zoom.value, LCD4linux.Wetter2Align.value, LCD4linux.Wetter2Split.value, LCD4linux.Wetter2Type.value, LCD4linux.Wetter2Color.value, LCD4linux.Wetter2Shadow.value, 1, getFont(LCD4linux.Wetter2Font.value)
				Lput(LCD4linux.Wetter2LCD.value, LCD4linux.Wetter2.value, putWetter, Para)
			if LCD4linux.WetterTransparenz.value != "true":
				Brief1.join()
				Brief2.join()
				Brief3.join()
# Netatmo CO2
			Para = "CO2", LCD4linux.NetAtmoCO2Pos.value, LCD4linux.NetAtmoCO2Size.value, LCD4linux.NetAtmoCO2Len.value, LCD4linux.NetAtmoCO2Align.value, LCD4linux.NetAtmoCO2Split.value, LCD4linux.NetAtmoCO2Station.value, LCD4linux.NetAtmoCO2Type.value
			Lput(LCD4linux.NetAtmoCO2LCD.value, LCD4linux.NetAtmoCO2.value, putNetatmoIllu, Para)
# Netatmo IDX
			Para = "IDX", LCD4linux.NetAtmoIDXPos.value, LCD4linux.NetAtmoIDXSize.value, LCD4linux.NetAtmoIDXLen.value, LCD4linux.NetAtmoIDXAlign.value, LCD4linux.NetAtmoIDXSplit.value, LCD4linux.NetAtmoIDXStation.value, LCD4linux.NetAtmoIDXType.value
			Lput(LCD4linux.NetAtmoIDXLCD.value, LCD4linux.NetAtmoIDX.value, putNetatmoIllu, Para)
# Box 1
			Para = LCD4linux.Box1x1.value, LCD4linux.Box1y1.value, LCD4linux.Box1x2.value, LCD4linux.Box1y2.value, LCD4linux.Box1Color.value, LCD4linux.Box1BackColor.value
			Lput(LCD4linux.Box1LCD.value, LCD4linux.Box1.value, putBox, Para)
# Box 2
			Para = LCD4linux.Box2x1.value, LCD4linux.Box2y1.value, LCD4linux.Box2x2.value, LCD4linux.Box2y2.value, LCD4linux.Box2Color.value, LCD4linux.Box2BackColor.value
			Lput(LCD4linux.Box2LCD.value, LCD4linux.Box2.value, putBox, Para)
# Moonphase
			Para = LCD4linux.MoonPos.value, LCD4linux.MoonSize.value, LCD4linux.MoonFontSize.value, LCD4linux.MoonAlign.value, LCD4linux.MoonInfos.value, LCD4linux.MoonTrends.value, LCD4linux.MoonSplit.value, LCD4linux.MoonColor.value, LCD4linux.MoonShadow.value, getFont(LCD4linux.MoonFont.value)
			Lput(LCD4linux.MoonLCD.value, LCD4linux.Moon.value, putMoon, Para)
# Netatmo
			Para = LCD4linux.NetAtmoPos.value, LCD4linux.NetAtmoSize.value, LCD4linux.NetAtmoAlign.value, LCD4linux.NetAtmoSplit.value, LCD4linux.NetAtmoStation.value, LCD4linux.NetAtmoModule.value, LCD4linux.NetAtmoModuleUser.value, LCD4linux.NetAtmoBasis.value, LCD4linux.NetAtmoName.value, LCD4linux.NetAtmoType.value, LCD4linux.NetAtmoType2.value, [LCD4linux.NetAtmoColor.value, LCD4linux.NetAtmoColor2.value, LCD4linux.NetAtmoColor3.value, LCD4linux.NetAtmoColor4.value, LCD4linux.NetAtmoColor5.value, LCD4linux.NetAtmoColor6.value, LCD4linux.NetAtmoColor7.value], LCD4linux.NetAtmoShadow.value, getFont(LCD4linux.NetAtmoFont.value)
			Lput(LCD4linux.NetAtmoLCD.value, LCD4linux.NetAtmo.value, putNetatmo, Para)
			Para = LCD4linux.NetAtmo2Pos.value, LCD4linux.NetAtmo2Size.value, LCD4linux.NetAtmo2Align.value, LCD4linux.NetAtmo2Split.value, LCD4linux.NetAtmo2Station.value, LCD4linux.NetAtmo2Module.value, LCD4linux.NetAtmo2ModuleUser.value, LCD4linux.NetAtmo2Basis.value, LCD4linux.NetAtmo2Name.value, LCD4linux.NetAtmo2Type.value, LCD4linux.NetAtmo2Type2.value, [LCD4linux.NetAtmo2Color.value, LCD4linux.NetAtmo2Color2.value, LCD4linux.NetAtmo2Color3.value, LCD4linux.NetAtmo2Color4.value, LCD4linux.NetAtmo2Color5.value, LCD4linux.NetAtmo2Color6.value, LCD4linux.NetAtmo2Color7.value], LCD4linux.NetAtmo2Shadow.value, getFont(LCD4linux.NetAtmo2Font.value)
			Lput(LCD4linux.NetAtmo2LCD.value, LCD4linux.NetAtmo2.value, putNetatmo, Para)
# Meteo station
			if wwwMeteo.find("current_conditions") > 1:
				Para = LCD4linux.MeteoPos.value, LCD4linux.MeteoZoom.value, LCD4linux.MeteoAlign.value, LCD4linux.MeteoSplit.value, LCD4linux.MeteoType.value, LCD4linux.MeteoColor.value
				Lput(LCD4linux.MeteoLCD.value, LCD4linux.Meteo.value, putMeteo, Para)
# get clock
			Para = LCD4linux.ClockPos.value, LCD4linux.ClockSize.value, LCD4linux.ClockAlign.value, LCD4linux.ClockSplit.value, LCD4linux.ClockType.value, LCD4linux.ClockSpacing.value, LCD4linux.ClockAnalog.value, LCD4linux.ClockColor.value, LCD4linux.ClockShadow.value, 0, getFont(LCD4linux.ClockFont.value)
			Lput(LCD4linux.ClockLCD.value, LCD4linux.Clock.value, putClock, Para)
			Para = LCD4linux.Clock2Pos.value, LCD4linux.Clock2Size.value, LCD4linux.Clock2Align.value, LCD4linux.Clock2Split.value, LCD4linux.Clock2Type.value, LCD4linux.Clock2Spacing.value, LCD4linux.Clock2Analog.value, LCD4linux.Clock2Color.value, LCD4linux.Clock2Shadow.value, 1, getFont(LCD4linux.Clock2Font.value)
			Lput(LCD4linux.Clock2LCD.value, LCD4linux.Clock2.value, putClock, Para)
# Informationen
			Para = LCD4linux.InfoPos.value, LCD4linux.InfoSize.value, LCD4linux.InfoAlign.value, LCD4linux.InfoLines.value, LCD4linux.InfoSplit.value, LCD4linux.InfoColor.value, LCD4linux.InfoTuner.value + LCD4linux.InfoSensor.value + LCD4linux.InfoCPU.value, LCD4linux.InfoShadow.value, getFont(LCD4linux.InfoFont.value)
			Lput(LCD4linux.InfoLCD.value, LCD4linux.Info.value, putInfo, Para)
			Para = LCD4linux.Info2Pos.value, LCD4linux.Info2Size.value, LCD4linux.Info2Align.value, LCD4linux.Info2Lines.value, LCD4linux.Info2Split.value, LCD4linux.Info2Color.value, LCD4linux.Info2Tuner.value + LCD4linux.Info2Sensor.value + LCD4linux.Info2CPU.value, LCD4linux.Info2Shadow.value, getFont(LCD4linux.Info2Font.value)
			Lput(LCD4linux.Info2LCD.value, LCD4linux.Info2.value, putInfo, Para)
# Satellit
			Para = LCD4linux.SatPos.value, LCD4linux.SatSize.value, LCD4linux.SatAlign.value, LCD4linux.SatSplit.value, LCD4linux.SatColor.value, LCD4linux.SatType.value, LCD4linux.SatShadow.value, getFont(LCD4linux.SatFont.value)
			Lput(LCD4linux.SatLCD.value, LCD4linux.Sat.value, putSat, Para)
# Provider
			Para = LCD4linux.ProvPos.value, LCD4linux.ProvSize.value, LCD4linux.ProvAlign.value, LCD4linux.ProvSplit.value, LCD4linux.ProvColor.value, LCD4linux.ProvType.value, LCD4linux.ProvShadow.value, getFont(LCD4linux.ProvFont.value)
			Lput(LCD4linux.ProvLCD.value, LCD4linux.Prov.value, putProv, Para)
# Timer Record
			Para = 0, LCD4linux.TimerPos.value, LCD4linux.TimerSize.value, LCD4linux.TimerLen.value, LCD4linux.TimerLines.value, LCD4linux.TimerType.value, LCD4linux.TimerType2.value, LCD4linux.TimerAlign.value, LCD4linux.TimerSplit.value, LCD4linux.TimerColor.value, LCD4linux.TimerShadow.value, getFont(LCD4linux.TimerFont.value)
			Lput(LCD4linux.TimerLCD.value, LCD4linux.Timer.value, putTimer, Para)
# aktive Sendernummer
			Para = LCD4linux.ChannelNumPos.value, LCD4linux.ChannelNumSize.value, LCD4linux.ChannelNumAlign.value, LCD4linux.ChannelNumBackColor.value, LCD4linux.ChannelNumColor.value, LCD4linux.ChannelNumShadow.value, getFont(LCD4linux.ChannelNumFont.value)
			Lput(LCD4linux.ChannelNumLCD.value, LCD4linux.ChannelNum.value, putChannelNum, Para)
# aktive Sendername
			Para = LCD4linux.ChannelPos.value, LCD4linux.ChannelSize.value, LCD4linux.ChannelLen.value, LCD4linux.ChannelLines.value, LCD4linux.ChannelAlign.value, LCD4linux.ChannelSplit.value, LCD4linux.ChannelColor.value, LCD4linux.ChannelShadow.value, getFont(LCD4linux.ChannelFont.value)
			Lput(LCD4linux.ChannelLCD.value, LCD4linux.Channel.value, putChannel, Para)
# Progress Bar
			Para = LCD4linux.ProgressPos.value, LCD4linux.ProgressSize.value, LCD4linux.ProgressLen.value, LCD4linux.ProgressType.value, LCD4linux.ProgressColor.value, LCD4linux.ProgressColorText.value, LCD4linux.ProgressAlign.value, LCD4linux.ProgressMinutes.value, LCD4linux.ProgressBorder.value, LCD4linux.ProgressShadow.value, LCD4linux.ProgressShadow2.value, getFont(LCD4linux.ProgressFont.value)
			Lput(LCD4linux.ProgressLCD.value, LCD4linux.Progress.value, putProgress, Para)
# Volume
			Para = LCD4linux.VolPos.value, LCD4linux.VolSize.value, LCD4linux.VolLen.value, LCD4linux.VolAlign.value, LCD4linux.VolSplit.value, LCD4linux.VolColor.value, LCD4linux.VolShadow.value
			Lput(LCD4linux.VolLCD.value, LCD4linux.Vol.value, putVol, Para)
# extended Description
			Para = LCD4linux.DescPos.value, LCD4linux.DescSize.value, LCD4linux.DescLen.value, LCD4linux.DescLines.value, LCD4linux.DescColor.value, LCD4linux.DescAlign.value, LCD4linux.DescSplit.value, LCD4linux.DescType.value, LCD4linux.DescShadow.value, LCD4linux.DescUseInfo.value, getFont(LCD4linux.DescFont.value)
			Lput(LCD4linux.DescLCD.value, LCD4linux.Desc.value, putDescription, Para)
# aktive Event
			Para = LCD4linux.ProgPos.value, LCD4linux.ProgSize.value, LCD4linux.ProgLen.value, LCD4linux.ProgLines.value, LCD4linux.ProgType.value, LCD4linux.ProgColor.value, LCD4linux.ProgAlign.value, LCD4linux.ProgSplit.value, LCD4linux.ProgShadow.value, getFont(LCD4linux.ProgFont.value)
			Lput(LCD4linux.ProgLCD.value, LCD4linux.Prog.value, putProg, Para)
			Para = LCD4linux.Prog2Pos.value, LCD4linux.Prog2Size.value, LCD4linux.Prog2Len.value, LCD4linux.Prog2Lines.value, LCD4linux.Prog2Type.value, LCD4linux.Prog2Color.value, LCD4linux.Prog2Align.value, LCD4linux.Prog2Split.value, LCD4linux.Prog2Shadow.value, getFont(LCD4linux.Prog2Font.value)
			Lput(LCD4linux.Prog2LCD.value, LCD4linux.Prog2.value, putProg, Para)
# next Event
			Para = LCD4linux.ProgNextPos.value, LCD4linux.ProgNextSize.value, LCD4linux.ProgNextLen.value, LCD4linux.ProgNextLines.value, LCD4linux.ProgNextType.value, LCD4linux.ProgNextColor.value, LCD4linux.ProgNextAlign.value, LCD4linux.ProgNextSplit.value, LCD4linux.ProgNextShadow.value, getFont(LCD4linux.ProgNextFont.value)
			Lput(LCD4linux.ProgNextLCD.value, LCD4linux.ProgNext.value, putProgNext, Para)
# Tuner
			Para = LCD4linux.TunerPos.value, LCD4linux.TunerSize.value, LCD4linux.TunerAlign.value, LCD4linux.TunerSplit.value, LCD4linux.TunerType.value, LCD4linux.TunerActive.value, getFont(LCD4linux.TunerFont.value)
			Lput(LCD4linux.TunerLCD.value, LCD4linux.Tuner.value, putTuner, Para)
# Audio/Video
			Para = LCD4linux.AVPos.value, LCD4linux.AVSize.value, LCD4linux.AVAlign.value, LCD4linux.AVSplit.value, LCD4linux.AVColor.value, LCD4linux.AVShadow.value, LCD4linux.AVType.value, getFont(LCD4linux.AVFont.value)
			Lput(LCD4linux.AVLCD.value, LCD4linux.AV.value, putAV, Para)
# Signal Quality Bar
			Para = LCD4linux.SignalPos.value, LCD4linux.SignalSize.value, LCD4linux.SignalLen.value, LCD4linux.SignalAlign.value, LCD4linux.SignalSplit.value, LCD4linux.SignalColor.value, LCD4linux.SignalGradient.value
			Lput(LCD4linux.SignalLCD.value, LCD4linux.Signal.value, putSignal, Para)
# Bitrate
			Para = LCD4linux.BitratePos.value, LCD4linux.BitrateSize.value, LCD4linux.BitrateAlign.value, LCD4linux.BitrateSplit.value, LCD4linux.BitrateColor.value, LCD4linux.BitrateShadow.value, getFont(LCD4linux.BitrateFont.value)
			Lput(LCD4linux.BitrateLCD.value, LCD4linux.Bitrate.value, putBitrate, Para)
# Online-Ping
			Para = LCD4linux.PingPos.value, LCD4linux.PingSize.value, LCD4linux.PingAlign.value, LCD4linux.PingSplit.value, LCD4linux.PingColor.value, LCD4linux.PingType.value, LCD4linux.PingShow.value, LCD4linux.PingTimeout.value, (LCD4linux.PingName1.value, LCD4linux.PingName2.value, LCD4linux.PingName3.value, LCD4linux.PingName4.value, LCD4linux.PingName5.value), LCD4linux.PingShadow.value, getFont(LCD4linux.PingFont.value)
			Lput(LCD4linux.PingLCD.value, LCD4linux.Ping.value, putOnline, Para)
# external IP
			Para = LCD4linux.ExternalIpPos.value, LCD4linux.ExternalIpSize.value, getFont(LCD4linux.ExternalIpFont.value), LCD4linux.ExternalIpAlign.value, LCD4linux.ExternalIpSplit.value, LCD4linux.ExternalIpColor.value, LCD4linux.ExternalIpBackColor.value, LCD4linux.ExternalIpShadow.value, self.ExternalIP
			Lput(LCD4linux.ExternalIpLCD.value, LCD4linux.ExternalIp.value, putExternalIP, Para)
# www Remote-Box
			Para = LCD4linux.RBoxPos.value, LCD4linux.RBoxSize.value, LCD4linux.RBoxAlign.value, False, [LCD4linux.RBoxColor.value, LCD4linux.RBoxColor2.value, LCD4linux.RBoxColor3.value, LCD4linux.RBoxColor4.value, LCD4linux.RBoxColor5.value], LCD4linux.RBoxProzent.value, LCD4linux.RBoxShow.value, LCD4linux.RBoxShadow.value, getFont(LCD4linux.RBoxFont.value)
			Lput(LCD4linux.RBoxLCD.value, LCD4linux.RBox.value, putRemoteBox, Para)
# www Remote-Timer Record
			Para = 1, LCD4linux.RBoxTimerPos.value, LCD4linux.RBoxTimerSize.value, LCD4linux.RBoxTimerLen.value, LCD4linux.RBoxTimerLines.value, LCD4linux.RBoxTimerType.value, LCD4linux.RBoxTimerType2.value, LCD4linux.RBoxTimerAlign.value, LCD4linux.RBoxTimerSplit.value, LCD4linux.RBoxTimerColor.value, LCD4linux.RBoxTimerShadow.value, getFont(LCD4linux.RBoxTimerFont.value)
			Lput(LCD4linux.RBoxTimerLCD.value, LCD4linux.RBoxTimer.value, putTimer, Para)
# Devices
			Para = LCD4linux.DevPos.value, LCD4linux.DevSize.value, LCD4linux.DevAlign.value, LCD4linux.DevSplit.value, LCD4linux.DevColor.value, (LCD4linux.DevExtra.value, LCD4linux.DevName1.value, LCD4linux.DevName2.value, LCD4linux.DevName3.value, LCD4linux.DevName4.value, LCD4linux.DevName5.value), LCD4linux.DevShadow.value, LCD4linux.DevType.value, LCD4linux.DevWarning.value, getFont(LCD4linux.DevFont.value)
			Lput(LCD4linux.DevLCD.value, LCD4linux.Dev.value, putDev, Para)
# HDD
			Para = LCD4linux.HddPos.value, LCD4linux.HddSize.value, LCD4linux.HddAlign.value, LCD4linux.HddSplit.value, LCD4linux.HddType.value
			Lput(LCD4linux.HddLCD.value, LCD4linux.Hdd.value, putHdd, Para)
# Mute
			Para = LCD4linux.MutePos.value, LCD4linux.MuteSize.value, LCD4linux.MuteAlign.value, LCD4linux.MuteSplit.value
			Lput(LCD4linux.MuteLCD.value, LCD4linux.Mute.value, putMute, Para)
# show OSCAM
			Para = LCD4linux.OSCAMPos.value, LCD4linux.OSCAMSize.value, LCD4linux.OSCAMColor.value, LCD4linux.OSCAMBackColor.value, LCD4linux.OSCAMAlign.value, LCD4linux.OSCAMSplit.value
			Lput(LCD4linux.OSCAMLCD.value, LCD4linux.OSCAM.value, putOSCAM, Para)
# show ECM
			Para = LCD4linux.ECMPos.value, LCD4linux.ECMSize.value, LCD4linux.ECMColor.value, LCD4linux.ECMBackColor.value, LCD4linux.ECMAlign.value, LCD4linux.ECMSplit.value
			Lput(LCD4linux.ECMLCD.value, LCD4linux.ECM.value, putECM, Para)
# show String Text
			Para = LCD4linux.StringPos.value, LCD4linux.StringSize.value, getFont(LCD4linux.StringFont.value), LCD4linux.StringAlign.value, LCD4linux.StringSplit.value, LCD4linux.StringColor.value, LCD4linux.StringBackColor.value, LCD4linux.StringShadow.value, LCD4linux.StringText.value
			Lput(LCD4linux.StringLCD.value, LCD4linux.String.value, putString, Para)
			Para = LCD4linux.String2Pos.value, LCD4linux.String2Size.value, getFont(LCD4linux.String2Font.value), LCD4linux.String2Align.value, LCD4linux.String2Split.value, LCD4linux.String2Color.value, LCD4linux.String2BackColor.value, LCD4linux.String2Shadow.value, LCD4linux.String2Text.value
			Lput(LCD4linux.String2LCD.value, LCD4linux.String2.value, putString, Para)

# show Textfile
			Para = LCD4linux.TextPos.value, LCD4linux.TextSize.value, getFont(LCD4linux.TextFont.value), LCD4linux.TextAlign.value, LCD4linux.TextColor.value, LCD4linux.TextBackColor.value, LCD4linux.TextShadow.value, LCD4linux.TextFile.value
			Lput(LCD4linux.TextLCD.value, LCD4linux.Text.value, putTextFile, Para)
			Para = LCD4linux.Text2Pos.value, LCD4linux.Text2Size.value, getFont(LCD4linux.Text2Font.value), LCD4linux.Text2Align.value, LCD4linux.Text2Color.value, LCD4linux.Text2BackColor.value, LCD4linux.Text2Shadow.value, LCD4linux.Text2File.value
			Lput(LCD4linux.Text2LCD.value, LCD4linux.Text2.value, putTextFile, Para)
			Para = LCD4linux.Text3Pos.value, LCD4linux.Text3Size.value, getFont(LCD4linux.Text3Font.value), LCD4linux.Text3Align.value, LCD4linux.Text3Color.value, LCD4linux.Text3BackColor.value, LCD4linux.Text3Shadow.value, LCD4linux.Text3File.value
			Lput(LCD4linux.Text3LCD.value, LCD4linux.Text3.value, putTextFile, Para)
# show HTTP Text
			Para = LCD4linux.HTTPPos.value, LCD4linux.HTTPSize.value, LCD4linux.HTTPAlign.value, LCD4linux.HTTPColor.value, LCD4linux.HTTPBackColor.value, LCD4linux.HTTPURL.value, LCD4linux.HTTPShadow.value, getFont(LCD4linux.HTTPFont.value)
			Lput(LCD4linux.HTTPLCD.value, LCD4linux.HTTP.value, putHTTP, Para)
# show Mail
			Para = LCD4linux.MailPos.value, LCD4linux.MailSize.value, LCD4linux.MailProzent.value, LCD4linux.MailColor.value, LCD4linux.MailBackColor.value, LCD4linux.MailAlign.value, LCD4linux.MailSplit.value, LCD4linux.MailLines.value, LCD4linux.MailType.value, LCD4linux.MailKonto.value, LCD4linux.MailShadow.value, getFont(LCD4linux.MailFont.value)
			Lput(LCD4linux.MailLCD.value, LCD4linux.Mail.value, putMail, Para)
# show Ereignis Icon Bar
			Para = LCD4linux.IconBarPos.value, LCD4linux.IconBarSize.value, LCD4linux.IconBarAlign.value, LCD4linux.IconBarSplit.value, LCD4linux.IconBarType.value, LCD4linux.IconBarPopup.value, LCD4linux.IconBarPopupLCD.value
			Lput(LCD4linux.IconBarLCD.value, LCD4linux.IconBar.value, putIconBar, Para)
# show Sonnenaufgang
			Para = LCD4linux.SunPos.value, LCD4linux.SunSize.value, LCD4linux.SunColor.value, LCD4linux.SunBackColor.value, LCD4linux.SunAlign.value, LCD4linux.SunSplit.value, LCD4linux.SunType.value, LCD4linux.SunShadow.value, getFont(LCD4linux.SunFont.value)
			Lput(LCD4linux.SunLCD.value, LCD4linux.Sun.value, putSun, Para)

# externe Elementeliste
			putL4LElist("On")

# FritzCall
			Para = LCD4linux.FritzPos.value, LCD4linux.FritzSize.value, LCD4linux.FritzColor.value, LCD4linux.FritzBackColor.value, LCD4linux.FritzAlign.value, LCD4linux.FritzType.value, LCD4linux.FritzPicPos.value, LCD4linux.FritzPicSize.value, LCD4linux.FritzPicAlign.value, LCD4linux.FritzShadow.value, getFont(LCD4linux.FritzFont.value)
			Lput(LCD4linux.FritzLCD.value, LCD4linux.Fritz.value, putFritz, Para)
# Recording
			Para = LCD4linux.RecordingPos.value, LCD4linux.RecordingSize.value, LCD4linux.RecordingAlign.value, LCD4linux.RecordingSplit.value, LCD4linux.RecordingType.value
			Lput(LCD4linux.RecordingLCD.value, LCD4linux.Recording.value, putRecording, Para)
# show OSD
			if str(LCD4linux.OSD.value) != "0" and ConfigMode == False and FritzTime == 0:
				if OSDon >= 2 and ((isMediaPlayer == "" and "T" in LCD4linux.OSDshow.value) or (isMediaPlayer == "radio" and "R" in LCD4linux.OSDshow.value)):
					if "1" in LCD4linux.OSDLCD.value:
						Brief1.put([putGrab, LCD4linux.OSDfast.value, LCD4linux.OSDsize.value, 1, 1])
					if "2" in LCD4linux.OSDLCD.value and LCD4linux.LCDType2.value != "00":
						Brief2.put([putGrab, LCD4linux.OSDfast.value, LCD4linux.OSDsize.value, 2, 2])
					if "3" in LCD4linux.OSDLCD.value and LCD4linux.LCDType3.value != "00":
						Brief3.put([putGrab, LCD4linux.OSDfast.value, LCD4linux.OSDsize.value, 3, 3])
					if OSDon == 3:
						OSDon = 2
# LCDoff
		if isOffTime(LCD4linux.LCDoff.value, LCD4linux.LCDon.value, LCD4linux.LCDWEoff.value, LCD4linux.LCDWEon.value) or LCDon == False or self.AutoOFF == -1:
			Dunkel = writeHelligkeit([0, 0, 0], [0, 0, 0], False)
			L4log("LCD on", "%s" % LCDon)
		else:
			Dunkel = writeHelligkeit([LCD4linux.Helligkeit.value, LCD4linux.Helligkeit2.value, LCD4linux.Helligkeit3.value], [LCD4linux.Night.value, LCD4linux.Night2.value, LCD4linux.Night3.value], False)
# Ende
##################
	q1, q2, q3 = Brief1.qsize(), Brief2.qsize(), Brief3.qsize()
	tw = time()
	tp = tw - tt
	Brief1.join()
	Brief2.join()
	Brief3.join()
	PUSH = "Push: %.3f (%d/%d/%d) Wait: %.3f" % (tp, q1, q2, q3, (time() - tw))
	L4log(PUSH)
# PopupText
	if ScreenActive[0] in LCD4linux.Popup.value and len(PopText[1]) > 2:
		Para = LCD4linux.PopupPos.value, LCD4linux.PopupSize.value, LCD4linux.PopupColor.value, LCD4linux.PopupBackColor.value, LCD4linux.PopupAlign.value, getFont(LCD4linux.PopupFont.value)
		if "1" in LCD4linux.PopupLCD.value:
			Brief1.put([putPopup, Para, 1, 1])
		if "2" in LCD4linux.PopupLCD.value and LCD4linux.LCDType2.value != "00":
			Brief2.put([putPopup, Para, 2, 2])
		if "3" in LCD4linux.PopupLCD.value and LCD4linux.LCDType3.value != "00":
			Brief2.put([putPopup, Para, 3, 3])
# show isCrashlog
	if LCD4linux.Crash.value == True:
		Brief1.put([putCrash, 1, 1])
	Brief1.join()
	Brief2.join()
	Brief3.join()
	TimePicture = time() - tt

	if self.Refresh >= LCD4linux.LCDRefresh1.value and not (getSA(1) in LCD4linux.TV.value and "1" in LCD4linux.TVLCD.value and not Standby.inStandby):
		if Dunkel and "1" in Dunkel:
			MAX_W, MAX_H = self.im[1].size
			self.draw[1].rectangle((0, 0, MAX_W, MAX_H), fill="black")
			QuickList = [[], [], []]
		if str(LCD4linux.LCDRotate1.value) != "0":
			self.im[1] = self.im[1].rotate(int(LCD4linux.LCDRotate1.value))
		Brief1.put([writeLCD1, self, 1, LCD4linux.BilderJPEG.value])
	if LCD4linux.LCDType2.value != "00" and self.Refresh >= LCD4linux.LCDRefresh2.value and not (getSA(2) in LCD4linux.TV.value and "2" in LCD4linux.TVLCD.value and not Standby.inStandby):
		if Dunkel and "2" in Dunkel:
			MAX_W, MAX_H = self.im[2].size
			self.draw[2].rectangle((0, 0, MAX_W, MAX_H), fill="black")
		if str(LCD4linux.LCDRotate2.value) != "0":
			self.im[2] = self.im[2].rotate(int(LCD4linux.LCDRotate2.value))
		Brief2.put([writeLCD2, self, 2, LCD4linux.BilderJPEG.value])
	if LCD4linux.LCDType3.value != "00" and self.Refresh >= LCD4linux.LCDRefresh3.value and not (getSA(3) in LCD4linux.TV.value and "3" in LCD4linux.TVLCD.value and not Standby.inStandby):
		if Dunkel and "3" in Dunkel:
			MAX_W, MAX_H = self.im[3].size
			self.draw[3].rectangle((0, 0, MAX_W, MAX_H), fill="black")
		if str(LCD4linux.LCDRotate3.value) != "0":
			self.im[3] = self.im[3].rotate(int(LCD4linux.LCDRotate3.value))
		Brief3.put([writeLCD3, self, 3, LCD4linux.BilderJPEG.value])
	Brief1.join()
	Brief2.join()
	Brief3.join()
	self.Refresh = "0"
	TimeEnd = time() - tt
	INFO = "RunTime: %.3f (Picture: %.3f / Write: %.3f)" % (TimeEnd, TimePicture, TimeEnd - TimePicture)
	L4log(INFO)  # (%.3f/%.3f) ,TimeLCD1,TimeLCD2
	INFO = PUSH + "   " + INFO


def main(session, **kwargs):
	session.open(LCDdisplayConfig)


def screenswitch(session, **kwargs):
	session.open(LCDscreenSwitch)


def autostart(reason, **kwargs):
	global session
	global LCDon
	global SamsungDevice
	global SamsungDevice2
	global SamsungDevice3
	global FritzList
	if reason == 0 and "session" in kwargs:
		session = kwargs["session"]
		L4log("Start %s (%s), Libusb %s, %s..." % (Version, L4LElist.getVersion(), USBok, TMP))
		Screen.L4L_show_old = Screen.show
		Screen.show = L4L_replacement_Screen_show
		if harddiskmanager.HDDCount() > 0:
			for hdd in harddiskmanager.HDDList():
				L4log(hdd[0], hdd[1].model())
		if isdir("%slcd4linux" % TMP) == False:
			try:
				mkdir("%slcd4linux" % TMP)
				L4log("create %s" % TMPL)
			except Exception:
				L4log("Error: create %s" % TMPL)
		rmFiles(PIC + "*.*")
		rmFile(xmlPIC)
		if LCD4linux.WebIfInitDelay.value == False:
			InitWebIF()
		if islink(LCD4lib + "libpython2.5.so.1.0") == False:
			try:
				symlink(LCD4lib + "libpython2.6.so.1.0", LCD4lib + "libpython2.5.so.1.0")
				L4log("create Link")
			except Exception:
				L4log("Error create Link")
		setFONT(LCD4linux.Font.value)
		if exists(LCD4config) and LCD4linux.L4LVersion.value != Version:
			L4log("Version changed from", LCD4linux.L4LVersion.value)
			LCD4linux.L4LVersion.value = Version
			LCD4linux.Crash.value = True
		CheckFstab()
		TFTCheck(False)
		if isfile(LCD4enigma2config + "skin_user.xml"):
			xmlRead()
			LCD4linux.xmlType01.value = False if xmlFind(1) == -1 else True
			LCD4linux.xmlType02.value = False if xmlFind(2) == -1 else True
			LCD4linux.xmlType03.value = False if xmlFind(3) == -1 else True
			if LCD4linux.LCDType1.value[0] != "5" and LCD4linux.LCDType2.value[0] != "5" and LCD4linux.LCDType3.value[0] != "5":
				if xmlDelete(1) or xmlDelete(2) or xmlDelete(3):
					L4log("removed old Skindata")
					xmlWrite()
			xmlClear()
		UpdateStatus(session)
		if isfile("%slcd4linux-start.sh" % LCD4bin):
			RunShell("%slcd4linux-start.sh" % LCD4bin)
		try:
			if isfile(LCD4enigma2config + "lcd4fritz"):
				L4logE("read Fritzlist")
				for line in open(LCD4enigma2config + "lcd4fritz", "r").readlines():
					exec("FritzList.append(%s)" % line)
				rmFile(LCD4enigma2config + "lcd4fritz")
		except Exception:
				L4log("Error load Fritzlist")

	if reason == 1:
		L4log("Stop...")
		LCDon = False
		if len(FritzList) > 0:
			L4logE("write Fritzlist")
			try:
				with open(LCD4enigma2config + "lcd4fritz", "w") as f:
					for i in FritzList:
						f.write(str(i) + "\n")
			except Exception:
				L4log("Error save Fritzlist")
		TFTCheck(False, SetMode="DREAM")
		if isfile("%slcd4linux-stop.sh" % LCD4bin):
			RunShell("%slcd4linux-stop.sh" % LCD4bin)
		if LCD4linux.LCDshutdown.value == True:
			try:
				writeHelligkeit([0, 0, 0], [0, 0, 0], True)
			except Exception:
				L4log("Helligkeit-Error -> Fallback")
				writeHelligkeit([0, 0, 0], [0, 0, 0], False)
			if SamsungDevice is not None and LCD4linux.LCDType1.value[0] == "2":
				try:
					MAX_W, MAX_H = getResolution(LCD4linux.LCDType1.value, LCD4linux.LCDRotate1.value)
					MAX_W = int(MAX_W)
					MAX_H = int(MAX_H)
					im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
					output = BytesIO()
					im.save(output, "JPEG")
					pic = output.getvalue()
					output.close()
					Photoframe.write_jpg2frame(SamsungDevice, pic)
					SamsungDevice = None
				except Exception:
					pass
			if SamsungDevice2 is not None and LCD4linux.LCDType2.value[0] == "2":
				try:
					MAX_W, MAX_H = getResolution(LCD4linux.LCDType2.value, LCD4linux.LCDRotate2.value)
					MAX_W = int(MAX_W)
					MAX_H = int(MAX_H)
					im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
					output = BytesIO()
					im.save(output, "JPEG")
					pic = output.getvalue()
					output.close()
					Photoframe.write_jpg2frame(SamsungDevice2, pic)
					SamsungDevice2 = None
				except Exception:
					pass
			if SamsungDevice3 is not None and LCD4linux.LCDType3.value[0] == "2":
				try:
					MAX_W, MAX_H = getResolution(LCD4linux.LCDType3.value, LCD4linux.LCDRotate3.value)
					MAX_W = int(MAX_W)
					MAX_H = int(MAX_H)
					im = Image.new('RGB', (MAX_W, MAX_H), (0, 0, 0, 0))
					output = BytesIO()
					im.save(output, "JPEG")
					pic = output.getvalue()
					output.close()
					Photoframe.write_jpg2frame(SamsungDevice3, pic)
					SamsungDevice3 = None
				except Exception:
					pass
		MJPEG_stop(9)


def setup(menuid, **kwargs):
	if IMAGEDISTRO in ("openvix", "openatv", "egami", "openhdf", "openbh", "openspa", "opendroid"):
		if menuid == "display" and SystemInfo["Display"]:
			return [("LCD4Linux", main, "lcd4linux", None)]
		elif menuid == "system" and not SystemInfo["Display"]:
			return [("LCD4Linux", main, "lcd4linux", None)]
		else:
			return []
	else:
		return [("LCD4Linux", main, "lcd4linux", None)] if menuid == "setup" else []


def Plugins(**kwargs):
	liste = [PluginDescriptor(name="LCD4linux", description=_("LCD4linux"), where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart)]
	liste.append(PluginDescriptor(name="LCD4linux", description=_("LCD4linux"), where=PluginDescriptor.WHERE_MENU, fnc=setup))
	liste.append(PluginDescriptor(name=_("LCD4Linux"), description=_("LCD4Linux"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, icon="plugin.png"))
	liste.append(PluginDescriptor(name=_("LCD4linux Screen Switch"), description=_("LCD4linux Screen Switch"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon="plugin.png", fnc=screenswitch))
	return liste

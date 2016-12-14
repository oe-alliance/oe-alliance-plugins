#Giga
# for localized messages
from . import _

from Screens.Screen import Screen
from Components.Console import Console
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.config import config, configfile, ConfigSubsection, ConfigEnableDisable, getConfigListEntry, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigSlider
from Components.ConfigList import ConfigListScreen, ConfigList
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from enigma import iPlayableService, eServiceCenter, eTimer, eActionMap
from boxbranding import getBoxType, getImageDistro
from os import system
from Plugins.Plugin import PluginDescriptor
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ServiceList import ServiceList
from Screens.InfoBar import InfoBar
from time import localtime, time
import Screens.Standby
from enigma import pNavigation
import Components.RecordingConfig
from Components.Harddisk import harddiskmanager

BOX = getBoxType()

config.plugins.VFD_Giga = ConfigSubsection()
config.plugins.VFD_Giga.showClock = ConfigSelection(default = "True_Switch", choices = [("False",_("Channelnumber in Standby off")),("True",_("Channelnumber in Standby Clock")),("True_Switch",_("Channelnumber/Clock in Standby Clock")),("True_All",_("Clock always")),("Off",_("Always off"))])
config.plugins.VFD_Giga.showClockDeepStandby = ConfigSelection(default = "False", choices = [("False",_("No")),("True",_("Yes"))])
config.plugins.VFD_Giga.channelnrformat = ConfigSelection(default = "True", choices = [("False",_("No")),("True",_("Yes"))])
config.plugins.VFD_Giga.setLed = ConfigYesNo(default = True)
config.plugins.VFD_Giga.recLedBlink = ConfigYesNo(default = True)
led = [("0",_("None")),("1",_("Blue")),("2",_("Red")),("3",_("Purple"))]
config.plugins.VFD_Giga.ledRUN = ConfigSelection(led, default = "1")
config.plugins.VFD_Giga.ledSBY = ConfigSelection(led, default = "2")
config.plugins.VFD_Giga.ledREC = ConfigSelection(led, default = "3")
config.plugins.VFD_Giga.ledDSBY = ConfigSelection(led, default = "2")
config.plugins.VFD_Giga.ledSDA1 = ConfigSelection(led, default = "0")
config.plugins.VFD_Giga.ledSDB1 = ConfigSelection(led, default = "0")
config.plugins.VFD_Giga.timeMode = ConfigSelection(default = "24h", choices = [("12h"),("24h")])
config.plugins.VFD_Giga.vfdBrightness = ConfigSlider(default=255, increment = 5, limits=(0,255))
config.plugins.VFD_Giga.vfdBrightnessStandby = ConfigSlider(default=255, increment = 5, limits=(0,255))

RecLed = None

def vfd_write(text):
	open("/dev/mcu", "w").write(text)

def setvfdBrightness(value):
		f = open("/proc/stb/fp/oled_brightness", "w")
		f.write(str(value))
		f.close()

def setLed(color):
	# 0 = off
	# 1 = blue
	# 2 = red
	# 3 = purple
	led0 = '/proc/stb/fp/led0_pattern'
	led1 = '/proc/stb/fp/led1_pattern'
	
	if BOX in ('gb800se', 'gb800solo', 'gb800ue'):
		if color == '0':
			value0 = 0
			value1 = 0
		elif color == '1':
			value0 = 1
			value1 = 1
		elif color == '2':
			value0 = 2
			value1 = 2
		elif color == '3':
			value0 = 3
			value1 = 3
		else:
			value0 = 0
			value1 = 0
	else:
		if color == '0':
			value0 = 0
			value1 = 0
		elif color == '1':
			value0 = 0
			value1 = 1
		elif color == '2':
			value0 = 1
			value1 = 0
		elif color == '3':
			value0 = 1
			value1 = 1
		else:
			value0 = 0
			value1 = 0

	f = open(led0,"w")
	f.write(str(value0))
	f.close()
	f = open(led1,"w")
	f.write(str(value1))
	f.close()

class Channelnumber:

	def __init__(self, session):
		self.session = session
		self.sign = 0
		self.updatetime = 1000
		self.blink = False
		self.channelnrdelay = 15
		self.begin = int(time())
		self.endkeypress = True
		eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.keyPressed)
		self.zaPrik = eTimer()
		self.zaPrik.timeout.get().append(self.vrime)
		self.zaPrik.start(1000, 1)
		self.onClose = [ ]

		self.__event_tracker = ServiceEventTracker(screen=self,eventmap=
			{
				iPlayableService.evUpdatedEventInfo: self.__eventInfoChanged
			})

	def __eventInfoChanged(self):
		self.RecordingLed()
		if BOX not in ('gb800se', 'gb800solo', 'gb800seplus', 'gbultra', 'gbultrase'):
			return
		if config.plugins.VFD_Giga.showClock.value == 'Off' or config.plugins.VFD_Giga.showClock.value == 'True_All':
			return
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		if info is None:
			chnr = "----"
		else:
			chnr = self.getchannelnr()
		info = None
		service = None
		if chnr == "----":
			vfd_write(chnr)
		else:
			if config.plugins.VFD_Giga.channelnrformat.value =='True':
				Channelnr = "%04d" % (int(chnr))
			else:
				Channelnr = "% 4d" % (int(chnr))
			vfd_write(Channelnr)

	def getchannelnr(self):
		if InfoBar.instance is None:
			chnr = "----"
			return chnr
		MYCHANSEL = InfoBar.instance.servicelist
		markersOffset = 0
		myRoot = MYCHANSEL.getRoot()
		mySrv = MYCHANSEL.servicelist.getCurrent()
		chx = MYCHANSEL.servicelist.l.lookupService(mySrv)
		if not MYCHANSEL.inBouquet():
			pass
		else:
			serviceHandler = eServiceCenter.getInstance()
			mySSS = serviceHandler.list(myRoot)
			SRVList = mySSS and mySSS.getContent("SN", True)
			for i in range(len(SRVList)):
				if chx == i:
					break
				testlinet = SRVList[i]
				testline = testlinet[0].split(":")
				if testline[1] == "64":
					markersOffset = markersOffset + 1
		chx = (chx - markersOffset) + 1
		rx = MYCHANSEL.getBouquetNumOffset(myRoot)
		chnr = str(chx + rx)
		return chnr

	def prikaz(self):
		if config.plugins.VFD_Giga.showClock.value == 'True' or config.plugins.VFD_Giga.showClock.value == 'True_All' or config.plugins.VFD_Giga.showClock.value == 'True_Switch':
			clock = str(localtime()[3])
			clock1 = str(localtime()[4])
			clk = str(localtime()[5])
			if config.plugins.VFD_Giga.timeMode.value != '24h':
				if int(clock) > 12:
					clock = str(int(clock) - 12)

			if self.sign == 0:
				clock2 = "%02d:%02d" % (int(clock), int(clock1))
				self.sign = 1
			else:
				clock2 = "%02d%02d" % (int(clock), int(clock1))
				self.sign = 0
			vfd_write(clock2)
		else:
			vfd_write("    ")

	def vrime(self):
		self.RecordingLed()
		if BOX not in ('gb800se', 'gb800solo', 'gb800seplus', 'gbultra', 'gbultrase'):
			self.zaPrik.start(self.updatetime, 1)
			return

		if (config.plugins.VFD_Giga.showClock.value == 'True' or config.plugins.VFD_Giga.showClock.value == 'False' or config.plugins.VFD_Giga.showClock.value == 'True_Switch') and not Screens.Standby.inStandby:
			if config.plugins.VFD_Giga.showClock.value == 'True_Switch':
				if time() >= self.begin:
					self.endkeypress = False
				if self.endkeypress:
					self.__eventInfoChanged()
				else:
					self.prikaz()
			else:
				self.__eventInfoChanged()

		if config.plugins.VFD_Giga.showClock.value == 'Off':
			vfd_write("    ")
			self.zaPrik.start(self.updatetime, 1)
			return
		else:
			self.zaPrik.start(1000, 1)

		if Screens.Standby.inStandby or config.plugins.VFD_Giga.showClock.value == 'True_All':
			self.prikaz()

	def RecordingLed(self):
		global RecLed
		led_sda1 = "0"
		if config.plugins.VFD_Giga.ledSDA1.getValue() != "0":
			try:
				for hdd in harddiskmanager.HDDList():
					if hdd[1].getDeviceName().startswith("/dev/sda"):
						if not hdd[1].isSleeping():
							led_sda1 = config.plugins.VFD_Giga.ledSDA1.getValue()
			except:
				pass
		led_sdb1 = "0"
		if config.plugins.VFD_Giga.ledSDB1.getValue() != "0":
			try:
				for hdd in harddiskmanager.HDDList():
					if hdd[1].getDeviceName().startswith("/dev/sdb"):
						if not hdd[1].isSleeping():
							led_sdb1 = config.plugins.VFD_Giga.ledSDB1.getValue()
			except:
				pass
		try:
			#not all images support recording type indicators
			recordings = self.session.nav.getRecordings(False,Components.RecordingConfig.recType(config.recording.show_rec_symbol_for_rec_types.getValue()))
		except:
			recordings = self.session.nav.getRecordings()
		led_rec = "0"
		if recordings:
			self.updatetime = 1000
			if not config.plugins.VFD_Giga.recLedBlink.value:
				self.blink = True
			if self.blink:
				led_rec = config.plugins.VFD_Giga.ledREC.getValue()
			else:
				if config.plugins.VFD_Giga.ledREC.value == "3":
					led_rec = "2"
				else:
					led_rec = "0"
			self.blink = not self.blink
			RecLed = True
		else:
			if (config.plugins.VFD_Giga.ledSDA1.getValue() != "0") or (config.plugins.VFD_Giga.ledSDB1.getValue() != "0"):
				self.updatetime = 1000
			else:
				self.updatetime = 10000
			if RecLed is not None:
				RecLed = None
			if Screens.Standby.inStandby:
				led_rec = config.plugins.VFD_Giga.ledSBY.getValue()
			else:
				led_rec = config.plugins.VFD_Giga.ledRUN.getValue()
		setLed(str(int(led_sda1) | int(led_sdb1) | int(led_rec)))
					
	def keyPressed(self, key, tag):
		self.begin = time() + int(self.channelnrdelay)
		self.endkeypress = True

ChannelnumberInstance = None

def leaveStandby():
	print "[LED-GIGA] Leave Standby"

	if config.plugins.VFD_Giga.showClock.value == 'Off':
		vfd_write("    ")

	if RecLed is None:
		if config.plugins.VFD_Giga.setLed.value:
			setLed(config.plugins.VFD_Giga.ledRUN.getValue())
		else:
			setLed("0")
	else:
		setLed(config.plugins.VFD_Giga.ledREC.getValue())

	if BOX in ('gb800seplus', 'gbultra', 'gbultrase'):
		if config.plugins.VFD_Giga.vfdBrightness.value:
			setvfdBrightness(config.plugins.VFD_Giga.vfdBrightness.getValue())
		else:
			setvfdBrightness("255")

def standbyCounterChanged(configElement):
	print "[LED-GIGA] In Standby"

	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)

	if config.plugins.VFD_Giga.showClock.value == 'Off':
		vfd_write("    ")

	if RecLed is None:
		if config.plugins.VFD_Giga.setLed.value:
			setLed(config.plugins.VFD_Giga.ledSBY.getValue())
		else:
			setLed("0")
	else:
		setLed(config.plugins.VFD_Giga.ledREC.getValue())

	if BOX in ('gb800seplus', 'gbultra', 'gbultrase'):
		if config.plugins.VFD_Giga.vfdBrightnessStandby.value:
			setvfdBrightness(config.plugins.VFD_Giga.vfdBrightnessStandby.getValue())
		else:
			setvfdBrightness("0")

def initLED():
	print "[LED-GIGA] initVFD box = %s" % BOX

	if config.plugins.VFD_Giga.setLed.value:
		setLed(config.plugins.VFD_Giga.ledRUN.getValue())
	else:
		setLed("0")

	if config.plugins.VFD_Giga.showClockDeepStandby.value == 'True':
		forcmd = '1'
	else:
		forcmd = '0'
	if BOX in ("gbquad", "gbuhdquad", "gb800ueplus", "gbquadplus", "gbultraue", "gbultraueh", "gbipbox", "gbx1", "gbx2", "gbx3", "gbx3h"):
		cmd = 'echo STB does not support to show clock in Deep Standby'
	else:
		cmd = 'echo '+str(forcmd)+' > /proc/stb/fp/enable_clock'
	res = system(cmd)

	if config.plugins.VFD_Giga.showClock.value == 'Off':
		vfd_write("    ")

	if BOX in ('gb800seplus', 'gbultra', 'gbultrase'):
		if config.plugins.VFD_Giga.vfdBrightness.value:
			setvfdBrightness(config.plugins.VFD_Giga.vfdBrightness.getValue())
		else:
			setvfdBrightness("255")

class LED_GigaSetup(ConfigListScreen, Screen):
	def __init__(self, session, args = None):

		self.skin = """
			<screen position="center,center" size="700,540" title="GigaBlue Setup" >
				<widget name="config" position="20,15" size="660,450" scrollbarMode="showOnDemand" />
				<ePixmap position="40,470" size="140,40" pixmap="skin_default/buttons/green.png" alphatest="on" />
				<ePixmap position="180,470" size="140,40" pixmap="skin_default/buttons/red.png" alphatest="on" />
				<widget name="key_green" position="40,470" size="140,40" font="Regular;20" backgroundColor="#1f771f" zPosition="2" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_red" position="180,470" size="140,40" font="Regular;20" backgroundColor="#9f1313" zPosition="2" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			</screen>"""

		Screen.__init__(self, session)
		self.onClose.append(self.abort)

		self.onChangedEntry = [ ]
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)

		self.createSetup()

		self.Console = Console()
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		if BOX in ("gbquad", "gbuhdquad", "gb800ueplus", "gbquadplus", "gbultraue", "gbultraueh", "gbipbox", "gbx1", "gbx2", "gbx3", "gbx3h"):
			self["key_yellow"] = Button("")
		else:
			self["key_yellow"] = Button(_("Update Date/Time"))

		self["setupActions"] = ActionMap(["SetupActions","ColorActions"],
		{
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
			"yellow": self.Update,
		}, -2)

	def createSetup(self):
		self.editListEntry = None
		self.list = []
		self.list.append(getConfigListEntry(_("Enable led"), config.plugins.VFD_Giga.setLed))
		if config.plugins.VFD_Giga.setLed.value:
			self.list.append(getConfigListEntry(_("Led state RUN"), config.plugins.VFD_Giga.ledRUN))
			self.list.append(getConfigListEntry(_("Led state Standby"), config.plugins.VFD_Giga.ledSBY))
			if BOX not in ("gbquad", "gbuhdquad", "gb800ueplus", "gb800seplus", "gbquadplus", "gbipbox", "gbultra", "gbultraue", "gbultraueh", "gbultrase", "gbx1", "gbx2", "gbx3", "gbx3h"):
				self.list.append(getConfigListEntry(_("Led state Deep Standby"), config.plugins.VFD_Giga.ledDSBY))
			self.list.append(getConfigListEntry(_("Led state Record"), config.plugins.VFD_Giga.ledREC))
			self.list.append(getConfigListEntry(_("Blink Record Led"), config.plugins.VFD_Giga.recLedBlink))
			self.list.append(getConfigListEntry(_("Led state HDD /dev/sda active"), config.plugins.VFD_Giga.ledSDA1))
			self.list.append(getConfigListEntry(_("Led state HDD /dev/sdb active"), config.plugins.VFD_Giga.ledSDB1))
			setLed(config.plugins.VFD_Giga.ledRUN.getValue())
		else:
			setLed("0")

		if BOX in ("gb800seplus", "gbultra", "gbultrase"):
			self.list.append(getConfigListEntry(_("Brightness"), config.plugins.VFD_Giga.vfdBrightness))
			self.list.append(getConfigListEntry(_("Brightness Standby"), config.plugins.VFD_Giga.vfdBrightnessStandby))
		if BOX in ('gb800se', 'gb800solo', "gb800seplus", "gbultra", "gbultrase"):
			self.list.append(getConfigListEntry(_("Show on VFD"), config.plugins.VFD_Giga.showClock))
			self.list.append(getConfigListEntry(_("Show clock in Deep Standby"), config.plugins.VFD_Giga.showClockDeepStandby))
			if config.plugins.VFD_Giga.showClock.value != "Off" or config.plugins.VFD_Giga.showClockDeepStandby.value == "True":
				self.list.append(getConfigListEntry(_("Time mode"), config.plugins.VFD_Giga.timeMode))
			self.list.append(getConfigListEntry(_("Channel number with leading zeros"), config.plugins.VFD_Giga.channelnrformat))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.newConfig()

	def newConfig(self):
		# print self["config"].getCurrent()[0]
		if self["config"].getCurrent()[0] == _('Enable led'):
			self.createSetup()
		elif self["config"].getCurrent()[0][:3].upper() == 'LED':
			setLed(config.plugins.VFD_Giga.ledRUN.getValue())
		elif self["config"].getCurrent()[0] == _('Show on VFD'):
			self.createSetup()
		elif self["config"].getCurrent()[0] == _('Show clock in Deep Standby'):
			self.createSetup()
		elif self["config"].getCurrent()[0] == _('Brightness'):
			setvfdBrightness(config.plugins.VFD_Giga.vfdBrightness.getValue())
		elif self["config"].getCurrent()[0] == _('Brightness Standby'):
			setvfdBrightness(config.plugins.VFD_Giga.vfdBrightnessStandby.getValue())

	def abort(self):
		print "aborting"

	def save(self):
		for x in self["config"].list:
			x[1].save()

		configfile.save()
		initLED()
		self.close()

	def cancel(self):
		initLED()
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def Update(self):
		# still needed? I doubt it, as i can't see a difference for gbquad and other models with LCD
		#if BOX != "gbquad":
		self.createSetup()
		initLED()

class LED_Giga:
	def __init__(self, session):
		print "[LED-GIGA] initializing"
		self.session = session
		self.service = None
		self.onClose = [ ]

		self.Console = Console()

		initLED()
		self.Timer = eTimer()
		self.Timer.callback.append(self.delay_init)
		self.Timer.start(5000, True)

		global ChannelnumberInstance
		if ChannelnumberInstance is None:
			ChannelnumberInstance = Channelnumber(session)

	def shutdown(self):
		self.abort()

	def abort(self):
		print "[LED-GIGA] aborting"

	def delay_init(self):
		print "[LED-GIGA] delay init on boot"
		initLED()

	config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call = False)

def main(menuid, **kwargs):
	if getImageDistro() == "openvix":
		if BOX in ('gb800se', 'gb800solo', 'gbx1', 'gbx2', 'gbx3', 'gbx3h') and menuid == "leddisplay":
			return [(_("Display/LED"), startLED, "LED_Giga", None)]
		elif BOX in ('gb800seplus', 'gbultra', 'gbultrase') and menuid == "display":
			return [(_("Display/LED"), startLED, "LED_Giga", None)]
		elif menuid == "display":
			return [(_("LED"), startLED, "LED_Giga", None)]
		else:
			return []
	else:
		if getImageDistro() in ('openmips'):
			if menuid != "frontpanel_menu":
				return [ ]
		else:
			if menuid != "system":
				return [ ]
		if BOX in ('gb800se', 'gb800solo', 'gb800seplus', 'gbultra', 'gbultrase'):
			return [(_("Display/LED"), startLED, "LED_Giga", None)]
		else:
			return [(_("LED"), startLED, "LED_Giga", None)]

def startLED(session, **kwargs):
	session.open(LED_GigaSetup)

gigaLED = None
gReason = -1
mySession = None

def controlgigaLED():
	global gigaLED
	global gReason
	global mySession

	if gReason == 0 and mySession != None and gigaLED == None:
		print "[LED-GIGA] Starting !!"
		gigaLED = LED_Giga(mySession)
	elif gReason == 1 and gigaLED != None:
		print "[LED-GIGA] Stopping !!"
		gigaLED = None

def SetTime():
	print "[LED-GIGA] Set RTC time"
	import time
	if time.localtime().tm_isdst == 0:
		forsleep = 7200+time.timezone
	else:
		forsleep = 3600-time.timezone

	t_local = time.localtime(int(time.time()))
	print "set Gigabox RTC to %s (rtc_offset = %s sec.)" % (time.strftime("%Y/%m/%d %H:%M", t_local), forsleep)

	# Set RTC OFFSET (diff. between UTC and Local Time)
	try:		
		open("/proc/stb/fp/rtc_offset", "w").write(str(forsleep))
	except IOError:
		print "[LED-GIGA] set RTC Offset failed!"

	# Set RTC
	try:		
		open("/proc/stb/fp/rtc", "w").write(str(int(time.time())))
	except IOError:
		print "[LED-GIGA] set RTC time failed!"

def sessionstart(reason, **kwargs):
	print "[LED-GIGA] sessionstart"
	global gigaLED
	global gReason
	global mySession

	if kwargs.has_key("session"):
		mySession = kwargs["session"]
	else:
		gReason = reason
	controlgigaLED()

def Plugins(**kwargs):
	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
		PluginDescriptor(name="LED_Giga", description="Change LED display settings",where = PluginDescriptor.WHERE_MENU, fnc = main) ]

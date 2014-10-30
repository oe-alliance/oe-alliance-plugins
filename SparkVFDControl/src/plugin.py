# for localized messages
from . import _

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.Console import Console
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList
from Components.config import config, configfile, ConfigSubsection, getConfigListEntry, ConfigSelection
from Components.ConfigList import ConfigListScreen
from enigma import iPlayableService, eServiceCenter, eTimer, eActionMap
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ServiceList import ServiceList
from Screens.InfoBar import InfoBar
from time import localtime, time
from Tools.Directories import fileExists

from boxbranding import getBoxType

import Screens.Standby
import NavigationInstance
from Screens.SessionGlobals import SessionGlobals

config.plugins.VFD_spark = ConfigSubsection()
config.plugins.VFD_spark.showClock = ConfigSelection(default = "True_Switch", choices = [("NameOff",_("Channelname in Standby off")), ("NameOn",_("Channelname in Standby Clock")), ("False",_("Channelnumber in Standby off")),("True",_("Channelnumber in Standby Clock")), ("True_Switch",_("Channelnumber/Clock in Standby Clock")),("True_All",_("Clock always")),("Off",_("Always off"))])
config.plugins.VFD_spark.timeMode = ConfigSelection(default = "24h", choices = [("12h"),("24h")])
config.plugins.VFD_spark.redLed = ConfigSelection(default = "0", choices = [("0",_("Off")),("1",_("Standby only")), ("2",_("Record only"))])
config.plugins.VFD_spark.greenLed = ConfigSelection(default = "0", choices = [("0",_("Off")),("1",_("Standby only"))])

def vfd_write(text):
	open("/dev/dbox/oled0", "w").write(text)

class Channelnumber:

	def __init__(self, session):
		self.session = session
		self.sign = 0
		self.updatetime = 10000
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
		session.nav.record_event.append(self.gotRecordEvent)

	def __eventInfoChanged(self):
		val = config.plugins.VFD_spark.showClock.value
		if val == 'Off' or val == 'True_All':
			return
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		if info is None:
			chnr = "----"
			name = "----"
		else:
			if val == 'NameOff' or val == 'NameOn':
				na = info.getName()
				name = na.replace('\xc2\x87', '').replace('\xc2\x86', '')
			else:
				chnr = self.getchannelnr()
		info = None
		service = None
		if val == 'NameOff' or val == 'NameOn':
			if name == "----":
				vfd_write(name)
			else:
				vfd_write(name)
		else:
			if chnr == "----":
				vfd_write(chnr)
			else:
				Channelnr = "%04d" % (int(chnr))
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
		val = config.plugins.VFD_spark.showClock.value
		if val == 'True' or val == 'NameOn' or val == 'True_All' or val == 'True_Switch':
			clock = str(localtime()[3])
			clock1 = str(localtime()[4])
			if config.plugins.VFD_spark.timeMode.value != '24h':
				if int(clock) > 12:
					clock = str(int(clock) - 12)

			if self.sign == 0:
				clock2 = "%02d.%02d" % (int(clock), int(clock1))
				self.sign = 1
			else:
				clock2 = "%02d%02d" % (int(clock), int(clock1))
				self.sign = 0

			vfd_write(clock2)
		else:
			vfd_write("....")

	def vrime(self):
		val = config.plugins.VFD_spark.showClock.value
		if (val == 'True' or val == 'False' or val == 'NameOff' or val == 'NameOn' or val == 'True_Switch') and not Screens.Standby.inStandby:
			if val == 'True_Switch':
				if time() >= self.begin:
					self.endkeypress = False
				if self.endkeypress:
					self.__eventInfoChanged()
				else:
					self.prikaz()
			else:
				self.__eventInfoChanged()
					
		if val == 'Off':
			vfd_write("....")
			self.zaPrik.start(self.updatetime, 1)
			return
		else:
			self.zaPrik.start(1000, 1)

		if Screens.Standby.inStandby or val == 'True_All':
			self.prikaz()

	def keyPressed(self, key, tag):
		self.begin = time() + int(self.channelnrdelay)
		self.endkeypress = True

	def gotRecordEvent(self, service, event):
		if config.plugins.VFD_spark.redLed.value == '2':
			self.RecTimer = eTimer()
			self.RecTimer.callback.append(self.showRec)
			self.RecTimer.start(1000, True)
    
	def showRec(self):
		recordings = len(NavigationInstance.instance.getRecordings())
		
		if recordings >= 1:
			pattern = 4294967295
			f = open("/proc/stb/fp/led0_pattern", "w")
			f.write("%08x" % pattern)
			f.close()
		else:
			pattern = 0
			f = open("/proc/stb/fp/led0_pattern", "w")
			f.write("%08x" % pattern)
			f.close()

ChannelnumberInstance = None

def leaveStandby():
	print "[VFD-SPARK] Leave Standby"

	if config.plugins.VFD_spark.showClock.value == 'Off':
		vfd_write("....")

def standbyCounterChanged(configElement):
	print "[VFD-SPARK] In Standby"

	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)

	if config.plugins.VFD_spark.showClock.value == 'Off':
		vfd_write("....")

def initVFD():
	print "[VFD-SPARK] initVFD"

	if config.plugins.VFD_spark.showClock.value == 'Off':
		vfd_write("....")

class VFD_SPARKSetup(ConfigListScreen, Screen):
	def __init__(self, session, args = None):

		self.skin = """
			<screen position="100,100" size="500,210" title="LED Display Setup" >
				<widget name="config" position="20,15" size="460,150" scrollbarMode="showOnDemand" />
				<ePixmap position="40,165" size="140,40" pixmap="skin_default/buttons/green.png" alphatest="on" />
				<ePixmap position="180,165" size="140,40" pixmap="skin_default/buttons/red.png" alphatest="on" />
				<widget name="key_green" position="40,165" size="140,40" font="Regular;20" backgroundColor="#1f771f" zPosition="2" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_red" position="180,165" size="140,40" font="Regular;20" backgroundColor="#9f1313" zPosition="2" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
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
		self.list.append(getConfigListEntry(_("Show on VFD"), config.plugins.VFD_spark.showClock))
		if config.plugins.VFD_spark.showClock.value != "Off":
			self.list.append(getConfigListEntry(_("Time mode"), config.plugins.VFD_spark.timeMode))
		self.list.append(getConfigListEntry(_("Show red LED on VFD"), config.plugins.VFD_spark.redLed))
		self.list.append(getConfigListEntry(_("Show green LED on VFD"), config.plugins.VFD_spark.greenLed))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.newConfig()

	def newConfig(self):
		print self["config"].getCurrent()[0]
		if self["config"].getCurrent()[0] == _('Show on VFD'):
			self.createSetup()

	def abort(self):
		print "aborting"

	def save(self):
		for x in self["config"].list:
			x[1].save()

		configfile.save()
		initVFD()
		self.close()

	def cancel(self):
		initVFD()
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def Update(self):
		self.createSetup()
		initVFD()

class VFD_SPARK:
	def __init__(self, session):
		print "[VFD-SPARK] initializing"
		self.session = session
		self.service = None
		self.onClose = [ ]

		self.Console = Console()

		initVFD()

		global ChannelnumberInstance
		if ChannelnumberInstance is None:
			ChannelnumberInstance = Channelnumber(session)

	def shutdown(self):
		self.abort()

	def abort(self):
		print "[VFD-SPARK] aborting"
		config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call = False)

baseSessionGlobals__init__ = None
SessionGlobals_instance = None

def newSessionGlobals__init__(self, session):
	baseSessionGlobals__init__(self, session)
	global SessionGlobals_instance
	SessionGlobals_instance = self
	from Components.Sources.CurrentService import CurrentService
	from Components.Sources.EventInfo import EventInfo
	from Components.Sources.FrontendStatus import FrontendStatus
	from Components.Sources.FrontendInfo import FrontendInfo
	from Components.Sources.Source import Source
	from Components.Sources.TunerInfo import TunerInfo
	from Components.Sources.Boolean import Boolean
	from Components.Sources.RecordState import RecordState
	from Components.Converter.Combine import Combine
	from Components.Renderer.FrontpanelLed import FrontpanelLed
	self["CurrentService"] = CurrentService(session.nav)
	self["Event_Now"] = EventInfo(session.nav, EventInfo.NOW)
	self["Event_Next"] = EventInfo(session.nav, EventInfo.NEXT)
	self["FrontendStatus"] = FrontendStatus(service_source = session.nav.getCurrentService)
	self["FrontendInfo"] = FrontendInfo(navcore = session.nav)
	self["VideoPicture"] = Source()
	self["TunerInfo"] = TunerInfo()
	self["RecordState"] = RecordState(session)
	self["Standby"] = Boolean(fixed = False)

	from Components.SystemInfo import SystemInfo

	combine = Combine(func = lambda s: {(False, False): 0, (False, True): 1, (True, False): 2, (True, True): 3}[(s[0].boolean, s[1].boolean)])
	combine.connect(self["Standby"])
	combine.connect(self["RecordState"])

	#                      |  two leds  | single led |
	# recordstate  standby   red green
	#    false      false    off   on     off
	#    true       false    blnk  on     blnk
	#    false      true      on   off    off
	#    true       true     blnk  off    blnk

	PATTERN_ON     = (20, 0xffffffff, 0xffffffff)
	PATTERN_OFF    = (20, 0, 0)
	PATTERN_BLINK  = (20, 0x55555555, 0xa7fccf7a)

	nr_leds = SystemInfo.get("NumFrontpanelLEDs", 0)

	if nr_leds == 1:
		FrontpanelLed(which = 0, boolean = False, patterns = [PATTERN_OFF, PATTERN_BLINK, PATTERN_OFF, PATTERN_BLINK]).connect(combine)
	elif nr_leds == 2:
		if config.plugins.VFD_spark.redLed.value == '1':
			FrontpanelLed(which = 0, boolean = False, patterns = [PATTERN_OFF, PATTERN_BLINK, PATTERN_ON, PATTERN_BLINK]).connect(combine)
		if config.plugins.VFD_spark.greenLed.value == '1':
			FrontpanelLed(which = 1, boolean = False, patterns = [PATTERN_OFF, PATTERN_OFF, PATTERN_ON, PATTERN_OFF]).connect(combine)
		else:
			FrontpanelLed(which = 0, boolean = False, patterns = [PATTERN_OFF, PATTERN_OFF, PATTERN_OFF, PATTERN_OFF]).connect(combine)
			FrontpanelLed(which = 1, boolean = False, patterns = [PATTERN_OFF, PATTERN_OFF, PATTERN_OFF, PATTERN_OFF]).connect(combine)


def main(menuid):
	if menuid != "system":
		return [ ]
	return [(_("LED Display Setup"), startVFD, "VFD_SPARK", None)]

def startVFD(session, **kwargs):
	session.open(VFD_SPARKSetup)

sparkVfd = None
gReason = -1
mySession = None

def controlsparkVfd():
	global sparkVfd
	global gReason
	global mySession

	if gReason == 0 and mySession != None and sparkVfd == None:
		print "[VFD-SPARK] Starting !!"
		sparkVfd = VFD_SPARK(mySession)
	elif gReason == 1 and sparkVfd != None:
		print "[VFD-SPARK] Stopping !!"

		sparkVfd = None

def sessionstart(reason, **kwargs):
	print "[VFD-SPARK] sessionstart"
	global sparkVfd
	global gReason
	global mySession

	if kwargs.has_key("session"):
		mySession = kwargs["session"]
	else:
		gReason = reason
	controlsparkVfd()
	global baseSessionGlobals__init__	
	if baseSessionGlobals__init__ is None:
		baseSessionGlobals__init__ = SessionGlobals.__init__
		SessionGlobals.__init__ = newSessionGlobals__init__

def Plugins(**kwargs):
		if getBoxType() in ('amiko8900', 'sognorevolution', 'arguspingulux', 'arguspinguluxmini', 'sparkreloaded', 'sabsolo', 'sparklx', 'gis8120', 'amikomini'):
			return [ PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
				PluginDescriptor(name="LED Display Setup", description="Change VFD display settings",where = PluginDescriptor.WHERE_MENU, fnc = main) ]
		else:
			return []

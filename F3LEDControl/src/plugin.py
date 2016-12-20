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
import Screens.Standby
from time import localtime, time
from Tools.Directories import fileExists

from boxbranding import getImageDistro, getBoxType

import Screens.Standby

config.plugins.SEG = ConfigSubsection()
config.plugins.SEG.showClock = ConfigSelection(default = "True_Switch", choices = [("False",_("Channelnumber in Standby off")),("True",_("Channelnumber in Standby Clock")), ("True_Switch",_("Channelnumber/Clock in Standby Clock")),("True_All",_("Clock always")),("Off",_("Always off"))])
config.plugins.SEG.showCHnumber = ConfigSelection(default = "15", choices = [("15",_("15 sec")),("30",_("30 sec")),("45",_("45 sec")),("60",_("60 sec"))])
config.plugins.SEG.timeMode = ConfigSelection(default = "24h", choices = [("12h"),("24h")])

def display_write(text):
	open("/dev/dbox/oled0", "w").write(text)

class Channelnumber:

	def __init__(self, session):
		self.session = session
		self.sign = 0
		self.updatetime = 15000
		self.blink = False
		self.channelnrdelay = config.plugins.SEG.showCHnumber.value
		self.dvb_service = ""
		self.begin = int(time())
		self.endkeypress = True
		eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.keyPressed)
		self.TimerText = eTimer()
		self.TimerText.timeout.get().append(self.showclock)
		self.TimerText.start(1000, True)
		self.onClose = [ ]

		self.__event_tracker = ServiceEventTracker(screen=self,eventmap=
			{
				iPlayableService.evStart: self.__evStart,
			})

	def __evStart(self):
		self.getCurrentlyPlayingService()

	def getCurrentlyPlayingService(self):
		playref = self.session.nav.getCurrentlyPlayingServiceReference()
		if not playref:
			self.dvb_service = ""
		else:
			str_service = playref.toString()
			if not '%3a//' in str_service and str_service.rsplit(":", 1)[1].startswith("/"):
				self.dvb_service = "video"
			else:
				self.dvb_service = ""

	def __eventInfoChanged(self, manual=False):
		if config.plugins.SEG.showClock.value == 'Off' or config.plugins.SEG.showClock.value == 'True_All':
			return
		if self.dvb_service == "":
			self.text = "----"
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			if info is None:
				self.text = "----"
			else:
				self.text = self.getchannelnr()
			info = None
			service = None
			if self.text == "----":
				display_write(self.text)
			else:
				Channelnr = "%04d" % (int(self.text))
				display_write(Channelnr)
		else:
			self.text = "----"
			return self.text

	def getchannelnr(self):
		MYCHANSEL = InfoBar.instance.servicelist
		serviceHandler = eServiceCenter.getInstance()
		myRoot = MYCHANSEL.servicelist.getRoot()
		mySSS = serviceHandler.list(myRoot)
		SRVList = mySSS and mySSS.getContent("SN", True)
		markersOffset = 0
		mySrv = MYCHANSEL.servicelist.getCurrent()
		chx = MYCHANSEL.servicelist.l.lookupService(mySrv)
		for i in range(len(SRVList)):
			if chx == i:
				break
			testlinet = SRVList[i]
			testline = testlinet[0].split(":")
			if testline[1] == "64":
				markersOffset = markersOffset + 1
		chx = (chx - markersOffset) + 1
		rx = MYCHANSEL.getBouquetNumOffset(myRoot)
		self.text = str(chx + rx)
		return self.text

	def show(self):
		if config.plugins.SEG.showClock.value == 'True' or config.plugins.SEG.showClock.value == 'True_All' or config.plugins.SEG.showClock.value == 'True_Switch':
			clock = str(localtime()[3])
			clock1 = str(localtime()[4])
			if config.plugins.SEG.timeMode.value != '24h':
				if int(clock) > 12:
					clock = str(int(clock) - 12)

			if self.sign == 0:
				clock2 = "%02d:%02d" % (int(clock), int(clock1))
				self.sign = 1
			else:
				clock2 = "%02d%02d" % (int(clock), int(clock1))
				self.sign = 0
			display_write(clock2)
		else:
			display_write("....")

	def showclock(self):
		standby_mode = Screens.Standby.inStandby
		if (config.plugins.SEG.showClock.value == 'True' or config.plugins.SEG.showClock.value == 'False' or config.plugins.SEG.showClock.value == 'True_Switch') and not Screens.Standby.inStandby:
			if config.plugins.SEG.showClock.value == 'True_Switch':
				if time() >= self.begin:
					self.endkeypress = False
				if self.endkeypress:
					self.__eventInfoChanged(True)
				else:
					self.show()
			else:
				self.__eventInfoChanged(True)
					
		if config.plugins.SEG.showClock.value == 'Off':
			display_write("....")
			self.TimerText.start(self.updatetime, True)
			return
		else:
			update_time = 1000
			if not standby_mode and self.dvb_service == "video":
				update_time = 15000
			self.TimerText.start(update_time, True)

		if standby_mode:
			self.show()

	def keyPressed(self, key, tag):
		self.begin = time() + int(self.channelnrdelay)
		self.endkeypress = True

ChannelnumberInstance = None

def leaveStandby():
	if config.plugins.SEG.showClock.value == 'Off':
		display_write("....")

def standbyCounterChanged(configElement):
	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)
	if config.plugins.SEG.showClock.value == 'Off':
		display_write("....")

def initSEG():
	if config.plugins.SEG.showClock.value == 'Off':
		display_write("....")

class VFD_INISetup(ConfigListScreen, Screen):
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
		self.setTitle(_("LED Display Setup"))
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
			"save": self.Save,
			"cancel": self.Cancel,
			"ok": self.Save,
			"yellow": self.Update,
		}, -2)

	def createSetup(self):
		self.editListEntry = None
		self.list = []
		self.list.append(getConfigListEntry(_("Show on LED"), config.plugins.SEG.showClock))
		self.list.append(getConfigListEntry(_("Time to show Clock in Display"), config.plugins.SEG.showCHnumber))
		if config.plugins.SEG.showClock.value != "Off":
			self.list.append(getConfigListEntry(_("Time mode"), config.plugins.SEG.timeMode))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.newConfig()

	def newConfig(self):
		if self["config"].getCurrent()[0] == _('Show on LED'):
			self.createSetup()

	def abort(self):
		pass

	def saveAll(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		initSEG()

	def Save(self):
		self.saveAll()
		self.close()

	def Cancel(self):
		self.saveAll()
		self.close()

	def Update(self):
		self.createSetup()
		initSEG()

class SEG:
	def __init__(self, session):
		self.session = session
		self.service = None
		self.onClose = [ ]
		self.Console = Console()
		initSEG()

		global ChannelnumberInstance
		if ChannelnumberInstance is None:
			ChannelnumberInstance = Channelnumber(session)

	def shutdown(self):
		self.abort()

	def abort(self):
		config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call = False)

def main(menuid):
		if getImageDistro() in ("openatv"):
			if menuid == "display":
				return [(_("LED Display Setup"), startSEG, "VFD_INI", None)]
			else:
				return[ ]
		else:
			if menuid != "system":
				return [ ]
			else:
				return [(_("LED Display Setup"), startSEG, "VFD_INI", None)]

def startSEG(session, **kwargs):
	session.open(VFD_INISetup)

Seg = None
gReason = -1
mySession = None

def controlSeg():
	global Seg
	global gReason
	global mySession

	if gReason == 0 and mySession != None and Seg == None:
		Seg = SEG(mySession)
	elif gReason == 1 and Seg != None:
		Seg = None

def sessionstart(reason, **kwargs):
	global Seg
	global gReason
	global mySession

	if kwargs.has_key("session"):
		mySession = kwargs["session"]
	else:
		gReason = reason
	controlSeg()

def Plugins(**kwargs):
	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
		PluginDescriptor(name="LED Display Setup", description="Change LED display settings",where = PluginDescriptor.WHERE_MENU, fnc = main) ]


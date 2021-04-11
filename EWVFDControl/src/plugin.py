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

import Screens.Standby

config.plugins.vfd_ew = ConfigSubsection()
config.plugins.vfd_ew.showClock = ConfigSelection(default="True_Switch", choices=[("False", _("Channelnumber in Standby off")), ("True", _("Channelnumber in Standby Clock")), ("True_Switch", _("Channelnumber/Clock in Standby Clock")), ("True_All", _("Clock always")), ("Off", _("Always off"))])
config.plugins.vfd_ew.timeMode = ConfigSelection(default="24h", choices=[("12h"), ("24h")])


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
		self.onClose = []

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUpdatedEventInfo: self.__eventInfoChanged
			})

	def __eventInfoChanged(self):
		if config.plugins.vfd_ew.showClock.value == 'Off' or config.plugins.vfd_ew.showClock.value == 'True_All':
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
		if config.plugins.vfd_ew.showClock.value == 'True' or config.plugins.vfd_ew.showClock.value == 'True_All' or config.plugins.vfd_ew.showClock.value == 'True_Switch':
			clock = str(localtime()[3])
			clock1 = str(localtime()[4])
			if config.plugins.vfd_ew.timeMode.value != '24h':
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
			vfd_write("....")

	def vrime(self):
		if (config.plugins.vfd_ew.showClock.value == 'True' or config.plugins.vfd_ew.showClock.value == 'False' or config.plugins.vfd_ew.showClock.value == 'True_Switch') and not Screens.Standby.inStandby:
			if config.plugins.vfd_ew.showClock.value == 'True_Switch':
				if time() >= self.begin:
					self.endkeypress = False
				if self.endkeypress:
					self.__eventInfoChanged()
				else:
					self.prikaz()
			else:
				self.__eventInfoChanged()

		if config.plugins.vfd_ew.showClock.value == 'Off':
			vfd_write("....")
			self.zaPrik.start(self.updatetime, 1)
			return
		else:
			self.zaPrik.start(1000, 1)

		if Screens.Standby.inStandby or config.plugins.vfd_ew.showClock.value == 'True_All':
			self.prikaz()

	def keyPressed(self, key, tag):
		self.begin = time() + int(self.channelnrdelay)
		self.endkeypress = True


ChannelnumberInstance = None


def leaveStandby():
	print "[VFD-EW] Leave Standby"

	if config.plugins.vfd_ew.showClock.value == 'Off':
		vfd_write("....")


def standbyCounterChanged(configElement):
	print "[VFD-EW] In Standby"

	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)

	if config.plugins.vfd_ew.showClock.value == 'Off':
		vfd_write("....")


def initVFD():
	print "[VFD-EW] initVFD"

	if config.plugins.vfd_ew.showClock.value == 'Off':
		vfd_write("....")


class vfd_ewSetup(ConfigListScreen, Screen):
	def __init__(self, session, args=None):

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

		self.onChangedEntry = []
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)

		self.createSetup()

		self.Console = Console()
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Update Date/Time"))

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
			"yellow": self.Update,
		}, -2)

	def createSetup(self):
		self.editListEntry = None
		self.list = []
		self.list.append(getConfigListEntry(_("Show on LED"), config.plugins.vfd_ew.showClock))
		if config.plugins.vfd_ew.showClock.value != "Off":
			self.list.append(getConfigListEntry(_("Time mode"), config.plugins.vfd_ew.timeMode))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.newConfig()

	def newConfig(self):
		print self["config"].getCurrent()[0]
		if self["config"].getCurrent()[0] == _('Show on LED'):
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


class vfd_ew:
	def __init__(self, session):
		print "[VFD-EW] initializing"
		self.session = session
		self.service = None
		self.onClose = []

		self.Console = Console()

		initVFD()

		global ChannelnumberInstance
		if ChannelnumberInstance is None:
			ChannelnumberInstance = Channelnumber(session)

	def shutdown(self):
		self.abort()

	def abort(self):
		print "[VFD-EW] aborting"
		config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call=False)


def main(menuid):
	if menuid != "system":
		return []
	return [(_("LED Display Setup"), startVFD, "vfd_ew", None)]


def startVFD(session, **kwargs):
	session.open(vfd_ewSetup)


ewVfd = None
gReason = -1
mySession = None


def controlewVfd():
	global ewVfd
	global gReason
	global mySession

	if gReason == 0 and mySession != None and ewVfd == None:
		print "[VFD-EW] Starting !!"
		ewVfd = vfd_ew(mySession)
	elif gReason == 1 and ewVfd != None:
		print "[VFD-EW] Stopping !!"

		ewVfd = None


def sessionstart(reason, **kwargs):
	print "[VFD-EW] sessionstart"
	global ewVfd
	global gReason
	global mySession

	if "session" in kwargs:
		mySession = kwargs["session"]
	else:
		gReason = reason
	controlewVfd()


def Plugins(**kwargs):
		if fileExists("/proc/stb/fp/version"):
			file = open("/proc/stb/fp/version")
			version = file.read().strip().lower()
			file.close()
		if version.startswith('2'):
			return []
		else:
			return [PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
				PluginDescriptor(name="LED Display Setup", description="Change LED display settings", where=PluginDescriptor.WHERE_MENU, fnc=main)]

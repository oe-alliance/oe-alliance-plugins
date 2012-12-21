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
from enigma import iPlayableService, eServiceCenter, eTimer
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ServiceList import ServiceList
from Screens.InfoBar import InfoBar
from time import localtime, time

import Screens.Standby

config.plugins.VFD_mara = ConfigSubsection()
config.plugins.VFD_mara.showClock = ConfigSelection(default = _("Yes"), choices = [("False",_("in standby: ") + _("No")),("True",_("in standby: ") + _("Yes")),("True_All",_("Yes")),("Off",_("Off"))])
config.plugins.VFD_mara.timeMode = ConfigSelection(default = "24h", choices = [("12h"),("24h")])

def vfd_write(text):
	open("/dev/dbox/oled0", "w").write(text)

class Channelnumber:

	def __init__(self, session):
		self.session = session
		self.sign = 1
		self.updatetime = 10000
		self.blink = False
		self.zaPrik = eTimer()
		self.zaPrik.timeout.get().append(self.vrime)
		self.zaPrik.start(1000, 1)
		self.onClose = [ ]

		self.__event_tracker = ServiceEventTracker(screen=self,eventmap=
			{
				iPlayableService.evUpdatedEventInfo: self.__eventInfoChanged
			})

	def __eventInfoChanged(self):
		if config.plugins.VFD_mara.showClock.value == 'Off' or config.plugins.VFD_mara.showClock.value == 'True_All':
			return
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		if info is None:
			chnr = "---"
		else:
			chnr = self.getchannelnr()
		info = None
		service = None
		########## Center Channel number #################
		t = len(chnr)
		if t == 1:
			CentChnr = " " + chnr + "  " + '\n'
		elif t == 2:
			CentChnr = " " + chnr + " " + '\n'
		elif t == 3:
			CentChnr = chnr + " " + '\n'
		else:
			CentChnr = chnr + '\n'
		#################################################

		vfd_write(CentChnr)

	def getchannelnr(self):
		if InfoBar.instance is None:
			chnr = "---"
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
		if config.plugins.VFD_mara.showClock.value == 'True' or config.plugins.VFD_mara.showClock.value == 'True_All':
			clock = str(localtime()[3])
			clock1 = str(localtime()[4])
			if config.plugins.VFD_mara.timeMode.value != '24h':
				if int(clock) > 12:
					clock = str(int(clock) - 12)

			if self.sign == 0:
				clock2 = "%02d:%02d" % (int(clock), int(clock1))
				self.sign = 1
			else:
				clock2 = "%02d%02d" % (int(clock), int(clock1))
				self.sign = 1 # disable : because it's not working yet

			vfd_write(clock2)
		else:
			vfd_write("    ")

	def vrime(self):
		if config.plugins.VFD_mara.showClock.value == 'Off':
			vfd_write("    ")
			self.zaPrik.start(self.updatetime, 1)
			return
		else:
			self.zaPrik.start(1000, 1)

		if Screens.Standby.inStandby or config.plugins.VFD_mara.showClock.value == 'True_All':
			self.prikaz()

ChannelnumberInstance = None

def leaveStandby():
	print "[VFD-MARAM7] Leave Standby"

	if config.plugins.VFD_mara.showClock.value == 'Off':
		vfd_write("    ")

def standbyCounterChanged(configElement):
	print "[VFD-MARAM7] In Standby"

	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)

	if config.plugins.VFD_mara.showClock.value == 'Off':
		vfd_write("    ")

def initVFD():
	print "[VFD-MARAM7] initVFD"

	if config.plugins.VFD_mara.showClock.value == 'Off':
		vfd_write("    ")

class VFD_MaraM7Setup(ConfigListScreen, Screen):
	def __init__(self, session, args = None):

		self.skin = """
			<screen position="100,100" size="500,210" title="VFD_MaraM7 Setup" >
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
		self.list.append(getConfigListEntry(_("Show clock"), config.plugins.VFD_mara.showClock))
		if config.plugins.VFD_mara.showClock.value != "Off":
			self.list.append(getConfigListEntry(_("Time mode"), config.plugins.VFD_mara.timeMode))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.newConfig()

	def newConfig(self):
		print self["config"].getCurrent()[0]
		if self["config"].getCurrent()[0] == _('Show clock'):
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

class VFD_Mara:
	def __init__(self, session):
		print "[VFD-MARAM7] initializing"
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
		print "[VFD-MARAM7] aborting"
		config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call = False)

def main(menuid):
	if menuid != "system":
		return [ ]
	return [(_("VFD_MaraM7"), startVFD, "VFD_MaraM7", None)]

def startVFD(session, **kwargs):
	session.open(VFD_MaraM7Setup)

maram7Vfd = None
gReason = -1
mySession = None

def controlmaram7Vfd():
	global maram7Vfd
	global gReason
	global mySession

	if gReason == 0 and mySession != None and maram7Vfd == None:
		print "[VFD-MARAM7] Starting !!"
		maram7Vfd = VFD_Mara(mySession)
	elif gReason == 1 and maram7Vfd != None:
		print "[VFD-MARAM7] Stopping !!"

		maram7Vfd = None

def sessionstart(reason, **kwargs):
	print "[VFD-MARAM7] sessionstart"
	global maram7Vfd
	global gReason
	global mySession

	if kwargs.has_key("session"):
		mySession = kwargs["session"]
	else:
		gReason = reason
	controlmaram7Vfd()

def Plugins(**kwargs):
 	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
 		PluginDescriptor(name="VFD_MaraM7", description="Change VFD display settings",where = PluginDescriptor.WHERE_MENU, fnc = main) ]

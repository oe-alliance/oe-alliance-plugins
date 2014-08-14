# for localized messages
from . import _

from Screens.Screen import Screen
from Components.Console import Console
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.config import config, configfile, ConfigSubsection, ConfigEnableDisable, getConfigListEntry, ConfigInteger, ConfigSelection, ConfigYesNo
from Components.ConfigList import ConfigListScreen, ConfigList
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import ServiceReference
from enigma import iPlayableService, eServiceCenter, eTimer, eDVBLocalTimeHandler, iServiceInformation
from os import system
from Plugins.Plugin import PluginDescriptor
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ServiceList import ServiceList
from Screens.InfoBar import InfoBar
from time import localtime, strftime
import Screens.Standby
import shlex, subprocess

config.plugins.VFD_spark = ConfigSubsection()
config.plugins.VFD_spark.ledMode = ConfigSelection(default = "True", choices = [("False",_("Led in Standby off")),("True",_("Led in Standby on"))])
config.plugins.VFD_spark.textMode = ConfigSelection(default = "ChName", choices = [("ChNumber",_("Channel number")),("ChName",_("Channel name"))])

def vfd_write_string(text):
	open("/dev/vfd", "w").write(text)

def vfd_set_icon(icon, on):
	text='i'+str(on)+str(icon)+' '
	open("/proc/stb/fp/aotom", "w").write(text);

def vfd_set_led(on):
	text='l'+str(on)+'0'+' '
        open("/proc/stb/fp/aotom", "w").write(text);

def vfd_clear():
        vfd_write_string('                ')
        vfd_set_icon(46,0)

class Channelnumber:

	def __init__(self, session):
		self.session = session
		self.onClose = [ ]
		self.__event_tracker = ServiceEventTracker(screen=self,eventmap=
			{
				iPlayableService.evUpdatedInfo: self.__eventInfoChanged,
				iPlayableService.evVideoSizeChanged: self.__videoSizeChanged
			})
		session.nav.record_event.append(self.gotRecordEvent)
		self.mp3Available = False
		self.dolbyAvailable = False

	def __eventInfoChanged(self):
		if Screens.Standby.inStandby:
			return
		if config.plugins.VFD_spark.textMode.value == 'ChNumber':
			vfdtext = self.getChannelNr()
		elif config.plugins.VFD_spark.textMode.value == 'ChName':
			vfdtext = self.getChannelName()
		else:
			vfdtext = "---"
		vfd_write_string(vfdtext)
		self.checkAudioTracks()
		self.showCrypted()
		self.showDolby()
		self.showMp3()

	def __videoSizeChanged(self):
                if Screens.Standby.inStandby:
                        return
		service=self.session.nav.getCurrentService()
		if service is not None:
			info=service.info()
			height = info and info.getInfo(iServiceInformation.sVideoHeight) or -1
			if height > 576 : #set HD symbol
				vfd_set_icon(14,1)
			else:
				vfd_set_icon(14,0)

	def getChannelNr(self):
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
		########## Center Channel number #################
		t = len(chnr)
		if t == 1:
			CentChnr = "000" + chnr + '\n'
		elif t == 2:
			CentChnr = "00" + chnr + '\n'
		elif t == 3:
			CentChnr = "0" + chnr + '\n'
		else:
			CentChnr = chnr + '\n'
		#################################################
		return CentChnr

	def getChannelName(self):
		servicename = ""
		currPlay = self.session.nav.getCurrentService()
		if currPlay != None and self.mp3Available:
			# show the MP3 tag
			servicename = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
		else:
			# show the service name
			self.service = self.session.nav.getCurrentlyPlayingServiceReference()
			if not self.service is None:
				service = self.service.toCompareString()
				servicename = ServiceReference.ServiceReference(service).getServiceName().replace('\xc2\x87', '').replace('\xc2\x86', '').ljust(16)
				subservice = self.service.toString().split("::")
				if subservice[0].count(':') == 9:
					servicename = subservice[1].replace('\xc2\x87', '').replace('\xc3\x9f', 'ss').replace('\xc2\x86', '').ljust(16)
				else:
					servicename=servicename
			else:
				servicename="---"
		return servicename

	def showCrypted(self):
		service=self.session.nav.getCurrentService()
		if service is not None:
			info=service.info()
			crypted = info and info.getInfo(iServiceInformation.sIsCrypted) or -1
			if crypted == 1 : #set crypt symbol
				vfd_set_icon(11,1)
			else:
				vfd_set_icon(11,0)

	def checkAudioTracks(self):
		self.dolbyAvailable = False
		self.mp3Available = False
		service=self.session.nav.getCurrentService()
		if service is not None:
			audio = service.audioTracks()
			if audio:
				n = audio.getNumberOfTracks()
				for x in range(n):
					i = audio.getTrackInfo(x)
					description = i.getDescription();
					if description.find("MP3") != -1:
						self.mp3Available = True
					if description.find("AC3") != -1 or description.find("DTS") != -1:
						self.dolbyAvailable = True

	def showDolby(self):
		if self.dolbyAvailable:
			vfd_set_icon(10,1)
		else:
			vfd_set_icon(10,0)

	def showMp3(self):
		if self.mp3Available:
			vfd_set_icon(25,1)
		else:
			vfd_set_icon(25,0)

	def gotRecordEvent(self, service, event):
		recs = self.session.nav.getRecordings()
		nrecs = len(recs)
		if nrecs > 0: #set rec symbol
			vfd_set_icon(7,1)
		else:
			vfd_set_icon(7,0)

ChannelnumberInstance = None

def leaveStandby():
	print "[VFD-SPARK] Leave Standby"
	vfd_write_string("....")
	vfd_set_icon(36,1)
	if config.plugins.VFD_spark.ledMode.value == 'True':
		vfd_set_led(0)

def standbyCounterChanged(configElement):
	print "[VFD-SPARK] In Standby"
	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)
	vfd_clear()
	if config.plugins.VFD_spark.ledMode.value == 'True':
		vfd_set_led(1)

def initVFD():
	print "[VFD-SPARK] initVFD"
	vfd_write_string("....")
	vfd_set_led(0)
#	vfd_set_time()

class VFD_SparkSetup(ConfigListScreen, Screen):
	def __init__(self, session, args = None):

		self.skin = """
			<screen position="100,100" size="500,210" title="VFD Spark Setup" >
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
		self.list.append(getConfigListEntry(_("VFD text"), config.plugins.VFD_spark.textMode))
		self.list.append(getConfigListEntry(_("VFD led in standby"), config.plugins.VFD_spark.ledMode))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.newConfig()

	def newConfig(self):
		print self["config"].getCurrent()[0]
		if self["config"].getCurrent()[0] == _('VFD text'):
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

class VFD_Spark:
	def __init__(self, session):
		print "[VFD-SPARK] initializing"
		self.session = session
		self.service = None
		self.onClose = [ ]
		self.Console = Console()
		initVFD()
#		eDVBLocalTimeHandler.getInstance().m_timeUpdated.get().append(vfd_set_time)
		global ChannelnumberInstance
		if ChannelnumberInstance is None:
			ChannelnumberInstance = Channelnumber(session)

	def shutdown(self):
		self.abort()

	def abort(self):
		print "[VFD-SPARK] aborting"
#		eDVBLocalTimeHandler.getInstance().m_timeUpdated.get().remove(vfd_set_time)

	config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call = False)

def main(menuid):
	if menuid != "system":
		return [ ]
	return [(_("VFD_Spark"), startVFD, "VFD_Spark", None)]

def startVFD(session, **kwargs):
	session.open(VFD_SparkSetup)

sparkVfd = None
gReason = -1
mySession = None

def controlsparkVfd():
	global sparkVfd
	global gReason
	global mySession

	if gReason == 0 and mySession != None and sparkVfd == None:
		print "[VFD-SPARK] Starting !!"
		sparkVfd = VFD_Spark(mySession)
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

def Plugins(**kwargs):
 	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
 		PluginDescriptor(name="VFD Spark", description="Change VFD display settings",where = PluginDescriptor.WHERE_MENU, fnc = main) ]


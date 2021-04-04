#!/usr/bin/python
#
# bitmap of each segment:
#        0x1
#       -----
# 0x20 |     | 0x2
#  0x40 -----
# 0x10 |     | 0x4
#       -----
#        0x8
# Note: 
#  extra segment is provided only in second digit. use 0x80 bit to turn on ':' sign.
#
# usage of led7ctrl:
#
#   command string should be feed into standard input.
#   accept multi-line command.
#   EOF will make program terminate.
#
#  command syntax:  "iX ..."
#    i is position specifier. 'a', 'b', 'c', 'd' can be used to specify each position. (from left side)
#    X is segment bitmap, expressed as hex form without "0x" prefix.
#    X can be one-byte string or two-byte string.
#
#  typical command form:  "aAA bBB cCC dDD"
#    AA is segment bitmap of first digit, expressed as hex form without "0x" prefix.
#    BB is segment bitmap of second digit, expressed as hex form without "0x" prefix.
#    CC is segment bitmap of third digit, expressed as hex form without "0x" prefix.
#    DD is segment bitmap of fourth digit, expressed as hex form without "0x" prefix.
#
#   AA, BB, CC, DD can be composed of one digit if the value is less than 0x10.
#      ex: a06 and a6 is both allowed.
#
from __future__ import print_function
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

from boxbranding import getBoxType

import Screens.Standby
import subprocess

config.plugins.VFD_SF8 = ConfigSubsection()
config.plugins.VFD_SF8.showClock = ConfigSelection(default="True_Switch", choices=[("False", _("Channelnumber in Standby off")), ("True", _("Channelnumber in Standby Clock")), ("True_Switch", _("Channelnumber/Clock in Standby Clock")), ("True_All", _("Clock always")), ("Off", _("Always off"))])
config.plugins.VFD_SF8.timeMode = ConfigSelection(default="24h", choices=[("12h"), ("24h")])

# this bitmap is not complete. 
# please populate it as you want.
ascii_bitmap = [
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # 0 ~ 7
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # 8 ~ f
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # 10 ~ 17
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # 18 ~ 1f
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # SPC ! " # $ % & ' 
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # ( ) * + - . /
	0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, # 0 1 2 3 4 5 6 7
	0x7f, 0x6f, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # 8 9 : ; < = > ?
	0x0, 0x77, 0x7c, 0x58, 0x5e, 0x79, 0x71, 0x0, # @ A B C D E F G
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # H I J K L M N O
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # P Q R S T U V W
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # X Y Z [ \ ] ^ _
	0x0, 0x77, 0x7c, 0x58, 0x5e, 0x79, 0x71, 0x0, # ` a b c d e f g
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # h i j k l m n o
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # p q r s t u v w
	0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, # x y z { | } ~ 
]


def vfd_write(text):
	open("/dev/dbox/oled0", "w").write(text)
	

def vfd_text_out(text):
	led7ctrl = subprocess.Popen(['/usr/lib/enigma2/python/Plugins/SystemPlugins/VFDControl/led7ctrl'], stdin=subprocess.PIPE)
	index = ['a', 'b', 'c', 'd'] # 'a' means the first digit, 'b' is second, ...
	cmd = ""
	for i in range(4): # display up to 4 character. todo: check short string.
		ascii_val = ord(text[i])
		# todo: we only has 128 byte length list. check ascii val.
		cmd += (index[i] + hex(ascii_bitmap[ascii_val])[2:]) # should not use 0x prefix in command.
		cmd += " "  # use space as seperator
	led7ctrl.communicate(cmd + "\n")


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
		if config.plugins.VFD_SF8.showClock.value == 'Off' or config.plugins.VFD_SF8.showClock.value == 'True_All':
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
			vfd_text_out(chnr)
		else:
			Channelnr = "%04d" % (int(chnr))
			vfd_text_out(Channelnr)

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
		if config.plugins.VFD_SF8.showClock.value == 'True' or config.plugins.VFD_SF8.showClock.value == 'True_All' or config.plugins.VFD_SF8.showClock.value == 'True_Switch':
			clock = str(localtime()[3])
			clock1 = str(localtime()[4])
			if config.plugins.VFD_SF8.timeMode.value != '24h':
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
			vfd_text_out("....")

	def vrime(self):
		if (config.plugins.VFD_SF8.showClock.value == 'True' or config.plugins.VFD_SF8.showClock.value == 'False' or config.plugins.VFD_SF8.showClock.value == 'True_Switch') and not Screens.Standby.inStandby:
			if config.plugins.VFD_SF8.showClock.value == 'True_Switch':
				if time() >= self.begin:
					self.endkeypress = False
				if self.endkeypress:
					self.__eventInfoChanged()
				else:
					self.prikaz()
			else:
				self.__eventInfoChanged()
					
		if config.plugins.VFD_SF8.showClock.value == 'Off':
			vfd_text_out("....")
			self.zaPrik.start(self.updatetime, 1)
			return
		else:
			self.zaPrik.start(1000, 1)

		if Screens.Standby.inStandby or config.plugins.VFD_SF8.showClock.value == 'True_All':
			self.prikaz()

	def keyPressed(self, key, tag):
		self.begin = time() + int(self.channelnrdelay)
		self.endkeypress = True


ChannelnumberInstance = None


def leaveStandby():
	print("[VFD-SF8] Leave Standby")

	if config.plugins.VFD_SF8.showClock.value == 'Off':
		vfd_text_out("....")


def standbyCounterChanged(configElement):
	print("[VFD-SF8] In Standby")

	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)

	if config.plugins.VFD_SF8.showClock.value == 'Off':
		vfd_text_out("....")


def initVFD():
	print("[VFD-SF8] initVFD")

	if config.plugins.VFD_SF8.showClock.value == 'Off':
		vfd_text_out("....")


class VFD_SF8Setup(ConfigListScreen, Screen):
	def __init__(self, session, args=None):

		self.skin = """
			<screen position="100,100" size="500,210" title="VFD_SF8 Setup" >
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
		self.list.append(getConfigListEntry(_("Show on VFD"), config.plugins.VFD_SF8.showClock))
		if config.plugins.VFD_SF8.showClock.value != "Off":
			self.list.append(getConfigListEntry(_("Time mode"), config.plugins.VFD_SF8.timeMode))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.newConfig()

	def newConfig(self):
		print(self["config"].getCurrent()[0])
		if self["config"].getCurrent()[0] == _('Show on VFD'):
			self.createSetup()

	def abort(self):
		print("aborting")

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


class VFD_SF8:
	def __init__(self, session):
		print("[VFD-SF8] initializing")
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
		print("[VFD-SF8] aborting")
		config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call=False)


def main(menuid):
	if menuid != "system":
		return []
	return [(_("VFD_SF8"), startVFD, "VFD_SF8", None)]


def startVFD(session, **kwargs):
	session.open(VFD_SF8Setup)


SF8VFD = None
gReason = -1
mySession = None


def controlSF8VFD():
	global SF8VFD
	global gReason
	global mySession

	if gReason == 0 and mySession != None and SF8VFD == None:
		print("[VFD-SF8] Starting !!")
		SF8VFD = VFD_SF8(mySession)
	elif gReason == 1 and SF8VFD != None:
		print("[VFD-SF8] Stopping !!")

		SF8VFD = None


def sessionstart(reason, **kwargs):
	print("[VFD-SF8] sessionstart")
	global SF8VFD
	global gReason
	global mySession

	if "session" in kwargs:
		mySession = kwargs["session"]
	else:
		gReason = reason
	controlSF8VFD()


def Plugins(**kwargs):
	if getBoxType() in ('sf8'):
	 	return [PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
	 		PluginDescriptor(name="LED Display Setup", description="Change LED display settings", where=PluginDescriptor.WHERE_MENU, fnc=main)]
	else:
		return []

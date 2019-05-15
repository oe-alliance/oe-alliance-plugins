# for localized messages
from . import _

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.NimManager import nimmanager
from Components.config import config, configfile, ConfigSubsection, ConfigSelection, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox
from Screens.ServiceScan import ServiceScan

from Tools.BoundFunction import boundFunction

from enigma import eComponentScan

from MisPlsLcnScan import MisPlsLcnScan
from providers import PROVIDERS

config.plugins.MisPlsLcnScan = ConfigSubsection()
config.plugins.MisPlsLcnScan.provider = ConfigSelection(default = "fransat_5W", choices = [(x, PROVIDERS[x]["name"]) for x in sorted(PROVIDERS.keys())])
config.plugins.MisPlsLcnScan.clearallservices = ConfigYesNo(default = False)
config.plugins.MisPlsLcnScan.onlyfree = ConfigYesNo(default = True)

class MisPlsLcnScanScreen(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _('MIS/PLS LCN Scan')
		Screen.setTitle(self, self.setup_title)
		self.skinName = ["MisPlsLcnScanScreen", "Setup"]
		self.onChangedEntry = []
		self.session = session
		ConfigListScreen.__init__(self, [], session = session, on_change = self.changedEntry)

		self["actions2"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"menu": self.keyCancel,
			"cancel": self.keyCancel,
			"save": self.keyGo,
		}, -2)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Scan"))

		self["description"] = Label("")

		self.transponders = []
		self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceOrGroup()

		self.createSetup()

		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def createSetup(self):
		setup_list = [
			getConfigListEntry(_("Provider"), config.plugins.MisPlsLcnScan.provider,_('Select the provider you wish to scan.')),
			getConfigListEntry(_("Clear before scan"), config.plugins.MisPlsLcnScan.clearallservices,_('If you select "yes" stored channels at the same orbital position will be deleted before starting the current search. Note: if you are scanning more than one provider this must be set to "no".')),
			getConfigListEntry(_("Only free scan"), config.plugins.MisPlsLcnScan.onlyfree,_('If you select "yes" the scan will only save channels that are not encrypted; "no" will find encrypted and non-encrypted channels.')),
		]

		self["config"].list = setup_list
		self["config"].l.setList(setup_list)

	def selectionChanged(self):
		self["description"].setText(self["config"].getCurrent()[2])

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	def keyGo(self):
		config.plugins.MisPlsLcnScan.save()
		configfile.save()
		self.startScan()

	def startScan(self):
		self.session.openWithCallback(self.MisPlsLcnScanCallback, MisPlsLcnScan, {})

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelCallback, MessageBox, _("Really close without saving settings?"))
		else:
			self.cancelCallback(True)

#	def keyLeft(self):
#		ConfigListScreen.keyLeft(self)
#		self.newConfig()
#
#	def keyRight(self):
#		ConfigListScreen.keyRight(self)
#		self.newConfig()
#
#	def newConfig(self):
#		cur = self["config"].getCurrent()
#		if len(cur)>1:
#			if cur[1] == config.plugins.MisPlsLcnScan.networkid_bool:
#				self.createSetup()

	def cancelCallback(self, answer):
		if answer:
			for x in self["config"].list:
				x[1].cancel()
			self.close(False)

	def MisPlsLcnScanCallback(self, answer=None):
		print "answer", answer
		if answer:
			self.feid = answer[0]
			self.transponders = answer[1]
			self.doServiceSearch()
		else:
			self.session.nav.playService(self.session.postScanService)

	def doServiceSearch(self):
		self.startServiceSearch(self.transponders, self.feid)

	def startServiceSearch(self, tlist, feid):
		flags = 0
		if config.plugins.MisPlsLcnScan.clearallservices.value:
			flags |= eComponentScan.scanRemoveServices
		else:
			flags |= eComponentScan.scanDontRemoveUnscanned
		if config.plugins.MisPlsLcnScan.onlyfree.value:
			flags |= eComponentScan.scanOnlyFree
		networkid = 0
		self.session.openWithCallback(self.startServiceSearchCallback, ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags, "networkid": networkid}])

	def startServiceSearchCallback(self, answer=None):
		self.session.nav.playService(self.session.postScanService)
		if answer:
			self.close(True)


def hasMultistream():
	return [nim for nim in nimmanager.nim_slots if nim.isCompatible("DVB-S") and nim.isMultistream()]

def MisPlsLcnScanStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("MIS/PLS LCN Scan"), MisPlsLcnScanMain, "MisPlsLcnScanScreen", 75, True)]
	return []

def MisPlsLcnScanMain(session, close=None, **kwargs):
	session.openWithCallback(boundFunction(MisPlsLcnScanCallback, close), MisPlsLcnScanScreen)

def MisPlsLcnScanCallback(close, answer):
	if close and answer:
		close(True)

def Plugins(**kwargs):
	pList = []
	if hasMultistream():
		pList.append( PluginDescriptor(name=_("MIS/PLS LCN Scan"), description="For scanning multiple input stream tv", where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=MisPlsLcnScanStart) )
	else:
		print "[MisPlsLcnScan] No MIS/PLS capable tuner available so don't load"
	return pList
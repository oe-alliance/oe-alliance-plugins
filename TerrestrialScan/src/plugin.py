# for localized messages
from . import _

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.NimManager import nimmanager
from Components.config import config, configfile, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigInteger, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox
from Screens.ServiceScan import ServiceScan

from enigma import eComponentScan

from TerrestrialScan import TerrestrialScan, setParams

config.plugins.TerrestrialScan = ConfigSubsection()
config.plugins.TerrestrialScan.networkid = ConfigInteger(default = 0, limits = (0, 65535))
config.plugins.TerrestrialScan.clearallservices = ConfigYesNo(default = True)
config.plugins.TerrestrialScan.onlyfree = ConfigYesNo(default = True)
config.plugins.TerrestrialScan.uhf_vhf = ConfigSelection(default = 'uhf', choices = [
			('uhf', _("UHF Europe")),
			('uhf_vhf', _("UHF/VHF Europe"))])

class TerrestrialScanScreen(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _('Terrestrial Scan')
		Screen.setTitle(self, self.setup_title)
		self.skinName = ["TerrestrialScanScreen", "Setup"]
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

		self.transponders_unique = {}
		self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceOrGroup()

		dvbt_capable_nims = []
		for nim in nimmanager.nim_slots:
			if nim.config_mode != "nothing":
				if nim.isCompatible("DVB-T") or (nim.isCompatible("DVB-S") and nim.canBeCompatible("DVB-T")):
					dvbt_capable_nims.append(nim.slot)
		
		nim_list = []
		nim_list.append((-1, _("Automatic")))
		for x in dvbt_capable_nims:
			nim_list.append((nimmanager.nim_slots[x].slot, nimmanager.nim_slots[x].friendly_full_description))
		self.scan_nims = ConfigSelection(choices = nim_list)

		self.createSetup()

		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def createSetup(self):
		setup_list = [
			getConfigListEntry(_("Tuner"), self.scan_nims,_('Select a tuner that is configured for terrestrial scans. "Automatic" will pick the highest spec available tuner.')),
			getConfigListEntry(_("Band"), config.plugins.TerrestrialScan.uhf_vhf,_('Most transmitters in European countries only have TV channels in the UHF band.')),
			getConfigListEntry(_('Network ID'), config.plugins.TerrestrialScan.networkid,_('Select "0" to search all networks, or enter the network ID of the provider you wish to search.')),
			getConfigListEntry(_("Clear before scan"), config.plugins.TerrestrialScan.clearallservices,_('If you select "yes" all stored terrestrial channels will be deleted before starting the current search.')),
			getConfigListEntry(_("Only free scan"), config.plugins.TerrestrialScan.onlyfree,_('If you select "yes" the scan will only save channels that are not encrypted; "no" will find encrypted and non-encrypted channels.'))
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
		config.plugins.TerrestrialScan.save()
		configfile.save()
		self.startScan()

	def startScan(self):
		self.session.openWithCallback(self.terrestrialScanCallback, TerrestrialScan, {"feid": int(self.scan_nims.value), "uhf_vhf": config.plugins.TerrestrialScan.uhf_vhf.value, "networkid": int(config.plugins.TerrestrialScan.networkid.value)})

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelCallback, MessageBox, _("Really close without saving settings?"))
		else:
			self.cancelCallback(True)

	def cancelCallback(self, answer):
		if answer:
			for x in self["config"].list:
				x[1].cancel()
			self.close(False)

	def terrestrialScanCallback(self, answer=None):
		print "answer", answer
		if answer:
			self.feid = answer[0]
			self.transponders_unique = answer[1]
			self.doServiceSearch()
		else:
			self.session.nav.playService(self.session.postScanService)

	def doServiceSearch(self):
		tlist = []
		for transponder in self.transponders_unique:
			tlist.append(setParams(self.transponders_unique[transponder]["frequency"], self.transponders_unique[transponder]["system"], self.transponders_unique[transponder]["bandwidth"]))
		self.startServiceSearch(tlist, self.feid)

	def startServiceSearch(self, tlist, feid):
		flags = 0
		if config.plugins.TerrestrialScan.clearallservices.value:
			flags |= eComponentScan.scanRemoveServices
		else:
			flags |= eComponentScan.scanDontRemoveUnscanned
		if config.plugins.TerrestrialScan.onlyfree.value:
			flags |= eComponentScan.scanOnlyFree
		networkid = 0
		self.session.openWithCallback(self.startServiceSearchCallback, ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags, "networkid": networkid}])

	def startServiceSearchCallback(self, answer=None):
		self.session.nav.playService(self.session.postScanService)
		if answer:
			self.close(True)

def TerrestrialScanStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Terrestrial Scan"), TerrestrialScanMain, "TerrestrialScanScreen", 75)]
	return []

def TerrestrialScanMain(session, **kwargs):
	session.open(TerrestrialScanScreen)

def Plugins(**kwargs):
	pList = []
	if nimmanager.hasNimType("DVB-T"):
		pList.append( PluginDescriptor(name=_("Terrestrial Scan"), description="For scanning terrestrial tv", where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=TerrestrialScanStart) )
	return pList
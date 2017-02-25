# for localized messages
from . import _, PluginLanguageDomain

from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, configfile, ConfigSubsection, ConfigIP, ConfigText, ConfigInteger, ConfigYesNo
from Screens.Setup import Setup
from ChannelsImporter import ChannelsImporter

config.plugins.ChannelsImporter = ConfigSubsection()
config.plugins.ChannelsImporter.ip = ConfigIP(default = [0,0,0,0])
config.plugins.ChannelsImporter.username = ConfigText(default = "root", fixed_size = False)
config.plugins.ChannelsImporter.password = ConfigText(default = "", fixed_size = False)
config.plugins.ChannelsImporter.port = ConfigInteger(21, (0, 65535))
config.plugins.ChannelsImporter.passive = ConfigYesNo(False)

class ChannelsImporterScreen(Setup):
	def __init__(self, session, setup, plugin=None, menu_path=None, PluginLanguageDomain=None):
		Setup.__init__(self, session, setup, plugin, menu_path, PluginLanguageDomain)
		self.skinName = ["ChannelsImporterScreen", "Setup"]

		self["actions2"] = ActionMap(["SetupActions","ColorActions"],
		{
			"ok": self.keyGo,
			"menu": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyGo,
		}, -2)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Import"))

	def keyGo(self):
		config.plugins.ChannelsImporter.save()
		configfile.save()
		self.startImporter()

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

	def startImporter(self):
		self.session.openWithCallback(self.startImporterCallback, ChannelsImporter)

	def startImporterCallback(self, answer = None):
		if answer:
			self.close()

def ChannelsImporterStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Channels importer"), ChannelsImporterMain, "ChannelsImporterScreen", 80)]
	return []

def ChannelsImporterMain(session, **kwargs):
	menu_path = _("Main menu")+' / '+_("Setup")+' / '+_('Service searching')
	session.open(ChannelsImporterScreen, 'channelsimporter', 'SystemPlugins/ChannelsImporter', menu_path, PluginLanguageDomain)

def Plugins(**kwargs):
	pList = []
	pList.append( PluginDescriptor(name=_("ChannelsImporter"), description="For importing bouquets from another receiver", where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=ChannelsImporterStart) )
	return pList

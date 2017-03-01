# for localized messages
from . import _, PluginLanguageDomain

from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, configfile, ConfigSubsection, ConfigIP, ConfigText, ConfigInteger, ConfigYesNo, ConfigSelection, ConfigClock
from Screens.Setup import Setup
from Components.SystemInfo import SystemInfo
from Screens.MessageBox import MessageBox # for are you sure questions after config changes

from ChannelsImporter import ChannelsImporter

from scheduler import autostart

config.plugins.ChannelsImporter = ConfigSubsection()
config.plugins.ChannelsImporter.ip = ConfigIP(default = [0,0,0,0])
config.plugins.ChannelsImporter.username = ConfigText(default = "root", fixed_size = False)
config.plugins.ChannelsImporter.password = ConfigText(default = "", fixed_size = False)
config.plugins.ChannelsImporter.port = ConfigInteger(21, (0, 65535))
config.plugins.ChannelsImporter.passive = ConfigYesNo(False)
config.plugins.ChannelsImporter.importOnRestart = ConfigYesNo(False)
config.plugins.ChannelsImporter.enableSchedule = ConfigYesNo(False)
config.plugins.ChannelsImporter.scheduleRepeatInterval = ConfigSelection(default = "daily", choices = [("60", _("Every hour")), ("120", _("Every 2 hours")), ("180", _("Every 3 hours")), ("360", _("Every 6 hours")), ("720", _("Every 12 hours")), ("daily", _("Daily"))])
config.plugins.ChannelsImporter.scheduletime = ConfigClock(default = 0) # 1:00
def scheduleRepeatIntervalChanged(configElement):
	print "config.plugins.ChannelsImporter.enableSchedule.value", config.plugins.ChannelsImporter.enableSchedule.value
	print "config.plugins.ChannelsImporter.scheduleRepeatInterval.value", config.plugins.ChannelsImporter.scheduleRepeatInterval.value
	if config.plugins.ChannelsImporter.enableSchedule.value and config.plugins.ChannelsImporter.scheduleRepeatInterval.value == "daily":
		SystemInfo["ChannelsImporterRepeatDaily"] = True
	else:
		SystemInfo["ChannelsImporterRepeatDaily"] = False
	print 'SystemInfo["ChannelsImporterRepeatDaily"]', SystemInfo["ChannelsImporterRepeatDaily"]
config.plugins.ChannelsImporter.enableSchedule.addNotifier(scheduleRepeatIntervalChanged, immediate_feedback = True, initial_call = True)
config.plugins.ChannelsImporter.scheduleRepeatInterval.addNotifier(scheduleRepeatIntervalChanged, immediate_feedback = True, initial_call = True)

class ChannelsImporterScreen(Setup):
	def __init__(self, session, setup, plugin=None, menu_path=None, PluginLanguageDomain=None):
		Setup.__init__(self, session, setup, plugin, menu_path, PluginLanguageDomain)
		self.skinName = ["ChannelsImporterScreen", "Setup"]

		self["actions2"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"menu": self.keyCancel,
			"cancel": self.keyCancel,
			"save": self.keyGo,
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
	pList.append( PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart))
	pList.append( PluginDescriptor(name=_("ChannelsImporter"), description="For importing bouquets from another receiver", where = PluginDescriptor.WHERE_MENU, fnc=ChannelsImporterStart, needsRestart=True) )
	return pList
# for localized messages
from . import _, PluginLanguageDomain

from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, configfile, ConfigSubsection, ConfigIP, ConfigText, ConfigInteger, ConfigYesNo, ConfigSelection, ConfigClock, NoSave, ConfigNumber
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
config.plugins.ChannelsImporter.importEPG = ConfigYesNo(False)
config.plugins.ChannelsImporter.retrycount = NoSave(ConfigNumber(default = 0))
config.plugins.ChannelsImporter.nextscheduletime = NoSave(ConfigNumber(default = 0))
config.plugins.ChannelsImporter.importOnRestart = ConfigYesNo(False)
config.plugins.ChannelsImporter.enableSchedule = ConfigYesNo(False)
config.plugins.ChannelsImporter.extensions = ConfigYesNo(default = False)
config.plugins.ChannelsImporter.setupFallback = ConfigYesNo(default = False)
config.plugins.ChannelsImporter.scheduleRepeatInterval = ConfigSelection(default = "daily", choices = [("2", _("Every 2 minutes (for testing)")), ("5", _("Every 5 minutes (for testing)")), ("60", _("Every hour")), ("120", _("Every 2 hours")), ("180", _("Every 3 hours")), ("360", _("Every 6 hours")), ("720", _("Every 12 hours")), ("daily", _("Daily"))])
config.plugins.ChannelsImporter.scheduletime = ConfigClock(default = 0) # 1:00
config.plugins.ChannelsImporter.errorMessages = ConfigYesNo(False)
def scheduleRepeatIntervalChanged(configElement):
	if config.plugins.ChannelsImporter.enableSchedule.value and config.plugins.ChannelsImporter.scheduleRepeatInterval.value == "daily":
		SystemInfo["ChannelsImporterRepeatDaily"] = True
	else:
		SystemInfo["ChannelsImporterRepeatDaily"] = False
config.plugins.ChannelsImporter.enableSchedule.addNotifier(scheduleRepeatIntervalChanged, immediate_feedback = True, initial_call = True)
config.plugins.ChannelsImporter.scheduleRepeatInterval.addNotifier(scheduleRepeatIntervalChanged, immediate_feedback = True, initial_call = True)

class ChannelsImporterScreen(Setup):
	skin = """
		<screen position="340,70" size="600,620">
			<widget source="key_red" render="Label" position="0,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#9f1313" font="Regular;18" transparent="1"/>
			<widget source="key_green" render="Label" position="150,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#1f771f" font="Regular;18" transparent="1"/>
			<widget source="key_yellow" render="Label" position="300,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#a08500" font="Regular;18" transparent="1"/>
			<widget name="HelpWindow" pixmap="buttons/vkey_icon.png" position="450,550" zPosition="1" size="541,720" transparent="1" alphatest="on"/>
			<ePixmap name="red" position="0,0" zPosition="2" size="140,40" pixmap="buttons/red.png" transparent="1" alphatest="on"/>
			<ePixmap name="green" position="150,0" zPosition="2" size="140,40" pixmap="buttons/green.png" transparent="1" alphatest="on"/>
			<ePixmap name="yellow" position="300,0" zPosition="2" size="140,40" pixmap="buttons/yellow.png" transparent="1" alphatest="on"/>
			<widget name="config" position="10,50" size="580,350" scrollbarMode="showOnDemand"/>
			<widget name="description" position="50,385" size="500,80" font="Regular;18" halign="center" valign="top" transparent="0" zPosition="1"/>
		</screen>"""

	def __init__(self, session, setup, plugin=None, menu_path=None, PluginLanguageDomain=None):
		try:
			Setup.__init__(self, session, setup, plugin, menu_path, PluginLanguageDomain)
		except TypeError:
			Setup.__init__(self, session, setup, plugin)

		self["actions2"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"menu": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.keyGo,
		}, -2)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Import"))

	def keySave(self):
		self.saveConfig()
		self.close()
	
	def keyGo(self):
		self.saveConfig()
		self.startImporter()

	def saveConfig(self):
		config.plugins.ChannelsImporter.save()
		if config.plugins.ChannelsImporter.setupFallback.value:
			config.usage.remote_fallback_enabled.value = True
			config.usage.remote_fallback_enabled.save()
			config.usage.remote_fallback.value = "http://%d.%d.%d.%d:8001" % (config.plugins.ChannelsImporter.ip.value[0], config.plugins.ChannelsImporter.ip.value[1], config.plugins.ChannelsImporter.ip.value[2], config.plugins.ChannelsImporter.ip.value[3])
			config.usage.remote_fallback.save()
		configfile.save()
	
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

def startimport(session, **kwargs):
	session.open(ChannelsImporter)

def ChannelsImporterStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Channels importer"), ChannelsImporterMain, "ChannelsImporterScreen", 80)]
	return []

def ChannelsImporterMain(session, **kwargs):
	menu_path = _("Main menu")+' / '+_("Setup")+' / '+_('Service searching')
	session.open(ChannelsImporterScreen, 'channelsimporter', 'SystemPlugins/ChannelsImporter', menu_path, PluginLanguageDomain)

def Plugins(**kwargs):
	pList = []
	if config.plugins.ChannelsImporter.extensions.getValue():
		pList.append(PluginDescriptor(name=_("Channels importer"), description=_("Fetch channels from the server."), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=startimport, needsRestart=True))
	pList.append( PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart))
	pList.append( PluginDescriptor(name=_("ChannelsImporter"), description=_("For importing bouquets from another receiver"), where = PluginDescriptor.WHERE_MENU, fnc=ChannelsImporterStart, needsRestart=True) )
	return pList

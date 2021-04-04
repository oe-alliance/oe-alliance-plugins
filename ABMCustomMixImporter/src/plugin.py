from __future__ import print_function
from __future__ import absolute_import
# for localized messages
from . import _, PluginLanguageDomain

# Python
from time import mktime, strftime, time, localtime
import os
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.error import URLError, HTTPError

# enigma
from enigma import eTimer

# Components
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigSelection, configfile
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.Button import Button

#screens
from Screens.MessageBox import MessageBox # for are you sure questions after config changes
from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.Standby import inStandby

# Tools
from Tools.Directories import pathExists, fileExists

#Plugins
from Plugins.Plugin import PluginDescriptor
from .mixes import Mixes

mixes = Mixes().read()
choices = sorted([(mixes[x]["key"], mixes[x]["name"]) for x in mixes], key=lambda listItem: listItem[1])

default_mix = "dsayers_vmuk_into_skyuk"
ABMpath = "/usr/lib/enigma2/python/Plugins/SystemPlugins/AutoBouquetsMaker/custom/"

config.plugins.abmImporter = ConfigSubsection()
config.plugins.abmImporter.mix = ConfigSelection(default=default_mix, choices=choices)
config.plugins.abmImporter.enableImporter = ConfigYesNo(default=False)
config.plugins.abmImporter.leadTime = ConfigSelection(default="5", choices=[("1", _("1 minute")), ("2", _("2 minutes")), ("3", _("3 minutes")), ("5", _("5 minutes")), ("10", _("10 minutes")), ("20", _("20 minutes")), ("30", _("30 minutes"))])

class ABMCustomMixImporterScreen(Setup):
	skin = """
		<screen position="340,70" size="600,620">
			<widget source="key_red" render="Label" position="0,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#9f1313" font="Regular;18" transparent="1"/>
			<widget source="key_green" render="Label" position="150,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#1f771f" font="Regular;18" transparent="1"/>
			<widget source="key_yellow" render="Label" position="300,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#a08500" font="Regular;18" transparent="1"/>
			<widget source="key_blue" render="Label" position="450,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#a08500" font="Regular;18" transparent="1"/>
			<widget name="HelpWindow" pixmap="skin_default/buttons/vkey_icon.png" position="450,550" zPosition="1" size="541,720" transparent="1" alphatest="on"/>
			<ePixmap name="red" position="0,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
			<ePixmap name="green" position="150,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
			<ePixmap name="yellow" position="300,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
			<ePixmap name="blue" position="450,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
			<widget name="config" position="10,50" size="580,350" scrollbarMode="showOnDemand"/>
			<widget name="description" position="50,385" size="500,80" font="Regular;18" halign="center" valign="top" transparent="0" zPosition="1"/>
		</screen>"""

	def __init__(self, session, setup, plugin=None, menu_path=None, PluginLanguageDomain=None):
		try:
			Setup.__init__(self, session, setup, plugin, menu_path, PluginLanguageDomain)
		except TypeError:
			Setup.__init__(self, session, setup, plugin)

		self.skinName = ["ABMCustomMixImporterScreen", "Setup4buttons"]

		self["actions2"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"menu": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.keyGo,
			"blue": self.keyDelete
		}, -2)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Save setup"))
		self["key_yellow"] = StaticText(_("Fetch file"))
		self["key_blue"] = StaticText()

		self.onLayoutFinish.append(self.updatebuttontext)

	def updatebuttontext(self):
		if fileExists(ABMpath + mixes[config.plugins.abmImporter.mix.value]["provider"] + "_CustomMix.xml", "w"):
			self["key_blue"].setText(_("Delete file"))
		else:
			self["key_blue"].setText("")

	def keyDelete(self):
		if fileExists(ABMpath + mixes[config.plugins.abmImporter.mix.value]["provider"] + "_CustomMix.xml", "w"):
			os.remove(ABMpath + mixes[config.plugins.abmImporter.mix.value]["provider"] + "_CustomMix.xml")
		self.updatebuttontext()

	def keySave(self):
		self.saveConfig()
		self.close()

	def keyGo(self):
		self.saveConfig()
		self.startImporter()

	def saveConfig(self):
		config.plugins.abmImporter.save()
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
		self.session.openWithCallback(self.startImporterCallback, ABMCustomMixImporter)

	def startImporterCallback(self, answer=None):
		if answer:
			self.close()

class ABMCustomMixImporter(Screen):
	skin = """
	<screen position="0,0" size="1280,35" backgroundColor="transpBlack" flags="wfNoBorder" >
		<widget name="action" position="5,3" size="435,25" font="Regular;22" backgroundColor="transpBlack" borderWidth="3" borderColor="black"/>
		<widget name="status" position="465,5" size="435,25" font="Regular;22" halign="center" backgroundColor="transpBlack" borderWidth="2" borderColor="black"/>
	</screen>"""

	def __init__(self, session):
		print("[ABMCustomMixImporter][__init__] Starting...")
		self.session = session
		Screen.__init__(self, session)
		self.skinName = ["AutoBouquetsMaker"]
		Screen.setTitle(self, _("ABM CustomMix"))
		self["action"] = Label(_("Starting importer..."))
		self["status"] = Label("")
		self["actions"] = ActionMap(["SetupActions"],
		{
			"cancel": self.keyCancel,
		}, -2)
		self.onFirstExecBegin.append(self.firstExec)

	def firstExec(self):
		if not inStandby:
			self["action"].setText(_('Fetching from github'))
			self["status"] = Label("1/1")
		CustomMix = self.fetchURL()
		if CustomMix:
			try:
				if not inStandby:
					self["action"].setText(_('Saving CustomMix file'))
					self["status"] = Label("")
				with open(ABMpath + mixes[config.plugins.abmImporter.mix.value]["provider"] + "_CustomMix.xml", "w") as f:
					f.write(CustomMix)
					f.close()
				if not inStandby:
					self["action"].setText(_('File fetched and saved OK'))
					self.donetimer = eTimer()
					self.donetimer.callback.append(self.success)
					self.donetimer.startLongTimer(3)
			except:
				self.showError("Saving the CustomMix file failed")
				print("[ABMCustomMixImporter]Saving file failed.")

	def fetchURL(self):
		try:
			req = Request(mixes[config.plugins.abmImporter.mix.value]["url"])
			response = urlopen(req)
			print('[ABMCustomMixImporter][fetchURL] Response: %d' % response.getcode())
			if int(response.getcode()) == 200:
				return response.read()
		except HTTPError as err:
			print('[ABMCustomMixImporter][fetchURL] ERROR:', err)
		except URLError as err:
			print('[ABMCustomMixImporter][fetchURL] ERROR:', err.reason[0])
		#except urllib2 as err:
		#	print('[ABMCustomMixImporter][fetchURL] ERROR:', err)
		except:
			import sys
			print('[ABMCustomMixImporter][fetchURL] undefined error', sys.exc_info()[0])
		self.showError("The CustomMix file could not be fetched")

	def showError(self, message):
		if not inStandby:
			mbox = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
			mbox.setTitle(_("Channels importer"))
		self.close()

	def success(self):
		self.close(True)

	def keyCancel(self):
		self.close()

class schedule:
	instance = None
	def __init__(self, session):
		print("[ABMCustomMixSchedule][__init__] Starting...")
		self.session = session
		self.justBootedOrConfigChanged = True
		self.enableImporter = config.plugins.abmImporter.enableImporter.value
		self.leadTime = config.plugins.abmImporter.leadTime.value
		self.mix = config.plugins.abmImporter.mix.value
		try:
			self.enableSchedule = config.autobouquetsmaker.schedule.value
			self.clock = [config.autobouquetsmaker.scheduletime.value[0], config.autobouquetsmaker.scheduletime.value[1]]
			self.repeattype = "daily" # config.autobouquetsmaker.repeattype.value
			print("[ABMCustomMixSchedule][__init__] ABM config available")
		except:
			self.enableSchedule = False
			self.clock = [0, 0]
			self.repeattype = "daily"
			print("[ABMCustomMixSchedule][__init__] ABM config was not available")
		self.fetchtimer = eTimer()
		self.fetchtimer.callback.append(self.doSchedule)
		if self.enableSchedule:
			self.fetchtimer.startLongTimer(0)
		self.configtimer = eTimer()
		self.configtimer.callback.append(self.configChecker)
		self.configtimer.startLongTimer(60)

		assert simpleSchedule.instance is None, "[ABMCustomMixImporter] class simpleSchedule is a singleton class and just one instance of this class is allowed!"
		schedule.instance = self

	def __onClose(self):
		schedule.instance = None

	def configChecker(self):
		if self.enableImporter != config.plugins.abmImporter.enableImporter.value or \
			self.leadTime != config.plugins.abmImporter.leadTime.value or \
			self.mix != config.plugins.abmImporter.mix.value or \
			self.enableSchedule != config.autobouquetsmaker.schedule.value or \
			self.clock[0] != config.autobouquetsmaker.scheduletime.value[0] or \
			self.clock[1] != config.autobouquetsmaker.scheduletime.value[1]		:
			print("[ABMCustomMixImporter][configChecker] config has changed")
			self.enableImporter = config.plugins.abmImporter.enableImporter.value
			self.leadTime = config.plugins.abmImporter.leadTime.value
			self.mix = config.plugins.abmImporter.mix.value
			self.enableSchedule = config.autobouquetsmaker.schedule.value
			self.clock[0] = config.autobouquetsmaker.scheduletime.value[0]
			self.clock[1] = config.autobouquetsmaker.scheduletime.value[1]
			justBootedOrConfigChanged = True
			self.doSchedule()
		self.configtimer.startLongTimer(60)

	def doSchedule(self):
		if self.fetchtimer.isActive():
			self.fetchtimer.stop()
		if self.enableSchedule and self.enableImporter:
			if not self.justBootedOrConfigChanged: # Do not do the task if this function was called due to a config change or reboot.
				taskToSchedule(self.session)
			self.startNextCycle()
		else:
			print("[ABMCustomMixImporter][doSchedule] Scheduler disabled.")
		self.justBootedOrConfigChanged = False

	def startNextCycle(self):
		now = int(time())
		if now < 1483228800: # STB clock not correctly set. Check back in 12 hours.
			return 60 * 60 * 12
		intervals = {"daily": 60 * 60 * 24, "weekly": 60 * 60 * 24 * 7, "monthly": 60 * 60 * 24 * 30}
		ltime = localtime(now)
		next = int(mktime((ltime.tm_year, ltime.tm_mon, ltime.tm_mday, self.clock[0], self.clock[1] - int(self.leadTime), 0, ltime.tm_wday, ltime.tm_yday, ltime.tm_isdst)))
		if next > 0:
			while (next-30) < now:
				next += intervals[self.repeattype]
			self.fetchtimer.startLongTimer(next - now)
		else:
			next = -1
		print("[ABMCustomMixImporter][startNextCycle] Time set to", strftime("%c", localtime(next)), strftime("(now=%c)", localtime(now)))


scheduleTimer = None
def pluginAutoStart(reason, session=None, **kwargs):
	"called with reason=1 to during /sbin/shutdown.sysvinit, with reason=0 at startup?"
	global scheduleTimer
	global _session
	now = int(time())
	if reason == 0:
		print("[ABMCustomMixImporter][pluginAutoStart] AutoStart Enabled")
		if session is not None:
			_session = session
			if scheduleTimer is None:
				scheduleTimer = schedule(session)
	else:
		print("[ABMCustomMixImporter][schedule] Stop")
		scheduleTimer.stop()

def ABMisLoaded():
	return pathExists(ABMpath)


def taskToSchedule(session, **kwargs):
	session.open(ABMCustomMixImporter)

def pluginManualStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("ABM CustomMix Importer"), ABMCustomMixImporterMain, "ABMCustomMixImporterScreen", 11)]
	return []

def ABMCustomMixImporterMain(session, **kwargs):
	menu_path = "%s / %s / %s" % (_('Main menu'), _('Setup'), _('Service searching'))
	session.open(ABMCustomMixImporterScreen, 'abmcustommiximporter', 'SystemPlugins/ABMCustomMixImporter', menu_path, PluginLanguageDomain)

def Plugins(**kwargs):
	pList = []
	if ABMisLoaded():
		pList.append(PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=pluginAutoStart))
		pList.append(PluginDescriptor(name=_("ABM CustomMix Importer"), description="Imports CustomMix files for ABM", where=PluginDescriptor.WHERE_MENU, fnc=pluginManualStart, needsRestart=True))
	return pList

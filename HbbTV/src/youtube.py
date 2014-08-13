from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText, getConfigListEntry

import vbcfg

from __init__ import _

config.plugins.youtubetv = ConfigSubsection()
config.plugins.youtubetv.showhelp = ConfigYesNo(default = False)
config.plugins.youtubetv.uri = ConfigText(default = "http://www.youtube.com/tv", visible_width = 50, fixed_size = False)

vbcfg.g_youtubetv_cfg = config.plugins.youtubetv

class YoutubeTVWindow(Screen, HelpableScreen):
	skin =  """
		<screen name="YoutubeTVWindow" position="center,center" size="550,160" title="Start YouTube TV" >
			<widget name="infomation" position="5,0" size="540,80" valign="center" halign="center" font="Regular;20" />
			<widget name="startdesc" position="10,80" size="395,40" valign="center" font="Regular;20" />
			<widget name="helpdesc" position="10,120" size="395,40" valign="center" font="Regular;20" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="400,80" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="400,120" size="140,40" alphatest="on" />
			<widget source="key_green" render="Label" position="400,80" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="400,120" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

        def __init__(self, session):
                Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "OkCancelActions","ColorActions", "EPGSelectActions",], {
			"cancel": self.keyCancel,
			"red"	: self.keyCancel,
			"green"	: self.keyGreen,
			"yellow": self.keyYellow,
		},-2)

		self["key_green"]  = StaticText(_("Start"))
		self["key_yellow"] = StaticText(_("Help"))

		self["infomation"] = Label()
		self["startdesc"]  = Label()
		self["helpdesc"]   = Label()

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Start YouTube TV'))
		self["infomation"].setText(_("YouTube TV is a new way to watch YouTube videos on Vu+"))
		self["startdesc" ].setText(_("* Start YouTube TV"))
		self["helpdesc"  ].setText(_("* RC Help"))

	def setHelpModeActions(self):
		self.helpList = []
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions", {
			"ok"    : (self.keyPass, _("Play ther selected the video")),
			"cancel": (self.keyPass, _("Exit the YouTube TV")),
		})
		self["EventViewActions"] = HelpableActionMap(self, "EventViewActions", {
			"pageUp"    : (self.keyPass, _("Move up")),
			"pageDown"  : (self.keyPass, _("Move down")),
			"prevEvent" : (self.keyPass, _("Move left")),
			"nextEvent" : (self.keyPass, _("Move right")),
		})
		self["EPGSelectActions"] = HelpableActionMap(self, "EPGSelectActions", {
			"info"        : (self.keyPass, _("Search a video")),
			"nextService" : (self.keyPass, _("Skip forward 10 sec")),
			"prevService" : (self.keyPass, _("Skip backward 10 sec")),
		})
		self["MediaPlayerActions"] = HelpableActionMap(self, "MediaPlayerActions", {
			"play"  : (self.keyPass, _("Play current video")),
			"pause" : (self.keyPass, _("Pause current video")),
			"stop"  : (self.keyPass, _("Stop current video")),
		})
		self["ColorActions"] = HelpableActionMap(self, "ColorActions", {
			"red"   : (self.keyPass, _("Back")),
		})
		self.showHelp()

	def keyPass(self):
		pass

	def keyCancel(self):
		config.plugins.youtubetv.showhelp.cancel()
		self.close(False)

	def keyGreen(self):
		config.plugins.youtubetv.showhelp.save()
		config.plugins.youtubetv.save()
		config.plugins.save()
		vbcfg.g_youtubetv_cfg = config.plugins.youtubetv
		self.close(True)

	def keyYellow(self):
		self.setHelpModeActions()

	def keyBlue(self):
		if config.plugins.youtubetv.showhelp.value == True :
			config.plugins.youtubetv.showhelp.setValue(False)
		else:	config.plugins.youtubetv.showhelp.setValue(True)

class YoutubeTVSettings(ConfigListScreen, Screen):
	skin=   """
		<screen position="center,center" size="600,140" title="YouTube TV Settings">
			<widget name="config" position="0,0" size="600,100" scrollbarMode="showOnDemand" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="310,100" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="150,100" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="310,100" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="150,100" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, session):
		self.session = session
		self.menulist = []

		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, self.menulist)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions",], {
			"ok"     : self.keyGreen,
			"green"  : self.keyGreen,
			"red"    : self.keyRed,
			"cancel" : self.keyRed,
		}, -2)
		self["key_red"]   = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))

		self.makeConfigList()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('YouTube TV Settings'))

	def keyGreen(self):
		config.plugins.youtubetv.showhelp.save()
		config.plugins.youtubetv.uri.save()
		config.plugins.youtubetv.save()
		config.plugins.save()

		vbcfg.g_youtubetv_cfg = config.plugins.youtubetv
		self.close()

	def keyRed(self):
		config.plugins.youtubetv.showhelp.cancel()
		config.plugins.youtubetv.uri.cancel()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def makeConfigList(self):
		self.menulist = []

		entryUri = getConfigListEntry(_("YouTube TV URL"), config.plugins.youtubetv.uri)
		entryShowHelp = getConfigListEntry(_("Do not show YouTube TV Starter again"), config.plugins.youtubetv.showhelp)
		self.menulist.append(entryUri)
		self.menulist.append(entryShowHelp)
		self["config"].list = self.menulist
		self["config"].l.setList(self.menulist)


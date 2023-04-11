
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText, getConfigListEntry, ConfigInteger, ConfigSelection
from enigma import eTimer
from . import cbcfg


class ChromiumOSSettings(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="600,220" title="ChromiumOS Settings">
			<widget name="config" position="0,0" size="600,180" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/buttons/red.png" position="310,180" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="150,180" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="310,180" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="150,180" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, session):
		self.session = session
		self.menulist = []
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, self.menulist)
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.keyGreen,
		 'green': self.keyGreen,
		 'red': self.keyRed,
		 'cancel': self.keyRed}, -2)
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Save'))
		self.makeConfigList()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('ChromiumOS Settings'))

	def keyGreen(self):
		config.plugins.browser.startup.save()
		config.plugins.browser.margin_x.save()
		config.plugins.browser.margin_y.save()
		config.plugins.browser.enable_ntpd.save()
		config.plugins.browser.ntpd_url.save()
		config.plugins.browser.rcu_type.save()
		config.plugins.browser.save()
		config.plugins.save()
		cbcfg.g_browser_cfg = config.plugins.browser
		self.close()

	def keyRed(self):
		config.plugins.browser.startup.cancel()
		config.plugins.browser.margin_x.cancel()
		config.plugins.browser.margin_y.cancel()
		config.plugins.browser.enable_ntpd.cancel()
		config.plugins.browser.ntpd_url.cancel()
		config.plugins.browser.rcu_type.cancel()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.makeConfigList()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.makeConfigList()

	def makeConfigList(self):
		self.menulist = []
		entryStartUp = getConfigListEntry(_('Start Up URL'), config.plugins.browser.startup)
		entryMarginX = getConfigListEntry(_('X-margin on GUI'), config.plugins.browser.margin_x)
		entryMarginY = getConfigListEntry(_('Y-margin on GUI'), config.plugins.browser.margin_y)
		entryEnableNtpd = getConfigListEntry(_('Enable Ntpd when start ChromiumOS'), config.plugins.browser.enable_ntpd)
		entryNtpdUri = getConfigListEntry(_('Ntpd URL'), config.plugins.browser.ntpd_url)
#		entryRcuType = getConfigListEntry(_("RCU language type"), config.plugins.browser.rcu_type)
		self.menulist.append(entryStartUp)
		self.menulist.append(entryMarginX)
		self.menulist.append(entryMarginY)
		self.menulist.append(entryEnableNtpd)
		if config.plugins.browser.enable_ntpd.value == True:
			self.menulist.append(entryNtpdUri)
#		self.menulist.append(entryRcuType)
		self['config'].list = self.menulist
		self['config'].l.setList(self.menulist)


class ChromiumOSHelpWindow(Screen, HelpableScreen):
	MODE_GLOBAL, MODE_KEYBOARD, MODE_MOUSE = (1, 2, 3)
	skin = """
		<screen name="ChromiumOSHelpWindow" position="center,center" size="600,40" title="ChromiumOS Help" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="450,0" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="450,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self['key_red'] = StaticText(_('Exit'))
		self['key_green'] = StaticText(_('Global'))
		self['key_yellow'] = StaticText(_('Mouse'))
		self['key_blue'] = StaticText(_('Keyboard'))
		self['actions'] = ActionMap(['DirectionActions', 'OkCancelActions', 'ColorActions'], {'ok': self.keyRed,
		 'cancel': self.keyRed,
		 'red': self.keyRed,
		 'green': self.keyGreen,
		 'yellow': self.keyYellow,
		 'blue': self.keyBlue}, -2)
		self.showHelpTimer = eTimer()
		self.showHelpTimer.callback.append(self.cbShowHelpTimerClosed)
		self.showHelpTimer.start(500)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Browser Help'))

	def cbShowHelpTimerClosed(self):
		self.showHelpTimer.stop()
		self.setHelpModeActions(self.MODE_GLOBAL)

	def setHelpModeActions(self, _mode=0):
		self.helpList = []
		if _mode == self.MODE_GLOBAL:
			self['OkCancelActions'] = HelpableActionMap(self, 'OkCancelActions', {'cancel': (self.keyPass, _('Exit the Browser.'))})
			self['ColorActions'] = HelpableActionMap(self, 'ColorActions', {'green': (self.keyPass, _('Enter Key')),
			 'blue': (self.keyPass, _('Backspace Key')),
			 'yellow': (self.keyPass, _('Open the virtual-keyboard on enigma2'))})
			self['EPGSelectActions'] = HelpableActionMap(self, 'EPGSelectActions', {'info': (self.keyPass, _('Switch to keyboard/mouse mode.'))})
		elif _mode == self.MODE_MOUSE:
			self['DirectionActions'] = HelpableActionMap(self, 'DirectionActions', {'up': (self.keyPass, _('It will move the mouse pointer up.')),
			 'down': (self.keyPass, _('It will move the mouse pointer down.')),
			 'left': (self.keyPass, _('It will move the mouse pointer left.')),
			 'right': (self.keyPass, _('It will move the mouse pointer right.'))})
			self['OkCancelActions'] = HelpableActionMap(self, 'OkCancelActions', {'ok': (self.keyPass, _('Left Mouse Button'))})
			self['EPGSelectActions'] = HelpableActionMap(self, 'EPGSelectActions', {'nextBouquet': (self.keyPass, _('Right Mouse Button')),
			 'prevService': (self.keyPass, _('Left Key')),
			 'nextService': (self.keyPass, _('Right Key'))})
			self['MenuActions'] = HelpableActionMap(self, 'MenuActions', {'menu': (self.keyPass, _('Page up key'))})
			self['InfobarActions'] = HelpableActionMap(self, 'InfobarActions', {'showTv': (self.keyPass, _('Page down key'))})
		elif _mode == self.MODE_KEYBOARD:
			self['DirectionActions'] = HelpableActionMap(self, 'DirectionActions', {'up': (self.keyPass, _('Up Key')),
			 'down': (self.keyPass, _('Down Key')),
			 'left': (self.keyPass, _('Left Key')),
			 'right': (self.keyPass, _('Right Key'))})
			self['OkCancelActions'] = HelpableActionMap(self, 'OkCancelActions', {'ok': (self.keyPass, _('Enter Key'))})
			self['EPGSelectActions'] = HelpableActionMap(self, 'EPGSelectActions', {'nextBouquet': (self.keyPass, _('PageUp Key')),
			 'prevBouquet': (self.keyPass, _('PageDown Key')),
			 'prevService': (self.keyPass, _('Go to previous page.')),
			 'nextService': (self.keyPass, _('Go to next page.'))})
		if _mode > 0:
			self.showHelp()

	def keyPass(self):
		pass

	def keyRed(self):
		self.close()

	def keyGreen(self):
		self.setHelpModeActions(self.MODE_GLOBAL)

	def keyYellow(self):
		self.setHelpModeActions(self.MODE_MOUSE)

	def keyBlue(self):
		self.setHelpModeActions(self.MODE_KEYBOARD)


class ChromiumOSWindow(ConfigListScreen, Screen):
	skin = """
		<screen name="ChromiumOSWindow" position="center,center" size="550,200" title="Start ChromiumOS" >
			<widget name="config" position="10,0" size="540,80" scrollbarMode="showOnDemand" />
			<widget name="startdesc" position="10,80" size="395,40" valign="center" font="Regular;20" />
			<widget name="settingdesc" position="10,120" size="395,40" valign="center" font="Regular;20" />
			<widget name="helpdesc" position="10,160" size="395,40" valign="center" font="Regular;20" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="400,80" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="400,120" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="400,160" size="140,40" alphatest="on" />
			<widget source="key_green" render="Label" position="400,80" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="400,120" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="400,160" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, session):
		self.session = session
		self.menulist = []
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, self.menulist)
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.keyGreen,
		 'cancel': self.keyCancel,
		 'red': self.keyCancel,
		 'green': self.keyGreen,
		 'blue': self.keyBlue,
		 'yellow': self.keyYellow}, -2)
		self['key_green'] = StaticText(_('Start'))
		self['key_blue'] = StaticText(_('Setting'))
		self['key_yellow'] = StaticText(_('Help'))
		self['startdesc'] = Label()
		self['settingdesc'] = Label()
		self['helpdesc'] = Label()
		self.makeConfigList()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Start ChromiumOS'))
		self['startdesc'].setText(_('* Start ChromiumOS'))
		self['settingdesc'].setText(_('* Setting ChromiumOS'))
		self['helpdesc'].setText(_('* RC Help'))

	def keyPass(self):
		pass

	def keyCancel(self):
		self.close(False)

	def keyGreen(self):
		self.close(True)

	def keyBlue(self):

		def _cb_setting_close():
			self.makeConfigList()

		self.session.openWithCallback(_cb_setting_close, ChromiumOSSettings)

	def keyYellow(self):
		self.session.open(ChromiumOSHelpWindow)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def makeConfigList(self):
		self.menulist = []
		entryURL = getConfigListEntry(_('Start URL'), config.plugins.browser.startup)
#		entryRcuType = getConfigListEntry(_("RCU Type"), config.plugins.browser.rcu_type)
		self.menulist.append(entryURL)
#		self.menulist.append(entryRcuType)
		self['config'].list = self.menulist
		self['config'].l.setList(self.menulist)

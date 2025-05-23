
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText, getConfigListEntry
from . import cbcfg


class YoutubeTVSettings(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="600,180" title="YouTube TV Settings">
			<widget name="config" position="0,0" size="600,140" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/buttons/red.png" position="310,140" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="150,140" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="310,140" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="150,140" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, session):
		self.session = session
		self.menulist = []
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, self.menulist)
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'],
		{
			'ok': self.keyGreen,
			'green': self.keyGreen,
			'red': self.keyRed,
			'cancel': self.keyRed
		}, -2)
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Save'))
		self.makeConfigList()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('YouTube TV Settings'))

	def keyGreen(self):
		config.plugins.browser.youtube_showhelp.save()
		config.plugins.browser.youtube_uri.save()
		config.plugins.browser.youtube_enable_ntpd.save()
		config.plugins.browser.youtube_ntpd_url.save()
		config.plugins.browser.youtube_mainmenu.save()
		config.plugins.browser.youtube_extmenu.save()
		config.plugins.browser.save()
		config.plugins.save()
		cbcfg.g_browser_cfg = config.plugins.browser
		self.close()

	def keyRed(self):
		config.plugins.browser.youtube_showhelp.cancel()
		config.plugins.browser.youtube_uri.cancel()
		config.plugins.browser.youtube_enable_ntpd.cancel()
		config.plugins.browser.youtube_ntpd_url.cancel()
		config.plugins.browser.youtube_mainmenu.cancel()
		config.plugins.browser.youtube_extmenu.cancel()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.makeConfigList()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.makeConfigList()

	def makeConfigList(self):
		self.menulist = []
#		entryUri = getConfigListEntry(_("YouTube TV URL"), config.plugins.browser.youtube_uri)
		entryShowHelp = getConfigListEntry(_('Do not show YouTube TV Starter again'), config.plugins.browser.youtube_showhelp)
		entryEnableNtpd = getConfigListEntry(_('Enable Ntpd when start YoutubeTV'), config.plugins.browser.youtube_enable_ntpd)
		entryNtpdUri = getConfigListEntry(_('Ntpd URL'), config.plugins.browser.youtube_ntpd_url)
		showInMainmenu = getConfigListEntry(_('Show in mainmenu'), config.plugins.browser.youtube_mainmenu)
		showInExtmenu = getConfigListEntry(_('Show in extensions'), config.plugins.browser.youtube_extmenu)
#		self.menulist.append(entryUri)
		self.menulist.append(entryShowHelp)
		self.menulist.append(entryEnableNtpd)
		if config.plugins.browser.youtube_enable_ntpd.value is True:
			self.menulist.append(entryNtpdUri)
		self.menulist.append(showInMainmenu)
		self.menulist.append(showInExtmenu)
		self['config'].list = self.menulist
		self['config'].l.setList(self.menulist)


class YoutubeTVWindow(Screen, HelpableScreen):
	skin = """
		<screen name="YoutubeTVWindow" position="center,center" size="550,200" title="Start YouTube TV" >
			<widget name="infomation" position="5,0" size="540,80" valign="center" halign="center" font="Regular;20" />
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
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self['actions'] = ActionMap(['WizardActions', 'DirectionActions', 'OkCancelActions', 'ColorActions', 'EPGSelectActions'],
		{
			'ok': self.keyGreen,
			'cancel': self.keyCancel,
			'red': self.keyCancel,
			'green': self.keyGreen,
			'yellow': self.keyYellow,
			'blue': self.keyBlue
		}, -2)
		self['key_green'] = StaticText(_('Start'))
		self['key_blue'] = StaticText(_('Setting'))
		self['key_yellow'] = StaticText(_('Help'))
		self['infomation'] = Label()
		self['startdesc'] = Label()
		self['settingdesc'] = Label()
		self['helpdesc'] = Label()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Start YouTube TV'))
		self['infomation'].setText(_('YouTube TV is a new way to watch YouTube videos on GigaBlue'))
		self['startdesc'].setText(_('* Start YouTube TV'))
		self['settingdesc'].setText(_('* Setting YouTube TV'))
		self['helpdesc'].setText(_('* RC Help'))

	def setHelpModeActions(self):
		self.helpList = []
		self['OkCancelActions'] = HelpableActionMap(self, 'OkCancelActions',
		{
			'ok': (self.keyPass, _('Play selected video')),
			'cancel': (self.keyPass, _('Exit YoutubeTV'))
		})
		self['ColorActions'] = HelpableActionMap(self, 'ColorActions',
		{
			'red': (self.keyPass, _('Back key'))
		})
		self['EventViewActions'] = HelpableActionMap(self, 'EventViewActions',
		{
			'pageUp': (self.keyPass, _('Move up')),
			'pageDown': (self.keyPass, _('Move down')),
			'prevEvent': (self.keyPass, _('Move left')),
			'nextEvent': (self.keyPass, _('Move right'))
		})
		self['EPGSelectActions'] = HelpableActionMap(self, 'EPGSelectActions',
		{
			'info': (self.keyPass, _('Search a video'))
		})
		self['InfobarSeekActions'] = HelpableActionMap(self, 'InfobarSeekActions',
		{
			'unPauseService': (self.keyPass, _('Play current video')),
			'playpauseService': (self.keyPass, _('Pause current video')),
			'seekFwd': (self.keyPass, _('Skip forward 10 sec')),
			'seekBack': (self.keyPass, _('Skip backward 10 sec'))
		})
		self.showHelp()

	def keyPass(self):
		pass

	def keyCancel(self):
		self.close(False)

	def keyGreen(self):
		self.close(True)

	def keyYellow(self):
		self.setHelpModeActions()

	def keyBlue(self):
		self.session.open(YoutubeTVSettings)

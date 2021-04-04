from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry

from enigma import getDesktop, ePoint

from .SCInfo import scthreads
from .stalkerclient import DEFAULT_URL, DEFAULT_MAC, SCThread, stalker


class StalkerClient_SetupScreen(Screen, ConfigListScreen):
	skin_default_1080p = """
	<screen name="stalkerclientsetup" position="center,center" size="900,470">
		<ePixmap pixmap="skin_default/buttons/red.png" position="48,20" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="268,20" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="493,20" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="718,20" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="48,20" zPosition="1" size="140,40" font="Regular;28" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_green" render="Label" position="268,20" zPosition="1" size="140,40" font="Regular;28" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_yellow" render="Label" position="493,20" zPosition="1" size="140,40" font="Regular;28" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_blue" render="Label" position="718,20" zPosition="1" size="140,40" font="Regular;28" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
		<widget name="config" zPosition="2" position="8,90" size="885,260" font="Regular;28" itemHeight="32" transparent="1" />
		<widget source="description" render="Label" position="8,350" size="885,90" font="Regular;27" halign="center" valign="center" />
		<widget name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" position="8,440" zPosition="10" size="35,25" transparent="1" alphatest="on" />
		<widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="310,445" zPosition="1" size="1,1" transparent="1" alphatest="on" />
	</screen>
	"""

	skin_default = """
	<screen name="stalkerclientsetup" position="center,center" size="600,360">
		<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="455,0" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_blue" render="Label" position="455,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
		<widget name="config" zPosition="2" position="5,70" size="590,200" transparent="1" />
		<widget source="description" render="Label" position="5,290" size="590,60" font="Regular;20" halign="center" valign="center" />
		<widget name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" position="5,330" zPosition="10" size="35,25" transparent="1" alphatest="on" />
		<widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="160,300" zPosition="1" size="1,1" transparent="1" alphatest="on" />
	</screen>
	"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.session = session
		dh = self.session.desktop.size().height()
		self.skin = StalkerClient_SetupScreen.skin_default_1080p if dh > 720 else StalkerClient_SetupScreen.skin_default

		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.onKeyOK,
			"cancel": self.onKeyCancel,
			"red": self.onKeyCancel,
			"green": self.onKeyOK,
			"yellow": self.onKeyYellow,
			"blue": self.onKeyBlue,
		}, -2)

		self["VirtualKB"] = ActionMap(["VirtualKeyboardActions"],
		{
			"showVirtualKeyboard": self.onKeyText,
		}, -1)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		self["key_yellow"] = StaticText(_("Default"))
		self["key_blue"] = StaticText(_("Login"))
		self["description"] = StaticText(_(""))

		self["VKeyIcon"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["VirtualKB"].setEnabled(False)

		self.backup = {
			"server": config.plugins.stalker_client.server.value,
			"mac": config.plugins.stalker_client.mac.value,
			"authEnabled": config.plugins.stalker_client.authEnabled.value,
		}
		if self.backup["authEnabled"] is "1":
			self.backup["username"] = config.plugins.stalker_client.username.value
			self.backup["password"] = config.plugins.stalker_client.password.value

		self.thread = SCThread('stalkerclientsetup')
		scthreads.pushThread(self.thread)

		self.createConfig()
		self.onLayoutFinish.append(self.onLayoutFinishCB)
		self.onClose.append(self.onCloseCB)

	def onLayoutFinishCB(self):
		self.setTitle(_("StalkerClient Setup"))
		self.createSetup()

		self["VKeyIcon"].hide()
		self["VirtualKB"].setEnabled(False)

		self.updateInfo()

	def onCloseCB(self):
		self.onClose.remove(self.onCloseCB)

		t = scthreads.popThread()
		if t:
			t.kill()
			t.join()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def onSelectionChangedCB(self):
		current = self["config"].getCurrent()
		if current == self.serverEntry:
			self.enableVKeyIcon()
			self.showKeypad()
		elif current == self.macEntry:
			self.enableVKeyIcon()
			self.showKeypad()
		elif current == self.authEnableEntry:
			self.disableVKeyIcon()
		elif current == self.usernameEntry:
			self.enableVKeyIcon()
			self.showKeypad()
		elif current == self.passwordEntry:
			self.enableVKeyIcon()
			self.showKeypad()

	def enableVKeyIcon(self):
		self["VKeyIcon"].show()
		self["VirtualKB"].setEnabled(True)

	def disableVKeyIcon(self):
		self["VKeyIcon"].hide()
		self["VirtualKB"].setEnabled(False)

	def showKeypad(self):
		screen_pos = self.instance.position()
		screen_size = self.instance.size()

		current = self["config"].getCurrent()
		if hasattr(current[1], 'help_window'):
			if current[1].help_window.instance is not None:
				help_window_size = current[1].help_window.instance.size()
				current[1].help_window.instance.show()
				current[1].help_window.instance.move(ePoint(screen_pos.x() + (screen_size.width() - help_window_size.width())/2, screen_pos.y() + screen_size.height() + 10))

	def hideKeypad(self):
		current = self["config"].getCurrent()
		if hasattr(current[1], 'help_window'):
			if current[1].help_window.instance is not None:
				current[1].help_window.instance.hide()

	def createConfig(self):
		self.serverEntry = getConfigListEntry(_("Stalker Server URL"), config.plugins.stalker_client.server)
		self.macEntry = getConfigListEntry(_("Stalker MAC"), config.plugins.stalker_client.mac)
		self.authEnableEntry = getConfigListEntry(_("Advanced option"), config.plugins.stalker_client.authEnabled)
		self.usernameEntry = getConfigListEntry(_("Stalker username"), config.plugins.stalker_client.username)
		self.passwordEntry = getConfigListEntry(_("Stalker password"), config.plugins.stalker_client.password)

		if not self.onSelectionChangedCB in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.onSelectionChangedCB)

	def createSetup(self):
		self.list = []
		self.list.append(self.serverEntry)
		self.list.append(self.macEntry)
		self.list.append(self.authEnableEntry)

		if config.plugins.stalker_client.authEnabled.value is "1":
			self.list.append(self.usernameEntry)
			self.list.append(self.passwordEntry)

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def newConfig(self):
		if self["config"].getCurrent() == self.authEnableEntry:
			self.createSetup()

	def updateInfo(self, data=None):
		if data is not None:
			self["description"].setText(data)
			return

		info = ""
		if not stalker.isAuthenticated():
			info += (_("offline"))
			info += "\n"
			info += stalker.getStatusMsg() is not None and stalker.getStatusMsg() or ""
		else:
			info += (_("online"))

		if stalker.isBlocked():
			info += "\n"
			info += stalker.getStatusMsg() is not None and stalker.getStatusMsg() or ""

		self["description"].setText(info)

	def Save(self):
		config.plugins.stalker_client.server.save()
		config.plugins.stalker_client.mac.save()
		config.plugins.stalker_client.authEnabled.save()
		if config.plugins.stalker_client.authEnabled.value is "1":
			config.plugins.stalker_client.username.save()
			config.plugins.stalker_client.password.save()
		config.plugins.stalker_client.save()
		config.plugins.save()
		config.save()

	def Restore(self):
		print("[StalkerClient] Restore previous settings.")
		config.plugins.stalker_client.server.value = self.backup["server"]
		config.plugins.stalker_client.mac.value = self.backup["mac"]
		config.plugins.stalker_client.authEnabled.value = self.backup["authEnabled"]
		if config.plugins.stalker_client.authEnabled.value is "1":
			config.plugins.stalker_client.username.value = self.backup["username"]
			config.plugins.stalker_client.password.value = self.backup["password"]

	def onKeyOK(self):
		self.Save()
		self.close()

	def onKeyCancel(self):
		self.Restore()
		self.close()

	def onKeyYellow(self):
		print("[StalkerClient] Setting default values.")
		config.plugins.stalker_client.server.value = DEFAULT_URL
		config.plugins.stalker_client.mac.value = DEFAULT_MAC
		config.plugins.stalker_client.authEnabled.value = 0
		config.plugins.stalker_client.username.value = ""
		config.plugins.stalker_client.password.value = ""
		self.createSetup()

	def onKeyBlue(self):
		if self.thread.hold:
			print("[StalkerClient] in progress...")
			return

		self.updateInfo("connecting")

		def onShowKeypadCB(unused):
			self.showKeypad()

		def authenticateCB(unused):
			if stalker.isBlocked():
				self.hideKeypad()
				message = stalker.getStatusMsg()
				self.session.openWithCallback(onShowKeypadCB, MessageBox, message, MessageBox.TYPE_INFO, timeout=5)
			self.updateInfo()
			self.thread.hold = False

		self.thread.addTask(authenticateCB, stalker.reload)
		self.thread.hold = True

	def onKeyText(self):
		self.hideKeypad()
		self.session.openWithCallback(self.cbKeyText, VirtualKeyBoard, title=self["config"].getCurrent()[0], text=self["config"].getCurrent()[1].getValue())

	def cbKeyText(self, data=None):
		if data is not None:
			self["config"].getCurrent()[1].setValue(data)
			self["config"].invalidate(self["config"].getCurrent())
		self.showKeypad()

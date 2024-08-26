from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText


class BluetoothSetupConfig(ConfigListScreen, Screen):
	skin = """
		<screen position="100,100" size="530,250">
			<ePixmap pixmap="skin_default/buttons/red.png" position="45,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="345,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="45,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="345,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="5,70" size="520,180" scrollbarMode="showOnDemand" transparent="1" />
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self["shortcuts"] = ActionMap(["BluetoothSetupActions"],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"vuRcuSetup": self.keyVuRcuSetup,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))

		self.skipVuRcuUpdateConfig = ConfigYesNo(default=True)
		self.skipVuRcuUpdateEntry = None
		self.createConfig()
		self.onLayoutFinish.append(self.onLayoutFinishCB)

	def onLayoutFinishCB(self):
		self.setTitle(_("Bluetooth Setup Options"))
		self.createSetup()

	def createConfig(self):
		self.btaudiodelay = getConfigListEntry(_("Set bluetooth audio delay (msec)"), config.plugins.bluetoothsetup.audiodelay)
		self.showMsgBoxEntry = getConfigListEntry(_("Show state message on infobar notification"), config.plugins.bluetoothsetup.showMessageBox)
		self.lastAudioConnEntry = getConfigListEntry(_("Try connect to last audio device on start enable"), config.plugins.bluetoothsetup.lastAudioConnEnable)
		self.showBatteryLowEntry = getConfigListEntry(_("Show battery low message on infobar notification"), config.plugins.bluetoothsetup.showBatteryLow)
		#self.voiceCheckDbEntry = getConfigListEntry(_("Voice Input Strength Value"), config.plugins.bluetoothsetup.voiceCheckDb)
		self.voiceCallbackName = getConfigListEntry(_("Voice event handler"), config.plugins.bluetoothsetup.voiceCallbackName)

		curSkipVer = config.plugins.bluetoothsetup.vurcuSkipFwVer.value
		if curSkipVer != 0:
			text = _("Skip firmware update of VUPLUS-BLE-RCU (version : %d)") % curSkipVer
			self.skipVuRcuUpdateEntry = getConfigListEntry(text, self.skipVuRcuUpdateConfig)

	def createSetup(self):
		self.list = []
		self.list.append(self.btaudiodelay)
		self.list.append(self.showMsgBoxEntry)
		self.list.append(self.lastAudioConnEntry)
		self.list.append(self.showBatteryLowEntry)
		#self.list.append( self.voiceCheckDbEntry )
		if self.skipVuRcuUpdateEntry:
			self.list.append(self.skipVuRcuUpdateEntry)
		self.list.append(self.voiceCallbackName)

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keySave(self):
		if not self.skipVuRcuUpdateConfig.value:
			config.plugins.bluetoothsetup.vurcuSkipFwVer.value = 0
			config.plugins.bluetoothsetup.vurcuSkipFwVer.save()

		self.saveAll()
		self.close()

	def keyVuRcuSetup(self):
		self.close("keyrcusetup")

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()

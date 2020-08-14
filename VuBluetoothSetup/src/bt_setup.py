from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Tools.Notifications import AddNotification
from Components.Label import Label
from Components.ActionMap import HelpableActionMap
from Components.config import config
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from enigma import eTimer
from .bt_types import getEventDesc, isAudioProfile, getIcon
from .bt import pybluetooth_instance
from .bt_config import BluetoothSetupConfig
from .bt_scan import BluetoothDiscoveryScreen, BluetoothRCUSetup
from .bt_task import BluetoothTask
from . import bt_types
from .OTAUpdate import VuRcuOtaUpdate

class BluetoothSetup(BluetoothTask):
	def __init__(self):
		BluetoothTask.__init__(self)
		self.vubt = pybluetooth_instance
		self.eventTimer = eTimer()
		self.eventTimer.callback.append(self.handleEvents)
		self.events = []

	def appendEventCallback(self, value = True):
		if value:
			if self.eventCallback not in self.vubt.pluginEventHandler:
				self.vubt.pluginEventHandler.append(self.eventCallback)
		else:
			if self.eventCallback in self.vubt.pluginEventHandler:
				self.vubt.pluginEventHandler.remove(self.eventCallback)

	def eventCallback(self, event, _data):
		print("[BluetoothSetup][eventCallback] event : %s" % (getEventDesc(event)))
		print("[BluetoothSetup][eventCallback] data : ", _data)

		data = None
		name = "noname"

		if _data:
			data = _data.copy()
			if "name" in data:
				name = data["name"]
			elif "bd_addr" in data:
				name = data["bd_addr"]

		self.events.append((event, name, data))

		if self.events:
			self.eventTimer.start(10, True)

	def handleEvents(self):
		(event, name, data) = self.events.pop(0)

		if event == bt_types.BT_EVENT_CONNECTED:
			self.updateDescription(_("%s is connected.") % name)
		elif event == bt_types.BT_EVENT_DISCONNECTED:
			self.updateDescription(_("%s is disconnected.") % name)
		elif event == bt_types.BT_EVENT_BT_CONNECTED:
			self.updateDescription(_("BT dongle has been inserted."))
		elif event == bt_types.BT_EVENT_BT_DISCONNECTED:
			self.updateDescription(_("BT dongle has been removed."))

		BluetoothTask.handleEvent(self, event, name, data)

		if event in (bt_types.BT_EVENT_CONNECTED, bt_types.BT_EVENT_CONNECT_TIMEOUT, bt_types.BT_EVENT_DISCONNECTED, bt_types.BT_EVENT_BT_CONNECTED, bt_types.BT_EVENT_BT_DISCONNECTED):
			self.eventHandled()

		if self.events:
			self.eventTimer.start(10, True)

	def connectDevice(self, args):
		(mac, profile, name) = args
		audio_connected = self.vubt.getAudioDeviceConnected()
		if isAudioProfile(profile) and bool(audio_connected):
			self.updateDescription(_("Connection failed.\nAnother audio device is connected. (%s)") % audio_connected['name'])
			return False

		res = self.vubt.requestConnect(mac)
		if res:
			self.clearKeyDesc()
			self.updateDescription(_("connecting %s") % name)

		else:
			self.updateDescription(_("connect to %s failed!!") % name)

		return res

	def disconnectDevice(self, args):
		(mac, profile, name) = args

		res = self.vubt.requestDisconnect(mac, profile)
		if res:
			self.clearKeyDesc()
			self.updateDescription(_("disconnecting %s") % name)
		else:
			self.updateDescription(_("disconnect to %s failed!!") % name)

		return res

	def removeDevice(self, args):
		(mac, profile, name) = args

		res = self.vubt.removePairing(mac, profile)
		if res:
			self.updateDescription()
			self.updateDeviceList()
		else:
			self.updateDescription(_("remove %s failed!!") % str(name))

		return res

	def addTaskConnect(self, mac, profile, name):
		args = (mac, profile, name)
		eventCB = {
			bt_types.BT_EVENT_CONNECTED : None,
			bt_types.BT_EVENT_CONNECT_TIMEOUT: self.onConnectTimeout}
		self.addTask(BluetoothTask.TASK_CONNECT, self.connectDevice, mac, args, eventCB)

	def addTaskDisconnect(self, mac, profile, name):
		args = (mac, profile, name)
		eventCB = {bt_types.BT_EVENT_LINK_DOWN : None}
		self.addTask(BluetoothTask.TASK_DISCONNECT, self.disconnectDevice, mac, args, eventCB)

	def addTaskRemove(self, mac, profile, name):
		args = (mac, profile, name)
		self.addTask(BluetoothTask.TASK_CALL_FUNC, self.removeDevice, None, args, None)

	def addTaskWaitDisconnect(self, mac, profile, name):
		args = (mac, profile, name)
		eventCB = {bt_types.BT_EVENT_LINK_DOWN : None}
		self.addTask(BluetoothTask.TASK_WAIT_DISCONNECT, None, mac, args, eventCB)

	def addTaskStartRcuSetupTimer(self):
		self.addTask(BluetoothTask.TASK_CALL_FUNC, self.startRCUSetupTimer, None, None, None)

	def onConnectTimeout(self, event, args):
		(mac, profile, name) = args

		text = _("Can't communicate with %s.") % name
		if name == bt_types.BT_VUPLUS_RCU_NAME:
			text += _("\nPlease repair Vu+ RCU. (by AUDIO+MENU)")

		self.updateDescription(text)

	def clearKeyDesc(self):
		pass

	def updateKeyDesc(self):
		pass

	def updateDescription(self, text = None):
		pass

	def updateDeviceList(self):
		pass

	def eventHandled(self):
		pass

class BluetoothSetupScreen(Screen, HelpableScreen, BluetoothSetup):
	skin = """
		<screen position="center,center" size="660,500">
			<ePixmap pixmap="skin_default/buttons/red.png" position="25,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="180,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="335,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="490,0" size="140,40" alphatest="on" />
			<widget name="key_red" position="25,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="180,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="335,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#a08500" transparent="1" />
			<widget name="key_blue" position="490,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#18188b" transparent="1" />
			<widget source="deviceList" render="Listbox" position="0,60" size="660,350" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
				{"template":
					[
						MultiContentEntryText(pos = (80, 0), size = (580, 40), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 0), # index 0 is Name
						MultiContentEntryText(pos = (80, 40), size = (180, 20), font=2, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1), # index 1 is type
						MultiContentEntryText(pos = (280, 40), size = (200, 20), font=2, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 2), # index 2 is status
						MultiContentEntryPixmapAlphaTest(pos = (10, 10), size = (50, 50), png = 3), # index 3 is bt_icon
					],
					"fonts": [gFont("Regular", 32), gFont("Regular", 28) ,gFont("Regular", 22), gFont("Regular", 16)],
					"itemHeight": 70
				}
				</convert>
			</widget>
			<widget source="description" render="Label" position="30,410" size="600,90" font="Regular;28" halign="center" valign="center" />
		</screen>
		"""
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		BluetoothSetup.__init__(self)
		self.session = session	

		self["key_red"] = Label(_("Enable"))
		self["key_green"] = Label(" ")
		self["key_yellow"] = Label(" ")
		self["key_blue"] = Label(_("Scan"))

		self["shortcuts"] = HelpableActionMap(self, "BluetoothSetupActions",
		{
			"ok": (self.keyOk, _("Connect/Disconnect selected device")),
			"cancel": (self.keyCancel, _("Exit bluetooth setup")),
			"red": (self.keyRed, _("Enable/Disable bluetooth")),
			"green": (self.keyGreen, _("Connect/Disconnect selected device")),
			"yellow": (self.keyYellow, _("Remove selected device")),
			"blue": (self.keyBlue, _("Start Scan / Setup VUPLUS BLE RCU")),
			"menu": (self.keyMenu, _("Setup bluetooth options")),
			"vuRcuSetup": self.keyVuRcuSetup,
		}, -2)

		self.deviceList = []
		self["deviceList"] = List(self.deviceList)

		self["description"] = StaticText(_("Starting..."))

		if not self.selectionChanged in self["deviceList"].onSelectionChanged:
			self["deviceList"].onSelectionChanged.append(self.selectionChanged)

		self.onLayoutFinish.append(self.onLayoutFinishCB)
		self.onClose.append(self.onCloseCB)

		self.enableTimer = eTimer()
		self.enableTimer.callback.append(self.changeEnable)

		self.openRcuSetupTimer = eTimer()
		self.openRcuSetupTimer.callback.append(self.openBluetoothRCUSetup)

		self.rcuSetupTimer = eTimer()
		self.rcuSetupTimer.callback.append(self.keyVuRcuSetup)

	def onLayoutFinishCB(self):
		self.setTitle(_("Bluetooth Setup"))
		self.appendEventCallback(True)
		self.startUp()

	def onCloseCB(self):
		self.appendEventCallback(False)
		config.plugins.bluetoothsetup.enable.save()

	def startUp(self):
		self.updateAll()
		self.updateKeyDesc()

	def selectionChanged(self):
		self.updateKeyDesc()

	def isEnabled(self):
		return self.vubt.isEnabled()

	def updateDeviceList(self):
		curIdx = self["deviceList"].getIndex()
		self.showPairedList()
		if self["deviceList"].count() > curIdx:
			self["deviceList"].setIndex(curIdx)

	def clearDeviceList(self):
		self.deviceList = []
		self["deviceList"].setList(self.deviceList)

	def getCurrentDeviceMAC(self):
		mac = None

		cur = self["deviceList"].getCurrent()
		if cur:
			mac = cur[4]["bd_addr"] # mac

		return mac

	def getCurrentDeviceNAME(self):
		name = None

		cur = self["deviceList"].getCurrent()
		if cur:
			name = cur[4]["name"] # mac

		return name

	def getCurrIsConnected(self):
		connected = None

		cur = self["deviceList"].getCurrent()
		if cur:
			connected = cur[4]["isConnected"]

		return connected

	def getCurrIsAudio(self):
		is_audio = False

		cur = self["deviceList"].getCurrent()
		if cur:
			profile = cur[4]["profile"]
			is_audio = isAudioProfile(profile) # is audio

		return is_audio

	def getCurrentDevice(self):
		dev = None
		cur = self["deviceList"].getCurrent()
		if cur:
			dev = cur[4]
		return dev

	def showPairedList(self):
		self.deviceList = []

		if not self.isEnabled():
			self["deviceList"].setList(self.deviceList)
			return

		pairedDevices = self.vubt.getPairedDevice()
		if pairedDevices:
			device_keys = list(pairedDevices.keys())
			device_keys.sort()

			for k in device_keys:
				v = pairedDevices[k]
				bd_addr = v['bd_addr']

				# check duplicate info
				skip = False
				for x in self.deviceList:
					_bd_addr = x[4]['bd_addr']
					if _bd_addr == bd_addr:
						skip = True
						break

				if skip:
					continue

				name = v['name']
				if not name:
					name = "NONAME"

				profile = v["profile"]
				if name == bt_types.BT_VUPLUS_RCU_NAME:
					profile = bt_types.BT_PROFILE_VU_RC

				name += ' (' + bd_addr + ')'
				classOfDevice = "type : %s" % v['classOfDevice'].split(',')[1]
				_statue = v['isConnected'] and "Connected" or "Disconnected"
				status = "status : %s" % _statue

				icon = getIcon(profile)

				deviceEntry = ( name, classOfDevice, status, icon, v)
				self.deviceList.append(deviceEntry)

		print("[showPairedList] self.deviceList : ", self.deviceList)

		self["deviceList"].setList(self.deviceList)

	def changeEnable(self):
		if self.isEnabled():
			config.plugins.bluetoothsetup.enable.value = False
		else:
			config.plugins.bluetoothsetup.enable.value = True
		self.updateAll()
		self.updateKeyDesc()

	def enableBT(self):
		self.clearDeviceList()
		if self.isEnabled():
			self.updateDescription(_("Device is disabling..."))
		else:
			self.updateDescription(_("Device is enabling..."))

		self.clearKeyDesc()

		self.enableTimer.start(0, True)

	def keyOk(self):
		self.keyGreen()

	def keyMenu(self):
		self.openBluetoothConfig()

	def keyCancel(self):
		self.close()

	def keyRed(self):
		if not self.isIdle():
			return

		self.enableBT()

	def keyGreen(self):
		if not self.isIdle():
			return

		isConnected = self.getCurrIsConnected()
		if isConnected is None:
			return

		mac = None
		name = None
		profile = None
		cur_dev = self.getCurrentDevice()
		if cur_dev:
			mac = cur_dev['bd_addr']
			name = cur_dev['name']
			profile = cur_dev['profile']

		print("[keyGreen] mac : ", mac)
		print("[keyGreen] name : ", name)
		print("[keyGreen] profile : ", profile)
		print("[keyGreen] isConnected : ", isConnected)

		if mac is None:
			return

		if isConnected:
			self.addTaskDisconnect(mac, profile, name)
		else:
			audio_connected = self.vubt.getAudioDeviceConnected()
			if isAudioProfile(profile) and bool(audio_connected):
				self.addTaskDisconnect(audio_connected['bd_addr'], audio_connected['profile'], audio_connected['name'])
				self.addTaskConnect(mac, profile, name)

			else:
				self.addTaskConnect(mac, profile, name)

	def keyYellow(self):
		if not self.isIdle():
			return

		name = None
		mac = None
		profile = None
		cur_dev = self.getCurrentDevice()
		if cur_dev:
			mac = cur_dev['bd_addr']
			name = cur_dev['name']
			profile = cur_dev['profile']

		if mac:
			if cur_dev["isConnected"]:
				self.addTaskDisconnect(mac, profile, name)
				self.addTaskRemove(mac, profile, name)
			else:
				self.addTaskRemove(mac, profile, name)

	def keyBlue(self):
		if not self.isIdle():
			return

		if not self.isEnabled():
			return

		if self.isPairedVuRcu():
			self.openBTScan()
		else:
			self.selectScanType()

	def openBTScan(self):
		self.appendEventCallback(False)
		self.session.openWithCallback(self.BTScanCB, BluetoothDiscoveryScreen)

	def BTScanCB(self, msg = None):
		self.appendEventCallback()
		self.updateAll(msg)

	def clearKeyDesc(self):
		self["key_red"].setText("")
		self["key_green"].setText("")
		self["key_yellow"].setText("")
		self["key_blue"].setText("")

	def updateKeyDesc(self):
		if self.isEnabled():
			self["key_red"].setText(_("Disable"))
			if self.getCurrentDevice():
				if self.getCurrIsConnected():
					self["key_green"].setText(_("Disconnect"))
				else:
					self["key_green"].setText(_("Connect"))
				self["key_yellow"].setText(_("Remove"))
			else:
				self["key_green"].setText("")
				self["key_yellow"].setText("")

			self["key_blue"].setText(_("Scan"))

		else:
			self["key_red"].setText(_("Enable"))
			self["key_green"].setText("")
			self["key_yellow"].setText("")
			self["key_blue"].setText("")

	def updateDescription(self, text = None):
		if text is None:
			if self.isEnabled():
				text = _("Device is enabled.")
			else:
				text = _("Press red key to enable bluetooth.")

		self["description"].setText(text)

	def updateAll(self, text=None):
		self.updateDescription(text)
		self.updateDeviceList()

	def eventHandled(self):
		self.updateDeviceList()

	def disconnectHIDDevices(self):
		for d in self.deviceList:
			deviceInfo = d[4]
			if deviceInfo['profile'] in [bt_types.BT_PROFILE_HID_UNKNOWN, bt_types.BT_PROFILE_KEYBOARD, bt_types.BT_PROFILE_MOUSE]:
				if deviceInfo['isConnected']:
					self.addTaskDisconnect(deviceInfo['bd_addr'], deviceInfo['profile'], deviceInfo['name'])

	def keyVuRcuSetup(self):
		if not self.isEnabled():
			self.updateDescription(_("Please enable bluetooth \nbefore pairing the VUPLUS-BLE-RCU."))
			return

		if not self.isIdle():
			print("[keyVuRcuSetup] current state : %d, wait 500ms." % self.getState())
			self.rcuSetupTimer.start(500, True)
			return

		self.disconnectHIDDevices()

		(mac, name, profile, isConnected) = self.getVuRcuInfo()

		if mac:
			self.updateDescription(_("Removing VUPLUS-BLE-RCU..."))
			if isConnected:
				self.addTaskWaitDisconnect(mac, profile, name)
				self.addTaskRemove(mac, profile, name)
			else:
				self.addTaskRemove(mac, profile, name)

			self.addTaskStartRcuSetupTimer()

		else:
			self.openBluetoothRCUSetup()

	def startRCUSetupTimer(self, timeout=1000):
		self.openRcuSetupTimer.start(timeout, True)

	def openBluetoothRCUSetup(self, autoStart=True):
		self.appendEventCallback(False)
		self.session.openWithCallback(self.BluetoothRCUSetupCB, BluetoothRCUSetup, autoStart=autoStart)

	def BluetoothRCUSetupCB(self, msg = None):
		self.appendEventCallback()
		self.updateAll(msg)

	def isPairedVuRcu(self):
		(mac, name, profile, isConnected) = self.getVuRcuInfo()
		return bool(mac)

	def getVuRcuInfo(self):
		_mac = None
		_name = None
		_profile = None
		_isConnected = False
		for d in self.deviceList:
			if d[4] ['name'] == bt_types.BT_VUPLUS_RCU_NAME:
				_mac = d[4]['bd_addr']
				_name = d[4]['name']
				_profile = d[4]['profile']
				_isConnected = d[4]['isConnected']
				break

		return (_mac, _name, _profile, _isConnected)

	def selectScanType(self):
		scanChoice = (
			(_("Scan and setup Vu+ Bluetooth RCU"), "vurcusetup"),
			(_("Scan other bluetooth 3.0 device (A2DP, HID)"), "scan")
		)

		from Screens.ChoiceBox import ChoiceBox
		self.session.openWithCallback(self.selectScanTypeConfirmed, ChoiceBox, title=_("Please select scan mode."), list = scanChoice)

	def selectScanTypeConfirmed(self, answer):
		answer = answer and answer[1]

		if answer == "scan":
			self.openBTScan()
		elif answer == "vurcusetup":
			self.openBluetoothRCUSetup(False)

	def openBluetoothConfig(self):
		self.session.openWithCallback(self.openBluetoothConfigCB, BluetoothSetupConfig)

	def openBluetoothConfigCB(self, res=None):
		if res == "keyrcusetup":
			self.keyVuRcuSetup()

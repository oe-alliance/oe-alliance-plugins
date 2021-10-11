from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from enigma import eTimer
from .bt_types import getEventDesc, isAudioProfile, getIcon
from .bt import pybluetooth_instance
from .bt_config import BluetoothSetupConfig
from . import bt_types
from .bt_task import BluetoothTask


class BluetoothDiscovery(BluetoothTask):
	def __init__(self):
		BluetoothTask.__init__(self)
		self.deviceList = []

		global pybluetooth_instance
		self.vubt = pybluetooth_instance

		# clear scan list
		self.vubt.resetScan()

		self.scanTimer = eTimer()
		self.scanTimer.callback.append(self.scanTimerCB)

		self.scanningTimer = eTimer()
		self.scanningTimer.callback.append(self.showScanning)
		self.scanningShowValue = 1
		self.scanningShowMax = 5
		self.scanningInterval = 1000
		self.scanningText = _("Scanning bluetooth devices")

		self.pairedDevices = self.getPairedList()

		self.pairingArgs = {}
		self.disconnectArgs = {}

		self.scanAbortTimer = eTimer()
		self.scanAbortTimer.callback.append(self.addTaskAbortScan)

		#self.pairingTime = 15
		#self.pairingCancelTimer = eTimer()
		#self.pairingCancelTimer.callback.append(self.pairingCancelTimerCB)

		self.eventTimer = eTimer()
		self.eventTimer.callback.append(self.handleEvents)
		self.events = []

		self.appendEventCallback()

		self.descriptionList = {
			bt_types.BT_EVENT_PAIRING_SUCCESS: _("%s is connected."),
			bt_types.BT_EVENT_PAIRING_FAIL: _("%s Pairing fail"),
			bt_types.BT_EVENT_PAIRING_TIMEOUT: _("Can't communicate with %s"),
			bt_types.BT_EVENT_PAIRING_WRONG_PIN: _("Wrong pin number for %s. Please try again and check pin number."),
			bt_types.BT_EVENT_DISCONNECTED: _("%s is disconnected.")}

	def appendEventCallback(self, value=True):
		if value:
			if self.discEventCallback not in self.vubt.pluginEventHandler:
				self.vubt.pluginEventHandler.append(self.discEventCallback)
		else:
			if self.discEventCallback in self.vubt.pluginEventHandler:
				self.vubt.pluginEventHandler.remove(self.discEventCallback)

	def initialStart(self):
		# clear scan list
		self.vubt.resetScan()

		self.addTaskStartScan()

	def deInit(self):
		self.scanningTimer.stop()
		self.scanAbortTimer.stop()
		#self.pairingCancelTimer.stop()
		self.eventTimer.stop()

		self.appendEventCallback(False)

	def getPairedList(self):
		pairedDeviceBdaddr = []
		pairedDevices = self.vubt.getPairedDevice()
		if pairedDevices:
			for (k, v) in list(pairedDevices.items()):
				pairedDeviceBdaddr.append(v['bd_addr'])

		return pairedDeviceBdaddr

	def displayScanMsgStart(self):
		self.scanningShowValue = 1
		self.showScanning()
		self.scanningTimer.start(self.scanningInterval)

	def showScanning(self):
		text = self.scanningText
		for idx in range(self.scanningShowValue):
			text += '.'

		for idx in range(self.scanningShowMax - self.scanningShowValue + 1):
			text += ' '

		self.updateDescription(text)
		self.scanningShowValue = (self.scanningShowValue % self.scanningShowMax) + 1

	def discEventCallback(self, event, _data):
		print("[BluetoothDiscovery][discEventCallback] event : %s" % (getEventDesc(event)))
		print("[BluetoothDiscovery][discEventCallback] data : ", _data)

		data = None
		name = "noname"

		if _data:
			data = _data.copy()
			if "name" in _data:
				name = _data["name"]
			elif "bd_addr" in _data:
				name = _data["bd_addr"]

		self.events.append((event, name, data))

		if self.events:
			self.eventTimer.start(10, True)

	def handleEvents(self):
		(event, name, data) = self.events.pop(0)

		if event == bt_types.BT_EVENT_DEVICE_ADDED:
			self.onDeviceAdded(event, name, data)
		elif event == bt_types.BT_EVENT_PAIRING_PASSCODE_REQUIRED:
			self.updateDescription(_("Type %s on %s to connect, then press Enter or Return." % (data['passcode'], data['name'])))
		else:
			BluetoothTask.handleEvent(self, event, name, data)

		self.eventHandled()

		if self.events:
			self.eventTimer.start(10, True)

	def getDiscDevice(self):
		return self.vubt.getDiscDevice()

	def startScan(self):
		ret = self.vubt.startScan()
		if ret:
			self.scanAbortTimer.start(int(config.plugins.bluetoothsetup.scanTime.value) * 1000, True)
			self.displayScanMsgStart()
		else:
			text = _("Scan failed! try again.")
			self.doExit(text)

		return ret

	def abortScan(self):
		if self.isScanning():
			self.vubt.abortScan()

	def startPairing(self, args):
		(mac, profile, name) = args
		ret = False
		audio_connected = self.vubt.getAudioDeviceConnected()
		if isAudioProfile(profile) and bool(audio_connected):
			self.updateDescription(_("Pairing Failed.\nAnother audio device is connected. (%s)") % audio_connected['name'])

		elif self.vubt.requestPairing(mac):
			self.updateDescription(_("Pairing %s") % name)
			#self.pairingCancelTimer.start(self.pairingTime * 1000, True)
			ret = True
		else:
			self.updateDescription(_("Pairing %s failed!!") % name)

		return ret

	def disconnectDevice(self, args):
		(mac, profile, name) = args
		ret = False
		if self.vubt.requestDisconnect(mac, profile):
			self.updateDescription(_("Disconnecting %s") % name)
			ret = True
		else:
			self.updateDescription(_("Disconnect %s failed!!") % name)

		return ret

	def cancelPairing(self, args):
		(mac, profile, name) = args
		ret = False
		if self.isPairing():
			print("[BluetoothDiscovery] cancelPairing %s" % mac)
			ret = self.vubt.cancelPairing(mac)

		return ret

	def scanTimerCB(self):
		self.addTaskStartScan()

	def addTaskStartScan(self):
		if self.isTaskEmpty():
			eventCB = {bt_types.BT_EVENT_SCAN_END: self.onScanFinished}
			BluetoothTask.addTask(self, BluetoothTask.TASK_START_SCAN, self.startScan, None, None, eventCB)

	def addTaskAbortScan(self):
		BluetoothTask.removeTask(self, BluetoothTask.TASK_START_SCAN)
		if self.isScanning():
			self.abortScan()
			#bluetoothTask.addTask(self, BluetoothTask.TASK_CALL_FUNC, self.abortScan, None, None, None)

	def addTaskPairing(self, mac, profile, name):
		if self.findTask(BluetoothTask.TASK_EXIT) or self.findTask(BluetoothTask.TASK_START_PAIRING):
			return

		if self.isScanning():
			self.addTaskAbortScan()

		args = (mac, profile, name)
		eventCB = {bt_types.BT_EVENT_PAIRING_SUCCESS: self.onPairingSuccess,
					bt_types.BT_EVENT_PAIRING_FAIL: self.onPairingFailed,
					bt_types.BT_EVENT_PAIRING_TIMEOUT: self.onPairingFailed,
					bt_types.BT_EVENT_PAIRING_WRONG_PIN: self.onPairingFailed,
					bt_types.BT_EVENT_PAIRING_PASSCODE_REQUIRED: self.onPairingFailed}
		BluetoothTask.addTask(self, BluetoothTask.TASK_START_PAIRING, self.startPairing, mac, args, eventCB)

	def addTaskCancelPair(self, mac, profile, name):
		args = (mac, profile, name)
		BluetoothTask.removeTask(self, BluetoothTask.TASK_START_PAIRING)
		if self.isPairing():
			self.cancelPairing(args)
			#BluetoothTask.addTask(self, BluetoothTask.TASK_CALL_FUNC, self.cancelPairing, mac, args, None)

	def addTaskDisconnect(self, mac, profile, name):
		if self.findTask(BluetoothTask.TASK_EXIT) or self.findTask(BluetoothTask.TASK_START_PAIRING):
			return

		args = (mac, profile, name)
		eventCB = {bt_types.BT_EVENT_LINK_DOWN: self.onDisconnected}
		self.addTask(BluetoothTask.TASK_DISCONNECT, self.disconnectDevice, mac, args, eventCB)

	def addTaskExit(self):
		BluetoothTask.removeAll(self)
		if self.isScanning():
			self.addTaskAbortScan()

		self.addTask(BluetoothTask.TASK_EXIT, self.doExit(), None, None, None)

	def onScanFinished(self, event, args):
		# stop scanning message
		self.scanningTimer.stop()
		self.updateDeviceList()

		if config.plugins.bluetoothsetup.autoRestartScan.value:
			self.scanTimer.start(0, True)

		if BluetoothTask.isTaskEmpty(self):
			if self.deviceList:
				self.updateDescription(_("Press green key to connect device."))
			else:
				self.updateDescription(_("No nearby bluetooth devices were found."))

	def onPairingSuccess(self, event, args):
		if event in self.descriptionList:
			(mac, profile, name) = args
			self.doExit(self.descriptionList[event] % name)

	def onPairingFailed(self, event, args):
		if event in self.descriptionList:
			(mac, profile, name) = args
			self.updateDescription(self.descriptionList[event] % name)

	def onDisconnected(self, event, args):
		if event in self.descriptionList:
			(mac, profile, name) = args
			self.updateDescription(self.descriptionList[event] % name)

	def onDeviceAdded(self, event, name, data):
		self.updateDeviceList()

	def doExit(self, msg=None):
		pass

	def updateDeviceList(self):
		pass

	def updateDescription(self, text):
		pass

	def eventHandled(self):
		pass


class BluetoothDiscoveryScreen(Screen, BluetoothDiscovery):
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
			<!--<ePixmap pixmap="skin_default/div-h.png" position="0,48" size="660,2" alphatest="on" />-->
			<widget source="deviceList" render="Listbox" position="0,60" size="660,350" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
				{"template":
					[
						MultiContentEntryText(pos = (80, 0), size = (490, 70), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 0), # index 0 is Name
						MultiContentEntryPixmapAlphaTest(pos = (10, 10), size = (50, 50), png = 1), # index 1 is bt_icon
					],
					"fonts": [gFont("Regular", 40), gFont("Regular", 28) ,gFont("Regular", 22), gFont("Regular", 16)],
					"itemHeight": 70
				}
				</convert>
			</widget>
			<widget source="description" render="Label" position="30,410" size="600,90" font="Regular;28" halign="center" valign="center" />
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
		BluetoothDiscovery.__init__(self)
		self.session = session

		self["key_red"] = Label(_("Exit"))
		self["key_green"] = Label(" ")
		self["key_yellow"] = Label(" ")
		self["key_blue"] = Label(" ")

		self["shortcuts"] = ActionMap(["BluetoothSetupActions"],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"red": self.keyRed,
			"green": self.keyGreen,
			"blue": self.keyBlue,
			"menu": self.keyMenu,
		}, -2)

		self["deviceList"] = List(self.deviceList)
		self["description"] = StaticText(_("Starting..."))

		self.onLayoutFinish.append(self.onLayoutFinishCB)
		self.onClose.append(self.onCloseCB)

		self.registerStateChangeCB(self.updateKeyDesc)

	def onLayoutFinishCB(self):
		self.setTitle(_("Bluetooth Scan"))
		self.initialStart()

	def onCloseCB(self):
		self.deInit()

	def updateDeviceList(self):
		self.deviceList = []
		discoverd_devices = self.getDiscDevice()
		if discoverd_devices:
			device_keys = list(discoverd_devices.keys())
			device_keys.sort()
			for k in device_keys:
				v = discoverd_devices[k]
				if v["bd_addr"] in self.pairedDevices:
					continue

				device_info = v.copy()

				bd_addr = device_info['bd_addr']

				# check duplicate info
				skip = False
				for x in self.deviceList:
					_mac_addr = x[2]['bd_addr']
					if _mac_addr == bd_addr:
						skip = True
						break

				if skip:
					continue

				name = device_info["name"]
				if not name:
					name = "NONAME"

				profile = device_info["profile"]
				if name == bt_types.BT_VUPLUS_RCU_NAME:
					profile = bt_types.BT_PROFILE_VU_RC

				name += ' (' + bd_addr + ')'
				icon = getIcon(profile)
				deviceEntry = (name, icon, device_info)
				self.deviceList.append(deviceEntry)

		self["deviceList"].setList(self.deviceList)

	def updateKeyDesc(self):
		key_blue_text = " "
		key_green_text = " "

		autoReScan = config.plugins.bluetoothsetup.autoRestartScan.value

		if self.isIdle():
			if not autoReScan:
				key_blue_text = _("Start scan")
		elif self.isScanning():
			if not autoReScan:
				key_blue_text = _("Stop scan")

		if not self.isPairing():
			if self.deviceList:
				cur = self["deviceList"].getCurrent()
				if cur:
					key_green_text = _("Connect")

		self["key_green"].setText(key_green_text)
		self["key_blue"].setText(key_blue_text)

	def updateDescription(self, text):
		self["description"].setText(text)

	def eventHandled(self):
		self.updateKeyDesc()

	def scanStartAbort(self):
		if config.plugins.bluetoothsetup.autoRestartScan.value:
			return

		if self.isIdle():
			self.addTaskStartScan()
		elif self.isScanning():
			self.addTaskAbortScan()

	def doExit(self, msg=None):
		if msg:
			self.close(msg)
		else:
			self.close()

	def keyGreen(self):
		cur = self["deviceList"].getCurrent()
		if not cur:
			return

		if self.isPairing() or self.isDisconnecting():
			return

		mac = cur[2]["bd_addr"]
		profile = cur[2]["profile"]
		name = cur[2]["name"]

		if isAudioProfile(profile):
			audio_connected = self.vubt.getAudioDeviceConnected()
			if audio_connected:
				self.addTaskDisconnect(audio_connected['bd_addr'], audio_connected['profile'], audio_connected['name'])

		self.addTaskPairing(mac, profile, name)

	def keyBlue(self):
		if self.isPairing() or self.isDisconnecting():
			return

		self.scanStartAbort()

	def keyRed(self):
		self.addTaskExit()

	def keyOk(self):
		self.keyGreen()

	def keyCancel(self):
		self.keyRed()

	def keyMenu(self):
		self.session.open(BluetoothSetupConfig)


class BluetoothRCUSetup(BluetoothDiscoveryScreen):
	def __init__(self, session, autoStart=True):
		BluetoothDiscoveryScreen.__init__(self, session)

		self["key_red"] = Label(_(" "))
		self["shortcuts"] = ActionMap(["BluetoothSetupActions"],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"vuRcuSetup": self.keyVuRcuSetup,
		}, -2)

		self.autoStart = autoStart

		self.pairingTimer = eTimer()
		self.pairingTimer.callback.append(self.pairingTimerCB)
		self.MaxscanTime = 10 # sec
		self.scanRetry = 3

		self.scanningText = _("Scanning VUPLUS BLE RCU")

	def keyVuRcuSetup(self):
		self.initialStart()

	def pairingTimerCB(self):
		if self.vuRcuPairingInfo:
			(mac, name, profile) = self.vuRcuPairingInfo
			self.addTaskPairing(mac, profile, name)
		else:
			text = _("%s is not found.") % (bt_types.BT_VUPLUS_RCU_NAME)
			self.Exit(text)

	def onLayoutFinishCB(self):
		self.setTitle(_("Vu+ Bluetooth RCU Setup"))
		if self.autoStart:
			self.initialStart()
		else:
			self.updateDescription(_("Press and hold the buttons <MENU+AUDIO>\n for five seconds to start."))

	def keyOk(self):
		if self.isTaskEmpty():
			self.close()

	def keyCancel(self):
		if self.isTaskEmpty():
			self.close()

	def updateKeyDesc(self):
		pass

	def startScan(self):
		ret = self.vubt.startScan(True)
		if ret:
			self.scanAbortTimer.start(self.MaxscanTime * 1000, True)
			self.displayScanMsgStart()

		else:
			text = _("Scan failed. Please try again VUPLUS BLE RCU setup.\n(AUDIO+MENU buttons)")
			self.Exit(text)

		return ret

	def updateDeviceList(self):
		self.deviceList = []
		discoverd_devices = self.getDiscDevice()
		if discoverd_devices:
			for (k, v) in list(discoverd_devices.items()):
				if v["name"] != bt_types.BT_VUPLUS_RCU_NAME:
					continue

				device_info = v.copy()
				bd_addr = device_info['bd_addr']
				name = device_info["name"]
				desc = "%s (%s)" % (name, bd_addr)

				icon = getIcon(bt_types.BT_PROFILE_VU_RC)
				deviceEntry = (desc, icon, device_info)
				self.deviceList.append(deviceEntry)
				break

		self["deviceList"].setList(self.deviceList)

	def getVuRCUInfo(self):
		vuRcuDevInfo = []
		for d in self.deviceList:
			if d[2]['name'] == bt_types.BT_VUPLUS_RCU_NAME:
				_mac = d[2]['bd_addr']
				_name = d[2]['name']
				_profile = d[2]['profile']
				vuRcuDevInfo = (_mac, _name, _profile)
				break

		return vuRcuDevInfo

	def onScanFinished(self, event, args):
		self.scanningTimer.stop()
		self.updateDeviceList()
		self.vuRcuPairingInfo = self.getVuRCUInfo()
		if self.vuRcuPairingInfo:
			self.updateDescription(_("Pairing %s") % bt_types.BT_VUPLUS_RCU_NAME)
			self.pairingTimer.start(1000, True)
		else:
			if self.scanRetry:
				self.scanRetry -= 1
				self.scanTimer.start(0, True)
			else:
				text = _("%s is not found.") % (bt_types.BT_VUPLUS_RCU_NAME)
				self.doExit(text)

	def onPairingSuccess(self, event, args):
		if event in self.descriptionList:
			(mac, profile, name) = args
			self.doExit(self.descriptionList[event] % name)

	def onPairingFailed(self, event, args):
		if event in self.descriptionList:
			(mac, profile, name) = args
			self.doExit(self.descriptionList[event] % name)

	def onDeviceAdded(self, event, name, data):
		if name == bt_types.BT_VUPLUS_RCU_NAME:
			self.scanAbortTimer.start(10, True)

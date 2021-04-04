from Plugins.Plugin import PluginDescriptor

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSelection, getConfigListEntry, ConfigSubsection, ConfigYesNo, ConfigText, ConfigSelectionNumber, ConfigNumber
from Components.ConfigList import ConfigListScreen
from Components.Console import Console
from Components.GUIComponent import GUIComponent
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap, MultiPixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.VolumeControl import VolumeControl

from Tools.BoundFunction import boundFunction

from Tools.Notifications import AddNotification, AddNotificationWithCallback, AddPopup
from Tools.Directories import pathExists, fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN, SCOPE_METADIR
from skin import loadSkin

from enigma import eTimer, eServiceReference
from enigma import eDVBVolumecontrol

import os
import re
import time
from . import vubt
from .bt_types import getEventDesc, isAudioProfile, getIcon
from . import bt_types

from .OTAUpdate import VuRcuOtaUpdate

BT_AUDIO_DELAY_PROC = "/proc/stb/audio/btaudio_delay_pcm"
BT_AUDIO_ONOFF_PROC = "/proc/stb/audio/btaudio"

config.plugins.bluetoothsetup = ConfigSubsection()
config.plugins.bluetoothsetup.enable = ConfigYesNo(default=False)
config.plugins.bluetoothsetup.audiodelay = ConfigSelectionNumber(-1000, 1000, 5, default=-50)
config.plugins.bluetoothsetup.showMessageBox = ConfigYesNo(default=True)
config.plugins.bluetoothsetup.showBatteryLow = ConfigYesNo(default=True)
config.plugins.bluetoothsetup.lastAudioConnEnable = ConfigYesNo(default=True)
config.plugins.bluetoothsetup.lastAudioConn = ConfigText(default="")
config.plugins.bluetoothsetup.autoRestartScan = ConfigYesNo(default=True)
config.plugins.bluetoothsetup.scanTime = ConfigSelectionNumber(8, 60, 1, default=30)
config.plugins.bluetoothsetup.vurcuSkipFwVer = ConfigNumber(default=0)
config.plugins.bluetoothsetup.voiceCheckDb = ConfigSelectionNumber(-40, -20, 1, default=-33)
config.plugins.bluetoothsetup.voiceCallbackName = ConfigSelection(default="Unknown", choices=[("Unknown", "Unknown")])

pybluetooth_instance = None


class VoiceEventHandler:
	def __init__(self):
		self.voiceHandlers = []
		self.textHandlers = []
		#self.voiceHandlers.append(self.startPlayVoiceTimer)

		self.showVoiceMsgTimer = eTimer()
		self.showVoiceMsgTimer.callback.append(self.showVoiceMsg)

		self.closeVoiceMsgTimer = eTimer()
		self.closeVoiceMsgTimer.callback.append(self.closeVoiceMsg)

		self.noVoiceMsgTimer = eTimer()
		self.noVoiceMsgTimer.callback.append(self.handleNoVoiceEventCB)

		self.voiceMsg = None

		self.isMuted = False

		self.playVoiceTimer = eTimer()
		self.playVoiceTimer.callback.append(self.playVoiceFile)

		self.playVoiceMsg = None
		self.closePlayVoiceMsgTimer = eTimer()
		self.closePlayVoiceMsgTimer.callback.append(self.closePlayVoiceMsg)

		self.lastServiceRef = None

	def showListenMessageBox(self, flag):
		try:
			callback = self.findListenCallbackByName(config.plugins.bluetoothsetup.voiceCallbackName.value)
			if callback is not None:
				callback(flag)
				return
		except Exception as e:
			pass

		if flag == "empty":
			text = _("There is no voice input.")
			self.session.open(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=5)
		elif flag == "listen":
			text = _("Put your voice close to the remote control...")
			self.voiceMsg = self.session.open(MessageBox, text, type=MessageBox.TYPE_INFO, enable_input=False)

	def setMute(self):
		volumeControlHandle = eDVBVolumecontrol.getInstance()
		if volumeControlHandle.isMuted():
			self.isMuted = True
		else:
			self.isMuted = False
			volumeControlHandle.volumeMute()

	def unsetMute(self):
		volumeControlHandle = eDVBVolumecontrol.getInstance()
		if volumeControlHandle.isMuted():
			if not self.isMuted:
				volumeControlHandle.volumeUnMute()

		self.isMuted = False

	def showVoiceMsg(self):
		self.setMute()
		if self.voiceMsg is None:
			self.showListenMessageBox("listen")

	def closeVoiceMsg(self):
		self.unsetMute()
		if self.voiceMsg:
			self.voiceMsg.close()
			self.voiceMsg = None

	def handleVoiceEvent(self, value):
		voiceCallbackName = config.plugins.bluetoothsetup.voiceCallbackName.value
		if value and (self.voiceMsg is None):
			self.showVoiceMsgTimer.start(True, 100)

		elif not value:
			self.closeVoiceMsgTimer.start(True, 100)

	def handleNoVoiceEvent(self):
		self.noVoiceMsgTimer.start(True, 500)

	def handleNoVoiceEventCB(self):
		if self.session.dialog_stack and not self.session.in_exec:
			self.handleNoVoiceEvent()
		else:
			self.showListenMessageBox("empty")

	# BT_EVENT_NEW_VOICE occurred.
	def voiceEventCallback(self):
		name = config.plugins.bluetoothsetup.voiceCallbackName.value
		for callback in self.findVoiceCallbackByName(name):
			try:
				callback(bt_types.BT_VOICE_PATH)
			except:
				pass

	def updateCallbackNameList(self):
		voiceCallbackNameList = [("Default", "Default")]
		for x in self.voiceHandlers:
			callbackItem = (x[2], x[2])
			if callbackItem not in voiceCallbackNameList:
				voiceCallbackNameList.append(callbackItem)
		config.plugins.bluetoothsetup.voiceCallbackName = ConfigSelection(default="Default", choices=voiceCallbackNameList)

	def findListenCallbackByName(self, name):
		for x in self.voiceHandlers:
			if x[2] == name:
				return x[3]
		return None

	def findVoiceCallbackByName(self, name):
		callback_list = []
		for x in self.voiceHandlers:
			if x[2] == name:
				callback_list.append(x[0])
		return callback_list

	def findVoiceCallbackByHandler(self, handler):
		for x in self.voiceHandlers:
			if x[0] == handler:
				return x
		return None

	# add Speech to Text handler
	def addVoiceHandler(self, handler):
		self.addVoiceHandlerWithName(handler)

	# add Speech to Text handler
	def addVoiceHandlerWithName(self, handler, priority=100, name="Default", listenHandler=None):
		if handler not in self.findVoiceCallbackByName(name):
			self.voiceHandlers.append((handler, priority, name, listenHandler))
			self.voiceHandlers = sorted(self.voiceHandlers, key=lambda h: h[1])
			self.updateCallbackNameList()

	def removeVoiceHandler(self, handler):
		callback = self.findVoiceCallbackByHandler(handler)
		if callback is not None:
			self.voiceHandlers.remove(callback)

	# Called by VoiceHandlers
	def textEventCallback(self, text):
		for x in self.textHandlers:
			x(text)

	def addTextHandler(self, handler):
		if handler not in self.textHandlers:
			self.textHandlers.append(handler)

	def removeTextHandler(self, handler):
		if handler in self.textHandlers:
			self.textHandlers.remove(handler)

	def startPlayVoiceTimer(self, value):
		self.playVoiceTimer.start(True, 200)

	def playVoiceFile(self):
		if self.session.dialog_stack and not self.session.in_exec:
			self.startPlayVoiceTimer(None)
			return

		if self.session:
			self.lastServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
			self.voiceSref = eServiceReference('4097:0:0:0:0:0:0:0:0:0:%s' % bt_types.BT_VOICE_PATH)
			self.session.nav.stopService()
			self.session.nav.playService(self.voiceSref)

			if self.playVoiceMsg is None:
				text = _("Playing Voice data...")
				self.session.openWithCallback(self.closePlayVoiceMsg, MessageBox, text, type=MessageBox.TYPE_INFO, timeout=10)

	def closePlayVoiceMsg(self, value):
		if self.lastServiceRef:
			self.session.nav.playService(self.lastServiceRef)
			self.lastServiceRef = None


class BTVolumeControl:
	def __init__(self):
		self.initVolumeTimer = eTimer()
		self.initVolumeTimer.callback.append(self.InitVolume)
		self.initVolumeTimer.start(500, True)

	def InitVolume(self):
		try:
			vol = config.audio.volume.value
			self.setVolume(vol)
		except:
			self.initVolumeTimer.start(100, True)

	def setVolume(self, vol):
		self.vubt.setVolume(int(vol))


class BTAutoAudioConnect:
	def __init__(self):
		self.requestAudioTimer = eTimer()
		self.requestAudioTimer.callback.append(self.doStartAudioConnectCB)

		self.btaudioActivated = False
		self.btaudioActivatedInstandby = False

		self.autoAudioMac = None
		self.autoAudioRetryDefault = 5
		self.autoAudioRetry = self.autoAudioRetryDefault

	def enable(self):
		# start Last Audio Connect
		isEnable = config.plugins.bluetoothsetup.enable.value
		bd_addr = config.plugins.bluetoothsetup.lastAudioConn.value

		if isEnable and bd_addr:
			pairedDevices = self.getPairedDevice()
			if pairedDevices:
				for (k, v) in list(pairedDevices.items()):
					if v['bd_addr'] == bd_addr:
						self.doStartAudioConnectTimer(bd_addr)
						return

		# bdaddr is not int pairind list
		config.plugins.bluetoothsetup.lastAudioConn.value = ""

	def disable(self):
		# save Last Audio Connect
		bd_addr = self.getLastAudioConnect()
		if bd_addr:
			self.updateLastAudioConnect(bd_addr)

	def doStartAudioConnectTimer(self, bd_addr):
		if not bd_addr:
			return

		self.requestAudioTimer.stop()
		self.autoAudioMac = bd_addr
		if not self.isAudioDeviceConnected():
			print("[BT] auto audio connect start, %s" % self.autoAudioMac)
			self.requestAudioTimer.start(500, True)

	def doStartAudioConnectCB(self):
		print("[BT] request audio connect, %s" % self.autoAudioMac)
		self.requestAudioTimer.stop()
		if self.autoAudioMac:
			self.requestConnect(self.autoAudioMac)

	def autoAudioReset(self):
		self.autoAudioMac = None
		self.autoAudioRetry = self.autoAudioRetryDefault

	def retryAudioConnectTimer(self, bd_addr):
		if (bd_addr is not None) and (self.autoAudioMac == bd_addr):
			if self.autoAudioRetry > 0:
				self.autoAudioRetry -= 1
				self.requestAudioTimer.stop()
				print("[BT] retry audio connect, %s" % self.autoAudioMac)
				self.requestAudioTimer.start(500, True)
			else:
				self.autoAudioReset()

	def getLastAudioConnect(self):
		audio_connected = self.getAudioDeviceConnected()
		if audio_connected:
			return audio_connected['bd_addr']

		return None

	def updateLastAudioConnect(self, bd_addr):
		if bd_addr is None:
			return

		self.autoAudioReset()

		print("[BT] update Last Audio Connect, %s" % bd_addr)
		if config.plugins.bluetoothsetup.lastAudioConn.value != bd_addr:
			config.plugins.bluetoothsetup.lastAudioConn.value = bd_addr
			config.plugins.bluetoothsetup.lastAudioConn.save()

	def activateBTAudioOut(self, enable):
		if enable and self.btaudioActivated:
			print("[BT] already btaudio activated!")
			return

		if not enable and not self.btaudioActivated:
			print("[BT] already btaudio inactivated!")
			return

		self.btaudioActivated = enable
		self.setBTAudioDelay(True)

		time.sleep(0.05)

		try:
			global BT_AUDIO_ONOFF_PROC
			fd = open(BT_AUDIO_ONOFF_PROC, 'w')
			data = enable and "on" or "off"
			fd.write(data)
			fd.close()
		except:
			print("[BT] set %s failed!" % BT_AUDIO_ONOFF_PROC)
 
	def setBTAudioDelay(self, updateNow=True):
		global BT_AUDIO_DELAY_PROC
		if self.btaudioActivated:
			data = int(config.plugins.bluetoothsetup.audiodelay.value) * 90
			if data < 0:
				data = hex(int('0xffffffff', 16) + data - 1).strip('0x')
			elif data > 0:
				data = hex(data).strip('0x')
			else:
				data = '0'
		else:
			data = '0'

		if self.btaudioActivated or updateNow:
			try:
				global BT_AUDIO_DELAY_PROC
				fd = open(BT_AUDIO_DELAY_PROC, 'w')
				fd.write(data)
				fd.close()
			except:
				print("[BT] set %s failed!" % BT_AUDIO_DELAY_PROC)

	def isAudioDeviceConnected(self):
		return bool(self.getAudioDeviceConnected())

	def getAudioDeviceConnected(self):
		audio_connected = None
		paired_devices = self.getPairedDevice()
		if paired_devices:
			for (k, v) in list(paired_devices.items()):
				if (isAudioProfile(v['profile'])) and v['isConnected']:
					audio_connected = {}
					audio_connected['name'] = v['name']
					audio_connected['bd_addr'] = v['bd_addr']
					audio_connected['profile'] = v['profile']
					break

		return audio_connected


class BTInStandby:
	def __init__(self):
		config.misc.standbyCounter.addNotifier(self.standbyBegin, initial_call=False)
		self.enable_on_standby = False

	def standbyBegin(self, configElement):
		self.enable_on_standby = config.plugins.bluetoothsetup.enable.value

		if self.enable_on_standby:
			from Screens.Standby import inStandby
			if self.standbyEnd not in inStandby.onClose:
				inStandby.onClose.append(self.standbyEnd)

			self.disconnectAll()

			time.sleep(0.1)
			self.disable(False)

	def standbyEnd(self):
		if self.enable_on_standby:
			self.enable()


class BTBatteryLevel:
	def __init__(self):
		self.batteryLevelTimer = eTimer()
		self.batteryLevelTimer.callback.append(self.updateBatteryLevel)
		self.batteryUpdateInterval = 60 * 60 * 12 * 1000 # every 12 hours
		self.batteryCheckRetryTime = 15 * 1000 # maximum time to waiting voice stop
		self.lastMsgMday = -1
		self.batteryLevel = 0

	def startBatteryTimer(self):
		self.lastMsgMday = -1
		self.batteryLevelTimer.start(100, True)

	def updateBatteryLevel(self):
		if self.vubt.getStatus() == self.BT_STATUS_ENABLED:
			# Do not check the battery during voice recording.
			if self.vubt.isVoiceRecording():
				self.batteryLevelTimer.start(self.batteryCheckRetryTime, True)
			else:
				self.vubt.updateBatteryLevel()
				self.batteryLevelTimer.start(self.batteryUpdateInterval, True)

	def disableBatteryLevel(self):
		self.batteryLevelTimer.stop()

	def getMday(self):
		return time.localtime().tm_mday

	def showLowBatteryMessage(self):
		mDay = self.getMday()
		if self.lastMsgMday != mDay:
			self.lastMsgMday = mDay
			AddNotification(MessageBox, _("Battery is low. Suggest to prepare replacement batteries for using properly %s.") % bt_types.BT_VUPLUS_RCU_NAME, type=MessageBox.TYPE_INFO)


class BTOTAProcess:
	OTA_COMPLETE = 34
	OTA_APP_VERSION = 2
	OTA_FILE_APP_VERSION = 7

	def __init__(self):
		self.pluginOtaEventHandler = []
		self.vubt.OTA_addEventCallback(self.OTAEventCallback)

		self.startOTATimer = eTimer()
		self.startOTATimer.callback.append(self.startOTAUpdate)

		self.handleOtaDoneTimer = eTimer()
		self.handleOtaDoneTimer.callback.append(self.handleOtaDoneTimerCB)

		self.firmwareCheckTimer = eTimer()
		self.firmwareCheckTimer.callback.append(self.checkFWVersion)
		self.FWCheckRetryTime = 15 * 1000 # maximum time to waiting voice stop
		self.bd_addr = None
		self.rcuAppVersion = None

	def OTAEventCallback(self, evType, value):
		print("[OTAEventCallback] evType : %s, value : %s" % (str(evType), str(value)))
		
		if evType == BTOTAProcess.OTA_COMPLETE:
			self.handleOtaDoneTimer.start(0, True)

		elif evType == BTOTAProcess.OTA_APP_VERSION:
			self.rcuAppVersion = value

		elif evType == BTOTAProcess.OTA_FILE_APP_VERSION:
			self.firmwareFileVersion = value

			# check app version
			if self.firmwareFileVersion > self.rcuAppVersion:
				if config.plugins.bluetoothsetup.vurcuSkipFwVer.value != self.firmwareFileVersion:
					self.showFWUpdateNoti()
		else:
			try:
				for handler in self.pluginOtaEventHandler:
					handler(evType, value)
			except Exception as e:
				print("[BT] exception error : %s" % str(e))

	def OTAInit(self):
		self.vubt.OTAInit()

	def OTADeInit(self):
		self.vubt.OTADeInit()

	def OTAStart(self):
		self.otaMode = True
		self.vubt.OTAStart()

	def OTAStop(self):
		self.vubt.OTAStop()
		self.otaMode = False

	def handleOtaDoneTimerCB(self):
		self.OTAStop()

	def startFWCheckTimer(self, bd_addr):
		self.bd_addr = bd_addr
		self.firmwareCheckTimer.start(0, True)

	def checkFWVersion(self):
		if self.vubt.getStatus() == self.BT_STATUS_ENABLED:
			# Do not check the battery during voice recording.
			if self.vubt.isVoiceRecording():
				self.firmwareCheckTimer.start(self.FWCheckRetryTime, True)
			else:
				self.vubt.OTACheckFWVersion(self.bd_addr, bt_types.BT_FIRMWARE_FILEPATH)

	def stopFWCheckTimer(self):
		self.firmwareCheckTimer.stop()

	def showFWUpdateNoti(self):
		_title = _("New firmware detected for VUPLUS-BLE-RCU.\n\n")
		_title += _("While the update is progress, RCU can not be used and other bluetooth device must be disconnected.\n\n")
		_title += _("Current FW version : %d\nNew FW version : %d") % (self.rcuAppVersion, self.firmwareFileVersion)
		choiceList = ((_("Upgrade now"), "update"), (_("Remind Me later"), "no"), (_("Skip this version"), "skip"))
		AddNotificationWithCallback(self.showFWUpdateAnswer, ChoiceBox, _title, choiceList)

	def showFWUpdateAnswer(self, answer):
		if answer:
			if answer[1] == 'update':
				config.plugins.bluetoothsetup.vurcuSkipFwVer.value = 0
				config.plugins.bluetoothsetup.vurcuSkipFwVer.save()
				if not self.isVuBleRcuConnected():
					text = _('VUPLUS-BLE-RCU is disconnected. Please connect and select again.')
					AddNotification(MessageBox, _(text), type=MessageBox.TYPE_INFO)
				elif self.session and self.bd_addr:
					self.startOTATimer.start(0, True)

			elif answer[1] == 'skip':
				config.plugins.bluetoothsetup.vurcuSkipFwVer.value = self.firmwareFileVersion
				config.plugins.bluetoothsetup.vurcuSkipFwVer.save()
				text = _('If you want to update this firmware version, follow belows.\n\n')
				text += _('1. Move to Bluetooth Setup Options.\n(press MENU key in BluetoothSetup)\n')
				text += _('2. Change "Skip firmware update of VUPLUS-BLE-RCU" option to "no"\n')
				text += _('3. Reconnect the VUPLUS-BLE-RCU.\n\n')
				AddNotification(MessageBox, _(text), type=MessageBox.TYPE_INFO)

	def startOTAUpdate(self):
		self.session.open(VuRcuOtaUpdate, self.bd_addr, self, self.batteryLevel, self.rcuAppVersion, self.firmwareFileVersion)

	def isVuBleRcuConnected(self):
		connected = False
		paired_devices = self.getPairedDevice()
		if paired_devices:
			for (k, v) in list(paired_devices.items()):
				if v['name'] == bt_types.BT_VUPLUS_RCU_NAME:
					if v['isConnected']:
						connected = True

					break

		return connected


class BTHotplugEvent:
	def __init__(self):
		self.btEnableTimer = eTimer()
		self.btEnableTimer.callback.append(self.enableTimerCB)

		self.btDisableTimer = eTimer()
		self.btDisableTimer.callback.append(self.disableTimerCB)

		self.showBtDongleMsgTimer = eTimer()
		self.showBtDongleMsgTimer.callback.append(self.showBtDongleMsg)

	def startEnableTimer(self, _enable):
		from Screens.Standby import inStandby
		if inStandby:
			print("[BTHotplugEvent] now in standby, skip BT hotplug event.")
			return

		print("[BTHotplugEvent] startEnableTimer! ", _enable)

		self.btEnableTimer.stop()
		self.btDisableTimer.stop()

		if _enable:
			self.btEnableTimer.start(500, True)
		else:
			self.btDisableTimer.start(500, True)

	def enableTimerCB(self):
		print("[BTHotplugEvent] Enable")

		if config.plugins.bluetoothsetup.enable.value:
			self.onOffChanged(True)
			time.sleep(0.1)

		if self.pluginEventHandler:
			for handler in self.pluginEventHandler:
				handler(bt_types.BT_EVENT_BT_CONNECTED, None)

	def disableTimerCB(self):
		print("[BTHotplugEvent] Disable")

		if self.isEnabled():
			if self.isVuBleRcuConnected():
				self.showBtDongleMsgTimer.start(100, True)

		self.onOffChanged(False)
		time.sleep(0.1)

		if self.pluginEventHandler:
			for handler in self.pluginEventHandler:
				handler(bt_types.BT_EVENT_BT_DISCONNECTED, None)

	def showBtDongleMsg(self):
		if self.session.dialog_stack and not self.session.in_exec:
			self.showBtDongleMsgTimer.start(500, True)
		else:
			text = _("The BT dongle has been removed. It takes 10 seconds from when the BT dongle is removed until the remote control operates in IR mode.")
			self.session.open(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=20)

	def handleInsertEvent(self):
		self.startEnableTimer(True)

	def handleRemoveEvent(self):
		self.startEnableTimer(False)

	def checkBTUSB(self):
		return self.vubt.checkBTUSB()


class PyBluetoothInterface(VoiceEventHandler, BTVolumeControl, BTAutoAudioConnect, BTInStandby, BTBatteryLevel, BTOTAProcess, BTHotplugEvent):
	BT_STATUS_DISABLED = 0
	BT_STATUS_ENABLED = 1

	def __init__(self):
		self.vubt = vubt.Vu_PyBluetooth()

		VoiceEventHandler.__init__(self)
		BTVolumeControl.__init__(self)
		BTAutoAudioConnect.__init__(self)
		BTInStandby.__init__(self)
		BTBatteryLevel.__init__(self)
		BTOTAProcess.__init__(self)
		BTHotplugEvent.__init__(self)

		self.vubt.addEventCallback(self.eventCallback)
		self.vubt.addBleEventCallback(self.bleEventCallback)
		self.status = self.BT_STATUS_DISABLED
		self.pluginEventHandler = []
		self.pluginBleEventHandler = []
		self.pluginStatusHandler = []
		self.session = None

		self.otaMode = False

	def disconnectAll(self):
		self.deviceList = []
		pairedDevices = self.vubt.getPairedDevice()

		if pairedDevices:
			for (k, v) in list(pairedDevices.items()):
				if v['isConnected']:
					self.vubt.requestDisconnect(v['bd_addr'])

	def setScanTime(self, scanDuration):
		scanDuration = int(scanDuration)
		if (scanDuration <= 0) or (scanDuration > 30):
			print("[BT] invalid scanDuration")
			return

		self.vubt.setScanTime(scanDuration)

	def eventCallback(self, evType, data):
		if self.otaMode:
			return

		'''
		print "[eventCallback] evType : %s" % str(evType)
		print "[eventCallback] data : %s" % str(data)
		print "[eventCallback] event : %s" % (getEventDesc(evType))
		'''

		bd_addr = data.get("bd_addr", None)
		name = data.get("name", bd_addr)

		try:
			if evType == bt_types.BT_EVENT_REQUEST_AUDIO_CONNECT:
				self.doStartAudioConnectTimer(bd_addr)
			elif evType == bt_types.BT_EVENT_CONNECT_TIMEOUT:
				if isAudioProfile(data['profile']):
					self.retryAudioConnectTimer(bd_addr)
			elif evType == bt_types.BT_EVENT_BT_CONNECTED:
				self.handleInsertEvent()
			elif evType == bt_types.BT_EVENT_BT_DISCONNECTED:
				self.handleRemoveEvent()

			elif evType in (bt_types.BT_EVENT_BT_VOICE_START, bt_types.BT_EVENT_BT_VOICE_STOP):
				self.handleVoiceEvent(evType == bt_types.BT_EVENT_BT_VOICE_START)

			elif evType == bt_types.BT_EVENT_NEW_VOICE:
				self.voiceEventCallback()
			elif evType == bt_types.BT_EVENT_BT_NO_VOICE:
				self.handleNoVoiceEvent()
			else:
				if evType == bt_types.BT_EVENT_CONNECTED:
					if (isAudioProfile(data['profile'])) and data['connected']:
						self.updateLastAudioConnect(bd_addr)
						self.activateBTAudioOut(True)

				if evType == bt_types.BT_EVENT_DISCONNECTED:
					if (isAudioProfile(data['profile'])) and not data['connected']:
						self.activateBTAudioOut(False)

				if self.pluginEventHandler:
					for handler in self.pluginEventHandler:
						handler(evType, data)

				elif evType in (bt_types.BT_EVENT_CONNECTED, bt_types.BT_EVENT_DISCONNECTED):
					if config.plugins.bluetoothsetup.showMessageBox.value:
						from Screens.Standby import inStandby
						if self.session and not inStandby:
							if evType == bt_types.BT_EVENT_CONNECTED:
								text = _("%s is connected.") % name
							elif evType == bt_types.BT_EVENT_DISCONNECTED:
								text = _("%s is disconnected.") % name
							AddPopup(text=text, type=MessageBox.TYPE_INFO, timeout=5, id="bt_event_connected")

		except Exception as e:
			print("[BT] exception error : %s" % str(e))

	def bleEventCallback(self, evType, data):
		if self.otaMode:
			return

		'''
		print "[bleEventCallback] evType : %s" % str(evType)
		print "[bleEventCallback] data : %s" % str(data)
		print "[bleEventCallback] event : %s" % (getEventDesc(evType))
		'''

		bd_addr = data.get("bd_addr", None)
		name = data.get("name", bd_addr)
		value = data.get("value", None)

		try:
			if evType == bt_types.BT_EVENT_CONNECTED:
				if name == bt_types.BT_VUPLUS_RCU_NAME:
					self.startBatteryTimer()

			elif evType == bt_types.BT_EVENT_DISCONNECTED:
				if name == bt_types.BT_VUPLUS_RCU_NAME:
					self.batteryLevelTimer.stop()

			elif evType == bt_types.BT_EVENT_CONNECT_TIMEOUT:
				pass
			elif evType == bt_types.BT_EVENT_READ_BATTERY_LEVEL:
				if value:
					print("[bleEventCallback] get battery level : %d (%s)" % (value, bd_addr))

					self.batteryLevel = value
					isBatteryLow = (name == bt_types.BT_VUPLUS_RCU_NAME) and (self.batteryLevel < bt_types.BT_BATTERY_LEVEL_LOW)
					if isBatteryLow:
						if config.plugins.bluetoothsetup.showBatteryLow.value:
							self.showLowBatteryMessage()
					else:
						self.startFWCheckTimer(bd_addr)

			if self.pluginBleEventHandler:
				for handler in self.pluginBleEventHandler:
					handler(evType, data)

		except Exception as e:
			print("[bleEventCallback] exception error : %s" % str(e))

	def onOffChanged(self, value=True):
		if value and (not self.isEnabled()):
			self.enable()
		elif (not value) and self.isEnabled():
			self.disable()

	def enable(self):
		self.vubt.enable()
		self.updateStatus()
		BTAutoAudioConnect.enable(self)

	def disable(self, update=True):
		BTAutoAudioConnect.disable(self)
		self.vubt.disable()
		if update:
			self.updateStatus()

		self.disableBatteryLevel()
		self.stopFWCheckTimer()

	def isEnabled(self):
		return self.status == self.BT_STATUS_ENABLED

	def updateStatus(self):
		self.status = self.vubt.getStatus()
		print("[BT] current status : %s" % str(self.status))

		for handler in self.pluginStatusHandler:
			handler(self.status)			

	def startScan(self, isBle=False):
		return self.vubt.startScan(False, isBle)

	def abortScan(self):
		self.vubt.abortScan()

	def resetScan(self):
		self.vubt.resetScan()

	def getSystemInfo(self):
		return self.vubt.getSystemInfo()

	def getDiscDevice(self):
		return self.vubt.getDiscDevice()

	def getPairedDevice(self):
		return self.vubt.getPairedDevice()

	def requestPairing(self, mac):
		return self.vubt.requestPairing(mac)

	def cancelPairing(self, mac):
		return self.vubt.cancelPairing(mac)

	def removePairing(self, mac, profile):
		if isAudioProfile(profile):
			self.updateLastAudioConnect("")
		return self.vubt.removePairing(mac)

	def requestConnect(self, mac):
		return self.vubt.requestConnect(mac)

	def requestDisconnect(self, mac, profile):
		if isAudioProfile(profile):
			self.updateLastAudioConnect("")
		return self.vubt.requestDisconnect(mac)

	def requestBLEConnect(self, mac):
		return self.vubt.requestBLEConnect(mac)

	def requestBLEDisconnect(self, mac):
		return self.vubt.requestBLEDisconnect(mac)

	def setDisCoverable(self, value):
		self.vubt.setDisCoverable(value)

	def setSession(self, session):
		self.session = session

	def cleanupBleClient(self):
		self.vubt.cleanupBleClient()

	def setVoiceCheckDB(self, value):
		int_value = int(value)
		print("[setVoiceCheckDB] value : %d" % int_value)
		self.vubt.setVoiceCheckDB(int_value)


pybluetooth_instance = PyBluetoothInterface()


def BluetoothOnOffChanged(configElement):
	global pybluetooth_instance
	pybluetooth_instance.onOffChanged(configElement.value)


config.plugins.bluetoothsetup.enable.addNotifier(BluetoothOnOffChanged)


def BluetoothAudioDelayChanged(configElement):
	global pybluetooth_instance
	pybluetooth_instance.setBTAudioDelay(False)


config.plugins.bluetoothsetup.audiodelay.addNotifier(BluetoothAudioDelayChanged)


def BluetoothVoiceCheckValChanged(configElement):
	global pybluetooth_instance
	pybluetooth_instance.setVoiceCheckDB(configElement.value)


config.plugins.bluetoothsetup.voiceCheckDb.addNotifier(BluetoothVoiceCheckValChanged)


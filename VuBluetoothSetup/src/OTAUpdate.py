# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.HelpMenu import HelpableScreen
from Screens.ChoiceBox import ChoiceBox

# Generic
from Tools.BoundFunction import boundFunction
from Tools.Directories import *
from Components.config import config
import os

# GUI (Components)
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Label import Label
from Components.Button import Button
from Components.ProgressBar import ProgressBar

# Timer
from enigma import eTimer

from . import bt_types
from .bt_types import getEventDesc
from .bt_task import BluetoothTask

OTA_ERROR_SERVICE_DISCOVERY = 0
OTA_BATTERY_LEVEL = 1
#OTA_APP_VERSION = 2
OTA_PATCH_VERSION = 3
OTA_ERROR_READ_BATTERY_LEVEL = 4
OTA_ERROR_READ_APP_VERSION = 5
OTA_ERROR_READ_PATCH_VERSION = 6
#OTA_FILE_APP_VERSION = 7
OTA_SET_OTA_MODE = 8
OTA_ERROR_SET_TO_OTA_MODE = 9
OTA_SCAN_OTA_DEVICE = 10
OTA_ERROR_SCAN_FAILED = 11
OTA_ERROR_NOT_FOUND_OTA_DEVICE = 12
OTA_CONNECT_OTA_DEVICE = 13
OTA_ERROR_CONNECT_TIMEOUT = 14
OTA_START_OTA_SERVICE_DISCOVERY = 15
OTA_ERROR_OTA_SERVICE_DISCOVERY = 16
OTA_ENABLE_NOTIFICATION = 17
OTA_ERROR_ENABLE_NOTIFICATION = 18
OTA_UPDATE_CONNECTION_PARAMS = 19
OTA_ERROR_UPDATE_CONNECTION_PARAMS = 20
OTA_GET_IMAGE_INFO = 21
OTA_ERROR_GET_IMAGE_INFO = 22
OTA_START_DFU = 23
OTA_ERROR_START_DFU = 24
OTA_RECEIVE_FIRMWARE_INFO = 25
OTA_ERROR_RECEIVE_FIRMWARE_INFO = 26
OTA_START_UPDATE_DATA = 27
OTA_PROGRESS_DATA = 28
OTA_ERROR_UPDATE_DATA = 29
OTA_VALIDATE_FIRMWARE = 30
OTA_ERROR_VALIDATE_FIRMWARE = 31
OTA_RCU_RESET = 32
OTA_RCU_DONE = 33
OTA_RCU_DISCONNECTED = 35
OTA_INVALID_FIRMWARE = 36

g_ota_event_description = {}
g_ota_event_description[OTA_ERROR_SERVICE_DISCOVERY] = "Service discovery failed."
g_ota_event_description[OTA_BATTERY_LEVEL] = "Reading battery level"
g_ota_event_description[OTA_PATCH_VERSION] = "Reading patch version"
g_ota_event_description[OTA_ERROR_READ_BATTERY_LEVEL] = "Can not read battery level."
g_ota_event_description[OTA_ERROR_READ_APP_VERSION] = "Can not read app version."
g_ota_event_description[OTA_ERROR_READ_PATCH_VERSION] = "Can not read patch version."
g_ota_event_description[OTA_SET_OTA_MODE] = "Switching RCU to OTA mode."
g_ota_event_description[OTA_ERROR_SET_TO_OTA_MODE] = "failed to set up RCU into OTA mode."
g_ota_event_description[OTA_SCAN_OTA_DEVICE] = "Scanning OTA device."
g_ota_event_description[OTA_ERROR_SCAN_FAILED] = "failed to scan OTA device."
g_ota_event_description[OTA_ERROR_NOT_FOUND_OTA_DEVICE] = "Can not find OTA device."
g_ota_event_description[OTA_CONNECT_OTA_DEVICE] = "Connecting to OTA device."
g_ota_event_description[OTA_ERROR_CONNECT_TIMEOUT] = "Timeout Connecting to OTA device."
g_ota_event_description[OTA_START_OTA_SERVICE_DISCOVERY] = "Starting OTA service discovery."
g_ota_event_description[OTA_ERROR_OTA_SERVICE_DISCOVERY] = "Service discovery failed on OTA mode."
g_ota_event_description[OTA_ENABLE_NOTIFICATION] = "Enable notification."
g_ota_event_description[OTA_ERROR_ENABLE_NOTIFICATION] = "failed to enable notification."
g_ota_event_description[OTA_UPDATE_CONNECTION_PARAMS] = "Updating connection parameters."
g_ota_event_description[OTA_ERROR_UPDATE_CONNECTION_PARAMS] = "failed to update connection parameters."
g_ota_event_description[OTA_GET_IMAGE_INFO] = "Getting RCU firmware info."
g_ota_event_description[OTA_ERROR_GET_IMAGE_INFO] = "failed to get RCU firmware info."
g_ota_event_description[OTA_START_DFU] = "Starting DFU."
g_ota_event_description[OTA_ERROR_START_DFU] = "failed to start DFU."
g_ota_event_description[OTA_RECEIVE_FIRMWARE_INFO] = "Getting firmware info with DFU."
g_ota_event_description[OTA_ERROR_RECEIVE_FIRMWARE_INFO] = "failed to get firmware info with DFU."
g_ota_event_description[OTA_START_UPDATE_DATA] = "Starting to transfer data."
g_ota_event_description[OTA_PROGRESS_DATA] = "OTA_PROGRESS_DATA"
g_ota_event_description[OTA_ERROR_UPDATE_DATA] = "Failed to transfer data."
g_ota_event_description[OTA_VALIDATE_FIRMWARE] = "Validating firmware."
g_ota_event_description[OTA_ERROR_VALIDATE_FIRMWARE] = "Failed to validate firmware."
g_ota_event_description[OTA_RCU_RESET] = "Resetting RCU."
g_ota_event_description[OTA_RCU_DONE] = "OTA Completed."
g_ota_event_description[OTA_RCU_DISCONNECTED] = "RCU disconnected."
g_ota_event_description[OTA_INVALID_FIRMWARE] = "invalid firmware"

class VuRcuOtaUpdate(Screen, HelpableScreen, BluetoothTask):
	skin = """
		<screen position="center,center" size="660,280" title="VU RCU OTA Update">
			<widget name="battery_check" position="30,20" size="600,40" font="Regular;28" halign="left" valign="center" />
			<widget name="app_version" position="30,60" size="600,40" font="Regular;28" halign="left" valign="center" />
			<widget name="new_app_version" position="30,100" size="600,40" font="Regular;28" halign="left" valign="center" />
			<widget name="text" position="30,140" size="600,90" font="Regular;26" halign="center" valign="center" />
			<widget name="progress" position="30,230" size="600,25" borderWidth="2" borderColor="uncccccc" />
		</screen>
		"""

	def __init__(self, session, mac, vubt_insttance, battery, app_version, new_app_version):
		BluetoothTask.__init__(self)
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self.session = session
		self.rcu_mac = mac
		self.vubt = vubt_insttance

		self.text = _("Starting...")

		self.batteryLevel = battery
		self.appVersion = app_version
		self.newAppVersion = new_app_version

		self["progress"] = ProgressBar()

		batteryLevelDesc = self.batteryLevel < bt_types.BT_BATTERY_LEVEL_OTA_TH and "Not enough" or "Good"
		self["battery_check"] = Label(_("Battery level for OTA : %s") % batteryLevelDesc)
		self["app_version"] = Label(_("Current FW version : %d") % self.appVersion)
		self["new_app_version"] = Label(_("New FW version : %d") % self.newAppVersion)

		self["text"] = Label(self.text)

		self["WizardActions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.exit,
			"back": self.exit,
			"red": self.exit,
		}, -2)

		self.otaInitTimer = eTimer()
		self.otaInitTimer.callback.append(self.otaInit)

		self.rcuRebootTimer = eTimer()
		self.rcuRebootTimer.callback.append(self.rcuRebootCB)

		self.onLayoutFinish.append(self.onLayoutFinished)
		self.onClose.append(self.onCloseCB)

		self.startUpdate = False

		self.eventTimer = eTimer()
		self.eventTimer.callback.append(self.handleEvents)
		self.events = []

		self.audio_connected = None

	def otaInit(self):
		self.appendEventCallback(True)
		self.appendOTAEventCallback(True)
		self.vubt.OTAInit()
		self.disconnectDevices()
		self.addTaskOTAStart()

	def onLayoutFinished(self):
		if self.batteryLevel < bt_types.BT_BATTERY_LEVEL_OTA_TH:
			self["text"].setText(_("Not enough battery level for OTA update.\nPress exit and change battery of VUPLUS-BLE-RCU."))
		else:
			self.otaInitTimer.start(100, True)

	def onCloseCB(self):
		self.vubt.OTADeInit()
		#if self.audio_connected:
		#	self.vubt.requestConnect(self.audio_connected['bd_addr'])

		self.appendOTAEventCallback(False)
		self.appendEventCallback(False)

	def appendOTAEventCallback(self, value=True):
		if value:
			if self.otaEventCallback not in self.vubt.pluginOtaEventHandler:
				self.vubt.pluginOtaEventHandler.append(self.otaEventCallback)
		else:
			if self.otaEventCallback in self.vubt.pluginOtaEventHandler:
				self.vubt.pluginOtaEventHandler.remove(self.otaEventCallback)

	def otaEventCallback(self, event, value):
		print("[VuRcuOtaUpdate][otaEventCallback] event : ", event)
		print("[VuRcuOtaUpdate][otaEventCallback] value : ", value)

		if event == OTA_PROGRESS_DATA: # OTA_PROGRESS_DATA
			self["text"].setText(_("Updateing %d %%") % value)
			self["progress"].setValue(value)
		elif event == OTA_RCU_DONE:
			text = "Wait 5 seconds while VUPLUS-BLE-RCU is rebooting..."
			self["text"].setText("%s" % text)
			self.rcuRebootTimer.start(5000, True)
		elif event == OTA_RCU_DISCONNECTED:
			self.exit_text = _("OTA Failed.\n%s is disconnected.") % bt_types.BT_VUPLUS_RCU_NAME
			self.exit_text += " Press exit."
			self["text"].setText("%s" % self.exit_text) 
		else:
			if event in g_ota_event_description:
				self["text"].setText(_("%s") % g_ota_event_description[event])
			else:
				self["text"].setText(_("%d event") % event)

	def rcuRebootCB(self):
		self.exit_text = _(g_ota_event_description[OTA_RCU_DONE])
		self.exit_text += "\nPress OK to exit."
		self["text"].setText("%s" % self.exit_text)

	def exit(self):
		self.close()

	def disconnectDevices(self):
		pairedDevices = self.vubt.getPairedDevice()

		print("pairedDevices : ", pairedDevices)

		if pairedDevices:
			for (k, v) in list(pairedDevices.items()):
				mac = v['bd_addr']
				name = v['name']
				profile = v["profile"]
				connected = v['isConnected']
				if (name != bt_types.BT_VUPLUS_RCU_NAME) and connected:
					self.addTaskDisconnect(mac, profile, name)

	def disconnectDevice(self, args):
		(mac, profile, name) = args

		res = self.vubt.requestDisconnect(mac, profile)
		if res:
			self["text"].setText(_("disconnecting %s") % name)
		else:
			self["text"].setText(_("disconnect to %s failed!!") % name)

		return res

	def addTaskDisconnect(self, mac, profile, name):
		args = (mac, profile, name)
		eventCB = {bt_types.BT_EVENT_LINK_DOWN : None}
		self.addTask(BluetoothTask.TASK_DISCONNECT, self.disconnectDevice, mac, args, eventCB)

	def addTaskOTAStart(self):
		self.addTask(BluetoothTask.TASK_CALL_FUNC, self.OTAStart, None, None, None)

	def OTAStart(self):
		self.startUpdate = True
		self["text"].setText(_("Starting..."))
		self.vubt.OTAStart()

	def __repr__(self):
		return str(type(self)) + "(" + self.text + ")"

	def appendEventCallback(self, value=True):
		if value:
			if self.eventCallback not in self.vubt.pluginEventHandler:
				self.vubt.pluginEventHandler.append(self.eventCallback)
		else:
			if self.eventCallback in self.vubt.pluginEventHandler:
				self.vubt.pluginEventHandler.remove(self.eventCallback)

	def eventCallback(self, event, _data):
		print("[VuRcuOtaUpdate][eventCallback] event : %s" % (getEventDesc(event)))
		print("[VuRcuOtaUpdate][eventCallback] data : ", _data)

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
		if event == bt_types.BT_EVENT_DISCONNECTED:
			self["text"].setText(_("%s is disconnected.") % name)

		BluetoothTask.handleEvent(self, event, name, data)

		if self.events:
			self.eventTimer.start(10, True)


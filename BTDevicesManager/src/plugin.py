#====================================================
# Bluetooth Devices Manager - basic version
# Version date - 20.11.2014
# Coding by a4tech - darezik@gmail.com (oe-alliance)
# Refactor by jbleyel (c) 2025
#
# requierments: bluez4-testtools bluez4 bluez-hcidump
# Some Kernel modules for support HID devices
#
# For example:
# kernel-module-hid-a4tech
# kernel-module-hid-apple
# kernel-module-hid-appleir
# kernel-module-hid-belkin
# kernel-module-hid-magicmouse
# kernel-module-hid-microsoft
# kernel-module-hid-wacom
#====================================================
from configparser import ConfigParser
from datetime import datetime, timedelta
from os import kill, listdir, system
from os.path import join, isdir, isfile
from signal import SIGUSR2
from twisted.internet.reactor import callInThread

from enigma import eTimer, iPlayableService

from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.config import config, ConfigText, ConfigSubsection, ConfigYesNo
from Components.MenuList import MenuList
from Components.ServiceEventTracker import ServiceEventTracker
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.Setup import Setup
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN, fileCheck
from .bluetoothctl import iBluetoothctl
from . import _


config.btdevicesmanager = ConfigSubsection()
config.btdevicesmanager.autostart = ConfigYesNo(default=False)
config.btdevicesmanager.audioconnect = ConfigYesNo(default=False)
config.btdevicesmanager.audioaddress = ConfigText(default="", fixed_size=False)


def applyBTAudioState():
	if not isfile("/proc/stb/audio/btaudio"):
		return

	newState = "off"
	if config.btdevicesmanager.audioaddress.value:
		newState = "on"

	config.btdevicesmanager.audioaddress.save()
	config.btdevicesmanager.audioconnect.save()
	if hasattr(config, "av") and hasattr(config.av, "btaudio"):
		config.av.btaudio.save()

	try:
		with open("/proc/stb/audio/btaudio", "w") as fn:
			fn.write(newState)
	except Exception as e:
		print(f"[BluetoothManager] Error writing btaudio: {e}")

	commandconnect = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/BTDevicesManager/BTAudioConnect")
	audioaddress = config.btdevicesmanager.audioaddress.value
	audioaddress = f" {audioaddress}" if audioaddress and config.btdevicesmanager.audioconnect.value else ""
	system(f"{commandconnect}{audioaddress}")


class BluetoothDevicesManagerSetup(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "BluetoothDevicesManager", plugin="Extensions/BTDevicesManager", PluginLanguageDomain="BTDevicesManager")


class BluetoothDevicesManager(Screen):
	skin = """
		<screen name="BluetoothDevicesManager" position="center,center" size="600,450" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="455,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
			<widget name="devicelist" position="0,50" size="600,300" foregroundColor="#ffffff" zPosition="10" scrollbarMode="showOnDemand" transparent="1"/>
			<widget name="ConnStatus" position="0,330" size="600,150" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Bluetooth Devices Manager"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
			"ok": self.keyYellow,
			"cancel": self.close,
			"red": self.close,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
		}, -1)

		self["audioActions"] = ActionMap(["ColorActions", "MenuActions"], {
			"blue": self.keyBlue,
			"menu": self.keyMenu
		}, -1)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Scan"))
		self["key_yellow"] = StaticText(_("Connect"))
		self["key_blue"] = StaticText("")
		self["ConnStatus"] = Label(_("Not connected to any device"))

		self.devicelist = []
		self["devicelist"] = MenuList(self.devicelist)
		self["devicelist"].onSelectionChanged.append(self.selectionChanged)

		self.refreshStatusTimer = eTimer()
		self.refreshStatusTimer.callback.append(self.cbRefreshStatus)
		self.refreshScanedTimer = eTimer()
		self.refreshScanedTimer.callback.append(self.cbRefreshScanStatus)

		self.cb_mac_address = None
		self.cb_name = None
		self.hasBTAudio = isfile("/proc/stb/audio/btaudio")
		self["audioActions"].setEnabled(self.hasBTAudio)
		self.rootDir = "/var/lib/bluetooth"
		self.controlerPath = None
		if isdir(self.rootDir):
			for controlerdir in listdir(self.rootDir):
				controlerPath = join(self.rootDir, controlerdir)
				if isdir(controlerPath):
					self.controlerPath = controlerPath

		if self.controlerPath:
			self.readDeviceList()

	def close(self):
		self.refreshStatusTimer.stop()
		self.refreshScanedTimer.stop()
		iBluetoothctl.stop_scan()
		Screen.close(self)

	def getDeviceInfo(self, macAddress):
		isAudio = False
		infoFile = join(self.controlerPath, macAddress, "info") if macAddress else None
		if infoFile and isfile(infoFile):
			configFile = ConfigParser()
			configFile.read(infoFile)
			if "General" in configFile and "Services" in configFile["General"]:
				isAudio = "0000110e-0000-1000-8000-00805f9b34fb" in configFile["General"]["Services"]
				#isKeyboard = "00001000-0000-1000-8000-00805f9b34fb" in configFile["General"]["Services"]
		return isAudio

	def readDeviceList(self):
		self.devicelist = []
		if self.controlerPath:
			for devicedir in listdir(self.controlerPath):
				devicePath = join(self.controlerPath, devicedir)
				if devicedir != "cache" and isdir(devicePath):
					infoFile = join(devicePath, "info")
					if isfile(infoFile):
						configFile = ConfigParser()
						configFile.read(infoFile)
						if "General" in configFile and "Name" in configFile["General"] and "Trusted" in configFile["General"]:
							name = configFile["General"]["Name"]
							trusted = configFile["General"]["Trusted"] == "true"
							connectedStr = _('Connected') if trusted else _('Not connected')
							isAudio = self.hasBTAudio and "Services" in configFile["General"] and "0000110e-0000-1000-8000-00805f9b34fb" in configFile["General"]["Services"]
							if self.hasBTAudio and trusted:
								connectedStr += " / "
								connectedStr += "Audio" if isAudio else "HID"
							self.devicelist.append((f"{name} / {connectedStr}", devicedir, name, trusted, isAudio))

		if self.devicelist:
			self["ConnStatus"].setText("")
		else:
			self["ConnStatus"].setText(_("No connected to any device"))
		self["devicelist"].setList(self.devicelist)
		self.selectionChanged()

	def selectionChanged(self):
		if self["devicelist"].list:
			self["key_blue"].setText("")
			current = self["devicelist"].getCurrent()
			if current[1]:
				self["key_yellow"].setText(_("Disconnect") if current[3] else _("Connect"))
				if self.hasBTAudio and current[3] and current[4]:
					self["key_blue"].setText(_("Audio Off") if config.btdevicesmanager.audioaddress.value == current[1] else _("Audio On"))
			else:
				self["key_yellow"].setText("")

	def keyGreen(self):
		self.scanForDevices()

	def scanForDevices(self):
		self.devicelist = []
		self.devicelist.append((_("Scanning for devices..."), ""))
		self["devicelist"].setList(self.devicelist)
		self.refreshScanedTimer.start(5000, False)
		iBluetoothctl.start_scan()

	def cbRefreshStatus(self):
		self.refreshStatusTimer.stop()
		mac_address = self.cb_mac_address
		name = self.cb_name
		msg = _("Can't not pair with selected device!")
		try:
			ret = iBluetoothctl.connect(mac_address)
			if ret is False:
				self["ConnStatus"].setText(msg)
			else:
				iBluetoothctl.trust(mac_address)
				msg = _("Connection with:\n") + name
				self["key_yellow"].setText(_("Disconnect"))
		except Exception as e:
			print(f"[BluetoothManager] Error cbRefreshStatus: {name} / {mac_address} / {e}")
			self["ConnStatus"].setText(msg)

	def cbRefreshScanStatus(self):
		available_devices = [(x["mac_address"], x["name"]) for x in iBluetoothctl.get_available_devices()]
		paired_devices = [(x["mac_address"], x["name"]) for x in iBluetoothctl.get_paired_devices()]
		paired_devices_mac = [x[0] for x in paired_devices]
		devicelist = []

		if available_devices:
			for d in available_devices:
				if d[0] != d[1].replace("-", ":"):  # show only devices with name != mac address
					connected = d[0] in paired_devices_mac
					connectedStr = _("Connected") if connected else _("Not connected")
					isAudio = self.hasBTAudio and self.getDeviceInfo(d[0])
					if self.hasBTAudio and connected:
						connectedStr += " / "
						connectedStr += "Audio" if isAudio else "HID"
					devicelist.append((f"{d[1]} / {connectedStr}", d[0], d[1], connected, isAudio))

		if devicelist != self.devicelist:
			self.devicelist = devicelist
			self["devicelist"].setList(self.devicelist)

	def _disconnect(self, mac_address, name):
		try:
			iBluetoothctl.remove(mac_address)
		except Exception as e:
			print(f"[BluetoothManager] Error Remove: {name} / {mac_address} / {e}")
			pass
		try:
			iBluetoothctl.disconnect(mac_address)
		except Exception as e:
			print(f"[BluetoothManager] Error Disconnect: {name} / {mac_address} / {e}")
			pass
		self.refreshScanedTimer.start(1000, True)
		msg = _("Disconnect with:\n") + name
		self["ConnStatus"].setText(msg)
		self["key_yellow"].setText(_("Connect"))

	def _connect(self, mac_address, name):
		try:
			ret = iBluetoothctl.pair(mac_address)
		except Exception as e:
			print(f"[BluetoothManager] Error Pair: {name} / {mac_address} / {e}")
			ret = False
		if ret is False:
			print(f"[BluetoothManager] can NOT connect with: {name} / {mac_address}")
			msg = _("Can't not pair with selected device!")
			self["ConnStatus"].setText(msg)
			if iBluetoothctl.passkey is not None:
				self.cb_mac_address = mac_address
				self.cb_name = name
				msg = _("Please Enter Passkey: \n") + iBluetoothctl.passkey
				self["ConnStatus"].setText(msg)
				self.refreshStatusTimer.start(5000, True)
				return
		iBluetoothctl.trust(mac_address)
		ret = iBluetoothctl.connect(mac_address)
		if ret:
			msg = _("Connection with:\n") + name
			self["ConnStatus"].setText(msg)
			self["key_yellow"].setText(_("Disconnect"))
			return
		print(f"[BluetoothManager] can NOT connect with: {name} / {mac_address}")
		msg = _("Can't not pair with selected device!")
		self["ConnStatus"].setText(msg)

	def keyYellow(self):
		if self["devicelist"].list:
			current = self["devicelist"].getCurrent()
			if current[1]:
				if current[3]:
					self.refreshScanedTimer.stop()
					self["ConnStatus"].setText(_("Disconnecting please wait..."))
					callInThread(self._disconnect, current[1], current[2])
				else:
					print(f"[BluetoothManager] trying to pair with: {current[2]}")
					msg = _("Trying to pair with:") + " " + current[2]
					self["ConnStatus"].setText(msg)
					self._connect(current[1], current[2])

	def keyBlue(self):
		if self.hasBTAudio and self["devicelist"].list:
			current = self["devicelist"].getCurrent()
			isAudio = self.getDeviceInfo(current[1])
			if current[3] and isAudio:
				if config.btdevicesmanager.audioaddress.value == current[1]:
					config.btdevicesmanager.audioaddress.value = ""
					config.btdevicesmanager.audioconnect.value = False
					config.av.btaudio.value = True
				else:
					config.btdevicesmanager.audioaddress.value = current[1]
					config.btdevicesmanager.audioconnect.value = True
					config.av.btaudio.value = False
				applyBTAudioState()
				self.selectionChanged()

	def keyMenu(self):
		if self.hasBTAudio:
			def setupCallback(*args):
				applyBTAudioState()
			self.session.openWithCallback(setupCallback, BluetoothDevicesManagerSetup)

	def setListOnView(self):
		return self.devicelist


def main(session, **kwargs):
	session.open(BluetoothDevicesManager)


iBluetoothDevicesTask = None


class BluetoothDevicesTask:
	def __init__(self, session):
		self.session = session
		self.onClose = []
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.__evStart,
			})
		self.timestamp = datetime.now()
		self.check_timer = eTimer()
		self.check_timer.callback.append(self.poll)
		self.check_timer.start(3600000)

	def __evStart(self):
		curr_time = datetime.now()
		next_time = self.timestamp + timedelta(hours=3)
		if curr_time > next_time:
			self.flush()

	def poll(self):
		curr_time = datetime.now()
		next_time = self.timestamp + timedelta(hours=6)
		if curr_time > next_time:
			self.flush()

	def flush(self):
		try:
			pid = open("/var/run/aplay.pid").read().split()[0]
			kill(int(pid), SIGUSR2)
		except Exception:
			pass
		self.timestamp = datetime.now()


def sessionstart(session, reason, **kwargs):
	global iBluetoothDevicesTask
	if reason == 0:
		if isfile("/proc/stb/audio/btaudio"):
			applyBTAudioState()
			if iBluetoothDevicesTask is None:
				iBluetoothDevicesTask = BluetoothDevicesTask(session)


def Plugins(**kwargs):
	if fileCheck("/sys/class/bluetooth/hci0"):
		return [
			PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
			PluginDescriptor(name=_("Bluetooth Devices Manager"), description=_("This is bt devices manager"), icon="plugin.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
		]
	else:
		return []

#====================================================
# Bluetooth Devices Manager - basic version
# Version date - 20.11.2014
# Coding by a4tech - darezik@gmail.com (oe-alliance)
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

from . import _
from boxbranding import getImageDistro, getBrandOEM, getMachineBuild, getBoxType

from Plugins.Plugin import PluginDescriptor
from enigma import eTimer, eConsoleAppContainer

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.Button import Button
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.config import config, ConfigSelection, getConfigListEntry, ConfigText, ConfigSubsection, ConfigYesNo, ConfigSelection
from Components.MenuList import MenuList
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN, fileExists
from bluetoothctl import iBluetoothctl, Bluetoothctl

import os
import time

brandoem = getBrandOEM()

class TaskManager:
	def __init__(self):
		self.taskIdx = 0
		self.taskList = []
		self.gTaskInstance = None
		self.occurError = False
		self.cbSetStatusCB = None

	def append(self, command, cbDataFunc, cbCloseFunc):
		self.taskList.append([command+'\n', cbDataFunc, cbCloseFunc])

	def dump(self):
		print "############### TASK ###############"
		print "Current Task Index :", self.taskIdx
		print "Current Task Instance :", self.gTaskInstance
		print "Occur Error :", self.occurError
		print "Task List:\n", self.taskList
		print "####################################"

	def error(self):
		print "[BluetoothManager] Info >> set task error!!"
		self.occurError = True

	def reset(self):
		self.taskIdx = 0
		self.gTaskInstance = None
		self.occurError = False

	def clean(self):
		self.reset()
		self.taskList = []
		self.cbSetStatusCB = None
		print "clear task!!"

	def index(self):
		self.taskIdx

	def setStatusCB(self, cbfunc):
		self.cbSetStatusCB = cbfunc

	def next(self):
		if self.taskIdx >= len(self.taskList) or self.occurError:
			print "[BluetoothManager] Info >> can't run task!!"
			return False
		command     = self.taskList[self.taskIdx][0]
		cbDataFunc  = self.taskList[self.taskIdx][1]
		cbCloseFunc = self.taskList[self.taskIdx][2]

		self.gTaskInstance = eConsoleAppContainer()
		if cbDataFunc is not None:
			self.gTaskInstance.dataAvail.append(cbDataFunc)
		if cbCloseFunc is not None:
			self.gTaskInstance.appClosed.append(cbCloseFunc)
		if self.cbSetStatusCB is not None:
			self.cbSetStatusCB(self.taskIdx)

		print "[BluetoothManager] Info >> prepared command : %s"%(command)
		self.gTaskInstance.execute(command)
		self.taskIdx += 1
		return True

config.btdevicesmanager = ConfigSubsection()
config.btdevicesmanager.autostart = ConfigYesNo(default=False)
config.btdevicesmanager.audioconnect = ConfigYesNo(default=False)
config.btdevicesmanager.audioaddress = ConfigText(default = "", fixed_size = False)

commandconnect = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/BTDevicesManager/BTAudioConnect")

class BluetoothDevicesManagerSetup(ConfigListScreen, Screen):
	__module__ = __name__
	def __init__(self, session, args = 0):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Bluetooth Devices Manager Setup"))
		self.skinName = ["Setup"]
			
		list = []
		list.append(getConfigListEntry(_('Autostart'), config.btdevicesmanager.autostart))
		list.append(getConfigListEntry(_('Audio Connect'), config.btdevicesmanager.audioconnect))
		list.append(getConfigListEntry(_('Audio Address'), config.btdevicesmanager.audioaddress))

		self["key_red"] = Label(_("Exit"))
		self["key_green"] = Label(_("Save"))
			
		ConfigListScreen.__init__(self, list)
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], 
		{
			'red' : self.dontSaveAndExit,  
			'green': self.saveAndExit, 
			'cancel': self.dontSaveAndExit
		}, -1)

	def saveAndExit(self):
		for x in self['config'].list:
			x[1].save()

		if brandoem not in ("xcore","edision"):
			if config.btdevicesmanager.autostart.getValue():
				print "[BluetoothManager] Autostart: Loading driver"
				os.system("modprobe rtk_btusb")
			else:
				print "[BluetoothManager] Autostart: Unloading driver"
				os.system("rmmod rtk_btusb")

		if brandoem in ("xcore","edision"):
			if config.btdevicesmanager.audioconnect.getValue():
				os.system("%s %s" % (commandconnect, config.btdevicesmanager.audioaddress.getValue()))
			else:
				os.system("%s" % commandconnect)

		config.btdevicesmanager.save()
		
		self.close()

	def dontSaveAndExit(self):
		for x in self['config'].list:
		    x[1].cancel()

		self.close()
		
class BluetoothDevicesManager(Screen):
	skin = 	"""
		<screen name="BluetoothDevicesManager" position="center,center" size="600,450" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,0" size="140,40" alphatest="on" />

			<widget name="key_red" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget name="key_green" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget name="key_yellow" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="key_blue" position="455,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />

			<widget name="devicelist" position="0,50" size="600,300" foregroundColor="#ffffff" zPosition="10" scrollbarMode="showOnDemand" transparent="1"/>
			<widget name="ConnStatus" position="0,330" size="600,150" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
	        </screen>
		"""
	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Bluetooth Devices Manager"))

		self.taskManager = TaskManager()

		self["actions"]  = ActionMap(["OkCancelActions","WizardActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"red"   : self.keyCancel,
			"green" : self.keyGreen,
			"yellow": self.keyYellow,
			"blue"  : self.keyBlue,
		}, -1)

		self["key_red"]    = Label(_("Exit"))
		self["key_green"]  = Label(_("(Re)Scan"))
		self["key_yellow"] = Label(_("Connect"))
		self["key_blue"]   = Label(_("Config"))

		self["ConnStatus"] = Label(_("No connected to any device"))
    
		self.devicelist = []
		self["devicelist"] = MenuList(self.devicelist)

		if config.btdevicesmanager.autostart.getValue():
			self.initDevice()
		if brandoem in ("xcore","edision"):
			self.initDevice()
			self.showConnections()

		self.refreshStatusTimer = eTimer()
		self.refreshStatusTimer.callback.append(self.cbRefreshStatus)
		self.cb_mac_address = None
		self.cb_name = None

	def initDevice(self):
		print "[BluetoothManager] initDevice"
		cmd = "hciconfig hci0 up"
		self.taskManager.append(cmd, self.cbPrintAvailBTDev, self.cbRunNextTask)
		cmd = "hcitool dev" ## check if hci0 is on the dev list, then make scan
		self.taskManager.append(cmd, self.cbPrintAvailBTDev, self.cbStopDone)
		self.taskManager.next()
		
	def cbPrintAvailBTDev(self, data):
		print "[BluetoothManager] cbPrintAvailBTDev"
		if data in ("Device is not available: No such device\n", "Devices:\n"): ## This message hidd return while it can not find bt dev
			msg = _("No BT devices found!")
			self["ConnStatus"].setText(_(msg))
		else:
			self.scanForDevices()
			
	def keyGreen(self):
		print "[BluetoothManager] keyGreen"  
		if config.btdevicesmanager.autostart.getValue() or brandoem in ("xcore","edision"):
			self["ConnStatus"].setText(_("No connected to any device"))
			self.initDevice()
		else:
			self["devicelist"].setList([])
			self["ConnStatus"].setText(_("Please load BT driver by pressing BLUE button."))
	  
	def scanForDevices(self):  
		print "[BluetoothManager] scanForDevices"
		# lets clear the list before Rescanning
		self.devicelist = []
		self.devicelist.append((_("Scanning for devices..."), _("Scanning...")))
		self["devicelist"].setList(self.devicelist)
		
		# add background task for scanning
		cmd = 'hcitool scan'
		self.taskManager.append(cmd, self.cbPrintAvailDevices, self.cbRunNextTask)
		self.taskManager.next()

	def cbPrintAvailDevices(self, data):
		print "[BluetoothManager] cbPrintAvailDevices"
		
		self.devicelist = []
		self.devicelist.append((_("MAC:\t\tDevice name:"),_("entry")))
		
		data = data.splitlines()
		i = 1
		for x in data:
			y = x.split("\t")
			if not y[0] == "Scanning ...": ## We do not need to put this to the list
			        i += 1
				self.devicelist.append((y[1] + "\t" + y[2],y[1]))
		
		if i == 1: ## Not sure if it is good idea, but worth to inform user that BT can not detect any other devices
			self.devicelist = []
			self.devicelist.append((_("MAC:\t\tDevice name:"),_("entry")))
			self["ConnStatus"].setText(_("Not detected devices around STB"))
			
		self["devicelist"].setList(self.devicelist)
		self.showConnections()
		
	def showConnections(self):
		print "[BluetoothManager] showConnections"
		if brandoem not in ("xcore","edision"):
			cmd = "hidd --show"
			self.taskManager.append(cmd, self.cbPrintCurrentConnections, self.cbStopDone)
			self.taskManager.next()
		else:
			paired_devices = iBluetoothctl.get_paired_devices()
			if paired_devices is not None:
				for d in paired_devices:
					if d is not None:
						mac_address = d['mac_address']
						name = d['name']
						msg = _("Connection with:\n") + name + " (" + mac_address + ")"
						self["ConnStatus"].setText(msg)
						self["key_yellow"].setText(_("Disconnect"))
			else:
				self["ConnStatus"].setText(_("No connected to any device"))
			
	def cbPrintCurrentConnections(self, data):
		print "[BluetoothManager] cbPrintCurrentConnections"
		msg = _("Connection with:\n") + data[:-12]
		self["ConnStatus"].setText(msg)
		self["key_yellow"].setText(_("Disconnect"))
		
	def cbRefreshStatus(self):
		self.refreshStatusTimer.stop()
		mac_address = self.cb_mac_address
		name = self.cb_name
		try:
			ret = iBluetoothctl.connect(mac_address)
			if ret is False:
				msg = _("Can't not pair with selected device!")
				self["ConnStatus"].setText(msg)
			else:
				iBluetoothctl.trust(mac_address)
				msg = _("Connection with:\n") + name + " (" + mac_address + ")"
				self["ConnStatus"].setText(msg)
				self["key_yellow"].setText(_("Disconnect"))
		except:
			msg = _("Can't not pair with selected device!")
			self["ConnStatus"].setText(msg)

	def keyYellow(self):
		if self["key_yellow"].getText() == _('Disconnect'):
			print "[BluetoothManager] Disconnecting"
			if brandoem not in ("xcore","edision"):
				cmd = "hidd --killall"
				rc = os.system(cmd)
				if not rc:
					self["ConnStatus"].setText(_("No connected to any device"))
					self["key_yellow"].setText(_("Connect"))
				self.showConnections()
			else:
				paired_devices = iBluetoothctl.get_paired_devices()
				if paired_devices is not None:
					for d in paired_devices:
						if d is not None:
							mac_address = d['mac_address']
							name = d['name']
							try:
								iBluetoothctl.remove(mac_address)
							except:
								pass
							try:
								iBluetoothctl.disconnect(mac_address)
							except:
								pass
							msg = _("Disconnect with:\n") + name + " (" + mac_address + ")"
							self["ConnStatus"].setText(msg)
							self["key_yellow"].setText(_("Connect"))
		else:
			print "[BluetoothManager] Connecting"
			selectedItem = self["devicelist"].getCurrent()
			if selectedItem is None or selectedItem[0] == "Scanning for devices...": ## If list is empty somehow or somebody pressed button while scanning
				return
			      
			print "[BluetoothManager] trying to pair with: ", selectedItem[1]
			msg = _("Trying to pair with:") + " " + selectedItem[1]
			self["ConnStatus"].setText(msg)
			
			if brandoem not in ("xcore","edision"):
				cmd = "hidd --connect " + selectedItem[1]
				self.taskManager.append(cmd, self.cbPrintAvailConnections, self.cbRunNextTask)
				cmd = "hidd --show"
				rc = os.system(cmd)
				if rc:
					print "[BluetoothManager] can NOT connect with: ", selectedItem[1]
					msg = _("Can't not pair with selected device!")
					self["ConnStatus"].setText(msg)
				self.taskManager.append(cmd, self.cbPrintCurrentConnections, self.cbStopDone)
				self.taskManager.next()
			else:
				mac_address = None
				name = None
				iBluetoothctl.pairable_on()
				iBluetoothctl.start_scan()
				for i in range(0, 20):
					time.sleep(0.5)
					available_devices = iBluetoothctl.get_available_devices()
					if available_devices is not None:
						for d in available_devices:
							if selectedItem[1] in str(d):
								mac_address = d['mac_address']
								name = d['name']
					if mac_address is not None:
						break

				if mac_address is not None:
					iBluetoothctl.agent_noinputnooutput()
					iBluetoothctl.default_agent()
					ret = iBluetoothctl.pair(mac_address)
					if config.btdevicesmanager.audioaddress.getValue() is "":
						config.btdevicesmanager.audioaddress.setValue(mac_address)
					if ret is False:
						if iBluetoothctl.passkey is not None:
							self.cb_mac_address = mac_address
							self.cb_name = name
							msg = _("Please Enter Passkey: \n") + iBluetoothctl.passkey
							self["ConnStatus"].setText(msg)
							self.refreshStatusTimer.start(10000, True)
					else:
						iBluetoothctl.trust(mac_address)
						ret = iBluetoothctl.connect(mac_address)
						msg = _("Connection with:\n") + name + " (" + mac_address + ")"
						self["ConnStatus"].setText(msg)
						self["key_yellow"].setText(_("Disconnect"))
				else:
					print "[BluetoothManager] can NOT connect with: ", selectedItem[1]
					msg = _("Can't not pair with selected device!")
					self["ConnStatus"].setText(msg)

	def cbPrintAvailConnections(self, data):
		print "[BluetoothManager] cbPrintAvailConnections"
		if data == "Can't get device information: Success\n": ## This message hidd return while it can not connect with device
			print "[BluetoothManager] connection faild"
			msg = _("Can't not pair with selected device!")
			self["ConnStatus"].setText(msg)
			
	def keyBlue(self):
		print "[BluetoothManager] keyBlue"
		self.session.openWithCallback(self.keyGreen, BluetoothDevicesManagerSetup)

	def showMessage(self,msg):
		self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, 3)

	def keyCancel(self):
		print "[BluetoothManager] keyCancel"
		self.close()

	def keyOK(self):
		print "[BluetoothManager] keyOK"
		self.keyYellow()

	def cbRunNextTask(self, ret):
		self.taskManager.next()
		
	def cbStopDone(self, ret):
		print "[BluetoothManager] cbStopDone"
		self.taskManager.clean()

	def setListOnView(self):
		return self.devicelist

def start_menu_main(menuid, **kwargs):
	if menuid == "system":
		return [(_("Bluetooth Devices Manager"), main, "bt_control", None)]
	else:
		return []
		      
def main(session, **kwargs):
	session.open(BluetoothDevicesManager)

def autostart(reason, **kwargs):
	if reason == 0:
		if brandoem not in ("xcore","edision"):
			if config.btdevicesmanager.autostart.getValue():
				print "[BluetoothManager] Autostart: Loading driver" ## We have it on a blacklist because We want to have faster system loading, so We load driver while we enable it.
				os.system("modprobe rtk_btusb")
			else:
				print "[BluetoothManager] Autostart: Unloading driver" ## We know it is blacklisted, but try to remove it anyway.
				os.system("rmmod rtk_btusb")

		if brandoem in ("xcore","edision"):
			if config.btdevicesmanager.audioconnect.getValue():
				os.system("%s %s" % (commandconnect, config.btdevicesmanager.audioaddress.getValue()))

def Plugins(**kwargs):
	ShowPlugin = True
	if getBoxType() in ("osnino"):
		if fileExists("/proc/stb/info/subtype"):
			file = open("/proc/stb/info/subtype")
			version = file.read().strip().lower()
			file.close()
			if version in ('10'):
				ShowPlugin = False

	if ShowPlugin :
		l = []
		l.append(PluginDescriptor(where = [PluginDescriptor.WHERE_AUTOSTART], fnc = autostart))
		if getImageDistro() in ("miracleboxhd", "miraclebox"):
			l.append(PluginDescriptor(name=_("Bluetooth Devices Manager"), icon="plugin.png", where=PluginDescriptor.WHERE_MENU, fnc=start_menu_main))
		else:
			l.append(PluginDescriptor(name=_("Bluetooth Devices Manager"), description = _("This is bt devices manager"), icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main))
		return l
	else:
		return []


from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen, ConfigList
from Components.config import config, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigIP, ConfigInteger
from Components.config import ConfigText, ConfigYesNo, NoSave, ConfigPassword, ConfigNothing, ConfigSequence
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from math import pow as math_pow
from Components.Network import iNetwork
from Components.PluginComponent import plugins
from Components.Console import Console
from os import path as os_path, system as os_system, listdir, makedirs, access, R_OK
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from enigma import eTimer

debug_msg_on = False
def printDebugMsg(msg):
	global debug_msg_on
	if debug_msg_on:
		print "[Wireless Access Point] ", msg

class fixedValue:
	def __init__(self, value = ""):
		self.value = value

ORIG_HOSTAPD_CONF = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/WirelessAccessPoint/hostapd.conf.orig")
HOSTAPD_CONF = "/etc/hostapd.conf"
HOSTAPD_CONF_BACK = "/etc/hostapd.conf.linuxap.back"

apModeConfig = ConfigSubsection()
apModeConfig.useap = ConfigYesNo(default = False)
apModeConfig.setupmode = ConfigSelection(default = "simple", choices = [ ("simple", "Simple"), ("advanced", "Advanced") ] )
#apModeConfig.wirelessdevice = fixedValue(value = "")
apModeConfig.branch = fixedValue(value = "br0")
apModeConfig.driver = fixedValue(value = "nl80211")
apModeConfig.wirelessmode = ConfigSelection(default = "g", choices = [ ("b", "802.11b"), ("a", "802.11a"), ("g", "802.11g") ] )
apModeConfig.channel = ConfigInteger(default = 1, limits = (1,13) )
apModeConfig.ssid = ConfigText(default = "Vuplus AP", visible_width = 50, fixed_size = False)
apModeConfig.beacon = ConfigInteger(default = 100, limits = (15,65535))
apModeConfig.rts_threshold = ConfigInteger(default = 2347, limits = (0,2347) )
apModeConfig.fragm_threshold = ConfigInteger(default = 2346, limits = (256,2346) )
apModeConfig.preamble = ConfigSelection(default = "0", choices = [ ("0", "Long"), ("1", "Short") ] )
apModeConfig.ignore_broadcast_ssid = ConfigSelection(default = "0", choices = [ ("0", _("disabled")), ("1", _("enabled")) ])

apModeConfig.encrypt = ConfigYesNo(default = False)
apModeConfig.method = ConfigSelection(default = "0", choices = [
	("0", _("WEP")), ("1", _("WPA")), ("2", _("WPA2")),("3", _("WPA/WPA2"))])
apModeConfig.wep = ConfigYesNo(default = False)
#apModeConfig.wep_default_key = ConfigSelection(default = "0", choices = [ ("0", "0"), ("1", "1"), ("2", "2"), ("3", "3") ] )
apModeConfig.wep_default_key = fixedValue(value = "0")
apModeConfig.wepType = ConfigSelection(default = "64", choices = [
	("64", _("Enable 64 bit (Input 10 hex keys)")), ("128", _("Enable 128 bit (Input 26 hex keys)"))])
apModeConfig.wep_key0 = ConfigPassword(default = "", visible_width = 50, fixed_size = False)
apModeConfig.wpa = ConfigSelection(default = "0", choices = [
	("0", _("not set")), ("1", _("WPA")), ("2", _("WPA2")),("3", _("WPA/WPA2"))])
apModeConfig.wpa_passphrase = ConfigPassword(default = "", visible_width = 50, fixed_size = False)
apModeConfig.wpagrouprekey = ConfigInteger(default = 600, limits = (0,3600))
apModeConfig.wpa_key_mgmt = fixedValue(value = "WPA-PSK")
apModeConfig.wpa_pairwise = fixedValue(value = "TKIP CCMP")
apModeConfig.rsn_pairwise = fixedValue(value = "CCMP")

apModeConfig.usedhcp = ConfigYesNo(default=False)
apModeConfig.address = ConfigIP(default = [0,0,0,0])
apModeConfig.netmask = ConfigIP(default = [255,0,0,0])
apModeConfig.gateway = ConfigIP(default = [0,0,0,0])
apModeConfig.nameserver = ConfigIP(default = [0,0,0,0])

class WirelessAccessPoint(Screen,ConfigListScreen):
	skin = """
		<screen position="center,center" size="590,450" title="Wireless Access Point" >
		<ePixmap pixmap="skin_default/buttons/red.png" position="20,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="160,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="300,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="440,0" size="140,40" alphatest="on" />

		<widget source="key_red" render="Label" position="20,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_green" render="Label" position="160,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_yellow" render="Label" position="300,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#a08500" transparent="1" />
		<widget source="key_blue" render="Label" position="440,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#18188b" transparent="1" />

		<widget name="config" zPosition="2" position="20,70" size="550,270" scrollbarMode="showOnDemand" transparent="1" />
		<widget source="current_settings" render="Label" position="10,340" size="570,20" font="Regular;19" halign="center" valign="center" transparent="1" />
		<widget source="IPAddress_text" render="Label" position="130,370" size="190,21" font="Regular;19" transparent="1" />
		<widget source="Netmask_text" render="Label" position="130,395" size="190,21" font="Regular;19" transparent="1" />
		<widget source="Gateway_text" render="Label" position="130,420" size="190,21" font="Regular;19" transparent="1" />
		<widget source="IPAddress" render="Label" position="340,370" size="240,21" font="Regular;19" transparent="1" />
		<widget source="Netmask" render="Label" position="340,395" size="240,21" font="Regular;19" transparent="1" />
		<widget source="Gateway" render="Label" position="340,420" size="240,21" font="Regular;19" transparent="1" />
		</screen>"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.session = session
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.doConfigMsg,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.doConfigMsg,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		self["key_yellow"] = StaticText(_(" "))
		self["key_blue"] = StaticText(_(" "))
		self["current_settings"] = StaticText(_("Current settings (interface : br0)"))
		self["IPAddress_text"] = StaticText(_("IP Address"))
		self["Netmask_text"] = StaticText(_("Netmask"))
		self["Gateway_text"] = StaticText(_("Gateway"))
		self["IPAddress"] = StaticText(_("N/A"))
		self["Netmask"] = StaticText(_("N/A"))
		self["Gateway"] = StaticText(_("N/A"))

		self.makeConfig()
		self.apModeChanged = False

		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self.currentNetworkSettings)
		self.onLayoutFinish.append(self.checkConfigError)

		self.configErrorTimer = eTimer()
		self.configErrorTimer.callback.append(self.configErrorMsg)

		self.configStartMsg = None

	def makeConfig(self):
		self.msg = ""
		if self.checkWirelessDevices():
			return

		self.checkRunHostapd()
		self.makeConfigList()
		self.loadInterfacesConfig()
		self.loadHostapConfig()
		self.setupCurrentEncryption()
		self.createConfigEntry()
		self.createConfig()

	def checkConfigError(self):
		if self.msg:
			self.configErrorTimer.start(100, True)

	def configErrorMsg(self):
		self.session.openWithCallback(self.close ,MessageBox, _(self.msg), MessageBox.TYPE_ERROR)

	def checkwlanDeviceList(self):
		if len(self.wlanDeviceList) == 0:
			self.checkwlanDeviceListTimer.start(100,True)

	def currentNetworkSettings(self):
		self["IPAddress"].setText(self.formatAddr(iNetwork.getAdapterAttribute("br0", "ip")))
		self["Netmask"].setText(self.formatAddr(iNetwork.getAdapterAttribute("br0", "netmask")))
		self["Gateway"].setText(self.formatAddr(iNetwork.getAdapterAttribute("br0", "gateway")))

	def formatAddr(self, address = [0,0,0,0]):
		if address is None:
			return "N/A"
		return "%d:%d:%d:%d"%(address[0],address[1],address[2],address[3])

	def checkRunHostapd(self):
		global apModeConfig
		if fileExists("/var/run/hostapd", 0):
			apModeConfig.useap.value = True

	def checkWirelessDevices(self):
		global apModeConfig
		self.wlanDeviceList = []
		wlanIfaces =[]
		for x in iNetwork.getInstalledAdapters():
			if x.startswith('eth') or x.startswith('br') or x.startswith('mon'):
				continue
			elif os_path.exists("/tmp/bcm/%s"%x):
				continue
			wlanIfaces.append(x)
			description=self.getAdapterDescription(x)
			if description == "Unknown network adapter":
				self.wlanDeviceList.append((x, x))
			else:
				self.wlanDeviceList.append(( x, description + " (%s)"%x ))

		if len(self.wlanDeviceList) == 0:
			self.msg = "Can not find wireless lan devices that support AP mode."
			return -1

		apModeConfig.wirelessdevice = ConfigSelection( choices = self.wlanDeviceList )
		return 0

	def makeConfigList(self):
		global apModeConfig
		self.hostapdConf = {}
		self.hostapdConf["interface"] = apModeConfig.wirelessdevice
		self.hostapdConf["bridge"] = apModeConfig.branch # "br0"
		self.hostapdConf["driver"] = apModeConfig.driver # "nl80211"
		self.hostapdConf["hw_mode"] = apModeConfig.wirelessmode
		self.hostapdConf["channel"] = apModeConfig.channel
		self.hostapdConf["ssid"] = apModeConfig.ssid
		self.hostapdConf["beacon_int"] = apModeConfig.beacon
		self.hostapdConf["rts_threshold"] = apModeConfig.rts_threshold
		self.hostapdConf["fragm_threshold"] = apModeConfig.fragm_threshold
		self.hostapdConf["preamble"] = apModeConfig.preamble
#		self.hostapdConf["macaddr_acl"] = "" # fix to add Access Control List Editer
#		self.hostapdConf["accept_mac_file"] = "" # fix to add Access Control List Editer
#		self.hostapdConf["deny_mac_file"] = "" # fix to add Access Control List Editer
		self.hostapdConf["ignore_broadcast_ssid"] = apModeConfig.ignore_broadcast_ssid
#		self.hostapdConf["wmm_enabled"] = ""
#		self.hostapdConf["ieee80211n"] = ""
#		self.hostapdConf["ht_capab"] = ""
		self.hostapdConf["wep_default_key"] = apModeConfig.wep_default_key
		self.hostapdConf["wep_key0"] = apModeConfig.wep_key0
		self.hostapdConf["wpa"] = apModeConfig.wpa
		self.hostapdConf["wpa_passphrase"] = apModeConfig.wpa_passphrase
		self.hostapdConf["wpa_key_mgmt"] = apModeConfig.wpa_key_mgmt # "WPA-PSK"
		self.hostapdConf["wpa_pairwise"] = apModeConfig.wpa_pairwise # "TKIP CCMP"
		self.hostapdConf["rsn_pairwise"] = apModeConfig.rsn_pairwise # "CCMP"
		self.hostapdConf["wpa_group_rekey"] = apModeConfig.wpagrouprekey

	def loadInterfacesConfig(self):
		global apModeConfig
		try:
			fp = file('/etc/network/interfaces', 'r')
			datas = fp.readlines()
			fp.close()
		except:
			printDebugMsg("Read failed, /etc/network/interfaces.")
			return -1

		current_iface = ""
		try:
			for line in datas:
				split = line.strip().split(' ')
				if (split[0] == "iface"):
					current_iface = split[1]

				if (current_iface == "br0" or current_iface == "eth0"):
					if (len(split) == 4 and split[3] == "dhcp"):
						apModeConfig.usedhcp.value = True
					if (split[0] == "address"):
						apModeConfig.address.value = map(int, split[1].split('.'))
					if (split[0] == "netmask"):
						apModeConfig.netmask.value = map(int, split[1].split('.'))
					if (split[0] == "gateway"):
						apModeConfig.gateway.value = map(int, split[1].split('.'))
					if (split[0] == "dns-nameservers"):
						apModeConfig.nameserver.value = map(int, split[1].split('.'))
		except:
			printDebugMsg("Parsing failed, /etc/network/interfaces.")
			return -1

		return 0

	def setupCurrentEncryption(self):
		global apModeConfig
		if len(apModeConfig.wep_key0.value) > 10:
			apModeConfig.wepType.value = "128"

		if apModeConfig.wpa.value is not "0" and apModeConfig.wpa_passphrase.value: # (1,WPA), (2,WPA2), (3,WPA/WPA2)
			apModeConfig.encrypt.value = True
			apModeConfig.method.value = apModeConfig.wpa.value
		elif apModeConfig.wep.value and apModeConfig.wep_key0.value:
			apModeConfig.encrypt.value = True
			apModeConfig.method.value = "0" # wep
		else:
			apModeConfig.encrypt.value = False

	def createConfigEntry(self):
		global apModeConfig
#hostap settings
		self.useApEntry = getConfigListEntry(_("Use AP Mode"), apModeConfig.useap)
		self.setupModeEntry = getConfigListEntry(_("Setup Mode"), apModeConfig.setupmode)
		self.wirelessDeviceEntry = getConfigListEntry(_("AP Device"), apModeConfig.wirelessdevice)
		self.wirelessModeEntry = getConfigListEntry(_("AP Mode"), apModeConfig.wirelessmode)
		self.channelEntry = getConfigListEntry(_("Channel (1~13)"), apModeConfig.channel)
		self.ssidEntry = getConfigListEntry(_("SSID (1~32 Characters)"), apModeConfig.ssid)
		self.beaconEntry = getConfigListEntry(_("Beacon (15~65535)"), apModeConfig.beacon)
		self.rtsThresholdEntry = getConfigListEntry(_("RTS Threshold (0~2347)"), apModeConfig.rts_threshold)
		self.fragmThresholdEntry = getConfigListEntry(_("FRAGM Threshold (256~2346)"), apModeConfig.fragm_threshold)
		self.prambleEntry = getConfigListEntry(_("Preamble"), apModeConfig.preamble)
		self.ignoreBroadcastSsid = getConfigListEntry(_("Ignore Broadcast SSID"), apModeConfig.ignore_broadcast_ssid)
# hostap encryption
		self.encryptEntry = getConfigListEntry(_("Encrypt"), apModeConfig.encrypt)
		self.methodEntry = getConfigListEntry(_("Method"), apModeConfig.method)
		self.wepKeyTypeEntry = getConfigListEntry(_("KeyType"), apModeConfig.wepType)
		self.wepKey0Entry = getConfigListEntry(_("WEP Key (HEX)"), apModeConfig.wep_key0)
		self.wpaKeyEntry = getConfigListEntry(_("KEY (8~63 Characters)"), apModeConfig.wpa_passphrase)
		self.groupRekeyEntry = getConfigListEntry(_("Group Rekey Interval"), apModeConfig.wpagrouprekey)
# interface settings
		self.usedhcpEntry = getConfigListEntry(_("Use DHCP"), apModeConfig.usedhcp)
		self.ipEntry = getConfigListEntry(_("IP Address"), apModeConfig.address)
		self.netmaskEntry = getConfigListEntry(_("NetMask"), apModeConfig.netmask)
		self.gatewayEntry = getConfigListEntry(_("Gateway"), apModeConfig.gateway)
		self.nameserverEntry = getConfigListEntry(_("Nameserver"), apModeConfig.nameserver)

	def createConfig(self):
		global apModeConfig
		apModeConfig.address.value = iNetwork.getAdapterAttribute(apModeConfig.branch.value, "ip") or [0,0,0,0]
		apModeConfig.netmask.value = iNetwork.getAdapterAttribute(apModeConfig.branch.value, "netmask") or [255,0,0,0]
		apModeConfig.gateway.value = iNetwork.getAdapterAttribute(apModeConfig.branch.value, "gateway") or [0,0,0,0]

		self.configList = []
		self.configList.append( self.useApEntry )
		if apModeConfig.useap.value is True:
			self.configList.append( self.setupModeEntry )
			self.configList.append( self.wirelessDeviceEntry )
			self.configList.append( self.wirelessModeEntry )
			self.configList.append( self.channelEntry )
			self.configList.append( self.ssidEntry )
			if apModeConfig.setupmode.value  is "advanced":
				self.configList.append( self.beaconEntry )
				self.configList.append( self.rtsThresholdEntry )
				self.configList.append( self.fragmThresholdEntry )
				self.configList.append( self.prambleEntry )
				self.configList.append( self.ignoreBroadcastSsid )
			self.configList.append( self.encryptEntry )
			if apModeConfig.encrypt.value is True:
				self.configList.append( self.methodEntry )
				if apModeConfig.method.value is "0": # wep
					self.configList.append( self.wepKeyTypeEntry )
					self.configList.append( self.wepKey0Entry )
				else:
					self.configList.append( self.wpaKeyEntry )
					if apModeConfig.setupmode.value  is "advanced":
						self.configList.append( self.groupRekeyEntry )
## 		set network interfaces
			self.configList.append( self.usedhcpEntry )
			if apModeConfig.usedhcp.value is False:
				self.configList.append( self.ipEntry )
				self.configList.append( self.netmaskEntry )
				self.configList.append( self.gatewayEntry )
				self.configList.append( self.nameserverEntry )
		self["config"].list = self.configList
		self["config"].l.setList(self.configList)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def newConfig(self):
		if self["config"].getCurrent() in [ self.encryptEntry, self.methodEntry, self.useApEntry, self.usedhcpEntry, self.setupModeEntry]:
			self.createConfig()

	# 0 : legacy module activated, 1 : kernel module activated, -1 : None
	def checkProcModules(self):
		proc_path = "/proc/modules"
		legacy_modules = ("rt3070", "rt3070sta", "rt5372", "rt5372sta", "rt5370", "rt5370sta")
		kernel_modules = ("rt2800usb", "rt2800lib")

		fd = open(proc_path, "r")
		data = fd.readlines()
		fd.close()

		for line in data:
			module = line.split()[0].strip()
			if module in legacy_modules:
				return 0
			elif module in kernel_modules:
				return 1

		return -1

	def isRalinkModule(self):
		global apModeConfig
		iface = apModeConfig.wirelessdevice.value

# check vendor ID for lagacy driver
		vendorID = "148f" # ralink vendor ID
		idVendorPath = "/sys/class/net/%s/device/idVendor" % iface
		if access(idVendorPath, R_OK):
			fd = open(idVendorPath, "r")
			data = fd.read().strip()
			fd.close()

			printDebugMsg("Vendor ID : %s" % data)

			if data == vendorID:
				return True

# check sys driver path for kernel driver
		ralinkKmod = "rt2800usb" # ralink kernel driver name
		driverPath = "/sys/class/net/%s/device/driver/" % iface
		if os_path.exists(driverPath):
			driverName = os_path.basename(os_path.realpath(driverPath))

			printDebugMsg("driverName : %s" % driverName)

			if driverName == ralinkKmod:
				return True

		return False

	def doConfigMsg(self):
		global apModeConfig
		msg = "Are you sure you want to setup AP?\n"

		isRainkIface = self.isRalinkModule()
		isApMode = apModeConfig.useap.value is True
		isRalinkKmodUploaded = self.checkProcModules() == 1

		if isRainkIface and isApMode and (not isRalinkKmodUploaded ):
			msg += "( STB should be reboot to enable AP mode. )\n"
		else:
			msg += ("\n")
		self.session.openWithCallback(self.doConfig, MessageBox, (_(msg) ) )

	def doConfig(self, ret = False):
		global apModeConfig
		if ret is not True:
			return
		if apModeConfig.useap.value is True and apModeConfig.encrypt.value is True:
			if not self.checkEncrypKey():
				return
		if not self.checkConfig():
			return

		self.configStartMsg = self.session.openWithCallback(self.ConfigFinishedMsg, MessageBox, _("Please wait for AP Configuration....\n") , type = MessageBox.TYPE_INFO, enable_input = False)

		if apModeConfig.useap.value is True:
			self.networkRestart( nextFunc = self.makeConf )
		else:
			self.networkRestart( nextFunc = self.removeConf )

	def checkEncrypKey(self):
		global apModeConfig
		if apModeConfig.method.value == "0":
			if self.checkWep(apModeConfig.wep_key0.value) is False:
				self.session.open(MessageBox, _("Invalid WEP key\n\n"), type = MessageBox.TYPE_ERROR, timeout = 10 )
			else:
				return True
		else:
			if not len(apModeConfig.wpa_passphrase.value) in range(8,65):
				self.session.open(MessageBox, _("Invalid WPA key\n\n"), type = MessageBox.TYPE_ERROR, timeout = 10)
			else:
				return True
		return False

	def checkWep(self,  key):
		global apModeConfig
		length = len(key)
		if length == 0:
			return False
		elif apModeConfig.wepType.value == "64" and length == 10:
			return True
		elif apModeConfig.wepType.value == "128" and length == 26:
			return True
		else:
			return False

	def checkConfig(self):
		global apModeConfig
		# ssid Check
		if len(apModeConfig.ssid.value) == 0 or len(apModeConfig.ssid.value) > 32:
			self.session.open(MessageBox, _("Invalid SSID\n"), type = MessageBox.TYPE_ERROR, timeout = 10)
			return False;
		elif apModeConfig.channel.value not in range(1,14):
			self.session.open(MessageBox, _("Invalid channel\n"), type = MessageBox.TYPE_ERROR, timeout = 10)
			return False;
		elif apModeConfig.beacon.value < 15 or apModeConfig.beacon.value > 65535:
			self.session.open(MessageBox, _("Invalid beacon\n"), type = MessageBox.TYPE_ERROR, timeout = 10)
			return False;
		elif apModeConfig.rts_threshold.value < 0 or apModeConfig.rts_threshold.value > 2347:
			self.session.open(MessageBox, _("Invalid RTS Threshold\n"), type = MessageBox.TYPE_ERROR, timeout = 10)
			return False;
		elif apModeConfig.fragm_threshold.value < 256 or apModeConfig.fragm_threshold.value > 2346:
			self.session.open(MessageBox, _("Invalid Fragm Threshold\n"), type = MessageBox.TYPE_ERROR, timeout = 10)
			return False;
		elif apModeConfig.wpagrouprekey.value < 0 or apModeConfig.wpagrouprekey.value > 3600:
			self.session.open(MessageBox, _("Invalid wpagrouprekey\n"), type = MessageBox.TYPE_ERROR, timeout = 10)
			return False;
		return True;

	def networkRestart(self, nextFunc = None ):
		self.networkRestart_stop( nextFunc = nextFunc )

	def networkRestart_stop(self, nextFunc = None ):
		printDebugMsg("networkRestart_stop")
		self.msgPlugins(False)
		self.commands = [] # stop current network
		self.networkRestartConsole = Console()
		self.commands.append("/etc/init.d/avahi-daemon stop")
		for iface in iNetwork.getAdapterList():
			if iface != 'eth0' or not iNetwork.onRemoteRootFS():
				self.commands.append("ifdown " + iface)
				self.commands.append("ip addr flush dev " + iface)
		self.commands.append("/etc/init.d/hostapd stop")
		self.commands.append("/etc/init.d/networking stop")
		self.commands.append("killall -9 udhcpc")
		self.commands.append("rm /var/run/udhcpc*")
		self.networkRestartConsole.eBatch(self.commands, nextFunc, debug = True)

	def makeConf(self,extra_args):
		printDebugMsg("makeConf")
		self.writeNetworkInterfaces()
		result = self.writeHostapdConfig()
		if result == -1:
			self.configStartMsg.close(False)
			self.configErrorTimer.start(100, True)
			return
		self.setIpForward(1)
		self.networkRestart_start()

	def removeConf(self,extra_args):
		global apModeConfig
		printDebugMsg("removeConf")
		if fileExists("/etc/hostapd.conf", 'f'):
			os_system("mv /etc/hostapd.conf /etc/hostapd.conf.linuxap.back")
		fp = file("/etc/network/interfaces", 'w')
		fp.write("# automatically generated by AP Setup Plugin\n# do NOT change manually!\n\n")
		fp.write("auto lo\n")
		fp.write("iface lo inet loopback\n\n")
		# eth0 setup
		fp.write("auto eth0\n")
		if apModeConfig.usedhcp.value is True:
			fp.write("iface eth0 inet dhcp\n")
		else:
			fp.write("iface eth0 inet static\n")
			fp.write("	address %d.%d.%d.%d\n" % tuple(apModeConfig.address.value) )
			fp.write("	netmask %d.%d.%d.%d\n" % tuple(apModeConfig.netmask.value) )
			fp.write("	gateway %d.%d.%d.%d\n" % tuple(apModeConfig.gateway.value) )
			fp.write("	dns-nameservers %d.%d.%d.%d\n" % tuple(apModeConfig.nameserver.value) )
		fp.close()
		self.setIpForward(0)
		self.networkRestart_start()

	def networkRestart_start(self):
		global apModeConfig
		printDebugMsg("networkRestart_start")
		self.restartConsole = Console()
		self.commands = []
		self.commands.append("/etc/init.d/networking start")
		self.commands.append("/etc/init.d/avahi-daemon start")
		if apModeConfig.useap.value is True:
			self.commands.append("/etc/init.d/hostapd start")
		self.restartConsole.eBatch(self.commands, self.networkRestartFinished, debug=True)

	def networkRestartFinished(self, data):
		printDebugMsg("networkRestartFinished")
		iNetwork.ifaces = {}
		iNetwork.getInterfaces(self.getInterfacesDataAvail)

	def getInterfacesDataAvail(self, data):
		self.blacklist_legacy_drivers()
		if data is True and self.configStartMsg is not None:
			self.configStartMsg.close(True)

	def ConfigFinishedMsg(self, ret):
		if ret is True:
			self.session.openWithCallback(self.ConfigFinishedMsgCallback ,MessageBox, _("Configuration your AP is finished"), type = MessageBox.TYPE_INFO, timeout = 5, default = False)

	def needRalinkKmod(self):
		global apModeConfig
		isRainkIface = self.isRalinkModule()
		ApMode = apModeConfig.useap.value is True

		if isRainkIface and ApMode:
			return True
		else:
			return False

	def ConfigFinishedMsgCallback(self,data):
		isRalinkKmodUploaded = self.checkProcModules() == 1
		needRalinkKmod_ = self.needRalinkKmod()
	
		if needRalinkKmod_ : # ralink device is activated in AP Mode.
			if not isRalinkKmodUploaded : # reboot to loading kernel module.
				msg = "You should now reboot your STB in order to ralink device operate in AP mode.\n\nReboot now ?\n\n"
				self.session.openWithCallback(self.doReboot, MessageBox, _(msg), type = MessageBox.TYPE_YESNO, default = True )
			else:
				self.close()
		elif isRalinkKmodUploaded :
			msg = "You should now reboot your STB to better performance of ralink device in STA mode.\n\nReboot now ?\n\n"
			self.session.openWithCallback(self.doReboot, MessageBox, _(msg), type = MessageBox.TYPE_YESNO, default = True )
		else:
			self.close()

	def blacklist_legacy_drivers(self):
		blacklist_conf_dir = "/etc/modprobe.d"
		blacklist_conf_file = blacklist_conf_dir + "/blacklist-wlan.conf"
		legacy_modules = ("rt3070", "rt3070sta", "rt5372", "rt5372sta", "rt5370", "rt5370sta")
		kernel_modules = ("rt2800usb", "rt2800lib")
		blacklist = ""

		need_ralink_kmod = self.needRalinkKmod()

		if access(blacklist_conf_file, R_OK) is True:
			fd = open(blacklist_conf_file, "r")
			data = fd.read()
			fd.close()

			if need_ralink_kmod: # check legacy modules in blacklist
				for mod in legacy_modules:
					if data.find(mod) != -1: return
			else:
				for mod in kernel_modules: # check kernel modules in blacklist
					if data.find(mod) != -1: return

		if not os_path.exists(blacklist_conf_dir):
			makedirs(blacklist_conf_dir)

		if need_ralink_kmod:
			blacklist_modules = legacy_modules
		else:
			blacklist_modules = kernel_modules

		for module in blacklist_modules:
			blacklist += "blacklist %s\n" % module
		f = open(blacklist_conf_file, "w+")
		f.write(blacklist)
		f.close()
		self.apModeChanged = True

	def doReboot(self, res):
		if res:
			self.session.open(TryQuitMainloop, 2)
		else:
			self.close()

	def msgPlugins(self,reason = False):
		for p in plugins.getPlugins(PluginDescriptor.WHERE_NETWORKCONFIG_READ):
				p(reason=reason)

	def writeNetworkInterfaces(self):
		global apModeConfig
		fp = file("/etc/network/interfaces", 'w')
		fp.write("# automatically generated by AP Setup Plugin\n# do NOT change manually!\n\n")
		fp.write("auto lo\n")
		fp.write("iface lo inet loopback\n\n")
		# eth0 setup
		fp.write("auto eth0\n")
		fp.write("iface eth0 inet manual\n")
		fp.write("	up ip link set $IFACE up\n")
		fp.write("	down ip link set $IFACE down\n\n")
		# branch setup
		fp.write("auto br0\n")
		if apModeConfig.usedhcp.value is True:
			fp.write("iface br0 inet dhcp\n")
		else:
			fp.write("iface br0 inet static\n")
			fp.write("	address %d.%d.%d.%d\n" % tuple(apModeConfig.address.value) )
			fp.write("	netmask %d.%d.%d.%d\n" % tuple(apModeConfig.netmask.value) )
			fp.write("	gateway %d.%d.%d.%d\n" % tuple(apModeConfig.gateway.value) )
			fp.write("	dns-nameservers %d.%d.%d.%d\n" % tuple(apModeConfig.nameserver.value) )
		fp.write("	pre-up brctl addbr br0\n")
		fp.write("	pre-up brctl addif br0 eth0\n")
		fp.write("	post-down brctl delif br0 eth0\n")
		fp.write("	post-down brctl delbr br0\n\n")
		fp.write("\n")
		fp.close()

	def setIpForward(self, setValue = 0):
		ipForwardFilePath = "/proc/sys/net/ipv4/ip_forward"
		if not fileExists(ipForwardFilePath):
			return -1
		printDebugMsg("set %s to %d" % (ipForwardFilePath, setValue))
		f = open(ipForwardFilePath, "w")
		f.write("%d" % setValue)
		f.close()
		sysctlPath = "/etc/sysctl.conf"
		sysctlLines = []
		if fileExists(sysctlPath):
			fp = file(sysctlPath, "r")
			sysctlLines = fp.readlines()
			fp.close()
		sysctlList = {}
		for line in sysctlLines:
			line = line.strip()
			try:
				(key,value) = line.split("=")
				key=key.strip()
				value=value.strip()
			except:
				continue
			sysctlList[key] = value
		sysctlList["net.ipv4.ip_forward"] = str(setValue)
		fp = file(sysctlPath, "w")
		for (key,value) in sysctlList.items():
			fp.write("%s=%s\n"%(key,value))
		fp.close()
		return 0

	def getAdapterDescription(self, iface):
		classdir = "/sys/class/net/" + iface + "/device/"
		driverdir = "/sys/class/net/" + iface + "/device/driver/"
		if os_path.exists(classdir):
			files = listdir(classdir)
			if 'driver' in files:
				if os_path.realpath(driverdir).endswith('rtw_usb_drv'):
					return _("Realtek")+ " " + _("WLAN adapter.")
				elif os_path.realpath(driverdir).endswith('ath_pci'):
					return _("Atheros")+ " " + _("WLAN adapter.")
				elif os_path.realpath(driverdir).endswith('zd1211b'):
					return _("Zydas")+ " " + _("WLAN adapter.")
				elif os_path.realpath(driverdir).endswith('rt73'):
					return _("Ralink")+ " " + _("WLAN adapter.")
				elif os_path.realpath(driverdir).endswith('rt73usb'):
					return _("Ralink")+ " " + _("WLAN adapter.")
				else:
					return str(os_path.basename(os_path.realpath(driverdir))) + " " + _("WLAN adapter")
			else:
				return _("Unknown network adapter")
		else:
			return _("Unknown network adapter")

	def __onClose(self):
		global apModeConfig
		for x in self["config"].list:
			x[1].cancel()
		apModeConfig.wpa.value = "0"
		apModeConfig.wep.value = False

	def keyCancel(self):
		self.close()

	def printConfigList(self, confList):
		printDebugMsg("== printConfigList ==");
		for (key, entry) in confList.items():
			printDebugMsg("%s = %s"%(key , str(entry.value)));
		
		printDebugMsg("== printConfigList end ==");

	def loadHostapConfig(self):
		global apModeConfig
		fd = -1
		if access("/etc/hostapd.conf", R_OK) is True:
			printDebugMsg("open /etc/hostapd.conf")
			fd = open("/etc/hostapd.conf", "r")
		elif access("/etc/hostapd.conf.linuxap.back", R_OK) is True:
			printDebugMsg("open /etc/hostapd.conf.linuxap.back")
			fd = open("/etc/hostapd.conf.linuxap.back", "r")
		if fd == -1:
			printDebugMsg("can not open hostapd.conf") 
			return -1

		for line in fd.readlines():
			line = line.strip()

			if (len(line) == 0) or (line.find('=') == -1):
				continue

			data = line.split('=', 1)
			if len(data) != 2:
				continue

			key = data[0].strip()
			value = data[1].strip()

			if key == "#wep_key0":
				self.hostapdConf["wep_key0"].value = value
				apModeConfig.wep.value = False

			elif key == "wep_key0":
				self.hostapdConf["wep_key0"].value = value
				apModeConfig.wep.value = True

			elif key.startswith('#'):
				continue

			elif key == "channel" :
				if int(value) not in range(14):
					self.hostapdConf[key].value = 1
				else:
					self.hostapdConf[key].value = int(value)

			elif key in ["beacon_int", "rts_threshold", "fragm_threshold", "wpa_group_rekey"]:
				self.hostapdConf[key].value = int(value)

			elif key in self.hostapdConf.keys():
				self.hostapdConf[key].value = value

		fd.close()
		self.printConfigList(self.hostapdConf)

		return 0

	def writeHostapdConfig(self):
		global apModeConfig
		global ORIG_HOSTAPD_CONF
		self.printConfigList(self.hostapdConf)
		if access(ORIG_HOSTAPD_CONF, R_OK) is not True:
			self.msg = "can not access file. (%s)" % ORIG_HOSTAPD_CONF
			printDebugMsg(self.msg)
			return -1

		orig_conf = open(ORIG_HOSTAPD_CONF, "r")
		if orig_conf == -1:
			print "can't open file. (%s)" % ORIG_HOSTAPD_CONF

		new_conf = open(HOSTAPD_CONF, "w")
		if new_conf == -1:
			print "can't open file. (%s)" % HOSTAPD_CONF

		isEncryptOn = apModeConfig.encrypt.value is True
		isEncryptWEP = apModeConfig.method.value == "0"
		isEncryptWPA = not isEncryptWEP

		for r_line in orig_conf.readlines():
			line = r_line.strip()
			if len(line) < 2:
				new_conf.write(r_line)
				continue

			fix_line = None
# for encrypt line
			if line.find("wep_default_key=") != -1 : # is wepLine
				if isEncryptOn and isEncryptWEP :
					fix_line = "wep_default_key=%s\n" % self.hostapdConf["wep_default_key"].value

			elif line.find("wep_key0=") != -1 : # is WepKeyLine
				if isEncryptOn: 
					if isEncryptWEP :
						fix_line = "wep_key0=%s\n" % self.hostapdConf["wep_key0"].value
					else:
						fix_line = "#wep_key0=%s\n" % self.hostapdConf["wep_key0"].value

				else:
					fix_line = "#wep_key0=%s\n" % self.hostapdConf["wep_key0"].value

			elif line.find("wpa=") != -1 : # is wpaLine
				if isEncryptOn and isEncryptWPA : 
					fix_line = "wpa=%s\n" % apModeConfig.method.value
##
			elif line.startswith("#ssid"):
				pass

			else:
				for (key , entry) in self.hostapdConf.items():
					value = str(entry.value)
					pos = line.find(key+'=')
					if ( (pos != -1) and (pos < 2) ) and len(value)!=0 :
						fix_line = "%s=%s\n" % (key, value)
						break

#			if fix_line is not None:
#				print "r_line : ", r_line,
#				print "fix_li : ", fix_line

			if fix_line is not None:
				new_conf.write(fix_line)
			else:
				new_conf.write(r_line)

		orig_conf.close()
		new_conf.close()
		return 0

def main(session, **kwargs):
	session.open(WirelessAccessPoint)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("Wireless Access Point"), description=_("Using a Wireless module as access point."), where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = True, fnc=main)]


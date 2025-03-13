#####################################################################################
# CAUTION: the USB ports on some boxes may not have enough electrical power to feed #
# a USB 3G/4G modem when the modem is trying to increase antenna power for dial-up. #
# Please use an active USB hub with its own power supply to ensure required power.  #
#####################################################################################

# PYTHON IMPORTS
from os import getpid, system, popen
from os.path import exists
from re import search
from select import POLLIN, POLLPRI
from socket import socket, AF_NETLINK, SOCK_DGRAM
from time import sleep
from xml.sax import make_parser, handler

# ENIGMA IMPORTS
from enigma import eTimer, eConsoleAppContainer, eSocketNotifier
from Components.About import about
from Components.ActionMap import ActionMap
from Components.ConditionalWidget import BlinkingWidget
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigText, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Network import iNetwork
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import resolveFilename, fileExists, SCOPE_CURRENT_PLUGIN
from twisted.internet.reactor import callInThread

# PLUGIN IMPORTS
from . import _  # for localized messages

# PLUGIN GLOBALS
DEBUGMODE = False  # activate for details infos when desired
WVDIALFILE = "/etc/wvdial.conf"
COMMANDBIN = resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/3GModemManager/3gcommand")
ONSTATUS = {0: _("1. Load a Mobile Broadband Device"), 1: _("2. Set up a Mobile Broadband Device"),
			2: _("3. Generate a WvDial profile"), 3: _("4. Attempt to connect"), 4: _("5. Done")}
OFFSTATUS = {0: _("1. Drop WvDial"), 1: _("2. Unload a Mobile Broadband Device"), 2: _("3. Done")}

config.plugins.gmodemmanager = ConfigSubsection()
config.plugins.gmodemmanager.autostart = ConfigYesNo(default=False)
config.plugins.gmodemmanager.vendorid = ConfigText(default="0000")
config.plugins.gmodemmanager.productid = ConfigText(default="0000")
config.plugins.gmodemmanager.apn = ConfigText(default="apn")
config.plugins.gmodemmanager.uid = ConfigText(default=_("{unknown}"))
config.plugins.gmodemmanager.pwd = ConfigText(default=_("{unknown}"))
config.plugins.gmodemmanager.pin = ConfigText(default=_("{unknown}"))
config.plugins.gmodemmanager.phone = ConfigText(default="*99#")


def printDebug(msg):
	if DEBUGMODE:
		print("[3GModemManagerDebug] %s" % msg)


def printInfo(msg):
	print("[3GModemManager] %s" % msg)


def isConnected():
	return len(popen("ifconfig -a | grep ppp").read().strip()) > 0


class DeviceEventListener:
	notifyCallbackFunctionList = []

	def __init__(self):
		self.sock = socket(AF_NETLINK, SOCK_DGRAM)
		try:
			self.sock.bind((getpid(), 1))
			self.notifier = eSocketNotifier(self.sock.fileno(), POLLIN | POLLPRI)
			self.notifier.callback.append(self.cbEventHandler)
		except Exception as err:
			printInfo("Exception in module '__init__' %s" % err)
			self.sock.close()

	def cbEventHandler(self, sockfd):
		recv = self.sock.recv(65536).decode("utf-8", errors="ignore")
		if recv.lower().startswith("add@/block") or recv.lower().startswith("remove@/block"):
			for x in self.notifyCallbackFunctionList:
				try:
					x(recv)
				except Exception as err:
					printInfo("Exception in module 'cbEventHandler': %s" % err)
					self.notifyCallbackFunctionList.remove(x)

	def addCallback(self, func):
		if func is not None:
			self.notifyCallbackFunctionList.append(func)

	def delCallback(self, func):
		if func is not None:
			self.notifyCallbackFunctionList.remove(func)

	def close(self):
		try:
			self.notifier.callback.remove(self.cbEventHandler)
			self.sock.close()
		except Exception as err:
			printInfo("Exception in module 'close': %s" % err)


class TaskManager:
	def __init__(self):
		self.taskIdx = 0
		self.taskList = []
		self.gTaskInstance = None
		self.occurError = False
		self.cbSetStatusCB = None

	def append(self, command, cbDataFunc, cbCloseFunc):
		self.taskList.append(["%s" % command, cbDataFunc, cbCloseFunc])

	def dump(self):
		printDebug("############### TASK ###############")
		printDebug("Current Task Index : %s" % self.taskIdx)
		printDebug("Current Task Instance : %s" % self.gTaskInstance)
		printDebug("Occur Error : %s" % self.occurError)
		printDebug("Task List:\n%s" % self.taskList)
		printDebug("####################################")

	def error(self):
		printDebug("set task error!!")
		self.occurError = True

	def reset(self):
		self.taskIdx = 0
		self.gTaskInstance = None
		self.occurError = False

	def clean(self):
		self.reset()
		self.taskList = []
		self.cbSetStatusCB = None
		printDebug("clear task!!")

	def index(self):
		return self.taskIdx

	def setStatusCB(self, cbfunc):
		self.cbSetStatusCB = cbfunc

	def next(self):
		if self.taskIdx >= len(self.taskList) or self.occurError:
			printDebug("can't run task!!")
			return False
		command = self.taskList[self.taskIdx][0]
		cbDataFunc = self.taskList[self.taskIdx][1]
		cbCloseFunc = self.taskList[self.taskIdx][2]
		self.gTaskInstance = eConsoleAppContainer()
		if cbDataFunc is not None:
			self.gTaskInstance.dataAvail.append(cbDataFunc)
		if cbCloseFunc is not None:
			self.gTaskInstance.appClosed.append(cbCloseFunc)
		if self.cbSetStatusCB is not None:
			self.cbSetStatusCB(self.taskIdx)
		printInfo("prepared command :%s" % command)
		sleep(1)  # give modem more time, maybe not needed?
		self.gTaskInstance.execute(command)
		self.taskIdx += 1
		return True


class ParserHandler(handler.ContentHandler):

	def __init__(self):
		self.nodeList = []

	def startDocument(self):
		pass

	def endDocument(self):
		pass

	def startElement(self, name, attrs):
		if name == "apn":
			node = {}
			for attr in attrs.getNames():
				node[attr] = str(attrs.getValue(attr))
			self.nodeList.append(node)

	def endElement(self, name):
		pass

	def characters(self, content):
		pass

	def setDocumentLocator(self, locator):
		pass

	def getNodeList(self):
		return self.nodeList


class BlinkingLabel(Label, BlinkingWidget):

	def __init__(self, text=""):
		Label.__init__(self, text=text)
		BlinkingWidget.__init__(self)


class EditModemManual(ConfigListScreen, Screen):
	skin = """
  		<screen position="center,center" size="900,540">
			<widget name="config" position="0,0" size="900,450" itemHeight="40" scrollbarMode="showOnDemand" zPosition="2" />
			<eLabel name="red" position="10,480" size="6,60" backgroundColor="red" zPosition="1" />
			<eLabel name="green" position="235,480" size="6,60" backgroundColor="green" zPosition="1" />
			<eLabel name="blue" position="675,480" size="6,60" backgroundColor="blue" zPosition="1" />
			<widget source="key_red" render="Label" position="30,480" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
			<widget source="key_green" render="Label" position="255,480" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
			<widget source="key_blue" render="Label" position="695,480" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
  		</screen>
  		"""

	def __init__(self, session, cbFuncClose, uid=None, pwd=None, pin=None, apn=None, phone="*99#", isAdd=False):
		Screen.__init__(self, session)
		self.configList = []
		ConfigListScreen.__init__(self, self.configList)
		self.cbFuncClose, self.isAdd = cbFuncClose, isAdd
		self.uid, self.pwd, self.pin, self.apn, self.phone = ("", "", "", "", "") if isAdd else (uid, pwd, pin, apn, phone)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", ],
		{
			"ok": self.KeyText,
			"cancel": self.keyExit,
			"red": self.keyExit,
			"green": self.keySave,
			"blue": self.keyRemove,
		}, -2)
		self.createConfigList()
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_blue"] = StaticText(_(self.isAdd and " " or "Remove"))
		title = _("Config Add") if self.isAdd else _("Config Edit")
		self.setTitle(title)

	def createConfigList(self):
		self.configRegion = ConfigText(default="", visible_width=50, fixed_size=False)
		self.configName = ConfigText(default="", visible_width=50, fixed_size=False)
		self.configUserName = ConfigText(default=self.uid, visible_width=50, fixed_size=False)
		self.configPassword = ConfigText(default=self.pwd, visible_width=50, fixed_size=False)
		self.configAPN = ConfigText(default=self.apn, visible_width=50, fixed_size=False)
		self.configPIN = ConfigText(default=self.pin, visible_width=50, fixed_size=False)
		self.configPhone = ConfigText(default=self.phone, visible_width=50, fixed_size=False)
		self.configEntryRegion = getConfigListEntry("%s :" % _("Region"), self.configRegion)
		self.configEntryName = getConfigListEntry("%s :" % _("Name"), self.configName)
		self.configEntryUserName = getConfigListEntry("%s :" % _("User"), self.configUserName)
		self.configEntryPassword = getConfigListEntry("%s :" % _("Password"), self.configPassword)
		self.configEntryAPN = getConfigListEntry("%s :" % _("APN"), self.configAPN)
		self.configEntryPIN = getConfigListEntry("%s :" % _("PIN"), self.configPIN)
		self.configEntryPhone = getConfigListEntry("%s :" % _("Phone"), self.configPhone)
		if self.isAdd:
			self.configList.append(self.configEntryRegion)
			self.configList.append(self.configEntryName)
		self.configList.append(self.configEntryUserName)
		self.configList.append(self.configEntryPassword)
		self.configList.append(self.configEntryAPN)
		self.configList.append(self.configEntryPIN)
		self.configList.append(self.configEntryPhone)
		self["config"].setList(self.configList)

	def getCurrentItem(self):
		currentPosition = self["config"].getCurrent()
		if currentPosition == self.configEntryRegion:
			return self.configRegion
		elif currentPosition == self.configEntryName:
			return self.configName
		elif currentPosition == self.configEntryUserName:
			return self.configUserName
		elif currentPosition == self.configEntryPassword:
			return self.configPassword
		elif currentPosition == self.configEntryAPN:
			return self.configAPN
		elif currentPosition == self.configEntryPIN:
			return self.configPIN
		elif currentPosition == self.configEntryPhone:
			return self.configPhone
		return None

	def KeyText(self):
		currentItemValue = ""
		currentItem = self.getCurrentItem()
		if currentItem is not None:
			currentItemValue = currentItem.value
			if not currentItemValue:
				currentItemValue = ""
		self.session.openWithCallback(self.cbKeyText, VirtualKeyBoard, title=(_("Please input here")), text=currentItemValue)

	def cbKeyText(self, data=None):
		if data is not None:
			currentItem = self.getCurrentItem()
			if currentItem is not None:
				currentItem.setValue(data)

	def keyExit(self):
		self.close()

	def keyRemove(self):
		if not self.isAdd and self.cbFuncClose is not None:
			self.cbFuncClose(isRemove=True)
			self.close()

	def keySave(self):
		message = _("'%s' field is empty!!")
		titletext = (_("Please input here"))
		if not self.configRegion.value and self.isAdd:
			self.session.openWithCallback(self.KeyBoard_back, VirtualKeyBoard, title=titletext, text=message % _("Region"))
		elif not self.configName.value and self.isAdd:
			self.session.openWithCallback(self.KeyBoard_back, VirtualKeyBoard, title=titletext, text=message % _("Name"))
		elif not self.configAPN.value:
			self.session.openWithCallback(self.KeyBoard_back, VirtualKeyBoard, title=titletext, text=message % _("APN"))
		elif self.cbFuncClose is not None:
			self.uid = self.configUserName.value
			self.pwd = self.configPassword.value
			self.pin = self.configPIN.value
			self.apn = self.configAPN.value
			self.phone = self.configPhone.value
			self.name = self.isAdd and self.configName.value or None
			self.region = self.isAdd and self.configRegion.value or None
			self.cbFuncClose(self.uid, self.pwd, self.pin, self.apn, self.phone, self.name, self.region)
		self.close()

	def KeyBoard_back(self, text):
		if text:
			self.cur.value = text


class ModemManual(Screen):
	skin = """
		<screen position="center,center" size="880,690">
  			<widget name="menulist" position="0,0" size="450,600" backgroundColor="#000000" scrollbarMode="showOnDemand" zPosition="2" />
  			<widget name="apnInfo" position="465,0" size="435,600" font="Regular;30" halign="left" />
			<eLabel name="red" position="10,630" size="6,60" backgroundColor="red" zPosition="1" />
			<eLabel name="green" position="235,630" size="6,60" backgroundColor="green" zPosition="1" />
			<eLabel name="yellow" position="460,630" size="6,60" backgroundColor="yellow" zPosition="1" />
			<eLabel name="blue" position="675,630" size="6,60" backgroundColor="blue" zPosition="1" />
  			<widget source="key_red" render="Label" position="30,630" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
  			<widget source="key_green" render="Label" position="255,630" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
  			<widget source="key_yellow" render="Label" position="480,630" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
  			<widget source="key_blue" render="Label" position="695,630" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
		</screen>
		"""

	def __init__(self, session, cbFuncClose, uid=None, pwd=None, pin=None, apn=None, phone="*99#"):
		Screen.__init__(self, session)
		self.cbFuncClose, self.uid, self.pwd, self.pin, self.apn, self.phone = cbFuncClose, uid, pwd, pin, apn, phone
		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions"],
		{
			"ok": self.keyOK,
			"cancel": self.keyExit,
			"red": self.keyExit,
			"green": self.keyOK,
			"yellow": self.keyEdit,
			"blue": self.keyAdd,
			"left": self.keyLeft,
			"right": self.keyRight,
			"up": self.keyUp,
			"down": self.keyDown,
		}, -2)
		self["menulist"] = MenuList(self.setListOnView())
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"] = StaticText(_("Add"))
		self["apnInfo"] = Label(" ")
		self.setTitle(_("Config"))
		self.keyUp()

	def keyAdd(self):
		self.session.open(EditModemManual, self.cb3GManualSetting, isAdd=True)

	def keyEdit(self):
		self.session.open(EditModemManual, self.cb3GManualSetting, self.uid, self.pwd, self.pin, self.apn, self.phone)

	def cb3GManualSetting(self, uid=None, pwd=None, pin=None, apn=None, phone="*99#", name=None, region=None, isRemove=False):
		if not isRemove:
			self.uid, self.pwd, self.pin, self.apn, self.phone = uid, pwd, pin, apn, phone
		if name is not None:
			self["menulist"].list.append((name, {"region": region, "carrier": name, "apn": self.apn, "user": self.uid, "password": self.pwd, "pin": self.pin, "phone": self.phone}))
			self["menulist"].setList(self["menulist"].list)
			self["menulist"].moveToIndex(len(self["menulist"].list) - 1)
		if isRemove:
			index = 0
			newList = []
			selectedIndex = self["menulist"].getSelectionIndex()
			for x in self["menulist"].list:
				if index == selectedIndex:
					index += 1
					continue
				newList.append(x)
				index += 1
			self["menulist"].setList(newList)
			self["menulist"].moveToIndex(0)
			self.setAPNInfo(True)
			name = " "
		if not isRemove and not name:
			self.updateAPNList()
		self.updateAPNInfo()
		self.saveAPNList(name)

	def updateAPNList(self):
		selectedIndex = self["menulist"].getSelectionIndex()
		apnList = self["menulist"].list
		currentListItem = apnList[selectedIndex][1]
		currentListItem["user"] = self.uid
		currentListItem["apn"] = self.apn
		currentListItem["password"] = self.pwd
		currentListItem["pin"] = self.pin
		currentListItem["phone"] = self.phone
		self["menulist"].setList(apnList)

	def saveAPNList(self, name=None):
		apnList = self["menulist"].list
		selectedIndex = self["menulist"].getSelectionIndex()

		def makeItem(region, carrier, apn, user, password, pin, phone):
			printDebug("%s, %s, %s, %s, %s, %s, %s" % (region, carrier, apn, user, password, pin, phone))
			tempStr = "    <apn"
			tempStr += ' region="%s"' % region
			tempStr += ' carrier="%s"' % carrier
			tempStr += ' apn="%s"' % apn
			if user:
				tempStr += ' user="%s"' % user
			if password:
				tempStr += ' password="%s"' % password
			if pin:
				tempStr += ' pin="%s"' % pin
			if phone:
				tempStr += ' phone="%s"' % phone
			tempStr += ' />\n'
			return tempStr
		tempIndex = 0
		apnString = '<apns version="1">\n'
		for x in apnList:
			if selectedIndex == tempIndex and name is None:
				apnString += makeItem(self.region, x[0], self.apn, self.uid, self.pwd, self.pin, self.phone)
				tempIndex += 1
				continue
			apnString += makeItem(x[1].get("region", ""), x[1].get("carrier", ""), x[1].get("apn", ""), x[1].get("user", ""), x[1].get("password", ""), x[1].get("pin", ""), x[1].get("phone", ""))
			tempIndex += 1
		apnString += "</apns>\n"
		printDebug(apnString)
		with open(resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/3GModemManager/apnlist.xml"), "w") as apnListFile:
			apnListFile.write(apnString)

	def keyLeft(self):
		self["menulist"].pageUp()
		self.setAPNInfo()

	def keyRight(self):
		self["menulist"].pageDown()
		self.setAPNInfo()

	def keyUp(self):
		self["menulist"].up()
		self.setAPNInfo()

	def keyDown(self):
		self["menulist"].down()
		self.setAPNInfo()

	def keyOK(self):
		if self.cbFuncClose is not None:
			config.plugins.gmodemmanager.apn.setValue(self.apn)
			config.plugins.gmodemmanager.uid.setValue(self.uid)
			config.plugins.gmodemmanager.pwd.setValue(self.pwd)
			config.plugins.gmodemmanager.pin.setValue(self.pin)
			config.plugins.gmodemmanager.phone.setValue(self.phone)
			config.plugins.gmodemmanager.save()
			self.cbFuncClose(self.uid, self.pwd, self.pin, self.apn, self.phone)
		self.close()

	def keyExit(self):
		system("chattr -i /etc/ppp/resolv.conf;chattr -i /etc/resolv.conf")
		self.close()

	def setAPNInfo(self, noUpdate=False):
		self.region, self.apn, self.uid, self.pwd, self.pin, self.phone = ("", "", "", "", "", "")
		x = self["menulist"].getCurrent()[1]
		self.region, self.apn, self.uid, self.pwd, self.pin, self.phone = x.get("region", ""), x.get("apn", ""), x.get("user", ""), x.get("password", ""), x.get("pin", ""), x.get("phone", "")
		if noUpdate:
			return
		self.updateAPNInfo()

	def updateAPNInfo(self):
		info = "REGION : %s\nAPN : %s\nUSER : %s\nPASSWD : %s\nPIN : %s\nPHONE : %s\n" % (self.region, self.apn, self.uid, self.pwd, self.pin, self.phone)
		self["apnInfo"].setText(info)

	def setListOnView(self):

		lvApnItems = []

		def isExistAPN(name):
			for x in lvApnItems:
				if x[0] == name:
					return True
			return False

		handle = ParserHandler()
		parser = make_parser()
		parser.setContentHandler(handle)
		parser.parse(resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/3GModemManager/apnlist.xml"))
		apnList = sorted(handle.getNodeList(), key=lambda k: k["region"])
		for x in apnList:
			name = x.get("carrier", "")
			if not name:
				continue
			if isExistAPN(name):
				continue
			d = {}
			d["carrier"] = name
			d["region"] = x.get("region", "")
			d["apn"] = x.get("apn", "")
			d["user"] = x.get("user", "")
			d["password"] = x.get("password", "")
			d["pin"] = x.get("pin", "")
			d["phone"] = x.get("phone", "")
			lvApnItems.append((name, d))
		del handle
		return lvApnItems


class ModemManager(Screen):
	skin = """
		<screen position="center,center" size="920,690">
			<widget name="menulist" position="0,0" size="450,225" backgroundColor="black" scrollbarMode="showOnDemand" zPosition="2" />
			<widget name="usbinfo" position="465,0" size="435,230" font="Regular;27" halign="left" />
			<widget name="statusTitle" position="160,235" size="180,40" font="Regular;30" foregroundColor="black" backgroundColor="grey" halign="center" />
			<widget name="statusText" position="360,235" size="520,40" font="Regular;30" foregroundColor="red" halign="left" />
 			<widget name="statusInfo" position="0,280" size="900,190" font="Regular;30" halign="left" />
			<widget name="myip" position="75,480" size="900,180" font="Regular;30" halign="left" />
  			<widget name="autostart_text" position="75,540" size="250,40" font="Regular;30" halign="left" valign="center" />
  			<widget name="autostart_stop" position="350,535" size="200,50" font="Regular;30" halign="center" valign="center" backgroundColor="red" />
  			<widget name="autostart_start" position="400,535" size="200,50" font="Regular;30" halign="center" valign="center" backgroundColor="green" zPosition="1" />
			<eLabel name="red" position="10,630" size="6,60" backgroundColor="red" zPosition="1" />
			<eLabel name="green" position="235,630" size="6,60" backgroundColor="green" zPosition="1" />
			<eLabel name="yellow" position="460,630" size="6,60" backgroundColor="yellow" zPosition="1" />
			<eLabel name="blue" position="675,630" size="6,60" backgroundColor="blue" zPosition="1" />
  			<widget source="key_red" render="Label" position="30,630" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
  			<widget source="key_green" render="Label" position="255,630" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
  			<widget source="key_yellow" render="Label" position="480,630" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
  			<widget source="key_blue" render="Label" position="695,630" size="210,60" font="Regular;30" halign="left" valign="center" foregroundColor="grey" zPosition="1" />
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions"],
		{
			"ok": self.keyOK,
			"cancel": self.keyExit,
			"red": self.keyExit,
			"green": self.keyOK,
			"yellow": self.keyManual,
			"blue": self.keyAutoConnect,
			"up": self.keyUp,
			"down": self.keyDown,
			"left": self.keyLeft,
			"right": self.keyRight,
			"0": self.keyNumber,
		}, -2)
		self["menulist"] = MenuList([])
		self["usbinfo"] = Label()
		self["statusTitle"] = Label(_("Status"))
		self["statusText"] = BlinkingLabel(_("Searching for USB-devices..."))
		self["statusText"].startBlinking()
		self["statusText"].show()
		self["statusInfo"] = Label()
		self["myip"] = Label()
		self["autostart_text"] = Label("%s:" % _("Autoconnect"))
		self["autostart_stop"] = Label(_("Disable"))
		self["autostart_start"] = Label(_("Enable"))
		self["key_red"] = StaticText(_("Exit"))
		if isConnected():
			self["key_green"] = StaticText(_("Disconnect"))
			self.setDisconnectStatus(-1)
		else:
			self["key_green"] = StaticText(_("Connect"))
			self.setConnectStatus(-1)
		self["key_yellow"] = StaticText(_("Manual"))
		self["key_blue"] = StaticText(_("Autoconnect"))
		self.data = None
		self.connectionStatus = -1
		self.udevListener = DeviceEventListener()
		self.udevListener.addCallback(self.cbUdevListener)
		self.taskManager = TaskManager()
		self.refreshStatusTimer = eTimer()
		self.refreshStatusTimer.callback.append(self.cbRefreshStatus)
		if config.plugins.gmodemmanager.autostart.value:
			self["autostart_stop"].hide()
			self["autostart_start"].show()
		else:
			self["autostart_stop"].show()
			self["autostart_start"].hide()
		self.setTitle("3G/4G Modem Manager")
		self.forceStop = False
		self.uid = config.plugins.gmodemmanager.uid.value
		self.pwd = config.plugins.gmodemmanager.pwd.value
		self.pin = config.plugins.gmodemmanager.pin.value
		self.apn = config.plugins.gmodemmanager.apn.value
		self.phone = config.plugins.gmodemmanager.phone.value
		callInThread(self.setListOnView)
		callInThread(self.GetIP)

	def GetIP(self):
		if self["key_green"].getText() == "Disconnect":
			system("killall -9 wget")
			cmd = 'wget -q -O - http://checkip.dyndns.org | grep "html" | cut -d" " -f6  | cut -d"<" -f1'
			self["myip"].setText("IP : %s" % popen(cmd).read().strip())
		else:
			self["myip"].setText("IP : 0.0.0.0")

	def cbRefreshStatus(self):
		self.refreshStatusTimer.stop()
		if self["key_green"].getText() == "Connect":
			self.setConnectStatus(-1)
		elif self["key_green"].getText() == "Disconnect":
			self.setDisconnectStatus(-1)
		self.GetIP()

	def cbUdevListener(self, data):
		printDebug("Udev Listener Refresh!!")
		sleep(1)  # give modem more time, maybe not needed?
		callInThread(self.setListOnView)

	def isAttemptConnect(self):
		if self.connectionStatus < 1 or self.forceStop:
			return False
		maxidx = 4
		if self["key_green"].getText() == "Disconnect":
			maxidx = 2
		if self.connectionStatus < maxidx:
			printDebug("can't excute a command during connecting...")
			return True
		return False

	def keyManual(self):
		if not self.isAttemptConnect():
			self.session.open(ModemManual, self.cb3GManualSetting, self.uid, self.pwd, self.pin, self.apn, self.phone)

	def disableAutoConnect(self, answer):
		if answer is True:
				config.plugins.gmodemmanager.autostart.setValue(False)
				config.plugins.gmodemmanager.vendorid.setValue("0000")
				config.plugins.gmodemmanager.productid.setValue("0000")
				config.plugins.gmodemmanager.autostart.save()
				config.plugins.gmodemmanager.vendorid.save()
				config.plugins.gmodemmanager.productid.save()
				self["autostart_stop"].show()
				self["autostart_start"].hide()

	def keyAutoConnect(self):
		## AUTOSTART
		if isConnected():
			if not config.plugins.gmodemmanager.autostart.value:
				config.plugins.gmodemmanager.autostart.setValue(True)
				config.plugins.gmodemmanager.autostart.save()
				config.plugins.gmodemmanager.vendorid.save()
				config.plugins.gmodemmanager.productid.save()
				self["autostart_stop"].hide()
				self["autostart_start"].show()
				message = _("3G/4G Modem Manager will connect automatically on boot")
				printInfo(message)
				self.session.open(MessageBox, message, MessageBox.TYPE_INFO, 5)
			else:
				message = _("3G/4G Modem Manager is already in 'autoconnect on startup'.\nWould You like to disable 'autoconnect on startup'?")
				self.session.openWithCallback(self.disableAutoConnect, MessageBox, message, MessageBox.TYPE_YESNO)
		elif not isConnected() and config.plugins.gmodemmanager.autostart.value:
			message = _("3G/4G Modem Manager is already in 'autoconnect on startup'.\nWould You like to disable 'autoconnect on startup'?")
			self.session.openWithCallback(self.disableAutoConnect, MessageBox, message, MessageBox.TYPE_YESNO)
		else:
			message = _("Please connect before enable 'autoconnect on startup'.")
			printInfo(message)
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO, 5)

	def cb3GManualSetting(self, uid=None, pwd=None, pin=None, apn=None, phone="*99#"):
		self.uid, self.pwd, self.pin, self.apn, self.phone = uid, pwd, pin, apn, phone
		self.updateUSBInfo()

	def keyNumber(self, num=None):
		global DEBUGMODE
		DEBUGMODE = not DEBUGMODE
		printInfo("changed log mode, debug %s" % (DEBUGMODE and "on" or "off"))

	def keyExit(self):
		if self.isAttemptConnect():
			message = _("Can't disconnect during connecting..\nDo you want to forcibly exit?")
			self.session.openWithCallback(self.cbForciblyExit, MessageBox, message, default=False)
		else:
			self.udevListener.close()
			self.close()

	def cbForciblyExit(self, result):
		if result:
			system("%s -s 1" % COMMANDBIN)
			system("%s -s 2" % COMMANDBIN)
			system("%s -s 6" % COMMANDBIN)
			self.udevListener.close()
			self.close()

	def keyLeft(self):
		self["menulist"].pageUp()
		self.updateUSBInfo()

	def keyRight(self):
		self["menulist"].pageDown()
		self.updateUSBInfo()

	def keyUp(self):
		self["menulist"].up()
		self.updateUSBInfo()

	def keyDown(self):
		self["menulist"].down()
		self.updateUSBInfo()

	def keyOK(self):
		if not self["menulist"].getCurrent():
			message = _("No USB-device found!\nPlease connect 3G or 4G modem to USB port!")
			printInfo(message)
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO, 5)
			self.close()
		else:
			self.forceStop = False
			if self.isAttemptConnect():
				return
			if self["key_green"].getText() == "Disconnect":
				message = _("Do you want to disconnect?")
				self.session.openWithCallback(self.cbConfirmDone, MessageBox, message, default=False)
				return
			if [x for x in iNetwork.getConfiguredAdapters() if "ppp" in x.lower()]:
				message = _("Another adapter connected has been found.\nA connection is attempted after disconnect all of other device.\n\nDo you want to?")
				self.session.openWithCallback(self.cbConfirmDone, MessageBox, message, default=True)
			else:
				self.cbConfirmDone(True)

	def cbConfirmDone(self, ret):
		if not ret:
			return
		if self["key_green"].getText() == "Connect":
			for x in iNetwork.getConfiguredAdapters():
				if "ppp" in x.lower():
					continue
				iNetwork.setAdapterAttribute(x, "up", False)
				iNetwork.deactivateInterface(x)
		x = self["menulist"].getCurrent()[1]
		if x is None:
			printInfo("no selected device..")
			return
		self["statusText"].setText(_("Accessing modem. Please wait..."))
		self["statusText"].startBlinking()
		self["statusText"].show()
		devFile = "/usr/share/usb_modeswitch/%s:%s" % (self.Vendor, self.ProdID)
		if not exists(devFile):
			self["statusText"].stopBlinking()
			self["statusText"].hide()
			message = _("Can't found device file!\n[%s]\n\nIs this selected USB-device really a Mobile Broadband Device?") % devFile
			printDebug(devFile)
			printInfo(message)
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO, 5)
			return
		if self["key_green"].getText() == "Disconnect":
			cmd = "%s 0" % COMMANDBIN
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbPrintClose)
			cmd = "%s 1" % COMMANDBIN
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbUnloadClose)
			self.taskManager.setStatusCB(self.setDisconnectStatus)
			self["myip"].setText("IP : 0.0.0.0")
			# After Disconnect turn on all adapters and restart network
			networkAdapters = iNetwork.getConfiguredAdapters()
			for x in networkAdapters:
				iNetwork.setAdapterAttribute(x, "up", True)
				iNetwork.activateInterface(x)
			iNetwork.restartNetwork()
		else:
			cmd = "%s 2 vendor=0x%s product=0x%s" % (COMMANDBIN, self.Vendor, self.ProdID)
			self.taskManager.append(cmd, self.cbStep1PrintAvail, self.cbPrintClose)
			cmd = "%s 3 %s %s" % (COMMANDBIN, self.Vendor, self.ProdID)
			# do not save new vendor id and product id changed by usb-switchmode, use only 1st ones ( when no /dev/ttyUSB0 ) - it appears ONLY when it is switched to GSM MODE
			if not fileExists("/dev/ttyUSB0"):
				config.plugins.gmodemmanager.vendorid.setValue(self.Vendor)
				config.plugins.gmodemmanager.productid.setValue(self.ProdID)
				config.plugins.gmodemmanager.vendorid.save()
				config.plugins.gmodemmanager.productid.save()
				printDebug("'Current Connection vendor' and 'product ids' have been saved for future Auto-Connect mode")
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbPrintClose)
			cmd = "%s 4" % COMMANDBIN
			self.taskManager.append(cmd, self.cbStep3PrintAvail, self.cbMakeWvDialClose)
			cmd = "%s 5" % COMMANDBIN
			self.taskManager.append(cmd, self.cbRunWvDialAvail, self.cbPrintClose)
			self.taskManager.setStatusCB(self.setConnectStatus)
		self.taskManager.next()

	def findDeviceInfos(self, info, key):
		if "=" in info:
			found = search(r"%s%s" % (key, "=([A-Za-z0-9]+)"), info)
			return found.group(1) if found else ""
		return info

	def printStatus(self, idx, status):
		message = ""
		self.connectionStatus = idx
		for x in range(len(status)):
			message += "  > " if idx == x else "     "
			message += status[x]
			message += "\n"
		self["statusInfo"].setText(message)

	def setConnectStatus(self, idx):
		self.printStatus(idx, ONSTATUS)

	def setDisconnectStatus(self, idx):
		self.printStatus(idx, OFFSTATUS)

	def cbStep1PrintAvail(self, data):
		if "modules.dep" in data.decode("utf-8", errors="ignore").lower():
			self.forceStop = True

	def cbStep3PrintAvail(self, data):
		if "no modem was detected" in data.decode("utf-8", errors="ignore").lower():
			self.forceStop = True

	def cbPrintAvail(self, data):
		printInfo("cbPrintAvai: %s" % data.decode("utf-8", errors="ignore").strip())

	def cbPrintClose(self, ret):
		if self.forceStop:
			self.executeForcedStop()
		self.taskManager.next()

	def cbUnloadClose(self, ret):
		self.taskManager.clean()
		sleep(1)  # give modem more time, maybe not needed?
		self["key_green"].setText(_("Connect"))
		self.setDisconnectStatus(2)
		self.refreshStatusTimer.start(1000)

	def cbRunWvDialAvail(self, data):
		data = data.decode("utf-8", errors="ignore").strip()
		if data:
			printInfo("cbRunWvDialAvail: %s" % data)
		self.data = data
		datalower = data.lower()
		if "waiting for" in datalower or "bad init" in datalower or "invalid dial" in datalower or "no carrier" in datalower:
			self["statusText"].stopBlinking()
			self["statusText"].hide()
			self.forceStop = True
		elif "pid of pppd:" in datalower:
			self.taskManager.clean()
			sleep(1)  # give modem more time, maybe not needed?
			self["statusText"].stopBlinking()
			self["statusText"].hide()
			self["key_green"].setText(_("Disconnect"))
			self.setConnectStatus(4)
			self.refreshStatusTimer.start(1000)

	def cbMakeWvDialClose(self, ret):
		if self.forceStop:
			self.executeForcedStop()
		info = {}
		if exists(WVDIALFILE):
			for x in open(WVDIALFILE).read().splitlines():
				if x.lower().startswith("modem"):
					printInfo("Modem: '%s'" % x)
					info["Modem"] = x[7:].strip()
				elif x.lower().startswith("init2"):
					printInfo("Init2: '%s'" % x)
					info["Init"] = x[7:].strip()
				elif x.lower().startswith("baud"):
					printInfo("Baud: '%s'" % x)
					info["Baud"] = x[6:].strip()
		else:
			printInfo("WARNING in module 'cbMakeWvDialClose': File not found : %s" % WVDIALFILE)
		if self.apn:
			info["apn"] = self.apn
		if self.uid:
			info["uid"] = self.uid
		if self.pwd:
			info["pwd"] = self.pwd
		if self.pin:
			info["pin"] = self.pin
		if self.phone:
			info["phone"] = self.phone
		self.makeWvDialConf(info)
		self.taskManager.next()

	def executeForcedStop(self):
		self.taskManager.clean()
		sleep(1)  # give modem more time, maybe not needed?
		self.printStatus(-1, ONSTATUS)
		self["statusText"].stopBlinking()
		self["statusText"].hide()
		message = _("Occur error during connection...\n\n%s\n\nPlease check your settings!")
		printInfo("%s\n" % (message % self.data))
		self.session.open(MessageBox, message % self.data, MessageBox.TYPE_INFO)

	def writeConf(self, data, oper=">>"):
		if oper == ">":
			if exists(WVDIALFILE):
				system("mv %s %s.bak" % (WVDIALFILE, WVDIALFILE))
			else:
				printInfo("WARNING in module 'writeConf': File not found : %s" % WVDIALFILE)
		system("echo '%s' %s %s" % (data, oper, WVDIALFILE))

	def makeWvDialConf(self, params):
		baud = params.get("Baud", _("{unknown}"))
		init = params.get("Init", _("{unknown}"))
		modem = params.get("Modem", _("{unknown}"))
		phone = params.get("phone", "*99#")
		apn = params.get("apn", _("{unknown}"))
		uid = params.get("uid", _("{unknown}"))
		pwd = params.get("pwd", _("{unknown}"))
		pin = params.get("pin", _("{unknown}"))
		idxInit = 1
		self.writeConf("", ">")
		self.writeConf("[Dialer modem-start]")
		self.writeConf("Init1 = ATZ+CFUN=1")
		self.writeConf("")
		self.writeConf("[Dialer Defaults]")
		self.writeConf("Modem = %s" % modem)
		self.writeConf("Baud = %s" % baud)
		self.writeConf("Modem = /dev/ttyUSB0")
		self.writeConf("Baud = 57600")
		self.writeConf("Init%d = ATE1" % idxInit)
		idxInit += 1
		if pin:
			self.writeConf("Init%d = AT+CPIN=%s" % (idxInit, pin))
			idxInit += 1
		self.writeConf("Init%d = %s" % (idxInit, init))
		idxInit += 1
		if not apn and not uid and not pwd and not pin:
			self.writeConf("Init%d = AT&F" % idxInit)
			idxInit += 1
		if apn:
			self.writeConf('Init%d = AT+CGDCONT=1,"IP","%s"' % (idxInit, apn))
			idxInit += 1
		self.writeConf("Init%d = AT+CFUN=1" % idxInit)
		self.writeConf("Dial Command = ATD")
		self.writeConf("Username = %s" % uid)
		self.writeConf("Password = %s" % pwd)
		self.writeConf("Phone = %s" % phone)  # standard: *99#
		self.writeConf("Modem Type = Analog Modem")
		self.writeConf("Stupid mode = yes")
		self.writeConf("ISDN = 0")
		self.writeConf("Carrier Check = 0")
		self.writeConf("Abort on No Dialtone = 0")
		self.writeConf("Auto DNS = 0")
		message = open(WVDIALFILE).read() if exists(WVDIALFILE) else "WARNING in module 'makeWvDialConf': File not found : '%s'" % WVDIALFILE
		printDebug(message)

	def updateUSBInfo(self):
		if self["menulist"].getCurrent():
			x = self["menulist"].getCurrent()[1]
			self.Vendor = self.findDeviceInfos(x.get("Vendor", ""), "Vendor")
			self.ProdID = self.findDeviceInfos(x.get("ProdID", ""), "ProdID")
			if not self.ProdID:
				self.ProdID = self.findDeviceInfos(x.get("Vendor", ""), "ProdID")
			printInfo("Found Vendor '%s', ProdID '%s'" % (self.Vendor, self.ProdID))
			info = "Vendor : %s\nProdID : %s\nAPN : %s\nUser : %s\nPassword : %s\nPin : %s\nPhone : %s" % (self.Vendor, self.ProdID, self.apn, self.uid, self.pwd, self.pin, self.phone)
			self["usbinfo"].setText(info)

	def setListOnView(self):
		items = []
		for x in self.getUSBList():
			items.append((x.get("Product"), x))
		self["menulist"].setList(items)
		self.updateUSBInfo()
		self["statusText"].stopBlinking()
		self["statusText"].hide()

	def getUSBList(self):
		kernel_ver = about.getKernelVersionString()
		parsed_usb_list = []
		cmd = "cat /proc/bus/usb/devices" if kernel_ver <= "3.0.0" else "/usr/bin/usb-devices"
		usb_devices = popen(cmd).read()
		tmp_device = {}
		for x in usb_devices.splitlines():
			if x is None or len(x) == 0:
				printDebug("TMP DEVICE : [%s]" % tmp_device)
				if len(tmp_device):
					parsed_usb_list.append(tmp_device)
				tmp_device = {}
				continue
			try:
				if x[0] in ("P", "S", "I", "T"):
					tmp = x[2:].strip()
					printDebug("TMP : [%s]" % tmp)
					if tmp.lower().startswith("bus"):
						printDebug("TMP SPLIT for BUS : %s" % tmp.split())
						for xx in tmp.split():
							if xx.lower().startswith("bus"):
								tmp_device["Bus"] = xx[4:]
								break
					if tmp.lower().startswith("manufacturer"):
						tmp_device["Manufacturer"] = tmp[13:]
					if tmp.lower().startswith("product"):
						tmp_device["Product"] = tmp[8:]
					elif tmp.lower().startswith("serialnumber"):
						tmp_device["SerialNumber"] = tmp[13:]
					elif tmp.lower().startswith("vendor"):
						printDebug("TMP SPLIT for BUS : %s" % tmp.split())
						for xx in tmp.split():
							if xx.lower().startswith("vendor"):
								tmp_device["Vendor"] = xx[7:]
							elif xx.lower().startswith("prodid"):
								tmp_device["ProdID"] = xx[7:]
						tmp_device["Vendor"] = tmp
					elif "driver" in tmp.lower():
						d = tmp[tmp.lower().find("driver") + 7:]
						if d != "(none)":
							tmp_device["Interface"] = d
			except Exception as err:
				printInfo("Exception in module 'getUSBList1' %s" % err)
		if len(tmp_device):
			parsed_usb_list.append(tmp_device)
		printDebug("PARSED DEVICE LIST : %s" % parsed_usb_list)
		rt_usb_list = []
		for x in parsed_usb_list:
			printDebug("Looking >> %s" % x)
			try:
				xx = x.get("Interface")
				if xx and xx.lower().startswith("usb"):
					rt_usb_list.append(x)
			except Exception as err:
				printInfo("Exception in module 'getUSBList2' %s" % err)
				printInfo("USB DEVICE LIST : %s" % rt_usb_list)
		if not rt_usb_list:
			self.keyOK()
			printInfo("USB DEVICE LIST : 'No USB-device found!'")
		return rt_usb_list


def autostart(reason, **kwargs):
	vendorid = config.plugins.gmodemmanager.vendorid.value
	productid = config.plugins.gmodemmanager.productid.value
	if reason == 0:
		if isConnected():
			args = ("%s 0;" % COMMANDBIN) + ("%s 1" % COMMANDBIN)
			is_running = True
		else:
			args = ("%s 2 vendor=0x%s product=0x%s;" % (COMMANDBIN, vendorid, productid)) + ("%s 3 %s %s;sleep 8;" % (COMMANDBIN, vendorid, productid)) + ("%s 5" % COMMANDBIN)
			is_running = False
		cmd = args
		if config.plugins.gmodemmanager.autostart.value:
			printInfo("AUTOSTART")
			if is_running:
				printInfo("already started")
			else:
				printInfo("starting ...")
				system(cmd)
				printInfo("disable all others network adapters ...")
				system("ifconfig eth0 down")
		elif config.plugins.gmodemmanager.autostart.value is False and is_running is True:
				printInfo("stopping ...")
				system(cmd)
				printInfo("disable all others network adapters ...")
				system("ifconfig eth0 up")


def main(session, **kwargs):
	session.open(ModemManager)


def Plugins(**kwargs):
	return [PluginDescriptor(name="3G/4G Modem Manager", icon="plugin.png", description=_("Management of 3G/4G USB-modems"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART], fnc=autostart)]

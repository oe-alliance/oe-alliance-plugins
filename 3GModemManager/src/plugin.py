from Plugins.Plugin import PluginDescriptor

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Components.Label import Label
from Components.Sources.Boolean import Boolean
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.Network import iNetwork
from Components.MenuList import MenuList
from Components.config import config, getConfigListEntry, ConfigInteger, ConfigSubsection, ConfigSelection, ConfigText, ConfigYesNo, NoSave, ConfigNothing
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.About import about

from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN, fileExists

from enigma import eTimer, eConsoleAppContainer, eSocketNotifier, getDesktop
from select import POLLIN, POLLPRI
from xml.sax import make_parser, handler
import os, socket, time


debug_mode_modem_mgr = False
def printDebugModemMgr(msg):
	global debug_mode_modem_mgr
	if debug_mode_modem_mgr:
		print "[ModemManager Plugin] Debug >>", msg

def printInfoModemMgr(msg):
	print "[ModemManager Plugin] Info >>", msg

isEmpty = lambda x: x is None or len(x)==0

class DeviceEventListener:
	notifyCallbackFunctionList = []
	def __init__(self):
		self.sock = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, 15)
		try:		
			self.sock.bind((os.getpid(), 1))
			self.notifier = eSocketNotifier(self.sock.fileno(), POLLIN|POLLPRI)
			self.notifier.callback.append(self.cbEventHandler)
		except Exception, msg:
			print "[ModemManager Plugin] Error >>", msg
			self.sock.close()

	def cbEventHandler(self, sockfd):
		recv = self.sock.recv(65536)
		#printDebugModemMgr(str(recv.splitlines()))
		if recv.startswith("add@/block") or recv.startswith("remove@/block"):
			for x in self.notifyCallbackFunctionList:
				try: 	x(recv)
				except:	self.notifyCallbackFunctionList.remove(x)

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
		except: pass

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
		printInfoModemMgr("set task error!!")
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
			printInfoModemMgr("can't run task!!")
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

		printInfoModemMgr("prepared command :%s"%(command))
		self.gTaskInstance.execute(command)
		self.taskIdx += 1
		return True

class ParserHandler(handler.ContentHandler):
	nodeList = []
	def __init__(self):
		self.nodeList = []
	def startDocument(self):
		pass
	def endDocument(self):  
		pass
	def startElement(self, name, attrs):
		if name == 'apn':
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

class EditModemManual(ConfigListScreen, Screen):
	skin = 	"""
		<screen position="center,center" size="600,360" title="3G Modem Manager Config Edit">
			<widget name="config" zPosition="2" position="0,0" size="600,300" scrollbarMode="showOnDemand" transparent="1" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="5,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,320" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="5,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="455,320" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#18188b"  foregroundColor="#ffffff" transparent="1" />

			<widget source="VKeyIcon" render="Pixmap" pixmap="skin_default/buttons/key_text.png" position="50,200" zPosition="10" size="35,25" transparent="1" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="160,300" zPosition="1" size="1,1" transparent="1" alphatest="on" />
		</screen>
		""" 
		
	def __init__(self, session, cbFuncClose, uid=None, pwd=None, pin=None, apn=None, phone='*99#', isAdd=False):
		Screen.__init__(self, session)
		self.cbFuncClose, self.isAdd = cbFuncClose, isAdd

		if isAdd:
			self.uid,self.pwd,self.pin,self.apn,self.phone = "","","","",""
		else:
			self.uid,self.pwd,self.pin,self.apn,self.phone = uid,pwd,pin,apn,phone
			if self.uid is None: self.uid = ""
			if self.pwd is None: self.pwd = ""
			if self.pin is None: self.pin = ""
			if self.apn is None: self.apn = ""
			if self.phone is None: self.phone = ""

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions",],
		{
			"ok":     self.keyOK,
			"cancel": self.keyExit,
			"red":    self.keyExit,
			"green":  self.keyOK,
			"blue":   self.keyRemove,
		}, -2)

		self["VirtualKB"] = ActionMap(["VirtualKeyboardActions" ],
		{
			"showVirtualKeyboard": self.KeyText,
		}, -1)

		self.configList = []
		ConfigListScreen.__init__(self, self.configList, session=session)
		self.createConfigList()

		self["key_red"]    = StaticText(_("Cancel"))
		self["key_green"]  = StaticText(_("Save"))
		self["key_blue"]   = StaticText(_(self.isAdd and " " or "Remove"))
		self["VKeyIcon"]   = Boolean(False)
		self["HelpWindow"] = Pixmap()
		self["VirtualKB"].setEnabled(False)
		if self.isAdd:
			self.setTitle("3G Modem Manager Config Add")

	def createConfigList(self):
		self.configRegion   = ConfigText(default="", visible_width=50, fixed_size=False)
		self.configName     = ConfigText(default="", visible_width=50, fixed_size=False)
		self.configUserName = ConfigText(default=str(self.uid), visible_width=50, fixed_size=False)
		self.configPassword = ConfigText(default=str(self.pwd), visible_width=50, fixed_size=False)
		self.configAPN      = ConfigText(default=str(self.apn), visible_width=50, fixed_size=False)
		self.configPIN      = ConfigText(default=str(self.pin), visible_width=50, fixed_size=False)
		self.configPhone    = ConfigText(default=str(self.phone), visible_width=50, fixed_size=False)

		self.configEntryRegion   = getConfigListEntry(_("Region :"),     self.configRegion)
		self.configEntryName     = getConfigListEntry(_("Name :"),     self.configName)
		self.configEntryUserName = getConfigListEntry(_("User :"),     self.configUserName)
		self.configEntryPassword = getConfigListEntry(_("Password :"), self.configPassword)
		self.configEntryAPN      = getConfigListEntry(_("APN :"),      self.configAPN)
		self.configEntryPIN      = getConfigListEntry(_("PIN :"),      self.configPIN)
		self.configEntryPhone    = getConfigListEntry(_("Phone :"),    self.configPhone)

		if self.isAdd:
			self.configList.append(self.configEntryRegion)
			self.configList.append(self.configEntryName)
		self.configList.append(self.configEntryUserName)
		self.configList.append(self.configEntryPassword)
		self.configList.append(self.configEntryAPN)
		self.configList.append(self.configEntryPIN)
		self.configList.append(self.configEntryPhone)

		self["config"].list = self.configList
		self["config"].l.setList(self.configList)

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
			if isEmpty(currentItemValue):
				currentItemValue = ""
		self.session.openWithCallback(self.cbKeyText, VirtualKeyBoard, title=("Please input here"), text=currentItemValue)

	def cbKeyText(self, data=None):
		if data is not None:
			currentItem = self.getCurrentItem()
			if currentItem is not None:
				currentItem.setValue(data)

	def keyExit(self):
		self.close()

	def keyRemove(self):
		if self.isAdd:
			return
		if self.cbFuncClose is not None:
			self.cbFuncClose(isRemove = True)
		self.close()

	def showKeyboard(self, ret=None):
		self["VKeyIcon"].boolean = True
		current = self["config"].getCurrent()
		if hasattr(current[1], 'help_window'):
			if current[1].help_window.instance is not None:
				current[1].help_window.instance.show()

	def hideKeyboard(self):
		self["VKeyIcon"].boolean = False
		current = self["config"].getCurrent()
		if hasattr(current[1], 'help_window'):
			if current[1].help_window.instance is not None:
				current[1].help_window.instance.hide()

	def keyOK(self):
		message = '%s field is empty!!'
		if isEmpty(self.configRegion.value) and self.isAdd:
			self.hideKeyboard()
			self.session.openWithCallback(self.showKeyboard, MessageBox, message%('Region'), MessageBox.TYPE_INFO)
			return
		if isEmpty(self.configName.value) and self.isAdd:
			self.hideKeyboard()
			self.session.openWithCallback(self.showKeyboard, MessageBox, message%('Name'), MessageBox.TYPE_INFO)
			return
		if isEmpty(self.configAPN.value):
			self.hideKeyboard()
			self.session.openWithCallback(self.showKeyboard, MessageBox, message%('APN'), MessageBox.TYPE_INFO)
			return

		if self.cbFuncClose is not None:
			self.uid   = self.configUserName.value
			self.pwd   = self.configPassword.value
			self.pin   = self.configPIN.value
			self.apn   = self.configAPN.value
			self.phone = self.configPhone.value
			self.name  = self.isAdd and self.configName.value or None
			self.region  = self.isAdd and self.configRegion.value or None
			self.cbFuncClose(self.uid,self.pwd,self.pin,self.apn,self.phone,self.name,self.region)
		self.close()


config.plugins.gmodemmanager = ConfigSubsection()
config.plugins.gmodemmanager.autostart = ConfigYesNo(default = False)
config.plugins.gmodemmanager.vendorid = ConfigText(default = "0000" )
config.plugins.gmodemmanager.productid = ConfigText(default = "0000")
config.plugins.gmodemmanager.apn = ConfigText(default = "apn")
config.plugins.gmodemmanager.uid = ConfigText(default = "user")
config.plugins.gmodemmanager.pwd = ConfigText(default = "pass")
config.plugins.gmodemmanager.pin = ConfigText(default = "")
config.plugins.gmodemmanager.phone = ConfigText(default = "*99#")

class ModemManual(Screen):
	skin = 	"""
		<screen position="center,center" size="600,360" title="3G Modem Manager Config">
			<widget name="menulist" position="0,0" size="300,300" backgroundColor="#000000" zPosition="10" scrollbarMode="showOnDemand" />
			<widget name="apnInfo" position="310,0" size="290,300" font="Regular;20" halign="left" backgroundColor="#a08500" transparent="1" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="5,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,320" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="5,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,320" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#a08500"  foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="455,320" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#18188b"  foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, session, cbFuncClose, uid=None, pwd=None, pin=None, apn=None, phone='*99#'):
		Screen.__init__(self, session)
		self.cbFuncClose,self.uid,self.pwd,self.pin,self.apn,self.phone = cbFuncClose,uid,pwd,pin,apn,phone
		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions"],
		{
			"ok":     self.keyOK,
			"cancel": self.keyExit,
			"red":    self.keyExit,
			"green":  self.keyOK,
			"yellow": self.keyEdit,
			"blue":   self.keyAdd,
			"left":   self.keyLeft,
			"right":  self.keyRight,
			"up":     self.keyUp,
			"down":   self.keyDown,
		}, -2)

		self.apnItems = self.setListOnView()
		self["menulist"]   = MenuList(self.apnItems)
		self["key_red"]    = StaticText(_("Cancel"))
		self["key_green"]  = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"]   = StaticText(_("Add"))
		self["apnInfo"]    = Label(' ')

		self.keyUp()
	
	def keyAdd(self):
		self.session.open(EditModemManual, self.cb3GManualSetting, isAdd=True)

	def keyEdit(self):
		self.session.open(EditModemManual, self.cb3GManualSetting, self.uid,self.pwd,self.pin,self.apn,self.phone)

	def cb3GManualSetting(self, uid=None, pwd=None, pin=None, apn=None, phone='*99#', name=None, region=None, isRemove=False):
		if not isRemove:
			self.uid = isEmpty(uid) and "" or uid
			self.pwd = isEmpty(pwd) and "" or pwd
			self.pin = isEmpty(pin) and "" or pin
			self.apn = isEmpty(apn) and "" or apn
			self.phone = isEmpty(phone) and "" or phone
			
		if name is not None:
			self["menulist"].list.append((name, {'region':region, 'carrier':name, 'apn':self.apn, 'user':self.uid, 'password':self.pwd, 'pin':self.pin, 'phone':self.phone}))
			self["menulist"].setList(self["menulist"].list)
			self["menulist"].moveToIndex(len(self["menulist"].list)-1)
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
			name = ' '
		if not isRemove and isEmpty(name):
			self.updateAPNList()
		self.updateAPNInfo()
		self.saveAPNList(name)

	def updateAPNList(self):
		selectedIndex = self["menulist"].getSelectionIndex()
		apnList = self["menulist"].list
		currentListItem = apnList[selectedIndex][1]

		currentListItem['user'] = self.uid
		currentListItem['apn'] = self.apn
		currentListItem['password'] = self.pwd
		currentListItem['pin'] = self.pin
		currentListItem['phone'] = self.phone

		self["menulist"].setList(apnList)

	def saveAPNList(self, name=None):
		apnList = self["menulist"].list
		selectedIndex = self["menulist"].getSelectionIndex()

		def makeItem(region, carrier, apn, user, password, pin, phone):
			printDebugModemMgr("%s, %s, %s, %s, %s, %s, %s"%(region, carrier, apn, user, password, pin, phone))
			tempStr  = '    <apn'
			tempStr += ' region="%s"'%(region)
			tempStr += ' carrier="%s"'%(carrier)
			tempStr += ' apn="%s"'%(apn)
			if not isEmpty(user):	  tempStr += ' user="%s"'%(user)
			if not isEmpty(password): tempStr += ' password="%s"'%(password)
			if not isEmpty(pin):	  tempStr += ' pin="%s"'%(pin)
			if not isEmpty(phone) :	  tempStr += ' phone="%s"'%(phone)
			tempStr += ' />\n'
			return tempStr

		tempIndex = 0
		apnString = '<apns version="1">\n'
		for x in apnList:
			try:
				if selectedIndex == tempIndex and name is None:
					apnString += makeItem(x[0], self.region, self.apn, self.uid, self.pwd, self.pin, self.phone)
					continue
				apnString += makeItem(x[1].get('region'), x[1].get('carrier'), x[1].get('apn'), x[1].get('user'), x[1].get('password'), x[1].get('pin'), x[1].get('phone'))
			finally: tempIndex += 1
		apnString += '</apns>\n'
		printDebugModemMgr(apnString)
		apnListFile = file(resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/3GModemManager/apnlist.xml"), 'w')
		apnListFile.write(apnString)
		apnListFile.close()

	def keyLeft(self):
		self['menulist'].pageUp()
		self.setAPNInfo()

	def keyRight(self):
		self['menulist'].pageDown()
		self.setAPNInfo()

	def keyUp(self):
		self['menulist'].up()
		self.setAPNInfo()

	def keyDown(self):
		self['menulist'].down()
		self.setAPNInfo()

	def keyOK(self):
		if self.cbFuncClose is not None:
			config.plugins.gmodemmanager.apn.setValue(str(self.apn))
			config.plugins.gmodemmanager.uid.setValue(str(self.uid))
			config.plugins.gmodemmanager.pwd.setValue(str(self.pwd))
			config.plugins.gmodemmanager.pin.setValue(str(self.pin))
			config.plugins.gmodemmanager.phone.setValue(str(self.phone))
			config.plugins.gmodemmanager.apn.save()
			config.plugins.gmodemmanager.uid.save()
			config.plugins.gmodemmanager.pwd.save()
			config.plugins.gmodemmanager.pin.save()
			config.plugins.gmodemmanager.phone.save()
			config.plugins.gmodemmanager.save()
			self.cbFuncClose(self.uid,self.pwd,self.pin,self.apn,self.phone)
		self.close()

	def keyExit(self):
		os.system("chattr -i /etc/ppp/resolv.conf;chattr -i /etc/resolv.conf")
		self.close()

	def setAPNInfo(self, noUpdate=False):
		try:
			x = self["menulist"].getCurrent()[1]
			self.region, self.apn, self.uid, self.pwd, self.pin, self.phone = x.get("region"), x.get("apn"), x.get("user"), x.get("password"), x.get('pin'), x.get('phone')
		except Exception, err: pass
		if noUpdate: return
		self.updateAPNInfo()

	def updateAPNInfo(self):
		region,apn,uid,pwd,pin,phone = self.region, self.apn,self.uid,self.pwd,self.pin,self.phone
		if region is None: region = ""
		if apn is None:   apn = ""
		if uid is None:   uid = ""
		if pwd is None:   pwd = ""
		if pin is None:   pin = ""
		if phone is None: phone = ""
		info = 'REGION : %s\nAPN : %s\nUSER : %s\nPASSWD : %s\nPIN : %s\nPHONE : %s\n' % (region, apn, uid, pwd, pin, phone)
		self["apnInfo"].setText(info)

	def setListOnView(self):
		lvApnItems = []
		def uppercaseCompare(a,b):
			aa = a.get("carrier")
			bb = b.get("carrier")
			if isEmpty(aa): aa = ""
			if isEmpty(bb): bb = ""
			return cmp(aa.upper(),bb.upper())
		def isExistAPN(name):
			for x in lvApnItems:
				if x[0] == name:
					return True
			return False
		try:
			handle = ParserHandler()
			parser = make_parser()
			parser.setContentHandler(handle)
			parser.parse(resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/3GModemManager/apnlist.xml"))

			apnList = handle.getNodeList()
			apnList.sort(uppercaseCompare)
			for x in apnList:
				name = str(x.get('carrier'))
				if isEmpty(name):
					continue
				if isExistAPN(name):
					continue
				d = {}
				d['carrier']  = name
				d['region']   = x.get('region')
				d['apn']      = x.get('apn')
				d['user']     = x.get('user')
				d['password'] = x.get('password')
				d['pin']      = x.get('pin')
				d['phone']    = x.get('phone')
				lvApnItems.append((name,d))
		except Exception, err: pass
		finally: del handle
		return lvApnItems


commandBin = resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/3GModemManager/3gcommand")

def isConnected():
	return len(os.popen('ifconfig -a | grep ppp').read().strip()) > 0

class ModemManager(Screen):
	skin = 	"""
		<screen position="center,center" size="600,460" title="3G Modem Manager">
			<widget name="menulist" position="0,0" size="300,150" backgroundColor="#000000" zPosition="10" scrollbarMode="showOnDemand" />
			<widget name="usbinfo" position="310,0" size="290,150" font="Regular;18" halign="left" />

			<widget name="statusTitle" position="0,160" size="600,120" font="Regular;20" halign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="statusInfo" position="0,185" size="600,120" font="Regular;20" halign="left" backgroundColor="#a08500" transparent="1" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="5,420" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,420" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,420" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,420" size="140,40" alphatest="on" />

			<widget name="myip" position="50,320" size="600,120" font="Regular;20" halign="left" backgroundColor="#a08500" transparent="1" />
			
			<widget name="autostart_text" position="50,360" size="200,120" font="Regular;20" halign="left" backgroundColor="#a08500" transparent="1" />
			<widget name="autostart_stop" position="190,357" size="100,30" font="Regular;20" valign="center"  halign="center" backgroundColor="red"/>
			<widget name="autostart_start" position="190,357" size="100,30" zPosition="1" font="Regular;20" valign="center"  halign="center" backgroundColor="green"/>
			
			<widget source="key_red" render="Label" position="5,420" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,420" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,420" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#a08500"  foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="455,420" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#18188b"  foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""
	uid,pwd,pin,apn,phone = None,None,None,None, '*99#'
	connectionStatus = 0
	def __init__(self, session): 
		Screen.__init__(self, session)
		self.usb_lv_items = self.setListOnView()

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions"],
		{
			"ok":     self.keyOK,
			"cancel": self.keyExit,
			"red":    self.keyExit,
			"green":  self.keyOK,
			"yellow": self.keyManual,
			"blue":   self.keyAutoConnect,
			"up":     self.keyUp,
			"down":   self.keyDown,
			"left":   self.keyLeft,
			"right":  self.keyRight,
			"0":      self.keyNumber,
		}, -2)
		self["menulist"] = MenuList(self.usb_lv_items)
		self['usbinfo'] = Label(' ')
		self['statusTitle'] = Label('[ Status ]')
		self['statusInfo'] = Label(' ')
		self['myip']= Label(' ')
		self['autostart_text'] = Label(_("Auto connect:"))
		self['autostart_stop'] = Label(_("Disable"))
		self['autostart_start'] = Label(_("Enable"))
		
		self["key_red"] = StaticText(_("Exit"))
		if isConnected():
			self["key_green"] = StaticText("Disconnect")
			self.setDisconnectStatus(0)
		else:
			self["key_green"] = StaticText("Connect")
			self.setConnectStatus(0)
			
		self["key_yellow"] = StaticText(_("Manual"))
		self["key_blue"] = StaticText(_("Auto connect"))

		self.updateUSBInfo()

		self.udevListener = DeviceEventListener()
		self.udevListener.addCallback(self.cbUdevListener)

		self.taskManager = TaskManager()

		self.refreshStatusTimer = eTimer()
		self.refreshStatusTimer.callback.append(self.cbRefreshStatus)

		if config.plugins.gmodemmanager.autostart.value:
			self['autostart_stop'].hide()
			self['autostart_start'].show()
		else:
			self['autostart_stop'].show()
			self['autostart_start'].hide()
			
		#self.restartAppTimer = eTimer()
		#self.restartAppTimer.callback.append(self.cbRestartAppTimer)
		self.forceStop = False
		self.GetIP()
		
	def GetIP(self):
		if self["key_green"].getText() == 'Disconnect':
		  os.system('killall -9 wget')
		  cmd = str('wget -q -O - http://checkip.dyndns.org | grep "html" | cut -d" " -f6  | cut -d"<" -f1')
		  res = os.popen(cmd).read()
		  self['myip'].setText(_('IP : ' + str(res)))
		else:
		  self['myip'].setText(_('IP : 0.0.0.0'))
		  
		
	def cbRestartAppTimer(self):
		self.restartAppTimer.stop()
		file = open('/proc/stb/info/vumodel')
		model = file.read().strip()
		file.close()
		if model is not None:
			if model == 'solo' or model == 'bm750':
				self.session.open(TryQuitMainloop, 3)

	def cbRefreshStatus(self):
		self.refreshStatusTimer.stop()
		if self["key_green"].getText() == 'Connect':
			self.setConnectStatus(0)
			self.GetIP()
		elif self["key_green"].getText() == 'Disconnect': 
			self.setDisconnectStatus(0)
			self.GetIP()

	def cbUdevListener(self, data):
		printDebugModemMgr('Udev Listener Refresh!!')
		time.sleep(2)
		self["menulist"].setList(self.setListOnView())
		self.updateUSBInfo()

	def isAttemptConnect(self):
		if self.connectionStatus == 0 or self.forceStop:
			return False
		maxIdx = 4
		if self["key_green"].getText() == 'Disconnect':
			maxIdx = 2
		if self.connectionStatus < maxIdx:
			printInfoModemMgr("can't excute a command during connecting...")
			return True
		return False

	def keyManual(self):
		if self.isAttemptConnect():
			return
		self.session.open(ModemManual, self.cb3GManualSetting, self.uid,self.pwd,self.pin,self.apn,self.phone)

	def disableAutoConnect(self, answer):
		if answer is True:
				config.plugins.gmodemmanager.autostart.setValue(False)
				config.plugins.gmodemmanager.vendorid.setValue("0000")
				config.plugins.gmodemmanager.productid.setValue("0000")
				config.plugins.gmodemmanager.vendorid.save()
				config.plugins.gmodemmanager.productid.save()
				config.plugins.gmodemmanager.autostart.save()
				self['autostart_stop'].show()
				self['autostart_start'].hide()
				
	def keyAutoConnect(self):
		## AUTOSTART
		if isConnected():
			if not config.plugins.gmodemmanager.autostart.value:
				config.plugins.gmodemmanager.autostart.setValue(True)
				config.plugins.gmodemmanager.vendorid.save()
				config.plugins.gmodemmanager.productid.save()
				config.plugins.gmodemmanager.autostart.save()
				self['autostart_stop'].hide()
				self['autostart_start'].show()
				message = "3G Modem Manager will connect automaticlly on boot"
				self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO,5)
			else:
				message = "3G Modem Manager is already in autoconnect mode on startup.\nWould You like to disable auto connect on startup ?"
				self.session.openWithCallback(self.disableAutoConnect, MessageBox, message, MessageBox.TYPE_YESNO)
		elif not isConnected() and config.plugins.gmodemmanager.autostart.value:
			message = "3G Modem Manager is already in autoconnect mode on startup.\nWould You like to disable auto connect on startup ?"
			self.session.openWithCallback(self.disableAutoConnect, MessageBox, message, MessageBox.TYPE_YESNO)		  
		else:
			message = "Please connect before enable autoconnect on startup!"
			self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO,5)

	def cb3GManualSetting(self, uid=None, pwd=None, pin=None, apn=None, phone='*99#'):
		self.uid,self.pwd,self.pin,self.apn,self.phone = uid,pwd,pin,apn,phone
		self.updateUSBInfo()

	def keyNumber(self, num=None):
		global debug_mode_modem_mgr
		debug_mode_modem_mgr = not debug_mode_modem_mgr
		printInfoModemMgr('changed log mode, debug %s'%(debug_mode_modem_mgr and 'on' or 'off'))

	def keyExit(self):
		if self.isAttemptConnect():
			message = "Can't disconnect doring connecting..\nDo you want to forcibly exit?"
			self.session.openWithCallback(self.cbForciblyExit, MessageBox, _(message), default = False)
			return
		self.udevListener.close()
		self.close()

	def cbForciblyExit(self, result):
		if result:
			os.system('%s -s 1' % commandBin)
			os.system('%s -s 2' % commandBin)
			os.system('%s -s 6' % commandBin)
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
		if len(self.usb_lv_items) < 1:
			message = "Please connect 3G or 4G modem to USB port!"
			self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO,5)
			self.close()
		else:
			self.forceStop = False
			if self.isAttemptConnect():
				return

			def areadyExistAnotherAdapter():
				networkAdapters = iNetwork.getConfiguredAdapters()
				for x in networkAdapters:
					if x[:3] != 'ppp':
						return True
				return False

			if self["key_green"].getText() == 'Disconnect':
				message = "Do you want to disconnect?"
				self.session.openWithCallback(self.cbConfirmDone, MessageBox, _(message), default = False)
				return

			if areadyExistAnotherAdapter():
				message = "Another adapter connected has been found.\n\nA connection is attempted after disconnect all of other device. Do you want to?"
				self.session.openWithCallback(self.cbConfirmDone, MessageBox, _(message), default = True)
			else:	self.cbConfirmDone(True)

	def cbConfirmDone(self, ret):
		if not ret: return
		if self["key_green"].getText() == 'Connect':
			networkAdapters = iNetwork.getConfiguredAdapters()
			for x in networkAdapters:
				if x[:3] == 'ppp': continue
				iNetwork.setAdapterAttribute(x, "up", False)
				iNetwork.deactivateInterface(x)

		x = {}
		try: x = self["menulist"].getCurrent()[1]
		except:
			printInfoModemMgr('no selected device..')
			return

		devFile = '/usr/share/usb_modeswitch/%s:%s' % (x.get("Vendor"), x.get("ProdID"))
		if not os.path.exists(devFile) :
			message = "Can't found device file!! [%s]" % (devFile)
			printInfoModemMgr(message)
			#self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO)
			return

		if self["key_green"].getText() == 'Disconnect':
			cmd = "%s 0" % (commandBin)
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbPrintClose)

			cmd = "%s 1" % (commandBin)
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbUnloadClose)
			self.taskManager.setStatusCB(self.setDisconnectStatus)
			
			self['myip'].setText(_('IP : 0.0.0.0'))
			
			# After Disconnect turn on all adapters and restart network
			networkAdapters = iNetwork.getConfiguredAdapters()
			for x in networkAdapters:
				iNetwork.setAdapterAttribute(x, "up", True)
				iNetwork.activateInterface(x)
			
			iNetwork.restartNetwork()	

		else:
			cmd = "%s 2 vendor=0x%s product=0x%s" % (commandBin, x.get("Vendor"), x.get("ProdID"))
			self.taskManager.append(cmd, self.cbStep1PrintAvail, self.cbPrintClose)

			cmd = "%s 3 %s %s" % (commandBin, x.get("Vendor"), x.get("ProdID"))

			# do not save new vendor id and product id changed by usb-switchmode, use only 1st ones ( when no /dev/ttyUSB0 ) - it appears ONLY when it is switched to GSM MODE 
			if not fileExists("/dev/ttyUSB0"):
				# SAVE Current Connection vendor and product ids for future Auto-Connect mode
				config.plugins.gmodemmanager.vendorid.setValue(x.get("Vendor"))
				config.plugins.gmodemmanager.productid.setValue(x.get("ProdID"))
				config.plugins.gmodemmanager.vendorid.save()
				config.plugins.gmodemmanager.productid.save()
			
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbPrintClose)

			cmd = "%s 4" % (commandBin)
			self.taskManager.append(cmd, self.cbStep3PrintAvail, self.cbMakeWvDialClose)

			cmd = "%s 5" % (commandBin)
			self.taskManager.append(cmd, self.cbRunWvDialAvail, self.cbPrintClose)
			self.taskManager.setStatusCB(self.setConnectStatus)
		
		self.taskManager.next()

	def printStatus(self, idx, STATUS):
		message = ''
		self.connectionStatus = idx
		for x in range(0,len(STATUS)):
			if idx == x:
				message += '  > '
			else: 	message += '      '
			message += STATUS[x]
			message += '\n'
		self['statusInfo'].setText(message)

	def setConnectStatus(self, idx):
		STATUS = {
		 0:'1. Load a Mobile Broadband Device'
		,1:'2. Set up a Mobile Broadband Device'
		,2:'3. Generate a WvDial profile'
		,3:'4. Attempt to connect'
		,4:'5. Done'
		}
		self.printStatus(idx, STATUS)

	def setDisconnectStatus(self, idx):
		STATUS = {
		 0:'1. Drop WvDial'
		,1:'2. Unload a Mobile Broadband Device'
		,2:'3. Done'
		}
		self.printStatus(idx, STATUS)

	def cbStep1PrintAvail(self, data):
		print data
		if data.find('modules.dep') > -1:
			self.forceStop = True

	def cbStep3PrintAvail(self, data):
		print data
		if data.find('no modem was detected') > -1:
			self.forceStop = True

	def cbPrintAvail(self, data):
		print data

	def cbPrintClose(self, ret):
		if self.forceStop:
			self.taskManager.clean()
			time.sleep(2)
			message = "Occur error during connection...\nPlease, Check your setting!!"
			self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO)
			return
		self.taskManager.next()

	def cbUnloadClose(self, ret):
		self.taskManager.clean()
		time.sleep(2)
		self["key_green"].setText('Connect')
		self.setDisconnectStatus(2)
		self.refreshStatusTimer.start(1000)

	def cbRunWvDialAvail(self, data):
		print data
		if data.find('Bad init') > -1 or data.find('Invalid dial') > -1 or data.find('No Carrier') > -1:
			self.forceStop = True
			return
		if data.find('Pid of pppd:') > -1:
			self.taskManager.clean()
			time.sleep(2)
			self["key_green"].setText('Disconnect')
			self.setConnectStatus(4)
			self.refreshStatusTimer.start(1000)
			#self.restartAppTimer.start(3000)

	def cbMakeWvDialClose(self, ret):
		if self.forceStop:
			self.taskManager.clean()
			time.sleep(2)
			message = "Occur error during connection...\nPlease, Check your setting!!"
			self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO)
			return

		info = {}
		try:
			datalist = file('/etc/wvdial.conf').read().splitlines()
			for x in datalist:
				if x.startswith('Modem ='):
					print x
					info['Modem'] = x[7:].strip()
				elif x.startswith('Init2 ='):
					print x
					info['Init'] = x[7:].strip()
				elif x.startswith('Baud ='):
					print x
					info['Baud'] = x[6:].strip()
		except Exception, err: 
			printDebugModemMgr("getModemInfo Error : [%s]" % (str(err)))
			# TODO : occur error!!
			return

		if not isEmpty(self.apn):   info['apn']   = self.apn
		if not isEmpty(self.uid):   info['uid']   = self.uid
		if not isEmpty(self.pwd):   info['pwd']   = self.pwd
		if not isEmpty(self.pin):   info['pin']   = self.pin
		if not isEmpty(self.phone): info['phone'] = self.phone

		self.makeWvDialConf(info)
		self.taskManager.next()

	def writeConf(self, data, oper='>>'):
		confFile = '/etc/wvdial.conf'
		if oper == '>':
			os.system('mv %s %s.bak' % (confFile, confFile))
		cmd = "echo '%s' %s %s" % (data, oper, confFile)
		os.system(cmd)

	def makeWvDialConf(self, params):
		baud  = params.get('Baud')
		init  = params.get('Init')
		modem = params.get('Modem')
		phone = params.get('phone')
		apn = params.get('apn')
		uid = params.get('uid')
		pwd = params.get('pwd')
		pin = params.get('pin')
		idxInit = 1

		if isEmpty(phone): phone = '*99#'
		if isEmpty(uid):   uid = 'USER'
		if isEmpty(pwd):   pwd = 'PASSWORD'

		self.writeConf('','>')

		#self.writeConf('[Dialer modem-start]')
		#self.writeConf('Init1 = ATZ+CFUN=1')
		#self.writeConf('')
		self.writeConf('[Dialer Defaults]')
		#self.writeConf('Modem = %s' % (modem))
		#self.writeConf('Baud = %s' % (baud))
		self.writeConf('Modem = /dev/ttyUSB0')
		self.writeConf('Baud = 57600')
		self.writeConf('Init%d = ATH' % (idxInit))
		idxInit = idxInit + 1
		self.writeConf('Init%d = ATE1' % (idxInit))
		idxInit = idxInit + 1
		if not isEmpty(pin):
			self.writeConf('Init%d = AT+CPIN=%s' % (idxInit, pin))
			idxInit = idxInit + 1
		#self.writeConf('Init%d = %s' % (idxInit, init))
		#idxInit = idxInit + 1
		#if isEmpty(apn) and isEmpty(uid) and isEmpty(pwd) and isEmpty(pin):
		#	self.writeConf('Init%d = AT&F' % (idxInit))
		#	idxInit = idxInit + 1
		if not isEmpty(apn):
			self.writeConf('Init%d = AT+CGDCONT=1,"IP","%s"' % (idxInit, apn))
			idxInit = idxInit + 1
		self.writeConf('Init%d = AT+CFUN = 1' % (idxInit))
		self.writeConf('Dial Command = ATD')
		self.writeConf('Username = %s' % (uid))
		self.writeConf('Password = %s' % (pwd))
		self.writeConf('Phone = %s' % (phone)) #*99#
		self.writeConf('Modem Type = Analog Modem')
		self.writeConf('Stupid mode = yes')
		self.writeConf('ISDN = 0')
		self.writeConf('Carrier Check = 0')
		self.writeConf('Abort on No Dialtone = 0')
		self.writeConf('Auto DNS = 0')
		if debug_mode_modem_mgr:
			printDebugModemMgr(file('/etc/wvdial.conf').read())

	def updateUSBInfo(self):
		info = ' '
		try:
			apn,uid,pwd,pin,phone = config.plugins.gmodemmanager.apn.getValue(), config.plugins.gmodemmanager.uid.getValue(), config.plugins.gmodemmanager.pwd.getValue(), config.plugins.gmodemmanager.pin.getValue(), config.plugins.gmodemmanager.phone.getValue()#self.apn,self.uid,self.pwd,self.pin,self.phone
			if apn is None:   apn = ""
			if uid is None:   uid = ""
			if pwd is None:   pwd = ""
			if pin is None:   pin = ""
			if phone is None: phone = ""
			x = self["menulist"].getCurrent()[1]
			info = 'Vendor : %s/%s\nAPN : %s\nUser : %s\nPassword : %s\nPin : %s\nPhone : %s' % (
					x.get("Vendor"), 
					x.get("ProdID"), 
					apn,
					uid,
					pwd,
					pin,
					phone
				)
		except: pass
		self['usbinfo'].setText(info)

	def setListOnView(self):
		lv_usb_items = []
		try:
			for x in self.getUSBList():
				lv_usb_items.append((x.get("Product"),x))
		except: pass
		return lv_usb_items

	def getUSBList(self):
		kernel_ver = about.getKernelVersionString()
		if kernel_ver <= "3.0.0":
			cmd = "cat /proc/bus/usb/devices"
		else:
			cmd = "/usr/bin/usb-devices"

		parsed_usb_list = []
		usb_devices = os.popen(cmd).read()
		tmp_device = {}
		for x in usb_devices.splitlines():
			if x is None or len(x) == 0:
				printDebugModemMgr("TMP DEVICE : [%s]" % (tmp_device))
				if len(tmp_device):
					parsed_usb_list.append(tmp_device)
				tmp_device = {}
				continue
			try:
				if x[0] in ('P', 'S', 'I', 'T'):
					tmp = x[2:].strip()
					printDebugModemMgr("TMP : [%s]" % (tmp))
					if tmp.startswith('Bus='):
						#printDebugModemMgr("TMP SPLIT for BUS : [%s]" % (str(tmp.split())))
						for xx in tmp.split():
							if xx.startswith('Bus='):
								tmp_device['Bus'] = xx[4:]
								break
					if tmp.startswith('Manufacturer='):
						tmp_device['Manufacturer'] = tmp[13:]
					if tmp.startswith('Product='):
						tmp_device['Product'] = tmp[8:]
					elif tmp.startswith('SerialNumber='):
						tmp_device['SerialNumber'] = tmp[13:]
					elif tmp.startswith('Vendor='):
						#printDebugModemMgr("TMP SPLIT for BUS : [%s]" % (str(tmp.split())))
						for xx in tmp.split():
							if xx.startswith('Vendor='):
								tmp_device['Vendor'] = xx[7:]
							elif xx.startswith('ProdID='):
								tmp_device['ProdID'] = xx[7:]
						#tmp_device['Vendor'] = tmp
					elif tmp.find('Driver=') > 0:
						d = tmp[tmp.find('Driver=')+7:]
						if d != '(none)':
							tmp_device['Interface'] = d
			except Exception, errmsg:
				print errmsg
		if len(tmp_device):
			parsed_usb_list.append(tmp_device)
		printDebugModemMgr("PARSED DEVICE LIST : " + str(parsed_usb_list))
		rt_usb_list = []
		for x in parsed_usb_list:
			printDebugModemMgr('Looking >> ' + str(x))
			try:
				xx = x.get("Interface")
				if xx.startswith('usb'):
					rt_usb_list.append(x)
			except: pass
		printInfoModemMgr("USB DEVICE LIST : " + str(rt_usb_list))
		return rt_usb_list

def autostart(reason, **kwargs):
	vendorid = config.plugins.gmodemmanager.vendorid.getValue()
	productid = config.plugins.gmodemmanager.productid.getValue()
	if reason == 0:
		if isConnected():
			args = ("%s 0;" % (commandBin))+ ("%s 1" % (commandBin))
			is_running = True
		else:
			args = ("%s 2 vendor=0x%s product=0x%s;" % (commandBin, vendorid, productid)) + ("%s 3 %s %s;sleep 8;" % (commandBin, vendorid, productid)) + ("%s 5" % (commandBin))
			is_running = False
		cmd = args
		if config.plugins.gmodemmanager.autostart.value:
			print "[3GModemManager] AUTOSTART"
			if is_running:
				print "[3GModemManager] already started"
			else:
				print "[3GModemManager] starting ..."
				os.system(cmd)
				print "[3GModemManager] disable all others network adapters ..."
				os.system("ifconfig eth0 down")
		elif config.plugins.gmodemmanager.autostart.value == False and is_running == True:
				print "[3GModemManager] stopping ..."
				os.system(cmd)
				print "[3GModemManager] disable all others network adapters ..."
				os.system("ifconfig eth0 up")
						


				
def main(session, **kwargs):
	session.open(ModemManager)
                                                           
def Plugins(**kwargs):            
	return [PluginDescriptor(name=_("3G / 4G Modem Manager"), description="management 3g modem", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		PluginDescriptor(where = [PluginDescriptor.WHERE_AUTOSTART], fnc = autostart)]


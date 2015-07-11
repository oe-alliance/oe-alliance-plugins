from . import _
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigYesNo, ConfigSelection, ConfigInteger, ConfigIP, ConfigSubsection
from Components.ActionMap import ActionMap, NumberActionMap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.Console import Console
from Tools.Directories import fileExists
from Plugins.Plugin import PluginDescriptor
from os import path as os_path

import xml.etree.cElementTree
from twisted.internet import reactor, task
from twisted.internet.protocol import DatagramProtocol
from Components.Network import iNetwork
from enigma import eTimer
import httplib

Config_Path = "/etc/satip-client.conf"

def modTupByIndex(tup, index, ins):
	lst = list(tup)
	lst[index] = ins
	return tuple(lst)

def isEmpty(x):
		return len(x) == 0

SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
MAN = "ssdp:discover"
MX = 2
ST = "urn:ses-com:device:SatIPServer:1"
MS = 'M-SEARCH * HTTP/1.1\r\nHOST: %s:%d\r\nMAN: "%s"\r\nMX: %d\r\nST: %s\r\n\r\n' % (SSDP_ADDR, SSDP_PORT, MAN, MX, ST)

SATIPSERVERDATA = {}

DEVICE_ATTR = [ 
'friendlyName',
'manufacturer',
'manufacturerURL',
'modelDescription',
'modelName',
'modelNumber',
'modelURL',
'serialNumber',
'presentationURL'
]

class SSDPServerDiscovery(DatagramProtocol):
	def __init__(self, callback, iface = None):
		self.callback = callback
		self.port = None

	def send_msearch(self, iface):
		if not iface:
			return

		self.port = reactor.listenUDP(0, self, interface=iface)
		if self.port is not None:
			print "Sending M-SEARCH..."
			self.port.write(MS, (SSDP_ADDR, SSDP_PORT))

	def stop_msearch(self):
		if self.port is not None:
			self.port.stopListening()

	def datagramReceived(self, datagram, address):
		self.callback(datagram)

	def stop(self):
		pass

discoveryTimeoutMS = 2000;

class SATIPDiscovery:
	def __init__(self):
		self.discoveryStartTimer = eTimer()
		self.discoveryStartTimer.callback.append(self.DiscoveryStart)

		self.discoveryStopTimer = eTimer()
		self.discoveryStopTimer.callback.append(self.DiscoveryStop)

		self.ssdp = SSDPServerDiscovery(self.dataReceive)
		self.updateCallback = []

	def formatAddr(self, address):
		if not address:
			return None

		return "%d.%d.%d.%d"%(address[0],address[1],address[2],address[3])

	def getEthernetAddr(self):
		return self.formatAddr(iNetwork.getAdapterAttribute("eth0", "ip") )

	def DiscoveryTimerStart(self):
		self.discoveryStartTimer.start(10, True)

	def DiscoveryStart(self, stop_timeout = discoveryTimeoutMS):
		self.discoveryStopTimer.stop()
		self.ssdp.stop_msearch()
		
		self.ssdp.send_msearch(self.getEthernetAddr())
		self.discoveryStopTimer.start(stop_timeout, True)

	def DiscoveryStop(self):
		self.ssdp.stop_msearch()

		for x in self.updateCallback:
			x()

	def dataReceive(self, data):
		serverData = self.dataParse(data)
		if serverData.has_key('LOCATION'):
			self.xmlParse(serverData['LOCATION'])

	def dataParse(self, data):
		serverData = {}
		for line in data.splitlines():
			if line.find(':') != -1:
				(attr, value) = line.split(':', 1)
				attr = attr.strip().upper()
				if not serverData.has_key(attr):
					serverData[attr] = value.strip()

		return serverData

	def xmlParse(self, location):
		def findChild(parent, tag, namespace):
			return parent.find('{%s}%s' % (namespace, tag))

		def getAttr(root, parent, tag, namespace):
			try:
				pElem = findChild(root, parent, namespace)
				if pElem is not None:
					child = findChild(pElem, tag, namespace)
					if child is not None:
						return child.text
			except:
				pass

			return None

		def getAttrN2(root, parent, tag, namespace_1 , namespace_2):
			try:
				pElem = findChild(root, parent, namespace_1)
				if pElem is not None:
					child = findChild(pElem, tag, namespace_2)
					if child is not None:
						return child.text
			except:
				pass

			return None

		def dumpData():
			for (k, v) in SATIPSERVERDATA.items():
				prestr = ""
				for (k2, v2) in v.items():
					prestr2 = prestr + "[%s]" % k2
					if not isinstance(v2, dict):
						print "%s %s" % (prestr2, v2)
						continue
					for (k3, v3) in v2.items():
						prestr3 = prestr2 + "[%s]" % k3
						print "%s %s" % (prestr3, v3)
			print ""

		print "[SATIPClient] Parsing %s" % location

		address = ""
		port = None
		request = ""

		try:
			location = location.strip().split("http://")[1]
			AAA = location.find(':')
			BBB = location.find('/')

			address = location[:AAA]
			port = int(location[AAA+1 : BBB])
			request = location[BBB:]

			conn = httplib.HTTPConnection(address, port)
			conn.request("GET", request)
			res = conn.getresponse()
		except Exception, ErrMsg:
			print "http request error %s" % ErrMsg
			return -1

		if res.status != 200 or res.reason !="OK":
			print "response error"
			return -1

		data = res.read()
		conn.close()

		# parseing xml data
		root = xml.etree.cElementTree.fromstring(data)

		xmlns_dev = "urn:schemas-upnp-org:device-1-0"
		xmlns_satip = "urn:ses-com:satip"

		udn = getAttr(root, 'device', 'UDN', xmlns_dev)
		if udn is None:
			return -1;

		uuid = udn.strip('uuid:')
		SATIPSERVERDATA[uuid] = {}

		SATIPSERVERDATA[uuid]['ipaddress'] = address

		pTag = 'device'
		SATIPSERVERDATA[uuid][pTag] = {}
		for tag in DEVICE_ATTR:
			SATIPSERVERDATA[uuid][pTag][tag] = getAttr(root, pTag, tag, xmlns_dev)

		tagList = ['X_SATIPCAP']
		for tag in tagList:
			SATIPSERVERDATA[uuid][pTag][tag] = getAttrN2(root, pTag, tag, xmlns_dev, xmlns_satip)

		pTag = 'specVersion'
		SATIPSERVERDATA[uuid][pTag] = {}
		tagList = ['major', 'minor']
		for tag in tagList:
			SATIPSERVERDATA[uuid][pTag][tag] = getAttr(root, pTag, tag, xmlns_dev)
	
	def isEmptyServerData(self):
		return isEmpty(SATIPSERVERDATA)

	def getServerKeys(self):
		return SATIPSERVERDATA.keys()

	def getServerInfo(self, uuid, attr):
		if attr in ["ipaddress"]:
			return SATIPSERVERDATA[uuid][attr]

		elif attr in DEVICE_ATTR + ['X_SATIPCAP']:
			return SATIPSERVERDATA[uuid]["device"][attr]

		elif attr in ['major', 'minor']:
			return SATIPSERVERDATA[uuid]["specVersion"][attr]
		else:
			return "Unknown"

	def getServerDescFromIP(self, ip):
		for (uuid, data) in SATIPSERVERDATA.items():
			if data.get('ipaddress') == ip:
				return data['device'].get('modelName')
		return 'Unknown'

	def getUUIDFromIP(self, ip):
		for (uuid, data) in SATIPSERVERDATA.items():
			if data.get('ipaddress') == ip:
				return uuid
		return None

satipdiscovery = SATIPDiscovery()

class SATIPTuner(Screen, ConfigListScreen):
	skin =  """
		<screen position="center,center" size="590,400">
			<ePixmap pixmap="skin_default/buttons/red.png" position="40,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="230,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="40,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="230,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="20,70" size="550,50" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="description" render="Label" position="20,120" size="550,210" font="Regular;20" halign="left" valign="center" />
			<widget source="choices" render="Label" position="20,330" size="550,60" font="Regular;20" halign="center" valign="center" />
		</screen>
	"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("SAT>IP Client Tuner Setup"))
		self.skin = SATIPTuner.skin
		self.session = session

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		self["key_yellow"] = StaticText(_("Discover"))
		self["description"] = StaticText(_("Starting..."))
		self["choices"] = StaticText(_(" "))

		self["OkCancelActions"] = ActionMap(["OkCancelActions"],
			{
			"cancel": self.keyCancel,
			"ok": self.keySave,
			})

		self["ColorActions"] = ActionMap(["ColorActions"],
			{
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow" : self.DiscoveryStart,
			})

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)
		self.satipconfig = ConfigSubsection()
		self.satipconfig.server = None

		if not self.discoveryEnd in satipdiscovery.updateCallback:
			satipdiscovery.updateCallback.append(self.discoveryEnd)

		self.onClose.append(self.OnClose)

		if satipdiscovery.isEmptyServerData():
			self.onLayoutFinish.append(self.DiscoveryStart)
		else:
			self.createServerConfig()
			self.createSetup()

	def OnClose(self):
		if self.discoveryEnd in satipdiscovery.updateCallback:
			satipdiscovery.updateCallback.remove(self.discoveryEnd)

		satipdiscovery.DiscoveryStop()

	def DiscoveryStart(self):
		self["config_actions"].setEnabled(False)
		self["description"].setText(_("SAT>IP server discovering for %d seconds..." % (discoveryTimeoutMS / 1000)))
		satipdiscovery.DiscoveryStart()

	def discoveryEnd(self):
		self["config_actions"].setEnabled(True)
		if not satipdiscovery.isEmptyServerData():
			self.createServerConfig()
			self.createSetup()
			self.showChoices()
		else:
			self["description"].setText(_("SAT>IP server is not detected."))

	def createServerConfig(self):
		if satipdiscovery.isEmptyServerData():
			return

		server_choices = []

		server_default = None
		for uuid in satipdiscovery.getServerKeys():
			description = satipdiscovery.getServerInfo(uuid, "modelName")
			server_choices.append( (uuid, description) )

		if server_default is None:
			server_default = server_choices[0][0]

		self.satipconfig.server = ConfigSelection(default = server_default, choices = server_choices )

	def createSetup(self):
		if self.satipconfig.server is None:
			return

		self.list = []
		self.server_entry = getConfigListEntry(_("SAT>IP Server : "), self.satipconfig.server)
		self.list.append( self.server_entry )

		self.createTypeConfig(self.satipconfig.server.value)
		self.type_entry = getConfigListEntry(_("SAT>IP Tuner Type : "), self.satipconfig.tunertype)
		self.list.append( self.type_entry )

		self["config"].list = self.list
		self["config"].l.setList(self.list)

		if not self.showChoices in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.showChoices)

		self.selectionChanged()

	def createTypeConfig(self, uuid):
		# type_choices = [ ("DVB-S", _("DVB-S")), ("DVB-C", _("DVB-C")), ("DVB-T", _("DVB-T"))]
		type_choices = []
		type_default = None
		capability = self.getCapability(uuid)

		for (t, n) in capability.items():
			if n != 0:
				type_choices.append( (t, _(t)) )

		if isEmpty(type_choices):
			type_choices = [ ("DVB-S", _("DVB-S")) ]

		self.satipconfig.tunertype = ConfigSelection(default = type_default, choices = type_choices )

	def selectionChanged(self):
		if self.satipconfig.server is None:
			return

		uuid = self.satipconfig.server.value

		modelDescription = satipdiscovery.getServerInfo(uuid, "modelDescription")
		manufacturer = satipdiscovery.getServerInfo(uuid, "manufacturer")
		modelURL = satipdiscovery.getServerInfo(uuid, "modelURL")
		presentationURL = satipdiscovery.getServerInfo(uuid, "presentationURL")

		capability = self.getCapability(uuid)
		satipcap_list = []
		for (t, n) in capability.items():
			if n != 0:
				satipcap_list.append("%d x %s" % (n, t))

		satipcap = ",".join(satipcap_list)

		description = ""
		description += "Description : %s\n" % modelDescription
		description += "Manufacturer : %s\n" % manufacturer 
		description += "Model URL : %s\n" % modelURL
		description += "Presentation URL : %s\n" % presentationURL
		description += "UUID : %s\n" % uuid		
		description += "SAT>IP capabilities: %s" % satipcap
		
		self["description"].setText(description)

	def showChoices(self):
		currentConfig = self["config"].getCurrent()[1]
		text_list = []
		for choice in currentConfig.choices.choices:
			text_list.append(choice[1])

		text = ", ".join(text_list)

		self["choices"].setText("Choices : \n%s" % (text))

	def getCapability(self, uuid):
		capability = { 'DVB-S' : 0, 'DVB-C' : 0, 'DVB-T' : 0}
		data = satipdiscovery.getServerInfo(uuid, "X_SATIPCAP")
		for x in data.split(','):
			if x.upper().find("DVBS") != -1:
				capability['DVB-S'] = int(x.split('-')[1])
			elif x.upper().find("DVBC") != -1:
				capability['DVB-C'] = int(x.split('-')[1])
			elif x.upper().find("DVBT") != -1:
				capability['DVB-T'] = int(x.split('-')[1])

		return capability

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self["config"].getCurrent() == self.server_entry:
			self.createSetup()
		self.selectionChanged()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent() == self.server_entry:
			self.createSetup()
		self.selectionChanged()

	def keySave(self):
		if self.satipconfig.server is None:
			self.keyCancel()
			return

		uuid = self.satipconfig.server.value
		tunertype = self.satipconfig.tunertype.value

		self.close((satipdiscovery.getServerInfo(uuid, 'ipaddress'), tunertype))

	def keyCancel(self):
		self.close(False)

class SatIPclientSetup(Screen,ConfigListScreen):
	skin =  """
		<screen name="SatIPclientSetup" position="center,center" size="600,450">
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<widget name="key_red" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget name="key_green" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget name="key_yellow" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="25,70" size="560,300" scrollbarMode="showOnDemand" transparent="1" />
			<widget name="text" position="20,430" size="540,20" font="Regular;22" halign="center" valign="center" />
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.onChangedEntry = []
		self.satipserver = []
		self.satipserver_old = []
		self.list = []
		self.vtuner = "0"
		self.ServerDisabled_old = True
		self.Console = Console()
		
		self.disabledSel = ConfigYesNo(default = True)
		self.vtunerEnabledSel = ConfigYesNo(default = False)
		self.vtunerSel = ConfigSelection(choices = [("0","0"),("1","1"),("2","2"),("3","3")])
		self.frontendSel = ConfigSelection(choices = [("0","DVB-S2"),("1","DVB-C"),("2","DVB-T")])
		self.logSel = ConfigSelection(default = "1", choices = [("0","None"),("1","Error"),("2","Warning"),("3","Info"),("4","Debug")])
		self.workaroundSel = ConfigInteger(default = 0, limits = (0, 7))

		self.disabledEntry = getConfigListEntry(_("Disable SAT>IP-client"), self.disabledSel)
		self.vtunerEntry = getConfigListEntry(_("vtuner"), self.vtunerSel)
		self.vtunerEnabledEntry = getConfigListEntry(_("Enable vtuner%s" %self.vtunerEntry[1].value), self.vtunerEnabledSel)
		self.serverEntry = getConfigListEntry(_("Server IP-adress"), ConfigIP(default=[0,0,0,0]))
		self.frontendEntry = getConfigListEntry(_("Frontend type"), self.frontendSel)
		self.logEntry = getConfigListEntry(_("Loglevel"), self.logSel)
		self.workaroundEntry = getConfigListEntry(_("Workarounds for various SAT>IP server quirks"), self.workaroundSel)

		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		
		for t in range(0, 4):
			self.satipserver.append((False,[0, 0, 0, 0],"0","0","0"))
		if os_path.exists(Config_Path):
			self.Read_Config()

		self.skinName = "SatIPclientSetup"
		self.setup_title = _("SAT>IP Client Setup")
		self.setTitle(self.setup_title)
		TEXT = _(" ")
		self["text"] = Label(_("%s")%TEXT)

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label(_("Discover"))
		

		self["OkCancelActions"] = ActionMap(["OkCancelActions"],
			{
			"cancel": self.keyCancel,
			"ok": self.keySave,
			})

		self["ColorActions"] = ActionMap(["ColorActions"],
			{
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow" : self.KeyDiscover,
			})
		
		self.createSetup()
		self.onClose.append(self.onClosed)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		pass

	def onClosed(self):
		self.close()

	def newConfig(self):
		if self["config"].getCurrent() == self.disabledEntry:
			self.createSetup()
			self.Fill_CurrentServerlist(int(self.vtuner))
		elif self["config"].getCurrent() == self.vtunerEntry or self["config"].getCurrent()[0][:-1] == self.vtunerEnabledEntry[0][:-1]:
			self.vtuner = self.vtunerEntry[1].value
			self.Fill_CurrentServerlist(int(self.vtuner))
			self.createSetup()
			self.Fill_CurrentServerlist(int(self.vtuner))
		
	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def createSetup(self):
		self.list = []
		self.vtunerEnabledEntry = getConfigListEntry(_("Enable vtuner%s" %self.vtunerEntry[1].value), self.vtunerEnabledSel)
		self.list.append(self.disabledEntry)
		
		if not self.disabledEntry[1].value:
			self.list.append(self.vtunerEntry)
			self.list.append(self.vtunerEnabledEntry)
			if self.vtunerEnabledEntry[1].value:
				self.list.append(self.serverEntry)
				self.list.append(self.frontendEntry)
				self.list.append(self.logEntry)
				self.list.append(self.workaroundEntry)

		self["config"].list = self.list
		self["config"].l.setList(self.list)

		if self.vtunerEnabledEntry[1].value:
			self["key_yellow"].show()
		else:
			self["key_yellow"].hide()

	def Store_CurrentServerlist(self):
		self.satipserver[int(self.vtuner)] = (self.vtunerEnabledEntry[1].value,self.serverEntry[1].value,self.frontendEntry[1].value,self.logEntry[1].value,str(self.workaroundEntry[1].value))

	def Fill_CurrentServerlist(self, TunerNr):
		self.vtunerEnabledEntry[1].value = self.satipserver[TunerNr][0]
		self.serverEntry[1].value = self.satipserver[TunerNr][1]
		self.frontendEntry[1].value = self.satipserver[TunerNr][2]
		self.logEntry[1].value = self.satipserver[TunerNr][3]
		self.workaroundEntry[1].value = int(self.satipserver[TunerNr][4])
		self["config"].l.setList(self.list)

	def keySave(self):
		self.Store_CurrentServerlist()
		self.Create_Config()
		if fileExists('/etc/init.d/satip-client'):
			if (not self.satipserver_old == self.satipserver or not self.ServerDisabled_old == self.disabledEntry[1].value):
				if self.disabledEntry[1].value:
					self.Console.ePopen('start-stop-daemon -K -p /var/run/satip-client0 /usr/bin/satip-client')
					self.Console.ePopen('start-stop-daemon -K -p /var/run/satip-client1 /usr/bin/satip-client')
					self.Console.ePopen('start-stop-daemon -K -p /var/run/satip-client2 /usr/bin/satip-client')
					self.Console.ePopen('start-stop-daemon -K -p /var/run/satip-client3 /usr/bin/satip-client')
					MsgText = _("To disable the vtuners you need to Resart the GUI.\nRestart GUI now?")
				else:
					self.Console.ePopen('/etc/init.d/satip-client restart')
					MsgText = _("To enable the vtuners you need to Resart the GUI.\nRestart GUI now?")
				self.session.openWithCallback(self.CB_RestartGUI, MessageBox, MsgText, MessageBox.TYPE_YESNO)
			else:
				self.close()
		else:
			self.session.open(MessageBox, _("SAT>IP Client not installed !!"), MessageBox.TYPE_ERROR)
			self.close()

	def CB_RestartGUI(self, ret):
		if ret:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

	def KeyDiscover(self):
		if self.vtunerEnabledEntry[1].value:
			self.session.openWithCallback(self.CB_Discover, SATIPTuner)

	def CB_Discover(self, ret):
		print ret
		if ret:
			type = "0"
			if ret[0]:
				ip = [ int(n) for n in ret[0].split('.') ]
				nr = int(self.vtunerEntry[1].value)
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],1, ip)
	
			if ret[1]:
				if ret[1].upper().find("DVBS") != -1:
					type = "0"
				elif ret[1].upper().find("DVBC") != -1:
					type = "1"
				elif ret[1].upper().find("DVBT") != -1:
					type = "2"
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],2, type)
			
			self.Fill_CurrentServerlist(nr)

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		if not self.satipserver_old == self.satipserver or not self.ServerDisabled_old == self.disabledEntry[1].value:
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		if not self["config"].getCurrent() == self.disabledEntry:
			if self["config"].getCurrent() == self.vtunerEntry or self["config"].getCurrent()[0][:-1] == self.vtunerEnabledEntry[0][:-1]:
				self.Store_CurrentServerlist()

	def Read_Config(self):
		f = open(Config_Path, "r")
		for line in f.readlines():
			line = line.replace(" ","")
			line = line[:-1]

			# DISABLED
			if line[0:9] == "DISABLED=":
				if line[9:].lower() == "no":
					self.disabledEntry[1].value = False
				else:
					self.disabledEntry[1].value = True
				continue

			# SATIPSERVER
			if line[0:11] == "SATIPSERVER":
				nr = int(line[11])
				ipstr = line[13:]
				iplist = ipstr.split(".")
				ip = []
				for t in range(0, 4):
					ip.append(int(iplist[t]))
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],0, True)
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],1, ip)
				continue

			if line[0:12] == "#SATIPSERVER":
				line = line[1:]
				nr = int(line[11])
				ipstr = line[13:]
				iplist = ipstr.split(".")
				ip = []
				for t in range(0, 4):
					ip.append(int(iplist[t]))
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],0, False)
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],1, ip)
				continue
				
			# FRONTENDTYPE
			if line[0:12] == "FRONTENDTYPE":
				nr = int(line[12])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],2, line[14:])
				continue

			if line[0:13] == "#FRONTENDTYPE":
				line = line[1:]
				nr = int(line[12])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],2, line[14:])
				continue

			# LOGLEVEL
			if line[0:8] == "LOGLEVEL":
				nr = int(line[8])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],3, line[10:])
				continue

			if line[0:9] == "#LOGLEVEL":
				line = line[1:]
				nr = int(line[8])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],3, line[10:])
				continue

			# WORKAROUND
			if line[0:10] == "WORKAROUND":
				nr = int(line[10])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],4, line[12:])
				continue

			if line[0:11] == "#WORKAROUND":
				line = line[1:]
				nr = int(line[10])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],4, line[12:])
				continue


		f.close()
		self.Fill_CurrentServerlist(0)
		self.satipserver_old = list(self.satipserver)
		self.ServerDisabled_old = self.disabledEntry[1].value

	def Create_Config(self):
		conftxt = []
		conftxt.append("# SAT>IP Client Config file")
		conftxt.append("###########################\n")

		# DISABLED
		if self.disabledEntry[1].value:
			conftxt.append("DISABLED=yes\n")
		else:
			conftxt.append("DISABLED=no\n")
		conftxt.append("# SAT>IP server address")
		
		# SATIPSERVER
		for t in range(0, 4):
			ip = ""
			for x in range(0, 4):
				ip = ip + str(self.satipserver[t][1][x]) + "."
			if self.satipserver[t][0]:
				dis = ""
			else:
				dis = "#"
			conftxt.append(dis + "SATIPSERVER%s=%s" %(t,ip[:-1]))

		# FRONTENDTYPE
		conftxt.append("")
		conftxt.append("# Frontend type:")
		conftxt.append("# 0: DVB-S2")
		conftxt.append("# 1: DVB-C")
		conftxt.append("# 2: DVB-T")
		for t in range(0, 4):
			if self.satipserver[t][0]:
				dis = ""
			else:
				dis = "#"
			conftxt.append(dis + "FRONTENDTYPE%s=%s" %(t,self.satipserver[t][2]))
	
		# LOGLEVEL
		conftxt.append("")
		conftxt.append("# Loglevel")
		for t in range(0, 4):
			if self.satipserver[t][0]:
				dis = ""
			else:
				dis = "#"
			conftxt.append(dis + "LOGLEVEL%s=%s" %(t,self.satipserver[t][3]))

		# WORKAROUND
		conftxt.append("")
		conftxt.append("# Workarounds for various SAT>IP server quirks")
		conftxt.append("# This is a bitmask.")
		conftxt.append("# 0: Disable all workarounds (default)")
		conftxt.append("# 1: Enable workaround ADD-DUMMY-PID  (AVM Fritz!WLAN Repeater DVB-C)")
		conftxt.append("# 2: Enable workaround FORCE-FULL-PID (AVM Fritz!WLAN Repeater DVB-C)")
		conftxt.append("# 4: Enable workaround FORCE-FE-LOCK  (AVM Fritz!WLAN Repeater DVB-C) CURRENTLY ALWAYS ACTIVE!")
		conftxt.append("# Example:")
		conftxt.append("# AVM Fritz!WLAN Repeater DVB-C: WORKAROUNDx=7")
		for t in range(0, 4):
			if self.satipserver[t][0]:
				dis = ""
			else:
				dis = "#"
			conftxt.append(dis + "WORKAROUND%s=%s" %(t,self.satipserver[t][4]))

		f = open( Config_Path, "w" )
		for x in conftxt:
			f.writelines(x + '\n')
		f.close()

	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

def main(session, close=None, **kwargs):
	session.open(SatIPclientSetup)

def TunerSetup(menuid, **kwargs):
	if menuid == "scan":
		return [(_("SAT>IP Client Setup"), main, "satipclient", 10)]
	else:
		return []

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("SAT>IP Client Setup"), description=_("SAT>IP Client Setup"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=TunerSetup)]


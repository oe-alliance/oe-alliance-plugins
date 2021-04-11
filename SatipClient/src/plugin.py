# -*- coding: UTF-8 -*-
from . import _
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists

from Components.MenuList import MenuList
from Components.Sources.List import List

from enigma import eTimer
from Screens.Standby import TryQuitMainloop
from Components.Network import iNetwork

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import pathExists, fileExists, resolveFilename, SCOPE_CURRENT_SKIN

import xml.etree.cElementTree
from twisted.internet import reactor, task
from twisted.internet.protocol import DatagramProtocol

import glob
import os
import httplib

import copy

from Components.config import config, ConfigSubList, ConfigSelection, ConfigElement


def isEmpty(x):
		return len(x) == 0


def getVtunerList():
	data = []
	for x in glob.glob('/dev/misc/vtuner*'):
		x = x.strip('/dev/misc/vtuner')
		data.append(x)
	data = [int(x) for x in data]
	data.sort()
	return data


VTUNER_IDX_LIST = getVtunerList()

SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
MAN = "ssdp:discover"
MX = 2
ST = "urn:ses-com:device:SatIPServer:1"
MS = 'M-SEARCH * HTTP/1.1\r\nHOST: %s:%d\r\nMAN: "%s"\r\nMX: %d\r\nST: %s\r\n\r\n' % (SSDP_ADDR, SSDP_PORT, MAN, MX, ST)


class SSDPServerDiscovery(DatagramProtocol):
	def __init__(self, callback, iface=None):
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
#		print "Received: (from %r)" % (address,)
# 		print "%s" % (datagram )
		self.callback(datagram)

	def stop(self):
		pass


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

discoveryTimeoutMS = 5000


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

		return "%d.%d.%d.%d" % (address[0], address[1], address[2], address[3])

	def getEthernetAddr(self):
		return self.formatAddr(iNetwork.getAdapterAttribute("eth0", "ip"))

	def DiscoveryTimerStart(self):
		self.discoveryStartTimer.start(10, True)

	def DiscoveryStart(self, stop_timeout=discoveryTimeoutMS):
		self.discoveryStopTimer.stop()
		self.ssdp.stop_msearch()

#		print "Discovery Start!"
		self.ssdp.send_msearch(self.getEthernetAddr())
		self.discoveryStopTimer.start(stop_timeout, True)

	def DiscoveryStop(self):
#		print "Discovery Stop!"
		self.ssdp.stop_msearch()

		for x in self.updateCallback:
			x()

	def dataReceive(self, data):
#		print "dataReceive:\n", data
#		print "\n"
		serverData = self.dataParse(data)
		if 'LOCATION' in serverData:
			self.xmlParse(serverData['LOCATION'])

	def dataParse(self, data):
		serverData = {}
		for line in data.splitlines():
#			print "[*] line : ", line
			if line.find(':') != -1:
				(attr, value) = line.split(':', 1)
				attr = attr.strip().upper()
				if attr not in serverData:
					serverData[attr] = value.strip()

#		for (key, value) in serverData.items():
#			print "[%s] %s" % (key, value)
#		print "\n"
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

		def getAttrN2(root, parent, tag, namespace_1, namespace_2):
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
			print "\n######## SATIPSERVERDATA ########"
			for (k, v) in SATIPSERVERDATA.items():
#				prestr = "[%s]" % k
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
		port = "80"
		request = ""

		try:
			location = location.strip().split("http://")[1]
			AAA = location.find(':')
			BBB = location.find('/')
			if AAA == -1:
				address = location[AAA + 1: BBB]
				port = "80"
				request = location[BBB:]
			else:
				address = location[:AAA]
				port = location[AAA + 1: BBB]
				request = location[BBB:]

			#print "address2 : ", address
			#print "port2: " , port
			#print "request : ", request

			conn = httplib.HTTPConnection(address, int(port))
			conn.request("GET", request)
			res = conn.getresponse()
		except Exception, ErrMsg:
			print "http request error %s" % ErrMsg
			return -1

		if res.status != 200 or res.reason != "OK":
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
			return -1

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

#		dumpData()

	def isEmptyServerData(self):
		return isEmpty(SATIPSERVERDATA)

	def getServerData(self):
		return SATIPSERVERDATA

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
SATIP_CONF_CHANGED = False


class SATIPTuner(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="590,370">
			<ePixmap pixmap="skin_default/buttons/red.png" position="40,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="230,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="40,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="230,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="20,60" size="550,50" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="description" render="Label" position="20,170" size="550,210" font="Regular;20" halign="left" valign="center" />
			<widget source="choices" render="Label" position="20,120" size="550,40" font="Regular;18" halign="left" valign="center" />
		</screen>
	"""

	def __init__(self, session, vtuner_idx, vtuner_uuid, vtuner_type, current_satipConfig):
		Screen.__init__(self, session)
		self.setTitle(_("SAT>IP Client Tuner Setup"))
		self.skin = SATIPTuner.skin
		self.session = session
		self.vtuner_idx = vtuner_idx
		self.vtuner_uuid = vtuner_uuid
		self.vtuner_type = vtuner_type
		self.current_satipConfig = current_satipConfig

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		self["key_yellow"] = StaticText(_("Discover"))
		self["description"] = StaticText(_("Starting..."))
		self["choices"] = StaticText(_(" "))

		self["shortcuts"] = ActionMap(["SATIPCliActions"],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.DiscoveryStart,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session)
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
		self["shortcuts"].setEnabled(False)
		self["config_actions"].setEnabled(False)
		self["description"].setText(_("SAT>IP server discovering for %d seconds...") % (discoveryTimeoutMS / 1000))
		satipdiscovery.DiscoveryStart()

	def discoveryEnd(self):
		self["shortcuts"].setEnabled(True)
		self["config_actions"].setEnabled(True)
		if not satipdiscovery.isEmptyServerData():
			self.createServerConfig()
			self.createSetup()
		else:
			self["description"].setText(_("SAT>IP server is not detected."))

	def createServerConfig(self):
		if satipdiscovery.isEmptyServerData():
			return

		server_choices = []

		server_default = None
		for uuid in satipdiscovery.getServerKeys():
			description = satipdiscovery.getServerInfo(uuid, "modelName")
			server_choices.append((uuid, description))
			if self.vtuner_uuid == uuid:
				server_default = uuid

		if server_default is None:
			server_default = server_choices[0][0]

		self.satipconfig.server = ConfigSelection(default=server_default, choices=server_choices)

	def createSetup(self):
		if self.satipconfig.server is None:
			return

		self.list = []
		self.server_entry = getConfigListEntry(_("SAT>IP Server : "), self.satipconfig.server)
		self.list.append(self.server_entry)

		self.createTypeConfig(self.satipconfig.server.value)
		self.type_entry = getConfigListEntry(_("SAT>IP Tuner Type : "), self.satipconfig.tunertype)
		self.list.append(self.type_entry)

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
				type_choices.append((t, _(t)))
				if self.vtuner_type == t:
					type_default = t

		if isEmpty(type_choices):
			type_choices = [("DVB-S", _("DVB-S"))]

		self.satipconfig.tunertype = ConfigSelection(default=type_default, choices=type_choices)

	def selectionChanged(self):
		if self.satipconfig.server is None:
			return

		uuid = self.satipconfig.server.value

#		ipaddress = satipdiscovery.getServerInfo(uuid, "ipaddress")
		modelDescription = satipdiscovery.getServerInfo(uuid, "modelDescription")
		manufacturer = satipdiscovery.getServerInfo(uuid, "manufacturer")
#		specversion = "%s.%s" % (satipdiscovery.getServerInfo(uuid, "major"), satipdiscovery.getServerInfo(uuid, "minor"))
		modelURL = satipdiscovery.getServerInfo(uuid, "modelURL")
		presentationURL = satipdiscovery.getServerInfo(uuid, "presentationURL")
#		satipcap = satipdiscovery.getServerInfo(uuid, "X_SATIPCAP")
#		serialNumber = satipdiscovery.getServerInfo(uuid, "serialNumber")

		capability = self.getCapability(uuid)
		satipcap_list = []
		for (t, n) in capability.items():
			if n != 0:
				satipcap_list.append("%d x %s" % (n, t))

		satipcap = ",".join(satipcap_list)

		description = ""
		description += _("Description") + " : %s\n" % modelDescription
		description += _("Manufacturer") + " : %s\n" % manufacturer
		description += "Model URL : %s\n" % modelURL
		description += "Presentation URL : %s\n" % presentationURL
		description += "UUID : %s\n" % uuid
		description += "SAT>IP Capability : %s" % satipcap

		self["description"].setText(description)

	def showChoices(self):
		currentConfig = self["config"].getCurrent()[1]
		text_list = []
		for choice in currentConfig.choices.choices:
			text_list.append(choice[1])

#		text = ",".join(text_list)
		text = _("Select") + " : " + ",".join(text_list)

#		self["choices"].setText("Choices : \n%s" % (text))
		self["choices"].setText(text)

	def getCapability(self, uuid):
		capability = {'DVB-S': 0, 'DVB-C': 0, 'DVB-T': 0}
		data = satipdiscovery.getServerInfo(uuid, "X_SATIPCAP")
		if data is not None:
			for x in data.split(','):
				if x.upper().find("DVBS") != -1:
					capability['DVB-S'] = int(x.split('-')[1])
				elif x.upper().find("DVBC") != -1:
					capability['DVB-C'] = int(x.split('-')[1])
				elif x.upper().find("DVBT") != -1:
					capability['DVB-T'] = int(x.split('-')[1])
		else:
			capability = {'DVB-S': 1, 'DVB-C': 0, 'DVB-T': 0}

		return capability

	def checkTunerCapacity(self, uuid, tunertype):
		capability = self.getCapability(uuid)
		t_cap = capability[tunertype]

		t_count = 0

		for idx in VTUNER_IDX_LIST:
			if self.vtuner_idx == idx:
				continue

			vtuner = self.current_satipConfig[int(idx)]
			if vtuner["vtuner_type"] == "satip_client" and vtuner["uuid"] == uuid and vtuner["tuner_type"] == tunertype:
#				print "[checkTunerCapacity] tuner %d use type %s" % (int(idx), tunertype)
				t_count += 1

#		print "[checkTunerCapacity] capability : ", capability
#		print "[checkTunerCapacity] t_cap : %d, t_count %d" % (t_cap, t_count)

		if int(t_cap) > t_count:
			return True

		return False

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

		if not self.checkTunerCapacity(uuid, tunertype):
			self.session.open(MessageBox, _("Server capacity is fulled."), MessageBox.TYPE_ERROR)

		else:
			data = {}
			data['idx'] = self.vtuner_idx
			data['ip'] = satipdiscovery.getServerInfo(uuid, 'ipaddress')
			data['desc'] = satipdiscovery.getServerInfo(uuid, "modelName")
			data['tuner_type'] = tunertype
			data['uuid'] = uuid

			self.close(data)

	def keyCancel(self):
		self.close()


SATIP_CONFFILE = "/etc/vtuner.conf"


class SATIPClient(Screen):
	skin = """
		<screen position="center,center" size="590,370">
			<ePixmap pixmap="skin_default/buttons/red.png" position="20,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="160,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="300,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="440,0" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="20,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="160,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="300,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#a08500" transparent="1" />
			<widget source="key_blue" render="Label" position="440,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#18188b" transparent="1" />

			<widget source="vtunerList" render="Listbox" position="30,60" size="540,272" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
				{"templates":
					{"default": (68,[
							MultiContentEntryText(pos = (20, 0), size = (200, 28), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 0),
							MultiContentEntryText(pos = (50, 28), size = (140, 20), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1),
							MultiContentEntryText(pos = (210, 28), size = (140, 20), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 2),
							MultiContentEntryText(pos = (370, 28), size = (140, 20), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 3),
							MultiContentEntryText(pos = (50, 48), size = (490, 20), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 4),


					]),
					},
					"fonts": [gFont("Regular", 24),gFont("Regular", 16)],
					"itemHeight": 68
				}
				</convert>
			</widget>
			<widget source="description" render="Label" position="0,340" size="590,30" font="Regular;20" halign="center" valign="center" />
		</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("SAT>IP Client Setup"))
		self.skin = SATIPClient.skin
		self.session = session

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Setup"))
		self["key_blue"] = StaticText(_("Disable"))
		self["description"] = StaticText(_("Select tuner and press setup key (Yellow)"))

		self.configList = []
		self["vtunerList"] = List(self.configList)

		self["shortcuts"] = ActionMap(["SATIPCliActions"],
		{
			"ok": self.keySetup,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.KeySave,
			"yellow": self.keySetup,
			"blue": self.keyDisable,
		}, -2)

		self.vtunerIndex = VTUNER_IDX_LIST
		self.vtunerConfig = self.loadConfig()
		self.sortVtunerConfig()
		self.old_vtunerConfig = copy.deepcopy(self.vtunerConfig)
		self.createSetup()
                self.onShown.append(self.checkVTuner)

        def checkVTuner(self):
                if not VTUNER_IDX_LIST:
                        self.session.open(MessageBox, _("No vtuner found."), MessageBox.TYPE_ERROR, close_on_any_key=True)
                        self.close()

	def isChanged(self):
		for vtuner_idx in self.vtunerIndex:
			vtuner = self.vtunerConfig[int(vtuner_idx)]
			old_vtuner = self.old_vtunerConfig[int(vtuner_idx)]
			if vtuner['vtuner_type'] != old_vtuner['vtuner_type']:
				return True

			elif vtuner['vtuner_type'] == "satip_client":
				for key in sorted(vtuner):
					if vtuner[key] != old_vtuner[key]:
						return True
		return False

	def KeySave(self):
		if self.isChanged():
			msg = "You should now reboot your STB to change SAT>IP Configuration.\n\nReboot now ?\n\n"
			self.session.openWithCallback(self.keySaveCB, MessageBox, (_(msg)))

		else:
			self.close()

	def keySaveCB(self, res):
		if res:
			self.saveConfig()
			self.doReboot()

	def doReboot(self):
		self.session.open(TryQuitMainloop, 2)

	def cancelConfirm(self, result):
		if not result:
			return

		self.close()

	def keyCancel(self):
		if self.isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def createSetup(self):
#		print "vtunerIndex : ", self.vtunerIndex
#		print "vtunerConfig : ", self.vtunerConfig
		self.configList = []
		for vtuner_idx in self.vtunerIndex:
			vtuner = self.vtunerConfig[int(vtuner_idx)]

			if vtuner['vtuner_type'] == "satip_client":
				entry = (
				_("VIRTUAL TUNER %s") % vtuner_idx,
				_("TYPE : %s") % vtuner['vtuner_type'].replace('_', ' ').upper(),
				_("IP : %s") % vtuner['ipaddr'],
				_("TUNER TYPE : %s") % vtuner['tuner_type'],
				_("SAT>IP SERVER : %s") % vtuner['desc'],
				vtuner_idx,
				vtuner['tuner_type'],
				vtuner['uuid'],
				)

			else:
				entry = (
				_("VIRTUAL TUNER %s") % vtuner_idx,
				_("TYPE : %s") % vtuner['vtuner_type'].replace('_', ' ').upper(),
				"",
				"",
				"",
				vtuner_idx,
				"",
				"",
				)

			self.configList.append(entry)
#		self.configList.sort()
		self["vtunerList"].setList(self.configList)

	def keyDisable(self):
		idx = self["vtunerList"].getCurrent()[5]

		self.vtunerConfig[int(idx)] = copy.deepcopy(self.old_vtunerConfig[int(idx)])
		if self.vtunerConfig[int(idx)] and self.vtunerConfig[int(idx)]['vtuner_type'] == "satip_client":
			self.vtunerConfig[int(idx)] = {'vtuner_type': "usb_tuner"}

		self.sortVtunerConfig()
		self.createSetup()

	def keySetup(self):
		vtuner_idx = self["vtunerList"].getCurrent()[5]
		vtuner_type = self["vtunerList"].getCurrent()[6]
		vtuner_uuid = self["vtunerList"].getCurrent()[7]
		self.session.openWithCallback(self.SATIPTunerCB, SATIPTuner, vtuner_idx, vtuner_uuid, vtuner_type, self.vtunerConfig)

	def SATIPTunerCB(self, data=None):
		if data is not None:
			self.setConfig(data)

	def setConfig(self, data):
		if data['uuid'] is not None:
			vtuner = self.vtunerConfig[int(data['idx'])]
			vtuner['vtuner_type'] = "satip_client"
			vtuner['ipaddr'] = data['ip']
			vtuner['desc'] = data['desc']
			vtuner['uuid'] = data['uuid']
			vtuner['tuner_type'] = data['tuner_type']

		self.sortVtunerConfig()
		self.createSetup()
#		else:
#			self.keyDisable()

	def sortVtunerConfig(self):
		self.vtunerConfig.sort(reverse=True)

	def saveConfig(self):
		data = ""

		for idx in self.vtunerIndex:
			conf = self.vtunerConfig[int(idx)]
			if not conf:
				continue

#			print "conf : ", conf

			attr = []
			for k in sorted(conf):
				attr.append("%s:%s" % (k, conf[k]))

			data += str(idx) + '=' + ",".join(attr) + "\n"

		if data:
			fd = open(SATIP_CONFFILE, 'w')
			fd.write(data)
			fd.close()

	def loadConfig(self):
		vtunerConfig = []

		for idx in self.vtunerIndex:
			vtunerConfig.append({'vtuner_type': "usb_tuner"})

		if os.access(SATIP_CONFFILE, os.R_OK):
			fd = open(SATIP_CONFFILE)
			confData = fd.read()
			fd.close()

			if confData:
				for line in confData.splitlines():
					if len(line) == 0 or line[0] == '#':
						continue

					data = line.split('=')
					if len(data) != 2:
						continue
					idx = data[0]

					try:
						vtunerConfig[int(idx)]
					except:
						continue

					data = data[1].split(',')
					if len(data) != 5:
						continue

					for x in data:
						s = x.split(':')
						if len(s) != 2:
							continue

						attr = s[0]
						value = s[1]
						vtunerConfig[int(idx)][attr] = value

		return vtunerConfig


def main(session, **kwargs):
	session.open(SATIPClient)


def menu(menuid, **kwargs):
	if menuid == "scan":
		return [(_("SAT>IP Client"), main, "sat_ip_client", 55)]
	return []


def Plugins(**kwargs):
	pList = []
	pList.append(PluginDescriptor(name=_("SAT>IP Client"), description=_("SAT>IP Client attached to vtuner."), where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=menu))
	return pList

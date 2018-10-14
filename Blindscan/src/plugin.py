# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor

from Screens.Screen import Screen
from Screens.ServiceScan import ServiceScan
from Screens.MessageBox import MessageBox

from Components.Label import Label
from Components.TuneTest import Tuner
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.NimManager import nimmanager, getConfigSatlist
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigInteger, getConfigListEntry, ConfigNothing, ConfigBoolean
from Components.Sources.Boolean import Boolean
from Components.Pixmap import Pixmap
from Components.Sources.List import List

from Tools.BoundFunction import boundFunction

from enigma import eTimer, eDVBFrontendParametersSatellite, eComponentScan, eConsoleAppContainer, eDVBResourceManager

import os
from boxbranding import getBoxType, getImageVersion, getImageBuild, getBrandOEM

#used for the XML file
from time import strftime, time

XML_BLINDSCAN_DIR = "/tmp"

# _supportNimType is only used by vuplus hardware
_supportNimType = { 'AVL1208':'', 'AVL6222':'6222_', 'AVL6211':'6211_', 'BCM7356':'bcm7346_', 'SI2166':'si2166_'}

# For STBs that support multiple DVB-S tuner models, e.g. Solo 4K.
_unsupportedNims = ( 'Vuplus DVB-S NIM(7376 FBC)', ) # format = nim.description from nimmanager

# blindscan-s2 supported tuners
_blindscans2Nims = ('TBS-5925', 'DVBS2BOX', 'M88DS3103')

# root2gold based on https://github.com/DigitalDevices/dddvb/blob/master/apps/pls.c
def root2gold(root):
	if root < 0 or root > 0x3ffff:
		return 0
	g = 0
	x = 1
	while g < 0x3ffff:
		if root == x:
			return g
		x = (((x ^ (x >> 7)) & 1) << 17) | (x >> 1)
		g += 1
	return 0

# helper function for initializing mis/pls properties
def getMisPlsValue(d, idx, defaultValue):
	try:
		return int(d[idx])
	except:
		return defaultValue

#used for blindscan-s2
def getAdapterFrontend(frontend, description):
	for adapter in range(1,5):
		try:
			product = open("/sys/class/dvb/dvb%d.frontend0/device/product" % adapter).read()
			if description in product:
				return " -a %d" % adapter
		except:
			break
	return " -f %d" % frontend


class BlindscanState(Screen, ConfigListScreen):
	skin="""
	<screen position="center,center" size="820,570" title="Satellite Blindscan">
		<widget name="progress" position="10,10" size="800,80" font="Regular;20" />
		<eLabel	position="10,95" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,102" size="524,425" />
		<eLabel	position="544,95" size="1,440" backgroundColor="grey"/>
		<widget name="post_action" position="554,102" size="256,140" font="Regular;19" halign="center"/>
		<widget source="key_red" render="Label" position="10,530" size="100,30" font="Regular;19" halign="center"/>
		<widget source="key_green" render="Label" position="120,530" size="100,30" font="Regular;19" halign="center"/>
		<widget source="key_yellow" render="Label" position="230,530" size="100,30" font="Regular;19" halign="center"/>
		<widget source="key_blue" render="Label" position="340,530" size="100,30" font="Regular;19" halign="center"/>
	</screen>
	"""

	def __init__(self, session, progress, post_action, tp_list, finished = False):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Blind scan state"))
		self.finished = finished
		self["progress"] = Label()
		self["progress"].setText(progress)
		self["post_action"] = Label()
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"cancel": self.keyCancel,
			"red": self.keyCancel,
		}, -2)

		self["actions2"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"green": self.scan,
			"yellow": self.selectAll,
			"blue": self.deselectAll,
		}, -2)
		
		if finished:
			self["post_action"].setText(_("Select transponders and press green to scan.\nPress yellow to select all transponders and blue to deselect all."))
			self["key_green"].setText(_("Scan"))
			self["key_yellow"].setText(_("Select all"))
			self["key_blue"].setText(_("Deselect all"))
			self["actions2"].setEnabled(True)
		else:
			self["post_action"].setText(post_action)
			self["actions2"].setEnabled(False)

		self.configBooleanTpList = []
		self.tp_list = []
		ConfigListScreen.__init__(self, self.tp_list, session = self.session)
		for t in tp_list:
			cb = ConfigBoolean(default = False, descriptions = {False: _("don't scan"), True: _("scan")})
			self.configBooleanTpList.append((cb, t[1]))
			self.tp_list.append(getConfigListEntry(t[0], cb))
		self["config"].list = self.tp_list
		self["config"].l.setList(self.tp_list)

	def keyOk(self):
		if self.finished:
			i = self["config"].getCurrent()
			i[1].setValue(not i[1].getValue())
			self["config"].setList(self["config"].getList())

	def selectAll(self):
		if self.finished:
			for i in self.configBooleanTpList:
				i[0].setValue(True)
			self["config"].setList(self["config"].getList())

	def deselectAll(self):
		if self.finished:
			for i in self.configBooleanTpList:
				i[0].setValue(False)
			self["config"].setList(self["config"].getList())

	def scan(self):
		if self.finished:
			scan_list = []
			for i in self.configBooleanTpList:
				if i[0].getValue():
					scan_list.append(i[1])
			if len(scan_list) > 0:
				self.close(True, scan_list)
			else:
				self.close(False)

	def keyCancel(self):
		self.close(False)


class Blindscan(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("Blindscan")
		Screen.setTitle(self, _(self.setup_title))
		self.skinName = "Setup"
		self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceReference()

		self.onChangedEntry = [ ]
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)
		self["description"] = Label("")
		self['footnote'] = Label("")
		self["status"] = StaticText()

		# update sat list
		self.satList = []
		for slot in nimmanager.nim_slots:
			if slot.canBeCompatible("DVB-S"):
				self.satList.append(nimmanager.getSatListForNim(slot.slot))
			else:
				self.satList.append(None)

		# make config
		self.legacy = True
		for slot in nimmanager.nim_slots:
			if slot.canBeCompatible("DVB-S"):
				try:
					slot.config.dvbs
					self.legacy = False
				except:
					self.legacy = True
				break
		self.createConfig()

		self.list = []
		self.status = ""

		self.blindscan_session = None
		self.is_circular_band_scan = False
		self.is_c_band_scan = False
		self.tmpstr = ""
		self.Sundtek_pol = ""
		self.Sundtek_band = ""
		self.SundtekScan = False
		self.offset = 0
		self.start_time = time()
		self.orb_pos = 0
		self.tunerEntry = None
		self.clockTimer = eTimer()

		# run command
		self.cmd = ""
		self.bsTimer = eTimer()
		self.bsTimer.callback.append(self.asyncBlindScan)

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
		if self.scan_nims.value is not None and self.scan_nims.value != "":
			self["actions"] = ActionMap(["ColorActions", "SetupActions", 'DirectionActions'],
			{
				"red": self.keyCancel,
				"green": self.keyGo,
				"ok": self.keyGo,
				"cancel": self.keyCancel,
			}, -2)
			self["key_red"] = StaticText(_("Exit"))
			self["key_green"] = StaticText(_("Scan"))
			self["footnote"] = Label(_("Press Green/OK to start the scan"))
			self.createSetup()
		else:
			self["actions"] = ActionMap(["ColorActions", "SetupActions", 'DirectionActions'],
			{
				"red": self.keyCancel,
				"green": self.keyNone,
				"ok": self.keyNone,
				"cancel": self.keyCancel,
			}, -2)
			self["key_red"] = StaticText(_("Exit"))
			self["key_green"] = StaticText("")
			self["footnote"] = Label(_("Please setup your tuner configuration."))

		self.i2c_mapping_table = None
		self.nimSockets = self.ScanNimsocket()
		self.makeNimSocket()

		self.changedEntry()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
	def getCurrentEntry(self):
		return self["config"].getCurrent() and self["config"].getCurrent()[0] or ""

	def getCurrentValue(self):
		return self["config"].getCurrent() and str(self["config"].getCurrent()[1].getText()) or ""

	def getCurrentDescription(self):
		return self["config"].getCurrent() and len(self["config"].getCurrent()) > 2 and self["config"].getCurrent()[2] or ""

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	def ScanNimsocket(self, filepath = '/proc/bus/nim_sockets'):
		_nimSocket = {}
		try:
			fp = open(filepath)
		except:
			return _nimSocket
		sNo, sName, sI2C = -1, "", -1
		for line in fp:
			line = line.strip()
			if line.startswith('NIM Socket'):
				sNo, sName, sI2C = -1, '', -1
				try:    sNo = line.split()[2][:-1]
				except:	sNo = -1
			elif line.startswith('I2C_Device:'):
				try:    sI2C = line.split()[1]
				except: sI2C = -1
			elif line.startswith('Name:'):
				splitLines = line.split()
				try:
					if splitLines[1].startswith('BCM'):
						sName = splitLines[1]
					else:
						sName = splitLines[3][4:-1]
				except: sName = ""
			if sNo >= 0 and sName != "":
				if sName.startswith('BCM'):
					sI2C = sNo
				if sI2C != -1:
					_nimSocket[sNo] = [sName, sI2C]
				else:	_nimSocket[sNo] = [sName]
		fp.close()
		print "[Blindscan][ScanNimsocket] parsed nimsocket:", _nimSocket
		return _nimSocket

	def makeNimSocket(self, nimname=""):
		is_exist_i2c = False
		self.i2c_mapping_table = {0:2, 1:3, 2:1, 3:0}
		if self.nimSockets is not None:
			for XX in self.nimSockets.keys():
				nimsocket = self.nimSockets[XX]
				if len(nimsocket) > 1:
					try:	self.i2c_mapping_table[int(XX)] = int(nimsocket[1])
					except: continue
					is_exist_i2c = True
		print "[Blindscan][makeNimSocket] i2c_mapping_table:", self.i2c_mapping_table, ", is_exist_i2c:", is_exist_i2c
		if is_exist_i2c: return

		if nimname == "AVL6222":
			if getBoxType() == "vuuno":
				self.i2c_mapping_table = {0:3, 1:3, 2:1, 3:0}
			elif getBoxType() == "vuduo2":
				nimdata = self.nimSockets['0']
				try:
					if nimdata[0] == "AVL6222":
						self.i2c_mapping_table = {0:2, 1:2, 2:4, 3:4}
					else:	self.i2c_mapping_table = {0:2, 1:4, 2:4, 3:0}
				except: self.i2c_mapping_table = {0:2, 1:4, 2:4, 3:0}
			else:	self.i2c_mapping_table = {0:2, 1:4, 2:0, 3:0}
		else:	self.i2c_mapping_table = {0:2, 1:3, 2:1, 3:0}

	def getNimSocket(self, slot_number):
		return self.i2c_mapping_table.get(slot_number, -1)

	def keyNone(self):
		None

	def callbackNone(self, *retval):
		None

	def openFrontend(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.raw_channel = res_mgr.allocateRawChannel(self.feid)
			if self.raw_channel:
				self.frontend = self.raw_channel.getFrontend()
				if self.frontend:
					return True
				else:
					print "[Blindscan][openFrontend] getFrontend failed"
			else:
				print "[Blindscan][openFrontend] getRawChannel failed"
		else:
			print "[Blindscan][openFrontend] getResourceManager instance failed"
		return False

	def prepareFrontend(self):
		self.releaseFrontend()
		if not self.openFrontend():
			self.oldref = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.stopService()
			if not self.openFrontend():
				if self.session.pipshown:
					self.session.pipshown = False
					del self.session.pip
					self.openFrontend()
		print '[Blindscan] self.frontend:',self.frontend
		if self.frontend == None:
			self.session.open(MessageBox, _("Sorry, this tuner is in use."), MessageBox.TYPE_ERROR)
			return False
		self.tuner = Tuner(self.frontend)
		return True

	def createConfig(self):
		self.feinfo = None
		frontendData = None
		defaultSat = {
			"orbpos": 192,
			"system": eDVBFrontendParametersSatellite.System_DVB_S,
			"frequency": 11836,
			"inversion": eDVBFrontendParametersSatellite.Inversion_Unknown,
			"symbolrate": 27500,
			"polarization": eDVBFrontendParametersSatellite.Polarisation_Horizontal,
			"fec": eDVBFrontendParametersSatellite.FEC_Auto,
			"fec_s2": eDVBFrontendParametersSatellite.FEC_9_10,
			"modulation": eDVBFrontendParametersSatellite.Modulation_QPSK
		}

		self.service = self.session.nav.getCurrentService()
		if self.service is not None:
			self.feinfo = self.service.frontendInfo()
			frontendData = self.feinfo and self.feinfo.getAll(True)
		if frontendData is not None:
			ttype = frontendData.get("tuner_type", "UNKNOWN")
			if ttype == "DVB-S":
				defaultSat["system"] = frontendData.get("system", eDVBFrontendParametersSatellite.System_DVB_S)
				defaultSat["frequency"] = frontendData.get("frequency", 0) / 1000
				defaultSat["inversion"] = frontendData.get("inversion", eDVBFrontendParametersSatellite.Inversion_Unknown)
				defaultSat["symbolrate"] = frontendData.get("symbol_rate", 0) / 1000
				defaultSat["polarization"] = frontendData.get("polarization", eDVBFrontendParametersSatellite.Polarisation_Horizontal)
				if defaultSat["system"] == eDVBFrontendParametersSatellite.System_DVB_S2:
					defaultSat["fec_s2"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
					defaultSat["rolloff"] = frontendData.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35)
					defaultSat["pilot"] = frontendData.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown)
				else:
					defaultSat["fec"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
				defaultSat["modulation"] = frontendData.get("modulation", eDVBFrontendParametersSatellite.Modulation_QPSK)
				defaultSat["orbpos"] = frontendData.get("orbital_position", 0)
		del self.feinfo
		del self.service
		del frontendData

		self.scan_sat = ConfigSubsection()
		self.scan_networkScan = ConfigYesNo(default = False)

		self.blindscan_Ku_band_start_frequency = ConfigInteger(default = 10700, limits = (10700, 12749))
		self.blindscan_Ku_band_stop_frequency = ConfigInteger(default = 12750, limits = (10701, 12750))
		self.blindscan_circular_band_start_frequency = ConfigInteger(default = 11700, limits = (11700, 12749))
		self.blindscan_circular_band_stop_frequency = ConfigInteger(default = 12750, limits = (11701, 12750))
		self.blindscan_C_band_start_frequency = ConfigInteger(default = 3600, limits = (3000, 4199))
		self.blindscan_C_band_stop_frequency = ConfigInteger(default = 4200, limits = (3001, 4200))
		self.blindscan_start_symbol = ConfigInteger(default = 2, limits = (1, 44))
		self.blindscan_stop_symbol = ConfigInteger(default = 45, limits = (2, 45))
		self.blindscan_step_mhz_tbs5925 = ConfigInteger(default = 10, limits = (1, 20))
		self.scan_clearallservices = ConfigYesNo(default = False)
		self.scan_onlyfree = ConfigYesNo(default = False)
		self.dont_scan_known_tps = ConfigYesNo(default = False)
		self.filter_off_adjacent_satellites = ConfigSelection(default = 0, choices = [
			(0, _("no")),
			(1, _("up to 1 degree")),
			(2, _("up to 2 degrees")),
			(3, _("up to 3 degrees"))])


		# collect all nims which are *not* set to "nothing"
		nim_list = []
		for n in nimmanager.nim_slots:
			if not n.isCompatible("DVB-S"):
				continue
			if not self.legacy:
				config = n.config.dvbs
			else:
				config = n.config
			config_mode = config.configMode.value

			if config_mode == "nothing":
				continue
			if n.canBeCompatible("DVB-S") and len(nimmanager.getSatListForNim(n.slot)) < 1: # empty setup
				continue
			if n.canBeCompatible("DVB-S") and n.description in _unsupportedNims: # DVB-S NIMs without blindscan hardware or software
				continue
			if config_mode in ("loopthrough", "satposdepends"):
				root_id = nimmanager.sec.getRoot(n.slot_id, int(config.connectedTo.value))
				if n.type == nimmanager.nim_slots[root_id].type: # check if connected from a DVB-S to DVB-S2 Nim or vice versa
					continue
			if n.canBeCompatible("DVB-S"):
				nim_list.append((str(n.slot), n.friendly_full_description))
		self.scan_nims = ConfigSelection(choices = nim_list)

		# sat
		self.scan_sat.frequency = ConfigInteger(default = defaultSat["frequency"], limits = (1, 99999))
		self.scan_sat.polarization = ConfigSelection(default = eDVBFrontendParametersSatellite.Polarisation_CircularRight + 1, choices = [
			(eDVBFrontendParametersSatellite.Polarisation_CircularRight + 1, _("vertical and horizontal")),
			(eDVBFrontendParametersSatellite.Polarisation_Vertical, _("vertical")),
			(eDVBFrontendParametersSatellite.Polarisation_Horizontal, _("horizontal")),
			(eDVBFrontendParametersSatellite.Polarisation_CircularRight + 2, _("circular right and circular left")),
			(eDVBFrontendParametersSatellite.Polarisation_CircularRight, _("circular right")),
			(eDVBFrontendParametersSatellite.Polarisation_CircularLeft, _("circular left"))])
		self.scan_scansat = {}
		for sat in nimmanager.satList:
			self.scan_scansat[sat[0]] = ConfigYesNo(default = False)

		self.scan_satselection = []
		for slot in nimmanager.nim_slots:
			if slot.canBeCompatible("DVB-S"):
				self.scan_satselection.append(getConfigSatlist(defaultSat["orbpos"], self.satList[slot.slot]))
		self.frontend = None # set for later use
		return True

	def getSelectedSatIndex(self, v):
		index    = 0
		none_cnt = 0
		for n in self.satList:
			if self.satList[index] == None:
				none_cnt = none_cnt + 1
			if index == int(v):
				return (index-none_cnt)
			index = index + 1
		return -1

	def createSetup(self):
		self.list = []
		self.multiscanlist = []
		index_to_scan = int(self.scan_nims.value)
		print "[Blindscan][createSetup] ID: ", index_to_scan

		if self.scan_nims == [ ]:
			return

		warning_text = ""
		nim = nimmanager.nim_slots[index_to_scan]
		nimname = nim.friendly_full_description

		self.SundtekScan = "Sundtek DVB-S/S2" in nimname and "V" in nimname
		if getBrandOEM() == 'vuplus' and "AVL6222" in nimname:
			warning_text = _("\nSecond slot dual tuner may not be supported blind scan.")
		elif self.SundtekScan:
			warning_text = _("\nYou must use the power adapter.")

		self.tunerEntry = getConfigListEntry(_("Tuner"), self.scan_nims,(_('Select a tuner that is configured for the satellite you wish to search') + warning_text))
		self.list.append(self.tunerEntry)

		self.systemEntry = None
		self.modulationEntry = None
		self.satelliteEntry = None

		self.scan_networkScan.value = False
		if nim.canBeCompatible("DVB-S"):
			self.satelliteEntry = getConfigListEntry(_('Satellite'), self.scan_satselection[self.getSelectedSatIndex(index_to_scan)],_('Select the satellite you wish to search'))
			self.list.append(self.satelliteEntry)
			self.SatBandCheck()
			if self.is_c_band_scan:
				self.list.append(getConfigListEntry(_('Scan start frequency'), self.blindscan_C_band_start_frequency,_('Frequency values must be between 3000 MHz and 4199 MHz (C-band)')))
				self.list.append(getConfigListEntry(_('Scan stop frequency'), self.blindscan_C_band_stop_frequency,_('Frequency values must be between 3001 MHz and 4200 MHz (C-band)')))
			elif self.is_circular_band_scan:
				self.list.append(getConfigListEntry(_('Scan start frequency'), self.blindscan_circular_band_start_frequency,_('Frequency values must be between 117000 MHz and 12749 MHz (Circular-band)')))
				self.list.append(getConfigListEntry(_('Scan stop frequency'), self.blindscan_circular_band_stop_frequency,_('Frequency values must be between 11701 MHz and 12750 MHz (Circular-band)')))
			elif (self.is_Ku_band_scan or self.is_user_defined_scan) or (not self.is_c_band_scan and not self.is_circular_band_scan):
				self.list.append(getConfigListEntry(_('Scan start frequency'), self.blindscan_Ku_band_start_frequency,_('Frequency values must be between 10700 MHz and 12749 MHz')))
				self.list.append(getConfigListEntry(_('Scan stop frequency'), self.blindscan_Ku_band_stop_frequency,_('Frequency values must be between 10701 MHz and 12750 MHz')))
			if nim.description == 'TBS-5925':
				self.list.append(getConfigListEntry(_("Scan Step in MHz(TBS5925)"), self.blindscan_step_mhz_tbs5925,_('Smaller steps takes longer but scan is more thorough')))
			self.list.append(getConfigListEntry(_("Polarisation"), self.scan_sat.polarization,_('The suggested polarisation for this satellite is "%s"') % (self.suggestedPolarisation)))
			self.list.append(getConfigListEntry(_('Scan start symbolrate'), self.blindscan_start_symbol,_('Symbol rate values are in megasymbols; enter a value between 1 and 44')))
			self.list.append(getConfigListEntry(_('Scan stop symbolrate'), self.blindscan_stop_symbol,_('Symbol rate values are in megasymbols; enter a value between 2 and 45')))
			self.list.append(getConfigListEntry(_("Clear before scan"), self.scan_clearallservices,_('If you select "yes" all channels on the satellite being search will be deleted before starting the current search.')))
			self.list.append(getConfigListEntry(_("Only free scan"), self.scan_onlyfree,_('If you select "yes" the scan will only save channels that are not encrypted; "no" will find encrypted and non-encrypted channels.')))
			self.list.append(getConfigListEntry(_("Only scan unknown transponders"), self.dont_scan_known_tps,_('If you select "yes" the scan will only search transponders not listed in satellites.xml')))
			self.list.append(getConfigListEntry(_("Filter out adjacent satellites"), self.filter_off_adjacent_satellites,_('When a neighbouring satellite is very strong this avoids searching transponders known to be coming from the neighbouring satellite.')))
			self["config"].list = self.list
			self["config"].l.setList(self.list)
			self.startDishMovingIfRotorSat()

	def newConfig(self):
		cur = self["config"].getCurrent()
		print "[Blindscan][newConfig] cur is", cur
		if cur and (cur == self.tunerEntry or cur == self.satelliteEntry):
			self.createSetup()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def keyCancel(self):
		if self.clockTimer:
			self.clockTimer.stop()
		self.releaseFrontend()
		self.session.nav.playService(self.session.postScanService)
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)

	def keyGo(self):
		print "[Blindscan][keyGo] started"
		self.start_time = time()
		self.tp_found = []

		tab_pol = {
			eDVBFrontendParametersSatellite.Polarisation_Horizontal : "horizontal",
			eDVBFrontendParametersSatellite.Polarisation_Vertical : "vertical",
			eDVBFrontendParametersSatellite.Polarisation_CircularLeft : "circular left",
			eDVBFrontendParametersSatellite.Polarisation_CircularRight : "circular right",
			eDVBFrontendParametersSatellite.Polarisation_CircularRight + 1 : "horizontal and vertical",
			eDVBFrontendParametersSatellite.Polarisation_CircularRight + 2 : "circular left and circular right"
		}

		self.tmp_tplist=[]
		tmp_pol = []
		tmp_band = []
		idx_selected_sat = int(self.getSelectedSatIndex(self.scan_nims.value))
		tmp_list=[self.satList[int(self.scan_nims.value)][self.scan_satselection[idx_selected_sat].index]]

		if self.is_c_band_scan:
			self.blindscan_start_frequency = self.blindscan_C_band_start_frequency
			self.blindscan_stop_frequency = self.blindscan_C_band_stop_frequency
		elif self.is_circular_band_scan:
			self.blindscan_start_frequency = self.blindscan_circular_band_start_frequency
			self.blindscan_stop_frequency = self.blindscan_circular_band_stop_frequency
		elif (self.is_Ku_band_scan or self.is_user_defined_scan) or (not self.is_c_band_scan and not self.is_circular_band_scan):
			self.blindscan_start_frequency = self.blindscan_Ku_band_start_frequency
			self.blindscan_stop_frequency = self.blindscan_Ku_band_stop_frequency

		# swap start and stop values if entered the wrong way round
		if self.blindscan_start_frequency.value > self.blindscan_stop_frequency.value:
			temp = self.blindscan_stop_frequency.value
			self.blindscan_stop_frequency.value = self.blindscan_start_frequency.value
			self.blindscan_start_frequency.value = temp
			del temp

		# swap start and stop values if entered the wrong way round
		if self.blindscan_start_symbol.value > self.blindscan_stop_symbol.value:
			temp = self.blindscan_stop_symbol.value
			self.blindscan_stop_symbol.value = self.blindscan_start_symbol.value
			self.blindscan_start_symbol.value = temp
			del temp

		if self.is_circular_band_scan and self.blindscan_circular_band_start_frequency.value > 11699:  #10750 l.o. Needs to start 150 MHz lower
			self.blindscan_circular_band_start_frequency.value = self.blindscan_circular_band_start_frequency.value - 150

		if self.is_circular_band_scan:
			uni_lnb_cutoff = 11550  #10750 l.o. Needs to start 150 MHz lower
		else:
			uni_lnb_cutoff = 11700
		if self.blindscan_start_frequency.value < uni_lnb_cutoff and self.blindscan_stop_frequency.value > uni_lnb_cutoff:
			tmp_band=["low","high"]
		elif self.blindscan_start_frequency.value < uni_lnb_cutoff:
			tmp_band=["low"]
		else:
			tmp_band=["high"]

		if self.scan_sat.polarization.value >  eDVBFrontendParametersSatellite.Polarisation_CircularRight: # must be searching both polarisations, either V and H, or R and L
			tmp_pol=["vertical", "horizontal"]
		elif self.scan_sat.polarization.value ==  eDVBFrontendParametersSatellite.Polarisation_CircularRight:
			tmp_pol=["vertical"]
		elif self.scan_sat.polarization.value ==  eDVBFrontendParametersSatellite.Polarisation_CircularLeft:
			tmp_pol=["horizontal"]
		else:
			tmp_pol=[tab_pol[self.scan_sat.polarization.value]]

		self.doRun(tmp_list, tmp_pol, tmp_band)


	def doRun(self, tmp_list, tmp_pol, tmp_band):
		print "[Blindscan][doRun] started"
		def GetCommand(nimIdx):
			_nimSocket = self.nimSockets
			try:
				sName = _nimSocket[str(nimIdx)][0]
				sType = _supportNimType[sName]
				return "vuplus_%(TYPE)sblindscan"%{'TYPE':sType}, sName
			except: pass
			return "vuplus_blindscan", ""
		if getBrandOEM() == 'vuplus' and not self.SundtekScan:
			self.binName,nimName =  GetCommand(self.scan_nims.value)

			self.makeNimSocket(nimName)
			if self.binName is None:
				self.session.open(MessageBox, _("Blindscan is not supported in ") + nimName + _(" tuner."), MessageBox.TYPE_ERROR)
				print "[Blindscan][doRun] " + nimName + " does not support blindscan."
				return

		self.full_data = ""
		self.total_list=[]
		for x in tmp_list:
			for y in tmp_pol:
				for z in tmp_band:
					self.total_list.append([x,y,z])
					print "[Blindscan][doRun] add scan item: ", x, ", ", y, ", ", z

		self.max_count = len(self.total_list)
		self.is_runable = True
		self.running_count = 0
		self.clockTimer = eTimer()
		self.clockTimer.callback.append(self.doClock)
		self.start_time = time()
		if self.SundtekScan:
			if self.clockTimer:
				self.clockTimer.stop()
				del self.clockTimer
				self.clockTimer = None
			orb = self.total_list[self.running_count][0]
			pol = self.total_list[self.running_count][1]
			band = self.total_list[self.running_count][2]
			self.prepareScanData(orb, pol, band, True)
		else:
			self.clockTimer.start(1000)

	def doClock(self):
		print "[Blindscan][doClock] started"
		is_scan = False
		print "[Blindscan][doClock] self.is_runable", self.is_runable
		if self.is_runable:
			if self.running_count >= self.max_count:
				self.clockTimer.stop()
				del self.clockTimer
				self.clockTimer = None
				print "[Blindscan][doClock] Done"
				return
			orb = self.total_list[self.running_count][0]
			pol = self.total_list[self.running_count][1]
			band = self.total_list[self.running_count][2]
			self.running_count = self.running_count + 1
			print "[Blindscan][doClock] running status-[%d]: [%d][%s][%s]" %(self.running_count, orb[0], pol, band)
			if self.running_count == self.max_count:
				is_scan = True
			self.prepareScanData(orb, pol, band, is_scan)

	def prepareScanData(self, orb, pol, band, is_scan):
		print "[Blindscan][prepareScanData] started"
		self.is_runable = False
		self.orb_position = orb[0]
		self.sat_name = orb[1]
		self.feid = int(self.scan_nims.value)
		tab_hilow = {"high" : 1, "low" : 0}
		tab_pol = {
			"horizontal" : eDVBFrontendParametersSatellite.Polarisation_Horizontal,
			"vertical" : eDVBFrontendParametersSatellite.Polarisation_Vertical,
			"circular left" : eDVBFrontendParametersSatellite.Polarisation_CircularLeft,
			"circular right" : eDVBFrontendParametersSatellite.Polarisation_CircularRight
		}

		returnvalue = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 1)

		if not self.prepareFrontend():
			print "[Blindscan][prepareScanData] self.prepareFrontend() failed (in prepareScanData)"
			return False

		if self.is_c_band_scan:
			self.scan_sat.frequency.value = 3600
		else:
			if tab_hilow[band]:
				self.scan_sat.frequency.value = 12515
			else:
				self.scan_sat.frequency.value = 11015
		returnvalue = (self.scan_sat.frequency.value,
					 0,
					 tab_pol[pol],
					 0,
					 0,
					 orb[0],
					 eDVBFrontendParametersSatellite.System_DVB_S,
					 0,
					 0,
					 0, -1, 0, 1)
		self.tuner.tune(returnvalue)

		nim = nimmanager.nim_slots[self.feid]
		tunername = nim.description
		if not self.SundtekScan and tunername not in _blindscans2Nims and self.getNimSocket(self.feid) < 0:
			print "[Blindscan][prepareScanData] can't find i2c number!!"
			return

		c_band_loc_osc = 5150
		uni_lnb_loc_osc = {"high" : 10600, "low" : 9750}
		uni_lnb_cutoff = 11700
		if self.is_circular_band_scan:
			uni_lnb_cutoff = 11550
		if self.is_c_band_scan:
			temp_start_int_freq = c_band_loc_osc - self.blindscan_stop_frequency.value
			temp_end_int_freq = c_band_loc_osc - self.blindscan_start_frequency.value
			status_box_start_freq = c_band_loc_osc - temp_end_int_freq
			status_box_end_freq = c_band_loc_osc - temp_start_int_freq

		else:
			if tab_hilow[band]:
				if self.blindscan_start_frequency.value < uni_lnb_cutoff:
					temp_start_int_freq = uni_lnb_cutoff - uni_lnb_loc_osc[band]
				else:
					temp_start_int_freq = self.blindscan_start_frequency.value - uni_lnb_loc_osc[band]
				temp_end_int_freq = self.blindscan_stop_frequency.value - uni_lnb_loc_osc[band]
			else:
				if self.blindscan_stop_frequency.value > uni_lnb_cutoff:
					temp_end_int_freq = uni_lnb_cutoff - uni_lnb_loc_osc[band]
				else:
					temp_end_int_freq = self.blindscan_stop_frequency.value - uni_lnb_loc_osc[band]
				temp_start_int_freq = self.blindscan_start_frequency.value - uni_lnb_loc_osc[band]
			status_box_start_freq = temp_start_int_freq + uni_lnb_loc_osc[band]
			status_box_end_freq = temp_end_int_freq + uni_lnb_loc_osc[band]

		cmd = ""
		self.cmd = ""
		self.tmpstr = ""

		if tunername in _blindscans2Nims:
			if tunername == "TBS-5925":
				cmd = "blindscan-s2 -b -s %d -e %d -t %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_step_mhz_tbs5925.value)
			else:
				cmd = "blindscan-s2 -b -s %d -e %d" % (temp_start_int_freq, temp_end_int_freq)
			cmd += getAdapterFrontend(self.feid, tunername)
			if pol == "horizontal":
				cmd += " -H"
			elif pol == "vertical":
				cmd += " -V"
			if self.is_c_band_scan:
				cmd += " -l 5150" # tested by el bandito with TBS-5925 and working
			elif tab_hilow[band]:
				cmd += " -l 10600 -2" # on high band enable 22KHz tone
			else:
				cmd += " -l 9750"
			#self.frontend and self.frontend.closeFrontend() # close because blindscan-s2 does not like to be open
			self.cmd = cmd
			self.bsTimer.stop()
			self.bsTimer.start(6000, True)
		elif self.SundtekScan:
			tools = "/opt/bin/mediaclient"
			if os.path.exists(tools):
				cmd = "%s --blindscan %d" % (tools, self.feid)
				if self.is_c_band_scan:
					cmd += " --band c"
			else:
				self.session.open(MessageBox, _("Not found blind scan utility '%s'!") % tools, MessageBox.TYPE_ERROR)
				return
		elif getBrandOEM() == 'ini' or getBrandOEM() == 'home':
			cmd = "ini_blindscan %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid))
		elif getBrandOEM() == 'vuplus':
			try:
				cmd = "%s %d %d %d %d %d %d %d %d" % (self.binName, temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid))
			except: return

		elif getBrandOEM() == 'ceryon':
			cmd = "ceryon_blindscan %d %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid), self.is_c_band_scan)
		elif getBrandOEM() == 'xtrend':
			cmd = "avl_xtrend_blindscan %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid)) # commented out by Huevos cmd = "avl_xtrend_blindscan %d %d %d %d %d %d %d %d" % (self.blindscan_start_frequency.value/1000000, self.blindscan_stop_frequency.value/1000000, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid))
		elif getBrandOEM() == 'odin':
			cmd = "odin_blindscan %d %d %d %d %d %d %d" % (self.feid, temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band]) # odin_blindscan tuner_idx min_frequency max_frequency min_symbolrate max_symbolrate polarization(Vertical & Horizontal) hilow_band
		elif getBrandOEM() == 'gigablue':
			cmd = "gigablue_blindscan %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid)) # commented out by Huevos cmd = "vuplus_blindscan %d %d %d %d %d %d %d %d" % (self.blindscan_start_frequency.value/1000000, self.blindscan_stop_frequency.value/1000000, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid))
		elif getBrandOEM() == 'azbox':
			cmd = "avl_azbox_blindscan %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid)) # commented out by Huevos cmd = "avl_azbox_blindscan %d %d %d %d %d %d %d %d" % (self.blindscan_start_frequency.value/1000000, self.blindscan_stop_frequency.value/1000000, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid))
			self.polsave=tab_pol[pol] # Data returned by the binary is not good we must save polarisation
		elif getBrandOEM() == 'xcore' or getBrandOEM() == 'edision':
			cmd = "blindscan --start=%d --stop=%d --min=%d --max=%d --slot=%d --i2c=%d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, self.feid, self.getNimSocket(self.feid))
			if tab_pol[pol]:
				cmd += " --vertical"
			if self.is_c_band_scan:
				cmd += " --cband"
			elif tab_hilow[band]:
				cmd += " --high"
		elif getBrandOEM() == 'clap':
			self.frontend and self.frontend.closeFrontend()
			cmd = "clap-blindscan %d %d %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid), self.is_c_band_scan,orb[0])
		elif getBrandOEM() == 'uclan':
			self.frontend and self.frontend.closeFrontend()
			cmd = "uclan-blindscan %d %d %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid), self.is_c_band_scan,orb[0])
		elif getBoxType() == 'sf8008':
			self.frontend and self.frontend.closeFrontend()
			cmd = "octagon-blindscan %d %d %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid), self.is_c_band_scan,orb[0])
		elif getBrandOEM() == 'dinobot':
			cmd = "dinobot-blindscan %d %d %d %d %d %d %d %d %d %d" % (temp_start_int_freq, temp_end_int_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value, tab_pol[pol], tab_hilow[band], self.feid, self.getNimSocket(self.feid), self.is_c_band_scan,orb[0])

		print "[Blindscan][prepareScanData] prepared command: [%s]" % (cmd)

		self.thisRun = [] # used to check result corresponds with values used above
		self.thisRun.append(int(temp_start_int_freq))
		self.thisRun.append(int(temp_end_int_freq))
		self.thisRun.append(int(tab_hilow[band]))

		if not self.cmd:
			if self.SundtekScan:
				print "[Blindscan][prepareScanData] closing frontend and starting blindscan"
				self.frontend and self.frontend.closeFrontend()
			self.blindscan_container = eConsoleAppContainer()
			self.blindscan_container.appClosed.append(self.blindscanContainerClose)
			self.blindscan_container.dataAvail.append(self.blindscanContainerAvail)
			self.blindscan_container.execute(cmd)

		display_pol = pol # Display the correct polarisation in the MessageBox below
		if self.scan_sat.polarization.value == eDVBFrontendParametersSatellite.Polarisation_CircularRight:
			display_pol = _("circular right")
		elif self.scan_sat.polarization.value == eDVBFrontendParametersSatellite.Polarisation_CircularLeft:
			display_pol = _("circular left")
		elif  self.scan_sat.polarization.value == eDVBFrontendParametersSatellite.Polarisation_CircularRight + 2:
			if pol == "horizontal":
				display_pol = _("circular left")
			else:
				display_pol = _("circular right")
		if display_pol == "horizontal":
			display_pol = _("horizontal")
		if display_pol == "vertical":
			display_pol = _("vertical")
		if self.is_circular_band_scan and status_box_start_freq < 11700:
			status_box_start_freq = 11700

		if self.SundtekScan:
			tmpmes = _("   Starting Sundtek hardware blind scan.")
		else:
			tmpmes = _("Current Status: %d/%d\nSatellite: %s\nPolarization: %s  Frequency range: %d - %d MHz  Symbol rates: %d - %d MHz") %(self.running_count, self.max_count, orb[1], display_pol, status_box_start_freq, status_box_end_freq, self.blindscan_start_symbol.value, self.blindscan_stop_symbol.value)
		if getBoxType() == ('vusolo2'):
			tmpmes2 = _("Looking for available transponders.\nThis will take a long time, please be patient.")
		else:
			tmpmes2 = _("Looking for available transponders.\nThis will take a short while.")
		self.tmpstr = tmpmes
		if is_scan:
			self.blindscan_session = self.session.openWithCallback(self.blindscanSessionClose, BlindscanState, tmpmes, tmpmes2, [])
		else:
			self.blindscan_session = self.session.openWithCallback(self.blindscanSessionNone, BlindscanState, tmpmes, tmpmes2, [])

	def dataSundtekIsGood(self, data):
		add_tp = False
		pol = self.scan_sat.polarization.value
		if pol == eDVBFrontendParametersSatellite.Polarisation_CircularRight + 1 or pol == eDVBFrontendParametersSatellite.Polarisation_CircularRight + 2:
			add_tp = True
		elif self.Sundtek_pol in (1, 3) and (pol == eDVBFrontendParametersSatellite.Polarisation_Vertical or pol == eDVBFrontendParametersSatellite.Polarisation_CircularRight):
			add_tp = True
		elif self.Sundtek_pol in (0, 2) and (pol == eDVBFrontendParametersSatellite.Polarisation_Horizontal or pol == eDVBFrontendParametersSatellite.Polarisation_CircularLeft):
			add_tp = True
		if add_tp:
			if data[2].isdigit() and data[3].isdigit():
				freq = (int(data[2]) + self.offset) / 1000
				symbolrate = int(data[3])
			else:
				return False
			if freq >= self.blindscan_start_frequency.value and freq <= self.blindscan_stop_frequency.value and symbolrate >= self.blindscan_start_symbol.value * 1000 and symbolrate <= self.blindscan_stop_symbol.value * 1000:
				add_tp = True
			else:
				add_tp = False
		if add_tp:
			if self.is_c_band_scan:
				if freq > 2999 and freq < 4201:
					add_tp = True
				else:
					add_tp = False
			else:
				if freq < 12751 and freq > 10700:
					add_tp = True
				else:
					add_tp = False
		return add_tp

	def blindscanContainerClose(self, retval):
		self.Sundtek_pol = ""
		self.Sundtek_band = ""
		self.offset = 0
		lines = self.full_data.split('\n')
		self.full_data = "" # Clear this string so we don't get duplicates on subsequent runs
		for line in lines:
			data = line.split()
			print "[Blindscan][blindscanContainerClose] cnt:", len(data), ", data:", data
			if self.SundtekScan:
				if len(data) == 3 and data[0] == 'Scanning':
					if data[1] == '13V':
						self.Sundtek_pol = 1
						if self.is_circular_band_scan or self.is_c_band_scan:
							self.Sundtek_pol = 3
					elif data[1] == '18V':
						self.Sundtek_pol = 0
						if self.is_circular_band_scan or self.is_c_band_scan:
							self.Sundtek_pol = 2
					if data[2] == 'Highband':
						self.Sundtek_band = "nigh"
					elif data[2] == 'Lowband':
						self.Sundtek_band = "low"
					self.offset = 0
					if self.is_c_band_scan:
						self.offset = 5150000
					elif self.is_circular_band_scan:
						self.offset = 10750000
					else:
						if self.Sundtek_band == "nigh":
							self.offset = 10600000
						elif self.Sundtek_band == "low":
							self.offset = 9750000
				if len(data) >= 6 and data[0] == 'OK' and self.Sundtek_pol != "" and self.offset and self.dataSundtekIsGood(data):
					parm = eDVBFrontendParametersSatellite()
					sys = { "DVB-S" : parm.System_DVB_S,
						"DVB-S2" : parm.System_DVB_S2},
						"DVB-S2X" : parm.System_DVB_S2}
					qam = { "QPSK" : parm.Modulation_QPSK,
						"8PSK" : parm.Modulation_8PSK,
						"16APSK" : parm.Modulation_16APSK,
						"32APSK" : parm.Modulation_32APSK}
					parm.orbital_position = self.orb_position
					parm.polarisation = self.Sundtek_pol
					frequency = ((int(data[2]) + self.offset) / 1000) * 1000
					parm.frequency = frequency
					symbol_rate = int(data[3]) * 1000
					parm.symbol_rate = symbol_rate
					parm.system = sys[data[1]]
					parm.inversion = parm.Inversion_Off
					parm.pilot = parm.Pilot_Off
					parm.fec = parm.FEC_Auto
					parm.modulation = qam[data[4]]
					parm.rolloff = parm.RollOff_alpha_0_35
					try:
						parm.pls_mode = eDVBFrontendParametersSatellite.PLS_Gold
						parm.is_id = eDVBFrontendParametersSatellite.No_Stream_Id_Filter
						parm.pls_code = 0
					except:
						pass
					self.tmp_tplist.append(parm)
			elif len(data) >= 10 and self.dataIsGood(data):
				if data[0] == 'OK':
					parm = eDVBFrontendParametersSatellite()
					sys = { "DVB-S" : parm.System_DVB_S,
						"DVB-S2" : parm.System_DVB_S2}
					qam = { "QPSK" : parm.Modulation_QPSK,
						"8PSK" : parm.Modulation_8PSK,
						"16APSK" : parm.Modulation_16APSK,
						"32APSK" : parm.Modulation_32APSK}
					inv = { "INVERSION_OFF" : parm.Inversion_Off,
						"INVERSION_ON" : parm.Inversion_On,
						"INVERSION_AUTO" : parm.Inversion_Unknown}
					fec = { "FEC_AUTO" : parm.FEC_Auto,
						"FEC_1_2" : parm.FEC_1_2,
						"FEC_2_3" : parm.FEC_2_3,
						"FEC_3_4" : parm.FEC_3_4,
						"FEC_4_5" : parm.FEC_4_5,
						"FEC_5_6": parm.FEC_5_6,
						"FEC_7_8" : parm.FEC_7_8,
						"FEC_8_9" : parm.FEC_8_9,
						"FEC_3_5" : parm.FEC_3_5,
						"FEC_9_10" : parm.FEC_9_10,
						"FEC_13_45" : parm.FEC_Auto,
						"FEC_9_20" : parm.FEC_Auto,
						"FEC_11_20" : parm.FEC_Auto,
						"FEC_23_36" : parm.FEC_Auto,
						"FEC_25_36" : parm.FEC_Auto,
						"FEC_13_18" : parm.FEC_Auto,
						"FEC_26_45" : parm.FEC_Auto,
						"FEC_28_45" : parm.FEC_Auto,
						"FEC_7_9" : parm.FEC_Auto,
						"FEC_77_90" : parm.FEC_Auto,
						"FEC_32_45" : parm.FEC_Auto,
						"FEC_11_15" : parm.FEC_Auto,
						"FEC_1_2_L" : parm.FEC_Auto,
						"FEC_8_15_L" : parm.FEC_Auto,
						"FEC_3_5_L" : parm.FEC_Auto,
						"FEC_2_3_L" : parm.FEC_Auto,
						"FEC_5_9_L" : parm.FEC_Auto,
						"FEC_26_45_L" : parm.FEC_Auto,
						"FEC_NONE" : parm.FEC_None}
					roll ={ "ROLLOFF_20" : parm.RollOff_alpha_0_20,
						"ROLLOFF_25" : parm.RollOff_alpha_0_25,
						"ROLLOFF_35" : parm.RollOff_alpha_0_35,
						"ROLLOFF_AUTO" : parm.RollOff_auto}
					pilot={ "PILOT_ON" : parm.Pilot_On,
						"PILOT_OFF" : parm.Pilot_Off,
						"PILOT_AUTO" : parm.Pilot_Unknown}
					pol = { "HORIZONTAL" : parm.Polarisation_Horizontal,
						"CIRCULARRIGHT" : parm.Polarisation_CircularRight,
						"CIRCULARLEFT" : parm.Polarisation_CircularLeft,
						"VERTICAL" : parm.Polarisation_Vertical}
					parm.orbital_position = self.orb_position
					if getBrandOEM() == 'azbox':
						parm.polarisation = self.polsave
					else:
						parm.polarisation = pol[data[1]]
					parm.frequency = int(data[2])
					parm.symbol_rate = int(data[3])
					parm.system = sys[data[4]]
					parm.inversion = inv[data[5]]
					parm.pilot = pilot[data[6]]
					parm.fec = fec[data[7]]
					parm.modulation = qam[data[8]]
					parm.rolloff = roll[data[9]]
					try:
						parm.pls_mode = getMisPlsValue(data, 10, eDVBFrontendParametersSatellite.PLS_Gold)
						parm.is_id = getMisPlsValue(data, 11, eDVBFrontendParametersSatellite.No_Stream_Id_Filter)
						parm.pls_code = getMisPlsValue(data, 12, 0)
						# when blindscan returns 0,0,0 then use defaults...
						if parm.pls_mode == parm.is_id == parm.pls_code == 0:
							parm.pls_mode = eDVBFrontendParametersSatellite.PLS_Gold
							parm.is_id = eDVBFrontendParametersSatellite.No_Stream_Id_Filter
						# when blidnscan returns root then switch to gold
						if parm.pls_mode == eDVBFrontendParametersSatellite.PLS_Root:
							parm.pls_mode = eDVBFrontendParametersSatellite.PLS_Gold
							parm.pls_code = root2gold(parm.pls_code)
					except:
						pass
					self.tmp_tplist.append(parm)
		self.blindscan_session.close(True)
		self.blindscan_session = None

	def blindscanContainerAvail(self, str):
		print "[Blindscan][blindscanContainerAvail]", str
		self.full_data = self.full_data + str
		if self.blindscan_session:
			tmpstr = ""
			data = str.split()
			if self.SundtekScan:
				if len(data) == 3 and data[0] == 'Scanning':
					if data[1] == '13V':
						self.Sundtek_pol = "V"
						if self.is_circular_band_scan:
							self.Sundtek_pol = "R"
					elif data[1] == '18V':
						self.Sundtek_pol = "H"
						if self.is_circular_band_scan:
							self.Sundtek_pol = "L"
					if data[2] == 'Highband':
						self.Sundtek_band = "nigh"
					elif data[2] == 'Lowband':
						self.Sundtek_band = "low"
					self.offset = 0
					if self.is_c_band_scan:
						self.offset = 5150000
					elif self.is_circular_band_scan:
						self.offset = 10750000
					else:
						if self.Sundtek_band == "nigh":
							self.offset = 10600000
						elif self.Sundtek_band == "low":
							self.offset = 9750000
					self.tp_found.append(str)
					seconds_done = int(time() - self.start_time)
					tmpstr += '\n'
					tmpstr += _("Step %d %d:%02d min") %(len(self.tp_found),seconds_done / 60, seconds_done % 60)
					self.blindscan_session["text"].setText(self.tmpstr + tmpstr)

	def blindscanSessionNone(self, *val):
		import time
		self.blindscan_container.sendCtrlC()
		self.blindscan_container = None
		time.sleep(2)

		self.blindscan_session = None
		self.releaseFrontend()

		if val[0] == False:
			self.tmp_tplist = []
			self.running_count = self.max_count

		self.is_runable = True

	def asyncBlindScan(self):
		self.bsTimer.stop()
		if not self.frontend:
			return
		print "[Blindscan][asyncBlindScan] closing frontend and starting blindscan"
		self.frontend.closeFrontend() # close because blindscan-s2 does not like to be open
		self.blindscan_container = eConsoleAppContainer()
		self.blindscan_container.appClosed.append(self.blindscanContainerClose)
		self.blindscan_container.dataAvail.append(self.blindscanContainerAvail)
		self.blindscan_container.execute(self.cmd)

	def blindscanSessionClose(self, *val):
		self.blindscanSessionNone(val[0])

		if self.SundtekScan:
			self.frontend and self.frontend.closeFrontend()

		if self.tmp_tplist != None and self.tmp_tplist != []:
			if not self.SundtekScan:
				self.tmp_tplist = self.correctBugsCausedByDriver(self.tmp_tplist)

			# Sync with or remove transponders that exist in satellites.xml
			self.known_transponders = self.getKnownTransponders(self.orb_position)
			if self.dont_scan_known_tps.value:
				self.tmp_tplist = self.removeKnownTransponders(self.tmp_tplist, self.known_transponders)
			else:
				self.tmp_tplist = self.syncWithKnownTransponders(self.tmp_tplist, self.known_transponders)

			# Filter off transponders on neighbouring satellites
			if self.filter_off_adjacent_satellites.value:
				 self.tmp_tplist = self.filterOffAdjacentSatellites(self.tmp_tplist, self.orb_position, self.filter_off_adjacent_satellites.value)

			# Process transponders still in list
			if self.tmp_tplist != []:
				blindscanStateList = []
				for p in self.tmp_tplist:
					print "[Blindscan][blindscanSessionClose] data: [%d][%d][%d][%d][%d][%d][%d][%d][%d][%d]" % (p.orbital_position, p.polarisation, p.frequency, p.symbol_rate, p.system, p.inversion, p.pilot, p.fec, p.modulation, p.modulation)

					pol = { p.Polarisation_Horizontal : "H KHz",
						p.Polarisation_CircularRight : "R KHz",
						p.Polarisation_CircularLeft : "L KHz",
						p.Polarisation_Vertical : "V KHz"}
					fec = { p.FEC_Auto : "Auto",
						p.FEC_1_2 : "1/2",
						p.FEC_2_3 : "2/3",
						p.FEC_3_4 : "3/4",
						p.FEC_4_5 : "4/5",
						p.FEC_5_6 : "5/6",
						p.FEC_7_8 : "7/8",
						p.FEC_8_9 : "8/9",
						p.FEC_3_5 : "3/5",
						p.FEC_9_10 : "9/10",
						p.FEC_None : "None"}
					sys = { p.System_DVB_S : "DVB-S",
						p.System_DVB_S2 : "DVB-S2"}
					qam = { p.Modulation_QPSK : "QPSK",
						p.Modulation_8PSK : "8PSK",
						p.Modulation_16APSK : "16APSK",
						p.Modulation_32APSK : "32APSK"}
					tp_str = "%d%s SR%d FEC %s %s %s" % (p.frequency, pol[p.polarisation], p.symbol_rate/1000, fec[p.fec], sys[p.system], qam[p.modulation])
					blindscanStateList.append((tp_str, p))

				self.tmp_tplist = sorted(self.tmp_tplist, key=lambda tp: (tp.frequency, tp.is_id, tp.pls_mode, tp.pls_code))
				runtime = int(time() - self.start_time)
				xml_location = self.createSatellitesXMLfile(self.tmp_tplist, XML_BLINDSCAN_DIR)
				self.session.openWithCallback(self.startScan, BlindscanState, _("Search completed\n%d transponders found in %d:%02d minutes.\nDetails saved in: %s") % (len(self.tmp_tplist), runtime / 60, runtime % 60, xml_location), "", blindscanStateList, True)
			else:
				msg = _("No new transponders found! \n\nOnly transponders already listed in satellites.xml \nhave been found for those search parameters!")
				self.session.openWithCallback(self.callbackNone, MessageBox, msg, MessageBox.TYPE_INFO, timeout=60)

		else:
			msg = _("No transponders were found for those search parameters!")
			if val[0] == False:
				msg = _("The blindscan run was cancelled by the user.")
			self.session.openWithCallback(self.callbackNone, MessageBox, msg, MessageBox.TYPE_INFO, timeout=60)
			self.tmp_tplist = []

	def startScan(self, *retval):
		if retval[0] == False:
			return

		tlist = retval[1]
		networkid = 0
		self.scan_session = None

		flags = 0
		if self.scan_clearallservices.value:
			flags |= eComponentScan.scanRemoveServices
		else:
			flags |= eComponentScan.scanDontRemoveUnscanned
		if self.scan_onlyfree.value:
			flags |= eComponentScan.scanOnlyFree
		self.session.openWithCallback(self.startScanCallback, ServiceScan, [{"transponders": tlist, "feid": self.feid, "flags": flags, "networkid": networkid}])

	def getKnownTransponders(self, pos):
		tlist = []
		list = nimmanager.getTransponders(pos)
		for x in list:
			if x[0] == 0:
				parm = eDVBFrontendParametersSatellite()
				parm.frequency = x[1]
				parm.symbol_rate = x[2]
				parm.polarisation = x[3]
				parm.fec = x[4]
				parm.inversion = x[7]
				parm.orbital_position = pos
				parm.system = x[5]
				parm.modulation = x[6]
				parm.rolloff = x[8]
				parm.pilot = x[9]
				if len(x) > 12:
					parm.is_id = x[10]
					parm.pls_mode = x[11]
					parm.pls_code = x[12]
				tlist.append(parm)
		return tlist

	def syncWithKnownTransponders(self, tplist, knowntp):
		tolerance = 5
		multiplier = 1000
		x = 0
		for t in tplist:
			for k in knowntp:
				if (t.polarisation % 2) == (k.polarisation % 2) and \
					abs(t.frequency - k.frequency) < (tolerance*multiplier) and \
					abs(t.symbol_rate - k.symbol_rate) < (tolerance*multiplier) and \
					t.is_id == k.is_id and t.pls_code == k.pls_code and t.pls_mode == k.pls_mode:
					tplist[x] = k
					#break
			x += 1
		tplist = self.removeDuplicateTransponders(tplist)
		return tplist

	def removeDuplicateTransponders(self, tplist):
		new_tplist = []
		for t in tplist:
			if t not in new_tplist:
				new_tplist.append(t)
		return new_tplist

	def removeKnownTransponders(self, tplist, knowntp):
		new_tplist = []
		tolerance = 5
		multiplier = 1000
		x = 0
		isnt_known = True
		for t in tplist:
			for k in knowntp:
				if (t.polarisation % 2) == (k.polarisation % 2) and \
					abs(t.frequency - k.frequency) < (tolerance*multiplier) and \
					abs(t.symbol_rate - k.symbol_rate) < (tolerance*multiplier):
					isnt_known = False
					#break
			x += 1
			if isnt_known:
				new_tplist.append(t)
			else:
				isnt_known = True
		return new_tplist

	def filterOffAdjacentSatellites(self, tplist, pos, degrees):
		neighbours = []
		tenths_of_degrees = degrees * 10
		for sat in nimmanager.satList:
			if sat[0] != pos and self.positionDiff(pos, sat[0]) <= tenths_of_degrees:
				neighbours.append(sat[0])
		for neighbour in neighbours:
			tplist = self.removeKnownTransponders(tplist, self.getKnownTransponders(neighbour))
		return tplist

	def correctBugsCausedByDriver(self, tplist):
		if self.is_c_band_scan: # for some reason a c-band scan (with a Vu+) returns the transponder frequencies in Ku band format so they have to be converted back to c-band numbers before the subsequent service search
			x = 0
			for transponders in tplist:
				if tplist[x].frequency > (4200*1000):
					tplist[x].frequency = (5150*1000) - (tplist[x].frequency - (9750*1000))
				x += 1
		elif self.is_circular_band_scan: # Add Standard 10750 L.O. LNB
			x = 0
			for transponders in tplist:
				tplist[x].frequency = (150*1000) + tplist[x].frequency
				x += 1

		x = 0
		for transponders in tplist:
			if tplist[x].system == 0: # convert DVB-S transponders to auto fec as for some reason the tuner incorrectly returns 3/4 FEC for all transmissions
				tplist[x].fec = 0
			if self.scan_sat.polarization.value == eDVBFrontendParametersSatellite.Polarisation_CircularRight: # Return circular transponders to correct polarisation
				tplist[x].polarisation = eDVBFrontendParametersSatellite.Polarisation_CircularRight
			elif self.scan_sat.polarization.value == eDVBFrontendParametersSatellite.Polarisation_CircularLeft: # Return circular transponders to correct polarisation
				tplist[x].polarisation = eDVBFrontendParametersSatellite.Polarisation_CircularLeft
			elif self.scan_sat.polarization.value == eDVBFrontendParametersSatellite.Polarisation_CircularRight + 2: # Return circular transponders to correct polarisation
				if tplist[x].polarisation == eDVBFrontendParametersSatellite.Polarisation_Horizontal: # Return circular transponders to correct polarisation
					tplist[x].polarisation = eDVBFrontendParametersSatellite.Polarisation_CircularLeft
				else:
					tplist[x].polarisation = eDVBFrontendParametersSatellite.Polarisation_CircularRight
			x += 1
		return tplist

	def positionDiff(self, pos1, pos2):
		diff = pos1 - pos2
		return min(abs(diff % 3600), 3600 - abs(diff % 3600))

	def dataIsGood(self, data): # check output of the binary for nonsense values
		good = False
		low_lo = 9750
		high_lo = 10600
		c_lo = 5150
		lower_freq = self.thisRun[0]
		upper_freq = self.thisRun[1]
		high_band = self.thisRun[2]
		data_freq = int(int(data[2])/1000)
		data_symbol = int(data[3])
		lower_symbol = (self.blindscan_start_symbol.value * 1000000) - 200000
		upper_symbol = (self.blindscan_stop_symbol.value * 1000000) + 200000

		if high_band:
			data_if_freq = data_freq - high_lo
		elif self.is_c_band_scan and data_freq > 2999 and data_freq < 4201:
			data_if_freq = c_lo - data_freq
		else:
			data_if_freq = data_freq - low_lo

		if data_if_freq >= lower_freq and data_if_freq <= upper_freq:
			good = True

		if data_symbol < lower_symbol or data_symbol > upper_symbol:
			good = False

		if good == False:
			print "[Blindscan][dataIsGood] Data returned by the binary is not good...\n	Data: Frequency [%d], Symbol rate [%d]" % (int(data[2]), int(data[3]))

		return good

	def createSatellitesXMLfile(self, tp_list, save_xml_dir):
		pos = self.orb_position
		if pos > 1800:
			pos -= 3600
		if pos < 0:
			pos_name = '%dW' % (abs(int(pos))/10)
		else:
			pos_name = '%dE' % (abs(int(pos))/10)
		location = '%s/blindscan_%s_%s.xml' %(save_xml_dir, pos_name, strftime("%d-%m-%Y_%H-%M-%S"))
		tuner = nimmanager.nim_slots[self.feid].friendly_full_description
		polarisation = ['horizontal', 'vertical', 'circular left', 'circular right', 'vertical and horizontal', 'circular right and circular left']
		adjacent = ['no', 'up to 1 degree', 'up to 2 degrees', 'up to 3 degrees']
		known_txp = 'no'
		if self.filter_off_adjacent_satellites.value:
			known_txp ='yes'
		xml = ['<?xml version="1.0" encoding="iso-8859-1"?>\n\n']
		xml.append('<!--\n')
		xml.append('	File created on %s\n' % (strftime("%A, %d of %B %Y, %H:%M:%S")))
		xml.append('	using %s receiver running Enigma2 image, version %s,\n' % (getBoxType(), getImageVersion()))
		xml.append('	build %s, with the blindscan plugin \n\n' % (getImageBuild()))
		xml.append('	Search parameters:\n')
		xml.append('		%s\n' % (tuner))
		xml.append('		Satellite: %s\n' % (self.sat_name))
		xml.append('		Start frequency: %dMHz\n' % (self.blindscan_start_frequency.value))
		xml.append('		Stop frequency: %dMHz\n' % (self.blindscan_stop_frequency.value))
		xml.append('		Polarization: %s\n' % (polarisation[self.scan_sat.polarization.value]))
		xml.append('		Lower symbol rate: %d\n' % (self.blindscan_start_symbol.value * 1000))
		xml.append('		Upper symbol rate: %d\n' % (self.blindscan_stop_symbol.value * 1000))
		xml.append('		Only save unknown tranponders: %s\n' % (known_txp))
		xml.append('		Filter out adjacent satellites: %s\n' % (adjacent[self.filter_off_adjacent_satellites.value]))
		xml.append('-->\n\n')
		xml.append('<satellites>\n')
		xml.append('	<sat name="%s" flags="0" position="%s">\n' % (self.sat_name.replace('&', '&amp;'), self.orb_position))
		for tp in tp_list:
			if tp.is_id != eDVBFrontendParametersSatellite.No_Stream_Id_Filter or tp.pls_code != 0 or tp.pls_mode != eDVBFrontendParametersSatellite.PLS_Gold:
				xml.append('		<transponder frequency="%d" symbol_rate="%d" polarization="%d" fec_inner="%d" system="%d" modulation="%d" is_id="%d" pls_code="%d" pls_mode="%d" />\n' % (tp.frequency, tp.symbol_rate, tp.polarisation, tp.fec, tp.system, tp.modulation, tp.is_id, tp.pls_code, tp.pls_mode))
			else:
				xml.append('		<transponder frequency="%d" symbol_rate="%d" polarization="%d" fec_inner="%d" system="%d" modulation="%d" />\n' % (tp.frequency, tp.symbol_rate, tp.polarisation, tp.fec, tp.system, tp.modulation))
		xml.append('	</sat>\n')
		xml.append('</satellites>\n')
		open(location, "w").writelines(xml)
		return location

	def SatBandCheck(self):
		pos = self.getOrbPos()
		freq = 0
		band = 'Unknown'
		self.is_c_band_scan = False
		self.is_circular_band_scan = False
		self.is_Ku_band_scan = False
		self.is_user_defined_scan = False
		self.suggestedPolarisation = _("vertical and horizontal")
		if band == "Unknown" and self.isLNB(pos, "c_band"):
			band = 'C'
			self.is_c_band_scan = True
		if band == "Unknown" and self.isLNB(pos, "circular_lnb"):
			band = 'circular'
			self.is_circular_band_scan = True
		if band == "Unknown" and self.isLNB(pos, "universal_lnb"):
			band = 'Ku'
			self.is_Ku_band_scan = True
		if band == "Unknown" and self.isLNB(pos, "user_defined"):
			band = 'user_defined'
			self.is_user_defined_scan = True
		# if satellites.xml didn't contain any entries for this satellite check
		# LNB type instead. Assumes the tuner is configured correctly for C-band.
		print "[Blindscan][SatBandCheck] band = %s" % (band)

	def isLNB(self, cur_orb_pos, lof_type):
		nim = nimmanager.nim_slots[int(self.scan_nims.value)]
		if not self.legacy:
			nimconfig = nim.config.dvbs
		else:
			nimconfig = nim.config
		if nimconfig.configMode.getValue() == "advanced":
			currSat = nimconfig.advanced.sat[cur_orb_pos]
			lnbnum = int(currSat.lnb.getValue())
			currLnb = nimconfig.advanced.lnb[lnbnum]
			if isinstance(currLnb, ConfigNothing):
				return False
			lof = currLnb.lof.getValue()
			print "[Blindscan][isLNB] LNB type: ", lof
			if lof == lof_type:
				if lof_type == "user_defined" and (currLnb.lofl.value == 10750 and currLnb.lofh.value == 10750):
					self.is_circular_band_scan = True
					self.suggestedPolarisation = _("circular right & circular left")
					return False
				return True
		elif lof_type == "circular_lnb" and nimconfig.configMode.getValue() == "simple" and nimconfig.diseqcMode.value == "single" and cur_orb_pos in (360, 560) and nimconfig.simpleDiSEqCSetCircularLNB.value:
			return True
		elif lof_type == "universal_lnb" and nimconfig.configMode.getValue() == "simple":
			return True
		return False

	def getOrbPos(self):
		idx_selected_sat = int(self.getSelectedSatIndex(self.scan_nims.value))
		tmp_list=[self.satList[int(self.scan_nims.value)][self.scan_satselection[idx_selected_sat].index]]
		orb = tmp_list[0][0]
		print "[Blindscan][getOrbPos] orb = ", orb
		return orb

	def startScanCallback(self, answer=True):
		if answer:
			self.releaseFrontend()
			self.session.nav.playService(self.session.postScanService)
			self.close(True)

	def startDishMovingIfRotorSat(self):
		orb_pos = self.getOrbPos()
		self.feid = int(self.scan_nims.value)
		rotorSatsForNim = nimmanager.getRotorSatListForNim(self.feid)
		if len(rotorSatsForNim) < 1:
			self.releaseFrontend() # stop dish if moving due to previous call
			return False
		rotorSat = False
		for sat in rotorSatsForNim:
			if sat[0] == orb_pos:
				rotorSat = True
				break
		if not rotorSat:
			self.releaseFrontend() # stop dish if moving due to previous call
			return False
		tps = nimmanager.getTransponders(orb_pos)
		if len(tps) < 1:
			return False
		# freq, sr, pol, fec, inv, orb, sys, mod, roll, pilot
		transponder = (tps[0][1] / 1000, tps[0][2] / 1000, tps[0][3], tps[0][4], 2, orb_pos, tps[0][5], tps[0][6], tps[0][8], tps[0][9], -1, 0, 1)
		if not self.prepareFrontend():
			print "[Blindscan][startDishMovingIfRotorSat] self.prepareFrontend() failed"
			return False
		self.tuner.tune(transponder)
		return True

	def releaseFrontend(self):
		if hasattr(self, 'frontend'):
			del self.frontend
			self.frontend = None
		if hasattr(self, 'raw_channel'):
			del self.raw_channel

def BlindscanCallback(close, answer):
	if close and answer:
		close(True)

def BlindscanMain(session, close=None, **kwargs):
	have_Support_Blindscan = False
	try:
		if 'Supports_Blind_Scan: yes' in open('/proc/bus/nim_sockets').read():
			have_Support_Blindscan = True
	except:
		pass
	if have_Support_Blindscan:
		import dmmBlindScan
		session.openWithCallback(boundFunction(BlindscanCallback, close), dmmBlindScan.DmmBlindscan)
	else:
		session.openWithCallback(boundFunction(BlindscanCallback, close), Blindscan)

def BlindscanSetup(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Blind scan"), BlindscanMain, "blindscan", 25, True)]
	else:
		return []

def Plugins(**kwargs):
	if nimmanager.hasNimType("DVB-S"):
		for n in nimmanager.nim_slots:
			if n.canBeCompatible("DVB-S") and n.description not in _unsupportedNims: # DVB-S NIMs without blindscan hardware or software
				return PluginDescriptor(name=_("Blind scan"), description=_("Scan satellites for new transponders"), where = PluginDescriptor.WHERE_MENU, fnc=BlindscanSetup)
	return []

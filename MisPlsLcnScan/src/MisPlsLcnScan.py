from __future__ import print_function
# for localized messages
from . import _

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.Sources.Progress import Progress
from Components.Sources.FrontendStatus import FrontendStatus
from Components.config import config
from Components.NimManager import nimmanager

from enigma import eDVBResourceManager, eTimer, eDVBDB, eDVBFrontendParameters, eDVBFrontendParametersSatellite

from providers import PROVIDERS

import datetime
import time

import dvbreader
from MisPlsLcnScanSkin import downloadBar

class MisPlsLcnScan(Screen):
	skin = downloadBar

	def __init__(self, session, args = 0):
		print("[MisPlsLcnScan][__init__] Starting...")
		print("[MisPlsLcnScan][__init__] args", args)
		self.session = session
		Screen.__init__(self, session)
		Screen.setTitle(self, _("MIS/PLS LCN Scan"))

		self["action"] = Label(_("Starting scanner"))
		self["status"] = Label("")
		self["progress"] = ProgressBar()
		self["progress_text"] = Progress()
		self["tuner_text"] = Label("")

		self["actions"] = ActionMap(["SetupActions"],
		{
			"cancel": self.keyCancel,
		}, -2)

		self.selectedNIM = -1
		self.FTA_only = config.plugins.MisPlsLcnScan.onlyfree.value
		if args:
			pass
		self.frontend = None
		self["Frontend"] = FrontendStatus(frontend_source = lambda : self.frontend, update_interval = 100)
		self.rawchannel = None
		self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.index = 0
		self.LOCK_TIMEOUT_ROTOR = 1200 	# 100ms for tick - 120 sec
		self.LOCK_TIMEOUT_FIXED = 50 	# 100ms for tick - 5 sec
		
		self.path = "/etc/enigma2"
		self.services_dict = {}
		self.tmp_services_dict = {}
		self.namespace_dict = {} # to store namespace when sub network is enabled
		self.logical_channel_number_dict = {}
		self.ignore_visible_service_flag = False # make this a user override later if found necessary
		self.VIDEO_ALLOWED_TYPES = [1, 4, 5, 17, 22, 24, 25, 27, 135]
		self.AUDIO_ALLOWED_TYPES = [2, 10]
		self.BOUQUET_PREFIX = "userbouquet.MisPlsLcnScan."
		self.bouquetsIndexFilename = "bouquets.tv"
		self.bouquetFilename = self.BOUQUET_PREFIX + config.plugins.MisPlsLcnScan.provider.value + ".tv"
		self.bouquetName = PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["name"] # already translated
		self.namespace_complete = not (config.usage.subnetwork.value if hasattr(config.usage, "subnetwork") else True) # config.usage.subnetwork not available in all images

		self.LOCK_TIMEOUT = self.LOCK_TIMEOUT_FIXED
		self.scanTransponders = self.getMisTransponders(PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["orb_pos"])
		self.transponders_correct_onid = []
		self.onClose.append(self.__onClose)
		self.onFirstExecBegin.append(self.firstExec)

	def showError(self, message):
		question = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
		question.setTitle(_("MIS/PLS LCN Scan"))
		self.close()

	def keyCancel(self):
		self.close()

	def firstExec(self):
		if len(self.scanTransponders) > 0:
			self["action"].setText(_('Starting search...'))
			self["status"].setText(_("Scanning transponders"))
			self.progresscount = len(self.scanTransponders)
			self.progresscurrent = 1
			self["progress_text"].range = self.progresscount
			self["progress_text"].value = self.progresscurrent
			self["progress"].setRange((0, self.progresscount))
			self["progress"].setValue(self.progresscurrent)
			self.timer = eTimer()
			self.timer.callback.append(self.readStreams)
			self.timer.start(100, 1)
		else:
			self.showError(_('No frequencies to search'))

	def readStreams(self):
		self["tuner_text"].setText("")
		if self.index < len(self.scanTransponders):
			self.transpondercurrent = self.scanTransponders[self.index]
			self.progresscurrent = self.index
			self["progress_text"].value = self.progresscurrent
			self["progress"].setValue(self.progresscurrent)
			self["action"].setText(_("Tuning %s MHz, IS %s") % (str(self.transpondercurrent.frequency/1000), str(self.transpondercurrent.is_id)))
			self["status"].setText((len(self.transponders_correct_onid) == 1 and _("Found %d transponder") or _("Found %d transponders")) % len(self.transponders_correct_onid))
			self.index += 1
			self.searchtimer = eTimer()
			self.searchtimer.callback.append(self.getFrontend)
			self.searchtimer.start(100, 1)
		else:
			if len(self.transponders_correct_onid) > 0:
				self.corelate_data()
				self.createBouquet()
				answer = [self.selectedNIM, self.transponders_correct_onid]
			else:
				answer = None
			self.close(answer)

	def getMisTransponders(self, pos):
		tlist = []
		def isMultistreamTP(tp):
			# since we are using Gold sequences there is no need to check the PLS Mode
			return tp[5] == eDVBFrontendParametersSatellite.System_DVB_S2 and (tp[10] > eDVBFrontendParametersSatellite.No_Stream_Id_Filter or tp[12] > eDVBFrontendParametersSatellite.PLS_Default_Gold_Code)
		for tp in [tp for tp in nimmanager.getTransponders(pos) if isMultistreamTP(tp)]:
			if tp[0] == 0:
				parm = eDVBFrontendParametersSatellite()
				parm.frequency = tp[1]
				parm.symbol_rate = tp[2]
				parm.polarisation = tp[3]
				parm.fec = tp[4]
				parm.inversion = tp[7]
				parm.orbital_position = pos
				parm.system = tp[5]
				parm.modulation = tp[6]
				parm.rolloff = tp[8]
				parm.pilot = tp[9]
				parm.is_id = tp[10]
				parm.pls_mode = tp[11]
				parm.pls_code = tp[12]
				if hasattr(parm, "t2mi_plp_id") and len(tp) > 13:
					parm.t2mi_plp_id = tp[13]
					if hasattr(parm, "t2mi_pid") and len(tp) > 14:
						parm.t2mi_pid = tp[14]
				tlist.append(parm)
		return tlist

	def isRotorSat(self, slot, orb_pos):
		rotorSatsForNim = nimmanager.getRotorSatListForNim(slot)
		if len(rotorSatsForNim) > 0:
			for sat in rotorSatsForNim:
				if sat[0] == orb_pos:
					return True
		return False

	def getFrontend(self):
		print("[MisPlsLcnScan][getFrontend] searching for available tuner")
		nimList = []
		for nim in nimmanager.nim_slots:
			if not nim.isCompatible("DVB-S") or \
				not nim.isMultistream() or \
				nim.isFBCLink() or \
				(hasattr(nim, 'config_mode_dvbs') and nim.config_mode_dvbs or nim.config_mode) in ("loopthrough", "satposdepends", "nothing") or \
				self.transpondercurrent.orbital_position not in [sat[0] for sat in nimmanager.getSatListForNim(nim.slot)]:
				continue
			nimList.append(nim.slot)

		if len(nimList) == 0:
			print("[MisPlsLcnScan][getFrontend] No compatible tuner found")
			self.showError(_('No compatible tuner found'))
			return

		resmanager = eDVBResourceManager.getInstance()
		if not resmanager:
			print("[MisPlsLcnScan][getFrontend] Cannot retrieve Resource Manager instance")
			self.showError(_('Cannot retrieve Resource Manager instance'))
			return

		# stop pip if running
		if self.session.pipshown:
			self.session.pipshown = False
			del self.session.pip
			print("[MisPlsLcnScan][getFrontend] Stopping PIP.")

		# stop currently playing service if it is using a tuner in ("loopthrough", "satposdepends")
		currentlyPlayingNIM = None
		currentService = self.session and self.session.nav.getCurrentService()
		frontendInfo = currentService and currentService.frontendInfo()
		frontendData = frontendInfo and frontendInfo.getAll(True)
		if frontendData is not None:
			currentlyPlayingNIM = frontendData.get("tuner_number", None)
			if currentlyPlayingNIM is not None and nimmanager.nim_slots[currentlyPlayingNIM].isCompatible("DVB-S"):
				nimConfigMode = hasattr(nimmanager.nim_slots[currentlyPlayingNIM], "config_mode_dvbs") and nimmanager.nim_slots[currentlyPlayingNIM].config_mode_dvbs or nimmanager.nim_slots[currentlyPlayingNIM].config_mode
				if nimConfigMode in ("loopthrough", "satposdepends"):
					self.postScanService = self.session.nav.getCurrentlyPlayingServiceReference()
					self.session.nav.stopService()
					currentlyPlayingNIM = None
					print("[MisPlsLcnScan][getFrontend] The active service was using a %s tuner, so had to be stopped (slot id %s)." % (nimConfigMode, currentlyPlayingNIM))
		del frontendInfo
		del currentService

		current_slotid = -1
		if self.rawchannel:
			del(self.rawchannel)

		self.frontend = None
		self.rawchannel = None

		nimList = [slot for slot in nimList if not self.isRotorSat(slot, self.transpondercurrent.orbital_position)] + [slot for slot in nimList if self.isRotorSat(slot, self.transpondercurrent.orbital_position)] #If we have a choice of dishes try "fixed" before "motorised".
		for slotid in nimList:
			if current_slotid == -1:	# mark the first valid slotid in case of no other one is free
				current_slotid = slotid

			self.rawchannel = resmanager.allocateRawChannel(slotid)
			if self.rawchannel:
				print("[MisPlsLcnScan][getFrontend] Nim found on slot id %d with sat %s" % (slotid, nimmanager.getSatName(self.transpondercurrent.orbital_position)))
				current_slotid = slotid
				break

			if self.rawchannel:
				break

		if current_slotid == -1:
			print("[MisPlsLcnScan][getFrontend] No valid NIM found")
			self.showError(_('No valid NIM found for %s') % PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["name"])
			return

		if not self.rawchannel:
			# if we are here the only possible option is to close the active service
			if currentlyPlayingNIM in nimList:
				slotid = currentlyPlayingNIM
				print("[MisPlsLcnScan][getFrontend] Nim found on slot id %d but it's busy. Stopping active service" % slotid)
				self.postScanService = self.session.nav.getCurrentlyPlayingServiceReference()
				self.session.nav.stopService()
				self.rawchannel = resmanager.allocateRawChannel(slotid)
				if self.rawchannel:
					print("[MisPlsLcnScan][getFrontend] The active service was stopped, and the NIM is now free to use.")
					current_slotid = slotid

			if not self.rawchannel:
				if self.session.nav.RecordTimer.isRecording():
					print("[MisPlsLcnScan][getFrontend] Cannot free NIM because a recording is in progress")
					self.showError(_('Cannot free NIM because a recording is in progress'))
					return
				else:
					print("[MisPlsLcnScan][getFrontend] Cannot get the NIM")
					self.showError(_('Cannot get the NIM'))
					return

		# set extended timeout for rotors
		self.motorised = False
		if self.isRotorSat(current_slotid, self.transpondercurrent.orbital_position):
			self.motorised = True
			self.LOCK_TIMEOUT = self.LOCK_TIMEOUT_ROTOR
			print("[MisPlsLcnScan][getFrontend] Motorised dish. Will wait up to %i seconds for tuner lock." % (self.LOCK_TIMEOUT/10))
		else:
			self.LOCK_TIMEOUT = self.LOCK_TIMEOUT_FIXED
			print("[MisPlsLcnScan][getFrontend] Fixed dish. Will wait up to %i seconds for tuner lock." % (self.LOCK_TIMEOUT/10))

		self.selectedNIM = current_slotid  # Remember for downloading SI tables
		
		self["tuner_text"].setText(chr(ord('A') + current_slotid))
		
		self.frontend = self.rawchannel.getFrontend()
		if not self.frontend:
			print("[MisPlsLcnScan][getFrontend] Cannot get frontend")
			self.showError(_('Cannot get frontend'))
			return

		self.demuxer_id = self.rawchannel.reserveDemux()
		if self.demuxer_id < 0:
			print("[ABM-main][doTune] Cannot allocate the demuxer.")
			self.showError(_('Cannot allocate the demuxer.'))
			return

		params_fe = eDVBFrontendParameters()
		params_fe.setDVBS(self.transpondercurrent, False)

#		try:
#			self.rawchannel.requestTsidOnid()
#		except (TypeError):
#			# for compatibility with some third party images
#			self.rawchannel.requestTsidOnid(self.gotTsidOnid)

		self.frontend.tune(params_fe)

		self.lockcounter = 0
		self.locktimer = eTimer()
		self.locktimer.callback.append(self.checkTunerLock)
		self.locktimer.start(100, 1)

	def checkTunerLock(self):
		self.dict = {}
		self.frontend.getFrontendStatus(self.dict)
		if self.dict["tuner_state"] == "TUNING":
			if self.lockcounter < 1: # only show this once in the log per retune event
				print("[MakeBouquet][checkTunerLock] TUNING")
		elif self.dict["tuner_state"] == "LOCKED":
			print("[MakeBouquet][checkTunerLock] TUNER LOCKED")
			self["action"].setText(_("Reading SI tables on %s MHz, IS %s") % (str(self.transpondercurrent.frequency/1000), str(self.transpondercurrent.is_id)))
			#self["status"].setText(_("???"))

			self.readTransponderCounter = 0
			self.readTranspondertimer = eTimer()
			self.readTranspondertimer.callback.append(self.readTransponder)
			self.readTranspondertimer.start(100, 1)
			return
		elif self.dict["tuner_state"] in ("LOSTLOCK", "FAILED"):
			print("[MakeBouquet][checkTunerLock] TUNING FAILED")
			self.readStreams()
			return

		self.lockcounter += 1
		if self.lockcounter > self.LOCK_TIMEOUT:
			print("[MakeBouquet][checkTunerLock] Timeout for tuner lock")
			self.readStreams()
			return
		self.locktimer.start(100, 1)

	def readTransponder(self):
		self.readSDT()
		if self.onid in PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["onids"]:
			self.transponders_correct_onid.append(self.transpondercurrent)
			self.readNIT()
		self.readStreams()

	def readSDT(self):
		adapter = 0
		demuxer_device = "/dev/dvb/adapter%d/demux%d" % (adapter, self.demuxer_id)

		self.tsid = None
		self.onid = None
		sdt_pid = 0x11
		sdt_current_table_id = 0x42
		mask = 0xff # only read SDT actual, not SDT other.
		sdtTimeout = 5 # maximum time allowed to read the service descriptor table (seconds)

		sdt_current_version_number = -1
		sdt_current_sections_read = []
		sdt_current_sections_count = 0
		sdt_current_content = []
		sdt_current_completed = False

		fd = dvbreader.open(demuxer_device, sdt_pid, sdt_current_table_id, mask, self.selectedNIM)
		if fd < 0:
			print("[MisPlsLcnScan][readSDT] Cannot open the demuxer")
			return None

		timeout = datetime.datetime.now()
		timeout += datetime.timedelta(0, sdtTimeout)

		while True:
			if datetime.datetime.now() > timeout:
				print("[MisPlsLcnScan][readSDT] Timed out")
				break

			section = dvbreader.read_sdt(fd, sdt_current_table_id, 0x00)
			if section is None:
				time.sleep(0.1)	# no data.. so we wait a bit
				continue

			if section["header"]["table_id"] == sdt_current_table_id and not sdt_current_completed:
				if section["header"]["version_number"] != sdt_current_version_number:
					sdt_current_version_number = section["header"]["version_number"]
					sdt_current_sections_read = []
					sdt_current_sections_count = section["header"]["last_section_number"] + 1
					sdt_current_content = []

				if section["header"]["section_number"] not in sdt_current_sections_read:
					sdt_current_sections_read.append(section["header"]["section_number"])
					sdt_current_content += section["content"]
					if self.tsid is None or self.onid is None: # save first read of tsid and onid.
						self.tsid = section["header"]["transport_stream_id"]
						self.onid = section["header"]["original_network_id"]
						if self.onid not in PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["onids"]:
							dvbreader.close(fd)
							return

					if len(sdt_current_sections_read) == sdt_current_sections_count:
						sdt_current_completed = True

			if sdt_current_completed:
				break

		dvbreader.close(fd)

		if not sdt_current_content:
			print("[MisPlsLcnScan][readSDT] no services found on transponder")
			return

		for i in range(len(sdt_current_content)):
			service = sdt_current_content[i]

			if self.FTA_only and service["free_ca"] != 0:
				continue

			if service["service_type"] not in self.VIDEO_ALLOWED_TYPES and service["service_type"] not in self.AUDIO_ALLOWED_TYPES:
				continue

			servicekey = "%x:%x:%x" % (service["transport_stream_id"], service["original_network_id"], service["service_id"])
			self.tmp_services_dict[servicekey] = service

	def readNIT(self):
		adapter = 0
		demuxer_device = "/dev/dvb/adapter%d/demux%d" % (adapter, self.demuxer_id)

		nit_current_pid = 0x10
		nit_current_table_id = 0x40
		nit_other_table_id = 0x00 # don't read other table
		if nit_other_table_id == 0x00:
			mask = 0xff
		else:
			mask = nit_current_table_id ^ nit_other_table_id ^ 0xff
		nit_current_timeout = 20 # maximum time allowed to read the network information table (seconds)

		nit_current_version_number = -1
		nit_current_sections_read = []
		nit_current_sections_count = 0
		nit_current_content = []
		nit_current_completed = False

		fd = dvbreader.open(demuxer_device, nit_current_pid, nit_current_table_id, mask, self.selectedNIM)
		if fd < 0:
			print("[MakeBouquet][readNIT] Cannot open the demuxer")
			return

		timeout = datetime.datetime.now()
		timeout += datetime.timedelta(0, nit_current_timeout)

		while True:
			if datetime.datetime.now() > timeout:
				print("[MakeBouquet][readNIT] Timed out reading NIT")
				break

			section = dvbreader.read_nit(fd, nit_current_table_id, nit_other_table_id)
			if section is None:
				time.sleep(0.1)	# no data.. so we wait a bit
				continue

			if section["header"]["table_id"] == nit_current_table_id and not nit_current_completed:
				if section["header"]["version_number"] != nit_current_version_number:
					nit_current_version_number = section["header"]["version_number"]
					nit_current_sections_read = []
					nit_current_sections_count = section["header"]["last_section_number"] + 1
					nit_current_content = []

				if section["header"]["section_number"] not in nit_current_sections_read:
					nit_current_sections_read.append(section["header"]["section_number"])
					nit_current_content += section["content"]

					if len(nit_current_sections_read) == nit_current_sections_count:
						nit_current_completed = True

			if nit_current_completed:
				break

		dvbreader.close(fd)

		if not nit_current_content:
			print("[MakeBouquet][readNIT] current transponder not found")
			return

		LCNs = [t for t in nit_current_content if "descriptor_tag" in t and t["descriptor_tag"] == 0x83 and t["original_network_id"] in PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["onids"]]
		print("[MakeBouquet][readNIT] LCNs", LCNs)
		if LCNs:
			for LCN in LCNs:
				LCNkey = "%x:%x:%x" % (LCN["transport_stream_id"], LCN["original_network_id"], LCN["service_id"])

				if not self.ignore_visible_service_flag and "visible_service_flag" in LCN and LCN["visible_service_flag"] == 0:
					continue

				# Only write to the dict if there is no entry, or override the entry if the data comes from the same transponder the channel is located on.
				if LCNkey not in self.logical_channel_number_dict or LCN["transport_stream_id"] == self.tsid:
					self.logical_channel_number_dict[LCNkey] = LCN

		namespace = self.transpondercurrent.orbital_position << 16
		if self.namespace_complete:
			namespace |= ((self.transpondercurrent.frequency / 1000) & 0xFFFF) | ((self.transpondercurrent.polarisation & 1) << 15)
		namespacekey = "%x:%x" % (self.tsid, self.onid)
		self.namespace_dict[namespacekey] = namespace

	def corelate_data(self):
		servicekeys = self.tmp_services_dict.keys()
		for servicekey in servicekeys:
			if servicekey in self.logical_channel_number_dict and (self.logical_channel_number_dict[servicekey]["logical_channel_number"] not in self.services_dict or \
				"priority" in PROVIDERS[config.plugins.MisPlsLcnScan.provider.value] and servicekey in PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["priority"]): # this line decides who wins if an LCN maps to more than one service
				self.tmp_services_dict[servicekey]["logical_channel_number"] = self.logical_channel_number_dict[servicekey]["logical_channel_number"]
				self.services_dict[self.logical_channel_number_dict[servicekey]["logical_channel_number"]] = self.tmp_services_dict[servicekey]

		if "overrides" in PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]: # ability to force missing LCNs
			for override in PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["overrides"]:
				if override in servicekeys:
					self.tmp_services_dict[override]["logical_channel_number"] = PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["overrides"][override]
					self.services_dict[PROVIDERS[config.plugins.MisPlsLcnScan.provider.value]["overrides"][override]] = self.tmp_services_dict[override]
					
		# for debug only
		for key in self.dict_sorter(self.tmp_services_dict, "service_name"):
			print("[service]", key, self.tmp_services_dict[key])

	def dict_sorter(self, in_dict, sort_by):
		sort_list = [(x[0], x[1][sort_by]) for x in in_dict.items()]
		return [x[0] for x in sorted(sort_list, key=lambda listItem: listItem[1])]

	def readBouquetIndex(self):
		try:
			bouquets = open(self.path + "/" + self.bouquetsIndexFilename, "r")
		except Exception as e:
			return ""
		content = bouquets.read()
		bouquets.close()
		return content

	def writeBouquetIndex(self, bouquetIndexContent):
		bouquets_tv_list = []
		bouquets_tv_list.append("#NAME Bouquets (TV)\n")
		bouquets_tv_list.append("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % self.bouquetFilename)
		if bouquetIndexContent:
			lines = bouquetIndexContent.split("\n", 1)
			if lines[0][:6] != "#NAME ":
				bouquets_tv_list.append("%s\n" % lines[0])
			if len(lines) > 1:
				bouquets_tv_list.append("%s" % lines[1])

		bouquets_tv = open(self.path + "/" + self.bouquetsIndexFilename, "w")
		bouquets_tv.write(''.join(bouquets_tv_list))
		bouquets_tv.close()
		del bouquets_tv_list

	def writeBouquet(self):
		bouquet_list = []
		bouquet_list.append("#NAME %s\n" % self.bouquetName)

		numbers = range(1, 1001)
		for number in numbers:
			if number in self.services_dict:
				bouquet_list.append(self.bouquetServiceLine(self.services_dict[number]))
			else:
				bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
				bouquet_list.append("#DESCRIPTION  \n")

		bouquetFile = open(self.path + "/" + self.bouquetFilename, "w")
		bouquetFile.write(''.join(bouquet_list))
		bouquetFile.close()
		del bouquet_list

	def bouquetServiceLine(self, service):
		return "#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
			service["service_type"],
			service["service_id"],
			service["transport_stream_id"],
			service["original_network_id"],
			self.getNamespace(service)
		)

	def getNamespace(self, service):
		namespacekey = "%x:%x" % (service["transport_stream_id"], service["original_network_id"])
		return self.namespace_dict[namespacekey] if namespacekey in self.namespace_dict else 0xBAD00BAD

	def createBouquet(self):
		bouquetIndexContent = self.readBouquetIndex()
		if '"' + self.bouquetFilename + '"' not in bouquetIndexContent: # only edit the index if bouquet file is not present
			self.writeBouquetIndex(bouquetIndexContent)
		self.writeBouquet()

		eDVBDB.getInstance().reloadBouquets()

	def __onClose(self):
		if self.frontend:
			self.frontend = None
			del(self.rawchannel)


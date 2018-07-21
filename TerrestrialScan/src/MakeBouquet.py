# for localized messages
from . import _

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.Sources.Progress import Progress
from Components.config import config

from enigma import eDVBResourceManager, eTimer, eDVBDB

import os
import sys

import datetime
import time

from Tools.Directories import resolveFilename, fileExists
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	pass

from TerrestrialScan import setParams, setParamsFe

from Plugins.SystemPlugins.AutoBouquetsMaker.scanner import dvbreader

class MakeBouquet(Screen):
	skin = """
	<screen position="c-300,e-80" size="600,70" flags="wfNoBorder" >
		<widget name="background" position="0,0" size="600,70" zPosition="-1" />
		<widget name="action" halign="center" valign="center" position="65,10" size="520,20" font="Regular;18" backgroundColor="#11404040" transparent="1" />
		<widget name="status" halign="center" valign="center" position="65,35" size="520,20" font="Regular;18" backgroundColor="#11000000" transparent="1" />
		<widget name="progress" position="65,55" size="520,5" borderWidth="1" backgroundColor="#11000000"/>
	</screen>"""

	def __init__(self, session, args = 0):
		print "[MakeBouquet][__init__] Starting..."
		print "[MakeBouquet][__init__] args", args
		self.session = session
		Screen.__init__(self, session)
		Screen.setTitle(self, _("MakeBouquet"))
		self.skinName = ["TerrestrialScan"]

		self.path = "/etc/enigma2"
		self.services_dict = {}
		self.tmp_services_dict = {}
		self.namespace_dict = {} # to store namespace when sub network is enabled
		self.logical_channel_number_dict = {}
		self.ignore_visible_service_flag = False # make this a user override later if found necessary
		self.VIDEO_ALLOWED_TYPES = [1, 4, 5, 17, 22, 24, 25, 27, 135]
		self.AUDIO_ALLOWED_TYPES = [2, 10]
		self.BOUQUET_PREFIX = "userbouquet.TerrestrialScan."
		self.bouquetsIndexFilename = "bouquets.tv"
		self.bouquetFilename = self.BOUQUET_PREFIX + "tv"
		self.bouquetName = _('Terrestrial')
		self.namespace_complete_terrestrial = not (config.usage.subnetwork_terrestrial.value if hasattr(config.usage, "subnetwork_terrestrial") else True) # config.usage.subnetwork not available in all images

		self["background"] = Pixmap()
		self["action"] = Label(_("Starting scanner"))
		self["status"] = Label("")
		self["progress"] = ProgressBar()
		self["progress_text"] = Progress()

		self["actions"] = ActionMap(["SetupActions"],
		{
			"cancel": self.keyCancel,
		}, -2)

		self.selectedNIM = -1
		self.transponders_unique = {}
		self.FTA_only = False
		if args:
			if "feid" in args:
				self.selectedNIM = args["feid"]
			if "transponders_unique" in args:
				self.transponders_unique = args["transponders_unique"]
			if "FTA_only" in args:
				self.FTA_only = args["FTA_only"]

		self.tsidOnidKeys = self.transponders_unique.keys()
		self.index = 0
		self.lockTimeout = 50 	# 100ms for tick - 5 sec

		self.frontend = None
		self.rawchannel = None

		self.onClose.append(self.__onClose)
		self.onFirstExecBegin.append(self.firstExec)

	def firstExec(self):
		try:
			png = resolveFilename(SCOPE_ACTIVE_SKIN, "terrestrialscan/background.png")
		except:
			png = None
		if not png or not fileExists(png):
			png = "%s/images/background.png" % os.path.dirname(sys.modules[__name__].__file__)
		self["background"].instance.setPixmapFromFile(png)

		if len(self.transponders_unique) > 0:
			self["action"].setText(_('Making bouquet...'))
			self["status"].setText(_("Reading streams"))
			self.progresscount = len(self.transponders_unique)
			self.progresscurrent = 1
			self["progress_text"].range = self.progresscount
			self["progress_text"].value = self.progresscurrent
			self["progress"].setRange((0, self.progresscount))
			self["progress"].setValue(self.progresscurrent)
			self.timer = eTimer()
			self.timer.callback.append(self.readStreams)
			self.timer.start(100, 1)
		else:
			self.showError(_('No transponders to read'))

	def readStreams(self):
		if self.index < len(self.transponders_unique):
			self.transponder = self.transponders_unique[self.tsidOnidKeys[self.index]]
			self.progresscurrent = self.index
			self["progress_text"].value = self.progresscurrent
			self["progress"].setValue(self.progresscurrent)
			self["action"].setText(_("Tuning %s MHz") % str(self.transponder["frequency"]/1000000))
			self["status"].setText(_("TSID: %d, ONID: %d") % (self.transponder["tsid"], self.transponder["onid"]))
			self.index += 1
			self.searchtimer = eTimer()
			self.searchtimer.callback.append(self.getFrontend)
			self.searchtimer.start(100, 1)
		else:
			if len(self.transponders_unique) > 0:
				self.corelate_data()
				if len(self.services_dict) > 0:
					self.createBouquet()
				answer = [self.selectedNIM, self.transponders_unique]
			else:
				answer = None
			self.close(answer)

	def getFrontend(self):
		resmanager = eDVBResourceManager.getInstance()
		if not resmanager:
			print "[MakeBouquet][getFrontend] Cannot retrieve Resource Manager instance"
			self.showError(_('Cannot retrieve Resource Manager instance'))
			return

		if self.rawchannel:
			del(self.rawchannel)

		self.frontend = None
		self.rawchannel = None

		self.rawchannel = resmanager.allocateRawChannel(self.selectedNIM)
		if not self.rawchannel:
			print "[MakeBouquet][getFrontend] Cannot get the NIM"
			self.showError(_('Cannot get the NIM'))
			return

		print "[MakeBouquet][getFrontend] Will wait up to %i seconds for tuner lock." % (self.lockTimeout/10)

		self.frontend = self.rawchannel.getFrontend()
		if not self.frontend:
			print "[MakeBouquet][getFrontend] Cannot get frontend"
			self.showError(_('Cannot get frontend'))
			return

		self.demuxer_id = self.rawchannel.reserveDemux()
		if self.demuxer_id < 0:
			print>>log, "[MakeBouquet][getFrontend] Cannot allocate the demuxer"
			self.showError(_('Cannot allocate the demuxer'))
			return

		self.frontend.tune(setParamsFe(setParams(self.transponder["frequency"], self.transponder["system"], self.transponder["bandwidth"])))

		self.lockcounter = 0
		self.locktimer = eTimer()
		self.locktimer.callback.append(self.checkTunerLock)
		self.locktimer.start(100, 1)

	def checkTunerLock(self):
		self.dict = {}
		self.frontend.getFrontendStatus(self.dict)
		if self.dict["tuner_state"] == "TUNING":
			print "[MakeBouquet][checkTunerLock] TUNING"
		elif self.dict["tuner_state"] == "LOCKED":
			print "[MakeBouquet][checkTunerLock] TUNER LOCKED"
			self["action"].setText(_("Reading SI tables on %s MHz") % str(self.transponder["frequency"]/1000000))
			#self["status"].setText(_("???"))

			self.readTransponderCounter = 0
			self.readTranspondertimer = eTimer()
			self.readTranspondertimer.callback.append(self.readTransponder)
			self.readTranspondertimer.start(100, 1)
			return
		elif self.dict["tuner_state"] in ("LOSTLOCK", "FAILED"):
			print "[MakeBouquet][checkTunerLock] TUNING FAILED"
			self.readStreams()
			return

		self.lockcounter += 1
		if self.lockcounter > self.lockTimeout:
			print "[MakeBouquet][checkTunerLock] Timeout for tuner lock"
			self.readStreams()
			return
		self.locktimer.start(100, 1)

	def readTransponder(self):
		self.readSDT()
		self.readNIT()
		self.readStreams()

	def readSDT(self):
		adapter = 0
		demuxer_device = "/dev/dvb/adapter%d/demux%d" % (adapter, self.demuxer_id)

		self.tsid = None
		self.onid = None
		sdt_pid = 0x11
		sdt_current_table_id = 0x42
		mask = 0xff
		sdtTimeout = 5 # maximum time allowed to read the service descriptor table (seconds)

		sdt_current_version_number = -1
		sdt_current_sections_read = []
		sdt_current_sections_count = 0
		sdt_current_content = []
		sdt_current_completed = False

		fd = dvbreader.open(demuxer_device, sdt_pid, sdt_current_table_id, mask, self.selectedNIM)
		if fd < 0:
			print "[MakeBouquet][readSDT] Cannot open the demuxer"
			return None

		timeout = datetime.datetime.now()
		timeout += datetime.timedelta(0, sdtTimeout)

		while True:
			if datetime.datetime.now() > timeout:
				print "[Satfinder][getCurrentTsidOnid] Timed out"
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
					if self.tsid is None or self.onid is None: # save first read of tsid and onid, although data in self.transponder should already be correct.
						self.tsid = self.transponder["tsid"] = section["header"]["transport_stream_id"]
						self.onid = self.transponder["onid"] = section["header"]["original_network_id"]

					if len(sdt_current_sections_read) == sdt_current_sections_count:
						sdt_current_completed = True

			if sdt_current_completed:
				break

		dvbreader.close(fd)

		if not sdt_current_content:
			print "[MakeBouquet][readSDT] no services found on transponder"
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
			print "[MakeBouquet][readNIT] Cannot open the demuxer"
			return

		timeout = datetime.datetime.now()
		timeout += datetime.timedelta(0, nit_current_timeout)

		while True:
			if datetime.datetime.now() > timeout:
				print "[MakeBouquet][readNIT] Timed out reading NIT"
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
			print "[MakeBouquet][readNIT] current transponder not found"
			return

		# descriptor_tag 0x5A is DVB-T, descriptor_tag 0x7f is DVB-T
		transponders = [t for t in nit_current_content if "descriptor_tag" in t and t["descriptor_tag"] in (0x5A, 0x7f) and t["original_network_id"] == self.transponder["onid"] and t["transport_stream_id"] == self.transponder["tsid"]] # this should only ever have a length of one transponder
		print "[MakeBouquet][readNIT] transponders", transponders
		if transponders:

			if transponders[0]["descriptor_tag"] == 0x5A: # DVB-T
				self.transponder["system"] = 0
			else: # must be DVB-T2
				self.transponder["system"] = 1

			if "frequency" in transponders[0] and abs((transponders[0]["frequency"]*10) - self.transponder["frequency"]) < 1000000:
				print "[MakeBouquet][readNIT] updating transponder frequency from %d MHz to %d MHz" % (self.transponder["frequency"]/1000000, transponders[0]["frequency"]/100000)
				self.transponder["frequency"] = transponders[0]["frequency"]*10

		LCNs = [t for t in nit_current_content if "descriptor_tag" in t and t["descriptor_tag"] == 0x83 and t["original_network_id"] == self.transponder["onid"]]
		print "[MakeBouquet][readNIT] LCNs", LCNs
		if LCNs:
			for LCN in LCNs:
				LCNkey = "%x:%x:%x" % (LCN["transport_stream_id"], LCN["original_network_id"], LCN["service_id"])

				if not self.ignore_visible_service_flag and "visible_service_flag" in LCN and LCN["visible_service_flag"] == 0:
					continue

				# Only write to the dict if there is no entry, or override the entry if the data comes from the same transponder the channel is located on.
				if LCNkey not in self.logical_channel_number_dict or LCN["transport_stream_id"] == self.transponder["tsid"]:
					self.logical_channel_number_dict[LCNkey] = LCN

		namespace = 0xEEEE0000
		if self.namespace_complete_terrestrial:
			namespace |= (self.transponder['frequency']/1000000)&0xFFFF
		namespacekey = "%x:%x" % (self.transponder["tsid"], self.transponder["onid"])
		self.namespace_dict[namespacekey] = namespace

	def createBouquet(self):
		bouquetIndexContent = self.readBouquetIndex()
		if '"' + self.bouquetFilename + '"' not in bouquetIndexContent: # only edit the index if bouquet file is not present
			self.writeBouquetIndex(bouquetIndexContent)
		self.writeBouquet()

		eDVBDB.getInstance().reloadBouquets()

	def corelate_data(self):
		servicekeys = self.tmp_services_dict.keys()
		for servicekey in servicekeys:
			if servicekey in self.logical_channel_number_dict and self.logical_channel_number_dict[servicekey]["logical_channel_number"] not in self.services_dict:
				self.tmp_services_dict[servicekey]["logical_channel_number"] = self.logical_channel_number_dict[servicekey]["logical_channel_number"]
				self.services_dict[self.logical_channel_number_dict[servicekey]["logical_channel_number"]] = self.tmp_services_dict[servicekey]

	def readBouquetIndex(self):
		try:
			bouquets = open(self.path + "/" + self.bouquetsIndexFilename, "r")
		except Exception, e:
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
		return self.namespace_dict[namespacekey] if namespacekey in self.namespace_dict else 0xEEEE0000

	def showError(self, message):
		question = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
		question.setTitle(_("TerrestrialScan"))
		self.close()

	def keyCancel(self):
		self.close()

	def __onClose(self):
		if self.frontend:
			self.frontend = None
			del(self.rawchannel)
# for localized messages
from . import _
from Components.ActionMap import NumberActionMap, ActionMap
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigInteger, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.NimManager import nimmanager, getConfigSatlist
from Components.Sources.CanvasSource import CanvasSource
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from enigma import eDVBFrontendParameters, eDVBFrontendParametersSatellite, eComponentScan, eTimer, eDVBResourceManager, getDesktop
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.ServiceScan import ServiceScan
from time import time, strftime
from Components.About import about
from Tools.Directories import fileExists
from Tools.Transponder import ConvertToHumanReadable

from filters import TransponderFiltering # imported from Blindscan folder

XML_BLINDSCAN_DIR = "/tmp"

try:
	boxtype = open("/proc/stb/info/model").read().strip()
except:
	boxtype = ""

def insertValues(xml, values):
	# The skin template is designed for an HD screen so the scaling factor is 720.
	# double negative to round up not round down
	return xml % tuple([int(-(x * getDesktop(0).size().height() // (-720))) for x in values])

class DmmBlindscanState(Screen):
	skin = insertValues("""
	<screen position="center,center" size="%d,%d" title="Satellite Blindscan">
		<widget name="text" position="%d,%d" size="%d,%d" font="Regular;%d" />
		<widget name="progress" position="%d,%d" size="%d,%d" font="Regular;%d" />
		<eLabel	position="%d,%d" size="%d,%d" backgroundColor="grey"/>
		<widget source="list" render="Listbox" position="%d,%d" size="%d,%d" scrollbarMode="showAlways" >
			<convert type="TemplatedMultiContent">
				{"template": [ MultiContentEntryText(pos = (%d, %d), size = (%d, %d), flags = RT_HALIGN_LEFT, text = %d) ],
				 "fonts": [gFont("Regular", %d)],
				 "itemHeight": %d
				}
			</convert>
		</widget>
		<eLabel	position="%d,%d" size="%d,%d" backgroundColor="grey"/>
		<widget name="post_action" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center"/>
		<widget source="constellation" render="Canvas" position="%d-128,%d-128" size="256,256" correct_aspect="width" />
		<eLabel	position="%d,%d" size="%d,%d" backgroundColor="grey"/>
		<widget source="key_red" render="Label" position="%d,e-%d" size="%d,%d" backgroundColor="#0x009f1313" font="Regular;%d" foregroundColor="#0x00ffffff" halign="center" valign="center" />
		<widget source="key_green" render="Label" position="%d,e-%d" size="%d,%d" backgroundColor="#0x001f771f" font="Regular;%d" foregroundColor="#0x00ffffff" halign="center" valign="center" />
	</screen>
	""", [
		820, 580, # screen
		10, 10, 800, 25, 20, # text
		10, 40, 800, 25, 20, # progress
		10, 70, 800, 1, # eLabel
		10, 82, 524, 425, # list
		5, 2, 514, 22, 0, # template
		19, # fonts
		25, # itemHeight
		544, 70, 1, 449, # eLabel
		554, 90, 256, 140, 19, # post_action
		682, 382, # constellation, 554 + 128 = 682, 254 + 128 = 382
		10, 519, 800, 1, # eLabel
		15, 50, 180, 40, 20, # key_red
		210, 50, 180, 40, 20 # key_green
		])

	def __init__(self, session, fe_num, text):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Blind scan state"))
		self.skinName = ["DmmBlindscanState", "SatBlindscanState2"]
		self["list"] = List()
		self["text"] = Label()
		self["text"].setText(text)
		self["post_action"] = Label()
		self["progress"] = Label()
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText("Auto / Manual")
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyGreen,
		}, -2)
		self.fe_num = fe_num
		self["constellation"] = CanvasSource()
		self.onLayoutFinish.append(self.updateConstellation)
		self.tmr = eTimer()
		self.tmr.callback.append(self.updateConstellation)
		self.constellation_supported = None
		if fe_num != -1:
			self.post_action = 1
			self.finished = 0
			self.keyGreen()
		else:
			self.post_action = -1

	def keyGreen(self):
		if self.finished:
			self.close(True)
		elif self.post_action != -1:
			self.post_action ^= 1
			if self.post_action:
				self["post_action"].setText(_("Service searching to be started MANUALLY by the user. To change this press green."))
			else:
				self["post_action"].setText(_("Service searching will start AUTOMATICALLY. To change this press green."))

	def setFinished(self):
		if self.post_action:
			self.finished = 1
			self["text"].setText(_("Transponder searching finished!"))
			self["post_action"].setText(_("Press green to start service searching."))
		else:
			self.close(True)

	def getConstellationBitmap(self, cnt=1):
		ret = []
		path = "/proc/stb/frontend/%d/constellation_bitmap" % self.fe_num
		if self.constellation_supported is None:
			s = fileExists(path)
			self.constellation_supported = s
			if not s:
				self["constellation"].fill(0,0,256,256,0x25101010)
				self["constellation"].flush()

		if self.constellation_supported:
			while cnt > 0:
				f = open(path, "r")
				ret.append(f.readline())
				cnt -= 1
				f.close()
		return ret

	def updateConstellation(self, constellation_bitmap_list=None):
		if not (self.constellation_supported or self.constellation_supported is None):
			return
		self["constellation"].fill(0,0,256,256,0x25101010)
		if constellation_bitmap_list:
			bitmap_list = constellation_bitmap_list
		else:
			bitmap_list = self.getConstellationBitmap()
		for bitmap in bitmap_list:
			Q = []
			I = []
			for pos in range(0,30,2):
				try:
					val = int(bitmap[pos:pos + 2], 16)
					val = 128 + (val - 256 if val > 127 else val)
					#val = (int(bitmap[pos:pos+2], 16) + 128) & 0xff
				except ValueError:
					print "[dmmBlindscan][updateConstellation] I constellation data broken at pos", pos
					val = 0
				I.append(val)
			for pos in range(30,60,2):
				try:
					val = int(bitmap[pos:pos + 2], 16)
					val = 128 + (val - 256 if val > 127 else val)
					#val = (int(bitmap[pos:pos+2], 16) + 128) & 0xff
				except ValueError:
					print "[dmmBlindscan][updateConstellation] Q constellation data broken at pos", pos
					val = 0
				Q.append(val)
			for i in range(15):
				self["constellation"].fill(I[i],Q[i],1,1,0x25ffffff)
		self["constellation"].flush()
		if constellation_bitmap_list:
			self.tmr.start(3000, True)
		else:
			self.tmr.start(50, True)

	def keyOk(self):
		cur_sel = self["list"].current
		if cur_sel:
			self.updateConstellation(cur_sel[1])

	def keyCancel(self):
		self.tmr.stop()
		self.close(False)

class SatelliteTransponderSearchSupport:
	def satelliteTransponderSearchSessionClosed(self, *val):
		user_aborted_scan = False
		self.releaseFrontend()
		print "[dmmBlindscan][satelliteTransponderSearchSessionClosed] val", val
		if val and len(val):
			if val[0]:
				self.tlist = self.__tlist
			else:
				self.tlist = None
				user_aborted_scan = True
		self.satellite_search_session = None
		self.__tlist = None
		self.timer.stop()
		self.TransponderSearchFinished(user_aborted_scan)

	def updateStateSat(self):
		self.frontendStateChanged()

	def frontendStateChanged(self):
		if self.frontend is None:
			self.timer.start(5000, True)
			return
		x = {}
		self.frontend.getFrontendStatus(x)
		assert x, "getFrontendStatus failed!"
		if x["tuner_state"] in ("LOCKED", "FAILED", "LOSTLOCK"):
			state = self.satellite_search_session

			d = {}
			self.frontend.getTransponderData(d, False)
			d["tuner_type"] = 'DVB-S' # what is this doing? Nothing good by the look of it.
			r = ConvertToHumanReadable(d)

			if x["tuner_state"] == "LOCKED":
				freq = int(round(d["frequency"], -3)) # round to nearest 1000
				parm = eDVBFrontendParametersSatellite()
				parm.frequency = freq
				if d["symbol_rate"] < 0:
					print "[dmmBlindscan][frontendStateChanged] WARNING blind SR is < 0... skip"
					if not self.auto_scan:
						self.parm.frequency += self.parm.symbol_rate
				else:
					parm.symbol_rate = int(round(d["symbol_rate"], -3))
					parm.fec = d["fec_inner"]
					parm.inversion = eDVBFrontendParametersSatellite.Inversion_Unknown
					parm.polarisation = d["polarization"]
					parm.orbital_position = d["orbital_position"]
					parm.system = d["system"]
					parm.modulation = d["modulation"]
					if parm.system == eDVBFrontendParametersSatellite.System_DVB_S2:
						parm.rolloff = d["rolloff"]
						parm.pilot = d["pilot"]
					if hasattr(parm, "is_id"):
						parm.is_id = d["is_id"]
					if hasattr(parm, "pls_mode"):
						parm.pls_mode = d["pls_mode"]
					if hasattr(parm, "pls_code"):
						parm.pls_code = d["pls_code"]
					if hasattr(parm, "t2mi_plp_id"):
						parm.t2mi_plp_id = d["t2mi_plp_id"]
					if hasattr(parm, "t2mi_pid"):
						parm.t2mi_pid = d["t2mi_pid"]

					print "[dmmBlindscan][frontendStateChanged] About to run filters"
					parm_list = self.runFilters([parm], self.__tlist) # parm_list will contain a maximum of one transponder as the input is only one transponder
					if parm_list:
						parm = parm_list[0]
						self.__tlist.append(parm)

					fstr = "%s %s %s %s %s %s" % (
						str(parm.frequency / 1000),
						{eDVBFrontendParametersSatellite.Polarisation_Horizontal: "H", eDVBFrontendParametersSatellite.Polarisation_Vertical: "V", eDVBFrontendParametersSatellite.Polarisation_CircularLeft: "L", eDVBFrontendParametersSatellite.Polarisation_CircularRight: "R"}.get(parm.polarisation),
						str(parm.symbol_rate / 1000),
						r["fec_inner"],
						r["system"],
						r["modulation"])

					if not parm_list:
						print "[dmmBlindscan][frontendStateChanged] Transponder removed by filters, %s" % fstr

					if self.auto_scan:
						print "[dmmBlindscan][frontendStateChanged] LOCKED at", freq, {eDVBFrontendParametersSatellite.Polarisation_Horizontal: "H", eDVBFrontendParametersSatellite.Polarisation_Vertical: "V", eDVBFrontendParametersSatellite.Polarisation_CircularLeft: "L", eDVBFrontendParametersSatellite.Polarisation_CircularRight: "R"}.get(parm.polarisation)
					else:
						print "[dmmBlindscan][frontendStateChanged] LOCKED at", freq, "SEARCHED at", self.parm.frequency, "half bw", (135L * ((sr + 1000) / 1000) / 200), "half search range", (self.parm.symbol_rate / 2)
						self.parm.frequency = freq
						self.parm.frequency += (135L * ((sr + 999) / 1000) / 200)
						self.parm.frequency += self.parm.symbol_rate / 2

					if parm_list:
						bm = state.getConstellationBitmap(5)
						self.tp_found.append((fstr, bm))
						state.updateConstellation(bm)

					if len(self.tp_found):
						state["list"].updateList(self.tp_found)
					else:
						state["list"].setList(self.tp_found)
						state["list"].setIndex(0)
			else:
				if self.auto_scan: #when driver based auto scan is used we got a tuneFailed event when the scan has scanned the last frequency...
					self.parm = self.setNextRange()
				else:
					self.parm.frequency += self.parm.symbol_rate

			if self.auto_scan:
#				freq = d["frequency"]
#				freq = int(round(float(freq*2) / 1000)) * 1000
#				freq /= 2
				freq = int(round(d["frequency"], -3)) # round to nearest 1000
				mhz_complete, mhz_done = self.stats(freq)
				print "[dmmBlindscan][frontendStateChanged] CURRENT freq", freq, "%d/%d" % (mhz_done, mhz_complete)
				check_finished = self.parm is None
			else:
				print "[dmmBlindscan][frontendStateChanged] NEXT freq", self.parm.frequency
				mhz_complete, mhz_done = self.stats()
				check_finished = self.parm.frequency > self.range_list[self.current_range][1]
				if check_finished:
					self.parm = self.setNextRange()

			seconds_done = int(time() - self.start_time)

			if check_finished:
				if self.parm is None:
					tmpstr = _("%dMHz scanned") % mhz_complete
					tmpstr += ', '
					tmpstr += _("%d transponders found at %d:%02d min") % (len(self.tp_found),seconds_done / 60, seconds_done % 60)
					state["progress"].setText(tmpstr)
					state.setFinished()
					self.frontend = None
					self.raw_channel = None
					return

			if self.auto_scan:
				tmpstr = str((freq + 500) / 1000)
			else:
				tmpstr = str((self.parm.frequency + 500) / 1000)

			if self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Horizontal:
				tmpstr += "H"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Vertical:
				tmpstr += "V"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularLeft:
				tmpstr += "L"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularRight:
				tmpstr += "R"

			tmpstr += ', '
			tmpstr += "%d/%dMhz" % (mhz_done, mhz_complete)

			tmpstr += ", "
			tmpstr += _("%d transponder(s) found") % len(self.tp_found)

			tmpstr += ', '

			seconds_complete = (seconds_done * mhz_complete) / max(mhz_done, 1)
			tmpstr += _("%d:%02d/%d:%02dmin") % (seconds_done / 60, seconds_done % 60, seconds_complete / 60, seconds_complete % 60)

			state["progress"].setText(tmpstr)

			self.tuneNext()
		else:
			print "[dmmBlindscan]unhandled tuner state", x["tuner_state"]
		self.timer.start(1500, True)

	def tuneNext(self):
		if self.parm is not None:
			print "[dmmBlindscan][tuneNext] pos %d, freq %d, pol %d, sys %d" % (self.parm.orbital_position, self.parm.frequency, self.parm.polarisation, self.parm.system)
			tparm = eDVBFrontendParameters()
			tparm.setDVBS(self.parm, False)
			self.frontend.tune(tparm, True)

	def setNextRange(self):
		if self.current_range is None:
			self.current_range = 0
		else:
			self.current_range += 1
		print "[dmmBlindscan][setNextRange] self.current_range", self.current_range
		if len(self.range_list) > self.current_range:
			bs_range = self.range_list[self.current_range]
			print "[dmmBlindscan][setNextRange] Sat Blindscan current range", bs_range
			parm = eDVBFrontendParametersSatellite()
			parm.frequency = bs_range[0]
			if self.nim.isCompatible("DVB-S2"):
				steps = {5: 2000, 4: 4000, 3: 6000, 2: 8000, 1: 10000}[self.dmmBlindscan.accuracy.value]
				parm.system = self.dmmBlindscan.system.value
				parm.pilot = eDVBFrontendParametersSatellite.Pilot_Unknown
				parm.rolloff = eDVBFrontendParametersSatellite.RollOff_alpha_0_35
				parm.pls_mode = eDVBFrontendParametersSatellite.PLS_Gold
				parm.is_id = eDVBFrontendParametersSatellite.No_Stream_Id_Filter
				parm.pls_code = eDVBFrontendParametersSatellite.PLS_Default_Gold_Code
				if hasattr(parm, "t2mi_plp_id"):
					parm.t2mi_plp_id = eDVBFrontendParametersSatellite.No_T2MI_PLP_Id
				if hasattr(parm, "t2mi_pid"):
					parm.t2mi_pid = eDVBFrontendParametersSatellite.T2MI_Default_Pid
			else:
				steps = 4000
				parm.system = eDVBFrontendParametersSatellite.System_DVB_S
			if self.auto_scan:
				parm.symbol_rate = (bs_range[1] - bs_range[0]) / 1000
			else:
				parm.symbol_rate = steps
			parm.fec = eDVBFrontendParametersSatellite.FEC_Auto
			parm.inversion = eDVBFrontendParametersSatellite.Inversion_Unknown
			parm.polarisation = bs_range[2]
			parm.orbital_position = self.orb_pos
			parm.modulation = eDVBFrontendParametersSatellite.Modulation_QPSK
			return parm
		return None

	def stats(self, freq=None):
		if freq is None:
			freq = self.parm.frequency
		mhz_complete = 0
		mhz_done = 0
		cnt = 0
		for range in self.range_list:
			mhz = (range[1] - range[0]) / 1000
			mhz_complete += mhz
			if cnt == self.current_range:
				mhz_done += (freq - range[0]) / 1000
			elif cnt < self.current_range:
				mhz_done += mhz
			cnt += 1
		return mhz_complete, mhz_done

	def openFrontend(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.raw_channel = res_mgr.allocateRawChannel(self.feid)
			if self.raw_channel:
				self.frontend = self.raw_channel.getFrontend()
				if self.frontend:
					return True
				else:
					print "[dmmBlindscan][openFrontend] getFrontend failed"
			else:
				print "[dmmBlindscan][openFrontend] getRawChannel failed"
		else:
			print "[dmmBlindscan][openFrontend] getResourceManager instance failed"
		return False

	def prepareFrontend(self):
		self.releaseFrontend()
		if not self.openFrontend():
			self.session.nav.stopService()
			if not self.openFrontend():
				if self.session.pipshown:
					if hasattr(self.session, 'infobar'):
						try:
							slist = self.session.infobar.servicelist
							if slist and slist.dopipzap:
								slist.togglePipzap()
						except:
							pass
					self.session.pipshown = False
					if hasattr(self.session, 'pip'):
						del self.session.pip
				self.openFrontend()
		return self.frontend and True or False

	def releaseFrontend(self):
		if hasattr(self, 'frontend'):
			del self.frontend
		if hasattr(self, 'raw_channel'):
			del self.raw_channel
		self.frontend = None
		self.raw_channel = None

	def startSatelliteTransponderSearch(self):
		self.releaseFrontend()
		self.nim = nimmanager.nim_slots[self.feid]
		tunername = nimmanager.getNimName(self.feid)
		self.__tlist = []
		self.tp_found = []
		self.current_range = None
		self.range_list = [] # contains tuples, (start, stop, polarisation), max length 4, i.e. 4 sub-bands
		tuner_no = -1
		self.auto_scan = False

		print "[dmmBlindscan][startSatelliteTransponderSearch] tunername", tunername
		if nimmanager.nim_slots[self.feid].supportsBlindScan() or tunername in ("BCM4505", "BCM4506 (internal)", "BCM4506", "Alps BSBE1 C01A/D01A.", "Si2166B", "Si2169C"):
			self.auto_scan = nimmanager.nim_slots[self.feid].supportsBlindScan() or tunername in ("Si2166B", "Si2169C")
			if not self.prepareFrontend():
				print "[dmmBlindscan][startSatelliteTransponderSearch] couldn't allocate tuner %d for blindscan!" % self.feid
				text = _("Sorry, this tuner is in use.")
				if self.session.nav.getRecordings():
					text += _("\nA recording is in progress.")
				self.session.open(MessageBox, text, MessageBox.TYPE_ERROR)
				return

			band_cutoff_frequency = 11700001

			s1 = self.dmmBlindscan.freq_start.value * 1000
			s2 = self.dmmBlindscan.freq_stop.value * 1000

			start = min(s1,s2)
			stop = max(s1,s2)

			if self.auto_scan: # hack for driver based blindscan... extend search range +/- 50Mhz
				freq_limits = list(map(lambda x: x * 1000, self.freq_limits))
				start -= 50000
				stop += 50000
				if start < freq_limits[0]:
					start = freq_limits[0]
				if stop > freq_limits[1]:
					stop = freq_limits[1]

			pols = {eDVBFrontendParametersSatellite.Polarisation_Horizontal: "horizontal", eDVBFrontendParametersSatellite.Polarisation_Vertical: "vertical"}
			for pol in (eDVBFrontendParametersSatellite.Polarisation_Vertical, eDVBFrontendParametersSatellite.Polarisation_Horizontal):
				if pols[pol] in self.dmmBlindscan.polarization.value:
					if self.auto_scan:
						pol or self.range_list.append((start, min(stop, start + 5000), pol)) # hack alert, this is crap and should not be here, but scan misses a lot of services without it.
						if start < band_cutoff_frequency:
							self.range_list.append((start, min(stop, band_cutoff_frequency - 1), pol))
						if stop > band_cutoff_frequency:
							self.range_list.append((max(band_cutoff_frequency, start), stop, pol))
					else:
						self.range_list.append((start, stop, pol))

#			if self.dmmBlindscan.multiple_scan.value > 1:
#				self.range_list = [self.range_list[i//self.dmmBlindscan.multiple_scan.value] for i in range(len(self.range_list)*self.dmmBlindscan.multiple_scan.value)]

			print "[dmmBlindscan][startSatelliteTransponderSearch] self.range_list", self.range_list

			self.parm = self.setNextRange()
			if self.parm is not None:
				tparm = eDVBFrontendParameters()
				tparm.setDVBS(self.parm, False)
				self.frontend.tune(tparm, True)
				self.start_time = time()
				tmpstr = _("Searching for active satellite transponders...")
			else:
				tmpstr = _("Nothing to scan! Press Exit!")
			x = {}
			data = self.frontend.getFrontendData(x)
			tuner_no = x["tuner_number"]
		else:
			if "Sundtek DVB-S/S2" in tunername and "V" in tunername:
				tmpstr = _("Use Sundtek full hardware blind scan!")
			else:
				tmpstr = _("Hardware blind scan is not supported by this tuner (%s)!") % tunername
			self.session.open(MessageBox, tmpstr, MessageBox.TYPE_ERROR)
			return
		self.satellite_search_session = self.session.openWithCallback(self.satelliteTransponderSearchSessionClosed, DmmBlindscanState, tuner_no, tmpstr)
		#if self.auto_scan:
		self.timer = eTimer()
		self.timer.callback.append(self.updateStateSat)
		self.timer.stop()
		self.updateStateSat()

class DmmBlindscan(ConfigListScreen, Screen, SatelliteTransponderSearchSupport, TransponderFiltering):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["DmmBlindscanScreen", "Blindscan", "Setup"]
		Screen.setTitle(self, _("Blind scan for DVB-S2 tuners"))
		self.updateSatList()
		self.service = session.nav.getCurrentService()
		self.feinfo = None
		frontendData = None

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

		if self.service is not None:
			self.feinfo = self.service.frontendInfo()
			frontendData = self.feinfo and self.feinfo.getAll(True)
		self.createConfig(frontendData)
		del self.feinfo
		del self.service
		try:
			self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		except:
			self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceReference()

		self["actions"] = NumberActionMap(["SetupActions"],
		{
			"cancel": self.keyCancel,
		}, -2)

		self["actions2"] = NumberActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"save": self.keyGo,
		}, -2)
		self["actions2"].setEnabled(False)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText("")
		self["description"] = Label("")

		self.list = []
		ConfigListScreen.__init__(self, self.list)
		if self.scan_nims.value == "": # no usable nims were found (handled in createConfig())
			self["introduction"] = Label(_("Please setup your tuner configuration."))
		else:
			self.createSetup()
			self["introduction"] = Label(_("Press OK to start the scan."))

		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()
		
	def selectionChanged(self):
		self["description"].setText(self["config"].getCurrent() and len(self["config"].getCurrent()) > 2 and self["config"].getCurrent()[2] or "")

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent() and self["config"].getCurrent()[0] or ""

	def getCurrentValue(self):
		return self["config"].getCurrent() and str(self["config"].getCurrent()[1].getText()) or ""

	def updateSatList(self):
		self.satList = []
		for slot in nimmanager.nim_slots:
			if slot.isCompatible("DVB-S"):
				self.satList.append(nimmanager.getSatListForNim(slot.slot))
			else:
				self.satList.append(None)

	def createSetup(self):
		self.list = []
		self.multiscanlist = []
		index_to_scan = int(self.scan_nims.value)
		print "[dmmBlindscan][createSetup] ID: ", index_to_scan

		self.tunerEntry = getConfigListEntry(_("Tuner"), self.scan_nims, _("Select a tuner that is configured for the satellite you wish to search"))
		self.list.append(self.tunerEntry)

		nim = nimmanager.nim_slots[index_to_scan]

		tunername = nimmanager.getNimName(index_to_scan)

		self.updateSatList()
#			selected_sat_pos = self.scan_satselection[index_to_scan].value
		self.satelliteEntry = getConfigListEntry(_("Satellite"), self.scan_satselection[index_to_scan], _("Select the satellite you wish to search"))
		self.list.append(self.satelliteEntry)
		self.searchtypeEntry = getConfigListEntry(_("Search type"), self.search_type, _('"scan for channels" searches for channels and saves them to your receiver; "Save to XML" does a transponder search and saves the results in satellites.xml format and stores it in /tmp'))
		self.list.append(self.searchtypeEntry)
		self.list.append(getConfigListEntry(_("Start frequency"), self.dmmBlindscan.freq_start, _("Frequency values must be between %d MHz and %d MHz") % (self.freq_limits[0], self.freq_limits[1] - 1)))
		self.list.append(getConfigListEntry(_("Stop frequency"), self.dmmBlindscan.freq_stop, _("Frequency values must be between %d MHz and %d MHz") % (self.freq_limits[0] + 1, self.freq_limits[1])))
		self.list.append(getConfigListEntry(_("Polarization"), self.dmmBlindscan.polarization, _("Polarisation, select horizontal, vertical or both.")))
		self.list.append(getConfigListEntry(_("Start symbol rate"), self.dmmBlindscan.sr_start, _("Symbol rate values are in megasymbols; enter a value between %d and %d") % (self.sr_limits[0], self.sr_limits[1] - 1)))
		self.list.append(getConfigListEntry(_("Stop symbol rate"), self.dmmBlindscan.sr_stop, _("Symbol rate values are in megasymbols; enter a value between %d and %d") % (self.sr_limits[0] + 1, self.sr_limits[1])))
		if nim.isCompatible("DVB-S2") and not (nimmanager.nim_slots[index_to_scan].supportsBlindScan() or tunername in ("Si2166B", "Si2169C")):
			self.list.append(getConfigListEntry(_("Accuracy (higher is better)"), self.dmmBlindscan.accuracy, _("Select between 1 and 5. Higher numbers give more accurat search results.")))
		if self.search_type.value == "services":
			self.list.append(getConfigListEntry(_("Clear before scan"), self.dmmBlindscan.scan_clearallservices, _('If you select "yes" all channels on the satellite being searched will be deleted before starting the current search, yes (keep feeds) means the same but hold all feed services/transponders.')))
			self.list.append(getConfigListEntry(_("Only free scan"), self.dmmBlindscan.scan_onlyfree, _('If you select "yes" the scan will only save channels that are not encrypted; "no" will find encrypted and non-encrypted channels.')))
			self.onlyUnknownTpsEntry = getConfigListEntry(_("Only scan unknown transponders"), self.dmmBlindscan.dont_scan_known_tps,_('If you select "yes" the scan will only search transponders not listed in satellites.xml'))
			self.list.append(self.onlyUnknownTpsEntry)
			if not self.dmmBlindscan.dont_scan_known_tps.value:
				self.list.append(getConfigListEntry(_("Disable sync with known transponders"), self.dmmBlindscan.disable_sync_with_known_tps,_('CAUTION: If you select "yes" the scan will not sync with transponders listed in satellites.xml. Default is "no". Only change this if you understand why you are doing it.')))
			self.list.append(getConfigListEntry(_("Disable remove duplicates"), self.dmmBlindscan.disable_remove_duplicate_tps,_('CAUTION: If you select "yes" the scan will not remove "duplicated" transponders from the list. Default is "no". Only change this if you understand why you are doing it.')))
			self.list.append(getConfigListEntry(_("Filter out adjacent satellites"), self.dmmBlindscan.filter_off_adjacent_satellites,_('When a neighbouring satellite is very strong this avoids searching transponders known to be coming from the neighbouring satellite.')))
#		self.list.append(getConfigListEntry(_("Scan multiple times"), self.dmmBlindscan.multiple_scan,_('Scan all frequencies multiple times to capture transponders missed on the first attempt.')))

		self["config"].list = self.list
		self["config"].l.setList(self.list)
		
		self["key_green"].setText(_("Scan"))
		self["actions2"].setEnabled(True)

	def Satexists(self, tlist, pos):
		for x in tlist:
			if x == pos:
				return 1
		return 0

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur in (self.tunerEntry, self.satelliteEntry, self.searchtypeEntry, self.onlyUnknownTpsEntry):
			self.createSetup()

	def createConfig(self, frontendData):
		self.tunerEntry = None
		self.satelliteEntry = None
		self.searchtypeEntry = None
		self.onlyUnknownTpsEntry = None

		defaultSat = {
			"orbpos": 192,
			"system": eDVBFrontendParametersSatellite.System_DVB_S,
			"frequency": 11836,
			"inversion": eDVBFrontendParametersSatellite.Inversion_Unknown,
			"symbolrate": 27500,
			"polarization": eDVBFrontendParametersSatellite.Polarisation_Horizontal,
			"fec": eDVBFrontendParametersSatellite.FEC_Auto,
			"fec_s2": eDVBFrontendParametersSatellite.FEC_9_10,
			"modulation": eDVBFrontendParametersSatellite.Modulation_QPSK}

		if frontendData is not None:
			ttype = frontendData.get("tuner_type", "UNKNOWN")
			if ttype == "DVB-S":
				defaultSat["system"] = frontendData.get("system", eDVBFrontendParametersSatellite.System_DVB_S)
				defaultSat["frequency"] = frontendData.get("frequency", 0) / 1000
				defaultSat["inversion"] = frontendData.get("inversion", eDVBFrontendParametersSatellite.Inversion_Unknown)
				defaultSat["symbolrate"] = frontendData.get("symbol_rate", 0) / 1000
				defaultSat["polarization"] = frontendData.get("polarization", eDVBFrontendParametersSatellite.Polarisation_Horizontal)
				defaultSat["modulation"] = frontendData.get("modulation", eDVBFrontendParametersSatellite.Modulation_QPSK)
				if defaultSat["system"] == eDVBFrontendParametersSatellite.System_DVB_S2:
					defaultSat["fec_s2"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
					defaultSat["rolloff"] = frontendData.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35)
					defaultSat["pilot"] = frontendData.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown)
				else:
					defaultSat["fec"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
				defaultSat["orbpos"] = frontendData.get("orbital_position", 0)

		self.dmmBlindscan = ConfigSubsection()
		self.dmmBlindscan.scan_clearallservices = ConfigSelection(default="no", choices=[("no", _("no")), ("yes", _("yes")), ("yes_hold_feeds", _("yes (keep feeds)"))])
		self.dmmBlindscan.scan_onlyfree = ConfigYesNo(default=False)

		self.freq_limits = (10700, 12750)
		self.dmmBlindscan.freq_start = ConfigInteger(default=self.freq_limits[0], limits=(self.freq_limits[0], self.freq_limits[1] - 1))
		self.dmmBlindscan.freq_stop = ConfigInteger(default=self.freq_limits[1], limits=(self.freq_limits[0] + 1, self.freq_limits[1]))

		self.sr_limits = (1, 60)
		sr_defaults = (2, 45)
		self.dmmBlindscan.sr_start = ConfigInteger(default=sr_defaults[0], limits=(self.sr_limits[0], self.sr_limits[1] - 1))
		self.dmmBlindscan.sr_stop = ConfigInteger(default=sr_defaults[1], limits=(self.sr_limits[0] + 1, self.sr_limits[1]))

		self.dmmBlindscan.dont_scan_known_tps = ConfigYesNo(default=False)
		self.dmmBlindscan.disable_sync_with_known_tps = ConfigYesNo(default=False)
		self.dmmBlindscan.disable_remove_duplicate_tps = ConfigYesNo(default=False)
		self.dmmBlindscan.filter_off_adjacent_satellites = ConfigSelection(default="1", choices=[
			("0", _("no")),
			("1", _("up to 1 degree")),
			("2", _("up to 2 degrees")),
			("3", _("up to 3 degrees"))])		

		nim_list = []
		for n in nimmanager.nim_slots:
			if hasattr(n, 'isFBCLink') and n.isFBCLink():
				continue
			if n.isCompatible("DVB-S"):
				if not self.legacy:
					nimconfig = n.config.dvbs
				else:
					nimconfig = n.config
				config_mode = nimconfig.configMode.value
				if config_mode == "nothing":
					continue
			if n.isCompatible("DVB-S") and len(nimmanager.getSatListForNim(n.slot)) < 1:
				if config_mode in ("advanced", "simple"):
					if not self.legacy:
						config.Nims[n.slot].dvbs.configMode.value = "nothing"
						config.Nims[n.slot].dvbs.configMode.save()
					else:
						config.Nims[n.slot].configMode.value = "nothing"
						config.Nims[n.slot].configMode.save()
					continue
			if n.isCompatible("DVB-S") and config_mode in ("loopthrough", "satposdepends"):
				root_id = nimmanager.sec.getRoot(n.slot_id, int(nimconfig.connectedTo.value))
				if n.type == nimmanager.nim_slots[root_id].type: # check if connected from a DVB-S to DVB-S2 Nim or vice versa
					continue
			if n.isCompatible("DVB-S"):
				nim_list.append((str(n.slot), n.friendly_full_description))
		self.scan_nims = ConfigSelection(choices=nim_list)

		# this is not currently a user option
		self.dmmBlindscan.system = ConfigSelection(default=eDVBFrontendParametersSatellite.System_DVB_S2, 
			choices=[(eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S + DVB-S2")),
				(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S only"))])

		self.dmmBlindscan.accuracy = ConfigSelection(default=2, choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")])
#		self.dmmBlindscan.multiple_scan = ConfigSelection(default = 1, choices = [(1, "only scan once"), (2, "scan twice"), (3, "scan three times")])
		self.search_type = ConfigSelection(default="services", choices=[
			("services", _("scan for channels")),
			("xml", _("save to XML file"))])

		self.dmmBlindscan.polarization = ConfigSelection(default="vertical and horizontal", choices=[
			("vertical and horizontal", _("vertical and horizontal")),
			("vertical", _("vertical")),
			("horizontal", _("horizontal"))])
		self.nim_sat_frequency_range = []
		self.nim_sat_band_cutoff_frequency = []
		self.scan_satselection = []
		for slot in nimmanager.nim_slots:
			slot_id = slot.slot
			if slot.isCompatible("DVB-S"):
				satlist_for_slot = self.satList[slot_id]
				self.scan_satselection.append(getConfigSatlist(defaultSat["orbpos"], satlist_for_slot))
				sat_freq_range = {(10700000, 12750000)}
				sat_band_cutoff = {11700000}
				for sat in satlist_for_slot:
					orbpos = sat[0]
				self.nim_sat_frequency_range.append(sat_freq_range)
				self.nim_sat_band_cutoff_frequency.append(sat_band_cutoff)
			else:
				self.nim_sat_frequency_range.append(None)
				self.nim_sat_band_cutoff_frequency.append(None)
				self.scan_satselection.append(None)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def keyGo(self):
		self.feid = int(self.scan_nims.value)
		
		self.checkStartStopValues(self.dmmBlindscan.freq_start, self.dmmBlindscan.freq_stop)
		self.checkStartStopValues(self.dmmBlindscan.sr_start, self.dmmBlindscan.sr_stop)

		self.tlist = []
		sat = self.satList[self.feid][self.scan_satselection[self.feid].index]
		self.orb_pos = sat[0]
		self.sat_name = sat[1]
		self.known_transponders = self.getKnownTransponders(self.orb_pos) # put this here so it runs just once per search
		self.startSatelliteTransponderSearch()

	def checkStartStopValues(self, start, stop):
		# swap start and stop values if entered the wrong way round
		if start.value > stop.value:
			start.value, stop.value = (stop.value, start.value)
	
	def TransponderSearchFinished(self, user_aborted_scan=False):
		if self.tlist is None:
			self.tlist = []
		if self.tlist:
			self.tlist = sorted(self.tlist, key=lambda tp: (tp.frequency, tp.polarisation))
			xml_location = self.createSatellitesXMLfile()
			if self.search_type.value == "services":
				self.startScan()
			else:
				msg = _("Search completed. %d transponders found.\n\nDetails saved in:\n%s") % (len(self.tlist), xml_location)
				self.session.openWithCallback(self.callbackNone, MessageBox, msg, MessageBox.TYPE_INFO, timeout=300)
		else:
			if user_aborted_scan:
				msg = _("The blindscan run was cancelled by the user.")
			else:
				msg = _("No transponders were found for those search parameters!")
			self.session.openWithCallback(self.callbackNone, MessageBox, msg, MessageBox.TYPE_INFO, timeout=60)

	def callbackNone(self, *retval):
		None

	def runFilters(self, tplist, orig_tplist=None):
		# tplist should only contain one tp

		# Sync with or remove transponders that exist in satellites.xml
		if self.dmmBlindscan.dont_scan_known_tps.value:
			tplist = self.removeKnownTransponders(tplist, self.known_transponders)
		elif not self.dmmBlindscan.disable_sync_with_known_tps.value:
			tplist = self.syncWithKnownTransponders(tplist, self.known_transponders)

		# Remove any duplicate transponders. This checks tps in tplist do not exist in self.__tlist. If they exist they will be removed from tplist.
		if orig_tplist and not self.dmmBlindscan.disable_remove_duplicate_tps.value:
			for i in reversed(range(len(tplist))): # i is the current index in tplist and iterated in reverse to allow deleting from the end of tplist without losing index corelation
				if len(orig_tplist) == len(self.removeDuplicateTransponders(orig_tplist + [tplist[i]])):
					del tplist[i]

		# Filter off transponders on neighbouring satellites
		if int(self.dmmBlindscan.filter_off_adjacent_satellites.value):
			tplist = self.filterOffAdjacentSatellites(tplist, self.orb_pos, int(self.dmmBlindscan.filter_off_adjacent_satellites.value))

		tplist = self.checkFrequencyAndSymbol(tplist)
		
		return tplist

	def checkFrequencyAndSymbol(self, tplist):
		# this checks frequency and symbol rate are within the limits set b the user
		new_tplist = []
		lower_freq = self.dmmBlindscan.freq_start.value * 1000
		upper_freq = self.dmmBlindscan.freq_stop.value * 1000
		lower_symbol = self.dmmBlindscan.sr_start.value * 1000000
		upper_symbol = self.dmmBlindscan.sr_stop.value * 1000000
		for tp in tplist:
			if lower_freq <= tp.frequency <= upper_freq and lower_symbol <= tp.symbol_rate <= upper_symbol:
				new_tplist.append(tp)
		return new_tplist
		

	def startScan(self):
		networkid = 0
		flags = 0
		tmp = self.dmmBlindscan.scan_clearallservices.value
		if tmp == "no":
			flags |= eComponentScan.scanDontRemoveUnscanned
		elif tmp == "yes":
			flags |= eComponentScan.scanRemoveServices
		elif tmp == "yes_hold_feeds":
			flags |= eComponentScan.scanRemoveServices
			flags |= eComponentScan.scanDontRemoveFeeds
		if self.dmmBlindscan.scan_onlyfree.value:
			flags |= eComponentScan.scanOnlyFree
			
		self.session.openWithCallback(self.startScanCallback, ServiceScan, [{"transponders": self.tlist, "feid": self.feid, "flags": flags, "networkid": networkid}])

	def keyCancel(self):
		self.releaseFrontend()
		self.session.nav.playService(self.session.postScanService)
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)

	def startScanCallback(self, answer=True):
		if answer:
			self.releaseFrontend()
			self.session.nav.playService(self.session.postScanService)
			self.close(True)
			

	def createSatellitesXMLfile(self):
		pos = self.orb_pos
		if pos > 1800:
			pos -= 3600
		if pos < 0:
			pos_name = '%dW' % (abs(int(pos)) / 10)
		else:
			pos_name = '%dE' % (abs(int(pos)) / 10)
		location = '%s/dmm_blindscan_%s_%s.xml' % (XML_BLINDSCAN_DIR, pos_name, strftime("%d-%m-%Y_%H-%M-%S"))
		tuner = nimmanager.nim_slots[self.feid].friendly_full_description
		xml = ['<?xml version="1.0" encoding="iso-8859-1"?>\n\n']
		xml.append('<!--\n')
		xml.append('	File created on %s\n' % (strftime("%A, %d of %B %Y, %H:%M:%S")))
		try:
			xml.append('	using %s receiver running Enigma2 image, version %s,\n' % (boxtype, about.getEnigmaVersionString()))
			xml.append('	image %s, with the Blind scan plugin\n\n' % (about.getImageTypeString()))
		except:
			xml.append('	using %s receiver running Enigma2 image (%s), with the blind scan plugin\n\n' % (boxtype, tuner))
		xml.append('-->\n\n')
		xml.append('<satellites>\n')
		xml.append('	<sat name="%s" flags="0" position="%s">\n' % (self.sat_name.replace('&', '&amp;'), self.orb_pos))
		for tp in self.tlist:
			xml.append('		<transponder frequency="%d" symbol_rate="%d" polarization="%d" fec_inner="%d" system="%d" modulation="%d"/>\n' % (tp.frequency, tp.symbol_rate, tp.polarisation, tp.fec, tp.system, tp.modulation))
		xml.append('	</sat>\n')
		xml.append('</satellites>')
		f = open(location, "w")
		f.writelines(xml)
		f.close()
		return location

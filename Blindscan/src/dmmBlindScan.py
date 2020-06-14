from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
# for localized messages
from . import _
from Components.ActionMap import NumberActionMap, ActionMap
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigInteger, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.NimManager import nimmanager, getConfigSatlist
from Components.Sources.CanvasSource import CanvasSource
from Components.Sources.List import List
from enigma import eDVBFrontendParameters, eDVBFrontendParametersSatellite, eComponentScan, eTimer, eDVBResourceManager
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.ServiceScan import ServiceScan
from time import time, strftime
from Components.About import about
from Tools.Directories import fileExists
from Tools.Transponder import ConvertToHumanReadable

XML_BLINDSCAN_DIR = "/tmp"

try:
	boxtype = open("/proc/stb/info/model").read().strip()
except:
	boxtype = ""

class TransponderSearchSupport:
	def tryGetRawFrontend(self, feid, ret_boolean=True, do_close=True):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			raw_channel = res_mgr.allocateRawChannel(self.feid)
			if raw_channel:
				frontend = raw_channel.getFrontend()
				if frontend:
					if do_close:
						frontend.closeFrontend() # immediate close... 
					if ret_boolean:
						del raw_channel
						del frontend
						return True
					return raw_channel, frontend
		if ret_boolean:
			return False
		return (False, False)

class SatBlindscanState(Screen):
	skin="""
	<screen position="center,center" size="820,520" title="Satellite Blindscan">
		<widget name="text" position="10,10" size="800,25" font="Regular;20" />
		<widget name="progress" position="10,40" size="800,25" font="Regular;20" />
		<eLabel	position="10,70" size="800,1" backgroundColor="grey"/>
		<widget source="list" render="Listbox" position="10,82" size="524,425" scrollbarMode="showAlways" >
			<convert type="TemplatedMultiContent">
				{"template": [ MultiContentEntryText(pos = (5, 2), size = (514, 22), flags = RT_HALIGN_LEFT, text = 0) ],
				 "fonts": [gFont("Regular", 19)],
				 "itemHeight": 25
				}
			</convert>
		</widget>
		<eLabel	position="544,70" size="1,440" backgroundColor="grey"/>
		<widget name="post_action" position="554,90" size="256,140" font="Regular;19" halign="center"/>
		<widget source="constellation" render="Canvas" position="554,254" size="256,256" correct_aspect="width" />
	</screen>
	"""

	def __init__(self, session, fe_num, text):
		Screen.__init__(self, session)
		self.setup_title = _("Blind scan state")
		Screen.setTitle(self, _(self.setup_title))
		self.skinName = ["SatBlindscanState2"]
		self["list"]=List()
		self["text"]=Label()
		self["text"].setText(text)
		self["post_action"]=Label()
		self["progress"]=Label()
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"green": self.keyGreen,
		}, -2)
		self.fe_num = fe_num
		self["constellation"] = CanvasSource()
		self.onLayoutFinish.append(self.updateConstellation)
		self.tmr = eTimer()
		self.tmr.callback.append(self.updateConstellation)
		self.constellation_supported = None
		if fe_num != -1:
			self.post_action=1
			self.finished=0
			self.keyGreen()
		else:
			self.post_action=-1

	def keyGreen(self):
		if self.finished:
			self.close(True)
		elif self.post_action != -1:
			self.post_action ^= 1
			if self.post_action:
				self["post_action"].setText(_("MANUALLY start service searching, press green to change."))
			else:
				self["post_action"].setText(_("AUTOMATICALLY start service searching, press green to change."))

	def setFinished(self):
		if self.post_action:
			self.finished=1
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
				self["constellation"].fill(0, 0, 256, 256, 0x25101010)
				self["constellation"].flush()

		if self.constellation_supported:
			while cnt > 0:
				f = open(path, "r")
				ret.append(f.readline())
				cnt -= 1
				f.close()
		return ret

	def updateConstellation(self, constellation_bitmap_list=None):
		if self.constellation_supported or self.constellation_supported is None:
			pass
		else:
			return
		self["constellation"].fill(0, 0, 256, 256, 0x25101010)
		if constellation_bitmap_list:
			bitmap_list = constellation_bitmap_list
		else:
			bitmap_list = self.getConstellationBitmap()
		for bitmap in bitmap_list:
			Q = []
			I = []
			for pos in range(0, 30, 2):
				try:
					val = int(bitmap[pos:pos+2], 16)
					val = 128 + (val - 256 if val > 127 else val)
					#val = (int(bitmap[pos:pos+2], 16) + 128) & 0xff
				except ValueError:
					print("I constellation data broken at pos", pos)
					val = 0
				I.append(val)
			for pos in range(30, 60, 2):
				try:
					val = int(bitmap[pos:pos+2], 16)
					val = 128 + (val - 256 if val > 127 else val)
					#val = (int(bitmap[pos:pos+2], 16) + 128) & 0xff
				except ValueError:
					print("Q constellation data broken at pos", pos)
					val = 0
				Q.append(val)
			for i in range(15):
				self["constellation"].fill(I[i], Q[i], 1, 1, 0x25ffffff)
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
		close_user = False
		if self.frontend:
			self.frontend = None
			self.channel = None
		print("satelliteTransponderSearchSessionClosed, val", val)
		if val and len(val):
			if val[0]:
				self.setTransponderSearchResult(self.__tlist)
			else:
				self.setTransponderSearchResult(None)
				close_user = True
		self.satellite_search_session = None
		self.__tlist = None
		self.timer.stop()
		self.TransponderSearchFinished(close_user)

	def updateStateSat(self):
		self.frontendStateChanged()

	def frontendStateChanged(self):
		if self.frontend is None:
			self.timer.start(5000, True)
			return
		x = { }
		self.frontend.getFrontendStatus(x)
		assert x, "getFrontendStatus failed!"
		if x["tuner_state"] in ("LOCKED", "FAILED", "LOSTLOCK"):
			state = self.satellite_search_session

			d = { }
			self.frontend.getTransponderData(d, False)
			d["tuner_type"] = 'DVB-S'
			r = ConvertToHumanReadable(d)

			if x["tuner_state"] == "LOCKED":
				freq = d["frequency"]
				parm = eDVBFrontendParametersSatellite()
				parm.frequency = int(round(float(freq*2) / 1000)) * 1000
				parm.frequency //= 2
				fstr = str(parm.frequency)
				if self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Horizontal:
					fstr += "H KHz SR"
				elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Vertical:
					fstr += "V KHz SR"
				elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularLeft:
					fstr += "L KHz SR"
				elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularRight:
					fstr += "R KHz SR"
				sr = d["symbol_rate"]
				if sr < 0:
					print("WARNING blind SR is < 0... skip")
					if not self.auto_scan:
						self.parm.frequency += self.parm.symbol_rate
				else:
					sr_rounded = round(float(sr*2) / 1000) * 1000
					sr_rounded /= 2
					parm.symbol_rate = int(sr_rounded)
					fstr += str(parm.symbol_rate/1000)
					parm.fec = d["fec_inner"]
					fstr += " "
					fstr += r["fec_inner"]
					parm.inversion = eDVBFrontendParametersSatellite.Inversion_Unknown
					parm.polarisation = d["polarization"]
					parm.orbital_position = d["orbital_position"]
					parm.system = d["system"]
					fstr += " "
					fstr += r["system"]
					parm.modulation = d["modulation"]
					fstr += " "
					fstr += r["modulation"]

					if parm.system == eDVBFrontendParametersSatellite.System_DVB_S2:
						parm.rolloff = d["rolloff"]
						parm.pilot = d["pilot"]
						parm.is_id = d["is_id"]
						parm.pls_mode = d["pls_mode"]
					self.__tlist.append(parm)
					if self.auto_scan:
						print("LOCKED at", freq)
					else:
						print("LOCKED at", freq, "SEARCHED at", self.parm.frequency, "half bw", (135*((sr+1000)/1000)/200), "half search range", (self.parm.symbol_rate/2))
						self.parm.frequency = freq
						self.parm.frequency += (135*((sr+999)/1000)/200)
						self.parm.frequency += self.parm.symbol_rate/2

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
				freq = d["frequency"]
				freq = int(round(float(freq*2) / 1000)) * 1000
				freq /= 2
				mhz_complete, mhz_done = self.stats(freq)
				print("CURRENT freq", freq, "%d/%d" %(mhz_done, mhz_complete))
				check_finished = self.parm is None
			else:
				print("NEXT freq", self.parm.frequency)
				mhz_complete, mhz_done = self.stats()
				check_finished = self.parm.frequency > self.range_list[self.current_range][1]
				if check_finished:
					self.parm = self.setNextRange()

			seconds_done = int(time() - self.start_time)

			if check_finished:
				if self.parm is None:
					tmpstr = _("%dMHz scanned") % mhz_complete
					tmpstr += ', '
					tmpstr += _("%d transponders found at %d:%02d min") %(len(self.tp_found), seconds_done / 60, seconds_done % 60)
					state["progress"].setText(tmpstr)
					state.setFinished()
					self.frontend = None
					self.channel = None
					return

			if self.auto_scan:
				tmpstr = str((freq+500)/1000)
			else:
				tmpstr = str((self.parm.frequency+500)/1000)

			if self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Horizontal:
				tmpstr += "H"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Vertical:
				tmpstr += "V"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularLeft:
				tmpstr += "L"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularRight:
				tmpstr += "R"

			tmpstr += ', '
			tmpstr += "%d/%dMhz" %(mhz_done, mhz_complete)

			tmpstr += ", "
			tmpstr += _("%d transponder(s) found") %len(self.tp_found)

			tmpstr += ', '

			seconds_complete = (seconds_done * mhz_complete) / max(mhz_done, 1)
			tmpstr += _("%d:%02d/%d:%02dmin") %(seconds_done / 60, seconds_done % 60, seconds_complete / 60, seconds_complete % 60)

			state["progress"].setText(tmpstr)

			self.tuneNext()
		else:
			print("unhandled tuner state", x["tuner_state"])
		self.timer.start(1500, True)

	def tuneNext(self):
		if self.parm is not None:
			tparm = eDVBFrontendParameters()
			tparm.setDVBS(self.parm, False)
			self.frontend.tune(tparm, True)

	def setNextRange(self):
		if self.current_range is None:
			self.current_range = 0
		else:
			self.current_range += 1
		if len(self.range_list) > self.current_range:
			bs_range = self.range_list[self.current_range]
			print("Sat Blindscan current range", bs_range)
			parm = eDVBFrontendParametersSatellite()
			parm.frequency = bs_range[0]
			if self.nim.isCompatible("DVB-S2"):
				steps = { 5 : 2000, 4 : 4000, 3 : 6000, 2 : 8000, 1 : 10000 }[self.scan_sat.bs_accuracy.value]
				parm.system = self.scan_sat.bs_system.value
				parm.pilot = eDVBFrontendParametersSatellite.Pilot_Unknown
				parm.rolloff = eDVBFrontendParametersSatellite.RollOff_alpha_0_35
				parm.pls_mode = eDVBFrontendParametersSatellite.PLS_Gold
				parm.is_id = eDVBFrontendParametersSatellite.No_Stream_Id_Filter
			else:
				steps = 4000
				parm.system = eDVBFrontendParametersSatellite.System_DVB_S
			if self.auto_scan:
				parm.symbol_rate = (bs_range[1] - bs_range[0]) // 1000
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

	def startSatelliteTransponderSearch(self, nim_idx, orb_pos):
		if hasattr(self, 'self.frontend'):
			del self.frontend
		if hasattr(self, 'self.channel'):
			del self.channel
		self.frontend = self.channel = None
		self.orb_pos = orb_pos
		self.nim = nimmanager.nim_slots[nim_idx]
		tunername = nimmanager.getNimName(nim_idx)
		self.__tlist = [ ]
		self.tp_found = [ ]
		self.current_range = None
		self.range_list = [ ]
		tuner_no = -1
		self.auto_scan = False

		print("tunername", tunername)
		if nimmanager.nim_slots[nim_idx].supportsBlindScan() or tunername in ("BCM4505", "BCM4506 (internal)", "BCM4506", "Alps BSBE1 C01A/D01A.", "Si2166B", "Si2169C"):
			self.auto_scan = nimmanager.nim_slots[nim_idx].supportsBlindScan() or tunername in ("Si2166B", "Si2169C")
			(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
			if not self.frontend:
				self.session.nav.stopService()
				(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
				if not self.frontend:
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
					(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
					if not self.frontend:
						print("couldn't allocate tuner %d for blindscan!!!" %nim_idx)
						text = _("Sorry, this tuner is in use.")
						if self.session.nav.getRecordings():
							text += "\n"
							text += _("Maybe the reason that recording is currently running.")
						self.session.open(MessageBox, text, MessageBox.TYPE_ERROR)
						return

			band_cutoff_frequency = 11700001

			s1 = self.scan_sat.bs_freq_start.value * 1000
			s2 = self.scan_sat.bs_freq_stop.value * 1000

			start = self.min_freq = min(s1, s2)
			stop = self.max_freq = max(s1, s2)

			if self.auto_scan: # hack for driver based blindscan... extend search range +/- 50Mhz
				limits = self.bs_freq_limits
				start -= 50000
				stop += 50000
				if start < limits[0]:
					start = limits[0]
				if stop >limits[1]:
					stop = limits[1]

			if self.scan_sat.bs_horizontal.value:
				if self.auto_scan and band_cutoff_frequency and stop > band_cutoff_frequency:
					if start < band_cutoff_frequency:
						self.range_list.append((start, min(stop, band_cutoff_frequency), eDVBFrontendParametersSatellite.Polarisation_Horizontal))
					if stop > band_cutoff_frequency:
						self.range_list.append((max(band_cutoff_frequency, start), stop, eDVBFrontendParametersSatellite.Polarisation_Horizontal))
				else:
					self.range_list.append((start, stop, eDVBFrontendParametersSatellite.Polarisation_Horizontal))

			if self.scan_sat.bs_vertical.value:
				if self.auto_scan and band_cutoff_frequency:
					if start < band_cutoff_frequency:
						self.range_list.append((start, min(stop, band_cutoff_frequency), eDVBFrontendParametersSatellite.Polarisation_Vertical))
					if stop > band_cutoff_frequency:
						self.range_list.append((max(band_cutoff_frequency, start), stop, eDVBFrontendParametersSatellite.Polarisation_Vertical))
				else:
					self.range_list.append((start, stop, eDVBFrontendParametersSatellite.Polarisation_Vertical))

			self.parm = self.setNextRange()
			if self.parm is not None:
				tparm = eDVBFrontendParameters()
				tparm.setDVBS(self.parm, False)
				self.frontend.tune(tparm, True)
				self.start_time = time()
				tmpstr = _("Try to find used satellite transponders...")
			else:
				tmpstr = _("Nothing to scan! Press Exit!")
			x = { }
			data = self.frontend.getFrontendData(x)
			tuner_no = x["tuner_number"]
		else:
			if "Sundtek DVB-S/S2" in tunername and "V" in tunername:
				tmpstr = _("Use Sundtek full hardware blind scan!")
			else:
				tmpstr = _("Hardware blind scan is not supported by this tuner (%s)!") % tunername
			self.session.open(MessageBox, tmpstr, MessageBox.TYPE_ERROR)
			return
		self.satellite_search_session = self.session.openWithCallback(self.satelliteTransponderSearchSessionClosed, SatBlindscanState, tuner_no, tmpstr)
		#if self.auto_scan:
		self.timer = eTimer()
		self.timer.callback.append(self.updateStateSat)
		self.timer.stop()
		self.updateStateSat()

class DmmBlindscan(ConfigListScreen, Screen, TransponderSearchSupport, SatelliteTransponderSearchSupport):
	skin="""
	<screen position="center,center" size="620,430" title="Satellite Blindscan">
		<widget name="config" position="10,10" size="600,360" itemHeight="30" scrollbarMode="showOnDemand" />
		<eLabel	position="10,390" size="600,1" backgroundColor="grey"/>
		<widget name="introduction" position="10,398" size="600,25" font="Regular;22" halign="center" />
	</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("Blind scan for DVB-S2 tuners")
		self.skinName = ["Blindscan"]
		Screen.setTitle(self, _(self.setup_title))
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
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list)
		if not self.scan_nims.value == "":
			self.createSetup()
			self["introduction"] = Label(_("Press OK to start the scan."))
		else:
			self["introduction"] = Label(_("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."))

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
		if self.scan_nims.value == "":
			return
		if self.scan_nims == [ ]:
			return
		index_to_scan = int(self.scan_nims.value)
		print("ID: ", index_to_scan)

		self.tunerEntry = getConfigListEntry(_("Tuner"), self.scan_nims)
		self.list.append(self.tunerEntry)

		self.systemEntry = None
		self.modulationEntry = None
		self.satelliteEntry = None
		self.searchtypeEntry = None
		nim = nimmanager.nim_slots[index_to_scan]

		self.scan_networkScan.value = False
		tunername = nimmanager.getNimName(index_to_scan)
		if nim.isCompatible("DVB-S"):
			self.updateSatList()
			selected_sat_pos = self.scan_satselection[index_to_scan].value
			limits = (10700, 12750)
			self.scan_sat.bs_freq_start = ConfigInteger(default = limits[0], limits = (limits[0], limits[1]))
			self.scan_sat.bs_freq_stop = ConfigInteger(default = limits[1], limits = (limits[0], limits[1]))
			self.satelliteEntry = getConfigListEntry(_("Satellite"), self.scan_satselection[index_to_scan])
			self.list.append(self.satelliteEntry)
			self.searchtypeEntry = getConfigListEntry(_("Search type"), self.search_type)
			self.list.append(getConfigListEntry(_("Scan start frequency"), self.scan_sat.bs_freq_start))
			self.list.append(getConfigListEntry(_("Scan stop frequency"), self.scan_sat.bs_freq_stop))
			if nim.isCompatible("DVB-S2") and tunername != "Si2166B" and tunername != "Si2169C":
				self.list.append(getConfigListEntry(_("Accuracy (higher is better)"), self.scan_sat.bs_accuracy))
			self.list.append(getConfigListEntry(_("Horizontal"), self.scan_sat.bs_horizontal))
			self.list.append(getConfigListEntry(_("Vertical"), self.scan_sat.bs_vertical))
			self.list.append(self.searchtypeEntry)
			if self.search_type.value == 0:
				self.list.append(getConfigListEntry(_("Network scan"), self.scan_networkScan))
				self.list.append(getConfigListEntry(_("Clear before scan"), self.scan_clearallservices))
				self.list.append(getConfigListEntry(_("Only free scan"), self.scan_onlyfree))
		self["config"].list = self.list
		self["config"].l.setList(self.list)
		self.bs_freq_limits = ( limits[0]*1000, limits[1]*1000 )

	def Satexists(self, tlist, pos):
		for x in tlist:
			if x == pos:
				return 1
		return 0

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur == self.tunerEntry or cur == self.systemEntry or \
			(self.modulationEntry and self.systemEntry[1].value == eDVBFrontendParametersSatellite.System_DVB_S2 and cur == self.modulationEntry) or \
			(self.satelliteEntry and cur == self.satelliteEntry) or (self.searchtypeEntry and cur == self.searchtypeEntry):
				self.createSetup()

	def createConfig(self, frontendData):
		defaultSat = {
			"orbpos": 192,
			"system": eDVBFrontendParametersSatellite.System_DVB_S,
			"frequency": 11836,
			"inversion": eDVBFrontendParametersSatellite.Inversion_Unknown,
			"symbolrate": 27500,
			"polarization": eDVBFrontendParametersSatellite.Polarisation_Horizontal,
			"fec": eDVBFrontendParametersSatellite.FEC_Auto,
			"fec_s2": eDVBFrontendParametersSatellite.FEC_9_10,
			"modulation": eDVBFrontendParametersSatellite.Modulation_QPSK }

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

		self.scan_sat = ConfigSubsection()
		self.scan_clearallservices = ConfigSelection(default = "no", choices = [("no", _("no")), ("yes", _("yes")), ("yes_hold_feeds", _("yes (keep feeds)"))])
		self.scan_onlyfree = ConfigYesNo(default = False)
		self.scan_networkScan = ConfigYesNo(default = False)

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
		self.scan_nims = ConfigSelection(choices = nim_list)

		self.scan_sat.bs_system = ConfigSelection(default = eDVBFrontendParametersSatellite.System_DVB_S2, 
			choices = [ (eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S + DVB-S2")),
				(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S only"))])

		self.scan_sat.bs_accuracy = ConfigSelection(default = 2, choices = [ (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")])
		self.search_type = ConfigSelection(default = 0, choices = [
			(0, _("scan for channels")),
			(1, _("save to XML file"))])

		self.scan_sat.bs_horizontal = ConfigYesNo(default = True)
		self.scan_sat.bs_vertical = ConfigYesNo(default = True)
		self.nim_sat_frequency_range = []
		self.nim_sat_band_cutoff_frequency = []
		self.scan_satselection = []
		for slot in nimmanager.nim_slots:
			slot_id = slot.slot
			if slot.isCompatible("DVB-S"):
				satlist_for_slot = self.satList[slot_id]
				self.scan_satselection.append(getConfigSatlist(defaultSat["orbpos"], satlist_for_slot))
				sat_freq_range = {(10700000, 12750000) }
				sat_band_cutoff = {11700000 }
				for sat in satlist_for_slot:
					orbpos = sat[0]
				self.nim_sat_frequency_range.append(sat_freq_range)
				self.nim_sat_band_cutoff_frequency.append(sat_band_cutoff)
			else:
				self.nim_sat_frequency_range.append(None)
				self.nim_sat_band_cutoff_frequency.append(None)
				self.scan_satselection.append(None)
		return True

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def addSatTransponder(self, tlist, frequency, symbol_rate, polarisation, fec, inversion, orbital_position, system, modulation, rolloff, pilot):
		print("Add Sat: frequency: " + str(frequency) + " symbol: " + str(symbol_rate) + " pol: " + str(polarisation) + " fec: " + str(fec) + " inversion: " + str(inversion) + " modulation: " + str(modulation) + " system: " + str(system) + " rolloff" + str(rolloff) + " pilot" + str(pilot))
		print("orbpos: " + str(orbital_position))
		parm = eDVBFrontendParametersSatellite()
		parm.modulation = modulation
		parm.system = system
		parm.frequency = frequency * 1000
		parm.symbol_rate = symbol_rate * 1000
		parm.polarisation = polarisation
		parm.fec = fec
		parm.inversion = inversion
		parm.orbital_position = orbital_position
		parm.rolloff = rolloff
		parm.pilot = pilot
		tlist.append(parm)

	def keyGo(self):
		self.orb_position = 0
		self.sat_name = "N\A"
		self.flags = 0
		if self.scan_nims.value == "":
			return
		if self.scan_nims == [ ]:
			self.session.open(MessageBox, _("No tuner is enabled!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			return
		tlist = []
		index_to_scan = int(self.scan_nims.value)

		nim = nimmanager.nim_slots[index_to_scan]
		if nim.isCompatible("DVB-S"):
			flags = self.scan_networkScan.value and eComponentScan.scanNetworkSearch or 0
			tmp = self.scan_clearallservices.value
			if tmp == "yes":
				flags |= eComponentScan.scanRemoveServices
			elif tmp == "yes_hold_feeds":
				flags |= eComponentScan.scanRemoveServices
				flags |= eComponentScan.scanDontRemoveFeeds
			if tmp != "no":
				flags |= eComponentScan.scanDontRemoveUnscanned
			if self.scan_onlyfree.value:
				flags |= eComponentScan.scanOnlyFree
			self.flags = flags
			self.feid = index_to_scan
			self.tlist = []
			sat = self.satList[index_to_scan][self.scan_satselection[index_to_scan].index]
			self.orb_position = sat[0]
			self.sat_name = sat[1]
			self.startSatelliteTransponderSearch(self.feid, sat[0])

	def setTransponderSearchResult(self, tlist):
		self.tlist = tlist

	def TransponderSearchFinished(self, close_user=False):
		if self.tlist is None:
			self.tlist = []
		if self.tlist:
			self.tlist = sorted(self.tlist, key=lambda transponder: transponder.frequency)
			xml_location = self.createSatellitesXMLfile(self.tlist, XML_BLINDSCAN_DIR)
			if self.search_type.value == 0 :
				self.startScan(self.tlist, self.flags, self.feid)
			else:
				msg = _("Search completed. %d transponders found.\n\nDetails saved in:\n%s") % (len(self.tlist), xml_location)
				self.session.openWithCallback(self.callbackNone, MessageBox, msg, MessageBox.TYPE_INFO, timeout=300)
		else:
			if close_user:
				msg = _("The blindscan run was cancelled by the user.")
			else:
				msg = _("No transponders were found for those search parameters!")
			self.session.openWithCallback(self.callbackNone, MessageBox, msg, MessageBox.TYPE_INFO, timeout=60)

	def callbackNone(self, *retval):
		None

	def startScan(self, tlist, flags, feid, networkid = 0):
		if len(tlist):
			self.session.openWithCallback(self.startScanCallback, ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags, "networkid": networkid}])

	def keyCancel(self):
		if hasattr(self, 'self.frontend'):
			del self.frontend
		if hasattr(self, 'self.channel'):
			del self.channel
		self.session.nav.playService(self.session.postScanService)
		for x in self["config"].list:
			x[1].cancel()
		self.close(True)

	def startScanCallback(self, answer=True):
		if answer:
			if hasattr(self, 'self.frontend'):
				del self.frontend
			if hasattr(self, 'self.channel'):
				del self.channel
			self.session.nav.playService(self.session.postScanService)
			self.close(True)

	def createSatellitesXMLfile(self, tp_list, save_xml_dir) :
		pos = self.orb_position
		if pos > 1800 :
			pos -= 3600
		if pos < 0 :
			pos_name = '%dW' % (abs(int(pos))/10)
		else :
			pos_name = '%dE' % (abs(int(pos))/10)
		location = '%s/dmm_blindscan_%s_%s.xml' %(save_xml_dir, pos_name, strftime("%d-%m-%Y_%H-%M-%S"))
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
		xml.append('	<sat name="%s" flags="0" position="%s">\n' % (self.sat_name.replace('&', '&amp;'), self.orb_position))
		for tp in tp_list:
			xml.append('		<transponder frequency="%d" symbol_rate="%d" polarization="%d" fec_inner="%d" system="%d" modulation="%d"/>\n' % (tp.frequency, tp.symbol_rate, tp.polarisation, tp.fec, tp.system, tp.modulation))
		xml.append('	</sat>\n')
		xml.append('</satellites>')
		f = open(location, "w")
		f.writelines(xml)
		f.close()
		return location

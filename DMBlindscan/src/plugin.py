# for localized messages
from . import _

from boxbranding import getBoxType
from Components.ActionMap import NumberActionMap, ActionMap
from Components.config import config, ConfigSubsection, ConfigSelection, \
	ConfigYesNo, ConfigInteger, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.NimManager import nimmanager, getConfigSatlist
from Components.Sources.CanvasSource import CanvasSource
from Components.Sources.List import List
from enigma import eDVBFrontendParameters, eDVBFrontendParametersSatellite, \
	eComponentScan, eDVBSatelliteEquipmentControl as secClass, \
	eTimer, eDVBResourceManager
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.ServiceScan import ServiceScan
from time import time
from Tools.Directories import fileExists
from Tools.Transponder import ConvertToHumanReadable


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
		self["list"]=List()
		self["text"]=Label()
		self["text"].setText(text)
		self["post_action"]=Label()
		self["progress"]=Label()
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
				self["post_action"].setText(_("MANUALLY start service searching, press green to change"))
			else:
				self["post_action"].setText(_("AUTOMATICALLY start service searching, press green to change"))

	def setFinished(self):
		if self.post_action:
			self.finished=1
			self["text"].setText(_("Transponder searching finished!"))
			self["post_action"].setText(_("Press green to start service searching!"))
		else:
			self.close(True)

	def getConstellationBitmap(self, cnt=1):
		ret = []
		path = "/proc/stb/frontend/%d/constellation_bitmap" %self.fe_num
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
		if self.constellation_supported or self.constellation_supported is None:
			pass
		else:
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
					val = int(bitmap[pos:pos+2], 16)
					val = 128 + (val - 256 if val > 127 else val)
				except ValueError:
					print "I constellation data broken at pos", pos
					val = 0
				I.append(val)
			for pos in range(30,60,2):
				try:
					val = int(bitmap[pos:pos+2], 16)
					val = 128 + (val - 256 if val > 127 else val)
				except ValueError:
					print "Q constellation data broken at pos", pos
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
		if self.frontend:
#			self.frontend.getStateChangeSignal().remove(self.frontendStateChanged)
			self.frontend = None
			self.channel = None
		print "satelliteTransponderSearchSessionClosed, val", val
		if val and len(val):
			if val[0]:
				self.setTransponderSearchResult(self.__tlist)
			else:
				self.setTransponderSearchResult(None)
		self.satellite_search_session = None
		self.__tlist = None
                self.timer.stop()
		self.TransponderSearchFinished()

	def updateStateSat(self):
		self.frontendStateChanged()

	def frontendStateChanged(self):
	    state = []
	    state = self.frontend.getState()
#	    print "State=", state[1]
	    if state[1] > 1:
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
				parm.frequency /= 2
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
#				print "SR before round", sr
				if sr < 0:
					print "WARNING blind SR is < 0... skip"
					self.parm.frequency += self.parm.symbol_rate
				else:
					sr_rounded = round(float(sr*2L) / 1000) * 1000
					sr_rounded /= 2
#					print "SR after round", sr_rounded
					parm.symbol_rate = int(sr_rounded)
					fstr += str(parm.symbol_rate/1000)
					parm.fec = d["fec_inner"]
					fstr += " "
					fstr += r["fec_inner"]
					parm.inversion = d["inversion"]
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
					self.__tlist.append(parm)

					print "LOCKED at", freq, "SEARCHED at", self.parm.frequency, "half bw", (135L*((sr+1000)/1000)/200), "half search range", (self.parm.symbol_rate/2)
					self.parm.frequency = freq
					self.parm.frequency += (135L*((sr+999)/1000)/200)
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
				self.parm.frequency += self.parm.symbol_rate

			print "NEXT freq", self.parm.frequency

			mhz_complete, mhz_done = self.stats()
			seconds_done = int(time() - self.start_time)

			if self.parm.frequency > self.range_list[self.current_range][1]:
				self.parm = self.setNextRange()
				if self.parm is not None:
					tparm = eDVBFrontendParameters()
					tparm.setDVBS(self.parm, False)
					self.frontend.tune(tparm)
				else:
					tmpstr = _("%dMHz scanned") %mhz_complete
					tmpstr += ', '
					tmpstr += _("%d transponders found at %d:%02dmin") %(len(self.tp_found),seconds_done / 60, seconds_done % 60)
					state["progress"].setText(tmpstr)
					state.setFinished()
#					self.frontend.getStateChangeSignal().remove(self.frontendStateChanged)
					self.frontend = None
					self.channel = None
					return

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
			tmpstr += "%d/%dMHz" %(mhz_done, mhz_complete)

			tmpstr += ", "
			tmpstr += _("%d transponder(s) found") %len(self.tp_found)

			tmpstr += ', '

			seconds_complete = (seconds_done * mhz_complete) / mhz_done
			tmpstr += _("%d:%02d/%d:%02dmin") %(seconds_done / 60, seconds_done % 60, seconds_complete / 60, seconds_complete % 60)

			state["progress"].setText(tmpstr)

			self.tuneNext()
		else:
			print "unhandled tuner state", x["tuner_state"]
	    self.timer.start(500, True)

	def tuneNext(self):
		tparm = eDVBFrontendParameters()
		tparm.setDVBS(self.parm, False)
		self.frontend.tune(tparm)

	def setNextRange(self):
		if self.current_range is None:
			self.current_range = 0
		else:
			self.current_range += 1
		if len(self.range_list) > self.current_range:
			bs_range = self.range_list[self.current_range]
			parm = eDVBFrontendParametersSatellite()
			parm.frequency = bs_range[0]
			if self.nim.isCompatible("DVB-S2"):
				steps = { 5 : 2000, 4 : 4000, 3 : 6000, 2 : 8000, 1 : 10000 }[self.scan_sat.bs_accuracy.value]
				parm.system = self.scan_sat.bs_system.value
				parm.pilot = eDVBFrontendParametersSatellite.Pilot_Unknown
				parm.rolloff = eDVBFrontendParametersSatellite.RollOff_alpha_0_35
			else:
				steps = 4000
				parm.system = eDVBFrontendParametersSatellite.System_DVB_S
			parm.symbol_rate = steps
			parm.fec = eDVBFrontendParametersSatellite.FEC_Auto
			parm.inversion = eDVBFrontendParametersSatellite.Inversion_Unknown
			parm.polarisation = bs_range[2]
			parm.orbital_position = self.orb_pos
			parm.modulation = eDVBFrontendParametersSatellite.Modulation_QPSK
			return parm
		return None

	def stats(self):
		mhz_complete = 0
		mhz_done = 0
		cnt = 0
		for range in self.range_list:
			mhz = (range[1] - range[0]) / 1000
			mhz_complete += mhz
			if cnt == self.current_range:
				mhz_done += (self.parm.frequency - range[0]) / 1000
			elif cnt < self.current_range:
				mhz_done += mhz
			cnt += 1
		return mhz_complete, mhz_done

	def startSatelliteTransponderSearch(self, nim_idx, orb_pos):
		self.frontend = None
		self.orb_pos = orb_pos
		self.nim = nimmanager.nim_slots[nim_idx]
		tunername = nimmanager.getNimName(nim_idx)
		self.__tlist = [ ]
		self.tp_found = [ ]
		self.current_range = None
		self.range_list = [ ]
		tuner_no = -1
		self.auto_scan = False
		self.timer = eTimer()
		self.timer.callback.append(self.updateStateSat)

		print "tunername", tunername
		if tunername in ("BCM4505", "BCM4506 (internal)", "BCM4506", "Alps BSBE1 C01A/D01A.", "Si2166B"):
			self.auto_scan = tunername == 'Si2166B'
			(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
			if not self.frontend:
				self.session.nav.stopService()
				(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
				if not self.frontend:
					if self.session.pipshown: # try to disable pip
						self.session.pipshown = False
	                                        self.session.deleteDialog(self.session.pip)
						del self.session.pip
					(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
					if not self.frontend:
						print "couldn't allocate tuner %d for blindscan!!!" %nim_idx
						return
#			self.frontend.getStateChangeSignal().append(self.frontendStateChanged)

			band_cutoff_frequency = self.nim_sat_band_cutoff_frequency[nim_idx][orb_pos][0]

			s1 = self.scan_sat.bs_freq_start.value * 1000
			s2 = self.scan_sat.bs_freq_stop.value * 1000

			start = self.min_freq = min(s1,s2)
			stop = self.max_freq = max(s1,s2)

			if self.auto_scan: # hack for driver based blindscan... extend search range +/- 50MHz
				limits = self.scan_sat.bs_freq_limits
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
				self.frontend.tune(tparm)
				self.start_time = time()
				tmpstr = _("Try to find used satellite transponders...")
			else:
				tmpstr = _("Nothing to scan! Press Exit!")
			x = { }
			data = self.frontend.getFrontendData(x)
			tuner_no = x["tuner_number"]
			self.updateStateSat()
		else:
			tmpstr = _("Blindscan is not supported by this tuner (%s)") %tunername
		self.satellite_search_session = self.session.openWithCallback(self.satelliteTransponderSearchSessionClosed, SatBlindscanState, tuner_no, tmpstr)


class Blindscan(ConfigListScreen, Screen, TransponderSearchSupport, SatelliteTransponderSearchSupport):
	skin="""
	<screen position="center,center" size="620,430" title="Satellite Blindscan">
		<widget name="config" position="10,10" size="600,360" itemHeight="30" scrollbarMode="showOnDemand" />
		<eLabel	position="10,390" size="600,1" backgroundColor="grey"/>
		<widget name="introduction" position="10,398" size="600,25" font="Regular;22" halign="center" />
	</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.finished_cb = None
		self.updateSatList()
		self.service = session.nav.getCurrentService()
		self.feinfo = None
		frontendData = None
		if self.service is not None:
			self.feinfo = self.service.frontendInfo()
			frontendData = self.feinfo and self.feinfo.getAll(True)

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

		self.createConfig(frontendData)

		del self.feinfo
		del self.service
		self.session.postScanService = session.nav.getCurrentlyPlayingServiceOrGroup()

		self["actions"] = NumberActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list)
		if not self.scan_nims.value == "":
			self.createSetup()
			self["introduction"] = Label(_("Press OK to start the scan"))
		else:
			self["introduction"] = Label(_("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."))

	def runAsync(self, finished_cb):
		self.finished_cb = finished_cb
		self.keyGo()

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
		index_to_scan = int(self.scan_nims.value)
		print "ID: ", index_to_scan

		self.tunerEntry = getConfigListEntry(_("Tuner"), self.scan_nims)
		self.list.append(self.tunerEntry)
		
		if self.scan_nims == [ ]:
			return
		
		self.systemEntry = None
		self.modulationEntry = None
		self.satelliteEntry = None
		nim = nimmanager.nim_slots[index_to_scan]

		self.scan_networkScan.value = False
#		self.scan_otherSDT.value = False
		if nim.isCompatible("DVB-S"):
			self.updateSatList()
			selected_sat_pos = self.scan_satselection[index_to_scan].value
			limit_list = self.nim_sat_frequency_range[index_to_scan][int(selected_sat_pos)]
			l = limit_list[0]
			limits = ( l[0]/1000, l[1]/1000 )
			self.scan_sat.bs_freq_start = ConfigInteger(default = limits[0], limits = (limits[0], limits[1]))
			self.scan_sat.bs_freq_stop = ConfigInteger(default = limits[1], limits = (limits[0], limits[1]))
			self.satelliteEntry = getConfigListEntry(_("Satellite"), self.scan_satselection[index_to_scan])
			self.list.append(self.satelliteEntry)
			self.list.append(getConfigListEntry(_("Frequency start"), self.scan_sat.bs_freq_start))
			self.list.append(getConfigListEntry(_("Frequency stop"), self.scan_sat.bs_freq_stop))
			if nim.isCompatible("DVB-S2"):
				self.list.append(getConfigListEntry(_("Accuracy (higher is better)"), self.scan_sat.bs_accuracy))
			self.list.append(getConfigListEntry(_("Horizontal"), self.scan_sat.bs_horizontal))
			self.list.append(getConfigListEntry(_("Vertical"), self.scan_sat.bs_vertical))
			self.scan_networkScan.value = True
		self.list.append(getConfigListEntry(_("Network scan"), self.scan_networkScan))
		self.list.append(getConfigListEntry(_("Clear before scan"), self.scan_clearallservices))
		self.list.append(getConfigListEntry(_("Only free scan"), self.scan_onlyfree))
#		if config.usage.setup_level.index >= 2:
#			self.list.append(getConfigListEntry(_("Lookup other SDT"), self.scan_otherSDT))
#			self.list.append(getConfigListEntry(_("Skip empty transponders"), self.scan_skipEmpty))
		self["config"].list = self.list
		self["config"].l.setList(self.list)
		self.scan_sat.bs_freq_limits = ( limits[0]*1000, limits[1]*1000 )

	def Satexists(self, tlist, pos):
		for x in tlist:
			if x == pos:
				return 1
		return 0

	def newConfig(self):
		cur = self["config"].getCurrent()
		print "cur is", cur
		if 	cur == self.tunerEntry or \
			cur == self.systemEntry or \
			(self.modulationEntry and self.systemEntry[1].value == eDVBFrontendParametersSatellite.System_DVB_S2 and cur == self.modulationEntry) or \
			(self.satelliteEntry and cur == self.satelliteEntry):
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
				"fec_s2_8psk": eDVBFrontendParametersSatellite.FEC_Auto,
				"fec_s2_qpsk": eDVBFrontendParametersSatellite.FEC_Auto,
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
						if defaultSat["modulation"] == eDVBFrontendParametersSatellite.Modulation_QPSK:
							defaultSat["fec_s2_qpsk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
						else:
							defaultSat["fec_s2_8psk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
						defaultSat["rolloff"] = frontendData.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35)
						defaultSat["pilot"] = frontendData.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown)
					else:
						defaultSat["fec"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
					defaultSat["orbpos"] = frontendData.get("orbital_position", 0)

			self.scan_sat = ConfigSubsection()
			self.scan_clearallservices = ConfigSelection(default = "no", choices = [("no", _("no")), ("yes", _("yes")), ("yes_hold_feeds", _("yes (keep feeds)"))])
			self.scan_onlyfree = ConfigYesNo(default = False)
			self.scan_networkScan = ConfigYesNo(default = False)
#			self.scan_skipEmpty = ConfigYesNo(default = True)
#			self.scan_otherSDT = ConfigYesNo(default = False)

			nim_list = []
			# collect all nims which are *not* set to "nothing"
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
				if config_mode == "advanced" and len(nimmanager.getSatListForNim(n.slot)) < 1:
					continue
				if config_mode in ("loopthrough", "satposdepends"):
					root_id = nimmanager.sec.getRoot(n.slot_id, int(config.connectedTo.value))
					if n.type == nimmanager.nim_slots[root_id].type: # check if connected from a DVB-S to DVB-S2 Nim or vice versa
						continue
				nim_list.append((str(n.slot), n.friendly_full_description))

			self.scan_nims = ConfigSelection(choices = nim_list)

			self.scan_sat.bs_system = ConfigSelection(default = eDVBFrontendParametersSatellite.System_DVB_S2, 
				choices = [ (eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S + DVB-S2")),
					(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S only"))])

			self.scan_sat.bs_accuracy = ConfigSelection(default = 2, choices = [ (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")])

			self.scan_sat.bs_horizontal = ConfigYesNo(default = True)
			self.scan_sat.bs_vertical = ConfigYesNo(default = True)

			self.scan_scansat = {}
			for sat in nimmanager.satList:
				#print sat[1]
				self.scan_scansat[sat[0]] = ConfigYesNo(default = False)

			sec = secClass.getInstance()

			self.nim_sat_frequency_range = []
			self.nim_sat_band_cutoff_frequency = []
			self.scan_satselection = []
			for slot in nimmanager.nim_slots:
				slot_id = slot.slot
				self.nim_sat_frequency_range.append
				if slot.isCompatible("DVB-S"):
					satlist_for_slot = self.satList[slot_id]
					self.scan_satselection.append(getConfigSatlist(defaultSat["orbpos"], satlist_for_slot))
					sat_freq_range = {}
					sat_band_cutoff = {}
					for sat in satlist_for_slot:
						orbpos = sat[0]
						sat_freq_range[orbpos] = sec.getFrequencyRangeList(slot_id, orbpos)
						sat_band_cutoff[orbpos] = sec.getBandCutOffFrequency(slot_id, orbpos)
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
		print "Add Sat: frequ: " + str(frequency) + " symbol: " + str(symbol_rate) + " pol: " + str(polarisation) + " fec: " + str(fec) + " inversion: " + str(inversion) + " modulation: " + str(modulation) + " system: " + str(system) + " rolloff" + str(rolloff) + " pilot" + str(pilot)
		print "orbpos: " + str(orbital_position)
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
		if self.scan_nims.value == "":
			return
		tlist = []
		flags = None
		startScan = True
		removeAll = True
		index_to_scan = int(self.scan_nims.value)
		
		if self.scan_nims == [ ]:
			self.session.open(MessageBox, _("No tuner is enabled!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			return

		nim = nimmanager.nim_slots[index_to_scan]
		print "nim", nim.slot
		if nim.isCompatible("DVB-S"):
			print "is compatible with DVB-S"
			startScan = False

		flags = self.scan_networkScan.value and eComponentScan.scanNetworkSearch or 0

#		if self.scan_otherSDT.value:
#			flags |= eComponentScan.scanOtherSDT

#		if not self.scan_skipEmpty.value:
#			flags |= eComponentScan.scanDontSkipEmptyTransponders

		tmp = self.scan_clearallservices.value
		if tmp == "yes":
			flags |= eComponentScan.scanRemoveServices
		elif tmp == "yes_hold_feeds":
			flags |= eComponentScan.scanRemoveServices
			flags |= eComponentScan.scanDontRemoveFeeds

		if tmp != "no" and not removeAll:
			flags |= eComponentScan.scanDontRemoveUnscanned

		if self.scan_onlyfree.value:
			flags |= eComponentScan.scanOnlyFree

		for x in self["config"].list:
			x[1].save()

		if startScan:
			self.startScan(tlist, flags, index_to_scan)
		else:
			self.flags = flags
			self.feid = index_to_scan
			self.tlist = []
			sat = self.satList[index_to_scan][self.scan_satselection[index_to_scan].index]
			self.startSatelliteTransponderSearch(self.feid, sat[0])

	def setTransponderSearchResult(self, tlist):
		self.tlist = tlist

	def TransponderSearchFinished(self):
		if self.tlist is None:
			self.tlist = []
		else:
			self.startScan(self.tlist, self.flags, self.feid)

	def startScan(self, tlist, flags, feid):
		if len(tlist):
			# flags |= eComponentScan.scanSearchBAT
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags}])
			else:
				self.session.open(ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags}])
		else:
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)

	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()


def main(session, close=None, **kwargs):
	session.openWithCallback(close, Blindscan)

def BlindscanSetup(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Blind scan"), main, "blindscan", 50)]
	else:
		return []

def Plugins(**kwargs):
	if nimmanager.hasNimType("DVB-S") and getBoxType().startswith('dm'):
		return PluginDescriptor(name=_("Blind scan"), description=_("Scan satellites for new transponders"), where = PluginDescriptor.WHERE_MENU, fnc=BlindscanSetup)
	else:
		return []

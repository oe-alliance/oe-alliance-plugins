# for localized messages
from . import _

from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.Sources.Progress import Progress
from Components.NimManager import nimmanager
from enigma import eDVBFrontendParameters, eDVBFrontendParametersTerrestrial, eDVBResourceManager, eTimer, iFrontendInformation

import os
import sys

from datetime import datetime
import time

from Tools.Directories import resolveFilename, fileExists
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	pass

def setParams(frequency, system, bandwidth = 8): # freq is nine digits (474000000)
	params = eDVBFrontendParametersTerrestrial()
	params.frequency = frequency
	params.bandwidth = bandwidth * 1000000
	params.code_rate_hp = eDVBFrontendParametersTerrestrial.FEC_Auto
	params.code_rate_lp = eDVBFrontendParametersTerrestrial.FEC_Auto
	params.inversion = eDVBFrontendParametersTerrestrial.Inversion_Unknown
	params.system = system
	params.modulation = eDVBFrontendParametersTerrestrial.Modulation_Auto
	params.transmission_mode = eDVBFrontendParametersTerrestrial.TransmissionMode_Auto
	params.guard_interval = eDVBFrontendParametersTerrestrial.GuardInterval_Auto
	params.hierarchy = eDVBFrontendParametersTerrestrial.Hierarchy_Auto
	return params

def setParamsFe(params):
	params_fe = eDVBFrontendParameters()
	params_fe.setDVBT(params)
	return params_fe

def channel2freq(channel, bandwidth = 8): # Europe channels
	if 4 < channel < 13: # Band III
		return (((177 + (bandwidth * (channel - 5))) * 1000000) + 500000)
	elif 20 < channel < 70: # Bands IV,V
		return ((474 + (bandwidth * (channel - 21))) * 1000000) # returns nine digits

class TerrestrialScan(Screen, ConfigListScreen):
	skin = """
	<screen position="c-300,e-80" size="600,70" flags="wfNoBorder" >
		<widget name="background" position="0,0" size="600,70" zPosition="-1" />
		<widget name="action" halign="center" valign="center" position="65,10" size="520,20" font="Regular;18" backgroundColor="#11404040" transparent="1" />
		<widget name="status" halign="center" valign="center" position="65,35" size="520,20" font="Regular;18" backgroundColor="#11000000" transparent="1" />
		<widget name="progress" position="65,55" size="520,5" borderWidth="1" backgroundColor="#11000000"/>
	</screen>"""

	def __init__(self, session, args = 0):
		print "[TerrestrialScan][__init__] Starting..."
		print "[TerrestrialScan][__init__] args", args
		self.session = session
		Screen.__init__(self, session)
		Screen.setTitle(self, _("TerrestrialScan"))

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
		self.uhf_vhf = "uhf"
		self.networkid = 0
		if args:
			if "feid" in args:
				self.selectedNIM = args["feid"]
			if "uhf_vhf" in args:
				self.uhf_vhf = args["uhf_vhf"]
			if "networkid" in args:
				self.networkid = args["networkid"]
		self.isT2tuner = False
		self.frontend = None
		self.rawchannel = None
		#self.feid = None
		self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.index = 0
		self.frequency = 0
		self.system = eDVBFrontendParametersTerrestrial.System_DVB_T
		self.lockTimeout = 50 	# 100ms for tick - 5 sec
		self.tsidOnidTimeout = 100 	# 100ms for tick - 10 sec
		self.snrTimeout = 100 	# 100ms for tick - 10 sec
		self.bandwidth = 8 # MHz
		self.scanTransponders = []
		if self.uhf_vhf == "uhf_vhf":
			for a in range(5,13): # channel
				for b in (eDVBFrontendParametersTerrestrial.System_DVB_T, eDVBFrontendParametersTerrestrial.System_DVB_T2): # system
					self.scanTransponders.append({"channel": a, "system": b, "bandwidth": 7})
		for a in range(21,70): # channel
			for b in (eDVBFrontendParametersTerrestrial.System_DVB_T, eDVBFrontendParametersTerrestrial.System_DVB_T2): # system
				self.scanTransponders.append({"channel": a, "system": b, "bandwidth": 8})
		self.transponders_found = []
		self.transponders_unique = {}
		self.onClose.append(self.__onClose)
		self.onFirstExecBegin.append(self.firstExec)

	def showError(self, message):
		question = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
		question.setTitle(_("TerrestrialScan"))
		self.close()

	def keyCancel(self):
		self.close()

	def firstExec(self):
		try:
			png = resolveFilename(SCOPE_ACTIVE_SKIN, "terrestrialscan/background.png")
		except:
			png = None
		if not png or not fileExists(png):
			png = "%s/images/background.png" % os.path.dirname(sys.modules[__name__].__file__)
		self["background"].instance.setPixmapFromFile(png)

		if len(self.scanTransponders) > 0:
			self["action"].setText(_('Starting search...'))
			self["status"].setText(_("Scanning for active transponders"))
			self.progresscount = len(self.scanTransponders)
			self.progresscurrent = 1
			self["progress_text"].range = self.progresscount
			self["progress_text"].value = self.progresscurrent
			self["progress"].setRange((0, self.progresscount))
			self["progress"].setValue(self.progresscurrent)
			self.timer = eTimer()
			self.timer.callback.append(self.search)
			self.timer.start(100, 1)
		else:
			self.showError(_('No frequencies to search'))

	def search(self):
		if self.index < len(self.scanTransponders):
			self.channel = self.scanTransponders[self.index]["channel"]
			self.system = self.scanTransponders[self.index]["system"]
			self.bandwidth = self.scanTransponders[self.index]["bandwidth"]
			self.frequency = channel2freq(self.channel, self.bandwidth)
			print "[TerrestrialScan][Search] Scan channel %d" % self.channel
			print "[TerrestrialScan][Search] Scan system %d" % self.system
			print "[TerrestrialScan][Search] Scan bandwidth %d" % self.bandwidth
			self.progresscurrent = self.index
			self["progress_text"].value = self.progresscurrent
			self["progress"].setValue(self.progresscurrent)
			self["action"].setText(_("Scanning channel %s") % str(self.channel))
			self["status"].setText(ngettext("Found %d unique transponder", "Found %d unique transponders", len(self.transponders_unique)) % len(self.transponders_unique))
			self.index += 1
			if self.frequency in self.transponders_found or self.system == eDVBFrontendParametersTerrestrial.System_DVB_T2 and self.isT2tuner == False:
				print "[TerrestrialScan][Search] Skipping T2 search of channel ", self.channel
				self.search()
				return
			self.searchtimer = eTimer()
			self.searchtimer.callback.append(self.getFrontend)
			self.searchtimer.start(100, 1)
		else:
			if len(self.transponders_unique) > 0:
				answer = [self.selectedNIM, self.transponders_unique]
			else:
				answer = None
			self.close(answer)

	def getFrontend(self):
		print "[TerrestrialScan][getFrontend] searching for available tuner"
		nimList = []
		if self.selectedNIM < 0: # automatic tuner selection
			for nim in nimmanager.nim_slots:
				if nim.config_mode not in ("nothing",) and (nim.isCompatible("DVB-T2") or (nim.isCompatible("DVB-S") and nim.canBeCompatible("DVB-T2"))):
					nimList.append(nim.slot)
					self.isT2tuner = True
			if len(nimList) == 0:
				print "[TerrestrialScan][getFrontend] No T2 tuner found"
				for nim in nimmanager.nim_slots:
					if nim.config_mode not in ("nothing",) and (nim.isCompatible("DVB-T") or (nim.isCompatible("DVB-S") and nim.canBeCompatible("DVB-T"))):
						nimList.append(nim.slot)
			if len(nimList) == 0:
				print "[TerrestrialScan][getFrontend] No terrestrial tuner found"
				self.showError(_('No terrestrial tuner found'))
				return
		else: # manual tuner selection, and subsequent iterations
			nim = nimmanager.nim_slots[self.selectedNIM]
			if nim.config_mode not in ("nothing",) and (nim.isCompatible("DVB-T2") or (nim.isCompatible("DVB-S") and nim.canBeCompatible("DVB-T2"))):
				nimList.append(nim.slot)
				self.isT2tuner = True
			if len(nimList) == 0:
				print "[TerrestrialScan][getFrontend] User selected tuner is not T2 compatible"
				if nim.config_mode not in ("nothing",) and (nim.isCompatible("DVB-T") or (nim.isCompatible("DVB-S") and nim.canBeCompatible("DVB-T"))):
					nimList.append(nim.slot)
			if len(nimList) == 0:
				print "[TerrestrialScan][getFrontend] User selected tuner not configured"
				self.showError(_('Selected tuner is not cofigured'))
				return

		if len(nimList) == 0:
			print "[TerrestrialScan][getFrontend] No terrestrial tuner found"
			self.showError(_('No terrestrial tuner found'))
			return

		resmanager = eDVBResourceManager.getInstance()
		if not resmanager:
			print "[TerrestrialScan][getFrontend] Cannot retrieve Resource Manager instance"
			self.showError(_('Cannot retrieve Resource Manager instance'))
			return

		if self.selectedNIM < 0: # automatic tuner selection
			print "[TerrestrialScan][getFrontend] Choosing NIM"

		# stop pip if running
		if self.session.pipshown:
			self.session.pipshown = False
			del self.session.pip
			print "[TerrestrialScan][getFrontend] Stopping PIP."

		# Find currently playin NIM
		currentlyPlayingNIM = None
		currentService = self.session and self.session.nav.getCurrentService()
		frontendInfo = currentService and currentService.frontendInfo()
		frontendData = frontendInfo and frontendInfo.getAll(True)
		if frontendData is not None:
			currentlyPlayingNIM = frontendData.get("tuner_number", None)
		del frontendInfo
		del currentService

		current_slotid = -1
		if self.rawchannel:
			self.rawchannel.receivedTsidOnid.get().remove(self.gotTsidOnid)
			del(self.rawchannel)

		self.frontend = None
		self.rawchannel = None

		nimList.reverse() # start from the last
		for slotid in nimList:
			if current_slotid == -1:	# mark the first valid slotid in case of no other one is free
				current_slotid = slotid
			self.rawchannel = resmanager.allocateRawChannel(slotid)
			if self.rawchannel:
 				print "[TerrestrialScan][getFrontend] Nim found on slot id %d" % (slotid)
				current_slotid = slotid
				break

		if current_slotid == -1:
			print "[TerrestrialScan][getFrontend] No valid NIM found"
			self.showError(_('No valid NIM found for terrestrial'))
			return

		if not self.rawchannel:
			# if we are here the only possible option is to close the active service
			if currentlyPlayingNIM in nimList:
				slotid = currentlyPlayingNIM
				print "[TerrestrialScan][getFrontend] Nim found on slot id %d but it's busy. Stopping active service" % slotid
				self.session.postScanService = self.session.nav.getCurrentlyPlayingServiceReference()
				self.session.nav.stopService()
				self.rawchannel = resmanager.allocateRawChannel(slotid)
				if self.rawchannel:
					print "[TerrestrialScan][getFrontend] The active service was stopped, and the NIM is now free to use."
					current_slotid = slotid

			if not self.rawchannel:
				if self.session.nav.RecordTimer.isRecording():
					print "[TerrestrialScan][getFrontend] Cannot free NIM because a recording is in progress"
					self.showError(_('Cannot free NIM because a recording is in progress'))
					return
				else:
					print "[TerrestrialScan][getFrontend] Cannot get the NIM"
					self.showError(_('Cannot get the NIM'))
					return

		print "[TerrestrialScan][getFrontend] Will wait up to %i seconds for tuner lock." % (self.lockTimeout/10)

		self.selectedNIM = current_slotid # Remember for next iteration

		self.rawchannel.receivedTsidOnid.get().append(self.gotTsidOnid)

		self.frontend = self.rawchannel.getFrontend()
		if not self.frontend:
			print "[TerrestrialScan][getFrontend] Cannot get frontend"
			self.showError(_('Cannot get frontend'))
			return

		self.rawchannel.requestTsidOnid()

		self.tsid = None
		self.onid = None

		self.frontend.tune(setParamsFe(setParams(self.frequency, self.system, self.bandwidth)))

		self.lockcounter = 0
		self.locktimer = eTimer()
		self.locktimer.callback.append(self.checkTunerLock)
		self.locktimer.start(100, 1)

	def checkTunerLock(self):
		self.dict = {}
		self.frontend.getFrontendStatus(self.dict)
		if self.dict["tuner_state"] == "TUNING":
			print "[TerrestrialScan][checkTunerLock] TUNING"
		elif self.dict["tuner_state"] == "LOCKED":
			print "[TerrestrialScan][checkTunerLock] ACQUIRING TSID/ONID"
			self["action"].setText(_("Reading channel %s") % str(self.channel))
			#self["status"].setText(_("Reading channel %s...") % str(self.channel))

			self.tsidOnidCounter = 0
			self.tsidOnidtimer = eTimer()
			self.tsidOnidtimer.callback.append(self.tsidOnidWait)
			self.tsidOnidtimer.start(100, 1)
			return
		elif self.dict["tuner_state"] in ("LOSTLOCK", "FAILED"):
			print "[TerrestrialScan][checkTunerLock] TUNING FAILED"
			self.search()
			return

		self.lockcounter += 1
		if self.lockcounter > self.lockTimeout:
			print "[TerrestrialScan][checkTunerLock] Timeout for tuner lock"
			self.search()
			return
		self.locktimer.start(100, 1)

	def tsidOnidWait(self):
		if self.tsid is not None and self.onid is not None:
			print "[TerrestrialScan][tsidOnidWait] tsid & onid found", self.tsid, self.onid
			self.signalQualityCounter = 0
			self.signalQualitytimer = eTimer()
			self.signalQualitytimer.callback.append(self.signalQualityWait)
			self.signalQualitytimer.start(100, 1)
			return

		self.tsidOnidCounter +=1
		if self.tsidOnidCounter > self.tsidOnidTimeout:
			print "[TerrestrialScan][tsidOnidWait] tsid & onid wait failed"
			self.search()
			return
		self.tsidOnidtimer.start(100, 1)

	def gotTsidOnid(self, tsid, onid):
		if tsid is not None and onid is not None:
			self.tsid = tsid
			self.onid = onid

	def signalQualityWait(self):
		signalQuality = self.frontend.readFrontendData(iFrontendInformation.signalQuality)
		if signalQuality > 0:
			time.sleep(2) # allow extra time to get a stable reading
			signalQuality = self.frontend.readFrontendData(iFrontendInformation.signalQuality)
			if signalQuality > 0:
				found = {"frequency": self.frequency, "tsid": self.tsid, "onid": self.onid, "system": self.system, "bandwidth": self.bandwidth,"signalQuality": signalQuality}
				self.transponders_found.append(self.frequency)
				tsidOnidKey = "%x:%x" % (self.tsid, self.onid)
				if (tsidOnidKey not in self.transponders_unique or self.transponders_unique[tsidOnidKey]["signalQuality"] < signalQuality) and (self.networkid == 0 or self.networkid == self.onid):
					self.transponders_unique[tsidOnidKey] = found
				print "[TerrestrialScan][signalQualityWait] transponder details", found
				self.search()
				return

		self.signalQualityCounter +=1
		if self.signalQualityCounter > self.snrTimeout:
			print "[TerrestrialScan][signalQualityWait] Failed to collect SNR"
			self.search()
			return
		self.signalQualitytimer.start(100, 1)

	def __onClose(self):
		if self.frontend:
			self.frontend = None
			self.rawchannel.receivedTsidOnid.get().remove(self.gotTsidOnid)
			del(self.rawchannel)

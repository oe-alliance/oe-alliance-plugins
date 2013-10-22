# for localized messages
from .. import _

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar

from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker
from Components.TuneTest import Tuner
from Components.NimManager import nimmanager
from enigma import eTimer, eServiceReference, eDVBDB, iPlayableService, eDVBFrontendParametersSatellite, eDVBResourceManager, eDVBFrontendParameters

from manager import Manager
from providerconfig import ProviderConfig
from time import localtime, time, strftime, mktime

from .. import log
import os
import sys

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, fileExists
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	pass

class AutoBouquetsMaker(Screen):
	skin = """
	<screen position="c-300,e-80" size="600,70" title="CrossEPG" flags="wfNoBorder" >
		<widget name="background" position="0,0" size="600,70" zPosition="-1" />
		<widget name="action" halign="center" valign="center" position="65,10" size="520,20" font="Regular;18" backgroundColor="#11404040" transparent="1" />
		<widget name="status" halign="center" valign="center" position="65,35" size="520,20" font="Regular;18" backgroundColor="#11000000" transparent="1" />
		<widget name="progress" position="65,55" size="520,5" borderWidth="1" backgroundColor="#11000000"/>
	</screen>"""

	LOCK_TIMEOUT = 300 	# 100ms for tick - 30 sec

	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)
		Screen.setTitle(self, _("AutoBouquetsMaker"))

		self["background"] = Pixmap()
		self["action"] = Label(_("Starting scanner"))
		self["status"] = Label("")
		self["progress"] = ProgressBar()

		self.frontend = None
		self.rawchannel = None
		self.postScanService = None
		self.providers = Manager().getProviders()
		self.actionsList = []

		self.onFirstExecBegin.append(self.firstExec)

	def firstExec(self, postScanService=None):
		from Screens.Standby import inStandby
		if not inStandby:
			try:
				png = resolveFilename(SCOPE_ACTIVE_SKIN, "autobouquetsmaker/background.png")
			except:
				png = None
			if not png or not fileExists(png):
				png = "%s/../images/background.png" % os.path.dirname(sys.modules[__name__].__file__)
			self["background"].instance.setPixmapFromFile(png)

		if len(config.autobouquetsmaker.providers.value) > 0:
			if not inStandby:
				self["action"].setText(_('Loading bouquets...'))
				self["status"].setText(_("Services: 0 video - 0 radio"))
			self.timer = eTimer()
			self.timer.callback.append(self.go)
			self.timer.start(100, 1)
		else:
			self.showError(_('Please first setup, in configuration'))

	def showError(self, message):
		from Screens.Standby import inStandby
		if self.rawchannel:
			del(self.rawchannel)

		self.frontend = None
		self.rawchannel = None

		if self.postScanService:
			self.session.nav.playService(self.postScanService)
			self.postScanService = None
		if not inStandby:
			question = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
			question.setTitle(_("AutoBouquetsMaker"))
		self.close()

	def keyCancel(self):
		if self.self.postScanService:
			self.session.nav.playService(self.postScanService)
		self.close()

	def go(self):
		from Screens.Standby import inStandby
		self.manager = Manager()
		self.manager.setPath("/etc/enigma2")
		self.manager.setAddPrefix(config.autobouquetsmaker.addprefix.value)

		self.selectedProviders = {}
		self.actionsList = []

		providers_tmp = config.autobouquetsmaker.providers.value.split("|")
		for provider_tmp in providers_tmp:
			provider_config = ProviderConfig(provider_tmp)
			if provider_config.isValid():
				self.actionsList.append(provider_config.getProvider())
				self.selectedProviders[provider_config.getProvider()] = provider_config

		if config.autobouquetsmaker.keepallbouquets.getValue():
			bouquets = Manager().getBouquetsList()
			bouquets_tv = []
			bouquets_radio = []
			for bouquet in bouquets["tv"]:
				if bouquet["filename"][:12] == "autobouquet.":
					continue
				if len(bouquet["filename"]) > 0:
					bouquets_tv.append(bouquet["filename"])
			for bouquet in bouquets["radio"]:
				if bouquet["filename"][:12] == "autobouquet.":
					continue
				if len(bouquet["filename"]) > 0:
					bouquets_radio.append(bouquet["filename"])
			self.manager.setBouquetsToKeep(bouquets_tv, bouquets_radio)
		else:
			bouquets = config.autobouquetsmaker.keepbouquets.value.split("|")
			bouquets_tv = []
			bouquets_radio = []
			for bouquet in bouquets:
				if bouquet[-3:] == ".tv":
					bouquets_tv.append(bouquet)
				else:
					bouquets_radio.append(bouquet)
			self.manager.setBouquetsToKeep(bouquets_tv, bouquets_radio)

		bouquetsToHide = {}
		bouquets = config.autobouquetsmaker.hidesections.value.split("|")
		for bouquet in bouquets:
			tmp = bouquet.split(":")
			if len(tmp) != 2:
				continue

			if tmp[0].strip() not in bouquetsToHide:
				bouquetsToHide[tmp[0].strip()] = []

			bouquetsToHide[tmp[0].strip()].append(int(tmp[1].strip()))
		self.manager.setBouquetsToHide(bouquetsToHide)

		self.manager.load()

		self.progresscount = (len(self.actionsList) * 2) + 3
		self.progresscurrent = 1

		if not inStandby:
			self["progress"].setRange((0, self.progresscount))
			self["progress"].setValue(self.progresscurrent)

		self.timer = eTimer()
		self.timer.callback.append(self.doActions)
		self.timer.start(100, 1)

	def doActions(self):
		from Screens.Standby import inStandby
		if len(self.actionsList) == 0:
			self.progresscurrent += 1
			if not inStandby:
				self["progress"].setValue(self.progresscurrent)
				self["action"].setText(_('Bouquets generation...'))
				self["status"].setText(_("Services: %d video - %d radio") % (self.manager.getServiceVideoRead(), self.manager.getServiceAudioRead()))
			self.timer = eTimer()
			self.timer.callback.append(self.doBuildIndex)
			self.timer.start(100, 1)
			return

		self.currentAction = self.actionsList[0]
		del(self.actionsList[0])

		self.progresscurrent += 1
		if not inStandby:
			self["progress"].setValue(self.progresscurrent)
			self["action"].setText(_("Tuning %s...") % str(self.providers[self.currentAction]["name"]))
			self["status"].setText(_("Services: %d video - %d radio") % (self.manager.getServiceVideoRead(), self.manager.getServiceAudioRead()))
		self.timer = eTimer()
		self.timer.callback.append(self.doTune)
		self.timer.start(100, 1)

	def doTune(self):
		from Screens.Standby import inStandby
		transponder = self.providers[self.currentAction]["transponder"]
		nimList = nimmanager.getNimListOfType("DVB-S")
		if len(nimList) == 0:
			print>>log, "[AutoBouquetsMaker] No DVB-S NIMs founds"
			self.showError(_('No DVB-S NIMs founds'))
			return

		resmanager = eDVBResourceManager.getInstance()
		if not resmanager:
			print>>log, "[AutoBouquetsMaker] Cannot retrieve Resource Manager instance"
			self.showError(_('Cannot retrieve Resource Manager instance'))
			return

		print>>log, "[AutoBouquetsMaker] Search NIM for orbital position %d" % transponder["orbital_position"]
		current_slotid = -1
		if self.rawchannel:
			del(self.rawchannel)

		self.frontend = None
		self.rawchannel = None

		nimList.reverse() # start from the last
		for slotid in nimList:
			sats = nimmanager.getSatListForNim(slotid)
			for sat in sats:
				if sat[0] == transponder["orbital_position"]:
					if current_slotid == -1:	# mark the first valid slotid in case of no other one is free
						current_slotid = slotid

					self.rawchannel = resmanager.allocateRawChannel(slotid)
					if self.rawchannel:
						print>>log, "[AutoBouquetsMaker] Nim found on slot id %d with sat %s" % (slotid, sat[1])
						current_slotid = slotid
						break

			if self.rawchannel:
				break

		if current_slotid == -1:
			print>>log, "[AutoBouquetsMaker] No valid NIM found"
			self.showError(_('No valid NIM found'))
			return

		if not self.rawchannel:
			print>>log, "[AutoBouquetsMaker] Nim found on slot id %d but it's busy. Stop current service" % current_slotid
			if self.session.nav.RecordTimer.isRecording():
				print>>log, "[AutoBouquetsMaker] Cannot free NIM because a record is in progress"
				self.showError(_('Cannot free NIM because a record is in progress'))
				return

			self.postScanService = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.stopService()
			if self.session.pipshown:
				self.session.pipshown = False

			self.rawchannel = resmanager.allocateRawChannel(current_slotid)
			if not self.rawchannel:
				print>>log, "[AutoBouquetsMaker] Cannot get the NIM"
				self.showError(_('Cannot get the NIM'))
				return

		self.frontend = self.rawchannel.getFrontend()
		if not self.frontend:
			print>>log, "[AutoBouquetsMaker] Cannot get frontend"
			self.showError(_('Cannot get frontend'))
			return

		demuxer_id = self.rawchannel.reserveDemux()
		if demuxer_id < 0:
			print>>log, "[AutoBouquetsMaker] Cannot allocate the demuxer"
			self.showError(_('Cannot allocate the demuxer'))
			return

		params = eDVBFrontendParametersSatellite()
		params.frequency = transponder["frequency"]
		params.symbol_rate = transponder["symbol_rate"]
		params.polarisation = transponder["polarization"]
		params.fec = transponder["fec_inner"]
		params.inversion = transponder["inversion"]
		params.orbital_position = transponder["orbital_position"]
		params.system = transponder["system"]
		params.modulation = transponder["modulation"]
		params.rolloff = transponder["roll_off"]
		params.pilot = transponder["pilot"]
		params_fe = eDVBFrontendParameters()
		params_fe.setDVBS(params, False)
		self.rawchannel.requestTsidOnid()
		self.frontend.tune(params_fe)
		self.manager.setAdapter(0)	# FIX: use the correct device
		self.manager.setDemuxer(demuxer_id)
		self.manager.setFrontend(current_slotid)

		self.lockcounter = 0
		self.locktimer = eTimer()
		self.locktimer.callback.append(self.checkTunerLock)
		self.locktimer.start(100, 1)

	def checkTunerLock(self):
		from Screens.Standby import inStandby
		dict = {}
		self.frontend.getFrontendStatus(dict)
		if dict["tuner_state"] == "TUNING":
			print>>log, "[AutoBouquetsMaker] TUNING"
		elif dict["tuner_state"] == "LOCKED":
			print>>log, "[AutoBouquetsMaker] ACQUIRING TSID/ONID"
			self.progresscurrent += 1
			if not inStandby:
				self["progress"].setValue(self.progresscurrent)
				self["action"].setText(_("Reading %s...") % str(self.providers[self.currentAction]["name"]))
				self["status"].setText(_("Services: %d video - %d radio") % (self.manager.getServiceVideoRead(), self.manager.getServiceAudioRead()))
			self.timer = eTimer()
			self.timer.callback.append(self.doScan)
			self.timer.start(100, 1)
			return
		elif dict["tuner_state"] == "LOSTLOCK" or dict["tuner_state"] == "FAILED":
			print>>log, "[AutoBouquetsMaker] FAILED"

		self.lockcounter += 1
		if self.lockcounter > self.LOCK_TIMEOUT:
			print>>log, "[AutoBouquetsMaker] Timeout for tuner lock"
			self.showError(_('Timeout for tuner lock'))
			return

		self.locktimer.start(100, 1)

	def doScan(self):
		if not self.manager.read(self.selectedProviders[self.currentAction]):
			print>>log, "[AutoBouquetsMaker] Cannot read data"
			self.showError(_('Cannot read data'))
			return
		self.doActions()

	def doBuildIndex(self):
		self.manager.save()
		self.scanComplete()

	def scanComplete(self):
		from Screens.Standby import inStandby
		if self.rawchannel:
			del(self.rawchannel)

		self.frontend = None
		self.rawchannel = None

		eDVBDB.getInstance().reloadServicelist()
		eDVBDB.getInstance().reloadBouquets()
		if self.postScanService:
			self.session.nav.playService(self.postScanService)
			self.postScanService = None
		self.progresscurrent += 1
		if not inStandby:
			self["progress"].setValue(self.progresscurrent)
			self["action"].setText(_('Done'))
			self["status"].setText(_("Services: %d video - %d radio") % (self.manager.getServiceVideoRead(), self.manager.getServiceAudioRead()))

		self.timer = eTimer()
		self.timer.callback.append(self.close)
		self.timer.start(2000, 1)

	def about(self):
		self.session.open(MessageBox,"AutoBouquetsMaker\nVersion date - 21/10/2012\n\nCoded by:\n\nSkaman and AndyBlac",MessageBox.TYPE_INFO)

	def help(self):
		self.session.open(MessageBox,"AutoBouquetsMaker\nto be coded.",MessageBox.TYPE_INFO)

	def cancel(self):
		self.close(None)

autoAutoBouquetsMakerTimer = None
def AutoBouquetsMakerautostart(reason, session=None, **kwargs):
	"called with reason=1 to during /sbin/shutdown.sysvinit, with reason=0 at startup?"
	global autoAutoBouquetsMakerTimer
	global _session
	now = int(time())
	if reason == 0:
		print>>log, "[AutoBouquetsMaker] AutoStart Enabled"
		if session is not None:
			_session = session
			if autoAutoBouquetsMakerTimer is None:
				autoAutoBouquetsMakerTimer = AutoAutoBouquetsMakerTimer(session)
	else:
		print>>log, "[AutoBouquetsMaker] Stop"
		autoAutoBouquetsMakerTimer.stop()

class AutoAutoBouquetsMakerTimer:
	instance = None
	def __init__(self, session):
		self.session = session
		self.autobouquetsmakertimer = eTimer()
		self.autobouquetsmakertimer.callback.append(self.AutoBouquetsMakeronTimer)
		self.autobouquetsmakeractivityTimer = eTimer()
		self.autobouquetsmakeractivityTimer.timeout.get().append(self.autobouquetsmakerdatedelay)
		now = int(time())
		global AutoBouquetsMakerTime
		if config.autobouquetsmaker.schedule.value:
			print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker Schedule Enabled at ", strftime("%c", localtime(now))
			if now > 1262304000:
				self.autobouquetsmakerdate()
			else:
				print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker Time not yet set."
				AutoBouquetsMakerTime = 0
				self.autobouquetsmakeractivityTimer.start(36000)
		else:
			AutoBouquetsMakerTime = 0
			print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker Schedule Disabled at", strftime("%c", localtime(now))
			self.autobouquetsmakeractivityTimer.stop()

		assert AutoAutoBouquetsMakerTimer.instance is None, "class AutoAutoBouquetsMakerTimer is a singleton class and just one instance of this class is allowed!"
		AutoAutoBouquetsMakerTimer.instance = self

	def __onClose(self):
		AutoAutoBouquetsMakerTimer.instance = None

	def autobouquetsmakerdatedelay(self):
		self.autobouquetsmakeractivityTimer.stop()
		self.autobouquetsmakerdate()

	def getAutoBouquetsMakerTime(self):
		backupclock = config.autobouquetsmaker.scheduletime.value
		nowt = time()
		now = localtime(nowt)
		return int(mktime((now.tm_year, now.tm_mon, now.tm_mday, backupclock[0], backupclock[1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))

	def autobouquetsmakerdate(self, atLeast = 0):
		self.autobouquetsmakertimer.stop()
		global AutoBouquetsMakerTime
		AutoBouquetsMakerTime = self.getAutoBouquetsMakerTime()
		now = int(time())
		if AutoBouquetsMakerTime > 0:
			if AutoBouquetsMakerTime < now + atLeast:
				if config.autobouquetsmaker.repeattype.value == "daily":
					AutoBouquetsMakerTime += 24*3600
					while (int(AutoBouquetsMakerTime)-30) < now:
						AutoBouquetsMakerTime += 24*3600
				elif config.autobouquetsmaker.repeattype.value == "weekly":
					AutoBouquetsMakerTime += 7*24*3600
					while (int(AutoBouquetsMakerTime)-30) < now:
						AutoBouquetsMakerTime += 7*24*3600
				elif config.autobouquetsmaker.repeattype.value == "monthly":
					AutoBouquetsMakerTime += 30*24*3600
					while (int(AutoBouquetsMakerTime)-30) < now:
						AutoBouquetsMakerTime += 30*24*3600
			next = AutoBouquetsMakerTime - now
			self.autobouquetsmakertimer.startLongTimer(next)
		else:
			AutoBouquetsMakerTime = -1
		print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker Time set to", strftime("%c", localtime(AutoBouquetsMakerTime)), strftime("(now=%c)", localtime(now))
		return AutoBouquetsMakerTime

	def backupstop(self):
		self.autobouquetsmakertimer.stop()

	def AutoBouquetsMakeronTimer(self):
		self.autobouquetsmakertimer.stop()
		now = int(time())
		wake = self.getAutoBouquetsMakerTime()
		# If we're close enough, we're okay...
		atLeast = 0
		if wake - now < 60:
			print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker onTimer occured at", strftime("%c", localtime(now))
			from Screens.Standby import inStandby
			if not inStandby:
				message = _("Your STB_BOX is about to update your bouquets,\nDo you want to allow this?")
				ybox = self.session.openWithCallback(self.doAutoBouquetsMaker, MessageBox, message, MessageBox.TYPE_YESNO, timeout = 30)
				ybox.setTitle('Scheduled AutoBouquetsMaker.')
			else:
				self.doAutoBouquetsMaker(True)
		else:
			self.autobouquetsmakerdate(60)

	def doAutoBouquetsMaker(self, answer):
		now = int(time())
		if answer is False:
			if config.autobouquetsmaker.retrycount.value < 2:
				print '[AutoBouquetsMaker] Number of retries',config.autobouquetsmaker.retrycount.value
				print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker delayed."
				repeat = config.autobouquetsmaker.retrycount.value
				repeat += 1
				config.autobouquetsmaker.retrycount.value = repeat
				AutoBouquetsMakerTime = now + (int(config.autobouquetsmaker.retry.value) * 60)
				print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker Time now set to", strftime("%c", localtime(AutoBouquetsMakerTime)), strftime("(now=%c)", localtime(now))
				self.autobouquetsmakertimer.startLongTimer(int(config.autobouquetsmaker.retry.value) * 60)
			else:
				atLeast = 60
				print>>log, "[AutoBouquetsMaker] Enough Retries, delaying till next schedule.", strftime("%c", localtime(now))
				self.session.open(MessageBox, _("Enough Retries, delaying till next schedule."), MessageBox.TYPE_INFO, timeout = 10)
				config.autobouquetsmaker.retrycount.value = 0
				self.autobouquetsmakerdate(atLeast)
		else:
			self.timer = eTimer()
			self.timer.callback.append(self.doautostartscan)
			print>>log, "[AutoBouquetsMaker] Running AutoBouquetsMaker", strftime("%c", localtime(now))
			self.timer.start(100, 1)

	def doautostartscan(self):
		print 'STARTing'
		self.session.open(AutoBouquetsMaker)

	def doneConfiguring(self):
		now = int(time())
		if config.autobouquetsmaker.schedule.value:
			if autoAutoBouquetsMakerTimer is not None:
				print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker Schedule Enabled at", strftime("%c", localtime(now))
				autoAutoBouquetsMakerTimer.autobouquetsmakerdate()
		else:
			if autoAutoBouquetsMakerTimer is not None:
				global AutoBouquetsMakerTime
				AutoBouquetsMakerTime = 0
				print>>log, "[AutoBouquetsMaker] AutoBouquetsMaker Schedule Disabled at", strftime("%c", localtime(now))
				autoAutoBouquetsMakerTimer.backupstop()
		if AutoBouquetsMakerTime > 0:
			t = localtime(AutoBouquetsMakerTime)
			autobouquetsmakertext = strftime(_("%a %e %b  %-H:%M"), t)
		else:
			autobouquetsmakertext = ""

from __future__ import print_function
from __future__ import absolute_import
# for localized messages
from . import _

from time import mktime, strftime, time, localtime
from Components.config import config
from enigma import eTimer

from .ChannelsImporter import ChannelsImporter

autoChannelsImporterTimer = None


def autostart(reason, session=None, **kwargs):
	"called with reason=1 to during /sbin/shutdown.sysvinit, with reason=0 at startup?"
	global autoChannelsImporterTimer
	global _session
	now = int(time())
	if reason == 0:
		print("[ChannelsImporterScheduler][ChannelsImporterautostart] AutoStart Enabled")
		if session is not None:
			_session = session
			if autoChannelsImporterTimer is None:
				autoChannelsImporterTimer = AutoChannelsImporterTimer(session)
	else:
		print("[ChannelsImporterScheduler][ChannelsImporterautostart] Stop")
		autoChannelsImporterTimer.stop()


class AutoChannelsImporterTimer:
	instance = None

	def __init__(self, session):
		self.session = session
		self.channelsimportertimer = eTimer()
		self.channelsimportertimer.callback.append(self.ChannelsImporteronTimer)
		self.channelsimporteractivityTimer = eTimer()
		self.channelsimporteractivityTimer.timeout.get().append(self.channelsimporterchannelsimporterdatedelay)
		now = int(time())
		if config.plugins.ChannelsImporter.importOnRestart.value:
			self.boottimer = eTimer()
			self.boottimer.callback.append(self.doautostartscan)
			print("[ChannelsImporterScheduler][AutoChannelsImporterTimer] Run plugin on boot")
			self.boottimer.start(100, 1)
	
		global ChannelsImporterTime
		if config.plugins.ChannelsImporter.enableSchedule.value:
			print("[ChannelsImporterScheduler][AutoChannelsImporterTimer] Schedule Enabled at ", strftime("%c", localtime(now)))
			if now > 1262304000:
				self.channelsimporterdate()
			else:
				print("[ChannelsImporterScheduler][AutoChannelsImporterTimer] Time not yet set.")
				ChannelsImporterTime = 0
				self.channelsimporteractivityTimer.start(36000)
		else:
			ChannelsImporterTime = 0
			print("[ChannelsImporterScheduler][AutoChannelsImporterTimer] Schedule Disabled at", strftime("%c", localtime(now)))
			self.channelsimporteractivityTimer.stop()

		assert AutoChannelsImporterTimer.instance is None, "class AutoChannelsImporterTimer is a singleton class and just one instance of this class is allowed!"
		AutoChannelsImporterTimer.instance = self

	def __onClose(self):
		AutoChannelsImporterTimer.instance = None

	def channelsimporterchannelsimporterdatedelay(self):
		self.channelsimporteractivityTimer.stop()
		self.channelsimporterdate()

	def getChannelsImporterTime(self):
		backupclock = config.plugins.ChannelsImporter.scheduletime.value
		nowt = time()
		now = localtime(nowt)
		if config.plugins.ChannelsImporter.scheduleRepeatInterval.value.isdigit(): # contains wait time in minutes
			repeatIntervalMinutes = int(config.plugins.ChannelsImporter.scheduleRepeatInterval.value)
			return int(mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min + repeatIntervalMinutes, 0, now.tm_wday, now.tm_yday, now.tm_isdst)))
		return int(mktime((now.tm_year, now.tm_mon, now.tm_mday, backupclock[0], backupclock[1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))

	def channelsimporterdate(self, atLeast=0):
		self.channelsimportertimer.stop()
		global ChannelsImporterTime
		ChannelsImporterTime = self.getChannelsImporterTime()
		now = int(time())
		if ChannelsImporterTime > 0:
			if ChannelsImporterTime < now + atLeast:
				if config.plugins.ChannelsImporter.scheduleRepeatInterval.value.isdigit(): # contains wait time in minutes
					ChannelsImporterTime = now + (60 * int(config.plugins.ChannelsImporter.scheduleRepeatInterval.value))
					while (int(ChannelsImporterTime) - 30) < now:
						ChannelsImporterTime += 60 * int(config.plugins.ChannelsImporter.scheduleRepeatInterval.value)
				elif config.plugins.ChannelsImporter.scheduleRepeatInterval.value == "daily":
					ChannelsImporterTime += 24 * 3600
					while (int(ChannelsImporterTime) - 30) < now:
						ChannelsImporterTime += 24 * 3600
				elif config.plugins.ChannelsImporter.scheduleRepeatInterval.value == "weekly":
					ChannelsImporterTime += 7 * 24 * 3600
					while (int(ChannelsImporterTime) - 30) < now:
						ChannelsImporterTime += 7 * 24 * 3600
				elif config.plugins.ChannelsImporter.scheduleRepeatInterval.value == "monthly":
					ChannelsImporterTime += 30 * 24 * 3600
					while (int(ChannelsImporterTime) - 30) < now:
						ChannelsImporterTime += 30 * 24 * 3600
			next = ChannelsImporterTime - now
			self.channelsimportertimer.startLongTimer(next)
		else:
			ChannelsImporterTime = -1
		print("[ChannelsImporterScheduler][channelsimporterdate] Time set to", strftime("%c", localtime(ChannelsImporterTime)), strftime("(now=%c)", localtime(now)))
		return ChannelsImporterTime

	def backupstop(self):
		self.channelsimportertimer.stop()

	def ChannelsImporteronTimer(self):
		self.channelsimportertimer.stop()
		now = int(time())
		wake = self.getChannelsImporterTime()
		# If we're close enough, we're okay...
		atLeast = 0
		if wake - now < 60:
			atLeast = 60
			print("[ChannelsImporterScheduler][ChannelsImporteronTimer] onTimer occured at", strftime("%c", localtime(now)))
			from Screens.Standby import inStandby
			if not inStandby:
				#message = _("Your channels list is about to be updated.\nDo you want to allow this?")
				#ybox = self.session.openWithCallback(self.doChannelsImporter, MessageBox, message, MessageBox.TYPE_YESNO, timeout = 30)
				#ybox.setTitle('Scheduled ChannelsImporter.')
				self.doChannelsImporter(True)
			else:
				self.doChannelsImporter(True)
		self.channelsimporterdate(atLeast)

	def doChannelsImporter(self, answer):
		now = int(time())
		if answer is False:
			if config.plugins.ChannelsImporter.retrycount.value < 2:
				print("[ChannelsImporterScheduler][doChannelsImporter] ChannelsImporter delayed.")
				repeat = config.plugins.ChannelsImporter.retrycount.value
				repeat += 1
				config.plugins.ChannelsImporter.retrycount.value = repeat
				ChannelsImporterTime = now + (int(config.plugins.ChannelsImporter.retry.value) * 60)
				print("[ChannelsImporterScheduler][doChannelsImporter] Time now set to", strftime("%c", localtime(ChannelsImporterTime)), strftime("(now=%c)", localtime(now)))
				self.channelsimportertimer.startLongTimer(int(config.plugins.ChannelsImporter.retry.value) * 60)
			else:
				atLeast = 60
				print("[ChannelsImporterScheduler][doChannelsImporter] Enough Retries, delaying till next schedule.", strftime("%c", localtime(now)))
				self.session.open(MessageBox, _("Enough Retries, delaying till next schedule."), MessageBox.TYPE_INFO, timeout=10)
				config.plugins.ChannelsImporter.retrycount.value = 0
				self.channelsimporterdate(atLeast)
		else:
			self.timer = eTimer()
			self.timer.callback.append(self.doautostartscan)
			print("[ChannelsImporterScheduler][doChannelsImporter] Running ChannelsImporter", strftime("%c", localtime(now)))
			self.timer.start(100, 1)

	def doautostartscan(self):
		self.session.open(ChannelsImporter)

	def doneConfiguring(self):
		now = int(time())
		if config.plugins.ChannelsImporter.enableSchedule.value:
			if autoChannelsImporterTimer is not None:
				print("[ChannelsImporterScheduler][doneConfiguring] Schedule Enabled at", strftime("%c", localtime(now)))
				autoChannelsImporterTimer.channelsimporterdate()
		else:
			if autoChannelsImporterTimer is not None:
				global ChannelsImporterTime
				ChannelsImporterTime = 0
				print("[ChannelsImporterScheduler][doneConfiguring] Schedule Disabled at", strftime("%c", localtime(now)))
				autoChannelsImporterTimer.backupstop()
		if ChannelsImporterTime > 0:
			t = localtime(ChannelsImporterTime)
			channelsimportertext = strftime(_("%a %e %b  %-H:%M"), t)
		else:
			channelsimportertext = ""

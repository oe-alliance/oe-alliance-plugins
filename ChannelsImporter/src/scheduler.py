from time import mktime, strftime, time, localtime
from Components.config import config
from enigma import eTimer

def autostart(session, **kwargs):
	configEnableSchedule = config.plugins.ChannelsImporter.enableSchedule
	configScheduleRepeatInterval = config.plugins.ChannelsImporter.scheduleRepeatInterval
	configScheduleClock = config.plugins.ChannelsImporter.scheduletime
	configImportOnRestart = config.plugins.ChannelsImporter.importOnRestart
	scheduler(session, configEnableSchedule, configScheduleRepeatInterval, configScheduleClock, configImportOnRestart) # start schedule at sessionstart
	
def taskToSchedule(session):
	# This is the task that is being scheduled
	from ChannelsImporter import ChannelsImporter
	session.open(ChannelsImporter)

class scheduler:
	def __init__(self, session, configEnableSchedule, configScheduleRepeatInterval, configScheduleClock = None, configImportOnRestart = None):
		self.session = session
		# configEnableSchedule is ConfigYesNo
		# configScheduleRepeatInterval is ConfigSelection containing a numeric string in minutes or "daily", "weeekly", or "monthly"
		# configScheduleClock is ConfigClock
		# configImportOnRestart is ConfigYesNo
		self.configEnableSchedule = configEnableSchedule
		self.configScheduleRepeatInterval = configScheduleRepeatInterval
		self.configScheduleClock = configScheduleClock
		self.configImportOnRestart = configImportOnRestart
		print "[ChannelsImporterScheduler][__init__] Starting..."
		self.timer = eTimer()
		self.timer.callback.append(self.doTask)
		self.justBooted = True
		self.configEnableSchedule.addNotifier(self.configChange, initial_call = False)
		self.configScheduleRepeatInterval.addNotifier(self.configChange, initial_call = False)
		if self.configScheduleClock:
			self.configScheduleClock.addNotifier(self.configChange, initial_call = False)
		self.timer.startLongTimer(0)
		
	def configChange(self, configElement = None):
		# config was changed in the plugin setup
		if self.timer.isActive():
			self.timer.stop()
		if self.configEnableSchedule.value:
			waitTime = self.getWaitTime()
			print "[ChannelsImporterScheduler][configChange] Setup values have changed. Next automatic import at ", strftime("%c", localtime(time() + waitTime))
			self.timer.startLongTimer(waitTime)
		else:
			print "[ChannelsImporterScheduler][configChange] Setup values have changed. Scheduler disabled."
			
	def doTask(self):
		if self.timer.isActive():
			self.timer.stop()
		if self.configEnableSchedule.value:
			if not self.justBooted or self.configImportOnRestart and self.configImportOnRestart.value:
				taskToSchedule(self.session)
			waitTime = self.getWaitTime()
			print "[ChannelsImporterScheduler][doTask] Next automatic import at", strftime("%c", localtime(time() + waitTime))
			self.timer.startLongTimer(waitTime)
		else:
			print "[ChannelsImporterScheduler][doTask] Scheduler disabled."
		self.justBooted = False
			
	def getWaitTime(self): # seconds
		if self.configScheduleRepeatInterval.value.isdigit():
			return 60 * int(self.configScheduleRepeatInterval.value)
		if int(time()) < 1483228800: # STB clock not correctly set. Check back in 12 hours.
			return 60 * 60 * 12
		intervals = {"daily": 60 * 60 * 24, "weekly": 60 * 60 * 24 * 7, "monthly": 60 * 60 * 24 * 30}
		clock = self.configScheduleClock.value
		curTime = time()
		now = localtime(curTime)
		next = int(mktime((now.tm_year, now.tm_mon, now.tm_mday, clock[0], clock[1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))
		while curTime > next:
			next += intervals[self.configScheduleRepeatInterval.value]
		return int(next - curTime)
		
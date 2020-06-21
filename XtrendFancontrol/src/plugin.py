from __future__ import print_function
#
# Fan Setup Plugin for et9x00, et8000 and et10000
# Coded by Dima73 (c) 2011
# Support: http://www.clarke-xtrend-support.com/
#
# Special thanks for help vlamo
# Support: http://dream.altmaster.net/
#
# v3.2: Added support for et8000 and et10000


# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Components.Harddisk import harddiskmanager
from Components.Pixmap import Pixmap, MultiPixmap
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSelection, getConfigListEntry, ConfigClock, ConfigYesNo, ConfigBoolean, ConfigText, ConfigSlider
from time import time as Time, localtime, strftime
from enigma import eTimer
import socket
from os import system as os_system
from enigma import eTimer
from Screens.MessageBox import MessageBox
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ
import os
import gettext
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from boxbranding import getImageDistro
import six

SIGN = '°' if six.PY3 else str('\xc2\xb0')

PLUGIN_VERSION = _(" ver. 3.2")

# all fan modes:
# 1 - always OFF
# 2 - always ON
# 3 - always AUTO (in wakeup mode - always ON, in standby mode: on idle - OFF, on rec and etc. - ON)
# 4 - on time set (startime:endtime) OFF
# 5 - on hdd sleeping set OFF
# 6 - on hdd temperature set ON
# 7 - on system temperature set ON
#
# configs:
# 1. Fan modes: OFF, ON, AUTO
# 2. Switch OFF mode on time setting: enable|disable
# 2.1. Start time: HH:MM
# 2.1. End time: HH:MM
# 3. Watch on HDD state: None|Sleeping|Temperature
# 3.1. Select internal HDD device: all|+mutable_hdd-device_list
# 3.2. Switch OFF mode on HDD sleep: enable|disable
# or
# 3.2. Switch ON mode on HDD max.temperature (0 - off): 0-80
# 3.2. Switch ON mode on System max.temperature: 15-80

modelist = {"off": _("Fan - Off"), "on": _("Fan - On"), "standby": _("Fan - Off in standby"), "auto": _("Fan - Auto")}
hddwatchlist = {"none": _("None"), "sleep": _("HDD Sleeping"), "temp": _("HDD Temperature")}
timsetlist = {"none": _("None"), "off": _("Fan - Off"), "on": _("Fan - On"), "auto": _("Fan - Auto")}
syswatchlist = {"off": _("Off"), "on": _("On")}

config.plugins.FanSetup = ConfigSubsection()
config.plugins.FanSetup.mode = ConfigSelection(choices = modelist, default = "auto")
config.plugins.FanSetup.timeset = ConfigSelection(choices = timsetlist, default = "none")
config.plugins.FanSetup.timestartoff = ConfigClock(default = ((21 * 60 + 30) * 60) )
config.plugins.FanSetup.timeendoff = ConfigClock(default = ((7 * 60 + 0) * 60) )
config.plugins.FanSetup.hddwatch = ConfigSelection(choices = hddwatchlist, default = "none")
config.plugins.FanSetup.hdddevice = ConfigText(default = "all")
config.plugins.FanSetup.hddsleep = ConfigBoolean(default = False)
config.plugins.FanSetup.hddtemp = ConfigInteger(0, limits = (0, 80))
config.plugins.FanSetup.menuhdd = ConfigYesNo(default = False)
config.plugins.FanSetup.fanspeed = ConfigSlider(default=127, increment=8, limits=(0, 255))
config.plugins.FanSetup.systemtemp = ConfigInteger(40, limits = (15, 80))
config.plugins.FanSetup.systempwatch = ConfigSelection(choices = syswatchlist, default = "off")


class FanSetupScreen(Screen, ConfigListScreen):
	global PLUGIN_VERSION
	skin = """
		<screen position="center,center" size="550,335" >
		<widget name="config" position="c-261,c-145" size="533,270" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="c-240,e-45" zPosition="0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/red.png" position="c-70,e-45" zPosition="0" size="140,40" alphatest="on" />
		<widget name="ok" position="c-240,e-45" size="140,40" valign="center" halign="center" zPosition="1" font="Regular;17" transparent="1" backgroundColor="green" />
		<widget name="cancel" position="c-70,e-45" size="140,40" valign="center" halign="center" zPosition="1" font="Regular;17" transparent="1" backgroundColor="red" />
		<ePixmap pixmap="skin_default/div-h.png" position="c-275,e-110" zPosition="1" size="550,2" />
		<ePixmap pixmap="skin_default/div-h.png" position="c-275,e-48" zPosition="1" size="550,2" />
		<widget name="powerstatus" position="c-259,e-105" size="160,20" font="Regular;19" zPosition="1" transparent="1" />
		<widget name="daemon0" alphatest="on" pixmap="skin_default/buttons/button_green_off.png" position="c-120,e-101" size="15,16" zPosition="10" transparent="1"/>
		<widget name="daemon1" alphatest="on" pixmap="skin_default/buttons/button_green.png" position="c-120,e-101" size="15,16" zPosition="10" transparent="1"/>
		<ePixmap alphatest="on" pixmap="skin_default/icons/clock.png" position="c+174,e-105" size="14,14" zPosition="1" />
		<widget font="Regular;18" halign="left" position="c+194,e-105" render="Label" size="55,20" source="global.CurrentTime" transparent="1" valign="center" zPosition="1">
		<convert type="ClockToText">Default</convert>
		</widget>
		<widget font="Regular;15" halign="left" position="c+248,e-106" render="Label" size="27,17" source="global.CurrentTime" transparent="1" valign="center" zPosition="1">
		<convert type="ClockToText">Format::%S</convert>
		</widget>
		<widget name="sysTemp" position="c-259,e-75" size="260,20" font="Regular;19" halign="left" zPosition="1" transparent="1" />
		<widget name="hddTemp" position="c+0,e-75" size="260,20" font="Regular;19" halign="right" zPosition="1" transparent="1" />
	</screen>
	"""
	def __init__(self, session, args = None):
		self.skin = FanSetupScreen.skin
		self.setup_title = _("Fan setup:") + PLUGIN_VERSION
		self.timer = eTimer()
		self.timer.callback.append(self.getCurrentMode)
		self.timer.start(50, True)
		self.temptimer = eTimer()
		self.temptimer.callback.append(self.updateTemps)
		self.fanspeedcontrol = self.fanSpeedControllable()
		self.systemtempsensor = self.hasSystemTempSensor()
		Screen.__init__(self, session)

		self["powerstatus"] = Label(_("Power status"))
		self["sysTemp"] = Label(_("System temperature"))
		self["hddTemp"] = Label(_("Harddisk temperature"))
		self["ok"] = Button(_("Save"))
		self["cancel"] = Button(_("Cancel"))
		self["daemon0"] = Pixmap()
		self["daemon0"].hide()
		self["daemon1"] = Pixmap()
		self["daemon1"].hide()

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyGreen,
			"cancel": self.keyRed,
		}, -2)

		ConfigListScreen.__init__(self, [])

		self.initConfig()
		self.createSetup()

		self.onClose.append(self.__closed)
		self.onLayoutFinish.append(self.__layoutFinished)

	def __closed(self):
		self.temptimer.stop()

	def __layoutFinished(self):
		self.setTitle(self.setup_title)
		self.temptimer.start(100, True)

	def fanSpeedControllable(self):
		try:
			fd = open('/proc/stb/fp/fan_pwm', 'r')
			pwm = fd.read().strip()
			fd.close()
			return True
		except:
			return False

	def hasSystemTempSensor(self):
		try:
			if os.path.exists("/proc/stb/sensors/temp/value"):
				fd = open('/proc/stb/sensors/temp/value', 'r')
				temp = int(fd.read().strip(), 0)
				fd.close()
			else:
				fd = open('/proc/stb/fp/temp_sensor', 'r')
				temp = fd.read().strip()
				fd.close()
			return True
		except:
			return False

	def updateTemps(self):
		if self.systemtempsensor:
			self["sysTemp"].setText(_("System temperature") + " " + str(getSysTemp()) + SIGN + ' C')
		else:
			self["sysTemp"].setText(_("System temperature") + " " + _("n.a."))

		disk, hddTemp = getHddTemp()
		if hddTemp is None:
			self["hddTemp"].setText(_("Harddisk temperature") + " " + _("n.a."))
		else:
			self["hddTemp"].setText(_("Harddisk temperature") + " " + str(hddTemp) + SIGN + ' C')

		self.temptimer.start(60000, True)

	def getCurrentMode(self):
		power = None
		try:
			fd = open('/proc/stb/fp/fan', 'r')
			power = fd.read().strip()
			fd.close()
		except:
			pass
		self.curmode = power
		if self.curmode != None:
			if self.curmode == "off":
				self["daemon1"].hide()
				self["daemon0"].show()
			else:
				self["daemon0"].hide()
				self["daemon1"].show()
		self.timer.start(1000, True)

	def getHddList(self):
		hddlist = { }
		for hdd in harddiskmanager.HDDList():
			if "pci" in hdd[1].phys_path or "ahci" in hdd[1].phys_path:
				devdir = hdd[1].getDeviceDir()
				name = hdd[1].model()
				if name in ("", "-?-"):
					name = devdir
				hddlist[devdir] = name
		return hddlist

	def initConfig(self):
		def getPrevValues(section):
			res = { }
			for (key, val) in section.content.items.items():
				if isinstance(val, ConfigSubsection):
					res[key] = getPrevValues(val)
				else:
					res[key] = val.value
			return res

		self.FAN = config.plugins.FanSetup
		self.prev_values      = getPrevValues(self.FAN)
		self.cfg_mode         = getConfigListEntry(_("Fan mode"), self.FAN.mode)
		self.cfg_timeset      = getConfigListEntry(_("Switch Fan mode on time setting"), self.FAN.timeset)
		self.cfg_hddwatch     = getConfigListEntry(_("Watch HDD state"), self.FAN.hddwatch)
		self.cfg_systempwatch = getConfigListEntry(_("Watch system temp"), self.FAN.systempwatch)

		# select internal hdd-drive
		hddlist = self.getHddList()
		hddlist["all"] = _("All")
		default = self.FAN.hdddevice.value not in hddlist and "all" or self.FAN.hdddevice.value
		self.hddlistsel = ConfigSelection(choices = hddlist, default = default)
		self.cfg_hdddevice= getConfigListEntry(_("Select internal HDD device"), self.hddlistsel)
		self.prev_hdddevice = self.FAN.hdddevice.value

	def createSetup(self):
		list = [ self.cfg_mode ]
		if self.FAN.mode.value !="off":
			list.append(self.cfg_timeset)
			if self.FAN.timeset.value != "none":
					list.append(getConfigListEntry(_("Start time"), self.FAN.timestartoff))
					list.append(getConfigListEntry(_("End time"), self.FAN.timeendoff))
		if self.FAN.mode.value =="off":
			list.append(self.cfg_hddwatch)
			if self.FAN.hddwatch.value != "none":
				list.append(self.cfg_hdddevice)
				if self.FAN.hddwatch.value == "temp":
					list.append(getConfigListEntry(_("Switch ON mode on HDD max.temp. (0 - disable)"), self.FAN.hddtemp))
				elif self.FAN.hddwatch.value == "sleep":
					list.append(getConfigListEntry(_("Switch OFF mode on HDD sleep"), self.FAN.hddsleep))
		list.append(getConfigListEntry(_("Show temp. HDD to extensions menu"), self.FAN.menuhdd))
		if self.fanspeedcontrol:
				list.append(getConfigListEntry(_("Initial fan speed") + "               ", self.FAN.fanspeed))
		if self.systemtempsensor:
			list.append(self.cfg_systempwatch)
			if self.FAN.systempwatch.value == "on":
				list.append(getConfigListEntry(_("Switch ON on system temp"), self.FAN.systemtemp))
		self["config"].list = list
		self["config"].l.setList(list)

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur in (self.cfg_mode, self.cfg_timeset, self.cfg_hddwatch, self.cfg_systempwatch):
			self.createSetup()
		elif cur in (self.cfg_hdddevice):
			self.FAN.hdddevice.value = self.hddlistsel.value

	def keyOk(self):
		pass

	def keyRed(self):
		def setPrevValues(section, values):
			for (key, val) in section.content.items.items():
				value = values.get(key, None)
				if value is not None:
					if isinstance(val, ConfigSubsection):
						setPrevValues(val, value)
					else:
						val.value = value

		setPrevValues(self.FAN, self.prev_values)
		self.keyGreen()

	def keyGreen(self):
		timehddsleep = config.usage.hdd_standby.value
		timeset = config.plugins.FanSetup.timeset.value
		mode = config.plugins.FanSetup.mode.value
		if mode == timeset:
			self.FAN.timeset.value = "none"
		if mode == "off":
			self.FAN.timeset.value = "none"
		if mode != "off":
			self.FAN.hddwatch.value = "none"
			self.FAN.hddsleep.value = False
			self.FAN.hddtemp.value = 0
		if mode == "off" and self.FAN.hddwatch.value != "none":
			removable = False
			file_removable = '/sys/block/sda/removable'
			if os.path.exists(file_removable) :
				fd = open(file_removable, 'r')
				removable = fd.read()
				fd.close()
				removable = removable.strip()
			if removable == '0':
				print("removable state for device HDD")
			else:
				self.session.open(MessageBox, _("You may not use this mode!\nNot found an internal hard drive!"), MessageBox.TYPE_INFO, timeout = 5)
				self.FAN.hddwatch.value = "none"
				return
		if self.FAN.timeset.value != "none" and self.FAN.timestartoff.value == self.FAN.timeendoff.value:
			# show warning message and return
			self.session.open(MessageBox, _("Start time OFF mode equal End time OFF mode\nYou may not use this time settings!"), MessageBox.TYPE_INFO, timeout = 5)
			self.FAN.timeset.value = "none"
			return
			# or just set it to False and continue
		if self.FAN.hddwatch.value == "sleep" and self.FAN.hddsleep.value is True and timehddsleep == "0":
			# show warning message and return
			self.session.open(MessageBox, _("Harddisk standby after - no standby\nYou may not use this mode!"), MessageBox.TYPE_INFO, timeout = 5)
			self.FAN.hddsleep.value = False
			return
			# or just set it to False and continue
			#self.FAN.hddsleep.value = False
		self.FAN.save()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()


class FanManager:
	def __init__(self):
		self.polltime = 120
		self.timer = eTimer()
		self.timer.callback.append(self.timerPoll)
		config.plugins.FanSetup.mode.addNotifier(self.fanModeChanged)
		config.plugins.FanSetup.fanspeed.addNotifier(self.fanModeChanged)

	def fanModeChanged(self, cfgElem):
		self.timer.start(0, True)

	def timerPoll(self):
		timeout = self.polltime
		FanConf = config.plugins.FanSetup
		mode = FanConf.mode.value
		timeset = FanConf.timeset.value

		# check time settings and if need change fan mode
		if mode != "off" and timeset != "none":
			ts = localtime()
			nowsec = (ts.tm_hour * 3600) + (ts.tm_min * 60)
			offlist= config.plugins.FanSetup.timestartoff.value
			offsec = (offlist[0] * 3600) + (offlist[1] * 60)
			onlist = config.plugins.FanSetup.timeendoff.value
			onsec = (onlist[0] * 3600) + (onlist[1] * 60)
			invert = False
			if offsec > onsec:
				invert = True
				offsec, onsec = onsec, offsec
			if (offsec <= nowsec < onsec):
				if not invert:
					mode = timeset
				timeout = min(self.polltime, onsec - nowsec)
			elif nowsec < offsec:
				if invert:
					mode = timeset
				timeout = min(self.polltime, offsec - nowsec)
			else:
				if invert:
					mode = timeset
				timeout = min(self.polltime, 86400 - nowsec)

		# check hdd settings (sleeping and temperature hdd's)
		if FanConf.hddwatch.value != "none" and mode == "off":
			hddcount = harddiskmanager.HDDCount()
			if hddcount:
				if FanConf.hddwatch.value == "sleep" and FanConf.hddsleep.value is True:
					sleepcount = 0
					hddlist = harddiskmanager.HDDList()
					for x in list(range(hddcount)):
						if hddlist[x][1].isSleeping():
							sleepcount += 1
						else:
							mode = "on"
					if sleepcount == hddcount:
						mode = "off"
				elif FanConf.hddwatch.value == "temp" and FanConf.hddtemp.value != 0:
					hddlist = harddiskmanager.HDDList()
					for hdd in hddlist:
						if not hdd[1].isSleeping():
							disk, hddtemp = getTempForDevice(hdd[1].getDeviceDir())
							if hddtemp >= FanConf.hddtemp.value:
								mode = "on"
							else:
								mode = "off"
						else:
							mode = "off"

		speed = FanConf.fanspeed.value
		if FanConf.systempwatch.value == "on":
			temp = getSysTemp()
			if temp is not None:
				if temp >= FanConf.systemtemp.value:
					mode = "on"
					# adjust speed: 
					# - use initial speed when current sys temp > user specified value
					# - increase speed til max. Max is reached when current sys temp = 2 * user specified value
					speed = min(FanConf.fanspeed.value + (255 - FanConf.fanspeed.value) * ((temp / FanConf.systemtemp.value) - 1), 255)

		if mode == "standby":
			from Screens.Standby import inStandby
			if inStandby:
				self.applySettings("off", 0)
			else:
				self.applySettings("on", speed)
		else:
			self.applySettings(mode, speed)
		self.timer.start(timeout * 1000, True)

	def applySettings(self, mode, speed):
		try:
			file = open("/proc/stb/fp/fan", "w")
			file.write('%s' % mode)
			file.close()
		except:
			pass
		try:
			file = open("/proc/stb/fp/fan_pwm", "w")
			file.write(hex(speed)[2:])
			file.close()
		except:
			pass

def getSysTemp():
	try:
		if os.path.exists("/proc/stb/sensors/temp/value"):
			fd = open('/proc/stb/sensors/temp/value', 'r')
			temp = int(fd.read().strip(), 0)
			fd.close()
		else:
			fd = open('/proc/stb/fp/temp_sensor', 'r')
			temp = int(fd.read().strip(), 0)
			fd.close()
		return temp
	except:
		return None

def getTempForDevice(device):
	try:
		os.system('/usr/sbin/hddtemp -q %s > /tmp/hdd.temperature' % device)
		f = open('/tmp/hdd.temperature', 'r')
		temperature = f.readline()
		f.close()
		if temperature.find("No such file or directory") != -1:
			return None, None
		pos1 = temperature.rfind(':')
		pos2 = temperature.rfind('C')
		if pos1 != -1 and pos2 != -1 and pos1 < pos2:
			temp = int(temperature[pos1+1:pos2])
			disk = temperature[1:pos1].replace('\x10\x80', '').strip()
			return disk, temp
	except:
		pass
	return None, None

def getHddTemp():
	if os.path.exists("/usr/sbin/hddtemp"):
		internal_hddlist = []
		for hdd in harddiskmanager.HDDList():
			if "pci" in hdd[1].phys_path or "ahci" in hdd[1].phys_path:
				internal_hddlist.append(hdd[1].getDeviceDir())

		if config.plugins.FanSetup.hdddevice.value == "all":
			for dev in internal_hddlist:
				disk, temp = getTempForDevice(dev)
				if disk and temp:
					return disk, temp
			return None, None
		else:
			disk, temp = getTempForDevice(config.plugins.FanSetup.hdddevice.value)
			if disk and temp:
				return disk, temp
			else:
				return None, None
	return None, None

def selSetup(menuid, **kwargs):
	if getImageDistro() in ("openatv"):
		if menuid != "extended":
			return [ ]
	else:
		if menuid != "system":
			return [ ]
	return [(_("Fan Control"), main, "fansetup_config", 70)]

def show_temp(session, **kwargs):
	sysTemp = getSysTemp()
	disk, hddTemp = getHddTemp()
	message = _("Harddisks:")
	if hddTemp is None:
		message += "\n" + _("No harddisk with temperature sensor found!")
	else:
		message += "\n" + disk + ": " + str(hddTemp) + SIGN + ' C'

	if sysTemp is None:
		message += "\n" + _("No system temperature sensor found!")
	else:
		message += "\n\n" + _("System temperature") + " " + str(sysTemp) + SIGN + ' C'
	session.open(MessageBox, message, type=MessageBox.TYPE_INFO)

def main(session, **kwargs):
	session.open(FanSetupScreen)

def startup(reason, **kwargs):
	fanmanager = FanManager()

def Plugins(**kwargs):
	from os import path
	if path.exists("/proc/stb/fp/fan"):
		from Plugins.Plugin import PluginDescriptor
		if config.plugins.FanSetup.menuhdd.value is True:
			return [PluginDescriptor(name=_("Fan Control"), description=_("switch Fan On/Off"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=selSetup),
					PluginDescriptor(name=_("Fan Setup"), description = "", where = PluginDescriptor.WHERE_SESSIONSTART, fnc = startup),
					PluginDescriptor(name=_("Show Temp"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc = show_temp)]
		else:
			return [PluginDescriptor(name=_("Fan Control"), description=_("switch Fan On/Off"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=selSetup),
					PluginDescriptor(name=_("Fan Setup"), description = "", where = PluginDescriptor.WHERE_SESSIONSTART, fnc = startup)]
	return []

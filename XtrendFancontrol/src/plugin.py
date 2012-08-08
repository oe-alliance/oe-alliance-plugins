#
# Fan Setup Plugin for et9x00
# Coded by Dima73 (c) 2011
# Support: http://www.clarke-xtrend-support.com/
#
# Special thanks for help vlamo
# Support: http://dream.altmaster.net/
#

# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Components.Harddisk import harddiskmanager
from Components.Pixmap import Pixmap, MultiPixmap
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSelection, getConfigListEntry, ConfigClock, ConfigYesNo, ConfigBoolean, ConfigText
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

PLUGIN_VERSION = _(" ver. 3.1")

# all fan modes:
# 1 - always OFF
# 2 - always ON
# 3 - always AUTO (in wakeup mode - always ON, in standby mode: on idle - OFF, on rec and etc. - ON)
# 4 - on time set (startime:endtime) OFF
# 5 - on hdd sleeping set OFF
# 6 - on hdd temperature set ON
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

modelist = {"off": _("Fan - Off"), "on": _("Fan - On"), "auto": _("Fan - Auto")}
hddwatchlist = {"none": _("None"), "sleep": _("HDD Sleeping"), "temp": _("HDD Temperature")}
timsetlist = {"none": _("None"), "off": _("Fan - Off"), "on": _("Fan - On"), "auto": _("Fan - Auto")}

config.plugins.FanSetup = ConfigSubsection()
config.plugins.FanSetup.mode = ConfigSelection(choices = modelist, default = "off")
config.plugins.FanSetup.timeset = ConfigSelection(choices = timsetlist, default = "none")
config.plugins.FanSetup.timestartoff = ConfigClock(default = ((21 * 60 + 30) * 60) )
config.plugins.FanSetup.timeendoff = ConfigClock(default = ((7 * 60 + 0) * 60) )
config.plugins.FanSetup.hddwatch = ConfigSelection(choices = hddwatchlist, default = "none")
config.plugins.FanSetup.hdddevice = ConfigText(default = "all")
config.plugins.FanSetup.hddsleep = ConfigBoolean(default = False)
config.plugins.FanSetup.hddtemp = ConfigInteger(0, limits = (0,80))
config.plugins.FanSetup.menuhdd = ConfigYesNo(default = False)

from HddTempWatcher import HddTempWatcher
tempwatcher = None


class FanSetupScreen(Screen, ConfigListScreen):
	global PLUGIN_VERSION
	skin = """
		<screen position="center,center" size="550,220" >
		<widget name="config" position="c-261,c-105" size="533,190" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="c-240,e-45" zPosition="0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/red.png" position="c-70,e-45" zPosition="0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="c+100,e-45" zPosition="0" size="140,40" alphatest="on" />
		<widget name="hddtemp" position="c+100,e-45" size="140,40" valign="center" halign="center" zPosition="1" font="Regular;17" transparent="1" backgroundColor="blue" />
		<widget name="ok" position="c-240,e-45" size="140,40" valign="center" halign="center" zPosition="1" font="Regular;17" transparent="1" backgroundColor="green" />
		<widget name="cancel" position="c-70,e-45" size="140,40" valign="center" halign="center" zPosition="1" font="Regular;17" transparent="1" backgroundColor="red" />
		<ePixmap pixmap="skin_default/div-h.png" position="c-275,e-80" zPosition="1" size="550,2" />
		<ePixmap pixmap="skin_default/div-h.png" position="c-275,e-48" zPosition="1" size="550,2" />
		<widget name="powerstatus" position="c-261,e-71" size="180,20" font="Regular;19" zPosition="1" transparent="1" />
		<widget name="daemon0" alphatest="on" pixmap="skin_default/buttons/button_green_off.png" position="c-93,e-70" size="15,16" zPosition="10" transparent="1"/>
		<widget name="daemon1" alphatest="on" pixmap="skin_default/buttons/button_green.png" position="c-93,e-70" size="15,16" zPosition="10" transparent="1"/>
		<ePixmap alphatest="on" pixmap="skin_default/icons/clock.png" position="c+174,e-74" size="14,14" zPosition="1" />
		<widget font="Regular;18" halign="left" position="c+194,e-71" render="Label" size="55,20" source="global.CurrentTime" transparent="1" valign="center" zPosition="1">
		<convert type="ClockToText">Default</convert>
		</widget>
		<widget font="Regular;15" halign="left" position="c+248,e-74" render="Label" size="27,17" source="global.CurrentTime" transparent="1" valign="center" zPosition="1">
		<convert type="ClockToText">Format::%S</convert>
		</widget>
	</screen>
	"""
	def __init__(self, session, args = None):
		self.skin = FanSetupScreen.skin
		self.setup_title = _("Fan setup:") + PLUGIN_VERSION
		self.timer = eTimer()
		self.timer.callback.append(self.getCurrentMode)
		self.timer.start(50, True)
		Screen.__init__(self, session)


		self["powerstatus"] = Label(_("Power status"))
		self["ok"] = Button(_("Save"))
		self["cancel"] = Button(_("Cancel"))
		self["daemon0"] = Pixmap()
		self["daemon0"].hide()
		self["daemon1"] = Pixmap()
		self["daemon1"].hide()
		self["hddtemp"] = Button(_("Show temp.HDD"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyGreen,
			"cancel": self.keyRed,
			"blue": self.keyBlue,
		}, -2)

		ConfigListScreen.__init__(self, [])

		self.initConfig()
		self.createSetup()

		self.onClose.append(self.__closed)
		self.onLayoutFinish.append(self.__layoutFinished)

	def __closed(self):
		pass

	def __layoutFinished(self):
		self.setTitle(self.setup_title)

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
			if "pci" in hdd[1].phys_path:
				devdir = hdd[1].getDeviceDir()
				name = hdd[1].model()
				if name in ("", "-?-"):
					name = devdir
				hddlist[devdir] = name
		return hddlist

	def initConfig(self):
		def getPrevValues(section):
			res = { }
			for (key,val) in section.content.items.items():
				if isinstance(val, ConfigSubsection):
					res[key] = getPrevValues(val)
				else:
					res[key] = val.value
			return res

		self.FAN = config.plugins.FanSetup
		self.prev_values  = getPrevValues(self.FAN)
		self.cfg_mode     = getConfigListEntry(_("Fan mode"), self.FAN.mode)
		self.cfg_timeset  = getConfigListEntry(_("Switch Fan mode on time setting"), self.FAN.timeset)
		self.cfg_hddwatch = getConfigListEntry(_("Watch HDD state"), self.FAN.hddwatch)

		# select internal hdd-drive
		hddlist = self.getHddList()
		hddlist["all"] = _("All")
		default = not hddlist.has_key(self.FAN.hdddevice.value) and "all" or self.FAN.hdddevice.value
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
		self["config"].list = list
		self["config"].l.setList(list)

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur in (self.cfg_mode, self.cfg_timeset, self.cfg_hddwatch):
			self.createSetup()
		elif cur in (self.cfg_hdddevice):
			self.FAN.hdddevice.value = self.hddlistsel.value

	def keyOk(self):
		pass

	def keyRed(self):
		def setPrevValues(section, values):
			for (key,val) in section.content.items.items():
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
				print "removable state for device HDD"
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
		if self.prev_hdddevice != self.FAN.hdddevice.value and self.FAN.hddwatch.value == "temp" and tempwatcher:
			tempwatcher.reloadHddTemp(devices = self.FAN.hdddevice.value)
		self.FAN.save()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def keyBlue(self):
		message, type = getHDDTempInfo()
		self.session.open(MessageBox, message, type=type, timeout = 5)



class FanManager:
	def __init__(self):
		self.polltime = 120
		self.timer = eTimer()
		self.timer.callback.append(self.timerPoll)
		config.plugins.FanSetup.mode.addNotifier(self.fanModeChanged)

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
					for x in range (hddcount):
						if hddlist[x][1].isSleeping():
							sleepcount += 1
						else:
							mode = "on"
					if sleepcount == hddcount:
						mode = "off"
				elif FanConf.hddwatch.value == "temp" and FanConf.hddtemp.value != 0:
					hddlist = harddiskmanager.HDDList()
					if not hddlist[0][1].isSleeping():
						hddlist = tempwatcher.getHddTempList()
						for d in hddlist:
							hddtemp = hddlist[d]["temp"]
							if hddtemp >= FanConf.hddtemp.value:
								mode = "on"
							else:
								mode = "off"
					else:
						mode = "off"
		self.applySettings(mode)
		self.timer.start(timeout * 1000, True)

	def applySettings(self, mode):
		try:
			file = open("/proc/stb/fp/fan", "w")
			file.write('%s' % mode)
			file.close()
		except:
			pass


def getHDDTempInfo():
	if not os.path.exists("/usr/sbin/hddtemp"):
		return _("hddtemp not installed!"), MessageBox.TYPE_ERROR
	if tempwatcher is None:
		return _("HddTempWatcher not running!"), MessageBox.TYPE_ERROR

	inernal_hddlist = []
	for hdd in harddiskmanager.HDDList():
		if "pci" in hdd[1].phys_path:
			inernal_hddlist.append(hdd[1].getDeviceDir())

	message = _(" ")
	hddlist = tempwatcher.getHddTempList()
	for d in hddlist:
		if d in inernal_hddlist:
			message += "%s %s\n" % (hddlist[d]["path"], hddlist[d]["name"])
			if hddlist[d]["temp"] == -253:
				message += _("Drive is sleeping\n")
			elif hddlist[d]["temp"] == -254:
				message += _("ERROR\n")
			else:
				message += _("temp : ") + "%s %s\n" % (hddlist[d]["temp"], hddlist[d]["unit"])
	if message == "":
		message = _("Not found an internal HDD !")
	else:
		message = _("Found internal HDD !\n") + message
	return message, MessageBox.TYPE_INFO

def selSetup(menuid, **kwargs):
	if menuid != "system":
		return [ ]
	return [(_("Fan Control"), main, "fansetup_config", 70)]

def show_temp(session, **kwargs):
	message, type = getHDDTempInfo()
	session.open(MessageBox, message, type=type)

def main(session, **kwargs):
	session.open(FanSetupScreen)

def startup(reason, **kwargs):
	global tempwatcher
	tempwatcher = HddTempWatcher(devices = config.plugins.FanSetup.hdddevice.value)
	fanmanager = FanManager()

def Plugins(**kwargs):
	from os import path
	if path.exists("/proc/stb/fp/fan"):
		from Plugins.Plugin import PluginDescriptor
		if config.plugins.FanSetup.menuhdd.value is True:
			return [PluginDescriptor(name=_("Fan Control"), description=_("switch Fan On/Off"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=selSetup),
					PluginDescriptor(name=_("Fan Setup"), description = "", where = PluginDescriptor.WHERE_SESSIONSTART, fnc = startup),
					PluginDescriptor(name=_("Show HDDTemp"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc = show_temp)]
		else:
			return [PluginDescriptor(name=_("Fan Control"), description=_("switch Fan On/Off"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=selSetup),
					PluginDescriptor(name=_("Fan Setup"), description = "", where = PluginDescriptor.WHERE_SESSIONSTART, fnc = startup)]
	return []
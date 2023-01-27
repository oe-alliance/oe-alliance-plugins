# Copyright (C) 2023 jbleyel
#
# OAWeather is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# dogtag is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OAWeather.  If not, see <http://www.gnu.org/licenses/>.

# Some parts are taken from MetrixHD skin.

from os import remove
from os.path import isfile, getmtime
from pickle import dump, load
from time import time
from enigma import eTimer

from twisted.internet.reactor import callInThread

from Components.ActionMap import HelpableActionMap
from Components.config import config
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.Setup import Setup
from Screens.MessageBox import MessageBox
from Tools.Weatherinfo import Weatherinfo
from . import _

from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigSelection, ConfigSelectionNumber, ConfigText, ConfigNumber, NoSave

from Plugins.Plugin import PluginDescriptor
from Tools.Directories import SCOPE_CONFIG, resolveFilename
from Tools.Weatherinfo import Weatherinfo


#############################################################
config.plugins.OAWeather = ConfigSubsection()
config.plugins.OAWeather.enabled = ConfigYesNo(default=True)
config.plugins.OAWeather.nighticons = ConfigYesNo(default=True)
config.plugins.OAWeather.cachedata = ConfigSelection(default="60", choices=[("0", _("Disabled"))] + [(str(x), _("%d Minutes") % x) for x in (30, 60, 120)])
config.plugins.OAWeather.refreshInterval = ConfigSelectionNumber(0, 1440, 30, default=120, wraparound=True)
config.plugins.OAWeather.apikey = ConfigText(default="")
GEODATA = ("Hamburg, DE", "10.000654,53.550341")
config.plugins.OAWeather.weathercity = ConfigText(default=GEODATA[0], visible_width=250, fixed_size=False)
config.plugins.OAWeather.owm_geocode = ConfigText(default=GEODATA[1])
config.plugins.OAWeather.tempUnit = ConfigSelection(default="Celsius", choices=[("Celsius", _("Celsius")), ("Fahrenheit", _("Fahrenheit"))])
config.plugins.OAWeather.weatherservice = ConfigSelection(default="MSN", choices=[("MSN", _("MSN weather")), ("OpenMeteo", _("Open-Meteo Wetter")), ("openweather", _("OpenWeatherMap"))])
config.plugins.OAWeather.debug = ConfigYesNo(default=False)


#######################################################################

MODULE_NAME = "OAWeather"

CACHEFILE = resolveFilename(SCOPE_CONFIG, "OAWeather.dat")


class WeatherSettingsView(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "WeatherSettings", plugin="Extensions/OAWeather", PluginLanguageDomain="OAWeather")
		self["key_blue"] = StaticText(_("Location Selection"))
		self["key_yellow"] = StaticText(_("Defaults"))
		self["blueActions"] = HelpableActionMap(self, ["ColorActions"], {
			"blue": (self.keycheckCity, _("Search for your City")),
			"yellow": (self.defaults, _("Set default values"))
		}, prio=0, description=_("Weather Settings Actions"))
		self.old_weatherservice = config.plugins.OAWeather.weatherservice.value
		self.citylist = []
		self.checkcity = False
		self.closeonsave = False

	def keycheckCity(self, closesave=False):
		weathercity = config.plugins.OAWeather.weathercity.value.split(",")[0]
		self["footnote"].setText(_("Search for City ID please wait..."))
		self.closeonsave = closesave
		callInThread(self.searchCity, weathercity)

	def searchCity(self, weathercity):
		services = {"MSN": "msn", "OpenMeteo": "omw", "openweather": "owm"}
		service = services.get(config.plugins.OAWeather.weatherservice.value, "msn")
		apikey = config.plugins.OAWeather.apikey.value
		if service == "owm" and len(apikey) < 32:
			self.session.open(MessageBox, text=_("The API key for OpenWeatherMap is not defined or invalid.\nPlease verify your input data.\nOtherwise your settings won't be saved."), type=MessageBox.TYPE_WARNING)
		else:
			WI = Weatherinfo(service, config.plugins.OAWeather.apikey.value)
			if WI.error:
				print("[WeatherSettingsView] Error in module 'searchCity': %s" % WI.error)
				self["footnote"].setText(_("Error in Weatherinfo"))
				self.session.open(MessageBox, text=WI.error, type=MessageBox.TYPE_ERROR)
			else:
				geodatalist = WI.getCitylist(weathercity, config.osd.language.value.replace('_', '-').lower())
				if WI.error or geodatalist is None or len(geodatalist) == 0:
					print("[WeatherSettingsView] Error in module 'searchCity': %s" % WI.error)
					self["footnote"].setText(_("Error getting City ID"))
					self.session.open(MessageBox, text=_("City '%s' not found! Please try another wording." % weathercity), type=MessageBox.TYPE_WARNING)
#				elif len(geodatalist) == 1:
#					self["footnote"].setText(_("Getting City ID Success"))
#					self.saveGeoCode(geodatalist[0])
				else:
					self.citylist = []
					for item in geodatalist:
						lon = " [lon=%s" % item[1] if float(item[1]) != 0.0 else ""
						lat = ", lat=%s]" % item[2] if float(item[2]) != 0.0 else ""
						try:
							self.citylist.append(("%s%s%s" % (item[0], lon, lat), item[0], item[1], item[2]))
						except Exception:
							print("[WeatherSettingsView] Error in module 'showMenu': faulty entry in resultlist.")
					self.session.openWithCallback(self.choiceIdxCallback, ChoiceBox, titlebartext=_("Select Your Location"), title="", list=tuple(self.citylist))

	def choiceIdxCallback(self, answer):
		if answer is not None:
			self["footnote"].setText(answer[1])
			self.saveGeoCode((answer[1].split(",")[0], answer[2], answer[3]))

	def saveGeoCode(self, value):
		config.plugins.OAWeather.weathercity.value = value[0]
		config.plugins.OAWeather.owm_geocode.value = "%s,%s" % (float(value[1]), float(value[2]))
		self.old_weatherservice = config.plugins.OAWeather.weatherservice.value
		self.checkcity = False
		if self.closeonsave:
			weatherhandler.reset()
			Setup.keySave(self)

	def keySelect(self):
		if self.getCurrentItem() == config.plugins.OAWeather.weathercity:
			self.checkcity = True
		Setup.keySelect(self)

	def keySave(self):
		weathercity = config.plugins.OAWeather.weathercity.value.split(",")[0]
		if len(weathercity) < 3:
			self["footnote"].setText(_("The city name is too short. More than 2 characters are needed for search."))
			return
		if self.checkcity or self.old_weatherservice != config.plugins.OAWeather.weatherservice.value:
			self.keycheckCity(True)
			return
		weatherhandler.reset()
		Setup.keySave(self)

	def defaults(self, SAVE=False):
		for x in self["config"].list:
			if len(x) > 1:
				self.setInputToDefault(x[1])
				if SAVE:
					x[1].save()
		if self.session:
			Setup.createSetup(self)

	def setInputToDefault(self, configItem):
		configItem.setValue(configItem.default)


class WeatherHandler():
	def __init__(self):
		self.enabledebug = config.plugins.OAWeather.debug.value
		modes = {"MSN": "msn", "openweather": "owm", "OpenMeteo": "omw"}
		mode = modes.get(config.plugins.OAWeather.weatherservice.value, "msn")
		self.WI = Weatherinfo(mode, config.plugins.OAWeather.apikey.value)
		self.geocode = config.plugins.OAWeather.owm_geocode.value.split(",")
		self.oldmode = mode
		self.weathercity = None
		self.trialcounter = 0
		self.currentWeatherDataValid = 3  # 0= green (data available), 1= yellow (still working), 2= red (no data available, wait on next refresh) 3=startup
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.refreshWeatherData)
		self.wetterdata = None
		self.onUpdate = []
		self.skydirs = {"N": _("North"), "NE": _("Northeast"), "E": _("East"), "SE": _("Southeast"), "S": _("South"), "SW": _("Southwest"), "W": _("West"), "NW": _("Northwest")}

	def sessionStart(self):
		self.debug("sessionStart")
		self.getCacheData()

	def writeData(self, data):
		self.debug("writeData")
		self.currentWeatherDataValid = 0
		self.wetterdata = data
		for callback in self.onUpdate:
			callback(data)

		seconds = int(config.plugins.OAWeather.refreshInterval.value * 60)
		self.refreshTimer.start(seconds * 1000, True)

	def getData(self):
		return self.wetterdata

	def getValid(self) -> int:
		return self.currentWeatherDataValid

	def getSkydirs(self) -> dict:
		return self.skydirs

	def getCacheData(self):
		cacheminutes = int(config.plugins.OAWeather.cachedata.value)
		if cacheminutes and isfile(CACHEFILE):
			timedelta = (time() - getmtime(CACHEFILE)) / 60
			if cacheminutes > timedelta:
				with open(CACHEFILE, "rb") as fd:
					cache_data = load(fd)
				self.writeData(cache_data)
				return

		self.refreshTimer.start(3000, True)

	def refreshWeatherData(self, entry=None):
		self.debug("refreshWeatherData")
		self.refreshTimer.stop()
		if config.misc.firstrun.value:  # don't refresh on firstrun try again after 10 seconds
			self.debug("firstrun")
			self.refreshTimer.start(10000, True)
			return
		if config.plugins.OAWeather.enabled.value:
			self.weathercity = config.plugins.OAWeather.weathercity.value
			geocode = config.plugins.OAWeather.owm_geocode.value.split(",")
			if geocode and len(geocode) == 2:
				geodata = (self.weathercity, geocode[0], geocode[1])  # tuple ("Cityname", longitude, latitude)
			else:
				geodata = None
			language = config.osd.language.value.replace("_", "-")
			unit = "imperial" if config.plugins.OAWeather.tempUnit.value == "Fahrenheit" else "metric"
			if geodata:
				self.WI.start(geodata=geodata, cityID=None, units=unit, scheme=language, reduced=True, callback=self.refreshWeatherDataCallback)
			else:
				print("[%s] error in OAWeather config" % (MODULE_NAME))
				self.currentWeatherDataValid = 2

	def refreshWeatherDataCallback(self, data, error):
		self.debug("refreshWeatherDataCallback")
		if error or data is None:
			self.trialcounter += 1
			if self.trialcounter < 2:
				print("[%s] lookup for city '%s' paused, try again in 10 secs..." % (MODULE_NAME, self.weathercity))
				self.currentWeatherDataValid = 1
				self.refreshTimer.start(10000, True)
			elif self.trialcounter > 5:
				print("[%s] lookup for city '%s' paused 1 h, to many errors..." % (MODULE_NAME, self.weathercity))
				self.currentWeatherDataValid = 2
				self.refreshTimer.start(3600000, True)
			else:
				print("[%s] lookup for city '%s' paused 5 mins, to many errors..." % (MODULE_NAME, self.weathercity))
				self.currentWeatherDataValid = 2
				self.refreshTimer.start(300000, True)
			return
		self.writeData(data)
		# TODO write cache only on close
		if config.plugins.OAWeather.cachedata.value != "0":
			with open(CACHEFILE, "wb") as fd:
				dump(data, fd, -1)

	def reset(self):
		self.refreshTimer.stop()
		if isfile(CACHEFILE):
			remove(CACHEFILE)
		self.refreshWeatherData()

	def debug(self, text: str):
		if self.enabledebug:
			print("[%s] WeatherHandler DEBUG %s" % (MODULE_NAME, text))


def main(session, **kwargs):
	session.open(WeatherSettingsView)


def sessionstart(session, **kwargs):
	from Components.Sources.OAWeather import OAWeather
	session.screen["OAWeather"] = OAWeather()
	weatherhandler.sessionStart()


def Plugins(**kwargs):
	pluginList = []
	pluginList.append(PluginDescriptor(name="OAWeather", where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart, needsRestart=False))
	pluginList.append(PluginDescriptor(name="OAWeather", description=_("Configuration tool for OAWeather"), icon="plugin.png", where=[PluginDescriptor.WHERE_PLUGINMENU], fnc=main))
	return pluginList


weatherhandler = WeatherHandler()

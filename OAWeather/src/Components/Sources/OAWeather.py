# Copyright (C) 2023 jbleyel, Mr.Servo
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

from datetime import datetime
from Components.config import config
from Components.Sources.Source import Source
from Plugins.Extensions.OAWeather.plugin import weatherhandler


class OAWeather(Source):

	YAHOOnightswitch = {
					"3": "47", "4": "47", "11": "45", "12": "45", "13": "46", "14": "46", "15": "46", "16": "46", "28": "27",
					"30": "29", "32": "31", "34": "33", "37": "47", "38": "47", "40": "45", "41": "46", "42": "46", "43": "46"
					}
	METEOnightswitch = {"1": "2", "3": "4", "B": "C", "H": "I", "J": "K"}

	def __init__(self):
		Source.__init__(self)
		self.enabledebug = config.plugins.OAWeather.debug.value
		weatherhandler.onUpdate.append(self.callbackUpdate)
		self.data = weatherhandler.getData() or {}
		self.valid = weatherhandler.getValid()
		self.skydirs = weatherhandler.getSkydirs()
		self.na = _("n/a")
		self.tempunit = self.data.get("tempunit", self.na)

	def debug(self, text: str):
		if self.enabledebug:
			print("[OAWeather] Source DEBUG %s" % text)

	def callbackUpdate(self, data):
		self.debug("callbackUpdate: %s" % str(data))
		self.data = data
		self.tempunit = self.data.get("tempunit", self.na)
		self.changed((self.CHANGED_ALL,))

	def getValid(self):
		return self.valid

	def getVal(self, key: str):
		return self.data.get(key, self.na) if self.data else self.na

	def getCurrentVal(self, key: str, default: str = _("n/a")):
		self.debug("getCurrentVal:%s" % key)
		value = default
		if self.data and "current" in self.data:
			current = self.data.get("current", {})
			if key in current:
				value = current.get(key, default)
				self.debug("current key val: %s" % value)
			else:
				self.debug("key not in current")
		else:
			self.debug("NO current in data")
		return value

	def getObservationTime(self):
		val = self.getCurrentVal("observationTime", "")
		return datetime.fromisoformat(val).strftime("%H:%M") if val else self.na

	def getSunrise(self):
		val = self.getCurrentVal("sunrise", "")
		return datetime.fromisoformat(val).strftime("%H:%M") if val else self.na

	def getSunset(self):
		val = self.getCurrentVal("sunset", "")
		return datetime.fromisoformat(val).strftime("%H:%M") if val else self.na

	def getIsNight(self):
		return self.getCurrentVal("isNight", "") != ""

	def getTemperature(self):
		return "%s %s" % (self.getCurrentVal("temp"), self.tempunit)

	def getFeeltemp(self):
		return "%s %s" % (self.getCurrentVal("feelsLike"), self.tempunit)

	def getHumidity(self):
		return "%s %s" % (self.getCurrentVal("humidity"), "%")

	def getWindSpeed(self):
		return "%s %s" % (self.getCurrentVal("windSpeed"), self.getVal("windunit"))

	def getWindDir(self):
		val = self.getCurrentVal("windDir")
		return ("%s °" % val) if val else self.na

	def getWindDirName(self):
		skydirection = self.getCurrentVal("windDirSign", "").split(" ")
		if skydirection:
			return self.skydirs[skydirection[1]] if skydirection[1] in self.skydirs else skydirection[1]
		else:
			return self.na

	def getWindDirShort(self):
		return self.getCurrentVal("windDirSign").split(" ")[1]

	def getMaxTemp(self, day: int):
		return "%s %s" % (self.getKeyforDay("maxTemp", day), self.tempunit)

	def getMinTemp(self, day: int):
		return "%s %s" % (self.getKeyforDay("minTemp", day), self.tempunit)

	def getMaxMinTemp(self, day: int):
		return "%s - %s" % (self.getMaxTemp(day), self.getMinTemp(day))

	def getYahooCode(self, day: int):
		iconcode = self.getKeyforDay("yahooCode", day, "")
		if day == 0 and config.plugins.OAWeather.nighticons.value and self.getIsNight() and iconcode in self.YAHOOnightswitch:
			iconcode = self.YAHOOnightswitch[iconcode]
		return iconcode

	def getMeteoCode(self, day: int):
		iconcode = self.getKeyforDay("meteoCode", day, "")
		if day == 0 and config.plugins.OAWeather.nighticons.value and self.getIsNight() and iconcode in self.METEOnightswitch:
			iconcode = self.METEOnightswitch[iconcode]
		return iconcode

	def getKeyforDay(self, key: str, day: int, default: str = _("n/a")):
		self.debug("getKeyforDay key:%s day:%s" % (key, day))
		if day == 0:
			return self.data.get("current", {}).get(key, default) if self.data else default
		else:
			day = day - 1
			forecast = self.data.get("forecast")
			if forecast and day in forecast:
				val = forecast.get(day).get(key, self.na)
				self.debug("getKeyforDay key:%s day:%s / val:%s" % (key, day, val))
				return val
			return default

	def destroy(self):
		weatherhandler.onUpdate.remove(self.callbackUpdate)
		Source.destroy(self)

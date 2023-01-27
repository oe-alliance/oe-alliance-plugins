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

# Some parts are taken from msnweathercomponent plugin for compatibility reasons.


from Components.Converter.Converter import Converter
from Components.config import config
from Components.Element import cached
from os.path import join, exists
from traceback import print_exc


class OAWeather(Converter, object):
	CURRENT = 0
	DAY1 = 1
	DAY2 = 2
	DAY3 = 3
	DAY4 = 4
	DAY5 = 5
	CITY = 6                    # Example: "Hamburg, Germany"
	TEMPERATURE_HIGH = 7        # Example: "9 °C"
	TEMPERATURE_LOW = 8         # Example: "6 °C"
	TEMPERATURE_TEXT = 9        # Example: "rain showers", HINT: OpenMeteo doesn't deliver descriptiontexts, therefore "N/A" comes up
	TEMPERATURE_CURRENT = 10    # Example: "8 °C"
	WEEKDAY = 11                # Example: "Friday"
	WEEKSHORTDAY = 12           # Example: "Fr"
	DATE = 13                   # Example: "2023-01-13"
	OBSERVATIONTIME = 14        # Example: "16:17"
	OBSERVATIONPOINT = 15       # is no longer supported by the weather services, is now identical with 'CITY'.
	FEELSLIKE = 16              # Example: "4 °C"
	HUMIDITY = 17               # Example: "81 %"
	WINDDISPLAY = 18            # Example: "12 km/h Southwest"
	ICON = 19                   # Example: "9" (matching the extended weather icon code: YAHOO+)
	TEMPERATURE_HIGH_LOW = 20   # Example: "6 - 9 °C"
#   new entries since January 2023
	WEATHERSOURCE = 21          # Example: "MSN Weather"
	LONGITUDE = 22              # Example: "53.5573"
	LATITUDE = 23               # Example: "9.996"
	SUNRISE = 24                # Example: "08:30"
	SUNSET = 25                 # Example: "16:27"
	ISNIGHT = 26                # Example: "False" or "True"
	TEMPUNIT = 27               # Example: "°C"
	WINDUNIT = 28               # Example: "km/h"
	WINDSPEED = 29              # Example: "12 km/h"
	WINDDIR = 30                # Example: "230 °"
	WINDDIRSIGN = 31            # Example: "↗ SW"
	WINDDIRARROW = 31           # Example: "↗"
	WINDDIRNAME = 32            # Example: "Southwest"
	WINDDIRSHORT = 33           # Example: "SW"
	YAHOOCODE = 34              # Example: "9" (matching the extended weather icon code: YAHOO+)
	METEOCODE = 35              # Example: "Q" (matching the character set: MetrixIcons.ttf)

	def __init__(self, type: str):
		self.enabledebug = config.plugins.OAWeather.debug.value
		Converter.__init__(self, type)
		self.debug("__init__ type:%s" % type)
		self.index = None
		self.mode = None
		self.path = None
		self.extension = "png"
		if type == "weathersource":
			self.mode = self.WEATHERSOURCE
		elif type == "city":
			self.mode = self.CITY
		elif type == "longitude":
			self.mode = self.LONGITUDE
		elif type == "latitude":
			self.mode = self.LATITUDE
		elif type == "observationpoint":
			self.mode = self.OBSERVATIONPOINT
		elif type == "observationtime":
			self.mode = self.OBSERVATIONTIME
		elif type == "sunrise":
			self.mode = self.SUNRISE
		elif type == "sunset":
			self.mode = self.SUNSET
		elif type == "isnight":
			self.mode = self.ISNIGHT
		elif type == "tempunit":
			self.mode = self.TEMPUNIT
		elif type == "windunit":
			self.mode = self.WINDUNIT
		elif type == "temperature_current":
			self.mode = self.TEMPERATURE_CURRENT
		elif type == "feelslike":
			self.mode = self.FEELSLIKE
		elif type == "humidity":
			self.mode = self.HUMIDITY
		elif type == "winddisplay":
			self.mode = self.WINDDISPLAY
		elif type == "windspeed":
			self.mode = self.WINDSPEED
		elif type == "winddir":
			self.mode = self.WINDDIR
		elif type == "winddirsign":
			self.mode = self.WINDDIRSIGN
		elif type == "winddirarrow":
			self.mode = self.WINDDIRARROW
		elif type == "winddirname":
			self.mode = self.WINDDIRNAME
		elif type == "winddirshort":
			self.mode = self.WINDDIRSHORT
		else:
			if type.startswith("weathericon"):
				self.mode = self.ICON
			if type.startswith("yahoocode"):
				self.mode = self.YAHOOCODE
			if type.startswith("meteocode"):
				self.mode = self.METEOCODE
			elif type.startswith("temperature_high_low"):
				self.mode = self.TEMPERATURE_HIGH_LOW
			elif type.startswith("temperature_high"):
				self.mode = self.TEMPERATURE_HIGH
			elif type.startswith("temperature_low"):
				self.mode = self.TEMPERATURE_LOW
			elif type.startswith("temperature_text"):
				self.mode = self.TEMPERATURE_TEXT
			elif type.startswith("weekday"):
				self.mode = self.WEEKDAY
			elif type.startswith("weekshortday"):
				self.mode = self.WEEKSHORTDAY
			elif type.startswith("date"):
				self.mode = self.DATE
			if self.mode is not None:
				dd = type.split(",")
				self.index = self.getIndex(dd[1].strip()) if len(dd) > 1 else None
				if self.mode in (self.ICON, self.YAHOOCODE, self.METEOCODE) and len(dd) > 2:
					self.path = dd[2].strip()
					if len(dd) > 3:
						self.extension = dd[3].strip()
		self.debug("__init__ DONE self.mode:%s self.index:%s self.path:%s" % (self.mode, self.index, self.path))
		if config.plugins.OAWeather.debug.value:
			self.getText = self.getTextDebug

	def getIndex(self, key: str):
		self.debug("getIndex key:%s" % (key))
		if key == "current":
			return self.CURRENT
		elif key == "day1":
			return self.DAY1
		elif key == "day2":
			return self.DAY2
		elif key == "day3":
			return self.DAY3
		elif key == "day4":
			return self.DAY4
		elif key == "day5":
			return self.DAY5
		else:
			return None

	@cached
	def getTextDebug(self):
		self.debug("getText mode:%s index:%s" % (self.mode, self.index))
		text = self.getText()
		self.debug("getText mode:%s index:%s value:%s" % (self.mode, self.index, text))
		return text

	@cached
	def getText(self):
		try:
			if self.mode == self.WEATHERSOURCE:
				return self.source.getVal("source")
			elif self.mode == self.CITY:
				return self.source.getVal("name")
			elif self.mode == self.LONGITUDE:
				return self.source.getVal("longitude")
			elif self.mode == self.LATITUDE:
				return self.source.getVal("latitude")
			elif self.mode == self.OBSERVATIONPOINT:
				return self.source.getVal("name")
			elif self.mode == self.OBSERVATIONTIME:
				return self.source.getObservationTime()
			elif self.mode == self.SUNRISE:
				return self.source.getSunrise()
			elif self.mode == self.SUNSET:
				return self.source.getSunset()
			elif self.mode == self.ISNIGHT:
				return self.source.getIsNight()
			elif self.mode == self.TEMPUNIT:
				return self.source.getVal("tempunit")
			elif self.mode == self.WINDUNIT:
				return self.source.getVal("windunit")
			elif self.mode == self.TEMPERATURE_CURRENT:
				return self.source.getTemperature()
			elif self.mode == self.FEELSLIKE:
				return self.source.getFeeltemp()
			elif self.mode == self.HUMIDITY:
				return self.source.getHumidity()
			elif self.mode == self.WINDDISPLAY:
				return "%s %s" % (self.source.getWindSpeed(), self.source.getWindDirName())
			elif self.mode == self.WINDSPEED:
				return self.source.getWindSpeed()
			elif self.mode == self.WINDDIR:
				return self.source.getWindDir()
			elif self.mode == self.WINDDIRSIGN:
				return self.source.getCurrentVal("windDirSign")
			elif self.mode == self.WINDDIRARROW:
				return self.source.getCurrentVal("windDirSign").split(" ")[0]
			elif self.mode == self.WINDDIRNAME:
				return self.source.getWindDirName()
			elif self.mode == self.WINDDIRSHORT:
				return self.source.getWindDirShort()
			elif self.mode == self.TEMPERATURE_HIGH and self.index is not None:
				return self.source.getMaxTemp(self.index)
			elif self.mode == self.TEMPERATURE_LOW and self.index is not None:
				return self.source.getMinTemp(self.index)
			elif self.mode == self.TEMPERATURE_HIGH_LOW and self.index is not None:
				return self.source.getMaxMinTemp(self.index)
			elif self.mode == self.TEMPERATURE_TEXT and self.index is not None:
				return self.source.getKeyforDay("text", self.index)
			elif self.mode in (self.ICON, self.YAHOOCODE) and self.index is not None:
				return self.source.getYahooCode(self.index)
			elif self.mode == self.METEOCODE and self.index is not None:
				return self.source.getMeteoCode(self.index)
			elif self.mode == self.WEEKDAY and self.index is not None:
				return self.source.getKeyforDay("day", self.index)
			elif self.mode == self.WEEKSHORTDAY and self.index is not None:
				return self.source.getKeyforDay("shortDay", self.index)
			elif self.mode == self.DATE and self.index is not None:
				return self.source.getKeyforDay("date", self.index)
			else:
				return ""
		except Exception as err:
			print("[OAWeather] Converter Error:%s" % str(err))
			print_exc()
			return ""

	text = property(getText)

	@cached
	def getIconFilename(self):
		path = ""
		if self.index in (self.CURRENT, self.DAY1, self.DAY2, self.DAY3, self.DAY4, self.DAY5):
			path = self.path
			if path and exists(path):
				code = self.source.getYahooCode(self.index)
				if code:
					path = join(path, "%s.%s" % (code, self.extension))
					if exists(path):
						return path
		self.debug("getIconFilename mode:%s index:%s self.path:%s path:%s" % (self.mode, self.index, self.path, path))
		return path

	def debug(self, text: str):
		if self.enabledebug:
			print("[OAWeather] Converter DEBUG %s" % text)

	iconfilename = property(getIconFilename)

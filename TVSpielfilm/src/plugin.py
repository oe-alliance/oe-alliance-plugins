########################################################################################################
# TV Spielfilm by Mr.Servo @OpenATV (c) 2025 - skinned by stein17 @OpenATV                             #
# Special thanks to jbleyel @OpenATV for his valuable support in creating the code.                    #
# -----------------------------------------------------------------------------------------------------#
# This plugin is licensed under the GNU version 3.0 <https://www.gnu.org/licenses/gpl-3.0.en.html>.    #
# This plugin is NOT free software. It is open source, you are allowed to modify it (if you keep       #
# the license), but it may not be commercially distributed. Advertise with this plugin is not allowed. #
# For other uses, permission from the authors is necessary.                                            #
########################################################################################################

# PYTHON IMPORTS
from datetime import datetime, timedelta
from glob import glob
from html import unescape
from json import loads, dumps
from os import rename, makedirs, remove
from os.path import exists, join, getmtime
from secrets import choice
from re import compile, match, findall
from requests import get, exceptions
from shutil import copy, rmtree
from twisted.internet.reactor import callInThread

# ENIGMA IMPORTS
from enigma import getDesktop, eServiceReference, eServiceCenter, eTimer, eEPGCache
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigText
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.Sources.List import List
from Components.ScrollLabel import ScrollLabel
from Components.Sources.ServiceList import ServiceList
from Components.Sources.StaticText import StaticText
from Components.UsageConfig import preferredTimerPath
from Plugins.Plugin import PluginDescriptor
from ServiceReference import ServiceReference
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.LocationBox import defaultInhibitDirs, LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.Timers import RecordTimerEdit, RecordTimerEntry
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, isPluginInstalled, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE, SCOPE_CONFIG
from Tools.LoadPixmap import LoadPixmap

STARTTIMES = ["00:00", "02:00", "04:00", "06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "19:00", "20:00", "20:15", "22:00"]
ASSETFILTERS = [("{keiner}", ""), ("Tipp", "isTipOfTheDay"), ("Neu", "isNew"), ("Tagestipp", "isTopTip")]
STARTING = [(i, f"{x} Uhr") for i, x in enumerate(STARTTIMES)]
DURANCES = [(x, f"{x} Minuten") for x in range(15, 135, 15)]
CACHEDAYS = [(x, f"+{x} Tage") for x in range(1, 14)]
config.plugins.tvspielfilm = ConfigSubsection()
config.plugins.tvspielfilm.showtips = ConfigSelection(default=2, choices=[(0, "niemals"), (1, "nur bei Pluginstart"), (2, "immer")])
config.plugins.tvspielfilm.filter = ConfigSelection(default=0, choices=[(i, f"{x[0]}") for i, x in enumerate(ASSETFILTERS)])
config.plugins.tvspielfilm.channelname = ConfigSelection(default=1, choices=[(0, "vom Image"), (1, "vom Server")])
config.plugins.tvspielfilm.prefered_db = ConfigSelection(default=0, choices=[(0, "jedesmal nachfragen"), (1, "IMDb - Internet Movie Database"), (2, "TMDb - The Movie Database")])
config.plugins.tvspielfilm.update_mapfile = ConfigSelection(default=1, choices=[(0, "niemals"), (1, "nach Updates")])
config.plugins.tvspielfilm.cachepath = ConfigText(default=join("/media/hdd/"))
config.plugins.tvspielfilm.keepcache = ConfigSelection(default=7, choices=[(x, f"-{x} Tage") for x in range(8)])
config.plugins.tvspielfilm.use_a = ConfigYesNo(default=False)
config.plugins.tvspielfilm.starttime_a = ConfigSelection(default=4, choices=STARTING)
config.plugins.tvspielfilm.durance_a = ConfigSelection(default=90, choices=DURANCES)
config.plugins.tvspielfilm.cache_a = ConfigSelection(default=7, choices=CACHEDAYS)
config.plugins.tvspielfilm.use_b = ConfigYesNo(default=False)
config.plugins.tvspielfilm.starttime_b = ConfigSelection(default=5, choices=STARTING)
config.plugins.tvspielfilm.durance_b = ConfigSelection(default=90, choices=DURANCES)
config.plugins.tvspielfilm.cache_b = ConfigSelection(default=7, choices=CACHEDAYS)
config.plugins.tvspielfilm.use_c = ConfigYesNo(default=True)
config.plugins.tvspielfilm.starttime_c = ConfigSelection(default=12, choices=STARTING)
config.plugins.tvspielfilm.durance_c = ConfigSelection(default=75, choices=DURANCES)
config.plugins.tvspielfilm.cache_c = ConfigSelection(default=7, choices=CACHEDAYS)
config.plugins.tvspielfilm.use_d = ConfigYesNo(default=True)
config.plugins.tvspielfilm.starttime_d = ConfigSelection(default=13, choices=STARTING)
config.plugins.tvspielfilm.durance_d = ConfigSelection(default=90, choices=DURANCES)
config.plugins.tvspielfilm.cache_d = ConfigSelection(default=7, choices=CACHEDAYS)
config.plugins.tvspielfilm.durance_n = ConfigSelection(default=90, choices=DURANCES)


class TVglobals():
	IMPORTDICT = {}
	RELEASE = "v1.0"
	MODULE_NAME = __name__.split(".")[-2]
	RESOLUTION = "FHD" if getDesktop(0).size().width() > 1300 else "HD"
	PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/TVSpielfilm/")
	ICONPATH = f"{PLUGINPATH}pics/{RESOLUTION}/icons/"
	FILTERDICT = {"{keiner}": "", "tip": "isTipOfTheDay", "Neu": "isNew", "Tagestipp": "isTopTip"}
	BASEURL = bytes.fromhex("68747470733a2f2f6c6976652e7476737069656c66696c6d2e64652f7"[:-1]).decode()
	USERAGENT = choice([
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
			"Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
			"Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edge/87.0.664.75",
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"
			])
	HAS_FUNCTIONTIMER = True
	try:
		from Scheduler import functionTimer
	except ImportError as error:
		HAS_FUNCTIONTIMER = False


tvglobals = TVglobals()


class TVhelper(Screen):
	def getTMPpath(self):
		return f"{config.plugins.tvspielfilm.cachepath.value}tmp/TVSpielfilm/" if config.plugins.tvspielfilm.cachepath.value == "/" else f"{config.plugins.tvspielfilm.cachepath.value}TVSpielfilm/"

	def imageDownload(self, url, imgfile, callback=None, widget=None):
		headers = {"User-Agent": tvglobals.USERAGENT, }
		try:
			response = get(url, headers=headers, timeout=(3.05, 6))
			response.raise_for_status()
		except exceptions.RequestException as error:
			print("[%s] ERROR in class 'TVglobals:imageDownload': %s" % (tvglobals.MODULE_NAME, str(error)))
			return
		if not exists(imgfile):
			with open(imgfile, "wb") as file:
				file.write(response.content)
			if callback:
				callback(widget, imgfile)

	def saveAllAssets(self, assetsdict, date, spanStarts):
		if assetsdict and date:
			try:
				filename = join(f"{self.getTMPpath()}cache/", f"allAssets{date}T{spanStarts}.json")
				if not exists(filename):
					with open(filename, "w") as file:
						file.write(dumps(assetsdict))
			except OSError as error:
				self.session.open(MessageBox, "Datensatz konnte nicht gespeichert werden:\n'%s'" % error, type=MessageBox.TYPE_INFO, timeout=2, close_on_any_key=True)
				return False
		return True

	def showAssetDetails(self, assetId, fullscreen=False):  # e.g. 'ARD672261f960673f600aef94d9'
		assetdict = {}
		assetfile = join(f"{self.getTMPpath()}assets/", f"{assetId}.json")
		if exists(assetfile):
			with open(assetfile, "r") as file:
				assetdict = {}
				try:
					assetdict = loads(file.read())  # load details for current asset from cache
				except OSError as error:
					self.session.open(MessageBox, "Fehler beim Laden einer Sendungsbeschreibung:\n'%s'" % error, type=MessageBox.TYPE_ERROR, timeout=2, close_on_any_key=True)
					return
		else:
			url = f"{tvglobals.BASEURL}api/reco/content/pub/details/{assetId}"
			errmsg, jsondict = getAPIdata(url)  # download details for current asset
			if errmsg:
				print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVoverview:showAssetDetails': {errmsg}!")
				return
			assetdict = jsondict.get("asset", {})
			with open(assetfile, "w") as file:  # save details for current asset to cache
				file.write(dumps(assetdict))
		if assetdict:
			isTopTip = assetdict.get("flags", {}).get("isTopTip", "")
			isTipOfTheDay = assetdict.get("flags", {}).get("isTipOfTheDay", "")
			isNew = assetdict.get("flags", {}).get("isNew", "")
			# isLive = assetdict.get("flags", {}).get("isLive", "")
			# isDolbyDigital = assetdict.get("flags", {}).get("isDolbyDigital", "")
			# isDolbySurround = assetdict.get("flags", {}).get("isDolbySurround", "")
			# isLastDate = assetdict.get("flags", {}).get("isLastDate", "")
			# isMediathek = assetdict.get("flags", {}).get("isMediathek", "")
			# isExpectedMediathek = assetdict.get("flags", {}).get("isExpectedMediathek", "")
			airInfo = assetdict.get("airInfo", {})
			timeStart = airInfo.get("timeStart", "")
			self.currdatetime = datetime.fromtimestamp(timeStart)
			timeStart = self.currdatetime.strftime("%H:%M") if timeStart else ""
			self.spanStarts = timeStart
			timeEnd = airInfo.get("timeEnd", "")
			timeEnd = datetime.fromtimestamp(timeEnd).strftime("%H:%M") if timeEnd else ""
			repeatHint = unescape(airInfo.get("repeatHint", ""))  # e.g.'Wh. um 00:20 Uhr, Nächste Episode um 21:55 Uhr (Staffel 8, Episode 24)'
			channelId = airInfo.get("channel", {}).get("id", "").lower()
			channelName = airInfo.get("channel", {}).get("name", "") if config.plugins.tvspielfilm.channelname.value else tvglobals.IMPORTDICT.get(channelId, ["", ""])[1]
			# isLiveTv = airInfo.get("channel", {}).get("isLiveTv", "")
			metaInfo = assetdict.get("metaInfo", {})
			# originalTitle = metaInfo.get("originalTitle", "")
			subline = metaInfo.get("subline", "") or metaInfo.get("preview", "")
			subline += "\n" if subline else ""
			seriesInfo = assetdict.get("seriesInfo", {})
			seasonNumber = seriesInfo.get("seasonNumber", "")
			seasonNumber = f"S{seasonNumber}" if seasonNumber else ""
			episodeNumber = seriesInfo.get("episodeNumber", "")
			episodeNumber = f"E{episodeNumber}" if episodeNumber else ""
			seasonEpisode = f"{seasonNumber} | {episodeNumber}" if seasonNumber else episodeNumber
			conclusion = unescape(metaInfo.get("conclusion", ""))
			text = unescape(metaInfo.get("text", "").replace("\n\n", "\n"))
			self.assetTitle = unescape(assetdict.get("title", ""))
			rating = assetdict.get("rating", {})
			thumbIdNumeric = rating.get("thumbIdNumeric", -1)
			demanding = rating.get("demanding")
			humor = rating.get("humor")
			action = rating.get("action")
			suspense = rating.get("suspense")
			erotic = rating.get("erotic")
			genre = assetdict.get("genre", {})
			broad = genre.get("broad", "")  # e.g. 'Katastrophenaction'
			fine = genre.get("fine", "")  # e.g. 'Katastrophen'
			TVSgenres = {"U": "Unterhaltung", "SE": "Serie", "SPO": "Sport", "SP": "Spielfilm", "KIN": "Kindersendung", "RE": "Reportage", "AND": "Andere"}
			programType = TVSgenres.get(assetdict.get("programType", "AND"), "")  # e.g. 'SP' becomes 'Spielfilm'
			media = assetdict.get("media", {})
			imgurl, imgcredits = "", ""
			for dictpart in media.get("images", []):
				imgurl = dictpart.get("size3", "")  # image 476 x 357
				imgcredits = dictpart.get("credits", "")  # e.g. 'Twentieth Century FOX Home Entertainment'
				imgcredits = f"Foto: {imgcredits}" if imgcredits else ""
				break
			if imgurl:
				imgfile = join(f"{self.getTMPpath()}images/", imgurl[imgurl.rfind("/") + 1:])
				if exists(imgfile):
					self["image"].instance.setPixmapFromFile(imgfile)
					self["image"].show()
				else:
					callInThread(self.imageDownload, imgurl, imgfile, self.setWidgetsImage, "image")
			self.trailerUrl = ""
			for dictpart in media.get("trailers", []):
				for subpart in dictpart.get("streams", []):
					self.trailerUrl = subpart.get("url", "")
					break
			productionInfo = assetdict.get("productionInfo", {})
			lengthNetAndGross = productionInfo.get("lengthNetAndGross", "").split("/")[0]
			lengthNetAndGross = int(lengthNetAndGross) if lengthNetAndGross else 0
			titleLength = lengthNetAndGross or productionInfo.get("titleLength", 0)
			self.titleLenStr = f"{lengthNetAndGross or titleLength} Minuten" if lengthNetAndGross or titleLength else ""
			anchorman = productionInfo.get("anchorman", "")
			anchorman = f"mit {anchorman}\n" if anchorman else ""
			currentTopics = productionInfo.get("currentTopics", "")
			currentTopics += "\n" if currentTopics else ""
			firstYear = productionInfo.get("firstYear", "")
			country = productionInfo.get("country", "")
			yearCountry = f"{firstYear} | {country}" if firstYear and country else firstYear or country
			imdbRating = productionInfo.get("imdbRating", "")
			imdbId = productionInfo.get("externalIds", {}).get("imdbId", "")
			tmdbId = productionInfo.get("externalIds", {}).get("tmdbId", "")
			if imdbId and tmdbId:
				infotext, self.dataBases = "IMDb+TMDb", ["imdb", "tmdb"]
			elif imdbId:
				infotext, self.dataBases = "IMDb", ["imdb"]
			elif tmdbId:
				infotext, self.dataBases = "TMDb", ["tmdb"]
			else:
				infotext, self.dataBases = "Titelsuche", ["imdb", "tmdb"]
			self["key_info"].setText(infotext)
			fsk = productionInfo.get("fsk", "")
			fskText = f"ab {fsk} Jahren" if fsk else ""
#			parentTitleGroupTitle = productionInfo.get("parentTitleGroupTitle", "")
			persons = productionInfo.get("persons", {})
			directors = persons.get("directors", [])
			personslist = f"Regie: {', '.join([x.get('name', '') for x in directors])}" if directors else ""
			actors = persons.get("actors", [])
			actorslist = ""  # create list 'Actors - Role in movie'
			if actors:
				actorslist += "\nSchauspieler:\n"
				for actor in actors:
					actorslist += f"{actor.get('name', '')} als '{actor.get('role')}'\n"
			personslist += actorslist
			crew = persons.get("crew", [])
			crewdict, crewlist = {}, ""
			for entry in crew:  # summarize the names of the role participants (e.g. in role 'camera')
				role = entry.get('role', '')
				name = entry.get('name', '')
				if role in crewdict:
					crewdict[role].append(name)
				else:
					crewdict[role] = [name]
			for role, namelist in crewdict.items():
				crewlist += f"{role}: {', '.join(namelist)}\n"
			personslist += crewlist
			sref = tvglobals.IMPORTDICT.get(channelId, ["", ""])[0]
			timeStartEnd = f"{timeStart} - {timeEnd}"
			hasTimer = self.isAlreadyListed(timeStartEnd, sref, self.currdatetime, self.getTimerlist()) if timeStartEnd and sref else False
			piconfile = self.getPiconFile(channelId)
			if piconfile and exists(piconfile):
				self["picon"].instance.setPixmapFromFile(piconfile)
				self["picon"].show()
			else:
				self["picon"].hide()
			self["channelName"].setText(channelName)
			for assetFlag, widget in [(isTopTip, "isTopTip"), (isNew, "isNew"), (isTipOfTheDay, "isTipOfTheDay"),
							(hasTimer, "hasTimer"), (imdbId, "isIMDB"), (tmdbId, "isTMDB")]:
				if assetFlag:
					self[widget].show()
				else:
					self[widget].hide()
			self["timeStartEnd"].setText(timeStartEnd)
			if self.trailerUrl:
				self["playButton"].show()
				self["play"].show()
				self["key_play"].setText("Trailer abspielen")
			else:
				self["playButton"].hide()
				self["play"].hide()
				self["key_play"].setText("")
			for index, (rating, category) in enumerate([(humor, "Humor"), (demanding, "Anspruch"), (action, "Action"), (suspense, "Spannung"), (erotic, "Erotik")]):
				self[f"ratingLabel{index}l"].setText(category if rating is None else "")
				self[f"ratingLabel{index}h"].setText("" if rating is None else category)
				picfile = join(tvglobals.ICONPATH, "pointbar_.png") if rating is None else join(tvglobals.ICONPATH, f"pointbar{rating}.png")
				if exists(picfile):
					self[f"ratingDots{index}"].instance.setPixmapFromFile(picfile)
					self[f"ratingDots{index}"].show()
				else:
					self[f"ratingDots{index}"].hide()
			self.currImdbId = imdbId
			self["imdbRating"].setText(f"IMDb-Wertung: {imdbRating}/10" if imdbRating else "")
			if thumbIdNumeric != -1:
				thumbfile = join(tvglobals.ICONPATH, f"thumb{thumbIdNumeric}.png")
				if exists(thumbfile):
					self["thumb"].instance.setPixmapFromFile(thumbfile)
					self["thumb"].show()
			else:
				self["thumb"].hide()
			fskfile = join(tvglobals.ICONPATH, f"FSK_{fsk}.png") if fsk else join(tvglobals.ICONPATH, "FSK_NA.png")
			self["fsk"].instance.setPixmapFromFile(fskfile)
			self["fsk"].show()
			self["repeatHint"].setText(repeatHint)
			self["title"].setText(self.assetTitle)
			self["editorial"].setText("Meinung der Redaktion:" if conclusion else "")
			self["conclusion"].setText(conclusion)
			self["longDescription"].setText(f"{subline}{currentTopics}{anchorman}{text}\n{personslist}")
			self["key_green"].setText("" if hasTimer else "Timer hinzufügen")
			self.currentAssetId = assetId
			if fullscreen:
				for index, (label, text) in enumerate([("Staffel/Episode", seasonEpisode), ("Genre", fine or broad), ("Typ", programType),
												("Altersfreigabe", fskText), ("Jahr", yearCountry), ("Länge", self.titleLenStr)]):
					if text:
						self[f"typeLabel{index}h"].setText(label)
						self[f"typeLabel{index}l"].setText("")
						self[f"typeText{index}"].setText(text)
					else:
						self[f"typeLabel{index}h"].setText("")
						self[f"typeLabel{index}l"].setText(label)
						self[f"typeText{index}"].setText("")
				self["credits"].setText(imgcredits)
				self.timeStartEnd = timeStartEnd
				self.serviceRef = sref
				self.subLine = subline
				self.spanDurance = titleLength
			self.setReviewdate(fullscreen)

	def setReviewdate(self, fullscreen=False):
		now = datetime.today()
		now -= timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)  # round to last 15 minutes for 'Jetzt im TV'
		spanStarts = self.spanStarts or now.strftime("%H:%M")
		currdatetime = self.currdatetime
		currdateonly = currdatetime.replace(hour=0, minute=0, second=0, microsecond=0)
		todaydateonly = datetime.today().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
		weekday = "heute" if currdateonly == todaydateonly else ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][currdateonly.weekday()]
		hour, minute = spanStarts.split(":") if spanStarts else [currdatetime.strftime("%H"), currdatetime.strftime("%M")]
		spanEnds = (currdatetime.replace(hour=int(hour), minute=int(minute)) + timedelta(minutes=int(self.spanDurance))).strftime("%H:%M")
		if fullscreen:
			reviewdate = f"{weekday} {currdatetime.strftime('%d.%m.%Y')} | von {spanStarts} Uhr bis {spanEnds} Uhr | {self.titleLenStr}"
		else:
			reviewdate = f"{weekday} {currdatetime.strftime('%d.%m.%Y')} | +{self.currdaydelta} Tag(e) | {spanStarts} Uhr bis {spanEnds} Uhr"
		self["reviewdate"].setText(reviewdate)

	def setWidgetsImage(self, widget, filename):
		self[widget].instance.setPixmapFromFile(filename)

	def getPiconFile(self, channelId):
		sref = tvglobals.IMPORTDICT.get(channelId, ["", ""])[0]
		fallback = sref.split(":")  # fallback from "1:0:*:..." to "1:0:1:..."
		if len(fallback) > 1:
			fallback[2] = "1"
			fallback = ":".join(fallback)
			fallback = (f"{fallback}FIN").replace(":", "_").replace("_FIN", "").replace("FIN", "")
		sref = f"{sref}FIN".replace(":", "_").replace("_FIN", "").replace("FIN", "")
		for piconsref in [sref, fallback]:
			piconfile = join(join(resolveFilename(SCOPE_SKIN_IMAGE), "picon/"), f"{piconsref}.png")
			if exists(piconfile):
				return piconfile
			return ""

	def getTips(self, callback):
		date = datetime.today().strftime("%F")
		tipsfile = join(f"{self.getTMPpath()}cache/", f"allTips{date}.json")
		if exists(tipsfile):
			with open(tipsfile, "r") as file:
				tipsdict = loads(file.read())
		else:
			url = f"{tvglobals.BASEURL}api/reco/content/pub/teasers/tips-of-the-day"
			params = [('date', date)]
			errmsg, tipsdict = getAPIdata(url, params)
			if errmsg:
				print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVmain:getTips': {errmsg}!")
				return
			with open(tipsfile, "w") as file:
				file.write(dumps(tipsdict))
		tipslist = []
		for index0, tips in enumerate([[tipsdict.get("topTip", {})], tipsdict.get("tips", {}), tipsdict.get("highlights", {}),]):
			for index1, tip in enumerate(tips):
				channelId = tip.get("channelId", "").lower()
				isTipOfTheDay = tip.get("isTipOfTheDay", False)
				programType = tip.get("programType", "")
				if channelId not in tvglobals.IMPORTDICT and isTipOfTheDay or (index0 == 2 and programType != "SP"):
					continue
				currTipId = tip.get("assetId", "")
				title = unescape(tip.get("title", ""))
				timeStart = tip.get("timeStart", "")
				timeStart = datetime.fromtimestamp(timeStart).strftime("%H:%M") if timeStart else ""
				timeEnd = tip.get("timeEnd", "")
				timeEnd = datetime.fromtimestamp(timeEnd).strftime("%H:%M") if timeEnd else ""
				timeStartEnd = f"{timeStart} - {timeEnd}" if timeStart or timeEnd else ""
				imgurl = tip.get("images", {}).get("size3", "")
				imgfile = join(f"{self.getTMPpath()}images/", f"{imgurl[imgurl.rfind('/') + 1:]}") if imgurl else ""
				if imgfile:
					if index1:
						if not exists(imgfile):
							callInThread(self.imageDownload, imgurl, imgfile)
					elif not exists(imgfile):  # very first tip image not exists?
						callInThread(self.imageDownload, imgurl, imgfile, self.setFirstTipImage, "image")  # set first tip image immediately
				genreBroad = tip.get("genreBroad", "")
				channelName = tip.get("channelName", "") if config.plugins.tvspielfilm.channelname.value else tvglobals.IMPORTDICT.get(channelId, ["", ""])[1]
				thumbIdNumeric = tip.get("thumbIdNumeric", -1)
				isTopTip = tip.get("isTopTip", False)
				isNew = tip.get("flags", {}).get("isNew", False)
				productionInfo = tip.get("productionInfo", {})
				titleLength = str(productionInfo.get("titleLength", ""))
				titleLength = f"{titleLength} Minuten" if titleLength else ""
				firstYear = productionInfo.get("firstYear", "")
				country = productionInfo.get("country", "")
				yearCountry = f"{firstYear} | {country}" if firstYear and country else firstYear or country
				imdbRating = productionInfo.get("imdbRating", "")
				imdbRating = f"IMDb-Wertung: {imdbRating}/10" if imdbRating else ""
				fsk = productionInfo.get("fsk", "")
				fskText = f"ab {fsk} Jahren" if fsk else ""
				metaInfo = tip.get("metaInfo", {})
				conclusion = unescape(metaInfo.get("conclusion", ""))
				tipslist.append((title, timeStartEnd, genreBroad, channelName, titleLength, yearCountry, imdbRating,
				  				fskText, conclusion, isTopTip, isTipOfTheDay, isNew, fsk, thumbIdNumeric, imgurl, channelId, currTipId))
		self.tipslist = tipslist
		callback()

	def getTipsCB(self):
		if config.plugins.tvspielfilm.showtips.value:
			self.showTVtipsBox(5000)
		else:
			self.hideTVtipsBox()

	def setFirstTipImage(self, widget, imgfile):
		if exists(imgfile):
			self.tvtipsbox.setImage(widget, imgfile)
			self.tvtipsbox.showWidget(widget)

	def isAlreadyListed(self, timespan, sref, currdatetime, timerlist):
		startTs, endTs = self.splitTimespan(timespan.split(" - "), currdatetime)  #  e.g. '20:15 - 21:45'
		timer = f"{datetime.fromtimestamp(startTs).strftime('%Y-%m-%d')}:::{datetime.fromtimestamp(startTs).strftime('%H:%M')}:::{sref}"  # e.g. ['2024-12-21:::20:15:::1:0:19:283D:41B:1:FFFF0000:0:0:0:', ...]
		return timer in timerlist

	def splitTimespan(self, timespan, currdatetime):
		startstr, endstr = timespan
		starthour, startminute = startstr.split(":")
		endhour, endminute = endstr.split(":")
		startTs = int(datetime.timestamp(currdatetime.replace(hour=int(starthour), minute=int(startminute), second=0, microsecond=0)))
		endTs = int(datetime.timestamp(currdatetime.replace(hour=int(endhour), minute=int(endminute), second=0, microsecond=0)))
		return startTs, endTs

	def getTimerlist(self):
		timerlist = []
		e2timer = resolveFilename(SCOPE_CONFIG, "timers.xml")  # /etc/enigma2/timers.xml
		if exists(e2timer):
			timerxml = open(e2timer).read()  # e.g. <timer begin="1734631080" end="1734636300" ... serviceref="1:0:19:C3FF:27FF:F001:FFFF0000:0:0:0:"
			timers = findall(r'<timer begin="(.*?)" end=".*?" serviceref="(.*?)"', timerxml)
			for timer in timers:
				start = int(timer[0]) + int(config.recording.margin_before.value) * 60
				day = datetime.fromtimestamp(start).strftime("%Y-%m-%d")
				hour = datetime.fromtimestamp(start).strftime("%H:%M")
				timerlist.append(f"{day}:::{hour}:::{timer[1]}")
		return timerlist  # e.g. ['2024-12-21:::20:15:::1:0:19:283D:41B:1:FFFF0000:0:0:0:', ...]

	def playTrailer(self):
		if self.trailerUrl:
			sref = eServiceReference(4097, 0, self.trailerUrl)
			sref.setName(self.assetTitle)
			try:
				self.session.open(MoviePlayer, sref, fromMovieSelection=False)  # some images don't support this option
			except Exception:
				self.session.open(MoviePlayer, sref)

	def keyInfo(self):
		if self.dataBases == ["imdb"]:
			self.openImdb()
		elif self.dataBases == ["tmdb"]:
			self.openTmdb()
		else:
			if config.plugins.tvspielfilm.prefered_db.value == 1:
				self.openImdb()
			elif config.plugins.tvspielfilm.prefered_db.value == 2:
				self.openTmdb()
			else:
				outlist = []
				for database, index in enumerate(self.dataBases):
					outlist.append((index, database))
				self.session.openWithCallback(self.keyInfoCB, ChoiceBox, list=outlist, keys=[], windowTitle="Wähle die gewünschte Datenbank:")

	def keyInfoCB(self, answer):
		if answer:
			if answer[0] == "imdb":
				self.openImdb()
			elif answer[0] == "tmdb":
				self.openTmdb()

	def openImdb(self):
		if isPluginInstalled("IMDb"):
			from Plugins.Extensions.IMDb.plugin import IMDB
			self.session.open(IMDB, self.assetTitle, imdbId=self.currImdbId)
		else:
			self.session.open(MessageBox, "Das Plugin 'IMDb' (Internet Movie DataBase) wurde nicht gefunden. Es muss zuerst installiert werden.", MessageBox.TYPE_WARNING, timeout=10)

	def openTmdb(self):
		if isPluginInstalled("tmdb"):
			from Plugins.Extensions.tmdb.tmdb import tmdbScreen
			self.session.open(tmdbScreen, self.assetTitle, 2)
		else:
			self.session.open(MessageBox, "Das Plugin 'TMDb' (The Movie DataBase) wurde nicht gefunden. Es muss zuerst installiert werden.", MessageBox.TYPE_WARNING, timeout=10)

	def openEPGSearch(self):
		if isPluginInstalled("EPGSearch"):
			from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearch
			self.session.open(EPGSearch, self.assetTitle, False)
		else:
			self.session.open(MessageBox, "Das Plugin 'EPGSearch' wurde nicht gefunden. Es muss zuerst installiert werden.", type=MessageBox.TYPE_INFO, timeout=10)


class TVfullscreen(TVhelper, Screen):
	skin = """
	<screen name="TVfullscreen" position="10,10" size="1260,700" resolution="1280,720" flags="wfNoBorder" backgroundColor="#16000000" transparent="0" title="TV Spielfilm Detailansicht">
		<eLabel name="TV_line" position="780,476" size="456,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="10,188" size="752,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="10,600" size="752,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="Gradient_BlueBlack" position="0,64" size="1260,590" zPosition="-10" backgroundColor="#10060613" />
		<eLabel name="TV_bg" position="0,0" size="1260,60" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="0,60" size="1260,2" backgroundColor=" #0027153c , #101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="0,652" size="1260,2" backgroundColor=" #0027153c , #101093 , black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="70,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
		<widget source="reviewdate" render="Label" position="270,34" size="720,24" font="Regular; 18" foregroundColor="white" backgroundColor="#16000000" halign="center" valign="center" zPosition="12" transparent="1" />
		<widget source="global.CurrentTime" render="Label" position="1110,0" size="140,60" font="Regular; 46" noWrap="1" halign="center" valign="bottom" foregroundColor="white" backgroundColor="#16000000" zPosition="12" transparent="1">
		<convert type="ClockToText">Default</convert>
			</widget>
		<widget source="global.CurrentTime" render="Label" position="1000,2" size="100,26" font="Regular;16" noWrap="1" halign="right" valign="bottom" foregroundColor="white" backgroundColor="#16000000" zPosition="12" transparent="1">
		<convert type="ClockToText">Format:%A</convert>
			</widget>
		<widget source="global.CurrentTime" render="Label" position="1000,26" size="100,26" font="Regular;16" noWrap="1" halign="right" valign="bottom" foregroundColor="white" backgroundColor="#16000000" zPosition="12" transparent="1">
			<convert type="ClockToText">Format:%e. %B</convert>
		</widget>
		<widget source="channelName" render="Label" position="548,158" size="220,32" font="Regular; 24" halign="center" foregroundColor="#0092cbdf" backgroundColor="#16000000" transparent="1" />
		<widget source="editorial" render="Label" position="90,80" size="490,30" font="Regular; 18" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="conclusion" render="Label" position="90,102" size="490,54" font="Regular;20" foregroundColor="#0092cbdf" backgroundColor="#16000000" transparent="1" valign="top" />
		<widget name="picon" position="586,66" size="147,88" alphatest="blend" scaleFlags="keepAspect" zPosition="1" />
		<widget source="title" render="Label" position="center,0" size="720,36" font="Regular;24" foregroundColor="#0092cbdf" backgroundColor="#16000000" transparent="1" wrap="ellipsis" halign="center" valign="center" zPosition="10" />
		<widget source="repeatHint" render="Label" position="10,600" size="750,46" font="Regular;18" valign="center" halign="left" backgroundColor="#16000000" transparent="1" />
		<widget name="image" position="794,70" size="400,302" alphatest="blend" scaleFlags="keepAspect" zPosition="1" />
		<widget name="playButton" position="970,194" size="60,60" alphatest="blend" zPosition="2" />
		<widget name="fsk" position="800,326" size="40,40" alphatest="blend" zPosition="2" />
		<widget source="credits" render="Label" position="756,372" size="474,22" font="Regular; 16" foregroundColor="grey" backgroundColor="#16000000" halign="center" transparent="1" />
		<widget name="isTopTip" position="94,164" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isTipOfTheDay" position="134,164" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isNew" position="174,164" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isIMDB" position="254,164" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isTMDB" position="214,164" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="hasTimer" position="529,166" size="14,14" alphatest="blend" zPosition="1" />
		<widget source="ratingLabel0l" render="Label" position="756,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel0h" render="Label" position="756,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots0" position="778,420" size="46,16" alphatest="blend" />
		<widget source="ratingLabel1l" render="Label" position="852,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel1h" render="Label" position="852,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots1" position="874,420" size="46,16" alphatest="blend" />
		<widget source="ratingLabel2l" render="Label" position="948,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel2h" render="Label" position="948,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots2" position="970,420" size="46,16" alphatest="blend" />
		<widget source="ratingLabel3l" render="Label" position="1044,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel3h" render="Label" position="1044,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots3" position="1066,420" size="46,16" alphatest="blend" />
		<widget source="ratingLabel4l" render="Label" position="1140,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel4h" render="Label" position="1140,396" size="90,24" font="Regular; 16" halign="center" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots4" position="1162,420" size="46,16" alphatest="blend" />
		<widget source="imdbRating" render="Label" position="292,160" size="170,22" font="Regular;16" halign="center" foregroundColor="yellow" backgroundColor="#16000000" transparent="1" zPosition="1" />
		<widget name="thumb" position="38,86" size="60,60" alphatest="blend" />
		<widget name="longDescription" position="10,190" size="750,410" font="Regular;20" backgroundColor="#16000000" transparent="1" scrollbarMode="showOnDemand" scrollbarBorderWidth="1" scrollbarWidth="10" scrollbarBorderColor="blue" scrollbarForegroundColor="#203060" />
		<widget source="title" render="RunningText" options="movetype=running,startpoint=0,startdelay=2000,wrap=0,always=0,repeat=2,oneshot=1" position="780,444" size="456,34" font="Regular; 22" halign="left" foregroundColor="#92cbdf" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel0l" render="Label" position="780,488" size="140,26" font="Regular;18" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel0h" render="Label" position="780,488" size="140,26" font="Regular;18" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel1l" render="Label" position="780,514" size="140,26" font="Regular;18" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel1h" render="Label" position="780,514" size="140,26" font="Regular;18" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel2l" render="Label" position="780,540" size="140,26" font="Regular;18" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel2h" render="Label" position="780,540" size="140,26" font="Regular;18" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel3l" render="Label" position="780,566" size="140,26" font="Regular;18" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel3h" render="Label" position="780,566" size="140,26" font="Regular;18" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel4l" render="Label" position="780,592" size="140,26" font="Regular;18" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel4h" render="Label" position="780,592" size="140,26" font="Regular;18" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel5l" render="Label" position="780,618" size="140,26" font="Regular;18" foregroundColor="#10333333" backgroundColor="#16000000" transparent="1" />
		<widget source="typeLabel5h" render="Label" position="780,618" size="140,26" font="Regular;18" foregroundColor="white" backgroundColor="#16000000" transparent="1" />
		<widget source="typeText0" render="Label" position="930,488" size="200,26" font="Regular;18" backgroundColor="#16000000" transparent="1" />
		<widget source="typeText1" render="Label" position="930,514" size="200,26" font="Regular;18" backgroundColor="#16000000" transparent="1" />
		<widget source="typeText2" render="Label" position="930,540" size="200,26" font="Regular;18" backgroundColor="#16000000" transparent="1" />
		<widget source="typeText3" render="Label" position="930,566" size="200,26" font="Regular;18" backgroundColor="#16000000" transparent="1" />
		<widget source="typeText4" render="Label" position="930,592" size="200,26" font="Regular;18" backgroundColor="#16000000" transparent="1" />
		<widget source="typeText5" render="Label" position="930,618" size="200,26" font="Regular;18" backgroundColor="#16000000" transparent="1" />
		<eLabel name="button_green" position="10,660" size="6,36" zPosition="1" backgroundColor=" #00006600, #0024a424, vertical" />
		<eLabel name="yellow" position="186,660" size="6,36" backgroundColor=" #007a6213, #00e6c619, vertical" zPosition="1" />
		<widget source="key_green" render="Label" position="20,666" size="160,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_yellow" render="Label" position="196,666" size="150,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_info" render="Label" position="960,666" size="120,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_play" render="Label" position="1116,666" size="160,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<eLabel text="Zurück" position="780,666" size="120,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<ePixmap position="910,664" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/info.png" alphatest="blend" zPosition="1" />
		<ePixmap position="730,664" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/ok.png" alphatest="blend" zPosition="1" />
		<widget name="play" position="1094,664" size="20,28" alphatest="blend" zPosition="2" />
		<eLabel name="" position="252,162" size="32,18" zPosition="-1" backgroundColor="#00505050" cornerRadius="2" />skin =
		<eLabel name="" position="172,162" size="32,18" zPosition="-1" backgroundColor="#00505050" cornerRadius="2" />
		<eLabel name="" position="212,162" size="32,18" zPosition="-1" backgroundColor="#00505050" cornerRadius="2" />
		<eLabel name="" position="132,162" size="32,18" zPosition="-1" backgroundColor="#00505050" cornerRadius="2" />
		<eLabel name="" position="92,162" size="32,18" zPosition="-1" backgroundColor="#00505050" cornerRadius="2" />
		<eLabel name="" position="88,158" size="376,26" zPosition="-1" backgroundColor="#00505050" cornerRadius="2" />
		<eLabel name="" position="253,163" size="30,16" zPosition="0" backgroundColor="#16000000" cornerRadius="2" />
		<eLabel name="" position="173,163" size="30,16" zPosition="0" backgroundColor="#16000000" cornerRadius="2" />
		<eLabel name="" position="213,163" size="30,16" zPosition="0" backgroundColor="#16000000" cornerRadius="2" />
		<eLabel name="" position="133,163" size="30,16" zPosition="0" backgroundColor="#16000000" cornerRadius="2" />
		<eLabel name="" position="93,163" size="30,16" zPosition="0" backgroundColor="#16000000" cornerRadius="2" />
		<eLabel name="" position="90,160" size="372,22" zPosition="0" backgroundColor="#16000000" cornerRadius="2" />
		<eLabel name="" position="168,162" size="1,18" zPosition="1" backgroundColor="#00505050" />
		<eLabel name="" position="288,162" size="1,18" zPosition="1" backgroundColor="#00505050" />
		<eLabel name="" position="128,162" size="1,18" zPosition="1" backgroundColor="#00505050" />
		<eLabel name="" position="208,162" size="1,18" zPosition="1" backgroundColor="#00505050" />
		<eLabel name="" position="248,162" size="1,18" zPosition="1" backgroundColor="#00505050" />
		<!-- <widget source="service" render="Cover" position="1140,478" size="104,156" zPosition="2" backgroundColor="#16000000" transparent="1" borderColor="#00203060" borderWidth="1" /> -->
	</screen>
	"""

	def __init__(self, session, assetId):
		self.assetId = assetId
		Screen.__init__(self, session)
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		self.assetTitle = ""
		self.timeStartEnd = ""
		self.spanStarts = ""
		self.spanDurance = 0
		self.titleLenStr = ""
		self.serviceRef = ""
		self.subLine = ""
		self.trailerUrl = ""
		self.dataBases = []
		self.currdatetime = datetime.today().astimezone()
		self["release"] = StaticText(tvglobals.RELEASE)
		self["longDescription"] = ScrollLabel()
		for wname in ["editorial", "conclusion", "repeatHint", "credits", "imdbRating", "timeStartEnd", "title",
						"reviewdate", "channelName", "key_info", "key_play"]:
			self[wname] = StaticText()
		for wname in ["picon", "image", "playButton", "fsk", "isTopTip", "isTipOfTheDay", "isNew", "isIMDB", "isTMDB",
						"hasTimer", "thumb", "info", "play"]:
			self[wname] = Pixmap()
			self[wname].hide()
		for index in range(5):
			self[f"ratingLabel{index}l"] = StaticText()
			self[f"ratingLabel{index}h"] = StaticText()
			self[f"ratingDots{index}"] = Pixmap()
			self[f"ratingDots{index}"].hide()
		for index in range(6):
			self[f"typeLabel{index}l"] = StaticText()
			self[f"typeLabel{index}h"] = StaticText()
			self[f"typeText{index}"] = StaticText()
		self["key_green"] = StaticText("Timer hinzufügen")
		self["key_yellow"] = StaticText("EPG-Suche")
		self["actions"] = ActionMap(["OkCancelActions",
									"ButtonSetupActions"],
													{"ok": self.keyExit,
													"cross_left": self.keyUp,
													"cross_right": self.keyDown,
													"cross_up": self.keyUp,
													"cross_down": self.keyDown,
													"channelup": self.keyUp,
													"channeldown": self.keyDown,
													"play": self.playTrailer,
													"playpause": self.playTrailer,
													"info": self.keyInfo,
													"green": self.keyGreen,
		 											"yellow": self.openEPGSearch,
													"cancel": self.keyExit}, -1)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		for widget, iconfile in [("isTopTip", "top.png"), ("isNew", "new.png"), ("isTipOfTheDay", "tip.png"),
								("hasTimer", "timer.png"), ("isIMDB", "imdb.png"), ("isTMDB", "tmdb.png")]:
			self[widget].instance.setPixmapFromFile(f"{tvglobals.ICONPATH}{iconfile}")
		for icon in [("play", "play.png"), ("info", "info.png"), ("playButton", "playbutton.png")]:
			imgfile = join(tvglobals.ICONPATH, icon[1])
			if exists(imgfile):
				self[icon[0]].instance.setPixmapFromFile(imgfile)
			self[icon[0]].hide()
		callInThread(self.showAssetDetails, self.assetId, fullscreen=True)

	def keyGreen(self):
		currdatetime = datetime.today().astimezone()
		hasTimer = self.isAlreadyListed(self.timeStartEnd, self.serviceRef, currdatetime, self.getTimerlist())  # timespan, sref
		if not hasTimer:
			startTs, endTs = self.splitTimespan(self.timeStartEnd.split(" - "), currdatetime)  #  e.g. '20:15 - 21:45'
			startTs -= int(config.recording.margin_before.value) * 60
			endTs += int(config.recording.margin_after.value) * 60
			data = (startTs, endTs, self.assetTitle, self.subLine, None)
			self.addE2Timer(ServiceReference(self.serviceRef), data)

	def addE2Timer(self, serviceRef, data):
		newEntry = RecordTimerEntry(serviceRef, checkOldTimers=False, dirname=preferredTimerPath(), fixDescription=True, *data)
		self.session.openWithCallback(boundFunction(self.finishKeyGreen), RecordTimerEdit, newEntry)

	def finishKeyGreen(self, answer):
		if answer and not isinstance(answer, bool):  # Special case for close recursive.
			if answer[0]:
				self.session.nav.RecordTimer.record(answer[1])
				self["hasTimer"].show()
				self["key_green"].setText("")

	def keyUp(self):
		self["longDescription"].pageUp()

	def keyDown(self):
		self["longDescription"].pageDown()

	def keyExit(self):
		self.close()


class TVtipsBox(Screen):
	skin = """
	<screen name="TVtips" position="50,center" size="410,264" flags="wfNoBorder" backgroundColor="#16000000" resolution="1280,720" title="TV Spielfilm Tipps">
		<eLabel position="0,0" size="410,264" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="406,260" zPosition="-2" />
		<eLabel name="TVSPro_line" position="2,38" size="406,2" backgroundColor=" #0027153c, #00101093, black, horizontal" zPosition="10" />
		<eLabel name="TVSPro_line" position="2,234" size="406,2" backgroundColor=" #0027153c, #00101093, black, horizontal" zPosition="10" />
		<eLabel position="2,2" size="406,36" backgroundColor=" #051a264d, #10304070, #051a264d, horizontal" zPosition="0" />
		<widget name="image" position="6,42" size="202,158" alphatest="blend" scaleFlags="keepAspect" zPosition="1" />
		<widget name="picon" position="258,82" size="100,60" alphatest="blend" scaleFlags="keepAspect" zPosition="1" />
		<widget name="hasTimer" position="359,82" size="14,14" alphatest="blend" zPosition="1" />
		<widget source="channelName" render="Label" position="212,42" size="194,36" font="Regular; 24" halign="center" valign="center" foregroundColor="#0092cbdf" backgroundColor="#16000000" transparent="1" />
		<widget source="timeStartEnd" render="Label" position="212,148" size="194,26" font="Regular;20" backgroundColor="#16000000" transparent="1" halign="center" />
		<widget source="titleLength" render="Label" position="212,174" size="194,26" font="Regular;20" foregroundColor="grey" backgroundColor="#16000000" transparent="1" halign="center" />
		<widget source="headline" render="Label" position="2,1" size="406,36" font="Regular; 24" wrap="ellipsis" backgroundColor="#16000000" zPosition="1" halign="center" valign="center" transparent="1" />
		<widget source="title" render="Label" position="10,204" size="396,28" font="Regular;20" wrap="ellipsis" foregroundColor="#0092cbdf" backgroundColor="#16000000" halign="left" valign="center" transparent="1" />
		<widget source="genreBroad" render="Label" position="70,236" size="286,24" font="Regular; 18" backgroundColor="#16000000" transparent="1" halign="left" valign="center" />
		<eLabel text="Genre :" position="10,236" size="66,24" font="Regular;18" backgroundColor="#16000000" transparent="1" halign="left" valign="center" />
		<widget source="yearCountry" render="Label" position="278,236" size="220,24" font="Regular; 18" backgroundColor="#16000000" transparent="1" halign="left" valign="center" />
		<widget name="thumb" position="362,91" size="40,40" alphatest="blend" zPosition="1" />
		<widget name="isTopTip" position="222,86" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isTipOfTheDay" position="222,106" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isNew" position="222,126" size="28,14" alphatest="blend" zPosition="1" />
	</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		for widget in ["headline", "title", "timeStartEnd", "genreBroad", "channelName", "titleLength",
				 		"yearCountry", "imdbRating", "fskText", "editorial", "conclusion"]:
			self[widget] = StaticText()
		for widget in ["isTopTip", "isTipOfTheDay", "isNew", "fsk", "thumb", "image", "picon", "hasTimer"]:
			self[widget] = Pixmap()
		self.isVisible = False

	def showDialog(self):
		self.isVisible = True
		self.show()

	def hideDialog(self):
		self.isVisible = False
		self.hide()

	def getIsVisible(self):
		return self.isVisible

	def setText(self, widget, text):
		self[widget].setText(text)

	def setImage(self, widget, imagefile):
		self[widget].instance.setPixmapFromFile(imagefile)

	def showWidget(self, widget):
		self[widget].show()

	def hideWidget(self, widget):
		self[widget].hide()


class TVinfoBox(Screen):
	skin = """
	<screen name="TVinfoBox" position="390,432" size="500,110" flags="wfNoBorder" resolution="1280,720" title="TV Spielfilm Infobox">
		<eLabel position="0,0" size="500,110" backgroundColor="#00203060" zPosition="-1" />
		<eLabel position="2,2" size="496,106" zPosition="-1" />
		<widget source="info" render="Label" position="5,5" size="490,100" font="Regular;24" halign="center" valign="center" />
	</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["info"] = StaticText()
		self.isVisible = False
		self.tvinfoboxTimer = eTimer()
		self.tvinfoboxTimer.callback.append(self.hideDialog)

	def showDialog(self, info, timeout):
		self["info"].setText(info)
		self.isVisible = True
		self.show()
		self.tvinfoboxTimer.start(timeout, True)

	def hideDialog(self):
		self.tvinfoboxTimer.stop()
		self.isVisible = False
		self.hide()

	def getIsVisible(self):
		return self.isVisible


class TVupdate(Screen):
	skin = """
	<screen name="TVupdate" position="820,250" size="410,182" flags="wfNoBorder" resolution="1280,720" title="TV Spielfilm EPG-Update">
		<eLabel name="TVSPro_bg" position="2,2" size="406,32" backgroundColor="black,#203060,horizontal" zPosition="-1" />
		<eLabel name="TVSPro_line" position="2,34" size="406,2" backgroundColor=" #27153c , #101093, black , horizontal" zPosition="10" />
		<eLabel position="0,0" size="410,182" backgroundColor="#203060" zPosition="-3" />
		<eLabel position="2,2" size="406,178" backgroundColor="#10060613" zPosition="-2" />
		<widget source="headline" render="Label" position="10,2" size="400,32" font="Regular;24" transparent="1" halign="left" valign="center"/>
		<widget source="progressHdr0" render="Label" position="10,38" size="390,28" font="Regular;18" wrap="ellipsis" transparent="1" valign="bottom" />
		<widget name="progressBar0" position="80,68" size="320,20" foregroundColor="#203060" zPosition="1" backgroundColor="#505050" />
		<widget source="progressTxt0" render="Label" position="10,70" size="68,16" font="Regular;14" foregroundColor="yellow" backgroundColor="#16000000" transparent="0" halign="center" valign="top" zPosition="2" />
		<eLabel name="" position="8,68" size="72,20" zPosition="-1" backgroundColor="#324b96" />
		<widget source="progressHdr1" render="Label" position="10,90" size="390,28" font="Regular;18" wrap="ellipsis" transparent="1" valign="bottom" />
		<widget name="progressBar1" position="80,120" size="320,20" foregroundColor="#203060" backgroundColor="#505050" />
		<widget source="progressTxt1" render="Label" position="10,122" size="68,16" font="Regular;14" foregroundColor="yellow" backgroundColor="#16000000" transparent="0" halign="center" valign="top" zPosition="2" />
		<eLabel name="" position="8,120" size="72,20" zPosition="-1" backgroundColor="#324b96" valign="top" halign="center" />
		<widget source="key_yellow" render="Label" position="36,148" size="120,24" font="Regular;18" transparent="1" halign="left" valign="center"/>
		<widget source="key_blue" render="Label" position="176,148" size="160,24" font="Regular;18" transparent="1" halign="left" valign="center"/>
		<eLabel name="button_yellow" position="20,146" size="6,30" backgroundColor="#7a6213,#e6c619,vertical" zPosition="1" />
		<eLabel name="blue" position="160,146" size="6,30" backgroundColor="#101093,#4040ff,vertical" zPosition="1" />
	</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["headline"] = StaticText()
		for index in range(2):
			self[f"progressHdr{index}"] = StaticText()
			self[f"progressBar{index}"] = ProgressBar()
			self[f"progressTxt{index}"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self.isVisible = False
		self.wasVisible = False

	def showDialog(self):
		self.wasVisible = False
		self.isVisible = True
		self.show()

	def hideDialog(self, status):
		self.wasVisible = status
		self.isVisible = False
		self.hide()

	def getIsVisible(self):
		return self.isVisible

	def getWasVisible(self):
		return self.wasVisible

	def setRange(self, widget, range):
		self[widget].setRange(range)

	def setValue(self, widget, value):
		self[widget].setValue(value)

	def setText(self, widget, text):
		self[widget].setText(text)


class TVsettingsLocationBox(LocationBox):
	def __init__(self, session, currDir):
		inhibit = defaultInhibitDirs[:]
		inhibit.remove("/usr")
		inhibit.remove("/share")
		if currDir == "":
			currDir = None
		LocationBox.__init__(self, session, text="Wo sollen die TVS-EPG Daten zwischengespeichert werden (Cache)?", currDir=currDir, inhibitDirs=inhibit)
		self.skinName = ["WeatherSettingsLocationBox", "LocationBox"]


class TVoverview(TVhelper, Screen):
	skin = """
	<screen name="TVoverview" position="10,10" size="1260,700" flags="wfNoBorder" resolution="1280,720" backgroundColor="#16000000" title="TV Spielfilm Übersicht">
		<eLabel name="Gradient_BlueBlack" position="0,0" size="120,70" zPosition="-1" backgroundColor="#10060613" />
		<eLabel name="Gradient_BlueBlack" position="0,64" size="1260,590" zPosition="-10" backgroundColor="#10060613" />
		<eLabel name="TV_bg" position="0,0" size="1260,60" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="0,60" size="1260,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="740,362" size="510,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="740,582" size="510,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="0,652" size="1260,2" backgroundColor=" #0027153c , #00101093 , black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="70,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
		<widget source="reviewdate" render="Label" position="0,2" size="1260,30" font="Regular; 20" foregroundColor="white" backgroundColor="#16000000" halign="center" valign="center" zPosition="12" transparent="1" />
		<widget source="global.CurrentTime" render="Label" position="1110,0" size="140,60" font="Regular; 46" noWrap="1" halign="center" valign="bottom" foregroundColor="white" backgroundColor="#16000000" zPosition="12" transparent="1">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget source="global.CurrentTime" render="Label" position="1000,2" size="100,26" font="Regular;16" noWrap="1" halign="right" valign="bottom" foregroundColor="white" backgroundColor="#16000000" zPosition="12" transparent="1">
			<convert type="ClockToText">Format:%A</convert>
		</widget>
		<widget source="global.CurrentTime" render="Label" position="1000,26" size="100,26" font="Regular;16" noWrap="1" halign="right" valign="bottom" foregroundColor="white" backgroundColor="#16000000" zPosition="12" transparent="1">
			<convert type="ClockToText">Format:%e. %B</convert>
		</widget>
		<widget source="menuList" render="Listbox" position="4,70" size="724,576" itemCornerRadiusSelected="6" itemGradientSelected=" black, #203060, black, horizontal" enableWrapAround="1" foregroundColorSelected="white" backgroundColor="#16000000" transparent="1" scrollbarMode="showOnDemand" scrollbarBorderWidth="1" scrollbarWidth="10" scrollbarBorderColor="blue" scrollbarForegroundColor="#203060">
			<convert type="TemplatedMultiContent">{"template": [
				MultiContentEntryPixmapAlphaBlend(pos=(6,4), size=(64,38), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER|BT_SCALE, png=1),  # picon
				MultiContentEntryText(pos=(78,0), size=(100,16), font=1, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS, color=0x00ffff, text=2),  # channelName
				MultiContentEntryText(pos=(78,18), size=(100,16), font=1, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, color=0x00ff00, text=3),  # time
				MultiContentEntryProgress(pos=(80,38), size=(88,6), borderWidth=1, foreColor=0xcbcbcb, percent=-4),  # progress
				MultiContentEntryText(pos=(184,0), size=(480,26), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS, text=5),  # title
				MultiContentEntryText(pos=(184,22), size=(480,22), font=1, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS, text=6),  # info
				MultiContentEntryPixmapAlphaBlend(pos=(666,0), size=(40,14), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=7),  # icon0
				MultiContentEntryPixmapAlphaBlend(pos=(666,16), size=(40,14), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=8),  # icon1
				MultiContentEntryPixmapAlphaBlend(pos=(666,32), size=(40,14), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=9),  # icon2
				MultiContentEntryPixmapAlphaBlend(pos=(56,0), size=(14,14), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=10)  # icon3
				],
				"fonts": [gFont("Regular",20),gFont("Regular",16),gFont("Regular",14)],
				"itemHeight":48
				}</convert>
		</widget>
		<eLabel position="8,1020" size="720,22" backgroundColor="grey" zPosition="-1" />
		<widget source="longStatus" render="Label" conditional="longStatus" position="0,30" size="1260,26" font="Regular;16" foregroundColor="#92cbdf" backgroundColor=" black, #00203060, horizontal" halign="center" valign="center" zPosition="10">
			<convert type="ConditionalShowHide" />
		</widget>
		<eLabel name="" position="386,32" size="64,24" zPosition="8" backgroundColor="#203060" />
		<widget name="progressBar" position="450,32" size="430,24" foregroundColor="#203060" backgroundColor="#505050" transparent="1" zPosition="8" />
		<widget source="progressTxt" render="Label" position="388,34" size="60,20" font="Regular; 16" foregroundColor="yellow" backgroundColor="#16000000" transparent="0" halign="center" valign="center" zPosition="9" />
		<widget source="shortStatus" render="Label" position="452,34" size="426,20" font="Regular;16" foregroundColor="#ffffff" transparent="1" halign="left" valign="center" wrap="ellipsis" zPosition="9" />
		<widget name="picon" position="760,210" size="147,88" alphatest="blend" scaleFlags="keepAspect" zPosition="1" />
		<widget source="channelName" render="Label" position="740,178" size="187,32" font="Regular; 24" halign="center" foregroundColor="#92cbdf" backgroundColor="#16000000" transparent="1" />
		<widget name="image" position="936,66" size="318,238" alphatest="blend" scaleFlags="keepAspect" zPosition="1" />
		<widget name="playButton" position="1060,160" size="60,60" alphatest="blend" zPosition="2" />
		<widget name="fsk" position="940,260" size="40,40" alphatest="blend" zPosition="2" />
		<widget name="isTopTip" position="1010,310" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isTipOfTheDay" position="942,310" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isNew" position="976,310" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isIMDB" position="1078,310" size="28,14" alphatest="blend" zPosition="3" />
		<widget name="isTMDB" position="1044,310" size="28,14" alphatest="blend" zPosition="3" />
		<widget name="hasTimer" position="884,212" size="14,14" alphatest="blend" zPosition="3" />
		<widget source="timeStartEnd" render="Label" position="748,302" size="170,24" font="Regular;24" halign="center" valign="center" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel0l" render="Label" position="760,70" size="90,24" font="Regular; 16" halign="right" valign="center" foregroundColor="#10333333" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel0h" render="Label" position="760,70" size="90,24" font="Regular; 16" halign="right" valign="center" foregroundColor="white" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots0" position="860,74" size="46,14" alphatest="blend" />
		<widget source="ratingLabel1l" render="Label" position="760,90" size="90,24" font="Regular; 16" valign="center" halign="right" foregroundColor="#10333333" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel1h" render="Label" position="760,90" size="90,24" font="Regular; 16" valign="center" halign="right" foregroundColor="white" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots1" position="860,94" size="46,14" alphatest="blend" />
		<widget source="ratingLabel2l" render="Label" position="760,110" size="90,24" font="Regular; 16" valign="center" halign="right" foregroundColor="#10333333" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel2h" render="Label" position="760,110" size="90,24" font="Regular; 16" valign="center" halign="right" foregroundColor="white" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots2" position="860,114" size="45,15" alphatest="blend" />
		<widget source="ratingLabel3l" render="Label" position="760,130" size="90,24" font="Regular; 16" valign="center" halign="right" foregroundColor="#10333333" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel3h" render="Label" position="760,130" size="90,24" font="Regular; 16" valign="center" halign="right" foregroundColor="white" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots3" position="860,134" size="45,15" alphatest="blend" />
		<widget source="ratingLabel4l" render="Label" position="760,150" size="90,24" font="Regular; 16" valign="center" halign="right" foregroundColor="#10333333" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget source="ratingLabel4h" render="Label" position="760,150" size="90,24" font="Regular; 16" valign="center" halign="right" foregroundColor="white" zPosition="0" backgroundColor="#16000000" transparent="1" />
		<widget name="ratingDots4" position="860,154" size="45,15" alphatest="blend" />
		<widget source="imdbRating" render="Label" position="1112,308" size="140,18" font="Regular; 14" foregroundColor="yellow" halign="center" noWrap="1" zPosition="2" backgroundColor="#16000000" transparent="1" />
		<widget name="thumb" position="726,295" size="40,40" alphatest="blend" zPosition="2" />
		<widget source="editorial" render="Label" position="740,584" size="510,24" font="Regular; 16" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="conclusion" render="Label" position="740,602" size="510,24" font="Regular; 18" foregroundColor="#92cbdf" backgroundColor="#16000000" transparent="1" />
		<widget source="repeatHint" render="RunningText" position="740,626" size="510,24" font="Regular;18" options="movetype=running,startpoint=0,startdelay=2000,wrap=0,always=0,repeat=2,oneshot=1" halign="left" noWrap="1" backgroundColor="#16000000" transparent="1" />
		<widget source="title" render="RunningText" options="movetype=running,startpoint=0,startdelay=2000,wrap=0,always=0,repeat=2,oneshot=1" position="740,330" size="510,32" font="Regular; 24" halign="left" noWrap="1" foregroundColor="#92cbdf" backgroundColor="#16000000" transparent="1" />
		<widget source="longDescription" render="RunningText" options="movetype=running,startdelay=6000,steptime=60,direction=top,startpoint=0,wrap=1,always=0,repeat=2,oneshot=1" position="740,366" size="510,214" font="Regular;21" backgroundColor="#16000000" transparent="1" />
		<eLabel name="button_red" position="10,660" size="6,36" backgroundColor=" #00821c17, #00fe0000, vertical" zPosition="1" />
		<eLabel name="button_green" position="150,660" size="6,36" backgroundColor=" #00006600, #0024a424, vertical" zPosition="1" />
		<eLabel name="yellow" position="306,660" size="6,36" backgroundColor=" #007a6213, #00e6c619, vertical" zPosition="1" />
		<widget source="key_red" render="Label" position="20,666" size="130,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_green" render="Label" position="160,666" size="150,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_yellow" render="Label" position="316,666" size="140,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<eLabel text=" Woche -" position="708,666" size="76,26" font="Regular;18" valign="center" halign="right" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<eLabel text="Woche + " position="838,666" size="76,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_info" render="Label" position="970,666" size="120,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_play" render="Label" position="1116,666" size="160,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<eLabel text="Tag -" position="414,666" size="54,26" font="Regular; 18" valign="center" halign="right" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<eLabel text="Tag +" position="526,666" size="54,26" font="Regular; 18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<eLabel text="Details" position="636,666" size="66,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<ePixmap position="920,664" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/info.png" alphatest="blend" zPosition="1" />
		<ePixmap position="474,664" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/ch_plus_minus.png" alphatest="blend" zPosition="1" />
		<ePixmap position="788,664" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/left0right.png" alphatest="blend" zPosition="1" />
		<ePixmap position="586,664" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/ok.png" alphatest="blend" zPosition="1" />
		<widget name="play" position="1094,664" size="20,28" alphatest="blend" zPosition="2" />
		<eLabel name="" position="936,306" size="318,22" zPosition="-1" backgroundColor="#505050" cornerRadius="2" />
		<eLabel name="" position="937,307" size="316,20" zPosition="0" backgroundColor="#16000000" cornerRadius="2" />
		<eLabel name="" position="1007,308" size="1,18" zPosition="10" backgroundColor="#505050" />
		<eLabel name="" position="1109,308" size="1,18" zPosition="10" backgroundColor="#505050" />
		<eLabel name="" position="973,308" size="1,18" zPosition="10" backgroundColor="#505050" />
		<eLabel name="" position="1041,308" size="1,18" zPosition="10" backgroundColor="#505050" />
		<eLabel name="" position="1075,308" size="1,18" zPosition="10" backgroundColor="#505050" />
	</screen>
	"""

	def __init__(self, session, userspan=""):
		self.session = session
		self.spanStarts, self.spanDurance = (userspan[0], userspan[1]) if userspan else ("", config.plugins.tvspielfilm.durance_n.value)
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		self.assetTitle = ""
		self.trailerUrl = ""
		self.filterIndex = config.plugins.tvspielfilm.filter.value
		self.skinlist = []
		self.assetslist = []
		self.currentAssetId = ""
		self.currdatetime = datetime.today().astimezone()
		self.currdaydelta = 0
		self.allAssetsCount = 0
		self.allImagesCount = 0
		self.lenIMPORTDICT = 0
		self.lenskinlist = 0
		self.dataBases = []
		self.currImdbId = ""
		self.currServiceRef = ""
		self.titleLenStr = ""
		self.loadAllEPGactive = False
		self.loadAllEPGstop = False
		Screen.__init__(self, session)
		self["release"] = StaticText(tvglobals.RELEASE)
		for wname in ["reviewdate", "longStatus", "progressTxt", "shortStatus", "channelName", "timeStartEnd", "imdbRating", "repeatHint",
						"title", "editorial", "conclusion", "longDescription", "key_info", "key_play"]:
			self[wname] = StaticText()
		for wname in ["picon", "image", "playButton", "isTopTip", "isTipOfTheDay", "isNew", "isIMDB", "isTMDB", "hasTimer", "thumb",
						"fsk", "play"]:
			self[wname] = Pixmap()
			self[wname].hide()
		for index in range(5):
			self[f"ratingLabel{index}l"] = StaticText()
			self[f"ratingLabel{index}h"] = StaticText()
			self[f"ratingDots{index}"] = Pixmap()
			self[f"ratingDots{index}"].hide()
		self["progressBar"] = ProgressBar()
		self["menuList"] = List()
		self["key_red"] = StaticText()
		self["key_green"] = StaticText("Timer hinzufügen")
		self["key_yellow"] = StaticText("EPG-Suche")
		self["actions"] = ActionMap(["OkCancelActions",
									"ButtonSetupActions"],
													{"ok": self.keyOk,
													"play": self.playTrailer,
													"playpause": self.playTrailer,
													"red": self.keyRed,
													"green": self.keyGreen,
		 											"yellow": self.openEPGSearch,
													"channeldown": self.prevday,
													"channelup": self.nextday,
													"previous": self.prevweek,
													"next": self.nextweek,
													"info": self.keyInfo,
													"cancel": self.keyExit}, -1)
		tvglobals.IMPORTDICT = readImportedFile()  # lade importierte Senderdaten
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self["menuList"].onSelectionChanged.append(self.showCurrentAsset)
		self["key_red"].setText(f"Filter: {ASSETFILTERS[self.filterIndex][0]}")
		for widget, iconfile in [("isTopTip", "top.png"), ("isNew", "new.png"), ("isTipOfTheDay", "tip.png"),
								("hasTimer", "timer.png"), ("isIMDB", "imdb.png"), ("isTMDB", "tmdb.png")]:
			self[widget].instance.setPixmapFromFile(f"{tvglobals.ICONPATH}{iconfile}")
		for icon in [("play", "play.png"), ("playButton", "playbutton.png")]:
			imgfile = join(tvglobals.ICONPATH, icon[1])
			if exists(imgfile):
				self[icon[0]].instance.setPixmapFromFile(imgfile)
			self[icon[0]].hide()
		self.startLoadAllEPG()

	def loadAllEPG(self, FinishOnStop):
		self.loadAllEPGactive = True
		todaydate = self.currdatetime.strftime("%F")
		now = datetime.today()
		now -= timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)  # round to last 15 minutes in case of 'Jetzt im TV'
		spanStarts = self.spanStarts or now.strftime("%H:%M")
		self["longStatus"].setText("")
		self.lenIMPORTDICT = len(tvglobals.IMPORTDICT)
		self["progressBar"].setRange((0, self.lenIMPORTDICT))
		allAssets = {}
		self.allAssetsCount = 0
		self.allImagesCount = 0
		self.assetslist = []
		self.skinlist = []
		downloaded = False
		for index, item in enumerate(tvglobals.IMPORTDICT.items()):
			if self.loadAllEPGstop:
				break
			self["progressBar"].setValue(index)
			self["progressTxt"].setText(f"{index + 1}/{self.lenIMPORTDICT}")
			self["shortStatus"].setText(f"Lade TVS-EPG Daten für '{item[1][1]}'")
			channelId = item[0]
			startslist = []  # avoids displaying duplicate entries for combination channels such as 'SWF/SR'
			downloaded, assetsdict = getAllAssets(channelId, todaydate, spanStarts)
			if assetsdict:
				for asset in assetsdict:
					if self.loadAllEPGstop:
						break
					startTime_iso, endTime_iso = asset.get("startTime", ""), asset.get("endTime", "")  # e.g. '2024-11-24T22:05:00.000Z'
					startTime, endTime = datetime.fromisoformat(startTime_iso).astimezone(), datetime.fromisoformat(endTime_iso).astimezone()
					now = datetime.today().astimezone()
					hour, minute = spanStarts.split(":") if spanStarts else [now.strftime("%H"), now.strftime("%M")]  # spanstars empty = 'Jetzt im TV'
					spanEnds = self.currdatetime.replace(hour=int(hour), minute=int(minute)) + timedelta(minutes=int(self.spanDurance))
					if startTime and startTime.timestamp() < spanEnds.timestamp() and startTime not in startslist:  # begin of transmission still in the period?
						startslist.append(startTime)
						progress = -1
						if endTime:
							durance = endTime - startTime
							progress = int(((now - startTime) / durance) * 100) if durance else -1
						assetId = asset.get("assetId", "")
						title = unescape(asset.get("title", ""))
						time = asset.get("time", "").split(" | ")  # e.g. '20:15 - 21:45 | DAS ERSTE'
						timespan, channelName = (time[0], time[1]) if time and len(time) > 1 else ("", "")
						if not config.plugins.tvspielfilm.channelname.value:
							channelName = tvglobals.IMPORTDICT.get(channelId, ["", ""])[1]
						info = asset.get("info", "")
						isTopTip = asset.get("isTopTip", False)
						isTipOfTheDay = asset.get("isTipOfTheDay", False)
						isNew = asset.get("flags", {}).get("isNew", False)
						sref = tvglobals.IMPORTDICT.get(channelId, ["", ""])[0]
						imgurl = asset.get("image", {}).get("476x357", "")
						imgfile = join(f"{self.getTMPpath()}images/", imgurl[imgurl.rfind("/") + 1:]) if imgurl else ""
						if imgfile:
							self.allImagesCount += 1
						self.assetslist.append([assetId, channelId, channelName, timespan, progress, title, info, isTopTip, isTipOfTheDay, isNew, sref, imgurl, imgfile])
						self.allAssetsCount += 1
						if self.allAssetsCount == 1:  # immediate display of details after downloading the first asset
							self.showCurrentAsset()
				if downloaded:
					allAssets[channelId] = assetsdict
			self.refreshSkinlist()
		if self.loadAllEPGstop:
			FinishOnStop()
		elif spanStarts:  # don't save to cache on 'Jetzt im TV' because this has no pre-defined time period to save
			self.saveAllAssets(allAssets, todaydate, spanStarts)
		self.setLongstatus()
		self["progressBar"].setValue(0)
		self["progressTxt"].setText("")
		self["shortStatus"].setText("")
		self.showCurrentAsset()
		self.loadAllEPGactive = False

	def setLongstatus(self):
		if self.allAssetsCount == self.lenskinlist:
			self["longStatus"].setText(f"{self.allAssetsCount} Einträge und {self.allImagesCount} Bilder in insgesamt {self.lenIMPORTDICT} Sendern gefunden.")
		else:
			self["longStatus"].setText(f"{self.allAssetsCount} Einträge und {self.allImagesCount} Bilder in insgesamt {self.lenIMPORTDICT} Sendern gefunden. Gefilterte Einträge: {self.lenskinlist}")

	def refreshSkinlist(self):
		timerlist = self.getTimerlist()
		skinlist = []
		currfilter = ASSETFILTERS[self.filterIndex]
		for asset in self.assetslist:
			if currfilter[1]:  # is a filter set?
				leaveout = True
				for assetFlag in [(asset[7], "isTopTip"), (asset[8], "isTipOfTheDay"), (asset[9], "isNew")]:
					if assetFlag[0] and assetFlag[1] == currfilter[1]:
						leaveout = False
						break
				if leaveout:
					continue
			hasTimer = self.isAlreadyListed(asset[3], asset[10], self.currdatetime, timerlist)  # timespan, sref
			piconfile = self.getPiconFile(asset[1])
			piconpix = LoadPixmap(cached=True, path=piconfile) if piconfile and exists(piconfile) else None
			assetId, channelName, timespan, progress, title, info, sref = asset[0], asset[2], asset[3], asset[4], asset[5], asset[6], asset[10]
			icon0 = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}top.png") if asset[7] else None  # isTopTip
			icon1 = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}tip.png") if asset[8] else None  # isTipOfTheDay
			icon2 = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}new.png") if asset[9] else None  # isNew
			icon3 = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}timer.png") if hasTimer else None  # timer-icon
			skinlist.append((assetId, piconpix, channelName, timespan, progress, title, info, icon0, icon1, icon2, icon3, sref))
		if skinlist:
			self.skinlist = skinlist
			self.showCurrentAsset()
		else:
			skinlist.append(("", None, "", "", -1, "keine Einträge gefunden", f"Der Filter '{currfilter[0]}' liefert für diesen Zeitraum leider kein Ergebnis.", None, None, None, None, ""))
			self.skinlist = []
			self.hideCurrentAsset()
		self["menuList"].updateList(skinlist)
		self.lenskinlist = len(skinlist)

	def showCurrentAsset(self):
		if self.skinlist:
			current = min(self["menuList"].getCurrentIndex(), len(self.skinlist) - 1)
			assetId = self.skinlist[current][0]
			if assetId and assetId != self.currentAssetId:  # is a new asset?
				callInThread(self.showAssetDetails, assetId, False)

	def hideCurrentAsset(self):
		for widget in ["picon", "thumb", "image", "playButton"]:
			self[widget].hide()
		for assetFlag in ["isTopTip", "isNew", "isTipOfTheDay", "hasTimer", "isIMDB", "isTMDB", "fsk"]:
			self[assetFlag].hide()
		for index in range(len(["Anspruch", "Humor", "Action", "Spannung", "Erotik"])):
				self[f"ratingLabel{index}l"].setText("")
				self[f"ratingLabel{index}h"].setText("")
				self[f"ratingDots{index}"].hide()
		for widget in ["channelName", "imdbRating", "repeatHint", "title", "editorial", "conclusion", "timeStartEnd", "longDescription"]:
			self[widget].setText("")

	def keyOk(self):
		if self.skinlist:
			current = min(self["menuList"].getCurrentIndex(), len(self.skinlist) - 1)
			assetId = self.skinlist[current][0]
			self.session.open(TVfullscreen, assetId)

	def keyRed(self):
		self.filterIndex = (self.filterIndex + 1) % len(ASSETFILTERS)
		self["key_red"].setText(f"Filter: {ASSETFILTERS[self.filterIndex][0]}")
		self.refreshSkinlist()
		self.setLongstatus()

	def keyGreen(self):
		if self.skinlist:
			current = self["menuList"].getCurrentIndex()
			skinlist = self.skinlist[current]
			hasTimer = self.isAlreadyListed(skinlist[3], skinlist[11], self.currdatetime, self.getTimerlist())
			if not hasTimer:
				title = skinlist[5]
				shortdesc = skinlist[6]
				serviceRef = ServiceReference(skinlist[11])
				startTs, endTs = self.splitTimespan(skinlist[3].split(" - "), self.currdatetime)  #  e.g. '20:15 - 21:45'
				startTs -= int(config.recording.margin_before.value) * 60
				endTs += int(config.recording.margin_after.value) * 60
				data = (startTs, endTs, title, shortdesc, None)
				self.addE2Timer(serviceRef, data)

	def addE2Timer(self, serviceRef, data):
		newEntry = RecordTimerEntry(serviceRef, checkOldTimers=False, dirname=preferredTimerPath(), fixDescription=True, *data)
		self.session.openWithCallback(boundFunction(self.finishKeyGreen), RecordTimerEdit, newEntry)

	def finishKeyGreen(self, answer):
		if answer and not isinstance(answer, bool):  # Special case for close recursive.
			if answer[0]:
				self.session.nav.RecordTimer.record(answer[1])
				self["hasTimer"].show()
				self["key_green"].setText("")
				self.refreshSkinlist()

	def prevday(self):
		if self.currdaydelta == -7:
			self.tvinfobox.showDialog("Vergangene TVS-EPG Daten nur bis maximal 7 Tage danach verfügbar.", 2500)
		self.currdaydelta = max(self.currdaydelta - 1, -7)  # max 7 days in past
		self.startLoadAllEPG()

	def prevweek(self):
		if self.currdaydelta == -7:
			self.tvinfobox.showDialog("Vergangene TVS-EPG Daten nur bis maximal 7 Tage danach verfügbar.", 2500)
		self.currdaydelta = max(self.currdaydelta - 7, -7)  # max 7 days in past
		self.startLoadAllEPG()

	def nextday(self):
		if self.currdaydelta == 13:
			self.tvinfobox.showDialog("Zukünftige TVS-EPG Daten nur bis maximal 13 Tage im Voraus verfügbar.", 2500)
		self.currdaydelta = min(self.currdaydelta + 1, 13)  # max 13 days in future
		self.startLoadAllEPG()

	def nextweek(self):
		if self.currdaydelta == 13:
			self.tvinfobox.showDialog("Zukünftige TVS-EPG Daten nur bis maximal 13 Tage im Voraus verfügbar.", 2500)
		self.currdaydelta = min(self.currdaydelta + 7, 13)  # max 13 days in future
		self.startLoadAllEPG()

	def startLoadAllEPG(self):
		self.currdatetime = datetime.today().astimezone() + timedelta(days=self.currdaydelta)
		self.setReviewdate(False)
		self.setLongstatus()
		if self.loadAllEPGactive:
			self.loadAllEPGstop = True
		else:
			self.loadAllEPGstop = False
			callInThread(self.loadAllEPG, self.startLoadAllEPGfinish)

	def startLoadAllEPGfinish(self):
		self.loadAllEPGstop = False
		self.assetslist = []
		self.refreshSkinlist()
		callInThread(self.loadAllEPG, self.startLoadAllEPGfinish)  # restart interrupted thread with new currdatetime

	def keyExit(self):
		self.close()


class TVmain(TVhelper, Screen):
	skin = """
	<screen name="TVmain" position="center,center" size="320,450" resolution="1280,720" backgroundColor="#16000000" flags="wfNoBorder" title="TV Spielfilm Hauptmenü">
		<eLabel position="0,0" size="320,450" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="316,446" zPosition="-1" />
		<eLabel name="TV_bg" position="2,2" size="316,58" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="2,60" size="316,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="2,382" size="316,2" backgroundColor=" #0027153c , #00101093 , black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="2,407" size="316,2" backgroundColor=" #0027153c , #00101093 , black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="70,20" font="Regular;18" textBorderColor="#505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
		<widget source="mainmenu" render="Listbox" position="2,60" size="316,320" itemCornerRadiusSelected="4" itemGradientSelected=" #051a264d, #10304070, #051a264d, horizontal" enableWrapAround="1" foregroundColorSelected="white" backgroundColor="#16000000" transparent="1" scrollbarMode="showNever">
			<convert type="TemplatedMultiContent">{"template": [
				MultiContentEntryText(pos=(0,0), size=(316,40), font=0, color=0xffffff, flags=RT_HALIGN_CENTER|RT_VALIGN_CENTER, text=0)  # menutext
				],
				"fonts": [gFont("Regular",24)],
				"itemHeight":40
				}</convert>
		</widget>
		<eLabel text="von Mr.Servo - Skin von stein17 " position="0,386" size="320,18" font="Regular; 14" foregroundColor="#0092cbdf" backgroundColor="#00000000" transparent="1" zPosition="2" halign="center" />
		<eLabel name="button_red" position="70,414" size="6,30" backgroundColor=" #00821c17, #00fe0000, vertical" zPosition="1" />
		<widget source="key_red" render="Label" position="84,418" size="70,24" font="Regular;18" foregroundColor="#00ffffff" backgroundColor="#00000000" valign="center" transparent="1" zPosition="2" />
		<eLabel name="button_green" position="150,414" size="6,30" backgroundColor=" #00006600, #0024a424, vertical" zPosition="1" />
		<widget source="key_green" render="Label" position="164,418" size="140,24" font="Regular;18" foregroundColor="#00ffffff" backgroundColor="#00000000" valign="center" transparent="1" zPosition="1" />
		<ePixmap position="10,416" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/menu.png" alphatest="blend" zPosition="1" />
	</screen>
	"""

	def __init__(self, session):
		self.session = session
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		Screen.__init__(self, session)
		self.tvupdate = session.instantiateDialog(TVupdate)
		self.tvinfobox = session.instantiateDialog(TVinfoBox)
		self.tvtipsbox = session.instantiateDialog(TVtipsBox)
		self.updateActive = False
		self.updateStop = False
		self.tipslist = ""
		self.currTipId = ""
		self.currTipCnt = 0
		self.currdaydelta = 0
		self.currdatetime = datetime.today().astimezone()
		self.tvtipsboxTimer = eTimer()
		self.tvtipsboxTimer.callback.append(self.showNextTip)
		self.oldChannelName = config.plugins.tvspielfilm.channelname.value
		self["release"] = StaticText(tvglobals.RELEASE)
		self["mainmenu"] = List()
		self["key_red"] = StaticText("Import")
		self["key_green"] = StaticText()
		self["actions"] = ActionMap(["WizardActions",
									 "ColorActions",
									 "MenuActions"], {"ok": self.keyOk,
			   											"back": self.exit,
														"right": self.rightDown,
														"left": self.leftUp,
														"down": self.down,
														"up": self.up,
														"red": self.keyRed,
														"green": self.keyGreen,
														"yellow": self.keyYellow,
														"blue": self.keyBlue,
														"menu": self.config}, -1)
		tvglobals.IMPORTDICT = readImportedFile()  # lade importierte Senderdaten
		if not self.createTMPpaths():
			self.exit()
		self.cleanupCache()
		callInThread(self.getTips, self.getTipsCB)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		for widget, iconfile in [("isTopTip", "top.png"), ("isTipOfTheDay", "tip.png"), ("isNew", "new.png"), ("hasTimer", "timer.png")]:
			self.tvtipsbox.setImage(widget, f"{tvglobals.ICONPATH}{iconfile}")
		self.tvupdate.setText("headline", "Sammle TVS-EPG Daten")
		self.tvupdate.setText("key_yellow", "Abbruch")
		self.tvupdate.setText("key_blue", "Ein-/Ausblenden")
		self.selectMainMenu()

	def showTVtipsBox(self, delay):
		self.tvtipsbox.showDialog()
		self.tvtipsboxTimer.start(delay, False)
		self["key_green"].setText("Sendungsdetail")
		self.showNextTip()

	def showNextTip(self):
		if self.tipslist:
			self.showTip(self.currTipCnt)
			self.currTipCnt = (self.currTipCnt + 1) % len(self.tipslist)

	def hideTVtipsBox(self):
		self.tvtipsboxTimer.stop()
		self.tvtipsbox.hideDialog()
		self["key_green"].setText("Tipps anzeigen")

	def selectMainMenu(self):
		userspans = self.getActiveTimespans()
		usermenu = []
		for index, userspan in enumerate(userspans):  # build main menu
			usermenu.append((f"{userspan[0]} im TV", index, TVoverview, userspan))
		usermenu.append(("Jetzt im TV", 4, TVoverview, None))
		usermenu.append(("laufende Sendung", 5, None, None))
		usermenu.append(("TVS-EPG Datenupdate", 6))
		usermenu.append(("lösche TVS-EPG Cache", 7))
		self["mainmenu"].updateList(usermenu)

	def keyOk(self):
		current = self["mainmenu"].getCurrent()
		if current:
			if current[1] in [0, 1, 2, 3, 4]:
				self.hideTVtipsBox()
				self.tvupdate.hideDialog(self.tvupdate.getIsVisible())
				self.session.openWithCallback(self.returnOk1, current[2], current[3])
			elif current[1] == 5:
				self.hideTVtipsBox()
				self.tvupdate.hideDialog(self.tvupdate.getIsVisible())
				callInThread(showCurrentEvent, self.session, self.returnOk4)
			elif current[1] == 6:
				if self.updateActive:
					self.tvinfobox.showDialog("Das TVS-EPG Update läuft bereits.", 2500)
				else:
					msgtext = "\nTVS-EPG Update durchführen?\n\nDies gilt für die im Setup eingestellten Zeiträume,\nläuft im Hintergrund und kann einige Minuten dauern."
					self.session.openWithCallback(self.returnOk2, MessageBox, msgtext, MessageBox.TYPE_YESNO, timeout=10, default=False)
			elif current[1] == 7:
				if self.updateActive:
					self.tvinfobox.showDialog("Das TVS-EPG Update läuft gerade.\nDer TVS-EPG Zwischenspeicher kann daher im Moment nicht gelöscht werden.", 2500)
				else:
					msgtext = "\nTVS-EPG Zwischenspeicher löschen?\n\nDies kann bei Problemen hilfreich sein,\ndanach sollte ein TVS-EPG Datenupdate durchgefürt werden."
					self.session.openWithCallback(self.returnOk3, MessageBox, msgtext, MessageBox.TYPE_YESNO, timeout=10, default=False)

	def returnOk1(self):
		if self.tvupdate.getWasVisible():
			self.tvupdate.showDialog()
		if config.plugins.tvspielfilm.showtips.value == 2:  # show tips allways?
			self.showTVtipsBox(5000)

	def returnOk2(self, answer):
		if answer is True:
			self.updateStop = False
			callInThread(self.updateFutureEPG, visible=True)

	def returnOk3(self, answer):
		if answer is True:
			self.removeTMPpaths()
			self.createTMPpaths()
			self.tvinfobox.showDialog("TVS-EPG Zwischenspeicher (=Cache) erfolgreich gelöscht", 2500)

	def returnOk4(self, answer):
		if not answer:
			self.session.open(MessageBox, "Dieser Sender wird von TV Spielfilm nicht unterstützt.", type=MessageBox.TYPE_INFO, timeout=2, close_on_any_key=True)

	def keyRed(self):
		if self.updateActive:
			self.tvinfobox.showDialog("Das TVS-EPG Update läuft gerade.\nDer Import kann daher im Moment nicht durchgeführt werden.", 2500)
		else:
			msgtext = "Importiere TV Spielfilm Sender?\nACHTUNG: Der TVS-EPG Zwischenspeicher (=Cache)\nmuß hierfür unwiderruflich gelöscht werden.\nDanach sollte ein TVS-EPG Datenupdate erfolgen.\n\nSind Sie sicher das Sie das wollen?"
			self.session.openWithCallback(self.returnRed, MessageBox, msgtext, MessageBox.TYPE_YESNO, timeout=10, default=False)

	def returnRed(self, answer):
		if answer is True:
			self.session.openWithCallback(self.importfileCB, TVimport)

	def importfileCB(self):
		self.removeTMPpaths()
		self.createTMPpaths()
		self.selectMainMenu()

	def keyGreen(self):
		if self.tvtipsbox.getIsVisible():
			self.tvupdate.hideDialog(self.tvupdate.getIsVisible())
			self.hideTVtipsBox()
			self.session.openWithCallback(self.returnOk1, TVfullscreen, self.currTipId)
		else:
			self.showTVtipsBox(5000)

	def keyYellow(self):
		if self.updateActive:
			self.session.openWithCallback(self.returnYellow, MessageBox, '\nTVS-EPG Update abbrechen?', MessageBox.TYPE_YESNO, timeout=10, default=False)

	def returnYellow(self, answer):
		if answer is True:
			self.updateStop = True

	def keyBlue(self):
		if self.tvupdate.getIsVisible():
			self.tvupdate.hideDialog(True)
		else:
			self.tvupdate.showDialog(False)

	def down(self):
		self["mainmenu"].down()

	def up(self):
		self["mainmenu"].up()

	def leftUp(self):
		self["mainmenu"].pageUp()

	def rightDown(self):
		self["mainmenu"].pageDown()

	def config(self):
		self.hideTVtipsBox()
		self.oldChannelName = config.plugins.tvspielfilm.channelname.value
		self.session.openWithCallback(self.configCB, TVsetup)

	def configCB(self):
		if self.oldChannelName != config.plugins.tvspielfilm.channelname.value:
			callInThread(self.getTips, self.getTipsCB)
		if config.plugins.tvspielfilm.showtips.value == 2:  # show tips allways
			self.showTVtipsBox(5000)
		self.selectMainMenu()

	def exit(self):
		if self.updateActive:
			self.session.openWithCallback(self.returnExit, MessageBox, '\nDas TVS-EPG Update läuft gerade!\nTVS-EPG Update abbrechen und Plugin verlassen?', MessageBox.TYPE_YESNO, timeout=10, default=False)
		else:
			self.returnExit(True)

	def returnExit(self, answer):
		if answer is True:
			self.updateStop = True
			self.session.deleteDialog(self.tvupdate)
			self.session.deleteDialog(self.tvinfobox)
			self.session.deleteDialog(self.tvtipsbox)
			self.close()

	def cleanupCache(self):  # delete older asset overviews, detailed assets and images
		latest = datetime.today() - timedelta(days=config.plugins.tvspielfilm.keepcache.value)
		ldate = latest.replace(hour=0, minute=0, second=0, microsecond=0)
		for filename in glob(join(f"{self.getTMPpath()}cache/", "allAssets*T*.json")):
			if datetime.strptime(filename.split("/")[-1][9:19], "%Y-%m-%d") < ldate:  # keepcache or older?
				remove(filename)
		for filenames in [glob(join(f"{self.getTMPpath()}assets/", "*.*")), glob(join(f"{self.getTMPpath()}images/", "*.*"))]:
			for filename in filenames:
				if (latest - datetime.fromtimestamp(getmtime(filename))).total_seconds() > 86400:  # older than 24h?
					remove(filename)

	def createTMPpaths(self):
		try:
			tmppath = self.getTMPpath()
			for path in [tmppath, f"{tmppath}cache/", f"{tmppath}assets/", f"{tmppath}images/"]:
				if not exists(path):
					makedirs(path, exist_ok=True)
		except OSError as error:
			self.session.open(MessageBox, "Dateipfad für Boxbilder konnte nicht neu angelegt werden:\n'%s'" % error, type=MessageBox.TYPE_ERROR, timeout=2, close_on_any_key=True)
			return False
		return True

	def removeTMPpaths(self):
		tmppath = self.getTMPpath()
		for path in [f"{tmppath}cache/", f"{tmppath}assets/", f"{tmppath}images/", tmppath]:
			if exists(path):
				rmtree(path)

	def updateFutureEPG(self, visible=False):  # visible=False is mandatory
		self.updateActive = True
		self.createTMPpaths()
		self.cleanupCache()
		if visible:
			self.tvupdate.showDialog()
		timespans = self.getActiveTimespans()
		len_total = 0
		for timespan in timespans:  # calculate len_total
			len_total += timespan[2] + 1  # days of a timespan to be cached
		progress = 0
		if timespans:
			importdict = tvglobals.IMPORTDICT  # mandatory if the thread should continue to run even if the plugin is terminated
			len_importdict = len(importdict)
			self.setProgressRange(1, (0, len_importdict))
			allAssets = {}
			for timespan in timespans:  # go through all defined timespans (A to D)
				if visible and self.updateStop:
					break
				spanstart = timespan[0]
				spancache = timespan[2]
				self.setProgressRange(0, (0, len_total))
				for index0, day in enumerate(range(spancache + 1)):  # from today up to next to be cached days
					if visible and self.updateStop:
						break
					date = datetime.today() + timedelta(days=day)
					datestr = date.strftime("%F")
					weekday = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][date.weekday()] if index0 else "heute"
					progress += 1
					self.setProgressValues(0, (f"Zeitraum: '{spanstart}' | {weekday} (+{index0}/+{spancache} Tage)", progress, f"{progress}/{len_total}"))
					for index1, item in enumerate(importdict.items()):
						if visible and self.updateStop:
							break
						self.setProgressValues(1, (f"Sender: '{item[1][1]}'", index1, f"{index1}/{len_importdict}"))
						channelId = item[0]
						downloaded, assetsdict = getAllAssets(channelId, datestr, spanstart, noLoadExisting=True)
						if downloaded:
							allAssets[channelId] = assetsdict
					if not self.saveAllAssets(allAssets, datestr, spanstart):
						self.updateStop = True  # force stop thread due to OS-error
		self.tvupdate.hideDialog(False)
		self.tvinfobox.showDialog("TVS-EPG Update erfolgreich abgebrochen." if self.updateStop else "TVS-EPG Update erfolgreich beendet.", 2500)
		self.updateStop = False
		self.updateActive = False

	def getActiveTimespans(self):
		timespans = []
		userconfigs = [(config.plugins.tvspielfilm.starttime_a.value, config.plugins.tvspielfilm.durance_a.value, config.plugins.tvspielfilm.cache_a.value),
			 			(config.plugins.tvspielfilm.starttime_b.value, config.plugins.tvspielfilm.durance_b.value, config.plugins.tvspielfilm.cache_b.value),
						(config.plugins.tvspielfilm.starttime_c.value, config.plugins.tvspielfilm.durance_c.value, config.plugins.tvspielfilm.cache_c.value),
						(config.plugins.tvspielfilm.starttime_d.value, config.plugins.tvspielfilm.durance_d.value, config.plugins.tvspielfilm.cache_d.value)
						]
		for index, userconfig in enumerate(userconfigs):
			if self.getUserMenuUsage(index):
				timespans.append((STARTTIMES[userconfig[0]], userconfig[1], userconfig[2]))
		return timespans

	def showTip(self, index):
		tip = self.tipslist[index]
		headline = f"Tipp des Tages ({index + 1}/{len(self.tipslist)})"
		for text, widget in [(headline, "headline"), (tip[0], "title"), (tip[1], "timeStartEnd"), (tip[2], "genreBroad"), (tip[3], "channelName"), (tip[4], "titleLength"),
							(tip[5], "yearCountry"), (tip[6], "imdbRating"), (tip[7], "fskText"), ("Meinung der Redaktion:" if tip[8] else "", "editorial"), (tip[8], "conclusion")]:
			self.tvtipsbox.setText(widget, text)
		for tipFlag, widget in [(tip[9], "isTopTip"), (tip[10], "isTipOfTheDay"), (tip[11], "isNew")]:
			if tipFlag:
				self.tvtipsbox.showWidget(widget)
			else:
				self.tvtipsbox.hideWidget(widget)
		fsk = tip[12]
		fskfile = join(tvglobals.ICONPATH, f"FSK_{fsk}.png") if fsk else join(tvglobals.ICONPATH, "FSK_NA.png")
		self.tvtipsbox.setImage("fsk", fskfile)
		self.tvtipsbox.showWidget("fsk")
		thumbIdNumeric = tip[13]
		if thumbIdNumeric != -1:
			thumbfile = join(tvglobals.ICONPATH, f"thumb{thumbIdNumeric}.png")
			if exists(thumbfile):
				self.tvtipsbox.setImage("thumb", thumbfile)
				self.tvtipsbox.showWidget("thumb")
			else:
				self.tvtipsbox.hideWidget("thumb")
		imgurl = tip[14]
		imgfile = join(f"{self.getTMPpath()}images/", f"{imgurl[imgurl.rfind('/') + 1:]}") if imgurl else ""
		if exists(imgfile):
			self.tvtipsbox.setImage("image", imgfile)
			self.tvtipsbox.showWidget("image")
		else:
			callInThread(self.imageDownload, imgurl, imgfile, self.setWidgetsImage, "image")
		piconfile = self.getPiconFile(tip[15])
		if piconfile and exists(piconfile):
			self.tvtipsbox.setImage("picon", piconfile)
			self.tvtipsbox.showWidget("picon")
		else:
			self.tvtipsbox.hideWidget("picon")
		sref = tvglobals.IMPORTDICT.get(tip[15], ["", ""])[0]
		hasTimer = self.isAlreadyListed(tip[1], sref, self.currdatetime, self.getTimerlist()) if tip[1] and sref else False
		if hasTimer:
			self.tvtipsbox.showWidget("hasTimer")
		else:
			self.tvtipsbox.hideWidget("hasTimer")
		self.currTipId = tip[16]

	def getUserMenuUsage(self, index):
		return [config.plugins.tvspielfilm.use_a.value, config.plugins.tvspielfilm.use_b.value, config.plugins.tvspielfilm.use_c.value, config.plugins.tvspielfilm.use_d.value][index]

	def setProgressRange(self, index, range):
		self.tvupdate.setRange(f"progressBar{index}", range)

	def setProgressValues(self, index, valuelist):
		self.tvupdate.setText(f"progressHdr{index}", valuelist[0])
		self.tvupdate.setValue(f"progressBar{index}", valuelist[1])
		self.tvupdate.setText(f"progressTxt{index}", valuelist[2])


class TVimport(TVhelper, Screen):
	skin = """
	<screen name="TVimport" position="480,90" size="320,500" backgroundColor="#16000000" flags="wfNoBorder" resolution="1280,720" title="TV Spielfilm Servicedatei">
		<eLabel position="0,0" size="320,500" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="316,496" zPosition="-1" />
		<eLabel name="TV_bg" position="2,2" size="316,58" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="2,60" size="316,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="70,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
		<widget source="bouquetslist" render="Listbox" position="2,60" size="316,440" itemCornerRadiusSelected="4" itemGradientSelected=" #051a264d, #10304070, #051a264d, horizontal" enableWrapAround="1" foregroundColorSelected="white" backgroundColor="#16000000" transparent="1" scrollbarMode="showNever">
			<convert type="TemplatedMultiContent">{"template": [
				MultiContentEntryText(pos=(0,0), size=(316,40), font=0,  flags=RT_HALIGN_CENTER|RT_VALIGN_CENTER, text=0)  # menutext
				],
				"fonts": [gFont("Regular",24)],
				"itemHeight":40
				}</convert>
		</widget>
	</screen>
	"""

	def __init__(self, session):
		self.session = session
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		Screen.__init__(self, session)
		self.tvinfobox = session.instantiateDialog(TVinfoBox)
		self.totaldupes = []
		self.totalimport = []
		self.totalsupp = []
		self.totalunsupp = []
		self["release"] = StaticText(tvglobals.RELEASE)
		self["bouquetslist"] = List()
		self["actions"] = ActionMap(["OkCancelActions"],
							  						{"ok": self.keyOk,
													"cancel": self.keyExit}, -1)
		self.onShown.append(self.shownFinished)

	def shownFinished(self):
		configpath = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/")  # /etc/enigma2/TVSpielfilm
		if not exists(configpath):
			makedirs(configpath, exist_ok=True)
		sourcefile = join(tvglobals.PLUGINPATH, "db/tvs_mapping.txt")
		mapfile = join(configpath, "tvs_mapping.txt")
		if not exists(mapfile) or config.plugins.tvspielfilm.update_mapfile.value and int(getmtime(sourcefile)) < int(getmtime(mapfile)):  # plugin mapfile older than user mapfile:
			print(f"[{tvglobals.MODULE_NAME}] Copy '{sourcefile}' to '{mapfile}'.")
			copy(sourcefile, mapfile)
		if exists(mapfile):
			self.getAllBouquets()
		else:
			print(f"[{tvglobals.MODULE_NAME}] Error in class 'TVimport:shownFinished': file '{mapfile}' not found.")
			self.session.open(MessageBox, f"Datei '{mapfile}' kann weder gefunden noch angelegt werden.\nTVS Import kann daher nicht fortgefahren werden!", MessageBox.TYPE_ERROR, timeout=30, close_on_any_key=True)
			self.keyExit()

	def keyExit(self):
		self.close()

	def keyOk(self):
		current = self["bouquetslist"].getCurrent()  # e.g. ('Favoriten (TV)', <enigma.eServiceReference; proxy of <Swig Object of type 'eServiceReference *' at 0xa70d46f8> >)
		importlist, dupeslist, supplist, unsupplist = self.importBouquet(current[1])
		if importlist:
			# combine two lists without duplicate entries while retaining the sort order
			self.totalimport = list(dict(dict(self.totalimport), **dict(importlist)).items())  # is later reduced by TVchannelselection
			self.totaldupes = list(dict(dict(self.totaldupes), **dict(dupeslist)).items())
			self.totalsupp = list(dict(dict(self.totalsupp), **dict(supplist)).items())  # complete list of channels supported by the server
			self.totalunsupp = list(dict(dict(self.totalunsupp), **dict(unsupplist)).items())
			totalfound = importlist + dupeslist + unsupplist
			self.appendImportLog(current[0], totalfound, importlist, dupeslist, unsupplist)
			msg = f"\nSoeben im Bouquet gefundene Kanäle: {len(totalfound)}"
			msg += f"\nSoeben erfolgreich importierte Kanalkürzel: {len(importlist)}"
			msg += f"\nSoeben nicht importierte doppelte Kanalkürzel: {len(dupeslist)}"
			msg += f"\nSoeben gefundene Kanäle die nicht von TVSpielfilm unterstützte werden: {len(unsupplist)}"
			msg += f"\n{'-' * 120}"
			msg += f"\nBisher erfolgreich importierte Kanalkürzel: {len(self.totalimport)}"
			msg += f"\nBisher nicht importierte doppelte Kanalkürzel: {len(self.totaldupes)}"
			msg += f"\nBisher gefundene Kanäle die nicht von TVSpielfilm unterstützt werden: {len(self.totalunsupp)}"
			msg += "\n\nSoll noch ein weiteres TV Bouquet importiert werden?"
		else:
			msg = "\nKeine TV Spielfilm Kanäle gefunden.\nBitte wähle ein anderes TV Bouquet."
		self.session.openWithCallback(self.anotherBouquet, MessageBox, msg, MessageBox.TYPE_YESNO, timeout=30, default=False)

	def anotherBouquet(self, answer):
		if answer is True:
			self.getAllBouquets()
		else:  # create TVSpielfilm service- and dupesJSON and finish successfully
			self.session.openWithCallback(self.anotherBouquetCB, TVchannelselection, self.totalimport)

	def anotherBouquetCB(self, answer):
		if answer:
			if answer[0] is True:
				if self.totalimport:
					supportedchannels = []
					importedchannels = []
					for index, channel in enumerate(answer[1]):
						if channel[1]:
							supportedchannels.append((self.totalsupp[index][1][0], (self.totalsupp[index][0], self.totalsupp[index][1][1])))
							importedchannels.append((self.totalimport[index][1][0], (self.totalimport[index][0], self.totalimport[index][1][1])))  # e.g. ('ard', ('1:0:19:283D:41B:1:FFFF0000:0:0:0:', 'Das Erste HD'))
					importfile = join(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/"), "tvs_imported.json")
					with open(f"{importfile}.new", 'w') as file:  # all imported channels only
						file.write(dumps(dict(importedchannels)))
						rename(f"{importfile}.new", importfile)
					suppfile = join(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/"), "tvs_supported.json")
					with open(f"{suppfile}.new", 'w') as file:  # all channels supported by Server
						file.write(dumps(dict(supportedchannels)))
						rename(f"{suppfile}.new", suppfile)
				if self.totaldupes:
					dupesfile = join(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/"), "tvs_dupes.json")
					with open(f"{dupesfile}.new", 'w') as file:
						file.write(dumps(dict(self.totaldupes)))
					rename(f"{dupesfile}.new", dupesfile)
				if self.totalunsupp:
					unsuppfile = join(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/"), "tvs_unsupported.json")
					with open(f"{unsuppfile}.new", 'w') as file:
						file.write(dumps(dict(self.totalunsupp)))
					rename(f"{unsuppfile}.new", unsuppfile)
				self.tvinfobox.showDialog("Senderimport erfolgreich durchgeführt.", 2500)
			else:
				self.tvinfobox.showDialog("Senderimport abgebrochen!", 2500)
			self.close()

	def getAllBouquets(self):
		bouquetstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet' if config.usage.multibouquet.value else '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
		root = eServiceReference(bouquetstr)
		serviceHandler = eServiceCenter.getInstance()
		bouquetsList = []
		if config.usage.multibouquet.value:
			serviceList = serviceHandler.list(root)
			while True:
				service = serviceList.getNext()
				if not service.valid():
					del serviceList
					break
				if service.flags & eServiceReference.isDirectory:
					info = serviceHandler.info(service)
					if info:
						bouquetsList.append((info.getName(service), service))
		else:
			info = serviceHandler.info(root)
			if info:
				bouquetsList.append((info.getName(root), root))
		self["bouquetslist"].updateList(bouquetsList)

	def importBouquet(self, bouquet=None):
		if not bouquet:  # fallback to favorites
			bouquet = eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet')
		supported, unsupported, importlist, dupeslist, = [], [], [], []
		slist = ServiceList(bouquet, validate_commands=False)
		services = slist.getServicesAsList(format='SN')  # z.B. [('1:0:27:212F:31B:1:FFFF0000:0:0:0:', 'Das Erste HD'), ...]
		for service in services:
			found = ""
			sname = service[1].strip()
			sref = f"{service[0].split("http")[0]}{{IPTV-Stream}}" if "http" in service[0].lower() else service[0]
			for channelId, regstr in self.readMappingList():  # find TVSpielfilm shortcut for channelname
				if match(compile(regstr), sname.lower()):
					found = channelId
					break
			if found:
				supported.append((sref.rstrip(), tuple((found.rstrip(), sname.rstrip()))))
			else:
				unsupported.append((sref.rstrip(), tuple(("", sname.rstrip()))))
		for item in supported:  # divide into import and duplicate
			if item[1][0] not in [x[1][0] for x in importlist]:
				importlist.append(item)
			else:
				dupeslist.append(item)

		return importlist, dupeslist, supported, unsupported

	def readMappingList(self):  # Read mapping (=translation rules 'TVSpielfilm channel abbreviation: E2 service name')
		maplist = []
		with open(join(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/"), "tvs_mapping.txt")) as file:  # /etc/enigma2/TVSpielfilm
			line = "{No line evaluated yet}"
			try:
				for line in file.read().replace(",", "").strip().split("\n"):
					if not line.startswith("#"):
						items = line.strip().split(": ")
						if items:
							maplist.append((items[0], items[1]))
			except Exception as error:
				print(f"[{tvglobals.MODULE_NAME}] Exception error class 'TVimport:readMappingList' in {line}: {error}")
		return maplist

	def appendImportLog(self, bouquetname, totalfound, importlist, dupeslist, unsupported):  # append last successful import to logfile
		with open("/home/root/logs/bouquetimport.log", "a") as file:
			file.write(f"{'=' * 78}\n{len(totalfound)} channels found in bouquet '{bouquetname}' (incl. duplicate TVSpielfilm shortcuts)\n{'=' * 78}\n")
			formatstr = "{0:<10} {1:<40} {2:<0}\n"
			for item in totalfound:
				file.write(formatstr.format(*(item[1][0] or "n/a", item[0], item[1][1])))
			file.write(f"\n{len(importlist)} imported TV movie channels (without duplicate TVSpielfilm shortcuts):\n{'-' * 78}\n")
			for item in importlist:
				file.write(formatstr.format(*(item[1][0], item[0], item[1][1])))
			file.write(f"\n{len(dupeslist)} not imported channels (because duplicate TVSpielfilm shortcuts):\n{'-' * 78}\n")
			for item in dupeslist:
				file.write(formatstr.format(*(item[1][0], item[0], item[1][1])))
			file.write(f"\n{len(unsupported)} channels not supported by TV-Spielfilm:\n{'-' * 78}\n")
			for item in unsupported:
				file.write(formatstr.format(*("n/a", item[0], item[1][1])))
			file.write("\n")


class TVchannelselection(Screen):
	skin = """
	<screen name="TVchannelselection" position="480,20" size="320,660" backgroundColor="#16000000" flags="wfNoBorder" resolution="1280,720" title="TV Spielfilm Kanalauswahl">
		<eLabel position="0,0" size="320,660" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="316,656" zPosition="-1" />
		<eLabel name="TV_bg" position="2,2" size="316,58" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="2,60" size="316,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="2,616" size="316,2" backgroundColor=" #0027153c , #00101093 , black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="70,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
		<widget source="channelList" render="Listbox" position="2,62" size="316,550" itemCornerRadiusSelected="4" itemGradientSelected="#051a264d,#10304070,#051a264d,horizontal" enableWrapAround="1" foregroundColorSelected="white" backgroundColor="#16000000" transparent="1" scrollbarMode="showOnDemand" scrollbarBorderWidth="1" scrollbarWidth="10" scrollbarBorderColor="blue" scrollbarForegroundColor="#00203060">
			<convert type="TemplatedMultiContent">{"template": [
				MultiContentEntryText(pos=(5,2), size=(270,30), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=0),  # menutext
				MultiContentEntryPixmapAlphaBlend(pos=(280,8), size=(20,20), flags=BT_SCALE, png="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/checkbox.png"),  # checkbox
			MultiContentEntryText(pos=(282,6), size=(18,18), font=1, color=MultiContentTemplateColor(2), color_sel=MultiContentTemplateColor(2), flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=1)  # checkmark
				],
				"fonts": [gFont("Regular",20),gFont("Regular",20),gFont("Regular",36)],
				"itemHeight":34
				}</convert>
		</widget>
		<eLabel name="button_red" position="10,626" size="6,30" backgroundColor=" #00821c17, #00fe0000, vertical" zPosition="1" />
		<eLabel name="button_green" position="180,626" size="6,30" backgroundColor=" #00006600, #0024a424, vertical" zPosition="1" />
		<widget source="key_red" render="Label" position="24,628" size="150,30" font="Regular;18" foregroundColor="#00ffffff" backgroundColor="#00000000" transparent="1" zPosition="2" halign="left" valign="center" />
		<widget source="key_green" render="Label" position="194,628" size="150,30" font="Regular;18" foregroundColor="#00ffffff" backgroundColor="#00000000" transparent="1" zPosition="1" halign="left" valign="center" />
	</screen>
	"""

	def __init__(self, session, totalimport):
		self.totalimport = totalimport
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		Screen.__init__(self, session)
		self.tvinfobox = session.instantiateDialog(TVinfoBox)
		self.channellist = []
		self.deselect = True
		self["release"] = StaticText(tvglobals.RELEASE)
		self["channelList"] = List()
		self["key_red"] = StaticText("Alle abwählen")
		self["key_green"] = StaticText("Übernehmen")
		self['actions'] = ActionMap(["OkCancelActions",
							   		"ColorActions"], {"ok": self.keyOk,
													"red": self.keyRed,
													"green": self.keyGreen,
													"cancel": self.keyExit}, -1)
		self.onShown.append(self.onShownFinished)

	def onShownFinished(self):
		self.channellist = []
		for service in self.totalimport:
			self.channellist.append([service[1][1], True])
		self.updateChannellist()

	def updateChannellist(self):
		skinlist = []
		for channel in self.channellist:
			skinlist.append((channel[0], "✔" if channel[1] else "✘", int("0x0004c81b", 0) if channel[1] else int("0x00f50808", 0)))  # alternatively "✓", "✗"
		self["channelList"].updateList(skinlist)

	def keyOk(self):
		current = self["channelList"].getCurrentIndex()
		if self.channellist:
			self.channellist[current][1] = not self.channellist[current][1]
		self.updateChannellist()

	def keyRed(self):
		if self.channellist:
			if self.deselect:
				for index in range(len(self.channellist)):
					self.channellist[index][1] = False
				self["key_red"].setText("Alle auswählen")
			else:
				for index in range(len(self.channellist)):
					self.channellist[index][1] = True
				self["key_red"].setText("Alle abwählen")
		self.deselect = not self.deselect
		self.updateChannellist()

	def keyGreen(self):
		if self.channellist:
			if all(not x[1] for x in self.channellist):
				self.tvinfobox.showDialog("Bitte wählen Sie mindestens einen Sender aus!", 2500)
				self.updateChannellist()
			else:
				self.close((True, self.channellist))

	def keyExit(self):
		self.close((False, []))


class TVsetup(TVhelper, Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "TVsetup", plugin="Extensions/TVSpielfilm", PluginLanguageDomain="TVSpielfilm")

	def keySelect(self):
		if self.getCurrentItem() == config.plugins.tvspielfilm.cachepath:
			self.session.openWithCallback(self.keySelectCB, TVsettingsLocationBox, currDir=config.plugins.tvspielfilm.cachepath.value)
			return
		Setup.keySelect(self)

	def keySelectCB(self, path):
		if path is not None:
			path = join(path, "")
			config.plugins.tvspielfilm.cachepath.value = path
		self["config"].invalidateCurrent()
		self.changedEntry()


def readImportedFile():
	importdict = {}
	importfile = join(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/"), "tvs_imported.json")
	if exists(importfile):
		with open(importfile, "r") as file:
			importdict = loads(file.read())
	return importdict  # e.g. [('ard': ('1:0:27:212F:31B:1:FFFF0000:0:0:0:', 'Das Erste HD')), ...]


def readSupportedFile():
	suppdict = {}
	suppfile = join(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/"), "tvs_supported.json")
	if exists(suppfile):
		with open(suppfile, "r") as file:
			suppdict = loads(file.read())
	return suppdict  # e.g. [('ard': ('1:0:27:212F:31B:1:FFFF0000:0:0:0:', 'Das Erste HD')), ...]


def getAPIdata(url, params=None):
	headers = {"User-Agent": tvglobals.USERAGENT}
	errmsg, jsondict = "", {}
	try:
		if not headers:
			headers = {}
		response = get(url, params=params, headers=headers, timeout=(3.05, 6))
		response.raise_for_status()
		if response.ok:
			errmsg, jsondict = "", response.json()
		else:
			errmsg, jsondict = f"API server access ERROR, response code: {response.raise_for_status()}", {}
		del response
		return errmsg, jsondict
	except exceptions.RequestException as errmsg:
		print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVglobals:getAPIdata': {errmsg}")
		return errmsg, jsondict


def getAllAssets(channelId, date, spanStarts, noLoadExisting=False):
	assetsdict = {}
	temppath = f"{config.plugins.tvspielfilm.cachepath.value}tmp/TVSpielfilm/" if config.plugins.tvspielfilm.cachepath.value == "/" else f"{config.plugins.tvspielfilm.cachepath.value}TVSpielfilm/"
	assetsfile = join(f"{temppath}cache/", f"allAssets{date}T{spanStarts}.json")
	if date and exists(assetsfile):  # load assets from cache if available and desired
		if noLoadExisting:
			return False, {}
		with open(assetsfile, "r") as file:
			filedict = loads(file.read()) or {}
		if filedict:
			assetsdict = filedict.get(channelId, {})  # extract assets for current channelId
		return False, assetsdict
	else:  # download assets for current channelId
		url = f"{tvglobals.BASEURL}api/epg/broadcast/{channelId.upper()}"
		params = [('mode', 'current'), ('date', f'{date}T{spanStarts}')] if spanStarts else [('mode', 'current')]
		errmsg, jsondict = getAPIdata(url, params)  # get today's EPG for channel shortcuts (e.g. 'ard' instead of 'Das Erste')
		if errmsg:
			return False, {}
		return True, jsondict.get("assets", {})  # extract assets only


def showCurrentEvent(session, callback=None, **kwargs):
	ref = session.nav.getCurrentlyPlayingServiceOrGroup()
	epg = eEPGCache.getInstance()
	ptr = ref and ref.valid() and epg.lookupEventTime(ref, -1)
	if ptr:
		eventStartTs = ptr.getBeginTime()
		Event = epg.lookupEventTime(ref, eventStartTs, +1)
		if Event:
			sref = str(ServiceReference(ref))
			channelId = [shortcut for shortcut, detail in readSupportedFile().items() if detail[0] == sref]
			if channelId:
				eventStart = datetime.fromtimestamp(eventStartTs)
				eventStart -= timedelta(minutes=eventStart.minute % 15, seconds=eventStart.second, microseconds=0)  # round to last 15 minutes
				date = eventStart.strftime("%F")
				timeStart = eventStart.strftime("%H:%M")
				downloaded, assetsdict = getAllAssets(channelId[0], date, timeStart)
				if downloaded and assetsdict:
					assetId = ""
					for assetdict in assetsdict:
						timeStartTs = assetdict.get("airInfo", {}).get("timeStart", 0)
						if timeStart and timeStartTs <= eventStart.timestamp():
							assetId = assetdict.get("assetId", "")
						else:
							break
					if assetId:
						if callback:
							session.openWithCallback(boundFunction(callback, True), TVfullscreen, assetId)
						else:
							session.open(TVfullscreen, assetId)
					return
	if callback:
		callback(False)
	else:
		session.open(MessageBox, "Dieser Sender wird nicht von TV Spielfilm unterstützt.", type=MessageBox.TYPE_INFO, timeout=2, close_on_any_key=True)


def showNowOnTv(session, **kwargs):
	session.open(TVoverview, None)


def main(session, **kwargs):
	if not exists(join(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/"), "tvs_imported.json")):
		session.open(TVimport)
	else:
		session.open(TVmain)


def autostart(reason, **kwargs):
	pass


def sessionstart(reason, session):
	if reason == 0 and tvglobals.HAS_FUNCTIONTIMER:
		pass
#		functionTimer.add(("TVupdate", {"name": "TV-Spielfilm-Update", "fnc": updateFutureEPG}))  # TODO: eigenständige Funktion!


def Plugins(**kwargs):
	return [
		PluginDescriptor(name="TV Spielfilm", icon=f"pics/{tvglobals.RESOLUTION}/logos/plugin.png", description="Die Entscheidungshilfe: Alterativer EPG mit umfangreichen Zusatzinfos.", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		PluginDescriptor(name="TV Spielfilm - Jetzt im TV", icon=f"pics/{tvglobals.RESOLUTION}/logos/TVjetzt.png", description="Zeige die aktuell laufenden und demnächst anstehenden Sendungen.", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=showNowOnTv),
		PluginDescriptor(name='TV Spielfilm - laufende Sendung', description='TV Spielfilm laufende Sendung', where=PluginDescriptor.WHERE_EVENTINFO, fnc=showCurrentEvent),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, needsRestart=True, fnc=sessionstart),
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, needsRestart=True, fnc=autostart)
		]

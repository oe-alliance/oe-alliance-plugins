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
from hashlib import sha256
from io import BytesIO
from json import load, dump
from os import rename, makedirs, remove
from os.path import exists, join, getmtime
from secrets import choice
from PIL import Image
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

# PLUGIN IMPORTS
from .tvsparser import tvsptips, tvspchannels, tvspassets
HAS_FUNCTIONTIMER = True
try:
	from Scheduler import functionTimer
except ImportError:
	HAS_FUNCTIONTIMER = False

TVS_UPDATEACTIVE, TVS_UPDATESTOP = False, False
STARTTIMES = [(spanSet[0].split("-")[0], spanSet[1]) for spanSet in tvspassets.spanSets.items()]  # [('00:00', '0'), ('05:00', '5'), ('14:00', '14'), ('18:00', '18'), ('20:00', '20'), ('20:15', 'prime'), ('22:00', '22')]
CATFILTERS = list(tvspassets.catFilters.items())  #  [('Spielfilm', 'SP'), ('Serie', 'SE'), ('Report', 'RE'), ('Unterhaltung', 'U'), ('Kinder', 'KIN'), ('Sport', 'SPO'), ('Andere', 'AND')]
ASSETFILTERS = [("{keiner}", ""), ("Daumen", "thumb"), ("Tipp", "isTipOfTheDay")] + CATFILTERS  # not supported by HP: ("Neu", "isNew"), ("Tagestipp", "isTopTip")]
STARTING = [(i, f"{x[0]} Uhr") for i, x in enumerate(STARTTIMES)]
DURANCES = [(x, f"{x} Minuten") for x in range(15, 540, 15)]
CACHEDAYS = [(x, f"+{x} Tage") for x in range(1, 14)]
VISIBILITY = [(0, "keine Anzeige"), (1, "im Extensionmenü (Taste BLAU-lang)"), (2, "im Pluginmanager (Taste GRÜN-kurz)"), (3, "in Extensionmenü und Pluginmanager")]
config.plugins.tvspielfilm = ConfigSubsection()
config.plugins.tvspielfilm.showtips = ConfigSelection(default=2, choices=[(0, "niemals"), (1, "nur bei Pluginstart"), (2, "immer")])
config.plugins.tvspielfilm.filter = ConfigSelection(default=0, choices=[(i, f"{x[0]}") for i, x in enumerate(ASSETFILTERS)])
config.plugins.tvspielfilm.channelname = ConfigSelection(default=1, choices=[(0, "vom Image"), (1, "vom Server")])
config.plugins.tvspielfilm.prefered_db = ConfigSelection(default=0, choices=[(0, "jedesmal nachfragen"), (1, "IMDb - Internet Movie Database"), (2, "TMDb - The Movie Database")])
config.plugins.tvspielfilm.update_mapfile = ConfigSelection(default=1, choices=[(0, "niemals"), (1, "nach Updates")])
config.plugins.tvspielfilm.cachepath = ConfigText(default=join("/media/hdd/"))
config.plugins.tvspielfilm.cacherange = ConfigSelection(default=7, choices=[(x, f"+{x} Tage") for x in range(1, 14)])
config.plugins.tvspielfilm.keepcache = ConfigSelection(default=7, choices=[(x, f"-{x} Tage") for x in range(8)])
config.plugins.tvspielfilm.autoupdate = ConfigSelection(default=1, choices=[(0, "ergänze nur fehlende Daten"), (1, "überschreibe vorhandene Daten")])
config.plugins.tvspielfilm.durance_n = ConfigSelection(default=90, choices=DURANCES)  # 'Jetzt im TV'
config.plugins.tvspielfilm.use_a = ConfigYesNo(default=False)
config.plugins.tvspielfilm.starttime_a = ConfigSelection(default=1, choices=STARTING)
config.plugins.tvspielfilm.durance_a = ConfigSelection(default=540, choices=DURANCES)
config.plugins.tvspielfilm.use_b = ConfigYesNo(default=False)
config.plugins.tvspielfilm.starttime_b = ConfigSelection(default=2, choices=STARTING)
config.plugins.tvspielfilm.durance_b = ConfigSelection(default=240, choices=DURANCES)
config.plugins.tvspielfilm.use_c = ConfigYesNo(default=True)
config.plugins.tvspielfilm.starttime_c = ConfigSelection(default=5, choices=STARTING)
config.plugins.tvspielfilm.durance_c = ConfigSelection(default=105, choices=DURANCES)
config.plugins.tvspielfilm.use_d = ConfigYesNo(default=True)
config.plugins.tvspielfilm.starttime_d = ConfigSelection(default=6, choices=STARTING)
config.plugins.tvspielfilm.durance_d = ConfigSelection(default=120, choices=DURANCES)
config.plugins.tvspielfilm.primetime = ConfigSelection(default=1, choices=VISIBILITY)
config.plugins.tvspielfilm.nowontv = ConfigSelection(default=1, choices=VISIBILITY)
config.plugins.tvspielfilm.currprogram = ConfigSelection(default=1, choices=VISIBILITY[:2])
config.plugins.tvspielfilm.mapfilehash = ConfigText(default="")


class TVglobals():
	IMPORTDICT = {}
	RELEASE = "v2.1"
	MODULE_NAME = __name__.split(".")[-2]
	RESOLUTION = "FHD" if getDesktop(0).size().width() > 1300 else "HD"
	PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/TVSpielfilm/")
	ICONPATH = f"{PLUGINPATH}pics/{RESOLUTION}/icons/"
	LOGPATH = "/home/root/logs/"
	WEBURL = bytes.fromhex("687474703a2f2f7777772e7476737069656c66696c6d2e64653"[:-1]).decode()
	IMGURL = bytes.fromhex("687474703a2f2f696d672e7476737069656c66696c6d2e6465a"[:-1]).decode()
	USERAGENT = choice([
			"Mozilla/5.0 (Linux; Android 14; SM-A536B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.231 Mobile Safari/537.36",
			"Mozilla/5.0 (Linux; Android 14; SM-S918W Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/122.0.6261.119 Mobile Safari/537.36/122.0.6261.119",
			"Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36",
			"Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/128.0.0.0 Mobile DuckDuckGo/5 Safari/537.36",
			"Mozilla/5.0 (Linux; Android 14; G9FPL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.48 Mobile Safari/537.36",
			"Mozilla/5.0 (Linux; arm_64; Android 14; Pixel Fold) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.232 YaBrowser/23.11.0.232.00 SA/3 Mobile Safari/537.36"
			"Mozilla/5.0 (Linux; Android 14; SM-F731N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 OPR/81.1.4292.78446"
			])


tvglobals = TVglobals()


class TVcoreHelper():
	def getTMPpath(self):
		return f"{config.plugins.tvspielfilm.cachepath.value}tmp/TVSpielfilm/" if config.plugins.tvspielfilm.cachepath.value == "/" else f"{config.plugins.tvspielfilm.cachepath.value}TVSpielfilm/"

	def createTMPpaths(self):
		try:
			tmppath = self.getTMPpath()
			for path in [tmppath, f"{tmppath}cache/", f"{tmppath}assets/", f"{tmppath}images/"]:
				if not exists(path):
					makedirs(path, exist_ok=True)
		except OSError as errmsg:
			return errmsg
		return ""

	def cleanupCache(self):  # delete older asset overviews, detailed assets and images
		today = datetime.today()
		latest = today - timedelta(days=config.plugins.tvspielfilm.keepcache.value)
		ldate = latest.replace(hour=0, minute=0, second=0, microsecond=0)
		for filename in glob(join(f"{self.getTMPpath()}cache/", "assets*_*.json")):
			if datetime.strptime(filename.split("/")[-1][6:16], "%Y-%m-%d") < ldate:  # keepcache or older?
				remove(filename)
		for filenames in [glob(join(f"{self.getTMPpath()}cache/", "allTips*.json")), glob(join(f"{self.getTMPpath()}assets/", "*.*")), glob(join(f"{self.getTMPpath()}images/", "*.*"))]:
			for filename in filenames:
				if datetime.timestamp(today) - getmtime(filename) > 86400:  # older than 24h?
					remove(filename)

	def getUserMenuUsage(self, index):
		return [config.plugins.tvspielfilm.use_a.value, config.plugins.tvspielfilm.use_b.value, config.plugins.tvspielfilm.use_c.value, config.plugins.tvspielfilm.use_d.value][index]

	def getUserTimespans(self):
		timeSpans = []
		userconfigs = [(config.plugins.tvspielfilm.starttime_a.value, config.plugins.tvspielfilm.durance_a.value),
						(config.plugins.tvspielfilm.starttime_b.value, config.plugins.tvspielfilm.durance_b.value),
						(config.plugins.tvspielfilm.starttime_c.value, config.plugins.tvspielfilm.durance_c.value),
						(config.plugins.tvspielfilm.starttime_d.value, config.plugins.tvspielfilm.durance_d.value)
						]
		for index, userconfig in enumerate(userconfigs):
			if self.getUserMenuUsage(index):
				timeSpans.append((STARTTIMES[userconfig[0]], userconfig[1]))
		return timeSpans

	def allAssetsFilename(self, spanStartsDt, channelId=None):
		filename = ""
		if channelId:  # single channel completely
			filename = join(f"{self.getTMPpath()}cache/", f"allAssets_{spanStartsDt.strftime('%F')}_{channelId.lower()}.json")
		elif spanStartsDt:  # time period
			filename = join(f"{self.getTMPpath()}cache/", f"allAssets_{spanStartsDt.strftime('%F')}T{spanStartsDt.strftime('%H:%M')}.json")
		return filename

	def loadAllAssets(self, spanStartsDt, channelId=None):  # load assets from cache if available
		allAssets = []
		filename = self.allAssetsFilename(spanStartsDt, channelId=channelId)
		if filename and exists(filename):
			with open(filename, "r") as file:
				allAssets = load(file)
		return allAssets

	def saveAllAssets(self, allAssets, spanStartsDt, channelId=None):
		errmsg = ""
		if allAssets:
			assetsFile = self.allAssetsFilename(spanStartsDt, channelId=channelId)
			try:
				if not exists(assetsFile):
					with open(assetsFile, "w") as file:
						dump(allAssets, file)
			except OSError as errmsg:
				print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVcoreHelper:saveAllAssets': {errmsg}!")
		return ""

	def getSingleAsset(self, assetUrl):
		errmsg = ""
		assetDict = {}
		if assetUrl:
			assetfile = join(f"{self.getTMPpath()}assets/", f"{self.convertAssetId(assetUrl)}.json")
			if exists(assetfile):  # load from cache if available
				with open(assetfile, "r") as file:
					assetDict = load(file)
			else:  # download
				errmsg, assetDict = tvspassets.parseSingleAsset(assetUrl)
				if not errmsg:
					try:
						assetfile = join(f"{self.getTMPpath()}assets/", f"{self.convertAssetId(assetUrl)}.json")
						if not exists(assetfile):
							with open(assetfile, "w") as file:
								dump(assetDict, file)
					except OSError as saveErr:
						print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVcoreHelper:getSingleAsset': {saveErr}!")
		return errmsg, assetDict

	def getCurrentAssetUrl(self, ref, callback=None):
		epg = eEPGCache.getInstance()
		ptr = ref and ref.valid() and epg.lookupEventTime(ref, -1)
		assetUrl = ""
		if ptr:
			eventStartTs = ptr.getBeginTime()
			Event = epg.lookupEventTime(ref, eventStartTs, +1)
			if Event:
				sref = ServiceReference(ref).toString()
				channelId = [shortcut for shortcut, detail in self.readSupportedFile().items() if detail[0] == sref]
				if channelId:
					channelId = channelId[0].lower()
					eventStartDt = datetime.fromtimestamp(eventStartTs)
					eventStartDt -= timedelta(minutes=eventStartDt.minute % 15, seconds=eventStartDt.second, microseconds=0)  # round off to last 15 minutes
					errmsg, pageAssets, lastPage = tvspassets.parseChannelPage(channelId=channelId, dateStr=eventStartDt.strftime("%F"), timeCode=("", "now"))  # get "Jetzt im TV" for current channelId
					if errmsg:
						print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVCorehelper:getCurrentAssetUrl' - parsing failed: {errmsg}")
						return ""
					for assetDict in pageAssets:
						timeStartIso = assetDict.get("timeStart", "")
						timeStartDt = datetime.fromisoformat(timeStartIso).replace(tzinfo=None) if timeStartIso else datetime.today()
						if timeStartDt and timeStartDt >= eventStartDt:
							assetUrl = assetDict.get("assetUrl", "")
							break
					if assetUrl:
						errmsg, assetDict = self.getSingleAsset(assetUrl)
						if errmsg:
							print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVcoreHelper:getCurrentAssetUrl': {errmsg}!")
		if callback:
			callback(assetUrl)
		return assetUrl

	def convertAssetId(self, assetUrl):
		return assetUrl[assetUrl.rfind(",") + 1:assetUrl.rfind(".html")]

	def convertImageFilename(self, imgUrl):
		filename = f"{imgUrl[imgUrl.rfind('/') + 1:imgUrl.rfind('?im')]}".replace(".jpeg", ".jpg")
		return join(f"{self.getTMPpath()}images/", filename) if imgUrl else ""

	def readImportedFile(self):
		importDict = {}
		importfile = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_imported.json")
		if exists(importfile):
			with open(importfile, "r") as file:
				importDict = load(file)
		return importDict  # e.g. [('ard': ('1:0:27:212F:31B:1:FFFF0000:0:0:0:', 'Das Erste HD')), ...]

	def readSupportedFile(self):
		suppdict = {}
		suppfile = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_supported.json")
		if exists(suppfile):
			with open(suppfile, "r") as file:
				suppdict = load(file)
		return suppdict  # e.g. [('ard': ('1:0:27:212F:31B:1:FFFF0000:0:0:0:', 'Das Erste HD')), ...]

	def updateMappingfile(self):
		configpath = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/")  # /etc/enigma2/TVSpielfilm/
		if not exists(configpath):
			makedirs(configpath)
		sourcefile = join(tvglobals.PLUGINPATH, "db/tvs_mapping.txt")
		mapfile = join(configpath, "tvs_mapping.txt")
		if exists(mapfile) and (config.plugins.tvspielfilm.update_mapfile.value and int(getmtime(sourcefile)) > int(getmtime(mapfile))):  # plugin mapfile older than user mapfile:
			with open(mapfile, "rb") as file:
				hashcode = sha256(file.read()).hexdigest()
			if hashcode != config.plugins.tvspielfilm.mapfilehash.value:  # has the content of the mapfile changed?
				print(f"[{tvglobals.MODULE_NAME}] Copy '{sourcefile}' to '{mapfile}'.")
				copy(sourcefile, mapfile)
				config.plugins.tvspielfilm.mapfilehash.value = hashcode
				config.plugins.tvspielfilm.mapfilehash.save()
				return True
		elif not exists(mapfile):
			print(f"[{tvglobals.MODULE_NAME}] Copy '{sourcefile}' to '{mapfile}'.")
			copy(sourcefile, mapfile)
			return True
		return False


class TVscreenHelper(TVcoreHelper, Screen):
	def imageDownload(self, url, imgFile, callback=None, assetUrl=""):
		if not exists(imgFile):
			headers = {"User-Agent": tvglobals.USERAGENT}
			try:
				response = get(url, headers=headers, stream=True, timeout=(3.05, 6))
				response.raise_for_status()
			except exceptions.RequestException as errmsg:
				print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVscreenHelper:imageDownload': {url} - picture could not be downloaded: {errmsg}")
				return
			try:
				img = Image.open(BytesIO(response.content))
				img.thumbnail((600, 450) if tvglobals.RESOLUTION == "FHD" else (400, 300), Image.LANCZOS)
				img.save(imgFile, format="jpeg", quality=25)
				img.close()
				if callback:
					callback(imgFile, assetUrl)
			except OSError as errmsg:
				print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVscreenHelper:imageDownload': {imgFile} - picture could not be saved: {errmsg}")

	def showAssetDetails(self, assetUrl, fullScreen=False):
		errmsg, assetDict = self.getSingleAsset(assetUrl)
		if errmsg:
			print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVcoreHelper:showAssetDetails': {errmsg}!")
		if assetUrl != self.currAssetUrl:  # stop if another asset was selected in the meantime
			return
		if assetDict:
			isTopTip = assetDict.get("isTopTip", "")
			isTipOfTheDay = assetDict.get("isTipOfTheDay", "")
			isNew = assetDict.get("isNew", "")
			timeStartIso = assetDict.get("timeStart", "")
			timeStartDt = datetime.fromisoformat(timeStartIso).replace(tzinfo=None) if timeStartIso else datetime.today()
			timeEndIso = assetDict.get("timeEnd", "")
			timeEndDt = datetime.fromisoformat(timeEndIso).replace(tzinfo=None) if timeEndIso else datetime.today()
			self.currDateDt = timeStartDt if timeStartDt else datetime.today()
			timeStartStr = self.currDateDt.strftime("%H:%M")
			timeStartEnd = f"{timeStartStr} - {timeEndDt.strftime('%H:%M')}"
			timeStartEndTs = (int(timeStartDt.timestamp()), int(timeEndDt.timestamp()))
			repeatHint = assetDict.get("repeatHint", "")  # e.g.'Wh. um 00:20 Uhr, Nächste Episode um 21:55 Uhr (Staffel 8, Episode 24)'
			channelId = assetDict.get("channelId", "").lower()
			channelName = assetDict.get("channelName", "") if config.plugins.tvspielfilm.channelname.value else tvglobals.IMPORTDICT.get(channelId, ["", ""])[1]
			subline = assetDict.get("preview", "")
			subline += "\n" if subline else ""
			seasonNumber = assetDict.get("seasonNumber", "")
			seasonNumber = f"S{seasonNumber}" if seasonNumber else ""
			episodeNumber = assetDict.get("episodeNumber", "")
			episodeNumber = f"E{episodeNumber}" if episodeNumber else ""
			seasonEpisode = " | ".join(list(filter(None, [seasonNumber, episodeNumber])))
			conclusion = assetDict.get("conclusion", "")
			text = assetDict.get("text", "").replace("\n\n", "\n")
			self.assetTitle = assetDict.get("title", "") or assetDict.get("episodeTitle", "")
			thumbIdNumeric = assetDict.get("thumbIdNumeric", 0)
			thumbIdNumeric = 3 - thumbIdNumeric if thumbIdNumeric else -1
			demanding = assetDict.get("ratingDemanding")
			humor = assetDict.get("ratingHumor")
			action = assetDict.get("ratingAction")
			suspense = assetDict.get("ratingSuspense")
			erotic = assetDict.get("ratingErotic")
			genre = assetDict.get("genre", "")  # e.g. 'Katastrophenaction'
			programType = dict((v, k) for k, v in tvspassets.catFilters.items()).get(assetDict.get("programType", "AND"), "")  # e.g. 'SP' becomes 'Spielfilm'
			imgUrl = assetDict.get("imgUrl", "")
			if imgUrl:
				imgFile = self.convertImageFilename(imgUrl)
				if exists(imgFile):
					self["image"].instance.setPixmapFromFile(imgFile)
					self["image"].show()
				else:
					self["image"].hide()
					callInThread(self.imageDownload, imgUrl, imgFile, self.setAssetImage, assetUrl)  # download + set image (if this assetUrl is still current)
			imgCredits = assetDict.get("imgCredits", "")
			self.trailerUrl = assetDict.get("trailerUrl", "")
			imdbRating = assetDict.get("imdbRating", 0)
			anchorman = assetDict.get("anchorman", "")
			anchorman = f"mit {anchorman}\n" if anchorman else ""
			currentTopics = assetDict.get("currentTopics", "")
			currentTopics += "\n" if currentTopics else ""
			firstYear = assetDict.get("firstYear", "")
			country = assetDict.get("country", "")
			countryYear = f"{country} {firstYear}".strip()
			imdbRating = assetDict.get("imdbRating", "")
			imdbId = assetDict.get("imdbId", "")
			tmdbId = assetDict.get("tmdbId", "")
			if imdbId and tmdbId:
				infotext, self.dataBases = "IMDb+TMDb", ["imdb", "tmdb"]
			elif imdbId:
				infotext, self.dataBases = "IMDb", ["imdb"]
			elif tmdbId:
				infotext, self.dataBases = "TMDb", ["tmdb"]
			else:
				infotext, self.dataBases = "Titelsuche", ["imdb", "tmdb"]
			fsk = assetDict.get("fsk", "")
			fskText = f"ab {fsk} Jahren" if fsk and fsk > -1 else ""
			persons = "\n"
			for member in assetDict.get("crew", {}).items():
				persons += f"{member[0]}:\t{', '.join(member[1])}\n"
			for index, member in enumerate(assetDict.get("cast", {}).items()):
				if not index:  # if very first member
					persons += "\nDarsteller:\n"
				persons += f"{', '.join(member[1])} als '{member[0]}'\n"
			sref = tvglobals.IMPORTDICT.get(channelId, ["", ""])[0]
			hasTimer = self.isAlreadyListed(timeStartEndTs, sref) if timeStartEndTs and sref else False
			self["key_info"].setText(infotext)
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
			self.currTmdbId = tmdbId
			self["imdbRating"].setText(f"IMDb-Wertung: {imdbRating}" if imdbRating else "")
			if thumbIdNumeric != -1:
				thumbfile = join(tvglobals.ICONPATH, f"thumb{thumbIdNumeric}.png")
				if exists(thumbfile):
					self["thumb"].instance.setPixmapFromFile(thumbfile)
					self["thumb"].show()
			else:
				self["thumb"].hide()
			fskfile = join(tvglobals.ICONPATH, f"FSK_{fsk}.png") if fsk and fsk > -1 else ""
			if fskfile:
				self["fsk"].instance.setPixmapFromFile(fskfile)
				self["fsk"].show()
			else:
				self["fsk"].hide()
			self["repeatHint"].setText(repeatHint)
			self["title"].setText(self.assetTitle)
			self["editorial"].setText("Meinung der Redaktion:" if conclusion else "")
			self["conclusion"].setText(conclusion)
			self["longDescription"].setText(f"{subline}{currentTopics}{anchorman}{text}\n{persons}")
			self["key_green"].setText("" if hasTimer else "Timer")
			self.currServiceRef = sref
			if fullScreen:
				startStr, endStr = timeStartEnd.split(" - ")
				titleLenStr = f"{int((datetime.strptime(endStr, '%H:%M') - datetime.strptime(startStr, '%H:%M')).seconds / 60)} Minuten"
				for index, (label, text) in enumerate([("Staffel/Episode", seasonEpisode), ("Genre", genre), ("Typ", programType),
														("Altersfreigabe", fskText), ("Land | Jahr", countryYear), ("Länge", titleLenStr)]):
					if text:
						self[f"typeLabel{index}h"].setText(label)
						self[f"typeLabel{index}l"].setText("")
						self[f"typeText{index}"].setText(text)
					else:
						self[f"typeLabel{index}h"].setText("")
						self[f"typeLabel{index}l"].setText(label)
						self[f"typeText{index}"].setText("")
				self["credits"].setText(imgCredits)
				self.timeStartEnd = timeStartEnd
				self.subLine = subline
				self.spanStartsStr = timeStartStr
				self.setReviewdate(datetime.today(), timeStartEnd, fullScreen=True)

	def setReviewdate(self, currentDt, timeStartEnd, fullScreen=False):
		now = datetime.today()
		now -= timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)  # round to last 15 minutes for 'Jetzt im TV'
		spanStartsStr = self.spanStartsStr or now.strftime("%H:%M")
		dateOnlyDt = currentDt.replace(hour=0, minute=0, second=0, microsecond=0)
		todaydateonly = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
		weekday = "heute" if dateOnlyDt == todaydateonly else ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][dateOnlyDt.weekday()]
		hour, minute = spanStartsStr.split(":") if spanStartsStr else [currentDt.strftime("%H"), currentDt.strftime("%M")]
		spanEnds = (currentDt.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0) + timedelta(minutes=self.spanDuranceTs)).strftime("%H:%M")
		if timeStartEnd:
			startStr, endStr = timeStartEnd.split(" - ")
			titleLenStr = f"{int((datetime.strptime(endStr, '%H:%M') - datetime.strptime(startStr, '%H:%M')).seconds / 60)} Minuten"
			timeStartEnd = f"{timeStartEnd} Uhr"
		else:
			titleLenStr = ""
		if fullScreen:
			reviewdate = " | ".join(list(filter(None, [f"{weekday} {currentDt.strftime('%d.%m.%Y')}", f"{timeStartEnd}", f"{titleLenStr}"])))
		else:
			if self.singleChannelId:
				reviewdate = " | ".join(list(filter(None, [f"{weekday} {currentDt.strftime('%d.%m.%Y')}", f"{self.currDayDelta:+} Tag(e)", "kompletter Tag"])))
			else:
				reviewdate = f"{weekday} {currentDt.strftime('%d.%m.%Y')} | {self.currDayDelta:+} Tag(e) | {spanStartsStr} - {spanEnds} Uhr"
		self["reviewdate"].setText(reviewdate)

	def setAssetImage(self, imgFile, assetUrl):
		if exists(imgFile) and assetUrl == self.currAssetUrl:  # show if no other asset was selected in the meantime
			self["image"].instance.setPixmapFromFile(imgFile)
			self["image"].show()

	def getPiconFile(self, channelId):
		sref = tvglobals.IMPORTDICT.get(channelId, ["", ""])[0]
		fallback = sref.split(":")  # fallback from "1:0:*:..." to "1:0:1:..."
		if len(fallback) > 1:
			fallback[2] = "1"
			fallback = ":".join(fallback)
			fallback = (f"{fallback}FIN").replace(":", "_").replace("_FIN", "").replace("FIN", "")
		sref = f"{sref}FIN".replace(":", "_").replace("_FIN", "").replace("FIN", "")
		for piconsref in [sref, fallback]:
			piconfile = resolveFilename(SCOPE_SKIN_IMAGE, f"picon/{piconsref}.png")
			if exists(piconfile):
				return piconfile
		return ""

	def isAlreadyListed(self, timespanTs, sref):
		timer = f"{datetime.fromtimestamp(timespanTs[0]).strftime('%Y-%m-%d')}:::{datetime.fromtimestamp(timespanTs[0]).strftime('%H:%M')}:::{sref}"  # e.g. ['2024-12-21:::20:15:::1:0:19:283D:41B:1:FFFF0000:0:0:0:', ...]
		return timer in self.getTimerlist()

	def splitTimespan(self, timeSpan, currentDt):
		startstr, endstr = timeSpan  # e.g. ("20:15", "22:45")
		starthour, startminute = startstr.split(":")
		endhour, endminute = endstr.split(":")
		startTs = int(datetime.timestamp(currentDt.replace(hour=int(starthour), minute=int(startminute), second=0, microsecond=0)))
		endTs = int(datetime.timestamp(currentDt.replace(hour=int(endhour), minute=int(endminute), second=0, microsecond=0)))
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
				choicelist = []
				for database, index in enumerate(self.dataBases):
					choicelist.append((index, database))
				self.session.openWithCallback(self.keyInfoCB, ChoiceBox, list=choicelist, keys=[], windowTitle="Wähle die gewünschte Datenbank:")

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

	def zapToCurrent(self):
		if self.zapAllowed and self.currServiceRef:
			self.session.nav.playService(eServiceReference(self.currServiceRef))
			self.close(True)  # True = close complete plugin


class TVfullscreen(TVscreenHelper, Screen):
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
		<widget source="release" render="Label" position="180,28" size="80,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
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
		<widget name="picon" position="586,66" size="147,88" alphatest="blend" scaleFlags="scale" zPosition="1" />
		<widget source="title" render="Label" position="center,0" size="720,36" font="Regular;24" foregroundColor="#0092cbdf" backgroundColor="#16000000" transparent="1" wrap="ellipsis" halign="center" valign="center" zPosition="10" />
		<widget source="repeatHint" render="Label" position="10,600" size="750,46" font="Regular;18" valign="center" halign="left" backgroundColor="#16000000" transparent="1" />
		<widget name="image" position="794,70" size="400,300" alphatest="blend" scaleFlags="centerBottom" zPosition="1" />
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
		<eLabel name="button_yellow" position="186,660" size="6,36" backgroundColor=" #007a6213, #00e6c619, vertical" zPosition="1" />
		<eLabel name="button_blue" position="362,660" size="6,36" backgroundColor="#101093,#4040ff,vertical" zPosition="1" />
		<widget source="key_green" render="Label" position="20,666" size="160,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_yellow" render="Label" position="196,666" size="150,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_blue" render="Label" position="372,666" size="150,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_info" render="Label" position="960,666" size="120,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_play" render="Label" position="1116,666" size="160,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<eLabel text="Zurück" position="780,666" size="120,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<ePixmap position="910,664" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/info.png" alphatest="blend" zPosition="1" />
		<ePixmap position="730,664" size="46,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/ok.png" alphatest="blend" zPosition="1" />
		<widget name="play" position="1094,664" size="20,28" alphatest="blend" zPosition="2" />
		<eLabel name="" position="252,162" size="32,18" zPosition="-1" backgroundColor="#00505050" cornerRadius="2" />
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

	def __init__(self, session, currAssetUrl, zapAllowed=False):
		self.currAssetUrl = currAssetUrl
		self.zapAllowed = zapAllowed
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		Screen.__init__(self, session)
		self.assetTitle, self.timeStartEnd, self.spanStartsStr = "", "", ""
		self.currServiceRef, self.subLine, self.trailerUrl = "", "", ""
		self.spanDuranceTs = 0
		self.dataBases = []
		self.currDateDt = datetime.today()
		self["release"] = StaticText(tvglobals.RELEASE)
		self["longDescription"] = ScrollLabel()
		for wname in ["editorial", "conclusion", "repeatHint", "credits", "imdbRating", "timeStartEnd",
						"title", "reviewdate", "channelName", "key_info", "key_play"]:
			self[wname] = StaticText()
		for wname in ["picon", "image", "playButton", "fsk", "isTopTip", "isTipOfTheDay", "isNew",
						"isIMDB", "isTMDB", "hasTimer", "thumb", "play"]:
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
		self["key_blue"] = StaticText("Zap" if zapAllowed else "")
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
													"blue": self.zapToCurrent,
													"yellow": self.openEPGSearch,
													"cancel": self.keyExit}, -1)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		for widget, iconfile in [("isTopTip", "top.png"), ("isNew", "new.png"), ("isTipOfTheDay", "tip.png"),
								("hasTimer", "timer.png"), ("isIMDB", "imdb.png"), ("isTMDB", "tmdb.png")]:
			self[widget].instance.setPixmapFromFile(f"{tvglobals.ICONPATH}{iconfile}")
		for icon in [("playButton", "playbutton.png")]:
			iconfile = join(tvglobals.ICONPATH, icon[1])
			if exists(iconfile):
				self[icon[0]].instance.setPixmapFromFile(iconfile)
				self[icon[0]].show()
			else:
				self[icon[0]].hide()
		callInThread(self.showAssetDetails, self.currAssetUrl, fullScreen=True)

	def keyGreen(self):
		startTs, endTs = self.splitTimespan(self.timeStartEnd.split(" - "), datetime.today())  #  e.g. '20:15 - 21:45' or 'heute | 20:15'
		hasTimer = self.isAlreadyListed((startTs, endTs), self.currServiceRef)  # timeSpan, sref
		if not hasTimer:
			startTs -= int(config.recording.margin_before.value) * 60
			endTs += int(config.recording.margin_after.value) * 60
			data = (startTs, endTs, self.assetTitle, self.subLine, None)
			self.addE2Timer(ServiceReference(self.currServiceRef), data)

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
		self.close(False)  # return to main menu


class TVtipsBox(Screen):
	skin = """
	<screen name="TVtips" position="50,center" size="410,264" flags="wfNoBorder" backgroundColor="#16000000" resolution="1280,720" title="TV Spielfilm Tipps">
		<eLabel position="0,0" size="410,264" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="406,260" zPosition="-2" />
		<eLabel name="TVSPro_line" position="2,38" size="406,2" backgroundColor=" #0027153c, #00101093, black, horizontal" zPosition="10" />
		<eLabel name="TVSPro_line" position="2,234" size="406,2" backgroundColor=" #0027153c, #00101093, black, horizontal" zPosition="10" />
		<eLabel name="TV_bg" position="2,2" size="406,36" backgroundColor=" black, #00203060, horizontal" zPosition="0" />
		<widget name="image" position="6,42" size="200,150" alphatest="blend" scaleFlags="scaleCenterBottom" zPosition="1" />
		<widget name="fsk" position="10,148" size="40,40" alphatest="blend" zPosition="2" />
		<widget name="picon" position="258,92" size="100,60" alphatest="blend" scaleFlags="scale" zPosition="1" />
		<widget name="hasTimer" position="359,92" size="14,14" alphatest="blend" zPosition="1" />
		<widget source="channelName" render="Label" position="212,42" size="194,48" font="Regular; 20" halign="center" valign="center" foregroundColor="#92cbdf" backgroundColor="#16000000" transparent="1" />
		<widget source="timeInfos" render="Label" position="212,156" size="194,24" font="Regular; 18" backgroundColor="#16000000" transparent="1" halign="center" />
		<widget source="imdbRating" render="Label" position="212,178" size="194,24" font="Regular; 18" foregroundColor="grey" backgroundColor="#16000000" transparent="1" halign="center" />
		<widget source="headline" render="Label" position="2,1" size="406,36" font="Regular; 24" wrap="ellipsis" backgroundColor="#16000000" zPosition="1" halign="center" valign="center" transparent="1" />
		<ePixmap position="8,14" size="24,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/left.png" alphatest="blend" zPosition="1" />
		<ePixmap position="384,14" size="24,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/icons/right.png" alphatest="blend" zPosition="1" />
		<widget source="title" render="Label" position="10,204" size="396,28" font="Regular;20" wrap="ellipsis" foregroundColor="#0092cbdf" backgroundColor="#16000000" halign="left" valign="center" transparent="1" />
		<eLabel text="Genre:" position="10,236" size="66,24" font="Regular;18" backgroundColor="#16000000" transparent="1" halign="left" valign="center" />
		<widget source="genre" render="Label" position="68,236" size="286,24" font="Regular; 18" backgroundColor="#16000000" transparent="1" halign="left" valign="center" />
		<widget source="category" render="Label" position="278,236" size="120,24" font="Regular; 18" backgroundColor="#16000000" transparent="1" halign="right" valign="center" />
		<widget name="thumb" position="362,102" size="40,40" alphatest="blend" zPosition="1" />
		<widget name="isTopTip" position="222,96" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isTipOfTheDay" position="222,116" size="28,14" alphatest="blend" zPosition="1" />
		<widget name="isNew" position="222,136" size="28,14" alphatest="blend" zPosition="1" />
	</screen>
	"""

	def __init__(self, session):
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		Screen.__init__(self, session)
		for widget in ["headline", "title", "timeInfos", "genre", "channelName", "imdbRating",
						"category", "imdbRating", "editorial", "conclusion"]:
			self[widget] = StaticText()
		for widget in ["isTopTip", "isTipOfTheDay", "isNew", "thumb", "image", "fsk", "picon", "hasTimer"]:
			self[widget] = Pixmap()
		self.isVisible = False
		self.wasVisible = False

	def showDialog(self):
		self.isVisible = True
		self.show()

	def hideDialog(self):
		self.wasVisible = self.isVisible
		self.isVisible = False
		self.hide()

	def getIsVisible(self):
		return self.isVisible

	def getWasVisible(self):
		return self.wasVisible

	def setText(self, widget, text):
		self[widget].setText(text)

	def setWidgetImage(self, widget, imagefile):
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

	def showDialog(self, info, timeout=2500):
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
		<eLabel name="button_blue" position="160,146" size="6,30" backgroundColor="#101093,#4040ff,vertical" zPosition="1" />
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

	def hideDialog(self):
		self.wasVisible = self.isVisible
		self.isVisible = False
		self.hide()

	def getWasVisible(self):
		return self.wasVisible

	def getIsVisible(self):
		return self.isVisible

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


class TVoverview(TVscreenHelper, Screen):
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
		<widget source="release" render="Label" position="180,28" size="80,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
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
				MultiContentEntryText(pos=(184,0), size=(456,26), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS, text=5),  # title
				MultiContentEntryText(pos=(184,22), size=(456,22), font=1, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS, text=6),  # info
				MultiContentEntryPixmapAlphaBlend(pos=(640,4), size=(40,40), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=7),  # thumb
				MultiContentEntryPixmapAlphaBlend(pos=(680,0), size=(40,14), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=8),  # icon0
				MultiContentEntryPixmapAlphaBlend(pos=(680,16), size=(40,14), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=9),  # icon1
				MultiContentEntryPixmapAlphaBlend(pos=(680,32), size=(40,14), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=10),  # icon2
				MultiContentEntryPixmapAlphaBlend(pos=(56,0), size=(14,14), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER, png=11)  # icon3
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
		<widget name="picon" position="760,210" size="147,88" alphatest="blend" scaleFlags="scale" zPosition="1" />
		<widget source="channelName" render="Label" position="740,178" size="187,32" font="Regular; 24" halign="center" foregroundColor="#92cbdf" backgroundColor="#16000000" transparent="1" />
		<widget name="image" position="936,66" size="320,240" alphatest="blend" scaleFlags="centerBottom" zPosition="1" />
		<widget name="playButton" position="1060,160" size="60,60" alphatest="blend" zPosition="2" />
		<widget name="fsk" position="940,262" size="40,40" alphatest="blend" zPosition="2" />
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
		<eLabel name="button_yellow" position="256,660" size="6,36" backgroundColor=" #007a6213, #00e6c619, vertical" zPosition="1" />
		<eLabel name="button_blue" position="362,660" size="6,36" backgroundColor="#101093,#4040ff,vertical" zPosition="1" />
		<widget source="key_red" render="Label" position="20,666" size="130,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_green" render="Label" position="160,666" size="96,26" font="Regular;18" valign="center" halign="left" wrap="ellipsis" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_yellow" render="Label" position="266,666" size="96,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
		<widget source="key_blue" render="Label" position="372,666" size="96,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
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

	def __init__(self, session, userspan, singleChannelId=""):
		self.session = session
		self.spanStartsStr, self.timeCode, self.spanDuranceTs = userspan[0][0], userspan[0][1], int(userspan[1])
		self.singleChannelId = singleChannelId
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		Screen.__init__(self, session)
		self.tvinfobox = session.instantiateDialog(TVinfoBox)
		self.filterIndex = config.plugins.tvspielfilm.filter.value
		self.currDateDt = datetime.today()
		self.dataBases, self.skinList, self.skinDicts = [], [], []
		self.currDayDelta, self.lenImportdict, self.totalAssetsCount = 0, 0, 0
		self.assetTitle, self.trailerUrl, self.currImdbId, self.currTmdbId = "", "", "", ""
		self.channelName, self.currServiceRef, self.currAssetUrl = "", "", ""
		self.loadAllEPGactive, self.loadAllEPGstop, self.zapAllowed = False, False, False
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
		self["key_green"] = StaticText("Timer")
		self["key_yellow"] = StaticText("EPG-Suche")
		self["key_blue"] = StaticText()
		self["actions"] = ActionMap(["OkCancelActions",
									"ButtonSetupActions"],
													{"ok": self.keyOk,
													"play": self.playTrailer,
													"playpause": self.playTrailer,
													"red": self.keyRed,
													"green": self.keyGreen,
													"yellow": self.openEPGSearch,
													"blue": self.zapToCurrent,
													"channeldown": self.prevday,
													"channelup": self.nextday,
													"previous": self.prevweek,
													"next": self.nextweek,
													"info": self.keyInfo,
													"cancel": self.keyExit}, -1)
		tvglobals.IMPORTDICT = self.readImportedFile()  # lade importierte Senderdaten
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self["menuList"].onSelectionChanged.append(self.showCurrentAsset)
		self["key_red"].setText(f"Filter: {ASSETFILTERS[self.filterIndex][0]}")
		for widget, iconfile in [("isTopTip", "top.png"), ("isNew", "new.png"), ("isTipOfTheDay", "tip.png"),
								("hasTimer", "timer.png"), ("isIMDB", "imdb.png"), ("isTMDB", "tmdb.png")]:
			self[widget].instance.setPixmapFromFile(f"{tvglobals.ICONPATH}{iconfile}")
		for icon in [("play", "play.png"), ("playButton", "playbutton.png")]:
			iconfile = join(tvglobals.ICONPATH, icon[1])
			if exists(iconfile):
				self[icon[0]].instance.setPixmapFromFile(iconfile)
				self[icon[0]].show()
			else:
				self[icon[0]].hide()
		self.startLoadAllEPG()

	def startLoadAllEPG(self):
		self.currDateDt = datetime.today() + timedelta(days=self.currDayDelta)
		self.setReviewdate(self.currDateDt, timeStartEnd="", fullScreen=False)
		self.setLongstatus()
		if self.loadAllEPGactive:
			self.loadAllEPGstop = True
		else:
			self.loadAllEPGstop = False
			callInThread(self.loadAllEPG, self.startLoadAllEPGfinish)

	def startLoadAllEPGfinish(self):
		self.loadAllEPGstop = False
		self.refreshSkinlist()
		self.showCurrentAsset()
		callInThread(self.loadAllEPG, self.startLoadAllEPGfinish)  # restart interrupted thread with new current datetime

	def loadAllEPG(self, FinishOnStop):
		self.loadAllEPGactive = True
		self["longStatus"].setText("")
		self.lenImportdict = len(tvglobals.IMPORTDICT)
		self["progressBar"].setRange((0, self.lenImportdict))
		self["progressBar"].setValue(0)
		self["progressTxt"].setText(f"{1}/{self.lenImportdict}")
		if self.singleChannelId:
			self.channelName = tvglobals.IMPORTDICT.get(self.singleChannelId, ["", "{unbekannt}"])[1]
		channelText = f"'{self.channelName}'" if self.channelName else "..."
		self["shortStatus"].setText(f"Lade TVS-EPG Daten für {channelText}")
		self.allAssetsCount, self.allImagesCount = 0, 0
		self.skinDicts, self.skinList = [], []
		now = datetime.today()
		now -= timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)  # round to last 15 minutes in case of 'Jetzt im TV'
		hour, minute = self.spanStartsStr.split(":") if self.spanStartsStr else [now.strftime("%H"), now.strftime("%M")]  # self.spanstartsStr empty = 'Jetzt im TV'
		spanStartsDt = self.currDateDt.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
		spanEndsDt = spanStartsDt + (timedelta(days=1) if self.singleChannelId else timedelta(minutes=self.spanDuranceTs))
		allAssets = self.loadAllAssets(spanStartsDt, channelId=self.singleChannelId)
		if not allAssets:  # build allAssets, channel by channel
			for index, channelDict in enumerate(tvglobals.IMPORTDICT.items()):
				if self.loadAllEPGstop:
					break
				channelId = channelDict[0].lower()
				channelName = channelDict[1][1]
				self["shortStatus"].setText(f"Lade TVS-EPG Daten für '{channelName}'")
				if self.singleChannelId and self.singleChannelId != channelId:
					continue  # skip downloads unless it is the desired channel in case of mode 'single channel' only
				page, maxPage = 0, 1
				while page < maxPage:
					if self.loadAllEPGstop:
						break
					errmsg, assetsDict, lastPage = tvspassets.parseChannelPage(channelId, dateStr=spanStartsDt.strftime("%F"), timeCode=self.timeCode, page=page + 1)
					if errmsg:
						print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVoverview:loadAllEPG' - parsing failed: {errmsg}")
					if not page:  # in case this is the first page
						maxPage = lastPage
					allAssets += assetsDict
					page += 1
				self.createAssetsLists(allAssets, spanStartsDt, spanEndsDt, now)
				self["progressBar"].setValue(index + 1)
				self["progressTxt"].setText(f"{index + 1}/{self.lenImportdict}")
			saveErr = self.saveAllAssets(allAssets, spanStartsDt, channelId=self.singleChannelId)
			if saveErr:
				self.session.open(MessageBox, "Der Datensatz 'Sendungsdetails' konnte nicht gespeichert werden:\n'%s'" % saveErr, type=MessageBox.TYPE_ERROR, timeout=2, close_on_any_key=True)
		self.createAssetsLists(allAssets, spanStartsDt, spanEndsDt, now)
		self.setLongstatus()
		self["progressBar"].setValue(0)
		self["progressTxt"].setText("")
		self["shortStatus"].setText("")
		self.loadAllEPGactive = False
		if self.loadAllEPGstop and FinishOnStop:
			FinishOnStop()

	def createAssetsLists(self, allAssets, spanStartsDt, spanEndsDt, now):
			skinDicts = []
			importDict = tvglobals.IMPORTDICT.keys()
			catFilters = {value: key for key, value in tvspassets.catFilters.items()}  # swap dict
			self.totalAssetsCount = 0
			for assetDict in allAssets:
				if self.loadAllEPGstop:
					break
				channelId = assetDict.get("channelId", "").lower()
				timeStartIso = assetDict.get("timeStart", "")
				timeStartDt = datetime.fromisoformat(timeStartIso).replace(tzinfo=None) if timeStartIso else spanStartsDt.replace(tzinfo=None)
				if channelId in importDict and timeStartDt < spanEndsDt:  # channel was imported and begins before span ends
					timeEndIso = assetDict.get("timeEnd", "")
					timeEndDt = datetime.fromisoformat(timeEndIso).replace(tzinfo=None) if timeEndIso else spanEndsDt
					progress = -1
					if timeEndDt:
						durance = timeEndDt - timeStartDt
						progress = int(((now - timeStartDt) / durance) * 100) if durance else -1
					assetUrl = assetDict.get("assetUrl", "")
					title = assetDict.get("title", "")
					category = assetDict.get("category", "")  # e.g. 'SP' for 'Spielfilm'
					genre = assetDict.get("genre", "")  # e.g. 'Katastrophenaction'
					timespanTs = (int(timeStartDt.timestamp()), int(timeEndDt.timestamp()))
					channelName = assetDict.get("channelName", "") if config.plugins.tvspielfilm.channelname.value else tvglobals.IMPORTDICT.get(channelId, ["", "{unbekannt}"])[1]
					info = " | ".join(filter(None, [genre, catFilters.get(category, ""), f"{assetDict.get('countryYear', '')}"]))
					thumbIdNumeric = assetDict.get("thumbIdNumeric", 0)
					thumbIdNumeric = 3 - thumbIdNumeric if thumbIdNumeric else -1
					isTopTip = assetDict.get("isTopTip", False)
					isTipOfTheDay = assetDict.get("isTipOfTheDay", False)
					isNew = assetDict.get("isNew", False)
					sref = tvglobals.IMPORTDICT.get(channelId, ["", ""])[0]
					skinDict = {"assetUrl": assetUrl, "channelId": channelId, "channelName": channelName, "sref": sref, "timespanTs": timespanTs,
								"progress": progress, "title": title, "info": info, "category": category, "genre": genre,
								"thumbIdNumeric": thumbIdNumeric, "isTopTip": isTopTip, "isTipOfTheDay": isTipOfTheDay, "isNew": isNew}
					skinDicts.append(skinDict)
					if not self.totalAssetsCount:  # immediate display of details after downloading the very first asset
						self.currAssetUrl = assetUrl  # set 'assetUrl is still active'
						callInThread(self.showAssetDetails, assetUrl, fullScreen=False)
					self.totalAssetsCount += 1
			self.skinDicts = skinDicts
			self.refreshSkinlist()

	def setLongstatus(self):
		msg = f"{self.totalAssetsCount} Einträge"
		if self.singleChannelId:
			channelName = self.channelName if config.plugins.tvspielfilm.channelname.value else tvglobals.IMPORTDICT.get(self.singleChannelId, ["", "{unbekannt}"])[1]
			msg += f" im Sender '{channelName}' gefunden."
		else:
			msg += f" in insgesamt {self.lenImportdict} Sendern gefunden."
			lenskinDicts = len(self.skinDicts)
			if self.totalAssetsCount != lenskinDicts:
				msg += f" Gefilterte Einträge: {lenskinDicts}"
		self["longStatus"].setText(msg)

	def refreshSkinlist(self):
		skinlist = []
		listpos, entrycounter = 0, 0
		currfilter = ASSETFILTERS[self.filterIndex]
		for assetDict in self.skinDicts:
			if currfilter[1]:  # is a filter set?
				leaveout = True
				if currfilter[1] == "thumb" and assetDict["thumbIdNumeric"] > -1:
					leaveout = False
				elif currfilter[1] in tvspassets.catFilters.values():
					if currfilter[1] == assetDict.get("category"):  # e.g. 'SP' for 'Spielfilm'
						leaveout = False
				else:
					for assetFlag in [(assetDict["isTipOfTheDay"], "isTipOfTheDay"), (assetDict["isTopTip"], "isTopTip"), (assetDict["isNew"], "isNew")]:
						if assetFlag[0] and assetFlag[1] == currfilter[1]:
							leaveout = False
							break
				if leaveout:
					continue
			assetUrl, channelName, timespanTs = assetDict["assetUrl"], assetDict["channelName"], assetDict["timespanTs"]
			progress, title, info, sref = assetDict["progress"], assetDict["title"], assetDict["info"], assetDict["sref"]
			hasTimer = self.isAlreadyListed(assetDict["timespanTs"], assetDict["sref"])
			piconfile = self.getPiconFile(assetDict["channelId"])
			piconpix = LoadPixmap(cached=True, path=piconfile) if piconfile and exists(piconfile) else None
			timeSpan = f"{datetime.fromtimestamp(timespanTs[0]).strftime('%H:%M')} - {datetime.fromtimestamp(timespanTs[1]).strftime('%H:%M')}"
			thumb = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}thumb{assetDict['thumbIdNumeric']}.png") if assetDict['thumbIdNumeric'] > -1 else None
			icon0 = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}top.png") if assetDict['isTopTip'] else None
			icon1 = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}tip.png") if assetDict['isTipOfTheDay'] else None
			icon2 = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}new.png") if assetDict['isNew'] else None
			icon3 = LoadPixmap(cached=True, path=f"{tvglobals.ICONPATH}timer.png") if hasTimer else None  # timer-icon
			skinlist.append((assetUrl, piconpix, channelName, timeSpan, progress, title, info, thumb, icon0, icon1, icon2, icon3, sref))
			self.skinList = skinlist
			if progress > -1 and progress < 101 and not listpos:  # transmission currently on air?
				listpos = entrycounter
			entrycounter += 1
		if not skinlist:
			skinlist.append(("", None, "", "", -1, "keine Einträge gefunden", f"Der Filter '{currfilter[0]}' liefert für diesen Zeitraum kein Ergebnis.", None, None, None, None, ""))
			self.skinList = []
			self.hideCurrentAsset()
		self["menuList"].updateList(skinlist)
		if self.singleChannelId:
			self["menuList"].setCurrentIndex(listpos)

	def showCurrentAsset(self):
		if self.skinList:
			curridx = min(self["menuList"].getCurrentIndex(), len(self.skinList) - 1)
			self.currAssetUrl = self.skinList[curridx][0]
			progress = self.skinList[curridx][4]
			self.zapAllowed = progress > -1 and progress < 101  # progressbar visible means: transmission is currently on air
			self["key_blue"].setText("Zap" if self.zapAllowed else "")
			callInThread(self.showAssetDetails, self.currAssetUrl, fullScreen=False)

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
		if self.skinList:
			curridx = min(self["menuList"].getCurrentIndex(), len(self.skinList) - 1)
			currAssetUrl = self.skinList[curridx][0]
			self.session.openWithCallback(self.keyOkCB, TVfullscreen, currAssetUrl, self.zapAllowed)

	def keyOkCB(self, answer):
		if answer:
			self.close(True)  # close plugin (e.g. after zap)

	def keyRed(self):
		self.filterIndex = (self.filterIndex + 1) % len(ASSETFILTERS)
		self["key_red"].setText(f"Filter: {ASSETFILTERS[self.filterIndex][0].replace('Unterhaltung', 'Unterhalt.')}")
		self.refreshSkinlist()
		self.showCurrentAsset()
		self.setLongstatus()

	def keyGreen(self):
		if self.skinList:
			current = self["menuList"].getCurrentIndex()
			skinlist = self.skinList[current]
			startTs, endTs = self.splitTimespan(skinlist[3].split(" - "), datetime.today())  #  e.g. '20:15 - 21:45' or 'heute | 20:15'
			hasTimer = self.isAlreadyListed((startTs, endTs), skinlist[12])
			if not hasTimer:
				title = skinlist[5]
				shortdesc = skinlist[6]
				serviceRef = ServiceReference(skinlist[12])
				startTs -= int(config.recording.margin_before.value) * 60
				endTs += int(config.recording.margin_after.value) * 60
				data = (startTs, endTs, title, shortdesc, None)
				self.addE2Timer(serviceRef, data)

	def addE2Timer(self, serviceRef, data):
		newEntry = RecordTimerEntry(serviceRef, checkOldTimers=False, dirname=preferredTimerPath(), fixDescription=True, *data)
		self.session.openWithCallback(self.finishKeyGreen, RecordTimerEdit, newEntry)

	def finishKeyGreen(self, answer):
		if answer and not isinstance(answer, bool):  # Special case for close recursive.
			if answer[0]:
				self.session.nav.RecordTimer.record(answer[1])
				self["hasTimer"].show()
				self["key_green"].setText("")
				self.refreshSkinlist()
				self.showCurrentAsset()

	def prevday(self):
		if self.currDayDelta == -7:
			self.tvinfobox.showDialog("Vergangene TVS-EPG Daten nur bis\nmaximal-7 Tage im Nachhinein verfügbar.")
		else:
			self.currDayDelta = max(self.currDayDelta - 1, -7)  # max. 7 days in past
			self.startLoadAllEPG()

	def prevweek(self):
		if self.currDayDelta == -7:
			self.tvinfobox.showDialog("Vergangene TVS-EPG Daten nur bis\nmaximal -7 Tage im Nachhinein verfügbar.")
		else:
			self.currDayDelta = max(self.currDayDelta - 7, -7)  # max. 7 days in past
			self.startLoadAllEPG()

	def nextday(self):
		if self.currDayDelta == 13:
			self.tvinfobox.showDialog("Zukünftige TVS-EPG Daten nur bis\nmaximal +13 Tage im Voraus verfügbar.")
		else:
			self.currDayDelta = min(self.currDayDelta + 1, 13)  # max. 13 days in future
			self.startLoadAllEPG()

	def nextweek(self):
		if self.currDayDelta == 13:
			self.tvinfobox.showDialog("Zukünftige TVS-EPG Daten nur bis\nmaximal +13 Tage im Voraus verfügbar.")
		else:
			self.currDayDelta = min(self.currDayDelta + 7, 13)  # max. 13 days in future
			self.startLoadAllEPG()

	def keyExit(self):
		self.close(False)  # return to main menu


class TVmain(TVscreenHelper, Screen):
	skin = """
	<screen name="TVmain" position="center,center" size="320,450" resolution="1280,720" backgroundColor="#16000000" flags="wfNoBorder" title="TV Spielfilm Hauptmenü">
		<eLabel position="0,0" size="320,450" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="316,446" zPosition="-1" />
		<eLabel name="TV_bg" position="2,2" size="316,58" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="2,60" size="316,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="2,382" size="316,2" backgroundColor=" #0027153c , #00101093 , black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="2,407" size="316,2" backgroundColor=" #0027153c , #00101093 , black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="80,20" font="Regular;18" textBorderColor="#505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
		<widget source="mainmenu" render="Listbox" position="2,60" size="316,320" itemCornerRadiusSelected="4" itemGradientSelected=" #051a264d, #10304070, #051a264d, horizontal" enableWrapAround="1" foregroundColorSelected="white" backgroundColor="#16000000" transparent="1" scrollbarMode="showOnDemand">
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
		self.tvtipsAllow = True
		self.tipsDicts = []
		self.singleChannelId = ""
		self.currAssetUrl = ""
		self.currTipCnt = 0
		self.currDayDelta = 0
		self.currDateDt = datetime.today()
		self.tvtipsboxTimer = eTimer()
		self.tvtipsboxTimer.callback.append(self.tipSlideshow)
		self.oldChannelName = config.plugins.tvspielfilm.channelname.value
		self["release"] = StaticText(tvglobals.RELEASE)
		self["mainmenu"] = List()
		self["key_red"] = StaticText("Import")
		self["key_green"] = StaticText()
		self["actions"] = ActionMap(["WizardActions",
									"ColorActions",
									"MenuActions"], {"ok": self.keyOk,
														"back": self.exit,
														"right": self.forceNextTip,
														"left": self.forcePrevTip,
														"down": self.down,
														"up": self.up,
														"red": self.keyRed,
														"green": self.keyGreen,
														"yellow": self.keyYellow,
														"blue": self.keyBlue,
														"menu": self.config}, -1)
		tvglobals.IMPORTDICT = self.readImportedFile()  # load imported channel data
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		if self.createTMPpaths():
			self.exit()
		self.cleanupCache()
		if self.updateMappingfile():
			self.tvinfobox.showDialog("Die Sender-Zuweisungstabelle\n'/etc/enigma2/tvspielfilm/tvs_mapping.txt'\nwurde aktualisiert.", 5000)
		callInThread(self.getTips)
		for widget, iconfile in [("isTopTip", "top.png"), ("isTipOfTheDay", "tip.png"), ("isNew", "new.png"), ("hasTimer", "timer.png")]:
			self.tvtipsbox.setWidgetImage(widget, f"{tvglobals.ICONPATH}{iconfile}")
		self.tvupdate.setText("headline", "Sammle TVS-EPG Daten")
		self.tvupdate.setText("key_yellow", "Abbruch")
		self.tvupdate.setText("key_blue", "Ein-/Ausblenden")
		self.selectMainMenu()

	def selectMainMenu(self):
		timespans = self.getUserTimespans()
		usermenu = []
		for index, userspan in enumerate(timespans):  # build main menu
			usermenu.append((f"{userspan[0][0]} im TV", index, TVoverview, userspan))
		usermenu.append(("Jetzt im TV", 4, TVoverview, (("", "now"), config.plugins.tvspielfilm.durance_n.value)))
		usermenu.append(("laufende Sendung", 5))
		usermenu.append(("Senderübersicht", 6))
		usermenu.append(("TVS-EPG Datenupdate", 7))
		usermenu.append(("lösche TVS-EPG Cache", 8))
		self["mainmenu"].updateList(usermenu)

	def keyOk(self):
		current = self["mainmenu"].getCurrent()
		if current:
			if current[1] in [0, 1, 2, 3, 4]:
				self.hideTVtipsBox()
				self.tvupdate.hideDialog()
				self.session.openWithCallback(self.returnOk1, current[2], current[3])
			elif current[1] == 5:
				self.hideTVtipsBox()
				self.tvupdate.hideDialog()
				callInThread(self.getCurrentAssetUrl, self.session.nav.getCurrentlyPlayingServiceOrGroup(), self.returnOk4)
			elif current[1] == 6:
				self.hideTVtipsBox()
				self.tvupdate.hideDialog()
				self.session.openWithCallback(self.returnOk1, selectChannelCategory)
			elif current[1] == 7:
				if TVS_UPDATEACTIVE:
					self.tvinfobox.showDialog("Das TVS-EPG Update läuft bereits.")
				else:
					self.hideTVtipsBox()
					msgtext = "TVS-EPG Update (nur für aktivierte Zeiträume) durchführen?"
					choicelist = [("Abbruch", 0), ("Ergänze nur die fehlenden Datensätze", 1), ("Überschreibe die Datensätze des heutigen Tages", 2), ("Überschreibe alle bereits vorhandene Datensätze", 3)]
					self.session.openWithCallback(self.returnOk2, ChoiceBox, list=choicelist, keys=[], title=msgtext)
			elif current[1] == 8:
				if TVS_UPDATEACTIVE:
					self.tvinfobox.showDialog("Das TVS-EPG Update läuft gerade.\nDer TVS-EPG Zwischenspeicher kann daher im Moment nicht gelöscht werden.")
				else:
					msgtext = "\nTVS-EPG Zwischenspeicher löschen?\n\nDies kann bei Problemen hilfreich sein,\ndanach sollte ein TVS-EPG Datenupdate durchgefürt werden."
					self.session.openWithCallback(self.returnOk3, MessageBox, msgtext, MessageBox.TYPE_YESNO, timeout=10, default=False)

	def returnOk1(self, answer):
		if answer:  # close plugin (e.g. after zap)
			self.exit()
		else:
			if self.tvupdate.getWasVisible():
				self.tvupdate.showDialog()
			self.showTVtipsBox()

	def returnOk2(self, answer):
		if answer:
			if answer[1] == 1:
				callInThread(self.updateFutureEPG, forceRefresh=False)
			elif answer[1] == 2:
				TVS_UPDATESTOP = False
				callInThread(self.updateFutureEPG, todayOnly=True)
			elif answer[1] == 3:
				TVS_UPDATESTOP = False
				callInThread(self.updateFutureEPG)
		self.showTVtipsBox()

	def returnOk3(self, answer):
		if answer is True:
			self.removeTMPpaths()
			self.createTMPpaths()
			self.tvinfobox.showDialog("TVS-EPG Zwischenspeicher (=Cache) erfolgreich gelöscht")

	def returnOk4(self, assetUrl):
		if assetUrl:
			self.session.openWithCallback(self.returnOk1, TVfullscreen, assetUrl)
		else:
			self.session.open(MessageBox, "Dieser Sender wird von TV Spielfilm nicht unterstützt.", type=MessageBox.TYPE_INFO, timeout=2, close_on_any_key=True)

	def keyRed(self):
		if TVS_UPDATEACTIVE:
			self.tvinfobox.showDialog("Das TVS-EPG Update läuft gerade.\nDer TVS Import kann daher im Moment nicht durchgeführt werden.")
		else:
			self.hideTVtipsBox()
			msgtext = "Importiere TV Spielfilm Sender?\nACHTUNG: Der TVS-EPG Zwischenspeicher (=Cache)\nmuß hierfür unwiderruflich gelöscht werden.\nDanach sollte ein TVS-EPG Datenupdate erfolgen.\n\nSind Sie sicher das Sie das wollen?"
			self.session.openWithCallback(self.returnRed, MessageBox, msgtext, MessageBox.TYPE_YESNO, timeout=10, default=False)

	def returnRed(self, answer):
		if answer is True:
			self.session.openWithCallback(self.importfileCB, TVimport)
		else:
			self.showTVtipsBox()

	def importfileCB(self):
		self.removeTMPpaths()
		self.createTMPpaths()
		self.showTVtipsBox()
		self.selectMainMenu()

	def keyGreen(self):
		if self.tvtipsbox.getIsVisible() and self.currAssetUrl:
			self.tvupdate.hideDialog()
			self.hideTVtipsBox()
			self.session.openWithCallback(self.returnOk1, TVfullscreen, self.currAssetUrl)
		else:
			self.showTVtipsBox()

	def keyYellow(self):
		if TVS_UPDATEACTIVE:
			self.session.openWithCallback(self.returnYellow, MessageBox, '\nTVS-EPG Update abbrechen?', MessageBox.TYPE_YESNO, timeout=10, default=False)

	def returnYellow(self, answer):
		if answer is True:
			TVS_UPDATESTOP = True

	def keyBlue(self):
		if self.tvupdate.getIsVisible():
			self.tvupdate.hideDialog()
		elif TVS_UPDATEACTIVE:
			self.tvupdate.showDialog()

	def down(self):
		self["mainmenu"].down()

	def up(self):
		self["mainmenu"].up()

	def leftUp(self):
		self["mainmenu"].pageUp()

	def rightDown(self):
		self["mainmenu"].pageDown()

	def showTVtipsBox(self, delay=5000, firstTip=False):  # special case: the first tip could only be displayed after opening a screen and then interfere
		if not firstTip:
			self.tvtipsAllow = True
		if self.tipsDicts and self.tvtipsAllow and (firstTip or config.plugins.tvspielfilm.showtips.value == 2):  # show tips allways?
			self.tvtipsbox.showDialog()
			self.tvtipsboxTimer.start(delay, False)
			self["key_green"].setText("Sendungsdetail")
			self.tipSlideshow()

	def hideTVtipsBox(self):
		self.tvtipsAllow = False
		if self.tipsDicts:
			self.tvtipsboxTimer.stop()
			self.tvtipsbox.hideDialog()
			self["key_green"].setText("Tipps anzeigen")

	def tipSlideshow(self):
		self.showTip()
		self.currTipCnt = (self.currTipCnt + 1) % len(self.tipsDicts)

	def forceNextTip(self):
		if self.tvtipsbox.getIsVisible():
			self.tvtipsboxTimer.stop()
			self.tvtipsboxTimer.start(5000, False)
			self.currTipCnt = (self.currTipCnt + 1) % len(self.tipsDicts)
			self.showTip()
		else:
			self.rightDown()

	def forcePrevTip(self):
		if self.tvtipsbox.getIsVisible():
			self.tvtipsboxTimer.stop()
			self.tvtipsboxTimer.start(5000, False)
			self.currTipCnt = (self.currTipCnt - 1) % len(self.tipsDicts)
			self.showTip()
		else:
			self.leftUp()

	def getTips(self, forceRefresh=False):
		tipsfile = join(f"{self.getTMPpath()}cache/", f"allTips_{datetime.today().strftime('%F')}.json")
		self.currTipCnt = 0
		if exists(tipsfile) and not forceRefresh:
			with open(tipsfile, "r") as file:
				completeDict = load(file)
				self.createTipsDict(completeDict)
		else:
			callInThread(tvsptips.parseTips, callback=self.getTipsReturn, passthrough=tipsfile)

	def getTipsReturn(self, completeDict, tipsfile):
		try:
			with open(tipsfile, "w") as file:
				dump(completeDict, file)
		except OSError as errmsg:
			self.session.open(MessageBox, "Datensatz 'Tipps' konnte nicht gespeichert werden:\n'%s'" % errmsg, type=MessageBox.TYPE_ERROR, timeout=2, close_on_any_key=True)
		self.createTipsDict(completeDict)

	def createTipsDict(self, completeDict):
		tipsDicts = []
		importDict = tvglobals.IMPORTDICT.keys()
		for index, tipDict in enumerate(completeDict):
			channelId = tipDict.get("channelId", "").lower()
			if channelId in importDict:  # channel was imported?
				isTipOfTheDay = tipDict.get("isTipOfTheDay", False)
				programType = tipDict.get("programType", "")
				if channelId not in tvglobals.IMPORTDICT and isTipOfTheDay or (index == 2 and programType != "SP"):
					continue
				self.currAssetUrl = tipDict.get("assetUrl", "")
				title = tipDict.get("title", "")
				timeInfos = tipDict.get("timeInfos", "")
				imgUrl = tipDict.get("imgUrl", "")
				if imgUrl:
					imgFile = self.convertImageFilename(imgUrl)
					if imgFile and not exists(imgFile):
						if index:
							callInThread(self.imageDownload, imgUrl, imgFile, assetUrl=self.currAssetUrl)  # download only image
						else:  # set very first image immediately
							callInThread(self.imageDownload, imgUrl, imgFile, self.setTipImage, self.currAssetUrl)  # download & set image
				genre = tipDict.get("genre", "")  # e.g. 'Katastrophenaction'
				channelName = tipDict.get("channelName", "") if config.plugins.tvspielfilm.channelname.value else tvglobals.IMPORTDICT.get(channelId, ["", "{unbekannt}"])[1]
				thumbIdNumeric = tipDict.get("thumbIdNumeric", 0)
				thumbIdNumeric = 3 - thumbIdNumeric if thumbIdNumeric else -1
				isTopTip = tipDict.get("isTopTip", False)
				isNew = tipDict.get("isNew", False)
				firstYear = tipDict.get("firstYear", "")
				country = tipDict.get("country", "")
				countryYear = tipDict.get("countryYear", "")
				category = tipDict.get("category", "")  # e.g. 'SP' for 'Spielfilm'
				imdbRating = tipDict.get("imdbRating", "")
				imdbRating = f"IMDb-Wertung: {imdbRating}" if imdbRating else ""
				fsk = tipDict.get("fsk", "")
				fskText = f"ab {fsk} Jahren" if fsk and fsk > -1 else ""
				metaInfo = tipDict.get("metaInfo", {})
				conclusion = metaInfo.get("conclusion", "")
				tipsDicts.append({"title": title, "timeInfos": timeInfos, "genre": genre, "category": category, "channelName": channelName,
								"countryYear": countryYear, "imdbRating": imdbRating, "fskText": fskText, "conclusion": conclusion, "isTopTip": isTopTip,
								"isTipOfTheDay": isTipOfTheDay, "isNew": isNew, "fsk": fsk, "thumbIdNumeric": thumbIdNumeric, "imgUrl": imgUrl,
								"channelId": channelId, "assetUrl": self.currAssetUrl, "firstYear": firstYear, "country": country})
		self.tipsDicts = tipsDicts
		self.showTVtipsBox(firstTip=self.currTipCnt == 0)

	def setTipImage(self, imgFile, tipId):
		if exists(imgFile) and tipId == self.currAssetUrl:  # show if current tip is still displayed
			self.tvtipsbox.setWidgetImage("image", imgFile)
			self.tvtipsbox.showWidget("image")

	def config(self):
		self.hideTVtipsBox()
		self.oldChannelName = config.plugins.tvspielfilm.channelname.value
		self.session.openWithCallback(self.configCB, TVsetup)

	def configCB(self):
		if self.oldChannelName != config.plugins.tvspielfilm.channelname.value:
			callInThread(self.getTips, forceRefresh=True)
		else:
			self.showTVtipsBox()
		self.selectMainMenu()

	def exit(self):
		if TVS_UPDATEACTIVE:
			self.session.openWithCallback(self.returnExit, MessageBox, '\nDas TVS-EPG Update läuft gerade!\nTVS-EPG Update abbrechen und Plugin verlassen?', MessageBox.TYPE_YESNO, timeout=10, default=False)
		else:
			self.returnExit(True)

	def returnExit(self, answer):
		if answer is True:
			TVS_UPDATESTOP = True
			self.session.deleteDialog(self.tvupdate)
			self.session.deleteDialog(self.tvinfobox)
			self.session.deleteDialog(self.tvtipsbox)
			self.close()

	def removeTMPpaths(self):
		tmppath = self.getTMPpath()
		for path in [f"{tmppath}cache/", f"{tmppath}assets/", f"{tmppath}images/", tmppath]:
			if exists(path):
				rmtree(path)

	def showTip(self):
		tipDict = self.tipsDicts[self.currTipCnt]
		headline = f"Tipp des Tages ({self.currTipCnt + 1}/{len(self.tipsDicts)})"
		for text, widget in [(headline, "headline"), (tipDict.get("title", ""), "title"), (tipDict.get("timeInfos", ""), "timeInfos"),
							(tipDict.get("genre", ""), "genre"), (tipDict.get("channelName", ""), "channelName"),
							(tipDict.get("imdbRating", ""), "imdbRating"), (tipDict.get("category", ""), "category"),
							(tipDict.get("imdbRating", ""), "imdbRating"), (tipDict.get("conclusion", ""), "conclusion")]:
			self.tvtipsbox.setText(widget, text)
		for tipFlag, widget in [(tipDict.get("isTopTip", ""), "isTopTip"), (tipDict.get("isTipOfTheDay", ""), "isTipOfTheDay"), (tipDict.get("isNew", ""), "isNew")]:
			if tipFlag:
				self.tvtipsbox.showWidget(widget)
			else:
				self.tvtipsbox.hideWidget(widget)
		fsk = tipDict.get("fsk", "")
		fskfile = join(tvglobals.ICONPATH, f"FSK_{fsk}.png") if fsk and fsk > -1 else ""
		if fskfile:
			self.tvtipsbox.setWidgetImage("fsk", fskfile)
			self.tvtipsbox.showWidget("fsk")
		else:
			self.tvtipsbox.hideWidget("fsk")
		thumbIdNumeric = tipDict.get("thumbIdNumeric", 0)
		thumbIdNumeric = 3 - thumbIdNumeric if thumbIdNumeric else -1
		if thumbIdNumeric != -1:
			thumbfile = join(tvglobals.ICONPATH, f"thumb{thumbIdNumeric}.png")
			if exists(thumbfile):
				self.tvtipsbox.setWidgetImage("thumb", thumbfile)
				self.tvtipsbox.showWidget("thumb")
			else:
				self.tvtipsbox.hideWidget("thumb")
		imgUrl = tipDict.get("imgUrl", "")
		self.currAssetUrl = tipDict.get("assetUrl", "")
		imgFile = self.convertImageFilename(imgUrl)
		if exists(imgFile):
			self.tvtipsbox.setWidgetImage("image", imgFile)
			self.tvtipsbox.showWidget("image")
		else:
			callInThread(self.imageDownload, imgUrl, imgFile, self.setTipImage, self.currAssetUrl)  # download image & set (if this tipId is still current)
		piconfile = self.getPiconFile(tipDict.get("channelId", ""))
		if piconfile and exists(piconfile):
			self.tvtipsbox.setWidgetImage("picon", piconfile)
			self.tvtipsbox.showWidget("picon")
		else:
			self.tvtipsbox.hideWidget("picon")
		sref = tvglobals.IMPORTDICT.get(tipDict.get("assetUrl", ""), ["", ""])[0]
		startTs, endTs = tipDict.get("timeStart", ""), 0
		hasTimer = self.isAlreadyListed((startTs, endTs), sref) if startTs and sref else False
		if hasTimer:
			self.tvtipsbox.showWidget("hasTimer")
		else:
			self.tvtipsbox.hideWidget("hasTimer")

	def setProgressRange(self, index, range):
		self.tvupdate.setRange(f"progressBar{index}", range)

	def setProgressValues(self, index, valuelist):
		self.tvupdate.setText(f"progressHdr{index}", valuelist[0])
		self.tvupdate.setValue(f"progressBar{index}", valuelist[1])
		self.tvupdate.setText(f"progressTxt{index}", valuelist[2])

	def updateFutureEPG(self, forceRefresh=True, todayOnly=False):
		global TVS_UPDATEACTIVE, TVS_UPDATESTOP
		TVS_UPDATEACTIVE, TVS_UPDATESTOP = True, False
		self.createTMPpaths()
		self.cleanupCache()
		self.tvupdate.showDialog()
		timespans = self.getUserTimespans()
		maxcachedays = 1 if todayOnly else config.plugins.tvspielfilm.cacherange.value + 1
		progress = 0
		if timespans:
			range0 = maxcachedays * len(timespans)
			self.setProgressRange(0, (0, range0))
			importdict = tvglobals.IMPORTDICT  # mandatory if the thread should continue to run even if the plugin is terminated
			len_importdict = len(importdict)
			self.setProgressRange(1, (0, len_importdict))
			for timespan in timespans:  # go through all defined timespans (A to D)
				if TVS_UPDATESTOP:
					break
				spanStartsStr = timespan[0][0]  # e.g. timespan = (('20:15', 'prime'), 105)
				for index0, day in enumerate(range(maxcachedays)):  # from today up to next to be cached days
					if TVS_UPDATESTOP:
						break
					currDateDt = datetime.today() + timedelta(days=day)
					hour, minute = spanStartsStr.split(":")
					spanStartsDt = currDateDt.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
					weekday = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][currDateDt.weekday()] if index0 else "heute"
					progress += 1
					self.setProgressValues(0, (f"Zeitraum: '{spanStartsStr}' | {weekday} (+{index0}/+{maxcachedays - 1} Tage)", progress, f"{progress}/{range0}"))
					allAssets = self.loadAllAssets(spanStartsDt) if not forceRefresh else []  # load from cache if available and desired
					if not allAssets:  # build allAssets, channel by channel
						for index1, item in enumerate(importdict.items()):
							self.setProgressValues(1, (f"Sender: '{item[1][1]}'", index1 + 1, f"{index1 + 1}/{len_importdict}"))
							channelId = item[0].lower()
							if self.singleChannelId:
								spanStartsDt = currDateDt.replace(hour=0, minute=0, second=0, microsecond=0)
							errmsg, assetsDict, lastPage = tvspassets.parseChannelPage(channelId, dateStr=spanStartsDt.strftime("%F"), timeCode=timespan[0][1])
							if errmsg:
								print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVmain:updateFutureEPG' - parsing failed: {errmsg}")
							allAssets += assetsDict
						saveErr = self.saveAllAssets(allAssets, spanStartsDt)
						if saveErr:
							TVS_UPDATESTOP = True  # forced thread stop due to OS-error
							print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVmain:updateFutureEPG' - saving failed: {saveErr}")
							self.session.open(MessageBox, "Datensatz 'Sendungsdetails' konnte nicht gespeichert werden:\n'%s'" % saveErr, type=MessageBox.TYPE_ERROR, timeout=2, close_on_any_key=True)
		self.tvupdate.hideDialog()
		self.tvinfobox.showDialog("TVS-EPG Update erfolgreich abgebrochen." if TVS_UPDATESTOP else "TVS-EPG Update erfolgreich beendet.")
		TVS_UPDATEACTIVE, TVS_UPDATESTOP = False, False


class selectChannelCategory(TVscreenHelper, Screen):
	skin = """
	<screen name="selectChannelCategory" position="480,50" size="320,620" backgroundColor="#16000000" flags="wfNoBorder" resolution="1280,720" title="TV Spielfilm Servicedatei">
		<eLabel position="0,0" size="320,620" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="316,616" zPosition="-1" />
		<eLabel name="TV_bg" position="2,2" size="316,58" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="2,60" size="316,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="80,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
		<widget source="menulist" render="Listbox" position="2,60" size="316,560" itemCornerRadiusSelected="4" itemGradientSelected=" #051a264d, #10304070, #051a264d, horizontal" enableWrapAround="1" foregroundColorSelected="white" backgroundColor="#16000000" transparent="1" scrollbarMode="showOnDemand">
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
		self.channels, self.categories, self.channelDicts = [], [], []
		self.categoryIndex, self.channelIndex = 0, 0
		self.categoryMenu = True
		self.channelLoaded = False
		self["release"] = StaticText(tvglobals.RELEASE)
		self["menulist"] = List()
		self["actions"] = ActionMap(["OkCancelActions"],
													{"ok": self.keyOk,
													"cancel": self.keyExit}, -1)
		callInThread(self.createChannelDicts)
		self.onLayoutFinish.append(self.refreshMenu)

	def refreshMenu(self):
		self["menulist"].updateList(self.getCategories())

	def createChannelDicts(self):
		channelDicts = []
		for channelDict in tvspchannels.parseChannels():  # add channelNames to dict
			channelDict["channelName"] = tvglobals.IMPORTDICT.get(channelDict["channelId"], ["", "{unbekannt}"])[1]
			channelDicts.append(channelDict)
		self.channelDicts = channelDicts
		self.channelLoaded = True
		self.refreshMenu()

	def getCategories(self):
		usedChannels = []
		categories = []
		importDict = tvglobals.IMPORTDICT.keys()
		for channel in self.channelDicts:
			channelId = channel.get("channelId", "").lower()
			if channelId in importDict:  # channel was imported?
				category = channel.get("category", "")
				if category and category not in categories:  # found category already listed?
					categories.append(category)
				usedChannels.append({"channelId": channelId, "category": category})
		self.categories = categories
		return categories  # e.g. ['Hauptsender', 'Auslandssender', 'Spartensender', 'News und Dokus', 'Dritte Programme', 'Sportsender', 'Kindersender', 'Musiksender', 'Shopping', 'Regionalsender', 'Sky Cinema', 'Pay TV', 'Sky Sport', 'Sky Entertainment']

	def keyExit(self):
		if self.categoryMenu:
			self.close(False)
		else:
			self.categoryMenu = True
			self["menulist"].updateList(self.categories)
			self["menulist"].setCurrentIndex(self.categoryIndex)

	def keyOk(self):
		if self["menulist"] and self.channelLoaded:
			if self.categoryMenu:
				self.categoryMenu = False
				category = self["menulist"].getCurrent()
				self.categoryIndex = self["menulist"].getCurrentIndex()
				channels = []
				importDict = tvglobals.IMPORTDICT.keys()
				for channelDict in self.channelDicts:
					channelId = channelDict.get("channelId", "").lower()
					if channelDict.get("category", "") == category and channelId in importDict:  # channel is in this category and was imported?
						channelName = channelDict.get("channelName", "") if config.plugins.tvspielfilm.channelname.value else tvglobals.IMPORTDICT.get(channelId, ["", ""])[1]
						channels.append((channelName, channelId))
				self.channels = channels
				self["menulist"].updateList(channels)
				self["menulist"].setCurrentIndex(self.channelIndex)
			else:
				self.channelIndex = self["menulist"].getCurrentIndex()
				channel = self["menulist"].getCurrent()  # e.g. ("Das Erste", "ard")
				if channel and len(channel) > 1:
					self.session.openWithCallback(self.keyOkReturn, TVoverview, (("", "day"), 0), singleChannelId=channel[1])

	def keyOkReturn(self, answer):
			if answer:
				self.close(True)


class TVimport(TVscreenHelper, Screen):
	skin = """
	<screen name="TVimport" position="480,90" size="360,550" backgroundColor="#16000000" flags="wfNoBorder" resolution="1280,720" title="TV Spielfilm Servicedatei">
		<eLabel position="0,0" size="360,500" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="356,496" zPosition="-1" />
		<eLabel name="TV_bg" position="2,2" size="356,58" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="2,60" size="356,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="80,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
		<widget source="bouquetslist" render="Listbox" position="2,60" size="356,440" itemCornerRadiusSelected="4" itemGradientSelected=" #051a264d, #10304070, #051a264d, horizontal" enableWrapAround="1" foregroundColorSelected="white" backgroundColor="#16000000" transparent="1" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">{"template": [
				MultiContentEntryText(pos=(0,0), size=(346,40), font=0,  flags=RT_HALIGN_CENTER|RT_VALIGN_CENTER, text=0)  # menutext
				],
				"fonts": [gFont("Regular",24)],
				"itemHeight":40
				}
			</convert>
		</widget>
		<eLabel name="button_blue" position="40,510" size="6,36" backgroundColor="#101093,#4040ff,vertical" zPosition="1" />
		<widget source="key_blue" render="Label" position="54,516" size="300,26" font="Regular;18" valign="center" halign="left" foregroundColor="grey" backgroundColor="#16000000" transparent="1" />
	</screen>
	"""

	def __init__(self, session):
		self.session = session
		if tvglobals.RESOLUTION == "FHD":
			self.skin = self.skin.replace("/HD/", "/FHD/")
		Screen.__init__(self, session)
		self.tvinfobox = session.instantiateDialog(TVinfoBox)
		self.maplist, self.totaldupes, self.totalimport = [], [], []
		self.totalsupp, self.totalunsupp = [], []
		self.mappinglog = ""
		self.mapfile = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_mapping.txt")  # /etc/enigma2/TVSpielfilm/tvs_mapping.txt
		self["release"] = StaticText(tvglobals.RELEASE)
		self["bouquetslist"] = List()
		self["key_blue"] = StaticText("Überprüfe Konvertierungsregeln")
		self['actions'] = ActionMap(["OkCancelActions",
									"ColorActions"], {"ok": self.keyOk,
													"blue": self.keyBlue,
													"cancel": self.keyExit}, -1)
		if self.createTMPpaths():
			self.exit()
		if self.updateMappingfile():
			self.tvinfobox.showDialog("Die Sender-Zuweisungstabelle\n'/etc/enigma2/tvspielfilm/tvs_mapping.txt'\nwurde aktualisiert.", 5000)
		self.maplist = self.readMappingList()
		self.onShown.append(self.shownFinished)

	def shownFinished(self):
		if exists(self.mapfile):
			self.getAllBouquets()
		else:
			print(f"[{tvglobals.MODULE_NAME}] Error in class 'TVimport:shownFinished': file '{self.mapfile}' not found.")
			self.session.open(MessageBox, f"Datei '{self.mapfile}' kann weder gefunden noch angelegt werden.\nTVS Import kann daher nicht fortgefahren werden!", MessageBox.TYPE_ERROR, timeout=30, close_on_any_key=True)
			self.keyExit()

	def keyExit(self):
		self.close()

	def keyBlue(self):
		self.checkMappingRules()
		self.session.open(MessageBox, f"Konvertierungsregeln in der Datei:\n'{self.mapfile}'\nwurden geprüft.\n\nDie detaillierte Analyse finden Sie in der Logdatei:\n'{self.mappinglog}'", MessageBox.TYPE_INFO, timeout=10, close_on_any_key=True)

	def keyOk(self):
		current = self["bouquetslist"].getCurrent()  # e.g. ('Favoriten (TV)', <enigma.eServiceReference; proxy of <Swig Object of type 'eServiceReference *' at 0xa70d46f8> >)
		importlist, dupeslist, supplist, unsupplist = self.importBouquet(current[1])
		if importlist:
			# combine two lists without duplicate entries while retaining the sort order
			self.totalimport = list(dict(dict(self.totalimport), **dict(importlist)).items())  # will be later reduced by TVchannelselection
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
					importedchannels = []
					for index, channel in enumerate(answer[1]):
						if channel[1]:
							importedchannels.append((self.totalimport[index][1][0], (self.totalimport[index][0], self.totalimport[index][1][1])))  # e.g. ('ard', ('1:0:19:283D:41B:1:FFFF0000:0:0:0:', 'Das Erste HD'))
					importfile = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_imported.json")
					with open(f"{importfile}.new", 'w') as file:  # all imported channels only
						dump(dict(importedchannels), file)
						rename(f"{importfile}.new", importfile)
				if self.totalsupp:
					supportedchannels = []
					for index, channel in enumerate(self.totalsupp):
						if channel[1]:
							supportedchannels.append((self.totalsupp[index][1][0], (self.totalsupp[index][0], self.totalsupp[index][1][1])))
					suppfile = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_supported.json")
					with open(f"{suppfile}.new", 'w') as file:  # all channels supported by server
						dump(dict(supportedchannels), file)
						rename(f"{suppfile}.new", suppfile)
				if self.totaldupes:  # all unused (duplicate) channels in bouquets
					dupesfile = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_dupes.json")
					with open(f"{dupesfile}.new", 'w') as file:
						dump(dict(self.totaldupes), file)
					rename(f"{dupesfile}.new", dupesfile)
				if self.totalunsupp:  # all channels not supported by server
					unsuppfile = resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_unsupported.json")
					with open(f"{unsuppfile}.new", 'w') as file:
						dump(dict(self.totalunsupp), file)
					rename(f"{unsuppfile}.new", unsuppfile)
				tvglobals.IMPORTDICT = self.readImportedFile()  # lade importierte Senderdaten
				self.session.open(MessageBox, "Senderimport erfolgreich durchgeführt.", type=MessageBox.TYPE_INFO, timeout=2, close_on_any_key=True)
			else:
				self.session.open(MessageBox, "Senderimport abgebrochen!", type=MessageBox.TYPE_WARNING, timeout=2, close_on_any_key=True)
			self.close()

	def getAllBouquets(self):
		bouquetstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet' if config.usage.multibouquet.value else '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
		root = eServiceReference(bouquetstr)
		serviceHandler = eServiceCenter.getInstance()
		bouquetsList = []
		if config.usage.multibouquet.value:
			slist = serviceHandler.list(root)
			while True:
				service = slist.getNext()
				if not service.valid():
					del slist
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
			sref = f"{service[0].split('http')[0]}{{IPTV-Stream}}" if "http" in service[0].lower() else service[0]
			for channelId, regstr in self.maplist:  # find TVSpielfilm shortcut for channelname
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
		with open(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_mapping.txt")) as file:  # /etc/enigma2/TVSpielfilm
			line = "{No line evaluated yet}"
			try:
				for line in file.read().replace(",", "").strip().split("\n"):
					if not line.startswith("#"):
						items = line.strip().split(": ")
						if items:
							maplist.append((items[0], items[1]))
			except Exception as errmsg:
				print(f"[{tvglobals.MODULE_NAME}] Exception error class 'TVimport:readMappingList' in {line}: {errmsg}")
		return maplist

	def appendImportLog(self, bouquetname, totalfound, importlist, dupeslist, unsupported):  # append last successful import to logfile
		with open(f"{tvglobals.LOGPATH}bouquetimport.log", "a") as file:
			file.write(f"{'=' * 78}\n{len(totalfound)} Kanäle im Bouquet gefunden '{bouquetname}' (inkl. doppelter TVSpielfilm-Kürzel)\n{'=' * 78}\n")
			formatstr = "{0:<10} {1:<40} {2:<0}\n"
			for item in totalfound:
				file.write(formatstr.format(*(item[1][0] or "n/a", item[0], item[1][1])))
			file.write(f"\n{len(importlist)} importierte TVSpielfilm Kanäle (ohne doppelte TVSpielfilm-Verknüpfungen):\n{'-' * 78}\n")
			for item in importlist:
				file.write(formatstr.format(*(item[1][0], item[0], item[1][1])))
			file.write(f"\n{len(dupeslist)} nicht importierte Kanäle (weil doppelte TVSpielfilm-Verknüpfungen):\n{'-' * 78}\n")
			for item in dupeslist:
				file.write(formatstr.format(*(item[1][0], item[0], item[1][1])))
			file.write(f"\n{len(unsupported)} Kanäle, die von TV-Spielfilm nicht unterstützt werden:\n{'-' * 78}\n")
			for item in unsupported:
				file.write(formatstr.format(*("n/a", item[0], item[1][1])))
			file.write("\n")

	def checkMappingRules(self):  # tool: checks whether conversion rules are missing / outdated / double in the mapping file
		maplist = sorted(self.maplist, key=lambda x: x[0])
		mapkeys = [x[0] for x in maplist]
		channelDicts = tvspchannels.parseChannels()
		usedChannels = []
		importDict = tvglobals.IMPORTDICT.keys()
		for channel in channelDicts if channelDicts else []:
			channelId = channel.get("channelId", "").lower()
			if channelId in importDict:  # channel was imported?
				category = channel.get("category", "")  # e.g. 'SP' for 'Spielfilm'
				name = tvglobals.IMPORTDICT.get(channelId, ["", ""])[1]
				usedChannels.append({"channelId": channelId, "name": name, "category": category})
		if usedChannels:
			reskeys = [x.get("channelId", "n/a").lower() for x in usedChannels]
			tabpos = "{0:<10} {1:<0}\n"
			self.mappinglog = join(tvglobals.LOGPATH, "mappingrules.log")
			with open(self.mappinglog, "w") as file:
				file.write(f"{len(usedChannels)} Kanäle gefunden, die von TV Spielfilm unterstützt werden\n")
				file.write("\nFehlende Regel(n) für Kanäle, die von TV Spielfilm unterstützt werden: ")
				notfound = []
				for service in usedChannels:  # search for missing conversion rules
					shortkey = service.get("channelId", "n/a").lower()
					if shortkey not in mapkeys:
						notfound.append((shortkey, service.get("name", "n/v")))
				if notfound:
					file.write(f"\n{tabpos.format(*('Kürzel', 'Sendername'))}")
					file.write(f"{'-' * 58}\n")
					for service in notfound:
						file.write(tabpos.format(*service))
					file.write("EMPFEHLUNG: Diese Regel(n) in die Datei 'tvs_mapping.txt' einpflegen.\n")
				else:
					file.write("{Keine fehlenden Regel(n) gefunden}\n")
				file.write("\nVeraltete Regel(n) für Kanäle, die von TV Spielfilm nicht unterstützt werden: ")
				outdated = []
				for service in maplist:  # search for outdated conversion rules
					if service[0] not in reskeys:
						outdated.append((service[0], service[1]))
				if outdated:
					file.write(f"\n{tabpos.format(*('Kürzel', 'Umsetzungsregel'))}")
					file.write(f"{'-' * 58}\n")
					for service in outdated:
						file.write(tabpos.format(*service))
					file.write("EMPFEHLUNG: Diese Regel(n) aus der Datei 'tvs_mapping.txt' entfernen.\n")
				else:
					file.write("{Keine veraltete Regel(n) gefunden}\n")
				file.write("\nDoppelte Regel(n) für Kanäle, die von TV Spielfilm unterstützt werden: ")
				double = []
				for idx in [i for i, x in enumerate(mapkeys) if mapkeys.count(x) > 1]:  # search for duplicate rules and get indexes
					double.append((maplist[idx][0], maplist[idx][1]))
				if double:
					file.write(f"\n{tabpos.format(*('Kürzel', 'Umsetzungsregel'))}")
					file.write(f"{'-' * 58}\n")
					for service in double:
						file.write(tabpos.format(*service))
					file.write("EMPFEHLUNG: Im Zweifel in der Datei 'tvs_mapping.txt' belasssen! Sender könnten z.B. bei verschiedenen Anbietern unter verschiedenen Namen geführt werden.\n")
				else:
					file.write("{Keine doppelten Regel(n) gefunden}\n")


class TVchannelselection(Screen):
	skin = """
	<screen name="TVchannelselection" position="480,20" size="320,660" backgroundColor="#16000000" flags="wfNoBorder" resolution="1280,720" title="TV Spielfilm Kanalauswahl">
		<eLabel position="0,0" size="320,660" backgroundColor="#00203060" zPosition="-2" />
		<eLabel position="2,2" size="316,656" zPosition="-1" />
		<eLabel name="TV_bg" position="2,2" size="316,58" backgroundColor=" black, #00203060, horizontal" zPosition="1" />
		<eLabel name="TV_line" position="2,60" size="316,2" backgroundColor=" #0027153c , #00101093, black , horizontal" zPosition="10" />
		<eLabel name="TV_line" position="2,616" size="316,2" backgroundColor=" #0027153c , #00101093 , black , horizontal" zPosition="10" />
		<ePixmap position="0,0" size="220,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TVSpielfilm/pics/HD/logos/TVSpielfilm.png" alphatest="blend" zPosition="13" />
		<widget source="release" render="Label" position="180,28" size="80,20" font="Regular;18" textBorderColor="#00505050" textBorderWidth="1" foregroundColor="#00ffff00" backgroundColor="#16000000" valign="center" zPosition="12" transparent="1" />
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
				self.tvinfobox.showDialog("Bitte wählen Sie mindestens einen Sender aus!")
				self.updateChannellist()
			else:
				self.close((True, self.channellist))

	def keyExit(self):
		self.close((False, []))


class TVsetup(TVscreenHelper, Setup):
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


class TVautoUpdate(TVcoreHelper):
	def autoUpdateEPG(self):
		global TVS_UPDATEACTIVE, TVS_UPDATEACTIVE
		TVS_UPDATEACTIVE, TVS_UPDATESTOP = True, False
		self.createTMPpaths()
		self.cleanupCache()
		print(f"[{tvglobals.MODULE_NAME}] Autoupdate starts, cache has been cleaned up")
		timespans = self.getUserTimespans()
		maxcachedays = config.plugins.tvspielfilm.cacherange.value
		if timespans:
			importdict = self.readImportedFile()
			allAssets = []
			for timespan in timespans:  # go through all defined timespans (A to D)
				if TVS_UPDATESTOP:
					break
				spanStartsStr = timespan[0][0]
				for index, day in enumerate(range(maxcachedays + 1)):  # from today up to next to be cached days
					if TVS_UPDATESTOP:
						break
					currDateDt = datetime.today() + timedelta(days=day)
					hour, minute = spanStartsStr.split(":")
					spanStartsDt = currDateDt.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
					weekday = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][currDateDt.weekday()] if index else "heute"
					if not exists(self.allAssetsFilename(spanStartsDt)) or config.plugins.tvspielfilm.autoupdate.value:
						for item in importdict.items():  # build allAssets, channel by channel
							channelId = item[0].lower()
							errmsg, assetsDict, lastPage = tvspassets.parseChannelPage(channelId, dateStr=spanStartsDt.strftime("%F"), timeCode=timespan[0][1])
							if errmsg:
								print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVautoUpdate:autoUpdateEPG' - parsing failed: {errmsg}")
							allAssets += assetsDict
						saveErr = self.saveAllAssets(allAssets, spanStartsDt)
						if saveErr:
							TVS_UPDATESTOP = True  # forced thread stop due to OS-error
							print(f"[{tvglobals.MODULE_NAME}] ERROR in class 'TVautoUpdate:autoUpdateEPG' - record 'program details' could not be saved: {saveErr}")
						else:
							print(f"[{tvglobals.MODULE_NAME}] time period successfully in cache: '{spanStartsStr}' | {weekday} (+{index}/+{maxcachedays} days) for {len(importdict.items())}")
		if TVS_UPDATESTOP:
			print(f"[{tvglobals.MODULE_NAME}] Autoupdate has been interrupted on user demand.")
		print(f"[{tvglobals.MODULE_NAME}] Autoupdate finished")
		TVS_UPDATEACTIVE, TVS_UPDATESTOP = False, False


tvautoupdate = TVautoUpdate()
tvcorehelper = TVcoreHelper()


def startAutoEPGupdate(**kwargs):
	tvautoupdate.autoUpdateEPG()


def stopAutoEPGupdate(**kwargs):
	global TVS_UPDATESTOP
	TVS_UPDATESTOP = False


def showCurrentProgram(session, **kwargs):
	assetUrl = tvcorehelper.getCurrentAssetUrl(session.nav.getCurrentlyPlayingServiceOrGroup())
	if assetUrl:
		session.open(TVfullscreen, assetUrl)
	else:
		session.open(MessageBox, "Dieser Sender wird nicht von TV Spielfilm unterstützt.", type=MessageBox.TYPE_INFO, timeout=2, close_on_any_key=True)


def showNowOnTv(session, **kwargs):
	if exists(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_imported.json")):
		session.open(TVoverview, (("", "now"), config.plugins.tvspielfilm.durance_n.value))
	else:
		session.open(TVimport)


def showPrimeTime(session, **kwargs):
	if exists(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_imported.json")):
		session.open(TVoverview, (STARTTIMES[config.plugins.tvspielfilm.starttime_c.value], config.plugins.tvspielfilm.durance_c.value))
	else:
		session.open(TVimport)


def main(session, **kwargs):
	if exists(resolveFilename(SCOPE_CONFIG, "TVSpielfilm/tvs_imported.json")):
		session.open(TVmain)
	else:
		session.open(TVimport)


def sessionstart(reason, session):
	if reason == 0 and HAS_FUNCTIONTIMER:
		pass
#		functionTimer.add(("TVupdate", {"name": "TV-Spielfilm EPG-Datenupdate", "entryFunction": startAutoEPGupdate, "cancelFunction": stopAutoEPGupdate, "isThreaded": True}))


def autostart(reason, **kwargs):
	pass


def Plugins(**kwargs):
	pdList = [
		PluginDescriptor(name="TV Spielfilm", icon=f"pics/{tvglobals.RESOLUTION}/logos/plugin.png", description="Elektronische Programmzeitschrift mit umfangreichen Zusatzinfos", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, needsRestart=True, fnc=sessionstart),
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, needsRestart=True, fnc=autostart)
		]
	primetime = config.plugins.tvspielfilm.primetime.value
	if primetime & 1:
		pdList.append(PluginDescriptor(name="TV Spielfilm - Primetime 20:15", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=showPrimeTime))
	if primetime & 2:
		pdList.append(PluginDescriptor(name="TV Spielfilm - Primetime 20:15", icon=f"pics/{tvglobals.RESOLUTION}/logos/TV2015.png", description="Zeige die laufenden und nachfolgenden Sendungen der Primetime 20:15 Uhr", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=showPrimeTime))
	if not primetime and hasattr(PluginDescriptor, 'WHERE_BUTTONSETUP'):
		pdList.append(PluginDescriptor(name="TV Spielfilm - Primetime 20:15", where=PluginDescriptor.WHERE_BUTTONSETUP, fnc=showPrimeTime))
	nowontv = config.plugins.tvspielfilm.nowontv.value
	if nowontv & 1:
		pdList.append(PluginDescriptor(name="TV Spielfilm - Jetzt im TV", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=showNowOnTv))
	if nowontv & 2:
		pdList.append(PluginDescriptor(name="TV Spielfilm - Jetzt im TV", icon=f"pics/{tvglobals.RESOLUTION}/logos/TVjetzt.png", description="Zeige die aktuell laufenden und demnächst anstehenden Sendungen", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=showNowOnTv))
	if not nowontv and hasattr(PluginDescriptor, 'WHERE_BUTTONSETUP'):
		pdList.append(PluginDescriptor(name="TV Spielfilm - Jetzt im TV", where=PluginDescriptor.WHERE_BUTTONSETUP, fnc=showNowOnTv))
	if config.plugins.tvspielfilm.currprogram.value == 1:
		pdList.append(PluginDescriptor(name="TV Spielfilm - laufende Sendung", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=showCurrentProgram))
	elif hasattr(PluginDescriptor, 'WHERE_BUTTONSETUP'):
		pdList.append(PluginDescriptor(name="TV Spielfilm - laufende Sendung", where=PluginDescriptor.WHERE_BUTTONSETUP, fnc=showCurrentProgram))
	return pdList

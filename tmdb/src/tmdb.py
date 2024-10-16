#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
# maintainer: schomi@vuplus-support.org
#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.
#######################################################################

from base64 import b64decode
from os import mkdir, remove
from os.path import exists, isdir
from re import search, sub, I, S

from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.config import config
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText

from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.BoundFunction import boundFunction

from enigma import eListboxPythonMultiContent, ePicLoad, eTimer, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER

from skin import parameters
import shutil
from requests import get, exceptions, Session
from PIL import Image

from twisted.internet.reactor import callInThread

import tmdbsimple as tmdb
from .__init__ import _
from .skins import tmdbScreenSkin, tmdbScreenMovieSkin, tmdbScreenPeopleSkin, tmdbScreenPersonSkin, tmdbScreenSeasonSkin


pname = "TMDb"
pdesc = _("Show movie details from TMDb")
pversion = "1.0.1"
pdate = "20230711"

tmdb.REQUESTS_SESSION = Session()
tmdb.REQUESTS_TIMEOUT = (5, 30)

noCover = "/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/no_cover.jpg"
tempDir = "/tmp/tmdb/"

if not isdir(tempDir):
	mkdir(tempDir)

DEFAULT = 0
CURRENT_MOVIES = 1
UPCOMING_MOVIES = 2
POPULAR_MOVIES = 3
SIMILAR_MOVIES = 4
RECOMENDED_MOVIES = 5
BEST_RATED_MOVIES = 6


def debug(s, flag="a"):  # pass
	with open("/usr/lib/enigma2/python/Plugins/Extensions/tmdb/debug.txt", flag) as f:
		f.write(f"{s}\n")


def cleanText(text):
	cutlist = ['x264', '720p', '1080p', '1080i', 'PAL', 'GERMAN', 'ENGLiSH', 'WS', 'DVDRiP', 'UNRATED', 'RETAIL', 'Web-DL', 'DL', 'LD', 'MiC', 'MD', 'DVDR', 'BDRiP', 'BLURAY', 'DTS', 'UNCUT', 'ANiME',
				'AC3MD', 'AC3', 'AC3D', 'TS', 'DVDSCR', 'COMPLETE', 'INTERNAL', 'DTSD', 'XViD', 'DIVX', 'DUBBED', 'LINE.DUBBED', 'DD51', 'DVDR9', 'DVDR5', 'h264', 'AVC',
				'WEBHDTVRiP', 'WEBHDRiP', 'WEBRiP', 'WEBHDTV', 'WebHD', 'HDTVRiP', 'HDRiP', 'HDTV', 'ITUNESHD', 'REPACK', 'SYNC']
	text = text.replace('.wmv', '').replace('.flv', '').replace('.ts', '').replace('.m2ts', '').replace('.mkv', '').replace('.avi', '').replace('.mpeg', '').replace('.mpg', '').replace('.iso', '').replace('.mp4', '')

	for word in cutlist:
		text = sub(r'(\_|\-|\.|\+)' + word + r'(\_|\-|\.|\+)', '+', text, flags=I)
	text = text.replace('.', ' ').replace('-', ' ').replace('_', ' ').replace('+', '').replace(" Director's Cut", "").replace(" director's cut", "").replace("[Uncut]", "").replace("Uncut", "")

	text_split = text.split()
	if text_split and text_split[0].lower() in ("new:", "live:"):
		text_split.pop(0)  # remove annoying prefixes
	text = " ".join(text_split)

	if search(r'[Ss][\d]+[Ee][\d]+', text):
		text = sub(r'[Ss][\d]+[Ee][\d]+.*[\w]+', '', text, flags=S | I)
	text = sub(r'\(.*\)', '', text).rstrip()  # remove episode number from series, like "series name (234)"

	return text


def cleanEnd(text):
	text = text.replace('.wmv', '').replace('.flv', '').replace('.ts', '').replace('.m2ts', '').replace('.mkv', '').replace('.avi', '').replace('.mpeg', '').replace('.mpg', '').replace('.iso', '').replace('.mp4', '')
	return text


def threadDownloadPage(link, file, success, fail=None):
	link = link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', '')
	try:
		response = get(link, timeout=(3.05, 6))
		response.raise_for_status()
		with open(file, "wb") as f:
			f.write(response.content)
		success(file)
	except exceptions.RequestException as error:
		if fail is not None:
			fail(error)


class CoverHelper():
	def __init__(self, backdrop=False, fskLogo=False):
		self['cover'] = Pixmap()
		self.picloadCover = ePicLoad()
		self.picloadCover.PictureData.get().append(self.showCoverCallback)
		if backdrop:
			self['backdrop'] = Pixmap()
			self.picloadBackdrop = ePicLoad()
			self.picloadBackdrop.PictureData.get().append(self.showBackdropCallback)

		if fskLogo:
			self['fsklogo'] = Pixmap()
			self.picloadFsk = ePicLoad()
			self.picloadFsk.PictureData.get().append(self.showFskCallback)

	def decodeCover(self, coverName):
		size = self['cover'].instance.size()
		self.picloadCover.setPara((size.width(), size.height(), 1, 1, False, 1, ""))
		self.picloadCover.startDecode(coverName)

	def decodeBackdrop(self, coverName):
		size = self['backdrop'].instance.size()
		self.picloadBackdrop.setPara((size.width(), size.height(), 1, 1, False, 1, ""))
		self.picloadBackdrop.startDecode(coverName)

	def decodeFsk(self, coverName):
		size = self['fsklogo'].instance.size()
		self.picloadFsk.setPara((size.width(), size.height(), 1, 1, False, 1, ""))
		self.picloadFsk.startDecode(coverName)

	def showCoverCallback(self, picInfo=None):
		ptr = self.picloadCover.getData()
		if ptr is not None:
			self["cover"].instance.setPixmap(ptr.__deref__())
			self["cover"].show()

	def showBackdropCallback(self, picInfo=None):
		ptr = self.picloadBackdrop.getData()
		if ptr is not None:
			self["backdrop"].instance.setPixmap(ptr.__deref__())
			self["backdrop"].show()

	def showFskCallback(self, picInfo=None):
		ptr = self.picloadFsk.getData()
		if ptr is not None:
			self["fsklogo"].instance.setPixmap(ptr.__deref__())
			self["fsklogo"].show()


class createList(MenuList):
	def __init__(self):
		MenuList.__init__(self, [], content=eListboxPythonMultiContent)
		font, size = parameters.get("TMDbListFont", ('Regular', 25))
		self.l.setFont(0, gFont(font, size))
		self.l.setItemHeight(30)
		self.l.setBuildFunc(self.buildList)

	def buildList(self, entry):
		# width = self.l.getItemSize().width()
		res = [None]
		x, y, w, h = parameters.get("TMDbListName", (5, 1, 1920, 40))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]


class tmdbConfigScreen(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "TMDB", plugin="Extensions/tmdb", PluginLanguageDomain="tmdb")
		self.setTitle(f"TMDb - The Movie Database v{pversion}")


class tmdbScreen(Screen, HelpableScreen, CoverHelper):
	skin = tmdbScreenSkin

	def __init__(self, session, text, path=""):
		Screen.__init__(self, session)
		tmdb.API_KEY = b64decode('ZDQyZTZiODIwYTE1NDFjYzY5Y2U3ODk2NzFmZWJhMzk=')
		if config.plugins.tmdb.apiKey.value != "intern":
			tmdb.API_KEY = config.plugins.tmdb.apiKey.value
#		print("[TMDb][tmdbScreen] API Key User: " + str(tmdb.API_KEY))
		self.cert = config.plugins.tmdb.cert.value
		self.text = cleanText(str(text))
		self.saveFilename = str(path)
		self.piclist = ""
		self.covername = noCover
		self.actcinema = DEFAULT
		self.searchtitle = (_("TMDb: ") + _("Results for %s"))
		#self.title = " "
		self.page = 1
		self.id = 1
		if not isdir(tempDir):
			mkdir(tempDir)

		print(f"[TMDb][tmdbScreen] Search for {self.text}")

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "TMDbActions",
			{
				"ok": (self.ok, _("Show details")),
				"cancel": (self.cancel, _("Exit")),
				"up": (self.keyUp, _("Selection up")),
				"down": (self.keyDown, _("Selection down")),
				"nextBouquet": (self.chDown, _("Details down")),
				"prevBouquet": (self.chUp, _("Details up")),
				"left": (self.keyLeft, _("Page up")),
				"right": (self.keyRight, _("Page down")),
				"red": (self.cancel, _("Exit")),
				"green": (self.ok, _("Show details")),
				"yellow": (self.searchString, _("Edit search")),
				"blue": (self.menu, _("More")),
				"menu": (self.setup, _("Setup")),
				"eventview": (self.searchString, _("Edit search"))
			}, -1)

		self['searchinfo'] = Label(_("TMDb: ") + _("Loading..."))
		self['key_red'] = Label(_("Exit"))
		self['key_green'] = Label(_("Details"))
		self['key_yellow'] = Label(_("Edit search"))
		self['key_blue'] = Label(_("More"))
		self["key_menu"] = StaticText(_("MENU"))  # auto menu button
		self['list'] = createList()

		CoverHelper.__init__(self)

		self.onLayoutFinish.append(self.onFinish)

	def onFinish(self):
		if self.text:
			self.timer = eTimer()
			callInThread(self.tmdbSearch)
		else:
			print("[TMDb][tmdbScreen] no movie found.")
			self['searchinfo'].setText(_("TMDb: ") + _("No results for %s") % self.text)

	def menu(self):
		options = [
			(_("Exit"), DEFAULT),
			(_("Current movies in cinemas"), CURRENT_MOVIES),
			(_("Upcoming movies"), UPCOMING_MOVIES),
			(_("Popular movies"), POPULAR_MOVIES),
			(_("Similar movies"), SIMILAR_MOVIES),
			(_("Recommendations"), RECOMENDED_MOVIES),
			(_("Best rated movies"), BEST_RATED_MOVIES)
		]
		self.session.openWithCallback(self.menuCallback, ChoiceBox, list=options)

	def menuCallback(self, ret):
		self.id = 1
		self.title = " "
		self.page = 1
		self.totalpages = 1
		if ret is not None:
			self.searchtitle = ret[0]
			self.actcinema = ret[1]
		if self.actcinema in (4, 5):
			self.id = self['list'].getCurrent()[3]
			self.title = self['list'].getCurrent()[0]
		callInThread(self.tmdbSearch)

	def tmdbSearch(self):
		self['searchinfo'].setText(_("TMDb: ") + _("Search for %s ...") % self.text)
		self.lang = config.plugins.tmdb.lang.value
		res = []
		self.count = 0
		json_data = {}
		if self.actcinema not in (CURRENT_MOVIES, UPCOMING_MOVIES, POPULAR_MOVIES, SIMILAR_MOVIES, RECOMENDED_MOVIES, BEST_RATED_MOVIES):
			search = tmdb.Search()
			json_data = search.multi(query=self.text, language=self.lang)
		elif self.actcinema == CURRENT_MOVIES:
			json_data = tmdb.Movies().now_playing(page=self.page, language=self.lang)
		elif self.actcinema == UPCOMING_MOVIES:
			json_data = tmdb.Movies().upcoming(page=self.page, language=self.lang)
		elif self.actcinema == POPULAR_MOVIES:
			json_data = tmdb.Movies().popular(page=self.page, language=self.lang)
		elif self.actcinema == SIMILAR_MOVIES:
			json_data = tmdb.Movies(self.id).similar_movies(page=self.page, language=self.lang)
		elif self.actcinema == RECOMENDED_MOVIES:
			json_data = tmdb.Movies(self.id).recommendations(page=self.page, language=self.lang)
		elif self.actcinema == BEST_RATED_MOVIES:
			json_data = tmdb.Movies().top_rated(page=self.page, language=self.lang)
#			print("[TMDb][tmdbSearch] json output\n", json_data)
		if json_data and json_data['results']:
			self.totalpages = json_data['total_pages']
#			print("[TMDb][tmdbSearch] results", json_data)

			for IDs in json_data['results']:
				self.count += 1
				media = fid = title = date = coverPath = backdropPath = ""
				if 'media_type' in IDs:
					media = IDs['media_type']
				if 'id' in IDs:
					fid = str(IDs['id'])
				if 'title' in IDs:
					title = IDs['title']
				if 'name' in IDs:
					title = IDs['name']
				if 'release_date' in IDs:
					date = f", {IDs['release_date'][:4]}"
				if 'first_air_date' in IDs:
					date = f", {IDs['first_air_date'][:4]}"
				if date == ", ":
					date = ""

				mediasubst = _("Movie") if media == "movie" else _("Series")

				title = f"{title} ({mediasubst}{date})"
				if 'poster_path' in IDs:
					coverPath = IDs['poster_path']
				if 'backdrop_path' in IDs:
					backdropPath = IDs['backdrop_path']

				url_cover = f"http://image.tmdb.org/t/p/{config.plugins.tmdb.themoviedb_coversize.value}/{coverPath}"
				url_backdrop = f"http://image.tmdb.org/t/p/{config.plugins.tmdb.themoviedb_coversize.value}/{backdropPath}"

				if fid or title or media:
					res.append(((title, url_cover, media, fid, url_backdrop),))
#			print("[TMDb][tmdbSearch] res", res)
			if res:
				self['list'].setList(res)
				self.piclist = res
				if self.actcinema >= 1:
					self['searchinfo'].setText(f"{_('TMDb: ')}{self.searchtitle} ({_('page ')}{self.page}/{self.totalpages}) {self.title})")
				else:
					self['searchinfo'].setText(_("TMDb: ") + _("Results for %s") % self.text)
				self.getInfo()
				self['list'].pageUp()
		else:
			print("[TMDb] data not found")
			self.showCover(noCover)
			self['searchinfo'].setText(_("TMDb: ") + _("Data not found!"))
			if self.count == 1:
				self['searchinfo'].setText(_("TMDb: ") + _("Results for %s") % self.text)
			if "total_results" not in json_data or json_data['total_results'] == 0:
				self['searchinfo'].setText(_("TMDb: ") + _("No results for %s") % self.text)

	def getInfo(self):
		url_cover = self['list'].getCurrent()[1]
		fid = self['list'].getCurrent()[3]

		if url_cover.endswith("None"):
			self.showCover(noCover)
		else:
			fileName = f"{tempDir}{fid}.jpg"
			if not exists(fileName):
				callInThread(threadDownloadPage, url_cover, fileName, boundFunction(self.getData, fileName, self.dataError))
			else:
				self.showCover(fileName)

	def getData(self, coverSaved, *args, **kwargs):
		self.showCover(coverSaved)

	def dataError(self, error):
		print(f"[TMDb] Error: {error}")

	def showCover(self, coverName):
		if not exists(coverName):
			coverName = noCover

		if exists(coverName):
			self.decodeCover(coverName)
		self.covername = coverName
		# Only one result, launch details
		if config.plugins.tmdb.firsthit.value:
			if self.count == 1:
				self.timer.callback.append(self.ok)
				self.timer.start(100, False)

	def ok(self):
		self.timer.stop()
		check = self['list'].getCurrent()
		if check is not None:
			# title, url_cover, media, id, url_backdrop
			title = self['list'].getCurrent()[0]
			media = self['list'].getCurrent()[2]
			fid = self['list'].getCurrent()[3]
			self.covername = f"{tempDir}{fid}.jpg"
			self.url_backdrop = self['list'].getCurrent()[4]
			self.session.open(tmdbScreenMovie, title, media, self.covername, fid, self.saveFilename, self.url_backdrop)

	def keyLeft(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].pageUp()
			self.getInfo()

	def keyRight(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].pageDown()
			self.getInfo()

	def keyDown(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].down()
			self.getInfo()

	def keyUp(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].up()
			self.getInfo()

	def chDown(self):
		if self.actcinema != DEFAULT:
			self.page += 1
			if self.page > self.totalpages:
				self.page = 1
			callInThread(self.tmdbSearch)

	def chUp(self):
		if self.actcinema != DEFAULT:
			self.page -= 1
			if self.page <= 0:
				self.page = 1
			callInThread(self.tmdbSearch)

	def keyYellow(self):
		return

	def setup(self):
		self.session.open(tmdbConfigScreen)

	def searchString(self):
		self.actcinema = DEFAULT
		self.session.openWithCallback(self.goSearch, VirtualKeyBoard, title=(_("Search for Movie:")), text=self.text)

	def goSearch(self, newTitle):
		if newTitle:
			self.text = newTitle
			print(f"[TMDb] Manual search for: {str(self.text)}")
			callInThread(self.tmdbSearch)

	def cancel(self):
		self.delCover()
		self.close()

	def delCover(self):
		if isdir(tempDir):
			shutil.rmtree(tempDir)


class tmdbScreenMovie(Screen, HelpableScreen, CoverHelper):
	skin = tmdbScreenMovieSkin

	def __init__(self, session, mname, media, coverName, fid, saveFilename, url_backdrop):
		Screen.__init__(self, session)
		self.mname = mname
		self.media = media
		if self.media == "movie":
			self.movie = True
		else:
			self.movie = False
		self.coverName = coverName
		self.url_backdrop = url_backdrop
		self.id = fid
		self.saveFilename = saveFilename

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "TMDbActions",
			{
				"ok": (self.ok, _("Cast")),
				"cancel": (self.cancel, _("Exit")),
				"up": (self.keyLeft, _("Selection up")),
				"down": (self.keyRight, _("Selection down")),
				"left": (self.keyLeft, _("Page up")),
				"right": (self.keyRight, _("Page down")),
				"red": (self.cancel, _("Exit")),
				"green": (self.keyGreen, _("Crew")),
				"yellow": (self.keyYellow, _("Seasons")),
				"blue": (self.menu, _("More")),
				"menu": (self.setup, _("Setup")),
				"eventview": (self.menu, _("More"))
			}, -1)

		self['searchinfo'] = Label(_("TMDb: ") + _("Loading..."))
		self['genre'] = Label("-")
		self['genre_txt'] = Label(_("Genre:"))
		self['description'] = ScrollLabel("")
		self['fulldescription'] = ScrollLabel("")
		self['rating'] = Label("0.0")
		self['votes'] = Label("-")
		self['votes_brackets'] = Label("")
		self['votes_txt'] = Label(_("Votes:"))
		self['runtime'] = Label("-")
		self['runtime_txt'] = Label(_("Runtime:"))
		self['fsk'] = Label("FSK: ?")
		self['subtitle'] = Label("-")
		self['year'] = Label("-")
		self['year_txt'] = Label(_("Year:"))
		self['country'] = Label("-")
		self['country_txt'] = Label(_("Countries:"))
		self['director'] = Label("-")
		self['director_txt'] = Label(_("Director:"))
		self['author'] = Label("-")
		self['author_txt'] = Label(_("Author:"))
		self['studio'] = Label("-")
		self['studio_txt'] = Label(_("Studio:"))
		self['key_red'] = Label(_("Exit"))
		self['key_green'] = Label(_("Cast"))
		self['key_yellow'] = Label(_("Seasons"))
		self['key_blue'] = Label(_("More"))
		self["key_menu"] = StaticText(_("MENU"))  # auto menu button
		CoverHelper.__init__(self, True, True)
		print("[TMDb][tmdbScreenMovie] entered")
		self.onLayoutFinish.append(self.onFinish)

	def onFinish(self):
		if self.movie:
			self['key_yellow'].setText(" ")
		if self.saveFilename == "":
			self['key_blue'].setText(" ")
		# TMDb read
		print(f"[TMDb] Selected: {self.mname}")
		self.showCover(self.coverName)
		self.getBackdrop(self.url_backdrop)
		callInThread(self.tmdbSearch)

	def menu(self):
		if self.saveFilename == "":
			pass
		else:
			options = [
				(_("Save movie description"), 1),
				(_("Delete movie EIT file"), 2),
				(_("Save movie cover"), 3),
				(_("Save movie backdrop"), 4),
				("1+2", 5),
				("1+3", 6),
				("1+2+3", 7),
				("1+2+3+4", 8),
				("3+4", 9)
			]
			self.session.openWithCallback(self.menuCallback, ChoiceBox, list=options)

	def menuCallback(self, ret):
		if ret is None:
			pass
		elif ret[1] == 1:
			self.createTXT()
		elif ret[1] == 2:
			self.deleteEIT()
		elif ret[1] == 3:
			self.saveCover()
		elif ret[1] == 4:
			self.saveBackdrop()
		elif ret[1] == 5:
			self.createTXT()
			self.deleteEIT()
		elif ret[1] == 6:
			self.createTXT()
			self.saveCover()
		elif ret[1] == 7:
			self.createTXT()
			self.deleteEIT()
			self.saveCover()
		elif ret[1] == 8:
			self.createTXT()
			self.deleteEIT()
			self.saveCover()
			self.saveBackdrop()
		elif ret[1] == 9:
			self.saveCover()
			self.saveBackdrop()
		else:
			pass

	def keyLeft(self):
		self['description'].pageUp()
		self['fulldescription'].pageUp()

	def keyRight(self):
		self['description'].pageDown()
		self['fulldescription'].pageDown()

	def tmdbSearch(self):
		self.lang = config.plugins.tmdb.lang.value
		self['searchinfo'].setText(_("TMDb: ") + _("Loading..."))
		print("[TMDb][tmdbScreenMovie]1 ID, self.movie: ", self.id, "   ", self.movie)

		try:
			if self.movie:
				json_data = tmdb.Movies(self.id).info(language=self.lang)
#				print("[TMDb][tmdbScreenMovie] Movie json_data", json_data)
				if json_data and json_data['overview'] == "":
					json_data = tmdb.Movies(self.id).info(language="en")
				json_data_cast = tmdb.Movies(self.id).credits(language=self.lang)
#				print("[TMDb][tmdbScreenMovie] Movie json_data_cast", json_data_cast)
				json_data_fsk = tmdb.Movies(self.id).releases(language=self.lang)
#				print("[TMDb][tmdbScreenMovie] Movie json_fsk", json_data_fsk)
			else:
				json_data = tmdb.TV(self.id).info(language=self.lang)
				if json_data and json_data['overview'] == "":
					json_data = tmdb.TV(self.id).info(language="en")
#				print("[TMDb][tmdbScreenMovie] TV json_data", json_data)
				json_data_cast = tmdb.TV(self.id).credits(language=self.lang)
#				print("[TMDb][tmdbScreenMovie] TV json_data_cast", json_data_cast)
				json_data_fsk = tmdb.TV(self.id).content_ratings(language=self.lang)
#				print("[TMDb][tmdbScreenMovie] TV json_fsk", json_data_fsk)
			self['searchinfo'].setText(f"{self.mname}")
		except Exception as e:
			print("[TMDb][tmdbScreenMovie]1 tmdb read fail", e)
			self['searchinfo'].setText(_("TMDb: ") + _("No results found, or does not respond!"))
			return
		year = vote_average = vote_count = runtime = country_string = genre_string = subtitle = cast_string = ""
		crew_string = director = author = studio_string = ""

		## Year

		if 'release_date' in json_data:
			year = json_data['release_date'][:+4]
			self['year'].setText(f"{str(year)}")

		## Rating
		if 'vote_average' in json_data:
			vote_average = json_data['vote_average']
			self['rating'].setText(f"{vote_average:.1f}")

		## Votes
		if 'vote_count' in json_data:
			vote_count = json_data['vote_count']
			self['votes'].setText(f"{str(vote_count)}")
			self['votes_brackets'].setText(f"({str(vote_count)})")

		## Runtime
		if 'runtime' in json_data:
			runtime = json_data['runtime']
			self['runtime'].setText(f"{str(runtime)} min.")
			runtime = f", {runtime} min."

		## Country
		if 'production_countries' in json_data:
			for country in json_data['production_countries']:
				country_string += f"{country['iso_3166_1']}/"
			country_string = country_string[:-1]
			self['country'].setText(f"{str(country_string)}")

		## Genre"
		if 'genres' in json_data:
			# genre_count = len(json_data['genres'])
			for genre in json_data['genres']:
				genre_string += f"{genre['name']}, "
			self['genre'].setText(f"{str(genre_string[:-2])}")

		## Subtitle
		if 'tagline' in json_data:
			subtitle = json_data['tagline']
			if json_data['tagline'] == "":
				subtitle = ""
			else:
				self['subtitle'].setText(f"{str(subtitle)}")
				subtitle = f"{subtitle}\n"

		## Cast
		if 'cast' in json_data_cast:
			for cast in json_data_cast['cast']:
				castx = cast['name'] if cast['character'] == "" else f"{cast['name']} ({cast['character']})"
				cast_string += f"{castx}\n"

		## Crew

		if 'crew' in json_data_cast:
			for crew in json_data_cast['crew']:
				crew_string += f"{crew['name']} ({crew['job']})\n"

				if crew['job'] == "Director":
					director += f"{crew['name']}, "
				if crew['job'] == "Screenplay" or crew['job'] == "Writer":
					author += f"{crew['name']}, "
			director = director[:-2]
			author = author[:-2]
			self['director'].setText(director)
			self['author'].setText(author)

		## Studio/Production Company
		if 'production_companies' in json_data:
			for studio in json_data['production_companies']:
				studio_string += f"{studio['name']}, "
			studio_string = studio_string[:-2]
			self['studio'].setText(studio_string)

		#
		# modify Data for TV/Series
		#
		season = year = country_string = director = studio_string = runtime = episodes = ""

		if not self.movie:
			## Year
			if 'first_air_date' in json_data:
				year = json_data['first_air_date'][:+4]
				self['year'].setText(f"{str(year)}")

			## Country
			if 'origin_country' in json_data:
				for country in json_data['origin_country']:
					country_string += f"{country}/"
				country_string = country_string[:-1]
				self['country'].setText(country_string)

			## Crew Director
			if 'created_by' in json_data:
				for directors in json_data['created_by']:
					director += f"{directors['name']}, "
				director = director[:-2]
				self['director'].setText(_("Various"))
				self['author'].setText(director)

			## Studio/Production Company
			if 'networks' in json_data:
				for studio in json_data['networks']:
					studio_string += f"{studio['name']}, "
				studio_string = studio_string[:-2]
				self['studio'].setText(studio_string)

			## Runtime
			seasons = json_data.get("number_of_seasons", "")
			episodes = json_data.get("number_of_episodes", "")
			runtime = f"{seasons} {_('Seasons')} / {episodes} {_('Episodes')}"
			self['runtime'].setText(f"{runtime}")
			runtime = f", {runtime}"

			# Series Description
			if 'seasons' in json_data:
				for seasons in json_data['seasons']:
					if seasons['season_number'] >= 1:
						season += f"{_('Season')} {seasons['season_number']} / {seasons['episode_count']} ({seasons['air_date'][:4]})\n"

		## Description
		description = ""
		if 'overview' in json_data:
			description = json_data['overview']
			description = f"{description}\n\n{cast_string}\n{crew_string}"
			self['description'].setText(description)

			movieinfo = f"{str(genre_string)}{str(country_string)} {str(year)} {str(runtime)}"
			fulldescription = f"{subtitle}{movieinfo}\n\n{description}\n{season}"
			self['fulldescription'].setText(fulldescription)
			self.text = fulldescription

		## FSK
		fsk = "100"
		if self.movie:
			if 'countries' in json_data_fsk:
				for country in json_data_fsk['countries']:
					if str(country['iso_3166_1']) == "DE":
						fsk = str(country['certification'])
		else:
			if 'results' in json_data_fsk:
				for country in json_data_fsk['results']:
					if str(country['iso_3166_1']) == "DE":
						fsk = str(country['rating'])

		self.showFSK(fsk)

	def dataError(self, error):
		print(f"[TMDb] Error: {error}")

	def showCover(self, coverName):
		if not exists(coverName):
			coverName = noCover

		if exists(coverName):
			self.decodeCover(coverName)

	def getBackdrop(self, url_backdrop):
		backdropSaved = f"{tempDir}backdrop.jpg"
		if exists(backdropSaved):
			remove(backdropSaved)
		if url_backdrop.endswith("None"):
			print("[TMDb] No backdrop found")
		else:
			callInThread(threadDownloadPage, url_backdrop, f"{tempDir}backdrop.jpg", boundFunction(self.gotBackdrop, f"{tempDir}backdrop.jpg"), self.dataError)

	def gotBackdrop(self, backdrop, *args, **kwargs):
		#print("Backdrop download returned", backdrop)
		backdropSaved = f"{tempDir}backdrop.jpg"
		if not exists(backdropSaved):
			pass

		if exists(f"{tempDir}backdrop.jpg"):
			self.decodeBackdrop(f"{tempDir}backdrop.jpg")

	def showFSK(self, fsk):
		self.fsklogo = f"/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/fsk_{fsk}.png"
		self.decodeFsk(self.fsklogo)

	def ok(self):
		self.keyGreen()

	def setup(self):
		self.session.open(tmdbConfigScreen)

	def keyYellow(self):
		if not self.movie:
			self.session.open(tmdbScreenSeason, self.mname, self.id, self.media)

	def keyGreen(self):
		self.session.open(tmdbScreenPeople, self.mname, self.id, self.media)

	def cancel(self):
		self.close(True)

	def saveCover(self):
		saveFile = cleanEnd(self.saveFilename)
		if exists(self.saveFilename):
			try:
				if config.plugins.tmdb.coverQuality.value != "original":
					width, height = config.plugins.tmdb.coverQuality.value.split("x", 1)
					img = Image.open(self.coverName)
					img = img.convert('RGBA', colors=256)
					img = img.resize((int(width), int(height)), Image.LANCZOS)
					img.save(self.coverName)  # img.save(f, quality=75)

				shutil.copy(self.coverName, f"{saveFile}.jpg")
				self.session.open(MessageBox, _("Cover saved!"), type=1, timeout=3)
				print(f"[TMDb] Cover {saveFile}.jpg created")
			except Exception:
				print("[TMDb] Error saving cover!")

	def saveBackdrop(self):
		saveFile = cleanEnd(self.saveFilename)
		if exists(self.saveFilename):
			try:
				backdropName = f"{tempDir}backdrop.jpg"
				if config.plugins.tmdb.backdropQuality.value != "original":
					width, height = config.plugins.tmdb.backdropQuality.value.split("x", 1)
					img = Image.open(backdropName)
					img = img.convert('RGBA', colors=256)
					img = img.resize((int(width), int(height)), Image.LANCZOS)
					img.save(backdropName)  # img.save(f, quality=75)

				shutil.copy(backdropName, f"{saveFile}.bdp.jpg")
				self.session.open(MessageBox, _("Backdrop saved!"), type=1, timeout=3)
				print(f"[TMDb] Backdrop {saveFile}.bdp.jpg created")
			except Exception:
				print("[TMDb] Error saving backdrop!")

	def createTXT(self):
		saveFile = cleanEnd(self.saveFilename)
		if exists(self.saveFilename):
			try:
				with open(f"{saveFile}.txt", "w") as fd:
					fd.write(self.text)
				print(f"[TMDb] {saveFile}.txt created")
				self.session.open(MessageBox, _("Movie description saved!"), type=1, timeout=3)
			except OSError:
				print("[TMDb] Error saving TXT file!")

	def deleteEIT(self):
		eitFile = f"{cleanEnd(self.saveFilename)}.eit"
		try:
			remove(eitFile)
			print(f"[TMDb] {eitFile} deleted")
			self.session.open(MessageBox, _("EIT file deleted!"), type=1, timeout=3)
		except OSError:
			print("[TMDb] Error deleting EIT file!")


class tmdbScreenPeople(Screen, HelpableScreen, CoverHelper):
	skin = tmdbScreenPeopleSkin

	def __init__(self, session, mname, fid, media):
		Screen.__init__(self, session)
		self.mname = mname
		self.id = fid
		self.media = media
		if self.media == "movie":
			self.movie = True
		else:
			self.movie = False
		self.covername = noCover

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "TMDbActions",
			{
				"ok": (self.ok, _("Show details")),
				"cancel": (self.cancel, _("Exit")),
				"down": (self.keyDown, _("Selection down")),
				"up": (self.keyUp, _("Selection up")),
				"nextBouquet": (self.chDown, _("Details down")),
				"prevBouquet": (self.chUp, _("Details up")),
				"right": (self.keyRight, _("Page down")),
				"left": (self.keyLeft, _("Page down")),
				"red": (self.cancel, _("Exit")),
				"green": (self.ok, _("Show details")),
				"blue": (self.keyBlue),
				"menu": (self.keyBlue, _("Setup"))
			}, -1)

		self['searchinfo'] = Label(_("TMDb: ") + _("Loading..."))
		self['data'] = ScrollLabel("")
		self['key_red'] = Label(_("Exit"))
		self['key_green'] = Label(_("Details"))
		self['key_blue'] = Label()
		self["key_menu"] = StaticText(_("MENU"))  # auto menu button
		self['list'] = createList()
		CoverHelper.__init__(self, True)

		self.onLayoutFinish.append(self.onFinish)

	def onFinish(self):
		# TMDb read
		print(f"[TMDb] Selected: {self.mname}")
		self['searchinfo'].setText(f"{self.mname}")
		self.showBackdrop()
		callInThread(self.tmdbSearch)

	def tmdbSearch(self):
		json_data_cast = []
		json_data_seasons = []
		json_data_season = []
		self.lang = config.plugins.tmdb.lang.value
		self['searchinfo'].setText(_("TMDb: ") + _("Loading..."))
		res = []
		try:
			if self.movie:
				json_data_cast = tmdb.Movies(self.id).credits(language=self.lang)
				#print(json_data_cast)
			else:
				json_data_cast = tmdb.TV(self.id).credits(language=self.lang)
		except Exception as e:
			print("[TMDb][tmdbScreenMovie]2 tmdb read fail", e)
			self['searchinfo'].setText(_("TMDb: ") + _("No results found, or does not respond!"))
			return
		if "cast" in json_data_cast and json_data_cast["cast"] is not None:
#			print("json_data_cast", json_data_cast)
			for casts in json_data_cast['cast']:
				title = date = ""
#				print("json_data_cast - casts", casts)
				fid = str(casts['id'])
				title = casts['name'] if casts['character'] == "" else f"{casts['name']} ({casts['character']})"
				coverPath = casts['profile_path']
				#cover = f"{tempDir}{fid}.jpg"
				url_cover = f"http://image.tmdb.org/t/p/{config.plugins.tmdb.themoviedb_coversize.value}/{coverPath}"

				if fid != "" or title != "":
					res.append(((title, url_cover, "", fid, None),))

			if not self.movie:
				try:
					json_data_seasons = tmdb.TV(self.id).info(language=self.lang)
				except Exception as e:
					print("[TMDb][tmdbScreenMovie]3 tmdb json_data_seasons = tmdb.TV(self.id).info", e)
					self['searchinfo'].setText(_("TMDb: ") + _("No results found, or does not respond!"))
					return
				if json_data_seasons:
					seasoncnt = 1
					for season in json_data_seasons['seasons']:
						date = " "
						#print"######", season
						seasoncnt = season['season_number']
						#print"#########", str(season['season_number'])
						#fid = str(season['id'])
						title = season['name']
						if season['air_date'] is not None:
							date = f"({season['air_date'][:4]})"
						res.append(((f"{title} {date}", "None", "", None, None),))
						json_data_season = tmdb.TV_Seasons(self.id, seasoncnt).credits(language=self.lang)
						if json_data_season:
							for casts in json_data_season['cast']:
								fid = str(casts['id'])
								title = casts['name'] if casts['character'] == "" else f"{casts['name']} ({casts['character']})"
								coverPath = str(casts['profile_path'])
								#cover = f"{tempDir}{fid}.jpg"
								url_cover = f"http://image.tmdb.org/t/p/{config.plugins.tmdb.themoviedb_coversize.value}/{coverPath}"

								if fid != "" or title != "":
									res.append(((f"    {title}", url_cover, "", fid, None),))
			if res:
				self['list'].setList(res)
				self.piclist = res
				self.getInfo()
				self['searchinfo'].setText(f"{self.mname}")
			else:
				self['searchinfo'].setText(_("TMDb: ") + _("No results found"))
		else:
			self['searchinfo'].setText(_("TMDb: ") + _("No results found, or does not respond!"))

	def getInfo(self):
		self['data'].setText("")
		url_cover = self['list'].getCurrent()[1]
		fid = self['list'].getCurrent()[3]

		if url_cover.endswith("None"):
			self.showCover(noCover)
		else:
			fileName = f"{tempDir}{fid}.jpg"
			if not exists(fileName):
				callInThread(threadDownloadPage, url_cover, fileName, boundFunction(self.getData, fileName), self.dataError)
			else:
				self.showCover(fileName)

	def getData(self, coverSaved, *args, **kwargs):
		self.showCover(coverSaved)

	def dataError(self, error):
		print(f"[TMDb] Error: {error}")

	def showCover(self, coverName):
		if not exists(coverName):
			coverName = noCover

		if exists(coverName):
			self.decodeCover(coverName)
		self.covername = coverName

	def showBackdrop(self):
		backdropSaved = f"{tempDir}backdrop.jpg"
		if exists(backdropSaved):
			self.decodeBackdrop(backdropSaved)

	def ok(self):
		check = self['list'].getCurrent()
		if check is not None and check[3] is not None:
			fid = self['list'].getCurrent()[3]
			self.session.open(tmdbScreenPerson, self.covername, fid)
		else:
			self['searchinfo'].setText(_("TMDb: ") + _("No cast details found"))

	def keyLeft(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].pageUp()
			self.getInfo()

	def keyRight(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].pageDown()
			self.getInfo()

	def keyDown(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].down()
			self.getInfo()

	def keyUp(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].up()
			self.getInfo()

	def chDown(self):
		self['data'].pageUp()

	def chUp(self):
		self['data'].pageDown()

	def keyBlue(self):
		self.session.open(tmdbConfigScreen)

	def cancel(self):
		self.close()


class tmdbScreenPerson(Screen, HelpableScreen, CoverHelper):
	skin = tmdbScreenPersonSkin

	def __init__(self, session, coverName, fid):
		Screen.__init__(self, session)
		self.coverName = coverName
		self.id = fid

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "TMDbActions",
			{
				"cancel": (self.cancel, _("Exit")),
				"up": (self.keyLeft, _("Selection up")),
				"down": (self.keyRight, _("Selection down")),
				"left": (self.keyLeft, _("Page up")),
				"right": (self.keyRight, _("Page down")),
				"red": (self.cancel, _("Exit")),
			}, -1)

		self['searchinfo'] = Label(_("TMDb: ") + _("Loading..."))
		self['fulldescription'] = ScrollLabel("")
		self['key_red'] = Label(_("Exit"))
		CoverHelper.__init__(self, True)

		self.onLayoutFinish.append(self.onFinish)

	def onFinish(self):
		self.showBackdrop()
		self.showCover(self.coverName)
		callInThread(self.tmdbSearch)

	def keyLeft(self):
		self['fulldescription'].pageUp()

	def keyRight(self):
		self['fulldescription'].pageDown()

	def tmdbSearch(self):
		self.lang = config.plugins.tmdb.lang.value
		print(f"[TMDb] ID: {self.id}")
		self['searchinfo'].setText(_("TMDb: ") + _("Loading..."))
		try:		# may be invalid id
			json_data_person = tmdb.People(self.id).info(language=self.lang)
		except Exception as e:
			print(f"[TMDb] 4 tmdb.People(self.id).inf {e}")
			self['searchinfo'].setText(_("TMDb: ") + _("No results found, or does not respond!"))
			return
		if json_data_person:
#			print("[TMDb]", json_data_person)
			self.mname = json_data_person['name']

			## Personal data
			birthday = birthplace = gender = altname = rank = biography = ""
			if "birthday" in json_data_person and json_data_person['birthday'] is not None:
				birthday = json_data_person['birthday']

			if "place_of_birth" in json_data_person and json_data_person['place_of_birth'] is not None:
				birthplace = json_data_person['place_of_birth']
			if "gender" in json_data_person:
				gender = json_data_person['gender']
				if gender == "1":
					gender = _("female")
				elif gender == "2":
					gender = _("male")
				else:
					gender = ""
#			print("[TMDb]", json_data_person["also_known_as"])
			if "also_known_as" in json_data_person and json_data_person["also_known_as"] != []:
				altname = f"\n{_("Known as: ")}{json_data_person['also_known_as'][0]}"
				if len(json_data_person['also_known_as']) > 1:
					altname = f"{altname}, {json_data_person['also_known_as'][1]}"

			if "popularity'" in json_data_person:
				rank = f"\n{_("Popularity")}: {json_data_person['popularity']}"

			if "biography" in json_data_person:
				biography = json_data_person['biography']
			if biography == "":
					json_data_person = tmdb.People(self.id).info(language='en')
			if "biography" in json_data_person:
					biography = json_data_person['biography']
			birthday = birthday if birthday == "" else _(f"Birthdate:{birthday}, ")
			birthplace = birthplace if birthplace == "" else _(f"Birthplace:{birthplace}")
			gender = gender if gender == "" else _(f", Gender:{gender}")
			print(f"[TMDb] cast person details 1 {birthday}  {birthplace}  {gender}")
			data = f"{birthday}{birthplace}{gender}{altname}{rank}\n\n{biography}\n\n"
			## Participated data
			json_data_person = tmdb.People(self.id).movie_credits(language=self.lang)
			json_data_person_tv = tmdb.People(self.id).tv_credits(language=self.lang)
			data_movies = []
			# Participated in movies
#			print("[tmdbScreenPerson][tmdbsearch]json_data_person, json_data_person_tv]", json_data_person, "   ", json_data_person_tv)
			release_date = title = character = first_air_date = name = ""
			if "cast" in json_data_person:
				for cast in json_data_person['cast']:
					if "release_date" in cast:
						release_date = cast['release_date']
					if "title" in cast:
						title = cast['title']
					if "character" in cast:
						character = cast['character']
					datacm = f"{release_date} {title}  ({character})" if character != "" else f"{release_date} {title}"
					data_movies.append(datacm)
#				print("[tmdbScreenPerson][tmdbsearch]data_movies]", data_movies)
			# Participated in TV
			if "cast" in json_data_person_tv:
				for cast in json_data_person_tv['cast']:
					if "first_air_date" in cast:
						first_air_date = cast['first_air_date']
					if "name" in cast:
						name = cast['name']
					if "character" in cast:
						character = cast['character']
					datactv = f"{first_air_date} [name]  ({character}) - TV" if character else f"{first_air_date} {name} - TV"
					data_movies.append(datactv)
#				print("[tmdbScreenPerson][tmdbsearch]data_movies+TV]", data_movies)

			data_movies.sort(reverse=True)
			cast_movies = ""
			for cast in data_movies:
				cast_movies += f"{cast}\n"

			data = f"{data}\n{_("Known for:")}\n{cast_movies}"
			self['fulldescription'].setText(data)
			self['searchinfo'].setText(f"{self.mname}")
		else:
			self['searchinfo'].setText(_("TMDb: ") + _("No results found, or does not respond!"))

	def showCover(self, coverName):
		self.decodeCover(coverName)

	def showBackdrop(self):
		backdropSaved = f"{tempDir}backdrop.jpg"
		if exists(backdropSaved):
			self.decodeBackdrop(backdropSaved)

	def ok(self):
		self.cancel()

	def cancel(self):
		self.close(True)


class tmdbScreenSeason(Screen, HelpableScreen, CoverHelper):
	skin = tmdbScreenSeasonSkin

	def __init__(self, session, mname, fid, media):
		Screen.__init__(self, session)
		self.mname = mname
		self.id = fid
		self.media = media
		self.movie = self.media == "movie"
		self.piclist = ""

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "TMDbActions",
			{
				"ok": (self.ok, _("Show details")),
				"cancel": (self.cancel, _("Exit")),
				"up": (self.keyUp, _("Selection up")),
				"down": (self.keyDown, _("Selection down")),
				"nextBouquet": (self.chDown, _("Details down")),
				"prevBouquet": (self.chUp, _("Details up")),
				"right": (self.keyRight, _("Page down")),
				"left": (self.keyLeft, _("Page down")),
				"red": (self.cancel, _("Exit")),
				"green": (self.ok, _(" ")),
				"blue": (self.keyBlue),
				"menu": (self.keyBlue, _("Setup"))
			}, -1)

		self['searchinfo'] = Label(_("TMDb: ") + _("Loading..."))
		self['data'] = ScrollLabel("")
		self['key_red'] = Label(_("Exit"))
		self['key_green'] = Label()
		self['key_blue'] = Label()
		self['list'] = createList()

		CoverHelper.__init__(self, True)

		self.onLayoutFinish.append(self.onFinish)

	def onFinish(self):
		# TMDb read
		print(f"[TMDb] Selected: {self.mname}")
		self['searchinfo'].setText(f"{self.mname}")
		self.showBackdrop()
		callInThread(self.tmdbSearch)

	def tmdbSearch(self):
		self.lang = config.plugins.tmdb.lang.value
		self['searchinfo'].setText(_("TMDb: ") + _("Loading..."))
		res = []
		# Seasons
		try:
			json_data_seasons = tmdb.TV(self.id).info(language=self.lang)
		except Exception as e:
			print("[TMDb] 5 Selectedtmdb.TV(self.id).info", e)
			self['searchinfo'].setText(_("TMDb: ") + _("No results found, or does not respond!"))
			return
		if json_data_seasons:
			for seasons in json_data_seasons['seasons']:
				print(f"[TMDb] Season: {seasons['season_number']}")
				fid = str(seasons['id'])
				season = seasons['season_number']

				#Episodes
				json_data_episodes = tmdb.TV_Seasons(self.id, season).info(language=self.lang)
				titledate = f"({json_data_episodes['air_date'][:4]})"
				title = str(json_data_episodes['name'])
				title = f"{title} {titledate}"
				overview = str(json_data_episodes['overview'])
				coverPath = str(json_data_episodes['poster_path'])
				#cover = f"{tempDir}{fid}.jpg"
				url_cover = f"http://image.tmdb.org/t/p/{config.plugins.tmdb.themoviedb_coversize.value}/{coverPath}"
				if fid != "" or title != "":
					res.append(((title, url_cover, overview, fid, None),))

				for names in json_data_episodes['episodes']:
					fid = str(names['id'])
					title = str(names['episode_number'])
					name = str(names['name'])
					title = "%+6s %s" % (title, name)
					overview = str(names['overview'])
					coverPath = str(names['still_path'])
					#cover = f"{tempDir}{fid}.jpg"
					url_cover = f"http://image.tmdb.org/t/p/{config.plugins.tmdb.themoviedb_coversize.value}/{coverPath}"
					if fid != "" or title != "":
						res.append(((title, url_cover, overview, fid, None),))
			self['list'].setList(res)
			self.piclist = res
			self.getInfo()
			self['searchinfo'].setText(f"{self.mname}")
		else:
			self['searchinfo'].setText(_("TMDb: ") + _("No results found, or does not respond!"))

	def getInfo(self):
		self['data'].setText("")
		try:
			url_cover = self['list'].getCurrent()[1]
		except Exception:
			self.showCover(noCover)
			return
		fid = self['list'].getCurrent()[3]
		if url_cover.endswith("None"):
			self.showCover(noCover)
		else:
			fileName = f"{tempDir}{fid}.jpg"
			if not exists(fileName):
				callInThread(threadDownloadPage, url_cover, fileName, boundFunction(self.getData, fileName), self.dataError)
			else:
				self.showCover(fileName)

	def getData(self, coverSaved, *args, **kwargs):
		self.showCover(coverSaved)

	def dataError(self, error):
		print(f"[TMDb] Error: {error}")

	def showCover(self, coverName):
		if not exists(coverName):
			coverName = noCover
		if exists(coverName):
			self.decodeCover(coverName)
		self.ok()  # Shortcut

	def showBackdrop(self):
		backdropSaved = f"{tempDir}backdrop.jpg"
		if exists(backdropSaved):
			self.decodeBackdrop(backdropSaved)

	def ok(self):
		check = self['list'].getCurrent()
		if check is not None:
			data = self['list'].getCurrent()[2]
			self['data'].setText(data)

	def keyLeft(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].pageUp()
			self.getInfo()

	def keyRight(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].pageDown()
			self.getInfo()

	def keyDown(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].down()
			self.getInfo()

	def keyUp(self):
		check = self['list'].getCurrent()
		if check is not None:
			self['list'].up()
			self.getInfo()

	def chDown(self):
		self['data'].pageUp()

	def chUp(self):
		self['data'].pageDown()

	def keyBlue(self):
		self.session.open(tmdbConfigScreen)

	def cancel(self):
		self.close()

# -*- coding: utf-8 -*-
#
#   Copyright (C) 2021 Team OpenSPA
#   https://openspa.info/
#
#   Copyright (c) 2021-2024 Billy2011 @ vuplus-support.org
#   20210618 (1st release)
#   - adaptions for VTI
#   - many fixes, improvements, mods & rewrites
#   - py3 adaption
#   20240831 (latest release)
#
#   Copyright (c) 2025 jbleyel
#   20250731 (release)
#   - remove python2 code
#   - remove twisted downloadPage
#
#   SPDX-License-Identifier: GPL-2.0-or-later
#   See LICENSES/README.md for more information.
#
#   PlutoTV is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PlutoTV is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with PlutoTV.  If not, see <http://www.gnu.org/licenses/>.
#

import os
from pickle import load, dump
from time import gmtime, localtime, strftime, time
from urllib.parse import urljoin, urlparse

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaBlend, MultiContentEntryText
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText
from Components.config import ConfigElement, ConfigSelection, ConfigYesNo, config, getConfigListEntry
from Plugins.Extensions.PlutoTV import downloader
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools import Notifications
from enigma import eListboxPythonMultiContent, ePicLoad, eServiceReference, eTimer, gFont, getDesktop, iPlayableService

from . import PlutoDownload, _, bigStorage, update_qsd

try:
	from Plugins.Extensions.tmdb import tmdb

	is_tmdb = True
except Exception:
	is_tmdb = False

try:
	from Plugins.Extensions.IMDb.plugin import main as imdb

	is_imdb = True
except Exception:
	is_imdb = False

screenWidth = getDesktop(0).size().width()

config.plugins.plutotv.silentmode = ConfigYesNo(default=True)


def fhd(num, factor=1.5):
	if screenWidth and screenWidth == 1920:
		prod = num * factor
	else:
		prod = num
	return int(round(prod))


def fontHD(nombre):
	if screenWidth and screenWidth == 1920:
		fuente = nombre
	else:
		fuente = nombre
	return fuente


def setResumePoint(session, sid=None):
	global resumePointCache
	service = session.nav.getCurrentService()
	ref = session.nav.getCurrentlyPlayingServiceReference()
	if (service is not None) and (ref is not None):
		seek = service.seek()
		if seek:
			pos = seek.getPlayPosition()
			if not pos[0]:
				key = sid
				lru = int(time())
				_l = seek.getLength()
				if _l:
					_l = _l[1]
				else:
					_l = None
				position = pos[1]
				resumePointCache[key] = [lru, position, _l]
				saveResumePoints(sid)


def getResumePoint(sid):
	global resumePointCache
	resumePointCache = loadResumePoints(sid)
	if sid is not None:
		try:
			entry = resumePointCache[sid]
			entry[0] = int(time())  # update LRU timestamp
			last = entry[1]
			length = entry[2]
		except KeyError:
			last = None
			length = 0
	return last, length


def saveResumePoints(sid):
	global resumePointCache
	name = os.path.join(FOLDER, sid) + ".cue"

	try:
		f = open(name, "wb")
		dump(resumePointCache, f, protocol=5)
	except Exception as err:
		print("[PlutoTV] Failed to write resumepoints: {}".format(err))


def loadResumePoints(sid):
	name = os.path.join(FOLDER, sid) + ".cue"

	try:
		return load(open(name, "rb"))
	except Exception as err:
		print("[PlutoTV] Failed to load resumepoints: {}".format(err))
		return {}


resumePointCache = {}

FOLDER = os.path.join(bigStorage(500 * 10 ** 6, "/tmp", "/media/hdd", "/media/usb", "/media/cf", "/media/mmc"), "PlutoTV")
if not os.path.exists(FOLDER):
	os.makedirs(FOLDER)

DownloadPosters = downloader.PlutoDownloader


class SelList(MenuList):
	def __init__(self, _list, enableWrapAround=False):
		MenuList.__init__(self, _list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setItemHeight(fhd(35))
		self.l.setFont(0, gFont(fontHD("Regular"), fhd(19)))


def listentry(name, data, _id, epid=0, region=None):
	res = [(name, data, _id, epid, region)]

	if data in ("menu", "favorites"):
		picture = "/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/menu.png"
	elif data in ("series", "seasons"):
		picture = "/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/series.png"
	elif data in ("movie", "episode"):
		picture = "/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/cine.png"
		if data == "episode":
			sid = epid
		else:
			sid = _id
		if sid:
			last, length = getResumePoint(sid)
			if last and (last > 900000) and (not length or (last < length - 900000)):
				picture = "/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/cine_half.png"
			elif last and last >= length - 900000:
				picture = "/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/cine_end.png"
	else:
		picture = None

	picload = ePicLoad()
	picload.setPara((fhd(20), fhd(20), 1, 1, False, 1, "#FF000000"))

	res.append(MultiContentEntryText(pos=(fhd(45), fhd(7)), size=(fhd(533), fhd(35)), font=0, text=name))
	if picture is not None:
		if os.path.isfile(picture):
			picload.startDecode(picture, 0, 0, False)
			png = picload.getData()
			res.append(MultiContentEntryPixmapAlphaBlend(pos=(fhd(7), fhd(9)), size=(fhd(20), fhd(20)), png=png))

	return res


class PlutoTV(Screen):
	if screenWidth and screenWidth == 1920:
		skin = """
		<screen name="PlutoTV" zPosition="2" position="0,0" size="1920,1080" flags="wfNoBorder" title="Pluto TV" transparent="0">
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/plutotv-fhd.png" position="0,0" size="1920,1080" zPosition="-2" alphatest="blend" />
		<widget name="logo" position="70,30" size="300,90" zPosition="0" alphatest="blend" transparent="1" />
		<widget source="global.CurrentTime" render="Label" position="1555,30" size="300,55" font="Regular; 44" halign="right" zPosition="5" backgroundColor="black" transparent="1">
		<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<widget source="global.CurrentTime" render="Label" position="1555,80" size="300,45" font="Regular; 27" halign="right" zPosition="5" backgroundColor="black" transparent="1">
		<convert type="ClockToText">Format:%A, %d. %b.</convert>
		</widget>
		<widget name="loading" position="560,440" size="800,200" font="Regular; 40" backgroundColor="black" transparent="0" zPosition="10" halign="center" valign="center" />
		<widget name="playlist" position="400,48" size="1150,55" font="Regular; 40" backgroundColor="black" transparent="1" foregroundColor="#ab2a3e" zPosition="2" halign="center" />
		<widget name="feedlist" position="70,140" size="615,743" scrollbarMode="showOnDemand" enableWrapAround="0" transparent="0" zPosition="5" foregroundColor="white" backgroundColorSelected="#00ff0063" backgroundColor="black" />
		<widget name="poster" position="772,210" size="483,675" alphatest="blend" />
		<widget source="description" position="1282,240" size="517,347" render="VRunningText" options="movetype=swimming,startpoint=0,direction=top,steptime=93,repeat=5,always=0,startdelay=8000,wrap" font="Regular; 29" backgroundColor="black" foregroundColor="white" transparent="0" valign="top" />
		<widget name="vtitle" position="775,140" size="1027,48" font="Regular; 38" backgroundColor="black" foregroundColor="#ffff00" transparent="1" />
		<widget name="vinfo" position="1282,205" size="517,48" font="Regular; 26" backgroundColor="black" foregroundColor="#9b9b9b" transparent="1" />
		<widget name="eptitle" position="1282,597" size="517,33" font="Regular; 29" backgroundColor="black" foregroundColor="#ffff00" transparent="1" />
		<widget source="epinfo" position="1284,637" size="517,246" render="VRunningText" options="movetype=swimming,startpoint=0,direction=top,steptime=93,repeat=5,always=0,startdelay=8000,wrap" font="Regular; 29" backgroundColor="black" foregroundColor="white" transparent="1" />
		<widget name="help" position="70,910" size="615,48" font="Regular; 23" backgroundColor="black" foregroundColor="#9b9b9b" transparent="0" halign="center" />
		<eLabel position="38,1050" size="420,8" backgroundColor="#ff0000" valign="center" />
		<eLabel position="473,1050" size="420,8" backgroundColor="#32cd32" />
		<eLabel position="908,1050" size="420,8" backgroundColor="#ffff00" />
		<eLabel position="1343,1050" size="420,8" backgroundColor="#ff" valign="center" />
		<widget name="red" position="38,1005" size="420,37" valign="center" halign="center" font="Regular; 30" backgroundColor="#20000000" foregroundColor="white" transparent="1" />
		<widget name="green" position="473,968" size="420,75" valign="center" halign="center" font="Regular; 30" backgroundColor="#20000000" foregroundColor="white" transparent="1" />
		<widget name="yellow" position="908,1005" size="420,37" valign="center" halign="center" font="Regular; 30" backgroundColor="#20000000" foregroundColor="white" transparent="1" />
		<widget name="blue" position="1343,1005" size="420,37" valign="center" halign="center" font="Regular; 30" backgroundColor="#20000000" foregroundColor="white" transparent="1" />
		<eLabel name="button ok" position="1800,968" size="60,27" backgroundColor="black" text="OK" font="Regular; 19" foregroundColor="white" halign="center" valign="center" shadowColor="#00000000" shadowOffset="-3,-3" zPosition="3" />
		<eLabel name="button ok bg" position="1798,968" size="63,30" backgroundColor="#616161" zPosition="2" />
		<eLabel name="button exit" position="1800,1013" size="60,27" backgroundColor="black" text="EXIT " font="Regular; 19" foregroundColor="white" halign="center" valign="center" shadowColor="#00000000" shadowOffset="-3,-3" zPosition="3" noWrap="1" />
		<eLabel name="button exit bg" position="1798,1013" size="63,30" backgroundColor="#616161" zPosition="2" font="Regular; 16" foregroundColor="#20000000" />
		</screen>"""
	else:
		skin = """
		<screen name="PlutoTV" zPosition="2" position="0,0" size="1280,720" flags="wfNoBorder" title="Pluto TV" transparent="0">
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/plutotv-hd.png" position="0,0" size="1280,720" zPosition="-2" alphatest="blend" />
		<widget name="logo" position="47,20" size="200,60" zPosition="0" alphatest="blend" transparent="1" />
		<widget source="global.CurrentTime" render="Label" position="1037,20" size="200,36" font="Regular; 29" halign="right" zPosition="5" backgroundColor="black" transparent="1">
		<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<widget source="global.CurrentTime" render="Label" position="1037,50" size="200,24" font="Regular; 18" halign="right" zPosition="5" backgroundColor="black" transparent="1">
		<convert type="ClockToText">Format:%A, %d. %b.</convert>
		</widget>
		<widget name="loading" position="373,293" size="533,123" font="Regular; 40" backgroundColor="black" transparent="0" zPosition="10" halign="center" valign="center" />
		<widget name="playlist" position="267,32" size="767,37" font="Regular; 28" backgroundColor="black" transparent="1" foregroundColor="#ab2a3e" zPosition="2" halign="center" />
		<widget name="feedlist" position="47,93" size="410,495" scrollbarMode="showOnDemand" enableWrapAround="0" transparent="1" zPosition="5" foregroundColor="white" backgroundColorSelected="#00ff0063" backgroundColor="black" />
		<widget name="poster" position="515,137" size="322,450" alphatest="blend" />
		<widget source="description" position="855,160" size="345,231" render="VRunningText" options="movetype=swimming,startpoint=0,direction=top,steptime=140,repeat=5,always=0,startdelay=8000,wrap" font="Regular; 19" backgroundColor="black" foregroundColor="white" transparent="0" valign="top" />
		<widget name="vtitle" position="517,100" size="685,32" font="Regular; 25" backgroundColor="black" foregroundColor="#ffff00" transparent="1" />
		<widget name="vinfo" position="855,137" size="345,32" font="Regular; 17" backgroundColor="black" foregroundColor="#9b9b9b" transparent="1" />
		<widget name="eptitle" position="855,398" size="345,22" font="Regular; 19" backgroundColor="black" foregroundColor="#ffff00" transparent="1" />
		<widget source="epinfo" position="855,426" size="345,164" render="VRunningText" options="movetype=swimming,startpoint=0,direction=top,steptime=140,repeat=5,always=0,startdelay=8000,wrap" font="Regular; 19" backgroundColor="black" foregroundColor="white" transparent="1" />
		<widget name="help" position="47,598" size="410,32" font="Regular; 16" backgroundColor="black" foregroundColor="#9b9b9b" transparent="0" halign="center" />
		<eLabel position="25,700" size="280,5" backgroundColor="#ff0000" valign="center" />
		<eLabel position="315,700" size="280,5" backgroundColor="#32cd32" />
		<eLabel position="605,700" size="280,5" backgroundColor="#ffff00" />
		<eLabel position="895,700" size="280,5" backgroundColor="#ff" valign="center" />
		<widget name="red" position="25,670" size="280,25" valign="center" halign="center" font="Regular; 20" backgroundColor="#20000000" foregroundColor="white" transparent="1" />
		<widget name="green" position="315,645" size="280,50" valign="center" halign="center" font="Regular; 20" backgroundColor="#20000000" foregroundColor="white" transparent="1" />
		<widget name="yellow" position="605,670" size="280,25" valign="center" halign="center" font="Regular; 20" backgroundColor="#20000000" foregroundColor="white" transparent="1" />
		<widget name="blue" position="895,670" size="280,25" valign="center" halign="center" font="Regular; 20" backgroundColor="#20000000" foregroundColor="white" transparent="1" />
		<eLabel name="button ok" position="1200,645" size="40,18" backgroundColor="black" text="OK" font="Regular; 13" foregroundColor="white" halign="center" valign="center" shadowColor="#00000000" shadowOffset="-3,-3" zPosition="3" />
		<eLabel name="button ok bg" position="1199,645" size="42,20" backgroundColor="#616161" zPosition="2" />
		<eLabel name="button exit" position="1200,675" size="40,18" backgroundColor="black" text="EXIT " font="Regular; 13" foregroundColor="white" halign="center" valign="center" shadowColor="#00000000" shadowOffset="-3,-3" zPosition="3" noWrap="1" />
		<eLabel name="button exit bg" position="1199,675" size="42,20" backgroundColor="#616161" zPosition="2" />
		</screen>"""
	FAVO_NAME = _("** My Favorites **")
	EMPTY_FAVO = ("0", _("No favorites available"), "", "", "", 0, "", "", "empty", "", 0, None)
	FAVO_PATH = "/etc/enigma2/plutotv-favorites"

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "PlutoTV"

		self["feedlist"] = SelList([])
		self["playlist"] = Label(_("VOD Menu"))
		self["loading"] = Label(_("Loading data... Please wait"))
		self["description"] = StaticText()
		self["vtitle"] = Label()
		self["vinfo"] = Label()
		self["eptitle"] = Label()
		self["epinfo"] = StaticText()
		self["red"] = Label(_("Exit"))
		self["green"] = Label()
		self["blue"] = Label()
		if is_tmdb:
			self["yellow"] = Label(_("TMDb"))
		elif is_imdb:
			self["yellow"] = Label(_("IMDb"))
		else:
			self["yellow"] = Label()
		self["poster"] = Pixmap()
		self["logo"] = Pixmap()
		self["help"] = Label(_("Press < or RED to go back in the menus"))

		self["vtitle"].hide()
		self["vinfo"].hide()
		self["eptitle"].hide()
		self["help"].hide()
		self["yellow"].hide()
		self.hidden = False

		self["feedlist"].onSelectionChanged.append(self.update_data)
		self.poster_to_download = []
		self.favo_menu = False
		self.favorites = None
		self.favo_cache_modified = False
		self.films = []
		self.menu = []
		self.history = []
		self.chapters = {}
		self.titlemenu = _("VOD Menu")

		self.picload = ePicLoad()
		self.picload.setPara((fhd(200), fhd(60), 1, 1, 0, 0, "#00000000"))
		self.picload.PictureData.get().append(self.showback)
		self.picload.startDecode("/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/logo.png")

		if config.plugins.plutotv.silentmode.value:
			self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.stopService()
		else:
			self.oldService = None

		self["actions"] = ActionMap(
			["OkCancelActions", "ColorActions", "InfobarChannelSelection", "MenuActions", "PlutoTV_Actions"],
			{
				"ok": self.action,
				"cancel": self.exit,
				"red": self.back,
				"green": self.green,
				"yellow": self.imdb,
				"blue": self.favorite,
				"leavePlayer": self.hide_screen,
				"historyBack": self.back,
				"menu": self.keyMenu,
			},
			-1,
		)

		self.updatebutton()
		self.read_favos()

		self.TimerTemp = eTimer()
		self.TimerTemp.callback.append(self.getCategories)
		self.TimerTemp.startLongTimer(1)
		self.posterTimer = eTimer()
		self.posterTimer.callback.append(self.getTimedPoster)
		self.onClose.append(self.save_favos)

	def showback(self, picInfo=None):
		try:
			ptr = self.picload.getData()
			if ptr is not None:
				self["logo"].instance.setPixmap(ptr.__deref__())
				self["logo"].instance.show()
		except Exception as err:
			self["logo"].instance.hide()
			print("[PlutoTV] ERROR showImage:", err)

	def update_data(self):
		if len(self["feedlist"].list) == 0:
			return
		index, name, tipo, _id, region = self.getSelection()
		self["yellow"].hide()
		self["blue"].hide()
		self.blue = False
		if tipo == "menu":
			self["poster"].hide()
			self["red"].setText(_("Exit"))
			if self.favo_menu and name == self.FAVO_NAME:
				self.favo_menu = False
		else:
			self["red"].setText(_("Back"))

		if tipo in ("movie", "series", "empty"):
			film = self.films[index]
			if tipo != "empty":
				self["vtitle"].setText(film[1])
				if not self.favo_menu:
					self["blue"].setText(_("Favorite"))
				else:
					self["blue"].setText(_("Delete favorite"))
				self["blue"].show()
				self.blue = True
			else:
				self["poster"].hide()
				self["vtitle"].setText("")
			self["description"].setText(film[2])
			info = film[4] + "       "
			if tipo == "movie":
				info = info + strftime("%Hh %Mm", gmtime(int(film[5])))
				if is_tmdb or is_imdb:
					self["yellow"].show()
			elif tipo == "series":
				info = info + str(film[10]) + " " + _("Seasons available")
				if is_tmdb or is_imdb:
					self["yellow"].show()
			self["vinfo"].setText(info)
			picname = film[0] + ".jpg"
			pic = film[6]
			pic = urlparse(pic)
			pic = urljoin("https://images.pluto.tv", pic.path.replace("/v3/images", ""))
			if len(picname) > 5:
				filename = os.path.join(FOLDER, picname)
				self.getPoster(filename, pic)
		elif tipo == "seasons":
			self["eptitle"].hide()
			self["epinfo"].setText("")
		elif tipo == "episode":
			film = self.chapters[int(_id)][index]
			self["epinfo"].setText(film[3])
			self["eptitle"].setText(film[1] + "  " + strftime("%Hh %Mm", gmtime(int(film[5]))))
			self["eptitle"].show()

	def getPoster(self, *args):
		self.poster_to_download.append(args)
		self.posterTimer.start(250, True)

	def getTimedPoster(self):
		args = self.poster_to_download[-1]
		self.poster_to_download *= 0
		self._getPoster(*args)

	def _getPoster(self, filename, url):
		down = DownloadPosters()
		if url.endswith(".jpg"):
			url += "?h=640&w=480"
		down.start(filename, url).addCallback(self.actualizaimg, "poster").addErrback(self.posterErr, filename, url)

	def posterErr(self, failure, filename=None, url=""):
		print("[PlutoTV] posterErr", failure, filename, url)
		if url.endswith("/poster.jpg?h=640&w=480"):
			url = url.replace("/poster.jpg?h=640&w=480", "/tile.jpg?h=480&w=480")
			return self._getPoster(filename, url)
		else:
			self["poster"].hide()

	def actualizaimg(self, filename, tipo=None):
		if tipo == "poster" and filename:
			self.decodePoster(filename)

	def getCategories(self):
		self.lvod = {}
		self.menu.append(self.FAVO_NAME)
		if not self.favorites:
			self.favorites = [self.EMPTY_FAVO]
		self.lvod[self.FAVO_NAME] = self.favorites

		region, ondemand = PlutoDownload.getOndemand()
		self.menuitems = int(ondemand.get("totalCategories", "0"))
		categories = ondemand.get("categories", [])
		if len(categories) == 0:
			self["loading"].hide()
			self.session.open(
				MessageBox,
				_("There is no data, it is possible that Pluto TV is not available in your Country"),
				type=MessageBox.TYPE_ERROR,
				timeout=10,
			)
		else:
			[self.buildlist(categorie, region) for categorie in iter(categories)]
			_list = [listentry(key, "menu", "", region=region) for key in iter(self.menu)]
			self["feedlist"].setList(_list)
			self["loading"].hide()

	def buildlist(self, categorie, region):
		name = categorie["name"]
		self.lvod[name] = []
		self.menu.append(name)
		items = categorie.get("items", [])
		for item in iter(items):
			# film = (_id,name,summary,genre,rating,duration,poster,image,type,region)
			itemid = item.get("_id", "")
			if len(itemid) == 0:
				continue
			itemname = item.get("name", "")
			itemsummary = item.get("summary", "")
			itemgenre = item.get("genre", "")
			itemrating = item.get("rating", "")
			if itemrating.isdigit():
				itemrating = "FSK-{0}".format(itemrating)
			itemduration = int(item.get("duration") or "0") // 1000  # in seconds
			itemimgs = item.get("covers", [])
			itemtype = item.get("type", "")
			seasons = len(item.get("seasonsNumbers", []))
			itemimage = ""
			itemposter = ""
			if itemtype == "movie":
				urls = item.get("stitched", {}).get("urls")
				if not isinstance(urls, list) or len(urls) == 0:
					continue
				else:
					url = urls[0].get("url", "")
			else:
				url = ""

			if len(itemimgs) > 2:
				itemimage = itemimgs[2].get("url", "")
			if len(itemimgs) > 1 and len(itemimage) == 0:
				itemimage = itemimgs[1].get("url", "")
			if len(itemimgs) > 0:
				itemposter = itemimgs[0].get("url", "")
			self.lvod[name].append(
				(
					itemid,
					itemname,
					itemsummary,
					itemgenre,
					itemrating,
					itemduration,
					itemposter,
					itemimage,
					itemtype,
					url,
					seasons,
					region,
				)
			)

	def buildchapters(self, chapters):
		self.chapters.clear()
		items = chapters.get("seasons", [])
		for item in iter(items):
			chs = item.get("episodes", [])
			for ch in iter(chs):
				season = ch.get("season", 0)
				if season != "":
					if season not in self.chapters:
						self.chapters[season] = []
					_id = ch.get("_id", "")
					name = ch.get("name", "")
					number = str(ch.get("number", "0"))
					summary = ch.get("description", "")
					rating = ch.get("rating", "")
					duration = int(ch.get("duration", "0") or "0") // 1000
					genre = ch.get("genre", "")
					imgs = ch.get("covers", [])
					urls = ch.get("stitched", {}).get("urls", [])
					if len(urls) > 0:
						url = urls[0].get("url", "")
					else:
						continue

					itemimage = ""
					itemposter = ""
					if len(imgs) > 2:
						itemimage = imgs[2].get("url", "")
					if len(imgs) > 1 and len(itemimage) == 0:
						itemimage = imgs[1].get("url", "")
					if len(imgs) > 0:
						itemposter = imgs[0].get("url", "")
					self.chapters[season].append(
						(_id, name, number, summary, rating, duration, genre, itemposter, itemimage, url)
					)

	def getSelection(self):
		try:
			index = self["feedlist"].getSelectionIndex()
			data = self["feedlist"].getCurrent()[0]

			return index, data[0], data[1], data[2], data[3]
		except TypeError:
			return index, "", None, None, None

	def action(self):
		index, name, tipo, _id, region = self.getSelection()
		menu = []
		menuact = self.titlemenu
		if tipo == "menu":
			if name == self.FAVO_NAME:
				self.favo_menu = True
			self.films = self.lvod[self.menu[index]]
			for x in iter(self.films):
				sname = x[1]
				stipo = x[8]
				sid = x[0]
				region = x[11]
				menu.append(listentry(sname, stipo, sid, region=region))
			self["feedlist"].moveToIndex(0)
			self["feedlist"].setList(menu)
			self.titlemenu = name
			self["playlist"].setText(self.titlemenu)
			self.history.append((index, menuact))
			self["vtitle"].show()
			self["vinfo"].show()
			self["help"].show()
		elif tipo == "series":
			region = self.films[index][11]
			chapters = PlutoDownload.getVOD(_id, region)
			self.buildchapters(chapters)
			stipo = "seasons"
			for key in self.chapters:
				sname = str(key)
				sid = str(key)
				menu.append(listentry(_("Season") + " " + sname, stipo, sid, region=region))

			if not menu:
				menu.append(listentry(_("No season available"), stipo, None, region=region))
			self["feedlist"].setList(menu)
			self.titlemenu = name + " - " + _("Seasons")
			self["playlist"].setText(self.titlemenu)
			self.history.append((index, menuact))
			self["feedlist"].moveToIndex(0)
		elif tipo == "seasons":
			stipo = "episode"
			try:
				for key in iter(self.chapters[int(_id)]):
					sname = key[1]
					sid = key[0]
					menu.append(listentry(_("Episode") + " " + key[2] + ". " + sname, stipo, _id, sid, region=region))
			except Exception as err:
				print("[PlutoTV] ERROR action:", err)
				return

			if not menu:
				menu.append(listentry(_("No episode available"), stipo, None, region=region))
			self["feedlist"].setList(menu)
			self.titlemenu = menuact.split(" - ")[0] + " - " + name
			self["playlist"].setText(self.titlemenu)
			self.history.append((index, menuact))
			self["feedlist"].moveToIndex(0)
		elif tipo == "movie":
			film = self.films[index]
			sid = film[0]
			name = film[1]
			url = film[9]
			self.playVOD(name, sid, url)
		elif tipo == "episode":
			film = self.chapters[int(_id)][index]
			sid = film[0]
			name = film[1]
			url = film[9]
			self.playVOD(name, sid, url)

	def back(self):
		index, name, tipo, _id, region = self.getSelection()
		if tipo == "menu":
			return self.exit()
		menu = []
		if len(self.history) > 0:
			hist = self.history[-1][0]
			histname = self.history[-1][1]
			if tipo in ("movie", "series", "empty"):
				for key in iter(self.menu):
					menu.append(listentry(key, "menu", "", region=region))
				self["help"].hide()
				self["description"].setText("")
				self["vtitle"].hide()
				self["vinfo"].hide()
			if tipo == "seasons":
				for x in iter(self.films):
					sname = x[1]
					stipo = x[8]
					sid = x[0]
					menu.append(listentry(sname, stipo, sid, region=region))
			if tipo == "episode":
				for key in self.chapters:
					sname = str(key)
					stipo = "seasons"
					sid = str(key)
					menu.append(listentry(_("Season") + " " + sname, stipo, sid, region=region))
			self["feedlist"].setList(menu)
			self.history.pop()
			self["feedlist"].moveToIndex(hist)
			self.titlemenu = histname
			self["playlist"].setText(self.titlemenu)

	def keyMenu(self):
		self.openPlutoSettings()

	def playVOD(self, name, sid, url):
		_sid, device_id = PlutoDownload.getUUID()
		url = update_qsd(
			url,
			{
				"deviceId": device_id,
				"sid": device_id,
				"deviceType": "web",
				"deviceMake": "Firefox",
				"deviceModel": "Firefox",
				"appName": "web",
			},
		)
		ref = "4097:0:0:0:0:0:0:0:0:0:{0}:{1}".format(url.replace(":", "%3A"), name.replace(":", "%3A"))
		reference = eServiceReference(ref)
		if "m3u8" in url.lower():
			self.session.openWithCallback(self.returnplayer, Pluto_Player, service=reference, sid=sid)

	def returnplayer(self):
		menu = []
		for _l in iter(self["feedlist"].list):
			menu.append(listentry(_l[0][0], _l[0][1], _l[0][2], _l[0][3], _l[0][4]))
		self["feedlist"].setList(menu)

	def decodePoster(self, image):
		try:
			x = self["poster"].instance.size().width()
			y = self["poster"].instance.size().height()
			picture = image.replace("\n", "").replace("\r", "")
			self.picload.setPara((x, y, 1, 1, 0, 0, "#00000000"))
			_l = self.picload.PictureData.get()
			del _l[:]
			_l.append(self.showImage)
			self.picload.startDecode(picture)
		except Exception as err:
			print("[PlutoTV] ERROR decodeImage:", err)

	def showImage(self, picInfo=None):
		try:
			ptr = self.picload.getData()
			if ptr is not None:
				self["poster"].instance.setPixmap(ptr.__deref__())
				self["poster"].instance.show()
		except Exception as err:
			print("[PlutoTV] ERROR showImage:", err)

	def green(self):
		self.session.openWithCallback(self.endupdateLive, PlutoDownload.PlutoDownload)

	def blue(self):
		pass

	def hide_screen(self):
		if self.hidden:
			self.show()
		else:
			self.hide()
		self.hidden = not self.hidden

	def endupdateLive(self, ret=None):
		self.updatebutton()
		if ret:
			self.session.open(
				MessageBox,
				_(
					"You now have an updated favorites list with Pluto TV channels on your channel list.\n\n"
					"Everything will be updated automatically every 5 hours."
				),
				type=MessageBox.TYPE_INFO,
				timeout=10,
			)

	def updatebutton(self):
		bouquets = open("/etc/enigma2/bouquets.tv", "r").read()
		upd_bouquets = [
			config.plugins.plutotv.ch_region_1.value,
			config.plugins.plutotv.ch_region_2.value,
			config.plugins.plutotv.ch_region_3.value,
			config.plugins.plutotv.ch_region_4.value,
			config.plugins.plutotv.ch_region_5.value,
		]

		if os.path.isfile("/etc/Plutotv.timer") and all(
			".pluto_tv{0}.tv".format("" if x in ("local",) else "_{0}".format(x)) in bouquets
			for x in filter(lambda v: v != "none", set(upd_bouquets))
		):
			last = float(open("/etc/Plutotv.timer", "r").read().replace("\n", "").replace("\r", ""))
			txt = _("Last:") + strftime(" %Y-%m-%d %H:%M", localtime(int(last)))
			self["green"].setText(_("Update Pluto TV Bouquets") + "\n" + txt)
		else:
			m = []
			for x in filter(lambda v: v != "none", set(upd_bouquets)):
				b = ".pluto_tv{0}.tv".format("" if x in ("local",) else "_{0}".format(x))
				if b not in bouquets:
					m.append(x.upper() if x != "local" else _("LOCAL"))
			txt = ", ".join(m) if m else _("None")
			txt = _("{0} Pluto TV Bouquets\n'{1}' missing").format(_("Create") if m else _("Update"), txt)
			self["green"].setText(txt)

	def exit(self):
		self.session.openWithCallback(
			self.confirmexit, MessageBox, _("Do you really want to leave PlutoTV?"), type=MessageBox.TYPE_YESNO
		)

	def confirmexit(self, ret=True):
		if ret:
			self.posterTimer.stop()
			self.TimerTemp.stop()
			if self.oldService:
				self.session.nav.playService(self.oldService)
			self.close()

	def imdb(self):
		index, name, tipo, _id, region = self.getSelection()
		if tipo in ("movie", "series"):
			if is_tmdb:
				try:
					self.session.open(tmdb.tmdbScreen, name, 0)
				except Exception as err:
					print("[PlutoTV] tmdb: ", err)
			elif is_imdb:
				try:
					imdb(self.session, name)
				except Exception as err:
					print("[PlutoTV] imdb: ", err)

	def favorite(self):
		if not self.blue:
			return

		index, name, tipo, _id, region = self.getSelection()
		if tipo in ("movie", "series"):
			if not self.favo_menu:
				for item in iter(self.favorites):
					if item[1] == name:
						print("[PlutoTV]", _("Favorite already exists"), name)
						return self.session.open(MessageBox, _("Favorite already exists"), MessageBox.TYPE_INFO, timeout=2)
				data = self.films[index]
				if len(self.favorites) == 1 and self.favorites[0][8] == "empty":
					self.favorites[0] = data
				else:
					self.favorites.append(data)
				self.favo_cache_modified = True
				print("[PlutoTV]", _("Favorite added"), name)
				return self.session.open(MessageBox, _("Favorite added"), MessageBox.TYPE_INFO, timeout=2)
			else:
				if self.favorites:
					self.favorites.pop(index)
					self.favo_cache_modified = True
				self["feedlist"].list.pop(index)
				if not self.favorites:
					self.favorites.append(self.EMPTY_FAVO)
					_list = [listentry(self.EMPTY_FAVO[1], "empty", "0")]
					self["poster"].hide()
					self["feedlist"].setList(_list)
				else:
					self["feedlist"].setList(self["feedlist"].list)
				print("[PlutoTV] Favorite deleted:", name)

	def save_favos(self):
		if not self.favo_cache_modified:
			return

		print("[PlutoTV] Saving favorites...")
		try:
			with open(self.FAVO_PATH, "wb") as picklefile:
				dump(self.favorites, picklefile, protocol=5)
				self.favo_cache_modified = False
		except Exception as err:
			print("[PlutoTV] Error saving favorites: ", err)

	def read_favos(self):
		print("[PlutoTV] Reading favorites...")
		self.favo_cache_modified = False
		self.favorites = []
		try:
			with open(self.FAVO_PATH, "rb") as picklefile:
				_favorites = load(picklefile)
			for _favo in iter(_favorites):
				if len(_favo) < len(self.EMPTY_FAVO):
					_favo += (None,)
					self.favo_cache_modified = True
				self.favorites.append(_favo)
		except Exception as err:
			print("[PlutoTV] Error reading favorites: ", err)

	def restartEnigma2(self, e2_restart=False, pluto_restart=False):
		if pluto_restart:
			if self.oldService:
				self.session.nav.playService(self.oldService)
			self.close(True)
		elif e2_restart:
			from Screens.Standby import TryQuitMainloop

			self.session.open(TryQuitMainloop, 3)

	def openPlutoSettings(self, callback=None):
		self.session.openWithCallback(self.restartEnigma2, PlutoTVConfig)


class _ConfigList(ConfigList):
	def __init__(self, _list, session=None):
		super(_ConfigList, self).__init__(_list, session)
		self.__cfg_none = {}

	def isChanged(self):
		is_changed = False
		for x in iter(self.list):
			if len(x) > 1:
				is_changed |= x[1].isChanged()
		for x in self.cfg_none.values():
			is_changed |= x.isChanged()
		return is_changed

	@property
	def cfg_none(self):
		return self.__cfg_none


class PlutoTVConfig(Screen, ConfigListScreen):
	if screenWidth and screenWidth == 1920:
		skin = """<screen position="center,center" size="909,800" title="" backgroundColor="#80ffffff" flags="wfNoBorder" name="plutotvConfigScreen">
		<widget name="config" position="15,79" size="879,624" font="Regular;30"  scrollbarMode="showOnDemand" itemHeight="39" zPosition="1" transparent="1" />
		<eLabel name="bg conf" position="2,63" size="906,735" backgroundColor="#20000000" />
		<eLabel name="bg title" position="2,2" size="906,60" backgroundColor="#20000000" />
		<widget name="title" position="2,2" size="906,60" font="Regular;36" backgroundColor="#20000000" foregroundColor="#00ffffff" zPosition="1" halign="center" valign="center" />
		<eLabel name="button green" position="690,770" size="200,8" backgroundColor="green" zPosition="1" />
		<widget name="F2" position="690,725" size="200,39" transparent="1" font="Regular;35" backgroundColor="#26181d20" foregroundColor="#00ffffff" valign="center" halign="center" zPosition="1" />
		</screen>"""
	else:
		skin = """<screen position="center,center" size="606,525" title="" backgroundColor="#80ffffff" flags="wfNoBorder" name="plutotvConfigScreen">
		<widget name="config" position="10,53" size="586,412" font="Regular;20" scrollbarMode="showOnDemand" itemHeight="26" zPosition="1" transparent="1" />
		<eLabel name="bg conf" position="1,42" size="604,482" backgroundColor="#20000000" />
		<eLabel name="bg title" position="1,1" size="604,40" backgroundColor="#20000000" />
		<widget name="title" position="1,1" size="604,40" font="Regular;26" backgroundColor="#20000000" foregroundColor="#00ffffff" zPosition="1" halign="center" valign="center" />
		<eLabel name="button green" position="460,505" size="133,5" backgroundColor="green" zPosition="1" />
		<widget name="F2" position="460,478" size="133,26" transparent="1" font="Regular;16" backgroundColor="#26181d20" foregroundColor="#00ffffff" valign="center" halign="center" zPosition="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "plutotvConfigScreen"
		self["F2"] = Label(_("Ok"))
		self["title"] = Label()
		self["setupActions"] = ActionMap(
			["SetupActions", "ColorActions"],
			{
				"cancel": self.keyCancel,
				"red": self.keyCancel,
				"green": self._keyOK,
				"right": self._keyRight,
			},
			-2,
		)
		self.testLatin = False
		self.config_list = None
		ConfigListScreen.__init__(self, self.config_list, session=session, on_change=self._onKeyChange)
		self["config"] = _ConfigList(self.config_list, session=session)
		self._getConfig()
		self.onLayoutFinish.append(self.layoutFinished)

	def _getConfig(self):
		self.config_list = []
		self.picon_dir = getConfigListEntry(_("Picon Directory"), config.usage.picon_dir)
		self.config_list.append(self.picon_dir)
		self.config_list.append(getConfigListEntry(_("Start PlutoTV in Silent Mode"), config.plugins.plutotv.silentmode))
		self.config_list.append(getConfigListEntry(_("Picon Mode"), config.plugins.plutotv.picon_mode))
		self.config_list.append(getConfigListEntry(_("Use Latin American regions"), config.plugins.plutotv.add_latin_regions))
		self.config_list.append(getConfigListEntry(_("Video Region"), config.plugins.plutotv.region))
		self.config_list.append(getConfigListEntry(_("Add Samsung Channels to bouquets"), config.plugins.plutotv.add_samsung))
		self.config_list.append(getConfigListEntry(_("Add Xiaomi Channels to bouquets"), config.plugins.plutotv.add_xiaomi))
		self.config_list.append(getConfigListEntry(_("Live TV Mode"), config.plugins.plutotv.live_tv_mode))
		self.config_list.append(getConfigListEntry(_("Live TV Channel Numbering"), config.plugins.plutotv.live_tv_ch_numbering))

		self._separator("— {0} {1}".format(_("Pluto TV Bouquets"), 200 * "—"))
		self.config_list.append(getConfigListEntry("1. {0}".format(_("Bouquet")), config.plugins.plutotv.ch_region_1, True))
		if config.plugins.plutotv.ch_region_1.value != "none":
			self.config_list.append(
				getConfigListEntry("   • {0}".format(_("Player Service")), config.plugins.plutotv.service_1)
			)

		if config.plugins.plutotv.ch_region_1.value != "none" or config.plugins.plutotv.ch_region_2.value != "none":
			self.config_list.append(getConfigListEntry("2. {0}".format(_("Bouquet")), config.plugins.plutotv.ch_region_2, True))
			if config.plugins.plutotv.ch_region_2.value != "none":
				self.config_list.append(
					getConfigListEntry("   • {0}".format(_("Player Service")), config.plugins.plutotv.service_2)
				)

		if config.plugins.plutotv.ch_region_2.value != "none" or config.plugins.plutotv.ch_region_3.value != "none":
			self.config_list.append(getConfigListEntry("3. {0}".format(_("Bouquet")), config.plugins.plutotv.ch_region_3, True))
			if config.plugins.plutotv.ch_region_3.value != "none":
				self.config_list.append(
					getConfigListEntry("   • {0}".format(_("Player Service")), config.plugins.plutotv.service_3)
				)

		if config.plugins.plutotv.ch_region_3.value != "none" or config.plugins.plutotv.ch_region_4.value != "none":
			self.config_list.append(getConfigListEntry("4. {0}".format(_("Bouquet")), config.plugins.plutotv.ch_region_4, True))
			if config.plugins.plutotv.ch_region_4.value != "none":
				self.config_list.append(
					getConfigListEntry("   • {0}".format(_("Player Service")), config.plugins.plutotv.service_4)
				)

		if config.plugins.plutotv.ch_region_4.value != "none" or config.plugins.plutotv.ch_region_5.value != "none":
			self.config_list.append(getConfigListEntry("5. {0}".format(_("Bouquet")), config.plugins.plutotv.ch_region_5, True))
			if config.plugins.plutotv.ch_region_5.value != "none":
				self.config_list.append(
					getConfigListEntry("   • {0}".format(_("Player Service")), config.plugins.plutotv.service_5)
				)
		self._separator()
		self["config"].setList(self.config_list)

	def layoutFinished(self):
		from . import __version__

		self["title"].setText("PlutoTV - Setup - (Version {0})".format(__version__))
		self["config"].onSelectionChanged.append(self.selectionChanged)
		self.testLatin = True

	def _keyOK(self):
		if any([config.usage.picon_dir.isChanged(), config.plugins.plutotv.add_latin_regions.isChanged()]):
			self.session.openWithCallback(
				self.saveSettingsAndClose,
				MessageBox,
				_("The Enigma2 settings was changed and Enigma2 should be restarted\n\nDo you want to restart it now?"),
				type=MessageBox.TYPE_YESNO,
			)
		elif any(
			[
				config.plugins.plutotv.live_tv_ch_numbering.isChanged(),
				config.plugins.plutotv.silentmode.isChanged(),
				config.plugins.plutotv.region.isChanged(),
				config.plugins.plutotv.picon_mode.isChanged(),
				config.plugins.plutotv.ch_region_1.isChanged(),
				config.plugins.plutotv.ch_region_2.isChanged(),
				config.plugins.plutotv.ch_region_3.isChanged(),
				config.plugins.plutotv.ch_region_4.isChanged(),
				config.plugins.plutotv.ch_region_5.isChanged(),
				config.plugins.plutotv.add_samsung.isChanged(),
				config.plugins.plutotv.add_xiaomi.isChanged(),
				config.plugins.plutotv.live_tv_mode.isChanged(),
				config.plugins.plutotv.service_1.isChanged(),
				config.plugins.plutotv.service_2.isChanged(),
				config.plugins.plutotv.service_3.isChanged(),
				config.plugins.plutotv.service_4.isChanged(),
				config.plugins.plutotv.service_5.isChanged(),
			]
		):
			if config.plugins.plutotv.picon_mode.isChanged() or (
				config.plugins.plutotv.live_tv_ch_numbering.isChanged() and config.plugins.plutotv.picon_mode.value == "srp"
			):
				self.session.open(
					MessageBox,
					_("The PlutoTV Picons should be deleted before the next Bouquet update."),
					type=MessageBox.TYPE_INFO,
					timeout=10,
				)
			self.saveSettingsAndClose(callback=True, pluto_restart=True)
		else:
			self.saveSettingsAndClose()

	def saveSettingsAndClose(self, callback=False, pluto_restart=False):
		if callback:
			self.saveAll()
		self.close(*(callback, pluto_restart))

	def selectionChanged(self):
		if self.testLatin and config.plugins.plutotv.add_latin_regions.isChanged():
			self.session.openWithCallback(
				self.onLatinChanged,
				MessageBox,
				_("The Latin American setting was changed and Enigma2 should be restarted\n\nDo you want to restart it now?"),
				type=MessageBox.TYPE_YESNO,
			)

	def onLatinChanged(self, answer=False):
		if answer:
			self.saveSettingsAndClose(callback=answer)
		else:
			self.testLatin = False

	def _separator(self, txt=200 * "—"):
		self.config_list.append(
			getConfigListEntry(
				txt,
			)
		)

	def _onKeyChange(self):
		try:
			c = self["config"].getCurrent()
			if c and len(c) > 2 and c[2]:
				if c[0] not in self["config"].cfg_none and c[1].value == "none":
					self["config"].cfg_none[c[0]] = c[1]
				elif c[0] in self["config"].cfg_none and c[1].value != "none":
					self["config"].cfg_none.pop(c[0])
				self._getConfig()
		except Exception as err:
			print("[PlutoTV] Error: {}".format(err))

	def saveAll(self):
		for x in iter(self["config"].list):
			if len(x) > 1:
				x[1].save()
		for x in self["config"].cfg_none.values():
			x.save()
		self["config"].cfg_none.clear()

	def cancelConfirm(self, result):
		if not result:
			return
		for x in iter(self["config"].list):
			if len(x) > 1:
				x[1].cancel()
		for x in self["config"].cfg_none.values():
			x.cancel()
		self.close()

	def _keyRight(self):
		cur = self["config"].getCurrent()
		if cur == self.picon_dir:
			ConfigListScreen.keyOK(self)
		else:
			ConfigListScreen.keyRight(self)


class Pluto_Player(MoviePlayer):

	ENABLE_RESUME_SUPPORT = False  # Don't use Enigma2 resume support. We use self resume support

	def __init__(self, session, service, sid):
		self.mpservice = service
		self.id = sid
		MoviePlayer.__init__(self, session, service)
		self.end = False
		self.started = False
		self.skinName = ["MoviePlayer"]

		self.__event_tracker = ServiceEventTracker(
			screen=self,
			eventmap={
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evBuffering: self.__serviceStarted,
				iPlayableService.evVideoSizeChanged: self.__serviceStarted,
				iPlayableService.evEOF: self.__evEOF,
			},
		)

		self["actions"] = ActionMap(
			["MoviePlayerActions", "OkCancelActions", "NumberActions", "EPGSelectActions"],
			{
				"cancel": self.leavePlayer,
				"exit": self.leavePlayer,
				"leavePlayer": self.leavePlayer,
				"ok": self.toggleShow,
			},
			-3,
		)
		self.session.nav.playService(self.mpservice)

	def up(self):
		pass

	def down(self):
		pass

	def doEofInternal(self, playing):
		self.close()

	def __evEOF(self):
		self.end = True

	def __serviceStarted(self):
		service = self.session.nav.getCurrentService()
		seekable = service.seek()
		last, length = getResumePoint(self.id)
		if last is None:
			return
		if seekable is None:
			return
		length = seekable.getLength() or (None, 0)
		print("[PlutoTV] seekable.getLength() returns:", length)
		# Hmm, this implies we don't resume if the length is unknown...
		if (last > 900000) and (not length[1] or (last < length[1] - 900000)):
			self.resume_point = last
			_l = last / 90000
			if not self.started:
				self.started = True
				Notifications.AddNotificationWithCallback(
					self.playLastCB,
					MessageBox,
					_("Do you want to resume this playback?")
					+ "\n"
					+ (_("Resume position at %s") % ("%d:%02d:%02d" % (_l / 3600, _l % 3600 / 60, _l % 60))),
					timeout=10,
					default="yes" in config.usage.on_movie_start.value,
				)

	def leavePlayer(self):
		laref = _("Stop play and exit to list movie?")
		try:
			dei = self.session.openWithCallback(self.callbackexit, MessageBox, laref, MessageBox.TYPE_YESNO)
			dei.setTitle(_("Stop play"))
		except Exception:
			self.callbackexit(True)

	def callbackexit(self, respuesta):
		if respuesta:
			self.is_closing = True
			setResumePoint(self.session, self.id)
			self.close()

	def leavePlayerConfirmed(self, answer):
		pass

	def exit(self):
		self.callbackexit(True)


def autostart(reason, session):
	if PlutoDownload.Silent is None:
		PlutoDownload.Silent = PlutoDownload.DownloadSilent(session)


def Download_PlutoTV(session, **kwargs):
	session.open(PlutoDownload.PlutoDownload)


def system(session, **kwargs):
	def restartPlutoTV(restart=False):
		if restart:
			session.openWithCallback(restartPlutoTV, PlutoTV)

	session.openWithCallback(restartPlutoTV, PlutoTV)


def Plugins(**kwargs):
	_list = [
		PluginDescriptor(
			name=_("PlutoTV"),
			where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
			icon="plutotv.png",
			description=_("Plugin to play videos and to create a PlutoTV channel list"),
			fnc=system,
		),
		PluginDescriptor(
			name=_("Download PlutoTV Bouquet, picons & EPG"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=Download_PlutoTV
		),
		PluginDescriptor(name=_("Silent Download PlutoTV"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart),
	]
	return _list

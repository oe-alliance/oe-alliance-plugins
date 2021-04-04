#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
# maintainer: schomi@vuplus-support.org & einfall
#
#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.
#######################################################################

from __future__ import print_function
from __future__ import absolute_import

from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import *
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmap, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.PluginComponent import plugins
from Components.config import *
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.ScrollLabel import ScrollLabel
# from Components.FileList import FileList
from re import compile as re_compile
from os import path as os_path, listdir
from Components.MenuList import MenuList
from Components.Harddisk import harddiskmanager
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename, fileExists
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, eServiceReference, eServiceCenter, gFont
from Tools.LoadPixmap import LoadPixmap
from Screens.EpgSelection import EPGSelection
from Screens.ChannelSelection import SimpleChannelSelection
from ServiceReference import ServiceReference
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.HelpMenu import HelpableScreen
from Components.GUIComponent import GUIComponent
from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Tools.Directories import pathExists, fileExists, SCOPE_SKIN_IMAGE, resolveFilename
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, loadPNG, RT_WRAP, eConsoleAppContainer, eServiceCenter, eServiceReference, getDesktop, loadPic, loadJPG, RT_VALIGN_CENTER, gPixmapPtr, ePicLoad, eTimer
import sys
import os
import re
import shutil
import json
import skin
from os import path, remove
from twisted.web.client import downloadPage
from twisted.web import client, error as weberror
from twisted.internet import reactor
from twisted.internet import defer
import six
from six.moves.urllib.parse import urlencode
from .__init__ import _

from . import tmdbsimple as tmdb
tmdb.API_KEY = 'd42e6b820a1541cc69ce789671feba39'


pname = _("TMDb")
pdesc = _("TMDb ... function for Movielist")
pversion = "0.7-r2"
pdate = "20171215"

config.plugins.tmdb = ConfigSubsection()
config.plugins.tmdb.themoviedb_coversize = ConfigSelection(default="w185", choices=["w92", "w185", "w500", "original"])
config.plugins.tmdb.lang = ConfigSelection(default="de", choices=["de", "en"])
config.plugins.tmdb.firsthit = ConfigYesNo(default=True)

def cleanFile(text):
	cutlist = ['x264','720p','1080p','1080i','PAL','GERMAN','ENGLiSH','WS','DVDRiP','UNRATED','RETAIL','Web-DL','DL','LD','MiC','MD','DVDR','BDRiP','BLURAY','DTS','UNCUT','ANiME',
				'AC3MD','AC3','AC3D','TS','DVDSCR','COMPLETE','INTERNAL','DTSD','XViD','DIVX','DUBBED','LINE.DUBBED','DD51','DVDR9','DVDR5','h264','AVC',
				'WEBHDTVRiP','WEBHDRiP','WEBRiP','WEBHDTV','WebHD','HDTVRiP','HDRiP','HDTV','ITUNESHD','REPACK','SYNC']
	text = text.replace('.wmv','').replace('.flv','').replace('.ts','').replace('.m2ts','').replace('.mkv','').replace('.avi','').replace('.mpeg','').replace('.mpg','').replace('.iso','')
	
	for word in cutlist:
		text = re.sub('(\_|\-|\.|\+)'+word+'(\_|\-|\.|\+)','+', text, flags=re.I)
	text = text.replace('.',' ').replace('-',' ').replace('_',' ').replace('+','')

	return text
	
def cleanEnd(text):
	text = text.replace('.wmv','').replace('.flv','').replace('.ts','').replace('.m2ts','').replace('.mkv','').replace('.avi','').replace('.mpeg','').replace('.mpg','').replace('.iso','').replace('.mp4','')
	return text

class createList(GUIComponent, object):
	GUI_WIDGET = eListbox
	
	def __init__(self, mode):
		GUIComponent.__init__(self)
		self.mode = mode
		self.l = eListboxPythonMultiContent()
		#self.l.setFont(0, gFont('Regular', 22))
		font, size = skin.parameters.get("TMDbListFont", ('Regular', 23))
		self.l.setFont(0, gFont(font, size))
		self.l.setItemHeight(30)
		self.l.setBuildFunc(self.buildList)

	def buildList(self, entry):
		if self.mode == 0:
			width = self.l.getItemSize().width()
			(title, coverUrl, media, id) = entry
			res = [None]
			x,y,w,h = skin.parameters.get("TMDbListName", (5,1,1920,30))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT, str(title)))
			#res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 0, 800, 30, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(title)))
			return res

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		self.instance.setWrapAround(True)

	def preWidgetRemove(self, instance):
		instance.setContent(None)

	def setList(self, list):
		self.l.setList(list)

	def moveToIndex(self, idx):
		self.instance.moveSelectionTo(idx)

	def getSelectionIndex(self):
		return self.l.getCurrentSelectionIndex()

	def getSelectedIndex(self):
		return self.l.getCurrentSelectionIndex()

	def selectionEnabled(self, enabled):
		if self.instance is not None:
			self.instance.setSelectionEnable(enabled)

	def pageUp(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageUp)

	def pageDown(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageDown)

	def up(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveUp)

	def down(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveDown)
		
class tmdbConfigScreen(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["tmdbConfigScreen", "Setup"]
		self.setup_title = _("Setup")

		self.onChangedEntry = []
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)
		
		self["actions"] = ActionMap(["TMDbActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keyOK,
				"red": self.keyCancel,
				"green": self.keyOK,
			}, -2)

		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))

		self.list = []
		self.createConfigList()	
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(pname + " (" + pversion + ")")

	def createConfigList(self):
		self.setTitle("TMDb - The Movie Database v"+pversion)
		self.list = []
		self.list.append(getConfigListEntry(_("Cover resolution:"), config.plugins.tmdb.themoviedb_coversize))
		self.list.append(getConfigListEntry(_("Language:"), config.plugins.tmdb.lang))
		self.list.append(getConfigListEntry(_("Show details if single result:"), config.plugins.tmdb.firsthit))		
		self["config"].list = self.list
		self["config"].setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def keyOK(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()			
		self.close()

class tmdbScreen(Screen, HelpableScreen):
	skin = """
		<screen position="40,80" size="1200,600" title="TMDb - The Movie Database" >
			<widget name="searchinfo" position="20,10" size="1180,30" font="Regular;24" foregroundColor="#00fff000"/>
			<widget name="list" position="10,60" size="800,480" scrollbarMode="showOnDemand"/>
			<widget name="cover" position="840,90" size="300,450" alphatest="blend"/>
			<widget name="key_red" position="100,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget name="key_green" position="395,570" size="260,25"  transparent="1" font="Regular;20"/>
			<widget name="key_yellow" position="690,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget name="key_blue" position="985,570" size="260,25" transparent="1" font="Regular;20"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""	

	def __init__(self, session, service, mode):
		Screen.__init__(self, session)
		self.session = session
		self.mode = mode
		self.saveFilename = ""
		self.coverName = ""
		self.piclist =""
		
		if self.mode == 1:
			self.isDirectory = False
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(service)
			path = service.getPath()
			self.savePath = path
			self.dir = '/'.join(path.split('/')[:-1]) + '/'
			self.file = self.baseName(path)
			if path.endswith("/") is True:
				path = path[:-1]
				self.file = self.baseName(path)
				self.text = self.baseName(path)
				self.isDirectory = True
			else:
				self.text = cleanFile(info.getName(service))
				self.saveFilename = path
				self.isDirectory = False
		else:
			self.text = service
		
		print("[TMDb] " + str(self.text))
		
		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self,"TMDbActions",
			{
				"ok": (self.ok, _("Show details")),
				"cancel": (self.cancel,_("Exit")),
				"up": (self.keyUp, _("Selection up")),
				"down": (self.keyDown, _("Selection down")),
				"left": (self.keyLeft, _("Page up")),
				"right": (self.keyRight, _("Page down")),
				"red": (self.cancel, _("Exit")),
				"green": (self.ok, _("Show details")),
				"yellow": (self.searchString, _("Edit search")),
				"blue": (self.keyBlue, _("Setup")),
				"menu": (self.keyBlue, _("Setup")),
				"eventview": (self.searchString, _("Edit search"))
			}, -1)		
		
		self['searchinfo'] = Label(_("Loading..."))
		self['key_red'] = Label(_("Exit"))
		self['key_green'] = Label(_("Details"))
		self['key_yellow'] = Label(_("Edit search"))
		self['key_blue'] = Label(_("Setup"))
		self['list'] = createList(0)
		
		self['cover'] = Pixmap()
		
		self.tempDir = "/var/volatile/tmp/"
		self.onLayoutFinish.append(self.onFinish)
		
	def onFinish(self):
		if not self.text == "":
			if re.search('[Ss][0-9]+[Ee][0-9]+', self.text):
				self.text = re.sub('[Ss][0-9]+[Ee][0-9]+.*[a-zA-Z0-9_]+','', self.text, flags=re.S|re.I)
			#self.text="xyzabc"
			self.tmdbSearch()
		else:
			print("[TMDb] no movie found.")
			self['searchinfo'].setText(_("No Movie information found for %s") % self.text)
			
	def tmdbSearch(self):
		self['searchinfo'].setText(_("Try to find %s in tmdb ...") % self.text)
		self.lang = config.plugins.tmdb.lang.value
		res = []	
		self.count = 0
		
		try:
			search = tmdb.Search()
			json_data = search.multi(query=self.text, language=self.lang)
			#print json_data
			
			for IDs in json_data['results']:
				self.count+=1
				try:
					media = str(IDs['media_type'])
				except:
					media = ""
				try:
					id = str(IDs['id'])
				except:
					id = ""
				
				title = ""
				try:
					title = str(IDs['title'])
				except:
					pass
				try:
					title = str(IDs['name'])
				except:
					pass
				
				date = ""
				try:
					date = ", "+ str(IDs['release_date'])[:4]
				except:
					pass					
				if date == ", ":
					date = ""
				
				if media == "movie":
					mediasubst = _("Movie")
				else:
					mediasubst = _("Series")
					
				title = "%s (%s%s)" % (title,mediasubst,date)
				
				coverPath = ""
				try:
					coverPath = str(IDs['poster_path'])
				except:
					pass
				
				cover = self.tempDir+id+".jpg"
				url_cover = "http://image.tmdb.org/t/p/%s/%s" % (config.plugins.tmdb.themoviedb_coversize.value, coverPath)

				if not id == "" or not title == "" or not media == "":
					res.append(((title, url_cover, media, id),))
			self['list'].setList(res)
			self.piclist = res
			self['searchinfo'].setText(_("TMDB: Results for %s") % self.text)
			self.getInfo()
		except:
			self['searchinfo'].setText(_("TMDb: No results found, or does not respond!"))

	def getInfo(self):
		url_cover = self['list'].getCurrent()[1]
		id = self['list'].getCurrent()[3]
		
		if url_cover[-4:] == "None":
			self.showCover("/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/no_cover.png")
		else:
			if not fileExists(self.tempDir+id+".jpg"):
				downloadPage(six.ensure_binary(url_cover), self.tempDir+id+".jpg").addCallback(self.getData, self.tempDir+id+".jpg").addErrback(self.dataError)
			else:
				self.showCover(self.tempDir+id+".jpg")

	def getData(self, data, coverSaved):
		self.showCover(coverSaved)

	def dataError(self, error):
		print("[TMDb] Error: %s" % error)

	def baseName(self, str):
		name = str.split('/')[-1]
		return name
			
	def showCover(self, coverName):
		self.picload = ePicLoad()
		if not fileExists(coverName):
			coverName = "/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/no_cover.png"

		if fileExists(coverName):
			self['cover'].instance.setPixmap(gPixmapPtr())
			scale = AVSwitch().getFramebufferScale()
			size = self['cover'].instance.size()
			self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, ""))
			if self.picload.startDecode(coverName, 0, 0, False) == 0:
				ptr = self.picload.getData()
				if ptr != None:
					self['cover'].instance.setPixmap(ptr)
					self['cover'].show()
			del self.picload
			self.coverName = coverName
		
		# Only one result launch details
		if config.plugins.tmdb.firsthit.value:
			if self.count == 1:
				self.ok()			
		
	def ok(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		# title, url_cover, media, id
		title =  self['list'].getCurrent()[0]
		media = self['list'].getCurrent()[2]
		id = self['list'].getCurrent()[3]
		cover = self.tempDir+id+".jpg"

		self.session.open(tmdbScreenMovie, title, media, cover, id, self.saveFilename)

	def keyLeft(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].pageUp()
		self.getInfo()

	def keyRight(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].pageDown()
		self.getInfo()

	def keyDown(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].down()
		self.getInfo()

	def keyUp(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].up()
		self.getInfo()

	def keyYellow(self):
		return
		
	def keyBlue(self):
		self.session.open(tmdbConfigScreen)

	def searchString(self):
		self.session.openWithCallback(self.goSearch, VirtualKeyBoard, title=(_("Search for Movie:")), text=self.text)

	def goSearch(self, newTitle):
		if newTitle is not None:
			self.text = newTitle
			self.tmdbSearch()
		else:
			self.tmdbSearch()

	def cancel(self):
		self.delCover()
		self.close()

	def delCover(self):
		list = self.piclist
		if list == None:
			return		
		
		count=0
		while count<len(list):
			id = list[count][0][3]
			try:
				os.remove(self.tempDir+id+".jpg")
			except:
				pass
			count+=1	

class tmdbScreenMovie(Screen, HelpableScreen):
	skin = """
		<screen position="40,80" size="1200,600" title="TMDb - The Movie Database" backgroundColor="#20666666">
			<widget name="searchinfo" position="10,10" size="930,30" font="Regular;24" foregroundColor="#00fff000" transparent="1"/>
			<widget name="fulldescription" position="10,60" size="620,490" font="Regular;22" transparent="1"/>
			<widget name="cover" position="950,30" size="200,300" alphatest="blend"/>
			<ePixmap position="705,45" size="100,100" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/star.png" transparent="1" alphatest="blend"/>
			<widget name="rating" position="680,85" size="150,25" zPosition="2" font="Regular;22" halign="center" foregroundColor="black" backgroundColor="#00ffba00" transparent="1"/>
			<widget name="votes_brackets" position="680,145" size="150,25" zPosition="2" font="Regular;22" halign="center" transparent="1"/>
			<widget name="fsk" position="0,0" size="0,0" zPosition="2" font="Regular;22" halign="center" transparent="1"/>
			<widget name="fsklogo" position="825,60" size="100,100" zPosition="2" alphatest="blend"/>
			
			<widget name="year_txt" position="650,220" size="400,25" zPosition="2" font="Regular;22"  transparent="1"/>
			<widget name="year" position="780,220" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="country_txt" position="650,250" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="country" position="780,250" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="runtime_txt" position="650,280" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="runtime" position="780,280" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="votes_txt" position="650,310" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="votes" position="780,310" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="director_txt" position="650,340" size="400,25" zPosition="2" font="Regular;22"  transparent="1"/>
			<widget name="director" position="780,340" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="author_txt" position="650,370" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="author" position="780,370" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="genre_txt" position="650,400" size="100,30" font="Regular; 22" transparent="1"/>
			<widget name="genre" position="780,400" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="studio_txt" position="650,430" size="100,30" font="Regular; 22" transparent="1"/>
			<widget name="studio" position="780,430" size="400,25" zPosition="2" font="Regular;22" transparent="1"/>
			<widget name="subtitle" position="0,0" size="0,0" zPosition="2" transparent="1" font="Regular;22" foregroundColor="#00fff000"/>			
			<widget name="description" position="0,0" size="0,0" zPosition="2" transparent="1" font="Regular;22"/>
			
			<widget name="key_red" position="100,570" size="260,25" font="Regular;20" transparent="1"/>
			<widget name="key_green" position="395,570" size="260,25" font="Regular;20" transparent="1"/>
			<widget name="key_yellow" position="690,570" size="260,25" font="Regular;20" transparent="1"/>
			<widget name="key_blue" position="985,570" size="260,25" font="Regular;20" transparent="1"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""	

	def __init__(self, session, mname, media, coverName, id, saveFilename):
		Screen.__init__(self, session)
		self.session = session
		self.mname = mname
		self.media = media
		if self.media == "movie":
			self.movie = True
		else:
			self.movie = False
		self.coverName = coverName
		self.trailer = None
		self.id = id
		self.saveFilename = saveFilename

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self,"TMDbActions",
			{
				"ok": (self.ok, _("Crew")),
				"cancel": (self.cancel,_("Exit")),
				"up": (self.keyLeft, _("Selection up")),
				"down": (self.keyRight, _("Selection down")),
				"left": (self.keyLeft, _("Page up")),
				"right": (self.keyRight, _("Page down")),
				"red": (self.cancel, _("Exit")),
				"green": (self.keyGreen, _("Crew")),
				"yellow": (self.keyYellow, _("Seasons")),
				"blue": (self.keyBlue, _("Setup")),
				"menu": (self.keyBlue, _("Setup")),
				"eventview": (self.writeTofile, _("Save TMDb movie infos to file"))				
			}, -1)	

		self['searchinfo'] = Label(_("Loading..."))
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
		self['key_green'] = Label(_("Crew"))
		self['key_yellow'] = Label(_("Seasons"))
		self['key_blue'] = Label(_("Setup"))
		self['cover'] = Pixmap()
		self['fsklogo'] = Pixmap()
		
		self.onLayoutFinish.append(self.onFinish)
		
	def onFinish(self):
		if self.movie:
			self['key_yellow'].setText(" ")
		# TMDb read
		print("[TMDb] Selected: %s" % self.mname)
		self['searchinfo'].setText("%s" % self.mname)
		self.showCover(self.coverName)
		self.getData()
		
	def keyLeft(self):
		self['description'].pageUp()
		self['fulldescription'].pageUp()
	
	def keyRight(self):
		self['description'].pageDown()
		self['fulldescription'].pageDown()

	def getData(self):
		self.lang = config.plugins.tmdb.lang.value
		print("[TMDb] ID: ", self.id)
				
		try:
			if self.movie:
				json_data = tmdb.Movies(self.id).info(language=self.lang)
				#print json_data
				json_data_cast = tmdb.Movies(self.id).credits(language=self.lang)
				#print json_data_cast
				json_data_fsk = tmdb.Movies(self.id).releases(language=self.lang)
				#print json_data_fsk				
			elif not self.movie:
				json_data = tmdb.TV(self.id).info(language=self.lang)
				#print json_data
				json_data_cast = tmdb.TV(self.id).credits(language=self.lang)
				#print json_data_cast
				json_data_fsk = tmdb.TV(self.id).content_ratings(language=self.lang)
				#print json_data_fsk				
			else:
				return
		except:
			self['searchinfo'].setText(_("TMDb: No results found, or does not respond!"))	
			return
		
		## Year
		year = ""
		try:
			year = json_data['release_date'][:+4]
			self['year'].setText("%s" % str(year))
		except:
			year = ""
			
		## Rating
		vote_average = ""
		try:
			vote_average = json_data['vote_average']
			self['rating'].setText("%s" % str(vote_average))
		except:
			vote_average = ""
		
		## Votes
		vote_count = ""
		try:
			vote_count = json_data['vote_count']
			self['votes'].setText("%s" % str(vote_count))
			self['votes_brackets'].setText("(%s)" % str(vote_count))
		except:
			vote_count = ""
		
		## Runtime
		runtime = ""
		try:
			runtime = json_data['runtime']
			self['runtime'].setText("%s min." % str(runtime))
			runtime = ", " + str(runtime) + " min."
		except:
			runtime = "-"
		
		## Country
		country_string = ""
		try:
			for country in json_data['production_countries']:
				country_string += country['iso_3166_1']+"/"
			country_string = country_string[:-1]
			self['country'].setText("%s" % str(country_string))
		except:
			country_string = ""
			
		## Genre"
		genre_string = ""
		try:
			genre_count = len(json_data['genres'])
			for genre in json_data['genres']:
				genre_string += genre['name']+", "
			self['genre'].setText("%s" % str(genre_string[:-2]))
		except:
			genre_string = ""
		
		## Subtitle
		subtitle = ""
		try:
			subtitle = json_data['tagline']
			self['subtitle'].setText("%s" % str(subtitle))
			subtitle = str(subtitle) + "\n"
		except:
			subtitle = ""
			
		## Cast
		cast_string = ""
		try:
			for cast in json_data_cast['cast']:
				cast_string += cast['name']+" ("+ cast['character'] + ")\n"
		except:
			cast_string = ""
			
		## Crew
		crew_string = ""
		director = ""
		author = ""
		try:
			for crew in json_data_cast['crew']:
				crew_string += crew['name']+" ("+ crew['job'] + ")\n"
				
				if crew['job'] == "Director":
					director += crew['name']+", "
				if crew['job'] == "Screenplay" or crew['job'] == "Writer":
					author += crew['name']+", "
			director = director[:-2]
			author = author[:-2]
			self['director'].setText("%s" % str(director))
			self['author'].setText("%s" % str(author))
		except:
			crew_string = ""
			director = ""
			author = ""
			
		## Studio/Production Company
		studio_string = ""
		try:
			for studio in json_data['production_companies']:
				studio_string += studio['name'] +", "
			studio_string = studio_string[:-2]
			self['studio'].setText("%s" % str(studio_string))
		except:
			studio_string = ""

		
		#
		# modify Data for TV/Series
		#
		season = ""
		if not self.movie:
			## Year
			year = ""
			try:
				year = json_data['first_air_date'][:+4]
				self['year'].setText("%s" % str(year))
			except:
				year = ""
			
			## Country
			country_string = ""
			try:
				for country in json_data['origin_country']:
					country_string += country + "/"
				country_string = country_string[:-1]
				self['country'].setText("%s" % str(country_string))
			except:
				country_string = ""

		
			## Crew Director 
			director = ""
			try:
				for directors in json_data['created_by']:
					director += directors['name'] +", "
				director = director[:-2]
				self['director'].setText(_("Various"))
				self['author'].setText("%s" % str(director))
			except:
				director = ""
				
			## Studio/Production Company
			try:
				for studio in json_data['networks']:
					studio_string += studio['name'] +", "
				studio_string = studio_string[:-2]
				self['studio'].setText("%s" % str(studio_string))
			except:
				studio_string = ""		
		
			## Runtime
			runtime = ""
			try:
				seasons = json_data['number_of_seasons']
				episodes = json_data['number_of_episodes']
				runtime = str(seasons) + " " + _("Seasons")+ " / " + str(episodes) + " " + _("Episodes")
				self['runtime'].setText("%s" % runtime)
				runtime =  ", " + runtime
			except:
				runtime = ""

			# Series Description
			season = ""
			try:
				for seasons in json_data['seasons']:
					if seasons['season_number'] >= 1:
						season += _("Season") + " " + str(seasons['season_number']) +"/"+ str(seasons['episode_count']) + " (" + str(seasons['air_date'])[:4] + ")\n"
			except:
				season = ""
			
		## Description
		description = ""
		try:
			description = json_data['overview']
			description = description + "\n\n" + cast_string + "\n" + crew_string
			self['description'].setText("%s" % description)
			
			movieinfo = "%s%s %s %s" % (str(genre_string), str(country_string), str(year), str(runtime))
			fulldescription = subtitle + movieinfo + "\n\n" + description + "\n" + season
			self['fulldescription'].setText("%s" % fulldescription)
			self.text = fulldescription
		except:
			description = "-"

		## FSK
		fsk = "100"
		if self.movie:
			try:
				for country in json_data_fsk['countries']:
					if str(country['iso_3166_1']) == "DE":
						fsk = str(country['certification'])
			except:
				pass
		if not self.movie:			
			try:
				for country in json_data_fsk['results']:
					if str(country['iso_3166_1']) == "DE":
						fsk = str(country['rating'])
			except:
				pass
				
		self.showFSK(fsk)
			
	def dataError(self, error):
		print(error)

	def showCover(self, coverName):
		self.picload = ePicLoad()
		if not fileExists(coverName):
			coverName = "/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/no_cover.png"

		if fileExists(coverName):
			self['cover'].instance.setPixmap(gPixmapPtr())
			scale = AVSwitch().getFramebufferScale()
			size = self['cover'].instance.size()
			self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, ""))
			if self.picload.startDecode(coverName, 0, 0, False) == 0:
				ptr = self.picload.getData()
				if ptr != None:
					self['cover'].instance.setPixmap(ptr)
					self['cover'].show()
			del self.picload

	def showFSK(self, fsk):
		self.fsklogo = "/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/fsk_" + fsk + ".png"
		self.picload = ePicLoad()
		self['fsklogo'].instance.setPixmap(gPixmapPtr())
		scale = AVSwitch().getFramebufferScale()
		size = self['fsklogo'].instance.size()
		self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, ""))
		if self.picload.startDecode(self.fsklogo, 0, 0, False) == 0:
			ptr = self.picload.getData()
			if ptr != None:
				self['fsklogo'].instance.setPixmap(ptr)
				self['fsklogo'].show()
		del self.picload

			
	def ok(self):
		self.keyGreen()
		
	def keyBlue(self):
		self.session.open(tmdbConfigScreen)

	def keyYellow(self):
		if not self.movie:
			self.session.open(tmdbScreenSeason, self.mname, self.id, self.media)

	def keyGreen(self):
		self.session.open(tmdbScreenPeople, self.mname, self.id, self.media)

	def cancel(self):
		self.close(True)

	def writeTofile(self):
		if not self.saveFilename == "":
			self.session.openWithCallback(self.createTXT, MessageBox, _("Write TMDb Information?"), MessageBox.TYPE_YESNO, default=False)
			
	def createTXT(self, result):
		if result:
			wFile = open(self.saveFilename+".txt","w") 
			wFile.write(self.text) 
			wFile.close()
			print("[TMDb] %s.txt created" % (self.saveFilename))
			self.session.open(MessageBox, _("TMDb information created!"), type=1, timeout=5)
			self.session.openWithCallback(self.deleteEIT, MessageBox, _("Delete EIT file?"), MessageBox.TYPE_YESNO, default=False)

	def deleteEIT(self, result):
		if result:
			eitFile = cleanEnd(self.saveFilename)+".eit"
			container = eConsoleAppContainer()
			container.execute("rm -rf '%s'" % eitFile)
			print("[TMDb] %s deleted" % (eitFile))
			self.session.open(MessageBox, _("EIT file deleted!"), type=1, timeout=5)

class tmdbScreenPeople(Screen, HelpableScreen):
	skin = """
		<screen position="40,80" size="1200,600" title="TMDb - The Movie Database" >
			<widget name="searchinfo" zPosition="10" position="20,10" size="1180,40" font="Regular;24" foregroundColor="#00fff000"/>
			<widget name="list" position="10,60" size="600,240" scrollbarMode="showOnDemand"/>
			<widget name="cover" position="640,60" size="160,240" alphatest="blend"/>
			<widget name="data" position="10,310" size="1180,250" font="Regular;21" />
			<widget name="key_red" position="100,570" size="260,25" font="Regular;20" transparent="1"/>
			<widget name="key_green" position="395,570" size="260,25" font="Regular;20" transparent="1"/>
			<widget name="key_blue" position="985,570" size="260,25" font="Regular;20" transparent="1"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""	

	def __init__(self, session, mname, id, media):
		Screen.__init__(self, session)
		self.session = session
		self.mname = mname
		self.id = id
		self.media = media
		if self.media == "movie":
			self.movie = True
		else:
			self.movie = False
		
		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self,"TMDbActions",
			{
				"ok": (self.ok, _("Show details")),
				"cancel": (self.cancel,_("Exit")),
				"up": (self.keyUp, _("Selection up")),
				"down": (self.keyDown, _("Selection down")),
				"up": (self.keyUp, _("Selection up")),
				"nextBouquet": (self.chDown, _("Details down")),
				"prevBouquet": (self.chUp, _("Details up")),
				"right": (self.keyRight, _("Page down")),
				"left": (self.keyLeft, _("Page down")),
				"red": (self.cancel, _("Exit")),
				"green": (self.ok, _("Show details")),
				"blue": (self.keyBlue, _("Setup")),
				"menu": (self.keyBlue, _("Setup"))
			}, -1)	

		self['searchinfo'] = Label(_("Loading..."))
		self['data'] = ScrollLabel("...")
		self['key_red'] = Label(_("Exit"))
		self['key_green'] = Label(_("Details"))
		self['key_blue'] = Label(_("Setup"))
		self['list'] = createList(0)
		
		self['cover'] = Pixmap()
		
		self.tempDir = "/var/volatile/tmp/"
		self.onLayoutFinish.append(self.onFinish)
		
	def onFinish(self):
		# TMDb read
		print("[TMDb] Selected: %s" % self.mname)
		self['searchinfo'].setText("%s" % self.mname)	
		self.tmdbSearch()
			
	def tmdbSearch(self):
		self.lang = config.plugins.tmdb.lang.value
		self['searchinfo'].setText("%s" % self.mname)
		res = []
		try:
			if self.movie:
				json_data_cast = tmdb.Movies(self.id).credits(language=self.lang)
				#print json_data_cast
			else:
				json_data_cast = tmdb.TV(self.id).credits(language=self.lang)
				#print json_data_cast

			for casts in json_data_cast['cast']:
				id = str(casts['id'])
				title = str(casts['name']) + " (" + str(casts['character']) + ")"
				coverPath = str(casts['profile_path'])
				cover = self.tempDir+id+".jpg"
				url_cover = "http://image.tmdb.org/t/p/%s/%s" % (config.plugins.tmdb.themoviedb_coversize.value, coverPath)
				
				if not id == "" or not title =="":
					res.append(((title, url_cover, "", id),))
			
			self['list'].setList(res)
			self.piclist = res
			self.getInfo()
		except:
			self['searchinfo'].setText(_("TMDb: No results found, or does not respond!"))
			
	def getInfo(self):
		self['data'].setText("...")
		url_cover = self['list'].getCurrent()[1]
		id = self['list'].getCurrent()[3]
		
		if url_cover[-4:] == "None":
			self.showCover("/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/no_cover.png")
		else:
			if not fileExists(self.tempDir+id+".jpg"):
				downloadPage(six.ensure_binary(url_cover), self.tempDir+id+".jpg").addCallback(self.getData, self.tempDir+id+".jpg").addErrback(self.dataError)
			else:
				self.showCover(self.tempDir+id+".jpg")
		
	def getData(self, data, coverSaved):
		self.showCover(coverSaved)

	def dataError(self, error):
		print("[TMDb] Error: %s" % error)

	def baseName(self, str):
		name = str.split('/')[-1]
		return name
			
	def showCover(self, coverName):
		self.picload = ePicLoad()
		if not fileExists(coverName):
			coverName = "/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/no_cover.png"

		if fileExists(coverName):
			self['cover'].instance.setPixmap(gPixmapPtr())
			scale = AVSwitch().getFramebufferScale()
			size = self['cover'].instance.size()
			self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, ""))
			if self.picload.startDecode(coverName, 0, 0, False) == 0:
				ptr = self.picload.getData()
				if ptr != None:
					self['cover'].instance.setPixmap(ptr)
					self['cover'].show()
			del self.picload

	def ok(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		id = self['list'].getCurrent()[3]
		
		json_data_person = tmdb.People(id).info(language=self.lang)
		#print json_data_person
		
		## Personal data
		birthday = ""
		try:
			birthday = str(json_data_person['birthday'])
		except:
			birthday = ""

		birthplace = ""
		try:
			birthplace = str(json_data_person['place_of_birth'])
		except:
			birthplace = ""
		
		biography = ""
		try:
			biography = str(json_data_person['biography'])
			if biography =="":
				json_data_person = tmdb.People(id).info()
				biography = str(json_data_person['biography'])
		except:
			biography = ""

		data = birthday + " " + birthplace + "\n\n" + biography
		self['data'].setText(data)
			
	def keyLeft(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].pageUp()
		self.getInfo()

	def keyRight(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].pageDown()
		self.getInfo()
		
	def keyDown(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].down()
		self.getInfo()

	def keyUp(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].up()
		self.getInfo()
	
	def chDown(self):
		self['data'].pageUp()
	
	def chUp(self):
		self['data'].pageDown()

	def keyBlue(self):
		self.session.open(tmdbConfigScreen)
		
	def cancel(self):
		self.delCover()
		self.close()

	def delCover(self):
		list = self.piclist
		if list == None:
			return		
		count=0
		while count<len(list):
			id = list[count][0][3]
			try:
				os.remove(self.tempDir+id+".jpg")
			except:
				pass
			count+=1
			
class tmdbScreenSeason(Screen, HelpableScreen):
	skin = """
		<screen position="40,80" size="1200,600" title="TMDb - The Movie Database" >
			<widget name="searchinfo" zPosition="10" position="20,10" size="1180,40" font="Regular;24" foregroundColor="#00fff000"/>
			<widget name="list" position="10,60" size="480,240" scrollbarMode="showOnDemand"/>
			<widget name="cover" position="550,60" size="530,300" zPosition="10" alphatest="blend"/>
			<widget name="data" position="10,310" size="1180,250" font="Regular;21" />
			<widget name="key_red" position="100,570" size="260,25" font="Regular;20" transparent="1"/>
			<widget name="key_green" position="395,570" size="260,25" font="Regular;20" transparent="1"/>
			<widget name="key_blue" position="985,570" size="260,25" font="Regular;20" transparent="1"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""	
	def __init__(self, session, mname, id, media):
		Screen.__init__(self, session)
		#self.skinName = [ "tmdbScreenSeason", "tmdbScreenPeople" ]
		self.session = session
		self.mname = mname
		self.id = id
		self.media = media
		if self.media == "movie":
			self.movie = True
		else:
			self.movie = False
		self.piclist = ""
		
		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self,"TMDbActions",
			{
				"ok": (self.ok, _("Show details")),
				"cancel": (self.cancel,_("Exit")),
				"up": (self.keyUp, _("Selection up")),
				"down": (self.keyDown, _("Selection down")),
				"up": (self.keyUp, _("Selection up")),
				"nextBouquet": (self.chDown, _("Details down")),
				"prevBouquet": (self.chUp, _("Details up")),
				"right": (self.keyRight, _("Page down")),
				"left": (self.keyLeft, _("Page down")),
				"red": (self.cancel, _("Exit")),
				"green": (self.ok, _(" ")),
				"blue": (self.keyBlue, _("Setup")),
				"menu": (self.keyBlue, _("Setup"))
			}, -1)	

		self['searchinfo'] = Label(_("Loading..."))
		self['data'] = ScrollLabel("...")
		self['key_red'] = Label(_("Exit"))
		self['key_green'] = Label(_(" "))
		self['key_blue'] = Label(_("Setup"))
		self['list'] = createList(0)
		
		self['cover'] = Pixmap()
		
		self.tempDir = "/var/volatile/tmp/"
		self.onLayoutFinish.append(self.onFinish)
		
	def onFinish(self):
		# TMDb read
		print("[TMDb] Selected: %s" % self.mname)
		self['searchinfo'].setText("%s" % self.mname)	
		self.tmdbSearch()
			
	def tmdbSearch(self):
		self.lang = config.plugins.tmdb.lang.value
		self['searchinfo'].setText("%s" % self.mname)
		res = []
		try:		
			# Seasons
			json_data_seasons = tmdb.TV(self.id).info(language=self.lang)
			for seasons in json_data_seasons['seasons']:
				print("[TMDb] Seasons: %s" % seasons['season_number'])
				id = str(seasons['id'])
				season = seasons['season_number']
				
				#Episodes
				json_data_episodes = tmdb.TV_Seasons(self.id, season).info(language=self.lang)
				titledate = "("+str(json_data_episodes['air_date'])[:4]+")"
				title = str(json_data_episodes['name'])
				title = "%s %s" %(title, titledate)
				overview = str(json_data_episodes['overview'])
				coverPath = str(json_data_episodes['poster_path'])
				cover = self.tempDir+id+".jpg"
				url_cover = "http://image.tmdb.org/t/p/%s/%s" % (config.plugins.tmdb.themoviedb_coversize.value, coverPath)
				if not id == "" or not title =="":
					res.append(((title, url_cover, overview, id),))

				for names in json_data_episodes['episodes']:
					id = str(names['id'])
					title = str(names['episode_number'])
					name = str(names['name'])
					title = "%+6s %s" %(title,name)
					overview = str(names['overview'])
					coverPath = str(names['still_path'])
					cover = self.tempDir+id+".jpg"
					url_cover = "http://image.tmdb.org/t/p/%s/%s" % (config.plugins.tmdb.themoviedb_coversize.value, coverPath)
					if not id == "" or not title =="":
						res.append(((title, url_cover, overview, id),))
			self['list'].setList(res)
			self.piclist = res
			self.getInfo()
		
		except:
			self['searchinfo'].setText(_("TMDb: No results found, or does not respond!"))
			
	def getInfo(self):
		self['data'].setText("...")
		url_cover = self['list'].getCurrent()[1]
		id = self['list'].getCurrent()[3]
		
		if url_cover[-4:] == "None":
			self.showCover("/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/no_cover.png")
		else:
			if not fileExists(self.tempDir+id+".jpg"):
				downloadPage(six.ensure_binary(url_cover), self.tempDir+id+".jpg").addCallback(self.getData, self.tempDir+id+".jpg").addErrback(self.dataError)
			else:
				self.showCover(self.tempDir+id+".jpg")
		
	def getData(self, data, coverSaved):
		self.showCover(coverSaved)

	def dataError(self, error):
		print("[TMDb] Error: %s" % error)

	def baseName(self, str):
		name = str.split('/')[-1]
		return name
			
	def showCover(self, coverName):
		self.picload = ePicLoad()
		if not fileExists(coverName):
			coverName = "/usr/lib/enigma2/python/Plugins/Extensions/tmdb/pic/no_cover.png"

		if fileExists(coverName):
			self['cover'].instance.setPixmap(gPixmapPtr())
			scale = AVSwitch().getFramebufferScale()
			size = self['cover'].instance.size()
			self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, ""))
			if self.picload.startDecode(coverName, 0, 0, False) == 0:
				ptr = self.picload.getData()
				if ptr != None:
					self['cover'].instance.setPixmap(ptr)
					self['cover'].show()
			del self.picload
		self.ok() # Shortcut
		
	def ok(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		data = self['list'].getCurrent()[2]
		self['data'].setText(data)
			
	def keyLeft(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].pageUp()
		self.getInfo()

	def keyRight(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].pageDown()
		self.getInfo()
		
	def keyDown(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].down()
		self.getInfo()

	def keyUp(self):
		check = self['list'].getCurrent()
		if check == None:
			return
		self['list'].up()
		self.getInfo()
	
	def chDown(self):
		self['data'].pageUp()
	
	def chUp(self):
		self['data'].pageDown()

	def keyBlue(self):
		self.session.open(tmdbConfigScreen)
		
	def cancel(self):
		self.delCover()
		self.close()

	def delCover(self):
		list = self.piclist
		if list == None:
			return		
		count=0
		while count<len(list):
			id = list[count][0][3]
			try:
				os.remove(self.tempDir+id+".jpg")
			except:
				pass
			count+=1

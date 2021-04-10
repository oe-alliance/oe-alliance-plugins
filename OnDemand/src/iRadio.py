"""
	iRadio Player - Enigma2 Radio Plugin
	Copyright (C) 2013 mcquaim

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# for localized messages
from . import _

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from enigma import eServiceReference, eTimer, getDesktop, ePicLoad
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk
from twisted.web import client
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigDirectory, ConfigYesNo, Config, ConfigInteger, ConfigSubList, ConfigText, getConfigListEntry, configfile
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
import NavigationInstance

import time
import random
from time import strftime, strptime, mktime
from datetime import timedelta, date, datetime

import urllib
import urllib2
import re
from urllib import quote

import xml.etree.cElementTree as ET

from CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler, StreamsThumbCommon

#----------------------------------------------------------------------------------------------------------------------------------------#
# The Dev ID for calling the API
devid = 'fa1jo93O_raeF0v9'

# The location of the favourites file
FAVORITE_FILE = '/etc/enigma2/iRadio.favorites'

#----------------------------------------------------------------------------------------------------------------------------------------#

def wgetUrl(target):
	try:
		req = urllib2.Request(target)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		outtxt = str(response.read())
		response.close()
		return outtxt
	except (Exception) as exception:
		print 'wgetUrl: Error retrieving URL ', exception
		return ''

#----------------------------------------------------------------------------------------------------------------------------------------#

def urlType(target):
	try:
		res = urllib.urlopen(target)
		http_message = res.info()
		full = http_message.type
		main = http_message.maintype
		
		return full
 
	except (Exception) as exception:
		print 'urlType: Error retrieving URL Type ', exception
		return ''

#----------------------------------------------------------------------------------------------------------------------------------------#

class iRadioMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="" >
			<widget name="iRadioMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("iRadio Player - Main Menu"))

		self.imagedir = '/tmp/onDemandImg/'

		self.action = action
		self.value = value
		osdList = []
		if self.action is "start":
			osdList.append((_("Favorites"), "favourites", "none"))
			osdList.append((_("SHOUTcast Radio"), "shoutcast", "http://api.shoutcast.com/genre/primary?k=%s&f=xml"))
			osdList.append((_("Tunein Radio"), "tunein", "http://opml.radiotime.com/"))
			osdList.append((_("Back"), "exit", "none"))

		self["iRadioMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)	  

	def go(self):
		name = self["iRadioMenu"].l.getCurrentSelection()[0]
		id = self["iRadioMenu"].l.getCurrentSelection()[1]
		url = self["iRadioMenu"].l.getCurrentSelection()[2]
		
		if id == "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
		elif self.action == "start":
			if id == 'favourites':
				self.session.open(FavoritesThumb, id, name, name)
			elif id == 'shoutcast':
				self.session.open(shoutGenresMenu, id, name, url)
			else:
				self.session.open(tuneinGenresMenu, id, name, url)

	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)		

	def removeFiles(self, targetdir):
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))

#----------------------------------------------------------------------------------------------------------------------------------------#

class shoutGenresMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" >
			<widget name="shoutGenresMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value, url):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("iRadio Player - SHOUTcast Genres"))

		self.action = action
		self.value = value
		self.genreurl = url % (devid)
		osdList = []

		osdList.append((_("Search"), "search", "false"))
		
		# Read the URL for the selected category on the Main Menu.
		try:
			# Read the Genre List from Shoutcast.
			xml = wgetUrl(self.genreurl)

			# Make sure data is returned.
			if xml:
				# Parse the XML with elementTree
				tree = ET.fromstring(xml)

				# Find the first element <genre>
				for elem in tree.iter('genre'):
					# Iterate through the elements
					name = str(elem.get('name'))
					id = str(elem.get('id'))
					children = str(elem.get('haschildren'))
					osdList.append((_(name), id, children))

		except (Exception) as exception:
			print 'iRadioMenu: Error parsing genres: ', exception											

		osdList.append((_("Exit"), "exit", "false"))

		self["shoutGenresMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1) 

	def go(self):
		name = self["shoutGenresMenu"].l.getCurrentSelection()[0]
		id = self["shoutGenresMenu"].l.getCurrentSelection()[1]
		children = self["shoutGenresMenu"].l.getCurrentSelection()[2]
		

		if id is not None:
			if id == "exit":
				self.close(None)
			elif children == "true":
				self.session.open(shoutSubGenresMenu, id, name, id)
			else:
				self.session.open(shoutGenresThumb, id, name, name)

	def cancel(self):
		self.close(None)

#----------------------------------------------------------------------------------------------------------------------------------------#

class shoutSubGenresMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" >
			<widget name="shoutSubGenresMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value, url):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("iRadio Player - SHOUTcast Sub Genres for " +value))

		self.action = action
		self.value = value
		self.subgenre = 'http://api.shoutcast.com/genre/secondary?id=%s&f=xml&k=%s' % (url, devid)
		osdList = []

		# Read the URL for the selected category on the Main Menu.
		try:
			# Read the URL for the selected genre on the Main Menu.
			xml = wgetUrl(self.subgenre)

			# Make sure data is returned.
			if xml:
				# Parse the XML with elementTree
				tree = ET.fromstring(xml)

				# Find the first element <genre>
				for elem in tree.iter('genre'):
					# Iterate through the elements
					parentid = str(elem.get('parentid'))
					if parentid == '0':
						name = str(elem.get('name'))+ " All"
						id = str(elem.get('id'))
						children = "false"
					else:
						name = str(elem.get('name'))
						id = str(elem.get('id'))
						children = str(elem.get('haschildren'))

					osdList.append((_(name), id, children))

		except (Exception) as exception:
			print 'shoutSubGenresMenu: Error parsing feed: ', exception											

		osdList.append((_("Exit"), "exit", "false"))

		self["shoutSubGenresMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1) 

	def go(self):
		name = self["shoutSubGenresMenu"].l.getCurrentSelection()[0]
		id = self["shoutSubGenresMenu"].l.getCurrentSelection()[1]
		children = self["shoutSubGenresMenu"].l.getCurrentSelection()[2]
		

		if id is not None:
			if id == "exit":
				self.close(None)
			elif children == "true":
				self.session.open(shoutSubGenresMenu, id, name, id)
			else:
				self.session.open(shoutGenresThumb, id, name, name)

	def cancel(self):
		self.close(None)

#----------------------------------------------------------------------------------------------------------------------------------------#

class tuneinGenresMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" >
			<widget name="tuneinGenresMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value, url):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("iRadio Player - Tunein Main Menu"))

		self.action = action
		self.value = value
		self.genreurl = url
		osdList = []

		osdList.append((_("Search"), "search", "false"))
		
		# Read the URL for the selected category on the Main Menu.
		try:
			# Read the Genre List from Shoutcast.
			xml = wgetUrl(self.genreurl)

			# Parse the XML with elementTree
			tree = ET.fromstring(xml)

			# Find the first element <outline>
			for elem in tree.iter('outline'):
				# Iterate through the elements
				name_tmp = str(elem.get('text'))
				name_split = name_tmp.rsplit('(',1)
				name = tidyString(name_split[0])
				id = str(elem.get('URL'))
				osdList.append((_(name), id, "false"))

		except (Exception) as exception:
			print 'tuneinGenresMenu: Error parsing genres: ', exception											

		osdList.append((_("Exit"), "exit", "false"))

		self["tuneinGenresMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1) 

	def go(self):
		name = self["tuneinGenresMenu"].l.getCurrentSelection()[0]
		id = self["tuneinGenresMenu"].l.getCurrentSelection()[1]
		

		if id != 'None':
			if id == "exit":
				self.close(None)
			else:
				self.session.open(tuneinGenresThumb, id, name, id)

	def cancel(self):
		self.close(None)

#----------------------------------------------------------------------------------------------------------------------------------------#

def findPlayUrl(showID, function, showWMA, **kwargs):
	# Take the accepted showID and append it onto the url below.
	url = showID
	print 'findPlayUrl: url: ', url
	fileUrl = ''

	try:
		html = wgetUrl(url)
		print 'findPlayUrl: html: ', html

		# If zero, an error occurred retrieving the url, pass empty string back
		if html:
			if function == 'tunein':
				stream = html.strip()
				if stream[-3:] == "mp3":
					fileUrl = stream
				else:
					urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', html)

					for link in urls:
						# Find out What type of URL we are dealing with.
						fileType = urlType(link)

						# This is an M3U URL containing Stream URL's
						if fileType == 'audio/x-mpegurl':
							result = wgetUrl(link)
							if result != '':
								stream = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', result)
								fileUrl = stream[0]
								break

						# This is an PLS URL containing Stream URL's
						elif fileType == 'audio/x-scpls':
							result = wgetUrl(link)
							if html != '':
								stream = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', result)
								fileUrl = stream[0]
								break

						# This is an ASX URL for playing Windows media.
						elif "asx" in link:
							if showWMA == 'False':
								print 'findPlayUrl: passing on asx file: ', link
								pass
							else:
								fileUrl = link

						# This is an actual Audio Stream so pass it back.
						elif fileType == 'audio/mpeg':
							fileUrl = link
							break
						
						# This is a HTML page that can be returned from the stream
						elif fileType == 'text/plain':
							result = wgetUrl(link)
							if "<HTML><HEAD>" in result:
								fileUrl = link
							else:
								pass

				print 'findPlayUrl: fileUrl: ', fileUrl
				return fileUrl
			else:
				stream = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', html)

				fileUrl = stream[0]
				print 'findPlayUrl: fileUrl: ', fileUrl
				return fileUrl
		else:
			print 'findPlayUrl: HTML is blank fileUrl: ', fileUrl
			return ""
	except (Exception) as exception:
		print 'findPlayUrl: Problem rerieving URL: ', exception
		return ""

#----------------------------------------------------------------------------------------------------------------------------------------#

def checkUnicode(value, **kwargs):
	stringValue = value 
	stringValue = stringValue.replace('&#39;', '\'')
	stringValue = stringValue.replace('&amp;', '&')
	return stringValue

#----------------------------------------------------------------------------------------------------------------------------------------#

def tidyString(value, **kwargs):
	stringValue = value 
	stringValue = stringValue.replace('(', '')
	stringValue = stringValue.replace(')', '')
	stringValue = stringValue.replace('|', '')
	stringValue = stringValue.strip()
	return stringValue

#----------------------------------------------------------------------------------------------------------------------------------------#

def main(session, **kwargs):
	action = "start"
	value = 0 
	start = session.open(iRadioMenu, action, value)

#----------------------------------------------------------------------------------------------------------------------------------------#

class shoutGenresThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = 'Extensions/OnDemand/icons/SHOUTcast.png'
		
		self.showWMA = str(config.ondemand.ShowiRadioWMA.value)
		self.showDefault = str(config.ondemand.ShowShoutcastDefault.value)
		self.showIcon = str(config.ondemand.ShowShoutcastLogos.value)

		if self.showIcon == 'True':		
			if self.showDefault == 'False':
				self.defaultImg = ''

		self.favoriteConfig = Config()
		if os_path.exists(FAVORITE_FILE):
			self.favoriteConfig.loadFromFile(FAVORITE_FILE)

		self.favoriteConfig.entriescount = ConfigInteger(0)
		self.favoriteConfig.Entries = ConfigSubList()
		self.initFavoriteConfig()

		self.screenName = "ShoutStreamsThumbCommon"
		StreamsThumbCommon.__init__(self, session, action, value, url, self.screenName)

		self.skin = """
				<screen position="0,0" size="e,e" flags="wfNoBorder" >
					<widget name="lab1" position="0,0" size="e,e" font="Regular;24" halign="center" valign="center" transparent="0" zPosition="5" />
					<widget source="Title" render="Label" position="20,0" size="e,50" font="Regular;32" />
					<widget name="list" position="0,50" size="e,e-50" scrollbarMode="showOnDemand" transparent="1" />
					<ePixmap pixmap="ViX-Common/buttons/green.png" position="800,10" size="40,40" transparent="1" alphatest="on" />
					<widget source="key_green" render="Label" position="810,0" zPosition="1" size="200,40" font="Regular;20" valign="center" halign="center" transparent="1" />
				</screen>"""

		self["key_green"] = StaticText(_("Add to Favorites"))
		
		self["genreActions"] = ActionMap(["ColorActions"],
		{
			"red": self.red_pressed,
			"green": self.green_pressed,
			"yellow": self.yellow_pressed,
			"blue": self.blue_pressed,
		
		}, -1)

	def layoutFinished(self):
		self.setTitle("SHOUTcast Radio Player: Listings for " +self.title)

#----------------------------------------------------------------------------------------------------------------------------------------#

	def red_pressed(self):
		pass

	def green_pressed(self):
		date1 = self["list"].l.getCurrentSelection()[0]
		name = self["list"].l.getCurrentSelection()[1]
		short = self["list"].l.getCurrentSelection()[2]
		channel = self["list"].l.getCurrentSelection()[3]
		stream = self["list"].l.getCurrentSelection()[4]
		icon = self["list"].l.getCurrentSelection()[5]
		duration = self["list"].l.getCurrentSelection()[6]
		exists = 'False'

		if stream is not None:
			for item in self.favoriteConfig.Entries:
				if str(item.text.value) == str(stream):
					exists = 'True'

			if exists == 'False':
				result = self.addFavorite(name=name, text=stream, favoritetype='shoutcast', audio=duration, bitrate=date1, icon=icon)
				if result == 0:
					self.session.open(MessageBox, _('Station saved to Favorites!'), type=MessageBox.TYPE_INFO, timeout=3)
				else:
					self.session.open(MessageBox, _('Station save failed, please check the Debug logs!'), type=MessageBox.TYPE_INFO, timeout=3)
			else:
				self.session.open(MessageBox, _('Station Already Saved in Favorites!'), type=MessageBox.TYPE_INFO, timeout=3)
				pass
		else:
			self.session.open(MessageBox, _('Selection does not contain a stream!'), type=MessageBox.TYPE_INFO, timeout=3)
			pass

	def yellow_pressed(self):
		pass

	def blue_pressed(self):
		pass

#----------------------------------------------------------------------------------------------------------------------------------------#

	def addFavorite(self, name='', text='', favoritetype='', audio='', bitrate='', icon=''):
		try:
			self.favoriteConfig.entriescount.value = self.favoriteConfig.entriescount.value + 1
			self.favoriteConfig.entriescount.save()
			newFavorite = self.initFavoriteEntryConfig()
			newFavorite.name.value = name
			newFavorite.text.value = text
			newFavorite.type.value = favoritetype
			newFavorite.audio.value = audio
			newFavorite.bitrate.value = bitrate
			newFavorite.icon.value = icon
			newFavorite.save()
			self.favoriteConfig.saveToFile(FAVORITE_FILE)
			return 0
		except (Exception) as exception:
			print 'addFavorite: Error saving to Favorites: ', exception
			return -1

	def getFavoriteList(self):
		self.getFavMediaData(self.mediaList, self.url)
		if len(self.mediaList) == 0:
			self.mediaProblemPopup("No Stations Found!")
		self.updateMenu()

	def initFavoriteEntryConfig(self):
		self.favoriteConfig.Entries.append(ConfigSubsection())
		i = len(self.favoriteConfig.Entries) - 1
		self.favoriteConfig.Entries[i].name = ConfigText(default='')
		self.favoriteConfig.Entries[i].text = ConfigText(default='')
		self.favoriteConfig.Entries[i].type = ConfigText(default='')
		self.favoriteConfig.Entries[i].audio = ConfigText(default='')
		self.favoriteConfig.Entries[i].bitrate = ConfigText(default='')
		self.favoriteConfig.Entries[i].icon = ConfigText(default='')
		return self.favoriteConfig.Entries[i]

	def initFavoriteConfig(self):
		count = self.favoriteConfig.entriescount.value
		if count != 0:
			i = 0
			while i < count:
				self.initFavoriteEntryConfig()
				i += 1

#----------------------------------------------------------------------------------------------------------------------------------------#

	def setupCallback(self, retval=None):
		if retval == 'cancel' or retval is None:
			return
			
		elif retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

		else:
			genresearch = self.url.replace(' All', '')
			genresearch = genresearch.replace(' ', '+')
			stationurl = 'http://api.shoutcast.com/legacy/genresearch?k=%s&genre=%s' % (devid, genresearch)
			
			self.getShoutcastMediaData(self.mediaList, stationurl)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Stations Found!")
			self.updateMenu()

	def keyboardCallback(self, callback=None):
		if callback is not None and len(callback):
			self.setTitle("SHOUTcast Radio Player: Search Listings for " +callback)
			
			genresearch = callback.replace(' ', '+')
			searchurl = 'http://api.shoutcast.com/legacy/stationsearch?k=%s&search=%s' % (devid, str(genresearch))
			
			self.getShoutcastMediaData(self.mediaList, searchurl)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_INFO, timeout=5, simple=True)
		else:
			self.close()

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]

		if showID:
			fileUrl = findPlayUrl(showID, 'shoutcast', self.showWMA)
			
			if fileUrl:
				fileRef = eServiceReference(4097,0,fileUrl)
				fileRef.setName(showName)
				lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
				self.session.open(MoviePlayer, fileRef, None, lastservice)
			else:
				self.session.open(MessageBox, _('Sorry, unable to find playable stream!'), type=MessageBox.TYPE_INFO, timeout=5)

#----------------------------------------------------------------------------------------------------------------------------------------#

	def getShoutcastMediaData(self, weekList, url):

		plsurl = 'http://yp.shoutcast.com/sbin/tunein-station.pls?id='
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''

		try:
			# Read the URL for the selected genre on the Main Menu.
			xml = wgetUrl(url)

			# Make sure reading the URL returned data.
			if xml:
				# Parse the XML with elementTree
				tree = ET.fromstring(xml)

				# Find the first element <station>
				for elem in tree.iter('station'):
					# Iterate through the elements
					name_tmp = str(elem.get('name'))
					name = checkUnicode(name_tmp)
					id = str(elem.get('id'))
					stream = plsurl+id
					short_tmp = str(elem.get('ct'))
					genre = str(elem.get('genre'))
					bitrate = str(elem.get('br'))
					audio = str(elem.get('mt'))
					
					if genre != 'None':
						short = _("Recently Played: ")+checkUnicode(short_tmp)+_("\n\nGenre: ")+genre
					else:
						short = _("Recently Played: ")+checkUnicode(short_tmp)

					if bitrate != 'None':
						date1 = _("Bitrate: ")+bitrate+" kbps"
					else:
						date1 = _("Bitrate: Unknown")
					
					if audio != 'None':
						duration = _("Audio: ")+audio
					else:
						duration = _("Audio: Unknown")

					weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print 'getShoutcastMediaData: Error getting Media info: ', exception

#----------------------------------------------------------------------------------------------------------------------------------------#

class FavoritesThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = 'Extensions/OnDemand/icons/favorite.png'
		
		self.showWMA = str(config.ondemand.ShowiRadioWMA.value)
		self.showDefault = str(config.ondemand.ShowFavoriteDefault.value)
		self.showIcon = str(config.ondemand.ShowFavoriteLogos.value)

		if self.showIcon == 'True':		
			if self.showDefault == 'False':
				self.defaultImg = ''

		self.favoriteConfig = Config()
		if os_path.exists(FAVORITE_FILE):
			self.favoriteConfig.loadFromFile(FAVORITE_FILE)

		self.favoriteConfig.entriescount = ConfigInteger(0)
		self.favoriteConfig.Entries = ConfigSubList()
		self.initFavoriteConfig()

		self.screenName = "RadioFavStreamsThumbCommon"
		StreamsThumbCommon.__init__(self, session, action, value, url, self.screenName)

		self.skin = """
				<screen position="0,0" size="e,e" flags="wfNoBorder" >
					<widget name="lab1" position="0,0" size="e,e" font="Regular;24" halign="center" valign="center" transparent="0" zPosition="5" />
					<widget source="Title" render="Label" position="20,0" size="e,50" font="Regular;32" />
					<widget name="list" position="0,50" size="e,e-50" scrollbarMode="showOnDemand" transparent="1" />
					<ePixmap pixmap="ViX-Common/buttons/yellow.png" position="800,10" size="40,40" transparent="1" alphatest="on" />
					<widget source="key_yellow" render="Label" position="810,0" zPosition="1" size="250,40" font="Regular;20" valign="center" halign="center" transparent="1" />
				</screen>"""

		self["key_yellow"] = StaticText(_("Delete from Favorites"))
		
		self["favActions"] = ActionMap(["ColorActions"],
		{
			"red": self.red_pressed,
			"green": self.green_pressed,
			"yellow": self.yellow_pressed,
			"blue": self.blue_pressed,
		
		}, -1)

	def layoutFinished(self):
		self.setTitle("iRadio Player: Favorite Listings")

#----------------------------------------------------------------------------------------------------------------------------------------#

	def red_pressed(self):
		pass

	def green_pressed(self):
		pass

	def yellow_pressed(self):
		result = self.removeFavorite()

		if result == 0:
			self.session.open(MessageBox, _('Station deleted from Favorites!'), type=MessageBox.TYPE_INFO, timeout=3)
		else:
			self.session.open(MessageBox, _('Station delete failed, please check the Debug logs!'), type=MessageBox.TYPE_INFO, timeout=3)

	def blue_pressed(self):
		pass

#----------------------------------------------------------------------------------------------------------------------------------------#

	def removeFavorite(self):
		try:
			selFav = self["list"].l.getCurrentSelection()[4]
			if selFav is not None:
				self.favoriteConfig.entriescount.value = self.favoriteConfig.entriescount.value - 1
				self.favoriteConfig.entriescount.save()
				
				for item in self.favoriteConfig.Entries:
					if str(item.text.value) == str(selFav):
						self.favoriteConfig.Entries.remove(item)

				self.favoriteConfig.Entries.save()
				self.favoriteConfig.saveToFile(FAVORITE_FILE)
				self.favoriteListIndex = 0
				self.mediaList = []
				self.getFavoriteList()
				return 0
		except (Exception) as exception:
			print 'removeFavorite: Error deleting Favorite: ', exception
			return -1

	def getFavoriteList(self):
		self.getFavMediaData(self.mediaList, self.url)
		if len(self.mediaList) == 0:
			self.mediaProblemPopup("No Stations Found!")
		self.updateMenu()

	def initFavoriteEntryConfig(self):
		self.favoriteConfig.Entries.append(ConfigSubsection())
		i = len(self.favoriteConfig.Entries) - 1
		self.favoriteConfig.Entries[i].name = ConfigText(default='')
		self.favoriteConfig.Entries[i].text = ConfigText(default='')
		self.favoriteConfig.Entries[i].type = ConfigText(default='')
		self.favoriteConfig.Entries[i].audio = ConfigText(default='')
		self.favoriteConfig.Entries[i].bitrate = ConfigText(default='')
		self.favoriteConfig.Entries[i].icon = ConfigText(default='')
		return self.favoriteConfig.Entries[i]

	def initFavoriteConfig(self):
		count = self.favoriteConfig.entriescount.value
		if count != 0:
			i = 0
			while i < count:
				self.initFavoriteEntryConfig()
				i += 1

#----------------------------------------------------------------------------------------------------------------------------------------#

	def setupCallback(self, retval=None):
		if retval == 'cancel' or retval is None:
			return
		else:
			self.getFavoriteList()

	def go(self):
		stationID = self["list"].l.getCurrentSelection()[4]
		stationName = self["list"].l.getCurrentSelection()[1]
		favType = self["list"].l.getCurrentSelection()[3]

		if stationID:
			if favType == 'manual':
				fileUrl = stationID
			elif favType == 'tunein':
				fileUrl = findPlayUrl(stationID, 'tunein', self.showWMA)
			else:
				fileUrl = findPlayUrl(stationID, 'favourite', self.showWMA)
			
			if fileUrl:
				fileRef = eServiceReference(4097,0,fileUrl)
				fileRef.setName(stationName)
				lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
				self.session.open(MoviePlayer, fileRef, None, lastservice)
			else:
				self.session.open(MessageBox, _('Sorry, unable to find playable stream!'), type=MessageBox.TYPE_INFO, timeout=5)

#----------------------------------------------------------------------------------------------------------------------------------------#

	def getFavMediaData(self, weekList, genre):
		
		shoutIcon = 'http://977music.com/images/uploads/pages/SHOUTcast_yellow.jpg'
		tuneIcon = 'http://www.ipadmaniac.com/wp-content/uploads/2011/06/TuneIn-Radio-Logo.png'
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''

		try:
			for item in self.favoriteConfig.Entries:
            			# Iterate through the elements
				date1 = str(item.bitrate.value)
				name_tmp = str(item.name.value)
				name = checkUnicode(name_tmp)
				short = str(item.text.value)
				channel = str(item.type.value)
				stream = str(item.text.value)
				duration = str(item.audio.value)
				
				# Show the logo for the Favorite source.
				if self.showIcon == 'True':
					icon = str(item.icon.value)
					if icon == '':
						if channel == 'shoutcast':
							icon = shoutIcon
						elif channel == 'tunein':
							icon = tuneIcon
				else:
					icon = ''

				weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print 'getFavMediaData: Error getting Media info: ', exception

#----------------------------------------------------------------------------------------------------------------------------------------#

class tuneinGenresThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = 'Extensions/OnDemand/icons/FolderIcon.png'
		
		self.showWMA = str(config.ondemand.ShowiRadioWMA.value)
		self.showDefault = str(config.ondemand.ShowTuneinDefault.value)
		self.showIcon = str(config.ondemand.ShowTuneinLogos.value)

		if self.showIcon == 'True':		
			if self.showDefault == 'False':
				self.defaultImg = ''
			
		self.favoriteConfig = Config()
		if os_path.exists(FAVORITE_FILE):
			self.favoriteConfig.loadFromFile(FAVORITE_FILE)

		self.favoriteConfig.entriescount = ConfigInteger(0)
		self.favoriteConfig.Entries = ConfigSubList()
		self.initFavoriteConfig()
		self.genreList = []
		self.getGenreList(self.genreList)

		self.screenName = "TuneinStreamsThumbCommon"
		StreamsThumbCommon.__init__(self, session, action, value, url, self.screenName)

		self.skin = """
				<screen position="0,0" size="e,e" flags="wfNoBorder" >
					<widget name="lab1" position="0,0" size="e,e" font="Regular;24" halign="center" valign="center" transparent="0" zPosition="5" />
					<widget source="Title" render="Label" position="20,0" size="e,50" font="Regular;32" />
					<widget name="list" position="0,50" size="e,e-50" scrollbarMode="showOnDemand" transparent="1" />
					<ePixmap pixmap="ViX-Common/buttons/green.png" position="800,10" size="40,40" transparent="1" alphatest="on" />
					<widget source="key_green" render="Label" position="810,0" zPosition="1" size="200,40" font="Regular;20" valign="center" halign="center" transparent="1" />
				</screen>"""

		self["key_green"] = StaticText(_("Add to Favorites"))
		
		self["genreActions"] = ActionMap(["ColorActions"],
		{
			"red": self.red_pressed,
			"green": self.green_pressed,
			"yellow": self.yellow_pressed,
			"blue": self.blue_pressed,
		
		}, -1)

	def layoutFinished(self):
		self.setTitle("Tunein Radio Player: Listings for " +self.title)

#----------------------------------------------------------------------------------------------------------------------------------------#

	def red_pressed(self):
		pass

	def green_pressed(self):
		date1 = self["list"].l.getCurrentSelection()[0]
		name = self["list"].l.getCurrentSelection()[1]
		short = self["list"].l.getCurrentSelection()[2]
		channel = self["list"].l.getCurrentSelection()[3]
		stream = self["list"].l.getCurrentSelection()[4]
		icon = self["list"].l.getCurrentSelection()[5]
		duration = self["list"].l.getCurrentSelection()[6]	
		exists = 'False'

		if (stream != 'None') and (channel != 'link'):
			for item in self.favoriteConfig.Entries:
				if str(item.text.value) == str(stream):
					exists = 'True'

			if exists == 'False':
				result = self.addFavorite(name=name, text=stream, favoritetype='tunein', audio=duration, bitrate=date1, icon=icon)
				if result == 0:
					self.session.open(MessageBox, _('Station saved to Favorites!'), type=MessageBox.TYPE_INFO, timeout=3)
				else:
					self.session.open(MessageBox, _('Station save failed, please check the Debug logs!'), type=MessageBox.TYPE_INFO, timeout=3)
			else:
				self.session.open(MessageBox, _('Station Already Saved in Favorites!'), type=MessageBox.TYPE_INFO, timeout=3)
				pass
		else:
			self.session.open(MessageBox, _('Selection does not contain a stream!'), type=MessageBox.TYPE_INFO, timeout=3)
			pass

	def yellow_pressed(self):
		pass

	def blue_pressed(self):
		pass

#----------------------------------------------------------------------------------------------------------------------------------------#

	def addFavorite(self, name='', text='', favoritetype='', audio='', bitrate='', icon=''):
		try:
			self.favoriteConfig.entriescount.value = self.favoriteConfig.entriescount.value + 1
			self.favoriteConfig.entriescount.save()
			newFavorite = self.initFavoriteEntryConfig()
			newFavorite.name.value = name
			newFavorite.text.value = text
			newFavorite.type.value = favoritetype
			newFavorite.audio.value = audio
			newFavorite.bitrate.value = bitrate
			newFavorite.icon.value = icon
			newFavorite.save()
			self.favoriteConfig.saveToFile(FAVORITE_FILE)
			return 0
		except (Exception) as exception:
			print 'addFavorite: Error saving to Favorites: ', exception
			return -1

	def initFavoriteEntryConfig(self):
		self.favoriteConfig.Entries.append(ConfigSubsection())
		i = len(self.favoriteConfig.Entries) - 1
		self.favoriteConfig.Entries[i].name = ConfigText(default='')
		self.favoriteConfig.Entries[i].text = ConfigText(default='')
		self.favoriteConfig.Entries[i].type = ConfigText(default='')
		self.favoriteConfig.Entries[i].audio = ConfigText(default='')
		self.favoriteConfig.Entries[i].bitrate = ConfigText(default='')
		self.favoriteConfig.Entries[i].icon = ConfigText(default='')
		return self.favoriteConfig.Entries[i]

	def initFavoriteConfig(self):
		count = self.favoriteConfig.entriescount.value
		if count != 0:
			i = 0
			while i < count:
				self.initFavoriteEntryConfig()
				i += 1

#----------------------------------------------------------------------------------------------------------------------------------------#

	def setupCallback(self, retval=None):
		if retval == 'cancel' or retval is None:
			return
		elif retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)
		else:
			self.getTuneinMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.session.open(MessageBox, _('Sorry, No Stations Found!'), type=MessageBox.TYPE_INFO, timeout=5)
			self.updateMenu()

	def keyboardCallback(self, callback=None):
		if callback is not None and len(callback):
			self.setTitle("Tunein Radio Player: Search Listings for " +callback)
			stationsearch = callback.replace(' ', '+')
			searchurl = 'http://opml.radiotime.com/Search.ashx?query=%s' % (stationsearch)
			self.getTuneinMediaData(self.mediaList, searchurl)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_INFO, timeout=5, simple=True)
		else:
			self.close()

#----------------------------------------------------------------------------------------------------------------------------------------#

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]
		children = self["list"].l.getCurrentSelection()[3]

		if children == "link":
			self.session.open(tuneinGenresThumb, showID, showName, showID)
		elif showID != 'None':
			fileUrl = findPlayUrl(showID, 'tunein', self.showWMA)
			
			if fileUrl:
				fileRef = eServiceReference(4097,0,fileUrl)
				fileRef.setName(showName)
				lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
				self.session.open(MoviePlayer, fileRef, None, lastservice)
				
				# TODO: Find out how to use this!
				#NavigationInstance.instance.playService(fileRef)
			else:
				self.session.open(MessageBox, _('Sorry, unable to find playable stream!'), type=MessageBox.TYPE_INFO, timeout=5)

#----------------------------------------------------------------------------------------------------------------------------------------#

	def getTuneinMediaData(self, weekList, url):

		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''

		try:
			# Read the URL for the selected genre on the Main Menu.
			xml = wgetUrl(url)

			# Parse the XML with elementTree
			tree = ET.fromstring(xml)

			# Find the first element <outline>
			for elem in tree.iter('outline'):
				# Iterate through the elements
				name_tmp = str(elem.get('text'))
				name_split = name_tmp.rsplit('(',1)
				name = tidyString(name_split[0])
				avail = str(elem.get('key'))
				
				if (avail != 'unavailable') and (name != 'This program is not available'):
					genreID = str(elem.get('genre_id'))
					genre = self.getGenreName(genreID)
					stream = str(elem.get('URL'))
					channel = str(elem.get('type'))
					formats = str(elem.get('formats'))

					if channel == 'link':
						date1 = 'More --->'
						short = '\nPress OK for sub items of '+name
						duration = ''
					else:
						bitrate = str(elem.get('bitrate'))
						if bitrate == 'None':
							date1 = _("Bitrate: Unknown")
						else:
							date1 = _("Bitrate: ")+bitrate+" kbps"

						short_tmp = str(elem.get('subtext'))
						if genre != 'None':
							short = _("Recently Played: ")+checkUnicode(short_tmp)+_("\n\nGenre: ")+genre
						else:
							short = _("Recently Played: ")+checkUnicode(short_tmp)

						if formats == 'None':
							duration = _("Audio: Unknown")
						else:
							duration = _("Audio: ")+formats

					if self.showIcon == 'True':
						icon = str(elem.get('image'))
						if icon == 'None':
							icon = ''
					else:
						icon = ''

					if (channel != 'None'):
						if (self.showWMA == 'False' and formats =='wma'):
							print 'getTuneinMediaData: Not showing WMA: showWMA: ', self.showWMA
							pass
						else:
							weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print 'getTuneinMediaData: Error getting Media info: ', exception

#----------------------------------------------------------------------------------------------------------------------------------------#

	def getGenreList(self, genreList):
		url = 'http://opml.radiotime.com/Describe.ashx?c=genres'
		# Read the URL for the selected category on the Main Menu.
		try:
			# Read the Genre List from Shoutcast.
			xml = wgetUrl(url)

			# Make sure data is returned before attempting to parse.
			if xml:
				# Parse the XML with elementTree
				tree = ET.fromstring(xml)

				# Find the first element <outline>
				for elem in tree.iter('outline'):
					# Iterate through the elements
					genre = str(elem.get('text'))
					id = str(elem.get('guide_id'))
					genreList.append((id, genre))

		except (Exception) as exception:
			print 'getGenreList: Error parsing genres: ', exception

	def getGenreName(self, genreID):
		try:
			genreName = 'None'

			for genre in self.genreList:
				if genre[0] == genreID:
					genreName = genre[1]
					break

			return genreName
		except (Exception) as exception:
			print 'getGenreName: Error Searching genres: ', exception
			return 'None'

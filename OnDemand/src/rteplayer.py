"""
	RTE Player - Enigma2 Video Plugin
	Copyright (C) 2013 rogerthis

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

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from ServiceReference import ServiceReference
from enigma import eServiceReference, eConsoleAppContainer, ePicLoad, getDesktop, eServiceCenter
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from cookielib import CookieJar
import urllib, urllib2, re, time, os
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigBoolean, ConfigSelection, getConfigListEntry
from enigma import eTimer, iPlayableService, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_WRAP, RT_VALIGN_TOP
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from httplib import HTTPException
from twisted.web import client
import socket
from datetime import date, timedelta
import urllib, urllib2, re, time, os
from os import path as os_path, remove as os_remove, mkdir as os_mkdir
from time import strftime, strptime
from datetime import datetime
from datetime import date
import xml.etree.ElementTree as ET
from lxml import etree

########### Retrieve the webpage data ####################################

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

##########################################################################

def calcDuration(miliseconds):
	try:
		mins = int((miliseconds / (1000*60)))
		duration = str(mins)
		return str(duration)
	except (Exception) as exception:
		print 'calcDuration: Error calculating minutes: ', exception
		return ''

##########################################################################
class RTEMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="RTE Player - Main Menu" >
			<widget name="RTEMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		Screen.__init__(self, session)

		self.imagedir = "/tmp/openRteImg/"
		self.action = action
		self.value = value
		osdList = []
		if self.action is "start":
			osdList.append((_("Latest Episodes"), "latest"))
			osdList.append((_("Most Popular Episodes"), "pop"))
			osdList.append((_("Episodes by Date"), "by_date"))
			osdList.append((_("Show Categories"), "cats"))
			osdList.append((_("Shows A to Z"), "a_z"))
			osdList.append((_("Back"), "exit"))

		self["RTEMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)	  

	def go(self):
		returnValue = self["RTEMenu"].l.getCurrentSelection()[1]
		if returnValue is "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
		elif self.action is "start":
			if returnValue is "latest":
				self.session.open(StreamsThumb, "latest", "Latest", "http://feeds.rasset.ie/rteavgen/player/latest/?platform=playerxl&limit=36")
			elif returnValue is "pop":
				self.session.open(StreamsThumb, "pop", "Most Popular", "http://feeds.rasset.ie/rteavgen/player/chart/?platform=playerxl&limit=36")
			elif returnValue is "by_date":
				self.session.open(StreamsMenu, "by_date", "0", "http://feeds.rasset.ie/rteavgen/player/datelist/?platform=playerxl")
			elif returnValue is "cats":
				self.session.open(StreamsMenu, "cats", "0", "http://feeds.rasset.ie/rteavgen/player/genrelist/?type=iptv")
			elif returnValue is "a_z":
				self.session.open(StreamsMenu, "a_z", "0", "http://feeds.rasset.ie/rteavgen/player/azlist/?platform=playerxl")

	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)		

	def removeFiles(self, targetdir):
		import os
		for root, dirs, files in os.walk(targetdir):
			for name in files:
				os.remove(os.path.join(root, name))

###########################################################################

class StreamsMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" >
			<widget name="latestMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value, url):
		Screen.__init__(self, session)
		if action is 'by_date':
			Screen.setTitle(self, _("RTE Player - Choose Date"))
		elif action is 'cats':
			Screen.setTitle(self, _("RTE Player - Categories"))
		elif action is 'a_z':
			Screen.setTitle(self, _("RTE Player - A to Z"))

		self.action = action
		self.value = value
		osdList = []

		# Read the URL for the selected category on the Main Menu.
		try:
			# Parse the XML with elementTree
			tree = etree.parse(url)

			# Find the first element <entry>
			for elem in tree.xpath('//*[local-name() = "entry"]'):
				# Iterate through the children of <entry>
				if not action is 'a_z':
					name = checkUnicode(str(elem[1].text))
					url = checkUnicode(str(elem[0].text))
					osdList.append((_(name), url))
				else:
					name = checkUnicode(str(elem[1].text))
					url = checkUnicode(str(elem[2].attrib.get('href')))
					osdList.append((_(name), url))

		except (Exception) as exception:
			print 'StreamsMenu: Error parsing feed: ', exception											

		osdList.append((_("Exit"), "exit"))

		self["latestMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1) 

	def go(self):
		returnValue = self["latestMenu"].l.getCurrentSelection()[1]
		title = self["latestMenu"].l.getCurrentSelection()[0]
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			elif self.action is "by_date":
				self.session.open(StreamsThumb, "by_date", title, returnValue)
			elif self.action is "cats" or self.action is "a_z":
				self.session.open(StreamsThumb, "cat_secs", title, returnValue)
			elif self.action is "cat_secs":
				self.session.open(StreamsThumb, "programmeListMenu", title, returnValue)

	def cancel(self):
		self.close(None)

###########################################################################

def findPlayUrl(showID, **kwargs):
	# Take the accepted showID and append it onto the url below.
	url = 'http://feeds.rasset.ie/rteavgen/player/playlist?type=iptv1&showId='+showID

	try:
		html = wgetUrl(url)

		# If zero, an error occurred retrieving the url, throw an error
		if len(html) == 0:
			self.mediaProblemPopup()

		links = (re.compile ('url="rtmpe://fmsod.rte.ie/rtevod/mp4:(.+?)" type="video/mp4"').findall(html)[0])
		fileUrl = "rtmpe://fmsod.rte.ie/rtevod/ app=rtevod/ swfUrl=http://www.rte.ie/player/assets/player_458.swf swfVfy=1 timeout=180 playpath=mp4:"+links
		return fileUrl
	except (Exception) as exception:
		print 'findPlayUrl: Problem rerieving URL: ', exception

###########################################################################

def checkUnicode(value, **kwargs):
	stringValue = value 
	returnValue = stringValue.replace('&#39;', '\'')
	return returnValue

###########################################################################

def main(session, **kwargs):
	action = "start"
	value = 0 
	start = session.open(RTEMenu, action, value)

###########################################################################

def MPanelEntryComponent(channel, text, png):
	res = [ channel ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 200, 15, 800, 100, 0, RT_HALIGN_LEFT|RT_WRAP|RT_VALIGN_TOP, text))
	res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 5, 178, 100, png))
	return res

###########################################################################
class MPanelList(MenuList):
	def __init__(self, list, selection = 0, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(120)
		self.selection = selection

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)

###########################################################################

class StreamsThumb(Screen):

	PROGDATE = 0
	PROGNAME = 1
	SHORT_DESCR = 2
	CHANNELNAME = 3
	STREAMURL = 4
	ICON = 5
	ICONTYPE = 6
	MAX_PIC_PAGE = 5

	TIMER_CMD_START = 0
	TIMER_CMD_VKEY = 1



	def __init__(self, session, action, value, url):
		self.skin = """
				<screen position="80,70" size="e-160,e-110" title="">
					<widget name="list" position="0,0" size="e-0,e-0" scrollbarMode="showOnDemand" transparent="1" zPosition="2"/>
					<widget name="thumbnail" position="0,0" size="178,100" alphatest="on" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)

		self["thumbnail"] = Pixmap()
		self["thumbnail"].hide()

		self.cbTimer = eTimer()
		self.cbTimer.callback.append(self.timerCallback)

		self.Details = {}
		self.pixmaps_to_load = []
		self.picloads = {}
		self.color = "#33000000"

		self.page = 0
		self.numOfPics = 0
		self.isAtotZ = False
		self.cmd = action
		self.url = url
		self.title = value
		self.timerCmd = self.TIMER_CMD_START

		self.png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/OnDemand/icons/rteDefault.png"))

		self.tmplist = []
		self.mediaList = []

		self.imagedir = "/tmp/openRteImg/"
		if (os_path.exists(self.imagedir) != True):
			os_mkdir(self.imagedir)

		self["list"] = MPanelList(list = self.tmplist, selection = 0)
		self.updateMenu()
		self["actions"] = ActionMap(["WizardActions", "MovieSelectionActions", "DirectionActions"],
		{
			"up": self.key_up,
			"down": self.key_down,
			"left": self.key_left,
			"right": self.key_right,
			"ok": self.go,
			"back": self.Exit,
		}, -1)
		self.onLayoutFinish.append(self.layoutFinished)
		self.cbTimer.start(10)

##############################################################

	def layoutFinished(self):
		self.setTitle("RTE Player: Listings for " +self.title)

##############################################################

	def updatePage(self):
		if self.page != self["list"].getSelectedIndex() / self.MAX_PIC_PAGE:
			self.page = self["list"].getSelectedIndex() / self.MAX_PIC_PAGE
			self.loadPicPage()

##############################################################

	def key_up(self):
		self["list"].up()
		self.updatePage()

	def key_down(self):
		self["list"].down()
		self.updatePage()

	def key_left(self):
		self["list"].pageUp()
		self.updatePage()

	def key_right(self):
		self["list"].pageDown()
		self.updatePage()

##############################################################

	def getThumbnailName(self, x):
		temp_icon = str(x[self.ICON])
		icon_name = temp_icon.rsplit('/',1)
		return str(icon_name[1])

##############################################################

	def updateMenu(self):
		self.tmplist = []
		if len(self.mediaList) > 0:
			pos = 0
			for x in self.mediaList:
				self.tmplist.append(MPanelEntryComponent(channel = x, text = (x[self.PROGNAME] + '\n' + x[self.PROGDATE] + '\n' + x[self.SHORT_DESCR]), png = self.png))
				tmp_icon = self.getThumbnailName(x)
				thumbnailFile = self.imagedir + tmp_icon
				self.pixmaps_to_load.append(tmp_icon)

				if not self.Details.has_key(tmp_icon):
					self.Details[tmp_icon] = { 'thumbnail': None}

				if x[self.ICON] != '':
					if (os_path.exists(thumbnailFile) == True):
						self.fetchFinished(True, picture_id = tmp_icon, failed = False)
					else:
						if config.ondemand.ShowImages.value:
							client.downloadPage(x[self.ICON], thumbnailFile).addCallback(self.fetchFinished, tmp_icon).addErrback(self.fetchFailed, tmp_icon)
				pos += 1
			self["list"].setList(self.tmplist)

##############################################################

	def Exit(self):
		self.close()		

##############################################################

	def clearList(self):
		elist = []
		self["list"].setList(elist)
		self.mediaList = []
		self.pixmaps_to_load = []
		self.page = 0

##############################################################

	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return

		if retval == 'latest' or retval == 'pop' or retval == 'by_date':
			self.clearList()
			self.getMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		if retval == 'cat_secs':
			self.clearList()
			self.getCatsMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif  retval == 'programmeListMenu':
			self.clearList()
			self.canBeMultiple(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()

##############################################################

	def timerCallback(self):
		self.cbTimer.stop()
		if self.timerCmd == self.TIMER_CMD_START:
			self.setupCallback(self.cmd)
		elif self.timerCmd == self.TIMER_CMD_VKEY:
			self.session.openWithCallback(self.keyboardCallback, VirtualKeyBoard, title = (_("Search term")), text = "")

##############################################################

	def keyboardCallback(self, callback = None):
		if callback is not None and len(callback):
			self.clearList()
			self.getMediaData(self.mediaList, self.STAGING_UG_BASE_URL + "ug/ajax/action/search/protocol/html/searchString/" + callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple = True)
		else:
			self.close()

##############################################################

	def mediaProblemPopup(self, error):
		self.session.openWithCallback(self.close, MessageBox, _(error), MessageBox.TYPE_ERROR, timeout=5, simple = True)

##############################################################

	def fetchFailed(self, string, picture_id):
		self.fetchFinished(False, picture_id, failed = True)

##############################################################

	def fetchFinished(self, x, picture_id, failed = False):
		if failed:
			return
		else:
			thumbnailFile = self.imagedir + str(picture_id)
		sc = AVSwitch().getFramebufferScale()
		if (os_path.exists(thumbnailFile) == True):
			start = self.page * self.MAX_PIC_PAGE
			end = (self.page * self.MAX_PIC_PAGE) + self.MAX_PIC_PAGE
			count = 0
			for x in self.mediaList:
				if count >= start and count < end:
					if self.getThumbnailName(x) == picture_id:
						self.picloads[picture_id] = ePicLoad()
						self.picloads[picture_id].PictureData.get().append(boundFunction(self.finish_decode, picture_id))
						self.picloads[picture_id].setPara((self["thumbnail"].instance.size().width(), self["thumbnail"].instance.size().height(), sc[0], sc[1], True, 1, "#00000000"))
						self.picloads[picture_id].startDecode(thumbnailFile)
				count += 1
				if count > end:
					break
		else:
			self.pixmaps_to_load.append(picture_id)
			self.fetchFinished(False, picture_id, failed = True)

##############################################################

	def loadPicPage(self):
		self.Details = {}
		self.updateMenu()

##############################################################

	def finish_decode(self, picture_id, info):
		ptr = self.picloads[picture_id].getData()
		thumbnailFile = self.imagedir + str(picture_id)
		if ptr != None:
			if self.Details.has_key(picture_id):
				self.Details[picture_id]["thumbnail"] = ptr

		self.tmplist = []
		pos = 0
		for x in self.mediaList:
			if self.Details[self.getThumbnailName(x)]["thumbnail"] is not None:
				self.tmplist.append(MPanelEntryComponent(channel = x, text = (x[self.PROGNAME] + '\n' + x[self.PROGDATE] + '\n' + x[self.SHORT_DESCR]), png = self.Details[self.getThumbnailName(x)]["thumbnail"]))
			else:
				self.tmplist.append(MPanelEntryComponent(channel = x, text = (x[self.PROGNAME] + '\n' + x[self.PROGDATE] + '\n' + x[self.SHORT_DESCR]), png = self.png))

			pos += 1
		self["list"].setList(self.tmplist)

##############################################################

	def go(self):
		showID = self["list"].l.getCurrentSelection()[0][4]
		showName = self["list"].l.getCurrentSelection()[0][1]

		if self.cmd == 'cat_secs':
			self.session.open(StreamsThumb, "programmeListMenu", showName, showID)
		else:
			fileUrl = findPlayUrl(showID)
			fileRef = eServiceReference(4097,0,fileUrl)
			fileRef.setName (showName)
			lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			self.session.open(MoviePlayer, fileRef, None, lastservice)

##############################################################

	def canBeMultiple(self, weekList, showID):
		url = 'http://www.rte.ie/player/ie/show/'+showID

		showIDs = []
		start1 = datetime.now()
		try: 
			parser = etree.HTMLParser(encoding='utf-8')
			tree   = etree.parse(url, parser)

			for shows in tree.xpath('//div[@class="more-videos-pane"]//article[@class="thumbnail-module"]//a[@class="thumbnail-programme-link"]/@href'):
				show_split = shows.rsplit('/',2)
				show = str(show_split[1])
				showIDs.append(show)

		except (Exception) as exception:
			print 'canBeMultiple:-getShows: Error getting show numbers: ', exception
			showIDs.append(showID)


		# If zero we only have 1 show in this category
		if len(showIDs) == 0:
			showIDs.append(showID)

		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''

		for show in showIDs:
			newUrl = 'http://feeds.rasset.ie/rteavgen/player/playlist?showId='+show

			try:
				# Parse the XML with lxml
				tree = etree.parse(newUrl)

				# Find the first element <entry>
				for elem in tree.xpath('//*[local-name() = "entry"]'):
					# Iterate through the children of <entry>
					stream = str(elem[0].text)
					date_tmp = str(elem[1].text)
					name_tmp = str(elem[3].text)
					short_tmp = str(elem[4].text)
					channel = str(elem[5].attrib.get('term'))
					millisecs = int(elem[16].attrib.get('ms'))
					icon_url = str(elem[23].attrib.get('url'))

					# Tidy up the format of the data
					year = int(date_tmp[0:4])
					month = int(date_tmp[5:7])
					day = int(date_tmp[8:10])
					oldDate = date(year, month, day)  # year, month, day
					dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
					date1 = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +date_tmp[11:16] + " " + channel

					name = checkUnicode(name_tmp)
					short = checkUnicode(short_tmp)

					# Calcualte the stream duration
					duration = calcDuration(millisecs)

					# Append duration onto the show description
					short = short+"\nDuration: "+str(duration)+" mins"

					icon = icon_url[0:-7]+"-261.jpg"
					icon_type = '.jpg'

					weekList.append((date1, name, short, channel, stream, icon, icon_type, False))

			except (Exception) as exception:
				print "canBeMultiple: Problem parsing data: ", exception

#################################################################

	def getMediaData(self, weekList, url):

		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''

		try:
			# Parse the XML with elementTree
			tree = etree.parse(url)

			# Find the first element <entry>
			for elem in tree.xpath('//*[local-name() = "entry"]'):
				# Iterate through the children of <entry>
				stream = str(elem[1].text)
				date_tmp = str(elem[3].text)
				name_tmp = str(elem[5].text)
				short_tmp = str(elem[6].text)
				channel = str(elem[7].attrib.get('term'))
				millisecs = int(elem[18].attrib.get('ms'))
				icon_url = str(elem[23].attrib.get('url'))

				year = int(date_tmp[0:4])
				month = int(date_tmp[5:7])
				day = int(date_tmp[8:10])
				oldDate = date(int(year), int(month), int(day)) # year, month, day
				dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
				date1 = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +date_tmp[11:16] + " " + channel

				name = checkUnicode(name_tmp)
				short = checkUnicode(short_tmp)
				icon = icon_url[0:-4]+"-261.jpg" # higher quality image 261x147
				#icon = line[5] lower quality image 150x84
				icon_type = '.jpg'

				# Calcualte the stream duration
				duration = calcDuration(millisecs)

				# Append duration onto the show description
				short = short+"\nDuration: "+str(duration)+" mins"

				weekList.append((date1, name, short, channel, stream, icon, icon_type, False))

		except (Exception) as exception:
			print 'getMediaData: Error getting Media info: ', exception

#################################################################

	def getCatsMediaData(self, weekList, url):
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''

		try:
			# Parse the XML with elementTree
			tree = etree.parse(url)

			# Find the first element <entry>
			for elem in tree.xpath('//*[local-name() = "entry"]'):
				# Iterate through the children of <entry>
				stream_tmp = str(elem[1].text)
				date_tmp = str(elem[4].text)
				name_tmp = str(elem[5].text)
				icon_url = str(elem[23].attrib.get('url'))

				year = int(date_tmp[0:4])
				month = int(date_tmp[5:7])
				day = int(date_tmp[8:10])
				oldDate = date(int(year), int(month), int(day)) # year, month, day
				dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
				date1 = "Last updated on " + dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +date_tmp[11:16]

				stream = checkUnicode(stream_tmp)
				name = checkUnicode(name_tmp)
				short = "\nThe current list of episodes stored for " + str(name)
				icon = icon_url[0:-4]+"-261.jpg" # higher quality image 261x147
				icon_type = '.jpg'

				weekList.append((date1, name, short, channel, stream, icon, icon_type, False))

		except (Exception) as exception:
			print 'getCatsMediaData: Error getting Media info: ', exception			

###########################################################################	   
class MoviePlayer(MP_parent):
	def __init__(self, session, service, slist = None, lastservice = None):
		MP_parent.__init__(self, session, service, slist, lastservice)

	def leavePlayer(self):
		self.leavePlayerConfirmed([True,"quit"])
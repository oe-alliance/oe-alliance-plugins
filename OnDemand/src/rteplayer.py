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

# Set the default config option to True to show images
config.plugins.rteplayer = ConfigSubsection()
config.plugins.rteplayer.showpictures = ConfigBoolean(default = True)

def wgetUrl(target):
	try:
		req = urllib2.Request(target)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		outtxt = str(response.read())
		response.close()
	except:
		return ''
	return outtxt

##########################################################################
class ShowHelp(Screen):
	skin = """
		<screen position="center,center" size="700,400" title="RTE Player">
			<widget name="myLabel" position="10,0" size="680,380" font="Console;18"/>
			</screen>"""
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		text = """
RTE Player Beta 1
rogerthis 2013

Plays single episodes from Latest, Popular and By Date
Multiple episode selection from Categories and A to Z
For single episodes from Categories and A to Z, it 
automatically play this file

Change Log
Beta 1 
fixed unicode character &#39;
code cleanup
	
Alpha 2
adds:
categories
a to z
	
Alpha 1
initial release
	
Main support on www.world-of-satellite.com
"""

		self["myLabel"] = ScrollLabel(text)
		self["myActionMap"] = ActionMap(["WizardActions", "SetupActions", "ColorActions"],
		{
		"cancel": self.close,
		"ok": self.close,
		"up": self["myLabel"].pageUp,
		"down": self["myLabel"].pageDown,
		}, -1)
		
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
			osdList.append((_("Setup"), 'setup'))
			osdList.append((_("Help & About"), "help"))
			osdList.append((_("Exit"), "exit"))
		
		self["RTEMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1)	  

	def go(self):
		returnValue = self["RTEMenu"].l.getCurrentSelection()[1]
		if returnValue is "help":
			self.session.open(ShowHelp)
		elif returnValue is "setup":
			self.session.open(OpenSetupScreen)
		elif returnValue is "exit":
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
		html = wgetUrl(url)
		
		# If zero, an error occurred retrieving the url, throw an error
		if len(html) == 0:
			self.mediaProblemPopup()
		
		# Depending on the Action, select the required data from the returned xml.
		if action is 'by_date' or action is 'cats':
			links = (re.compile ('<id>(.+?)</id> \n        <title type="text">(.+?)</title>').findall(html))
		elif action is 'a_z':
			links = (re.compile ('<title type="text">(.+?)</title>\n        \n        \n        \n        \n        \n        <link rel="self" type=".+?" href="(.+?)"').findall(html))
		elif action is 'cat_secs':
			links = (re.compile ('<showid>(.+?)</showid>\n        <platform>.+?</platform>\n        <published>.+?</published>\n        <updated>.+?</updated>\n        <title type="text">(.+?)</title>').findall(html))
		
		# Remove the Unicode characters from the display text.
		for link in links:
			if not action is 'a_z':
				returned = checkUnicode(link[1])
				osdList.append((_(returned), link[0]))
			else:
				returned = checkUnicode(link[0])
				osdList.append((_(returned), link[1]))
				
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
				self.session.open(StreamsMenu, "cat_secs", title, returnValue)
			elif self.action is "cat_secs":
				self.session.open(StreamsThumb, "programmeListMenu", title, returnValue)

 
	def cancel(self):
		self.close(None)

###########################################################################
def findPlayUrl(showID, **kwargs):
	# Take the accepted showID and append it onto the url below.
	url = 'http://feeds.rasset.ie/rteavgen/player/playlist?type=iptv1&showId='+showID
	html = wgetUrl(url)
	
	# If zero, an error occurred retrieving the url, throw an error
	if len(html) == 0:
		self.mediaProblemPopup()
	
	links = (re.compile ('url="rtmpe://fmsod.rte.ie/rtevod/mp4:(.+?)" type="video/mp4"').findall(html)[0])
	fileUrl = "rtmpe://fmsod.rte.ie/rtevod/ app=rtevod/ swfUrl=http://www.rte.ie/player/assets/player_458.swf swfVfy=1 timeout=180 playpath=mp4:"+links
	return fileUrl
	
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
	#session.open(RTEMenu)
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
class OpenSetupScreen(Screen, ConfigListScreen):

	def __init__(self, session):
		self.skin = """
				<screen position="center,center" size="400,100" title="">
					<widget name="config" position="10,10" size="e-20,e-10" scrollbarMode="showOnDemand" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self["config"].list = self.list
		self.list.append(getConfigListEntry(_("Show pictures"), config.plugins.rteplayer.showpictures))
		self["config"].l.setList(self.list)
		
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("RTE Player: Setup Screen"))

	def keyGo(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

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

		self.png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/rteplayer/logo.jpg"))
		
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
		}
		, -1)
		self.onLayoutFinish.append(self.layoutFinished)
		self.cbTimer.start(10)

	def layoutFinished(self):
		self.setTitle("RTE Player: Listings for " +self.title)

	def updatePage(self):
		if self.page != self["list"].getSelectedIndex() / self.MAX_PIC_PAGE:
			self.page = self["list"].getSelectedIndex() / self.MAX_PIC_PAGE
			self.loadPicPage()

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

	def getThumbnailName(self, x):
		return str(x[self.STREAMURL]) + str(x[self.ICONTYPE])

	def updateMenu(self):
		self.tmplist = []
		if len(self.mediaList) > 0:
			pos = 0
			for x in self.mediaList:
				self.tmplist.append(MPanelEntryComponent(channel = x, text = (x[self.PROGNAME] + '\n' + x[self.PROGDATE] + '\n' + x[self.SHORT_DESCR]), png = self.png))
				#tmp_icon = str(x[4]) + ".jpg"
				tmp_icon = self.getThumbnailName(x)
				thumbnailFile = self.imagedir + tmp_icon
				self.pixmaps_to_load.append(tmp_icon)

				if not self.Details.has_key(tmp_icon):
					self.Details[tmp_icon] = { 'thumbnail': None}

				if x[self.ICON] != '':
					if (os_path.exists(thumbnailFile) == True):
						self.fetchFinished(True, picture_id = tmp_icon, failed = False)
					else:
						if config.plugins.rteplayer.showpictures.value:
							client.downloadPage(x[self.ICON], thumbnailFile).addCallback(self.fetchFinished, tmp_icon).addErrback(self.fetchFailed, tmp_icon)
				pos += 1
			self["list"].setList(self.tmplist)

	def Exit(self):
		self.close()		

	def clearList(self):
		elist = []
		self["list"].setList(elist)
		self.mediaList = []
		self.pixmaps_to_load = []
		self.page = 0

	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return
		
		if retval == 'latest' or retval == 'pop' or retval == 'by_date':
			self.clearList()
			self.getMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif  retval == 'programmeListMenu':
			self.clearList()
			self.canBeMultiple(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		else:
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

	def timerCallback(self):
		self.cbTimer.stop()
		if self.timerCmd == self.TIMER_CMD_START:
			self.setupCallback(self.cmd)
		elif self.timerCmd == self.TIMER_CMD_VKEY:
			self.session.openWithCallback(self.keyboardCallback, VirtualKeyBoard, title = (_("Search term")), text = "")

	def keyboardCallback(self, callback = None):
		if callback is not None and len(callback):
			self.clearList()
			self.getMediaData(self.mediaList, self.STAGING_UG_BASE_URL + "ug/ajax/action/search/protocol/html/searchString/" + callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple = True)
		else:
			self.close()

	def mediaProblemPopup(self):
		self.session.openWithCallback(self.close, MessageBox, _("There was a problem retrieving the media list"), MessageBox.TYPE_ERROR, timeout=5, simple = True)

	def fetchFailed(self, string, picture_id):
		self.fetchFinished(False, picture_id, failed = True)

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
						#self.picloads[picture_id].setPara((178, 100, sc[0], sc[1], False, 1, "#00000000"))
						self.picloads[picture_id].startDecode(thumbnailFile)
				count += 1
				if count > end:
					break
		else:
			self.pixmaps_to_load.append(picture_id)
			self.fetchFinished(False, picture_id, failed = True)

	def loadPicPage(self):
		self.Details = {}
		self.updateMenu()

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

	def go(self):
		showID = self["list"].l.getCurrentSelection()[0][4]
		showName = self["list"].l.getCurrentSelection()[0][1]
		
		fileUrl = findPlayUrl(showID)
		fileRef = eServiceReference(4097,0,fileUrl)
		fileRef.setName (showName)
		lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.session.open(MoviePlayer, fileRef, None, lastservice)

	def canBeMultiple(self, weekList, showID):
		url = 'http://www.rte.ie/player/ie/show/'+showID
		html = wgetUrl(url)
		
		# If zero, an error occurred retrieving the url, throw an error
		if len(html) == 0:
			self.mediaProblemPopup()
		
		# Now get all the related Show ID's
		urlHeads = (re.compile ('<a class="thumbnail-programme-link" href="/player/ie/show/(.+?)/">\r\n').findall(html))
		
		if len(urlHeads) == 0:
			urlHeads.append(showID) # If zero we only have 1 show in this category
		
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		
		for show in urlHeads:
			newUrl = 'http://feeds.rasset.ie/rteavgen/player/playlist?showId='+show
			data = wgetUrl(newUrl)
			
			# If zero, an error occurred retrieving the url, throw an error
			if len(data) == 0:
				self.mediaProblemPopup()
			
			try:
				# Parse the XML with elementTree
				tree = ET.fromstring(data)
				
				# Find the first element <entry> (Don't know why it appends the URL onto here???)
				for elem in tree.iter('{http://www.w3.org/2005/Atom}entry'):
					# Iterate through the children of <entry>
					for el in elem:
						#print el.tag, el.attrib, el.text (If you want to see each element and attribs use this line)
						stream = str(elem.find('{http://www.w3.org/2005/Atom}id').text)
						date_tmp = str(elem.find('{http://www.w3.org/2005/Atom}published').text)
						name_tmp = str(elem.find('{http://www.w3.org/2005/Atom}title').text)
						short_tmp = str(elem.find('{http://www.w3.org/2005/Atom}content').text)
						channel_tmp = elem.find('{http://www.w3.org/2005/Atom}category', "channel")
						channel = str(channel_tmp.get('term'))
						icon_tmp = elem.find('{http://search.yahoo.com/mrss/}thumbnail')
						icon_url = str(icon_tmp.get('url'))
										
					# Tidy up the format of the data
					year = int(date_tmp[0:4])
					month = int(date_tmp[5:7])
					day = int(date_tmp[8:10])
					oldDate = date(year, month, day)  # year, month, day
					dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
					date1 = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +date_tmp[11:16] + " " + channel
					
					name = checkUnicode(name_tmp)
					short = checkUnicode(short_tmp)
					icon = icon_url[0:-7]+"-261.jpg"
					icon_type = '.jpg'
					
					# Debug: Print the field outputs
					#print stream
					#print date1
					#print name
					#print short
					#print channel
					#print icon
					
					weekList.append((date1, name, short, channel, stream, icon, icon_type, False))

			except:
				self.session.open(MessageBox, _("Problem with show"), MessageBox.TYPE_INFO, timeout=5)
				print "Problem with show number:", show

	def getMediaData(self, weekList, url):
		data = wgetUrl(url)
		
		# If zero, an error occurred retrieving the url, throw an error
		if len(data) == 0:
			self.mediaProblemPopup()

		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''

		links = (re.compile ('<showid>(.+?)</showid>\s*' \
		                     '<platform>.+?</platform>\s*' \
		                     '<published>(.+?)</published>\s*' \
		                     '<updated>.+?</updated>\s*' \
		                     '<title type="text">(.+?)</title>\s*' \
		                     '<content type="text">(.+?)</content>\s*' \
		                     '<category term="(.+?)" rte:type="channel"/>\s*' \
		                     '<category term=".+?" rte:type="genre"/>\s*' \
		                     '<category term=".+?" rte:type="series"/>\s*' \
		                     '<category term=".+?" rte:type="episode"/>\s*' \
		                     '<category term=".+?" rte:type="ranking"/>\s*' \
		                     '<category term=".+?" rte:type="genrelist"/>\s*' \
		                     '<category term=".+?" rte:type="keywordlist"/>\s*' \
		                     '<category term=".+?" rte:type="progid"/>\s*' \
		                     '<link rel="self" type=".+?" href=".+?" />\s*' \
		                     '<link rel="alternate" type=".+?" href=".+?" />\s*' \
				     '<rte:valid start=".+?" end=".+?"/>\s*' \
				     '<rte:duration ms=".+?" formatted=".+?" />\s*' \
				     '<rte:statistics views=".+?" />\s*' \
				     '<media:title type=".+?">.+?</media:title>\s*' \
				     '<media:description type=".+?">.+?</media:description>\s*' \
				     '<media:player url=".+?" width=".+?" height=".+?"/>\s*' \
				     '<media:thumbnail url="(.+?)" time=".+?"/>').findall(data))

		for line in links:
			stream = line[0]

			# Format the date to display onscreen
			year = int(line[1][0:4])
			month = int(line[1][5:7])
			day = int(line[1][8:10])
			oldDate = date(int(year), int(month), int(day)) # year, month, day
			dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
			date1 = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +line[1][11:16] + " " + line[4]
			
			name = checkUnicode(line[2])
			short = checkUnicode(line[3])
			channel = line[4]
			icon = line[5][0:-4]+"-261.jpg" # higher quality image 261x147
			#icon = line[5] lower quality image 150x84
			icon_type = '.jpg'
			weekList.append((date1, name, short, channel, stream, icon, icon_type, False))
			
###########################################################################	   
class MoviePlayer(MP_parent):
	def __init__(self, session, service, slist = None, lastservice = None):
		MP_parent.__init__(self, session, service, slist, lastservice)

	def leavePlayer(self):
		self.leavePlayerConfirmed([True,"quit"])
############################################################################
def Plugins(**kwargs):
	return PluginDescriptor(
		name="111RTEPlayer",
		description="RTE Player - Irish Video On Demand Service",
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon="./rteplayer.png",
		fnc=main)

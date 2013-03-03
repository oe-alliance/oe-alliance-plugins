"""
    3Player - Enigma2 Video Plugin
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

from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from ServiceReference import ServiceReference
from enigma import eServiceReference, eConsoleAppContainer, ePicLoad, getDesktop, eServiceCenter
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from cookielib import CookieJar
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigBoolean, ConfigInteger, ConfigSelection, getConfigListEntry
from enigma import eTimer, iPlayableService, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_WRAP, RT_VALIGN_TOP
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from httplib import HTTPException
from twisted.web import client
from os import path as os_path, remove as os_remove, mkdir as os_mkdir
from time import strftime, strptime
import socket
import random
import urllib, urllib2, re, time, os
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from lxml import etree

# Set the default config option to False for IP Forward
config.plugins.threeplayer = ConfigSubsection()
config.plugins.threeplayer.ipforward = ConfigBoolean(default = False)
config.plugins.threeplayer.seg1 = ConfigInteger(default = 46, limits=(1, 255) )
config.plugins.threeplayer.seg2 = ConfigInteger(default = 7, limits=(1, 255) )

##########################################################################
class threeMainMenu(Screen):

	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="3Player - Main Menu" >
			<widget name="threeMainMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""


	def __init__(self, session, action, value):

		self.imagedir = "/tmp/openThreeImg/"
		self.session = session
		self.action = action
		self.value = value
		osdList = []

		if self.action is "start":

			osdList.append((_("Most Talked About"), "talked"))
			osdList.append((_("Straight Off The Telly"), "straight"))
			osdList.append((_("Going, Going..."), "going"))
			osdList.append((_("All Shows"), "all_shows"))
			osdList.append((_("Setup"), 'setup'))
			osdList.append((_("Back"), "exit"))

		Screen.__init__(self, session)
		self["threeMainMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)


	def go(self):
		returnValue = self["threeMainMenu"].l.getCurrentSelection()[1]

		if returnValue is "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
		elif returnValue is "setup":
			self.session.open(OpenSetupScreen)
		elif self.action is "start":
			if returnValue is "talked":
				self.session.open(StreamsThumb, "talked", "Most Talked About", "http://www.tv3.ie/3player")
			elif returnValue is "straight":
				self.session.open(StreamsThumb, "straight", "Straight Off The Telly", "http://www.tv3.ie/3player")
			elif returnValue is "going":
				self.session.open(StreamsThumb, "going", "Going Going Gone", "http://www.tv3.ie/3player")
			elif returnValue is "all_shows":
				self.session.open(StreamsThumb, "all_shows", "All Shows", "http://www.tv3.ie/3player/allshows")


	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)
        
	def removeFiles(self, targetdir):
		for root, dirs, files in os.walk(targetdir):
			for name in files:
				os.remove(os.path.join(root, name))

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
					<widget name="config" position="10,10"   size="e-20,e-10" scrollbarMode="showOnDemand" />
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
		self.list.append(getConfigListEntry(_("Enable IP Forward"), config.plugins.threeplayer.ipforward))
		self.list.append(getConfigListEntry(_("Segment 1 (e.g. 46.X.X.X) "), config.plugins.threeplayer.seg1))
		self.list.append(getConfigListEntry(_("Segment 2 (e.g. XX.7.X.X) "), config.plugins.threeplayer.seg2))
		self["config"].l.setList(self.list)
		
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Three Player: Setup Screen"))

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

		self.png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/OnDemand/icons/threeDefault.png"))

		self.tmplist = []
		self.mediaList = []

		self.imagedir = "/tmp/openThreeImg/"
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

	def layoutFinished(self):
		self.setTitle("3 Player: Listings for " +self.title)

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
		temp_icon = str(x[self.ICON])
		icon_name = temp_icon.rsplit('/',1)
		return str(icon_name[1])

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

		if retval == 'talked':
			self.clearList()
			self.getMediaData(self.mediaList, self.url, "slider1")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif  retval == 'straight':
			self.clearList()
			self.getMediaData(self.mediaList, self.url, "slider2")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif  retval == 'going':
			self.clearList()
			self.getMediaData(self.mediaList, self.url, "slider3")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif  retval == 'all_shows':
			self.clearList()
			self.getAllShowsMediaData(self.mediaList, self.url, "gridshow")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif  retval == 'one_show':
			self.clearList()
			self.getMediaData(self.mediaList, self.url, "slider1a")
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
			self.getMediaData(self.mediaList, self.STAGING_UG_BASE_URL + "ug/ajax/action/search/protocol/html/searchString/" + callback, '')
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
			end  = (self.page * self.MAX_PIC_PAGE) + self.MAX_PIC_PAGE
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
		icon = self["list"].l.getCurrentSelection()[0][5]

		if self.cmd == 'all_shows':
			self.session.open(StreamsThumb, "one_show", showName, showID)
		else:
			if self.cmd == 'straight':
				fileUrl = findPlayUrl(showID)
				print 'fileUrl: ', fileUrl
			else:
				fileUrl = str(icon[:-12])+'.mp4'
				fileUrl = fileUrl.replace('3player', '3Player')
				print 'fileUrl: ', fileUrl
				
			fileRef = eServiceReference(4097,0,str(fileUrl))
			fileRef.setName (showName)
			lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			self.session.open(MoviePlayer, fileRef, None, lastservice)

##############################################################################

	def getMediaData(self, weekList, url, function):

		func = function[:7]
		funcDiff = function[-1:]
		duration = ""
		icon_type = ".jpg"
		channel = "TV3"
		short = ''
		name = ''
		date = ''
		stream = ''
		icon = ''
		iconSet = False

		try:
			parser = etree.HTMLParser(encoding='utf-8')
			tree   = etree.parse(url, parser)

			for elem in tree.xpath("//div[@id='"+func+"']//div[contains(@id,'gridshow')] | //div[@id='"+func+"']//div[contains(@id,'gridshow')]//img[@class='shadow smallroundcorner']"):
				if elem.tag == 'img':
					icon = str(elem.attrib.get('src'))
					iconSet = True               

				if elem.tag == 'div':
					stream = str(elem[0].attrib.get('href'))
					titleData = elem[0].attrib.get('title')
					titleDecode = titleData.encode('charmap', 'ignore')

					match=re.search("3player\s+\|\s+(.+),\s+(\d\d/\d\d/\d\d\d\d)\.\s*(.*)", titleDecode) 
					name = str(match.group(1))
					date = str(match.group(2))
					short = str(match.group(3))

					if func == "slider1":
						if funcDiff == "a":
							duration = elem[3].text
						else:
							duration = elem[4].text

				if iconSet == True:
					if func == "slider1":
						short = short+"\nDuration: "+str(duration)
					weekList.append((date, name, short, channel, stream, icon, icon_type, False))
					iconSet = False

		except (Exception) as exception:
			print 'getMediaData: Error parsing feed: ', exception
		        
###########################################################################

	def getAllShowsMediaData(self, weekList, url, function):

		baseUrl = "http://www.tv3.ie"
		baseDescription = "A list of all shows currently stored for "
		duration = ""
		icon_type = ".jpg"
		channel = "TV3"
		short = ''
		name = ''
		date = ''
		stream = ''
		icon = ''
		hrefSet = False

		try:
			parser = etree.HTMLParser(encoding='utf-8')
			tree   = etree.parse(url, parser)

			for elem in tree.xpath("//div[contains(@class,'gridshow')]//h3//a | //div[contains(@class,'gridshow')]//a//img"):
				if elem.tag == 'img':
					icon = str(elem.attrib.get('src'))              

				if elem.tag == 'a':
					stream = baseUrl + str(elem.attrib.get('href'))
					name = str(elem.text)
					date = " "
					short = baseDescription + str(elem.text)				
					hrefSet = True

				if hrefSet == True:
					weekList.append((date, name, short, channel, stream, icon, icon_type, False))
					hrefSet = False

		except (Exception) as exception:
			print 'getAllShowsMediaData: Error parsing feed: ', exception

###########################################################################
	
def findPlayUrl(value, **kwargs):
	fileUrl = ""
	url = value
	ipSegment1 = config.plugins.threeplayer.seg1.value
	ipSegment2 = config.plugins.threeplayer.seg2.value

	try:
		url1 = 'http://www.tv3.ie'+url
		print "url1: ", url1
		req = urllib2.Request(url1)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		if config.plugins.threeplayer.ipforward.value:
			forwardedForIP = '%d.%d.%d.%d' % (ipSegment1, ipSegment2, random.randint(0, 255), random.randint(0, 254)) 
			print 'findPlayUrl: forwardedForIP: ', forwardedForIP
			req.add_header('X-Forwarded-For', forwardedForIP)
		response = urllib2.urlopen(req)
 		html = str(response.read())
 		print "html: ", html
		response.close()
 
		if html.find('age_check_form_row') > 0:
			try:
				headers = { 'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'}
				values = {'age_ok':'1'}
				data = urllib.urlencode(values)
				req = urllib2.Request(url1, data, headers)
				response = urllib2.urlopen(req)
				html = str(response.read())
				response.close()

			except (Exception) as exception:
					print 'Error getting webpage for age restrict: ', exception
					return False
 
		#links = (re.compile ('url: "mp4:(.+?)",\r\n\t\t\t\t        autoPlay: true,\r\n\t\t\t\t\t\tautoBuffering: true,\r\n\t\t\t\t        provider: "rtmp"\r\n\t\t\t\t\t}\r\n\t\t\t\t],\r\n\t\t\t\t\r\n\t\t\t\t// All FP Plug ins:\r\n\t\t\t\tplugins:\r\n\t\t\t\t{  \r\n\t\t\t\t\tcontrols:  \r\n\t\t\t\t\t{\r\n\t\t\t\t\t\turl:"flowplayer.controls.gc-build-112011.swf"\r\n\t\t\t\t\t}\r\n\t\t\t\t\t\r\n\t\t\t\t\t,\r\n\r\n\t\t\t\t\trtmp: {\r\n\t\t\t\t\t\turl: "flowplayer.rtmp-3.2.3.swf",\r\n\t\t\t\t\t\tnetConnectionUrl: "rtmp://.+?content/videos/(.+?)/"\r\n').findall(html)[0])
		url = (re.compile ('url: "mp4:(.+?)",').findall(html)[0])
		#print "url: ", url
		connection = (re.compile ('netConnectionUrl: "rtmp://.+?content/videos/(.+?)/"').findall(html)[0])
		#print "connection: ", connection
		#fileUrl = 'http://content.tv3.ie/content/videos/'+str(links[1])+'/'+str(links[0])
		fileUrl = 'http://content.tv3.ie/content/videos/'+str(connection)+'/'+str(url)
		print "fileUrl: ", fileUrl

	except urllib2.HTTPError, exception:
		exResp = str(exception.read())
		print 'findPlayUrl: HTTPError: Error getting URLs: ', exResp		
	except (Exception) as exception:
		print 'findPlayUrl: Error getting URLs: ', exception
		return False
 
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
	start = session.open(threeMainMenu, action, value)
	#session.open(RTEMenu)
###########################################################################    
class MoviePlayer(MP_parent):
	def __init__(self, session, service, slist = None, lastservice = None):		
		self.session = session
		self.WithoutStopClose = False
		MP_parent.__init__(self, session, service, slist, lastservice)

	def leavePlayer(self):
		self.leavePlayerConfirmed([True,"quit"])
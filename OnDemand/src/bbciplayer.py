
"""
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
import xml.dom.minidom as dom
import httplib
import dns.resolver


##########################################################################

def wgetUrl(target):
	try:
		req = urllib2.Request(target)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		outtxt = str(response.read())
		response.close()
	except (URLError, HTTPException, socket.error):
		return ''
	return outtxt

##########################################################################
def checkUnicode(value, **kwargs):
	stringValue = value 
	returnValue = stringValue.replace('&#39;', '\'')
	return returnValue
###########################################################################

class ShowHelp(Screen):
	skin = """
		<screen position="center,center" size="700,400" title="BBC iPlayer">
			<widget name="myLabel" position="10,0" size="680,380" font="Console;18"/>
			</screen>"""
	def __init__(self, session, args = None):
		self.session = session

		Screen.__init__(self, session)
		#Help text
		text = """
	   BBC iPlayer 

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
class BBCiMenu(Screen):
	print "BBCiMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="BBC iPlayer" >
		<widget name="BBCiMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""
			
	def __init__(self, session, action, value):
		
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		if self.action is "start":
			print "start"
			osdList.append((_("TV HIGHLIGHTS"), "bbchighlights"))
			osdList.append((_("MOST POPULAR TV"), "bbcpopular"))
			osdList.append((_("DRAMA"), "bbcdrama"))
			osdList.append((_("ENTERTAINMENT"), "bbcentertainment"))
			osdList.append((_("MOVIES"), "film"))
			osdList.append((_("FACTUAL"), "bbcfactual"))
			osdList.append((_("COMEDY"), "bbccomedy"))
			osdList.append((_("SOAPS"), "bbcsoaps"))
			osdList.append((_("CHILDRENS"), "bbckids"))
			osdList.append((_("NEWS"), "bbcnews"))
			osdList.append((_("SPORT"), "bbcsport"))
			osdList.append((_("MUSIC"), "bbcmusic"))
			osdList.append((_("HEALTH AND WELLBEING"), "bbchealth"))
			osdList.append((_("RELIGON"), "bbcreligous"))
			osdList.append((_("SIGNED"), "bbcsigned"))
			osdList.append((_("BBC NORTHERN IRELAND"), "bbcni"))
			osdList.append((_("BBC WALES"), "bbcwales"))
			osdList.append((_("BBC SCOTLAND"), "bbcscotland"))
			osdList.append((_("BBC One"), "bbc1"))
			osdList.append((_("BBC Two"), "bbc2"))
			osdList.append((_("BBC Three"), "bbc3"))
			osdList.append((_("BBC Four"), "bbc4"))
			osdList.append((_("CBBC"), "cbbc"))
			osdList.append((_("Cbeebies"), "cbeeb"))
			osdList.append((_("BBC Parliamanent"), "bbcp"))
			osdList.append((_("BBC News"), "bbcn"))
			osdList.append((_("BBC Alba"), "bbca"))
			osdList.append((_("BBC HD"), "bbchd"))
		
		osdList.append((_("Help & About"), "help"))
		osdList.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["BBCiMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1)	  
	
	def go(self):
		returnValue = self["BBCiMenu"].l.getCurrentSelection()[1]
		returnValue2 = self["BBCiMenu"].l.getCurrentSelection()[1] + "," + self["BBCiMenu"].l.getCurrentSelection()[0] 
		
		if returnValue is "help":
				self.session.open(ShowHelp)
		elif returnValue is "exit":
				self.close(None)
		elif self.action is "start":
			if returnValue is "bbc1":
				self.session.open(StreamsThumb, "bbc1", "0", "http://feeds.bbc.co.uk/iplayer/bbc_one/list")
			elif returnValue is "bbc2":
				self.session.open(StreamsThumb, "bbc2", "0", "http://feeds.bbc.co.uk/iplayer/bbc_two/list")
			elif returnValue is "bbc3":
				self.session.open(StreamsThumb, "bbc3", "0", "http://feeds.bbc.co.uk/iplayer/bbc_three/list")
			elif returnValue is "bbc4":
				self.session.open(StreamsThumb, "bbc4", "0", "http://feeds.bbc.co.uk/iplayer/bbc_four/list")
			elif returnValue is "cbbc":
				self.session.open(StreamsThumb, "cbbc", "0", "http://feeds.bbc.co.uk/iplayer/cbbc/list")
			elif returnValue is "cbeeb":
				self.session.open(StreamsThumb, "cbeeb", "0", "http://feeds.bbc.co.uk/iplayer/cbeebies/list")
			elif returnValue is "bbcp":
				self.session.open(StreamsThumb, "bbcp", "0", "http://feeds.bbc.co.uk/iplayer/bbc_parliament/list")
			elif returnValue is "bbcn":
				self.session.open(StreamsThumb, "bbcn", "0", "http://feeds.bbc.co.uk/iplayer/bbc_news24/list")
			elif returnValue is "bbca":
				self.session.open(StreamsThumb, "bbca", "0", "http://feeds.bbc.co.uk/iplayer/bbc_alba/list")
			elif returnValue is "bbchd":
				self.session.open(StreamsThumb, "bbchd", "0", "http://feeds.bbc.co.uk/iplayer/bbc_hd/list")
			elif returnValue is "bbchighlights":
				self.session.open(StreamsThumb, "bbchighlights", "0", "http://feeds.bbc.co.uk/iplayer/highlights/tv")
			elif returnValue is "bbcpopular":
				self.session.open(StreamsThumb, "bbcpopular", "0", "http://feeds.bbc.co.uk/iplayer/popular/tv")
			elif returnValue is "bbcdrama":
				self.session.open(StreamsThumb, "bbcdrama", "0", "http://feeds.bbc.co.uk/iplayer/categories/drama/tv/list")
			elif returnValue is "bbcentertainment":
				self.session.open(StreamsThumb, "bbcentertainment", "0", "http://feeds.bbc.co.uk/iplayer/categories/entertainment/tv/list")
			elif returnValue is "bbcfactual":
				self.session.open(StreamsThumb, "bbcfactual", "0", "http://feeds.bbc.co.uk/iplayer/categories/factual/tv/list")
			elif returnValue is "bbcsigned":
				self.session.open(StreamsThumb, "bbcsigned", "0", "http://feeds.bbc.co.uk/iplayer/categories/signed/tv/list")
			elif returnValue is "bbconedrama":
				self.session.open(StreamsThumb, "bbconedrama", "0", "http://feeds.bbc.co.uk/iplayer/bbc_one/drama/tv/list")
			elif returnValue is "bbccomedy":
				self.session.open(StreamsThumb, "bbccomedy", "0", "http://feeds.bbc.co.uk/iplayer/comedy/tv/list")
			elif returnValue is "bbchealth":
				self.session.open(StreamsThumb, "bbchealth", "0", "http://feeds.bbc.co.uk/iplayer/bbc_three/factual/health_and_wellbeing/tv/list")
			elif returnValue is "bbcwales":
				self.session.open(StreamsThumb, "bbcwales", "0", "http://feeds.bbc.co.uk/iplayer/wales/tv/list")
			elif returnValue is "bbcscotland":
				self.session.open(StreamsThumb, "bbcscotland", "0", "http://feeds.bbc.co.uk/iplayer/scotland/tv/list")
			elif returnValue is "bbcni":
				self.session.open(StreamsThumb, "bbcni", "0", "http://feeds.bbc.co.uk/iplayer/northern_ireland/tv/list")
			elif returnValue is "film":
				self.session.open(StreamsThumb, "film", "0", "http://feeds.bbc.co.uk/iplayer/films/tv/list")
			elif returnValue is "bbckids":
				self.session.open(StreamsThumb, "bbckids", "0", "http://feeds.bbc.co.uk/iplayer/childrens/tv/list")
			elif returnValue is "bbcnews":
				self.session.open(StreamsThumb, "bbcnews", "0", "http://feeds.bbc.co.uk/iplayer/news/tv/list/")
			elif returnValue is "bbcmusic":
				self.session.open(StreamsThumb, "bbcmusic", "0", "http://feeds.bbc.co.uk/iplayer/music/tv/list")
			elif returnValue is "bbcsoaps":
				self.session.open(StreamsThumb, "bbcsoaps", "0", "http://feeds.bbc.co.uk/iplayer/soaps/tv/list")
			elif returnValue is "bbcsport":
				self.session.open(StreamsThumb, "bbcsport", "0", "http://feeds.bbc.co.uk/iplayer/sport/tv/list")
			elif returnValue is "bbcreligous":
				self.session.open(StreamsThumb, "bbcreligous", "0", "http://feeds.bbc.co.uk/iplayer/religion_and_ethics/tv/list")

	def cancel(self):
		self.close(None)

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
					<widget name="config" position="10,10"	 size="e-20,e-10" scrollbarMode="showOnDemand" />
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

		self.imagedir = "/tmp/openBbcImg/"
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
						#if config.plugins.rteplayer.showpictures.value:
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
		
		self.clearList()
		self.getMediaData(self.mediaList, self.url)
		if len(self.mediaList) == 0:
			self.mediaProblemPopup()
		self.updateMenu()


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
			end	 = (self.page * self.MAX_PIC_PAGE) + self.MAX_PIC_PAGE
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
		print "showID", showID
		print "showName", showName
		self.session.open(bbcStreamUrl, "bbcStreamUrl", showID)


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
		
		links = (re.compile ('<entry>\n	   <title type="text">(.+?)</title>\n	 <id>tag:feeds.bbc.co.uk,2008:PIPS:(.+?)</id>\n	   <updated>(.+?)</updated>\n	 <content type="html">\n	  &lt;p&gt;\n		 &lt;a href=&quot;.+?&quot;&gt;\n		   &lt;img src=&quot;(.+?)&quot; alt=&quot;.+?&quot; /&gt;\n		&lt;/a&gt;\n	  &lt;/p&gt;\n		&lt;p&gt;\n		   (.+?)\n		&lt;/p&gt;\n	</content>').findall(data))
					
		for line in links:
			name = checkUnicode(line[0])
			stream = line[1]
			
			# Format the date to display onscreen
			year = int(line[2][0:4])
			month = int(line[2][5:7])
			day = int(line[2][8:10])
			oldDate = date(int(year), int(month), int(day))	 # year, month, day
			dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
			date1 = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +line[2][11:16]
			icon = line[3]
			icon_type = '.jpg'
			short = checkUnicode(line[4])
			channel = ""
			weekList.append((date1, name, short, channel, stream, icon, icon_type, False))
			
##################################################################################
class bbcStreamSelect(Screen):
	print "BBC One"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="BBC iPlayer" >
		<widget name="bbcStreamSelect" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value, url):
		Screen.__init__(self, session)
		self.action = action
		self.value = value
		osdList = []
		print 'URL:',url
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		links = (re.compile ('<link rel="alternate" href="(.+?)" type="text/html" title="(.+?)">').findall(html))
		for link in links:
			osdList.append((_(link[1]), link))
		osdList.sort()
			
		osdList.append((_("Help & About"), "help"))
		osdList.append((_("Exit"), "exit"))
		
		self["bbcStreamSelect"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1) 
		
	def go(self):
		returnValue = self["bbcStreamSelect"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "help":
				self.session.open(ShowHelp)
			elif returnValue is "exit":
				self.close(None)
			else:
				print "returnValue",returnValue
				self.session.open(bbcStreamUrl, "bbcStreamUrl", returnValue)
				
	def cancel(self):
		self.close(None) 

###########################################################################
class bbcStreamUrl(Screen):
	print "BBC One"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="BBC iPlayer" >
		<widget name="bbcStreamUrl" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		Screen.__init__(self, session)
		self.action = action
		returnValue = value
		osdList = []
		title = returnValue
		fileUrl = returnValue
		print 'title',title
		print 'fileurl',fileUrl
		#code1 = (re.compile ('http://www.bbc.co.uk/iplayer/episode/(.+?)/.+?/').findall(fileUrl)[0])
		#print "code1",code1
		url1 = 'http://www.bbc.co.uk/iplayer/playlist/'+fileUrl
		req = urllib2.Request(url1)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		links = (re.compile ('<mediator identifier="(.+?)" name=".+?" media_set=".+?"/>').findall(html)[1])
		print 'links',links
		url2 = 'http://www.bbc.co.uk/mediaselector/4/mtis/stream/'+links
		print 'url2',url2
		req = urllib2.Request(url2)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html1 = str(response.read())
		#print 'html1',html1
		response.close()
		
		if html1.find('notukerror') > 0:
			print "Non UK Address"
			opener = urllib2.build_opener(MyHTTPHandler)
			urllib2.install_opener (opener)
			print 'links',links
			url2 = 'http://www.bbc.co.uk/mediaselector/4/mtis/stream/'+links
			print 'url2',url2
			req = urllib2.Request(url2)
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
			response = urllib2.urlopen(req)
			html1 = str(response.read())
			#print 'html1',html1
			response.close()

		
		

		doc = dom.parseString(html1)
		root = doc.documentElement
		media = root.getElementsByTagName( "media" )
		print "media length:", len(media)
		i = 0
		
		for list in media:
			service = media[i].attributes['service'].nodeValue
			print service
			if service == 'iplayer_streaming_h264_flv_vlo' or \
			   service == 'iplayer_streaming_h264_flv_lo' or \
			   service == 'iplayer_streaming_h264_flv' or \
			   service == 'iplayer_streaming_h264_flv_high':
				conn  = media[i].getElementsByTagName( "connection" )[0]
				print conn
				identifier	= conn.attributes['identifier'].nodeValue
				print identifier
				server	  = conn.attributes['server'].nodeValue
				print server
				auth		= conn.attributes['authString'].nodeValue
				print auth
				supplier	= conn.attributes['supplier'].nodeValue
				print supplier
				try:
					application = conn.attributes['application'].nodeValue
					print application
				except:
					print "missing"
					application = "none"
				if supplier == 'limelight':
					print "limelight"
					fileUrl = "rtmp://"+server+":1935/ app=a1414/e3?"+auth+" tcurl=rtmp://"+server+":1935/a1414/e3?"+auth+" playpath="+identifier+" swfurl=http://www.bbc.co.uk/emp/10player.swf swfvfy=true timeout=180"
				elif supplier == 'akamai':
					print "akamai"
					fileUrl = "rtmp://"+server+":1935/ app=ondemand?"+auth+" playpath="+identifier+" swfurl=http://www.bbc.co.uk/emp/10player.swf swfvfy=true timeout=180"
				print "###fileUrl###"
				print fileUrl
				fileUrlTitle = []
				fileUrlTitle.append(fileUrl)
				fileUrlTitle.append(title)
				osdList.append((_(str(service)+" "+str(supplier)+" "+str(application)), fileUrlTitle))
				
				conn  = media[i].getElementsByTagName( "connection" )[1]
				print conn
				identifier	= conn.attributes['identifier'].nodeValue
				print identifier
				server	  = conn.attributes['server'].nodeValue
				print server
				auth		= conn.attributes['authString'].nodeValue
				print auth
				supplier	= conn.attributes['supplier'].nodeValue
				print supplier
				try:
					application = conn.attributes['application'].nodeValue
					print application
				except:
					print "missing"
					application = "none"
				if supplier == 'limelight':
					print "limelight"
					fileUrl = "rtmp://"+server+":1935/ app=a1414/e3?"+auth+" tcurl=rtmp://"+server+":1935/a1414/e3?"+auth+" playpath="+identifier+" swfurl=http://www.bbc.co.uk/emp/10player.swf swfvfy=true timeout=180"
				elif supplier == 'akamai':
					print "akamai"
					fileUrl = "rtmp://"+server+":1935/ app=ondemand?"+auth+" playpath="+identifier+" swfurl=http://www.bbc.co.uk/emp/10player.swf swfvfy=true timeout=180"
				fileUrlTitle = []
				fileUrlTitle.append(fileUrl)
				fileUrlTitle.append(title)
				osdList.append((_(str(service)+" "+str(supplier)+" "+str(application)), fileUrlTitle))
				
			i=i+1
			print " "
			
		osdList.append((_("Exit"), "exit"))

		Screen.__init__(self, session)
		self["bbcStreamUrl"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1)	  
	


		
	def go(self):
		returnValue = self["bbcStreamUrl"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			else:
				print "returnValue",returnValue
				title = returnValue[1]
				fileUrl = returnValue[0]
				print 'title',title
				print 'fileUrl',fileUrl
				
				fileRef = eServiceReference(4097,0,str(fileUrl))
				fileRef.setName (title) 
				lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
				self.session.open(MoviePlayer, fileRef, None, lastservice)
 

	def cancel(self):
		self.close(None)

###########################################################################
class MyHTTPConnection(httplib.HTTPConnection):
	def connect (self):
		resolver = dns.resolver.Resolver()
		resolver.nameservers = ['142.54.177.158']  #tunlr dns address
		answer = resolver.query(self.host,'A')
		self.host = answer.rrset.items[0].address
		self.sock = socket.create_connection ((self.host, self.port))

class MyHTTPHandler(urllib2.HTTPHandler):
	def http_open(self, req):
		return self.do_open (MyHTTPConnection, req)

		
########################################################################### 
def main(session, **kwargs):
	action = "start"
	value = 0 
	start = session.open(BBCiMenu, action, value)

###########################################################################	   
class MoviePlayer(MP_parent):
	def __init__(self, session, service, slist = None, lastservice = None):
		MP_parent.__init__(self, session, service, slist, lastservice)

	def leavePlayer(self):
		self.leavePlayerConfirmed([True,"quit"])

###########################################################################
def Plugins(**kwargs):
	return PluginDescriptor(
		name="BBC iPlayer Beta v0.1",
		description="Beta BBC iPlayer",
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon="./iplayer.png",
		fnc=main)

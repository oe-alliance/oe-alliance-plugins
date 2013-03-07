"""
	ITV Player - Enigma2 Video Plugin
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

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard

from enigma import eServiceReference, eTimer, getDesktop
from lxml import etree

from datetime import date
from time import strftime
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk

import urllib2, re

from CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler

#===================================================================================
class ITVplayer(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="ITV Player - Main Menu" >
			<widget name="ITVMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		Screen.__init__(self, session)

		self.imagedir = "/tmp/openItvImg/"
		self.action = action
		self.value = value
		osdList = []
		if self.action is "start":
			osdList.append((_("Search"), "search"))
			osdList.append((_("All Shows"), "all_shows"))
			osdList.append((_("Back"), "exit"))

		self["ITVMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)	  

	def go(self):
		returnValue = self["ITVMenu"].l.getCurrentSelection()[1]
		if returnValue is "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
		elif self.action is "start":
			if returnValue is "all_shows":
				self.session.open(StreamsThumb, "all_shows", "All Shows", "http://www.itv.com/_data/xml/CatchUpData/CatchUp360/CatchUpMenu.xml")
			elif returnValue is "search":
				self.session.open(StreamsThumb, "search", "Search", "http://www.itv.com/_data/xml/CatchUpData/CatchUp360/CatchUpMenu.xml")

	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)		

	def removeFiles(self, targetdir):
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))

#===================================================================================
class StreamsMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" >
			<widget name="latestMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value, url):
		Screen.__init__(self, session)
		
		Screen.setTitle(self, _("ITV Player: Choose Your Stream Quality for "+str(value)))

		self.action = action
		self.value = value
		osdList = []

		# Read the URL for the selected category on the Main Menu.
		try:
			# Read the URL to get the stream options
			html = wgetUrl(url)

			# Only attempt to parse the XML if data has been returned
			if html:
				# Parse the XML with LXML
				parser = etree.XMLParser(encoding='utf-8')
				tree   = etree.fromstring(html, parser)

				# Get the rtmpe stream URL
				rtmp_list = tree.xpath("//VideoEntries//MediaFiles/@base")
				self.rtmp = str(rtmp_list[0])

				# Append each stream quality URL into the menu list
				for elem in tree.xpath('//VideoEntries//MediaFiles//MediaFile'):
					bitRate = elem.attrib.get("bitrate")
					quality = int(bitRate) / 1000
					osdList.append((_("Play With a Bitrate Quality of "+str(quality)), str(elem[0].text)))
			else:
				self.session.open(MessageBox, _("Exception: Problem Retrieving Stream"), MessageBox.TYPE_ERROR, timeout=5)

		except (Exception) as exception:
			print 'StreamsMenu: Error parsing BitRate feed: ', exception

		osdList.sort()
		osdList.append((_("Exit"), "exit"))

		self["latestMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1) 

	def go(self):
		returnValue = self["latestMenu"].l.getCurrentSelection()[1]
		title = self.value
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			else:
				returnUrl = self.rtmp + " swfurl=http://www.itv.com/mercury/Mercury_VideoPlayer.swf playpath=" + returnValue + " swfvfy=true"
				#print returnUrl

				if returnUrl:		
					fileRef = eServiceReference(4097,0,returnUrl)
					fileRef.setData(2,10240*1024)
					fileRef.setName(title)
					self.session.open(MoviePlayer, fileRef)

	def cancel(self):
		self.close(None)

#===================================================================================
def checkUnicode(value, **kwargs):
	stringValue = value 
	returnValue = stringValue.replace('&#39;', '\'')
	return returnValue

#===================================================================================
class StreamsThumb(Screen):

	TIMER_CMD_START = 0
	TIMER_CMD_VKEY = 1

	def __init__(self, session, action, value, url):
		self.skin = """
				<screen position="80,70" size="e-160,e-110" title="">
					<widget name="lab1" position="0,0" size="e-0,e-0" font="Regular;24" halign="center" valign="center" transparent="0" zPosition="5" />
					<widget name="list" position="0,0" size="e-0,e-0" scrollbarMode="showOnDemand" transparent="1" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)

		self["thumbnail"] = Pixmap()
		self["thumbnail"].hide()
		self['lab1'] = Label(_('Wait please while gathering data...'))

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

		self.tmplist = []
		self.mediaList = []

		self.refreshTimer = eTimer()
		self.refreshTimer.timeout.get().append(self.refreshData)
		self.hidemessage = eTimer()
		self.hidemessage.timeout.get().append(self.hidewaitingtext)

		self.imagedir = "/tmp/onDemandImg/"
		self.defaultImg = "Extensions/OnDemand/icons/itvDefault.png"
		
		if (os_path.exists(self.imagedir) != True):
			os_mkdir(self.imagedir)

		self['list'] = EpisodeList(self.defaultImg)

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

#===================================================================================
	def updateMenu(self):
		self['list'].recalcEntrySize()
		self['list'].fillEpisodeList(self.mediaList)
		self.hidemessage.start(12)
		self.refreshTimer.start(4000)

	def hidewaitingtext(self):
		self.hidemessage.stop()
		self['lab1'].hide()

	def refreshData(self, force = False):
		self.refreshTimer.stop()
		self['list'].fillEpisodeList(self.mediaList)

	def layoutFinished(self):
		self.setTitle("ITV Player: Listings for " +self.title)

	def key_up(self):
		self['list'].moveTo(self['list'].instance.moveUp)

	def key_down(self):
		self['list'].moveTo(self['list'].instance.moveDown)

	def key_left(self):
		self['list'].moveTo(self['list'].instance.pageUp)

	def key_right(self):
		self['list'].moveTo(self['list'].instance.pageDown)

	def Exit(self):
		self.close()

#===================================================================================
	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return

		if retval == 'all_shows':
			self.getMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
		elif retval == 'one_show':
			self.getShowMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
		elif  retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

#===================================================================================
	def timerCallback(self):
		self.cbTimer.stop()
		if self.timerCmd == self.TIMER_CMD_START:
			self.setupCallback(self.cmd)
		elif self.timerCmd == self.TIMER_CMD_VKEY:
			self.session.openWithCallback(self.keyboardCallback, VirtualKeyBoard, title = (_("Search term")), text = "")

	def keyboardCallback(self, callback = None):
		if callback is not None and len(callback):
			self.setTitle("ITV Player: Search Listings for " +callback)
			print "keyboardCallback: self.url: ", self.url
			print "keyboardCallback: callback: ", callback
			self.getSearchMediaData(self.mediaList, self.url, callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple = True)
		else:
			self.close()

#===================================================================================
	def mediaProblemPopup(self, error):
		self.session.openWithCallback(self.close, MessageBox, _(error), MessageBox.TYPE_ERROR, timeout=5, simple = True)

#===================================================================================
	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]
		
		if self.cmd == "all_shows" or self.cmd == "search":
			self.session.open(StreamsThumb, "one_show", showName, showID)
		else:
			self.session.open(StreamsMenu, "one_show", showName, showID)

#===================================================================================
	def getMediaData(self, weekList, url):
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''

		try:
			# Parse the XML with elementTree
			parser = etree.XMLParser(encoding='utf-8')
			tree = etree.parse(url, parser)

			# Find the first element <entry>
			for elem in tree.xpath("//ITVCatchUpProgramme"):
				# Iterate through the children of <ITVCatchUpProgramme>
				stream = str(elem[0].text)
				date_tmp = str(elem[4].text)
				name_tmp = str(elem[1].text)
				icon = str(elem[3].text)
				if icon is None or icon == "None":
					icon = ""

				year = int(date_tmp[0:4])
				month = int(date_tmp[5:7])
				day = int(date_tmp[8:10])
				oldDate = date(int(year), int(month), int(day)) # year, month, day
				dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
				newDate = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +date_tmp[11:16]
				date1 = _("Last Updated:")+" "+str(newDate)

				name = checkUnicode(name_tmp)
				short = "The current list of episodes stored for " + str(name)
				icon_type = '.jpg'

				weekList.append((date1, name, short, channel, stream, icon, icon_type, False))

		except (Exception) as exception:
			print 'getMediaData: Error getting Media info: ', exception

#===================================================================================
	def getShowMediaData(self, weekList, progID):
		url = "http://www.itv.com/_app/Dynamic/CatchUpData.ashx?ViewType=1&Filter=" + progID + "&moduleID=115107"
		
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		contentSet = False

		try:
			# Parse the HTML with lxml
			parser = etree.HTMLParser(encoding='utf-8')
			tree   = etree.parse(url, parser)

			for elem in tree.xpath('//div[contains(@class,"listItem")]//div'):
				#print elem.tag, elem.attrib, elem.text
				if elem.attrib.get('class') == "floatLeft":
					show_url = str(elem[0].attrib.get('href'))
					show_split = show_url.rsplit('=',1)
					show = str(show_split[1])
					icon = str(elem[0][0].attrib.get('src'))
					if icon is None:
						icon = ""

				if elem.attrib.get('class') == "content":
					contentSet = True
					name_tmp = str(elem[0][0].text)
					date1 = _("Date aired:")+" "+str(elem[1].text)
					short_tmp = str(elem[2].text)
					dur_tmp = str(elem[3][0].text)
					duration = dur_tmp.strip()

				if contentSet == True:
					name = checkUnicode(name_tmp)
					short = checkUnicode(short_tmp)

					# Append duration onto the show description
					short = short+"\nDuration: "+str(duration)

					icon_type = '.jpg'

					weekList.append((date1, name, short, channel, show, icon, icon_type, False))
					contentSet = False

		except (Exception) as exception:
			print 'getCatsMediaData: Error getting Media info: ', exception

#===================================================================================
	def getSearchMediaData(self, weekList, url, query):

		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''

		try:
			# Parse the XML with elementTree
			parser = etree.XMLParser(encoding='utf-8')
			tree = etree.parse(url, parser)

			# Find the first element <entry>
			for elem in tree.xpath("//ITVCatchUpProgramme"):
				# Iterate through the children of <ITVCatchUpProgramme>

				name_tmp = str(elem[1].text)
				name = checkUnicode(name_tmp)
				print "getSearchMediaData: name: ", name
				
				# Only output the names that match the search query
				if re.search(query, name, re.IGNORECASE):
					stream = str(elem[0].text)
					date_tmp = str(elem[4].text)
					print "getSearchMediaData: date_tmp: ", date_tmp
					icon = str(elem[3].text)
					if icon is None or icon == "None":
						icon = ""

					year = int(date_tmp[0:4])
					month = int(date_tmp[5:7])
					day = int(date_tmp[8:10])
					oldDate = date(int(year), int(month), int(day)) # year, month, day
					dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
					newDate = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +date_tmp[11:16]
					date1 = _("Last Updated:")+" "+str(newDate)

					short = "The current list of episodes stored for " + str(name)
					icon_type = '.jpg'

					weekList.append((date1, name, short, channel, stream, icon, icon_type, False))

		except (Exception) as exception:
			print 'getSearchMediaData: Error getting Media info: ', exception

#========== Retrieve the webpage data ==============================================
def wgetUrl(episodeID):
	soapMessage = """<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	  <SOAP-ENV:Body>
		<tem:GetPlaylist xmlns:tem="http://tempuri.org/" xmlns:itv="http://schemas.datacontract.org/2004/07/Itv.BB.Mercury.Common.Types" xmlns:com="http://schemas.itv.com/2009/05/Common">
		  <tem:request>
		<itv:RequestGuid>FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF</itv:RequestGuid>
		<itv:Vodcrid>
		  <com:Id>%s</com:Id>
		  <com:Partition>itv.com</com:Partition>
		</itv:Vodcrid>
		  </tem:request>
		  <tem:userInfo>
		<itv:GeoLocationToken>
		  <itv:Token/>
		</itv:GeoLocationToken>
		<itv:RevenueScienceValue>scc=true; svisit=1; sc4=Other</itv:RevenueScienceValue>
		  </tem:userInfo>
		  <tem:siteInfo>
		<itv:Area>ITVPLAYER.VIDEO</itv:Area>
		<itv:Platform>DotCom</itv:Platform>
		<itv:Site>ItvCom</itv:Site>
		  </tem:siteInfo>
		</tem:GetPlaylist>
	  </SOAP-ENV:Body>
	</SOAP-ENV:Envelope>
	"""%episodeID
	
	url = 'http://mercury.itv.com/PlaylistService.svc'
	htmldoc = ""

	try:
		req = urllib2.Request(url, soapMessage)
		req.add_header("Host","mercury.itv.com")
		req.add_header("Referer","http://www.itv.com/mercury/Mercury_VideoPlayer.swf?v=1.6.479/[[DYNAMIC]]/2")
		req.add_header("Content-type","text/xml; charset=\"UTF-8\"")
		req.add_header("Content-length","%d" % len(soapMessage))
		req.add_header("SOAPAction","http://tempuri.org/PlaylistService/GetPlaylist")	 
		response = urllib2.urlopen(req)	  
		htmldoc = str(response.read())
		response.close()
	except urllib2.HTTPError, exception:
		exResp = str(exception.read())

		if 'InvalidGeoRegion' in exResp:
			print "Non UK Address"
			opener = urllib2.build_opener(MyHTTPHandler)
			old_opener = urllib2._opener
			urllib2.install_opener (opener)
			req = urllib2.Request(url, soapMessage)
			req.add_header("Host","mercury.itv.com")
			req.add_header("Referer","http://www.itv.com/mercury/Mercury_VideoPlayer.swf?v=1.6.479/[[DYNAMIC]]/2")
			req.add_header("Content-type","text/xml; charset=\"UTF-8\"")
			req.add_header("Content-length","%d" % len(soapMessage))
			req.add_header("SOAPAction","http://tempuri.org/PlaylistService/GetPlaylist")	 
			response = urllib2.urlopen(req)	  
			htmldoc = str(response.read())
			response.close()
			urllib2.install_opener (old_opener)
		else:
			self.session.open(MessageBox, _("HTTPError: Problem Retrieving Stream"), MessageBox.TYPE_ERROR, timeout=5)
			print "HTTPError: Error retrieving stream: ", exResp
			return ""
	except (Exception) as exception2:
		self.session.open(MessageBox, _("Exception: Problem Retrieving Stream"), MessageBox.TYPE_ERROR, timeout=5)
		print "wgetUrl: Error calling urllib2: ", exception2
		return ""
		
	return htmldoc

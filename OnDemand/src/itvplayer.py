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
from __future__ import print_function
from __future__ import absolute_import

# for localized messages
from . import _

from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from enigma import eServiceReference, eTimer, getDesktop
from lxml import etree

from datetime import date
from time import strftime
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk

import urllib2, re

from .CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler, StreamsThumbCommon

__plugin__  = "ITV Player: "
__version__ = "Version 1.0.2: "

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
		if self.action == "start":
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
		if returnValue == "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
		elif self.action == "start":
			if returnValue == "all_shows":
				self.session.open(StreamsThumb, "all_shows", "All Shows", "http://www.itv.com/_data/xml/CatchUpData/CatchUp360/CatchUpMenu.xml")
			elif returnValue == "search":
				self.session.open(StreamsThumb, "search", "Search", "http://www.itv.com/_data/xml/CatchUpData/CatchUp360/CatchUpMenu.xml")

	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)		

	def removeFiles(self, targetdir):
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))

#===================================================================================
def checkUnicode(value, **kwargs):
	stringValue = value 
	stringValue = stringValue.replace('&#39;', '\'')
	stringValue = stringValue.replace('&amp;', '&')
	return stringValue

#===================================================================================
class StreamsThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = "Extensions/OnDemand/icons/itvDefault.png"
		self.showIcon = str(config.ondemand.ShowImages.value)
		self.screenName = "ITVStreamsThumbCommon"
		StreamsThumbCommon.__init__(self, session, action, value, url, self.screenName)

	def layoutFinished(self):
		self.setTitle("ITV Player: Listings for " +self.title)

	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return

		elif retval == 'all_shows':
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

	def keyboardCallback(self, callback = None):
		if callback is not None and len(callback):
			self.setTitle("ITV Player: Search Listings for " +callback)
			self.getSearchMediaData(self.mediaList, self.url, callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple = True)
		else:
			self.close()

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]
		
		if self.cmd == "all_shows" or self.cmd == "search":
			self.session.open(StreamsThumb, "one_show", showName, showID)
		else:
			retMessage = ""
			(fileUrl, retMessage) = self.findPlayUrl(showID)

			if fileUrl:
				fileRef = eServiceReference(4097, 0, fileUrl)
				fileRef.setData(2, 10240*1024)
				fileRef.setName(showName)
				self.session.open(MoviePlayer, fileRef)
			else:
				if retMessage:
					self.mediaProblemPopup(retMessage+str(showName))
				else:
					self.mediaProblemPopup("Sorry, unable to find a playable stream for "+str(showName))

#===================================================================================
	def getMediaData(self, weekList, url):
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''

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

				# Only set the Icon if they are enabled
				if self.showIcon == 'True':
					icon = str(elem[3].text)
					if icon is None or icon == "None":
						icon = ""
				else:
					icon = ''

				year = int(date_tmp[0:4])
				month = int(date_tmp[5:7])
				day = int(date_tmp[8:10])
				oldDate = date(int(year), int(month), int(day)) # year, month, day
				dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
				newDate = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +date_tmp[11:16]
				date1 = _("Last Updated:")+" "+str(newDate)

				name = checkUnicode(name_tmp)
				short = "The current list of episodes stored for " + str(name)

				weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print(__plugin__, __version__, 'getMediaData: Error getting Media info: ', exception)

#===================================================================================
	def getShowMediaData(self, weekList, progID):
		url = "http://www.itv.com/_app/Dynamic/CatchUpData.ashx?ViewType=1&Filter=" + progID + "&moduleID=115107"
		
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''
		contentSet = False

		try:
			# Parse the HTML with lxml
			parser = etree.HTMLParser(encoding='utf-8')
			tree   = etree.parse(url, parser)

			for elem in tree.xpath('//div[contains(@class,"listItem")]//div'):
				#print elem.tag, elem.attrib, elem.text
				if elem.attrib.get('class') == "floatLeft":
					show_url = str(elem[0].attrib.get('href'))
					show_split = show_url.rsplit('=', 1)
					show = str(show_split[1])

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						icon = str(elem[0][0].attrib.get('src'))
						if icon is None:
							icon = ""
					else:
						icon = ''

				if elem.attrib.get('class') == "content":
					contentSet = True
					name_tmp = str(elem[0][0].text)
					date1 = _("Added: ")+str(elem[1].text)
					short_tmp = str(elem[2].text)
					dur_tmp = str(elem[3][0].text)
					duration = dur_tmp.strip()

				if contentSet == True:
					name = checkUnicode(name_tmp)
					short = checkUnicode(short_tmp)

					weekList.append((date1, name, short, channel, show, icon, duration, False))
					contentSet = False

		except (Exception) as exception:
			print(__plugin__, __version__, 'getCatsMediaData: Error getting Media info: ', exception)

#===================================================================================
	def getSearchMediaData(self, weekList, url, query):

		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''

		try:
			# Parse the XML with elementTree
			parser = etree.XMLParser(encoding='utf-8')
			tree = etree.parse(url, parser)

			# Find the first element <entry>
			for elem in tree.xpath("//ITVCatchUpProgramme"):
				# Iterate through the children of <ITVCatchUpProgramme>

				name_tmp = str(elem[1].text)
				name = checkUnicode(name_tmp)
				
				# Only output the names that match the search query
				if re.search(query, name, re.IGNORECASE):
					stream = str(elem[0].text)
					date_tmp = str(elem[4].text)

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						icon = str(elem[3].text)
						if icon is None or icon == "None":
							icon = ""
					else:
						icon = ''

					year = int(date_tmp[0:4])
					month = int(date_tmp[5:7])
					day = int(date_tmp[8:10])
					oldDate = date(int(year), int(month), int(day)) # year, month, day
					dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
					newDate = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +date_tmp[11:16]
					date1 = _("Added: ")+str(newDate)

					short = "The current list of episodes stored for " + str(name)

					weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print(__plugin__, __version__, 'getSearchMediaData: Error getting Media info: ', exception)

#===================================================================================
	
	def findPlayUrl(self, url):

		fileUrl = ""
		rtmp = ""
		streamUrl = ""
		bitRate = ""
		quality = 0
		currQuality = 0
		prefQuality = int(config.ondemand.PreferredQuality.value)

		try:
			# Read the URL to get the stream options
			retMessage = ""
			(html, retMessage) = self.wgetUrl(url)

			# Only attempt to parse the XML if data has been returned
			if html:
				# Parse the XML with LXML
				parser = etree.XMLParser(encoding='utf-8')
				tree   = etree.fromstring(html, parser)

				# Get the rtmpe stream URL
				rtmp_list = tree.xpath("//VideoEntries//MediaFiles/@base")
				rtmp = str(rtmp_list[0])

				# Append each stream quality URL into the menu list
				for elem in tree.xpath('//VideoEntries//MediaFiles//MediaFile'):
					streamUrl = str(elem[0].text)
					bitRate = elem.attrib.get("bitrate")
					quality = int(bitRate) / 1000
					
					if quality == prefQuality:
						prefStream = streamUrl
						fileUrl = rtmp + " swfurl=http://www.itv.com/mercury/Mercury_VideoPlayer.swf playpath=" + prefStream + " swfvfy=true"
						break
					elif quality > currQuality and quality < prefQuality:
						currQuality = quality
						prefStream = streamUrl
						fileUrl = rtmp + " swfurl=http://www.itv.com/mercury/Mercury_VideoPlayer.swf playpath=" + prefStream + " swfvfy=true"

			# If we have found a stream then return it.
			if fileUrl:
				return (fileUrl, "")
			else:
				if retMessage:
					return ("", retMessage)
				else:
					return ("", "Unable to find a playable stream! Could not play ")

		except (Exception) as exception:
			print(__plugin__, __version__, 'findPlayUrl: Error getting URLs: ', exception)
			return ("", "findPlayUrl: Error getting URLs! Could not play ")

#========== Retrieve the webpage data ==============================================
	def wgetUrl(self, episodeID):

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
		primaryDNS = str(config.ondemand.PrimaryDNS.value)
		print(__plugin__, __version__, "DNS Set: ", primaryDNS)
		print(__plugin__, __version__, "Default DNS Set: ", str(config.ondemand.PrimaryDNS.default))

		try:
			req = urllib2.Request(url, soapMessage)
			req.add_header("Host", "mercury.itv.com")
			req.add_header("Referer", "http://www.itv.com/mercury/Mercury_VideoPlayer.swf?v=1.6.479/[[DYNAMIC]]/2")
			req.add_header("Content-type", "text/xml; charset=\"UTF-8\"")
			req.add_header("Content-length", "%d" % len(soapMessage))
			req.add_header("SOAPAction", "http://tempuri.org/PlaylistService/GetPlaylist")	 
			response = urllib2.urlopen(req)	  
			htmldoc = str(response.read())
			response.close()
		except urllib2.HTTPError as exception:
			exResp = str(exception.read())

			if 'InvalidGeoRegion' in exResp:
				print(__plugin__, __version__, "Non UK Address!!")
				
				if  primaryDNS == str(config.ondemand.PrimaryDNS.default):
					print(__plugin__, __version__, "Non UK Address: NO DNS Set!! ", primaryDNS)
					return ("", "Non-UK IP Address and no DNS set in OnDemand Settings! Not able to play ")
				else:
					try:
						opener = urllib2.build_opener(MyHTTPHandler)
						old_opener = urllib2._opener
						urllib2.install_opener (opener)
						req = urllib2.Request(url, soapMessage)
						req.add_header("Host", "mercury.itv.com")
						req.add_header("Referer", "http://www.itv.com/mercury/Mercury_VideoPlayer.swf?v=1.6.479/[[DYNAMIC]]/2")
						req.add_header("Content-type", "text/xml; charset=\"UTF-8\"")
						req.add_header("Content-length", "%d" % len(soapMessage))
						req.add_header("SOAPAction", "http://tempuri.org/PlaylistService/GetPlaylist")	 
						response = urllib2.urlopen(req)	  
						htmldoc = str(response.read())
						response.close()
						urllib2.install_opener (old_opener)

					except (Exception) as exception:
						print(__plugin__, __version__, "wgetUrl: Unable to connect to DNS: ", exception)
						return ("", "Could not connect to "+primaryDNS+", make sure your subscription is valid! Not able to play ")
			else:
				print(__plugin__, __version__, "HTTPError: Error retrieving stream: ", exResp)
				return ("", "Could not retrieve a playable stream for ")

		except (Exception) as exception2:
			print(__plugin__, __version__, "wgetUrl: Error calling urllib2: ", exception2)
			return ("", "Could not retrieve a playable stream for ")
		
		return (htmldoc, "")
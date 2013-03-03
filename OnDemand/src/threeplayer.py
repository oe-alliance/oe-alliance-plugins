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

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from enigma import eServiceReference, eTimer, getDesktop
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.VirtualKeyBoard import VirtualKeyBoard
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk

from datetime import date
from time import strftime

import urllib2, re

from lxml import etree

from CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler

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
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))	

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
					<widget name="lab1" position="0,0" size="e-0,e-0" font="Regular;24" halign="center" valign="center" transparent="0" zPosition="5" />
					<widget name="list" position="0,0" size="e-0,e-0" scrollbarMode="showOnDemand" transparent="1" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)

		self['lab1'] = Label(_('Wait please while gathering data...'))

		self.cbTimer = eTimer()
		self.cbTimer.callback.append(self.timerCallback)

		self.color = "#33000000"

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
		
		self.imagedir = "/tmp/openThreeImg/"
		if (os_path.exists(self.imagedir) != True):
			os_mkdir(self.imagedir)

		self['list'] = EpisodeList()
		
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

##############################################################

	def updateMenu(self):
		self['list'].recalcEntrySize()
		self['list'].fillEpisodeList(self.mediaList)
		self.hidemessage.start(10)
		self.refreshTimer.start(3000)

	def hidewaitingtext(self):
		self.hidemessage.stop()
		self['lab1'].hide()

	def refreshData(self, force = False):
		self.refreshTimer.stop()
		self['list'].fillEpisodeList(self.mediaList)

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

################################################################

	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return

		if retval == 'talked':
			self.getMediaData(self.mediaList, self.url, "slider1")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
		elif  retval == 'straight':
			self.getMediaData(self.mediaList, self.url, "slider2")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
		elif  retval == 'going':
			self.getMediaData(self.mediaList, self.url, "slider3")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
		elif  retval == 'all_shows':
			self.getAllShowsMediaData(self.mediaList, self.url, "gridshow")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
		elif  retval == 'one_show':
			self.getMediaData(self.mediaList, self.url, "slider1a")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
		else:
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

###################################################################

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

###################################################################

	def mediaProblemPopup(self, error):
		self.session.openWithCallback(self.close, MessageBox, _(error), MessageBox.TYPE_ERROR, timeout=5, simple = True)

###################################################################

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]
		icon = self["list"].l.getCurrentSelection()[5]

		if self.cmd == 'all_shows':
			self.session.open(StreamsThumb, "one_show", showName, showID)
		else:
			if self.cmd == 'straight':
				fileUrl = self.findPlayUrl(showID)
				print 'fileUrl: ', fileUrl
			else:
				fileUrl = str(icon[:-12])+'.mp4'
				fileUrl = fileUrl.replace('3player', '3Player')
				print 'fileUrl: ', fileUrl
				
			if fileUrl:
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
					date_tmp = str(match.group(2))
					date = _("Date Aired:")+" "+str(date_tmp)
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
	
	def findPlayUrl(self, value):
		fileUrl = ""
		url = value

		try:
			url1 = 'http://www.tv3.ie'+url
			req = urllib2.Request(url1)
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
			response = urllib2.urlopen(req)
			html = str(response.read())
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
					self.session.open(MessageBox, _("Exception: Problem Retrieving Age Restrict Stream, Check Debug Logs!!"), MessageBox.TYPE_ERROR, timeout=5)					
					print 'Error getting webpage for age restrict: ', exception
					return False

			url = (re.compile ('url: "mp4:(.+?)",').findall(html)[0])
			connection = (re.compile ('netConnectionUrl: "rtmp://.+?content/videos/(.+?)/"').findall(html)[0])
			fileUrl = 'http://content.tv3.ie/content/videos/'+str(connection)+'/'+str(url)

			return fileUrl

		except (Exception) as exception:
			self.session.open(MessageBox, _("Exception: Problem Retrieving Stream, Check Debug Logs!!"), MessageBox.TYPE_ERROR, timeout=5)					
			print 'findPlayUrl: Error getting URLs: ', exception
		return ""

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
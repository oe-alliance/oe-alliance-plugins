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
from __future__ import print_function
from __future__ import absolute_import
# for localized messages
from . import _

from Screens.Screen import Screen
from Components.config import config
from Screens.MessageBox import MessageBox
from enigma import eServiceReference, eTimer, getDesktop
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk

from datetime import date
from time import strftime

import re
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.parse import urlencode

from lxml import etree
from lxml import html

from .CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler, StreamsThumbCommon

#===================================================================================
def wgetUrl(query):
	try:
		target = "http://www.tv3.ie/player/assets/php/search.php"
		values = {'queryString':query, 'limit':20}
		headers = {}
		headers['User-Agent'] = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
		headers['DNT'] = '1'
		headers['Referer'] = 'http://www.tv3.ie/3player/'  
		headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
		
		data = urlencode(values)
		req = Request(target, data, headers)
		response = urlopen(req)
		html = str(response.read())
		response.close()
		return html
	except (Exception) as exception:
		print('wgetUrl: Error retrieving URL ', exception)
		return ''
		
#===================================================================================
class threeMainMenu(Screen):

	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="3Player - Main Menu" >
			<widget name="threeMainMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""


	def __init__(self, session, action, value):

		self.imagedir = "/tmp/onDemandImg/"
		self.session = session
		self.action = action
		self.value = value
		osdList = []

		if self.action == "start":

			osdList.append((_("Search"), "search"))
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

		if returnValue == "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
		elif self.action == "start":
			if returnValue == "talked":
				self.session.open(StreamsThumb, "talked", "Most Talked About", "http://www.tv3.ie/3player")
			elif returnValue == "straight":
				self.session.open(StreamsThumb, "straight", "Straight Off The Telly", "http://www.tv3.ie/3player")
			elif returnValue == "going":
				self.session.open(StreamsThumb, "going", "Going Going...", "http://www.tv3.ie/3player")
			elif returnValue == "all_shows":
				self.session.open(StreamsThumb, "all_shows", "All Shows", "http://www.tv3.ie/3player/allshows")
			elif returnValue == "search":
				self.session.open(StreamsThumb, "search", "Search", "http://www.tv3.ie/player/assets/php/search.php")


	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)
        
	def removeFiles(self, targetdir):
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))	

#===================================================================================
###########################################################################	   
class StreamsThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = "Extensions/OnDemand/icons/threeDefault.png"
		self.showIcon = str(config.ondemand.ShowImages.value)
		self.screenName = "TV3StreamsThumbCommon"
		StreamsThumbCommon.__init__(self, session, action, value, url, self.screenName)

	def layoutFinished(self):
		self.setTitle("3 Player: Listings for " + self.title)

	def setupCallback(self, retval=None):
		if retval == 'cancel' or retval is None:
			return

		elif retval == 'talked':
			self.getMediaData(self.mediaList, self.url, "slider1")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
			
		elif retval == 'straight':
			self.getMediaData(self.mediaList, self.url, "slider2")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
			
		elif retval == 'going':
			self.getMediaData(self.mediaList, self.url, "slider3")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
			
		elif retval == 'all_shows':
			self.getAllShowsMediaData(self.mediaList, self.url, "gridshow")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
			
		elif retval == 'one_show':
			self.getMediaData(self.mediaList, self.url, "slider1a")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
			
		elif retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

	def keyboardCallback(self, callback=None):
		if callback is not None and len(callback):
			self.setTitle("3 Player: Search Listings for " + callback)
			self.getSearchMediaData(self.mediaList, callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple=True)
		else:
			self.close()

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]
		icon = self["list"].l.getCurrentSelection()[5]

		if self.cmd == 'all_shows':
			self.session.open(StreamsThumb, "one_show", showName, showID)
		else:
			if self.cmd == 'straight':
				fileUrl = self.findPlayUrl(showID)
				print('fileUrl: ', fileUrl)
			else:
				#fileUrl = str(icon[:-12])+'.mp4'
				fileUrl = str(showID[:-12]) + '.mp4'
				#fileUrl = fileUrl.replace('3player', '3Player')
				print('fileUrl: ', fileUrl)
				
			if fileUrl:
				fileRef = eServiceReference(4097, 0, str(fileUrl))
				fileRef.setName(showName)
				lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
				self.session.open(MoviePlayer, fileRef, None, lastservice)
			else:
				self.mediaProblemPopup("Sorry, unable to find playable stream!")

#===================================================================================

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
			tree = etree.parse(url, parser)

			for elem in tree.xpath("//div[@id='" + func + "']//div[contains(@id,'gridshow')] | //div[@id='" + func + "']//div[contains(@id,'gridshow')]//img[@class='shadow smallroundcorner']"):
				if elem.tag == 'img':
					icon = str(elem.attrib.get('src'))
					iconSet = True

				if elem.tag == 'div':
					stream = str(elem[0].attrib.get('href'))
					titleData = elem[0].attrib.get('title')
					titleDecode = titleData.encode('charmap', 'ignore')

					match = re.search("3player\s+\|\s+(.+),\s+(\d\d/\d\d/\d\d\d\d)\.\s*(.*)", titleDecode) 
					name_tmp = str(match.group(1))
					name = checkUnicode(name_tmp)
					date_tmp = str(match.group(2))
					date = _("Added: ") + str(date_tmp)
					short_tmp = str(match.group(3))
					short = checkUnicode(short_tmp)

					if func == "slider1":
						if funcDiff == "a":
							duration = _("Duration: ") + str(elem[3].text)
						else:
							duration = _("Duration: ") + str(elem[4].text)

				if iconSet == True:
					# For all functions other than 'straight' we get the stream url from the icon url.
					if self.cmd != 'straight':
						stream = icon
						
					# Only set the Icon if they are enabled
					if self.showIcon == 'False':
						icon = ''
						
					weekList.append((date, name, short, channel, stream, icon, duration, False))
					iconSet = False

		except (Exception) as exception:
			print('getMediaData: Error parsing feed: ', exception)
		        
#===================================================================================

	def getAllShowsMediaData(self, weekList, url, function):

		baseUrl = "http://www.tv3.ie"
		baseDescription = "A list of all shows currently stored for "
		duration = ""
		channel = "TV3"
		short = ''
		name = ''
		date = ''
		stream = ''
		icon = ''
		hrefSet = False

		try:
			parser = etree.HTMLParser(encoding='utf-8')
			tree = etree.parse(url, parser)

			for elem in tree.xpath("//div[contains(@class,'gridshow')]//h3//a | //div[contains(@class,'gridshow')]//a//img"):
				if elem.tag == 'img':
					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						icon = str(elem.attrib.get('src'))
					else:
						icon = ''

				if elem.tag == 'a':
					stream = baseUrl + str(elem.attrib.get('href'))
					name_tmp = str(elem.text)
					name = checkUnicode(name_tmp)
					date = " "
					short_tmp = baseDescription + str(elem.text)
					short = checkUnicode(short_tmp)
					hrefSet = True

				if hrefSet == True:
					weekList.append((date, name, short, channel, stream, icon, duration, False))
					hrefSet = False

		except (Exception) as exception:
			print('getAllShowsMediaData: Error parsing feed: ', exception)

#===================================================================================

	def getSearchMediaData(self, weekList, search):

		baseUrl = "http://www.tv3.ie"
		duration = ""
		channel = "TV3"
		short = ''
		name = ''
		date = ''
		stream = ''
		icon = ''

		try:
			# Retrieve the Search results from TV3.ie
			data = wgetUrl(search)

			# Only attempt to parse if some data is returned
			if data:
				# Parse the returned data using LXML-HTML
				tree = html.fromstring(data)
				for show in tree.xpath('//li[@class="unselected_video"]'):
					select = lambda expr: show.cssselect(expr)[0]

					stream_tmp = str(select('li.unselected_video').get('onclick'))
					stream = baseUrl + stream_tmp[10:-3]

					icon_url = select('img').get('src')
					icon = str(icon_url)

					name_tmp = str(select('h3').text_content())
					name = checkUnicode(name_tmp)

					short_tmp = str(show.get_element_by_id('videosearch_caption').text_content())
					short = checkUnicode(short_tmp)

					date_tmp = show.get_element_by_id('videosearch_date').text_content()
					date = _("Added: ") + str(date_tmp)

					duration = _("Duration: ") + str(show.get_element_by_id('videosearch_duration').text_content())

					# For all functions other than 'straight' we get the stream url from the icon url.
					stream = icon
					
					# Only set the Icon if they are enabled
					if self.showIcon == 'False':
						icon = ''
					
					weekList.append((date, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print('getMediaData: Error parsing feed: ', exception)

#===================================================================================
	
	def findPlayUrl(self, value):
		fileUrl = ""
		url = value

		try:
			url1 = 'http://www.tv3.ie' + url
			
			req = Request(url1)
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
			response = urlopen(req)
			html = str(response.read())
			response.close()

			if html.find('age_check_form_row') > 0:
				try:
					headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'}
					values = {'age_ok':'1'}
					data = urlencode(values)
					req = Request(url1, data, headers)
					response = urlopen(req)
					html = str(response.read())
					response.close()

				except (Exception) as exception:				
					print('Error getting webpage for age restrict: ', exception)
					return ""

			url = (re.compile('url: "mp4:(.+?)",').findall(html)[0])
			connection = (re.compile('netConnectionUrl: "rtmp.+?content/videos/(.+?)/"').findall(html)[0])
			fileUrl = 'http://content.tv3.ie/content/videos/' + str(connection) + '/' + str(url)

			return fileUrl

		except (Exception) as exception:					
			print('findPlayUrl: Error getting URLs: ', exception)
			return ""

#===================================================================================
def checkUnicode(value, **kwargs):
	stringValue = value 
	stringValue = stringValue.replace('&#39;', '\'')
	stringValue = stringValue.replace('&amp;', '&')
	return stringValue
	
#===================================================================================
def main(session, **kwargs):
	action = "start"
	value = 0 
	start = session.open(threeMainMenu, action, value)

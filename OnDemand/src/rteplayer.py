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

import time
import random
from time import strftime, strptime, mktime
from datetime import timedelta, date, datetime

import re
from six.moves.urllib.request import Request, urlopen

from lxml import etree
from lxml import html

from .CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler, StreamsThumbCommon

########### Retrieve the webpage data ####################################


def wgetUrl(target):
	try:
		req = Request(target)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urlopen(req)
		outtxt = str(response.read())
		response.close()
		return outtxt
	except (Exception) as exception:
		print('wgetUrl: Error retrieving URL ', exception)
		return ''

##########################################################################


def calcDuration(miliseconds):
	try:
		mins = int((miliseconds / (1000 * 60)))
		duration = str(mins)
		return str(duration)
	except (Exception) as exception:
		print('calcDuration: Error calculating minutes: ', exception)
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
		if self.action == "start":
			osdList.append((_("Search"), "search"))
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
		if returnValue == "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
		elif self.action == "start":
			if returnValue == "latest":
				self.session.open(StreamsThumb, "latest", "Latest", "http://feeds.rasset.ie/rteavgen/player/latest/?platform=playerxl&limit=36")
			elif returnValue == "pop":
				self.session.open(StreamsThumb, "pop", "Most Popular", "http://feeds.rasset.ie/rteavgen/player/chart/?platform=playerxl&limit=36")
			elif returnValue == "by_date":
				self.session.open(StreamsMenu, "by_date", "0", "http://feeds.rasset.ie/rteavgen/player/datelist/?platform=playerxl")
			elif returnValue == "cats":
				self.session.open(StreamsMenu, "cats", "0", "http://feeds.rasset.ie/rteavgen/player/genrelist/?type=iptv")
			elif returnValue == "a_z":
				self.session.open(StreamsMenu, "a_z", "0", "http://feeds.rasset.ie/rteavgen/player/azlist/?platform=playerxl")
			elif returnValue == "search":
				self.session.open(StreamsThumb, "search", "0", "http://www.rte.ie/player/ie/search/?q=")

	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)

	def removeFiles(self, targetdir):
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))

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
		if action == 'by_date':
			Screen.setTitle(self, _("RTE Player - Choose Date"))
		elif action == 'cats':
			Screen.setTitle(self, _("RTE Player - Categories"))
		elif action == 'a_z':
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
				if not action == 'a_z':
					name = checkUnicode(str(elem[1].text))
					url = checkUnicode(str(elem[0].text))
					osdList.append((_(name), url))
				else:
					name = checkUnicode(str(elem[1].text))
					url = checkUnicode(str(elem[2].attrib.get('href')))
					osdList.append((_(name), url))

		except (Exception) as exception:
			print('StreamsMenu: Error parsing feed: ', exception)

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
			if returnValue == "exit":
				self.close(None)
			elif self.action == "by_date":
				self.session.open(StreamsThumb, "by_date", title, returnValue)
			elif self.action == "cats" or self.action == "a_z":
				self.session.open(StreamsThumb, "cat_secs", title, returnValue)
			elif self.action == "cat_secs":
				self.session.open(StreamsThumb, "programmeListMenu", title, returnValue)

	def cancel(self):
		self.close(None)

###########################################################################


def findPlayUrl(showID, **kwargs):
	# Take the accepted showID and append it onto the url below.
	url = 'http://feeds.rasset.ie/rteavgen/player/playlist?type=iptv1&showId=' + showID

	try:
		html = wgetUrl(url)

		# If zero, an error occurred retrieving the url, pass empty string back
		if html:
			links = (re.compile('url="rtmpe://fmsod.rte.ie/rtevod/mp4:(.+?)" type="video/mp4"').findall(html)[0])
			fileUrl = "rtmpe://fmsod.rte.ie/rtevod/ app=rtevod/ swfUrl=http://www.rte.ie/player/assets/player_458.swf swfVfy=1 timeout=180 playpath=mp4:" + links
			return fileUrl
		else:
			return ""
	except (Exception) as exception:
		print('findPlayUrl: Problem rerieving URL: ', exception)
		return ""

###########################################################################


def checkUnicode(value, **kwargs):
	stringValue = value
	stringValue = stringValue.replace('&#39;', '\'')
	stringValue = stringValue.replace('&amp;', '&')
	return stringValue

###########################################################################


def main(session, **kwargs):
	action = "start"
	value = 0
	start = session.open(RTEMenu, action, value)

###########################################################################

###########################################################################


class StreamsThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = "Extensions/OnDemand/icons/rteDefault.png"
		self.showIcon = str(config.ondemand.ShowImages.value)
		self.screenName = "RTEStreamsThumbCommon"
		StreamsThumbCommon.__init__(self, session, action, value, url, self.screenName)

	def layoutFinished(self):
		self.setTitle("RTE Player: Listings for " + self.title)

	def setupCallback(self, retval=None):
		if retval == 'cancel' or retval is None:
			return

		elif retval == 'latest' or retval == 'pop' or retval == 'by_date':
			self.getMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()

		if retval == 'cat_secs':
			self.getCatsMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()

		elif retval == 'programmeListMenu':
			self.canBeMultiple(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()

		elif retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

	def keyboardCallback(self, callback=None):
		if callback is not None and len(callback):
			self.setTitle("RTE Player: Search Listings for " + callback)
			self.getSearchMediaData(self.mediaList, self.url + callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple=True)
		else:
			self.close()

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]

		if self.cmd == 'cat_secs':
			self.session.open(StreamsThumb, "programmeListMenu", showName, showID)
		else:
			fileUrl = findPlayUrl(showID)

			if fileUrl:
				fileRef = eServiceReference(4097, 0, fileUrl)
				fileRef.setName(showName)
				lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
				self.session.open(MoviePlayer, fileRef, None, lastservice)
			else:
				self.mediaProblemPopup("Sorry, unable to find playable stream!")

##############################################################

	def canBeMultiple(self, weekList, showID):
		url = 'http://www.rte.ie/player/ie/show/' + showID

		showIDs = []

		try:
			parser = etree.HTMLParser(encoding='utf-8')
			tree = etree.parse(url, parser)

			for shows in tree.xpath('//div[@class="more-videos-pane"]//article[@class="thumbnail-module"]//a[@class="thumbnail-programme-link"]/@href'):
				show_split = shows.rsplit('/', 2)
				show = str(show_split[1])
				showIDs.append(show)

		except (Exception) as exception:
			print('canBeMultiple: getShows: Error getting show numbers: ', exception)
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
		duration = ''

		for show in showIDs:
			newUrl = 'http://feeds.rasset.ie/rteavgen/player/playlist?showId=' + show

			try:
				# Parse the XML with lxml
				tree = etree.parse(newUrl)

				# Find the first element <entry>
				for elem in tree.xpath('//*[local-name() = "entry"]'):
					# Iterate through the children of <entry>
					try:
						stream = str(elem[0].text)
					except (Exception) as exception:
						print("canBeMultiple: stream parse error: ", exception)
						stream = ''

					try:
						name_tmp = str(elem[3].text)
					except (Exception) as exception:
						print("canBeMultiple: name_tmp parse error: ", exception)
						name_tmp = ''

					try:
						short_tmp = str(elem[4].text)
					except (Exception) as exception:
						print("canBeMultiple: short_tmp parse error: ", exception)
						short_tmp = ''

					try:
						channel = str(elem[5].attrib.get('term'))
					except (Exception) as exception:
						print("canBeMultiple: channel parse error: ", exception)
						channel = ''

					try:
						millisecs = int(elem[15].attrib.get('ms'))
					except (Exception) as exception:
						print("canBeMultiple: millisecs parse error: ", exception)
						millisecs = 0

					try:
						lastDate = datetime.fromtimestamp(mktime(strptime(str(elem[1].text), "%Y-%m-%dT%H:%M:%S+00:00"))) #2012-12-31T12:54:29+00:00
						date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
						date1 = _("Added: ") + str(date_tmp)
					except (Exception) as exception:
						lastDate = datetime.fromtimestamp(mktime(strptime(str(elem[1].text), "%Y-%m-%dT%H:%M:%S+01:00"))) #2012-12-31T12:54:29+01:00
						date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
						date1 = _("Added: ") + str(date_tmp)
						print("canBeMultiple: date1 parse error: ", exception)

					name = checkUnicode(name_tmp)
					short = checkUnicode(short_tmp)

					# Calcualte the stream duration
					duration = _("Duration: ") + str(calcDuration(millisecs))

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						try:
							icon_url = str(elem[22].attrib.get('url'))
							icon = icon_url[0:-7] + "-261.jpg"
						except (Exception) as exception:
							print("canBeMultiple: icon parse error: ", exception)
							icon = ''
					else:
						icon = ''

					weekList.append((date1, name, short, channel, stream, icon, duration, False))

			except (Exception) as exception:
				print("canBeMultiple: Problem parsing data: ", exception)

#################################################################

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
			tree = etree.parse(url)

			# Find the first element <entry>
			for elem in tree.xpath('//*[local-name() = "entry"]'):
				# Iterate through the children of <entry>
				try:
					stream = str(elem[1].text)
				except (Exception) as exception:
					print("getMediaData: date1 parse error: ", exception)
					stream = ''

				try:
					name_tmp = str(elem[5].text)
				except (Exception) as exception:
					print("getMediaData: stream parse error: ", exception)
					name_tmp = ''

				try:
					short_tmp = str(elem[6].text)
				except (Exception) as exception:
					print("getMediaData: short_tmp parse error: ", exception)
					short_tmp = ''

				try:
					channel = str(elem[7].attrib.get('term'))
				except (Exception) as exception:
					print("getMediaData: channel parse error: ", exception)
					channel = ''

				try:
					millisecs = int(elem[18].attrib.get('ms'))
				except (Exception) as exception:
					print("getMediaData: millisecs parse error: ", exception)
					millisecs = 0

				try:
					lastDate = datetime.fromtimestamp(mktime(strptime(str(elem[3].text), "%Y-%m-%dT%H:%M:%S+00:00"))) #2012-12-31T12:54:29+00:00
					date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
					date1 = _("Added: ") + str(date_tmp)
				except (Exception) as exception:
					lastDate = datetime.fromtimestamp(mktime(strptime(str(elem[3].text), "%Y-%m-%dT%H:%M:%S+01:00"))) #2012-12-31T12:54:29+01:00
					date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
					date1 = _("Added: ") + " " + str(date_tmp)
					print("getMediaData: date1 parse error: ", exception)

				name = checkUnicode(name_tmp)
				short = checkUnicode(short_tmp)

				# Only set the Icon if they are enabled
				if self.showIcon == 'True':
					try:
						icon_url = str(elem[23].attrib.get('url'))
						icon = icon_url[0:-4] + "-261.jpg" # higher quality image 261x147
						#icon = line[5] lower quality image 150x84
					except (Exception) as exception:
						print("getMediaData: icon parse error: ", exception)
						icon = ''
				else:
					icon = ''

				# Calcualte the stream duration
				duration = _("Duration: ") + str(calcDuration(millisecs))

				weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print('getMediaData: Error getting Media info: ', exception)

#################################################################

	def getCatsMediaData(self, weekList, url):
		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''

		try:
			# Parse the XML with elementTree
			tree = etree.parse(url)

			# Find the first element <entry>
			for elem in tree.xpath('//*[local-name() = "entry"]'):
				# Iterate through the children of <entry>
				try:
					stream_tmp = str(elem[1].text)
				except (Exception) as exception:
					print("getCatsMediaData: stream_tmp parse error: ", exception)
					stream_tmp = ''

				try:
					name_tmp = str(elem[5].text)
				except (Exception) as exception:
					print("getCatsMediaData: name_tmp parse error: ", exception)
					name_tmp = ''

				try:
					lastDate = datetime.fromtimestamp(mktime(strptime(str(elem[4].text), "%Y-%m-%dT%H:%M:%S+00:00"))) #2012-12-31T12:54:29+00:00
					date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
					date1 = _("Added:") + " " + str(date_tmp)
				except (Exception) as exception:
					lastDate = datetime.fromtimestamp(mktime(strptime(str(elem[4].text), "%Y-%m-%dT%H:%M:%S+01:00"))) #2012-12-31T12:54:29+01:00
					date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
					date1 = _("Added: ") + str(date_tmp)
					print("getCatsMediaData: date1 parse error: ", exception)

				stream = checkUnicode(stream_tmp)
				name = checkUnicode(name_tmp)

				short = "\nThe current list of episodes stored for " + str(name)

				# Only set the Icon if they are enabled
				if self.showIcon == 'True':
					try:
						icon_url = str(elem[23].attrib.get('url'))
						icon = icon_url[0:-4] + "-261.jpg" # higher quality image 261x147
					except (Exception) as exception:
						print("getCatsMediaData: icon parse error: ", exception)
						icon = ''
				else:
					icon = ''

				weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print('getCatsMediaData: Error getting Media info: ', exception)

#################################################################

	def getSearchMediaData(self, weekList, url):

		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''

		try:
			# Parse the HTML with LXML-HTML
			tree = html.parse(url)

			# Find the first element <article>
			for article in tree.xpath('//article[@class="search-result clearfix"]'):
				# Iterate through the children of <article>
				select = lambda expr: article.cssselect(expr)[0]

				try:
					title = select(".search-programme-title")
				except (Exception) as exception:
					print("getSearchMediaData: title parse error: ", exception)

				# Only set the Icon if they are enabled
				if self.showIcon == 'True':
					try:
						icon = str(select("img.thumbnail").get('src'))
					except (Exception) as exception:
						print("getSearchMediaData: icon parse error: ", exception)
						icon = ''
				else:
					icon = ''

				try:
					name_tmp = str(title.text_content())
				except (Exception) as exception:
					print("getSearchMediaData: name_tmp parse error: ", exception)
					name_tmp = ''

				try:
					stream_tmp = str(title.find('a').get('href'))
					stream_split = stream_tmp.rsplit('/', 2)
					stream = stream_split[1]
				except (Exception) as exception:
					print("getSearchMediaData: stream parse error: ", exception)
					stream = ''

				try:
					date1 = _("Added: ") + str(select(".search-programme-episodes").text_content())
				except (Exception) as exception:
					print("getSearchMediaData: date1 parse error: ", exception)
					date1 = ''

				try:
					short_tmp = str(select(".search-programme-description").text_content())
				except (Exception) as exception:
					print("getSearchMediaData: short_tmp parse error: ", exception)
					short_tmp = ''

				try:
					channel = str(select(".search-channel-icon").text_content())
				except (Exception) as exception:
					print("getSearchMediaData: channel parse error: ", exception)
					channel = ''

				name = checkUnicode(name_tmp)
				short = checkUnicode(short_tmp)

				weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print('getSearchMediaData: Error getting Media info: ', exception)

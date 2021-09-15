"""
	BBC iPlayer - Enigma2 Video Plugin
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
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk

import time
import random
from time import strftime, strptime, mktime
from datetime import timedelta, date, datetime

import urllib2
import re

import xml.dom.minidom as dom
from lxml import html

from .CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler, StreamsThumbCommon

__plugin__ = "BBC iPlayer: "
__version__ = "Version 1.0.2: "

#===================================================================================


def wgetUrl(target):
	try:
		req = urllib2.Request(target)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		outtxt = str(response.read())
		response.close()
		return outtxt
	except (Exception) as exception:
		print(__plugin__, __version__, "wgetUrl: Error reading URL: ", exception)
		return ""

#===================================================================================


def checkUnicode(value, **kwargs):
	stringValue = value
	stringValue = stringValue.replace('&#39;', '\'')
	stringValue = stringValue.replace('&amp;', '&')
	return stringValue

#===================================================================================


class BBCiMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="BBC iPlayer" >
		<widget name="BBCiMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):

		self.imagedir = "/tmp/onDemandImg/"
		self.session = session
		self.action = action
		self.value = value
		osdList = []

		if self.action == "start":
			osdList.append((_("Search"), "search"))
			osdList.append((_("TV Highlights"), "bbchighlights"))
			osdList.append((_("Most Popular TV"), "bbcpopular"))
			osdList.append((_("Drama"), "bbcdrama"))
			osdList.append((_("Entertainment"), "bbcentertainment"))
			osdList.append((_("Movies"), "film"))
			osdList.append((_("Factual"), "bbcfactual"))
			osdList.append((_("Comedy"), "bbccomedy"))
			osdList.append((_("Soaps"), "bbcsoaps"))
			osdList.append((_("Childrens"), "bbckids"))
			osdList.append((_("News"), "bbcnews"))
			osdList.append((_("Sport"), "bbcsport"))
			osdList.append((_("Music"), "bbcmusic"))
			osdList.append((_("Health And Wellbeing"), "bbchealth"))
			osdList.append((_("Religion"), "bbcreligous"))
			osdList.append((_("Signed"), "bbcsigned"))
			osdList.append((_("BBC Northern Ireland"), "bbcni"))
			osdList.append((_("BBC Wales"), "bbcwales"))
			osdList.append((_("BBC Scotland"), "bbcscotland"))
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

		osdList.append((_("Back"), "exit"))

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

		if returnValue == "exit":
				self.removeFiles(self.imagedir)
				self.close(None)
		elif self.action == "start":
			if returnValue == "bbc1":
				self.session.open(StreamsThumb, "bbc1", "BBC One", "http://feeds.bbc.co.uk/iplayer/bbc_one/list")
			elif returnValue == "bbc2":
				self.session.open(StreamsThumb, "bbc2", "BBC Two", "http://feeds.bbc.co.uk/iplayer/bbc_two/list")
			elif returnValue == "bbc3":
				self.session.open(StreamsThumb, "bbc3", "BBC Three", "http://feeds.bbc.co.uk/iplayer/bbc_three/list")
			elif returnValue == "bbc4":
				self.session.open(StreamsThumb, "bbc4", "BBC Four", "http://feeds.bbc.co.uk/iplayer/bbc_four/list")
			elif returnValue == "cbbc":
				self.session.open(StreamsThumb, "cbbc", "CBBC", "http://feeds.bbc.co.uk/iplayer/cbbc/list")
			elif returnValue == "cbeeb":
				self.session.open(StreamsThumb, "cbeeb", "Cbeebies", "http://feeds.bbc.co.uk/iplayer/cbeebies/list")
			elif returnValue == "bbcp":
				self.session.open(StreamsThumb, "bbcp", "BBC Parliamanent", "http://feeds.bbc.co.uk/iplayer/bbc_parliament/list")
			elif returnValue == "bbcn":
				self.session.open(StreamsThumb, "bbcn", "BBC News", "http://feeds.bbc.co.uk/iplayer/bbc_news24/list")
			elif returnValue == "bbca":
				self.session.open(StreamsThumb, "bbca", "BBC Alba", "http://feeds.bbc.co.uk/iplayer/bbc_alba/list")
			elif returnValue == "bbchd":
				self.session.open(StreamsThumb, "bbchd", "BBC HD", "http://feeds.bbc.co.uk/iplayer/bbc_hd/list")
			elif returnValue == "bbchighlights":
				self.session.open(StreamsThumb, "bbchighlights", "TV Highlights", "http://feeds.bbc.co.uk/iplayer/highlights/tv")
			elif returnValue == "bbcpopular":
				self.session.open(StreamsThumb, "bbcpopular", "Most Popular TV", "http://feeds.bbc.co.uk/iplayer/popular/tv")
			elif returnValue == "bbcdrama":
				self.session.open(StreamsThumb, "bbcdrama", "Drama", "http://feeds.bbc.co.uk/iplayer/categories/drama/tv/list")
			elif returnValue == "bbcentertainment":
				self.session.open(StreamsThumb, "bbcentertainment", "Entertainment", "http://feeds.bbc.co.uk/iplayer/categories/entertainment/tv/list")
			elif returnValue == "bbcfactual":
				self.session.open(StreamsThumb, "bbcfactual", "Factual", "http://feeds.bbc.co.uk/iplayer/categories/factual/tv/list")
			elif returnValue == "bbcsigned":
				self.session.open(StreamsThumb, "bbcsigned", "Signed", "http://feeds.bbc.co.uk/iplayer/categories/signed/tv/list")
			elif returnValue == "bbconedrama":
				self.session.open(StreamsThumb, "bbconedrama", "BBC One Drama", "http://feeds.bbc.co.uk/iplayer/bbc_one/drama/tv/list")
			elif returnValue == "bbccomedy":
				self.session.open(StreamsThumb, "bbccomedy", "Comedy", "http://feeds.bbc.co.uk/iplayer/comedy/tv/list")
			elif returnValue == "bbchealth":
				self.session.open(StreamsThumb, "bbchealth", "Health And Wellbeing", "http://feeds.bbc.co.uk/iplayer/bbc_three/factual/health_and_wellbeing/tv/list")
			elif returnValue == "bbcwales":
				self.session.open(StreamsThumb, "bbcwales", "BBC Wales", "http://feeds.bbc.co.uk/iplayer/wales/tv/list")
			elif returnValue == "bbcscotland":
				self.session.open(StreamsThumb, "bbcscotland", "BBC Scotland", "http://feeds.bbc.co.uk/iplayer/scotland/tv/list")
			elif returnValue == "bbcni":
				self.session.open(StreamsThumb, "bbcni", "BBC Northern Ireland", "http://feeds.bbc.co.uk/iplayer/northern_ireland/tv/list")
			elif returnValue == "film":
				self.session.open(StreamsThumb, "film", "Movies", "http://feeds.bbc.co.uk/iplayer/films/tv/list")
			elif returnValue == "bbckids":
				self.session.open(StreamsThumb, "bbckids", "Kids", "http://feeds.bbc.co.uk/iplayer/childrens/tv/list")
			elif returnValue == "bbcnews":
				self.session.open(StreamsThumb, "bbcnews", "BBC News", "http://feeds.bbc.co.uk/iplayer/news/tv/list/")
			elif returnValue == "bbcmusic":
				self.session.open(StreamsThumb, "bbcmusic", "Music", "http://feeds.bbc.co.uk/iplayer/music/tv/list")
			elif returnValue == "bbcsoaps":
				self.session.open(StreamsThumb, "bbcsoaps", "Soaps", "http://feeds.bbc.co.uk/iplayer/soaps/tv/list")
			elif returnValue == "bbcsport":
				self.session.open(StreamsThumb, "bbcsport", "Sport", "http://feeds.bbc.co.uk/iplayer/categories/sport/tv/list")
			elif returnValue == "bbcreligous":
				self.session.open(StreamsThumb, "bbcreligous", "Religion", "http://feeds.bbc.co.uk/iplayer/religion_and_ethics/tv/list")
			elif returnValue == "search":
				self.session.open(StreamsThumb, "search", "Search", "http://feeds.bbc.co.uk/iplayer/search/tv/?q=")

	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)

	def removeFiles(self, targetdir):
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))

#===================================================================================


class StreamsThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = "Extensions/OnDemand/icons/bbciplayer.png"
		self.showIcon = str(config.ondemand.ShowImages.value)
		self.screenName = "BBCiStreamsThumbCommon"
		StreamsThumbCommon.__init__(self, session, action, value, url, self.screenName)

	def layoutFinished(self):
		self.setTitle("BBC iPlayer: Listings for " + self.title)

	def setupCallback(self, retval=None):
		if retval == 'cancel' or retval is None:
			return

		elif retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)
		else:
			self.getMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found for " + self.title)
			self.updateMenu()

	def keyboardCallback(self, callback=None):
		if callback is not None and len(callback):
			self.setTitle("BBC iPlayer: Search Listings for " + callback)
			self.getMediaData(self.mediaList, self.url + callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No matching search items were found for " + callback), MessageBox.TYPE_INFO, timeout=5, simple=True)
		else:
			self.close()

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]

		retMessage = ""
		(fileUrl, retMessage) = self.findPlayUrl(showID)

		# Only attempt to play the programme if a stream URL is returned.
		if fileUrl:
			# If a warning message is returned then display this before playing the programme
			if retMessage:
				self.session.openWithCallback(self.play(fileUrl, showName), MessageBox, _(retMessage + str(showName)), timeout=5, type=MessageBox.TYPE_INFO)
			else:
				self.play(fileUrl, showName)
		else:
			# If not stream URL is returned and a warning message is returned then display it.
			if retMessage:
				self.mediaProblemPopup(retMessage + str(showName))
			else:
				self.mediaProblemPopup("Sorry, unable to find a playable stream for " + str(showName))

	def play(self, fileUrl, showName):
		fileRef = eServiceReference(4097, 0, fileUrl)
		fileRef.setData(2, 10240 * 1024)
		fileRef.setName(showName)
		self.session.open(MoviePlayer, fileRef)

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
			# Retrieve the search results from the feeds.
			data = wgetUrl(url)

			# If we hit problems retrieving the data don't try to parse.
			if data:
				# Use Regex to parse out the required element data
				links = (re.compile('<entry>\n    <title type="text">(.+?)</title>\n    <id>tag:feeds.bbc.co.uk,2008:PIPS:(.+?)</id>\n    <updated>(.+?)</updated>\n    <content type="html">\n      &lt;p&gt;\n        &lt;a href=&quot;.+?&quot;&gt;\n          &lt;img src=&quot;(.+?)&quot; alt=&quot;.+?&quot; /&gt;\n        &lt;/a&gt;\n      &lt;/p&gt;\n      &lt;p&gt;\n        (.+?)\n      &lt;/p&gt;\n    </content>').findall(data))

				# Loop through each element <entry>
				for line in links:
					name = checkUnicode(line[0])
					stream = line[1]

					# Format the date to display onscreen
					try:
						lastDate = datetime.fromtimestamp(mktime(strptime(str(line[2]), "%Y-%m-%dT%H:%M:%SZ"))) #2013-03-06T18:27:43Z
						date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
						date1 = _("Added:") + " " + str(date_tmp)
					except (Exception) as exception:
						date1 = str(line[2])

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						icon = line[3]
					else:
						icon = ''

					short = checkUnicode(line[4])

					weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print(__plugin__, __version__, "getMediaData: Error getting Media info: ", exception)

#===================================================================================
	def getSearchMediaData(self, weekList, url):

		#============ Not Used - More robust but not as quick ==============

		short = ''
		name = ''
		date1 = ''
		stream = ''
		channel = ''
		icon = ''
		duration = ''

		try:
			# Retrieve the search results from the feeds.
			data = wgetUrl(url)

			# Problems with tags resulted in non-parsed tags, fix them.
			data = data.replace("&lt;", "<")
			data = data.replace("&gt;", ">")

			# Parse the HTML with LXML-HTML
			tree = html.document_fromstring(data)

			# Find the first element <entry> and loop
			for show in tree.xpath('//entry'):
				# Iterate through the children of <entry>
				select = lambda expr: show.cssselect(expr)[0]

				# Only set the Icon if they are enabled
				if self.showIcon == 'True':
					icon = select("thumbnail").get('url')
				else:
					icon = ''

				name_tmp = str(select('title').text_content())

				stream_tmp = select('id').text_content()
				stream_split = stream_tmp.rsplit(':', 1)
				stream = stream_split[1]

				try:
					lastDate = datetime.fromtimestamp(mktime(strptime(str(select('updated').text_content()), "%Y-%m-%dT%H:%M:%SZ"))) #2013-03-06T18:27:43Z
					date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
					date1 = _("Added:") + " " + str(date_tmp)
				except (Exception) as exception:
					date1 = select('updated').text_content()
					print(__plugin__, __version__, "getMediaData: date1 parse error: ", exception)

				short_tmp = str(select('content').text_content().strip())

				name = checkUnicode(name_tmp)
				short = checkUnicode(short_tmp)

				weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print(__plugin__, __version__, "getMediaData: Error getting Media info: ", exception)

#===================================================================================

	def findPlayUrl(self, showID):

		notUK = 0
		url1 = 'http://www.bbc.co.uk/iplayer/playlist/' + showID
		supplier = ""
		fileUrl = ""
		quality = 0
		akamaiFileUrl = ""
		otherAkamaiUrl = ""
		akamaiFound = False
		limelightFileUrl = ""
		otherLimelightUrl = ""
		limelightFound = False
		currQuality = 0
		prefQuality = int(config.ondemand.PreferredQuality.value)
		primaryDNS = str(config.ondemand.PrimaryDNS.value)
		print(__plugin__, __version__, "DNS Set: ", primaryDNS)
		print(__plugin__, __version__, "Default DNS Set: ", str(config.ondemand.PrimaryDNS.default))

		try:
			# Read the URL to get the stream options
			html = wgetUrl(url1)
			try:
				links = (re.compile('<mediator identifier="(.+?)" name=".+?" media_set=".+?"/>').findall(html)[1])
			except:
				links = (re.compile('<mediator identifier="(.+?)" name=".+?" media_set=".+?"/>').findall(html)[0])

			url2 = 'http://www.bbc.co.uk/mediaselector/4/mtis/stream/' + links
			html1 = html = wgetUrl(url2)

			if html1.find('notukerror') > 0:
				notUK = 1
				print(__plugin__, __version__, "Non UK Address!!")

				if primaryDNS == str(config.ondemand.PrimaryDNS.default):
					print(__plugin__, __version__, "Non UK Address: NO DNS Set!! ", primaryDNS)
					return ("", "Non-UK IP Address and no DNS set in OnDemand Settings! Not able to play ")
				else:
					try:
						opener = urllib2.build_opener(MyHTTPHandler)
						old_opener = urllib2._opener
						urllib2.install_opener(opener)
						req = urllib2.Request(url2)
						req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
						response = urllib2.urlopen(req)
						html1 = str(response.read())
						response.close()
						urllib2.install_opener(old_opener)

					except (Exception) as exception:
						print(__plugin__, __version__, "findPlayUrl: Unable to connect to DNS: ", exception)
						return ("", "Could not connect to " + primaryDNS + ", make sure your subscription is valid! Not able to play ")

			# Parse the HTML returned
			doc = dom.parseString(html1)
			root = doc.documentElement
			media = root.getElementsByTagName("media")
			i = 0

			# Loop for each streaming option available
			for list in media:
				service = media[i].attributes['service'].nodeValue

				# If quality is Very-Low, Low, Normal, High or HD proceed
				if service == 'iplayer_streaming_h264_flv_vlo' or \
					service == 'iplayer_streaming_h264_flv_lo' or \
					service == 'iplayer_streaming_h264_flv' or \
					service == 'iplayer_streaming_h264_flv_high' or \
					service == 'pc_streaming_hd':

					# Get stream data for first Media element
					conn = media[i].getElementsByTagName("connection")[0]
					returnedList = self.getHosts(conn, service)

					if returnedList:
						fileUrl = str(returnedList[0])
						supplier = str(returnedList[1])
						quality = int(returnedList[2])

					if fileUrl:
						# Try and match the stream quality to the preferred config stream quality
						if quality == prefQuality:
							currQuality = quality
							if supplier == 'akamai':
								akamaiFileUrl = fileUrl
								akamaiFound = True
							else:
								limelightFileUrl = fileUrl
								limelightFound = True

						elif quality > currQuality and quality < prefQuality:
							currQuality = quality
							if supplier == 'akamai':
								akamaiFileUrl = fileUrl
							else:
								limelightFileUrl = fileUrl
						else:
							if supplier == 'akamai':
								otherAkamaiUrl = fileUrl
							else:
								otherLimelightUrl = fileUrl

					# Repeat for the second Media element
					conn = media[i].getElementsByTagName("connection")[1]
					returnedList = self.getHosts(conn, service)

					if returnedList:
						fileUrl = str(returnedList[0])
						supplier = str(returnedList[1])
						quality = int(returnedList[2])

					if fileUrl:
						# Try and match the stream quality to the preferred config stream quality
						if quality == prefQuality:
							currQuality = quality
							if supplier == 'akamai':
								akamaiFileUrl = fileUrl
								akamaiFound = True
							else:
								limelightFileUrl = fileUrl
								limelightFound = True

						elif quality > currQuality and quality < prefQuality:
							currQuality = quality
							if supplier == 'akamai':
								akamaiFileUrl = fileUrl
							else:
								limelightFileUrl = fileUrl
						else:
							if supplier == 'akamai':
								otherAkamaiUrl = fileUrl
							else:
								otherLimelightUrl = fileUrl

				i = i + 1

			# If we have found our required Stream Quality and it's limelight return the URL.
			if limelightFound:
				return (limelightFileUrl, "")
			else:
				# If UK User and HD Quality Required & Found return the URL.
				if prefQuality == 3200 and akamaiFound and notUK == 0:
					return (akamaiFileUrl, "")
				else:
					# If we have any Limelight URL saved then return it.
					if limelightFileUrl:
						return (limelightFileUrl, "")
					else:
						# We have no Limelight URL so only return Akamai if UK user.
						if akamaiFileUrl and notUK == 0:
							return (akamaiFileUrl, "")
						else:
							# If we haven't found a matching stream quality or lower return whatever found
							if otherLimelightUrl:
								print(__plugin__, __version__, "findPlayUrl: Unable to find Preferred Stream quality, playing only available stream!!")
								return (otherLimelightUrl, "Unable to find Preferred Stream quality, playing only available stream for ")
							elif otherAkamaiUrl and notUK == 0:
								return (otherAkamaiUrl, "")
							else:
								print(__plugin__, __version__, "findPlayUrl: Non-UK and no limelight, return blank: ")
								return ("", "Non-UK and no limelight, No playable stream for ")

		except (Exception) as exception:
			print(__plugin__, __version__, "findPlayUrl: Error getting URLs: ", exception)
			return ("", "findPlayUrl: Error getting URLs! Could not play ")

#===================================================================================
	def getHosts(self, conn, service):

		try:
			identifier = str(conn.attributes['identifier'].nodeValue)
			server = str(conn.attributes['server'].nodeValue)
			auth = str(conn.attributes['authString'].nodeValue)
			supplier = str(conn.attributes['supplier'].nodeValue)

			# Build up the stream URL based on the supplier
			if supplier == 'limelight':    # SD streams that can be played by all users.
				fileUrl = "rtmp://" + server + ":1935/ app=a1414/e3?" + auth + " tcurl=rtmp://" + server + ":1935/a1414/e3?" + auth + " playpath=" + identifier + " swfurl=http://www.bbc.co.uk/emp/releases/iplayer/revisions/617463_618125_4/617463_618125_4_emp.swf swfvfy=true timeout=180"
			elif supplier == 'akamai':     # SD & HD streams that only UK users can play.
				fileUrl = "rtmp://" + server + ":1935/ondemand?" + auth + " playpath=" + identifier + " swfurl=http://www.bbc.co.uk/emp/releases/iplayer/revisions/617463_618125_4/617463_618125_4_emp.swf swfvfy=true timeout=180"
			elif supplier == 'level3':     # HD Streams that can be played by all users.
				fileUrl = "rtmp://" + server + ":1935/iplayertok?" + auth + " playpath=" + identifier + " swfurl=http://www.bbc.co.uk/emp/releases/iplayer/revisions/617463_618125_4/617463_618125_4_emp.swf swfvfy=true timeout=180"
			else:
				fileUrl = ""

			# Determine the Bitrate from the Service idenifier
			if service == 'iplayer_streaming_h264_flv_vlo':
				bitrate = 400
			elif service == 'iplayer_streaming_h264_flv_lo':
				bitrate = 480
			elif service == 'iplayer_streaming_h264_flv':
				bitrate = 800
			elif service == 'iplayer_streaming_h264_flv_high':
				bitrate = 1500
			elif service == 'pc_streaming_hd':
				bitrate = 3200

			streamData = []
			streamData.append(fileUrl)
			streamData.append(supplier)
			streamData.append(bitrate)
			return streamData

		except (Exception) as exception:
			print(__plugin__, __version__, "getHosts: Error setting stream URL: ", exception)
			return ""

#===================================================================================


def main(session, **kwargs):
	action = "start"
	value = 0
	start = session.open(BBCiMenu, action, value)

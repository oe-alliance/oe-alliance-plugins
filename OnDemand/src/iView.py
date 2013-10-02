"""
	ABC iView - Enigma2 Video Plugin
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

from Screens.Screen import Screen
from Components.config import config
from Screens.MessageBox import MessageBox
from enigma import eServiceReference, eTimer, getDesktop
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk

import time, random
from time import strftime, strptime, mktime
from datetime import timedelta, date, datetime

import urllib2, re

import simplejson
from bs4 import BeautifulSoup

from CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler, StreamsThumbCommon

__plugin__  = "ABC iView"
__version__ = "1.0.1"

#==============================================================================
def wgetUrl(target):
	try:
		req = urllib2.Request(target)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		outtxt = str(response.read())
		response.close()
		return outtxt
	except (Exception) as exception:
		print "%s: version %s: wgetUrl: Error retrieving URL: %s" % (__plugin__, __version__, exception)
		return ""

#==============================================================================
def calcDuration(seconds):
	try:
		mins = int((seconds / 60))
		duration = str(mins)
		return str(duration)
	except (Exception) as exception:
		print "%s: version %s: calcDuration: Error calculating minutes: %s" % (__plugin__, __version__, exception)
		return ""

#==============================================================================
class iViewMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="ABC iView - Main Menu" >
			<widget name="iViewMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		Screen.__init__(self, session)

		self.imagedir = "/tmp/onDemandImg/"
		self.action = action
		self.value = value
		osdList = []
		if self.action is "start":
			osdList.append((_("Search"), "search"))
			osdList.append((_("Recently Added"), "recent"))
			osdList.append((_("Comedy - Cult"), "cult"))
			osdList.append((_("Comedy - Satire"), "satire"))
			osdList.append((_("Comedy - Sitcom"), "sitcom"))
			osdList.append((_("Comedy - Sketch"), "sketch"))
			osdList.append((_("Drama - Crime"), "crime"))
			osdList.append((_("Drama - Historical"), "historical"))
			osdList.append((_("Drama - Period"), "period"))
			osdList.append((_("Drama - Romance"), "romance"))
			osdList.append((_("Drama - Sci-fi"), "sci-fi"))
			osdList.append((_("Documentary - Biography"), "bio"))
			osdList.append((_("Documentary - History"), "history"))
			osdList.append((_("Documentary - Nature"), "nature"))
			osdList.append((_("Documentary - Science"), "science"))
			osdList.append((_("Documentary - Real Life"), "real-life"))
			osdList.append((_("Lifestyle - Games"), "games"))
			osdList.append((_("Lifestyle - Reality"), "reality"))
			osdList.append((_("News & Current Affairs"), "news"))
			osdList.append((_("Sport"), "sport"))
			osdList.append((_("Arts & Culture - Music"), "music"))
			osdList.append((_("Arts & Culture - People"), "people"))
			osdList.append((_("Arts & Culture - Performance"), "performance"))
			osdList.append((_("Arts & Culture - Reviews"), "reviews"))
			osdList.append((_("iView Exclusives"), "original"))
			osdList.append((_("Featured Programs"), "featured"))
			osdList.append((_("Panel & Discussion"), "panel"))
			osdList.append((_("Last Chance"), "last-chance"))
			osdList.append((_("ABC4Kids"), "pre-school"))
			osdList.append((_("Education"), "education"))
			osdList.append((_("Indigenous"), "indigenous"))
			osdList.append((_("Trailers"), "trailers"))
			osdList.append((_("ABC1"), "abc1"))
			osdList.append((_("ABC2"), "abc2"))
			osdList.append((_("ABC3"), "abc3"))
			osdList.append((_("ABC News 24"), "abc4"))
			osdList.append((_("A to Z"), "atoz"))
			osdList.append((_("Back"), "exit"))

		self["iViewMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)	  

	def go(self):
		name = self["iViewMenu"].l.getCurrentSelection()[0]
		selection = self["iViewMenu"].l.getCurrentSelection()[1]
		
		if selection is "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
			
		elif self.action is "start":
			if selection is "atoz":
				self.session.open(StreamsMenu, selection, name, selection)
			else:
				self.session.open(StreamsThumb, selection, name, selection)

	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)		

	def removeFiles(self, targetdir):
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))

#==============================================================================
class StreamsMenu(Screen):
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" >
			<widget name="latestMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value, url):
		Screen.__init__(self, session)
		if action is 'atoz':
			Screen.setTitle(self, _("ABC iView - A to Z"))

		self.action = action
		self.value = value
		osdList = []

		osdList.append((_("All Shows"), "index"))
		osdList.append((_("A - C"), "a-c"))
		osdList.append((_("D - F"), "d-f"))
		osdList.append((_("G - J"), "g-j"))
		osdList.append((_("K - M"), "k-m"))
		osdList.append((_("N - P"), "n-p"))
		osdList.append((_("Q - T"), "q-t"))
		osdList.append((_("U - Z"), "u-z"))
		osdList.append((_("0 - 9"), "0-9"))
		osdList.append((_("Exit"), "exit"))

		self["latestMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1) 

	def go(self):
		title = self["latestMenu"].l.getCurrentSelection()[0]
		selection = self["latestMenu"].l.getCurrentSelection()[1]
		
		if selection is not None:
			if selection is "exit":
				self.close(None)
			else:
				self.session.open(StreamsThumb, selection, title, selection)

	def cancel(self):
		self.close(None)

#==============================================================================

def checkUnicode(value, **kwargs):
	stringValue = value 
	stringValue = stringValue.replace('&#39;', '\'')
	stringValue = stringValue.replace('&amp;', '&')
	return stringValue
	
#==============================================================================
def remove_extra_spaces(data):
	p = re.compile(r'\s+')
	return p.sub(' ', data)

#==============================================================================

def main(session, **kwargs):
	action = "start"
	value = 0 
	start = session.open(iViewMenu, action, value)

#==============================================================================	   
class StreamsThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = "Extensions/OnDemand/icons/iView.png"
		self.showIcon = str(config.ondemand.ShowImages.value)
		StreamsThumbCommon.__init__(self, session, action, value, url)

	def layoutFinished(self):
		self.setTitle("ABC iView: Listings for " +self.title)

	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return
			
		if retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

		elif retval == 'episode':
			self.getMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
			
		else:
			self.getCatsMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()

#==============================================================================
	def keyboardCallback(self, callback = None):
		if callback is not None and len(callback):
			self.setTitle("ABC iView: Search Listings for " +callback)
			self.getSearchMediaData(self.mediaList, callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple = True)
		else:
			self.close()

#==============================================================================
	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]

		if self.cmd <> "episode":
			self.session.open(StreamsThumb, "episode", showName, showID)
		else:
			fileUrl = self.findPlayUrl(showID)

			if fileUrl:
				fileRef = eServiceReference(4097,0,fileUrl)
				fileRef.setName (showName)
				lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
				self.session.open(MoviePlayer, fileRef, None, lastservice)
			else:
				self.mediaProblemPopup("Sorry, unable to find playable stream!")

#==============================================================================
	def findPlayUrl(self, showID):

		try:
			iview_config = self.get_config()
			auth = self.get_auth(iview_config)

			# If zero, an error occurred retrieving the url, pass empty string back
			if auth:
				swf_url  = 'http://www.abc.net.au/iview/images/iview.jpg'

				playpath = auth['playpath_prefix'] + showID
				if playpath.split('.')[-1] == 'mp4':
					playpath = 'mp4:' + playpath

				# Strip off the .flv or .mp4
				playpath = playpath.split('.')[0]

				# rtmp://cp53909.edgefcs.net/ondemand?auth=daEbjbeaCbGcgb6bedYacdWcsdXc7cWbDda-bmt0Pk-8-slp_zFtpL&aifp=v001 
				# playpath=mp4:flash/playback/_definst_/kids/astroboy_10_01_22 swfurl=http://www.abc.net.au/iview/images/iview.jpg swfvfy=true
				rtmp_url = "%s?auth=%s playpath=%s swfurl=%s swfvfy=true" % (auth['rtmp_url'], auth['token'], playpath, swf_url)
				print "%s: version %s: findPlayUrl: rtmp_url: %s" % (__plugin__, __version__, rtmp_url)
				return str(rtmp_url)
			else:
				return ""

		except (Exception) as exception:
			print "%s: version %s: findPlayUrl: Problem rerieving URL: %s" % (__plugin__, __version__, exception)
			return ""

#==============================================================================
	def get_config(self):
		"""This function fetches the iView "config". Among other things,
			it tells us an always-metered "fallback" RTMP server, and points
			us to many of iView's other XML files.
		"""
		config_url = "http://www.abc.net.au/iview/xml/config.xml?r=383"

		try:
			iview_config = wgetUrl(config_url)

			if iview_config:
				return self.parse_config(iview_config)
			else:
				return ""

		except (Exception) as exception:
			print "%s: version %s: get_config: Problem Getting Config: %s" % (__plugin__, __version__, exception)
			return ""

#==============================================================================
	def parse_config(self, soup):
		"""There are lots of goodies in the config we get back from the ABC.
			In particular, it gives us the URLs of all the other XML data we
			need.
		"""

		try:
			soup = soup.replace('&amp;', '&#38;')

			xml = BeautifulSoup(soup)

			# should look like "rtmp://cp53909.edgefcs.net/ondemand"
			# Looks like the ABC don't always include this field.
			# If not included, that's okay -- ABC usually gives us the server in the auth result as well.

			rtmp_url = xml.find('param', attrs={'name':'server_streaming'}).get('value')
			rtmp_chunks = rtmp_url.split('/')

			return {
				'rtmp_url'  : rtmp_url,
				'rtmp_host' : rtmp_chunks[2],
				'rtmp_app'  : rtmp_chunks[3],
				'api_url' : xml.find('param', attrs={'name':'api'}).get('value'),
				'categories_url' : xml.find('param', attrs={'name':'categories'}).get('value'),
			}
		except (Exception) as exception:
			print "%s: version %s: parse_config: Problem Parsing Config: %s" % (__plugin__, __version__, exception)
			return ""

#==============================================================================
	def get_auth(self, iview_config):
		"""This function performs an authentication handshake with iView.
			Among other things, it tells us if the connection is unmetered,
			and gives us a one-time token we need to use to speak RTSP with
			ABC's servers, and tells us what the RTMP URL is.
		"""
		auth_url   = 'http://tviview.abc.net.au/iview/auth/?v2'

		try:
			auth_config = wgetUrl(auth_url)
			print '%s: version %s: get_auth: auth_config: %s' % (__plugin__, __version__, auth_config)

			if auth_config:
				return self.parse_auth(auth_config, iview_config)
			else:
				return ""

		except (Exception) as exception:
			print "%s: version %s: get_auth: Problem Getting Auth: %s" % (__plugin__, __version__, exception)
			return ""

#==============================================================================
	def parse_auth(self, soup, iview_config):
		"""	There are lots of goodies in the auth handshake we get back,
			but the only ones we are interested in are the RTMP URL, the auth
			token, and whether the connection is unmetered.
		"""

		akamai_playpath_prefix = 'flash/playback/_definst_/'

		xml = BeautifulSoup(soup)

		# should look like "rtmp://203.18.195.10/ondemand"
		try:
			rtmp_url = xml.find('server').string

			# at time of writing, either 'Akamai' (usually metered) or 'Hostworks' (usually unmetered)
			stream_host = xml.find('host').string

			playpath_prefix = ''
			if stream_host == 'Akamai':
				playpath_prefix = akamai_playpath_prefix

			if rtmp_url is not None:
				# Being directed to a custom streaming server (i.e. for unmetered services).
				# Currently this includes Hostworks for all unmetered ISPs except iiNet.
				rtmp_chunks = rtmp_url.split('/')
				rtmp_host = rtmp_chunks[2]
				rtmp_app = rtmp_chunks[3]
			else:
				# We are a bland generic ISP using Akamai, or we are iiNet.
				rtmp_url = iview_config['rtmp_url']
				rtmp_host = iview_config['rtmp_host']
				rtmp_app = iview_config['rtmp_app']

			token = xml.find("token").string
			token = token.replace('&amp;', '&') # work around BeautifulSoup bug

		except:
			print "%s: version %s: parse_auth: Problem Parsing Auth: %s" % (__plugin__, __version__, exception)
			return ""

		return {
			'rtmp_url'        : rtmp_url,
			'rtmp_host'       : rtmp_host,
			'rtmp_app'        : rtmp_app,
			'playpath_prefix' : playpath_prefix,
			'token'           : token,
			'free'            : (xml.find("free").string == "yes")
		}

#==============================================================================
	def getMediaData(self, weekList, seriesID):

		self.url = u"http://tviview.abc.net.au/iview/api2/?series="+seriesID
		channel = ""
		short = ''
		name = ''
		date1 = ''
		stream = ''
		icon = ''
		duration = ''

		try:
			# Read the Category URL
			jsonText = wgetUrl(self.url)

			# Only want to try and parse if stream data is returned.
			if jsonText:
				# Use JSON to parse the returned data
				jsonData = simplejson.loads(jsonText)

				for entry in jsonData[0][u'f']:

					try:
						stream = str(entry[u'n'])
					except (Exception) as exception:
						stream = ""

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						try:
							icon = str(entry[u's'])
						except (Exception) as exception:
							icon = ""
					else:
						icon = ''

					try:
						name_tmp = str(unicode(entry[u'b']))
						name_tmp1 = checkUnicode(name_tmp)
						name = remove_extra_spaces(name_tmp1)
					except (Exception) as exception:
						name = ""

					try:
						short_tmp = str(entry[u'd'])
						short_tmp1 = checkUnicode(short_tmp)
						short = remove_extra_spaces(short_tmp1)
					except (Exception) as exception:
						short = ""

					try:
						# Calcualte the stream duration
						secs = int(entry[u'j'])
						duration = _("Duration: ")+str(calcDuration(secs))
					except (Exception) as exception:
						episodes = ""

					try:
						lastDate = datetime.fromtimestamp(mktime(strptime(str(entry[u'f']), u"%Y-%m-%d %H:%M:%S")))
						date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
						date1 = _("Added:")+" "+str(date_tmp)
					except (Exception) as exception:
						lastDate = datetime.fromtimestamp(mktime(strptime(str(entry[u'g']), u"%Y-%m-%d %H:%M:%S")))
						date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
						date1 = _("Added:")+" "+str(date_tmp)

					try:
						channel = str(entry[u'a'])
					except (Exception) as exception:
						channel = ""

					weekList.append((date1, name, short, channel, stream, icon, duration, False))			

		except (Exception) as exception:
			print "%s: version %s: getMediaData: Error parsing feed: %s" % (__plugin__, __version__, exception)

#==============================================================================
	def getCatsMediaData(self, weekList, category):

		self.url = u"http://tviview.abc.net.au/iview/api2/?keyword="+category
		channel = ""
		short = ''
		name = ''
		date1 = ''
		stream = ''
		icon = ''
		duration = ''

		try:
			# Read the Category URL
			jsonText = wgetUrl(self.url)

			# Only want to try and parse if stream data is returned.
			if jsonText:
				# Use JSON to parse the returned data
				jsonData = simplejson.loads(jsonText)

				for entry in jsonData:

					try:
						stream = str(entry['a'])
					except (Exception) as exception:
						stream = ""

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						try:
							icon = str(entry['d'])
						except (Exception) as exception:
							icon = ""
					else:
						icon = ''

					try:
						name_tmp = str(entry['b'])
						name_tmp1 = checkUnicode(name_tmp)
						name = remove_extra_spaces(name_tmp1)
					except (Exception) as exception:
						name = ""

					try:
						short_tmp = str(entry['c'])
						short_tmp1 = checkUnicode(short_tmp)
						short = remove_extra_spaces(short_tmp1)
					except (Exception) as exception:
						short = ""

					try:
						episodes = _("Episodes: ")+str(len(entry['f']))
					except (Exception) as exception:
						episodes = ""

					weekList.append((date1, name, short, channel, stream, icon, episodes, False))

		except (Exception) as exception:
			print "%s: version %s: getMediaData: Error getting Media info: %s" % (__plugin__, __version__, exception)

#==============================================================================
	def getSearchMediaData(self, weekList, query):

		self.url = u"http://tviview.abc.net.au/iview/api2/?keyword=index"
		channel = ""
		short = ''
		name = ''
		date1 = ''
		stream = ''
		icon = ''
		duration = ''

		try:
			# Read the Category URL
			jsonText = wgetUrl(self.url)

			# Only want to try and parse if stream data is returned.
			if jsonText:
				# Use JSON to parse the returned data
				jsonData = simplejson.loads(jsonText)

				for entry in jsonData:

					try:
						name_tmp = str(entry['b'])
						name_tmp1 = checkUnicode(name_tmp)
						name = remove_extra_spaces(name_tmp1)
					except (Exception) as exception:
						name = ""

					try:
						short_tmp = str(entry['c'])
						short_tmp1 = checkUnicode(short_tmp)
						short = remove_extra_spaces(short_tmp1)
					except (Exception) as exception:
						short = ""
					
									
					# Only output the names that match the search query
					if re.search(query, name, re.IGNORECASE) or re.search(query, short, re.IGNORECASE):
						try:
							stream = str(entry['a'])
						except (Exception) as exception:
							stream = ""

						# Only set the Icon if they are enabled
						if self.showIcon == 'True':
							try:
								icon = str(entry['d'])
							except (Exception) as exception:
								icon = ""
						else:
							icon = ''

						try:
							episodes = _("Episodes: ")+str(len(entry['f']))
						except (Exception) as exception:
							episodes = ""

						weekList.append((date1, name, short, channel, stream, icon, episodes, False))

		except (Exception) as exception:
			print "%s: version %s: getSearchMediaData: Error getting Media info: %s" % (__plugin__, __version__, exception)

#==============================================================================
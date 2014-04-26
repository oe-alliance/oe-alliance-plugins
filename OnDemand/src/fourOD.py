# -*- coding: utf-8 -*-
"""
    4OD Player - Enigma2 Video Plugin
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
from Tools.LoadPixmap import LoadPixmap
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk

import time, random
from time import strftime, strptime, mktime
from datetime import timedelta, date, datetime

import urllib2, re
from bs4 import BeautifulSoup
import simplejson

import fourOD_token_decoder

from CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler, StreamsThumbCommon, RTMP

__plugin__  = "4OD: "
__version__ = "Version 1.0.2: "

#=================== Default URL's =======================================================

fourodSearchDefault = u'http://www.channel4.com/search/predictive/?q='

#=========================================================================================
def readUrl(target):
	try:
		req = urllib2.Request(target)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		outtxt = str(response.read())
		response.close()
		return outtxt
	except:
		return ''

def wgetUrl(target):
	try:
		isUK = 0
		outtxt = ""
		primaryDNS = str(config.ondemand.PrimaryDNS.value)
		print __plugin__, __version__,"DNS Set: ", primaryDNS
		
		req = urllib2.Request(target)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)	

		# Find out the character set of the returned data
		charset = GetCharset(response)

		data = response.read()

		# If the character set wasnt found attempt to decode as utf-8
		if charset is None:
			try:
				data.decode('utf-8')
				charset = 'utf-8'
			except:
				charset = 'latin1'

		# Now decode the data into the found character set
		outtxt = str(data.decode(charset))
		response.close()

		# If the returned data contains ERROR then geo restriction has applied.
		# Now attempt to use your proxy DNS to bypass the Geo restriction.
		if outtxt.find('ERROR') > 0:
			print __plugin__, __version__,"Non UK Address"
			isUK = 1
							
			if  primaryDNS == str(config.ondemand.PrimaryDNS.default):
				print __plugin__, __version__,"Non UK Address: NO DNS Set!! ", primaryDNS
				return ("NODNS", isUK)
			else:
				try:
					opener = urllib2.build_opener(MyHTTPHandler)
					old_opener = urllib2._opener
					urllib2.install_opener (opener)
					req = urllib2.Request(target)
					req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
					response = urllib2.urlopen(req)

					# Find out the character set of the returned data
					charset = GetCharset(response)

					data = response.read()

					if charset is None:
						try:
							data.decode('utf-8')
							charset = 'utf-8'
						except:
							charset = 'latin1'

					outtxt = str(data.decode(charset))			
					response.close()
					urllib2.install_opener (old_opener)

				except (Exception) as exception:
					print __plugin__, __version__,"wgetUrl: Unable to connect to DNS: ", exception
					return ("NOCONNECT", isUK)

		# Now return the decoded webpage
		return (outtxt, isUK)

	except (Exception) as exception:
		print __plugin__, __version__,"wgetUrl: Exception: ", exception
		outtxt = str(response.read())
		response.close()
		
		# If we managed to read the URL then return data, might have failed on decode.
		if outtxt:
			print __plugin__, __version__,"wgetUrl: Exception: outtxt: ", outtxt
			return (outtxt, isUK)
		else:
			return ("", isUK)
		
#==============================================================================
def GetCharset(response):
	if u'content-type' in response.info():
		contentType = response.info()[u'content-type']

	typeItems = contentType.split('; ')
	pattern = "charset=(.+)"
	for item in typeItems:
		try:
			match = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
			return match.group(1)
		except:
			pass

	return None
        
#==============================================================================
class fourODMainMenu(Screen):

	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300

	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="4OD - Main Menu" >
			<widget name="fourODMainMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""


	def __init__(self, session, action, value):

		self.imagedir = "/tmp/onDemandImg/"
		self.session = session
		self.action = action
		self.value = value
		self.url = "http://m.channel4.com/4od/tags"
		osdList = []

		osdList.append((_("Search"), "search"))
		if self.action is "start":
			# Read the URL for the selected category on the Main Menu.
			try:
				(data, isUK) = wgetUrl(self.url)

				if data:
					soup = BeautifulSoup(data)
					categoriesSection = soup.find('section', id="categories")
					entries = categoriesSection.find('nav').findAll('a')

					pattern = u'/4od/tags/(.+)'

					for entry in entries:
						"""
						  <section id="categories" class="clearfix">

						    <aside class="catNav clearfix">
							<nav>
							    <h2>Most popular</h2>
							    <ul>

								<li class="active">
								    <span class="chevron"></span>
								    <a href="/4od/tags/comedy">Comedy (100)</a>
								</li>
							    </ul>

							    <h2>More categories</h2>

							    <ul>
								<li>
								    <span class="chevron"></span>
								    <a href="/4od/tags/animals">Animals (4)</a>
								</li>

						"""

						id = entry['href']
						match = re.search(pattern, id, re.DOTALL | re.IGNORECASE)

						categoryName = match.group(1)
						label = unicode(entry.text).replace('\r\n', '')
						label = re.sub(' +', ' ', label)

						osdList.append((_(str(label)), str(categoryName)))

			except (Exception) as exception:
				print __plugin__, __version__,'StreamsMenu: Error parsing feed: ', exception

			osdList.append((_("Back"), "exit"))

		Screen.__init__(self, session)
		self["fourODMainMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)

#==============================================================================
	def go(self):
		title = self["fourODMainMenu"].l.getCurrentSelection()[0]
		category = self["fourODMainMenu"].l.getCurrentSelection()[1]
		
		if category is "exit":
			self.removeFiles(self.imagedir)
			self.close(None)
		elif category is "search":
			self.session.open(StreamsThumb, category, title, category)
		else:
			self.session.open(StreamsThumb, self.action, title, category)

#==============================================================================
	def cancel(self):
		self.removeFiles(self.imagedir)
		self.close(None)

#==============================================================================
	def removeFiles(self, targetdir):
		for root, dirs, files in os_walk(targetdir):
			for name in files:
				os_remove(os_path.join(root, name))

###########################################################################	   
class StreamsThumb(StreamsThumbCommon):
	def __init__(self, session, action, value, url):
		self.defaultImg = "Extensions/OnDemand/icons/fourOD.png"
		self.showIcon = str(config.ondemand.ShowImages.value)
		StreamsThumbCommon.__init__(self, session, action, value, url)

	def layoutFinished(self):
		self.setTitle("4OD Player: Listings for " +self.title)

	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return

		elif retval == 'start':
			self.getCatsMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Categories Found!")
			self.updateMenu()
		elif retval == 'show':
			self.getShowMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()
		elif retval == 'searchShow':
			self.getShowMediaData(self.mediaList, self.url)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("Programme Not Available on PS3 4OD!")
			self.updateMenu()
		elif retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

	def keyboardCallback(self, callback = None):
		if callback is not None and len(callback):
			self.setTitle("4OD: Search Listings for " +callback)
			self.getSearchMediaData(self.mediaList, fourodSearchDefault + callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple = True)
		else:
			self.close()

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]

		if self.cmd == 'start':
			self.session.open(StreamsThumb, "show", showName, showID)
		elif self.cmd == 'search':
			self.session.open(StreamsThumb, "searchShow", showName, showID)
		else:
			try:
				(fileUrl, rtmpvar, returnMessage) = self.getRTMPUrl(showID)
				
				if fileUrl:
					fileRef = eServiceReference(4097,0,str(fileUrl))
					fileRef.setName (showName)
					lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
					self.session.open(MoviePlayer, fileRef, None, lastservice)
				else:
					if returnMessage:
						self.mediaProblemPopup(returnMessage)
					else:
						self.mediaProblemPopup("Problem retreiving the stream URL!")
					
			except (Exception) as exception:
				print __plugin__, __version__,'go: Error getting fileUrl: ', exception

#==============================================================================
	def getRTMPUrl(self, showID):
		playUrl = None

		try:
			aisUrl = "http://ais.channel4.com/asset/%s"
			assetUrl = aisUrl % showID
			(rtmpvar, returnMessage) = self.InitialiseRTMP(assetUrl)
			if rtmpvar:
				playUrl = rtmpvar.getPlayUrl()    

				return (playUrl, rtmpvar, returnMessage)
			else:
				return ("", "", returnMessage)

		except (Exception) as exception:
			print __plugin__, __version__,'getRTMPUrl: Error getting playUrl: ', exception
			return ("", "", "")

#==============================================================================			
	def InitialiseRTMP(self, assetUrl):

		try:
			self.urlRoot = u"http://m.channel4.com"
			streamUri = ""
			auth = ""
			
			# Get the stream info
			(streamUri, auth, returnMessage) = self.GetStreamInfo(assetUrl)
			
			if streamUri:
				url = re.search(u'(.*?)mp4:', streamUri).group(1)
				app = re.search(u'.com/(.*?)mp4:', streamUri).group(1)
				playPath = re.search(u'(mp4:.*)', streamUri).group(1)

				if "ll."  not in streamUri: 
					app = app + u"?ovpfv=1.1&" + auth
				else:
					playPath += "?" + auth

				swfPlayer = self.GetSwfPlayer()
				
				port = None
				
				rtmpvar =  RTMP(rtmp = streamUri, app = app, swfVfy = swfPlayer, playPath = playPath, pageUrl = self.urlRoot, port = port)
				return (rtmpvar, returnMessage)
			else:
				return ("", returnMessage)
		except (Exception) as exception:
			print __plugin__, __version__,'InitialiseRTMP: Error getting mp4: ', exception
			return ("", "InitialiseRTMP: Error getting mp4")

#==============================================================================
	def GetStreamInfo(self, assetUrl):
		maxAttempts = 15
		
		streamURI = ""
		auth = ""
		returnMessage = "Non-UK User!!\n\nUnable to find playable Stream in "+str(maxAttempts)+" attempts!!\n\nPlease try again!"
		
		for attemptNumber in range(0, maxAttempts):
			(xml, isUK) = wgetUrl( assetUrl )
			
			# No DNS set in Settings, exit.NOCONNECT
			if (xml == "NODNS"):
				return (streamURI, auth, "Non-UK User!!\n\nYou need to specify a DNS in the OnDemand Settings!!")
				break

			# No DNS set in Settings, exit.
			if (xml == "NOCONNECT"):
				return (streamURI, auth, "Non-UK User!!\n\nCould not connect to your specified DNS!\n\n Check the DNS in the OnDemand Settings!!")
				break

			# Only check stream data if data has been returned.
			if xml:
				# Parse the returned XML
				soup = BeautifulSoup(xml)

				uriData = soup.find(u'uridata')
				streamURI = uriData.find(u'streamuri').text

				# If call is from Outside UK then stream URL might need to be altered.
				if isUK == 1:
					print __plugin__, __version__,"GetStreamInfo: notUK user: streamURI: ", streamURI, " streamURI[:10]: ", streamURI[:10]
					if streamURI[:10] <> "rtmpe://ll":
						streamURI = ""
						continue

				# If HTTP Dynamic Streaming is used for this show then there will be no mp4 file,
				# and decoding the token will fail, therefore we abort before
				# parsing authentication info if there is no mp4 file.
				if u'mp4:' not in streamURI.lower():
					# Unable to find MP4 video file to play.
					# No MP4 found, probably HTTP Dynamic Streaming. Stream URI - %s
					raise exception

				auth =  self.GetAuthentication(uriData)

				if auth is None:
					# If we didn't get the cdn we're looking for then try again
					# Error getting correct cdn, trying again
					continue

				break
			else:
				break
		
		if streamURI:
			return (streamURI, auth, "")
		else:
			return (streamURI, auth, returnMessage)

#==============================================================================
	def GetAuthentication(self, uriData):
		token = uriData.find(u'token').string
		cdn = uriData.find(u'cdn').string

		try:
			decodedToken = fourOD_token_decoder.Decode4odToken(token)
		except (Exception) as exception:
			print __plugin__, __version__,'GetAuthentication: Error getting decodedToken: ', exception
			return ("")

		if ( cdn ==  u"ll" ):
			ip = uriData.find(u'ip')
			e = uriData.find(u'e')

			if (ip):
				auth = u"e=%s&ip=%s&h=%s" % (e.string, ip.string, decodedToken)
			else:
				auth = "e=%s&h=%s" % (e.string, decodedToken)
		else:
			fingerprint = uriData.find('fingerprint').string
			slist = uriData.find('slist').string

			auth = "auth=%s&aifp=%s&slist=%s" % (decodedToken, fingerprint, slist)

		return auth

#==============================================================================
	def GetSwfPlayer(self):
		try:
			self.urlRoot = u"http://m.channel4.com"
			self.jsRoot = u"http://m.channel4.com/js/script.js"
			self.swfDefault = u"http://m.channel4.com/swf/mobileplayer-10.2.0-1.43.swf"

			jsHtml = None
			(jsHtml, isUK) = wgetUrl(self.jsRoot)

			# Looking for the string below
			"""
			getPlayerSwf:function(){return"swf/mobileplayer-10.2.0-1.43.swf"},
			"""
			pattern = u"options.swfPath = \"(/swf/mobileplayer-10.2.0-1.43.swf)\";"
			match = re.search(pattern, jsHtml, re.DOTALL | re.IGNORECASE)

			swfPlayer = self.urlRoot + match.group(1)

		except (Exception) as exception:
			if jsHtml is not None:
				msg = "jsHtml:\n\n%s\n\n" % jsHtml
				print __plugin__, __version__,"GetSwfPlayer: Error getting player: ", msg

			# Unable to determine swfPlayer URL. Using default:
			print __plugin__, __version__,"GetSwfPlayer: Unable to determine swfPlayer URL. Using default: ", exception
			swfPlayer = self.swfDefault

		return swfPlayer

#==============================================================================
	def getShowMediaData(self, weekList, showId):

		self.url = u"http://m.channel4.com/4od/%s%s" # (showId, /series-1 )
		channel = "CH4"
		short = ''
		name = ''
		date1 = ''
		stream = ''
		icon = ''
		duration = ''
		season = ''

		# Below is a sample of the returned data stream for a Show.
		"""
		<article class="episode clearfix" data-rating="18"
			 data-wsbrandtitle="/shameless" data-preselectasseturl="http://ais.channel4.com/asset/3270370"
			 data-preselectassetguidance="Very strong language and sexual scenes">

		<div class="screenshotCont">
		    <a href="">
			<img class="screenShot" src="http://cache.channel4.com/assets/programmes/images/shameless/series-1/episode-1/c06b3dbe-c9d6-4908-9f2c-708518482916_200x113.jpg" width="160" height="91"
			     alt="Shameless"><span></span>
		    </a>
		</div>
		<div class="details">
		    <h1>
			<a href="/4od/shameless/series-1/3270370">
				Shameless</a>
		    </h1>
			<p>
				Series 1
				Episode 1

			</p>
			<p>
			    12am
			     Tue 13 Jan
			     2004
			</p>
		    <p>
				Channel 4
			(49min)
			    <span class="guidance">Very strong language and sexual scenes</span>
		    </p>
		</div>
		<div class="rightLinks">
				 <a class="seeAll" href="/4od/shameless/series-1/3270370"><span>More</span></a>
		</div>
		</article>
		"""

		# Need to loop here until last page reached or 500 entries returned
		self.nextUrl = self.url % (showId, season)

		try:

			# Read the Show URL
			data = readUrl(self.nextUrl)

			# Only want to try and parse if stream data is returned.
			if data:
				# Use BeautifulSoup to parse the returned data
				soup = BeautifulSoup(data)
				
				# I'm afraid that each episode does not have it's own description.
				summary = soup.find("div", id="aboutTheShow").findAll('p')
				sum1 = str(summary[0])
				sum1 = re.sub('<p>', '', sum1)
				sum1 = re.sub('</p>', '', sum1)
				short = sum1.strip()

				entries = soup.find("section", id="episodeList").findAll('article')

				for entry in entries:

					details = entry.find('div', 'details')
					pList = details.findAll('p')

					try:
						assetUrl = entry['data-preselectasseturl']
						match = re.search(u'http://ais.channel4.com/asset/(\d+)', assetUrl)
						stream= str(match.group(1))
					except (Exception) as exception:
						stream = ""

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						try:
							icon = entry.find('img')['src']
						except (Exception) as exception:
							icon = ""
					else:
						icon = ''

					try:
						for p in pList:
							try:
								timeString = p.text.replace('\r\n', '').replace('Sept', 'Sep').replace('July', 'Jul').replace('June', 'Jun')
								timeString = re.sub(' +', ' ', timeString)
								time_split = timeString.rsplit('m ',1)
								lastDate = date.fromtimestamp(mktime(strptime(time_split[1].strip(), u"%a %d %b %Y")))
								premieredDate = lastDate.strftime(u"%a %b %d %Y")
								date1 = _("Added:")+" "+str(premieredDate)
								break
							except (Exception) as exception:
								date1 = ""
					except (Exception) as exception:
						print __plugin__, __version__,'getShowMediaData: name error: ', exception
						date1 = ""

					try:
						name_tmp = details.find('p').text.replace('\r\n', '')
						name_tmp1 = re.sub(' +', ' ', name_tmp)
						name_tmp1 = checkUnicode(str(name_tmp1))
						name = name_tmp1.strip()
					except (Exception) as exception:
						print __plugin__, __version__,'getShowMediaData: name error: ', exception
						name = ""
					
					try:
						pattern = u'\s*Channel\s4\s*\((.*?)\)'
						for p in pList:
							try:
								durationMatch = re.search( pattern, p.text, re.DOTALL | re.IGNORECASE )
								duration = _("Duration:")+" "+str(durationMatch.group(1))
								break
							except (Exception) as exception:
								duration = ""
					                    
					except (Exception) as exception:
						print __plugin__, __version__,'getShowMediaData: name error: ', exception
						duration = ""

					weekList.append((date1, name, short, channel, stream, icon, duration, False))

		except (Exception) as exception:
			print __plugin__, __version__,'getShowMediaData: Error parsing feed: ', exception

#==============================================================================
	def getCatsMediaData(self, weekList, category):

		self.url = u"http://m.channel4.com/4od/tags/%s%s%s" # % (category, /order?, /page-X? )
		channel = "CH4"
		short = ''
		name = ''
		date1 = ''
		stream = ''
		icon = ''
		duration = ''

		# Below is a sample of the returned data stream for a Category.
		"""
		{"count":50,"results":[
		    {    "title":"The Function Room",
			 "url":"/4od/the-function-room",
			 "img":"http://cache.channel4.com/assets/programmes/images/the-function-room/7d5d701c-f7f8-4357-a128-67cac7896f95_200x113.jpg"
		    },...        
		"""

		# You can specify the order and page number but I'm just hard-coding for now.
		page = '1'
		order = u'/atoz'
		
		# Need to loop here until last page is reached or 500 entries have been returned.
		self.nextUrl = self.url % (category, order, u'/page-%s' % page)

		try:
			# Read the Category URL
			(jsonText, isUK) = wgetUrl(self.nextUrl)

			# Only want to try and parse if stream data is returned.
			if jsonText:
				# Use JSON to parse the returned data
				jsonData = simplejson.loads(jsonText)

				entries = jsonData[u'results'] 

				for entry in entries:

					try:
						id = str(entry['url'])
						pattern = '/4od/(.+)'
						match = re.search(pattern, id, re.DOTALL | re.IGNORECASE)
						stream = str(match.group(1))
					except (Exception) as exception:
						stream = ""

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						try:
							icon = str(entry['img'])
						except (Exception) as exception:
							icon = ""
					else:
						icon = ''

					try:
						name_tmp = str(unicode(entry['title']))
						name_tmp1 = checkUnicode(name_tmp)
						name = remove_extra_spaces(name_tmp1)
					except (Exception) as exception:
						name = ""

					#try:
					#	short_tmp = str(entry['summary']['$'])
					#	short_tmp1 = checkUnicode(short_tmp)
					#	short = remove_extra_spaces(short_tmp1)
					#except (Exception) as exception:
					#	short = ""

					#try:
					#	lastDate = datetime.fromtimestamp(mktime(strptime(str(entry[u'dc:date.TXDate']), u"%Y-%m-%dT%H:%M:%S.%fZ")))
					#	date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
					#	date1 = _("Added:")+" "+str(date_tmp)
					#except (Exception) as exception:
					#	lastDate = datetime.fromtimestamp(mktime(strptime(str(entry[u'updated']), u"%Y-%m-%dT%H:%M:%S.%fZ")))
					#	date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
					#	date1 = _("Added:")+" "+str(date_tmp)

					weekList.append((date1, name, short, channel, stream, icon, duration, False))				

		except (Exception) as exception:
			print __plugin__, __version__,'getCatsMediaData: Error parsing feed: ', exception

#==============================================================================
	def getSearchMediaData(self, weekList, searchUrl):

		channel = "CH4"
		short = ''
		name = ''
		date1 = ''
		stream = ''
		icon = ''
		duration = ''

		try:
			# Read the Category URL
			(jsonText, isUK) = wgetUrl(searchUrl)
			
			# Only want to try and parse if stream data is returned.
			if jsonText:
				# We need to tidy the returned search results, format not json friendly
				jsonText = getJsonReady(jsonText)

				# Use JSON to parse the returned data
				jsonData = simplejson.loads(jsonText)

				if isinstance(jsonData['results'], list):
					entries = jsonData['results']
				else:
					# Single entry, put in a list
					entries = [ jsonData['results'] ] 

				# Loop through each of the search result entries.
				for entry in entries:

					# If this value is false then the programme is not available on 4OD
					if entry['fourOnDemand'] == "false":
						continue

					try:
						stream_tmp = str(unicode(entry[u'siteUrl']))
						stream_split = stream_tmp.rsplit('/',2)
						stream = str(stream_split[1])
					except (Exception) as exception:
						stream = ""

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						try:
							icon = str(unicode(entry[u'imgUrl']))
						except (Exception) as exception:
							icon = ""
					else:
						icon = ''

					try:
						name_tmp = str(unicode(entry[u'value']))
						name_tmp1 = checkUnicode(name_tmp)
						name = remove_extra_spaces(name_tmp1)
					except (Exception) as exception:
						name = ""

					try:
						short = "\nThe current list of episodes stored for " + str(name)
					except (Exception) as exception:
						short = ""

					weekList.append((date1, name, short, channel, stream, icon, duration, False))		

		except (Exception) as exception:
			print __plugin__, __version__,'getSearchMediaData: Error parsing feed: ', exception
			
#==============================================================================
def checkUnicode(value, **kwargs):
	stringValue = value 
	stringValue = stringValue.replace('&#39;', '\'')
	stringValue = stringValue.replace('&amp;', '&')
	return stringValue

#==============================================================================
def getJsonReady(value, **kwargs):
	stringValue = str(value)
	stringValue = stringValue.replace("(", "")
	stringValue = stringValue.replace(")", "")
	stringValue = stringValue.replace(";", "")
	stringValue = stringValue.replace("\\'s", "'s")
	return stringValue
	
#==========================================================================
def remove_extra_spaces(data):
	p = re.compile(r'\s+')
	return p.sub(' ', data)

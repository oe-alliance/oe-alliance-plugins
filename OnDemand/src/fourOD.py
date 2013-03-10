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
from Screens.MessageBox import MessageBox
from enigma import eServiceReference, eTimer, getDesktop
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.VirtualKeyBoard import VirtualKeyBoard
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

#=================== Default URL's =======================================================

fourodSearchDefault = u'http://www.channel4.com/search/predictive/?q='

#=========================================================================================
def wgetUrl(target):
	try:
		isUK = 0
		outtxt = ""
		
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
		# Now attempt to use TUNLR to bypass the Geo restriction.
		if outtxt.find('ERROR') > 0:
			print "Non UK Address"
			isUK = 1
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

		# Now return the decoded webpage
		return (outtxt, isUK)

	except (Exception) as exception:
		print "wgetUrl: Exception: ", exception
		outtxt = str(response.read())
		response.close()
		
		# If we managed to read the URL then return data, might have failed on decode.
		if outtxt:
			print "wgetUrl: Exception: outtxt: ", outtxt
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
		self.url = "http://ps3.channel4.com/pmlsd/tags.json?platform=ps3&uid=%d"
		osdList = []

		osdList.append((_("Search"), "search"))
		if self.action is "start":
			# Read the URL for the selected category on the Main Menu.
			try:
				(data, isUK) = wgetUrl(self.url % int(time.time()*1000))

				jsonData = simplejson.loads(data)

				if isinstance(jsonData['feed']['entry'], list):
					entries = jsonData['feed']['entry']
				else:
					# Single entry, put in a list
					entries = [ jsonData['feed']['entry'] ]

				#TODO Error handling?

				for entry in entries:
					"""
					{"link":
						{"self":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals.json?platform=ps3",
						"related":
							["http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals\/title.json?platform=ps3",
							"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals\/4od.json?platform=ps3",
							"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals\/4od\/title.json?platform=ps3"]
						},
					"$":"\n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n  ",
					"id":"tag:ps3.channel4.com,2009:\/programmes\/tags\/animals",
					"title":"Animals",
					"summary":
						{"@type":"html",
						"$":"Channel 4 Animals Programmes"
						},
					"updated":"2013-01-29T13:34:11.491Z",
					"dc:relation.CategoryType":"None",
					"dc:relation.AllProgrammeCount":5,
					"dc:relation.4oDProgrammeCount":1
					}
					"""
					if entry['dc:relation.4oDProgrammeCount'] == 0:
						continue

					id = entry[u'id']
					pattern = u'/programmes/tags/(.+)'
					match = re.search(pattern, id, re.DOTALL | re.IGNORECASE)

					categoryName = match.group(1)
					#label = unicode(entry[u'title']) + u' (' + unicode(entry['dc:relation.4oDProgrammeCount']) + u')'
					summary = unicode(entry[u'summary'][u'$']) + u' (' + unicode(entry['dc:relation.4oDProgrammeCount']) + u')' 
					
					osdList.append((_(str(summary)), str(categoryName)))

			except (Exception) as exception:
				print 'StreamsMenu: Error parsing feed: ', exception

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
				print 'go: Error getting fileUrl: ', exception

#==============================================================================
	def getRTMPUrl(self, assetUrl):
		playUrl = None

		try:
			(rtmpvar, returnMessage) = self.InitialiseRTMP(assetUrl)
			if rtmpvar:
				playUrl = rtmpvar.getPlayUrl()    

				return (playUrl, rtmpvar, returnMessage)
			else:
				return ("", "", returnMessage)

		except (Exception) as exception:
			print 'getRTMPUrl: Error getting playUrl: ', exception
			return ("", "", "")

#==============================================================================			
	def InitialiseRTMP(self, assetUrl):

		try:
			self.urlRoot = u"http://www.channel4.com"
			streamUri = ""
			auth = ""
			
			# Get the stream info
			(streamUri, auth, returnMessage) = self.GetStreamInfo(assetUrl)
			
			if streamUri:
				url = re.search('(.*?)mp4:', streamUri).group(1)
				app = re.search('.com/(.*?)mp4:', streamUri).group(1)
				playPath = re.search('(mp4:.*)', streamUri).group(1) + "?" + auth
				if "ll."  not in streamUri: 
					url = url + "?ovpfv=1.1&" + auth
					app = app + "?ovpfv=1.1&" + auth

				swfPlayer = self.GetSwfPlayer()
				rtmpvar = RTMP(rtmp = streamUri, app = app, swfVfy = swfPlayer, playPath = playPath, pageUrl = self.urlRoot)
				return (rtmpvar, returnMessage)
			else:
				return ("", returnMessage)
		except (Exception) as exception:
			print 'InitialiseRTMP: Error getting mp4: ', exception
			return ("", "")

#==============================================================================
	def GetStreamInfo(self, assetUrl):
		maxAttempts = 15
		
		streamURI = ""
		auth = ""
		returnMessage = "Non-UK User!!\n\nUnable to find playable Stream in "+str(maxAttempts)+" attempts!!\n\nPlease try again!"
		
		for attemptNumber in range(0, maxAttempts):
			(xml, isUK) = wgetUrl( assetUrl )
			
			# Parse the returned XML
			soup = BeautifulSoup(xml)

			uriData = soup.find(u'uridata')
			streamURI = uriData.find(u'streamuri').text
			
			# If call is from Outside UK then stream URL might need to be altered.
			if isUK == 1:
				print "GetStreamInfo: notUK user: streamURI: ", streamURI, " streamURI[:10]: ", streamURI[:10]
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
		
		if streamURI:
			return (streamURI, auth, "")
		else:
			return (streamURI, auth, returnMessage)

#==============================================================================
	def GetAuthentication(self, uriData):
		token = uriData.find(u'token').string
		cdn = uriData.find(u'cdn').string

		decodedToken = fourOD_token_decoder.Decode4odToken(token)

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
			self.ps3Root = u"http://ps3.channel4.com"
			self.swfDefault = u"http://ps3.channel4.com/swf/ps3player-9.0.124-1.27.2.swf"

			rootHtml = None
			(rootHtml, isUK) = wgetUrl(self.ps3Root)

			soup = BeautifulSoup(rootHtml)
			
			script = soup.find('script', src=re.compile('.+com.channel4.aggregated.+', re.DOTALL | re.IGNORECASE))
			jsUrl = script['src']

			jsHtml = None
			(jsHtml, isUK) = wgetUrl(self.ps3Root + '/' + jsUrl)
            
			# Looking for the string below
			"""
			getPlayerSwf:function(){return"swf/ps3player-9.0.124-1.27.2.swf"},
			"""
			pattern = "getPlayerSwf[^\"]+\"([^\"]+)\""
			match = re.search(pattern, jsHtml, re.DOTALL | re.IGNORECASE)

			swfPlayer = self.ps3Root + '/' + match.group(1)

		except (Exception) as exception:
			if rootHtml is not None:
				msg = "rootHtml:\n\n%s\n\n" % rootHtml
				print "GetSwfPlayer: Error getting player: ", msg

			if jsHtml is not None:
				msg = "jsHtml:\n\n%s\n\n" % jsHtml
				print "GetSwfPlayer: Error getting player: ", msg

			# Unable to determine swfPlayer URL. Using default:
			print "GetSwfPlayer: Unable to determine swfPlayer URL. Using default: ", exception
			swfPlayer = self.swfDefault

		return swfPlayer

#==============================================================================
	def getShowMediaData(self, weekList, showId):

		self.url = u"http://ps3.channel4.com/pmlsd/%s/4od.json?platform=ps3&uid=%s" # showId, time
		channel = "CH4"
		short = ''
		name = ''
		date = ''
		stream = ''
		icon = ''
		duration = ''

		# Below is a sample of the returned data stream for a Show.
		"""
		{"feed":
			{"link":
				{"self":"http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder.json?platform=ps3",
				"related":["http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/episode-guide.json?platform=ps3","http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/4od.json?platform=ps3","http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/4od\/recommendations.json?platform=ps3"]
				},
				"$":"\n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n",
				"id":"tag:ps3.channel4.com,2009:\/programmes\/the-horse-hoarder",
				"title":"The Horse Hoarder",
				"subtitle":
					{"@type":"html",
					"$":"Pensioner Clwyd Davies has accumulated 52 untamed horses, which he keeps at his home in Wrexham's suburbs"
					},
				"updated":"2013-01-07T12:30:53.872Z",
				"author":
					{"$":"\n	\n  ",
					"name":"Channel 4 Television"
					},
				"logo":
					{"@imageSource":"own",
					"$":"http:\/\/cache.channel4.com\/assets\/programmes\/images\/the-horse-hoarder\/ea8a20f0-2ba9-4648-8eec-d25a0fe35d3c_200x113.jpg"
					},
				"category":[
					{"@term":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals.atom?platform=ps3",
					"@scheme":"tag:ps3.channel4.com,2010:\/category\/primary",
					"@label":"Animals"
					},
					{"@term":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/documentaries.atom?platform=ps3",
					"@scheme":"tag:ps3.channel4.com,2010:\/category\/secondary",
					"@label":"Documentaries"
					}],
				"dc:relation.BrandFlattened":false,
				"dc:relation.presentationBrand":"C4",
				"dc:relation.platformClientVersion":1,
				"dc:relation.BrandWebSafeTitle":"the-horse-hoarder",
				"dc:relation.BrandTitle":"The Horse Hoarder",
				"dc:relation.ProgrammeType":"OOS",
				"generator":
					{"@version":"1.43","$":"PMLSD"},
				"entry":
					{"link":
						{"related":"http:\/\/ais.channel4.com\/asset\/3464654",
						"self":"http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/episode-guide\/series-1\/episode-1.json?platform=ps3"
						},
					"$":"\n	\n	\n	\n	\n	\n	\n	\n	\n	\n	\n	\n  ",
					"id":"tag:ps3.channel4.com,2009:\/programmes\/the-horse-hoarder\/episode-guide\/series-1\/episode-1",
					"title":"The Horse Hoarder",
					"summary":
						{"@type":"html",
						"$":"Pensioner Clwyd Davies squats in a derelict house, dedicating his life to caring for 52 wild horses. But he has been reported to the RSPCA. This documentary follows Clwyd's battle to keep his horses."
						},
					"updated":"2013-01-07T12:30:54.027Z",
					"content":
						{"$":"\n	  \n	",
						"thumbnail":
							{"@url":"http:\/\/cache.channel4.com\/assets\/programmes\/images\/the-horse-hoarder\/series-1\/episode-1\/e5c98d93-4f82-4174-b3f1-a1f7d180958a_200x113.jpg",
							"@height":"113",
							"@width":"200",
							"@imageSource":"own",
							"@altText":"The Horse Hoarder"
							}
						},
					"dc:relation.SeriesNumber":1,
					"dc:relation.EpisodeNumber":1,
					"dc:date.Last":"2013-01-07T20:30:00.000Z",
					"dc:relation.LastChannel":"C4"
				}
			}
		}
		"""

		# Need to loop here until last page reached or 500 entries returned
		self.nextUrl = self.url % (showId, int(time.time()*1000))

		try:
			while len(weekList) < 500 and self.nextUrl is not None:

				# Read the Show URL
				(jsonText, isUK) = wgetUrl(self.nextUrl)

				# Only want to try and parse if stream data is returned.
				if jsonText:
					# Use JSON to parse the returned data
					jsonData = simplejson.loads(jsonText)

					if isinstance(jsonData['feed']['entry'], list):
						entries = jsonData['feed']['entry']
					else:
						# Single entry, put in a list
						entries = [ jsonData['feed']['entry'] ]

					for entry in entries:

						try:
							stream = str(entry[u'group'][u'player']['@url'])
						except (Exception) as exception:
							stream = ""

						try:
							seriesNum = int(entry[u'dc:relation.SeriesNumber'])
						except (Exception) as exception:
							seriesNum = ""

						try:
							epNum = int(entry[u'dc:relation.EpisodeNumber'])
						except (Exception) as exception:
							epNum = ""

						try:
							seriesData = " (S"+str(("%02d" % seriesNum))+"E"+str(("%02d" % epNum))+")"
						except (Exception) as exception:
							seriesData = ""

						try:
							hasSubtitles = bool(entry['dc:relation.Subtitles'])
						except (Exception) as exception:
							hasSubtitles = False

						try:
							icon = str(entry[u'group'][u'thumbnail'][u'@url'])
						except (Exception) as exception:
							icon = ""

						try:
							lastDate = datetime.fromtimestamp(mktime(strptime(str(entry[u'dc:date.TXDate']), u"%Y-%m-%dT%H:%M:%S.%fZ")))
							date_tmp = lastDate.strftime(u"%a %b %d %Y")
							date1 = _("Added:")+" "+str(date_tmp)
						except (Exception) as exception:
							lastDate = datetime.fromtimestamp(mktime(strptime(str(entry[u'updated']), u"%Y-%m-%dT%H:%M:%S.%fZ")))
							date_tmp = lastDate.strftime(u"%a %b %d %Y")
							date1 = _("Added:")+" "+str(date_tmp)

						try:
							name_tmp = str(unicode(entry[u'title']))
							name_tmp1 = checkUnicode(name_tmp)
							name = remove_extra_spaces(name_tmp1)
							if seriesData:
								name = name+seriesData
						except (Exception) as exception:
							name = ""

						try:
							short_tmp = str(entry[u'summary'][u'$'])
							short_tmp1 = checkUnicode(short_tmp)
							short = remove_extra_spaces(short_tmp1)
						except (Exception) as exception:
							short = ""

						weekList.append((date1, name, short, channel, stream, icon, duration, False))

					if 'next' in jsonData['feed']['link']:
						self.nextUrl = jsonData['feed']['link']['next']
					else:
						self.nextUrl = None

		except (Exception) as exception:
			print 'getShowMediaData: Error parsing feed: ', exception

#==============================================================================
	def getCatsMediaData(self, weekList, category):

		self.url = u"http://ps3.channel4.com/pmlsd/tags/%s/4od/title.json?platform=ps3" #category
		channel = "CH4"
		short = ''
		name = ''
		date1 = ''
		stream = ''
		icon = ''
		duration = ''

		# Below is a sample of the returned data stream for a Category.
		"""
		{"feed":
		    {"link":
			{"self":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals\/4od.json?platform=ps3",
			"up":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals.json?platform=ps3"},
			"$":"\n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n",
			"id":"tag:ps3.channel4.com,2009:\/programmes\/tags\/animals\/4od",
			"title":"4oD Animals Programmes",
			"updated":"2013-01-29T15:12:58.105Z",
			"author":
			    {"$":"\n    \n  ",
			    "name":"Channel 4 Television"
			    },
			"logo":
			    {"@imageSource":"default",
			    "$":"http:\/\/cache.channel4.com\/static\/programmes\/images\/c4-atom-logo.gif"
			    },
			"fh:complete":"",
			"dc:relation.CategoryType":"None",
			"dc:relation.AllProgrammeCount":5,
			"dc:relation.4oDProgrammeCount":1,
			"dc:relation.platformClientVersion":1,
			"generator":{"@version":"1.43","$":"PMLSD"},
			"entry":
			    {"link":
				{"self":"http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder.json?platform=ps3",
				"related":["http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/4od.json?platform=ps3",
				"http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/episode-guide.json?platform=ps3"]
				},
			    "$":"\n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n  ",
			    "id":"tag:ps3.channel4.com,2009:\/programmes\/the-horse-hoarder",
			    "title":"The Horse Hoarder",
			    "summary":
				{"@type":"html",
				"$":"Pensioner Clwyd Davies has accumulated 52 untamed horses, which he keeps at his home in Wrexham's suburbs"
				},
			    "updated":"2013-01-07T12:30:53.872Z",
			    "dc:relation.sortLetter":"H",
			    "dc:date.TXDate":"2013-01-13T02:40:00.000Z",
			    "dc:relation.BrandWebSafeTitle":"the-horse-hoarder",
			    "content":
				{"$":"\n      \n
				    ",
				"thumbnail":
				    {"@url":"http:\/\/cache.channel4.com\/assets\/programmes\/images\/the-horse-hoarder\/ea8a20f0-2ba9-4648-8eec-d25a0fe35d3c_200x113.jpg",
				    "@height":"113",
				    "@width":"200",
				    "@imageSource":"own",
				    "@altText":"The Horse Hoarder"
				    }
				}
			    }
			}
		}

		"""

		# Need to loop here until last page is reached or 500 entries have been returned.
		self.nextUrl = self.url % category

		try:
			while len(weekList) < 500 and self.nextUrl is not None:

				# Read the Category URL
				(jsonText, isUK) = wgetUrl(self.nextUrl)

				# Only want to try and parse if stream data is returned.
				if jsonText:
					# Use JSON to parse the returned data
					jsonData = simplejson.loads(jsonText)

					if isinstance(jsonData['feed']['entry'], list):
						entries = jsonData['feed']['entry']
					else:
						# Single entry, put in a list
						entries = [ jsonData['feed']['entry'] ] 

					for entry in entries:

						try:
							id = str(entry['id'])
							pattern = '/programmes/(.+)'
							match = re.search(pattern, id, re.DOTALL | re.IGNORECASE)
							stream = str(match.group(1))
						except (Exception) as exception:
							stream = ""

						try:
							icon = str(entry['content']['thumbnail']['@url'])
						except (Exception) as exception:
							icon = ""

						try:
							name_tmp = str(unicode(entry['title']))
							name_tmp1 = checkUnicode(name_tmp)
							name = remove_extra_spaces(name_tmp1)
						except (Exception) as exception:
							name = ""

						try:
							short_tmp = str(entry['summary']['$'])
							short_tmp1 = checkUnicode(short_tmp)
							short = remove_extra_spaces(short_tmp1)
						except (Exception) as exception:
							short = ""

						try:
							lastDate = datetime.fromtimestamp(mktime(strptime(str(entry[u'dc:date.TXDate']), u"%Y-%m-%dT%H:%M:%S.%fZ")))
							date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
							date1 = _("Added:")+" "+str(date_tmp)
						except (Exception) as exception:
							lastDate = datetime.fromtimestamp(mktime(strptime(str(entry[u'updated']), u"%Y-%m-%dT%H:%M:%S.%fZ")))
							date_tmp = lastDate.strftime(u"%a %b %d %Y %H:%M")
							date1 = _("Added:")+" "+str(date_tmp)

						weekList.append((date1, name, short, channel, stream, icon, duration, False))

					if 'next' in jsonData['feed']['link']:
						self.nextUrl = jsonData['feed']['link']['next']
					else:
						self.nextUrl = None				

		except (Exception) as exception:
			print 'getCatsMediaData: Error parsing feed: ', exception

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

					try:
						icon = str(unicode(entry[u'imgUrl']))
					except (Exception) as exception:
						icon = ""

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
			print 'getSearchMediaData: Error parsing feed: ', exception
			
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

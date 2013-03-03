
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

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from enigma import eServiceReference, eTimer, getDesktop
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.VirtualKeyBoard import VirtualKeyBoard
from os import path as os_path, remove as os_remove, mkdir as os_mkdir, walk as os_walk

from datetime import date
from time import strftime

import urllib2, re

import xml.dom.minidom as dom
from dns.resolver import Resolver

from CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler

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

class BBCiMenu(Screen):
	print "BBCiMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="BBC iPlayer" >
		<widget name="BBCiMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""
			
	def __init__(self, session, action, value):
		
		self.imagedir = "/tmp/openBbcImg/"
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		if self.action is "start":
			print "start"
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
		
		if returnValue is "exit":
				self.removeFiles(self.imagedir)
				self.close(None)
		elif self.action is "start":
			if returnValue is "bbc1":
				self.session.open(StreamsThumb, "bbc1", "BBC One", "http://feeds.bbc.co.uk/iplayer/bbc_one/list")
			elif returnValue is "bbc2":
				self.session.open(StreamsThumb, "bbc2", "BBC Two", "http://feeds.bbc.co.uk/iplayer/bbc_two/list")
			elif returnValue is "bbc3":
				self.session.open(StreamsThumb, "bbc3", "BBC Three", "http://feeds.bbc.co.uk/iplayer/bbc_three/list")
			elif returnValue is "bbc4":
				self.session.open(StreamsThumb, "bbc4", "BBC Four", "http://feeds.bbc.co.uk/iplayer/bbc_four/list")
			elif returnValue is "cbbc":
				self.session.open(StreamsThumb, "cbbc", "CBBC", "http://feeds.bbc.co.uk/iplayer/cbbc/list")
			elif returnValue is "cbeeb":
				self.session.open(StreamsThumb, "cbeeb", "Cbeebies", "http://feeds.bbc.co.uk/iplayer/cbeebies/list")
			elif returnValue is "bbcp":
				self.session.open(StreamsThumb, "bbcp", "BBC Parliamanent", "http://feeds.bbc.co.uk/iplayer/bbc_parliament/list")
			elif returnValue is "bbcn":
				self.session.open(StreamsThumb, "bbcn", "BBC News", "http://feeds.bbc.co.uk/iplayer/bbc_news24/list")
			elif returnValue is "bbca":
				self.session.open(StreamsThumb, "bbca", "BBC Alba", "http://feeds.bbc.co.uk/iplayer/bbc_alba/list")
			elif returnValue is "bbchd":
				self.session.open(StreamsThumb, "bbchd", "BBC HD", "http://feeds.bbc.co.uk/iplayer/bbc_hd/list")
			elif returnValue is "bbchighlights":
				self.session.open(StreamsThumb, "bbchighlights", "TV Highlights", "http://feeds.bbc.co.uk/iplayer/highlights/tv")
			elif returnValue is "bbcpopular":
				self.session.open(StreamsThumb, "bbcpopular", "Most Popular TV", "http://feeds.bbc.co.uk/iplayer/popular/tv")
			elif returnValue is "bbcdrama":
				self.session.open(StreamsThumb, "bbcdrama", "Drama", "http://feeds.bbc.co.uk/iplayer/categories/drama/tv/list")
			elif returnValue is "bbcentertainment":
				self.session.open(StreamsThumb, "bbcentertainment", "Entertainment", "http://feeds.bbc.co.uk/iplayer/categories/entertainment/tv/list")
			elif returnValue is "bbcfactual":
				self.session.open(StreamsThumb, "bbcfactual", "Factual", "http://feeds.bbc.co.uk/iplayer/categories/factual/tv/list")
			elif returnValue is "bbcsigned":
				self.session.open(StreamsThumb, "bbcsigned", "Signed", "http://feeds.bbc.co.uk/iplayer/categories/signed/tv/list")
			elif returnValue is "bbconedrama":
				self.session.open(StreamsThumb, "bbconedrama", "BBC One Drama", "http://feeds.bbc.co.uk/iplayer/bbc_one/drama/tv/list")
			elif returnValue is "bbccomedy":
				self.session.open(StreamsThumb, "bbccomedy", "Comedy", "http://feeds.bbc.co.uk/iplayer/comedy/tv/list")
			elif returnValue is "bbchealth":
				self.session.open(StreamsThumb, "bbchealth", "Health And Wellbeing", "http://feeds.bbc.co.uk/iplayer/bbc_three/factual/health_and_wellbeing/tv/list")
			elif returnValue is "bbcwales":
				self.session.open(StreamsThumb, "bbcwales", "BBC Wales", "http://feeds.bbc.co.uk/iplayer/wales/tv/list")
			elif returnValue is "bbcscotland":
				self.session.open(StreamsThumb, "bbcscotland", "BBC Scotland", "http://feeds.bbc.co.uk/iplayer/scotland/tv/list")
			elif returnValue is "bbcni":
				self.session.open(StreamsThumb, "bbcni", "BBC Northern Ireland", "http://feeds.bbc.co.uk/iplayer/northern_ireland/tv/list")
			elif returnValue is "film":
				self.session.open(StreamsThumb, "film", "Movies", "http://feeds.bbc.co.uk/iplayer/films/tv/list")
			elif returnValue is "bbckids":
				self.session.open(StreamsThumb, "bbckids", "Kids", "http://feeds.bbc.co.uk/iplayer/childrens/tv/list")
			elif returnValue is "bbcnews":
				self.session.open(StreamsThumb, "bbcnews", "BBC News", "http://feeds.bbc.co.uk/iplayer/news/tv/list/")
			elif returnValue is "bbcmusic":
				self.session.open(StreamsThumb, "bbcmusic", "Music", "http://feeds.bbc.co.uk/iplayer/music/tv/list")
			elif returnValue is "bbcsoaps":
				self.session.open(StreamsThumb, "bbcsoaps", "Soaps", "http://feeds.bbc.co.uk/iplayer/soaps/tv/list")
			elif returnValue is "bbcsport":
				self.session.open(StreamsThumb, "bbcsport", "Sport", "http://feeds.bbc.co.uk/iplayer/sport/tv/list")
			elif returnValue is "bbcreligous":
				self.session.open(StreamsThumb, "bbcreligous", "Religion", "http://feeds.bbc.co.uk/iplayer/religion_and_ethics/tv/list")

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
		
		self.imagedir = "/tmp/onDemandImg/"
		self.defaultImg = "Extensions/OnDemand/icons/bbciplayer.png"
		
		if (os_path.exists(self.imagedir) != True):
			os_mkdir(self.imagedir)

		self['list'] = EpisodeList(self.defaultImg)
		
		self.updateMenu()
		self["actions"] = ActionMap(["SetupActions", "WizardActions", "MovieSelectionActions", "DirectionActions"],
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
		self.setTitle("BBC iPlayer: Listings for " +self.title)

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

	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return
		
		self.getMediaData(self.mediaList, self.url)
		if len(self.mediaList) == 0:
			self.mediaProblemPopup("No Episodes Found!")
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

	def mediaProblemPopup(self, error):
		self.session.openWithCallback(self.close, MessageBox, _(error), MessageBox.TYPE_ERROR, timeout=5, simple = True)

	def go(self):
		showID = self["list"].l.getCurrentSelection()[4]
		showName = self["list"].l.getCurrentSelection()[1]
		returnedData = (showID,showName)
		print "showID", showID
		print "showName", showName
		self.session.open(bbcStreamUrl, "bbcStreamUrl", returnedData)

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
		
		links = (re.compile ('<entry>\n    <title type="text">(.+?)</title>\n    <id>tag:feeds.bbc.co.uk,2008:PIPS:(.+?)</id>\n    <updated>(.+?)</updated>\n    <content type="html">\n      &lt;p&gt;\n        &lt;a href=&quot;.+?&quot;&gt;\n          &lt;img src=&quot;(.+?)&quot; alt=&quot;.+?&quot; /&gt;\n        &lt;/a&gt;\n      &lt;/p&gt;\n      &lt;p&gt;\n        (.+?)\n      &lt;/p&gt;\n    </content>').findall(data))
	        		
		for line in links:
			name = checkUnicode(line[0])
			stream = line[1]
			
			# Format the date to display onscreen
			year = int(line[2][0:4])
			month = int(line[2][5:7])
			day = int(line[2][8:10])
			oldDate = date(int(year), int(month), int(day)) # year, month, day
			dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
			date_tmp = dayofWeek[date.weekday(oldDate)] + " " + oldDate.strftime("%d %b %Y") + " " +line[2][11:16]
			date1 = _("Date Aired:")+" "+str(date_tmp)
			icon = line[3]
			icon_type = '.jpg'
			short = checkUnicode(line[4])
			channel = ""
			weekList.append((date1, name, short, channel, stream, icon, icon_type, False))
			

###########################################################################
class bbcStreamUrl(Screen):
	print "BBC One"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="" >
		<widget name="bbcStreamUrl" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		Screen.__init__(self, session)
		self.action = action
		returnValue = value
		osdList = []
		self.notUK = 0
		self.title = returnValue[1]
		fileUrl = returnValue[0]
		#print 'title',self.title
		#print 'fileurl',fileUrl
		url1 = 'http://www.bbc.co.uk/iplayer/playlist/'+fileUrl
		req = urllib2.Request(url1)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		try:
			links = (re.compile ('<mediator identifier="(.+?)" name=".+?" media_set=".+?"/>').findall(html)[1])
		except:
			links = (re.compile ('<mediator identifier="(.+?)" name=".+?" media_set=".+?"/>').findall(html)[0])
		#print 'links',links
		url2 = 'http://www.bbc.co.uk/mediaselector/4/mtis/stream/'+links
		#print 'url2',url2
		req = urllib2.Request(url2)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html1 = str(response.read())
		#print 'html1',html1
		response.close()
		
		if html1.find('notukerror') > 0:
			self.notUK = 1
			print "Non UK Address"
			opener = urllib2.build_opener(MyHTTPHandler)
			old_opener = urllib2._opener
			urllib2.install_opener (opener)
			#print 'links',links
			url2 = 'http://www.bbc.co.uk/mediaselector/4/mtis/stream/'+links
			#print 'url2',url2
			req = urllib2.Request(url2)
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
			response = urllib2.urlopen(req)
			html1 = str(response.read())
			#print 'html1',html1
			response.close()
			urllib2.install_opener (old_opener)

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
				returnedList = self.getHosts(conn, self.title, service)
				if returnedList[0].find('akamai') > 0 and self.notUK == 1:
					print "Not UK no Akamai"
				else:
					osdList.append(returnedList)
				#print osdList
				conn  = media[i].getElementsByTagName( "connection" )[1]
				returnedList = self.getHosts(conn, self.title, service)
				#print "returnedList", returnedList
				if returnedList[0].find('akamai') > 0 and self.notUK == 1:
					print "Not UK no Akamai"
				else:
					osdList.append(returnedList)
				#print osdList
				
			i=i+1
			
		
		osdList.sort()
		osdList.append((_("Exit"), "exit"))

		Screen.__init__(self, session)
		self["bbcStreamUrl"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_(self.title + " Choose Bitrate"))
	

	def getHosts(self, conn, title, service):
		#print conn
		identifier  = conn.attributes['identifier'].nodeValue
		#print identifier
		server = conn.attributes['server'].nodeValue
		#print server
		auth = conn.attributes['authString'].nodeValue
		#print auth
		supplier = conn.attributes['supplier'].nodeValue
		#print supplier
		try:
			application = conn.attributes['application'].nodeValue
			#print application
		except:
			print "application missing"
			application = "none"
		if supplier == 'limelight':
			print "limelight"
			fileUrl = "rtmp://"+server+":1935/ app=a1414/e3?"+auth+" tcurl=rtmp://"+server+":1935/a1414/e3?"+auth+" playpath="+identifier+" swfurl=http://www.bbc.co.uk/emp/10player.swf swfvfy=true timeout=180"
		elif supplier == 'akamai':
			print "akamai"
			fileUrl = "rtmp://"+server+":1935/ondemand?"+auth+" playpath="+identifier+" swfurl=http://www.bbc.co.uk/emp/10player.swf swfvfy=true timeout=180"
		if service == 'iplayer_streaming_h264_flv_vlo':
			bitrate = 400
		elif service == 'iplayer_streaming_h264_flv_lo':
			bitrate = 480
		elif service == 'iplayer_streaming_h264_flv':
			bitrate = 800
		elif service == 'iplayer_streaming_h264_flv_high':
			bitrate = 1500
		
		#print "###fileUrl###"
		#print fileUrl
		fileUrlTitle = []
		fileUrlTitle.append(fileUrl)
		fileUrlTitle.append(title)
		returnList = ((_(str(bitrate)+" "+str(supplier)), fileUrlTitle))
		return returnList 


	def go(self):
		returnValue = self["bbcStreamUrl"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			else:
				#print "returnValue",returnValue
				title = returnValue[1]
				fileUrl = returnValue[0]
				#print 'title',title
				#print 'fileUrl',fileUrl
				
				fileRef = eServiceReference(4097,0,str(fileUrl))
				fileRef.setName (title) 
				lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
				self.session.open(MoviePlayer, fileRef, None, lastservice)

	def cancel(self):
		self.close(None)

########################################################################### 
def main(session, **kwargs):
	action = "start"
	value = 0 
	start = session.open(BBCiMenu, action, value)

###########################################################################	

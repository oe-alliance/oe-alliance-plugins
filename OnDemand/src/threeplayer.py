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

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from ServiceReference import ServiceReference
from enigma import eServiceReference, eConsoleAppContainer, ePicLoad, getDesktop, eServiceCenter
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from cookielib import CookieJar
import urllib, urllib2, re, time, os
from bs4 import BeautifulSoup

##########################################################################
class ShowHelp(Screen):
	skin = """
		<screen position="center,center" size="700,400" title="3Player">
			<widget name="myLabel" position="10,0" size="680,380" font="Console;18"/>
			</screen>"""
	def __init__(self, session, args = None):
		self.session = session

		Screen.__init__(self, session)
		#Help text
		text = """
	3Player Alpha 2
	rogerthis 2013
	
	Change Log
	
	Alpha 2
	Added more
	
	Alpha 1
	initial release
	
	Main support on www.world-of-satellite.com
		"""
		
		self["myLabel"] = ScrollLabel(text)
		self["myActionMap"] = ActionMap(["WizardActions", "SetupActions", "ColorActions"],
		{
		"cancel": self.close,
		"ok": self.close,
		"up": self["myLabel"].pageUp,
		"down": self["myLabel"].pageDown,
		}, -1)
		
##########################################################################
class threeMainMenu(Screen):
	#print	"MainMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="3Player - Main Menu" >
		<widget name="threeMainMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""
			

		
	def __init__(self, session, action, value):
		
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		
		if self.action is "start":
			#print	"start"
			osdList.append((_("Most Talked About"), "talked"))
			osdList.append((_("Straight Off The Telly"), "straight"))
			osdList.append((_("Going, Going..."), "going"))
			osdList.append((_("All Shows"), "all_shows"))
		
		
		osdList.append((_("Help & About"), "help"))
		osdList.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["threeMainMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1)	  
		
	
	def go(self):
		returnValue = self["threeMainMenu"].l.getCurrentSelection()[1]
		
		if returnValue is "help":
				self.session.open(ShowHelp)
		elif returnValue is "exit":
				self.close(None)
			
		
		elif self.action is "start":
			if returnValue is "talked":
				self.session.open(talkedMenu, "talked", "0")
			elif returnValue is "straight":
				self.session.open(straightMenu, "straight", "0")
			elif returnValue is "going":
				self.session.open(goingMenu, "going", "0")
			elif returnValue is "all_shows":
				self.session.open(allShowsMenu, "all_shows", "0")
			


	def cancel(self):
		self.close(None)
###########################################################################
class talkedMenu(Screen):
	#print	"talkedMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="3Player - Latest" >
		<widget name="talkedMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		#print	"########latest#################"
		url = "http://www.tv3.ie/3player"
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		soup = BeautifulSoup(''.join(html));
		slider1 = soup.find('div', id='slider1')
		for mymatch in slider1.findAll('div', id=(('gridshow'), ('gridshow-right'))):
			try:
				url = mymatch.a['href']
				print url
				description = str(mymatch.a['title'])
				description = description[10:]
				print description
				osdList.append((_(description), url))
			except:
				print "filed"

		osdList.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["talkedMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1) 
		
	def go(self):
		returnValue = self["talkedMenu"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			else:
				#print	"returnValue"
				#print	returnValue
				fileUrl = findPlayUrl(returnValue)
				try:
					fileRef = eServiceReference(4097,0,fileUrl)
					returnValue = self.session.open(MoviePlayer, fileRef)
				except:
					self.session.open(MessageBox,_("Host Resolver > Unable to resolve:\n" + self["myMenu"].l.getCurrentSelection()[0]), MessageBox.TYPE_ERROR, timeout = 5)
 
	def cancel(self):
		self.close(None) 
		
###########################################################################
class straightMenu(Screen):
	#print	"straightMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="3Player - Latest" >
		<widget name="straightMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		#print	"########latest#################"
		url = "http://www.tv3.ie/3player"
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		soup = BeautifulSoup(''.join(html));
		slider1 = soup.find('div', id='slider2')
		for mymatch in slider1.findAll('div', id=(('gridshow'), ('gridshow-right'))):
			url = mymatch.a['href']
			print url
			description = str(mymatch.a['title'])
			description = description[10:]
			print description
			osdList.append((_(description), url))

		osdList.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["straightMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1) 
		
	def go(self):
		returnValue = self["straightMenu"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			else:
				#print	"returnValue"
				#print	returnValue
				fileUrl = findPlayUrl(returnValue)
				fileRef = eServiceReference(4097,0,fileUrl)
				returnValue = self.session.open(MoviePlayer, fileRef)
 
	def cancel(self):
		self.close(None)
###########################################################################
class goingMenu(Screen):
	#print	"goingMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="3Player - Latest" >
		<widget name="goingMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		#print	"########latest#################"
		url = "http://www.tv3.ie/3player"
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		soup = BeautifulSoup(''.join(html));
		slider1 = soup.find('div', id='slider3')
		for mymatch in slider1.findAll('div', id=(('gridshow'), ('gridshow-right'))):
			url = mymatch.a['href']
			#print url
			description = str(mymatch.a['title'])
			description = description[10:]
			#print description
			osdList.append((_(description), url))

		osdList.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["goingMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1) 
		
	def go(self):
		returnValue = self["goingMenu"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			else:
				#print	"returnValue"
				#print	returnValue
				fileUrl = findPlayUrl(returnValue)
				fileRef = eServiceReference(4097,0,fileUrl)
				returnValue = self.session.open(MoviePlayer, fileRef)
 
	def cancel(self):
		self.close(None) 
###########################################################################		   
class allShowsMenu(Screen):
	#print	"allShowsMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="3Player - Latest" >
		<widget name="allShowsMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		#print	"########latest#################"
		url = "http://www.tv3.ie/3player/allshows"
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		links = (re.compile ('<div id="tooltip_header" class="shadow"><h3><a href="(.+?)">(.+?)</a></h3>').findall(html))
		print links
		for link in links:
			print link[1]
			osdList.append((_(link[1]), "http://www.tv3.ie"+link[0]))

		osdList.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["allShowsMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1) 
		
	def go(self):
		returnValue = self["allShowsMenu"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			else:
				
				self.session.open(showListMenu, "showListMenu", returnValue)
 
	def cancel(self):
		self.close(None) 
###########################################################################
class showListMenu(Screen):
	#print	"talkedMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="3Player - Latest" >
		<widget name="talkedMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, action, value):
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		#print	"########latest#################"
		url = self.value
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		soup = BeautifulSoup(''.join(html));
		slider1 = soup.find('div', id='slider1')
		for mymatch in slider1.findAll('div', id=(('gridshow'), ('gridshow-right'))):
			url = mymatch.a['href']
			print url
			description = str(mymatch.a['title'])
			description = description[10:]
			print description
			osdList.append((_(description), url))

		osdList.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["talkedMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1) 
		
	def go(self):
		returnValue = self["talkedMenu"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "exit":
				self.close(None)
			else:
				#print	"returnValue"
				#print	returnValue
				fileUrl = findPlayUrl(returnValue)
				fileRef = eServiceReference(4097,0,fileUrl)
				returnValue = self.session.open(MoviePlayer, fileRef)
 
	def cancel(self):
		self.close(None) 
		
		
###########################################################################
 
def findPlayUrl(value, **kwargs):
	fileUrl = ""
	url = value
	try:
		url1 = 'http://www.tv3.ie/'+url
		req = urllib2.Request(url1)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		html = str(response.read())
		response.close()
		links = (re.compile ('url: "mp4:(.+?)",\r\n\t\t\t\t		   autoPlay: true,\r\n\t\t\t\t\t\tautoBuffering: true,\r\n\t\t\t\t		  provider: "rtmp"\r\n\t\t\t\t\t}\r\n\t\t\t\t],\r\n\t\t\t\t\r\n\t\t\t\t// All FP Plug ins:\r\n\t\t\t\tplugins:\r\n\t\t\t\t{	 \r\n\t\t\t\t\tcontrols:  \r\n\t\t\t\t\t{\r\n\t\t\t\t\t\turl:"flowplayer.controls.gc-build-112011.swf"\r\n\t\t\t\t\t}\r\n\t\t\t\t\t\r\n\t\t\t\t\t,\r\n\r\n\t\t\t\t\trtmp: {\r\n\t\t\t\t\t\turl: "flowplayer.rtmp-3.2.3.swf",\r\n\t\t\t\t\t\tnetConnectionUrl: "rtmp://.+?content/videos/(.+?)/"\r\n').findall(html)[0])
		print links
		fileUrl = 'http://content.tv3.ie/content/videos/'+links[1]+'/'+links[0]
	except:
		print "failed findPlayUrl"
	
	
	
	return fileUrl
	
###########################################################################
def checkUnicode(value, **kwargs):
	stringValue = value 
	#print	"stringValue"
	#print	stringValue
	returnValue = stringValue.replace('&#39;', '\'')
	return returnValue
###########################################################################
def main(session, **kwargs):
	action = "start"
	value = 0 
	start = session.open(threeMainMenu, action, value)
	#session.open(RTEMenu)
###########################################################################	   
class MoviePlayer(MP_parent):
	def __init__(self, session, service):
		self.session = session
		self.WithoutStopClose = False
		MP_parent.__init__(self, self.session, service)
###########################################################################
def Plugins(**kwargs):
	return PluginDescriptor(
		name="3Player",
		description="3Player - Irish Video On Demand Service",
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon="./rteplayer.png",
		fnc=main)

# coding: utf-8
###########################################################################
##################### By:subixonfire  www.satforum.me #####################

""" This file is part of ITV Player E2 Plugin.

	ITV Player E2 Plugin is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	ITV Player E2 Plugin is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with Foobar.	If not, see <http://www.gnu.org/licenses/>."""
	
###########################################################################
# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from ServiceReference import ServiceReference
from enigma import eServiceReference, eConsoleAppContainer, ePicLoad, getDesktop, eServiceCenter, loadPic
from Components.MenuList import MenuList
from Components.Input import Input
from Components.Pixmap import Pixmap
from Screens.InputBox import InputBox
from Components.ActionMap import ActionMap
from Tools.Directories import fileExists
from cookielib import CookieJar
import urllib, urllib2, re, time, os, random
import socket
socket.setdefaulttimeout(300) #in seconds
import httplib
from dns.resolver import Resolver

	 

###########################################################################

class ITVplayer(Screen):
	print "ITVPlayer"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="ITV Player" >
		<widget name="myMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""
			
	fileTitle1 = ""
	fileTitle2 = ""
	theFunc = "main"
	downDir = "/mnt/hdd"
	oldlist = []
	osdList = []
	osdList.append((_("ITV Player	 (This will take some time to load.)"), "itv"))
	osdList.append((_("Back"), "exit"))
	historyList = []
	historyInt = 0
	rtmp = ""
	
		
	def __init__(self, session):
		
	   
		Screen.__init__(self, session)
		self["myMenu"] = MenuList(self.osdList)
		self['pix'] = Pixmap()
		self["myActionMap"] = ActionMap(["SetupActions","ColorActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1)
		
		   
		
	
	def go(self):
		
		returnTitle = self["myMenu"].l.getCurrentSelection()[0]
		returnValue = self["myMenu"].l.getCurrentSelection()[1]
		returnIndex = self["myMenu"].getSelectedIndex()
		if returnValue is "exit":
			self.close(None)

		if not self.theFunc == "itv2": 
			if not returnValue == "help":
				try:
					self.historyList[int(self.historyInt)] = [self.theFunc, self.osdList, returnIndex]
				except:	   
					self.historyList.append([self.theFunc, self.osdList, returnIndex])
				self.historyInt = self.historyInt + 1
		
		
		if self.theFunc == "main":
			if returnValue == "itv":
			   
				self.oldList = self.osdList
				
				
				url = "http://www.itv.com/_data/xml/CatchUpData/CatchUp360/CatchUpMenu.xml"
	
				try:
					req = urllib2.Request(url,)
					req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
					response = urllib2.urlopen(req)	  
					htmldoc = str(response.read())
					response.close()
					print htmldoc 
				except :
					print "jebiga gethtml"
				
				
				
				
				xList = (re.compile ('<ProgrammeId>(.+?)</ProgrammeId>.+?<ProgrammeTitle>(.+?)</ProgrammeTitle>',re.DOTALL).findall(htmldoc))
				#for x in xList:
	
					#try:	 
					#	 progTitle = re.search('<ProgrammeTitle>(.*?)</ProgrammeTitle>', x).group(1)
					#	 progId = re.search('<ProgrammeId>(.+?)</ProgrammeId>', x).group(1)
					#except:
					#	 pass
					#self.osdList.append((_(progTitle), progId))
				self.osdList = [(x[1], x[0]) for x in xList]
				self["myMenu"].setList(self.osdList) 
				   
			   
				self.theFunc = "itv"
				
			if returnValue == "exit":
				self.close(None)
						
		elif self.theFunc == "itv":
		
			self.oldList = self.osdList
			
			url = "http://www.itv.com/_app/Dynamic/CatchUpData.ashx?ViewType=1&Filter=" + returnValue + "&moduleID=115107"
	
			try:
				req = urllib2.Request(url, "GET")
				req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
				response = urllib2.urlopen(req)	  
				htmldoc = str(response.read())
				response.close() 
			except :
				print "jebiga gethtml"
	
			xList = (re.compile ('<h3><a href=".+?Filter=([0-9]+?)">(.+?)</a></h3>.+?<p class="date">(.+?)</p>',re.DOTALL).findall(htmldoc))
			self.osdList = [(x[1] + " " + x[2], x[0]) for x in xList]
			self["myMenu"].setList(self.osdList)
			
			self.theFunc = "itv1"
			
			
		elif self.theFunc == "itv1":
		
			self.fileTitle1 = returnTitle
			self.fileTitle2 = ""
			
			self.oldList = self.osdList
			
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
	"""%returnValue
	
			url = 'http://mercury.itv.com/PlaylistService.svc'

			try:
				req = urllib2.Request(url, soapMessage)
				req.add_header("Host","mercury.itv.com")
				req.add_header("Referer","http://www.itv.com/mercury/Mercury_VideoPlayer.swf?v=1.6.479/[[DYNAMIC]]/2")
				req.add_header("Content-type","text/xml; charset=\"UTF-8\"")
				req.add_header("Content-length","%d" % len(soapMessage))
				req.add_header("SOAPAction","http://tempuri.org/PlaylistService/GetPlaylist")	 
				response = urllib2.urlopen(req)	  
				htmldoc = str(response.read())
				response.close()
			except urllib2.HTTPError, exception:
				exResp = str(exception.read())
				
				if 'InvalidGeoRegion' in exResp:
					print "Non UK Address"
					opener = urllib2.build_opener(MyHTTPHandler)
					old_opener = urllib2._opener
					urllib2.install_opener (opener)
					req = urllib2.Request(url, soapMessage)
					req.add_header("Host","mercury.itv.com")
					req.add_header("Referer","http://www.itv.com/mercury/Mercury_VideoPlayer.swf?v=1.6.479/[[DYNAMIC]]/2")
					req.add_header("Content-type","text/xml; charset=\"UTF-8\"")
					req.add_header("Content-length","%d" % len(soapMessage))
					req.add_header("SOAPAction","http://tempuri.org/PlaylistService/GetPlaylist")	 
					response = urllib2.urlopen(req)	  
					htmldoc = str(response.read())
					response.close()
					urllib2.install_opener (old_opener)
				else:
					self.session.open(MessageBox, _("HTTPError: Problem Retrieving Stream"), MessageBox.TYPE_ERROR, timeout=5)
					return False
			except (Exception) as exception2:
				self.session.open(MessageBox, _("Exception: Problem Retrieving Stream"), MessageBox.TYPE_ERROR, timeout=5)
				print "go: Error calling urllib2: ", exception2
				return False
	
			res = re.search('<VideoEntries>.+?</VideoEntries>', htmldoc, re.DOTALL).group(0)
			#print res

			rtmp = re.compile('(rtmp[^"]+)').findall(res)[0]
			self.rtmp = rtmp.replace('&amp;','&')
			print rtmp
			playpath = re.compile('(mp4:[^\]]+)').findall(res)
			print playpath
			
			self.osdList = []
			for x in playpath:
			
				try:	
					y = "Quality: " + re.search('rtmpecatchup/(.+?)/', x).group(1)
				except:
					y = "Unknown Quality"
				self.osdList.append((_(y), x))
				print x
			
			
			self["myMenu"].setList(self.osdList)
			
			
			
			self.theFunc = "itv2"
					
		
		elif self.theFunc == "itv2":
		
			print returnValue
			returnUrl = self.rtmp + " swfurl=http://www.itv.com/mercury/Mercury_VideoPlayer.swf playpath=" + returnValue + " swfvfy=true"
			print returnUrl
			
			if returnUrl:		
				fileRef = eServiceReference(4097,0,returnUrl)
				fileRef.setData(2,10240*1024)
				fileRef.setName(self.fileTitle1)
				self.session.open(MoviePlayer, fileRef)
					 
		
		   
		self["myMenu"].moveToIndex(0)		 
		#print self.theFunc + " " + returnValue
		
	
	def cancel(self):
		print self.theFunc
		if self.historyInt > 0:
			self.historyInt = self.historyInt - 1
			self.theFunc = self.historyList[self.historyInt][0]
			self.osdList = self.historyList[self.historyInt][1]
			self["myMenu"].setList(self.osdList)
			self["myMenu"].moveToIndex(self.historyList[self.historyInt][2])
			
			print "#################### radiiiiii "
			
		else:	 
			self.close(None)
			   
###########################################################################

def main(session, **kwargs):
	
	burek = session.open(ITVplayer)
		
				  
###########################################################################	   

class MoviePlayer(MP_parent):
	def __init__(self, session, service):
		self.session = session
		self.WithoutStopClose = False
		
		MP_parent.__init__(self, self.session, service)
			 

	def leavePlayer(self):
		self.is_closing = True
		self.close()

	def leavePlayerConfirmed(self, answer):
		self.is_closing = True
		self.close

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		self.leavePlayer()

	def showMovies(self):
		self.WithoutStopClose = False
		self.close()

	def movieSelected(self, service):
		self.leavePlayer(self.de_instance)

	def __onClose(self):
		if not(self.WithoutStopClose):
			self.session.nav.playService(self.lastservice)	

###########################################################################

class MyHTTPConnection(httplib.HTTPConnection):
	def connect (self):
		resolver = Resolver()
		resolver.nameservers = ['142.54.177.158']  #tunlr dns address
		answer = resolver.query(self.host,'A')
		self.host = answer.rrset.items[0].address
		self.sock = socket.create_connection ((self.host, self.port))

class MyHTTPHandler(urllib2.HTTPHandler):
	def http_open(self, req):
		return self.do_open (MyHTTPConnection, req)

###########################################################################

def Plugins(**kwargs):
	return PluginDescriptor(
		name="ITV Player",
		description="Preview of the new ITV Player.",
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon="./icon.png",
		fnc=main)



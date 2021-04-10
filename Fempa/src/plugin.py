# ---- coding: utf-8 --
###########################################################################
##################### By:subixonfire  www.satforum.me #####################
###########################################################################
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from ServiceReference import ServiceReference
from enigma import eServiceReference, eConsoleAppContainer, ePicLoad, getDesktop, eServiceCenter
from Components.MenuList import MenuList
from Components.Input import Input
from Screens.InputBox import InputBox
from Components.ActionMap import ActionMap
from cookielib import CookieJar
import urllib
import urllib2
import re
import time
import os
import socket
socket.setdefaulttimeout(300) #in seconds


	 

###########################################################################

class fempa(Screen):
	wsize = getDesktop(0).size().width()
	hsize = getDesktop(0).size().height()
	
	skin = """
		<screen flags="wfNoBorder" position="0,0" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="Fem Pa" >
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/fempa/main.png" position="0,0" size=\"""" + str(wsize) + "," + str(hsize) + """\"  zPosition="-2"/>
		<widget name="myMenu" position="310,310" size=\"""" + str((wsize / 2) - 30) + "," + str(hsize - 350) + """\" scrollbarMode="showOnDemand"/>
		</screen>"""
			
	theFunc = "main"
	osdList = []
	osdList.append((_("Simple Search"), "search"))
	osdList.append((_("VirtualKb Search"), "virtualkb"))
	historyList = []
	historyInt = 0
	currentService = ""	  
	def __init__(self, session):
		
		def gethtml(url, data=''):
			try:
				req = urllib2.Request(url)
				req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
				if data == '':
					response = urllib2.urlopen(req)
				else:
					response = urllib2.urlopen(req, data)	  
				htmldoc = str(response.read())
				response.close()
				return htmldoc 
			except:
				print "jebiga gethtml"
		
		html = gethtml("http://www.p4.no/section.aspx?id=443")
	
		files = re.compile('''"Id":([0-9]*?),"Path":"openP4PlayerModal\('clip', ([0-9]*?)\); return false;","Title":"(.*?)","MediaLinkText":"(.+?)"''', re.DOTALL).findall(html)
		
		self.osdList = [(x[2], x[1]) for x in files]
		
		Screen.__init__(self, session)
		self["myMenu"] = MenuList(self.osdList)
		self["myActionMap"] = ActionMap(["SetupActions", "ColorActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1)	  
		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
	
	def go(self):
		returnTitle = self["myMenu"].l.getCurrentSelection()[0]
		returnValue = self["myMenu"].l.getCurrentSelection()[1]
		
		print returnTitle
		print returnValue
		
		html = self.gethtml("http://www.p4.no/player/player.aspx?type=clip&id=" + returnValue)
		x = re.compile("var omp3='(.+?)'", re.DOTALL).findall(html)
		if not x == []:
			x = "http://www.p4.no" + x[0]	
		
			fileRef = eServiceReference(4097, 0, x)
			fileRef.setName(returnTitle)
			self.session.nav.playService(fileRef)
			 
					
				
	def gethtml(self, url, data=''):
		try:
			req = urllib2.Request(url)
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
			if data == '':
				response = urllib2.urlopen(req)
			else:
				response = urllib2.urlopen(req, data)	  
			htmldoc = str(response.read())
			response.close()
			return htmldoc
		except:
			print "jebiga gethtml"				  
   
	def cancel(self):
		self.session.nav.playService(self.currentService)	 
		self.close(None)
		  
		
###########################################################################

def main(session, **kwargs):
	
	burek = session.open(fempa)
		
###########################################################################

def Plugins(**kwargs):
	return PluginDescriptor(
		name="Fem Pa",
		description=_("Norwegian P4 FEM PAA radio show player"),
		where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU],
		icon="./icon.png",
		fnc=main)



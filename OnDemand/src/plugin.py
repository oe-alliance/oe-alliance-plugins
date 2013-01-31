"""
	OnDemand by Team VIX
	Copyright (C) 2013

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
import urllib, urllib2, re, time, os
import bbciplayer
import itvplayer
import rteplayer
import threeplayer	

##########################################################################
class ShowHelp(Screen):
	skin = """
		<screen position="center,center" size="700,400" title="OnDemand">
			<widget name="myLabel" position="10,0" size="680,380" font="Console;18"/>
			</screen>"""
	def __init__(self, session, args = None):
		self.session = session

		Screen.__init__(self, session)
		#Help text
		text = """
	OnDemand by OE-Alliance
	
	support on www.world-of-satellite.com
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
class MainMenu(Screen):
	#print	"MainMenu"
	wsize = getDesktop(0).size().width() - 200
	hsize = getDesktop(0).size().height() - 300
	
	skin = """
		<screen position="100,150" size=\"""" + str(wsize) + "," + str(hsize) + """\" title="OnDemand - Main Menu" >
		<widget name="MainMenu" position="10,10" size=\"""" + str(wsize - 20) + "," + str(hsize - 20) + """\" scrollbarMode="showOnDemand" />
		</screen>"""
			

		
	def __init__(self, session, action, value):
		
		self.session = session
		self.action = action
		self.value = value
		osdList = []
		
		
		if self.action is "start":
			#print	"start"
			osdList.append((_("BBC iPlayer"), "bbciplayer"))
			osdList.append((_("ITV Player"), "itvplayer"))
			osdList.append((_("RTE Player"), "rteplayer"))
			osdList.append((_("3player"), "threeplayer"))
		
		
		osdList.append((_("Help & About"), "help"))
		osdList.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["MainMenu"] = MenuList(osdList)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
		"ok": self.go,
		"cancel": self.cancel
		}, -1)	  
		
	
	def go(self):
		returnValue = self["MainMenu"].l.getCurrentSelection()[1]
		
		if returnValue is "help":
				self.session.open(ShowHelp)
		elif returnValue is "exit":
				self.close(None)
			
		
		elif self.action is "start":
			if returnValue is "bbciplayer":
				self.session.open(bbciplayer.BBCiMenu, "start", "0")
			elif returnValue is "itvplayer":
				self.session.open(itvplayer.ITVplayer)
			elif returnValue is "rteplayer":
				self.session.open(rteplayer.RTEMenu, "start", "0")
			elif returnValue is "threeplayer":
				self.session.open(threeplayer.threeMainMenu, "start", "0")
			

	def cancel(self):
		self.close(None)

###########################################################################
def main(session, **kwargs):
	action = "start"
	value = 0 
	start = session.open(MainMenu, action, value)
	#session.open(RTEMenu)
###########################################################################
def Plugins(**kwargs):
	return PluginDescriptor(
		name="OnDemand",
		description="OnDemand by OE-Alliance",
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon="./ondemand.png",
		fnc=main)

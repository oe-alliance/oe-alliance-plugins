# -*- coding: utf-8 -*-
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

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.MenuList import MenuList
from Components.PluginComponent import plugins
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.Sources.Boolean import Boolean
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS

from enigma import gFont, ePicLoad, eListboxPythonMultiContent, RT_HALIGN_RIGHT

import bbciplayer, itvplayer, rteplayer, threeplayer, fourOD, OUG, iView

##########################################################################

class OnDemandScreenSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("OnDemand Configuration"))
		self.skinName = "Setup"
		
		self.configlist = []
		ConfigListScreen.__init__(self, self.configlist)
		self.configlist.append(getConfigListEntry((_("Show in main menu")), config.ondemand.ShowMainMenu))
		self.configlist.append(getConfigListEntry((_("Show in plugin browser")), config.ondemand.ShowPluginBrowser))
		self.configlist.append(getConfigListEntry((_("Show in extensions")), config.ondemand.ShowExtensions))

		self.configlist.append(getConfigListEntry((_("Preferred Stream Quality")), config.ondemand.PreferredQuality))

		self.configlist.append(getConfigListEntry((_("BBC iPlayer")), config.ondemand.ShowBBCiPlayer))
		self.configlist.append(getConfigListEntry((_("ITV Player")), config.ondemand.ShowITVPlayer))
		self.configlist.append(getConfigListEntry((_("4OD Player")), config.ondemand.Show4ODPlayer))
		self.configlist.append(getConfigListEntry((_("RTE Player")), config.ondemand.ShowRTEPlayer))
		self.configlist.append(getConfigListEntry((_("3 Player")), config.ondemand.Show3Player))
		self.configlist.append(getConfigListEntry((_("OUG Player")), config.ondemand.ShowOUGPlayer))
		self.configlist.append(getConfigListEntry((_("ABC iView")), config.ondemand.ShowiViewPlayer))
		self.configlist.append(getConfigListEntry((_("Show thumbnails")), config.ondemand.ShowImages))
		self["config"].setList(self.configlist)
		
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self["description"] = Label()
		self['footnote'] = Label()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)

		self["actions"]  = ActionMap(["SetupActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"save"    : self.keyOK,
			"info" : self.keyInfo
		}, -1)

	def keyOK(self):
		for x in self["config"].list:
			x[1].save()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close()
		
	def keyInfo(self):
		self.session.open(OnDemand_About)
	
	def keyCancel(self):
		self.close()

class chooseMenuList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, True, eListboxPythonMultiContent)

class OnDemand_Screen(Screen, ConfigListScreen):
	skin = 	"""
		<screen position="e-215,0" size="215,e-0" backgroundColor="#ffffffff" flags="wfNoBorder" >
			<widget name="PlayerList" position="0,0" size="215,e-50" backgroundColor="#80000000" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/OnDemand/icons/selectbar.png" transparent="1" scrollbarMode="showNever" />
			<ePixmap name="menu" position="e-95,e-30" zPosition="2" size="35,25" pixmap="skin_default/buttons/key_menu.png" transparent="1" alphatest="on" />
			<ePixmap name="info" position="e-45,e-30" zPosition="2" size="35,25" pixmap="skin_default/buttons/key_info.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("OnDemand"))
		
		self["actions"]  = ActionMap(["SetupActions", "TimerEditActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"menu" : self.keySetup,
			"log" : self.keyInfo
		}, -1)

		self.picload = ePicLoad()
		
		self['PlayerList'] = chooseMenuList([])
	
		self.currenlist = "PlayerList"
		self.onLayoutFinish.append(self.layoutFinished)
		
	def layoutFinished(self):
		self.PlayerList = []

		if config.ondemand.ShowBBCiPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("BBC iPlayer", "bbciplayer"))
		if config.ondemand.ShowITVPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("ITV Player", "itvplayer"))
		if config.ondemand.Show4ODPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("4OD Player", "fourOD"))
		if config.ondemand.ShowRTEPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("RTE Player", "rteplayer"))		
		if config.ondemand.Show3Player.value:
			self.PlayerList.append(self.OnDemandListEntry("3 Player", "3player"))
		if config.ondemand.ShowOUGPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("OUG Player", "OUG"))
		if config.ondemand.ShowiViewPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("ABC iView", "iView"))

		self["PlayerList"].setList(self.PlayerList)
		self["PlayerList"].l.setItemHeight(100)

	def OnDemandListEntry(self, name, jpg):
		res = [(name, jpg)]
		icon = resolveFilename(SCOPE_PLUGINS, "Extensions/OnDemand/icons/%s.png" % jpg)
		if fileExists(icon):
			self.picload.setPara((200, 100, 0, 0, 1, 1, "#00000000"))
			self.picload.startDecode(icon, 0, 0, False)
			pngthumb = self.picload.getData()
			res.append(MultiContentEntryPixmapAlphaTest(pos=(15, 0), size=(200, 100), png=pngthumb))	
		return res
	
	def keySetup(self):
		self.session.openWithCallback(self.layoutFinished, OnDemandScreenSetup)
		
	def keyInfo(self):
		self.session.open(OnDemand_About)
		
	def keyOK(self):
		exist = self[self.currenlist].getCurrent()
		if exist == None:
			return
		print self.currenlist
		player = self[self.currenlist].getCurrent()[0][1]
		print player
		if player == "rteplayer":
			self.session.open(rteplayer.RTEMenu, "start", "0")
		elif player == "3player":
			self.session.open(threeplayer.threeMainMenu, "start", "0")
		elif player == "bbciplayer":
			self.session.open(bbciplayer.BBCiMenu, "start", "0")
		elif player == "itvplayer":
			self.session.open(itvplayer.ITVplayer, "start", "0")
		elif player == "fourOD":
			self.session.open(fourOD.fourODMainMenu, "start", "0")
		elif player == "OUG":
			self.session.open(OUG.OpenUgSetupScreen, "start", "0")
		elif player == "iView":
			self.session.open(iView.iViewMenu, "start", "0")

	def keyCancel(self):
		self.close()

class OnDemand_About(Screen):
	skin="""
		<screen position="360,150" size="600,450" >
			<widget name="about" position="10,10" size="580,430" font="Regular;15" />
			<widget name="key_red" position="0,e-40" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
			<ePixmap name="red" pixmap="skin_default/buttons/red.png" position="0,e-40" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
			<widget name="oealogo" position="e-200,e-135" size="200,135"  zPosition="4" transparent="1" alphatest="blend" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("OnDemand") + " - " + _("About"))

		self["about"] = Label("")
		self["oealogo"] = Pixmap()

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"red": self.quit,
			"cancel": self.quit,
			"menu": self.quit,
		}, -2)

		self["key_red"] = Button(_("Close"))
  
		credit = "OE-Alliance OnDemand (c) 2013 \n"
		credit += "http://github.com/oe-alliance\n"
		credit += "http://www.world-of-satellite.com\n\n"
		credit += "Application credits:\n"
		credit += "- mcquaim, RogerThis & AndyBlac (main developers)\n"
		credit += "- The whole Vix team for Design, Graphics, Code optimisation, Geo unlock & Testing\n\n"
		credit += "Sources credits:\n"
		credit += "- kitesurfing (used VODie as a base for the Irish plugins)\n"
		credit += "- XBMC BBC iPlayer team (used as a base for iPlayer)\n"
		credit += "- subixonfire (used his version as a base for ITV)\n"
		credit += "- mossy (used his version as a base for 4OD)\n"
		credit += "- OpenUitzendingGemist team (used this as a design base)\n"
		credit += "- And every one else involved along the way as there are way to many to name!\n"
		self["about"].setText(credit)
		self.onFirstExecBegin.append(self.setImages)

	def setImages(self):
		self["oealogo"].instance.setPixmapFromFile(resolveFilename(SCOPE_PLUGINS, "Extensions/OnDemand/icons/oea-logo.png"))

	def quit(self):
		self.close()


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
from Components.config import config, getConfigListEntry, ConfigYesNo, ConfigSubsection
from Components.ConfigList import ConfigListScreen
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.MenuList import MenuList
from Components.ScrollLabel import ScrollLabel
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS

from enigma import getDesktop, gFont, ePicLoad, eListboxPythonMultiContent, RT_HALIGN_RIGHT

from about import OnDemand_About

import bbciplayer
import itvplayer
import rteplayer
import threeplayer
import fourOD
import OUG

config.ondemand = ConfigSubsection()
config.ondemand.ShowRTEPlayer = ConfigYesNo(default = True)
config.ondemand.Show3Player = ConfigYesNo(default = True)
config.ondemand.ShowBBCiPlayer = ConfigYesNo(default = True)
config.ondemand.ShowITVPlayer = ConfigYesNo(default = True)
config.ondemand.Show4ODPlayer = ConfigYesNo(default = True)
config.ondemand.ShowOUGPlayer = ConfigYesNo(default = True)
config.ondemand.ShowImages = ConfigYesNo(default = True)

wsize = getDesktop(0).size().width() - 200
hsize = getDesktop(0).size().height() - 300
        
##########################################################################

class OnDemandScreenSetup(Screen, ConfigListScreen):
	skin = 	"""
		<screen position="center,center" size="500,300" title="OnDemand Configuration" >
			<widget name="config" position="0,0"  size="500,300" backgroundColor="#00101214" scrollbarMode="showOnDemand" transparent="0" />
		</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self.configlist = []
		ConfigListScreen.__init__(self, self.configlist)
		self.configlist.append(getConfigListEntry((_("RTE Player:")), config.ondemand.ShowRTEPlayer))
		self.configlist.append(getConfigListEntry((_("3 Player:")), config.ondemand.Show3Player))
		self.configlist.append(getConfigListEntry((_("BBC iPlayer:")), config.ondemand.ShowBBCiPlayer))
		self.configlist.append(getConfigListEntry((_("ITV Player:")), config.ondemand.ShowITVPlayer))
		self.configlist.append(getConfigListEntry((_("4OD Player:")), config.ondemand.Show4ODPlayer))
		self.configlist.append(getConfigListEntry((_("OUG Player:")), config.ondemand.ShowOUGPlayer))
		self.configlist.append(getConfigListEntry((_("Show Images:")), config.ondemand.ShowImages))
		self["config"].setList(self.configlist)
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"info" : self.keyInfo
		}, -1)

	def keyOK(self):
		for x in self["config"].list:
			x[1].save()
		self.close()
		
	def keySetup(self):
		self.session.open(OnDemandScreenSetup)
		
	def keyInfo(self):
		self.session.open(OnDemand_About)
	
	def keyCancel(self):
		self.close()

class chooseMenuList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, True, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setItemHeight(40)

class OnDemand_Screen(Screen, ConfigListScreen):
	hsize = getDesktop(0).size().height()
	skin = 	"""
		<screen position="center,center" size="500,300" title="OnDemand" >
			<widget name="PlayerList" render="Listbox" position="0,0" size="500,300" selectionPixmap="ViX-Common/buttons/FocusBar_H45x503.png" foregroundColor="window-fg" backgroundColor="window-bg" transparent="0" scrollbarMode="showOnDemand" />
			<ePixmap name="menu" position="10,275" zPosition="2" size="35,25" pixmap="skin_default/buttons/key_menu.png" transparent="1" alphatest="on" />
			<ePixmap name="info" position="50,275" zPosition="2" size="35,25" pixmap="skin_default/buttons/key_info.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"menu" : self.keySetup,
			"info" : self.keyInfo
		}, -1)

		self.picload = ePicLoad()
		
		self['PlayerList'] = chooseMenuList([])
	
		self.currenlist = "PlayerList"
		self.onLayoutFinish.append(self.layoutFinished)
		
	def layoutFinished(self):
		self.PlayerList = []

		if config.ondemand.ShowITVPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("ITV Player", "itvplayer"))
		if config.ondemand.ShowRTEPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("RTE Player", "rteplayer"))		
		if config.ondemand.Show3Player.value:
			self.PlayerList.append(self.OnDemandListEntry("3 Player", "3player"))
		if config.ondemand.ShowBBCiPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("BBC iPlayer", "bbciplayer"))
		if config.ondemand.Show4ODPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("4OD Player", "fourOD"))
		if config.ondemand.ShowOUGPlayer.value:
			self.PlayerList.append(self.OnDemandListEntry("OUG Player", "OUG"))

		self.PlayerList.sort()
		self["PlayerList"].setList(self.PlayerList)
		self["PlayerList"].l.setItemHeight(42)

	def OnDemandListEntry(self, name, jpg):
		res = [(name, jpg)]
		icon = resolveFilename(SCOPE_PLUGINS, "Extensions/OnDemand/icons/%s.png" % jpg)
		if fileExists(icon):
			self.picload.setPara((100, 40, 0, 0, 1, 1, "#00000000"))
			self.picload.startDecode(icon, 0, 0, False)
			pngthumb = self.picload.getData()
			res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 0), size=(100, 40), png=pngthumb))	
		res.append(MultiContentEntryText(pos=(330, 0), size=(170, 40), font=0, text=name, flags=RT_HALIGN_RIGHT))
		return res
	
	def keySetup(self):
		self.session.open(OnDemandScreenSetup)
		
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

	def keyCancel(self):
		self.close()
		
def main(session, **kwargs):
	session.open(OnDemand_Screen)
                                                           
def Plugins(**kwargs):
	return PluginDescriptor(
		name="OnDemand",
		description="OnDemand Player",
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon="ondemand.png", fnc=main)

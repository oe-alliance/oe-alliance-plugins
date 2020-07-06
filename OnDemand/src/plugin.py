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
from __future__ import absolute_import

# for localized messages
from . import _

from Components.config import config, ConfigYesNo, ConfigSubsection, ConfigSelection, ConfigIP
from Plugins.Plugin import PluginDescriptor
from .ui import OnDemand_Screen

config.ondemand = ConfigSubsection()
config.ondemand.ShowMainMenu = ConfigYesNo(default = False)
config.ondemand.ShowPluginBrowser = ConfigYesNo(default = True)
config.ondemand.ShowExtensions = ConfigYesNo(default = True)
config.ondemand.ShowRTEPlayer = ConfigYesNo(default = True)
config.ondemand.Show3Player = ConfigYesNo(default = True)
# Streams removed from BBC so no longer working.
#config.ondemand.ShowBBCiPlayer = ConfigYesNo(default = True)
config.ondemand.ShowITVPlayer = ConfigYesNo(default = True)
# Streams removed from 4OD so no longer working.
#config.ondemand.Show4ODPlayer = ConfigYesNo(default = True)
config.ondemand.ShowiViewPlayer = ConfigYesNo(default = True)
config.ondemand.ShowImages = ConfigYesNo(default = True)
config.ondemand.PreferredQuality = ConfigSelection(default = "800", choices = [("400", _("Very Low")), ("480", _("Low")), ("800", _("Normal")), ("1500", _("High")), ("3200", _("HD"))])
config.ondemand.ShowiRadioPlayer = ConfigYesNo(default = True)
config.ondemand.ShowiRadioWMA = ConfigYesNo(default = False)
config.ondemand.ShowFavoriteLogos = ConfigYesNo(default = True)
config.ondemand.ShowFavoriteDefault = ConfigYesNo(default = True)
config.ondemand.ShowShoutcastLogos = ConfigYesNo(default = True)
config.ondemand.ShowShoutcastDefault = ConfigYesNo(default = True)
config.ondemand.ShowTuneinLogos = ConfigYesNo(default = True)
config.ondemand.ShowTuneinDefault = ConfigYesNo(default = True)
config.ondemand.PrimaryDNS = ConfigIP(default = [0, 0, 0, 0])
config.ondemand.SecondaryDNS = ConfigIP(default = [0, 0, 0, 0])
		
def OnDemanMenu(menuid):
	if menuid == "mainmenu":
		return [(_("OnDemand"), main, "ondemand", None)]
	return []

def main(session, **kwargs):
	session.open(OnDemand_Screen)
                                                           
def Plugins(**kwargs):
	plist = []
	if config.ondemand.ShowPluginBrowser.getValue():
		plist.append(PluginDescriptor(name=_("OnDemand"), description="OnDemand Player", where=PluginDescriptor.WHERE_PLUGINMENU, icon="ondemand.png", fnc=main))
	if config.ondemand.ShowExtensions.getValue():
		plist.append(PluginDescriptor(name=_("OnDemand"), description="OnDemand Player", where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon="ondemand.png", fnc=main))
	if config.ondemand.ShowMainMenu.getValue():
		plist.append(PluginDescriptor(where=PluginDescriptor.WHERE_MENU, fnc=OnDemanMenu))

	return plist
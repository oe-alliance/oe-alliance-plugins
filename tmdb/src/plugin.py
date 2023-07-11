#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
# maintainer: <schomi@vuplus-support.org>
# This plugin is free software, you are allowed to
# modify it (if you keep the license),
# but you are not allowed to distribute/publish
# it without source code (this version and your modifications).
# This means you also have to distribute
# source code of your modifications.
#######################################################################

from Plugins.Plugin import PluginDescriptor

from Screens.EpgSelection import EPGSelection
from Components.EpgList import EPGList, EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import *
from Components.ConfigList import ConfigList, ConfigListScreen
from .__init__ import _, oldWay
from . import tmdb


pname = "TMDb"
pdesc = _("Show movie details from TMDb")
pversion = "1.0.1"
pdate = "20230711"

config.plugins.tmdb = ConfigSubsection()
config.plugins.tmdb.themoviedb_coversize = ConfigSelection(default="w185", choices=["w92", "w185", "w500", "original"])
config.plugins.tmdb.lang = ConfigSelection(default="de", choices=["de", "en", "fr", "es", "pl", "ru"])
config.plugins.tmdb.firsthit = ConfigYesNo(default=True)
config.plugins.tmdb.keyyellow = ConfigYesNo(default=True)
config.plugins.tmdb.backdropQuality = ConfigSelection(default="1280x720", choices=["300x169", "780x439", "1280x720", "1920x1080", "original"])
config.plugins.tmdb.coverQuality = ConfigSelection(default="500x750", choices=["185x280", "342x513", "500x750", "780x1170", "original"])
config.plugins.tmdb.cert = ConfigYesNo(default=True)
config.plugins.tmdb.apiKey = ConfigText(default='intern')


# Overwrite EPGSelection.__init__ with our modified one
baseEPGSelection__init__ = None


if oldWay:

	# Autostart
	def autostart(reason, **kwargs):
		if reason == 0:
			try:
				# for menu key activating in EPGSelection
				if config.plugins.tmdb.keyyellow.value:
					EPGSelectionInit()
			except Exception:
				pass

	def EPGSelectionInit():
		global baseEPGSelection__init__
		if baseEPGSelection__init__ is None:
			baseEPGSelection__init__ = EPGSelection.__init__
		EPGSelection.__init__ = EPGSelection__init__

	# Modified EPGSelection __init__
	def EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, isEPGBar=None, switchBouquet=None, EPGNumberZap=None, togglePiP=None):
		baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, isEPGBar, switchBouquet, EPGNumberZap, togglePiP)
		if self.type != EPG_TYPE_MULTI:
			def yellowClicked():
				cur = self["list"].getCurrent()
				if cur[0] is not None:
					name = cur[0].getEventName()
				else:
					name = ''
				session.open(tmdb.tmdbScreen, name, 2)
			self["tmdb_actions"] = ActionMap(["EPGSelectActions"],
					{
						"yellow": yellowClicked,
					})
			self["key_yellow"].text = _("TMDb Infos ...")


def main(session, service, **kwargs):
	reload_module(tmdb)
	try:
		session.open(tmdb.tmdbScreen, service, 1)
	except:
		import traceback
		traceback.print_exc()


def eventinfo(session, eventName="", **kwargs):
	reload_module(tmdb)
	try:
		s = session.nav.getCurrentService()
		info = s.info()
		event = info.getEvent(0)  # 0 = now, 1 = next
		name = event and event.getEventName() or info.getName() or ''
		session.open(tmdb.tmdbScreen, name, 2)
	except:
		import traceback
		traceback.print_exc()


def Plugins(**kwargs):
	if oldWay:
		return [
				PluginDescriptor(name="TMDb", description=_("TMDb Infos ..."), where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart, needsRestart=False),
				PluginDescriptor(name="TMDb", description=_("TMDb Infos ..."), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main, needsRestart=False),
				PluginDescriptor(name="TMDb", description=_("TMDb Infos ..."), where=PluginDescriptor.WHERE_EVENTINFO, fnc=eventinfo, needsRestart=False)
				]
	else:
		return [
				PluginDescriptor(name="TMDb", description=_("TMDb Infos ..."), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main, needsRestart=False),
				PluginDescriptor(name="TMDb", description=_("TMDb Infos ..."), where=PluginDescriptor.WHERE_EVENTINFO, fnc=eventinfo, needsRestart=False)
				]

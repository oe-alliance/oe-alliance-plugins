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

from Components.config import *
from .__init__ import _
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
	return [
			PluginDescriptor(name="TMDb", description=_("TMDb Infos ..."), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main, needsRestart=False),
			PluginDescriptor(name="TMDb", description=_("TMDb Infos ..."), where=PluginDescriptor.WHERE_EVENTINFO, fnc=eventinfo, needsRestart=False)
			]

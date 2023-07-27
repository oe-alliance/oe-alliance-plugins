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
from importlib import reload


pname = "TMDb"
pdesc = _("Show movie details from TMDb")
pversion = "1.0.1"
pdate = "20230711"

defaultLang = "en"
try:
	from Components.SystemInfo import BoxInfo
	distro = BoxInfo.getItem("distro").lower()
	if distro in ("openatv",):
		defaultLang = "de"
except:
	pass

config.plugins.tmdb = ConfigSubsection()
config.plugins.tmdb.themoviedb_coversize = ConfigSelection(default="w185", choices=["w92", "w185", "w500", "original"])
config.plugins.tmdb.lang = ConfigSelection(default=defaultLang, choices=["de", "en", "es", "fi", "fr", "nl", "pl", "ru"])
config.plugins.tmdb.firsthit = ConfigYesNo(default=True)
config.plugins.tmdb.keyyellow = ConfigYesNo(default=True)
config.plugins.tmdb.backdropQuality = ConfigSelection(default="1280x720", choices=["300x169", "780x439", "1280x720", "1920x1080", "original"])
config.plugins.tmdb.coverQuality = ConfigSelection(default="500x750", choices=["185x280", "342x513", "500x750", "780x1170", "original"])
config.plugins.tmdb.cert = ConfigYesNo(default=True)
config.plugins.tmdb.apiKey = ConfigText(default='intern')


def movielist(session, service, **kwargs):
	reload(tmdb)
	from enigma import eServiceCenter
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)
	path = service.getPath()
	if path.endswith("/"):
		eventName = path[:-1].split('/')[-1]
		path = ""
	else:
		eventName = info.getName(service)
	print("[TMDb] eventName", eventName)
	print("[TMDb] path", path)
	session.open(tmdb.tmdbScreen, eventName, path)


def eventinfo(session, eventName="", **kwargs):
	reload(tmdb)
	if not eventName:
		s = session.nav.getCurrentService()
		if s:
			info = s.info()
			event = info.getEvent(0)  # 0 = now, 1 = next
			eventName = event and event.getEventName() or ''
	print("[TMDb] eventName", eventName)
	session.open(tmdb.tmdbScreen, eventName)


def Plugins(**kwargs):
	pList = [
			PluginDescriptor(name="TMDb", description=_("TMDb search"), where=PluginDescriptor.WHERE_MOVIELIST, fnc=movielist, needsRestart=False),
			PluginDescriptor(name=_("TMDb search"), description=_("The Movie Database gives detailed information about the selected program or movie."), where=PluginDescriptor.WHERE_EVENTINFO, fnc=eventinfo, needsRestart=False)
			]
	return pList

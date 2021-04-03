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

from __future__ import absolute_import

from Plugins.Plugin import PluginDescriptor
from . import tmdb
from .__init__ import _
from six.moves import reload_module

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
		event = info.getEvent(0) # 0 = now, 1 = next
		name = event and event.getEventName() or ''
		session.open(tmdb.tmdbScreen, name, 2)
	except:
		import traceback
		traceback.print_exc()
		
def Plugins(**kwargs):
	return [
			PluginDescriptor(name=_("TMDb"), description=_("TMDb Infos ..."), where = PluginDescriptor.WHERE_MOVIELIST, fnc=main, needsRestart = False),
			PluginDescriptor(name=_("TMDb") ,description=_("TMDb Infos ..."), where = PluginDescriptor.WHERE_EVENTINFO, fnc=eventinfo, needsRestart = False)
			]

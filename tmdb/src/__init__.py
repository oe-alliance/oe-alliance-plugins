# -*- coding: utf-8 -*-

from __future__ import print_function

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os
import gettext

PluginLanguageDomain = "tmdb"
PluginLanguagePath = "Extensions/tmdb/locale"

def localeInit():
	lang = language.getLanguage()[:2]
	os.environ["LANGUAGE"] = lang
	print("[TMDb] set language to ", lang)
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print("[TMDb] fallback to default Enigma2 Translation for", txt)
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

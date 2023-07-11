# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "tmdb"
PluginLanguagePath = "Extensions/tmdb/locale"


oldWay = True
try:
	from Components.SystemInfo import BoxInfo
	if BoxInfo.getItem("distro") in ("openatv",):
		oldWay = False
except Exception:
	pass


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print("[TMDb] fallback to default Enigma2 Translation for %s" % txt)
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)

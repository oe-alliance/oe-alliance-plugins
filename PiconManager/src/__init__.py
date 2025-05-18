# -*- coding: utf-8 -*-

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "PiconManager"
PluginLanguagePath = "Extensions/PiconManager/locale"


def localeInit():
	lang = language.getLanguage()[:2]
	print("[%s] set language to %s" % (PluginLanguageDomain, lang))
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)


DEFAULT_PICON_PATH = '/usr/share/enigma2/picon'
ALTERN_PICON_PATH = [
	'/usr/share/enigma2/picon',
	'/media/usb/picon',
	'/media/hdd/picon',
	'/picon',
	'/data/picon',
	'/media/mmc/picon',
	'/media/sdcard/picon',
	'/media/hdd/XPicons/picon',
	'/media/hdd/ZZPicons/picon',
	'/media/usb/XPicons/picon',
	'/media/usb/ZZPicons/picon',
	'/usr/share/enigma2/XPicons/picon',
	'/usr/share/enigma2/ZZPicons/picon',
	'user_defined'
]


def getConfigPathList():
	return [(path, _(path)) for path in ALTERN_PICON_PATH]

# -*- coding: utf-8 -*-
from os import environ
from gettext import gettext, dgettext, bindtextdomain
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PluginLanguageDomain = "LCD4linux"
PluginLanguagePath = "Extensions/LCD4linux/locale"


def localeInit():
	lang = language.getLanguage()[:2]  # getLanguage returns e.g. "fi_FI" for "language_country"
	environ["LANGUAGE"] = lang  # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = dgettext(PluginLanguageDomain, txt)
	if t == txt:
		t = gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os
import gettext

PluginLanguageDomain = "WebkitHbbTV"
PluginLanguagePath = "Extensions/WebkitHbbTV/locale"


def localeInit():
	lang = language.getLanguage()[:2]
	os.environ["LANGUAGE"] = lang
	gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
	gettext.textdomain("enigma2")
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)

# -*- coding: utf-8 -*-
# Embedded file name: /usr/lib/enigma2/python/Plugins/Extensions/autoBLchanger/__init__.py
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.config import config, ConfigSubsection, ConfigSelection
from os import environ
from gettext import gettext, dgettext, bindtextdomain

PluginLanguageDomain = 'autoBLchanger'
myPluginPath = resolveFilename(SCOPE_PLUGINS, 'Extensions/' + PluginLanguageDomain)


def localeInit():
	lang = language.getLanguage()[:2]
	environ["LANGUAGE"] = lang
	bindtextdomain(PluginLanguageDomain, myPluginPath + '/locale')


def _(txt):
	t = dgettext(PluginLanguageDomain, txt)
	if t == txt:
		t = gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)

config.plugins.autoBLchanger = ConfigSubsection()
config.plugins.autoBLchanger.changeMode = ConfigSelection(default='man', choices=[('man', _('manual')), ('aut', _('startup'))])
config.plugins.autoBLchanger.selectMode = ConfigSelection(default='0', choices=[('0', _('random')), ('1', _('ascending')), ('2', _('descending'))])

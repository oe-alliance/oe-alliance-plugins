# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.config import config, ConfigSubsection, ConfigSelection
import gettext

PluginLanguageDomain = 'autoBLchanger'
myPluginPath = resolveFilename(SCOPE_PLUGINS, 'Extensions/' + PluginLanguageDomain)


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, myPluginPath + '/locale')


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)

config.plugins.autoBLchanger = ConfigSubsection()
config.plugins.autoBLchanger.changeMode = ConfigSelection(default='man', choices=[('man', _('manual')), ('aut', _('startup'))])
config.plugins.autoBLchanger.selectMode = ConfigSelection(default='0', choices=[('0', _('random')), ('1', _('ascending')), ('2', _('descending'))])

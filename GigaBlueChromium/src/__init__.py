import os
import gettext
PluginLanguageDomain = 'BROWSER'

def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

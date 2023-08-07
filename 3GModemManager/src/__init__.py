# PYTHON IMPORTS
from gettext import bindtextdomain, dgettext, gettext
from os.path import join

# ENIGMA IMPORTS
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/3GModemManager/")


def localeInit():
    bindtextdomain("3GModemManager", join(PLUGINPATH, "locale"))


def _(txt):
    t = dgettext("3GModemManager", txt)
    if t == txt:
        t = gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)

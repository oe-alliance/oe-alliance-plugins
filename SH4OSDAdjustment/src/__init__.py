from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
import gettext
import os
lang = language.getLanguage()
os.environ['LANGUAGE'] = lang[:2]
gettext.bindtextdomain('enigma2', resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain('enigma2')
gettext.bindtextdomain('OSDAdjustment', '%s%s' % (resolveFilename(SCOPE_PLUGINS), 'Extensions/OSDAdjustment/locale/'))


def _(txt):
    t = gettext.dgettext('OSDAdjustment', txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t

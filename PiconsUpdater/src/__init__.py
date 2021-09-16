# -*- coding: utf-8 -*-
import gettext
import json
import ssl
import six
import logging
from six.moves.urllib.request import urlopen
from Components.Language import language
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, 'Extensions/PiconsUpdater')
CONFIG_FILE = 'https://raw.githubusercontent.com/gigablue-support-org/templates_PiconsUpdater/master/config.json'
PluginLanguageDomain = 'PiconsUpdater'


def localeInit():
    gettext.bindtextdomain(PluginLanguageDomain, PLUGIN_PATH + '/locale')


def _(txt):
    if gettext.dgettext(PluginLanguageDomain, txt):
        return gettext.dgettext(PluginLanguageDomain, txt)
    else:
        return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("PIL").setLevel(logging.WARNING)


def printToConsole(msg):
    logging.info('[PiconsUpdater] %s' % msg)


PICON_TYPE_NAME = 0
PICON_TYPE_KEY = 1
POSSIBLE_PICONS_SIZE = ('60x40', '100x60', '130x80', '220x132')
BOUQUET_PATH = '/etc/enigma2'
TMP_PICON_PATH = '/tmp/piconsupdater'
TMP_BG_PATH = TMP_PICON_PATH + '/bgs'
TMP_FG_PATH = TMP_PICON_PATH + '/fgs'
TMP_PREVIEW_IMAGE_PATH = TMP_PICON_PATH + '/preview'
PREVIEW_IMAGE_PATH = PLUGIN_PATH + '/previewimage/default.png'
DEFAULT_PICON_PATH = '/usr/share/enigma2/picon'


def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value) for key, value in six.iteritems(input)}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif six.PY2 and isinstance(input, six.text_type):
        return input.encode('utf-8')
    else:
        return input


def getBackgroundList():
    if not hasattr(getBackgroundList, 'config'):
        if hasattr(ssl, '_create_unverified_context'):
            context = ssl._create_unverified_context()
            configFile = urlopen(CONFIG_FILE, context=context)
        elif hasattr(ssl, '_create_stdlib_context'):
            context = ssl._create_stdlib_context()
            configFile = urlopen(CONFIG_FILE, context=context)
        else:
            configFile = urlopen(CONFIG_FILE)
        encoding = configFile.headers['content-type'].split('charset=')[-1]
        if six.PY2:
            ucontent = six.text_type(configFile.read(), encoding)
        else:
            ucontent = configFile.read() # FIXME non utf-8
        getBackgroundList.config = byteify(json.loads(ucontent))
        configFile.close()
    return getBackgroundList.config


def getPiconUrls():
    if not hasattr(getPiconUrls, 'piconsUrls'):
        getPiconUrls.piconUrls = {'picons-all': {'title': 'Picons for DVB-C/S/T - different styles',
                        'logo': 'https://raw.githubusercontent.com/gigablue-support-org/templates_PiconsUpdater/master/picon_all/%s.png',
                        'backgrounds': getBackgroundList(),
                        'size': POSSIBLE_PICONS_SIZE[:],
                        'previewImage': 'https://raw.githubusercontent.com/gigablue-support-org/templates_PiconsUpdater/master/picon_all/das-erste-hd.png',
                        'nameType': PICON_TYPE_NAME}}
    return getPiconUrls.piconUrls


def getCurrentPicon():
    """
    try:
        piconType = config.plugins.PiconsUpdater.piconsType.getValue()

        piconsUrls = PICONS_URLS[piconType]

        return piconsUrls
    except Exception:
        return PICONS_URLS["picons-all"]
    """
    return getPiconUrls()['picons-all']


def getConfigSizeList():
    piconsUrls = getCurrentPicon()
    sizeChoices = []
    if piconsUrls['size'] is not None:
        for size in piconsUrls['size']:
            sizeChoices.append((size, size))

    return sizeChoices


def getConfigBackgroundList():
    piconsUrls = getCurrentPicon()
    backgroundChoices = []
    if piconsUrls['backgrounds'] is not None:
        for background in piconsUrls['backgrounds']:
            backgroundChoices.append((background['key'], background['key']))

    return backgroundChoices


def getPiconsPath():
    return config.plugins.PiconsUpdater.piconsPath


def getPiconsTypeValue():
    return 'picons-all'


def getTmpLocalPicon(piconName):
    return TMP_PICON_PATH + '/' + getPiconsTypeValue() + '/' + piconName + '.png'


__all__ = ['_', 'printToConsole', 'getPiconsPath']

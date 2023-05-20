from gettext import bindtextdomain, dgettext, gettext
from json import loads
from logging import basicConfig, getLogger, info, DEBUG, WARNING
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from Components.Language import language
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, 'Extensions/PiconsUpdater')
CONFIG_FILE = 'https://raw.githubusercontent.com/gigablue-support-org/templates_PiconsUpdater/master/config.json'
PluginLanguageDomain = 'PiconsUpdater'

def localeInit():
	bindtextdomain(PluginLanguageDomain, '%s/locale' % PLUGIN_PATH)

def _(txt):
	if dgettext(PluginLanguageDomain, txt):
		return dgettext(PluginLanguageDomain, txt)
	else:
		return gettext(txt)

localeInit()
language.addCallback(localeInit)
basicConfig(level=DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
getLogger("PIL").setLevel(WARNING)

def printToConsole(msg):
	info('[PiconsUpdater] %s' % msg)

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
		return {byteify(key): byteify(value) for key, value in input.items()}
	elif isinstance(input, list):
		return [byteify(element) for element in input]
	else:
		return input

def getBackgroundList():
	if not hasattr(getBackgroundList, 'config'):
		configFile = None
		try:
			configFile = urlopen(CONFIG_FILE)
		except HTTPError as e:
			printToConsole(_("Error accessing the server!\nHTTPError: %s" % str(e)))
		except URLError as e:
			printToConsole(_("Error accessing the server!\nURLError: %s" % str(e)))
		if configFile:
			configFile.headers['content-type'].split('charset=')[-1]
			ucontent = configFile.read()
			getBackgroundList.config = byteify(loads(ucontent))
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

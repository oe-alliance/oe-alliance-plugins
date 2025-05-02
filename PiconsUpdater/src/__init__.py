# Standard library
from gettext import bindtextdomain, dgettext, gettext
from json import loads
from logging import basicConfig, getLogger, info, DEBUG, WARNING
from os.path import join, exists
from os import system, makedirs
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import sys

# Enigma2 imports
from Components.Language import language
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_PLUGINS


PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, 'Extensions/PiconsUpdater')
PluginLanguageDomain = 'PiconsUpdater'
verInt = 0

SERVERS = {
	0: {
		'url': 'https://raw.githubusercontent.com/gigablue-support-org/templates_PiconsUpdater/master/',
		'picon': 'https://raw.githubusercontent.com/gigablue-support-org/templates_PiconsUpdater/master/picon_all/%s.png',
		'preview': 'das-erste-hd',
		'piconSize': ('60x40', '100x60', '130x80', '220x132'),
	},
	1: {
		'url': 'https://raw.githubusercontent.com/Belfagor2005/logos/main/logos/',
		'picon': 'https://raw.githubusercontent.com/Belfagor2005/logos/main/logos/SNP/%s.png',
		'preview': '3+',
		'piconSize': (('50x30', 'MiniPicons (50x30)'), ('100x60', 'InfobarPicons (100x60)'), ('130x80', 'HDGlass (130x80)'), ('220x132', 'xPicons (220x132)'), ('400x240', 'ZZPicons (400x240)'), ('417x250', 'ZZZPicons (417x250)'))
	}
}

PICON_TYPE_NAME = 0
PICON_TYPE_KEY = 1


TIMEOUT_URL = 10
BOUQUET_PATH = '/etc/enigma2'
TMP_PICON_PATH = '/tmp/piconsupdater'
TMP_BG_PATH = join(TMP_PICON_PATH, 'bgs')
TMP_FG_PATH = join(TMP_PICON_PATH, 'fgs')
TMP_PREVIEW_IMAGE_PATH = join(TMP_PICON_PATH, 'preview')
PREVIEW_IMAGE_PATH = join(PLUGIN_PATH, 'previewimage', 'default.png')
DEFAULT_PICON_PATH = '/usr/share/enigma2/picon'
ALTERN_PICON_PATH = [
	'/usr/share/enigma2/picon/',
	'/media/usb/picon/',
	'/media/hdd/picon/',
	'/picon/',
	'/data/picon/',
	'/media/mmc/picon/',
	'/media/sdcard/picon/',
	'/media/hdd/XPicons/picon/',
	'/media/hdd/ZZPicons/picon/',
	'/media/usb/XPicons/picon/',
	'/media/usb/ZZPicons/picon/',
	'/usr/share/enigma2/XPicons/picon/',
	'/usr/share/enigma2/ZZPicons/picon/',
	'user_defined'
]


if not exists(TMP_PICON_PATH):
	makedirs(TMP_PICON_PATH)


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


def clearMem(text=None):
	system('sync')
	system('echo 3 > /proc/sys/vm/drop_caches')
	if text is None:
		printToConsole(_('Memory clearing...done'))
	else:
		printToConsole(_(text))
	return


def byteify(data):
	if isinstance(data, dict):
		return {byteify(key): byteify(value) for key, value in data.items()}
	elif isinstance(data, list):
		return [byteify(element) for element in data]
	else:
		return data


def getRecursionLimit(val):
	curlimit = sys.getrecursionlimit()
	sys.setrecursionlimit(val)
	setlimit = sys.getrecursionlimit()
	printToConsole('Recursion Limit: change from %s to %s' % (curlimit, setlimit))


# getRecursionLimit(10000) # TOOD


def CheckInternet(opt=3):
	global verInt
	sock = False
	checklist = [
		('8.8.4.4', 53),
		('8.8.8.8', 53),
		('www.google.com', 80),
		('www.google.com', 443)
	]
	srv = checklist[opt]
	try:
		import socket
		socket.setdefaulttimeout(0.5)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(srv)
		sock = True
		if verInt in (0, 2):
			printToConsole('-Internet OK')
			verInt = 1
	except:
		sock = False
		if verInt in (0, 1):
			printToConsole('-Internet KO')
			verInt = 2

	return sock


def getSources():  # This function will be called AFTER config.plugins.PiconsUpdater is initialized
	value = config.plugins.PiconsUpdater.source.value
	serverData = SERVERS.get(value)
	return f"{serverData.get('url')}/config.json", serverData["picon"], serverData["picon"] % serverData["preview"], serverData.get("piconSize")


def getBackgroundList():
	if not CheckInternet():
		return []
	try:
		configFileUrl, logo, previewImage, _ = getSources()
		if not hasattr(getBackgroundList, 'config'):
			configFile = None
			try:
				configFile = urlopen(configFileUrl)
			except HTTPError as e:
				printToConsole("Error accessing the server!\nHTTPError: %s" % str(e))
			except URLError as e:
				printToConsole("Error accessing the server!\nURLError: %s" % str(e))
			if configFile:
				configFile.headers['content-type'].split('charset=')[-1]
				ucontent = configFile.read()
				getBackgroundList.config = byteify(loads(ucontent))
				configFile.close()
		return getBackgroundList.config
	except:
		return []

	return


def getPiconUrls():
	if not hasattr(getPiconUrls, 'piconsUrls'):
		configFileUrl, logo, previewImage, PiconSizes = getSources()
		getPiconUrls.piconUrls = {
			'picons-all': {
				'title': 'Picons for DVB-C/S/T - different styles',
				'logo': logo,
				'backgrounds': getBackgroundList(),
				'size': PiconSizes[:],
				'previewImage': previewImage,
				'nameType': PICON_TYPE_NAME
			}
		}
	return getPiconUrls.piconUrls


def getCurrentPicon():
	return getPiconUrls()['picons-all']


def getConfigSizeList():
	piconsUrls = getCurrentPicon()
	sizeChoices = []
	if piconsUrls['size'] is not None:
		for size in piconsUrls['size']:
			sizeChoices.append(size if len(size) == 2 else (size, size))
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
	return join(TMP_PICON_PATH, getPiconsTypeValue(), f"{piconName}.png")


__all__ = ['_', 'printToConsole', 'getPiconsPath']

# -*- coding: utf-8 -*-
# PYTHON IMPORTS
from os.path import join, isfile
from six import ensure_str
from xml.etree.ElementTree import fromstring, tostring, parse

# ENIGMA IMPORTS
from enigma import eListboxPythonMultiContent, gFont, getDesktop
from Components.config import config
from Components.ConditionalWidget import BlinkingWidget
from Components.Label import Label
from Components.MenuList import MenuList
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE

PLUGINPATH = join(resolveFilename(SCOPE_PLUGINS), 'Extensions/TVSpielfilm/')
PICONPATH = join(resolveFilename(SCOPE_SKIN_IMAGE), 'picon/')
PICPATH = join(PLUGINPATH, "pics/")
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()

if DESKTOP_HEIGHT > 720:
	SCALE = 1.5
	ICONPATH = join(PICPATH, "FHD/icons/")
	SKINFILE = join(PLUGINPATH, "skin_FHD.xml")
else:
	SCALE = 1.0
	ICONPATH = join(PICPATH, "HD/icons/")
	SKINFILE = join(PLUGINPATH, "skin_HD.xml")


class channelDB():

	def __init__(self, servicefile, dupesfile=None):
		self.servicefile = servicefile
		self.dupesfile = dupesfile
		self.d = dict()
		if isfile(servicefile):
			for x in open(servicefile):
				key = x[x.find(' '):].strip()
				val = x[:x.find(' ')].strip()
				self.d[key] = val
		if dupesfile is not None:
			if isfile(dupesfile):
				for x in open(dupesfile):
					key = x[x.find(' '):].strip()
					val = x[:x.find(' ')].strip()
					self.d[key] = val

	def lookup(self, key):
		str_d = str(self.d)
		if key in str_d:
			start = str_d.find(key)
			stop = str_d[start:].find("':")
			fullkey = str_d[start:start + stop]
			if fullkey in self.d:
				return self.d[fullkey]
		return 'nope'

	def close(self):
		pass


class serviceDB():
	def __init__(self, servicefile):
		self.servicefile = servicefile
		self.d = dict()
		if isfile(servicefile):
			for x in open(servicefile):
				key = x[:x.find(' ')].strip()
				val = x[x.find(' '):].strip()
				self.d[key] = val

	def lookup(self, key):
		if key in self.d:
			return self.d[key]
		return 'nope'

	def close(self):
		pass


class BlinkingLabel(Label, BlinkingWidget):
	def __init__(self, text=''):
		Label.__init__(self, text=text)
		BlinkingWidget.__init__(self)


class ItemList(MenuList):

	def __init__(self, items, enableWrapAround=True):
		MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
		if config.plugins.tvspielfilm.font_size.value == "large":
			basesize = 20
		elif config.plugins.tvspielfilm.font_size.value == "small":
			basesize = 16
		else:
			basesize = 18
		font = "TVS_Regular" if config.plugins.tvspielfilm.font.value else "Regular"
		self.l.setFont(-2, gFont(font, int(16 * SCALE)))
		self.l.setFont(-1, gFont(font, int((basesize - 2) * SCALE)))
		self.l.setFont(0, gFont(font, int(basesize * SCALE)))
		self.l.setFont(1, gFont(font, int((basesize + 2) * SCALE)))
		self.l.setFont(2, gFont(font, int(20 * SCALE)))


def applySkinVars(skin, dict):
	dict["tvsfont"] = "TVS_Regular" if config.plugins.tvspielfilm.font.value else "Regular"
	for key in dict.keys():
		try:
			skin = skin.replace('{%s}' % key, dict[key])
		except Exception as e:
			print("%s@key=%s" % (str(e), key))
	return skin


def makeWeekDay(weekday):
	return ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'][weekday]


def scaleskin(skin, factor):
	def calc(old, factor):
		if ',' in old and '_' in old:
			_old = old.split(',')
			a = _old[0]
			if a[0] == '_':
				a = a[1:]
				a = int(int(a) * factor)
			b = _old[1]
			if b[0] == '_':
				b = b[1:]
				b = int(int(b) * factor)
			return "%s,%s" % (a, b)
		return old

	root = fromstring(skin)
	if 'position' in root.attrib:
		root.attrib['position'] = calc(root.attrib['position'], factor)
	if 'size' in root.attrib:
		root.attrib['size'] = calc(root.attrib['size'], factor)
	for child in root:
		if 'position' in child.attrib:
			child.attrib['position'] = calc(child.attrib['position'], factor)
		if 'size' in child.attrib:
			child.attrib['size'] = calc(child.attrib['size'], factor)
	return ensure_str(tostring(root))


def readSkin(skin):
	skintext = ""
	try:
		with open(SKINFILE, "r") as fd:
			try:
				domSkin = parse(fd).getroot()
				for element in domSkin:
					if element.tag == "screen" and element.attrib['name'] == skin:
						skintext = ensure_str(tostring(element))
						break
			except Exception as err:
				print("[Skin] Error: Unable to parse skin data in '%s' - '%s'!" % (SKINFILE, err))

	except OSError as err:
		print("[Skin] Error: Unexpected error opening skin file '%s'! (%s)" % (SKINFILE, err))
	return skintext


def printStackTrace():
	import sys
	import traceback
	print("--- STACK TRACE ---")
	traceback.print_exc(file=sys.stdout)
	print('-' * 50)

#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from re import sub, findall, S as RES
from Components.config import config
from Components.ConditionalWidget import BlinkingWidget
from Components.ScrollLabel import ScrollLabel
from Components.Label import Label
from Components.MenuList import MenuList
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from enigma import eListboxPythonMultiContent, gFont, getDesktop

from xml.etree.ElementTree import fromstring, tostring, parse
from six import ensure_str

PICONPATH = resolveFilename(SCOPE_SKIN_IMAGE) + 'picon/'
PLUGINPATH = resolveFilename(SCOPE_PLUGINS) + 'Extensions/TVSpielfilm/'
PICPATH = PLUGINPATH + "pics/"
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()

if DESKTOP_HEIGHT > 720:
	SCALE = 1.5
	ICONPATH = PICPATH + "FHD/icons/"
	SKINFILE = PLUGINPATH + "skin_FHD.xml"
else:
	SCALE = 1.0
	ICONPATH = PICPATH + "HD/icons/"
	SKINFILE = PLUGINPATH + "skin_HD.xml"


class channelDB():

	def __init__(self, servicefile):
		self.servicefile = servicefile
		self.d = dict()
		try:
			for x in open(self.servicefile):
				val, key = x.split()
				self.d[key] = val
		except:
			pass

	def lookup(self, key):
		if key in self.d:
			return self.d[key]
		return 'nope'

	def close(self):
		pass


class serviceDB():

	def __init__(self, servicefile):
		self.servicefile = servicefile
		self.d = dict()
		try:
			for x in open(self.servicefile):
				key, val = x.split()
				self.d[key] = val
		except:
			pass

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
			basesize = 18
		elif config.plugins.tvspielfilm.font_size.value == "small":
			basesize = 14
		else:
			basesize = 16
		self.l.setFont(-2, gFont('Regular', int(16 * SCALE)))
		self.l.setFont(-1, gFont('Regular', int((basesize - 2) * SCALE)))
		self.l.setFont(0, gFont('Regular', int(basesize * SCALE)))
		self.l.setFont(1, gFont('Regular', int((basesize + 2) * SCALE)))
		self.l.setFont(2, gFont('Regular', int(20 * SCALE)))


def applySkinVars(skin, dict):
	for key in dict.keys():
		try:
			skin = skin.replace('{' + key + '}', dict[key])
		except Exception as e:
			print(e, '@key=', key)
	return skin


def makeWeekDay(weekday):
	if weekday == 0:
		_weekday = 'Montag'
	elif weekday == 1:
		_weekday = 'Dienstag'
	elif weekday == 2:
		_weekday = 'Mittwoch'
	elif weekday == 3:
		_weekday = 'Donnerstag'
	elif weekday == 4:
		_weekday = 'Freitag'
	elif weekday == 5:
		_weekday = 'Samstag'
	elif weekday == 6:
		_weekday = 'Sonntag'
	return _weekday


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

	except Exception as err:
		print("[Skin] Error: Unexpected error opening skin file '%s'! (%s)" % (SKINFILE, err))
	return skintext


def printStackTrace():
	import sys
	import traceback
	print("--- STACK TRACE ---")
	traceback.print_exc(file=sys.stdout)
	print('-' * 50)

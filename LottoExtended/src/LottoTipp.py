# -*- coding: utf-8 -*-
#===============================================================================
# LottoExtended Plugin by apostrophe 2009
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from datetime import date, timedelta
from enigma import getDesktop
from xml.etree.ElementTree import parse, tostring
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PLUGINPATH = resolveFilename(SCOPE_PLUGINS) + 'Extensions/LottoExtended/'
if getDesktop(0).size().height() > 720:
	SCALE = 1.5
	SKINFILE = PLUGINPATH + "skin_FHD.xml"
else:
	SCALE = 1.0
	SKINFILE = PLUGINPATH + "skin_HD.xml"


def readSkin(skin):
	skintext = ""
	try:
		with open(SKINFILE, "r") as fd:
			try:
				domSkin = parse(fd).getroot()
				for element in domSkin:
					if element.tag == "screen" and element.attrib['name'] == skin:
						skintext = tostring(element).decode()
						break
			except Exception as err:
				print("[Skin] Error: Unable to parse skin data in '%s' - '%s'!" % (SKINFILE, err))
	except OSError as err:
		print("[Skin] Error: Unexpected error opening skin file '%s'! (%s)" % (SKINFILE, err))
	return skintext


class LottoTipp(object):
	def __init__(self, cfg):
		self.cfg = cfg
		self.resetTreffer()

	def getCfg(self):
		return self.cfg

	def getName(self):
		return self.cfg.name.value

	def name(self):
		return self.cfg.name

	def getLosnummer(self):
		return self.cfg.losnummer

	def getLosnummerv(self):
		return self.cfg.losnummer.value

	def losnummer(self):
		value = "0000000" + str(self.cfg.losnummer.value)
		return value[-7:]

	def getSpiel77JaNein(self):
		return self.cfg.actSpiel77.getText()

	def getSuper6JaNein(self):
		return self.cfg.actSuper6.getText()

	def getActSpiel77(self):
		return self.cfg.actSpiel77.value

	def actSpiel77(self):
		return self.cfg.actSpiel77

	def getActSuper6(self):
		return self.cfg.actSuper6.value

	def actSuper6(self):
		return self.cfg.actSuper6

	def getZiehungTag(self):
		tage = ["ausgesetzt", "Samstag", "Mittwoch", "Sa + Mi"]
		return tage[self.cfg.ziehung.index]

	def getZiehung(self):
		return int(self.cfg.ziehung.value)

	def ziehung(self):
		return self.cfg.ziehung

	def spiel(self, index):
		return self.cfg.spiel[index]

	def spielv(self, index):
		return self.cfg.spiel[index].value

	def system(self, index):
		return self.cfg.system[index]

	def systemv(self, index):
		return self.cfg.system[index].value

	def getZiehungTagKurz(self):
		tage = ["", "Sa", "Mi", "Sa+Mi"]
		return tage[self.cfg.ziehung.index]

	def getZiehungTagTxt(self):
		return self.cfg.ziehung.getText()

	def getFirstDrawFormat(self, fmt="%d.%m.%Y"):
		datum = date.fromtimestamp(self.cfg.firstDraw.value)
		return datum.strftime(fmt)

	def drawings(self):
		return self.cfg.drawings

	def getDrawings(self):
		return int(self.cfg.drawings.value)

	def getDrawingsText(self):
		return self.cfg.drawings.getText()

	def getLastDrawFormat(self, fmt="%d.%m.%Y"):
		if self.getDrawings() == 0:
			return "unbegrenzt"
		return self.getLastDrawDate().strftime(fmt)

	def getLastDrawDate(self):
		fromDate = date.fromtimestamp(self.cfg.firstDraw.value)
		if self.getZiehung() == 3:  # Sa+Mi
			days = (self.getDrawings() - 1) * 7 + 3 + (fromDate.weekday() == 5)
		else:
			days = (self.getDrawings() - 1) * 7
		datum = fromDate + timedelta(days=days)
		return datum

	def getFirstDraw(self):
		return self.cfg.firstDraw.value

	def firstDraw(self):
		return self.cfg.firstDraw

	def resetTreffer(self):
		self.lottotreffer = [0, 0, 0, 0, 0, 0, 0, 0, 0]
		self.spiel77treffer = 0
		self.super6treffer = 0
		for i in range(12):
			self.spiel(i).treffer = [0, 0]
		self.gewinnSumme = 0

	def getTeilnahme(self, weekday):
		if self.getZiehung() == 0:
			return -1			# ausgesetzt
		elif self.getZiehung() == 1 and weekday == 5:  # teilnahme nur sa
			return 1
		elif self.getZiehung() == 2 and weekday == 2:  # teilnahme nur mi
			return 1
		elif self.getZiehung() == 3:					# teilnahme sa+mi
			return 1
		return 0

	def participation(self, datum):
		""" prüft spielscheinteilnahme zum übergebenen datum
			rückgabewerte: 
			-3	keine teilnahme - wochentag trifft nicht zu
			-2	keine teilnahme - letzte teilnahme vor datum
			-1	keine teilnahme - erste teilnahme nach datum
			0	keine teilnahme - spielschein ausgesetzt
			1	teilnahme """
		if self.getZiehung() == 0:
			return 0		# ausgesetzt
		if date.fromtimestamp(self.cfg.firstDraw.value) > datum:
			return -1							# teilnahme später
		if self.getDrawings() == 0: 			# unlimited
			pass
		elif self.getLastDrawDate() < datum:
			return -2							# teilnahme früher

		if self.getZiehung() == 3:				# sa+mi
			return 1
		else:
			weekday = datum.weekday()
			if self.getZiehung() == 1 and weekday != 5:
				return -3
			elif self.getZiehung() == 2 and weekday != 2:
				return -3
		return 1

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
from time import mktime
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.config import ConfigInteger, ConfigSelection, ConfigSubList, ConfigSubsection, ConfigText, ConfigYesNo, ConfigSequence, ConfigDateTime, config, getConfigListEntry, KEY_LEFT, KEY_RIGHT
from Components.Label import Label
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from .LottoTipp import LottoTipp
from .LottoTipp import readSkin


class LottoSelection(ConfigSelection):
	def __init__(self, choices, default):
		ConfigSelection.__init__(self, choices, default)

	def deleteNotifier(self, notifier):
		self.notifiers.remove(notifier)


class LottoSystem(ConfigSelection):
	def __init__(self, choices, default, counter):
		self.counter = counter
		ConfigSelection.__init__(self, choices, default)

	def deleteNotifier(self, notifier):
		self.notifiers.remove(notifier)

	def save(self):
		pass

	def isChanged(self):
		return False

	def load(self):
		pass

	def cancel(self):
		pass


class LottoConfigDateTime(ConfigDateTime):
	def __init__(self, default, formatstring, ziehung):
		ConfigDateTime.__init__(self, default, formatstring)
		self.ziehung = ziehung

	def setDateDay(self):
		tag = self.ziehung.value
		fDate = date.fromtimestamp(self.value)
		cur_day = fDate.weekday()
		if tag == "0":
			return 0
		elif tag == "1":  # Samstag
			if cur_day < 5:
				self.handleKey(KEY_RIGHT, "mydummy")
				return 1
			elif cur_day > 5:
				self.handleKey(KEY_LEFT, "mydummy")
				return 1
		elif tag == "2" or tag == "3":  # Mittwoch ; Mi +Sa
			if cur_day < 2:
				self.handleKey(KEY_RIGHT, "mydummy")
				return 1
			elif cur_day > 2:
				self.handleKey(KEY_LEFT, "mydummy")
				return 1
		return 0

	def handleKey(self, key, dummy):
		fDate = date.fromtimestamp(self.value)
		cur_day = fDate.weekday()
		tag = self.ziehung.value
		increment = -7
		if tag == "0":
			pass
		elif key == KEY_LEFT:  # prev date
			if tag == "1":  # Samstag
				increment = (cur_day + 2) % 7 or 7
			elif tag == "2":  # Mittwoch
				increment = (cur_day + 5) % 7 or 7
			elif tag == "3":  # Mi+Sa
				increment = (cur_day + 2) % 7 if cur_day <= 2 or cur_day == 6 else cur_day - 2
			newDate = fDate - timedelta(days=increment)
			self.value = int(mktime(newDate.timetuple()))
		elif key == KEY_RIGHT:  # next date
			if tag == "1":  # Samstag
				increment = (12 - cur_day) % 7 or 7
			elif tag == "2":  # Mittwoch
				increment = (9 - cur_day) % 7 or 7
			elif tag == "3":  # Mi+Sa
				if cur_day < 2:
					increment = (2 - cur_day)
				elif cur_day < 5:
					increment = 5 - cur_day
				else:
					increment = 9 - cur_day
			newDate = fDate + timedelta(days=increment)
			self.value = int(mktime(newDate.timetuple()))
#		elif key == KEY_HOME or key == KEY_END:
#			self.value = self.default

	def extendDraw(self, weeks):
		days = int(weeks) * 7
		fDate = date.fromtimestamp(self.value)
		newDate = fDate + timedelta(days=days)
		self.value = int(mktime(newDate.timetuple()))

	def deleteNotifier(self, notifier):
		self.notifiers.remove(notifier)


class LottoConfigSequence(ConfigSequence):
	def __init__(self, lottosystemcfg):
		self.system = lottosystemcfg
		self.treffer = [0, 0]
		self.marked_pos = 0
		zahlen = int(self.system.value)
		ConfigSequence.__init__(self, " ", [(1, 49) for i in range(zahlen)], [0 for i in range(zahlen)])

	def switchNormalSystem(self):
		i = int(self.system.value)
		j = len(self.value)
		self.setLimitDefault(i)
		dif = i - j
		if dif > 0:
			for ii in range(dif):
				self.value.append(0)
		elif dif < 0:
			del self.value[i:j]

	def setLimitDefault(self, count):
		self.default = [0 for i in range(count)]
		self.limits = [(1, 49) for i in range(count)]
		self.blockLen = [len(str(x[1])) for x in self.limits]
		self.totalLen = sum(self.blockLen) - 1
		self.markedPos = 0

	def cancel(self):
		self.load()

	def save(self):
		if self.save_disabled or self.value == self.default:
			self.saved_value = None
		else:
			self.value.sort()
			try:
				self.saved_value = self.toString(self.value)  # bei openATV 7.x
			except Exception:
				self.saved_value = self.tostring(self.value)  # bei openATV 6.x
			self.marked_pos = 0

	def validate(self):
		max_pos = 0
		num = 0
		for i in self._value:
			max_pos += len(str(self.limits[num][1]))
			if self._value[num] > self.limits[num][1]:
				self._value[num] = self.limits[num][1]
			num += 1
		if self.marked_pos >= max_pos:
			if self.endNotifier:
				for x in self.endNotifier:
					x(self)
			self.marked_pos = max_pos - 1
		if self.marked_pos < 0:
			self.marked_pos = 0

	def toDefault(self):
		self.value = self.default[:]
		self.marked_pos = 0

	def load(self):
		sv = self.saved_value
		try:
			self.value = [0 for i in range(6)] if sv is None else self.fromString(sv)  # bei openATV 7.x
		except Exception:
			self.value = [0 for i in range(6)] if sv is None else self.fromstring(sv)  # bei openATV 6.x
		count = len(self.value)
		self.setLimitDefault(count)
		self.system.value = str(count)


class __LottoTippConfig(object):
	def __init__(self):
		self.tipplist = []
		config.plugins.lotto = ConfigSubsection()
		config.plugins.lotto.tippcount = ConfigInteger(0)
		config.plugins.lotto.tipps = ConfigSubList()
		for tippnum in range(0, config.plugins.lotto.tippcount.value):
			self.new()

	def new(self):  # Add a new tipp or load a configsection if existing
		newTippConfigSubsection = ConfigSubsection()
		config.plugins.lotto.tipps.append(newTippConfigSubsection)
		newTippConfigSubsection.name = ConfigText("Tipp %s" % self.getTippCount(), False)
		if newTippConfigSubsection.name.value == newTippConfigSubsection.name.default:
			newTippConfigSubsection.name.default = ""
		newTippConfigSubsection.losnummer = ConfigInteger(0000000, (0000000, 9999999))
		newTippConfigSubsection.actSpiel77 = ConfigYesNo(False)
		newTippConfigSubsection.actSuper6 = ConfigYesNo(False)
		ziehung = LottoSelection([("0", "ausgesetzt"), ("1", "Samstag"), ("2", "Mittwoch"), ("3", "Samstag+Mittwoch")], "0")
		newTippConfigSubsection.drawings = ConfigSelection([("0", "unbegrenzt"),
			("1", "1 Woche"),
			("2", "2 Wochen"),
			("3", "3 Wochen"),
			("4", "4 Wochen"),
			("5", "5 Wochen"),
			("6", "6 Wochen"),
			("7", "7 Wochen"),
			("8", "8 Wochen")], "0")
		today = date.today()
		drawing = today - timedelta(days=today.weekday())
		newTippConfigSubsection.firstDraw = LottoConfigDateTime(int(mktime(drawing.timetuple())), "%d. %B  %Y", ziehung)
		newTippConfigSubsection.ziehung = ziehung
		newTippConfigSubsection.spiel = ConfigSubList()
		newTippConfigSubsection.system = ConfigSubList()
		for i in range(12):
			newTippConfigSubsection.system.append(LottoSystem(
				[("6", "Normaltipp"),
				 ("7", "Vollsystem 6 aus 7"),
				 ("8", "Vollsystem 6 aus 8"),
				 ("9", "Vollsystem 6 aus 9"),
				 ("10", "Vollsystem 6 aus 10"),
				 ("11", "Vollsystem 6 aus 11"),
				 ("12", "Vollsystem 6 aus 12"),
				], "6", i))
			newTippConfigSubsection.spiel.append(LottoConfigSequence(newTippConfigSubsection.system[i]))
		newTipp = LottoTipp(newTippConfigSubsection)
		self.tipplist.append(newTipp)
		return newTipp

	def delete(self, tipp):
		config.plugins.lotto.tipps.remove(tipp.getCfg())
		self.tipplist.remove(tipp)
		self.__save()

	def save(self, tipp):
		tipp.getCfg().save()
		self.__save()

	def cancel(self, tipp):
		for element in tipp.getCfg().dict().values():
			if isinstance(element, ConfigSubList):
				for subelement in element.dict().values():
					subelement.cancel()
			else:
				element.cancel()

	def getTipplist(self):
		return self.tipplist

	def getTippByName(self, name):
		for tipp in self.tipplist:
			if tipp.getName() == name:
				return tipp
		return None

	def __save(self):
		config.plugins.lotto.tippcount.value = self.getTippCount()
		config.plugins.lotto.tippcount.save()

	def getTippCount(self):
		return len(config.plugins.lotto.tipps)


lottoTippConfig = __LottoTippConfig()


class LottoTippConfigScreen(Screen, ConfigListScreen):
	def __init__(self, session, tipp):
		self.skin = readSkin("LottoTippConfigScreen")
		Screen.__init__(self, session)
		self.session = session
		self.tipp = tipp
		self.toValidate = None
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"yellow": self.extendDraw,
			"blue": self.keyDeleteSpiel,
			"cancel": self.keyCancel,
			"up": self.up,
			"down": self.down
		}, -2)
		self["key_red"] = Button(_("Abbrechen"))
		self["key_green"] = Button("Abspeichern")
		self["key_yellow"] = Button("Erweitert")
		self["key_blue"] = Button("Tipp löschen")
		self["statuslabel"] = Label(" ")
		cfglist = []
		cfglist.append(getConfigListEntry("Tippscheinname", self.tipp.name()))
		cfglist.append(getConfigListEntry("Teilnahme an Ziehung(en)", self.tipp.ziehung()))
		cfglist.append(getConfigListEntry("Erste Ziehung", self.tipp.firstDraw()))
		self.tipp.ziehung().addNotifier(self.setFirstDraw, False)
		cfglist.append(getConfigListEntry("Teilnahme in Wochen", self.tipp.drawings()))
		cfglist.append(getConfigListEntry("Losnummer (für Spiel77, Super6, Superzahl)", self.tipp.getLosnummer()))
		cfglist.append(getConfigListEntry("Teilnahme an Spiel77?", self.tipp.actSpiel77()))
		cfglist.append(getConfigListEntry("Teilnahme an Super6?", self.tipp.actSuper6()))
		for ix in range(12):
			cfglist.append(getConfigListEntry("Spiel " + str(ix + 1) + ": Normal/System", self.tipp.system(ix)))
			self.tipp.system(ix).addNotifier(self.setSwitchNormalSystem, False)
			cfglist.append(getConfigListEntry("Tipp Spiel " + str(ix + 1) + ":", self.tipp.spiel(ix)))
		ConfigListScreen.__init__(self, cfglist, session)
		self.tipp.ziehung().addNotifier(self.checkExpired, False)
		self.tipp.firstDraw().addNotifier(self.checkExpired, False)
		self.tipp.drawings().addNotifier(self.checkExpired, False)
		self.checkExpired(None)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.tipp.ziehung().deleteNotifier(self.setFirstDraw)
		self.tipp.ziehung().deleteNotifier(self.checkExpired)
		self.tipp.firstDraw().deleteNotifier(self.checkExpired)
		self.tipp.drawings().notifiers.remove(self.checkExpired)
		for i in range(12):
			self.tipp.system(i).deleteNotifier(self.setSwitchNormalSystem)

	def setFirstDraw(self, configElement):
		firstDraw = self.tipp.firstDraw()
		done = firstDraw.setDateDay()
		if done:
			ix = self["config"].getCurrentIndex()
			self["config"].setCurrentIndex(ix + 1)
			self["config"].invalidateCurrent()
			self["config"].setCurrentIndex(ix)
			self["statuslabel"].setText("Erster Ziehungstag wurde angepasst")

	def extendDraw(self):
		if self.checkExpired(None):
			self.tipp.firstDraw().extendDraw(self.tipp.getDrawings())
			ix = self["config"].getCurrentIndex()
			self["config"].setCurrentIndex(2)
			self["config"].invalidateCurrent()
			self["config"].setCurrentIndex(ix)
			# self.checkExpired()

	def checkExpired(self, configelement):
		if self.tipp.getZiehung() != 0:
			if self.tipp.getDrawings() != 0:
				if self.tipp.getLastDrawDate() < date.today():
					self["key_yellow"].setText("verlängern")
					return 1
		self["key_yellow"].setText("")
		return 0

	def setSwitchNormalSystem(self, configElement):
		counter = configElement.counter
		self.tipp.spiel(counter).switchNormalSystem()
		ix = self["config"].getCurrentIndex()
		self["config"].setCurrentIndex(ix + 1)
		self["config"].invalidateCurrent()
		self["config"].setCurrentIndex(ix)
		self.toValidate = self.tipp.spiel(counter)

	def validateSpiel(self, spiel):
		self.toValidate = None
		if not spiel.value == spiel.default:
			name = self["config"].getCurrent()[0]
			dups = []
			for i in spiel.value:
				if i == 0:
					self.session.open(MessageBox, _(("Ungültige Zahl (0) in %s\n\nNur 01 - 49 erlaubt." % (name))), MessageBox.TYPE_WARNING, timeout=3, close_on_any_key=True)
					return False
				if dups.count(i) == 0 and spiel.value.count(i) > 1:  # doppelte Werte nicht zulassen
					dups.append(i)
			if len(dups) > 0:
				self.session.open(MessageBox, _(("Doppelte Zahl(en) in %s:\n\n%s" % (name, str(dups)))), MessageBox.TYPE_WARNING, timeout=3, close_on_any_key=True)
				return False
		return True

	def keyDeleteSpiel(self):
		spiel = self.getCurrentConfigPath()
		if isinstance(spiel, LottoConfigSequence):
			if spiel._value != spiel.default:
				name = self["config"].getCurrent()[0]
				self.session.openWithCallback(self.deleteSpiel, MessageBox, ("Soll '%s' wirklich gelöscht werden?" % name), MessageBox.TYPE_YESNO, timeout=20, default=False)

	def deleteSpiel(self, result):
		if result:
			spiel = self.getCurrentConfigPath()
			spiel.toDefault()
			self["config"].invalidateCurrent()

	def getCurrentConfigPath(self):
		return self["config"].getCurrent()[1]

	def setDeleteButtonText(self, cfgentry):
		self["statuslabel"].setText(" ")
		txt = self["key_blue"].getText()
		if isinstance(cfgentry, LottoConfigSequence):
			if txt != "Lösche Spiel":
				self["key_blue"].setText("Lösche Spiel")
		else:
			if txt != " ":
				self["key_blue"].setText(" ")

	def up(self):
		self["statuslabel"].setText("")
		current = self.getCurrentConfigPath()
		if isinstance(current, LottoConfigSequence):
			if not self.validateSpiel(current):
				return
		elif self.toValidate:
			if not self.validateSpiel(self.toValidate):
				self["config"].instance.moveSelection(self["config"].instance.moveDown)
				return
		self["config"].instance.moveSelection(self["config"].instance.moveUp)
		self.setDeleteButtonText(self.getCurrentConfigPath())

	def down(self):
		self["statuslabel"].setText("")
		self.toValidate = None
		current = self.getCurrentConfigPath()
		if isinstance(current, LottoConfigSequence):
			if not self.validateSpiel(current):
				return
		self["config"].instance.moveSelection(self["config"].instance.moveDown)
		self.setDeleteButtonText(self.getCurrentConfigPath())

	def keySave(self):
		self["statuslabel"].setText("")
		current = self.getCurrentConfigPath()
		if isinstance(current, LottoConfigSequence):
			if not self.validateSpiel(current):
				return
		elif self.toValidate:
			if not self.validateSpiel(self.toValidate):
				self["config"].instance.moveSelection(self["config"].instance.moveDown)
				return
		self.close(True, self.tipp)

	def isChanged(self):
		for element in self.tipp.getCfg().dict().values():
			if isinstance(element, ConfigSubList):
				for subelement in element.dict().values():
					if subelement.isChanged():
						return True
			else:
				if element.isChanged():
					return True
		return False

	def keyCancel(self):
		if self.isChanged():
			self.session.openWithCallback(self.cancelCallback, MessageBox, "Sollen die Änderungen wirklich rückgängig gemacht werden?", MessageBox.TYPE_YESNO, timeout=20, default=False)
		else:
			self.close(False, self.tipp)

	def cancelCallback(self, result):
		if result:
			if result:
				self.close(False, self.tipp)

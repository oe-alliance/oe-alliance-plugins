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
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Sources.List import List
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from .LottoTippConfig import lottoTippConfig, LottoTippConfigScreen
from .LottoTipp import readSkin

SYSTEMTAB = (  # seit 4.5.2013 mit 9 gewinnklassen
	#+6 aus 7 neu							#pos	anzahl richtige klasse
	((5, 0, 0, 0, 0, 0, 0, 0, 0),			# 0		2+
	(0, 4, 0, 0, 0, 0, 0, 0, 0),			# 1		3
	(3, 0, 4, 0, 0, 0, 0, 0, 0),			# 2		3+
	(0, 4, 0, 3, 0, 0, 0, 0, 0),			# 3		4
	(0, 0, 4, 0, 3, 0, 0, 0, 0),			# 4		4+
	(0, 0, 0, 5, 0, 2, 0, 0, 0),			# 5		5
	(0, 0, 0, 0, 5, 0, 2, 0, 0),			# 6		5+
	(0, 0, 0, 0, 0, 6, 0, 1, 0),			# 7		6
	(0, 0, 0, 0, 0, 0, 6, 0, 1)),			# 8		6+
#	 9	8  7  6  5  4  3  2  1     = anzahl der gewinne in klasse
#	 2+	3  3+ 4  4+ 5  5+ 6  6+sz  = anzahl richtige
	#+6 aus 8 neu
	((15, 0, 0, 0, 0, 0, 0, 0, 0),
	(0, 10, 0, 0, 0, 0, 0, 0, 0),
	(15, 0, 10, 0, 0, 0, 0, 0, 0),
	(0, 16, 0, 6, 0, 0, 0, 0, 0),
	(6, 0, 16, 0, 6, 0, 0, 0, 0),
	(0, 10, 0, 15, 0, 3, 0, 0, 0),
	(0, 0, 10, 0, 15, 0, 3, 0, 0),
	(0, 0, 0, 15, 0, 12, 0, 1, 0),
	(0, 0, 0, 0, 15, 0, 12, 0, 1)),
	#+6 aus 9 neu
	((35, 0, 0, 0, 0, 0, 0, 0, 0),
	(0, 20, 0, 0, 0, 0, 0, 0, 0),
	(45, 0, 20, 0, 0, 0, 0, 0, 0),
	(0, 40, 0, 10, 0, 0, 0, 0, 0),
	(30, 0, 40, 0, 10, 0, 0, 0, 0),
	(0, 40, 0, 30, 0, 4, 0, 0, 0),
	(10, 0, 40, 0, 30, 0, 4, 0, 0),
	(0, 20, 0, 45, 0, 18, 0, 1, 0),
	(0, 0, 20, 0, 45, 0, 18, 0, 1)),
	#+6 aus 10 neu
	((70, 0, 0, 0, 0, 0, 0, 0, 0),
	(0, 35, 0, 0, 0, 0, 0, 0, 0),
	(105, 0, 35, 0, 0, 0, 0, 0, 0),
	(0, 80, 0, 15, 0, 0, 0, 0, 0),
	(90, 0, 80, 0, 15, 0, 0, 0, 0),
	(0, 100, 0, 50, 0, 5, 0, 0, 0),
	(50, 0, 100, 0, 50, 0, 5, 0, 0),
	(0, 80, 0, 90, 0, 24, 0, 1, 0),
	(15, 0, 80, 0, 90, 0, 24, 0, 1)),
	#+6 aus 11 neu
	((126, 0, 0, 0, 0, 0, 0, 0, 0),
	(0, 56, 0, 0, 0, 0, 0, 0, 0),
	(210, 0, 56, 0, 0, 0, 0, 0, 0),
	(0, 140, 0, 21, 0, 0, 0, 0, 0),
	(210, 0, 140, 0, 21, 0, 0, 0, 0),
	(0, 200, 0, 75, 0, 6, 0, 0, 0),
	(150, 0, 200, 0, 75, 0, 6, 0, 0),
	(0, 200, 0, 150, 0, 30, 0, 1, 0),
	(75, 0, 200, 0, 150, 0, 30, 0, 1)),
	#+6 aus 12 neu
	((210, 0, 0, 0, 0, 0, 0, 0, 0),
	(0, 84, 0, 0, 0, 0, 0, 0, 0),
	(378, 0, 84, 0, 0, 0, 0, 0, 0),
	(0, 224, 0, 28, 0, 0, 0, 0, 0),
	(420, 0, 224, 0, 28, 0, 0, 0, 0),
	(0, 350, 0, 105, 0, 7, 0, 0, 0),
	(350, 0, 350, 0, 105, 0, 7, 0, 0),
	(0, 400, 0, 225, 0, 36, 0, 1, 0),
	(225, 0, 400, 0, 225, 0, 36, 0, 1)))


def num2FormStr(nummer):
	nummer += 0.00
	if nummer < 0:
		nummer = abs(nummer)
		sign = '-'
	else:
		sign = ''
	nummer = "%.2f" % nummer
	numstr = str(nummer).split('.')
	ret1 = numstr[1]
	l = len(numstr[0])
	if l <= 3:
		ret = numstr[0]
	else:
		start = l % 3
		loop = int(l / 3 + 1)
		ret = numstr[0][:start]
		for i in range(1, loop):
			if start != 0:
				ret += '.'
			ret += numstr[0][start:start + 3]
			start += 3
	return "%s%s,%s" % (sign, ret, ret1)


class GewinnListScreen(Screen):
	def __init__(self, session, currdate, ziehungen,):
		self.skin = readSkin("GewinnListScreen")
		Screen.__init__(self, session)
		self.session = session
		self.ziehungen = ziehungen
		self.currDate = currdate
		self.ziehung = self.ziehungen.drawings[self.currDate]
		self["spiel77"] = Label(self.ziehung.strSpiel77)
		self["super6"] = Label(self.ziehung.strSuper6)
		if self.ziehung.datum.weekday() == 5:
			tag = "Samstag"
		else:
			tag = "Mittwoch"
		self["auslosung"] = Label(" Auslosung vom %s, %s" % (tag, self.ziehung.datum.strftime("%d. %B %Y")))
		self["dispsuper"] = Label(self.ziehung.strSuperzahl)
		self["displotto"] = Label(" - ".join(self.ziehung.strLotto))
		self["tipplist"] = List([])
		self["spiel77"] = Label("")
		self["super6"] = Label("")
		self["auslosung"] = Label("")
		self["dispsuper"] = Label("")
		self["displotto"] = Label("")
		self["key_red"] = Button()
		self["key_green"] = Button("Detailansicht")
		self["key_yellow"] = Button("Tipp löschen")
		self["key_blue"] = Button()
		self["statuslabel"] = Label()
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"back": self.close,
			"red": self.prevDraw,
			"green": self.keyDetail,
			"yellow": self.keyDelete,
			"blue": self.nextDraw,
#			 "blue": self.changeZiehung,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.down,
			"ok": self.keyEditTipp
#			 "ok": self.keyNoAction
		}, -1)
		self.onLayoutFinish.append(self.newDrawing)
		#self.newDrawing(currdate)

	def newDrawing(self, datum=None):
		if datum is not None:
			self.currDate = datum
		self.ziehung = self.ziehungen.drawings[self.currDate]
		self.gezogen = list(map(int, self.ziehung.strLotto))
		if self.ziehung.datum.weekday() == 5:
			tag = "Samstag"
		else:
			tag = "Mittwoch"
		self["spiel77"].text = self.ziehung.strSpiel77
		self["super6"].text = self.ziehung.strSuper6
		if self.ziehung.datum.weekday() == 5:
			tag = "Samstag"
		else:
			tag = "Mittwoch"
		self["auslosung"].text = " Auslosung vom %s, %s" % (tag, self.ziehung.datum.strftime("%d. %B %Y"))
		self["dispsuper"].text = self.ziehung.strSuperzahl
		self["displotto"].text = " - ".join(self.ziehung.strLotto)
		self.setDates()
		self.updateTipplist()

	def updateTipplist(self):
		count = 0
		self.active = 0
		self.totalsumme = 0.0
		self.gewinne = 0
		tipplist = []
		for tipp in lottoTippConfig.getTipplist():
			tipp.resetTreffer()
			if tipp.participation(self.ziehung.datum) == 1:
				self.active += 1
				self.gewinnAuswertung(tipp)
			count += 1
			tipp.count = count
			tipplist.append(self.buildListboxEntry(tipp))
		self["tipplist"].setList(tipplist)
		if self.gewinne:
			if self.ziehung.lottoquote is None:
				self["statuslabel"].setText("Quoten wurden noch nicht ermittelt")
			if self.totalsumme:
				self["statuslabel"].setText("Gewinnsumme: %s € - ohne Gewähr -" % num2FormStr(self.totalsumme))
		elif self.active == 0:
			self["statuslabel"].setText("Keine Teilnahme an dieser Auslosung")
		else:
			self["statuslabel"].setText("Kein Gewinn festgestellt")

	def gewinnAuswertung(self, tipp):
		tipp.resetTreffer()
		if tipp.participation(self.ziehung.datum) == 1:
			check = True
			if tipp.getActSpiel77():
				if self.ziehung.strSpiel77[0] == '?':
					tipp.spiel77treffer = -1
				else:
					tipp.spiel77treffer = self.ziehung.richtigeS77(tipp.getLosnummerv())
					if tipp.spiel77treffer and check:
						self.gewinne += 1
						check = False
			if tipp.getActSuper6():
				if self.ziehung.strSuper6[0] == '?':
					tipp.super6treffer = -1
				else:
					tipp.super6treffer = self.ziehung.richtigeS6(tipp.getLosnummerv())
					if tipp.super6treffer and check:
						self.gewinne += 1
						check = False
			for ix in range(12):
				if tipp.spielv(ix) != tipp.spiel(ix).default:
					systemtipp = len(tipp.spielv(ix)) - 7
					richtigeSpiel = len(self.ziehung.richtigeLotto(tipp.spielv(ix)))
					tipp.spiel(ix).treffer[0] = richtigeSpiel
					if richtigeSpiel > 1:
						gotSZ = self.ziehung.richtigeSuperzahl(tipp.losnummer())
					if richtigeSpiel >= 3 or (richtigeSpiel == 2 and gotSZ):  # 2+
						if gotSZ:
							tipp.spiel(ix).treffer[1] = 1
						if check:
							self.gewinne += 1
							check = False
						if richtigeSpiel == 2:
							pos = 0  # gotSZ is set ; already checked
						elif richtigeSpiel == 3:
							pos = 1 + gotSZ
						elif richtigeSpiel == 4:
							pos = 3 + gotSZ
						elif richtigeSpiel == 5:
							pos = 5 + gotSZ
						elif richtigeSpiel == 6:
							pos = 7 + gotSZ
						if systemtipp >= 0:
							tipp.lottotreffer = list(map(lambda x, y: x + y, tipp.lottotreffer, SYSTEMTAB[systemtipp][pos]))
						else:
							tipp.lottotreffer[pos] += 1
			if self.gewinne and self.ziehung.lottoquote is not None:
				self.computeGewinnSumme(tipp)
				self.totalsumme += tipp.gewinnSumme

	def buildListboxEntry(self, tipp):
		res = [tipp, " " + tipp.getName()]
		participation = tipp.participation(self.ziehung.datum)
		if participation == 0:
			res.extend([" ausgesetzt", "", ""])
		elif participation == -3:
			res.extend([" Teiln. nur am %s" % tipp.getZiehungTagTxt(), "", ""])
		elif participation == -1:
			res.extend([" Teilnahme ab %s" % tipp.getFirstDrawFormat("%d.%m.%Y"), "", ""])
		elif participation == -2:
			res.extend([" Teilnahme bis %s" % tipp.getLastDrawFormat("%d.%m.%Y"), "", ""])
		else:
			res.append(" " + tipp.getZiehungTagKurz())
			if tipp.getActSpiel77():
				if tipp.spiel77treffer > 0:
					m = ["-", "-", "-", "-", "-", "-", "-"]
					m[-tipp.spiel77treffer:] = self.ziehung.strSpiel77[-tipp.spiel77treffer:]
					val = "".join(m)
				elif tipp.spiel77treffer < 0:
					val = '???????'
				else:
					val = "-------"
			else:
				val = ""
			res.append(val)
			if tipp.getActSuper6():
				if tipp.super6treffer > 0:
					m = ["-", "-", "-", "-", "-", "-"]
					m[-tipp.super6treffer:] = self.ziehung.strSuper6[-tipp.super6treffer:]
					val = "".join(m)
				elif tipp.super6treffer < 0:
					val = '??????'
				else:
					val = "------"
			else:
				val = ""
			res.append(val)
		for ix in range(9):
			val = "" if tipp.lottotreffer[ix] == 0 else str(tipp.lottotreffer[ix])
			res.append(val)
		return tuple(res)

	def computeGewinnSumme(self, tipp):
		summe = 0
		if tipp.participation(self.ziehung.datum) == 1:
			summe += sum(list(map(lambda x, y: x * y, tipp.lottotreffer, self.ziehung.lottoquote)))
			if tipp.spiel77treffer > 0:
				summe += self.ziehung.s77quote[tipp.spiel77treffer - 1]
			if tipp.super6treffer > 0:
				summe += self.ziehung.s6quote[tipp.super6treffer - 1]
			tipp.gewinnSumme = summe

	def keyNoAction(self):
		pass

	def keyDetail(self):
		if self["tipplist"].current:
			tipp = self["tipplist"].current[0]
			if tipp is not None:
				self.session.openWithCallback(self.detailCallback, GewinnDetailScreen, tipp, self.ziehung, self.totalsumme)

	def detailCallback(self, result):
		if result == 0:
			return
		elif result == 1:
			self.up()
		else:
			self.down()
		self.keyDetail()

	def keyDelete(self):
		if self["tipplist"].current:
			tipp = self["tipplist"].current[0]
			if tipp is not None:
				self.session.openWithCallback(self.deleteCallback, MessageBox, ("Soll '%s' wirklich gelöscht werden?" % tipp.getName()))

	def deleteCallback(self, result):
		if result:
			tipp = self["tipplist"].current[0]
			index = self["tipplist"].index
			lottoTippConfig.delete(tipp)
			self.updateTipplist()
			self["tipplist"].index = index - 1

	def keyEditTipp(self):
		if self["tipplist"].current:
			tipp = self["tipplist"].current[0]
			if tipp is not None:
				self.session.openWithCallback(self.editCallback, LottoTippConfigScreen, tipp)

	def editCallback(self, result, tipp):
		index = self["tipplist"].index
		if result:
			lottoTippConfig.save(tipp)
			self.updateTipplist()
			self["tipplist"].index = index

	def setDates(self):
		if self.currDate.weekday() == 5:  # Saturday
			nxt = 4
			prv = -3
		else:
			nxt = 3
			prv = -4
		self.nextDate = min(self.ziehungen.highDate, self.currDate + timedelta(days=nxt))
		self.prevDate = max(self.currDate + timedelta(days=prv), date(2013, 5, 4))
		if self.nextDate == self.currDate:
			self["key_blue"].text = ""
		else:
			self["key_blue"].text = self.nextDate.strftime(_("%d.%m.%Y"))
		if self.prevDate == self.currDate:
			self["key_red"].text = ""
		else:
			self["key_red"].text = self.prevDate.strftime(_("%d.%m.%Y"))

	def prevDraw(self):
		if self.currDate == self.prevDate:
			return
		self.download(self.prevDate)

	def nextDraw(self):
		if self.currDate == self.nextDate:
			return
		self.download(self.nextDate)

	def download(self, datum):
		if datum in self.ziehungen.drawings:
			self.newDrawing(datum)
		else:
			self["statuslabel"].setText(_("Download gestartet"))
			self.ziehungen.download(datum, self.downloadOK, self.downloadFailed)

	def downloadFailed(self, text, output):
		self["statuslabel"].setText(text)
		self.currDate = self.prevDate = self.nextDate = date(1970, 1, 1)
		self["key_blue"].text = ""
		self["key_red"].text = ""
		if isinstance(output, str):
			self.session.open(MessageBox, "%s\n\n%s" % (text, output), type=MessageBox.TYPE_ERROR)

	def downloadOK(self, datum):
		self.newDrawing(datum)

	def up(self):
		self["tipplist"].selectPrevious()

	def down(self):
		self["tipplist"].selectNext()

	def left(self):
		self["tipplist"].pageUp()

	def right(self):
		self["tipplist"].pageDown()

	def close(self):
		Screen.close(self, True, self.currDate)


class GewinnDetailList(List):
	def __init__(self, tipp, gewinnzahlen):
		List.__init__(self, [])
		self.ziehung = gewinnzahlen
		self.gewinn = False
		self.tipp = tipp

	def buildListbox(self):
		list = []
		res = ["" for x in range(18)]
		res[0] = " Tippschein: "
		res[1] = " " + self.tipp.getName()
		list.append(tuple(res))
		res = ["" for x in range(18)]
		res[0] = " Teilname:"
		participation = self.tipp.participation(self.ziehung.datum)
		if participation == 1:
			res[1] = " %s / ab %s / %s" % (self.tipp.getZiehungTagTxt(), self.tipp.getFirstDrawFormat("%d.%m.%Y"), self.tipp.getDrawingsText())
		elif participation == 0:
			res[1] = " keine Teilnahme"
		elif participation == -3:
			res[1] = " keine Teilnahme am %s" % self.tipp.getZiehungTagKurz()
		elif participation == -1:
			res[1] = " ab %s" % self.tipp.getFirstDrawFormat("%d.%m.%y")
		else:
			res[1] = " endete %s" % self.tipp.getLastDrawFormat("%d.%m.%y")  # participation -2
		list.append(tuple(res))

		def spiel77super6(teilgenommen, zahl, treffer):
			if teilgenommen:
				if treffer > 0:
					redstart = len(zahl) - treffer
					self.gewinn = True
				else:
					redstart = 9
				num = 0
				ix = 2
				for ziffer in zahl:
					num += 1
					if num > redstart:
						res[ix + 1] = ziffer
					else:
						res[ix] = ziffer
					ix += 2
				if treffer == -1:
					res[17] = " noch nicht bekannt"
				else:
					if treffer > 0:
						res[17] = " %d richtige Endziffer(n)" % treffer
					else:
						res[16] = " %d richtige Endziffer(n)" % treffer
			else:
				res[16] = " keine Teilnahme"
		if participation == 1:
			#Spiel77
			res = ["" for x in range(18)]
			res[0] = " Spiel 77: "
			spiel77super6(self.tipp.getActSpiel77(), self.tipp.losnummer(), self.tipp.spiel77treffer)
			list.append(tuple(res))
			# Super6
			res = ["" for x in range(18)]
			res[0] = " Super6: "
			spiel77super6(self.tipp.getActSuper6(), self.tipp.losnummer()[1:], self.tipp.super6treffer)
			list.append(tuple(res))
			for index in range(12):
				spiel = self.tipp.spielv(index)
				treffer = self.tipp.spiel(index).treffer
				if spiel != self.tipp.spiel(index).default:
					res = ["" for x in range(18)]
					res[0] = " Spiel " + str(index + 1) + ":"
					if treffer[0] > 2 or treffer[1] == 1:  # mind 2er+sz
						self.gewinn = True
					if treffer[1] == 0:
						if treffer[0] > 2:
							res[17] = " %d Richtige" % treffer[0]
						else:
							res[16] = " %d Richtige" % treffer[0]
					elif treffer[1] == 1:
						res[17] = " %d Richtige + Superzahl %s" % (treffer[0], self.ziehung.strSuperzahl)
					num = 0
					ix = 0
					for valint in spiel:
						num += 1
						ix += 2
						if num == 7:  # systemtipp mit mehr als 6 getippten Zahlen
							list.append(tuple(res))
							res = ["" for x in range(18)]
							ix = 2
						value = str(valint)
						if value in self.ziehung.strLotto:
							res[ix + 1] = value
						else:
							res[ix] = value
					list.append(tuple(res))
		self.setList(list)
		self.index = 0
		return


class GewinnDetailScreen(Screen):
	def __init__(self, session, tipp, gewinnzahlen, totalsumme):
		self.skin = readSkin("GewinnDetailScreen")
		Screen.__init__(self, session)
		self.session = session
		self.ziehung = gewinnzahlen
		self.tipp = tipp
		self.totalsumme = totalsumme
		self.detaillist = GewinnDetailList(self.tipp, self.ziehung)
		self["spiel77"] = Label(self.ziehung.strSpiel77)
		self["super6"] = Label(self.ziehung.strSuper6)
		if self.ziehung.datum.weekday() == 5:
			tag = "Samstag"
		else:
			tag = "Mittwoch"
		self["auslosung"] = Label(" Auslosung vom %s, %s" % (tag, self.ziehung.datum.strftime("%d. %B %Y")))
		self["displotto"] = Label(" - ".join(list(map(str, self.ziehung.strLotto))))
		self["dispsuper"] = Label(self.ziehung.strSuperzahl)
		self["detaillist"] = self.detaillist
		self["key_green"] = Button("vorheriger Tipp")
		self["key_yellow"] = Button("nächster Tipp")
		self["key_blue"] = Button("zurück")
		entries = lottoTippConfig.getTippCount()
		if entries == 1:
			self["key_green"].text = ""
			self["key_yellow"].text = ""
		elif self.tipp.count == 1:
			self["key_green"].text = ""
		elif self.tipp.count == entries:
			self["key_yellow"].text = ""
		self["statuslabel"] = Label()
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"back": self.close,
			"blue": self.close,
			"yellow": self.nextEntry,
			"green": self.previousEntry,
			"up": self.detaillist.selectPrevious,
			"down": self.detaillist.selectNext,
			"left": self.detaillist.pageUp,
			"right": self.detaillist.pageDown,
			"ok": self.keyNoAction
		}, -1)

		self.onLayoutFinish.append(self.initialBuild)

	def initialBuild(self):
		self.detaillist.buildListbox()
		if self.detaillist.gewinn or self.totalsumme:
			if not self.ziehung.lottoquote:
				self["statuslabel"].setText("Quoten sind noch nicht ermittelt")
			elif self.tipp.gewinnSumme or self.totalsumme:
				self["statuslabel"].setText("Gewinn: %s € / %s € -ohne Gewähr-" % (num2FormStr(self.tipp.gewinnSumme), num2FormStr(self.totalsumme)))
		elif self.tipp.getTeilnahme(self.ziehung.datum.weekday()) != 1:
			self["statuslabel"].setText("Keine Teilnahme an dieser Auslosung")
		else:
			self["statuslabel"].setText("Kein Gewinn")

	def previousEntry(self):
		if self.tipp.count > 1:
			self.close(1)

	def nextEntry(self):
		entries = lottoTippConfig.getTippCount()
		if self.tipp.count < entries:
			self.close(2)

	def keyNoAction(self):
		pass

	def close(self, direction=0):
		Screen.close(self, direction)

#-*- coding: utf-8 -*-
#===============================================================================
# LottoExtended Plugin by apostrophe 2009
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from datetime import date, datetime, timedelta
from json import loads
from re import sub, search
from requests import get, exceptions
from twisted.internet.reactor import callInThread
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Label import Label
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from .LottoTippList import LottoTippListScreen
from .GewinnList import GewinnListScreen, num2FormStr
from .LottoTipp import readSkin

lotto_pluginversion = '16.01.2023'


def str2floatQuotes(strList):
	quotes = []
	for q in strList:
		if q == "unbesetzt" or q == None:
			q = "0"
		elif q == "unbekannt":
			q = "-1"
		else:
			q = sub('\.', '', q)
		quotes.append(sub(',', '.', q))
	quotes.reverse()
	return map(float, quotes)


def date2ymd(date):
	return date.strftime("%Y-%m-%d")


class Ziehung():
	def __init__(self, datum, drawing):
		print("*********drawing:", drawing)
		self.datum = datum
		self.strLotto = list(map(str, drawing["lotto"]))
		self.strSuperzahl = str(drawing["sz"])
		self.strSpiel77 = str(drawing["s77"])
		self.strSuper6 = str(drawing["s6"])
		self.strLottoQuote = list(map(str, drawing["qlotto"]))
		self.strLottoWinners = list(map(str, drawing["wlotto"]))
		self.strS77Winners = list(map(str, drawing["ws77"]))
		self.strS6Winners = list(map(str, drawing["ws6"]))
		self.strLottoE = ""
		self.strSpiel77E = ""
		self.strSuper6E = ""
		if "elotto" in drawing:
			self.strLottoE = str(drawing["elotto"])
		if "es77" in drawing:
			self.strSpiel77E = str(drawing["es77"])
		if "es6" in drawing:
			self.strSuper6E = str(drawing["es6"])
		try:
			x = drawing["s6"]
		except:
			self.strSuper6 = '??????'
		else:
			self.strSuper6 = drawing["s6"]
		try:
			x = drawing["s77"]
		except:
			self.strSpiel77 = '???????'
		else:
			self.strSpiel77 = drawing["s77"]
		self.strS6Quote = ["100.000,00", "6.666,00", "666,00", "66,00", "6,00", "2,50"]
		self.strS77Quote = ["unbekannt", "77.777,00", "7.777,00", "777,00", "77,00", "17,00", "5,00"]
		if self.strLottoQuote == []:
			self.strLottoQuote = None
			self.strLottoWinners = None
			self.strS6Winners = None
			self.strS77Winners = None
			self.lottoquote = None
		else:
			self.lottoquote = str2floatQuotes(self.strLottoQuote)
			self.strS77Quote[0:2] = drawing["qs77"][0:2]
		self.lotto = map(int, self.strLotto)
		self.s77quote = str2floatQuotes(self.strS77Quote)
		self.s6quote = str2floatQuotes(self.strS6Quote)

	def richtigeLotto(self, spiel):
		#print"[Ziehung] richtigeLotto"
		return [i for i in spiel if i in self.lotto]

	def richtigeS6(self, intLosnummer):
		#print"[Ziehung] richtigeS6"
		return len(search('0*$', str(1000000 + int(self.strSuper6) - intLosnummer % 1000000)).group(0))

	def richtigeS77(self, intLosnummer):
		#print"[Ziehung] richtigeS77"
		return len(search('0*$', str(10000000 + int(self.strSpiel77) - intLosnummer)).group(0))

	def richtigeSuperzahl(self, strLosnummer):
		#print"[Ziehung] richtigeSuperzahl"
		return int(strLosnummer[-1:]) == int(self.strSuperzahl)


class Ziehungen():
	def __init__(self):
		#print"[Ziehungen] __init__"
		#self.url= "http://xs/webdav/LottoMai.htm"
		#self.url= "https://info.lotto-brandenburg.de/index.php?id=210" #05.12.2012
		#self.url = "https://www.lotto-brandenburg.de/webapp/app" #getDrawResults"
		self.url = "https://www.lotto-brandenburg.de/app"  # getDrawResults"
		self.drawings = {}
		self.highDate = date(1970, 1, 1)

	def download(self, datum, callback, errback):
		#print"[Ziehungen_download]"#
		if datum == None:
			datum = self.getLastDrawDate()
		if datum in self.drawings:
			callback(datum)
			return
		url = "%s/getDrawResults?gameType=LOTTO&date=%s&useTipHighlighting=false" % (self.url, datum.strftime("%Y-%m-%d"))
		self.zdatum = datum
		self.callback = callback
		self.errback = errback
		callInThread(self.threadGetPage, url, self.downloadOK, self.downloadFailed)

	def threadGetPage(self, link, success, fail=None):
		link = link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', '').encode('utf-8')
		try:
			response = get(link)
			response.raise_for_status()
			success(response.content)
		except exceptions.RequestException as error:
			if fail is not None:
				fail(error)

	def getLastDrawDate(self, not_today=False):
		#print"[Ziehung - getLastDrawDate]"
		today = datetime.today()
		if today.weekday() in (0, 1, 6):  # mo, di, so
			days = (today.weekday() + 7) % 12 % 5
		elif today.weekday() in (3, 4):  # do, fr
			days = (today.weekday() + 5) % 7
		else:
			if not_today == False:
				hhmm = today.hour * 100 + today.minute + 5 - 100 * (today.weekday() == 5)  # 18:35 Mi; 19:35 Sa
				if hhmm > 1835:
					return today.date()
			if today.weekday() == 2:  # Mi
				days = 4
			else:  # Sa
				days = 3
		return today.date() + timedelta(days=-days)

	def parsingFailed(self, datum, errback):
		#print"[Ziehungen_parsingFailed]"
		if errback:
			errback('Fehler beim Parsen der Website', "")

	def downloadFailed(self, output):
		#print"[Ziehungen_downloadfailed]" #, output
		if self.errback:
			self.errback("Fehler beim Aufruf der Website:", output)

	def downloadOK(self, output):
		#print"[Ziehungen_downloadOK] %s" % datum
		if output == "[]" and self.zdatum == date.today():  # neue ziehung noch nicht verf�gbar
			last_date = self.getLastDrawDate(not_today=True)
			self.download(last_date, self.callback, self.errback)
			return
		try:
			data = loads(output)
			returned = {"LOTTO": [0, 0], "GAME_77": [0, 0], "SUPER_6": [0, 0]}
			for lottery in data:
				typ = lottery["gameType"]
				if typ in ("LOTTO", "SUPER_6", "GAME_77"):
					returned[typ][0] = 1
					quotes = []
					winners = []
					einsatz = None
					if lottery["totalStake"] != "None":
						try:
							einsatz = num2FormStr(float(lottery["totalStake"]) / 100)
						except:
							einsatz = None
					if lottery["winningClasses"]:
						returned[typ][1] = 1
						for lvl in lottery["winningClasses"]:
							if lvl['quote'] == "EMPTY":
								quotes.append("unbesetzt")
								winners.append("0")
							else:
								quotes.append(num2FormStr(float(lvl['quote']) / 100))
								winners.append(num2FormStr(float(lvl['winnings'])).split(',')[0])
					else:
						pass
					if typ == "LOTTO":
						lotto = lottery["winningDigits"]
						sz = lottery["superNumber"]
						qlotto = quotes
						wlotto = winners
						elotto = einsatz
					elif typ == "SUPER_6":
						s6 = ''.join(lottery["winningDigits"])
						#qs6 = quotes
						ws6 = winners
						es6 = einsatz
					else:  # "GAME_77":
						s77 = ''.join(lottery["winningDigits"])
						qs77 = quotes
						ws77 = winners
						es77 = einsatz
		except:
			self.parsingFailed(self.zdatum, self.errback)
			return
		for i in returned:  # got results from all lotteries?
			if returned[i][0] == 0:  # no
				if self.zdatum == date.today():  # neue ziehung noch nicht vollständig verfügbar
					last_date = self.getLastDrawDate(not_today=True)
					self.download(last_date, self.callback, self.errback)
					return
				if self.callback:
					self.callback(self.zdatum)
				else:
					return
		for i in returned:  # got results form all lotteries?
			if returned[i][1] == 0:  # did not get all quotes
				ws6 = []
				ws77 = []
				qs77 = []
				qlotto = []
				wlotto = []
				break
		if self.zdatum > self.highDate:  # neue ziehung
			self.highDate = self.zdatum
		drawing = {"lotto": lotto, "s77": s77, "s6": s6, "sz": sz, "qlotto": qlotto, "wlotto": wlotto, "qs77": qs77, "ws77": ws77, "ws6": ws6, "elotto": elotto, "es77": es77, "es6": es6}
		self.drawings[self.zdatum] = Ziehung(self.zdatum, drawing)
		if self.callback:
			self.callback(self.zdatum)


class LottoMain(Screen):
	def __init__(self, session):
		self.skin = readSkin("LottoMain")
		Screen.__init__(self, session)
		self.session = session
		self["quotlist"] = List([])
		self["key_red"] = Button()
		self["key_green"] = Button()
		self["key_yellow"] = Button("Manager")
		self["key_blue"] = Button()
		self["statuslabel"] = Label()
		self["version"] = Label("Version %s" % lotto_pluginversion)
		self["spiel77"] = Label("")
		self["super6"] = Label("")
		self["auslosung"] = Label("")
		self["displotto"] = Label("")
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
			{
				"back": self.close,
				"red": self.prevDraw,
				"green": self.showGewinnList,
				"yellow": self.showTippList,
				"blue": self.nextDraw,
				"cancel": self.close,
				"ok": self.ok,
				"up": self.up,
				"down": self.down,
				"right": self.nextDraw,
				"left": self.prevDraw,
			}, -1)
		self.lowDate = date(2013, 5, 4)
		self.ziehungen = Ziehungen()
		self.retry_auswertung = False
		self.currDate = self.prevDate = self.nextDate = date(1970, 1, 1)
		#self.download(None)
		self.onLayoutFinish.append(self.download)

	def download(self, datum=None):
		#print"[LottoMain download]"
		if datum != None and datum in self.ziehungen.drawings:
			self.dispDraw(datum)
		else:
			self["statuslabel"].setText("Download gestartet")
			self.ziehungen.download(datum, self.downloadOK, self.downloadFailed)

	def downloadFailed(self, text, output):
		#print"[downloadFailed]"
		self.retry_auswertung = False
		self["statuslabel"].setText(text)
		if output:
			try:
				self["details"].setText(str(output))
			except:
				self["details"].setText(text)
				pass
		self.currDate = self.prevDate = self.nextDate = date(1970, 1, 1)
		self["key_blue"].text = ""
		self["key_red"].text = ""
		self["key_green"].text = ""
		self["quotlist"].setList([])

	def downloadOK(self, datum):
		#print"[downloadOK]"
		self.dispDraw(datum)
		self["key_green"].text = "Auswertung"
		if self.retry_auswertung:
			self.retry_auswertung = False
			self.showGewinnList()

	def showGewinnList(self):
		self["statuslabel"].setText("")
		if self.currDate == date(1970, 1, 1):
			self.retry_auswertung = True
			self["statuslabel"].setText("Download ist noch aktiv!")
		else:
			self.session.openWithCallback(self.gewinnlistClosed, GewinnListScreen, self.currDate, self.ziehungen)

	def gewinnlistClosed(self, trueFalse, datum):
		#print"[Lotto] gewinnlistClosed"
		if datum == date(1970, 1, 1):
			self.currDate = self.prevDate = self.nextDate = date(1970, 1, 1)
			self["key_blue"].text = ""
			self["key_red"].text = ""
			self["key_green"].text = ""
			self["statuslabel"].setText("Fehler in der Verarbeitung")
		elif datum != self.currDate:
			self.dispDraw(datum)

	def showTippList(self):
		self["statuslabel"].setText("")
		self.retry_auswertung = False
		self.session.openWithCallback(self.tipplistClosed, LottoTippListScreen)

	def tipplistClosed(self, trueFalse):
		#print"[Lotto] tipplistClosed"
		pass

	def down(self):
		self["quotlist"].selectNext()

	def up(self):
		self["quotlist"].selectPrevious()

	def ok(self):
		if self.currDate == self.ziehungen.highDate:
			return
		self.retry_auswertung = False
		self.download(self.ziehungen.highDate)

	def prevDraw(self):
		self.retry_auswertung = False
		if self.currDate == self.prevDate:
			return
		self.download(self.prevDate)

	def nextDraw(self):
		self.retry_auswertung = False
		if self.currDate == self.nextDate:
			return
		self.download(self.nextDate)

	def dispDraw(self, datum):
		#print"[dispDraw]"
		self.currDate = datum
		self.setDates()
		ziehung = self.ziehungen.drawings[self.currDate]
		if ziehung.datum.weekday() == 5:
			tag = "Samstag"
		else:
			tag = "Mittwoch"
		if self.currDate.weekday() == 5:
			tag = 'Sa'
		else:
			tag = 'Mi'
		self["auslosung"].text = " Auslosung vom %s, %s" % (tag, ziehung.datum.strftime("%d. %B %Y"))
		self["spiel77"].text = "  ".join(ziehung.strSpiel77)
		self["super6"].text = "  ".join(ziehung.strSuper6)
		self["displotto"].text = " - ".join(ziehung.strLotto) + ' / ' + ziehung.strSuperzahl
		xlist = []
		list = ["" for i in range(11)]
		if ziehung.strLottoQuote == None:
			self["statuslabel"].setText("Ziehung vom %s, %s - Die Gewinnquoten stehen noch nicht fest." % (tag, self.currDate.strftime("%d.%m.%Y")))
			xlist.append(tuple(list))
			self["quotlist"].index = 0
		else:
			for i in range(9):
				j = str(i + 1)
				list[0] = j
				list[1] = ziehung.strLottoWinners[i]
				list[2] = "%s €" % ziehung.strLottoQuote[i]
				if i < 7:
					list[3] = ziehung.strS77Winners[i]
					list[4] = "%s €" % ziehung.strS77Quote[i]
				if i < 6:
					list[5] = ziehung.strS6Winners[i]
					list[6] = "%s €" % ziehung.strS6Quote[i]
				xlist.append(tuple(list))
				list = ["" for i in range(11)]
			list[0] = "Einsatz:"
			if ziehung.strLotto:
				list[7] = "%s €" % ziehung.strLottoE
			if ziehung.strSpiel77:
				list[8] = "%s €" % ziehung.strSpiel77E
			if ziehung.strSuper6:
				list[9] = "%s €" % ziehung.strSuper6E
			xlist.append(tuple(list))
			self["statuslabel"].setText("Ziehung vom %s, %s" % (tag, self.currDate.strftime("%d.%m.%Y")))
		self["quotlist"].setList(xlist)

	def setDates(self):
		#print"[setDates]"
		if self.currDate.weekday() == 5:  # Saturday
			nxt = 4
			prv = -3
		else:
			nxt = 3
			prv = -4
		self.nextDate = min(self.ziehungen.highDate, self.currDate + timedelta(days=nxt))
		self.prevDate = max(self.currDate + timedelta(days=prv), self.lowDate)
		if self.nextDate == self.currDate:
			self["key_blue"].text = ""
		else:
			self["key_blue"].text = self.nextDate.strftime(_("%d.%m.%Y"))
		if self.prevDate == self.currDate:
			self["key_red"].text = ""
		else:
			self["key_red"].text = self.prevDate.strftime(_("%d.%m.%Y"))


def main(session, **kwargs):
	session.open(LottoMain)


def Plugins(**kwargs):
	return PluginDescriptor(
		name="LottoExtended", description=_("Tippscheinmanager, Gewinnauswertung, Gewinnzahlen, Quoten"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main)

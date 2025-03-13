# -*- coding: utf-8 -*-
#===============================================================================
# LottoExtended Plugin by apostrophe 2009
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Sources.List import List
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from .LottoTippConfig import lottoTippConfig
from .LottoTippConfig import LottoTippConfigScreen
from .LottoTipp import readSkin


class LottoTippList(List):
	def __init__(self):
		List.__init__(self, [])

	def update(self, tippList):
		list = []
		for tipp in tippList:
			list.append((tipp, tipp.getName(), tipp.getFirstDrawFormat(), tipp.getLastDrawFormat(), tipp.getZiehungTag(), tipp.getSpiel77JaNein(), tipp.getSuper6JaNein()))
		self.setList(list)
		self.index = 0


class LottoTippListScreen(Screen):
	def __init__(self, session):
		self.skin = readSkin("LottoTippListScreen")
		Screen.__init__(self, session)
		self.session = session
		self.tipplist = LottoTippList()
		self["tipplist"] = self.tipplist
		self["tipptitle"] = Label("Tippschein")
		self["datetitle"] = Label("erste  -  Ziehung  -  letzte")
		self["ziehungtitle"] = Label("Teilnahme")
		self["spiel77title"] = Label("Spiel77")
		self["super6title"] = Label("Super6")
		self["key_red"] = Button("Tipp löschen")
		self["key_green"] = Button("Tipp hinzufügen")
		self["key_yellow"] = Button("Tipp bearbeiten")
		self["key_blue"] = Button("zurück")
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"back": self.close,
			"red": self.keyDelete,
			"green": self.keyAddTipp,
			"yellow": self.keyEditTipp,
			"blue": self.close,
			"up": self.tipplist.selectPrevious,
			"down": self.tipplist.selectNext,
			"left": self.tipplist.pageUp,
			"right": self.tipplist.pageDown,
			"ok": self.keyEditTipp
		}, -1)
		self.onLayoutFinish.append(self.updateTipplist)

	def updateTipplist(self):
		self.tipplist.update(lottoTippConfig.getTipplist())

	def keyNoAction(self):
		pass

	def keyAddTipp(self):
		newTipp = lottoTippConfig.new()
		self.session.openWithCallback(self.addCallback, LottoTippConfigScreen, newTipp)

	def addCallback(self, result, tipp):
		if result:
			lottoTippConfig.save(tipp)
			self.updateTipplist()
		else:
			lottoTippConfig.delete(tipp)

	def keyDelete(self):
		if self.tipplist.current:
			tipp = self.tipplist.current[0]
			self.session.openWithCallback(self.deleteCallback, MessageBox, ("Soll '%s' wirklich gelöscht werden?" % tipp.getName()))

	def deleteCallback(self, result):
		index = self.tipplist.index
		if result:
			tipp = self.tipplist.current[0]
			lottoTippConfig.delete(tipp)
			self.updateTipplist()
			index -= 1
		if index >= 0:
			self.tipplist.index = index

	def keyEditTipp(self):
		if self.tipplist.current:
			tipp = self.tipplist.current[0]
			self.session.openWithCallback(self.editCallback, LottoTippConfigScreen, tipp)

	def editCallback(self, result, tipp):
		index = self.tipplist.index
		if result:
			tipp = self.tipplist.current[0]
			lottoTippConfig.save(tipp)
			self.updateTipplist()
		else:
			lottoTippConfig.cancel(tipp)
		self.tipplist.index = index

	def close(self):
		Screen.close(self, True)

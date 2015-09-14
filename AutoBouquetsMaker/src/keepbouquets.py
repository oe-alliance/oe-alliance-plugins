# -*- coding: utf-8 -*-
# for localized messages
from . import _

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import getConfigListEntry, config, configfile
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.Button import Button
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	pass

from scanner.manager import Manager

from urlparse import urlparse

class AutoBouquetsMaker_KeepBouquets(Screen):
	skin = """
		<screen position="center,center" size="600,500">
			<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#9f1313" font="Regular;18" transparent="1"/>
			<widget name="key_green" position="150,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#1f771f" font="Regular;18" transparent="1"/>
			<ePixmap name="red" position="0,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
			<ePixmap name="green" position="150,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
			<widget source="list" render="Listbox" position="10,50" size="580,450" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryPixmapAlphaTest(pos = (10, 0), size = (32, 32), png = 0),
						MultiContentEntryText(pos = (47, 0), size = (400, 30), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
						MultiContentEntryText(pos = (450, 0), size = (120, 30), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 2),
						],
						"fonts": [gFont("Regular", 22)],
						"itemHeight": 30
					}
				</convert>
			</widget>
		</screen>"""

	ABM_BOUQUET_PREFIX = "userbouquet.abm."
		
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		Screen.setTitle(self, _("AutoBouquetsMaker Keep bouquets"))
		self.startlist = config.autobouquetsmaker.keepbouquets.getValue()
		self.drawList = []

		self["list"] = List(self.drawList)
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button("Save")
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
				{
					"red": self.keyCancel,
					"green": self.keySave,
					"ok": self.ok,
					"cancel": self.keyCancel,
				}, -2)

		self.refresh()

	def buildListEntry(self, enabled, name, type):
		if enabled:
			try:
				pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "icons/lock_on.png"))
			except:
				pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_on.png"))
		else:
			try:
				pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "icons/lock_off.png"))
			except:
				pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_off.png"))

		return((pixmap, name, type))

	def refresh(self):
		bouquets = Manager().getBouquetsList()
		self.listTv = bouquets["tv"]
		self.listRadio = bouquets["radio"]
		self.drawList = []
		self.listAll = []
		self.bouquets = config.autobouquetsmaker.keepbouquets.value.split("|")

		if self.listTv is not None and self.listRadio is not None:
			for bouquet in self.listTv:
				if bouquet["filename"][:12] == "autobouquet." or bouquet["filename"][:len(self.ABM_BOUQUET_PREFIX)] == self.ABM_BOUQUET_PREFIX:
					continue
				if bouquet["filename"] in self.bouquets:
					self.drawList.append(self.buildListEntry(True, bouquet["name"], "TV"))
				else:
					self.drawList.append(self.buildListEntry(False, bouquet["name"], "TV"))
				self.listAll.append(bouquet["filename"])

			for bouquet in self.listRadio:
				if bouquet["filename"][:12] == "autobouquet." or bouquet["filename"][:len(self.ABM_BOUQUET_PREFIX)] == self.ABM_BOUQUET_PREFIX:
					continue
				if bouquet["filename"] in self.bouquets:
					self.drawList.append(self.buildListEntry(True, bouquet["name"], "Radio"))
				else:
					self.drawList.append(self.buildListEntry(False, bouquet["name"], "Radio"))
				self.listAll.append(bouquet["filename"])
		self["list"].setList(self.drawList)

	def ok(self):
		if len(self.listAll) == 0:
			return
		index = self["list"].getIndex()
		if self.listAll[index] in self.bouquets:
			self.bouquets.remove(self.listAll[index])
		else:
			self.bouquets.append(self.listAll[index])
		config.autobouquetsmaker.keepbouquets.value = "|".join(self.bouquets)
		self.refresh()
		self["list"].setIndex(index)

	# keySave and keyCancel are just provided in case you need them.
	# you have to call them by yourself.
	def keySave(self):
		config.autobouquetsmaker.keepbouquets.save()
		configfile.save()
		self.close()

	def cancelConfirm(self, result):
		if not result:
			return
		config.autobouquetsmaker.hidesections.cancel()
		self.close()

	def keyCancel(self):
		if self.startlist != config.autobouquetsmaker.keepbouquets.getValue():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

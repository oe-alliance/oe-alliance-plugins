import os
from enigma import eDVBDB
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
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

class AutoBouquetsMaker_DeleteBouquets(Screen):
	skin = """
		<screen position="center,center" size="600,500">
			<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#9f1313" font="Regular;18" transparent="1"/>
			<widget name="key_green" position="150,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#1f771f" font="Regular;18" transparent="1"/>
			<widget name="key_yellow" position="300,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="888800" font="Regular;18" transparent="1"/>
			<widget name="key_blue" position="450,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#000099" font="Regular;18" transparent="1"/>
			<ePixmap name="red" position="0,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
			<ePixmap name="green" position="150,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
			<ePixmap name="yellow" position="300,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
			<ePixmap name="blue" position="450,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
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
		Screen.setTitle(self, _("AutoBouquetsMaker Delete bouquets"))
		self.startlist = []
		self.drawList = []
		self.options = [_('ABM only'), _('User only'), _('All'), _('None')]
		self.type = self.options[3]
		self["list"] = List(self.drawList)
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button("Delete")
		self["key_yellow"] = Button(self.options[0])
		self["key_blue"] = Button(self.options[2])
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
				{
					"red": self.keyCancel,
					"green": self.keyDelete,
					"yellow": self.keyYellow,
					"blue": self.keyBlue,
					"ok": self.ok,
					"cancel": self.keyCancel,
				}, -2)
		self.bouquetsToDelete = []
		self.path = Manager().getPath()
		self.bouquetsInIndex = Manager().getBouquetsList()
		if "tv" not in self.bouquetsInIndex:
			self.bouquetsInIndex["tv"] = []
		if "radio" not in self.bouquetsInIndex:
			self.bouquetsInIndex["radio"] = []
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
		bouquets = self.bouquetsInIndex
		self.listTv = bouquets["tv"]
		self.listRadio = bouquets["radio"]
		self.drawList = []
		self.listAll = []

		if self.listTv is not None and self.listRadio is not None:
			for bouquet in self.listTv:
				if bouquet["filename"] in self.bouquetsToDelete:
					self.drawList.append(self.buildListEntry(True, bouquet["name"], "TV"))
				else:
					self.drawList.append(self.buildListEntry(False, bouquet["name"], "TV"))
				self.listAll.append(bouquet["filename"])

			for bouquet in self.listRadio:
				if bouquet["filename"] in self.bouquetsToDelete:
					self.drawList.append(self.buildListEntry(True, bouquet["name"], "Radio"))
				else:
					self.drawList.append(self.buildListEntry(False, bouquet["name"], "Radio"))
				self.listAll.append(bouquet["filename"])
		self["list"].setList(self.drawList)

	def ok(self):
		if len(self.listAll) == 0:
			return
		index = self["list"].getIndex()
		if self.listAll[index] in self.bouquetsToDelete:
			self.bouquetsToDelete.remove(self.listAll[index])
		else:
			self.bouquetsToDelete.append(self.listAll[index])
		self.refresh()
		self["list"].setIndex(index)

	def delete(self, result):
		if not result:
			return
		print "self.listAll", self.listAll
		print "self.bouquetsToDelete", self.bouquetsToDelete
		
		bouquetsToSave = [item for item in self.listAll if item not in self.bouquetsToDelete]
		
		for bouquet_type in ["tv", "radio"]:
			toSave = ''
			bouquetsIn = open(self.path + "/bouquets." + bouquet_type, "r")
			content = bouquetsIn.read().strip().split("\n")
			bouquetsIn.close()
			for line in content:
				for filename in bouquetsToSave:
					if filename in line:
						toSave += line + "\n"
						break
			bouquetsOut = open(self.path + "/bouquets." + bouquet_type, "w")
			bouquetsOut.write(toSave)
			bouquetsOut.close()
		
		for filename in self.bouquetsToDelete:
			try:
				os.remove(self.path + "/" + filename)
			except Exception, e:
				print>>log, "[Delete bouquets] Cannot delete %s: %s" % (filename, e)
		
		eDVBDB.getInstance().reloadServicelist()
		eDVBDB.getInstance().reloadBouquets()
		self.close()

	def keyDelete(self):
		self.session.openWithCallback(self.delete, MessageBox, _("Are you sure you want to permanently remove these bouquets? Hiding them might be a better option."))

	def cancelConfirm(self, result):
		if not result:
			return
		self.close()

	def keyCancel(self):
		if self.startlist != self.bouquetsToDelete:
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Close without saving these changes?"))
		else:
			self.close()

	def keyYellow(self):
		self.bouquetsToDelete = []
		self.options[0] == self["key_yellow"].getText()
		for filename in self.listAll:
			if (filename[:len(self.ABM_BOUQUET_PREFIX)] == self.ABM_BOUQUET_PREFIX) == (self.options[0] == self["key_yellow"].getText()):
				self.bouquetsToDelete.append(filename)
		self["key_yellow"].setText(self.options[1] if self.options[0] == self["key_yellow"].getText() else self.options[0])
		self.refresh()

	def keyBlue(self):
		self.bouquetsToDelete = []
		if self.options[2] == self["key_blue"].getText():
			self.bouquetsToDelete = self.listAll
		self["key_blue"].setText(self.options[3] if self["key_blue"].getText() == self.options[2] else self.options[2])
		self.refresh()
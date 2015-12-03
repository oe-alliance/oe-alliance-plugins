# for localized messages
from . import _

from scanner.main import AutoBouquetsMaker, AutoAutoBouquetsMakerTimer
from scanner.manager import Manager
from about import AutoBouquetsMaker_About
from setup import AutoBouquetsMaker_Setup, AutoBouquetsMaker_ProvidersSetup
from hidesections import AutoBouquetsMaker_HideSections
from keepbouquets import AutoBouquetsMaker_KeepBouquets
from ordering import AutoBouquetsMaker_Ordering
from deletebouquets import AutoBouquetsMaker_DeleteBouquets, AutoBouquetsMaker_DeleteMsg

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	pass
from Tools.LoadPixmap import LoadPixmap

from time import localtime, time, strftime
import os, sys, log

class AutoBouquetsMaker_Menu(Screen):
	skin = """
<screen position="center,center" size="560,360">
	<widget source="list" render="Listbox" position="0,0" size="560,360" scrollbarMode="showOnDemand">
		<convert type="TemplatedMultiContent">
			{"template": [
				MultiContentEntryPixmapAlphaTest(pos = (12, 4), size = (32, 32), png = 0),
				MultiContentEntryText(pos = (58, 5), size = (440, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
				],
				"fonts": [gFont("Regular", 22)],
				"itemHeight": 40
			}
		</convert>
	</widget>
</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("AutoBouquetsMaker")
		Screen.setTitle(self, self.setup_title)
		self.init_providers = config.autobouquetsmaker.providers.getValue()
		self.init_keepallbouquets = config.autobouquetsmaker.keepallbouquets.getValue()
		self.init_schedule = config.autobouquetsmaker.schedule.getValue()
		self.init_scheduletime = config.autobouquetsmaker.scheduletime.getValue()
		print 'self.init_schedule',self.init_schedule
		print 'self.init_scheduletime',self.init_scheduletime

		self.onChangedEntry = [ ]
		l = []

		self["list"] = List(l)

		self["setupActions"] = ActionMap(["SetupActions", "MenuActions"],
		{
			"cancel": self.quit,
			"ok": self.openSelected,
			"menu": self.quit,
		}, -2)

		self.createsetup()
		if len(config.autobouquetsmaker.providers.value) < 1:
			self.onFirstExecBegin.append(self.openSetup)

	def createsetup(self):
		l = []
		l.append(self.buildListEntry(_("Configure"), "configure.png"))
		l.append(self.buildListEntry(_("Providers"), "opentv.png"))
		if len(config.autobouquetsmaker.providers.getValue().split('|')) > 1:
			l.append(self.buildListEntry(_("Providers order"), "reorder.png"))
		if len(config.autobouquetsmaker.providers.getValue().split('|')) > 0:
			l.append(self.buildListEntry(_("Hide sections"), "reorder.png"))
		if not config.autobouquetsmaker.keepallbouquets.value:
			l.append(self.buildListEntry(_("Keep bouquets"), "reorder.png"))
		l.append(self.buildListEntry(_("Start scan"), "download.png"))
		l.append(self.buildListEntry(_("Delete bouquets"), "reorder.png"))
		l.append(self.buildListEntry(_("Show log"), "dbinfo.png"))
		l.append(self.buildListEntry(_("About"), "about.png"))
		self["list"].list = l

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return str(self["list"].getCurrent()[1])

	def getCurrentValue(self):
		return ""

	def createSummary(self):
		return AutoBouquetsMaker_MenuSummary

	def buildListEntry(self, description, image):
		try:
			pixmap = LoadPixmap(resolveFilename(SCOPE_ACTIVE_SKIN, "autobouquetsmaker/" + image))
		except:
			pixmap = None
		if pixmap == None:
			pixmap = LoadPixmap(cached=True, path="%s/images/%s" % (os.path.dirname(sys.modules[__name__].__file__), image));
		return((pixmap, description))

	def openSetup(self):
		self.session.open(AutoBouquetsMaker_Setup)

	def refresh(self):
		AutoAutoBouquetsMakerTimer.instance.doneConfiguring()
		if self.init_providers != config.autobouquetsmaker.providers.getValue() or self.init_keepallbouquets != config.autobouquetsmaker.keepallbouquets.getValue():
			self.init_providers = config.autobouquetsmaker.providers.getValue()
			self.init_keepallbouquets = config.autobouquetsmaker.keepallbouquets.getValue()
			index = self["list"].getIndex()
			self.createsetup()
			if index is not None and len(self["list"].list) > index:
				self["list"].setIndex(index)
			else:
				self["list"].setIndex(0)

	def openSelected(self):

		index = self["list"].getIndex()

		if index == 0:
			self.session.openWithCallback(self.refresh, AutoBouquetsMaker_Setup)
			return

		if index == 1:
			self.session.openWithCallback(self.refresh, AutoBouquetsMaker_ProvidersSetup)
			return

		if len(config.autobouquetsmaker.providers.getValue().split('|')) < 2:	# menu "ordering" not showed
			index += 1

		if index == 2:
			self.session.open(AutoBouquetsMaker_Ordering)
			return

		if len(config.autobouquetsmaker.providers.getValue().split('|')) < 1:	# menu "hie sections" not showed
			index += 1

		if index == 3:
			self.session.open(AutoBouquetsMaker_HideSections)
			return

		if config.autobouquetsmaker.keepallbouquets.value:	# menu "keep bouquets" not showed
			index += 1

		if index == 4:
			self.session.open(AutoBouquetsMaker_KeepBouquets)
			return

		if index == 5:
			self.session.open(AutoBouquetsMaker)
			return

		if index == 6:
			self.session.openWithCallback(AutoBouquetsMaker_DeleteBouquets, AutoBouquetsMaker_DeleteMsg)
			return

		if index == 7:
			self.session.open(AutoBouquetsMaker_Log)
			return

		if index == 8:
			self.session.open(AutoBouquetsMaker_About)
			return

	def quit(self):
		self.close()

class AutoBouquetsMaker_MenuSummary(Screen):
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent = parent)
		self["SetupTitle"] = StaticText(_(parent.setup_title))
		self["SetupEntry"] = StaticText("")
		self["SetupValue"] = StaticText("")
		self.onShow.append(self.addWatcher)
		self.onHide.append(self.removeWatcher)

	def addWatcher(self):
		self.parent.onChangedEntry.append(self.selectionChanged)
		self.parent["list"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)
		self.parent["list"].onSelectionChanged.remove(self.selectionChanged)

	def selectionChanged(self):
		self["SetupEntry"].text = self.parent.getCurrentEntry()
		self["SetupValue"].text = self.parent.getCurrentValue()

class AutoBouquetsMaker_Log(Screen):
	skin = """
<screen name="AutoBouquetsMakerLogView" position="center,center" size="600,500" title="Backup Log">
	<widget name="list" position="0,0" size="600,500" font="Regular;16"/>
	<widget name="key_yellow" position="0,310" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
	<ePixmap name="yellow" pixmap="skin_default/buttons/yellow.png" position="0,310" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
</screen>"""
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		Screen.setTitle(self, _("AutoBouquetsMaker Log"))
		self["list"] = ScrollLabel(log.getvalue())
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions", "MenuActions"],
		{
			"cancel": self.cancel,
			"ok": self.cancel,
			"up": self["list"].pageUp,
			"down": self["list"].pageDown,
			"menu": self.closeRecursive,
			"yellow": self.save,
		}, -2)

		self["key_yellow"] = Button(_("Save Log"))
		self["key_red"] = Button(_("Close"))		

	def save(self):
		output = open('/tmp/abm.log', 'w')
		output.write(log.getvalue())
		output.close()
		self.session.open(MessageBox,_("Log now saved to /tmp/abm.log"),MessageBox.TYPE_INFO, timeout = 5)

	def cancel(self):
		self.close()

	def closeRecursive(self):
		self.close(True)

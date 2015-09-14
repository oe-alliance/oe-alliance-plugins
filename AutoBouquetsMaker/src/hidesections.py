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
from scanner.providerconfig import ProviderConfig

from urlparse import urlparse

class AutoBouquetsMaker_HideSections(Screen):
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

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		Screen.setTitle(self, _("AutoBouquetsMaker Hide sections"))
		self.startlist = config.autobouquetsmaker.hidesections.getValue()
		self.drawList = []

		self["list"] = List(self.drawList)
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
				{
					"red": self.keyCancel,
					"green": self.keySave,
					"ok": self.ok,
					"cancel": self.keyCancel,
				}, -2)

		self.providers = Manager().getProviders()
		self.providers_enabled = []
		providers_tmp = config.autobouquetsmaker.providers.value.split("|")
		for provider_tmp in providers_tmp:
			provider_config = ProviderConfig(provider_tmp)
			
			if not provider_config.isValid():
				continue
				
			if provider_config.getProvider() not in self.providers:
				continue
				
			self.providers_enabled.append(provider_config.getProvider())

		self.housekeeping()	
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

		return((pixmap, str(name), str(type)))

	def refresh(self):
		self.providers_selected = config.autobouquetsmaker.hidesections.value.split("|")
		self.drawList = []
		self.listAll = []
		
		for provider in self.providers_enabled:
			for section in sorted(self.providers[provider]["sections"].keys()):
				key = provider + ":" + str(section)
				self.listAll.append(key)
				self.drawList.append(self.buildListEntry(key in self.providers_selected, self.providers[provider]["sections"][section], self.providers[provider]["name"]))

		self["list"].setList(self.drawList)

	def ok(self):
		if len(self.listAll) == 0:
			return
		index = self["list"].getIndex()

		if self.listAll[index] in self.providers_selected:
			self.providers_selected.remove(self.listAll[index])
		else:
			self.providers_selected.append(self.listAll[index])
		config.autobouquetsmaker.hidesections.value = "|".join(self.providers_selected)
		self.refresh()
		self["list"].setIndex(index)

	# keySave and keyCancel are just provided in case you need them.
	# you have to call them by yourself.
	def keySave(self):
		config.autobouquetsmaker.hidesections.save()
		configfile.save()
		self.close()

	def cancelConfirm(self, result):
		if not result:
			return
		config.autobouquetsmaker.hidesections.cancel()
		self.close()

	def keyCancel(self):
		if self.startlist != config.autobouquetsmaker.hidesections.getValue():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()
			
	def housekeeping(self):
		# remove non-existent hidden sections, due to changes in the provider file
		hidden_sections = config.autobouquetsmaker.hidesections.value.split("|")
		new_hidden_sections = []
		for provider in self.providers_enabled:
			for section in sorted(self.providers[provider]["sections"].keys()):
				key = provider + ":" + str(section)
				if key in hidden_sections:
					new_hidden_sections.append(key)
		config.autobouquetsmaker.hidesections.value = "|".join(new_hidden_sections)

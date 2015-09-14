# -*- coding: utf-8 -*-
# for localized messages
from . import _

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import getConfigListEntry, config, configfile
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from enigma import eTimer

from scanner.manager import Manager
from scanner.providerconfig import ProviderConfig

class AutoBouquetsMaker_Ordering(Screen):
	skin = """
		<screen position="center,center" size="600,500">
			<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#9f1313" font="Regular;18" transparent="1"/>
			<widget name="key_green" position="150,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#1f771f" font="Regular;18" transparent="1"/>
			<widget name="key_yellow" position="300,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#a08500" font="Regular;18" transparent="1"/>
			<widget name="key_blue" position="450,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" backgroundColor="#18188b" font="Regular;18" transparent="1"/>
			<ePixmap name="red" position="0,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
			<ePixmap name="green" position="150,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
			<ePixmap name="yellow" position="300,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
			<ePixmap name="blue" position="450,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
			<widget source="list" render="Listbox" position="20,50" size="560,360" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryText(pos = (12, 1), size = (440, 32), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
						],
						"fonts": [gFont("Regular", 22)],
						"itemHeight": 30
					}
				</convert>
			</widget>
			<widget name="pleasewait" position="10,60" size="580,140" font="Regular;18" halign="center" valign="center" transparent="0" zPosition="1"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("Bouquets order")
		Screen.setTitle(self, self.setup_title)

		self.providers_order = config.autobouquetsmaker.providers.value.split("|")
		self.has_changed = False

		self.onChangedEntry = [ ]
		self.list = []
		self["list"] = List(self.list)
		self["list"].onSelectionChanged.append(self.selectionChanged)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button("Save")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.moveUp,
			"blue": self.moveDown,
			"menu": self.keyCancel,
		}, -2)

		self["pleasewait"] = Label()

		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.prepare)

		self.onLayoutFinish.append(self.populate)

	def populate(self):
		self["actions"].setEnabled(False)
		self["pleasewait"].setText(_("Please wait..."))
		self.activityTimer.start(1)

	def prepare(self):
		self.activityTimer.stop()
		self.providers = Manager().getProviders()
		self.buildList()

		if len(self.list) <= 1:
			return

		index = self["list"].getIndex()
		if index == 0:
			self["key_yellow"].setText("")
			self["key_blue"].setText(_("Move down"))
		elif index == len(self.list) - 1:
			self["key_yellow"].setText(_("Move up"))
			self["key_blue"].setText("")
		else:
			self["key_yellow"].setText(_("Move up"))
			self["key_blue"].setText(_("Move down"))

	def buildList(self):
		self.list = []
		self.providers_configs = {}
		for tmp in self.providers_order:
			provider_config = ProviderConfig(tmp)
			
			if not provider_config.isValid():
				continue
				
			if provider_config.getProvider() not in self.providers:
				continue
				
			providers = (str(self.providers[provider_config.getProvider()]["name"]), provider_config.getProvider())
			self.list.append(providers)
			self.providers_configs[provider_config.getProvider()] = provider_config
			
		self["list"].setList(self.list)
		self["pleasewait"].hide()
		self["actions"].setEnabled(True)

	def selectionChanged(self):
		if len(self.list) <= 1:
			return

		index = self["list"].getIndex()
		if index == 0:
			self["key_yellow"].setText("")
			self["key_blue"].setText(_("Move down"))
		elif index == len(self.list) - 1:
			self["key_yellow"].setText(_("Move up"))
			self["key_blue"].setText("")
		else:
			self["key_yellow"].setText(_("Move up"))
			self["key_blue"].setText(_("Move down"))

	def moveUp(self):
		if len(self.list) <= 1:
			return

		self.has_changed = True

		index = self["list"].getIndex()
		if index > 0:
			tmp = self.providers_order[index - 1]
			self.providers_order[index - 1] = self.providers_order[index]
			self.providers_order[index] = tmp

			self.buildList()
			self["list"].setIndex(index - 1)

	def moveDown(self):
		if len(self.list) <= 1:
			return

		self.has_changed = True

		index = self["list"].getIndex()
		if index < len(self.list) - 1:
			tmp = self.providers_order[index + 1]
			self.providers_order[index + 1] = self.providers_order[index]
			self.providers_order[index] = tmp

			self.buildList()
			self["list"].setIndex(index + 1)

	def cancelConfirm(self, result):
		if not result:
			return
		self.close()

	def keyCancel(self):
		if self.has_changed :
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def keySave(self):
		config_string = ""
		for provider in self.list:
			provider = provider[1]
			if len(config_string) > 0:
				config_string += "|"
				
			config_string += self.providers_configs[provider].serialize()
			
		config.autobouquetsmaker.providers.setValue(config_string)
		config.autobouquetsmaker.providers.save()
		configfile.save()
		self.close()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		if self["list"].getCurrent():
			return str(self["list"].getCurrent()[0])
		else:
			return ""

	def getCurrentValue(self):
		return ""

	def createSummary(self):
		from menu import AutoBouquetsMaker_MenuSummary
		return AutoBouquetsMaker_MenuSummary


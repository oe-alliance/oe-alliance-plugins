# for localized messages
from . import _

import urllib2

from Components.ActionMap import ActionMap
from Components.config import ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop

class xmlUpdate(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("XML update")
		Screen.setTitle(self, self.setup_title)
		self.skinName = ["xmlUpdate", "Setup"]
		self.session = session
		ConfigListScreen.__init__(self, [], session=session)

		self.url = "https://raw.githubusercontent.com/oe-alliance/oe-alliance-tuxbox-common/master/src/%s.xml"
		self.source = ConfigSelection(default="OE-Alliance", choices=[("OE-Alliance", _("OE-Alliance"))])
		self.DVBtype = ConfigSelection(default="satellites", choices=[("satellites", _("satellite")), ("cables", _("cable")), ("terrestrial", _("terrestrial"))])
		self.folder = ConfigSelection(default="/etc/tuxbox", choices=[("/etc/tuxbox", _("/etc/tuxbox (default)")), ("/etc/enigma2", _("/etc/enigma2"))])
		
		self["actions"] = ActionMap(["SetupActions"],
		{
			"cancel": self.keyCancel,
			"save": self.keyGo,
		}, -2)

		self["actions2"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"menu": self.keyCancel,
		}, 2)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Fetch"))

		self["description"] = Label("")
		
		self.createSetup()

		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def selectionChanged(self):
		self["description"].setText(self.getCurrentDescription())

	def createSetup(self):
		self.list = []

		self.list.append(getConfigListEntry(_("Source"), self.source, _('Online source where the transponder xml file is being retrieved from.')))
		self.list.append(getConfigListEntry(_("Fetch"), self.DVBtype, _('File being updated, i.e. satellites.xml, cables.xml, or terrestrial.xml.')))
		self.list.append(getConfigListEntry(_("Save to"), self.folder, _('Folder where the downloaded file will be saved. "/etc/tuxbox" is the default location. Files stored in "/etc/enigma2" override the default file and are not updated on a software update.')))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyGo(self):
		XMLdata = self.fetchURL()
		if XMLdata:
			if self.validXML(XMLdata):
				try:
					with open(self.folder.value + "/" + self.DVBtype.value + ".xml", "w") as f:
						f.write(XMLdata)
						f.close()
				except IOError, err:
					print "[xmlUpdate][keyGo] Saving file failed.", err
					self.showError(_("Saving the %s.xml file failed") % self.DVBtype.value)
				else:
					print "[xmlUpdate][keyGo] Saving file succeeded."
					self.showRestartMessage(_("Fetching and saving %s.xml succeeded.\nRestart now for changes to take immediate effect?") % self.DVBtype.value)
			else: # XML did not validate
				print "[xmlUpdate][validXML] Closing documentElement missing."
				self.showError(_("The %s.xml download was corrupt.") % self.DVBtype.value)

	def keyCancel(self):
		self.close()

	def fetchURL(self):
		try:
			print '[xmlUpdate][fetchURL] URL', self.url % self.DVBtype.value
			req = urllib2.Request(self.url % self.DVBtype.value)
			response = urllib2.urlopen(req)
			print '[xmlUpdate][fetchURL] Response: %d' % response.getcode()
			if int(response.getcode()) == 200:
				return response.read()
		except urllib2.HTTPError, err:
			print '[xmlUpdate][fetchURL] ERROR:', err
		except urllib2.URLError, err:
			print '[xmlUpdate][fetchURL] ERROR:', err.reason[0]
		except urllib2, err:
			print '[xmlUpdate][fetchURL] ERROR:', err
		except:
			import sys
			print '[xmlUpdate][fetchURL] undefined error', sys.exc_info()[0]
		self.showError(_("The %s.xml file could not be fetched") % self.DVBtype.value)

	def validXML(self, XMLdata): # Looks for closing documentElement, i.e. </satellites>, </cables>, or </locations>
		return self.DVBtype.value in ('satellites', 'cables') and ("</%s>" % self.DVBtype.value) in XMLdata or self.DVBtype.value == "terrestrial" and "</locations>" in XMLdata

	def showError(self, message):
		mbox = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
		mbox.setTitle(_("XML update"))

	def showRestartMessage(self, message):
		mbox = self.session.openWithCallback(self.restartGUI, MessageBox, message, MessageBox.TYPE_YESNO)
		mbox.setTitle(_("XML update"))

	def restartGUI(self, answer=None):
		if answer:
			self.session.open(TryQuitMainloop, 3)

def xmlUpdateStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("XML update"), xmlUpdateMain, "xmlUpdate", 70)]
	return []

def xmlUpdateMain(session, **kwargs):
	session.open(xmlUpdate)

def Plugins(**kwargs):
	pList = []
	pList.append(PluginDescriptor(name=_("XML update"), description="For undating transponder xml files", where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=xmlUpdateStart))
	return pList

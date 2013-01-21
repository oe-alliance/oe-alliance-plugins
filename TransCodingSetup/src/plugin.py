from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from enigma import eTimer
from os import system as os_system
from __init__ import _

config.plugins.transcodingsetup = ConfigSubsection()
config.plugins.transcodingsetup.transcoding = ConfigSelection(default = "disabled", choices = [ ("enabled", _("enabled")), ("disabled", _("disabled"))] )

_trascodingsetup_error_msg = ""

def ERR(msg):
	print _("[TranscodingSetup]"), msg
	global _trascodingsetup_error_msg
	_trascodingsetup_error_msg = msg

def isExistFile(filename):
	if not fileExists(filename):
		ERR(_("File not found : ") + filename)
		return False
	return True

class TranscodingSetupInit:
	def __init__(self):
		self.old_trascoding = config.plugins.transcodingsetup.transcoding.value

		self.setTranscoding()

	def setTranscoding(self):
		trascoding = config.plugins.transcodingsetup.transcoding.value
		if not self.isAvailableModel():
			ERR(_("This plugin is only supported for solo2/duo2."))
			return False
		if not isExistFile("/proc/stb/encoder/enable") or not isExistFile("/etc/inetd.conf"):
			return False
		activate = trascoding == "enabled"
		activate_msg = activate and "activate" or "inactivate"
		self.activateEncoder(activate)

		# if not self.activateEncoder(activate):
		# 	ERR(_("Encoder failed to ") + activate_msg)
		# 	return False
		# if not self.activateTranstreamproxy(activate):
		# 	ERR(_("Transtreamproxy failed to ") + activate_msg)
		# 	activate = self.old_trascoding == "enabled"
		# 	self.activateEncoder(activate)
		# 	return False
		# if fileExists("/etc/init.d/inetd.busybox"):
		# 	os_system("/etc/init.d/inetd.busybox restart")
		return True

	def activateEncoder(self, activate=False):
		def tryWrite(filename, retry, value):
			self.old_trascoding = file(filename).read().strip()
			for x in range(retry):
				file = open(filename,'w')
				file.write(value)
				if file(filename).read().strip() == value:
					file.close()
					return True
			file.close()
			return False
		enable = activate and "enabled" or "disabled"
		return tryWrite("/proc/stb/encoder/enable", 2, enable)

	def activateTranstreamproxy(self, activate=False):
		try:
			lines = ""
			for line in file('/etc/inetd.conf').readlines():
				if line.find("transtreamproxy") != -1:
					continue
				lines += line
			if activate:
				lines += '8002\tstream\ttcp\tnowait\troot\t/usr/bin/transtreamproxy\ttranstreamproxy\n'
			file("/etc/inetd.conf",'w').write(lines)
		except:	return False
		return True

	def isAvailableModel(self):
		try:
			file = open("/proc/stb/info/vumodel")
			info = file.read().strip()
			file.close()
			return info in ["solo2", "duo2"]
		except: return False

class TranscodingSetup(Screen,ConfigListScreen, TranscodingSetupInit):
	skin =  """
		<screen position="center,center" size="560,280" title="Transcoding Setup" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="110,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="310,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="110,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="310,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="5,70" size="550,80" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="text" render="Label" position="20,150" size="520,130" font="Regular;18" halign="center" valign="center" />
		</screen>
		"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.session = session
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		TEXT = "Transcoding can be started when there is no corresponding channel recordings."
		TEXT += "\nWhen transcoding, both PIP and analog video outputs are disabled."
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		self["text"] = StaticText(_("%s")%TEXT)
		self.createSetup()
		self.onLayoutFinish.append(self.checkModel)
		self.checkModelTimer = eTimer()
		self.checkModelTimer.callback.append(self.invalidmodel)

	def checkModel(self):
		if not self.isAvailableModel():
			self.checkModelTimer.start(1000,True)

	def invalidmodel(self):
		self.session.openWithCallback(self.close, MessageBox, _("This plugin is available on SOLO2/DUO2"), MessageBox.TYPE_ERROR)

	def createSetup(self):
		self.list = []
		self.transcoding = getConfigListEntry(_("Transcoding"), config.plugins.transcodingsetup.transcoding)
		self.port = getConfigListEntry(_("Port"), ConfigSelection(default = "8002", choices = [ ("8002", "8002")] ))
		self.list.append( self.transcoding )
		if config.plugins.transcodingsetup.transcoding.value == "enabled":
			self.list.append( self.port )
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keySave(self):
		if not self.setupTranscoding() :
			self.resetConfig()
			global _trascodingsetup_error_msg
			self.session.openWithCallback(self.close, MessageBox, _trascodingsetup_error_msg, MessageBox.TYPE_ERROR)
			return
		self.saveAll()
		msg = config.plugins.transcodingsetup.transcoding.value
		self.session.openWithCallback(self.close, MessageBox, _("OK. Encoder ")+msg, MessageBox.TYPE_INFO)
		self.close()

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()

	def setupTranscoding(self, transcoding = None, port = None):
		return self.setTranscoding()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self["config"].getCurrent() == self.transcoding:
			self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent() == self.transcoding:
			self.createSetup()

def main(session, **kwargs):
	session.open(TranscodingSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("TranscodingSetup"), description="Transcoding Setup", where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

transcodingsetupinit = TranscodingSetupInit()


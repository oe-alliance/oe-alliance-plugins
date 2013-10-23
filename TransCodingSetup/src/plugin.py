# for localized messages
from . import _

from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigNumber, NoSave
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from enigma import eTimer, getBoxType
from os import system as os_system
from __init__ import _

transcodingsetupinit = None
	
config.plugins.transcodingsetup = ConfigSubsection()
config.plugins.transcodingsetup.transcoding = ConfigSelection(default = "enable", choices = [ ("enable", _("enabled")), ("disable", _("disabled"))] )
config.plugins.transcodingsetup.port = ConfigNumber(default = 8002)
config.plugins.transcodingsetup.tsport = ConfigNumber(default = 8003)
if fileExists("/proc/stb/encoder/0/bitrate"):
	if getBoxType() == "vusolo2":
		config.plugins.transcodingsetup.bitrate = ConfigSelection(default = "100000", choices = [ ("50000", "50 Kbits"), ("100000", "100 Kbits"), ("200000", "200 Kbits"), ("300000", "300 Kbits"), ("400000", "400 Kbits"), ("500000", "500 Kbits"), ("600000", "600 Kbits"), ("700000", "700 Kbits"), ("800000", "800 Kbits"), ("900000", "900 Kbits"), ("1000000", "1 Mbits")])
	else:
		config.plugins.transcodingsetup.bitrate = ConfigSelection(default = "500000", choices = [ ("100000", "100 Kbits"), ("500000", "500 Kbits"), ("1000000", "1 Mbits"), ("1500000", "1.5 Mbits"), ("2000000", "2 Mbits"), ("2500000", "2.5 Mbits"), ("3000000", "3 Mbits"), ("3500000", "3.5 Mbits"), ("4000000", "4 Mbits"), ("4500000", "4.5 Mbits"), ("5000000", "5 Mbits")])
if fileExists("/proc/stb/encoder/0/framerate"):
	config.plugins.transcodingsetup.framerate = ConfigSelection(default = "30000", choices = [ ("23976", "23.976 fps"), ("24000", "24 fps"), ("25000", "25 fps"), ("29970", "29.970 fps"), ("30000", "30 fps"), ("50000", "50 fps"), ("59940", "59.940 fps"), ("60000", "60 fps")])

class TranscodingSetupInit:
	def __init__(self):
		self.pluginsetup = None
		config.plugins.transcodingsetup.transcoding.addNotifier(self.setTranscoding)
		config.plugins.transcodingsetup.port.addNotifier(self.setSteamPort)
		config.plugins.transcodingsetup.tsport.addNotifier(self.setTSPort)
		if hasattr(config.plugins.transcodingsetup, "bitrate"):
			config.plugins.transcodingsetup.bitrate.addNotifier(self.setBitrate)
		if hasattr(config.plugins.transcodingsetup, "framerate"):
			config.plugins.transcodingsetup.framerate.addNotifier(self.setFramerate)

		self.setSteamPort(config.plugins.transcodingsetup.port)
		self.setTSPort(config.plugins.transcodingsetup.tsport)

	def setConfig(self, procPath, value):
		if not fileExists(procPath):
			return -1
		if isinstance(value, str):
			value = value.strip(' ').strip('\n')
		else:
			value = str(value)
		try:
			fd = open(procPath,'r')
			oldValue = fd.read().strip(' ').strip('\n')
			fd.close()
			if oldValue != value:
				print "[TranscodingSetup] set %s "%procPath, value
				fd = open(procPath,'w')
				fd.write(value)
				fd.close()
				fd = open(procPath,'r')
				setvalue = fd.read().strip(' ').strip('\n')
				fd.close()
				if value != setvalue:
					print "[TranscodingSetup] set failed. (%s > %s)" % ( value, procPath )
					return -1
				return 0
		except:
			print "setConfig exception error (%s > %s)" % ( value, procPath )
			return -1

	def setTranscoding(self, configElement):
		encoder = configElement.getValue()
		encodertext = configElement.getText()
		procPath = "/proc/stb/encoder/enable"
		if self.setConfig(procPath, encoder):
			self.showMessage("Set encoder %s failed."%encodertext, MessageBox.TYPE_ERROR)
		elif encoder == "enable" and config.plugins.transcodingsetup.port.value == "8001":
			msg = "OK. Encoder enable.\nPC Streaming is replaced with mobile streaming."
			self.showMessage(msg, MessageBox.TYPE_INFO)
		else:
			self.showMessage("OK. Encoder %s."%encodertext, MessageBox.TYPE_INFO)
			if encoder == "disabled":
				config.plugins.transcodingsetup.port.value = "8002"

	def setBitrate(self, configElement):
		bitrate = configElement.value
		procPath = "/proc/stb/encoder/0/bitrate"
		if self.setConfig(procPath, bitrate):
			fd = open(procPath,'r')
			curValue = fd.read().strip(' ').strip('\n')
			fd.close()
			if curValue.isdigit():
				config.plugins.transcodingsetup.bitrate.value = int(curValue)
				config.plugins.transcodingsetup.bitrate.save()
			self.showMessage("Set bitrate failed.", MessageBox.TYPE_ERROR)

	def setFramerate(self, configElement):
		framerate = configElement.value
		procPath = "/proc/stb/encoder/0/framerate"
		if self.setConfig(procPath, framerate):
			self.showMessage("Set framerate failed.", MessageBox.TYPE_ERROR)

		procPath = "/proc/stb/encoder/0/refreshrate"
		if fileExists(procPath) and self.setConfig(procPath, framerate):
			self.showMessage("Set refreshrate failed.", MessageBox.TYPE_ERROR)

	def setSteamPort(self, configElement):
		self.SteamPort = str(configElement.getValue())
		self.TSPort = str(config.plugins.transcodingsetup.tsport.getValue())
		print "[TranscodingSetup] set Channel port",self.SteamPort
		self.setPort()

	def setTSPort(self, configElement):
		self.SteamPort = str(config.plugins.transcodingsetup.port.getValue())
		self.TSPort = str(configElement.getValue())
		print "[TranscodingSetup] set Channel port",self.TSPort
		self.setPort()

	def setPort(self):
		try:
			fp = file('/etc/inetd.conf', 'r')
			datas = fp.readlines()
			fp.close()
		except:
#			print "file open error, inetd.conf!"
			self.showMessage("Set port failed.", MessageBox.TYPE_ERROR)
			return
		# try:
		newdatas=""
		s_port = ""
		if self.SteamPort == "8001":
			s_port = "8002"
		else:
			s_port = "8001"
		for line in datas:
			if line.find("transtreamproxy") != -1:
				p=line.replace('\t',' ').find(' ')
				line = self.SteamPort+line[p:]
			elif line.find("filestreamproxy") != -1:
				p=line.replace('\t',' ').find(' ')
				line = self.TSPort+line[p:]
			elif line.find("streamproxy") != -1:
				p=line.replace('\t',' ').find(' ')
				line = s_port+line[p:]
			newdatas+=line

		if newdatas.find("transtreamproxy") == -1:
			newdatas+=self.SteamPort+'\t'+'stream'+'\t'+'tcp'+'\t'+'nowait'+'\t'+'root'+'\t'+'/usr/bin/transtreamproxy'+'\t'+'transtreamproxy\n'
		if newdatas.find("filestreamproxy") == -1:
			newdatas+=self.TSPort+'\t'+'stream'+'\t'+'tcp'+'\t'+'nowait'+'\t'+'root'+'\t'+'/usr/bin/filestreamproxy'+'\t'+'filestreamproxy\n'
		fd = file("/etc/inetd.conf",'w')
		fd.write(newdatas)
		fd.close()
		# except:
		# 	self.showMessage("Set port failed.", MessageBox.TYPE_ERROR)
		# 	return
		self.inetdRestart()
		if config.plugins.transcodingsetup.transcoding.value == "enable" and self.SteamPort == "8001":
			msg = "Set port OK.\nPC Streaming is replaced with mobile streaming."
			self.showMessage(msg, MessageBox.TYPE_INFO)

	def inetdRestart(self):
		if fileExists("/etc/init.d/inetd"):
			os_system("/etc/init.d/inetd restart")
		elif fileExists("/etc/init.d/inetd.busybox"):
			os_system("/etc/init.d/inetd.busybox restart")

	def showMessage(self, msg, msgType):
		if self.pluginsetup:
			self.pluginsetup.showMessage(msg, msgType)

class TranscodingSetup(Screen,ConfigListScreen):
	skin =  """
		<screen position="center,center" size="540,320">
			<ePixmap pixmap="skin_default/buttons/red.png" position="30,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="200,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="370,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="30,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="200,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="370,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="20,70" size="500,120" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="text" render="Label" position="30,190" size="480,130" font="Regular;18" halign="center" valign="center" />
		</screen>
		"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.setTitle(_("Transcoding Setup"))
		self.onChangedEntry = [ ]
		self.skinName = ["Setup" ]
		self.setup_title = _("Video enhancement setup")
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)
		self['footnote'] = Label()

		TEXT = _("Transcoding can be started when there is no corresponding channel recordings.")
		if getBoxType() == "vusolo2":
			TEXT += _("\nWhen transcoding, both PIP and analog video outputs are disabled.")
		else:
			TEXT += _("\nWhen transcoding, PIP is disabled.")
		self.session = session
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow" : self.KeyDefault,
		}, -2)
		self.list = []
		self.onChangedEntry = [ ]
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Default"))
		self["description"] = Label(_("%s")%TEXT)
		self.createSetup()
		self.onLayoutFinish.append(self.checkEncoder)
		self.invaliedModelTimer = eTimer()
		self.invaliedModelTimer.callback.append(self.invalidmodel)
		global transcodingsetupinit
		transcodingsetupinit.pluginsetup = self
		# if not self.SelectionChanged in self["config"].onSelectionChanged:
		# 	self["config"].onSelectionChanged.append(self.SelectionChanged)
		self.changedEntry()
		self.onClose.append(self.onClosed)

	def onClosed(self):
		transcodingsetupinit.pluginsetup = None

	def checkEncoder(self):
		if not fileExists("/proc/stb/encoder/enable"):
			self.invaliedModelTimer.start(100,True)

	def invalidmodel(self):
		self.session.openWithCallback(self.close, MessageBox, _("This model is not support transcoding."), MessageBox.TYPE_ERROR)

	def createSetup(self):
		self.list = []
		self.transcoding = getConfigListEntry(_("Transcoding"), config.plugins.transcodingsetup.transcoding)
		self.list.append( self.transcoding )
		if config.plugins.transcodingsetup.transcoding.value == "enable":
			self.list.append(getConfigListEntry(_("Channel Port"), config.plugins.transcodingsetup.port))
			self.list.append(getConfigListEntry(_("Media Port"), config.plugins.transcodingsetup.tsport))
			if hasattr(config.plugins.transcodingsetup, "bitrate"):
				self.list.append(getConfigListEntry(_("Bitrate"), config.plugins.transcodingsetup.bitrate))
			if hasattr(config.plugins.transcodingsetup, "framerate"):
				self.list.append(getConfigListEntry(_("Framerate"), config.plugins.transcodingsetup.framerate))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	# def SelectionChanged(self):
	# 	if self["config"].getCurrent() == self.transcoding:
	# 		self.createSetup()

	def showMessage(self, msg, msgType = MessageBox.TYPE_ERROR):
		self.session.open(MessageBox, _(msg), msgType)

	def keySave(self):
		transcodingsetupinit.setSteamPort(config.plugins.transcodingsetup.port)
		transcodingsetupinit.setTSPort(config.plugins.transcodingsetup.tsport)
		self.saveAll()
		self.close()

	def KeyDefault(self):
		config.plugins.transcodingsetup.port.value = config.plugins.transcodingsetup.port.default
		config.plugins.transcodingsetup.tsport.value = config.plugins.transcodingsetup.tsport.default
		if hasattr(config.plugins.transcodingsetup, "bitrate"):
			config.plugins.transcodingsetup.bitrate.value = config.plugins.transcodingsetup.bitrate.default
		if hasattr(config.plugins.transcodingsetup, "framerate"):
			config.plugins.transcodingsetup.framerate.value = config.plugins.transcodingsetup.framerate.default
		self.createSetup()

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()

	def cancelConfirm(self, result):
		if not result:
			return
		configlist = []
		configlist.append(config.plugins.transcodingsetup.transcoding)
		configlist.append(config.plugins.transcodingsetup.port)
		configlist.append(config.plugins.transcodingsetup.tsport)
		configlist.append(config.plugins.transcodingsetup.bitrate)
		configlist.append(config.plugins.transcodingsetup.framerate)
		for x in configlist:
			x.cancel()
		self.close()

	def keyCancel(self):
		transcodingsetupinit.pluginsetup = None
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		if self["config"].getCurrent() == self.transcoding:
			self.createSetup()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

def main(session, **kwargs):
	session.open(TranscodingSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("TranscodingSetup"), description=_("Transcoding Setup"), where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

transcodingsetupinit = TranscodingSetupInit()


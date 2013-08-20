# for localized messages
from . import _

from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from enigma import eTimer, getBoxType
from os import system as os_system
from __init__ import _

error_msg ={
	-1 : "File not exist - /proc/stb/encoder/enable.",
	-2 : "File not exist - /etc/inetd.conf.",
	-3 : "File open error - /proc/stb/encoder/enable.",
	-4 : "File open error - /etc/inetd.conf.",
	-5 : "Set encoder error.",
	-6 : "Set port error.",
	-7 : "Setting value is incorrect.",
	-8 : "Set encoder bitrate error.",
	-9 : "Set encoder framerate error.",
}
TranscodingConfigList = []

class TranscodingSetupInit:
	def __init__(self):
		self.createConfigList()
		self.createConfig()
		self.transcoding_value = config.plugins.transcodingsetup.transcoding.value
		if self.transcoding_value == "disable":
			self.port_value = "8002"
		else:
			self.port_value = config.plugins.transcodingsetup.port.value
		self.transcoding_old = config.plugins.transcodingsetup.transcoding.value
		# res = self.setTranscoding(self.transcoding_value, self.port_value)

		def setTranscode(configElement):
			self.setTranscoding(self.transcoding_value, self.port_value)
			if res is not None and res < 0:
				print "[TranscodingSetup] set failed!(%s, %s, %d)"%(self.transcoding_value, self.port_value, res)
		config.plugins.transcodingsetup.transcoding.addNotifier(setTranscode)
		config.plugins.transcodingsetup.port.addNotifier(setTranscode)
		config.plugins.transcodingsetup.bitrate.addNotifier(setTranscode)
		config.plugins.transcodingsetup.framerate.addNotifier(setTranscode)

	def createConfigList(self):
		global TranscodingConfigList
		configList = [
			["Bitrate", "/proc/stb/encoder/0/bitrate", -8],
			["Framerate", "/proc/stb/encoder/0/framerate", -9]
		]
		for x in configList:
			if fileExists(x[1]):
				TranscodingConfigList.append(x)

	def createConfig(self):
		config.plugins.transcodingsetup = ConfigSubsection()
		config.plugins.transcodingsetup.transcoding = ConfigSelection(default = "enable", choices = [ ("enable", _("enable")), ("disable", _("disable"))] )
		config.plugins.transcodingsetup.port = ConfigSelection(default = "8002", choices = [ ("8001", "8001"), ("8002", "8002")] )
		global TranscodingConfigList
		for x in TranscodingConfigList:
			if x[0] == "Bitrate":
				if getBoxType() == "vusolo2":
					config.plugins.transcodingsetup.bitrate = ConfigSelection(default = "500000", choices = [ ("50000", "50 Kbits"), ("100000", "100 Kbits"), ("200000", "200 Kbits"), ("300000", "300 Kbits"), ("400000", "400 Kbits"), ("500000", "500 Kbits"), ("600000", "600 Kbits"), ("700000", "700 Kbits"), ("800000", "800 Kbits"), ("900000", "900 Kbits"), ("1000000", "1 Mbits")])
				else:
					config.plugins.transcodingsetup.bitrate = ConfigSelection(default = "500000", choices = [ ("100000", "100 Kbits"), ("500000", "500 Kbits"), ("1000000", "1 Mbits"), ("1500000", "1.5 Mbits"), ("2000000", "2 Mbits"), ("2500000", "2.5 Mbits"), ("3000000", "3 Mbits"), ("3500000", "3.5 Mbits"), ("4000000", "4 Mbits"), ("4500000", "4.5 Mbits"), ("5000000", "5 Mbits")])
				x.append(config.plugins.transcodingsetup.bitrate)
			elif x[0] == "Framerate":
				config.plugins.transcodingsetup.framerate = ConfigSelection(default = "30000", choices = [ ("23976", "23.976 fps"), ("24000", "24 fps"), ("25000", "25 fps"), ("29970", "29.970 fps"), ("30000", "30 fps"), ("50000", "50 fps"), ("59940", "59.940 fps"), ("60000", "60 fps")])
				x.append(config.plugins.transcodingsetup.framerate)

	def setTranscoding(self, transcoding, port):
		if transcoding not in ["enable","disable"] or port not in ["8001","8002"]:
#			print "Input error."
			return -7
		if not fileExists("/proc/stb/encoder/enable"):
			return -1
		elif not fileExists("/etc/inetd.conf"):
			return -2
		res = self.setEncoderExtra()
		if res < 0:
			return res
		if self.setEncoderEnable(transcoding) < 0:
			return -5
		res = self.setPort(port)
		if res < 0:
			self.setEncoderEnable(self.transcoding_old)
			return res
		else:
			self.inetdRestart()
		return res

	def setEncoderEnable(self,mode = "disable"):
#		print "<TranscodingSetup> set encoder %s" % mode
		mode = mode.strip(' ').strip('\n')
		try:
			fd = open("/proc/stb/encoder/enable",'r')
			self.transcoding_old = fd.read()
			fd.close()
			fd = open("/proc/stb/encoder/enable",'w')
			fd.write(mode)
			fd.close()
			fd = open("/proc/stb/encoder/enable",'r')
			encoder_enable = fd.read().strip(' ').strip('\n')
			fd.close()
			if encoder_enable == mode:
				return 0
			else:
#				print "<TranscodingSetup> can not setting."
				return -1
		except:
#			print "setEncoderEnable exception error"
			return -1

	def setPort(self, port = "8001"):
#		print "<TranscodingSetup> set port %s" % port
		try:
			fp = file('/etc/inetd.conf', 'r')
			datas = fp.readlines()
			fp.close()
		except:
#			print "file open error, inetd.conf!"
			return -4
		try:
			newdatas=""
			s_port = ""
			if port == "8001":
				s_port = "8002"
			else:
				s_port = "8001"
			for line in datas:
				if line.find("transtreamproxy") != -1:
					p=line.replace('\t',' ').find(' ')
					line = port+line[p:]
				elif line.find("streamproxy") != -1:
					p=line.replace('\t',' ').find(' ')
					line = s_port+line[p:]
				newdatas+=line

			if newdatas.find("transtreamproxy") == -1:
				newdatas+=port+'\t'+'stream'+'\t'+'tcp'+'\t'+'nowait'+'\t'+'root'+'\t'+'/usr/bin/transtreamproxy'+'\t'+'transtreamproxy\n'
			fd = file("/etc/inetd.conf",'w')
			fd.write(newdatas)
			fd.close()
		except:
			return -6
		return 0

	def inetdRestart(self):
		if fileExists("/etc/init.d/inetd"):
			os_system("/etc/init.d/inetd restart")
		elif fileExists("/etc/init.d/inetd.busybox"):
			os_system("/etc/init.d/inetd.busybox restart")

	def setEncoderExtra(self):
		global TranscodingConfigList
		for x in TranscodingConfigList:
			if self.setEncoder(x[1], x[3].value):
				return x[2]
		return 0

	def setEncoder(self, procPath, value):
#		print "<TranscodingSetup> set %s "%procPath, value
		if not fileExists(procPath):
			return -1
		if isinstance(value, str):
			value = value.strip(' ').strip('\n')
		else:
			value = str(value)
		try:
			fd = open(procPath,'r')
			old_value = fd.read().strip(' ').strip('\n')
			fd.close()
			if old_value != value:
				print "[TranscodingSetup] set %s "%procPath, value
				fd = open(procPath,'w')
				fd.write(value)
				fd.close()
				fd = open(procPath,'r')
				encoder_value = fd.read().strip(' ').strip('\n')
				fd.close()
				if encoder_value != value:
					return -1
			return 0
		except:
			return -1

class TranscodingSetup(Screen, ConfigListScreen, TranscodingSetupInit):
	skin =  """
		<screen position="center,center" size="400,270" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="30,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="230,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="30,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="230,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="5,70" size="390,125" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="text" render="Label" position="20,120" size="370,150" font="Regular;18" halign="center" valign="bottom" />
		</screen>
		"""
	def __init__(self,session):
		Screen.__init__(self,session)
		self.setup_title = _('Transcoding Setup')
		self.setTitle(self.setup_title)
		self.session = session
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
		}, -2)
		self.onChangedEntry = [ ]
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		self["text"] = StaticText()
		self.createSetup()
		self.onLayoutFinish.append(self.checkEncoder)
		self.invaliedModelTimer = eTimer()
		self.invaliedModelTimer.callback.append(self.invalidmodel)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def selectionChanged(self):
		self.text = _("Transcoding can be started when there is no corresponding channel recordings.")
		if getBoxType() == "vuduo2":
			self.text += _("\nWhen transcoding, PIP is disabled.")
		else:
			self.text += _("\nWhen transcoding, both PIP and analog video outputs are disabled.")
		self["text"].setText(_("%s")%self.text)

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.selectionChanged()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def checkEncoder(self):
		if not fileExists("/proc/stb/encoder/enable"):
			self.invaliedModelTimer.start(100,True)

	def invalidmodel(self):
		self.session.openWithCallback(self.close, MessageBox, _("This model is not support transcoding."), MessageBox.TYPE_ERROR)

	def createSetup(self):
		global TranscodingConfigList
		self.list = []
		self.transcoding = getConfigListEntry(_("Transcoding"), config.plugins.transcodingsetup.transcoding)
		self.port = getConfigListEntry(_("Port"), config.plugins.transcodingsetup.port)
		self.list.append( self.transcoding )
		if config.plugins.transcodingsetup.transcoding.value == "enable":
			self.list.append(self.port)
			for x in TranscodingConfigList:
				self.list.append(getConfigListEntry(_(x[0]), x[3]))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keySave(self):
		transcoding = config.plugins.transcodingsetup.transcoding.value
		port = config.plugins.transcodingsetup.port.value
#		print "<TranscodingSetup> Transcoding %s(port : %s)"%(transcoding, port)
		ret = self.setupTranscoding(transcoding, port)
		if ret is not None and ret <0 :
			self.resetConfig()
			global error_msg
			self.session.openWithCallback(self.close, MessageBox, _("Failed, Encoder %s\n(%s).")%(transcoding, error_msg[ret]), MessageBox.TYPE_ERROR)
		else:
			self.saveAll()
			if transcoding == "enable" and port == "8001" :
				text = "PC Streaming is replaced with mobile streaming."
				self.session.openWithCallback(self.close, MessageBox, _("OK. Encoder %s.\n%s")%(transcoding,text), MessageBox.TYPE_INFO)
			else:
				self.session.openWithCallback(self.close, MessageBox, _("OK. Encoder %s.")%transcoding, MessageBox.TYPE_INFO)
			self.close()

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()

	def setupTranscoding(self, transcoding = None, port = None):
		if transcoding == "disable":
			config.plugins.transcodingsetup.port.value = "8002"
			port = "8002"
		return self.setTranscoding(transcoding, port)

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
	return [PluginDescriptor(name=_("TranscodingSetup"), description=_("Transcoding Setup"), where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

transcodingsetupinit = TranscodingSetupInit()


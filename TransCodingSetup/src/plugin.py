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
config.plugins.transcodingsetup.port = ConfigSelection(default = "8002", choices = [ ("8001", "8001"), ("8002", "8002")] )

error_msg ={
	-1 : "File not exist - /proc/stb/encoder/enable.",
	-2 : "File not exist - /etc/inetd.conf.",
	-3 : "File open error - /proc/stb/encoder/enable.",
	-4 : "File open error - /etc/inetd.conf.",
	-5 : "Set encoder error.",
	-6 : "Set port error.",
	-7 : "Setting value is incorrect."
}
class TranscodingSetupInit:
	def __init__(self):
		self.transcoding_value = config.plugins.transcodingsetup.transcoding.value
		if self.transcoding_value == "disabled":
			self.port_value = "8002"
		else:
			self.port_value = config.plugins.transcodingsetup.port.value
		self.transcoding_old = config.plugins.transcodingsetup.transcoding.value
		ret = self.setTranscoding(self.transcoding_value, self.port_value)
		if ret is not None and ret < 0:
			print "[TranscodingSetup] set failed!(%s, %s)"%(self.transcoding_value, self.port_value)

	def setTranscoding(self, transcoding, port):
		if not self.getModel():
			print "This plugin is only supported for solo2/duo2."
			return -8
		if transcoding not in ["enabled","disabled"] or port not in ["8001","8002"]:
			print "Input error."
			return -7
		if not fileExists("/proc/stb/encoder/enable"):
			return -1
		elif not fileExists("/etc/inetd.conf"):
			return -2
		if self.setEncoder(transcoding) < 0:
			return -5
		res = self.setPort(port)
		if res < 0:
			self.setEncoder(self.transcoding_old)
			return res
		else:
			self.inetdRestart()
		return res

	def setEncoder(self,mode = "disabled"):
		print "<TranscodingSetup> set encoder : %s" % mode
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
#			print "setEncoder exception error"
			return -1

	def setPort(self, port = "8001"):
		print "<TranscodingSetup> set port : %s" % port
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

	def getModel(self):
		if fileExists("/proc/stb/info/vumodel"):
			vumodel = open("/proc/stb/info/vumodel")
			info=vumodel.read().strip()
			vumodel.close()
			if info in ["solo2", "duo2"]:
				return True
			else:
				return False
		else:
			return False

class TranscodingSetup(Screen,ConfigListScreen, TranscodingSetupInit):
	skin =  """
		<screen position="center,center" size="560,270" title="Transcoding Setup" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="110,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="310,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="110,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="310,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="5,70" size="550,70" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="text" render="Label" position="20,140" size="520,130" font="Regular;18" halign="center" valign="center" />
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
		if not self.getModel():
			self.checkModelTimer.start(1000,True)

	def invalidmodel(self):
			self.session.openWithCallback(self.close, MessageBox, _("This plugin is available on SOLO2/DUO2"), MessageBox.TYPE_ERROR)

	def createSetup(self):
		self.list = []
		self.transcoding = getConfigListEntry(_("Transcoding"), config.plugins.transcodingsetup.transcoding)
		self.port = getConfigListEntry(_("Port"), config.plugins.transcodingsetup.port)
		self.list.append( self.transcoding )
		if config.plugins.transcodingsetup.transcoding.value == "enabled":
			self.list.append( self.port )
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keySave(self):
		transcoding = config.plugins.transcodingsetup.transcoding.value
		port = config.plugins.transcodingsetup.port.value
		print "<TranscodingSetup> Transcoding %s(port : %s)"%(transcoding, port)
		ret = self.setupTranscoding(transcoding, port)
		if ret is not None and ret <0 :
			self.resetConfig()
			global error_msg
			self.session.openWithCallback(self.close, MessageBox, _("Failed, Encoder %s\n(%s).")%(transcoding, error_msg[ret]), MessageBox.TYPE_ERROR)
		else:
			self.saveAll()
			if transcoding == "enabled" and port == "8001" :
				text = "PC Streaming is replaced with mobile streaming."
				self.session.openWithCallback(self.close, MessageBox, _("OK. Encoder %s.\n%s")%(transcoding,text), MessageBox.TYPE_INFO)
			else:
				self.session.openWithCallback(self.close, MessageBox, _("OK. Encoder %s.")%transcoding, MessageBox.TYPE_INFO)
			self.close()

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()

	def setupTranscoding(self, transcoding = None, port = None):
		if transcoding == "disabled":
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
	return [PluginDescriptor(name=_("TranscodingSetup"), description="Transcoding Setup", where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

transcodingsetupinit = TranscodingSetupInit()


# for localized messages
from . import _

from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, configfile, ConfigSubList, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger, integer_limits, NoSave
from Components.ActionMap import ActionMap
from Components.SystemInfo import SystemInfo
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from enigma import eTimer
from boxbranding import getBoxType
from os import system as os_system, path as os_path, listdir as os_listdir

def getProcValue(procPath):
#	print "[TranscodingSetup] get %s from %s" % (curValue, procPath)
	fd = open(procPath,'r')
	curValue = fd.read().strip(' ').strip('\n')
	fd.close()
	return curValue

def setProcValue(procPath, value):
#	print "[TranscodingSetup] set %s to %s" % (procPath, value)
	fd = open(procPath,'w')
	fd.write(value)
	fd.close()

def getProcPath(encoder, configName):
	_configName = {
		"bitrate"		:	"bitrate",
		"framerate"		:	"framerate",
		"resolution" 	: 	"display_format",
		"aspectratio" 	: 	"aspectratio",
		"audiocodec" 	: 	"audio_codec",
		"videocodec" 	: 	"video_codec",
		"gopframeb" 	: 	"gop_frameb",
		"gopframep" 	: 	"gop_framep",
		"level" 		: 	"level",
		"profile" 		: 	"profile",
		"width" 		: 	"width",
		"height" 		: 	"height",
	}.get(configName)
	return "/proc/stb/encoder/%s/%s" % (encoder, _configName)

def checkSupportAdvanced():
	if fileExists(getProcPath(0, "aspectratio")):
		return True
	return False

config.plugins.transcodingsetup = ConfigSubsection()
config.plugins.transcodingsetup.transcoding = ConfigSelection(default = "enable", choices = [ ("enable", _("enable")), ("disable", _("disable"))])
config.plugins.transcodingsetup.port = ConfigInteger(default = 8002, limits = (8002, 9999))
config.plugins.transcodingsetup.encoder = ConfigSubList()

def createTransCodingConfig(encoder):
	if fileExists(getProcPath(encoder ,"bitrate")):
		if getBoxType() == "vusolo2":
			choice = ConfigSelection(default = "400000", choices=[("50000", "50 Kbits"), ("100000", "100 Kbits"), ("150000", "150 Kbits"), ("200000", "200 Kbits"), ("250000", "250 Kbits"), ("300000", "300 Kbits"), ("350000", "350 Kbits"), ("400000", "400 Kbits"), ("450000", "450 Kbits"), ("500000", "500 Kbits"), ("600000", "600 Kbits"), ("700000", "700 Kbits"), ("800000", "800 Kbits"), ("900000", "900 Kbits"), ("1000000", "1 Mbits")])
		else:
			choice = ConfigSelection(default = "2000000", choices=[("100000", "100 Kbits"), ("150000", "150 Kbits"), ("200000", "200 Kbits"), ("250000", "250 Kbits"), ("300000", "300 Kbits"), ("350000", "350 Kbits"), ("400000", "400 Kbits"), ("450000", "450 Kbits"), ("500000", "500 Kbits"), ("750000", "750 Kbits"), ("1000000", "1 Mbits"), ("1500000", "1.5 Mbits"), ("2000000", "2 Mbits"), ("2500000", "2.5 Mbits"), ("3000000", "3 Mbits"), ("3500000", "3.5 Mbits"), ("4000000", "4 Mbits"), ("4500000", "4.5 Mbits"), ("5000000", "5 Mbits"), ("10000000", "10 Mbits")])
		config.plugins.transcodingsetup.encoder[int(encoder)].bitrate = choice

	if fileExists(getProcPath(encoder ,"framerate")):
		choice = ConfigSelection(default = "50000", choices = [("23976", "23.976 fps"), ("24000", "24 fps"), ("25000", "25 fps"), ("29970", "29.970 fps"), ("30000", "30 fps"), ("50000", "50 fps"), ("59940", "59.940 fps"), ("60000", "60 fps")])
		config.plugins.transcodingsetup.encoder[int(encoder)].framerate = choice
	
	if checkSupportAdvanced():
		if (hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "bitrate") or hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "framerate")):
			choice = ConfigSelection(default = "Off", choices = [ ("On", _("On")), ("Off", _("Off")) ])
			config.plugins.transcodingsetup.encoder[int(encoder)].automode = choice
	
		if fileExists(getProcPath(encoder, "resolution")):
			choice = ConfigSelection(default = "480p", choices = [ ("480p", _("480p")), ("576p", _("576p")), ("720p", _("720p")), ("320x240", _("320x240")), ("160x120", _("160x120")) ])
			config.plugins.transcodingsetup.encoder[int(encoder)].resolution = choice
	
		if fileExists(getProcPath(encoder, "aspectratio")):
			choice = ConfigSelection(default = "2", choices = [ ("0", _("auto")), ("1", _("4x3")), ("2", _("16x9")) ])
			config.plugins.transcodingsetup.encoder[int(encoder)].aspectratio = choice
	
		if fileExists(getProcPath(encoder, "audiocodec")):
			choice = ConfigSelection(default = "aac", choices = [("mpg", _("mpg")), ("mp3", _("mp3")), ("aac", _("aac")), ("aac+", _("aac+")), ("aac+loas", _("aac+loas")), ("aac+adts", _("aac+adts")), ("ac3", _("ac3"))])
			config.plugins.transcodingsetup.encoder[int(encoder)].audiocodec = choice
	
		if fileExists(getProcPath(encoder, "videocodec")):
			choice = ConfigSelection(default = "h264", choices = [ ("h264", _("h264")) ])
			config.plugins.transcodingsetup.encoder[int(encoder)].videocodec = choice
	
		if fileExists(getProcPath(encoder, "gopframeb")):
			choice = ConfigInteger(default = 0, limits = (0, 60))
			config.plugins.transcodingsetup.encoder[int(encoder)].gopframeb = choice
	
		if fileExists(getProcPath(encoder, "gopframep")):
			choice = ConfigInteger(default = 29, limits = (0, 60))
			config.plugins.transcodingsetup.encoder[int(encoder)].gopframep = choice
	
		if fileExists(getProcPath(encoder, "level")):
			choice = ConfigSelection(default = "3.1", choices = [("1.0", _("1.0")), ("2.0", _("2.0")),
				("2.1", _("2.1")), ("2.2", _("2.2")), ("3.0", _("3.0")), ("3.1", _("3.1")),
				("3.2", _("3.2")), ("4.0", _("4.0")), ("4.1", _("4.1")), ("4.2", _("4.2")),
				("5.0", _("5.0")), ("low", _("low")), ("main", _("main")), ("high", _("high"))])
			config.plugins.transcodingsetup.encoder[int(encoder)].level = choice
	
		if fileExists(getProcPath(encoder, "profile")):
			choice = ConfigSelection(default = "baseline", choices = [("baseline", _("baseline")), ("simple", _("simple")), ("main", _("main")), ("high", _("high")), ("advanced simple", _("advancedsimple"))])
			config.plugins.transcodingsetup.encoder[int(encoder)].profile = choice

# check encoders
encoders = []
encoderPath = "/proc/stb/encoder"
numofencoders = os_listdir(encoderPath)
numofencoders.sort()
for encoder in numofencoders:
	encPath = os_path.join(encoderPath, encoder)
	if not os_path.isdir(encPath):
		continue
	if fileExists(os_path.join(encPath, "bitrate")):
		encoders.append(encoder)
		config.plugins.transcodingsetup.encoder.append(ConfigSubsection())
		createTransCodingConfig(encoder)

choices = []
if len(encoders) > 1:
	encoders.sort()
	for encoder in encoders:
		choices.append((encoder, encoder))
else:
	choices.append(('0','0'))
	
config.plugins.transcodingsetup.encodernum = ConfigSelection(default = '0', choices = choices)

SystemInfo["AdvancedTranscoding"] = checkSupportAdvanced()
SystemInfo["MultipleEncoders"] = len(encoders) > 1

transcodingsetupinit = None
class TranscodingSetupInit:
	def __init__(self):
		self.pluginsetup = None
		self.setTranscoding()
		for encoder in encoders:
			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "automode"):
				if config.plugins.transcodingsetup.encoder[int(encoder)].automode.getValue() == "On":
					config.plugins.transcodingsetup.encoder[int(encoder)].automode.addNotifier(self.setAutomode, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "bitrate"):
				config.plugins.transcodingsetup.encoder[int(encoder)].bitrate.addNotifier(self.setBitrate, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "framerate"):
				config.plugins.transcodingsetup.encoder[int(encoder)].framerate.addNotifier(self.setFramerate, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "resolution"):
				config.plugins.transcodingsetup.encoder[int(encoder)].resolution.addNotifier(self.setResolution, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "aspectratio"):
				config.plugins.transcodingsetup.encoder[int(encoder)].aspectratio.addNotifier(self.setAspectRatio, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "audiocodec"):
				config.plugins.transcodingsetup.encoder[int(encoder)].audiocodec.addNotifier(self.setAudioCodec, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "videocodec"):
				config.plugins.transcodingsetup.encoder[int(encoder)].videocodec.addNotifier(self.setVideoCodec, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "gopframeb"):
				config.plugins.transcodingsetup.encoder[int(encoder)].gopframeb.addNotifier(self.setGopFrameB, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "gopframep"):
				config.plugins.transcodingsetup.encoder[int(encoder)].gopframep.addNotifier(self.setGopFrameP, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "level"):
				config.plugins.transcodingsetup.encoder[int(encoder)].level.addNotifier(self.setLevel, extra_args=[int(encoder)])

			if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "profile"):
				config.plugins.transcodingsetup.encoder[int(encoder)].profile.addNotifier(self.setProfile, extra_args=[int(encoder)])

		config.plugins.transcodingsetup.port.addNotifier(self.setPort)

	def setConfig(self, procPath, value):
		if not fileExists(procPath):
			return -1
		if isinstance(value, str):
			value = value.strip(' ').strip('\n')
		else:
			value = str(value)
		try:
			oldValue = getProcValue(procPath)
			if oldValue != value:
				# print "[TranscodingSetup] set %s "%procPath, value
				setProcValue(procPath, value)
				setValue = getProcValue(procPath)
				if value != setValue:
					print "[TranscodingSetup] set failed. (%s > %s)" % (value, procPath)
					return -1
				return 0
		except:
			print "setConfig exception error (%s > %s)" % (value, procPath)
			return -1
		return 0

	def setupConfig(self, configElement, procPath):
		if fileExists(procPath):
			print "[TranscodingSetup] set %s to %s" % (procPath, configElement.value)
			configValue = configElement.getValue()
			if self.setConfig(procPath, configValue):
				# set config failed, reset to current proc value
				self.getConfigFromProc(procPath, configElement)
				self.showMessage("Set %s failed." % (procPath), MessageBox.TYPE_ERROR)

	def getConfigFromProc(self, procPath, configElement):
		if fileExists(procPath):
			curValue = getProcValue(procPath)
			if isinstance(configElement.value, int): # is int ?
				curValue = int(curValue)
			configElement.value = curValue
			configElement.save()

	def setTranscoding(self):
		procPath = "/proc/stb/encoder/enable"
		self.setConfig(procPath, 'enable')

	def setAutomode(self, configElement, extra_args):
		configName = "AutoMode"
		# print "[TranscodingSetup]  setAutomode, configName %s, value %s" % (configName, configElement.value)
		if configElement.value == "On":
			autoValue = str(-1)
			if (hasattr(config.plugins.transcodingsetup.encoder[int(extra_args[0])], "bitrate") and self.setConfig(getProcPath(int(extra_args[0]) ,"bitrate"), autoValue)) or (hasattr(config.plugins.transcodingsetup.encoder[int(extra_args[0])], "framerate") and self.setConfig(getProcPath(int(extra_args[0]), "framerate"), autoValue)):
				configElement.value = "Off" # set config failed, reset to previous value
				configElement.save()
				self.showMessage("Set %s failed." % (configName), MessageBox.TYPE_ERROR)
		else: # Off
			if hasattr(config.plugins.transcodingsetup.encoder[int(extra_args[0])], "bitrate"):
				self.setBitrate(config.plugins.transcodingsetup.encoder[int(extra_args[0])].bitrate)
			if hasattr(config.plugins.transcodingsetup.encoder[int(extra_args[0])], "framerate"):
				self.setFramerate(config.plugins.transcodingsetup.encoder[int(extra_args[0])].framerate)

	def setBitrate(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"bitrate"))

	def setFramerate(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"framerate"))

	def setResolution(self, configElement, extra_args):
		resolution = configElement.value
		if resolution in [ "320x240", "160x120" ]:
			(width, height) = tuple(resolution.split('x'))
			self.setConfig(getProcPath(int(extra_args[0]) ,"resolution"), "custom")
			self.setConfig(getProcPath(int(extra_args[0]) ,"width"), width)
			self.setConfig(getProcPath(int(extra_args[0]) ,"height"), height)
		else:
			self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"resolution"))

	def setAspectRatio(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"aspectratio"))

	def setAudioCodec(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"audiocodec"))

	def setVideoCodec(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"videocodec"))

	def setGopFrameB(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"gopframeb"))

	def setGopFrameP(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"gopframep"))

	def setLevel(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"level"))

	def setProfile(self, configElement, extra_args):
		self.setupConfig(configElement, getProcPath(int(extra_args[0]) ,"profile"))

	def setPort(self, configElement):
		port = configElement.getValue()

		print "[TranscodingSetup] set port",port
		try:
			fp = file('/etc/inetd.conf', 'r')
			datas = fp.read()
			fp.close()

			newConfigData = ""
			oldConfigData = datas
			for L in oldConfigData.splitlines():
				try:
					if L[0] == '#':
						newConfigData += L + '\n'
						continue
				except: continue
				LL = L.split()
				if LL[5] == '/usr/bin/transtreamproxy':
					LL[0] = port
				if LL[5] == '/usr/bin/filestreamproxy':
					LL = ''
				newConfigData += ''.join(str(X) + "\t" for X in LL) + '\n'

			if newConfigData.find("transtreamproxy") == -1:
				newConfigData += port + "/tstream\ttcp\tnowait\troot\t/usr/bin/transtreamproxy\ttranstreamproxy\n"
			fd = file("/etc/inetd.conf",'w')
			fd.write(newConfigData)
			fd.close()
		except:
			self.showMessage("Set port failed.", MessageBox.TYPE_ERROR)
			return

		self.inetdRestart()

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
		<screen name="TranscodingSetup" position="center,center" size="600,450">
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<widget name="blue" pixmap="skin_default/buttons/blue.png" position="455,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="key_blue" render="Label" position="455,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="25,70" size="560,300" scrollbarMode="showOnDemand" transparent="1" />
			<widget name="description" position="20,370" size="540,60" font="Regular;20" halign="center" valign="center" />
			<widget name="text" position="20,430" size="540,20" font="Regular;22" halign="center" valign="center" />
		</screen>
		"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.session = session
		self.onChangedEntry = [ ]
		self.skinName = "TranscodingSetup"
		self.setup_title = _("Transcoding Setup")
		self.setTitle(self.setup_title)

		if getBoxType() == "vusolo2":
			TEXT = _("Transcoding and PIP are mutually exclusive.")
		else:
			TEXT = _("2nd transcoding and PIP are mutually exclusive.")
		self["text"] = Label(_("%s")%TEXT)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Default"))
		self["key_blue"] = Button(_("Advanced"))

		# Background for Buttons
		self["blue"] = Pixmap()

		if not checkSupportAdvanced():
			self["blue"].hide()
			self["key_blue"].hide()

		self["description"] = Label()

		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow" : self.KeyDefault,
			"blue" : self.keyBlue,
		}, -2)

		self.list = []
		self.onChangedEntry = [ ]
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.setupMode = "Normal" # Normal / Advanced
		self.encoder = None
		self.automode = None
		self.createSetup()
		self.onLayoutFinish.append(self.checkEncoder)
		self.invaliedModelTimer = eTimer()
		self.invaliedModelTimer.callback.append(self.invalidmodel)
		global transcodingsetupinit
		transcodingsetupinit.pluginsetup = self
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
		self.list.append(getConfigListEntry(_("Port"), config.plugins.transcodingsetup.port))

		encoder = None
		if len(encoders) == 1:
			encoder = encoders[0]
		elif len(encoders) > 1:
			self.encoder = getConfigListEntry(_("Encoder"), config.plugins.transcodingsetup.encodernum)
			self.list.append(self.encoder)
			encoder = config.plugins.transcodingsetup.encodernum.getValue()
		self.curencoder = encoder
		self.createSetup2()

	def createSetup2(self):
		encoder = self.curencoder
		if encoder is not None:
			self.automode = None
			if checkSupportAdvanced() and hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "automode"):
				self.automode = getConfigListEntry(_("Auto set Framerate / Bitrate"), config.plugins.transcodingsetup.encoder[int(encoder)].automode)

			if self.automode is not None:
				self.list.append(self.automode)

			if not hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "automode") or (hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "automode") and config.plugins.transcodingsetup.encoder[int(encoder)].automode.getValue() != "On"):
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "bitrate"):
					self.list.append(getConfigListEntry(_("Bitrate"), config.plugins.transcodingsetup.encoder[int(encoder)].bitrate))
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "framerate"):
					self.list.append(getConfigListEntry(_("Framerate"), config.plugins.transcodingsetup.encoder[int(encoder)].framerate))
			
			if checkSupportAdvanced() and self.setupMode != "Normal":
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "resolution"):
					self.list.append(getConfigListEntry(_("Resolution"), config.plugins.transcodingsetup.encoder[int(encoder)].resolution))
			
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "aspectratio"):
					self.list.append(getConfigListEntry(_("Aspect Ratio"), config.plugins.transcodingsetup.encoder[int(encoder)].aspectratio))
			
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "audiocodec"):
					self.list.append(getConfigListEntry(_("Audio codec"), config.plugins.transcodingsetup.encoder[int(encoder)].audiocodec))
			
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "videocodec"):
					self.list.append(getConfigListEntry(_("Video codec"), config.plugins.transcodingsetup.encoder[int(encoder)].videocodec))
			
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "gopframe"):
					self.list.append(getConfigListEntry(_("GOP Frame B"), config.plugins.transcodingsetup.encoder[int(encoder)].gopframeb))
			
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "gopframep"):
					self.list.append(getConfigListEntry(_("GOP Frame P"), config.plugins.transcodingsetup.encoder[int(encoder)].gopframep))
			
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "level"):
					self.list.append(getConfigListEntry(_("Level"), config.plugins.transcodingsetup.encoder[int(encoder)].level))
			
				if hasattr(config.plugins.transcodingsetup.encoder[int(encoder)], "profile"):
					self.list.append(getConfigListEntry(_("Profile"), config.plugins.transcodingsetup.encoder[int(encoder)].profile))

		self["config"].list = self.list
		self["config"].l.setList(self.list)
		if not self.showDescription in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.showDescription)

	def showDescription(self):
		configName = "<%s>\n"%self["config"].getCurrent()[0]
		current = self["config"].getCurrent()[1]
		className = self["config"].getCurrent()[1].__class__.__name__
		text = ""
		if className == "ConfigSelection" or className == "TconfigSelection":
			text = configName
			for choice in current.choices.choices:
				if text == configName:	
					text += choice[1]
				else:
					text += ', ' + choice[1]
		elif className == "ConfigInteger" or className == "TconfigInteger":
			limits = current.limits[0]
			text = configName
			text += "%s : %d, %s : %d" % (_("Min"), limits[0], _("Max"), limits[1])
		self["description"].setText(text)

	def showMessage(self, msg, msgType = MessageBox.TYPE_ERROR):
		self.session.open(MessageBox, _(msg), msgType)

	def saveAll(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()

	def keySave(self):
		self.saveAll()
		transcodingsetupinit.setPort(config.plugins.transcodingsetup.port)
		self.close()

	def KeyDefault(self):
		for x in self["config"].list:
			x[1].setValue(x[1].default)
		self.createSetup()

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		transcodingsetupinit.pluginsetup = None
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def keyBlue(self):
		if not checkSupportAdvanced():
			return
		if self.setupMode == "Normal":
			self.setupMode = "Advanced"
			self["key_blue"].setText(_("Normal"))
		else:
			self.setupMode = "Normal"
			self["key_blue"].setText(_("Advanced"))
		self.createSetup()

	# for summary:
	def changedEntry(self):
		print 'self.onChangedEntry',self.onChangedEntry
		for x in self.onChangedEntry:
			x()
		self.createSetup()
	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

def main(session, **kwargs):
	session.open(TranscodingSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("TranscodingSetup"), description=_("Transcoding Setup"), where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

transcodingsetupinit = TranscodingSetupInit()

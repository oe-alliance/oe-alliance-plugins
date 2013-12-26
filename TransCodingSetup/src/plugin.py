from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger, integer_limits
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import SystemInfo
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from enigma import eTimer, getDesktop
from os import system as os_system, path as os_path, listdir as os_listdir
from __init__ import _

class TconfigSelection(ConfigSelection):
	def __init__(self, encoder, choices, default = None):
		self.encoder = encoder
		ConfigSelection.__init__(self, choices, default)

class TconfigInteger(ConfigInteger):
	def __init__(self, encoder, default, limits = integer_limits):
		self.encoder = encoder
		ConfigInteger.__init__(self, default, limits)

def getModel():
	filename = "/proc/stb/info/vumodel"
	if fileExists(filename):
		return file(filename).read().strip()
	return ""

def getProcValue(procPath):
	fd = open(procPath,'r')
	curValue = fd.read().strip(' ').strip('\n')
	fd.close()
#	print "[TranscodingSetup] get %s from %s" % (curValue, procPath)
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
	if fileExists( getProcPath(0, "aspectratio") ):
		return True
	return False

config.plugins.transcodingsetup = ConfigSubsection()
config.plugins.transcodingsetup.transcoding = ConfigSelection(default = "enable", choices = [ ("enable", _("enable")), ("disable", _("disable"))] )
config.plugins.transcodingsetup.port = ConfigSelection(default = "8002", choices = [ ("8001", "8001"), ("8002", "8002")] )

def getAttr(attr, encoder):
	return getattr(config.plugins.transcodingsetup, encoder == '0' and attr or "%s_%s"%(attr, encoder))

def hasAttr(attr, encoder):
	return hasattr(config.plugins.transcodingsetup, encoder == '0' and attr or "%s_%s"%(attr, encoder))

def setAttr(attr, encoder, value):
	setattr(config.plugins.transcodingsetup, encoder == '0' and attr or "%s_%s"%(attr, encoder), value)

def createTransCodingConfig(encoder):
	if fileExists( getProcPath(encoder ,"bitrate") ):
		if getModel() == "solo2":
			choice = TconfigInteger(encoder, default = 400000, limits = (50000, 1000000))
		else:
			choice = TconfigInteger(encoder, default = 2000000, limits = (100000, 10000000))
		setAttr("bitrate", encoder, choice)

	if fileExists( getProcPath(encoder ,"framerate") ):
		choice = TconfigSelection(encoder, default = "30000", choices = [ ("23976", _("23976")), ("24000", _("24000")), ("25000", _("25000")), ("29970", _("29970")), ("30000", _("30000")), ("50000", _("50000")), ("59940", _("59940")), ("60000", _("60000"))] )
		setAttr("framerate", encoder, choice)

	if checkSupportAdvanced() and (hasAttr("bitrate", encoder) or hasAttr("framerate", encoder)):
		choice = TconfigSelection(encoder, default = "Off", choices = [ ("On", _("On")), ("Off", _("Off")) ] )
		setAttr("automode", encoder, choice)

	if fileExists( getProcPath(encoder, "resolution") ):
		choice = TconfigSelection(encoder, default = "480p", choices = [ ("480p", _("480p")), ("576p", _("576p")), ("720p", _("720p")), ("320x240", _("320x240")), ("160x120", _("160x120")) ] )
		setAttr("resolution", encoder, choice)

	if fileExists( getProcPath(encoder, "aspectratio") ):
		choice = TconfigSelection(encoder, default = "1", choices = [ ("0", _("auto")), ("1", _("4x3")), ("2", _("16x9")) ] )
		setAttr("aspectratio", encoder, choice)

	if fileExists( getProcPath(encoder, "audiocodec") ):
		choice = TconfigSelection(encoder, default = "aac", choices = [("mpg", _("mpg")), ("mp3", _("mp3")), ("aac", _("aac")), ("aac+", _("aac+")), ("aac+loas", _("aac+loas")), ("aac+adts", _("aac+adts")), ("ac3", _("ac3"))] )
		setAttr("audiocodec", encoder, choice)

	if fileExists( getProcPath(encoder, "videocodec") ):
		choice = TconfigSelection(encoder, default = "h264", choices = [ ("h264", _("h264")) ] )
		setAttr("videocodec", encoder, choice)

	if fileExists( getProcPath(encoder, "gopframeb") ):
		choice = TconfigInteger(encoder, default = 0, limits = (0, 60))
		setAttr("gopframeb", encoder, choice)

	if fileExists( getProcPath(encoder, "gopframep") ):
		choice = TconfigInteger(encoder, default = 29, limits = (0, 60))
		setAttr("gopframep", encoder, choice)

	if fileExists( getProcPath(encoder, "level") ):
		choice = TconfigSelection(encoder, default = "3.1", choices = [("1.0", _("1.0")), ("2.0", _("2.0")),
			("2.1", _("2.1")), ("2.2", _("2.2")), ("3.0", _("3.0")), ("3.1", _("3.1")),
			("3.2", _("3.2")), ("4.0", _("4.0")), ("4.1", _("4.1")), ("4.2", _("4.2")),
			("5.0", _("5.0")), ("low", _("low")), ("main", _("main")), ("high", _("high"))] )
		setAttr("level", encoder, choice)

	if fileExists( getProcPath(encoder, "profile") ):
		choice = TconfigSelection(encoder, default = "baseline", choices = [("baseline", _("baseline")), ("simple", _("simple")), ("main", _("main")), ("high", _("high")), ("advanced simple", _("advancedsimple"))] )
		setAttr("profile", encoder, choice)

# check encoders
encoders = []
encoderPath = "/proc/stb/encoder"
for encoder in os_listdir(encoderPath):
	encPath = os_path.join(encoderPath, encoder)
	if not os_path.isdir(encPath):
		continue
	if fileExists(os_path.join(encPath, "bitrate")):
		encoders.append(encoder)
		createTransCodingConfig(encoder)

if len(encoders) > 1:
	encoders.sort()
	choices = []
	for encoder in encoders:
		choices.append((encoder, encoder))
	config.plugins.transcodingsetup.encoder = ConfigSelection(default = '0', choices = choices )

transcodingsetupinit = None
class TranscodingSetupInit:
	def __init__(self):
		self.pluginsetup = None
		config.plugins.transcodingsetup.port.addNotifier(self.setPort)

		for encoder in encoders:
			if hasAttr("automode", encoder):
				if getAttr("automode", encoder).value == "On":
					getAttr("automode", encoder).addNotifier(self.setAutomode)

					if hasAttr("bitrate", encoder):
						getAttr("bitrate", encoder).addNotifier(self.setBitrate, False)

					if hasAttr("framerate", encoder):
						getAttr("framerate", encoder).addNotifier(self.setFramerate, False)

				else: # autoMode Off
					getAttr("automode", encoder).addNotifier(self.setAutomode, False)
					if hasAttr("bitrate", encoder):
						getAttr("bitrate", encoder).addNotifier(self.setBitrate)

					if hasAttr("framerate", encoder):
						getAttr("framerate", encoder).addNotifier(self.setFramerate)

			if hasAttr("resolution", encoder):
				getAttr("resolution", encoder).addNotifier(self.setResolution)

			if hasAttr("aspectratio", encoder):
				getAttr("aspectratio", encoder).addNotifier(self.setAspectRatio)

			if hasAttr("audiocodec", encoder):
				getAttr("audiocodec", encoder).addNotifier(self.setAudioCodec)

			if hasAttr("videocodec", encoder):
				getAttr("videocodec", encoder).addNotifier(self.setVideoCodec)

			if hasAttr("gopframeb", encoder):
				getAttr("gopframeb", encoder).addNotifier(self.setGopFrameB)

			if hasAttr("gopframep", encoder):
				getAttr("gopframep", encoder).addNotifier(self.setGopFrameP)

			if hasAttr("level", encoder):
				getAttr("level", encoder).addNotifier(self.setLevel)

			if hasAttr("profile", encoder):
				getAttr("profile", encoder).addNotifier(self.setProfile)

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
#				print "[TranscodingSetup] set %s "%procPath, value
				setProcValue(procPath, value)
				setValue = getProcValue(procPath)
				if value != setValue:
					print "[TranscodingSetup] set failed. (%s > %s)" % ( value, procPath )
					return -1
				return 0
		except:
			print "setConfig exception error (%s > %s)" % ( value, procPath )
			return -1
		return 0

	def setPort(self, configElement):
		port = configElement.value
		port2 = (port == "8001") and "8002" or "8001"

#		print "[TranscodingSetup] set port ",port
		try:
			newConfigData = ""
			oldConfigData = file('/etc/inetd.conf').read()
			for L in oldConfigData.splitlines():
				try:
					if L[0] == '#':
						newConfigData += L + '\n'
						continue
				except: continue
				LL = L.split()
				if LL[5] == '/usr/bin/streamproxy':
					LL[0] = port2
				elif LL[5] == '/usr/bin/transtreamproxy':
					LL[0] = port
				newConfigData += ''.join(str(X) + " " for X in LL) + '\n'

			if newConfigData.find("transtreamproxy") == -1:
				newConfigData += port + " stream tcp nowait root /usr/bin/transtreamproxy transtreamproxy\n"
			file('/etc/inetd.conf', 'w').write(newConfigData)
		except:
			self.showMessage("Set port failed.", MessageBox.TYPE_ERROR)
			return

		self.inetdRestart()
		if port == "8001":
			msg = "Set port OK.\nPC Streaming is replaced with mobile streaming."
			self.showMessage(msg, MessageBox.TYPE_INFO)

	def setupConfig(self, configElement, procPath):
#		print "[TranscodingSetup] set %s to %s" % ( procPath, configElement.value )
		configValue = configElement.value
		if self.setConfig(procPath, configValue):
			# set config failed, reset to current proc value
			self.getConfigFromProc(procPath, configElement)
			self.showMessage("Set %s failed." % (procPath), MessageBox.TYPE_ERROR)

	def getConfigFromProc(self, procPath, configElement):
		curValue = getProcValue(procPath)
		if isinstance(configElement.value, int): # is int ?
			curValue = int(curValue)
		configElement.value = curValue
		configElement.save()

	def setAutomode(self, configElement):
		configName = "AutoMode"
#		print "[TranscodingSetup]  setAutomode, configName %s, value %s" % ( configName, configElement.value )
		if configElement.value == "On":
			autoValue = str(-1)
			if ((hasAttr("bitrate", configElement.encoder) and
					self.setConfig(getProcPath(configElement.encoder ,"bitrate"), autoValue) ) or
					(hasAttr("framerate", configElement.encoder) and
					self.setConfig(getProcPath(configElement.encoder ,"framerate"), autoValue) ) ):
				configElement.value = "Off" # set config failed, reset to previous value
				configElement.save()
				self.showMessage("Set %s failed." % (configName), MessageBox.TYPE_ERROR)
		else: # Off
			if hasAttr("bitrate", configElement.encoder):
				self.setBitrate(getAttr("bitrate", configElement.encoder))
			if hasAttr("framerate", configElement.encoder):
				self.setFramerate(getAttr("framerate", configElement.encoder))

	def setBitrate(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"bitrate"))

	def setFramerate(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"framerate"))

	def setResolution(self, configElement):
		resolution = configElement.value
		if resolution in [ "320x240", "160x120" ]:
			(width, height) = tuple(resolution.split('x'))
			self.setConfig(getProcPath(configElement.encoder ,"resolution"), "custom")
			self.setConfig(getProcPath(configElement.encoder ,"width"), width)
			self.setConfig(getProcPath(configElement.encoder ,"height"), height)
		else:
			self.setupConfig(configElement, getProcPath(configElement.encoder ,"resolution"))

	def setAspectRatio(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"aspectratio"))

	def setAudioCodec(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"audiocodec"))

	def setVideoCodec(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"videocodec"))

	def setGopFrameB(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"gopframeb"))

	def setGopFrameP(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"gopframep"))

	def setLevel(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"level"))

	def setProfile(self, configElement):
		self.setupConfig(configElement, getProcPath(configElement.encoder ,"profile"))

	def inetdRestart(self):
		if fileExists("/etc/init.d/inetd"):
			os_system("/etc/init.d/inetd restart")
		elif fileExists("/etc/init.d/inetd.busybox"):
			os_system("/etc/init.d/inetd.busybox restart")

	def showMessage(self, msg, msgType):
		if self.pluginsetup:
			self.pluginsetup.showMessage(msg, msgType)

class TranscodingSetup(Screen, ConfigListScreen):
	size = getDesktop(0).size()
	if checkSupportAdvanced():
		if size.width() > 750:
			size_h = 450
		else:
			size_h = 370
	else:
		size_h = 280

	pos_h = ( size_h , size_h - 150 , (size_h - 150) + 70, (size_h - 150) + 70 + 60 )
	skin_advanced =  """
		<screen position="center,center" size="600,%d">
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="455,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="25,70" size="560,%d" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="description" render="Label" position="20,%d" size="540,60" font="Regular;20" halign="center" valign="center" />
			<widget source="text" render="Label" position="20,%d" size="540,20" font="Regular;22" halign="center" valign="center" />
		</screen>
		""" % pos_h

	skin_normal =  """
		<screen position="center,center" size="600,%d">
			<ePixmap pixmap="skin_default/buttons/red.png" position="40,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="230,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="40,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="230,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="25,70" size="560,%d" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="description" render="Label" position="20,%d" size="540,60" font="Regular;20" halign="center" valign="center" />
			<widget source="text" render="Label" position="20,%d" size="540,20" font="Regular;22" halign="center" valign="center" />
		</screen>
		""" % pos_h

	def __init__(self,session):
		Screen.__init__(self,session)
		self.session = session
		self.setTitle(_("Transcoding Setup"))

		if checkSupportAdvanced():
			self.skin = TranscodingSetup.skin_advanced
		else:
			self.skin = TranscodingSetup.skin_normal

		if getModel() == "solo2":
			TEXT = _("Transcoding and PIP are mutually exclusive.")
		else:
			TEXT = _("2nd transcoding and PIP are mutually exclusive.")
		self["text"] = StaticText(_("%s")%TEXT)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Default"))
		if checkSupportAdvanced():
			self["key_blue"] = StaticText(_("Advanced"))
		else:
			self["key_blue"] = StaticText("")
		self["description"] = StaticText(_("Transcoding Setup"))

		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"cancel"	: self.keyCancel,
			"red"		: self.keyCancel,
			"green"		: self.keySave,
			"yellow" 	: self.KeyDefault,
			"blue" 		: self.keyBlue,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self.setupMode = "Normal" # Normal / Advanced
		self.encoder = None
		self.automode = None
		self.createSetup()
		self.onLayoutFinish.append(self.checkEncoder)
		self.invaliedModelTimer = eTimer()
		self.invaliedModelTimer.callback.append(self.invalidmodel)
		global transcodingsetupinit
		transcodingsetupinit.pluginsetup = self
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
			self.encoder = getConfigListEntry(_("Encoder"), config.plugins.transcodingsetup.encoder)
			self.list.append( self.encoder )
			encoder = config.plugins.transcodingsetup.encoder.value			

		if encoder is not None:
			self.automode = None
			if checkSupportAdvanced() and hasAttr('automode', encoder):
				self.automode = getConfigListEntry(_("Auto set Framerate / Bitrate"), getAttr('automode', encoder))

			if self.automode is not None:
				self.list.append( self.automode )

			if not ( hasAttr('automode', encoder) and getAttr('automode', encoder).value == "On" ):
				if hasAttr('bitrate', encoder):
					self.list.append(getConfigListEntry(_("Bitrate"), getAttr('bitrate', encoder)))
				if hasAttr('framerate', encoder):
					self.list.append(getConfigListEntry(_("Framerate"), getAttr('framerate', encoder)))

			if hasAttr('resolution', encoder):
					self.list.append(getConfigListEntry(_("Resolution"), getAttr('resolution', encoder)))

			if checkSupportAdvanced() and self.setupMode != "Normal":
				if hasAttr('aspectratio', encoder):
					self.list.append(getConfigListEntry(_("Aspect Ratio"), getAttr('aspectratio', encoder)))

				if hasAttr('audiocodec', encoder):
					self.list.append(getConfigListEntry(_("Audio codec"), getAttr('audiocodec', encoder)))

				if hasAttr('videocodec', encoder):
					self.list.append(getConfigListEntry(_("Video codec"), getAttr('videocodec', encoder)))

				if hasAttr('gopframe', encoder):
					self.list.append(getConfigListEntry(_("GOP Frame B"), getAttr('gopframeb', encoder)))

				if hasAttr('gopframep', encoder):
					self.list.append(getConfigListEntry(_("GOP Frame P"), getAttr('gopframep', encoder)))

				if hasAttr('level', encoder):
					self.list.append(getConfigListEntry(_("Level"), getAttr('level', encoder)))

				if hasAttr('profile', encoder):
					self.list.append(getConfigListEntry(_("Profile"), getAttr('profile', encoder)))

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
		configs = config.plugins.transcodingsetup.dict()
		for (configName, configElement) in configs.items():
			configElement.save()

	def keySave(self):
		self.saveAll()
		self.close()

	def KeyDefault(self):
		configs = config.plugins.transcodingsetup.dict()
		for (configName, configElement) in configs.items():
			if configName.startswith("automode"):
				continue
			configElement.value = configElement.default

		for (configName, configElement) in configs.items():
			if configName.startswith("automode"):
				configElement.value = configElement.default

		self.createSetup()

	def keyBlue(self):
		if not checkSupportAdvanced():
			return
		if self.setupMode == "Normal":
			self.setupMode = "Advanced"
			self["key_blue"].setText( _("Normal") )
		else:
			self.setupMode = "Normal"
			self["key_blue"].setText( _("Advanced") )
		self.createSetup()

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self.encoder is not None and (self["config"].getCurrent() == self.encoder) or self.automode is not None and (self["config"].getCurrent() == self.automode):
			self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self.encoder is not None and (self["config"].getCurrent() == self.encoder) or self.automode is not None and (self["config"].getCurrent() == self.automode):
			self.createSetup()

	def cancelConfirm(self, result):
		if not result:
			return

		configs = config.plugins.transcodingsetup.dict()

		for (configName, configElement) in configs.items():
			if configName.startswith("automode"):
				continue
			configElement.cancel()

		for (configName, configElement) in configs.items():
			if configName.startswith("automode"):
				configElement.cancel()

		self.close()

	def keyCancel(self):
		transcodingsetupinit.pluginsetup = None
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

def main(session, **kwargs):
	session.open(TranscodingSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("TranscodingSetup"), description=_("Transcoding Setup"), where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

transcodingsetupinit = TranscodingSetupInit()

if getModel() == "duo2":
	SystemInfo["SimpleTranscoding"] = False
	SystemInfo["AdvancedTranscoding"] = True
elif getModel() == "solo2":
	SystemInfo["SimpleTranscoding"] = True
	SystemInfo["AdvancedTranscoding"] = False
else:
	SystemInfo["SimpleTranscoding"] = False
	SystemInfo["AdvancedTranscoding"] = False

from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists

AUDIOEFFECT_PROC_PATH = {
	"3D_SURROUND"					: "/proc/stb/audio/3d_surround",
	"AVL"							: "/proc/stb/audio/avl",
	"3D_SURROUND_CHOICE"			: "/proc/stb/audio/3d_surround_choices",
	"AVL_CHOICE"					: "/proc/stb/audio/avl_choices",
	"3D_SURROUND_SPEAKER_POSITION"			: "/proc/stb/audio/3d_surround_speaker_position",
	"3D_SURROUND_SPEAKER_POSITION_CHOICE"	: "/proc/stb/audio/3d_surround_speaker_position_choices"
}

AUDIOOUT_ENTRY_NAME = {
	"dac"	:	"Analog Audio"
}

AUDIOEFFECT_DEFAULT = "none"
AUDIOOUT_DEFAULT = "off"
SPEAKER_POSITION_DEFAULT = "wide"

SUPPORT_AUDIOEFFECT = False
SUPPORT_3D_SURROUND = False
SUPPORT_3D_SURROUND_SPEAKER_POSITION = False
SUPPORT_AVL = False

if fileExists(AUDIOEFFECT_PROC_PATH["3D_SURROUND"]) and fileExists(AUDIOEFFECT_PROC_PATH["3D_SURROUND_CHOICE"]):
	SUPPORT_3D_SURROUND = True

if SUPPORT_3D_SURROUND is True:
	if fileExists(AUDIOEFFECT_PROC_PATH["3D_SURROUND_SPEAKER_POSITION"]) and fileExists(AUDIOEFFECT_PROC_PATH["3D_SURROUND_SPEAKER_POSITION_CHOICE"]):
		SUPPORT_3D_SURROUND_SPEAKER_POSITION = True

if fileExists(AUDIOEFFECT_PROC_PATH["AVL"]) and fileExists(AUDIOEFFECT_PROC_PATH["AVL_CHOICE"]):
	SUPPORT_AVL = True

if SUPPORT_3D_SURROUND or SUPPORT_AVL:
	SUPPORT_AUDIOEFFECT = True

def getProcValue(procPath):
	fd = open(procPath, 'r')
	curValue = fd.read().strip(' ').strip('\n')
	fd.close()
#	print "[AudioEffect] get %s from %s" % (curValue, procPath)
	return curValue

def setProcValue(procPath, value):
#	print "[AudioEffect] set %s to %s" % (value, procPath)
	fd = open(procPath, 'w')
	fd.write(value)
	fd.close()

def setConfigValue(procPath, value):
#	print "[AudioEffect][setConfigValue] try set %s to %s" % (value, procPath)
	curValue = getProcValue(procPath)
	if curValue != value:
		setProcValue(procPath, value)
	return 0

def getEffectChoices():
	choices = [ ("none", _("none")) ]
	if SUPPORT_3D_SURROUND :
		choices.append( ("3D_Surround", _("3D Surround") ) )
	if SUPPORT_AVL :
		choices.append( ("AVL", _("AVL (Automatic Volume Leveler)") ) )
	return choices

def getAudioOutTypes():
	if SUPPORT_3D_SURROUND:
		data = getProcValue(AUDIOEFFECT_PROC_PATH["3D_SURROUND_CHOICE"])
	elif SUPPORT_AVL:
		data = getProcValue(AUDIOEFFECT_PROC_PATH["AVL_CHOICE"])
	aTypes = []
	for aType in data.split(' '):
		if aType == "none":
			continue
		aTypes.append( aType )
	return aTypes

if SUPPORT_AUDIOEFFECT:
	AUDIOOUT_TYPES = getAudioOutTypes()

def getSpeakerPosition():
	choices = []
	data = getProcValue(AUDIOEFFECT_PROC_PATH["3D_SURROUND_SPEAKER_POSITION_CHOICE"])
	for choice in data.split(' '):
		choices.append( (choice, _(choice)) )
	return choices

config.plugins.audioeffect = ConfigSubsection()
config.plugins.audioeffect.effect = ConfigSelection( default = AUDIOEFFECT_DEFAULT, choices = getEffectChoices() )
if SUPPORT_AUDIOEFFECT:
	for aout in AUDIOOUT_TYPES:
		setattr(config.plugins.audioeffect, aout, ConfigSelection( default = AUDIOOUT_DEFAULT, choices = [("on", _("On")), ("off", _("Off"))] ) )
	if SUPPORT_3D_SURROUND_SPEAKER_POSITION:
		config.plugins.audioeffect.speakerposition = ConfigSelection( default = SPEAKER_POSITION_DEFAULT, choices = getSpeakerPosition() )

def setAudioEffectConfigs():
		if not SUPPORT_AUDIOEFFECT:
			return
		_3DSurroundValue = None
		_AvlValue = None
		if config.plugins.audioeffect.effect.value == "none":
			_3DSurroundValue = "none"
			_AvlValue = "none"
		elif SUPPORT_AUDIOEFFECT:
			_audioOnList = []
			for aout in AUDIOOUT_TYPES:
				if getattr(config.plugins.audioeffect, aout).value == "on":
					_audioOnList.append(aout)
			if _audioOnList:
				audioOnList = ' '.join(_audioOnList)
			else:
				audioOnList = "none"
			if config.plugins.audioeffect.effect.value == "3D_Surround":
				_3DSurroundValue = audioOnList
				_AvlValue = "none"
			elif config.plugins.audioeffect.effect.value == "AVL":
				_3DSurroundValue = "none"
				_AvlValue = audioOnList

		if SUPPORT_3D_SURROUND:
			setConfigValue(AUDIOEFFECT_PROC_PATH["3D_SURROUND"], _3DSurroundValue)
		if SUPPORT_AVL:
			setConfigValue(AUDIOEFFECT_PROC_PATH["AVL"], _AvlValue)
		if SUPPORT_3D_SURROUND_SPEAKER_POSITION:
			if _3DSurroundValue == "none" :
				config.plugins.audioeffect.speakerposition.value = config.plugins.audioeffect.speakerposition.default
			_3DSpeakerPosition = config.plugins.audioeffect.speakerposition.value
			setConfigValue(AUDIOEFFECT_PROC_PATH["3D_SURROUND_SPEAKER_POSITION"], _3DSpeakerPosition)

class AudioEffect(Screen, ConfigListScreen):
	skin =  """
		<screen position="center,center" size="540,300">
			<ePixmap pixmap="skin_default/buttons/red.png" position="30,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="200,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="370,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="30,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="200,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="370,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="20,70" size="500,170" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="description" render="Label" position="30,240" size="480,60" font="Regular;18" halign="center" valign="center" />
		</screen>
	"""

	def __init__(self, session):		
		Screen.__init__(self, session)
		self.setTitle(_("Audio Effect Setup"))
		self.skin = AudioEffect.skin

		self.session = session

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Default"))
		self["description"] = StaticText(_("Audio Effect Setup is not supported."))

		self["shortcuts"] = ActionMap(["AudioEffectActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.keyDefault,
		}, -2)

		self.setupList = []
		ConfigListScreen.__init__(self, self.setupList, session = self.session)
		self.configEffect = None
		self.createSetup()

	def createSetup(self):
		if not SUPPORT_AUDIOEFFECT:
			return
		self.setupList = []
		self.configEffect = getConfigListEntry(_("Effect"), config.plugins.audioeffect.effect)
		self.setupList.append(self.configEffect)
		if config.plugins.audioeffect.effect.value != "none" :
			for aout in AUDIOOUT_TYPES:
				entryName = AUDIOOUT_ENTRY_NAME.get(aout, aout.upper())
				self.setupList.append(getConfigListEntry(_(entryName), getattr(config.plugins.audioeffect, aout)))
			if config.plugins.audioeffect.effect.value == "3D_Surround" and SUPPORT_3D_SURROUND_SPEAKER_POSITION is True:
				self.setupList.append(getConfigListEntry(_("3D Surround Speaker Position"), config.plugins.audioeffect.speakerposition))
		self["config"].list = self.setupList
		self["config"].l.setList(self.setupList)
		if not self.showDescription in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.showDescription)

	def keySave(self):
		self.saveAll()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		setAudioEffectConfigs()
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		setAudioEffectConfigs()
		self.createSetup()

	def cancelConfirm(self, result):
		if not result:
			return

		for x in self["config"].list:
			x[1].cancel()
		setAudioEffectConfigs()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def keyDefault(self):
		for (configName, configElement) in config.plugins.audioeffect.dict().items():
			configElement.value = configElement.default
		setAudioEffectConfigs()
		self.createSetup()

	def showDescription(self):
		def getClassName(C):
			return C.__class__.__name__

		configName = "<%s>\n"%self["config"].getCurrent()[0]
		currentConfig = self["config"].getCurrent()[1]
		className = getClassName(currentConfig)
		text = ""
		if className == "ConfigSelection":
			text = configName
			for choice in currentConfig.choices.choices:
				if text == configName:	
					text += choice[1]
				else:
					text += ', ' + choice[1]
		self["description"].setText( _(text) )

def main(session, **kwargs):
	session.open(AudioEffect)

def OnSessionStart(session, **kwargs):
	setAudioEffectConfigs()

def Plugins(**kwargs):
	if SUPPORT_AUDIOEFFECT:
		return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=OnSessionStart),
				PluginDescriptor(name=_("AudioEffect"), description=_("sets the audio effetcs"), where = PluginDescriptor.WHERE_AUDIOMENU, fnc=main)]
	else:
		return []
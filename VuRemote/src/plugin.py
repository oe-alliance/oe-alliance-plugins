from __future__ import print_function
# for localized messages
from . import _

from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, configfile, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigYesNo
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Tools.Directories import fileExists
from enigma import eTimer
try:
	from Components.SystemInfo import BoxInfo
	IMAGEDISTRO = BoxInfo.getItem("distro")
	MODEL = BoxInfo.getItem("machinebuild")
except:
	from boxbranding import getImageDistro, getBoxType
	IMAGEDISTRO = getImageDistro()
	MODEL = getBoxType()


def getRcuDefaultType():
	if MODEL in ["vuultimo4k"]:
		return "type5"
	elif MODEL in ["vuuno4kse", "vuzero4k", "vuduo4k", "vuduo4kse"]:
		return "type6"
	return "legacy"


config.misc.remotecontrol_text_support = ConfigYesNo(default=True)

config.plugins.remotecontrolcode = ConfigSubsection()
if MODEL in ("vusolo", "vuduo"):
	config.plugins.remotecontrolcode.systemcode = ConfigSelection(default="1", choices=[("1", "1 "), ("2", "2 "), ("3", "3 "), ("4", "4 ")])
else:
	config.plugins.remotecontrolcode.systemcode = ConfigSelection(default="2", choices=[("1", "1 "), ("2", "2 "), ("3", "3 "), ("4", "4 ")])
config.plugins.remotecontrolcode.rcuType = ConfigSelection(default=getRcuDefaultType(), choices=[("legacy", "Legacy Vu+ Universal RCU"), ("type5", "New Vu+ Bluetooth RCU"), ("type6", "New Vu+ Type 6 RCU")])


class RemoteControlCodeInit:
	def __init__(self):
		self.setSystemCode(int(config.plugins.remotecontrolcode.systemcode.value))

	def setSystemCode(self, type=2):
		if not fileExists("/proc/stb/fp/remote_code"):
			return -1
		print("[RemoteControlCode] Write Remote Control Code : %d" % type)
		f = open("/proc/stb/fp/remote_code", "w")
		f.write("%d" % type)
		f.close()
		return 0

	def getModel(self):
		if MODEL in ("vuuno", "vuultimo", "vusolo2", "vuduo2", "vusolose", "vuzero", "vusolo4k", "vuuno4k", "vuuno4kse", "vuzero4k", "vuultimo4k", "vuduo4k", "vuduo4kse"):
			return True
		else:
			return False


class RemoteControlCode(Screen, ConfigListScreen, RemoteControlCodeInit):
	skin = """
		<screen position="center,center" size="400,250" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="30,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="230,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="30,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="230,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="5,70" size="380,180" scrollbarMode="showOnDemand" transparent="1" />
		</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ['RemoteControlCode', 'Setup']
		self.session = session
		Screen.setTitle(self, _("Remote Control Code"))
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions"],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
		}, -2)
		self.codestartup = config.plugins.remotecontrolcode.systemcode.value
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self.createSetup()
		self.onLayoutFinish.append(self.checkModel)
		self.checkModelTimer = eTimer()
		self.checkModelTimer.callback.append(self.invalidmodel)

	def checkModel(self):
		if not self.getModel():
			self.checkModelTimer.start(1000, True)

	def invalidmodel(self):
		self.session.openWithCallback(self.close, MessageBox, _("Sorry, but %s is not supported.") % MODEL, MessageBox.TYPE_ERROR)

	def createSetup(self):
		self.list = []
		self.rcuTypeEntry = getConfigListEntry(_("Remote Control Type"), config.plugins.remotecontrolcode.rcuType)
		self.rcsctype = getConfigListEntry(_("Remote Control System Code"), config.plugins.remotecontrolcode.systemcode)
		self.list.append(self.rcuTypeEntry)
		self.list.append(self.rcsctype)
		if IMAGEDISTRO in ("openvix", "openatv"):
			self.list.append(getConfigListEntry(_("Text support"), config.misc.remotecontrol_text_support))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keySave(self):
		config.misc.remotecontrol_text_support.save()
		configfile.save()
		if self.codestartup != config.plugins.remotecontrolcode.systemcode.value:
			print("[RemoteControlCode] Selected System Code : ", config.plugins.remotecontrolcode.systemcode.value)
			ret = self.setSystemCode(int(config.plugins.remotecontrolcode.systemcode.value))
			if ret == -1:
				self.restoreCode()
				self.session.openWithCallback(self.close, MessageBox, _("FILE NOT EXIST : /proc/stb/fp/remote_code"), MessageBox.TYPE_ERROR)
			else:
				msg = _("Please change your remote mode") + '\n'
				if config.plugins.remotecontrolcode.rcuType.value == "legacy":
					msg += _("Press and hold '2' & '7' until red LED is solid, then press 'Help', then press '000") + config.plugins.remotecontrolcode.systemcode.value + "'\n"
				else:
					msg += _("Press and hold <OK> and <STB> until red LED is solid, then press '0000") + config.plugins.remotecontrolcode.systemcode.value + "', then press <OK>\n"
				msg += _("Then choose 'Keep' within seconds")
				self.session.openWithCallback(self.MessageBoxConfirmCodeCallback, MessageBoxConfirmCode, msg)
		else:
			self.close()

	def restoreCode(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def MessageBoxConfirmCodeCallback(self, ret):
		if ret:
			ConfigListScreen.keySave(self)
		else:
			self.restoreCode()
			self.setSystemCode(int(config.plugins.remotecontrolcode.systemcode.value))


class MessageBoxConfirmCode(MessageBox):
	def __init__(self, session, text):
		MessageBox.__init__(self, session, text, MessageBox.TYPE_YESNO, timeout=60, default=False)
		self.list = [(_("Keep"), True), (_("Restore"), False)]
		self["list"].setList(self.list)


remotecontrolcodeinit = RemoteControlCodeInit()


def main(session, **kwargs):
	session.open(RemoteControlCode)


def RemoteControlSetup(menuid, **kwargs):
	if menuid == "system":
		return [(_("Remote Control Code"), main, "remotecontrolcode", 50)]
	else:
		return []


def Plugins(**kwargs):
	if fileExists("/proc/stb/fp/remote_code"):
		from Plugins.Plugin import PluginDescriptor
		return [PluginDescriptor(name=_("Remote Control Code"), where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=RemoteControlSetup)]
	return []

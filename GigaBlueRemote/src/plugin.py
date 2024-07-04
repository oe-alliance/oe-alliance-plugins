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
	MACHINEBUILD = BoxInfo.getItem("model")
	MODEL = BoxInfo.getItem("machinebuild")
except:
	from boxbranding import getImageDistro, getMachineBuild, getBoxType
	IMAGEDISTRO = getImageDistro()
	MACHINEBUILD = getMachineBuild()
	MODEL = getBoxType()


config.plugins.remotecontrolcode = ConfigSubsection()
config.plugins.remotecontrolcode.systemcode = ConfigSelection(default="50af", choices=[("50af", _("Code 1")), ("51ae", _("Code 2"))])


class RemoteControlCodeInit:
	def __init__(self):
		self.setSystemCode(config.plugins.remotecontrolcode.systemcode.value)

	def setSystemCode(self, type):
		if not fileExists("/proc/stb/ir/rc/customcode"):
			return -1
		print("[RemoteControlCode] Write Remote Control Code : ", type)
		f = open("/proc/stb/ir/rc/customcode", "w")
		f.write(type)
		f.close()
		return 0

	def getModel(self):
		if MACHINEBUILD in ("gb7252", "gb7356", "gb73625", "gb7362", "gb7358", "gbmv200"):
			return True
		else:
			return False


class RemoteControlCode(ConfigListScreen, Screen, RemoteControlCodeInit):
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
		self.rcsctype = getConfigListEntry(_("Remote Control Code:"), config.plugins.remotecontrolcode.systemcode)
		self.list.append(self.rcsctype)
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keySave(self):
		configfile.save()
		if self.codestartup != config.plugins.remotecontrolcode.systemcode.value:
			print("[RemoteControlCode] Selected System Code : ", config.plugins.remotecontrolcode.systemcode.value)
			ret = self.setSystemCode(config.plugins.remotecontrolcode.systemcode.value)
			if ret == -1:
				self.restoreCode()
				self.session.openWithCallback(self.close, MessageBox, _("FILE DOES NOT EXIST : /proc/stb/ir/rc/customcode"), MessageBox.TYPE_ERROR)
			else:
				self.session.openWithCallback(self.MessageBoxConfirmCodeCallback, MessageBoxConfirmCode, _("Please change now the mode on your RCU.") + '\n\n' + _("Press and hold 'GIGA' & '5' for 5 seconds.") + "\n" + _("Then choose 'Confirm' "))
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
			self.setSystemCode(config.plugins.remotecontrolcode.systemcode.value)


class MessageBoxConfirmCode(MessageBox):
	def __init__(self, session, text):
		MessageBox.__init__(self, session, text, MessageBox.TYPE_YESNO, timeout=60, default=False)
		self.list = [(_("Confirm"), True), (_("Cancel"), False)]
		self["list"].setList(self.list)


remotecontrolcodeinit = RemoteControlCodeInit()


def main(session, **kwargs):
	session.open(RemoteControlCode)


def RemoteControlSetup(menuid, **kwargs):
	if IMAGEDISTRO in ("teamblue"):
		if menuid != "devices_menu":
			return []
	else:
		if menuid != "system":
			return []
	return [(_("Remote Control Code"), main, "remotecontrolcode", 50)]


def Plugins(**kwargs):
	if fileExists("/proc/stb/ir/rc/customcode"):
		from Plugins.Plugin import PluginDescriptor
		return [PluginDescriptor(name=_("Remote Control Code"), where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=RemoteControlSetup)]
	return []

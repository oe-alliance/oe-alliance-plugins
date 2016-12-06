# for localized messages
from . import _

from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, configfile, ConfigSubList, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger, integer_limits, NoSave, ConfigSelectionNumber
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Button import Button
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from enigma import eTimer
from boxbranding import getMachineBuild
from os import path


config.plugins.transcodingsetup = ConfigSubsection()
config.plugins.transcodingsetup.transcoding = ConfigSelection(default = "enable", choices = [ ("enable", _("enable")), ("disable", _("disable"))])
if getMachineBuild() in ('ew7356','formuler1'):
	choice = ConfigSelection(default = "400000", choices=[("-1", "Auto"), ("50000", "50 Kbits"), ("100000", "100 Kbits"), ("150000", "150 Kbits"), ("200000", "200 Kbits"), ("250000", "250 Kbits"), ("300000", "300 Kbits"), ("350000", "350 Kbits"), ("400000", "400 Kbits"), ("450000", "450 Kbits"), ("500000", "500 Kbits"), ("600000", "600 Kbits"), ("700000", "700 Kbits"), ("800000", "800 Kbits"), ("900000", "900 Kbits"), ("1000000", "1 Mbits")])
	config.plugins.transcodingsetup.bitrate = choice
	choice = ConfigSelection(default = "50000", choices = [("-1", "Auto"), ("23976", "23.976 fps"), ("24000", "24 fps"), ("25000", "25 fps"), ("29970", "29.970 fps"), ("30000", "30 fps"), ("50000", "50 fps"), ("59940", "59.940 fps"), ("60000", "60 fps")])
	config.plugins.transcodingsetup.framerate = choice
else:
	choice = ConfigSelectionNumber(min = 100000, max = 10000000, stepwidth = 100000, default = 400000, wraparound = True)
	config.plugins.transcodingsetup.bitrate = choice
	choice = ConfigSelection(default = "50000", choices = [("23976", "23.976 fps"), ("24000", "24 fps"), ("25000", "25 fps"), ("29970", "29.970 fps"), ("30000", "30 fps"), ("50000", "50 fps"), ("59940", "59.940 fps"), ("60000", "60 fps")])
	config.plugins.transcodingsetup.framerate = choice
	choice = ConfigSelection(default = "854x480", choices = [ ("854x480", _("480p")), ("768x576", _("576p")), ("1280x720", _("720p")), ("320x240", _("320x240")), ("160x120", _("160x120")) ])
	config.plugins.transcodingsetup.resolution = choice
	config.plugins.transcodingsetup.aspectratio = ConfigSelection(default = "2", choices = [("0", _("4x3")), ("1", _("16x9")), ("2", _("Auto")) ])
	config.plugins.transcodingsetup.interlaced = ConfigSelection(default = "0", choices = [ ("1", _("Yes")), ("0", _("No"))])

class TranscodingSetup(Screen,ConfigListScreen):
	skin =  """
		<screen name="TranscodingSetup" position="center,center" size="900,500">
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="25,50" size="860,300" scrollbarMode="showOnDemand" transparent="1" />
			<widget name="description" position="20,200" size="840,70" font="Regular;17" halign="center" valign="center" />
			<widget name="HelpTextHeader1" position="10,300" size="880,22" font="Regular;19" halign="center" valign="center" foregroundColor="#ff0000"/>
			<widget name="HelpText1" position="10,330" size="880,110" font="Regular;16" halign="center" valign="center" foregroundColor="#ffffff"/>
			<widget name="HelpTextHeader2" position="10,440" size="880,22" font="Regular;19" halign="center" valign="center" foregroundColor="#ff0000"/>
			<widget name="HelpText2" position="10,470" size="880,20" font="Regular;16" halign="center" valign="center" foregroundColor="#ffffff"/>
		</screen>
		"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.session = session

		self.skinName = "TranscodingSetup"
		self.setup_title = _("Transcoding Setup")
		self.setTitle(self.setup_title)

		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)
		self.createSetup()

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText()
		self["key_blue"] = Button()

		self["description"] = Label()
		self["text"] = Label("")

		text =  (_("To use transcoding You can build URL for VLC by Yourself\n\n"))
		self["HelpTextHeader1"] = Label(text)

		text2 = "http://STB_IP:PORT/CH_REF:?bitrate=BITRATE?width=WIDTH?height=HEIGHT?aspectration=ASPECT?interlaced=0\n\ne.x:\n\n"
		text2 += "http://192.168.1.5:8001/1:0:1:C25:1E78:71:820000:0:0:0:?bitrate=300000?width=320?height=240?aspectratio=2?interlaced=0\n\n"
		self["HelpText1"] = Label(_(text2))

		text3 = (_("Transcoding from HDMI-IN e.x:\n\n"))
		self["HelpTextHeader2"] = Label(_(text3))

		text4 = "http://192.168.1.5:8001/8192:0:1:0:0:0:0:0:0:0:?bitrate=300000?width=720?height=480?aspectratio=2?interlaced=1"
		self["HelpText2"] = Label(_(text4))

		self.onLayoutFinish.append(self.checkEncoder)

		self.invaliedModelTimer = eTimer()
		self.invaliedModelTimer.callback.append(self.invalidmodel)

		self["config"].onSelectionChanged.append(self.showDescription)

	def checkEncoder(self):
		if not path.exists("/proc/stb/encoder"):
			self.invaliedModelTimer.start(100,True)

	def invalidmodel(self):
		self.session.openWithCallback(self.close, MessageBox, _("This model does not support transcoding."), MessageBox.TYPE_ERROR)

	def createSetup(self):
		self.list = []
		if getMachineBuild() in ('ew7356','formuler1'):
			self.list.append(getConfigListEntry(_("Bitrate in bits"), config.plugins.transcodingsetup.bitrate))
			self.list.append(getConfigListEntry(_("Framerate"), config.plugins.transcodingsetup.framerate))
		else:
			self.list.append(getConfigListEntry(_("Bitrate in bits"), config.plugins.transcodingsetup.bitrate))
			self.list.append(getConfigListEntry(_("Framerate"), config.plugins.transcodingsetup.framerate))
			self.list.append(getConfigListEntry(_("Resolution"), config.plugins.transcodingsetup.resolution))
			self.list.append(getConfigListEntry(_("Aspect Ratio"), config.plugins.transcodingsetup.aspectratio))
			self.list.append(getConfigListEntry(_("Interlaced"), config.plugins.transcodingsetup.interlaced))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

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
		elif className == "ConfigSelectionNumber":
			text = configName
			text += "min : 100 Kbits, max : 10 Mbits, step : 100 Kbits"

		text = str(text).split("\n")[1]
		self["description"].setText(_(text))

	def saveAll(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()

	def keySave(self):
		self.saveAll()
		self.close()

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

def main(session, **kwargs):
	session.open(TranscodingSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(
		name=_("Multi-Transcoding Setup"),
		description=_("Multi device transcoding setup"),
		where = PluginDescriptor.WHERE_PLUGINMENU,
		needsRestart = False,
		icon="./plugin.png",
		fnc=main)]

from __future__ import print_function
# for localized messages
from . import _

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.Console import Console
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList
from Components.config import config, configfile, ConfigSubsection, getConfigListEntry, ConfigSelection
from Components.ConfigList import ConfigListScreen

from boxbranding import getMachineBuild

import Screens.Standby

config.plugins.booster = ConfigSubsection()
if getMachineBuild() in ("spark"):
	config.plugins.booster.startfrequenz = ConfigSelection(default="3841", choices=[('3841', _("450 (default)")), ('12803', "500"), ('4609', "550"), ('5121', "600"), ('16643', "650"), ('17923', "700")])
	config.plugins.booster.normalfrequenz = ConfigSelection(default="3841", choices=[('3841', _("450 (default)")), ('12803', "500"), ('4609', "550"), ('5121', "600"), ('16643', "650"), ('17923', "700")])
	config.plugins.booster.standbyfrequenz = ConfigSelection(default="3841", choices=[('3841', _("450 (default)")), ('2561', "300"), ('5123', "200")])
else:
	config.plugins.booster.startfrequenz = ConfigSelection(default="4609", choices=[('4609', _("540 (default)")), ('5377', "630"), ('18179', "710"), ('39686', "775"), ('20483', "800")])
	config.plugins.booster.normalfrequenz = ConfigSelection(default="4609", choices=[('4609', _("540 (default)")), ('5377', "630"), ('18179', "710"), ('39686', "775"), ('20483', "800")])
	config.plugins.booster.standbyfrequenz = ConfigSelection(default="4609", choices=[('4609', _("540 (default)")), ('2561', "300"), ('5123', "200")])

def leaveStandby():
	print("[SH4BoosterControl] Leave Standby")
	initBooster()

def standbyCounterChanged(configElement):
	print("[SH4BoosterControl] In Standby")
	initStandbyBooster()
	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)

def initBooster():
	print("[SH4BoosterControl] initBooster")
	f = open("/proc/cpu_frequ/pll0_ndiv_mdiv", "w")
	f.write(config.plugins.booster.normalfrequenz.getValue())
	f.close()
	
def initStandbyBooster():
	print("[SH4BoosterControl] initStandbyBooster")
	f = open("/proc/cpu_frequ/pll0_ndiv_mdiv", "w")
	f.write(config.plugins.booster.standbyfrequenz.getValue())
	f.close()

class SH4BoosterControl(ConfigListScreen, Screen):
	def __init__(self, session, args=None):

		self.skin = """
			<screen position="100,100" size="500,210" title="Booster Control" >
				<widget name="config" position="20,15" size="460,150" scrollbarMode="showOnDemand" />
				<ePixmap position="40,165" size="140,40" pixmap="skin_default/buttons/green.png" alphatest="on" />
				<ePixmap position="180,165" size="140,40" pixmap="skin_default/buttons/red.png" alphatest="on" />
				<widget name="key_green" position="40,165" size="140,40" font="Regular;20" backgroundColor="#1f771f" zPosition="2" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_red" position="180,165" size="140,40" font="Regular;20" backgroundColor="#9f1313" zPosition="2" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			</screen>"""

		Screen.__init__(self, session)
		self.onClose.append(self.abort)

		self.onChangedEntry = [ ]
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)

		self.createSetup()

		self.Console = Console()
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Test"))

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
			"yellow": self.Test,
		}, -2)

	def createSetup(self):
		self.editListEntry = None
		self.list = []
		
		self.list.append(getConfigListEntry(_("Start boot frequency"), config.plugins.booster.startfrequenz))
		self.list.append(getConfigListEntry(_("Normal running frequency"), config.plugins.booster.normalfrequenz))		
		self.list.append(getConfigListEntry(_("Standby saver frequency"), config.plugins.booster.standbyfrequenz))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.newConfig()

	def newConfig(self):
		print(self["config"].getCurrent()[0])
		if self["config"].getCurrent()[0] == _('Start Boot Frequency'):
			self.createSetup()

	def abort(self):
		print("aborting")

	def save(self):
		for x in self["config"].list:
			x[1].save()

		configfile.save()
		initBooster()
		self.close()

	def cancel(self):
		initBooster()
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def Test(self):
		self.createSetup()
		initBooster()

class SH4_Booster:
	def __init__(self, session):
		print("[SH4BoosterControl] initializing")
		self.session = session
		self.service = None
		self.onClose = [ ]

		self.Console = Console()

		initBooster()

	def shutdown(self):
		self.abort()

	def abort(self):
		print("[SH4BoosterControl] aborting")
	
	config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call=False)

def main(menuid):
	if menuid != "system":
		return [ ]
	return [(_("Booster Control"), startBooster, "Booster Control", None)]

def startBooster(session, **kwargs):
	session.open(SH4BoosterControl)

sh4booster = None
gReason = -1
mySession = None

def controlsh4booster():
	global sh4booster
	global gReason
	global mySession

	if gReason == 0 and mySession != None and sh4booster == None:
		print("[SH4BoosterControl] Starting !!")
		sh4booster = SH4_Booster(mySession)
	elif gReason == 1 and sh4booster != None:
		print("[SH4BoosterControl] Stopping !!")
		
		sh4booster = None

def sessionstart(reason, **kwargs):
	print("[SH4BoosterControl] sessionstart")
	global sh4booster
	global gReason
	global mySession

	if "session" in kwargs:
		mySession = kwargs["session"]
	else:
		gReason = reason
	controlsh4booster()

def Plugins(**kwargs):
	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
		PluginDescriptor(name="SH4 Booster Control", description="Change CPU speed settings", where=PluginDescriptor.WHERE_MENU, fnc=main) ]


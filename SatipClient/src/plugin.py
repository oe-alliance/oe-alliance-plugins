from . import _
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigYesNo, ConfigSelection, ConfigInteger, ConfigIP
from Components.ActionMap import ActionMap, NumberActionMap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.Console import Console
from Tools.Directories import fileExists
from Plugins.Plugin import PluginDescriptor
from os import path as os_path

Config_Path = "/etc/satip-client.conf"

def modTupByIndex(tup, index, ins):
	lst = list(tup)
	lst[index] = ins
	return tuple(lst)

class SatIPclientSetup(Screen,ConfigListScreen):
	skin =  """
		<screen name="SatIPclientSetup" position="center,center" size="600,450">
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="25,70" size="560,300" scrollbarMode="showOnDemand" transparent="1" />
			<widget name="text" position="20,430" size="540,20" font="Regular;22" halign="center" valign="center" />
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.onChangedEntry = []
		self.satipserver = []
		self.satipserver_old = []
		self.list = []
		self.vtuner = "0"
		self.ServerDisabled_old = True
		self.Console = Console()
		
		self.disabledSel = ConfigYesNo(default = True)
		self.vtunerEnabledSel = ConfigYesNo(default = False)
		self.vtunerSel = ConfigSelection(choices = [("0","0"),("1","1"),("2","2"),("3","3")])
		self.frontendSel = ConfigSelection(choices = [("0","DVB-S2"),("1","DVB-C"),("2","DVB-T")])
		self.logSel = ConfigSelection(choices = [("1","1"),("2","2"),("3","3")])
		self.workaroundSel = ConfigInteger(default = 0, limits = (0, 7))

		self.disabledEntry = getConfigListEntry(_("Disable SAT>IP-client"), self.disabledSel)
		self.vtunerEntry = getConfigListEntry(_("Vtuner"), self.vtunerSel)
		self.vtunerEnabledEntry = getConfigListEntry(_("Enable Vtuner%s" %self.vtunerEntry[1].value), self.vtunerEnabledSel)
		self.serverEntry = getConfigListEntry(_("Server IP-adress"), ConfigIP(default=[0,0,0,0]))
		self.frontendEntry = getConfigListEntry(_("Frontend type"), self.frontendSel)
		self.logEntry = getConfigListEntry(_("Loglevel"), self.logSel)
		self.workaroundEntry = getConfigListEntry(_("Workarounds for various SAT>IP server quirks"), self.workaroundSel)

		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		
		for t in range(0, 4):
			self.satipserver.append((False,[0, 0, 0, 0],"0","0","0"))
		if os_path.exists(Config_Path):
			self.Read_Config()

		self.skinName = "SatIPclientSetup"
		self.setup_title = _("SAT>IP Client Setup")
		self.setTitle(self.setup_title)
		TEXT = _(" ")
		self["text"] = Label(_("%s")%TEXT)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Auto Config"))
		

		self["OkCancelActions"] = ActionMap(["OkCancelActions"],
			{
			"cancel": self.keyCancel,
			"ok": self.keySave,
			})

		self["ColorActions"] = ActionMap(["ColorActions"],
			{
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow" : self.KeyAuto,
			})
		
		self.createSetup()
		self.onClose.append(self.onClosed)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		pass

	def onClosed(self):
		self.close()

	def newConfig(self):
		if self["config"].getCurrent() == self.disabledEntry:
			self.createSetup()
			self.Fill_CurrentServerlist(int(self.vtuner))
		elif self["config"].getCurrent() == self.vtunerEntry or self["config"].getCurrent()[0][:-1] == self.vtunerEnabledEntry[0][:-1]:
			self.vtuner = self.vtunerEntry[1].value
			self.Fill_CurrentServerlist(int(self.vtuner))
			self.createSetup()
			self.Fill_CurrentServerlist(int(self.vtuner))
		
	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def createSetup(self):
		self.list = []
		self.vtunerEnabledEntry = getConfigListEntry(_("Enable Vtuner%s" %self.vtunerEntry[1].value), self.vtunerEnabledSel)
		self.list.append(self.disabledEntry)
		
		if not self.disabledEntry[1].value:
			self.list.append(self.vtunerEntry)
			self.list.append(self.vtunerEnabledEntry)
			if self.vtunerEnabledEntry[1].value:
				self.list.append(self.serverEntry)
				self.list.append(self.frontendEntry)
				self.list.append(self.logEntry)
				self.list.append(self.workaroundEntry)

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def Store_CurrentServerlist(self):
		self.satipserver[int(self.vtuner)] = (self.vtunerEnabledEntry[1].value,self.serverEntry[1].value,self.frontendEntry[1].value,self.logEntry[1].value,str(self.workaroundEntry[1].value))

	def Fill_CurrentServerlist(self, TunerNr):
		self.vtunerEnabledEntry[1].value = self.satipserver[TunerNr][0]
		self.serverEntry[1].value = self.satipserver[TunerNr][1]
		self.frontendEntry[1].value = self.satipserver[TunerNr][2]
		self.logEntry[1].value = self.satipserver[TunerNr][3]
		self.workaroundEntry[1].value = int(self.satipserver[TunerNr][4])
		self["config"].l.setList(self.list)

	def keySave(self):
		self.Store_CurrentServerlist()
		self.Create_Config()
		if fileExists('/etc/init.d/satip-client'):
			if not self.satipserver_old == self.satipserver or not self.ServerDisabled_old == self.disabledEntry[1].value:
				self.Console.ePopen('/etc/init.d/satip-client restart')
				self.session.openWithCallback(self.CB_RestartGUI, MessageBox, _("To enable the vtuners you need to Resart the GUI.\nRestart GUI now?"), MessageBox.TYPE_YESNO)
			else:
				self.close()
		else:
			self.session.open(MessageBox, _("SAT>IP Client not installed !!"), MessageBox.TYPE_ERROR)
			self.close()

	def CB_RestartGUI(self, ret):
		if ret:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

	def KeyAuto(self):
		self.session.open(MessageBox, _("Not yet implemented,\nComing soon ..."), MessageBox.TYPE_INFO, simple=True)
		return

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		if not self.satipserver_old == self.satipserver or not self.ServerDisabled_old == self.disabledEntry[1].value:
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		if not self["config"].getCurrent() == self.disabledEntry:
			if self["config"].getCurrent() == self.vtunerEntry or self["config"].getCurrent()[0][:-1] == self.vtunerEnabledEntry[0][:-1]:
				self.Store_CurrentServerlist()

	def Read_Config(self):
		f = open(Config_Path, "r")
		for line in f.readlines():
			line = line.replace(" ","")
			line = line[:-1]

			# DISABLED
			if line[0:9] == "DISABLED=":
				if line[9:].lower() == "no":
					self.disabledEntry[1].value = False
				else:
					self.disabledEntry[1].value = True
				continue

			# SATIPSERVER
			if line[0:11] == "SATIPSERVER":
				nr = int(line[11])
				ipstr = line[13:]
				iplist = ipstr.split(".")
				ip = []
				for t in range(0, 4):
					ip.append(int(iplist[t]))
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],0, True)
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],1, ip)
				continue

			if line[0:12] == "#SATIPSERVER":
				line = line[1:]
				nr = int(line[11])
				ipstr = line[13:]
				iplist = ipstr.split(".")
				ip = []
				for t in range(0, 4):
					ip.append(int(iplist[t]))
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],0, False)
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],1, ip)
				continue
				
			# FRONTENDTYPE
			if line[0:12] == "FRONTENDTYPE":
				nr = int(line[12])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],2, line[14:])
				continue

			if line[0:13] == "#FRONTENDTYPE":
				line = line[1:]
				nr = int(line[12])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],2, line[14:])
				continue

			# LOGLEVEL
			if line[0:8] == "LOGLEVEL":
				nr = int(line[8])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],3, line[10:])
				continue

			if line[0:9] == "#LOGLEVEL":
				line = line[1:]
				nr = int(line[8])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],3, line[10:])
				continue

			# WORKAROUND
			if line[0:10] == "WORKAROUND":
				nr = int(line[10])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],4, line[12:])
				continue

			if line[0:11] == "#WORKAROUND":
				line = line[1:]
				nr = int(line[10])
				self.satipserver[nr] = modTupByIndex(self.satipserver[nr],4, line[12:])
				continue


		f.close()
		self.Fill_CurrentServerlist(0)
		self.satipserver_old = list(self.satipserver)
		self.ServerDisabled_old = self.disabledEntry[1].value

	def Create_Config(self):
		conftxt = []
		conftxt.append("# SAT>IP Client Config file")
		conftxt.append("###########################\n")

		# DISABLED
		if self.disabledEntry[1].value:
			conftxt.append("DISABLED=yes\n")
		else:
			conftxt.append("DISABLED=no\n")
		conftxt.append("# SAT>IP server address")
		
		# SATIPSERVER
		for t in range(0, 4):
			ip = ""
			for x in range(0, 4):
				ip = ip + str(self.satipserver[t][1][x]) + "."
			if self.satipserver[t][0]:
				dis = ""
			else:
				dis = "#"
			conftxt.append(dis + "SATIPSERVER%s=%s" %(t,ip[:-1]))

		# FRONTENDTYPE
		conftxt.append("")
		conftxt.append("# Frontend type:")
		conftxt.append("# 0: DVB-S2")
		conftxt.append("# 1: DVB-C")
		conftxt.append("# 2: DVB-T")
		for t in range(0, 4):
			if self.satipserver[t][0]:
				dis = ""
			else:
				dis = "#"
			conftxt.append(dis + "FRONTENDTYPE%s=%s" %(t,self.satipserver[t][2]))
	
		# LOGLEVEL
		conftxt.append("")
		conftxt.append("# Loglevel")
		for t in range(0, 4):
			if self.satipserver[t][0]:
				dis = ""
			else:
				dis = "#"
			conftxt.append(dis + "LOGLEVEL%s=%s" %(t,self.satipserver[t][3]))

		# WORKAROUND
		conftxt.append("")
		conftxt.append("# Workarounds for various SAT>IP server quirks")
		conftxt.append("# This is a bitmask.")
		conftxt.append("# 0: Disable all workarounds (default)")
		conftxt.append("# 1: Enable workaround ADD-DUMMY-PID  (AVM Fritz!WLAN Repeater DVB-C)")
		conftxt.append("# 2: Enable workaround FORCE-FULL-PID (AVM Fritz!WLAN Repeater DVB-C)")
		conftxt.append("# 4: Enable workaround FORCE-FE-LOCK  (AVM Fritz!WLAN Repeater DVB-C) CURRENTLY ALWAYS ACTIVE!")
		conftxt.append("# Example:")
		conftxt.append("# AVM Fritz!WLAN Repeater DVB-C: WORKAROUNDx=7")
		for t in range(0, 4):
			if self.satipserver[t][0]:
				dis = ""
			else:
				dis = "#"
			conftxt.append(dis + "WORKAROUND%s=%s" %(t,self.satipserver[t][4]))

		f = open( Config_Path, "w" )
		for x in conftxt:
			f.writelines(x + '\n')
		f.close()

	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

def main(session, close=None, **kwargs):
	session.open(SatIPclientSetup)

def TunerSetup(menuid, **kwargs):
	if menuid == "scan":
		return [(_("SAT>IP Client Setup"), main, "satipclient", 10)]
	else:
		return []

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("SAT>IP Client Setup"), description=_("SAT>IP Client Setup"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=TunerSetup)]


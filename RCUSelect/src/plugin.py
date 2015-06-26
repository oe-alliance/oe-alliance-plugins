# -*- coding: utf-8 -*-
# for localized messages
from . import _

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Tools.HardwareInfo import HardwareInfo
import os

class RCUSelect(Screen):
	skin = """
	<screen name="Menusimple" position="center,center" size="350,175" title="" >
	<widget name="list" position="30,30" size="290,70" scrollbarMode="showOnDemand" />
	<widget name="info" position="75,5" zPosition="4" size="280,40" font="Regular;18" foregroundColor="#ffffff" transparent="1" halign="left" valign="center" />
	<ePixmap name="red"    position="20,125"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
	<ePixmap name="green"  position="190,125" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
	<widget name="key_red" position="20,125" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="#25062748" shadowOffset="-2,-2" /> 
	<widget name="key_green" position="190,125" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="#25062748" shadowOffset="-2,-2" /> 
	</screen>"""

	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)
		self.skinName = "RCUSelect"                 
		self.index = 0
		self.rcuval = []
		self.rcuvalOSD = []
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.action,
			"cancel": self.close,
			"red": self.close,
			"green": self.action,
		}, -1)
		self["key_green"] = Button(_("Apply"))
		self["key_red"] = Button(_("Cancel"))
		
		self.testlist = []
		self["info"] = Label()
		self["list"] = MenuList(self.rcuvalOSD)
		title = _("RCU Select")
		self.setTitle(title)
		self["pixmap"] = Pixmap()
		self.rcuval = ["WeTek Play (Classic) RCU", "WeTek Play Enigma2 RCU"]
		self.SetOSDList()

	def SetOSDList(self):
		choice = "WeTek Play Enigma2 RCU"
		try:
			choice = open("/etc/amremote/.choice", "r").read()
		except IOError:
			pass
		for x in self.rcuval:
			print "*****************"
			print choice[11:17]
			print choice
			print "*****************"
			#if x == choice[11:17]:
			if x == choice:
				self.rcuvalOSD.append(x + "  -  SET")
			else:
				self.rcuvalOSD.append(x)
		self["list"].setList(self.rcuvalOSD)


	def action(self):
		from Screens.MessageBox import MessageBox
		self.session.openWithCallback(self.confirm, MessageBox, _("Are you sure !?"), MessageBox.TYPE_YESNO, timeout = 15, default = False)

	def confirm(self, confirmed):
		if not confirmed:
			print "not confirmed"
			self.close()
		else:
			var = self["list"].getSelectionIndex()
			self.rcuv = self.rcuval[var]
			try:
				if self.rcuv == 'WeTek Play (Classic) RCU':
					os.system("cp -f /etc/amremote/wetek1.conf /etc/amremote/wetek.conf &")
				else:
					os.system("cp -f /etc/amremote/wetek2.conf /etc/amremote/wetek.conf &")
				f = open("/etc/amremote/.choice", "w")
				f.write(self.rcuv)
				f.close()
				os.system("killall -9 remotecfg &")
				os.system("/usr/bin/remotecfg /etc/amremote/wetek.conf &")
			except IOError:
				print "RCU select failed."
			self.close()

	def cancel(self):
		self.close()




###################################                
def startConfig(session, **kwargs):
        session.open(RCUSelect)

def mainmenu(menuid):
        if menuid != "setup":
                return [ ]
        return [(_("RCU Select"), startConfig, "RCU Select", None)]
        

def Plugins(**kwargs):
	boxime = HardwareInfo().get_device_name()
	if boxime == 'wetekplay' :
		return \
			[PluginDescriptor(name=_("RCU Select"), where = PluginDescriptor.WHERE_MENU, fnc=mainmenu),
			]
	else:
		return []

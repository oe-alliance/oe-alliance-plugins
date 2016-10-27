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
from boxbranding import getImageDistro
import os
import os.path

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
		self.rcuval = [_("WeTek Play2 RCU"),
		_('WeTek Play (Classic) RCU'),
		_("WeTek Play Enigma2 RCU"),
		_("WeTek Play OpenElec RCU"),
		_("AB IPBox 9900/99/55 HD RCU"),
		_("Alien2/1 RCU"),
		_("Alien1 old RCU"),
		_("GI LX3 RCU"),
		_("Gigablue 800 UE Plus RCU"),
		_("Mutant HD2400 RCU"),
		_("Octagon SF8 RCU"),
		_("Technomate Nano RCU"),
		_("xtrend ET10000 RCU"),
		_("Zgemma Star RCU")]
		self.SetOSDList()
		self.MakeKeymapBckUp()

	def MakeKeymapBckUp(self):
		filename = '/usr/lib/enigma2/python/Plugins/Extensions/RCUSelect/conf/keymap.orig.xml'
		cmd ='cp -f /usr/share/enigma2/keymap.xml ' + filename + ' &'
		if not os.path.exists(filename):
			os.system(cmd)

	def SetOSDList(self):
		boxime = HardwareInfo().get_device_name()
		if boxime == 'wetekplay2': choice = 'WeTek Play2 RCU'
		if boxime == 'wetekplay': choice = 'WeTek Play Enigma2 RCU'
		try:
			choice = open("/etc/amremote/.choice", "r").read()
		except IOError:
			pass
		self.rcuold = choice
		for x in self.rcuval:
			if x == choice:
				self.rcuvalOSD.append(x + "  -  SET")
			else:
				self.rcuvalOSD.append(x)
		self["list"].setList(self.rcuvalOSD)

	def action(self):
		from Screens.MessageBox import MessageBox
		self.session.openWithCallback(self.confirm, MessageBox, _("Are you sure?"), MessageBox.TYPE_YESNO, timeout = 15, default = False)

	def confirm(self, confirmed):
		if not confirmed:
			print "not confirmed"
			self.close()
		else:
			var = self["list"].getSelectionIndex()
			self.rcuv = self.rcuval[var]
			#if self.rcuv != self.rcuold: copy keymap
			try:
				if self.rcuv == 'WeTek Play2 RCU':
					os.system("cp -f /etc/amremote/wetek_play2.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'WeTek Play (Classic) RCU':
					os.system("cp -f /etc/amremote/wetek1.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'WeTek Play OpenElec RCU':
					os.system("cp -f /etc/amremote/wetek3.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'AB IPBox 9900/99/55 HD RCU':
					os.system("cp -f /etc/amremote/wetek_ipbox9900remote.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'Alien2/1 RCU':
					os.system("cp -f /etc/amremote/alien2.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'Alien1 old RCU':
					os.system("cp -f /etc/amremote/alien.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'GI LX3 RCU':
					os.system("cp -f /etc/amremote/gilx3.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'Gigablue 800 UE Plus RCU':
					os.system("cp -f /etc/amremote/gb800ueplus.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'Mutant HD2400 RCU':
					os.system("cp -f /etc/amremote/wetek_hd2400remote.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'Octagon SF8 RCU':
					os.system("cp -f /etc/amremote/octagonsf8.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'Technomate Nano RCU':
					os.system("cp -f /etc/amremote/wetek_tmnanoremote.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'xtrend ET10000 RCU':
					os.system("cp -f /etc/amremote/wetek_et10000remote.conf /etc/amremote/wetek.conf &")
				elif self.rcuv == 'Zgemma Star RCU':
					os.system("cp -f /etc/amremote/zgemmastar.conf /etc/amremote/wetek.conf &")
				else:
					os.system("cp -f /etc/amremote/wetek2.conf /etc/amremote/wetek.conf &")
				f = open("/etc/amremote/.choice", "w")
				f.write(self.rcuv)
				f.close()
				os.system("killall -9 remotecfg &")
				boxime = HardwareInfo().get_device_name()
				if boxime == 'wetekplay2':
					fin = file('/etc/amremote/wetek.conf')
					fout = open('/etc/amremote/wetek_tmp.conf', 'w')
					for line in fin :
						if 'work_mode' in line: line = 'work_mode  	= 0\n'
						fout.write(line)
					fout.close()
					os.system('mv -f /etc/amremote/wetek_tmp.conf /etc/amremote/wetek.conf &')
				os.system("/usr/bin/remotecfg /etc/amremote/wetek.conf &")
				if self.rcuold == "WeTek Play OpenElec RCU" or self.rcuv == "WeTek Play OpenElec RCU":
					if self.rcuold != self.rcuv:
						if self.rcuv == 'WeTek Play OpenElec RCU':
							if getImageDistro() == "openspa":
								os.system("cp -f /usr/lib/enigma2/python/Plugins/Extensions/RCUSelect/conf/keymap_OpenELEC.xml /usr/share/enigma2/keymap.xml &")
							else:
								os.system("cp -f /usr/lib/enigma2/python/Plugins/Extensions/RCUSelect/conf/keymap.OE.xml /usr/share/enigma2/keymap.xml &")
						else:
							os.system("cp -f /usr/lib/enigma2/python/Plugins/Extensions/RCUSelect/conf/keymap.orig.xml /usr/share/enigma2/keymap.xml &")
						os.system("killall -9 enigma2 &")
				else:
					os.system("cp -f /usr/lib/enigma2/python/Plugins/Extensions/RCUSelect/conf/keymap.orig.xml /usr/share/enigma2/keymap.xml &")
			except IOError:
				print "RCU select failed."
			self.close()

	def cancel(self):
		self.close()

def startConfig(session, **kwargs):
        session.open(RCUSelect)

def system(menuid):
	if menuid == "system":
		return [(_("RCU Select"), startConfig, "RCU Select", None)]
	else:
		return []
        
def Plugins(**kwargs):
	boxime = HardwareInfo().get_device_name()
	if boxime == 'wetekplay' or boxime == 'wetekplayplus' or boxime == 'wetekplay2' or boxime == 'wetekplay2s' :
		return \
			[PluginDescriptor(name=_("RCU Select"), where = PluginDescriptor.WHERE_MENU, fnc=system),
			]
	else:
		return []

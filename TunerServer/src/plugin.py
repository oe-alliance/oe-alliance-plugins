##############################################################################
#                          <<< Tuner Server >>>
#
#                      2012 meo <lupomeo@hotmail.com>
#
#  This file is open source software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License version 2 as
#               published by the Free Software Foundation.
#
#                    Modified for OE-Allinace by rossi2000
#
##############################################################################

# This plugin implement the Tuner Server feature included.
# Author: meo / rossi2000
# Please Respect credits

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Network import iNetwork
from Tools.Directories import fileExists
from enigma import eServiceCenter, eServiceReference, eTimer
from boxbranding import getImageDistro
from shutil import rmtree, move, copy
import os

class TunerServer(Screen):
	skin = """
	<screen position="center,center" size="800,505" >
		<widget name="lab1" position="10,4" size="780,400" font="Regular;20" transparent="0"/>
		<widget name="lab2" position="10,400" size="300,30" font="Regular;20" valign="center" halign="right" transparent="0"/>
		<widget name="labstop" position="320,400" size="260,30" font="Regular;20" valign="center" halign="center" backgroundColor="red"/>
		<widget name="labrun" position="320,400" size="260,30" zPosition="1" font="Regular;20" valign="center" halign="center" backgroundColor="green"/>
		<ePixmap pixmap="skin_default/buttons/red.png" position="95,450" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="330,450" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="565,450" size="140,40" alphatest="on" />
		<widget name="key_red" position="95,450" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
		<widget name="key_green" position="330,450" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
		<widget name="key_yellow" position="565,450" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Tuner Server setup"))

		mytext = """
This plugin implements the Tuner Server feature included. It will allow you to share the tuners of this box with another STB, PC and/or another compatible device in your home network.
The server will build a virtual channels list in the folder /media/hdd/tuner on this box.
You can access the tuner(s) of this box from clients on your internal lan using nfs, cifs, UPnP or any other network mountpoint.
The tuner of the server (this box) has to be avaliable. This means that if you have ony one tuner in your box you can only stream the channel you are viewing (or any channel you choose if your box is in standby).
Remember to select the correct audio track in the audio menu if there is no audio or the wrong language is streaming.
NOTE: The server is built, based on your current ip and the current channel list of this box. If you change your ip or your channel list is updated, you will need to rebuild the server database.

		"""
		self["lab1"] = Label(_(mytext))
		self["lab2"] = Label(_("Current Status:"))
		self["labstop"] = Label(_("Server Disabled"))
		self["labrun"] = Label(_("Server Enabled"))
		self["key_red"] = Label(_("Build Server"))
		self["key_green"] = Label(_("Disable Server"))
		self["key_yellow"] = Label(_("Close"))
		self.my_serv_active = False
		self.ip = "0.0.0.0"

		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.close,
			"back": self.close,
			"red": self.ServStart,
			"green": self.ServStop,
			"yellow": self.close
		})
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.doServStart)
		self.onClose.append(self.delTimer)
		self.onLayoutFinish.append(self.updateServ)

	def ServStart(self):
		if os.path.ismount("/media/hdd"):
			self["lab1"].setText(_("Your server is now building\nPlease wait ..."))
			self.activityTimer.start(10)
		else:
			self.session.open(MessageBox, _("Sorry, but you need to have a device mounted at '/media/hd'"), MessageBox.TYPE_INFO)

	def doServStart(self):
		self.activityTimer.stop()
		if os.path.exists("/media/hdd/tuner"):
			rmtree("/media/hdd/tuner")
		ifaces = iNetwork.getConfiguredAdapters()
		for iface in ifaces:
			ip = iNetwork.getAdapterAttribute(iface, "ip")
			ipm = "%d.%d.%d.%d" % (ip[0], ip[1], ip[2], ip[3])
			if ipm != "0.0.0.0":
				self.ip = ipm

		os.mkdir("/media/hdd/tuner", 0755)
		s_type = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 134) || (type == 195)'
		serviceHandler = eServiceCenter.getInstance()
		services = serviceHandler.list(eServiceReference('%s FROM BOUQUET "bouquets.tv" ORDER BY bouquet'%(s_type)))
		bouquets = services and services.getContent("SN", True)
		count = 1
		for bouquet in bouquets:
			self.poPulate(bouquet, count)
			count += 1

		mytext = "Server avaliable on ip %s\nTo access this box's tuners you can connect via Lan or UPnP.\n\n1) To connect via lan you have to mount the /media/hdd folder of this box in the client /media/hdd folder. Then you can access the tuners server channel list from the client Media player -> Harddisk -> tuner.\n2) To connect via UPnP you need an UPnP server that can manage .m3u files like Mediatomb." % (self.ip)
		self["lab1"].setText(_(mytext))
		self.session.open(MessageBox, _("Build Complete!"), MessageBox.TYPE_INFO)
		self.updateServ()


	def poPulate(self, bouquet, count):
		n = "%03d_" % (count)
		name = n + self.cleanName(bouquet[1])
		path = "/media/hdd/tuner/" + name
		os.mkdir(path, 0755)
		serviceHandler = eServiceCenter.getInstance()
		services = serviceHandler.list(eServiceReference(bouquet[0]))
		channels = services and services.getContent("SN", True)
		count2 = 1
		for channel in channels:
			if not int(channel[0].split(":")[1]) & 64:
				n2 = "%03d_" % (count2)
				filename = path + "/" + n2 + self.cleanName(channel[1]) + ".m3u"
				try:
					out = open(filename, "w")
				except:
					continue
				out.write("#EXTM3U\n")
				out.write("#EXTINF:-1," + channel[1] + "\n")
				out.write("http://" + self.ip + ":8001/" + channel[0]+ "\n\n")
				out.close()
				count2 += 1

	def cleanName(self, name):
		name = name.replace(" ", "_")
		name = name.replace('\xc2\x86', '').replace('\xc2\x87', '')
		name = name.replace(".", "_")
		name = name.replace("<", "")
		name = name.replace("<", "")
		name = name.replace("/", "")
		return name

	def ServStop(self):
		if self.my_serv_active == True:
			self["lab1"].setText(_("Your server is now being deleted\nPlease Wait ..."))
			if os.path.exists("/media/hdd/tuner"):
				rmtree("/media/hdd/tuner")
			mybox = self.session.open(MessageBox, _("Tuner Server Disabled."), MessageBox.TYPE_INFO)
			mybox.setTitle(_("Info"))
			self.updateServ()
		self.session.open(MessageBox, _("Server now disabled!"), MessageBox.TYPE_INFO)

	def updateServ(self):
		self["labrun"].hide()
		self["labstop"].hide()
		self.my_serv_active = False

		if os.path.isdir("/media/hdd/tuner"):
			self.my_serv_active = True
			self["labstop"].hide()
			self["labrun"].show()
		else:
			self["labstop"].show()
			self["labrun"].hide()

	def delTimer(self):
		del self.activityTimer


def settings(menuid, **kwargs):
	if menuid == "network":
		return [(_("Tuner Server setup"), main, "tuner_server_setup", None)]
	return []

def main(session, **kwargs):
	session.open(TunerServer)

def Plugins(**kwargs):
	if getImageDistro() == "openvix":
		return PluginDescriptor(name=_("Tuner Server setup"), description=_("Allow Streaming From Box Tuners"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=settings)
	else:
		return PluginDescriptor(name=_("Tuner Server"), description=_("Allow Streaming From Box Tuners"), where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)

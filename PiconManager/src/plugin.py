#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
# maintainer: einfall & schomi (schomi@vuplus-support.org)
# This plugin is free software, you are allowed to
# modify it (if you keep the license),
# but you are not allowed to distribute/publish
# it without source code (this version and your modifications).
# This means you also have to distribute
# source code of your modifications.
#######################################################################
# this version is complete modified by shadowrider and NaseDC
# python3 fix by jbleyel
#######################################################################
#  Thanks to vuplus-support.org for the webspace
#######################################################################

from uuid import uuid4
from shutil import rmtree
from random import choice
from datetime import date
from re import S, I, search
from skin import parameters
from requests import get, exceptions
from os import mkdir, makedirs, statvfs, remove
from os.path import exists, isdir, basename, join, splitext
from six import ensure_binary, ensure_str
from Screens.ChannelSelection import SimpleChannelSelection, service_types_tv, service_types_radio
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.HelpMenu import HelpableScreen
from ServiceReference import ServiceReference
from Plugins.Plugin import PluginDescriptor
from Components.Label import Label
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config, ConfigSelection, getConfigListEntry, ConfigText, ConfigYesNo, ConfigSubsection, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.Slider import Slider
from Components.FileList import FileList
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from twisted.internet import defer
from twisted.internet.reactor import callInThread
from six.moves.urllib.parse import quote
from enigma import eServiceCenter, eServiceReference, gFont, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_VALIGN_CENTER

from .piconnames import reducedName, getInteroperableNames  #check for by-name-picons that dont fit with VTi Syntax (Picon Buddy Mode)
from . import _

pname = _("PiconManager (mod)")
pdesc = _("Manage your Picons")
pversion = "2.5-r4"
pdate = "20220816"

picon_tmp_dir = "/tmp/piconmanager/"
picon_debug_file = "/tmp/piconmanager_error"

picon_info_file = "picons/picon_info.txt"
picon_list_file = "zz_picon_list.txt"

server_choices = [("http://picons.vuplus-support.org/", "VTi: vuplus-support.org"), ]

config.plugins.piconmanager = ConfigSubsection()
config.plugins.piconmanager.savetopath = ConfigText(default="/usr/share/enigma2/", fixed_size=False)
config.plugins.piconmanager.piconname = ConfigText(default="picon", fixed_size=False)
config.plugins.piconmanager.selected = ConfigText(default="All", fixed_size=False)
config.plugins.piconmanager.spicon = ConfigText(default="", fixed_size=False)
config.plugins.piconmanager.saving = ConfigYesNo(default=True)
config.plugins.piconmanager.debug = ConfigYesNo(default=False)
config.plugins.piconmanager.server = ConfigSelection(default=server_choices[0][0], choices=server_choices)
config.plugins.piconmanager.alter = ConfigInteger(default=365, limits=(0, 1000))


def ListEntry(entry):
	x, y, w, h = parameters.get("PiconManagerList", (10, 0, 1280, 25))
	return [entry, (eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])]


def errorWrite(error):
	if config.plugins.piconmanager.debug.value:
		if not exists(picon_debug_file):
			f = open(picon_debug_file, "w")
		else:
			f = open(picon_debug_file, "a")
		f.write("%s\n" % error)
		f.close()


def notfoundWrite(picon):
	if config.plugins.piconmanager.debug.value:
			f = open("/tmp/picon_dl_err", "a")
			f.write("%s\n" % picon)
			f.close()


def getServiceList(ref):
	root = eServiceReference(str(ref))
	serviceHandler = eServiceCenter.getInstance()
	return serviceHandler.list(root).getContent("SN", True)


def getTVBouquets():
	return getServiceList(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')


def getRadioBouquets():
	return getServiceList(service_types_radio + ' FROM BOUQUET "bouquets.radio" ORDER BY bouquet')


def buildChannellist():
	rm_chlist = None
	rm_chlist = []
	tvbouquets = getTVBouquets()
	radiobouquets = getRadioBouquets()
	allbouquets = tvbouquets + radiobouquets
	print("[PiconManager] found %s bouquets" % (len(allbouquets)))

	for bouquet in allbouquets:
		bouquetlist = []
		bouquetlist = getServiceList(bouquet[0])
		for (serviceref, servicename) in bouquetlist:
			rm_chlist.append((serviceref, servicename))
	return rm_chlist


class PiconManagerScreen(Screen, HelpableScreen):
	skin = """
	<screen name="PiconManager" title="PiconManager" position="center,center" size="1160,650">
		<widget name="piconpath" position="20,10" size="690,60" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="1" halign="left" />
		<widget name="piconpath2" position="200,10" size="500,60" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="1" halign="left" />
		<widget name="piconspace" position="20,40" size="690,60" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="1" halign="left" />
		<widget name="piconcount" position="20,70" size="690,60" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="1" halign="left" />
		<widget name="picondownload" position="20,100" size="690,60" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="1" halign="left" />
		<widget name="piconerror" position="20,130" size="690,60" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="1" halign="left" />
		<widget name="piconslidername" position="20,160" size="690,60" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="1" halign="left" />
		<widget name="selectedname" position="20,190" size="160,40" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="1" halign="left" />
		<widget name="selected" position="180,190" size="200,40" noWrap="1" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="1" halign="left" />
		<widget name="creatorname" position="20,220" size="160,40" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="1" halign="left" />
		<widget name="creator" position="180,220" size="200,40" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="1" halign="left" />
		<widget name="sizename" position="390,190" size="160,40" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="1" halign="left" />
		<widget name="size" position="580,190" size="160,40" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="1" halign="left" />
		<widget name="bitname" position="390,220" size="160,40" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="1" halign="left" />
		<widget name="bit" position="580,220" size="160,40" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="1" halign="left" />
		<widget name="spiconname" position="20,250" size="690,40" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="1" halign="left" />
		<widget name="spicon" position="180,250" size="690,40" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="1" halign="left" />
		<widget name="altername" position="390,250" size="690,40" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="1" halign="left" />
		<widget name="alter" position="580,250" size="690,40" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="1" halign="left" />
		<widget name="piconslider" position="280,164" size="180,20" zPosition="2" transparent="0" />
		<widget name="picon" position="738,10" size="400,240" zPosition="4" transparent="1" borderWidth="0" borderColor="#0000000" alphatest="blend" />
		<widget name="list" position="10,300" size="1130,295" zPosition="1" foregroundColor="#00ffffff" foregroundColorSelected="#00fff000" scrollbarMode="showOnDemand" transparent="1" />
		<widget name="key_red" position="42,615" size="300,25" transparent="1" font="Regular;20"/>
		<widget name="key_green" position="285,615" size="300,25" transparent="1" font="Regular;20"/>
		<widget name="key_yellow" position="451,615" size="300,25" transparent="1" font="Regular;20"/>
		<widget name="key_blue" position="734,615" size="300,25" transparent="1" font="Regular;20"/>
		<ePixmap position="10,615" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_red.png" transparent="1" alphatest="on"/>
		<ePixmap position="257,615" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_green.png" transparent="1" alphatest="on"/>
		<ePixmap position="421,615" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_yellow.png" transparent="1" alphatest="on"/>
		<ePixmap position="701,615" size="263,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_blue.png" transparent="1" alphatest="on"/>
		<ePixmap position="916,610" size="260,35" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_info.png" transparent="1" alphatest="on"/>
		<ePixmap position="977,610" size="260,35" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_menu.png" transparent="1" alphatest="on"/>
		<ePixmap position="1038,610" size="260,35" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_channel.png" transparent="1" alphatest="on"/>
		<ePixmap position="1095,610" size="260,35" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_help.png" transparent="1" alphatest="on"/>
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.server_url = config.plugins.piconmanager.server.value
		self.piconname = config.plugins.piconmanager.piconname.value
		self.picondir = config.plugins.piconmanager.savetopath.value
		self.alter = config.plugins.piconmanager.alter.value
		self.piconfolder = "%s%s/" % (self.picondir, self.piconname)
		self.picon_name = ""
		self.piconlist = []
		self.tried_mirrors = []
		self.art_list = []
		self.prev_sel = None
		self.spicon_name = ""
		self.aktdl_pico = None
		self['piconpath'] = Label(_("Picon folder: "))
		self['piconpath2'] = Label(self.piconfolder)
		self['piconspace'] = Label(_(" "))
		self['piconcount'] = Label(_("Reading Channels..."))
		self['picondownload'] = Label(_("Picons loaded: "))
		self['piconerror'] = Label(_("Picons not found: "))
		self['piconslidername'] = Label(_("Download progress: "))
		self['selectedname'] = Label(_("Show group: "))
		self['selected'] = Label()
		self['creatorname'] = Label(_("Creator: "))
		self['creator'] = Label()
		self['sizename'] = Label(_("Size: "))
		self['size'] = Label()
		self['bitname'] = Label(_("Color depth: "))
		self['bit'] = Label()
		self['altername'] = Label(_("Not older than X days: "))
		self['alter'] = Label(str(self.alter))
		self['spiconname'] = Label(_("Standard picon: "))
		self['spicon'] = Label()
		self.chlist = buildChannellist()
		self.getFreeSpace()
		self.countchlist = len(self.chlist)
		self.activityslider = Slider(0, self.countchlist)
		self["piconslider"] = self.activityslider
		self['key_red'] = Label(_("Select drive"))
		self['key_green'] = Label(_("Download picons"))
		self['key_yellow'] = Label(_("Select path"))
		self['key_blue'] = Label(_("Create folder"))
		self['picon'] = Pixmap()
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"ok": (self.keyOK, _("Show random Picon")),
			"cancel": (self.keyCancel, _("Exit")),
		}, -2)

		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
			{
				"1": (self.sel_creator_back, _("Previous picon creator")),
				"3": (self.sel_creator_next, _("Next picon creator")),
				"4": (self.sel_size_back, _("Previous picon size")),
				"6": (self.sel_size_next, _("Next picon size")),
				"7": (self.sel_bit_back, _("Previous color depth")),
				"9": (self.sel_bit_next, _("Next color depth")),
			}
		)
		self["EPGSelectActions"] = HelpableActionMap(self, "EPGSelectActions",
		{
			"menu": (self.settings, _("More selections")),
			"nextService": (self.sel_satpos_next, _("Next Group")),
			"prevService": (self.sel_satpos_back, _("Previous Group")),
			"info": (self.set_picon, _("Set / clear standard Picon")),
			"red": (self.changeDrive, _("Select drive")),
			"timerAdd": (self.downloadPicons, _("Download picons")),
			"yellow": (self.keyYellow, _("Select path")),
			"blue": (self.changePiconName, _("Create folder")),
			}, -2)
		self.channelMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		font, size = parameters.get("PiconManagerListFont", ('Regular', 22))
		self.channelMenuList.l.setFont(0, gFont(font, size))
		self.channelMenuList.l.setItemHeight(25)
		self.setTitle(pname + " " * 3 + _("V") + " %s" % pversion)
		self['list'] = self.channelMenuList
		self['list'].onSelectionChanged.append(self.showPic)
		self.keyLocked = True
		self.piconTempDir = picon_tmp_dir
		if not exists(self.piconTempDir):
			mkdir(self.piconTempDir)
		self.onLayoutFinish.append(self.getPiconList)

	def settings(self):
		if self.piconlist and self.art_list:
			self.session.openWithCallback(self.makeList, pm_conf)

	def set_picon(self):
		if config.plugins.piconmanager.spicon.value == "":
			self.session.openWithCallback(self.got_picon, SimpleChannelSelection, _("Select service for preferred picon"))
		else:
			self.got_picon()

	def got_picon(self, service=""):
		service_name = ""
		if isinstance(service, eServiceReference):
			service_name = ServiceReference(service).getServiceName()
			service2 = service.toString()
			service = service.toString().replace(':', '_').rstrip('_') + ".png"
		if service == "":
			config.plugins.piconmanager.spicon.value = service
		else:
			for channel in self.chlist:
				if channel[0] == service2:
					service_name = channel[1]
					break
			config.plugins.piconmanager.spicon.value = service + "|" + service_name
		config.plugins.piconmanager.spicon.save()
		self['spicon'].setText(service_name)
		try:
			rmtree(self.piconTempDir)
			mkdir(self.piconTempDir)
		except OSError:
			pass
		self.getPiconList()

	def sel_creator_next(self):
		self.change_filter_mode(+1, 0)

	def sel_creator_back(self):
		self.change_filter_mode(-1, 0)

	def sel_bit_next(self):
		self.change_filter_mode(+1, 1)

	def sel_bit_back(self):
		self.change_filter_mode(-1, 1)

	def sel_size_next(self):
		self.change_filter_mode(+1, 2)

	def sel_size_back(self):
		self.change_filter_mode(-1, 2)

	def sel_satpos_next(self):
		self.change_filter_mode(+1, 3)

	def sel_satpos_back(self):
		self.change_filter_mode(-1, 3)

	def change_filter_mode(self, direction, filter_type):
		if filter_type == 0:
			if config.plugins.piconmanager.creator.value in self.creator_list:
				idx = self.creator_list.index(config.plugins.piconmanager.creator.value) + direction
			else:
				idx = 0
			if idx < 0:
				idx = len(self.creator_list) - 1
			elif idx > len(self.creator_list) - 1:
				idx = 0
			if len(self.creator_list):
				config.plugins.piconmanager.creator.value = self.creator_list[idx]
				self['creator'].setText(_(str(config.plugins.piconmanager.creator.value)))
				config.plugins.piconmanager.creator.save()
		elif filter_type == 1:
			if config.plugins.piconmanager.bit.value in self.bit_list:
				idx = self.bit_list.index(config.plugins.piconmanager.bit.value) + direction
			else:
				idx = 0
			if idx < 0:
				idx = len(self.bit_list) - 1
			elif idx > len(self.bit_list) - 1:
				idx = 0
			if len(self.bit_list):
				config.plugins.piconmanager.bit.value = self.bit_list[idx]
				self['bit'].setText(_(str(config.plugins.piconmanager.bit.value)))
				config.plugins.piconmanager.bit.save()
		elif filter_type == 2:
			if config.plugins.piconmanager.size.value in self.size_list:
				idx = self.size_list.index(config.plugins.piconmanager.size.value) + direction
			else:
				idx = 0
			if idx < 0:
				idx = len(self.size_list) - 1
			elif idx > len(self.size_list) - 1:
				idx = 0
			if len(self.size_list):
				config.plugins.piconmanager.size.value = self.size_list[idx]
				self['size'].setText(_(str(config.plugins.piconmanager.size.value)))
				config.plugins.piconmanager.size.save()
		elif filter_type == 3:
			if config.plugins.piconmanager.selected.value in self.art_list:
				idx = self.art_list.index(config.plugins.piconmanager.selected.value) + direction
			else:
				idx = 0
			if idx < 0:
				idx = len(self.art_list) - 1
			elif idx > len(self.art_list) - 1:
				idx = 0
			if len(self.art_list):
				config.plugins.piconmanager.selected.value = self.art_list[idx]
				self['selected'].setText(str(config.plugins.piconmanager.selected.value).replace("+", " ").replace("-", " "))
				config.plugins.piconmanager.selected.save()
		alter = config.plugins.piconmanager.alter.value
		self.makeList(config.plugins.piconmanager.creator.value, config.plugins.piconmanager.size.value, config.plugins.piconmanager.bit.value, config.plugins.piconmanager.server.value, True, False, alter)

	def getFreeSpace(self):
		if isdir(self.picondir):
			which = "MB"
			free = 0
			currstatvfs = statvfs(self.picondir)
			free = (currstatvfs.f_frsize * currstatvfs.f_bfree) / 1024 / 1024
			if free > 1024:
				free = int(free / 1024.)
				which = "GB"
			self['piconspace'].setText(_("FreeSpace:") + " %s %s" % (free, which))
		else:
			self['piconspace'].setText(_("FreeSpace: Drive Not Found !"))

	def showPic(self):
		self["picon"].hide()
		if len(self.piconlist) and self['list'].getCurrent() and len(self['list'].getCurrent()[0]) >= 3:
			self.auswahl = self['list'].getCurrent()[0][2]
			picon_name = basename(self.auswahl)
			if config.plugins.piconmanager.spicon.value != "":
				if not "by name" in self['list'].getCurrent()[0][0].lower():
					picon_sname = txt = config.plugins.piconmanager.spicon.value.split('|')[0]
				else:
					picon_sname = txt = config.plugins.piconmanager.spicon.value.split('|')[1].replace(" ", "%20") + ".png"
				self.auswahl = self.auswahl.replace(picon_name, picon_sname)
			self.downloadPiconPath = join(self.piconTempDir, self['list'].getCurrent()[0][4] + ".png")
			if not exists(self.downloadPiconPath):
				callInThread(self.threadDownloadPage, self.auswahl, self.downloadPiconPath, self.showPiconFile, self.dataError)
			else:
				self.showPiconFile(self.downloadPiconPath, None)

	def getPiconList(self):
		print("[PiconManager] started ...")
		self['piconcount'].setText("%s %s" % (_("Channels:"), self.countchlist))
		self['selected'].setText(_(str(config.plugins.piconmanager.selected.value).replace("_", ", ").replace("+", " ").replace("-", " ")))
		if config.plugins.piconmanager.spicon.value != "":
			txt = config.plugins.piconmanager.spicon.value.split('|')
			if len(txt) == 2:
				txt = txt[1]
			else:
				txt = txt[0]
		else:
			txt = ""
		self['spicon'].setText(txt)
		url = "%s%s" % (self.server_url, picon_info_file)
		print("[PiconManager] Server: %s" % self.server_url)
		if config.plugins.piconmanager.selected.value == _("All"):
			config.plugins.piconmanager.selected.setValue("All")
			config.plugins.piconmanager.selected.save()
		self.channelMenuList.setList(list(map(ListEntry, [(_("Loading, please wait..."),)])))
		callInThread(self.threadGetPage, url, self.parsePiconList, self.dataError2)

	def threadGetPage(self, link, success, fail):
		try:
			response = get(link, timeout=(3.05, 6))
			response.raise_for_status()
		except exceptions.RequestException as error:
			fail(error)
		else:
			success(response.content)

	def parsePiconList(self, data):
		print("[PiconManager] parsing ...")
		self.size_list = ["All"]
		self.bit_list = ["All"]
		self.creator_list = ["All"]
		self.piconlist = []
		self.art_list = ["All"]
		data = ensure_str(data).replace("\xc2\x86", "").replace("\xc2\x87", "")
		picon_data = data.split("\n")
		if picon_data:
			for picon_info in picon_data:
				if len(picon_info) and not picon_info.startswith('<meta'):
					info_list = picon_info.split(';')
					if len(info_list) >= 9:
						dirUrl = join(self.server_url, info_list[0]).replace(" ", "%20")
						picUrl = join(self.server_url, info_list[0], info_list[1]).replace(" ", "%20")
						cur_dir = info_list[0]
						p_date = info_list[2]
						p_name = info_list[3]
						p_pos = info_list[4]
						p_creator = info_list[5]
						p_bit = (info_list[6].replace(' ', '').lower()).replace('bit', ' bit')
						p_size = info_list[7].replace(' ', '').lower()
						p_uploader = info_list[8]
						if p_size not in self.size_list:
							self.size_list.append(p_size)
						if p_bit not in self.bit_list:
							self.bit_list.append(p_bit)
						if p_creator not in self.creator_list:
							self.creator_list.append(p_creator)
						if p_pos not in self.art_list:
							self.art_list.append(p_pos)
						p_identifier = str(uuid4())
						p_name = "%s | %s - %s | %s | %s | %s | %s" % (p_pos, p_creator, p_name, p_size, p_bit, p_date, p_uploader)
						self.piconlist.append((p_name, dirUrl, picUrl, (p_creator, p_size, p_bit, p_pos), p_identifier, cur_dir))
			if config.plugins.piconmanager.selected.value not in self.art_list:
				config.plugins.piconmanager.selected.setValue("All")
				self['selected'].setText(_("All"))
			if not len(self.piconlist):
				self.dataError2(None)
			else:
				self.size_list.sort()
				self.bit_list.sort()
				self.creator_list.sort()
				self.art_list.sort()
				self.piconlist.sort(key=lambda x: x[0].lower())
				self.keyLocked = False
				prev_value = None
				if hasattr(config.plugins.piconmanager, "bit"):
					prev_value = config.plugins.piconmanager.bit.value
				config.plugins.piconmanager.bit = ConfigSelection(default="All", choices=self.createChoiceList(self.bit_list, [("All", _("All"))]))
				if prev_value:
					config.plugins.piconmanager.bit.value = prev_value
				prev_value = None
				if hasattr(config.plugins.piconmanager, "size"):
					prev_value = config.plugins.piconmanager.size.value
				config.plugins.piconmanager.size = ConfigSelection(default="All", choices=self.createChoiceList(self.size_list, [("All", _("All"))]))
				if prev_value:
					config.plugins.piconmanager.size.value = prev_value
				prev_value = None
				if hasattr(config.plugins.piconmanager, "creator"):
					prev_value = config.plugins.piconmanager.creator.value
				config.plugins.piconmanager.creator = ConfigSelection(default="All", choices=self.createChoiceList(self.creator_list, [("All", _("All"))]))
				if prev_value:
					config.plugins.piconmanager.creator.value = prev_value
				self['creator'].setText(_(str(config.plugins.piconmanager.creator.value)))
				self['size'].setText(_(str(config.plugins.piconmanager.size.value)))
				self['bit'].setText(_(str(config.plugins.piconmanager.bit.value)))
				alter = config.plugins.piconmanager.alter.value
				self.makeList(config.plugins.piconmanager.creator.value, config.plugins.piconmanager.size.value, config.plugins.piconmanager.bit.value, self.server_url, True, False, alter)

	def createChoiceList(self, choicelist, default_choice):
		ret = default_choice
		if len(choicelist):
			for x in choicelist:
				ret.append((x, _("%s") % x))
		return ret

	def makeList(self, creator="All", size="All", bit="All", server=config.plugins.piconmanager.server.value, update=True, reload_picons=False, alter=0):
		if reload_picons:
			self.server_url = server
			self.channelMenuList.setList([])
			self.getPiconList()
		else:
			if update:
				new_list = []
				self['alter'].setText(str(alter))
				art = config.plugins.piconmanager.selected.value
				for x in self.piconlist:
					if alter:
						present = date.today()
						pdatestr = str(x[0]).split(" | ")[4]
						pdatestr = pdatestr.split(".")
						pdate = date(int(pdatestr[2]), int(pdatestr[1]), int(pdatestr[0]))
						diff = present - pdate
						if int(diff.days) > alter:
							continue
					if (art != "All" and x[3][3] != art) or (creator != "All" and x[3][0] != creator) or (size != "All" and x[3][1] != size) or (bit != "All" and x[3][2] != bit):
						continue
					else:
						new_list.append((x[0], x[1], x[2], x[3], x[4], x[5]))
				if len(new_list):
					self.channelMenuList.setList(list(map(ListEntry, new_list)))
				else:
					self.channelMenuList.setList(list(map(ListEntry, [(_("No search results, please change filter options ..."),)])))

	def keyOK(self):
		if len(self.piconlist) > 0 and not self.keyLocked:
			if self['list'].getCurrent() is not None:
				if len(self['list'].getCurrent()[0]) >= 6:
					self.auswahl = self['list'].getCurrent()[0][4]
					self.cur_selected_dir = self['list'].getCurrent()[0][5]
					self.picon_list_file = "%s%s_list" % (self.piconTempDir, self.auswahl)
					if exists(self.picon_list_file):
						self.getPiconFiles()
					else:
						url = "%s%s/%s" % (self.server_url, self.cur_selected_dir, picon_list_file)
						callInThread(self.threadDownloadPage, url, self.picon_list_file, self.getPiconFiles, self.dataError)

	def getPiconFiles(self, data=None):
		if exists(self.picon_list_file):
			if self.prev_sel != self.picon_list_file:
				self.prev_sel = self.picon_list_file
				with open(self.picon_list_file) as f:
					self.picon_files = f.readlines()
			self.picon_name = choice(self.picon_files)
			downloadPiconUrl = "%s%s/%s" % (self.server_url, self.cur_selected_dir, self.picon_name)
			self.downloadPiconPath = "%s%s.png" % (self.piconTempDir, self.auswahl)
			self.keyLocked = False
			callInThread(self.threadDownloadPage, downloadPiconUrl, self.downloadPiconPath, self.showPiconFile, self.dataError)

	def threadDownloadPage(self, link, file, success, fail=None):
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		try:
			response = get(link, timeout=(3.05, 6))
			response.raise_for_status()
			with open(file, "wb") as f:
				f.write(response.content)
			if file:
				success(file)
		except exceptions.RequestException as error:
			if fail is not None:
				fail(error)

	def keyCancel(self):
		config.plugins.piconmanager.savetopath.value = self.picondir
		config.plugins.piconmanager.savetopath.save()
		config.plugins.piconmanager.piconname.value = self.piconname
		config.plugins.piconmanager.piconname.save()
		self.channelMenuList.setList([])
		try:
			rmtree(self.piconTempDir)
		except OSError:
			pass
		self.close()

	def keyYellow(self):
		self.session.openWithCallback(self.selectedMediaFile, PiconManagerFolderScreen, self.picondir)

	def selectedMediaFile(self, res):
		if res is not None:
			self.piconfolder = res
			self.piconname = res.split("/")[-2]
			self['piconpath2'].setText(self.piconfolder)

	def changeDrive(self):
		if search("/usr/share/enigma2/", self.piconfolder, S | I):
			self.picondir = "/media/usb/"
		elif search("/media/usb/", self.piconfolder, S | I):
			self.picondir = "/media/hdd/"
		elif search("/media/hdd/", self.piconfolder, S | I):
			self.picondir = "/usr/share/enigma2/"
		self.piconfolder = "%s%s/" % (self.picondir, self.piconname)
		self['piconpath2'].setText(self.piconfolder)
		print("[PiconManager] set picon path to: %s" % self.piconfolder)
		self.getFreeSpace()

	def changePiconName(self):
		self.session.openWithCallback(self.gotNewPiconName, VirtualKeyBoard, title=(_("Enter Picon Dir:")), text=self.piconname)

	def gotNewPiconName(self, name):
		if name is not None:
			self.piconname = name
			self.piconfolder = "%s%s/" % (self.picondir, self.piconname)
			self['piconpath2'].setText(self.piconfolder)
			print("[PiconManager] set picon path to: %s" % self.piconfolder)
	##################################### OH #############################################

	def url2Str(self, url):
		try:
			from urllib.request import Request, urlopen
			header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
					'Accept-Charset': 'utf-8;q=0.7,*;q=0.7', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
			searchrequest = Request(url, None, header)
			return urlopen(searchrequest).read()
		except:
			return ''

	def prepByNameList(self):  #load picon list, then create reducedNames (for flexible comparing with channel names)
		self.nameList = []
		self.reducedList = []
		try:
			if not "by name" in self['list'].getCurrent()[0][0].lower():
				return 1
			self.auswahl = self['list'].getCurrent()[0][4]
			self.cur_selected_dir = self['list'].getCurrent()[0][5]
			self.picon_list_file = self.piconTempDir + self.auswahl + "_list"
			url = self.server_url + self.cur_selected_dir + "/" + picon_list_file
			for x in self.url2Str(url).split('\n'):
				self.nameList.append(x[:-4])
				self.reducedList.append(reducedName(x[:-4]))
		except:
			pass

	def comparableChannelName(self, channelName):  # check picon list for comparable channelname
		try:
			if channelName in self.nameList:
				return channel
			r = reducedName(channelName)
			if r in self.reducedList:
				return self.nameList[self.reducedList.index(r)]
		except:
			pass
		return channelName

	def primaryByName(self, channelName):  # if a picon-by-name already exists, use its name
		try:
			if exists("%s%s.png" % (self.piconfolder, channelName)):
				return channelName
			for c in getInteroperableNames(channelName):
				if exists(self.piconfolder + c + '.png'):
					return c
		except:
			pass
		return channelName

	##################################### /OH #############################################

	def downloadPicons(self):
		no_drive = False
		if self['list'].getCurrent():
			if not isdir(self.picondir):
				txt = "%s\n" % self.picondir + _("is not installed.")
				self.session.open(MessageBox, txt, MessageBox.TYPE_INFO, timeout=3)
				no_drive = True

		self.prepByNameList()  #### OH #####
		if not no_drive:
			if not isdir(self.piconfolder):
				print("[PiconManager] create folder %s" % self.piconfolder)
				makedirs(self.piconfolder)
			self['piconpath2'].setText(self.piconfolder)
			urls = []
			if int(self.countchlist) > 0 and not self.keyLocked and self['list'].getCurrent():
				if len(self['list'].getCurrent()[0]) >= 2:
					f = open("/tmp/picon_dl_err", "w")
					f.write(self['list'].getCurrent()[0][0] + "\n" + "#" * 50 + "\n")
					f.close()
					self['piconpath2'].setText(_("loading"))
					self.auswahl = self['list'].getCurrent()[0][1] + "/"
					for channel in self.chlist:
						downloadPiconUrl = None
						if "by name" in self['list'].getCurrent()[0][0].lower():
							#downloadPiconUrl = quote(channel[1] + ".png")     #### OH #####
							#downloadPiconPath = "%s%s.png" % (self.piconfolder, channel[1])     #### OH #####
							downloadPiconUrl = quote(self.comparableChannelName(channel[1]) + ".png")  #### OH #####
							downloadPiconPath = "%s%s.png" % (self.piconfolder, self.primaryByName(channel[1]))  #### OH #####
						else:
							downloadPiconUrl = str(channel[0])
							downloadPiconUrl = downloadPiconUrl.split("http")[0]
							downloadPiconUrl = downloadPiconUrl.split("rtmp")[0]
							downloadPiconUrl = "%s:" % downloadPiconUrl.split("::")[0].rstrip(':')  #### OH #####
							if downloadPiconUrl.startswith('4097:'):
								downloadPiconUrl = '1%s' % downloadPiconUrl[4:]  #### OH #####
							downloadPiconUrl = downloadPiconUrl.replace(':', '_')
							downloadPiconUrl = "%s.png" % downloadPiconUrl[:-1]
							downloadPiconPath = self.piconfolder + downloadPiconUrl  # .replace("%20"," ")
						if downloadPiconUrl:
							downloadPiconUrl = self.auswahl + downloadPiconUrl
							urls.append((downloadPiconUrl, downloadPiconPath))

			if len(urls) > 0:
				self.countload = 0
				self.counterrors = 0
				ds = defer.DeferredSemaphore(tokens=10)
				downloads = [ds.run(self.download, downloadPiconUrl, downloadPiconPath).addCallback(self.downloadDone).addErrback(self.downloadError) for downloadPiconUrl, downloadPiconPath in urls]
				finished = defer.DeferredList(downloads).addErrback(self.dataError)

	def download(self, downloadPiconUrl, downloadPiconPath):
		self.aktdl_pico = splitext(basename(downloadPiconPath))[0]
#		return downloadPage(downloadPiconUrl, downloadPiconPath)
		return callInThread(self.threadDownloadPage, downloadPiconUrl, downloadPiconPath, None, None)

	def downloadError(self, error):
		if self.aktdl_pico:
			if not "by name" in self['list'].getCurrent()[0][0].lower():
				for channel in self.chlist:
					if channel[0] == self.aktdl_pico.replace('_', ':') + ":":
						self.aktdl_pico = self.aktdl_pico + " = " + channel[1] + " / " + channel[0]
						notfoundWrite(self.aktdl_pico)
		self.counterrors += 1
		self['piconerror'].setText(_("Not found Picons:") + " %s" % self.counterrors)
		total = self.countload + self.counterrors
		self["piconslider"].setValue(total)
		if self.countchlist == total:
			self.checkDouble(5)

	def downloadDone(self, data):
		self.countload += 1
		self['picondownload'].setText(_("Loaded Picons:") + " %s" % self.countload)
		total = self.countload + self.counterrors
		self["piconslider"].setValue(total)
		if self.countchlist == total:
			self.checkDouble(5)
			self.getFreeSpace()

	def checkDouble(self, num=0):
		if num == 5:
			try:
				remove("/tmp/piconmanager_err")
			except:
				pass
			lena = 1
			self['piconpath2'].setText(_("Clean up the directory"))
			for channel in self.chlist:
				downloadPiconUrl = channel[0]
				downloadPiconUrl = str(downloadPiconUrl).split("http")[0]
				downloadPiconUrl = str(downloadPiconUrl).split("rtmp")[0]
				downloadPiconUrl = downloadPiconUrl.replace(':', '_')
				downloadPiconUrl = self.piconfolder + downloadPiconUrl[:-1] + ".png"
				d2 = self.piconfolder + channel[1] + ".png"
				try:
					if exists(downloadPiconUrl) and exists(d2):
						if "by name" in self['list'].getCurrent()[0][0].lower():
							remove(downloadPiconUrl)
						else:
							remove(d2)

				except:
					pass
				if lena < len(self.chlist):
					lena += 1
				else:
					self['piconerror'].setText(_("Not found Picons:") + " %s" % self.counterrors)
					self['piconpath2'].setText(_("Download finished !"))

	def dataError2(self, error=None):
		if hasattr(self, "server_url"):
			errorWrite(str(self.server_url) + "\n")
			self.tried_mirrors.append(self.server_url)
			all_mirrors = True
			for x in server_choices:
				if x[0] not in self.tried_mirrors:
					self.server_url = x[0]
					all_mirrors = False
					break
			if all_mirrors:
				self.channelMenuList.setList(list(map(ListEntry, [(_("Sorry, service is temporarily unavailable"),)])))
			else:
				self.getPiconList()

	def dataError(self, error):
		print("[PiconManager] ERROR:%s" % error)
		try:
			if "500 Internal Server Error" in error:
				self.session.open(MessageBox, _("Server temporarily unavailable"), MessageBox.TYPE_ERROR, timeout=10)
		except TypeError:
			pass
		errorWrite(str(len(self.auswahl)) + " - " + str(self.auswahl) + "\n" + str(error) + "\n")
		self["picon"].hide()

	def showPiconFile(self, picPath, data=None):
		if exists(picPath):
			self["picon"].show()
			if picPath is not None:
				self["picon"].instance.setPixmapFromFile(picPath)


class PiconManagerFolderScreen(Screen):
	skin = """
		<screen position="center,center" size="650,400" title=" ">
			<widget name="media" position="10,10" size="540,30" valign="top" font="Regular;22" />
			<widget name="folderlist" position="10,45" zPosition="1" size="540,300" scrollbarMode="showOnDemand"/>
			<ePixmap position="10,370" size="260,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_red.png" alphatest="on" />
			<ePixmap position="210,370" size="260,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_green.png" alphatest="on" />
			<widget render="Label" source="key_red" position="40,372" size="100,20" valign="center" halign="left" zPosition="2" font="Regular;18" foregroundColor="white" />
			<widget render="Label" source="key_green" position="240,372" size="70,20" valign="center" halign="left" zPosition="2" font="Regular;18" foregroundColor="white" />
		</screen>
		"""

	def __init__(self, session, initDir, plugin_path=None):
		Screen.__init__(self, session)

		if not initDir or not isdir(initDir):
			initDir = "/usr/share/enigma2/"

		self["folderlist"] = FileList(initDir, inhibitMounts=False, inhibitDirs=False, showMountpoints=False, showFiles=False)
		self["media"] = Label()
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"back": self.cancel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"ok": self.ok,
			"green": self.green,
			"red": self.cancel
		}, -1)
		self.title = _("Choose Picon folder")
		try:
			self["title"] = StaticText(self.title)
		except:
			print('self["title"] was not found in skin')
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))

	def cancel(self):
		self.close(None)

	def green(self):
		directory = self["folderlist"].getSelection()[0]
		if (directory.endswith("/")):
			self.fullpath = self["folderlist"].getSelection()[0]
		else:
			self.fullpath = self["folderlist"].getSelection()[0] + "/"
		self.close(self.fullpath)

	def up(self):
		self["folderlist"].up()
		self.updateFile()

	def down(self):
		self["folderlist"].down()
		self.updateFile()

	def left(self):
		self["folderlist"].pageUp()
		self.updateFile()

	def right(self):
		self["folderlist"].pageDown()
		self.updateFile()

	def ok(self):
		if self["folderlist"].canDescent():
			self["folderlist"].descent()
			self.updateFile()

	def updateFile(self):
		currFolder = self["folderlist"].getSelection()[0]
		self["media"].setText(currFolder)


class pm_conf(Screen, ConfigListScreen, HelpableScreen):
	skin = """
		<screen position="center,center" size="600,480" title="Select Color" >
		<widget name="config" position="10,5" size="580,430" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,440" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="155,440" size="140,40" alphatest="on" />
		<widget name="key_red" position="10,443" zPosition="1" size="140,35" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" noWrap="1" shadowOffset="-1,-1" />
		<widget name="key_green" position="155,443" zPosition="1" size="140,35" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" noWrap="1" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session):
		self.liste = []
		self.size = config.plugins.piconmanager.size.value
		self.creator = config.plugins.piconmanager.creator.value
		self.bit = config.plugins.piconmanager.bit.value
		self.server = config.plugins.piconmanager.server.value
		self.alter = config.plugins.piconmanager.alter.value
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		ConfigListScreen.__init__(self, self.liste, on_change=self.load_list)
		self.setTitle(_("PiconManagerMod - Settings"))
		self["key_green"] = Label(_("OK"))
		self["key_red"] = Label(_("Cancel"))

		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
		{
			"cancel": (self.cancel, _("Cancel")),
			"ok": (self.save, _("OK and exit")),
		}, -1)

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"green": (self.save, _("OK and exit")),
			"red": (self.cancel, _("Cancel")),
		}, -1)
		self.onLayoutFinish.append(self.load_list)

	def load_list(self):
		self.liste = []
		if len(server_choices) > 1:
			self.liste.append(getConfigListEntry(_("Select Server:"), config.plugins.piconmanager.server))
		self.liste.append(getConfigListEntry(_("Set Filter:"),))
		self.liste.append(getConfigListEntry(_("Size"), config.plugins.piconmanager.size))
		self.liste.append(getConfigListEntry(_("Creator"), config.plugins.piconmanager.creator))
		self.liste.append(getConfigListEntry(_("Color depth: "), config.plugins.piconmanager.bit))
		self.liste.append(getConfigListEntry(_("Not older than X days:"), config.plugins.piconmanager.alter))
		self.liste.append(getConfigListEntry("------ " + _("Option:") + " ------",))
		self.liste.append(getConfigListEntry(_("Remember permanently?"), config.plugins.piconmanager.saving))
		self.liste.append(getConfigListEntry(_("Activate debug logging?"), config.plugins.piconmanager.debug))
		self["config"].setList(self.liste)

	def save(self):
		self.size = config.plugins.piconmanager.size.value
		self.creator = config.plugins.piconmanager.creator.value
		self.bit = config.plugins.piconmanager.bit.value
		self.alter = config.plugins.piconmanager.alter.value
		reload_picons = False
		if len(server_choices) > 1:
			if self.server != config.plugins.piconmanager.server.value:
				reload_picons = True
				self.server = config.plugins.piconmanager.server.value
		config.plugins.piconmanager.saving.save()
		if config.plugins.piconmanager.saving.value:
			for x in self.liste:
				if len(x) >= 2:
					x[1].save()
		else:
			for x in self.liste:
				if len(x) >= 2:
					x[1].cancel()
		self.close(self.creator, self.size, self.bit, self.server, True, reload_picons, self.alter)

	def cancel(self):
		self.close(self.creator, self.size, self.bit, self.server, False, False)


def main(session, **kwargs):
	session.open(PiconManagerScreen)


def Plugins(**kwargs):
	return PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main)

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
# 20250328 recode by @lululla:
# fix progressbar
# skin fixed
# downloaded fixed
# counter fixed
# set and save piconpath
# add remove picons unused
# ##########################

# Built-in
import errno
from uuid import uuid4
from shutil import rmtree
from random import choice
from datetime import date
from re import S, I, search, sub, match
from os import mkdir, makedirs, statvfs, remove, listdir
from os.path import exists, isdir, basename, join

# Third-party
from requests import get, exceptions
from six import ensure_str
from six.moves.urllib.parse import quote
from twisted.internet import defer, threads, reactor
from twisted.internet.reactor import callInThread

# Enigma2
from enigma import (
	eServiceCenter, eServiceReference, gFont,
	eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_VALIGN_CENTER
)
from Screens.ChannelSelection import SimpleChannelSelection, service_types_tv, service_types_radio
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
# from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.HelpMenu import HelpableScreen
from Components.Label import Label
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import (
	config, ConfigSelection, getConfigListEntry, ConfigText,
	ConfigYesNo, ConfigSubsection, ConfigInteger
)
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ProgressBar import ProgressBar
from Components.FileList import FileList
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor

# Local/project-specific
from skin import parameters
from ServiceReference import ServiceReference

from .piconnames import reducedName, getInteroperableNames  # check for by-name-picons that dont fit with VTi Syntax (Picon Buddy Mode)
from . import _, DEFAULT_PICON_PATH, ALTERN_PICON_PATH, getConfigPathList

# constants
pname = _("PiconManager")
pdesc = _("Manage your Picons")
pversion = "2.6-r0"
pdate = "20250328"

picon_tmp_dir = "/tmp/piconmanager/"
picon_debug_file = "/tmp/piconmanager_error"
picon_info_file = "picons/picon_info.txt"
picon_list_file = "zz_picon_list.txt"

server_choices = [("http://picons.vuplus-support.org/", "VTi: vuplus-support.org"), ]

config.plugins.piconmanager = ConfigSubsection()
config.plugins.piconmanager.savetopath = ConfigSelection(default=DEFAULT_PICON_PATH, choices=getConfigPathList())
# config.plugins.piconmanager.piconname = ConfigText(default="picon", fixed_size=False)
config.plugins.piconmanager.selected = ConfigText(default="All", fixed_size=False)
config.plugins.piconmanager.spicon = ConfigText(default="", fixed_size=False)
config.plugins.piconmanager.saving = ConfigYesNo(default=True)
config.plugins.piconmanager.debug = ConfigYesNo(default=False)
config.plugins.piconmanager.server = ConfigSelection(default=server_choices[0][0], choices=server_choices)
config.plugins.piconmanager.alter = ConfigInteger(default=365, limits=(0, 1000))


def create_picon_directory(path):
	path = path.value
	if not exists(path):
		print(f"[DEBUG] Creating directory: {path}")
		makedirs(path)
	else:
		print(f"[DEBUG] Directory already exists: {path}")


create_picon_directory(config.plugins.piconmanager.savetopath)


def ListEntry(entry):
	x, y, w, h = parameters.get("PiconManagerList", (10, 0, 1280, 25))
	return [entry, (eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])]


def errorWrite(error: str):
	if not config.plugins.piconmanager.debug.value:
		return

	try:
		mode = 'a' if exists(picon_debug_file) else 'w'
		with open(picon_debug_file, mode, encoding='utf-8') as f:
			f.write(f"{error}\n")
	except IOError as e:
		print(f"Failed to write to debug log {picon_debug_file}: {str(e)}")
	except Exception as e:
		print(f"Unexpected error while logging: {str(e)}")


def notfoundWrite(picon):
	if config.plugins.piconmanager.debug.value:
		try:
			with open("/tmp/picon_dl_err", "a", encoding="utf-8", errors='replace') as f:
				f.write(f"{picon}\n")
		except (IOError, OSError) as e:
			if e.errno == errno.EROFS:
				print("[PiconManager] Debug log disabled (read-only filesystem)")
			else:
				print(f"[PiconManager] Error writing debug log: {str(e)}")
		except Exception as e:
			print(f"[PiconManager] Unexpected error in debug log: {str(e)}")


def getServiceList(ref):
	try:
		root = eServiceReference(str(ref))
		serviceHandler = eServiceCenter.getInstance()
		if serviceHandler is None:
			print("[PiconManager] Error: Cannot get service handler instance")
			return []
		return serviceHandler.list(root).getContent("SN", True) or []
	except Exception as e:
		print(f"[PiconManager] Error getting service list: {str(e)}")
		return []


def getTVBouquets():
	try:
		bouquet_ref = service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
		return getServiceList(bouquet_ref)
	except Exception as e:
		print(f"[PiconManager] Error getting TV bouquets: {str(e)}")
		return []


def getRadioBouquets():
	try:
		bouquet_ref = service_types_radio + ' FROM BOUQUET "bouquets.radio" ORDER BY bouquet'
		return getServiceList(bouquet_ref)
	except Exception as e:
		print(f"[PiconManager] Error getting Radio bouquets: {str(e)}")
		return []


def buildChannellist():
	channellist = []
	try:
		tvbouquets = getTVBouquets()
		radiobouquets = getRadioBouquets()
		allbouquets = tvbouquets + radiobouquets
		bouquet_count = len(allbouquets)
		print(f"[PiconManager] Found {bouquet_count} bouquets")

		for bouquet in allbouquets:
			if not bouquet or not bouquet[0]:
				continue

			bouquet_list = getServiceList(bouquet[0])
			if bouquet_list:
				channellist.extend(
					(serviceref, servicename)
					for serviceref, servicename in bouquet_list
					if serviceref and servicename
				)

		print("[PiconManager] Built channel list with", len(channellist), "entries")
		return channellist
	except Exception as e:
		print(f"[PiconManager] Critical error building channel list: {str(e)}")
		return []


class PiconManagerScreen(Screen, HelpableScreen):
	skin = """
	<screen name="PiconManager" title="PiconManager" position="center,center" size="1160,650">
		<widget name="piconpath" position="20,10" size="190,30" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="3" halign="left" />
		<widget name="piconpath2" position="210,10" size="500,30" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="3" halign="left" />
		<widget name="piconspace" position="20,40" size="690,30" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="3" halign="left" />
		<widget name="piconcount" position="20,70" size="690,30" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="3" halign="left" />
		<widget name="picondownload" position="20,100" size="690,30" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="3" halign="left" />
		<widget name="piconerror" position="20,130" size="690,30" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="3" halign="left" />
		<widget name="piconslidername" position="20,160" size="190,30" font="Regular;20" foregroundColor="#00fff000" transparent="1" zPosition="3" halign="left" />
		<widget name="selectedname" position="20,190" size="160,30" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="3" halign="left" />
		<widget name="selected" position="180,190" size="210,30" noWrap="1" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="3" halign="left" />
		<widget name="creatorname" position="20,220" size="160,30" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="3" halign="left" />
		<widget name="creator" position="180,220" size="210,30" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="3" halign="left" />
		<widget name="sizename" position="390,190" size="200,30" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="3" halign="left" />
		<widget name="size" position="590,190" size="150,30" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="3" halign="left" />
		<widget name="bitname" position="390,220" size="200,30" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="3" halign="left" />
		<widget name="bit" position="590,220" size="150,30" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="3" halign="left" />
		<widget name="spiconname" position="20,250" size="190,30" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="3" halign="left" />
		<widget name="spicon" position="180,250" size="210,30" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="3" halign="left" />
		<widget name="altername" position="390,250" size="200,30" font="Regular;20" foregroundColor="#00fba207" transparent="1" zPosition="3" halign="left" />
		<widget name="alter" position="590,250" size="150,30" font="Regular;20" foregroundColor="#00f8f2e6" transparent="1" zPosition="3" halign="left" />
		<widget name="piconslider" position="213,171" size="500,10" pixmap="skin_default/progress_big.png" zPosition="5" />
		<widget name="picon" position="738,10" size="400,240" zPosition="3" transparent="1" borderWidth="0" borderColor="#0000000" alphatest="blend" />
		<widget name="list" position="10,300" size="1130,295" zPosition="3" foregroundColor="#00ffffff" foregroundColorSelected="#00fff000" scrollbarMode="showOnDemand" transparent="1" />
		<widget name="key_red" position="42,615" size="200,25" transparent="1" font="Regular;20" />
		<widget name="key_green" position="265,615" size="200,25" transparent="1" font="Regular;20" />
		<widget name="key_yellow" position="466,615" size="200,25" transparent="1" font="Regular;20" />
		<widget name="key_blue" position="714,615" size="200,25" transparent="1" font="Regular;20" />
		<ePixmap position="10,615" size="60,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_red.png" transparent="1" alphatest="on" />
		<ePixmap position="227,615" size="60,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_green.png" transparent="1" alphatest="on" />
		<ePixmap position="436,615" size="60,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="681,615" size="60,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_blue.png" transparent="1" alphatest="on" />
		<ePixmap position="916,610" size="60,35" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_info.png" transparent="1" alphatest="on" />
		<ePixmap position="977,610" size="60,35" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_menu.png" transparent="1" alphatest="on" />
		<ePixmap position="1038,610" size="60,35" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_channel.png" transparent="1" alphatest="on" />
		<ePixmap position="1095,610" size="60,35" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_help.png" transparent="1" alphatest="on" />
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.server_url = config.plugins.piconmanager.server.value
		# self.piconname = config.plugins.piconmanager.piconname.value
		self.picondir = config.plugins.piconmanager.savetopath.value
		self.alter = config.plugins.piconmanager.alter.value
		self.piconfolder = "%s/" % self.picondir
		self.picon_name = ""
		self.piconlist = []
		self.tried_mirrors = []
		self.art_list = []
		self.prev_sel = None
		self.spicon_name = ""
		self.aktdl_pico = None
		self.countload = 0
		self.counterrors = 0
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
		self.activityslider = ProgressBar()
		self["piconslider"] = self.activityslider
		self["piconslider"].hide()
		self['key_red'] = Label(_("Select drive"))
		self['key_green'] = Label(_("Download picons"))
		self['key_yellow'] = Label(_("Select path"))
		self['key_blue'] = Label(_("Remove Picons Unused"))
		self['picon'] = Pixmap()
		self["OkCancelActions"] = HelpableActionMap(
			self, "OkCancelActions",
			{
				"ok": (self.keyOK, _("Show random Picon")),
				"cancel": (self.keyCancel, _("Exit")),
			},
			-2
		)

		self["SetupActions"] = HelpableActionMap(
			self, "SetupActions",
			{
				"1": (self.sel_creator_back, _("Previous picon creator")),
				"3": (self.sel_creator_next, _("Next picon creator")),
				"4": (self.sel_size_back, _("Previous picon size")),
				"6": (self.sel_size_next, _("Next picon size")),
				"7": (self.sel_bit_back, _("Previous color depth")),
				"9": (self.sel_bit_next, _("Next color depth")),
			}
		)

		self["EPGSelectActions"] = HelpableActionMap(
			self, "EPGSelectActions",
			{
				"menu": (self.settings, _("More selections")),
				"nextService": (self.sel_satpos_next, _("Next Group")),
				"prevService": (self.sel_satpos_back, _("Previous Group")),
				"info": (self.set_picon, _("Set / clear standard Picon")),
				"red": (self.changeDrive, _("Select drive")),
				"timerAdd": (self.downloadPicons, _("Download picons")),
				"yellow": (self.keyYellow, _("Select path")),
				"blue": (self.showPiconRemover, _("Open picon remover")),
				# "blue": (self.changePiconName, _("Create folder")),
			},
			-2
		)
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

	def showPiconRemover(self):
		self.session.openWithCallback(
			self.afterRemoval,  # Rimuovi la parentesi qui
			PicRemoverScreen,
			self.piconfolder
		)

	def afterRemoval(self, result=None):  # Aggiungi valore di default
		if result:
			self.getFreeSpace()
			self.session.open(
				MessageBox,
				_("Removed %d unused picons!") % result,
				MessageBox.TYPE_INFO
			)

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
		service2 = ""

		if isinstance(service, eServiceReference):
			service_name = ServiceReference(service).getServiceName()
			service2 = service.toString()
			service = service2.replace(":", "_").rstrip("_") + ".png"

		if service == "":
			config.plugins.piconmanager.spicon.value = service
		else:
			for channel in self.chlist:
				if channel[0] == service2:
					service_name = channel[1]
					break

			config.plugins.piconmanager.spicon.value = service + "|" + service_name

		config.plugins.piconmanager.spicon.save()
		self["spicon"].setText(service_name)
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

	def change_filter_mode(self, direction: int, filter_type: int):
		# Define filter configurations
		filter_configs = {
			0: {
				'config': config.plugins.piconmanager.creator,
				'list': self.creator_list,
				'widget': 'creator',
				'format': _(str)
			},
			1: {
				'config': config.plugins.piconmanager.bit,
				'list': self.bit_list,
				'widget': 'bit',
				'format': _(str)
			},
			2: {
				'config': config.plugins.piconmanager.size,
				'list': self.size_list,
				'widget': 'size',
				'format': _(str)
			},
			3: {
				'config': config.plugins.piconmanager.selected,
				'list': self.art_list,
				'widget': 'selected',
				'format': lambda x: str(x).replace("+", " ").replace("-", " ")
			}
		}

		# Get current filter config
		config_data = filter_configs.get(filter_type)
		if not config_data:
			return

		current_list = config_data['list']
		if not current_list:
			return

		# Calculate new index
		current_value = config_data['config'].value
		try:
			idx = current_list.index(current_value) + direction
		except ValueError:
			idx = 0

		# Handle index wrapping
		idx = max(
			0,
			min(idx, len(current_list) - 1) if direction > 0 else
			len(current_list) - 1 if idx < 0 else idx
		)

		# Update config and UI
		new_value = current_list[idx]
		config_data['config'].value = new_value
		self[config_data['widget']].setText(config_data['format'](new_value))
		config_data['config'].save()

		# Refresh the list
		self.makeList(
			config.plugins.piconmanager.creator.value,
			config.plugins.piconmanager.size.value,
			config.plugins.piconmanager.bit.value,
			config.plugins.piconmanager.server.value,
			True,
			False,
			config.plugins.piconmanager.alter.value
		)

	def getFreeSpace(self):
		if not isdir(self.picondir):
			self['piconspace'].setText(_("FreeSpace: Drive Not Found!"))
			return

		try:
			stat = statvfs(self.picondir)
			free_bytes = stat.f_frsize * stat.f_bfree

			if free_bytes >= 1024**3:  # 1 GB
				free_space = round(free_bytes / 1024**3, 1)
				unit = "GB"
			else:
				free_space = round(free_bytes / 1024**2, 1)
				unit = "MB"

			self['piconspace'].setText(
				_("FreeSpace:") + f" {free_space} {unit}"
			)

		except OSError as e:
			self['piconspace'].setText(
				_("FreeSpace: Error - {error}").format(error=str(e))
			)

	def showPic(self):
		self["picon"].hide()

		current_item = self['list'].getCurrent()
		if not self.piconlist or not current_item or len(current_item[0]) < 3:
			return

		self.auswahl = current_item[0][2]
		picon_name = basename(self.auswahl)

		if config.plugins.piconmanager.spicon.value:
			is_by_name = "by name" in current_item[0][0].lower()
			parts = config.plugins.piconmanager.spicon.value.split('|')

			if is_by_name and len(parts) > 1:
				# Format service name picon
				picon_sname = parts[1].replace(" ", "%20") + ".png"
			else:
				# Use regular service reference picon
				picon_sname = parts[0] if parts else ""

			if picon_sname:
				self.auswahl = self.auswahl.replace(picon_name, picon_sname)

		self.downloadPiconPath = join(
			self.piconTempDir,
			f"{current_item[0][4]}.png"
		)

		if not exists(self.downloadPiconPath):
			callInThread(
				self.threadDownloadPage,
				self.auswahl,
				self.downloadPiconPath,
				self.showPiconFile,
				self.dataError
			)
		else:
			self.showPiconFile(self.downloadPiconPath, None)

	def getPiconList(self):
		print("[PiconManager] Started fetching picon list...")

		self['piconcount'].setText(f"{_('Channels:')} {self.countchlist}")

		selected_text = str(config.plugins.piconmanager.selected.value)
		formatted_text = selected_text.replace("_", ", ").replace("+", " ").replace("-", " ")
		self['selected'].setText(_(formatted_text))

		spicon_value = config.plugins.piconmanager.spicon.value
		if spicon_value:
			parts = spicon_value.split('|')
			display_text = parts[1] if len(parts) > 1 else parts[0]
		else:
			display_text = ""
		self['spicon'].setText(display_text)

		url = f"{self.server_url}{picon_info_file}"
		print(f"[PiconManager] Server: {self.server_url}")

		if config.plugins.piconmanager.selected.value == _("All"):
			config.plugins.piconmanager.selected.setValue("All")
			config.plugins.piconmanager.selected.save()

		loading_entry = ListEntry((_("Loading, please wait..."),))
		self.channelMenuList.setList([loading_entry])

		callInThread(
			self.threadGetPage,
			url,
			self.parsePiconList,
			self.dataError2
		)

	def threadGetPage(self, link, success, fail):
		try:
			response = get(link, timeout=(3.05, 6))
			response.raise_for_status()
		except exceptions.RequestException as error:
			fail(error)
		else:
			success(response.content)

	def parsePiconList(self, data: str):
		print("[PiconManager] Parsing picon list...")

		self.size_list = ["All"]
		self.bit_list = ["All"]
		self.creator_list = ["All"]
		self.piconlist = []
		self.art_list = ["All"]

		data = ensure_str(data).replace("\xc2\x86", "").replace("\xc2\x87", "")
		picon_data = [line for line in data.split("\n") if line and not line.startswith('<meta')]

		for picon_info in picon_data:
			info_list = picon_info.split(';')
			if len(info_list) < 9:
				continue

			# Extract picon info
			dirUrl = join(self.server_url, info_list[0]).replace(" ", "%20")
			picUrl = join(self.server_url, info_list[0], info_list[1]).replace(" ", "%20")
			p_creator = info_list[5]
			p_bit = info_list[6].replace(' ', '').lower().replace('bit', ' bit')
			p_size = info_list[7].replace(' ', '').lower()
			p_pos = info_list[4]

			for item, target_list in [
				(p_size, self.size_list),
				(p_bit, self.bit_list),
				(p_creator, self.creator_list),
				(p_pos, self.art_list)
			]:
				if item not in target_list:
					target_list.append(item)

			p_name = f"{p_pos} | {p_creator} - {info_list[3]} | {p_size} | {p_bit} | {info_list[2]} | {info_list[8]}"
			self.piconlist.append((
				p_name, dirUrl, picUrl,
				(p_creator, p_size, p_bit, p_pos),
				str(uuid4()), info_list[0]
			))

		if not self.piconlist:
			self.dataError2(None)
			return

		for lst in [self.size_list, self.bit_list, self.creator_list, self.art_list]:
			lst.sort()
		self.piconlist.sort(key=lambda x: x[0].lower())

		self._update_config_selections()

		self.keyLocked = False
		alter = config.plugins.piconmanager.alter.value
		self.makeList(
			config.plugins.piconmanager.creator.value,
			config.plugins.piconmanager.size.value,
			config.plugins.piconmanager.bit.value,
			self.server_url,
			True,
			False,
			alter
		)

	def _update_config_selections(self):
		"""Update configuration selections while preserving current values."""
		# Handle 'All' selection case
		if config.plugins.piconmanager.selected.value not in self.art_list:
			config.plugins.piconmanager.selected.setValue("All")
			self['selected'].setText(_("All"))

		# Update config selections
		config_attrs = [
			('bit', self.bit_list),
			('size', self.size_list),
			('creator', self.creator_list)
		]

		for attr, source_list in config_attrs:
			prev_value = getattr(config.plugins.piconmanager, attr).value if hasattr(config.plugins.piconmanager, attr) else None
			choices = self.createChoiceList(source_list, [("All", _("All"))])
			setattr(config.plugins.piconmanager, attr, ConfigSelection(default="All", choices=choices))
			if prev_value:
				getattr(config.plugins.piconmanager, attr).value = prev_value

		# Update UI text
		self['creator'].setText(_(str(config.plugins.piconmanager.creator.value)))
		self['size'].setText(_(str(config.plugins.piconmanager.size.value)))
		self['bit'].setText(_(str(config.plugins.piconmanager.bit.value)))

	def createChoiceList(self, choicelist, default_choice):
		ret = default_choice
		if len(choicelist):
			for x in choicelist:
				ret.append((x, _("%s") % x))
		return ret

	def makeList(
		self,
		creator="All",
		size="All",
		bit="All",
		server=config.plugins.piconmanager.server.value,
		update=True,
		reload_picons=False,
		alter=0
	):

		"""
		Filter and display the picon list based on specified criteria.

		Args:
			creator: Filter by creator name ('All' for no filter)
			size: Filter by size ('All' for no filter)
			bit: Filter by bit depth ('All' for no filter)
			server: Server URL to use
			update: Whether to update the list display
			reload_picons: Whether to reload the picon list from server
			alter: Days threshold for filtering by date (0 = no date filter)
		"""
		if reload_picons:
			self.server_url = server
			self.channelMenuList.setList([])
			self.getPiconList()
			return

		if not update:
			return

		self['alter'].setText(str(alter))
		art = config.plugins.piconmanager.selected.value
		new_list = []
		today = date.today()

		for item in self.piconlist:
			if alter > 0:
				date_str = str(item[0]).split(" | ")[4].split(".")
				try:
					item_date = date(int(date_str[2]), int(date_str[1]), int(date_str[0]))
					if (today - item_date).days > alter:
						continue
				except (ValueError, IndexError):
					continue

				art_match = (art == "All" or item[3][3] == art)
				creator_match = (creator == "All" or item[3][0] == creator)
				size_match = (size == "All" or item[3][1] == size)
				bit_match = (bit == "All" or item[3][2] == bit)

				if not (art_match and creator_match and size_match and bit_match):
					continue

			new_list.append(item)

		if new_list:
			self.channelMenuList.setList(list(map(ListEntry, new_list)))
		else:
			no_results_msg = _("No search results, please change filter options...")
			self.channelMenuList.setList(list(map(ListEntry, [(no_results_msg,)])))

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
					# Strip whitespace and filter out empty lines
					self.picon_files = [line.strip() for line in f.readlines() if line.strip()]
			if self.picon_files:
				self.picon_name = choice(self.picon_files)
				# URL-encode the picon name to handle special characters
				encoded_picon_name = quote(self.picon_name)
				downloadPiconUrl = f"{self.server_url}{self.cur_selected_dir}/{encoded_picon_name}"
				self.downloadPiconPath = f"{self.piconTempDir}{self.auswahl}.png"
				self.keyLocked = False
				callInThread(self.threadDownloadPage, downloadPiconUrl, self.downloadPiconPath, self.showPiconFile, self.dataError)
			else:
				print("[PiconManager] Empty picon list file")
				self['piconerror'].setText(_("No picons available in selected list"))

	def keyCancel(self):
		config.plugins.piconmanager.savetopath.value = self.picondir
		config.plugins.piconmanager.savetopath.save()
		# config.plugins.piconmanager.piconname.value = self.piconname
		# config.plugins.piconmanager.piconname.save()
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
			# self.piconname = res.split("/")[-2]
			self['piconpath2'].setText(self.piconfolder)

	def changeDrive(self):
		current = self.piconfolder.rstrip("/")
		try:
			idx = ALTERN_PICON_PATH.index(current)
			idx = (idx + 1) % len(ALTERN_PICON_PATH)
		except ValueError:
			idx = 0

		self.picondir = ALTERN_PICON_PATH[idx]
		self.piconfolder = self.picondir + "/"
		self["piconpath2"].setText(self.piconfolder)
		print("[PiconManager] set picon path to: %s" % self.piconfolder)
		self.getFreeSpace()

	""" paused for remove picons space
	def changePiconName(self):
		self.session.openWithCallback(self.gotNewPiconName, VirtualKeyBoard, title=(_("Enter Picon Dir:")), text=self.piconname)

	def gotNewPiconName(self, name):
		if name is not None:
			self.piconname = name
			self.piconfolder = "%s%s/" % (self.picondir, self.piconname)
			self['piconpath2'].setText(self.piconfolder)
			print("[PiconManager] set picon path to: %s" % self.piconfolder)
	"""

	def url2Str(self, url):
		try:
			from urllib.request import Request, urlopen
			header = {
				'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
				'Accept-Charset': 'utf-8;q=0.7,*;q=0.7',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
			}
			searchrequest = Request(url, None, header)
			return urlopen(searchrequest).read()
		except:
			return ''

	def prepByNameList(self):
		self.nameList = []
		self.reducedList = []
		try:
			if "by name" not in self['list'].getCurrent()[0][0].lower():
				return 1
			self.auswahl = self['list'].getCurrent()[0][4]
			self.cur_selected_dir = self['list'].getCurrent()[0][5]
			self.picon_list_file = self.piconTempDir + self.auswahl + "_list"
			url = self.server_url + self.cur_selected_dir + "/" + self.picon_list_file
			content = self.url2Str(url)
			if content:
				for x in content.split('\n'):
					if x.endswith('.png'):
						self.nameList.append(x[:-4])
						self.reducedList.append(reducedName(x[:-4]))
		except Exception:
			pass

	def comparableChannelName(self, channelName: str):
		"""Find a comparable channel name from the picon name list.
		Args:
			channelName: The original channel name to match
		Returns:
			The matching name from the picon list if found, otherwise the original name
		"""
		try:
			if channelName in self.nameList:
				return channelName

			reduced_name = reducedName(channelName)
			if reduced_name in self.reducedList:
				return self.nameList[self.reducedList.index(reduced_name)]

		except Exception as e:
			print(f"Error in comparableChannelName: {str(e)}")

		return channelName

	def primaryByName(self, channelName: str):
		try:
			picon_path = join(self.piconfolder, f"{channelName}.png")
			if exists(picon_path):
				return channelName

			for variant in getInteroperableNames(channelName):
				variant_path = join(self.piconfolder, f"{variant}.png")
				if exists(variant_path):
					return variant

		except Exception as e:
			print(f"Error in primaryByName: {str(e)}")

		return channelName

	def downloadPicons(self):
		no_drive = False
		self.countload = 0
		self.counterrors = 0

		if self['list'].getCurrent():
			if not isdir(self.picondir):
				txt = f"{self.picondir}\n{_('is not installed.')}"
				self.session.open(MessageBox, txt, MessageBox.TYPE_INFO, timeout=3)
				no_drive = True

		self.prepByNameList()

		if not no_drive:
			try:
				if not isdir(self.piconfolder):
					print(f"[PiconManager] create folder {self.piconfolder}")
					makedirs(self.piconfolder)
			except OSError as e:
				self.session.open(MessageBox, f"Error creating folder: {str(e)}", MessageBox.TYPE_ERROR)
				return

			self['piconpath2'].setText(self.piconfolder)
			urls = []
			if int(self.countchlist) > 0 and not self.keyLocked and self['list'].getCurrent():
				if len(self['list'].getCurrent()[0]) >= 2:
					with open("/tmp/picon_dl_err", "w") as f:
						f.write(f"{self['list'].getCurrent()[0][0]}\n{'#' * 50}\n")

					self['piconpath2'].setText(_("loading"))
					self.auswahl = f"{self['list'].getCurrent()[0][1]}/"

					for channel in self.chlist:
						try:
							downloadPiconUrl, downloadPiconPath = self.getDownloadPaths(channel)
							if downloadPiconUrl and downloadPiconPath:
								urls.append((downloadPiconUrl, downloadPiconPath))
						except Exception as e:
							print('error: ', e)
							self.counterrors += 1
							reactor.callFromThread(self.update_error_display)

		if urls:
			total_downloads = len(urls)
			self.activityslider.setRange((0, total_downloads))
			self.activityslider.setValue(0)
			self["piconslider"] = self.activityslider
			self["piconslider"].show()
			ds = defer.DeferredSemaphore(tokens=10)
			downloads = []

			def update_progress(success=True):
				if success:
					self.countload += 1
				else:
					self.counterrors += 1

				current_value = self.countload + self.counterrors
				self.activityslider.setValue(current_value)
				self['picondownload'].setText(_("Picon loaded:") + f" {self.countload}")
				self['piconerror'].setText(_("Picons not found: ") + " %s" % self.counterrors)

			for url, path in urls:
				d = ds.run(
					threads.deferToThread,
					self.threadDownloadPage,
					url,
					path
				)
				d.addCallbacks(update_progress, update_progress)
				downloads.append(d)

			def final_update(result):
				message = _("Downloads completed") + "\n" + _("Success: %d") % self.countload + "\n" + _("Errors: %d") % self.counterrors
				reactor.callFromThread(
					self.session.open,
					MessageBox,
					message,
					MessageBox.TYPE_INFO,
					timeout=10
				)
				reactor.callFromThread(self.cleanup_after_download)

			defer.DeferredList(downloads).addCallback(final_update)

	def showPiconFile(self, picPath, data=None):
		if picPath and exists(picPath):
			try:
				self["picon"].instance.setPixmapFromFile(picPath)
				self["picon"].show()
			except Exception as e:
				print(f"[PiconManager] Error loading picon: {str(e)}")
				errorWrite(f"Failed to load {picPath}: {str(e)}")
				self["picon"].hide()
		else:
			print(f"[PiconManager] Picon file not found: {picPath}")
			self["picon"].hide()

	def threadDownloadPage(self, url, file_path, success_callback, error_callback):
		try:
			response = get(url, stream=True, timeout=10)
			response.raise_for_status()
			with open(file_path, 'wb') as f:
				for chunk in response.iter_content(chunk_size=8192):
					if chunk:
						f.write(chunk)
			# Verify the downloaded file is a valid PNG
			if not self.is_valid_png(file_path):
				raise ValueError("Invalid PNG file")
			reactor.callFromThread(success_callback, file_path, None)
		except Exception as e:
			error_msg = f"Download failed: {url} - {str(e)}"
			errorWrite(error_msg)
			reactor.callFromThread(error_callback, error_msg)

	def is_valid_png(self, file_path):
		try:
			with open(file_path, 'rb') as f:
				header = f.read(8)
				return header == b'\x89PNG\r\n\x1a\n'
		except:
			return False

	def cleanup_after_download(self):
		"""Callback after downloaded"""
		try:
			self.countload += 1
			self['picondownload'].setText(_("Picon loaded:") + f" {self.countload}")
			self["piconpath2"].setText(self.piconfolder)
			self.activityslider.setValue(self.activityslider.max)
			self.checkDouble(5)
			self.getFreeSpace()
		except Exception as e:
			print(f"[PiconManager] Error in downloadDone handler: {str(e)}")

	def update_error_display(self):
		self["piconerror"].setText(_("Picons not found: ") + f" {self.counterrors}")

	def getDownloadPaths(self, channel):
		"""Generate download URL and path for a given channel."""
		try:
			if not channel or len(channel) < 2 or channel[1] == '<n/a>':
				return None, None

			current_item = self['list'].getCurrent()
			if not current_item or "by name" not in current_item[0][0].lower():
				# Service Reference-based path
				service_ref = str(channel[0]).split("::")[0].rstrip(':').replace(':', '_')
				downloadPiconUrl = f"{service_ref}.png"
				downloadPiconPath = join(self.piconfolder, downloadPiconUrl)
			else:
				# Name-based path
				clean_name = self.comparableChannelName(channel[1])
				primary_name = self.primaryByName(channel[1])
				downloadPiconUrl = quote(f"{clean_name}.png")
				downloadPiconPath = join(self.piconfolder, f"{primary_name}.png")

			full_url = f"{self.auswahl}{downloadPiconUrl}"
			return full_url, downloadPiconPath

		except Exception as e:
			print(f"[PiconManager] Error in getDownloadPaths: {str(e)}")
			return None, None

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
					self['piconerror'].setText(_("Picons not found: ") + " %s" % self.counterrors)
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


class PicRemoverScreen(Screen):
	skin = """
	<screen name="PicRemoverScreen" position="center,center" size="1200,700" title="Picon Remover">
		<widget name="piconpath" position="21,4" size="190,30" font="Regular;24" foregroundColor="#00fba207" transparent="1" zPosition="3" halign="left" />
		<widget name="piconpath2" position="219,4" size="500,30" font="Regular;24" foregroundColor="#00f8f2e6" transparent="1" zPosition="3" halign="left" />
		<widget name="piconcount" position="770,4" size="403,30" font="Regular;24" foregroundColor="#00fff000" transparent="1" zPosition="3" halign="left" />
		<widget name="picon" position="766,82" size="400,240" zPosition="3" transparent="1" borderWidth="0" borderColor="#0000000" alphatest="blend" />
		<widget name="list" position="20,44" size="1160,476" itemHeight="35" font="Regular;28" transparent="1" scrollbarMode="showOnDemand" />
		<widget name="info" position="20,540" size="1160,40" font="Regular;26" foregroundColor="#00ffffff" />
		<widget name="key_red" position="42,615" size="200,25" transparent="1" font="Regular;22" />
		<widget name="key_green" position="265,615" size="200,25" transparent="1" font="Regular;22" />
		<ePixmap position="10,615" size="60,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_red.png" transparent="1" alphatest="on" />
		<ePixmap position="227,615" size="60,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PiconManager/pic/button_green.png" transparent="1" alphatest="on" />
	</screen>"""

	def __init__(self, session, picon_path):
		Screen.__init__(self, session)
		self.skinName = "PicRemoverScreen"
		self.piconfolder = picon_path
		self.unused_picons = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		font, size = parameters.get("PiconManagerListFont", ('Regular', 22))
		self.unused_picons.l.setFont(0, gFont(font, size))
		self.unused_picons.l.setItemHeight(25)
		self.setTitle(pname + " " * 3 + _("V") + " %s" % pversion)
		self['list'] = self.unused_picons
		self['list'].onSelectionChanged.append(self.showPic)
		self["info"] = Label()
		self['piconpath'] = Label(_("Picon folder: "))
		self['piconcount'] = Label(_("Reading Picons..."))
		self['piconpath2'] = Label(self.piconfolder)
		self['picon'] = Pixmap()
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Delete"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
			"red": self.close,
			"green": self.executeRemoval,
			"cancel": self.close
		}, -1)

		self.channel_refs = set()
		self.onLayoutFinish.append(self.start_workflow)

	def start_workflow(self):
		if not exists(self.piconfolder):
			self['info'].setText(_("Invalid path!"))
			return

		channel_list = buildChannellist()
		self.channel_refs = self.generate_picon_refs(channel_list)
		files = [f for f in listdir(self.piconfolder) if f.lower().endswith('.png')]
		# matched = [f for f in files if f.lower() in self.channel_refs]
		unmatched = [f for f in files if f.lower() not in self.channel_refs]
		self.unused_picons = [join(self.piconfolder, f) for f in unmatched]
		self['piconcount'].setText(_("To delete: {}").format(len(unmatched)))
		self._update_ui()

	def generate_picon_refs(self, channel_list):
		refs = set()
		for serviceref, servicename in channel_list:
			try:
				sref = eServiceReference(serviceref)
				base = sref.toString().replace(':', '_').rstrip('_')
				refs.add(f"{base}.png")
				refs.add("_".join(base.split("_")[:10]) + ".png")
				clean = self._sanitize(servicename)
				if clean:
					refs.add(f"{clean}.png")
				for suffix in ('', '-hd', '_fhd', '-4k', '_uhd'):
					short = "_".join(base.split("_")[:7])
					refs.add(f"{short}{suffix}.png")
			except Exception as e:
				notfoundWrite(f"Ref error for {serviceref}: {e}")
		return {f.lower() for f in refs}

	def _scan_picons(self):
		self.unused_picons = []
		valid, invalid = 0, 0
		for f in listdir(self.piconfolder):
			if not f.lower().endswith('.png') or not self.is_valid_picon_name(f):
				invalid += 1
				continue
			name = f.lower()
			if name in self.channel_refs:
				valid += 1
			else:
				self.unused_picons.append(join(self.piconfolder, f))
		print(f"[DEBUG] Valid: {valid}, Invalid: {invalid}, Unused: {len(self.unused_picons)}")

	def _sanitize_name(self, name):
		"""Service name cleaning for precise match"""
		if not name:
			return ""
		return sub(r'[^\w\-_]', '', name.replace(' ', '_')).lower()

	def _update_ui(self):
		"""Update UI with external data"""
		try:
			self.display_entries = [[basename(p)] for p in self.unused_picons]
			templated_list = [ListEntry(e) for e in self.display_entries]
			count = len(templated_list)
			self['piconcount'].setText(_("Picons to be deleted: {}").format(count))

			if count == 0:
				self["info"].setText(_("No picons to delete"))
				self["list"].setList(list(map(ListEntry, [(_("No picons to delete"),)])))
			else:
				count_text = _("Picons found: {}").format(count)
				self["info"].setText(count_text)
				self.showPic()
				self["list"].setList(templated_list)
			print(f"[DEBUG] Picons not used: {len(templated_list)}")
		except Exception as e:
			print(f"UI update error: {str(e)}")
			self["info"].setText(_("Data display error"))

	def executeRemoval(self):
		"""Perform deletion with external logging"""
		if not self.unused_picons:
			print("[DEBUG] No unused picons to delete.")
			return

		deleted = 0
		errors = 0
		print(f"[DEBUG] Total picons to remove: {len(self.unused_picons)}")
		for picon in self.unused_picons:
			try:
				picon_path = join(self.piconfolder, picon)
				if not self.is_valid_picon_name(picon):
					print(f"[DEBUG] Skipping invalid file name: {picon}")
					continue

				print(f"[DEBUG] Attempting to delete: {picon_path}")
				if exists(picon_path) and picon_path.startswith(self.piconfolder):
					print(f"[DEBUG] Removing picon: {picon_path}")
					remove(picon_path)
					deleted += 1
				else:
					notfoundWrite(f"Skipped invalid path: {picon_path}")
					errors += 1
			except Exception as e:
				notfoundWrite(f"Delete Error: {picon_path} - {str(e)}")
				errors += 1
		if config.plugins.piconmanager.debug.value:
			with open(picon_debug_file, "a") as log:
				log.write(f"Valid References: {self.channel_refs}\n")
				log.write(f"Unmatched Files: {self.unused_picons}\n")
		self._show_result(deleted, errors)

	def _show_result(self, deleted, errors):
		msg = _("Operation completed!") + "\n"
		msg += _("Deleted: {}").format(deleted) + "\n"
		msg += _("Errors: {}").format(errors)
		self.session.openWithCallback(
			self.close,
			MessageBox,
			msg,
			MessageBox.TYPE_INFO
		)

	def showPic(self):
		self["picon"].hide()

		current_index = self["list"].l.getCurrentSelectionIndex()
		print(f"[DEBUG] Current selection index: {current_index}")
		if current_index < 0 or current_index >= len(self.unused_picons):
			print("[DEBUG] Invalid index, nothing to show")
			return

		pic_name = self.unused_picons[current_index]
		pic_path = join(self.piconfolder, pic_name)
		if not exists(pic_path):
			print(f"[DEBUG] Picon file does not exist: {pic_path}")
			return

		self.showPiconFile(pic_path)

	def showPiconFile(self, picPath, data=None):
		if picPath and exists(picPath):
			try:
				self["picon"].instance.setPixmapFromFile(picPath)
				self["picon"].show()
			except Exception as e:
				print(f"[PiconManager] Error loading picon: {str(e)}")
				errorWrite(f"Failed to load {picPath}: {str(e)}")
				self["picon"].hide()
		else:
			print(f"[PiconManager] Picon file not found: {picPath}")
			self["picon"].hide()

	def is_valid_picon_name(self, picon):
		filename = basename(picon)
		valid = bool(match(r'^[\w\-\.]+$', filename))
		print(f"[DEBUG] Validating picon: {filename} -> {'Valid' if valid else 'Invalid'}")
		return valid

	def close(self, result=None):
		super().close(result)


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
		self["actions"] = ActionMap(
			["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
			{
				"back": self.cancel,
				"left": self.left,
				"right": self.right,
				"up": self.up,
				"down": self.down,
				"ok": self.ok,
				"green": self.green,
				"red": self.cancel
			},
			-1
		)
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


class pm_conf(ConfigListScreen, Screen, HelpableScreen):
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

		self["SetupActions"] = HelpableActionMap(
			self, "SetupActions",
			{
				"cancel": (self.cancel, _("Cancel")),
				"ok": (self.save, _("OK and exit")),
			},
			-1
		)

		self["ColorActions"] = HelpableActionMap(
			self, "ColorActions",
			{
				"green": (self.save, _("OK and exit")),
				"red": (self.cancel, _("Cancel")),
			},
			-1
		)

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
		try:
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

			for x in self.liste:
				if len(x) >= 2:
					if config.plugins.piconmanager.saving.value:
						x[1].save()
					else:
						x[1].cancel()

			self.close(
				self.creator,
				self.size,
				self.bit,
				self.server,
				True,
				reload_picons,
				self.alter
			)

		except Exception as e:
			print(f"Error saving piconmanager configuration: {e}")

	def cancel(self):
		self.close(self.creator, self.size, self.bit, self.server, False, False)


def main(session, **kwargs):
	session.open(PiconManagerScreen)


def Plugins(**kwargs):
	return PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main)

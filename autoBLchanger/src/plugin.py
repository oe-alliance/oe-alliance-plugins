# -*- coding: utf-8 -*-
#######################################
# coded by pain2000 - v1.3 (Nov 2022) #
#  modyfied for py3 usage by Mr.Servo #
#######################################

from . import _, myPluginPath
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, NoSave, ConfigNothing
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from enigma import ePicLoad
from os import curdir, walk, sep, rename, remove, symlink, system
from os.path import normpath, abspath, realpath, join, islink, exists, lexists, dirname
from random import randrange

strPluginName = 'autoBLchanger'
strVersionIdx = 'v1.3'
strSearchPath = normpath(myPluginPath + '/logos') + '/'
strTargetPath = '/usr/share/bootlogo.mvi'
strChangeMode = config.plugins.autoBLchanger.changeMode.value  # 'man', 'aut'
strSelectMode = config.plugins.autoBLchanger.selectMode.value  # 0: random, 1: ascending, 2: descending


def searchForFiles(directory=curdir, depth=-1, extensions=('.mvi')):
	foundFiles = []
	for root, dirs, files in walk(abspath(directory)):
		if root[len(directory):].count(sep) < depth or depth < 0:  # check the directory depth to search in
			foundFiles.extend(join(root, fileName) for fileName in files if fileName.lower().endswith(extensions))  # check files with given extensions
	return foundFiles


def checkBootLogo():
	if exists(strTargetPath):  # check if BootLogo already exists
		if islink(strTargetPath):  # check if existing BootLogo is a SymLink
			remove(strTargetPath)  # must be removed
		else:  # no SymLink
			rename(strTargetPath, strTargetPath + '.org')  # rename the original BootLogo to keep it
	else:  # not existing
		if islink(strTargetPath):  # SymLink should be broken
			remove(strTargetPath)  # must be removed


def getBootLogoIdx(lstBootLogos):
	if islink(strTargetPath):  # check if existing BootLogo is a SymLink
		try:
			iBootLogoIdx = lstBootLogos.index(realpath(strTargetPath))  # try to find index of actual used logo
		except:  # SymLink is maybe broken (actual logo not in list)
			iBootLogoIdx = -1
	else:
		iBootLogoIdx = -1
	return iBootLogoIdx


def autoChangeBootLogo():
	try:
		BLogos = searchForFiles(strSearchPath, 1)
		BLogos.sort()
		if BLogos:  # BootLogos found
			iLogoIdx = getBootLogoIdx(BLogos)
			checkBootLogo()  # check for BootLogo existence, rename or remove it
			if strSelectMode is '1':  # ascending
				iLogoIdx = iLogoIdx + 1 if iLogoIdx + 1 < len(BLogos) else 0  # increase index by one or set to first index (0)
			elif strSelectMode is '2':  # descanding
				iLogoIdx = len(BLogos) - 1 if iLogoIdx - 1 < 0 else iLogoIdx - 1  # decrease index by one or set to last index
			else:  # random
				iRandIdx = iLogoIdx
				while iLogoIdx == iRandIdx:
					iRandIdx = randrange(len(BLogos))
				iLogoIdx = iRandIdx
			symlink(BLogos[iLogoIdx], strTargetPath)  # create symLink to BootLogo
	except:
		pass


class autoBLchanger(Screen, ConfigListScreen):  # /usr/lib/enigma2/python/Plugins/Extensions/autoBLchanger/images/
	skin = """
	<screen name="autoBLchanger" position="center,center" size="650,715" title="{title_ver}" flags="wfNoBorder" backgroundColor="#00000000">
		<ePixmap pixmap="{path}images/back.png" position="0,0" size="650,715" alphatest="off" transparent="0" zPosition="-1" />
		<eLabel name="myTitle" position="25,6" size="220,30" text="{title}" halign="right" valign="center" font="Console; 25" foregroundColor="#00c8c8c8" transparent="1" zPosition="1" />
		<eLabel name="myVersion" position="255,6" size="100,30" text="({version})" halign="left" valign="bottom" font="Console; 18" foregroundColor="#00c8c8c8" transparent="1" zPosition="1" />
		<widget name="config" position="25,60" size="600,480" enableWrapAround="1" scrollbarMode="showNever" font="Regular; 24" foregroundColor="#00c8c8c8" foregroundColorSelected="#00c8c8c8" backgroundColorSelected="#005a5a5a" itemHeight="30" transparent="1" zPosition="1" />
		<widget name="LogosInfo" position="25,550" size="600,80" halign="left" valign="top" font="Console; 22" foregroundColor="#00c8c8c8" transparent="1" zPosition="1" />
		<widget name="LogosPict" position="325,371" size="300,169" alphatest="on" zPosition="2" borderWidth="1" borderColor="#005a5a5a" />
		<widget name="key_red" position="25,640" size="150,45" halign="center" valign="center" font="Regular; 20" foregroundColor="#00c8c8c8" transparent="1" zPosition="1" />
		<widget name="key_green" position="175,640" size="150,45" halign="center" valign="center" font="Regular; 20" foregroundColor="#00c8c8c8" transparent="1" zPosition="1" />
		<widget name="key_yellow" position="325,640" size="150,45" halign="center" valign="center" font="Regular; 20" foregroundColor="#00c8c8c8" transparent="1" zPosition="1" />
		<widget name="key_blue" position="475,640" size="150,45" halign="center" valign="center" font="Regular; 20" foregroundColor="#00c8c8c8" transparent="1" zPosition="1" />
		<ePixmap pixmap="{path}images/red.png" position="25,685" size="150,5" alphatest="blend" transparent="1" zPosition="1" />
		<ePixmap pixmap="{path}images/green.png" position="175,685" size="150,5" alphatest="blend" transparent="1" zPosition="1" />
		<ePixmap pixmap="{path}images/yellow.png" position="325,685" size="150,5" alphatest="blend" transparent="1" zPosition="1" />
		<ePixmap pixmap="{path}images/blue.png" position="475,685" size="150,5" alphatest="blend" transparent="1" zPosition="1" />
	</screen>""".format(title_ver=strPluginName + ' - ' + strVersionIdx, title=strPluginName, version=strVersionIdx, path=myPluginPath)

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		self.session = session
		self.idxOff = 3
		self.conOff = self.idxOff - 1
		self.list = []
		self.Logos = []
		ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
		self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'], {'red': self.cancel, 'cancel': self.cancel, 'green': self.save, 'yellow': self.yellow, 'blue': self.blue, 'ok': self.run}, -2)
		self['key_red'] = Label(_('Cancel'))
		self['key_green'] = Label(_('Save'))
		self['key_yellow'] = Label('')
		self['key_blue'] = Label('')
		self['LogosPict'] = Pixmap()
		self['LogosInfo'] = Label('./.')
		self.changeMode = strChangeMode  # config.plugins.autoBLchanger.changeMode.value
		self.selectMode = strSelectMode  # config.plugins.autoBLchanger.selectMode.value
		self.CurLogoIdx = -2
		self.SelByUser = True
		self.isOrigLogo = False
		self.Scale = AVSwitch().getFramebufferScale()
		self.PicLoad = ePicLoad()
		self.populateConfigList()  # search for BootLogos and fill/show list
		self.CurLogoIdx = getBootLogoIdx(self.Logos)
		if self.CurLogoIdx >= 0:
			self['key_yellow'].setText(_('show current\nBootLogo'))
		if exists(strTargetPath + '.org'):  # for key_blue
			self.isOrigLogo = True
			self['key_blue'].setText(_('reset orig.\nBootLogo'))
		if self.selectionChanged not in self['config'].onSelectionChanged:
			self['config'].onSelectionChanged.append(self.selectionChanged)
		self.onLayoutFinish.append(self.UpdatePicture)

	def populateConfigList(self):
		self.set_changeMode = getConfigListEntry(_('BootLogo ChangeMode :'), config.plugins.autoBLchanger.changeMode, _('change the BootLogo manually or at system startup'))
		self.set_selectMode = getConfigListEntry(_('BootLogo SelectMode :'), config.plugins.autoBLchanger.selectMode, _('order to choose the new BootLogo\n(only effective if \'ChangeMode = startup\')'))
		self.set_fake_entry = NoSave(ConfigNothing())
		self.list = []
		self.list.append(self.set_changeMode)
		self.list.append(self.set_selectMode)
		self.Logos = searchForFiles(strSearchPath, 1)
		if self.Logos:  # BootLogos found
			self.Logos.sort(key=str.lower)
			strEntry = _('---- found %02d BootLogo%s to select ----') % (len(self.Logos), 's' if len(self.Logos) > 1 else '')
			self.list.append(getConfigListEntry(strEntry, self.set_fake_entry, '-'))
			if self.changeMode == 'man':
				iLogoCount = 1
				for x in self.Logos:
					strEntry = '%02d: %s' % (iLogoCount, str(dirname(x.replace(strSearchPath, ''))))
					self.list.append(getConfigListEntry(strEntry, self.set_fake_entry, x))
					iLogoCount += 1
		else:  # no BootLogos found
			self.list.append(getConfigListEntry(_('---- no BootLogos found :\'( ----'), self.set_fake_entry, '-'))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def selectionChanged(self):
		try:
			idx = self["config"].getCurrentIndex()
			cur = self["config"].getCurrent()
			if idx < self.conOff:  # config section, show description
				self['LogosInfo'].setText(str(cur[2]))
			elif idx > self.conOff:  # BootLogo section
				strInfo = str(cur[0])
				if idx - self.idxOff == self.CurLogoIdx:
					self['LogosInfo'].setText(_('... \'%s\' is currently set as BootLogo') % (strInfo))
				else:
					self['LogosInfo'].setText(_('... press \'OK\' to select \'%s\' as new BootLogo') % (strInfo[strInfo.find(': ') + 2:]))
			else:  # info section (self.conOff)
				if self.Logos:  # BootLogos found
					iLogoCount = len(self.Logos)
					self['LogosInfo'].setText(_('... there %s %02d BootLogo%s available') % (_('are') if iLogoCount > 1 else _('is only'), iLogoCount, 's' if iLogoCount > 1 else ''))
				else:
					self['LogosInfo'].setText(_('... unfortunately no BootLogo available, please check:\n\'%s\'') % (strSearchPath))
			self.setPicture(idx, str(cur[2]))
		except:
			self['LogosInfo'].setText('./.')

	def changedEntry(self):
		try:
			idx = self["config"].getCurrentIndex()
			if idx == 0:
				self.changeMode = config.plugins.autoBLchanger.changeMode.value
				self.populateConfigList()
			elif idx == 1:
				self.selectMode = config.plugins.autoBLchanger.selectMode.value
			else:
				pass
		except:
			pass

	def setPicture(self, logoIdx, logoPath):
		if logoIdx > self.conOff and self.SelByUser:
			pix = searchForFiles(dirname(logoPath), 1, ('.jpg', '.jpeg', '.png'))
			if not pix:
				pix = ['/tmp/nothing.found']
			pix.sort(key=str.lower)
			if exists(pix[0]):
				self.PicLoad.setPara([self["LogosPict"].instance.size().width(), self["LogosPict"].instance.size().height(), self.Scale[0], self.Scale[1], 0, 1, '#00000000'])
				self.PicLoad.startDecode(pix[0])
				#self['LogosPict'].show()
				# move pixmap if necessary (to not mask the selection)
				curPos = self["LogosPict"].getPosition()
				if curPos[0] == 325:
					logoModIdx = logoIdx % 16
					logoOffset = ((16 - logoModIdx) * 30) + 10
					y_Pos = 371 if logoModIdx <= 9 else 371 - logoOffset
					if curPos[1] != y_Pos:  # only move if position is different
						self["LogosPict"].setPosition(curPos[0], y_Pos)
			else:
				self['LogosPict'].hide()
		else:
			self['LogosPict'].hide()

	def UpdatePicture(self):
		#self.setTitle('auto BootLogo changer - %s' % (strVersionIdx))  # it is done by parsing the skin
		self.PicLoad.PictureData.get().append(self.DecodePicture)
		#self.yellow()  # show current BootLogo if one

	def DecodePicture(self, PicInfo=""):
		ptr = self.PicLoad.getData()
		if ptr is not None:
			self["LogosPict"].instance.setPixmap(ptr)
			self['LogosPict'].show()
		else:
			self['LogosPict'].hide()

	def run(self):
		try:
			idx = self["config"].getCurrentIndex() - self.idxOff
			if idx >= 0 and not idx == self.CurLogoIdx:
				checkBootLogo()  # check for BootLogo existence, rename or remove it
				symlink(self.Logos[idx], strTargetPath)  # create symLink to BootLogo
				restartbox = self.session.openWithCallback(self.restartSTB, MessageBox, _('Your STB needs a restart to apply the new bootlogo.\nDo you want to Restart you STB now?'), MessageBox.TYPE_YESNO, default=False)
				restartbox.setTitle(_('Restart STB'))
		except:
			self.session.open(MessageBox, _('Error setting BootLogo!'), MessageBox.TYPE_ERROR, timeout=4)

	def yellow(self):
		if self.CurLogoIdx >= 0:
			self.SelByUser = False  # flag to not load the picture by setting new index
			self['key_yellow'].setText(_('show current\nBootLogo'))
			if self.changeMode == 'man':
				self["config"].setCurrentIndex(self.CurLogoIdx + self.idxOff)
			else:
				self["config"].setCurrentIndex(2)
				strInfo = '%02d: %s' % (self.CurLogoIdx + 1, dirname(self.Logos[self.CurLogoIdx].replace(strSearchPath, '')))
				self['LogosInfo'].setText(_('... \'%s\' is currently set as BootLogo') % (strInfo))
			self.SelByUser = True  # flag to load the picture
			self.setPicture(self.CurLogoIdx + self.idxOff, self.Logos[self.CurLogoIdx])
		else:
			self['config'].setCurrentIndex(0)

	def blue(self):
		if self.isOrigLogo:
			try:
				if lexists(strTargetPath):  # check if BootLogo already exists
					remove(strTargetPath)  # must be removed
				rename(strTargetPath + '.org', strTargetPath)  # rename the original BootLogo back
				self.isOrigLogo = False
				self['key_blue'].setText('')
				self['LogosInfo'].setText(_('The original BootLogo was successfully reset...'))
				self.CurLogoIdx = getBootLogoIdx(self.Logos)
				self['key_yellow'].setText('')
			except:
				self.session.open(MessageBox, _('Error setting back original BootLogo!'), MessageBox.TYPE_ERROR, timeout=4)
		else:
			self['config'].setCurrentIndex(0)

	def cancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def save(self):
		for x in self["config"].list:
			x[1].save()
		if self.changeMode == 'aut':
			autoChangeBootLogo()  # set a new BootLogo for next system start
		self.close()

	def restartSTB(self, answer):
		if answer is True:
			system('reboot')
		else:
			self.save()

#### setup the Plugin #########################################################################


def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
			name=strPluginName,
			description=_('change the BootLogo manually or at system startup') + ' (%s)' % (strVersionIdx),
			icon='plugin.png',
			fnc=normalStart
		),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_SESSIONSTART,  # starts AFTER the Enigma2 booting
			fnc=sessionStart
		)
	]


def normalStart(session, **kwargs):
	session.open(autoBLchanger)


def sessionStart(reason, **kwargs):  # starts AFTER the Enigma2 booting
	if "session" in kwargs and reason == 0 and strChangeMode == 'aut':
		autoChangeBootLogo()
	else:
		pass

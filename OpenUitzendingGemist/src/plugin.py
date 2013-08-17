from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigBoolean, ConfigSelection, getConfigListEntry
from enigma import eServiceReference, eTimer, iPlayableService, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_WRAP, RT_VALIGN_TOP, ePicLoad
from ServiceReference import ServiceReference
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from urllib2 import Request, URLError, HTTPError, urlopen as urlopen2
from httplib import HTTPException
from twisted.web import client
from os import path as os_path, remove as os_remove, mkdir as os_mkdir
import socket
from datetime import date, timedelta


config.plugins.OpenUitzendingGemist = ConfigSubsection()
config.plugins.OpenUitzendingGemist.showpictures = ConfigBoolean(default = True)


def wgetUrl(target):
	std_headers = {
		'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'en-us,en;q=0.5',
	}
	outtxt = Request(target, None, std_headers)
	try:
		outtxt = urlopen2(target, timeout = 5).read()
	except (URLError, HTTPException, socket.error):
		return ''
	return outtxt


def MPanelEntryComponent(channel, text, png):
	res = [ text ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 200, 15, 800, 100, 0, RT_HALIGN_LEFT|RT_WRAP|RT_VALIGN_TOP, text))
	res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 5, 150, 150, png))
	return res


class MPanelList(MenuList):
	def __init__(self, list, selection = 0, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(120)
		self.selection = selection

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)


class UGMediaPlayer(Screen, InfoBarNotifications, InfoBarSeek):
	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2

	skin = """<screen name="MediaPlayer" flags="wfNoBorder" position="0,380" size="720,160" title="Media player" backgroundColor="transparent">
		<ePixmap position="0,0" pixmap="skin_default/info-bg_mp.png" zPosition="-1" size="720,160" />
		<ePixmap position="29,40" pixmap="skin_default/screws_mp.png" size="665,104" alphatest="on" />
		<ePixmap position="48,70" pixmap="skin_default/icons/mp_buttons.png" size="108,13" alphatest="on" />
		<ePixmap pixmap="skin_default/icons/icon_event.png" position="207,78" size="15,10" alphatest="on" />
		<widget source="session.CurrentService" render="Label" position="230,73" size="360,40" font="Regular;20" backgroundColor="#263c59" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1">
			<convert type="ServiceName">Name</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="580,73" size="90,24" font="Regular;20" halign="right" backgroundColor="#4e5a74" transparent="1">
			<convert type="ServicePosition">Length</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="205,129" size="100,20" font="Regular;18" halign="center" valign="center" backgroundColor="#06224f" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1">
			<convert type="ServicePosition">Position</convert>
		</widget>
		<widget source="session.CurrentService" render="PositionGauge" position="300,133" size="270,10" zPosition="2" pointer="skin_default/position_pointer.png:540,0" transparent="1" foregroundColor="#20224f">
			<convert type="ServicePosition">Gauge</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="576,129" size="100,20" font="Regular;18" halign="center" valign="center" backgroundColor="#06224f" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1">
			<convert type="ServicePosition">Remaining</convert>
		</widget>
		</screen>"""

	def __init__(self, session, service, mediatype):
		Screen.__init__(self, session)
		self.skinName = "MoviePlayer"
		InfoBarNotifications.__init__(self)
		if mediatype == 'rtl':
			InfoBarSeek.__init__(self)
		self.session = session
		self.service = service
		self.screen_timeout = 3000
		self.mediatype = mediatype
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
				iPlayableService.evEOF: self.__evEOF,
			})
		self["actions"] = ActionMap(["OkCancelActions", "InfobarSeekActions", "MediaPlayerActions", "MovieSelectionActions"],
		{
				"ok": self.ok,
				"cancel": self.leavePlayer,
				"stop": self.leavePlayer,
				"showEventInfo": self.showVideoInfo,
			}, -2)
		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.ok)
		self.returning = False
		self.state = self.STATE_PLAYING
		self.lastseekstate = self.STATE_PLAYING
		self.onPlayStateChanged = [ ]
		self.play()
		self.onClose.append(self.__onClose)

	def __seekableStatusChanged(self):
		if self.mediatype != 'rtl':
			return
		if not self.isSeekable():
			self["SeekActions"].setEnabled(False)
			self.setSeekState(self.STATE_PLAYING)
		else:
			self["SeekActions"].setEnabled(True)

	def __onClose(self):
		self.session.nav.stopService()

	def __evEOF(self):
		self.handleLeave()

	def __setHideTimer(self):
		self.hidetimer.start(self.screen_timeout)

	def showInfobar(self):
		self.show()
		if self.state == self.STATE_PLAYING:
			self.__setHideTimer()
		else:
			pass

	def hideInfobar(self):
		self.hide()
		self.hidetimer.stop()

	def ok(self):
		if self.shown:
			self.hideInfobar()
		else:
			self.showInfobar()

	def showVideoInfo(self):
		if self.shown:
			self.hideInfobar()

	def playService(self, newservice):
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.service = newservice
		self.play()

	def play(self):
		if self.state == self.STATE_PAUSED:
			if self.shown:
				self.__setHideTimer()
		self.state = self.STATE_PLAYING
		self.session.nav.playService(self.service)
		if self.shown:
			self.__setHideTimer()

	def stopCurrent(self):
		self.session.nav.stopService()
		self.state = self.STATE_IDLE

	def __serviceStarted(self):
		self.state = self.STATE_PLAYING
		self.__seekableStatusChanged()

	def handleLeave(self):
		self.close()

	def leavePlayer(self):
		self.handleLeave()

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		self.handleLeave()

	def lockShow(self):
		return

	def unlockShow(self):
		return

class OpenUgConfigureScreen(Screen, ConfigListScreen):
	def __init__(self, session):
		self.skin = """
				<screen position="center,center" size="400,100" title="">
					<widget name="config" position="10,10"   size="e-20,e-10" scrollbarMode="showOnDemand" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self["config"].list = self.list
		self.list.append(getConfigListEntry(_("Show pictures"), config.plugins.OpenUitzendingGemist.showpictures))
		self["config"].l.setList(self.list)
		
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Open Uitzending Gemist options"))

	def keyGo(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

class OpenUgSetupScreen(Screen):
	def __init__(self, session):
		self.skin = """
				<screen position="center,center" size="400,400" title="">
					<widget name="menu" position="10,10"   size="e-20,200" scrollbarMode="showOnDemand" />
					<widget name="info" position="10,e-125" size="e-20,150" halign="center" font="Regular;22" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self.lastservice = session.nav.getCurrentlyPlayingServiceReference()

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.imagedir = '/tmp/openUgImg/'

		self["info"] = Label(_("Open Uitzending Gemist\n\nBased on Xtrend code"))

		self.mmenu= []
		self.mmenu.append((_("UG Recently added"), 'recent'))
		self.mmenu.append((_("UG Popular"), 'pop'))
		self.mmenu.append((_("UG A-Z"), 'atotz'))
		self.mmenu.append((_("UG Search"), 'search'))
		self.mmenu.append((_("RTL XL A-Z"), 'rtl'))
		self.mmenu.append((_("RTL XL Gemist"), 'rtlback'))
		self.mmenu.append((_("RTL XL Search"), 'rsearch'))
		self.mmenu.append((_("Setup"), 'setup'))
		self["menu"] = MenuList(self.mmenu)

		self.onLayoutFinish.append(self.layoutFinished)

	def loadUrl(self, url, sub):
		try:
			lines = open(url).readlines()
			for x in lines:
				if sub in x.lower():
					return True
		except:
			return False
		return False

	def layoutFinished(self):
		self.setTitle('Open Uitzending Gemist')

	def keyGo(self):
		selection = self["menu"].l.getCurrentSelection()
		if selection is not None:
			if selection[1] == 'recent':
				self.session.open(OpenUg, selection[1])
			elif selection[1] == 'pop':
				self.session.open(OpenUg, selection[1])
			elif selection[1] == 'atotz':
				self.session.open(OpenUg, selection[1])
			elif selection[1] == 'search':
				self.isRtl = False
				self.session.open(OpenUg, selection[1])
			elif selection[1] == 'rtl':
				self.session.open(OpenUg, selection[1])
			elif selection[1] == 'rtlback':
				self.session.open(DaysBackScreen)
			elif selection[1] == 'rsearch':
				self.isRtl = True
				self.session.open(OpenUg, selection[1])
			elif selection[1] == 'setup':
				self.session.open(OpenUgConfigureScreen)

	def keyCancel(self):
		self.removeFiles(self.imagedir)
		if self.lastservice is not None:
			self.session.nav.playService(self.lastservice)
		self.close()

	def removeFiles(self, targetdir):
		import os
		for root, dirs, files in os.walk(targetdir):
			for name in files:
				os.remove(os.path.join(root, name))


class DaysBackScreen(Screen):
	def __init__(self, session):
		self.skin = """
				<screen position="center,center" size="400,400" title="">
					<widget name="menu" position="10,10"   size="e-20,e-10" scrollbarMode="showOnDemand" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.mmenu= []
		count = 0
		now = date.today()
		while count < 15:
			if count == 0:
				self.mmenu.append((_("Today"), count))
			else:
				self.mmenu.append(((now.strftime("%A")), count))
			now = now - timedelta(1)
			count += 1
		self["menu"] = MenuList(self.mmenu)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("RTL Number of days back"))

	def keyGo(self):
		selection = self["menu"].l.getCurrentSelection()
		self.session.open(OpenUg, selection[1])
		self.close()

	def keyCancel(self):
		self.close()

class OpenUg(Screen):

	UG_PROGDATE = 0
	UG_PROGNAME = 1
	UG_SHORT_DESCR = 2
	UG_CHANNELNAME = 3
	UG_STREAMURL = 4
	UG_ICON = 5
	UG_ICONTYPE = 6
	UG_SERIE = 7
	UG_LEVEL_ALL = 0
	UG_LEVEL_SERIE = 1
	MAX_PIC_PAGE = 5

	TIMER_CMD_START = 0
	TIMER_CMD_VKEY = 1
	UG_BASE_URL = "http://hbbtv.distributie.publiekeomroep.nl"
	HBBTV_UG_BASE_URL = UG_BASE_URL + "/nu/ajax/action/"
	RTL_BASE_URL = "http://rtl.ksya.net/"

	def __init__(self, session, cmd):
		self.skin = """
				<screen position="80,70" size="e-160,e-110" title="">
					<widget name="list" position="0,0" size="e-0,e-0" scrollbarMode="showOnDemand" transparent="1" zPosition="2"/>
					<widget name="thumbnail" position="0,0" size="150,150" alphatest="on" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)

		self["thumbnail"] = Pixmap()
		self["thumbnail"].hide()

		self.cbTimer = eTimer()
		self.cbTimer.callback.append(self.timerCallback)

		self.Details = {}
		self.pixmaps_to_load = []
		self.picloads = {}
		self.color = "#33000000"

		self.page = 0
		self.numOfPics = 0
		self.isAtotZ = False
		self.isRtl = False
		self.isRtlBack = False
		self.level = self.UG_LEVEL_ALL
		self.cmd = cmd
		self.timerCmd = self.TIMER_CMD_START

		self.png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/OpenUitzendingGemist/oe-alliance.png"))
		
		self.tmplist = []
		self.mediaList = []

		self.imagedir = "/tmp/openUgImg/"
		if (os_path.exists(self.imagedir) != True):
			os_mkdir(self.imagedir)

		self["list"] = MPanelList(list = self.tmplist, selection = 0)
		self.updateMenu()
		self["actions"] = ActionMap(["WizardActions", "MovieSelectionActions", "DirectionActions"],
		{
			"up": self.key_up,
			"down": self.key_down,
			"left": self.key_left,
			"right": self.key_right,
			"ok": self.go,
			"back": self.Exit,
		}
		, -1)
		self.onLayoutFinish.append(self.layoutFinished)
		self.cbTimer.start(10)

	def layoutFinished(self):
		self.setTitle("Open Uitzending Gemist")

	def updatePage(self):
		if self.page != self["list"].getSelectedIndex() / self.MAX_PIC_PAGE:
			self.page = self["list"].getSelectedIndex() / self.MAX_PIC_PAGE
			self.loadPicPage()

	def key_up(self):
		self["list"].up()
		self.updatePage()

	def key_down(self):
		self["list"].down()
		self.updatePage()

	def key_left(self):
		self["list"].pageUp()
		self.updatePage()

	def key_right(self):
		self["list"].pageDown()
		self.updatePage()

	def getThumbnailName(self, x):
		if self.isRtl:
			if x[self.UG_ICON]:
				return str(x[self.UG_ICON]).split("/uuid=")[1].split("/")[0] + ".jpg"
			else:
				return ""
		return str(x[self.UG_STREAMURL]) + str(x[self.UG_ICONTYPE])

	def updateMenu(self):
		self.tmplist = []
		if len(self.mediaList) > 0:
			pos = 0
			for x in self.mediaList:
				self.tmplist.append(MPanelEntryComponent(channel = x[self.UG_CHANNELNAME], text = (x[self.UG_PROGNAME] + '\n' + x[self.UG_PROGDATE] + '\n' + x[self.UG_SHORT_DESCR]), png = self.png))
				tmp_icon = self.getThumbnailName(x)
				thumbnailFile = self.imagedir + tmp_icon
				self.pixmaps_to_load.append(tmp_icon)

				if not self.Details.has_key(tmp_icon):
					self.Details[tmp_icon] = { 'thumbnail': None}

				if x[self.UG_ICON] != '':
					if (os_path.exists(thumbnailFile) == True):
						self.fetchFinished(True, picture_id = tmp_icon, failed = False)
					else:
						if config.plugins.OpenUitzendingGemist.showpictures.value:
							client.downloadPage(x[self.UG_ICON], thumbnailFile).addCallback(self.fetchFinished, tmp_icon).addErrback(self.fetchFailed, tmp_icon)
				pos += 1
			self["list"].setList(self.tmplist)

	def Exit(self):
		doExit = False
		if self.level == self.UG_LEVEL_ALL:
			doExit = True
		else:
			if self.isRtl:
				if self.isRtlBack:
					doExit = True
				else:
					self.setupCallback("rtl")
			else:
				if self.isAtotZ:
					self.setupCallback("atotz")
				else:
					doExit = True
		if doExit:
			self.close()

	def clearList(self):
		elist = []
		self["list"].setList(elist)
		self.mediaList = []
		self.pixmaps_to_load = []
		self.page = 0

	def setupCallback(self, retval = None):
		if retval == 'cancel' or retval is None:
			return

		if retval == 'recent':
			self.clearList()
			self.level = self.UG_LEVEL_SERIE
			self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "archive_week/protocol/html")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif retval == 'pop':
			self.clearList()
			self.level = self.UG_LEVEL_SERIE
			self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "popular/protocol/html")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif retval == 'atotz':
			self.clearList()
			self.isAtotZ = True
			self.level = self.UG_LEVEL_ALL
			self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z/a2zActiveIndex/0/protocol/html")
			self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z/a2zActiveIndex/1/protocol/html")
			self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z/a2zActiveIndex/2/protocol/html")
			self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z/a2zActiveIndex/3/protocol/html")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			self.updateMenu()
		elif retval == 'search':
			self.isRtl = False
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)
		elif retval == 'rsearch':
			self.isRtl = True
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)
		elif retval == 'rtl':
			self.clearList()
			self.isRtl = True
			self.level = self.UG_LEVEL_ALL
			self.getRTLMediaData(self.mediaList, self.RTL_BASE_URL + "programmalijst.php")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			else:
				self.updateMenu()
		else:
			self.clearList()
			self.isRtl = True
			self.isRtlBack = True
			self.level = self.UG_LEVEL_SERIE
			self.getRTLMediaDataBack(self.mediaList, retval)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup()
			else:
				self.updateMenu()

	def timerCallback(self):
		self.cbTimer.stop()
		if self.timerCmd == self.TIMER_CMD_START:
			self.setupCallback(self.cmd)
		elif self.timerCmd == self.TIMER_CMD_VKEY:
			self.session.openWithCallback(self.keyboardCallback, VirtualKeyBoard, title = (_("Search term")), text = "")

	def keyboardCallback(self, callback = None):
		if callback is not None and len(callback):
			self.clearList()
			self.level = self.UG_LEVEL_SERIE
			print "[UG] testing!"
			if self.isRtl == False:
				print "[UG] isRtl = False!"
				self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "search/protocol/html/searchString/" + callback)
				self.updateMenu()
			elif self.isRtl == True:
				print "[UG] isRtl = True!"
				self.getRTLSerie(self.mediaList, "search.php?q=*" + callback + "*")
				self.updateMenu()
			print "[UG] testing2!"
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple = True)
		else:
			self.close()

	def mediaProblemPopup(self):
		self.session.openWithCallback(self.close, MessageBox, _("There was a problem retrieving the media list"), MessageBox.TYPE_ERROR, timeout=5, simple = True)

	def fetchFailed(self, string, picture_id):
		self.fetchFinished(False, picture_id, failed = True)

	def fetchFinished(self, x, picture_id, failed = False):
		if failed:
			return
		else:
			thumbnailFile = self.imagedir + str(picture_id)
		sc = AVSwitch().getFramebufferScale()
		if (os_path.exists(thumbnailFile) == True):
			start = self.page * self.MAX_PIC_PAGE
			end  = (self.page * self.MAX_PIC_PAGE) + self.MAX_PIC_PAGE
			count = 0
			for x in self.mediaList:
				if count >= start and count < end:
					if self.getThumbnailName(x) == picture_id:
						self.picloads[picture_id] = ePicLoad()
						self.picloads[picture_id].PictureData.get().append(boundFunction(self.finish_decode, picture_id))
						self.picloads[picture_id].setPara((150, 150, sc[0], sc[1], False, 1, "#00000000"))
						self.picloads[picture_id].startDecode(thumbnailFile)
				count += 1
				if count > end:
					break
		else:
			self.pixmaps_to_load.append(picture_id)
			self.fetchFinished(False, picture_id, failed = True)

	def loadPicPage(self):
		self.Details = {}
		self.updateMenu()

	def finish_decode(self, picture_id, info):
		ptr = self.picloads[picture_id].getData()
		thumbnailFile = self.imagedir + str(picture_id)
		if ptr != None:
			if self.Details.has_key(picture_id):
				self.Details[picture_id]["thumbnail"] = ptr

		self.tmplist = []
		pos = 0
		for x in self.mediaList:
			if self.Details[self.getThumbnailName(x)]["thumbnail"] is not None:
				self.tmplist.append(MPanelEntryComponent(channel = x[self.UG_CHANNELNAME], text = (x[self.UG_PROGNAME] + '\n' + x[self.UG_PROGDATE] + '\n' + x[self.UG_SHORT_DESCR]), png = self.Details[self.getThumbnailName(x)]["thumbnail"]))
			else:
				self.tmplist.append(MPanelEntryComponent(channel = x[self.UG_CHANNELNAME], text = (x[self.UG_PROGNAME] + '\n' + x[self.UG_PROGDATE] + '\n' + x[self.UG_SHORT_DESCR]), png = self.png))

			pos += 1
		self["list"].setList(self.tmplist)

	def go(self):
		if len(self.mediaList) == 0 or self["list"].getSelectionIndex() > len(self.mediaList) - 1:
			return

		if self.isRtl:
			if self.level == self.UG_LEVEL_ALL:
				tmp = self.mediaList[self["list"].getSelectionIndex()][self.UG_STREAMURL]
				self.clearList()
				self.getRTLSerie(self.mediaList, tmp)
				self.level = self.UG_LEVEL_SERIE
				self.updateMenu()
				self.loadPicPage()
			elif self.level == self.UG_LEVEL_SERIE:
				tmp = self.getRTLStream(self.mediaList[self["list"].getSelectionIndex()][self.UG_STREAMURL])
				if tmp != '':
					myreference = eServiceReference(4097, 0, tmp)
					myreference.setName(self.mediaList[self["list"].getSelectionIndex()][self.UG_PROGNAME])
					self.session.open(UGMediaPlayer, myreference, 'rtl')

		else:
			if self.level == self.UG_LEVEL_ALL:
				if self.mediaList[self["list"].getSelectionIndex()][self.UG_SERIE]:
					tmp = self.mediaList[self["list"].getSelectionIndex()][self.UG_STREAMURL]
					self.clearList()
					self.isRtl = False
					self.level = self.UG_LEVEL_SERIE
					self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z-serie/a2zSerieId/" + tmp)
					self.updateMenu()
				else:
					self.doUGPlay()
			else:
				self.doUGPlay()

	def doUGPlay(self):
		url = self.UG_BASE_URL + "/streams/video/pr_id/" + self.mediaList[self["list"].getSelectionIndex()][self.UG_STREAMURL]
		print "[UG] %s" % url 
		out = wgetUrl(url)
		print "[UG] %s" % out
		if out !='':
			url = out.split('stream_link":"')[1].split('\",')[0].replace('\/', '/')
			if url != '':
				myreference = eServiceReference(4097, 0, url)
				myreference.setName(self.mediaList[self["list"].getSelectionIndex()][self.UG_PROGNAME])
				self.session.open(UGMediaPlayer, myreference, 'npo')

	def getRTLStream(self, url):
		data = wgetUrl(self.RTL_BASE_URL + url)
		data = data.split('\n')
		state = 0
		url = ''
		name = ''
		icon = ''
		for line in data:
			if ".mp4" in line:
				tmp = 'href=\"'
				if tmp in line:
					url = line.split(tmp)[1].split('\">')[0]
				return url
		return ''

	def getRTLSerie(self, weekList, url):
		data = wgetUrl(self.RTL_BASE_URL + url)
		data = data.split('\n')
		state = 0
		name = ''
		short = ''
		icon = ''
		stream = ''
		date = ''
		channel = ''
		for line in data:
			if "<li>" in line:
				state = 1
			if state == 1:
				tmp = "<a href=\"video"
				if tmp in line:
					tmp = "<a href=\""
					stream = line.split(tmp)[1].split('\">')[0]

				tmp = "<img class=\"thumbnail\" src=\""
				if tmp in line:
					icon = line.split(tmp)[1].split('\" ')[0]

				tmp = "<span class=\"title\">"
				if tmp in line:
					name = line.split(tmp)[1].split('</span>')[0]
					state = 2

			elif state == 2:
				if '<span class=\"extra_info\">' in line:
					continue
				short = line.split("<br />")[0].lstrip()
				state = 3

			elif state == 3:
				tmp = '<span class=\"extra_info\">'
				if tmp in line:
					continue
				tmp = "<span class=\"small\">"
				if tmp in line:
					date = short
					short = line.split(tmp)[1].split('</span>')[0]
				else:
					date = ' '.join(line.split())
				icon_type = self.getIconType(icon)
				weekList.append((date, name, short, channel, stream, icon, icon_type, False))
				state = 0

	def getRTLMediaData(self, weekList, url):
		data = wgetUrl(url)
		data = data.split('\n')
		state = 0
		name = ''
		short = ''
		icon = ''
		stream = ''
		date = ''
		channel = ''
		for line in data:
			if state == 0:
				if "</li>" in line:
					state = 1
			if state == 1:
				tmp = "<a href=\""
				if tmp in line:
					stream = line.split(tmp)[1].split('\">')[0]

				tmp = "<span class=\"title\">"
				if tmp in line:
					name = line.split(tmp)[1].split("</span>")[0]
					icon_type = self.getIconType(icon)
					ignore = False
					for x in weekList:
						if stream == x[self.UG_STREAMURL] and icon == x[self.UG_ICON]:
							ignore = True
							break
					if ignore is False:
						weekList.append((date, name, short, channel, stream, icon, icon_type, True))
					state = 0
					
	def getRTLMediaDataBack(self, weekList, days):
		url = self.RTL_BASE_URL + "?daysback=" + '%d' % (days)
		data = wgetUrl(url)
		data = data.split('\n')
		state = 0
		name = ''
		short = ''
		icon = ''
		stream = ''
		date = ''
		channel = ''
		for line in data:
			if "</li>" in line:
				state = 1
			if state == 1:
				if "<a href=\"video" in line:
					stream = line.split("<a href=\"")[1].split('\" ')[0]
					continue
				tmp = "<img class=\"thumbnail\" src=\""
				if tmp in line:
					icon = line.split(tmp)[1].split('\" ')[0]
					continue
				tmp = "<span class=\"title\">"
				if tmp in line:
					name = line.split(tmp)[1].split("</span>")[0]
					name.replace("&amp;", "&")
					state = 2
					continue;

			elif state == 2:
				if "<br />" in line:
					short = line.split("<br />")[0]
					state = 3
					continue;

			elif state == 3:
				tmp = line.split("<br")[0].split(" | ")
				channel = tmp[0]
				state = 4
				continue;

			elif state == 4:
				date = line.split("</span>")[0]
				icon_type = self.getIconType(icon)
				weekList.append((date, name, short, channel, stream, icon, icon_type, False))
				state = 0

	def getMediaData(self, weekList, url):
		data = wgetUrl(url)
		state = 0
		short = ''
		name = ''
		date = ''
		stream = ''
		channel = ''
		icon = ''
		data = data.split("\n")
		for line in data:
			if state == 0:
				tmp = "<div class=\"vid\""
				if tmp in line:
					state = 1
					short = ''
					name = ''
					date = ''
					stream = ''
					icon = ''
					continue

			elif state == 1:
				if (not icon or not stream):
					tmp = "<img class=\"vid_view\" src=\""
					if tmp in line:
						icon = line.split(tmp)[1].split("\" />")[0]
						tmp = "<img class=\"vid_view\" src=\"http://hbbtv.distributie.publiekeomroep.nl/imagecache/epg/pr_id/"
						stream = line.split(tmp)[1].split('/')[0]
						continue

				if (not short):
					tmp = "<p class=\"titleshort\">"
					if tmp in line:
						short = line.split(tmp)[1].split("</p>")[0]
						continue

				if (not name):
					tmp = "<p class=\"title\">"
					if tmp in line:
						name = line.split(tmp)[1].split("</p>")[0]
						continue

				if (not date):
					tmp = "<p class=\"date_time bottom\">"
					if tmp in line:
						date = line.split(tmp)[1].split("</p>")[0]

				if stream and date and name and short and icon:
					icon_type = self.getIconType(icon)
					print "[UG] name: %s" % name
					print "[UG] short: %s" % short
					print "[UG] channel: %s" % channel
					print "[UG] stream: %s" % stream
					print "[UG] date: %s" % date
					weekList.append((date, name, short, channel, stream, icon, icon_type, False))
					state = 0

	def getIconType(self, data):
		tmp = ".png"
		if tmp in data:
			return tmp
		tmp = ".gif"
		if tmp in data:
			return tmp
		tmp = ".jpg"
		if tmp in data:
			return tmp
		return ""

def main(session, **kwargs):
	session.open(OpenUgSetupScreen)

def Plugins(**kwargs):

	return [PluginDescriptor(name = "Open uitzending gemist", description = _("Watch uitzending gemist"), where = PluginDescriptor.WHERE_PLUGINMENU, icon="oe-alliance.png", fnc = main),
			PluginDescriptor(name = "Open uitzending gemist", description = _("Watch uitzending gemist"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = main)]

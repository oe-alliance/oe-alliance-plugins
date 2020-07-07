from __future__ import absolute_import
from __future__ import print_function
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarNotifications
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.EpgList import EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from enigma import eTimer, ePicLoad, iPlayableService

from .SCConfig import StalkerClient_SetupScreen
from .SCEPG import StalkerClient_EPGSelection, StalkerClient_EventViewEPGSelect, StalkerEvent
from .SCInfo import scthreads
from .stalkerclient import stalker

from time import localtime, strftime, time

PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/StalkerClient")


class StalkerClient_Player(Screen, InfoBarNotifications):
	skin_default_1080p = """
	<screen name="stalkerclientplayer" flags="wfNoBorder" position="0,830" size="1920,250" title="StalkerClient Player" backgroundColor="#41000000" >
		<ePixmap position="270,40" size="117,72" pixmap="%s/channel_background.png" zPosition="-1" transparent="1" alphatest="blend" />
		<widget name="channel_icon" position="311,58" zPosition="10" size="35,35" backgroundColor="#41000000" />
		<widget name="channel_name" position="440,30" size="1010,60" font="Regular;48" halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#41000000" />
		<widget name="channel_uri" position="440,100" size="1010,40" font="Regular;30" halign="left" valign="top" foregroundColor="#f4df8d" backgroundColor="#41000000" />
		<widget name="eventNow_time" position="270,150" size="125,45" font="Regular;30" halign="center" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNow_name" position="440,150" size="830,45" font="Regular;32" halign="left" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" noWrap="1" />
		<widget name="eventNow_remaining" position="1280,150" size="150,45" font="Regular;30" halign="right" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNext_time" position="270,195" size="125,45" font="Regular;30" halign="center" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNext_name" position="440,195" size="830,45" font="Regular;32" halign="left" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" noWrap="1" />
		<widget name="eventNext_duration" position="1280,195" size="150,45" font="Regular;30" halign="right" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventProgressbar" position="1450,160" size="200,25" borderColor="#9c9c9c" backgroundColor="#41000000" borderWidth="1" />
		<ePixmap pixmap="%s/clock.png" position="1470,45" size="31,31" alphatest="on" />
		<widget source="global.CurrentTime" render="Label" position="1505,30" size="75,60" font="Regular;30" halign="right" valign="center" backgroundColor="#41000000" foregroundColor="#ffffff" transparent="1">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="1460,100" size="120,40" font="Regular;30" halign="right" valign="top" foregroundColor="#f4df8d" backgroundColor="#41000000" transparent="0">
			<convert type="ServicePosition">Position</convert>
		</widget>
	</screen>
	""" % (PLUGIN_PATH, PLUGIN_PATH)

	skin_default_720p = """
	<screen name="stalkerclientplayer" flags="wfNoBorder" position="0,560" size="1280,160" title="StalkerClient Player" backgroundColor="#41000000" >
		<ePixmap position="80,25" size="117,72" pixmap="%s/channel_background.png" zPosition="-1" transparent="1" alphatest="blend" />
		<widget name="channel_icon" position="121,43" zPosition="10" size="35,35" backgroundColor="#41000000" />
		<widget name="channel_name" position="250,20" size="780,40" font="Regular;36" halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#41000000" />
		<widget name="channel_uri" position="250,65" size="780,30" font="Regular;22" halign="left" valign="top" foregroundColor="#f4df8d" backgroundColor="#41000000" />
		<widget name="eventNow_time" position="250,95" size="60,30" font="Regular;22" halign="left" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNow_name" position="320,95" size="600,30" font="Regular;22" halign="left" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" noWrap="1" />
		<widget name="eventNow_remaining" position="930,95" size="100,30" font="Regular;22" halign="right" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNext_time" position="250,125" size="60,30" font="Regular;22" halign="left" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNext_name" position="320,125" size="600,30" font="Regular;22" halign="left" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" noWrap="1" />
		<widget name="eventNext_duration" position="930,125" size="100,30" font="Regular;22" halign="right" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventProgressbar" position="1055,98" size="145,25" borderColor="#9c9c9c" backgroundColor="#41000000" borderWidth="1" />
		<ePixmap pixmap="%s/clock.png" position="1055,25" size="31,31" alphatest="on" />
		<widget source="global.CurrentTime" render="Label" position="1090,20" size="60,40" font="Regular;22" halign="right" valign="center" backgroundColor="#41000000" foregroundColor="#ffffff" transparent="1">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="1040,65" size="110,30" font="Regular;22" halign="right" valign="top" foregroundColor="#f4df8d" backgroundColor="#41000000" transparent="1">
			<convert type="ServicePosition">Position</convert>
		</widget>
	</screen>
	""" % (PLUGIN_PATH, PLUGIN_PATH)

	skin_default_576p = """
	<screen name="stalkerclientplayer" flags="wfNoBorder" position="0,430" size="720,150" title="StalkerClient Player" backgroundColor="#41000000" >
		<ePixmap position="20,25" size="0,72" pixmap="%s/channel_background.png" zPosition="-1" transparent="1" alphatest="blend" />
		<widget name="channel_icon" position="61,43" zPosition="10" size="0,35" backgroundColor="#41000000" />
		<widget name="channel_name" position="20,20" size="580,40" font="Regular;36" halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#41000000" />
		<widget name="channel_uri" position="20,70" size="560,0" font="Regular;22" halign="left" valign="top" foregroundColor="#f4df8d" backgroundColor="#41000000" />
		<widget name="eventNow_time" position="510,70" size="70,30" font="Regular;22" halign="center" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNow_name" position="20,70" size="500,30" font="Regular;22" halign="left" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" noWrap="1" />
		<widget name="eventNow_remaining" position="510,70" size="70,0" font="Regular;22" halign="right" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNext_time" position="510,105" size="70,30" font="Regular;22" halign="center" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventNext_name" position="20,105" size="500,30" font="Regular;22" halign="left" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" noWrap="1" />
		<widget name="eventNext_duration" position="510,105" size="70,0" font="Regular;22" halign="right" valign="center" foregroundColor="#9c9c9c" backgroundColor="#41000000" />
		<widget name="eventProgressbar" position="590,75" size="110,20" borderColor="#9c9c9c" backgroundColor="#41000000" borderWidth="1" />
		<ePixmap pixmap="%s/clock.png" position="590,25" size="31,0" alphatest="on" />
		<widget source="global.CurrentTime" render="Label" position="590,20" size="110,40" font="Regular;22" halign="right" valign="center" backgroundColor="#41000000" foregroundColor="#ffffff" transparent="1">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="590,105" size="110,30" font="Regular;22" halign="right" valign="center" foregroundColor="#f4df8d" backgroundColor="#41000000" transparent="1">
			<convert type="ServicePosition">Position</convert>
		</widget>
	</screen>
	""" % (PLUGIN_PATH, PLUGIN_PATH)

	PLAYER_IDLE	= 0
	PLAYER_PLAYING 	= 1
	PLAYER_PAUSED 	= 2
	def __init__(self, session, service_ref, service, cbListCommand=None, cbServiceCommand=None):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		self.session = session

		dh = self.session.desktop.size().height()
		self.skin = {1080:StalkerClient_Player.skin_default_1080p, \
						720:StalkerClient_Player.skin_default_720p, \
						576:StalkerClient_Player.skin_default_576p}.get(dh, StalkerClient_Player.skin_default_1080p)

		self.service_ref = service_ref
		self.service = service
		self.cbListCommand = cbListCommand
		self.cbServiceCommand = cbServiceCommand
		self["actions"] = ActionMap(["OkCancelActions", "InfobarChannelSelection", "InfobarEPGActions", "InfobarMenuActions", "InfobarSeekActions"], {
			"ok": self.doInfoAction,
			"cancel": self.doExit,
			"switchChannelUp": self.onKeyUp,
			"switchChannelDown": self.onKeyDown,
			"openServiceList": self.openServiceList,
			"zapUp": self.onKeyLeft,
			"zapDown": self.onKeyRight,
			"showEventInfo": self.onKeyEPG,
			"mainMenu": self.onKeyMenu,
			"stop": self.doExit,
			"playpauseService": self.playpauseService,
		}, -2)

		self.__event_tracker = ServiceEventTracker(screen = self, eventmap = {
			iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
			iPlayableService.evStart: self.__serviceStarted,
			iPlayableService.evEOF: self.__evEOF,
		})

		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.doInfoAction)

		self.state = self.PLAYER_PLAYING
		self.lastseekstate = self.PLAYER_PLAYING
		self.__seekableStatusChanged()

		current_ref = self.session.nav.getCurrentlyPlayingServiceReference()
		if self.session.nav.getCurrentlyPlayingServiceReference() != self.service_ref:
			self.doPlay()
		else:
			if self.shown:
				self.__setHideTimer()

		self['channel_icon'] = Pixmap()
		self['channel_name'] = Label("")
		self['channel_uri']  = Label("")

		self['eventNow_time']  = Label("")
		self['eventNow_name']  = Label("")
		self['eventNow_remaining']  = Label("")
		self['eventNext_time']  = Label("")
		self['eventNext_name']  = Label("")
		self['eventNext_duration']  = Label("")
		self['eventProgressbar'] = ProgressBar()
		self['eventProgressbar'].hide()

		self.picload = ePicLoad()
		self.scale   = AVSwitch().getFramebufferScale()
		self.picload.PictureData.get().append(self.cbDrawChannelIcon)

		self.event_timer = eTimer()
		self.event_timer.callback.append(self.checkServiceEvents)

		self.event_now_next = []
		self.event_view_cur = 0
		self.setServiceInfo(self.service)

		chIcon = '%s/%s'%(PLUGIN_PATH, 'default.png')
		self.picload.setPara((35, 35, self.scale[0], self.scale[1], False, 0, "#00000000"))
		self.picload.startDecode(chIcon)

	def setServiceInfo(self, info):
		self.service = info
		if self.service:
			self['channel_name'].setText(self.service.name)
			self['channel_uri'].setText(self.service.getUrl(False))
			self.checkServiceEvents()

	def resetServiceEvents(self):
		self.event_now_next[:] = []
		self.event_view_cur = 0

	def checkServiceEvents(self):
		if len(self.event_now_next) > 0 and isinstance(self.event_now_next[0], StalkerEvent):
			eventNow = self.event_now_next[0]
			if float(eventNow.time_to) < time():
				self.updateServiceEvents()
			else:
				self.setServiceEvents()
		else:
			self.updateServiceEvents()

		checkNext = int(61 - time() % 60)
		self.event_timer.start(checkNext * 1000)

	def updateServiceEvents(self):
		t = scthreads.getRunningThread()
		if t:
			t.addTask(self.getServiceEvents, stalker.getSimpleDataTable, self.service.getId(), str(strftime('%Y-%m-%d', localtime(time()))), "0")

	def getServiceEvents(self, result):
		self.resetServiceEvents()
		if result:
			selected_item = int(result.get('selected_item'))
			max_page_items = int(result.get('max_page_items'))
			total_items = int(result.get('total_items'))
			cur_page = int(result.get('cur_page'))

			cur_item = max_page_items * (cur_page - 1) + selected_item

			data = result.get('data')
			if isinstance(data, list) and selected_item > 0:
				eventNow = StalkerEvent(data[selected_item - 1])
				if float(eventNow.time_to) > time():
					self.event_now_next.append(eventNow)

				if len(self.event_now_next) > 0:
					if cur_item == total_items:
						t = scthreads.getRunningThread()
						if t:
							t.addTask(self.getEventNext, stalker.getSimpleDataTable, self.service.getId(), str(strftime('%Y-%m-%d', localtime(time() + 60*60*24))), "0")
					elif selected_item == max_page_items:
						t = scthreads.getRunningThread()
						if t:
							t.addTask(self.getEventNext, stalker.getSimpleDataTable, self.service.getId(), str(strftime('%Y-%m-%d', localtime(time()))), str(cur_page + 1))
					elif selected_item < max_page_items:
						eventNext = StalkerEvent(data[selected_item])
						if float(eventNext.time) > time():
							self.event_now_next.append(eventNext)
		self.setServiceEvents()

	def getEventNext(self, result):
		if result:
			data = result.get('data')
			if len(data) > 0:
				eventNext = StalkerEvent(data[0])
				if float(eventNext.time) > time():
					self.event_now_next.append(eventNext)
				self.setServiceEvents()

	def setServiceEvents(self):
		if len(self.event_now_next) > 0 and isinstance(self.event_now_next[0], StalkerEvent):
			eventNow = self.event_now_next[0]
			self['eventNow_time'].setText(strftime("%H:%M", localtime(float(eventNow.time))))
			self['eventNow_name'].setText(eventNow.name)

			remaining = int((float(eventNow.time_to) - time()) / 60)
			self['eventNow_remaining'].setText("+" + str(remaining) + " min")

			percent = (time() - float(eventNow.time)) * 100 / (float(eventNow.time_to) - float(eventNow.time))
			self['eventProgressbar'].setValue(int(percent))
			self['eventProgressbar'].show()
		else:
			self['eventNow_time'].setText("")
			self['eventNow_name'].setText(_("No channel info"))
			self['eventNow_remaining'].setText("")
			self['eventProgressbar'].hide()

		if len(self.event_now_next) > 1 and isinstance(self.event_now_next[1], StalkerEvent):
			eventNext = self.event_now_next[1]
			self['eventNext_time'].setText(strftime("%H:%M", localtime(float(eventNext.time))))
			self['eventNext_name'].setText(eventNext.name)

			duration = int((float(eventNext.time_to) - float(eventNext.time)) / 60)
			self['eventNext_duration'].setText(str(duration) + " min")
		else:
			self['eventNext_time'].setText("")
			if self['eventProgressbar'].getVisible():
				self['eventNext_name'].setText(_("No channel info"))
			else:
				self['eventNext_name'].setText("")
			self['eventNext_duration'].setText("")

	def cbDrawChannelIcon(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			self["channel_icon"].instance.setPixmap(ptr.__deref__())
			self["channel_icon"].show()

	def __seekableStatusChanged(self):
		service = self.session.nav.getCurrentService()
		if service is not None:
			seek = service.seek()
			if seek is None or not seek.isCurrentlySeekable():
				self.setSeekState(self.PLAYER_PLAYING)

	def __serviceStarted(self):
		self.state = self.PLAYER_PLAYING
		self.__seekableStatusChanged()

	def __evEOF(self):
		self.doExit()

	def __setHideTimer(self):
		self.hidetimer.start(5000)

	def doExit(self):
		list = ((_("Yes"), "y"), (_("No"), "n"),)
		self.session.openWithCallback(self.cbDoExit, ChoiceBox, title=_("Stop playing this stream?"), list=list)

	def cbDoExit(self, answer):
		answer = answer and answer[1]
		if answer == "y":
			if self.cbListCommand is not None:
				self.cbListCommand(256)
			self.close()

	def setSeekState(self, wantstate):
		service = self.session.nav.getCurrentService()
		if service is None:
			print("[StalkerClient] No Service found")
			return

		pauseable = service.pause()
		if pauseable is not None:
			if wantstate == self.PLAYER_PAUSED:
				pauseable.pause()
				self.state = self.PLAYER_PAUSED
				if not self.shown:
					self.hidetimer.stop()
					self.show()
			elif wantstate == self.PLAYER_PLAYING:
				pauseable.unpause()
				self.state = self.PLAYER_PLAYING
				if self.shown:
					self.__setHideTimer()
		else:
			self.state = self.PLAYER_PLAYING

	def doInfoAction(self):
		if self.shown:
			self.hidetimer.stop()
			self.hide()
			self.event_timer.stop()
		else:
			self.checkServiceEvents()
			self.show()
			if self.state == self.PLAYER_PLAYING:
				self.__setHideTimer()

	def doPlay(self):
		if self.state == self.PLAYER_PAUSED:
			if self.shown:
				self.__setHideTimer()	
		self.state = self.PLAYER_PLAYING
		self.session.nav.playService(self.service_ref)
		if self.shown:
			self.__setHideTimer()

	def playpauseService(self):
		if self.state == self.PLAYER_PLAYING:
			self.setSeekState(self.PLAYER_PAUSED)
		elif self.state == self.PLAYER_PAUSED:
			self.setSeekState(self.PLAYER_PLAYING)

	def openServiceList(self):
		if self.cbListCommand is not None:
			self.cbListCommand(0)
		self.close()

	def onKeyUp(self):
		if self.cbListCommand is not None:
			self.cbListCommand(-1)
		self.close()

	def onKeyDown(self):
		if self.cbListCommand is not None:
			self.cbListCommand(+1)
		self.close()

	def onKeyLeft(self):
		if self.cbServiceCommand is not None:
			self.resetServiceEvents()
			self.cbServiceCommand(-1, self.setServiceInfo)
			self.__setHideTimer()

	def onKeyRight(self):
		if self.cbServiceCommand is not None:
			self.resetServiceEvents()
			self.cbServiceCommand(+1, self.setServiceInfo)
			self.__setHideTimer()

	def onKeyEPG(self):
		self.hidetimer.stop()
		self.hide()
		self.event_timer.stop()
		if len(self.event_now_next) > 0 and isinstance(self.event_now_next[0], StalkerEvent):
			self.event_view_cur = 0
			self.session.openWithCallback(self.doInfoAction, StalkerClient_EventViewEPGSelect, self.event_now_next[0], (self.service.getId(), self.service.name), self.eventViewCallback, self.openSingleEPG, self.opneMultiEPG)
		else:
			self.session.openWithCallback(self.doInfoAction, StalkerClient_EPGSelection, (self.service.getId(), self.service.name), EPG_TYPE_MULTI)

	def onKeyMenu(self):
		self.hidetimer.stop()
		self.hide()
		self.event_timer.stop()
		self.session.openWithCallback(self.doInfoAction, StalkerClient_SetupScreen)

	def eventViewCallback(self, setEvent, setService, val):
		epglist = self.event_now_next
		if len(epglist) > 1:
			self.event_view_cur = 0 if self.event_view_cur == 1 else 1
			setEvent(epglist[self.event_view_cur])

	def openSingleEPG(self):
		self.session.open(StalkerClient_EPGSelection, (self.service.getId(), self.service.name), EPG_TYPE_SINGLE)

	def opneMultiEPG(self):
		self.session.open(StalkerClient_EPGSelection, (self.service.getId(), self.service.name), EPG_TYPE_MULTI)
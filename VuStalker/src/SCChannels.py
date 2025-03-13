from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ChoiceList import ChoiceList, ChoiceEntryComponent
from Components.EpgList import EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.config import config
from Screens.EpgSelection import EPGSelection

from enigma import eTimer, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT

from .SCPlayer import StalkerClient_Player
from .SCConfig import StalkerClient_SetupScreen
from .SCEPG import StalkerClient_EPGSelection, updateEvent
from .SCInfo import scinfo, scthreads, getTsidOnid, createStalkerSref
from .stalkerclient import SUPPORT_MODULES, SCThread, stalker

from copy import deepcopy
from math import ceil as math_ceil


class StalkerClient_AccountInfoScreen(Screen):
	skin_default_1080p = """
	<screen name="stalkerclientinfo" position="center,center" size="900,300">
		<widget name="AccountInfo" position="48,45" size="805,200" font="Regular;28" halign="left" />
	</screen>
	"""

	skin_default = """
	<screen name="stalkerclientinfo" position="center,center" size="600,250">
		<widget name="AccountInfo" position="20,25" size="560,200" font="Regular;20" halign="left" />
	</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		dh = self.session.desktop.size().height()
		self.skin = StalkerClient_AccountInfoScreen.skin_default_1080p if dh > 720 else StalkerClient_AccountInfoScreen.skin_default

		self["AccountInfo"] = Label(" ")
		self["actions"] = ActionMap(["OkCancelActions"],
			{
				"cancel": self.close,
				"ok": self.close,
			})

		self.thread = SCThread('stalkerclientinfo')
		scthreads.pushThread(self.thread)

		self.onLayoutFinish.append(self.onLayoutFinishCB)
		self.onClose.append(self.onCloseCB)

	def onLayoutFinishCB(self):
		self.title = (_("StalkerClient Account"))

		authenticated = stalker.isAuthenticated()
		available = stalker.isAvailable(SUPPORT_MODULES['account'])

		def getAccountInfoCB(result):
			if result:
				AccountInfo = ""
				for i in [i for i in list(result.values()) if isinstance(result, dict)]:
					AccountInfo += (str(i) + "\n") if (len(i) > 0) else ""
					self["AccountInfo"].setText(AccountInfo)

		if authenticated and available:
			self.thread.addTask(getAccountInfoCB, stalker.getAccountInfo)
		else:
			self["AccountInfo"].setText("")

	def onCloseCB(self):
		self.onClose.remove(self.onCloseCB)

		t = scthreads.popThread()
		if t:
			t.kill()
			t.join()


from Screens.InfoBar import InfoBar
from Screens.ChannelSelection import BouquetSelector


class StalkerClient_ChannelContextMenu(Screen):
	skin_default_1080p = """
	<screen name="stalkerclientcontext" position="center,center" size="680,300">
		<widget name="info" position="45,30" size="620,60" font="Regular;28" halign="left" />
		<widget name="menu" position="0,95" size="680,200" itemHeight="36" scrollbarMode="showOnDemand" />
	</screen>
	"""

	skin_default = """
	<screen name="stalkerclientcontext" position="center,center" size="350,260">
		<widget name="info" position="45,25" size="300,30" font="Regular;20" halign="left" />
		<widget name="menu" position="0,70" size="350,180"  valign="center" scrollbarMode="showOnDemand" />
	</screen>
	"""

	def __init__(self, session, service):
		Screen.__init__(self, session)
		self.session = session
		dh = self.session.desktop.size().height()
		self.skin = StalkerClient_ChannelContextMenu.skin_default_1080p if dh > 720 else StalkerClient_ChannelContextMenu.skin_default

		self.service = service
		sid = int(self.service.getId())
		tsid, onid = getTsidOnid()
		haslink = int(int(self.service.m_http_temp_link) == 1 or int(self.service.m_load_balancing) == 1)
		uri = self.service.getUrl(False).replace(':', '%3a')
		name = self.service.name
		self.service_ref = createStalkerSref(sid, tsid, onid, haslink, uri, name)

		self.csel = InfoBar.instance.servicelist
		self.bsel = None

		self["actions"] = ActionMap(["OkCancelActions"],
			{
				"ok": self.onKeyOK,
				"cancel": self.onKeyCancel,
			})

		self.setTitle(_("StalkerClient TV Menu"))
		self["info"] = Label(self.service.name)

		self.menulist = []
		self["menu"] = ChoiceList(self.menulist)
		self.bouquets = None
		self.onLayoutFinish.append(self.onLayoutFinishCB)

	def onLayoutFinishCB(self):
		self.bouquets = self.csel.getBouquetList()
		bouquetCnt = 0
		if self.bouquets:
			bouquetCnt = len(self.bouquets)
		if config.usage.multibouquet.value and bouquetCnt > 1:
			self.menulist.append(ChoiceEntryComponent(text=(_("add service to bouquet"), self.addServiceToBouquetSelected, 0)))
		elif bouquetCnt == 1:
			self.menulist.append(ChoiceEntryComponent(text=(_("add service to favourites"), self.addServiceToBouquetSelected, 1)))
		self["menu"].setList(self.menulist)

	def onKeyOK(self):
		(_text, fnc, idx) = self["menu"].getCurrent()[0]
		fnc(idx)

	def onKeyCancel(self):
		self.close()

	def addServiceToBouquetSelected(self, idx):
		if idx == 0:
			self.bsel = self.session.openWithCallback(self.bouquetSelClosed, BouquetSelector, self.bouquets, self.addCurrentServiceToBouquet)
		elif idx == 1:  # add to only one existing bouquet
			self.addCurrentServiceToBouquet(self.bouquets[0][1], closeBouquetSelection=False)

	def bouquetSelClosed(self, recursive):
		self.bsel = None
		if recursive:
			self.close(False)

	def addCurrentServiceToBouquet(self, dest, closeBouquetSelection=True):
		self.csel.addServiceToBouquet(dest, self.service_ref)
		scinfo.epgdb.serviceListUpdated()

		if self.bsel is not None:
			self.bsel.close(True)
		else:
			self.close(closeBouquetSelection)  # close bouquet selection


class StalkerClient_ChannelSelection(Screen):
	MODE_DEFAULT = 0
	MODE_GENRE = 1
	MODE_SERVICE = 2

	skin_default_1080p = """
	<screen name="stalkerclientchannels" position="center,center" size="900,745">
		<ePixmap pixmap="skin_default/buttons/red.png" position="48,10" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="268,10" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="493,10" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="718,10" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="48,10" zPosition="1" size="140,40" font="Regular;28" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_green" render="Label" position="268,10" zPosition="1" size="140,40" font="Regular;28" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_yellow" render="Label" position="493,10" zPosition="1" size="140,40" font="Regular;28" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_blue" render="Label" position="718,10" zPosition="1" size="140,40" font="Regular;28" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
		<widget name="sclist" position="0,60" size="900,640" backgroundColor="#000000" foregroundColor="#9c9c9c" zPosition="10" scrollbarMode="showOnDemand" />
		<widget name="infomation" position="30,710" size="860,32" font="Regular;26" halign="left" />
	</screen>
	"""

	skin_default = """
	<screen name="stalkerclientchannels" position="center,center" size="600,570">
		<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="455,0" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
		<widget source="key_blue" render="Label" position="455,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
		<widget name="sclist" position="0,50" size="600,480" backgroundColor="#000000" foregroundColor="#9c9c9c" zPosition="10" scrollbarMode="showOnDemand" />
		<widget name="infomation" position="22,540" size="575,20" font="Regular;18" halign="left" />
	</screen>
	"""

	def __init__(self, session, csel=None, parent=None):
		Screen.__init__(self, session, parent=parent)
		self.session = session
		dh = self.session.desktop.size().height()
		self.skin = StalkerClient_ChannelSelection.skin_default_1080p if dh > 720 else StalkerClient_ChannelSelection.skin_default

		self["actions"] = ActionMap(["OkCancelActions", "WizardActions", "ColorActions", "MenuActions", "ChannelSelectEPGActions"], {
			"ok": self.onKeyOK,
			"cancel": self.onKeyCancel,
			"up": self.onKeyUp,
			"down": self.onKeyDown,
			"left": self.onKeyLeft,
			"right": self.onKeyRight,
			"red": self.onKeyRed,
			"green": self.onKeyGreen,
			"yellow": self.onKeyYellow,
			"blue": self.onKeyBlue,
			"menu": self.onKeyMenu,
			"showEPGList": self.onKeyEPG,
		}, -1)

		self["key_red"] = StaticText(_("Genres"))
		self["key_green"] = StaticText(_("Account"))
		self["key_yellow"] = StaticText(_("Reload"))
		self["key_blue"] = StaticText(_("Setup"))

		self.scList = StalkerList(dh)
		self.scListMode = self.MODE_DEFAULT
		self.scListGenre = [self.scList.getSelectedIndex(), "*"]
		self.scListService = ["*", 1, 0]
		self.scListLast = None
		self["sclist"] = self.scList

		self.scPlayerQuit = True
		self.scPlayerCur = self.scList.getCurrent()
		self.scPlayerRef = None

		self.m_total_items = {}
		self.m_max_page_items = 0
		self.m_last_page = 0

		self.m_need2reload_queue = []
		self["infomation"] = Label(_("Loading"))

		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.onLayoutFinishCB)

		self.thread = SCThread('stalkerclientchannels')
		scthreads.pushThread(self.thread)

		self.onLayoutFinish.append(self.onLayoutFinishCB)
		self.onClose.append(self.onCloseCB)

	def onLayoutFinishCB(self):
		self.title = (_("Stalker Client"))
		if stalker.isAvailable(SUPPORT_MODULES['tv']):
			self.showGenres()
		else:
			self.checkTimer.start(1000, True)

	def onCloseCB(self):
		self.checkTimer.callback.remove(self.onLayoutFinishCB)
		self.checkTimer = None

		self.onClose.remove(self.onCloseCB)

		t = scthreads.popThread()
		if t:
			t.kill()
			t.join()

	def updateInfomation(self):
		if self.scList.hasItems():
			if int(self.scList.getPage()) > 0:
				cmd = "%s/%s " % (self.scList.getPage(), self.m_last_page)
			else:
				cmd = ""

			item = self.scList.getCurrent()
			if item.isFolder():
				cmd += _("Available") if stalker.isAvailable(SUPPORT_MODULES['tv']) else _("Not available")
			else:
				cmd += " " + str(item.getUrl(False))

			self["infomation"].setText(cmd)
		else:
			self["infomation"].setText(_("Not available"))

	def totalItems(self, genre, force=False):
		total_items = self.m_total_items.get(genre[0].getId())

		if total_items:
			genre[0].size = total_items
		else:
			result = stalker.getOrderedList(genre[0].getId(), 1, force)
			if result:
				try:
					self.m_total_items[genre[0].getId()] = result.get('total_items')
					genre[0].size = self.m_total_items[genre[0].getId()]
				except Exception as e:
					print("[StalkerClient]", e)
					genre[0].size = -1

		new = (eListboxPythonMultiContent.TYPE_TEXT, genre[1][1] + genre[1][3], genre[1][2], 100, genre[1][4], 0, RT_HALIGN_RIGHT, str(genre[0].size))
		genre.remove(genre[2])
		genre.append(new)

	def showGenres(self, force=False):
		def totalItemsCB(unused):
			self.scList.updateList(self.scList.getSelectedIndex())

		def showGenresDone():
			self.thread.hold = False

		def showGenresCB(result):
			if result:
				self.scListMode = self.MODE_GENRE
				self.scListGenre[1] = "*"

				self.scList.clear()
				for genre in result:
					if isinstance(genre, dict):
						g = StalkerGenre(genre)
						self.scList.addItem(g)

				self.scList.updateList(self.scListGenre[0])

				for g in self.scList.list:
					self.thread.addTask(totalItemsCB, self.totalItems, g, force)
				self.thread.addTask(None, showGenresDone)
			else:
				print("[StalkerClient] got no genres.")

			self.updateInfomation()

		if stalker.isAvailable(SUPPORT_MODULES['tv']):
			self.thread.addTask(showGenresCB, stalker.getGenres, force)

	def showOrderedList(self, id, page="1", index=0, force=False):
		if (id, page) in self.m_need2reload_queue:
			force = True
			self.m_need2reload_queue.remove((id, page))

		def showOrderedListCB(result):
			items = None
			if result:
				try:
					items = result.get('data')
					total_items = float(result.get('total_items'))

					self.m_max_page_items = int(result.get('max_page_items'))
					self.m_last_page = int(math_ceil(total_items / float(self.m_max_page_items)))
				except Exception as e:
					print("[StalkerClient]", e)
					items = None

			if items:
				self.scListMode = self.MODE_SERVICE
				self.scListService[0] = id
				need2reload = False

				self.scList.clear(page, self.m_last_page)
				for service in items:
					if isinstance(service, dict):
						s = StalkerService(service)
						self.scList.addItem(s)
						if s.name == '':
							need2reload = True
					else:
						need2reload = True

				if page is self.m_last_page and len(items) != int(total_items % self.m_max_page_items):
					need2reload = True

				if need2reload:
					self.m_need2reload_queue.append((id, page))

				self.scListService[1] = page
				self.scListService[2] = index
				self.scList.updateList(index)
			else:
				self.m_need2reload_queue.append((id, page))
			self.updateInfomation()

		if stalker.isAvailable(SUPPORT_MODULES['tv']):
			self.thread.addTask(showOrderedListCB, stalker.getOrderedList, id, page, force)

	def onKeyLeft(self):
		idx = self.scList.getSelectedIndex()
		self.scList.leftPage()
		if self.scListMode is self.MODE_GENRE:
			self.scListGenre[0] = self.scList.getSelectedIndex()
		if self.scListMode is self.MODE_SERVICE:
			if int(self.m_last_page) > 1:
				self.showOrderedList(self.scListGenre[1], self.scList.getPage(), idx)
			else:
				self.scListService[2] = self.scList.getSelectedIndex()
		self.updateInfomation()

	def onKeyRight(self):
		idx = self.scList.getSelectedIndex()
		self.scList.rightPage()
		if self.scListMode is self.MODE_GENRE:
			self.scListGenre[0] = self.scList.getSelectedIndex()
		if self.scListMode is self.MODE_SERVICE:
			if int(self.m_last_page) > 1:
				self.showOrderedList(self.scListGenre[1], self.scList.getPage(), idx)
			else:
				self.scListService[2] = self.scList.getSelectedIndex()
		self.updateInfomation()

	def onKeyUp(self):
		self.scList.upPage()
		if self.scListMode is self.MODE_GENRE:
			self.scListGenre[0] = self.scList.getSelectedIndex()
		if self.scListMode is self.MODE_SERVICE:
			if self.scList.getRefresh():
				self.showOrderedList(self.scListGenre[1], self.scList.getPage(), self.m_max_page_items)
			else:
				self.scListService[2] = self.scList.getSelectedIndex()
		self.updateInfomation()

	def onKeyDown(self):
		self.scList.downPage()
		if self.scListMode is self.MODE_GENRE:
			self.scListGenre[0] = self.scList.getSelectedIndex()
		if self.scListMode is self.MODE_SERVICE:
			if self.scList.getRefresh():
				self.showOrderedList(self.scListGenre[1], self.scList.getPage(), 0)
			else:
				self.scListService[2] = self.scList.getSelectedIndex()
		self.updateInfomation()

	def onKeyMenu(self):
		if self.scList.hasItems() and self.scListMode is self.MODE_SERVICE:
			self.session.open(StalkerClient_ChannelContextMenu, self.scList.getCurrent())

	def onKeyRed(self):
		if self.scList.hasItems():
			item = self.scList.getCurrent()
			if item.isPlayable():
				self.showGenres()

	def onKeyGreen(self):
		self.session.open(StalkerClient_AccountInfoScreen)

	def onKeyYellow(self):
		if self.thread.hold:
			print("[StalkerClient] in progress...")
			return

		def authenticateCB(result):
			if result and stalker.isAvailable(SUPPORT_MODULES['tv']):
				self.showGenres(True)

		self.scListGenre[0] = 0
		self.m_total_items.clear()
		self.thread.clearTask()

		authenticated = stalker.isAuthenticated()
		if not authenticated:
			self.thread.addTask(authenticateCB, stalker.authenticate)
		else:
			self.showGenres(True)
		self.thread.hold = True

	def onKeyBlue(self):
		if self.scListMode is self.MODE_SERVICE:
			self.session.open(StalkerClient_SetupScreen)
		else:
			self.session.openWithCallback(self.showGenres, StalkerClient_SetupScreen)

	def onKeyEPG(self):
		if self.scListMode is self.MODE_SERVICE:
			current = self.scList.getCurrent()
			self.session.open(StalkerClient_EPGSelection, (current.getId(), current.name), EPG_TYPE_SINGLE)

	def onKeyCancel(self):
		self.thread.clearTask()

		if self.scPlayerQuit:
			if self.scList.hasItems():
				item = self.scList.getCurrent()
				if item.isFolder():
					self.close()
				else:
					self.showGenres()
			else:
				self.close()
		else:
			if self.scListLast:
				self.scListGenre = self.scListLast[0][:]
				self.scListService = self.scListLast[1][:]
				self.showOrderedList(*self.scListService)
			self.doStreamAction(player=True)

	def onKeyOK(self):
		if self.scList.hasItems():
			self.thread.clearTask()

			item = self.scList.getCurrent()
			if item.isFolder():
				self.scListGenre = [self.scList.getSelectedIndex(), item.getId()]
				self.showOrderedList(self.scListGenre[1])
			elif item.isPlayable():
				uri_addr = item.getUrl(False)
				print("[StalkerClient] PLAY", item.name, uri_addr)
				self.doStreamAction(uri_addr, True)

	def doStreamAction(self, uri=None, player=False):
		service = self.scList.getCurrent()
		if uri and (self.scPlayerCur is None or self.scPlayerCur.getId() != service.getId()):
			sid = int(service.getId())
			tsid, onid = getTsidOnid()
			haslink = int(int(service.m_http_temp_link) == 1 or int(service.m_load_balancing) == 1)
			uri = uri.replace(':', '%3a')
			name = service.name
			self.scPlayerRef = createStalkerSref(sid, tsid, onid, haslink, uri, name)

			self.scPlayerCur = service
			if self.scPlayerQuit:
				self.beforeService = self.session.nav.getCurrentlyPlayingServiceReference()
				self.scPlayerQuit = False

			self.scListLast = (self.scListGenre[:], self.scListService[:])
		else:
			self.scPlayerRef = self.session.nav.getCurrentlyPlayingServiceReference()

		if player:
			self.currentService = self.session.openWithCallback(self.cbFinishedStream,
				StalkerClient_Player,
				self.scPlayerRef, self.scPlayerCur,
				self.cbListCommand, self.cbServiceCommand
			)
		else:
			self.session.nav.playService(self.scPlayerRef)

	def cbListCommand(self, val):
		l = self["sclist"]
		old = l.getCurrent()
		if val == -1:
			self.onKeyUp()
		elif val == +1:
			self.onKeyDown()
		cur = l.getCurrent()

		if val == 256:
			self.scPlayerQuit = True
		else:
			self.scPlayerQuit = False

	def cbServiceCommand(self, val, setInfo=None):
		l = self["sclist"]
		old = l.getCurrent()
		if val == -1:
			self.onKeyUp()
		elif val == +1:
			self.onKeyDown()
		cur = l.getCurrent()

		def readyPlay():
			uri_addr = None
			cur = self.scList.getCurrent()
			if cur.isPlayable():
				uri_addr = cur.getUrl(False)
				print("[StalkerClient] PLAY", cur.name, uri_addr)

			if setInfo:
				setInfo(cur)

			return uri_addr

		self.thread.addTask(self.doStreamAction, readyPlay)

	def cbFinishedStream(self):
		if self.scPlayerQuit:
			self.session.nav.playService(self.beforeService)
			print('[StalkerClient] player done!!')
			self.scPlayerCur = None


class StalkerBaseService(object):
	def __init__(self, isFolder=False, isPlayable=False):
		self.m_folder = isFolder
		self.m_playable = isPlayable

	def isFolder(self):
		return self.m_folder

	def isPlayable(self):
		return self.m_playable


class StalkerService(StalkerBaseService):
	def __init__(self, data):
		StalkerBaseService.__init__(self, isPlayable=True)

		self.m_id = str(data.get('id'))
		self.m_name = str(data.get('name', '')).strip()
		self.m_number = int(data.get('number', 0))
		self.m_cmd = data.get('cmd')
		self.m_type, self.m_url = self.parseUrl(self.m_cmd)
		self.m_http_temp_link = data.get('use_http_tmp_link')
		self.m_load_balancing = data.get('use_load_balancing')

	def intValue(self, value):
		try:
			return int(value)
		except:
			return 0

	def dict(self):
		data = {}
		data["id"] = self.m_id
		data["name"] = self.m_name
		data["url"] = self.m_url
		data["use_http_tmp_link"] = self.m_http_temp_link
		data["use_load_balancing"] = self.m_load_balancing
		return data

	def parseUrl(self, cmd):
		cmd = str(cmd).split(" ")
		if len(cmd) > 1:
			u = cmd[1]
			t = cmd[0]
		else:
			u = cmd[0]
			t = "ffrt"
		return t, u

	def checkUrl(self):
		if stalker.isForceLinkCheck():
			return True

		return int(self.m_http_temp_link) == 1 or int(self.m_load_balancing) == 1

	def getUrl(self, real=False):
		return self.m_url

	def getId(self):
		return self.m_id

	def getName(self):
		return self.m_name

	def setName(self, name):
		self.m_name = name

	name = property(getName, setName)

	def __str__(self):
		return "[StalkerClient] TV [%04s] #%s %s %s (%s, %s)" % (self.m_id, self.m_number, self.m_name, self.m_url, self.m_http_temp_link, self.m_load_balancing)


class StalkerGenre(StalkerBaseService):
	def __init__(self, data, count=0):
		StalkerBaseService.__init__(self, isFolder=True)

		self.m_id = data.get('id')
		self.m_title = str(data.get('title')).strip().capitalize()

		self.m_count = count

	def dict(self):
		data = {}
		data["id"] = self.m_id
		data["title"] = self.m_title
		data["count"] = self.m_count
		return data

	def getId(self):
		return self.m_id

	def getName(self):
		return self.m_title

	def setName(self, title):
		self.m_title = title

	def getSize(self):
		return self.m_count

	def setSize(self, count):
		self.m_count = count

	name = property(getName, setName)
	size = property(getSize, setSize)

	def __str__(self):
		return "[StalkerClient] Genre [%03s] %s (%s)" % (self.m_id, self.m_title, self.m_count)


def StalkerEntryComponent(entry, x, y, w, h):
	res = [entry]
	name = entry.name

	if entry.isFolder():
		size = str(entry.size) if entry.size > 0 else "loading"
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w - 100, h, 0, RT_HALIGN_LEFT, name))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x + w - 100, y, 100, h, 0, RT_HALIGN_RIGHT, size))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT, name))
	return res


class StalkerList(MenuList):
	def __init__(self, dh, enableWrapAround=False):
		self.dh = dh
		self.font_size = 28 if dh > 720 else 22
		self.item_width = 840 if dh > 720 else 550
		self.item_height = 40 if dh > 720 else 30

		self.list = []
		MenuList.__init__(self, [], enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont('Regular', self.font_size))
		self.l.setItemHeight(self.item_height)

		self.page_current = -1
		self.page_last = 0
		self.item_last = -1
		self.item_refresh = False

	def clear(self, current=-1, last=-1):
		del self.list[:]
		self.l.setList(self.list)
		self.page_current = current
		self.page_last = last
		self.item_last = -1
		self.item_refresh = False

	def addItem(self, item):
		self.list.append(StalkerEntryComponent(item, self.font_size, self.font_size / 4, self.item_width, self.item_height))
		self.item_last += 1

	def leftPage(self):
		if self.page_last < 0 or int(self.page_last) == 1:
			self.pageUp()
		else:
			self.page_current = int(self.page_current) - 1 if (int(self.page_current) > 1) else self.page_last

	def rightPage(self):
		if self.page_last < 0 or int(self.page_last) == 1:
			self.pageDown()
		else:
			self.page_current = int(self.page_current) + 1 if (int(self.page_current) < int(self.page_last)) else 1

	def upPage(self):
		if self.getSelectedIndex() > 0:
			self.up()
		else:
			if int(self.page_last) < 2:
				self.moveToIndex(self.item_last)
			else:
				self.item_refresh = True if not int(self.page_last) == 1 else False
				self.leftPage()

	def downPage(self):
		if self.getSelectedIndex() < self.item_last:
			self.down()
		else:
			if int(self.page_last) < 2:
				self.moveToIndex(0)
			else:
				self.item_refresh = True if not int(self.page_last) == 1 else False
				self.rightPage()

	def updateList(self, index=0):
		self.l.setList(self.list)
		i = index if int(index) < int(self.item_last) else self.item_last
		self.moveToIndex(int(i))

	def getRefresh(self):
		return self.item_refresh

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]

	def getPage(self):
		return self.page_current

	def hasItems(self):
		return True if len(self.list) > 0 else False

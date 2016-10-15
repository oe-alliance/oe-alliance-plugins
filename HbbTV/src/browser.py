from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label, MultiColorLabel
from Components.Language import language
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean
from Components.Sources.StaticText import StaticText
from Components.config import ConfigText, ConfigSelection, ConfigSlider, getConfigListEntry

import os, vbcfg

from enigma import fbClass, eRCInput, eTimer, getDesktop

from __init__ import _
from bookmark import BookmarkManager, BookmarkData, CategoryData
from vbipc import VBController

strIsEmpty = lambda x: x is None or len(x) == 0

class BrowserSetting:
	def __init__(self):
		self._settingFileName = '%s/home/setting.ini' % vbcfg.APPROOT
		self._start = None
		self._type = None
		self._keymap = None
		self._read()

	def _read(self):
		if not os.path.exists(self._settingFileName):
			self.getDefault()
			return

		f = open(self._settingFileName)
		for line in f.readlines():
			if line.startswith('start='):
				tmp = line[6:len(line)-1].split()
				self._start = tmp[0]
				if len(tmp) > 1:
					self._type = int(tmp[1])
				else:	self._type = 0
			elif line.startswith('keymap='):
				self._keymap = line[7:len(line)-1]
		f.close()

	def _write(self):
		tmpstr = []
		tmpstr.append('start=%s %d\n' % (self._start, self._type))
		tmpstr.append('keymap=%s\n' % (self._keymap))
		f = open(self._settingFileName, 'w')
		f.writelines(tmpstr)
		f.close()

	def getDefault(self):
		self._start = 'http://www.google.com'
		self._type = 0
		self._keymap = 'us-rc'

	def setData(self, start, types=0, keymap="us-rc"):
		self._start = start
		self._type = types
		self._keymap = keymap
		self._write()

	def getData(self):
		return {
			'start':self._start,
			'type':self._type,
			'keymap':self._keymap,
		}

class BrowserPositionSetting:
	def __init__(self):
		self._positionFileName = '%s/home/position.cfg' % vbcfg.APPROOT
		self._left = 0
		self._width = 0
		self._top = 0
		self._height = 0
		self._read()

	def _read(self):
		if not os.path.exists(self._positionFileName):
			self.getDefault()
			return

		f = open(self._positionFileName)
		str = f.read()
		f.close()

		pos = str.split();
		self._left = int(pos[0])
		self._width = int(pos[1])
		self._top = int(pos[2])
		self._height = int(pos[3])

	def _write(self):
		tmpstr = "%d %d %d %d\n" % (self._left, self._width, self._top, self._height)
		f = open(self._positionFileName, 'w')
		f.write(tmpstr)
		f.close()

	def getDefault(self):
		self._left = 0
		self._top = 0
		self._width = 720
		self._height = 576

	def setPosition(self, params):
		self._left = params[0]
		self._width = params[1]
		self._top = params[2]
		self._height = params[3]
		self._write()

	def getPosition(self):
		return (self._left, self._width, self._top, self._height)

class BrowserPositionWindow(Screen, ConfigListScreen):
	skin = 	"""
		<screen position="0,0" size="%d,%d" title="Browser Position Setup" backgroundColor="#27d8dee2" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="%d,%d" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="%d,%d" size="140,40" alphatest="on" />"

			<widget source="key_red" render="Label" position="%d,%d" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="%d,%d" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />

			<widget name="config" zPosition="2" position="%d,%d" size="500,200" scrollbarMode="showOnDemand" foregroundColor="#1c1c1c" transparent="1" />
		</screen>
		"""
	def __init__(self, session):
		w,h   = session.desktop.size().width(), session.desktop.size().height()
		cw,ch = w/2, h/2
		#                             btn_red        btn_green     lb_red         lb_green      config
		self.skin = self.skin % (w,h, cw-190,ch-110, cw+50,ch-110, cw-190,ch-110, cw+50,ch-110, cw-250,ch-50)

		Screen.__init__(self,session)
		self.session = session
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyOk,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["current"] = StaticText(_(" "))
		vbcfg.g_position = vbcfg.getPosition()
		self.createSetup()

	def createSetup(self):
		self.list = []

		params = BrowserPositionSetting().getPosition()
		vbcfg.setPosition(params)

		left   = params[0]
		width  = params[1]
		top    = params[2]
		height = params[3]

		self.dst_left   = ConfigSlider(default = left, increment = 5, limits = (0, 720))
		self.dst_width  = ConfigSlider(default = width, increment = 5, limits = (0, 720))
		self.dst_top    = ConfigSlider(default = top, increment = 5, limits = (0, 576))
		self.dst_height = ConfigSlider(default = height, increment = 5, limits = (0, 576))

		self.dst_left_entry   = getConfigListEntry(_("left"), self.dst_left)
		self.dst_width_entry  = getConfigListEntry(_("width"), self.dst_width)
		self.dst_top_entry    = getConfigListEntry(_("top"), self.dst_top)
		self.dst_height_entry = getConfigListEntry(_("height"), self.dst_height)

		self.list.append(self.dst_left_entry)
		self.list.append(self.dst_width_entry)
		self.list.append(self.dst_top_entry)
		self.list.append(self.dst_height_entry)

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def resetDisplay(self):
		for entry in self["config"].getList():
			self["config"].l.invalidateEntry(self["config"].getList().index(entry))

	def adjustBorder(self):
		if self["config"].getCurrent() == self.dst_left_entry:
			if self.dst_left.value + self.dst_width.value >720:
				self.dst_width.setValue(720-self.dst_left.value)
				self.resetDisplay()
		elif self["config"].getCurrent() == self.dst_width_entry:
			if self.dst_left.value + self.dst_width.value >720:
				self.dst_left.setValue(720-self.dst_width.value)
				self.resetDisplay()
		elif self["config"].getCurrent() == self.dst_top_entry:
			if self.dst_top.value + self.dst_height.value >576:
				self.dst_height.setValue(576-self.dst_top.value)
				self.resetDisplay()
		elif self["config"].getCurrent() == self.dst_height_entry:
			if self.dst_top.value + self.dst_height.value >576:
				self.dst_top.setValue(576-self.dst_height.value)
				self.resetDisplay()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.adjustBorder()
		params = (int(self.dst_left.value), int(self.dst_width.value), int(self.dst_top.value), int(self.dst_height.value))
		vbcfg.setPosition(params)

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.adjustBorder()
		params = (int(self.dst_left.value), int(self.dst_width.value), int(self.dst_top.value), int(self.dst_height.value))
		vbcfg.setPosition(params)

	def keyOk(self):
		params = (int(self.dst_left.value), int(self.dst_width.value), int(self.dst_top.value), int(self.dst_height.value))
		BrowserPositionSetting().setPosition(params)
		vbcfg.setPosition(vbcfg.g_position)
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			vbcfg.setPosition(vbcfg.g_position)
			self.close()

	def cancelConfirm(self,ret):
		if ret:
			vbcfg.setPosition(vbcfg.g_position)
			self.close()


class BrowserPreferenceWindow(ConfigListScreen, Screen):
	skin = """
		<screen position="center,120" size="600,350" title="Preference">
			<widget name="url" position="5,0" size="590,100" valign="center" font="Regular;20" />
			<widget name="config" position="0,100" size="600,200" scrollbarMode="showOnDemand" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="310,310" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="150,310" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="310,310" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="150,310" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""
	def __init__(self, session, currentUrl):
		self.session = session
		Screen.__init__(self, session)

		self.menulist = []
		ConfigListScreen.__init__(self, self.menulist)

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", ], {
			"red"	 : self.keyRed,
			"green"	 : self.keyGreen,
			"ok"	 : self.keyOK,
			"cancel" : self.keyRed
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["url"] = Label()

		self._currentPageUrl = currentUrl
		if self._currentPageUrl is None:
			self._currentPageUrl = ''
		self._startPageUrl = None
		self._keymapType = None
		self.makeMenuEntry()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Preference'))

	def updateStartPageUrl(self):
		if self.menuItemStartpage.value == "startpage":
			self["url"].setText(self._startPageUrl)
		elif self.menuItemStartpage.value == "current":
			self["url"].setText(self._currentPageUrl)
		elif self.menuItemStartpage.value == "direct":
			self["url"].setText('')

	def keyGreen(self):
		url = self["url"].getText()
		if strIsEmpty(url):
			self.session.open(MessageBox, _('Invalid URL!!(Empty)\nPlease, Input to the URL.'), type = MessageBox.TYPE_INFO)
			return
		mode = 0
		if url.find('/usr/local/manual') > 0:
			mode = 1
		self._keymapType = self.menuItemKeyboardLayout.value
		BrowserSetting().setData(url, mode, self._keymapType)
		VBController.command('CONTROL_RELOAD_KEYMAP')
		self.close()

	def keyRed(self):
		self.close()

	def keyOK(self):
		def _cb_directInputUrl(data):
			if strIsEmpty(data):
				return
			self["url"].setText(data)
		if self["config"].l.getCurrentSelectionIndex() == 0 and self.menuItemStartpage.value == "direct":
			self.session.openWithCallback(_cb_directInputUrl, VirtualKeyBoard, title=(_("Please enter URL here")), text='http://')

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.updateStartPageUrl()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.updateStartPageUrl()

	def getKeymapTypeList(self):
		types = []
		for f in os.listdir("%s/keymap" % vbcfg.APPROOT):
			filesplit = f.split('.')
			if len(filesplit) < 2:
				continue
			types.append((filesplit[1], filesplit[1]))
		types.sort()
		return types

	def makeMenuEntry(self):
		l = []
		l.append(("startpage", _("Start Page")))
		if not strIsEmpty(self._currentPageUrl):
			l.append(("current", _("Current Page")))
		l.append(("direct", _("Direct Input")))
		self.menuItemStartpage = ConfigSelection(default="startpage", choices = l)
		self.menuEntryStartpage = getConfigListEntry(_("Startpage"), self.menuItemStartpage)

		kl = self.getKeymapTypeList()

		try:
			d = BrowserSetting().getData()
			self._startPageUrl = d['start']
			self._keymapType = d['keymap']
			#d['type']
		except: self._startPageUrl = 'http://www.google.com'
		self.updateStartPageUrl()

		if self._keymapType is None or len(self._keymapType) == 0:
			self._keymapType = "us-rc"
		self.menuItemKeyboardLayout = ConfigSelection(default=self._keymapType, choices = kl)
		self.menuEntryKeyboardLayout = getConfigListEntry(_("Keyboard Layout"), self.menuItemKeyboardLayout)
		self.resetMenuList()

	def resetMenuList(self):
		self.menulist = []
		self.menulist.append(self.menuEntryStartpage)
		self.menulist.append(self.menuEntryKeyboardLayout)

		self["config"].list = self.menulist
		self["config"].l.setList(self.menulist)

class BookmarkEditWindow(ConfigListScreen, Screen):
	CATEGORY,BOOKMARK = 0,1
	skin = """
		<screen position="center,center" size="600,140" title="Bookmark Edit">
			<widget name="config" position="0,0" size="600,100" scrollbarMode="showOnDemand" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="310,100" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="150,100" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="310,100" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="150,100" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />

			<widget source="VKeyIcon" render="Pixmap" pixmap="skin_default/buttons/key_text.png" position="0,100" zPosition="10" size="35,25" transparent="1" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>

		</screen>
		"""
	def __init__(self, session, _mode, _type, _data, _bm):
		self.mMode = _mode
		self.mType = _type
		self.mData = _data
		self.mSession = session
		self.mBookmarkManager = _bm

		if _data is not None:
			vbcfg.DEBUG("0x%x" % _data.mId)

		Screen.__init__(self, session)

		self.menulist = []
		ConfigListScreen.__init__(self, self.menulist)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions",], {
			"ok"	 : self.keyGreen,
			"green"	 : self.keyGreen,
			"red"	 : self.keyRed,
			"cancel" : self.keyRed,
		}, -2)

		self["VKeyIcon"] = Boolean(False)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))

		self.menuItemTitle = None
		self.menuItemUrl   = None
		self.menuItemName  = None

		self.menuEntryName = None
		self.menuEntryTitle = None
		self.menuEntryUrl = None

		self.makeConfigList()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Bookmark') + ' ' + self.mMode)

	def selectedItem(self):
		currentPosition = self["config"].getCurrent()
		if self.mType == BookmarkEditWindow.CATEGORY:
			return (_("Name"), self.menuItemName)
		else:
			if currentPosition == self.menuEntryTitle:
				return (_("Title"), self.menuItemTitle)
			elif currentPosition == self.menuEntryUrl:
				return (_("Url"), self.menuItemUrl)
		return None

	def showMessageBox(self, text):
		msg = _("Invalid ") + text + _("!!(Empty)\nPlease, Input to the") + " " + text + "."
		self.mSession.openWithCallback(self.showVKeyWindow, MessageBox, msg, MessageBox.TYPE_INFO)
		return False

	def showVKeyWindow(self, data=None):
		itemTitle = ""
		itemValue = ""
		selected = self.selectedItem()
		if selected is not None:
			itemValue = selected[1].value
			if strIsEmpty(itemValue):
				itemValue = ""
			itemTitle = selected[0]

		self.session.openWithCallback(self.cbVKeyWindow, VirtualKeyBoard, title=itemTitle, text=itemValue)

	def cbVKeyWindow(self, data=None):
		if data is not None:
			selected = self.selectedItem()
			if selected is not None:
				selected[1].setValue(data)

	def saveData(self):
		if self.mType == BookmarkEditWindow.CATEGORY:
			if self.mMode == _('Add'):
				categoryName = self.menuItemName.value
				if strIsEmpty(categoryName):
					return self.showMessageBox(_("Category Name"))
				self.mBookmarkManager.addCategory(categoryName)
			else:
				if strIsEmpty(self.menuItemName.value):
					return self.showMessageBox(_("Category Name"))
				self.mData.mName = self.menuItemName.value
				self.mBookmarkManager.updateCategory(self.mData)
		else:
			if self.mMode == _('Add'):
				bookmarkTitle = self.menuItemTitle.value
				bookmarkUrl = self.menuItemUrl.value
				if strIsEmpty(bookmarkTitle):
					self["config"].setCurrentIndex(0)
					return self.showMessageBox(_("Bookmark Title"))
				if strIsEmpty(bookmarkUrl):
					self["config"].setCurrentIndex(1)
					return self.showMessageBox(_("Bookmark URL"))
				self.mBookmarkManager.addBookmark(bookmarkTitle, bookmarkUrl, self.mData.mParent, 0)
			else:
				if strIsEmpty(self.menuItemTitle.value):
					self["config"].setCurrentIndex(0)
					return self.showMessageBox(_("Bookmark Title"))
				if strIsEmpty(self.menuItemUrl.value):
					self["config"].setCurrentIndex(1)
					return self.showMessageBox(_("Bookmark URL"))
				self.mData.mTitle = self.menuItemTitle.value
				self.mData.mUrl = self.menuItemUrl.value
				self.mBookmarkManager.updateBookmark(self.mData)
		return True

	def keyGreen(self):
		if not self.saveData():
			return
		self.close(True)

	def keyRed(self):
		self.close(False)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def makeConfigList(self):
		self.menulist = []

		if self.mType == BookmarkEditWindow.CATEGORY:
			self.menuItemName = ConfigText(default=self.mData.mName, visible_width=65, fixed_size=False)

			self.menuEntryName = getConfigListEntry(_("Name"), self.menuItemName)

			self.menulist.append(self.menuEntryName)
		else:
			self.menuItemTitle = ConfigText(default=self.mData.mTitle, visible_width=65, fixed_size=False)
			self.menuItemUrl   = ConfigText(default=self.mData.mUrl, visible_width=65, fixed_size=False)

			self.menuEntryTitle = getConfigListEntry(_("Title"), self.menuItemTitle)
			self.menuEntryUrl = getConfigListEntry(_("Url"), self.menuItemUrl)

			self.menulist.append(self.menuEntryTitle)
			self.menulist.append(self.menuEntryUrl)

		self["config"].list = self.menulist
		self["config"].l.setList(self.menulist)

class BrowserBookmarkWindow(Screen):
	skin = """
		<screen name="BrowserBookmarkWindow" position="center,120" size="600,400" title="Bookmark" >
			<widget name="bookmarklist" position="0,0" size="600,200" zPosition="10" scrollbarMode="showOnDemand" />

			<ePixmap pixmap="skin_default/buttons/key_0.png" position="556,330" size="35,30" alphatest="on" />
			<widget source="key_0" render="Label" position="258,330" zPosition="1" size="300,30" font="Regular;20" halign="right" valign="center"/>

			<ePixmap pixmap="skin_default/buttons/red.png" position="5,360" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,360" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,360" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="450,360" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="5,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="450,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, _session, _url=None, _title=None):
		self.mUrl = _url
		self.mTitle = _title
		self.mBookmarkManager = BookmarkManager.getInstance()
		self.mSession = _session
		Screen.__init__(self, _session)
		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions","ColorActions", "NumberActions"], {
				"ok"	: self.keyOK,
				"cancel": self.keyCancel,
				"red"	: self.keyRed,
				"green" : self.keyGreen,
				"yellow": self.keyYellow,
				"blue"	: self.keyBlue,
				"0" : self.keyNumber,
			},-2)

		self["key_red"]    = StaticText(_("Exit"))
		self["key_green"]  = StaticText(_("Add"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"]   = StaticText(_("Delete"))
		self["key_0"]      = StaticText(_("Set as Startpage"))

		self.mBookmarkList = self.setBookmarkList()
		self["bookmarklist"] = MenuList(self.mBookmarkList)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Bookmark'))

	def setBookmarkList(self):
		l = []
		#self.mBookmarkManager.dump()
		cd = self.mBookmarkManager.getBookmarkRoot()
		for ck in cd.iterkeys():
			l.append(('# ' + cd[ck].mName, cd[ck]))
			bd = cd[ck].mBookmarks
			for bk in bd.iterkeys():
				l.append(('    - ' + bd[bk].mTitle, bd[bk]))
		return l

	def updateBookmarkList(self):
		self.mBookmarkList = self.setBookmarkList()
		self["bookmarklist"].setList(self.mBookmarkList)

	def cbEditWindow(self, ret=False):
		if not ret:
			return
		self.updateBookmarkList()

	def getParentCategory(self):
		idx = self["bookmarklist"].getSelectedIndex()
		try:
			while idx >= 0:
				data = self.mBookmarkList[idx][0].strip()
				if data[0] == '#':
					return self.mBookmarkList[idx][1]
				idx -= 1
		except: pass
		return None

	def isCategoryItem(self):
		try:
			head = self["bookmarklist"].getCurrent()[0].strip()
			if head[0] == '#':
				return True
		except: pass
		return False

	def keyNumber(self):
		if self.isCategoryItem(): return

		data = self["bookmarklist"].getCurrent()[1]
		if strIsEmpty(data.mUrl):
			msg = _("Invalid URL. Please check again!!")
			self.mSession.open(MessageBox, msg, MessageBox.TYPE_INFO)
			return
		def cbSetStartpage(ret=None):
			if ret is None: return
			if ret:
				data = self["bookmarklist"].getCurrent()[1]
				BrowserSetting().setData(data.mUrl, data.mType)
		msg = _("Do you want to set selected url to the Startpage?")
		self.mSession.openWithCallback(cbSetStartpage, MessageBox, msg, MessageBox.TYPE_YESNO, default=True)

	def keyGreen(self):
		def cbGreen(data):
			if data is None:
				return
			if data[1] == 1:
				parent = self.getParentCategory()
				if parent is None:
					return
				if strIsEmpty(self.mTitle):
					return
				retAdd = self.mBookmarkManager.addBookmark(self.mTitle, self.mUrl, parent.mId, 0)
				if not retAdd:
					msg = _("Current page is already exist.")
					self.mSession.open(MessageBox, msg, MessageBox.TYPE_INFO)
				self.cbEditWindow(True)
			elif data[1] == 2:
				parent = self.getParentCategory()
				if parent is None:
					return
				b = BookmarkData(0, '', '', parent.mId, 0)
				self.mSession.openWithCallback(self.cbEditWindow, BookmarkEditWindow, _('Add'), BookmarkEditWindow.BOOKMARK, b, self.mBookmarkManager)
			elif data[1] == 3:
				c = CategoryData(0, '')
				self.mSession.openWithCallback(self.cbEditWindow, BookmarkEditWindow, _('Add'), BookmarkEditWindow.CATEGORY, c, self.mBookmarkManager)
		if strIsEmpty(self.mUrl):
			l = [(_('Direct Input(Bookmark)'),2,), (_('Direct Input(Category)'),3,)]
		else:	l = [(_('Currentpage(Bookmark)'),1,), (_('Direct Input(Bookmark)'),2,), (_('Direct Input(Category)'),3,)]
		self.mSession.openWithCallback(cbGreen, ChoiceBox, title=_("Please choose."), list=l)

	def keyYellow(self):
		data = self["bookmarklist"].getCurrent()[1]
		if self.isCategoryItem():
			self.mSession.openWithCallback(self.cbEditWindow, BookmarkEditWindow, _('Edit'), BookmarkEditWindow.CATEGORY, data, self.mBookmarkManager)
		else:	self.mSession.openWithCallback(self.cbEditWindow, BookmarkEditWindow, _('Edit'), BookmarkEditWindow.BOOKMARK, data, self.mBookmarkManager)

	def keyBlue(self):
		def cbBlue(ret=None):
			if not ret: return
			data = self["bookmarklist"].getCurrent()[1]
			if self.isCategoryItem():
				self.mBookmarkManager.deleteCategory(data.mId)
			else:	self.mBookmarkManager.deleteBookmark(data.mId)
			self.updateBookmarkList()
		if self.isCategoryItem():
			msg = _("Do you want to delete the category and the bookmarks?")
		else:	msg = _("Do you want to delete the bookmark?")
		self.mSession.openWithCallback(cbBlue, MessageBox, msg, MessageBox.TYPE_YESNO, default=True)

	def keyOK(self):
		if self.isCategoryItem(): return

		data = self["bookmarklist"].getCurrent()[1]
		url = data.mUrl.strip()
		if len(url) == 0:
			self.session.open(MessageBox, _("Can't open selected bookmark.\n   - URL data is empty!!"), type = MessageBox.TYPE_INFO)
			return
		mode = data.mType
		if mode:
			lang = language.getLanguage()
			if os.path.exists(vbcfg.MANUALROOT + '/' + lang):
				url = vbcfg.MANUALROOT + '/' + lang + '/main.html'
		self.close((url, mode))

	def keyRed(self):
		self.keyCancel()

	def keyCancel(self):
		self.close()

class BrowserHelpWindow(Screen, HelpableScreen):
	MODE_GLOBAL,MODE_KEYBOARD,MODE_MOUSE = 1,2,3
	skin = """
		<screen name="BrowserHelpWindow" position="center,center" size="600,40" title="Browser Help" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="450,0" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="450,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self["key_red"]    = StaticText(_("Exit"))
		self["key_green"]  = StaticText(_("Global"))
		self["key_yellow"] = StaticText(_("Mouse"))
		self["key_blue"]   = StaticText(_("Keyboard"))

		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions","ColorActions"], {
				"ok"    : self.keyRed,
				"cancel": self.keyRed,
				"red"	: self.keyRed,
				"green" : self.keyGreen,
				"yellow": self.keyYellow,
				"blue"	: self.keyBlue,
			},-2)

		self.showHelpTimer = eTimer()
		self.showHelpTimer.callback.append(self.cbShowHelpTimerClosed)
		self.showHelpTimer.start(500)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Browser Help'))

	def cbShowHelpTimerClosed(self):
		self.showHelpTimer.stop()
		self.setHelpModeActions(self.MODE_GLOBAL)

	def setHelpModeActions(self, _mode=0):
		self.helpList = []
		if _mode == self.MODE_GLOBAL:
			self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions", {
				"cancel" : (self.keyPass, _("Exit the Browser.")),
			})
			self["MenuActions"] = HelpableActionMap(self, "MenuActions", {
				"menu" : (self.keyPass, _("Show the Menu window.")),
			})
			self["ColorActions"] = HelpableActionMap(self, "ColorActions", {
				"green"  : (self.keyPass, _("Enter Key")),
				"yellow" : (self.keyPass, _("Show the Virtual keyboard window.")),
				"blue"   : (self.keyPass, _("Backspace Key")),
			})
			self["EPGSelectActions"] = HelpableActionMap(self, "EPGSelectActions", {
				"info" : (self.keyPass, _("Switch to keyboard/mouse mode.")),
			})

		elif _mode == self.MODE_MOUSE:
			self["DirectionActions"] = HelpableActionMap(self, "DirectionActions", {
				"up"    : (self.keyPass, _("It will move the mouse pointer up.")),
				"down"  : (self.keyPass, _("It will move the mouse pointer down.")),
				"left"  : (self.keyPass, _("It will move the mouse pointer left.")),
				"right" : (self.keyPass, _("It will move the mouse pointer right.")),
			})
			self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions", {
				"ok" : (self.keyPass, _("Left Mouse Button")),
			})
			self["EPGSelectActions"] = HelpableActionMap(self, "EPGSelectActions", {
				"nextBouquet" : (self.keyPass, _("Right Mouse Button")),
				"nextService" : (self.keyPass, _("Left Key")),
				"prevService" : (self.keyPass, _("Right Key")),
			})
		elif _mode == self.MODE_KEYBOARD:
			self["DirectionActions"] = HelpableActionMap(self, "DirectionActions", {
				"up"    : (self.keyPass, _("Up Key")),
				"down"  : (self.keyPass, _("Down Key")),
				"left"  : (self.keyPass, _("Left Key")),
				"right" : (self.keyPass, _("Right Key")),
			})
			self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions", {
				"ok" : (self.keyPass, _("Enter Key")),
			})
			self["EPGSelectActions"] = HelpableActionMap(self, "EPGSelectActions", {
				"nextBouquet" : (self.keyPass, _("PageUp Key")),
				"prevBouquet" : (self.keyPass, _("PageDown Key")),
				"nextService" : (self.keyPass, _("Go to previous page.")),
				"prevService" : (self.keyPass, _("Go to next page.")),
			})

		if _mode > 0:
			self.showHelp()

	def keyPass(self):
		pass

	def keyRed(self):
		self.close()

	def keyGreen(self):
		self.setHelpModeActions(self.MODE_GLOBAL)

	def keyYellow(self):
		self.setHelpModeActions(self.MODE_MOUSE)

	def keyBlue(self):
		self.setHelpModeActions(self.MODE_KEYBOARD)

class Browser(Screen):
	MENU_ITEM_WIDTH  = 150
	MENU_ITEM_HEIGHT = 30
	MENULIST_WIDTH   = 200
	MENULIST_HEIGHT  = 25

	# menulist->position->y : MENU_ITEM_HEIGHT+30
	# menulist->size->x     : MENULIST_WIDTH

	size = getDesktop(0).size()
	WIDTH  = int(size.width())
	HEIGHT = int(size.height())
	skin =	"""
		<screen name="OperaBrowser" position="0,0" size="%(width)d,%(height)d" backgroundColor="transparent" flags="wfNoBorder" title="Opera Browser">
			<widget name="topArea" zPosition="-1" position="0,0" size="1280,60" font="Regular;20" valign="center" halign="center" backgroundColor="#000000" />
			<widget name="menuitemFile" position="30,20" size="150,30" font="Regular;20" valign="center" halign="center" backgroundColor="#000000" foregroundColors="#9f1313,#a08500" />
			<widget name="menuitemTool" position="180,20" size="150,30" font="Regular;20" valign="center" halign="center" backgroundColor="#000000" foregroundColors="#9f1313,#a08500" />
			<widget name="menuitemHelp" position="330,20" size="150,30" font="Regular;20" valign="center" halign="center" backgroundColor="#000000" foregroundColors="#9f1313,#a08500" />
			<widget name="menulist" position="50,60" size="200,150" backgroundColor="#000000" zPosition="10" scrollbarMode="showOnDemand" />
			<widget name="submenulist" position="252,60" size="200,150" backgroundColor="#000000" zPosition="10" scrollbarMode="showOnDemand" />
			<widget name="bottomArea" position="0,%(bottom_pos_y)d" size="%(bottom_size_x)d,80" font="Regular;20" valign="center" halign="center" backgroundColor="#000000" />
		</screen>
		""" % { 'width'  :WIDTH,
			'height' :HEIGHT,
			'bottom_pos_y'  :HEIGHT-80,
			'bottom_size_x' :WIDTH }

	MENULIST_ITEMS = []
	COMMAND_MAP = {}
	def __init__(self, session, url=None, is_webapp=False):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["DirectionActions", "MenuActions", "OkCancelActions"], {
			 "cancel"      : self.keyCancel
			,"ok"          : self.keyOK
			,"left"        : self.keyLeft
			,"right"       : self.keyRight
			,"up"          : self.keyUp
			,"down"        : self.keyDown
			,"menu"        : self.keyMenu
		}, -2)

		self._cb_update_language()

		self.idx_menu = 0
		self.is_browser_opened = False
		self.is_show_top = True
		self.is_show_menu = False

		self._current_url = None
		self._current_title = None

		self["topArea"]    = Label()
		self["bottomArea"] = Label()

		self["menuitemFile"] = MultiColorLabel()
		self["menuitemTool"] = MultiColorLabel()
		self["menuitemHelp"] = MultiColorLabel()

		self.top_menus = [self["menuitemFile"], self["menuitemTool"], self["menuitemHelp"]]

		self["menulist"] = MenuList(self.get_menulist_items(self.idx_menu))
		self["submenulist"] = MenuList(None)

		self.onLayoutFinish.append(self.layoutFinished)

		self._close_timer = eTimer()
		self._close_timer.callback.append(self._cb_stop_browser)

		self.m_url = url
		self.m_webapp = is_webapp
		language.addCallback(self._cb_update_language)

	def layoutFinished(self):
		self["menuitemFile"].setText(_("File"))
		self["menuitemTool"].setText(_("Tools"))
		self["menuitemHelp"].setText(_("Help"))

		self["menulist"].hide()
		self["submenulist"].hide()

		self["bottomArea"].setText(_("Opera Web Browser Plugin v2.0"))
		self.setTitle(_("BrowserMain"))
		self.set_menu_item()
		vbcfg.LOG("Starting Browser")

		if self.m_url is not None:
			self.keyMenu()
			if self.m_webapp:
				self._cb_start_browser(self.m_url, 1, 'YOUTUBETV_OPENURL')
			else:
				self._cb_start_browser(self.m_url, 1)

	def _cb_update_language(self):
		self.MENULIST_ITEMS = [
			[(_('Open Startpage'), None), (_('Open URL'), None), (_('Start/Stop'),None), (_('Exit'), None)],
			[(_('Bookmark'), None), (_('Preference'), None), (_('Position Setup'), None)],
			[(_('About'), None), (_('Help'), None)]
		]
		self.COMMAND_MAP = {}
		self.COMMAND_MAP[_('Open Startpage')] = self._cmd_OpenStartpage
		self.COMMAND_MAP[_('Open URL')] = self._cmd_OpenURL
		self.COMMAND_MAP[_('Start/Stop')] = self._cmd_StartStop
		self.COMMAND_MAP[_('Exit')] = self._cmd_Exit
		self.COMMAND_MAP[_('Bookmark')] = self._cmd_Bookmark
		self.COMMAND_MAP[_('Preference')] = self._cmd_Preference
		self.COMMAND_MAP[_('Position Setup')] = self._cmd_Position
		self.COMMAND_MAP[_('About')] = self._cmd_About
		self.COMMAND_MAP[_('Help')] = self._cmd_Help
		self.COMMAND_MAP[_('Return')] = self._cmd_Return

	def _cb_set_title(self, title=None):
		vbcfg.LOG("page title: %s" % title)
		if title is None:
			return
		self.setTitle(title)

	def _cb_close_window(self):
		self._close_timer.start(1000)

	def _cb_start_browser(self, data=None, mode=0, opcode='BROWSER_OPENURL'):
		if not vbcfg.g_main.check_browser():
			if self.m_url is not None:
				if vbcfg.g_service:
					self.session.nav.playService(vbcfg.g_service)
			return
		vbcfg.LOG("open url: %s %d" % (data, mode))
		if strIsEmpty(data):
			return

		try:
			if self._cb_set_title not in vbcfg.g_main.vbhandler.onSetTitleCB:
				vbcfg.g_main.vbhandler.onSetTitleCB.append(self._cb_set_title)
		except Exception:
			pass

		try:
			if self._cb_close_window not in vbcfg.g_main.vbhandler.onCloseCB:
				vbcfg.g_main.vbhandler.onCloseCB.append(self._cb_close_window)
		except Exception:
			pass

		vbcfg.g_position = vbcfg.getPosition()
		fbClass.getInstance().lock()
		eRCInput.getInstance().lock()

		self.toggle_top()
		ret = VBController.command(opcode, data)
		self._current_url = data
		if ret:
			self.is_browser_opened = True
		else:
			self.is_browser_opened = False
			vbcfg.ERR("Failed to open url: %s" % data)

		vbcfg.g_main.vbhandler.soft_volume = -1

	def _cb_stop_browser(self):
		self._close_timer.stop()

		try:
			if self._cb_set_title in vbcfg.g_main.vbhandler.onSetTitleCB:
				vbcfg.g_main.vbhandler.onSetTitleCB.remove(self._cb_set_title)
		except Exception:
			pass

		try:
			if self._cb_close_window in vbcfg.g_main.vbhandler.onCloseCB:
				vbcfg.g_main.vbhandler.onCloseCB.remove(self._cb_close_window)
		except Exception:
			pass

		self.toggle_top()

		from enigma import gMainDC
		gMainDC.getInstance().setResolution(self.WIDTH, self.HEIGHT)
		vbcfg.setPosition(vbcfg.g_position)

		fbClass.getInstance().unlock()
		eRCInput.getInstance().unlock()
		getDesktop(0).paint()
		self.is_browser_opened = False

		vbcfg.LOG("Stop Browser")
		self.setTitle(_("BrowserMain"))
		if self.m_url is not None:
			self.keyCancel()
			if vbcfg.g_service:
				self.session.nav.playService(vbcfg.g_service)
		else:
			self.keyRight()
			self.keyLeft()

	def _cb_update_bookmark(self, data=None):
		if data is None:
			return
		if not vbcfg.g_main.check_browser():
			message = _("Opera Browser was not running.\nPlease running browser using [File]>[Start/Stop] menu.")
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
			return
		(url, mode) = data
		self._cb_start_browser(url, mode)

	def _cmd_OpenStartpage(self):
		if not vbcfg.g_main.check_browser():
			message = _("Opera Browser was not running.\nPlease running browser using [File]>[Start/Stop] menu.")
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
			return
		mode = 0
		#startpage = 'http://www.google.com'
		try:
			d = BrowserSetting().getData()
			start = d['start']
			mode = d['type']
		except:
			pass
		self._cb_start_browser(start, mode)

	def _cmd_OpenURL(self):
		if not vbcfg.g_main.check_browser():
			message = _("Opera Browser was not running.\nPlease running browser using [File]>[Start/Stop] menu.")
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
			return
		self.session.openWithCallback(self._cb_start_browser, VirtualKeyBoard, title=(_("Please enter URL here")), text='http://')

	def _cmd_StartStop(self):
		if vbcfg.g_main is None:
			return
		vbcfg.g_main.menu_toggle_browser(self.keyMenu())

	def _cmd_Exit(self):
		self.close()

	def _cmd_Bookmark(self):
		url = self._current_url
		if url is None:
			url = ''
		title = self._current_title
		if title is None:
			title = ''
		self.session.openWithCallback(self._cb_update_bookmark, BrowserBookmarkWindow, url, title)

	def _cmd_Preference(self):
		url = self._current_url
		if url is None:
			url = ''
		self.session.open(BrowserPreferenceWindow, url)

	def _cmd_Position(self):
		self.session.open(BrowserPositionWindow)

	def _cmd_About(self):
		self.session.open(MessageBox, _('Opera Web Browser Plugin v2.0'), type = MessageBox.TYPE_INFO)

	def _cmd_Help(self):
		self.session.open(BrowserHelpWindow)

	def _cmd_Return(self):
		self.keyCancel()

	def do_command(self, command):
		try:
			self.COMMAND_MAP[command]()
		except Exception, ErrMsg:
			vbcfg.ERR(ErrMsg)

	def get_menulist_items(self, idx=0):
		l = self.MENULIST_ITEMS[idx]
		if self.is_browser_opened and idx == 0:
			l = [(_("Return"), None)]
		return l

	def set_menu_item(self):
		self["menuitemFile"].setForegroundColorNum(0)
		self["menuitemTool"].setForegroundColorNum(0)
		self["menuitemHelp"].setForegroundColorNum(0)
		self.top_menus[self.idx_menu].setForegroundColorNum(1)

	def toggle_top(self):
		if self.is_show_top:
			self.hide()
		else:
			self.show()
		self.is_show_top = not self.is_show_top

	def toggle_menulist(self):
		if self.is_show_menu:
			self["menulist"].hide()
		else:
			self["menulist"].show()
		self.is_show_menu = not self.is_show_menu

	def toggle_browser(self, url=None, title=None):
		self._current_url = url
		if title is None:
			idx = len(url)
			if idx > 10:
				idx = 10
			title = url[:idx]
		self._current_title = title
		if self._current_url:
			vbcfg.DEBUG(self._current_url)

		self.toggle_top()

		self["menulist"].pageUp()
		self.keyUp()
		self.keyDown()

	def keyCancel(self):
		if self.is_browser_opened:
			fbClass.getInstance().lock()
			eRCInput.getInstance().lock()
			self.toggle_top()

			VBController.command("BROWSER_MENU_CLOSE")
			return
		self._cmd_Exit()

	def keyOK(self):
		if not self.is_show_top:
			self.keyMenu()
			return
		if not self.is_show_menu:
			self.keyDown()
			return
		if self["menulist"].getCurrent()[1] is None:
			self.do_command(self["menulist"].getCurrent()[0])
			return
		self.keyRight()

	def keyLeft(self):
		if self.idx_menu == 0:
			self.idx_menu = 2
		else:
			self.idx_menu = self.idx_menu - 1

		if self.is_show_menu:
			self["menulist"].pageUp()
			self.keyUp()
			self.keyDown()
		self.set_menu_item()

	def keyRight(self):
		if self.idx_menu == 2:
			self.idx_menu = 0
		else:
			self.idx_menu = self.idx_menu + 1

		if self.is_show_menu:
			self["menulist"].pageUp()
			self.keyUp()
			self.keyDown()
		self.set_menu_item()

	def keyUp(self):
		if self.is_show_menu and self["menulist"].getSelectedIndex() == 0:
			self.toggle_menulist()
			return
		self["menulist"].up()

	def keyDown(self):
		if not self.is_show_menu:
			self["menulist"].setList(self.get_menulist_items(self.idx_menu))
			self["menulist"].resize(self.MENULIST_WIDTH, self.MENULIST_HEIGHT*len(self.get_menulist_items(self.idx_menu))+5)
			self["menulist"].move(self.MENU_ITEM_WIDTH*self.idx_menu+50,self.MENU_ITEM_HEIGHT+30)
			self.toggle_menulist()
			return
		self["menulist"].down()

	def keyMenu(self):
		self.toggle_top()

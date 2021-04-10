"""
	Episode List GUI for OnDemand plugin.
	Copyright (C) 2013 andyblac

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# for localized messages
from . import _

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Components.config import config
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	from Tools.Directories import SCOPE_CURRENT_SKIN
from enigma import eSize, ePoint, ePicLoad, eTimer, eListbox, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_TOP, RT_VALIGN_BOTTOM, RT_WRAP
from twisted.web import client
from dns.resolver import Resolver
from os import path as os_path, mkdir as os_mkdir

from httplib import HTTPConnection
import socket
import urllib
import urllib2
import sys

socket.setdefaulttimeout(300) #in seconds

class Rect:
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.w = width
		self.h = height

class MainMenuList(HTMLComponent, GUIComponent):
	def __init__(self):
		GUIComponent.__init__(self)
		self.picload = ePicLoad()
		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildEntry)
		self.onSelChanged = []

	def applySkin(self, desktop, screen):
		rc = GUIComponent.applySkin(self, desktop, screen)
		self.listHeight = self.instance.size().height()
		self.listWidth = self.instance.size().width()
		self.setItemsPerPage()
		return rc

	GUI_WIDGET = eListbox

	def selectionChanged(self):
		for x in self.onSelChanged:
			if x is not None:
				x()

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def pageDown(self):
		self['list'].moveTo(self['list'].instance.pageDown)

	def pageUp(self):
		self['list'].moveTo(self['list'].instance.pageUp)

	def moveTo(self, dir):
		if self.instance is not None:
			self.instance.moveSelection(dir)

	def showArrows(self):
		rowsshown = self.listHeight / self.itemHeight
		if self.totalitems > rowsshown:
			print 'TRUE'
			return 1
		else:
			print 'FALSE'
			return 0

	def setItemsPerPage(self):
		self.itemHeight = 94
		self.itemWidth = 188
		self.l.setItemHeight(self.itemHeight)
		self.instance.resize(eSize(self.itemWidth + 15, (self.listHeight / self.itemHeight) * self.itemHeight))
		self.listHeight = self.instance.size().height()
		self.listWidth = self.instance.size().width()

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.selectionChanged.get().append(self.selectionChanged)
		instance.setContent(self.l)

	def preWidgetRemove(self, instance):
		instance.selectionChanged.get().remove(self.selectionChanged)
		instance.setContent(None)

	def recalcEntrySize(self):
		esize = self.l.getItemSize()
		self.image_rect = Rect(15, 0, self.itemWidth, self.itemHeight)

	def buildEntry(self, name, imagename):
		r1 = self.image_rect

		res = [None]
		
		icon = resolveFilename(SCOPE_PLUGINS, "Extensions/OnDemand/icons/%s.png" % imagename)
		if fileExists(icon):
			self.picload.setPara((r1.w, r1.h, 0, 0, 1, 1, "#00000000"))
			self.picload.startDecode(icon, 0, 0, False)
			pngthumb = self.picload.getData()
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r1.x, r1.y, r1.w, r1.h, pngthumb))

 		return res

	def fillList(self, list):
		self.totalitems = len(list)
		self.l.setList(list)
		self.selectionChanged()

class EpisodeList(HTMLComponent, GUIComponent):
	def __init__(self, iconDefault, showIcon):
		GUIComponent.__init__(self)
		self.picload = ePicLoad()
		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildEntry)
		self.onSelChanged = []

		self.titleFontName = "Regular"
		self.titleFontSize = 26
		self.dateFontName = "Regular"
		self.dateFontSize = 22
		self.descriptionFontName = "Regular"
		self.descriptionFontSize = 18

		self.imagedir = "/tmp/onDemandImg/"
		self.defaultImg = iconDefault
		self.showIcon = showIcon
		
		if not os_path.exists(self.imagedir):
			os_mkdir(self.imagedir)

	def applySkin(self, desktop, screen):
		if self.skinAttributes is not None:
			attribs = []
			for (attrib, value) in self.skinAttributes:
				if attrib == "TileFont":
					font = parseFont(value, ((1,1),(1,1)))
					self.tileFontName = font.family
					self.tileFontSize = font.pointSize
				elif attrib == "DateFont":
					font = parseFont(value, ((1,1),(1,1)))
					self.dateFontName = font.family
					self.dateFontSize = font.pointSize
				elif attrib == "DescriptionFont":
					font = parseFont(value, ((1,1),(1,1)))
					self.descriptionFontName = font.family
					self.descriptionFontSize = font.pointSize
				else:
					attribs.append((attrib,value))
			self.skinAttributes = attribs
		rc = GUIComponent.applySkin(self, desktop, screen)
		self.listHeight = self.instance.size().height()
		self.listWidth = self.instance.size().width()
		self.setItemsPerPage()
		return rc

	GUI_WIDGET = eListbox

	def selectionChanged(self):
		for x in self.onSelChanged:
			if x is not None:
				x()

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def pageDown(self):
		self['list'].moveTo(self['list'].instance.pageDown)

	def pageUp(self):
		self['list'].moveTo(self['list'].instance.pageUp)

	def setCurrentIndex(self, index):
		if self.instance is not None:
			self.instance.moveSelectionTo(index)

	def moveTo(self, dir):
		if self.instance is not None:
			self.instance.moveSelection(dir)

	def setItemsPerPage(self):
		itemHeight = int(self.listHeight / 5)
		self.l.setItemHeight(itemHeight)
		self.instance.resize(eSize(self.listWidth, self.listHeight / itemHeight * itemHeight))

	def setFontsize(self):
		self.l.setFont(0, gFont(self.titleFontName, self.titleFontSize))
		self.l.setFont(1, gFont(self.dateFontName, self.dateFontSize))
		self.l.setFont(2, gFont(self.descriptionFontName, self.descriptionFontSize))

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.selectionChanged.get().append(self.selectionChanged)
		instance.setContent(self.l)
		self.setFontsize()

	def preWidgetRemove(self, instance):
		instance.selectionChanged.get().remove(self.selectionChanged)
		instance.setContent(None)

	def recalcEntrySize(self):
		esize = self.l.getItemSize()
		width = esize.width()
		height = esize.height()
		self.image_rect = Rect(0, 0, 178, height)
		self.name_rect = Rect(15, 0, width - 178 - 35, 30)
		self.descr_rect = Rect(15, 0, width - 178 - 35, height - 30 - 25)
		self.date_rect = Rect(15, 0, width - 178 - 35, 25)

	def buildEntry(self, date, name, short, channel, show, icon, duration, test):
		r1 = self.image_rect
		r2 = self.name_rect
		r3 = self.descr_rect
		r4 = self.date_rect

		res = [None]
		
		# If we don't want to show the icons then shift everything to the left.
		if self.showIcon != 'False':
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r2.x + r1.w, r2.y, r2.w, r2.h, 0, RT_HALIGN_LEFT | RT_VALIGN_TOP, name))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x + r1.w, r3.y + r2.h, r3.w, r3.h, 2, RT_HALIGN_LEFT | RT_VALIGN_TOP | RT_WRAP, short))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r4.x + r1.w, r4.y + r2.h + r3.h, r4.w, r4.h, 1, RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, date))
			if duration:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r4.x + r1.w, r4.y + r2.h + r3.h, r4.w, r4.h, 1, RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, duration))

			self.picload.setPara((r1.w, r1.h, 0, 0, 1, 1, "#00000000"))
			self.picload.startDecode(resolveFilename(SCOPE_PLUGINS, "Extensions/OnDemand/icons/empty.png"), 0, 0, False)
			pngthumb = self.picload.getData()

			if icon:
				tmp_icon = self.getThumbnailName(icon)
				thumbnailFile = self.imagedir + tmp_icon

				if os_path.exists(thumbnailFile):
					self.picload.startDecode(thumbnailFile, 0, 0, False)
					pngthumb = self.picload.getData()
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r1.x, r1.y, r1.w, r1.h, pngthumb))
				else:
					self.picload.startDecode(resolveFilename(SCOPE_PLUGINS, "Extensions/OnDemand/icons/empty.png"), 0, 0, False)
					pngthumb = self.picload.getData()
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r1.x, r1.y, r1.w, r1.h, pngthumb))
			else:
				self.picload.startDecode(resolveFilename(SCOPE_PLUGINS, self.defaultImg), 0, 0, False)
				pngthumb = self.picload.getData()
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r1.x, r1.y, r1.w, r1.h, pngthumb))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, r2.w, r2.h, 0, RT_HALIGN_LEFT | RT_VALIGN_TOP, name))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y + r2.h, r3.w, r3.h, 2, RT_HALIGN_LEFT | RT_VALIGN_TOP | RT_WRAP, short))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r4.x + r1.w, r4.y + r2.h + r3.h, r4.w, r4.h, 1, RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, date))
			if duration:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r4.x, r4.y + r2.h + r3.h, r4.w, r4.h, 1, RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, duration))

		self.picload.setPara((self.l.getItemSize().width(), 2, 0, 0, 1, 1, "#00000000"))
		try:
			self.picload.startDecode(resolveFilename(SCOPE_ACTIVE_SKIN, "div-h.png"), 0, 0, False)
		except:
			self.picload.startDecode(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/div-h.png"), 0, 0, False)
		pngthumb = self.picload.getData()
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 0, self.l.getItemSize().height() - 2, self.l.getItemSize().width(), 2, pngthumb))

 		return res

	def fillEpisodeList(self, mediaList):
		for x in mediaList:
			if x[5]:
				tmp_icon = self.getThumbnailName(x[5])
				thumbnailFile = self.imagedir + tmp_icon
				if not os_path.exists(thumbnailFile):
					client.downloadPage(x[5], thumbnailFile)
			
		self.l.setList(mediaList)
		self.selectionChanged()

	def getThumbnailName(self, x):
		try:
			temp_icon = str(x)
			icon_name = temp_icon.rsplit('/',1)
			
			# OUG streams doesn't handle thumbnals well
			if icon_name[1][:5] == "nicam":
				icon_name = temp_icon.rsplit('/',2)
				return str(icon_name[1]) + ".jpg"
			else:				
				return str(icon_name[1])
		except (Exception) as exception:
			print "getThumbnailName: No image found: ", exception, " for: ", x
			return ''

###########################################################################
class StreamsThumbCommon(Screen):

	TIMER_CMD_START = 0
	TIMER_CMD_VKEY = 1

	def __init__(self, session, action, value, url, name):
		self.skin = """
				<screen position="0,0" size="e,e" flags="wfNoBorder" >
					<widget name="lab1" position="0,0" size="e,e" font="Regular;24" halign="center" valign="center" transparent="0" zPosition="5" />
					<widget source="Title" render="Label" position="20,0" size="e,50" font="Regular;32" />
					<widget name="list" position="0,50" size="e,e-50" scrollbarMode="showOnDemand" transparent="1" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)
		self.skinName = [name, "StreamsThumbCommon"]

		self['lab1'] = Label(_('Wait please while gathering data...'))

		self.cbTimer = eTimer()
		self.cbTimer.callback.append(self.timerCallback)

		self.cmd = action
		self.url = url
		self.title = value
		self.timerCmd = self.TIMER_CMD_START

		self.tmplist = []
		self.mediaList = []

		self.refreshTimer = eTimer()
		self.refreshTimer.timeout.get().append(self.refreshData)
		self.hidemessage = eTimer()
		self.hidemessage.timeout.get().append(self.hidewaitingtext)

		self.imagedir = "/tmp/onDemandImg/"
		if (os_path.exists(self.imagedir) != True):
			os_mkdir(self.imagedir)

		self['list'] = EpisodeList(self.defaultImg, self.showIcon)
		self.updateMenu()

		self["actions"] = ActionMap(["SetupActions", "DirectionActions"],
		{
			"up": self.key_up,
			"down": self.key_down,
			"left": self.key_left,
			"right": self.key_right,
			"ok": self.go,
			"cancel": self.exit,
		}, -1)
		self.onLayoutFinish.append(self.layoutFinished)
		self.cbTimer.start(10)

	def updateMenu(self):
		self['list'].recalcEntrySize()
		self['list'].fillEpisodeList(self.mediaList)
		self.hidemessage.start(12)
		self.refreshTimer.start(4000)

	def hidewaitingtext(self):
		self.hidemessage.stop()
		self['lab1'].hide()

	def refreshData(self, force=False):
		self.refreshTimer.stop()
		self['list'].fillEpisodeList(self.mediaList)

	def key_up(self):
		self['list'].moveTo(self['list'].instance.moveUp)

	def key_down(self):
		self['list'].moveTo(self['list'].instance.moveDown)

	def key_left(self):
		self['list'].moveTo(self['list'].instance.pageUp)

	def key_right(self):
		self['list'].moveTo(self['list'].instance.pageDown)

	def exit(self):
		self.close()

	def timerCallback(self):
		self.cbTimer.stop()
		if self.timerCmd == self.TIMER_CMD_START:
			self.setupCallback(self.cmd)
		elif self.timerCmd == self.TIMER_CMD_VKEY:
			self.session.openWithCallback(self.keyboardCallback, VirtualKeyBoard, title=(_("Search term")), text="")

	def mediaProblemPopup(self, error):
		self.session.openWithCallback(self.close, MessageBox, _(error), MessageBox.TYPE_ERROR, timeout=5, simple=True)

###########################################################################
class MyHTTPConnection(HTTPConnection):
	def connect(self):
		try:
			primaryDNS = ".".join("%d" % d for d in config.ondemand.PrimaryDNS.value)
			myDNS = []
			myDNS.append(primaryDNS)
			resolver = Resolver()
			resolver.nameservers = myDNS  #DNS Now coming from OnDemand Settings
			answer = resolver.query(self.host,'A')
			self.host = answer.rrset.items[0].address
			self.sock = socket.create_connection((self.host, self.port))
		except (Exception) as exception:
			print "MyHTTPConnection: Failed to Connect to: ", primaryDNS, " , error: ", exception

			try:
				secondaryDNS = str(config.ondemand.SecondaryDNS.value)

				if secondaryDNS != str(config.ondemand.SecondaryDNS.default):
					secondaryDNS = ".".join("%d" % d for d in config.ondemand.SecondaryDNS.value)
					myDNS = []
					myDNS.append(secondaryDNS)
					resolver = Resolver()
					resolver.nameservers = myDNS  #DNS Now coming from OnDemand Settings
					answer = resolver.query(self.host,'A')
					self.host = answer.rrset.items[0].address
					self.sock = socket.create_connection((self.host, self.port))

			except (Exception) as exception:
				print "MyHTTPConnection: Failed to Connect to: ", secondaryDNS, " , error: ", exception

class MyHTTPHandler(urllib2.HTTPHandler):
	def http_open(self, req):
		return self.do_open(MyHTTPConnection, req)

###########################################################################	   
class MoviePlayer(MP_parent):
	def __init__(self, session, service, slist=None, lastservice=None):
		MP_parent.__init__(self, session, service, slist, lastservice)

	def leavePlayer(self):
		self.close()

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		self.close()

###########################################################################	   
class RTMP:
	def __init__(self, rtmp, tcUrl=None, auth=None, app=None, playPath=None, swfUrl=None, swfVfy=None, pageUrl=None, live=None, socks=None, port=None):

		self.rtmp = rtmp
		self.tcUrl = tcUrl
		self.auth = auth
		self.app = app
		self.playPath = playPath
		self.swfUrl = swfUrl
		self.swfVfy = swfVfy
		self.pageUrl = pageUrl
		self.live = live
		self.socks = socks
		self.port = port

		self.rtmpdumpPath = None
		self.downloadFolder = None

	# hostname:port
	def setProxyString(self, string):
		self.socks = string

	def setDownloadDetails(self, rtmpdumpPath, downloadFolder):
		self.rtmpdumpPath = rtmpdumpPath
		self.downloadFolder = downloadFolder

	def getDumpCommand(self):
		if self.rtmpdumpPath is None or self.rtmpdumpPath == '':
			# rtmpdump path is not set
			raise exception

		args = [self.rtmpdumpPath]
		args.append(getParameters())
		command = ' '.join(args)

		return command

	def getSimpleParameters(self):
		if self.downloadFolder is None or self.downloadFolder == '':
			# Download Folder is not set
			raise exception

		if self.rtmp is None or self.rtmp == '':
			# rtmp url is not set
			raise exception

		parameters = {}

		parameters[u"url"] = self.rtmp
		parameters[u"download_path"] = self.downloadFolder

		if self.auth is not None:
			parameters[u"auth"] = self.auth

		if self.app is not None:
			parameters[u"app"] = self.app

		if self.playPath is not None:
			parameters[u"playpath"] = self.playPath

		if self.tcUrl is not None:
			parameters[u"tcUrl"] = self.tcUrl

		if self.swfUrl is not None:
			parameters[u"swfUrl"] = self.swfUrl

		if self.swfVfy is not None:
			parameters[u"swfVfy"] = self.swfVfy

		if self.pageUrl is not None:
			parameters[u"pageUrl"] = self.pageUrl

		if self.live is not None and self.live is not False:
			parameters[u"live"] = u"true"

		if self.socks is not None:
			parameters[u"socks"] = self.socks

		if self.port is not None:
			parameters[u"port"] = self.port

		return parameters

	def getParameters(self):
		if self.downloadFolder is None or self.downloadFolder == '':
			# Download Folder is not set
			raise exception

		if self.rtmp is None or self.rtmp == '':
			# rtmp url is not set
			raise exception

		args = [u"--rtmp", u'"%s"' % self.rtmp, u"-o", u'"%s"' % self.downloadFolder]

		if self.auth is not None:
			args.append(u"--auth")
			args.append(u'"%s"' % self.auth)

		if self.app is not None:
			args.append(u"--app")
			args.append(u'"%s"' % self.app)

		if self.playPath is not None:
			args.append(u"--playpath")
			args.append(u'"%s"' % self.playPath)

		if self.swfUrl is not None:
			args.append(u"--swfUrl")
			args.append(u'"%s"' % self.swfUrl)

		if self.tcUrl is not None:
			args.append(u"--tcUrl")
			args.append(u'"%s"' % self.tcUrl)

		if self.swfVfy is not None:
			args.append(u"--swfVfy")
			args.append(u'"%s"' % self.swfVfy)

		if self.pageUrl is not None:
			args.append(u"--pageUrl")
			args.append(u'"%s"' % self.pageUrl)

		if self.live is not None and self.live is not False:
			args.append(u"--live")

		if self.socks is not None:
			args.append(u"--socks")
			args.append(u'"%s"' % self.socks)

		if self.port is not None:
			args.append(u"--port")
			args.append(u'%d' % self.port)

		parameters = u' '.join(args)

		return parameters

	def getPlayUrl(self):
		if self.rtmp is None or self.rtmp == '':
			# rtmp url is not set
			raise exception

		if self.port is None:
			args = [u"%s" % self.rtmp]
		else:
			try:
				# Replace "rtmp://abc.def.com:default_port/ghi/jkl" with "rtmp://abc.def.com:port/ghi/jkl"
				match = re.search("(.+//[^/]+):\d+(/.*)", self.rtmp, re.DOTALL | re.IGNORECASE)
				if match is None:
					# Replace "rtmp://abc.def.com/ghi/jkl" with "rtmp://abc.def.com:port/ghi/jkl"
					match = re.search("(.+//[^/]+)(/.*)", self.rtmp, re.DOTALL | re.IGNORECASE)

				args = [u"%s:%d%s" % (match.group(1), self.port, match.group(2))]
			except (Exception) as exception:
				args = [u"%s" % self.rtmp]

		if self.auth is not None:
			args.append(u"auth=%s" % self.auth)

		if self.app is not None:
			args.append(u"app=%s" % self.app)

		if self.playPath is not None:
			args.append(u"playpath=%s" % self.playPath)

		if self.swfUrl is not None:
			args.append(u"swfurl=%s" % self.swfUrl)

		if self.tcUrl is not None:
			args.append(u"tcUrl=%s" % self.tcUrl)

		if self.swfVfy is not None:
			args.append(u"swfurl=%s" % self.swfVfy)
			args.append(u"swfvfy=true")

		if self.pageUrl is not None:
			args.append(u"pageurl=%s" % self.pageUrl)

		if self.live is not None and self.live is not False:
			args.append(u"live=true")

		if self.socks is not None:
			args.append(u"socks=%s" % self.socks)

		playURL = u' '.join(args)

		return playURL

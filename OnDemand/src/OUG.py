# -*- coding: utf-8 -*-
"""
    OpenUitzendingGemist - Enigma2 Video Plugin
    Copyright (C) 2013 mcquaim

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

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.config import config
from Components.MenuList import MenuList
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText
from enigma import eServiceReference, eTimer, iPlayableService, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_WRAP, RT_VALIGN_TOP, ePicLoad
from ServiceReference import ServiceReference
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek
from Screens.MessageBox import MessageBox
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from urllib2 import Request, URLError, HTTPError, urlopen as urlopen2
from httplib import HTTPException
from os import path as os_path, remove as os_remove, mkdir as os_mkdir
import socket
from datetime import date, timedelta

from CommonModules import EpisodeList, MoviePlayer, MyHTTPConnection, MyHTTPHandler, StreamsThumbCommon

#=========================================================================================


def wgetUrl(target):
	std_headers = {
		'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'en-us,en;q=0.5',
	}
	outtxt = Request(target, None, std_headers)
	try:
		#outtxt = urlopen2(target, timeout = 5).read()
		outtxt = urlopen2(target).read()
	except (URLError, HTTPException, socket.error):
		return ''
	return outtxt

#=========================================================================================


class OpenUgSetupScreen(Screen):
	def __init__(self, session, action, value):
		self.skin = """
				<screen position="center,center" size="400,320" title="">
					<widget name="menu" position="10,10"   size="e-20,180" scrollbarMode="showOnDemand" />
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

		self.imagedir = '/tmp/onDemandImg/'

		self["info"] = Label(_("Open Uitzending Gemist\n\nBased on Xtrend code"))

		self.mmenu = []
		self.mmenu.append((_("UG Recently added"), 'recent'))
		self.mmenu.append((_("UG Popular"), 'pop'))
		self.mmenu.append((_("UG A-Z"), 'atotz'))
		self.mmenu.append((_("UG Search"), 'search'))
		self.mmenu.append((_("RTL XL A-Z"), 'rtl'))
		self.mmenu.append((_("RTL XL Gemist"), 'rtlback'))
		self["menu"] = MenuList(self.mmenu)

		self.onLayoutFinish.append(self.layoutFinished)

#=========================================================================================
	def loadUrl(self, url, sub):
		try:
			lines = open(url).readlines()
			for x in lines:
				if sub in x.lower():
					return True
		except:
			return False
		return False

#=========================================================================================
	def layoutFinished(self):
		self.setTitle('Open Uitzending Gemist')

#=========================================================================================
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
				self.session.open(OpenUg, selection[1])
			elif selection[1] == 'rtl':
				self.session.open(OpenUg, selection[1])
			elif selection[1] == 'rtlback':
				self.session.open(DaysBackScreen)

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

#=========================================================================================


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

		self.mmenu = []
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

###########################################################################


class OpenUg(StreamsThumbCommon):
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

	UG_BASE_URL = "http://hbbtv.distributie.publiekeomroep.nl"
	HBBTV_UG_BASE_URL = UG_BASE_URL + "/ug/ajax/action/"
	STAGING_UG_BASE_URL = "http://staging.hbbtv.distributie.publiekeomroep.nl/"
	RTL_BASE_URL = "http://rtl.ksya.net/"

	def __init__(self, session, action, value=None, url=None):
		self.defaultImg = "Extensions/OnDemand/icons/OUG.png"
		self.showIcon = str(config.ondemand.ShowImages.value)
		self.screenName = "OUGStreamsThumbCommon"
		StreamsThumbCommon.__init__(self, session, action, value, url, self.screenName)

		self.isAtotZ = False
		self.isRtl = False
		self.isRtlBack = False
		self.level = self.UG_LEVEL_ALL

	def layoutFinished(self):
		self.setTitle("Open Uitzending Gemist")

	def exit(self):
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

	def setupCallback(self, retval=None):
		if retval == 'cancel' or retval is None:
			return
		self.isAtotZ = False
		self.isRtl = False
		self.isRtlBack = False

		if retval == 'recent':
			self.level = self.UG_LEVEL_SERIE
			self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "archive_week/protocol/html")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()

		elif retval == 'pop':
			self.level = self.UG_LEVEL_SERIE
			self.getMediaData(self.mediaList, self.HBBTV_UG_BASE_URL + "popular/protocol/html")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()

		elif retval == 'atotz':
			self.isAtotZ = True
			self.level = self.UG_LEVEL_ALL
			self.getMediaDataAlph(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z/a2zActiveIndex/0/protocol/html")
			self.getMediaDataAlph(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z/a2zActiveIndex/1/protocol/html")
			self.getMediaDataAlph(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z/a2zActiveIndex/2/protocol/html")
			self.getMediaDataAlph(self.mediaList, self.HBBTV_UG_BASE_URL + "a2z/a2zActiveIndex/3/protocol/html")
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			self.updateMenu()

		elif retval == 'search':
			self.timerCmd = self.TIMER_CMD_VKEY
			self.cbTimer.start(10)

		elif retval == 'rtl':
			self.isRtl = True
			self.level = self.UG_LEVEL_ALL
			self.getRTLMediaData(self.mediaList)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			else:
				self.updateMenu()
		else:
			self.isRtl = True
			self.isRtlBack = True
			self.level = self.UG_LEVEL_SERIE
			self.getRTLMediaDataBack(self.mediaList, retval)
			if len(self.mediaList) == 0:
				self.mediaProblemPopup("No Episodes Found!")
			else:
				self.updateMenu()

	def keyboardCallback(self, callback=None):
		if callback is not None and len(callback):
			self.isRtl = False
			self.level = self.UG_LEVEL_SERIE
			self.getMediaData(self.mediaList, self.STAGING_UG_BASE_URL + "ug/ajax/action/search/protocol/html/searchString/" + callback)
			self.updateMenu()
			if len(self.mediaList) == 0:
				self.session.openWithCallback(self.close, MessageBox, _("No items matching your search criteria were found"), MessageBox.TYPE_ERROR, timeout=5, simple=True)
		else:
			self.close()

	def go(self):
		currSel = self["list"].l.getCurrentSelection()
		selIndex = self.mediaList.index(currSel)

		if len(self.mediaList) == 0 or selIndex > len(self.mediaList) - 1:
			return

		if self.isRtl:
			print "go: isRtl: ", self.isRtl
			if self.level == self.UG_LEVEL_ALL:
				tmp = self.mediaList[selIndex][self.UG_STREAMURL]
				self.getRTLSerie(self.mediaList, tmp)
				self.level = self.UG_LEVEL_SERIE
				self.updateMenu()

			elif self.level == self.UG_LEVEL_SERIE:
				tmp = self.getRTLStream(self.mediaList[selIndex][self.UG_STREAMURL])

				if tmp:
					myreference = eServiceReference(4097, 0, tmp)
					myreference.setName(self.mediaList[selIndex][self.UG_PROGNAME])
					lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
					self.session.open(MoviePlayer, myreference, None, lastservice)
				else:
					self.mediaProblemPopup("Sorry, unable to find playable stream!")

		else:
			if self.level == self.UG_LEVEL_ALL:
				if self.mediaList[selIndex][self.UG_SERIE]:
					tmp = self.mediaList[selIndex][self.UG_STREAMURL]
					self.isRtl = False
					self.level = self.UG_LEVEL_SERIE
					self.getMediaData(self.mediaList, self.STAGING_UG_BASE_URL + "ug/ajax/action/a2z-serie/a2zSerieId/" + tmp)
					self.updateMenu()
				else:
					self.doUGPlay(selIndex)
			else:
				self.doUGPlay(selIndex)

#=========================================================================================
	def doUGPlay(self, selIndex):
		out = wgetUrl(self.STAGING_UG_BASE_URL + "streams/video/pr_id/" + self.mediaList[selIndex][self.UG_STREAMURL])

		if out:
			myreference = eServiceReference(4097, 0, out.split('stream_link":"')[1].split('\",')[0].replace('\/', '/'))
			myreference.setName(self.mediaList[selIndex][self.UG_PROGNAME])
			lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			self.session.open(MoviePlayer, myreference, None, lastservice)
		else:
			self.mediaProblemPopup("Sorry, unable to find playable stream!")

#=========================================================================================
	def getRTLStream(self, url):
		data = wgetUrl(self.RTL_BASE_URL + url)
		data = data.split('\n')
		state = 0
		url = ''
		name = ''
		icon = ''
		for line in data:
			if ".mp4" in line:
				tmp = "<source src=\""
				if tmp in line:
					url = line.split("src=\"")[1].split("\"")[0]
				return url
		return ''

#=========================================================================================
	def getRTLSerie(self, weekList, url):

		data = wgetUrl(self.RTL_BASE_URL + url)

		# Only attempt to parse the data if anything returned.
		if data:
			data = data.split('\n')

			state = 0
			name = ''
			short = ''
			icon = ''
			stream = ''
			date = ''
			channel = ''
			duration = ''

			for line in data:
				if "<li>" in line:
					state = 1
				if state == 1:
					tmp = "<a href=\"video"
					if tmp in line:
						tmp = "<a href=\""
						stream = line.split(tmp)[1].split('\">')[0]

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						tmp = "<img class=\"thumbnail\" src=\""
						if tmp in line:
							icon = line.split(tmp)[1].split('\" ')[0]
					else:
						icon = ''

					tmp = "<div class=\"stationlogo\""
					if tmp in line:
						lineTmp = line.split(tmp)[1].split('</div>')[0]
						channelTmp = lineTmp.rsplit('>', 1)
						channel = channelTmp[1]

					tmp = "<span class=\"title\">"
					if tmp in line:
						name = line.split(tmp)[1].split('</span>')[0]
						name = checkUnicode(name)
						state = 2

				elif state == 2:
					if '<span class=\"extra_info\">' in line:
						continue
					date = _("Added: ") + str(line.split("<br />")[0].lstrip())
					state = 3

				elif state == 3:
					tmp = "<span class=\"small\">"
					if tmp in line:
						short = line.split(tmp)[1].split('</span>')[0]
						short = checkUnicode(short)

					weekList.append((date, name, short, channel, stream, icon, duration, False))
					state = 0

#=========================================================================================
	def getRTLMediaData(self, weekList):

		url = self.RTL_BASE_URL + "serieslist.php"
		data = wgetUrl(url)

		# Only attempt to parse the data if anything returned.
		if data:
			data = data.split('\n')

			state = 0
			name = ''
			short = ''
			icon = ''
			stream = ''
			date = ''
			channel = ''
			duration = ''

			for line in data:
				if "<li" in line:
					tmp = "<a href=\""
					if tmp in line:
						stream = line.split(tmp)[1].split('\">')[0]

					tmp = "<span class=\"title\">"
					if tmp in line:
						name = line.split(tmp)[1].split("</span>")[0]
						name = checkUnicode(name)

						ignore = False
						for x in weekList:
							if stream == x[self.UG_STREAMURL] and icon == x[self.UG_ICON]:
								ignore = True
								break
						if ignore is False:
							weekList.append((date, name, short, channel, stream, icon, duration, True))

#=========================================================================================
	def getRTLMediaDataBack(self, weekList, days):

		url = self.RTL_BASE_URL + "?daysback=" + '%d' % (days)
		data = wgetUrl(url)

		# Only attempt to parse the data if anything returned.
		if data:
			data = data.split('\n')
			state = 0
			name = ''
			short = ''
			icon = ''
			stream = ''
			date = ''
			channel = ''
			duration = ''

			for line in data:
				if "<li>" in line:
					state = 1
				if state == 1:
					if "<a href=\"video" in line:
						stream = line.split("<a href=\"")[1].split('\" ')[0]

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						tmp = "<img class=\"thumbnail\" src=\""
						if tmp in line:
							icon = line.split(tmp)[1].split('\" ')[0]
					else:
						icon = ''

					tmp = "<div class=\"stationlogo\""
					if tmp in line:
						lineTmp = line.split(tmp)[1].split('</div>')[0]
						channelTmp = lineTmp.rsplit('>', 1)
						channel = channelTmp[1]

					tmp = "<span class=\"title\">"
					if tmp in line:
						name = line.split(tmp)[1].split("</span>")[0]
						name = checkUnicode(name)
						if "<br />" in line:
							short = line.split("<br />")[1]
							short = checkUnicode(short)
						state = 2

				elif state == 2:
					tmp = "<span class=\"extra_info\">"
					if tmp in line:
						state = 3

				elif state == 3:
					date = _("Time: ") + str(line[:5])
					weekList.append((date, name, short, channel, stream, icon, duration, False))
					state = 0

#=========================================================================================
	def getMediaData(self, weekList, url):
		data = wgetUrl(url)

		# Only attempt to parse the data if anything returned.
		if data:
			state = 0
			short = ''
			name = ''
			date = ''
			stream = ''
			channel = ''
			icon = ''
			duration = ''

			data = data.split("\n")

			for line in data:
				if state == 0:
					if "<div class=\"menuEntry\">" in line:
						state = 1
						short = ''
						name = ''
						date = ''
						stream = ''
						icon = ''

				elif state == 1:
					tmp = "<div class=\"programDetails\" id=\""
					if tmp in line:
						stream = line.split(tmp)[1].split('\">')[0]

					tmp = "<h3>"
					if tmp in line:
						name = line.split(tmp)[1].split("</h3>")[0]
						name = checkUnicode(name)

					tmp = "<div class='short'>"
					if tmp in line:
						short = line.split(tmp)[1].split("</div>")[0]
						short = checkUnicode(short)

					tmp = "<div class='datum'>"
					if tmp in line and date == '':
						date = _("Added: ") + str(line.split(tmp)[1].split("</div>")[0])
						channel = date[-3:]

					# Only set the Icon if they are enabled
					if self.showIcon == 'True':
						tmp = "<img class='thumbnail' src='"
						if tmp in line:
							icon = line.split(tmp)[1].split("\'/>")[0]
							if "http://" not in icon:
								icon_tmp = self.UG_BASE_URL
								icon = icon_tmp + icon
					else:
						icon = ''

					if self.showIcon == 'True':
						if "</div>" in line[:6] and date and name and short and icon:
							weekList.append((date, name, short, channel, stream, icon, duration, False))
							state = 0
					else:
						if "</div>" in line[:6] and date and name and short:
							weekList.append((date, name, short, channel, stream, icon, duration, False))
							state = 0

#=========================================================================================
	def getMediaDataAlph(self, weekList, url):

		data = wgetUrl(url)

		# Only attempt to parse the data if anything returned.
		if data:
			state = 0
			short = ''
			name = ''
			date = ''
			stream = ''
			channel = ''
			icon = ''
			serieid = ''
			duration = ''

			data = data.split('\n')

			for line in data:
				if "<div class=\"menuItem" in line:
					serieid = ''
					short = ''
					name = ''
					date = ''
					stream = ''
					channel = ''
					icon = ''
					if "id=" in line:
						serieid = line.split("id=\"")[1].split('\"')[0]
					state = 1

				if state == 1:
					tmp = "<h3>"
					if tmp in line and name == '':
						name = line.split(tmp)[1].split("</h3>")[0]
						name = checkUnicode(name)

					tmp = "<div class=\"programDetails\" id=\""
					if tmp in line and stream == '':
						stream = line.split(tmp)[1].split("\"")[0]

					if serieid == '':
						# Only set the Icon if they are enabled
						if self.showIcon == 'True':
							tmp = "<img class='thumbnail' src='"
							if tmp in line:
								icon = line.split(tmp)[1].split('\'/>')[0]
								if "http://" not in icon:
									icon_tmp = self.UG_BASE_URL
									icon = icon_tmp + icon
						else:
							icon = ''

						tmp = "<div class='datum'>"
						if tmp in line and date == '':
							date = _("Added: ") + str(line.split(tmp)[1].split("</div>")[0])
							channel = date[-3:]

						tmp = "<div class='short'>"
						if tmp in line:
							short = line.split(tmp)[1].split("</div>")[0]
							short = checkUnicode(short)
					else:
						# Only set the Icon if they are enabled
						if self.showIcon == 'True':
							tmp = "<div class='thumbHolder'>"
							if tmp in line:
								icon = line.split("url(\"")[1].split("\"")[0]
								if "http://" not in icon:
									icon_tmp = self.UG_BASE_URL
									icon = icon_tmp + icon
						else:
							icon = ''

					isdone = False
					if self.showIcon == 'True':
						if serieid == '':
							if name and stream and icon and date:
								isdone = True
						else:
							if name and serieid and icon:
								isdone = True
					else:
						if serieid == '':
							if name and stream and date:
								isdone = True
						else:
							if name and serieid:
								isdone = True

					if isdone:
						if serieid != '':
							weekList.append((date, name, short, channel, serieid, icon, duration, True))
						else:
							weekList.append((date, name, short, channel, stream, icon, duration, False))
						state = 0

#=========================================================================================


def checkUnicode(value, **kwargs):
	stringValue = value
	stringValue = stringValue.replace('&#39;', '\'')
	stringValue = stringValue.replace('&amp;', '&')
	return stringValue

#=========================================================================================


def Plugins(**kwargs):
	return [PluginDescriptor(name="Open uitzending gemist", description=_("Watch uitzending gemist"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]

#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import datetime
from socket import error as socketerror
from base64 import b64encode, b64decode
from RecordTimer import RecordTimerEntry
from time import mktime, strftime, gmtime, localtime
from os import remove, linesep, rename, path
from re import findall, match, search, split, sub, S, compile
from Tools.Directories import fileExists, isPluginInstalled
from twisted.web import client, error
from twisted.web.client import getPage, downloadPage
from six import PY2, ensure_binary, ensure_str
from six.moves.http_client import HTTPException
from six.moves.urllib.error import URLError, HTTPError
from six.moves.urllib.parse import unquote_plus, urlencode, parse_qs
from six.moves.urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler, HTTPHandler, HTTPCookieProcessor
from Components.Input import Input
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Slider import Slider
from Components.Sources.List import List
from Components.MenuList import MenuList
from Components.FileList import FileList
from Components.ScrollLabel import ScrollLabel
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, configfile, ConfigSubsection, getConfigListEntry
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest, MultiContentEntryProgress
from enigma import ePicLoad, eConsoleAppContainer, eListboxPythonMultiContent, eListbox, eEPGCache, eServiceCenter, eServiceReference, eTimer, gFont, loadJPG, loadPNG, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP, BT_SCALE, BT_KEEP_ASPECT_RATIO, BT_HALIGN_CENTER, BT_VALIGN_CENTER
from Screens.Screen import Screen
from Screens.Console import Console
from Screens.ChoiceBox import ChoiceBox
from Screens.TimerEntry import TimerEntry
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from ServiceReference import ServiceReference
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.TimerEdit import TimerSanityConflict
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.ChannelSelection import ChannelSelection
from .util import applySkinVars, PLUGINPATH, PICPATH, ICONPATH, serviceDB, BlinkingLabel, ItemList, makeWeekDay, printStackTrace, channelDB, readSkin, DESKTOP_WIDTH, DESKTOP_HEIGHT, SCALE, FULLHD
from .parser import transCHANNEL, shortenChannel, transHTML, cleanHTML, parsedetail, fiximgLink, parsePrimeTimeTable, parseTrailerUrl, buildTVTippsArray, parseNow, NEXTPage1, NEXTPage2

try:
	from cookielib import MozillaCookieJar
except Exception:
	from http.cookiejar import MozillaCookieJar

RELEASE = 'V6.7'
NOTIMER = '\nTimer nicht möglich:\nKeine Service Reference vorhanden, der ausgewählte Sender wurde nicht importiert.'
NOEPG = 'Keine EPG Informationen verfügbar'
ALPHA = '/proc/stb/video/alpha' if fileExists('/proc/stb/video/alpha') else None


def findPicon(sref, folder):
	sref = sref + 'FIN'
	sref = sref.replace(':', '_')
	sref = sref.replace('_FIN', '')
	sref = sref.replace('FIN', '')
	pngname = folder + sref + '.png'
	if fileExists(pngname):
		return pngname


def showPic(pixmap, picpath):
	if fileExists(picpath):
		try:
			pixmap.instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
			pixmap.instance.setPixmapFromFile(picpath)
		except:
			currPic = loadJPG(picpath)
			pixmap.instance.setScale(1)
			pixmap.instance.setPixmap(currPic)
		pixmap.show()


def getEPGText():
	try:
		NOEPGTIME = 'Noch keine EPG Informationen verfügbar\n\nEPG Vorschauzeit: %s Tage\nEPG Vorhaltezeit: %s Stunden' % (
			str(config.epg.maxdays), str(config.epg.histminutes))
		return NOEPGTIME
	except (KeyError, NameError):
		return NOEPG


def Bouquetlog(info, wert='', debug=False):
	if debug and not config.plugins.tvspielfilm.debuglog.value:
		return
	if config.plugins.tvspielfilm.logtofile.value:
		try:
			with open('/home/root/logs/tvspielfilm.log', 'a') as f:
				f.write(info)
		except IOError:
			TVSlog('Logging-Error:', IOError)
	else:
		print('[TVSpielfilm] %s %s' % (str(info), str(wert)))


def TVSlog(info, wert='', debug=False):
	if debug and not config.plugins.tvspielfilm.debuglog.value:
		return
	if config.plugins.tvspielfilm.logtofile.value:
		try:
			with open('/home/root/logs/tvspielfilm.log', 'a') as f:
				f.write(strftime('%H:%M:%S') + ' %s %s\r\n' % (str(info), str(wert)))
		except IOError:
			TVSlog('Logging-Error:', IOError)
	else:
		print('[TVSpielfilm] %s %s' % (str(info), str(wert)))


class tvAllScreen(Screen):

	def __init__(self, session, skin=None, dic=None, scale=False):
		w = DESKTOP_WIDTH - (80 * SCALE)
		mw = w - (20 * SCALE)
		h = DESKTOP_HEIGHT - (120 * SCALE) - 40
		mh = h - 60
		self.menuwidth = mw
		if dic == None:
			dic = {}
		dic['picpath'] = PICPATH
		if skin:
			self.skin = applySkinVars(skin, dic)
		Screen.__init__(self, session)
		self.fontlarge = True if config.plugins.tvspielfilm.font_size.value == 'large' else False
		self.fontsmall = True if config.plugins.tvspielfilm.font_size.value == 'normal' else False
		self.baseurl = 'https://www.tvspielfilm.de'
		self.servicefile = PLUGINPATH + 'db/service.references'

	def hideScreen(self):
		global HIDEFLAG
		if ALPHA:
			if HIDEFLAG:
				HIDEFLAG = False
				for count in range(40, -1, -1):
					with open(ALPHA, 'w') as f:
						f.write('%i' % (config.av.osd_alpha.value * count / 40))
			else:
				HIDEFLAG = True
				for count in range(41):
					with open(ALPHA, 'w') as f:
						f.write('%i' % (config.av.osd_alpha.value * count / 40))

	def zapUp(self):
		if InfoBar and InfoBar.instance:
			InfoBar.zapUp(InfoBar.instance)

	def zapDown(self):
		if InfoBar and InfoBar.instance:
			InfoBar.zapDown(InfoBar.instance)

	def picReturn(self):
		pass

	def makeTimerDB(self):
		timerxml = open('/etc/enigma2/timers.xml').read()
		timers = findall('<timer begin="(.*?)" end=".*?" serviceref="(.*?)"', timerxml)
		with open(PLUGINPATH + 'db/timer.db', 'w') as f:
			self.timer = []
			for timer in timers:
				timerstart = int(timer[0]) + int(config.recording.margin_before.value) * 60
				timerday = strftime('%Y-%m-%d', localtime(timerstart))
				timerhour = strftime('%H:%M', localtime(timerstart))
				self.timer.append(timerday + ':::' + timerhour + ':::' + timer[1])
			f.write('\n'.join(self.timer))

	def getFill(self, text):
		return '______________________________________\n%s' % text


class tvAllScreenFull(tvAllScreen):
	skin = '''<screen position="0,0" size="{size}"></screen>'''

	def __init__(self, session):
		size = "%s,%s" % (DESKTOP_WIDTH, DESKTOP_HEIGHT)
		dic = {'size': size}
		tvAllScreen.__init__(self, session, tvAllScreenFull.skin, dic)


class tvBaseScreen(tvAllScreen):

	def __init__(self, session, skin=None, dic=None, scale=True):
		tvAllScreen.__init__(self, session, skin, dic, scale)
		self.current = 'menu'
		self.oldcurrent = 'menu'
		self.start = ''
		self.end = ''
		self.day = ''
		self.name = ''
		self.shortdesc = ''
		self.picfile = '/tmp/tvspielfilm.jpg'
		self.pics = []
		self.trailer = False
		self.trailerurl = ''
		self.searchcount = 0
		for i in range(6):
			self.pics.append('/tmp/tvspielfilm%s.jpg' % i)
		self.localhtml = '/tmp/tvspielfilm.html'
		self.localhtml2 = '/tmp/tvspielfilmii.html'
		self.tagestipp = False
		if config.plugins.tvspielfilm.picon.value == 'plugin':
			self.picon = True
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		else:
			self.picon = False

	def _tvinfoHide(self):
		for i in range(5):
			self['tvinfo%s' % i].hide()

	def infotextHide(self):
		for i in range(8):
			self['infotext%s' % i].hide()
		self['picon'].hide()
		self['cinlogo'].hide()
		self['playlogo'].hide()
		self['searchtext'].hide()
		self['searchmenu'].hide()

	def setTVTitle(self, output):
		title = search('<title>(.*?)</title>', output)
		title = title.group(1).replace('&amp;', '&')
		title = sub(' - TV Spielfilm', '', title)
		self.setTitle(title)

	def finishedAutoTimer(self, answer):
		if answer:
			from Plugins.Extensions.AutoTimer.AutoTimerEditor import AutoTimerEditor
			answer, session = answer
			session.openWithCallback(self.finishedAutoTimerEdit, AutoTimerEditor, answer)

	def finishedAutoTimerEdit(self, answer):
		if answer:
			from Plugins.Extensions.AutoTimer.plugin import autotimer
			if autotimer is None:
				from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
				autotimer = AutoTimer()
			autotimer.add(answer)
			autotimer.writeXml()

	def getPics(self, output, idx):
		with open(self.pic[idx], 'wb') as f:
			f.write(output)
		if fileExists(self.pics[idx]):
			self['pic%s' % idx].instance.setPixmapFromFile(self.pic[idx])

	def GetPics(self, picurllist, offset, show=True, playshow=False):
		for i in range(6):
			try:
				picurl = picurllist[offset + i]
				self.picdownload(picurl, self.getPics, i)
				if show:
					self['pic%s' % i].show()
				if playshow:
					self['play%s' % i].show()
			except IndexError:
				if playshow:
					self['play%s' % i].hide()
				if show:
					self['pic%s' % i].hide()

	def picdownload(self, link, name, idx):
		getPage(ensure_binary(link)).addCallback(name, idx).addErrback(self.picdownloadError)

	def picdownloadError(self, output):
		pass

	def getRecPNG(self):
		return self.getPNG("rec", self.menuwidth - 140)

	def getPNG(self, x, Pos):
		png = '%s%sFHD.png' % (ICONPATH, x) if FULLHD else '%s%s.png' % (ICONPATH, x)
		if self.picon:
			if fileExists(png):
				return MultiContentEntryPixmapAlphaTest(pos=(Pos, 20), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png))
		else:
			if fileExists(png):
				return MultiContentEntryPixmapAlphaTest(pos=(Pos, 10), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png))
		return None

	def infotextStartEnd(self, infotext):
		try:
			parts = infotext[0].split(', ')
			x = parts[0]
			if x == 'Heute':
				d = sub('....-', '', str(self.date))
				d2 = sub('-..', '', d)
				d3 = sub('..-', '', d)
				x = 'he ' + d3 + '.' + d2 + '.'
			day = sub('.. ', '', x)
			self.day = sub('[.]..[.]', '', day)
			month = sub('.. ..[.]', '', x)
			month = sub('[.]', '', month)
			date = str(self.date) + 'FIN'
			year = sub('......FIN', '', date)
			self.postdate = year + '-' + month + '-' + self.day
			today = datetime.date(int(year), int(month), int(self.day))
			one_day = datetime.timedelta(days=1)
			self.nextdate = today + one_day
		except:
			pass

		try:
			parts = infotext[0].split(', ')
			x = parts[1]
			start = sub(' - ..:..', '', x)
			start = start + ':00'
			end = sub('..:.. - ', '', x)
			end = end + ':00'
			self.start = start
			self.end = end
		except IndexError:
			pass

	def infotextText(self, infotext):
		try:
			idx = 0
			for i in range(len(infotext)):
				parts = infotext[i].split(', ')
				for j in range(len(parts)):
					if idx < 8:
						self['infotext%s' % idx].setText(parts[j])
						self['infotext%s' % idx].show()
						idx += 1
		except IndexError:
			self['infotext%s' % idx].setText('')

	def _shortdesc(self, bereich):
		shortdesc = search('<section class="serial-info">\\n\\s+(.*?)</section>', bereich)
		if shortdesc:
			self.shortdesc = sub('<span class="info">', '', shortdesc.group(1))
			self.shortdesc = sub('</span>\\s+', ', ', self.shortdesc)
			self.shortdesc = sub('  ', '', self.shortdesc)
		else:
			self.shortdesc = ''
		name = findall('<h1 class="headline headline--article">(.*?)</h1>', bereich)
		try:
			self.name = name[0]
		except IndexError:
			name = findall('<span itemprop="name"><strong>(.*?)</strong></span>', bereich)
			try:
				self.name = name[0]
			except IndexError:
				self.name = ''

	def makePostTimer(self, output):
		output = ensure_str(output)
		startpos = output.find('<div class="content-area">')
		endpos = output.find('>Weitere Bildergalerien<')
		if endpos == -1:
			endpos = output.find('<h2 class="broadcast-info">')
			if endpos == -1:
				endpos = output.find('<div class="OUTBRAIN"')
				if endpos == -1:
					endpos = output.find('</footer>')
		bereich = output[startpos:endpos]
		bereich = transHTML(bereich)
		infotext = findall('<span class="text-row">(.*?)<', bereich)
		self.infotextStartEnd(infotext)
		self._shortdesc(bereich)
		self.current = 'postview'
		self.postviewready = True
		self.red()

	def makeTimer(self):
		if config.plugins.tvspielfilm.autotimer.value == 'yes' and isPluginInstalled('AutoTimer'):
			self.autotimer = True
			self.session.openWithCallback(self.choiceTimer, ChoiceBox, title='Timer Auswahl', list=[('Timer', 'timer'), ('AutoTimer', 'autotimer')])
		else:
			self.autotimer = False
			self.red()

	def choiceTimer(self, choice):
		choice = choice and choice[1]
		if choice == 'autotimer':
			self.autotimer = True
			self.red()
		else:
			self.autotimer = False
			self.red()

	def finishSanityCorrection(self, answer):
		self.finishedTimer(answer)

	def _makePostviewPage(self, string):
		output = open(self.localhtml2, 'r').read()
		output = ensure_str(output)
		self['label2'].setText('= Timer')
		self['label3'].setText('= YouTube Trailer')
		self['label4'].setText('')  # = Wikipedia
		self.setBlueButton('= Aus-/Einblenden')
		self['searchmenu'].hide()
		self['searchtext'].hide()
		output = sub('</dl>.\n\\s+</div>.\n\\s+</section>', '</cast>', output)
		startpos = output.find('<div class="content-area">')
		endpos = output.find('>Weitere Bildergalerien<')
		if endpos == -1:
			endpos = output.find('</cast>')
			if endpos == -1:
				endpos = output.find('<h2 class="broadcast-info">')
				if endpos == -1:
					endpos = output.find('<div class="OUTBRAIN"')
					if endpos == -1:
						endpos = output.find('</footer>')
		bereich = output[startpos:endpos]
		bereich = cleanHTML(bereich)
		trailerurl = parseTrailerUrl(output)
		if trailerurl:
			self.trailerurl = trailerurl
			self.trailer = True
		else:
			self.trailer = False
		bereich = sub('" alt=".*?" width="', '" width="', bereich)
		picurl = search('<img src="(.*?)" data-src="(.*?)" width="', bereich)
		if picurl:
			self.downloadPicPost(picurl.group(2), True)
		else:
			picurl = search('<meta property="og:image" content="(.*?)"', output)
			if picurl:
				self.downloadPicPost(picurl.group(1), True)
			else:
				picurl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
				self.downloadPicPost(picurl, True)
		if not self.search:
			title = search('<title>(.*?)</title>', output)
			title = transHTML(title.group(1))
			self.setTitle(title)
		if search('<ul class="rating-dots">', bereich):
			self.movie = True
		else:
			self.movie = False
		if search('<div class="film-gallery">', output):
			self.mehrbilder = True
			if self.trailer:
				self['label'].setText('OK = Zum Video, Text = Fotostrecke, 7/8/9 = IMDb/TMDb/TVDb, Info = EPG')
			else:
				self['label'].setText('OK = Fotostrecke, 7/8/9 = IMDb/TMDb/TVDb, Info = EPG')
		else:
			self.mehrbilder = False
			if self.trailer:
				self['label'].setText('OK = Zum Video, Text = Vollbild, 7/8/9 = IMDb/TMDb/TVDb, Info = EPG')
			else:
				self['label'].setText('OK = Vollbild, 7/8/9 = IMDb/TMDb/TVDb, Info = EPG')
		infotext = findall('<span class="text-row">(.*?)<', bereich)
		self.infotextStartEnd(infotext)
		self.infotextText(infotext)
		tvinfo = findall('<span class="add-info (.*?)">', bereich)
		for i in list(range(len(tvinfo))):
			try:
				tvi = ICONPATH + tvinfo[i] + 'FHD.png' if FULLHD else ICONPATH + tvinfo[i] + '.png'
				self.showTVinfos(tvi, i)
			except IndexError:
				pass
		self['piclabel'].setText(self.start[0:5])
		try:
			parts = infotext[0].split(', ')
			text = shortenChannel(parts[2])
			self['piclabel2'].setText(text[0:10])
		except IndexError:
			self['piclabel2'].setText('')
		self._shortdesc(bereich)
		if self.tagestipp:
			channel = findall("var adsc_sender = '(.*?)'", output)
			try:
				self.sref = self.service_db.lookup(channel[0])
				if self.sref != 'nope':
					self.zap = True
			except IndexError:
				pass
		picons = findall('<img src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*?).png.*?', bereich)
		picon = PICPATH + 'picons/' + picons[0] + '.png'
		if fileExists(picon):
			self['picon'].instance.setScale(1)
			self['picon'].instance.setPixmapFromFile(picon)
			self['picon'].show()
		else:
			self['picon'].hide()
		text = parsedetail(bereich)
		fill = self.getFill('TV Spielfilm Online\n\n*Info/EPG = EPG einblenden')
		self.POSTtext = text + fill
		self['textpage'].setText(self.POSTtext)
		self['textpage'].show()
		self.showEPG = False
		self.postviewready = True

	def showsearch(self):
		self.postviewready = False
		self.infotextHide()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self._tvinfoHide()
		self['seitennr'].setText('')
		self['label'].setText('')
		self['label2'].setText('')
		self['label3'].setText('')
		self['label4'].setText('')
		self['label5'].setText('')
		self['searchmenu'].show()
		self['searchtext'].show()

	def showTVinfos(self, picinfo, idx):
		if fileExists(picinfo):
			self['tvinfo%s' % idx].instance.setPixmapFromFile(picinfo)
			self['tvinfo%s' % idx].show()

	def getPicPost(self, output, label):
		with open(self.picfile, 'wb') as f:
			f.write(output)
		self.showPicPost(label)

	def showPicPost(self, label=False):
		if fileExists(self.picfile):
			try:
				self['picpost'].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
				self['picpost'].instance.setPixmapFromFile(self.picfile)
			except:
				currPic = loadJPG(self.picfile)
				self['picpost'].instance.setScale(1)
				self['picpost'].instance.setPixmap(currPic)
			self['picpost'].show()
			if label:
				self['piclabel'].show()
				self['piclabel2'].show()
			if self.trailer:
				self['cinlogo'].show()
				self['playlogo'].show()

	def downloadPicPost(self, link, label):
		link = sub('.*?data-src="', '', link)
		getPage(ensure_binary(link)).addCallback(self.getPicPost, label).addErrback(self.downloadPicPostError)

	def downloadPicPostError(self, output):
		pass

	def IMDb(self):
		if self.current == 'postview':
			if isPluginInstalled('IMDb'):
				from Plugins.Extensions.IMDb.plugin import IMDB
				self.session.open(IMDB, self.name)
			else:
				self.session.openWithCallback(
					self.IMDbInstall, MessageBox, '\nDas IMDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)

	def TMDb(self):
		if self.current == 'postview':
			if isPluginInstalled('tmdb'):
				from Plugins.Extensions.tmdb.tmdb import tmdbScreen
				self.session.open(tmdbScreen, self.name, 2)
			else:
				self.session.openWithCallback(
					self.TMDbInstall, MessageBox, '\nDas TMDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)

	def TVDb(self):
		if self.current == 'postview':
			if isPluginInstalled('TheTVDB'):
				from Plugins.Extensions.TheTVDB.plugin import TheTVDBMain
				self.name = sub('Die ', '', self.name)
				self.session.open(TheTVDBMain, self.name)
			else:
				self.session.openWithCallback(
					self.TVDbInstall, MessageBox, '\nDas TheTVDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)

	def IMDbInstall(self, answer):
		if answer is True:
			self.container = eConsoleAppContainer()
			self.container.appClosed.append(self.finishedIMDbInstall)
			self.container.execute('opkg update && opkg install enigma2-plugin-extensions-imdb')

	def finishedIMDbInstall(self, retval):
		del self.container.appClosed[:]
		del self.container
		if isPluginInstalled('IMDb'):
			self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas IMDb Plugin wurde installiert.\nBitte starten Sie Enigma neu.', MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, '\nDas IMDb Plugin ist nicht auf dem Feed ihres Images vorhanden.\n\nBitte installieren Sie das IMDb Plugin manuell.', MessageBox.TYPE_ERROR)

	def TMDbInstall(self, answer):
		if answer is True:
			self.container = eConsoleAppContainer()
			self.container.appClosed.append(self.finishedTMDbInstall)
			self.container.execute('opkg update && opkg install enigma2-plugin-extensions-tmdbinfo')

	def finishedTMDbInstall(self, retval):
		del self.container.appClosed[:]
		del self.container
		if isPluginInstalled('TMDb'):
			self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas TMDb Plugin wurde installiert.\nBitte starten Sie Enigma neu.', MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, '\nDas TMDb Plugin ist nicht auf dem Feed ihres Images vorhanden.\n\nBitte installieren Sie das TMDb Plugin manuell.', MessageBox.TYPE_ERROR)

	def TVDbInstall(self, answer):
		if answer is True:
			self.container = eConsoleAppContainer()
			self.container.appClosed.append(self.finishedTVDbInstall)
			self.container.execute('opkg update && opkg install enigma2-plugin-extensions-thetvdb')

	def finishedTVDbInstall(self, retval):
		del self.container.appClosed[:]
		del self.container
		if isPluginInstalled('TheTVDB'):
			self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas TheTVDb Plugin wurde installiert.\nBitte starten Sie Enigma neu.', MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, '\nDas TheTVDb Plugin ist nicht auf dem Feed ihres Images vorhanden.\n\nBitte installieren Sie das TheTVDb Plugin manuell.', MessageBox.TYPE_ERROR)

	def restartGUI(self, answer):
		if answer is True:
			try:
				self.session.open(TryQuitMainloop, 3)
			except RuntimeError:
				self.close()

	def playTrailer(self):
		if self.current == 'postview' and self.postviewready and self.trailer:
			sref = eServiceReference(4097, 0, self.trailerurl)
			sref.setName(self.name)
			self.session.open(MoviePlayer, sref)

	def _pressText(self):
		if self.current == 'postview' and self.postviewready:
			if self.mehrbilder:
				self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
			else:
				self.session.openWithCallback(self.showPicPost, FullScreen)

	def redTimer(self, search=False, sref=None):
		if sref == None:
			try:
				if search:
					c = self['searchmenu'].getSelectedIndex()
					self.oldsearchindex = c
					sref = self.searchref[c]
				else:
					c = self['menu'].getSelectedIndex()
					self.oldindex = c
					sref = self.sref[c]
				serviceref = ServiceReference(sref)
			except IndexError:
				serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())
		else:
			serviceref = ServiceReference(sref)
		try:
			start = self.start
			s1 = sub(':..', '', start)
			date = str(self.postdate) + 'FIN'
			date = sub('..FIN', '', date)
			date = date + self.day
			parts = start.split(':')
			seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
			seconds -= int(config.recording.margin_before.value) * 60
			start = strftime('%H:%M:%S', gmtime(seconds))
			s2 = sub(':..:..', '', start)
			if int(s2) > int(s1):
				start = str(self.date) + ' ' + start
			else:
				start = date + ' ' + start
			start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
			end = self.end
			parts = end.split(':')
			seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
			seconds += int(config.recording.margin_after.value) * 60
			end = strftime('%H:%M:%S', gmtime(seconds))
			e2 = sub(':..:..', '', end)
			if int(s2) > int(e2):
				end = str(self.nextdate) + ' ' + end
			else:
				end = date + ' ' + end
			end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
		except IndexError:
			pass

		name = self.name
		shortdesc = self.shortdesc
		if shortdesc != '' and search('Staffel [0-9]+, Folge [0-9]+', shortdesc):
			episode = search('(Staffel [0-9]+, Folge [0-9]+)', shortdesc)
			episode = sub('Staffel ', 'S', episode.group(1))
			episode = sub(', Folge ', 'E', episode)
			name = name + ' ' + episode

		try:
			data = (int(mktime(start.timetuple())),
					int(mktime(end.timetuple())),
					name,
					shortdesc,
					None)
		except:
			printStackTrace()

		try:
			newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *data)
			if not self.autotimer:
				self.session.openWithCallback(self.finishedTimer, TimerEntry, newEntry)
			else:
				from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
				from Plugins.Extensions.AutoTimer.plugin import autotimer
				if autotimer is None:
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
					autotimer = AutoTimer()
				autotimer.readXml()
				newTimer = autotimer.defaultTimer.clone()
				newTimer.id = autotimer.getUniqueId()
				newTimer.name = self.name
				newTimer.match = ''
				newTimer.enabled = True
				self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(
					mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)
		except:
			printStackTrace()

	def initBlueButton(self, text):
		self['bluebutton'] = Pixmap()
		if ALPHA:
			self['bluebutton'].show()
			self['label5'] = Label(text)
		else:
			self['bluebutton'].hide()
			self['label5'] = Label('')

	def setBlueButton(self, text):
		if ALPHA:
			self['bluebutton'].show()
			self['label5'].setText(text)
		else:
			self['bluebutton'].hide()
			self['label5'].setText('')

	def _commonInit(self, ltxt='= Suche', lltxt='= Zappen'):
		self['picpost'] = Pixmap()
		for i in range(5):
			self['tvinfo%s' % i] = Pixmap()
		self['picon'] = Pixmap()
		self['cinlogo'] = Pixmap()
		self['playlogo'] = Pixmap()
		self['searchtext'] = Label('')
		for i in range(8):
			self['infotext%s' % i] = Label('')
		self['searchmenu'] = ItemList([])
		self['textpage'] = ScrollLabel('')
		self['piclabel'] = Label('')
		self['piclabel'].hide()
		self['piclabel2'] = Label('')
		self['piclabel2'].hide()
		self['seitennr'] = Label('')
		self['label'] = BlinkingLabel('Bitte warten...')
		self['label'].startBlinking()
		self['label2'] = Label('= Timer')
		self['label3'] = Label(ltxt)
		self['label4'] = Label(lltxt)
		self.initBlueButton('= Aus-/Einblenden')

	def _makeSearchView(self, url, titlemode=0, searchmode=0):
		header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
				  'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
				  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
				  'Accept-Language': 'en-us,en;q=0.5'}
		searchrequest = Request(url, None, header)
		try:
			output = urlopen(searchrequest, timeout=5).read()
		except (HTTPError, URLError, HTTPException, error, AttributeError):
			output = ' '

		if titlemode == 1:
			title = 'Genre: ' + self.genre.replace(':', ' -') + ', Filter: ' + self.searchstring
			self.setTitle(title)
		else:
			title = search('<title>(.*?)</title>', output)
			if title:
				self['searchtext'].setText(title.group(1))
				self['searchtext'].show()
				self.setTitle('')
				self.setTitle(title.group(1))
		items, bereich = parsePrimeTimeTable(output)
		mh = int(41 * SCALE + 0.5)
		for DATUM, START, TITLE, GENRE, INFOS, LOGO, LINK, RATING in items:  # TV-Genre
			if DATUM:
				self.datum_string = DATUM
				res_datum = [DATUM]
				if self.backcolor:
					res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=0, backcolor_sel=self.back_color, text=''))
				res_datum.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=2, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=DATUM))
				self.searchref.append('na')
				self.searchlink.append('na')
				self.searchentries.append(res_datum)
				self.filter = True
				continue
			res = [LOGO]
			if self.backcolor:
				res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=0, backcolor_sel=self.back_color, text=''))
			start = START
			res.append(MultiContentEntryText(pos=(int(67 * SCALE), 0), size=(175, 40), font=0, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=START))
			if LOGO:
				service = LOGO
				sref = self.service_db.lookup(service)
				if sref == 'nope':
					self.filter = True
				else:
					self.filter = False
					self.searchref.append(sref)
					if self.picon:
						picon = findPicon(sref, self.piconfolder)
						if picon:
							res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(picon), flags=BT_SCALE))
						else:
							res.append(MultiContentEntryText(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
					else:
						png = '%slogos/%s.png' % (PICPATH, LOGO)
						if fileExists(png):
							res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(59, 36), png=loadPNG(png)))
					start = sub(' - ..:..', '', start)
					daynow = sub('....-..-', '', str(self.date))
					day = search(', ([0-9]+). ', self.datum_string)
					if day:
						day = day.group(1)
					else:
						day = daynow
					if int(day) >= int(daynow) - 1:
						date = str(self.date) + 'FIN'
					else:
						four_weeks = datetime.timedelta(weeks=4)
						date = str(self.date + four_weeks) + 'FIN'
					date = sub('[0-9][0-9]FIN', day, date)
					timer = date + ':::' + start + ':::' + str(sref)
					if timer in self.timer:
						self.rec = True
						rp = self.getRecPNG()
						if rp:
							res.append(rp)
					self.searchlink.append(LINK)
					titelfilter = TITLE
					if GENRE is None:
						res.append(MultiContentEntryText(pos=(int(190 * SCALE), int(10 * SCALE)), size=(int(445 * SCALE), 40), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
					infooffset = 140
					for INFO in INFOS:
						if self.rec:
							self.rec = False
						else:
							rp = self.getPNG(INFO, self.menuwidth - infooffset)
							if rp:
								res.append(rp)
							infooffset = infooffset + 70
					self.datum = False
					if RATING:
						if RATING != 'rating small':
							RATING = RATING.replace(' ', '-')
							png = '%s%sFHD.png' % (ICONPATH, RATING) if FULLHD else '%s%s.png' % (ICONPATH, RATING)
							if fileExists(png):
								res.append(MultiContentEntryPixmapAlphaTest(pos=(int(785 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
					res.append(MultiContentEntryText(pos=(int(190 * SCALE), 10), size=(int(445 * SCALE), 40), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titelfilter))
					self.searchentries.append(res)
		self['searchmenu'].l.setItemHeight(mh)
		self['searchmenu'].l.setList(self.searchentries)
		self['searchmenu'].show()
		self.searchcount += 1
		if searchmode == 1:
			searchtext1 = '<a class="next" href=".*?"'
			searchtext2 = '<a class="next" href="(.*?)"'
		else:
			searchtext1 = NEXTPage1
			searchtext2 = NEXTPage2
		if self.searchcount <= self.maxsearchcount and search(searchtext1, bereich):
			nextpage = search(searchtext2, bereich)
			if nextpage:
				self.makeSearchView(nextpage.group(1))
			else:
				self.ready = True
		else:
			try:
				if self.searchref[-1] == 'na':
					del self.searchref[-1]
					del self.searchlink[-1]
					del self.searchentries[-1]
					self['searchmenu'].l.setList(self.searchentries)
			except IndexError:
				pass
			self['searchmenu'].moveToIndex(self.oldsearchindex)
			self.current = 'searchmenu'
			self.ready = True

	def _ok(self):
		if not HIDEFLAG:
			return
		if self.current == 'postview' and self.postviewready:
			if self.trailer:
				sref = eServiceReference(4097, 0, self.trailerurl)
				sref.setName(self.name)
				self.session.open(MoviePlayer, sref)
			elif self.mehrbilder:
				self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
			else:
				self.session.openWithCallback(self.showPicPost, FullScreen)
		elif self.current == 'postview' and not self.postviewready:
			pass
		else:
			self.selectPage('ok')


class TVTippsView(tvBaseScreen):

	def __init__(self, session, link, sparte):
		global HIDEFLAG
		skin = readSkin("TVTippsView")
		tvBaseScreen.__init__(self, session, skin)
		self.skinName = "TVTippsView"
		if sparte == 'neu':
			self.titel = 'TV Neuerscheinungen - TV Spielfilm'
		else:
			self.titel = 'TV-Tipps - TV Spielfilm'
		self.menuwidth = self.menuwidth - 135
		self.sparte = sparte
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.picurllist = []
		self.searchlink = []
		self.searchref = []
		self.searchentries = []
		self.sref = []
		self.postlink = link
		self.link = link
		self.POSTtext = ''
		self.EPGtext = ''
		HIDEFLAG = True
		self.new = False
		self.newfilter = False
		self.search = False
		self.rec = False
		self.ready = False
		self.postviewready = False
		self.mehrbilder = False
		self.movie = False
		self.datum = False
		self.filter = True
		self.len = 0
		self.oldindex = 0
		self.oldsearchindex = 1
		self['release'] = Label(RELEASE)
		self['release'].show()
		for i in range(6):
			self['pic%s' % i] = Pixmap()
		self._commonInit()
		self.infotextHide()
		self['menu'] = ItemList([])
		self['actions'] = ActionMap(['OkCancelActions',
									 'ChannelSelectBaseActions',
									 'DirectionActions',
									 'EPGSelectActions',
									 'NumberActions',
									 'InfobarTeletextActions',
									 'MoviePlayerActions'], {'ok': self.ok,
															 'cancel': self.exit,
															 'right': self.rightDown,
															 'left': self.leftUp,
															 'down': self.down,
															 'up': self.up,
															 'nextBouquet': self.nextDay,
															 'prevBouquet': self.prevDay,
															 'nextMarker': self.nextWeek,
															 'prevMarker': self.prevWeek,
															 '0': self.gotoEnd,
															 '1': self.zapUp,
															 '2': self.zapDown,
															 '7': self.IMDb,
															 '8': self.TMDb,
															 '9': self.TVDb,
															 'info': self.getEPG,
															 'epg': self.getEPG,
															 'leavePlayer': self.youTube,
															 'startTeletext': self.pressText}, -1)
		self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
															'yellow': self.yellow,
															'red': self.makeTimer,
															'blue': self.hideScreen}, -1)
		self.service_db = serviceDB(self.servicefile)
		self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		if config.plugins.tvspielfilm.genreinfo.value == 'no':
			self.showgenre = False
		else:
			self.showgenre = True
		self.makeTVTimer = eTimer()
		self.makeTVTimer.callback.append(self.downloadFullPage(link, self.makeTVTipps))
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PICPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		self.makeTVTimer.start(200, True)

	def makeTVTipps(self, string):
		output = open(self.localhtml, 'r').read()
		output = ensure_str(output)
		self.sref = []
		for i in range(6):
			self['pic%s' % i].hide()
		items = buildTVTippsArray(self.sparte, output)
		date = str(self.date.strftime('%d.%m.%Y'))
		self.titel = 'TV-Tipps - ' + str(self.sparte) + ' - ' + str(self.weekday) + ', ' + date
		if self.sparte == 'neu':
			self.titel = 'TV Neuerscheinungen - ' + str(self.weekday) + ', ' + date
		self.setTitle(self.titel)
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.picurllist = []
		mh = int(41 * SCALE)
		for LINK, PIC, TIME, INFOS, NAME, GENRE, LOGO in items:
			sref = None
			self.new = False
			if LINK:
				res = [LINK]
				if self.backcolor:
					res.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * SCALE), mh), font=1, backcolor_sel=self.back_color, text=''))
				linkfilter = LINK
			if PIC:
				picfilter = PIC
			if TIME:
				start = TIME
				res.append(MultiContentEntryText(pos=(int(70 * SCALE), 0), size=(int(60 * SCALE), mh), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=TIME))
			icount = 0
			for INFO in INFOS:
				if search('neu|new', INFO) or self.sparte != "neu":
					self.new = True
				png = '%s%sFHD.png' % (ICONPATH, INFO) if FULLHD else '%s%s.png' % (ICONPATH, INFO)
				if fileExists(png):
					yoffset = int((mh - 14 * SCALE * len(INFOS)) / 2 + 14 * SCALE * icount)
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1110 * SCALE), yoffset), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
					icount += 1
			if NAME:
				titelfilter = NAME
				res.append(MultiContentEntryText(pos=(int(160 * SCALE), 0), size=(int(580 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=NAME))
			if GENRE:
				text = GENRE.replace(',', '\n', 1)
				res.append(MultiContentEntryText(pos=(int(700 * SCALE), 0), size=(int(400 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT | RT_VALIGN_CENTER | RT_WRAP, text=text))
				if self.sparte == 'Spielfilm':
					png = ICONPATH + 'rating-small1FHD.png' if FULLHD else ICONPATH + 'rating-small1.png'
					if fileExists(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
			if LOGO:
				service = LOGO
				sref = self.service_db.lookup(service)
				if config.plugins.tvspielfilm.picon.value == "plugin":
					png = self.piconfolder + '%s.png' % LOGO
				else:
					png = findPicon(sref, self.piconfolder)
				if png:
					res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
				else:
					res.append(MultiContentEntryText(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
				if sref == 'nope':
					sref = None
				elif self.new:
					hour = sub(':..', '', start)
					if int(hour) < 5:
						one_day = datetime.timedelta(days=1)
						date = self.date + one_day
					else:
						date = self.date
					timer = str(date) + ':::' + start + ':::' + str(sref)
					if timer in self.timer:
						png = ICONPATH + 'recFHD.png' if FULLHD else ICONPATH + 'rec.png'
						if fileExists(png):
							res.append(MultiContentEntryPixmapAlphaTest(pos=(int(930 * SCALE), int(14 * SCALE)), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
			if sref and self.new:
				self.sref.append(sref)
				self.picurllist.append(picfilter)
				self.tvlink.append(linkfilter)
				self.tvtitel.append(titelfilter)
				self.tventries.append(res)
		self['menu'].l.setItemHeight(mh)
		self['menu'].l.setList(self.tventries)
		self['menu'].moveToIndex(self.oldindex)
		if self.oldindex > 5:
			self.leftUp()
			self.rightDown()
		self.len = len(self.tventries)
		self['label'].setText('Info = Filter: NEU, Bouquet = +- Tag, <> = +- Woche')
		if self.sparte == 'neu':
			self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
		self['label'].stopBlinking()
		self['label'].show()
		self.ready = True

	def makePostviewPage(self, string):
		self['menu'].hide()
		for i in range(6):
			self['pic%s' % i].hide()
		try:
			self._makePostviewPage(string)
		except:
			printStackTrace()

	def makeSearchView(self, url):
		self._makeSearchView(url, 0, 1)

	def ok(self):
		self._ok()

	def selectPage(self, action):
		if self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				self.postlink = self.tvlink[c]
			except IndexError:
				pass
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			try:
				self.postlink = self.searchlink[c]
			except IndexError:
				pass

		if action == 'ok' and self.ready:
			if search('www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				self.downloadPostPage(self.postlink, self.makePostviewPage)

	def getEPG(self):
		if self.current == 'postview' and self.postviewready:
			if not self.showEPG:
				self.showEPG = True
				if not self.search:
					try:
						c = self['menu'].getSelectedIndex()
						sref = self.sref[c]
						channel = ServiceReference(eServiceReference(sref)).getServiceName()
					except IndexError:
						sref = None
						channel = ''
				else:
					try:
						c = self['searchmenu'].getSelectedIndex()
						sref = self.searchref[c]
						channel = ServiceReference(eServiceReference(sref)).getServiceName()
					except IndexError:
						sref = None
						channel = ''
				if sref:
					try:
						start = self.start
						s1 = sub(':..', '', start)
						date = str(self.postdate) + 'FIN'
						date = sub('..FIN', '', date)
						date = date + self.day
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(':..:..', '', start)
						if int(s2) > int(s1):
							start = str(self.date) + ' ' + start
						else:
							start = date + ' ' + start
						start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
						start = int(mktime(start.timetuple()))
						epgcache = eEPGCache.getInstance()
						event = epgcache.startTimeQuery(eServiceReference(sref), start)
						if event == -1:
							self.EPGText = getEPGText()
						else:
							event = epgcache.getNextTimeEntry()
							self.EPGtext = event.getEventName()
							short = event.getShortDescription()
							ext = event.getExtendedDescription()
							dur = '%d Minuten' % (event.getDuration() / 60)
							if short and short != self.EPGtext:
								self.EPGtext += '\n\n' + short
							if ext:
								self.EPGtext += '\n\n' + ext
							if dur:
								self.EPGtext += '\n\n' + dur
					except:
						self.EPGText = getEPGText()
				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n\n' + fill
				self['textpage'].setText(self.EPGtext)
				self['textpage'].show()
			else:
				self.showEPG = False
				self['textpage'].setText(self.POSTtext)
				self['textpage'].show()
		elif self.sparte != 'neu' and self.current == 'menu' and self.ready and not self.search:
			if not self.newfilter:
				self.newfilter = True
			else:
				self.newfilter = False
			self.refresh()

	def red(self):
		if self.current == 'postview' and self.postviewready:
			if not self.search:
				self.redTimer()
			elif self.search:
				self.redTimer(True)
			else:
				self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
		elif self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.oldindex = c
			try:
				self.postlink = self.tvlink[c]
			except IndexError:
				pass

			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			try:
				self.postlink = self.searchlink[c]
			except IndexError:
				pass

			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)

	def finishedTimer(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)

				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			self.makeTimerDB()
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
				self.refresh()
			else:
				self.showsearch()
		else:
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
			else:
				self.showsearch()

	def green(self):
		if self.current == 'menu' and not self.search:
			c = self['menu'].getSelectedIndex()
			try:
				sref = self.sref[c]
				if sref != '':
					self.session.nav.playService(eServiceReference(sref))
			except IndexError:
				pass

	def yellow(self):
		if self.current == 'postview':
			self.youTube()
		elif self.current == 'menu' and not self.search and self.ready:
			try:
				c = self['menu'].getSelectedIndex()
				self.oldindex = c
				titel = self.tvtitel[c]
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
			except IndexError:
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

	def searchReturn(self, search):
		if search and search != '':
			self.searchstring = search
			self['menu'].hide()
			for i in range(6):
				self['pic%s' % i].hide()
			self['label'].setText('')
			self['label2'].setText('')
			self['label3'].setText('')
			self['label4'].setText('')
			self['label5'].setText('')
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = search.replace(' ', '+')
			searchlink = self.baseurl + '/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=' + search + '&page=1'
			self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(searchYouTube, self.name, self.movie)
		elif self.current == 'menu' and not self.search and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				titel = self.tvtitel[c]
				self.session.open(searchYouTube, titel, self.movie)
			except IndexError:
				pass

	def nextDay(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('date', self.link):
				self.link = self.link + 'FIN'
				date1 = findall('date=(.*?)-..-..FIN', self.link)
				date2 = findall('date=....-(.*?)-..FIN', self.link)
				date3 = findall('date=....-..-(.*?)FIN', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

				one_day = datetime.timedelta(days=1)
				tomorrow = today + one_day
				self.weekday = makeWeekDay(tomorrow.weekday())
				nextday = sub('date=(.*?FIN)', 'date=', self.link)
				nextday = nextday + str(tomorrow)
				self.date = tomorrow
				one_day = datetime.timedelta(days=1)
				self.nextdate = self.date + one_day
			else:
				today = datetime.date.today()
				one_day = datetime.timedelta(days=1)
				tomorrow = today + one_day
				self.weekday = makeWeekDay(tomorrow.weekday())
				nextday = self.link + '?date=' + str(tomorrow)
				self.date = tomorrow
				one_day = datetime.timedelta(days=1)
				self.nextdate = self.date + one_day
			self.link = nextday
			self.oldindex = 0
			self.refresh()
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def prevDay(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('date', self.link):
				self.link = self.link + 'FIN'
				date1 = findall('date=(.*?)-..-..FIN', self.link)
				date2 = findall('date=....-(.*?)-..FIN', self.link)
				date3 = findall('date=....-..-(.*?)FIN', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

				one_day = datetime.timedelta(days=1)
				yesterday = today - one_day
				self.weekday = makeWeekDay(yesterday.weekday())
				prevday = sub('date=(.*?FIN)', 'date=', self.link)
				prevday = prevday + str(yesterday)
				self.date = yesterday
				one_day = datetime.timedelta(days=1)
				self.nextdate = self.date + one_day
			else:
				today = datetime.date.today()
				one_day = datetime.timedelta(days=1)
				yesterday = today - one_day
				self.weekday = makeWeekDay(yesterday.weekday())
				prevday = self.link + '?date=' + str(yesterday)
				self.date = yesterday
				one_day = datetime.timedelta(days=1)
				self.nextdate = self.date + one_day
			self.link = prevday
			self.oldindex = 0
			self.refresh()
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def nextWeek(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('date', self.link):
				self.link = self.link + 'FIN'
				date1 = findall('date=(.*?)-..-..FIN', self.link)
				date2 = findall('date=....-(.*?)-..FIN', self.link)
				date3 = findall('date=....-..-(.*?)FIN', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

				one_week = datetime.timedelta(days=7)
				tomorrow = today + one_week
				self.weekday = makeWeekDay(tomorrow.weekday())
				nextweek = sub('date=(.*?FIN)', 'date=', self.link)
				nextweek = nextweek + str(tomorrow)
				self.date = tomorrow
				one_week = datetime.timedelta(days=7)
				self.nextdate = self.date + one_week
			else:
				today = datetime.date.today()
				one_week = datetime.timedelta(days=7)
				tomorrow = today + one_week
				self.weekday = makeWeekDay(tomorrow.weekday())
				nextweek = self.link + '?date=' + str(tomorrow)
				self.date = tomorrow
				one_week = datetime.timedelta(days=7)
				self.nextdate = self.date + one_week
			self.link = nextweek
			self.oldindex = 0
			self.refresh()

	def prevWeek(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('date', self.link):
				self.link = self.link + 'FIN'
				date1 = findall('date=(.*?)-..-..FIN', self.link)
				date2 = findall('date=....-(.*?)-..FIN', self.link)
				date3 = findall('date=....-..-(.*?)FIN', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

				one_week = datetime.timedelta(days=7)
				yesterday = today - one_week
				self.weekday = makeWeekDay(yesterday.weekday())
				prevweek = sub('date=(.*?FIN)', 'date=', self.link)
				prevweek = prevweek + str(yesterday)
				self.date = yesterday
				one_week = datetime.timedelta(days=7)
				self.nextdate = self.date + one_week
			else:
				today = datetime.date.today()
				one_week = datetime.timedelta(days=7)
				yesterday = today - one_week
				self.weekday = makeWeekDay(yesterday.weekday())
				prevweek = self.link + '?date=' + str(yesterday)
				self.date = yesterday
				one_week = datetime.timedelta(days=7)
				self.nextdate = self.date + one_week
			self.link = prevweek
			self.oldindex = 0
			self.refresh()

	def gotoEnd(self):
		if self.current != 'postview' and self.ready and not self.search:
			end = self.len - 1
			self['menu'].moveToIndex(end)
			if end > 5:
				self.leftUp()
				self.rightDown()
		elif self.current != 'postview' and self.ready and self.search:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

	def downloadPostPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

	def downloadFullPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

	def downloadPageError(self, output):
		self['label'].setText('Info = Filter: NEU, Bouquet = +- Tag, <> = +- Woche')
		if self.sparte == 'neu':
			self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
		self['label'].stopBlinking()
		self['label'].show()
		self.ready = True

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['label'].setText('Bitte warten...')
		self['label'].startBlinking()
		self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVTipps))

	def showProgrammPage(self):
		self['label'].setText('Info = Filter: NEU, Bouquet = +- Tag, <> = +- Woche')
		if self.sparte == 'neu':
			self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
		self['label2'].setText('= Timer')
		self['label3'].setText('= Suche')
		self['label4'].setText('= Zappen')
		self.infotextHide()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self._tvinfoHide()
		self.current = 'menu'
		self['menu'].show()
		try:
			c = self['menu'].getSelectedIndex()
			d = self.len - c
			x = self.len % 6
			if d > 6:
				x = 0
			elif d > x:
				x = 0
		except IndexError:
			x = 0
		if x == 0:
			x = 6
		for i in range(6 - x, 6):
			self['pic%s' % (5 - i)].show()

	def down(self):
		if self.current == 'menu':
			c = self['menu'].getSelectedIndex()
			self['menu'].down()
			if c + 1 == self.len:
				self.GetPics(self.picurllist, 0)
			elif c % 6 == 5:
				self.GetPics(self.picurllist, c + 1)
		elif self.current == 'searchmenu':
			self['searchmenu'].down()
		else:
			self['textpage'].pageDown()

	def up(self):
		if self.current == 'menu':
			c = self['menu'].getSelectedIndex()
			self['menu'].up()
			if c == 0:
				l = self.len
				d = l % 6
				if d == 0:
					d = 6
				self.GetPics(self.picurllist, l - d)
			elif c % 6 == 0:
				self.GetPics(self.picurllist, c - 6)

		elif self.current == 'searchmenu':
			self['searchmenu'].up()
		else:
			self['textpage'].pageUp()

	def rightDown(self):
		if self.current == 'menu':
			c = self['menu'].getSelectedIndex()
			self['menu'].pageDown()
			l = self.len
			d = c % 6
			e = l % 6
			if e == 0:
				e = 6
			if c + e >= l:
				pass
			self.GetPics(self.picurllist, c - d + 6)
		elif self.current == 'searchmenu':
			self['searchmenu'].pageDown()
		else:
			self['textpage'].pageDown()

	def leftUp(self):
		if self.current == 'menu':
			c = self['menu'].getSelectedIndex()
			self['menu'].pageUp()
			d = c % 6
			if c < 6:
				pass
			self.GetPics(self.picurllist, c - d - 6, False)
			for i in range(6):
				self['pic%s' % i].show()
		elif self.current == 'searchmenu':
			self['searchmenu'].pageUp()
		else:
			self['textpage'].pageUp()

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.current == 'menu':
			self.close()
		elif self.current == 'searchmenu':
			self.search = False
			self.oldsearchindex = 1
			self['searchmenu'].hide()
			self['searchtext'].hide()
			self.showProgrammPage()
			self.setTitle('')
			self.setTitle(self.titel)
		elif self.current == 'postview' and not self.search:
			self.postviewready = False
			self.setTitle('')
			self.setTitle(self.titel)
			self.showProgrammPage()
		elif self.current == 'postview' and self.search:
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


class tvGenreJetztProgrammView(tvBaseScreen):

	def __init__(self, session, link):
		global HIDEFLAG
		skin = readSkin("TVProgrammView")
		tvBaseScreen.__init__(self, session, skin)
		self.skinName = "TVProgrammView"
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.searchlink = []
		self.searchref = []
		self.searchentries = []
		self.postlink = link
		self.POSTtext = ''
		self.EPGtext = ''
		self.rec = False
		self.ready = False
		HIDEFLAG = True
		self.movie = False
		self.datum = False
		self.filter = True
		self.search = False
		self.postviewready = False
		self.mehrbilder = False
		self.oldindex = 0
		self.oldsearchindex = 1
		self.titel = ''
		self['menu'] = ItemList([])
		self['release'] = Label(RELEASE)
		self['release'].show()
		self.initBlueButton('= Aus-/Einblenden')


class TVGenreView(tvGenreJetztProgrammView):

	def __init__(self, session, link, genre):
		tvGenreJetztProgrammView.__init__(self, session, link)
		self.sref = []
		self.link = link
		self.genre = genre
		if search('Serie', genre):
			self.serie = True
		else:
			self.serie = False
		self.load = True
		self.maxgenrecount = config.plugins.tvspielfilm.maxgenre.value
		self.genrecount = 0
		self._commonInit('= Filter')
		self.infotextHide()
		self['actions'] = ActionMap(['OkCancelActions',
									 'DirectionActions',
									 'EPGSelectActions',
									 'NumberActions',
									 'InfobarTeletextActions',
									 'ChannelSelectBaseActions',
									 'MoviePlayerActions'], {'ok': self.ok,
															 'cancel': self.exit,
															 'right': self.rightDown,
															 'left': self.leftUp,
															 'down': self.down,
															 'up': self.up,
															 'nextBouquet': self.zap,
															 'prevBouquet': self.zap,
															 '0': self.gotoEnd,
															 '1': self.zapUp,
															 '2': self.zapDown,
															 '7': self.IMDb,
															 '8': self.TMDb,
															 '9': self.TVDb,
															 'info': self.getEPG,
															 'epg': self.getEPG,
															 'leavePlayer': self.youTube,
															 'startTeletext': self.pressText}, -1)
		self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
															'yellow': self.yellow,
															'red': self.makeTimer,
															'blue': self.hideScreen}, -1)
		self.service_db = serviceDB(self.servicefile)
		f = open(self.servicefile, 'r')
		lines = f.readlines()
		f.close()
		self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		if config.plugins.tvspielfilm.genreinfo.value == 'no':
			self.showgenre = False
		else:
			self.showgenre = True
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PICPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		self.makeTVTimer = eTimer()
		self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVGenreView))
		self.makeTVTimer.start(200, True)

	def makeTVGenreView(self, output):
		output = ensure_str(output)
		self.titel = ' %s - Sendungen der nächsten 14 Tage' % self.genre
		self.setTitle(self.titel)
		items, bereich = parsePrimeTimeTable(output)
		res = [items]
		mh = int(41 * SCALE)
		for DATUM, START, TITLE, GENRE, INFOS, LOGO, LINK, RATING in items:
			if DATUM:
				self.datum_string = DATUM
				res_datum = [DATUM]
				if self.backcolor:
					res_datum.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * SCALE), mh), font=1, backcolor_sel=self.back_color, text=''))
				res_datum.append(MultiContentEntryText(pos=(int(85 * SCALE), 0), size=(int(500 * SCALE), mh), font=2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=DATUM))
				self.sref.append('na')
				self.tvlink.append('na')
				self.tvtitel.append('na')
				self.tventries.append(res_datum)
				self.filter = True
				continue
			res = [LOGO]
			if self.backcolor:
				res.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * SCALE), mh), font=1, backcolor_sel=self.back_color, text=''))
			start = START
			res.append(MultiContentEntryText(pos=(int(50 * SCALE), 0), size=(int(120 * SCALE), mh), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=START))
			if LOGO:
				service = LOGO
				sref = self.service_db.lookup(service)
				if sref == 'nope':
					self.filter = True
				else:
					self.filter = False
					self.sref.append(sref)
					if config.plugins.tvspielfilm.picon.value == "plugin":
						png = self.piconfolder + '%s.png' % LOGO
					else:
						png = findPicon(sref, self.piconfolder)
					if png:
						res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
					else:
						res.append(MultiContentEntryText(pos=(0, int(30 * (SCALE - 1))), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
					start = sub(' - ..:..', '', start)
					daynow = sub('....-..-', '', str(self.date))
					day = search(', ([0-9]+). ', self.datum_string)
					if day:
						day = day.group(1)
					else:
						day = daynow
					if int(day) >= int(daynow) - 1:
						date = str(self.date) + 'FIN'
					else:
						four_weeks = datetime.timedelta(weeks=4)
						date = str(self.date + four_weeks) + 'FIN'
					date = sub('[0-9][0-9]FIN', day, date)
					timer = date + ':::' + start + ':::' + str(sref)
					if timer in self.timer:
						self.rec = True
						png = ICONPATH + 'recFHD.png' if FULLHD else ICONPATH + 'rec.png'
						if fileExists(png):
							res.append(MultiContentEntryPixmapAlphaTest(pos=(self.menuwidth - int(170 * SCALE), int(7 * SCALE)), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
					self.tvlink.append(LINK)
					self.tvtitel.append(TITLE)
					if GENRE:
						titelfilter = TITLE.replace(GENRE, '')
						text = GENRE.replace(',', '\n', 1)
						res.append(MultiContentEntryText(pos=(int(760 * SCALE), 0), size=(int(400 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT | RT_VALIGN_CENTER | RT_WRAP, text=text))
					icount = 0
					for INFO in INFOS:
						if self.rec:
							self.rec = False
						else:
							png = '%s%sFHD.png' % (ICONPATH, INFO) if FULLHD else '%s%s.png' % (ICONPATH, INFO)
							if fileExists(png):
								yoffset = int(icount * 21 + (3 - len(INFOS)) * 10 + int(30 * (SCALE - 1)))
								res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1180 * SCALE), yoffset), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
								icount += 1
					self.datum = False
					if RATING:
						if RATING != 'rating small':
							RATING = RATING.replace(' ', '-')
							png = '%s%sFHD.png' % (ICONPATH, RATING) if FULLHD else '%s%s.png' % (ICONPATH, RATING)
							if fileExists(png):
								res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
					res.append(MultiContentEntryText(pos=(int(160 * SCALE), 0), size=(int(600 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text=titelfilter))
					self.tventries.append(res)
		self['menu'].l.setItemHeight(mh)
		self['menu'].l.setList(self.tventries)
		end = len(self.tventries) - 1
		self['menu'].moveToIndex(end)
		self['menu'].show()
		self.genrecount += 1
		if self.genrecount <= self.maxgenrecount and search(NEXTPage1, bereich) and self.load:
			nextpage = search(NEXTPage2, bereich)
			if nextpage:
				self.downloadFull(nextpage.group(1), self.makeTVGenreView)
			else:
				self.load = False
				self.ready = True
		else:
			self['label'].setText('OK = Sendung, Stop = YouTube Trailer')
			self['label'].stopBlinking()
			self['label'].show()
			try:
				if self.sref[-1] == 'na':
					del self.sref[-1]
					del self.tvlink[-1]
					del self.tvtitel[-1]
					del self.tventries[-1]
					self['menu'].l.setList(self.tventries)
			except IndexError:
				pass
			self['menu'].moveToIndex(self.oldindex)
			self.load = False
			self.ready = True

	def makePostviewPage(self, string):
		self['menu'].hide()
		try:
			self._makePostviewPage(string)
		except:
			printStackTrace()

	def makeSearchView(self, url):
		self._makeSearchView(url, 1, 0)

	def ok(self):
		self._ok()

	def selectPage(self, action):
		if self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				self.postlink = self.tvlink[c]
			except IndexError:
				pass

		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			try:
				self.postlink = self.searchlink[c]
			except IndexError:
				pass
		if action == 'ok' and self.ready:
			if search('www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				self.downloadPostPage(self.postlink, self.makePostviewPage)

	def stopLoad(self, answer):
		if answer is True:
			self.load = False
			self.ready = True

	def getEPG(self):
		if self.current == 'postview' and self.postviewready:
			if not self.showEPG:
				self.showEPG = True
				if not self.search:
					try:
						c = self['menu'].getSelectedIndex()
						sref = self.sref[c]
						channel = ServiceReference(eServiceReference(sref)).getServiceName()
					except IndexError:
						sref = None
						channel = ''

				else:
					try:
						c = self['searchmenu'].getSelectedIndex()
						sref = self.searchref[c]
						channel = ServiceReference(eServiceReference(sref)).getServiceName()
					except IndexError:
						sref = None
						channel = ''

				if sref:
					try:
						start = self.start
						s1 = sub(':..', '', start)
						date = str(self.postdate) + 'FIN'
						date = sub('..FIN', '', date)
						date = date + self.day
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(':..:..', '', start)
						if int(s2) > int(s1):
							start = str(self.date) + ' ' + start
						else:
							start = date + ' ' + start
						start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
						start = int(mktime(start.timetuple()))
						epgcache = eEPGCache.getInstance()
						event = epgcache.startTimeQuery(eServiceReference(sref), start)
						if event == -1:
							self.EPGText = getEPGText()

						else:
							event = epgcache.getNextTimeEntry()
							self.EPGtext = event.getEventName()
							short = event.getShortDescription()
							ext = event.getExtendedDescription()
							dur = '%d Minuten' % (event.getDuration() / 60)
							if short and short != self.EPGtext:
								self.EPGtext += '\n\n' + short
							if ext:
								self.EPGtext += '\n\n' + ext
							if dur:
								self.EPGtext += '\n\n' + dur
					except:
						self.EPGText = getEPGText()

				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n\n' + fill
				self['textpage'].setText(self.EPGtext)
				self['textpage'].show()
			else:
				self.showEPG = False
				self['textpage'].setText(self.POSTtext)
				self['textpage'].show()

	def red(self):
		if self.current == 'postview' and self.postviewready:
			if not self.search:
				self.redTimer()
			elif self.search:
				self.redTimer(True)
			else:
				self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
		elif self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.oldindex = c
			try:
				self.postlink = self.tvlink[c]
			except IndexError:
				pass

			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			try:
				self.postlink = self.searchlink[c]
			except IndexError:
				pass

			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)

	def finishedTimer(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)

				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			self.makeTimerDB()
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
			else:
				self.showsearch()
		else:
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
			else:
				self.showsearch()

	def green(self):
		if self.current == 'menu' and not self.search:
			c = self['menu'].getSelectedIndex()
			try:
				sref = self.sref[c]
				if sref != '':
					self.session.nav.playService(eServiceReference(sref))
			except IndexError:
				pass

	def yellow(self):
		if self.current == 'postview':
			self.youTube()
		elif self.current == 'menu' and not self.search and self.ready:
			try:
				c = self['menu'].getSelectedIndex()
				self.oldindex = c
				try:
					titel = self.tvtitel[c]
				except IndexError:
					pass

				if titel != 'na':
					self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Genre: ' + self.genre.replace(':', ' -') + ', Filter:', text=titel)
				else:
					self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Genre: ' + self.genre.replace(':', ' -') + ', Filter:', text='')
			except IndexError:
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Genre: ' + self.genre.replace(':', ' -') + ', Filter:', text='')

	def searchReturn(self, search):
		if search and search != '':
			self.searchstring = search
			self['menu'].hide()
			self['label'].setText('')
			self['label2'].setText('')
			self['label3'].setText('')
			self['label4'].setText('')
			self['label5'].setText('')
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = search.replace(' ', '+')
			searchlink = sub('&q=', '&q=' + search, self.link)
			self.maxsearchcount = config.plugins.tvspielfilm.maxgenre.value
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(searchYouTube, self.name, self.movie)
		elif self.current == 'menu' and not self.search and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				titel = self.tvtitel[c]
				if titel != 'na':
					self.session.open(searchYouTube, titel, self.movie)
			except IndexError:
				pass

	def gotoEnd(self):
		if self.current != 'postview' and self.ready and not self.search:
			end = len(self.tventries) - 1
			self['menu'].moveToIndex(end)
		elif self.current != 'postview' and self.ready and self.search:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

	def downloadFull(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadFullError)

	def downloadFullError(self, output):
		self['label'].setText('OK = Sendung, Stop = YouTube Trailer')
		self['label'].stopBlinking()
		self['label'].show()
		self['menu'].moveToIndex(self.oldindex)
		self.load = False
		self.ready = True

	def downloadPostPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

	def downloadFullPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

	def downloadPageError(self, output):
		self['label'].setText('OK = Sendung, Stop = YouTube Trailer')
		self['label'].stopBlinking()
		self['label'].show()
		self.ready = True

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.datum = False
		self.filter = True
		self.current = 'menu'
		self['label'].setText('Bitte warten...')
		self['label'].startBlinking()
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.sref = []
		self.genrecount = 0
		self.makeTVTimer.callback.append(self.downloadFull(self.link, self.makeTVGenreView))

	def showProgrammPage(self):
		self['label'].setText('OK = Sendung, Stop = YouTube Trailer')
		self['label2'].setText('= Timer')
		self['label3'].setText('= Filter')
		self['label4'].setText('= Zappen')
		self.infotextHide()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self._tvinfoHide()
		self.current = 'menu'
		self['menu'].show()

	def down(self):
		try:
			if self.current == 'menu':
				self['menu'].down()
			elif self.current == 'searchmenu':
				self['searchmenu'].down()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def up(self):
		try:
			if self.current == 'menu':
				self['menu'].up()
			elif self.current == 'searchmenu':
				self['searchmenu'].up()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def rightDown(self):
		try:
			if self.current == 'menu':
				self['menu'].pageDown()
			elif self.current == 'searchmenu':
				self['searchmenu'].pageDown()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def leftUp(self):
		try:
			if self.current == 'menu':
				self['menu'].pageUp()
			elif self.current == 'searchmenu':
				self['searchmenu'].pageUp()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.load:
			self.session.openWithCallback(self.stopLoad, MessageBox, '\nDie Suche ist noch nicht beendet. Soll die Suche abgebrochen und das Ergebnis angezeigt werden?', MessageBox.TYPE_YESNO)
		elif self.current == 'menu' and not self.search:
			if fileExists(self.picfile):
				remove(self.picfile)
			if fileExists(self.localhtml):
				remove(self.localhtml)
			if fileExists(self.localhtml2):
				remove(self.localhtml2)
			self.close()
		elif self.current == 'searchmenu':
			self.search = False
			self.oldsearchindex = 1
			self['searchmenu'].hide()
			self['searchtext'].hide()
			self.setTitle('')
			self.setTitle(self.titel)
			self.showProgrammPage()
		elif self.current == 'postview' and not self.search:
			self.postviewready = False
			self.setTitle('')
			self.setTitle(self.titel)
			self.showProgrammPage()
		elif self.current == 'postview' and self.search:
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


class TVJetztView(tvGenreJetztProgrammView):

	def __init__(self, session, link, standalone):
		tvGenreJetztProgrammView.__init__(self, session, link)
		self.sref = []
		self.link1 = link
		self.link2 = link
		self.standalone = standalone
		self.jetzt = False
		self.gleich = False
		self.abends = False
		self.nachts = False
		self.index = 0
		self.date = datetime.date.today()
		self._commonInit()
		self.infotextHide()
		self['actions'] = ActionMap(['OkCancelActions',
									 'DirectionActions',
									 'EPGSelectActions',
									 'NumberActions',
									 'InfobarTeletextActions',
									 'ChannelSelectBaseActions',
									 'MoviePlayerActions'], {'ok': self.ok,
															 'cancel': self.exit,
															 'right': self.rightDown,
															 'left': self.leftUp,
															 'down': self.down,
															 'up': self.up,
															 'nextBouquet': self.zap,
															 'prevBouquet': self.zap,
															 '0': self.gotoEnd,
															 '1': self.zapUp,
															 '2': self.zapDown,
															 '7': self.IMDb,
															 '8': self.TMDb,
															 '9': self.TVDb,
															 'info': self.getEPG,
															 'epg': self.getEPG,
															 'leavePlayer': self.youTube,
															 'startTeletext': self.pressText}, -1)
		self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
															'yellow': self.yellow,
															'red': self.makeTimer,
															'blue': self.hideScreen}, -1)
		self.service_db = serviceDB(self.servicefile)
		f = open(self.servicefile, 'r')
		lines = f.readlines()
		f.close()
		ordertext = ['"%s": %d, ' % (line.partition(' ')[0], i) for i, line in enumerate(lines)]
		self.order = '{' + str(''.join(ordertext)) + '}'
		if self.standalone:
			self.movie_stop = config.usage.on_movie_stop.value
			self.movie_eof = config.usage.on_movie_eof.value
			config.usage.on_movie_stop.value = 'quit'
			config.usage.on_movie_eof.value = 'quit'
			self.makeTimerDB()
		else:
			self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		if config.plugins.tvspielfilm.genreinfo.value == 'no':
			self.showgenre = False
		else:
			self.showgenre = True
		self.makeTVTimer = eTimer()
		if search('/sendungen/jetzt.html', link):
			self.jetzt = True
			self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
		elif search('time=shortly', link):
			self.gleich = True
			self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
		elif search('/sendungen/abends.html', link):
			self.abends = True
			self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
		elif search('/sendungen/fernsehprogramm-nachts.html', link):
			self.nachts = True
			self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PICPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		self.makeTVTimer.start(200, True)

	def makeTVJetztView(self, output):
		output = ensure_str(output)
		date = str(self.date.strftime('%d.%m.%Y'))
		if self.jetzt:
			self.titel = 'Jetzt'
		elif self.gleich:
			self.titel = 'Gleich'
		elif self.abends:
			self.titel = '20:15'
		else:
			self.titel = '22:00'
		self.titel = self.titel + ' im TV - Heute, ' + str(self.weekday) + ', ' + date
		self.setTitle(self.titel)
		items, bereich = parseNow(output)
		nowhour = datetime.datetime.now().hour
		if self.jetzt or self.gleich or self.abends and nowhour == 20 or self.abends and nowhour == 21 or self.nachts and nowhour == 22:
			self.progress = True
			nowminute = datetime.datetime.now().minute
			nowsec = int(nowhour) * 3600 + int(nowminute) * 60
		else:
			self.progress = False
#20:15#########################################################################################
		mh = int(41 * SCALE + 0.5)
		for LOGO, TIME, LINK, title, sparte, genre, RATING in items:
			service = LOGO
			sref = self.service_db.lookup(service)
			if sref == 'nope':
				self.filter = True
			else:
				self.filter = False
				res_sref = []
				res_sref.append(service)
				res_sref.append(sref)
				self.sref.append(res_sref)
				res = [LOGO]
				if self.backcolor:
					res.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * SCALE), mh), font=0, backcolor_sel=self.back_color, text=''))
				if config.plugins.tvspielfilm.picon.value == "plugin":
					png = self.piconfolder + '%s.png' % LOGO
				else:
					png = findPicon(sref, self.piconfolder)
				if png:
					res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
				else:
					res.append(MultiContentEntryText(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
				percent = None
				if self.progress:
					start = sub(' - ..:..', '', TIME)
					startparts = start.split(':')
					startsec = int(startparts[0]) * 3600 + int(startparts[1]) * 60
					end = sub('..:.. - ', '', TIME)
					endparts = end.split(':')
					endsec = int(endparts[0]) * 3600 + int(endparts[1]) * 60
					if endsec >= startsec:
						length = endsec - startsec
					else:
						length = 86400 - startsec + endsec
					if nowsec < startsec and endsec - nowsec > 43200:
						percent = 100
					elif nowsec < startsec and endsec > startsec:
						percent = 0
					elif endsec < startsec:
						if nowsec > startsec:
							passed = nowsec - startsec
							percent = passed * 100 / length
						elif nowsec < endsec:
							passed = 86400 - startsec + nowsec
							percent = passed * 100 / length
						elif nowsec - endsec < startsec - nowsec:
							percent = 100
						else:
							percent = 0
					elif nowsec > endsec and nowsec - endsec > 43200:
						percent = 0
					elif nowsec > endsec:
						percent = 100
					else:
						passed = nowsec - startsec
						percent = passed * 100 / length
				start = sub(' - ..:..', '', TIME)
				hour = sub(':..', '', start)
				if int(nowhour) - int(hour) > 6:
					one_day = datetime.timedelta(days=1)
					date = self.date + one_day
				else:
					date = self.date
				timer = str(date) + ':::' + start + ':::' + str(sref)
				if timer in self.timer:
					self.rec = True
					png = ICONPATH + 'recFHD.png' if FULLHD else ICONPATH + 'rec.png'
					ypos = int(24 * SCALE) if sparte else int(14 * SCALE)
					if fileExists(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1120 * SCALE), ypos), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
				res_link = []
				res_link.append(service)
				res_link.append(LINK)
				self.tvlink.append(res_link)
				if title:
					if self.showgenre and genre:
						x = title + " " + genre
					else:
						x = title
					res_titel = []
					res_titel.append(service)
					res_titel.append(title)
					self.tvtitel.append(res_titel)
					res.append(MultiContentEntryText(pos=(int(74 * SCALE), 0), size=(int(110 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=TIME))
					if self.progress or percent:
						res.append(MultiContentEntryProgress(pos=(int(85 * SCALE), int(32 * SCALE)), size=(int(100 * SCALE), int(6 * SCALE)), percent=percent, borderWidth=1, foreColor=16777215))
					res.append(MultiContentEntryText(pos=(int(200 * SCALE), 0), size=(int(860 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
				if sparte:
					valign = RT_HALIGN_RIGHT if self.rec else RT_HALIGN_RIGHT | RT_VALIGN_CENTER
					res.append(MultiContentEntryText(pos=(int(1040 * SCALE), 0), size=(int(120 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=valign, text=sparte))
				if self.rec:
					self.rec = False
				if RATING != 'rating small':
					RATING = RATING.replace(' ', '-')
					png = '%s%sFHD.png' % (ICONPATH, RATING) if FULLHD else '%s%s.png' % (ICONPATH, RATING)
					if fileExists(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
				self.tventries.append(res)
		order = eval(self.order)
		self.sref = sorted(self.sref, key=lambda x: order[x[0]])
		self.tvlink = sorted(self.tvlink, key=lambda x: order[x[0]])
		self.tvtitel = sorted(self.tvtitel, key=lambda x: order[x[0]])
		self.tventries = sorted(self.tventries, key=lambda x: order[x[0]])
		self['menu'].l.setItemHeight(mh)
		self['menu'].l.setList(self.tventries)
		if self.jetzt:
			nextpage = search(NEXTPage2, bereich)
			if nextpage:
				self.downloadFull(nextpage.group(1), self.makeTVJetztView)
			else:
				self['menu'].moveToIndex(self.index)
				self.ready = True
				self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
				self['label'].stopBlinking()
				self['label'].show()
		elif self.gleich:
			if search('<a href=".*?tvspielfilm.de/tv-programm/sendungen/.*?page=[2-9]', bereich):
				nextpage = search(NEXTPage2, bereich)
				if nextpage:
					self.downloadFull(nextpage.group(1), self.makeTVJetztView)
			else:
				self['menu'].moveToIndex(self.index)
				self.ready = True
				self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
				self['label'].stopBlinking()
				self['label'].show()
		elif search('<a href=".*?tvspielfilm.de/tv-programm/sendungen/.*?page=[2-9]', bereich):
			nextpage = search(NEXTPage2, bereich)
			if nextpage:
				self.downloadFull(nextpage.group(1), self.makeTVJetztView)
		else:
			self['menu'].moveToIndex(self.index)
			self.ready = True
			self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
			self['label'].stopBlinking()
			self['label'].show()

	def makePostviewPage(self, string):
		self['menu'].hide()
		try:
			self._makePostviewPage(string)
		except:
			printStackTrace()

	def makeSearchView(self, url):
		self._makeSearchView(url)

	def ok(self):
		self._ok()

	def selectPage(self, action):
		if self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				self.postlink = self.tvlink[c][1]
			except IndexError:
				pass

		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			try:
				self.postlink = self.searchlink[c]
			except IndexError:
				pass

		if action == 'ok' and self.ready:
			if search('www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				self.downloadPostPage(self.postlink, self.makePostviewPage)

	def getEPG(self):
		if self.current == 'postview' and self.postviewready:
			if not self.showEPG:
				self.showEPG = True
				if not self.search:
					try:
						c = self['menu'].getSelectedIndex()
						sref = self.sref[c][1]
						channel = ServiceReference(eServiceReference(sref)).getServiceName()
					except IndexError:
						sref = None
						channel = ''

				else:
					try:
						c = self['searchmenu'].getSelectedIndex()
						sref = self.searchref[c]
						channel = ServiceReference(eServiceReference(sref)).getServiceName()
					except IndexError:
						sref = None
						channel = ''

				if sref:
					try:
						start = self.start
						s1 = sub(':..', '', start)
						date = str(self.postdate) + 'FIN'
						date = sub('..FIN', '', date)
						date = date + self.day
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(':..:..', '', start)
						if int(s2) > int(s1):
							start = str(self.date) + ' ' + start
						else:
							start = date + ' ' + start
						start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
						start = int(mktime(start.timetuple()))
						epgcache = eEPGCache.getInstance()
						event = epgcache.startTimeQuery(eServiceReference(sref), start)
						if event == -1:
							self.EPGText = getEPGText()

						else:
							event = epgcache.getNextTimeEntry()
							self.EPGtext = event.getEventName()
							short = event.getShortDescription()
							ext = event.getExtendedDescription()
							dur = '%d Minuten' % (event.getDuration() / 60)
							if short and short != self.EPGtext:
								self.EPGtext += '\n\n' + short
							if ext:
								self.EPGtext += '\n\n' + ext
							if dur:
								self.EPGtext += '\n\n' + dur
					except:
						self.EPGText = getEPGText()

				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n\n' + fill
				self['textpage'].setText(self.EPGtext)
				self['textpage'].show()
			else:
				self.showEPG = False
				self['textpage'].setText(self.POSTtext)
				self['textpage'].show()
		elif self.current == 'menu' and self.ready and not self.search:
			self.ready = False
			self.tventries = []
			self.tvlink = []
			self.tvtitel = []
			self.sref = []
			if self.jetzt:
				self.jetzt = False
				self.gleich = True
				self['label'].setText('Bitte warten...')
				self['label'].startBlinking()
				link = self.baseurl + '/tv-programm/sendungen/?page=1&order=time&time=shortly'
				self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
			else:
				self.jetzt = True
				self.gleich = False
				self.abends = False
				self.nachts = False
				self['label'].setText('Bitte warten...')
				self['label'].startBlinking()
				link = self.baseurl + '/tv-programm/sendungen/jetzt.html'
				self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))

	def red(self):
		if self.current == 'postview' and self.postviewready:
			if not self.search:
				try:
					c = self['menu'].getSelectedIndex()
					self.oldindex = c
					sref = self.sref[c][1]
					self.redTimer(False, sref)
				except IndexError:
					self.redTimer(False)
			elif self.search:
				try:
					c = self['searchmenu'].getSelectedIndex()
					self.oldsearchindex = c
					sref = self.searchref[c]
					self.redTimer(False, sref)
				except IndexError:
					self.redTimer(False)
			else:
				self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
		elif self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.oldindex = c
			try:
				self.postlink = self.tvlink[c][0]
			except IndexError:
				pass

			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.index = self.oldindex
				self.download(self.postlink, self.makePostTimer)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			try:
				self.postlink = self.searchlink[c]
			except IndexError:
				pass

			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)

	def finishedTimer(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)

				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			self.makeTimerDB()
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
				self.refresh()
			else:
				self.showsearch()
		else:
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
			else:
				self.showsearch()

	def green(self):
		if self.current == 'menu' and not self.search:
			c = self['menu'].getSelectedIndex()
			try:
				sref = self.sref[c][1]
				if sref != '':
					self.session.nav.playService(eServiceReference(sref))
					if config.plugins.tvspielfilm.zapexit.value == 'yes' and self.standalone:
						self.close()
			except IndexError:
				pass

	def yellow(self):
		if self.current == 'postview':
			self.youTube()
		elif self.current == 'menu' and not self.search and self.ready:
			try:
				c = self['menu'].getSelectedIndex()
				self.oldindex = c
				try:
					titel = self.tvtitel[c][1]
				except IndexError:
					pass
					titel = ''

				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
			except IndexError:
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

	def searchReturn(self, search):
		if search and search != '':
			self.searchstring = search
			self['menu'].hide()
			self['label'].setText('')
			self['label2'].setText('')
			self['label3'].setText('')
			self['label4'].setText('')
			self['label5'].setText('')
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = search.replace(' ', '+')
			searchlink = self.baseurl + '/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=' + search + '&page=1'
			self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		if self.current == 'menu' and self.ready:
			try:
				c = self['menu'].getSelectedIndex()
				channel = self.sref[c][0]
				link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
				self.session.open(TVProgrammView, link, True, False)
			except IndexError:
				pass
		else:
			self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(searchYouTube, self.name, self.movie)
		elif self.current == 'menu' and not self.search and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				titel = self.tvtitel[c][1]
				self.session.open(searchYouTube, titel, self.movie)
			except IndexError:
				pass

	def gotoEnd(self):
		if self.current != 'postview' and self.ready and not self.search:
			end = len(self.tventries) - 1
			self['menu'].moveToIndex(end)
		elif self.current != 'postview' and self.ready and self.search:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

	def downloadFull(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadFullError)

	def downloadFullError(self, output):
		try:
			self['label'].setText('Text = Sender,        Info = Jetzt im TV/Gleich im TV')
			self['label'].stopBlinking()
			self['label'].show()
		except:
			pass
		self.ready = True

	def downloadPostPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

	def downloadFullPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

	def downloadPageError(self, output):
		try:
			self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
			self['label'].stopBlinking()
			self['label'].show()
		except:
			pass
		self.ready = True

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['label'].setText('Bitte warten...')
		self['label'].startBlinking()
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.sref = []
		if self.jetzt:
			link = self.baseurl + '/tv-programm/sendungen/jetzt.html'
			self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
		elif self.gleich:
			link = self.baseurl + '/tv-programm/sendungen/?page=1&order=time&time=shortly'
			self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
		elif self.abends:
			link = self.baseurl + '/tv-programm/sendungen/abends.html'
			self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
		else:
			link = self.baseurl + '/tv-programm/sendungen/fernsehprogramm-nachts.html'
			self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))

	def showProgrammPage(self):
		self['label'].setText('Text = Sender, Info = Jetzt im TV/Gleich im TV')
		self['label2'].setText('= Timer')
		self['label3'].setText('= Suche')
		self['label4'].setText('= Zappen')
		self.infotextHide()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self._tvinfoHide()
		self.current = 'menu'
		self['menu'].show()

	def down(self):
		try:
			if self.current == 'menu':
				self['menu'].down()
			elif self.current == 'searchmenu':
				self['searchmenu'].down()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def up(self):
		try:
			if self.current == 'menu':
				self['menu'].up()
			elif self.current == 'searchmenu':
				self['searchmenu'].up()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def rightDown(self):
		try:
			if self.current == 'menu':
				self['menu'].pageDown()
			elif self.current == 'searchmenu':
				self['searchmenu'].pageDown()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def leftUp(self):
		try:
			if self.current == 'menu':
				self['menu'].pageUp()
			elif self.current == 'searchmenu':
				self['searchmenu'].pageUp()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.current == 'menu' and not self.search:
			if fileExists(self.picfile):
				remove(self.picfile)
			if fileExists(self.localhtml):
				remove(self.localhtml)
			if fileExists(self.localhtml2):
				remove(self.localhtml2)
			if self.standalone:
				config.usage.on_movie_stop.value = self.movie_stop
				config.usage.on_movie_eof.value = self.movie_eof
			self.close()
		elif self.current == 'searchmenu':
			self.search = False
			self.oldsearchindex = 1
			self['searchmenu'].hide()
			self['searchtext'].hide()
			self.setTitle('')
			self.setTitle(self.titel)
			self.showProgrammPage()
		elif self.current == 'postview' and not self.search:
			self.postviewready = False
			self.setTitle('')
			self.setTitle(self.titel)
			self.showProgrammPage()
		elif self.current == 'postview' and self.search:
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


class TVProgrammView(tvGenreJetztProgrammView):

	def __init__(self, session, link, eventview, tagestipp):
		tvGenreJetztProgrammView.__init__(self, session, link)
		self.eventview = eventview
		self.tagestipp = tagestipp
		self.service_db = serviceDB(self.servicefile)
		if not self.tagestipp:
			channel = findall(',(.*?).html', link)
			service = channel[0]
			self.sref = self.service_db.lookup(service)
			if self.sref == 'nope':
				self.zap = False
				self.picon = False
			else:
				self.zap = True
				if self.picon:
					self.piconname = findPicon(self.sref, self.piconfolder)
					if self.piconname is None:
						self.picon = False
		self.link = link
		self.primetime = False
		if not self.eventview:
			self._commonInit()
		else:
			self._commonInit('= Suche', '= Refresh')
		self.infotextHide()
		self['actions'] = ActionMap(['OkCancelActions',
									 'ChannelSelectBaseActions',
									 'DirectionActions',
									 'EPGSelectActions',
									 'InfobarTeletextActions',
									 'NumberActions',
									 'MoviePlayerActions'], {'ok': self.ok,
															 'cancel': self.exit,
															 'right': self.rightDown,
															 'left': self.leftUp,
															 'down': self.down,
															 'up': self.up,
															 'nextBouquet': self.nextDay,
															 'prevBouquet': self.prevDay,
															 'nextMarker': self.nextWeek,
															 'prevMarker': self.prevWeek,
															 '0': self.gotoEnd,
															 '1': self.zapUp,
															 '2': self.zapDown,
															 '7': self.IMDb,
															 '8': self.TMDb,
															 '9': self.TVDb,
															 'info': self.getEPG,
															 'epg': self.getEPG,
															 'leavePlayer': self.youTube,
															 'startTeletext': self.pressText}, -1)
		self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
															'yellow': self.yellow,
															'red': self.makeTimer,
															'blue': self.hideScreen}, -1)
		self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		if config.plugins.tvspielfilm.genreinfo.value == 'no':
			self.showgenre = False
		else:
			self.showgenre = True
		if self.eventview:
			self.movie_stop = config.usage.on_movie_stop.value
			self.movie_eof = config.usage.on_movie_eof.value
			config.usage.on_movie_stop.value = 'quit'
			config.usage.on_movie_eof.value = 'quit'
			from Components.ServiceEventTracker import ServiceEventTracker
			from enigma import iPlayableService
			self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evUpdatedEventInfo: self.zapRefresh})
			self.channel_db = channelDB(self.servicefile)
		elif not self.tagestipp:
			nextday = sub('/sendungen/.*?html', '/sendungen/?page=1&order=time&date=', self.link)
			nextday = nextday + str(self.date)
			nextday = nextday + '&tips=0&time=day&channel=' + channel[0]
			self.link = nextday
		self.makeTVTimer = eTimer()
		if not self.tagestipp:
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVProgrammView))
		else:
			self.current = 'postview'
			self['label'].stopBlinking()
			self['label'].show()
			self.makeTVTimer.callback.append(self.downloadPostPage(self.link, self.makePostviewPage))
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PICPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		self.makeTVTimer.start(200, True)

	def makeTVProgrammView(self, string):
		output = open(self.localhtml, 'r').read()
		output = ensure_str(output)
		titel = search('<title>(.*?)von', output)
		date = str(self.date.strftime('%d.%m.%Y'))
		self.titel = str(titel.group(1)) + ' - ' + str(self.weekday) + ', ' + date
		self.setTitle(self.titel)
		items, bereich = parseNow(output)
		today = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		yesterday = today - one_day
		nowhour = datetime.datetime.now().hour
		if self.date == today and nowhour > 4 or self.date == yesterday and nowhour < 5:
			self.progress = True
			nowminute = datetime.datetime.now().minute
			nowsec = int(nowhour) * 3600 + int(nowminute) * 60
		else:
			self.progress = False
			self.percent = False
		mh = int(41 * SCALE + 0.5)
		for LOGO, TIME, LINK, TITEL, SPARTE, GENRE, RATING in items:
			res = [LOGO]
			service = LOGO
			sref = self.service_db.lookup(service)
			if self.backcolor:
				res.append(MultiContentEntryText(pos=(0, 0), size=(self.menuwidth, mh), font=0, backcolor_sel=self.back_color, text=''))
			if config.plugins.tvspielfilm.picon.value == "plugin":
				png = self.piconfolder + '%s.png' % LOGO
			else:
				png = findPicon(sref, self.piconfolder)
			if png:
				res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
			else:
				res.append(MultiContentEntryText(pos=(0, 0), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
			if self.progress:
				start = sub(' - ..:..', '', TIME)
				startparts = start.split(':')
				startsec = int(startparts[0]) * 3600 + int(startparts[1]) * 60
				end = sub('..:.. - ', '', TIME)
				endparts = end.split(':')
				endsec = int(endparts[0]) * 3600 + int(endparts[1]) * 60
				if endsec >= startsec:
					length = endsec - startsec
				else:
					length = 86400 - startsec + endsec
				if nowsec < startsec and endsec > startsec:
					percent = 0
					self.percent = False
				elif endsec < startsec:
					if nowsec > startsec:
						passed = nowsec - startsec
						percent = passed * 100 / length
						self.percent = True
					elif nowsec < endsec:
						passed = 86400 - startsec + nowsec
						percent = passed * 100 / length
						self.percent = True
					elif nowsec - endsec < startsec - nowsec:
						percent = 100
						self.percent = False
					else:
						percent = 0
						self.percent = False
				elif nowsec > endsec:
					percent = 100
					self.percent = False
				else:
					passed = nowsec - startsec
					percent = passed * 100 / length
					self.percent = True
			if search('20:15 -', TIME) or self.percent:
				self.primetime = True
			else:
				self.primetime = False
			start = sub(' - ..:..', '', TIME)
			hour = sub(':..', '', start)
			if int(hour) < 5 and len(self.tventries) > 6 or int(hour) < 5 and self.eventview:
				one_day = datetime.timedelta(days=1)
				date = self.date + one_day
			else:
				date = self.date
			timer = str(date) + ':::' + start + ':::' + str(self.sref)
			if timer in self.timer:
				self.rec = True
				png = ICONPATH + 'recFHD.png' if FULLHD else ICONPATH + 'rec.png'
				if fileExists(png):
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1120 * SCALE), int(14 * SCALE)), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
			self.tvlink.append(LINK)
			t = TITEL
			if self.showgenre and GENRE:
				x = t + " " + GENRE
			else:
				x = t
			self.tvtitel.append(t)
			res.append(MultiContentEntryText(pos=(int(74 * SCALE), 0), size=(int(110 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=TIME))
			if self.progress and self.percent:
				res.append(MultiContentEntryProgress(pos=(int(85 * SCALE), int(32 * SCALE)), size=(int(100 * SCALE), int(6 * SCALE)), percent=percent, borderWidth=1, foreColor=16777215))
			res.append(MultiContentEntryText(pos=(int(200 * SCALE), 0), size=(int(860 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
			if SPARTE:
				stext = SPARTE.replace('<br/>', '')
				res.append(MultiContentEntryText(pos=(int(1040 * SCALE), 0), size=(int(120 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text=SPARTE))
			if self.rec:
				self.rec = False
			if RATING != 'rating small':
				RATING = RATING.replace(' ', '-')
				png = '%s%sFHD.png' % (ICONPATH, RATING) if FULLHD else '%s%s.png' % (ICONPATH, RATING)
				if fileExists(png):
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1180 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
			self.tventries.append(res)
		self['menu'].l.setItemHeight(mh)
		self['menu'].l.setList(self.tventries)
		self['menu'].moveToIndex(self.oldindex)
		if search(NEXTPage1, bereich):
			link = search(NEXTPage2, bereich)
			if link:
				self.makeTVTimer.callback.append(self.downloadFullPage(link.group(1), self.makeTVProgrammView))
			else:
				self.ready = True
		else:
			self.ready = True
			if not self.eventview:
				self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
				self['label'].stopBlinking()
				self['label'].show()
			else:
				self['label'].setText('Bouquet = +- Tag, <> = +- Woche, 1/2 = Zap Up/Down')
				self['label'].stopBlinking()
				self['label'].show()
		if self.eventview and config.plugins.tvspielfilm.eventview.value == 'info':
			self.postlink = self.tvlink[1]
			if search('www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				self.downloadPostPage(self.postlink, self.makePostviewPage)
			else:
				self.ready = True

	def makePostviewPage(self, string):
		self['menu'].hide()
		try:
			self._makePostviewPage(string)
		except:
			printStackTrace()

	def makeSearchView(self, url):
		self._makeSearchView(url)

	def ok(self):
		self._ok()

	def selectPage(self, action):
		if self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				self.postlink = self.tvlink[c]
			except IndexError:
				pass

		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			try:
				self.postlink = self.searchlink[c]
			except IndexError:
				pass

		if action == 'ok' and self.ready:
			if search('www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				self.downloadPostPage(self.postlink, self.makePostviewPage)

	def getEPG(self):
		if self.current == 'postview' and self.postviewready:
			if not self.showEPG:
				self.showEPG = True
				if self.zap and not self.search:
					sref = self.sref
					channel = ServiceReference(eServiceReference(sref)).getServiceName()
				elif self.search:
					try:
						c = self['searchmenu'].getSelectedIndex()
						sref = self.searchref[c]
						channel = ServiceReference(eServiceReference(sref)).getServiceName()
					except IndexError:
						sref = None
						channel = ''

				else:
					sref = None
					channel = ''
				if sref:
					try:
						start = self.start
						s1 = sub(':..', '', start)
						date = str(self.postdate) + 'FIN'
						date = sub('..FIN', '', date)
						date = date + self.day
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(':..:..', '', start)
						if int(s2) > int(s1):
							start = str(self.date) + ' ' + start
						else:
							start = date + ' ' + start
						start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
						start = int(mktime(start.timetuple()))
						epgcache = eEPGCache.getInstance()
						event = epgcache.startTimeQuery(eServiceReference(sref), start)
						if event == -1:
							self.EPGText = getEPGText()

						else:
							event = epgcache.getNextTimeEntry()
							self.EPGtext = event.getEventName()
							short = event.getShortDescription()
							ext = event.getExtendedDescription()
							dur = '%d Minuten' % (event.getDuration() / 60)
							if short and short != self.EPGtext:
								self.EPGtext += '\n\n' + short
							if ext:
								self.EPGtext += '\n\n' + ext
							if dur:
								self.EPGtext += '\n\n' + dur
					except:
						self.EPGText = getEPGText()

				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n\n' + fill
				self['textpage'].setText(self.EPGtext)
				self['textpage'].show()
			else:
				self.showEPG = False
				self['textpage'].setText(self.POSTtext)
				self['textpage'].show()

	def red(self):
		if self.current == 'postview' and self.postviewready:
			if self.zap and not self.search:
				try:
					c = self['menu'].getSelectedIndex()
					self.oldindex = c
					sref = self.sref
					self.redTimer(False, sref)
				except IndexError:
					self.redTimer(False)
			elif self.search:
				try:
					c = self['searchmenu'].getSelectedIndex()
					self.oldsearchindex = c
					sref = self.searchref[c]
					self.redTimer(False, sref)
				except IndexError:
					self.redTimer(False)
			else:
				self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
		elif self.current == 'menu' and self.ready and self.zap:
			c = self['menu'].getSelectedIndex()
			self.oldindex = c
			try:
				self.postlink = self.tvlink[c]
			except IndexError:
				pass

			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			try:
				self.postlink = self.searchlink[c]
			except IndexError:
				pass

			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)
		else:
			self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)

	def finishedTimer(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)

				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			self.makeTimerDB()
			if not self.tagestipp:
				self.ready = True
				self.postviewready = False
				self.current = self.oldcurrent
				if not self.search:
					self.showProgrammPage()
					self.refresh()
				else:
					self.showsearch()
		elif not self.tagestipp:
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
			else:
				self.showsearch()

	def green(self):
		if self.current == 'menu' and self.zap and not self.eventview and not self.search:
			c = self['menu'].getSelectedIndex()
			try:
				sref = self.sref
				if sref != '':
					self.session.nav.playService(eServiceReference(sref))
			except IndexError:
				pass

		elif self.current == 'menu' and self.eventview and not self.search:
			sref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())
			sref = str(sref) + 'FIN'
			sref = sub(':0:0:0:.*?FIN', ':0:0:0:', sref)
			self.sref = sref
			channel = self.channel_db.lookup(sref)
			if channel == 'nope':
				self.session.open(MessageBox, 'Service nicht gefunden:\nKein Eintrag für aktuelle Servicereferenz\n%s' % str(sref), MessageBox.TYPE_INFO, close_on_any_key=True)
			else:
				if self.picon:
					self.piconname = findPicon(sref, self.piconfolder)
					if self.piconname is None:
						self.piconname = 'none.png'
				self.link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
				self.refresh()

	def yellow(self):
		if self.current == 'postview':
			self.youTube()
		elif self.current == 'menu' and not self.search and self.ready:
			try:
				c = self['menu'].getSelectedIndex()
				self.oldindex = c
				titel = self.tvtitel[c]
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
			except IndexError:
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

	def searchReturn(self, search):
		if search and search != '':
			self.searchstring = search
			self['menu'].hide()
			self['label'].setText('')
			self['label2'].setText('')
			self['label3'].setText('')
			self['label4'].setText('')
			self['label5'].setText('')
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = search.replace(' ', '+')
			searchlink = self.baseurl + '/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=' + search + '&page=1'
			self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(searchYouTube, self.name, self.movie)
		elif self.current == 'menu' and not self.search and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				titel = self.tvtitel[c]
				self.session.open(searchYouTube, titel, self.movie)
			except IndexError:
				pass

	def nextDay(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('time&date', self.link):
				date1 = findall('time&date=(.*?)-..-..&tips', self.link)
				date2 = findall('time&date=....-(.*?)-..&tips', self.link)
				date3 = findall('time&date=....-..-(.*?)&tips', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()
			else:
				self.link = sub('.html', '', self.link)
				self.link = sub('&page=0,', '?page=0&order=time&date=channel=', self.link)
				today = datetime.date.today()
			one_day = datetime.timedelta(days=1)
			tomorrow = today + one_day
			self.weekday = makeWeekDay(tomorrow.weekday())
			self.link = self.link + 'FIN'
			channel = findall('channel=(.*?)FIN', self.link)
			nextday = sub('[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
			nextday = nextday + str(tomorrow)
			nextday = nextday + '&tips=0&time=day&channel=' + channel[0]
			self.date = tomorrow
			one_day = datetime.timedelta(days=1)
			self.nextdate = self.date + one_day
			self.link = nextday
			self.oldindex = 0
			self.refresh()
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def prevDay(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('time&date', self.link):
				date1 = findall('time&date=(.*?)-..-..&tips', self.link)
				date2 = findall('time&date=....-(.*?)-..&tips', self.link)
				date3 = findall('time&date=....-..-(.*?)&tips', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

			else:
				self.link = sub('.html', '', self.link)
				self.link = sub('&page=0,', '?page=0&order=time&date=channel=', self.link)
				today = datetime.date.today()
			one_day = datetime.timedelta(days=1)
			yesterday = today - one_day
			self.weekday = makeWeekDay(yesterday.weekday())
			self.link = self.link + 'FIN'
			channel = findall('channel=(.*?)FIN', self.link)
			prevday = sub('[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
			prevday = prevday + str(yesterday)
			prevday = prevday + '&tips=0&time=day&channel=' + channel[0]
			self.date = yesterday
			one_day = datetime.timedelta(days=1)
			self.nextdate = self.date + one_day
			self.link = prevday
			self.oldindex = 0
			self.refresh()
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def nextWeek(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('time&date', self.link):
				date1 = findall('time&date=(.*?)-..-..&tips', self.link)
				date2 = findall('time&date=....-(.*?)-..&tips', self.link)
				date3 = findall('time&date=....-..-(.*?)&tips', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

			else:
				self.link = sub('.html', '', self.link)
				self.link = sub('&page=0,', '?page=0&order=time&date=channel=', self.link)
				today = datetime.date.today()
			one_week = datetime.timedelta(days=7)
			tomorrow = today + one_week
			self.weekday = makeWeekDay(tomorrow.weekday())
			self.link = self.link + 'FIN'
			channel = findall('channel=(.*?)FIN', self.link)
			nextweek = sub('[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
			nextweek = nextweek + str(tomorrow)
			nextweek = nextweek + '&tips=0&time=day&channel=' + channel[0]
			self.date = tomorrow
			one_week = datetime.timedelta(days=7)
			self.nextdate = self.date + one_week
			self.link = nextweek
			self.oldindex = 0
			self.refresh()

	def prevWeek(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('time&date', self.link):
				date1 = findall('time&date=(.*?)-..-..&tips', self.link)
				date2 = findall('time&date=....-(.*?)-..&tips', self.link)
				date3 = findall('time&date=....-..-(.*?)&tips', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

			else:
				self.link = sub('.html', '', self.link)
				self.link = sub('&page=0,', '?page=0&order=time&date=channel=', self.link)
				today = datetime.date.today()
			one_week = datetime.timedelta(days=7)
			yesterday = today - one_week
			self.weekday = makeWeekDay(yesterday.weekday())
			self.link = self.link + 'FIN'
			channel = findall('channel=(.*?)FIN', self.link)
			prevweek = sub('[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
			prevweek = prevweek + str(yesterday)
			prevweek = prevweek + '&tips=0&time=day&channel=' + channel[0]
			self.date = yesterday
			one_week = datetime.timedelta(days=7)
			self.nextdate = self.date + one_week
			self.link = prevweek
			self.oldindex = 0
			self.refresh()

	def gotoEnd(self):
		if self.current != 'postview' and self.ready and not self.search:
			end = len(self.tventries) - 1
			self['menu'].moveToIndex(end)
		elif self.current != 'postview' and self.ready and self.search:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

	def downloadPostPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

	def downloadFullPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

	def downloadPageError(self, output):
		if not self.eventview:
			self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
			self['label'].stopBlinking()
			self['label'].show()
		else:
			self['label'].setText('Bouquet = +- Tag, <> = +- Woche, 1/2 = Zap Up/Down')
			self['label'].stopBlinking()
			self['label'].show()
		self.ready = True

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['label'].setText('Bitte warten...')
		self['label'].startBlinking()
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVProgrammView))

	def showProgrammPage(self):
		if not self.eventview:
			self['label'].setText('Bouquet = +- Tag, <> = +- Woche')
			self['label2'].setText('= Timer')
			self['label3'].setText('= Suche')
			self['label4'].setText('= Zappen')
		else:
			self['label'].setText('Bouquet = +- Tag, <> = +- Woche, 1/2 = Zap Up/Down')
			self['label2'].setText('= Timer')
			self['label3'].setText('= Suche')
			self['label4'].setText('= Refresh')
		self.infotextHide()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self._tvinfoHide()
		self.current = 'menu'
		self['menu'].show()

	def down(self):
		try:
			if self.current == 'menu':
				self['menu'].down()
			elif self.current == 'searchmenu':
				self['searchmenu'].down()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def up(self):
		try:
			if self.current == 'menu':
				self['menu'].up()
			elif self.current == 'searchmenu':
				self['searchmenu'].up()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def rightDown(self):
		try:
			if self.current == 'menu':
				self['menu'].pageDown()
			elif self.current == 'searchmenu':
				self['searchmenu'].pageDown()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def leftUp(self):
		try:
			if self.current == 'menu':
				self['menu'].pageUp()
			elif self.current == 'searchmenu':
				self['searchmenu'].pageUp()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def zapRefresh(self):
		if self.current == 'menu' and self.eventview and not self.search:
			sref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())
			sref = str(sref) + 'FIN'
			sref = sub(':0:0:0:.*?FIN', ':0:0:0:', sref)
			self.sref = sref
			channel = self.channel_db.lookup(sref)
			if channel == 'nope':
				self.session.open(MessageBox, 'Service nicht gefunden:\nKein Eintrag für aktuelle Servicereferenz\n%s' % str(sref), MessageBox.TYPE_INFO, close_on_any_key=True)
			else:
				if self.picon:
					self.piconname = findPicon(sref, self.piconfolder)
					if self.piconname is None:
						self.piconname = 'none.png'
				self.link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
				self.refresh()

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.current == 'menu':
			if fileExists(self.picfile):
				remove(self.picfile)
			if fileExists(self.localhtml):
				remove(self.localhtml)
			if fileExists(self.localhtml2):
				remove(self.localhtml2)
			if self.eventview:
				config.usage.on_movie_stop.value = self.movie_stop
				config.usage.on_movie_eof.value = self.movie_eof
			self.close()
		elif self.current == 'searchmenu':
			self.search = False
			self.oldsearchindex = 1
			self['searchmenu'].hide()
			self['searchtext'].hide()
			self.showProgrammPage()
			self.setTitle('')
			self.setTitle(self.titel)
		elif self.current == 'postview' and not self.search:
			if self.tagestipp:
				self.close()
			else:
				self.postviewready = False
				self.setTitle('')
				self.setTitle(self.titel)
				self.showProgrammPage()
		elif self.current == 'postview' and self.search:
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


class TVTrailerBilder(tvBaseScreen):

	def __init__(self, session, link, sparte):
		global HIDEFLAG
		skin = readSkin("TVTrailerBilder")
		tvBaseScreen.__init__(self, session, skin)
		self.sparte = sparte
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.picurllist = []
		HIDEFLAG = True
		self.charts = False
		self.ready = False
		self.len = 0
		self.oldindex = 0
		self['release'] = Label(RELEASE)
		self['release'].show()
		for i in range(6):
			self['pic%s' % i] = Pixmap()
			self['play%s' % i] = Pixmap()
		self['menu'] = ItemList([])
		self['label'] = Label('OK = Zum Video')
		if sparte == '_pic':
			self['label'] = Label('OK = Zur Bildergalerie')
			self.title = 'Bildergalerien - TV Spielfilm'
		else:
			self.title = 'Trailer - Video - TV Spielfilm'
		self.initBlueButton('= Aus-/Einblenden')
		self['actions'] = ActionMap(['OkCancelActions',
									 'DirectionActions',
									 'ColorActions',
									 'NumberActions'], {'ok': self.ok,
														'cancel': self.exit,
														'right': self.rightDown,
														'left': self.leftUp,
														'down': self.down,
														'up': self.up,
														'blue': self.hideScreen,
														'0': self.gotoEnd}, -1)
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		self.makeTVTimer = eTimer()
		if sparte == '_pic':
			self.makeTVTimer.callback.append(self.downloadFullPage(link, self.makeTVGalerie))
		else:
			self.makeTVTimer.callback.append(self.downloadFullPage(link, self.makeTVTrailer))
		self.makeTVTimer.start(200, True)

	def makestart(self):
		for i in range(6):
			self['pic%s' % i].hide()
			self['play%s' % i].hide()

	def makeTVGalerie(self, string):
		output = open(self.localhtml, 'r').read()
		output = ensure_str(output)
		self.makestart()
		startpos = output.find('<p class="headline headline--section">')
		endpos = output.find('<div id="gtm-livetv-footer"></div>')
		bereich = output[startpos:endpos]
		bereich = transHTML(bereich)
		date = str(self.date.strftime('%d.%m.%Y'))
		self.titel = str(self.weekday) + ', ' + date
		self.setTitle(self.titel)
		bereich = sub('<a href="', '<td>LINK', bereich)
		bereich = sub('" target="', '</td>', bereich)
		bereich = sub('<img src="', '<td>PIC', bereich)
		bereich = sub('.jpg"', '.jpg</td>', bereich)
		bereich = sub('.png"', '.png</td>', bereich)
		bereich = sub('<span class="headline">', '<td>TITEL', bereich)
		bereich = sub('</span>', '</td>', bereich)
		a = findall('<td>(.*?)</td>', bereich)
		y = 0
		mh = int(41 * SCALE + 0.5)
		offset = 3
		for x in a:
			if y == 0:
				res = [x]
				if self.backcolor:
					res.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * SCALE), mh), font=0, backcolor_sel=self.back_color, text=''))
				x = sub('LINK', '', x)
				self.tvlink.append(x)
			if y == 1:
				x = sub('PIC', '', x)
				self.picurllist.append(x)
			if y == 2:
				x = sub('TITEL', '', x)
				res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(10 * SCALE)), size=(int(1140 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
				png = ICONPATH + 'picFHD.png' if FULLHD else ICONPATH + 'pic.png'
				if fileExists(png):
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1180 * SCALE), int(10 * SCALE)), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
				self.tventries.append(res)
			y += 1
			if y == offset:
				y = 0
		self['menu'].l.setItemHeight(mh)
		self['menu'].l.setList(self.tventries)
		self['menu'].moveToIndex(self.oldindex)
		if self.oldindex > 5:
			self.leftUp()
			self.rightDown()
		self.len = len(self.tventries)
		self.ready = True
		playlogo = ICONPATH + 'playFHD.png' if FULLHD else ICONPATH + 'play.png'
		if fileExists(playlogo):
			for i in range(6):
				self.showPlays(playlogo, i)
				self['play%s' % i].show()
		self.GetPics(self.picurllist, 0)

	def makeTVTrailer(self, string):
		output = open(self.localhtml, 'r').read()
		output = ensure_str(output)
		self.makestart()
		if self.sparte == 'Kino Neustarts':
			startpos = output.find('<p class="headline headline--section">Kino Neustarts</p>')
			endpos = output.find('<div class="OUTBRAIN"')
		elif self.sparte == 'Kino Vorschau':
			startpos = output.find('<h2 class="headline headline--section">Neustarts')
			endpos = output.find('</section>')
		elif self.sparte == 'Neueste Trailer':
			startpos = output.find('<p class="headline headline--section">Neueste Trailer</p>')
			endpos = output.find('<p class="headline headline--section">Kino Neustarts</p>')
		elif self.sparte == 'Kino Charts':
			self.charts = True
			startpos = output.find('<ul class="chart-content charts-list-content">')
			endpos = output.find('footer')
		elif self.sparte == 'DVD Charts':
			self.charts = True
			startpos = output.find('<ul class="chart-content charts-list-content">')
			endpos = output.find('footer')
		bereich = output[startpos:endpos]
		bereich = sub('<ul class="btns">.*?</ul>', '', bereich, flags=S)
		bereich = transHTML(bereich)
		date = str(self.date.strftime('%d.%m.%Y'))
		self.titel = str(self.sparte) + ' - ' + str(self.weekday) + ', ' + date
		self.setTitle(self.titel)
		if self.sparte == 'Neueste Trailer':
			bereich = sub('<span class="badge">', '<span class="subline ">', bereich)
			bereich = sub('<div class="badge-holder">\n\\s+</div>', '<span class="subline ">Trailer</span>', bereich)
			bereich = sub('<a href="', '<td>LINK', bereich)
			bereich = sub('" target="', '</td>', bereich)
			bereich = sub('<img src="', '<td>PIC', bereich)
			bereich = sub('.jpg"', '.jpg</td>', bereich)
			bereich = sub('.png"', '.png</td>', bereich)
			bereich = sub('<span class="headline">', '<td>TITEL', bereich)
			bereich = sub('<span class="subline .*?">', '<td>TEXT', bereich)
			bereich = sub('</span>', '</td>', bereich)
			a = findall('<td>(.*?)</td>', bereich)
			y = 0  # kann weg?
			offset = 4  # kann weg?
			mh = int(60 * SCALE + 0.5)
			for x in a:
				if y == 0:
					res = [x]
					if self.backcolor:
						res.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * SCALE), mh), font=0, backcolor_sel=self.back_color, text=''))
					x = sub('LINK', '', x)
					self.tvlink.append(x)
				if y == 1:
					x = sub('PIC', '', x)
					self.picurllist.append(x)
				if y == 2:
					x = sub('TEXT', '', x)
					res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(10 * SCALE)), size=(int(1140 * SCALE), mh), font=1, color=10857646, color_sel=10857646, flags=RT_HALIGN_LEFT, text=x))
				if y == 3:
					x = sub('TITEL', '', x)
					titel = search('"(.*?)"', x)
					if titel:
						self.tvtitel.append(titel.group(1))
					else:
						self.tvtitel.append(x)
					res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(30 * SCALE)), size=(int(1140 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
					png = ICONPATH + 'cinFHD.png' if FULLHD else ICONPATH + 'cin.png'
					if fileExists(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1160 * SCALE), int(15 * SCALE)), size=(int(60 * SCALE), int(29 * SCALE)), png=loadPNG(png)))
					self.tventries.append(res)
				y = (y + 1) % offset
			self['menu'].l.setItemHeight(mh)
			self['menu'].l.setList(self.tventries)
			self['menu'].moveToIndex(self.oldindex)
		elif not self.charts:
			if self.sparte == 'Kino Vorschau':
				bereich = sub('<a href="https://www.cinema.de.*?</a>', '', bereich)
			bereich = sub('<a href="', '<td>LINK', bereich)
			bereich = sub('" target="', '</td>', bereich)
			bereich = sub('<img src="', '<td>PIC', bereich)
			bereich = sub('.jpg"', '.jpg</td>', bereich)
			bereich = sub('.png"', '.png</td>', bereich)
			bereich = sub('<span class="headline">', '<td>TITEL', bereich)
			bereich = sub('<span class="subline .*?">', '<td>TEXT', bereich)
			bereich = sub('</span>', '</td>', bereich)
			a = findall('<td>(.*?)</td>', bereich)
			y = 0
			offset = 4
			mh = int(61 * SCALE + 0.5)
			for x in a:
				if y == 0:
					res = [x]
					if self.backcolor:
						res.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * SCALE), mh), font=0, backcolor_sel=self.back_color, text=''))
					x = sub('LINK', '', x)
					self.tvlink.append(x)
				if y == 1:
					x = sub('PIC', '', x)
					self.picurllist.append(x)
				if y == 2:
					x = sub('TITEL', '', x)
					titel = search('"(.*?)"', x)
					if titel:
						self.tvtitel.append(titel.group(1))
					else:
						self.tvtitel.append(x)
					res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(10 * SCALE)), size=(int(1140 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
					png = ICONPATH + 'cinFHD.png' if FULLHD else ICONPATH + 'cin.png'
					if fileExists(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1160 * SCALE), int(15 * SCALE)), size=(int(60 * SCALE), int(29 * SCALE)), png=loadPNG(png)))
				if y == 3:
					x = sub('TEXT', '', x)
					res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(30 * SCALE)), size=(int(1140 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
					self.tventries.append(res)
				y += 1
				y = y % offset
			self['menu'].l.setItemHeight(mh)
			self['menu'].l.setList(self.tventries)
			self['menu'].moveToIndex(self.oldindex)
		elif self.charts:
			bereich = sub('<li class="active">\n\\s+<a href="', '<td>LINK', bereich)
			bereich = sub('<li class="inactive ">\n\\s+<a href="', '<td>LINK', bereich)
			bereich = sub('" target="', '</td>', bereich)
			bereich = sub('<p class="title">', '<td>TITEL', bereich)
			bereich = sub('</p>', '</td>', bereich)
			bereich = sub('<img src="', '<td>PIC', bereich)
			bereich = sub('.jpg"', '.jpg</td>', bereich)
			bereich = sub('.png"', '.png</td>', bereich)
			bereich = sub('<span class="country">', '<td>TEXT', bereich)
			bereich = sub('</span>', '</td>', bereich)
			a = findall('<td>(.*?)</td>', bereich)
			y = 0
			offset = 4
			mh = int(60 * SCALE + 0.5)
			for x in a:
				if y == 0:
					res = [x]
					if self.backcolor:
						res.append(MultiContentEntryText(pos=(0, 0), size=(int(1220 * SCALE), mh), font=0, backcolor_sel=self.back_color, text=''))
					x = sub('LINK', '', x)
					self.tvlink.append(x)
				if y == 1:
					x = sub('TITEL', '', x)
					titel = search('"(.*?)"', x)
					if titel:
						self.tvtitel.append(titel.group(1))
					else:
						self.tvtitel.append(x)
					res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(10 * SCALE)), size=(int(1140 * SCALE), mh), font=1, color=10857646, color_sel=10857646, flags=RT_HALIGN_LEFT, text=x))
					png = ICONPATH + 'cinFHD.png' if FULLHD else ICONPATH + 'cin.png'
					if fileExists(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1160 * SCALE), int(15 * SCALE)), size=(int(60 * SCALE), int(29 * SCALE)), png=loadPNG(png)))
				if y == 2:
					x = sub('TEXT', '', x)
					res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(30 * SCALE)), size=(int(1140 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=x))
				if y == 3:
					x = sub('PIC', '', x)
					self.picurllist.append(x)
					self.tventries.append(res)
				y += 1
				y = y % offset
			self['menu'].l.setItemHeight(int(60 * SCALE))
			self['menu'].l.setList(self.tventries)
			self['menu'].moveToIndex(self.oldindex)
		if self.oldindex > 5:
			self.leftUp()
			self.rightDown()
		self.len = len(self.tventries)
		self.ready = True
		playlogo = ICONPATH + 'playFHD.png' if FULLHD else ICONPATH + 'play.png'
		if fileExists(playlogo):
			for i in range(6):
				self.showPlays(playlogo, i)
				self['play%s' % i].show()
			self.GetPics(self.picurllist, 0)

	def ok(self):
		if not HIDEFLAG:
			return
		if self.ready:
			c = self['menu'].getSelectedIndex()
			self.link = self.tvlink[c]
			if self.sparte == '_pic':
				self.session.openWithCallback(self.picReturn, TVPicShow, self.link, 1)
				return
			self.titel = self.tvtitel[c]
			self.download(self.link, self.playTrailer)

	def playTrailer(self, output):
		output = output.decode()
		trailerurl = parseTrailerUrl(output)
		if trailerurl:
			self.trailer = trailerurl
			try:
				sref = eServiceReference(4097, 0, self.trailer)
				sref.setName(self.titel)
				self.session.open(MoviePlayer, sref)
			except IndexError:
				pass
		elif search('https://video.tvspielfilm.de/.*?flv', output):
			self.session.open(MessageBox, 'Der Trailer kann nicht abgespielt werden:\nnicht unterstützter Video-Codec: On2 VP6/Flash', MessageBox.TYPE_INFO, close_on_any_key=True)
		else:
			self.session.open(MessageBox, '\nKein Trailer vorhanden', MessageBox.TYPE_INFO, close_on_any_key=True)

	def gotoEnd(self):
		if self.ready:
			end = self.len - 1
			self['menu'].moveToIndex(end)
			if end > 5:
				self.leftUp()
				self.rightDown()

	def showPlays(self, playlogo, idx):
		if fileExists(playlogo):
			self['play%s' % idx].instance.setPixmapFromFile(playlogo)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadFullPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

	def down(self):
		try:
			c = self['menu'].getSelectedIndex()
		except IndexError:
			return

		self['menu'].down()
		if c + 1 == len(self.tventries):
			self.GetPics(self.picurllist, 0, True, True)

		elif c % 6 == 5:
			self.GetPics(self.picurllist, c + 1, True, True)

	def up(self):
		try:
			c = self['menu'].getSelectedIndex()
		except IndexError:
			return

		self['menu'].up()
		if c == 0:
			l = len(self.tventries)
			d = l % 6
			if d == 0:
				d = 6
			self.GetPics(self.picurllist, l - d, True, True)

		elif c % 6 == 0:
			self.GetPics(self.picurllist, c - 6, True, True)

	def rightDown(self):
		c = self['menu'].getSelectedIndex()
		self['menu'].pageDown()
		l = len(self.tventries)
		d = c % 6
		e = l % 6
		if e == 0:
			e = 6
		if c + e >= l:
			pass
		self.GetPics(self.picurllist, c - d + 6, True, True)

	def leftUp(self):
		c = self['menu'].getSelectedIndex()
		self['menu'].pageUp()
		d = c % 6
		if c < 6:
			pass
		self.GetPics(self.picurllist, c + d - 6, False)
		for i in range(6):
			self['pic%s' % i].show()

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class TVNews(tvBaseScreen):

	def __init__(self, session, link):
		global HIDEFLAG
		skin = readSkin("TVNews")
		tvBaseScreen.__init__(self, session, skin)
		self.menulist = []
		self.menulink = []
		self.picurllist = []
		self.pictextlist = []
		self.postlink = link
		self.link = link
		self.titel = ''
		HIDEFLAG = True
		self.mehrbilder = False
		self.ready = False
		self.postviewready = False
		self['release'] = Label(RELEASE)
		self['release'].show()
		self['picture'] = Pixmap()
		self['picpost'] = Pixmap()
		self['cinlogo'] = Pixmap()
		self['cinlogo'].hide()
		self['playlogo'] = Pixmap()
		self['playlogo'].hide()
		self['statuslabel'] = Label('')
		self['statuslabel'].hide()
		self['picturetext'] = Label('')
		self['textpage'] = ScrollLabel('')
		self['menu'] = ItemList([])
		self['label'] = Label('')
		self.initBlueButton('= Aus-/Einblenden')
		self['actions'] = ActionMap(['OkCancelActions',
									 'DirectionActions',
									 'ColorActions',
									 'ChannelSelectBaseActions'], {'ok': self.ok,
																   'cancel': self.exit,
																   'right': self.rightDown,
																   'left': self.leftUp,
																   'down': self.down,
																   'up': self.up,
																   'nextBouquet': self.zap,
																   'prevBouquet': self.zap,
																   'blue': self.hideScreen}, -1)
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		self.getInfoTimer = eTimer()
		self.getInfoTimer.callback.append(self.downloadFullPage(link, self.makeTVNews))
		self.getInfoTimer.start(200, True)

	def makeTVNews(self, string):
		output = open(self.localhtml, 'r').read()
		output = ensure_str(output)
		titel = search('<title>(.*?)</title>', output)
		self.titel = titel.group(1).replace('&amp;', '&')
		self.setTitle(self.titel)
		startpos = output.find('<div class="content-area">')
		endpos = output.find('<div class="widget-box tvsearch">')
		bereich = output[startpos:endpos]
		bereich = sub('<ul class=".*?</ul>', '', bereich, flags=S)
		bereich = sub('<script.*?</script>', '', bereich, flags=S)
		bereich = sub('<section id="content">.*?</section>', '', bereich, flags=S)
		bereich = sub('<a href="https://tvspielfilm-abo.de.*?\n', '', bereich)
		bereich = sub('<a href="https://www.tvspielfilm.de/news".*?\n', '', bereich)
		bereich = transHTML(bereich)
		link = findall('<a href="(.*?)" target="_self"', bereich)
		picurl = findall('<img src="(.*?)"', bereich)
		picurltvsp = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
		name = findall('<span class="headline">(.*?)</span>', bereich)
		idx = 0
		for x in name:
			idx += 1
		for i in range(idx):
			try:
				self.picurllist.append(picurl[i])
			except IndexError:
				self.picurllist.append(picurltvsp)
			try:
				self.pictextlist.append(name[i])
			except IndexError:
				self.pictextlist.append(' ')
			try:
				res = ['']
				if self.backcolor:
					res.append(MultiContentEntryText(pos=(0, 0), size=(int(870 * SCALE), int(30 * SCALE)), font=0, backcolor_sel=self.back_color, text=''))
				res.append(MultiContentEntryText(pos=(0, 0), size=(int(870 * SCALE), int(30 * SCALE)), font=1, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=name[i]))
				self.menulist.append(res)
				self.menulink.append(link[i])
			except IndexError:
				pass
		self['menu'].l.setItemHeight(int(30 * SCALE))
		self['menu'].l.setList(self.menulist)
		try:
			self.download(picurl[0], self.getPic)
		except IndexError:
			self.download(picurltvsp, self.getPic)
		try:
			self['picturetext'].setText(name[0])
		except IndexError:
			self['picturetext'].setText('')
		self.ready = True

	def makePostviewPageNews(self, string):
		output = open(self.localhtml2, 'r').read()
		output = ensure_str(output)
		self['picture'].hide()
		self['picturetext'].hide()
		self['statuslabel'].hide()
		self['menu'].hide()
		self.setTVTitle(output)
		output = sub('</dl>.\n\\s+</div>.\n\\s+</section>', '</cast>', output)
		startpos = output.find('<div class="content-area">')
		endpos = output.find('>Weitere Bildergalerien<')
		if endpos == -1:
			endpos = output.find('</cast>')
			if endpos == -1:
				endpos = output.find('<h2 class="broadcast-info">')
				if endpos == -1:
					endpos = output.find('<div class="OUTBRAIN"')
					if endpos == -1:
						endpos = output.find('</footer>')
		bereich = output[startpos:endpos]
		bereich = cleanHTML(bereich)
		trailerurl = parseTrailerUrl(output)
		if trailerurl:
			self.trailerurl = trailerurl
			self.trailer = True
		else:
			self.trailer = False
		bereich = sub('" alt=".*?" width="', '" width="', bereich)
		picurl = search('<img src="(.*?)" data-src="(.*?)" width="', bereich)
		if picurl:
			self.downloadPicPost(picurl.group(2), False)
		else:
			picurl = search('<meta property="og:image" content="(.*?)"', output)
			if picurl:
				self.downloadPicPost(picurl.group(1), False)
			else:
				picurl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
				self.downloadPicPost(picurl, False)
		if search('<div class="film-gallery">', output):
			self.mehrbilder = True
			if self.trailer:
				self['label'].setText('OK = Zum Video')
			else:
				self['label'].setText('OK = Fotostrecke')
		else:
			self.mehrbilder = False
			if self.trailer:
				self['label'].setText('OK = Zum Video')
			else:
				self['label'].setText('OK = Vollbild')
		text = parsedetail(bereich)
		fill = self.getFill('TV Spielfilm Online')
		self.POSTtext = text + fill
		self['textpage'].setText(self.POSTtext)
		self['textpage'].show()
		self.showEPG = False
		self.postviewready = True

	def ok(self):
		if not HIDEFLAG:
			return
		else:
			if self.current == 'menu' and self.ready:
				self.selectPage('ok')
			elif self.current == 'postview' and self.postviewready:
				if self.trailer:
					sref = eServiceReference(4097, 0, self.trailerurl)
					sref.setName(self.title)
					self.session.open(MoviePlayer, sref)
				elif self.mehrbilder:
					self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink, 1)
				else:
					self.session.openWithCallback(self.showPicPost, FullScreen)

	def selectPage(self, action):
		c = self['menu'].getSelectedIndex()
		try:
			self.postlink = self.menulink[c]
			if action == 'ok':
				if search('www.tvspielfilm.de', self.postlink):
					self.current = 'postview'
					self.downloadPostPage(self.postlink, self.makePostviewPageNews)
				else:
					self['statuslabel'].setText('Kein Artikel verfuegbar')
					self['statuslabel'].show()
		except IndexError:
			pass

	def getPic(self, output):
		with open(self.picfile, 'wb') as f:
			f.write(output)
		showPic(self['picture'], self.picfile)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadPostPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

	def downloadFullPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)
		self['statuslabel'].setText('Download Fehler')
		self['statuslabel'].show()

	def showTVNews(self):
		self.current = 'menu'
		self['menu'].show()
		self['label'].setText('OK = Zum Artikel')
		self['picture'].show()
		self['picturetext'].show()
		self['textpage'].hide()
		self['picpost'].hide()
		self['cinlogo'].hide()
		self['playlogo'].hide()
		self['statuslabel'].hide()

	def down(self):
		try:
			if self.current == 'menu':
				self['menu'].down()
				c = self['menu'].getSelectedIndex()
				picurl = self.picurllist[c]
				self.download(picurl, self.getPic)
				pictext = self.pictextlist[c]
				self['picturetext'].setText(pictext)
				self['statuslabel'].hide()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def up(self):
		try:
			if self.current == 'menu':
				self['menu'].up()
				c = self['menu'].getSelectedIndex()
				picurl = self.picurllist[c]
				self.download(picurl, self.getPic)
				pictext = self.pictextlist[c]
				self['picturetext'].setText(pictext)
				self['statuslabel'].hide()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def rightDown(self):
		try:
			if self.current == 'menu':
				self['menu'].pageDown()
				c = self['menu'].getSelectedIndex()
				picurl = self.picurllist[c]
				self.download(picurl, self.getPic)
				pictext = self.pictextlist[c]
				self['picturetext'].setText(pictext)
				self['statuslabel'].hide()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def leftUp(self):
		try:
			if self.current == 'menu':
				self['menu'].pageUp()
				c = self['menu'].getSelectedIndex()
				picurl = self.picurllist[c]
				self.download(picurl, self.getPic)
				pictext = self.pictextlist[c]
				self['picturetext'].setText(pictext)
				self['statuslabel'].hide()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.current == 'menu':
			self.close()
		else:
			self.postviewready = False
			self.setTitle(self.titel)
			self.showTVNews()


class TVPicShow(tvBaseScreen):

	def __init__(self, session, link, picmode=0):
		global HIDEFLAG
		skin = readSkin("TVPicShow")
		tvBaseScreen.__init__(self, session, skin)
		self.picmode = picmode
		HIDEFLAG = True
		self.link = link
		self.pixlist = []
		self.topline = []
		self.titel = ''
		self.setTitle('Fotostrecke - TV Spielfilm')
		self.picmax = 1
		self.count = 0
		self['release'] = Label(RELEASE)
		self['release'].show()
		for i in range(8):
			self['infotext%s' % i] = Label('')
		self['picture'] = Pixmap()
		self['picindex'] = Label('')
		self['pictext'] = ScrollLabel('')
		self['textpage'] = ScrollLabel('')
		self['label'] = Label('OK = Vollbild\n< > = Zurück / Vorwärts')
		self.initBlueButton('= Aus-/Einblenden')
		self['NumberActions'] = NumberActionMap(['NumberActions',
												 'OkCancelActions',
												 'DirectionActions',
												 'ColorActions',
												 'ChannelSelectBaseActions'], {'ok': self.ok,
																			   'cancel': self.exit,
																			   'right': self.picup,
																			   'left': self.picdown,
																			   'up': self.up,
																			   'down': self.down,
																			   'nextBouquet': self.zap,
																			   'prevBouquet': self.zap,
																			   'blue': self.hideScreen,
																			   '0': self.gotoPic,
																			   '1': self.gotoPic,
																			   '2': self.gotoPic,
																			   '3': self.gotoPic,
																			   '4': self.gotoPic,
																			   '5': self.gotoPic,
																			   '6': self.gotoPic,
																			   '7': self.gotoPic,
																			   '8': self.gotoPic,
																			   '9': self.gotoPic}, -1)
		self.getInfoTimer = eTimer()
		if picmode == 1:
			self.getInfoTimer.callback.append(self.download(link, self.getNewsPicPage))
		else:
			self.getInfoTimer.callback.append(self.download(link, self.getPicPage))
		self.getInfoTimer.start(200, True)

	def getPicPage(self, output):
		output = ensure_str(output)
		output = transHTML(output)
		self.setTVTitle(output)
		startpos = output.find('<div class="film-gallery">')
		endpos = output.find('<div class="swiper-slide more-galleries">')
		bereich = output[startpos:endpos]
		bereich = sub('<span class="credit">', '', bereich)
		bereich = sub('<span class="counter">.*?</span>\n\\s+', '', bereich)
		bereich = sub('</span>\n\\s+', '', bereich)
		self.pixlist = findall('data-src="(.*?)"', bereich)
		try:
			self.download(self.pixlist[0], self.getPic)
		except IndexError:
			pass
		self.description = findall(' alt="(.*?)" width=', bereich, flags=S)
		self.picmax = len(self.pixlist) if self.pixlist else 1
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))
		self['pictext'].setText(self.description[0])
		self.topline = findall('data-caption="<div class="firstParagraph">(.*?)</div>', bereich)
		self.infotextText(self.topline)

	def getNewsPicPage(self, output):
		output = ensure_str(output)
		self.setTVTitle(output)
		startpos = output.find('<div class="film-gallery">')
		if startpos == -1:
			startpos = output.find('class="film-gallery paragraph')
		endpos = output.find('<div class="swiper-slide more-galleries">')
		if endpos == -1:
			endpos = output.find('<div class="paragraph clear film-gallery"')
		bereich = output[startpos:endpos]
		bereich = sub('<br />\r\n<br />\r\n', ' \x95 ', bereich)
		bereich = sub('<br />\r\n<br />', ' \x95 ', bereich)
		bereich = sub('<br />', '', bereich)
		bereich = sub('<br/>', '', bereich)
		bereich = sub('<b>', '', bereich)
		bereich = sub('</b>', '', bereich)
		bereich = sub('<i>', '', bereich)
		bereich = sub('</i>', '', bereich)
		bereich = sub('<a href.*?</a>', '', bereich)
		bereich = sub('</h2>\n\\s+<p>', '', bereich)
		bereich = sub('&copy;', '', bereich)
		bereich = transHTML(bereich)
		self.pixlist = findall('<img src="(.*?)"', bereich)
		try:
			self.download(self.pixlist[0], self.getPic)
		except IndexError:
			pass
		self.picmax = len(self.pixlist) if self.pixlist else 1
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))
		infotext = findall('data-caption="<div class="firstParagraph">(.*?)</div>', bereich, flags=S)
		credit = findall('<span class="credit">(.*?)</span>', bereich, flags=S)
		self.topline = [infotext[i] + '\n' + credit[i] for i in range(self.picmax)]
		self['pictext'].setText(self.topline[self.count])

	def ok(self):
		self.session.openWithCallback(self.dummy, PicShowFull, self.link, self.count)

	def picup(self):
		self.count = (self.count + 1) % self.picmax
		self.picupdate()

	def picdown(self):
		self.count = (self.count - 1) % self.picmax
		self.picupdate()

	def picupdate(self):
		try:
			link = self.pixlist[self.count]
			self.download(link, self.getPic)
		except IndexError:
			pass
#        if self.picmode == 0:
#            self['pictext'].setText(self.description[self.count] + '\n%s von %s' % (self.count + 1, self.picmax))
#        else:
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))
		if self.topline:
			self['pictext'].setText(self.topline[self.count])

	def gotoPic(self, number):
		self.session.openWithCallback(self.numberEntered, getNumber, number)

	def numberEntered(self, number):
		if number is None or number == 0:
			pass
		else:
			if number > self.picmax:
				number = self.picmax
			self.count = number - 1
			self.picupdate()
			try:
				link = self.pixlist[self.count]
				self.download(link, self.getPic)
			except IndexError:
				pass

	def up(self):
		if self.picmode == 0:
			self.picup()
		else:
			self['pictext'].pageUp()

	def down(self):
		if self.picmode == 0:
			self.picdown()
		else:
			self['pictext'].pageDown()

	def getPic(self, output):
		with open(self.picfile, 'wb') as f:
			f.write(output)
		showPic(self['picture'], self.picfile)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)
		self['pictext'].setText('Download Fehler')

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def initBlueButton(self, text):
		self['bluebutton'] = Pixmap()
		if ALPHA:
			self['bluebutton'].show()
			self['label5'] = Label(text)
		else:
			self['bluebutton'].hide()
			self['label5'] = Label('')

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()

	def dummy(self):
		pass


class PicShowFull(tvBaseScreen):

	def __init__(self, session, link, count):
		global HIDEFLAG
		skin = readSkin("PicShowFull")
		tvBaseScreen.__init__(self, session, skin)
		HIDEFLAG = True
		self.pixlist = []
		self.count = count
		self.picmax = 1
		self['release'] = Label(RELEASE)
		self['release'].show()
		self['picture'] = Pixmap()
		self['picindex'] = Label('')
		self['NumberActions'] = NumberActionMap(['NumberActions',
												 'OkCancelActions',
												 'DirectionActions',
												 'ColorActions',
												 'ChannelSelectBaseActions'], {'ok': self.picup,
																			   'cancel': self.exit,
																			   'right': self.picup,
																			   'left': self.picdown,
																			   'up': self.picup,
																			   'down': self.picdown,
																			   'nextBouquet': self.zap,
																			   'prevBouquet': self.zap,
																			   'blue': self.hideScreen,
																			   '0': self.gotoPic,
																			   '1': self.gotoPic,
																			   '2': self.gotoPic,
																			   '3': self.gotoPic,
																			   '4': self.gotoPic,
																			   '5': self.gotoPic,
																			   '6': self.gotoPic,
																			   '7': self.gotoPic,
																			   '8': self.gotoPic,
																			   '9': self.gotoPic}, -1)
		self.getPicTimer = eTimer()
		self.getPicTimer.callback.append(self.download(link, self.getPicPage))
		self.getPicTimer.start(200, True)

	def getPicPage(self, output):
		output = ensure_str(output)
		startpos = output.find('<div class="film-gallery">')
		if startpos == -1:
			startpos = output.find('class="film-gallery paragraph')
		endpos = output.find('<div class="swiper-slide more-galleries">')
		if endpos == -1:
			endpos = output.find('<div class="paragraph clear film-gallery"')
		bereich = output[startpos:endpos]
		self.pixlist = findall('data-src="(.*?)" alt=', bereich)
		try:
			self.download(self.pixlist[self.count], self.getPic)
		except IndexError:
			pass
		self.picmax = len(self.pixlist) if self.pixlist else 1
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))

	def picup(self):
		self.count = (self.count + 1) % self.picmax
		self.picupdate()

	def picdown(self):
		self.count = (self.count - 1) % self.picmax
		self.picupdate()

	def picupdate(self):
		try:
			link = self.pixlist[self.count]
			self.download(link, self.getPic)
		except IndexError:
			pass
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))

	def gotoPic(self, number):
		self.session.openWithCallback(self.numberEntered, getNumber, number)

	def numberEntered(self, number):
		if number is None or number == 0:
			pass
		else:
			if number > self.picmax:
				number = self.picmax
			self.count = number - 1
		self.picupdate()

	def getPic(self, output):
		with open(self.picfile, 'wb') as f:
			f.write(output)
		showPic(self['picture'], self.picfile)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)
		self['picindex'].setText('Download Fehler')

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class FullScreen(tvAllScreen):

	def __init__(self, session):
		global HIDEFLAG
		skin = readSkin("FullScreen")
		tvAllScreen.__init__(self, session, skin)
		self.picfile = '/tmp/tvspielfilm.jpg'
		HIDEFLAG = True
		self['picture'] = Pixmap()
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.exit,
																		  'cancel': self.exit,
																		  'blue': self.hideScreen}, -1)
		self.onShown.append(self.showPic)

	def showPic(self):
		if fileExists(self.picfile):
			try:
				self['picture'].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
				self['picture'].instance.setPixmapFromFile(self.picfile)
			except:
				currPic = loadJPG(self.picfile)
				self['picture'].instance.setScale(1)
				self['picture'].instance.setPixmap(currPic)
			self['picture'].show()

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class searchYouTube(tvAllScreen):

	def __init__(self, session, name, movie):
		global HIDEFLAG
		self.LinesPerPage = 6
		skin = readSkin("searchYouTube")
		tvAllScreen.__init__(self, session, skin)
		if movie:
			name = name + ' Trailer'
		name = ensure_str(name)
		self.name = name
		self.link = 'https://www.youtube.com/results?filters=video&search_query=' + name
		self.titel = 'YouTube Trailer Suche'
		self.localposter = []
		for i in range(self.LinesPerPage):
			self.localposter.append('/tmp/youtube%s.jpg' % i)
			self['poster%s' % i] = Pixmap()
		self.trailer_id = []
		self.trailer_list = []
		self.localhtml = '/tmp/youtube.html'
		self.ready = False
		HIDEFLAG = True
		self.count = 1
		self['list'] = ItemList([])
		self['label2'] = Label('= YouTube Suche')
		self.initBlueButton('= Aus-/Einblenden')
		self['actions'] = ActionMap(['OkCancelActions',
									 'DirectionActions',
									 'ColorActions',
									 'ChannelSelectBaseActions',
									 'NumberActions',
									 'MovieSelectionActions'], {'ok': self.ok,
									'cancel': self.exit,
																'right': self.rightDown,
																'left': self.leftUp,
																'down': self.down,
																'up': self.up,
																'nextBouquet': self.rightDown,
																'prevBouquet': self.leftUp,
																'yellow': self.search,
																'blue': self.hideScreen,
																'0': self.gotoEnd,
																'bluelong': self.showHelp,
																'showEventInfo': self.showHelp}, -1)
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		self.makeTrailerTimer = eTimer()
		self.makeTrailerTimer.callback.append(self.downloadFullPage(self.link, self.makeTrailerList))
		self.makeTrailerTimer.start(200, True)

	def initBlueButton(self, text):
		self['bluebutton'] = Pixmap()
		if ALPHA:
			self['bluebutton'].show()
			self['label5'] = Label(text)
		else:
			self['bluebutton'].hide()
			self['label5'] = Label('')

	def makeTrailerList(self, string):
		self.setTitle(self.titel)
		output = ensure_str(open(self.localhtml, 'r').read())
		startpos = output.find('class="masthead-skeleton-icon">')
		endpos = output.find(';/*')
		bereich = output[startpos:endpos]
		bereich = transHTML(bereich)
# remove this after tests are finished #################################################
#        analyse = bereich.replace('a><a', 'a>\n<a').replace('script><script', 'script>\n<script').replace('},{', '},\n{').replace('}}}]},"publishedTimeText"', '}}}]},\n"publishedTimeText"')
#        with open('/home/root/logs/bereich.log', 'a') as f:
#                f.write(analyse)
		self.trailer_id = findall('{"videoRenderer":{"videoId":"(.*?)","thumbnail', bereich)
		self.trailer_titel = findall('"title":{"runs":\[{"text":"(.*?)"}\],"accessibility', bereich)
		self.trailer_time = findall('{"text":{"accessibility":{"accessibilityData":{"label":"(.*?)"}},', bereich)
		mh = int(60 * SCALE)
		for i in range(len(self.trailer_id)):
			res = ['']
			if self.backcolor:
				res.append(MultiContentEntryText(pos=(0, 0), size=(int(560 * SCALE), mh), font=0, backcolor_sel=self.back_color, text=''))
			titel = self.trailer_titel[i].split(' | ')[0].replace('\\u0026', '&')
			time = self.trailer_time[i]
			res.append(MultiContentEntryText(pos=(int(10 * SCALE), 0), size=(int(530 * SCALE), mh), font=1, color=16777215, flags=RT_HALIGN_LEFT, text=titel))
			res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(42 * SCALE)), size=(int(530 * SCALE), mh), font=-2, color=16777215, flags=RT_HALIGN_LEFT, text=time))
			self.trailer_list.append(res)
		self['list'].l.setList(self.trailer_list)
		self['list'].l.setItemHeight(int(mh))
		self['list'].moveToIndex(0)
		self.ready = True
		for i in range(self.LinesPerPage):
			try:
				poster = 'https://i.ytimg.com/vi/' + self.trailer_id[i] + '/mqdefault.jpg'
				self.idownload(poster, self.igetPoster, i)
				self['poster%s' % i].show()
			except IndexError:
				self['poster%s' % i].hide()

	def ok(self):
		if self.ready:
			try:
				from youtube_dl import YoutubeDL
			except:
				self.session.open(MessageBox, 'Plugin "youtube-dl" nicht gefunden! Bitte installieren!', MessageBox.TYPE_ERROR)
				return
			c = self['list'].getSelectedIndex()
			trailer_id = self.trailer_id[c]
			ydl = YoutubeDL({'format': '%s' % config.plugins.tvspielfilm.ytresolution.value})
			with ydl:
				trailer_url = 'https://www.youtube.com/watch?v=%s' % trailer_id
				result = ydl.extract_info(trailer_url, download=False)  # only the extracted info is needed
			try:
				sref = eServiceReference(4097, 0, result['url'])
				sref.setName(result['title'])
				self.session.open(MoviePlayer, sref)
			except ValueError:
				pass

	def search(self):
		if self.ready:
			self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='YouTube Trailer Suche:', text=self.name)

	def searchReturn(self, name):
		if name and name != '':
			name = name.replace(' ', '+').replace(':', '+').replace('_', '+').replace('\xc3\x84', 'Ae').replace('\xc3\x96', 'Oe').replace('\xc3\x9c', 'Ue').replace('\xc3\x9f', 'ss').replace('ä', 'ae').replace(
				'ö', 'oe').replace('ü', 'ue').replace('ß', 'ss').replace('\xc4', 'Ae').replace('\xd6', 'Oe').replace('\xdc', 'Ue').replace('\xe4', 'ae').replace('\xf6', 'oe').replace('ü', 'ue')
			self.name = name
			self.link = 'https://www.youtube.com/results?filters=video&search_query=' + name
			self.count = 1
			self.trailer_id = []
			self.trailer_list = []
			self.makeTrailerTimer.callback.append(self.downloadFullPage(self.link, self.makeTrailerList))

	def down(self):
		if self.ready:
			c = self['list'].getSelectedIndex()
			self['list'].down()
			if (c + 1) % self.LinesPerPage == 0:
				offset = (c + 1) // self.LinesPerPage * self.LinesPerPage if (c + 1) < len(self.trailer_id) else 0
				self.setPosters(offset)

	def up(self):
		if self.ready:
			c = self['list'].getSelectedIndex()
			self['list'].up()
			if c % self.LinesPerPage == 0:
				offset = (c - 1) // self.LinesPerPage * self.LinesPerPage if c != 0 else (len(self.trailer_id) - 1) // self.LinesPerPage * self.LinesPerPage
				self.setPosters(offset)

	def rightDown(self):
		if self.ready:
			c = self['list'].getSelectedIndex()
			self['list'].pageDown()
			offset = (c + self.LinesPerPage) // self.LinesPerPage * self.LinesPerPage
			if offset < len(self.trailer_id):
				self.setPosters(offset)

	def leftUp(self):
		if self.ready:
			c = self['list'].getSelectedIndex()
			self['list'].pageUp()
			offset = (c - self.LinesPerPage) // self.LinesPerPage * self.LinesPerPage
			if offset >= 0:
				self.setPosters(offset)

	def setPosters(self, offset):
		for i in range(self.LinesPerPage):
			if offset + i < len(self.trailer_id):
				poster = 'https://i.ytimg.com/vi/' + self.trailer_id[offset + i] + '/mqdefault.jpg'
				try:
					self.idownload(poster, self.igetPoster, i)
					self['poster%s' % i].show()
				except IndexError:
					self['poster%s' % i].hide()
			else:
				self['poster%s' % i].hide()

	def gotoEnd(self):
		if self.ready:
			end = len(self.trailer_list) - 1
			if end > 4:
				self['list'].moveToIndex(end)
				self.leftUp()
				self.rightDown()

	def igetPoster(self, output, i):
		with open(self.localposter[i], 'wb') as f:
			f.write(output)
		if fileExists(self.localposter[i]):
			try:
				self['poster%s' % i].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
				self['poster%s' % i].instance.setPixmapFromFile(self.localposter[i])
			except:
				currPic = loadJPG(self.localposter[i])
				self['poster%s' % i].instance.setScale(1)
				self['poster%s' % i].instance.setPixmap(currPic)

	def idownload(self, link, name, idx):
		getPage(ensure_binary(link)).addCallback(name, idx).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

	def downloadFullPage(self, link, name):
		url = ensure_binary(link.replace(' ', '%20').encode('ascii', 'xmlcharrefreplace'))
		downloadPage(url, self.localhtml).addCallback(name).addErrback(self.downloadPageError)

	def downloadPageError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'The YouTube Server is not reachable:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, '\nThe YouTube Server is not reachable.', MessageBox.TYPE_ERROR)

		self.close()

	def showHelp(self):
		self.session.open(MessageBox, '\n%s' % 'Bouquet = +- Seite\nGelb = Neue YouTube Suche', MessageBox.TYPE_INFO, close_on_any_key=True)

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if fileExists(self.localhtml):
			remove(self.localhtml)
		for i in range(self.LinesPerPage):
			if fileExists(self.localposter[i]):
				remove(self.localposter[i])
		self.close()


class tvMain(tvBaseScreen):

	def __init__(self, session):
		global HIDEFLAG
		skin = readSkin("tvMain")
		tvBaseScreen.__init__(self, session, skin)
		self.senderhtml = '/tmp/tvssender.html'
		if config.plugins.tvspielfilm.tipps.value == 'false':
			self.tipps = False
			self.hidetipps = True
		elif config.plugins.tvspielfilm.tipps.value == 'no':
			self.tipps = True
			self.hidetipps = True
		else:
			self.tipps = True
			self.hidetipps = False
		HIDEFLAG = True
		self.ready = False
		self.sparte = []
		self.genre = []
		self.sender = []
		self.mainmenulist = []
		self.mainmenulink = []
		self.secondmenulist = []
		self.secondmenulink = []
		self.thirdmenulist = []
		self.thirdmenulink = []
		self['release'] = Label(RELEASE)
		self['release'].show()
		self['mainmenu'] = ItemList([])
		self['secondmenu'] = ItemList([])
		self['thirdmenu'] = ItemList([])
		self.actmenu = 'mainmenu'
		self['label'] = Label('Import')
		if self.tipps:
			self['label2'] = Label('Tipp')
		self.initBlueButton('Hide')
		self['actions'] = ActionMap(['OkCancelActions',
									 'DirectionActions',
									 'ColorActions',
									 'MovieSelectionActions',
									 'ChannelSelectBaseActions'], {'ok': self.ok,
																   'cancel': self.exit,
																   'right': self.rightDown,
																   'left': self.leftUp,
																   'down': self.down,
																   'up': self.up,
																   'nextBouquet': self.zap,
																   'prevBouquet': self.zap,
																   'yellow': self.config,
																   'red': self.red,
																   'green': self.green,
																   'blue': self.hideScreen,
																   'contextMenu': self.config}, -1)
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		self.movie_stop = config.usage.on_movie_stop.value
		self.movie_eof = config.usage.on_movie_eof.value
		config.usage.on_movie_stop.value = 'quit'
		config.usage.on_movie_eof.value = 'quit'
		if self.tipps:
			self.TagesTipps = self.session.instantiateDialog(tvTipps)
			if not self.hidetipps:
				self.TagesTipps.start()
				self.TagesTipps.show()
		if config.plugins.tvspielfilm.meintvs.value == 'yes':
			self.MeinTVS = True
			self.error = False
			self.loginerror = False
			self.baseurl = 'https://my.tvspielfilm.de'
			self.login = config.plugins.tvspielfilm.login.value
			self.password = config.plugins.tvspielfilm.password.value
			if config.plugins.tvspielfilm.encrypt.value == 'yes':
				try:
					self.password = b64decode(self.password)
				except TypeError:
					config.plugins.tvspielfilm.encrypt.value = 'no'
					config.plugins.tvspielfilm.encrypt.save()
					configfile.save()

			self.cookiefile = PLUGINPATH + 'db/cookie'
			self.cookie = MozillaCookieJar(self.cookiefile)
			if fileExists(self.cookiefile):
				self.cookie.load()
			self.opener = build_opener(HTTPRedirectHandler(), HTTPHandler(debuglevel=0), HTTPCookieProcessor(self.cookie))
			self.opener.addheaders = [('Host', 'member.tvspielfilm.de'),
									  ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:27.0) Gecko/20100101 Firefox/27.0'),
									  ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'),
									  ('Referer', 'https://member.tvspielfilm.de/login/70.html'),
									  ('Connection', 'keep-alive')]
			self.loginToTVSpielfilm()
		else:
			self.MeinTVS = False
			self.opener = False
			self.AnzTimer = eTimer()
			self.AnzTimer.callback.append(self.makeTimerDB)
			self.AnzTimer.callback.append(self.checkMainMenu)
			self.AnzTimer.start(200, True)

	def loginToTVSpielfilm(self):
		values = urlencode({'email': self.login,
							'pw': self.password,
							'perma_login': '1',
							'done': '1',
							'checkErrors': '1'})
		try:
			response = self.opener.open('https://member.tvspielfilm.de/login/70.html', values, timeout=60)
			result = response.read()
			if search('"error":"', result):
				error = search('"error":"(.*?)\\.', result)
				self.error = 'Mein TV SPIELFILM: ' + error.group(1) + '!'
				self.loginerror = True
				if fileExists(self.cookiefile):
					remove(self.cookiefile)
			else:
				self.cookie.save()
			response.close()
		except HTTPException as e:
			self.error = 'HTTP Exception Error ' + str(e)
		except HTTPError as e:
			self.error = 'HTTP Error: ' + str(e.code)
		except URLError as e:
			self.error = 'URL Error: ' + str(e.reason)
		except error as e:
			self.error = 'Socket Error: ' + str(e)
		except AttributeError as e:
			self.error = 'Attribute Error: ' + str(e.message)

		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		if not self.error:
			self.AnzTimer = eTimer()
			self.AnzTimer.callback.append(self.makeTimerDB)
			self.AnzTimer.callback.append(self.checkMainMenu)
			self.AnzTimer.start(200, True)
		else:
			self.makeErrorTimer = eTimer()
			self.makeErrorTimer.callback.append(self.displayError)
			self.makeErrorTimer.start(200, True)

	def displayError(self):
		self.ready = True
		if self.loginerror:
			self.session.openWithCallback(self.configError, MessageBox, '%s\n\nSetup aufrufen und Einstellungen anpassen?' % self.error, MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, '\n%s' % self.error, MessageBox.TYPE_ERROR)

	def configError(self, answer):
		if answer is True:
			self.config()
		else:
			self.MeinTVS = False
			self.AnzTimer = eTimer()
			self.AnzTimer.callback.append(self.makeTimerDB)
			self.AnzTimer.callback.append(self.checkMainMenu)
			self.AnzTimer.start(200, True)

	def ok(self):
		if self.ready:
			try:
				c = self.getIndex(self[self.actmenu])
			except IndexError:
				c = 0

			if self.actmenu == 'mainmenu':
				try:
					if search('jetzt', self.mainmenulink[c]) or search('time=shortly', self.mainmenulink[c]) or search('abends', self.mainmenulink[c]) or search('nachts', self.mainmenulink[c]):
						if self.tipps:
							self.stopTipps()
						link = self.mainmenulink[c]
						self.session.openWithCallback(self.selectMainMenu, TVJetztView, link, False)
					elif search('page=1', self.mainmenulink[c]):
						if self.tipps:
							self.stopTipps()
						link = self.mainmenulink[c]
						self.session.openWithCallback(self.selectMainMenu, TVHeuteView, link, self.opener)
					elif search('/bilder', self.mainmenulink[c]):
						if self.tipps:
							self.stopTipps()
						link = self.mainmenulink[c]
						self.session.openWithCallback(self.selectMainMenu, TVTrailerBilder, link, '_pic')
					elif search('/tv-tipps//', self.mainmenulink[c]):
						if self.tipps:
							self.stopTipps()
						link = self.mainmenulink[c]
						self.session.openWithCallback(self.selectMainMenu, TVTippsView, link, 'neu')
					elif search('/tv-tipps/', self.mainmenulink[c]) or search('/tv-genre/', self.mainmenulink[c]) or search('/trailer-und-clips/', self.mainmenulink[c]) or search('/news-und-specials/', self.mainmenulink[c]):
						link = self.mainmenulink[c]
						self.makeSecondMenu(None, link)
					else:
						self.ready = False
						link = self.mainmenulink[c]
						if fileExists(self.senderhtml):
							self.makeSecondMenu('string', link)
						else:
							self.downloadSender(link)
				except IndexError:
					self.ready = True

			elif self.actmenu == 'secondmenu':
				if search('/tv-tipps/', self.secondmenulink[c]):
					try:
						if self.tipps:
							self.stopTipps()
						sparte = self.sparte[c]
						link = self.secondmenulink[c]
						self.session.openWithCallback(self.selectSecondMenu, TVTippsView, link, sparte)
					except IndexError:
						pass
				elif search('/trailer-und-clips/', self.secondmenulink[c]) or search('/kino/charts/', self.secondmenulink[c]) or search('/dvd/charts/', self.secondmenulink[c]) or search('/kino/kino-vorschau/', self.secondmenulink[c]):
					try:
						if self.tipps:
							self.stopTipps()
						sparte = self.sparte[c]
						link = self.secondmenulink[c]
						self.session.openWithCallback(self.selectSecondMenu, TVTrailerBilder, link, sparte)
					except IndexError:
						pass
				elif search('/news|/news-und-specials|/streaming|/kino|/stars|/tatort|/kids-tv|/tv-tipps|/tv-programm', self.secondmenulink[c]):
					try:
						if self.tipps:
							self.stopTipps()
						link = self.secondmenulink[c]
						self.session.openWithCallback(self.selectSecondMenu, TVNews, link)
					except IndexError:
						pass
				elif search('/tv-genre/', self.secondmenulink[c]):
					try:
						self.ready = False
						sparte = self.sparte[c]
						link = self.secondmenulink[c]
						self.makeThirdMenu(None, sparte)
					except IndexError:
						self.ready = True
				else:
					try:
						self.ready = False
						sender = self.sender[c]
						link = self.secondmenulink[c]
						self.makeThirdMenu('string', sender)
					except IndexError:
						self.ready = True

			elif self.actmenu == 'thirdmenu':
				if search('/suche/', self.thirdmenulink[c]):
					try:
						if self.tipps:
							self.stopTipps()
						genre = self.genre[c]
						link = self.thirdmenulink[c]
						self.session.openWithCallback(self.selectThirdMenu, TVGenreView, link, genre)
					except IndexError:
						pass
				elif search('/tv-tipps/', self.thirdmenulink[c]):
					try:
						if self.tipps:
							self.stopTipps()
						sparte = self.genre[c]
						link = self.thirdmenulink[c]
						self.session.openWithCallback(self.selectThirdMenu, TVTippsView, link, sparte)
					except IndexError:
						pass
				else:
					try:
						if self.tipps:
							self.stopTipps()
						link = self.thirdmenulink[c].replace('my.tvspielfilm.de', 'www.tvspielfilm.de')
						self.session.openWithCallback(self.selectThirdMenu, TVProgrammView, link, False, False)
					except IndexError:
						pass

	def makeMenuItem(self, text, link):
		res = ['']
		if self.backcolor:
			res.append(MultiContentEntryText(pos=(0, 0), size=(int(270 * SCALE), int(30 * SCALE)), font=2, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, text=''))
		res.append(MultiContentEntryText(pos=(0, 1), size=(int(270 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=text))
		self.mainmenulist.append(res)
		self.mainmenulink.append(self.baseurl + link)

	def makeSecondMenuItem(self, text):
		self.makeSecondMenuItem3(text, '')
		self.sender.append(text)

	def makeSecondMenuItem2(self, text, link):
		self.makeSecondMenuItem3(text, link)
		self.sparte.append(text)

	def makeSecondMenuItem3(self, text, link):
		res = ['']
		if self.backcolor:
			res.append(MultiContentEntryText(pos=(0, 0), size=(int(270 * SCALE), int(30 * SCALE)), font=2, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, text=''))
		res.append(MultiContentEntryText(pos=(0, 1), size=(int(270 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=text))
		self.secondmenulist.append(res)
		self.secondmenulink.append(self.baseurl + link)

	def makeMainMenu(self):
		self.makeMenuItem('Heute im TV', '/tv-programm/tv-sender/?page=1')
		self.makeMenuItem('TV-Tipps', '/tv-tipps/')
		self.makeMenuItem('TV-Genre', '/tv-genre/')
		self.makeMenuItem('Neu im TV', '/tv-tipps//')
		self.makeMenuItem('Jetzt im TV', '/tv-programm/sendungen/jetzt.html')
		self.makeMenuItem('Gleich im TV', '/tv-programm/sendungen/?page=1&order=time&time=shortly')
		self.makeMenuItem('20:15 im TV', '/tv-programm/sendungen/abends.html')
		self.makeMenuItem('22:00 im TV', '/tv-programm/sendungen/fernsehprogramm-nachts.html')
		self.makeMenuItem('TV-Programm', '/tv-programm/tv-sender/')
		self.makeMenuItem('TV-Trailer', '/kino/trailer-und-clips/')
		self.makeMenuItem('TV-Bilder', '/bilder/')
		self.makeMenuItem('TV-News', '/news-und-specials/')
		self.makeMenuItem('Streaming', '/streaming/')
		self['mainmenu'].l.setList(self.mainmenulist)
		self['mainmenu'].l.setItemHeight(int(30 * SCALE))
		self.selectMainMenu()

	def makeSecondMenu(self, string, link):
		if fileExists(self.senderhtml):
			output = open(self.senderhtml, 'r').read()
			output = ensure_str(output)
		else:
			output = ''
		self.secondmenulist = []
		self.secondmenulink = []
		self.sender = []
		self.sparte = []
		if search('/tv-sender/', link):
			startpos = output.find('<option value="" label="Alle Sender">Alle Sender</option>')
			endpos = output.find('<div class="button-toggle">')
			bereich = output[startpos:endpos]
			bereich = transHTML(bereich)
			bereich = sub('verschlüsselte ', '', bereich)
			bereich = sub(' .deutschspr..', '', bereich)
			bereich = sub('Spartensender ARD', 'Digitale ARD', bereich)
			bereich = sub('Meine Lieblingssender', 'Lieblingssender', bereich)
			name = findall('<optgroup label="(.*?)">', bereich)
			for i in range(len(name)):
				if name[i] in ['Lieblingssender', 'Hauptsender', 'Dritte Programme', 'Digitale ARD & ZDF', 'Sky Cinema', 'Sky 3D HD', 'Sky Sport', 'Sky Entertainment', 'Sky Select', 'Pay-TV']:
					self.makeSecondMenuItem(name[i])
			for mi in ['Kindersender', 'Sportsender', 'Musiksender', 'News', 'Ausland', 'Spartensender', 'Auslandssender', 'Regionalsender']:
				self.makeSecondMenuItem(mi)
			if self.tipps:
				self.hideTipps()
		elif search('/tv-tipps/', link):
			for mi in ['Spielfilm', 'Serie', 'Report', 'Unterhaltung', 'Kinder', 'Sport']:
				self.makeSecondMenuItem2(mi, '/tv-tipps/')
		elif search('/tv-genre/', link):
			for mi in ['Spielfilm', 'Serie', 'Report', 'Unterhaltung', 'Kinder', 'Sport']:
				self.makeSecondMenuItem2(mi, '/tv-genre/')
		elif search('/trailer-und-clips/', link):
			self.makeSecondMenuItem2('Kino Neustarts', '/kino/trailer-und-clips/')
			self.makeSecondMenuItem2('Kino Vorschau', '/kino/kino-vorschau/')
			self.makeSecondMenuItem2('Neueste Trailer', '/kino/trailer-und-clips/')
			self.makeSecondMenuItem2('Kino Charts', '/kino/charts/')
			self.makeSecondMenuItem2('DVD Charts', '/kino/dvd/charts/')
		elif search('/news-und-specials/', link):
			self.makeSecondMenuItem3('TV News', '/news/tv/')
			self.makeSecondMenuItem3('Serien-News', '/news/serien/')
			self.makeSecondMenuItem3('Streaming-News', '/news/streaming/')
			self.makeSecondMenuItem3('Film-News', '/news/filme/')
			self.makeSecondMenuItem3('Kino Neustarts', '/kino/neustarts/')
			self.makeSecondMenuItem3('Star-News', '/news/stars/')
			self.makeSecondMenuItem3('Star Videos', '/news-und-specials/star-video-news/')
			self.makeSecondMenuItem3('Shopping-News', '/news/shopping/')
			self.makeSecondMenuItem3('Interviews & Stories', '/news-und-specials/interviewsundstories/')
			self.makeSecondMenuItem3('Tatort', '/tatort/')
			self.makeSecondMenuItem3('Kids TV', '/kids-tv/')
		elif search('/streaming/', link):
			self.makeSecondMenuItem3('Streaming-News', '/news/streaming/')
			self.makeSecondMenuItem3('Vergleich: Netflix & Co.', '/streaming/streamingvergleich/')
			self.makeSecondMenuItem3('Neu auf Netflix', '/news/filme/neu-bei-netflix-diese-serien-und-filme-lohnen-sich,8941871,ApplicationArticle.html')
			self.makeSecondMenuItem3('Neu bei Amazon Prime', '/news/filme/neu-bei-amazon-prime-diese-serien-und-filme-lohnen-sich,10035760,ApplicationArticle.html')
			self.makeSecondMenuItem3('Neu auf Disney+', '/news/serien/neu-auf-disneyplus-serien-filme,10127377,ApplicationArticle.html')
			self.makeSecondMenuItem3('Sky Ticket', '/news/serien/neu-auf-sky-ticket-die-besten-filme-und-serien,10090987,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Netflix Serien', '/news/serien/die-besten-netflix-serien,9437468,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Netflix Filme', '/news/filme/die-besten-netflix-filme,9659520,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Amazon Prime Filme', '/news-und-specials/die-besten-filme-bei-amazon-prime-unsere-empfehlungen,10155040,ApplicationArticle.html')
		self['secondmenu'].l.setList(self.secondmenulist)
		self['secondmenu'].l.setItemHeight(int(30 * SCALE))
		self.selectSecondMenu()

	def makeThirdMenuItem(self, output, start, end):
		startpos = output.find('<optgroup label="%s' % start)
		endpos = output.find('<optgroup label="%s' % end)
		bereich = output[startpos:endpos]
		bereich = transHTML(bereich)
		lnk = findall("value='(.*?)'", bereich)
		name = findall("<option label='(.*?)'", bereich)
		for i in range(len(name)):
			res = ['']
			if self.backcolor:
				res.append(MultiContentEntryText(pos=(0, 0), size=(int(270 * SCALE), int(30 * SCALE)), font=2, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, text=''))
			res.append(MultiContentEntryText(pos=(0, 1), size=(int(270 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=name[i]))
			self.thirdmenulist.append(res)
			self.thirdmenulink.append(lnk[i])

	def makeThirdMenuItem2(self, text, genre, link=None, cat='SP'):
		res = ['']
		if self.backcolor:
			res.append(MultiContentEntryText(pos=(0, 0), size=(int(270 * SCALE), int(30 * SCALE)), font=2, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, text=''))
		res.append(MultiContentEntryText(pos=(0, 1), size=(int(270 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=text))
		self.thirdmenulist.append(res)
		if link == None:
			link = text
		self.thirdmenulink.append(self.baseurl + '/suche/?tab=TV-Sendungen&ext=1&q=&cat[]=' + cat + '&genre' + cat + '=' + link + '&time=day&date=&channel=')
		self.genre.append(genre + ':' + text)

	def makeThirdMenu(self, string, sender):
		if string:
			output = open(self.senderhtml, 'r').read()
			output = ensure_str(output)
		self.thirdmenulist = []
		self.thirdmenulink = []
		self.genre = []
		if sender == 'Lieblingssender':
			self.makeThirdMenuItem(output, 'Meine Lieblingssender">', 'Hauptsender">')
		elif sender == 'Hauptsender':
			self.makeThirdMenuItem(output, 'Hauptsender">', 'Dritte Programme">')
		elif sender == 'Dritte Programme':
			self.makeThirdMenuItem(output, 'Dritte Programme">', 'Sportsender">')
		elif sender == 'Kindersender':
			self.makeThirdMenuItem(output, 'Kindersender">', 'Ausland ')
		elif sender == 'Digitale ARD & ZDF':
			self.makeThirdMenuItem(output, 'Spartensender ARD', 'News')
		elif sender == 'Ausland':
			self.makeThirdMenuItem(output, 'Ausland (deutschspr.)">', 'Regionalsender">')
		elif sender == 'Regionalsender':
			self.makeThirdMenuItem(output, 'Regionalsender">', 'Musiksender">')
		elif sender == 'News':
			self.makeThirdMenuItem(output, 'News', 'Kindersender">')
		elif sender == 'Sportsender':
			self.makeThirdMenuItem(output, 'Sportsender">', 'Spartensender ARD')
		elif sender == 'Musiksender':
			self.makeThirdMenuItem(output, 'Musiksender">', 'Spartensender">')
		elif sender == 'Spartensender':
			self.makeThirdMenuItem(output, 'Spartensender">', 'Shopping">')
		elif sender == 'Sky Cinema':
			self.makeThirdMenuItem(output, 'Sky Cinema">', 'Sky Sport">')
		elif sender == 'Sky Sport':
			self.makeThirdMenuItem(output, 'Sky Sport">', 'Sky Sport">')
		elif sender == 'Sky Entertainment':
			self.makeThirdMenuItem(output, 'Sky Entertainment">', 'Blue Movie">')
		elif sender == 'Sky Select':
			self.makeThirdMenuItem(output, 'Sky Select">', 'Pay-TV">')
		elif sender == 'Pay-TV':
			self.makeThirdMenuItem(output, 'Pay-TV">', 'Auslandssender">')
		elif sender == 'Auslandssender':
			self.makeThirdMenuItem(output, 'Auslandssender">', 'alle Sender')
		elif sender == 'Spielfilm':
			self.makeThirdMenuItem2('Alle Genres', sender, '')
			self.makeThirdMenuItem2('Abenteuer', sender)
			self.makeThirdMenuItem2('Action', sender)
			self.makeThirdMenuItem2('Dokumentation', sender)
			self.makeThirdMenuItem2('Drama', sender)
			self.makeThirdMenuItem2('Episodenfilm', sender)
			self.makeThirdMenuItem2('Erotik', sender)
			self.makeThirdMenuItem2('Familie/Kinder', sender, 'Familie%2FKinder')
			self.makeThirdMenuItem2('Fantasy', sender)
			self.makeThirdMenuItem2('Filmkunst', sender)
			self.makeThirdMenuItem2('Heimat', sender)
			self.makeThirdMenuItem2('Historie', sender)
			self.makeThirdMenuItem2('Horror', sender)
			self.makeThirdMenuItem2('Klassiker', sender)
			self.makeThirdMenuItem2('Komödie', sender, 'Kom%C3%B6die')
			self.makeThirdMenuItem2('Kriegsfilm', sender)
			self.makeThirdMenuItem2('Krimi', sender)
			self.makeThirdMenuItem2('Literatur/Theater', sender, 'Literatur%2FTheater')
			self.makeThirdMenuItem2('Love Story', sender, 'Love+Story')
			self.makeThirdMenuItem2('Märchen', sender, 'M%C3%A4rchen')
			self.makeThirdMenuItem2('Musikfilm', sender)
			self.makeThirdMenuItem2('Porträt', sender, 'Portr%C3%A4t')
			self.makeThirdMenuItem2('Road Movie', sender, 'Road+Movie')
			self.makeThirdMenuItem2('SciFi', sender)
			self.makeThirdMenuItem2('Thriller', sender)
			self.makeThirdMenuItem2('Trickfilm', sender)
			self.makeThirdMenuItem2('Western', sender)
		elif sender == 'Serie':
			self.makeThirdMenuItem2('Alle Genres', sender, '', 'SE')
			self.makeThirdMenuItem2('Action', sender, None, 'SE')
			self.makeThirdMenuItem2('Arzt', sender, None, 'SE')
			self.makeThirdMenuItem2('Comedy', sender, None, 'SE')
			self.makeThirdMenuItem2('Daily Soap', sender, 'Daily+Soap', 'SE')
			self.makeThirdMenuItem2('Dokuserie', sender, None, 'SE')
			self.makeThirdMenuItem2('Familienserie', sender, None, 'SE')
			self.makeThirdMenuItem2('Horror', sender, None, 'SE')
			self.makeThirdMenuItem2('Kinder-/Jugend', sender, 'Kinder-%2FJugend', 'SE')
			self.makeThirdMenuItem2('Krimi', sender, None, 'SE')
			self.makeThirdMenuItem2('Science Fiction', sender, 'Science+Fiction', 'SE')
			self.makeThirdMenuItem2('Soap', sender, None, 'SE')
			self.makeThirdMenuItem2('Western', sender, None, 'SE')
		elif sender == 'Report':
			self.makeThirdMenuItem2('Alle Genres', sender, '', 'RE')
			self.makeThirdMenuItem2('Gesellschaft', sender, None, 'RE')
			self.makeThirdMenuItem2('Justiz', sender, None, 'RE')
			self.makeThirdMenuItem2('Magazin', sender, None, 'RE')
			self.makeThirdMenuItem2('Natur', sender, None, 'RE')
			self.makeThirdMenuItem2('Politik', sender, None, 'RE')
			self.makeThirdMenuItem2('Ratgeber', sender, None, 'RE')
			self.makeThirdMenuItem2('Technik', sender, None, 'RE')
			self.makeThirdMenuItem2('Wissenschaft', sender, None, 'RE')
		elif sender == 'Unterhaltung':
			self.makeThirdMenuItem2('Alle Genres', sender, '', 'U')
			self.makeThirdMenuItem2('Comedy', sender, None, 'U')
			self.makeThirdMenuItem2('Familie', sender, None, 'U')
			self.makeThirdMenuItem2('Kultur', sender, None, 'U')
			self.makeThirdMenuItem2('Late Night', sender, 'Late+Night', 'U')
			self.makeThirdMenuItem2('Musik', sender, None, 'U')
			self.makeThirdMenuItem2('Quiz', sender, None, 'U')
			self.makeThirdMenuItem2('Show', sender, None, 'U')
			self.makeThirdMenuItem2('Talk', sender, None, 'U')
		elif sender == 'Kinder':
			self.makeThirdMenuItem2('Alle Genres', sender, '', 'KIN')
			self.makeThirdMenuItem2('Bildung', sender, None, 'KIN')
			self.makeThirdMenuItem2('Magazin', sender, None, 'KIN')
			self.makeThirdMenuItem2('Reportage', sender, None, 'KIN')
			self.makeThirdMenuItem2('Serie', sender, None, 'KIN')
			self.makeThirdMenuItem2('Show', sender, None, 'KIN')
		elif sender == 'Sport':
			self.makeThirdMenuItem2('Alle Genres', sender, '', 'SPO')
			self.makeThirdMenuItem2('Basketball', sender, None, 'SPO')
			self.makeThirdMenuItem2('Billard', sender, None, 'SPO')
			self.makeThirdMenuItem2('Boxen', sender, None, 'SPO')
			self.makeThirdMenuItem2('Formel 1', sender, 'Formel+1', 'SPO')
			self.makeThirdMenuItem2('Funsport', sender, None, 'SPO')
			self.makeThirdMenuItem2('Fußball', sender, 'Fu%C3%9Fball', 'SPO')
			self.makeThirdMenuItem2('Golf', sender, None, 'SPO')
			self.makeThirdMenuItem2('Handball', sender, None, 'SPO')
			self.makeThirdMenuItem2('Kampfsport', sender, None, 'SPO')
			self.makeThirdMenuItem2('Leichtathletik', sender, None, 'SPO')
			self.makeThirdMenuItem2('Motorsport', sender, None, 'SPO')
			self.makeThirdMenuItem2('Poker', sender, None, 'SPO')
			self.makeThirdMenuItem2('Radsport', sender, None, 'SPO')
			self.makeThirdMenuItem2('Tennis', sender, None, 'SPO')
			self.makeThirdMenuItem2('US Sport', sender, 'US+Sport', 'SPO')
			self.makeThirdMenuItem2('Wassersport', sender, None, 'SPO')
			self.makeThirdMenuItem2('Wintersport', sender, None, 'SPO')
		self['thirdmenu'].l.setList(self.thirdmenulist)
		self['thirdmenu'].l.setItemHeight(int(30 * SCALE))
		self.selectThirdMenu()

	def selectMainMenu(self):
		self.actmenu = 'mainmenu'
		self['mainmenu'].show()
		self['secondmenu'].hide()
		self['thirdmenu'].hide()
		self['mainmenu'].selectionEnabled(1)
		self['secondmenu'].selectionEnabled(0)
		self['thirdmenu'].selectionEnabled(0)
		if self.tipps:
			if not self.hidetipps:
				self.showTipps()
			else:
				self['release'].show()
				self['label2'].show()
		self.ready = True

	def selectSecondMenu(self):
		if len(self.secondmenulist) > 0:
			self.actmenu = 'secondmenu'
			self['mainmenu'].hide()
			self['secondmenu'].show()
			self['thirdmenu'].hide()
			self['mainmenu'].selectionEnabled(0)
			self['secondmenu'].selectionEnabled(1)
			self['thirdmenu'].selectionEnabled(0)
			self['secondmenu'].moveToIndex(0)
			if self.tipps and not self.hidetipps:
				self.showTipps()
		self.ready = True

	def selectThirdMenu(self):
		if len(self.thirdmenulist) > 0:
			self.actmenu = 'thirdmenu'
			self['mainmenu'].hide()
			self['secondmenu'].hide()
			self['thirdmenu'].show()
			self['mainmenu'].selectionEnabled(0)
			self['secondmenu'].selectionEnabled(0)
			self['thirdmenu'].selectionEnabled(1)
			self['thirdmenu'].moveToIndex(0)
			if self.tipps:
				self.hideTipps()
		self.ready = True

	def green(self):
		if self.tipps and self.ready:
			if not self.hidetipps:
				self.TagesTipps.ok()
			elif self.actmenu == 'mainmenu' or self.actmenu == 'secondmenu' and self.hidetipps:
				self.startTipps()

	def hideTipps(self):
		self.TagesTipps.hide()
		self['label2'].hide()
		self.hidetipps = True

	def showTipps(self):
		self.TagesTipps.show()
		self['label2'].show()
		self.hidetipps = False

	def startTipps(self):
		self.TagesTipps.start()
		self.TagesTipps.show()
		self.hidetipps = False

	def stopTipps(self):
		self.TagesTipps.stop()
		self.TagesTipps.hide()
		self.hidetipps = True

	def up(self):
		self[self.actmenu].up()

	def down(self):
		self[self.actmenu].down()

	def leftUp(self):
		self[self.actmenu].pageUp()

	def rightDown(self):
		self[self.actmenu].pageDown()

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar:\n%s' % error, MessageBox.TYPE_ERROR)
			self.ready = True
		except AttributeError:
			self.ready = True

	def checkMainMenu(self):
		if fileExists(self.servicefile):
			self.makeMainMenu()
		else:
			self.session.openWithCallback(self.returnFirstRun, makeServiceFile)

	def downloadSender(self, link):
		if self.MeinTVS:
			try:
				response = self.opener.open(link, timeout=60)
				data = response.read()
				with open(self.senderhtml, 'wb') as f:
					f.write(data)
				response.close()
			except HTTPException as e:
				self.error = 'HTTP Exception Error ' + str(e)
			except HTTPError as e:
				self.error = 'HTTP Error: ' + str(e.code)
			except URLError as e:
				self.error = 'URL Error: ' + str(e.reason)
			except error as e:
				self.error = 'Socket Error: ' + str(e)
			except AttributeError as e:
				self.error = 'Attribute Error: ' + str(e.message)

			if not self.error:
				self.makeSecondMenu('string', link)
			else:
				self.makeErrorTimer = eTimer()
				self.makeErrorTimer.callback.append(self.displayError)
				self.makeErrorTimer.start(200, True)
		else:
			downloadPage(ensure_binary(link), self.senderhtml).addCallback(self.makeSecondMenu, link).addErrback(self.downloadError)

	def getIndex(self, list):
		return list.getSelectedIndex()

	def red(self):
		if self.ready:
			if self.tipps:
				self.stopTipps()
			self.session.openWithCallback(self.returnRed, MessageBox, '\nImportiere TV Spielfilm Sender?', MessageBox.TYPE_YESNO)

	def returnRed(self, answer):
		if answer is True:
			if fileExists(self.servicefile):
				remove(self.servicefile)
			self.session.openWithCallback(self.returnServiceFile, makeServiceFile)

	def returnServiceFile(self, result):
		if result:
			self.selectMainMenu()
		else:
			if ALPHA:
				with open(ALPHA, 'w') as f:
					f.write('%i' % config.av.osd_alpha.value)
			self.close()

	def returnFirstRun(self, result):
		if result:
			self.checkMainMenu()
		else:
			if ALPHA:
				with open(ALPHA, 'w') as f:
					f.write('%i' % config.av.osd_alpha.value)
			self.close()

	def config(self):
		if self.ready:
			if self.tipps:
				self.stopTipps()
				self.session.deleteDialog(self.TagesTipps)
			if fileExists(self.senderhtml):
				remove(self.senderhtml)
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.session.openWithCallback(self.closeconf, tvsConfig)

	def closeconf(self):
		if fileExists(self.picfile):
			remove(self.picfile)
		for i in range(6):
			if fileExists(self.pics[i]):
				remove(self.pics[i])
		if fileExists(self.senderhtml):
			remove(self.senderhtml)
		if fileExists(self.localhtml):
			remove(self.localhtml)
		if fileExists(self.localhtml2):
			remove(self.localhtml2)
		self.close()

	def zap(self):
		if self.ready:
			if self.tipps:
				self.stopTipps()
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.actmenu == 'mainmenu':
			if self.tipps:
				self.TagesTipps.stop()
				self.session.deleteDialog(self.TagesTipps)
			if fileExists(self.picfile):
				remove(self.picfile)
			for i in range(6):
				if fileExists(self.pics[i]):
					remove(self.pics[i])
			if fileExists(self.senderhtml):
				remove(self.senderhtml)
			if fileExists(self.localhtml):
				remove(self.localhtml)
			if fileExists(self.localhtml2):
				remove(self.localhtml2)
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.close()
		elif self.actmenu == 'secondmenu':
			self.selectMainMenu()
		elif self.actmenu == 'thirdmenu':
			self.selectSecondMenu()


class makeServiceFile(Screen):
	skin = '''<screen position="center,center" size="600,200" backgroundColor="#20000000" title="Import TV Spielfilm Sender: TV Bouquet Auswahl">
			   <ePixmap position="0,0" size="600,60" pixmap="{picpath}tvspielfilm.png" alphatest="blend" zPosition="1" />
			   <widget name="list" position="10,70" size="580,130" scrollbarMode="showOnDemand" zPosition="1" />
			  </screen>'''

	def __init__(self, session):
		self.skin = makeServiceFile.skin
		Screen.__init__(self, session)
		dic = {}
		dic['picpath'] = PICPATH
		self.skin = applySkinVars(self.skin, dic)
		self['list'] = MenuList([])
		self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.ok,
														  'cancel': self.exit}, -1)
		self.servicefile = PLUGINPATH + 'db/service.references'
		self.ready = False
		self.bouquetsTimer = eTimer()
		self.bouquetsTimer.callback.append(self.getBouquets)
		self.bouquetsTimer.start(200, True)

	def getBouquets(self):
		bouquets = []
		if config.usage.multibouquet.value:
			eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet')
			bouquet_rootstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
		else:
			bouquet_rootstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
		bouquet_root = eServiceReference(bouquet_rootstr)
		serviceHandler = eServiceCenter.getInstance()
		if config.usage.multibouquet.value:
			list = serviceHandler.list(bouquet_root)
			if list:
				while True:
					s = list.getNext()
					if not s.valid():
						break
					if s.flags & eServiceReference.isDirectory:
						info = serviceHandler.info(s)
						if info:
							bouquets.append((info.getName(s), s))
		else:
			info = serviceHandler.info(bouquet_root)
			if info:
				bouquets.append((info.getName(bouquet_root), bouquet_root))
		entrys = [(x[0], x[1]) for x in bouquets]
		self['list'].l.setList(entrys)
#        try:
#        self['list'].l.setFont(gFont('Regular', 24))
#        except (AttributeError, TypeError):
#            pass
		self.ready = True

	def ok(self):
		if self.ready:
			self.ready = False
			try:
				bouquet = self.getCurrent()
				from Components.Sources.ServiceList import ServiceList
				slist = ServiceList(bouquet, validate_commands=False)
				services = slist.getServicesAsList(format='S')
				search = ['IBDCTSERNX']
				search.extend([(service, 0, -1) for service in services])
				self.epgcache = eEPGCache.getInstance()
				events = self.epgcache.lookupEvent(search)
				eventlist = []
				for eventinfo in events:
					eventlist.append((eventinfo[8], eventinfo[7]))
			except Exception:
				bouquet = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
				bouquet = eServiceReference(bouquet)
				from Components.Sources.ServiceList import ServiceList
				slist = ServiceList(bouquet, validate_commands=False)
				services = slist.getServicesAsList(format='S')
				search = ['IBDCTSERNX']
				search.extend([(service, 0, -1) for service in services])
				self.epgcache = eEPGCache.getInstance()
				events = self.epgcache.lookupEvent(search)
				eventlist = []
				for eventinfo in events:
					eventlist.append((eventinfo[8], eventinfo[7]))
			data = str(eventlist)
			data = sub('[[]', '', data)
			data = sub('[)][]]', '', data)
			data = sub('[(]', '', data)
			data = sub('[/]', ' ', data)
			data = sub(':0:0:0:.*?[)], ', ':0:0:0:\n', data)
			data = sub(':0:0:0::[a-zA-Z0-9_-]+', ':0:0:0:', data)
			data = sub("'", '', data)
			data = sub('HITRADIO.*?\n', '', data)
# for analysis purpose only, activate when picons are missing
#            Bouquetlog('Sendernamen aus Bouquets:\n' + '-'*70 + '\n')
#            Bouquetlog(data)
			data = transCHANNEL(data)
#            Bouquetlog('\n\nSendernamen als Piconname:\n' + '-'*70 + '\n')
#            Bouquetlog(data)
			f = open(self.servicefile, 'a')
			f.write(data)
			f.close()
			fnew = open(self.servicefile + '.new', 'w')
			newdata = ''
			count = 0
			search = compile(' [a-z0-9-]+ ').search
			for line in open(self.servicefile):
				if search(line):
					line = ''
				elif 'nickcc' in line:
					line = line.replace('nickcc', 'nick') + line.replace('nickcc', 'cc')
					count += 1
				elif 'vivacc' in line:
					line = line.replace('vivacc', 'viva') + line.replace('vivacc', 'cc')
					count += 1
				line = line.strip()
				if not line == '' and ',' not in line and '/' not in line and ' 1:64:' not in line and '#' + line[0:5] not in newdata:
					count += 1
					fnew.write(line)
					fnew.write(linesep)
					newdata = newdata + '#' + str(line[0:5])
			f.close()
			fnew.close()
			rename(self.servicefile + '.new', self.servicefile)
			self.ready = True
			if newdata == '':
				self.session.openWithCallback(self.noBouquet, MessageBox, '\nKeine TV Spielfilm Sender gefunden.\nBitte waehlen Sie ein anderes TV Bouquet.', MessageBox.TYPE_YESNO)
			else:
				self.session.openWithCallback(self.otherBouquet, MessageBox,
											  '\nInsgesamt %s TV Spielfilm Sender importiert.\nMoechten Sie ein weiteres TV Bouquet importieren?' % str(count), MessageBox.TYPE_YESNO)

	def otherBouquet(self, answer):
		if answer is True:
			self.bouquetsTimer.callback.append(self.getBouquets)
		else:
			self.close(True)

	def noBouquet(self, answer):
		if answer is True:
			self.bouquetsTimer.callback.append(self.getBouquets)
		else:
			if fileExists(self.servicefile):
				remove(self.servicefile)
			self.close(False)

	def getCurrent(self):
		cur = self['list'].getCurrent()
		return cur and cur[1]

	def up(self):
		if self.ready:
			self['list'].up()

	def down(self):
		if self.ready:
			self['list'].down()

	def exit(self):
		if self.ready:
			self.close(False)


class getNumber(Screen):

	def __init__(self, session, number):
		self.skin = readSkin("getNumber")
		Screen.__init__(self, session)
		self.field = str(number)
		self['release'] = Label(RELEASE)
		self['release'].show()
		self['number'] = Label(self.field)
		self['actions'] = NumberActionMap(['SetupActions'], {'cancel': self.quit,
															 'ok': self.keyOK,
															 '1': self.keyNumber,
															 '2': self.keyNumber,
															 '3': self.keyNumber,
															 '4': self.keyNumber,
															 '5': self.keyNumber,
															 '6': self.keyNumber,
															 '7': self.keyNumber,
															 '8': self.keyNumber,
															 '9': self.keyNumber,
															 '0': self.keyNumber})
		self.Timer = eTimer()
		self.Timer.callback.append(self.keyOK)
		self.Timer.start(2500, True)

	def keyNumber(self, number):
		self.Timer.start(2000, True)
		self.field = self.field + str(number)
		self['number'].setText(self.field)
		if len(self.field) >= 2:
			self.keyOK()

	def keyOK(self):
		self.Timer.stop()
		self.close(int(self['number'].getText()))

	def quit(self):
		self.Timer.stop()
		self.close(0)


class gotoPageMenu(tvAllScreen):

	def __init__(self, session, count, maxpages):
		global HIDEFLAG
		self.skin = readSkin("gotoPageMenu")
		tvAllScreen.__init__(self, session)
		self.localhtml = '/tmp/tvspielfilm.html'
		HIDEFLAG = True
		self.index = count - 1
		self.maxpages = maxpages
		self.pagenumber = []
		self.pagemenulist = []
		self['release'] = Label(RELEASE)
		self['release'].show()
		self['pagemenu'] = ItemList([])
		self['NumberActions'] = NumberActionMap(['NumberActions',
												 'OkCancelActions',
												 'DirectionActions',
												 'ColorActions'], {'ok': self.ok,
																   'cancel': self.exit,
																   'down': self.down,
																   'up': self.up,
																   'blue': self.hideScreen,
																   '0': self.gotoPage,
																   '1': self.gotoPage,
																   '2': self.gotoPage,
																   '3': self.gotoPage,
																   '4': self.gotoPage,
																   '5': self.gotoPage,
																   '6': self.gotoPage,
																   '7': self.gotoPage,
																   '8': self.gotoPage,
																   '9': self.gotoPage}, -1)
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		self.makeMenuTimer = eTimer()
		self.makeMenuTimer.callback.append(self.makePageMenu)
		self.makeMenuTimer.start(200, True)

	def makePageMenu(self):
		self.setTitle('Senderliste')
		output = ensure_str(open(self.localhtml, 'r').read())
		startpos = output.find('label="Alle Sender">Alle Sender</option>')
		if config.plugins.tvspielfilm.meintvs.value == 'yes':
			endpos = output.find('<optgroup label="Hauptsender">')
		else:
			endpos = output.find('<optgroup label="alle Sender alphabetisch">')
		bereich = output[startpos:endpos]
		sender = findall('"channel":"(.*?)","broadcastChannelGroup"', bereich)
# for analysis purpose only! activate when picons are missing or for detecting unneeded picons
#        fullname = findall("<option label='(.*?)' value=", bereich)
#        from glob import glob
#        availpicons = glob(PICPATH + 'picons/*.png')
#        for i in range(len(availpicons)):
#            availpicons[i] = availpicons[i][availpicons[i].rfind('/') + 1 :]
#        ff = open("/home/root/logs/avail_picons.txt", "w")
#        ff.write('list of available picons in pluginpath ../pic/picons/:\n')
#        ff.write('----------------------------------------------------\n')
#        for i in range(len(availpicons)):
#            ff.write(availpicons[i] + '\n')
#        ff.close()
#        ff = open("/home/root/logs/missing_picons.txt", "w")
#        ff.write('list of missing picons in pluginpath ../pic/picons/:\n')
#        ff.write('----------------------------------------------------\n')
#        for i in range(len(sender)):
#            if fileExists(PICPATH + 'picons/' + sender[i].lower() + '.png'):
#                availpicons.remove(sender[i].lower() + '.png')
#            else:
#                ff.write(str(fullname[i]) + ", " + str(sender[i].lower()) + '.png\n')
#        ff.close()
#        ff = open("/home/root/logs/unneeded_picons.txt", "w")
#        ff.write('list of unneeded picons in pluginpath ../pic/picons/:\n')
#        ff.write('----------------------------------------------------\n')
#        for i in range(len(availpicons)):
#            ff.write(availpicons[i] + '\n')
#        ff.close()
#        ff = open("/home/root/logs/complete_piconslist.txt", "w")
#        ff.write('Complete list of picons from homepage:\n')
#        ff.write('--------------------------------------\n')
#        for i in range(len(sender)):
#            ff.write(str(fullname[i]) + ", " + str(sender[i].lower()) + '.png\n')
#        ff.close()
		self.maxpages = len(sender) // 6
		if len(sender) % 6 != 0:
			self.maxpages += 1
		count = 0
		page = 1
		mh = int(37 * SCALE + 0.5)
		while page <= self.maxpages:
			res = ['']
			if self.backcolor:
				res.append(MultiContentEntryText(pos=(0, 0), size=(int(420 * SCALE), mh), font=0, backcolor_sel=self.back_color, text=''))
			res.append(MultiContentEntryText(pos=(0, 0), size=(int(28 * SCALE), mh), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=str(page)))
			for i in range(6):
				try:
					service = sender[count].lower().replace(' ', '').replace('.', '').replace('ii', '2')
					png = PICPATH + 'picons/%s.png' % service
					if fileExists(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(40 * SCALE + 60 * i * SCALE), 0), size=(int(59 * SCALE), int(36 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
				except IndexError:
					pass
				count += 1
			self.pagemenulist.append(res)
			self.pagenumber.append(str(page))
			page += 1
		self['pagemenu'].l.setItemHeight(mh)
		self['pagemenu'].l.setList(self.pagemenulist)
		self['pagemenu'].moveToIndex(self.index)

	def ok(self):
		try:
			c = self.getIndex(self['pagemenu'])
			number = int(self.pagenumber[c])
			self.close(number)
		except IndexError:
			pass

	def gotoPage(self, number):
		self.session.openWithCallback(self.numberEntered, getNumber, number)

	def numberEntered(self, number):
		if number is None or number == 0:
			pass
		elif number >= 29:
			number = 29
		self.close(number)

	def getIndex(self, list):
		return list.getSelectedIndex()

	def down(self):
		self['pagemenu'].down()

	def up(self):
		self['pagemenu'].up()

	def download(self, link, name):
		getPage(link).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close(0)


class tvTipps(tvAllScreen):

	def __init__(self, session):
		global HIDEFLAG
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			color = '4176B6'
		else:
			color = str(config.plugins.tvspielfilm.color.value)
			color = sub('0x00', '', color)
		self.dict = {'picpath': PICPATH, 'color': color}
		skin = readSkin("tvTipps")
		self.skin = applySkinVars(skin, self.dict)
		tvAllScreen.__init__(self, session)
		self.baseurl = 'http://www.tvspielfilm.de'
		self.localhtml = '/tmp/tvspielfilm.html'
		self.max = 6
		self.pic = []
		for i in range(self.max):
			self.pic.append('/tmp/tvspielfilm%s.jpg' % i)
		self.count = 0
		self.ready = False
		HIDEFLAG = True
		self.infolink = ''
		self.tippsinfo = []
		self.tippslink = []
		self.tippschannel = []
		self.tippspicture = []
		self['picture'] = Pixmap()
		self['thumb'] = Pixmap()
		self['picture'].hide()
		self['thumb'].hide()
		self['label'] = Label('')
		self['label2'] = Label('')
		self['label3'] = Label('')
		self['label4'] = Label('')
		self['label5'] = Label('')
		self['elabel3'] = Label('')
		self['label'].hide()
		self['label2'].hide()
		self['label3'].hide()
		self['label4'].hide()
		self['label5'].hide()
		self['elabel3'].hide()
		self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.ok,
														  'cancel': self.exit}, -1)
		self.onLayoutFinish.append(self.start)

	def start(self):
		self.getTippsTimer = eTimer()
		self.getTippsTimer.callback.append(self.downloadFirst(self.baseurl, self.getTagesTipps))
		self.getTippsTimer.start(500, True)
		self.getNextTimer = eTimer()
		self.getNextTimer.callback.append(self.nextTipp)
		self.getNextTimer.start(5000, False)

	def stop(self):
		self.getTippsTimer.stop()
		self.getNextTimer.stop()
		if self.nextTipp in self.getNextTimer.callback:
			self.getNextTimer.callback.remove(self.nextTipp)
		self.hide()

	def getTagesTipps(self, output):
		self.ready = False
		output = ensure_str(output)
		startpos = output.find('teaser-top">')
		endpos = output.find('<div class="block-rotation">')
		bereich = output[startpos:endpos]
		bereich = sub('<ul.*?</ul>', '', bereich, flags=S)
		if search('/news-und-specials/', bereich):
			bereich = sub('<a href="https://my.tvspielfilm.de/news-und-specials/.*?</a>', '', bereich, flags=S)
			bereich = sub('<a href="https://www.tvspielfilm.de/news-und-specials/.*?</a>', '', bereich, flags=S)
		if search('pdf.tvspielfilm.de', bereich):
			bereich = sub('<a href="https://pdf.tvspielfilm.de/.*?</a>', '', bereich, flags=S)
		self.tippspicture = findall('<img src="(.*?)"', bereich, flags=S)
		for i in range(len(self.tippspicture)):
			self.idownload(self.tippspicture[i], self.getPics, i)
		self.tippschannel = findall('<span class="subline .*?">(.*?)</span>', bereich)
		try:
			parts = self.tippschannel[0].split(' | ')
			times = parts[1]
			channel = parts[2]
			channel = shortenChannel(channel)
			self['label4'].setText(times)
			self['label4'].show()
			self['label5'].setText(channel[0:10])
			self['label5'].show()
		except IndexError:
			self['label4'].hide()
			self['label5'].hide()
		self.tippsinfo = findall('<span class="headline">(.*?)</span>', bereich)
		self.tippslink = findall('<a href="(.*?)" target', bereich)
		try:
			self.infolink = self.tippslink[0]
			tipp = 'Tipp des Tages'
			titel = self.tippsinfo[0]
			text = self.tippschannel[0]
		except IndexError:
			tipp = ''
			titel = ''
			text = ''
		self['label'].setText(tipp)
		self['label2'].setText(titel)
		self['label3'].setText(text)
		self['label'].show()
		self['label2'].show()
		self['label3'].show()
		self['elabel3'].show()
		self['thumb'].show()
		self.ready = True

	def ok(self):
		if self.ready and search('/tv-programm/sendung/', self.infolink):
			self.hide()
			self.getNextTimer.stop()
			self.session.openWithCallback(self.returnInfo, TVProgrammView, self.infolink, False, True)

	def returnInfo(self):
		self.show()
		self.getNextTimer.start(5000, False)

	def nextTipp(self):
		if self.ready:
			self.count += 1
			self.count = self.count % len(self.tippspicture)
			if fileExists(self.pic[self.count]):
				showPic(self['picture'], self.pic[self.count])
			try:
				self.infolink = self.tippslink[self.count]
				tipp = 'Tipp des Tages'
				titel = self.tippsinfo[self.count]
				text = self.tippschannel[self.count]
			except IndexError:
				tipp = ''
				titel = ''
				text = ''
			self['label'].setText(tipp)
			self['label2'].setText(titel)
			self['label3'].setText(text)
			try:
				parts = self.tippschannel[self.count].split(' | ')
				times = parts[1]
				channel = parts[2]
				channel = shortenChannel(channel)
				self['label4'].setText(times)
				self['label4'].show()
				self['label5'].setText(channel[0:10])
				self['label5'].show()
			except IndexError:
				self['label4'].hide()
				self['label5'].hide()

	def getPics(self, output, idx):
		with open(self.pic[idx], 'wb') as f:
			f.write(output)
		if idx == 0:
			showPic(self['picture'], self.pic[idx])

	def idownload(self, link, name, idx):
		getPage(ensure_binary(link)).addCallback(name, idx).addErrback(self.idownloadError)

	def idownloadError(self, output):
		self.ready = True

	def downloadFirst(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadFirstError)

	def downloadFirstError(self, output):
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar.', MessageBox.TYPE_ERROR)
			self.ready = True

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class tvsConfig(ConfigListScreen, tvAllScreen):

	def __init__(self, session):
		skin = readSkin("tvsConfig")
		tvAllScreen.__init__(self, session, skin)
		self.password = config.plugins.tvspielfilm.password.value
		self.encrypt = config.plugins.tvspielfilm.encrypt.value
		self['release'] = Label(RELEASE)
		self['release'].show()
		self['plugin'] = Pixmap()

		list = []
		if config.plugins.tvspielfilm.plugin_size == 'FHD':
			list.append(getConfigListEntry('Plugin Größe:', config.plugins.tvspielfilm.plugin_size))
#        list.append(getConfigListEntry('Plugin Position:', config.plugins.tvspielfilm.position))
		list.append(getConfigListEntry('Plugin Schriftgroesse:', config.plugins.tvspielfilm.font_size))
		list.append(getConfigListEntry('Benutze Mein TV SPIELFILM:', config.plugins.tvspielfilm.meintvs))
		list.append(getConfigListEntry('Login (E-mail):', config.plugins.tvspielfilm.login))
		list.append(getConfigListEntry('Passwort:', config.plugins.tvspielfilm.password))
		list.append(getConfigListEntry('Passwort Verschlüsselung:', config.plugins.tvspielfilm.encrypt))
		list.append(getConfigListEntry('Herkunft der Picons:', config.plugins.tvspielfilm.picon))
		self.piconfolder = getConfigListEntry('Eigener Picon Ordner:', config.plugins.tvspielfilm.piconfolder)
		list.append(self.piconfolder)
		if config.plugins.tvspielfilm.picon.value == "own":
			pass
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PICPATH + 'picons'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		list.append(getConfigListEntry('Farbe Listen Auswahl:', config.plugins.tvspielfilm.color))
		list.append(getConfigListEntry('Zeige Tipp des Tages:', config.plugins.tvspielfilm.tipps))
		list.append(getConfigListEntry('Starte Heute im TV mit:', config.plugins.tvspielfilm.primetime))
		list.append(getConfigListEntry('Starte TVS EventView mit:', config.plugins.tvspielfilm.eventview))
		list.append(getConfigListEntry('Beende TVS Jetzt nach dem Zappen:', config.plugins.tvspielfilm.zapexit))
		list.append(getConfigListEntry('Zeige Genre/Episode/Jahr am Ende des Titels:', config.plugins.tvspielfilm.genreinfo))
		list.append(getConfigListEntry('Max. Seiten TV-Suche:', config.plugins.tvspielfilm.maxsearch))
		list.append(getConfigListEntry('Max. Seiten TV-Genre Suche:', config.plugins.tvspielfilm.maxgenre))
		list.append(getConfigListEntry('Benutze AutoTimer Plugin:', config.plugins.tvspielfilm.autotimer))
		list.append(getConfigListEntry('Maximale YouTube-Auflösung:', config.plugins.tvspielfilm.ytresolution))
		list.append(getConfigListEntry('DebugLog', config.plugins.tvspielfilm.debuglog, "Debug Logging aktivieren"))
		list.append(getConfigListEntry('Log in Datei', config.plugins.tvspielfilm.logtofile, "Log in Datei '/home/root/logs'"))
		ConfigListScreen.__init__(self, list, on_change=self.UpdateComponents)
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'cancel': self.cancel,
																		  'red': self.cancel,
																		  'green': self.save}, -1)
		self.onLayoutFinish.append(self.UpdateComponents)

	def UpdateComponents(self):
		png = PICPATH + 'setup/' + str(config.plugins.tvspielfilm.color.value) + '.png'
		if fileExists(png):
			self['plugin'].instance.setPixmapFromFile(png)
		current = self['config'].getCurrent()
		if current == self.piconfolder:
			self.session.openWithCallback(self.folderSelected, FolderSelection, config.plugins.tvspielfilm.piconfolder.value)

	def folderSelected(self, folder):
		if folder:
			config.plugins.tvspielfilm.piconfolder.value = folder
			config.plugins.tvspielfilm.piconfolder.save()

	def save(self):
		# config.plugins.tvspielfilm.plugin_size.save()
		config.plugins.tvspielfilm.font_size.save()
		config.plugins.tvspielfilm.meintvs.save()
		config.plugins.tvspielfilm.login.save()
		if config.plugins.tvspielfilm.password.value != self.password:
			if config.plugins.tvspielfilm.encrypt.value == 'yes':
				password = b64encode(ensure_binary(config.plugins.tvspielfilm.password.value))
				config.plugins.tvspielfilm.password.value = password
			config.plugins.tvspielfilm.password.save()
		elif config.plugins.tvspielfilm.encrypt.value != self.encrypt:
			if self.encrypt == 'yes':
				try:
					password = ensure_str(b64decode(config.plugins.tvspielfilm.password.value))
					config.plugins.tvspielfilm.password.value = password
				except TypeError:
					pass

			else:
				password = b64encode(ensure_binary(config.plugins.tvspielfilm.password.value))
				config.plugins.tvspielfilm.password.value = password
			config.plugins.tvspielfilm.password.save()
			config.plugins.tvspielfilm.encrypt.save()
		config.plugins.tvspielfilm.picon.save()
		config.plugins.tvspielfilm.piconfolder.save()
		config.plugins.tvspielfilm.color.save()
		config.plugins.tvspielfilm.tipps.save()
		config.plugins.tvspielfilm.primetime.save()
		config.plugins.tvspielfilm.eventview.save()
		config.plugins.tvspielfilm.zapexit.save()
		config.plugins.tvspielfilm.genreinfo.save()
		config.plugins.tvspielfilm.maxsearch.save()
		config.plugins.tvspielfilm.maxgenre.save()
		config.plugins.tvspielfilm.autotimer.save()
		config.plugins.tvspielfilm.ytresolution.save()
		config.plugins.tvspielfilm.debuglog.save()
		config.plugins.tvspielfilm.logtofile.save()

		configfile.save()
		self.exit()

	def cancel(self):
		for x in self['config'].list:
			x[1].cancel()

		self.exit()

	def exit(self):
		if config.plugins.tvspielfilm.meintvs.value == 'yes' and config.plugins.tvspielfilm.login.value == '' or config.plugins.tvspielfilm.meintvs.value == 'yes' and config.plugins.tvspielfilm.password.value == '':
			self.session.openWithCallback(
				self.nologin_return, MessageBox, 'Sie haben den Mein TV SPIELFILM Login aktiviert, aber unvollstaendige Login-Daten angegeben.\n\nMoechten Sie die Mein TV SPIELFILM Login-Daten jetzt angeben oder Mein TV SPIELFILM deaktivieren?', MessageBox.TYPE_YESNO)
		else:
			self.session.openWithCallback(self.close, tvMain)

	def nologin_return(self, answer):
		if answer is True:
			pass
		else:
			config.plugins.tvspielfilm.meintvs.value = 'no'
			config.plugins.tvspielfilm.meintvs.save()
			configfile.save()
			self.session.openWithCallback(self.close, tvMain)


class FolderSelection(tvAllScreen):

	def __init__(self, session, folder):
		skin = readSkin("FolderSelection")
		tvAllScreen.__init__(self, session, skin)
		self['release'] = Label(RELEASE)
		self['release'].show()
		self['plugin'] = Pixmap()
		noFolder = ['/bin',
					'/boot',
					'/dev',
					'/etc',
					'/proc',
					'/sbin',
					'/sys']
		self['folderlist'] = FileList(folder, showDirectories=True, showFiles=False, inhibitDirs=noFolder)
		self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions'], {'ok': self.ok,
																							  'cancel': self.cancel,
																							  'right': self.right,
																							  'left': self.left,
																							  'down': self.down,
																							  'up': self.up,
																							  'red': self.cancel,
																							  'green': self.green}, -1)
		self.onLayoutFinish.append(self.pluginPic)

	def pluginPic(self):
		png = PICPATH + 'setup/' + str(config.plugins.tvspielfilm.color.value) + '.png'
		if fileExists(png):
			self['plugin'].instance.setPixmapFromFile(png)

	def ok(self):
		if self['folderlist'].canDescent():
			self['folderlist'].descent()

	def right(self):
		self['folderlist'].pageDown()

	def left(self):
		self['folderlist'].pageUp()

	def down(self):
		self['folderlist'].down()

	def up(self):
		self['folderlist'].up()

	def green(self):
		self.close(self['folderlist'].getSelection()[0])

	def cancel(self):
		self.close(None)


class tvJetzt(tvAllScreenFull):

	def __init__(self, session, link):
		self.link = link
		tvAllScreenFull.__init__(self, session)
		self.channel_db = channelDB(self.servicefile)
		self.JetztTimer = eTimer()
		self.JetztTimer.callback.append(self.makeTimerDB)
		self.JetztTimer.callback.append(self.makeCheck)
		self.JetztTimer.start(200, True)

	def makeCheck(self):
		if fileExists(self.servicefile):
			self.session.openWithCallback(self.exit, TVJetztView, self.link, True)
		else:
			self.session.openWithCallback(self.returnServiceFile, makeServiceFile)

	def returnServiceFile(self, result):
		if result:
			self.session.openWithCallback(self.exit, TVJetztView, self.link, True)
		else:
			self.close()

	def exit(self):
		self.close()


class tvEvent(tvAllScreenFull):

	def __init__(self, session):
		tvAllScreenFull.__init__(self, session)
		self.channel_db = channelDB(self.servicefile)
		self.EventTimer = eTimer()
		self.EventTimer.callback.append(self.makeTimerDB)
		self.EventTimer.callback.append(self.makeChannelLink)
		self.EventTimer.start(200, True)

	def makeChannelLink(self):
		if fileExists(self.servicefile):
			sref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())
			sref = str(sref) + 'FIN'
			sref = sub(':0:0:0:.*?FIN', ':0:0:0:', sref)
			self.sref = sref
			channel = self.channel_db.lookup(sref)
			if channel == 'nope':
				self.session.open(MessageBox, 'Service nicht gefunden:\nKein Eintrag für aktuelle Servicereferenz\n%s' % str(sref), MessageBox.TYPE_INFO, close_on_any_key=True)
				self.close()
			else:
				link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
				self.session.openWithCallback(self.exit, TVProgrammView, link, True, False)
		else:
			self.session.openWithCallback(self.returnServiceFile, makeServiceFile)

	def returnServiceFile(self, result):
		if result:
			self.EventTimer.callback.append(self.makeChannelLink)
		else:
			self.close()

	def exit(self):
		self.close()


class TVHeuteView(tvBaseScreen):

	def __init__(self, session, link, opener):
		global HIDEFLAG
		skin = readSkin("TVHeuteView")
		tvBaseScreen.__init__(self, session, skin)
		if config.plugins.tvspielfilm.meintvs.value == 'yes':
			self.MeinTVS = True
			self.error = False
			self.opener = opener
			page = sub('https://my.tvspielfilm.de/tv-programm/tv-sender/.page=', '', link)
			self.count = int(page)
		else:
			self.MeinTVS = False
			page = sub('https://www.tvspielfilm.de/tv-programm/tv-sender/.page=', '', link)
			self.count = int(page)
		if config.plugins.tvspielfilm.picon.value == 'plugin':
			self.picon = True
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		else:
			self.picon = False
		self.localhtml = '/tmp/tvspielfilm.html'
		self.localhtml2 = '/tmp/tvspielfilm2.html'
		self.tventriess = [[], [], [], [], [], []]
		self.tvlinks = [[], [], [], [], [], []]
		self.tvtitels = [[], [], [], [], [], []]
		self.srefs = [[], [], [], [], [], []]
		self.picloads = {}
		self.searchlink = []
		self.searchref = []
		self.searchentries = []
		self.link = link
		self.postlink = link
		self.titel = ''
		self.POSTtext = ''
		self.EPGtext = ''
		HIDEFLAG = True
		self.search = False
		self.zaps = [True, True, True, True, True, True]
		self.rec = False
		self.first = True
		self.ready = False
		self.postviewready = False
		self.mehrbilder = False
		self.movie = False
		self.datum = False
		self.filter = True
		self.oldindex = 0
		self.oldsearchindex = 1
		self.localhtml = '/tmp/tvspielfilm.html'
		self['release'] = Label(RELEASE)
		self['release'].show()
		self.initBlueButton('= Aus-/Einblenden')
		for i in range(6):
			self['pic%s' % i] = Pixmap()
			self['picon%s' % i] = Pixmap()
		self._commonInit()
		for i in range(6):
			self['sender%s' % i] = Label('')
			self['pictime%s' % i] = Label('')
			self['pictext%s' % i] = Label('')
		self.infotextHide()
		for i in range(6):
			self['menu%s' % i] = ItemList([])
		self.oldcurrent = 'menu0'
		self.currentsearch = 'menu0'
		self.current = 'menu0'
		self.menu = 'menu0'
		self['NumberActions'] = NumberActionMap(['NumberActions',
												 'OkCancelActions',
												 'ChannelSelectBaseActions',
												 'DirectionActions',
												 'EPGSelectActions',
												 'InfobarTeletextActions',
												 'MoviePlayerActions',
												 'MovieSelectionActions'], {'ok': self.ok,
																			'cancel': self.exit,
																			'right': self.rightDown,
																			'left': self.leftUp,
																			'down': self.down,
																			'up': self.up,
																			'nextBouquet': self.nextDay,
																			'prevBouquet': self.prevDay,
																			'nextMarker': self.nextWeek,
																			'prevMarker': self.prevWeek,
																			'0': self.gotoPage,
																			'1': self.gotoPage,
																			'2': self.gotoPage,
																			'3': self.gotoPage,
																			'4': self.gotoPage,
																			'5': self.gotoPage,
																			'6': self.gotoPage,
																			'7': self.gotoPage,
																			'8': self.gotoPage,
																			'9': self.gotoPage,
																			'contextMenu': self.gotoPageMenu,
																			'info': self.getEPG,
																			'epg': self.getEPG,
																			'leavePlayer': self.youTube,
																			'startTeletext': self.pressText}, -1)
		self['ColorActions'] = ActionMap(['ColorActions'], {'green': self.green,
															'yellow': self.yellow,
															'red': self.makeTimer,
															'blue': self.hideScreen}, -1)
		self.service_db = serviceDB(self.servicefile)
		self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		self.morgens = False
		self.mittags = False
		self.vorabend = False
		self.abends = True
		self.nachts = False
		if config.plugins.tvspielfilm.primetime.value == 'now':
			self.abends = False
			hour = datetime.datetime.now().hour
			if hour >= 5 and hour < 14:
				self.morgens = True
			elif hour >= 14 and hour < 18:
				self.mittags = True
			elif hour >= 18 and hour < 20:
				self.vorabend = True
			elif hour >= 20 and hour <= 23:
				self.abends = True
			else:
				self.nachts = True
		if config.plugins.tvspielfilm.color.value == '0x00000000':
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.tvspielfilm.color.value, 16)
		if config.plugins.tvspielfilm.genreinfo.value == 'no':
			self.showgenre = False
		else:
			self.showgenre = True
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self.makeTVTimer = eTimer()
		self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVHeuteView))
		self.makeTVTimer.start(200, True)

	def makeTVHeuteView(self, string):
		output = open(self.localhtml, 'r').read()
		output = ensure_str(output)
		if self.first:
			self.first = False
			startpos = output.find('label="Alle Sender">Alle Sender</option>')
			if self.MeinTVS:
				endpos = output.find('<optgroup label="Hauptsender">')
			else:
				endpos = output.find('<optgroup label="alle Sender alphabetisch">')
			bereich = output[startpos:endpos]
			sender = findall("<option label='(.*?)' value='https", bereich)
			self.maxpages = len(sender) // 6
			if len(sender) % 6 != 0:
				self.maxpages += 1
			self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
		self.zaps = [True, True, True, True, True, True]
		self.srefs = [[], [], [], [], [], []]
		date = str(self.date.strftime('%d.%m.%Y'))
		self.titel = 'Heute im TV  - ' + str(self.weekday) + ', ' + date
		self.setTitle(self.titel)
		startpostop = output.find('<div class="gallery-area">')
		endpostop = output.find('<div class="info-block">')
		bereichtop = output[startpostop:endpostop]
		bereichtop = transHTML(bereichtop)
		bereichtop = sub('<wbr/>', '', bereichtop)
		bereichtop = sub('<div class="first-program block-1">\n.*?</div>', '<div class="first-program block-1"><img src="http://a2.tvspielfilm.de/imedia/8461/5218461,qfQElNSTpxAGvxxuSsPkPjQRIrO6vJjPQCu3KaA_RQPfIknB77GUEYh_MB053lNvumg7bMd+vkJk3F+_CzBZSQ==.jpg" width="149" height="99" border="0" /><span class="time"> </span><strong class="title"> </strong></div>', bereichtop)
		picons = findall('"sendericon","channel":"(.*?)","broadcastChannelGroup"', bereichtop)
		if picons:
			for i in range(6):
				sref = picons[i].lower().replace(' ', '').replace('.', '').replace('ii', '2')
				if sref == 'nope':
					self.srefs[i].append('')
					self.zaps[i] = False
					self['picon%s' % i].hide()
				else:
					self.srefs[i].append(sref)
					picon = PICPATH + 'picons/' + sref + '.png'
					if fileExists(picon):
						self['picon%s' % i].instance.setScale(1)
						self['picon%s' % i].instance.setPixmapFromFile(picon)
						self['picon%s' % i].show()
					else:
						self['picon%s' % i].hide()
		sender = findall('<h3>(.*?)</h3>', bereichtop)
		if sender:
			for i in range(6):
				self['sender%s' % i].setText(sender[i])
				self['sender%s' % i].show()
		else:
			for i in range(6):
				self['sender%s' % i].setText('')
		pic = findall('<img src="(.*?)" alt="(.*?)"', bereichtop)
		idx = 0
		for i in range(len(pic)):
			try:
				picdata, dummy = pic[i]
				if picdata[-4:] == '.jpg':
					picurl = ('https://' + search('https://(.*).jpg', picdata).group(1) + '.jpg').replace('159', '300')
					self.idownloadPic(picurl, self.getPics, idx)
					self['pic%s' % idx].show()
					idx += 1
			except IndexError:
				pass
		pictime = findall('<span class="time">(.*?)</span>', bereichtop)
		if pictime:
			for i in range(6):
				self['pictime%s' % i].setText(pictime[i])
				self['pictime%s' % i].show()
		else:
			for i in range(6):
				self['pictime%s' % i].setText('')
		pictext = findall('<strong class="title">(.*?)</strong>', bereichtop)
		if pictext:
			for i in range(6):
				self['pictext%s' % i].setText(pictext[i])
				self['pictext%s' % i].show()
		else:
			for i in range(6):
				self['pictext%s' % i].setText('')
		if self.abends:
			startpos = output.find('<div id="toggleslot-20-p"')
			endpos = output.find('<div id="toggleslot-0-p"')
		elif self.nachts:
			startpos = output.find('<div id="toggleslot-0-p"')
			endpos = output.find('<div class="block-now-stations">')
		elif self.morgens:
			startpos = output.find('<div id="toggleslot-5-p"')
			endpos = output.find('<div id="toggleslot-14-p"')
		elif self.mittags:
			startpos = output.find('<div id="toggleslot-14-p"')
			endpos = output.find('<div id="toggleslot-18-p"')
		elif self.vorabend:
			startpos = output.find('<div id="toggleslot-18-p"')
			endpos = output.find('<div id="toggleslot-20-p"')
		bereich = output[startpos:endpos]
		bereich = transHTML(bereich)
		bereich = sub('<a href="javascript://".*?\n', '', bereich)
		bereich = sub('<a title="Sendung jetzt.*?\n', '', bereich)
		bereich = sub('<span class="add-info icon-livetv"></span>', '', bereich)
		bereich = sub('<span class="time"></span>', '<td>TIME00:00</span>', bereich)
		bereich = sub('<span class="time">', '<td>TIME', bereich)
		bereich = sub('<span class="add-info editorial-rating small"></span>', '', bereich)
		bereich = sub('<span class="add-info editorial-', '<td>RATING', bereich)
		bereich = sub('<span class="add-info ', '<td>LOGO', bereich)
		bereich = sub('<a href="http://my', '<td>LINKhttp://www', bereich)
		bereich = sub('<a href="http://www', '<td>LINKhttp://www', bereich)
		bereich = sub('<a href="https://my', '<td>LINKhttp://www', bereich)
		bereich = sub('<a href="https://www', '<td>LINKhttp://www', bereich)
		bereich = sub('" target="_self"', '</td>', bereich)
		bereich = sub('<strong class="title">', '<td>TITEL', bereich)
		bereich = sub('<span class="subtitle">', '<td>SUBTITEL', bereich)
		bereich = sub('</strong>', '</td>', bereich)
		bereich = sub('">TIPP</span>', '</td>', bereich)
		bereich = sub('">LIVE</span>', '</td>', bereich)
		bereich = sub('">HDTV</span>', '</td>', bereich)
		bereich = sub('">NEU</span>', '</td>', bereich)
		bereich = sub('">OMU</span>', '</td>', bereich)
		bereich = sub('"></span>', '</td>', bereich)
		bereich = sub('</span>', '</td>', bereich)
		bereich = sub('<wbr/>', '', bereich)
		bereich = sub('<div class="program-block">', '<td>BLOCK</td>', bereich)
		self.tventriess = [[], [], [], [], [], []]
		self.tvlinks = [[], [], [], [], [], []]
		self.tvtitels = [[], [], [], [], [], []]
		menupos = - 1
		menuitems = [[], [], [], [], [], []]
		a = findall('<td>(.*?)</td>', bereich)
		for x in a:
			if x == 'BLOCK':
				menupos = (menupos + 1) % 6
			else:
				menuitems[menupos].append(x)
		midx = 0
		currentitem = None
		currentlink = 'na'
		currenttitle = ''
		mh = int(92 * SCALE)
		for mi in menuitems:
			self.menu = 'menu%s' % midx
			for x in mi:
				if search('TIME', x):
					x = sub('TIME', '', x)
					currentitem = [x]
					if currentitem:
						self.tventriess[midx].append(currentitem)
						self.tvlinks[midx].append(currentlink)
						self.tvtitels[midx].append(currenttitle)
					if self.backcolor:
						currentitem.append(MultiContentEntryText(pos=(0, 0), size=(int(200 * SCALE), mh), font=0, backcolor_sel=self.back_color, text=''))
					currentitem.append(MultiContentEntryText(pos=(0, 0), size=(int(40 * SCALE), int(23 * SCALE)), font=-2, backcolor=13388098, color=16777215, backcolor_sel=13388098, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
					currentlink = 'na'
					currenttitle = ''
					hour = sub(':..', '', x)
					icount = 0
					if int(hour) < 5:
						one_day = datetime.timedelta(days=1)
						date = self.date + one_day
					else:
						date = self.date
					timer = str(date) + ':::' + x + ':::' + self.srefs[midx][0]
					boxtimers = ''
					for item in self.timer:
						boxtimers += item[:21] + transCHANNEL(ServiceReference(eServiceReference(item[21:].strip())).getServiceName() + ',')
					if timer in boxtimers:
						self.rec = True
						png = ICONPATH + 'recFHD.png' if FULLHD else ICONPATH + 'rec.png'
						if fileExists(png):
							currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(0, int((24 + icount * 14) * SCALE)), size=(int(40 * SCALE), int(13 * SCALE)), png=loadPNG(png)))
							icount += 1
				if search('LOGO', x):  # NEU
					x = sub('LOGO', '', x)
					png = '%s%sFHD.png' % (ICONPATH, x) if FULLHD else '%s%s.png' % (ICONPATH, x)
					if fileExists(png):
						currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(0, int((24 + icount * 14) * SCALE)), size=(int(40 * SCALE), int(13 * SCALE)), png=loadPNG(png)))
						icount += 1
				if search('RATING', x):  # DAUMEN
					x = sub('RATING', '', x).replace(' ', '-')
					png = '%s%sFHD.png' % (ICONPATH, x) if FULLHD else '%s%s.png' % (ICONPATH, x)
					if fileExists(png):
						currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(int(6 * SCALE), int((24 + icount * 14) * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
				if search('LINK', x):
					x = sub('LINK', '', x)
					currentlink = x
				if search('TITEL', x) and search('SUBTITEL', x) is None:
					x = sub('TITEL', '', x)
					currenttitle = x
				if search('SUBTITEL', x):
					x = sub('SUBTITEL', '', x)
					if x != '':
						currenttitle = currenttitle + ', ' + x
				if self.rec:
					self.rec = False
				if SCALE == 1.5:
					tsize = mh - 15 if self.fontlarge else mh
				else:
					tsize = mh - 10 if self.fontlarge else mh
				currentitem.append(MultiContentEntryText(pos=(int(45 * SCALE), 0), size=(int(155 * SCALE), tsize), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=currenttitle))
			midx += 1

		if currentitem:
			midx -= 1
			self.tventriess[midx].append(currentitem)
			self.tvlinks[midx].append(currentlink)
			self.tvtitels[midx].append(currenttitle)

		for i in range(6):
			self.tvlinks[i].pop(0)  # der jeweils allererster Eintrag ist für die Tonne
			self.tvtitels[i].pop(0)
			self['menu%s' % i].l.setItemHeight(mh)
			self['menu%s' % i].l.setList(self.tventriess[i])
			self['menu%s' % i].moveToIndex(self.oldindex)
		for i in range(6):
			if self.current == 'menu%s' % i:
				for j in range(6):
					self['menu%s' % j].selectionEnabled(1 if i == j else 0)
		self['label'].setText('Info = +- Tageszeit, Bouquet = +- Tag, <> = +- Woche, Menue = Senderliste')
		self['label'].stopBlinking()
		self['label'].show()
		self.ready = True

	def makePostviewPage(self, string):
		for i in range(6):
			self['sender%s' % i].hide()
			self['picon%s' % i].hide()
			self['pic%s' % i].hide()
			self['pictime%s' % i].hide()
			self['pictext%s' % i].hide()
			self['menu%s' % i].hide()
		try:
			self._makePostviewPage(string)
		except:
			printStackTrace()

	def makeSearchView(self, url):
		self._makeSearchView(url)

	def ok(self):
		self._ok()

	def selectPage(self, action):
		self.oldcurrent = self.current
		if self.ready:
			for i in range(6):
				if self.current == 'menu%s' % i:
					c = self['menu%s' % i].getSelectedIndex()
					try:
						self.postlink = self.tvlinks[i][c]
						if action == 'ok':
							if search('www.tvspielfilm.de', self.postlink):
								self.current = 'postview'
								self.downloadPostPage(self.postlink, self.makePostviewPage)
					except IndexError:
						pass
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			try:
				self.postlink = self.searchlink[c]
				if action == 'ok':
					if search('www.tvspielfilm.de', self.postlink):
						self.current = 'postview'
						self.downloadPostPage(self.postlink, self.makePostviewPage)
			except IndexError:
				pass

	def getEPG(self):
		if self.current == 'postview' and self.postviewready:
			if not self.showEPG:
				self.showEPG = True
				sref = None
				channel = ''
				if not self.search:
					for i in range(6):
						if self.oldcurrent == 'menu%s' % i and self.zaps[i]:
							try:
								c = self['menu%s' % i].getSelectedIndex()
								sref = self.srefs[i][0]
								channel = ServiceReference(eServiceReference(sref)).getServiceName()
							except IndexError:
								sref = None
								channel = ''
				else:
					try:
						c = self['searchmenu'].getSelectedIndex()
						sref = self.searchref[c]
						channel = ServiceReference(eServiceReference(sref)).getServiceName()
					except IndexError:
						sref = None
						channel = ''
				if sref:
					try:
						start = self.start
						s1 = sub(':..', '', start)
						date = str(self.postdate) + 'FIN'
						date = sub('..FIN', '', date)
						date = date + self.day
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(':..:..', '', start)
						if int(s2) > int(s1):
							start = str(self.date) + ' ' + start
						else:
							start = date + ' ' + start
						start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
						start = int(mktime(start.timetuple()))
						epgcache = eEPGCache.getInstance()
						event = epgcache.startTimeQuery(eServiceReference(sref), start)
						if event == -1:
							self.EPGText = getEPGText()
						else:
							event = epgcache.getNextTimeEntry()
							self.EPGtext = event.getEventName()
							short = event.getShortDescription()
							ext = event.getExtendedDescription()
							dur = '%d Minuten' % (event.getDuration() / 60)
							if short and short != self.EPGtext:
								self.EPGtext += '\n\n' + short
							if ext:
								self.EPGtext += '\n\n' + ext
							if dur:
								self.EPGtext += '\n\n' + dur
					except:
						self.EPGText = getEPGText()

				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n\n' + fill
				self['textpage'].setText(self.EPGtext)
			else:
				self.showEPG = False
				self['textpage'].setText(self.POSTtext)
			self['textpage'].show()
		elif self.current != 'postview' and self.ready and not self.search:
			self.oldindex = 0
			if self.abends:
				self.morgens = False
				self.mittags = False
				self.vorabend = False
				self.abends = False
				self.nachts = True
				self.makeTVHeuteView('')
			elif self.nachts:
				self.morgens = True
				self.mittags = False
				self.vorabend = False
				self.abends = False
				self.nachts = False
				self.makeTVHeuteView('')
			elif self.morgens:
				self.morgens = False
				self.mittags = True
				self.vorabend = False
				self.abends = False
				self.nachts = False
				self.makeTVHeuteView('')
			elif self.mittags:
				self.morgens = False
				self.mittags = False
				self.vorabend = True
				self.abends = False
				self.nachts = False
				self.makeTVHeuteView('')
			elif self.vorabend:
				self.morgens = False
				self.mittags = False
				self.vorabend = False
				self.abends = True
				self.nachts = False
				self.makeTVHeuteView('')

	def red(self):
		if self.current == 'postview' and self.postviewready:
			for i in range(6):
				if self.oldcurrent == 'menu%s' % i and self.zaps[i]:
					c = self['menu%s' % i].getSelectedIndex()
					self.oldindex = c
					try:
						sref = self.srefs[i][0]
						self.redTimer(False, sref)
					except IndexError:
						self.redTimer(False)
			if self.oldcurrent == 'searchmenu':
				c = self['searchmenu'].getSelectedIndex()
				self.oldsearchindex = c
				try:
					c = self['searchmenu'].getSelectedIndex()
					sref = self.searchref[c]
					self.redTimer(False, sref)
				except IndexError:
					self.redTimer(False)
			else:
				self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
		if self.ready:
			for i in range(6):
				if self.current == 'menu%s' % i:
					c = self['menu%s' % i].getSelectedIndex()
					self.oldindex = c
					try:
						self.postlink = self.tvlinks[i][c]
						if search('www.tvspielfilm.de', self.postlink):
							self.oldcurrent = self.current
							self.download(self.postlink, self.makePostTimer)
					except IndexError:
						pass
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			try:
				self.postlink = self.searchlink[c]
				if search('www.tvspielfilm.de', self.postlink):
					self.oldcurrent = self.current
					self.download(self.postlink, self.makePostTimer)
			except IndexError:
				pass

	def finishedTimer(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)

				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			self.makeTimerDB()
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
				self.makeTVHeuteView('')
			else:
				self.showsearch()
		else:
			self.ready = True
			self.postviewready = False
			self.current = self.oldcurrent
			if not self.search:
				self.showProgrammPage()
			else:
				self.showsearch()

	def green(self):
		for i in range(6):
			if self.current == 'menu%s' % i and self.zaps[i] and not self.search:
				try:
					sref = self.srefs[i][0]
					self.session.nav.playService(eServiceReference(sref))
				except IndexError:
					pass

	def yellow(self):
		if self.current == 'postview':
			self.youTube()
		elif not self.search and self.ready:
			self.currentsearch = self.current
			for i in range(6):
				if self.current == 'menu%s' % i:
					c = self['menu%s' % i].getSelectedIndex()
					self.oldindex = c
					try:
						titel = self.tvtitels[i][c]
						self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
					except IndexError:
						self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

	def searchReturn(self, search):
		if search and search != '':
			self.searchstring = search
			for i in range(6):
				self['sender%s' % i].hide()
				self['picon%s' % i].hide()
				self['pic%s' % i].hide()
				self['pictime%s' % i].hide()
				self['pictext%s' % i].hide()
				self['menu%s' % i].hide()
			self['seitennr'].setText('')
			self['label'].setText('')
			self['label2'].setText('')
			self['label3'].setText('')
			self['label4'].setText('')
			self['label5'].setText('')
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = search.replace(' ', '+')
			searchlink = self.baseurl + '/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=' + search + '&page=1'
			self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(searchYouTube, self.name, self.movie)
		elif not self.search and self.ready:
			for i in range(6):
				if self.current == 'menu%s' % i:
					c = self['menu%s' % i].getSelectedIndex()
					try:
						titel = self.tvtitels[i][c]
						self.session.open(searchYouTube, titel, self.movie)
					except IndexError:
						pass

	def gotoPageMenu(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.session.openWithCallback(self.numberEntered, gotoPageMenu, self.count, self.maxpages)

	def gotoPage(self, number):
		if self.current != 'postview' and self.ready and not self.search:
			self.session.openWithCallback(self.numberEntered, getNumber, number)
		elif self.current == 'searchmenu' and self.search and self.ready and number == 0:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)
		elif self.current == 'postview' and number == 1:
			self.zapDown()
		elif self.current == 'postview' and number == 2:
			self.zapUp()
		elif self.current == 'postview' and number == 7:
			self.IMDb()
		elif self.current == 'postview' and number == 8:
			self.TMDb()
		elif self.current == 'postview' and number == 9:
			self.TVDb()

	def numberEntered(self, number):
		if self.current != 'postview' and self.ready and not self.search:
			if number is None or number == 0:
				pass
			else:
				if number >= self.maxpages:
					number = self.maxpages
				self.count = number
				self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
				if search('date', self.link):
					self.link = self.link + 'FIN'
					date = findall('date=(.*?)FIN', self.link)
					self.link = sub('page=.*?FIN', '', self.link)
					self.link = self.link + 'page=' + str(self.count) + '&date=' + date[0]
				else:
					self.link = self.link + 'FIN'
					self.link = sub('page=.*?FIN', '', self.link)
					self.link = self.link + 'page=' + str(self.count)
				self['label'].setText('Bitte warten...')
				self['label'].startBlinking()
				self.ready = False
				self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVHeuteView))

	def nextDay(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('date', self.link):
				self.link = self.link + 'FIN'
				date1 = findall('date=(.*?)-..-..FIN', self.link)
				date2 = findall('date=....-(.*?)-..FIN', self.link)
				date3 = findall('date=....-..-(.*?)FIN', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

				one_day = datetime.timedelta(days=1)
				tomorrow = today + one_day
				self.weekday = makeWeekDay(tomorrow.weekday())
				nextday = sub('date=(.*?FIN)', 'date=', self.link)
				nextday = nextday + str(tomorrow)
				self.date = tomorrow
				one_day = datetime.timedelta(days=1)
				self.nextdate = self.date + one_day
			else:
				today = datetime.date.today()
				one_day = datetime.timedelta(days=1)
				tomorrow = today + one_day
				self.weekday = makeWeekDay(tomorrow.weekday())
				nextday = self.link + '&date=' + str(tomorrow)
				self.date = tomorrow
				one_day = datetime.timedelta(days=1)
				self.nextdate = self.date + one_day
			self.link = nextday
			self.oldindex = 0
			self['label'].setText('Bitte warten...')
			self['label'].startBlinking()
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVHeuteView))
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def prevDay(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('date', self.link):
				self.link = self.link + 'FIN'
				date1 = findall('date=(.*?)-..-..FIN', self.link)
				date2 = findall('date=....-(.*?)-..FIN', self.link)
				date3 = findall('date=....-..-(.*?)FIN', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

				one_day = datetime.timedelta(days=1)
				yesterday = today - one_day
				self.weekday = makeWeekDay(yesterday.weekday())
				prevday = sub('date=(.*?FIN)', 'date=', self.link)
				prevday = prevday + str(yesterday)
				self.date = yesterday
				one_day = datetime.timedelta(days=1)
				self.nextdate = self.date + one_day
			else:
				today = datetime.date.today()
				one_day = datetime.timedelta(days=1)
				yesterday = today - one_day
				self.weekday = makeWeekDay(yesterday.weekday())
				prevday = self.link + '&date=' + str(yesterday)
				self.date = yesterday
				one_day = datetime.timedelta(days=1)
				self.nextdate = self.date + one_day
			self.link = prevday
			self.oldindex = 0
			self['label'].setText('Bitte warten...')
			self['label'].startBlinking()
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVHeuteView))
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def nextWeek(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('date', self.link):
				self.link = self.link + 'FIN'
				date1 = findall('date=(.*?)-..-..FIN', self.link)
				date2 = findall('date=....-(.*?)-..FIN', self.link)
				date3 = findall('date=....-..-(.*?)FIN', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

				one_week = datetime.timedelta(days=7)
				tomorrow = today + one_week
				self.weekday = makeWeekDay(tomorrow.weekday())
				nextweek = sub('date=(.*?FIN)', 'date=', self.link)
				nextweek = nextweek + str(tomorrow)
				self.date = tomorrow
				one_week = datetime.timedelta(days=7)
				self.nextdate = self.date + one_week
			else:
				today = datetime.date.today()
				one_week = datetime.timedelta(days=7)
				tomorrow = today + one_week
				self.weekday = makeWeekDay(tomorrow.weekday())
				nextweek = self.link + '&date=' + str(tomorrow)
				self.date = tomorrow
				one_week = datetime.timedelta(days=7)
				self.nextdate = self.date + one_week
			self.link = nextweek
			self.oldindex = 0
			self['label'].setText('Bitte warten...')
			self['label'].startBlinking()
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVHeuteView))

	def prevWeek(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			if search('date', self.link):
				self.link = self.link + 'FIN'
				date1 = findall('date=(.*?)-..-..FIN', self.link)
				date2 = findall('date=....-(.*?)-..FIN', self.link)
				date3 = findall('date=....-..-(.*?)FIN', self.link)
				try:
					today = datetime.date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = datetime.date.today()

				one_week = datetime.timedelta(days=7)
				yesterday = today - one_week
				self.weekday = makeWeekDay(yesterday.weekday())
				prevweek = sub('date=(.*?FIN)', 'date=', self.link)
				prevweek = prevweek + str(yesterday)
				self.date = yesterday
				one_week = datetime.timedelta(days=7)
				self.nextdate = self.date + one_week
			else:
				today = datetime.date.today()
				one_week = datetime.timedelta(days=7)
				yesterday = today - one_week
				self.weekday = makeWeekDay(yesterday.weekday())
				prevweek = self.link + '&date=' + str(yesterday)
				self.date = yesterday
				one_week = datetime.timedelta(days=7)
				self.nextdate = self.date + one_week
			self.link = prevweek
			self.oldindex = 0
			self['label'].setText('Bitte warten...')
			self['label'].startBlinking()
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVHeuteView))

	def rightDown(self):
		try:
			for i in range(6):
				if self.current == 'menu%s' % i:
					self['menu%s' % i].selectionEnabled(0)
					self['menu%s' % ((i + 1) % 6)].selectionEnabled(1)
					self.current = 'menu%s' % ((i + 1) % 6)
					break
			if self.current == 'menu0':
				self.count = self.count + 1 if self.count < self.maxpages else 1
				if search('date', self.link):
					self.link = self.link + 'FIN'
					date = findall('date=(.*?)FIN', self.link)
					self.link = sub('page=.*?FIN', '', self.link)
					self.link = self.link + 'page=' + str(self.count) + '&date=' + date[0]
				else:
					self.link = self.link + 'FIN'
					self.link = sub('page=.*?FIN', '', self.link)
					self.link = self.link + 'page=' + str(self.count)
				self['label'].setText('Bitte warten...')
				self['label'].startBlinking()
				self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
				self.ready = False
				self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVHeuteView))
			elif self.current == 'searchmenu':
				self['searchmenu'].pageDown()
			else:
				self['textpage'].pageDown()
		except IndexError:
			pass

	def leftUp(self):
		try:
			for i in range(6):
				if self.current == 'menu%s' % i:
					self['menu%s' % i].selectionEnabled(0)
					self['menu%s' % ((i - 1) % 6)].selectionEnabled(1)
					self.current = 'menu%s' % ((i - 1) % 6)
					break
			if self.current == 'menu5':
				self.count = self.count - 1 if self.count > 1 else self.maxpages
				if search('date', self.link):
					self.link = self.link + 'FIN'
					date = findall('date=(.*?)FIN', self.link)
					self.link = sub('page=.*?FIN', '', self.link)
					self.link = self.link + 'page=' + str(self.count) + '&date=' + date[0]
				else:
					self.link = self.link + 'FIN'
					self.link = sub('page=.*?FIN', '', self.link)
					self.link = self.link + 'page=' + str(self.count)
				self['label'].setText('Bitte warten...')
				self['label'].startBlinking()
				self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
				self.ready = False
				self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVHeuteView))
			elif self.current == 'searchmenu':
				self['searchmenu'].pageUp()
			else:
				self['textpage'].pageUp()
		except IndexError:
			pass

	def down(self):
		if self.current == 'searchmenu':
			self['searchmenu'].down()
		elif self.current.startswith("menu"):
			self[self.current].down()
		else:
			self['textpage'].pageDown()

	def up(self):
		if self.current == 'searchmenu':
			self['searchmenu'].up()
		elif self.current.startswith("menu"):
			self[self.current].up()
		else:
			self['textpage'].pageUp()

	def getPics(self, output, idx):
		with open(self.pics[idx], 'wb') as f:
			f.write(output)
		if fileExists(self.pics[idx]):
			try:
				self['pic%s' % idx].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
				self['pic%s' % idx].instance.setPixmapFromFile(self.pics[idx])
			except:
				currPic = loadJPG(self.pics[idx])
				self['pic%s' % idx].instance.setScale(1)
				self['pic%s' % idx].instance.setPixmap(currPic)

	def idownloadPic(self, link, name, idx):
		getPage(ensure_binary(link)).addCallback(name, idx).addErrback(self.downloadError)

	def download(self, link, name):
		getPage(ensure_binary(link)).addCallback(name).addErrback(self.downloadError)

	def downloadError(self, output):
		pass
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

	def downloadPostPage(self, link, name):
		downloadPage(ensure_binary(link), self.localhtml2).addCallback(name).addErrback(self.downloadError)

	def downloadFullPage(self, link, name):
		if self.MeinTVS:
			try:
				response = self.opener.open(link, timeout=60)
				data = response.read()
				with open(self.localhtml, 'wb') as f:
					f.write(data)
				response.close()
			except HTTPException as e:
				self.error = 'HTTP Exception Error ' + str(e)
			except HTTPError as e:
				self.error = 'HTTP Error: ' + str(e.code)
			except URLError as e:
				self.error = 'URL Error: ' + str(e.reason)
			except error as e:
				self.error = 'Socket Error: ' + str(e)
			except AttributeError as e:
				self.error = 'Attribute Error: ' + str(e.message)

			if not self.error:
				self.makeTVHeuteView('')
			else:
				self.makeErrorTimer = eTimer()
				self.makeErrorTimer.callback.append(self.displayError)
				self.makeErrorTimer.start(200, True)
		else:
			downloadPage(ensure_binary(link), self.localhtml).addCallback(name).addErrback(self.downloadPageError)

	def displayError(self):
		self.session.openWithCallback(self.closeError, MessageBox, '%s' % self.error, MessageBox.TYPE_ERROR)

	def closeError(self, retval):
		self.close()

	def downloadPageError(self, output):
		self['label'].setText('Info = +- Tageszeit, Bouquet = +- Tag, <> = +- Woche, Menue = Senderliste')
		self['label'].stopBlinking()
		self['label'].show()
		self.ready = True

	def showProgrammPage(self):
		self['label2'].setText('= Timer')
		self['label3'].setText('= Suche')
		self['label4'].setText('= Zappen')
		self.infotextHide()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self._tvinfoHide()
		for i in range(6):
			self['sender%s' % i].show()
			self['picon%s' % i].show()
			self['pic%s' % i].show()
			self['pictime%s' % i].show()
			self['pictext%s' % i].show()
			self['menu%s' % i].show()

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.current == 'menu0' or self.current == 'menu1' or self.current == 'menu2' or self.current == 'menu3' or self.current == 'menu4' or self.current == 'menu5':
			self.close()
		elif self.current == 'searchmenu':
			self.search = False
			self.oldsearchindex = 1
			self['searchmenu'].hide()
			self['searchtext'].hide()
			self.setTitle('')
			self.setTitle(self.titel)
			self.current = self.currentsearch
			self.showProgrammPage()
		elif self.current == 'postview' and not self.search:
			self.postviewready = False
			self.setTitle('')
			self.setTitle(self.titel)
			self.current = self.oldcurrent
			self.showProgrammPage()
		elif self.current == 'postview' and self.search:
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'

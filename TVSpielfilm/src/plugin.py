# -*- coding: utf-8 -*-
from __future__ import absolute_import
from base64 import b64decode, b64encode
from datetime import date, datetime, timedelta
from glob import glob
from html import unescape
from json import dumps, loads
from os import linesep, remove, rename
from os.path import join, isdir, isfile
from re import S, findall, search, sub
from requests import get, exceptions
from socket import error as SocketError
from six import ensure_binary, ensure_str
from six.moves.http_client import HTTPException
from six.moves.urllib.error import HTTPError, URLError
from six.moves.urllib.parse import quote
from six.moves.urllib.request import HTTPCookieProcessor, HTTPHandler, HTTPRedirectHandler, build_opener
from time import gmtime, localtime, mktime, strftime
from twisted.internet.reactor import callInThread
from enigma import BT_HALIGN_CENTER, BT_KEEP_ASPECT_RATIO, BT_SCALE, BT_VALIGN_CENTER, RT_HALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, RT_VALIGN_BOTTOM, RT_WRAP, eConsoleAppContainer, eEPGCache, eServiceCenter, eServiceReference, eTimer, loadJPG, loadPNG
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigDirectory, ConfigInteger, ConfigPassword, ConfigSelection, ConfigSubsection, ConfigText, ConfigYesNo, ConfigSelectionNumber, configfile, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryProgress, MultiContentEntryText
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Plugins.Plugin import PluginDescriptor
from RecordTimer import RecordTimerEntry
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.TimerEdit import TimerSanityConflict
from Screens.TimerEntry import TimerEntry
from Screens.VirtualKeyBoard import VirtualKeyBoard
from ServiceReference import ServiceReference
from Tools.Directories import isPluginInstalled
from .parser import NEXTPage1, NEXTPage2, buildTVTippsArray, cleanHTML, parsedetail, parseNow, parsePrimeTimeTable, parseTrailerUrl, shortenChannel, transCHANNEL
from .util import DESKTOP_HEIGHT, DESKTOP_WIDTH, ICONPATH, PICONPATH, PICPATH, PLUGINPATH, SCALE, BlinkingLabel, ItemList, applySkinVars, channelDB, makeWeekDay, printStackTrace, readSkin, serviceDB

try:
	from cookielib import MozillaCookieJar
except Exception:
	from http.cookiejar import MozillaCookieJar

RELEASE = 'V6.9'
NOTIMER = '\nTimer nicht möglich:\nKeine Service Reference vorhanden, der ausgewählte Sender wurde nicht importiert.'
NOEPG = 'Keine EPG Informationen verfügbar'
HIDEFLAG = True
ALPHA = '/proc/stb/video/alpha' if isfile('/proc/stb/video/alpha') else None
SERVICEFILE = join(PLUGINPATH, 'db/service.references')
DUPESFILE = join(PLUGINPATH, 'db/dupes.references')
TIMERFILE = join(PLUGINPATH, 'db/timer.db')

config.plugins.tvspielfilm = ConfigSubsection()
if DESKTOP_WIDTH > 1280:
	config.plugins.tvspielfilm.plugin_size = ConfigSelection(default='FHD', choices=[('FHD', 'FullHD (1920x1080)'), ('HD', 'HD (1280x720)')])
else:
	config.plugins.tvspielfilm.plugin_size = ConfigSelection(default='HD', choices=[('HD', 'HD (1280x720)')])
config.plugins.tvspielfilm.position = ConfigInteger(40, (0, 160))
config.plugins.tvspielfilm.font = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
if config.plugins.tvspielfilm.font.value == 'yes':
	from enigma import addFont
	try:
		addFont(join(PLUGINPATH, 'font/Roboto-Regular.ttf'), 'Regular', 100, False)
	except Exception as ex:
		addFont(join(PLUGINPATH, 'font/Roboto-Regular.ttf'), 'Regular', 100, False, 0)
config.plugins.tvspielfilm.font_size = ConfigSelection(default='normal', choices=[('large', 'Groß'), ('normal', 'Normal'), ('small', 'Klein')])
config.plugins.tvspielfilm.meintvs = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.login = ConfigText(default='', fixed_size=False)
config.plugins.tvspielfilm.password = ConfigPassword(default='', fixed_size=False)
config.plugins.tvspielfilm.encrypt = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.picon = ConfigSelection(default='image', choices=[('plugin', 'vom Plugin'), ('image', 'vom Image'), ('user', 'vom eigenen Ordner')])
config.plugins.tvspielfilm.piconfolder = ConfigDirectory(default=PICONPATH)
fullpaths = glob(join(PLUGINPATH, 'pics/FHD/selectors/selector_*.png')) if config.plugins.tvspielfilm.plugin_size == 'FHD' else glob(join(PLUGINPATH, 'pics/HD/selectors/selector_*.png'))
selectors = list(set([i[i.rfind('_') + 1:].replace('.png', '') if '_' in i else None for i in fullpaths]))
config.plugins.tvspielfilm.selectorcolor = ConfigSelection(default='Standard', choices=selectors)
config.plugins.tvspielfilm.tipps = ConfigSelection(default='yes', choices=[('no', 'Gruene Taste im Startmenue'), ('yes', 'Beim Start des Plugins'), ('false', 'Deaktiviert')])
config.plugins.tvspielfilm.primetime = ConfigSelection(default='primetime', choices=[('primetime', 'Primetime'), ('now', 'Aktuelle Zeit')])
config.plugins.tvspielfilm.eventview = ConfigSelection(default='list', choices=[('list', 'Programmliste'), ('info', 'Sendungsinfo')])
config.plugins.tvspielfilm.genreinfo = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
config.plugins.tvspielfilm.zapexit = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.maxlist = ConfigSelectionNumber(5, 40, 1, default=15)
config.plugins.tvspielfilm.maxsearch = ConfigSelectionNumber(1, 20, 1, default=2)
config.plugins.tvspielfilm.autotimer = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
config.plugins.tvspielfilm.ytresolution = ConfigSelection(default='best', choices=[('best', 'bestmöglich'), ('best[height<=?480]', 'max. 480p')])
config.plugins.tvspielfilm.debuglog = ConfigYesNo(default=False)
config.plugins.tvspielfilm.logtofile = ConfigYesNo(default=False)


def TVSlog(info, wert='', debug=False):
	if debug and not config.plugins.tvspielfilm.debuglog.value:
		return
	if config.plugins.tvspielfilm.logtofile.value:
		try:
			with open('/home/root/logs/tvspielfilm.log', 'a') as f:
				f.write('%s %s %s\r\n' % (strftime('%H:%M:%S'), info, wert))
		except IOError:
			TVSlog("Logging-Error in 'globals:TVSlog': %s" % IOError)
	else:
		print('[TVSpielfilm] %s %s' % (info, wert))


if not ALPHA:
	print('Alphachannel not found! Hide/show-function (=blue button) is disabled')
	TVSlog('Alphachannel not found! Hide/show-function (=blue button) is disabled')


def showPic(pixmap, picpath):
	if isfile(picpath):
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


def getPiconname(LOGO, sref=None):
	if sref is not None and sref != "nope":
		fallback = sref.split(":")  # Fallback from "1:0:*:..." to "1:0:1:..."
		fallback[2] = "1"
		fallback = ":".join(fallback)
		fallback = ("%sFIN" % fallback).replace(":", "_").replace("_FIN", "").replace("FIN", "")
		sref = ("%sFIN" % sref).replace(":", "_").replace("_FIN", "").replace("FIN", "")
	else:
		fallback = None
	if config.plugins.tvspielfilm.picon.value == "user":   # user picons
		for picon in [sref, fallback, LOGO]:
			pngname = "%s%s.png" % (config.plugins.tvspielfilm.piconfolder.value, picon)
			if LOGO is not None and isfile(pngname):
				return pngname
	elif config.plugins.tvspielfilm.picon.value == "image":  # image picons
		for picon in [sref, fallback, LOGO]:
			pngname = "%s%s.png" % (PICONPATH, picon)
			if LOGO is not None and isfile(pngname):
				return pngname
	for picon in [LOGO, sref, fallback]:
		pngname = join(PLUGINPATH, "picons/%s.png" % picon)  # plugin picons
		if LOGO is not None and isfile(pngname):
			return pngname
	return ""


class TVSAllScreen(Screen):
	def __init__(self, session, skin=None, dic=None, scale=False):
		w = DESKTOP_WIDTH - (80 * SCALE)
		mw = w - (20 * SCALE)
		self.menuwidth = mw
		if dic is None:
			dic = {}
		dic['picpath'] = PICPATH
		dic['selbg'] = str(config.plugins.tvspielfilm.selectorcolor.value)
		if skin:
			self.skin = applySkinVars(skin, dic)
		Screen.__init__(self, session)
		self.fontlarge = True if config.plugins.tvspielfilm.font_size.value == 'large' else False
		self.fontsmall = True if config.plugins.tvspielfilm.font_size.value == 'small' else False
		self.baseurl = 'https://www.tvspielfilm.de'

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def threadGetPage(self, link, success, fail=None):
		try:
			response = get(ensure_binary(link))
			response.close()
			response.raise_for_status()
			success(response.content)
		except exceptions.RequestException as error:
			printStackTrace()
			if fail is not None:
				fail(error)

	def threadDownloadPage(self, link, file, success, fail=None):
		try:
			response = get(link)
			response.close()
			response.raise_for_status()
			with open(file, 'wb') as f:
				f.write(response.content)
			success()
		except exceptions.RequestException as error:
			printStackTrace()
			if fail is not None:
				fail(error)

	def threadDownloadError(self, output):
		TVSlog("Downloaderror in module 'TVSAllScreen:showDownloadError':", output)
		self.showDownloadError(output)

	def showDownloadError(self, output):
		try:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output.getErrorMessage(), MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)
		self.close()

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

	def makeTimerDB(self):
		e2timer = '/etc/enigma2/timers.xml'
		if isfile(e2timer):
			timerxml = open(e2timer).read()
			timers = findall(r'<timer begin="(.*?)" end=".*?" serviceref="(.*?)"', timerxml)
			with open(TIMERFILE, 'w') as f:
				self.timer = []
				for timer in timers:
					timerstart = int(timer[0]) + int(config.recording.margin_before.value) * 60
					timerday = strftime('%Y-%m-%d', localtime(timerstart))
					timerhour = strftime('%H:%M', localtime(timerstart))
					self.timer.append("%s:::%s:::%s" % (timerday, timerhour, timer[1]))
				f.write('\n'.join(self.timer))

	def getFill(self, text):
		return '______________________________________\n%s\n' % text


class TVSAllScreenFull(TVSAllScreen):
	skin = '''<screen position="0,0" size="{size}"></screen>'''

	def __init__(self, session):
		size = "%s,%s" % (DESKTOP_WIDTH, DESKTOP_HEIGHT)
		dic = {'size': size}
		TVSAllScreen.__init__(self, session, TVSAllScreenFull.skin, dic)


class TVSBaseScreen(TVSAllScreen):
	def __init__(self, session, skin=None, dic=None, scale=True):
		TVSAllScreen.__init__(self, session, skin, dic, scale)
		self.current = 'menu'
		self.oldcurrent = 'menu'
		self.start = ''
		self.end = ''
		self.day = ''
		self.name = ''
		self.shortdesc = ''
		self.trailer = False
		self.trailerurl = ''
		self.searchcount = 0
		self.picfile = '/tmp/tvspielfilm.jpg'
		self.pics = []
		for i in range(6):
			self.pics.append('/tmp/tvspielfilm%s.jpg' % i)
		self.localhtml = '/tmp/tvspielfilm.html'
		self.localhtml2 = '/tmp/tvspielfilm2.html'
		self.tagestipp = False
		self.finishedTimerMode = 0
		self.showgenre = config.plugins.tvspielfilm.genreinfo.value != 'no'

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
				if self.finishedTimerMode == 1:
					self.refresh()
				if self.finishedTimerMode == 2:
					self.makeTVHeuteView()
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

	def hideTVinfo(self):
		for i in range(5):
			self['tvinfo%s' % i].hide()

	def hideInfotext(self):
		for i in range(9):
			self['infotext%s' % i].hide()
		self['picon'].hide()
		self['playlogo'].hide()
		self['searchtext'].hide()
		self['searchmenu'].hide()

	def setTVTitle(self, output):
		title = search(r'<title>(.*?)</title>', output)
		title = title.group(1).replace('&amp;', '&') if title is not None else ""
		title = sub(r' - TV Spielfilm', '', title)
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

	def getPics(self, picurllist, offset, show=True, playshow=False):
		for i in range(6):
			try:
				picurl = picurllist[offset + i]
				callInThread(self.picDownload, picurl, i)
				if show:
					self['pic%s' % i].show()
				if playshow:
					self['play%s' % i].show()
			except IndexError:
				if playshow:
					self['play%s' % i].hide()
				if show:
					self['pic%s' % i].hide()

	def picDownload(self, link, idx):
		try:
			response = get(link)
			response.close()
			response.raise_for_status()
			with open(self.pics[idx], 'wb') as f:
				f.write(response.content)
			if isfile(self.pics[idx]):
				self['pic%s' % idx].instance.setPixmapFromFile(self.pics[idx])
		except OSError as error:
			self.showDownloadError(error)

	def infotextStartEnd(self, infotext):
		part = infotext[1].strip()
		if 'heute' in infotext[0].strip().lower():
			d = sub(r'....-', '', str(self.date))
			d2 = sub(r'-..', '', d)
			d3 = sub(r'..-', '', d)
			part = 'he %s.%s.' % (d3, d2)
		else:
			part = sub(r'.,', '', infotext[0].strip())
		day = sub(r'.. ', '', part)
		self.day = sub(r'[.]..[.]', '', day)
		month = sub(r'.. ..[.]', '', part)
		month = sub(r'[.]', '', month)
		datum = '%sFIN' % self.date
		year = search(r'\d+', sub(r'......FIN', '', datum))
		year = year.group(0) if year else self.date[:4]
		self.postdate = "%s-%s-%s" % (year, month, self.day)
		today = date(int(year), int(month), int(self.day))
		one_day = timedelta(days=1)
		self.nextdate = today + one_day
		part = infotext[1].split(' - ')
		self.start = part[0].replace(' Uhr', '').strip()
		self.end = part[1].replace(' Uhr', '').strip()

	def showInfotext(self, infotexts):
			for i, infotext in enumerate(infotexts):
				if i < 9:
					try:
						self['infotext%s' % i].setText(infotext)
						self['infotext%s' % i].show()
					except IndexError:
						self['infotext%s' % i].hide()

	def showRatinginfos(self, output):
		startpos = output.find('<section class="broadcast-detail__rating">')
		endpos = output.find('<section class="broadcast-detail__description">')
		bereich = output[startpos:endpos]
		bereich = cleanHTML(bereich)
		ratinglabels = findall(r'<span class="broadcast-detail__rating-label">(.*?)</span>', bereich)  # Humor, Anspruch, Action, Spannung, Erotik
		ratingdots = findall(r'<span class="broadcast-detail__rating-dots__rating rating-(.*?)">', bereich)
		for i, ri in enumerate(ratinglabels):
			if len(ratingdots) <= i:
				ratingdots.append('0')
			ratingfile = join(ICONPATH, 'pointbar%s.png' % ratingdots[i])
			if isfile(ratingfile):
				try:
					self['ratinglabel%s' % i].setText(ri)
					self['ratinglabel%s' % i].show()
					self['ratingdot%s' % i].instance.setPixmapFromFile(ratingfile)
					self['ratingdot%s' % i].show()
				except IndexError:
					pass
		starslabel = findall(r'<span class="rating-stars__label">(.*?)</span>', bereich)  # Community
		starsrating = findall(r'<span class="rating-stars__rating" data-rating="(.*?)"></span>', bereich)
		if len(starsrating):
			starsfile = join(ICONPATH, 'starbar%s.png' % starsrating[0])
			if isfile(starsfile):
				try:
					self['starslabel'].setText(starslabel[0])
					self['starslabel'].show()
					self['starsrating'].instance.setPixmapFromFile(starsfile)
					self['starsrating'].show()
				except IndexError:
					pass

	def hideRatingInfos(self):
		for i in range(5):
			self['ratinglabel%s' % i].hide()
			self['ratingdot%s' % i].hide()
		self['starslabel'].hide()
		self['starsrating'].hide()

	def getShortdesc(self, output):
		startpos = output.find('<article class="broadcast-detail" >')
		endpos = output.find('<section class="teaser-section">')
		bereich = output[startpos:endpos]
		names = findall(r'<h1\s*class="headline\s*headline\-\-article\s*broadcast\s*stage\-heading">(.*?)</h1>', bereich)
		extensions = findall(r'<span class="info">(.*?)</span>', bereich)
		extensions = [item.replace("Staffel ", " S") if "Staffel" in item else item for item in extensions]
		extensions = [item.replace("Folge ", " F") if "Folge" in item else item for item in extensions]
		extensions = [item.replace("Episode ", " E") if "Folge" in item else item for item in extensions]
		self.name = "".join(names + extensions)
		shortdesc = findall(r'<span class="text-row">(.*?)</span>', bereich)
		self.shortdesc = shortdesc[0] if shortdesc else "{keine Kurzbeschreibung gefunden}"

	def makePostTimer(self, output):
		output = ensure_str(output)
		startpos = output.find('<div class="content-area">')
		endpos = output.find('<h2 class="broadcast-info">')
		bereich = unescape(output[startpos:endpos]).replace("&shy;", "-")
		infotext = self.getInfotext(bereich)
		self.infotextStartEnd(infotext)
		self.getShortdesc(bereich)
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

	def hideMenubar(self):
		self['CHANNELkey'].hide()
		self['CHANNELtext'].hide()
		self['BOUQUETkey'].hide()
		self['BOUQUETtext'].hide()
		self['INFOkey'].hide()
		self['INFOtext'].hide()

	def showMenubar(self):
		self['CHANNELkey'].show()
		self['CHANNELtext'].show()
		self['BOUQUETkey'].show()
		self['BOUQUETtext'].show()
		self['INFOkey'].show()
		self['INFOtext'].show()

	def _makePostviewPage(self):
		output = ensure_str(open(self.localhtml2, 'r').read())
		self['label2'].setText('Timer')
		self['label2'].show()
		self['label3'].setText('YouTube Trailer')
		self['label3'].show()
		self['label4'].hide()
		self['label6'].hide()
		self.setBlueButton('Aus-/Einblenden')
		self.hideMenubar()
		self['searchmenu'].hide()
		self['searchtext'].hide()
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
		trailerurl = parseTrailerUrl(bereich)
		if trailerurl:
			self.trailerurl = trailerurl
			self.trailer = True
		else:
			self.trailer = False
		bereich = sub(r'" alt=".*?" width="', '" width="', bereich)
		picurl = search(r'<img src="(.*?)" data-src="(.*?)" width="', bereich)
		if picurl:
			callInThread(self.downloadPicPost, picurl.group(2), True)
		else:
			picurl = search(r'<meta property="og:image" content="(.*?)"', output)
			if picurl:
				callInThread(self.downloadPicPost, picurl.group(1), True)
			else:
				picurl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
				callInThread(self.downloadPicPost, picurl, True)
		if not self.search:
			title = search(r'<title>(.*?)</title>', output)
			if title:
				title = unescape(title.group(1)).replace("&shy;", "-")
			self.setTitle(title)
		if search(r'<ul class="rating-dots">', bereich):
			self.movie = True
		else:
			self.movie = False
		self.hideMenubar()
		if search(r'<div class="film-gallery">', output):
			self.mehrbilder = True
			if self.trailer:
				self['label_OK'].setText('Zum Video')
				self['button_TEXT'].show()
				self['label_TEXT'].setText('Zur Fotostrecke')
				self['label_TEXT'].show()
			else:
				self['label_OK'].setText('Zur Fotostrecke')
				self['button_TEXT'].hide()
				self['label_TEXT'].hide()
			self['button_INFO'].show()
		else:
			self.mehrbilder = False
			if self.trailer:
				self['label_OK'].setText('Zum Video')
				self['button_TEXT'].show()
				self['label_TEXT'].setText('Vollbild')
				self['label_TEXT'].show()
			else:
				self['label_OK'].setText('Vollbild')
				self['button_TEXT'].hide()
				self['label_TEXT'].hide()
		self['button_OK'].show()
		self['label_OK'].show()
		self['button_7_8_9'].show()
		self['Line_top'].show()
		self['Line_mid'].show()
		self['Line_down'].show()
		self['button_INFO'].show()
		self['label_INFO'].setText('EPG')
		self['label_INFO'].show()
		infotext = self.getInfotext(bereich)
		self['piclabel2'].setText(infotext[2])
		self.infotextStartEnd(infotext)
		self['piclabel'].setText(self.start[0:5])
		self.showInfotext(infotext)
		self.showRatinginfos(bereich)
		self.getShortdesc(bereich)
		self['waiting'].stopBlinking()
		# Infoausgabe: NEU, TIPP, LIVE
		tvinfo = []
		sref = self.service_db.lookup(infotext[2].lower())
		timer = '%s:::%s:::%s' % (self.postdate, self.start, sref)
		if timer in self.timer:
			tvinfo.append('REC')
		info = findall(r'<span class="add-info icon-new nodistance">(.*?)</span>', bereich)
		if len(info):
			tvinfo.append(info[0])
		info = findall(r'<span class="add-info icon-tip nodistance">(.*?)</span>', bereich)
		if len(info):
			tvinfo.append(info[0])
		info = findall(r'<span class="add-info icon-live nodistance">(.*?)</span>', bereich)
		if len(info):
			tvinfo.append(info[0])
		for i, ti in enumerate(tvinfo):
			self['tvinfo%s' % i].setText(ti)
			self['tvinfo%s' % i].show()
		if self.tagestipp:
			channel = findall(r"var adsc_sender = '(.*?)'", output)
			if len(channel):
				self.sref = self.service_db.lookup(channel[0].lower())
				if self.sref != "nope":
					self.zapflag = True
		picons = findall(r'<img src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*?).png.*?', bereich)
		picon = getPiconname(picons[0], self.service_db.lookup(picons[0]))
		if isfile(picon):
			self['picon'].instance.setScale(1)
			self['picon'].instance.setPixmapFromFile(picon)
			self['picon'].show()
		else:
			self['picon'].hide()
		rawtext = parsedetail(bereich)
		text = ''
		for part in rawtext.split('\n'):
			if ':' in part:
				text += '\n%s' % part if 'cast & crew:' in part.lower() else part
			else:
				text += "%s\n" % part
		fill = self.getFill('TV Spielfilm Online')
		self.POSTtext = "%s\n%s" % (text.strip(), fill)
		self['textpage'].setText(self.POSTtext)
		self['textpage'].show()
		self.showEPG = False
		self.postviewready = True

	def getInfotext(self, bereich):
		# weitere Sendungsinformationen
		startpos = bereich.find('<div class="text-wrapper">')
		endpos = bereich.find('<section class="broadcast-detail__stage')
		extract = bereich[startpos:endpos]
		text = findall(r'<span\s*class="text\-row">(.*?)</span>', extract, S)  # Suchstring voher mit re.escape wandeln
		# Sendezeit & Sender
		startpos = bereich.find('<div class="schedule-widget__header__attributes">')
		infotext = []
		if startpos > 0:
			endpos = bereich.find('<div class="schedule-widget__tabs">')
			extract = bereich[startpos:endpos]
			infotext = findall(r'<li>(.*?)</li>', extract)
			index = 1 if len(text) > 1 else 0
			infotext.extend(text[index].strip().split(' | '))
			self.start = infotext[1]
		else:  # manche Sendungen benötigen eine andere Auswertung
			channel = search(r"data\-layer\-categories='(.*?)'\s*", bereich, flags=S)
			if not channel:  # Alternative 1
				channel = search(r"data\-tracking\-point='(.*?)'\s*", bereich, flags=S)
			channel = loads(channel.group(1))['channel'] if channel else None
			if not channel:  # Alternative 2
				channel = search(r'srcset=".*?mini/(.*?)\.', bereich)
				channel = channel.group(1).upper() if channel else "{Sender unbekannt}"
			zeit = search(r'<span\s*class="stage\-underline\s*gray">(.*?)</span>', bereich, flags=S)
			zeit = zeit.group(1) if zeit else "{Zeit unbekannt}"
			zeit = sub(r"(\d+:\d+)\s*\-\s*(\d+:\d+)", "\g<1> Uhr - \g<2> Uhr", zeit)
			infotext = zeit.strip().split(' | ')
			if len(infotext) > 2:
				infotext[2] = channel
			else:
				infotext.append(channel)
			if len(text):
				index = 1 if len(text) > 1 else 0
				infotext.extend(text[index].strip().split(' | '))
				self.start = infotext[1][0:5]
			else:
				self.start = ''
		part = ''
		if len(text) > 2:
			for pi in text[2].split(', '):
				if pi.find('(') > 0:
					part = pi
				elif pi.find(')') > 0:
					infotext.append("%s, %s" % (part, pi))
				else:
					infotext.append(pi)
		return infotext

	def showsearch(self):
		self.postviewready = False
		self.hideInfotext()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self.hideTVinfo()
		self['seitennr'].hide()
		self['label2'].show()
		self['label3'].hide()
		self['label4'].hide()
		self['label5'].show()
		self['searchmenu'].show()
		self['searchtext'].show()

	def getPicPost(self, output, label):
		with open(self.picfile, 'wb') as f:
			f.write(output)
		self.showPicPost(label)

	def showPicPost(self, label=False):
		if isfile(self.picfile):
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
				self['playlogo'].show()

	def downloadPicPost(self, link, label):
		link = sub(r'.*?data-src="', '', link)
		try:
			response = get(link)
			response.close()
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.downloadPicPostError(error)
		else:
			self.getPicPost(response.content, label)

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
				self.name = sub(r'Die ', '', self.name)
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
				self.session.open(TVSPicShow, self.postlink)
			else:
				self.session.openWithCallback(self.showPicPost, TVSFullScreen)

	def redTimer(self, searching=False, sref=None):
		if sref is None:
			if searching:
				c = self['searchmenu'].getSelectedIndex()
				self.oldsearchindex = c
				sref = self.searchref[c]
			else:
				c = self['menu'].getSelectedIndex()
				self.oldindex = c
				sref = self.sref[c]
		serviceref = ServiceReference(sref)
		start = self.start
		s1 = sub(r':..', '', start)
		datum = '%sFIN' % self.postdate
		datum = sub(r'..FIN', '', datum)
		datum = datum + self.day
		parts = start.split(':')
		seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
		seconds -= int(config.recording.margin_before.value) * 60
		start = strftime('%H:%M:%S', gmtime(seconds))
		s2 = sub(r':..:..', '', start)
		start = "%s %s" % (self.date, start) if int(s2) > int(s1) else "%s %s" % (datum, start)
		start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
		end = self.end
		parts = end.split(':')
		seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
		seconds += int(config.recording.margin_after.value) * 60
		end = strftime('%H:%M:%S', gmtime(seconds))
		e2 = sub(r':..:..', '', end)
		end = "%s %s" % (self.nextdate, end) if int(s2) > int(e2) else "%s %s" % (datum, end)
		end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
		name = self.name
		shortdesc = self.shortdesc
		if shortdesc != '' and search(r'Staffel [0-9]+, Episode [0-9]+', shortdesc):
			episode = search(r'(Staffel [0-9]+, Episode [0-9]+)', shortdesc)
			if episode is not None:
				episode = sub(r'Staffel ', 'S', episode.group(1))
				episode = sub(r', Episode ', 'E', episode)
			else:
				episode = ""
			name = "%s %s" % (name, episode)
		data = (int(mktime(start.timetuple())), int(mktime(end.timetuple())), name, shortdesc, None)
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
			self.session.openWithCallback(self.finishedAutoTimer, AutoTimerImporter, newTimer, self.name, int(mktime(start.timetuple())), int(mktime(end.timetuple())), None, serviceref, None, None, None, None)

	def setBlueButton(self, text):
		if ALPHA:
			self['bluebutton'].show()
			self['label5'].setText(text)
			self['label5'].show()
		else:
			self['bluebutton'].hide()
			self['label5'].hide()

	def _commonInit(self, ltxt='Suche', lltxt='Zappen'):
		self['picpost'] = Pixmap()
		for i in range(5):
			self['tvinfo%s' % i] = Label()
		self['picon'] = Pixmap()
		self['playlogo'] = Pixmap()
		self['searchtext'] = Label()
		for i in range(9):
			self['infotext%s' % i] = Label()
		for i in range(5):
			self['ratinglabel%s' % i] = Label()
			self['ratingdot%s' % i] = Pixmap()
		self['starslabel'] = Label()
		self['starsrating'] = Pixmap()
		self['searchmenu'] = ItemList([])
		self['textpage'] = ScrollLabel()
		self['piclabel'] = Label()
		self['piclabel'].hide()
		self['piclabel2'] = Label()
		self['piclabel2'].hide()
		self['release'] = Label(RELEASE)
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['seitennr'] = Label()
		self['label2'] = Label('Timer')
		self['label3'] = Label(ltxt)
		self['label4'] = Label(lltxt)
		self['label5'] = Label()
		self['label6'] = Label('MENU')
		self['bluebutton'] = Label()
		self.setBlueButton('Aus-/Einblenden')

	def makeSearchView(self, url):
		self.hideMenubar()
		response = None
		try:
			response = get(url)
			response.close()
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.showDownloadError(error)
			self.close()
		output = ensure_str(response.content) if response is not None else ""
		title = search(r'<title>(.*?)</title>', output[:300])
		if title:
			self['searchtext'].setText(title.group(1))
			self['searchtext'].show()
			self.setTitle(title.group(1))
		startpos = output.find('<table class="primetime-table">')
		endpos = output.find('</table>')
		output = output[startpos:endpos]
		items, bereich = parsePrimeTimeTable(output)
		mh = int(47 * SCALE + 0.5)
		for DATUM, START, TITLE, GENRE, LOGO, LINK, RATING in items:
			datum_string = ""
			if DATUM:
				datum_string = DATUM
				res_datum = [DATUM]
				res_datum.append(MultiContentEntryText(pos=(int(3 * SCALE), int(2 * SCALE)), size=(int(200 * SCALE), mh), font=0, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text=DATUM))
				self.searchref.append('na')
				self.searchlink.append('na')
				self.searchentries.append(res_datum)
				continue
			res = [LOGO]
			start = START
			res.append(MultiContentEntryText(pos=(int(70 * SCALE), 0), size=(int(130 * SCALE), mh), font=0, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=START))
			res.append(MultiContentEntryText(pos=(int(190 * SCALE), 0), size=(int(840 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=TITLE))
			if LOGO:
				sref = self.service_db.lookup(LOGO)
				if sref != "nope":
					self.searchref.append(sref)
				png = getPiconname(LOGO, sref)
				if png:
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
				else:
					res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
				start = sub(r' - ..:..', '', start)
				daynow = sub(r'....-..-', '', str(self.date))
				day = search(r', ([0-9]+). ', datum_string)
				if day:
					day = day.group(1)
				else:
					day = daynow
				if int(day) >= int(daynow) - 1:
					datum = '%sFIN' % self.date
				else:
					four_weeks = timedelta(weeks=4)
					datum = '%sFIN' % (self.date + four_weeks)
				datum = sub(r'[0-9][0-9]FIN', day, datum)
				timer = '%s:::%s:::%s' % (datum, start, sref)
				if timer in self.timer:
					self.rec = True
					png = ICONPATH + 'rec.png'
					if isfile(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), int(16 * SCALE)), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
				self.searchlink.append(LINK)
				if GENRE:
					res.append(MultiContentEntryText(pos=(int(940 * SCALE), 0), size=(int(220 * SCALE), mh), font=0, color_sel=16777215, flags=RT_HALIGN_RIGHT | RT_VALIGN_CENTER | RT_WRAP, text=GENRE))
				self.datum = False
				self.rec = False
				if RATING:  # DAUMEN
					if RATING != 'rating small':
						RATING = RATING.replace(' ', '-')
						png = '%s%s.png' % (ICONPATH, RATING)
						if isfile(png):
							res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1220 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
				self.searchentries.append(res)
		self['searchmenu'].l.setItemHeight(mh)
		self['searchmenu'].l.setList(self.searchentries)
		self['searchmenu'].show()
		self.searchcount += 1
		if self.searchcount <= config.plugins.tvspielfilm.maxsearch.value and search(NEXTPage1, bereich):
			nextpage = search(NEXTPage2, bereich)
			if nextpage:
				self.makeSearchView(nextpage.group(1))
			else:
				self.ready = True
		else:
			if self.searchref:
				if self.searchref[-1] == 'na':
					del self.searchref[-1]
					del self.searchlink[-1]
					del self.searchentries[-1]
					self['searchmenu'].l.setList(self.searchentries)
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
				self.session.open(TVSPicShow, self.postlink)
			else:
				self.session.openWithCallback(self.showPicPost, TVSFullScreen)
		else:
			self.selectPage('ok')
		if self.current == 'searchmenu':
			self.selectPage('ok')


class TVSTippsView(TVSBaseScreen):
	def __init__(self, session, link, sparte):
		global HIDEFLAG
		skin = readSkin("TVSTippsView")
		TVSBaseScreen.__init__(self, session, skin)
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
		self.len = 0
		self.oldindex = 0
		self.oldsearchindex = 1
		self['release'] = Label(RELEASE)
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		for i in range(6):
			self['pic%s' % i] = Pixmap()
		self._commonInit()
		self.hideInfotext()
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
		self.service_db = serviceDB(SERVICEFILE)
		if isfile(TIMERFILE):
			self.timer = open(TIMERFILE).read().split('\n')
		else:
			self.timer = ''
		self.date = date.today()
		one_day = timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		callInThread(self.threadDownloadPage, link, self.localhtml, self.makeTVTipps, self.downloadError)

	def makeTVTipps(self, output):
		output = ensure_str(output)
		self.sref = []
		self['release'].show()
		self['waiting'].stopBlinking()
		for i in range(6):
			self['pic%s' % i].hide()
		items = buildTVTippsArray(self.sparte, output)
		date = str(strftime('%d.%m.%Y'))
		self.titel = 'TV-Tipps - %s - %s, %s' % (self.sparte, self.weekday, date)
		if self.sparte == 'neu':
			self.titel = 'TV Neuerscheinungen - %s, %s' % (self.weekday, date)
		self.setTitle(self.titel)
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.picurllist = []
		mh = int(47 * SCALE + 0.5)
		for LINK, PIC, TIME, INFOS, NAME, GENRE, LOGO in items:
			sref = self.service_db.lookup(LOGO)
			self.new = False
			if LINK:
				res = [LINK]
				linkfilter = LINK
			else:
				res = []
				linkfilter = ''
			if PIC:
				picfilter = PIC
			else:
				picfilter = ''
			if TIME:
				start = TIME
				res.append(MultiContentEntryText(pos=(int(70 * SCALE), 0), size=(int(60 * SCALE), mh), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=TIME))
			else:
				start = ''
			icount = 0
			for INFO in INFOS:
				if search(r'neu|new', INFO) or self.sparte != "neu":
					self.new = True
				png = '%s%s.png' % (ICONPATH, INFO)
				if isfile(png):  # NEU, TIPP
					yoffset = int((mh - 14 * SCALE * len(INFOS)) / 2 + 14 * SCALE * icount)
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), yoffset), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
					icount += 1
			titelfilter = ""
			if NAME:
				titelfilter = NAME
				res.append(MultiContentEntryText(pos=(int(160 * SCALE), 0), size=(int(580 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=NAME))
			if GENRE:
				text = GENRE.replace(',', '\n', 1)
				res.append(MultiContentEntryText(pos=(int(1040 * SCALE), 0), size=(int(400 * SCALE), mh), font=-1,
						   color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT | RT_VALIGN_CENTER | RT_WRAP, text=text))
				if self.sparte == 'Spielfilm':
					png = join(ICONPATH, 'rating-small1.png')
					if isfile(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1220 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
			if LOGO:
				png = getPiconname(LOGO, sref)
				if png:
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
				else:
					res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
				if sref == "nope":
					sref = None
				elif self.new:
					hour = sub(r':..', '', start)
					if int(hour) < 5:
						one_day = timedelta(days=1)
						date = self.date + one_day
					else:
						date = self.date
					timer = '%s:::%s:::%s' % (date, start, sref)
					if timer in self.timer:
						png = join(ICONPATH, 'rec.png')
						if isfile(png):
							res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), int(16 * SCALE)), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
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
		self['CHANNELkey'].show()
		self['BOUQUETkey'].show()
		self['INFOkey'].show()
		self['MENUkey'].hide()
		self['TEXTkey'].hide()
		if self.sparte == 'neu':
			self['INFOkey'].hide()
		self['label'].show()
		self.ready = True

	def ok(self):
		self['TEXTkey'].hide()
		self['TEXTtext'].hide()
		self._ok()

	def selectPage(self, action):
		if self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.postlink = self.tvlink[c]
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.postlink = self.searchlink[c]
		if action == 'ok' and self.ready:
			if search(r'www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				callInThread(self.threadDownloadPage, self.postlink, self.localhtml2, self.makePostviewPage, self.downloadError)

	def makePostviewPage(self):
		self['menu'].hide()
		for i in range(6):
			self['pic%s' % i].hide()
		try:
			self._makePostviewPage()
		except:
			printStackTrace()

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
						s1 = sub(r':..', '', start)
						date = '%sFIN' % self.postdate
						date = sub(r'..FIN', '', date)
						date = date + self.day
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(r':..:..', '', start)
						start = "%s %s" % (self.date, start) if int(s2) > int(s1) else "%s %s" % (date, start)
						start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
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
								self.EPGtext += '\n\n%s' % short
							if ext:
								self.EPGtext += '\n\n%' % ext
							if dur:
								self.EPGtext += '\n\n%' % dur
					except:
						self.EPGText = getEPGText()
				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n%s' % fill
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

	def redDownload(self):
		if self.current == 'menu' and self.ready:
			self.oldindex = self['menu'].getSelectedIndex()
			self.postlink = self.tvlink[self.oldindex]
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			self.postlink = self.searchlink[c]
		else:
			return
		if search(r'www.tvspielfilm.de', self.postlink):
			self.oldcurrent = self.current
			callInThread(self.threadGetPage, self.postlink, self.makePostTimer, self.threadDownloadError)

	def red(self):
		if self.current == 'postview' and self.postviewready:
			self.redTimer(self.search is not None)
		else:
			self.redDownload()

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
				titel = self.tvtitel[c].split(', ')
				if len(titel) == 1:
					titel = titel[0].split(' ')
					titel = "%s %s" % (titel[0], titel[1]) if titel[0].find(':') > 0 else titel[0]
				elif len(titel) == 2:
					titel = titel[0].rsplit(' ', 1)[0]
				else:
					titel = titel[0]
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
			except IndexError:
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

	def searchReturn(self, search):
		if search and search != '':
			self.searchstring = search
			self['menu'].hide()
			for i in range(6):
				self['pic%s' % i].hide()
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			search = quote(search).replace('%20', '+')
			searchlink = "%s/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=%s" % (self.baseurl, search)
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(TVSsearchYouTube, self.name, self.movie)
		elif self.current == 'menu' and not self.search and self.ready:
			c = self['menu'].getSelectedIndex()
			try:
				titel = self.tvtitel[c]
				self.session.open(TVSsearchYouTube, titel, self.movie)
			except IndexError:
				pass

	def nextDay(self):
		self.changeday(1)

	def prevDay(self):
		self.changeday(-1)

	def nextWeek(self):
		self.changeday(7)

	def prevWeek(self):
		self.changeday(-7)

	def changeday(self, deltadays):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			timespan = timedelta(days=deltadays)
			if search(r'date', self.link):
				self.link = '%sFIN' % self.link
				date1 = findall(r'date=(.*?)-..-..FIN', self.link)
				date2 = findall(r'date=....-(.*?)-..FIN', self.link)
				date3 = findall(r'date=....-..-(.*?)FIN', self.link)
				try:
					today = date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = date.today()
				self.date = today + timespan
				self.nextdate = self.date + timespan
				self.link = "%s%s" % (sub(r'date=(.*?FIN)', 'date=', self.link), self.date)
			else:
				today = date.today()
				self.date = today + timespan
				self.nextdate = self.date + timespan
				self.link = "%s&date=%s" % (self.link, self.date)
			self.weekday = makeWeekDay(self.date.weekday())
			self.oldindex = 0
			self.refresh()
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

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

	def threadDownloadError(self, output):
		TVSlog("Downloaderror in module 'TVSTippsView:threadDownloadError':", output)
		self['CHANNELkey'].show()
		self['BOUQUETkey'].show()
		self['INFOkey'].show()
		self['MENUkey'].hide()
		self['TEXTkey'].hide()
		if self.sparte == 'neu':
			self['INFOkey'].hide()
		self['label'].show()
		self.ready = True
		self.showDownloadError(output)

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['waiting'].startBlinking()
		self['waiting'].show()
		callInThread(self.threadDownloadPage, self.link, self.localhtml, self.makeTVTipps, self.downloadError)

	def showProgrammPage(self):
		self['CHANNELkey'].show()
		self['BOUQUETkey'].show()
		self['INFOkey'].show()
		self['MENUkey'].hide()
		self['TEXTkey'].hide()
		if self.sparte == 'neu':
			self['INFOkey'].hide()
		self['label2'].setText('Timer')
		self['label2'].show()
		self['label3'].setText('Suche')
		self['label3'].show()
		self['label4'].setText('Zappen')
		self['label4'].show()
		self.hideInfotext()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self.hideTVinfo()
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
				self.getPics(self.picurllist, 0)
			elif c % 6 == 5:
				self.getPics(self.picurllist, c + 1)
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
				self.getPics(self.picurllist, l - d)
			elif c % 6 == 0:
				self.getPics(self.picurllist, c - 6)

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
			self.getPics(self.picurllist, c - d + 6)
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
			self.getPics(self.picurllist, c - d - 6, False)
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
			self.setTitle(self.titel)
		elif self.current == 'postview' and not self.search:
			self.hideRatingInfos()
			self.postviewready = False
			self.setTitle(self.titel)
			self.showProgrammPage()
			self['label_OK'].hide()
			self['label_TEXT'].hide()
			self['button_OK'].hide()
			self['button_TEXT'].hide()
			self['button_INFO'].hide()
			self['button_7_8_9'].hide()
		elif self.current == 'postview' and self.search:
			self.hideRatingInfos()
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


class TVSGenreJetztProgrammView(TVSBaseScreen):
	def __init__(self, session, link):
		global HIDEFLAG
		skin = readSkin("TVSProgrammView")
		TVSBaseScreen.__init__(self, session, skin)
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
		self.search = False
		self.postviewready = False
		self.mehrbilder = False
		self.oldindex = 0
		self.oldsearchindex = 1
		self.titel = ''
		self.date = date.today()
		self['menu'] = ItemList([])
		self['release'] = Label(RELEASE)
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['ready'] = Label("OK")
		self['seitennr'] = Label()
		self['CHANNELkey'] = Pixmap()
		self['CHANNELtext'] = Label()
		self['BOUQUETkey'] = Pixmap()
		self['BOUQUETtext'] = Label()
		self['INFOkey'] = Pixmap()
		self['INFOtext'] = Label()
		self['TEXTkey'] = Pixmap()
		self['TEXTtext'] = Label()
		self['button_OK'] = Pixmap()
		self['label_OK'] = Label()
		self['button_TEXT'] = Pixmap()
		self['label_TEXT'] = Label()
		self['button_INFO'] = Pixmap()
		self['label_INFO'] = Label()
		self['1_zapup'] = Pixmap()
		self['2_zapdown'] = Pixmap()
		self['button_7_8_9'] = Pixmap()
		self['Line_top'] = Label()
		self['Line_mid'] = Label()
		self['Line_down'] = Label()
		self['label5'] = Label()
		self['bluebutton'] = Label()
		self.setBlueButton('Aus-/Einblenden')


class TVSJetztView(TVSGenreJetztProgrammView):
	def __init__(self, session, link, standalone=True):
		TVSGenreJetztProgrammView.__init__(self, session, link)
		self.sref = []
		self.link1 = link
		self.link2 = link
		self.standalone = standalone
		self.jetzt = False
		self.gleich = False
		self.abends = False
		self.nachts = False
		self.date = date.today()
		self.finishedTimerMode = 1
		self.index = 0
		self._commonInit()
		self.hideInfotext()
		self.hideRatingInfos()
		self.hideTVinfo()
		self.showMenubar()
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
		self.service_db = serviceDB(SERVICEFILE)
		if isfile(SERVICEFILE):
			with open(SERVICEFILE, 'r') as f:
				lines = f.readlines()
			self.order = {}
			for idx, line in enumerate(lines):
				self.order[line.partition(' ')[0]] = idx
			self.date = date.today()
			if self.standalone:
				self.movie_stop = config.usage.on_movie_stop.value
				self.movie_eof = config.usage.on_movie_eof.value
				config.usage.on_movie_stop.value = 'quit'
				config.usage.on_movie_eof.value = 'quit'
				self.makeTimerDB()
			else:
				if isfile(TIMERFILE):
					self.timer = open(TIMERFILE).read().split('\n')
				else:
					self.timer = ''
			one_day = timedelta(days=1)
			self.nextdate = self.date + one_day
			self.weekday = makeWeekDay(self.date.weekday())
			if search(r'/sendungen/jetzt.html', link):
				self.jetzt = True
			elif search(r'time=shortly', link):
				self.gleich = True
			elif search(r'/sendungen/abends.html', link):
				self.abends = True
			elif search(r'/sendungen/fernsehprogramm-nachts.html', link):
				self.nachts = True
			callInThread(self.threadGetPage, link, self.makeTVJetztView, self.downloadError)
			self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self['label_OK'].hide()
		self['label_TEXT'].hide()
		self['label_INFO'].hide()
		self['button_OK'].hide()
		self['button_TEXT'].hide()
		self['button_INFO'].hide()
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['ready'].hide()
		self['seitennr'].hide()
		self['CHANNELkey'].hide()
		self['CHANNELtext'].hide()
		self['BOUQUETkey'].hide()
		self['BOUQUETtext'].hide()
		self['TEXTkey'].show()
		self['TEXTtext'].setText('Sender')
		self['TEXTtext'].show()
		self['INFOtext'].setText('Jetzt/Gleich im TV')
		self['INFOtext'].show()

	def makeTVJetztView(self, output):
		output = ensure_str(output)
		datum = str(strftime('%d.%m.%Y'))
		self['TEXTtext'].setText('Sender')
		self['TEXTtext'].show()
		self['INFOtext'].setText('Jetzt/Gleich im TV')
		self['INFOtext'].show()
		if self.jetzt:
			self.titel = 'Jetzt'
			self['CHANNELkey'].hide()
			self['CHANNELtext'].hide()
			self['BOUQUETkey'].hide()
			self['BOUQUETtext'].hide()
		elif self.gleich:
			self.titel = 'Gleich'
		elif self.abends:
			self.titel = '20:15'
		else:
			self.titel = '22:00'
		self.titel = '%s im TV - Heute, %s, %s' % (self.titel, self.weekday, datum)
		self.setTitle(self.titel)
		items, bereich = parseNow(output)
		nowhour = datetime.now().hour
		nowminute = datetime.now().minute
		nowsec = int(nowhour) * 3600 + int(nowminute) * 60
		if self.jetzt or self.gleich or self.abends and nowhour == 20 or self.abends and nowhour == 21 or self.nachts and nowhour == 22:
			self.progress = True
		else:
			self.progress = False
#20:15#########################################################################################
		mh = int(47 * SCALE + 0.5)
		for LOGO, TIME, LINK, title, sparte, genre, RATING, trailer in items:
			sref = self.service_db.lookup(LOGO)
			if sref != "nope":
				res_sref = []
				res_sref.append(LOGO)
				res_sref.append(sref)
				self.sref.append(res_sref)
				res = [LOGO]
				png = getPiconname(LOGO, sref)
				if png:
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
				else:
					res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), font=-2,
							   color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
				percent = None
				if self.progress:
					start = sub(r' - ..:..', '', TIME)
					startparts = start.split(':')
					startsec = int(startparts[0]) * 3600 + int(startparts[1]) * 60
					end = sub(r'..:.. - ', '', TIME)
					endparts = end.split(':')
					endsec = int(endparts[0]) * 3600 + int(endparts[1]) * 60
					length = endsec - startsec if endsec >= startsec else 86400 - startsec + endsec
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
				start = sub(r' - ..:..', '', TIME)
				hour = sub(r':..', '', start)
				if int(nowhour) - int(hour) > 6:
					one_day = timedelta(days=1)
					datum = self.date + one_day
				else:
					datum = self.date
				timer = "%s:::%s:::%s" % (datum, start, sref)
				res_link = []
				res_link.append(LOGO)
				res_link.append(LINK)
				self.tvlink.append(res_link)
				if title:
					x = "%s %s" % (title, genre) if self.showgenre and genre else title
					res_titel = []
					res_titel.append(LOGO)
					res_titel.append(title)
					self.tvtitel.append(res_titel)
					if self.progress or percent:
						ypos = int(12 * SCALE)
						res.append(MultiContentEntryProgress(pos=(int(77 * SCALE), int(32 * SCALE)), size=(int(90 * SCALE), int(6 * SCALE)), percent=percent, borderWidth=1, foreColor=16777215))
					else:
						ypos = int(14 * SCALE)
					res.append(MultiContentEntryText(pos=(int(75 * SCALE), ypos), size=(int(110 * SCALE), int(20 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT, text=TIME))
					res.append(MultiContentEntryText(pos=(int(220 * SCALE), 0), size=(int(830 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
				if timer in self.timer:
					self.rec = True
					png = join(ICONPATH, 'rec.png')
					ypos = int(24 * SCALE) if sparte else int(16 * SCALE)
					if isfile(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1160 * SCALE), ypos), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
				if sparte:
					if self.rec:
						ypos = 4
						ysize = int(20 * SCALE)
						valign = RT_HALIGN_RIGHT
						sparte = sparte.split("\n")[0]
					else:
						ypos = 0
						ysize = mh
						valign = RT_HALIGN_RIGHT | RT_VALIGN_CENTER
					res.append(MultiContentEntryText(pos=(int(1080 * SCALE), ypos), size=(int(120 * SCALE), ysize), font=-2, color=10857646, color_sel=16777215, flags=valign, text=sparte))
				self.rec = False
				if RATING != 'rating small':
					RATING = RATING.replace(' ', '-')
					png = '%s%s.png' % (ICONPATH, RATING)
					if isfile(png):  # DAUMEN
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1220 * SCALE), int(10 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
				if trailer:
					png = join(ICONPATH, 'trailer.png')
					if isfile(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(180 * SCALE), int(8 * SCALE)), size=(int(30 * SCALE), int(30 * SCALE)), png=loadPNG(png)))
				self.tventries.append(res)
		self.sref = sorted(self.sref, key=lambda x: self.order[x[0]])
		self.tvlink = sorted(self.tvlink, key=lambda x: self.order[x[0]])
		self.tvtitel = sorted(self.tvtitel, key=lambda x: self.order[x[0]])
		self.tventries = sorted(self.tventries, key=lambda x: self.order[x[0]])
		self['menu'].l.setItemHeight(mh)
		self['menu'].l.setList(self.tventries)
		startpos = output.find('<ul class="pagination__items">')
		endpos = output.find(NEXTPage1)
		bereich = output[startpos:endpos]
		nextpage = search(NEXTPage2, bereich)
		nextpage = nextpage.group(1) if nextpage else ""
		pagenumber = search(r'\d+', nextpage)
		pagenumber = int(pagenumber.group()) if pagenumber is not None else 888
		if self.jetzt:
			if pagenumber < min(int(config.plugins.tvspielfilm.maxlist.value) + 1, 10):
				callInThread(self.threadGetPage, nextpage, self.makeTVJetztView, self.downloadError)
			else:
				self.showready()
		else:
			if pagenumber < int(config.plugins.tvspielfilm.maxlist.value) + 1:
				callInThread(self.threadGetPage, nextpage, self.makeTVJetztView, self.downloadError)
			else:
				self.showready()

	def showready(self):
		self['menu'].moveToIndex(self.index)
		self.ready = True
		self['TEXTkey'].show()
		self['INFOkey'].show()
		self['waiting'].stopBlinking()
		self['waiting'].hide()
		self['ready'].show()
		self.readyTimer = eTimer()
		self.readyTimer.callback.append(self.hideready)
		self.readyTimer.start(1500, False)

	def hideready(self):
		self.readyTimer.stop()
		self['ready'].hide()

	def makePostviewPage(self):
		self['menu'].hide()
		try:
			self._makePostviewPage()
		except:
			printStackTrace()

	def ok(self):
		self['TEXTkey'].hide()
		self['TEXTtext'].hide()
		self._ok()

	def selectPage(self, action):
		if self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.postlink = self.tvlink[c][1]
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.postlink = self.searchlink[c]
		if action == 'ok' and self.ready:
			if search(r'www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				callInThread(self.threadDownloadPage, self.postlink, self.localhtml2, self.makePostviewPage, self.downloadError)

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
						s1 = sub(r':..', '', start)
						datum = '%sFIN' % self.postdate
						datum = sub(r'..FIN', '', str(date))
						datum = "%s%s" % (datum, self.day)
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(r':..:..', '', start)
						if int(s2) > int(s1):
							start = '%s %s' % (self.date, start)
						else:
							start = "%s %s" % (datum, start)
						start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
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
								self.EPGtext += '\n\n%s' % short
							if ext:
								self.EPGtext += '\n\n%s' % ext
							if dur:
								self.EPGtext += '\n\n%s' % dur
					except:
						self.EPGText = getEPGText()

				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n%s' % fill
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
			self['waiting'].startBlinking()
			self['waiting'].show()
			if self.jetzt:
				self.jetzt = False
				self.gleich = True
				link = "%s/tv-programm/sendungen/?page=1&order=time&time=shortly" % self.baseurl
			else:
				self.jetzt = True
				self.gleich = False
				self.abends = False
				self.nachts = False
				link = "%s/tv-programm/sendungen/jetzt.html" % self.baseurl
			callInThread(self.threadGetPage, link, self.makeTVJetztView, self.downloadError)

	def red(self):
		if self.current == 'postview' and self.postviewready:
			if not self.search:
				c = self['menu'].getSelectedIndex()
				self.oldindex = c
				sref = self.sref[c][1]
				self.redTimer(False, sref)
			else:
				c = self['searchmenu'].getSelectedIndex()
				self.oldsearchindex = c
				sref = self.searchref[c]
				self.redTimer(False, sref)
		elif self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.oldindex = c
			self.postlink = self.tvlink[c][1]
			if search(r'www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.index = self.oldindex
				callInThread(self.threadGetPage, self.postlink, self.makePostTimer, self.threadDownloadError)
			else:
				self.redTimer(False, self.postlink)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			self.postlink = self.searchlink[c]
			if search(r'www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				callInThread(self.threadGetPage, self.postlink, self.makePostTimer, self.threadDownloadError)

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
				titel = self.tvtitel[c][1].split(', ')
				if len(titel) == 1:
					titel = titel[0].split(' ')
					titel = "%s %s" % (titel[0], titel[1]) if titel[0].find(':') > 0 else titel[0]
				elif len(titel) == 2:
					titel = titel[0].rsplit(' ', 1)[0]
				else:
					titel = titel[0]
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
			except IndexError:
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

	def searchReturn(self, search):
		if search and search != '':
			self['menu'].hide()
			self['TEXTtext'].hide()
			self['TEXTkey'].hide()
			self.searchstring = search
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			search = quote(search).replace('%20', '+')
			searchlink = "%s/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=%s" % (self.baseurl, search)
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		if self.current == 'menu' and self.ready:
			try:
				c = self['menu'].getSelectedIndex()
				channel = self.sref[c][0]
				link = "%s/tv-programm/sendungen/&page=0,%s.html" % (self.baseurl, channel)
				self.session.open(TVSProgrammView, link, True, False)
			except IndexError:
				pass
		else:
			self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(TVSsearchYouTube, self.name, self.movie)
		elif self.current == 'menu' and not self.search and self.ready:
			c = self['menu'].getSelectedIndex()
			titel = self.tvtitel[c][1]
			self.session.open(TVSsearchYouTube, titel, self.movie)

	def gotoEnd(self):
		if self.current != 'postview' and self.ready and not self.search:
			end = len(self.tventries) - 1
			self['menu'].moveToIndex(end)
		elif self.current != 'postview' and self.ready and self.search:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)

	def downloadError(self, error):
		self['CHANNELkey'].hide()
		self['CHANNELtext'].hide()
		self['BOUQUETkey'].hide()
		self['BOUQUETtext'].hide()
		self['INFOkey'].show()
		self['MENUkey'].hide()
		self['TEXTkey'].show()
		self['OKtext'].hide()
		self['TEXTtext'].setText('Sender')
		self['TEXTtext'].show()
		self['INFOtext'].setText('Jetzt/Gleich im TV')
		self['INFOtext'].show()
		self.ready = True
		self.showDownloadError(error)

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['waiting'].startBlinking()
		self['waiting'].show()
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.sref = []
		if self.jetzt:
			link = "%s/tv-programm/sendungen/jetzt.html" % self.baseurl
		elif self.gleich:
			link = "%s/tv-programm/sendungen/?page=1&order=time&time=shortly" % self.baseurl
		elif self.abends:
			link = "%s/tv-programm/sendungen/abends.html" % self.baseurl
		else:
			link = "%s/tv-programm/sendungen/fernsehprogramm-nachts.html" % self.baseurl
		callInThread(self.downloadFull, link, self.makeTVJetztView)

	def showProgrammPage(self):
		self['CHANNELkey'].hide()
		self['CHANNELtext'].hide()
		self['BOUQUETkey'].hide()
		self['BOUQUETtext'].hide()
		self['INFOkey'].show()
		self['TEXTkey'].show()
		self['TEXTtext'].setText('Sender')
		self['TEXTtext'].show()
		self['INFOtext'].setText('Jetzt/Gleich im TV')
		self['INFOtext'].show()
		self['label2'].setText('Timer')
		self['label3'].show()
		self['label3'].setText('Suche')
		self['label3'].show()
		self['label4'].setText('Zappen')
		self['label4'].show()
		self.setBlueButton('Aus-/Einblenden')
		self.hideInfotext()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self.hideTVinfo()
		self.current = 'menu'
		self['menu'].show()

	def setBlueButton(self, text):
		if ALPHA:
			self['bluebutton'].show()
			self['label5'].setText(text)
			self['label5'].show()
		else:
			self['bluebutton'].hide()
			self['label5'].hide()

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

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.current == 'menu' and not self.search:
			if isfile(self.picfile):
				remove(self.picfile)
			if isfile(self.localhtml):
				remove(self.localhtml)
			if isfile(self.localhtml2):
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
			self.showProgrammPage()
			self.setTitle(self.titel)
		elif self.current == 'postview' and not self.search:
			self.hideRatingInfos()
			self.postviewready = False
			self.setTitle(self.titel)
			self.showProgrammPage()
			self['button_OK'].hide()
			self['label_OK'].hide()
			self['button_TEXT'].hide()
			self['label_TEXT'].hide()
			self['button_INFO'].hide()
			self['label_INFO'].hide()
			self['button_7_8_9'].hide()
		elif self.current == 'postview' and self.search:
			self.hideRatingInfos()
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


class TVSProgrammView(TVSGenreJetztProgrammView):
	def __init__(self, session, link, eventview, tagestipp):
		TVSGenreJetztProgrammView.__init__(self, session, link)
		self.link = link
		self.eventview = eventview
		self.tagestipp = tagestipp
		self.service_db = serviceDB(SERVICEFILE)
		self.localhtml = '/tmp/tvspielfilm.html'
		channel = []
		if not self.tagestipp:
			channel = findall(r',(.*?).html', link)
			service = channel[0].lower()
			self.sref = self.service_db.lookup(service)
			if self.sref == 'nope':
				self.zapflag = False
				self.picon = False
			else:
				self.zapflag = True
		self.primetime = False
		self.finishedTimerMode = 1
		if not self.eventview:
			self._commonInit()
		else:
			self._commonInit('Suche', ' Refresh')
		self.hideTVinfo()
		self.hideInfotext()
		self.hideRatingInfos()
		self.showMenubar()
		self['ready'].hide()
		self['seitennr'].hide()
		self['INFOkey'].hide()
		self['INFOtext'].hide()
		self['TEXTkey'].hide()
		self['TEXTtext'].hide()
		self['button_OK'].hide()
		self['label_OK'].hide()
		self['button_TEXT'].hide()
		self['label_TEXT'].hide()
		self['button_INFO'].hide()
		self['label_INFO'].hide()
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
		if isfile(TIMERFILE):
			self.timer = open(TIMERFILE).read().split('\n')
		else:
			self.timer = ''
		self.date = date.today()
		one_day = timedelta(days=1)
		self.nextdate = "%s%s" % (self.date, one_day)
		self.weekday = makeWeekDay(self.date.weekday())
		if self.eventview:
			self.movie_stop = config.usage.on_movie_stop.value
			self.movie_eof = config.usage.on_movie_eof.value
			config.usage.on_movie_stop.value = 'quit'
			config.usage.on_movie_eof.value = 'quit'
			from Components.ServiceEventTracker import ServiceEventTracker
			from enigma import iPlayableService
			self.event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evUpdatedEventInfo: self.zapRefresh})
			self.channel_db = channelDB(SERVICEFILE)
		elif not self.tagestipp:
			self.link = "%s%s&tips=0&time=day&channel=%s" % (sub(r'/sendungen/.*?html', '/sendungen/?page=1&order=time&date=', self.link), self.date, channel[0])
		if not self.tagestipp:
			callInThread(self.threadGetPage, self.link, self.makeTVSProgrammView, self.downloadError)
		else:
			self.current = 'postview'
			callInThread(self.threadDownloadPage, self.link, self.localhtml2, self.makePostviewPage, self.downloadError)

	def makeTVSProgrammView(self, output):
		output = ensure_str(output)
		self['CHANNELkey'].show()
		self['CHANNELtext'].setText('Tag +/-')
		self['CHANNELtext'].show()
		self['BOUQUETkey'].show()
		self['BOUQUETtext'].setText('Woche +/-')
		self['BOUQUETtext'].show()
		datum = self.date.strftime('%d.%m.%Y')
		titel = search(r'<title>(.*?)von', output[:300])
		self.titel = "%s%s, %s" % (titel.group(1), self.weekday, datum) if titel is not None else ""
		self.setTitle(self.titel)
		items, bereich = parseNow(output)
		today = date.today()
		one_day = timedelta(days=1)
		yesterday = today - one_day
		nowhour = datetime.now().hour
		if self.date == today and nowhour > 4 or self.date == yesterday and nowhour < 5:
			self.progress = True
			nowminute = datetime.now().minute
			nowsec = int(nowhour) * 3600 + int(nowminute) * 60
		else:
			nowminute = ''
			nowsec = 0
			self.progress = False
			self.percent = False
		mh = int(47 * SCALE + 0.5)
		for LOGO, TIME, LINK, TITEL, SPARTE, GENRE, RATING, TRAILER in items:
			res = [LOGO]
			sref = self.service_db.lookup(LOGO)
			png = getPiconname(LOGO, sref)
			if png:
				res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
			else:
				res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), font=-2,
						   color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
			percent = 0
			if self.progress:
				start = sub(r' - ..:..', '', TIME)
				startparts = start.split(':')
				startsec = int(startparts[0]) * 3600 + int(startparts[1]) * 60
				end = sub(r'..:.. - ', '', TIME)
				endparts = end.split(':')
				endsec = int(endparts[0]) * 3600 + int(endparts[1]) * 60
				if endsec >= startsec:
					length = endsec - startsec
				else:
					length = 86400 - startsec + endsec
				if nowsec < startsec and endsec > startsec:
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
						self.percent = False
				elif nowsec > endsec:
					percent = 100
					self.percent = False
				else:
					passed = nowsec - startsec
					percent = passed * 100 / length
					self.percent = True
			if search(r'20:15 -', TIME) or self.percent:
				self.primetime = True
			else:
				self.primetime = False
			start = sub(r' - ..:..', '', TIME)
			hour = sub(r':..', '', start)
			if int(hour) < 5 and len(self.tventries) > 6 or int(hour) < 5 and self.eventview:
				one_day = timedelta(days=1)
				datum = "%s%s" % (self.date, one_day)
			else:
				datum = self.date
			timer = "%s:::%s:::%s" % (datum, start, sref)
			self.tvlink.append(LINK)
			t = TITEL
			if self.showgenre and GENRE:
				x = "%s %s" % (t, GENRE)
			else:
				x = t
			self.tvtitel.append(t)
			if self.progress and self.percent:
				ypos = int(12 * SCALE)
				res.append(MultiContentEntryProgress(pos=(int(77 * SCALE), int(32 * SCALE)), size=(int(95 * SCALE), int(6 * SCALE)), percent=percent, borderWidth=1, foreColor=16777215))
			else:
				ypos = int(14 * SCALE)
			res.append(MultiContentEntryText(pos=(int(75 * SCALE), ypos), size=(int(110 * SCALE), int(20 * SCALE)),
					   font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=TIME))
			res.append(MultiContentEntryText(pos=(int(220 * SCALE), 0), size=(int(830 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
			if TRAILER:
				png = join(ICONPATH, 'trailer.png')
				if isfile(png):
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(180 * SCALE), int(8 * SCALE)), size=(int(30 * SCALE), int(30 * SCALE)), png=loadPNG(png)))
			if timer in self.timer:
				self.rec = True
				png = join(ICONPATH, 'rec.png')
				ypos = int(24 * SCALE) if SPARTE else int(16 * SCALE)
				if isfile(png):
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1160 * SCALE), ypos), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
			if SPARTE:
				stext = SPARTE.replace('<br/>', '')
				ypos = int(4 * SCALE) if self.rec else 0
				valign = RT_HALIGN_RIGHT if self.rec else RT_HALIGN_RIGHT | RT_VALIGN_CENTER
				res.append(MultiContentEntryText(pos=(int(1080 * SCALE), ypos), size=(int(120 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=valign, text=stext))
			self.rec = False
			if RATING != 'rating small':
				RATING = RATING.replace(' ', '-')
				png = '%s%s.png' % (ICONPATH, RATING)
				if isfile(png):  # DAUMEN
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1220 * SCALE), int(10 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
			self.tventries.append(res)
		self['menu'].l.setItemHeight(mh)
		self['menu'].l.setList(self.tventries)
		self['menu'].moveToIndex(self.oldindex)
		startpos = bereich.find('<li class="pagination__item pagination__item--current">')
		endpos = bereich.find('<div class="link-row">')
		bereich = bereich[startpos:endpos]
		nextpage = search(NEXTPage2, bereich)
		if nextpage is not None:
			nextpage = nextpage.group(1)
			if nextpage.find("?page=") != -1:
				callInThread(self.threadGetPage, nextpage, self.makeTVSProgrammView, self.downloadError)
			else:
				self.ready = True
		else:
			self.ready = True
		if self.ready:
			if not self.eventview:
				self['1_zapup'].hide()
				self['2_zapdown'].hide()
			else:
				self['1_zapup'].show()
				self['2_zapdown'].show()
			self.showready()
		if self.eventview and config.plugins.tvspielfilm.eventview.value == 'info':
			self.postlink = self.tvlink[1]
			if search(r'www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				callInThread(self.threadDownloadPage, self.postlink, self.localhtml2, self.makePostviewPage, self.downloadError)
			else:
				self.ready = True

	def makePostviewPage(self):
		self['menu'].hide()
		try:
			self._makePostviewPage()
		except:
			printStackTrace()

	def showready(self):
		self['waiting'].stopBlinking()
		self['waiting'].hide()
		self['ready'].show()
		self.readyTimer = eTimer()
		self.readyTimer.callback.append(self.hideready)
		self.readyTimer.start(1500, False)

	def hideready(self):
		self.readyTimer.stop()
		self['ready'].hide()

	def ok(self):
		self['TEXTkey'].hide()
		self['TEXTtext'].hide()
		self._ok()

	def selectPage(self, action):
		if self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.postlink = self.tvlink[c]
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.postlink = self.searchlink[c]
		if action == 'ok' and self.ready:
			if search(r'www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				callInThread(self.threadDownloadPage, self.postlink, self.localhtml2, self.makePostviewPage, self.downloadError)

	def getEPG(self):
		if self.current == 'postview' and self.postviewready:
			if not self.showEPG:
				self.showEPG = True
				if self.zapflag and not self.search:
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
						s1 = sub(r':..', '', start)
						datum = "%s%s" % (self.postdate, 'FIN')
						datum = sub(r'..FIN', '', datum)
						datum = "%s%s" % (datum, self.day)
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(r':..:..', '', start)
						start = "%s %s" % (self.date, start) if int(s2) > int(s1) else "%s %s" % (datum, start)
						start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
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
								self.EPGtext += '\n\n%s' % short
							if ext:
								self.EPGtext += '\n\n%s' % ext
							if dur:
								self.EPGtext += '\n\n%s' % dur
					except:
						self.EPGText = getEPGText()
				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n%s' % fill
				self['textpage'].setText(self.EPGtext)
				self['textpage'].show()
			else:
				self.showEPG = False
				self['textpage'].setText(self.POSTtext)
				self['textpage'].show()

	def red(self):
		if self.current == 'postview' and self.postviewready:
			if self.zapflag and not self.search:
				c = self['menu'].getSelectedIndex()
				self.oldindex = c
				sref = self.sref
				self.redTimer(False, sref)
			elif self.search:
				c = self['searchmenu'].getSelectedIndex()
				self.oldsearchindex = c
				sref = self.searchref[c]
				self.redTimer(False, sref)
			else:
				self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
		elif self.current == 'menu' and self.ready and self.zapflag:
			c = self['menu'].getSelectedIndex()
			self.oldindex = c
			self.postlink = self.tvlink[c]
			if search(r'www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				callInThread(self.threadGetPage, self.postlink, self.makePostTimer, self.downloadError)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			self.postlink = self.searchlink[c]
			if search(r'www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				callInThread(self.threadGetPage, self.postlink, self.makePostTimer, self.downloadError)
		else:
			self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)

	def green(self):
		if self.current == 'menu' and self.zapflag and not self.eventview and not self.search:
			c = self['menu'].getSelectedIndex()
			try:
				sref = self.sref
				if sref != '':
					self.session.nav.playService(eServiceReference(sref))
			except IndexError:
				pass
		elif self.current == 'menu' and self.eventview and not self.search:
			sref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference())
			sref = '%sFIN' % sref
			sref = sub(r':0:0:0:.*?FIN', ':0:0:0:', sref)
			self.sref = sref
			channel = self.channel_db.lookup(sref)
			if channel == 'nope':
				self.session.open(MessageBox, 'Service nicht gefunden:\nKein Eintrag für aktuelle Servicereferenz\n%s' % sref, MessageBox.TYPE_INFO, close_on_any_key=True)
			else:
				self.link = '%s/tv-programm/sendungen/&page=0,%s.html' % (self.baseurl, channel)
				self.refresh()

	def yellow(self):
		if self.current == 'postview':
			self.youTube()
		elif self.current == 'menu' and not self.search and self.ready:
			try:
				c = self['menu'].getSelectedIndex()
				self.oldindex = c
				titel = self.tvtitel[c].split(', ')
				if len(titel) == 1:
					titel = titel[0].split(' ')
					titel = '%s %s' % (titel[0], titel[1]) if titel[0].find(':') > 0 else titel[0]
				elif len(titel) == 2:
					titel = titel[0].rsplit(' ', 1)[0]
				else:
					titel = titel[0]
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text=titel)
			except IndexError:
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='TV Spielfilm Suche:', text='')

	def searchReturn(self, search):
		if search and search != '':
			self.searchstring = search
			self['menu'].hide()
			self['label3'].hide()
			self['label4'].hide()
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			search = quote(search).replace('%20', '+')
			searchlink = "%s/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=%s" % (self.baseurl, search)
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(TVSsearchYouTube, self.name, self.movie)
		elif self.current == 'menu' and not self.search and self.ready:
			c = self['menu'].getSelectedIndex()
			titel = self.tvtitel[c]
			self.session.open(TVSsearchYouTube, titel, self.movie)

	def nextDay(self):
		self.changeday(1)

	def prevDay(self):
		self.changeday(-1)

	def nextWeek(self):
		self.changeday(7)

	def prevWeek(self):
		self.changeday(-7)

	def changeday(self, deltadays):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			timespan = timedelta(days=deltadays)
			if search(r'time&date', self.link):
				date1 = findall(r'time&date=(.*?)-..-..&tips', self.link)
				date2 = findall(r'time&date=....-(.*?)-..&tips', self.link)
				date3 = findall(r'time&date=....-..-(.*?)&tips', self.link)
				try:
					today = date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = date.today()
			else:
				self.link = sub(r'.html', '', self.link)
				self.link = sub(r'&page=0,', '?page=0&order=time&date=channel=', self.link)
				today = date.today()
			self.date = today + timespan
			self.weekday = makeWeekDay(self.date.weekday())
			self.link = '%sFIN' % self.link
			channel = findall(r'channel=(.*?)FIN', self.link)
			nextday = sub(r'[?]page=.&order=time&date=(.*?FIN)', '?page=1&order=time&date=', self.link)
			nextday = '%s%s&tips=0&time=day&channel=%s' % (nextday, self.date, channel[0])
			self.nextdate = self.date + timespan
			self.link = nextday
			self.oldindex = 0
			self.refresh()
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def gotoEnd(self):
		if self.current != 'postview' and self.ready and not self.search:
			end = len(self.tventries) - 1
			self['menu'].moveToIndex(end)
		elif self.current != 'postview' and self.ready and self.search:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)

	def downloadError(self, output):
		self['CHANNELkey'].show()
		self['BOUQUETkey'].show()
		self['INFOkey'].hide()
		if not self.eventview:
			self['1_zapup'].hide()
			self['2_zapdown'].hide()
		else:
			self['1_zapup'].show()
			self['2_zapdown'].show()
		self.ready = True
		TVSlog("Downloaderror in module 'TVSProgrammView:downloadError':", output)
		self.showDownloadError(output)

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['waiting'].startBlinking()
		self['waiting'].show()
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		callInThread(self.threadGetPage, self.link, self.makeTVSProgrammView, self.downloadError)

	def showProgrammPage(self):
		self['CHANNELkey'].show()
		self['CHANNELtext'].show()
		self['BOUQUETkey'].show()
		self['BOUQUETtext'].show()
		self['INFOkey'].hide()
		self['INFOtext'].hide()
		self['TEXTkey'].hide()
		self['TEXTtext'].hide()
		if not self.eventview:
			self['1_zapup'].hide()
			self['2_zapdown'].hide()
			self['label2'].setText('Timer')
			self['label2'].show()
			self['label3'].setText('Suche')
			self['label3'].show()
			self['label4'].setText('Zappen')
			self['label4'].show()
		else:
			self['1_zapup'].show()
			self['2_zapdown'].show()
			self['label2'].setText('Timer')
			self['label2'].show()
			self['label3'].setText('Suche')
			self['label3'].show()
			self['label4'].setText('Refresh')
			self['label4'].show()
		self.hideInfotext()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self.hideTVinfo()
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
			sref = '%sFIN' % sref
			sref = sub(r':0:0:0:.*?FIN', ':0:0:0:', sref)
			self.sref = sref
			channel = self.channel_db.lookup(sref)
			if channel == "nope":
				self.session.open(MessageBox, 'Service nicht gefunden:\nKein Eintrag für aktuelle Servicereferenz\n%s' % sref, MessageBox.TYPE_INFO, close_on_any_key=True)
			else:
				self.link = '%s/tv-programm/sendungen/&page=0,%s.html' % (self.baseurl, channel)
				self.refresh()

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.current == 'menu':
			if isfile(self.picfile):
				remove(self.picfile)
			if isfile(self.localhtml):
				remove(self.localhtml)
			if isfile(self.localhtml2):
				remove(self.localhtml2)
			if self.eventview:
				config.usage.on_movie_stop.value = self.movie_stop
				config.usage.on_movie_eof.value = self.movie_eof
			self.hideRatingInfos()
			self.close()
		elif self.current == 'searchmenu':
			self.search = False
			self.oldsearchindex = 1
			self.hideRatingInfos()
			self['searchmenu'].hide()
			self['searchtext'].hide()
			self.showProgrammPage()
			self.setTitle(self.titel)
		elif self.current == 'postview' and not self.search:
			if self.tagestipp:
				self.close()
			else:
				self.postviewready = False
				self.hideRatingInfos()
				self.setTitle(self.titel)
				self.showProgrammPage()
			self['button_OK'].hide()
			self['button_TEXT'].hide()
			self['button_7_8_9'].hide()
		elif self.current == 'postview' and self.search:
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


class TVSNews(TVSBaseScreen):
	def __init__(self, session, link):
		global HIDEFLAG
		skin = readSkin("TVSNews")
		TVSBaseScreen.__init__(self, session, skin)
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
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['ready'] = Label('OK')
		self['picture'] = Pixmap()
		self['picpost'] = Pixmap()
		self['playlogo'] = Pixmap()
		self['statuslabel'] = Label()
		self['picturetext'] = Label()
		self['seitennr'] = Label()
		self['textpage'] = ScrollLabel()
		self['menu'] = ItemList([])
		self['OKkey'] = Pixmap()
		self['OKtext'] = Label()
		self['Line_down'] = Label()
		self['label5'] = Label()
		self['bluebutton'] = Label()
		self.setBlueButton('Aus-/Einblenden')
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
		callInThread(self.threadGetPage, link, self.makeTVSNews, self.downloadError)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['ready'].hide()
		self['playlogo'].hide()
		self['statuslabel'].hide()
		self['seitennr'].hide()

	def makeTVSNews(self, output):
		output = ensure_str(output)
		titel = search(r'<title>(.*?)</title>', output[:300])
		self.titel = titel.group(1).replace('&amp;', '&') if titel is not None else ""
		self.setTitle(self.titel)
		self['seitennr'].hide()
		self['Line_down'].show()
		startpos = output.find('<div class="content-teaser teaser-m teaser-m-standard">')
		startpos2 = output.find('id="c-sp-opener"><span>Spielfilm</span></a>')  # alternative Startpos wegen TV-Tipps
		if startpos2 > startpos:
			startpos = startpos2
		endpos = output.find('<h2 class="headline headline--section">')
		if endpos == -1 or endpos < startpos:  # andere Endekennung bei Genres
			endpos = output.find('<div class="pagination pagination--numbers"')
		if endpos == -1 or endpos < startpos:  # andere Endekennung bei Streaming
			endpos = output.find('<div class="widget-box tips-box media-top3">')
		if endpos == -1 or endpos < startpos:  # andere Endekennung bei TV-Tipps
			endpos = output.find('class="desktop_rectangle_any "')
		bereich = output[startpos:endpos]
		bereich = unescape(bereich).replace("&shy;", "-")
		sektionen = bereich.split('</a>')
		sektionen.pop(-1)
		for sektion in sektionen:
			link = search(r'<a href="(.*?)" target="_self"', sektion)
			if link is None:
				link = ''
			else:
				link = link.group(1)
			picurl = search(r'<img src="(.*?)" ', sektion)
			if picurl is None:
				picurl = ''
			else:
				picurl = picurl.group(1)
			trailer = search(r'"videoIntegration": "(.*?)"', sektion)
			if trailer is None:
				trailer = '0'
			else:
				trailer = trailer.group(1)
			name = search(r'<span class="headline">(.*?)</span>', sektion)
			if name is None:  # andere Umklammerung bei Genres
				name = search(r'<p class="title">(.*?)</p>', sektion)
			if name is None:
				name = ''
			else:
				name = name.group(1)
			subline = search(r'<span\s*class="subline icon-thumb\s*icon-thumb-1">(.*?)</span>', sektion)
			fullname = name if subline is None else "%s | %s" % (name, subline.group(1))
			res = ['']
			res.append(MultiContentEntryText(pos=(int(10 * SCALE), 0), size=(int(870 * SCALE), int(30 * SCALE)), font=1, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=fullname))
			if trailer is not None and trailer != "0":
				png = join(ICONPATH, 'trailer.png')
				if isfile(png):
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(790 * SCALE), 0), size=(int(30 * SCALE), int(30 * SCALE)), png=loadPNG(png)))
			if len(picurl) > 0:
				self.picurllist.append(picurl)
				self.pictextlist.append(fullname)
				self.menulist.append(res)
				self.menulink.append(link)
		self['menu'].l.setItemHeight(int(30 * SCALE))
		self['menu'].l.setList(self.menulist)
		callInThread(self.threadGetPage, self.picurllist[0], self.getPic, self.downloadError)
		self['picturetext'].setText(self.pictextlist[0])
		self.ready = True
		self.showTVSNews()

	def makePostviewPageNews(self):
		output = ensure_str(open(self.localhtml2, 'r').read())
		self['picture'].hide()
		self['picturetext'].hide()
		self['statuslabel'].hide()
		self['menu'].hide()
		self.setTVTitle(output)
		output = sub(r'</dl>.\n\\s+</div>.\n\\s+</section>', '</cast>', output)
		startpos = output.find('<div class="content-area">')
		endpos = output.find('<div class="content-teaser teaser-m teaser-m-standard">')
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
		picurl = search(r'<img src="(.*?).jpg"', bereich)
		if picurl:
			callInThread(self.downloadPicPost, "%s.jpg" % picurl.group(1), False)
		else:
			picurl = search(r'<meta property="og:image" content="(.*?)"', bereich)
			if picurl:
				callInThread(self.downloadPicPost, picurl.group(1), False)
				self.downloadPicPost(picurl.group(1), False)
			else:
				if self.picurl:
					callInThread(self.downloadPicPost, self.picurl, False)
				else:
					picurl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
					callInThread(self.downloadPicPost, picurl, False)
		if search(r'<div class="film-gallery">', output):
			self.mehrbilder = True
			if self.trailer:
				self['OKtext'].setText('Zum Video')
			else:
				self['OKtext'].setText('Fotostrecke')
		else:
			self.mehrbilder = False
			if self.trailer:
				self['OKtext'].setText('Zum Video')
			else:
				self['OKtext'].setText('Vollbild')
		self['OKkey'].show()
		self['OKtext'].show()
		self['seitennr'].hide()
		self.setBlueButton('Aus-/Einblenden')
		head = search(r'<h1 class="film-title">(.*?)</h1>', bereich)
		if not head:
			head = search(r'<p class="prelude">(.*?)</p>', bereich)
		if not head:
			head = search(r'<h1 class="headline headline--article broadcast">(.*?)</h1>', bereich)
		if not head:
			head = search(r'<h1 class="headline headline--article">(.*?)</h1>', bereich)
		short = search(r'<span class="title-caption">(.*?)</span>', bereich)
		if not short:
			short = search(r'<span class="title-caption">(.*?)</span>', bereich)
		intro = search(r'<p class="intro">"(.*?)</p>', bereich)
		if not intro:
			intro = search(r'<span class="text-row">(.*?)</span>', bereich)
		if head or short or intro:
			text = ''
			if head:
				text += "%s\n\n" % head.group(1)
			if short:
				text += "%s\n\n" % short.group(1)
			if intro:
				text += "%s\n" % intro.group(1)
		else:
			text = '{keine Beschreibung gefunden}\n'
		fill = self.getFill('TV Spielfilm Online')
		self.POSTtext = "%s\n%s" % (text.strip(), fill)
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
					self.session.open(TVSPicShow, self.postlink, 1)
				else:
					self.session.openWithCallback(self.showPicPost, TVSFullScreen)

	def selectPage(self, action):
		c = self['menu'].getSelectedIndex()
		self.postlink = self.menulink[c]
		self.picurl = self.picurllist[c]
		if action == 'ok':
			if search(r'www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				callInThread(self.threadDownloadPage, self.postlink, self.localhtml2, self.makePostviewPageNews, self.downloadError)
			else:
				self['statuslabel'].setText('Kein Artikel verfügbar')
				self['statuslabel'].show()

	def getPic(self, output):
		with open(self.picfile, 'wb') as f:
			f.write(output)
		showPic(self['picture'], self.picfile)

	def downloadError(self, output):
		self['statuslabel'].setText('Download Fehler')
		self['statuslabel'].show()
		TVSlog("Downloaderror in module 'TVSNews:downloadError':", output)
		self.showDownloadError(output)

	def showTVSNews(self):
		self.current = 'menu'
		self.showready()
		self['menu'].show()
		self['OKkey'].show()
		self['OKtext'].setText('Zum Artikel')
		self['OKtext'].show()
		self['picture'].show()
		self['picturetext'].show()
		self['textpage'].hide()
		self['picpost'].hide()
		self['playlogo'].hide()
		self['statuslabel'].hide()
		self.setBlueButton('Aus-/Einblenden')

	def showready(self):
		self['waiting'].stopBlinking()
		self['waiting'].hide()
		self['ready'].show()
		self.readyTimer = eTimer()
		self.readyTimer.callback.append(self.hideready)
		self.readyTimer.start(1500, False)

	def hideready(self):
		self.readyTimer.stop()
		self['ready'].hide()

	def down(self):
		if self.current == 'menu':
			self['menu'].down()
			c = self['menu'].getSelectedIndex()
			picurl = self.picurllist[c]
			callInThread(self.threadGetPage, picurl, self.getPic, self.downloadError)
			pictext = self.pictextlist[c]
			self['picturetext'].setText(pictext)
			self['statuslabel'].hide()
		else:
			self['textpage'].pageDown()

	def up(self):
		if self.current == 'menu':
			self['menu'].up()
			c = self['menu'].getSelectedIndex()
			picurl = self.picurllist[c]
			callInThread(self.threadGetPage, picurl, self.getPic, self.downloadError)
			pictext = self.pictextlist[c]
			self['picturetext'].setText(pictext)
			self['statuslabel'].hide()
		else:
			self['textpage'].pageUp()

	def rightDown(self):
		if self.current == 'menu':
			self['menu'].pageDown()
			c = self['menu'].getSelectedIndex()
			picurl = self.picurllist[c]
			callInThread(self.threadGetPage, picurl, self.getPic, self.downloadError)
			pictext = self.pictextlist[c]
			self['picturetext'].setText(pictext)
			self['statuslabel'].hide()
		else:
			self['textpage'].pageDown()

	def leftUp(self):
		if self.current == 'menu':
			self['menu'].pageUp()
			c = self['menu'].getSelectedIndex()
			picurl = self.picurllist[c]
			callInThread(self.threadGetPage, picurl, self.getPic, self.downloadError)
			pictext = self.pictextlist[c]
			self['picturetext'].setText(pictext)
			self['statuslabel'].hide()
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
		else:
			self.postviewready = False
			self.setTitle(self.titel)
			self.showTVSNews()


class TVSPicShow(TVSBaseScreen):
	def __init__(self, session, link, picmode=0):
		global HIDEFLAG
		self.link = link
		skin = readSkin("TVSPicShow")
		TVSBaseScreen.__init__(self, session, skin)
		self.picmode = picmode
		HIDEFLAG = True
		self.pixlist = []
		self.topline = []
		self.titel = ''
		self.picmax = 1
		self.count = 0
		self['release'] = Label(RELEASE)
		self['picture'] = Pixmap()
		self['picindex'] = Label()
		self['pictext'] = ScrollLabel()
		self['textpage'] = ScrollLabel()
		self['seitennr'] = Label()
		self['OKkey'] = Pixmap()
		self['OKtext'] = Label()
		self['Line_down'] = Label()
		self['label5'] = Label()
		self['bluebutton'] = Label()
		self.setBlueButton('Aus-/Einblenden')
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
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self['OKtext'].setText('Vollbild')
		self['OKtext'].show()
		self['Line_down'].show()
		self['seitennr'].hide()
		if self.picmode == 1:
			callInThread(self.threadGetPage, self.link, self.getNewsPicPage, self.downloadError)
		else:
			callInThread(self.threadGetPage, self.link, self.getPicPage, self.downloadError)

	def getPicPage(self, output):
		output = unescape(ensure_str(output)).replace("&shy;", "-")
		self.setTVTitle(output)
		startpos = output.find('<div class="film-gallery">')
		endpos = output.find('<div class="swiper-slide more-galleries">')
		bereich = output[startpos:endpos]
		self.pixlist = findall(r'<source srcset="(.*?)" type="image/jpeg">', bereich)
		callInThread(self.threadGetPage, self.pixlist[0], self.getPic, self.downloadError)
		self.topline = findall(r'data-caption="<div class="firstParagraph">(.*?)</div>', bereich)
		self.description = findall(r' alt="(.*?)" width=', bereich, flags=S)
		self.picmax = len(self.pixlist) if self.pixlist else 1
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))
		self['pictext'].setText(self.description[0])

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
		bereich = cleanHTML(bereich)
		bereich = sub(r'<br />\r\n<br />\r\n', ' \x95 ', bereich)
		bereich = sub(r'<br />\r\n<br />', ' \x95 ', bereich)
		bereich = sub(r'<br />', '', bereich)
		bereich = sub(r'<br/>', '', bereich)
		bereich = sub(r'<b>', '', bereich)
		bereich = sub(r'</b>', '', bereich)
		bereich = sub(r'<i>', '', bereich)
		bereich = sub(r'</i>', '', bereich)
		bereich = sub(r'<a href.*?</a>', '', bereich)
		bereich = sub(r'</h2>\n\\s+<p>', '', bereich)
		bereich = sub(r'&copy;', '', bereich)
		bereich = sub(r'&amp;', '&', bereich)
		self.pixlist = []
		infotext = []
		credits = []
		datenfeld = findall(r'<div\s*class="swiper-slide"(.*?)<span class="counter">', bereich, flags=S)
		for daten in datenfeld:
			foundpix = findall(r'<source srcset="(.*?)" type="image/jpeg">', daten)
			if not foundpix:  # Alternative
				foundpix = findall(r'<img\s*src="(.*?)" alt="', daten)
			if foundpix:
				self.pixlist.append(foundpix[0])
				callInThread(self.threadGetPage, self.pixlist[0], self.getPic, self.downloadError)
			else:
				self.pixlist.append('https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png')
			foundpara1 = findall(r'<div class="firstParagraph">(.*?)</div>', daten, flags=S)
			if foundpara1:
				if foundpara1[0].find('<a class="switch-paragraph" href="#">mehr...</a>'):
					foundpara2 = findall(r'<div class="secondParagraph" style="display:none;">(.*?)</div>', daten, flags=S)
					if foundpara2:
						info = foundpara2[0]
					else:
						info = foundpara1[0]
				else:
					info = foundpara1[0]
			else:
				foundpara2 = findall(r'<div class="secondParagraph" style="(.*?)">(.*?)</div>', daten, flags=S)
				if foundpara2:
					info = foundpara2[0]
				else:
					info = '{keine Beschreibung gefunden}\n'
			info = info.replace(', <a class="switch-paragraph" href="#">mehr...</a>', '').replace('<font size="+1">', '').replace('</font>', '')
			info = info.replace("%s\n" % '<a class="switch-paragraph" href="#">mehr...</a>', '').replace('<br ', '').rstrip()
			infotext.append(info)
			foundcredits = findall(r'<span class="credit">(.*?)</span>', bereich, flags=S)
			if foundcredits:
				credits.append(foundcredits[0])
			else:
				credits.append('')
		self.picmax = len(self.pixlist) if self.pixlist else 0
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))
		self.topline = ["%s\n%s" % (infotext[i], credits[i]) for i in range(self.picmax)]
		self['pictext'].setText(self.topline[self.count])

	def ok(self):
		self.session.openWithCallback(self.dummy, TVSPicShowFull, self.link, self.count)

	def picup(self):
		self.count = (self.count + 1) % self.picmax
		self.picupdate()

	def picdown(self):
		self.count = (self.count - 1) % self.picmax
		self.picupdate()

	def picupdate(self):
		link = self.pixlist[self.count]
		callInThread(self.threadGetPage, link, self.getPic, self.downloadError)
		if self.picmode == 0:
			self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))
			self['pictext'].setText(self.description[self.count])
		else:
			self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))
		if self.topline:
			self['pictext'].setText(self.topline[self.count])

	def gotoPic(self, number):
		self.session.openWithCallback(self.numberEntered, TVSgetNumber, number)

	def numberEntered(self, number):
		if number is None or number == 0:
			pass
		else:
			if number > self.picmax:
				number = self.picmax
			self.count = number
			self.picupdate()
			link = self.pixlist[self.count]
			callInThread(self.threadGetPage, link, self.getPic, self.downloadError)

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

	def downloadError(self, output):
		self['pictext'].setText('Download Fehler')
		TVSlog("Downloaderror in module 'TVSPicShow:downloadError':", output)
		self.showDownloadError(output)

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()

	def dummy(self):
		pass


class TVSPicShowFull(TVSBaseScreen):
	def __init__(self, session, link, count):
		global HIDEFLAG
		skin = readSkin("TVSPicShowFull")
		TVSBaseScreen.__init__(self, session, skin)
		HIDEFLAG = True
		self.pixlist = []
		self.count = count
		self.picmax = 1
		self['release'] = Label(RELEASE)
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['picture'] = Pixmap()
		self['picindex'] = Label()
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
		callInThread(self.threadGetPage, link, self.getPicPage, self.downloadError)

	def getPicPage(self, output):
		output = ensure_str(output)
		self['waiting'].stopBlinking()
		startpos = output.find('<div class="film-gallery">')
		if startpos == -1:
			startpos = output.find('class="film-gallery paragraph')
		endpos = output.find('<div class="swiper-slide more-galleries">')
		if endpos == -1:
			endpos = output.find('<div class="paragraph clear film-gallery"')
		bereich = output[startpos:endpos]
		self.pixlist = findall(r'" data-src="(.*?)" alt=', bereich)
		if not self.pixlist:
			self.pixlist = findall(r'<img src="(.*?)" alt=', bereich)
		if self.pixlist:
			callInThread(self.threadGetPage, self.pixlist[self.count], self.getPic, self.downloadError)
		self.picmax = len(self.pixlist) if self.pixlist else 1
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))

	def picup(self):
		self.count = (self.count + 1) % self.picmax
		self.picupdate()

	def picdown(self):
		self.count = (self.count - 1) % self.picmax
		self.picupdate()

	def picupdate(self):
		link = self.pixlist[self.count]
		callInThread(self.threadGetPage, link, self.getPic, self.downloadError)
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))

	def gotoPic(self, number):
		self.session.openWithCallback(self.numberEntered, TVSgetNumber, number)

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

	def downloadError(self, output):
		self['picindex'].setText('Download Fehler')
		TVSlog("Downloaderror in module 'TVSPicShowFull:downloadError':", output)
		self.showDownloadError(output)

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class TVSFullScreen(TVSAllScreen):
	def __init__(self, session):
		global HIDEFLAG
		skin = readSkin("TVSFullScreen")
		TVSAllScreen.__init__(self, session, skin)
		self.picfile = '/tmp/tvspielfilm.jpg'
		HIDEFLAG = True
		self['picture'] = Pixmap()
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.exit,
																		  'cancel': self.exit,
																		  'blue': self.hideScreen}, -1)
		self.onShown.append(self.showFullPic)

	def showFullPic(self):
		if isfile(self.picfile):
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


class TVSsearchYouTube(TVSAllScreen):
	def __init__(self, session, name, movie):
		global HIDEFLAG
		self.name = ensure_str(name)
		self.LinesPerPage = 6
		skin = readSkin("TVSsearchYouTube")
		TVSAllScreen.__init__(self, session, skin)
		if movie:
			name = "%s Trailer" % name
		name = ensure_str(name.encode('ascii', 'xmlcharrefreplace')).replace(' ', '+')
		self.link = 'https://www.youtube.com/results?filters=video&search_query=%s' % name
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
		self['label2'] = Label(' YouTube Suche')
		self['Line_down'] = Label()
		self['label5'] = Label()
		self['bluebutton'] = Label()
		self.setBlueButton('Aus-/Einblenden')
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
		callInThread(self.threadGetPage, self.link, self.makeTrailerList, self.YTdownloadError)
		self['Line_down'].show()

	def makeTrailerList(self, output):
		output = ensure_str(output)
		self.setTitle(self.titel)
		startpos = output.find('class="masthead-skeleton-icon">')
		endpos = output.find(';/*')
		bereich = unescape(output[startpos:endpos]).replace("&shy;", "-")
		# für Analysezwecke, wenn z.B. der YouTube-Zugang nicht ordentlich läuft
		if config.plugins.tvspielfilm.debuglog.value and config.plugins.tvspielfilm.logtofile.value:
			analyse = bereich.replace('a><a', 'a>\n<a').replace('script><script', 'script>\n<script').replace('},{', '},\n{').replace('}}}]},"publishedTimeText"', '}}}]},\n"publishedTimeText"')
			with open('/home/root/logs/YT-analyse.log', 'w') as f:
				f.write(analyse)
		self.trailer_id = findall(r'{"videoRenderer":{"videoId":"(.*?)","thumbnail', bereich)  # Suchstring voher mit re.escape wandeln
		self.trailer_titel = findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', bereich)
		self.trailer_time = findall(r'"lengthText":{"accessibility":{"accessibilityData":{"label":"(.*?)"}},"simpleText"', bereich)
		trailer_info = findall(r'"viewCountText":{"simpleText":"(.*?)"},"navigationEndpoint"', bereich)
		mh = int(100 * SCALE)
		for i in range(len(self.trailer_id)):
			res = ['']
			titel = self.trailer_titel[i].split(' | ')[0].replace('\\u0026', '&')
			time = self.trailer_time[i] if i < len(self.trailer_time) else ''
			info = trailer_info[i] if i < len(trailer_info) else ''
			res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(10 * SCALE)), size=(int(1060 * SCALE), mh), font=2, color=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=titel))
			res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(65 * SCALE)), size=(int(840 * SCALE), mh), font=1, color=16777215, flags=RT_HALIGN_LEFT, text=time))
			res.append(MultiContentEntryText(pos=(int(800 * SCALE), int(65 * SCALE)), size=(int(220 * SCALE), mh), font=1, color=16777215, flags=RT_HALIGN_RIGHT, text=info))
			self.trailer_list.append(res)
		self['list'].l.setList(self.trailer_list)
		self['list'].l.setItemHeight(int(mh))
		self['list'].moveToIndex(0)
		self.ready = True
		for i in range(self.LinesPerPage):
			try:
				poster = "https://i.ytimg.com/vi/%s/mqdefault.jpg" % self.trailer_id[i]
				callInThread(self.igetPoster, poster, i)
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
			name = str(name.encode('ascii', 'xmlcharrefreplace')).replace(' ', '+')
			self.name = name
			self.link = "https://www.youtube.com/results?filters=video&search_query=%s" % name
			self.count = 1
			self.trailer_id = []
			self.trailer_list = []
			callInThread(self.threadGetPage, self.link, self.makeTrailerList, self.YTdownloadError)

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
				poster = "https://i.ytimg.com/vi/%s/mqdefault.jpg" % self.trailer_id[offset + i]
				try:
					callInThread(self.igetPoster, poster, i)
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

	def igetPoster(self, link, i):
		try:
			response = get(link)
			response.close()
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.YTdownloadError(error)
		else:
			with open(self.localposter[i], 'wb') as f:
				f.write(response.content)
			try:
				self['poster%s' % i].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
				self['poster%s' % i].instance.setPixmapFromFile(self.localposter[i])
			except:
				currPic = loadJPG(self.localposter[i])
				self['poster%s' % i].instance.setScale(1)
				self['poster%s' % i].instance.setPixmap(currPic)

	def YTdownloadError(self, output):
		TVSlog("Downloaderror in module 'TVSsearchYouTube:YTdownloadError':", output)
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Der YouTube Server ist nicht erreichbar:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, '\nDer YouTube Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
		self.close()

	def showHelp(self):
		self.session.open(MessageBox, '\n%s' % 'Bouquet = +- Seite\nGelb = Neue YouTube Suche', MessageBox.TYPE_INFO, close_on_any_key=True)

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if isfile(self.localhtml):
			remove(self.localhtml)
		for i in range(self.LinesPerPage):
			if isfile(self.localposter[i]):
				remove(self.localposter[i])
		self.close()

	def setBlueButton(self, text):
		if ALPHA:
			self['bluebutton'].show()
			self['label5'].setText(text)
			self['label5'].show()
		else:
			self['bluebutton'].hide()
			self['label5'].hide()


class TVSMain(TVSBaseScreen):
	def __init__(self, session):
		global HIDEFLAG
		skin = readSkin("TVSMain")
		TVSBaseScreen.__init__(self, session, skin)
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
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].stopBlinking()
		self['mainmenu'] = ItemList([])
		self['secondmenu'] = ItemList([])
		self['thirdmenu'] = ItemList([])
		self.actmenu = 'mainmenu'
		self['label'] = Label('Import')
		if self.tipps:
			self['label2'] = Label('Tipp')
		self['label5'] = Label()
		self['bluebutton'] = Label()
		self.setBlueButton('Hide')
		self['actions'] = ActionMap(['OkCancelActions',
									 'DirectionActions',
									 'ColorActions',
									 'NumberActions',
									 'MovieSelectionActions',
									 'ChannelSelectBaseActions'], {'ok': self.ok,
																   'cancel': self.exit,
																   'right': self.rightDown,
																   'left': self.leftUp,
																   'down': self.down,
																   'up': self.up,
																   'nextBouquet': self.zap,
																   'prevBouquet': self.zap,
																   '1': self.zapUp,
																   '2': self.zapDown,
																   'yellow': self.config,
																   'red': self.red,
																   'green': self.green,
																   'blue': self.hideScreen,
																   'contextMenu': self.config}, -1)
		self.onShown.append(self.onShownFinished)

	def onShownFinished(self):
		self.movie_stop = config.usage.on_movie_stop.value
		self.movie_eof = config.usage.on_movie_eof.value
		config.usage.on_movie_stop.value = 'quit'
		config.usage.on_movie_eof.value = 'quit'
		if self.tipps and isfile(SERVICEFILE):
			self.TagesTipps = self.session.instantiateDialog(TVSTipps)
			if not self.hidetipps:
				self.startTipps()
		if config.plugins.tvspielfilm.meintvs.value == 'yes':
			self.MeinTVS = True
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
			self.cookiefile = join(PLUGINPATH, 'db/cookie')
			self.cookie = MozillaCookieJar(self.cookiefile)
			if isfile(self.cookiefile):
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
			self.opener = None
			self.makeTimerDB()
			self.checkMainMenu()

	def loginToTVSpielfilm(self):
		values = {'email': self.login, 'pw': self.password, 'perma_login': '1', 'done': '1', 'checkErrors': '1'}
		values = ensure_binary(dumps(values))
		error = None
		loginerror = False
		try:
			# https://member.tvspielfilm.de/login/70.html?email=myNutzername%40gmx.de&pw=myPasswort&perma_login=1&done=1&checkErrors=1
			if self.opener is not None:
				response = self.opener.open("https://member.tvspielfilm.de/login/70.html", data=values, timeout=60)
				result = ensure_str(response.read())
				if search(r'"error":"', result):
					error = search(r'"error":"(.*?)\\.', result)
					error = 'Mein TV SPIELFILM: %s!' % error.group(1) if error is not None else ""
					loginerror = True
					if isfile(self.cookiefile):
						remove(self.cookiefile)
				else:
					self.cookie.save()
				response.close()
		except HTTPException as e:
			error = 'HTTP Exception Error: %s' % e
		except HTTPError as e:
			error = 'HTTP Error: %s' % e.code
		except URLError as e:
			error = 'URL Error: %s' % e.reason
		except SocketError as e:
			error = 'Socket Error: %s' % e
		except AttributeError as e:
			error = 'Attribute Error: %s' % e
		if not error:
			self.makeTimerDB()
			self.checkMainMenu()
		else:
			self.ready = True
			if loginerror:
				self.session.openWithCallback(self.configError, MessageBox, '%s\n\nSetup aufrufen und Einstellungen anpassen?' % error, MessageBox.TYPE_YESNO)
			else:
				self.session.open(MessageBox, '\n%s' % error, MessageBox.TYPE_ERROR)

	def configError(self, answer):
		if answer is True:
			self.config()
		else:
			self.MeinTVS = False
			self.makeTimerDB()
			self.checkMainMenu()

	def ok(self):
		if self.ready:
			try:
				c = self.getIndex(self[self.actmenu])
			except IndexError:
				c = 0
			if self.actmenu == 'mainmenu':
				try:
					if self.tipps:
						self.stopTipps()
					if search(r'jetzt', self.mainmenulink[c]) or search(r'time=shortly', self.mainmenulink[c]) or search(r'abends', self.mainmenulink[c]) or search(r'nachts', self.mainmenulink[c]):
						self.session.openWithCallback(self.selectMainMenu, TVSJetztView, self.mainmenulink[c], False)
					elif search(r'page=1', self.mainmenulink[c]):
						self.session.openWithCallback(self.selectMainMenu, TVSHeuteView, self.mainmenulink[c], self.opener)
					elif search(r'/bilder', self.mainmenulink[c]):
						self.session.openWithCallback(self.selectMainMenu, TVSNews, self.mainmenulink[c])
					elif search(r'/news-und-specials', self.mainmenulink[c]):
						self.session.openWithCallback(self.selectMainMenu, TVSNews, self.mainmenulink[c])
					elif search(r'/tv-tipps|/tv-genre|/trailer-und-clips', self.mainmenulink[c]):
						self.makeSecondMenu(self.mainmenulink[c])
					else:
						self.ready = False
						link = self.mainmenulink[c]
						if isfile(self.senderhtml):
							self.makeSecondMenu(link)
						else:
							self.downloadSender(link)
				except IndexError:
					self.ready = True

			elif self.actmenu == 'secondmenu':
				if search(r'/genre', self.secondmenulink[c]):
					try:
						self.ready = False
						self.makeThirdMenu(self.secondmenulink[c], self.sparte[c])
					except IndexError:
						self.ready = True
				elif search(r'/news|/serien|/streaming|/trailer-und-clips|/stars|/charts|/neustarts|/neuerscheinungen|/kino-vorschau|/tatort|/kids-tv|/bestefilme|/tv-programm|/tv-tipps|/awards|/oscars', self.secondmenulink[c]):
					try:
						self.session.openWithCallback(self.selectSecondMenu, TVSNews, self.secondmenulink[c])
					except IndexError:
						pass
				else:
					try:
						self.ready = False
						self.makeThirdMenu(None, self.sender[c])
					except IndexError:
						self.ready = True

			elif self.actmenu == 'thirdmenu':
				if search(r'/genre', self.thirdmenulink[c]):
					if self.tipps:
						self.stopTipps()
					self.session.openWithCallback(self.selectThirdMenu, TVSNews, self.thirdmenulink[c])
				if search(r'/suche', self.thirdmenulink[c]):
					if self.tipps:
						self.stopTipps()
					self.session.openWithCallback(self.selectThirdMenu, self.TVSGenreView, self.thirdmenulink[c], self.genre[c])
				elif search(r'/tv-tipps', self.thirdmenulink[c]):
					if self.tipps:
						self.stopTipps()
					self.session.openWithCallback(self.selectThirdMenu, self.TVSTippsView, self.thirdmenulink[c], self.genre[c])
				else:
					if self.tipps:
						self.stopTipps()
					link = self.thirdmenulink[c].replace('my.tvspielfilm.de', 'www.tvspielfilm.de')
					self.session.openWithCallback(self.selectThirdMenu, TVSProgrammView, link, False, False)

	def makeMainMenuItem(self, text, link):
		res = ['']
		res.append(MultiContentEntryText(pos=(0, 1), size=(int(310 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=text))
		self.mainmenulist.append(res)
		self.mainmenulink.append("%s%s" % (self.baseurl, link))

	def makeSecondMenuItem(self, text):
		self.makeSecondMenuItem3(text, '')
		self.sender.append(text)

	def makeSecondMenuItem2(self, text, link):
		self.makeSecondMenuItem3(text, link)
		self.sparte.append(text)

	def makeSecondMenuItem3(self, text, link):
		res = ['']
		res.append(MultiContentEntryText(pos=(0, 1), size=(int(310 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=text))
		self.secondmenulist.append(res)
		self.secondmenulink.append("%s%s" % (self.baseurl, link))

	def makeMainMenu(self):
		if not self.mainmenulist:
			self.makeMainMenuItem('Heute im TV', '/tv-programm/tv-sender/?page=1')
			self.makeMainMenuItem('Jetzt im TV', '/tv-programm/sendungen/jetzt.html')
			self.makeMainMenuItem('Gleich im TV', '/tv-programm/sendungen/?page=1&order=time&time=shortly')
			self.makeMainMenuItem('20:15 im TV', '/tv-programm/sendungen/abends.html')
			self.makeMainMenuItem('22:00 im TV', '/tv-programm/sendungen/fernsehprogramm-nachts.html')
			self.makeMainMenuItem('TV-Programm', '/tv-programm/tv-sender/')
			self.makeMainMenuItem('News', '/news/')
			self.makeMainMenuItem('Streaming', '/streaming/')
			self.makeMainMenuItem('TV-Tipps', '/tv-tipps/')
			self.makeMainMenuItem('Serien', '/serien/')
			self.makeMainMenuItem('Filme', '/kino/')
			self.makeMainMenuItem('Stars', '/stars/')
			self.makeMainMenuItem('Nachrichten', '/news-und-specials/')
			self.makeMainMenuItem('Bildergalerien', '/bilder/')
		self['mainmenu'].l.setList(self.mainmenulist)
		self['mainmenu'].l.setItemHeight(int(30 * SCALE))
		self.selectMainMenu()

	def makeSecondMenu(self, link):
		if isfile(self.senderhtml):
			output = ensure_str(open(self.senderhtml, 'r').read())
		else:
			output = ''
		self.secondmenulist = []
		self.secondmenulink = []
		self.sender = []
		self.sparte = []
		if search(r'/tv-sender/', link):
			startpos = output.find('<option value="" label="Alle Sender">Alle Sender</option>')
			endpos = output.find('<div class="button-toggle">')
			bereich = output[startpos: endpos]
			bereich = unescape(bereich).replace("&shy;", "-")
			name = findall(r'<optgroup label="(.*?)">', bereich)
			for ni in name:
				self.makeSecondMenuItem(ni)
			if self.tipps:
				self.hideTipps()
		elif search(r'/news/', link):
			self.makeSecondMenuItem3('TV-News', '/news/tv/')
			self.makeSecondMenuItem3('Serien-News', '/news/serien/')
			self.makeSecondMenuItem3('Streaming-News', '/news/streaming/')
			self.makeSecondMenuItem3('Film-News', '/news/filme/')
			self.makeSecondMenuItem3('Star-News', '/news/stars/')
			self.makeSecondMenuItem3('Shopping-News', '/news/shopping/')
		elif search(r'/tv-tipps/', link):
			self.makeSecondMenuItem3('Filmtipps', '/tv-tipps/spielfilm/')
			self.makeSecondMenuItem3('Serie', '/tv-tipps/serien/')
			self.makeSecondMenuItem3('Unterhaltung', '/tv-tipps/unterhaltung/')
			self.makeSecondMenuItem3('Sport', '/tv-tipps/sport/')
			self.makeSecondMenuItem3('Report', '/tv-tipps/report/')
			self.makeSecondMenuItem3('Kinder', '/kids-tv/')
			self.makeSecondMenuItem3('Free-TV', '/tv-tipps/free-tv/')
			self.makeSecondMenuItem3('Pay-TV', '/tv-tipps/pay-tv/')
			self.makeSecondMenuItem3('Erstmals im Free-TV', '/tv-tipps/galerien/freetvpremieren/')
			self.makeSecondMenuItem3('Programmänderungen', '/tv-programm/programmaenderung/')
		elif search(r'/serien/', link):
			self.makeSecondMenuItem2('Serien-News', '/news/serien/')
			self.makeSecondMenuItem2('Quizze', '/news/quizze/')
			self.makeSecondMenuItem2('Serien-Trailer', '/serien/serien-trailer/')
			self.makeSecondMenuItem2('Genres', '/serien/genre/')
			self.makeSecondMenuItem2('Beste Serien', '/news/serien/die-besten-us-serien-aller-zeiten,9250353,ApplicationArticle.html')
			self.makeSecondMenuItem2('Beste Netflix Serien', '/news/serien/die-besten-netflix-serien,9437468,ApplicationArticle.html')
			self.makeSecondMenuItem2('The Walking Dead', '/serien/walkingdead/')
			self.makeSecondMenuItem2('The Big Bang Theory', '/serien/thebigbangtheory/')
			self.makeSecondMenuItem2('''Grey's Anatomy''', '/serien/greys-anatomy/')
			self.makeSecondMenuItem2('Tatort', '/tatort/')
		elif search(r'/streaming/', link):
			self.makeSecondMenuItem3('Streaming-News', '/news/streaming/')
			self.makeSecondMenuItem3('Streaming-Vergleich', '/streaming/streamingvergleich/')
			self.makeSecondMenuItem3('Neu auf Netflix', '/news/filme/neu-bei-netflix-diese-serien-und-filme-lohnen-sich,8941871,ApplicationArticle.html')
			self.makeSecondMenuItem3('Neu bei Amazon Prime', '/news/filme/neu-bei-amazon-prime-diese-serien-und-filme-lohnen-sich,10035760,ApplicationArticle.html')
			self.makeSecondMenuItem3('Neu auf Disney+', '/news/serien/neu-auf-disneyplus-serien-filme,10127377,ApplicationArticle.html')
			self.makeSecondMenuItem3('Sky Ticket', '/news/serien/neu-auf-sky-ticket-die-besten-filme-und-serien,10090987,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Netflix Serien', '/news/serien/die-besten-netflix-serien,9437468,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Netflix Filme', '/news/filme/die-besten-netflix-filme,9659520,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Amazon Prime Filme', '/news-und-specials/die-besten-filme-bei-amazon-prime-unsere-empfehlungen,10155040,ApplicationArticle.html')
		elif search(r'/kino/', link):
			self.makeSecondMenuItem2('Film-News', '/news/filme/')
			self.makeSecondMenuItem2('Beste Filme', '/bestefilme/')
			self.makeSecondMenuItem2('Filmtipps', '/bestefilme/toplisten/')
			self.makeSecondMenuItem2('Trailer', '/kino/trailer-und-clips/')
			self.makeSecondMenuItem2('Genres', '/genre/')
			self.makeSecondMenuItem2('Neu im Kino', '/kino/neustarts/')
			self.makeSecondMenuItem2('Kino-Charts', '/kino/charts/')
			self.makeSecondMenuItem2('Kino Vorschau', '/kino/kino-vorschau/')
			self.makeSecondMenuItem2('Neu auf DVD', '/dvd/neuerscheinungen/')
			self.makeSecondMenuItem2('DVD Charts', '/kino/dvd/charts/')
			self.makeSecondMenuItem2('TV Spielfilm Awards', '/stars/awards/')
			self.makeSecondMenuItem2('Oscar - Academy Awards', '/kino/oscars/')
		elif search(r'/stars/', link):
			self.makeSecondMenuItem3('Star-News', '/news/stars/')
			self.makeSecondMenuItem3('Star-Videos', '/news-und-specials/star-video-news/')
			self.makeSecondMenuItem3('Interviews', '/news-und-specials/interviewsundstories/')
			self.makeSecondMenuItem3('TV Spielfilm Awards', '/stars/awards/')
			self.makeSecondMenuItem3('Stars A-Z', '/kino/stars/archiv/')
		self['secondmenu'].l.setList(self.secondmenulist)
		self['secondmenu'].l.setItemHeight(int(30 * SCALE))
		self.selectSecondMenu()

	def makeThirdMenuItem(self, output, start):
		startpos = output.find('<optgroup label="%s"' % start)
		endpos = output.find('</optgroup>', startpos)
		bereich = unescape(output[startpos: endpos]).replace("&shy;", "-")
		lnk = findall(r"value='(.*?)'", bereich)
		name = findall(r"<option label='(.*?)'", bereich)
		for i, ni in enumerate(name):
			res = ['']
			res.append(MultiContentEntryText(pos=(0, 1), size=(int(310 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=ni))
			self.thirdmenulist.append(res)
			self.thirdmenulink.append(lnk[i])

	def makeThirdMenuItem2(self, genre, link):
		res = ['']
		res.append(MultiContentEntryText(pos=(0, 1), size=(int(310 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=genre))
		self.thirdmenulist.append(res)
		self.thirdmenulink.append(link)
		self.genre.append(genre)

	def makeThirdMenu(self, link, sender):
		self.thirdmenulist = []
		self.thirdmenulink = []
		self.genre = []
		if link is None:
			output = ensure_str(open(self.senderhtml, 'r').read())
			startpos = output.find('<option value="" label="Alle Sender">Alle Sender</option>')
			endpos = output.find('<div class="button-toggle">')
			string = unescape(output[startpos: endpos]).replace("&shy;", "-")
			self.makeThirdMenuItem(string, sender)
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
				self['waiting'].stopBlinking()
				self['label2'].show()
		self.ready = True

	def selectSecondMenu(self):
		if len(self.secondmenulist):
			self.actmenu = 'secondmenu'
			self['mainmenu'].hide()
			self['secondmenu'].show()
			self['thirdmenu'].hide()
			self['mainmenu'].selectionEnabled(0)
			self['secondmenu'].selectionEnabled(1)
			self['thirdmenu'].selectionEnabled(0)
			if self.tipps and not self.hidetipps:
				self.showTipps()
		self.ready = True

	def selectThirdMenu(self):
		if len(self.thirdmenulist):
			self.actmenu = 'thirdmenu'
			self['mainmenu'].hide()
			self['secondmenu'].hide()
			self['thirdmenu'].show()
			self['mainmenu'].selectionEnabled(0)
			self['secondmenu'].selectionEnabled(0)
			self['thirdmenu'].selectionEnabled(1)
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

	def checkMainMenu(self):
		if isfile(SERVICEFILE):
			self.makeMainMenu()
		else:
			self.session.openWithCallback(self.returnFirstRun, TVSmakeServiceFile)

	def downloadSender(self, link):
		if self.MeinTVS:
			error = None
			try:
				if self.opener is not None:
					response = self.opener.open(link, timeout=60)
					data = response.read()
					with open(self.senderhtml, 'wb') as f:
						f.write(data)
					response.close()
			except HTTPException as e:
				error = 'HTTP Exception Error: %s' % e
			except HTTPError as e:
				error = 'HTTP Error: %s' % e.code
			except URLError as e:
				error = 'URL Error: %s' % e.reason
			except SocketError as e:
				error = 'Socket Error: %s' % e
			except AttributeError as e:
				error = 'Attribute Error: %s' % e
			if not error:
				self.makeSecondMenu(link)
			else:
				self.showDownloadError(error)
		else:
			callInThread(self.download, link, self.makeSecondMenu)

	def download(self, link, name):
		try:
			response = get(link)
			response.close()
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.downloadError(error)
		else:
			with open(self.senderhtml, 'wb') as f:
				f.write(response.content)
			name(link)

	def getIndex(self, list):
		return list.getSelectedIndex()

	def red(self):
		if self.ready:
			if self.tipps:
				self.stopTipps()
			self.session.openWithCallback(self.returnRed, MessageBox, '\nImportiere TV Spielfilm Sender?', MessageBox.TYPE_YESNO)

	def returnRed(self, answer):
		if answer is True:
			if isfile(SERVICEFILE):
				remove(SERVICEFILE)
			self.session.openWithCallback(self.returnServiceFile, TVSmakeServiceFile)

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
			if isfile(self.senderhtml):
				remove(self.senderhtml)
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.session.openWithCallback(self.closeconf, TVSConfig)

	def closeconf(self):
		if isfile(self.picfile):
			remove(self.picfile)
		for i in range(6):
			if isfile(self.pics[i]):
				remove(self.pics[i])
		if isfile(self.senderhtml):
			remove(self.senderhtml)
		if isfile(self.localhtml):
			remove(self.localhtml)
		if isfile(self.localhtml2):
			remove(self.localhtml2)
		self.close()

	def zapUp(self):
		if InfoBar and InfoBar.instance:
			InfoBar.zapUp(InfoBar.instance)

	def zapDown(self):
		if InfoBar and InfoBar.instance:
			InfoBar.zapDown(InfoBar.instance)

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
				self.stopTipps()
				self.session.deleteDialog(self.TagesTipps)
			if isfile(self.picfile):
				remove(self.picfile)
			for i in range(6):
				if isfile(self.pics[i]):
					remove(self.pics[i])
			if isfile(self.senderhtml):
				remove(self.senderhtml)
			if isfile(self.localhtml):
				remove(self.localhtml)
			if isfile(self.localhtml2):
				remove(self.localhtml2)
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.close()
		elif self.actmenu == 'secondmenu':
			self['secondmenu'].moveToIndex(0)
			self.selectMainMenu()
		elif self.actmenu == 'thirdmenu':
			self['thirdmenu'].moveToIndex(0)
			self.selectSecondMenu()


class TVSmakeServiceFile(Screen):
	def __init__(self, session):
		self.skin = readSkin("TVSmakeServiceFile")
		Screen.__init__(self, session)
		dic = {}
		dic['picpath'] = PICPATH
		dic['selbg'] = str(config.plugins.tvspielfilm.selectorcolor.value)
		self.skin = applySkinVars(self.skin, dic)
		self['list'] = MenuList([])
		self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.ok,
														  'cancel': self.exit}, -1)
		self.fdata = ''
		self.supported = ''
		self.unsupported = ''
		self.ready = False
		self.onShown.append(self.getBouquets)

	def getBouquets(self):
		bouquets = []
		if config.usage.multibouquet.value:
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
		self.ready = True

	def ok(self):
		if self.ready:
			self.ready = False
			try:
				bouquet = self.getCurrent()
			except Exception:
				bouquet = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
				bouquet = eServiceReference(bouquet)
			from Components.Sources.ServiceList import ServiceList
			slist = ServiceList(bouquet, validate_commands=False)
			services = slist.getServicesAsList(format='SN')
			data = ''
			for service in services:
				sref = service[0].split('http')[0].replace("4097:", "1:").replace(":21:", ":C00000:") if "http" in service[0].lower() else service[0]
				data += '%s %s\n' % (service[1], sref)
				self.fdata += '%s\n' % '{0:<40} {1:<0}'.format(service[1], sref)
			supported, unsupported = transCHANNEL(data, separate=True)
			newfound = 0
			for line in supported.split("\n"):
				channel = line[: line.find(' ')].strip()
				if channel not in self.supported:
					self.supported += "%s\n" % line
					newfound += 1
			for line in unsupported.split("\n"):
				channel = line[: line.find(' ')].strip()
				if channel not in self.unsupported:
					self.unsupported += "%s\n" % line
			newdata = ''
			self.imported = ''
			fnew = open("%s.new" % SERVICEFILE, 'w')
			dnew = open("%s.new" % DUPESFILE, 'w')
			for line in self.supported.split("\n"):
				line = line.strip()
				channel = line[: line.find(' ')].strip()
				sref = line[line.find(' '):].strip()
				if line != '' and ',' not in line:
					if '#%s' % channel not in newdata:
						fnew.write(line)
						fnew.write(linesep)
					else:
						dnew.write(line)
						dnew.write(linesep)
					self.imported += '%s\n' % '{0:<15} {1:<0}'.format(channel, sref)
					newdata = "%s#%s" % (newdata, channel)
			dnew.close()
			fnew.close()
			rename("%s.new" % DUPESFILE, DUPESFILE)
			rename("%s.new" % SERVICEFILE, SERVICEFILE)
			self.ready = True
			if newdata == '':
				self.session.openWithCallback(self.noBouquet, MessageBox,
					'\nKeine TV Spielfilm Sender gefunden.\nBitte wählen Sie ein anderes TV Bouquet.', MessageBox.TYPE_YESNO)
			else:
				self.session.openWithCallback(self.otherBouquet, MessageBox,
					'\nZuletzt gefundene neue TV Spielfilm Sender: %s\nInsgesamt importierte TV Spielfilm Sender: %s\n\nMöchten Sie ein weiteres TV Bouquet importieren?' %
					(newfound, len(self.imported.rstrip().split("\n"))), MessageBox.TYPE_YESNO, default=False)

	def Bouquetlog(self, info, debug=False):
		if debug and not config.plugins.tvspielfilm.debuglog.value:
			return
		if config.plugins.tvspielfilm.logtofile.value:
			try:
				with open('/home/root/logs/Bouquetimport.log', 'a') as f:
					f.write(info)
			except IOError:
				TVSlog("Logging-Error in 'globals:Bouquetlog': %s" % IOError)

	def otherBouquet(self, answer):
		if answer is True:
			self.getBouquets()
		else:
			# für Analysezwecke, z.B. zur Überprüfung der Wandlung 'Sendername' in 'Kürzel/Piconname'
			logdatei = '/home/root/logs/Bouquetimport.log'
			imported = len(self.imported.rstrip().split("\n"))
			unsupported = len(self.unsupported.rstrip().split("\n"))
			all = imported + unsupported
			if isfile(logdatei):
				remove(logdatei)
			self.Bouquetlog('%i gefundene Sender aus den Bouquets (inklusive Doppelte):\n%s\n' % (len(self.fdata.split("\n")), '-' * 78))
			self.Bouquetlog(self.fdata)
			self.Bouquetlog('%s\ndavon %i unterschiedliche TV Spielfilm Sender (ohne Doppelte)\n' % ('-' * 78, imported + unsupported))
			self.Bouquetlog('\n%i importierte Sender als Küzel/Piconname (ohne Doppelte):\n%s\n' % (imported, '-' * 78))
			self.Bouquetlog(self.imported)
			self.Bouquetlog('\n%i nicht unterstützte TV Spielfilm Sender als Küzel/Piconname (ohne Doppelte):\n%s\n' % (unsupported, '-' * 78))
			self.Bouquetlog(self.unsupported)
			self.close(True)

	def noBouquet(self, answer):
		if answer is True:
			self.getBouquets()
		else:
			if isfile(SERVICEFILE):
				remove(SERVICEFILE)
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


class TVSgetNumber(Screen):
	def __init__(self, session, number):
		self.skin = readSkin("TVSgetNumber")
		Screen.__init__(self, session)
		self.field = str(number)
		self['release'] = Label(RELEASE)
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
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
		self.field = "%s%s" % (self.field, number)
		self['number'].setText(self.field)
		if len(self.field) >= 4:
			self.keyOK()

	def keyOK(self):
		self['waiting'].stopBlinking()
		self.Timer.stop()
		self.close(int(self['number'].getText()))

	def quit(self):
		self.Timer.stop()
		self.close(0)


class TVSgotoPageMenu(TVSAllScreen):
	def __init__(self, session, count, maxpages):
		global HIDEFLAG
		self.skin = readSkin("TVSgotoPageMenu")
		TVSAllScreen.__init__(self, session)
		self.localhtml = '/tmp/tvspielfilm.html'
		HIDEFLAG = True
		self.index = count - 1
		self.maxpages = maxpages
		self.pagenumber = []
		self.pagemenulist = []
		self['release'] = Label(RELEASE)
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
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
		self.onLayoutFinish.append(self.makePageMenu)

	def makePageMenu(self):
		self.setTitle('Senderliste')
		self['waiting'].stopBlinking()
		output = ensure_str(open(self.localhtml, 'r').read())
		startpos = output.find('label="Alle Sender">Alle Sender</option>')
		if config.plugins.tvspielfilm.meintvs.value == 'yes':
			endpos = output.find('<optgroup label="Hauptsender">')
		else:
			endpos = output.find('<optgroup label="alle Sender alphabetisch">')
		bereich = output[startpos:endpos]
		sender = findall(r'"channel":"(.*?)","broadcastChannelGroup"', bereich)
		sender = [sub.replace('&amp;', '&') for sub in sender]
		# für Analysezwecke, z.B. wenn Picon fehlen oder überflüsssig sind
		if config.plugins.tvspielfilm.debuglog.value and config.plugins.tvspielfilm.logtofile.value:
			from glob import glob
			fullnames = findall(r"<option label='(.*?)' value=", bereich)
			ff = open('/home/root/logs/komplette_Senderliste.log', 'w')
			ff.write('vollständige Liste der unterstützten Sender:\n')
			ff.write('%s\n' % ('-' * 78))
			i = -1
			for i, sendung in enumerate(sender):
				ff.write('%s\n' % '{0:<30} {1:<2} {2:10}'.format(fullnames[i], '=', sendung.lower()))
			ff.write('%s\n' % ('-' * 78))
			ff.write('Anzahl : %s Sender' % (i + 1))
			ff.close()
			availpicons = glob(join(PLUGINPATH, 'picons/*.png'))
			if availpicons:
				ff = open('/home/root/logs/verfuegbare_Picons.log', 'w')
				ff.write('Liste der verfügbaren Picon im Pluginpfad ./picons/:\n')
				ff.write('%s\n' % ('-' * 78))
				for availpicon in availpicons:
					availpicon = availpicon[availpicon.rfind('/') + 1:]
					ff.write("%s\n" % availpicon)
				ff.close()
				ff = open('/home/root/logs/fehlende_Picons.log', 'w')
				ff.write('Liste der fehlenden Picons im Pluginpfad ./picons/:\n')
				ff.write('%s\n' % ('-' * 78))
				for i, sendung in enumerate(sender):
					eintrag = join(PLUGINPATH, 'picons/%s.png' % sendung.lower())
					if isfile(eintrag):
						availpicons = list(set(availpicons).difference(set([eintrag])))
					else:
						ff.write('%s, %s.png\n' % (fullnames[i], sendung.lower()))
				ff.close()
				ff = open('/home/root/logs/ungenutze_Picons.log', 'w')
				ff.write('Liste der ungenutzten Picons im Pluginpfad ./picons/:\n')
				ff.write('%s\n' % ('-' * 78))
				for availpicon in availpicons:
					ff.write("%s\n" % availpicon)
				ff.close()
		self.maxpages = len(sender) // 6
		if len(sender) % 6 != 0:
			self.maxpages += 1
		count = 0
		page = 1
		mh = int(37 * SCALE + 0.5)
		while page <= self.maxpages:
			res = ['']
			res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(2 * SCALE)), size=(int(28 * SCALE), mh), font=1,
					   color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=str(page)))
			for i in range(6):
				try:
					service = sender[count].lower().replace(' ', '').replace('.', '').replace('ii', '2')
					png = join(PLUGINPATH, 'picons/%s.png' % service)
					if isfile(png):
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
		c = self.getIndex(self['pagemenu'])
		self.close(int(self.pagenumber[c]))

	def gotoPage(self, number):
		self.session.openWithCallback(self.numberEntered, TVSgetNumber, number)

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

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close(0)


class TVSTipps(TVSAllScreen):
	def __init__(self, session):
		global HIDEFLAG
		self.dict = {'picpath': PICPATH, 'selbg': str(config.plugins.tvspielfilm.selectorcolor.value)}
		skin = readSkin("TVSTipps")
		self.skin = applySkinVars(skin, self.dict)
		TVSAllScreen.__init__(self, session)
		self.baseurl = 'http://www.tvspielfilm.de'
		self.localhtml = '/tmp/tvspielfilm.html'
		self.count = 0
		self.ready = False
		HIDEFLAG = True
		self.max = 6
		self.pics = []
		for i in range(self.max):
			self.pics.append('/tmp/tvspielfilm%s.jpg' % i)
		self.infolink = ''
		self.tippsinfo = []
		self.tippslink = []
		self.tippschannel = []
		self.tippspicture = []
		self['picture'] = Pixmap()
		self['thumb'] = Pixmap()
		self['picture'].hide()
		self['thumb'].hide()
		self['label'] = Label()
		self['label2'] = Label()
		self['label3'] = Label()
		self['label4'] = Label()
		self['label5'] = Label()
		self['label6'] = Label()
		self['label'].hide()
		self['label2'].hide()
		self['label3'].hide()
		self['label4'].hide()
		self['label5'].hide()
		self['label6'].hide()
		self['1_zapup'] = Pixmap()
		self['2_zapdown'] = Pixmap()
		self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.ok,
														  'cancel': self.exit}, -1)
		self.onLayoutFinish.append(self.start)

	def start(self):
		callInThread(self.downloadFirst, self.baseurl)
		self.getNextTimer = eTimer()
		self.getNextTimer.callback.append(self.nextTipp)
		self.getNextTimer.start(5000, False)

	def stop(self):
		self.getNextTimer.stop()
		if self.nextTipp in self.getNextTimer.callback:
			self.getNextTimer.callback.remove(self.nextTipp)
		self.hide()

	def getTagesTipps(self, output):
		output = ensure_str(output)
		self.ready = False
		startpos = output.find('<div class="content-teaser sub-navigation-teaser teaser-m sub-navigation-teaser teaser-m-standard">')
		endpos = output.find('<div id="nav-r" class="navigation-display-table">')
		bereich = output[startpos:endpos]
		self.tippspicture = findall(r'data-src="(.*?)"', bereich, flags=S)
		for idx, link in enumerate(self.tippspicture):
			callInThread(self.idownload, idx, link)
		self.tippschannel = findall(r'<span class="subline .*?">(.*?)</span>', bereich)
		try:
			parts = self.tippschannel[0].split(' | ')
			times = parts[1]
			channel = shortenChannel(parts[2])
			self['label4'].setText(times)
			self['label4'].show()
			self['label5'].setText(channel[0:10])
			self['label5'].show()
		except IndexError:
			self['label4'].hide()
			self['label5'].hide()
		self.tippsinfo = findall(r'<span class="headline">(.*?)</span>', bereich)
		self.tippslink = findall(r'<a href="(.*?)" target', bereich)
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
		self['label'].show()
		self['label2'].setText(titel)
		self['label2'].show()
		self['label3'].setText(text)
		self['label3'].show()
		self['thumb'].show()
		self.ready = True

	def idownload(self, idx, link):  # TVTipps-PicsDownload
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		try:
			response = get(link)
			response.close()
			response.raise_for_status()
		except exceptions.RequestException as error:
			TVSlog("Downloaderror in module 'TVSTipps:idownload': %s" % link)
			self.showDownloadError(error)
		else:
			with open(self.pics[idx], 'wb') as f:
				f.write(response.content)
			if idx == 0:
				showPic(self['picture'], self.pics[idx])

	def ok(self):
		if self.ready and search(r'/tv-programm/sendung/', self.infolink):
			self.hide()
			self.getNextTimer.stop()
			self.session.openWithCallback(self.returnInfo, TVSProgrammView, self.infolink, False, True)

	def returnInfo(self):
		self.getNextTimer.start(5000, False)

	def nextTipp(self):
		if self.ready and len(self.tippspicture) > 0:
			self.count += 1
			self.count = self.count % len(self.tippspicture)
			if isfile(self.pics[self.count]):
				showPic(self['picture'], self.pics[self.count])
			self.infolink = self.tippslink[self.count]
			tipp = 'Tipp des Tages'
			titel = self.tippsinfo[self.count]
			text = self.tippschannel[self.count]
			self['label'].setText(tipp)
			self['label'].show()
			self['label2'].setText(titel)
			self['label2'].show()
			self['label3'].setText(text)
			self['label3'].show()
			parts = self.tippschannel[self.count].split(' | ')
			times = parts[1]
			channel = shortenChannel(parts[2])
			self['label4'].setText(times)
			self['label4'].show()
			self['label5'].setText(channel[0:10])
			self['label5'].show()

	def downloadFirst(self, link):
		try:
			response = get(link)
			response.close()
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.ready = True
			self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar:\n%s' % error, MessageBox.TYPE_ERROR)
		else:
			self.getTagesTipps(response.content)

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class TVSConfig(ConfigListScreen, TVSAllScreen):
	def __init__(self, session):
		skin = readSkin("TVSConfig")
		TVSAllScreen.__init__(self, session, skin)
		self.password = config.plugins.tvspielfilm.password.value
		self.encrypt = config.plugins.tvspielfilm.encrypt.value
		self['release'] = Label(RELEASE)
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['plugin'] = Pixmap()
		ConfigListScreen.__init__(self, [], on_change=self.UpdateComponents)
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'cancel': self.exit,
																		  'red': self.exit,
																		  'green': self.save}, -1)
		self.onLayoutFinish.append(self.UpdateComponents)

	def createSetup(self):
		list = []
		if config.plugins.tvspielfilm.plugin_size == 'FHD':
			list.append(getConfigListEntry('Plugin Größe:', config.plugins.tvspielfilm.plugin_size))
		list.append(getConfigListEntry('Verwende Plugin-eigene Schrift:', config.plugins.tvspielfilm.font))
		list.append(getConfigListEntry('Schriftgröße Auswahlzeilen:', config.plugins.tvspielfilm.font_size))
		list.append(getConfigListEntry('Farbe des Auswahlbalkens:', config.plugins.tvspielfilm.selectorcolor))
		list.append(getConfigListEntry('Benutze Mein TV SPIELFILM:', config.plugins.tvspielfilm.meintvs))
		list.append(getConfigListEntry('Login (E-mail):', config.plugins.tvspielfilm.login))
		list.append(getConfigListEntry('Passwort:', config.plugins.tvspielfilm.password))
		list.append(getConfigListEntry('Passwort Verschlüsselung:', config.plugins.tvspielfilm.encrypt))
		list.append(getConfigListEntry('Herkunft der Picons:', config.plugins.tvspielfilm.picon))
		if config.plugins.tvspielfilm.picon.value == "user":
			list.append(getConfigListEntry('Eigener Picon Ordner:', config.plugins.tvspielfilm.piconfolder))
			piconfolder = config.plugins.tvspielfilm.piconfolder.value
			if not isdir(piconfolder):
				list.append(getConfigListEntry('>>> Eigener Picon Ordner nicht vorhanden, nutze Plugin-eigene Picons <<<'))
				piconfolder = PICONPATH
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			piconfolder = "%spicons/" % PICPATH
		else:
			piconfolder = PICONPATH
		list.append(getConfigListEntry('Zeige Tipp des Tages:', config.plugins.tvspielfilm.tipps))
		list.append(getConfigListEntry('Starte Heute im TV mit:', config.plugins.tvspielfilm.primetime))
		list.append(getConfigListEntry('Starte TVS EventView mit:', config.plugins.tvspielfilm.eventview))
		list.append(getConfigListEntry('Beende TVS Jetzt nach dem Zappen:', config.plugins.tvspielfilm.zapexit))
		list.append(getConfigListEntry('Zeige Genre/Episode/Jahr am Ende des Titels:', config.plugins.tvspielfilm.genreinfo))
		list.append(getConfigListEntry('Max. Seiten Sendungen (Gleich / 20:15 / 22:00):', config.plugins.tvspielfilm.maxlist))
		list.append(getConfigListEntry('Max. Seiten TV-Suche:', config.plugins.tvspielfilm.maxsearch))
		list.append(getConfigListEntry('Benutze AutoTimer Plugin:', config.plugins.tvspielfilm.autotimer))
		list.append(getConfigListEntry('Maximale YouTube-Auflösung:', config.plugins.tvspielfilm.ytresolution))
		list.append(getConfigListEntry('DebugLog', config.plugins.tvspielfilm.debuglog, "Debug Logging aktivieren"))
		list.append(getConfigListEntry('Log in Datei', config.plugins.tvspielfilm.logtofile, "Log in Datei '/home/root/logs'"))
		self["config"].setList(list)

	def UpdateComponents(self):
		self['waiting'].stopBlinking()
		self.createSetup()

	def keySelect(self):
		if self["config"].getCurrent()[1] is config.plugins.tvspielfilm.piconfolder:
			self.session.openWithCallback(self.folderSelected, LocationBox, text="Wähle Zielordner")
		else:
			ConfigListScreen.keySelect(self)

	def folderSelected(self, folder):
		if folder:
			config.plugins.tvspielfilm.piconfolder.value = folder

	def save(self):
		if config.plugins.tvspielfilm.password.value != self.password:
			if config.plugins.tvspielfilm.encrypt.value == 'yes':
				config.plugins.tvspielfilm.password.value = b64encode(ensure_binary(config.plugins.tvspielfilm.password.value))
		elif config.plugins.tvspielfilm.encrypt.value != self.encrypt:
			if self.encrypt == 'yes':
				try:
					config.plugins.tvspielfilm.password.value = b64decode(config.plugins.tvspielfilm.password.value.encode('ascii', 'xmlcharrefreplace'))
				except TypeError:
					pass
			else:
				config.plugins.tvspielfilm.password.value = b64encode(ensure_binary(config.plugins.tvspielfilm.password.value))
		ConfigListScreen.saveAll(self)
		self.exit()

	def exit(self):
		if config.plugins.tvspielfilm.meintvs.value == 'yes' and config.plugins.tvspielfilm.login.value == '' or config.plugins.tvspielfilm.meintvs.value == 'yes' and config.plugins.tvspielfilm.password.value == '':
			self.session.openWithCallback(
				self.nologin_return, MessageBox, 'Sie haben den Mein TV SPIELFILM Login aktiviert, aber unvollständige Login-Daten angegeben.\n\nMöchten Sie die Mein TV SPIELFILM Login-Daten jetzt angeben oder Mein TV SPIELFILM deaktivieren?', MessageBox.TYPE_YESNO)
		else:
			self.session.openWithCallback(self.close, TVSMain)

	def nologin_return(self, answer):
		if answer is True:
			pass
		else:
			config.plugins.tvspielfilm.meintvs.value = 'no'
			config.plugins.tvspielfilm.meintvs.save()
			configfile.save()
			self.session.openWithCallback(self.close, TVSMain)


class TVSHeuteView(TVSBaseScreen):
	def __init__(self, session, link, opener):
		global HIDEFLAG
		skin = readSkin("TVSHeuteView")
		TVSBaseScreen.__init__(self, session, skin)
		if config.plugins.tvspielfilm.meintvs.value == 'yes':
			self.MeinTVS = True
			self.opener = opener
			page = sub(r'https://my.tvspielfilm.de/tv-programm/tv-sender/.page=', '', link)
			self.count = int(page)
		else:
			self.MeinTVS = False
			page = sub(r'https://www.tvspielfilm.de/tv-programm/tv-sender/.page=', '', link)
			self.count = int(page)
		self.tventriess = [[] for _ in range(6)]
		self.tvlinks = [[] for _ in range(6)]
		self.tvtitels = [[] for _ in range(6)]
		self.srefs = [[] for _ in range(6)]
		self.zaps = [True for _ in range(6)]
		self.spalten = 6
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
		self.rec = False
		self.first = True
		self.ready = False
		self.postviewready = False
		self.mehrbilder = False
		self.movie = False
		self.datum = False
		self.oldindex = 0
		self.oldsearchindex = 1
		self.finishedTimerMode = 2
		self.localhtml = '/tmp/tvspielfilm.html'
		self['release'] = Label(RELEASE)
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['ready'] = Label("OK")
		self['CHANNELkey'] = Pixmap()
		self['CHANNELtext'] = Label()
		self['BOUQUETkey'] = Pixmap()
		self['BOUQUETtext'] = Label()
		self['INFOkey'] = Pixmap()
		self['INFOtext'] = Label()
		self['MENUkey'] = Pixmap()
		self['MENUtext'] = Label()
		self['button_OK'] = Pixmap()
		self['label_OK'] = Label()
		self['button_TEXT'] = Pixmap()
		self['label_TEXT'] = Label()
		self['button_INFO'] = Pixmap()
		self['label_INFO'] = Label()
		self['button_7_8_9'] = Pixmap()
		self['Line_top'] = Label()
		self['Line_mid'] = Label()
		self['Line_down'] = Label()
		self['label5'] = Label()
		self['bluebutton'] = Label()
		for i in range(6):
			self['pic%s' % i] = Pixmap()
			self['picon%s' % i] = Pixmap()
			self['sender%s' % i] = Label()
			self['sender%s' % i].hide()
			self['pictime%s' % i] = Label()
			self['pictext%s' % i] = Label()
			self['pictext%s_bg' % i] = Label()
			self['pictext%s_bg' % i].hide()
			self['menu%s' % i] = ItemList([])
		self._commonInit()
		self.oldcurrent = 'menu0'
		self.currentsearch = 'menu0'
		self.current = 'menu0'
		self.menu = 'menu0'
		self.hideInfotext()
		self.hideTVinfo()
		self.showMenubar()
		self.setBlueButton('Aus-/Einblenden')
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
		self.service_db = serviceDB(SERVICEFILE)
		if isfile(TIMERFILE):
			self.timer = open(TIMERFILE).read().split('\n')
		else:
			self.timer = ''
		self.date = date.today()
		one_day = timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		self.morgens = False
		self.mittags = False
		self.vorabend = False
		self.abends = True
		self.nachts = False
		if config.plugins.tvspielfilm.primetime.value == 'now':
			self.abends = False
			hour = datetime.now().hour
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
		callInThread(self.threadDownloadPage, self.link, self.localhtml, self.makeTVHeuteView, self.downloadError)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['ready'].hide()
		self['MENUkey'].show()
		self['MENUtext'].show()
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['label_OK'].hide()
		self['label_TEXT'].hide()
		self['label_INFO'].hide()
		self['button_TEXT'].hide()
		self['button_OK'].hide()
		self['button_INFO'].hide()
		self['button_7_8_9'].hide()
		self['Line_top'].hide()
		self['Line_mid'].hide()
		self['Line_down'].show()
		self['seitennr'].hide()
		self['CHANNELkey'].show()
		self['CHANNELtext'].show()
		self['BOUQUETkey'].show()
		self['BOUQUETtext'].show()
		self['INFOkey'].show()
		self['INFOtext'].show()
		self['MENUkey'].show()
		self['MENUtext'].show()
		self['CHANNELtext'].setText('Tag +/-')
		self['BOUQUETtext'].setText('Woche +/-')
		self['INFOtext'].setText('Tageszeit +/-')
		self['MENUtext'].setText('Senderliste')

	def makeTVHeuteView(self):
		output = ensure_str(open(self.localhtml, 'r').read())
		if self.first:
			self.first = False
			startpos = output.find('label="Alle Sender">Alle Sender</option>')
			if self.MeinTVS:
				endpos = output.find('<optgroup label="Hauptsender">')
			else:
				endpos = output.find('<optgroup label="alle Sender alphabetisch">')
			bereich = output[startpos:endpos]
			allsender = findall(r"<option label='(.*?)' value='https", bereich)
			self.maxpages = len(allsender) // 6
			if len(allsender) % 6 != 0:
				self.maxpages += 1
			self['seitennr'].show()
			self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
		self.titel = 'Heute im TV  - %s, %s' % (self.weekday, self.date.strftime('%d.%m.%Y'))
		self.setTitle(self.titel)
		startpostop = output.find('<div class="gallery-area">')
		endpostop = output.find('<div class="info-block">')
		bereichtop = unescape(output[startpostop:endpostop]).replace("&shy;", "-")
		bereichtop = sub(r'<wbr/>', '', bereichtop)
		bereichtop = sub(r'<div class="first-program block-1">\n.*?</div>', '<div class="first-program block-1"><img src="http://a2.tvspielfilm.de/imedia/8461/5218461,qfQElNSTpxAGvxxuSsPkPjQRIrO6vJjPQCu3KaA_RQPfIknB77GUEYh_MB053lNvumg7bMd+vkJk3F+_CzBZSQ==.jpg" width="149" height="99" border="0" /><span class="time"> </span><strong class="title"> </strong></div>', bereichtop)
		picons = findall(r'"sendericon","channel":"(.*?)","broadcastChannelGroup"', bereichtop)
		self.showready()
		self.zaps = [True for _ in range(6)]
		if picons:
			for i in range(6):
				if i < len(picons):
					LOGO = picons[i].lower().replace(' ', '').replace('.', '').replace('ii', '2')
					if LOGO == "nope":
						self.zaps[i] = False
						self['picon%s' % i].hide()
					else:
						png = getPiconname(LOGO, self.service_db.lookup(LOGO))
						if isfile(png):
							self['picon%s' % i].instance.setScale(1)
							self['picon%s' % i].instance.setPixmapFromFile(png)
							self['picon%s' % i].show()
						else:
							self['picon%s' % i].hide()
				else:
					self['picon%s' % i].hide()
		else:
			for i in range(6):
				self['picon%s' % i].hide()
		sender = findall(r' <h3>(.*?)</h3>', bereichtop)
		self.spalten = min(len(sender), 6)  # begrenze auf max 6 Spalten
		self.srefs = [[] for _ in range(6)]
		if sender:
			for i in range(6):
				if i < self.spalten:
					self.srefs[i].append(serviceDB(SERVICEFILE).lookup(transCHANNEL(sender[i])))
					self.srefs[i].append(sender[i])
					self['sender%s' % i].setText(sender[i])
					self['sender%s' % i].show()
				else:
					self['sender%s' % i].hide()
		else:
			for i in range(6):
				self['sender%s' % i].hide()
		pics = findall(r'<img src="(.*?)" alt="(.*?)"', bereichtop)
		idx = 0
		if pics:
			for i, pic in enumerate(pics):
				try:
					picdata, dummy = pic
					if picdata[-4:] == '.jpg':
						picsearch = search(r'https://(.*).jpg', picdata)
						if picsearch is not None:
							picurl = ('https://%s.jpg' % picsearch.group(1)).replace('159', '300')
							callInThread(self.idownload, idx, picurl)
							idx += 1
				except IndexError:
					pass
			for i in range(idx, 6):  # hide column in case column is unused
				self['pic%s' % idx].hide()
				idx += 1
		else:
			for i in range(6):
				self['pic%s' % i].hide()
		pictimes = findall(r'<span class="time">(.*?)</span>', bereichtop)
		if pictimes:
			for i in range(6):
				if i < len(pictimes):
					self['pictime%s' % i].setText(pictimes[i])
					self['pictime%s' % i].show()
				else:
					self['pictime%s' % i].hide()
		else:
			for i in range(6):
				self['pictime%s' % i].hide()
		pictexts = findall(r'<strong class="title">(.*?)</strong>', bereichtop)
		if pictexts:
			for i in range(6):
				if i < len(pictexts):
					self['pictext%s' % i].setText(pictexts[i])
					self['pictext%s' % i].show()
					self['pictext%s_bg' % i].show()
				else:
					self['pictext%s' % i].hide()
					self['pictext%s_bg' % i].hide()
		else:
			for i in range(6):
				self['pictext%s' % i].hide()
				self['pictext%s_bg' % i].hide()
		startpos = 0
		endpos = 0
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
		bereich = unescape(output[startpos:endpos]).replace("&shy;", "-")
		bereich = sub(r'<a href="javascript://".*?\n', '', bereich)
		bereich = sub(r'<a title="Sendung jetzt.*?\n', '', bereich)
		bereich = sub(r'<span class="add-info icon-livetv"></span>', '', bereich)
		bereich = sub(r'<span class="time"></span>', '<td>TIME00:00</span>', bereich)
		bereich = sub(r'<span class="time">', '<td>TIME', bereich)
		bereich = sub(r'<span class="add-info editorial-rating small"></span>', '', bereich)
		bereich = sub(r'<span class="add-info editorial-', '<td>RATING', bereich)
		bereich = sub(r'<span class="add-info ', '<td>LOGO', bereich)
		bereich = sub(r'<a href="http://my', '<td>LINKhttp://www', bereich)
		bereich = sub(r'<a href="http://www', '<td>LINKhttp://www', bereich)
		bereich = sub(r'<a href="https://my', '<td>LINKhttp://www', bereich)
		bereich = sub(r'<a href="https://www', '<td>LINKhttp://www', bereich)
		bereich = sub(r'" target="_self"', '</td>', bereich)
		bereich = sub(r'<strong class="title">', '<td>TITEL', bereich)
		bereich = sub(r'<span class="subtitle">', '<td>SUBTITEL', bereich)
		bereich = sub(r'</strong>', '</td>', bereich)
		bereich = sub(r'">TIPP</span>', '</td>', bereich)
		bereich = sub(r'">LIVE</span>', '</td>', bereich)
		bereich = sub(r'">HDTV</span>', '</td>', bereich)
		bereich = sub(r'">NEU</span>', '</td>', bereich)
		bereich = sub(r'">OMU</span>', '</td>', bereich)
		bereich = sub(r'"></span>', '</td>', bereich)
		bereich = sub(r'</span>', '</td>', bereich)
		bereich = sub(r'<wbr/>', '', bereich)
		bereich = sub(r'<div class="program-block">', '<td>BLOCK</td>', bereich)
		self.tventriess = [[] for _ in range(6)]
		self.tvlinks = [[] for _ in range(6)]
		self.tvtitels = [[] for _ in range(6)]
		menupos = - 1
		menuitems = [[] for _ in range(6)]
		a = findall(r'<td>(.*?)</td>', bereich)
		for x in a:
			if x == 'BLOCK':
				menupos = (menupos + 1) % self.spalten
			else:
				menuitems[menupos].append(x)
		midx = 0
		currentitem = []
		currentlink = 'na'
		currenttitle = ''
		mh = int(86 * SCALE)
		icount = 0
		for mi in menuitems:
			self.menu = 'menu%s' % midx
			for x in mi:
				if search(r'TIME', x):
					x = sub(r'TIME', '', x)
					if not len(currentitem):
						currentitem = [x]
					if currentitem != [x]:
						self.tventriess[midx].append(currentitem)
						self.tvlinks[midx].append(currentlink)
						self.tvtitels[midx].append(currenttitle)
						currentitem = [x]
					currentitem.append(MultiContentEntryText(pos=(0, 2), size=(int(40 * SCALE), int(17 * SCALE)), font=-2, backcolor=13388098, color=16777215, backcolor_sel=13388098, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
					currentlink = 'na'
					currenttitle = ''
					hour = sub(r':..', '', x)
					icount = 0
					if int(hour) < 5:
						one_day = timedelta(days=1)
						datum = "%s%s" % (self.date, one_day)
					else:
						datum = self.date
					timer = "%s:::%s:::%s" % (datum, x, self.srefs[midx][0])
					boxtimers = ''
					for item in self.timer:
						boxtimers += '%s\n' % item   # [:21] + transCHANNEL(ServiceReference(eServiceReference(item[21:].strip())).getServiceName())
					if timer in boxtimers:
						self.rec = True
						png = '%srec.png' % ICONPATH
						if isfile(png):
							currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(0, int((20 + icount * 14) * SCALE)), size=(int(40 * SCALE), int(13 * SCALE)), png=loadPNG(png)))
							icount += 1
				if search(r'LOGO', x):  # NEU
					x = sub(r'LOGO', '', x)
					png = '%s%s.png' % (ICONPATH, x)
					if isfile(png):
						currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(0, int((20 + icount * 14) * SCALE)), size=(int(40 * SCALE), int(13 * SCALE)), png=loadPNG(png)))
						icount += 1
				if search(r'RATING', x):  # DAUMEN
					x = sub(r'RATING', '', x).replace(' ', '-')
					png = '%s%s.png' % (ICONPATH, x)
					if isfile(png):
						currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(int(8 * SCALE), int((20 + icount * 14) * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
				if search(r'LINK', x):
					x = sub(r'LINK', '', x)
					currentlink = x
				if search(r'TITEL', x) and search(r'SUBTITEL', x) is None:
					x = sub(r'TITEL', '', x)
					currenttitle = x
				if search(r'SUBTITEL', x):
					x = sub(r'SUBTITEL', '', x).strip()
					if x != '':
						currenttitle = "%s, %s" % (currenttitle, x)
				if self.rec:
					self.rec = False
				currentitem.append(MultiContentEntryText(pos=(int(45 * SCALE), 0), size=(int(155 * SCALE), mh), font=0, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=currenttitle))
			if currentitem:
				self.tventriess[midx].append(currentitem)
				self.tvlinks[midx].append(currentlink)
				self.tvtitels[midx].append(currenttitle)
			currentitem = []
			midx += 1
		if self.current[-1].isdigit():
			if int(self.current[-1]) > self.spalten - 1:
				self.current = 'menu%s' % (self.spalten - 1)
		for i in range(6):
			self['menu%s' % i].l.setItemHeight(mh)
			self['menu%s' % i].l.setList(self.tventriess[i])
			self['menu%s' % i].moveToIndex(self.oldindex)
			if self.current == 'menu%s' % i:
				for j in range(6):
					self['menu%s' % j].selectionEnabled(1 if i == j else 0)
		self['CHANNELkey'].show()
		self['CHANNELtext'].show()
		self['BOUQUETkey'].show()
		self['BOUQUETtext'].show()
		self['INFOkey'].show()
		self['INFOtext'].show()
		self['MENUkey'].show()
		self['MENUtext'].show()
		self['CHANNELtext'].setText('Tag +/-')
		self['BOUQUETtext'].setText('Woche +/-')
		self['INFOtext'].setText('Tageszeit +/-')
		self['MENUtext'].setText('Senderliste')
		self.ready = True

	def makePostviewPage(self):
		for i in range(6):
			self['sender%s' % i].hide()
			self['picon%s' % i].hide()
			self['pic%s' % i].hide()
			self['pictime%s' % i].hide()
			self['pictext%s' % i].hide()
			self['pictext%s_bg' % i].hide()
			self['menu%s' % i].hide()
		self['MENUkey'].hide()
		self['MENUtext'].hide()
		try:
			self._makePostviewPage()
		except:
			printStackTrace()

	def showready(self):
		self['waiting'].stopBlinking()
		self['waiting'].hide()
		self['ready'].show()
		self.readyTimer = eTimer()
		self.readyTimer.callback.append(self.hideready)
		self.readyTimer.start(1500, False)

	def hideready(self):
		self.readyTimer.stop()
		self['ready'].hide()

	def ok(self):
		self._ok()

	def selectPage(self, action):
		self.oldcurrent = self.current
		if self.ready:
			idx = search(r'\d', self.current)
			if idx is not None:
				idx = int(idx.group(0))
				c = self['menu%s' % idx].getSelectedIndex()
				self.postlink = self.tvlinks[idx][c]
				if c < len(self.postlink) and action == 'ok' and search(r'www.tvspielfilm.de', self.postlink):
					self.current = 'postview'
					callInThread(self.threadDownloadPage, self.postlink, self.localhtml2, self.makePostviewPage, self.downloadError)
			if self.current == 'searchmenu':
				c = self['searchmenu'].getSelectedIndex()
				self.postlink = self.searchlink[c]
				if action == 'ok':
					if search(r'www.tvspielfilm.de', self.postlink):
						self.current = 'postview'
						callInThread(self.threadDownloadPage, self.postlink, self.localhtml2, self.makePostviewPage, self.downloadError)

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
						s1 = sub(r':..', '', start)
						datum = '%sFIN' % self.postdate
						datum = sub(r'..FIN', '', datum)
						datum = "%s%s" % (datum, self.day)
						parts = start.split(':')
						seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
						start = strftime('%H:%M:%S', gmtime(seconds))
						s2 = sub(r':..:..', '', start)
						start = "%s %s" % (self.date, start) if int(s2) > int(s1) else "%s %s" % (datum, start)
						start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
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
								self.EPGtext += '\n\n%s' % short
							if ext:
								self.EPGtext += '\n\n%s' % ext
							if dur:
								self.EPGtext += '\n\n%s' % dur
					except:
						self.EPGText = getEPGText()

				else:
					self.EPGtext = NOEPG
				fill = self.getFill(channel)
				self.EPGtext += '\n%s' % fill
				self['textpage'].setText(self.EPGtext)
			else:
				self.showEPG = False
				self['textpage'].setText(self.POSTtext)
			self['textpage'].show()
		elif self.current != 'postview' and self.ready and not self.search:
			self.oldindex = 0
			self.morgens = False
			self.mittags = False
			self.vorabend = False
			self.abends = False
			self.nachts = False
			if self.abends:
				self.nachts = True
				self.makeTVHeuteView()
			elif self.nachts:
				self.morgens = True
				self.makeTVHeuteView()
			elif self.morgens:
				self.mittags = True
				self.makeTVHeuteView()
			elif self.mittags:
				self.vorabend = True
				self.makeTVHeuteView()
			elif self.vorabend:
				self.abends = True
				self.makeTVHeuteView()

	def red(self):
		if self.current == 'postview' and self.postviewready:
			if self.oldcurrent == 'searchmenu':
				c = self['searchmenu'].getSelectedIndex()
				self.oldsearchindex = c
				c = self['searchmenu'].getSelectedIndex()
				sref = self.searchref[c]
				self.redTimer(False, sref)
			else:
				sref = None
				for i in range(6):
					if self.oldcurrent == 'menu%s' % i and self.zaps[i]:
						c = self['menu%s' % i].getSelectedIndex()
						self.oldindex = c
						sref = self.srefs[i][0]
						self.redTimer(False, sref)
				if not sref:
					self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)
		if self.ready:
			for i in range(6):
				if self.current == 'menu%s' % i:
					c = self['menu%s' % i].getSelectedIndex()
					self.oldindex = c
					self.postlink = self.tvlinks[i][c]
					if search(r'www.tvspielfilm.de', self.postlink):
						self.oldcurrent = self.current
						callInThread(self.threadGetPage, self.postlink, self.makePostTimer, self.downloadError)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			self.postlink = self.searchlink[c]
			if search(r'www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				callInThread(self.threadGetPage, self.postlink, self.makePostTimer, self.downloadError)

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
						titel = self.tvtitels[i][c].split(', ')
						if len(titel) == 1:
							titel = titel[0].split(' ')
							titel = "%s %s" % (titel[0], titel[1]) if titel[0].find(':') > 0 else titel[0]
						elif len(titel) == 2:
							titel = titel[0].rsplit(' ', 1)[0]
						else:
							titel = titel[0]
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
				self['pictext%s_bg' % i].hide()
				self['menu%s' % i].hide()
			self['seitennr'].hide()
			self['MENUkey'].hide()
			self['MENUtext'].hide()
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			search = quote(search).replace('%20', '+')
			searchlink = "%s/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&q=%s" % (self.baseurl, search)
			self.searchcount = 0
			self.makeSearchView(searchlink)

	def pressText(self):
		self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(TVSsearchYouTube, self.name, self.movie)
		elif not self.search and self.ready:
			for i in range(6):
				if self.current == 'menu%s' % i:
					c = self['menu%s' % i].getSelectedIndex()
					try:
						titel = self.tvtitels[i][c]
						self.session.open(TVSsearchYouTube, titel, self.movie)
					except IndexError:
						pass

	def gotoPageMenu(self):
		if self.current != 'postview' and self.ready and not self.search:
			self.session.openWithCallback(self.numberEntered, TVSgotoPageMenu, self.count, self.maxpages)

	def gotoPage(self, number):
		if self.current != 'postview' and self.ready and not self.search:
			self.session.openWithCallback(self.numberEntered, TVSgetNumber, number)
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
				self['seitennr'].show()
				self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
				if search(r'date', self.link):
					self.link = '%sFIN' % self.link
					datum = findall(r'date=(.*?)FIN', self.link)
					self.link = sub(r'page=.*?FIN', '', self.link)
					self.link = "%spage=%s&date=%s" % (self.link, self.count, datum[0])
				else:
					self.link = "%s%s" % (self.link, 'FIN')
					self.link = sub(r'page=.*?FIN', '', self.link)
					self.link = "%spage=%s" % (self.link, self.count)
				self['waiting'].startBlinking()
				self['waiting'].show()
				self.ready = False
				callInThread(self.threadDownloadPage, self.link, self.localhtml, self.makeTVHeuteView, self.downloadError)

	def nextDay(self):
		self.changeday(1)

	def prevDay(self):
		self.changeday(-1)

	def nextWeek(self):
		self.changeday(7)

	def prevWeek(self):
		self.changeday(-7)

	def changeday(self, deltadays):
		if self.current != 'postview' and self.ready and not self.search:
			self.ready = False
			timespan = timedelta(days=deltadays)
			if search(r'date', self.link):
				self.link = '%sFIN' % self.link
				date1 = findall(r'date=(.*?)-..-..FIN', self.link)
				date2 = findall(r'date=....-(.*?)-..FIN', self.link)
				date3 = findall(r'date=....-..-(.*?)FIN', self.link)
				try:
					today = date(int(date1[0]), int(date2[0]), int(date3[0]))
				except IndexError:
					today = date.today()
				self.date = today + timespan
				self.link = "%s%s" % (sub(r'date=(.*?FIN)', 'date=', self.link), self.date)
			else:
				self.date = date.today() + timespan
				self.link = "%s&date=%s" % (self.link, self.date)
			self.nextdate = self.date + timespan
			self.weekday = makeWeekDay(self.date.weekday())
			self.oldindex = 0
			self['waiting'].startBlinking()
			self['waiting'].show()
			callInThread(self.threadDownloadPage, self.link, self.localhtml, self.makeTVHeuteView, self.downloadError)
		elif self.current == 'postview' or self.search:
			servicelist = self.session.instantiateDialog(ChannelSelection)
			self.session.execDialog(servicelist)

	def rightDown(self):
		try:
			for i in range(6):
				if self.current == 'menu%s' % i:
					self['menu%s' % i].selectionEnabled(0)
					self['menu%s' % ((i + 1) % self.spalten)].selectionEnabled(1)
					self.current = 'menu%s' % ((i + 1) % self.spalten)
					break
			if self.current == 'menu0':
				self.count = self.count + 1 if self.count < self.maxpages else 1
				if search(r'date', self.link):
					self.link = '%sFIN' % self.link
					date = findall(r'date=(.*?)FIN', self.link)
					self.link = sub(r'page=.*?FIN', '', self.link)
					self.link = '%spage=%s&date=%s' % (self.link, self.count, date[0])
				else:
					self.link = '%sFIN' % self.link
					self.link = sub(r'page=.*?FIN', '', self.link)
					self.link = '%spage=%s' % (self.link, self.count)
					self['waiting'].startBlinking()
					self['waiting'].show()
				self['seitennr'].show()
				self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
				self.ready = False
				callInThread(self.threadDownloadPage, self.link, self.localhtml, self.makeTVHeuteView, self.downloadError)
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
				if search(r'date', self.link):
					self.link = '%sFIN' % self.link
					date = findall(r'date=(.*?)FIN', self.link)
					self.link = sub(r'page=.*?FIN', '', self.link)
					self.link = '%spage=%s&date=%s' % (self.link, self.count, date[0])
				else:
					self.link = '%sFIN' % self.link
					self.link = sub(r'page=.*?FIN', '', self.link)
					self.link = '%spage=%s' % (self.link, self.count)
					self['waiting'].startBlinking()
					self['waiting'].show()
				self['seitennr'].show()
				self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
				self.ready = False
				callInThread(self.threadDownloadPage, self.link, self.localhtml, self.makeTVHeuteView, self.downloadError)
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

	def idownload(self, idx, link):  # TVheute-PreviewpicsDownload
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		try:
			response = get(link)
			response.close()
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.downloadError(error)
		else:
			with open(self.pics[idx], 'wb') as f:
				f.write(response.content)
			if isfile(self.pics[idx]):
				try:
					self['pic%s' % idx].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
					self['pic%s' % idx].instance.setPixmapFromFile(self.pics[idx])
				except:
					currPic = loadJPG(self.pics[idx])
					self['pic%s' % idx].instance.setScale(1)
					self['pic%s' % idx].instance.setPixmap(currPic)
				self['pic%s' % idx].show()

	def downloadError(self, output):
		self['CHANNELkey'].show()
		self['CHANNELtext'].show()
		self['BOUQUETkey'].show()
		self['BOUQUETtext'].show()
		self['INFOkey'].show()
		self['INFOtext'].show()
		self['MENUkey'].show()
		self['MENUtext'].show()
		self['CHANNELtext'].setText('Tag +/-')
		self['BOUQUETtext'].setText('Woche +/-')
		self['INFOtext'].setText('Tageszeit +/-')
		self['MENUtext'].setText('Senderliste')
		self.ready = True
		TVSlog("Downloaderror in module 'TVSHeuteView:downloadError':", output)
		self.showDownloadError(output)

	def showProgrammPage(self):
		self['label2'].setText('Timer')
		self['label2'].show()
		self['label3'].setText('Suche')
		self['label3'].show()
		self['label4'].setText('Zappen')
		self['label4'].show()
		self['label6'].setText('MENU')
		self['label6'].show()
		self.hideInfotext()
		self['textpage'].hide()
		self['picpost'].hide()
		self['piclabel'].hide()
		self['piclabel2'].hide()
		self.hideTVinfo()
		for i in range(6):
			self['sender%s' % i].show()
			self['picon%s' % i].show()
			self['pic%s' % i].show()
			self['pictime%s' % i].show()
			self['pictext%s' % i].show()
			self['pictext%s_bg' % i].show()
			self['menu%s' % i].show()

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if sub(r'[0-9]', '', self.current) == "menu":
			self.close()
		elif self.current == 'searchmenu':
			self.search = False
			self.oldsearchindex = 1
			self['searchmenu'].hide()
			self['searchtext'].hide()
			self.setTitle(self.titel)
			self.current = self.currentsearch
			self.showProgrammPage()
		elif self.current == 'postview' and not self.search:
			self.showMenubar()
			self['MENUkey'].show()
			self['MENUtext'].show()
			self.hideRatingInfos()
			self.postviewready = False
			self.setTitle(self.titel)
			self.current = self.oldcurrent
			self.showProgrammPage()
			self['label_OK'].hide()
			self['label_TEXT'].hide()
			self['button_7_8_9'].hide()
			self['button_OK'].hide()
			self['button_INFO'].hide()
			self['button_7_8_9'].hide()
			self['Line_top'].hide()
			self['Line_mid'].hide()
			self['Line_down'].show()
		elif self.current == 'postview' and self.search:
			self.hideRatingInfos()
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


def main(session, **kwargs):
	session.open(TVSMain)


def checkChannels(session, screen, link=None):
	def openScreen(retval=None):
		if link:
			session.open(screen, llink)
		else:
			channel_db = channelDB(SERVICEFILE, DUPESFILE)
			sref = ServiceReference(session.nav.getCurrentlyPlayingServiceReference())
			sref = '%sFIN' % sref
			sref = sub(r':0:0:0:.*?FIN', ':0:0:0:', sref)
			channel = channel_db.lookup(sref)
			if channel == "nope":
				session.open(MessageBox, 'Service nicht gefunden:\nKein Eintrag für aktuelle Servicereferenz\n%s' % sref, MessageBox.TYPE_INFO, close_on_any_key=True)
			else:
				session.open(screen, 'https://www.tvspielfilm.de/tv-programm/sendungen/&page=0,%s.html' % channel, True, False)
	llink = link
	if isfile(SERVICEFILE):
		openScreen()
	else:
		session.openWithCallback(openScreen, TVSmakeServiceFile)


def mainjetzt(session, **kwargs):
	checkChannels(session, TVSJetztView, 'https://www.tvspielfilm.de/tv-programm/sendungen/jetzt.html')


def mainprime(session, **kwargs):
	checkChannels(session, TVSJetztView, 'https://www.tvspielfilm.de/tv-programm/sendungen/abends.html')


def mainlate(session, **kwargs):
	checkChannels(session, TVSJetztView, 'https://www.tvspielfilm.de/tv-programm/sendungen/fernsehprogramm-nachts.html')


def mainevent(session, **kwargs):
	checkChannels(session, TVSProgrammView)


def Plugins(**kwargs):
	return [PluginDescriptor(name='TV Spielfilm', description='TV Spielfilm', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='./pics/FHD/logos/TVmain.png', fnc=main),
			PluginDescriptor(name='TV Spielfilm 20:15', description='TV Spielfilm Prime Time', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='./pics/FHD/logos/TV2015.png', fnc=mainprime),
			PluginDescriptor(name='TV Spielfilm 22:00', description='TV Spielfilm LateNight', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='./pics/FHD/logos/TVlate.png', fnc=mainlate),
			PluginDescriptor(name='TV Spielfilm Jetzt', description='TV Spielfilm Jetzt im TV', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='./pics/FHD/logos/TVjetzt.png', fnc=mainjetzt),
			PluginDescriptor(name='TV Spielfilm EventView', description='TV Spielfilm EventView', where=[PluginDescriptor.WHERE_EVENTINFO], icon='./pics/FHD/logos/TVevent.png', fnc=mainevent)]

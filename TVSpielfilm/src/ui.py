# -*- coding: utf-8 -*-
from __future__ import print_function
import datetime
import requests
from json import loads
from socket import error as socketerror
from base64 import b64encode, b64decode
from RecordTimer import RecordTimerEntry
from time import mktime, strftime, gmtime, localtime
from os import remove, linesep, rename
from os.path import isfile
from re import findall, match, search, split, sub, S, compile
from Tools.Directories import isPluginInstalled
from twisted.internet import reactor
from six import PY2, ensure_binary, ensure_str
from six.moves.http_client import HTTPException
from six.moves.urllib.error import URLError, HTTPError
from six.moves.urllib.parse import unquote_plus, quote, urlencode, parse_qs
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
from .util import applySkinVars, PLUGINPATH, PICPATH, ICONPATH, serviceDB, BlinkingLabel, ItemList, makeWeekDay, printStackTrace, channelDB, readSkin, DESKTOP_WIDTH, DESKTOP_HEIGHT, SCALE
from .parser import transCHANNEL, shortenChannel, transHTML, cleanHTML, parsedetail, fiximgLink, parsePrimeTimeTable, parseTrailerUrl, buildTVTippsArray, parseNow, NEXTPage1, NEXTPage2

try:
	from cookielib import MozillaCookieJar
except Exception:
	from http.cookiejar import MozillaCookieJar

RELEASE = 'V6.8'
NOTIMER = '\nTimer nicht möglich:\nKeine Service Reference vorhanden, der ausgewählte Sender wurde nicht importiert.'
NOEPG = 'Keine EPG Informationen verfügbar'
ALPHA = '/proc/stb/video/alpha' if isfile('/proc/stb/video/alpha') else None


def findPicon(sref, folder):
	sref = sref + 'FIN'
	sref = sref.replace(':', '_')
	sref = sref.replace('_FIN', '')
	sref = sref.replace('FIN', '')
	pngname = folder + sref + '.png'
	if isfile(pngname):
		return pngname


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
		dic['selbg'] = str(config.plugins.tvspielfilm.selectorcolor.value)
		if skin:
			self.skin = applySkinVars(skin, dic)
		Screen.__init__(self, session)
		self.fontlarge = True if config.plugins.tvspielfilm.font_size.value == 'large' else False
		self.fontsmall = True if config.plugins.tvspielfilm.font_size.value == 'small' else False
		self.baseurl = 'https://www.tvspielfilm.de'
		self.servicefile = PLUGINPATH + 'db/service.references'

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def download(self, link, name):
		reactor.callInThread(self._download, link, name)

	def _download(self, link, name):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.downloadError(error)
		else:
			name(response.content)

	def downloadError(self, output):
		TVSlog(output)
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Download Fehler:\n%s' % error, MessageBox.TYPE_ERROR)
		except AttributeError:
			self.session.open(MessageBox, 'Download Fehler:\n%s' % output, MessageBox.TYPE_ERROR)

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
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PLUGINPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
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
		if isfile(self.pics[idx]):
			self['pic%s' % idx].instance.setPixmapFromFile(self.pic[idx])

	def GetPics(self, picurllist, offset, show=True, playshow=False):
		for i in range(6):
			try:
				picurl = picurllist[offset + i]
				self.picdownload(picurl, i)
				if show:
					self['pic%s' % i].show()
				if playshow:
					self['play%s' % i].show()
			except IndexError:
				if playshow:
					self['play%s' % i].hide()
				if show:
					self['pic%s' % i].hide()

	def picdownload(self, link, idx):
		reactor.callInThread(self._picdownload, link, idx)

	def _picdownload(self, link, idx):
		try:
			response = requests.get(link)
			response.raise_for_status()
			self.getPics(response.content, idx)
		except OSError as err:
			self.picdownloadError(err)

	def picdownloadError(self, output):
		TVSlog(output)

	def getPNG(self, x, Pos):
		png = '%s%s.png' % (ICONPATH, x)
		if isfile(png):
			return MultiContentEntryPixmapAlphaTest(pos=(Pos, 20), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png))
		else:
			if isfile(png):
				return MultiContentEntryPixmapAlphaTest(pos=(Pos, 10), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png))
		return None

	def infotextStartEnd(self, infotext):
		part = infotext[1].strip()
		if infotext[0].strip() == 'Heute':
			d = sub('....-', '', str(self.date))
			d2 = sub('-..', '', d)
			d3 = sub('..-', '', d)
			part = 'he ' + d3 + '.' + d2 + '.'
		day = sub('.. ', '', part)
		self.day = sub('[.]..[.]', '', day)
		month = sub('.. ..[.]', '', part)
		month = sub('[.]', '', month)
		date = str(self.date) + 'FIN'
		year = sub('......FIN', '', date)
		self.postdate = year + '-' + month + '-' + self.day
		today = datetime.date(int(year), int(month), int(self.day))
		one_day = datetime.timedelta(days=1)
		self.nextdate = today + one_day
		part = infotext[1].split(' - ')
		self.start = part[0].replace(' Uhr', '').strip()
		self.end = part[1].replace(' Uhr', '').strip()

	def showInfotext(self, infotext):
		try:
			for i, pi in enumerate(infotext):
				if i < 9:
					self['infotext%s' % i].setText(pi)
					self['infotext%s' % i].show()
		except IndexError:
			self['infotext%s' % i].hide()

	def showRatinginfos(self, output):
		startpos = output.find('<section class="broadcast-detail__rating">')
		endpos = output.find('<section class="broadcast-detail__description">')
		bereich = output[startpos:endpos]
		bereich = cleanHTML(bereich)
		ratinglabels = findall('<span class="rating-dots__label">(.*?)</span>', bereich)
		ratingdots = findall('data-rating="(.*?)"><i></i></span>', bereich)
		for i, ri in enumerate(ratinglabels):
			if len(ratingdots) <= i:
				ratingdots.append('0')
			ratingfile = ICONPATH + 'starbar%s.png' % ratingdots[i]
			if isfile(ratingfile):
				try:
					self['ratinglabel%s' % i].setText(ri)
					self['ratinglabel%s' % i].show()
					self['ratingdot%s' % i].instance.setPixmapFromFile(ratingfile)
					self['ratingdot%s' % i].show()
				except IndexError:
					pass
		starslabel = findall('<span class="rating-stars__label">(.*?)</span>', bereich)
		starsrating = findall('<span class="rating-stars__rating" data-rating="(.*?)"></span>', bereich)
		if len(starsrating) > 0:
			starsfile = ICONPATH + 'starbar%s.png' % starsrating[0]
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

	def _shortdesc(self, bereich):
		name = findall('<h1 class="headline headline--article broadcast">(.*?)</h1>', bereich)
		try:
			self.name = name[0]
		except IndexError:
			name = findall('headline headline--article broadcast">(.*?)</h1>', bereich)
			try:
				self.name = name[0]
			except IndexError:
				self.name = ''
		startpos = bereich.find('<h1 class="headline headline--article broadcast">')
		endpos = bereich.find('<section class="broadcast-detail__stage')
		bereich = bereich[startpos:endpos]
		shortdesc = findall('<span class="text-row">(.*?)</span>', bereich)[-1]
		if shortdesc:
			self.shortdesc = shortdesc
		else:
			self.shortdesc = ''

	def makePostTimer(self, output):
		output = ensure_str(output)
		startpos = output.find('<div class="content-area">')
		endpos = output.find('<h2 class="broadcast-info">')
		if endpos == -1:
			endpos = output.find('>Weitere Bildergalerien<') # unnötig?
			if endpos == -1:
				endpos = output.find('<div class="OUTBRAIN"') # unnötig?
				if endpos == -1:
					endpos = output.find('</footer>') # unnötig?
		bereich = transHTML(output[startpos:endpos])
		infotext = self.getInfotext(bereich)
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

	def _makePostviewPage(self, string):
		output = ensure_str(open(self.localhtml2, 'r').read())
		self['label2'].setText('Timer')
		self['label2'].show()
		self['label3'].setText('YouTube Trailer')
		self['label3'].show()
		self['label4'].hide()  # = Wikipedia
		self['label6'].hide()
		self.setBlueButton('Aus-/Einblenden')
		self.hideMenubar()
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
		self.hideMenubar()
		if search('<div class="film-gallery">', output):
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
		self.showRatinginfos(output)
		self._shortdesc(bereich)

# Infoausgabe: NEU, TIPP, LIVE
		tvinfo = []
		sref = self.service_db.lookup(infotext[2].lower())
		timer = self.postdate + ':::' + self.start + ':::' + str(sref)
		if timer in self.timer:
			tvinfo.append('REC')
		info = findall('<span class="add-info icon-new nodistance">(.*?)</span>', bereich)
		if len(info):
			tvinfo.append(info[0])
		info = findall('<span class="add-info icon-tip nodistance">(.*?)</span>', bereich)
		if len(info):
			tvinfo.append(info[0])
		info = findall('<span class="add-info icon-live nodistance">(.*?)</span>', bereich)
		if len(info):
			tvinfo.append(info[0])
		for i, ti in enumerate(tvinfo):
			self['tvinfo%s' % i].setText(ti)
			self['tvinfo%s' % i].show()
		if self.tagestipp:
			channel = findall("var adsc_sender = '(.*?)'", output)
			if len(channel) > 0:
				self.sref = self.service_db.lookup(channel[0])
				if self.sref != 'nope':
					self.zap = True
		picons = findall('<img src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*?).png.*?', bereich)
		picon = PLUGINPATH + 'picons/' + picons[0] + '.png'
		if isfile(picon):
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

	def getInfotext(self, bereich):
# weitere Sendungsinformationen
		startpos = bereich.find('<div class="text-wrapper">')
		endpos = bereich.find('<section class="broadcast-detail__stage')
		extract = bereich[startpos:endpos]
		text = findall('span\ class="text\-row">(.*?)</span>', extract, S) # Suchstring voher mit re.escape wandeln
# Sendezeit & Sender
		startpos = bereich.find('<div class="schedule-widget__header__attributes">')
		if startpos > 0:
			endpos = bereich.find('<div class="schedule-widget__tabs">')
			extract = bereich[startpos:endpos]
			infotext = findall('<li>(.*?)</li>', extract)
			infotext.extend(text[1].strip().split(' | '))
			self.start = infotext[1]
		else: # manche Sendungen (z.B. Tagesschau) benötigen eine andere Auswertung
			channel = findall("data-tracking-point='(.*?)'", bereich)
			if len(text) > 0:
				infotext = text[0].strip().split(' | ')
				infotext[2] = loads(channel[0])['channel']
				infotext.extend(text[1].strip().split(' | '))
				self.start = infotext[1][0:5]
			else:
				self.start = ''
		if len(text) > 2:
			for pi in text[2].split(', '):
				if pi.find('(') > 0:
					part = pi
				elif pi.find(')') > 0:
					infotext.append(part + ', ' + pi)
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
		self['label2'].hide()
		self['label3'].hide()
		self['label4'].hide()
		self['label5'].hide()
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
		link = sub('.*?data-src="', '', link)
		reactor.callInThread(self._downloadPicPost, link, label)

	def _downloadPicPost(self, link, label):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
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
				self.session.openWithCallback(self.IMDbInstall, MessageBox, '\nDas IMDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)

	def TMDb(self):
		if self.current == 'postview':
			if isPluginInstalled('tmdb'):
				from Plugins.Extensions.tmdb.tmdb import tmdbScreen
				self.session.open(tmdbScreen, self.name, 2)
			else:
				self.session.openWithCallback(self.TMDbInstall, MessageBox, '\nDas TMDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)

	def TVDb(self):
		if self.current == 'postview':
			if isPluginInstalled('TheTVDB'):
				from Plugins.Extensions.TheTVDB.plugin import TheTVDBMain
				self.name = sub('Die ', '', self.name)
				self.session.open(TheTVDBMain, self.name)
			else:
				self.session.openWithCallback(self.TVDbInstall, MessageBox, '\nDas TheTVDb Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden automatisch installiert werden?', MessageBox.TYPE_YESNO)

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

	def redTimer(self, searching=False, sref=None):
		if sref == None:
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
		name = self.name
		shortdesc = self.shortdesc
		if shortdesc != '' and search('Staffel [0-9]+, Episode [0-9]+', shortdesc):
			episode = search('(Staffel [0-9]+, Episode [0-9]+)', shortdesc)
			episode = sub('Staffel ', 'S', episode.group(1))
			episode = sub(', Episode ', 'E', episode)
			name = name + ' ' + episode
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

	def initBlueButton(self, text):
		self['bluebutton'] = Label()
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
			self['label5'].show()
		else:
			self['bluebutton'].hide()
			self['label5'].hide()

	def _commonInit(self, ltxt='Suche', lltxt='Zappen'):
		self['picpost'] = Pixmap()
		for i in range(5):
			self['tvinfo%s' % i] = Label('')
		self['picon'] = Pixmap()
		self['playlogo'] = Pixmap()
		self['searchtext'] = Label('')
		for i in range(9):
			self['infotext%s' % i] = Label('')
		for i in range(5):
			self['ratinglabel%s' % i] = Label('')
			self['ratingdot%s' % i] = Pixmap()
		self['starslabel'] = Label('')
		self['starsrating'] = Pixmap()
		self['searchmenu'] = ItemList([])
		self['textpage'] = ScrollLabel('')
		self['piclabel'] = Label('')
		self['piclabel'].hide()
		self['piclabel2'] = Label('')
		self['piclabel2'].hide()
		self['release'] = Label(RELEASE)
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['seitennr'] = Label('')
		self['label2'] = Label('Timer')
		self['label3'] = Label(ltxt)
		self['label4'] = Label(lltxt)
		self['label6'] = Label('MENU')
		self.initBlueButton('Aus-/Einblenden')

	def _makeSearchView(self, url, titlemode=0, searchmode=0):
		self.hideMenubar()
		header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
				  'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
				  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
				  'Accept-Language': 'en-us,en;q=0.5'}
		searchrequest = Request(url, None, header)
		output = ensure_str(urlopen(searchrequest, timeout=5).read())
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
		mh = int(47 * SCALE + 0.5)
		for DATUM, START, TITLE, GENRE, INFOS, LOGO, LINK, RATING in items:
			if DATUM:
				self.datum_string = DATUM
				res_datum = [DATUM]
				res_datum.append(MultiContentEntryText(pos=(int(3 * SCALE), int(2 * SCALE)), size=(int(120 * SCALE), mh), font=2, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=DATUM))
				self.searchref.append('na')
				self.searchlink.append('na')
				self.searchentries.append(res_datum)
				self.filter = True
				continue
			res = [LOGO]
			start = START
			res.append(MultiContentEntryText(pos=(int(70 * SCALE), 0), size=(int(110 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=START))
			res.append(MultiContentEntryText(pos=(int(190 * SCALE), 0), size=(int(840 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=TITLE))
			if LOGO:
				service = LOGO
				sref = self.service_db.lookup(service)
				if sref == 'nope':
					self.filter = True
				else:
					self.filter = False
					self.searchref.append(sref)
					if config.plugins.tvspielfilm.picon.value == "plugin":
						png = self.piconfolder + '%s.png' % LOGO
					else:
						png = findPicon(sref, self.piconfolder)
					if png:
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
					else:
						res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
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
						png = ICONPATH + 'rec.png'
						if isfile(png):
							res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), int(16 * SCALE)), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
					self.searchlink.append(LINK)
					if GENRE:
						res.append(MultiContentEntryText(pos=(int(940 * SCALE), 0), size=(int(220 * SCALE), mh), font=-2, color_sel=16777215, flags=RT_HALIGN_RIGHT | RT_VALIGN_CENTER | RT_WRAP, text=GENRE))
					self.datum = False
					self.rec = False
					if RATING: # DAUMEN
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
		if searchmode == 1:
			searchtext1 = '<a class="next" href=".*?"'
			searchtext2 = '<a class="next" href="(.*?)"'
		else:
			searchtext1 = NEXTPage1
			searchtext2 = NEXTPage2
		if self.searchcount <= int(self.maxsearchcount) and search(searchtext1, bereich):
			nextpage = search(searchtext2, bereich)
			if nextpage:
				self._makeSearchView(nextpage.group(1))
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
				self.session.openWithCallback(self.picReturn, TVPicShow, self.postlink)
			else:
				self.session.openWithCallback(self.showPicPost, FullScreen)
		elif self.current == 'postview' and not self.postviewready:
			pass
		else:
			self.selectPage('ok')
		if self.current == 'searchmenu':
			self.selectPage('ok')

	def downloadPostPage(self, link, name):
		reactor.callInThread(self._downloadPostPage, link, name)

	def _downloadPostPage(self, link, name):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.downloadError(error)
		else:
			with open(self.localhtml2, 'wb') as f:
				f.write(response.content)
			name(response.content)

	def downloadFullPage(self, link, name):
		reactor.callInThread(self._downloadFullPage, link, name)

	def _downloadFullPage(self, link, name):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.downloadPageError(error)
		else:
			with open(self.localhtml, 'wb') as f:
				f.write(response.content)
			name(response.content)

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
		self.service_db = serviceDB(self.servicefile)
		if isfile(PLUGINPATH + 'db/timer.db'):
			self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		else:
			self.timer = ''
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		self.makeTVTimer = eTimer()
		self.makeTVTimer.callback.append(self.downloadFullPage(link, self.makeTVTipps))
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PLUGINPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		self.makeTVTimer.start(200, True)

	def makeTVTipps(self, string):
		output = ensure_str(open(self.localhtml, 'r').read())
		self.sref = []
		self['release'].show()
		self['waiting'].stopBlinking()
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
		mh = int(47 * SCALE + 0.5)
		for LINK, PIC, TIME, INFOS, NAME, GENRE, LOGO in items:
			sref = None
			self.new = False
			if LINK:
				res = [LINK]
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
				png = '%s%s.png' % (ICONPATH, INFO)
				if isfile(png): # NEU, TIPP
					yoffset = int((mh - 14 * SCALE * len(INFOS)) / 2 + 14 * SCALE * icount)
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), yoffset), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
					icount += 1
			if NAME:
				titelfilter = NAME
				res.append(MultiContentEntryText(pos=(int(160 * SCALE), 0), size=(int(580 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=NAME))
			if GENRE:
				text = GENRE.replace(',', '\n', 1)
				res.append(MultiContentEntryText(pos=(int(1040 * SCALE), 0), size=(int(400 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT | RT_VALIGN_CENTER | RT_WRAP, text=text))
				if self.sparte == 'Spielfilm':
					png = ICONPATH + 'rating-small1.png'
					if isfile(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1220 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
			if LOGO:
				service = LOGO
				sref = self.service_db.lookup(service)
				if config.plugins.tvspielfilm.picon.value == "plugin":
					png = self.piconfolder + '%s.png' % LOGO
				else:
					png = findPicon(sref, self.piconfolder)
				if png:
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), 0), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
				else:
					res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(2 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
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
						png = ICONPATH + 'rec.png'
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

	def makePostviewPage(self, string):
		self['menu'].hide()
		for i in range(6):
			self['pic%s' % i].hide()
		self._makePostviewPage(string)

	def makeSearchView(self, url):
		self._makeSearchView(url, 0, 1)

	def ok(self):
		self._ok()

	def selectPage(self, action):
		if self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.postlink = self.tvlink[c]
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.postlink = self.searchlink[c]
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
		if search('www.tvspielfilm.de', self.postlink):
			self.oldcurrent = self.current
			self.download(self.postlink, self.makePostTimer)

	def red(self):
		if self.current == 'postview' and self.postviewready:
			self.redTimer(self.search != None)
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
				titel = self.tvtitel[c]
				titel = titel.split(', ')
				if len(titel) == 1:
					titel = titel[0].split(' ')
					titel = titel[0] + ' ' + titel[1] if titel[0].find(':') > 0 else titel[0]
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
			self['label2'].hide()
			self['label3'].hide()
			self['label4'].hide()
			self['label5'].hide()
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = quote(search).replace('%20', '+')
			searchlink = self.baseurl + '/suche/?q=%s&tab=TV-Sendungen?page=1' % search
			self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
			self.searchcount = 0
			self._makeSearchView(searchlink)

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

	def downloadPageError(self, output):
		TVSlog(output)
		self['CHANNELkey'].show()
		self['BOUQUETkey'].show()
		self['INFOkey'].show()
		self['MENUkey'].hide()
		self['TEXTkey'].hide()
		if self.sparte == 'neu':
			self['INFOkey'].hide()
		self['label'].show()
		self.ready = True

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['release'].hide()
		self['waiting'].startBlinking()
		self['waiting'].show()
		self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVTipps))

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
			self.hideRatingInfos()
			self.postviewready = False
			self.setTitle('')
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
		self.date = datetime.date.today()
		self['menu'] = ItemList([])
		self['release'] = Label(RELEASE)
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['seitennr'] = Label('')
		self['CHANNELkey'] = Pixmap()
		self['CHANNELtext'] = Label('')
		self['BOUQUETkey'] = Pixmap()
		self['BOUQUETtext'] = Label('')
		self['INFOkey'] = Pixmap()
		self['INFOtext'] = Label('')
		self['TEXTkey'] = Pixmap()
		self['TEXTtext'] = Label('')
		self['button_OK'] = Pixmap()
		self['label_OK'] = Label('')
		self['button_TEXT'] = Pixmap()
		self['label_TEXT'] = Label('')
		self['button_INFO'] = Pixmap()
		self['label_INFO'] = Label('')
		self['1_zapup'] = Pixmap()
		self['2_zapdown'] = Pixmap()
		self['button_7_8_9'] = Pixmap()
		self['Line_top'] = Label('')
		self['Line_mid'] = Label('')
		self['Line_down'] = Label('')
		self['button_OK'] = Pixmap()
		self['button_TEXT'] = Pixmap()
		self['button_INFO'] = Pixmap()
		self['CHANNELtext'] = Label('')
		self['BOUQUETtext'] = Label('')
		self.initBlueButton('Aus-/Einblenden')


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
		self._commonInit(' Filter')
		self.hideInfotext()
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
		if isfile(PLUGINPATH + 'db/timer.db'):
			self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		else:
			self.timer = ''
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PLUGINPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		self.makeTVTimer = eTimer()
		self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVGenreView))
		self.makeTVTimer.start(200, True)

	def makeTVGenreView(self, output):
		output = ensure_str(output)
		self.titel = ' %s - Sendungen der nächsten 14 Tage' % self.genre
		self.setTitle(self.titel)
		self['release'].show()
		self['waiting'].stopBlinking()
		items, bereich = parsePrimeTimeTable(output)
		res = [items]
		mh = int(47 * SCALE + 0.5)
		for DATUM, START, TITLE, GENRE, INFOS, LOGO, LINK, RATING in items:
			if DATUM:
				self.datum_string = DATUM
				res_datum = [DATUM]
				res_datum.append(MultiContentEntryText(pos=(int(85 * SCALE), 0), size=(int(500 * SCALE), mh), font=2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=DATUM))
				self.sref.append('na')
				self.tvlink.append('na')
				self.tvtitel.append('na')
				self.tventries.append(res_datum)
				self.filter = True
				continue
			res = [LOGO]
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
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), 0), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
					else:
						res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(30 * (SCALE - 1))), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
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
						png = ICONPATH + 'rec.png'
						if isfile(png):
							res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1170 * SCALE), int(7 * SCALE)), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
					self.tvlink.append(LINK)
					self.tvtitel.append(TITLE)
					if GENRE:
						titelfilter = TITLE.replace(GENRE, '')
						text = GENRE.replace(',', '\n', 1)
						res.append(MultiContentEntryText(pos=(int(1040 * SCALE), 0), size=(int(400 * SCALE), mh), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_RIGHT | RT_VALIGN_CENTER | RT_WRAP, text=text))
					icount = 0
					for INFO in INFOS:
						if self.rec:
							self.rec = False
						else:
							png = '%s%s.png' % (ICONPATH, INFO)
							if isfile(png): # DAUMEN
								yoffset = int(icount * 21 + (3 - len(INFOS)) * 10 + int(30 * (SCALE - 1)))
								res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1220 * SCALE), yoffset), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
								icount += 1
					self.datum = False
					if RATING:
						if RATING != 'rating small':
							RATING = RATING.replace(' ', '-')
							png = '%s%s.png' % (ICONPATH, RATING)
							if isfile(png):
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
			self['CHANNELkey'].hide()
			self['BOUQUETkey'].hide()
			self['INFOkey'].hide()
			self['MENUkey'].hide()
			self['TEXTkey'].hide()
			self['OKkey'].show()
			self['OKtext'].setText('Sendung')
			self['OKtext'].show()
			self['STOPtext'].setText('YouTube Trailer')
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
			self.postlink = self.tvlink[c]

		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.postlink = self.searchlink[c]
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
			self.redTimer(self.search != None)
		elif self.current == 'menu' and self.ready:
			c = self['menu'].getSelectedIndex()
			self.oldindex = c
			self.postlink = self.tvlink[c]
			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			self.postlink = self.searchlink[c]
			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)

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
			self['label2'].hide()
			self['label3'].hide()
			self['label4'].hide()
			self['label5'].hide()
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = quote(search).replace('%20', '+')
			searchlink = self.baseurl + '/suche/?q=%s&tab=TV-Sendungen?page=1' % search
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
			titel = self.tvtitel[c]
			if titel != 'na':
				self.session.open(searchYouTube, titel, self.movie)

	def gotoEnd(self):
		if self.current != 'postview' and self.ready and not self.search:
			end = len(self.tventries) - 1
			self['menu'].moveToIndex(end)
		elif self.current != 'postview' and self.ready and self.search:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)

	def downloadFull(self, link, name):
		reactor.callInThread(self._downloadFull, link, name)

	def _downloadFull(self, link, name):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.downloadFullError(error)
		else:
			with open(self.localhtml2, 'wb') as f:
				f.write(response.content)
			name(response.content)

	def downloadFullError(self, output):
		TVSlog(output)
		self['CHANNELkey'].hide()
		self['BOUQUETkey'].hide()
		self['INFOkey'].hide()
		self['MENUkey'].hide()
		self['TEXTkey'].hide()
		self['OKtext'].setText('Sendung')
		self['OKtext'].show()
		self['STOPtext'].setText('YouTube Trailer')
		self['menu'].moveToIndex(self.oldindex)
		self.load = False
		self.ready = True

	def downloadPageError(self, output):
		TVSlog(output)
		self['CHANNELkey'].hide()
		self['BOUQUETkey'].hide()
		self['INFOkey'].hide()
		self['MENUkey'].hide()
		self['TEXTkey'].hide()
		self['OKtext'].setText('Sendung')
		self['OKtext'].show()
		self['STOPtext'].setText('YouTube Trailer')
		self.ready = True

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.datum = False
		self.filter = True
		self.current = 'menu'
		self['release'].hide()
		self['waiting'].startBlinking()
		self['waiting'].show()
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.sref = []
		self.genrecount = 0
		self.makeTVTimer.callback.append(self.downloadFull(self.link, self.makeTVGenreView))

	def showProgrammPage(self):
		self['CHANNELkey'].hide()
		self['BOUQUETkey'].hide()
		self['INFOkey'].hide()
		self['MENUkey'].hide()
		self['TEXTkey'].hide()
		self['OKtext'].setText('Sendung')
		self['OKtext'].show()
		self['STOPtext'].setText('YouTube Trailer')
		self['label2'].setText('Timer')
		self['label2'].show()
		self['label3'].setText('Filter')
		self['label3'].show()
		self['label4'].setText('Zappen')
		self['label3'].show()
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

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.load:
			self.session.openWithCallback(self.stopLoad, MessageBox, '\nDie Suche ist noch nicht beendet. Soll die Suche abgebrochen und das Ergebnis angezeigt werden?', MessageBox.TYPE_YESNO)
		elif self.current == 'menu' and not self.search:
			if isfile(self.picfile):
				remove(self.picfile)
			if isfile(self.localhtml):
				remove(self.localhtml)
			if isfile(self.localhtml2):
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
			self['OKtext'].hide()
			self['TEXTtext'].hide()
			self['button_OK'].hide()
			self['button_TEXT'].hide()
			self['button_INFO'].hide()
			self['button_7_8_9'].hide()

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
			if isfile(PLUGINPATH + 'db/timer.db'):
				self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
			else:
				self.timer = ''
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PLUGINPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		if search('/sendungen/jetzt.html', link):
			self.jetzt = True
		elif search('time=shortly', link):
			self.gleich = True
		elif search('/sendungen/abends.html', link):
			self.abends = True
		elif search('/sendungen/fernsehprogramm-nachts.html', link):
			self.nachts = True
		self.makeTVTimer = eTimer()
		self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self['INFOkey'].show()
		self['INFOtext'].hide()
		self['TEXTkey'].show()
		self['TEXTtext'].setText('Sender')
		self['TEXTtext'].show()
		self['INFOtext'].setText('Jetzt/Gleich im TV')
		self['INFOtext'].show()
		self['seitennr'].hide()
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
		mh = int(47 * SCALE + 0.5)
		for LOGO, TIME, LINK, title, sparte, genre, RATING, trailer in items:
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
				if config.plugins.tvspielfilm.picon.value == "plugin":
					png = self.piconfolder + '%s.png' % LOGO
				else:
					png = findPicon(sref, self.piconfolder)
				if png:
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
				else:
					res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(4 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
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
				res_link = []
				res_link.append(service)
				res_link.append(LINK)
				self.tvlink.append(res_link)
				if title:
					if self.showgenre and genre:
						x = title + ", " + genre
					else:
						x = title
					res_titel = []
					res_titel.append(service)
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
					png = ICONPATH + 'rec.png'
					ypos = int(24 * SCALE) if sparte else int(16 * SCALE)
					if isfile(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1160 * SCALE), ypos), size=(int(40 * SCALE), int(14 * SCALE)), png=loadPNG(png)))
				if sparte:
					if self.rec:
						ypos = 4
						ysize = int(20 * SCALE)
						valign = RT_HALIGN_RIGHT
					else:
						ypos = 0
						ysize = mh
						valign = RT_HALIGN_RIGHT | RT_VALIGN_CENTER
					res.append(MultiContentEntryText(pos=(int(1080 * SCALE), ypos), size=(int(120 * SCALE), ysize), font=-2, color=10857646, color_sel=16777215, flags=valign, text=sparte))
				self.rec = False
				if RATING != 'rating small':
					RATING = RATING.replace(' ', '-')
					png = '%s%s.png' % (ICONPATH, RATING)
					if isfile(png): # DAUMEN
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1220 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
				if trailer:
					png = ICONPATH + 'trailer.png'
					if isfile(png):
						res.append(MultiContentEntryPixmapAlphaTest(pos=(int(180 * SCALE), int(8 * SCALE)), size=(int(30 * SCALE), int(30 * SCALE)), png=loadPNG(png)))
				self.tventries.append(res)
		order = eval(self.order.replace('&', ''))
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
				self['CHANNELkey'].hide()
				self['BOUQUETkey'].hide()
				self['INFOkey'].hide()
				self['TEXTkey'].show()
				self['INFOkey'].show()
				self['release'].show()
				self['waiting'].stopBlinking()
		elif self.gleich:
			if search('<a href=".*?tvspielfilm.de/tv-programm/sendungen/.*?page=[2-9]', bereich):
				nextpage = search(NEXTPage2, bereich)
				if nextpage:
					self.downloadFull(nextpage.group(1), self.makeTVJetztView)
			else:
				self['menu'].moveToIndex(self.index)
				self.ready = True
				self['CHANNELkey'].hide()
				self['BOUQUETkey'].hide()
				self['INFOkey'].show()
				self['TEXTkey'].show()
				self['TEXTtext'].setText('Sender')
				self['TEXTtext'].show()
				self['INFOtext'].setText('Jetzt/Gleich im TV')
				self['INFOtext'].show()
				self['release'].show()
				self['waiting'].stopBlinking()
		elif search('<a href=".*?tvspielfilm.de/tv-programm/sendungen/.*?page=[2-9]', bereich):
			nextpage = search(NEXTPage2, bereich)
			if nextpage:
				self.downloadFull(nextpage.group(1), self.makeTVJetztView)
		else:
			self['menu'].moveToIndex(self.index)
			self.ready = True
			self['CHANNELkey'].hide()
			self['BOUQUETkey'].hide()
			self['INFOkey'].show()
			self['TEXTkey'].show()
			self['TEXTtext'].setText('Sender')
			self['TEXTtext'].show()
			self['INFOtext'].setText('Jetzt/Gleich im TV')
			self['INFOtext'].show()
			self['release'].show()
			self['waiting'].stopBlinking()

	def makePostviewPage(self, string):
		self['menu'].hide()
		try:
			self._makePostviewPage(string)
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
				self['release'].hide()
				self['waiting'].startBlinking()
				self['waiting'].show()
				link = self.baseurl + '/tv-programm/sendungen/?page=1&order=time&time=shortly'
				self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))
			else:
				self.jetzt = True
				self.gleich = False
				self.abends = False
				self.nachts = False
				self['release'].hide()
				self['waiting'].startBlinking()
				self['waiting'].show()
				link = self.baseurl + '/tv-programm/sendungen/jetzt.html'
				self.makeTVTimer.callback.append(self.downloadFull(link, self.makeTVJetztView))

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
			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.index = self.oldindex
				self.download(self.postlink, self.makePostTimer)
			else:
				self.redTimer(False, self.postlink)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			self.postlink = self.searchlink[c]
			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)

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
				titel = self.tvtitel[c][1]
				titel = titel.split(', ')
				if len(titel) == 1:
					titel = titel[0].split(' ')
					titel = titel[0] + ' ' + titel[1] if titel[0].find(':') > 0 else titel[0]
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
			self['label2'].hide()
			self['label3'].hide()
			self['label4'].hide()
			self['label5'].hide()
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = quote(search).replace('%20', '+')
			searchlink = self.baseurl + '/suche/?q=%s&tab=TV-Sendungen?page=1' % search
			self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
			self.searchcount = 0
			self._makeSearchView(searchlink)

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
			titel = self.tvtitel[c][1]
			self.session.open(searchYouTube, titel, self.movie)

	def gotoEnd(self):
		if self.current != 'postview' and self.ready and not self.search:
			end = len(self.tventries) - 1
			self['menu'].moveToIndex(end)
		elif self.current != 'postview' and self.ready and self.search:
			end = len(self.searchentries) - 1
			self['searchmenu'].moveToIndex(end)

	def downloadFull(self, link, name):
		reactor.callInThread(self._downloadFull, link, name)

	def _downloadFull(self, link, name):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.downloadFullError(error)
		else:
			name(response.content)

	def downloadFullError(self, output):
		TVSlog(output)
		try:
			self['CHANNELkey'].hide()
			self['BOUQUETkey'].hide()
			self['INFOkey'].show()
			self['MENUkey'].hide()
			self['TEXTkey'].show()
			self['OKtext'].hide()
			self['TEXTtext'].setText('Sender')
			self['TEXTtext'].show()
			self['INFOtext'].setText('Jetzt/Gleich im TV')
			self['INFOtext'].show()
		except:
			pass
		self.ready = True

	def downloadPageError(self, output):
		TVSlog(output)
		self['CHANNELkey'].hide()
		self['BOUQUETkey'].hide()
		self['INFOkey'].show()
		self['MENUkey'].hide()
		self['TEXTkey'].show()
		self['OKtext'].hide()
		self['TEXTtext'].setText('Sender')
		self['TEXTtext'].show()
		self['INFOtext'].setText('Jetzt/Gleich im TV')
		self['INFOtext'].show()
		self.ready = True

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['release'].hide()
		self['waiting'].startBlinking()
		self['waiting'].show()
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
		self['CHANNELkey'].hide()
		self['BOUQUETkey'].hide()
		self['INFOkey'].show()
		self['TEXTkey'].show()
		self['TEXTtext'].setText('Sender')
		self['TEXTtext'].show()
		self['INFOtext'].setText('Jetzt im TV/Gleich im TV')
		self['INFOtext'].show()
		self['label2'].setText('Timer')
		self['label3'].show()
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
			self.setTitle('')
			self.setTitle(self.titel)
			self.showProgrammPage()
		elif self.current == 'postview' and not self.search:
			self.hideRatingInfos()
			self.postviewready = False
			self.setTitle('')
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


class TVProgrammView(tvGenreJetztProgrammView):

	def __init__(self, session, link, eventview, tagestipp):
		tvGenreJetztProgrammView.__init__(self, session, link)
		self.eventview = eventview
		self.tagestipp = tagestipp
		self.service_db = serviceDB(self.servicefile)
		if not self.tagestipp:
			channel = findall(',(.*?).html', link)
			service = channel[0].lower()
			self.sref = self.service_db.lookup(service)
			if self.sref == 'nope':
				self.zap = False
				self.picon = False
			else:
				self.zap = True
				self.piconname = findPicon(self.sref, self.piconfolder)
		self.link = link
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
		if isfile(PLUGINPATH + 'db/timer.db'):
			self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		else:
			self.timer = ''
		self.date = datetime.date.today()
		one_day = datetime.timedelta(days=1)
		self.nextdate = self.date + one_day
		self.weekday = makeWeekDay(self.date.weekday())
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
			self.makeTVTimer.callback.append(self.downloadPostPage(self.link, self.makePostviewPage))
		if config.plugins.tvspielfilm.picon.value == "own":
			self.piconfolder = config.plugins.tvspielfilm.piconfolder.value
		elif config.plugins.tvspielfilm.picon.value == "plugin":
			self.piconfolder = PLUGINPATH + 'picons/'
		else:
			self.piconfolder = '/usr/share/enigma2/picon/'
		self.makeTVTimer.start(200, True)

	def makeTVProgrammView(self, string):
		output = ensure_str(open(self.localhtml, 'r').read())
		titel = search('<title>(.*?)von', output)
		date = str(self.date.strftime('%d.%m.%Y'))
		self.titel = str(titel.group(1)) + str(self.weekday) + ', ' + date
		self.setTitle(self.titel)
		items, bereich = parseNow(output)
		self['CHANNELkey'].show()
		self['CHANNELtext'].setText('Tag +/-')
		self['CHANNELtext'].show()
		self['BOUQUETkey'].show()
		self['BOUQUETtext'].setText('Woche +/-')
		self['BOUQUETtext'].show()
		self['INFOkey'].hide()
		self['INFOtext'].hide()
		self['TEXTkey'].hide()
		self['TEXTtext'].hide()
		self['seitennr'].hide()
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
		mh = int(47 * SCALE + 0.5)
		for LOGO, TIME, LINK, TITEL, SPARTE, GENRE, RATING, TRAILER in items:
			res = [LOGO]
			service = LOGO
			sref = self.service_db.lookup(service)
			if config.plugins.tvspielfilm.picon.value == "plugin":
				png = self.piconfolder + '%s.png' % LOGO
			else:
				png = findPicon(sref, self.piconfolder)
			if png:
				res.append(MultiContentEntryPixmapAlphaTest(pos=(int(3 * SCALE), int(2 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), png=loadPNG(png), flags=BT_SCALE))
			else:
				res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(2 * SCALE)), size=(int(67 * SCALE), int(40 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='Picon not found'))
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
			timer = str(date) + ':::' + start + ':::' + str(sref)
			self.tvlink.append(LINK)
			t = TITEL
			if self.showgenre and GENRE:
				x = t + " " + GENRE
			else:
				x = t
			self.tvtitel.append(t)
			if self.progress and self.percent:
				ypos = int(12 * SCALE)
				res.append(MultiContentEntryProgress(pos=(int(77 * SCALE), int(32 * SCALE)), size=(int(95 * SCALE), int(6 * SCALE)), percent=percent, borderWidth=1, foreColor=16777215))
			else:
				ypos = int(14 * SCALE)
			res.append(MultiContentEntryText(pos=(int(75 * SCALE), ypos), size=(int(110 * SCALE), int(20 * SCALE)), font=-2, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=TIME))
			res.append(MultiContentEntryText(pos=(int(220 * SCALE), 0), size=(int(830 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=x))
			if TRAILER:
				png = ICONPATH + 'trailer.png'
				if isfile(png):
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(180 * SCALE), int(8 * SCALE)), size=(int(30 * SCALE), int(30 * SCALE)), png=loadPNG(png)))
			if timer in self.timer:
				self.rec = True
				png = ICONPATH + 'rec.png'
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
				if isfile(png): # DAUMEN
					res.append(MultiContentEntryPixmapAlphaTest(pos=(int(1220 * SCALE), int(7 * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
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
				self['1_zapup'].hide()
				self['2_zapdown'].hide()
			else:
				self['1_zapup'].show()
				self['2_zapdown'].show()
			self['release'].show()
			self['waiting'].stopBlinking()
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
			self.postlink = self.tvlink[c]

		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.postlink = self.searchlink[c]

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
			if not self.search: #if self.zap and not self.search:
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
		elif self.current == 'menu' and self.ready: # and self.zap:
			c = self['menu'].getSelectedIndex()
			self.oldindex = c
			self.postlink = self.tvlink[c]
			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			self.postlink = self.searchlink[c]
			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)
		else:
			self.session.open(MessageBox, NOTIMER, MessageBox.TYPE_ERROR, close_on_any_key=True)

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
				self.piconname = findPicon(sref, self.piconfolder)
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
				titel = titel.split(', ')
				if len(titel) == 1:
					titel = titel[0].split(' ')
					titel = titel[0] + ' ' + titel[1] if titel[0].find(':') > 0 else titel[0]
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
			self['label2'].hide()
			self['label3'].hide()
			self['label4'].hide()
			self['label5'].hide()
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = quote(search).replace('%20', '+')
			searchlink = self.baseurl + '/suche/?q=%s&tab=TV-Sendungen?page=1' % search
			self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
			self.searchcount = 0
			self._makeSearchView(searchlink)

	def pressText(self):
		self._pressText()

	def youTube(self):
		if self.current == 'postview' and self.postviewready:
			self.session.open(searchYouTube, self.name, self.movie)
		elif self.current == 'menu' and not self.search and self.ready:
			c = self['menu'].getSelectedIndex()
			titel = self.tvtitel[c]
			self.session.open(searchYouTube, titel, self.movie)

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

	def downloadPageError(self, output):
		TVSlog(output)
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

	def refresh(self):
		self.postviewready = False
		self.ready = False
		self.current = 'menu'
		self['release'].hide()
		self['waiting'].startBlinking()
		self['waiting'].show()
		self.tventries = []
		self.tvlink = []
		self.tvtitel = []
		self.makeTVTimer.callback.append(self.downloadFullPage(self.link, self.makeTVProgrammView))

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
			sref = str(sref) + 'FIN'
			sref = sub(':0:0:0:.*?FIN', ':0:0:0:', sref)
			self.sref = sref
			channel = self.channel_db.lookup(sref)
			if channel == 'nope':
				self.session.open(MessageBox, 'Service nicht gefunden:\nKein Eintrag für aktuelle Servicereferenz\n%s' % str(sref), MessageBox.TYPE_INFO, close_on_any_key=True)
			else:
				self.piconname = findPicon(sref, self.piconfolder)
				self.link = self.baseurl + '/tv-programm/sendungen/&page=0,' + str(channel) + '.html'
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
			self.setTitle('')
			self.setTitle(self.titel)
		elif self.current == 'postview' and not self.search:
			if self.tagestipp:
				self.close()
			else:
				self.postviewready = False
				self.hideRatingInfos()
				self.setTitle('')
				self.setTitle(self.titel)
				self.showProgrammPage()
			self['button_OK'].hide()
			self['button_TEXT'].hide()
			self['button_7_8_9'].hide()
		elif self.current == 'postview' and self.search:
			self.postviewready = False
			self.showsearch()
			self.current = 'searchmenu'


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
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['picture'] = Pixmap()
		self['picpost'] = Pixmap()
		self['playlogo'] = Pixmap()
		self['playlogo'].hide()
		self['statuslabel'] = Label('')
		self['statuslabel'].hide()
		self['picturetext'] = Label('')
		self['seitennr'] = Label('')
		self['textpage'] = ScrollLabel('')
		self['menu'] = ItemList([])
		self['OKkey'] = Pixmap()
		self['OKtext'] = Label('')
		self['Line_down'] = Label('')
		self.initBlueButton('Aus-/Einblenden')
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
		self.getInfoTimer = eTimer()
		self.getInfoTimer.callback.append(self.downloadFullPage(link, self.makeTVNews))
		self.getInfoTimer.start(200, True)

	def makeTVNews(self, string):
		output = ensure_str(open(self.localhtml, 'r').read())
		titel = search('<title>(.*?)</title>', output)
		self.titel = titel.group(1).replace('&amp;', '&')
		self.setTitle(self.titel)
		self['seitennr'].hide()
		self['Line_down'].show()
		startpos = output.find('<div class="content-area">')
		endpos = output.find('<div class="text--list">')
		if endpos == -1: # andere Endekennung bei Genres
			endpos = output.find('<div class="pagination pagination--numbers"')
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
		if len(name) == 0: # andere Umklammerung bei Genres
			name = findall('<p class="title">(.*?)</p>', bereich)
		subline = findall('<span class="subline">(.*?)</span>', bereich)
		fullname = []
		for i, ni in enumerate(name):
			fullname.append(ni + ' | ' + subline[i]) if len(subline) > 0 else fullname.append(ni)
			try:
				self.picurllist.append(picurl[i])
			except IndexError:
				self.picurllist.append(picurltvsp)
			try:
				self.pictextlist.append(fullname[i])
			except IndexError:
				self.pictextlist.append(' ')
			try:
				res = ['']
				res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(2 * SCALE)), size=(int(870 * SCALE), int(30 * SCALE)), font=1, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=fullname[i]))
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
			self['picturetext'].hide()
		self.ready = True
		self.showTVNews()

	def makePostviewPageNews(self, string):
		output = ensure_str(open(self.localhtml2, 'r').read())
		self['picture'].hide()
		self['picturetext'].hide()
		self['statuslabel'].hide()
		self['menu'].hide()
		self.setTVTitle(output)
		output = sub('</dl>.\n\\s+</div>.\n\\s+</section>', '</cast>', output)
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
		picurl = search('<img src="(.*?).jpg"', bereich)
		if picurl:
			self.downloadPicPost(picurl.group(1) + '.jpg', False)
		else:
			picurl = search('<meta property="og:image" content="(.*?)"', output)
			if picurl:
				self.downloadPicPost(picurl.group(1), False)
			else:
				if self.picurl:
					self.downloadPicPost(self.picurl, False)
				else:
					picurl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png'
					self.downloadPicPost(picurl, False)
		if search('<div class="film-gallery">', output):
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
		head = search('<h1 class="film-title">(.*?)</h1>', bereich)
		if not head:
			head = search('<p class="prelude">(.*?)</p>', bereich)
		if not head:
			head = search('<h1 class="headline headline--article broadcast">(.*?)</h1>', bereich)
		short = search('<span class="title-caption">(.*?)</span>', bereich)
		if not short:
			short = search('<span class="title-caption">(.*?)</span>', bereich)
		intro = search('<p class="intro">"(.*?)</p>', bereich)
		if not intro:
			intro = search('<span class="text-row">(.*?)</span>', bereich)
		if head or short or intro:
			text = ''
			if head:
				text += head.group(1) + '\n\n'
			if short:
				text += short.group(1) + '\n\n'
			if intro:
				text += intro.group(1) + '\n'
		else:
			text = '{keine Beschreibung gefunden}\n'
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
		self.postlink = self.menulink[c]
		self.picurl = self.picurllist[c]
		if action == 'ok':
			if search('www.tvspielfilm.de', self.postlink):
				self.current = 'postview'
				self.downloadPostPage(self.postlink, self.makePostviewPageNews)
			else:
				self['statuslabel'].setText('Kein Artikel verfügbar')
				self['statuslabel'].show()

	def getPic(self, output):
		with open(self.picfile, 'wb') as f:
			f.write(output)
		showPic(self['picture'], self.picfile)

	def downloadError(self, output):
		TVSlog(output)
		tvAllScreen.downloadError(output)
		self['statuslabel'].setText('Download Fehler')
		self['statuslabel'].show()

	def showTVNews(self):
		self.current = 'menu'
		self['release'].show()
		self['waiting'].stopBlinking()
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
		self.initBlueButton('Aus-/Einblenden')

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
		self.link = link
		self.picmode = picmode
		HIDEFLAG = True
		self.link = link
		self.pixlist = []
		self.topline = []
		self.titel = ''
		self.picmax = 1
		self.count = 0
		self['release'] = Label(RELEASE)
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		for i in range(9):
			self['infotext%s' % i] = Label('')
		self['picture'] = Pixmap()
		self['picindex'] = Label('')
		self['pictext'] = ScrollLabel('')
		self['textpage'] = ScrollLabel('')
		self['label5'] = Label('')
		self['seitennr'] = Label('')
		self['OKkey'] = Pixmap()
		self['OKtext'] = Label('')
		self['Line_down'] = Label('')
		self.initBlueButton('Aus-/Einblenden')
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
		self.getInfoTimer = eTimer()
		if self.picmode == 1:
			self.getInfoTimer.callback.append(self.download(self.link, self.getNewsPicPage))
		else:
			self.getInfoTimer.callback.append(self.download(self.link, self.getPicPage))
		self.getInfoTimer.start(200, True)

	def getPicPage(self, output):
		output = transHTML(ensure_str(output))
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
		self.showInfotext(self.topline)

	def getNewsPicPage(self, output):
		output = ensure_str(output)
		self.setTVTitle(output)
		self['release'].show()
		self['waiting'].stopBlinking()
		startpos = output.find('<div class="film-gallery">')
		if startpos == -1:
			startpos = output.find('class="film-gallery paragraph')
		endpos = output.find('<div class="swiper-slide more-galleries">')
		if endpos == -1:
			endpos = output.find('<div class="paragraph clear film-gallery"')
		bereich = output[startpos:endpos]
		bereich = cleanHTML(bereich)
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
		bereich = sub('&amp;', '&', bereich)
		self.pixlist = []
		infotext = []
		credits = []
		datenfeld = findall('<div class="swiper-slide"(.*?)<span class="counter">', bereich, flags=S)
		for daten in datenfeld:
			foundpix = findall('<img src="(.*?)"', daten)
			if foundpix:
				self.pixlist.append(foundpix[0])
				try:
					self.download(self.pixlist[0], self.getPic)
				except IndexError:
					pass
			else:
				self.pixlist.append('https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/TV-Spielfilm-Logo.svg/500px-TV-Spielfilm-Logo.svg.png')
			foundpara1 = findall('<div class="firstParagraph">(.*?)</div>', daten, flags=S)
			if foundpara1:
				if foundpara1[0].find('<a class="switch-paragraph" href="#">mehr...</a>'):
					foundpara2 = findall('<div class="secondParagraph" style="display:none;">(.*?)</div>', daten, flags=S)
					if foundpara2:
						info = foundpara2[0]
					else:
						info = foundpara1[0]
				else:
					info = foundpara1[0]
			else:
				foundpara2 = findall('<div class="secondParagraph" style="(.*?)">(.*?)</div>', daten, flags=S)
				if foundpara2:
					info = foundpara2[0]
				else:
					info = '{keine Beschreibung gefunden}\n'
			info = info.replace(', <a class="switch-paragraph" href="#">mehr...</a>', '').replace('<font size="+1">', '').replace('</font>', '')
			info = info.replace('<a class="switch-paragraph" href="#">mehr...</a>', '').replace('<br ', '').rstrip() + '\n'
			infotext.append(info)
			foundcredits = findall('<span class="credit">(.*?)</span>', bereich, flags=S)
			if foundcredits:
				credits.append(foundcredits[0])
			else:
				credits.append('')
		self.picmax = len(self.pixlist) if self.pixlist else 0
		self['picindex'].setText('%s von %s' % (self.count + 1, self.picmax))
		self.topline = [infotext[i] + '\n' + credits[i] for i in range(self.picmax)]
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
		if self.picmode == 0:
			self['pictext'].setText(self.description[self.count] + '\n%s von %s' % (self.count + 1, self.picmax))
		else:
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

	def downloadError(self, output):
		TVSlog(output)
		tvAllScreen.downloadError(output)
		self['pictext'].setText('Download Fehler')

	def initBlueButton(self, text):
		self['bluebutton'] = Label()
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
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
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
		self['release'].show()
		self['waiting'].stopBlinking()
		startpos = output.find('<div class="film-gallery">')
		if startpos == -1:
			startpos = output.find('class="film-gallery paragraph')
		endpos = output.find('<div class="swiper-slide more-galleries">')
		if endpos == -1:
			endpos = output.find('<div class="paragraph clear film-gallery"')
		bereich = output[startpos:endpos]
		self.pixlist = findall('" data-src="(.*?)" alt=', bereich)
		if not self.pixlist:
			self.pixlist = findall('<img src="(.*?)" alt=', bereich)
		if self.pixlist:
			self.download(self.pixlist[self.count], self.getPic)
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

	def downloadError(self, output):
		TVSlog(output)
		tvAllScreen.downloadError(output)
		self['picindex'].setText('Download Fehler')

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


class searchYouTube(tvAllScreen):

	def __init__(self, session, name, movie):
		name = ensure_str(name)
		global HIDEFLAG
		self.LinesPerPage = 6
		skin = readSkin("searchYouTube")
		tvAllScreen.__init__(self, session, skin)
		if movie:
			name = name + ' Trailer'
		name = str(name.encode('ascii', 'xmlcharrefreplace')).replace(' ', '+')
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
		self['label2'] = Label(' YouTube Suche')
		self['Line_down'] = Label('')
		self.initBlueButton('Aus-/Einblenden')
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
		self.makeTrailerTimer = eTimer()
		self.makeTrailerTimer.callback.append(self.downloadFullPage(self.link, self.makeTrailerList))
		self.makeTrailerTimer.start(200, True)
		self['Line_down'].show()

	def initBlueButton(self, text):
		self['bluebutton'] = Label()
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
		bereich = transHTML(output[startpos:endpos])
# for analysis purpose only, activate when YouTube-Access won't work properly
#		analyse = bereich.replace('a><a', 'a>\n<a').replace('script><script', 'script>\n<script').replace('},{', '},\n{').replace('}}}]},"publishedTimeText"', '}}}]},\n"publishedTimeText"')
#		with open('/home/root/logs/analyse.log', 'a') as f:
#			f.write(analyse)
		self.trailer_id = findall('{"videoRenderer":{"videoId":"(.*?)","thumbnail', bereich) # Suchstring voher mit re.escape wandeln
		self.trailer_titel = findall('"title":{"runs":\[{"text":"(.*?)"}\]', bereich) # Suchstring voher mit re.escape wandeln
		self.trailer_time = findall('"lengthText":{"accessibility":{"accessibilityData":{"label":"(.*?)"}},"simpleText"', bereich) # Suchstring voher mit re.escape wandeln
		trailer_info = findall('"viewCountText":{"simpleText":"(.*?)"},"navigationEndpoint"', bereich) # Suchstring voher mit re.escape wandeln
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
				poster = 'https://i.ytimg.com/vi/' + self.trailer_id[i] + '/mqdefault.jpg'
				reactor.callInThread(self.igetPoster, poster, i)
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
					reactor.callInThread(self.igetPoster, poster, i)
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
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.downloadPageError(error)
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

	def downloadFullPage(self, link, name):
		reactor.callInThread(self._downloadFullpage, link, name)

	def _downloadFullpage(self, link, name):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.downloadPageError(error)
		else:
			with open(self.localhtml, 'wb') as f:
				f.write(response.content)
			name(response.content)

	def downloadPageError(self, output):
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
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].stopBlinking()
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
			response = self.opener.open(ensure_binary('https://member.tvspielfilm.de/login/70.html'), values, timeout=60)
			result = response.read()
			error = ''
			if search('"error":"', result):
				error = search('"error":"(.*?)\\.', result)
				self.error = 'Mein TV SPIELFILM: ' + error.group(1) + '!'
				self.loginerror = True
				if isfile(self.cookiefile):
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
					if self.tipps:
						self.stopTipps()
					if search('jetzt', self.mainmenulink[c]) or search('time=shortly', self.mainmenulink[c]) or search('abends', self.mainmenulink[c]) or search('nachts', self.mainmenulink[c]):
						self.session.openWithCallback(self.selectMainMenu, TVJetztView, self.mainmenulink[c], False)
					elif search('page=1', self.mainmenulink[c]):
						self.session.openWithCallback(self.selectMainMenu, TVHeuteView, self.mainmenulink[c], self.opener)
					elif search('/bilder', self.mainmenulink[c]):
						self.session.openWithCallback(self.selectMainMenu, TVNews, self.mainmenulink[c])
#						self.session.openWithCallback(self.selectMainMenu, TVTrailerBilder, self.mainmenulink[c], '_pic')
					elif search('/news-und-specials', self.mainmenulink[c]):
						self.session.openWithCallback(self.selectMainMenu, TVNews, self.mainmenulink[c])
					elif search('/tv-tipps|/tv-genre|/trailer-und-clips', self.mainmenulink[c]):
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
				if search('/genre', self.secondmenulink[c]):
					try:
						self.ready = False
						self.makeThirdMenu(self.secondmenulink[c], self.sparte[c])
					except IndexError:
						self.ready = True
				elif search('/news|/serien|/streaming|/trailer-und-clips|/stars|/charts|/neustarts|/neuerscheinungen|/kino-vorschau|/tatort|/kids-tv|/bestefilme|/tv-programm|/tv-tipps|/awards|/oscars', self.secondmenulink[c]):
					try:
						self.session.openWithCallback(self.selectSecondMenu, TVNews, self.secondmenulink[c])
					except IndexError:
						pass
				else:
					try:
						self.ready = False
						self.makeThirdMenu(None, self.sender[c])
					except IndexError:
						self.ready = True

			elif self.actmenu == 'thirdmenu':
				if search('/suche', self.thirdmenulink[c]):
					try:
						if self.tipps:
							self.stopTipps()
						self.session.openWithCallback(self.selectThirdMenu, TVGenreView, self.thirdmenulink[c], self.genre[c])
					except IndexError:
						pass
				elif search('/genre', self.thirdmenulink[c]):
					try:
						if self.tipps:
							self.stopTipps()
						self.session.openWithCallback(self.selectThirdMenu, TVNews, self.thirdmenulink[c])
					except IndexError:
						pass
				elif search('/tv-tipps', self.thirdmenulink[c]):
					try:
						if self.tipps:
							self.stopTipps()
						self.session.openWithCallback(self.selectThirdMenu, TVTippsView, self.thirdmenulink[c], self.genre[c])
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
		res.append(MultiContentEntryText(pos=(0, 1), size=(int(310 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=text))
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
		res.append(MultiContentEntryText(pos=(0, 1), size=(int(310 * SCALE), int(30 * SCALE)), font=2, flags=RT_HALIGN_CENTER, text=text))
		self.secondmenulist.append(res)
		self.secondmenulink.append(self.baseurl + link)

	def makeMainMenu(self):
		self.makeMenuItem('Heute im TV', '/tv-programm/tv-sender/?page=1')
		self.makeMenuItem('Jetzt im TV', '/tv-programm/sendungen/jetzt.html')
		self.makeMenuItem('Gleich im TV', '/tv-programm/sendungen/?page=1&order=time&time=shortly')
		self.makeMenuItem('20:15 im TV', '/tv-programm/sendungen/abends.html')
		self.makeMenuItem('22:00 im TV', '/tv-programm/sendungen/fernsehprogramm-nachts.html')
		self.makeMenuItem('TV-Programm', '/tv-programm/tv-sender/')
		self.makeMenuItem('News', '/news/')
		self.makeMenuItem('Streaming', '/streaming/')
		self.makeMenuItem('TV-Tipps', '/tv-tipps/')
		self.makeMenuItem('Serien', '/serien/')
		self.makeMenuItem('Filme', '/kino/')
		self.makeMenuItem('Stars', '/stars/')
		self.makeMenuItem('Nachrichten', '/news-und-specials/')
		self.makeMenuItem('Bildergalerien', '/bilder/')
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
		if search('/tv-sender/', link):
			startpos = output.find('<option value="" label="Alle Sender">Alle Sender</option>')
			endpos = output.find('<div class="button-toggle">')
			bereich = output[startpos:endpos]
			bereich = transHTML(bereich)
			name = findall('<optgroup label="(.*?)">', bereich)
			for ni in name:
				self.makeSecondMenuItem(ni)
			if self.tipps:
				self.hideTipps()
		elif search('/news/', link):
			self.makeSecondMenuItem3('TV-News', '/news/tv/')
			self.makeSecondMenuItem3('Serien-News', '/news/serien/')
			self.makeSecondMenuItem3('Streaming-News', '/news/streaming/')
			self.makeSecondMenuItem3('Film-News', '/news/filme/')
			self.makeSecondMenuItem3('Star-News', '/news/stars/')
			self.makeSecondMenuItem3('Shopping-News', '/news/shopping/')
		elif search('/tv-tipps/', link):
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
		elif search('/serien/', link):
#			self.makeSecondMenuItem2('Serien', '/serien/')
			self.makeSecondMenuItem2('Serien-News', '/news/serien/')
			self.makeSecondMenuItem2('Quizze', '/news/quizze/')
			self.makeSecondMenuItem2('Serien-Trailer', '/serien/serien-trailer/')
#			self.makeSecondMenuItem2('Serien A-Z', '/serien/serienarchiv/')
			self.makeSecondMenuItem2('Genres', '/serien/genre/')
			self.makeSecondMenuItem2('Beste Serien', '/news/serien/die-besten-us-serien-aller-zeiten,9250353,ApplicationArticle.html')
			self.makeSecondMenuItem2('Beste Netflix Serien', '/news/serien/die-besten-netflix-serien,9437468,ApplicationArticle.html')
			self.makeSecondMenuItem2('The Walking Dead', '/serien/walkingdead/')
			self.makeSecondMenuItem2('The Big Bang Theory', '/serien/thebigbangtheory/')
			self.makeSecondMenuItem2('''Grey's Anatomy''', '/serien/greys-anatomy/')
			self.makeSecondMenuItem2('Tatort', '/tatort/')
		elif search('/streaming/', link):
			self.makeSecondMenuItem3('Streaming-News', '/news/streaming/')
			self.makeSecondMenuItem3('Streaming-Vergleich', '/streaming/streamingvergleich/')
			self.makeSecondMenuItem3('Neu auf Netflix', '/news/filme/neu-bei-netflix-diese-serien-und-filme-lohnen-sich,8941871,ApplicationArticle.html')
			self.makeSecondMenuItem3('Neu bei Amazon Prime', '/news/filme/neu-bei-amazon-prime-diese-serien-und-filme-lohnen-sich,10035760,ApplicationArticle.html')
			self.makeSecondMenuItem3('Neu auf Disney+', '/news/serien/neu-auf-disneyplus-serien-filme,10127377,ApplicationArticle.html')
			self.makeSecondMenuItem3('Sky Ticket', '/news/serien/neu-auf-sky-ticket-die-besten-filme-und-serien,10090987,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Netflix Serien', '/news/serien/die-besten-netflix-serien,9437468,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Netflix Filme', '/news/filme/die-besten-netflix-filme,9659520,ApplicationArticle.html')
			self.makeSecondMenuItem3('beste Amazon Prime Filme', '/news-und-specials/die-besten-filme-bei-amazon-prime-unsere-empfehlungen,10155040,ApplicationArticle.html')
		elif search('/kino/', link):
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
		elif search('/stars/', link):
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
		bereich = transHTML(output[startpos:endpos])
		lnk = findall("value='(.*?)'", bereich)
		name = findall("<option label='(.*?)'", bereich)
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
			string = transHTML(output[startpos:endpos])
			self.makeThirdMenuItem(string, sender)
			self['thirdmenu'].l.setList(self.thirdmenulist)
			self['thirdmenu'].l.setItemHeight(int(30 * SCALE))
			self.selectThirdMenu()
		elif search('/genre', link):
			self.downloadFullPage(link, self.makeGenres)

	def makeGenres(self, dummy):
		output = ensure_str(open(self.localhtml, 'r').read())
		startpos = output.find('<p class="filter-title">Genre</p>')
		endpos = output.find('<section class="filter abc-filter">')
		bereich = transHTML(output[startpos:endpos])
		genres = findall('<a title="(.*?)" href="', bereich)
		links = findall('" href="(.*?)/">', bereich)
		for i, gi in enumerate(genres):
			self.makeThirdMenuItem2(gi, links[i])
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
				self['waiting'].stopBlinking()
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

	def _downloadError(self, output):
		TVSlog(output)
		try:
			error = output.getErrorMessage()
			self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar:\n%s' % error, MessageBox.TYPE_ERROR)
			self.ready = True
		except AttributeError:
			self.ready = True

	def checkMainMenu(self):
		if isfile(self.servicefile):
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
				self.makeSecondMenu(link)
			else:
				self.makeErrorTimer = eTimer()
				self.makeErrorTimer.callback.append(self.displayError)
				self.makeErrorTimer.start(200, True)
		else:
			reactor.callInThread(self.download, link, self.makeSecondMenu)

	def download(self, link, name):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
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
			if isfile(self.servicefile):
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
			if isfile(self.senderhtml):
				remove(self.senderhtml)
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.session.openWithCallback(self.closeconf, tvsConfig)

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
				self.TagesTipps.stop()
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


class makeServiceFile(Screen):

	def __init__(self, session):
		self.skin = readSkin("makeServiceFile")
		Screen.__init__(self, session)
		dic = {}
		dic['picpath'] = PICPATH
		dic['selbg'] = str(config.plugins.tvspielfilm.selectorcolor.value)
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
			services = slist.getServicesAsList(format='S')
			search = ['IBDCTSERNX']
			search.extend([(service, 0, -1) for service in services])
			self.epgcache = eEPGCache.getInstance()
			events = self.epgcache.lookupEvent(search)
			data = ''
			for eventinfo in events:
				station = eventinfo[8]
				station = sub('[/]', ' ', station)
				station = sub("'", '', station)
				service = eventinfo[7]
				service = sub(':0:0:0:.*?[)], ', ':0:0:0:\n', service)
				service = sub(':0:0:0::[a-zA-Z0-9_-]+', ':0:0:0:', service)
				data += '%s\t %s\n' % (station, service)
##			for analysis purpose only, activate when picons are missing
#			Bouquetlog('Sendernamen aus Bouquets:\n' + '-' * 70 + '\n') # analysis
#			Bouquetlog(data) # analysis
			data = transCHANNEL(data) # Diese Zeile darf nicht auskommentiert werden
#			Bouquetlog('\n\nSendernamen als Piconname:\n' + '-' * 70 + '\n') # analysis
#			Bouquetlog(data) # analysis
			with open(self.servicefile, 'a') as f:
				f.write(data)
			fnew = open(self.servicefile + '.new', 'w')
			count = 0
			newdata = ''
			search = compile(' [a-z0-9-]+ ').search
			for line in open(self.servicefile):
				line = line.strip()
				if line != '' and ',' not in line and '/' not in line and '#' + line[0:5] not in newdata:
					fnew.write(line)
					fnew.write(linesep)
					newdata = newdata + '#' + str(line[0:5])
					count += 1
			f.close()
			fnew.close()
			rename(self.servicefile + '.new', self.servicefile)
			self.ready = True
			if newdata == '':
				self.session.openWithCallback(self.noBouquet, MessageBox, '\nKeine TV Spielfilm Sender gefunden.\nBitte wählen Sie ein anderes TV Bouquet.', MessageBox.TYPE_YESNO)
			else:
				self.session.openWithCallback(self.otherBouquet, MessageBox, '\nInsgesamt %s TV Spielfilm Sender importiert.\nMöchten Sie ein weiteres TV Bouquet importieren?' % str(count), MessageBox.TYPE_YESNO, default=False)

	def otherBouquet(self, answer):
		if answer is True:
			self.bouquetsTimer.callback.append(self.getBouquets)
		else:
			self.close(True)

	def noBouquet(self, answer):
		if answer is True:
			self.bouquetsTimer.callback.append(self.getBouquets)
		else:
			if isfile(self.servicefile):
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
		self['release'].hide()
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
		self.field = self.field + str(number)
		self['number'].setText(self.field)
		if len(self.field) >= 2:
			self.keyOK()

	def keyOK(self):
		self['release'].show()
		self['waiting'].stopBlinking()
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
		self.makeMenuTimer = eTimer()
		self.makeMenuTimer.callback.append(self.makePageMenu)
		self.makeMenuTimer.start(200, True)

	def makePageMenu(self):
		self.setTitle('Senderliste')
		self['release'].show()
		self['waiting'].stopBlinking()
		output = ensure_str(open(self.localhtml, 'r').read())
		startpos = output.find('label="Alle Sender">Alle Sender</option>')
		if config.plugins.tvspielfilm.meintvs.value == 'yes':
			endpos = output.find('<optgroup label="Hauptsender">')
		else:
			endpos = output.find('<optgroup label="alle Sender alphabetisch">')
		bereich = output[startpos:endpos]
		sender = findall('"channel":"(.*?)","broadcastChannelGroup"', bereich)
# for analysis purpose only! activate when picons are missing or for detecting unneeded picons
#		fullname = findall("<option label='(.*?)' value=", bereich)
#		from glob import glob
#		availpicons = glob(PLUGINPATH + 'picons/*.png')
#		if availpicons:
#			TVSlog('availpicons:', availpicons)
#			for i in range(len(availpicons)):
#				availpicons[i] = availpicons[i][availpicons[i].rfind('/') + 1 :]
#			ff = open("/home/root/logs/avail_picons.txt", "w")
#			ff.write('list of available picons in pluginpath ./picons/:\n')
#			ff.write('----------------------------------------------------\n')
#			for i in range(len(availpicons)):
#				ff.write(availpicons[i] + '\n')
#			ff.close()
#			ff = open("/home/root/logs/missing_picons.txt", "w")
#			ff.write('list of missing picons in pluginpath ./picons/:\n')
#			ff.write('----------------------------------------------------\n')
#			TVSlog('sender:', sender)
#			for i in range(len(sender)):
#				if isfile(PLUGINPATH + 'picons/' + sender[i].lower() + '.png'):
#					TVSlog('sender[i]:', sender[i])
#					availpicons.remove(sender[i].lower() + '.png')
#				else:
#					ff.write(str(fullname[i]) + ", " + str(sender[i].lower()) + '.png\n')
#				ff.close()
#			ff = open("/home/root/logs/unneeded_picons.txt", "w")
#			ff.write('list of unneeded picons in pluginpath ./picons/:\n')
#			ff.write('----------------------------------------------------\n')
#			for i in range(len(availpicons)):
#				ff.write(availpicons[i] + '\n')
#			ff.close()
#			ff = open("/home/root/logs/complete_stationlist.txt", "w")
#			ff.write('complete list of from homepage supported stations:\n')
#			ff.write('--------------------------------------\n')
#		for i in range(len(sender)):
#			ff.write(str(fullname[i]) + " = " + str(sender[i].lower())\n')
#		ff.close()
		self.maxpages = len(sender) // 6
		if len(sender) % 6 != 0:
			self.maxpages += 1
		count = 0
		page = 1
		mh = int(37 * SCALE + 0.5)
		while page <= self.maxpages:
			res = ['']
			res.append(MultiContentEntryText(pos=(int(3 * SCALE), int(2 * SCALE)), size=(int(28 * SCALE), mh), font=1, color=10857646, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=str(page)))
			for i in range(6):
				try:
					service = sender[count].lower().replace(' ', '').replace('.', '').replace('ii', '2')
					png = PLUGINPATH + 'picons/%s.png' % service
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

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close(0)


class tvTipps(tvAllScreen):

	def __init__(self, session):
		global HIDEFLAG
		self.dict = {'picpath': PICPATH, 'selbg': str(config.plugins.tvspielfilm.selectorcolor.value)}
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
		self['label6'] = Label('')
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
		self.getTippsTimer = eTimer()
		self.getTippsTimer.callback.append(self.downloadFirst(self.baseurl))
		self.getTippsTimer.start(200, True)
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
		reactor.callInThread(self.idownload)
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
		self['label'].show()
		self['label2'].setText(titel)
		self['label2'].show()
		self['label3'].setText(text)
		self['label3'].show()
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
			if self.tippspicture:
				self.count = self.count % len(self.tippspicture)
			if isfile(self.pic[self.count]):
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
			self['label'].show()
			self['label2'].setText(titel)
			self['label2'].show()
			self['label3'].setText(text)
			self['label3'].show()
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

	def idownload(self):
		for idx, link in enumerate(self.tippspicture):
			try:
				response = requests.get(link)
				response.raise_for_status()
			except requests.exceptions.RequestException as error:
				self.ready = True
				TVSlog(error)
			else:
				with open(self.pic[idx], 'wb') as f:
					f.write(response.content)
				if idx == 0:
					showPic(self['picture'], self.pic[idx])

	def downloadFirst(self, link):
		reactor.callInThread(self._downloadFirst, link)

	def _downloadFirst(self, link):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.ready = True
			self.session.open(MessageBox, 'Der TV Spielfilm Server ist zurzeit nicht erreichbar:\n%s' % error, MessageBox.TYPE_ERROR)
		else:
			self.getTagesTipps(response.content)

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
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['plugin'] = Pixmap()
		list = []
		if config.plugins.tvspielfilm.plugin_size == 'FHD':
			list.append(getConfigListEntry('Plugin Größe:', config.plugins.tvspielfilm.plugin_size))
#        list.append(getConfigListEntry('Plugin Position:', config.plugins.tvspielfilm.position))
		list.append(getConfigListEntry('Verwende Plugin-eigene Schrift:', config.plugins.tvspielfilm.font))
		list.append(getConfigListEntry('Schriftgröße Auswahlzeilen:', config.plugins.tvspielfilm.font_size))
		list.append(getConfigListEntry('Farbe des Auswahlbalkens:', config.plugins.tvspielfilm.selectorcolor))
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
		self['release'].show()
		self['waiting'].stopBlinking()
		current = self['config'].getCurrent()
		if current == self.piconfolder:
			self.session.openWithCallback(self.folderSelected, FolderSelection, config.plugins.tvspielfilm.piconfolder.value)

	def folderSelected(self, folder):
		if folder:
			config.plugins.tvspielfilm.piconfolder.value = folder
			config.plugins.tvspielfilm.piconfolder.save()

	def save(self):
		# config.plugins.tvspielfilm.plugin_size.save()
		config.plugins.tvspielfilm.font.save()
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
					password = ensure_str(b64decode(config.plugins.tvspielfilm.password.value.encode('ascii', 'xmlcharrefreplace')))
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
		config.plugins.tvspielfilm.selectorcolor.save()
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
			self.session.openWithCallback(self.nologin_return, MessageBox, 'Sie haben den Mein TV SPIELFILM Login aktiviert, aber unvollständige Login-Daten angegeben.\n\nMöchten Sie die Mein TV SPIELFILM Login-Daten jetzt angeben oder Mein TV SPIELFILM deaktivieren?', MessageBox.TYPE_YESNO)
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
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
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
		self['release'].show()
		self['waiting'].stopBlinking()

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
		if isfile(self.servicefile):
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
		if isfile(self.servicefile):
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
		self.finishedTimerMode = 2
		self.localhtml = '/tmp/tvspielfilm.html'
		self['release'] = Label(RELEASE)
		self['release'].hide()
		self['waiting'] = BlinkingLabel('Bitte warten...')
		self['waiting'].startBlinking()
		self['waiting'].show()
		self['CHANNELkey'] = Pixmap()
		self['CHANNELtext'] = Label('')
		self['BOUQUETkey'] = Pixmap()
		self['BOUQUETtext'] = Label('')
		self['INFOkey'] = Pixmap()
		self['INFOtext'] = Label('')
		self['MENUkey'] = Pixmap()
		self['MENUtext'] = Label('')
		self['button_OK'] = Pixmap()
		self['label_OK'] = Label('')
		self['button_TEXT'] = Pixmap()
		self['label_TEXT'] = Label('')
		self['button_INFO'] = Pixmap()
		self['label_INFO'] = Label()
		self['button_7_8_9'] = Pixmap()
		self['Line_top'] = Label('')
		self['Line_mid'] = Label('')
		self['Line_down'] = Label('')
		for i in range(6):
			self['pic%s' % i] = Pixmap()
			self['picon%s' % i] = Pixmap()
			self['sender%s' % i] = Label('')
			self['sender%s' % i].hide()
			self['pictime%s' % i] = Label('')
			self['pictext%s' % i] = Label('')
			self['pictext%s_bg' % i] = Label('')
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
		self.initBlueButton('Aus-/Einblenden')
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
		if isfile(PLUGINPATH + 'db/timer.db'):
			self.timer = open(PLUGINPATH + 'db/timer.db').read().split('\n')
		else:
			self.timer = ''
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
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self['MENUkey'].show()
		self['MENUtext'].show()
		self['release'].hide()
		self['waiting'].startBlinking()
		self['waiting'].show()
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
		self.makeTVTimer = eTimer()
		self.makeTVTimer.callback.append(self.downloadFullPage(self.link))
		self.makeTVTimer.start(200, True)

	def makeTVHeuteView(self, string):
		output = ensure_str(open(self.localhtml, 'r').read())
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
			self['seitennr'].show()
			self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
		self.zaps = [True, True, True, True, True, True]
		self.srefs = [[], [], [], [], [], []]
		date = str(self.date.strftime('%d.%m.%Y'))
		self.titel = 'Heute im TV  - ' + str(self.weekday) + ', ' + date
		self.setTitle(self.titel)
		startpostop = output.find('<div class="gallery-area">')
		endpostop = output.find('<div class="info-block">')
		bereichtop = transHTML(output[startpostop:endpostop])
		bereichtop = sub('<wbr/>', '', bereichtop)
		bereichtop = sub('<div class="first-program block-1">\n.*?</div>', '<div class="first-program block-1"><img src="http://a2.tvspielfilm.de/imedia/8461/5218461,qfQElNSTpxAGvxxuSsPkPjQRIrO6vJjPQCu3KaA_RQPfIknB77GUEYh_MB053lNvumg7bMd+vkJk3F+_CzBZSQ==.jpg" width="149" height="99" border="0" /><span class="time"> </span><strong class="title"> </strong></div>', bereichtop)
		picons = findall('"sendericon","channel":"(.*?)","broadcastChannelGroup"', bereichtop)
		for i in range(6):
			self['sender%s' % i].show()
			self['pictext%s_bg' % i].show()
		self['release'].show()
		self['waiting'].stopBlinking()
		if picons:
			for i in range(6):
				sref = picons[i].lower().replace(' ', '').replace('.', '').replace('ii', '2')
				if sref == 'nope':
					self.zaps[i] = False
					self['picon%s' % i].hide()
				else:
					picon = PLUGINPATH + 'picons/' + sref + '.png'
					if isfile(picon):
						self['picon%s' % i].instance.setScale(1)
						self['picon%s' % i].instance.setPixmapFromFile(picon)
						self['picon%s' % i].show()
					else:
						self['picon%s' % i].hide()
		sender = findall('<h3>(.*?)</h3>', bereichtop)
		if sender:
			for i in range(6):
				self.srefs[i].append(serviceDB(self.servicefile).lookup(transCHANNEL(sender[i]).strip()))
				self.srefs[i].append(sender[i])
				self['sender%s' % i].setText(sender[i])
				self['sender%s' % i].show()
		else:
			for i in range(6):
				self.srefs[i].append('')
				self['sender%s' % i].hide()
		pic = findall('<img src="(.*?)" alt="(.*?)"', bereichtop)
		idx = 0
		picDownloads = []
		for i, pi in enumerate(pic):
			try:
				picdata, dummy = pi
				if picdata[-4:] == '.jpg':
					picurl = ('https://' + search('https://(.*).jpg', picdata).group(1) + '.jpg').replace('159', '300')
					picDownloads.append((picurl, idx))
					self['pic%s' % idx].show()
					idx += 1
			except IndexError:
				pass
		reactor.callInThread(self.idownloadPics, picDownloads)
		pictime = findall('<span class="time">(.*?)</span>', bereichtop)
		if pictime:
			for i in range(6):
				self['pictime%s' % i].setText(pictime[i])
				self['pictime%s' % i].show()
		else:
			for i in range(6):
				self['pictime%s' % i].hide()
		pictext = findall('<strong class="title">(.*?)</strong>', bereichtop)
		if pictext:
			for i in range(6):
				self['pictext%s' % i].setText(pictext[i])
				self['pictext%s' % i].show()
				self['pictext%s_bg' % i].show()
		else:
			for i in range(6):
				self['pictext%s' % i].hide()
				self['pictext%s_bg' % i].hide()
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
		bereich = transHTML(output[startpos:endpos])
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
		currentitem = []
		currentlink = 'na'
		currenttitle = ''
		mh = int(86 * SCALE)
		for mi in menuitems:
			self.menu = 'menu%s' % midx
			for x in mi:
				if search('TIME', x):
					x = sub('TIME', '', x)
					if len(currentitem) == 0:
						currentitem = [x]
					if currentitem != [x]:
						self.tventriess[midx].append(currentitem)
						self.tvlinks[midx].append(currentlink)
						self.tvtitels[midx].append(currenttitle)
						currentitem = [x]
					currentitem.append(MultiContentEntryText(pos=(0, 2), size=(int(40 * SCALE), int(17 * SCALE)), font=-2, backcolor=13388098, color=16777215, backcolor_sel=13388098, color_sel=16777215, flags=RT_HALIGN_CENTER, text=x))
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
						boxtimers += item + '\n'# [:21] + transCHANNEL(ServiceReference(eServiceReference(item[21:].strip())).getServiceName())
					if timer in boxtimers:
						self.rec = True
						png = ICONPATH + 'rec.png'
						if isfile(png):
							currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(0, int((20 + icount * 14) * SCALE)), size=(int(40 * SCALE), int(13 * SCALE)), png=loadPNG(png)))
							icount += 1
				if search('LOGO', x):  # NEU
					x = sub('LOGO', '', x)
					png = '%s%s.png' % (ICONPATH, x)
					if isfile(png):
						currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(0, int((20 + icount * 14) * SCALE)), size=(int(40 * SCALE), int(13 * SCALE)), png=loadPNG(png)))
						icount += 1
				if search('RATING', x):  # DAUMEN
					x = sub('RATING', '', x).replace(' ', '-')
					png = '%s%s.png' % (ICONPATH, x)
					if isfile(png):
						currentitem.append(MultiContentEntryPixmapAlphaTest(pos=(int(8 * SCALE), int((20 + icount * 14) * SCALE)), size=(int(27 * SCALE), int(27 * SCALE)), png=loadPNG(png)))
				if search('LINK', x):
					x = sub('LINK', '', x)
					currentlink = x
				if search('TITEL', x) and search('SUBTITEL', x) is None:
					x = sub('TITEL', '', x)
					currenttitle = x
				if search('SUBTITEL', x):
					x = sub('SUBTITEL', '', x).strip()
					if x != '':
						currenttitle = currenttitle + ', ' + x
				if self.rec:
					self.rec = False
				currentitem.append(MultiContentEntryText(pos=(int(45 * SCALE), 0), size=(int(155 * SCALE), mh), font=1, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=currenttitle))
			self.tventriess[midx].append(currentitem)
			self.tvlinks[midx].append(currentlink)
			self.tvtitels[midx].append(currenttitle)
			currentitem = []
			midx += 1
		for i in range(6):
			self['menu%s' % i].l.setItemHeight(mh)
			self['menu%s' % i].l.setList(self.tventriess[i])
			self['menu%s' % i].moveToIndex(self.oldindex)
		for i in range(6):
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

	def makePostviewPage(self, string):
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
		self._makePostviewPage(string)

	def ok(self):
		self._ok()

	def selectPage(self, action):
		self.oldcurrent = self.current
		if self.ready:
			for i in range(6):
				if self.current == 'menu%s' % i:
					c = self['menu%s' % i].getSelectedIndex()
					self.postlink = self.tvlinks[i][c]
					if action == 'ok':
						if search('www.tvspielfilm.de', self.postlink):
							self.current = 'postview'
							self.downloadPostPage(self.postlink, self.makePostviewPage)
			if self.current == 'searchmenu':
				c = self['searchmenu'].getSelectedIndex()
				self.postlink = self.searchlink[c]
				if action == 'ok':
					if search('www.tvspielfilm.de', self.postlink):
						self.current = 'postview'
						self.downloadPostPage(self.postlink, self.makePostviewPage)

	def getEPG(self):
		if self.current == 'postview' and self.postviewready:
			if not self.showEPG:
				self.showEPG = True
				sref = None
				channel = ''
				if not self.search:
					for i in range(6):
						if self.oldcurrent == 'menu%s' % i: # and self.zaps[i]:
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
			if self.oldcurrent == 'searchmenu':
				c = self['searchmenu'].getSelectedIndex()
				self.oldsearchindex = c
				c = self['searchmenu'].getSelectedIndex()
				sref = self.searchref[c]
				self.redTimer(False, sref)
			else:
				sref = None
				for i in range(6):
					if self.oldcurrent == 'menu%s' % i: # and self.zaps[i]:
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
					if search('www.tvspielfilm.de', self.postlink):
						self.oldcurrent = self.current
						self.download(self.postlink, self.makePostTimer)
		elif self.current == 'searchmenu':
			c = self['searchmenu'].getSelectedIndex()
			self.oldsearchindex = c
			self.postlink = self.searchlink[c]
			if search('www.tvspielfilm.de', self.postlink):
				self.oldcurrent = self.current
				self.download(self.postlink, self.makePostTimer)

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
						titel = titel.split(', ')
						if len(titel) == 1:
							titel = titel[0].split(' ')
							titel = titel[0] + ' ' + titel[1] if titel[0].find(':') > 0 else titel[0]
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
			self['label2'].hide()
			self['label3'].hide()
			self['label4'].hide()
			self['label5'].hide()
			self.searchlink = []
			self.searchref = []
			self.searchentries = []
			self.search = True
			self.datum = False
			self.filter = True
			search = quote(search).replace('%20', '+')
			searchlink = self.baseurl + '/suche/?q=%s&tab=TV-Sendungen?page=1' % search
			self.maxsearchcount = config.plugins.tvspielfilm.maxsearch.value
			self.searchcount = 0
			self._makeSearchView(searchlink)

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
				self['seitennr'].show()
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
					self['release'].hide()
					self['waiting'].startBlinking()
					self['waiting'].show()
				self.ready = False
				self.makeTVTimer.callback.append(self.downloadFullPage(self.link))

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
			self['release'].hide()
			self['waiting'].startBlinking()
			self['waiting'].show()
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link))
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
			self['release'].hide()
			self['waiting'].startBlinking()
			self['waiting'].show()
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link))
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
			self['release'].hide()
			self['waiting'].startBlinking()
			self['waiting'].show()
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link))

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
			self['release'].hide()
			self['waiting'].startBlinking()
			self['waiting'].show()
			self.makeTVTimer.callback.append(self.downloadFullPage(self.link))

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
					self['release'].hide()
					self['waiting'].startBlinking()
					self['waiting'].show()
				self['seitennr'].show()
				self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
				self.ready = False
				self.makeTVTimer.callback.append(self.downloadFullPage(self.link))
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
					self['release'].hide()
					self['waiting'].startBlinking()
					self['waiting'].show()
				self['seitennr'].show()
				self['seitennr'].setText('Seite %s von %s' % (self.count, self.maxpages))
				self.ready = False
				self.makeTVTimer.callback.append(self.downloadFullPage(self.link))
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

	def idownloadPics(self, downloads):
		for link, idx in downloads:
			try:
				response = requests.get(link)
				response.raise_for_status()
			except requests.exceptions.RequestException as error:
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

	def downloadFullPage(self, link):
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
			reactor.callInThread(self._downloadFullPage, link)

	def _downloadFullPage(self, link):
		try:
			response = requests.get(link)
			response.raise_for_status()
		except requests.exceptions.RequestException as error:
			self.downloadPageError(error)
		else:
			with open(self.localhtml, 'wb') as f:
				f.write(response.content)
			self.makeTVHeuteView('')

	def displayError(self):
		self.session.openWithCallback(self.closeError, MessageBox, '%s' % self.error, MessageBox.TYPE_ERROR)

	def closeError(self, retval):
		self.close()

	def downloadPageError(self, output):
		TVSlog(output)
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
		if "menu" in self.current:
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
			self.showMenubar()
			self['MENUkey'].show()
			self['MENUtext'].show()
			self.hideRatingInfos()
			self.postviewready = False
			self.setTitle('')
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

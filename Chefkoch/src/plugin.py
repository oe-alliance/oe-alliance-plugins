# -*- coding: utf-8 -*-
from base64 import b64encode, b64decode
from datetime import datetime
from json import loads
from operator import itemgetter
from os import linesep, rename, remove
from random import randrange
from re import match
from requests import get, exceptions
from PIL import Image
from smtplib import SMTP, SMTP_SSL, SMTPResponseException
from time import strftime
from twisted.internet.reactor import callInThread
from xml.etree.ElementTree import tostring, parse
from six import ensure_str, ensure_binary
from six.moves.email_mime_multipart import MIMEMultipart
from six.moves.email_mime_text import MIMEText
from six.moves.email_mime_image import MIMEImage
from enigma import eListboxPythonMultiContent, eServiceReference, ePicLoad, eTimer, getDesktop, gFont, loadPNG, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigPassword, ConfigSelection, ConfigText, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean
from Components.ScrollLabel import ScrollLabel
from Components.ProgressBar import ProgressBar
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS

RELEASE = 'V2.0'
MODULE_NAME = __name__.split(".")[-1]
LINESPERPAGE = 8
PICURLBASE = 'https://img.chefkoch-cdn.de/rezepte/'
APIURIBASE = 'https://api.chefkoch.de/v2/'

config.plugins.chefkoch = ConfigSubsection()
PLUGINPATH = resolveFilename(SCOPE_PLUGINS) + 'Extensions/Chefkoch/'
if getDesktop(0).size().width() >= 1920:
	config.plugins.chefkoch.plugin_size = ConfigSelection(default='FHD', choices=[('FHD', 'FullHD (1920x1080)'), ('HD', 'HD (1280x720)')])
else:
	config.plugins.chefkoch.plugin_size = ConfigSelection(default='HD', choices=[('HD', 'HD (1280x720)')])
config.plugins.chefkoch.font_size = ConfigSelection(default='large', choices=[('large', 'Groß'), ('normal', 'Normal')])
config.plugins.chefkoch.maxrecipes = ConfigSelection(default='100', choices=['10', '20', '50', '100', '200', '500', '1000'])
config.plugins.chefkoch.maxcomments = ConfigSelection(default='100', choices=['10', '20', '50', '100', '200', '500'])
config.plugins.chefkoch.maxpictures = ConfigSelection(default='20', choices=['10', '20', '50', '100'])
config.plugins.chefkoch.mail = ConfigYesNo(default=False)
config.plugins.chefkoch.mailfrom = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.mailto = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.login = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.password = ConfigPassword(default='', fixed_size=False)
config.plugins.chefkoch.server = ConfigText(default='', fixed_size=False)
config.plugins.chefkoch.port = ConfigInteger(465, (0, 99999))
config.plugins.chefkoch.ssl = ConfigYesNo(default=True)
config.plugins.chefkoch.debuglog = ConfigYesNo(default=False)
config.plugins.chefkoch.logtofile = ConfigYesNo(default=False)
if config.plugins.chefkoch.plugin_size.value == "FHD":
	SCALE = 1.5
	SKINFILE = PLUGINPATH + "skin_FHD.xml"
else:
	SCALE = 1.0
	SKINFILE = PLUGINPATH + "skin_HD.xml"


class AllScreen(Screen):
	def __init__(self):
		pass

	def applySkinVars(self, skin, dict):
		for key in dict.keys():
			skin = skin.replace('{' + key + '}', dict[key])
		return skin

	def getAPIdata(self, apiuri, fail=None):
		f = get('%s%s' % (APIURIBASE, apiuri))
		return (f.text, f.status_code)

	def CKlog(self, info, wert="", debug=False):
		if debug and not config.plugins.chefkoch.debuglog.value:
			return
		if config.plugins.chefkoch.logtofile.value:
			try:
				with open('/home/root/logs/chefkoch.log', 'a') as f:
					f.write(strftime('%H:%M:%S') + ' %s %s\r\n' % (str(info), str(wert)))
			except IOError:
				print('[Chefkoch] Logging-Error')
		else:
			print('[Chefkoch] %s %s' % (str(info), str(wert)))

	def hideScreen(self):
		global HIDEFLAG
		if ALPHA:
			if HIDEFLAG:
				HIDEFLAG = False
				for i in range(40, -1, -1):
					with open(ALPHA, 'w') as f:
						f.write('%i' % (config.av.osd_alpha.value * i / 40))
			else:
				HIDEFLAG = True
				for i in range(41):
					with open(ALPHA, 'w') as f:
						f.write('%i' % (config.av.osd_alpha.value * i / 40))

	def readSkin(self, skin):
		skintext = ""
		try:
			with open(SKINFILE, "r") as fd:
				try:
					domSkin = parse(fd).getroot()
					for element in domSkin:
						if element.tag == "screen" and element.attrib['name'] == skin:
							skintext = ensure_str(tostring(element))
							break
				except Exception as err:
					print("[Skin] Error: Unable to parse skin data in '%s' - '%s'!" % (SKINFILE, err))
		except OSError as err:
			print("[Skin] Error: Unexpected error opening skin file '%s'! (%s)" % (SKINFILE, err))
		return skintext


class CKview(AllScreen):
	def __init__(self, session, query, titel, sort, fav, zufall):
		global HIDEFLAG
		HIDEFLAG = True
		fontsize = '%d' % int(22 * SCALE) if config.plugins.chefkoch.font_size.value == 'large' else '%d' % int(20 * SCALE)
		self.dict = {'picpath': PLUGINPATH + 'pic/', 'fontsize': fontsize}
		skin = self.readSkin("CKview")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session, skin)
		self.REZ = None
		self.session = session
		self.query = query
		self.titel = titel
		self.sort = sort
		self.fav = fav
		self.zufall = zufall
		self.sortname = ['{keine}', 'Anzahl Bewertungen', 'Anzahl Sterne', 'mit Video', 'Erstelldatum']
		self.orgGRP = []
		self.KOM = []
		self.picfile = '/tmp/chefkoch.jpg'
		self.currItem = 0
		self.rezept = 'https://www.chefkoch.de/rezepte/'
		self.rezeptfile = '/tmp/Rezept.html'
		self.ready = False
		self.postviewready = False
		self.comment = False
		self.len = 0
		self.count = 0
		self.maxPage = 0
		self.current = 'menu'
		self.name = ''
		self.chefvideo = ''
		self.kochentries = []
		self.kochId = []
		self.picurllist = []
		self.titellist = []
		self.videolist = []
		self.rezeptelist = []
		self.rezeptelinks = []
		self.pic = []
		for i in range(LINESPERPAGE):
			self['pic%d' % i] = Pixmap()
			self['vid%d' % i] = Pixmap()
			self['pic%d' % i].hide()
			self['vid%d' % i].hide()
			self.pic.append('/tmp/chefkoch%d.jpg' % i)
		self['postpic'] = Pixmap()
		self['postvid'] = Pixmap()
		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self['scoretext'] = Label('')
		self['scoretext'].hide()
		self['recipetext'] = Label('')
		self['recipetext'].hide()
		self['button_green'] = Pixmap()
		self['button_red'] = Pixmap()
		self['button_yellow'] = Pixmap()
		self['button_blue'] = Pixmap()
		self['textpage'] = ScrollLabel('')
		self['textpage'].hide()
		self['menu'] = ItemList([])
		self['button_green'].hide()
		self['button_yellow'].hide()
		self['button_red'].hide()
		self['button_blue'].hide()
		self['label_red'] = Label('')
		self['label_green'] = Label('')
		self['label_yellow'] = Label('')
		self['label_blue'] = Label('')
		self['label_rezeptnr'] = Label('')
		self['label_1-0'] = Label('')
		self['label_1-0'].hide()
		self['button_1-0'] = Pixmap()
		self['button_1-0'].hide()
		self['pageinfo'] = Label('')
		self['pageinfo'].hide()
		self['label_ok'] = Label('')
		self['label_ok'].hide()
		self['button_ok'] = Pixmap()
		self['button_ok'].hide()
		self['postvid'].hide()
		self['label_play'] = Label('')
		self['label_play'].hide()
		self['button_play'] = Pixmap()
		self['button_play'].hide()
		self['Line_Bottom'] = Label('')
		self['Line_Bottom'].hide()
		self['release'] = Label(RELEASE)
		self['helpactions'] = ActionMap(['HelpActions'], {'displayHelp': self.infoScreen}, -1)
		self['NumberActions'] = NumberActionMap(['NumberActions', 'OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'ButtonSetupActions'], {
			'ok': self.ok,
			'cancel': self.exit,
			'play': self.playVideo,
			'playpause': self.playVideo,
			'right': self.nextPage,
			'left': self.prevPage,
			'down': self.down,
			'up': self.up,
			'nextBouquet': self.nextPage,
			'prevBouquet': self.prevPage,
			'red': self.red,
			'yellow': self.yellow,
			'green': self.green,
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
			'9': self.gotoPage,
		}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)
		self.postpicload = ePicLoad()
		self.prevpicload = []
		for i in range(LINESPERPAGE):
			self.prevpicload.append(ePicLoad())

	def onLayoutFinished(self):
		self.postpicload.setPara((self['postpic'].instance.size().width(), self['postpic'].instance.size().height(), 1.0, 0, False, 1, "#00000000"))
		xres = self['pic0'].instance.size().width()
		yres = self['pic0'].instance.size().height()
		for i in range(LINESPERPAGE):
			self.prevpicload[i].setPara((xres, yres, 1.0, 0, False, 1, "#00000000"))
		if self.zufall:
			self.current = 'postview'
			self.GRP = self.getGRP()
			self.maxPage = (len(self.GRP) - 1) // LINESPERPAGE + 1
			zufallsId = self.GRP[randrange(0, len(self.GRP))]['id']
			callInThread(self.makePostviewPage, zufallsId)
		elif self.fav:
			self.current = 'postview'
			callInThread(self.makePostviewPage, self.query)
		else:
			self.current = 'menu'
			callInThread(self.makeChefkoch)

	def makeChefkoch(self):  # erzeuge Rezeptliste
		for i in range(LINESPERPAGE):
			self['pic%d' % i].hide()
			self['vid%d' % i].hide()
		self.GRP = self.getGRP()
		self.maxPage = (len(self.GRP) - 1) // LINESPERPAGE + 1
		self.kochentries = []
		self.kochId = []
		self.picurllist = []
		self.titellist = []
		self.videolist = []
		self['postvid'].hide()
		self['button_green'].hide()
		self['button_yellow'].hide()
		self['button_red'].show()
		self['button_blue'].show()
		self['label_red'].setText('Rezept zu Favoriten')
		self['label_green'].setText('Sortierung: %s' % self.sortname[self.sort])
		self['label_yellow'].setText('Suche')
		self['label_blue'].setText('Ein-/Ausblenden')
		self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
		self['label_1-0'].setText('')
		self['button_1-0'].hide()
		self['postvid'].hide()
		self['label_play'].setText('Video abspielen')
		self['label_play'].hide()
		self['button_play'].hide()
		self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))
		self['pageinfo'].show()
		self['label_ok'].setText('zum Rezept')
		self['label_ok'].show()
		self['button_ok'].show()
		self.headline = str(len(self.GRP)) + ' ' + self.titel.replace(' Rezepte', '') + ' Rezepte ('
		self.headline += '1 Video)' if self.videocount == 1 else str(self.videocount) + ' Videos)'
		self.setTitle(str(self.headline))
		for i in range(len(self.GRP)):
			id = str(self.GRP[i]['id'])
			titel = self.GRP[i]['title']
			time = str(self.GRP[i]['preparationTime'])
			if self.GRP[i]['numVotes']:
				count = str(self.GRP[i]['numVotes'])
				score = str(round(self.GRP[i]['rating'] / 5, 1) * 5).replace('.', '_').replace('_0', '')
			else:
				count = 'keine'
				score = '0'
			if self.GRP[i]['previewImageId']:
				picurl = PICURLBASE + id + '/bilder/' + str(self.GRP[i]['previewImageId']) + '/crop-160x120/' + titel.replace(' ', '-') + '.jpg'
			else:
				picurl = 'http://img.chefkoch-cdn.de/img/default/layout/recipe-nopicture.jpg'
			text = self.GRP[i]['subtitle']
			if len(text) > 155:
				text = text[:155] + '…'
			self.kochId.append(id)
			self.picurllist.append(picurl)
			self.titellist.append(titel)
			self.videolist.append(self.GRP[i]['hasVideo'])
			res = [i]
			res.append(MultiContentEntryText(pos=(int(110 * SCALE), 10), size=(int(965 * SCALE), int(30 * SCALE)), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titel))  # TITLE
			if config.plugins.chefkoch.plugin_size.value == 'FHD':
				png = PLUGINPATH + 'pic/FHD/smallFHD-%s.png' % score
			else:
				png = PLUGINPATH + 'pic/HD/smallHD-%s.png' % score
			if fileExists(png):
				res.append(MultiContentEntryPixmapAlphaTest(pos=(int(14 * SCALE), int(36 * SCALE)), size=(int(75 * SCALE), int(15 * SCALE)), png=loadPNG(png)))  # STARS
			res.append(MultiContentEntryText(pos=(int(11 * SCALE), int(52 * SCALE)), size=(int(75 * SCALE), int(30 * SCALE)), font=1, color=16777215, color_sel=16777215,
                                    		 flags=RT_HALIGN_CENTER, text='(' + count + ')'))  # COUNT
			res.append(MultiContentEntryText(pos=(int(111 * SCALE), int(45 * SCALE)), size=(int(965 * SCALE), int(70 * SCALE)),
											 font=-1, color=10857646, color_sel=13817818, flags=RT_HALIGN_LEFT | RT_WRAP, text=text))  # TEXT
			res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(6 * SCALE)), size=(int(75 * SCALE), int(26 * SCALE)), font=0, backcolor=3899463,
											 color=16777215, backcolor_sel=15704383, color_sel=16777215, flags=RT_HALIGN_CENTER, text=time))  # TIME
			self.kochentries.append(res)
		self.setPrevIcons(0)
		self.len = len(self.kochentries)
		self['menu'].l.setItemHeight(int(75 * SCALE))
		self['menu'].l.setList(self.kochentries)
		self['menu'].moveToIndex(0)
		self.ready = True

	def formatDatum(self, date):
		return str(datetime.strptime(date[:10], '%Y-%m-%d').strftime('%d.%m.%Y'))

	def formatDatumZeit(self, date):
		datum = datetime.strptime(date[:10], '%Y-%m-%d').strftime('%d.%m.%Y')
		zeit = datetime.strptime(date[11:19], '%H:%M:%S').strftime('%H:%M')
		return 'vom ' + str(datum) + ' um ' + str(zeit)

	def formatUsername(self, username, rank, trim):
		return 'Unbekannt' if "unknown" in username else (str(username) + ' (' + str(rank) + '*)')[:trim if trim > 0 else 100]

	def makePostviewPage(self, Id):  # erzeuge eigentliches Rezept
		self.currId = Id
		for i in range(LINESPERPAGE):
			self['pic%d' % i].hide()
			self['vid%d' % i].hide()
		self['menu'].hide()
		self['button_green'].hide()
		self['button_yellow'].hide()
		self['button_red'].show()
		self['button_blue'].show()
		self['label_green'].setText('Rezept per Email')
		self['label_red'].setText('Rezept zu Favoriten')
		self['label_yellow'].setText('')
		self['label_blue'].setText('Ein-/Ausblenden')
		self['label_rezeptnr'].setText('')
		self['label_1-0'].setText('')
		self['button_1-0'].hide()
		self['pageinfo'].hide()
		self['label_ok'].setText('zum Rezept')
		self['label_ok'].show()
		self['button_ok'].show()
		self['postvid'].hide()
		self['label_play'].hide()
		self['button_play'].hide()
		self['Line_Bottom'].hide()
		self['textpage'].setText('')
		self['textpage'].show()
		self.REZ = self.getREZ(self.currId)
		if self.REZ['rating']:
			score = self.REZ['rating']['rating'] * 20
			scoretext = str('%1.1f' % self.REZ['rating']['rating']) + ' (' + str(self.REZ['rating']['numVotes']) + ' Bewertungen)'
		else:
			score = 0.0
			scoretext = '(ohne Bewertung)'
		preptime = self.REZ['preparationTime']
		cooktime = self.REZ['cookingTime']
		resttime = self.REZ['restingTime']
		totaltime = self.REZ['totalTime']
		self.picCount = self.REZ['imageCount']
		self.setTitle(str(self.REZ['title']))
		if preptime != 0:
			scoretext += '\nArbeitszeit\t: %s' % self.getTimeString(preptime)
		if cooktime != 0:
			scoretext += '\nKoch-/Backzeit\t: %s' % self.getTimeString(cooktime)
		if resttime != 0:
			scoretext += '\nRuhezeit\t: %s' % self.getTimeString(resttime)
		if totaltime != 0:
			scoretext += '\nGesamtzeit\t: %s' % self.getTimeString(totaltime)
		self["starsbg"].show()
		self["stars"].show()
		self["stars"].setValue(score)
		self['scoretext'].setText(scoretext)
		self['scoretext'].show()
		effort = ['keiner', 'simpel', 'normal', 'pfiffig']
		recipetext = 'Rezept-Identnr.\t: ' + str(self.currId)
		recipetext += '\nAufwand\t: ' + effort[self.REZ['difficulty']]
		recipetext += '\nErstellername\t: ' + self.formatUsername(self.REZ['owner']['username'], self.REZ['owner']['rank'], 22)
		recipetext += '\nErstelldatum\t: ' + self.formatDatum(self.REZ['createdAt'])
		if self.REZ['nutrition']:
			kcalori = self.REZ['nutrition']['kCalories']
			if kcalori:
				kcalori = '%s' % kcalori
			else:
				kcalori = 'k.A.'
			protein = self.REZ['nutrition']['proteinContent']
			if protein:
				protein = '%s g' % protein
			else:
				protein = 'k.A.'
			fatcont = self.REZ['nutrition']['fatContent']
			if fatcont:
				fatcont = '%s g' % fatcont
			else:
				fatcont = 'k.A.'
			carbohyd = self.REZ['nutrition']['carbohydrateContent']
			if carbohyd:
				carbohyd = '%s g' % carbohyd
			else:
				carbohyd = 'k.A.'
			recipetext += '\n\n{0:13}{1:13}{2:14}{3}'.format('kcal', 'Eiweiß', 'Fett', 'Kohlenhydr.')
			recipetext += '\n{0:13}{1:13}{2:12}{3}'.format(kcalori, protein, fatcont, carbohyd)
		self['recipetext'].setText(str(recipetext))
		self['recipetext'].show()
		self['Line_Bottom'].show()
		if self.REZ['hasImage']:
			picurl = PICURLBASE + self.currId + '/bilder/' + self.REZ['previewImageId'] + '/crop-960x720/' + self.titel + '.jpg'
		else:
			picurl = 'https://img.chefkoch-cdn.de/img/default/layout/recipe-nopicture.jpg'
		callInThread(self.threadedGetPage, picurl, self.getPostPic, self.downloadError)
		self.postpicload.PictureData.get().append(self.showPostPic)
		self['postpic'].show()
		self.IMG = self.getIMG(self.currId)
		if self.picCount == 1:
			self['label_ok'].setText('Vollbild')
		elif self.picCount > 1:
			self['label_ok'].setText('%d Rezeptbilder' % (self.IMGlen))
		else:
			self['label_ok'].setText('')
			self['button_ok'].hide()
		self.KOM = self.getKOM(self.currId)
		self.makeRezept()
		self.postviewready = True

	def getREZ(self, id):  # hole den jeweiligen Rezeptdatensatz
		content, resp = self.getAPIdata('recipes/' + id)
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
			self.close()
			return {}
		else:
			return loads(content)

	def getIMG(self, id):  # hole die jeweilige Rezeptbilderliste
		content, resp = self.getAPIdata('recipes/' + id + '/images?&offset=0&limit=' + config.plugins.chefkoch.maxpictures.value)
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
			self.close()
			return {}
		else:
			result = loads(content)
			self.IMGlen = int(config.plugins.chefkoch.maxpictures.value) if result['count'] > int(config.plugins.chefkoch.maxpictures.value) else result['count']
			dict = {}
			dict['count'] = self.IMGlen
			dict['results'] = result['results']
			return dict

	def getKOM(self, id):  # hole die jeweilige Rezeptkommentarliste
		content, resp = self.getAPIdata('recipes/' + id + '/comments?&offset=0&limit=' + config.plugins.chefkoch.maxcomments.value)
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
			self.close()
			return {}
		else:
			result = loads(content)
			self.KOMlen = int(config.plugins.chefkoch.maxcomments.value) if result['count'] > int(config.plugins.chefkoch.maxcomments.value) else result['count']
			return result

	def getGRP(self):  # hole die gewünschte Rezeptgruppe (alle Rezepte, davon 'videocount' mit Video)
		if not self.orgGRP:
			limit = int(config.plugins.chefkoch.maxrecipes.value)
			videocount = 0
			for i in range(max((limit) // 100, 1)):
				content, resp = self.getAPIdata('recipes?query=%s&offset=%d&limit=%d' % (self.query, i * 100, min(limit, 100)))
				if resp != 200:
					self.session.openWithCallback(self.eject, MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
					self.close()
					return []
				result = loads(content)
				for j in range(len(result['results'])):
					if result['results'][j]['recipe']['isRejected']:
						continue
					dict = {}
					dict['id'] = result['results'][j]['recipe']['id']
					dict['createdAt'] = result['results'][j]['recipe']['createdAt']
					dict['preparationTime'] = result['results'][j]['recipe']['preparationTime']
					if result['results'][j]['recipe']['rating']:
						dict['rating'] = result['results'][j]['recipe']['rating']['rating']
						dict['numVotes'] = result['results'][j]['recipe']['rating']['numVotes']
					else:
						dict['rating'] = 0
						dict['numVotes'] = False
					if result['results'][j]['recipe']['hasImage']:
						dict['previewImageId'] = result['results'][j]['recipe']['previewImageId']
					else:
						dict['previewImageId'] = False
					dict['hasVideo'] = result['results'][j]['recipe']['hasVideo']
					titel = str(result['results'][j]['recipe']['title'])
					dict['title'] = titel
					dict['subtitle'] = str(result['results'][j]['recipe']['subtitle'])
					if result['results'][j]['recipe']['hasVideo']:
						videocount += 1
					self.orgGRP.append(dict)
			self.videocount = videocount
		if self.sort == 0:
			return self.orgGRP
		elif self.sort == 1:
			return sorted(self.orgGRP, key=itemgetter('numVotes'), reverse=True)
		elif self.sort == 2:
			return sorted(self.orgGRP, key=itemgetter('rating'), reverse=True)
		elif self.sort == 3:
			return sorted(self.orgGRP, key=itemgetter('hasVideo', 'numVotes'), reverse=True)
		elif self.sort == 4:
			return sorted(self.orgGRP, key=itemgetter('createdAt'), reverse=True)

	def getTimeString(self, duration):
		days = duration // 1440
		hours = duration // 60
		minutes = duration % 60
		if days == 0:
			daytext = ''
			hourtext = 'ca. %s h' % hours if hours != 0 else ''
			minutetext = '%s min' % minutes if minutes != 0 else ''
		else:
			daytext = '%s Tage' % days if days > 1 else '1 Tag'
			hourtext = ''
			minutetext = ''
		ausgabe = '%s %s %s' % (daytext, hourtext, minutetext)
		return ausgabe

	def ok(self):
		if HIDEFLAG:
			if self.current == 'menu':
				self.selectPage()
			elif self.current == 'postview' and self.postviewready:
				if self.picCount == 1:
					self.session.openWithCallback(self.showPostPic, CKfullscreen)
				if self.picCount > 1:
					self.session.openWithCallback(self.returnPicShow, CKpicshow, self.titel, self.REZ, self.IMG)

	def selectPage(self):
		if self.ready:
			self.current = 'postview'
			self.currItem = self['menu'].getSelectedIndex()
			self.currId = '%s%s' % ('recipes/', self.kochId[self.currItem])
			callInThread(self.makePostviewPage, self.kochId[self.currItem])

	def red(self):
		if self.ready or self.postviewready:
			if not self.zufall:
				self.currItem = self['menu'].getSelectedIndex()
				name = self.titellist[self.currItem]
			else:
				name = self.name
			self.session.openWithCallback(self.red_return, MessageBox, "\nRezept '%s' zu den Favoriten hinzufügen?" % name, MessageBox.TYPE_YESNO)

	def red_return(self, answer):
		if answer is True:
			favoriten = PLUGINPATH + 'db/favoriten'
			if not self.zufall:
				self.currItem = self['menu'].getSelectedIndex()
				data = self.titellist[self.currItem] + ':::' + self.kochId[self.currItem]
			else:
				data = self.name + ':::' + self.kochId[self.currItem]
			with open(favoriten, 'a') as f:
				f.write(data)
				f.write(linesep)
			self.session.open(CKfavoriten)

	def green(self):
		if self.current == 'postview' and self.postviewready:
			if config.plugins.chefkoch.mail.value:
				mailto = config.plugins.chefkoch.mailto.value.split(",")
				mailto = [(i.strip(),) for i in mailto]
				self.session.openWithCallback(self.green_return, ChoiceBox, title='Rezept an folgende E-mail Adresse senden:', list=mailto)
			else:
				self.session.open(MessageBox, '\nDie E-mail Funktion ist nicht aktiviert. Aktivieren Sie die E-mail Funktion im Setup des Plugins.', MessageBox.TYPE_INFO, close_on_any_key=True)
		if self.current == 'menu':
			self.sort = self.sort + 1 if self.sort < len(self.sortname) - 1 else 0
			self.currItem = 0
			callInThread(self.makeChefkoch)

	def green_return(self, answer):
		if answer:
			self.sendRezept(answer[0])

	def sendRezept(self, mailTo):
		effort = ['keine', 'simpel', 'normal', 'pfiffig']
		msgText = '\n'
		msgText = '<p>Linkadresse: <a href="' + self.rezept + self.currId + '">' + self.rezept + self.currId + '</a></p>'
		if self.REZ['rating']:
			scoretext = str('%1.1f' % self.REZ['rating']['rating']) + ' (' + str(self.REZ['rating']['numVotes']) + ' Bewertungen)'
		else:
			scoretext = '(ohne Bewertung)'
		preptime = self.REZ['preparationTime']
		cooktime = self.REZ['cookingTime']
		resttime = self.REZ['restingTime']
		totaltime = self.REZ['totalTime']
		if preptime != 0:
			scoretext += '\nArbeitszeit   : %s' % self.getTimeString(preptime)
		if cooktime != 0:
			scoretext += '\nKoch-/Backzeit: %s' % self.getTimeString(cooktime)
		if resttime != 0:
			scoretext += '\nRuhezeit      : %s' % self.getTimeString(resttime)
		if totaltime != 0:
			scoretext += '\nGesamtzeit    : %s' % self.getTimeString(totaltime)
		msgText += scoretext
		recipetext = '\n\nRezept-Identnr.: ' + str(self.currId)
		recipetext += '\nAufwand: ' + effort[self.REZ['difficulty']]
		recipetext += '\nErstellername: ' + self.formatUsername(self.REZ['owner']['username'], self.REZ['owner']['rank'], 22)
		recipetext += '\nErstelldatum: ' + self.formatDatum(self.REZ['createdAt'])
		if self.REZ['nutrition']:
			kcalori = self.REZ['nutrition']['kCalories']
			if kcalori:
				kcalori = str(kcalori)
			else:
				kcalori = 'k.A.'
			protein = self.REZ['nutrition']['proteinContent']
			if protein:
				protein = str(protein) + 'g'
			else:
				protein = 'k.A.'
			fatcont = self.REZ['nutrition']['fatContent']
			if fatcont:
				fatcont = str(fatcont) + 'g'
			else:
				fatcont = 'k.A.'
			carbohyd = self.REZ['nutrition']['carbohydrateContent']
			if carbohyd:
				carbohyd = str(carbohyd) + 'g'
			else:
				carbohyd = 'k.A.'
			recipetext += '\n\nkcal  Eiweiß  Fett  Kohlenhydr.'
			recipetext += '\n' + str(kcalori) + ' ' + str(protein) + ' ' + str(fatcont) + ' ' + str(carbohyd)
		msgText += recipetext + '\n\n'
		if self.REZ['subtitle']:
			msgText += 'BESCHREIBUNG: ' + self.REZ['subtitle'] + '\n\n'
		msgText += 'ZUTATEN\n'
		for i in range(len(self.REZ['ingredientGroups'])):
			for j in range(len(self.REZ['ingredientGroups'][i]['ingredients'])):
				if not (i == 0 and j == 0):
					msgText += '; '
				if self.REZ['ingredientGroups'][i]['ingredients'][j]['amount'] != 0:
					msgText += str(self.REZ['ingredientGroups'][i]['ingredients'][j]['amount']).replace('.0', '') + ' '
					msgText += self.REZ['ingredientGroups'][i]['ingredients'][j]['unit'] + ' '
				msgText += self.REZ['ingredientGroups'][i]['ingredients'][j]['name']
				msgText += self.REZ['ingredientGroups'][i]['ingredients'][j]['usageInfo']
		msgText += '\n\nZUBEREITUNG\n' + self.REZ['instructions']
		msgText += '\n' + '_' * 30 + '\nChefkoch.de'
		Image.open('/tmp/chefkoch.jpg').resize((320, 240), Image.ANTIALIAS).save('/tmp/emailpic.jpg')

		mailFrom = ensure_str(config.plugins.chefkoch.mailfrom.value.encode('ascii', 'xmlcharrefreplace'))
		mailTo = ensure_str(mailTo.encode('ascii', 'xmlcharrefreplace'))
		mailLogin = ensure_str(config.plugins.chefkoch.login.value.encode('ascii', 'xmlcharrefreplace'))
		mailPassword = ensure_str(b64decode(config.plugins.chefkoch.password.value.encode('ascii', 'xmlcharrefreplace')))
		mailServer = ensure_str(config.plugins.chefkoch.server.value.encode('ascii', 'xmlcharrefreplace'))
		mailPort = config.plugins.chefkoch.port.value
		msgRoot = MIMEMultipart('related')
		msgRoot['Subject'] = 'Chefkoch.de: %s' % self.titel
		msgRoot['From'] = mailFrom
		msgRoot['To'] = mailTo  # bei Bedarf ergänzbar: msgRoot['Cc'] =cc
		msgRoot.preamble = 'Multi-part message in MIME format.'
		msgAlternative = MIMEMultipart('alternative')
		msgRoot.attach(msgAlternative)
		msgAlternative.attach(MIMEText(msgText, _subtype='plain', _charset='UTF-8'))
		msgHeader = '"' + self.titel + '" gesendet vom Plugin "Chefkoch.de"'
		msgText = ensure_str(msgText.replace('\n', '<br>').encode('ascii', 'xmlcharrefreplace'))
		msgAlternative.attach(MIMEText('<b>' + msgHeader + '</b><br><br><img src="cid:0"><br>' + msgText, 'html'))
		with open('/tmp/emailpic.jpg', 'rb') as img:
			msgImage = MIMEImage(img.read(), _subtype="jpeg")
		msgImage.add_header('Content-ID', '<0>')
		msgRoot.attach(msgImage)
		try:
			if config.plugins.chefkoch.ssl.value:
				server = SMTP_SSL(mailServer, mailPort)
			else:
				server = SMTP(mailServer, mailPort)
			server.login(mailLogin, mailPassword)
			server.sendmail(mailFrom, mailTo, msgRoot.as_string())
			server.quit()
			self.session.open(MessageBox, 'E-mail erfolgreich gesendet an: %s' % mailTo, MessageBox.TYPE_INFO, close_on_any_key=True)
		except SMTPResponseException as err:
			self.CKlog('SMTP_Response_Exception Error:', err)
			self.session.open(MessageBox, 'E-mail konnte aufgrund eines Serverproblems nicht gesendet werden: \n%s' % str(err), MessageBox.TYPE_INFO, close_on_any_key=True)

	def nextPage(self):
		if self.current == 'menu':
			self.currItem = self['menu'].getSelectedIndex()
			offset = self.currItem % LINESPERPAGE
			if self.currItem + LINESPERPAGE > self.len - 1:
				if offset > (self.len - 1) % LINESPERPAGE:
					self.currItem = self.len - 1
					self['menu'].moveToIndex(self.currItem)  # springe auf letzten Eintrag der letzten Seite
					self.setPrevIcons(self.currItem - offset)
				else:
					self.currItem = offset
					self['menu'].moveToIndex(self.currItem)  # springe auf gleichen Offset der ersten Seite
					self.setPrevIcons(0)
			else:
				self.currItem = self.currItem + LINESPERPAGE
				self['menu'].pageDown()
				self.setPrevIcons(self.currItem - offset)
			self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
			self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))
		else:
			self['textpage'].pageDown()

	def prevPage(self):
		if self.current == 'menu':
			self.currItem = self['menu'].getSelectedIndex()
			offset = self.currItem % LINESPERPAGE
			lasttop = (self.len - 1) // LINESPERPAGE * LINESPERPAGE
			if self.currItem - LINESPERPAGE < 0:
				if offset > (self.len - 1) % LINESPERPAGE:
					self.currItem = self.len - 1
					self['menu'].moveToIndex(self.currItem)  # springe auf gleichen Offset der vorherigen Seite
				else:
					self.currItem = lasttop + offset
					self['menu'].moveToIndex(self.currItem)  # springe auf letzten Eintrag der letzten Seite
				self.setPrevIcons(lasttop)
			else:
				self.currItem = self.currItem - LINESPERPAGE
				self['menu'].pageUp()
				self.setPrevIcons(self.currItem - offset)
			self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
			self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))
		else:
			self['textpage'].pageUp()

	def down(self):
		if self.current == 'menu':
			self['menu'].down()
			self.currItem = self['menu'].getSelectedIndex()
			self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
			self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))
			if self.currItem == self.len:  # neue Vorschaubilder der ersten Seite anzeigen
				self.setPrevIcons(0)
			if self.currItem % LINESPERPAGE == 0:  # neue Vorschaubilder der nächsten Seite anzeigen
				self.setPrevIcons(self.currItem)
		else:
			self['textpage'].pageDown()

	def up(self):
		if self.current == 'menu':
			self['menu'].up()
			self.currItem = self['menu'].getSelectedIndex()
			self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
			self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))
			if self.currItem == self.len - 1:  # neue Vorschaubilder der letzte Seite anzeigen
				d = self.len % LINESPERPAGE if self.len % LINESPERPAGE != 0 else LINESPERPAGE
				self.setPrevIcons(self.len - d)
			if self.currItem % LINESPERPAGE == LINESPERPAGE - 1:  # neue Vorschaubilder der vorherige Seite anzeigen
				self.setPrevIcons(self.currItem // LINESPERPAGE * LINESPERPAGE)
		else:
			self['textpage'].pageUp()

	def gotoPage(self, number):
		if self.current != 'postview' and self.ready:
			self.session.openWithCallback(self.numberEntered, getNumber, number, 5)
		elif self.current == 'postview':
			if number == 0:
				self['textpage'].lastPage()
			elif number == 1:
				if self.comment:
					self.makeKommentar()
				else:
					self.makeRezept()

	def numberEntered(self, number):
		if number and number != 0:
			count = int(number)
			if count > self.maxPage:
				count = self.maxPage
				self.session.open(MessageBox, '\nNur %s Seiten verfügbar. Gehe zu Seite %s.' % (str(count), str(count)), MessageBox.TYPE_INFO, close_on_any_key=True)
			self.currItem = (count - 1) * LINESPERPAGE
			self['menu'].moveToIndex(self.currItem)
			self.setPrevIcons(self.currItem)
			self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
			self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))

	def setPrevIcons(self, toppos):
		self.pic = []
		for i in range(LINESPERPAGE):
			self.pic.append('/tmp/chefkoch%d.jpg' % i)
			if len(self.picurllist) > toppos + i:
				self.prevpicload[i].PictureData.get().append(self.showPrevPic)
				self.Idownload(i, self.picurllist[toppos + i], self.getPrevPic)
				self['pic%d' % i].show()
				if self.videolist[toppos + i]:
					self['vid%d' % i].show()
				else:
					self['vid%d' % i].hide()
			else:
				self['pic%d' % i].hide()
				self['vid%d' % i].hide()

	def yellow(self):
		if self.current == 'menu':
			self.currItem = self['menu'].getSelectedIndex()
			self.session.open(CKfavoriten, False)
		elif self.current == 'postview' and self.postviewready:
			if self.KOMlen > 0:
				if self.comment:
					self.comment = False
					self.makeRezept()
				else:
					self.comment = True
					self.makeKommentar()

	def makeKommentar(self):
		self.postviewready = False
		self['label_yellow'].setText('Beschreibung einblenden')
		self['label_1-0'].setText('Erster/Letzer Kommentar')
		self['label_1-0'].show()
		self['button_1-0'].show()
		self['label_ok'].setText('%d Rezeptbilder' % (self.IMGlen))
		self['button_ok'].show()
		self['pageinfo'].hide()
		self['textpage'].setText('')
		text = ''
		for i in range(self.KOMlen):
			text += 'Kommentar %s/%s' % (i + 1, self.KOMlen) + ' von '
			text += self.formatUsername(self.KOM['results'][i]['owner']['username'], self.KOM['results'][i]['owner']['rank'], 0)
			text += ' %s Uhr\n' % self.formatDatumZeit(self.KOM['results'][i]['createdAt'])
			text += self.KOM['results'][i]['text']
			if config.plugins.chefkoch.plugin_size.value == 'FHD':
				repeat = 102 if config.plugins.chefkoch.font_size.value == 'large' else 109
				text += '\n%s\n' % ('_' * repeat)
			else:
				repeat = 96 if config.plugins.chefkoch.font_size.value == 'large' else 105
				text += '\n%s\n' % ('_' * repeat)
		text += '\nChefkoch.de'
		self['textpage'].setText(str(text))
		self.postviewready = True

	def makeRezept(self):  # bereite die eigentliche Rezeptseite vor
		self.postviewready = False
		self['button_green'].show()
		self['label_green'].setText('Rezept per Email')
		self['label_1-0'].setText('')
		self['button_1-0'].hide()
		self['pageinfo'].setText('')
		if self.KOMlen > 0:
			self['label_yellow'].setText('%s Kommentare einblenden' % self.KOMlen)
			self['button_yellow'].show()
		else:
			self['label_yellow'].setText('')
			self['button_yellow'].hide()
		self['label_rezeptnr'].setText('')
		self['label_ok'].setText('%d Rezeptbilder' % (self.IMGlen))
		self['button_ok'].show()
		self['textpage'].setText('')
		if self.REZ['hasVideo']:
			self['postvid'].show()
			self['label_play'].show()
			self['button_play'].show()
		else:
			self['postvid'].hide()
			self['label_play'].hide()
			self['button_play'].hide()
		text = ''
		if self.REZ['subtitle']:
			text += 'BESCHREIBUNG: ' + self.REZ['subtitle'] + '\n\n'
		text += 'ZUTATEN\n'
		for i in range(len(self.REZ['ingredientGroups'])):
			for j in range(len(self.REZ['ingredientGroups'][i]['ingredients'])):
				if not (i == 0 and j == 0):
					text += '; '
				if self.REZ['ingredientGroups'][i]['ingredients'][j]['amount'] != 0:
					text += str(self.REZ['ingredientGroups'][i]['ingredients'][j]['amount']).replace('.0', '') + ' '
					text += self.REZ['ingredientGroups'][i]['ingredients'][j]['unit'] + ' '
				text += self.REZ['ingredientGroups'][i]['ingredients'][j]['name']
				text += self.REZ['ingredientGroups'][i]['ingredients'][j]['usageInfo']
		text += '\n\nZUBEREITUNG\n' + self.REZ['instructions']
		if config.plugins.chefkoch.plugin_size.value == 'FHD':
			repeat = 102 if config.plugins.chefkoch.font_size.value == 'large' else 109
		else:
			repeat = 96 if config.plugins.chefkoch.font_size.value == 'large' else 105
		text += '\n%s\nChefkoch.de' % ('_' * repeat)
		self['textpage'].setText(str(text))
		self.postviewready = True

	def getPrevPic(self, picdata, i):
		with open(self.pic[i], 'wb') as f:
			f.write(picdata)
		self.prevpicload[i].startDecode(self.pic[i])

	def showPrevPic(self, picInfo=None):
		if picInfo:
			i = int(match('/tmp/chefkoch(\d.*).jpg', picInfo).groups()[0])
			ptr = self.prevpicload[i].getData()
			if ptr:
				self['pic%d' % i].instance.setPixmap(ptr.__deref__())

	def getPostPic(self, picdata):
		with open(self.picfile, 'wb') as f:
			f.write(picdata)
		self.postpicload.startDecode(self.picfile)

	def showPostPic(self, picInfo=None):
		ptr = self.postpicload.getData()
		if ptr:
			self['postpic'].instance.setPixmap(ptr.__deref__())

	def Idownload(self, idx, link, success):  # PrevPic-Download
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		callInThread(self._Idownload, idx, link, success)

	def _Idownload(self, idx, link, success):
		try:
			response = get(link)
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.downloadError(error)
		else:
			success(response.content, idx)

	def threadedGetPage(self, link, success, fail=None):
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		try:
			response = get(ensure_binary(link))
			response.raise_for_status()
			success(response.content)
		except exceptions.RequestException as error:
			if fail is not None:
				fail(error)

	def downloadError(self, output):
		self.CKlog(output)

	def showProgrammPage(self):  # zeige Rezeptliste
		self.current = 'menu'
		self['button_green'].hide()
		self['button_yellow'].hide()
		self['button_red'].show()
		self['button_blue'].show()
		self['label_red'].setText('Rezept zu Favoriten')
		self['label_green'].setText('Sortierung: %s' % self.sortname[self.sort])
		self['label_yellow'].setText('Suche')
		self['label_blue'].setText('Ein-/Ausblenden')
		self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
		self['label_1-0'].setText('')
		self['button_1-0'].hide()
		self['label_ok'].setText('zum Rezept')
		self['label_ok'].show()
		self['button_ok'].show()
		self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))
		self['scoretext'].hide()
		self['recipetext'].hide()
		self['textpage'].hide()
		self['postpic'].hide()
		self['menu'].show()
		self.currItem = self['menu'].getSelectedIndex()
		self.setPrevIcons(self.currItem - self.currItem % LINESPERPAGE)

	def returnPicShow(self):
		pass

	def returnVideo(self):
		self.ready = True

	def infoScreen(self):
		pass

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def eject(self, answer):
		self.exit()

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.current == 'menu':
			self.close()
		elif self.fav:
			self.close()
		elif self.current == 'postview' and self.zufall:
			self.close()
		elif self.current == 'postview' and not self.zufall:
			self['label_ok'].setText('zum Rezept')
			self['label_1-0'].setText('')
			self['button_1-0'].hide()
			self['postvid'].hide()
			self['label_play'].hide()
			self['button_play'].hide()
			self['Line_Bottom'].hide()
			self['pageinfo'].show()
			self["starsbg"].hide()
			self["stars"].hide()
			self.postviewready = False
			self.setTitle(str(self.headline))
			self.showProgrammPage()

	def playVideo(self):
		if self.current == 'menu':
			self.REZ = self.getREZ(self.kochId[self.currItem])
		if self.REZ['recipeVideoId']:
			content, resp = self.getAPIdata('videos/' + self.REZ['recipeVideoId'])
			if resp != 200:
				self.session.openWithCallback(self.eject, MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
				self.close()
				return
			result = loads(content)
			sref = eServiceReference(4097, 0, str(result['video_brightcove_url']))
			description = result['video_description']
			if len(result['video_title'] + ' - ' + description) < 30:
				sref.setName(str(result['video_title'] + ' - ' + result['video_description']))
			else:
				sref.setName(str(result['video_title']))
			self.session.openWithCallback(self.returnVideo, MoviePlayer, sref)


class CKgetNumber(AllScreen):
	def __init__(self, session, number, max):
		self.skin = self.readSkin("CKgetNumber")
		Screen.__init__(self, session, self.skin)
		self.field = str(number)
		self['number'] = Label(self.field)
		self.max = max
		self['actions'] = NumberActionMap(['NumberActions', 'OkCancelActions'], {
			'cancel': self.quit,
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
			'0': self.keyNumber
		}, -2)
		self.Timer = eTimer()
		self.Timer.callback.append(self.keyOK)
		self.Timer.start(2000, True)

	def keyNumber(self, number):
		self.Timer.start(2000, True)
		self.field = self.field + str(number)
		self['number'].setText(self.field)
		if len(self.field) >= self.max:
			self.keyOK()

	def keyOK(self):
		self.Timer.stop()
		self.close(int(self['number'].getText()))

	def quit(self):
		self.Timer.stop()
		self.close(0)


class CKpicshow(AllScreen):
	def __init__(self, session, titel, recipe, images):
		global HIDEFLAG
		HIDEFLAG = True
		self.dict = {'picpath': PLUGINPATH + 'pic/'}
		skin = self.readSkin("CKpicshow")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session, skin)
		self.session = session
		self.REZ = recipe
		self.IMG = images
		self.titel = titel
		self.currId = str(recipe['id'])
		self.setTitle(titel)
		self.picfile = '/tmp/chefkoch.jpg'
		self.pixlist = []
		self.picmax = 0
		self.count = 0
		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self['scoretext'] = Label('')
		self['scoretext'].hide()
		self['picture'] = Pixmap()
		self['picindex'] = Label('')
		self['pictext'] = Label('')
		self['label_ok'] = Label()
		self['button_ok'] = Pixmap()
		self['label_left-right'] = Label('')
		self['button_left-right'] = Pixmap()
		self['NumberActions'] = NumberActionMap(['NumberActions', 'OkCancelActions', 'DirectionActions', 'ColorActions', 'HelpActions'], {
			'ok': self.ok,
			'cancel': self.exit,
			'right': self.picup,
			'left': self.picdown,
			'up': self.picup,
			'down': self.picdown,
			'red': self.infoScreen,
			'yellow': self.infoScreen,
			'green': self.infoScreen,
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
			'9': self.gotoPic,
			'displayHelp': self.infoScreen
		}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.showPic)

	def onLayoutFinished(self):
		self['label_ok'].setText('Vollbild')
		self['label_ok'].show()
		self['button_ok'].show()
		self['label_left-right'].setText('Zurück / Vorwärts')
		self['label_left-right'].show()
		self['button_left-right'].show()
		self.picload.setPara((self['picture'].instance.size().width(), self['picture'].instance.size().height(), 1.0, 1, False, 1, "#00000000"))
		self.count = 0
		self.setTitle(str(self.titel))
		if self.REZ['subtitle']:
			self['pictext'].setText('BESCHREIBUNG: ' + str(self.REZ['subtitle']))
		if self.REZ['rating']:
			score = self.REZ['rating']['rating'] * 20
			scoretext = str(self.REZ['rating']['rating']) + ' (' + str(self.REZ['rating']['numVotes']) + ' Bewertungen)'
		else:
			score = 0.0
			scoretext = '(ohne Bewertung)'
		self["starsbg"].show()
		self["stars"].show()
		self["stars"].setValue(score)
		self['scoretext'].setText(scoretext)
		self['scoretext'].show()
		if self.IMG['count'] > 0:
			for i in range(len(self.IMG['results'])):
				self.pixlist.append(self.IMG['results'][i]['id'])
			picurl = PICURLBASE + self.currId + '/bilder/' + self.REZ['previewImageId'] + '/crop-960x720/' + self.titel + '.jpg'
			callInThread(self.threadedGetPage, picurl, self.getPic, self.downloadError)
			self.picmax = len(self.pixlist) - 1
			username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
			self['picindex'].setText('Bild %d von %d' % (self.count + 1, self.picmax + 1) + '\nvon ' + username)
		else:
			self.session.open(MessageBox, '\nKein Foto vorhanden', MessageBox.TYPE_INFO, close_on_any_key=True)

	def formatUsername(self, username, rank, trim=100):
		return 'Unbekannt' if "unknown" in username else (str(username) + ' (' + str(rank) + '*)')[:trim]

	def ok(self):
		self.session.openWithCallback(self.showPic, CKfullscreen)

	def picup(self):
		self.count += 1 if self.count < self.picmax else - self.count
		picurl = PICURLBASE + self.currId + '/bilder/' + str(self.IMG['results'][self.count]['id']) + '/crop-960x720/' + self.titel + '.jpg'
		callInThread(self.threadedGetPage, picurl, self.getPic, self.downloadError)
		username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
		self['picindex'].setText('Bild %d von %d' % (self.count + 1, self.picmax + 1) + '\nvon ' + username)

	def picdown(self):
		self.count -= 1 if self.count > 0 else - self.picmax
		picurl = PICURLBASE + self.currId + '/bilder/' + str(self.IMG['results'][self.count]['id']) + '/crop-960x720/' + self.titel + '.jpg'
		callInThread(self.threadedGetPage, picurl, self.getPic, self.downloadError)
		username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
		self['picindex'].setText('Bild %d von %d' % (self.count + 1, self.picmax + 1) + '\nvon ' + username)

	def gotoPic(self, number):
		self.session.openWithCallback(self.numberEntered, getNumber, number, 2)

	def numberEntered(self, number):
		if number > self.picmax:
			number = self.picmax
		self.count = number - 1
		picurl = picuribase + '/' + self.currId + '/bilder/' + str(self.IMG['results'][self.count]['id']) + '/crop-960x720/' + self.titel + '.jpg'
		self.pixlist[self.count]
		callInThread(self.threadedGetPage, picurl, self.getPic, self.downloadError)
		username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
		self['picindex'].setText('Bild %d von %d' % (self.count + 1, self.picmax + 1) + '\nvon ' + username)

	def getPic(self, output):
		with open(self.picfile, 'wb') as f:
			f.write(output)
		self.picload.startDecode(self.picfile)

	def showPic(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr:
			self['picture'].instance.setPixmap(ptr.__deref__())

	def threadedGetPage(self, link, success, fail=None):
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		try:
			response = get(ensure_binary(link))
			response.raise_for_status()
			success(response.content)
		except exceptions.RequestException as error:
			if fail is not None:
				fail(error)

	def downloadError(self, output):
		self.CKlog(output)

	def infoScreen(self):
		pass

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class CKfullscreen(AllScreen):
	def __init__(self, session):
		global HIDEFLAG
		HIDEFLAG = True
		self.skin = self.readSkin("CKfullscreen")
		Screen.__init__(self, session, self.skin)
		self.picfile = '/tmp/chefkoch.jpg'
		self.hideflag = True
		self['picture'] = Pixmap()
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'],
			{
			'ok': self.exit,
			'cancel': self.exit,
			'blue': self.hideScreen
			}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.showPic)

	def onLayoutFinished(self):
		self.picload.setPara((self['picture'].instance.size().width(), self['picture'].instance.size().height(), 1.0, 1, False, 1, "#00000000"))
		self.picload.startDecode(self.picfile)

	def showPic(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr:
			self['picture'].instance.setPixmap(ptr.__deref__())

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class CKfavoriten(AllScreen):
	def __init__(self, session, favmode=True):
		global HIDEFLAG
		HIDEFLAG = True
		self.dict = {'picpath': PLUGINPATH + 'pic/'}
		skin = self.readSkin("CKfavoriten")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session, skin)
		self['release'] = Label(RELEASE)
		self.favmode = favmode
		self.session = session
		self.favlist = []
		self.favId = []
		self.faventries = []
		self['favmenu'] = ItemList([])
		self['label_red'] = Label('Entferne Favorit') if self.favmode else Label('Entferne Suchbegriff')
		self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'NumberActions'], {
			'ok': self.ok,
			'cancel': self.exit,
			'down': self.down,
			'up': self.up,
			'red': self.red,
			'yellow': self.infoScreen,
			'green': self.infoScreen,
			'blue': self.hideScreen,
			'0': self.move2end,
			'1': self.move2first
		}, -1)
		self.makeFav()

	def makeFav(self):
		if self.favmode:
			self.setTitle('Chefkoch - Favoriten')
			self.favoriten = PLUGINPATH + 'db/favoriten'
		else:
			self.setTitle('Chefkoch - letzte Suchbegriffe')
			self.favoriten = PLUGINPATH + 'db/suchen'
			titel = '>>> Neue Suche <<<'
			res = ['']
			res.append(MultiContentEntryText(pos=(4, 0), size=(int(570 * SCALE), int(34 * SCALE)), font=-2, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=titel))
			self.faventries.append(res)
			self.favlist.append(titel)
			self.favId.append('')
		if fileExists(self.favoriten):
			with open(self.favoriten, 'r') as f:
				for line in f:
					if ':::' in line:
						favline = line.split(':::')
						titel = str(favline[0])
						Id = favline[1].replace('\n', '')
						res = ['']
						res.append(MultiContentEntryText(pos=(4, 0), size=(int(570 * SCALE), int(34 * SCALE)), font=-2, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=titel))
						self.faventries.append(res)
						self.favlist.append(titel)
						self.favId.append(Id)
		self['favmenu'].l.setList(self.faventries)
		self['favmenu'].l.setItemHeight(int(34 * SCALE))

	def ok(self):
		self.currItem = self.getIndex(self['favmenu'])
		if len(self.favlist) > 0:
			titel = self.favlist[self.currItem]
			Id = self.favId[self.currItem]
			if self.favmode:
				self.session.open(CKview, Id, '"' + titel + '"', 1, True, False)
			elif titel == '>>> Neue Suche <<<':
				titel = ''
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Chefkoch - Suche Rezepte:', text=titel)
			else:
				self.session.openWithCallback(self.exit, CKview, titel, 'mit "' + titel + '" gefundene Rezepte', 0, False, False)

	def searchReturn(self, search):
		if search and search != '':
			found = False
			if fileExists(self.favoriten):
				with open(self.favoriten, 'r') as f:
					for line in f:
						if search in line and line != '\n':
							found = True
							break
			if not found:
				with open(self.favoriten, 'a') as f:
					f.write(search + ':::' + search)
					f.write(linesep)
			self.session.openWithCallback(self.exit, CKview, search, 'mit "' + search + '" gefundene Rezepte', 0, False, False)

	def red(self):
		if len(self.favlist) > 0:
			try:
				self.currItem = self.getIndex(self['favmenu'])
				name = self.favlist[self.currItem]
			except IndexError:
				name = ''
			if name != '>>> Neue Suche <<<' and name != '':
				text = "\nRezept '%s' aus den Favoriten entfernen?" if self.favmode else "\nsuche '%s' aus den letzten Suchbegriffen entfernen?"
				self.session.openWithCallback(self.red_return, MessageBox, text % name, MessageBox.TYPE_YESNO)

	def red_return(self, answer):
		if answer is True:
			self.currItem = self.getIndex(self['favmenu'])
			try:
				favorite = self.favId[self.currItem]
			except IndexError:
				favorite = 'NONE'
			if fileExists(self.favoriten):
				data = ''
				with open(self.favoriten, 'r') as f:
					for line in f:
						if favorite not in line and line != '\n':
							data = data + line
				with open(self.favoriten + '.new', 'w') as fnew:
					fnew.write(data)
				rename(self.favoriten + '.new', self.favoriten)
			self.favlist = []
			self.favId = []
			self.faventries = []
			self.makeFav()

	def move2first(self):
		try:
			self.currItem = self.getIndex(self['favmenu'])
			fav = self.favlist[self.currItem] + ':::' + self.favId[self.currItem]
			with open(self.favoriten + '.new', 'w') as fnew:
				fnew.write(fav)
			data = ''
			with open(self.favoriten, 'r') as f:
				for line in f:
					if fav not in line and line != '\n':
						data = data + line
			with open(self.favoriten + '.new', 'a') as fnew:
				fnew.write(data)
			rename(self.favoriten + '.new', self.favoriten)
			self.favlist = []
			self.favId = []
			self.faventries = []
			self.makeFav()
		except IndexError:
			pass

	def move2end(self):
		try:
			self.currItem = self.getIndex(self['favmenu'])
			fav = self.favlist[self.currItem] + ':::' + self.favId[self.currItem]
			data = ''
			with open(self.favoriten, 'r') as f:
				for line in f:
					if fav not in line and line != '\n':
						data = data + line
			with open(self.favoriten + '.new', 'w') as fnew:
				fnew.write(data)
			with open(self.favoriten + '.new', 'a') as fnew:
				fnew.write(fav)
			rename(self.favoriten + '.new', self.favoriten)
			self.favlist = []
			self.favId = []
			self.faventries = []
			self.makeFav()
		except IndexError:
			pass

	def getIndex(self, list):
		return list.getSelectedIndex()

	def down(self):
		self['favmenu'].down()

	def up(self):
		self['favmenu'].up()

	def infoScreen(self):
		pass

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()

	def playVideo(self, answer):
		if answer is True:
			sref = eServiceReference(4097, 0, self.filename)
			sref.setName(self.name)
			self.session.openWithCallback(self.exit, MoviePlayer, sref)
		else:
			self.close()

	def infoScreen(self):
		pass


class ItemList(MenuList):
	def __init__(self, items, enableWrapAround=True):
		MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
		fontoffset = 2 if config.plugins.chefkoch.font_size.value == 'large' else 0
		self.l.setFont(-2, gFont('Regular', int(24 * SCALE)))
		self.l.setFont(-1, gFont('Regular', int((22 + fontoffset) * SCALE)))
		self.l.setFont(0, gFont('Regular', int((20 + fontoffset) * SCALE)))
		self.l.setFont(1, gFont('Regular', int((18 + fontoffset) * SCALE)))
		self.l.setFont(2, gFont('Regular', int((16 + fontoffset) * SCALE)))


class CKmain(AllScreen):
	def __init__(self, session):
		global ALPHA
		global HIDEFLAG
		self.session = session
		HIDEFLAG = True
		ALPHA = '/proc/stb/video/alpha' if fileExists('/proc/stb/video/alpha') else None
		if not ALPHA:
			self.CKlog('Alphachannel not found! Hide/Show-Function (=blue button) disabled')
		self.dict = {'picpath': PLUGINPATH + 'pic/'}
		skin = self.readSkin("CKmain")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session, skin)
		self.apidata = None
		self.mainId = None
		self.picfile = '/tmp/chefkoch.jpg'
		self.rezeptfile = '/tmp/Rezept.html'
		self.actmenu = 'mainmenu'
		self['mainmenu'] = ItemList([])
		self['secondmenu'] = ItemList([])
		self['thirdmenu'] = ItemList([])
		self['label_red'] = Label('Favorit')
		self['label_green'] = Label('Zufall')
		self['label_yellow'] = Label('Suche')
		self['label_blue'] = Label('Ein-/Ausblenden')
		self['release'] = Label(RELEASE)
		self['helpactions'] = ActionMap(['HelpActions'], {'displayHelp': self.infoScreen}, -1)
		self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'MovieSelectionActions'], {
			'ok': self.ok,
			'cancel': self.exit,
			'right': self.rightDown,
			'left': self.leftUp,
			'down': self.down,
			'up': self.up,
			'nextBouquet': self.zap,
			'prevBouquet': self.zap,
			'red': self.fav,
			'yellow': self.yellow,
			'green': self.zufall,
			'blue': self.hideScreen,
			'showEventInfo': self.infoScreen,
			'contextMenu': self.config
		}, -1)
		self.movie_stop = config.usage.on_movie_stop.value
		self.movie_eof = config.usage.on_movie_eof.value
		config.usage.on_movie_stop.value = 'quit'
		config.usage.on_movie_eof.value = 'quit'
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		callInThread(self.makeMainMenu)

	def ok(self):
		self.currItem = self.getIndex(self[self.actmenu])
		if self.actmenu == 'mainmenu' and self.mainId:
			mainId = self.mainId[self.currItem]
			if mainId == '998':  # Id für CK-Video Hauptmenü (= Secondmenu)
				self.CKvideo = True
				self.currKAT = self.getVKAT()
				callInThread(self.makeSecondMenu, mainId)
			elif mainId == '996':  # Id für CK-Magazin Hauptmenü (= Secondmenu)
				self.CKvideo = False
				self.currKAT = self.getMKAT()
				callInThread(self.makeSecondMenu, mainId)
			else:
				self.CKvideo = False
				self.currKAT = self.getNKAT()
				if list(filter(lambda i: i['parentId'] == mainId, self.currKAT)):
					callInThread(self.makeSecondMenu, mainId)
				else:
					sort = 4 if mainId == '999' else 1  # Datumsortierung für "Das perfekte Dinner"
					self.session.openWithCallback(self.selectMainMenu, CKview, self.mainmenuquery[self.currItem], '"' + self.mainmenutitle[self.currItem] + '"', sort, False, False)

		elif self.actmenu == 'secondmenu':
			secondId = self.secondId[self.currItem]
			if list(filter(lambda i: i['parentId'] == secondId, self.currKAT)):
				callInThread(self.makeThirdMenu, secondId)
			else:
				sort = 3 if self.CKvideo else 1  # Videosortierung für "Chefkoch Video"
				self.session.openWithCallback(self.selectSecondMenu, CKview, self.secondmenuquery[self.currItem], '"' + self.secondmenutitle[self.currItem] + '"', sort, False, False)

		elif self.actmenu == 'thirdmenu':
			sort = 3 if self.CKvideo else 1  # Videosortierung für "Chefkoch Video"
			self.session.openWithCallback(self.selectThirdMenu, CKview, self.thirdmenuquery[self.currItem], '"' + self.thirdmenutitle[self.currItem] + '"', sort, False, False)

	def makeMainMenu(self):
		global totalrecipes
		content, resp = self.getAPIdata('recipes')
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nDer XChefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
			self.close()
			return
		totalrecipes = loads(content)['count']
		self.NKAT = []  # Normalkategorien
		self.VKAT = []  # Videokategorien
		self.MKAT = []  # Magazinkategorien
		self.mainmenulist = []
		self.mainmenuquery = []
		self.mainmenutitle = []
		self.mainId = []
		self.currKAT = self.getNKAT()
		self.setTitle('Hauptmenü')
		for i in range(len(self.currKAT)):
			res = ['']
			if self.currKAT[i]['level'] == 1:
				res.append(MultiContentEntryText(pos=(0, 1), size=(int(570 * SCALE), int(30 * SCALE)), font=-2, flags=RT_HALIGN_CENTER, text=str(self.currKAT[i]['descriptionText'])))
				self.mainmenulist.append(res)
				self.mainmenuquery.append(self.currKAT[i]['descriptionText'])
				self.mainmenutitle.append(self.currKAT[i]['descriptionText'])
				self.mainId.append(self.currKAT[i]['id'])
		self['mainmenu'].l.setList(self.mainmenulist)
		self['mainmenu'].l.setItemHeight(int(34 * SCALE))
		self.selectMainMenu()

	def makeSecondMenu(self, parentId):
		self.secondmenulist = []
		self.secondmenuquery = []
		self.secondmenutitle = []
		self.secondId = []
		self.parentId = parentId
		for i in range(len(self.currKAT)):
			res = ['']
			if self.currKAT[i]['level'] == 2 and self.currKAT[i]['parentId'] == parentId:
				res.append(MultiContentEntryText(pos=(0, 1), size=(int(570 * SCALE), int(30 * SCALE)), font=-2, flags=RT_HALIGN_CENTER, text=str(self.currKAT[i]['descriptionText'])))
				self.secondmenulist.append(res)
				self.secondmenuquery.append(self.currKAT[i]['descriptionText'])
				self.secondmenutitle.append(self.currKAT[i]['descriptionText'])
				self.secondId.append(self.currKAT[i]['id'])
		self['secondmenu'].l.setList(self.secondmenulist)
		self['secondmenu'].l.setItemHeight(int(34 * SCALE))
		self['secondmenu'].moveToIndex(0)
		for i in range(len(self.currKAT)):
			if self.currKAT[i]['id'] == parentId:
				break
		self.setTitle(str(self.currKAT[i]['title']))
		self.selectSecondMenu()

	def makeThirdMenu(self, parentId):
		self.thirdmenulist = []
		self.thirdmenuquery = []
		self.thirdmenutitle = []
		for i in range(len(self.currKAT)):
			res = ['']
			if self.currKAT[i]['level'] == 3 and self.currKAT[i]['parentId'] == parentId:
				res.append(MultiContentEntryText(pos=(0, 1), size=(int(570 * SCALE), int(30 * SCALE)), font=-2, flags=RT_HALIGN_CENTER, text=str(self.currKAT[i]['descriptionText'])))
				self.thirdmenulist.append(res)
				self.thirdmenuquery.append(self.currKAT[i]['descriptionText'])
				self.thirdmenutitle.append(self.currKAT[i]['descriptionText'])
		self['thirdmenu'].l.setList(self.thirdmenulist)
		self['thirdmenu'].l.setItemHeight(int(34 * SCALE))
		self['thirdmenu'].moveToIndex(0)
		for i in range(len(self.currKAT)):
			if self.currKAT[i]['id'] == parentId:
				break
		self.setTitle(str(self.currKAT[i]['title']))
		self.selectThirdMenu()

	def makeVKATdb(self):  # hole alle verfügbaren Videokategorien
		content, resp = self.getAPIdata('videos?&offset=0&limit=10000')
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
			self.close()
			return
		result = loads(content)
		VKAT = []
		with open(PLUGINPATH + 'db/VKATdb', 'a') as f:
			for i in range(len(result)):
				data = result[i]['video_format']
				if data != 'unknown':
					id = ''.join(x for x in data if x.isdigit())
					if id not in VKAT:
						VKAT.append(id)
						f.write(data + '|' + data + '\n')

	def getNKAT(self):  # erzeuge die normale Kategorie
		if not self.NKAT:
			content, resp = self.getAPIdata('recipes/categories')
			if resp != 200:
				self.session.openWithCallback(self.eject, MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
				self.close()
				return {}
			self.NKAT = loads(content)
			self.NKAT.append({'id': '996', 'title': 'Chefkoch Magazin', 'parentId': None, 'level': 1, 'descriptionText': 'Chefkoch Magazin', 'linkName': 'https://www.chefkoch.de/magazin/'})
			self.NKAT.append({'id': '998', 'title': 'Chefkoch Videos', 'parentId': None, 'level': 1, 'descriptionText': 'Chefkoch Videos', 'linkName': 'video.html'})
			self.NKAT.append({'id': '999', 'title': 'Perfekte Dinner', 'parentId': None, 'level': 1, 'descriptionText': 'Das perfekte Dinner Rezepte', 'linkName': 'das-perfekte-dinner.html'})
		return self.NKAT

	def getVKAT(self):  # erzeuge die Videokategorie
		if not self.VKAT:
			for i in range(len(self.NKAT)):
				if self.NKAT[i]['level'] == 1:
					self.VKAT.append(self.NKAT[i])
			if not fileExists(PLUGINPATH + 'db/VKATdb'):
				self.makeVKATdb()  # wird nur bei fehlender VKATdb erzeugt (= Notfall)
			i = 1000  # erzeuge eigene Video-IDs über 1000
			with open(PLUGINPATH + 'db/VKATdb', 'r') as f:
				for data in f:
					dict = {}
					dict['id'] = str(i)
					dict['title'] = data.split('|')[1].replace('\n', '')
					if data.split('|')[0].startswith('drupal'):
						dict['parentId'] = '998'  # Id für CK-Video Hauptmenü (= Secondmenu)
						dict['level'] = 2
					else:
						dict['parentId'] = '997'  # Id für CK-Video Untermenü (= Thirdmenu)
						dict['level'] = 3
					dict['descriptionText'] = data.split('|')[1].replace('\n', '')
					dict['linkName'] = data.split('|')[0]
					self.VKAT.append(dict)
					i += 1
			self.VKAT.append({'id': '997', 'title': 'weitere Videos', 'parentId': '998', 'level': 2, 'descriptionText': '>>> weitere Chefkoch Videos <<<', 'linkName': ''})
		return self.VKAT

	def getMKAT(self):  # erzeuge die Magazinkategorie
		if not self.MKAT:
			content, resp = self.getAPIdata('magazine/categories')
			if resp != 200:
				self.session.openWithCallback(self.eject, MessageBox, '\nDer Chefkoch.de Server ist nicht erreichbar!', MessageBox.TYPE_INFO, close_on_any_key=True)
				self.close()
				return
			result = loads(content)
			offset = 2000  # erzeuge eigene Magazin-IDs über 2000
			for i in range(len(result)):
				dict = {}
				if result[i]['parent'] == '34' and result[i]['published']:  # Id 34 ist die Root von CK-Magazin
					dict['id'] = str(int(result[i]['id']) + offset)
					dict['title'] = result[i]['name']
					dict['parentId'] = '996'  # Id für CK-Magazin Hauptmenü (= Secondmenu)
					dict['level'] = 2
					dict['descriptionText'] = result[i]['name']
					dict['linkName'] = result[i]['url']
					self.MKAT.append(dict)
			for i in range(len(result)):
				for j in range(len(self.MKAT)):
					dict = {}
					parentId = result[i]['parent']
					if parentId:
						if int(parentId) + offset == int(self.MKAT[j]['id']):
							dict['id'] = str(int(result[i]['id']) + offset)
							dict['title'] = result[i]['name']
							dict['parentId'] = str(int(parentId) + offset)
							dict['level'] = 3
							dict['descriptionText'] = result[i]['name']
							dict['linkName'] = result[i]['url']
							self.MKAT.append(dict)
							break
			self.MKAT.reverse()
			self.MKAT.append({'id': '996', 'title': 'Chefkoch Magazin', 'parentId': None, 'level': 1, 'descriptionText': 'Chefkoch Magazin', 'linkName': 'https://www.chefkoch.de/magazin/'})
		return self.MKAT

	def selectMainMenu(self):
		self.actmenu = 'mainmenu'
		self['mainmenu'].show()
		self['secondmenu'].hide()
		self['thirdmenu'].hide()
		self['mainmenu'].selectionEnabled(1)
		self['secondmenu'].selectionEnabled(0)
		self['thirdmenu'].selectionEnabled(0)

	def selectSecondMenu(self):
		if len(self.secondmenulist) > 0:
			self.actmenu = 'secondmenu'
			self['mainmenu'].hide()
			self['secondmenu'].show()
			self['thirdmenu'].hide()
			self['mainmenu'].selectionEnabled(0)
			self['secondmenu'].selectionEnabled(1)
			self['thirdmenu'].selectionEnabled(0)

	def selectThirdMenu(self):
		if len(self.thirdmenulist) > 0:
			self.actmenu = 'thirdmenu'
			self['mainmenu'].hide()
			self['secondmenu'].hide()
			self['thirdmenu'].show()
			self['mainmenu'].selectionEnabled(0)
			self['secondmenu'].selectionEnabled(0)
			self['thirdmenu'].selectionEnabled(1)

	def up(self):
		self[self.actmenu].up()

	def down(self):
		self[self.actmenu].down()

	def leftUp(self):
		self[self.actmenu].pageUp()

	def rightDown(self):
		self[self.actmenu].pageDown()

	def getIndex(self, list):
		return list.getSelectedIndex()

	def yellow(self):
		self.session.open(CKfavoriten, False)

	def fav(self):
		self.session.open(CKfavoriten)

	def zufall(self):
		self.session.openWithCallback(self.selectMainMenu, CKview, 'recipe-of-today', ' "Zufallsrezept"', 1, False, True)

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def config(self):
		config.usage.on_movie_stop.value = self.movie_stop
		config.usage.on_movie_eof.value = self.movie_eof
		self.session.openWithCallback(self.exit, CKconfig)

	def infoScreen(self):
		pass

	def eject(self, dummy):
		self.exit()

	def exit(self):
		global HIDEFLAG
		if ALPHA and not HIDEFLAG:
			HIDEFLAG = True
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		if self.actmenu == 'mainmenu':
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			for i in range(LINESPERPAGE):
				pic = '/tmp/chefkoch%d.jpg' % i
				if fileExists(pic):
					remove(pic)
			if fileExists(self.picfile):
				remove(self.picfile)
			if fileExists(self.rezeptfile):
				remove(self.rezeptfile)
			self.close()
		elif self.actmenu == 'secondmenu':
			self.CurrKAT = self.getNKAT()
			self.setTitle('Hauptmenü')
			self.selectMainMenu()
		elif self.actmenu == 'thirdmenu':
			for i in range(len(self.currKAT)):
				if self.currKAT[i]['id'] == self.parentId:
					break
			self.setTitle(str(self.currKAT[i]['title']))
			self.selectSecondMenu()


class CKconfig(ConfigListScreen, AllScreen):
	def __init__(self, session):
		self.dict = {'picpath': PLUGINPATH + 'pic/'}
		skin = self.readSkin("CKconfig")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session)
		self['VKeyIcon'] = Boolean(False)
		self.password = config.plugins.chefkoch.password.value
		self['plugin'] = Pixmap()
		list = []
		list.append(getConfigListEntry('Plugin Auflösung:', config.plugins.chefkoch.plugin_size, "Plugin Auflösung"))
		list.append(getConfigListEntry('Schriftgröße Rezepte/Kommentare:', config.plugins.chefkoch.font_size, "Schriftgröße Langtexte"))
		list.append(getConfigListEntry('Maximale Anzahl Rezepte:', config.plugins.chefkoch.maxrecipes, "Maximale Anzahl Rezepte"))
		list.append(getConfigListEntry('Maximale Anzahl Kommentare:', config.plugins.chefkoch.maxcomments, "Maximale Anzahl Kommentare"))
		list.append(getConfigListEntry('Maximale Anzahl Rezeptbilder:', config.plugins.chefkoch.maxpictures, "Maximale Anzahl Rezeptbilder"))
		list.append(getConfigListEntry('Versende Rezepte per E-mail:', config.plugins.chefkoch.mail, "Versende Rezepte per E-mail"))
		list.append(getConfigListEntry('E-mail Absender:', config.plugins.chefkoch.mailfrom, "E-mail Absender"))
		list.append(getConfigListEntry('E-mail Empfänger:', config.plugins.chefkoch.mailto, "E-mail Empfänger"))
		list.append(getConfigListEntry('E-mail Login:', config.plugins.chefkoch.login, "E-mail Login"))
		list.append(getConfigListEntry('E-mail Passwort:', config.plugins.chefkoch.password, "E-mail Passwort"))
		list.append(getConfigListEntry('E-mail Server:', config.plugins.chefkoch.server, "E-mail Server"))
		list.append(getConfigListEntry('E-mail Server Port:', config.plugins.chefkoch.port, "E-mail Server Port"))
		list.append(getConfigListEntry('E-mail Server SSL:', config.plugins.chefkoch.ssl, "E-mail Server SSL"))
		list.append(getConfigListEntry('DebugLog', config.plugins.chefkoch.debuglog, "Debug Logging aktivieren"))
		list.append(getConfigListEntry('Log in Datei', config.plugins.chefkoch.logtofile, "Log in Datei '/home/root/logs'"))

		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {
			'cancel': self.keyCancel,
			'red': self.keyCancel,
			'green': self.keySave
		}, -2)
		ConfigListScreen.__init__(self, list, on_change=self.UpdateComponents)
		self.onLayoutFinish.append(self.UpdateComponents)

	def UpdateComponents(self):
		png = PLUGINPATH + 'pic/setup/' + config.plugins.chefkoch.plugin_size.value + '.png'
		if fileExists(png):
			PNG = loadPNG(png)
			if PNG:
				self['plugin'].instance.setPixmap(PNG)

	def keySave(self):
		if config.plugins.chefkoch.password.value != self.password:
			password = b64encode(ensure_binary(config.plugins.chefkoch.password.value))
			config.plugins.chefkoch.password.value = password
		self.saveAll()
		self.exit()

	def keyCancel(self):
		for x in self['config'].list:
			x[1].cancel()
		self.exit()

	def exit(self):
		self.session.openWithCallback(self.close, CKmain)


def main(session, **kwargs):
	session.open(CKmain)


def Plugins(**kwargs):
	return [PluginDescriptor(name='Chefkoch.de', description='Chefkoch.de Rezepte', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=main), PluginDescriptor(name='Chefkoch.de', description='Chefkoch.de Rezepte', where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]

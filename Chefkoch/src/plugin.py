# -*- coding: utf-8 -*-
# Plugin still runs under Pyton 2 and Python 3

# PYTHON IMPORTS
from base64 import b64encode, b64decode
from datetime import datetime
from json import loads
from operator import itemgetter
from os import linesep, rename, remove
from random import randrange, choice
from requests import get, exceptions
from PIL import Image
from smtplib import SMTP, SMTP_SSL, SMTPResponseException
from six import ensure_str, ensure_binary, PY3
from six.moves.email_mime_multipart import MIMEMultipart
from six.moves.email_mime_text import MIMEText
from six.moves.email_mime_image import MIMEImage
from time import strftime
from twisted.internet.reactor import callInThread
from xml.etree.ElementTree import tostring, parse

# ENIGMA IMPORTS
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

# GLOBALS
RELEASE = 'V2.3'
LINESPERPAGE = 8
PICFILE = '/tmp/chefkoch.jpg'
MODULE_NAME = __name__.split(".")[-1]
PICURLBASE = 'https://img.chefkoch-cdn.de/rezepte/'
APIURIBASE = 'https://api.chefkoch.de/v2/'
NOPICURL = 'https://img.chefkoch-cdn.de/img/default/layout/recipe-nopicture.jpg'
ALPHA = '/proc/stb/video/alpha' if fileExists('/proc/stb/video/alpha') else None
AGENTS = [
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
		"Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
		"Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edge/87.0.664.75",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"
		]

# orderBy-Codes: 0= unbekannt, 1= = unbekannt, 2= unbekannt, 3= rating, 4= unbekannt, 5= unbekannt, 6= createdAt, 7= isPremium, 8= unbekannt
# nicht unterstüzte orderBy-Queries: numVotes, preparationTime

config.plugins.chefkoch = ConfigSubsection()
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
FULLHD = True if getDesktop(0).size().width() >= 1920 else False
PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/Chefkoch/")
if FULLHD:
	SCALE = 1.5
	SKINFILE = "%sskin_FHD.xml" % PLUGINPATH
else:
	SCALE = 1.0
	SKINFILE = "%sskin_HD.xml" % PLUGINPATH


class AllScreen(Screen):
	def __init__(self):
		pass

	def applySkinVars(self, skin, dict):
		for key in dict.keys():
			skin = skin.replace('{%s}' % key, dict[key])
		return skin

	def getAPIdata(self, apiuri):
		headers = {"User-Agent": choice(AGENTS), 'Accept': 'application/json'}
		try:
			response = get('%s%s' % (APIURIBASE, apiuri), headers=headers, timeout=(3.05, 6))
			response.raise_for_status()
			return (response.text, response.status_code)
		except exceptions.RequestException as error:
			return ("", error)

	def CKlog(self, info, wert="", debug=False):
		if debug and not config.plugins.chefkoch.debuglog.value:
			return
		if config.plugins.chefkoch.logtofile.value:
			try:
				with open('/home/root/logs/chefkoch.log', 'a') as f:
					f.write('%s %s %s\r\n' % (strftime('%H:%M:%S'), info, wert))
			except IOError as err:
				print("[Chefkoch] Error writing Logfile: %s" % str(err))
		else:
			print("[Chefkoch] %s %s" % (str(info), str(wert)))

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

	def Pdownload(self, link):
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		headers = {"User-Agent": choice(AGENTS), 'Accept': 'application/json'}
		try:
			response = get(link, headers=headers, timeout=(3.05, 6))
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.downloadError(error)
		else:
			try:
				with open(PICFILE, 'wb') as f:
					f.write(response.content)
					self.showPic()
			except IOError as logerr:
				self.CKlog("Error writing PICFILE: %s" % str(logerr))

	def showPic(self):
		picload = ePicLoad()
		picload.setPara(self['picture'].instance.size().width(), self['picture'].instance.size().height(), 1, 0, 0, 1, "#00000000")
		if picload.startDecode(PICFILE, 0, 0, False) == 0:
			ptr = picload.getData()
			if ptr is not None:
				self['picture'].instance.setPixmap(ptr)

	def downloadError(self, output):
		self.CKlog(output)


class CKview(AllScreen):
	def __init__(self, session, query, titel, sort, fav, zufall):
		global HIDEFLAG
		HIDEFLAG = True
		fontsize = '%d' % int(22 * SCALE) if config.plugins.chefkoch.font_size.value == 'large' else '%d' % int(20 * SCALE)
		self.dict = {'picpath': '%spic/' % PLUGINPATH, 'fontsize': fontsize}
		skin = self.readSkin("CKview")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session, skin)
		self.session = session
		self.query = query
		self.titel = titel
		self.sort = sort
		self.fav = fav
		self.zufall = zufall
		self.rezept = 'https://www.chefkoch.de/rezepte/'
		self.rezeptfile = '/tmp/Rezept.html'
		self.comment = False
		self.len = 0
		self.count = 0
		self.maxPage = 0
		self.currItem = 0
		self.current = 'menu'
		self.name = ''
		self.chefvideo = ''
		self.GRP = {}
		self.REZ = {}
		self.KOM = {}
		self.orgGRP = []
		self.kochId = []
		self.picurllist = []
		self.titellist = []
		self.videolist = []
		self.rezeptelist = []
		self.rezeptelinks = []
		self.sortname = ['{keine}', 'Anzahl Bewertungen', 'Anzahl Sterne', 'mit Video', 'Erstelldatum']
		for i in range(LINESPERPAGE):
			self['pic%d' % i] = Pixmap()
			self['vid%d' % i] = Pixmap()
		self['picture'] = Pixmap()
		self['postvid'] = Pixmap()
		self['stars'] = ProgressBar()
		self['starsbg'] = Pixmap()
		self['scoretext'] = Label('')
		self['recipetext'] = Label('')
		self['button_green'] = Pixmap()
		self['button_red'] = Pixmap()
		self['button_yellow'] = Pixmap()
		self['button_blue'] = Pixmap()
		self['textpage'] = ScrollLabel('')
		self['menu'] = ItemList([])
		self['label_red'] = Label('')
		self['label_green'] = Label('')
		self['label_yellow'] = Label('')
		self['label_blue'] = Label('')
		self['label_rezeptnr'] = Label('')
		self['label_1-0'] = Label('')
		self['button_1-0'] = Pixmap()
		self['pageinfo'] = Label('')
		self['label_ok'] = Label('')
		self['button_ok'] = Pixmap()
		self['label_play'] = Label('')
		self['button_play'] = Pixmap()
		self['Line_Bottom'] = Label('')
		self['release'] = Label(RELEASE)
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

	def onLayoutFinished(self):
		if self.zufall:
			self.current = 'postview'
			if not self.GRP:
				self.GRP = self.getGRP()
				self.maxPage = (len(self.GRP) - 1) // LINESPERPAGE + 1
			self.showRecipe(self.GRP[randrange(0, len(self.GRP))]['id'])
			callInThread(self.fillRecipe)
		elif self.fav:
			self.current = 'postview'
			self.showRecipe(self.query)
			callInThread(self.fillRecipe)
		else:
			self.current = 'menu'
			self.showRlist()
			callInThread(self.fillRlist)

	def showRlist(self):  # zeige leere Rezeptliste
		for i in range(LINESPERPAGE):
			self['pic%d' % i].hide()
			self['vid%d' % i].hide()
		self['postvid'].hide()
		self['Line_Bottom'].hide()
		self['starsbg'].hide()
		self['stars'].hide()
		self['button_green'].hide()
		self['button_yellow'].hide()
		self['button_red'].show()
		self['button_blue'].show()
		self['label_red'].setText('Rezept zu Favoriten')
		self['label_green'].setText("")
		self['label_yellow'].setText('Suche')
		self['label_blue'].setText('Ein-/Ausblenden')
		self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
		self['label_ok'].setText('zum Rezept')
		self['label_ok'].show()
		self['label_1-0'].setText('')
		self['button_1-0'].hide()
		self['button_ok'].show()
		self['button_play'].hide()
		self['label_play'].hide()
		self['scoretext'].hide()
		self['recipetext'].hide()
		self['textpage'].hide()
		self['picture'].hide()
		self['pageinfo'].show()
		self['menu'].show()

	def fillRlist(self):  # fülle die Rezeptliste
		self.GRP = self.getGRP()
		self.maxPage = (len(self.GRP) - 1) // LINESPERPAGE + 1
		self.setTitle("%s %s Rezepte (%s %s)" % (len(self.GRP), self.titel.replace(" Rezepte", ""), self.videocount, "Video" if self.videocount == 1 else "Videos"))
		self['label_green'].setText('Sortierung: %s' % self.sortname[self.sort])
		self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))
		kochentries = []
		titellist = []
		videolist = []
		picurllist = []
		for i in range(len(self.GRP)):
			ident = str(self.GRP[i]['id'])
			titel = self.GRP[i]['title']
			time = str(self.GRP[i]['preparationTime'])
			if self.GRP[i]['numVotes']:
				count = str(self.GRP[i]['numVotes'])
				score = str(round(self.GRP[i]['rating'] / 5, 1) * 5).replace('.', '_').replace('_0', '')
			else:
				count = 'keine'
				score = '0'
			picurl = "%s%s/bilder/%s/crop-160x120/%s.jpg" % (PICURLBASE, ident, self.GRP[i]['previewImageId'], titel.replace(' ', '-')) if self.GRP[i]['previewImageId'] else NOPICURL
			text = self.GRP[i]['subtitle']
			if len(text) > 155:
				text = "%s…" % text[:155]
			self.kochId.append(ident)
			titellist.append(titel)
			videolist.append(self.GRP[i]['hasVideo'])
			picurllist.append(picurl)
			res = [i]
			res.append(MultiContentEntryText(pos=(int(110 * SCALE), 10), size=(int(965 * SCALE), int(30 * SCALE)), font=-1, color_sel=16777215, flags=RT_HALIGN_LEFT, text=titel))  # TITLE
			png = "%spic/FHD/smallFHD-%s.png" % (PLUGINPATH, score) if FULLHD else "%spic/HD/smallHD-%s.png" % (PLUGINPATH, score)
			if fileExists(png):
				res.append(MultiContentEntryPixmapAlphaTest(pos=(int(14 * SCALE), int(36 * SCALE)), size=(int(75 * SCALE), int(15 * SCALE)), png=loadPNG(png)))  # STARS
			res.append(MultiContentEntryText(pos=(int(11 * SCALE), int(52 * SCALE)), size=(int(75 * SCALE), int(30 * SCALE)), font=1, color=16777215, color_sel=16777215,
											flags=RT_HALIGN_CENTER, text='(%s)' % count))  # COUNT
			res.append(MultiContentEntryText(pos=(int(111 * SCALE), int(45 * SCALE)), size=(int(965 * SCALE), int(70 * SCALE)),
											font=-1, color=10857646, color_sel=13817818, flags=RT_HALIGN_LEFT | RT_WRAP, text=text))  # TEXT
			res.append(MultiContentEntryText(pos=(int(10 * SCALE), int(6 * SCALE)), size=(int(75 * SCALE), int(26 * SCALE)), font=0, backcolor=3899463,
											color=16777215, backcolor_sel=15704383, color_sel=16777215, flags=RT_HALIGN_CENTER, text=time))  # TIME
			kochentries.append(res)
		self.titellist = titellist
		self.videolist = videolist
		self.picurllist = picurllist
		self.setPrevIcons(0)
		self.len = len(kochentries)
		self['menu'].l.setItemHeight(int(75 * SCALE))
		self['menu'].l.setList(kochentries)
		self['menu'].moveToIndex(self.currItem)
		self.currItem = self['menu'].getSelectedIndex()
		self.setPrevIcons(self.currItem - self.currItem % LINESPERPAGE)

	def formatDatum(self, date):
		return str(datetime.strptime(date[:10], '%Y-%m-%d').strftime('%d.%m.%Y'))

	def formatDatumZeit(self, date):
		datum = datetime.strptime(date[:10], '%Y-%m-%d').strftime('%d.%m.%Y')
		zeit = datetime.strptime(date[11:19], '%H:%M:%S').strftime('%H:%M')
		return 'vom %s um %s' % (datum, zeit)

	def formatUsername(self, username, rank, trim):
		trim = trim if trim > 0 else 100
		return 'Unbekannt' if "unknown" in username else '%s (%s*)' % (username, rank)[:trim]

	def showRecipe(self, ident):  # zeige leeres Rezept
		self.currId = ident
		for i in range(LINESPERPAGE):
			self['pic%d' % i].hide()
			self['vid%d' % i].hide()
		self['picture'].hide()
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
		self['label_ok'].setText('')
		self['button_ok'].hide()
		self['postvid'].hide()
		self['label_play'].hide()
		self['button_play'].hide()
		self['Line_Bottom'].hide()
		self['textpage'].setText('')
		self['textpage'].show()

	def fillRecipe(self):  # fülle das Rezept
		self.REZ = self.getREZ(self.currId)
		picurl = "%s%s/bilder/%s/crop-960x720/%s.jpg" % (PICURLBASE, self.currId, self.REZ['previewImageId'], self.titel) if self.REZ['hasImage'] else NOPICURL
		callInThread(self.Pdownload, picurl)
		if self.REZ['rating']:
			score = self.REZ['rating']['rating'] * 20.0
			scoretext = '%1.1f (%s Bewertungen)' % (self.REZ['rating']['rating'], self.REZ['rating']['numVotes'])
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
		self['stars'].setValue(score)
		self['stars'].show()
		self['starsbg'].show()
		self['scoretext'].setText(scoretext)
		self['scoretext'].show()
		effort = ['keiner', 'simpel', 'normal', 'pfiffig']
		recipetext = "Rezept-Identnr.\t: %s" % self.currId
		recipetext += "\nAufwand\t: %s" % effort[self.REZ['difficulty']]
		recipetext += "\nErstellername\t: %s" % self.formatUsername(self.REZ['owner']['username'], self.REZ['owner']['rank'], 22)
		recipetext += "\nErstelldatum\t: %s" % self.formatDatum(self.REZ['createdAt'])
		if self.REZ['nutrition']:
			kcalori = self.REZ['nutrition']['kCalories']
			kcalori = '%s' % kcalori if kcalori else 'k.A.'
			protein = self.REZ['nutrition']['proteinContent']
			protein = '%s g' % protein if protein else 'k.A.'
			fatcont = self.REZ['nutrition']['fatContent']
			fatcont = '%s g' % fatcont if fatcont else 'k.A.'
			carbohyd = self.REZ['nutrition']['carbohydrateContent']
			carbohyd = '%s g' % carbohyd if carbohyd else 'k.A.'
			recipetext += '\n\n{0:13}{1:13}{2:14}{3}'.format('kcal', 'Eiweiß', 'Fett', 'Kohlenhydr.')
			recipetext += '\n{0:13}{1:13}{2:12}{3}'.format(kcalori, protein, fatcont, carbohyd)
		self['recipetext'].setText(str(recipetext))
		self['recipetext'].show()
		self['Line_Bottom'].show()
		self.IMG = self.getIMG(self.currId)
		if self.picCount == 1:
			self['label_ok'].setText('Vollbild')
			self['button_ok'].show()
		elif self.picCount > 1:
			self['label_ok'].setText('%d Rezeptbilder' % (self.IMGlen))
			self['button_ok'].show()
		else:
			self['label_ok'].setText('')
			self['button_ok'].hide()
		self.KOM = self.getKOM(self.currId)
		if self.current == 'postview':
			self.showRezept()

	def getREZ(self, ident):  # hole den jeweiligen Rezeptdatensatz
		content, resp = self.getAPIdata('recipes/%s' % ident)
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
			self.close()
			return {}
		else:
			return loads(content)

	def getIMG(self, ident):  # hole die jeweilige Rezeptbilderliste
		content, resp = self.getAPIdata('recipes/%s/images?&offset=0&limit=%s' % (ident, config.plugins.chefkoch.maxpictures.value))
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
			self.close()
			return {}
		else:
			result = loads(content)
			self.IMGlen = int(config.plugins.chefkoch.maxpictures.value) if result['count'] > int(config.plugins.chefkoch.maxpictures.value) else result['count']
			img = {}
			img['count'] = self.IMGlen
			img['results'] = result['results']
			return img

	def getKOM(self, ident):  # hole die jeweilige Rezeptkommentarliste
		content, resp = self.getAPIdata('recipes/%s/comments?&offset=0&limit=%s' % (ident, config.plugins.chefkoch.maxcomments.value))
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
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
				content, resp = self.getAPIdata('recipes?query=%s&offset=%d&limit=%d&orderBy=3' % (self.query, i * 100, min(limit, 100)))  # 3= sort by 'rating'
				if resp != 200:
					self.session.openWithCallback(self.eject, MessageBox, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
					self.close()
					return []
				result = loads(content)
				for j in range(len(result['results'])):
					if result['results'][j]['recipe']['isRejected']:
						continue
					grp = {}
					grp['id'] = result['results'][j]['recipe']['id']
					grp['createdAt'] = result['results'][j]['recipe']['createdAt']
					grp['preparationTime'] = result['results'][j]['recipe']['preparationTime']
					if result['results'][j]['recipe']['rating']:
						grp['rating'] = result['results'][j]['recipe']['rating']['rating']
						grp['numVotes'] = result['results'][j]['recipe']['rating']['numVotes']
					else:
						grp['rating'] = 0
						grp['numVotes'] = False
					if result['results'][j]['recipe']['hasImage']:
						grp['previewImageId'] = result['results'][j]['recipe']['previewImageId']
					else:
						grp['previewImageId'] = False
					grp['hasVideo'] = result['results'][j]['recipe']['hasVideo']
					titel = str(result['results'][j]['recipe']['title'])
					grp['title'] = titel
					grp['subtitle'] = str(result['results'][j]['recipe']['subtitle'])
					if result['results'][j]['recipe']['hasVideo']:
						videocount += 1
					self.orgGRP.append(grp)
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
		else:
			return []

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
				self.current = 'postview'
				self.currItem = self['menu'].getSelectedIndex()
				if self.kochId:
					self.showRecipe(self.kochId[self.currItem])
					callInThread(self.fillRecipe)
			elif self.current == 'postview' and self.REZ:
				if self.picCount == 1:
					self.session.openWithCallback(self.showPic, CKfullscreen)
				if self.picCount > 1:
					self.session.open(CKpicshow, self.titel, self.REZ, self.IMG)

	def red(self):
		if self.titellist:
			if self.zufall:
				name = self.name
			else:
				self.currItem = self['menu'].getSelectedIndex()
				name = self.titellist[self.currItem]
			self.session.openWithCallback(self.red_return, MessageBox, "\nRezept '%s' zu den Favoriten hinzufügen?" % name, MessageBox.TYPE_YESNO, timeout=2, default=True)

	def red_return(self, answer):
		if answer is True:
			favoriten = "%sdb/favoriten" % PLUGINPATH
			if self.zufall:
				data = '%s:::%s' % (self.name, self.kochId[self.currItem])
			else:
				self.currItem = self['menu'].getSelectedIndex()
				data = '%s:::%s' % (self.titellist[self.currItem], self.kochId[self.currItem])
			with open(favoriten, 'a') as f:
				f.write(data)
				f.write(linesep)
			self.session.open(CKfavoriten)

	def green(self):
		if self.current == 'postview' and self.REZ:
			if config.plugins.chefkoch.mail.value:
				mailto = config.plugins.chefkoch.mailto.value.split(",")
				mailto = [(i.strip(),) for i in mailto]
				self.session.openWithCallback(self.green_return, ChoiceBox, title='Rezept an folgende E-Mail Adresse senden:', list=mailto)
			else:
				self.session.open(MessageBox, '\nDie E-Mail Funktion ist nicht aktiviert. Aktivieren Sie die E-Mail Funktion im Setup des Plugins.', MessageBox.TYPE_INFO, timeout=5, close_on_any_key=True)
		if self.current == 'menu' and self.sortname:
			self.sort = (self.sort + 1) % len(self.sortname)
			self.currItem = 0
			callInThread(self.fillRlist)

	def green_return(self, answer):
		if answer:
			self.sendRezept(answer[0])

	def sendRezept(self, mailTo):
		effort = ['keine', 'simpel', 'normal', 'pfiffig']
		msgText = '<p>Linkadresse: <a href="%s%s">%s%s</a></p>' % (self.rezept, self.currId, self.rezept, self.currId)
		scoretext = '%1.1f (%s' % (self.REZ['rating']['rating'], "%s Bewertungen)" % self.REZ['rating']['numVotes']) if self.REZ and self.REZ['rating'] else '(ohne Bewertung)'
		preptime = self.REZ['preparationTime'] if self.REZ else ""
		cooktime = self.REZ['cookingTime'] if self.REZ else ""
		resttime = self.REZ['restingTime'] if self.REZ else ""
		totaltime = self.REZ['totalTime'] if self.REZ else ""
		if preptime != 0:
			scoretext += '\nArbeitszeit   : %s' % self.getTimeString(preptime)
		if cooktime != 0:
			scoretext += '\nKoch-/Backzeit: %s' % self.getTimeString(cooktime)
		if resttime != 0:
			scoretext += '\nRuhezeit      : %s' % self.getTimeString(resttime)
		if totaltime != 0:
			scoretext += '\nGesamtzeit    : %s' % self.getTimeString(totaltime)
		msgText += scoretext
		recipetext = '\n\nRezept-Identnr.: %s' % self.currId
		recipetext += '\nAufwand: %s' % (effort[self.REZ['difficulty']] if self.REZ else "")
		recipetext += '\nErstellername : %s' % (self.formatUsername(self.REZ['owner']['username'], self.REZ['owner']['rank'], 22) if self.REZ else "")
		recipetext += '\nErstelldatum: %s' % (self.formatDatum(self.REZ['createdAt']) if self.REZ else "")
		if self.REZ and self.REZ['nutrition']:
			kcalori = self.REZ['nutrition']['kCalories']
			kcalori = str(kcalori) if kcalori else 'k.A.'
			protein = self.REZ['nutrition']['proteinContent']
			protein = '%sg' % protein if protein else 'k.A.'
			fatcont = self.REZ['nutrition']['fatContent']
			fatcont = '%sg' % fatcont if fatcont else 'k.A.'
			carbohyd = self.REZ['nutrition']['carbohydrateContent']
			carbohyd = '%sg' % carbohyd if carbohyd else 'k.A.'
			recipetext += '\n\nkcal  Eiweiß  Fett  Kohlenhydr.'
			recipetext += '\n%s %s %s %s' % (kcalori, protein, fatcont, carbohyd)
		msgText += '%s\n\n' % recipetext
		if self.REZ and self.REZ['subtitle']:
			msgText += 'BESCHREIBUNG: %s\n\n' % self.REZ['subtitle']
		msgText += 'ZUTATEN\n'
		for i in range(len(self.REZ['ingredientGroups']) if self.REZ else 0):
			for j in range(len(self.REZ['ingredientGroups'][i]['ingredients']) if self.REZ else 0):
				if not (i == 0 and j == 0):
					msgText += '; '
				if self.REZ and self.REZ['ingredientGroups'][i]['ingredients'][j]['amount'] != 0:
					msgText += "%s " % str(self.REZ['ingredientGroups'][i]['ingredients'][j]['amount']).replace('.0', '')
					msgText += "%s " % self.REZ['ingredientGroups'][i]['ingredients'][j]['unit']
				msgText += self.REZ['ingredientGroups'][i]['ingredients'][j]['name'] if self.REZ else ""
				msgText += self.REZ['ingredientGroups'][i]['ingredients'][j]['usageInfo'] if self.REZ else ""
		msgText += '\n\nZUBEREITUNG\n%s' % self.REZ['instructions'] if self.REZ else ""
		msgText += '\n%s\nChefkoch.de' % ('_' * 30)
		if fileExists(PICFILE):
			if PY3:
				Image.open(PICFILE).resize((320, 240), Image.LANCZOS).save('/tmp/emailpic.jpg')
			else:
				Image.open(PICFILE).resize((320, 240), Image.ANTIALIAS).save('/tmp/emailpic.jpg')
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
		msgHeader = "'%s' gesendet vom Plugin 'Chefkoch.de'" % self.titel
		msgText = ensure_str(msgText.replace('\n', '<br>').encode('ascii', 'xmlcharrefreplace'))
		msgAlternative.attach(MIMEText('<b>%s</b><br><br><img src="cid:0"><br>%s' % (msgHeader, msgText), 'html'))
		with open('/tmp/emailpic.jpg', 'rb') as img:
			msgImage = MIMEImage(img.read(), _subtype="jpeg")
		msgImage.add_header('Content-ID', '<0>')
		msgRoot.attach(msgImage)
		try:
			if config.plugins.chefkoch.ssl.value:
				server = SMTP_SSL(mailServer, mailPort)
			else:
				server = SMTP(mailServer, mailPort)
		except Exception as err:
			self.CKlog('SMTP_Response_Exception Error:', str(err))
			self.session.open(MessageBox, 'E-Mail konnte aufgrund eines Serverproblems oder fehlerhafter\nAngaben (mailServer oder mailPort) nicht gesendet werden!\nERROR: %s' % str(err), MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)
			return
		try:
			server.login(mailLogin, mailPassword)
		except SMTPResponseException as err:
			self.CKlog('SMTP_Response_Exception Error:', str(err))
			self.session.open(MessageBox, 'E-Mail konnte aufgrund eines Serverproblems oder fehlerhafter\nAnmeldedaten (Login oder Passwort) nicht gesendet werden!\nERROR: %s' % str(err), MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)
			return
		try:
			server.sendmail(mailFrom, mailTo, msgRoot.as_string())
			server.quit()
			self.session.open(MessageBox, 'E-Mail erfolgreich gesendet an: %s' % mailTo, MessageBox.TYPE_INFO, close_on_any_key=True)
		except SMTPResponseException as err:
			self.CKlog('SMTP_Response_Exception Error:', str(err))
			self.session.open(MessageBox, 'E-Mail konnte aufgrund eines Serverproblems oder fehlerhafter\nMailadressen (Absender oder Empfänger) nicht gesendet werden!\nERROR: %s' % str(err), MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)

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
		if self.current != 'postview':
			self.session.openWithCallback(self.numberEntered, CKgetNumber, number, self.maxPics)
		elif self.current == 'postview':
			if number == 0:
				self['textpage'].lastPage()
			elif number == 1:
				if self.comment:
					self.showComments()
				else:
					self.showRezept()

	def numberEntered(self, number):
		if number and number != 0:
			count = int(number)
			if count > self.maxPage:
				count = self.maxPage
				self.session.open(MessageBox, '\nNur %s Seiten verfügbar. Gehe zu Seite %s.' % (count, count), MessageBox.TYPE_INFO, timeout=2, close_on_any_key=True)
			self.currItem = (count - 1) * LINESPERPAGE
			self['menu'].moveToIndex(self.currItem)
			self.setPrevIcons(self.currItem)
			self['label_rezeptnr'].setText('Rezept Nr. %s' % (self.currItem + 1))
			self['pageinfo'].setText('Seite %s von %s' % (int(self.currItem // LINESPERPAGE + 1), self.maxPage))

	def setPrevIcons(self, toppos):
		for i in range(LINESPERPAGE):
			if len(self.picurllist) > toppos + i:
				callInThread(self.Idownload, self.picurllist[toppos + i], i)
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
		elif self.current == 'postview' and self.KOMlen > 0:
			if self.comment:
				self.comment = False
				self.showRezept()
			else:
				self.comment = True
				self.showComments()

	def showComments(self):  # zeige leere Kommentaransicht
		self['label_yellow'].setText('Beschreibung einblenden')
		self['label_1-0'].setText('Erster/Letzer Kommentar')
		self['label_1-0'].show()
		self['button_1-0'].show()
		if self.picCount == 1:
			self['label_ok'].setText('Vollbild')
			self['button_ok'].show()
		elif self.picCount > 1:
			self['label_ok'].setText('%d Rezeptbilder' % (self.IMGlen))
			self['button_ok'].show()
		else:
			self['label_ok'].setText('')
			self['button_ok'].hide()
		self['pageinfo'].hide()
		self['textpage'].setText('')
		callInThread(self.fillComments)

	def fillComments(self):  # fülle die Kommentaransicht
		text = ''
		for idx, kom in enumerate(self.KOM['results']):
			text += 'Kommentar %s/%s von ' % (idx + 1, self.KOMlen)
			text += self.formatUsername(kom['owner']['username'], kom['owner']['rank'], 0)
			text += ' %s Uhr\n' % self.formatDatumZeit(kom['createdAt'])
			text += kom['text']
			if FULLHD:
				repeat = 102 if config.plugins.chefkoch.font_size.value == 'large' else 109
				text += '\n%s\n' % ('_' * repeat)
			else:
				repeat = 96 if config.plugins.chefkoch.font_size.value == 'large' else 105
				text += '\n%s\n' % ('_' * repeat)
		text += '\nChefkoch.de'
		self['textpage'].setText(text)

	def showRezept(self):  # zeige leere Rezeptansicht
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
		if self.picCount == 1:
			self['label_ok'].setText('Vollbild')
			self['button_ok'].show()
		elif self.picCount > 1:
			self['label_ok'].setText('%d Rezeptbilder' % (self.IMGlen))
			self['button_ok'].show()
		else:
			self['label_ok'].setText('')
			self['button_ok'].hide()
		self['textpage'].setText('')
		if self.REZ and self.REZ['hasVideo']:
			self['postvid'].show()
			self['label_play'].setText('Video abspielen')
			self['label_play'].show()
			self['button_play'].show()
		else:
			self['postvid'].hide()
			self['label_play'].hide()
			self['button_play'].hide()
		callInThread(self.fillRezept)

	def fillRezept(self):  # fülle die Rezeptansicht
		text = ''
		if self.REZ and self.REZ['subtitle']:
			text += 'BESCHREIBUNG: %s\n\n' % self.REZ['subtitle']
		text += 'ZUTATEN\n'
		for i in range(len(self.REZ['ingredientGroups']) if self.REZ else 0):
			for j in range(len(self.REZ['ingredientGroups'][i]['ingredients']) if self.REZ else 0):
				if not (i == 0 and j == 0):
					text += '; '
				if self.REZ and self.REZ['ingredientGroups'][i]['ingredients'][j]['amount'] != 0:
					text += "%s " % str(self.REZ['ingredientGroups'][i]['ingredients'][j]['amount']).replace('.0', '')
					text += "%s " % self.REZ['ingredientGroups'][i]['ingredients'][j]['unit']
				text += self.REZ['ingredientGroups'][i]['ingredients'][j]['name'] if self.REZ else ""
				text += self.REZ['ingredientGroups'][i]['ingredients'][j]['usageInfo'] if self.REZ else ""
		text += '\n\nZUBEREITUNG\n%s' % self.REZ['instructions'] if self.REZ else ""
		if FULLHD:
			repeat = 102 if config.plugins.chefkoch.font_size.value == 'large' else 109
		else:
			repeat = 96 if config.plugins.chefkoch.font_size.value == 'large' else 105
		text += '\n%s\nChefkoch.de' % ('_' * repeat)
		self['textpage'].setText(str(text))
		self['picture'].show()

	def Idownload(self, link, i):
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		headers = {"User-Agent": choice(AGENTS), 'Accept': 'application/json'}
		try:
			response = get(link, headers=headers, timeout=(3.05, 6))
			response.raise_for_status()
		except exceptions.RequestException as error:
			self.downloadError(error)
		else:
			picFile = '/tmp/chefkoch%d.jpg' % i
			try:
				with open(picFile, 'wb') as f:
					f.write(response.content)
			except IOError as err:
				print("[Chefkoch] Error writing picFile: %s" % str(err))
			else:
				picload = ePicLoad()
				picload.setPara((self['pic%d' % i].instance.size().width(), self['pic%d' % i].instance.size().height(), 1, 0, 0, 1, "#00000000"))
				if picload.startDecode(picFile, 0, 0, False) == 0:
					ptr = picload.getData()
					if self.current == 'menu' and ptr is not None:
						self['pic%d' % i].instance.setPixmap(ptr)
						self['pic%d' % i].show()

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
			self.current = "menu"
			self.showRlist()
			callInThread(self.fillRlist)

	def playVideo(self):
		if self.current == 'menu':
			self.REZ = self.getREZ(self.kochId[self.currItem])
		if self.REZ and self.REZ['recipeVideoId']:
			content, resp = self.getAPIdata('videos/%s' % self.REZ['recipeVideoId'])
			if resp != 200:
				self.session.openWithCallback(self.eject, MessageBox, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
				self.close()
				return
			result = loads(content)
			sref = eServiceReference(4097, 0, str(result['video_brightcove_url']))
			description = result['video_description']
			if len("%s - %s" % (result['video_title'], description)) < 30:
				sref.setName("%s - %s" % (result['video_title'], result['video_description']))
			else:
				sref.setName(result['video_title'])
			self.session.open(MoviePlayer, sref)


class CKgetNumber(AllScreen):
	def __init__(self, session, number, maxPics):
		self.skin = self.readSkin("CKgetNumber")
		Screen.__init__(self, session, self.skin)
		self.field = str(number)
		self.maxPics = maxPics
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
		if len(self.field) >= 3:
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
		self.dict = {'picpath': '%spic/' % PLUGINPATH}
		skin = self.readSkin("CKpicshow")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session, skin)
		self.session = session
		self.REZ = recipe
		self.IMG = images
		self.titel = titel
		self.currId = str(recipe['id'])
		self.setTitle(titel)
		self.pixlist = []
		self.maxPics = 0
		self.count = 0
		self['stars'] = ProgressBar()
		self['starsbg'] = Pixmap()
		self['stars'].hide()
		self['starsbg'].hide()
		self['scoretext'] = Label('')
		self['scoretext'].hide()
		self['picture'] = Pixmap()
		self['picture'].show()
		self['picindex'] = Label('')
		self['pictext'] = Label('')
		self['label_ok'] = Label()
		self['button_ok'] = Pixmap()
		self['label_left-right'] = Label('')
		self['button_left-right'] = Pixmap()
		self['release'] = Label(RELEASE)
		self['NumberActions'] = NumberActionMap(['NumberActions', 'OkCancelActions', 'DirectionActions', 'ColorActions', 'HelpActions'], {
			'ok': self.ok,
			'cancel': self.exit,
			'right': self.picup,
			'left': self.picdown,
			'up': self.picup,
			'down': self.picdown,
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
		}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self['label_ok'].setText('Vollbild')
		self['button_ok'].show()
		self['label_left-right'].setText('Zurück / Vorwärts')
		self['label_left-right'].show()
		self['button_left-right'].show()
		self.count = 0
		self.setTitle(str(self.titel))
		if self.REZ['subtitle']:
			self['pictext'].setText('BESCHREIBUNG: %s' % self.REZ['subtitle'])
		if self.REZ['rating']:
			score = self.REZ['rating']['rating'] * 20
			scoretext = "%s (%s Bewertungen)" % (self.REZ['rating']['rating'], self.REZ['rating']['numVotes'])
		else:
			score = 0.0
			scoretext = '(ohne Bewertung)'
		self['starsbg'].show()
		self['stars'].show()
		self['stars'].setValue(score)
		self['scoretext'].setText(scoretext)
		self['scoretext'].show()
		if self.IMG['count'] > 0:
			for i in range(len(self.IMG['results'])):
				self.pixlist.append(self.IMG['results'][i]['id'])
			picurl = "%s%s/bilder/%s/crop-960x720/%s.jpg" % (PICURLBASE, self.currId, self.REZ['previewImageId'], self.titel)
			callInThread(self.Pdownload, picurl)
			self.maxPics = len(self.pixlist) - 1
			username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
			self['picindex'].setText('Bild %d von %d\nvon %s' % (self.count + 1, self.maxPics + 1, username))
		else:
			self.session.open(MessageBox, '\nKein Foto vorhanden', MessageBox.TYPE_INFO, timeout=2, close_on_any_key=True)

	def formatUsername(self, username, rank, trim=100):
		return 'Unbekannt' if "unknown" in username else "%s (%s)" % (username, rank)[:trim]

	def ok(self):
		self.session.openWithCallback(self.showPic, CKfullscreen)

	def picup(self):
		self.count += 1 if self.count < self.maxPics else - self.count
		picurl = "%s%s/bilder/%s/crop-960x720/%s.jpg" % (PICURLBASE, self.currId, self.IMG['results'][self.count]['id'], self.titel) if self.REZ['hasImage'] else NOPICURL
		callInThread(self.Pdownload, picurl)
		username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
		self['picindex'].setText('Bild %d von %d\nvon %s' % (self.count + 1, self.maxPics + 1, username))

	def picdown(self):
		self.count -= 1 if self.count > 0 else - self.maxPics
		picurl = "%s%s/bilder/%s/crop-960x720/%s.jpg" % (PICURLBASE, self.currId, self.IMG['results'][self.count]['id'], self.titel) if self.REZ['hasImage'] else NOPICURL
		callInThread(self.Pdownload, picurl)
		username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
		self['picindex'].setText('Bild %d von %d\nvon %s' % (self.count + 1, self.maxPics + 1, username))

	def gotoPic(self, number):
		self.session.openWithCallback(self.numberEntered, CKgetNumber, number, self.maxPics)

	def numberEntered(self, number):
		if number > self.maxPics + 1:
			number = self.maxPics + 1
		self.count = number - 1
		picurl = "%s%s/bilder/%s/crop-960x720/%s.jpg" % (PICURLBASE, self.currId, self.IMG['results'][self.count]['id'], self.titel) if self.REZ['hasImage'] else NOPICURL
		self.pixlist[self.count]
		callInThread(self.Pdownload, picurl)
		username = self.formatUsername(self.IMG['results'][self.count]['owner']['username'], self.IMG['results'][self.count]['owner']['rank'], 22)
		self['picindex'].setText('Bild %d von %d\nvon %s' % (self.count + 1, self.maxPics + 1, username))

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class CKfullscreen(AllScreen):
	def __init__(self, session):
		global HIDEFLAG
		HIDEFLAG = True
		self.dict = {'picpath': '%spic/' % PLUGINPATH}
		skin = self.readSkin("CKfullscreen")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session, skin)
		self.session = session
		self.hideflag = True
		self['picture'] = Pixmap()
		self['picture'].show()
		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'],
			{
			'ok': self.exit,
			'cancel': self.exit,
			'blue': self.hideScreen
			}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self.showPic()

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


class CKfavoriten(AllScreen):
	def __init__(self, session, favmode=True):
		global HIDEFLAG
		HIDEFLAG = True
		self.dict = {'picpath': '%spic/' % PLUGINPATH}
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
			'0': self.move2end,
			'1': self.move2first
		}, -1)
		self.makeFav()

	def makeFav(self):
		if self.favmode:
			self.setTitle("Chefkoch - Favoriten")
			self.favoriten = "%sdb/favoriten" % PLUGINPATH
		else:
			self.setTitle("Chefkoch - letzte Suchbegriffe")
			self.favoriten = "%sdb/suchen" % PLUGINPATH
			titel = ">>> Neue Suche <<<"
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
						res = ['']
						res.append(MultiContentEntryText(pos=(4, 0), size=(int(570 * SCALE), int(34 * SCALE)), font=-2, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=titel))
						self.faventries.append(res)
						self.favlist.append(titel)
						self.favId.append(favline[1].replace('\n', ''))
		self['favmenu'].l.setList(self.faventries)
		self['favmenu'].l.setItemHeight(int(34 * SCALE))

	def ok(self):
		self.currItem = self.getIndex(self['favmenu'])
		if len(self.favlist) > 0:
			titel = self.favlist[self.currItem]
			if self.favmode:
				self.session.open(CKview, self.favId[self.currItem], "'%s'" % titel, 1, True, False)
			elif titel == '>>> Neue Suche <<<':
				titel = ''
				self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Chefkoch - Suche Rezepte:', text=titel)
			else:
				self.session.open(CKview, titel, "mit '%s' gefundene Rezepte" % titel, 0, False, False)

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
					f.write("%s:::%s" % (search, search))
					f.write(linesep)
			self.session.openWithCallback(self.exit, CKview, search, "mit '%s' gefundene Rezepte" % search, 0, False, False)

	def red(self):
		if len(self.favlist) > 0:
			try:
				self.currItem = self.getIndex(self['favmenu'])
				name = self.favlist[self.currItem]
			except IndexError:
				name = ''
			if name != '>>> Neue Suche <<<' and name != '':
				text = "\nRezept '%s' aus den Favoriten entfernen?" if self.favmode else "\nsuche '%s' aus den letzten Suchbegriffen entfernen?"
				self.session.openWithCallback(self.red_return, MessageBox, text % name, MessageBox.TYPE_YESNO, timeout=2, default=False)

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
				newfavs = "%s.new" % self.favoriten
				with open(newfavs, "w") as fnew:
					fnew.write(data)
				rename(newfavs, self.favoriten)
			self.favlist = []
			self.favId = []
			self.faventries = []
			self.makeFav()

	def move2first(self):
		self.currItem = self.getIndex(self['favmenu'])
		fav = "%s:::%s" % (self.favlist[self.currItem], self.favId[self.currItem])
		newfavs = "%s.new" % self.favoriten
		with open(newfavs, 'w') as fnew:
			fnew.write(fav)
		data = ''
		with open(self.favoriten, 'r') as f:
			for line in f:
				if fav not in line and line != '\n':
					data = data + line
		with open(newfavs, 'a') as fnew:
			fnew.write(data)
		rename(newfavs, self.favoriten)
		self.favlist = []
		self.favId = []
		self.faventries = []
		self.makeFav()

	def move2end(self):
		self.currItem = self.getIndex(self['favmenu'])
		fav = "%s:::%s" % (self.favlist[self.currItem], self.favId[self.currItem])
		data = ''
		with open(self.favoriten, 'r') as f:
			for line in f:
				if fav not in line and line != '\n':
					data = data + line
		newfavs = "%s.new" % self.favoriten
		with open(newfavs, 'w') as fnew:
			fnew.write(data)
		with open(newfavs, 'a') as fnew:
			fnew.write(fav)
		rename(newfavs, self.favoriten)
		self.favlist = []
		self.favId = []
		self.faventries = []
		self.makeFav()

	def getIndex(self, list):
		return list.getSelectedIndex()

	def down(self):
		self['favmenu'].down()

	def up(self):
		self['favmenu'].up()

	def exit(self):
		if ALPHA and not HIDEFLAG:
			with open(ALPHA, 'w') as f:
				f.write('%i' % config.av.osd_alpha.value)
		self.close()


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
		global HIDEFLAG
		self.session = session
		HIDEFLAG = True
		if not ALPHA:
			self.CKlog('Alphachannel not found! Hide/Show-Function (=blue button) disabled')
		self.dict = {'picpath': '%spic/' % PLUGINPATH}
		skin = self.readSkin("CKmain")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session, skin)
		self.apidata = None
		self.mainId = None
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
		self['totalrecipes'] = Label('')
		self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'InfoActions', 'MenuActions'], {
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
			'menu': self.config
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
					query = '%s%s' % (self.mainmenuquery[self.currItem], '&orderBy=6')  # 6= sort by 'createdAt'
					self.session.openWithCallback(self.selectMainMenu, CKview, query, "'%s'" % self.mainmenutitle[self.currItem], sort, False, False)

		elif self.actmenu == 'secondmenu':
			secondId = self.secondId[self.currItem]
			if self.currKAT and list(filter(lambda i: i['parentId'] == secondId, self.currKAT)):
				callInThread(self.makeThirdMenu, secondId)
			else:
				sort = 3 if self.CKvideo else 1  # Videosortierung für "Chefkoch Video"
				query = '%s%s' % (self.secondmenuquery[self.currItem], '&orderBy=3')  # 3= sort by 'rating'
				self.session.openWithCallback(self.selectSecondMenu, CKview, query, "'%s'" % self.secondmenutitle[self.currItem], sort, False, False)

		elif self.actmenu == 'thirdmenu':
			sort = 3 if self.CKvideo else 1  # Videosortierung für "Chefkoch Video"
			query = '%s%s' % (self.thirdmenuquery[self.currItem], '&orderBy=3')  # 3= sort by 'rating'
			self.session.openWithCallback(self.selectThirdMenu, CKview, query, "'%s'" % self.thirdmenutitle[self.currItem], sort, False, False)

	def makeMainMenu(self):
		content, resp = self.getAPIdata('recipes?limit=1')
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
			self.close()
			return
		self.setTitle('Hauptmenü')
		self['totalrecipes'].setText('%s%s' % (loads(content)['count'], ' Rezepte'))
		self.NKAT = {}  # Normalkategorien
		self.VKAT = []  # Videokategorien
		self.MKAT = []  # Magazinkategorien
		self.mainmenulist = []
		self.mainmenuquery = []
		self.mainmenutitle = []
		self.mainId = []
		self.currKAT = self.getNKAT()
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
		if self.currKAT:
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
			for currkat in self.currKAT:
				if currkat['id'] == parentId:
					self.setTitle(currkat['title'])
					break
			self.selectSecondMenu()

	def makeThirdMenu(self, parentId):
		self.thirdmenulist = []
		self.thirdmenuquery = []
		self.thirdmenutitle = []
		if self.currKAT:
			for currkat in self.currKAT:
				res = ['']
				if currkat['level'] == 3 and currkat['parentId'] == parentId:
					res.append(MultiContentEntryText(pos=(0, 1), size=(int(570 * SCALE), int(30 * SCALE)), font=-2, flags=RT_HALIGN_CENTER, text=currkat['descriptionText']))
					self.thirdmenulist.append(res)
					self.thirdmenuquery.append(currkat['descriptionText'])
					self.thirdmenutitle.append(currkat['descriptionText'])
			self['thirdmenu'].l.setList(self.thirdmenulist)
			self['thirdmenu'].l.setItemHeight(int(34 * SCALE))
			self['thirdmenu'].moveToIndex(0)
			for currkat in self.currKAT:
				if currkat['id'] == parentId:
					self.setTitle(currkat['title'])
					break
			self.selectThirdMenu()

	def makeVKATdb(self):  # hole alle verfügbaren Videokategorien
		content, resp = self.getAPIdata('videos?&offset=0&limit=10000')
		if resp != 200:
			self.session.openWithCallback(self.eject, MessageBox, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
			self.close()
			return
		result = loads(content)
		VKAT = []
		with open("%sdb/VKATdb" % PLUGINPATH, "a") as f:
			for i in range(len(result)):
				data = result[i]['video_format']
				if data != 'unknown':
					if ''.join(x for x in data if x.isdigit()) not in VKAT:
						VKAT.append(id)
						f.write("%s|%s\n" % (data, data))

	def getNKAT(self):  # erzeuge die normale Kategorie
		if not self.NKAT:
			content, resp = self.getAPIdata('recipes/categories')
			if resp != 200:
				self.session.openWithCallback(self.eject, MessageBox, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
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
			datapath = "%sdb/VKATdb" % PLUGINPATH
			if not fileExists(datapath):
				self.makeVKATdb()  # wird nur bei fehlender VKATdb erzeugt (= Notfall)
			i = 1000  # erzeuge eigene Video-IDs über 1000
			with open(datapath, "r") as f:
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
				self.session.openWithCallback(self.eject, '\nFehlermeldung vom Chefkoch.de Server: %s' % resp, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)
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
			if fileExists(PICFILE):
				remove(PICFILE)
			if fileExists(self.rezeptfile):
				remove(self.rezeptfile)
			self.close()
		elif self.actmenu == 'secondmenu':
			self.currKAT = self.getNKAT()
			self.setTitle('Hauptmenü')
			self.selectMainMenu()
		elif self.actmenu == 'thirdmenu':
			if self.currKAT:
				for currkat in self.currKAT:
					if currkat['id'] == self.parentId:
						self.setTitle(currkat['title'])
						break
			self.selectSecondMenu()


class CKconfig(ConfigListScreen, AllScreen):
	def __init__(self, session):
		self.dict = {'picpath': '%spic/' % PLUGINPATH}
		skin = self.readSkin("CKconfig")
		self.skin = self.applySkinVars(skin, self.dict)
		Screen.__init__(self, session)
		self['VKeyIcon'] = Boolean(False)
		self.password = config.plugins.chefkoch.password.value
		self['plugin'] = Pixmap()
		clist = []
		clist.append(getConfigListEntry('Schriftgröße Rezepte/Kommentare:', config.plugins.chefkoch.font_size, "Schriftgröße Langtexte"))
		clist.append(getConfigListEntry('Maximale Anzahl Rezepte:', config.plugins.chefkoch.maxrecipes, "Maximale Anzahl Rezepte"))
		clist.append(getConfigListEntry('Maximale Anzahl Kommentare:', config.plugins.chefkoch.maxcomments, "Maximale Anzahl Kommentare"))
		clist.append(getConfigListEntry('Maximale Anzahl Rezeptbilder:', config.plugins.chefkoch.maxpictures, "Maximale Anzahl Rezeptbilder"))
		clist.append(getConfigListEntry('Versende Rezepte per E-Mail:', config.plugins.chefkoch.mail, "Versende Rezepte per E-Mail"))
		clist.append(getConfigListEntry('*E-Mail Absender:', config.plugins.chefkoch.mailfrom, "E-Mail Absender"))
		clist.append(getConfigListEntry('*E-Mail Empfänger:', config.plugins.chefkoch.mailto, "E-Mail Empfänger"))
		clist.append(getConfigListEntry('*E-Mail Login:', config.plugins.chefkoch.login, "E-Mail Login"))
		clist.append(getConfigListEntry('*E-Mail Passwort:', config.plugins.chefkoch.password, "E-Mail Passwort"))
		clist.append(getConfigListEntry('*E-Mail Server:', config.plugins.chefkoch.server, "E-Mail Server"))
		clist.append(getConfigListEntry('*E-Mail Server Port:', config.plugins.chefkoch.port, "E-Mail Server Port"))
		clist.append(getConfigListEntry('*E-Mail Server SSL:', config.plugins.chefkoch.ssl, "E-Mail Server SSL"))
		clist.append(getConfigListEntry('DebugLog', config.plugins.chefkoch.debuglog, "Debug Logging aktivieren"))
		clist.append(getConfigListEntry('Log in Datei', config.plugins.chefkoch.logtofile, "Log in Datei '/home/root/logs'"))

		self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {
			'cancel': self.keyCancel,
			'red': self.keyCancel,
			'green': self.keySave
		}, -2)
		ConfigListScreen.__init__(self, clist, on_change=self.UpdateComponents)
		self.onLayoutFinish.append(self.UpdateComponents)

	def UpdateComponents(self):
		png = "%spic/setup/%s'.png" % (PLUGINPATH, "FHD" if FULLHD else "HD")
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

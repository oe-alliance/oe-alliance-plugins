# PYTHON IMPORTS
from json import loads
from os.path import join, exists
from re import findall, search, S
from random import choice
from requests import get, exceptions
from twisted.internet.reactor import callInThread
from Tools.BoundFunction import boundFunction

# ENIGMA IMPORTS
from enigma import getDesktop, ePoint
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config, ConfigSelection, ConfigSubsection, ConfigText
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Setup import Setup
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap


class CTglobs():
	MODULE_NAME = __name__.split(".")[-2]
	PLUGINPATH = f"{resolveFilename(SCOPE_PLUGINS)}Extensions/{MODULE_NAME}/"
	RESOLUTION = "fHD" if getDesktop(0).size().width() > 1300 else "HD"
	BASEURL = "http://www.clever-tanken.de"
	SORTDICT = {"p": "€", "km": "km", "abc": "A-Z", "keine": "keine"}
	RADIUSDICT = {'1': '1 km', '2': '2 km', '5': '5 km', '10': '10 km', '15': '15 km', '20': '20 km', '25': '25 km'}
	SPRITDICT = {'3': 'Diesel', '5': 'Super E10', '7': 'Super E5', '6': 'SuperPlus', '12': 'Premium Diesel',
				 '264': 'GTL-Diesel', '2': 'LKW-Diesel', '1': 'LPG', '8': 'CNG', '262': 'LNG', '4': 'Bioethanol',
				 '266': 'AdBlue PKW', '13': 'AdBlue LKW', '246': 'Wasserstoff', '314': 'HVO Diesel'}

	def download(self, url, callback):
		AGENTS = [
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
				"Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
				"Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edge/87.0.664.75",
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"
				]
		headers = {"User-Agent": choice(AGENTS)}
		try:
			response = get(url.encode(), headers=headers, timeout=(3.05, 6))
			response.raise_for_status()
		except exceptions.RequestException as error:
			print("[%s] ERROR in module 'download': %s" % (self.MODULE_NAME, str(error)))
		else:
			callback(response.content.decode())


class CTinfo(Screen):
	skin = """
	<screen name="tankenInfo" position="990,150" size="510,798" zPosition="2" flags="wfNoBorder" resolution="1920,1080" title="Tankstellendetails" >
		<eLabel position="0,0" size="510,798" backgroundColor="grey" zPosition="-1" />
		<widget source="info" render="Label" position="5,5" size="500,788" font="Regular;27" backgroundColor="#10233d67" halign="center" valign="top" transparent="0" zPosition="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["info"] = StaticText("")

	def moveInfo(self, xpos, ypos):
		self.instance.move(ePoint(xpos, ypos))


class CTmain(Screen, CTglobs):
	skin = """
	<screen name="CleverTankenMain" position="center,center" size="1863,1032" resolution="1920,1080" title="" flags="wfNoBorder">
		<eLabel position="0,75" size="1860,1032" backgroundColor="#10152e4e" zPosition="-2" />
		<ePixmap position="9,6" size="255,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CleverTanken/pic/ct_logo.png" alphatest="blend" scale="1" zPosition="1" />
		<ePixmap position="1095,15" size="45,45" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CleverTanken/pic/key_ok.png" alphatest="blend" scale="1" zPosition="1" />
		<ePixmap position="1418,15" size="45,45" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CleverTanken/pic/key_menu.png" alphatest="blend" scale="1" zPosition="1" />
		<widget source="key_ok" render="Label" position="1149,15" size="249,45" font="Regular;30" foregroundColor="#10233d67" backgroundColor="#10afb9cf" halign="left" valign="center" />
		<widget source="key_menu" render="Label" position="1473,15" size="250,45" font="Regular;30" foregroundColor="#10233d67" backgroundColor="#10afb9cf" halign="left" valign="center" />
		<eLabel position="0,75" size="921,45" backgroundColor="#103B5AA2" zPosition="-1" />
		<widget source="headline_A" render="Label" position="12,75" size="900,45" font="Regular;30" halign="left" valign="center" foregroundColor="white" backgroundColor="#103B5AA2" />
		<widget source="frameAactive" render="Label" conditional="frameAactive" position="0,120" size="921,810" backgroundColor="#00c8ff12" zPosition="-1">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="frame_A" render="Listbox" position="6,126" size="909,795" backgroundColor="#10f5f5f5" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/CleverTanken/pic/selector_%s.png" enableWrapAround="1" scrollbarMode="showNever" scrollbarBorderWidth="2" scrollbarForegroundColor="#10f5f5f5" scrollbarBorderColor="#7e7e7e">
			<convert type="TemplatedMultiContent">
				{"template": [  # index 0 is the identnumber (here unused)
				MultiContentEntryText(pos=(0,0), size=(906,114), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e"),  # background filler
				MultiContentEntryText(pos=(7,0), size=(99,90), font=0, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=1),  # price main
				MultiContentEntryText(pos=(108,2), size=(30,60), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=2),  # price suffix
				MultiContentEntryText(pos=(138,3), size=(126,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=3),  # changetype
				MultiContentEntryText(pos=(138,39), size=(126,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=4),  # changedate
				MultiContentEntryText(pos=(138,75), size=(126,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=5),  # changedurance
				MultiContentEntryText(pos=(315,0), size=(591,39), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=6),  # name
				MultiContentEntryText(pos=(315,39), size=(540,36), font=2, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=7),  # street
				MultiContentEntryText(pos=(315,75), size=(540,36), font=2, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=8),  # zipcode
				MultiContentEntryText(pos=(774,33), size=(105,45), font=1,color="#10152e4e",  backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=9),  # distance
				MultiContentEntryText(pos=(273,0), size=(30,45), font=1, color="#103B5AA2", backcolor="#10f5f5f5", color_sel="yellow", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=10),  # favorite
				MultiContentEntryPixmapAlphaBlend(pos=(60,70), size=(39,39), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER|BT_SCALE|BT_KEEP_ASPECT_RATIO, png=11)  # pricealert
				],
				"fonts": [gFont("Regular",42), gFont("Regular",30), gFont("Regular",27), gFont("Regular",24)],
				"itemHeight":114
				}
			</convert>
		</widget>
		<eLabel position="939,75" size="921,45" backgroundColor="#103B5AA2" zPosition="-1" />
		<widget source="headline_B" render="Label" position="948,75" size="900,45" font="Regular;30" halign="left" valign="center" foregroundColor="white" backgroundColor="#103B5AA2" />
		<widget source="frameBactive" render="Label" conditional="frameBactive" position="939,120" size="921,810" backgroundColor="#00c8ff12" zPosition="-1">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="frame_B" render="Listbox" position="945,126" size="909,795" backgroundColor="#10f5f5f5" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/CleverTanken/pic/selector_%s.png" enableWrapAround="1" scrollbarMode="showNever" scrollbarBorderWidth="2" scrollbarForegroundColor="#10f5f5f5" scrollbarBorderColor="#7e7e7e">
			<convert type="TemplatedMultiContent">
				{"template": [  # index 0 is the identnumber (here unused)
				MultiContentEntryText(pos=(0,0), size=(906,114), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e"),  # background filler
				MultiContentEntryText(pos=(7,0), size=(99,90), font=0, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=1),  # price main
				MultiContentEntryText(pos=(108,2), size=(30,60), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=2),  # price suffix
				MultiContentEntryText(pos=(138,3), size=(126,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=3),  # changetype
				MultiContentEntryText(pos=(138,39), size=(126,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=4),  # changedate
				MultiContentEntryText(pos=(138,75), size=(126,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=5),  # changedurance
				MultiContentEntryText(pos=(315,0), size=(591,39), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=6),  # name
				MultiContentEntryText(pos=(315,39), size=(540,36), font=2, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=7),  # street
				MultiContentEntryText(pos=(315,75), size=(540,36), font=2, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=8),  # zipcode
				MultiContentEntryText(pos=(774,33), size=(105,45), font=1,color="#10152e4e",  backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=9),  # distance
				MultiContentEntryText(pos=(273,0), size=(30,45), font=1, color="#103B5AA2", backcolor="#10f5f5f5", color_sel="yellow", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=10),  # favorite
				MultiContentEntryPixmapAlphaBlend(pos=(60,70), size=(39,39), flags=BT_HALIGN_LEFT|BT_VALIGN_CENTER|BT_SCALE|BT_KEEP_ASPECT_RATIO, png=11)  # pricealert
				],
				"fonts": [gFont("Regular",42), gFont("Regular",30), gFont("Regular",27), gFont("Regular",24)],
				"itemHeight":114
				}
			</convert>
		</widget>
		<eLabel name="red" position="15,951" size="9,68" backgroundColor="red" zPosition="1" />
		<eLabel name="green" position="444,951" size="9,68" backgroundColor="green" zPosition="1" />
		<eLabel name="yellow" position="960,951" size="9,68" backgroundColor="yellow" zPosition="1" />
		<eLabel name="blue" position="1419,951" size="9,68" backgroundColor="blue" zPosition="1" />
		<widget source="ukey_red" render="Label" position="36,942" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="dkey_red" render="Label" position="36,987" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="ukey_green" render="Label" position="465,942" size="471,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="dkey_green" render="Label" position="465,987" size="471,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="ukey_yellow" render="Label" position="981,942" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="dkey_yellow" render="Label" position="981,987" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="ukey_blue" render="Label" position="1440,942" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="dkey_blue" render="Label" position="1440,987" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<eLabel name="line" position="6,240" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,354" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,468" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,582" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,696" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,810" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,240" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,354" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,468" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,582" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,696" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,810" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
	</screen>""" % (CTglobs.RESOLUTION, CTglobs.RESOLUTION)

	def __init__(self, session):
		Screen.__init__(self, session)
		favorites = config.plugins.clevertanken.favorites.value
		self.favlist = favorites.split(",") if favorites else []
		self.ready = False
		self.showInfo = self.session.instantiateDialog(CTinfo)
		self.isInfo = False
		self.currframe = "A"
		self.sort = {}
		self.sprit = {}
		self.radius = {}
		self.identdict = {}
		self.framefavs = []
		self.frameBmode = config.plugins.clevertanken.startframeB.value
		self.twaittext = "Tankstellen werden geladen..."
		self.fwaittext = "Favoriten werden geladen..."
		self.getConfigs()
		self.setEvadePosition()
		self["frame_A"] = List([])
		self["frame_B"] = List([])
		self["frameAactive"] = StaticText(" ")
		self["frameBactive"] = StaticText()
		self["headline_A"] = StaticText()
		self["headline_B"] = StaticText()
		self["ukey_red"] = StaticText()
		self["dkey_red"] = StaticText()
		self["ukey_green"] = StaticText()
		self["dkey_green"] = StaticText()
		self["ukey_yellow"] = StaticText()
		self["dkey_yellow"] = StaticText()
		self["ukey_blue"] = StaticText()
		self["dkey_blue"] = StaticText()
		self["key_ok"] = StaticText("Details ein/aus")
		self["key_menu"] = StaticText("Einstellungen")
		self["actions"] = ActionMap(["OkCancelActions",
									"DirectionActions",
									"MenuActions",
		 							"ColorActions"], {"ok": self.ok,
		 											"cancel": self.exit,
		 											"right": self.toggleFrame,
		 											"left": self.toggleFrame,
		 											"down": self.down,
		 											"up": self.up,
													"chplus": self.pageUp,
													"chminus": self.pageDown,
		 											"red": boundFunction(self.selectSort, "A"),
													"redlong": boundFunction(self.selectSprit, "A"),
		 											"green": boundFunction(self.selectRadius, "A"),
													"greenlong": self.changeFavorites,
		 											"yellow": boundFunction(self.selectSort, "B"),
		 											"yellowlong": boundFunction(self.selectSprit, "B"),
		 											"blue": boundFunction(self.selectRadius, "B"),
		 											"bluelong": self.toggleFrame_B,
		 											"menu": self.config
		 											}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self.refreshButtons()
		self.refreshFrame("AB")

	def refreshFrame(self, frames):
		for frame in frames:
			waittext = self.fwaittext if frame == "B" and self.frameBmode == "F" else self.twaittext
			self[f"headline_{frame}"].setText(waittext)
			self[f"frame_{frame}"].updateList([])
			if frame == "B" and self.frameBmode == "F":
				if self.favlist:
					self.ready = False
					self.framefavs = []
					for ident in self.favlist:
						callInThread(self.download, f"{self.BASEURL}/tankstelle_details/{ident}?spritsorte={self.sprit[frame]}", self.makeFavoriteView)
				else:
					self[f"frame_{frame}"].updateList([tuple(("", "", "", "", "", "", "keine Favoriten vorhanden", "", "", "", ""))])
			else:
				callInThread(self.download, self.createLink(frame), boundFunction(self.makeTankenView, frame))

	def getConfigs(self):
		self.sort["A"] = config.plugins.clevertanken.sortA.value
		self.sort["B"] = config.plugins.clevertanken.sortB.value
		self.sprit["A"] = config.plugins.clevertanken.spritA.value
		self.sprit["B"] = config.plugins.clevertanken.spritB.value if self.frameBmode == "Z" else config.plugins.clevertanken.spritF.value
		self.radius["A"] = config.plugins.clevertanken.radiusA.value
		self.radius["B"] = config.plugins.clevertanken.radiusB.value
		self.alertlist = (
						("red", config.plugins.clevertanken.priceRed.value, config.plugins.clevertanken.spritRed.value),
						("yellow", config.plugins.clevertanken.priceYellow.value, config.plugins.clevertanken.spritYellow.value),
						("green", config.plugins.clevertanken.priceGreen.value, config.plugins.clevertanken.spritGreen.value)
						)

	def createLink(self, frame):
		if frame == "A":
			zipname = config.plugins.clevertanken.cityAzipname.value.replace(" ", "+").replace("/", "%2F")
			geodata = eval(config.plugins.clevertanken.cityAgeodata.value)
		else:
			zipname = config.plugins.clevertanken.cityBzipname.value.replace(" ", "+").replace("/", "%2F")
			geodata = eval(config.plugins.clevertanken.cityBgeodata.value)
		return f'{self.BASEURL}/tankstelle_liste?lat={geodata[0]}&lon={geodata[1]}&ort={zipname}&spritsorte={self.sprit[frame]}&r={self.radius[frame]}&sort={self.sort[frame]}'

	def makeTankenView(self, frame, output):
		startpos = output.find('<div class="background-row-container background-mat-blue">')
		endpos = output.find('<div class="pagination d-flex justify-content-center align-items-center mt-2">')
		identlist = []
		framelist = []
		maxentries = config.plugins.clevertanken.maxentries.value
		for counter, eintrag in enumerate(output[startpos:endpos].split('<a href="/tankstelle_details/')[1:]):
			if maxentries and counter >= maxentries:
				break
			ident = eintrag[:eintrag.find('"')]
			identlist.append(ident)
			prices = self.searchOneValue(r'<div class="price-text price text-color-ct-blue">\s+(.*?)\s+</div>', eintrag, "", flag_S=True)
			if prices and prices[0]:
				price = prices.replace("</sup>", "").split("<sup>") if prices and prices[0] != " " else ("nicht\ngeöffnet", "")  # example: ['1.75', '9']
				change = findall(r'<span class="price-changed">(.*?)\s*</span>', eintrag, S)
				cnglen = len(change) if change else 0
				firstline = change[0].split("<br>")
				lenfline = len(firstline) if firstline else 0
				if len(firstline) < 3:  # normal case: '<span class="price-changed">geändert<br></span> <span class="price-changed">Heute<br></span> <span class="price-changed">vor 38 Min.</span>'
					pcngtype = change[0].replace("<br>", "") if cnglen > 0 else "unbekannt"
					pcngdate = change[1].replace("<br>", "") if cnglen > 1 else "unbekannt"
					pcngdur = change[2].replace("<br>", "") if cnglen > 2 else "unbekannt"
				else:  # special case: <span class="price-changed">geändert<br>Gestern<br> <span class="price-changed"></span>23:12 Uhr</span>
					pcngtype = firstline[0] if lenfline > 0 else "unbekannt"
					pcngdate = firstline[1] if lenfline > 1 else "unbekannt"
					pcngdur = self.searchOneValue(r'<span class="price-changed"></span>(.*?)</span>', eintrag, "unbekannt", flag_S=True)
				if pcngdate == "unbekannt" and pcngdur == "unbekannt":  # special case: use alternative method for older entry dates
					part = pcngtype.split(" ")
					if len(part) > 3:
						pcngtype = part[0]
						pcngdate = part[2]
						pcngdur = part[3].replace("&nbsp;", " ")
			else:
				price, pcngtype, pcngdate, pcngdur = (("zu", ""), "Tankstelle", "momentan", "geschlossen")
			name = self.searchOneValue(r'<span class="fuel-station-location-name">(.*?)</span>', eintrag, "kein Name gefunden")
			street = self.searchOneValue(r'<div class="fuel-station-location-street">(.*?)</div>', eintrag, "kein Straßennamen gefunden")
			zipcode = self.searchOneValue(r'<div class="fuel-station-location-city">(.*?)</div>', eintrag, "kein Ort gefunden").strip()
			distance = self.searchOneValue(r'<div class="fuel-station-location-distance d-flex justify-content-end">\s+<span>(.*?)</span>\s+</div>', eintrag, "keine Distanz gefunden", flag_S=True)
			favorite = "♥" if ident in self.favlist else ""
			pricealert = self.createPricealert(price, self.sprit[frame])
			framelist.append(tuple((ident, price[0], price[1], pcngtype, pcngdate, pcngdur, name, street, zipcode, distance, favorite, pricealert)))
		self.identdict[frame] = identlist
		self[f"frame_{frame}"].updateList(framelist)
		zipname = config.plugins.clevertanken.cityAzipname.value if frame == "A" else config.plugins.clevertanken.cityBzipname.value
		self[f"headline_{frame}"].setText(f"Hauptort: {zipname} | {len(identlist)} Tankstellen")
		self.ready = True
		self.refreshInfo()

	def makeTankenInfo(self, output):
		name = self.searchOneValue(r'itemprop="name">(.*?)</span>', output, "")
		street = self.searchOneValue(r'<span itemprop="streetAddress">(.*?)</span>', output, "")
		zipcode = self.searchOneValue(r'<span itemprop="http://schema.org/postalCode">(.*?)</span>', output, "")
		city = self.searchOneValue(r'<span itemprop="http://schema.org/addressCountry">(.*?)</span>', output, "")
		openlist = []
		for rawentry in findall(r'<div class="d-flex justify-content-between weak-body">(.*?)</div>', output, S):
			opendata = rawentry.replace("<span>", "").replace("</span>", "").replace("&nbsp;", "").strip().split("\n")
			if len(opendata) > 1:
				opendata[1] = opendata[1].strip()
			openlist.append(" ".join(opendata))
		openings = "\n".join(openlist)
		rawentry = self.searchOneValue(r'<div class="price-footer row col-12 text text-color-ice-blue d-flex flex-column">(.*?)</div>', output, "", flag_S=True)
		lastlist = []
		for last in rawentry.replace("<span>", "").replace("</span>", "").strip().split("\n"):
			part = last.split(": ")
			lastlist.append(f"{part[0]}\n{part[1]}" if len(part) > 1 else "")
		lastlist[1] = lastlist[1].strip() if len(lastlist) > 1 else ""
		lastdates = "\n".join(lastlist)
		prices = ""
		for rawentry in output.split('<div class="price-type col-6 d-flex flex-column justify-content-start headline">')[1:]:
			sprittype = self.searchOneValue(r'<div class="price-type-name">(.*?)</div>', rawentry, "")
			price = self.searchOneValue(r'<span id="current-price-.d*">(.*?)</span>', rawentry, "")
			price += self.searchOneValue(r'<sup id="suffix-price-.d*">(.*?)</sup>', rawentry, "")
			pricetype = self.searchOneValue(r'<div class="price-type-mtsk">(.*?)</div>', rawentry, "").strip()
			prices += f"{sprittype}: {price}{f' ({pricetype})' if pricetype else ''}\n"
		infos = f"{name}\n{street}\n{zipcode} {city}\n\nÖffnungszeiten:\n{openings}\n\nKraftstoffpreise:\n{prices}\n{lastdates}"
		self.showInfo['info'].setText(infos)
		self.showInfo.show()
		self.isInfo = True
		self.ready = True

	def makeFavoriteView(self, output):
		spritdict = self.SPRITDICT
		ident = self.searchOneValue(r"var object_id = '(.*?)'", output, "")
		name = self.searchOneValue(r'itemprop="name">(.*?)</span>', output, "")
		street = self.searchOneValue(r'<span itemprop="streetAddress">(.*?)</span>', output, "")
		zipcode = self.searchOneValue(r'<span itemprop="http://schema.org/postalCode">(.*?)</span>', output, "")
		city = self.searchOneValue(r'<span itemprop="http://schema.org/addressCountry">(.*?)</span>', output, "")
		price = ["n.v.", ""]
		for rawentry in output.split('<div class="price-type col-6 d-flex flex-column justify-content-start headline">')[1:]:
			sprittype = self.searchOneValue(r'<div class="price-type-name">(.*?)</div>', rawentry, "")
			if sprittype == spritdict.get(self.sprit["B"]):
				price[0] = self.searchOneValue(r'<span id="current-price-.d*">(.*?)</span>', rawentry, price[0])
				price[1] = self.searchOneValue(r'<sup id="suffix-price-.d*">(.*?)</sup>', rawentry, price[1])
				break
		rawentry = self.searchOneValue(r'<div class="price-footer row col-12 text text-color-ice-blue d-flex flex-column">(.*?)</div>', output, "", flag_S=True)
		pcngtype, pcngdate, pcngdur = ("geändert", "unbekannt", "unbekannt")
		changes = rawentry.replace("<span>", "").replace("</span>", "").strip().split("\n")
		part = changes[0].split(": ") if changes else []  # changes[0] = Letzte MTS-K Preisänderung, changes[1] = Letzte Aktualisierung
		pcngdate, pcngdur = part[1].split(" ") if len(part) > 1 else ("unbekannt", "unbekannt")
		pricealert = self.createPricealert(price, self.sprit["B"])
		self.framefavs.append(tuple((ident, price[0], price[1], pcngtype, pcngdate, pcngdur, name, street, f"{zipcode} {city}", "", "♥", pricealert)))
		if len(self.framefavs) == len(self.favlist):  # all favorites downloaded?
			self.sortRefreshFavorites()

	def sortRefreshFavorites(self):
		if self.sort["B"] == "p":
			sortedfavs = sorted(self.framefavs, key=lambda tup: tup[1])
		elif self.sort["B"] == "abc":
			sortedfavs = sorted(self.framefavs, key=lambda tup: tup[6].casefold())
		else:
			sortedfavs = self.framefavs
		self["headline_B"].setText(f"Favoriten | {len(sortedfavs)} Tankstellen")
		self["frame_B"].updateList(sortedfavs)
		self.ready = True
		self.refreshInfo()

	def createPricealert(self, price, sprit):
			alerttype = None
			if price[0].replace('.', '', 1).isdigit() and price[1]:
				centprice = float(price[0]) + int(price[1]) * .0001 if price[1].isdigit() else float(price[0])
			else:
				centprice = 0.0
			if centprice:
				for alert in self.alertlist:
					if alert[1] != "aus" and sprit == alert[2] and centprice < float(alert[1]):
						alerttype = alert[0]
						break
			picfile = join(f"{self.PLUGINPATH}pic/", f"alert-{alerttype}_{self.RESOLUTION}.png") if alerttype else join("")
			return LoadPixmap(cached=True, path=picfile) if exists(picfile) else None

	def toggleFrame_B(self):
		self.frameBmode = "F" if self.frameBmode == "Z" else "Z"
		self.refreshButtons()
		self.refreshFrame("B")
		self.refreshInfo()

	def searchOneValue(self, regex, text, fallback, flag_S=False):
		text = search(regex, text, flags=S) if flag_S else search(regex, text)
		return text.group(1) if text else fallback

	def ok(self):
		if self.isInfo:
			self.isInfo = False
			self.showInfo.hide()
		else:
			current = self[f"frame_{self.currframe}"].getCurrent()
			if current:
				callInThread(self.download, f"{self.BASEURL}/tankstelle_details/{current[0]}?spritsorte={self.sprit['B']}", self.makeTankenInfo)

	def changeFavorites(self):
		current = self[f"frame_{self.currframe}"].getCurrent()
		if current:
			self.refreshButtons()
			self["frame_B"].updateList([])
			callInThread(self.download, f"{self.BASEURL}/tankstelle_details/{current[0]}?spritsorte={self.sprit['B']}", boundFunction(self.makeTankenView, "B"))
			ident = current[0]
			if ident in self.favlist:
				text = "Wollen Sie diese Tankstelle wirklich aus den Favoriten entfernen?"
				self.session.openWithCallback(boundFunction(self.writeConfig, ident, True), MessageBox, text, MessageBox.TYPE_YESNO, timeout=5, default=False)
			else:
				self.writeConfig(ident, False, True)

	def writeConfig(self, ident, remove, answer):
		self.favlist.remove(ident) if remove else self.favlist.append(ident)
		if answer is True:
			config.plugins.clevertanken.favorites.value = ",".join(self.favlist)
			config.plugins.clevertanken.favorites.save()
			config.plugins.clevertanken.save()
			self.refreshFrame("B")

	def selectSort(self, frame):
		if self.ready:
			outlist = list({v: k for k, v in self.SORTDICT.items()}.items())  # flip keys and values in dict
			if frame == "B" and self.frameBmode == "F" and ("km", "km") in outlist:
				outlist.remove(("km", "km"))
			elif ("keine", "keine") in outlist:
				outlist.remove(("keine", "keine"))
			keylist = [x[1] for x in outlist]
			index = keylist.index(self.sort[frame]) if self.sort[frame] in keylist else 0
			self.session.openWithCallback(boundFunction(self.selectSort_CB, frame), ChoiceBox, list=outlist, keys=[], selection=index, windowTitle="Wähle die gewünschte Sortierung:")

	def selectSort_CB(self, frame, choice):
		if choice:
			self.sort[frame] = choice[1]
			self[f"headline_{frame}"].setText(self.twaittext)
			self[f"frame_{frame}"].updateList([])
			self.ready = False
			self.refreshButtons()
			if frame == "B" and self.frameBmode == "F":
				self.sortRefreshFavorites()
			else:
				callInThread(self.download, self.createLink(frame), boundFunction(self.makeTankenView, frame))

	def selectRadius(self, frame):
		if self.ready and not (frame == "B" and self.frameBmode == "F"):
			outlist = list({v: k for k, v in self.RADIUSDICT.items()}.items())  # flip keys and values in dict
			keylist = [x[1] for x in outlist]
			index = keylist.index(self.radius[frame]) if self.radius[frame] in keylist else 0
			self.session.openWithCallback(boundFunction(self.selectRadius_CB, frame), ChoiceBox, list=outlist, keys=[], selection=index, windowTitle="Wähle den gewünschten Suchradius:")

	def selectRadius_CB(self, frame, choice):
		if choice:
			self.radius[frame] = choice[1]
			self[f"headline_{frame}"].setText(self.twaittext)
			self[f"frame_{frame}"].updateList([])
			self.ready = False
			self.refreshButtons()
			callInThread(self.download, self.createLink(frame), boundFunction(self.makeTankenView, frame))

	def selectSprit(self, frame):
		if self.ready:
			outlist = list({v: k for k, v in self.SPRITDICT.items()}.items())  # flip keys and values in dict
			keylist = [x[1] for x in outlist]
			index = keylist.index(self.sprit[frame]) if self.sprit[frame] in keylist else 0
			self.session.openWithCallback(boundFunction(self.selectSprit_CB, frame), ChoiceBox, list=outlist, keys=[], selection=index, windowTitle="Wähle die gewünschte Kraftstoffart:")

	def selectSprit_CB(self, frame, choice):
		if choice:
			self.sprit[frame] = choice[1]
			self[f"frame_{frame}"].updateList([])
			self.ready = False
			if frame == "B" and self.frameBmode == "F":
				self[f"headline_{frame}"].setText(self.fwaittext)
				self.framefavs = []
				for ident in self.favlist:
					callInThread(self.download, f"{self.BASEURL}/tankstelle_details/{ident}?spritsorte={self.sprit[frame]}", boundFunction(self.makeFavoriteView))
			else:
				self.refreshButtons()
				self[f"headline_{frame}"].setText(self.twaittext)
				callInThread(self.download, self.createLink(frame), boundFunction(self.makeTankenView, frame))

	def refreshButtons(self):
		if self.frameBmode == "F" and self.sort["B"] == "km":
			self.sort["B"] = "keine"
		if self.frameBmode == "Z" and self.sort["B"] == "keine":
			self.sort["B"] = "km"
		self["ukey_red"].setText(f"kurz | Sortierung: {self.SORTDICT.get(self.sort['A'], '€')}")
		self["dkey_red"].setText(f"lang | Sprit: {self.SPRITDICT.get(self.sprit['A'], 'SuperPlus')}")
		self["ukey_green"].setText(f"kurz | Radius: {self.RADIUSDICT.get(self.radius['A'], '5 km')}")
		self["ukey_yellow"].setText(f"kurz | Sortierung: {self.SORTDICT.get(self.sort['B'], '€')}")
		self["dkey_yellow"].setText(f"lang | Sprit: {self.SPRITDICT.get(self.sprit['B'], 'SuperPlus')}")
		self["ukey_blue"].setText(f"kurz | Radius: {self.RADIUSDICT.get(self.radius['B'], 'SuperPlus')}" if self.frameBmode == "Z" else "")
		self["dkey_blue"].setText("lang | wechsle zu Favoriten" if self.frameBmode == "Z" else "lang | wechsle zu Zweitort")

	def refreshInfo(self):
		if self.ready:
			current = self[f"frame_{self.currframe}"].getCurrent()
			if current:
				ident = current[0]
				if ident:
					if self.isInfo:
						callInThread(self.download, f"{self.BASEURL}/tankstelle_details/{ident}?spritsorte={self.sprit['B']}", self.makeTankenInfo)
					self["dkey_green"].setText("lang | aus Favoriten entfernen" if ident in self.favlist else "lang | zu Favoriten hinzufügen")
				else:
					if self.isInfo:
						self.showInfo['info'].setText("keine Favoriten vorhanden")
					self["dkey_green"].setText("")

	def down(self):
		self[f"frame_{self.currframe}"].down()
		self.refreshInfo()

	def up(self):
		self[f"frame_{self.currframe}"].up()
		self.refreshInfo()

	def pageUp(self):
		self[f"frame_{self.currframe}"].pageUp()
		self.refreshInfo()

	def pageDown(self):
		self[f"frame_{self.currframe}"].pageDown()

	def toggleFrame(self):
		if self.ready:
			if self.currframe == "A":
				self.currframe = "B"
				self["frameAactive"].setText("")
				self["frameBactive"].setText(" ")
			elif self.currframe == "B":
				self.currframe = "A"
				self["frameAactive"].setText(" ")
				self["frameBactive"].setText("")
			self.setEvadePosition()
			self.refreshButtons()
			self.refreshInfo()

	def setEvadePosition(self):
		ypos = int(100 * (1.5 if self.RESOLUTION == "fHD" else 1.0))
		if self.currframe == "A":
			xpos = int(660 * (1.5 if self.RESOLUTION == "fHD" else 1.0))
		else:
			xpos = int(280 * (1.5 if self.RESOLUTION == "fHD" else 1.0))
		CTinfo.moveInfo(self.showInfo, xpos, ypos)

	def config(self):
		self.isInfo = False
		self.showInfo.hide()
		self.session.openWithCallback(self.configCB, CTconfig)

	def configCB(self, saved=False):
		if saved:
			self.getConfigs()
			self.refreshButtons()
			self.refreshFrame("AB")

	def exit(self):
		if self.isInfo:
			self.isInfo = False
			self.showInfo.hide()
		else:
			self.session.deleteDialog(self.showInfo)
			self.close()


class CTconfig(Setup, CTglobs):
	def __init__(self, session):
		Setup.__init__(self, session, "clevertankenconfig", plugin="Extensions/CleverTanken", PluginLanguageDomain="CleverTanken")
		self["key_yellow"] = StaticText("Hauptort suchen")
		self["key_blue"] = StaticText("Zweitort suchen")
		self.cityAzipname = config.plugins.clevertanken.cityAzipname.value
		self.cityAgeodata = config.plugins.clevertanken.cityAgeodata.value
		self.cityBzipname = config.plugins.clevertanken.cityBzipname.value
		self.cityBgeodata = config.plugins.clevertanken.cityBgeodata.value
		self["entryActions"] = HelpableActionMap(self, ["ColorActions"],
														{
														"yellow": (self.cityAsearch, "Hauptort suchen"),
														"blue": (self.cityBsearch, "Zweitort suchen")
														}, prio=0, description="clevertanken Eingabeaktionen")

	def cityAsearch(self):
		subnames = config.plugins.clevertanken.cityAzipname.value.split(" ")
		cityname = " ".join(subnames[1:] if (len(subnames) > 1 and subnames[0].isdigit()) else subnames)
		self.session.openWithCallback(boundFunction(self.VirtualKeyBoardCB, "A"), VirtualKeyBoard, title="Geben Sie den gewünschen Hauptort ein.", text=cityname)

	def cityBsearch(self):
		subnames = config.plugins.clevertanken.cityBzipname.value.split(" ")
		cityname = " ".join(subnames[1:] if (len(subnames) > 1 and subnames[0].isdigit()) else subnames)
		self.session.openWithCallback(boundFunction(self.VirtualKeyBoardCB, "B"), VirtualKeyBoard, title="Geben Sie den gewünschen Zweitort ein.", text=cityname)

	def VirtualKeyBoardCB(self, frame, answer):
		if answer is not None:
			cityname = answer.replace(" ", "+").replace("/", "%2F")
			limit = config.plugins.clevertanken.maxcities.value
			url = f"https://gcx01.123map.de/pcplace.json?thm=inforoad-ct1&zipcodecenter=1&limit={limit}&qa={cityname}"
			self.download(url, boundFunction(self.citysearchCB, frame))

	def citysearchCB(self, frame, jsonstr):
		citydict = dict()
		try:
			citydict = loads(jsonstr)
		except Exception as error:
			print("[%s] ERROR in module 'citysearchCB': %s" % (self.MODULE_NAME, str(error)))
		citylist = []
		for city in citydict:
			zipname, lat, lon = city.get("value", ""), city.get("lat", ""), city.get("lon", "")
			if zipname and lat and lon:
				citylist.append((zipname, lat, lon))
		text = "Wähle den gewünschten Ort / Ortsteil."
		title = f"Städtesuche ({len(citylist)} Städte)"
		self.session.openWithCallback(boundFunction(self.citysearchReturn, frame), ChoiceBox, text=text, title=title, list=citylist, keys=[])

	def citysearchReturn(self, frame, answer):
		if answer is not None:
			if frame == "A":
				self.cityAzipname = config.plugins.clevertanken.cityAzipname.value = answer[0].strip()
				config.plugins.clevertanken.cityAgeodata.value = f"{answer[1]},{answer[2]}"
				config.plugins.clevertanken.cityAgeodata.save()
			elif frame == "B":
				self.cityBzipname = config.plugins.clevertanken.cityBzipname.value = answer[0].strip()
				config.plugins.clevertanken.cityBgeodata.value = f"{answer[1]},{answer[2]}"
				config.plugins.clevertanken.cityBgeodata.save()

	def keyCancel(self):  # This overrides the same class in ConfigList.py as part of Setup.py
		config.plugins.clevertanken.cityAzipname.value = self.cityAzipname
		config.plugins.clevertanken.cityAgeodata.value = self.cityAgeodata
		config.plugins.clevertanken.cityBzipname.value = self.cityBzipname
		config.plugins.clevertanken.cityBgeodata.value = self.cityBgeodata
		self.close()

	def keySave(self):  # This overrides the same class in ConfigList.py as part of Setup.py
		newcityAzipname = config.plugins.clevertanken.cityAzipname.value
		newcityBzipname = config.plugins.clevertanken.cityBzipname.value
		if newcityAzipname != self.cityAzipname:
			subnames = newcityAzipname.split(" ")
			cityname = " ".join(subnames[1:] if (len(subnames) > 1 and subnames[0].isdigit()) else subnames)
			self.VirtualKeyBoardCB("A", cityname)
		elif newcityBzipname != self.cityBzipname:
			subnames = newcityBzipname.split(" ")
			cityname = " ".join(subnames[1:] if (len(subnames) > 1 and subnames[0].isdigit()) else subnames)
			self.VirtualKeyBoardCB("B", cityname)
		else:
			self.saveAll()
			self.close(True)


def main(session, **kwargs):
	session.open(CTmain)


def sessionstart(reason, session=None, **kwargs):
	if reason == 0:
		radiuslist = list(CTglobs.RADIUSDICT.items())
		spritlist = list(CTglobs.SPRITDICT.items())
		fulllist = list(CTglobs.SORTDICT.items())
		sortlist = fulllist[:]
		sortlist.remove(("keine", "keine")) if ("keine", "keine") in sortlist else None
		fsortlist = fulllist[:]
		fsortlist.remove(("km", "km")) if ("km", "km") in fsortlist else None
		maxlist = [(0, "alle Einträge"), (7, "max. 7 Einträge"), (14, "max. 14 Einträge"), (21, "max. 21 Einträge"), (29, "max. 29 Einträge")]
		pricelist = ["aus"] + ["{:.2f}".format(x / 100) for x in range(100, 300)]
		config.plugins.clevertanken = ConfigSubsection()
		config.plugins.clevertanken.maxcities = ConfigSelection(default=10, choices=[(10, "max. 10 Städte"), (20, "max. 20 Städte"), (30, "max. 30 Städte"), (40, "max. 40 Städte"), (50, "max. 50 Städte")])
		config.plugins.clevertanken.cityAzipname = ConfigText(default="10117 Berlin", fixed_size=False)
		config.plugins.clevertanken.cityAgeodata = ConfigText(default="52.5170365161785,13.3888598914667", fixed_size=False)
		config.plugins.clevertanken.radiusA = ConfigSelection(default="5", choices=radiuslist)
		config.plugins.clevertanken.spritA = ConfigSelection(default="6", choices=spritlist)
		config.plugins.clevertanken.sortA = ConfigSelection(default="p", choices=sortlist)
		config.plugins.clevertanken.cityBzipname = ConfigText(default="80331 München", fixed_size=False)
		config.plugins.clevertanken.cityBgeodata = ConfigText(default="48.1371079183914,11.5753822176437", fixed_size=False)
		config.plugins.clevertanken.radiusB = ConfigSelection(default="5", choices=radiuslist)
		config.plugins.clevertanken.spritB = ConfigSelection(default="6", choices=spritlist)
		config.plugins.clevertanken.sortB = ConfigSelection(default="p", choices=sortlist)
		config.plugins.clevertanken.spritF = ConfigSelection(default="6", choices=spritlist)
		config.plugins.clevertanken.sortF = ConfigSelection(default="p", choices=fsortlist)
		config.plugins.clevertanken.maxentries = ConfigSelection(default=0, choices=maxlist)
		config.plugins.clevertanken.startframeB = ConfigSelection(default="Z", choices=[("Z", "Zweitort"), ("F", "Favoriten")])
		config.plugins.clevertanken.favorites = ConfigText(default="", fixed_size=False)
		config.plugins.clevertanken.priceRed = ConfigSelection(default="aus", choices=pricelist)
		config.plugins.clevertanken.spritRed = ConfigSelection(default="6", choices=spritlist)
		config.plugins.clevertanken.priceYellow = ConfigSelection(default="aus", choices=pricelist)
		config.plugins.clevertanken.spritYellow = ConfigSelection(default="6", choices=spritlist)
		config.plugins.clevertanken.priceGreen = ConfigSelection(default="aus", choices=pricelist)
		config.plugins.clevertanken.spritGreen = ConfigSelection(default="6", choices=spritlist)


def Plugins(**kwargs):
	return [PluginDescriptor(name="CleverTanken.de", description="Tankstellen-Preisvergleich", where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main),
		 PluginDescriptor(name="CleverTanken.de", description="Tankstellen-Preisvergleich mit eigenen Preisalarmen", where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, needsRestart=True, fnc=sessionstart)]

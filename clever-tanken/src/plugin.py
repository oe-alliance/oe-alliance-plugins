# PYTHON IMPORTS
from json import loads
from re import findall, search, S
from random import choice
from requests import get, exceptions
from twisted.internet.reactor import callInThread
from Tools.BoundFunction import boundFunction

# ENIGMA IMPORTS
from enigma import getDesktop
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config, configfile, ConfigSelection, ConfigSubsection, ConfigText
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Setup import Setup
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

# GLOBALS
MODULE_NAME = __name__.split(".")[-2]
BASEURL = "http://www.clever-tanken.de"


def download(url, callback):
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
		response = get(url.encode(), headers=headers, timeout=(3.05, 3))
		response.raise_for_status()
	except exceptions.RequestException as error:
		print("[%s] ERROR in module 'download': %s" % (MODULE_NAME, str(error)))
	else:
		callback(response.content.decode())


def createDroplists(output):
	global SORTDICT
	global SPRITDICT
	global RADIUSDICT
	sortliste = [("p", "€"), ("km", "km"), ("abc", "A-Z")]
	SORTDICT = dict(sortliste)
	startpos = output.find('<span>Spritsorte</span>')
	endpos = output.find('<div class="dropdown radius">')
	spritliste = findall(r'<a class="dropdown-item" value="(.*?)" href="#">(.*?)</a>', output[startpos:endpos])
	SPRITDICT = dict(spritliste)
	startpos = output.find('<span>Radius</span>')
	endpos = output.find('<div class="favoriten">')
	radiusliste = findall(r'<a class="dropdown-item" value="(.*?)" href="#">(.*?)</a>', output[startpos:endpos])
	RADIUSDICT = dict(radiusliste)
	config.plugins.clevertanken = ConfigSubsection()
	config.plugins.clevertanken.cityAzipname = ConfigText(default="10117 Berlin", fixed_size=False)
	config.plugins.clevertanken.cityAgeodata = ConfigText(default=(52.5170365161785, 13.3888598914667), fixed_size=False)
	config.plugins.clevertanken.radiusA = ConfigSelection(default="5", choices=radiusliste)
	config.plugins.clevertanken.spritA = ConfigSelection(default="6", choices=spritliste)
	config.plugins.clevertanken.sortA = ConfigSelection(default="p", choices=sortliste)
	config.plugins.clevertanken.cityBzipname = ConfigText(default="80331 München", fixed_size=False)
	config.plugins.clevertanken.cityBgeodata = ConfigText(default=(48.1371079183914, 11.5753822176437), fixed_size=False)
	config.plugins.clevertanken.radiusB = ConfigSelection(default="5", choices=radiusliste)
	config.plugins.clevertanken.spritB = ConfigSelection(default="6", choices=spritliste)
	config.plugins.clevertanken.sortB = ConfigSelection(default="p", choices=sortliste)
	config.plugins.clevertanken.maxentries = ConfigSelection(default=0, choices=[(0, "alle Einträge"), (7, "max. 7 Einträge"), (14, "max. 14 Einträge"), (21, "max. 21 Einträge"), (29, "max. 29 Einträge")])
	config.plugins.clevertanken.startframeB = ConfigSelection(default="Z", choices=[("Z", "Zweitort"), ("F", "Favoriten")])
	config.plugins.clevertanken.favorites = ConfigText(default="", fixed_size=False)


download(BASEURL, createDroplists)   # lade zuerst die obligatorische spritliste & radiusliste für Config


class clevertankenMain(Screen):
	res = "fHD" if getDesktop(0).size().width() > 1300 else "HD"
	skin = """
	<screen name="clevertankenMain" position="center,center" size="1863,1032" resolution="1920,1080" title="" flags="wfNoBorder">
		<eLabel position="0,0" size="1863,1032" backgroundColor="#10152e4e" zPosition="-2" />
		<ePixmap position="9,6" size="255,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/clever-tanken/pic/ct_logo.png" alphatest="blend" scale="1" zPosition="1" />
		<ePixmap position="1104,22" size="30,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/clever-tanken/pic/key_ok.png" alphatest="blend" scale="1" zPosition="1" />
		<ePixmap position="1428,22" size="30,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/clever-tanken/pic/key_menu.png" alphatest="blend" scale="1" zPosition="1" />
		<widget source="key_ok" render="Label" position="1149,15" size="249,45" font="Regular;30" foregroundColor="#10233d67" backgroundColor="#10afb9cf" halign="left" valign="center" />
		<widget source="key_menu" render="Label" position="1473,15" size="250,45" font="Regular;30" foregroundColor="#10233d67" backgroundColor="#10afb9cf" halign="left" valign="center" />
		<eLabel position="0,75" size="918,45" backgroundColor="#103B5AA2" zPosition="-1" />
		<widget source="headline_A" render="Label" position="12,75" size="900,45" font="Regular;30" halign="left" valign="center" foregroundColor="white" backgroundColor="#103B5AA2" />
		<widget source="frameAactive" render="Label" conditional="frameAactive" position="0,120" size="921,810" backgroundColor="#00c8ff12" zPosition="-1">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="frame_A" render="Listbox" position="6,126" size="909,798" backgroundColor="#10f5f5f5" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/clever-tanken/pic/selector_%s.png" enableWrapAround="1" scrollbarMode="showNever" scrollbarBorderWidth="2" scrollbarForegroundColor="f5f5f5" scrollbarBorderColor="#7e7e7e">
			<convert type="TemplatedMultiContent">
				{"template": [  # index 0 is the identnumber (here unused)
				MultiContentEntryText(pos=(0,0), size=(906,114), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e"),  # background filler
				MultiContentEntryText(pos=(0,0), size=(99,114), font=0, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=1),  # price main
				MultiContentEntryText(pos=(102,9), size=(30,60), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=2),  # price suffix
				MultiContentEntryText(pos=(138,3), size=(120,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=3),  # changetype
				MultiContentEntryText(pos=(138,39), size=(120,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=4),  # changedate
				MultiContentEntryText(pos=(138,75), size=(120,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=5),  # changedurance
				MultiContentEntryText(pos=(315,0), size=(591,39), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=6),  # name
				MultiContentEntryText(pos=(315,39), size=(540,36), font=2, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=7),  # street
				MultiContentEntryText(pos=(315,75), size=(540,36), font=2, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=8),  # zipcode
				MultiContentEntryText(pos=(774,33), size=(105,45), font=1,color="#10152e4e",  backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=9),  # distance
				MultiContentEntryText(pos=(273,36), size=(30,45), font=1, color="#103B5AA2", backcolor="#10f5f5f5", color_sel="yellow", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=10)  # favorite
				],
				"fonts": [gFont("Regular",42), gFont("Regular",30), gFont("Regular",27), gFont("Regular",24)],
				"itemHeight":114
				}
			</convert>
		</widget>
		<eLabel position="939,75" size="918,45" backgroundColor="#103B5AA2" zPosition="-1" />
		<widget source="headline_B" render="Label" position="948,75" size="900,45" font="Regular;30" halign="left" valign="center" foregroundColor="white" backgroundColor="#103B5AA2" />
		<widget source="frameBactive" render="Label" conditional="frameBactive" position="939,120" size="921,810" backgroundColor="#00c8ff12" zPosition="-1">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="frame_B" render="Listbox" position="945,126" size="909,798" backgroundColor="#10f5f5f5" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/clever-tanken/pic/selector_%s.png" enableWrapAround="1" scrollbarMode="showNever" scrollbarBorderWidth="2" scrollbarForegroundColor="f5f5f5" scrollbarBorderColor="#7e7e7e">
			<convert type="TemplatedMultiContent">
				{"template": [  # index 0 is the identnumber (here unused)
				MultiContentEntryText(pos=(0,0), size=(906,114), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e"),  # background filler
				MultiContentEntryText(pos=(0,0), size=(99,114), font=0, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=1),  # price main
				MultiContentEntryText(pos=(102,9), size=(30,60), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=2),  # price suffix
				MultiContentEntryText(pos=(138,3), size=(120,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=3),  # changetype
				MultiContentEntryText(pos=(138,39), size=(120,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=4),  # changedate
				MultiContentEntryText(pos=(138,75), size=(120,33), font=3, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=5),  # changedurance
				MultiContentEntryText(pos=(315,0), size=(591,39), font=1, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=6),  # name
				MultiContentEntryText(pos=(315,39), size=(540,36), font=2, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=7),  # street
				MultiContentEntryText(pos=(315,75), size=(540,36), font=2, color="#10152e4e", backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=8),  # zipcode
				MultiContentEntryText(pos=(774,33), size=(105,45), font=1,color="#10152e4e",  backcolor="#10f5f5f5", color_sel="#10f5f5f5", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=9),  # distance
				MultiContentEntryText(pos=(273,36), size=(30,45), font=1, color="#103B5AA2", backcolor="#10f5f5f5", color_sel="yellow", backcolor_sel="#10152e4e", flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=10)  # favorite
				],
				"fonts": [gFont("Regular",42), gFont("Regular",30), gFont("Regular",27), gFont("Regular",24)],
				"itemHeight":114
				}
			</convert>
		</widget>
		<eLabel name="red" position="15,951" size="9,68" backgroundColor="red" zPosition="1" />
		<eLabel name="green" position="444,951" size="9,68" backgroundColor="green" zPosition="1" />
		<eLabel name="yellow" position="915,951" size="9,68" backgroundColor="yellow" zPosition="1" />
		<eLabel name="blue" position="1374,951" size="9,68" backgroundColor="blue" zPosition="1" />
		<widget source="ukey_red" render="Label" position="36,942" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="dkey_red" render="Label" position="36,987" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="ukey_green" render="Label" position="465,942" size="471,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="dkey_green" render="Label" position="465,987" size="471,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="ukey_yellow" render="Label" position="936,942" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="dkey_yellow" render="Label" position="936,987" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="ukey_blue" render="Label" position="1395,942" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<widget source="dkey_blue" render="Label" position="1395,987" size="465,45" font="Regular; 30" halign="left" foregroundColor="grey" backgroundColor="#10152e4e" transparent="1" />
		<eLabel name="line" position="6,240" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,354" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,468" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,582" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,696" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,810" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="6,924" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,240" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,354" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,468" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,582" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,696" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,810" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
		<eLabel name="line" position="945,924" size="909, 2" backgroundColor="#103B5AA2" zPosition="10" />
	</screen>""" % (res, res)

	def __init__(self, session):
		Screen.__init__(self, session)
		favorites = config.plugins.clevertanken.favorites.value
		self.favlist = favorites.split(",") if favorites else []
		self.ready = False
		self.showInfo = self.session.instantiateDialog(tankenInfo)
		self.isInfo = False
		self.currframe = "A"
		self.identdict = dict()
		self.identdict["A"] = list()
		self.identdict["B"] = list()
		self.framefavs = []
		self.frameBmode = config.plugins.clevertanken.startframeB.value
		self.getConfigs()
		self["frame_A"] = List([])
		self["frame_B"] = List([])
		self["frameAactive"] = StaticText(" ")
		self["frameBactive"] = StaticText()
		self["headline_A"] = StaticText()
		self["headline_B"] = StaticText()
		self["ukey_red"] = StaticText(f"kurz | Sortierung: {SORTDICT.get(self.sortA, "€")}")
		self["dkey_red"] = StaticText(f"lang | Sprit: {SPRITDICT.get(self.spritA, "SuperPlus")}")
		self["ukey_green"] = StaticText(f"kurz | Radius: {RADIUSDICT.get(self.radiusA)}")
		self["dkey_green"] = StaticText()
		self["ukey_yellow"] = StaticText(f"kurz | Sortierung: {SORTDICT.get(self.sortB, "€")}")
		self["dkey_yellow"] = StaticText(f"lang | Sprit: {SPRITDICT.get(self.spritB, "SuperPlus")}")
		self["ukey_blue"] = StaticText(f"kurz | Radius: {RADIUSDICT.get(self.radiusB)}")
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
		 											"nextBouquet": self.zap,
		 											"prevBouquet": self.zap,
		 											"red": self.turnSortA,
													"redlong": self.turnSpritA,
		 											"green": self.turnRadiusA,
													"greenlong": self.changeFavorites,
		 											"yellow": self.turnSortB,
		 											"yellowlong": self.turnSpritB,
		 											"blue": self.turnRadiusB,
		 											"bluelong": self.toggleFrameB,
		 											"menu": self.config
		 											}, -1)
		self.onLayoutFinish.append(self.refreshFrames)

	def refreshFrames(self):
		self.refreshFrameA()
		self.refreshFrameB()

	def getConfigs(self):
		self.sortA = config.plugins.clevertanken.sortA.value
		self.sortB = config.plugins.clevertanken.sortB.value
		self.spritA = config.plugins.clevertanken.spritA.value
		self.spritB = config.plugins.clevertanken.spritB.value
		self.radiusA = config.plugins.clevertanken.radiusA.value
		self.radiusB = config.plugins.clevertanken.radiusB.value

	def refreshFrameA(self):
		callInThread(download, self.createLink("A", self.sortA, self.spritA, self.radiusA), boundFunction(self.makeTankenView, "A"))

	def refreshFrameB(self):
		if self.frameBmode == "Z":
			callInThread(download, self.createLink("B", self.sortB, self.spritB, self.radiusB), boundFunction(self.makeTankenView, "B"))
		else:
			if self.favlist:
				self.ready = False
				self.framefavs = []
				for ident in self.favlist:
					callInThread(download, f"{BASEURL}/tankstelle_details/{ident}?spritsorte={self.spritB}", boundFunction(self.makeFavoriteView))
			else:
				self["frame_B"].updateList([tuple(("", "", "", "", "", "", "keine Favoriten vorhanden", "", "", "", ""))])
			self["headline_B"].setText(f"Favoriten | {len(self.favlist)} Tankstellen")

	def createLink(self, frame, sort, spritsorte, radius):
		if frame == "A":
			zipname = config.plugins.clevertanken.cityAzipname.value.replace(" ", "+").replace("/", "%2F")
			geodata = eval(str(config.plugins.clevertanken.cityAgeodata.value))
		else:
			zipname = config.plugins.clevertanken.cityBzipname.value.replace(" ", "+").replace("/", "%2F")
			geodata = eval(str(config.plugins.clevertanken.cityBgeodata.value))
		return f'{BASEURL}/tankstelle_liste?lat={geodata[0]}&lon={geodata[1]}&ort={zipname}&spritsorte={spritsorte}&r={radius}&sort={sort}'

	def makeTankenView(self, frame, output):
		self.ready = True
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
			prices = self.searchOneValue(r'<div class="price-text price text-color-ct-blue">\s+(.*?)\s+</div>', eintrag, " ", flag_S=True)
			if prices and prices[0] != " ":
				price = prices.replace("</sup>", "").split("<sup>") if prices and prices[0] != " " else ("nicht\ngeöffnet", "")
				change = findall(r'<span class="price-changed">(.*?)\s*</span>', eintrag, S)
				cnglen = len(change) if change else 0
				pcngtype = change[0].replace("<br>", "") if cnglen > 0 else "unbekannt"
				pcngdate = change[1].replace("<br>", "") if cnglen > 1 else "unbekannt"
				pcngdur = change[2].replace("<br>", "") if cnglen > 2 else "unbekannt"
			else:
				price, pcngtype, pcngdate, pcngdur = (("zu", ""), "Tankstelle", "momentan", "geschlossen")
			name = self.searchOneValue(r'<span class="fuel-station-location-name">(.*?)</span>', eintrag, "kein Name gefunden")
			street = self.searchOneValue(r'<div class="fuel-station-location-street">(.*?)</div>', eintrag, "kein Straßennamen gefunden")
			zipcode = self.searchOneValue(r'<div class="fuel-station-location-city">(.*?)</div>', eintrag, "kein Ort gefunden").strip()
			distance = self.searchOneValue(r'<div class="fuel-station-location-distance d-flex justify-content-end">\s+<span>(.*?)</span>\s+</div>', eintrag, "keine Distanz gefunden", flag_S=True)
			favorite = "♥" if ident in self.favlist else ""
			framelist.append(tuple((ident, price[0], price[1], pcngtype, pcngdate, pcngdur, name, street, zipcode, distance, favorite)))
		self.identdict[frame] = identlist
		self[f"frame_{frame}"].updateList(framelist)
		if frame == "A":
			zipname = config.plugins.clevertanken.cityAzipname.value
			self["headline_A"].setText(f"Hauptort: {zipname} | {len(identlist)} Tankstellen")
			self["ukey_red"].setText(f"kurz | Sortierung: {SORTDICT.get(self.sortA, "€")}")
			self["dkey_red"].setText(f"lang | Sprit: {SPRITDICT.get(self.spritA, "SuperPlus")}")
			self["ukey_green"].setText(f"kurz | Radius: {RADIUSDICT.get(self.radiusA, "5 km")}")
		elif frame == "B":
			zipname = config.plugins.clevertanken.cityBzipname.value
			self["headline_B"].setText(f"Zweitort: {zipname} | {len(identlist)} Tankstellen")
			self["ukey_yellow"].setText(f"kurz | Sortierung: {SORTDICT.get(self.sortB, "€")}")
			self["dkey_yellow"].setText(f"lang | Sprit: {SPRITDICT.get(self.spritB, "SuperPlus")}")
			self["ukey_blue"].setText(f"kurz | Radius: {RADIUSDICT.get(self.radiusB, "SuperPlus")}")
		self.refreshInfo()

	def makeTankenInfo(self, output):
		self.ready = True
		name = self.searchOneValue(r'itemprop="name">(.*?)</span>', output, "")
		street = self.searchOneValue(r'<span itemprop="streetAddress">(.*?)</span>', output, "")
		zipcode = self.searchOneValue(r'<span itemprop="http://schema.org/postalCode">(.*?)</span>', output, "")
		city = self.searchOneValue(r'<span itemprop="http://schema.org/addressCountry">(.*?)</span>', output, "")
		openlist = []
		for rawentry in findall(r'<div class="d-flex justify-content-between weak-body">(.*?)</div>', output, S):
			opendata = rawentry.replace("<span>", "").replace("</span>", "").strip().split("\n")
			opendata[1] = opendata[1].strip() if len(opendata) > 1 else ""
			openlist.append(" ".join(opendata))
		openings = "\n".join(openlist)
		rawentry = self.searchOneValue(r'<div class="price-footer row col-12 text text-color-ice-blue d-flex flex-column">(.*?)</div>', output, "", flag_S=True)
		lastlist = []
		for last in rawentry.replace("<span>", "").replace("</span>", "").strip().split("\n"):
			part = last.split(": ")
			lastlist.append(f"{part[0]}\n{part[1]}" if len(part) > 0 else "")
		lastlist[1] = lastlist[1].strip() if len(lastlist) > 1 else ""
		lastdates = "\n".join(lastlist)
		prices = ""
		for rawentry in output.split('<div class="price-type col-6 d-flex flex-column justify-content-start headline">')[1:]:
			sprittype = self.searchOneValue(r'<div class="price-type-name">(.*?)</div>', rawentry, "")
			price = self.searchOneValue(r'<span id="current-price-.d*">(.*?)</span>', rawentry, "")
			price += self.searchOneValue(r'<sup id="suffix-price-.d*">(.*?)</sup>', rawentry, "")
			pricetype = self.searchOneValue(r'<div class="price-type-mtsk">(.*?)</div>', rawentry, "").strip()
			prices += f"{sprittype}: {price}{f" ({pricetype})" if pricetype else ""}\n"
		infos = f"{name}\n{street}\n{zipcode} {city}\n\nÖffnungszeiten:\n{openings}\n\nKraftstoffpreise:\n{prices}\n{lastdates}"
		self.showInfo['info'].setText(infos)
		self.showInfo.show()
		self.isInfo = True

	def makeFavoriteView(self, output):
		ident = self.searchOneValue(r"var object_id = '(.*?)'", output, "")
		name = self.searchOneValue(r'itemprop="name">(.*?)</span>', output, "")
		street = self.searchOneValue(r'<span itemprop="streetAddress">(.*?)</span>', output, "")
		zipcode = self.searchOneValue(r'<span itemprop="http://schema.org/postalCode">(.*?)</span>', output, "")
		city = self.searchOneValue(r'<span itemprop="http://schema.org/addressCountry">(.*?)</span>', output, "")
		price = []
		for rawentry in output.split('<div class="price-type col-6 d-flex flex-column justify-content-start headline">')[1:]:
			sprittype = self.searchOneValue(r'<div class="price-type-name">(.*?)</div>', rawentry, "")
			if sprittype == SPRITDICT.get(self.spritB, ""):
				price.append(self.searchOneValue(r'<span id="current-price-.d*">(.*?)</span>', rawentry, "?.???"))
				price.append(self.searchOneValue(r'<sup id="suffix-price-.d*">(.*?)</sup>', rawentry, "?"))
				break
		rawentry = self.searchOneValue(r'<div class="price-footer row col-12 text text-color-ice-blue d-flex flex-column">(.*?)</div>', output, "", flag_S=True)
		pcngtype, pcngdate, pcngdur = ("geändert", "unbekannt", "unbekannt")
		for last in rawentry.replace("<span>", "").replace("</span>", "").strip().split("\n"):
			part = last.split(": ")
			pcngdate, pcngdur = part[1].split(" ") if len(part) > 0 else ("unbekannt", "unbekannt")
		self.framefavs.append(tuple((ident, price[0], price[1], pcngtype, pcngdate, pcngdur, name, street, f"{zipcode} {city}", "", "♥")))
		if len(self.framefavs) == len(self.favlist):  # sämtliche Favoriten heruntergeladen?
			self["frame_B"].updateList(self.framefavs)
			self.ready = True
			self.refreshInfo()

	def toggleFrameB(self):
		self.frameBmode = "F" if self.frameBmode == "Z" else "Z"
		self.refresh_downblue()
		self.refreshFrameB()

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
				callInThread(download, f"{BASEURL}/tankstelle_details/{current[0]}?spritsorte={self.spritB}", self.makeTankenInfo)

	def changeFavorites(self):
		current = self[f"frame_{self.currframe}"].getCurrent()
		if current:
			callInThread(download, f"{BASEURL}/tankstelle_details/{current[0]}?spritsorte={self.spritB}", boundFunction(self.makeTankenView, "B"))
			ident = current[0]
			if ident in self.favlist:
				text = "Wollen Sie diese Tankstelle wirklich aus den Favoriten entfernen?"
				self.session.openWithCallback(boundFunction(self.writeConfig, ident, True), MessageBox, text, MessageBox.TYPE_YESNO, timeout=20, default=False)
			else:
				self.writeConfig(ident, False, True)

	def writeConfig(self, ident, remove, answer):
		self.favlist.remove(ident) if remove else self.favlist.append(ident)
		if answer is True:
			config.plugins.clevertanken.favorites.value = ",".join(self.favlist)
			config.plugins.clevertanken.favorites.save()
			config.plugins.clevertanken.save()
			self.refreshFrames()

	def turnSortA(self):
		if self.ready:
			self.ready = False
			keylist = list(SORTDICT.keys())
			self.sortA = list(SORTDICT.keys())[(keylist.index(self.sortA) + 1) % len(keylist)]  # get next key in turn
			callInThread(download, self.createLink("A", self.sortA, self.spritA, self.radiusA), boundFunction(self.makeTankenView, "A"))

	def turnSortB(self):
		if self.ready:
			self.ready = False
			keylist = list(SORTDICT.keys())
			self.sortB = list(SORTDICT.keys())[(keylist.index(self.sortB) + 1) % len(keylist)]  # get next key in turn
			callInThread(download, self.createLink("B", self.sortB, self.spritB, self.radiusB), boundFunction(self.makeTankenView, "B"))

	def turnRadiusA(self):
		if self.ready:
			self.ready = False
			keylist = list(RADIUSDICT.keys())
			self.radiusA = list(RADIUSDICT.keys())[(keylist.index(self.radiusA) + 1) % len(keylist)]  # get next key in turn
			callInThread(download, self.createLink("A", self.sortA, self.spritA, self.radiusA), boundFunction(self.makeTankenView, "A"))

	def turnRadiusB(self):
		if self.ready:
			self.ready = False
			keylist = list(RADIUSDICT.keys())
			self.radiusB = list(RADIUSDICT.keys())[(keylist.index(self.radiusB) + 1) % len(keylist)]  # get next key in turn
			callInThread(download, self.createLink("B", self.sortB, self.spritB, self.radiusB), boundFunction(self.makeTankenView, "B"))

	def turnSpritA(self):
		if self.ready:
			self.ready = False
			keylist = list(SPRITDICT.keys())
			self.spritA = list(SPRITDICT.keys())[(keylist.index(self.spritA) + 1) % len(keylist)]  # get next key in turn
			callInThread(download, self.createLink("A", self.sortA, self.spritA, self.radiusA), boundFunction(self.makeTankenView, "A"))

	def turnSpritB(self):
		if self.ready:
			self.ready = False
			keylist = list(SPRITDICT.keys())
			self.spritB = list(SPRITDICT.keys())[(keylist.index(self.spritB) + 1) % len(keylist)]  # get next key in turn
			callInThread(download, self.createLink("B", self.sortB, self.spritB, self.radiusB), boundFunction(self.makeTankenView, "B"))

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

	def refreshInfo(self):
		if self.ready:
			current = self[f"frame_{self.currframe}"].getCurrent()
			if current:
				ident = current[0]
				if ident:
					if self.isInfo:
						callInThread(download, f"{BASEURL}/tankstelle_details/{ident}?spritsorte={self.spritB}", self.makeTankenInfo)
					self["dkey_green"].setText("lang | aus Favoriten entfernen" if ident in self.favlist else "lang | zu Favoriten hinzufügen")
				else:
					if self.isInfo:
						self.showInfo['info'].setText("keine Favoriten vorhanden")
					self["dkey_green"].setText("")
			self.refresh_downblue()

	def refresh_downblue(self):
		self["dkey_blue"].setText("lang | wechsle zu Favoriten" if self.frameBmode == "Z" else "lang | wechsle zu Zweitort")

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
			self.refreshInfo()

	def config(self):
		self.isInfo = False
		self.showInfo.hide()
		self.session.openWithCallback(self.refreshAfterConfig, TankenConfig)

	def refreshAfterConfig(self):
		self.getConfigs()
		self.refreshFrames()

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def exit(self):
		if self.isInfo:
			self.isInfo = False
			self.showInfo.hide()
		else:
			self.session.deleteDialog(self.showInfo)
			self.close()


class tankenInfo(Screen):
	skin = """
	<screen name="tankenInfo" position="center,center" size="510,795" zPosition="2" flags="wfNoBorder" title="Tankstellendetails" >
		<eLabel position="0,0" size="510,795" backgroundColor="grey" zPosition="-1" />
		<widget source="info" render="Label" position="5,5" size="500,785" font="Regular;27" backgroundColor="#10233d67" halign="center" valign="top" transparent="0" zPosition="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["info"] = StaticText("")


class TankenConfig(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "clevertankenconfig", plugin="Extensions/clever-tanken", PluginLanguageDomain="clevertanken")
		self["key_yellow"] = StaticText("Hauptort suchen")
		self["key_blue"] = StaticText("Zweitort suchen")
		self["entryActions"] = HelpableActionMap(self, ["ColorActions"],
														{
														"yellow": (self.cityAsearch, "Hauptort suchen"),
														"blue": (self.cityBsearch, "Zweitort suchen")
														}, prio=0, description="clever-tanken Eingabeaktionen")

	def cityAsearch(self):
		cityname = " ".join(config.plugins.clevertanken.cityAzipname.value.split(" ")[1:])
		self.session.openWithCallback(boundFunction(self.VirtualKeyBoardCB, "A"), VirtualKeyBoard, title="Geben Sie den gewünschen Hauptort ein.", text=cityname)

	def cityBsearch(self):
		cityname = " ".join(config.plugins.clevertanken.cityBzipname.value.split(" ")[1:])
		self.session.openWithCallback(boundFunction(self.VirtualKeyBoardCB, "B"), VirtualKeyBoard, title="Geben Sie den gewünschen Hauptort ein.", text=cityname)

	def VirtualKeyBoardCB(self, frame, answer):
		if answer is not None:
			cityname = answer.replace(" ", "+").replace("/", "%2F")
			text = f"https://gcx01.123map.de/pcplace.json?thm=inforoad-ct1&zipcodecenter=1&limit=10&qa={cityname}"
			callInThread(download, text, boundFunction(self.citysearchCB, frame))

	def citysearchCB(self, frame, jsonstr):
		citydict = dict()
		try:
			citydict = loads(jsonstr)
		except Exception as error:
			print("[%s] ERROR in module 'cityserachCB': %s" % (MODULE_NAME, str(error)))
		citylist = []
		for city in citydict:
			zipname, lat, lon = city.get("value", ""), city.get("lat", ""), city.get("lon", "")
			if zipname and lat and lon:
				citylist.append((zipname, lat, lon))
		self.session.openWithCallback(boundFunction(self.citysearchReturn, frame), ChoiceBox, text="Wähle den gewünschten Ort / Ortsteil.", title="Städtesuche", list=tuple(citylist))

	def citysearchReturn(self, frame, answer):
		if answer is not None:
			if frame == "A":
				config.plugins.clevertanken.cityAzipname.value = answer[0].strip()
				config.plugins.clevertanken.cityAgeodata.value = (answer[1], answer[2])
				config.plugins.clevertanken.cityAgeodata.save()
			else:
				config.plugins.clevertanken.cityBzipname.value = answer[0].strip()
				config.plugins.clevertanken.cityBgeodata.value = (answer[1], answer[2])
				config.plugins.clevertanken.cityBgeodata.save()
			config.plugins.clevertanken.save()
			configfile.save()

	def keyCancel(self):
		self.close()


def main(session, **kwargs):
	session.open(clevertankenMain)


def Plugins(**kwargs):
	return [PluginDescriptor(name="clever-tanken.de", description="Tankstellen-Preisvergleich", where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main), PluginDescriptor(name="clever-tanken.de", description="Tankstellen-Preisvergleich", where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]

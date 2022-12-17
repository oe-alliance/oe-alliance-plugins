#!/usr/bin/python
# -*- coding: utf-8 -*-
from re import sub, findall, S as RES, search
from six import ensure_str
from twisted.internet import reactor
NEXTPage1 = 'class="js-track-link pagination__link pagination__link--next"'
NEXTPage2 = '<a\ href="(.*?)"'


def shortenChannel(text):
	text = text.strip()
	map = {"ProSieben": "Pro7 ", "kabel eins CLASSICS": "k1CLASSICS", "Sky Family": "SkyFamily", "Sky Cinema+": "SkyCine+",
			"Sky Comedy": "SkyComedy", "Sky Emotion": "SkyEmotion", "Sky Sport HD": "SkySport", "Eurosport ": "Eurosport",
			"EXTREME SPORTS": "EXTREME", "NAT GEO WILD": "NatGeoWild", "Romance TV": "RomanceTV", "13th Street": "13thStreet",
			"VH1 Classic": "VH1Classic", "COMEDY CENTRAL": "COMEDY C", "Cartoon Network": "CartoonNet", "Beate-Uhse": "Beate Uhse",
			"Disney Cinemagic": "DisneyCine", "HISTORY HD": "History HD", "DELUXE MUSIC": "DeluxMusic"
			}
	return map[text] if text in map else text


def transHTML(text):
	map = {"&nbsp;": " ", "&szlig;": "ß", "&quot;": ""","&ndash;": "-","&Oslash;": "","&bdquo;": """, "&ldquo;": """,
			"&rsquo;": """, "&gt;": ">", "&lt;": "<", "&shy;": "", "&copy;.*": " ", "&copy;": "", "&amp;": "&", "&uuml;": "ü",
			"&auml;": "ä", "&ouml;": "ö", "&eacute;": "é", "&hellip;": "...", "&egrave;": "è", "&agrave;": "à", "&aacute;": "á",
			"&mdash;": "-", "&Uuml;": "Ü", "&Auml;": "Ä", "&Ouml;": "Ö", "&#034;": ""","&#039;": """, "&#34;": """, "&#38;": "und",
			"&#39;": """, "&#133;": "...", "&#196;": "Ä", "&#214;": "Ö", "&#223;": "ß", "&#228;": "ä", "&#246;": "ö", "&#220;": "Ü",
			"&#252;": "ü", "&#287;": "c", "&#324;": "n", "&#351;": "s", "&#8211;": "-", "&#8212;": "\x97", "&#8216;": """,
			"&#8217;": """, "&#8220;": ""","&#8221;": """, "&#8230;": "...", "&#8242;": ""","&#8243;": """
			}
	return map[text] if text in map else text


def transCHANNEL(data, separate=False):
	map = {"das erste.*?": "ard",
			"zdf_neo.*?": "2neo",
			"zdfinfo.*?": "zinfo",
			"zdf.*?": "zdf",
			"tagesschau.*?": "tag24",
			"phoenix.*?": "phoen",
			"pro.*?fun.*?": "pro7f",
			"pro.*?maxx.*?": "pro7m",
			"pro.*?": "pro7",
			"sat.*?e.*?": "sat1e",
			"sat.*?g.*?": "sat1g",
			"sat.*?": "sat1",
			"3sat.*?": "3sat",
			"rtl c.*?": "rtl-c",
			"rtl l.*?": "rtl-l",
			"nitro.*?": "rtl-n",
			"rtl n.*?": "rtl-n",
			"rtln.*?": "rtl-n",
			"rtl p.*?": "pass",
			"rtlzwei.*?": "rtl2",
			"rtl.*?2.*?": "rtl2",
			"rtlup.*?": "rtlpl",
			"super rtl.*?": "super",
			"rtl.*?": "rtl",
			"voxup.*?": "voxup",
			"vox.*?": "vox",
			"sixx.*?": "sixx",
			"kabel.*? c.*?": "k1cla",
			"kabel.*? d.*?": "k1doku",
			"kabel.*?": "k1",
			"sky 1.*?": "sky1",
			"sky one.*?": "sky1",
			"sky .*?action.*?": "sky-a",
			"sky .*?atlantic.*?": "skyat",
			"sky .*?fun.*?": "sky-c",
			"sky .*?special.*?": "skycs",
			"sky .*?family.*?": "sky-f",
			"sky .*?007.*?": "sky-h",
			"sky .*?best of.*?": "sky-h",
			"sky .*?nature.*?": "sky-na",
			"sky .*?documentaries.*?": "sky-d",
			"sky .*?star.*?": "sky-h",
			"sky .*?krimi.*?": "sky-k",
			"sky .*?crime.*?": "sky-cr",
			"sky .*?classics.*?": "sky-n",
			"sky .*?select.*?": "sky-s",
			"sky .*?replay.*?": "skyrp",
			"sky .*?premieren.*?24.*?": "cin24",
			"sky .*?premieren.*?": "cin",
			"sky .*?thriller.*?": "skyth",
			"sky .*?special.*?": "skycs",
			"sky .*?showcase.*?": "skysh",
			"sky .*?xmas.*?": "xmas",
			"sky .*?christmas.*?": "xmas",
			"sky .*?comedy.*?": "sky-co",
			"sky .*?sport.*? golf.*?": "skysg",
			"sky .*?sport.*? mix.*?": "skysm",
			"sky .*?sport.*? golf.*?": "skysg",
			"sky .*?sport.*? top.*?event.*?": "skyste",
			"sky .*?sport.*? premier.*?league.*?": "skyspl",
			"sky .*?sport.*? tennis.*?": "skyst",
			"sky .*?sport.*? f1.*?": "skyf1",
			"sky .*?sport.*? austria.*?": "spo-a",
			"sky .*?sport.*? hd 1.*?": "hdspo",
			"sky .*?sport.*? 1.*?": "hdspo",
			"sky .*?buli.*? bundesliga*?": "buli",
			"sky .*?sport.*? hd 2.*?": "shd2",
			"sky .*?sport.*? 2.*?": "shd2",
			"sky .*?sport.*? news.*?": "snhd",
			"sky .*?bundesliga.*?": "buli",
			"sky.bundesliga.*?": "buli",
			"bundesliga.*?": "buli",
			"sky. bundesliga.*?": "buli",
			"eurosport 1.*?": "euro",
			"eurosport 2.*?": "euro2",
			"sport1\\+.*?": "s1plu",
			"sport1.*?": "sport",
			"sport 1.*?": "sport",
			"dazn 2.*?": "dazn",
			"esports1.*?": "es1",
			"motorvision tv.*?": "movtv",
			"auto.*?motor.*?sport.*?": "ams",
			"sportdigital.*?fussball.*?": "spo-d",
			"magenta.*?sport.*?": "maspo",
			"extreme.*? sports.*?": "ex-sp",
			"kinowelt.*?": "kinow",
			"fox.*?": "fox",
			"syfy.*?": "scifi",
			"universal.*?": "unive",
			"toggo.*?": "toggo",
			"romance tv.*?": "rom",
			"heimatkanal.*?": "heima",
			"biography.*?": "bio",
			"bio channel": "bio",
			"tele 5.*?": "tele5",
			"anixe.*?": "anixe",
			"13th.*?": "13th",
			"axn.*?": "axn",
			"silverline.*?": "silve",
			"welt der wunder.*?": "wdwtv",
			"arte.*?": "arte",
			"ntv.*?": "ntv",
			"n24 d.*?": "n24doku",
			"n24.*?": "welt",
			"cnn.*?": "cnn",
			"bbc w.*?": "bbc",
			"bbc e.*?": "bbc-e",
			"dmax.*?": "dmax",
			"spiegel .*?geschichte.*?": "sp-ge",
			"spiegel .*?history.*?": "sp-ge",
			"spiegel .*?wissen.*?": "sptvw",
			"curiosity channel.*?": "sptvw",
			"the history.*?": "hishd",
			"history.*?": "hishd",
			"animal planet.*?": "aplan",
			"crime \\+ investigation.*?": "crin",  # Suchstrings zuerst mit re.escape wandeln (z.B. siehe hier '\\+' = '+')
			"planet.*?": "plane",
			"discovery.*?": "hddis",
			"discovery channel.*?": "disco",
			"natgeo wild.*?": "n-gw",
			"nat geo wild.*?": "n-gw",
			"natgeo people.*?": "n-gp",
			"nat geo people.*?": "n-gp",
			"natgeo.*?": "n-ghd",
			"nat geo.*?": "n-ghd",
			"national geographic.*?": "n-ghd",
			"bongusto.*?": "gusto",
			"bon gusto.*?": "gusto",
			"servus.*?": "servu",
			"one.*?": "fes",
			"ard alpha.*?": "alpha",
			"ard-alpha.*?": "alpha",
			"srf1.*?": "sf1",
			"srf 1.*?": "sf1",
			"srf.*?": "sf2",
			"srf2.*?": "sf2",
			"srf 2.*?": "sf2",
			"srf zwei.*?": "sf2",
			"hamburg 1": "hh1",
			"m.*?nchen2": "mue2",
			"m.*?nchen.tv": "tvm",
			"tv.berlin": "tvb",
			"leipzig fernsehen.*?": "leitv",
			"nrw.tv.*?": "nrwtv",
			"rheinmain tv.*?": "rmtv",
			"rnf.*?": "rnf",
			"sachsen fernsehen.*?": "sach",
			"orf 1.*?": "orf1",
			"orf1.*?": "orf1",
			"orf eins.*?": "orf1",
			"orf 2.*?": "orf2",
			"orf2.*?": "orf2",
			"orf 3.*?": "orf3",
			"orf.sport.*?": "orfsp",
			"orf.*?": "orf1",
			"sf1.*?": "sf1",
			"sf 1.*?": "sf1",
			"sf 2.*?": "sf2",
			"sf zwei.*?": "sf2",
			"atv": "atv",
			"atv hd": "atv",
			"atv2.*?": "atv2",
			"atv 2.*?": "atv2",
			"atv ii": "atv2",
			"puls 4.*?": "puls4",
			"boomerang.*?": "boom",
			"nick jr.*?": "nickj",
			"nick.*?": "nick",
			"nicktoons.*?": "nickt",
			"comedy central.*?": "cc",
			"cartoon net.*?": "c-net",
			"disney cinema.*?": "dcm",
			"disney channel.*?": "disne",
			"disney junior.*?": "djun",
			"disney xd.*?": "dxd",
			"disney hd": "disne",
			"junior.*?": "junio",
			"kika.*?": "kika",
			"vh1 classic.*?": "vh1",
			"deluxe music.*?": "dmc",
			"mtv": "mtv",
			"mtv hd": "mtv",
			"mtv g.*?": "mtv",
			"mtv ba.*?": "mtv-b",
			"mtv da.*?.*?": "mtv-d",
			"mtv hi.*?.*?": "mtv-h",
			"mtv li.*?": "mtv-l",
			"viva.*?": "viva",
			"im1": "imt",
			"rock tv.*?": "rck",
			"jukebox.*?": "juke",
			"trace.*?": "trace",
			"classica.*?": "class",
			"gute laune.*?": "laune",
			"beate uhse.*?": "butv",
			"lust pur.*?": "lustp",
			"playboy tv": "pboy",
			"al jazeera.*?": "aljaz",
			"bloomberg.*?": "blm",
			"euronews.*?": "euron",
			"bibel tv.*?": "bibel",
			"kirchen tv.*?": "ktv",
			"timm.*?": "timm",
			"sonnenklar.*?": "sklar",
			"goldstar tv": "gold",
			"animax": "amax",
			"adult channel.*?": "adult",
			"das neue tv.*?": "dntv",
			"deutsches wetter.*?": "dwf",
			"e!.*?": "e!",
			"fashion tv.*?": "fatv",
			"family tv.*?": "famtv",
			"mezzo.*?": "mezzo",
			"nautical.*?": "nauch",
			"nl 1.*?": "nl1",
			"nl 2.*?": "nl2",
			"nl 3.*?": "nl3",
			"dr1.*?": "dr1",
			"belgien.*?": "be1",
			"france24.*?fr.*?": "fr24f",
			"france24.*?en.*?": "fr24e",
			"france 2.*?": "fra2",
			"france 3.*?": "fra3",
			"france 5.*?": "fra5",
			"tv 2.*?": "tv5",
			"tv 5.*?": "tv5",
			"ric.*?": "ric",
			"tlc.*?": "tlc",
			"star tv.*?": "sttv",
			"center.tv.*?": "cente",
			"sony.*?": "sony",
			"3 plus.*?": "3plus",
			"3\\+.*?": "3plus",
			"marco polo.*?": "mapo",
			"travel channel.*?": "trch",
			"home.*?garden.*?": "hgtv",
			'hgtv.*?': 'hgtv',
			"channel21.*?": "ch21",
			"geo television.*?": "geo",
			"geo tv.*?": "geo",
			"fix.*?foxi.*?": "fftv",
			"welt.*?": "welt",
			"uhd1.*?": "uhd1",
			"dw.*?": "dwtv",
			"deutsches musik fernsehen.*?": "dmf",
			"rbb.*?": "rbb",
			"ndr.*?": "n3",
			"mdr.*?": "mdr",
			"wdr.*?": "wdr",
			"hr.*?": "hr",
			"swr.*?": "swr",
			"sr fernsehen.*?": "swr",
			"br.*?": "br",
			"bayerisches.*?": "br",
			"tele 5.*?": "TELE5",
			"bild hd": "bild",
			"warner .*?comedy.*?": "tnt-c",
			"warner .*?film.*?": "tnt-f",
			"warner .*?serie.*?": "tnt-s",
			"tnt .*?comedy.*?": "tnt-c",
			"tnt .*?film.*?": "tnt-f",
			"tnt .*?serie.*?": "tnt-s",
			"hse.*?": "hse",
			"qvc.*?": "qvc",
			"health.*?": "health"
			}
	new = []
	for item in data.strip().split("\n"):  # Trenner '\t' und Return '\n' geeignet einfügen
		sref = search(" \d+:\d+:\w+:\w+:\w+:\w+:\w+:\d+:\w+:\w+:.*", item)
		new.append("%s\t\n" % item.lower() if sref is None else "%s\t%s\n" % (item[:sref.start(0)].strip().lower(), sref.group(0)))
	new = "".join(new)
	for pattern, shortcut in map.items():  # alle Sendernamen austauschen
		new = "%s\n" % sub("%s\t" % pattern, "%s\t" % shortcut, new).strip()
	if separate:
		supported = []
		unsupported = []
		for item in new.rstrip().split("\n"):  # separieren
			if item.split("\t")[0] in list(map.values()):
				supported.append(item.replace("\t", ""))
			else:
				unsupported.append(item.replace("\t", ""))
		supported = "\n".join(supported)
		unsupported = "\n".join(unsupported)
		return supported, unsupported
	else:
		return new.replace("\t", "")


def parsedetail(bereich, debug=None):
	bereich = sub('<blockquote class="broadcast-detail__quote">\n\\s+<p>', '<p>>> ', bereich)
	bereich = sub('</p>\n[ ]+</blockquote>', ' <<</p>', bereich)
	bereich = sub('<section class="serial-info">\n\\s+', '<p>', bereich)
	bereich = sub('</section>', '</p>', bereich)
	bereich = sub('</span>\\s+', '</span>, ', bereich)
	bereich = sub('<li class="titleName">', '</p><p> \xc2\xb7 ', bereich)
	bereich = sub('<li class="subtitleName">', '#sub#', bereich)
	bereich = sub('ShowView [0-9-]+', '', bereich)
	bereich = sub('<a href=".*?">', '', bereich)
	bereich = sub('<h1.*?>', '<p>', bereich)
	bereich = sub('</h1>', '</p>', bereich)
	bereich = sub('<h3.*?>', '<p>', bereich)
	bereich = sub('</h3>', '</p>', bereich)
	bereich = sub('<br/>', '</p><p>', bereich)
	bereich = sub('<p>\n', '<p>', bereich)
	bereich = sub('<dt>', '<p>', bereich)
	bereich = sub('<dt class="role">', '<p>', bereich)
	bereich = sub('</dt>\n\\s+<dd>\n\\s+', ' ', bereich)
	bereich = sub('</dt>\n\\s+<dd>', ' ', bereich)
	bereich = sub('</dt>\n\\s+<dd class="name">', ': ', bereich)
	bereich = sub('\n[ ]+,', ',', bereich)
	bereich = sub(', [ ]+', ', ', bereich)
	bereich = sub('</a>', '</p>', bereich)
	bereich = sub('\n\\s+</dd>', '</p>', bereich)
	bereich = sub('</a></dd>', '</p>', bereich)
	bereich = sub('</dd>', '</p>', bereich)
	bereich = sub('</dt>', '</p>', bereich)
	text = ''
	a = findall('<p.*?>(.*?)</p>', bereich)
	for x in a:
		if x != '':
			text += x + '\n\n'
	if debug != None:
		print("[DEBUG] parsedetail %s\n" % debug)
		print(text)
	text = sub('<[^>]*>', '', text)
	text = sub('</p<<p<', '\n\n', text)
	text = sub('\n\\s+\n*', '\n\n', text)
	text = sub('#sub#', '\n  ', text)
	if debug != None:
		print("[DEBUG] parsedetail %s\n" % debug)
		print(text)
	return text


def cleanHTML(bereich):
	bereich = transHTML(bereich)
	bereich = sub('\r', '', bereich)
	bereich = sub('<ul class="slidelist">.*?</ul>', '', bereich, flags=RES)
	bereich = sub('<div class="vod".*?<script>', '<script>', bereich, flags=RES)
	bereich = sub('<script.*?</script>', '', bereich, flags=RES)
	bereich = sub('<style.*?</style>', '', bereich, flags=RES)
	bereich = sub('<div class="text" id=".*?</div>', '', bereich, flags=RES)
	bereich = sub('<div class="vod".*?</div>', '', bereich, flags=RES)
	return bereich


def fiximgLink(link):
	link = sub('" alt.*', '', link)
	return sub('.*data-src="', '', link)


def parsePrimeTimeTable(output, debug=None):
	startpos = output.find('<table class="primetime-table">')
	endpos = output.find('</table>')
	bereich = transHTML(output[startpos:endpos])
	items = findall('<tr>(.*?)</tr>', bereich, RES)
	entries = []
	for item in items:
		date = findall('<span>TV-Sendungen am (.*?)</span>', item, RES)
		if len(date) == 1:
			entries.append((date[0], None, None, None, None, None, None, None))
		else:
			try:
				LOGO = findall('<img src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*?).png.*?', item, RES)[0]
				START, END = findall('class="search-starttimes">\n\\s+<span>(.*?)</span> - (.*?)\n', item, RES)[0]
				INFOS = findall('<li class="(.*?)', item, RES)
				try:
					LINK, TITLE = findall('<h3><a href="(.*?)".*?title="(.*?)"', item, RES)[0]
				except:
					LINK = None
					TITLE = None
				try:
					GENRE = findall('<p>(.*?)\n', item, RES)[0]
				except:
					GENRE = None
				try:
					RATING = findall('class="editorial-(.*?)"', item, RES)[0]
				except:
					RATING = None
				entries.append((None, START, TITLE, GENRE, INFOS, LOGO, LINK, RATING))
			except:
				pass
	if debug != None:
		print("[DEBUG] parsePrimeTimeTable %s\n" % debug)
		print(bereich)
	return entries, bereich


def parseTrailerUrl(output, videoformat='.mp4'):
	output = ensure_str(output)
	if search('https://video.tvspielfilm.de/.*?' + videoformat, output) is not None:
		trailerurl = search('https://video.tvspielfilm.de/(.*?)' + videoformat, output)
		return 'https://video.tvspielfilm.de/' + trailerurl.group(1) + videoformat
	else:
		return None


def buildTVTippsArray(sparte, output):
	if sparte == 'neu':
		startpos = output.find('id="c-sp-opener"><span>Spielfilm</span></a>')
		endpos = output.find('id="c-spo-opener"><span>Sport</span></a>')
	elif sparte == 'Spielfilm':
		startpos = output.find('id="c-sp-opener"><span>Spielfilm</span></a>')
		endpos = output.find('id="c-se-opener"><span>Serie</span></a>')
	elif sparte == 'Serie':
		startpos = output.find('id="c-se-opener"><span>Serie</span></a>')
		endpos = output.find('id="c-re-opener"><span>Report</span></a>')
	elif sparte == 'Report':
		startpos = output.find('id="c-re-opener"><span>Report</span></a>')
		endpos = output.find('id="c-u-opener"><span>Unterhaltung</span></a>')
	elif sparte == 'Unterhaltung':
		startpos = output.find('id="c-u-opener"><span>Unterhaltung</span></a>')
		endpos = output.find('id="c-kin-opener"><span>Kinder</span></a>')
	elif sparte == 'Kinder':
		startpos = output.find('id="c-kin-opener"><span>Kinder</span></a>')
		endpos = output.find('id="c-spo-opener"><span>Sport</span></a>')
	elif sparte == 'Sport':
		startpos = output.find('id="c-spo-opener"><span>Sport</span></a>')
		endpos = output.find('<p class="h3 headline headline--section">')
	bereich = output[startpos:endpos]
	bereich = transHTML(bereich)
	items = findall('<li>(.*?)</li>', bereich, RES)
	entries = []
	for item in items:
		LOGO = findall('<img src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*?).png.*?', item, RES)[0]
		TIME = findall('<span class="time">(.*?)</span>', item, RES)[0]
		try:
			LINK = findall('<div class="full-image image-wrapper.*?">\n\\s+<a href="(.*?)"', item, RES)[0]
		except:
			LINK = None
		NAME = findall('<strong>(.*?)</strong>', item, RES)[0]
		try:
			GENRE = findall('<span>(.*?)</span>', item, RES)[0]
		except:
			GENRE = None
		INFOS = findall('<span class="add-info (.*?)">', item, RES)
		PIC = findall(' data-src="(.*?)" ', item, RES)
		if len(PIC) > 0:
			PIC = PIC[0]
		else:
			PIC = findall('<img src="(https://a2.tvspielfilm.de/imedia/.*?)" ', item, RES)[0]
		entries.append((LINK, PIC, TIME, INFOS, NAME, GENRE, LOGO))
	return entries


def parseNow(output):
	startpos = output.find('<table class="info-table"')
	endpos = output.find('<div class="block-in">')
	if endpos == -1:
		endpos = output.find('<div class="two-blocks">')
	bereich = transHTML(output[startpos:endpos])
	items = findall('<tr class="hover">(.*?)</tr>', bereich, RES)
	entries = []
	for item in items:
		b = findall('<img src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*?).png.*?<div>\n\\s+<strong>(.*?)</strong>\n\\s+<span>(.*?)</span>', item, RES)
		LOGO, TIME, DATE = b[0]
		try:
			title = findall('link" title="(.*?)"', item, RES)[1]
		except:
			title = findall('link" title="(.*?)"', item, RES)[0]
		try:
			genre = findall('<td class="col-4">\n\\s+<span>(.*?)</span>', item, RES)[0]
		except:
			genre = None
		try:
			sparte = findall('<td class="col-5">\n\\s+<span>(.*?)\n\\s+</span>', item, RES)[0].replace('<br/>', '')
			sparte = findall('<td class="col-5">\n\\s+<span>(.*?)\n\\s+</span>', item, RES)[0].replace('<br/>', '')
			subsparte = None
			if search('<em>', sparte):
				subsparte = findall('<em>(.*?)</em>', sparte)[0]
				sparte = sub('<em>.*?</em>', '', sparte).rstrip()
				if subsparte:
					sparte = sparte + '\n' + subsparte
		except:
			sparte = None
		try:
			rating = findall('class="editorial-(.*?)"', item, RES)[0]
		except:
			rating = None
		LINK = findall('<span>\n\\s+<a href="(https://www..*?.html)"', item, RES)[0]
		try:
			trailer = findall('<span class="add-info icon-movieteaser"></span>', item, RES)[0]
		except:
			trailer = None
		entries.append((LOGO, TIME, LINK, title, sparte, genre, rating, trailer))
	return entries, output


def parseInfo(output):
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
	print(bereich)
	print(trailerurl)
	bereich = sub('" alt=".*?" width="', '" width="', bereich)
	picurl = search('<img src="(.*?)" data-src="(.*?)" width="', bereich)
	print(picurl.group(2))


def testtvtipps(output):
	output = ensure_str(output)
	a = buildTVTippsArray("Serie", output)
	print(a)


def testtvnow(output):
	output = ensure_str(output)
	a = parsePrimeTimeTable(output, True)
	#a = findall('<td>(.*?)</td>', bereich)
	print(a)


def saveerr(output):
	print(output)
	reactor.stop()


def savefile(output):
	open('tmp.html', 'wb').write(output)
	reactor.stop()


def testparseNow(output):
	output = ensure_str(output)
	a, b = parseNow(output)
	print(a)


def testparseInfo(output):
	output = ensure_str(output)
	parseInfo(output)


def test():
#	from twisted.web.client import getPage
#	link = b'https://www.tvspielfilm.de/tv-tipps/'
#	link = b'https://www.tvspielfilm.de/tv-programm/sendungen/jetzt.html'
#    link = b'https://www.tvspielfilm.de/tv-programm/sendungen/?page=1&order=time&date=2021-05-06&tips=0&time=day&channel=3SAT'
#    link = b'https://www.tvspielfilm.de/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&ext=1&q=&cat%5B0%5D=SP&genreSP=Abenteuer&time=day&date=&channel='
#    link = b'https://www.tvspielfilm.de/tv-programm/sendungen/?page=1&order=time&date=2021-05-07&tips=0&time=day&channel=ARD'
#    link = b'https://www.tvspielfilm.de/tv-programm/sendungen/abends.html'
#	link = b'https://www.tvspielfilm.de/tv-programm/sendung/wasserball,60f06a338189652e9978032c.html'
#    getPage(link).addCallback(savefile).addErrback(saveerr)
#    reactor.run()
	output = open('tmp.html', 'rb').read()
#    testtvsuche(output)
#    testparseNow(output)
#    testparseNow(output)
	testparseInfo(output)


if __name__ == '__main__':
	test()

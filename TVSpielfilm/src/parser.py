# -*- coding: utf-8 -*-
# PYTHON IMPORTS
from re import sub, findall, search, S
from six import ensure_str
from twisted.internet import reactor
from xml.sax.saxutils import unescape

NEXTPage1 = r'class="js-track-link pagination__link pagination__link--next"'
NEXTPage2 = r'<a\ href="(.*?)"'


def shortenChannel(text):
	text = text.replace('ProSieben', 'Pro7').replace('EXTREME SPORTS', 'EXTREME').replace('NatGeo Wild', 'NatGeoWild').replace('Nat Geo Wild', 'NatGeoWild')
	text = text.replace("National Geographic", "NatGeo").replace("SRF 1", "SRF1").replace("SRF 2", "SRF2").replace("ATV 2", "ATV2")
	return text.rstrip()


def transCHANNEL(data, separate=False):
	mapping = {r"das\s+erste.*?": "ard",
			r"zdf_neo.*?": "2neo",
			r"zdfinfo.*?": "zinfo",
			r"zdf\s+.*?": "zdf",
			r"tagesschau.*?": "tag24",
			r"phoenix.*?": "phoen",
			r"prosieben.*?fun.*?": "pro7f",
			r"prosieben.*?maxx.*?": "pro7m",
			r"prosieben.*?": "pro7",
			r"sat.*?e.*?": "sat1e",
			r"sat.*?g.*?": "sat1g",
			r"sat.1.*?": "sat1",
			r"3sat.*?": "3sat",
			r"rtl\s+c.*?": "rtl-c",
			r"rtl\s+l.*?": "rtl-l",
			r"nitro.*?": "rtl-n",
			r"rtl\s+n.*?": "rtl-n",
			r"rtln.*?": "rtl-n",
			r"rtl\s+p.*?": "pass",
			r"rtlzwei.*?": "rtl2",
			r"rtl.*?2.*?": "rtl2",
			r"rtlup.*?": "rtlpl",
			r"super\s+rtl.*?": "super",
			r"rtl\s+": "rtl",
			r"voxup.*?": "voxup",
			r"vox.*?": "vox",
			r"sixx.*?": "sixx",
			r"kabel.*? c.*?": "k1cla",
			r"kabel.*? d.*?": "k1doku",
			r"kabel.*?": "k1",
			r"n24\s+d.*?": "n24doku",
			r"n24\s+": "welt",
			r"sky\s+1.*?": "sky1",
			r"sky\s+one.*?": "sky1",
			r"sky\s+action.*?": "sky-a",
			r"sky\s+atlantic.*?": "skyat",
			r"sky\s+fun.*?": "sky-c",
			r"sky\s+special.*?": "skycs",
			r"sky\s+family.*?": "sky-f",
			r"sky\s+007.*?": "sky-h",
			r"sky\s+best\s+of.*?": "sky-h",
			r"sky\s+nature.*?": "sky-na",
			r"sky\s+documentaries.*?": "sky-d",
			r"sky\s+star.*?": "sky-h",
			r"sky\s+krimi.*?": "sky-k",
			r"sky\s+crime.*?": "sky-cr",
			r"sky\s+classics.*?": "sky-n",
			r"sky\s+select.*?": "sky-s",
			r"sky\s+replay.*?": "skyrp",
			r"sky\s+premieren.*?24.*?": "cin24",
			r"sky\s+premieren.*?": "cin",
			r"sky\s+thriller.*?": "skyth",
			r"sky\s+special.*?": "skycs",
			r"sky\s+showcase.*?": "skysh",
			r"sky\s+xmas.*?": "xmas",
			r"sky\s+christmas.*?": "xmas",
			r"sky\s+comedy.*?": "sky-co",
			r"sky\s+sport.*? golf.*?": "skysg",
			r"sky\s+sport.*? mix.*?": "skysm",
			r"sky\s+sport.*? golf.*?": "skysg",
			r"sky\s+sport.*? top.*?event.*?": "skyste",
			r"sky\s+sport.*? premier.*?league.*?": "skyspl",
			r"sky\s+sport.*? tennis.*?": "skyst",
			r"sky\s+sport.*? f1.*?": "skyf1",
			r"sky\s+sport.*? austria.*?": "spo-a",
			r"sky\s+sport.*? hd 1.*?": "hdspo",
			r"sky\s+sport.*? 1.*?": "hdspo",
			r"sky\s+buli.*? bundesliga*?": "buli",
			r"sky\s+sport.*? hd 2.*?": "shd2",
			r"sky\s+sport.*? 2.*?": "shd2",
			r"sky\s+sport.*? news.*?": "snhd",
			r"sky\s+bundesliga.*?": "buli",
			r"eurosport\s+1.*?": "euro",
			r"eurosport\s+2.*?": "euro2",
			r"sport1\\+.*?": "s1plu",
			r"sport\s+1.*?": "sport",
			r"sport1.*?": "sport",
			r"dazn\s+2.*?": "dazn",
			r"esports1.*?": "es1",
			r"motorvision\s+tv.*?": "movtv",
			r"auto.*?motor.*?sport.*?": "ams",
			r"sportdigital.*?fussball.*?": "spo-d",
			r"magenta.*?sport.*?": "maspo",
			r"extreme.*?": "ex-sp",
			r"kinowelt.*?": "kinow",
			r"fox.*?": "fox",
			r"syfy.*?": "scifi",
			r"universal.*?": "unive",
			r"toggo.*?": "toggo",
			r"romance.*?tv.*?": "rom",
			r"heimatkanal.*?": "heima",
			r"biography.*?": "bio",
			r"bio\s+channel": "bio",
			r"tele\s+5.*?": "tele5",
			r"anixe.*?": "anixe",
			r"13th.*?": "13th",
			r"axn.*?": "axn",
			r"silverline.*?": "silve",
			r"welt\s+der wunder.*?": "wdwtv",
			r"arte.*?": "arte",
			r"ntv.*?": "ntv",
			r"cnn.*?": "cnn",
			r"bbc\s+w.*?": "bbc",
			r"bbc\s+e.*?": "bbc-e",
			r"dmax.*?": "dmax",
			r"spiegel\s+geschichte.*?": "sp-ge",
			r"spiegel\s+history.*?": "sp-ge",
			r"spiegel\s+wissen.*?": "sptvw",
			r"curiosity channel.*?": "sptvw",
			r"the\s+history.*?": "hishd",
			r"history.*?": "hishd",
			r"animal planet.*?": "aplan",
			r"crime\s+\\+ investigation.*?": "crin",  # Suchstrings zuerst mit re.escape wandeln (z.B. siehe hier '\\+' = '+')
			r"planet.*?": "plane",
			r"discovery.*?": "hddis",
			r"discovery\s+channel.*?": "disco",
			r"natgeo\s+wild.*?": "n-gw",
			r"natgeo.*?": "n-ghd",
			r"bon.*?gusto.*?": "gusto",
			r"servus.*?": "servu",
			r"one.*?": "fes",
			r"ard-alpha.*?": "alpha",
			r"srf1.*?": "sf1",
			r"srf.*?": "sf2",
			r"srf2.*?": "sf2",
			r"srf\s+zwei.*?": "sf2",
			r"hamburg\s+1": "hh1",
			r"m.*?nchen2": "mue2",
			r"m.*?nchen.tv": "tvm",
			r"tv.berlin": "tvb",
			r"leipzig\s+fernsehen.*?": "leitv",
			r"nrw.tv.*?": "nrwtv",
			r"rheinmain\s+tv.*?": "rmtv",
			r"rnf.*?": "rnf",
			r"sachsen\s+fernsehen.*?": "sach",
			r"orf\s+1.*?": "orf1",
			r"orf1.*?": "orf1",
			r"orf\s+eins.*?": "orf1",
			r"orf\s+2.*?": "orf2",
			r"orf2.*?": "orf2",
			r"orf\s+3.*?": "orf3",
			r"orf\s+iii.*?": "orf3",
			r"orf.sport.*?": "orfsp",
			r"sf1.*?": "sf1",
			r"sf\s+1.*?": "sf1",
			r"sf\s+2.*?": "sf2",
			r"sf\s+zwei.*?": "sf2",
			r"atv2.*?": "atv2",
			r"atv\s+ii.*?": "atv2",
			r"atv\s+": "atv",
			r"puls\s+4.*?": "puls4",
			r"boomerang.*?": "boom",
			r"nick\s+jr.*?": "nickj",
			r"nick.*?": "nick",
			r"nicktoons.*?": "nickt",
			r"comedy\s+central.*?": "cc",
			r"cartoonnet.*?": "c-net",
			r"cartoon\s+net.*?": "c-net",
			r"disney\s+cinema.*?": "dcm",
			r"disney\s+channel.*?": "disne",
			r"disney\s+junior.*?": "djun",
			r"disney\s+xd.*?": "dxd",
			r"disney\s+hd": "disne",
			r"junior.*?": "junio",
			r"kika.*?": "kika",
			r"vh1.*?classic.*?": "vh1",
			r"deluxe\s+music.*?": "dmc",
			r"mtv": "mtv",
			r"mtv\s+hd": "mtv",
			r"mtv\s+g.*?": "mtv",
			r"mtv\s+ba.*?": "mtv-b",
			r"mtv\s+da.*?.*?": "mtv-d",
			r"club\s+mtv.*?": "mtv-d",
			r"mtv\s+hi.*?.*?": "mtv-h",
			r"mtv\s+li.*?": "mtv-l",
			r"viva.*?": "viva",
			r"im1": "imt",
			r"rock\s+tv.*?": "rck",
			r"jukebox.*?": "juke",
			r"trace.*?": "trace",
			r"classica.*?": "class",
			r"gute\s+laune.*?": "laune",
			r"beate\s+uhse.*?": "butv",
			r"lust\s+pur.*?": "lustp",
			r"playboy\s+tv": "pboy",
			r"al\s+jazeera.*?": "aljaz",
			r"bloomberg.*?": "blm",
			r"euronews.*?": "euron",
			r"bibel\s+tv.*?": "bibel",
			r"kirchen\s+tv.*?": "ktv",
			r"timm.*?": "timm",
			r"sonnenklar.*?": "sklar",
			r"goldstar\s+tv": "gold",
			r"animax": "amax",
			r"adult\s+channel.*?": "adult",
			r"das\s+neue\s+tv.*?": "dntv",
			r"deutsches\s+wetter.*?": "dwf",
			r"e!.*?": "e!",
			r"fashion\s+tv.*?": "fatv",
			r"family\s+tv.*?": "famtv",
			r"mezzo.*?": "mezzo",
			r"nautical.*?": "nauch",
			r"nl\s+1.*?": "nl1",
			r"nl\s+2.*?": "nl2",
			r"nl\s+3.*?": "nl3",
			r"dr1.*?": "dr1",
			r"belgien.*?": "be1",
			r"france24.*?fr.*?": "fr24f",
			r"france24.*?en.*?": "fr24e",
			r"france\s+2.*?": "fra2",
			r"france\s+3.*?": "fra3",
			r"france\s+5.*?": "fra5",
			r"tv\s+2.*?": "tv5",
			r"tv\s+5.*?": "tv5",
			r"ric.*?": "ric",
			r"tlc.*?": "tlc",
			r"star\s+tv.*?": "sttv",
			r"center.tv.*?": "cente",
			r"sony.*?": "sony",
			r"3\s+plus.*?": "3plus",
			r"3\\+.*?": "3plus",
			r"marco\s+polo.*?": "mapo",
			r"travel\s+channel.*?": "trch",
			r"home.*?garden.*?": "hgtv",
			r"hgtv.*?": "hgtv",
			r"channel21.*?": "ch21",
			r"geo\s+television.*?": "geo",
			r"geo\s+tv.*?": "geo",
			r"fix.*?foxi.*?": "fftv",
			r"welt.*?": "welt",
			r"uhd1.*?": "uhd1",
			r"dw\s+": "dwtv",
			r"deutsches\s+musik fernsehen.*?": "dmf",
			r"rbb\s+": "rbb",
			r"ndr\s+": "n3",
			r"mdr\s+": "mdr",
			r"wdr\s+": "wdr",
			r"hr\s+": "hr",
			r"hr-fernsehen.*?": "hr",
			r"swr\s+": "swr",
			r"sr\s+fernsehen.*?": "swr",
			r"br.*?": "br",
			r"bayerisches.*?": "br",
			r"bild.*?": "bild",
			r"warner\s+comedy.*?": "tnt-c",
			r"warner\s+film.*?": "tnt-f",
			r"warner\s+serie.*?": "tnt-s",
			r"tnt\s+comedy.*?": "tnt-c",
			r"tnt\s+film.*?": "tnt-f",
			r"tnt\s+serie.*?": "tnt-s",
			r"hse\s+": "hse",
			r"qvc.*?": "qvc",
			r"health.*?": "health"
			}
	new = ''
	data = data.replace('Pro7', 'ProSieben').replace("ARD alpha", "ARD-alpha").replace("Nat Geo", "NatGeo")
	for item in data.strip().split("\n"):  # Trenner '\t' und Return '\n' geeignet einfügen
		sref = search(" \d+:\d+:\w+:\w+:\w+:\w+:\w+:\d+:\w+:\w+:.*", item)
		new += "%s\t\n" % item.lower() if sref is None else "%s\t%s\n" % (item[:sref.start(0)].strip().lower(), sref.group(0))
	for pattern, shortcut in mapping.items():  # alle Sendernamen austauschen
		if search(r"%s" % pattern, new):
			new = new.replace(data.split("\t")[0].lower(), shortcut)
	if separate:
		supported = ''
		unsupported = ''
		for item in new.rstrip().split("\n"):  # separieren
			if item.split("\t")[0] in list(mapping.values()):
				supported += "%s\n" % item.strip()
			else:
				unsupported += "%s\n" % item.strip()
		return supported.replace("\t", "").rstrip(), unsupported.replace("\t", "").rstrip()
	else:
		return new.replace("\t", "").rstrip()


def searchOneValue(regex, text, fallback, flags=None):
	text = search(regex, text) if flags is None else search(regex, text, flags=flags)
	return text.group(1) if text else fallback


def searchTwoValues(regex, text, fallback1, fallback2, flags=None):
	text = search(regex, text) if flags is None else search(regex, text, flags=flags)
	return (text.group(1), text.group(2)) if text else (fallback1, fallback2)


def parsedetail(bereich, debug=None):
	quelle = search(r'<p\s*class="title">(.*?)</p>', bereich)
	quelle = quelle.group(1) if quelle else ""
	bewertung = search(r'<blockquote class="broadcast-detail__quote">\s*<p>(.*?)</p>\s*</blockquote>', bereich, flags=S)
	bewertung = bewertung.group(1) if bewertung else ""
	# entferne alle Tags
	bereich = sub(r'<p\s*class="title">(.*?)</p>', '', bereich)
	bereich = sub(r'<blockquote class="broadcast-detail__quote">\s*<p>(.*?)</p>\s*</blockquote>', '', bereich, flags=S)
	bereich = sub(r'</p>\s*[\s]+</blockquote>', ' <<</p>', bereich)
	bereich = sub(r'<section class="serial-info">\s*', '<p>', bereich)
	bereich = sub(r'</span>\s*', '</span>, ', bereich)
	bereich = sub(r'<li\sclass="titleName">', '</p><p> \xc2\xb7 ', bereich)
	bereich = sub(r'<li\sclass="subtitleName">', '#sub#', bereich)
	bereich = sub(r'ShowView [0-9-]+', '', bereich)
	bereich = sub(r'<a href=".*?">', '', bereich)
	bereich = sub(r'<h1[^>]>', '<p>', bereich)
	bereich = sub(r'<h3[^>]>', '<p>', bereich)
	bereich = sub(r'<p>\s*', '<p>', bereich)
	bereich = sub(r'</dt>\s*<dd>\s*', ' ', bereich)
	bereich = sub(r'</dt>\s*<dd>', ' ', bereich)
	bereich = sub(r'</dt>\s*<dd class="name">', ': ', bereich)
	bereich = sub(r'\s*[\s]+,', ',', bereich)
	bereich = sub(r',\s[\s]+', ', ', bereich)
	bereich = sub(r'\s*</dd>', '</p>', bereich)
	bereich = bereich.replace('</section>', '</p>').replace('&nbsp;', '').replace('</h1>', '</p>').replace('</h3>', '</p>')
	bereich = bereich.replace('<br/>', '</p><p>').replace('<dt>', '<p>').replace('<dt class="role">', '<p>').replace('</a>', '</p>')
	bereich = bereich.replace('</a></dd>', '</p>').replace('</dd>', '</p>').replace('</dt>', '</p>')
	text = ''
	for x in findall(r'<p.*?>(.*?)</p>', bereich):
		if x != '':
			text += "%s\n\n" % x
	if debug != None:
		print("[DEBUG] parsedetail %s\n" % debug)
		print(text)
	text = sub(r'<[^>]*>', '', text)
	text = sub(r'\n\\s+\n*', '\n\n', text)
	text = text.replace("</p<<p<", "\n\n").replace("#sub#", "\n  ")
	if debug != None:
		print("[DEBUG] parsedetail %s\n" % debug)
		print(text)
	return quelle, bewertung, text


def cleanHTML(bereich):
	bereich = unescape(bereich).replace('\r', '')
	bereich = sub(r'<ul class="slidelist">.*?</ul>', '', bereich, flags=S)
	bereich = sub(r'<div class="vod".*?<script>', '<script>', bereich, flags=S)
	bereich = sub(r'<script.*?</script>', '', bereich, flags=S)
	bereich = sub(r'<style.*?</style>', '', bereich, flags=S)
	bereich = sub(r'<div class="text" id=".*?</div>', '', bereich, flags=S)
	bereich = sub(r'<div class="vod".*?</div>', '', bereich, flags=S)
	return bereich


def fiximgLink(link):
	link = sub(r'" alt.*', '', link)
	return sub(r'.*data-src="', '', link)


def parsePrimeTimeTable(output, debug=None):
	startpos = output.find('<table class="primetime-table">')
	endpos = output.find('</table>')
	bereich = unescape(output[startpos:endpos])
	items = findall(r'<tr>(.*?)</tr>', bereich, S)
	entries = []
	for item in items:
		date = searchOneValue(r'<span>TV-Sendungen am (.*?)</span>', item, None, S)
		if date is not None:
			entries.append((date, None, None, None, None, None, None))
		else:
			LOGO = searchOneValue(r'<img\s*src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*).png"', item, None, S)
			START = searchOneValue(r'class="search\-starttimes">\s*<span>(.*?)</span>\s*\-\s*(.*?)\s*</div>', item, "00:00", S)
			LINK, TITLE = searchTwoValues(r'<h3><a\ href="(.*?)".*?title="(.*?)"', item, None, "{kein Titel gefunden}", S)
			GENRE = searchOneValue(r'<p>(.*?)\s*</p>', item, None, S)
			RATING = searchOneValue(r'<span class="editorial\-(.*?)">', item, None, S)
			entries.append((None, START, TITLE, GENRE, LOGO, LINK, RATING))
	if debug != None:
		print("[DEBUG] parsePrimeTimeTable %s\n" % debug)
		print(bereich)
	return entries, bereich


def parseTrailerUrl(output, videoformat='.mp4'):
	output = ensure_str(output)
	if search('https://video.tvspielfilm.de/.*?' + videoformat, output) is not None:
		trailerurl = search('https://video.tvspielfilm.de/(.*?)' + videoformat, output)
		return 'https://video.tvspielfilm.de/%s%s' % (trailerurl.group(1), videoformat) if trailerurl else None
	else:
		return


def buildTVTippsArray(sparte, output):
	startpos = 0
	endpos = 0
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
	bereich = unescape(bereich)
	items = findall(r'<li>(.*?)</li>', bereich, S)
	entries = []
	for item in items:
		LOGO = searchOneValue(r'<img src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*?).png.*?', item, None, S)
		TIME = searchOneValue(r'<span class="time">(.*?)</span>', item, None, S)
		LINK = searchOneValue(r'<div class="full-image image-wrapper.*?">\s*<a href="(.*?)"', item, None, S)
		NAME = searchOneValue(r'<strong>(.*?)</strong>', item, None, S)
		GENRE = searchOneValue(r'<span>(.*?)</span>', item, None, S)
		INFOS = searchOneValue(r'<span class="add-info (.*?)">', item, None, S)
		PIC = searchOneValue(r' data-src="(.*?)" ', item, None, S)
		if not PIC:
			PIC = searchOneValue(r'<img src="(.*?)" ', None, S)
		entries.append((LINK, PIC, TIME, INFOS, NAME, GENRE, LOGO))
	return entries


def parseNow(output):
	startpos = output.find('<table class="info-table"')
	endpos = output.find('<div class="block-in">')
	if endpos == -1:
		endpos = output.find('<div class="two-blocks">')
	bereich = unescape(output[startpos:endpos])
	items = findall('<tr class="hover">(.*?)</tr>', bereich, S)
	entries = []
	for item in items:
		LOGO = searchOneValue(r'<img\s*src="https://a2.tvspielfilm.de/images/tv/sender/mini/(.*?).png"', item, None, S)
		TIME = searchOneValue(r'<div>\s*<strong>(.*?)</strong>', item, "00:00", S)
		title = findall(r'link" title="(.*?)" data', item, S)
		title = title[-1] if title else "- keine Sendungsinformation gefunden -"
		genre = searchOneValue(r'<td class="col-4">\s*<span>(.*?)</span>', item, None, S)
		sparte = searchOneValue(r'<td class="col-5">\s*<span>(.*?)\s*</span>', item, "", S).replace('<br/>', '')
		if search('<em>', sparte):
			subsparte = searchOneValue(r'<em>(.*?)</em>', sparte, None)
			sparte = sub(r'<em>.*?</em>', '', sparte).rstrip()
			sparte = "%s\n%s" % (sparte, subsparte) if subsparte else sparte
		rating = searchOneValue(r'class="editorial\-(.*?)"', item, None, S)
		LINK = searchOneValue(r'<span>\s*<a href="(.*?)"', item, None, S)
		trailer = search(r'<span class="add-info icon-movieteaser"></span>', item, flags=S)
		entries.append((LOGO, TIME, LINK, title, sparte, genre, rating, trailer))
	return entries, output


def parseInfo(output):
	output = sub(r'</dl>.\n\\s+</div>.\n\\s+</section>', '</cast>', output)
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
	bereich = sub(r'" alt=".*?" width="', '" width="', bereich)
	picurl = search(r'<img src="(.*?)" data-src="(.*?)" width="', bereich)
	if picurl:
		print(picurl.group(2))


def testtvtipps(output):
	output = ensure_str(output)
	a = buildTVTippsArray("Serie", output)
	print(a)


def testtvnow(output):
	output = ensure_str(output)
	a = parsePrimeTimeTable(output, True)
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
	print(transCHANNEL("ServusTV Deutschland"))
	print(transCHANNEL("SAT.1 HD"))


if __name__ == '__main__':
	test()

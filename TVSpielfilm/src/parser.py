# -*- coding: utf-8 -*-
from re import sub, findall, S, search
from six import ensure_str
from twisted.internet import reactor
from xml.sax.saxutils import unescape

NEXTPage1 = r'class="js-track-link pagination__link pagination__link--next"'
NEXTPage2 = r'<a\ href="(.*?)"'


def shortenChannel(text):
	text = text.replace('ProSieben', 'Pro7').replace('EXTREME SPORTS', 'EXTREME').replace('NatGeo Wild', 'NatGeoWild').replace('Nat Geo Wild', 'NatGeoWild')
	text = text.replace("National Geographic", "NatGeo").replace("SRF 1", "SRF1").replace("SRF 2", "SRF2").replace("ATV 2", "ATV2")
	return text.rstrip()


def transCHANNEL(data):
	mapping = {r"das erste.*?": "ard",
			r"zdf_neo.*?": "2neo",
			r"zdfinfo.*?": "zinfo",
			r"zdf .*?": "zdf",
			r"tagesschau.*?": "tag24",
			r"phoenix.*?": "phoen",
			r"prosieben.*?fun.*?": "pro7f",
			r"prosieben.*?maxx.*?": "pro7m",
			r"prosieben.*?": "pro7",
			r"pro7.*?fun.*?": "pro7f",
			r"pro7.*?maxx.*?": "pro7m",
			r"sat.*?e.*?": "sat1e",
			r"sat.*?g.*?": "sat1g",
			r"sat.1.*?": "sat1",
			r"3sat.*?": "3sat",
			r"rtl c.*?": "rtl-c",
			r"rtl l.*?": "rtl-l",
			r"nitro.*?": "rtl-n",
			r"rtl n.*?": "rtl-n",
			r"rtln.*?": "rtl-n",
			r"rtl p.*?": "pass",
			r"rtlzwei.*?": "rtl2",
			r"rtl.*?2.*?": "rtl2",
			r"rtlup.*?": "rtlpl",
			r"super rtl.*?": "super",
			r"rtl .*?": "rtl",
			r"voxup.*?": "voxup",
			r"vox.*?": "vox",
			r"sixx.*?": "sixx",
			r"kabel.*? c.*?": "k1cla",
			r"kabel.*? d.*?": "k1doku",
			r"kabel.*?": "k1",
			r"n24 d.*?": "n24doku",
			r"n24 .*?": "welt",
			r"sky 1.*?": "sky1",
			r"sky one.*?": "sky1",
			r"sky .*?action.*?": "sky-a",
			r"sky .*?atlantic.*?": "skyat",
			r"sky .*?fun.*?": "sky-c",
			r"sky .*?special.*?": "skycs",
			r"sky .*?family.*?": "sky-f",
			r"sky .*?007.*?": "sky-h",
			r"sky .*?best of.*?": "sky-h",
			r"sky .*?nature.*?": "sky-na",
			r"sky .*?documentaries.*?": "sky-d",
			r"sky .*?star.*?": "sky-h",
			r"sky .*?krimi.*?": "sky-k",
			r"sky .*?crime.*?": "sky-cr",
			r"sky .*?classics.*?": "sky-n",
			r"sky .*?select.*?": "sky-s",
			r"sky .*?replay.*?": "skyrp",
			r"sky .*?premieren.*?24.*?": "cin24",
			r"sky .*?premieren.*?": "cin",
			r"sky .*?thriller.*?": "skyth",
			r"sky .*?special.*?": "skycs",
			r"sky .*?showcase.*?": "skysh",
			r"sky .*?xmas.*?": "xmas",
			r"sky .*?christmas.*?": "xmas",
			r"sky .*?comedy.*?": "sky-co",
			r"sky .*?sport.*? golf.*?": "skysg",
			r"sky .*?sport.*? mix.*?": "skysm",
			r"sky .*?sport.*? golf.*?": "skysg",
			r"sky .*?sport.*? top.*?event.*?": "skyste",
			r"sky .*?sport.*? premier.*?league.*?": "skyspl",
			r"sky .*?sport.*? tennis.*?": "skyst",
			r"sky .*?sport.*? f1.*?": "skyf1",
			r"sky .*?sport.*? austria.*?": "spo-a",
			r"sky .*?sport.*? hd 1.*?": "hdspo",
			r"sky .*?sport.*? 1.*?": "hdspo",
			r"sky .*?buli.*? bundesliga*?": "buli",
			r"sky .*?sport.*? hd 2.*?": "shd2",
			r"sky .*?sport.*? 2.*?": "shd2",
			r"sky .*?sport.*? news.*?": "snhd",
			r"sky .*?bundesliga.*?": "buli",
			r"eurosport 1.*?": "euro",
			r"eurosport 2.*?": "euro2",
			r"sport1\\+.*?": "s1plu",
			r"sport 1.*?": "sport",
			r"sport1.*?": "sport",
			r"dazn 2.*?": "dazn",
			r"esports1.*?": "es1",
			r"motorvision tv.*?": "movtv",
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
			r"bio channel": "bio",
			r"tele 5.*?": "tele5",
			r"anixe.*?": "anixe",
			r"13th.*?": "13th",
			r"axn.*?": "axn",
			r"silverline.*?": "silve",
			r"welt der wunder.*?": "wdwtv",
			r"arte.*?": "arte",
			r"ntv.*?": "ntv",
			r"cnn.*?": "cnn",
			r"bbc w.*?": "bbc",
			r"bbc e.*?": "bbc-e",
			r"dmax.*?": "dmax",
			r"spiegel .*?geschichte.*?": "sp-ge",
			r"spiegel .*?history.*?": "sp-ge",
			r"spiegel .*?wissen.*?": "sptvw",
			r"curiosity channel.*?": "sptvw",
			r"the history.*?": "hishd",
			r"history.*?": "hishd",
			r"animal planet.*?": "aplan",
			r"crime \\+ investigation.*?": "crin",  # Suchstrings zuerst mit re.escape wandeln (z.B. siehe hier '\\+' = '+')
			r"planet.*?": "plane",
			r"discovery.*?": "hddis",
			r"discovery channel.*?": "disco",
			r"natgeo wild.*?": "n-gw",
			r"natgeo.*?": "n-ghd",
			r"bon.*?gusto.*?": "gusto",
			r"servus.*?": "servu",
			r"one.*?": "fes",
			r"ard.*?alpha.*?": "alpha",
			r"srf1.*?": "sf1",
			r"srf.*?": "sf2",
			r"srf2.*?": "sf2",
			r"srf zwei.*?": "sf2",
			r"hamburg 1": "hh1",
			r"m.*?nchen2": "mue2",
			r"m.*?nchen.tv": "tvm",
			r"tv.berlin": "tvb",
			r"leipzig fernsehen.*?": "leitv",
			r"nrw.tv.*?": "nrwtv",
			r"rheinmain tv.*?": "rmtv",
			r"rnf.*?": "rnf",
			r"sachsen fernsehen.*?": "sach",
			r"orf 1.*?": "orf1",
			r"orf1.*?": "orf1",
			r"orf eins.*?": "orf1",
			r"orf 2.*?": "orf2",
			r"orf2.*?": "orf2",
			r"orf 3.*?": "orf3",
			r"orf iii.*?": "orf3",
			r"orf.sport.*?": "orfsp",
			r"sf1.*?": "sf1",
			r"sf 1.*?": "sf1",
			r"sf 2.*?": "sf2",
			r"sf zwei.*?": "sf2",
			r"atv2.*?": "atv2",
			r"atv ii.*?": "atv2",
			r"atv .*?": "atv",
			r"puls 4.*?": "puls4",
			r"boomerang.*?": "boom",
			r"nick jr.*?": "nickj",
			r"nick.*?": "nick",
			r"nicktoons.*?": "nickt",
			r"comedy central.*?": "cc",
			r"cartoonnet.*?": "c-net",
			r"cartoon net.*?": "c-net",
			r"disney cinema.*?": "dcm",
			r"disney channel.*?": "disne",
			r"disney junior.*?": "djun",
			r"disney xd.*?": "dxd",
			r"disney hd": "disne",
			r"junior.*?": "junio",
			r"kika.*?": "kika",
			r"vh1.*?classic.*?": "vh1",
			r"deluxe music.*?": "dmc",
			r"mtv": "mtv",
			r"mtv hd": "mtv",
			r"mtv g.*?": "mtv",
			r"mtv ba.*?": "mtv-b",
			r"mtv da.*?.*?": "mtv-d",
			r"club mtv.*?": "mtv-d",
			r"mtv hi.*?.*?": "mtv-h",
			r"mtv li.*?": "mtv-l",
			r"viva.*?": "viva",
			r"im1": "imt",
			r"rock tv.*?": "rck",
			r"jukebox.*?": "juke",
			r"trace.*?": "trace",
			r"classica.*?": "class",
			r"gute laune.*?": "laune",
			r"beate uhse.*?": "butv",
			r"lust pur.*?": "lustp",
			r"playboy tv": "pboy",
			r"al jazeera.*?": "aljaz",
			r"bloomberg.*?": "blm",
			r"euronews.*?": "euron",
			r"bibel tv.*?": "bibel",
			r"kirchen tv.*?": "ktv",
			r"timm.*?": "timm",
			r"sonnenklar.*?": "sklar",
			r"goldstar tv": "gold",
			r"animax": "amax",
			r"adult channel.*?": "adult",
			r"das neue tv.*?": "dntv",
			r"deutsches wetter.*?": "dwf",
			r"e!.*?": "e!",
			r"fashion tv.*?": "fatv",
			r"family tv.*?": "famtv",
			r"mezzo.*?": "mezzo",
			r"nautical.*?": "nauch",
			r"nl 1.*?": "nl1",
			r"nl 2.*?": "nl2",
			r"nl 3.*?": "nl3",
			r"dr1.*?": "dr1",
			r"belgien.*?": "be1",
			r"france24.*?fr.*?": "fr24f",
			r"france24.*?en.*?": "fr24e",
			r"france 2.*?": "fra2",
			r"france 3.*?": "fra3",
			r"france 5.*?": "fra5",
			r"tv 2.*?": "tv5",
			r"tv 5.*?": "tv5",
			r"ric.*?": "ric",
			r"tlc.*?": "tlc",
			r"star tv.*?": "sttv",
			r"center.tv.*?": "cente",
			r"sony.*?": "sony",
			r"3 plus.*?": "3plus",
			r"3\\+.*?": "3plus",
			r"marco polo.*?": "mapo",
			r"travel channel.*?": "trch",
			r"home.*?garden.*?": "hgtv",
			r"hgtv.*?": "hgtv",
			r"channel21.*?": "ch21",
			r"geo television.*?": "geo",
			r"geo tv.*?": "geo",
			r"fix.*?foxi.*?": "fftv",
			r"welt.*?": "welt",
			r"uhd1.*?": "uhd1",
			r"dw .*?": "dwtv",
			r"deutsches musik fernsehen.*?": "dmf",
			r"rbb .*?": "rbb",
			r"ndr .*?": "n3",
			r"mdr .*?": "mdr",
			r"wdr .*?": "wdr",
			r"hr .*?": "hr",
			r"hr-fernsehen.*?": "hr",
			r"swr .*?": "swr",
			r"sr fernsehen.*?": "swr",
			r"br.*?": "br",
			r"bayerisches.*?": "br",
			r"bild.*?": "bild",
			r"warner .*?comedy.*?": "tnt-c",
			r"warner .*?film.*?": "tnt-f",
			r"warner .*?serie.*?": "tnt-s",
			r"tnt .*?comedy.*?": "tnt-c",
			r"tnt .*?film.*?": "tnt-f",
			r"tnt .*?serie.*?": "tnt-s",
			r"hse .*?": "hse",
			r"qvc.*?": "qvc",
			r"health.*?": "health"
			}
	supported = ''
	unsupported = ''
	for item in data.strip().split("\n"):
		sref = search(r" \d+:\d+:\w+:\w+:\w+:\w+:\w+:\d+:\w+:\w+:.*", item)
		name = item[:sref.start(0)].strip().lower() if sref else item.lower()
		sref = item[sref.start(0):].strip() if sref else ""
		for pattern, shortcut in mapping.items():  # Sendernamen in Kürzel austauschen
			if search(pattern, name):
				name = name.replace(name, shortcut)
				break
		if name in list(mapping.values()):
			supported += "%s %s\n" % (name, sref)
		else:
			unsupported += "%s %s\n" % (name, sref)
	return supported.rstrip(), unsupported.rstrip()


def searchOneValue(regex, text, fallback, flags=None):
	text = search(regex, text) if flags is None else search(regex, text, flags=flags)
	return text.group(1) if text else fallback


def searchTwoValues(regex, text, fallback1, fallback2, flags=None):
	text = search(regex, text) if flags is None else search(regex, text, flags=flags)
	return (text.group(1), text.group(2)) if text else (fallback1, fallback2)


def parsedetail(bereich, debug=None):
	quelle = search(r'content-rating__rating-genre__title">(.*?)</div>', bereich)
	quelle = quelle.group(1) if quelle else ""
	bewertung = search(r'content-rating__rating-genre__conclusion-quote">\s*<p>(.*?)</p>', bereich, flags=S)
	bewertung = bewertung.group(1) if bewertung else "{keine Bewertung gefunden}"
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
	datalong = """Das Erste HD 1:0:19:283D:41B:1:FFFF0000:0:0:0:
ZDF HD 1:0:19:2B66:437:1:FFFF0000:0:0:0:
SAT.1 HD 1:0:19:C362:2723:F001:FFFF0000:0:0:0:
SAT.1 Gold HD 1:0:19:C39A:2724:F001:FFFF0000:0:0:0:
ServusTV HD 1:0:19:C365:2716:F001:FFFF0000:0:0:0:
unbekannt hd 1:0:19:CBCB:432:1:FFFF0000:0:0:0:"""

	datashort = """Das Erste
ZDF HD
SAT.1 HD
SAT.1 Gold HD
ServusTV HD
unbekannt hd"""

	results = transCHANNEL(datalong)
	print(results[0])  # [0] = supported services
	print("-----------------------------------------------")
	print(results[1])  # [1] = unsupported services


if __name__ == '__main__':
	test()

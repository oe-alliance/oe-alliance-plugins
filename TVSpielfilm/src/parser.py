#!/usr/bin/python
# -*- coding: utf-8 -*-
from re import sub, findall, S as RES, search
from six import ensure_str
from twisted.internet import reactor

NEXTPage1 = 'class="js-track-link pagination__link pagination__link--next"'
NEXTPage2 = '<a href="(.*?)"\n\\s+class="js-track-link pagination__link pagination__link--next"'


def shortenChannel(text):
	text = text.replace('ProSieben ', 'Pro7 ').replace('kabel eins CLASSICS', 'k1CLASSICS').replace('Sky Family', 'SkyFamily').replace('Sky Cinema+', 'SkyCine+')
	text = text.replace('Sky Comedy', 'SkyComedy').replace('Sky Emotion', 'SkyEmotion').replace('Sky Sport HD', 'SkySport').replace('Eurosport ', 'Eurosport')
	text = text.replace('EXTREME SPORTS', 'EXTREME').replace('NAT GEO WILD', 'NatGeoWild').replace('Romance TV', 'RomanceTV').replace('13th Street', '13thStreet')
	text = text.replace('VH1 Classic', 'VH1Classic').replace('COMEDY CENTRAL', 'COMEDY C').replace('Cartoon Network', 'CartoonNet')
	text = text.replace('Disney Cinemagic', 'DisneyCine').replace('HISTORY HD', 'History HD').replace('DELUXE MUSIC', 'DeluxMusic')
	return text


def transWIKI(text):
	text = text.replace('\xc3\x84', '\xc4').replace('\xc3\x96', '\xd6').replace('\xc3\x9c', '\xdc').replace('\xc3\x9f', '\xdf').replace(
		'\xc3\xa4', '\xe4').replace('\xc3\xb6', '\xf6').replace('\xc3\xbc', '\xfc').replace('&', '%26').replace('\xe2\x80', '-')
	return text


def transHTML(text):
	text = text.replace('&nbsp;', ' ').replace('&szlig;', 'ß').replace('&quot;', '"').replace('&ndash;', '-').replace('&Oslash;', '').replace('&bdquo;', '"')
	text = text.replace('&ldquo;', '"').replace('&rsquo;', "'").replace('&gt;', '>').replace('&lt;', '<').replace('&shy;', '').replace('&copy;.*', ' ')
	text = text.replace('&copy;', '').replace('&amp;', '&').replace('&uuml;', 'ü').replace('&auml;', 'ä').replace('&ouml;', 'ö')
	text = text.replace('&eacute;', 'é').replace('&hellip;', '...').replace('&egrave;', 'è').replace('&agrave;', 'à').replace('&aacute;', 'á').replace('&mdash;', '-')
	text = text.replace('&Uuml;', 'Ü').replace('&Auml;', 'Ä').replace('&Ouml;', 'Ö').replace('&#034;', '"').replace('&#039;', "'").replace('&#34;', '"')
	text = text.replace('&#38;', 'und').replace('&#39;', "'").replace('&#133;', '...').replace('&#196;', 'Ä').replace('&#214;', 'Ö')
	text = text.replace('&#223;', 'ß').replace('&#228;', 'ä').replace('&#246;', 'ö').replace('&#220;', 'Ü').replace('&#252;', 'ü')
	text = text.replace('&#287;', 'c').replace('&#324;', 'n').replace('&#351;', 's').replace('&#8211;', '-').replace('&#8212;', '\x97').replace('&#8216;', "'")
	text = text.replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"').replace('&#8230;', '...').replace('&#8242;', "'").replace('&#8243;', '"')
	return text


def transCHANNEL(data):
	neu = ''
	for x in data.split('\n'):
		sref = search(' \d+:\d+:\w+:\w+:\w+:\w+:\w+:\d+:\w+:\w+:.*', x)
		if sref is None:
			neu += x.lower() + '\t\n'
		else:
			neu += x[:sref.start(0)].lower() + '\t' + sref.group(0) + '\n'
	data = neu
	data = sub('das erste.*?\t', 'ard', data)
	data = sub('zdf_neo.*?\t', '2neo', data)
	data = sub('zdfinfo.*?\t', 'zinfo', data)
	data = sub('zdf.*?\t', 'zdf', data)
	data = sub('tagesschau.*?\t', 'tag24', data)
	data = sub('3sat.*?\t', '3sat', data)
	data = sub('phoenix.*?\t', 'phoen', data)
	data = sub('pro.*?fun.*?\t', 'pro7f', data)
	data = sub('pro.*?maxx.*?\t', 'pro7m', data)
	data = sub('pro.*?\t', 'pro7', data)
	data = sub('sat.*?e.*?\t', 'sat1e', data)
	data = sub('sat.*?g.*?\t', 'sat1g', data)
	data = sub('sat.*?\t', 'sat1', data)
	data = sub('rtl c.*?\t', 'rtl-c', data)
	data = sub('rtl l.*?\t', 'rtl-l', data)
	data = sub('nitro.*?\t', 'rtl-n', data)
	data = sub('rtl n.*?\t', 'rtl-n', data)
	data = sub('rtln.*?\t', 'rtl-n', data)
	data = sub('rtl p.*?\t', 'pass', data)
	data = sub('rtlzwei.*?\t', 'rtl2', data)
	data = sub('rtl.*?2.*?\t', 'rtl2', data)
	data = sub('rtlup.*?\t', 'rtlpl', data)
	data = sub('super rtl.*?\t', 'super', data)
	data = sub('rtl.*?\t', 'rtl', data)
	data = sub('voxup.*?\t', 'voxup', data)
	data = sub('vox.*?\t', 'vox', data)
	data = sub('sixx.*?\t', 'sixx', data)
	data = sub('kabel.*? c.*?\t', 'k1cla', data)
	data = sub('kabel.*? d.*?\t', 'k1doku', data)
	data = sub('kabel.*?\t', 'k1', data)
	data = sub('sky 1.*?\t', 'sky1', data)
	data = sub('sky one.*?\t', 'sky1', data)
	data = sub('sky .*?action.*?\t', 'sky-a', data)
	data = sub('sky .*?atlantic.*?\t', 'skyat', data)
	data = sub('sky .*?fun.*?\t', 'sky-c', data)
	data = sub('sky .*?special.*?\t', 'skycs', data)
	data = sub('sky .*?family.*?\t', 'sky-f', data)
	data = sub('sky .*?007.*?\t', 'sky-h', data)
	data = sub('sky .*?best of.*?\t', 'sky-h', data)
	data = sub('sky .*?nature.*?\t', 'sky-na', data)
	data = sub('sky .*?documentaries.*?\t', 'sky-d', data)
	data = sub('sky .*?star.*?\t', 'sky-h', data)
	data = sub('sky .*?krimi.*?\t', 'sky-k', data)
	data = sub('sky .*?classics.*?\t', 'sky-n', data)
	data = sub('sky .*?select.*?\t', 'sky-s', data)
	data = sub('sky .*?premieren.*?24.*?\t', 'cin24', data)
	data = sub('sky .*?premieren.*?\t', 'cin', data)
	data = sub('sky .*?thriller.*?\t', 'skyth', data)
	data = sub('sky .*?special.*?\t', 'skycs', data)
	data = sub('sky .*?xmas.*?\t', 'xmas', data)
	data = sub('sky .*?christmas.*?\t', 'xmas', data)
	data = sub('sky .*?comedy.*?\t', 'sky-co', data)
	data = sub('sky .*?sport.*? golf.*?\t', 'skysg', data)
	data = sub('sky .*?sport.*? mix.*?\t', 'skysm', data)
	data = sub('sky .*?sport.*? golf.*?\t', 'skysg', data)
	data = sub('sky .*?sport.*? top.*?event.*?\t', 'skyste', data)
	data = sub('sky .*?sport.*? premier.*?league.*?\t', 'skyspl', data)
	data = sub('sky .*?sport.*? tennis.*?\t', 'skyst', data)
	data = sub('sky .*?sport.*? f1.*?\t', 'skyf1', data)
	data = sub('sky .*?sport.*? austria.*?\t', 'spo-a', data)
	data = sub('sky .*?sport.*? hd 1.*?\t', 'hdspo', data)
	data = sub('sky .*?sport.*? 1.*?\t', 'hdspo', data)
	data = sub('sky .*?buli.*? bundesliga*?\t', 'buli', data)
	data = sub('sky .*?sport.*? hd 2.*?\t', 'shd2', data)
	data = sub('sky .*?sport.*? 2.*?\t', 'shd2', data)
	data = sub('sky .*?sport.*? news.*?\t', 'snhd', data)
	data = sub('sky .*?bundesliga.*?\t', 'buli', data)
	data = sub('sky.bundesliga.*?\t', 'buli', data)
	data = sub('bundesliga.*?\t', 'buli', data)
	data = sub('sky. bundesliga.*?\t', 'buli', data)
	data = sub('eurosport 1.*?\t', 'euro', data)
	data = sub('eurosport 2.*?\t', 'euro2', data)
	data = sub('sport1\\+.*?\t', 's1plu', data)
	data = sub('sport1.*?\t', 'sport', data)
	data = sub('sport 1.*?\t', 'sport', data)
	data = sub('dazn 2.*?\t', 'dazn', data)
	data = sub('esports1.*?\t', 'es1', data)
	data = sub('motorvision tv.*?\t', 'movtv', data)
	data = sub('auto.*?motor.*?sport.*?\t', 'ams', data)
	data = sub('sportdigital.*?fussball.*?\t', 'spo-d', data)
	data = sub('magenta.*?sport.*?\t', 'maspo', data)
	data = sub('extreme.*? sports.*?\t', 'ex-sp', data)
	data = sub('kinowelt.*?\t', 'kinow', data)
	data = sub('fox.*?\t', 'fox', data)
	data = sub('syfy.*?\t', 'scifi', data)
	data = sub('universal.*?\t', 'unive', data)
	data = sub('toggo.*?\t', 'toggo', data)
	data = sub('romance tv.*?\t', 'rom', data)
	data = sub('heimatkanal.*?\t', 'heima', data)
	data = sub('biography.*?\t', 'bio', data)
	data = sub('bio channel\t', 'bio', data)
	data = sub('tele 5.*?\t', 'tele5', data)
	data = sub('anixe.*?\t', 'anixe', data)
	data = sub('13th.*?\t', '13th', data)
	data = sub('axn.*?\t', 'axn', data)
	data = sub('silverline.*?\t', 'silve', data)
	data = sub('welt der wunder.*?\t', 'wdwtv', data)
	data = sub('arte.*?\t', 'arte', data)
	data = sub('ntv.*?\t', 'ntv', data)
	data = sub('n24 d.*?\t', 'n24doku', data)
	data = sub('n24.*?\t', 'welt', data)
	data = sub('cnn.*?\t', 'cnn', data)
	data = sub('bbc w.*?\t', 'bbc', data)
	data = sub('bbc e.*?\t', 'bbc-e', data)
	data = sub('dmax.*?\t', 'dmax', data)
	data = sub('spiegel .*?geschichte.*?\t', 'sp-ge', data)
	data = sub('spiegel .*?history.*?\t', 'sp-ge', data)
	data = sub('spiegel .*?wissen.*?\t', 'sptvw', data)
	data = sub('curiosity channel.*?\t', 'sptvw', data)
	data = sub('the history.*?\t', 'hishd', data)
	data = sub('history.*?\t', 'hishd', data)
	data = sub('animal planet.*?\t', 'aplan', data)
	data = sub('crime \\+ investigation.*?\t', 'crin', data)
	data = sub('planet.*?\t', 'plane', data)
	data = sub('discovery.*?\t', 'hddis', data)
	data = sub('discovery channel.*?\t', 'disco', data)
	data = sub('natgeo wild.*?\t', 'n-gw', data)
	data = sub('nat geo wild.*?\t', 'n-gw', data)
	data = sub('natgeo people.*?\t', 'n-gp', data)
	data = sub('nat geo people.*?\t', 'n-gp', data)
	data = sub('natgeo.*?\t', 'n-ghd', data)
	data = sub('nat geo.*?\t', 'n-ghd', data)
	data = sub('national geographic.*?\t', 'n-ghd', data)
	data = sub('bongusto.*?\t', 'gusto', data)
	data = sub('bon gusto.*?\t', 'gusto', data)
	data = sub('servus.*?\t', 'servu', data)
	data = sub('sr fernsehen.*?\t', 'swr', data)
	data = sub('bayerisches.*?\t', 'br', data)
	data = sub('br m.*?\t', 'br', data)
	data = sub('br n.*?\t', 'br', data)
	data = sub('br s.*?\t', 'br', data)
	data = sub('br fern.*?\t', 'br', data)
	data = sub('one.*?\t', 'fes', data)
	data = sub('ard alpha.*?\t', 'alpha', data)
	data = sub('ard-alpha.*?\t', 'alpha', data)
	data = sub('srf1.*?\t', 'sf1', data)
	data = sub('srf 1.*?\t', 'sf1', data)
	data = sub('srf.*?\t', 'sf2', data)
	data = sub('srf2.*?\t', 'sf2', data)
	data = sub('srf 2.*?\t', 'sf2', data)
	data = sub('srf zwei.*?\t', 'sf2', data)
	data = sub('hamburg 1\t', 'hh1', data)
	data = sub('m.*?nchen2\t', 'mue2', data)
	data = sub('m.*?nchen.tv\t', 'tvm', data)
	data = sub('tv.berlin\t', 'tvb', data)
	data = sub('leipzig fernsehen.*?\t', 'leitv', data)
	data = sub('nrw.tv.*?\t', 'nrwtv', data)
	data = sub('rheinmain tv.*?\t', 'rmtv', data)
	data = sub('rnf.*?\t', 'rnf', data)
	data = sub('sachsen fernsehen.*?\t', 'sach', data)
	data = sub('orf 1.*?\t', 'orf1', data)
	data = sub('orf1.*?\t', 'orf1', data)
	data = sub('orf eins.*?\t', 'orf1', data)
	data = sub('orf 2.*?\t', 'orf2', data)
	data = sub('orf2.*?\t', 'orf2', data)
	data = sub('orf 3.*?\t', 'orf3', data)
	data = sub('orf.sport.*?\t', 'orfsp', data)
	data = sub('orf.*?\t', 'orf1', data)
	data = sub('sf1.*?\t', 'sf1', data)
	data = sub('sf 1.*?\t', 'sf1', data)
	data = sub('sf 2.*?\t', 'sf2', data)
	data = sub('sf zwei.*?\t', 'sf2', data)
	data = sub('atv\t', 'atv', data)
	data = sub('atv hd\t', 'atv', data)
	data = sub('atv2.*?\t', 'atv2', data)
	data = sub('atv 2.*?\t', 'atv2', data)
	data = sub('atv ii\t', 'atv2', data)
	data = sub('puls 4.*?\t', 'puls4', data)
	data = sub('boomerang.*?\t', 'boom', data)
	data = sub('nick jr.*?\t', 'nickj', data)
	data = sub('nick.*?\t', 'nick', data)
	data = sub('nicktoons.*?\t', 'nickt', data)
	data = sub('comedy central.*?\t', 'cc', data)
	data = sub('cartoon net.*?\t', 'c-net', data)
	data = sub('disney cinema.*?\t', 'dcm', data)
	data = sub('disney channel.*?\t', 'disne', data)
	data = sub('disney junior.*?\t', 'djun', data)
	data = sub('disney xd.*?\t', 'dxd', data)
	data = sub('disney hd\t', 'disne', data)
	data = sub('junior.*?\t', 'junio', data)
	data = sub('kika.*?\t', 'kika', data)
	data = sub('vh1 classic.*?\t', 'vh1', data)
	data = sub('deluxe music.*?\t', 'dmc', data)
	data = sub('mtv\t', 'mtv', data)
	data = sub('mtv hd\t', 'mtv', data)
	data = sub('mtv g.*?\t', 'mtv', data)
	data = sub('mtv ba.*?\t', 'mtv-b', data)
	data = sub('mtv da.*?.*?\t', 'mtv-d', data)
	data = sub('mtv hi.*?.*?\t', 'mtv-h', data)
	data = sub('mtv li.*?\t', 'mtv-l', data)
	data = sub('viva.*?\t', 'viva', data)
	data = sub('im1\t', 'imt', data)
	data = sub('rock tv.*?\t', 'rck', data)
	data = sub('jukebox.*?\t', 'juke', data)
	data = sub('trace.*?\t', 'trace', data)
	data = sub('classica.*?\t', 'class', data)
	data = sub('gute laune.*?\t', 'laune', data)
	data = sub('beate-uhse.*?\t', 'butv', data)
	data = sub('lust pur.*?\t', 'lustp', data)
	data = sub('playboy tv\t', 'pboy', data)
	data = sub('al jazeera.*?\t', 'aljaz', data)
	data = sub('bloomberg.*?\t', 'blm', data)
	data = sub('euronews.*?\t', 'euron', data)
	data = sub('bibel tv.*?\t', 'bibel', data)
	data = sub('kirchen tv.*?\t', 'ktv', data)
	data = sub('timm.*?\t', 'timm', data)
	data = sub('sonnenklar.*?\t', 'sklar', data)
	data = sub('goldstar tv\t', 'gold', data)
	data = sub('animax\t', 'amax', data)
	data = sub('adult channel.*?\t', 'adult', data)
	data = sub('das neue tv.*?\t', 'dntv', data)
	data = sub('deutsches wetter.*?\t', 'dwf', data)
	data = sub('e!.*?\t', 'e!', data)
	data = sub('fashion tv.*?\t', 'fatv', data)
	data = sub('family tv.*?\t', 'famtv', data)
	data = sub('mezzo.*?\t', 'mezzo', data)
	data = sub('nautical.*?\t', 'nauch', data)
	data = sub('nl 1.*?\t', 'nl1', data)
	data = sub('nl 2.*?\t', 'nl2', data)
	data = sub('nl 3.*?\t', 'nl3', data)
	data = sub('dr1.*?\t', 'dr1', data)
	data = sub('belgien.*?\t', 'be1', data)
	data = sub('france24.*?fr.*?\t', 'fr24f', data)
	data = sub('france24.*?en.*?\t', 'fr24e', data)
	data = sub('france 2.*?\t', 'fra2', data)
	data = sub('france 3.*?\t', 'fra3', data)
	data = sub('france 5.*?\t', 'fra5', data)
	data = sub('tv 2.*?\t', 'tv5', data)
	data = sub('tv 5.*?\t', 'tv5', data)
	data = sub('ric.*?\t', 'ric', data)
	data = sub('tlc.*?\t', 'tlc', data)
	data = sub('star tv.*?\t', 'sttv', data)
	data = sub('center.tv.*?\t', 'cente', data)
	data = sub('sony.*?\t', 'sony', data)
	data = sub('3 plus.*?\t', '3plus', data)
	data = sub('3\\+.*?\t', '3plus', data)
	data = sub('marco polo.*?\t', 'mapo', data)
	data = sub('travel channel.*?\t', 'trch', data)
	data = sub('home.*?garden.*?\t', 'hgtv', data)
	data = sub('channel21.*?\t', 'ch21', data)
	data = sub('geo television.*?\t', 'geo', data)
	data = sub('geo tv.*?\t', 'geo', data)
	data = sub('fix.*?foxi.*?\t', 'fftv', data)
	data = sub('welt.*?\t', 'welt', data)
	data = sub('uhd1.*?\t', 'uhd1', data)
	data = sub('dw.*?\t', 'dwtv', data)
	data = sub('deutsches musik fernsehen.*?\t', 'dmf', data)
	data = sub('rbb.*?\t', 'rbb', data)
	data = sub('ndr.*?\t', 'n3', data)
	data = sub('mdr.*?\t', 'mdr', data)
	data = sub('wdr.*?\t', 'wdr', data)
	data = sub('hr.*?\t', 'hr', data)
	data = sub('swr.*?\t', 'swr', data)
	data = sub('br.*?\t', 'swr', data)
	data = sub('tele 5.*?\t', 'TELE5', data)
	data = sub('bild hd\t', 'bild', data)
	data = sub('warner .*?comedy.*?\t', 'tnt-c', data)
	data = sub('warner .*?film.*?\t', 'tnt-f', data)
	data = sub('warner .*?serie.*?\t', 'tnt-s', data)
	data = sub('tnt .*?comedy.*?\t', 'tnt-c', data)
	data = sub('tnt .*?film.*?\t', 'tnt-f', data)
	data = sub('tnt .*?serie.*?\t', 'tnt-s', data)
	data = sub('hse.*?\t', 'hse', data)
	data = sub('qvc.*?\t', 'qvc', data)
	return data


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
	bereich = output[startpos:endpos]
	bereich = transHTML(bereich)
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
	bereich = output[startpos:endpos]
	output = transHTML(bereich)
	items = findall('<tr class="hover">(.*?)</tr>', output, RES)
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
	# from twisted.web.client import getPage
	#    link = b'https://www.tvspielfilm.de/tv-tipps/'
	link = b'https://www.tvspielfilm.de/tv-programm/sendungen/jetzt.html'
#    link = b'https://www.tvspielfilm.de/tv-programm/sendungen/?page=1&order=time&date=2021-05-06&tips=0&time=day&channel=3SAT'
#    link = b'https://www.tvspielfilm.de/suche/tvs-suche,,ApplicationSearch.html?tab=TV-Sendungen&ext=1&q=&cat%5B0%5D=SP&genreSP=Abenteuer&time=day&date=&channel='
#    link = b'https://www.tvspielfilm.de/tv-programm/sendungen/?page=1&order=time&date=2021-05-07&tips=0&time=day&channel=ARD'
#    link = b'https://www.tvspielfilm.de/tv-programm/sendungen/abends.html'
	link = b'https://www.tvspielfilm.de/tv-programm/sendung/wasserball,60f06a338189652e9978032c.html'
#    getPage(link).addCallback(savefile).addErrback(saveerr)
#    reactor.run()
	output = open('tmp.html', 'rb').read()
#    testtvsuche(output)
#    testparseNow(output)
#    testparseNow(output)
	testparseInfo(output)


if __name__ == '__main__':
	test()

#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from six import ensure_str
from re import sub, findall, S as RES, search
from twisted.web.client import getPage
from twisted.internet import reactor
import sys

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
        if x:
            name, sref = x.strip().split(',')
            neu += name.lower() + ',' + sref + '\n'
    data = neu
    data = sub('das erste.*?,', 'ard', data)
    data = sub('zdf_neo.*?,', '2neo', data)
    data = sub('zdf neo.*?,', '2neo', data)
    data = sub('zdfinfo.*?,', 'zinfo', data)
    data = sub('zdf.*?,', 'zdf', data)
    data = sub('tagesschau.*?,', 'tag24', data)
    data = sub('3sat.*?,', '3sat', data)
    data = sub('phoenix.*?,', 'phoen', data)
    data = sub('pro.*?fun.*?,', 'pro7f', data)
    data = sub('pro.*?maxx.*?,', 'pro7m', data)
    data = sub('pro.*?,', 'pro7', data)
    data = sub('sat.*?e.*?,', 'sat1e', data)
    data = sub('sat.*?g.*?,', 'sat1g', data)
    data = sub('sat.*?,', 'sat1', data)
    data = sub('rtl c.*?,', 'rtl-c', data)
    data = sub('rtl l.*?,', 'rtl-l', data)
    data = sub('nitro.*?,', 'rtl-n', data)
    data = sub('rtl n.*?,', 'rtl-n', data)
    data = sub('rtln.*?,', 'rtl-n', data)
    data = sub('rtl p.*?,', 'pass', data)
    data = sub('rtlzwei.*?,', 'rtl2', data)
    data = sub('rtlup.*?,', 'rtlpl', data)
    data = sub('super rtl.*?,', 'super', data)
    data = sub('rtl.*?,', 'rtl', data)
    data = sub('vox.*?,', 'vox', data)
    data = sub('sixx.*?,', 'sixx', data)
    data = sub('kabel.*? c.*?,', 'k1cla', data)
    data = sub('kabel.*? d.*?,', 'k1doku', data)
    data = sub('kabel.*?,', 'k1', data)
    data = sub('sky 1.*?,', 'sky1', data)
    data = sub('sky one.*?,', 'sky1', data)
    data = sub('sky .*?action.*?,', 'sky-a', data)
    data = sub('sky .*?atlantic.*?,', 'skyat', data)
    data = sub('sky .*?fun.*?,', 'sky-c', data)
    data = sub('sky .*?special.*?,', 'skycs', data)
    data = sub('sky .*?family.*?,', 'sky-f', data)
    data = sub('sky .*?007.*?,', 'sky-h', data)
    data = sub('sky .*?best of.*?,', 'sky-h', data)
    data = sub('sky .*?star.*?,', 'sky-h', data)
    data = sub('sky .*?krimi.*?,', 'sky-k', data)
    data = sub('sky .*?classics.*?,', 'sky-n', data)
    data = sub('sky .*?select.*?,', 'sky-s', data)
    data = sub('sky .*?premieren.*?24.*?,', 'cin24', data)
    data = sub('sky .*?premieren.*?,', 'cin', data)
    data = sub('sky .*?thriller.*?,', 'skyth', data)
    data = sub('sky .*?special.*?,', 'skycs', data)
    data = sub('sky .*?xmas.*?,', 'xmas', data)
    data = sub('sky .*?christmas.*?,', 'xmas', data)
    data = sub('sky bundesliga.*?,', 'buli', data)
    data = sub('sky comedy.*?,', 'sky-co', data)
    data = sub('sky sport news.*?,', 'snhd', data)
    data = sub('sky sport hd,', 'snhd', data)
    data = sub('sky sport hd 1,', 'hdspo', data)
    data = sub('sky sport 1 hd,', 'hdspo', data)
    data = sub('sky sport hd 2,', 'shd2', data)
    data = sub('sky sport 2 hd,', 'shd2', data)
    data = sub('sky sport 1,', 'spo1', data)
    data = sub('sky sport 2,', 'spo2', data)
    data = sub('sky sport austria.*?,', 'spo-a', data)
    data = sub('sky,*?,', 'sky', data)
    data = sub('sport.*?[+].*?,', 's1plu', data)
    data = sub('sport.*?,', 'sport', data)
    data = sub('sport.*?us.*?,', 'sp1us', data)
    data = sub('one.*?,', 'fes', data)
    data = sub('eurosport 2.*?,', 'euro2', data)
    data = sub('eurosport .*?,', 'euro', data)
    data = sub('espn america.*?,', 'nasn', data)
    data = sub('espn classic.*?,', 'espn', data)
    data = sub('motors tv.*?,', 'motor', data)
    data = sub('motorvision tv.*?,', 'movtv', data)
    data = sub('sportdigital.*?,', 'spo-d', data)
    data = sub('extreme sports.*?,', 'ex-sp', data)
    data = sub('kinowelt.*?,', 'kinow', data)
    data = sub('fox.*?,', 'fox', data)
    data = sub('syfy.*?,', 'scifi', data)
    data = sub('universal.*?,', 'unive', data)
    data = sub('toggo.*?,', 'toggo', data)
    data = sub('romance tv.*?,', 'rom', data)
    data = sub('heimatkanal.*?,', 'heima', data)
    data = sub('biography.*?,', 'bio', data)
    data = sub('bio channel,', 'bio', data)
    data = sub('tele 5.*?,', 'tele5', data)
    data = sub('anixe.*?,', 'anixe', data)
    data = sub('13th.*?,', '13th', data)
    data = sub('axn.*?,', 'axn', data)
    data = sub('silverline.*?,', 'silve', data)
    data = sub('welt der wunder.*?,', 'wdwtv', data)
    data = sub('arte.*?,', 'arte', data)
    data = sub('ntv.*?,', 'ntv', data)
    data = sub('n24 d.*?,', 'n24doku', data)
    data = sub('n24.*?,', 'welt', data)
    data = sub('welt.*?,', 'welt', data)
    data = sub('cnn.*?,', 'cnn', data)
    data = sub('bbc w.*?,', 'bbc', data)
    data = sub('bbc e.*?,', 'bbc-e', data)
    data = sub('dmax.*?,', 'dmax', data)
    data = sub('spiegel .*? geschichte.*?,', 'sp-ge', data)
    data = sub('spiegel .*? history.*?,', 'sp-ge', data)
    data = sub('spiegel .*? wissen.*?,', 'sptvw', data)
    data = sub('the history.*?,', 'hishd', data)
    data = sub('animal planet.*?,', 'aplan', data)
    data = sub('planet.*?,', 'plane', data)
    data = sub('discovery.*?,', 'hddis', data)
    data = sub('discovery channel.*?,', 'disco', data)
    data = sub('natgeo wild.*?,', 'n-gw', data)
    data = sub('nat geo wild.*?,', 'n-gw', data)
    data = sub('natgeo people.*?,', 'n-gp', data)
    data = sub('nat geo people.*?,', 'n-gp', data)
    data = sub('natgeo.*?,', 'n-ghd', data)
    data = sub('nat geo.*?,', 'n-ghd', data)
    data = sub('national geographic.*?,', 'n-geo', data)
    data = sub('bongusto.*?,', 'gusto', data)
    data = sub('bon gusto.*?,', 'gusto', data)
    data = sub('servus.*?,', 'servu', data)
    data = sub('sr fernsehen.*?,', 'swr', data)
    data = sub('bayerisches.*?,', 'br', data)
    data = sub('br m.*?,', 'br', data)
    data = sub('br n.*?,', 'br', data)
    data = sub('br s.*?,', 'br', data)
    data = sub('br fern.*?,', 'br', data)
    data = sub('ard alpha.*?,', 'alpha', data)
    data = sub('srf1.*?,', 'sf1', data)
    data = sub('srf 1.*?,', 'sf1', data)
    data = sub('srf.*?,', 'sf2', data)
    data = sub('srf2.*?,', 'sf2', data)
    data = sub('srf 2.*?,', 'sf2', data)
    data = sub('srf zwei.*?,', 'sf2', data)
    data = sub('hamburg 1,', 'hh1', data)
    data = sub('m.*?nchen2,', 'mue2', data)
    data = sub('m.*?nchen.tv,', 'tvm', data)
    data = sub('tv.berlin,', 'tvb', data)
    data = sub('leipzig fernsehen.*?,', 'leitv', data)
    data = sub('nrw.tv.*?,', 'nrwtv', data)
    data = sub('rheinmain tv.*?,', 'rmtv', data)
    data = sub('rnf.*?,', 'rnf', data)
    data = sub('sachsen fernsehen.*?,', 'sach', data)
    data = sub('orf 1.*?,', 'orf1', data)
    data = sub('orf1.*?,', 'orf1', data)
    data = sub('orf eins.*?,', 'orf1', data)
    data = sub('orf 2.*?,', 'orf2', data)
    data = sub('orf2.*?,', 'orf2', data)
    data = sub('orf.iii.*?,', 'orf3', data)
    data = sub('orf.sport.*?,', 'orfsp', data)
    data = sub('sf1.*?,', 'sf1', data)
    data = sub('sf 1.*?,', 'sf1', data)
    data = sub('sf 2.*?,', 'sf2', data)
    data = sub('sf zwei.*?,', 'sf2', data)
    data = sub('atv,', 'atv', data)
    data = sub('atv hd,', 'atv', data)
    data = sub('atv2.*?,', 'atv2', data)
    data = sub('atv 2.*?,', 'atv2', data)
    data = sub('atv ii,', 'atv2', data)
    data = sub('puls 4.*?,', 'puls4', data)
    data = sub('boomerang.*?,', 'boom', data)
    data = sub('nick jr.*?,', 'nickj', data)
    data = sub('nick.*?,', 'nick', data)
    data = sub('nicktoons.*?,', 'nickt', data)
    data = sub('comedy central.*?,', 'cc', data)
    data = sub('cartoon net.*?,', 'c-net', data)
    data = sub('disney cinema.*?,', 'dcm', data)
    data = sub('disney channel.*?,', 'disne', data)
    data = sub('disney junior.*?,', 'djun', data)
    data = sub('disney xd.*?,', 'dxd', data)
    data = sub('disney hd,', 'disne', data)
    data = sub('junior.*?,', 'junio', data)
    data = sub('kika.*?,', 'kika', data)
    data = sub('vh1 classic.*?,', 'vh1', data)
    data = sub('deluxe music.*?,', 'dmc', data)
    data = sub('mtv,', 'mtv', data)
    data = sub('mtv hd,', 'mtv', data)
    data = sub('mtv g.*?,', 'mtv', data)
    data = sub('mtv ba.*?,', 'mtv-b', data)
    data = sub('mtv da.*?.*?,', 'mtv-d', data)
    data = sub('mtv hi.*?.*?,', 'mtv-h', data)
    data = sub('mtv li.*?,', 'mtv-l', data)
    data = sub('viva.*?,', 'viva', data)
    data = sub('im1,', 'imt', data)
    data = sub('rock tv.*?,', 'rck', data)
    data = sub('jukebox.*?,', 'juke', data)
    data = sub('trace.*?,', 'trace', data)
    data = sub('classica.*?,', 'class', data)
    data = sub('gute laune.*?,', 'laune', data)
    data = sub('beate-uhse.*?,', 'butv', data)
    data = sub('lust pur.*?,', 'lustp', data)
    data = sub('playboy tv,', 'pboy', data)
    data = sub('al jazeera.*?,', 'aljaz', data)
    data = sub('bloomberg.*?,', 'blm', data)
    data = sub('euronews.*?,', 'euron', data)
    data = sub('bibel tv.*?,', 'bibel', data)
    data = sub('kirchen tv.*?,', 'ktv', data)
    data = sub('timm.*?,', 'timm', data)
    data = sub('sonnenklar.*?,', 'sklar', data)
    data = sub('goldstar tv,', 'gold', data)
    data = sub('animax,', 'amax', data)
    data = sub('adult channel.*?,', 'adult', data)
    data = sub('das neue tv.*?,', 'dntv', data)
    data = sub('deutsches wetter.*?,', 'dwf', data)
    data = sub('e!.*?,', 'e!', data)
    data = sub('fashion tv.*?,', 'fatv', data)
    data = sub('family tv.*?,', 'famtv', data)
    data = sub('mezzo.*?,', 'mezzo', data)
    data = sub('nautical.*?,', 'nauch', data)
    data = sub('nl 1.*?,', 'nl1', data)
    data = sub('nl 2.*?,', 'nl2', data)
    data = sub('nl 3.*?,', 'nl3', data)
    data = sub('dr1.*?,', 'dr1', data)
    data = sub('belgien.*?,', 'be1', data)
    data = sub('france24.*?fr.*?,', 'fr24f', data)
    data = sub('france24.*?en.*?,', 'fr24e', data)
    data = sub('france 2.*?,', 'fra2', data)
    data = sub('france 3.*?,', 'fra3', data)
    data = sub('france 5.*?,', 'fra5', data)
    data = sub('tv 2.*?,', 'tv5', data)
    data = sub('tv 5.*?,', 'tv5', data)
    data = sub('ric.*?,', 'ric', data)
    data = sub('tlc.*?,', 'tlc', data)
    data = sub('star tv.*?,', 'sttv', data)
    data = sub('center.tv.*?,', 'cente', data)
    data = sub('sony.*?,', 'sony', data)
    data = sub('auto motor sport.*?,', 'ams', data)
    data = sub('3 plus.*?,', '3plus', data)
    data = sub('3+.*?,', '3plus', data)
    data = sub('marco polo.*?,', 'mapo', data)
    data = sub('travel channel.*?,', 'trch', data)
    data = sub('channel21.*?,', 'ch21', data)
    data = sub('geo television.*?,', 'geo', data)
    data = sub('geo tv.*?,', 'geo', data)
    data = sub('fix.*?foxi.*?,', 'fftv', data)
    data = sub('welt.*?,', 'welt', data)
    data = sub('dw.*?,', 'dwtv', data)
    data = sub('deutsches musik fernsehen.*?,', 'dmf', data)
    data = sub('rbb.*?,', 'rbb', data)
    data = sub('ndr.*?,', 'n3', data)
    data = sub('mdr.*?,', 'mdr', data)
    data = sub('wdr.*?,', 'wdr', data)
    data = sub('hr.*?,', 'hr', data)
    data = sub('swr.*?,', 'swr', data)
    data = sub('br.*?,', 'swr', data)
    data = sub('tele 5.*?,', 'TELE5', data)
    data = sub('bild hd,', 'bild', data)
    data = sub('warner .*?comedy.*?,', 'tnt-c', data)
    data = sub('warner .*?film.*?,', 'tnt-f', data)
    data = sub('warner .*?serie.*?,', 'tnt-s', data)
    data = sub('hse.*?,', 'hse', data)
    data = sub('qvc.*?,', 'qvc', data)
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
            text = text + x + '\n\n'
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
        entries.append((LOGO, TIME, LINK, title, sparte, genre, rating))
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

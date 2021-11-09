#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import six
from re import sub, findall, S as RES, search
from twisted.web.client import getPage
from twisted.internet import reactor
import sys

NEXTPage1 = 'class="js-track-link pagination__link pagination__link--next"'
NEXTPage2 = '<a href="(.*?)"\n\\s+class="js-track-link pagination__link pagination__link--next"'


def shortenChannel(text):
    text = text.replace('ProSieben ', 'Pro7 ').replace('kabel eins CLASSICS', 'k1CLASSICS').replace('Sky Family', 'SkyFamily').replace('Sky Cinema+', 'SkyCine+').replace('Sky Comedy', 'SkyComedy').replace('Sky Emotion', 'SkyEmotion').replace('Sky Sport HD', 'SkySport').replace('Eurosport ', 'Eurosport').replace('EXTREME SPORTS', 'EXTREME').replace('NAT GEO WILD', 'NatGeoWild').replace('Romance TV', 'RomanceTV')
    text = text.replace('13th Street', '13thStreet').replace('VH1 Classic', 'VH1Classic').replace('COMEDY CENTRAL', 'COMEDY C').replace('Cartoon Network', 'CartoonNet').replace('Disney Cinemagic', 'DisneyCine').replace('HISTORY HD', 'History HD').replace('DELUXE MUSIC', 'DeluxMusic')
    return text


def transWIKI(text):
    text = text.replace('\xc3\x84', '\xc4').replace('\xc3\x96', '\xd6').replace('\xc3\x9c', '\xdc').replace('\xc3\x9f', '\xdf').replace('\xc3\xa4', '\xe4').replace('\xc3\xb6', '\xf6').replace('\xc3\xbc', '\xfc').replace('&', '%26').replace('\xe2\x80', '-')
    return text


def transHTML(text):
    text = text.replace('&nbsp;', ' ').replace('&szlig;', 'ss').replace('&quot;', '"').replace('&ndash;', '-').replace('&Oslash;', '').replace('&bdquo;', '"').replace('&ldquo;', '"').replace('&rsquo;', "'").replace('&gt;', '>').replace('&lt;', '<').replace('&shy;', '')
    text = text.replace('&copy;.*', ' ').replace('&amp;copy;', '').replace('&amp;', '&').replace('&uuml;', '\xc3\xbc').replace('&auml;', '\xc3\xa4').replace('&ouml;', '\xc3\xb6').replace('&eacute;', '\xe9').replace('&hellip;', '...').replace('&egrave;', '\xe8').replace('&agrave;', '\xe0').replace('&mdash;', '-')
    text = text.replace('&Uuml;', 'Ue').replace('&Auml;', 'Ae').replace('&Ouml;', 'Oe').replace('&#034;', '"').replace('&#039;', "'").replace('&#34;', '"').replace('&#38;', 'und').replace('&#39;', "'").replace('&#133;', '...').replace('&#196;', '\xc3\x84').replace('&#214;', '\xc3\x96').replace('&#220;', '\xc3\x9c').replace('&#223;', '\xc3\x9f').replace('&#228;', '\xc3\xa4').replace('&#246;', '\xc3\xb6').replace('&#252;', '\xc3\xbc').replace('&#287;', 'c').replace('&#324;', 'n').replace('&#351;', 's')
    text = text.replace('&#8211;', '-').replace('&#8212;', '\x97').replace('&#8216;', "'").replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"').replace('&#8230;', '...').replace('&#8242;', "'").replace('&#8243;', '"')
    return text


def transCHANNEL(data):
    data = sub('Das Erste.*?,', 'ard', data)
    data = sub('ZDF HD,', 'zdf', data)
    data = sub('ZDF,', 'zdf', data)
    data = sub('zdf_neo.*?,', '2neo', data)
    data = sub('zdf neo.*?,', '2neo', data)
    data = sub('ZDF_neo.*?,', '2neo', data)
    data = sub('ZDF neo.*?,', '2neo', data)
    data = sub('ZDFneo.*?,', '2neo', data)
    data = sub('ZDFinfo.*?,', 'zinfo', data)
    data = sub('ZDF info.*?,', 'zinfo', data)
    data = sub('EinsPlus.*?,', 'mux', data)
    data = sub('eins plus.*?,', 'mux', data)
    data = sub('Zee.One.*?,', 'zee-1', data)
    data = sub('zee.one.*?,', 'zee-1', data)
    data = sub('One,', 'fes', data)
    data = sub('One HD,', 'fes', data)
    data = sub('ONE,', 'fes', data)
    data = sub('ONE HD,', 'fes', data)
    data = sub('tagesschau.*?,', 'tag24', data)
    data = sub('3sat.*?,', '3sat', data)
    data = sub('3Sat.*?,', '3sat', data)
    data = sub('phoenix.*?,', 'phoen', data)
    data = sub('Phoenix.*?,', 'phoen', data)
    data = sub('PHOENIX.*?,', 'phoen', data)
    data = sub('ProSieben,', 'pro7', data)
    data = sub('ProSieben Austria,', 'pro7', data)
    data = sub('ProSieben HD,', 'pro7', data)
    data = sub('Prosieben,', 'pro7', data)
    data = sub('Prosieben Austria,', 'pro7', data)
    data = sub('Prosieben HD,', 'pro7', data)
    data = sub('Pro 7,', 'pro7', data)
    data = sub('Pro7,', 'pro7', data)
    data = sub('Pro 7 HD,', 'pro7', data)
    data = sub('Pro7 HD,', 'pro7', data)
    data = sub('Pro.*?Fun,', 'pro7f', data)
    data = sub('Pro.*?FUN,', 'pro7f', data)
    data = sub('Pro.*?Fun HD,', 'pro7f', data)
    data = sub('Pro.*?FUN HD,', 'pro7f', data)
    data = sub('Pro.*?Maxx,', 'pro7m', data)
    data = sub('Pro.*?MAXX,', 'pro7m', data)
    data = sub('Pro.*?Maxx HD,', 'pro7m', data)
    data = sub('Pro.*?MAXX HD,', 'pro7m', data)
    data = sub('SAT 1,', 'sat1', data)
    data = sub('SAT.1,', 'sat1', data)
    data = sub('Sat.1,', 'sat1', data)
    data = sub('SAT.1 A.*?,', 'sat1', data)
    data = sub('Sat.1 A.*?,', 'sat1', data)
    data = sub('SAT 1 HD,', 'sat1', data)
    data = sub('SAT.1 HD,', 'sat1', data)
    data = sub('Sat.1 HD,', 'sat1', data)
    data = sub('SAT 1 emotions.*?,', 'sat1e', data)
    data = sub('SAT.1 emotions.*?,', 'sat1e', data)
    data = sub('Sat.1 emotions.*?,', 'sat1e', data)
    data = sub('SAT 1 Emotions.*?,', 'sat1e', data)
    data = sub('SAT.1 Emotions.*?,', 'sat1e', data)
    data = sub('Sat.1 Emotions.*?,', 'sat1e', data)
    data = sub('SAT 1 Gold.*?,', 'sat1g', data)
    data = sub('SAT.1 Gold.*?,', 'sat1g', data)
    data = sub('Sat.1 Gold.*?,', 'sat1g', data)
    data = sub('RTL,', 'rtl', data)
    data = sub('RTL Television.*?,', 'rtl', data)
    data = sub('RTL Austria,', 'rtl', data)
    data = sub('RTL HD,', 'rtl', data)
    data = sub('RTLZWEI,', 'rtl2', data)
    data = sub('RTLZWEI HD,', 'rtl2', data)
    data = sub('Super rtl', 'super', data)
    data = sub('SUPER rtl', 'super', data)
    data = sub('SUPER RTL.*?,', 'super', data)
    data = sub('RTLPlus,', 'rtlpl', data)
    data = sub('RTLplus,', 'rtlpl', data)
    data = sub('rtlplus,', 'rtlpl', data)
    data = sub('RTL Crime.*?,', 'rtl-c', data)
    data = sub('RTL Living.*?,', 'rtl-l', data)
    data = sub('RTL Nitro.*?,', 'rtl-n', data)
    data = sub('RTL NITRO.*?,', 'rtl-n', data)
    data = sub('RTLNITRO.*?,', 'rtl-n', data)
    data = sub('NITRO.*?,', 'rtl-n', data)
    data = sub('RTL Passion.*?,', 'pass', data)
    data = sub('Passion,', 'pass', data)
    data = sub('Passion HD,', 'pass', data)
    data = sub('VOX.*?,', 'vox', data)
    data = sub('Vox.*?,', 'vox', data)
    data = sub('sixx.*?,', 'sixx', data)
    data = sub('SIXX.*?,', 'sixx', data)
    data = sub('kabel eins,', 'k1', data)
    data = sub('kabel eins C.*?,', 'k1cla', data)
    data = sub('Kabel 1,', 'k1', data)
    data = sub('Kabel 1 Austria,', 'k1', data)
    data = sub('Kabel 1 C.*?,', 'k1cla', data)
    data = sub('kabel 1 C.*?,', 'k1cla', data)
    data = sub('kabel eins HD,', 'k1', data)
    data = sub('kabel 1 HD,', 'k1', data)
    data = sub('Kabel 1 HD,', 'k1', data)
    data = sub('kabel eins Doku,', 'k1doku', data)
    data = sub('Kabel eins Doku,', 'k1doku', data)
    data = sub('kabel 1 Doku,', 'k1doku', data)
    data = sub('Kabel 1 Doku,', 'k1doku', data)
    data = sub('kabel eins Doku Austria,', 'k1doku', data)
    data = sub('Kabel eins Doku Austria,', 'k1doku', data)
    data = sub('kabel 1 Doku Austria,', 'k1doku', data)
    data = sub('Kabel 1 Doku Austria,', 'k1doku', data)
    data = sub('SKY', 'Sky', data)
    data = sub('Sky 1.*?,', 'sky1', data)
    data = sub('Sky Arts.*?,', 'arts', data)
    data = sub('Sky 007.*?,', 'sky-h', data)
    data = sub('Sky Atlantic.*?,', 'skyat', data)
    data = sub('Sky Cinema Premieren,', 'cin', data)
    data = sub('Sky Cinema Premieren HD,', 'cin', data)
    data = sub('Sky Cinema Thriller HD,', 'skyth', data)
    data = sub('Sky Cinema Premieren.*?,', 'cin24', data)
    data = sub('Sky Cinema Premieren +24,', 'cin24', data)
    data = sub('Sky Action.*?,', 'sky-a', data)
    data = sub('Sky Cinema Action.*?,', 'sky-a', data)
    data = sub('Sky Fun.*?,', 'sky-c', data)
    data = sub('Sky Cinema Fun.*?,', 'sky-c', data)
    data = sub('Sky Special HD.*?,', 'sky-e', data)
    data = sub('Sky Cinema Special HD,*?,', 'skycs', data)
    data = sub('Sky Family.*?,', 'sky-f', data)
    data = sub('Sky Cinema Family.*?,', 'sky-f', data)
    data = sub('Sky Best Of HD.*?,', 'sky-h', data)
    data = sub('Sky Cinema Best Of HD.*?,', 'sky-h', data)
    data = sub('Sky Cinema Classics.*?,', 'sky-n', data)
    data = sub('Sky Xmas.*?,', 'xmas', data)
    data = sub('Sky Christmas.*?,', 'xmas', data)
    data = sub('Sky Cinema Star.*?,', 'sky-h', data)
    data = sub('Sky Krimi.*?,', 'sky-k', data)
    data = sub('Sky 3D,', 'sky3d', data)
    data = sub('Sky Select.*?,', 'sky-s', data)
    data = sub('Sky select.*?,', 'sky-s', data)
    data = sub('Sky Bundesliga 1,', 'buli', data)
    data = sub('Sky Bundesliga HD 1,', 'buli', data)
    data = sub('Sky Bundesliga.*?\n', '', data)
    data = sub('Sky Sport News.*?,', 'snhd', data)
    data = sub('Sky Sport HD,', 'snhd', data)
    data = sub('Sky Sport HD 1,', 'hdspo', data)
    data = sub('Sky Sport 1 HD,', 'hdspo', data)
    data = sub('Sky Sport HD 2,', 'shd2', data)
    data = sub('Sky Sport 2 HD,', 'shd2', data)
    data = sub('Sky Sport 1,', 'spo1', data)
    data = sub('Sky Sport 2,', 'spo2', data)
    data = sub('Sky Sport Austria.*?,', 'spo-a', data)
    data = sub('Sky Sport.*?\n', '', data)
    data = sub('SPORT1,', 'sport', data)
    data = sub('Sport1,', 'sport', data)
    data = sub('SPORT 1,', 'sport', data)
    data = sub('Sport 1,', 'sport', data)
    data = sub('SPORT1 HD,', 'sport', data)
    data = sub('Sport1 HD,', 'sport', data)
    data = sub('SPORT 1 HD,', 'sport', data)
    data = sub('Sport 1 HD,', 'sport', data)
    data = sub('SPORT1[+].*?,', 's1plu', data)
    data = sub('Sport1[+].*?,', 's1plu', data)
    data = sub('SPORT 1[+],', 's1plu', data)
    data = sub('Sport 1[+],', 's1plu', data)
    data = sub('SPORT 1[+] HD,', 's1plu', data)
    data = sub('Sport 1[+] HD,', 's1plu', data)
    data = sub('SPORT1 US.*?,', 'sp1us', data)
    data = sub('Sport1 US.*?,', 'sp1us', data)
    data = sub('SPORT 1 US,', 'sp1us', data)
    data = sub('Sport 1 US,', 'sp1us', data)
    data = sub('SPORT 1 US HD,', 'sp1us', data)
    data = sub('Sport 1 US HD,', 'sp1us', data)
    data = sub('EUROSPORT 2.*?,', 'euro2', data)
    data = sub('Eurosport 2.*?,', 'euro2', data)
    data = sub('EUROSPORT .*?,', 'euro', data)
    data = sub('Eurosport .*?,', 'euro', data)
    data = sub('ESPN America.*?,', 'nasn', data)
    data = sub('ESPN Classic.*?,', 'espn', data)
    data = sub('Motors TV.*?,', 'motor', data)
    data = sub('Motorvision TV.*?,', 'movtv', data)
    data = sub('sportdigital.*?,', 'spo-d', data)
    data = sub('Extreme Sports.*?,', 'ex-sp', data)
    data = sub('kabel.*?lassic.*?,', 'k1cla', data)
    data = sub('Kabel.*?lassic.*?,', 'k1cla', data)
    data = sub('MGM.*?,', 'mgm', data)
    data = sub('KINOWELT.*?,', 'kinow', data)
    data = sub('Kinowelt.*?,', 'kinow', data)
    data = sub('FOX.*?,', 'fox', data)
    data = sub('Fox.*?,', 'fox', data)
    data = sub('SYFY.*?,', 'scifi', data)
    data = sub('SyFy.*?,', 'scifi', data)
    data = sub('Syfy.*?,', 'scifi', data)
    data = sub('TNT G.*?,', 'glitz', data)
    data = sub('glitz.*?,', 'glitz', data)
    data = sub('Universal.*?,', 'unive', data)
    data = sub('UNIVERSAL.*?,', 'unive', data)
    data = sub('TOGGO.*?,', 'toggo', data)
    data = sub('Romance TV.*?,', 'rom', data)
    data = sub('Heimatkanal.*?,', 'heima', data)
    data = sub('The Biography.*?,', 'bio', data)
    data = sub('Biography.*?,', 'bio', data)
    data = sub('Bio Channel,', 'bio', data)
    data = sub('Tele 5.*?,', 'tele5', data)
    data = sub('TELE 5.*?,', 'tele5', data)
    data = sub('ANIXE.*?,', 'anixe', data)
    data = sub('Anixe.*?,', 'anixe', data)
    data = sub('13th.*?,', '13th', data)
    data = sub('13TH.*?,', '13th', data)
    data = sub('AXN.*?,', 'axn', data)
    data = sub('Silverline.*?,', 'silve', data)
    data = sub('Welt der Wunder.*?,', 'wdwtv', data)
    data = sub('arte.*?,', 'arte', data)
    data = sub('ARTE.*?,', 'arte', data)
    data = sub('n-tv.*?,', 'ntv', data)
    data = sub('N24 D.*?,', 'n24doku', data)
    data = sub('N24.*?,', 'welt', data)
    data = sub('Welt.*?,', 'welt', data)
    data = sub('CNN.*?,', 'cnn', data)
    data = sub('BBC W.*?,', 'bbc', data)
    data = sub('BBC E.*?,', 'bbc-e', data)
    data = sub('DMAX.*?,', 'dmax', data)
    data = sub('Spiegel TV.*?,', 'sptvw', data)
    data = sub('Spiegel Geschichte.*?,', 'sp-ge', data)
    data = sub('Spiegel History.*?,', 'sp-ge', data)
    data = sub('HISTORY.*?,', 'hishd', data)
    data = sub('History.*?,', 'hishd', data)
    data = sub('The History.*?,', 'hishd', data)
    data = sub('Animal Planet.*?,', 'aplan', data)
    data = sub('Planet.*?,', 'plane', data)
    data = sub('PLANET.*?,', 'plane', data)
    data = sub('Discovery.*?HD,', 'hddis', data)
    data = sub('Discovery Channel,', 'disco', data)
    data = sub('NatGeo Wild.*?,', 'n-gw', data)
    data = sub('Nat Geo Wild.*?,', 'n-gw', data)
    data = sub('Nat GEO Wild.*?,', 'n-gw', data)
    data = sub('NatGeo People.*?,', 'n-gp', data)
    data = sub('Nat Geo People.*?,', 'n-gp', data)
    data = sub('Nat GEO People.*?,', 'n-gp', data)
    data = sub('NatGeo HD,', 'n-ghd', data)
    data = sub('Nat Geo HD,', 'n-ghd', data)
    data = sub('Nat GEO HD,', 'n-ghd', data)
    data = sub('NATGEO HD,', 'n-ghd', data)
    data = sub('NAT GEO HD,', 'n-ghd', data)
    data = sub('National Geographic.*?,', 'n-geo', data)
    data = sub('BonGusto,', 'gusto', data)
    data = sub('Bon Gusto HD,', 'gusto', data)
    data = sub('ServusTV.*?,', 'servu', data)
    data = sub('Servus TV.*?,', 'servu', data)
    data = sub('SR Fernsehen.*?,', 'swr', data)
    data = sub('Bayerisches.*?,', 'br', data)
    data = sub('BR M.*?,', 'br', data)
    data = sub('BR N.*?,', 'br', data)
    data = sub('BR S.*?,', 'br', data)
    data = sub('BR Fern.*?,', 'br', data)
    data = sub('BR-alpha,', 'bralp', data)
    data = sub('ARD-alpha,', 'alpha', data)
    data = sub('SRF1.*?,', 'sf1', data)
    data = sub('SRF 1.*?,', 'sf1', data)
    data = sub('SF2.*?,', 'sf2', data)
    data = sub('SRF2.*?,', 'sf2', data)
    data = sub('SRF 2.*?,', 'sf2', data)
    data = sub('SRF zwei.*?,', 'sf2', data)
    data = sub('Hamburg 1,', 'hh1', data)
    data = sub('m.*?nchen2,', 'mue2', data)
    data = sub('m.*?nchen.tv,', 'tvm', data)
    data = sub('tv.berlin,', 'tvb', data)
    data = sub('Leipzig Fernsehen.*?,', 'leitv', data)
    data = sub('NRW.TV.*?,', 'nrwtv', data)
    data = sub('rheinmain tv.*?,', 'rmtv', data)
    data = sub('Rhein-Neckar Fernsehen.*?,', 'rnf', data)
    data = sub('Sachsen Fernsehen.*?,', 'sach', data)
    data = sub('ORF 1.*?,', 'orf1', data)
    data = sub('ORF1.*?,', 'orf1', data)
    data = sub('ORF eins.*?,', 'orf1', data)
    data = sub('ORF 2.*?,', 'orf2', data)
    data = sub('ORF2.*?,', 'orf2', data)
    data = sub('ORF.III.*?,', 'orf3', data)
    data = sub('ORF.Sport.*?,', 'orfsp', data)
    data = sub('ORF.SPORT.*?,', 'orfsp', data)
    data = sub('SF1.*?,', 'sf1', data)
    data = sub('SF 1.*?,', 'sf1', data)
    data = sub('SF 2.*?,', 'sf2', data)
    data = sub('SF zwei.*?,', 'sf2', data)
    data = sub('ATV,', 'atv', data)
    data = sub('ATV HD,', 'atv', data)
    data = sub('ATV2,', 'atv2', data)
    data = sub('ATV2 HD,', 'atv2', data)
    data = sub('ATV 2,', 'atv2', data)
    data = sub('ATV 2 HD,', 'atv2', data)
    data = sub('ATV II,', 'atv2', data)
    data = sub('PULS 4.*?,', 'puls4', data)
    data = sub('Boomerang.*?,', 'boom', data)
    data = sub('Nick/Comedy.*?,', 'nickcc', data)
    data = sub('NICK/Comedy.*?,', 'nickcc', data)
    data = sub('VIVA/Comedy.*?,', 'vivacc', data)
    data = sub('VIVA/COMEDY.*?,', 'vivacc', data)
    data = sub('Nick Jr.*?,', 'nickj', data)
    data = sub('NICK.*?,', 'nick', data)
    data = sub('Nicktoons.*?,', 'nickt', data)
    data = sub('COMEDY CENTRAL.*?,', 'cc', data)
    data = sub('Comedy Central.*?,', 'cc', data)
    data = sub('ComedyCentral.*?,', 'cc', data)
    data = sub('Cartoon Net.*?,', 'c-net', data)
    data = sub('Disney Cine.*?,', 'dcm', data)
    data = sub('Disney Channel.*?,', 'disne', data)
    data = sub('Disney HD,', 'disne', data)
    data = sub('Disney Junior.*?,', 'djun', data)
    data = sub('Disney XD.*?,', 'dxd', data)
    data = sub('Junior.*?,', 'junio', data)
    data = sub('KiKA.*?,', 'kika', data)
    data = sub('VH1 Classic.*?,', 'vh1', data)
    data = sub('DELUXE MUSIC.*?,', 'dmc', data)
    data = sub('Deluxe Music.*?,', 'dmc', data)
    data = sub('MTV,', 'mtv', data)
    data = sub('MTV HD,', 'mtv', data)
    data = sub('MTV G.*?,', 'mtv', data)
    data = sub('MTV Ba.*?,', 'mtv-b', data)
    data = sub('MTV Da.*?.*?,', 'mtv-d', data)
    data = sub('MTV Hi.*?.*?,', 'mtv-h', data)
    data = sub('MTV Li.*?,', 'mtv-l', data)
    data = sub('VIVA.*?,', 'viva', data)
    data = sub('iM1,', 'imt', data)
    data = sub('Rock TV.*?,', 'rck', data)
    data = sub('Jukebox.*?,', 'juke', data)
    data = sub('TRACE.*?,', 'trace', data)
    data = sub('CLASSICA.*?,', 'class', data)
    data = sub('Classica.*?,', 'class', data)
    data = sub('Gute Laune.*?,', 'laune', data)
    data = sub('Beate-Uhse.*?,', 'butv', data)
    data = sub('Lust Pur.*?,', 'lustp', data)
    data = sub('Playboy TV,', 'pboy', data)
    data = sub('Al Jazeera.*?,', 'aljaz', data)
    data = sub('center.tv.*?,', 'cente', data)
    data = sub('Bloomberg.*?,', 'blm', data)
    data = sub('euronews.*?,', 'euron', data)
    data = sub('EuroNews.*?,', 'euron', data)
    data = sub('bibel TV,', 'bibel', data)
    data = sub('Bibel TV,', 'bibel', data)
    data = sub('Kirchen TV,', 'ktv', data)
    data = sub('TIMM,', 'timm', data)
    data = sub('HSE 24.*?,', 'hse', data)
    data = sub('HSE24.*?,', 'hse', data)
    data = sub('QVC.*?,', 'qvc', data)
    data = sub('Sonnenklar.*?,', 'sklar', data)
    data = sub('sonnenklar.*?,', 'sklar', data)
    data = sub('Goldstar TV,', 'gold', data)
    data = sub('Animax,', 'amax', data)
    data = sub('ANIMAX,', 'amax', data)
    data = sub('Blue Movie 2,', 'blum2', data)
    data = sub('BLUE MOVIE 2,', 'blum2', data)
    data = sub('Blue Movie 3,', 'blum3', data)
    data = sub('BLUE MOVIE 3,', 'blum3', data)
    data = sub('Blue Movie.*?,', 'blum', data)
    data = sub('BLUE MOVIE.*?,', 'blum', data)
    data = sub('Adult Channel,', 'adult', data)
    data = sub('Das Neue TV.*?,', 'dntv', data)
    data = sub('Deutsches Wetter.*?,', 'dwf', data)
    data = sub('E!.*?,', 'e!', data)
    data = sub('Fashion TV.*?,', 'fatv', data)
    data = sub('Family TV.*?,', 'famtv', data)
    data = sub('Mezzo.*?,', 'mezzo', data)
    data = sub('Nautical.*?,', 'nauch', data)
    data = sub('NL 1.*?,', 'nl1', data)
    data = sub('NL 2.*?,', 'nl2', data)
    data = sub('NL 3.*?,', 'nl3', data)
    data = sub('DR1.*?,', 'dr1', data)
    data = sub('Belgien.*?,', 'be1', data)
    data = sub('France 24.*?fran.*?,', 'fr24f', data)
    data = sub('France 24.*?eng.*?,', 'fr24e', data)
    data = sub('TV2.*?,', 'tv2', data)
    data = sub('TV5.*?,', 'tv5', data)
    data = sub('RiC.*?,', 'ric', data)
    data = sub('TLC.*?,', 'tlc', data)
    data = sub('STAR TV.*?,', 'sttv', data)
    data = sub('Star TV.*?,', 'sttv', data)
    data = sub('center.tv.*?,', 'cente', data)
    data = sub('Liga total!.*?,', 'liga', data)
    data = sub('LIGA total!.*?,', 'liga', data)
    data = sub('Sony.*?,', 'sony', data)
    data = sub('SONY.*?,', 'sony', data)
    data = sub('eoTV.*?,', 'eotv', data)
    data = sub('EOTV.*?,', 'eotv', data)
    data = sub('Erf.*?,', 'erf', data)
    data = sub('ERF.*?,', 'erf', data)
    data = sub('FLT.*?,', 'flt', data)
    data = sub('flt.*?,', 'flt', data)
    data = sub('Joiz.*?,', 'joiz', data)
    data = sub('joiz.*?,', 'joiz', data)
    data = sub('Auto Motor Sport.*?,', 'ams', data)
    data = sub('yourfamily.*?,', 'yfe', data)
    data = sub('Yourfamily.*?,', 'yfe', data)
    data = sub('Your Family.*?,', 'yfe', data)
    data = sub('3 Plus,', '3plus', data)
    data = sub('3+,', '3plus', data)
    data = sub('A&E,', 'aetv', data)
    data = sub('blizz.*?,', 'blizz', data)
    data = sub('QLAR.*?,', 'qlar', data)
    data = sub('Fine Living.*?,', 'fln', data)
    data = sub('Food Network.*?,', 'food', data)
    data = sub('Marco Polo.*?,', 'mapo', data)
    data = sub('Travel Channel.*?,', 'trch', data)
    data = sub('Channel21.*?,', 'ch21', data)
    data = sub('GEO Television.*?,', 'geo', data)
    data = sub('Geo Television.*?,', 'geo', data)
    data = sub('FIX.*?FOXI.*?,', 'fftv', data)
    data = sub('Fix.*?Foxi.*?,', 'fftv', data)
    data = sub('WELT HD.*?,', 'welt', data)
    data = sub('DW,', 'dwtv', data)
    data = sub('Deutsche Welle.*?,', 'dwtv', data)
    data = sub('rbb.*?,', 'rbb', data)
    data = sub('RBB.*?,', 'rbb', data)
    data = sub('NDR.*?,', 'n3', data)
    data = sub('MDR.*?,', 'mdr', data)
    data = sub('WDR.*?,', 'wdr', data)
    data = sub('hr.*?,', 'hr', data)
    data = sub('HR.*?,', 'hr', data)
    data = sub('SWR.*?,', 'swr', data)
    data = sub('BR.*?,', 'swr', data)
    data = sub('TELE 5.*?,', 'TELE5', data)
    data = sub('BILD HD,', 'bild', data)
    data = sub('Warner TV Comedy HD,', 'tnt-c', data)
    data = sub('Warner TV Film HD,', 'tnt-f', data)
    data = sub('Warner TV Serie HD,', 'tnt-s', data)
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
#    startpos = output.find('<table class="info-table"')
#    endpos = output.find('<div class="block-in">')
#    if endpos == -1:
#        endpos = output.find('<div class="two-blocks">')
#    bereich = output[startpos:endpos]
#    output = transHTML(bereich)
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
            sparte = findall('<td class="col-5">\n\\s+<span>(.*?)\n\\s+</span>', item, RES)[0]
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
    output = six.ensure_str(output)
    a = buildTVTippsArray("Serie", output)
    print(a)


def testtvnow(output):
    output = six.ensure_str(output)
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
    output = six.ensure_str(output)
    a, b = parseNow(output)
    print(a)


def testparseInfo(output):
    output = six.ensure_str(output)
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

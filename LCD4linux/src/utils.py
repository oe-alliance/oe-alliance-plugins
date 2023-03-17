# -*- coding: utf-8 -*-#

def getIPTVProvider(url):
#	This function determines the name of the IPTV provider by
#	the unique value of the substring in the broadcast url-link
#	:param url: the url from serviceref
#	:param type: url
#	:ret: IPTV provider name
#	:ret type: String limited to 12 characters
	providers = {
			'tvshka.net': 'ShuraTV',      # shura.tv
			'1ott.': '1ott',         # my.1ott.net
			'only4.tv': '1Cent',        # 1cent.tv
			'satbiling.com': 'Satbilling',  # iptv.satbilling.com
			'.crd-s.': 'CdruTV',       # crdru.net
			'/live/s.': 'Shara.club',   # shara.club
			'/live/u.': 'IPStream',     # ipstream.one
			'/iptv/': 'iLook',        # edem.tv (ilook.tv)
			'.ottg.': 'Glanz',        # glanz (ottg.tv)
			'.fox-tv.': 'Fox-TV',       # fox-tv.fun
			'.iptv.': 'IPTV.Online',  # iptv.online
			'.mymagic.': 'MyMagic',      # mymagic.tv
			'tvfor.pro': 'Shara-TV',     # shara-tv.org
			'uz-tv': 'UZ-TV',        # uz-tv.net
			'.bcumedia.pro': 'BCUMedia',    # bcumedia.pro
			'.antifriz.': 'Antifriz',     # antifriz.tx
			'app-greatiptv': 'GreatIPTV',   # app.greatiptv.cc
			'.zala.': 'ZalaBY',       # zala.by
			'/zatv/': 'ZalaBY',       # zala.by
			'178.124.183.': 'ZalaBY',       # zala.by
			'zabava': 'Zabava',       # zabava.tv
			'cdn.ngenix.net': 'Zabava',     # zabava.tv
			'.spr24.': 'Sharavoz',     # sharavoz.tv
			'.onlineott.': 'TvoeTV',       # tvoetv.in.ua
			'85.143.191.': 'NTTV',         # ttv.run
			'myott.top': 'Ottclub',      # ottclub.cc
			'.itv.': 'ITV',          # itv.live
			'cdn.wf': 'ITV',          # itv.live
			'iptvx.tv': 'Cbilling',     # cbilling.me
			'tv.team': 'TVTeam',       # tv.team
			'troya.tv': 'TVTeam',       # tv.team
			'1usd.tv': 'TVTeam',       # tv.team
			'cdntv.online': 'VIPLime',      # viplime.fun
			'.tvdosug.': 'TVDosug',      # tvdosug.tv
			'/channel/': 'Zmedia',       # ZMedia Proxy vps https://t.me/wink_news/107
			'/rmtv/': 'Zmedia',       # ZMedia Proxy local
			'undefined': '',
		}
	return providers[next(iter([x for x in list(providers.keys()) if x in url]), 'undefined')][:12]


def getAudio(description):

#	Returns the picon file for the corresponding audio track
#	:param description: audio track description
#	:param type: str
#	:ret: picon file for audiotrack
#	:ret type: str

	if "Dolby Digital" in description:
		return "audio/dolbydigital.png"
	elif any(x in description for x in ["AC3+", "DD+", "E-AC-3", "EC-3", "ac3+", "dd+", "e-ac-3", "ec-3"]):
		return "audio/AC3plus.png"
	elif any(x in description for x in ["AC3", "AC-3", "ac3", "ac-3"]):
		return "audio/AC3.png"
	elif "DTS-HD" in description:
		return "audio/DTS-HD.png"
	elif "DTS" in description:
		return "audio/DTS.png"
	elif "AAC-HE" in description:
		return "audio/AAC-HE.png"
	elif "AAC" in description:
		return "audio/AAC.png"
	elif "MPEG-1" in description:
		return "audio/MP1.png"
	elif "MPEG-4" in description:
		return "audio/MPEG4.png"
	elif "MPEG" in description:
		return "audio/MPEG.png"
	else:
		return "audio/picon_default.png"

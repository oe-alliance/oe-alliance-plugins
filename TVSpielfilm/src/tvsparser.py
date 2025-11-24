#######################################################################################################
#                                                                                                     #
#  tvsparser is a multiplatform tool (runs on Enigma2 & Windows and probably many others)             #
#  Coded by Mr.Servo @ openATV (c) 2025                                                               #
#  Learn more about the tool by running it in the shell: "python Buildstatus.py -h"                   #
#  ---------------------------------------------------------------------------------------------------#
#  This plugin is licensed under the GNU version 3.0 <https://www.gnu.org/licenses/gpl-3.0.en.html>.  #
#  This plugin is NOT free software. It is open source, you are allowed to modify it (if you keep     #
#  the license), but it may not be commercially distributed. Advertise with this tool is not allowed. #
#  For other uses, permission from the authors is necessary.                                          #
#                                                                                                     #
#######################################################################################################

# PYTHON IMPORTS
from datetime import datetime, timedelta
from getopt import getopt, GetoptError
from html import unescape
from json import dump
from re import compile, search, findall, S
from requests import get, exceptions
from secrets import choice
from sys import exit, argv


class TVSparserGlobals:
	MODULE_NAME = __name__.split(".")[-1]
	WEBURL = bytes.fromhex("687474703a2f2f7777772e7476737069656c66696c6d2e64653"[:-1]).decode()
	MWEBURL = bytes.fromhex("68747470733a2f2f6d2e7476737069656c66696c6d2e64653"[:-1]).decode()
	USERAGENT = choice([
			"Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/129.0.2792.65",
			"Mozilla/5.0 (Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0 Viewer/98.9.5608.9",
			"Mozilla/5.0 (Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/104.0.0.0",
			"Mozilla/5.0 (Mozilla/5.0 (Macintosh; Intel Mac OS X 15.0; rv:130.0) Gecko/20100101 Firefox/130.0",
			"Mozilla/5.0 (Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0 beta 7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15"
			"Mozilla/5.0 (Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.89 Safari/537.36"
			])


tvspglobals = TVSparserGlobals()


class TVSparserHelper:
	def getHTMLdata(self, url, params=None, timeout=(3.05, 6)):
		errMsg, htmldata = "", ""
		headers = {"User-Agent": tvspglobals.USERAGENT}
		try:
			if not headers:
				headers = {}
			response = get(url, params=params, headers=headers, timeout=timeout)
			if response.ok:
				errMsg, htmldata = "", response.text
			else:
				errMsg, htmldata = f"Website access ERROR, response code: {response.raise_for_status()}", ""
			del response
			return errMsg, htmldata
		except exceptions.RequestException as errMsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVcoreHelper:getHTMLdata': {errMsg}")
			return errMsg, htmldata

	def getBinaryData(self, url):
		errMsg, binary = "", None
		headers = {"User-Agent": tvspglobals.USERAGENT}
		try:
			response = get(url, headers=headers, stream=True, timeout=(3.05, 6))
			response.raise_for_status()
			if response.ok:
				errMsg, binary = "", response.content
			else:
				errMsg, binary = f"URL access ERROR, response code: {response.raise_for_status()}", None
			del response
			return errMsg, binary
		except exceptions.RequestException as errMsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'tvsphelper:getBinaryData': {url} - binary data could not be downloaded: {errMsg}")
			return errMsg, binary

	def searchOneValue(self, regex, text, fallback, flags=None):
		text = search(regex, text, flags=flags) if flags else search(regex, text)
		return text.group(1) if text else fallback


tvsphelper = TVSparserHelper()


class TVSparserTips:
	def parseTips(self, callback=None, passthrough=None):
		url = f"{tvspglobals.WEBURL}{bytes.fromhex('2f74762d74697070732f737069656c66696c6d2fb'[:-1]).decode()}"
		errMsg, htmldata = tvsphelper.getHTMLdata(url)
		if errMsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserTips:parseTips': {errMsg}")
			return
		extract = htmldata[htmldata.find('<div class="swiper-wrapper tips-teaser-container ">'):]
		extract = extract[:extract.find('class="recommendations-box clear">')]
		tipsDicts = []
		for entry in findall('<a href=(.*?)</a>', extract, S):
			entry = f"<a href={entry}</a>"  # add search patterns
			tipId = tvsphelper.searchOneValue(r'data-id="BC(.*?)"', entry, "")
			if tipId:
				title = unescape(tvsphelper.searchOneValue(r'title="(.*?)"', entry, ""))
				genre = tvsphelper.searchOneValue(r'<span class="detail-genre">(.*?)</span>', entry, "")  # e.g. 'Katastrophenaction'
				category = tvsphelper.searchOneValue(r'<span class="tips-teaser__top__category">(.*?)</span>', entry, "")  # e.g. 'SP' for 'Spielfilm'
				intro = tvsphelper.searchOneValue(r'<div class="tips-teaser__bottom__intro">(.*?)</div>', entry, "")  # e.g. 'heute | 20:15 | ZDF'
				intros = intro.split(" | ") or []
				timeStartTs, hourmin = None, datetime.strptime(intros[1], '%H:%M').time() if len(intros) > 1 else None
				now = datetime.now(tz=None)
				if hourmin and intros:
					if "heute" in intros[0]:
						timeStartTs = int(datetime.combine(now, hourmin).timestamp())
					else:
						timeStartTs = int(datetime.combine(datetime.strptime(f"{intros[0]}{now.year}", '%d.%m.%Y'), hourmin).timestamp())
				channelName = intros[2] if len(intros) > 2 else ""
				timeInfos = intros[0] or ""
				timeInfos += f" | {intros[1]} Uhr" if len(intros) > 1 else ""
				rating = tvsphelper.searchOneValue(r'<div class=\"tips-teaser__bottom__top-rating-text\">(.*?)</div>', entry, "").lower()
				# 'TOP BEWERTET': Highlights, wenn sie von der TVSpielfilm-Redaktion einen 'Daumen hoch'und eine IMDb-Bewertung von über 7,0 erhalten haben.
				isTip, thumbIdNumeric, imdbRating = (True, 3, "TOP") if "top bewertet" in rating else (False, 0, "")
				new = tvsphelper.searchOneValue(r'<div class=\"tips-teaser__bottom__new-text\">(.*?)</div>', entry, "").lower()
				isNew = True if "neu" in new else False
				isTopTip = False  # none of them
				imgUrl = tvsphelper.searchOneValue(r'<img src="(.*?)" width', entry, "")
				channelId = tvsphelper.searchOneValue(r'mini/(.*?).png', entry, "").lower()
				assetUrl = tvsphelper.searchOneValue(r'<a href="(.*)"', entry, "")
				# not supported/used for the moment: timeEndTs, countryYear, titleLength, imdbRating, fskText, conclusion, fsk
				tipsDicts.append({"tipId": tipId, "channelName": channelName, "channelId": channelId, "timeStart": timeStartTs,
								"timeInfos": timeInfos, "title": title, "genre": genre, "category": category,
								"imdbRating": imdbRating, "isTopTip": isTopTip, "isTip": isTip, "isNew": isNew,
								"thumbIdNumeric": thumbIdNumeric, "imgUrl": imgUrl, "assetUrl": assetUrl})
		if callback:
			if passthrough:
				callback(tipsDicts, passthrough)
			else:
				callback(tipsDicts)
		else:
			return tipsDicts


tvsptips = TVSparserTips()


class TVSparserChannels:
	def parseChannels(self, callback=None):
		url = f"{tvspglobals.WEBURL}{bytes.fromhex('2f73656e6465722ff'[:-1]).decode()}"
		errMsg, htmldata = tvsphelper.getHTMLdata(url)
		if errMsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserChannels:parseChannelList': {errMsg}")
			return []
		extract = htmldata[htmldata.find('<div class="my-channels">'):]
		extract = extract[:extract.find('</div>')]
		channelDicts = []
		for catSet in findall(r'<h2 class="headline headline--section"(.*?)</ul>', extract, flags=S):
			category = search(r'>(.*?)</h2>', catSet)
			category = unescape(category.group(1)) if category else ""  # e.g. ['Hauptsender', 'Auslandssender', 'Spartensender', 'News und Dokus', 'Dritte Programme', 'Sportsender', 'Kindersender', 'Musiksender', 'Shopping', 'Regionalsender', 'Sky Cinema', 'Pay TV', 'Sky Sport', 'Sky Entertainment']
			regex = '/tv-programm/sendungen/(.*?).html"'
			channellist = findall(compile(regex), catSet)
			for channel in channellist:
				if channel and len(channel) > 0:
					channelId = channel.split(",")[1].lower()
					channelDicts.append({"channelId": channelId, "category": category})
		if callback:
			callback(channelDicts)
		return channelDicts


tvspchannels = TVSparserChannels()


class TVSparserAssets:
	spanSets = {"05:00-14:00": "5", "14:00-18:00": "14", "18:00-20:00": "18", "20:00-22:00": "20", "20:15": "prime", "22:00-00:00": "22", "00:00-05:00": "0"}
	# also existing but not used: {"jetzt": "now", "gleich": "shortly",  "abends": "primetips", "ganzer Tag": "day"}
	catFilters = {"Spielfilm": "SP", "Serie": "SE", "Report": "RE", "Unterhaltung": "U", "Kinder": "KIN", "Sport": "SPO", "Andere": "AND"}
	channelSets = {"Hauptsender": "g:1", "Dritte Programme": "g:2", "Sportsender": "g:8", "Spartensender ARD & ZDF": "g:4103125",
					"News und Doku": "g:11", "Kindersender": "g:10", "Ausland (deutschspr.)": "g:4", "Regionalsender": "g:3",
					"Musiksender": "g:9", "Spartensender": "g:3534866", "Shopping": "g:7", "Sky Cinema": "g:21", "Sky Sport": "g:13",
					"Sky Entertainment": "g:3738244", "Pay-TV": "g:19", "Auslandssender": "g:12"}

	def __init__(self):
		pass

	def getChannelAssets(self, channelIds=[], dateOnlyStr=None, timeCode=None):
		pagesList = []
		for channelId in channelIds:
			errMsg, assetsDicts = self.parseChannelPage(channelId, dateOnlyStr=dateOnlyStr, timeCode=timeCode)
			if errMsg:
				print(f"[{tvspglobals.MODULE_NAME}] Error when parsing channel '{channelId}': {errMsg}")
			else:
				print(f"[{tvspglobals.MODULE_NAME}] Successfully parsed channel '{channelId}'")
				pagesList += assetsDicts
		return pagesList

	def parseChannelPage(self, channelId, dateOnlyStr=None, timeCode=None, tips=None, categories=[]):
		def setAssetKey(key, value):
			if value:
				assetDict[key] = value
		now = datetime.now(tz=None)
		url = f"{tvspglobals.MWEBURL}{bytes.fromhex('2f73756368652e68746d6c1'[:-1]).decode()}"
		dateOnlyDt = datetime.fromisoformat(dateOnlyStr) if dateOnlyStr else now  # fallback to today
		# In case desired time span is between 00:00 and 05:00, request data from previous day
		# Server philosophy: The server considers a day to be the period from 5:00 a.m. to 5:00 a.m. the following day.
		midnight = dateOnlyDt.replace(hour=0, minute=0, second=0, microsecond=0)
		morning = dateOnlyDt.replace(hour=5, minute=0, second=0, microsecond=0)
		corrStartStr = (dateOnlyDt + timedelta(days=-1)).strftime("%F") if timeCode == "0" or timeCode == "now" and now >= midnight and now < morning else dateOnlyDt
		finish = False
		assetsDicts = []
		index, offset = 0, 0
		while True:
			params = {
					"offset": offset,  # offset=20 means assets #20...#39
					"filter": 1 if categories else None,  # None = all filters active |'1' = selected filters
					"order": None,  # sort order 'time' or 'channel', ('time' is default)
					"date": corrStartStr,  # e.g. '2025-05-18'
					"tips": tips,  # '1' = load tips only, ('None' is default)
					"cat[]": [self.catFilters.get(catFilter) for catFilter in categories],   # e.g. ["Spielfilm", "Report"] -> ['SP', 'RE']
					"time": timeCode or "prime",  # for details see dict {spanSets}
					"channel": channelId  # e.g. 'ARD' for 'Das Erste'
					}
			errMsg, htmldata = tvsphelper.getHTMLdata(url, params)
			if errMsg:
				print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserAssets:parseChannelPage': {errMsg}")
				return errMsg, []
			limit = 5 if timeCode == "now" else 0  # 'Jetzt im TV' needs only the first 5 assets per channel
			extract = htmldata[htmldata.find('<div class="row component tv-tip-list">'):htmldata.find('<div class="row component category-select">')]
			for entry in findall(r'<li class="tv-tip time-listing js-tv-show"(.*?)</li>', extract, S):
				if limit and index > limit:
					finish = True
					break
				assetDict = {}
				setAssetKey("id", tvsphelper.searchOneValue(r'data-id="(.*?)"', entry, ""))
				setAssetKey("title", unescape(tvsphelper.searchOneValue(r'<span class="title">(.*?)</span>', entry, "")))
				genretime = tvsphelper.searchOneValue(r'<span class="genre-time">(.*?)</span>', entry, "").split(" | ")
				setAssetKey("countryYear", genretime[0].upper())  # e.g. 'SP' for 'Spielfilm'
				setAssetKey("genre", genretime[1] if len(genretime) > 1 else "")  # e.g. 'Katastrophenaction'
				itholder = tvsphelper.searchOneValue(r'<div class="image-text-holder">(.*?)</a>', entry, "", flags=S)
				pageElement = tvsphelper.searchOneValue(r'"pageElementCreative":"(.*?)"', itholder, "").split("|")  # "the-big-bang-theory|pro7|se|daumen-hoch|sitcom|komoedie|0|0"
				channelId = pageElement[1].lower()
				setAssetKey("category", pageElement[2].upper())
				thumbIdnumeric = tvsphelper.searchOneValue(r'<span class="listing-icon rating-(.*?)"></span>', itholder, "0")
				setAssetKey("thumbIdNumeric", int(thumbIdnumeric) if thumbIdnumeric.isdigit() else 0)
#               setAssetKey("isTopTip", False)  # not supported for the moment
				setAssetKey("isTip", itholder.find('<span class="add-info icon-tip">TIPP</span>') > -1)
				setAssetKey("isNew", itholder.find('<span class="add-info icon-new">NEU</span>') > -1)
				setAssetKey("isLive", itholder.find('<span class="add-info icon-tip">Live</span>') > -1)
				setAssetKey("channelId", channelId)
				setAssetKey("channelName", tvsphelper.searchOneValue(r'<span class="c">(.*?)</span>', itholder, ""))
				timeStartStr = tvsphelper.searchOneValue(r'data-start-time="(.*?)"', entry, "")
				timeStartTs = int(timeStartStr) if timeStartStr.isdigit() else 0
				timeEndStr = tvsphelper.searchOneValue(r'data-end-time="(.*?)"', entry, "")
				timeEndTs = int(timeEndStr) if timeEndStr.isdigit() else 0
				setAssetKey("timeStart", f"{datetime.fromtimestamp(timeStartTs).isoformat()}+00:00")
				setAssetKey("timeEnd", f"{datetime.fromtimestamp(timeEndTs).isoformat()}+00:00")
				setAssetKey("assetUrl", tvsphelper.searchOneValue(r'<div class="image-text-holder">\s*<a href="(.*?)"', entry, "", flags=S).replace("https://m.", "https://"))
				assetsDicts.append(assetDict)
				index += 1
			if finish or extract.find('<span>Weitere Sendungen</span>') == -1:
				break
			offset += 20  # offset for the next 20 assets (=next page)
		return errMsg, assetsDicts

	def resolveTrailerUrl(self, cid, lic):
		url = f"{bytes.fromhex('68747470733A2F2F6D656469612D6170692D70726F642E677265656E766964656F2E696F2F6170692F76312F636F6E74656E742F3'[:-1]).decode()}{cid}"
		headers = {
					"User-Agent": tvspglobals.USERAGENT,
					"Accept": "*/*",
					"Accept-Language": "de,en-US;q=0.7,en;q=0.3",
					"Accept-Encoding": "gzip, deflate, zstd",
					"Connection": "keep-alive",
					bytes.fromhex("52656665726572E"[:-1]).decode(): bytes.fromhex("68747470733A2F2F7777772E7476737069656C66696C6D2E64652FE"[:-1]).decode(),
					bytes.fromhex("782D646C382D6C6963656E73656B65794"[:-1]).decode(): lic,
					bytes.fromhex("4F726967696EE"[:-1]).decode(): bytes.fromhex("68747470733A2F2F7777772E7476737069656C66696C6D2E64651"[:-1]).decode(),
					bytes.fromhex("5365632D4750433"[:-1]).decode(): bytes.fromhex("311"[:-1]).decode(),
					bytes.fromhex("5365632D46657463682D44657374A"[:-1]).decode(): bytes.fromhex("656D7074796"[:-1]).decode(),
					bytes.fromhex("5365632D46657463682D4D6F6465D"[:-1]).decode(): bytes.fromhex("636F72738"[:-1]).decode(),
					bytes.fromhex("5365632D46657463682D536974657"[:-1]).decode(): bytes.fromhex("63726F73732D73697465A"[:-1]).decode()
					}
		try:
			response = get(url, headers=headers, timeout=(3.05, 6))
			if response.ok:
				trailerDicts = response.json().get("result", {}).get("videoRenditions", {})
				return trailerDicts[0].get("src", "") if trailerDicts else ""
			else:
				print(f"[{tvspglobals.MODULE_NAME}] API server access ERROR, response code: {response.raise_for_status()}")
		except exceptions.RequestException as errMsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserAssets:resolveTrailerUrl': {errMsg}")
		return ""

	def parseSingleAsset(self, assetUrl):
		def setAssetKey(key, value):
			if value:
				assetDict[key] = value

		errMsg, htmldata = tvsphelper.getHTMLdata(assetUrl)
		if errMsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserAssets:parseSingleAsset': {errMsg}")
			return errMsg, {}
		extract = htmldata[htmldata.find('<div class="content-area">'):]
		extract = extract[:extract.find('<div class="schedule-widget__tabs">')]
		title = unescape(tvsphelper.searchOneValue(r'<h1 class="headline headline--article broadcast stage-heading">(.*?)</h1>', extract, ""))
		block = tvsphelper.searchOneValue(r'<span class="text-row">(.*?)</span></div>', extract, "").split(" | ")
		countryYear = block[0] if block else ""
		if len(block) > 1:
			genre = block[1][:block[1].find("</span>")] if "</span>" in block[1] else block[1]
		else:
			genre = ""
		repeatHint = unescape(tvsphelper.searchOneValue(r'<span class="text-row repeat">(.*?)</span>', f"{block[1].replace('</span>', '')}</span>", "")) if len(block) > 1 else ""
		serialinfo = tvsphelper.searchOneValue(r'<section class="serial-info">\s*<span>(.*?)</span>', extract, "").split(",")
		len_serialinfo = len(serialinfo)
		seasonNumber = serialinfo[0].replace("Staffel", "").strip() if len_serialinfo > 1 else ""
		episodeNumber = serialinfo[len_serialinfo - 1].replace("Folge", "").strip()
		category = tvsphelper.searchOneValue(r'"epgCategory1" : "(.*?)",', htmldata, "").upper()  # e.g. "SP" for 'Spielfilm'
		conclusion = tvsphelper.searchOneValue(r'<blockquote class="content-rating__rating-genre__conclusion-quote">(.*?)</blockquote>', extract, "", flags=S)
		conclusion = unescape(conclusion.replace("<p>", "").replace("</p>", "").strip())
		broadblock = tvsphelper.searchOneValue(r'<div class="schedule-widget__header__attributes">(.*?)</div>', extract, "", flags=S)
		broadblock = findall(r'<li>(.*)</li>', broadblock) or ["", "", ""]  # e.g. 'Heute | 20:15 Uhr - 21:45 Uhr | Das Erste'
		timeStartEnd = broadblock[1].split(" - ") if broadblock[1] else ""
		timeStartTs, startHourmin = None, datetime.strptime(timeStartEnd[0].replace(" Uhr", ""), '%H:%M').time() if timeStartEnd else None
		timeEndTs, endHourmin = None, datetime.strptime(timeStartEnd[1].replace(" Uhr", ""), '%H:%M').time() if len(timeStartEnd) > 1 else None
		now = datetime.now(tz=None)
		if "heute" in broadblock[0].lower():
			timeStartTs = int(datetime.combine(now, startHourmin).timestamp()) if startHourmin else ""
			timeEndTs = int(datetime.combine(now, endHourmin).timestamp()) if endHourmin else ""
		else:
			daydate = broadblock[0][broadblock[0].find(",") + 2:]  # convert 'Fr., 23.05.' -> '23.05.'
			timeStartTs = int(datetime.combine(datetime.strptime(f"{daydate}{now.year}", '%d.%m.%Y'), startHourmin).timestamp()) if startHourmin else ""
			timeEndTs = int(datetime.combine(datetime.strptime(f"{daydate}{now.year}", '%d.%m.%Y'), endHourmin).timestamp()) if endHourmin else ""
		channelName = broadblock[2] if len(broadblock) > 2 else ""
		channelId = tvsphelper.searchOneValue(r'"pageElementCreative":"(.*?)"', extract, "").upper().replace("N\\/A", "").lower()
		imgUrl = tvsphelper.searchOneValue(r'<picture class=".*?">\s*<img src="(.*?)" width', extract, "", flags=S)
		if not imgUrl:  # alternative search
			imgUrl = tvsphelper.searchOneValue(r'--tv-detail ">\s*<img src="(.*?)" alt', extract, "", flags=S)
			if not imgUrl:  # alternative search for assets with trailer
				imgUrl = tvsphelper.searchOneValue(r'<div class="tips-teaser__image">\s*<img src="(.*?)"\s*width', extract, "", flags=S)
		imgCredits = tvsphelper.searchOneValue(r'<span class="credit">(.*?)</span>', extract, "")
		access = tvsphelper.searchOneValue(r'<script src="(.*?)"></script>', extract, "")
		access = access[access.find("key=") + 4:] if access else ""
		cid = tvsphelper.searchOneValue(r'content-id="(.*?)"', extract, "")
		lic = tvsphelper.searchOneValue(r'data-license-key="(.*?)"', extract, "")
		trailerData = f"{cid},{lic}" if cid and lic else ""
		descblock = tvsphelper.searchOneValue(r'<section class="broadcast-detail__description">(.*?)</section>', extract, "", flags=S)
		preview = tvsphelper.searchOneValue(r'<p class="headline">(.*?)</p>', descblock, "")
		text = unescape(tvsphelper.searchOneValue(r'<p>(.*?)</p>', descblock, "")).replace("<br/>", "\n").replace('&amp;', '&')
		infoblock = tvsphelper.searchOneValue(r'<p class="headline">Infos</p>(.*?)<p class="headline headline--spacing">', extract, "", flags=S)
		infodict = dict(findall(r'<dt>(.*?)</dt>\s*<dd>(.*?)</dd>', infoblock, flags=S))
		country, firstyear, length = infodict.get("Land", ""), infodict.get("Jahr", ""), infodict.get("Länge", "")
		fsk = infodict.get("FSK", "-1")[:2]
		fsk = int(fsk) if fsk.isdigit() else -1
		crewblock = tvsphelper.searchOneValue(r'<p class="headline headline--spacing">Crew</p>(.*?)</div>', extract, "", flags=S)
		crewblock = findall(r'<dt>(.*?)</dt>\s*<dd>\s*(.*?)\s*</dd>', crewblock, flags=S)
		crewdict = {}
		crewdict["crew"] = {}
		for crew in crewblock:
			role = crew[0].strip()
			name = tvsphelper.searchOneValue(r'title="(.*?)"', crew[1], "")
			if not name:  # alternatively, in case of missing photo of this crew member
				name = crew[1]
			namelist = crewdict.get(role, [])
			namelist.append(name)
			crewdict["crew"][role] = namelist
		castblock = tvsphelper.searchOneValue(r'<p class="headline">Cast</p>(.*?)</dl>', extract, "", flags=S)
		castblock = findall(r'<dt>(.*?)</dt>\s*<dd>\s*(.*?)\s*</dd>', castblock, flags=S)
		castdict = {}
		castdict["cast"] = {}
		for cast in castblock:
			role = cast[0].strip()
			name = tvsphelper.searchOneValue(r'title="(.*?)"', cast[1], "")
			if not name:  # alternatively, in case there is no photo of this actor
				name = cast[1]
			namelist = castdict.get(role, [])
			namelist.append(name)
			castdict["cast"][role] = namelist
		thumbIdnumeric = tvsphelper.searchOneValue(r'<div class="content-rating__rating-genre__thumb rating-(.*?)"></div>', extract, "0")
		thumbIdnumeric = int(thumbIdnumeric) if thumbIdnumeric.isdigit() else 0
		isTopTip = "TOP BEWERTET" in tvsphelper.searchOneValue(r'<div class="content-rating__top-rated">(.*?)</div>', extract, "").upper()
		isTip, isNew, isLive = False, False, False
		addinfo = tvsphelper.searchOneValue(r'<ul class="set-list">(.*?)</ul>', extract, "")
		for info in findall(r'<span class="add-info icon-tip nodistance">(.*?)</span>', addinfo):
			isTip = True if not isTip and "TIPP" in info else isTip
			isNew = True if not isNew and "NEU" in info else isNew
			isLive = True if not isLive and "LIVE" in info else isLive
		ratingblock = tvsphelper.searchOneValue(r'<ul class="content-rating__rating-genre__list">(.*?)</ul>', extract, "", flags=S)
		ratingblock = findall(r'<li class="content-rating__rating-genre__list-item">(.*?)</li>', ratingblock, flags=S)
		ratingdict = {}
		for rating in ratingblock:
			label = tvsphelper.searchOneValue(r'<span class="content-rating__rating-genre__list-item__label">(.*?)</span>', rating, "")
			label = label.replace("Humor", "ratingHumor").replace("Anspruch", "ratingDemanding").replace("Action", "ratingAction").replace("Spannung", "ratingSuspense").replace("Erotik", "ratingErotic")
			rating = tvsphelper.searchOneValue(r'class="content-rating__rating-genre__list-item__rating rating-(.*?)">', rating, "-1")
			rating = int(rating) if rating.isdigit() else -1
			ratingdict[label] = rating
		imdbRating = tvsphelper.searchOneValue(r'<div class="content-rating__imdb-rating__rating-value">(.*?)</div>', extract, "")
		assetDict = {}
		setAssetKey("title", title)
		setAssetKey("category", category)
		setAssetKey("genre", genre)
		setAssetKey("length", length)
		setAssetKey("countryYear", countryYear)
		setAssetKey("firstYear", firstyear)
		setAssetKey("country", country)
		setAssetKey("preview", preview)
		setAssetKey("text", text)
		setAssetKey("conclusion", conclusion)
		setAssetKey("thumbIdNumeric", thumbIdnumeric)
		setAssetKey("isTopTip", isTopTip)
		setAssetKey("isTip", isTip)
		setAssetKey("isNew", isNew)
		setAssetKey("isLive", isLive)
		assetDict.update(ratingdict)
		setAssetKey("imdbRating", imdbRating)
		assetDict.update(crewdict)
		assetDict.update(castdict)
		setAssetKey("fsk", fsk)
		setAssetKey("imgUrl", imgUrl)
		setAssetKey("imgCredits", imgCredits)
		setAssetKey("trailerData", trailerData)
		setAssetKey("channelId", channelId)
		setAssetKey("channelName", channelName)
		setAssetKey("seasonNumber", seasonNumber)
		setAssetKey("episodeNumber", episodeNumber)
		setAssetKey("repeatHint", repeatHint)
		setAssetKey("timeStart", f"{datetime.fromtimestamp(timeStartTs).isoformat()}+00:00" if timeStartTs else "")
		setAssetKey("timeEnd", f"{datetime.fromtimestamp(timeEndTs).isoformat()}+00:00" if timeEndTs else "")
		setAssetKey("assetUrl", assetUrl)
		return errMsg, assetDict


tvspassets = TVSparserAssets()


def main(argv):  # shell interface
	filename = ""
	jsonList = []
	helpstring = "tvsparser v1.0: try 'python Buildstatus.py -h' for more information"
	try:
		opts, args = getopt(argv, "j:anchst", ["json=", "assetslist=", "now", "channellist=", "help", "singleasset=", "tipslist="])
	except GetoptError as error:
		print(f"Error: {error}\n{helpstring}")
		exit(2)
	currDateStr = datetime.now().strftime("%F")
	for opt, arg in opts:
		opt = opt.lower().strip()
		arg = arg.strip()
		if not opts or opt == "-h":
			print("Usage 'tvsparser v1.0': python tvsparser.py [option...] <data>\n"
			"-a, --assetslist\tget list of assets of a channel (details: see code)\n"
			"-n, --now\t\t\tget list of assets of currently running programs (details: see code)\n"
			"-c, --channellist\t\tget list of all supported channels\n"
			"-h, --help\t\t\tget an overview of the options\n"
			"-s, --single\t\t\tget a single asset (url: see code)\n"
			"-t, --tipslist\t\t\tget all TV-tips\n"
			"-j, --json <filename>\t\tFile output formatted in JSON\n")
			exit()
		elif opt in ("-a", "--assetslist"):
			jsonList = tvspassets.getChannelAssets(["ZDF"], dateOnlyStr=currDateStr, timeCode="0")
		elif opt in ("-n", "--new"):
			jsonList = tvspassets.getChannelAssets(["ARD"], dateOnlyStr=currDateStr, timeCode="now")
		elif opt in ("-c", "--channellist"):
			jsonList = tvspchannels.parseChannels()
		elif opt in ("-j", "--json"):
			filename = arg
		elif opt in ("-s", "--single"):
			errMsg, jsonList = tvspassets.parseSingleAsset("https://www.tvspielfilm.de/tv-programm/sendung/schtonk,68b6f1817d255456791151e0.html")
			if errMsg:
				print("errMsg")
		elif opt in ("-t", "--tipslist"):
			jsonList = tvsptips.parseTips()
	if jsonList and filename:
		with open(filename, "w") as file:
			dump(jsonList, file)
		print(f"JSON file '{filename}' was successfully created.")


if __name__ == "__main__":
	main(argv[1:])

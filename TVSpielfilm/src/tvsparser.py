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
from json import dump, loads
from re import compile, search, findall, S
from requests import get, exceptions
from secrets import choice
from sys import exit, argv


class TVSparserGlobals():
	MODULE_NAME = __name__.split(".")[-1]
	WEBURL = bytes.fromhex("687474703a2f2f7777772e7476737069656c66696c6d2e64653"[:-1]).decode()
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


class TVSparserHelper():
	def getHTMLdata(self, url, params=None, timeout=(3.05, 6)):
		headers = {"User-Agent": tvspglobals.USERAGENT}
		errmsg, htmldata = "", ""
		try:
			if not headers:
				headers = {}
			response = get(url, params=params, headers=headers, timeout=timeout)
			response.raise_for_status()
			if response.ok:
				errmsg, htmldata = "", response.text
			else:
				errmsg, htmldata = f"Website access ERROR, response code: {response.raise_for_status()}", ""
			del response
			return errmsg, htmldata
		except exceptions.RequestException as errmsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVcoreHelper:getHTMLdata': {errmsg}")
			return errmsg, htmldata

	def searchOneValue(self, regex, text, fallback, flags=None):
		text = search(regex, text, flags=flags) if flags else search(regex, text)
		return text.group(1) if text else fallback


tvsphelper = TVSparserHelper()


class TVSparserTips():
	def parseTips(self, callback=None, passthrough=None):
		url = f"{tvspglobals.WEBURL}{bytes.fromhex('2f74762d74697070732f737069656c66696c6d2fb'[:-1]).decode()}"
		errmsg, htmldata = tvsphelper.getHTMLdata(url)
		if errmsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserTips:parseTips': {errmsg}")
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
				if hourmin and intros:
					if "heute" in intros[0]:
						timeStartTs = int(datetime.combine(datetime.today(), hourmin).timestamp())
					else:
						timeStartTs = int(datetime.combine(datetime.strptime(f"{intros[0]}{datetime.today().year}", '%d.%m.%Y'), hourmin).timestamp())
				channelName = intros[2] if len(intros) > 2 else ""
				timeInfos = intros[0] or ""
				timeInfos += f" | {intros[1]} Uhr" if len(intros) > 1 else ""
				rating = tvsphelper.searchOneValue(r'<div class=\"tips-teaser__bottom__top-rating-text\">(.*?)</div>', entry, "").lower()
				# 'TOP BEWERTET': Highlights, wenn sie von der TVSpielfilm-Redaktion einen 'Daumen hoch'und eine IMDb-Bewertung von über 7,0 erhalten haben.
				isTipOfTheDay, thumbIdNumeric, imdbRating = (True, 2, "TOP") if "top bewertet" in rating else (False, -1, "")
				new = tvsphelper.searchOneValue(r'<div class=\"tips-teaser__bottom__new-text\">(.*?)</div>', entry, "").lower()
				isNew = True if "neu" in new else False
				isTopTip = False  # none of them
				imgUrl = tvsphelper.searchOneValue(r'<img src="(.*?)" width', entry, "")
				channelId = tvsphelper.searchOneValue(r'mini/(.*?).png', entry, "").lower()
				assetUrl = tvsphelper.searchOneValue(r'<a href="(.*)"', entry, "")
				# not supported/used for the moment: timeEndTs, countryYear, titleLength, imdbRating, fskText, conclusion, fsk
				tipsDicts.append({"tipId": tipId, "channelName": channelName, "channelId": channelId, "timeStart": timeStartTs,
								"timeInfos": timeInfos, "title": title, "genre": genre, "category": category,
								"imdbRating": imdbRating, "isTopTip": isTopTip, "isTipOfTheDay": isTipOfTheDay, "isNew": isNew,
								"thumbIdNumeric": thumbIdNumeric, "imgUrl": imgUrl, "assetUrl": assetUrl})
		if callback:
			if passthrough:
				callback(tipsDicts, passthrough)
			else:
				callback(tipsDicts)
		else:
			return tipsDicts


tvsptips = TVSparserTips()


class TVSparserChannels():
	def parseChannels(self, callback=None):
		url = f"{tvspglobals.WEBURL}{bytes.fromhex('2f73656e6465722ff'[:-1]).decode()}"
		errmsg, htmldata = tvsphelper.getHTMLdata(url)
		if errmsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserChannels:parseChannelList': {errmsg}")
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


class TVSparserAssets():
	spanSets = {"00:00-05:00": "0", "05:00-14:00": "5", "14:00-18:00": "14", "18:00-20:00": "18", "20:00-22:00": "20", "20:15": "prime", "22:00-00:00": "22"}
	# also existing but not used: {"jetzt": "now", "gleich": "shortly",  "abends": "primetips", "ganzer Tag": "day"}
	catFilters = {"Spielfilm": "SP", "Serie": "SE", "Report": "RE", "Unterhaltung": "U", "Kinder": "KIN", "Sport": "SPO", "Andere": "AND"}
	channelSets = {"Hauptsender": "g:1", "Dritte Programme": "g:2", "Sportsender": "g:8", "Spartensender ARD & ZDF": "g:4103125",
					"News und Doku": "g:11", "Kindersender": "g:10", "Ausland (deutschspr.)": "g:4", "Regionalsender": "g:3",
					"Musiksender": "g:9", "Spartensender": "g:3534866", "Shopping": "g:7", "Sky Cinema": "g:21", "Sky Sport": "g:13",
					"Sky Entertainment": "g:3738244", "Pay-TV": "g:19", "Auslandssender": "g:12"}

	def __init__(self):
		pass

	def getChannelAssets(self, channelIds=[], dateStr=None, timeCode=None):
		pagesList = []
		for channelId in channelIds:
			errmsg, pageAssets, lastPage = self.parseChannelPage(channelId, dateStr=dateStr, timeCode=timeCode)
			if errmsg:
				print(f"Error when parsing page #1 of channel '{channelId}': {errmsg}")
			else:
				print(f"Succesfully parsed page #1 of channel '{channelId}'")
				pagesList += pageAssets
		return pagesList

	def parseChannelPage(self, channelId, dateStr=None, timeCode=None, page=1, order=None, tips=None, categories=[]):
		url = f"{tvspglobals.WEBURL}{bytes.fromhex('2f74762d70726f6772616d6d2f73656e64756e67656e2f1'[:-1]).decode()}"
		if timeCode == "0" and dateStr:  # if timespanStart = '00:00' -> use yesterday (server philosophy)
			dateStr = (datetime.fromisoformat(dateStr) + timedelta(days=-1)).strftime("%F")
		params = {
				"page": page,  # 1 | 2 | ...
				"filter": 1 if categories else None,  # None = all filters active |'1' = selected filters
				"order": order,  # sort order 'time' or 'channel', ('time' is default)
				"date": dateStr or datetime.today().strftime("%F"),  # e.g. '2025-05-18'
				"tips": tips,  # '1' = load tips only, ('None' is default)
				"cat[]": [self.catFilters.get(catFilter) for catFilter in categories],   # e.g. ["Spielfilm", "Report"] -> ['SP', 'RE']
				"time": timeCode or "prime",  # for details see dict {self.spanSets}
				"channel": channelId  # e.g. 'ARD' for 'Das Erste'
				}
		errmsg, htmldata = tvsphelper.getHTMLdata(url, params)
		if errmsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserAssets:parseChannelPage': {errmsg}")
			return errmsg, [], 0
		pageAssets = []
		pagination = tvsphelper.searchOneValue(r'<ul class="pagination__items">(.*?)</ul>', htmldata, "", flags=S)
		lastPage = len(findall(r'href="(.*?)"', pagination, S))
		extract = htmldata[htmldata.find(r'<table class="info-table">'):htmldata.find('<ul class="pagination__items">')]
		for entry in findall(r'<tr class="hover">(.*?)</tr>', extract, S):
			title = unescape(tvsphelper.searchOneValue(r'<strong>(.*?)</strong>\s*</a>', entry, ""))
			if not title:  # alternative search
				title = unescape(tvsphelper.searchOneValue(r'<div class="programm-listing-livetv">\s*<a title="(.*?)"', entry, "", flags=S))
			col3block = tvsphelper.searchOneValue(r'<td class="col-3">(.*?)</td>', entry, "", flags=S)
			spanblock = tvsphelper.searchOneValue(r'<span>\s*<a href=(.*?)\s*</span>', col3block, "", flags=S)
			assetUrl, countryYear = "", ""
			if spanblock:
				spanblock = f"<a href={spanblock}"
				assetUrl = tvsphelper.searchOneValue(r'<a href="(.*?)"', spanblock, "")
				longtitles = tvsphelper.searchOneValue(r'title="(.*)" ', spanblock, "").split(", ")
				countryYear = longtitles[-1] if len(longtitles) > 1 else ""
			datastr = tvsphelper.searchOneValue(r"data-tracking-point=(.*?) data-tracking-datalayer", col3block, "").strip("'")
			col3json = loads(datastr)
			channelName = tvsphelper.searchOneValue(r'title="(.*?) Programm"', entry, "")
			fsk = tvsphelper.searchOneValue(r'<td class="col-5">.*?<em>ab (.*?) Jahren</em>', entry, "", flags=S).strip()
			fsk = int(fsk) if fsk.isdigit() else -1
			thumbIdnumeric = tvsphelper.searchOneValue(r'class="editorial-rating small(.*?)"', entry, "0")
			thumbIdnumeric = int(thumbIdnumeric) if thumbIdnumeric.isdigit() else 0
			timeStartTs = tvsphelper.searchOneValue(r'data-rel-start="(.*?)"', entry, "")
			timeStartTs = int(timeStartTs) if timeStartTs.isdigit() else 0
			timeEndTs = tvsphelper.searchOneValue(r'data-rel-end="(.*?)"', entry, "")
			timeEndTs = int(timeEndTs) if timeEndTs.isdigit() else 0
			assetDict = {}
			assetDict["title"] = title
			assetDict["genre"] = col3json.get("category1", "")  # e.g. 'Katastrophenaction'
			assetDict["category"] = col3json.get("genre", "")  # e.g. 'SP' for 'Spielfilm'
			assetDict["countryYear"] = countryYear
			assetDict["thumbIdNumeric"] = thumbIdnumeric
			assetDict["isTopTip"] = False  # not supported for the moment
			assetDict["isTipOfTheDay"] = True if col3json.get("tipp", 0) == 1 else False
			assetDict["isNew"] = False  # not supported for the moment
			assetDict["fsk"] = fsk
			assetDict["channelId"] = col3json.get("channel", "").lower()
			assetDict["channelName"] = channelName
			assetDict["timeStart"] = f"{datetime.fromtimestamp(timeStartTs).isoformat()}+00:00"
			assetDict["timeEnd"] = f"{datetime.fromtimestamp(timeEndTs).isoformat()}+00:00"
			assetDict["assetUrl"] = assetUrl
			pageAssets.append(assetDict)
		return errmsg, pageAssets, lastPage

	def parseSingleAsset(self, assetUrl):
		errmsg, htmldata = tvsphelper.getHTMLdata(assetUrl)
		if errmsg:
			print(f"[{tvspglobals.MODULE_NAME}] ERROR in class 'TVSparserTips:parseSingleAsset': {errmsg}")
			return errmsg, {}
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
		if "heute" in broadblock[0].lower():
			timeStartTs = int(datetime.combine(datetime.today(), startHourmin).timestamp()) if startHourmin else ""
			timeEndTs = int(datetime.combine(datetime.today(), endHourmin).timestamp()) if endHourmin else ""
		else:
			daydate = broadblock[0][broadblock[0].find(",") + 2:]  # convert 'Fr., 23.05.' -> '23.05.'
			timeStartTs = int(datetime.combine(datetime.strptime(f"{daydate}{datetime.today().year}", '%d.%m.%Y'), startHourmin).timestamp()) if startHourmin else ""
			timeEndTs = int(datetime.combine(datetime.strptime(f"{daydate}{datetime.today().year}", '%d.%m.%Y'), endHourmin).timestamp()) if endHourmin else ""
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
		trailerId = tvsphelper.searchOneValue(r'"contentDesc": "(.*?)"', extract, "")
		part0 = bytes.fromhex("68747470733a2f2f6d656469612e64656c696768742e766964656f2fa"[:-1]).decode()
		part1 = bytes.fromhex("2f4d454449412f76302f48442f6d656469612e6d7034f"[:-1]).decode()
		trailerUrl = f"{part0}{access}/{trailerId}{part1}" if access and trailerId else ""
		descblock = tvsphelper.searchOneValue(r'<section class="broadcast-detail__description">(.*?)</section>', extract, "", flags=S)
		preview = tvsphelper.searchOneValue(r'<p class="headline">(.*?)</p>', descblock, "")
		text = unescape(tvsphelper.searchOneValue(r'<p>(.*?)</p>', descblock, ""))
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
		isTipOfTheDay, isNew = False, False
		addinfo = tvsphelper.searchOneValue(r'<ul class="set-list">(.*?)</ul>', extract, "")
		for info in findall(r'<span class="add-info icon-tip nodistance">(.*?)</span>', addinfo):
			isTipOfTheDay = True if not isTipOfTheDay and "TIPP" in info else isTipOfTheDay
			isNew = True if not isNew and "NEU" in info else isNew
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
		assetDict["title"] = title
		assetDict["category"] = category
		assetDict["genre"] = genre
		assetDict["length"] = length
		assetDict["countryYear"] = countryYear
		assetDict["firstYear"] = firstyear
		assetDict["country"] = country
		assetDict["preview"] = preview
		assetDict["text"] = text
		assetDict["conclusion"] = conclusion
		assetDict["thumbIdNumeric"] = thumbIdnumeric
		assetDict["isTopTip"] = isTopTip
		assetDict["isTipOfTheDay"] = isTipOfTheDay
		assetDict["isNew"] = isNew
		assetDict.update(ratingdict)
		assetDict["imdbRating"] = imdbRating
		assetDict.update(crewdict)
		assetDict.update(castdict)
		assetDict["fsk"] = fsk
		assetDict["imgUrl"] = imgUrl
		assetDict["imgCredits"] = imgCredits
		assetDict["trailerUrl"] = trailerUrl
		assetDict["channelId"] = channelId
		assetDict["channelName"] = channelName
		assetDict["seasonNumber"] = seasonNumber
		assetDict["episodeNumber"] = episodeNumber
		assetDict["repeatHint"] = repeatHint
		assetDict["timeStart"] = f"{datetime.fromtimestamp(timeStartTs).isoformat()}+00:00" if timeStartTs else ""
		assetDict["timeEnd"] = f"{datetime.fromtimestamp(timeEndTs).isoformat()}+00:00" if timeEndTs else ""
		assetDict["assetUrl"] = assetUrl
		return errmsg, assetDict


tvspassets = TVSparserAssets()


def main(argv):  # shell interface
	filename = ""
	jsonList = []
	helpstring = "tvsparser v1.0: try 'python Buildstatus.py -h' for more information"
	try:
		opts, args = getopt(argv, "j:achst", ["json=", "assetslist=", "channellist=", "help", "singleasset=", "tipslist="])
	except GetoptError as error:
		print(f"Error: {error}\n{helpstring}")
		exit(2)
	for opt, arg in opts:
		opt = opt.lower().strip()
		arg = arg.strip()
		if not opts or opt == "-h":
			print("Usage 'tvsparser v1.0': python tvsparser.py [option...] <data>\n"
			"-a, --assetslist <options>\tget list of assets of a channel (details: see code)\n"
			"-c, --channellist\tget list of all supported channels\n"
			"-h, --help\t\tget an overview of the options\n"
			"-s, --single\tget a single asset (url: see code)\n"
			"-t, --tipslist\t\tget all TV-tips\n"
			"-j, --json <filename>\tFile output formatted in JSON\n")
			exit()
		elif opt in ("-a", "--assetslist"):
			jsonList = tvspassets.getChannelAssets(["ARD", "ZDF", "WDR", "RTL"])
		elif opt in ("-c", "--channellist"):
			jsonList = tvspchannels.parseChannels()
		elif opt in ("-j", "--json"):
			filename = arg
		elif opt in ("-s", "--assetslist"):
			errmsg, jsonList = tvspassets.parseSingleAsset("https://www.tvspielfilm.de/tv-programm/sendung/citizen-sleuth-die-podcast-detektivin,68416ef34d62107df4f47a79.html")
		elif opt in ("-t", "--tipslist"):
			jsonList = tvsptips.parseTips()
	if jsonList and filename:
		with open(filename, "w") as file:
			dump(jsonList, file)
		print(f"JSON file '{filename}' was successfully created.")


if __name__ == "__main__":
	main(argv[1:])

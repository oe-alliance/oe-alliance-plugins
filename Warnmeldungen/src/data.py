##############################################################################
#	(c)2021 by Oberhesse (oh20@gmx.de)
#	Creative Commons CC BY-NC-SA 3.0 License
#	Check the file "LICENSE" for more informations
##############################################################################
#	Amtlicher Regionalschluessel (ARS) ist ein 12-stelliger Schluessel:
#	Bundesland (2 Stellen), Regierungsbezirk (1 Stelle, wenn nicht vorhanden 0), Kreis (2 Stellen),
#	Gemeindeverband (4 Stellen) und Gemeinde (3 Stellen).
#	GENUTZT WERDEN FUER NINA-ABFRAGEN NUR DIE ERSTEN 5 STELLEN (KREIS)
##############################################################################
from datetime import datetime, timedelta
import json
import os
from . import cfg
from .cfg import configValue, warnReset
from __init__ import _

PATH = "/usr/lib/enigma2/python/Plugins/Extensions/Warnmeldungen/"
DIVIDER = '\n---------------------------------------------\n'
isAlert = 0
nextCheckDif = 0
wasAlarm = 0
wasError = 0
wasExtreme = 0
extremeLevelFound = 0
actMessages = []
lastMessages = []
miniView = False
miniMessages = []  #Kompaktanzeige
timeAlarmEnd = None
newestDate = ''
bufferedJson = ''
additionalPos = -1
additionalARS = []
lastDoubleTime = None
C_NoMsg = 'Keine Meldungen vorhanden'


def hasAdditionalARS(): return len(additionalARS) > 0


def eDebug(e, s=''):
	from plugin import exceptDebug
	exceptDebug(e, s)


def isStandby():
	try:
		from Screens.Standby import inStandby
		return inStandby != None
	except:
		return 0


def wakeUp():
	try:
		from Screens.Standby import inStandby
		if inStandby != None:
			inStandby.Power()
			return 1
	except:
		pass
	return 0


def getEmulatedJson(check):
	try:
		emulFile = PATH + 'emulate.json'
		if (not cfg.debugMode()) or (not os.path.exists(emulFile)):
			return ''
		s = open(emulFile, 'r').read()
		bak = emulFile + datetime.now().strftime('-%y-%m-%d-%H-%M-%S')
		os.rename(emulFile, bak)
		if os.path.exists(emulFile) or not os.path.exists(bak):
			return ''
		if s:
			s = '#' + s
		return s
	except:
		return ''
	return ''


def readAdditionalARS():
	try:
		global additionalARS
		additionalARS = []
		s = configValue('ARS2').strip()
		if s:
			additionalARS.append(s)
		fName = PATH + 'ars.txt'
		if os.path.exists(fName):
			with open(fName) as file:
				for line in file:
					if line.strip() and not line.strip().startswith('#'):
						additionalARS.append(line.strip())
	except Exception as e:
		eDebug(str(e), 'ReadAdditionalARS:')


def getARS(nameOnly=0, forcePos=-1):
	try:
		if additionalPos >= 0:
			s = additionalARS[additionalPos]
		else:
			s = configValue('ARS', '').strip()
		ars = s[:5]
		name = s.lstrip('0123456789;,-/ ')
		if name.startswith('('):
			name = name[1:-1]
		if (ars) and (not name) and (nameOnly):
			return _('Bitte den Regionalschl_uessel um den Gemeindnamen erg_aenzen')
		if (not ars) and nameOnly and (additionalPos < 0):
			return _('Bitte die Region in den Einstellungen festlegen')
		if nameOnly:
			return _('Amtliche NINA-Warnungen f_uer ') + name
		return ars + '0000000'
	except Exception as e:
		eDebug(str(e), 'getARS:')
		return ''


def NinaUrl(): return 'https://warnung.bund.de/api31/dashboard/' + getARS() + '.json'


def setAlarmEnd():
	i = getInt(configValue('afterAlarm'))
	if i <= 0:
		timeAlarmEnd = None
	else:
		timeAlarmEnd = datetime.now() + timedelta(hours=i)


def afterAlarm():
	if timeAlarmEnd == None:
		return False
	return datetime.now() <= timeAlarmEnd


def formatDate(s): s = s.split('+'); return s[0].replace('T', '  um ')  # 2021-07-23T12:26:47+02:00 zu  2021-07-23 12:26:47
	#return datetime.strptime( s , '%Y-%m-%d %H:%M:%S')


def header(detail=0):
	if miniView:
		return ''
	timeInfo = 'Stand der Abfrage: ' + datetime.now().strftime("%H:%M:%S Uhr")
	return timeInfo + ['  (Details: Blaue Taste)', ''][detail] + DIVIDER


def inCheckList(s, listS):
	s = s.lower()
	for c in listS.lower().split(';'):
		if c.strip() and (s.find(c) >= 0):
			return True
	return False


def getInt(s):
	try:
		if s == None:
			return 0
		return int(str(s).strip())
	except:
		return 0


def headLineSimple(s): return ''.join([i for i in s if not i.isdigit()])

#def ddd(s):  import plugin;  plugin.debug( str(s), 'a', 'test.txt')


def doubleEndTime():
	d = configValue('noDouble', 'false')
	d = str(d)
	if (d.isdigit()) and (lastDoubleTime != None):
		return 'aktiv bis ' + str(lastDoubleTime + timedelta(minutes=int(d)))
	return ['ohne', 'dauerhaft'][d.lower() != "false"]


def headlineAlreadyShown(s):
	global lastDoubleTime
	d = configValue('noDouble', 'false')
	d = str(d)
	if d.lower() == 'false':
		return False  # no check
	ignoreList = configValue('ignoreDoubleList', '')
	if ignoreList and not inCheckList(s, ignoreList):
		return False
	if not (headLineSimple(s) in lastMessages):
		return False  # headline not shown before
	if (not d.isdigit()) or (lastDoubleTime == None):
		lastDoubleTime = None
		return True  # check always
	okTime = lastDoubleTime + timedelta(minutes=int(d))
	return datetime.now() < okTime  # only return true if old enough


########### NINA ##############

def getNiNAHeadlines(s, checkMode=0, detail=0):  # checkmode:hintergrundpruefung
	import plugin
	global wasExtreme
	wasExtreme = False
	global extremeLevelFound
	global isAlert
	isAlert = levelOption = 0
	msgList = []
	timeList = []
	headlineList = []
	global miniMessages
	miniMessages = []
	global newestDate
	noDebug = cfg.sleepDuringStandby() and isStandby()

	def debug(msg, mode='a'):
		if (not noDebug) and checkMode:
			plugin.debug(msg, mode)
	ignoreDate = emulinfo = ''
	latestWarningDate = configValue('lastAlert', '')
	if checkMode:
		levelOption = getInt(configValue('level', '1'))
	diff, emul = configValue('ignoreInterval', 0), s.startswith('#')
	if emul:
		s = s[1:]
		emulinfo = '#EMULATION# '
	if diff:
		d = datetime.now() - timedelta(days=diff)
		ignoreDate = d.strftime("%Y-%m-%d um %H:%M:%S")  # siehe formatDate()
	res, j = '', json.loads(s)
	resetSourceData()
	try:
		if additionalPos < 0:
			debug(_('Hintergrundpr_uefung: ') + NinaUrl(), 'w')
		else:
			debug(_('\n\n--------------------------\nSekund_aerpr_uefung:  ') + NinaUrl())
		debug(getARS(True))
		debug('Standby: ' + str(isStandby()))
		debug(str(s) + '\n')
		debug('Letzte Einblendung: ' + str(lastDoubleTime))
		debug('Doppelmeldungs-Check: ' + doubleEndTime())
		debug('Vorherige Headlines: ' + str(lastMessages) + '\n')
		debug('Verarbeitung:')
		debug(header())
		debug(str(len(j)) + ' Eintraege')
	except Exception as e:
		eDebug(str(e), 'gnh:')
	for dct in j:
		headline = type = severity = provider = sent = id = expires = ''
		if 'payload' in dct:
			if 'id' in dct['payload']:
				id = dct['payload']['id']
			if 'data' in dct['payload']:
				data = dct['payload']['data']
				if 'provider' in data:
					provider = str(data['provider'])
				if 'headline' in data:
					headline = str(data['headline'])
				if 'msgType' in data:
					type = str(data['msgType'])
				if 'severity' in data:
					severity = str(data['severity'])
		if 'sent' in dct:
			sent = str(dct['sent'])
		if 'expires' in dct:
			expires = str(dct['expires'])
		if headline:
			headline = emulinfo + headline
			outS = headline.replace(_('. G_ueltig ab '), _('.\nG_ueltig ab '))
			debug('------------')
			debug(headline)
			debug(id)
			debug('Zuletzt gewarnt: ' + str(latestWarningDate))
			msgLevel = ['minor', 'moderate', 'severe', 'extreme'].index(severity.lower())
			if checkMode and (levelOption == 3) and (msgLevel == 3):
				wasExtreme = True  #vollanzeige erzwingen
			mustShow = inCheckList(headline, configValue('whiteList', ''))
			if mustShow:
				debug('Erzwingen (Whitelist)')
			mustHide = (not mustShow) and inCheckList(headline, configValue('ignoreList', ''))
			mustHideAll = (not mustShow) and inCheckList(headline, configValue('ignoreAllList', ''))
			if mustHideAll or (checkMode and mustHide):
				debug('Ignoriert (Blacklist)')
				continue
			#ir checkMode and (type.lower() != 'alert') and (not mustShow):  continue
			if sent:
				if detail:
					outS += ('\nErstellt: ' + formatDate(sent))
				debug('Erstellt: ' + str(sent))
				if ignoreDate and (formatDate(sent) < ignoreDate):
					debug('Ignoriert (zu alt)')
					continue
			if type:
				outS += '\nMeldungsart: '
				outS += type.replace('Alert', 'Warnung').replace('Update', 'Folgemeldung (Update)').replace('Cancel', 'Entwarnung')
			if checkMode and (levelOption > 0):  #levelOption 0=Alle Warnstufen
				if (levelOption == 1) and (msgLevel == 0):
					debug('Warnstufe ignoriert')
					continue     #levelOption 1=Ab Moderat
				if (levelOption == 2) and (msgLevel <= 1):
					debug('Warnstufe ignoriert')
					continue     #levelOption 2=Ab Hoch
				if (levelOption == 3) and (msgLevel <= 1):
					debug('Warnstufe ignoriert')
					continue     #levelOption 3=Ab Hoch,Extremvollanzeige
				if (levelOption == 4) and (msgLevel <= 2):
					debug('Warnstufe ignoriert')
					continue     #levelOption 4=Ab Extrem
			if not checkMode and (msgLevel >= 0):
				outS += '\nWarnstufe: ' + ['Niedrig', 'Moderat', 'Hoch', 'Extreme Gefahr!'][msgLevel]
			if checkMode:
				debug('Letzte Warnung: ' + str(latestWarningDate))
			if checkMode and (latestWarningDate >= sent):
				debug('Ignoriert (kein Update)')
				continue
			if checkMode and (not mustShow) and headlineAlreadyShown(headline):
				debug('Ignoriert (gleicher Text schon gezeigt)')
				continue
			if msgLevel == 3:
				extremeLevelFound = True
			if sent > newestDate:  #neuer
				newestDate = sent
				debug('Aktualisiere Timestamp: "' + sent + '"')
			if id and detail:
				description = getLongDescription(provider.lower(), id)
				if description:
					outS += ('\n' + description)
			headlineList.append(headLineSimple(headline))
			miniMessages.append(headline)
			if hasAdditionalARS():
				outS = getARS(True) + '\n' + outS
			msgList.append(outS)
			timeList.append(sent)
			debug('Meldung registriert (' + headLineSimple(headline) + ')')
	#debug(msgList)
	if timeAlarmEnd != None:
		debug(_('Verk_uerzter Alarm bis ') + str(timeAlarmEnd))
	if len(msgList):
		global actMessages
		if not checkMode:  # Anzeige auf Screen
			for h in headlineList:
				actMessages.append(h)
			debug('Aktuelle Headlines:\n' + str(actMessages) + '\n')
		if configValue('invertedOrder', True):
			msgList = [x for _z_, x in sorted(zip(timeList, msgList), reverse=True)]
			miniMessages = [x for _z_, x in sorted(zip(timeList, miniMessages), reverse=True)]
		res = header(detail) + DIVIDER.join(msgList)
	if not res:
		if checkMode and not plugin.forceAlarm:
			res = ''
		else:
			res = header(detail) + emulinfo + C_NoMsg
			if hasAdditionalARS():
				res = getARS(True) + '\n' + res
	#elif newestDate>latestWarningDate: warnReset(newestDate);
	if checkMode:
		plugin.forceAlarm = False
	resetSourceData()
	return res


def downloadToString(url):
	header = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
				'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'en-us,en;q=0.5'}
	try:
		from urllib2 import Request, urlopen  # self.message(url)
		searchrequest = Request(url, None, header)
		return urlopen(searchrequest).read()
	except:
		return ''

################ READ PROVIDER SOURCES ###################


sources = [
	{"provider": "katwarn", "id": "kat", "url": "katwarn/warnmeldungen", "data": "", "name": "Katwarn"},
	{"provider": "mowas", "id": "mow", "url": "mowas/gefahrendurchsagen", "data": "", "name": "Mowas (Modulares Warnsystem)"},
	{"provider": "biwapp", "id": "biw", "url": "biwapp/warnmeldungen", "data": "", "name": "Biwapp (B_uerger Info- & Warn-App)"},
	{"provider": "dwd", "id": "dwd", "url": "dwd/unwetter", "data": "", "name": "DWD (Deutscher Wetterdienst)"},
	{"provider": "lhp", "id": "lhp", "url": "lhp/hochwassermeldungen", "data": "", "name": "LHP (L_aender_uebergr. Hochwasserportal)"}]


def resetSourceData():
	global sources
	for x in sources:
		x['data'] = 'null'


def getWarnJson(url):
	try:
		return downloadToString('https://warnung.bund.de/bbk.' + url + '.json')
	except:
		return ''


def getLongDescription(provider, id):
	global sources
	try:
		if not id:
			return ''
		baseName = data = ''
		for source in sources:
			if (provider == source['provider']) or (id.lower().startswith(source['id'])):
				if source['data'] == 'null':
					source['data'] = getWarnJson(source['url'])
				data, baseName = source['data'], _(source['name'])
				break
		if not baseName:
			return 'Keine Beschreibung in Katwarn, Mowas, Biwapp, DWD oder LHP vorhanden'
		if not data:
			return 'Kein Zugriff auf ' + baseName + _(' m_oeglich')
		j = json.loads(data)
		data = ''
		for dct in j:
			if 'identifier' in dct:
				_id = dct['identifier']
				if (not _id) or (id.find(_id) < 0):
					continue
			if 'info' in dct:
				info = dct['info']
				if len(info):
					info = info[0]
					instruction = sender = area = contact = ''
					if 'instruction' in info:
						instruction = '\n\nHandlungsempfehlung:\n' + formatted(str(info['instruction']))
					if 'parameter' in info:
						try:
							p = info['parameter']
							if len(p):
								for v in p:
									if 'valueName' in v:
										if v['valueName'] == 'sender_langname':
											sender += (['\n\nErsteller: ', ', '][sender != ''] + formatted(str(v['value'])))
						except:
							sender = ''
					if 'area' in info:
						try:
							_area = info['area']
							if len(_area):
								for a in _area:
									if 'areaDesc' in a:
										area += ['\n\nBetroffene Region(en): ', ', '][area != ''] + formatted(str(a['areaDesc']))
						except:
							area = ''
					if 'contact' in info:
						contact = '\n\nWeitere Informationen: ' + formatted(str(info['contact']))
					if 'description' in info:
						head = '\n++++ Details - Quelle: ' + baseName + ' ++++ \n'
						return head + formatted(str(info['description'])) + instruction + contact + area + sender + '\n'

	except:
		return _('Beschreibung f_uer ') + baseName + ' kann nicht verarbeitet werden'
	return 'Keine Beschreibung in ' + baseName + ' gefunden'


############ MAIN FUNCTION ###############

def _getMsg(check=0, detail=0):
	global wasError
	global bufferedJson
	wasError = False
	try:
		if int(getARS()) > 0:
			if bufferedJson and not check:
				s = bufferedJson
				bufferedJson = ''
			else:
				s = getEmulatedJson(check)
				if not s:
					s = downloadToString(NinaUrl())
				if not s:
					wasError = True
					return ''
				elif check:
					bufferedJson = s
			return getNiNAHeadlines(s, check, detail)
		else:
			return ''
	except Exception as e:
		eDebug(e, 'getMsg: ')
		wasError = True
		return ''


def getNinaMsg(check=0, detail=0):
	try:
		global additionalPos
		global bufferedJson
		global miniMessages
		global newestDate
		global lastMessages
		global actMessages
		global extremeLevelFound
		actMessages = []
		newestDate = ''
		extremeLevelFound = False
		if cfg.sleepDuringStandby() and isStandby():
			return ''
		readAdditionalARS()
		additionalPos = -1
		res = _getMsg(check, detail)
		if hasAdditionalARS():
			for idx, ars in enumerate(additionalARS):
				additionalPos = idx
				bufferedJson = ''
				saveList = miniMessages
				res += ('\n\n' + _getMsg(check, detail))
				res = res.strip()
				additionalPos = -1
				bufferedJson = ''
			if len(saveList):
				miniMessages[:0] = saveList  # insert
		if not check:
			lastMessages = []  # actMessages[:]
			for m in actMessages:
				if m and not (m in lastMessages):
					lastMessages.append(m)
		if res and (newestDate > configValue('lastAlert', '')):
			warnReset(newestDate)
		return res
	except Exception as e:
		eDebug(e, 'GetNinaMsg:')
		return ''


############## HTML-TO-PLAINTEXT #################

def tagsRemove(s):
	while 1:
		i, j = s.find('<'), s.find('>')
		if (i < 0) or (j < 0) or (j < i):
			break
		s = s[:i] + s[(j + 1):]
	return s


def unEscape(s):
	try:
		import sys
		if sys.version_info[0] >= 3:
			from html.parser import HTMLParser
		else:
			from HTMLParser import HTMLParser
		return HTMLParser().unescape(s).encode('utf8')
	except:
		return s


def formatted(s):
	s = s.replace('<br/>', '<br>').replace('<br><br>', '\n\n')
	s = s.replace('<br>0', '\n0').replace('.<br>', '.\n').replace('<br>', ' ').strip()
	s = tagsRemove(s)
	if s.find('&') >= 0:
		s = unEscape(s).replace('\xc2\xa0', ' ')
	return s

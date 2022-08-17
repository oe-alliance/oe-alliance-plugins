##############################################################################
#	(c)2021 by Oberhesse (oh20@gmx.de)
#	Creative Commons CC BY-NC-SA 3.0 License
#	Check the file "LICENSE" for more informations
##############################################################################

VERSION = '102'
VERSIONSTR = '1.0.2'
VERSIONDATE = '06.01.2022'

from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigClock, ConfigSubsection, ConfigOnOff, ConfigYesNo, ConfigEnableDisable, ConfigSelection, getConfigListEntry, NoSave, ConfigNothing, ConfigText
from Components.ConfigList import ConfigListScreen
from Components.MenuList import MenuList
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from enigma import getDesktop, eTimer
from datetime import datetime, timedelta
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
import json
from os import path
from __init__ import _

desktopSize = getDesktop(0).size()
scale = desktopSize.width() / 1280.0
_isDebugMode = None

PATH = "/usr/lib/enigma2/python/Plugins/Extensions/Warnmeldungen/"

##############################################################################


config.plugins.Warnung = ConfigSubsection()
config.plugins.Warnung.format = ConfigSelection(default="0",
	choices=[('0', 'Vollanzeige'), ('1', 'Kompaktanzeige oben'), ('2', _('Kompaktanzeige oben einger_ueckt'))])
config.plugins.Warnung.scale = ConfigSelection(default="0", choices=[('0', 'Standard'), ('1', 'Kompakt')])
config.plugins.Warnung.ARS = ConfigText(default='')
config.plugins.Warnung.ARS2 = ConfigText(default='')
config.plugins.Warnung.duration = ConfigInteger(default=30, limits=(0, 3600))
config.plugins.Warnung.interval = ConfigInteger(default=10, limits=(0, 240))
config.plugins.Warnung.afterAlarm = ConfigSelection(default="0", choices=[('0', _('Unver_aendert')),
		('1', _('Min_uetliche Pr_uefung f_uer 1 Stunde')), ('2', _('Min_uetliche Pr_uefung f_uer 2 Stunden')),
		('3', _('Min_uetliche Pr_uefung f_uer 3 Stunden')), ('4', _('Min_uetliche Pr_uefung f_uer 4 Stunden'))])
config.plugins.Warnung.ignoreInterval = ConfigInteger(default=0, limits=(0, 9999))
config.plugins.Warnung.resetOnStart = ConfigYesNo(default=True)
config.plugins.Warnung.highAlertOnly = ConfigYesNo(default=False)
config.plugins.Warnung.level = ConfigSelection(default="1", choices=[
		('0', _('Alle Warnstufen')), ('1', _('Ab Warnstufe "Moderat"')), ('2', _('Ab Warnstufe "Hoch"')),
		('3', _('Ab Warnstufe "Hoch" (Vollanzeige bei "Extrem")')), ('4', _('Nur Extremstufe'))])
config.plugins.Warnung.standbyMode = ConfigSelection(default="1", choices=[('0', _('Normalbetrieb')),
		('1', _('Hintergrundpr_uefung aussetzen')),
		('2', _('Bei Warnung Standby beenden')),
		('3', _('Bei Warnung Standby beenden (06:00-00:00)')),
		('4', _('Bei Warnung Standby beenden (08:00-22:00)')),
		('5', _('Bei Extremwarnung Standby beenden')),
		('6', _('Bei Extremwarnung Standby beenden (06:00-00:00)')),
		('7', _('Bei Extremwarnung Standby beenden (08:00-22:00)'))])
config.plugins.Warnung.invertedOrder = ConfigYesNo(default=True)
#config.plugins.Warnung.noDouble = ConfigYesNo(default = False)
config.plugins.Warnung.noDouble = ConfigSelection(default="false", choices=[('false', _('Nein')),
		('30', _('f_uer 30 Minuten')),
		('60', _('f_uer 1 Stunde')),
		('120', _('f_uer 2 Stunden')),
		('180', _('f_uer 3 Stunden')),
		('240', _('f_uer 4 Stunden')),
		('300', _('f_uer 5 Stunden')),
		('360', _('f_uer 6 Stunden')),
		('true', _('Dauerhaft'))])
config.plugins.Warnung.lastAlert = ConfigText(default='')
config.plugins.Warnung.ignoreDoubleList = ConfigText(default='')
config.plugins.Warnung.ignoreList = ConfigText(default='')
config.plugins.Warnung.ignoreAllList = ConfigText(default='')
config.plugins.Warnung.whiteList = ConfigText(default=_('Unfall;Flut;Explosion;schwemmung;hang;rutsch'))
config.plugins.Warnung.debug = ConfigYesNo(default=False)

##############################################################################


def debugMode(reset=False):
	global _isDebugMode  # buffer
	if reset or (_isDebugMode == None):
		_isDebugMode = config.plugins.Warnung.debug.value
	return _isDebugMode


def warnReset(val=''):
	try:
		config.plugins.Warnung.lastAlert.value = val
		config.plugins.Warnung.lastAlert.save()
	except:
		pass


def configValue(id, default="0"):
	try:
		res = getattr(config.plugins.Warnung, id).value
		if res == None:
			return default
		else:
			return res
	except:
		return default


def wakeUpOk():
	from data import extremeLevelFound
	type = int(config.plugins.Warnung.standbyMode.value)
	if (type >= 5) and not extremeLevelFound:
		return 0
	if (type >= 5):
		type -= 3
	hour = datetime.now().hour
	return (type == 2) or ((type == 3) and (hour >= 6)) or ((type == 4) and (hour >= 8) and (hour < 22))


def sleepDuringStandby():  #im Standby schlafen
	return int(config.plugins.Warnung.standbyMode.value) == 1


#################################  SCREEN ###################################

class WarnCfg (Screen, ConfigListScreen):
	skin = """<screen position="center,center" size="*scrSize*" backgroundColor="#11111111"  flags="wfNoBorder"  title=" ">
			<eLabel  position="*linePos1*" backgroundColor="#112233" size="*bottomBkSize*" />
			<eLabel  position="0,0"  size="*titleSize*" backgroundColor="#112233" zPosition="10"/>
			<eLabel  position="*versionPos1*"  font="Regular;*fs4*" valign="top" halign="left"  foregroundColor="#999999"
				size="*titleSize*" text="*version1*" transparent="1"   zPosition="10"/>
			<eLabel  position="*versionPos2*"  font="Regular;*fs4*" valign="top" halign="left"  foregroundColor="#999999"
				size="*titleSize*" text="*version2*" transparent="1"   zPosition="10"/>
			<eLabel  position="*titlePos*"  font="Regular;*fs*" valign="top" halign="center"
				size="*titleSize*" text="*title*" transparent="1"   zPosition="10"/>
			<eLabel  position="*linePos0*" backgroundColor="#606060" size="*lineSize*" zPosition="10"/>
			<widget name="config" itemHeight="*ih*" font="Regular;*fs*" position="*listPos*" size="*listSize*"
				backgroundColor="#11111111"  scrollbarSliderForegroundColor="#bbaab4" scrollbarMode="showOnDemand"
				scrollbarSliderBorderColor="#00333333" scrollbarSliderBorderWidth="1"  scrollbarWidth="*sb*"  />
			<widget name="info" position="*labelPos*" valign="center" size="*labelSize*" font="Light;*fs2*"
				transparent="1" zPosition="9"/>
			<eLabel  position="*linePos1*" backgroundColor="#606060" size="*lineSize*" zPosition="10"/>
			<eLabel  position="*linePos2*" backgroundColor="#606060" size="*lineSize*" zPosition="10"/>
			*buttons*
			<widget name="saveMsg"  backgroundColor="#006600" position="center,center" font="Regular;*fs*"
				size="*msgSize*" valign="center" halign="center" zPosition="99"/>
		</screen>"""

	def __init__(self, session, args=0):
		self.session = session
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MenuActions", "EPGSelectActions"],
			{"cancel": self.abort, "red": self.abort, "green": self.save, "yellow": self.initSearch, "blue": self.blue}, -1)
		self["key_red"] = StaticText(_("Abbruch"))
		self["key_green"] = StaticText(_("Sichern"))
		self["key_yellow"] = StaticText(_("Regionalschl_uessel setzen"))
		self["key_blue"] = StaticText(_("Testalarm"))
		#self["key_menu"] = StaticText(_("Menu: Quellen"))
		self["saveMsg"] = Label(_("Gespeichert"))
		self["info"] = Label('')
		self.list = []
		self.infos = []
		self.createSetupList()
		self.initSkin()
		ConfigListScreen.__init__(self, self.list, session=self.session)
		self.onLayoutFinish.append(self.initMenu)
		self.cfgTimer = eTimer()
		self.cfgTimer.callback.append(self.onCfgTimerRun)
		self.initTimer = eTimer()
		self.initTimer.callback.append(self.onInitTimerRun)
		self["config"].onSelectionChanged.append(self.info)
		self.onCfgTimerRun()
		self.initTimer.start(200, True)
		globals()["_isDebugMode"] = None

	def endMsg(self, answer=0): pass

	def message(self, s, d=-1):
		if s != '':
			self.msgBox = self.session.openWithCallback(self.endMsg, MessageBox, s, MessageBox.TYPE_INFO, d)
			self.msgBox.setTitle(" ")

	def question(self, callback, s):
		self.msgBox = self.session.openWithCallback(endMessage, MessageBox, s, MessageBox.TYPE_YESNO)
		self.msgBox.setTitle(" ")

	def channelChoiceFinish(self, answer):
		import data
		if (answer != None):
			if (self["config"].getCurrentIndex() == 3):
				data.ARS2 = answer[1]
				config.plugins.Warnung.ARS2.value = answer[1].replace(',  ', ', ')
			else:
				data.ARS = answer[1]
				config.plugins.Warnung.ARS.value = answer[1].replace(',  ', ', ')

	def onInitTimerRun(self):
		self.initTimer.stop()
		if not config.plugins.Warnung.ARS.value:
			self.initSearch()

	def getChoice(self, choices=[]):
		from Screens.ChoiceBox import ChoiceBox
		if len(choices) == 0:
			message('Keine Eintr_aege gefunden')
		else:
			self.session.openWithCallback(self.channelChoiceFinish, ChoiceBox, title=_("Regionalschl_uessel"), list=choices)

	def holeSchluessel(self, spec='mar'):
		res = []
		F = PATH + 'Regionalschluessel.json'
		if not path.exists(F):
			return res
		try:
			with open(F) as json_file:
				data = json.load(json_file)
				for p in data['daten']:
					if str(p[1]).lower().startswith(spec.lower()):
						lst = (str(p[1]), str(p[0]) + ' (' + str(p[1]) + ')')
						res.append(lst)
			self.getChoice(sorted(res))
		except:
			pass
		return res

	def initSearch(self):
		from Screens.VirtualKeyBoard import VirtualKeyBoard
		idx = self["config"].getCurrentIndex()
		if (idx != 2) and (idx != 3):
			self.message(_('Bitte die Zeile f_uer den gew_uenschten Regionalschl_uessel selektieren (Zeilen3/4)'), 10)
		else:
			self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='Erste Buchstaben des Gemeindenamens eingeben (mind. 3)', text='')

	def searchReturn(self, search):
		if search and search != '':
			self.holeSchluessel(search)

	def initSkin(self):
		_scale = scale
		if configValue('scale') == '1':
			_scale = _scale * 0.8

		def sizeStr(i1, i2): return str(i1) + ',' + str(i2)

		def lineStr(x, y, w, h):
			return '<eLabel backgroundColor="#444444" zPosition="99" position="' + sizeStr(x, y) + '" size="' + sizeStr(w, h) + '" />'
		iH = int(32 * _scale)
		labelH = int(70 * _scale)
		titleH = int(48 * _scale)
		buttonH = int(30 * _scale)
		fS = int(24 * _scale)
		fS2 = int(21 * _scale)
		lineH = int(round(_scale))
		listW = int(940 * _scale)
		dif = int(_scale * 10)
		scrW = listW + 2 * dif
		fS3 = int(20 * _scale)
		fS4 = int(17 * _scale)
		listH = min(16, len(self.list)) * iH
		scrH = listH + 4 * dif + labelH + buttonH + titleH
		self.skin = self.skin.replace('*title*', _('Einstellungen'))
		self.skin = self.skin.replace('*version1*', 'Version: ' + VERSIONSTR).replace('*version2*', 'Stand: ' + VERSIONDATE)
		self.skin = self.skin.replace('*titleSize*', sizeStr(scrW, titleH))
		self.skin = self.skin.replace('*titlePos*', sizeStr(0, int(8 * _scale)))
		self.skin = self.skin.replace('*versionPos1*', sizeStr(12, int(3 * _scale)))
		self.skin = self.skin.replace('*versionPos2*', sizeStr(12, int(23 * _scale)))
		self.skin = self.skin.replace('*scrSize*', sizeStr(scrW, scrH))
		self.skin = self.skin.replace('*listSize*', sizeStr(listW, listH))
		self.skin = self.skin.replace('*listPos*', sizeStr(dif, dif + titleH))
		self.skin = self.skin.replace('*linePos0*', sizeStr(1, titleH))
		self.skin = self.skin.replace('*linePos1*', sizeStr(1, listH + titleH + dif * 2))
		self.skin = self.skin.replace('*linePos2*', sizeStr(1, listH + titleH + dif * 2 + labelH))
		self.skin = self.skin.replace('*lineSize*', sizeStr(scrW, lineH))
		self.skin = self.skin.replace('*labelPos*', sizeStr(dif * 2, listH + titleH + dif * 2))
		self.skin = self.skin.replace('*labelSize*', sizeStr(listW, labelH))
		self.skin = self.skin.replace('*bottomBkSize*', sizeStr(scrW, labelH))
		self.skin = self.skin.replace('*msgSize*', sizeStr(int(220 * _scale), int(56 * _scale))).replace('*fs4*', str(fS4))
		self.skin = self.skin.replace('*fs*', str(fS)).replace('*fs2*', str(fS2)).replace('*ih*', str(iH)).replace('*sb*', str(int(_scale * 7)))
		#buttons/label
		cPos = pos = 0
		s = ''
		step = int(scrW / 4) + 1
		but = '<widget source="key_%1" render="Label" position="%2,' + str(scrH - buttonH - dif)
		but += '" zPosition="1" size="' + sizeStr(step, buttonH) + '" '
		but += ' font="Regular;' + str(fS3) + '" foregroundColor="foreground" halign="center" valign="top" transparent="1" />'
		lab = '<eLabel backgroundColor="#%3" position="%4,' + str(scrH - dif) + '" size="' + sizeStr(step, dif) + '" zPosition="2"/>'
		for k in ["red", "green", "yellow", "blue"]:
			s += but.replace("%1", k).replace("%2", str(pos))
			pos += step
		for c in ["b81c46", "009f3c", "9ca81b", "2673ec"]:
			s += lab.replace("%3", c).replace("%4", str(cPos))
			cPos += step
		s += lineStr(0, 0, scrW, 1)
		s += lineStr(0, scrH - 1, scrW, 1)
		s += lineStr(0, 0, 1, scrH)
		s += lineStr(scrW - 1, 0, 1, scrH)
		self.skin = self.skin.replace("*buttons*", s)

	def onCfgTimerRun(self):
		try:
			self.cfgTimer.stop()
			self["saveMsg"].hide()
		except:
			pass

	def cfgOut(self, cfg):
		for (text, id, notify) in cfg:
			if text.startswith('- -'):
				self.separatorPos.append(len(self.list))
				self.list.append(getConfigListEntry(text, NoSave(ConfigNothing())))
			else:
				x = getattr(config.plugins.Kiosk, id)
				self.list.append(getConfigListEntry(_(text), x))
				if notify:
					x.addNotifier(self.refresh, initial_call=False)

	def separator(self, s, add=''): return '- - - - - - - ' + _(s) + add + ' - - - - - - -'

	def info(self):
		try:
			self["info"].setText(self.infos[self["config"].getCurrentIndex()])
		except:
			pass

	def createSetupList(self, reset=False):
		def _info(s): self.infos.append(_(s.replace('$', 'Begriffe mit ";" trennen, Gro_ss-/Kleinschreibung muss nicht beachtet werden')))
		self.list = []
		self.infos = []

		self.list.append(getConfigListEntry(_('Warnfenster (Einblendung)'), config.plugins.Warnung.format))
		_info('_Aenderung der Anzeige wird erst beim n_aechsten Fensteraufruf wirksam.')

		self.list.append(getConfigListEntry(_('Anzeigegr_oe_sse'), config.plugins.Warnung.scale))
		_info('_Aenderung der Anzeige wird erst beim n_aechsten Fensteraufruf wirksam.')

		self.list.append(getConfigListEntry(_('Regionalschl_uessel, Ort (Gelbe Taste)'), config.plugins.Warnung.ARS))
		_info('Amtlicher Regionalschl_uessel zum Zugriff auf die NINA-Schnittstelle. Die Abfrage erfolgt KREISGENAU _ueber die ersten 5 Stellen des Schl_uessels. WICHTIG:  Den Gemeindenamen hinter der Nummer eintragen.')

		self.list.append(getConfigListEntry(_('Regionalschl_uessel, Sekund_aerort (Gelbe T.)'), config.plugins.Warnung.ARS2))
		_info('OPTIONAL - Der Sekund_aerort muss in einem anderen Kreis liegen, da sonst Doppelmeldungen erzeugt werden. Weitere Schl_uessel k_oennen ggfl. manuell in der Datei ars.txt eingetragen werden.')

		self.list.append(getConfigListEntry(_('Abfrageintervall (Minuten, 0=keine Hintergrundpr_uefung)'), config.plugins.Warnung.interval))
		_info('Zeitabstand f_uer Hintergrundabfragen')

		self.list.append(getConfigListEntry(_('Abfrageintervall nach Warnungen (Minuten)'), config.plugins.Warnung.afterAlarm))
		_info('Reduzierter Zeitabstand f_uer Hintergrundabfragen, nachdem eine neue Warnung eingegangen ist..')

		self.list.append(getConfigListEntry(_('Warnstufe f_uer Einblendungen'), config.plugins.Warnung.level))
		_info('Legt das Verhalten fest, das f_uer automatische Einblendungen gilt.')

		self.list.append(getConfigListEntry(_('Warnanzeige (Sekunden)'), config.plugins.Warnung.duration))
		_info('Dauer der Warnungseinblendung in Sekunden.\nEine Warnungseinblendung kann mit mit Ok/Exit geschlossen werden.')

		self.list.append(getConfigListEntry(_('Verhalten im Standby'), config.plugins.Warnung.standbyMode))
		_info('Wichtig: Diese Einstellungen gelten mir f_uer das einfache Standby. Im Deep-Standby sind keine Abfragen m_oeglich.')

		self.list.append(getConfigListEntry(_('Warnungswiederholungen vermeiden'), config.plugins.Warnung.noDouble))
		_info('Gilt nur f_uer automatische Warnungen, wenn deren Text identisch geblieben ist')

		self.list.append(getConfigListEntry(_('Eingrenzungsbegriffe f_uer Wiederholungsvermeidung'),
						config.plugins.Warnung.ignoreDoubleList))
		_info('Doppelmeldung nur vermeiden, wenn sie einen der eingetragenen Begriffe enthalten ($). Leer: Immer Doppelvermeidung ')

		self.list.append(getConfigListEntry(_('Alter f_uer zu ignorierende Meldungen (Tage, 0=nicht ign.)'),
						config.plugins.Warnung.ignoreInterval))
		_info('Gilt f_uer alle Warnungsanzeigen')

		self.list.append(getConfigListEntry(_('Neue Meldungen zuerst'), config.plugins.Warnung.invertedOrder))
		_info('Reihenfolge der Meldungen (bezogen auf den Ort')

		self.list.append(getConfigListEntry(_('Alarm-Ignorierliste'), config.plugins.Warnung.ignoreList))
		_info('Neue Warnungen nicht automatisch einblenden, wenn sie einen der eingetragenen Begriffe enthalten  ($)')

		self.list.append(getConfigListEntry(_('Sperrliste (f_uer alle Meldungen)'), config.plugins.Warnung.ignoreAllList))
		_info('Meldungen in allen Anzeigen ignorieren, wenn sie einen der eingetragenen Begriffe enthalten  ($)')

		self.list.append(getConfigListEntry(_('Wichtige Alarmbegriffe'), config.plugins.Warnung.whiteList))
		_info('Neue Warnungen immer automatisch einblenden, wenn sie einen der eingetragenen Begriffe enthalten  ($)')

		self.list.append(getConfigListEntry(_('Debugmodus'), config.plugins.Warnung.debug))
		_info('Erzeugt eine Debugdatei (debug.txt) mit Daten der letzten Hintergrundabfrage. Die Datei emulate.json kann f_uer Testalarme genutzt werden.')

	def initMenu(self): self["config"].instance.setWrapAround(True)

	def yellow(self): pass

	def blue(self):
		import plugin
		plugin.pNina.loop = -1
		plugin.forceAlarm = True
		self.session.open(MessageBox, _("Automatische Warnung 5 Sekunden nach dem Schlie_ssen des Meldungsfensters"),
				MessageBox.TYPE_INFO)

	def onChanged(self): pass

	def refresh(self, *args, **kwargs): self.onChanged()

	def startMenuMode(self):
		self["config"].instance.setWrapAround(True)
		for x in self["config"].list:
			x[1].cancel()

	def save(self):
		try:
			self["saveMsg"].show()
			self.cfgTimer.start(1300, True)
		except:
			pass
		self.saveAll()
		try:
			for x in self["config"].list:
				x[1].cancel()
		except:
			pass
		try:
			self.createSetupList()
			self["config"].list = self.list
		except:
			self.close()

	def abort(self): self.keyCancel()

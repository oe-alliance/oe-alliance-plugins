##############################################################################
#	(c)2021 by Oberhesse (oh20@gmx.de)
#	Creative Commons CC BY-NC-SA 3.0 License
#	Check the file "LICENSE" for more informations
##############################################################################
from Components.ActionMap import ActionMap
from Components.Label import Label
from enigma import ePoint, eSize, eLabel, eTimer, getDesktop, gFont, gRGB
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from datetime import datetime, timedelta
from os import path
from . import cfg
from . import data
from .data import getARS, getInt, miniView
from .cfg import scale, configValue
from .__init__ import _

PATH = "/usr/lib/enigma2/python/Plugins/Extensions/Warnmeldungen/"
mainSession = None
firstRun = True
forceAlarm = False


def aktMS(): return datetime.now().strftime("%H:%M:%S [%f]")[:12] + ']:  '


def debug(s, flag='a', fName='debug.txt'):
	if cfg.debugMode():
		f = open(PATH + fName, flag)
		f.write(aktMS() + str(s) + '\n')
		f.close()


def exceptDebug(e, s=''): debug(s + str(e), 'w', 'error.txt')

##############################################################################44


class NinaScreenX (Screen):
	skin = """<screen position="0,0" size="0,0" zPosition="10" backgroundColor="#ff000000"  title=" " flags="wfNoBorder"></screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.timer = eTimer()
		self.timer.callback.append(self.onTimerRun)
		self.onShow.append(self.onValueShow)
		self.onLayoutFinish.append(self.formatLabels)

	def formatLabels(self): pass
	def onTimerRun(self): pass
	def onValueShow(self): pass

##############################################################################88


skinMini = """<screen position="_dif_,_dif_" size="_miniW_,_miniH_"  zPosition="99" backgroundColor="#22550000"
			title=" " flags="wfNoBorder">
		<widget name="infoSmall" font="Regular;_fnt1_" position="_mX0_,_mY0_" size="_miniW_,_miniH_" foregroundColor="#ffffaa"
			shadowColor="#111111"  shadowOffset="-1,-1"  zPosition="100"  valign="top" halign="left" transparent="1"   />
		<ePixmap alphatest="blend" zPosition="100" position="_mX2_,_mY2_" size="_mW2_,_mH2_"
				 scale="1" pixmap="%path%warnung.png" />
		<eLabel  backgroundColor="#cc0000"  foregroundColor="#ffffff" position="_mX1_,_mY1_" size="_mW1_,_mH1_"
				zPosition="101"  text="Ok _gt_"  font="Regular;_fnt0_" valign="center" halign="center" />
		</screen>"""


class NinaScreen (Screen):
	skin = """<screen position="center,center" size="_scrW_,_scrH_"  zPosition="10" backgroundColor="#11111111"
		title=" " flags="wfNoBorder">
		<eLabel  backgroundColor="#0a660000"  position="0,0" size="_scrW_,_h0_" zPosition="3"   />
		<eLabel  backgroundColor="#0a660000"  position="0,0" size="_lineW_,_scrH_" zPosition="3"   />
		<eLabel  backgroundColor="#0a660000"  position="_lineX_,0" size="_lineW_,_scrH_" zPosition="3"   />
		<widget name="ARS" font="Regular;_fnt2_" position="_x0_,_y0a_" size="_w0_,_h0_" foregroundColor="#fffffff"
			zPosition="20"  valign="top" halign="top" transparent="1"   />
		<widget name="date" font="Regular;_fnt0_" position="_x1_,_y0b_" size="_w1_,_h0_" foregroundColor="#aa9999"
			zPosition="99"  valign="top" halign="right" transparent="1"   />
		<widget name="countdown" font="Regular;_fnt1_" position="0,_y0d_" size="_w1_,_h0_" foregroundColor="#ffaaaa"
			zPosition="99"  valign="top" halign="right" transparent="1"   />
		<widget name="time" font="Regular;_fnt1_" position="_x1_,_y0c_" size="_w1_,_h0_" foregroundColor="#ffffff"
			zPosition="99"  valign="top" halign="right" transparent="1"   />
		<widget name="scrolltext0" font="Regular;_fnt2_" position="_x1_,_y1_" size="_w1_,_h1_" foregroundColor="#fffffff"
				 		scrollbarSliderBorderColor="#00333333" scrollbarSliderBorderWidth="1"  scrollbarWidth="_sb_"
				 		backgroundColor="#111111ff"
				 		zPosition="3"  transparent="1" /> *buttons*
		</screen>"""

	def __init__(self, session, wasStandby=False):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
			{"cancel": self.keyCancel, "red": self.keyCancel,
				"green": self.green,
				"yellow": self.cfg, "ok": self.ok,
				"blue": self.showDetail,
				"up": self.up, "down": self.down}, -1)
		self["scrolltext0"] = ScrollLabel("")
		self["infoSmall"] = Label('')
		self["key_red"] = StaticText(_("Schlie_ssen"))
		self["key_green"] = StaticText(_("Aktualisieren"))
		self["key_yellow"] = StaticText(_("Einstellungen"))
		self["key_blue"] = StaticText(_("Erweiterte Infos"))
		self["ARS"] = Label(_("Laden...."))
		self["time"] = Label(_(" "))
		self["date"] = Label(_(" "))
		self["countdown"] = Label(_(" "))
		self.formatSkin()
		self.detailled = self.loadDetail = self.refresh = self.msgIdx = self.msgLoop = 0
		self.countDown = -1
		if data.wasAlarm:
			self.countDown = configValue('duration', 0)
		if wasStandby:
			self.countDown = max(self.countDown, 3600)
		if self.countDown == 0:
			self.countDown = -1
		self.timer = eTimer()
		self.timer.callback.append(self.onTimerRun)
		self.onTimerRun(True)
		try:
			pNina.stopTimer()
		except:
			pass
		self.init = 1
		self.timer.start(100, True)
		self.onClose.append(self.closeProc)

	def _setText(self, key, s):
		if not data.miniView:
			self[key].setText(s)

	def formatSkin(self):
		_scale = scale
		if getInt(configValue('scale')) == 1:
			_scale = _scale * [0.8, 0.9][data.miniView]

		def val(i): return int(_scale * i)
		def valStr(i): return str(val(i))
		def sizeStr(w, h): return str(w) + ',' + str(h)
		s = [self.skin, skinMini][data.miniView]
		scrW = val(900)
		scrH = val(530)
		dif = 0
		s = s.replace('_fnt0_', valStr(18)).replace('_fnt1_', valStr(23)).replace('_fnt2_', valStr(26)).replace('_sb_', valStr(10))
		if data.miniView: #Kompaktanzeige fuer Wanungen (oben)
			if getInt(configValue('format', '0')) == 2:
				dif = 12
			scrW = int(scale * 1280) - val(2 * dif)
			butX = scrW - val(70)
			s = s.replace('_dif_', valStr(dif))
			s = s.replace('_miniW_', str(scrW)).replace('_miniH_', valStr(44))
			s = s.replace('_mX0_', valStr(52)).replace('_mY0_', valStr(6)).replace('%path%', PATH)
			s = s.replace('_mX1_', str(butX)).replace('_mY1_', valStr(7))
			s = s.replace('_mW1_', valStr(60)).replace('_mH1_', valStr(28))
			s = s.replace('_mX2_', valStr(5)).replace('_mY2_', valStr(2)).replace('_mW2_', valStr(34)).replace('_mH2_', valStr(34))
			s = s.replace('_gt_', '&gt;')
			self.skin = s
		s = s.replace('_scrW_', str(scrW)).replace('_scrH_', str(scrH))
		s = s.replace('_lineW_', valStr(2)).replace('_lineX_', valStr(900 - 2))
		s = s.replace('_y0a_', valStr(11)).replace('_y0b_', valStr(2)).replace('_y0c_', valStr(23)).replace('_y0d_', valStr(57))
		s = s.replace('_x0_', valStr(20)).replace('_y0_', valStr(0)).replace('_w0_', valStr(780)).replace('_h0_', valStr(55))
		s = s.replace('_x1_', valStr(20)).replace('_y1_', valStr(20 + 55)).replace('_w1_', valStr(900 - 22)).replace('_h1_', valStr(490 - 50 - 30))
		#buttons/label
		cPos = pos = 0
		step = scrW / 4
		dif = val(12)
		buttonH = val(30)
		s2 = ''
		but = '<widget source="key_%1" render="Label" position="%2,' + str(scrH - buttonH - dif)
		but += '" zPosition="4" size="' + sizeStr(step, buttonH) + '" '
		but += ' font="Regular;' + valStr(20) + '" foregroundColor="#cccccc" halign="center" valign="top" transparent="1" />'
		lab = '<eLabel backgroundColor="#%3" position="%4,' + str(scrH - dif) + '" size="' + sizeStr(step, dif) + '" zPosition="4"/>'
		for k in ["red", "green", "yellow", "blue"]:
			s2 += but.replace("%1", k).replace("%2", str(pos))
			pos += step
		for c in ["b81c46", "009f3c", "9ca81b", "2673ec"]:
			s2 += lab.replace("%3", c).replace("%4", str(cPos))
			cPos += step
		s = s.replace("*buttons*", s2)
		self.skin = s

	def showAlerts(self, answer=True):
		s = s2 = ''
		error = False
		try:
			s = data.getNinaMsg(False, self.detailled)
			s2 = getARS(True)
		except:
			s = _('Abfrage nicht m_oeglich')
			error = True
		if data.miniView:
			if len(data.miniMessages):
				s = self.indexInfo() + data.miniMessages[0]
			self["infoSmall"].setText(s)
		else:
			self["scrolltext0"].setText(s)
			self.scrollLabelRepair(self["scrolltext0"])
			if data.hasAdditionalARS():
				self["ARS"].setText('Amtliche NINA-Warnungen')
			else:
				self["ARS"].setText(s2)
		self.onTimerRun()
		data.lastDoubleTime = datetime.now()
		return error

	def cfg(self): self.session.openWithCallback(self.warnReset, cfg.WarnCfg); self.countDown = -1

	def ok(self):
		self.countDown = -1
		if data.miniView:
			pNina.runFullView = True
			self.close()

	def warnReset(self, _=''):
		try:
			cfg.warnReset('')
			self.showAlerts()
			self.countDown = -1
		except:
			pass
		self._setText("countdown", '')
		self.timer.start(1000, True)

	def green(self): self._setText("countdown", 'Aktualisieren... '); self.refresh = True; self.timer.start(100, True)

	def showDetail(self, init=True):
		if init:
			self._setText("countdown", 'Detailabfrage... ')
			self.loadDetail = True
			self.timer.start(100, True)
		else:
			self.detailled = True
			self.warnReset()
			self.countDown = -1

	def down(self): self.up(False)

	def up(self, isUp=True):
		self.countDown = -1
		try:
			for k in self.keys():
				if k.startswith('scroll'):
					if isUp:
						self[k].pageUp()
					else:
						self[k].pageDown()
		except:
			pass

	def onTimerRun(self, initOnly=0):
		self.timer.stop()
		self._setText("time", datetime.now().strftime("%H:%M:%S   "))
		self._setText("date", datetime.now().strftime("%Y-%m-%d   "))
		if initOnly:
			return 0
		if self.init:
			self.init = 0
			self.showAlerts()
			return 0
		if self.loadDetail:
			self.loadDetail = False
			self.showDetail(False)
			return 0
		if self.refresh:
			self.refresh = False
			self.warnReset()
			return 0
		if self.countDown >= 0:
			if self.countDown > 600:
				s = str(self.countDown / 60) + ' Min. '
			else:
				s = str(self.countDown) + ' Sek. '
			self._setText("countdown", _('Schlie_ssen in ') + s)
			self.countDown -= 1
			if self.countDown < 0:
				self.close()
				return 0
		else:
			self._setText("countdown", '')
		try:
			if data.miniView and (len(data.miniMessages) > 1):
				self.msgLoop = [self.msgLoop + 1, 0][self.msgLoop > 2]
				if self.msgLoop == 0:
					self.msgIdx = [self.msgIdx + 1, 0][self.msgIdx + 1 >= len(data.miniMessages)]
					self["infoSmall"].setText(self.indexInfo() + data.miniMessages[self.msgIdx])
		except:
			pass
		self.timer.start(1000, True)

	def indexInfo(self):
		if len(data.miniMessages) <= 1:
			return ''
		return '(' + str(self.msgIdx + 1) + '/' + str(len(data.miniMessages)) + ') '

	def closeProc(self):
		self.timer.stop()
		data.wasAlarm = False
		data.miniView = False
		self.detailled = False
		data.lastDoubleTime = datetime.now()
		pNina.restartTimer()

	def onValueShow(self): pass
	def keyCancel(self): self.close()

	def scrollLabelRepair(self, elem):   #workaround (bug in scrolllabel.py)
		try:
			if (elem.long_text != None) and (elem.pageHeight) and (elem.pages > 10):
				s = elem.long_text.size()
				elem.long_text.resize(eSize(s.width(), elem.pageHeight * elem.pages))
				elem.updateScrollbar()
		except:
			pass


##############################################################################88

class NinaMonitor ():
	def __init__(self):
		self.interval = 9999
		self.loop = 0
		self.ninaS = ''
		self.runFullView = False
		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.onCheck)
		self.finishTimer = eTimer()
		self.finishTimer.callback.append(self.onCheckFinish)

	def stopTimer(self): self.checkTimer.stop()

	def getInterval(self, alarm=None):
		if data.afterAlarm():
			return 1
		else:
			return getInt(configValue('interval', 10))

	def restartTimer(self, wasError=False):
		try:
			if self.runFullView:
				self.checkTimer.start(100, True)
				return 0
			if self.getInterval(False) > 0:
				if self.loop < 0:
					self.interval = 4999
					self.loop = 0
					cfg.warnReset()  #Testalarm, wenn loop==-1
				elif self.loop == 0:
					self.interval = 9999
				else:
					self.interval = 1000 * 60 * self.getInterval()
					if wasError:
						self.interval = min(self.interval, 2 * 60 * 1000) #im Fehlerfall mind. nach 2 Min nachladen
				self.checkTimer.start(self.interval, True)
				self.loop += 1
		except Exception as e:
			exceptDebug(e, 'restartTimer: ')

	def onCheckFinish(self, wasStandby=True):
		self.finishTimer.stop()
		if data.isStandby():
			self.finishTimer.start(2000)
			return 0
		mainSession.open(NinaScreen, wasStandby)
		if (self.interval != 9999) and not wasStandby and (self.interval != 4999) and self.ninaS and (self.ninaS.find('#EMUL') < 0):
			data.setAlarmEnd()

	def onCheck(self):
		global mainSession
		self.stopTimer()
		error = False
		try:
			if (mainSession != None):
				s = data.getNinaMsg(True)
				error = data.wasError
				if s or self.runFullView:
					self.ninaS = s
					data.wasAlarm = not self.runFullView
					if self.runFullView:
						self.runFullView = False
						data.miniView = False
					else:
						data.miniView = (not data.wasExtreme) and getInt(configValue('format', '0')) > 0
					data.wasExtreme = False
					if cfg.wakeUpOk():
						if data.wakeUp():
							self.finishTimer.start(2000)
							data.miniView = False
							return 0
					self.onCheckFinish(False)
					return 0
				else:
					data.bufferedJson = ''
		except Exception as e:
			error = True
			exceptDebug(e, 'onCheck: ')
		#except: error=True
		self.runFullView = False
		self.restartTimer(error)

	def gotSession(self, session):
		#self.dialog = session.instantiateDialog(NinaScreen)#self.dialog.hide()
		self.restartTimer()


pNina = NinaMonitor()

##############################################################################


def sessionstart(reason, **kwargs):
	global mainSession
	mainSession = kwargs["session"]
	if reason == 0:
		pNina.gotSession(kwargs["session"])


def Main(session, **kwargs):
	global mainSession
	mainSession.open(NinaScreen)

##############################################################################


def Plugins(**kwargs):
	return [PluginDescriptor(
			 	where=[PluginDescriptor.WHERE_SESSIONSTART],
				fnc=sessionstart),
			PluginDescriptor(
				name="Warnmeldungen",
				description=_("Amtliche Notfall-Informationen (NINA)"),
				where=[PluginDescriptor.WHERE_PLUGINMENU],
				icon="plugin.png",
				needsRestart=True,
				fnc=Main)
			]

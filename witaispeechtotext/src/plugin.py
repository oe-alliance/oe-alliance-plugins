from __future__ import print_function
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigBoolean
import os

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, getConfigListEntry, ConfigText
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

from enigma import eTimer

import requests
import json
import threading

config.plugins.witaisttsetup = ConfigSubsection()
config.plugins.witaisttsetup.serverAccessToken = ConfigText(fixed_size=False, visible_width=32)

g_session = None


class WitAiSttSetup(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="550,350">
			<ePixmap pixmap="skin_default/buttons/red.png" position="55,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="355,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="55,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="355,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="description" render="Label" position="10,50" size="500,220" font="Regular;24" halign="left" valign="center" />
			<widget name="config" zPosition="2" position="10,270" size="530,30" scrollbarMode="showOnDemand" transparent="1" />
			<ePixmap pixmap="skin_default/buttons/key_text.png" position="510,310" zPosition="10" size="35,25" transparent="1" alphatest="on" />
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session

		self["shortcuts"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session)
		self["VirtualKB"].setEnabled(True)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		text = ""
		text += _("\"Wit.ai speech to text Setup\" gets the speech data from VUPLUS-BLE-RCU and converts it to text using wit.ai.\n\n")
		text += _("1. Sign up for wit.ai (https://wit.ai)\n")
		text += _("2. Enter \"server access token\" under the settings menu to below.\n")

		self["description"] = StaticText(_(text))
		self.createConfig()
		self.onLayoutFinish.append(self.onLayoutFinishCB)

	def onLayoutFinishCB(self):
		self.setTitle(_("Wit.ai Speech to Text Setup"))
		self.createSetup()

		pos = 50
		if self.session.desktop.size().height() > 720:
			pos = 80

		from enigma import ePoint
		help_win = self["config"].getCurrent()[1].help_window.instance
		orgpos = help_win.position()
		help_win.move(ePoint(orgpos.x(), orgpos.y() + pos))
		self.keyLeft()

	def createConfig(self):
		self.tokenEntry = getConfigListEntry(_("Input server access token"), config.plugins.witaisttsetup.serverAccessToken)

	def createSetup(self):
		self.list = []
		self.list.append(self.tokenEntry)
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keySave(self):
		self.saveAll()
		self.close()

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()


witaistt_thread_instance = None


class WitAiSttThread(threading.Thread):
	def __init__(self, textCB):
		threading.Thread.__init__(self)
		self.running = False
		self.voicePath = "/tmp/voice.wav"
		self.textCB = textCB

	def updateTime(self):
		os.system("ntpd -nqp 0.rhel.pool.ntp.org")

	def runRequestPost(self):
		text = None
		serverAccessToken = config.plugins.witaisttsetup.serverAccessToken.value
		if serverAccessToken:
			fd = open(self.voicePath, 'rb').read()
			full_url = "https://api.wit.ai/speech"
			headers = {
			 'authorization': 'Bearer %s' % serverAccessToken,
			 'accept': 'application/vnd.wit.20160526+json',
			 'Content-Type': 'audio/wav'
			}

			#params = {'verbose':True}
			resp = requests.post(
				  url=full_url,
				  data=fd,
				  headers=headers)
			if resp.status_code == 200:
				text = resp.json()['_text']

		return text

	def run(self):
		if self.running:
			return

		text = None

		try:
			text = self.runRequestPost()
		except requests.exceptions.SSLError:
			print("[WitAiSttThread] update current time")
			self.updateTime()
			try:
				text = self.runRequestPost()
			except:
				print("[WitAiSttThread] unknown error.")
		except:
			print("[WitAiSttThread] unknown error.")

		print("[WitAiSttThread] response text : ", text)

		self.textCB(text)

	def setVoicePath(self, voicePath):
		self.voicePath = voicePath


class WitAiSpeechToText:
	def __init__(self):
		self.sendTextTimer = eTimer()
		self.sendTextTimer.callback.append(self.sendText)
		self.closeMsgTimer = eTimer()
		self.closeMsgTimer.callback.append(self.closeMessage)
		self.msgFailTimer = eTimer()
		self.msgFailTimer.callback.append(self.showMsgFail)
		self.msg_instance = None
		self.text = None
		self.voicePath = "/tmp/voice.wav"
		self.running = False	

	def setVoicePath(self, voicePath):
		self.voicePath = voicePath

	def start(self):
		if self.running:
			return
		
		self.running = True
		self.text = None

		global witaistt_thread_instance
		witaistt_thread_instance = WitAiSttThread(self.STTCallBack)
		witaistt_thread_instance.setVoicePath(self.voicePath)
		
		global g_session
		self.msg_instance = g_session.openWithCallback(self.msgCallback, MessageBox, _("Converting speech to text using wit.ai server..."), type=MessageBox.TYPE_INFO, enable_input=False, timeout=30)

		witaistt_thread_instance.start()

	def STTCallBack(self, text):
		self.text = text
		self.closeMsgTimer.start(100, True)

	def closeMessage(self):
		if self.msg_instance:
			self.msg_instance.close(True)

	def msgCallback(self, ret):
		self.msg_instance = None

		if self.text:
			self.sendTextTimer.start(100, True)
		else:
			self.msgFailTimer.start(100, True)

	def sendText(self):
		text = self.text
		self.text = None

		from Plugins.SystemPlugins.BluetoothSetup.bt import pybluetooth_instance
		if pybluetooth_instance:
			pybluetooth_instance.textEventCallback(text)
		self.running = False

	def showMsgFail(self):
		global g_session
		msg = _("Conversion of speech to text failed.\nPlease check auth token in Wit.ai STT Setup Plugin.")
		g_session.openWithCallback(self.msgFailCB, MessageBox, msg, type=MessageBox.TYPE_ERROR, timeout=10)

	def msgFailCB(self, ret):
		self.running = False


witaispeechtotext_instance = WitAiSpeechToText()


def main(session, **kwargs):
	session.open(WitAiSttSetup)


def voiceHandler(voicePath):
	global witaispeechtotext_instance
	witaispeechtotext_instance.setVoicePath(voicePath)
	witaispeechtotext_instance.start()


def auto_start_main(reason, **kwargs):
	if reason == 0:
		pass

	else:
		try:
			from Plugins.SystemPlugins.BluetoothSetup.bt import pybluetooth_instance
			if pybluetooth_instance:
				pybluetooth_instance.removeVoiceHandler(voiceHandler)

			global witaistt_thread_instance
			if witaistt_thread_instance:
				witaistt_thread_instance.join()
		except:
			pass


def sessionstart(reason, session):
	global g_session
	g_session = session

	try:
		from Plugins.SystemPlugins.BluetoothSetup.bt import pybluetooth_instance
		if pybluetooth_instance:
			pybluetooth_instance.addVoiceHandler(voiceHandler)
	except:
		pass


def Plugins(**kwargs):
	list = []
	list.append(
		PluginDescriptor(name=_("Wit.ai Speech to Text Setup"),
		description=_("Speech to text using Wit.ai for VUPLUS-BLE-RCU."),
		where=[PluginDescriptor.WHERE_PLUGINMENU],
		needsRestart=False,
		fnc=main))

	list.append(
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=auto_start_main))

	list.append(
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart))

	return list


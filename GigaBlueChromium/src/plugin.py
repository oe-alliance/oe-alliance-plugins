

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.config import config

import time
import subprocess
from . import cbcfg
from . import pipc

from enigma import eTimer, fbClass, eRCInput, eDVBResourceManager, eDVBVolumecontrol
from Tools.Transponder import ConvertToHumanReadable
from .pipc import PServerThread, PServerHandlers
from .youtube import YoutubeTVWindow, YoutubeTVSettings
from .chromium import ChromiumOSWindow, ChromiumOSSettings

_g_launcher_handler = None
pipc._SOCKETFILE = '/tmp/.chromium.sock'
cbcfg.INIT(cbcfg._ERROR)
_g_locked = False


def enigma2_lock():
	global _g_locked
	cbcfg.DEBUG('enigma2_lock')
	_g_locked = True
	eRCInput.getInstance().lock()


def enigma2_unlock():
	global _g_locked
	cbcfg.DEBUG('enigma2_unlock')
	_g_locked = False
	eRCInput.getInstance().unlock()


_OPCODES = ['CONTROL_EXIT', 'VIRTUAL_KEYBOARD', 'OPCODE_END']


class BrowserHandlers(PServerHandlers):

	def __init__(self):
		print('BrowserHandlers:__init__')
		PServerHandlers.__init__(self, _OPCODES, '_CBH_')
		self._player_exit_cb()

	def _player_exit_cb(self, ret=None):
		print('BrowserHandlers:_player_exit_cb')
		try:
			self.playerHandle.playlist.clear()
		except:
			pass

		self.playerHandle = None

	def _CBH_CONTROL_EXIT(self, result, packet):
		global _g_launcher_handler
		print('BrowserHandlers:_CBH_CONTROL_EXIT')
		try:
			if _g_launcher_handler is not None:
				_g_launcher_handler.Exit()
				_g_launcher_handler = None
		except Exception as err:
			cbcfg.ERROR('%s', err)
			return (False, None)

		return (True, None)

	def _CBH_VIRTUAL_KEYBOARD(self, result, packet):
		print('BrowserHandlers:_CBH_VIRTUAL_KEYBOARD')
		default_data = packet
		returned_data = None
		try:
			_g_launcher_handler.ShowVirtualKeyborad(default_data)
			while True:
				returned_data = _g_launcher_handler.GetVirtualKeyboardData()
				if returned_data is not None:
					break
				time.sleep(1)

		except Exception as err:
			cbcfg.ERROR('%s', err)
			return (False, None)

		return (True, returned_data)


_HANDLER = BrowserHandlers()


class BBrowserLauncher(Screen):
	skin = '<screen name="BBrowserLauncher" position="0,0" size="0,0" backgroundColor="transparent" flags="wfNoBorder" title=" "></screen>'

	def __init__(self, session, mode=None, url='http://gigablue.de'):
		global _g_launcher_handler
		print('BBrowserLauncher:__init__')
		self.session = session
		Screen.__init__(self, session)
		self.isMute = -1
		self.pServerThread = PServerThread()
		self.pServerThread.open(timeout=1)
		self.pServerThread.start()
		self.closeTimer = eTimer()
		self.closeTimer.timeout.get().append(self._cb_CloseTimer)
		_g_launcher_handler = self
		cbcfg.g_service = session.nav.getCurrentlyPlayingServiceReference()
		if cbcfg.g_service is not None:
			feId = self.GetCurrentFeId()
			session.nav.stopService()
			if feId != -1:
				self.TryCloseFrontend(feId)
		if eDVBVolumecontrol.getInstance().isMuted():
			eDVBVolumecontrol.getInstance().volumeUnMute()
			self.isMute = 1
		else:
			self.isMute = 0
		cbcfg.DEBUG('[Chromium Plugin] ==== >> default mute [%d]' % self.isMute)
		command = '/usr/local/chromium/run.sh '
		if mode == 'youtubetv':
			self.setTitle(_('YouTubeTV'))
			command += '-u %s -x 0 -y 0 ' % config.plugins.browser.youtube_uri.value
			if config.plugins.browser.youtube_enable_ntpd.value == True:
				command += '-n %s ' % config.plugins.browser.youtube_ntpd_url.value
			try:
				if config.plugins.fccsetup.activate.value == True:
					command += '-d 4'
			except:
				pass

			command += '&'
		elif mode == 'chromiumos':
			self.setTitle(_('ChromiumOS'))
			command += '-c %s ' % config.plugins.browser.startup.value
			command += '-x %d -y %d ' % (config.plugins.browser.margin_x.value, config.plugins.browser.margin_y.value)
			if config.plugins.browser.enable_ntpd.value == True:
				command += '-n %s ' % config.plugins.browser.ntpd_url.value
			command += '-r %s ' % config.plugins.browser.rcu_type.value
			try:
				if config.plugins.fccsetup.activate.value == True:
					command += '-d 4'
			except:
				pass

			command += '&'
		else:
			self.setTitle(_('ChromiumOS by STT'))
			command += '-c %s ' % url
			command += '-x %d -y %d ' % (config.plugins.browser.margin_x.value, config.plugins.browser.margin_y.value)
			if config.plugins.browser.enable_ntpd.value == True:
				command += '-n %s ' % config.plugins.browser.ntpd_url.value
			command += '-r %s ' % config.plugins.browser.rcu_type.value
			try:
				if config.plugins.fccsetup.activate.value == True:
					command += '-d 4'
			except:
				pass

			command += '&'
		subprocess.call(command, shell=True)
		self.enigma2LockTimer = eTimer()
		self.enigma2LockTimer.timeout.get().append(self._cb_enigma2LockTimer)
		self.enigma2LockTimer.start(2000)
		self.virtual_keyboard_data = None
		self.virtual_keyboard_closed = True

	def GetCurrentFeId(self):
		print('BBrowserLauncher:GetCurrentFeId')
		feId = -1
		sref = self.session.nav.getCurrentService()
		if sref is not None:
			feInfo = sref.frontendInfo()
			feDatas = feInfo and feInfo.getAll(False)
			if feDatas and len(feDatas):
				feData = ConvertToHumanReadable(feDatas)
				feId = int(feData['tuner_number'])
		return feId

	def TryCloseFrontend(self, feId):
		print('BBrowserLauncher:TryCloseFrontend')
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			raw_channel = res_mgr.allocateRawChannel(feId)
			if raw_channel:
				frontend = raw_channel.getFrontend()
				if frontend:
					frontend.closeFrontend()
					del frontend
					del raw_channel
					return True
		return False

	def _cb_enigma2LockTimer(self):
		print('BBrowserLauncher:_cb_enigma2LockTimer')
		self.enigma2LockTimer.stop()
		enigma2_lock()

	def Exit(self):
		print('BBrowserLauncher:Exit')
		if self.isMute:
			eDVBVolumecontrol.getInstance().volumeMute()
		else:
			eDVBVolumecontrol.getInstance().volumeUnMute()
		cbcfg.DEBUG('[Chromium Plugin] ==== >> default mute [%d] , restore mute [%d]' % (self.isMute, self.isMute))
		self.closeTimer.start(1500)

	def _cb_CloseTimer(self):
		print('BBrowserLauncher:_cb_CloseTimer')
		self.closeTimer.stop()
		self.pServerThread.kill()
		self.pServerThread.join()
		enigma2_unlock()
		if cbcfg.g_service is not None:
			self.session.nav.playService(cbcfg.g_service)
		self.close()

	def _virtual_keyborad_closed_cb(self, data):
		print('BBrowserLauncher:_virtual_keyborad_closed_cb')
		self.virtual_keyboard_data = data
		self.virtual_keyboard_closed = True

	def GetVirtualKeyboardData(self):
		print('BBrowserLauncher: GetVirtualKeyboardData')
		if self.virtual_keyboard_closed == False:
			return
		eRCInput.getInstance().lock()
		if self.virtual_keyboard_data is None:
			return ''
		return self.virtual_keyboard_data

	def ShowVirtualKeyborad(self, default_data='http://'):
		print('BBrowserLauncher:ShowVirtualKeyborad')
		eRCInput.getInstance().unlock()
		self.virtual_keyboard_data = None
		self.virtual_keyboard_closed = False
		self.session.openWithCallback(self._virtual_keyborad_closed_cb, VirtualKeyBoard, title=_('Chromium Virtual Keyboard'), text=default_data)


global_session = None


def stt_event_callback(text):
	global global_session
	global _g_locked
	print('stt_event_callback')
	url = 'https://www.google.co.kr/search?q=' + text.replace(' ', '+')
	if global_session is not None and _g_locked == False:
		enigma2_unlock()
		_g_locked = True
		cbcfg.g_browser = global_session.open(BBrowserLauncher, mode='chromiumos_stt', url=url)


def start_youtubetv_main(session, **kwargs):
	print('start_youtubetv_main')

	def _cb_youtubetv_close(ret):
		if ret:
			enigma2_unlock()
			cbcfg.g_browser = session.open(BBrowserLauncher, mode='youtubetv')

	if config.plugins.browser.youtube_showhelp.value == True:
		_cb_youtubetv_close(True)
	else:
		session.openWithCallback(_cb_youtubetv_close, YoutubeTVWindow)


def menu_start_youtube(menuid, **kwargs):
	print(' menu_start_youtube')
	if menuid == 'mainmenu':
		return [(_('YouTubeTV'),
		  start_youtubetv_main,
		  'youtubetv',
		  46)]
	return []


def plugin_setting_youtube(session, **kwargs):
	print('plugin_setting_youtube')
	session.open(YoutubeTVSettings)


def plugin_start_chromiumos(session, **kwargs):
	print('plugin_start_chromiumos')
	enigma2_unlock()

	def _cb_chromiumos_close(ret):
		if ret:
			enigma2_unlock()
			cbcfg.g_browser = session.open(BBrowserLauncher, mode='chromiumos')

	cbcfg.g_browser = session.openWithCallback(_cb_chromiumos_close, ChromiumOSWindow)


def session_start_main(session, reason, **kwargs):
	global global_session
	print('session_start_main')
	PServerThread.close()
	try:
		from Plugins.SystemPlugins.BluetoothSetup.bt import pybluetooth_instance
		pybluetooth_instance.addTextHandler(stt_event_callback)
		global_session = session
	except:
		pass


def Plugins(**kwargs):
	l = []
	l.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=session_start_main))
	if config.plugins.browser.youtube_mainmenu.getValue():
		l.append(PluginDescriptor(name=_('YouTubeTV'), where=PluginDescriptor.WHERE_MENU, icon='youtubetv.png', fnc=menu_start_youtube))
	if config.plugins.browser.youtube_extmenu.getValue():
		l.append(PluginDescriptor(name=_('YouTubeTV'), where=PluginDescriptor.WHERE_PLUGINMENU, icon='youtubetv.png', fnc=start_youtubetv_main))
	l.append(PluginDescriptor(name=_('YouTubeTV Settings'), where=PluginDescriptor.WHERE_PLUGINMENU, icon='youtubetv.png', fnc=plugin_setting_youtube))
	l.append(PluginDescriptor(name=_('ChromiumOS'), description=_('Start ChromiumOS'), where=PluginDescriptor.WHERE_PLUGINMENU, icon="chromium.png", needsRestart=True, fnc=plugin_start_chromiumos))
	return l

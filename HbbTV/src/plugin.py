from __future__ import absolute_import
import os
import struct
import six
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import InfoBar
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import eTimer, fbClass, eRCInput, iServiceInformation, iPlayableService, eDVBVolumecontrol
from . import vbcfg
from .__init__ import _
from .hbbtv import HbbTVWindow
from .browser import Browser
from .youtube import YoutubeTVWindow, YoutubeTVSettings
from .vbipc import VBController, VBServerThread, VBHandlers

strIsEmpty = lambda x: x is None or len(x) == 0

vbcfg.SOCKETFILE = '/tmp/.browser.support'
vbcfg.CONTROLFILE = '/tmp/.browser.controller'
_OPCODE_LIST = [
		'CONTROL_BACK',
		'CONTROL_FORWARD',
		'CONTROL_STOP',
		'CONTROL_RELOAD',
		'CONTROL_OPENURL',
		'CONTROL_EXIT',
		'CONTROL_TITLE',
		'CONTROL_OK',
		'CONTROL_OUT_OF_MEMORY',
		'CONTROL_INVALIDATE',
		'CONTROL_GET_FBSIZE',
		'CONTROL_GET_VOLUME',
		'CONTROL_SET_VOLUME',
		'CONTROL_VOLUME_UP',
		'CONTROL_VOLUME_DOWN',
		'HBBTV_LOADAIT',
		'HBBTV_OPENURL',
		'YOUTUBETV_OPENURL',
		'BROWSER_OPENURL',
		'BROWSER_MENU_OPEN',
		'BROWSER_MENU_CLOSE',
		'BROWSER_VKB_OPEN',
		'BROWSER_VKB_CLOSE',
		'OOIF_GET_CURRENT_CHANNEL',
		'OOIF_BROADCAST_PLAY',
		'OOIF_BROADCAST_STOP',
		'OOIF_BROADCAST_CHECK',
		'CONTROL_RELOAD_KEYMAP',
		'OPCODE_END'
		]


class VBHandler(VBHandlers):
	def __init__(self, session):
		self._session = session
		self.current_title = None
		self.max_volume = -1
		self.soft_volume = -1
		self.videobackend_activate = False
		self.onSetTitleCB = []
		self.onCloseCB = []
		VBHandlers.__init__(self, _OPCODE_LIST, '_CB_')
		self.hdmi_cec = None
		try:
			from Components.HdmiCec import hdmi_cec
			if hdmi_cec.instance and hasattr(hdmi_cec.instance, "keyVolUp"):
				self.hdmi_cec = hdmi_cec.instance
		except ImportError:
			pass

	def set_volume(self, volume):
		if self.hdmi_cec:
			ret = 0
			if volume == 5:
				ret = self.hdmi_cec.keyVolUp()
			else:
				ret = self.hdmi_cec.keyVolDown()
			if ret:
				return

		if self.max_volume < 0:
			self.max_volume = eDVBVolumecontrol.getInstance().getVolume()

		self.max_volume += volume
		if self.max_volume > 100:
			self.max_volume = 100
		elif self.max_volume < 0:
			self.max_volume = 0

		if self.soft_volume > 0:
			v = int((self.max_volume * self.soft_volume) / 100)
			eDVBVolumecontrol.getInstance().setVolume(v, v)
		else:
			eDVBVolumecontrol.getInstance().setVolume(self.max_volume, self.max_volume)

	def close_vkb(self, data=""):
		fbClass.getInstance().lock()
		eRCInput.getInstance().lock()

		if strIsEmpty(data):
			data = ""
		VBController.command("BROWSER_VKB_CLOSE", data)

	def _CB_CONTROL_EXIT(self, result, packet):
		if self.onCloseCB:
			for x in self.onCloseCB:
				try:
					x()
				except Exception:
					if x in self.onCloseCB:
						self.onCloseCB.remove(x)
		if self.videobackend_activate is False:
			if vbcfg.g_service is not None:
				self._session.nav.playService(vbcfg.g_service)
		return (True, None)

	def _CB_CONTROL_TITLE(self, result, packet):
		if packet.startswith(b'file://') or packet.startswith(b'http://'):
			return (True, None)
		for x in self.onSetTitleCB:
			try:
				x(packet)
				self.current_title = packet
			except Exception:
				if x in self.onSetTitleCB:
					self.onSetTitleCB.remove(x)
		return (True, None)

	def _CB_CONTROL_OK(self, result, packet):
		if vbcfg.g_browser and packet.startswith(b'stop'):
			vbcfg.g_browser.keyOK()
		return (True, None)

	def _CB_CONTROL_OUT_OF_MEMORY(self, result, packet):
		vbcfg.need_restart = True
		return (True, None)

	def _CB_CONTROL_INVALIDATE(self, result, packet):
		# redraw enigma
		from enigma import getDesktop
		getDesktop(0).paint()
		return (True, None)

	def _CB_CONTROL_GET_FBSIZE(self, result, packet):
		from enigma import getDesktop
		desktop_size = getDesktop(0).size()
		data = "%dx%d" % (desktop_size.width(), desktop_size.height())
		return (True, data)

	def _CB_CONTROL_SET_VOLUME(self, result, packet):
		if self.max_volume < 0:
			self.max_volume = eDVBVolumecontrol.getInstance().getVolume()
		self.soft_volume = int(packet)

		v = 0
		if self.soft_volume > 0 and self.max_volume > 0:
			v = int((self.max_volume * self.soft_volume) / 100)
		eDVBVolumecontrol.getInstance().setVolume(v, v)
		return (True, None)

	def _CB_CONTROL_VOLUME_UP(self, result, packet):
		self.set_volume(5)
		return (True, None)

	def _CB_CONTROL_VOLUME_DOWN(self, result, packet):
		self.set_volume(-5)
		return (True, None)

	def _CB_BROWSER_MENU_OPEN(self, result, packet):
		if vbcfg.g_browser and vbcfg.g_browser.is_browser_opened:
			vbcfg.setPosition(vbcfg.g_position)
			fbClass.getInstance().unlock()
			eRCInput.getInstance().unlock()

			vbcfg.g_browser.toggle_browser(packet, self.current_title)
		return (True, None)

	def _CB_BROWSER_VKB_OPEN(self, result, packet):
		if vbcfg.g_browser and vbcfg.g_browser.is_browser_opened:
			vbcfg.setPosition(vbcfg.g_position)
			fbClass.getInstance().unlock()
			eRCInput.getInstance().unlock()

			if strIsEmpty(packet):
				packet = ""
			self._session.openWithCallback(self.close_vkb, VirtualKeyBoard, title=("Please enter URL here"), text=str(packet))
		return (True, None)

	def _CB_OOIF_GET_CURRENT_CHANNEL(self, result, packet):
		if (vbcfg.g_channel_info):
			try:
				data = struct.pack('iiii', vbcfg.g_channel_info[0], vbcfg.g_channel_info[1], vbcfg.g_channel_info[2], len(vbcfg.g_channel_info[3]))
				if six.PY3:
					data += bytes(vbcfg.g_channel_info[3], 'utf-8')
				else:
					data += vbcfg.g_channel_info[3]
			except Exception as err:
				vbcfg.ERR(err)
				return (False, None)
		else:
			return (False, None)
		return (True, data)

	def _CB_OOIF_BROADCAST_PLAY(self, result, packet):
		if vbcfg.g_service is not None:
			self._session.nav.playService(vbcfg.g_service)
		self.videobackend_activate = False
		return (True, None)

	def _CB_OOIF_BROADCAST_STOP(self, result, packet):
		vbcfg.g_service = self._session.nav.getCurrentlyPlayingServiceReference()
		self._session.nav.stopService()
		self.videobackend_activate = True
		return (True, None)

	def _CB_OOIF_BROADCAST_CHECK(self, result, packet):
		if self._session.nav.getCurrentService() is None:
			return (False, None)
		return (True, None)


class VBMain(Screen):
	skin = """<screen name="VBMAIN" position="0,0" size="0,0" backgroundColor="transparent" flags="wfNoBorder" title=" "></screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.vbcallback = None
		self.vbhandler = VBHandler(session)
		self.vbserver = VBServerThread()
		self.vbserver.open(1)
		self.vbserver.start()

		# comment for dev
		self.restart_browser()
		vbcfg.LOG("browser start")

		self._timer_infobar = eTimer()
		self._timer_infobar.callback.append(self._cb_register_infobar)
		self._timer_infobar.start(1000)

		self._event = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evHBBTVInfo: self._cb_ait_detected,
				iPlayableService.evUpdatedInfo: self._cb_info_updated
			})
		self._applicationList = None
		self._app_info = None

		try:
			from Screens.InfoBarGenerics import gHbbtvApplication
			self.m_vuplus = gHbbtvApplication.getUseAit()
		except:
			self.m_vuplus = False

	def _cb_register_infobar(self):
		if InfoBar.instance:
			self._timer_infobar.stop()
			if self._cb_hbbtv_activated not in InfoBar.instance.onHBBTVActivation:
				InfoBar.instance.onHBBTVActivation.append(self._cb_hbbtv_activated)
		vbcfg.DEBUG("registred HbbTV in InfoBar")

	def _cb_hbbtv_activated(self, url=None, app_info=None):
		if not self.check_browser():
			message = _("HbbTV Browser was not running.\nPlease running browser before start HbbTV Application.")
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
			return
		self.start_hbbtv_application(url, app_info)

	def _cb_ait_detected(self):
		vbcfg.g_channel_info = None
		self._applicationList = None
		self._app_info = self.get_autostart_application()
		vbcfg.DEBUG("detected AIT")

	def _cb_info_updated(self):
		vbcfg.g_service = self.session.nav.getCurrentlyPlayingServiceReference()
		vbcfg.DEBUG("updated channel info")

	def start_hbbtv_application(self, url, app_info):
		if vbcfg.need_restart:
			self.restart_browser()
			os.time.sleep(2)
			vbcfg.need_restart = False

		if not app_info:
			app_info = self._app_info
		self.session.open(HbbTVWindow, url, app_info)

	def menu_toggle_browser(self, callback=None):
		mode = []
		self.vbcallback = callback
		if self.check_browser():
			mode.append((_('Stop'), 'Stop'))
		else:
			mode.append((_('Start'), 'Start'))
		self.session.openWithCallback(self.toggle_browser, ChoiceBox, title=_("Please choose one."), list=mode)

	def toggle_browser(self, selected):
		if selected is not None:
			if self.vbcallback:
				self.vbcallback()
			try:
				mode = selected[1]
				if mode == 'Start':
					if not self.check_browser():
						self.start_browser()
				elif mode == 'Stop':
					self.stop_browser()

			except Exception as ErrMsg:
				vbcfg.ERR("toggle browser: %s" % ErrMsg)

	def menu_hbbtv_applications(self):
		applications = []
		if self._applicationList is not None:
			for x in self._applicationList:
				applications.append((x["name"], x))
		else:
			applications.append((_("No detected HbbTV applications."), None))
		self.session.openWithCallback(self.start_application_selected, ChoiceBox, title=_("Please choose an HbbTV application."), list=applications)

	def start_application_selected(self, selected):
		vbcfg.DEBUG(selected)
		try:
			if selected[1] is not None:
				self._cb_hbbtv_activated(selected[1]["url"], selected[1])
		except Exception as ErrMsg:
			vbcfg.ERR(ErrMsg)

	def get_autostart_application(self):
		if self._applicationList is None:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			if info is not None:
				sid = info.getInfo(iServiceInformation.sSID)
				onid = info.getInfo(iServiceInformation.sONID)
				tsid = info.getInfo(iServiceInformation.sTSID)
				name = info.getName()
				vbcfg.g_channel_info = (sid, onid, tsid, name)

				pmtid = info.getInfo(iServiceInformation.sPMTPID)
				demux = info.getInfoString(iServiceInformation.sLiveStreamDemuxId)
				vbcfg.DEBUG("demux = %s, pmtid = 0x%x, sid = 0x%x" % (demux, pmtid, sid))

				from .aitreader import eAITSectionReader
				reader = eAITSectionReader(demux, pmtid, sid)
				if reader.doOpen(info, self.m_vuplus):
					reader.doParseApplications()
					#reader.doDump()
				else:
					vbcfg.ERR("no AIT")

				try:
					self._applicationList = reader.getApplicationList()
				except:
					pass

		if self._applicationList is not None:
			for app in self._applicationList:
				if app["control"] in (1, -1):
					return app
		return None

	def start_browser(self):
		if not self.check_browser():
			os.system("%s/%s start" % (vbcfg.APPROOT, vbcfg.APP_RUN))
		return True

	def stop_browser(self):
		VBController.command('CONTROL_EXIT')
		#try:
		#	os.system("%s/%s stop" % (vbcfg.APPROOT, vbcfg.APP_RUN))
		#except:
		#	pass
		return True

	def check_browser(self):
		try:
			ret = os.popen('%s/%s check' % (vbcfg.APPROOT, vbcfg.APP_RUN)).read()
			return ret.strip() != "0"
		except Exception as ErrMsg:
			vbcfg.ERR("check browser running: %s" % ErrMsg)
		return False

	def restart_browser(self):
		try:
			os.system("%s/%s restart" % (vbcfg.APPROOT, vbcfg.APP_RUN))
		except:
			pass
		return True


def auto_start_main(reason, **kwargs):
	if reason:
		try:
			if vbcfg.g_main.vbserver is not None:
				vbcfg.g_main.vbserver.kill()
		except:
			pass


def session_start_main(session, reason, **kwargs):
	vbcfg.g_main = session.open(VBMain)


def start_youtubetv_main(session, **kwargs):
	def _cb_youtubetv_close(ret):
		if ret:
			vbcfg.g_service = session.nav.getCurrentlyPlayingServiceReference()
			if vbcfg.g_service is not None:
				session.nav.stopService()
			vbcfg.g_browser = session.open(Browser, vbcfg.g_youtubetv_cfg.uri.value, True)

	if config.plugins.youtubetv.showhelp.value is True:
		_cb_youtubetv_close(True)
	else:
		session.openWithCallback(_cb_youtubetv_close, YoutubeTVWindow)


def plugin_setting_youtube(session, **kwargs):
	session.open(YoutubeTVSettings)


def plugin_start_browser(session, **kwargs):
	vbcfg.g_browser = session.open(Browser)


def extension_toggle_browser(session, **kwargs):
	if vbcfg.g_main is not None:
		vbcfg.g_main.menu_toggle_browser()


def extension_start_application(session, **kwargs):
	if vbcfg.g_main is not None:
		vbcfg.g_main.menu_hbbtv_applications()


def Plugins(**kwargs):
	l = []
	l.append(PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=auto_start_main))
	l.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, needsRestart=True, fnc=session_start_main, weight=-10))
	#l.append(PluginDescriptor(name=_("YouTube TV"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=start_youtubetv_main, needsRestart=True))
	#l.append(PluginDescriptor(name=_("YouTube TV Settings"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=plugin_setting_youtube))
	l.append(PluginDescriptor(name=_("Browser Start/Stop"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart=True, fnc=extension_toggle_browser))
	l.append(PluginDescriptor(name=_("HbbTV Applications"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart=True, fnc=extension_start_application))
	l.append(PluginDescriptor(name=_("Opera Web Browser"), description=_("start opera web browser"), where=PluginDescriptor.WHERE_PLUGINMENU, needsRestart=True, fnc=plugin_start_browser))
	return l

from __future__ import absolute_import
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import InfoBar
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ServiceEventTracker import ServiceEventTracker
from Components.VolumeControl import VolumeControl

from enigma import eTimer, iServiceInformation, iPlayableService

import os
import struct
import time

from .__init__ import _
from . import vbcfg
from .hbbtv import HbbTVWindow
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
	'GET_TIME_OFFSET',
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
		ret = 0
		if self.hdmi_cec:
			if volume == 5:
				ret = self.hdmi_cec.keyVolUp()
			else:
				ret = self.hdmi_cec.keyVolDown()
			if ret:
				return

		if self.max_volume < 0:
			self.max_volume = VolumeControl.instance.volctrl.getVolume()

		self.max_volume += volume
		if self.max_volume > 100:
			self.max_volume = 100
		elif self.max_volume < 0:
			self.max_volume = 0

		if self.soft_volume > 0:
			v = int((self.max_volume * self.soft_volume) / 100)
			VolumeControl.instance.volctrl.setVolume(v, v)
		else:
			VolumeControl.instance.volctrl.setVolume(self.max_volume, self.max_volume)

	def close_vkb(self, data=""):
		vbcfg.osd_lock()

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
			self.max_volume = VolumeControl.instance.volctrl.getVolume()
		self.soft_volume = int(packet)

		v = 0
		if self.soft_volume > 0 and self.max_volume > 0:
			v = int((self.max_volume * self.soft_volume) / 100)
		VolumeControl.instance.volctrl.setVolume(v, v)
		return (True, None)

	def _CB_CONTROL_VOLUME_UP(self, result, packet):
		self.set_volume(5)
		return (True, None)

	def _CB_CONTROL_VOLUME_DOWN(self, result, packet):
		self.set_volume(-5)
		return (True, None)

	def _CB_BROWSER_VKB_OPEN(self, result, packet):
		if vbcfg.g_browser and vbcfg.g_browser.is_browser_opened:
			vbcfg.setPosition(vbcfg.g_position)
			vbcfg.osd_unlock()

			if strIsEmpty(packet):
				packet = ""
			self._session.openWithCallback(self.close_vkb, VirtualKeyBoard, title=("Please enter URL here"), text=str(packet))
		return (True, None)

	def _CB_OOIF_GET_CURRENT_CHANNEL(self, result, packet):
		appinfo = vbcfg.g_main.get_autostart_application()
		orgid = appinfo and appinfo["orgid"]
		if (vbcfg.g_channel_info):
			try:
				data = struct.pack('iiiii', int(orgid), vbcfg.g_channel_info[0], vbcfg.g_channel_info[1], vbcfg.g_channel_info[2], len(vbcfg.g_channel_info[3])) + bytes(vbcfg.g_channel_info[3], 'utf-8')
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

	def _CB_GET_TIME_OFFSET(self, result, packet):

		time_struct = time.localtime()
		offset = (time_struct.tm_hour * 3600) + (time_struct.tm_min * 60) + time_struct.tm_sec

		try:
 			data = struct.pack('i', int(offset))
		except Exception as err:
			vbcfg.ERR(err)
			return (False, None)

		return (True, data)


class VBMain(Screen):
	skin = """<screen name="VBMAIN" position="0,0" size="0,0" backgroundColor="transparent" flags="wfNoBorder" title=" "></screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.vbcallback = None
		self.vbhandler = VBHandler(session)
		self.vbserver = VBServerThread()
		self.vbserver.open(1)
		self.vbserver.start()

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
			vbcfg.need_restart = False

		if not app_info:
			app_info = self._app_info

		InfoBar.instance.hide()
		self.session.open(HbbTVWindow, url, app_info)

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
				# avoid demux is 0xFF
				demux = demux if demux > '/' else '0'
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


def auto_start_main(reason, **kwargs):
	if reason:
		try:
			if vbcfg.g_main.vbserver is not None:
				vbcfg.g_main.vbserver.kill()
		except:
			pass


def session_start_main(session, reason, **kwargs):
	vbcfg.g_main = session.open(VBMain)


def extension_start_application(session, **kwargs):
	if vbcfg.g_main is not None:
		vbcfg.g_main.menu_hbbtv_applications()


def Plugins(**kwargs):
	l = []
	l.append(PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=auto_start_main))
	l.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, needsRestart=True, fnc=session_start_main, weight=-10))
	l.append(PluginDescriptor(name=_("HbbTV Applications"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart=True, fnc=extension_start_application))
	return l

from __future__ import absolute_import
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

pipc._SOCKETFILE = "/tmp/.chromium.sock"
cbcfg.INIT(cbcfg._ERROR)

_g_locked = False


def dvbapp_lock():
    cbcfg.DEBUG("dvbapp_lock")
#       fbClass.getInstance().lock()
    global _g_locked
    _g_locked = True
    eRCInput.getInstance().lock()


def dvbapp_unlock():
    cbcfg.DEBUG("dvbapp_unlock")
#       fbClass.getInstance().unlock()
    global _g_locked
    _g_locked = False
    eRCInput.getInstance().unlock()


_OPCODES = ['CONTROL_EXIT', 'VIRTUAL_KEYBOARD', 'OPCODE_END']


class BrowserHandlers(PServerHandlers):
    def __init__(self):
        PServerHandlers.__init__(self, _OPCODES, '_CBH_')
        self._player_exit_cb()

    def _player_exit_cb(self, ret=None):
        try:
            self.playerHandle.playlist.clear()
        except:
            pass
        self.playerHandle = None

    def _CBH_CONTROL_EXIT(self, result, packet):
        try:
            global _g_launcher_handler
            if _g_launcher_handler is not None:
                _g_launcher_handler.Exit()
                _g_launcher_handler = None
        except Exception as err:
            cbcfg.ERROR("%s", err)
            return (False, None)
        return (True, None)

    def _CBH_VIRTUAL_KEYBOARD(self, result, packet):
        default_data = packet
        returned_data = None
        try:
            _g_launcher_handler.ShowVirtualKeyborad(default_data)
            while (True):
                returned_data = _g_launcher_handler.GetVirtualKeyboardData()
                if returned_data is not None:
                    break
                time.sleep(1)
        except Exception as err:
            cbcfg.ERROR("%s", err)
            return (False, None)
        return (True, returned_data)


_HANDLER = BrowserHandlers()


class BBrowserLauncher(Screen):
    skin = """<screen name="BBrowserLauncher" position="0,0" size="0,0" backgroundColor="transparent" flags="wfNoBorder" title=" "></screen>"""

    def __init__(self, session, mode=None, url="http://vuplus.com"):
        self.session = session

        Screen.__init__(self, session)

        self.isMute = -1

        self.pServerThread = PServerThread()
        self.pServerThread.open(timeout=1)
        self.pServerThread.start()

        self.closeTimer = eTimer()
        self.closeTimer.timeout.get().append(self._cb_CloseTimer)

        global _g_launcher_handler
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

        cbcfg.DEBUG("[Chromium Plugin] ==== >> default mute [%d]" % self.isMute)

        command = "/usr/local/chromium/run.sh "
        if mode == "youtubetv":
            self.setTitle(_('YouTubeTV'))
            command += "-u %s -x 0 -y 0 " % (config.plugins.browser.youtube_uri.value)
            if config.plugins.browser.youtube_enable_ntpd.value == True:
                command += "-n %s " % (config.plugins.browser.youtube_ntpd_url.value)
            try:
                if config.plugins.fccsetup.activate.value == True:
                    command += "-d 4"
            except:
                pass
            command += "&"
        elif mode == "chromiumos":
            self.setTitle(_('ChromiumOS'))
            command += "-c %s " % (config.plugins.browser.startup.value)
            command += "-x %d -y %d " % (config.plugins.browser.margin_x.value, config.plugins.browser.margin_y.value)
            if config.plugins.browser.enable_ntpd.value == True:
                command += "-n %s " % (config.plugins.browser.ntpd_url.value)
            command += "-r %s " % (config.plugins.browser.rcu_type.value)
            try:
                if config.plugins.fccsetup.activate.value == True:
                    command += "-d 4"
            except:
                pass
            command += "&"
        else:
            self.setTitle(_('ChromiumOS by STT'))
            command += "-c %s " % (url)
            command += "-x %d -y %d " % (config.plugins.browser.margin_x.value, config.plugins.browser.margin_y.value)
            if config.plugins.browser.enable_ntpd.value == True:
                command += "-n %s " % (config.plugins.browser.ntpd_url.value)
            command += "-r %s " % (config.plugins.browser.rcu_type.value)
            try:
                if config.plugins.fccsetup.activate.value == True:
                    command += "-d 4"
            except:
                pass
            command += "&"

        #os.system(command)
        subprocess.call(command, shell=True)

        self.dvbappLockTimer = eTimer()
        self.dvbappLockTimer.timeout.get().append(self._cb_DvbappLockTimer)
        self.dvbappLockTimer.start(2000)

        self.virtual_keyboard_data = None
        self.virtual_keyboard_closed = True

    def GetCurrentFeId(self):
        feId = -1
        sref = self.session.nav.getCurrentService()
        if sref is not None:
            feInfo = sref.frontendInfo()
            feDatas = feInfo and feInfo.getAll(False)
            if feDatas and len(feDatas):
                feData = ConvertToHumanReadable(feDatas)
                feId = int(feData["tuner_number"])

        return feId

    def TryCloseFrontend(self, feId):
        res_mgr = eDVBResourceManager.getInstance()
        if res_mgr:
            raw_channel = res_mgr.allocateRawChannel(feId)
            if raw_channel:
                frontend = raw_channel.getFrontend()
                if frontend:
                    frontend.closeFrontend()  # immediate close...
                    del frontend
                    del raw_channel
                    return True
        return False

    def _cb_DvbappLockTimer(self):
        self.dvbappLockTimer.stop()
        dvbapp_lock()

    def Exit(self):
        if self.isMute:
            eDVBVolumecontrol.getInstance().volumeMute()
        else:
            eDVBVolumecontrol.getInstance().volumeUnMute()

        cbcfg.DEBUG("[Chromium Plugin] ==== >> default mute [%d] , restore mute [%d]" % (self.isMute, self.isMute))

        self.closeTimer.start(1500)

    def _cb_CloseTimer(self):
        self.closeTimer.stop()

        self.pServerThread.kill()
        self.pServerThread.join()

        dvbapp_unlock()

        if cbcfg.g_service is not None:
            self.session.nav.playService(cbcfg.g_service)
        self.close()

    def _virtual_keyborad_closed_cb(self, data):
        self.virtual_keyboard_data = data
        self.virtual_keyboard_closed = True

    def GetVirtualKeyboardData(self):
        if self.virtual_keyboard_closed == False:
            return None
        eRCInput.getInstance().lock()
        if self.virtual_keyboard_data is None:
            return ""
        return self.virtual_keyboard_data

    def ShowVirtualKeyborad(self, default_data='http://'):
        eRCInput.getInstance().unlock()
        self.virtual_keyboard_data = None
        self.virtual_keyboard_closed = False
        self.session.openWithCallback(self._virtual_keyborad_closed_cb, VirtualKeyBoard, title=(_("Chromium Virtual Keyboard")), text=default_data)


global_session = None


def stt_event_callback(text):
    global _g_locked
    url = "https://www.google.co.kr/search?q=" + text.replace(' ', '+')
    if global_session is not None and _g_locked == False:
        dvbapp_unlock()
        _g_locked = True
        cbcfg.g_browser = global_session.open(BBrowserLauncher, mode="chromiumos_stt", url=url)


def start_youtubetv_main(session, **kwargs):
    def _cb_youtubetv_close(ret):
        if ret:
            dvbapp_unlock()
            cbcfg.g_browser = session.open(BBrowserLauncher, mode="youtubetv")

    if config.plugins.browser.youtube_showhelp.value == True:
        _cb_youtubetv_close(True)
    else:
        session.openWithCallback(_cb_youtubetv_close, YoutubeTVWindow)


def menu_start_youtube(menuid, **kwargs):
    if menuid == "mainmenu":
        return [(_("YouTubeTV"), start_youtubetv_main, "youtubetv", 46)]
    return []


def plugin_setting_youtube(session, **kwargs):
    session.open(YoutubeTVSettings)


def plugin_start_chromiumos(session, **kwargs):
    dvbapp_unlock()

    def _cb_chromiumos_close(ret):
        if ret:
            dvbapp_unlock()
            cbcfg.g_browser = session.open(BBrowserLauncher, mode="chromiumos")
    cbcfg.g_browser = session.openWithCallback(_cb_chromiumos_close, ChromiumOSWindow)


def session_start_main(session, reason, **kwargs):
    PServerThread.close()
    try:
        from Plugins.SystemPlugins.BluetoothSetup.bt import pybluetooth_instance
        pybluetooth_instance.addTextHandler(stt_event_callback)

        global global_session
        global_session = session
    except:
        pass


def Plugins(**kwargs):
    l = []
    l.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=session_start_main))
    l.append(PluginDescriptor(name=_("YouTubeTV"), where=PluginDescriptor.WHERE_MENU, fnc=menu_start_youtube))
    l.append(PluginDescriptor(name=_("YouTubeTV Settings"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=plugin_setting_youtube))
    l.append(PluginDescriptor(name=_("ChromiumOS"), description=_("Start ChromiumOS"), where=PluginDescriptor.WHERE_PLUGINMENU, needsRestart=True, fnc=plugin_start_chromiumos))
    return l

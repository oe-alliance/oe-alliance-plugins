from __future__ import absolute_import
from Plugins.Plugin import PluginDescriptor
from .bt_setup import BluetoothSetupScreen
from .bt import pybluetooth_instance
from enigma import eActionMap, eDVBVolumecontrol

g_BTVolumeControlHandle = None


def main(session, **kwargs):
	session.open(BluetoothSetupScreen)


def bt_keyPressed(key, flag):
	if flag != 0:  # if not release
		global g_BTVolumeControlHandle
		if key in (114, 115):
			if g_BTVolumeControlHandle:
				v = g_BTVolumeControlHandle.getVolume()
				pybluetooth_instance.setVolume(int(v))

		elif key == 113:
			if g_BTVolumeControlHandle:
				if g_BTVolumeControlHandle.isMuted():
					pybluetooth_instance.setVolume(int(0))
				else:
					v = g_BTVolumeControlHandle.getVolume()
					pybluetooth_instance.setVolume(int(v))

	return 0


def auto_start_main(reason, **kwargs):
	if reason == 0:  # when add plugins
		global g_BTVolumeControlHandle
		if g_BTVolumeControlHandle is None:
			g_BTVolumeControlHandle = eDVBVolumecontrol.getInstance()
			eActionMap.getInstance().bindAction('', -0x7FFFFFFF, bt_keyPressed)

	else:  # when remove plugins
		try:
			if pybluetooth_instance:
				pybluetooth_instance.disable()
		except:
			pass


def selSetup(menuid, **kwargs):
	res = []

	if menuid == "system" and pybluetooth_instance.checkBTUSB():
		res.append((_("Bluetooth Setup"), main, "bluetooth_setup", 80))
	return res


def sessionstart(reason, session):
	if pybluetooth_instance:
		pybluetooth_instance.setSession(session)


def Plugins(**kwargs):
	list = []

	list.append(
		PluginDescriptor(name=_(_("BluetoothSetup")),
		description=_("Bluetooth Setup"),
		where=[PluginDescriptor.WHERE_MENU],
		fnc=selSetup))

	list.append(
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=auto_start_main))

	list.append(
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart))

	return list

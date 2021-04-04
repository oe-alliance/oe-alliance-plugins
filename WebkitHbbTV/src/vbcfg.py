from __future__ import print_function
from time import strftime, localtime
from Tools.Directories import fileExists
from enigma import fbClass, eRCInput

import os

g_main = None
g_browser = None
g_youtubetv_cfg = None
g_service = None
g_channel_info = None
g_position = None

need_restart = False

APPROOT = "/usr/bin"
APP_ENV = "MOZ_PLUGIN_PATH=/usr/lib/mozilla/plugins"
APP_RUN = "browser"
APP_INDEX = "/home/root/none.html"

PLUGINROOT = "/usr/lib/enigma2/python/Plugins/Extensions/WebkitHbbTV"
MANUALROOT = "/usr/local/manual"
DFBRC = "/etc/directfbrc"

SOCKETFILE = None
CONTROLFILE = None

def getPosition():
	if fileExists("/proc/stb/fb/dst_left"):
		try:
			file = open("/proc/stb/fb/dst_left", "r")
			dst_left = int(file.read().strip(), 16)
			file.close()
			file = open("/proc/stb/fb/dst_width", "r")
			dst_width = int(file.read().strip(), 16)
			file.close()
			file = open("/proc/stb/fb/dst_top", "r")
			dst_top = int(file.read().strip(), 16)
			file.close()
			file = open("/proc/stb/fb/dst_height", "r")
			dst_height = int(file.read().strip(), 16)
			file.close()
		except Exception as Err:
			ERR(Err)
			return None
	return (dst_left, dst_width, dst_top, dst_height)

def setPosition(params):
	if params is None:
		return
	if params[0] + params[1] > 720 or params[2] + params[3] > 576:
		return
	else:
		try:
			file = open("/proc/stb/fb/dst_left", "w")
			file.write('%X' % params[0])
			file.close()
			file = open("/proc/stb/fb/dst_width", "w")
			file.write('%X' % params[1])
			file.close()
			file = open("/proc/stb/fb/dst_top", "w")
			file.write('%X' % params[2])
			file.close()
			file = open("/proc/stb/fb/dst_height", "w")
			file.write('%X' % params[3])
			file.close()
		except Exception as Err:
			ERR(Err)
			return

def osd_lock():
	fbClass.getInstance().lock()
	eRCInput.getInstance().lock()

	if fileExists("/usr/bin/config"):
		try:
			os.system('config -c DirectFB -visible on; config -c 1 -visible off')
		except Exception as Err:
			ERR(Err)

def osd_unlock():
	if fileExists("/usr/bin/config"):
		try:
			os.system('config -c 1 -visible on; config -c DirectFB -visible off')
		except Exception as Err:
			ERR(Err)

	fbClass.getInstance().unlock()
	eRCInput.getInstance().unlock()

def set_bgcolor(val):
	DEBUG("val = %s from %s" % (val, DFBRC))
	os.system('sed \'s/bg-color=[0,f]*/bg-color=%s/\' %s > /tmp/tmprc' % (val, DFBRC))
	os.system('mv /tmp/tmprc %s && rm -f /tmp/tmprc' % DFBRC)

# for debug True
#g_debug = True
g_debug = False

def LogEntry(mode, string):
	if g_debug:
		print(strftime("%x %X", localtime()), "%5s [%12s]" % (mode, "Plugin"), string)
	elif mode != "DEBUG":
		print("[browser] %s" % string)

def DEBUG(string):
	if g_debug:
		LogEntry("DEBUG", string)

def LOG(string):
	if g_debug:
		LogEntry("LOG", string)

def WARN(string):
	if g_debug:
		LogEntry("WARN", string)

def ERR(string):
	if g_debug:
		LogEntry("ERROR", string)

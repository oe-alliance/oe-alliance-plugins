from time import strftime, localtime
from Tools.Directories import fileExists

g_main = None
g_browser = None
g_youtubetv_cfg = None
g_service = None
g_channel_info = None
g_position = None

need_restart = False

APPROOT = "/usr/local/hbb-browser"
APP_RUN = "run.sh"

PLUGINROOT = "/usr/lib/enigma2/python/Plugins/Extensions/HbbTV"
MANUALROOT = "/usr/local/manual"

SOCKETFILE  = None
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
		except Exception, Err:
			ERR(Err)
			return None
	return (dst_left, dst_width, dst_top, dst_height)

def setPosition(params):
	if params is None:
		return
	if params[0] + params[1] > 720 or params[2] + params[3] > 576 :
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
		except Exception, Err:
			ERR(Err)
			return

# for debug True
g_debug = False

def LogEntry(mode, string):
	if g_debug:
		print strftime("%x %X", localtime()), "%5s [%12s]" % (mode, "Plugin"), string
	elif mode != "DEBUG":
		print "[browser]", string

def DEBUG(string):
	LogEntry("DEBUG", string)

def LOG(string):
	LogEntry("LOG", string)

def WARN(string):
	LogEntry("WARN", string)

def ERR(string):
	LogEntry("ERROR", string)

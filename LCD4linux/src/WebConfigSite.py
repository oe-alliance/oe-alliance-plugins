# -*- coding: utf-8 -*-
from __future__ import absolute_import
from glob import glob
from os import stat
from os.path import isfile, join, basename
from six import PY2, ensure_str, ensure_binary
if PY2:
	from HTMLParser import HTMLParser
	_unescape = HTMLParser().unescape
else:
	from html import unescape as _unescape
from time import time
from twisted.web import resource, http
from enigma import eTimer
try:
	from Components.SystemInfo import BoxInfo
	OE43 = BoxInfo.getItem("oe") == "OE-Alliance 4.3"
except ImportError:
	from boxbranding import getOEVersion
	OE43 = getOEVersion() == "OE-Alliance 4.3"
from Components.config import ConfigClock, ConfigSlider, ConfigPassword, ConfigText, ConfigYesNo, ConfigSelection
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CONFIG
from .module import L4Lelement
# from .plugin import *
from .plugin import (
	ConfTimeCheck,
	CrashFile,
	L4LoadNewConfig,
	L4log,
	L4logE,
	LCD4config,
	LCD4linux,
	MJPEG_start,
	MJPEG_stop,
	PICfritz,
	PopText,
	Version,
	WWWpic,
	getBilder,
	getConfigMode,
	getConfigStandby,
	getINFO,
	getMJPEGreader,
	getSaveEventListChanged,
	getScreenActive,
	getTMPL,
	getWWW,
	getisMediaPlayer,
	resetCal,
	resetWetter,
	rmFile,
	rmFiles,
	setConfigMode,
	setConfigStandby,
	setFONT,
	setPopText,
	setSaveEventListChanged,
	setScreenActive,
	setisMediaPlayer,
	xmlClear,
	xmlDelete,
	xmlRead,
	xmlSkin,
	xmlWrite,
)
from . import _

Py = resolveFilename(SCOPE_PLUGINS, "Extensions/LCD4linux/plugin.py")
L1 = []
L2 = []
L3 = []
L4 = []
M1 = ["LCD4linux.OSD", "LCD4linux.Scr", "LCD4linux.Bil", "LCD4linux.Wet", "LCD4linux.Net", "LCD4linux.Pop", "LCD4linux.Fri", "LCD4linux.Fon", "LCD4linux.Mai", "LCD4linux.Cal", "LCD4linux.RBo", "LCD4linux.Www", "LCD4linux.Web", "LCD4linux.MJP", "LCD4linux.xml", "LCD4linux.Tun", "LCD4linux.Key", "LCD4linux.Blu", "LCD4linux.Son", "LCD4linux.YMC"]
M2 = [_("OSD"), _("Screen"), _("Picture"), _("Weather"), _("Netatmo"), _("Popup-Text"), _("FritzCall"), _("Font"), _("Mail"), _("Calendar"), _("Remote Box"), _("WWW Converter"), _("WebIF"), _("MJPEG Stream"), _("Box-Skin-LCD"), _("Tuner"), _("Key"), _("BlueSound"), _("Sonos"), _("MusicCast")]
Mode = "1"
ModeOld = ""
Element = ""
ElementList = []
ExeMode = False
StatusMode = False
L4LElement = L4Lelement()


def _exec(command):
	if PY2:
		exec(command)
	else:
		variable = command.split(" ", 1)[0]
		exec("global %s;%s" % (variable, command))


def ParseCode():
	global L1
	global L2
	global L3
	global L4
	global ElementList
	L1 = []
	L2 = []
	L3 = []
	L4 = []
	i1 = 0
	i2 = 0
	i3 = 0
	i4 = 0
	L4log("WebIF: parsing Code....")
	for line in open(Py, "r").readlines():
		if line.find("self.list1.append") >= 0 or line.find("self.list2.append") >= 0 or line.find("self.list3.append") >= 0 or line.find("self.list4.append") >= 0:
			Z = line.replace("getConfigListEntry(_", ",").replace(")", "").replace("(", "").replace(".append", "").replace("\t", "").replace("\n", "").replace("\r", "").replace("\"", "").split(",")
			if Z[0] == "self.list1":
				if Z[2].strip()[:13] in M1:
					idx = M1.index(Z[2].strip()[:13])
					i1 = idx + 1
				Z.append(i1)
				i1 = 0
				L1.append(Z)
			elif Z[0] == "self.list2":
				if Z[1][:1] != "-":
					i2 += 1
				Z.append(i2)
				L2.append(Z)
			elif Z[0] == "self.list3":
				if Z[1][:1] != "-":
					i3 += 1
				Z.append(i3)
				L3.append(Z)

			elif Z[0] == "self.list4":
				if Z[1][:1] != "-":
					i4 += 1
				Z.append(i4)
				L4.append(Z)


def _l(st):
	st = ensure_str(st, "utf-8", "ignore")
	st = st.replace(" [ok]>", "").encode('ascii', 'xmlcharrefreplace')
	return ensure_str(st)


def AktiveMode(Test, R):
	Aktiv = ""
	Color = ""
	if Mode == Test:
		Aktiv = "checked"
		Color = "style=\"color: #FFCC00\""
	return Aktiv, Color, R


def AktiveElement(Test):
	Aktiv = ""
	Color = ""
	if Element == Test:
		Aktiv = "checked"
		Color = "style=\"color: #FFCC00\""
	return Aktiv, Color


def AktiveScreen(Test):
	return "; background-color:lime" if getScreenActive() == Test else "; background-color:ButtonFace"

########################################################


class LCD4linuxConfigweb(resource.Resource):
	title = "L4L Webinterface"
	isLeaf = True
	RestartGUI = False

	def __init__(self):
		self.StatusTimer = eTimer()
		self.StatusTimer.callback.append(self.resetWeb)
		self.CurrentMode = ("-", "-")

	def resetWeb(self):
		L4log("Reset Web")
		self.StatusTimer.stop()
		setConfigMode(False)
		setisMediaPlayer(self.CurrentMode[1])
		setConfigStandby(self.CurrentMode[0])
		self.CurrentMode = ("-", "-")

	def restartTimer(self):
		L4log("Restart Timer")
		self.StatusTimer.stop()
		self.StatusTimer.startLongTimer(60)

	def render_GET(self, request):
		L4logE("GET received", request.args)
		return self.action(request)

	def render_POST(self, request):
		L4logE("POST received", request.args)
		return self.action(request)

	def action(self, req):
		global Mode
		global ModeOld
		global Element
		global ElementList
		global ExeMode
		global StatusMode
		IP = ensure_str(req.getClientIP())
		if OE43:
			IP = IP.split(":")[-1]
		L4logE("IP1:", IP)
		if IP is None:
			L4logE("IP2:", req.client.host)
			IP = None if IP.find(".") == -1 else req.client.host.split(":")[-1]
		else:
			IP = IP.split(":")[-1]
		if IP is None:
			Block = False
		else:
			Block = True
			WL = LCD4linux.WebIfAllow.value
			for x in WL.split():
				if IP.startswith(x):
					Block = False
					break
			if "*" in WL:
				Block = False
			WL = LCD4linux.WebIfDeny.value
			for x in WL.split():
				if IP.startswith(x):
					Block = True
					break
		if Block is True:
			html = "<html>"
			html += "<head>\n"
			html += "<meta http-equiv=\"Content-Language\" content=\"de\">\n"
			html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\">\n"
			html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
			html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
			html += "<meta http-equiv=\"expires\" content=\"0\">\n"
			html += "</head>"
			html += "Config-WebIF Access Deny ( IP: %s )<br>\n" % IP
			html += "Please check Setting in Global > %s\n" % _l(_("WebIF IP Allow"))
			html += "Default is: 127. 192.168. 172. 10.\n"
			html += "</body>\n"
			html += "</html>\n"
			return ensure_binary(html)
		if len(L1) == 0:
			ParseCode()
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')
		command = req.args.get(b"cmd", None)
		_command = ensure_str(command[0]) if command is not None else ""
		ex = req.args.get(b"ex", None)
		_ex = ensure_str(ex[0]) if ex is not None else req.args.get(b"ex", None)
		mo = req.args.get(b"Mode", None)
		el = req.args.get(b"Element", None)
		self.restartTimer()
		L4log("Command received %s" % (command), ex)
		if self.CurrentMode == ("-", "-"):
			self.CurrentMode = (getConfigStandby(), getisMediaPlayer())
		if mo is not None:
			Mode = ensure_str(mo[0])
			setConfigMode(True)
			if Mode in ["1", "2"]:
				setisMediaPlayer("")
				setConfigStandby(False)
			elif Mode == "3":
				setisMediaPlayer("config")
				setConfigStandby(False)
			elif Mode == "4":
				setisMediaPlayer("")
				setConfigStandby(True)
			elif Mode == "5":
				self.resetWeb()
			getBilder()
		html = ""
		if el is not None:
			Element = ensure_str(el[0])
		if req.args.get(b"save.y", None) is not None:
			L4log("WebIF: save Config-File")
			LCD4linux.save()
			LCD4linux.saveToFile(LCD4config)
			ConfTimeCheck()
		if req.args.get(b"download.y", None) is not None:
			L4log("WebIF: download Config")
			req.setResponseCode(http.OK)
			lcd4config = resolveFilename(SCOPE_CONFIG) + "lcd4config"
			req.setHeader('Content-type', 'text/plain')
			req.setHeader('Content-Disposition', 'attachment;filename=lcd4config')
			req.setHeader('Content-Length', str(stat(lcd4config).st_size))
			req.setHeader('charset', 'UTF-8')
			f = open(lcd4config, "r")
			html = f.read()
			f.close()
			return ensure_binary(html)
		if req.args.get(b"upload.y", None) is not None:
			L4log("WebIF: upload Config")
			lcd4config = "/tmp/test"
			data = req.args[b"uploadName"][0]
			if len(data) > 0 and data.startswith(b"config."):
				f = open(lcd4config, "wb")
				f.write(data)
				f.close()
				if isfile(lcd4config):
					L4LoadNewConfig(lcd4config)
			else:
				L4log("WebIF: Error upload")
				html += "<script language=\"JavaScript\">\n"
				html += "alert(\"%s\")\n" % _("No or wrong File selected, try a correct File first !")
				html += "</script>\n"
		if req.args.get(b"logdel.y", None) is not None:
			L4log("WebIF: delete Logfile")
			rmFile("/tmp/L4log.txt")
		if req.args.get(b"logdownload.y", None) is not None:
			L4log("WebIF: download Logfile")
			lcd4config = "/tmp/L4log.txt"
			if isfile(lcd4config):
				req.setResponseCode(http.OK)
				req.setHeader('Content-type', 'text/plain')
				req.setHeader('Content-Disposition', 'attachment;filename=l4log.txt')
				req.setHeader('Content-Length', str(stat(lcd4config).st_size))
				req.setHeader('charset', 'UTF-8')
				f = open(lcd4config, "r")
				html = f.read()
				f.close()
				return ensure_binary(html)
		if command is None:
			L4logE("no command")
		elif _command == "exec" and ex is not None:
			L4logE("exec: %s" % _ex)
			exec(str(_ex))  # FIXME PY3
		elif _command == "enable":
			ExeMode = True
		elif _command == "status":
			StatusMode = True
		elif _command == "pop":
			V = _l(req.args.get(b"PopText", "")[0])
			try:
				V = _unescape(V)
			except Exception as e:
				L4log("WebIF Error: Parse Text", e)
			setPopText(V)
			L4LElement.setRefresh()
		elif _command == "popclear":
			setPopText("")
		elif _command.startswith("Screen"):
			setScreenActive(_command[-1])
			L4LElement.setRefresh()
		elif _command == "crashdel":
			rmFile(CrashFile)
		elif _command == "add" and ex is not None:
			L4LElement.web(_ex)
		elif _command == "delete" and ex is not None:
			L4LElement.delete(_ex)
		elif _command == "refresh":
			L4LElement.setRefresh()
		elif _command == "hold":
			setScreenActive("0")
			setSaveEventListChanged(not getSaveEventListChanged())
		elif _command == "screen" and ex is not None:
			exs = _ex.split(",")
			if len(exs) == 1:
				L4LElement.setScreen(exs[0])
			elif len(exs) == 2:
				L4LElement.setScreen(exs[0], exs[1])
			elif len(exs) == 3:
				L4LElement.setScreen(exs[0], exs[1], exs[2] == "True")
		elif _command == "brightness" and ex is not None:
			exs = _ex.split(",")
			if len(exs) == 1:
				L4LElement.setBrightness(exs[0])
			elif len(exs) == 2:
				L4LElement.setBrightness(exs[0], exs[1] == "True")
		elif _command == "getbrightness" and ex is not None:
			if int(_ex) < 1 or int(_ex) > 3:
				return "0"
			else:
				return str(L4LElement.getBrightness(int(_ex)))
		elif _command == "getmjpeg" and ex is not None:
			if int(_ex) < 1 or int(_ex) > 3:
				return "0"
			else:
				return str(getMJPEGreader(_ex))
		elif _command == "getexec" and ex is not None:
			L4logE("getexec", _ex)
			_exec("getexec = %s" % _ex)  # FIXME PY3
			return str(_ex)
		elif _command == "copyMP":
			for a in req.args.keys():
				_a = ensure_str(a)
				if ".Standby" in _a:
					b = _a.replace(".Standby", ".MP")
					if (" " + b) in list(zip(*L3))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
				elif "." in _a:
					b = _a.replace(".", ".MP")
					if (" " + b) in list(zip(*L3))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
		elif _command == "copyIdle":
			for a in req.args.keys():
				_a = ensure_str(a)
				if ".MP" in _a:
					b = _a.replace(".MP", ".Standby")
					if (" " + b) in list(zip(*L4))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
				elif "." in _a:
					b = _a.replace(".", ".Standby")
					if (" " + b) in list(zip(*L4))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
		elif _command == "copyOn":
			for a in req.args.keys():
				_a = ensure_str(a)
				if ".MP" in _a:
					b = _a.replace(".MP", ".")
					if (" " + b) in list(zip(*L2))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
				elif ".Standby" in _a:
					b = _a.replace(".Standby", ".")
					if (" " + b) in list(zip(*L2))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value

#####################
# Konfig schreiben
#####################
		elif _command == "config":
			Cfritz = False
			Cwetter = False
			Cpicon = False
			Ccal = False
			Cwww = False
			for a in req.args.keys():
				_a = ensure_str(a)
				if _a.find(".") > 0:
					val = req.args.get(a, "")[0]
					val = ensure_str(val)
					# ConfigSelection
					ConfObj = eval(_a)
					if isinstance(ConfObj, ConfigSelection):
						ConfObj.value = val
					else:
						# ConfigYesNo
						if isinstance(ConfObj, ConfigYesNo):
							val = req.args.get(a, "")
							ConfObj.value = True if len(val) == 2 else False
						else:
							# ConfigText
							if isinstance(ConfObj, ConfigText):
								V = _l(val)
								try:
									V = _unescape(V)
								except Exception as e:
									L4log("WebIF Error: Parse Text", e)
								ConfObj.value = V
							else:
								# ConfigSlider
								if isinstance(ConfObj, ConfigSlider):
									if val.isdigit():
										ConfObj.value = val
								else:
									# ConfigClock
									if isinstance(ConfObj, ConfigClock):
										t = val.split(":")
										if len(t) == 2:
											if t[0].isdigit() and t[1].isdigit():
												ConfObj.value = [int(t[0]), int(t[1])]
					if ConfObj.isChanged():
						ConfObj.save()
						L4log("Changed", a)
						if _a.find("Fritz") > 0:
							Cfritz = True
						elif _a.find("Wetter") > 0:
							Cwetter = True
						elif _a.find("Picon") > 0:
							Cpicon = True
						elif _a.find(".Cal") > 0 or _a.find(".MPCal") > 0 or _a.find(".StandbyCal") > 0:
							Ccal = True
						elif _a.find(".xmlType") > 0:
							if _a.find(".xmlLCDType") > 0:
								xmlRead()
								if xmlDelete(1) or xmlDelete(2) or xmlDelete(3):
									L4log("removed old Skindata")
									xmlWrite()
							if xmlSkin():
								xmlWrite()
								LCD4linuxConfigweb.RestartGUI = True
							xmlClear()
						elif _a.find(".MJPEG") > 0:
							MJPEG_stop("")
							MJPEG_start()
						elif _a.find(".Font") > 0:
							setFONT(LCD4linux.Font.value)
						if _a.find("WetterCity") > 0:
							LCD4linux.WetterCoords.value = "0,0"
							LCD4linux.WetterCoords.save()
							LCD4linux.saveToFile(LCD4config)
							resetWetter(0)
						if _a.find("Wetter2City") > 0:
							LCD4linux.Wetter2Coords.value = "0,0"
							LCD4linux.Wetter2Coords.save()
							LCD4linux.saveToFile(LCD4config)
							resetWetter(1)
						if _a.find("ScreenActive") > 0:
							setScreenActive(LCD4linux.ScreenActive.value)
						if _a.find("BildFile") > 0:
							getBilder()
						if _a.find("WWW1") > 0:
							if _a.find("WWW1url") > 0 or isfile(WWWpic % "1") is False:
								Cwww = True
							else:
								rmFile(WWWpic % "1p")
			if Cfritz:
				rmFile(PICfritz)
			if Cwetter:
				# resetWetter(None)  # action after changing weather parameters
				pass
			if Cpicon:
				if len(LCD4linux.PiconCache.value) > 2:
					rmFiles(join(LCD4linux.PiconCache.value, "*.png"))
				if len(LCD4linux.Picon2Cache.value) > 2:
					rmFiles(join(LCD4linux.Picon2Cache.value, "*.png"))
			if Ccal:
				resetCal()
			if Cwww:
				getWWW()
			L4LElement.setRefresh()
#####################
# Anzeige
#####################
		html += "<html>"
		html += "<head>\n"
		html += "<meta http-equiv=\"Content-Language\" content=\"de\">\n"
		html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n"
		html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"expires\" content=\"0\">\n"
		html += "<link rel=\"shortcut icon\" href=\"/lcd4linux/data/favicon.png\">"
		if isfile(CrashFile):
			html += "<script language=\"JavaScript\">\n"
			html += "function fensterchen() {\n"
			html += "fens1=window.open(\"\", \"Crashlog\",\"width=500,height=300,resizable=yes\");\n"
			for line in open(CrashFile, "r").readlines():
				html += "fens1.document.write('%s');\n" % line.replace("\n", "<br>").replace("'", "\\'")
			html += "} </script>\n"
		html += "<style type=\"text/css\">\n"
		html += ".style1 {\n"
		html += "vertical-align: middle; font-size:8px; }\n"
		html += "</style>\n"
		if L4LElement.getRefresh() is True:
			glob
			GI = getINFO().split()
			GR = min(int(float(GI[6])) + 1, 6) if len(GI) > 6 else 6
			html += "<meta http-equiv=\"refresh\" content=\"%d\">\n" % GR
		html += "<title>LCD4linux</title>\n"
		html += "</head>"
		html += "<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n"
		html += "<form method=\"POST\" action=\"--WEBBOT-SELF--\">\n"
		html += "</form>\n"
		html += "<table border=\"1\" rules=\"groups\" width=\"100%\" bordercolorlight=\"#000000\" bordercolordark=\"#000000\" cellspacing=\"0\">"
		html += "<tr><td bgcolor=\"#000000\" width=\"220\">\n"
		html += "<p align=\"center\"><img title=\"\" border=\"0\" src=\"/lcd4linux/data/WEBdreambox.png\" width=\"181\" height=\"10\">\n"
		CCM = "#FFFFFF" if getConfigMode() is False else "#FFCC00"
		html += "<font color=\"%s\"><b>LCD4linux Config</b></font><br />%s\n" % (CCM, (Version if L4LElement.getVersion() is True else Version + "") + " (%s: Py" + ("2" if PY2 else "3") + ")") % _l(_("Mode"))
		if IP is None:
			html += "<br><span style=\"font-size:7pt;color: #FF0000\">%s!</span>" % _l(_("IP seurity not supported by Box"))
		html += "</p></td><td bgcolor=\"#000000\">\n"
		html += "<p align=\"left\">"
		d = glob("%sdpf.*" % getTMPL())
		if len(d) > 0:
			html += "<a href=\"/lcd4linux\"><img style=\"color:#FFCC00\" title=\"LCD 1\" src=\"/lcd4linux/%s?%d\" border=\"1\" height=\"80\" id=\"reloader1\" onload=\"setTimeout('document.getElementById(\\'reloader1\\').src=\\'/lcd4linux/%s?\\'+new Date().getTime()', 5000)\" ></a>" % (basename(d[0]), time(), basename(d[0]))
		d = glob("%sdpf2.*" % getTMPL())
		if len(d) > 0:
			html += "<a href=\"/lcd4linux?file=%s\"><img style=\"color:#FFCC00\" title=\"LCD 2\" src=\"/lcd4linux/%s?%d\" border=\"1\" height=\"80\" id=\"reloader2\" onload=\"setTimeout('document.getElementById(\\'reloader2\\').src=\\'/lcd4linux/%s?\\'+new Date().getTime()', 5000)\" ></a>" % (basename(d[0]), basename(d[0]), time(), basename(d[0]))
		d = glob("%sdpf3.*" % getTMPL())
		if len(d) > 0:
			html += "<a href=\"/lcd4linux?file=%s\"><img style=\"color:#FFCC00\" title=\"LCD 3\" src=\"/lcd4linux/%s?%d\" border=\"1\" height=\"80\" id=\"reloader3\" onload=\"setTimeout('document.getElementById(\\'reloader3\\').src=\\'/lcd4linux/%s?\\'+new Date().getTime()', 5000)\" ></a>" % (basename(d[0]), basename(d[0]), time(), basename(d[0]))
		html += "</p></td>\n"
		if isfile(CrashFile):
			html += "<td valign=\"top\" align=\"left\"  bgcolor=\"#000000\">\n"
			html += "<form method=\"post\"><font color=\"#FFFF00\">%s</font><br>\n" % _l(_("Crashlog"))
			html += "<input type=\"hidden\" name=\"cmd\" value=\"\">\n"
			html += "<input type=\"button\" value=\"%s\" style=\"font-size:8pt;background-color:yellow;\" onClick=\"fensterchen()\">\n" % _l(_("Show"))
			html += "<input type=\"button\" value=\"%s\" style=\"font-size:8pt;background-color:yellow;\"   onclick=\"this.form.cmd.value = 'crashdel'; this.form.submit();\">\n" % _l(_("Delete"))
			html += "</form></td>\n"
		html += "<td valign=\"top\" align=\"right\"  bgcolor=\"#000000\">\n"
		html += "<form method=\"post\" enctype=\"multipart/form-data\">\n"
		html += "<input type=\"file\" name=\"uploadName\" title=\"%s\" class=\"style1\" >\n" % _l(_("Filename"))
		html += "<input type=\"image\" name=\"upload\" value=\"klick\" src=\"/lcd4linux/data/WEBupload.png\" height=\"25\" title=\"%s\" class=\"style1\"  >\n" % _l(_("Restore Config"))
		html += "<input type=\"image\" name=\"download\" value=\"klick\" src=\"/lcd4linux/data/WEBdownload.png\" height=\"25\" title=\"%s\" class=\"style1\" >\n" % _l(_("Backup Config"))
		if isfile("/tmp/L4log.txt"):
			html += "<input type=\"image\" name=\"logdel\" value=\"klick\" src=\"/lcd4linux/data/WEBlogdel.png\" height=\"25\" title=\"%s\" class=\"style1\"  >\n" % _l(_("Delete Logfile"))
			html += "<input type=\"image\" name=\"logdownload\" value=\"klick\" src=\"/lcd4linux/data/WEBlogshow.png\" height=\"25\" title=\"%s\" class=\"style1\" >\n" % _l(_("Download Logfile"))
		html += "<input type=\"image\" name=\"save\" value=\"klick\" src=\"/lcd4linux/data/WEBsave.png\" height=\"40\" title=\"%s\" class=\"style1\" >\n" % _l(_("Save Config"))
		html += "</form>\n"
		html += "<form method=\"post\"><font color=\"#FFFFFF\">%s</font>\n" % _l(_("Screen"))
		html += "<input type=\"hidden\" name=\"cmd\" value=\"\">\n"
		for i in range(1, 10):
			html += "<input type=\"button\" value=\"%d\" style=\"width:15px; text-align:center; font-size:8pt%s\" onclick=\"this.form.cmd.value = 'Screen%d'; this.form.submit();\">\n" % (i, AktiveScreen(str(i)), i)
		Aktiv = "checked" if getSaveEventListChanged() else ""
		html += "<input type=\"hidden\" name=\"hold\" value=\"%s\">" % ("unchecked")
		html += "<input type=\"checkbox\" title=\"%s\" name=\"hold\" value=\"%s\" onclick=\"this.form.cmd.value = 'hold'; this.form.submit();\" %s>" % (_l(_("stop Screencycle")), "checked", Aktiv)
		html += "</form>\n"
		html += "</td></tr></table>\n"
		html += "<form method=\"get\">"
		html += "<fieldset style=\"width:auto\" name=\"Mode1\">"
		html += "<legend style=\"color: #FFCC00\">%s&nbsp;</legend>\n" % _l(_("Mode"))
		html += "<input id=\"r1\" name=\"Mode\" type=\"radio\" value=\"1\" %s onclick=\"this.form.submit();\"><label %s for=\"r1\">%s&nbsp;&nbsp;</label>\n" % (AktiveMode("1", _l(_("Global"))))
		html += "<input id=\"r2\" name=\"Mode\" type=\"radio\" value=\"2\" %s onclick=\"this.form.submit();\"><label %s for=\"r2\">%s&nbsp;&nbsp;</label>\n" % (AktiveMode("2", _l(_("On"))))
		html += "<input id=\"r3\" name=\"Mode\" type=\"radio\" value=\"3\" %s onclick=\"this.form.submit();\"><label %s for=\"r3\">%s&nbsp;&nbsp;</label>\n" % (AktiveMode("3", _l(_("Media"))))
		html += "<input id=\"r4\" name=\"Mode\" type=\"radio\" value=\"4\" %s onclick=\"this.form.submit();\"><label %s for=\"r4\">%s&nbsp;&nbsp;</label>\n" % (AktiveMode("4", _l(_("Idle"))))
		if LCD4linuxConfigweb.RestartGUI is True:
			html += "<span style=\"color: #FF0000;\"><strong>%s</strong></span>" % _l(_("GUI Restart is required"))
		if str(LCD4linux.Popup.value) != "0":
			html += "<input id=\"r5\" name=\"Mode\" type=\"radio\" value=\"5\" %s onclick=\"this.form.submit();\"><label %s for=\"r5\">%s&nbsp;&nbsp;</label>\n" % (AktiveMode("5", "Popup-Text"))
		html += "</fieldset></form>\n"
		if Mode != "5":
			if Mode == "1":
				L = L1
			elif Mode == "2":
				L = L2
			elif Mode == "3":
				L = L3
			elif Mode == "4":
				L = L4
			else:
				Mode = "1"
				L = L1
				Element = "other"
			if str(LCD4linux.WebIfDesign.value) == "2":
				html += "<table border=\"0\"width=\"100%\" cellspacing=\"1\">"
				html += "<tr><td valign=\"top\" width=\"250\">"
			html += "<form method=\"get\">"
			html += "<fieldset style=\"width:auto\" name=\"Mode2\">"
			html += "<legend style=\"color: #FFCC00\">%s&nbsp;</legend>\n" % _l(_("Element"))
			i = 0
			ElementList = []
			ElementText = ""
			for LL in L:
				Conf = LL[2].strip()
				if Mode == "1":
					Conf = Conf[:13]
				if ((LL[1][:1] != "-" and Mode != "1") or (Mode == "1" and Conf not in ElementList)) and LL[3] != 0:
					if Element == "" or ModeOld != Mode:
						Element = "other"
						ModeOld = Mode
					ElementList.append(Conf)
					i += 1
					Ea, Ec = AktiveElement(Conf)
					if Mode != "1":
						ConfObj = eval(Conf)
						Curr = ConfObj.value
						L4log("Curr = %s.value" % Conf, Curr)
						if Curr != "0":
							Ec = "style=\"font-weight:bold;color:#CCFFBB\"" if Ec == "" else Ec.replace("=\"", "=\"font-weight:bold;")
					if Ea == "checked":
						ElementText = (_l(_(LL[1])) if Mode != "1" else _l(M2[LL[3] - 1]))
					html += "<input id=\"e%d\" name=\"Element\" type=\"radio\" value=\"%s\" %s onclick=\"this.form.submit();\"><label %s for=\"e%d\">%s&nbsp;&nbsp;</label>\n" % (i, Conf, Ea, Ec, i, (_l(_(LL[1])) if Mode != "1" else _l(M2[LL[3] - 1])))
					if str(LCD4linux.WebIfDesign.value) == "2":
						html += "<br>"
			Ea, Ec = AktiveElement("other")
			if Ea == "checked":
				ElementText = _l(_("other"))
			html += "<input id=\"e%d\" name=\"Element\" type=\"radio\" value=\"%s\" %s onclick=\"this.form.submit();\"><label %s for=\"e%d\">%s&nbsp;&nbsp;</label>\n" % (0, "other", Ea, Ec, 0, _l(_("other")))
			html += "</fieldset></form>\n"
			if str(LCD4linux.WebIfDesign.value) == "2":
				html += "<br></td><td valign=\"top\">"
			html += "<form name=\"Eingabe\" method=\"POST\">\n"
			if str(LCD4linux.WebIfDesign.value) == "2":
				html += "<fieldset style=\"width:auto\" name=\"Mode3\"><legend style=\"color: #FFCC00\">%s&nbsp;</legend>" % ElementText
			html += "<table border=\"1\" rules=\"groups\" width=\"100%\">"
			AktCode = 0
			isOn = False
			isMP = False
			isSb = False
			for LL in L:
				Conf = LL[2].strip()
				ConfObj = eval(Conf)
				if (Conf.startswith(Element) and (LL[3] == AktCode or AktCode == 0)) or (Element == "other" and LL[3] == 0):
					if Mode in "2":
						if "." in Conf:
							b = Conf.replace(".", ".MP")
							if (" " + b) in list(zip(*L3))[2]:
								isMP = True
							b = Conf.replace(".", ".Standby")
							if (" " + b) in list(zip(*L4))[2]:
								isSb = True
					elif Mode in "3":
						if ".MP" in Conf:
							b = Conf.replace(".MP", ".")
							if (" " + b) in list(zip(*L2))[2]:
								isOn = True
							b = Conf.replace(".MP", ".Standby")
							if (" " + b) in list(zip(*L4))[2]:
								isSb = True
					elif Mode in "4":
						if ".Standby" in Conf:
							b = Conf.replace(".Standby", ".")
							if (" " + b) in list(zip(*L2))[2]:
								isOn = True
							b = Conf.replace(".Standby", ".MP")
							if (" " + b) in list(zip(*L3))[2]:
								isMP = True
					if AktCode == 0:
						AktCode = LL[3]
					Curr = ConfObj.value
					# ConfigSelection
					html += "<tr>\n"
					if isinstance(ConfObj, ConfigSelection):
						html += "<td width=\"300\">%s</td><td>\n" % _l(_(LL[1]))
						html += "<select name=\"%s\" size=\"1\">\n" % Conf
						Len = len(ConfObj.description)
						for i in list(range(Len)):
							Choice = ConfObj.choices[i]
							Wert = ConfObj.description[Choice]
							Aktiv = " selected" if str(Choice) == str(Curr) else ""
							html += "<option value=\"%s\" %s>%s</option>\n" % (Choice, Aktiv, _l(Wert))
						html += "</select>\n"
						html += "</td>\n"
					else:
						# ConfigYesNo
						if isinstance(ConfObj, ConfigYesNo):
							html += "<td width=\"300\">%s</td><td>\n" % _l(_(LL[1]))
							Aktiv = "checked" if Curr else ""
							html += "<input type=\"hidden\" name=\"%s\" value=\"%s\">" % (Conf, "unchecked")
							html += "<input type=\"checkbox\" name=\"%s\" value=\"%s\" %s>" % (Conf, "checked", Aktiv)
							html += "</td>\n"
						else:
							# ConfigText
							if isinstance(ConfObj, ConfigText):
								html += "<td width=\"300\">%s</td><td>\n" % _l(_(LL[1]))
								html += "<input type=\"password\" name=\"%s\" size=\"60\" value=\"%s\">" % (Conf, _l(Curr)) if isinstance(ConfObj, ConfigPassword) else "<input type=\"text\" name=\"%s\" size=\"60\" value=\"%s\">" % (Conf, _l(Curr))
								html += "</td>\n"
							else:
								# ConfigSlider
								if isinstance(ConfObj, ConfigSlider):
									Min = ConfObj.min
									Max = ConfObj.max
									html += "<td width=\"300\">%s (%d - %d)</td><td>\n" % (_l(_(LL[1])), Min, Max)
									html += "<input type=\"text\" name=\"%s\" size=\"5\" value=\"%s\">" % (Conf, Curr)
									html += "</td>\n"
								else:
									# ConfigClock
									if isinstance(ConfObj, ConfigClock):
										html += "<td width=\"300\">%s</td><td>\n" % _l(_(LL[1]))
										html += "<input type=\"text\" name=\"%s\" size=\"6\" value=\"%02d:%02d\">" % (Conf, Curr[0], Curr[1])
										html += "</td>\n"
			html += "</tr></table>\n"
			html += "<input type=\"hidden\" name=\"cmd\" value=\"config\">\n"
			html += "<input type=\"submit\" style=\"background-color: #FFCC00\" value=\"%s\">\n" % _l(_("set Settings"))
			if Element != "other":
				if Mode in ["3", "4"] and isOn:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"%s\" onclick=\"this.form.cmd.value = 'copyOn'; this.form.submit(); \">\n" % _l(_("copy to On"))
				if Mode in ["2", "4"] and isMP:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"%s\" onclick=\"this.form.cmd.value = 'copyMP'; this.form.submit(); \">\n" % _l(_("copy to Media"))
				if Mode in ["2", "3"] and isSb:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"%s\" onclick=\"this.form.cmd.value = 'copyIdle'; this.form.submit(); \">\n" % _l(_("copy to Idle"))
			html += "</fieldset></td></tr></table>" if str(LCD4linux.WebIfDesign.value) == "2" else "</form>\n"
		elif Mode == "5":
			html += "<form method=\"POST\">\n"
			html += "<fieldset style=\"width:auto\" name=\"Mode2\">\n"
			html += "<textarea name=\"PopText\" style=\"height: 120px; width: 416px\">%s</textarea>" % _l(PopText[1])
			html += "<input type=\"hidden\" name=\"cmd\" value=\"pop\">\n"
			html += "<input type=\"submit\" style=\"background-color: #FFCC00\" value=\"%s\">\n" % _l(_("set Settings"))
			html += "</fieldset></form>\n"

		if ExeMode is True:
			html += "<br />\n"
			html += "<form method=\"GET\">\n"
			html += "<input type=\"hidden\" name=\"cmd\" value=\"exec\">\n"
			html += "<input style=\"width: 400px\" type=\"text\" name=\"ex\">\n"
			html += "<input type=\"submit\" value=\"%s\">\n" % _l(_("Exec"))
			html += "</form>\n"
		if StatusMode is True:
			html += "<br />\n"
			html += "Screen: %s<br />\n" % str(getScreenActive(True))
			html += "Hold/HoldKey: %s/%s<br />\n" % (str(getSaveEventListChanged()), str(L4LElement.getHoldKey()))
			html += "Brightness org/set %s/%s<br />\n" % (str(L4LElement.getBrightness()), str(L4LElement.getBrightness(0, False)))

		html += "<hr><span style=\"font-size:8pt\">%s (%s)</span>" % (getINFO(), IP)
		html += "<BR><a style=\"font-size:10pt; color:#FFCC00;\" href=\"http://www.i-have-a-dreambox.com/wbb2/thread.php?postid=1634882\">Support & FAQ & Info & Donation</a>"
		if len(L4LElement.get()) > 0:
			html += "<script language=\"JavaScript\">\n"
			html += "function Efensterchen() {\n"
			html += "fens1=window.open(\"\", \"Externals\",\"width=500,height=300,resizable=yes\");\n"
			L4Lkeys = sorted(L4LElement.get().keys())
			for CUR in L4Lkeys:
				html += "fens1.document.write('%s %s<BR>');\n" % (CUR, str(L4LElement.get(CUR)).replace("\n", "<br>").replace("'", "\\'"))
			html += "} </script>\n"
			html += "<form method=\"post\"><br>\n"
			html += "<input type=\"button\" value=\"%s\" style=\"font-size:8pt;\" onClick=\"Efensterchen()\">\n" % _l(_("Show Externals"))
			html += "</form></td>\n"
		html += "</body>\n"
		html += "</html>\n"
		return ensure_binary(html)

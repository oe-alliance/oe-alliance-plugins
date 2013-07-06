# -*- coding: utf-8 -*-
# print " LCD4linux.StandbyBildLCD" in zip(*L4)[2]
from twisted.web import resource, http
from plugin import *
from __init__ import _
from Components.config import configfile, config
from enigma import eTimer

import os
import datetime
import glob
import time

Py = "/usr/lib/enigma2/python/Plugins/Extensions/LCD4linux/plugin.pyo"

L1 = []
L2 = []
L3 = []
L4 = []
M1 = ["LCD4linux.OSD","LCD4linux.Scr","LCD4linux.Bil","LCD4linux.Rec","LCD4linux.Wet","LCD4linux.Pop","LCD4linux.Fri","LCD4linux.Fon","LCD4linux.Mai","LCD4linux.Cal","LCD4linux.xml"]
M2 = [_("OSD"),_("Screen"),_("Picture"),_("Recording"),_("Weather"),_("Popup-Text"),_("FritzCall"),_("Font"),_("Mail"),_("Calendar"),_("Box-Skin-LCD")]

Mode = "1"
ModeOld = ""
Element = ""
ElementList = []
ExeMode = False

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
	for line in open(Py,"r").readlines():
#		print line
		if line.find("self.list1.append") >= 0 or line.find("self.list2.append") >= 0 or line.find("self.list3.append") >= 0 or line.find("self.list4.append") >= 0:
			Z = line.replace("getConfigListEntry(_",",").replace(")","").replace("(","").replace(".append","").replace("\t","").replace("\n","").replace("\"","").split(",")
			if Z[0]=="self.list1":
				if Z[2].strip()[:13] in M1:
					idx = M1.index(Z[2].strip()[:13])
					i1 = idx+1
				Z.append(i1)
				i1 = 0
				L1.append(Z)
			elif Z[0]=="self.list2":
				if Z[1][:1] != "-":
					i2+=1
				Z.append(i2)
				L2.append(Z)
			elif Z[0]=="self.list3":
				if Z[1][:1] != "-":
					i3+=1
				Z.append(i3)
				L3.append(Z)
			elif Z[0]=="self.list4":
				if Z[1][:1] != "-":
					i4+=1
				Z.append(i4)
				L4.append(Z)

def _l(st):
	return codecs.encode(st.decode("utf-8","ignore").replace(" [ok]>",""),"latin","ignore")
def _l2(st):
	return st.decode("latin").encode("utf-8")

def AktiveMode(Test):
	Aktiv = ""
	Color = ""
	if Mode == Test:
		Aktiv = "checked"
		Color = "style=\"color: #FFCC00\""
	return Aktiv,Color

def AktiveElement(Test):
	Aktiv = ""
	Color = ""
	if Element == Test:
		Aktiv = "checked"
		Color = "style=\"color: #FFCC00\""
	return Aktiv,Color

def AktiveScreen(Test):
	Color = ""
	if getScreenActive() == Test:
		Color = "; background-color:lime"
	else:
		Color = "; background-color:ButtonFace"
	return Color

########################################################
class LCD4linuxConfigweb(resource.Resource):
	title = "L4L Webinterface"
	isLeaf = True
	RestartGUI = False
	def __init__(self):
		self.StatusTimer = eTimer()
		self.StatusTimer.callback.append(self.resetWeb)
		self.CurrentMode = ("-","-")

	def resetWeb(self):
		L4log("Reset Web")
		self.StatusTimer.stop()
		setConfigMode(False)
		setisMediaPlayer(self.CurrentMode[1])
		setConfigStandby(self.CurrentMode[0])
		self.CurrentMode = ("-","-")

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
		if len(L1) == 0:
			ParseCode()

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		command = req.args.get("cmd",None)
		ex = req.args.get("ex",None)
		mo = req.args.get("Mode",None)
		el = req.args.get("Element",None)
		sa = req.args.get("save.y",None)
		self.restartTimer()
		L4log("Command received %s" % (command))
#		print "[L4L EX]-", ex,"-"
		if self.CurrentMode == ("-","-"):
			self.CurrentMode = (getConfigStandby(),getisMediaPlayer())
		if mo is not None:
			Mode = mo[0]
			setConfigMode(True)
			if Mode in ["1","2"]:
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
		if el is not None:
			Element = el[0]
		if sa is not None:
			LCD4linux.save()
			LCD4linux.saveToFile(LCD4config)
		if command is None:
			L4logE("no command")
		elif command[0] == "exec" and ex is not None:
			L4logE("exec",ex[0])
			exec(ex[0])
		elif command[0] == "enable":
			ExeMode = True
		elif command[0] == "pop":
			setPopText(req.args.get("PopText",[""])[0])
			open(Push,"w").write("")
		elif command[0] == "popclear":
			setPopText("")
		elif command[0].startswith("Screen"):
			setScreenActive(command[0][-1])
			open(Push,"w").write("")
		elif command[0] == "crashdel":
			rmFile(CrashFile)
		elif command[0] == "copyMP":
			for a in req.args.keys():
				if ".Standby" in a:
					b = a.replace(".Standby",".MP")
					if (" "+b) in zip(*L3)[2]:
						print a,b
						exec("%s.value = %s.value" % (b,a))
				elif "." in a:
					b = a.replace(".",".MP")
					if (" "+b) in zip(*L3)[2]:
						print a,b
						exec("%s.value = %s.value" % (b,a))
		elif command[0] == "copyIdle":
			for a in req.args.keys():
				if ".MP" in a:
					b = a.replace(".MP",".Standby")
					if (" "+b) in zip(*L4)[2]:
						print a,b
						exec("%s.value = %s.value" % (b,a))
				elif "." in a:
					b = a.replace(".",".Standby")
					if (" "+b) in zip(*L4)[2]:
						print a,b
						exec("%s.value = %s.value" % (b,a))
		elif command[0] == "copyOn":
			for a in req.args.keys():
				if ".MP" in a:
					b = a.replace(".MP",".")
					if (" "+b) in zip(*L2)[2]:
						print a,b
				elif ".Standby" in a:
					b = a.replace(".Standby",".")
					if (" "+b) in zip(*L2)[2]:
						print a,b
#####################
# Konfig schreiben
#####################
		elif command[0] == "config":
			Cfritz = False
			Cwetter = False
			Cpicon = False
			Ccal = False
			Cwww = False
			for a in req.args.keys():
				if a.find(".") > 0:
#ConfigSelection
					exec("Typ = isinstance(%s,ConfigSelection)" % a)
					if Typ == True:
#						print a, "Select", req.args.get(a,None)
						exec("%s.value = '%s'" % (a,req.args.get(a,"")[0]))
					else:
#ConfigYesNo
						exec("Typ = isinstance(%s,ConfigYesNo)" % a)
						if Typ == True:
#							print a, "YesNo", req.args.get(a,"")
							if len(req.args.get(a,"")) == 2:
								exec("%s.value = True" % a)
							else:
								exec("%s.value = False" % a)
						else:
#ConfigText
							exec("Typ = isinstance(%s,ConfigText)" % a)
							if Typ == True:
#								print a, "Text", req.args.get(a,None)
								exec("%s.value = '%s'" % (a,_l2(req.args.get(a,"")[0])))
							else:
#ConfigSlider
								exec("Typ = isinstance(%s,ConfigSlider)" % a)
								if Typ == True:
#									print a, "Slider", req.args.get(a,None)
									if req.args.get(a,"")[0].isdigit():
										exec("%s.value = %s" % (a,req.args.get(a,"")[0]))
								else:
#ConfigClock
									exec("Typ = isinstance(%s,ConfigClock)" % a)
									if Typ == True:
#										print a, "Clock", req.args.get(a,"")
										t=req.args.get(a,"")[0].split(":")
										if len(t)==2:
											if t[0].isdigit() and t[1].isdigit():
												w1 = "[%s,%s]" % (int(t[0]),int(t[1]))
												exec("%s.value = %s" % (a,w1))
					exec("C = %s.isChanged()" % a)
					if C:
						exec("C = %s.save()" % a)
						L4log("Changed",a)
						if a.find("Fritz") >0:
							Cfritz = True
						elif a.find("Wetter") >0:
							Cwetter = True
						elif a.find("Picon") >0:
							Cpicon = True
						elif a.find(".Cal") >0 or a.find(".MPCal") >0 or a.find(".StandbyCal") >0:
							Ccal = True
						elif a.find(".xmlType") >0:
							if a.find(".xmlLCDType") >0:
								xmlRead()
								if xmlDelete(1) or xmlDelete(2) or xmlDelete(3):
									L4log("removed old Skindata")
									xmlWrite()
							if xmlSkin():
								xmlWrite()
								LCD4linuxConfigweb.RestartGUI = True
							xmlClear()
						if a.find("WetterCity") >0:
							resetWetter()
						if a.find("ScreenActive") >0:
							setScreenActive(LCD4linux.ScreenActive.value)
						if a.find("BildFile") >0:
							getBilder()
						if a.find("WWW1") >0:
							rmFile(WWWpic % "1p")
							if a.find("WWW1url") >0 or os.path.isfile(WWWpic % "1") == False:
								Cwww = True
#			print "L4L",Cfritz,	Cwetter, Cpicon
			if Cfritz:
				CheckFritz()
				rmFile(PICfritz)
			if Cwetter:
				rmFile(PICwetter % "0")
				rmFile(PICwetter % "1")
				resetWetter()
			if Cpicon:
				rmFiles(LCD4linux.PiconCache.value + "*.png")
			if Ccal:
				rmFile(PICcal)
			if Cwww:
				getWWW()

			open(Push,"w").write("")
#####################
# Anzeige
#####################
		html = "<html>"
		html += "<head>\n"
		html += "<meta http-equiv=\"Content-Language\" content=\"de\">\n"
		html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\">\n"
		html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"expires\" content=\"0\">\n"
		if os.path.isfile(CrashFile):
			html += "<script language=\"JavaScript\">\n"
			html += "function fensterchen() {\n"
			html += "fens1=window.open(\"\", \"Crashlog\",\"width=500,height=300,resizable=yes\");\n"
			for line in open(CrashFile,"r").readlines():
				html += "fens1.document.write('%s');\n" % line.replace("\n","<br>").replace("'","\\'")
			html += "} </script>\n"
		if os.path.isfile(Push):
			html += "<meta http-equiv=\"refresh\" content=\"6\">\n"
		html += "<title>LCD4linux</title>\n"
		html += "</head>"
		html += "<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n"
		html += "<form method=\"POST\" action=\"--WEBBOT-SELF--\">\n"
		html += "</form>\n"
		html += "<table border=\"1\" rules=\"groups\" width=\"100%\" bordercolorlight=\"#000000\" bordercolordark=\"#000000\" cellspacing=\"0\">"
		html += "<tr><td bgcolor=\"#000000\" width=\"220\">\n"
		html += "<p align=\"center\"><img alt=\"\" border=\"0\" src=\"/lcd4linux/data/WEBdreambox.png\" width=\"181\" height=\"10\">\n"
		html += "<font color=\"#FFFFFF\"><b>LCD4linux Config</b></font><br />%s\n" % Version
		html += "</p></td><td bgcolor=\"#000000\">\n"
		html += "<p align=\"left\">"
		d = glob.glob("%sdpf.*" % getTMPL())
		if len(d)>0:
			html += "<a href=\"/lcd4linux\"><img alt=\"LCD 1\" src=\"/lcd4linux/%s?%d\" height=\"80\" id=\"reloader1\" onload=\"setTimeout('document.getElementById(\\'reloader1\\').src=\\'/lcd4linux/%s?\\'+new Date().getTime()', 5000)\" ></a>" % (os.path.basename(d[0]),time.time(),os.path.basename(d[0]))
		d = glob.glob("%sdpf2.*" % getTMPL())
		if len(d)>0:
			html += "<a href=\"/lcd4linux?file=%s\"><img alt=\"LCD 2\" src=\"/lcd4linux/%s?%d\" height=\"80\" id=\"reloader2\" onload=\"setTimeout('document.getElementById(\\'reloader2\\').src=\\'/lcd4linux/%s?\\'+new Date().getTime()', 5000)\" ></a>" % (os.path.basename(d[0]),os.path.basename(d[0]),time.time(),os.path.basename(d[0]))
		d = glob.glob("%sdpf3.*" % getTMPL())
		if len(d)>0:
			html += "<a href=\"/lcd4linux?file=%s\"><img alt=\"LCD 3\" src=\"/lcd4linux/%s?%d\" height=\"80\" id=\"reloader3\" onload=\"setTimeout('document.getElementById(\\'reloader3\\').src=\\'/lcd4linux/%s?\\'+new Date().getTime()', 5000)\" ></a>" % (os.path.basename(d[0]),os.path.basename(d[0]),time.time(),os.path.basename(d[0]))
		html += "</p></td>\n"
		if os.path.isfile(CrashFile):
			html += "<td valign=\"top\" align=\"left\"  bgcolor=\"#000000\">\n"
			html += "<form method=\"post\"><font color=\"#FFFFFF\">%s</font><br>\n" % _l(_("Crashlog"))
			html += "<input type=\"hidden\" name=\"cmd\" value=\"\">\n"
			html += "<input type=\"button\" value=\"%s\" style=\"font-size:8pt;\" onClick=\"fensterchen()\">\n"  % _l(_("Show"))
			html += "<input type=\"button\" value=\"%s\" style=\"font-size:8pt;\"   onclick=\"this.form.cmd.value = 'crashdel'; this.form.submit();\">\n"  % _l(_("Delete"))
			html += "</form></td>\n"
		html += "<td  valign=\"top\" align=\"right\"  bgcolor=\"#000000\">\n"
		html += "<form method=\"post\">\n"
		html += "<input type=\"image\" name=\"save\" value=\"klick\" src=\"/lcd4linux/data/WEBsave.png\" height=\"40\" alt=\"Save Config\">\n"
		html += "</form>\n"
		html += "<form method=\"post\"><font color=\"#FFFFFF\">%s</font>\n" % _l(_("Screen"))

		html += "<input type=\"hidden\" name=\"cmd\" value=\"\">\n"
		for i in range(1,10):
			html += "<input type=\"button\" value=\"%d\" style=\"width:15px; text-align:center; font-size:8pt%s\" onclick=\"this.form.cmd.value = 'Screen%d'; this.form.submit();\">\n" % (i,AktiveScreen(str(i)),i)

		html += "</form>\n"
		html += "</td></tr></table>\n"

		html += "<form method=\"get\">"
		html += "<fieldset style=\"width:auto\" name=\"Mode1\">"
#		html += "<fieldset style=\"width:330px\" name=\"Mode1\">"
		html += "<legend style=\"color: #FFCC00\">Modus</legend>\n"
		html += "<input id=\"r1\" name=\"Mode\" type=\"radio\" value=\"1\" %s onclick=\"this.form.submit();\"><label %s for=\"r1\">Global&nbsp;&nbsp;</label>\n" % (AktiveMode("1"))
		html += "<input id=\"r2\" name=\"Mode\" type=\"radio\" value=\"2\" %s onclick=\"this.form.submit();\"><label %s for=\"r2\">On&nbsp;&nbsp;</label>\n" % (AktiveMode("2"))
		html += "<input id=\"r3\" name=\"Mode\" type=\"radio\" value=\"3\" %s onclick=\"this.form.submit();\"><label %s for=\"r3\">Media&nbsp;&nbsp;</label>\n" % (AktiveMode("3"))
		html += "<input id=\"r4\" name=\"Mode\" type=\"radio\" value=\"4\" %s onclick=\"this.form.submit();\"><label %s for=\"r4\">Idle&nbsp;&nbsp;</label>\n" % (AktiveMode("4"))
		if LCD4linux.Popup.value != "0":
			html += "<input id=\"r5\" name=\"Mode\" type=\"radio\" value=\"5\" %s onclick=\"this.form.submit();\"><label %s for=\"r5\">Popup-Text&nbsp;&nbsp;</label>\n" % (AktiveMode("5"))
		html += "</fieldset></form>\n"

		if Mode != "5":
			if Mode == "1":
				L = L1
#				Element = "other"
			elif Mode == "2":
				L = L2
			elif Mode == "3":
				L = L3
			elif Mode == "4":
				L = L4
			else:
				Mode == "1"
				L = L1
				Element = "other"
			html += "<form method=\"get\">"
			html += "<fieldset style=\"width:auto\" name=\"Mode2\">"
			html += "<legend style=\"color: #FFCC00\">Element</legend>\n"
			i=0
			ElementList = []
			for LL in L:
				Conf = LL[2].strip()
				if Mode == "1":
					Conf = Conf[:13]
				if ((LL[1][:1] != "-" and Mode!="1") or (Mode == "1" and Conf not in ElementList )) and LL[3] != 0:
					if Element == "" or ModeOld != Mode:
						Element = "other"
						ModeOld = Mode
#						if Mode == "1":
#							Conf = M1[LL[3]-1]
#							Element = Conf
					ElementList.append(Conf)
					i+=1
					Ea,Ec = AktiveElement(Conf)
					html += "<input id=\"e%d\" name=\"Element\" type=\"radio\" value=\"%s\" %s onclick=\"this.form.submit();\"><label %s for=\"e%d\">%s&nbsp;&nbsp;</label>\n" % (i,Conf,Ea,Ec,i, (_l(_(LL[1])) if Mode !="1" else M2[LL[3]-1]) )
#			if Mode != "4":
			Ea,Ec = AktiveElement("other")
			html += "<input id=\"e%d\" name=\"Element\" type=\"radio\" value=\"%s\" %s onclick=\"this.form.submit();\"><label %s for=\"e%d\">%s&nbsp;&nbsp;</label>\n" % (0,"other",Ea,Ec,0,_("other"))
			html += "</fieldset></form>\n"

			html += "<form name=\"Eingabe\" method=\"POST\">\n"

			html += "<table border=\"1\" rules=\"groups\" width=\"100%\">"
			AktCode = 0
			isOn = False
			isMP = False
			isSb = False
			for LL in L:
#				print LL
				Conf = LL[2].strip()

				if (Conf.startswith(Element) and (LL[3] == AktCode or AktCode == 0)) or (Element=="other" and LL[3] == 0):
				
					if Mode in "2":
						if "." in Conf:
							b = Conf.replace(".",".MP")
							if (" "+b) in zip(*L3)[2]:
								isMP = True
							b = Conf.replace(".",".Standby")
							if (" "+b) in zip(*L4)[2]:
								isSb = True
					elif Mode in "3":
						if ".MP" in Conf:
							b = Conf.replace(".MP",".")
							if (" "+b) in zip(*L2)[2]:
								isOn = True
							b = Conf.replace(".MP",".Standby")
							if (" "+b) in zip(*L4)[2]:
								isSb = True
					elif Mode in "4":
						if ".Standby" in Conf:
							b = Conf.replace(".Standby",".")
							if (" "+b) in zip(*L2)[2]:
								isOn = True
							b = Conf.replace(".Standby",".MP")
							if (" "+b) in zip(*L3)[2]:
								isMP = True
		
					if AktCode == 0:
						AktCode = LL[3]
					exec("Curr = %s.value" % Conf)
#ConfigSelection
					exec("Typ = isinstance(%s,ConfigSelection)" % Conf)
					html += "<tr>\n"
					if Typ == True:
						html += "<td width=\"300\">%s</td><td>\n" % _l(_(LL[1]))
						html += "<select name=\"%s\" size=\"1\">\n" % Conf
						exec("Len = len(%s.description)" % Conf)
						for i in range(Len):
							exec("Choice = %s.choices[%d]" % (Conf,i))
							exec("Wert = %s.description[\"%s\"]" % (Conf,Choice))
							if Choice == Curr:
								Aktiv = " selected"
							else:
								Aktiv = ""
							html += "<option value=\"%s\" %s>%s</option>\n" % (Choice,Aktiv,_l(Wert))
						html += "</select>\n"
						html += "</td>\n"
					else:
#ConfigYesNo
						exec("Typ = isinstance(%s,ConfigYesNo)" % Conf)
						if Typ == True:
							html += "<td width=\"300\">%s</td><td>\n" % _l(_(LL[1]))
							Aktiv = "checked" if Curr else ""
							html += "<input type=\"hidden\" name=\"%s\" value=\"%s\">" % (Conf,"unchecked")
							html += "<input type=\"checkbox\" name=\"%s\" value=\"%s\" %s>" % (Conf,"checked",Aktiv)
							html += "</td>\n"
						else:
#ConfigText	
							exec("Typ = isinstance(%s,ConfigText)" % Conf)
							if Typ == True:
								html += "<td width=\"300\">%s</td><td>\n" % _l(_(LL[1]))
								exec("Typ = isinstance(%s,ConfigPassword)" % Conf)
								if Typ == True:
									html += "<input type=\"password\" name=\"%s\" size=\"60\" value=\"%s\">" % (Conf,_l(Curr))
								else:
									html += "<input type=\"text\" name=\"%s\" size=\"60\" value=\"%s\">" % (Conf,_l(Curr))
								html += "</td>\n"
							else:
#ConfigSlider
								exec("Typ = isinstance(%s,ConfigSlider)" % Conf)
								if Typ == True:
									exec("Min = %s.min" % Conf)
									exec("Max = %s.max" % Conf)
									html += "<td width=\"300\">%s (%d - %d)</td><td>\n" % (_l(_(LL[1])), Min, Max)
									html += "<input type=\"text\" name=\"%s\" size=\"5\" value=\"%s\">" % (Conf,Curr)
									html += "</td>\n"
								else:
#ConfigClock
									exec("Typ = isinstance(%s,ConfigClock)" % Conf)
									if Typ == True:
										html += "<td width=\"300\">%s</td><td>\n" % _l(_(LL[1]))
										html += "<input type=\"text\" name=\"%s\" size=\"6\" value=\"%02d:%02d\">" % (Conf,Curr[0],Curr[1])
										html += "</td>\n"

			html += "</tr></table>\n"
			html += "<input type=\"hidden\" name=\"cmd\" value=\"config\">\n"
			html += "<input type=\"submit\" style=\"background-color: #FFCC00\" value=\"%s\">\n" % _("set Settings")
			if Element != "other":
				if Mode in ["3","4"] and isOn:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"%s\" onclick=\"this.form.cmd.value = 'copyOn'; this.form.submit(); \">\n" % _("copy to On")
				if Mode in ["2","4"] and isMP:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"%s\" onclick=\"this.form.cmd.value = 'copyMP'; this.form.submit(); \">\n" % _("copy to Media")
				if Mode in ["2","3"] and isSb:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"%s\" onclick=\"this.form.cmd.value = 'copyIdle'; this.form.submit(); \">\n" % _("copy to Idle")
			html += "</form>\n"
		elif Mode == "5":
			html += "<form method=\"POST\">\n"
			html += "<fieldset style=\"width:auto\" name=\"Mode2\">\n"
			html += "<textarea name=\"PopText\" style=\"height: 120px; width: 416px\">%s</textarea>" % PopText[1]
			html += "<input type=\"hidden\" name=\"cmd\" value=\"pop\">\n"
			html += "<input type=\"submit\" style=\"background-color: #FFCC00\" value=\"%s\">\n" % _("set Settings")
			html += "</fieldset></form>\n"

		if LCD4linuxConfigweb.RestartGUI == True:
			html += "<span style=\"color: #FF0000;\"><strong>%s</strong></span>" % _l(_("GUI Restart is required"))
		if ExeMode == True:
			html += "<br />\n"
			html += "<form method=\"GET\">\n"
			html += "<input type=\"hidden\" name=\"cmd\" value=\"exec\">\n"
			html += "<input style=\"width: 400px\" type=\"text\" name=\"ex\">\n"
			html += "<input type=\"submit\" value=\"%s\">\n" % _l(_("Exec"))
			html += "</form>\n"
	
		html += "<hr><span style=\"font-size:8pt\">%s</span>" % getINFO()
		
		html += "</body>\n"
		html += "</html>\n"

		return html

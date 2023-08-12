# -*- coding: utf-8 -*-
# external interface for LCD4linux
# by joergm6 @ IHAD
# for documentation look at IHAD Support Thread

from os import popen
from os.path import isfile, exists


class L4Lelement:
	List = {}
	Refresh = False
	MAX_W = [0, 0, 0]
	MAX_H = [0, 0, 0]
	Bright = [-1, -1, -1]
	BrightAkt = [0, 0, 0]
	Screen = ""
	LCD = ""
	Hold = False
	HoldKey = False
	Font = ["", "", "", ""]
	Version = False

	def __init__(self):
		self.session = None

	def add(self, element, para):
		print("[LCD4linuxE] Add: %s %s" % (element, para))
		if "%" in para.get("Align", ""):
			para["Align"] = ("0000" + para["Align"].replace("%", "00"))[-4:]
		if para.get("Value", None) is not None:
			para["Value"] = min(max(int(para["Value"]), 0), 100)
		L4Lelement.List[element] = para

	def delete(self, element):
		print("[LCD4linuxE] Del: %s" % element)
		if L4Lelement.List.get(element, None) is not None:
			del L4Lelement.List[element]
		else:
			for x in list(L4Lelement.List):
				if x.startswith(element):
					del L4Lelement.List[x]

	def show(self):
		print(L4Lelement.List)

	def get(self, element=None):
		if element == None:
			return L4Lelement.List
		else:
			return L4Lelement.List.get(element, {})

	def web(self, EX):
		try:
			exec("self.add('%s)" % EX.replace(",", "',", 1))
		except:
			print("[LCD4linuxE] Error: L4L Web-Elements")

	def getResolution(self, LCD):
		if int(LCD) < 1 or int(LCD) > 3:
			return 0, 0
		return L4Lelement.MAX_W[int(LCD) - 1], L4Lelement.MAX_H[int(LCD) - 1]

	def setResolution(self, LCD, MW, MH):
		L4Lelement.MAX_W[int(LCD) - 1] = int(MW)
		L4Lelement.MAX_H[int(LCD) - 1] = int(MH)

	def resetRefresh(self):
		L4Lelement.Refresh = False

	def setRefresh(self):
		L4Lelement.Refresh = True

	def getRefresh(self):
		return L4Lelement.Refresh

	def getHold(self):
		return L4Lelement.Hold

	def setHold(self, H):
		print("[LCD4linuxE] Hold: %s" % H)
		L4Lelement.Hold = H

	def getHoldKey(self):
		return L4Lelement.HoldKey

	def setHoldKey(self, H=False):
		print("[LCD4linuxE] HoldKey: %s" % H)
		L4Lelement.HoldKey = H

	def getFont(self, F="0"):
		if L4Lelement.Font[int(F)].endswith(".ttf") and isfile(L4Lelement.Font[int(F)]):
			return L4Lelement.Font[int(F)]
		else:
			return L4Lelement.Font[0]

	def setFont(self, F):
		L4Lelement.Font = F

	def getScreen(self):
		return L4Lelement.Screen

	def setScreen(self, S, Lcd="", Hold=False):
		if Lcd != "":
			if len(str(Lcd)) > 1 or int(Lcd) > 3:
				Lcd = "1"
		L4Lelement.Screen = str(S)
		L4Lelement.LCD = str(Lcd)
		L4Lelement.Hold = Hold
		L4Lelement.Refresh = True

	def resetBrightness(self, AKT=[]):
		if len(AKT) == 3:
			L4Lelement.BrightAkt = AKT
		else:
			L4Lelement.Bright = [-1, -1, -1]

	def setBrightness(self, LCD, BRI=-1):
		if int(LCD) < 1 or int(LCD) > 3:
			return
		L4Lelement.Bright[int(LCD) - 1] = int(BRI)
		L4Lelement.Refresh = True

	def getBrightness(self, LCD=0, ORG=True):
		if LCD > 0 and LCD < 4:
			return L4Lelement.Bright[LCD - 1] if ORG == False else L4Lelement.BrightAkt[LCD - 1]
		else:
			return L4Lelement.Bright[0] if ORG == False else L4Lelement.BrightAkt[0]

	def getLcd(self):
		return L4Lelement.LCD

	def setVersion(self, V):
		L4Lelement.Version = L4LVtest(V)

	def getVersion(self):
		return L4Lelement.Version


def getstatusoutput(cmd):
	try:
		pipe = popen('{ ' + cmd + '; } 2>&1', 'r')
		text = pipe.read()
		sts = pipe.close()
		if sts is None:
			sts = 0
		if text[-1:] == '\n':
			text = text[:-1]
	except:
		sts = 1
		text = "- -"
		print("[LCD4linux] Error on os-call")
	finally:
		return sts, text


def L4LVtest(VV):
	L4Linfo = "/%s/lib/%s/info/enigma2-plugin-extensions-lcd4linux.control"
	O = ""
	OO = False
	P = "opkg"
	if exists(L4Linfo % ("var", "opkg")):
		O = "var"
	elif exists(L4Linfo % ("var", "dpkg")):
		O = "var"
		P = "dpkg"
	elif exists("/var/lib/dpkg/status"):
		(r1, r2) = getstatusoutput("dpkg -s enigma2-plugin-extensions-lcd4linux | grep Version")
		if r1 == 0:
			OO = r2.strip().split()[1].startswith(VV[1:])
	if O != "":
		try:
			f = open(L4Linfo % (O, P))
			OO = f.readline().strip().split()[1].startswith(VV[1:])
			f.close()
		except:
			pass
	return OO

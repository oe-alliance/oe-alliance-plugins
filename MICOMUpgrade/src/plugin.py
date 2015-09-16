# for localized messages
from . import _

import os, urllib
from urllib import urlretrieve

from Plugins.Plugin import PluginDescriptor

from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigText, ConfigSelection, ConfigYesNo,ConfigText
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.Label import Label

from Components.FileList import FileList
from Components.Slider import Slider

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from enigma import ePoint, eConsoleAppContainer, eTimer
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from shutil import copyfile

fwlist = None
fwdata = None

if os.path.exists("/proc/stb/info/boxtype"):
	inimodel = open("/proc/stb/info/boxtype")
	info = inimodel.read().strip()
	inimodel.close()

	if info == "ini-1000":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS100_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-1000ru":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS100RU_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-1000sv":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS100SV_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-1000de":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS100DE_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-1000am":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS300AM_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-2000am":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS200AM_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-2000sv":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS200SV_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-3000":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS300_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-5000":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS500_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-5000ru":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS500RU_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-5000sv":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS500SV_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-7000":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS700_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-7012":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS712_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-7012au":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "RHS712AU_Micom.bin", "/dev/dbox/oled0;/dev/mcu;"]
			}
	elif info == "ini-8000am":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "INI800AM_Micom.bin", "/proc/vfd;/dev/mcu;"]
			}
	elif info == "ini-8000sv":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "INI800SV_Micom.bin", "/proc/vfd;/dev/mcu;"]
			}
	elif info == "ini-9000de":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "INI900DE_Micom.bin", "/proc/vfd;/dev/mcu;"]
			}
	elif info == "ini-9000ru":
		fwlist= [
			("fp", _("Front Panel"))
			]
		fwdata= {
			 "micom" : ["http://code-ini.com/software/micom/", "INI900RU_Micom.bin", "/proc/vfd;/dev/mcu;"]
			}
			
class Filebrowser(Screen):
	skin = 	"""
		<screen position="center,center" size="500,490" title="File Browser" >
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/MICOMUpgrade/buttons/yellow.png" position="5,7" size="140,40" alphatest="blend" />		
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/MICOMUpgrade/buttons/blue-340.png" position="150,7" size="340,40" alphatest="blend" />
			<widget source="key_yellow" render="Label" position="5,7" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" transparent="1"/>
			<widget source="key_blue" render="Label" position="150,7" zPosition="1" size="340,40" font="Regular;20" halign="center" valign="center" transparent="1"/>
			<widget name="file_list" position="0,60" size="500,360" scrollbarMode="showOnDemand" />
			<widget source="status" render="Label" position="0,430" zPosition="1" size="500,75" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
                </screen>
		"""

	def __init__(self, session, parent, firmware):
		Screen.__init__(self, session)
                self.session = session

		self["key_blue"] = StaticText(_("Download the firmware (latest)"))
		self["key_yellow"] = StaticText(_("Cancel"))

		self["status"]    = StaticText(" ")
		self["file_list"] = FileList("/", matchingPattern = "^.*")

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", ],
                {
			"ok":     self.onClickOk,
			"cancel": self.onClickCancel,
			"blue":   self.onClickBlue,
			"yellow": self.onClickCancel,
			"up":     self.onClickUp,
			"down":   self.onClickDown,
			"left":   self.onClickLeft,
			"right":  self.onClickRight,
                }, -1)

		self.resetGUI()
		self.firmware = firmware

		self.callback = None
		self.timer_downloading = None

		self.downloadLock = False
		self.setTitle(firmware.upper() + " File Browser")

	def resetGUI(self):
		self["status"].setText("Select to press OK, Exit to press Cancel.")

	def setCallback(self, func):
		self.callback = func

	def onClickOk(self):
		if self.downloadLock:
			return

	        if self["file_list"].canDescent() : # isDir
	        	self["file_list"].descent()
        		return

		# verify data
		self.gbin = self["file_list"].getCurrentDirectory() + self["file_list"].getFilename()
		if not os.path.exists(self.gbin):
			self.session.open(MessageBox, _("Can't found binary file."), MessageBox.TYPE_INFO, timeout = 10)
			return
		if not os.path.exists(self.gbin+".md5"):
			self.session.open(MessageBox, _("Can't found MD5 file."), MessageBox.TYPE_INFO, timeout = 10)
			return
		try:
			def checkExt(ext):
				name_ext = os.path.splitext(self["file_list"].getFilename())
				return len(name_ext)==2 and ext.startswith(name_ext[1])
			self.check_ext = False
			if (self.firmware == "micom" and checkExt(".bin")):
				self.check_ext = True
			if self.check_ext == False:
				self.session.open(MessageBox, _("You chose the incorrect file."), MessageBox.TYPE_INFO)
				return
		except:
			self.session.open(MessageBox, _("You chose the incorrect file."), MessageBox.TYPE_INFO)
			return

		if os.path.exists("/usr/bin/md5sum") == False:
			self.session.open(MessageBox, _("Can't find /usr/bin/md5sum"), MessageBox.TYPE_INFO, timeout = 10)
			return
		md5sum_A = os.popen("md5sum %s | awk \'{print $1}\'"%(self.gbin)).readline().strip()
		md5sum_B = os.popen("cat %s.md5 | awk \'{print $1}\'"%(self.gbin)).readline().strip()
		#print "[FirmwareUpgrade] - Verify : file[%s], md5[%s]"%(md5sum_A,md5sum_B)

		if md5sum_A != md5sum_B:
			self.session.open(MessageBox, _("Fail to verify data file. \nfile[%s]\nmd5[%s]"%(md5sum_A,md5sum_B)), MessageBox.TYPE_INFO, timeout = 10)
			return

		
		if self.callback is not None:
			self.callback(_(self.gbin))
		self.close()

	def onClickCancel(self):
		self.close()

	# uri : source file url(string)
	# tf  : target file name(string)
	# bd  : target base directory(string)
	# cbfunc(string) : callback function(function)
	def doDownload(self, uri, tf, bd='/tmp', cbfunc=None, errmsg="Fail to download."):
		tar = bd + "/" + tf
		#print "[FirmwareUpgrade] - Download Info : [%s][%s]" % (uri, tar)
		def doHook(blockNumber, blockSize, totalSize) :
			if blockNumber*blockSize > totalSize and cbfunc is not None:
				cbfunc(tar)
		opener = urllib.URLopener()
		try:
			opener.open(uri)
		except:
			#self.session.open(MessageBox, _("File not found in this URL:\n%s"%(uri)), MessageBox.TYPE_INFO, timeout = 10)
			print "[FirmwareUpgrade] - Fail to download. URL :",uri
			self.session.open(MessageBox, _(errmsg), MessageBox.TYPE_INFO, timeout = 10)
			del opener
			return False
		try :
			f, h = urlretrieve(uri, tar, doHook)
		except IOError, msg:
			#self.session.open(MessageBox, _(str(msg)), MessageBox.TYPE_INFO, timeout = 10)
			print "[FirmwareUpgrade] - Fail to download. ERR_MSG :",str(msg)
			self.session.open(MessageBox, _(errmsg), MessageBox.TYPE_INFO, timeout = 10)
			del opener
			return False
		del opener
		return True

	def runDownloading(self) :
		self.timer_downloading.stop()
		machine = str(open("/proc/stb/info/boxtype").read().strip())

		def cbDownloadDone(tar):
			try:
				self["status"].setText("Downloaded : %s\nSelect to press OK, Exit to press Cancel."%(tar))
			except:
				pass
		# target
		global fwdata
		root_uri  = fwdata[self.firmware][0]
		root_file = fwdata[self.firmware][1]
		micom_url = root_uri + machine + "/" + root_file
		
		target_path = "/tmp/" + root_file

		self.guri = micom_url
		self.gbin = os.path.basename(target_path)
		os.system("rm -f /tmp/" + root_file)

		# md5
		if not self.doDownload(self.guri+".md5", self.gbin+".md5", cbfunc=cbDownloadDone, errmsg="Can't download the checksum file."):
			self.resetGUI()
			self.downloadLock = False
			return
		# data
		if not self.doDownload(self.guri, self.gbin, cbfunc=cbDownloadDone, errmsg="Can't download the firmware file."):
			self.resetGUI()
			self.downloadLock = False
			return
		# version
		if not self.doDownload(self.guri+".version", self.gbin+".version", cbfunc=cbDownloadDone, errmsg="Can't download the version file."):
			self.resetGUI()
			self.downloadLock = False
			return
		      
		t = ''
		self["file_list"].changeDir("/tmp/")
		self["file_list"].moveToIndex(0)
		while cmp(self["file_list"].getFilename(), self.gbin) != 0 :
			self["file_list"].down()
			if cmp(t, self["file_list"].getFilename()) == 0:
				break
			t = self["file_list"].getFilename()

		del self.timer_downloading
		self.timer_downloading = None
		self.downloadLock = False

	def onClickBlue(self):
		if self.downloadLock:
			return
		self.downloadLock = True
		if not os.path.exists("/proc/stb/info/boxtype"):
			self.session.open(MessageBox, _("Can't found model name."), MessageBox.TYPE_INFO, timeout = 10)
			self.downloadLock = False
			return
		self["status"].setText("Please wait during download.")
		self.timer_downloading = eTimer()
		self.timer_downloading.callback.append(self.runDownloading)
		self.timer_downloading.start(1000)

	def onClickUp(self):
		if self.downloadLock:
			return
		self.resetGUI()
		self["file_list"].up()

	def onClickDown(self):
		if self.downloadLock:
			return
		self.resetGUI()
		self["file_list"].down()

	def onClickLeft(self):
		if self.downloadLock:
			return
		self.resetGUI()
		self["file_list"].pageUp()

	def onClickRight(self):
		if self.downloadLock:
			return
		self.resetGUI()
		self["file_list"].pageDown()

	def keyNone(self):
		None

class FirmwareUpgrade(Screen):
	skin = 	"""
		<screen position="center,center" size="530,295" title="Firmware Upgrade" >
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/MICOMUpgrade/buttons/red.png" position="80,7" size="140,40" alphatest="blend" />
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/MICOMUpgrade/buttons/green.png" position="320,7" size="140,40" alphatest="blend" />
			<widget source="key_red" render="Label" position="80,7" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget source="key_green" render="Label" position="320,7" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget name="oldversion_label" position="80,100" size="290,25" font="Regular;20" />
			<widget name="newversion_label" position="80,125" size="290,25" font="Regular;20" />
			<widget name="oldversion" position="320,100" size="100,25" font="Regular;20" />
			<widget name="newversion" position="320,125" size="100,25" font="Regular;20" />
			<widget source="status" render="Label" position="0,180" zPosition="1" size="510,75" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
                </screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)
                self.session = session

		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok":      self.keyGreen,
			"cancel":  self.keyRed,
			"red":     self.keyRed,
			"green":   self.keyGreen,
		}, -2)

		self.list = []
		self.updateFilePath = ""

		self.finishedExit = False

		self.rebootLock = False
		self.rebootMessage = ""
		self.cbRebootCallCount = 0;

		from Tools.StbHardware import getFPVersion
		self.version = str(getFPVersion() or "N/A")
		newversion = str("N/A")

		self["oldversion_label"] = Label(_("Current version:"))
		self["newversion_label"] = Label(_("New version:"))

		self["oldversion"] = Label(self.version)
		self["newversion"] = Label(newversion)
		
		self["key_red"] = StaticText(_("Close"))

		self.logmode = None
		self.old_blue_clicked = 0
		self.fileopenmode = False
		self.upgrade_auto_run_timer = eTimer()
		self.upgrade_auto_run_timer.callback.append(self.keyGreen)

		global fwlist
		if fwlist is None:
			self["key_green"] = StaticText(" ")
			self["status"] = StaticText(_("This plugin is supported only the INI-Series."))
		else:
			self["key_green"] = StaticText(_("Upgrade"))
			self["status"] = StaticText(" ")
			self.setupUI()

	def setupUI(self):
		self.setupStatus()

	def setupStatus(self,message=None,reboot=False):
		self.updateFilePath = ""
		if message is not None:
			self.rebootLock = reboot
		if not self.rebootLock:
			self["status"].setText("Press the Green/OK button to upgrade")

	def doReboot(self):
		from Screens.Standby import TryQuitMainloop
		self.session.open(TryQuitMainloop, 44)
		
	# filebrowser window callback function
	def cbSetStatus(self, data=None):
		if data is not None:
			try:
				fp = open(data+'.version', "r")
				self.verfile = fp.readline()
				fp.close()
				self.verfile = self.verfile.strip("\n")
			except:
				self.verfile = "N/A"
			self["newversion"].setText(self.verfile)
			
			# HACK for samples, which does not have micom version
			try:
				if int(self.verfile) <= int(self.version):
					self["status"].setText("You have already latest front panel version")
				else:
					self["status"].setText("Press the Green/OK button, if you want to upgrade to this file:\n%s\n" % (data))
			except:
				self["status"].setText("Press the Green/OK button, if you want to upgrade to this file:\n%s\n" % (data))
			self.updateFilePath = data
			if self.fileopenmode == False:
				self.upgrade_auto_run_timer.start(1000)
		
	def cbRunUpgrade(self, ret):
		if ret == False:
			return

		if self.updateFilePath == "":
			self.session.open(MessageBox, _("No selected binary data!!"), MessageBox.TYPE_INFO, timeout = 10)
			return
		device = None
		for d in fwdata['micom'][2].split(';'):
			if os.path.exists(d):
				device = d
		if device is None:
			self.session.open(MessageBox, _("Can't found device file!!"), MessageBox.TYPE_INFO, timeout = 10)
			return
		      
		copyfile(self.updateFilePath,"/tmp/micom.bin")
		self.doReboot()
		return

	def doFileOpen(self):
		fbs = self.session.open(Filebrowser, self, "micom")
		fbs.setCallback(self.cbSetStatus)

	def keyGreen(self):
		self.upgrade_auto_run_timer.stop()
		if self.rebootLock:
			return
		global fwlist
		if fwlist is None:
			return
		if self.updateFilePath == "":
			self.doFileOpen()
			return
		# check if downloaded verion is newer then flashed one
		# HACK for samples, which does not have micom version
		try:
			if int(self.verfile) <= int(self.version):      
				self.session.open(MessageBox, _("You can not upgrade to the same or lower version !"), MessageBox.TYPE_INFO, timeout = 10)
				return
		except:
			pass # always flash when no micom version
		msg = "You should not be stop during the upgrade.\nDo you want to upgrade?"
		self.session.openWithCallback(self.cbRunUpgrade, MessageBox, _(msg), MessageBox.TYPE_YESNO, timeout = 15, default = True)
		self.fileopenmode = False


	def keyRed(self):
		if self.rebootLock:
			return
		self.close()

	def keyNone(self):
		None

      
def main(session, **kwargs):
        session.open(FirmwareUpgrade)

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Front Panel Update"), description="Upgrade Front panel..", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)


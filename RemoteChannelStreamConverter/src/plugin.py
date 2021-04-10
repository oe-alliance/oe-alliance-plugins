# -*- coding: UTF-8 -*-
# for localized messages
import os
import re
from . import _
from boxbranding import getBoxType, getImageDistro

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.SelectionList import SelectionList
from Components.ActionMap import ActionMap
from Components.config import config, configfile, ConfigInteger, ConfigSubsection, ConfigText, ConfigYesNo, getConfigListEntry, ConfigIP
from enigma import eServiceCenter, eServiceReference, eDVBDB
from ServiceReference import ServiceReference
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.protocols.ftp import FTPClient
from urllib import quote

from FTPDownloader import FTPDownloader

DIR_ENIGMA2 = '/etc/enigma2/'
DIR_TMP = '/tmp/'
RCSC_PREFIX = 'userbouquet.rcsc.'

config.plugins.RemoteStreamConverter = ConfigSubsection()
config.plugins.RemoteStreamConverter.address = ConfigText(default = "", fixed_size = False)
config.plugins.RemoteStreamConverter.ip = ConfigIP(default = [0,0,0,0])
config.plugins.RemoteStreamConverter.username = ConfigText(default = "root", fixed_size = False)
config.plugins.RemoteStreamConverter.password = ConfigText(default = "", fixed_size = False)
config.plugins.RemoteStreamConverter.port = ConfigInteger(21, (0, 65535))
config.plugins.RemoteStreamConverter.passive = ConfigYesNo(False)
config.plugins.RemoteStreamConverter.telnetport = ConfigInteger(23, (0, 65535))


class ServerEditor(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="560,230" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label"  position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="10,50" size="550,150" scrollbarMode="showOnDemand" enableWrapAround="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("FTP Server Editor"))
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self.isIp = True
		self.list = []
		ConfigListScreen.__init__(self, self.list)
		if config.plugins.RemoteStreamConverter.address.value != '':
			self.createMenuAdress()
		else:
			self.createMenuIp()
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"],
			{
				"up": self.keyUp,
				"down": self.keyDown,
				"ok": self.keySave,
				"save": self.keySave,
				"cancel": self.keyCancel,
				"blue": self.enterUrl,
				"yellow": self.switchMode
			}, -2)

	def keyUp(self):
		if self["config"].getCurrentIndex() > 0:
			self["config"].setCurrentIndex(self["config"].getCurrentIndex() - 1)
			self.setVkeyOnOff()

	def keyDown(self):
		if self["config"].getCurrentIndex() < len(self.list) - 1:
			self["config"].setCurrentIndex(self["config"].getCurrentIndex() + 1)
			self.setVkeyOnOff()

	def switchMode(self):
		if self["config"].getCurrentIndex() != 0:
			return
		config.plugins.RemoteStreamConverter.ip.value = [0, 0, 0, 0]
		config.plugins.RemoteStreamConverter.address.value = ""
		if self.isIp:
			self.createMenuAdress()
		else:
			self.createMenuIp()

	def setVkeyOnOff(self):
		if self.list[self["config"].getCurrentIndex()][2]:
			self["key_blue"].setText(_("Keyboard"))
		else:
			self["key_blue"].setText("")

		if self["config"].getCurrentIndex() == 0:
			if self.isIp:
				self["key_yellow"].setText(_("Use address"))
			else:
				self["key_yellow"].setText(_("Use IP"))
		else:
			self["key_yellow"].setText("")

	def createMenuIp(self):
		self.list = []
		self.list.append(getConfigListEntry(_("IP:"), config.plugins.RemoteStreamConverter.ip, False))
		self.list.append(getConfigListEntry(_("Username:"), config.plugins.RemoteStreamConverter.username, True))
		self.list.append(getConfigListEntry(_("Password:"), config.plugins.RemoteStreamConverter.password, True))
		self.list.append(getConfigListEntry(_("FTPport:"), config.plugins.RemoteStreamConverter.port, False))
		self.list.append(getConfigListEntry(_("Passive:"), config.plugins.RemoteStreamConverter.passive, False))
		self.list.append(getConfigListEntry(_("Telnetport:"), config.plugins.RemoteStreamConverter.telnetport, False))
		self["config"].list = self.list
		self["config"].l.setList(self.list)
		self.isIp = True
		self.setVkeyOnOff()

	def createMenuAdress(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Adress:"), config.plugins.RemoteStreamConverter.address, True))
		self.list.append(getConfigListEntry(_("Username:"), config.plugins.RemoteStreamConverter.username, True))
		self.list.append(getConfigListEntry(_("Password:"), config.plugins.RemoteStreamConverter.password, True))
		self.list.append(getConfigListEntry(_("FTPport:"), config.plugins.RemoteStreamConverter.port, False))
		self.list.append(getConfigListEntry(_("Passive:"), config.plugins.RemoteStreamConverter.passive, False))
		self.list.append(getConfigListEntry(_("Telnetport:"), config.plugins.RemoteStreamConverter.telnetport, False))
		self["config"].list = self.list
		self["config"].l.setList(self.list)
		self.isIp = False
		self.setVkeyOnOff()

	POS_ADDRESS = 0
	POS_USERNAME = 1
	POS_PASSWORD = 2

	def enterUrl(self):
		if not self.list[self["config"].getCurrentIndex()][2]:
			return
		if self["config"].getCurrentIndex() == self.POS_ADDRESS and not self.isIp:
			txt = config.plugins.RemoteStreamConverter.address.value
			head = _("Enter address")
		elif self["config"].getCurrentIndex() == self.POS_USERNAME:
			txt = config.plugins.RemoteStreamConverter.username.value
			head = _("Enter username")
		elif self["config"].getCurrentIndex() == self.POS_PASSWORD:
			txt = config.plugins.RemoteStreamConverter.password.value
			head = _("Enter password")
		self.session.openWithCallback(self.urlCallback, VirtualKeyBoard, title = head, text = txt)

	def urlCallback(self, res):
		if res is not None:
			if self["config"].getCurrentIndex() == self.POS_ADDRESS:
				config.plugins.RemoteStreamConverter.address.value = res
			elif self["config"].getCurrentIndex() == self.POS_USERNAME:
				config.plugins.RemoteStreamConverter.username.value = res
			elif self["config"].getCurrentIndex() == self.POS_PASSWORD:
				config.plugins.RemoteStreamConverter.password.value = res

	def keySave(self):
		config.plugins.RemoteStreamConverter.address.value = config.plugins.RemoteStreamConverter.address.value.strip()
		self.saveAll()
		if self.isIp:
			config.plugins.RemoteStreamConverter.address.save()
		else:
			config.plugins.RemoteStreamConverter.ip.save()
		configfile.save()
		self.close(True)

class StreamingChannelFromServerScreen(Screen):
	skin = """
		<screen name="StreamingChannelFromServerScreen" position="center,center" size="550,450" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="list" position="5,50" size="540,360" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,410" zPosition="10" size="560,2" transparent="1" alphatest="on" />
			<widget source="statusbar" render="Label" position="5,420" zPosition="10" size="550,30" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Select bouquets to convert"))
		self.session = session
		self.workList = []
		self.readIndex = 0
		self.working = False
		self.hasFiles = False
		self.list = SelectionList()
		self["list"] = self.list
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText(_("Set server IP"))
		self["key_blue"] = StaticText("")
		self["statusbar"] = StaticText(_("Select a remote server IP first"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"cancel": self.close,
			"red": self.close,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue
		}, -1)

	def keyOk(self):
		if self.working:
			return
		if self.readIndex > 0:
			self.list.toggleSelection()

	def keyBlue(self):
		if not self.hasFiles or self.working:
			return
		if self.readIndex > 0:
			try:
				self.list.toggleAllSelection()
			except AttributeError:
				self.list.toggleSelection()

	def keyYellow(self):
		if not self.hasFiles:
			self.session.openWithCallback(self.setRemoteIpCallback, ServerEditor)

	def setRemoteIpCallback(self, ret = False):
		if ret:
			self["statusbar"].setText(_("Testing remote connection"))
			timeout = 3000
			self.currentLength = 0
			self.total = 0
			self.working = True
			creator = ClientCreator(reactor, FTPClient, config.plugins.RemoteStreamConverter.username.value, config.plugins.RemoteStreamConverter.password.value, config.plugins.RemoteStreamConverter.passive.value)
			creator.connectTCP(self.getRemoteAdress(), config.plugins.RemoteStreamConverter.port.value, timeout).addCallback(self.controlConnectionMade).addErrback(self.connectionFailed)

	def controlConnectionMade(self, ftpclient):
		self["statusbar"].setText(_("Connection to remote IP ok"))
		ftpclient.quit()
		self.fetchRemoteBouqets()

	def connectionFailed(self, *args):
		self.working = False
		self["statusbar"].setText(_("Could not connect to remote IP"))

	def fetchRemoteBouqets(self):
		self["statusbar"].setText(_("Downloading remote services"))
		self.readIndex = 0
		self.workList = []
		self.workList.append('bouquets.tv')
		self.workList.append('bouquets.radio')
		self.download(self.workList[0]).addCallback(self.fetchRemoteBouqetsFinished).addErrback(self.fetchRemoteBouqetsFailed)

	def fetchRemoteBouqetsFailed(self, string):
		self.working = False
		self["statusbar"].setText(_("Download from remote failed"))

	def fetchRemoteBouqetsFinished(self, string):
		self.readIndex += 1
		if self.readIndex < len(self.workList):
			self.download(self.workList[self.readIndex]).addCallback(self.fetchRemoteBouqetsFinished).addErrback(self.fetchRemoteBouqetsFailed)
		else:
			self.parseBouqets()

	def parserWork(self, list, name):
		file = open(name)
		lines = file.readlines()
		file.close()
		if len(lines) > 0:
			for line in lines:
				if line.startswith('#SERVICE'):
					line = line.replace('\n', '').replace('\r', '').split()
					if not int(line[1].split(":")[1]) & eServiceReference.isInvisible:
						if len(line) > 3 and line[2] == 'BOUQUET' and (line[3].find('.tv') != -1 or line[3].find('.radio')):
							tmp = line[3].replace('"', '')
							if len(tmp) > 1 and tmp not in list:
								list.append(tmp)
						elif line[1].find('0:0:0:0:0:0:0:'):
							tmp = line[1].split('0:0:0:0:0:0:0:')
							if tmp[1] not in list:
								list.append(tmp[1])

	def parseBouqets(self):
		list = []
		self.parserWork(list, DIR_TMP + 'bouquets.tv')
		self.parserWork(list, DIR_TMP + 'bouquets.radio')
		self.readIndex = 0
		self.workList = []
		for listindex in range(len(list)):
			self.workList.append(list[listindex])
		self.workList.append('lamedb')
		self.download(self.workList[0]).addCallback(self.fetchUserBouquetsFinished).addErrback(self.fetchUserBouquetsFailed)

	def fetchUserBouquetsFailed(self, string):
		print "string", string
		if self.readIndex < len(self.workList) and self.readIndex > 0:
			self.workList.remove(self.workList[self.readIndex])
			self.readIndex -= 1
			self.fetchUserBouquetsFinished('')
		self.working = False
		self["statusbar"].setText(_("Download from remote failed"))

	def fetchUserBouquetsFinished(self, string):
		self.readIndex += 1
		if self.readIndex < len(self.workList):
			self["statusbar"].setText(_("FTP reading bouquets %d of %d") % (self.readIndex, len(self.workList)-1))
			self.download(self.workList[self.readIndex]).addCallback(self.fetchUserBouquetsFinished).addErrback(self.fetchUserBouquetsFailed)
		else:
			if len(self.workList) > 0:
				# Download alternatives files where services have alternatives
				self.findAlternatives()
				self.alternativesCounter = 0
				if len(self.alternatives) > 0:
					self.download(self.alternatives[self.alternativesCounter]).addCallback(self.downloadAlternativesCallback).addErrback(self.downloadAlternativesErrback)

				self["statusbar"].setText(_("Make your selection"))
				self.editBouquetNames()
				bouquetFilesContents = ''
				for suffix in ['tv', 'radio']:
					fp = open(DIR_ENIGMA2 + "bouquets." + suffix)
					bouquetFilesContents += fp.read()
					fp.close()
				for listindex in range(len(self.workList) - 1):
					truefalse = self.workList[listindex] in bouquetFilesContents
					name = self.readBouquetName(DIR_TMP + self.workList[listindex])
					self.list.addSelection(name, self.workList[listindex], listindex, truefalse)
				self.removeFiles(DIR_TMP, "bouquets.")
				self.working = False
				self.hasFiles = True
				self["key_green"].setText(_("Download"))
				self["key_blue"].setText(_("Invert"))
				self["key_yellow"].setText("")

	def download(self, file, contextFactory = None, *args, **kwargs):
		client = FTPDownloader(
			self.getRemoteAdress(),
			config.plugins.RemoteStreamConverter.port.value,
			DIR_ENIGMA2 + file,
			DIR_TMP + file,
			config.plugins.RemoteStreamConverter.username.value,
			config.plugins.RemoteStreamConverter.password.value,
			*args,
			**kwargs
		)
		return client.deferred

	def convertBouquets(self):
		self.readIndex = 0
		while True:
			if 'lamedb' not in self.workList[self.readIndex]:
				filename = DIR_TMP + self.workList[self.readIndex]
				fp = open(DIR_ENIGMA2 + self.workList[self.readIndex], 'w')
				try:
					fp2 = open(filename)
					lines = fp2.readlines()
					fp2.close()
					was_html = False
					for line in lines:
						if was_html and '#DESCRIPTION' in line:
							was_html = False
							continue
						if '#NAME' in line:
							txt = _("remote of")
							line = "%s (%s %s) \n" % (line.rstrip('\n'), txt, self.getRemoteAdress())
						was_html = False
						if 'http' in line:
							was_html = True
							continue
						elif '#SERVICE' in line:
							# alternative services that cannot be fed directly into the "play"-handler.
							if int(line.split()[1].split(":")[1]) & eServiceReference.mustDescent:
								line = self.getAlternativeLine(line)
								if line == None:
									continue
							# normal services
							line = line.strip('\r\n')
							line = line.strip('\n')
							tmp = line.split('#SERVICE')
							if '::' in tmp[1]:
								desc = tmp[1].split("::")
								if (len(desc)) == 2:
									tmp2 = tmp[1].split('::')
									service_ref = ServiceReference(tmp2[0] + ':')
									tag = tmp2[0][1:]
							else:
								tag = tmp[1][1:-1]
								service_ref = ServiceReference(tag)
							out = '#SERVICE ' + tag + ':' + quote('http://' + self.getRemoteAdress() + ':8001/' + tag) + ':' + service_ref.getServiceName() + '\n'
						else:
							out = line
						fp.write(out)
				except:
					pass
				fp.close()
			self.readIndex += 1
			if self.readIndex == len(self.workList):
				break
		self.removeFilesByPattern(DIR_TMP, "[.](tv|radio)$")

	def getTransponders(self, fp):
		step = 0
		fp2 = open(DIR_TMP + 'lamedb')
		lines = fp2.readlines()
		fp2.close()
		for line in lines:
			if step == 0:
				if 'transponders' in line:
					step =1
			elif step == 1:
				if 'end' in line[:3]:
					fp.write(line)
					break
				else:
					fp.write(line)

	def getServices(self, fp):
		step = 0
		fp2 = open(DIR_TMP + 'lamedb')
		lines = fp2.readlines()
		fp2.close()
		for line in lines:
			if step == 0:
				if 'services' in line[:8]:
					step =1
			elif step == 1:
				if 'end' in line[:3]:
					fp.write(line)
					break
				else:
					fp.write(line)

	def createBouquetFile(self, target, source, matchstr, typestr):
		tmpFile = []
		prefix = "%s%s." % (RCSC_PREFIX, self.getRemoteAdress().replace('.', '_'))
		self.removeFiles(DIR_ENIGMA2, prefix)
		fp = open(target, 'w')
		try:
			fp2 = open(source)
			lines = fp2.readlines()
			fp2.close()
			for line in lines:
				if prefix not in line:
					tmpFile.append(line)
					fp.write(line)
			for item in self.workList:
				if typestr in item:
					tmp = matchstr + item + '\" ORDER BY bouquet\n'
					match = False
					for x in tmpFile:
						if tmp in x:
							match = True
					if match is not True:
						fp.write(tmp)
			fp.close()
			self.copyFile(target, source)
		except:
			pass

	def keyGreen(self):
		if not self.hasFiles:
			return
		self.workList = []
		tmpList = []
		tmpList = self.list.getSelectionsList()
		if len(tmpList) == 0:
			self["statusbar"].setText(_("No bouquets selected"))
			return
		for item in tmpList:
			self.workList.append(item[1])
		fileValid = False
		state = 0
		fp = open(DIR_TMP + 'tmp_lamedb', 'w')
		try:
			fp2 = open(DIR_ENIGMA2 + 'lamedb')
			lines = fp2.readlines()
			fp2.close()
			for line in lines:
				if 'eDVB services' in line:
					fileValid = True
				if state == 0:
					if 'transponders' in line[:12]:
						fp.write(line)
					elif 'end' in line[:3]:
						self.getTransponders(fp)
						state = 1
					else:
						fp.write(line)
				elif state == 1:
					if 'services' in line[:8]:
						fp.write(line)
					elif 'end' in line[:3]:
						self.getServices(fp)
						state = 2
					else:
						fp.write(line)
				elif state == 2:
					fp.write(line)
		except:
			pass
		fp.close()
		if fileValid is not True:
			self.copyFile(DIR_TMP + 'lamedb', DIR_TMP + 'tmp_lamedb')
		tv = False
		radio = False
		for item in self.workList:
			if '.tv' in item:
				tv = True
			if '.radio' in item:
				radio = True
		if radio or tv:
			if tv:
				self.createBouquetFile(DIR_TMP + 'tmp_bouquets.tv', DIR_ENIGMA2 + 'bouquets.tv', '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"', '.tv')
			if radio:
				self.createBouquetFile(DIR_TMP + 'tmp_bouquets.radio', DIR_ENIGMA2 + 'bouquets.radio', '#SERVICE 1:7:2:0:0:0:0:0:0:0:FROM BOUQUET \"', '.radio')
			self.copyFile(DIR_TMP + 'tmp_lamedb', DIR_ENIGMA2 + 'lamedb')
			db = eDVBDB.getInstance()
			db.reloadServicelist()
			self.convertBouquets()
			self.removeFiles(DIR_TMP, "tmp_")
			self.removeFiles(DIR_TMP, "lamedb")
			db = eDVBDB.getInstance()
			db.reloadServicelist()
			db.reloadBouquets()
		self.close()

	def getRemoteAdress(self):
		if config.plugins.RemoteStreamConverter.address.value != "":
			return config.plugins.RemoteStreamConverter.address.value
		else:
			return '%d.%d.%d.%d' % (config.plugins.RemoteStreamConverter.ip.value[0], config.plugins.RemoteStreamConverter.ip.value[1], config.plugins.RemoteStreamConverter.ip.value[2], config.plugins.RemoteStreamConverter.ip.value[3])

	def readBouquetName(self, filename):
		try:
			fp = open(filename)
			lines = fp.readlines()
			fp.close()
			for line in lines:
				if '#NAME' in line:
					tmp = line.split('#NAME ')
					if '\r' in tmp[1]:
						bouquetname = tmp[1].split('\r\n')[0]
					else:
						bouquetname = tmp[1].split('\n')[0]
					return bouquetname
		except:
			pass
		return ""

	def readBouquetList(self, list, rootstr):
		bouquet_root = eServiceReference(rootstr)
		if not bouquet_root is None:
			serviceHandler = eServiceCenter.getInstance()
			if not serviceHandler is None:
				servicelist = serviceHandler.list(bouquet_root)
				if not servicelist is None:
					while True:
						service = servicelist.getNext()
						if not service.valid():
							break
						tmp = service.toString()
						if len(tmp) > 1 and len(tmp[1]) > 0:
							tmp2 = tmp.split()[2].replace('"','')
							name = self.readBouquetName(DIR_ENIGMA2 + tmp2)
							list.append((name, tmp2))

	def removeFiles(self, targetdir, target):
		targetLen = len(target)
		for root, dirs, files in os.walk(targetdir):
			for name in files:
				if target in name[:targetLen]:
					os.remove(os.path.join(root, name))

	def removeFilesByPattern(self, targetdir, target):
		for root, dirs, files in os.walk(targetdir):
			for name in files:
				if re.search(target, name) is not None:
					os.remove(os.path.join(root, name))

	def copyFile(self, source, dest):
		import shutil
		shutil.copy2(source, dest)

	def editBouquetNames(self):
		self.removeFiles(DIR_TMP, RCSC_PREFIX)
		tmp_workList = []
		for filename in self.workList:
			if filename.startswith(RCSC_PREFIX):
				continue
			if filename == 'lamedb':
				tmp_workList.append(filename)
			if filename.endswith('.tv') or filename.endswith('.radio'):
				newFilename = "%s%s.%s" % (RCSC_PREFIX, self.getRemoteAdress().replace('.', '_'), filename)
				os.rename(DIR_TMP + filename, DIR_TMP + newFilename)
				tmp_workList.append(newFilename)
		self.workList = tmp_workList

	def findAlternatives(self):
		self["statusbar"].setText(_("Checking for alternatives"))
		self.alternatives = []
		for filename in self.workList:
			if filename != "lamedb":
				try:
					fp = open(DIR_TMP + filename)
					lines = fp.readlines()
					fp.close()
					for line in lines:
						if '#SERVICE' in line and int(line.split()[1].split(":")[1]) & eServiceReference.mustDescent:
							if int(line.split()[1].split(":")[1]) & eServiceReference.mustDescent:
								result = re.match("^.*FROM BOUQUET \"(.+)\" ORDER BY.*$", line) or re.match("[#]SERVICE[:] (?:[0-9a-f]+[:])+([^:]+[.](?:tv|radio))$", line, re.IGNORECASE)
								if result is None:
									continue
								self.alternatives.append(result.group(1))
				except:
					pass

	def downloadAlternativesCallback(self, string):
		self.alternativesCounter += 1
		if self.alternativesCounter < len(self.alternatives):
			self["statusbar"].setText(_("FTP reading alternatives %d of %d") % (self.alternativesCounter, len(self.alternatives)-1))
			self.download(self.alternatives[self.alternativesCounter]).addCallback(self.downloadAlternativesCallback).addErrback(self.downloadAlternativesErrback)
		else:
			self["statusbar"].setText(_("Make your selection"))

	def downloadAlternativesErrback(self, string):
		print "[RCSC] error downloading alternative: '%s', error: %s" % (self.alternatives[self.alternativesCounter], string)
		self.downloadAlternativesCallback(string)

	def getAlternativeLine(self, line):
		result = re.match("^.*FROM BOUQUET \"(.+)\" ORDER BY.*$", line) or re.match("[#]SERVICE[:] (?:[0-9a-f]+[:])+([^:]+[.](?:tv|radio))$", line, re.IGNORECASE)
		if result is None:
			return None
		filename = result.group(1)
		if filename in self.alternatives:
			try:
				fp = open(DIR_TMP + filename)
				lines = fp.readlines()
				fp.close()
				for line in lines:
					if '#SERVICE' in line:
						return line
			except:
				pass
		return None

def main(session, **kwargs):
	session.open(StreamingChannelFromServerScreen)

def mainInMenu(menuid, **kwargs):
	if getImageDistro() in ('teamblue') and getBoxType() in ('gbipbox', 'gbx2'):
		if menuid == "setup":
			return [(_("Remote channel stream converter"), main, "streamconvert", 20)]
		else:
			return []
	else:
		if menuid == "scan":
			return [(_("Remote channel stream converter"), main, "streamconvert", 99)]
		else:
			return []

def Plugins(**kwargs):
	return [ PluginDescriptor(name = _("Remote channel stream converter"), description = _("Convert remote channel list for streaming"), where = PluginDescriptor.WHERE_MENU, fnc = mainInMenu) ]

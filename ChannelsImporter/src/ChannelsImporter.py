# -*- coding: UTF-8 -*-
# for localized messages
from __future__ import print_function
from __future__ import absolute_import
from . import _

import os
import re
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.error import URLError, HTTPError

from enigma import eServiceReference, eDVBDB

from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import inStandby

from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.protocols.ftp import FTPClient

from .FTPDownloader import FTPDownloader

DIR_ENIGMA2 = '/etc/enigma2/'
DIR_TMP = '/tmp/'

class ChannelsImporter(Screen):
	skin = """
	<screen position="0,0" size="1280,35" backgroundColor="transpBlack" flags="wfNoBorder" >
		<widget name="action" position="5,3" size="435,25" font="Regular;22" backgroundColor="transpBlack" borderWidth="3" borderColor="black"/>
		<widget name="status" position="465,5" size="435,25" font="Regular;22" halign="center" backgroundColor="transpBlack" borderWidth="2" borderColor="black"/>
	</screen>"""

	def __init__(self, session):
		print("[ChannelsImporter][__init__] Starting...")
		self.session = session
		Screen.__init__(self, session)
		self.skinName = ["ChannelsImporter", "AutoBouquetsMaker"]
		Screen.setTitle(self, _("Channels importer"))
		self["action"] = Label(_("Starting importer"))
		self["status"] = Label("")
		self["actions"] = ActionMap(["SetupActions"],
		{
			"cancel": self.keyCancel,
		}, -2)
		self.onFirstExecBegin.append(self.firstExec)

	def firstExec(self):
		if not inStandby:
			self["action"].setText(_('Starting importer...'))
		self.checkFTPConnection()

	def checkFTPConnection(self):
		print("[ChannelsImporter] Checking FTP connection to remote receiver")
		if not inStandby:
			self["status"].setText(_("Checking FTP connection to remote receiver"))
		timeout = 5
		self.currentLength = 0
		self.total = 0
		self.working = True
		creator = ClientCreator(reactor, FTPClient, config.plugins.ChannelsImporter.username.value, config.plugins.ChannelsImporter.password.value, config.plugins.ChannelsImporter.passive.value)
		creator.connectTCP(self.getRemoteAddress(), config.plugins.ChannelsImporter.port.value, timeout).addCallback(self.checkConnectionCallback).addErrback(self.checkConnectionErrback)

	def checkConnectionErrback(self, *args):
		print("[ChannelsImporter] Could not connect to the remote IP")
		print("[ChannelsImporter] Error messages:", args)
		self.showError(_('Could not connect to the remote IP'))

	def checkConnectionCallback(self, ftpclient):
		print("[ChannelsImporter] Connection to remote IP ok")
		if not inStandby:
			self["action"].setText(_('Connection to remote IP ok'))
			self["status"].setText("")
			ftpclient.quit()
		self.fetchRemoteBouquets()

	def fetchRemoteBouquets(self):
		print("[ChannelsImporter] Fetch bouquets.tv and bouquets.radio")
		self.readIndex = 0
		self.workList = []
		self.workList.append('bouquets.tv')
		self.workList.append('bouquets.radio')
		if not inStandby:
			self["action"].setText(_('Downloading channel indexes...'))
			self["status"].setText(_("%d/%d") % (self.readIndex + 1, len(self.workList)))
		self.download(self.workList[0]).addCallback(self.fetchRemoteBouquetsCallback).addErrback(self.fetchRemoteBouquetsErrback)

	def fetchRemoteBouquetsErrback(self, msg):
		print("[ChannelsImporter] Download from remote failed. %s" % msg)
		self.showError(_('Download from remote failed %s') % msg)

	def fetchRemoteBouquetsCallback(self, msg):
		self.readIndex += 1
		if self.readIndex < len(self.workList):
			if not inStandby:
				self["status"].setText(_("%d/%d") % (self.readIndex + 1, len(self.workList)))
			self.download(self.workList[self.readIndex]).addCallback(self.fetchRemoteBouquetsCallback).addErrback(self.fetchRemoteBouquetsErrback)
		else:
			self.readBouquets()

	def getBouquetsList(self, bouquetFilenameList, bouquetfile):
		file = open(bouquetfile)
		lines = file.readlines()
		file.close()
		if len(lines) > 0:
			for line in lines:
				result = re.match("^.*FROM BOUQUET \"(.+)\" ORDER BY.*$", line) or re.match("[#]SERVICE[:] (?:[0-9a-f]+[:])+([^:]+[.](?:tv|radio))$", line, re.IGNORECASE)
				if result is None:
					continue
				bouquetFilenameList.append(result.group(1))

	def readBouquets(self):
		bouquetFilenameList = []
		self.getBouquetsList(bouquetFilenameList, DIR_TMP + 'bouquets.tv')
		self.getBouquetsList(bouquetFilenameList, DIR_TMP + 'bouquets.radio')
		self.readIndex = 0
		self.workList = []
		for listindex in range(len(bouquetFilenameList)):
			self.workList.append(bouquetFilenameList[listindex])
		self.workList.append('lamedb')
		if not inStandby:
			self["action"].setText(_('Downloading bouquets...'))
			self["status"].setText(_("%d/%d") % (self.readIndex + 1, len(self.workList)))
		self.download(self.workList[0]).addCallback(self.readBouquetsCallback).addErrback(self.readBouquetsErrback)

	def readBouquetsErrback(self, msg):
		print("[ChannelsImporter] Download from remote failed. %s" % msg)
		self.showError(_('Download from remote failed %s') % msg)

	def readBouquetsCallback(self, msg):
		self.readIndex += 1
		if self.readIndex < len(self.workList):
			if not inStandby:
				self["status"].setText(_("%d/%d") % (self.readIndex + 1, len(self.workList)))
			self.download(self.workList[self.readIndex]).addCallback(self.readBouquetsCallback).addErrback(self.readBouquetsErrback)
		elif len(self.workList) > 0:
			# Download alternatives files where services have alternatives
			self["action"].setText(_('Checking for alternatives...'))
			self["status"].setText("")
			self.findAlternatives()
			self.alternativesCounter = 0
			if len(self.alternatives) > 0:
				if not inStandby:
					self["action"].setText(_('Downloading alternatives...'))
					self["status"].setText(_("%d/%d") % (self.alternativesCounter + 1, len(self.alternatives)))
				self.download(self.alternatives[self.alternativesCounter]).addCallback(self.downloadAlternativesCallback).addErrback(self.downloadAlternativesErrback)
			self.processFiles()
		else:
			print("[ChannelsImporter] There were no remote bouquets to download")
			self.showError(_('Download from remote failed %s'))

	def downloadAlternativesErrback(self, msg):
		print("[ChannelsImporter] Download from remote failed. %s" % msg)
		self.showError(_('Download from remote failed %s') % msg)

	def downloadAlternativesCallback(self, msg):
		self.alternativesCounter += 1
		if self.alternativesCounter < len(self.alternatives):
			if not inStandby:
				self["status"].setText(_("%d/%d") % (self.alternativesCounter + 1, len(self.alternatives)))
			self.download(self.alternatives[self.alternativesCounter]).addCallback(self.downloadAlternativesCallback).addErrback(self.downloadAlternativesErrback)

	def processFiles(self):
		allFiles = self.workList + self.alternatives + ["bouquets.tv", "bouquets.radio"]
		if not inStandby:
			self["action"].setText(_('Removing current channel list...'))
			self["status"].setText("")
		print("[ChannelsImporter] Removing current channel list...")
		for target in ["lamedb", "bouquets.", "userbouquet."]:
			self.removeFiles(DIR_ENIGMA2, target)
		print("[ChannelsImporter] Loading new channel list...")
		if not inStandby:
			self["action"].setText(_('Loading new channel list...'))
		for filename in allFiles:
			self.copyFile(DIR_TMP + filename, DIR_ENIGMA2 + filename)
			self.removeFiles(DIR_TMP, filename)
		db = eDVBDB.getInstance()
		db.reloadServicelist()
		db.reloadBouquets()
		print("[ChannelsImporter] New channel list loaded.")
		self.checkEPG()

	def checkEPG(self):
		if config.plugins.ChannelsImporter.importEPG.value:
			if not inStandby:
				self["action"].setText(_('Force EPG save on remote receiver'))
				self["status"].setText("")
			
			self.forceSaveEPGonRemoteReceiver()
			print("[ChannelsImporter] Searching for epg.dat...")
			if not inStandby:
				self["action"].setText(_('Searching for epg.dat'))
				self["status"].setText("")
			self.download("settings").addCallback(self.checkEPGCallback).addErrback(self.checkEPGErrback)
		else:
			self.close(True)

	def checkEPGErrback(self, msg):
		print("[ChannelsImporter] Download settings from remote failed. %s" % msg)
		self.showError(_('Download settings from remote failed %s') % msg)

	def checkEPGCallback(self, msg):
		file = open(DIR_TMP + "settings")
		lines = file.readlines()
		file.close()
		self.remoteEPGpath = DIR_ENIGMA2
		self.remoteEPGfile = "epg"
		for line in lines:
			if "config.misc.epgcachepath" in line:
				self.remoteEPGpath = line.strip().split("=")[1]
			if "config.misc.epgcachefilename" in line:
				self.remoteEPGfile = line.strip().split("=")[1]
		self.remoteEPGfilename = "%s%s.dat" % (self.remoteEPGpath, self.remoteEPGfile.replace('.dat', ''))
		print("[ChannelsImporter] Remote EPG filename. '%s'" % self.remoteEPGfilename)
		self.removeFiles(DIR_TMP, "settings")
		self.download2(self.remoteEPGfilename, "epg.dat").addCallback(self.importEPGCallback).addErrback(self.importEPGErrback)

	def importEPGErrback(self, msg):
		print("[ChannelsImporter] Download epg.dat from remote receiver failed. Check file exists on remote receiver.\n%s" % msg)
		self["action"].setText(_('epg.dat not found'))
		self.showError(_('Download epg.dat from remote receiver failed. Check file exists on remote receiver.\n%s') % msg)

	def importEPGCallback(self, msg):
		print("[ChannelsImporter] '%s' downloaded successfully. " % self.remoteEPGfilename)
		print("[ChannelsImporter] Removing current EPG data...")
		self["action"].setText(_('Loading epg.dat...'))
		try:
			os.remove(config.misc.epgcache_filename.value)
		except OSError:
			pass
		self.copyFile(DIR_TMP + "epg.dat", config.misc.epgcache_filename.value)
		self.removeFiles(DIR_TMP, "epg.dat")
		from enigma import eEPGCache
		epgcache = eEPGCache.getInstance()
		epgcache.load()
		print("[ChannelsImporter] New EPG data loaded...")
		print("[ChannelsImporter] Closing importer.")
		self.close(True)

	def findAlternatives(self):
		print("[ChannelsImporter] Checking for alternatives")
		self.alternatives = []
		for filename in self.workList:
			if filename != "lamedb":
				try:
					fp = open(DIR_TMP + filename)
					lines = fp.readlines()
					fp.close()
					for line in lines:
						if '#SERVICE' in line and int(line.split()[1].split(":")[1]) & eServiceReference.mustDescent:
							result = re.match("^.*FROM BOUQUET \"(.+)\" ORDER BY.*$", line) or re.match("[#]SERVICE[:] (?:[0-9a-f]+[:])+([^:]+[.](?:tv|radio))$", line, re.IGNORECASE)
							if result is None:
								continue
							self.alternatives.append(result.group(1))
				except:
					pass

	def showError(self, message):
		if not inStandby and config.plugins.ChannelsImporter.errorMessages.value:
			mbox = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
			mbox.setTitle(_("Channels importer"))
		self.close()

	def keyCancel(self):
		self.close()

	def removeFiles(self, targetdir, target):
		targetLen = len(target)
		for root, dirs, files in os.walk(targetdir):
			for name in files:
				if target in name[:targetLen]:
					os.remove(os.path.join(root, name))

	def copyFile(self, source, dest):
		import shutil
		shutil.copy2(source, dest)

	def getRemoteAddress(self):
		return '%d.%d.%d.%d' % (config.plugins.ChannelsImporter.ip.value[0], config.plugins.ChannelsImporter.ip.value[1], config.plugins.ChannelsImporter.ip.value[2], config.plugins.ChannelsImporter.ip.value[3])

	def download(self, file, contextFactory = None, *args, **kwargs):
		print("[ChannelsImporter] Downloading remote file '%s'" % file)
		client = FTPDownloader(
			self.getRemoteAddress(),
			config.plugins.ChannelsImporter.port.value,
			DIR_ENIGMA2 + file,
			DIR_TMP + file,
			config.plugins.ChannelsImporter.username.value,
			config.plugins.ChannelsImporter.password.value,
			*args,
			**kwargs
		)
		return client.deferred

	def download2(self, sourcefile, destfile, contextFactory = None, *args, **kwargs):
		print("[ChannelsImporter] Downloading remote file '%s'" % sourcefile)
		client = FTPDownloader(
			self.getRemoteAddress(),
			config.plugins.ChannelsImporter.port.value,
			sourcefile,
			DIR_TMP + destfile,
			config.plugins.ChannelsImporter.username.value,
			config.plugins.ChannelsImporter.password.value,
			*args,
			**kwargs
		)
		return client.deferred

	def forceSaveEPGonRemoteReceiver(self):
		url = "http://%s/api/saveepg" % self.getRemoteAddress()
		print('[ChannelsImporter][saveEPGonRemoteReceiver] URL: %s' % url)
		try:
			req = Request(url)
			response = urlopen(req)
			print('[ChannelsImporter][saveEPGonRemoteReceiver] Response: %d, %s' % (response.getcode(), response.read().strip().replace("\r", "").replace("\n", "")))
		except HTTPError as err:
			print('[ChannelsImporter][saveEPGonRemoteReceiver] ERROR:', err)
		except URLError as err:
			print('[ChannelsImporter][saveEPGonRemoteReceiver] ERROR:', err.reason[0])
		#except urllib2 as err:
		#	print('[ChannelsImporter][saveEPGonRemoteReceiver] ERROR:', err)
		except:
			print('[ChannelsImporter][saveEPGonRemoteReceiver] undefined error')

from os import makedirs
from os.path import isdir, isfile, basename
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config, configfile, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from . import _, printToConsole, getPiconsPath, getPiconsTypeValue, getCurrentPicon, getConfigSizeList, getConfigBackgroundList, getBackgroundList, getPiconUrls, BOUQUET_PATH, TMP_PICON_PATH, TMP_BG_PATH, TMP_FG_PATH, TMP_PREVIEW_IMAGE_PATH, PREVIEW_IMAGE_PATH
from .DiskUtils import pathIsWriteable
from .JobProgressView import JobProgressView
from .DownloadPicons import DownloadPicons, DOWNLOAD_ALL_FINISHED, DOWNLOAD_FINISHED
from .DownloadJob import DownloadJob
from .EventDispatcher import addEventListener, removeEventListener
from .Picon import MergePiconJob, OptimizePiconsFileSize, OPTIMIZE_PICONS_FINISHED, MERGE_PICONS_FINISHED
from .BouquetParser import BouquetParser


class PiconsUpdaterView(ConfigListScreen, Screen):
	skin = """
	<screen name="PiconsUpdater-Setup" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#90000000">
	<eLabel name="new eLabel" position="40,40" zPosition="-2" size="1200,640" backgroundColor="#20000000" transparent="0" />
	<eLabel font="Regular; 20" foregroundColor="unffffff" backgroundColor="#20000000" halign="left" position="77,645" size="250,33" text="Cancel" transparent="1" />
	<eLabel font="Regular; 20" foregroundColor="unffffff" backgroundColor="#20000000" halign="left" position="375,645" size="250,33" text="Save" transparent="1" />
	<eLabel font="Regular; 20" foregroundColor="unffffff" backgroundColor="#20000000" halign="left" position="682,645" size="250,33" text="Download Picons" transparent="1" />
	<widget name="config" position="61,114" size="590,500" scrollbarMode="showOnDemand" transparent="1" />
	<eLabel position="60,55" size="348,50" text="PiconsUpdater" font="Regular; 40" valign="center" transparent="1" backgroundColor="#20000000" />
	<eLabel position="400,58" size="349,50" text="Setup" foregroundColor="unffffff" font="Regular; 30" valign="center" backgroundColor="#20000000" transparent="1" halign="left" />
	<eLabel position="60,640" size="5,40" backgroundColor="#e61700" />
	<eLabel position="360,640" size="5,40" backgroundColor="#61e500" />
	<eLabel position="665,640" size="5,40" backgroundColor="#e5dd00" />
	<widget name="backgroundImage" position="719,210" size="500,300" zPosition="1" alphatest="blend" transparent="1" backgroundColor="transparent"/>
	<widget name="previewImage" position="744,225" size="450,270" zPosition="1" alphatest="blend" transparent="1" backgroundColor="transparent"/>
	<widget name="foregroundImage" position="719,210" size="500,300" zPosition="1" alphatest="blend" transparent="1" backgroundColor="transparent"/>
	<eLabel text="coded by svox, idea by arn354" position="692,70" size="540,25" zPosition="1" font="Regular; 15" halign="right" valign="top" backgroundColor="#20000000" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		getPiconsPath().addNotifier(self.__checkReadWriteDir, initial_call=False, immediate_feedback=False)
		self['previewImage'] = Pixmap()
		self['backgroundImage'] = Pixmap()
		self['foregroundImage'] = Pixmap()
		self.onClose.append(self.clean)
		self['actions'] = ActionMap(['OkCancelActions', 'ShortcutActions'], {'cancel': self.cancel,
		 'ok': self.okClicked,
		 'green': self.save,
		 'yellow': self.startDownloadPicons,
		 'red': self.cancel}, -1)
		self.onChangedEntry = []
		ConfigListScreen.__init__(self, self.getMenuItemList(), session, self.__selectionChanged)
		# FIXME : don't scan channels on start without background thread
		parser = BouquetParser(BOUQUET_PATH)
		self.serviceList = parser.getServiceList()
		self.previewImagesToDownload = len(getPiconUrls().items())
		self.previewImageDownloadCount = 0
		self.backgroundImagesToDownload = len(getBackgroundList())
		self.foregroundImagesToDownload = len(getBackgroundList())
		self.backgroundImageDownloadCount = 0
		self.foregroundImageDownloadCount = 0
		self.onLayoutFinish.append(self.layoutFinished)

	def __del__(self):
		print('######## DESTRUCTOR: PiconsUpdaterView')

	def getMenuItemList(self):
		menuList = []
		piconsUrls = {}
		try:
			piconsUrls = getCurrentPicon()
		except Exception as e:
			print(e)
		try:
			if piconsUrls['size'] is not None:
				sizeChoices = getConfigSizeList()
				config.plugins.PiconsUpdater.size.setChoices(sizeChoices, sizeChoices[0][0])
				menuList.append(getConfigListEntry(_('Size'), config.plugins.PiconsUpdater.size, _('Picons size')))
		except Exception as e:
			print(e)
		try:
			if piconsUrls['backgrounds'] is not None:
				backgroundChoices = getConfigBackgroundList()
				config.plugins.PiconsUpdater.background.setChoices(backgroundChoices, backgroundChoices[0][0])
				menuList.append(getConfigListEntry(_('Picon Style'), config.plugins.PiconsUpdater.background, _('Picons background/foreground image'), 'BACKGROUND'))
				self['backgroundImage'].visible = True
			else:
				self['backgroundImage'].visible = False
		except Exception as e:
			print(e)
		menuList.append(getConfigListEntry(_('Mirror Effect'), config.plugins.PiconsUpdater.mirror_effect, _('Mirror Effect')))
		menuList.append(getConfigListEntry(_('Picons Folder'), getPiconsPath(), _("Picons folder\n\nPress 'Ok' to open path selection view")))
		menuList.append(getConfigListEntry(_('Exclude IPTV'), config.plugins.PiconsUpdater.exclude_iptv, _("Exclude IPTV")))
		menuList.append(getConfigListEntry(_('Exclude Radio'), config.plugins.PiconsUpdater.exclude_radio, _("Exclude Radio")))
		return menuList

	def downloadPreviewImages(self):
		"""
		download all preview images to /tmp folder
		"""
		if isdir(TMP_PREVIEW_IMAGE_PATH) is False:
			makedirs(TMP_PREVIEW_IMAGE_PATH, 493)
		for key, piconStyleData in getPiconUrls().items():
			localPreviewPath = TMP_PREVIEW_IMAGE_PATH + '/' + key + '.png'
			if isfile(localPreviewPath) is False:
				DownloadJob(piconStyleData['previewImage'], localPreviewPath, self.__previewDownloadFinished, self.__previewDownloadFailed)
			else:
				self.__previewDownloadFinished()

	def downloadBackgroundImages(self):
		"""
		download all background and foreground images to /tmp folder
		"""
		if isdir(TMP_BG_PATH) is False:
			makedirs(TMP_BG_PATH, 493)
		if isdir(TMP_FG_PATH) is False:
			makedirs(TMP_FG_PATH, 493)
		for data in getBackgroundList():
			localPiconBgPath = TMP_BG_PATH + '/' + basename(data['bg'])
			if isfile(localPiconBgPath) is False:
				DownloadJob(data['bg'], localPiconBgPath, self.__bgDownloadFinished, self.__bgDownloadFailed)
			else:
				self.__bgDownloadFinished()
			if 'fg' in data:
				localPiconFgPath = TMP_FG_PATH + '/' + basename(data['fg'])
				if isfile(localPiconFgPath) is False:
					DownloadJob(data['fg'], localPiconFgPath, self.__fgDownloadFinished, self.__fgDownloadFailed)
				else:
					self.__fgDownloadFinished()
			else:
				self.__fgDownloadFinished()
		self.__checkDownloadDecorateImagesFinished()

	def getCurrentBackgroundList(self):
		return getCurrentPicon()['backgrounds']

	def getCurrentBackground(self):
		backgroundType = config.plugins.PiconsUpdater.background.getValue()
		backgroundList = self.getCurrentBackgroundList()
		if backgroundList is not None:
			for background in backgroundList:
				if background['key'] == backgroundType:
					return background

	def getCurrentPiconUrl(self):
		piconUrls = {}
		try:
			piconUrls = getCurrentPicon()['logo']
			return piconUrls
		except Exception:
			return None

	def getCurrentPiconNameType(self):
		try:
			piconType = getCurrentPicon()['nameType']
			return piconType
		except Exception:
			return None

	def getCurrentSize(self):
		sizeValue = config.plugins.PiconsUpdater.size.getValue()
		return tuple((int(i) for i in sizeValue.split('x')))

	def layoutFinished(self):
		self.setWindowTitle()
		self.downloadPreviewImages()
		self.downloadBackgroundImages()

	def setWindowTitle(self):
		self.setTitle(_('Choose Picons'))

	def getPreviewImagePath(self):
		try:
			previewImagePath = TMP_PREVIEW_IMAGE_PATH + '/' + getPiconsTypeValue() + '.png'
			if isfile(previewImagePath) is False:
				raise
			return previewImagePath
		except Exception:
			return PREVIEW_IMAGE_PATH

	def showPreviewPicture(self):
		self['previewImage'].instance.setPixmapFromFile(self.getPreviewImagePath())
		self['previewImage'].instance.setScale(1)

	def getBackgroundImagePath(self):
		background = self.getCurrentBackground()
		if background:
			backgroundUrl = background['bg']
			localPiconBgPath = '%s/%s' % (TMP_BG_PATH, basename(backgroundUrl))
			return localPiconBgPath
		else:
			return None

	def getForegroundImagePath(self):
		background = self.getCurrentBackground()
		if background and 'fg' in background:
			foregroundUrl = background['fg']
			localPiconFgPath = '%s/%s' % (TMP_FG_PATH, basename(foregroundUrl))
			return localPiconFgPath
		else:
			return None

	def showBackgroundPicture(self):
		if self.getCurrentBackgroundList() is not None:
			self['backgroundImage'].instance.setPixmapFromFile(self.getBackgroundImagePath())
			self['backgroundImage'].instance.setScale(1)

	def showForegroundPicture(self):
		if self.getCurrentBackgroundList() is not None and self.getForegroundImagePath() is not None:
			self['foregroundImage'].instance.setPixmapFromFile(self.getForegroundImagePath())
			self['foregroundImage'].instance.setScale(1)
			self['foregroundImage'].visible = True
		else:
			self['foregroundImage'].visible = False

	def startDownloadPicons(self):
		try:
			if isdir(getPiconsPath().getValue()) == False:
				makedirs(getPiconsPath().getValue(), 493)
		except Exception:
			pass

		if self.__checkReadWriteDir(getPiconsPath()) == False:
			return
		bgimagepath = self.getBackgroundImagePath()
		if bgimagepath and self.getCurrentBackgroundList() is not None and isfile(bgimagepath) is False:
			self.session.open(MessageBox, _('Background Image not downloaded yet, please wait some seconds and try again.'), type=MessageBox.TYPE_INFO)
			return
		addEventListener(DOWNLOAD_ALL_FINISHED, self.__downloadAllFinished)
		self.session.open(JobProgressView, 'Download Progress', msgBoxID='startDownload')
		self.totalDownloads = 1
		piconUrl = self.getCurrentPiconUrl()
		if piconUrl is not None:
			addEventListener(DOWNLOAD_FINISHED, self.__downloadFinished)
			tmpPiconsPath = TMP_PICON_PATH + '/' + getPiconsTypeValue()
			if isdir(tmpPiconsPath) is False:
				makedirs(tmpPiconsPath, 493)
			downloadPicons = DownloadPicons(self.serviceList, piconUrl, tmpPiconsPath, self.getCurrentPiconNameType())
			self.totalDownloads = downloadPicons.totalDownloads

	def okClicked(self):
		cur = self.getCurrent()
		if cur == getPiconsPath():
			self.__chooseDestination()
		else:
			ConfigListScreen.keyOK(self)

	def cancel(self):
		for x in self['config'].list:
			if len(x) > 1:
				x[1].cancel()

		self.close()

	def save(self):
		# FIXME : rescan channels if needed
		for x in self['config'].list:
			if len(x) > 1:
				x[1].save_forced = True
				x[1].save()

		configfile.save()
		self.close()

	def clean(self):
		if hasattr(self, 'timer') and self.timer:
			self.timer.stop()
			self.timer = None
		removeEventListener(DOWNLOAD_FINISHED, self.__downloadFinished)
		removeEventListener(DOWNLOAD_ALL_FINISHED, self.__downloadAllFinished)
		removeEventListener(MERGE_PICONS_FINISHED, self.processFinished)
		removeEventListener(OPTIMIZE_PICONS_FINISHED, self.__optimizePiconsFinished)
		getPiconsPath().clearNotifiers()

	def getCurrent(self):
		cur = self['config'].getCurrent()
		cur = cur and cur[1]
		return cur

	def __pathSelected(self, res):
		if res is not None:
			pathInput = self.getCurrent()
			pathInput.setValue(res)

	def __chooseDestination(self):
		from Screens.LocationBox import LocationBox
		self.session.openWithCallback(self.__pathSelected, LocationBox, _('Choose folder'), minFree=100)

	def __setPreviewImageDownloadFinished(self):
		self.previewImageDownloadCount += 1
		if self.previewImageDownloadCount is self.previewImagesToDownload:
			self.showPreviewPicture()

	def __setBackgroundImageDownloadFinished(self):
		self.backgroundImageDownloadCount += 1
		self.__checkDownloadDecorateImagesFinished()

	def __setForegroundImageDownloadFinished(self):
		self.foregroundImageDownloadCount += 1
		self.__checkDownloadDecorateImagesFinished()

	def __checkDownloadDecorateImagesFinished(self):
		if self.backgroundImageDownloadCount is self.backgroundImagesToDownload and self.foregroundImageDownloadCount is self.foregroundImagesToDownload:
			self.showBackgroundPicture()
			self.showForegroundPicture()

	def __checkReadWriteDir(self, configElement):
		if pathIsWriteable(configElement.getValue()):
			configElement.lastValue = configElement.getValue()
			return True
		else:
			dirName = configElement.getValue()
			configElement.value = configElement.lastValue
			self.__showPathIsNotWriteableWarning(dirName)
			return False

	def __showPathIsNotWriteableWarning(self, dirName):
		self.session.open(MessageBox, _('The directory %s is not writable.\nMake sure you select a writable directory instead.') % dirName, MessageBox.TYPE_ERROR)

	def __selectionChanged(self):
		cur = self['config'].getCurrent()
		cur = cur and len(cur) > 3 and cur[3]
		if cur == 'TYPE':
			self['config'].setList(self.getMenuItemList())
			self.showPreviewPicture()
		elif cur == 'BACKGROUND':
			self.showBackgroundPicture()
			self.showForegroundPicture()

	def __previewDownloadFinished(self, downloadJob=None):
		self.__setPreviewImageDownloadFinished()

	def __previewDownloadFailed(self, downloadJob):
		self.__setPreviewImageDownloadFinished()
		printToConsole("[ERROR] Download Failed: '%s'" % downloadJob.errorMessage)

	def __bgDownloadFinished(self, downloadJob=None):
		if downloadJob is not None:
			printToConsole("Background Download finished for url '%s'" % downloadJob.downloadUrl)
		self.__setBackgroundImageDownloadFinished()

	def __bgDownloadFailed(self, downloadJob):
		printToConsole("Background Download failed for url '%s'" % downloadJob.downloadUrl)
		self.__setBackgroundImageDownloadFinished()

	def __fgDownloadFinished(self, downloadJob=None):
		if downloadJob is not None:
			printToConsole("Foreground Download finished for url '%s'" % downloadJob.downloadUrl)
		self.__setForegroundImageDownloadFinished()

	def __fgDownloadFailed(self, downloadJob):
		printToConsole("Foreground Download failed for url '%s'" % downloadJob.downloadUrl)
		self.__setForegroundImageDownloadFinished()

	def __downloadFinished(self, downloadsFinished):
		progress = int(100 * (float(downloadsFinished) / float(self.totalDownloads)))
		self.session.current_dialog.setProgress(progress, _('Downloading %d of %d Picons') % (downloadsFinished, self.totalDownloads))

	def __downloadAllFinished(self, downloadPicons):
		removeEventListener(DOWNLOAD_FINISHED, self.__downloadFinished)
		removeEventListener(DOWNLOAD_ALL_FINISHED, self.__downloadAllFinished)
		printToConsole('Picons downloads finished!')
		piconsNotFoundMessage = "Picons not found for '%s' channels" % len(downloadPicons.channelsNotFoundList)
		channelsNotFoundFile = open(TMP_PICON_PATH + '/channelsNotFoundList.txt', 'w')
		channelsNotFoundFile.write(piconsNotFoundMessage + '\n\n')
		for channel in downloadPicons.channelsNotFoundList:
			channelsNotFoundFile.write(basename(channel[1]) + ';' + channel[0] + ';' + channel[1] + '\n')

		channelsNotFoundFile.close()
		self.finishedMessage = _('Process Finished.\n%s Picons downloaded\n%s Picons not found') % (str(downloadPicons.downloadsFinished), str(downloadPicons.downloadsFailed))
		printToConsole(self.finishedMessage)
		self.session.current_dialog.callback = self.__mergePicons
		self.session.current_dialog.close(True)

	def __mergePicons(self, *args):
		addEventListener(MERGE_PICONS_FINISHED, self.processFinished)
		background = self.getCurrentBackground()
		if background:
			factor = background['factor']
			MergePiconJob(self.session, self.serviceList, self.getBackgroundImagePath(), self.getForegroundImagePath(), factor, self.getCurrentSize())

	def processFinished(self, *args):
		printToConsole('merge finished')
		removeEventListener(MERGE_PICONS_FINISHED, self.processFinished)
		self.session.current_dialog.callback = self.showOptimizeFileSizeMessage
		self.session.current_dialog.close(True)

	def showOptimizeFileSizeMessage(self, *args):
		self.session.openWithCallback(self.__optimizeFileSizeWindowCallback, MessageBox, _('Optimize Picons file size?\n\nBe aware, this function is maybe very slow and reduces the quality!!'), MessageBox.TYPE_YESNO, default=False)

	def __optimizeFileSizeWindowCallback(self, result):
		if result:
			addEventListener(OPTIMIZE_PICONS_FINISHED, self.__optimizePiconsFinished)
			OptimizePiconsFileSize(self.session)
		else:
			self.showFinishedMessage()

	def __optimizePiconsFinished(self):
		removeEventListener(OPTIMIZE_PICONS_FINISHED, self.__optimizePiconsFinished)
		self.session.current_dialog.callback = self.showFinishedMessage
		self.session.current_dialog.close(True)

	def showFinishedMessage(self, *args):
		self.session.open(MessageBox, self.finishedMessage, type=MessageBox.TYPE_INFO, timeout=10)
		print(' ')
		printToConsole('Finished!')
		print(' ')

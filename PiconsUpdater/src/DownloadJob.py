from os import path
from requests import get, exceptions
from urllib.parse import quote
from twisted.internet.reactor import callInThread
from . import printToConsole


class download:
	def __init__(self, url, outputfile):
		self.url = url
		self.file = outputfile

	def start(self, success, fail=None):
		return callInThread(self.downloadPage, self.url, self.file, success, fail)

	def stop(self):
		return

	def downloadPage(self, link, file, success, fail=None):
		link = quote(link.strip(), safe=':/%')
		try:
			response = get(link, timeout=(3.05, 6))
			content = response.content
			response.raise_for_status()
			with open(file, "wb") as f:
				f.write(content)
			success(file)
		except exceptions.RequestException as err:
			if fail is not None:
				printToConsole("Error in module 'downloadPage': %s" % err)
				fail(err)


class DownloadJob:
	def __init__(self, downloadUrl, targetFileName, callbackFinished=None, callbackFailed=None, override=False):
		self.downloadUrl = downloadUrl
		self.targetFileName = targetFileName
		self.callbackFinished = callbackFinished
		self.callbackFailed = callbackFailed
		self.download = None
		if override is False and path.isfile(self.targetFileName) is True:
			callInThread(self.__downloadFromCache)
		else:
			self.run()

	def __del__(self):
		self.clean()

	def clean(self):
		try:
			del self.callbackFinished
		except:
			pass

		try:
			del self.callbackFailed
		except:
			pass

	def run(self):
		self.download = download(self.downloadUrl, self.targetFileName)
		self.download.start(self.__downloadFinished, self.__downloadFailed)

	def __downloadFromCache(self):
		printToConsole("file '%s' already exists." % self.targetFileName)
		self.__downloadFinished()

	def __downloadFinished(self, string=''):
		if self.callbackFinished is not None:
			callback = self.callbackFinished
			self.clean()
			callback(self)
		if self.download:
			self.download.stop()
			self.download = None

	def __downloadFailed(self, errorMessage=''):
		self.errorMessage = errorMessage
		"""
		# if errorMessage == '' and failureInstance is not None:
			# self.errorMessage = failureInstance.getErrorMessage()
		# self.errorMessage = self.downloadUrl + ' - ' + self.errorMessage
		"""
		if self.callbackFailed is not None:
			callback = self.callbackFailed
			self.clean()
			callback(self)
		if self.download:
			self.download.stop()
		self.download = None

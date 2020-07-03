# -*- coding: utf-8 -*-
import os
import six
from six.moves.urllib.parse import urlparse
from threading import Thread
from twisted.web import client
from twisted.web.client import HTTPDownloader
from twisted.internet import reactor, ssl
from . import _, printToConsole


class download:
    def __init__(self, url, outputfile):
        self.url = six.ensure_binary(url)
        self.file = outputfile

    def start(self):
        return client.downloadPage(self.url, self.file)

    def stop(self):
        return


class DownloadJob:

    def __init__(self, downloadUrl, targetFileName, callbackFinished = None, callbackFailed = None, override = False):
        self.downloadUrl = downloadUrl
        self.targetFileName = targetFileName
        self.callbackFinished = callbackFinished
        self.callbackFailed = callbackFailed
        self.download = None
        if override == False and os.path.isfile(self.targetFileName) is True:
            t = Thread(target=self.__downloadFromCache)
            t.start()
        else:
            self.run()

    def __del__(self):
        self.clean()

    def clean(self):
        try:
            del self.callbackFailed
            del self.callbackFinished
        except:
            pass

    def run(self):
        self.download = download(self.downloadUrl, self.targetFileName)
        self.download.start().addCallback(self.__downloadFinished).addErrback(self.__downloadFailed)

    def __downloadFromCache(self):
        printToConsole("file '%s' already exists." % self.targetFileName)
        self.__downloadFinished()

    def __downloadFinished(self, string = ''):
        if self.callbackFinished is not None:
            callback = self.callbackFinished
            self.clean()
            callback(self)
        if self.download:
            self.download.stop()
            self.download = None

    def __downloadFailed(self, failureInstance = None, errorMessage = ''):
        self.errorMessage = errorMessage
        if errorMessage == '' and failureInstance is not None:
            self.errorMessage = failureInstance.getErrorMessage()
        self.errorMessage = self.downloadUrl + ' - ' + self.errorMessage
        if self.callbackFailed is not None:
            callback = self.callbackFailed
            self.clean()
            callback(self)
        self.download.stop()
        self.download = None
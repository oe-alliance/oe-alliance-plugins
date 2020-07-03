# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
import os
from _collections import deque
from subprocess import call
from threading import Thread
from PIL import Image
from .reflection import add_reflection
from Components.config import config
from .BouquetParser import getChannelKey
from .DiskUtils import getFiles
from .EventDispatcher import dispatchEvent
from .JobProgressView import JobProgressView
from . import _, printToConsole, getPiconsPath, getTmpLocalPicon
MERGE_PICONS_FINISHED = 'mergePiconsFinished'
OPTIMIZE_PICONS_FINISHED = 'optimizePiconsFinished'

class MergeVO:

    def __init__(self, channelPicon, targetPicon):
        self.channelPicon = channelPicon
        self.targetPicon = targetPicon


class MergePiconJob:

    def __init__(self, session, serviceList, bgPath, fgPath, factor, size):
        self.session = session
        self.session.open(JobProgressView, _('Merge Picons'), msgBoxID='mergePicons')
        self.serviceList = serviceList
        self.bgPath = bgPath
        self.fgPath = fgPath
        self.targetPicon = getPiconsPath().getValue() + '/%s.png'
        self.factor = factor
        self.size = size
        self.executionQueueList = deque()
        for service in self.serviceList:
            piconName = getChannelKey(service)
            piconFile = getTmpLocalPicon(piconName)
            if os.path.isfile(piconFile):
                job = MergeVO(piconFile, self.targetPicon % piconName)
                self.executionQueueList.append(job)

        self.mergePiconsTotal = len(self.executionQueueList)
        self.mergePiconsCount = 0
        self.execQueue()

    def __del__(self):
        del self.session

    def execQueue(self):
        try:
            if len(self.executionQueueList) > 0:
                self.mergePiconsCount += 1
                progress = int(100 * (float(self.mergePiconsCount) / float(self.mergePiconsTotal)))
                self.session.current_dialog.setProgress(progress, _('Merge %d of %d Picons') % (self.mergePiconsCount, self.mergePiconsTotal))
                mergeData = self.executionQueueList.popleft()
                t = Thread(target=self.mergePicon, args=(mergeData.channelPicon, mergeData.targetPicon))
                t.start()
        except Exception as e:
            self.__clearExecutionQueueList()
            printToConsole('MergePicon execQueue exception:\n' + str(e))

    def __clearExecutionQueueList(self):
        self.executionQueueList = deque()

    def __runFinished(self):
        try:
            if len(self.executionQueueList) > 0:
                self.execQueue()
            else:
                printToConsole('MergePicon Queue finished!')
                dispatchEvent(MERGE_PICONS_FINISHED)
        except Exception as e:
            self.__clearExecutionQueueList()
            printToConsole('MergePicon runFinished exception:\n' + str(e))

    def mergePicon(self, channelPicon, targetPicon):
        try:
            background = Image.open(self.bgPath)
        except Exception:
            printToConsole("Error: Background '%s' is corrupted!" % self.bgPath)
            return

        try:
            picon = Image.open(channelPicon)
        except Exception:
            printToConsole("Error: Picon '%s' is corrupted!" % channelPicon)
            return

        backgroundWidth, backgroundHeight = background.size
        piconWidth, piconHeight = picon.size
        scaleWidth = int(piconWidth * self.factor)
        scaleHeight = int(piconHeight * self.factor)
        picon = picon.resize((scaleWidth, scaleHeight), Image.ANTIALIAS)
        centerPoint = ((backgroundWidth - scaleWidth) // 2, (backgroundHeight - scaleHeight) // 2)
        if config.plugins.PiconsUpdater.mirror_effect.getValue():
            picon = add_reflection(picon)
        try:
            background.paste(picon, centerPoint, picon)
            if self.fgPath is not None:
                foreground = Image.open(self.fgPath)
                background.paste(foreground, None, foreground)
        except Exception as e:
            printToConsole("Error: ChannelPicon: %s '%s'" % (str(e), channelPicon))
            return

        if piconWidth != self.size[0] or piconHeight != self.size[1]:
            background.thumbnail(self.size, Image.ANTIALIAS)
        else:
            background.thumbnail(self.size)
        background.save(targetPicon)
        self.__runFinished()


class OptimizePiconsFileSize:

    def __init__(self, session):
        self.session = session
        self.session.open(JobProgressView, _('Optimize Picons Progress'), onAbort=self.onAbort, msgBoxID='optimizePicons')
        self.execCommand = ''
        self.executionQueueList = deque()
        piconsList = getFiles(getPiconsPath().getValue(), '.png')
        self.optimizePiconsTotal = len(piconsList)
        self.optimizePiconsCount = 0
        for piconFile in piconsList:
            execCommand = 'pngquant --ext .png --speed 10 --force 128 %s' % piconFile
            self.executionQueueList.append(execCommand)

        self.execQueue()

    def __del__(self):
        del self.session

    def execQueue(self):
        try:
            if len(self.executionQueueList) > 0:
                self.optimizePiconsCount += 1
                progress = int(100 * (float(self.optimizePiconsCount) / float(self.optimizePiconsTotal)))
                self.session.current_dialog.setProgress(progress, _('Optimize %d of %d Picons') % (self.optimizePiconsCount, self.optimizePiconsTotal))
                self.execCommand = self.executionQueueList.popleft()
                t = Thread(target=self.optimizePicon)
                t.start()
        except Exception as e:
            self.__clearExecutionQueueList()
            printToConsole('OptimizePicons execQueue exception:\n' + str(e))

    def __clearExecutionQueueList(self):
        self.executionQueueList = deque()

    def __runFinished(self, retval = None):
        try:
            if len(self.executionQueueList) > 0:
                self.execQueue()
            else:
                printToConsole('OptimizePicons Queue finished!')
                dispatchEvent(OPTIMIZE_PICONS_FINISHED)
        except Exception as e:
            self.__clearExecutionQueueList()
            printToConsole('OptimizePicons runFinished exception:\n' + str(e))

    def optimizePicon(self):
        try:
            call(self.execCommand, shell=True)
            self.__runFinished()
        except Exception as e:
            printToConsole("Error: optimizePngFileSizes '%s'" % e.message)

    def onAbort(self):
        self.__clearExecutionQueueList()
        self.__runFinished()
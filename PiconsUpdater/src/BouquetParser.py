# -*- coding: utf-8 -*-
import re, unicodedata
import six
from enigma import eServiceCenter, eServiceReference
from ServiceReference import ServiceReference
SKIP_BOUQUET_NAMES = 'userbouquet.lastscanned.tv'

def getChannelKey(service):
    channelKeyMatch = re.match('([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):', str(service))
    channelKey = '_'.join(map(str, channelKeyMatch.groups()))
    try:
        return six.ensure_str(unicodedata.normalize('NFKD', channelKey).encode('ascii', 'ignore'))
    except:
        return channelKey


class BouquetParser:

    def __init__(self, bouquetPath):
        self.serviceList = []
        self.bouquetPath = bouquetPath
        self.__loadBouquetList()

    def getServiceList(self):
        return self.serviceList

    def __loadBouquetList(self):
        file = open(self.bouquetPath + '/bouquets.tv', 'r')
        data = file.read()
        file.close()
        bouquetFiles = re.findall('([-_a-z0-9]+\\.[^.]+\\.[a-z]+)', data, re.DOTALL | re.IGNORECASE)
        self.serviceList = []
        for fileName in bouquetFiles:
            if fileName.lower() not in SKIP_BOUQUET_NAMES:
                bouquetList = eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + fileName + '" ORDER BY bouquet')
                services = self.__getBouquetServices(bouquetList)
                self.serviceList += services

    def __getBouquetServices(self, bouquet):
        services = []
        Servicelist = eServiceCenter.getInstance().list(bouquet)
        if Servicelist is not None:
            while True:
                service = Servicelist.getNext()
                if not service.valid():
                    break
                if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
                    continue
                services.append(ServiceReference(service))

        return services
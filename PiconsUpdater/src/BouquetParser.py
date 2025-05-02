# Standard library
from re import match, findall, DOTALL, IGNORECASE
from unicodedata import normalize

# Enigma2 imports
from enigma import eServiceCenter, eServiceReference
from Components.config import config
from Components.SystemInfo import BoxInfo

# Local imports
from ServiceReference import ServiceReference


SKIP_BOUQUET_NAMES = 'userbouquet.lastscanned'


def getChannelKey(service):
	channelKeyMatch = match('([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):', str(service))
	if channelKeyMatch:
		channelKey = '_'.join(map(str, channelKeyMatch.groups()))

		try:
			return normalize('NFKD', channelKey)
		except Exception:
			return channelKey


class BouquetParser:
	def __init__(self, bouquetPath):
		self.serviceList = []
		self.bouquetPath = bouquetPath
		self.excludeiptv = config.plugins.PiconsUpdater.exclude_iptv.value
		self.excluderadio = config.plugins.PiconsUpdater.exclude_radio.value
		self.__loadBouquetList()

	def getServiceList(self):
		return self.serviceList

	def __loadBouquetList(self):
		file = open(self.bouquetPath + '/bouquets.tv', 'r')
		data = file.read()
		file.close()
		bouquetFilesTV = findall('([-_a-z0-9]+\\.[^.]+\\.[a-z]+)', data, DOTALL | IGNORECASE)
		self.serviceList = []
		for fileName in bouquetFilesTV:
			if SKIP_BOUQUET_NAMES not in fileName.lower():
				bouquetList = eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + fileName + '" ORDER BY bouquet')
				services = self.__getBouquetServices(bouquetList)
				self.serviceList += services
		if self.excluderadio:
			return
		file = open(self.bouquetPath + '/bouquets.radio', 'r')
		data = file.read()
		file.close()
		bouquetFilesRadio = findall('([-_a-z0-9]+\\.[^.]+\\.[a-z]+)', data, DOTALL | IGNORECASE)
		for fileName in bouquetFilesRadio:
			if SKIP_BOUQUET_NAMES not in fileName.lower():
				bouquetList = eServiceReference('1:7:2:0:0:0:0:0:0:0:FROM BOUQUET "' + fileName + '" ORDER BY bouquet')
				services = self.__getBouquetServices(bouquetList)
				self.serviceList += services

	def __getBouquetServices(self, bouquet):
		services = []
		Servicelist = eServiceCenter.getInstance().list(bouquet)
		if Servicelist is not None:
			getServiceHook = BoxInfo.getItem("getServiceHook")
			while True:
				service = Servicelist.getNext()
				if not service.valid():
					break
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
					continue
				if getServiceHook and callable(getServiceHook):
					_service = getServiceHook(service, self.excludeiptv)
				else:
					_service = self.getService(service)
				if _service:
					services.append(_service)
		return services

	def getService(self, service):
		if self.excludeiptv:
			sref = service.toString()
			fields = sref.split(':', 10)[:10]
			if fields[0] != '1':
				return None
			sref = ':'.join(fields) + ':'
			return ServiceReference(sref)
		else:
			return ServiceReference(service)

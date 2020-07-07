from __future__ import absolute_import
from __future__ import print_function
from enigma import eServiceReference, eServiceCenter
from enigma import iPlayableService
from enigma import eTimer
from .stalkerclient import stalker
import time
import NavigationInstance
from enigma import eEPGCache
from Components.config import config
from Tools import Notifications
from Screens.MessageBox import MessageBox

from threading import Lock
from copy import deepcopy

navigation_playservice = None
SREF_FLAG_STALKER = 256
SREF_FLAG_HASLINK = 512

class StalkerServiceReference:
	def __init__(self, sref):
		self.type = 0
		self.flag = 0
		self.sid = 0
		self.tsid = 0
		self.onid = 0
		self.is_stalker = 0
		self.haslink = 0
		self.uri = ""
		self.name = ""

		self.sref = sref
		if isinstance(self.sref, eServiceReference):
			self.sref = self.sref.toString()
		self.parse(self.sref)

	def parse(self, sref):
		if sref is None:
			return

		for (idx, data) in enumerate(sref.split(':')):
			try:
				if idx == 0:
					self.type = int(data)
				elif idx == 1:
					self.flag = int(data)
				elif idx in (3, 4, 5, 6):
					int_data = int(data, 16)
					if idx == 3:
						self.sid = int_data
					elif idx == 4:
						self.tsid = int_data
					elif idx == 5:
						self.onid = int_data
					elif idx == 6:
						self.haslink = int_data
				elif idx == 9:
					int_data = int(data)
					self.is_stalker = int_data & SREF_FLAG_STALKER and 1 or 0
					self.haslink = int_data & SREF_FLAG_HASLINK and 1 or 0
				elif idx == 10:
					self.uri = data
				elif idx == 11:
					self.name = data
			except Exception as e:
				print("[StalkerServiceReference] error :", e)

	def getType(self):
		return self.type

	def getFlag(self):
		return self.flag

	def getSid(self):
		return self.sid

	def getTsid(self):
		return self.tsid

	def getOnid(self):
		return self.onid

	def getHaslink(self):
		return self.haslink

	def getUri(self):
		return self.uri

	def getName(self):
		return self.name

	def isStalkerService(self):
		return self.is_stalker

	def hasLink(self):
		return self.getHaslink() == 1

	def __str__(self):
		return "type : %d, flag : %d, sid : %d, tsid : %d, onid : %d, is_stalker : %d, haslink : %d, uri : %s, name : %s" % (self.type, self.flag, self.sid, self.tsid, self.onid, self.is_stalker, self.haslink, self.uri, self.name)

def getTsidOnid():
		from Components.config import config
		import hashlib
		m = hashlib.md5()
		try:
			m.update(config.plugins.stalker_client.server.value.strip('/'))
			tsid = int(str(int(m.hexdigest(), 16))[:4])
		except:
			tsid = 0
		onid = 8000
		return (tsid, onid)

def createStalkerSref(sid, tsid, onid, haslink, uri, name):
	if isinstance(sid, int):
		sid = str(hex(sid).replace("0x", "", 1))

	if isinstance(tsid, int):
		tsid = str(hex(tsid).replace("0x", "", 1))

	if isinstance(onid, int):
		onid = str(hex(onid).replace("0x", "", 1))

	stalker_flag = SREF_FLAG_STALKER
	if haslink:
		stalker_flag |= SREF_FLAG_HASLINK
	stalker_flag = str(stalker_flag)

	sref_str = "4097:0:1:%(SID)s:%(TSID)s:%(ONID)s:0:0:0:%(SFLAG)s:%(URI)s:%(NAME)s" % {
		'SID' : sid,
		'TSID' : tsid,
		'ONID' : onid,
		'SFLAG' : stalker_flag,
		'URI'  : uri,
		'NAME' : name.replace(':', '%3A')
	}
	return eServiceReference(sref_str)

def checkSameSref(sref_1, sref_2):
	if not isinstance(sref_1, eServiceReference) or not isinstance(sref_2, eServiceReference):
		return False

	if sref_1 is None or sref_2 is None:
		return False

	return sref_1 == sref_2

prev_linked = ()
def getLink(sref):
	global prev_linked
	if prev_linked and sref.toString() == prev_linked[1]:
		sref = eServiceReference(prev_linked[0])

	new_sref = sref
	ssref = StalkerServiceReference(sref)
	has_link = ssref.hasLink()
	if stalker.isForceLinkCheck() or has_link:
		sid = ssref.getSid()
		tsid = ssref.getTsid()
		onid = ssref.getOnid()
		uri = ssref.getUri()
		sname = ssref.getName()
		json_object = stalker.createLink(uri)
		# print "[getLink] json_object :", json_object
		if json_object:
			try:
				cmd = str(json_object.get('cmd')).split(" ")
				uri = len(cmd) > 1 and cmd[1] or cmd[0]
				new_sref = createStalkerSref(sid, tsid, onid, 0, uri, sname)
				prev_linked = (sref.toString(), new_sref.toString())
			except Exception as e:
				print("[getLink]", e)
		else:
			new_sref = None

	return new_sref

class checkAvailable:
	def __init__(self):
		self.sref = None
		self.checkParentalControl = None
		self.forceRestart = None
		self.count = 0
		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.checkTimerCB)

	def stop(self):
		self.sref = None
		self.checkTimer.stop()

	def start(self, sref, checkParentalControl, forceRestart):
		self.sref = sref
		self.checkParentalControl = checkParentalControl
		self.forceRestart = forceRestart
		self.count = 0
		self.checkTimer.start(1000, True)

	def getCurrentChannel(self):
		res = None
		import NavigationInstance
		if NavigationInstance.instance:
			res = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		return res

	def setCurrentChannel(self, ref):
		import NavigationInstance
		if NavigationInstance.instance:
			NavigationInstance.instance.currentlyPlayingServiceReference = ref

	def checkTimerCB(self):
		self.count += 1
		cur_playing_sref = self.getCurrentChannel()
		if not checkSameSref(self.sref, cur_playing_sref):
			self.sref = None

		if self.sref:
			if stalker.isAvailable(0x1):
				new_sref = getLink(self.sref)
				if new_sref is not None:
					navigation_playservice(new_sref, self.checkParentalControl, self.forceRestart)
					if new_sref == self.getCurrentChannel():
						self.setCurrentChannel(self.sref)
				else:
					self.checkTimer.start(1000, True)
			else:
				self.checkTimer.start(1000, True)

check_available_instance = checkAvailable()

def createLink(sref, checkParentalControl, forceRestart):
	check_available_instance.stop()
	new_sref = sref
	ssref = StalkerServiceReference(sref)
	if ssref.isStalkerService(): # stalker channel
		if stalker.isAvailable(0x1):
			new_sref = getLink(sref)
			if new_sref is None:
				check_available_instance.start(sref, checkParentalControl, forceRestart)
		else:
			check_available_instance.start(sref, checkParentalControl, forceRestart)

	return new_sref

def sc_playService(ref, checkParentalControl = True, forceRestart = False):
	new_sref = createLink(ref, checkParentalControl, forceRestart)
	res = navigation_playservice(new_sref, checkParentalControl, forceRestart)
	if not res:
		cur_sref = check_available_instance.getCurrentChannel()
		if new_sref and cur_sref and new_sref == cur_sref:
			check_available_instance.setCurrentChannel(ref)

def hookPlayService():
	global navigation_playservice
	import NavigationInstance
	if NavigationInstance.instance:
		navigation_playservice = NavigationInstance.instance.playService
		NavigationInstance.instance.playService = sc_playService

class EPGDB:
	def __init__(self):
		self.infobar = None
		self.serviceList = []
		self.updateFavouriteServiceList()

		self.epgcache = eEPGCache.getInstance()
		self.importEventsTimer = eTimer()
		self.importEventsTimer.callback.append(self.importEvents)
		self.events = {}
		self.lock = Lock()

	def getInfoBar(self):
		if not self.infobar:
			from Screens.InfoBar import InfoBar
			if InfoBar.instance:
				self.infobar = InfoBar.instance
		return self.infobar

	def getScServices(self, bouquet_root):
		services = []
		serviceHandler = eServiceCenter.getInstance()
		bouquetList = serviceHandler.list(bouquet_root)
		bouquetListContents = bouquetList.getContent('R', True)
		for sref in bouquetListContents:
			isBouquet = sref.flags & eServiceReference.isDirectory
			isScService = sref and StalkerServiceReference(sref).isStalkerService()
			if isBouquet:
				services.extend(self.getScServices(sref))
			elif isScService:
				services.append(sref.toString())
		return services

	def getServicesFromChList(self):
		stalker_services = []
		infobar = self.getInfoBar()
		if infobar:
			stalker_services = self.getScServices(infobar.servicelist.bouquet_root)

		return stalker_services

	def getFavouriteServiceList(self):
		if not self.serviceList:
			self.serviceList = self.getServicesFromChList()

		chid_list = [StalkerServiceReference(sref).getSid() for sref in self.serviceList]
		return chid_list

	def numFavouriteServiceList(self):
		return len(self.getFavouriteServiceList())

	def serviceListUpdated(self):
		self.updateFavouriteServiceList()
		config.plugins.stalker_client.numFavlist.value = self.numFavouriteServiceList()

	def updateFavouriteServiceList(self):
		self.serviceList = self.getServicesFromChList()

	def getServiceFromFavList(self, t_sid):
		t_tsid, t_onid = getTsidOnid()
		service = None
		for x in self.serviceList:
			ssref = StalkerServiceReference(x)
			sid = ssref.getSid()
			tsid = ssref.getTsid()
			onid = ssref.getOnid()
			if t_sid == sid and t_tsid == tsid and t_onid == onid:
				service = x
				break

		return service

	def putEvent(self, event):
		try:
			channelId = int(event['ch_id'])
			beginTime = int(event['start_timestamp'])
			duration = int(event['duration'])
			eventId = int(event['id'])
			eventName = event['name']
			shortDescription = event['descr']
			extendedDescription = event['descr']

			service = self.getServiceFromFavList(channelId)
			data = (beginTime, duration, eventName, shortDescription, extendedDescription, 0, eventId)

			self.addEvent(service, data)
		except:
			pass

	def importEvents(self):
		data = self.getEvents()
		if data:
			(sref, events) = data
			self.epgcache.importEvents(sref, events)
			ssref = StalkerServiceReference(sref)
			self.epgUpdated(ssref.getSid())

		if self.events:
			self.importEventsTimer.start(100, True)

	def addEvent(self, sref, ev):
		with self.lock:
			data = self.events.setdefault(sref, [])
			data.append(ev)
		self.importEventsTimer.start(1000, True)

	def getEvents(self):
		data = None
		with self.lock:
			ks = self.events.keys()
			if ks:
				sref = ks[0]
				events = tuple(deepcopy(self.events[sref]))
				del self.events[sref]
				data = (sref, events)
		return data

	def epgUpdated(self, sid):
		if NavigationInstance.instance is not None:
			curService = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
			ssref = StalkerServiceReference(curService)
			if ssref.isStalkerService():
				cur_sid = ssref.getSid()
				if cur_sid == sid:
					self.sendUpdatedEventInfo()

	def sendUpdatedEventInfo(self):
		from enigma import iPlayableService
		if NavigationInstance.instance is not None:
			NavigationInstance.instance.dispatchEvent(iPlayableService.evUpdatedEventInfo)

class StalkerThreadHandler:
	def __init__(self):
		self.threads = []

	def clearThread(self):
		while len(self.threads):
			t = self.popThread()
			t.kill()
			t.join()

	def getRunningThread(self):
		if len(self.threads):
			return self.threads[0]
		return None

	def pushThread(self, t):
		if t:
			self.threads.append(t)

	def popThread(self):
		if len(self.threads) > 0:
			return self.threads.pop()

class StalkerEventHandler:
	def __init__(self):
		self.epgdb = EPGDB()
		self.session = None
		self.addSessionStart()

	def addSessionStart(self):
		from Components.PluginComponent import plugins
		from Plugins.Plugin import PluginDescriptor
		p = PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc=self.onSessionStart)
		plugins.plugins.setdefault(PluginDescriptor.WHERE_SESSIONSTART, []).append(p)

	def onSessionStart(self, session, **kwargs):
		self.session = session
		hookPlayService()

scinfo = StalkerEventHandler()
scthreads = StalkerThreadHandler()

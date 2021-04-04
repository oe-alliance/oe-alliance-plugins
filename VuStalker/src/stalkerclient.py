from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, ConfigInteger

from enigma import eTimer

import collections
import json
import os
import threading

from ctypes import cdll, cast, c_char_p, c_void_p
from time import localtime, strftime, time
from urllib.parse import quote as urlencode
from uuid import getnode


def get_mac_address():
	macaddr = "00:00:00:00:00:00"
	try:
		macaddr = ':'.join(("%012X" % getnode())[i:i + 2] for i in range(0, 12, 2))
	except Exception:
		macaddr = "00:00:00:00:00:00"
	return macaddr


DEFAULT_MAC = get_mac_address()
DEFAULT_URL = "http://stalker-server/stalker_portal/c/"

SUPPORT_MODULES = {
	'tv': 0x1,
	'epg': 0x2,
	'epg.simple': 0x4,
	'account': 0x80,
}

selection_list = [("0", _("Disabled")), ("1", _("Enabled"))]

config.plugins.stalker_client = ConfigSubsection()
config.plugins.stalker_client.server = ConfigText(default=DEFAULT_URL, fixed_size=False)
config.plugins.stalker_client.mac = ConfigText(default=DEFAULT_MAC, fixed_size=False, visible_width=18)
config.plugins.stalker_client.authEnabled = ConfigSelection(choices=selection_list)
config.plugins.stalker_client.username = ConfigText(default="", fixed_size=False, visible_width=18)
config.plugins.stalker_client.password = ConfigText(default="", fixed_size=False, visible_width=18)
config.plugins.stalker_client.retrycount = ConfigInteger(default=5, limits=(1, 5))
config.plugins.stalker_client.numFavlist = ConfigInteger(default=0)


def convert(data):
	if isinstance(data, str):
		return str(data)
	elif isinstance(data, collections.Mapping):
		return dict(list(map(convert, iter(data.items()))))
	elif isinstance(data, collections.Iterable):
		return type(data)(list(map(convert, data)))
	else:
		return data


class SCAPI(object):
	LIB_DIR = os.path.dirname(os.path.realpath(__file__))

	def __init__(self):
		self.m_clib = cdll.LoadLibrary('%s/libvustalkerclient.so' % self.LIB_DIR)
		self.m_lock = threading.Lock()
		self.m_obj = None
		self.m_str = None

		self.m_clib.SCAPI_DestroyString.argtypes = [c_void_p]

		self.m_clib.GetStatusMessage.restype = c_void_p
		self.m_clib.ITV_CreateLink.restype = c_void_p
		self.m_clib.ITV_GetAllChannels.restype = c_void_p
		self.m_clib.ITV_GetGenres.restype = c_void_p
		self.m_clib.ITV_GetOrderedList.restype = c_void_p
		self.m_clib.ITV_GetEpgInfo.restype = c_void_p
		self.m_clib.ITV_GetShortEpg.restype = c_void_p
		self.m_clib.EPG_GetWeek.restype = c_void_p
		self.m_clib.EPG_GetSimpleDataTable.restype = c_void_p
		self.m_clib.EPG_GetDataTable.restype = c_void_p
		self.m_clib.OTHER_GetAccountInfo.restype = c_void_p

	def __del__(self):
		self.ResetString()
		if self.m_obj:
			self.m_clib.SCAPI_DestroyObject(self.m_obj)
		self.m_obj = None

	def CreateObject(self):
		if not self.m_obj:
			 self.m_obj = self.m_clib.SCAPI_CreateObject()

	def ResetString(self):
		with self.m_lock:
			if self.m_str:
				self.m_clib.SCAPI_DestroyString(self.m_str)
			self.m_str = None

	def CFG_SetStalkerServer(self, server, mac, enabled):
		self.m_clib.CFG_SetStalkerServer(self.m_obj, server, mac, enabled)

	def CFG_SetStalkerAuth(self, username, password):
		self.m_clib.CFG_SetStalkerAuth(self.m_obj, username, password)

	def IsAuthenticated(self):
		return self.m_clib.IsAuthenticated(self.m_obj)

	def IsBlocked(self):
		return self.m_clib.IsBlocked(self.m_obj)

	def IsAvailable(self, module):
		return self.m_clib.IsAvailable(self.m_obj, module)

	def IsForceLinkCheck(self):
		return self.m_clib.IsForceLinkCheck(self.m_obj)

	def GetStatus(self):
		return self.m_clib.GetStatus(self.m_obj)

	def GetStatusMessage(self):
		self.ResetString()
		self.m_str = self.m_clib.GetStatusMessage(self.m_obj)
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def Authenticate(self):
		return self.m_clib.Authenticate(self.m_obj)

	def ITV_CreateLink(self, cmd):
		self.ResetString()
		self.m_str = self.m_clib.ITV_CreateLink(self.m_obj, str(cmd).encode())
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def ITV_GetAllChannels(self):
		self.ResetString()
		self.m_str = self.m_clib.getAllChannels(self.m_obj)
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def ITV_GetGenres(self):
		self.ResetString()
		self.m_str = self.m_clib.ITV_GetGenres(self.m_obj)
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def ITV_GetOrderedList(self, genre_id, idx):
		self.ResetString()
		self.m_str = self.m_clib.ITV_GetOrderedList(self.m_obj, str(genre_id).encode(), str(idx).encode())
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def ITV_GetEpgInfo(self, period):
		self.ResetString()
		self.m_str = self.m_clib.ITV_GetEpgInfo(self.m_obj, str(period))
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def ITV_GetShortEpg(self, ch_id):
		self.ResetString()
		self.m_str = self.m_clib.ITV_GetShortEpg(self.m_obj, str(ch_id))
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def EPG_GetWeek(self):
		self.ResetString()
		self.m_str = self.m_clib.EPG_GetWeek(self.m_obj)
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def EPG_GetSimpleDataTable(self, ch_id, date, page):
		self.ResetString()
		self.m_str = self.m_clib.EPG_GetSimpleDataTable(self.m_obj, str(ch_id).encode(), str(date).encode(), str(page).encode())
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def EPG_GetDataTable(self, from_ts, to_ts, fav, ch_id, page):
		self.ResetString()

		t_from = urlencode(strftime('%Y-%m-%d %H:%M:%S', localtime(float(from_ts))))
		t_to = urlencode(strftime('%Y-%m-%d %H:%M:%S', localtime(float(to_ts))))

		self.m_str = self.m_clib.EPG_GetDataTable(self.m_obj, "", "", str(t_from).encode(), str(t_to).encode(), str(fav).encode(), str(ch_id).encode(), str(page).encode())
		return cast(self.m_str, c_char_p).value.decode('utf-8')

	def OTHER_GetAccountInfo(self):
		self.ResetString()
		self.m_str = self.m_clib.OTHER_GetAccountInfo(self.m_obj)
		return cast(self.m_str, c_char_p).value.decode('utf-8')


class SCAsyncCall(object):
	def __init__(self, func, callback=None):
		self.func = func
		self.callback = callback
		self.lock = threading.Lock()

	def __call__(self, *args, **kwargs):
		self.thread = threading.Thread(target=self.wrapper, args=args, kwargs=kwargs)
		self.thread.start()
		return self

	def wrapper(self, *args, **kwargs):
		if self.func:
			with self.lock:
				result = self.func(*args, **kwargs)
			if self.callback:
				self.callback(result)


class SCTask:
	def __init__(self, cb, func, *args):
		self.func = func
		self.args = args
		self.cb = cb

	@property
	def getFunc(self):
		return self.func

	@property
	def getArgs(self):
		return self.args

	@property
	def getCallback(self):
		return self.cb

	def __str__(self):
		return "task: %s [%s]" % (self.func and self.func.__name__ or "None", self.cb and self.cb.__name__ or "None")


class SCThread(threading.Thread):
	CHECK_INTERVAL = 100

	def __init__(self, name):
		threading.Thread.__init__(self, name=name)
		self.semaphore = threading.Semaphore(0)
		self.lock = threading.Lock()
		self.running = False
		self.holding = False
		self.tasks_to_poll = []
		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.timeout)
		self.checkTimer.start(self.CHECK_INTERVAL, True)
		self.daemon = True
		self.start()

	def isHold(self):
		return self.holding

	def doHold(self, val=False):
		self.holding = val

	hold = property(isHold, doHold)

	def timeout(self):
		self.semaphore.release()

	def run(self):
		self.running = True
		while self.running:
			self.semaphore.acquire()
			with self.lock:
				tasks_to_poll = self.tasks_to_poll

			while len(tasks_to_poll):
				t = tasks_to_poll.pop()
				if isinstance(t, SCTask):
					func = t.func
					args = t.args
					cb = t.cb

					res = self.running and func(*args) or None
					if self.running and cb:
						cb(res)
					else:
						break

			if len(tasks_to_poll):
				self.checkTimer.start(self.CHECK_INTERVAL, True)
			else:
				self.checkTimer.stop()

	def kill(self):
		self.clearTask()
		self.running = False
		self.timeout()

	def addTask(self, cb, func, *args):
		if self.running:
			task = SCTask(cb, func, *args)
			with self.lock:
				self.tasks_to_poll.insert(0, task)
			self.checkTimer.start(self.CHECK_INTERVAL, True)

	def clearTask(self):
		self.tasks_to_poll[:] = []
		self.checkTimer.stop()


class SCCache(object):
	CACHE_DIR = '/tmp/stalker/'
	# check last time: update 12h
	CACHE_DURATION = 12

	def __init__(self, url):
		self.prefix = url.split("/")[2]
		self.basepath = self.CACHE_DIR + self.prefix
		self.PrepareCache()

	def PrepareCache(self):
		if not os.path.exists(self.basepath):
			os.makedirs(self.basepath)

	def ClearCache(self):
		for file in os.listdir(self.basepath):
			if file.startswith(self.prefix):
				os.remove(self.basepath + '/' + file)
		os.rmdir(self.basepath)

	def SaveData(self, filename, contents='\"\"'):
		self.PrepareCache()

		if len(contents) == 0:
			contents = '\"\"'

		file = self.basepath + "/" + self.prefix + "-" + filename
		data = '{"time":"' + str(time()) + '","contents":' + contents + '}'
		with open(file, 'w') as f:
			f.write(data)

	def LoadData(self, filename):
		file = self.basepath + "/" + self.prefix + "-" + filename
		if os.access(file, os.R_OK):
			data = None
			try:
				with open(file) as f:
					data = json.load(f)
			except ValueError as e:
				data = None

			if data:
				time_cahced = float(data['time'])
				if ((time() - time_cahced) / 3600) < self.CACHE_DURATION:
					return json.dumps(convert(data['contents']))

		return None


class StalkerClient(object):
	def __init__(self):
		self.m_api = SCAPI()
		self.m_cache = SCCache(config.plugins.stalker_client.server.value)
		self.m_retry = config.plugins.stalker_client.retrycount.value

	def __del__(self):
		if self.m_api:
			del self.m_api
		self.m_api = None

	def setStalkerServer(self):
		self.m_api.CFG_SetStalkerServer(config.plugins.stalker_client.server.value, config.plugins.stalker_client.mac.value, config.plugins.stalker_client.authEnabled.value)

	def setStalkerAuth(self):
		self.m_api.CFG_SetStalkerAuth(config.plugins.stalker_client.username.value, config.plugins.stalker_client.password.value)

	def getRetry(self):
		return self.m_retry

	def setRetry(self, value):
		self.m_retry = value

	retry = property(getRetry, setRetry)

	def startup(self):
		self.m_api.CreateObject()
		return self.reload(True)

	def reload(self, init=False):
		if not init:
			self.setStalkerServer()
			self.setStalkerAuth()

		if self.getStatus() == 200:
			return self.authenticate()
		return False

	def authenticate(self):
		return self.m_api.Authenticate()

	def isAuthenticated(self):
		return self.m_api.IsAuthenticated()

	def isBlocked(self):
		return self.m_api.IsBlocked()

	def isAvailable(self, module):
		return self.m_api.IsAvailable(module)

	def isForceLinkCheck(self):
		return self.m_api.IsForceLinkCheck()

	def getStatus(self):
		return self.m_api.GetStatus()

	def getStatusMsg(self):
		return self.m_api.GetStatusMessage()

	def getJsonItems(self, response):
		json_items = None

		try:
			json_object = json.loads(response).get('js')
			json_items = convert(json_object)
		except Exception as e:
			json_items = None

		return json_items

	def createLink(self, cmd):
		if not self.isAuthenticated():
			return None

		response = self.m_api.ITV_CreateLink(cmd)
		return self.getJsonItems(response)

	def getAllChannels(self):
		if not self.isAuthenticated():
			return None

		response = self.m_api.ITV_GetAllChannels()
		return self.getJsonItems(response)

	def getGenres(self, force=False):
		if not self.isAuthenticated():
			return None

		postfix = "genres"
		response = None

		if force:
			self.m_cache.ClearCache()
		else:
			response = self.m_cache.LoadData(postfix)

		if not response:
			response = self.m_api.ITV_GetGenres()
			self.m_cache.SaveData(postfix, response)

		return self.getJsonItems(response)

	def getOrderedList(self, genre_id, idx, force=False):
		if not self.isAuthenticated():
			return None

		postfix = ("all" if genre_id == "*" else genre_id) + "-" + str(idx)
		response = None

		if not force:
			response = self.m_cache.LoadData(postfix)

		if not response:
			response = self.m_api.ITV_GetOrderedList(genre_id, idx)
			self.m_cache.SaveData(postfix, response)

		return self.getJsonItems(response)

	def getEpgInfo(self, period):
		if not self.isAuthenticated():
			return None

		response = self.m_api.ITV_GetEpgInfo(period)
		return self.getJsonItems(response)

	def getShortEpg(self, ch_id):
		if not self.isAuthenticated():
			return None

		response = self.m_api.ITV_GetShortEpg(ch_id)
		return self.getJsonItems(response)

	def getWeek(self):
		if not self.isAuthenticated():
			return None

		response = self.m_api.EPG_GetWeek()
		return self.getJsonItems(response)

	def getSimpleDataTable(self, ch_id, date, page):
		if not self.isAuthenticated():
			return None

		response = self.m_api.EPG_GetSimpleDataTable(ch_id, date, page)
		return self.getJsonItems(response)

	def getDataTable(self, from_ts, to_ts, fav, ch_id, page):
		if not self.isAuthenticated():
			return None

		response = self.m_api.EPG_GetDataTable(from_ts, to_ts, fav, ch_id, page)
		return self.getJsonItems(response)

	def getAccountInfo(self):
		if not self.isAuthenticated():
			return None

		response = self.m_api.OTHER_GetAccountInfo()
		return self.getJsonItems(response)


stalker = StalkerClient()

from Components.config import config
from Plugins.Plugin import PluginDescriptor
from enigma import eTimer

from .SCInfo import scinfo, scthreads
from .SCChannels import StalkerClient_ChannelSelection
from .SCConfig import StalkerClient_SetupScreen
from .SCEPG import updateEvents
from .stalkerclient import SCThread, stalker, DEFAULT_URL

from math import ceil as math_ceil

scpoll = None

class SCPoll:
	CHECK_INTERVAL = 3600
	RETRY_INTERVAL = 3000

	def __init__(self):
		self.thread = None
		self.state = False

		self.initialized = False
		self.poll_timer = None

	def __del__(self):
		self.shutdown()

	def poll(self):
		if self.poll_timer is not None and stalker.isAvailable(0x4):
			self.poll_timer.stop()
			self.task(None, updateEvents, self.initialized)
			self.poll_timer.startLongTimer(self.CHECK_INTERVAL)
			self.initialized = True

	def task(self, cb, func, *args):
		if self.thread:
			self.thread.addTask(cb, func, *args)

	def startup(self):
		if self.thread:
			if config.plugins.stalker_client.server.value == DEFAULT_URL:
				self.shutdown()
			return

		if not config.plugins.stalker_client.server.value == DEFAULT_URL:
			self.thread = SCThread('stalkerclientpoll')
			scthreads.threads.insert(0, self.thread)
			self.state = True

			self.poll_timer = eTimer()
			self.poll_timer.callback.append(self.poll)
		else:
			self.state = False

	def shutdown(self):
		if self.thread:
			scthreads.threads.remove(self.thread)
			self.thread.kill()
			self.thread.join()
			self.thread = None
		self.state = False

		if self.poll_timer:
			self.poll_timer.callback.remove(self.poll)
			self.poll_timer = None

def sc_genres_cb(result):
	if result:
		print("[StalkerClient] genres available.")
	else:
		print("[StalkerClient] got no genres.")

def sc_authenticate_cb(result):
	print("[StalkerClient] authenticated: %s" % ("OK" if result is not None and result > 0 else "Fail"))
	if result is not None and result > 0:
		scpoll.task(sc_genres_cb, stalker.getGenres)
		scinfo.epgdb.serviceListUpdated()
		if config.plugins.stalker_client.numFavlist.value > 0:
			scpoll.poll_timer.start(scpoll.RETRY_INTERVAL, True)
	else:
		if stalker.isBlocked():
			print("[StalkerClient] %s is blocked: %s" % (config.plugins.stalker_client.server.value, stalker.getStatusMsg()))
		elif stalker.getStatus() > 0:
			print("[StalkerClient] retry authenticate: %d / %d" % (stalker.retry, config.plugins.stalker_client.retrycount.value))

			stalker.retry -= 1
			if stalker.retry > 0:
				scpoll.task(sc_authenticate_cb, stalker.authenticate)

def sc_changed_setup(unused):
	print("[StalkerClient] changed config values.")
	if not scpoll.state:
		scpoll.startup()
		scpoll.task(sc_authenticate_cb, stalker.startup)

def sc_changed_favlists(unused):
	if scpoll.state:
		print("[StalkerClient] updated favourites.")
		if config.plugins.stalker_client.numFavlist.value == 0:
			scpoll.poll_timer.stop()
		else:
			scpoll.poll_timer.start(scpoll.RETRY_INTERVAL, True)

def sc_autostart(reason, **kwargs):
	global scpoll
	if reason == 0:
		scpoll = SCPoll()
	else:
		if scpoll:
			scpoll.shutdown()
			del scpoll
		scthreads.clearThread()

def sc_sessionstart(session, **kwargs):
	config.plugins.stalker_client.mac.addNotifier(sc_changed_setup, initial_call=False, immediate_feedback=False)
	config.plugins.stalker_client.server.addNotifier(sc_changed_setup, initial_call=False, immediate_feedback=False)
	config.plugins.stalker_client.numFavlist.addNotifier(sc_changed_favlists, initial_call=False, immediate_feedback=True)

	scpoll.startup()
	if scpoll.state:
		scpoll.task(sc_authenticate_cb, stalker.startup)

def sc_setup(session, **kwargs):
	session.open(StalkerClient_SetupScreen)

def sc_main(session, **kwargs):
	session.open(StalkerClient_ChannelSelection)

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART, fnc=sc_autostart),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sc_sessionstart),
		PluginDescriptor(
			name=_("StalkerClient Configuration"),
			description=_("Configure Stalker Client"),
			where=[PluginDescriptor.WHERE_PLUGINMENU ],
			fnc=sc_setup),
		PluginDescriptor(
			name=_("StalkerClient TV"),
			description=_("Stalker Client TV Channels"),
			where=[ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
			fnc=sc_main),
		]

from __future__ import print_function
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText, ConfigInteger, ConfigSelection
g_main = None
g_browser = None
g_browser_cfg = None
g_service = None
config.plugins.browser = ConfigSubsection()
config.plugins.browser.startup = ConfigText(default='http://www.gigablue.de', visible_width=50, fixed_size=False)
config.plugins.browser.margin_x = ConfigInteger(default=30, limits=(0, 1280))
config.plugins.browser.margin_y = ConfigInteger(default=20, limits=(0, 720))
config.plugins.browser.rcu_type = ConfigSelection(choices={'en': 'en',
 'de': 'de'}, default='en')
config.plugins.browser.enable_ntpd = ConfigYesNo(default=False)
config.plugins.browser.ntpd_url = ConfigText(default='0.rhel.pool.ntp.org', visible_width=50, fixed_size=False)
config.plugins.browser.youtube_showhelp = ConfigYesNo(default=False)
config.plugins.browser.youtube_uri = ConfigText(default='http://www.youtube.com/tv', visible_width=50, fixed_size=False)
config.plugins.browser.youtube_enable_ntpd = ConfigYesNo(default=False)
config.plugins.browser.youtube_ntpd_url = ConfigText(default='0.rhel.pool.ntp.org', visible_width=50, fixed_size=False)
g_browser_cfg = config.plugins.browser

class PSingleton:

	def __init__(self, decorated):
		self._decorated = decorated

	def GetInstance(self):
		try:
			return self._instance
		except AttributeError:
			self._instance = self._decorated()
			return self._instance

	def __call__(self):
		raise TypeError('Singletons must be accessed through `GetInstance()`.')

	def __instancecheck__(self, inst):
		return isinstance(inst, self._decorated)


_DEBUG, _WARNING, _ERROR = (177, 178, 179)
_LVSTR = {_DEBUG: '  DEBUG',
 _WARNING: 'WARNING',
 _ERROR: '  ERROR'}

@PSingleton

class PLogger:

	def __init__(self):
		self.level = _DEBUG
		self.initialized = False

	def Init(self, level):
		self.level = level
		self.initialized = True

	def Log(self, level, format, argv):
		if level < self.level:
			return
		print('[' + _LVSTR[level] + ']', format % argv)


def INIT(level = _ERROR):
	PLogger.GetInstance().Init(level)


def DEBUG(format, *argv):
	PLogger.GetInstance().Log(_DEBUG, format, argv)


def WARNING(format, *argv):
	PLogger.GetInstance().Log(_WARNING, format, argv)


def ERROR(format, *argv):
	PLogger.GetInstance().Log(_ERROR, format, argv)

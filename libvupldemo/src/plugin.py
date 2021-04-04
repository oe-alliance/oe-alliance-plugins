from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap

from os import system as cmd, popen

RUNPATH = "/usr/bin"
RUNNAME = "cube"


class runScreen(Screen):
	skin = """
		<screen position="center,center" size="640,480">
		</screen>
		"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions"], {
				"ok": self.onKeyOK,
				"cancel": self.onKeyCancel,
			}, -2)

		self.session = session
		self.onLayoutFinish.append(self.start_application)

	def start_application(self):
		cmd("exec %s/%s &" % (RUNPATH, RUNNAME))

	def stop_application(self):
		pid = popen("ps -e | grep '%s' | grep -v grep | awk '{ print $1 }'" % RUNNAME[:15]).read()
		if pid:
			cmd("kill %s" % pid)

	def onKeyOK(self):
		self.onKeyCancel()

	def onKeyCancel(self):
		self.stop_application()
		self.close()


def runMenu(session, **kwargs):
	session.open(runScreen)


def Plugins(**kwargs):
	l = []
	l.append(PluginDescriptor(where=PluginDescriptor.WHERE_PLUGINMENU, fnc=runMenu, name="Cube Demo", description=_("Plugin for libvupl Demo")))
	return l

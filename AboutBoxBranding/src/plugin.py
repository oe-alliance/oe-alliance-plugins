# for localized messages
from . import _

from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText

from Screens.Screen import Screen


class AboutBoxBranding(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("About Boxbranding"))
		self.skinName = ["AboutBoxBranding", "AboutOE", "About"]

		self["key_red"] = StaticText(_("Close"))
		self["AboutScrollLabel"] = ScrollLabel(self.getBoxbranding())

		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"back": self.close,
			"red": self.close,
			"up": self.pageUp,
			"down":	self.pageDown,
			"left":	self.pageUp,
			"right": self.pageDown,
		}, -2)

	def pageUp(self):
		self["AboutScrollLabel"].pageUp()

	def pageDown(self):
		self["AboutScrollLabel"].pageDown()

	def getBoxbranding(self):
		import boxbranding
		bblist = []
		for m in sorted(boxbranding.__dict__.keys()):
			if callable(getattr(boxbranding, m)):
				v = getattr(boxbranding, m)()
				for x in ("http://", "https://"): # Trim URLs to domain only
					if v.startswith(x):
						v = x + v.split(x)[1].split('/')[0] + "/"
				bblist.append("%s:\t%s\n" % (m, v))
		return ''.join(bblist)

def main(session, **kwargs):
	session.open(AboutBoxBranding)

def start(menuid):
	try:
		import boxbranding
		if menuid == "information":
			return [(_("Boxbranding"), main, "About Boxbranding", 1000)]
	except:
		print("[AboutBoxBranding] Error: %s: '%s'!" % (type(err).__name__, err))
	return []

def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor
	return [PluginDescriptor(where = PluginDescriptor.WHERE_MENU, fnc=start)]
			

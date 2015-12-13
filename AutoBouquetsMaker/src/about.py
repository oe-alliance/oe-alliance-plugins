from enigma import getDesktop

from Screens.Screen import Screen

from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap

import os
import sys

class AutoBouquetsMaker_About(Screen):
	skin="""
<screen position="center,center" size="600,350">
	<widget name="about" position="10,10" size="580,430" font="Regular;15"/>
	<widget name="key_red" position="0,310" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
	<ePixmap name="red" pixmap="skin_default/buttons/red.png" position="0,310" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
	<widget name="oealogo" position="400,215" size="200,135"  zPosition="4" transparent="1" alphatest="blend"/>
</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		Screen.setTitle(self, _("AutoBouquetsMaker") + " - " + _("About"))

		self["about"] = Label("")
		self["oealogo"] = Pixmap()

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"red": self.quit,
			"cancel": self.quit,
			"menu": self.quit,
		}, -2)

		self["key_red"] = Button(_("Close"))

		try:
			from version import PLUGIN_VERSION
		except Exception, e:
			version = "unknown version"

		credit = "OE-Alliance AutoBouquetsMaker %s (c) 2012 \nSandro Cavazzoni & Andrew Blackburn\n" % PLUGIN_VERSION
		credit += "http://github.com/oe-alliance\n"
		credit += "http://www.sifteam.eu\n"
		credit += "http://www.world-of-satellite.com\n\n"
		credit += "Application credits:\n"
		credit += "- Sandro Cavazzoni aka skaman (main developer)\n"
		credit += "- Andrew Blackburn aka AndyBlac (main developer)\n"
		credit += "- Peter de Jonge aka PeterJ (developer)\n"
		credit += "- Huevos (developer)\n\n"
		credit += "Sources credits:\n"
		credit += "- LraiZer (used his AutoBouquets script as a start point)"
		self["about"].setText(credit)
		self.onFirstExecBegin.append(self.setImages)

	def setImages(self):
		self["oealogo"].instance.setPixmapFromFile("%s/images/oea-logo.png" % (os.path.dirname(sys.modules[__name__].__file__)))

	def quit(self):
		self.close()


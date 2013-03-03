from enigma import getDesktop

from Screens.Screen import Screen

from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap

import os
import sys

class OnDemand_About(Screen):
	skin="""
<screen position="360,150" size="600,350" title="OnDemand - About">
	<widget name="about" position="10,10" size="580,430" font="Regular;15" />
	<widget name="key_red" position="0,310" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
	<ePixmap name="red" pixmap="skin_default/buttons/red.png" position="0,310" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
	<widget name="oealogo" position="400,215" size="200,135"  zPosition="4" transparent="1" alphatest="blend" />
</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		Screen.setTitle(self, _("OnDemand") + " - " + _("About"))

		self["about"] = Label("")
		self["oealogo"] = Pixmap()

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"red": self.quit,
			"cancel": self.quit,
			"menu": self.quit,
		}, -2)

		self["key_red"] = Button(_("Close"))
  
		credit = "OE-Alliance OnDemand (c) 2013 \n"
		credit += "http://github.com/oe-alliance\n"
		credit += "http://www.world-of-satellite.com\n\n"
		credit += "Application credits:\n"
		credit += "- mcquaim, RogerThis & AndyBlac (main developers)\n"
		credit += "- The whole Vix team for Design, Graphics, Code optimisation, Geo unlock & Testing\n\n"
		credit += "Sources credits:\n"
		credit += "- kitesurfing (used VODie as a base for the Irish plugins)\n"
		credit += "- XBMC BBC iPlayer team (used as a base for iPlayer)\n"
		credit += "- subixonfire (used his version as a base for ITV)\n"
		credit += "- mossy (used his version as a base for 4OD)\n"
		credit += "- OpenUitzendingGemist team (used this as a design base)\n"
		credit += "- And every one else involved along the way as there are way to many to name!\n"
		self["about"].setText(credit)
		self.onFirstExecBegin.append(self.setImages)

	def setImages(self):
		self["oealogo"].instance.setPixmapFromFile("%s/images/oea-logo.png" % (os.path.dirname(sys.modules[__name__].__file__)))

	def quit(self):
		self.close()


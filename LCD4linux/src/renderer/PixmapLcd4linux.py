from Renderer import Renderer
from enigma import ePixmap
import os

class PixmapLcd4linux(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.mTime = 0
		self.swap = "0"

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		if os.path.isfile("/tmp/l4ldisplay.png"):
			try:
				mtime = os.stat("/tmp/l4ldisplay.png").st_mtime
				if self.mTime != mtime:
					if self.instance:
						self.instance.setScale(1)
						if self.swap == "0":
							self.swap = "1"
							self.instance.setPixmapFromFile("/tmp/l4ldisplay.png")
						else:
							self.swap = "0"
							self.instance.setPixmapFromFile("/tmp/lcd4linux/dpf.png")						
						self.instance.show()
						self.mTime = mtime
					else:
						self.mTime = 0
			except:
				pass
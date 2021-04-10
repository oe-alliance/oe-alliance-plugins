from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, eTimer
from Tools.BoundFunction import boundFunction
import os
try:
	from enigma import eMediaDatabase
	DPKG = True
except:
	DPKG = False


class PixmapLcd4linux(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.mTime = 0
		self.swap = False
		self.L4Ltimer = eTimer()
		if DPKG:
			self.L4Ltimer_conn = self.L4Ltimer.timeout.connect(self.changed)
		else:
			self.L4Ltimer.callback.append(self.changed)

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		self.changed((self.CHANGED_DEFAULT,))

	def changed(*s):
		sel = s[0]
		sel.L4Ltimer.stop()
		if os.path.isfile("/tmp/l4ldisplay.png"):
			try:
				mtime = os.stat("/tmp/l4ldisplay.png").st_mtime
				if sel.mTime != mtime:
					if sel.instance:
						if sel.swap:
							if not os.path.isfile("/tmp/l4ldisplaycp.png"):
								os.symlink("/tmp/l4ldisplay.png", "/tmp/l4ldisplaycp.png")
							sel.instance.setPixmapFromFile("/tmp/l4ldisplaycp.png")
						else:
							sel.instance.setPixmapFromFile("/tmp/l4ldisplay.png")
						sel.mTime = mtime
						sel.swap = not sel.swap
					else:
						sel.mTime = 0
			except:
				pass
			sel.L4Ltimer.start(200, True)

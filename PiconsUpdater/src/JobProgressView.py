
from Screens.Screen import Screen
from Components.Sources.StaticText import StaticText
from Components.ProgressBar import ProgressBar
from Components.ActionMap import ActionMap
from . import printToConsole

class JobProgressView(Screen):
	skin = '\n        <screen name="JobProgressView" position="390,178" size="500,210" zPosition="1" title="Job Progress" backgroundColor="#1A0F0F0F">\n            <eLabel name="new eLabel" position="0,0" zPosition="-2" size="500,210" backgroundColor="#20000000" transparent="0" />\n            <widget source="titleText" position="30,30" size="400,40" render="Label" font="Regular; 24" foregroundColor="#00ffffff" backgroundColor="#00000000" halign="center" transparent="1" />\n            <widget name="downloadProgress" position="30,90" size="440,30" borderWidth="2" borderColor="#cccccc" />\n            <widget source="downloadProgressText" position="100,140" size="300,30" render="Label" font="Regular; 20" foregroundColor="#00ffffff" backgroundColor="#00000000" halign="center" transparent="1" />\n        </screen>\n        '

	def __init__(self, session, title, onAbort=None, msgBoxID=None):
		Screen.__init__(self, session)
		self.onAbort = onAbort
		self.msgBoxID = msgBoxID
		self['titleText'] = StaticText('')
		self['titleText'].setText(title)
		self['downloadProgress'] = ProgressBar()
		self['downloadProgress'].setValue(0)
		self['downloadProgressText'] = StaticText('')
		self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.ok,
		 'cancel': self.cancel}, -1)

	def __del__(self):
		printToConsole('######## DESTRUCTOR: JobProgressView')

	def ok(self):
		pass

	def cancel(self):
		printToConsole('######## CANCEL')
		if self.onAbort is not None:
			self.onAbort()
		self.close(False)

	def setProgress(self, progress, progressText):
		self['downloadProgress'].setValue(progress)
		self['downloadProgressText'].setText(progressText)

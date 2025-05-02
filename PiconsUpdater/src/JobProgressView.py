# ENIGMA IMPORTS
from Screens.Screen import Screen
from Components.Sources.StaticText import StaticText
from Components.ProgressBar import ProgressBar
from Components.ActionMap import ActionMap

# PLUGIN IMPORTS
from . import printToConsole


class JobProgressView(Screen):
	skin = '''<screen name="JobProgressView" position="1250,10" size="650,110" zPosition="1" title="Job Progress" backgroundColor="#1A0F0F0F" flags="wfNoBorder">\n
				<widget source="titleText" position="25,0" size="600,30" render="Label" font="Regular; 24" foregroundColor="#00ffffff" backgroundColor="#00000000" halign="center" transparent="1" />\n            \n
				<eLabel name="new eLabel" position="0,0" zPosition="-2" size="650,110" backgroundColor="#20000000" transparent="0" />
				<widget source="textmessage" position="25,10" size="600,93" render="Label" font="Regular;25" foregroundColor="#00ffffff" backgroundColor="#00000000" halign="center" transparent="1" />
				<widget name="downloadProgress" position="25,30" size="597,25" borderWidth="2" borderColor="#001f6cff" foregroundColor="#001f6cff" backgroundColor="#10000000" />
				<widget source="downloadProgressText" position="25,30" size="597,25" render="Label" zPosition="1" font="Regular;20" foregroundColor="#00ffffff" backgroundColor="#00000000" halign="center" transparent="1" />
				<widget source="elaborateChannel" position="25,74" size="300,25" render="Label" zPosition="1" font="Regular;20" foregroundColor="#00ffffff" backgroundColor="#00000000" halign="center" transparent="1" />
				<widget source="downloadPChannel" position="326,74" size="300,25" render="Label" font="Regular;20" foregroundColor="#00ffffff" backgroundColor="#00000000" halign="center" transparent="1" />
			</screen>'''

	def __init__(self, session, title, onAbort=None, msgBoxID=None):
		Screen.__init__(self, session)
		self.onAbort = onAbort
		self.msgBoxID = msgBoxID
		self.ScaSum = None
		self['titleText'] = StaticText('')
		self['titleText'].setText(title)
		self['textmessage'] = StaticText('')
		self['downloadProgress'] = ProgressBar()
		self['downloadProgress'].setValue(0)
		self["downloadProgress"].hide()
		self['downloadProgressText'] = StaticText('')
		self['elaborateChannel'] = StaticText('')
		self['downloadPChannel'] = StaticText('')
		self['actions'] = ActionMap(
			['OkCancelActions'],
			{
				'ok': self.ok,
				'cancel': self.cancel
			},
			-1
		)

	def __del__(self):
		printToConsole('######## DESTRUCTOR: JobProgressView')

	def ok(self):
		pass
		# self.okClicked()

	def okClicked(self):
		if self.shown:
			self.shown = False
			self.instance.hide()
		else:
			self.instance.show()
			self.shown = True

	def cancel(self):
		printToConsole('######## CANCEL')
		if self.onAbort is not None:
			self.onAbort()
		self.close(False)
		"""
		if not self.shown:
			self.okClicked()
		else:
			printToConsole('######## CANCEL')
			if self.onAbort is not None:
				self.onAbort()
			self.close(False)
		return
		"""

	"""
	# def setProgress(self, progress, progressText):
		# self['downloadProgress'].setValue(progress)
		# self['downloadProgressText'].setText(progressText)
	"""
	"""
	# def setProgress(self, recvbytes, totalbytes):
		# self["downloadProgress"].show()
		# if totalbytes > 0:
			# self['downloadProgress'].value = int(100 * recvbytes // float(totalbytes))
			# self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (
				# recvbytes // 1024, totalbytes // 1024, 100 * recvbytes // float(totalbytes))
		# else:
			# self['downloadProgress'].value = 0
			# self['progresstext'].text = '0 of 0 kBytes (0.00%%)'
	"""

	def __downloadFinished(self, downloadsFinished):
		progress = int(100 * float(downloadsFinished) // float(self.totalDownloads))
		self.session.current_dialog.setProgress(progress, 'Downloading %d of %d Picons' % (downloadsFinished, self.totalDownloads))

	def setProgress(self, progress, progressText, elChan='', dwChan=''):
		self["downloadProgress"].show()
		self['downloadProgress'].setValue(progress)
		self['downloadProgressText'].setText(progressText)
		self['elaborateChannel'].setText(elChan)
		self['downloadPChannel'].setText(dwChan)
		"""
		try:
			self.session.summary.updateProgress(progress)
			self.session.summary.updateTitle(progressText)
		except:
			pass
			"""
	"""
	def createSummary(self):
		return ServiceScanSummary

	def hideSessionSummary(self):
		try:
			self.session.summary.setHideProgress()
		except:
			pass

	def setDialog(self):
		self.ScaSum = self.session.instantiateDialog(JobProgressView, self.title, None, msgBoxID=self.msgBoxID)
		self.ScaSum.show()
		return self.ScaSum
	"""

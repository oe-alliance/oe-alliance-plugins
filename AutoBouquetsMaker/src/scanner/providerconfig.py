class ProviderConfig():
	def __init__(self, value = ""):
		self.provider = ""
		self.area = ""
		self.flags = 0x1d	# default value mean main:yes, sections: yes, hd: yes, fta: yes
		self.customfilename = ""

		if len(value) > 0:
			chunks = value.split(":")
			if len(chunks) != 4:
				return
	
			try:
				self.provider = str(chunks[0].strip())
				self.area = str(chunks[1].strip())
				self.flags = int(chunks[2].strip())
				self.customfilename = str(chunks[3].strip())
			except Exception, e:
				return
	
	def isValid(self):
		return len(self.provider) > 0

	def getProvider(self):
		return self.provider

	def getArea(self):
		return self.area

	def getCustomFilename(self):
		return self.customfilename

	def setProvider(self, value):
		self.provider = value

	def setArea(self, value):
		self.area = value

	def setCustomFilename(self, value):
		self.customfilename = value

	def isMakeNormalMain(self):
		return (self.flags & 0x03) == 0x01

	def isMakeCustomMain(self):
		return (self.flags & 0x03) == 0x02

	def isMakeHDMain(self):
		return (self.flags & 0x03) == 0x03

	def isMakeFTAHDMain(self):
		return (self.flags & 0x40) == 0x40

	def isMakeSections(self):
		return (self.flags & 0x04) == 0x04

	def isMakeHD(self):
		return (self.flags & 0x08) == 0x08

	def isMakeFTA(self):
		return (self.flags & 0x10) == 0x10

	def isMakeFTAHD(self):
		return (self.flags & 0x80) == 0x80

	def isSwapChannels(self):
		return (self.flags & 0x20) == 0x20

	def setMakeNormalMain(self):
		self.flags = (self.flags & 0xbc) | 0x01

	def setMakeCustomMain(self):
		self.flags = (self.flags & 0xbc) | 0x02

	def setMakeHDMain(self):
		self.flags = (self.flags & 0xbc) | 0x03

	def setMakeFTAHDMain(self):
		self.flags = (self.flags & 0xbc) | 0x40

	def unsetMakeMain(self):
		self.flags &= 0xbc

	def unsetMakeFTAMain(self):
		self.flags &= 0xbc

	def unsetMakeFTAHDMain(self):
		self.flags &= 0xbc

	def setMakeSections(self):
		self.flags |= 0x04

	def unsetMakeSections(self):
		self.flags &= 0xfb

	def setMakeHD(self):
		self.flags |= 0x08

	def unsetMakeHD(self):
		self.flags &= 0xf7

	def setMakeFTA(self):
		self.flags |= 0x10

	def unsetMakeFTA(self):
		self.flags &= 0xef

	def setMakeFTAHD(self):
		self.flags |= 0x80

	def unsetMakeFTAHD(self):
		self.flags &= 0x7f

	def setSwapChannels(self):
		self.flags |= 0x20

	def unsetSwapChannels(self):
		self.flags &= 0xdf

	def unsetAllFlags(self):
		self.flags = 0x00

	def serialize(self):
		return "%s:%s:%d:%s" % (self.provider, self.area, self.flags, self.customfilename)


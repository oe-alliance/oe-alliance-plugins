#######################################################################
#
#    Vali's File-List with some extendet functions
#    based on FileList(Enigma-2)
#
#    Coded by Vali (c)2009-2011
#    Main idea and getTSLength/getTSInfo/Sort functions by DarkVolli
#    Support: www.dreambox-tools.info
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

from os import path as os_path, listdir, stat as os_stat
from Components.MenuList import MenuList
from Components.Harddisk import harddiskmanager
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, eServiceReference, eServiceCenter, gFont, iServiceInformation
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import SCOPE_PLUGINS, resolveFilename


def FileEntryComponent(name, absolute=None, isDir=False):
	res = [(absolute, isDir)]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 40, 2, 1000, 22, 0, RT_HALIGN_LEFT, name))
	png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/LCD4linux/data/dir.png")) if isDir else None
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 12, 3, 20, 20, png))
	return res


class FileList(MenuList):
	def __init__(self, directory, showDirectories=True, showFiles=True, showMountpoints=True, matchingPattern=None, useServiceRef=False, inhibitDirs=False, inhibitMounts=False, isTop=False, enableWrapAround=True, additionalExtensions=None):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.additional_extensions = additionalExtensions
		self.mountpoints = []
		self.current_directory = None
		self.current_mountpoint = None
		self.useServiceRef = useServiceRef
		self.showDirectories = showDirectories
		self.showMountpoints = showMountpoints
		self.showFiles = showFiles
		self.isTop = isTop
		self.matchingPattern = matchingPattern
		self.inhibitDirs = inhibitDirs or []
		self.inhibitMounts = inhibitMounts or []
		self.refreshMountpoints()
		direct = directory
		if directory.endswith("/"):
			se = directory
		else:
			se = os_path.basename(directory)
			direct = "%s/" % directory
		self.changeDir(direct, se)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(26)
		self.serviceHandler = eServiceCenter.getInstance()

	def refreshMountpoints(self):
		self.mountpoints = [os_path.join(p.mountpoint, "") for p in harddiskmanager.getMountedPartitions()]
		self.mountpoints.sort(reverse=True)

	def getMountpoint(self, file):
		file = os_path.join(os_path.realpath(file), "")
		for m in self.mountpoints:
			if file.startswith(m):
				return m
		return False

	def getMountpointLink(self, file):
		if os_path.realpath(file) == file:
			return self.getMountpoint(file)
		else:
			if file[-1] == "/":
				file = file[:-1]
			mp = self.getMountpoint(file)
			last = file
			file = os_path.dirname(file)
			while last != "/" and mp == self.getMountpoint(file):
				last = file
				file = os_path.dirname(file)
			return os_path.join(last, "")

	def getSelection(self):
		if self.l.getCurrentSelection() is None:
			return ""
		return self.l.getCurrentSelection()[0]

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return None if not l or l[0][1] is True else self.serviceHandler.info(l[0][0]).getEvent(l[0][0])

	def getFileList(self):
		return self.list

	def inParentDirs(self, dir, parents):
		dir = os_path.realpath(dir)
		for p in parents:
			if dir.startswith(p):
				return True
		return False

	def changeDir(self, directory, select=None):
		self.list = []
		if self.current_directory is None:
			self.current_mountpoint = self.getMountpointLink(directory) if directory and self.showMountpoints else None
		self.current_directory = directory
		directories = []
		files = []
		if directory is None and self.showMountpoints:
			for p in harddiskmanager.getMountedPartitions():
				path = os_path.join(p.mountpoint, "")
				if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
					self.list.append(FileEntryComponent(name=p.description, absolute=path, isDir=True))
			files = []
			directories = []
		elif directory is None:
			files = []
			directories = []
		elif self.useServiceRef:
			root = eServiceReference("2:0:1:0:0:0:0:0:0:0:%s" % directory)
			if self.additional_extensions:
				root.setName(self.additional_extensions)
			serviceHandler = eServiceCenter.getInstance()
			list = serviceHandler.list(root)
			while True:
				s = list.getNext()
				if not s.valid():
					del list
					break
				if s.flags & s.mustDescent:
					directories.append(s.getPath())
				else:
					files.append(s)
			directories.sort()
			files.sort()
		else:
			if os_path.exists(directory):
				try:
					files = listdir(directory)
				except Exception:
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if os_path.isdir("%s%s" % (directory, x)):
						directories.append("%s%s/" % (directory, x))
						files.remove(x)
		if directory is not None and self.showDirectories and not self.isTop:
			if directory == self.current_mountpoint is not None and self.showMountpoints is not None:
				self.list.append(FileEntryComponent(name="<%s>" % _("List of Storage Devices"), absolute=None, isDir=True))
			elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
				self.list.append(FileEntryComponent(name="<%s>" % _("Parent Directory"), absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))
		if self.showDirectories:
			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					self.list.append(FileEntryComponent(name=name, absolute=x, isDir=True))
		if self.showFiles:
			nx = 0
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
				else:
					path = "%s%s" % (directory, x)
					name = x
					nx = None
				EXext = os_path.splitext(path)[1]
				EXext = EXext.replace(".", "")
				EXext = EXext.lower()
				if (EXext == ""):
					EXext = "nothing"
				if (self.matchingPattern is None) or (EXext in self.matchingPattern):
					if nx is None:
						self.list.append(FileEntryComponent(name=name, absolute=x, isDir=False))
					else:
						res = [(x, False)]
						res.append((eListboxPythonMultiContent.TYPE_TEXT, 40, 2, 1000, 22, 0, RT_HALIGN_LEFT, "%s [%s]" % (name, self.getTSLength(path))))
						self.list.append(res)
		self.l.setList(self.list)
		if select is not None:
			i = 0
			self.moveToIndex(0)
			select2 = select
			if select.endswith("/"):
				select2 = os_path.basename(select[:-1])
			for x in self.list:
				p = x[0][0]
				if isinstance(p, eServiceReference):
					p = p.getPath()
				if p == select or p == select2:
					self.moveToIndex(i)
				i += 1

	def getCurrentDirectory(self):
		return self.current_directory

	def canDescent(self):
		return False if self.getSelection() == "" else self.getSelection()[1]

	def descent(self):
		if self.getSelection() != "":
			se = ""
			if self.current_directory is not None:
				se = self.current_directory if self.current_directory.endswith("/") else os_path.basename(self.current_directory)
			self.changeDir(self.getSelection()[0], select=se)

	def getFilename(self):
		if self.getSelection() == "":
			return ""
		x = self.getSelection()[0]
		if isinstance(x, eServiceReference):
			x = x.getPath()
		return x

	def getServiceRef(self):
		if self.getSelection() == "":
			return None
		x = self.getSelection()[0]
		return x if isinstance(x, eServiceReference) else None

	def execBegin(self):
		harddiskmanager.on_partition_list_change.append(self.partitionListChanged)

	def execEnd(self):
		harddiskmanager.on_partition_list_change.remove(self.partitionListChanged)

	def refresh(self):
		se = ""
		if self.getFilename() != "":
			se = self.getFilename() if self.getFilename().endswith("/") else os_path.basename(self.getFilename())
		self.changeDir(self.current_directory, se)

	def partitionListChanged(self, action, device):
		self.refreshMountpoints()
		if self.current_directory is None:
			self.refresh()

	def getTSInfo(self, path):
		if path.endswith(".ts"):
			serviceref = eServiceReference("1:0:0:0:0:0:0:0:0:0:%s" % path)
			if not serviceref.valid():
				return None
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(serviceref)
			if info is not None:
				txt = info.getName(serviceref)
				description = info.getInfoString(serviceref, iServiceInformation.sDescription)
				if not txt.endswith(".ts"):
					return "%s - %s" % (txt, description) if description != "" else txt
				else:
					evt = info.getEvent(serviceref)
					return "%s - %s" % (evt.getEventName(), evt.getShortDescription()) if evt else None

	def getTSLength(self, path):
		tslen = ""
		if path.endswith(".ts"):
			serviceref = eServiceReference("1:0:0:0:0:0:0:0:0:0:%s" % path)
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(serviceref)
			tslen = info.getLength(serviceref)
			return "%d:%02d" % (tslen / 60, tslen % 60) if tslen > 0 else ""

	def byNameFunc(self, a, b):
		return cmp(b[0][1], a[0][1]) or cmp(a[1][7], b[1][7])

	def sortName(self):
		self.list.sort(self.byNameFunc)
		self.l.setList(self.list)
		self.moveToIndex(0)

	def byDateFunc(self, a, b):
		try:
			stat1 = os_stat(self.current_directory + a[0][0])
			stat2 = os_stat(self.current_directory + b[0][0])
		except Exception:
			return 0
		return cmp(b[0][1], a[0][1]) or cmp(stat2.st_ctime, stat1.st_ctime)

	def sortDate(self):
		self.list.sort(self.byDateFunc)
		self.l.setList(self.list)
		self.moveToIndex(0)

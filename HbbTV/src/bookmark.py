import vbcfg

class BookmarkData:
	def __init__(self, _id, _title, _url, _parent, _type):
		self.mId 	= _id
		self.mTitle 	= _title
		self.mUrl 	= _url
		self.mParent 	= _parent
		self.mType	= _type
	def dump(self, _intent='  '):
		print "%s-> %d, %s, %s, %d, %d" % (_intent, self.mId, self.mTitle, self.mUrl, self.mParent, self.mType)

class CategoryData:
	def __init__(self, _id, _name):
		self.mId 	= _id
		self.mName	= _name
		self.mBookmarks	= {}

	def setBookmarks(self, _bookmarks):
		self.mBookmarks = _bookmarks

	def appendBookmark(self, _bookmark):
		self.mBookmarks[_bookmark.mId] = _bookmark

	def dump(self):
		print "  -> %d, %s" % (self.mId, self.mName)
		for key in self.mBookmarks.iterkeys():
			self.mBookmarks[key].dump('      ')

import ConfigParser
class SimpleConfigParser:
	def __init__(self):
		self.mFileName = None
		self.mConfig = None
		self.mCategoryCurrentIdx = 0
		self.mBookmarkCurrentIdx = 0
		self.mDataValid = False
		self.mPopulateValid = False

	def _read(self):
		if self.mDataValid:
			return
		self.mConfig.read(self.mFileName)

		self.mCategoryCurrentIdx = self.getNumber('__SYS__', 'category_current_idx')
		self.mBookmarkCurrentIdx = self.getNumber('__SYS__', 'bookmark_current_idx')
		self.mDataValid = True

	def _save(self):
		with open(self.mFileName, 'wb') as bookmarkFile:
			self.mConfig.write(bookmarkFile)
		self.mDataValid = False
		self.mPopulateValid = False

	def _del(self, _section, _option=None):
		if _option is None:
			if not self.exist(_section):
				return
			self.mConfig.remove_section(_section)
			return
		if not self.exist(_section, _option):
			return
		self.mConfig.remove_option(_section, _option)

	def _get(self, _section, _option, _default):
		try:
			data = self.mConfig.get(_section, _option)
		except Exception, e:
			vbcfg.ERR(e)
			return _default
		else :	return data

	def _set(self, _section, _option, _value):
		self.mConfig.set(_section, _option, _value)

	def exist(self, _section, _option=None):
		if _option is None:
			return self.mConfig.has_section(_section)
		return self.mConfig.has_option(_section, _option)

	def setNumber(self, _section, _option, _value):
		self._set(_section, _option, str(_value))

	def setString(self, _section, _option, _value):
		self._set(_section, _option, _value)

	def getNumber(self, _section, _option, _default=0):
		return int(self._get(_section, _option, _default))

	def getString(self, _section, _option, _default=''):
		return self._get(_section, _option, _default)

	def delOption(self, _section, _option):
		self._del(_section, _option)

	def addSection(self, _section):
		self.mConfig.add_section(_section)

	def delSection(self, _section):
		self._del(_section)

	def init(self, _fileName):
		self.mFileName = _fileName
		self.mConfig = ConfigParser.RawConfigParser()
		if self.mConfig is None:
			return False
		self._read()
		return True

class BookmarkManager(SimpleConfigParser):
	_instance = None
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self, _dbFileName):
		SimpleConfigParser.__init__(self)
		self.mBookmarkRoot = None
		self.mDebugEnable = True

		import os
		if not os.path.exists(_dbFileName):
			f = file('/proc/stb/info/vumodel')
			model = f.read().strip()
			f.close()
			manualmode = (model == "solo2" or model == "duo2" or model == "solose" or model == "zero")

			os.system('echo "[__SYS__]" > %s'%(_dbFileName))
			os.system('echo "category_current_idx = 1" >> %s'%(_dbFileName))
			if manualmode :
				os.system('echo "bookmark_current_idx = 2" >> %s'%(_dbFileName))
			else:	os.system('echo "bookmark_current_idx = 1" >> %s'%(_dbFileName))
			os.system('echo "[c-1]" >> %s'%(_dbFileName))
			os.system('echo "id = 1" >> %s'%(_dbFileName))
			os.system('echo "name = My favorite" >> %s'%(_dbFileName))
			os.system('echo "[b-1]" >> %s'%(_dbFileName))
			os.system('echo "url = http://www.vuplus.com/" >> %s'%(_dbFileName))
			os.system('echo "id = 1" >> %s'%(_dbFileName))
			os.system('echo "parent = 1" >> %s'%(_dbFileName))
			os.system('echo "title = Vuplus Home" >> %s'%(_dbFileName))
			os.system('echo "type = 0" >> %s'%(_dbFileName))
			if manualmode :
				os.system('echo "[b-2]" >> %s'%(_dbFileName))
				os.system('echo "url = file:///usr/local/manual/main.html" >> %s'%(_dbFileName))
				os.system('echo "id = 2" >> %s'%(_dbFileName))
				os.system('echo "parent = 1" >> %s'%(_dbFileName))
				os.system('echo "title = User Manual" >> %s'%(_dbFileName))
				os.system('echo "type = 1" >> %s'%(_dbFileName))
		self.init(_dbFileName)

	def message(self, format, params=None):
		if not self.mDebugEnable:
			return
		if params is None:
			vbcfg.DEBUG(format)
		else:
			vbcfg.DEBUG(format % (params))

	def getBookmark(self, _title):
		self.populate()
		for key in self.mBookmarkRoot.iterkeys():
			for key2 in self.mBookmarkRoot[key].mBookmarks.iterkeys():
				if self.mBookmarkRoot[key].mBookmarks[key2].mTitle == _title:
					return 'b-%d' % (self.mBookmarkRoot[key].mBookmarks[key2].mId)
		return None

	def addBookmark(self, _title, _url, _parent, _type):
		if self.getBookmark(_title) is not None:
			return False
		i = self.mBookmarkCurrentIdx + 1
		s = "b-%d" % (i,)
		self.message("add bookmark : %s, %s, %d, %d", (_title, _url, _parent, _type,))

		self.mConfig.add_section(s)
		self.setNumber(s, 'id', i)
		self.setString(s, 'title', _title)
		self.setString(s, 'url', _url)
		self.setNumber(s, 'parent', _parent)
		self.setNumber(s, 'type', _type)
		self.setNumber('__SYS__', 'bookmark_current_idx', i)
		self._save()

		return True

	def deleteBookmark(self, _id):
		self.populate()
		self.message("delete bookmark : %d", (_id,))
		self.delSection('b-%d' % (_id,))
		self._save()

	def updateBookmark(self, _bookmark):
		self.populate()
		s = "b-%d" % (_bookmark.mId)
		self.message("update bookmark : %s, %s, %d, %d", (_bookmark.mTitle, _bookmark.mUrl, _bookmark.mParent, _bookmark.mType,))
		self.setString(s, 'title', _bookmark.mTitle)
		self.setString(s, 'url', _bookmark.mUrl)
		self.setNumber(s, 'parent', _bookmark.mParent)
		self.setNumber(s, 'type', _bookmark.mType)
		self._save()

	def getCategory(self, _name):
		self.populate()
		for key in self.mBookmarkRoot.iterkeys():
			if self.mBookmarkRoot[key].mName == _name:
				return 'c-%d' % (self.mBookmarkRoot[key].mId)
		return None

	def addCategory(self, _name):
		if self.getCategory(_name) is not None:
			return False
		self.message("add category : %s", (_name,))
		i = self.mCategoryCurrentIdx + 1
		s = "c-%d" % (i)

		self.mConfig.add_section(s)
		self.setNumber(s, 'id', i)
		self.setNumber(s, 'name', _name)
		self.setNumber('__SYS__', 'category_current_idx', i)
		self._save()

		return True

	def deleteCategory(self, _id):
		self.populate()
		self.message("delete category : %d", (_id,))
		try:
			for key in self.mBookmarkRoot[_id].mBookmarks.iterkeys():
				self.delSection('b-%d' % (key,))
		except: pass
		self.delSection('c-%d' % (_id,))
		self._save()

	def updateCategory(self, _category):
		self.populate()
		self.message("update category : %s", (_category.mName,))
		s = "c-%d" % (_category.mId)
		self.setNumber(s, 'name', _category.mName)
		self._save()

	def populate(self):
		cx, bx = 0, 0
		categoryList = {}
		self.message("populate : %d, %d", (self.mPopulateValid, self.mDataValid))

		self._read()
		if self.mPopulateValid:
			return

		while cx <= self.mCategoryCurrentIdx:
			s = 'c-%d' % (cx,)
			i = self.getNumber(s, 'id', -1)
			if i != -1:
				n = self.getString(s, 'name')
				categoryList[i] = CategoryData(i, n)
			cx += 1
		sorted(categoryList)
		while bx <= self.mBookmarkCurrentIdx:
			s = 'b-%d' % (bx,)
			i = self.getNumber(s, 'id', -1)
			if i != -1:
				t = self.getString(s, 'title')
				u = self.getString(s, 'url')
				p = self.getNumber(s, 'parent')
				e = self.getNumber(s, 'type')
				try:
					categoryList[p].appendBookmark(BookmarkData(i, t, u, p, e))
				except Exception, e: self._del(s)
			bx += 1
		for key in categoryList.iterkeys():
			sorted(categoryList[key].mBookmarks)
		self.mBookmarkRoot = categoryList
		self.mPopulateValid = True
		self.dump()

	def getBookmarkRoot(self):
		self.populate()
		return self.mBookmarkRoot

	def dump(self):
		if not self.mDebugEnable:
			return
		self.populate()
		print "-- snapshot --"
		for key in self.mBookmarkRoot.iterkeys():
			self.mBookmarkRoot[key].dump()
		print "--------------"

	@staticmethod
	def getInstance():
		return BookmarkManager(vbcfg.PLUGINROOT + "/bookmark.ini")



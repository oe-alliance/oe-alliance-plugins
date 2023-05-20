from os import listdir, walk, access, W_OK, statvfs
from os.path import getmtime, join, basename, isfile, dirname, isdir, realpath, ismount, islink, exists
from re import sub
from unicodedata import normalize

def getCleanFileName(value):
#   Converts to lowercase, removes non-word characters (alphanumerics and underscores) and converts spaces to hyphens.
#	Also strips leading and trailing whitespace. Function is from django
#	https://github.com/django/django/blob/9108696a7553123f57c5d42f9c4a90cad44532f4/django/utils/text.py#L417
	value = normalize('NFKD', value)
	value = sub('[+]', '___plus___', value)
	value = sub('[&]', '___and___', value)
	value = sub('[^\\w\\s-]', '', value).strip().lower()
	value = sub('[-\\s]+', '-', value)
	return value.encode('utf-8')

def getOldestFile(path, fileExtensions=None):
#	get oldest file from folder
#	fileExtensions as tuple. example: ('.txt', '.png')
	files = getFilesFromPath(path)
	if not files:
		return None
	files = __filterFileListByFileExtension(files, fileExtensions)
	oldestFile = min(files, key=getmtime)
	return oldestFile


def getFiles(path, fileExtensions=None):
#	get file list as an array sorted by date. The oldest first
#	fileExtensions as tuple. example: ('.txt', '.png')
	files = getFilesFromPath(path)
	if not files:
		return None
	files = __filterFileListByFileExtension(files, fileExtensions)
	files.sort(key=lambda s: getmtime(join(path, s)))
	return files

def getFilesFromPath(path):
	return [join(path, fname) for fname in listdir(path)]

def getFilesWithNameKey(path, excludedDirNames=None, excludeDirs=None):
#	get recursive all files from given path
	rs = {}
	for dirPath, dirNames, fileNames in walk(path):
		for fileName in fileNames:
			if excludedDirNames is not None and basename(dirPath) in excludedDirNames:
				continue
			fullFilePath = join(dirPath, fileName)
			skipFile = False
			pathToCheck = dirPath if dirPath.endswith('/') else "%s/" % dirPath
			if excludeDirs is not None:
				for excludeDir in excludeDirs:
					if pathToCheck[:len(excludeDir)] == excludeDir:
						skipFile = True
						break
			if skipFile == True:
				continue
			rs[join(dirPath.replace(path, ''), fileName)] = fullFilePath
	return rs

def pathIsWriteable(path):
	if isfile(path):
		path = dirname(path)
	return True if isdir(path) and is_mount(path) and access(path, W_OK) else False

def is_mount(path):
	return isdir(mountpoint(path))

def mountpoint(path, first=True):
	if first:
		path = realpath(path)
	if ismount(path) or len(path) == 0:
		return path
	return mountpoint(dirname(path), False)

def removeSymbolicLinks(pathList):
	tmpExcludedDirs = []
	for folder in pathList:
		if islink(folder) == False:
			tmpExcludedDirs.append(folder)
	return tmpExcludedDirs

def getFreeDiskspace(path):
	if exists(path):
		stat = statvfs(path)
		free = (stat.f_bavail if stat.f_bavail != 0 else stat.f_bfree) * stat.f_bsize / 1024 / 1024
		return free
	return 0

def getFreeDiskspaceText(path):
	free = getFreeDiskspace(path)
	return '%d GB' % (free / 1024) if free >= 10240 else '%d MB' % free

def reachedLimit(path, limit):
	free = getFreeDiskspace(path)
	return True if limit > free / 1024 else False

def __filterFileListByFileExtension(files, fileExtensions):
#	fileExtensions as tuple. example: ('.txt', '.png')
	if fileExtensions is not None:
		files = list(filter(lambda s: s.lower().endswith(fileExtensions), files))
	return files

# Standard library
from os import listdir, walk, access, W_OK, statvfs
from os.path import getmtime, join, basename, isfile, dirname, isdir, realpath, relpath, ismount, islink, exists
from re import sub
from unicodedata import normalize


TMP_PICON_PATH = '/tmp/piconsupdater'
TMP_PATH = join(TMP_PICON_PATH, 'picons-all')


def correctedFileName(s):  # remove forbidden characters
	return s.replace('>', '').replace('<', '').replace('|', '').replace(':', '').replace('*', '').replace('=', '').replace('\\', '').replace('/', '').replace('?', '')


def xCxName(serviceName):
	return correctedFileName(serviceName.replace('\xc2\x86', '').replace('\xc2\x87', '').replace('/', '_'))


def normalizeServiceName(serviceName):
	for ch in [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('Ä', 'Ae'), ('Ö', 'Oe'), ('Ü', 'Ue'), ('ß', 'ss'), ('*', 'star'), ('+', 'plus'), ('&', 'and')]:
		serviceName = serviceName.replace(ch[0], ch[1])
	return sub('[^a-z0-9]', '', serviceName.lower())


def fallBackName(serviceName):
	res, ok = serviceName, True
	for x in 'hd,uhd,austria,oesterreich,österreich,deutschland,nord,sued,süd'.split(','):
		if res.lower().endswith(' ' + x):
			res = res[:-(len(x) + 1)]
	for x in 'WDR,NDR,BR Fernsehen,SR,SWR,MDR,RTL,SAT.1,RBB,rbb,VOX,ORF2,ORF1,BBC,CNN'.split(','):
		if res.startswith(x + ' '):
			for chSub in 'gold,emotion,ii,2,zwei'.split(','):
				if res.lower().find(' ' + chSub) >= 0:
					ok = False
			if ok:
				res = x
	if res == serviceName:
		res = ''
	return res


def reducedName(byName):
	fallback = fallBackName(byName.upper())
	if fallback:
		byName = fallback
	return normalizeServiceName(byName)


def generateInteroperableNames(serviceName, vtiMode=1):
	try:
		res = []
		comp = fb = ''  # example Nick/MTV+ HD
		if vtiMode:
			serviceNamexCx = xCxName(serviceName)  # Nick_MTV+ HD
		else:
			serviceNamexCx = serviceName   # Nick/MTV+ HD

		corr = correctedFileName(serviceName)   # NickMTV+ HD
		if (corr != serviceName):
			res.append(corr)
			serviceName = corr

		comp = normalizeServiceName(serviceName)   # nickmtvplushd
		if comp and (comp != serviceName):
			res.append(comp)

		fb = fallBackName(serviceNamexCx)   # Nick_MTV+
		if fb and (fb != serviceNamexCx):
			res.append(fb)

		if serviceNamexCx != serviceName:
			fb = fallBackName(serviceName)  # NickMTV+
			if fb and (fb != serviceName):
				res.append(fb)

		fb2 = normalizeServiceName(fb)  # nickmtvplus
		if fb2 and (fb2 != fb):
			res.append(fb2)
	except:
		pass
	return res


def piconByName(channelName, read=0):
	name = xCxName(channelName)
	piconPath = TMP_PATH
	if exists(join(piconPath, name)):
		return name

	newName = normalizeServiceName(channelName)
	if newName and (newName != channelName) and exists(join(piconPath, newName)):
		return newName

	if read:
		nameList = generateInteroperableNames(channelName)
		for x in nameList:
			if x and exists(join(piconPath, x)):
				return x

	if newName and (newName != channelName):
		name = newName

	return name


"""
# # for future version
# def getCleanFileName(value):
	# if config.plugins.PiconsUpdater.getfiltername:
		# getCleanFileNameAdv(value)
	# else:
		# getCleanFileNameAlt(value)
	# # return


# def getCleanFileName(value):
	# getCleanFileNameAlt(value)
	# return
"""


def getCleanFileNameAdv(value):
	"""
	Converts to lowercase, removes non-word characters (alphanumerics and
	underscores) and converts spaces to hyphens. Also strips leading and
	trailing whitespace.
	"""
	print('getCleanFileNameAdv Value Original is:', value)

	# Normalize and remove non-ASCII characters
	value = normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')

	# Remove non-alphanumeric characters and excess spaces
	value = sub(r'[^\w\s-]', '', value).strip().lower()

	# value = sub('[-\\s]+', '-', value)

	# Remove consecutive spaces and hyphens
	value = sub(r'[-\s]+', '', value)

	# Replace specific patterns with 'dvbs' or 'dvbt'
	if 'vsid0x' in value[5:13] or 'hsid0x' in value[5:13]:
		value = 'dvbs'
	elif value[:5].isdigit() and ('v' in value[5:] or 'h' in value[5:]):
		value = 'dvbs'
	elif 'sid0x' in value[6:13]:
		value = 'dvbt'

	# Apply the piconByName function (presumably defined elsewhere)
	value = piconByName(value)
	print('getCleanFileNameAdv Value Final is:', value)

	return value


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


def getOldestFile(path, fileExtensions=None):  # get oldest file from folder fileExtensions as tuple. example: ('.txt', '.png')
	files = getFilesFromPath(path)
	if not files:
		return None

	if fileExtensions:
		files = filterFileListByFileExtension(files, fileExtensions)

	if not files:
		return None

	oldestFile = min(files, key=getmtime)
	return oldestFile


def getFiles(path, fileExtensions=None):  # get file list as an array sorted by date. The oldest first fileExtensions as tuple. example: ('.txt', '.png')
	files = getFilesFromPath(path)
	if not files:
		return None
	if fileExtensions:
		files = filterFileListByFileExtension(files, fileExtensions)
	files.sort(key=lambda s: getmtime(join(path, s)))
	return files


def getFilesFromPath(path):
	return [join(path, fname) for fname in listdir(path)]


def getFilesWithNameKey(path, excludedDirNames=None, excludeDirs=None):  # get recursive all files from given path
	if not exists(path):
		raise ValueError(f"The path {path} does not exist.")
	rs = {}
	for dirPath, dirNames, fileNames in walk(path):
		if excludedDirNames is not None and basename(dirPath) in excludedDirNames:
			continue
		for fileName in fileNames:
			fullFilePath = join(dirPath, fileName)
			skipFile = False
			pathToCheck = dirPath if dirPath.endswith('/') else f"{dirPath}/"
			if excludeDirs is not None:
				for excludeDir in excludeDirs:
					if pathToCheck.startswith(excludeDir):
						skipFile = True
						break
			if skipFile:
				continue
			relativePath = join(relpath(dirPath, path), fileName)
			rs[relativePath] = fullFilePath
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
		if islink(folder) is False:
			tmpExcludedDirs.append(folder)
	return tmpExcludedDirs


def getFreeDiskspace(path):
	if exists(path):
		stat = statvfs(path)
		free = (stat.f_bavail if stat.f_bavail != 0 else stat.f_bfree) * stat.f_bsize // 1024 / 1024
		return free
	return 0


def getFreeDiskspaceText(path):
	free = getFreeDiskspace(path)
	return '%d GB' % (free // 1024) if free >= 10240 else '%d MB' % free


def reachedLimit(path, limit):
	free = getFreeDiskspace(path)
	return True if limit > free // 1024 else False


def filterFileListByFileExtension(files, fileExtensions):  # fileExtensions as tuple. example: ('.txt', '.png')
	if fileExtensions is not None:
		files = list(filter(lambda s: s.lower().endswith(fileExtensions), files))
	return files

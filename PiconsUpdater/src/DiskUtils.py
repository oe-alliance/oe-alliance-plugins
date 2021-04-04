# -*- coding: utf-8 -*-
import os
import unicodedata
import re
import six


def getCleanFileName(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    
    Function is from django
    
    https://github.com/django/django/blob/9108696a7553123f57c5d42f9c4a90cad44532f4/django/utils/text.py#L417
    """
    if six.PY2:
        value = six.text_type(value, errors='replace')
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[+]', '___plus___', value)
    value = re.sub('[&]', '___and___', value)
    value = re.sub('[^\\w\\s-]', '', value).strip().lower()
    value = re.sub('[-\\s]+', '-', value)
    return six.ensure_str(value)


def getOldestFile(path, fileExtensions=None):
    """
    get oldest file from folder
    
    fileExtensions as tuple. example: ('.txt', '.png')
    """
    files = getFilesFromPath(path)
    if not files:
        return None
    files = __filterFileListByFileExtension(files, fileExtensions)
    oldestFile = min(files, key=os.path.getmtime)
    return oldestFile


def getFiles(path, fileExtensions=None):
    """
    get file list as an array
    sorted by date.
    The oldest first
    
    fileExtensions as tuple. example: ('.txt', '.png')
    """
    files = getFilesFromPath(path)
    if not files:
        return None
    files = __filterFileListByFileExtension(files, fileExtensions)
    files.sort(key=lambda s: os.path.getmtime(os.path.join(path, s)))
    return files


def getFilesFromPath(path):
    return [os.path.join(path, fname) for fname in os.listdir(path)]


def getFilesWithNameKey(path, excludedDirNames=None, excludeDirs=None):
    """
    get recursive all files from given path
    """
    rs = {}
    for dirPath, dirNames, fileNames in os.walk(path):
        for fileName in fileNames:
            if excludedDirNames is not None and os.path.basename(dirPath) in excludedDirNames:
                continue
            fullFilePath = os.path.join(dirPath, fileName)
            skipFile = False
            if dirPath.endswith('/'):
                pathToCheck = dirPath
            else:
                pathToCheck = dirPath + '/'
            if excludeDirs is not None:
                for excludeDir in excludeDirs:
                    if pathToCheck[:len(excludeDir)] == excludeDir:
                        skipFile = True
                        break

            if skipFile == True:
                continue
            rs[os.path.join(dirPath.replace(path, ''), fileName)] = fullFilePath

    return rs


def pathIsWriteable(path):
    if os.path.isfile(path):
        path = os.path.dirname(path)
    if os.path.isdir(path) and ismount(path) and os.access(path, os.W_OK):
        return True
    else:
        return False


def ismount(path):
    return os.path.isdir(mountpoint(path))


def mountpoint(path, first=True):
    if first:
        path = os.path.realpath(path)
    if os.path.ismount(path) or len(path) == 0:
        return path
    return mountpoint(os.path.dirname(path), False)


def removeSymbolicLinks(pathList):
    tmpExcludedDirs = []
    for folder in pathList:
        if os.path.islink(folder) == False:
            tmpExcludedDirs.append(folder)

    return tmpExcludedDirs


def getFreeDiskspace(path):
    if os.path.exists(path):
        stat = os.statvfs(path)
        free = (stat.f_bavail if stat.f_bavail != 0 else stat.f_bfree) * stat.f_bsize / 1024 / 1024
        return free
    return 0


def getFreeDiskspaceText(path):
    free = getFreeDiskspace(path)
    if free >= 10240:
        free = '%d GB' % (free / 1024)
    else:
        free = '%d MB' % free
    return free


def reachedLimit(path, limit):
    free = getFreeDiskspace(path)
    if limit > free / 1024:
        return True
    else:
        return False


def __filterFileListByFileExtension(files, fileExtensions):
    """
    fileExtensions as tuple. example: ('.txt', '.png')
    """
    if fileExtensions is not None:
        files = list(filter(lambda s: s.lower().endswith(fileExtensions), files))
    return files

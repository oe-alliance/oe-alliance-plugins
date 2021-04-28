from __future__ import absolute_import
from __future__ import print_function
import os
import xml.dom.minidom
import re
from enigma import iServiceInformation

from . import vbcfg

import six


RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
				u'|' + \
				u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
				(six.unichr(0xd800), six.unichr(0xdbff), six.unichr(0xdc00), six.unichr(0xdfff),
				six.unichr(0xd800), six.unichr(0xdbff), six.unichr(0xdc00), six.unichr(0xdfff),
				six.unichr(0xd800), six.unichr(0xdbff), six.unichr(0xdc00), six.unichr(0xdfff))

DUMPBIN = vbcfg.PLUGINROOT + "/dumpait"


class eAITSectionReader:
	def __init__(self, demux, pmtid, sid):
		self.mVuplusBox = False
		self.mInfo = None
		self.mAppList = []
		self.mDocument = None
		self.mCommand = "%s --demux=%s --pmtid=%x --serviceid=%x" % (DUMPBIN, demux, pmtid, sid)

	def __text(self, nodelist):
		rc = []
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc.append(node.data)
		return ''.join(rc)

	def __item(self, application, name):
		for item in application.getElementsByTagName(name):
			return self.__text(item.childNodes)
		return None

	def __application(self, application):
		item = {}

		if self.mVuplusBox:
			item["name"] = str(application[1])
			item["url"] = str(application[2])
			item["control"] = int(application[0])
			item["orgid"] = int(application[3])
			item["appid"] = int(application[4])
			item["profile"] = int(application[5])
		else:
			item["name"] = str(self.__item(application, "name"))
			item["url"] = str(self.__item(application, "url"))
			item["control"] = int(self.__item(application, "control"))
			item["orgid"] = int(self.__item(application, "orgid"))
			item["appid"] = int(self.__item(application, "appid"))
			item["profile"] = int(self.__item(application, "profile"))
		return item

	def doParseApplications(self):
		l = []

		if self.mVuplusBox:
			for application in self.mInfo.getInfoObject(iServiceInformation.sHBBTVUrl):
				item = self.__application(application)
				l.append(item)
		else:
			for application in self.mDocument.getElementsByTagName("application"):
				item = self.__application(application)
				l.append(item)
		self.mAppList = l

	def getApplicationList(self):
		return self.mAppList

	def doOpen(self, info, is_vuplusbox):
		if is_vuplusbox:
			self.mVuplusBox = is_vuplusbox
			self.mInfo = info
			return True

		document = ""
		try:
			document = os.popen(self.mCommand).read()
		except Exception as ErrMsg:
			vbcfg.ERR(ErrMsg)
			return False
		if len(document) == 0:
			return False
		document = re.sub(RE_XML_ILLEGAL, "?", document)
		document = re.sub("&", "+", document)
		# document = document.decode("cp1252").encode("utf-8") # Py3 does not have str.decode()
		document = "<URL>" + document + "</URL>"
		try:
			self.mDocument = xml.dom.minidom.parseString(document)
		except Exception as ErrMsg:
			vbcfg.ERR("XML parse: %s" % ErrMsg)
			return False
		return True

	def doDump(self):
		for x in self.getApplicationList():
			print("Name  :", x["name"])
			print("URL   :", x["url"])
			print("OrgID :", x["orgid"])
			print("AppID :", x["appid"])
			print("Control Code :", x["control"])
			print("Profile Code :", x["profile"])
			print("")


def unit_test(demux, pmtid, sid):
	reader = eAITSectionReader(demux, pmtid, sid)
	if reader.doOpen():
		reader.doParseApplications()
		reader.doDump()
	else:
		vbcfg.ERR("no data!!")

#unit_test('0', 0x17d4, 0x2b66)

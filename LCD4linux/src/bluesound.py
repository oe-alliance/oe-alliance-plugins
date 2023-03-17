# -*- coding: utf-8 -*-
from six.moves.urllib.request import urlopen
from xml.etree.ElementTree import fromstring


def parseXmlToJson(xml):
	response = {}
	for child in list(xml):
		if len(list(child)) > 0:
			response[child.tag] = parseXmlToJson(child)
		else:
			response[child.tag] = child.text or ''
	return response


class BlueSound:
	def __init__(self, ip):
		self.IP = ip
		self.baseUrl = "http://" + ip + ":11000/"

	def Urlget(self, url):
		f = urlopen(url, timeout=1)
		fr = f.read()
		fc = f.code
		f.close()
		return (fr, fc)

	def getStatus(self):
		try:
			content, resp = self.Urlget(self.baseUrl + "Status")
			if resp == 200:
				xml = fromstring(content)
				r = parseXmlToJson(xml)
				return r
			else:
				return {}
		except:
			print("Bluesound Error")
			from traceback import format_exc
			print("Error: %s" % format_exc())
			return {}

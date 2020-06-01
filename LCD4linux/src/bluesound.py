# -*- coding: utf-8 -*-
from __future__ import print_function
try:
	import urllib2
	url2 = True
except:
	url2 = False
	import urllib
from xml.etree import ElementTree as ET

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
		if url2:
			f = urllib2.urlopen(url, timeout = 1)
		else:
			f = urllib.urlopen(url)
		fr = f.read()
		fc = f.code
		f.close()
		return (fr, fc)

	def getStatus(self):
		try:
			content, resp=self.Urlget(self.baseUrl + "Status")
			if resp == 200:
				xml = ET.fromstring(content)
				r = parseXmlToJson(xml)
				return r
			else:
				return {}
		except:
			print("Bluesound Error")
			from traceback import format_exc
			print("Error:", format_exc()) 
			return {}

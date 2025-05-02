# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
try:
	import simplejson
except Exception as e:
	import json as simplejson
from six.moves.urllib.request import urlopen


class YMC:
	def __init__(self, ip, L4logE):
		self.IP = ip
		self.L4logE = L4logE

	def Urlget(self, url):
		f = urlopen(url, timeout=1)
		fr = f.read()
		fc = f.code
		f.close()
		return (fr, fc)

	def getPlayInfo(self):
		try:
			content, resp = self.Urlget("http://%s/YamahaExtendedControl/v1/netusb/getPlayInfo" % self.IP)
			return simplejson.loads(content) if resp == 200 else {}

		except Exception as e:
			self.L4logE("YMC Error: %s" % e)
			return {}

	def getStatus(self):
		try:
			content, resp = self.Urlget("http://%s/YamahaExtendedControl/v1/main/getStatus" % self.IP)
			return simplejson.loads(content) if resp == 200 else {}
		except Exception as e:
			self.L4logE("YMC Error: %s" % e)
			return {}

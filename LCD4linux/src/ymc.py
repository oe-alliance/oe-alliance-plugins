# -*- coding: utf-8 -*-
try:
	import simplejson
except:
	import json as simplejson
try:
	import urllib2
	url2 = True
except:
	url2 = False
	import urllib

class YMC:
	def __init__(self,ip):
		self.IP = ip
	def Urlget(self, url):
		if url2:
			f = urllib2.urlopen(url, timeout = 1)
		else:
			f = urllib.urlopen(url)
		fr = f.read()
		fc = f.code
		f.close()
		return (fr, fc)

	def getPlayInfo(self):
		try:
			content,resp=self.Urlget("http://%s/YamahaExtendedControl/v1/netusb/getPlayInfo" % self.IP)
			if resp == 200:
				r=simplejson.loads(content)
				return r
			else:
				return {}
		except:
			print "YMC Error"
			return {}

	def getStatus(self):
		try:
			content,resp=self.Urlget("http://%s/YamahaExtendedControl/v1/main/getStatus" % self.IP)
			if resp == 200:
				r=simplejson.loads(content)
				return r
			else:
				return {}
		except:
			print "YMC Error"
			return {}

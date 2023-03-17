# -*- coding: utf-8 -*-
from __future__ import division, absolute_import
from os.path import isfile, getmtime
from six import ensure_str, ensure_binary
from twisted.web import resource
from .plugin import *


class LCD4linuxweb(resource.Resource):

	title = "LCD4Linux Webinterface"
	isLeaf = False

	def __init__(self):
		self.HREF = "href=\"/lcd4linux/config\""

	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')
#		rendering server response
		w = ""
		command = req.args.get(b"width", None)
		if command is not None:
			cmd = ensure_str(command[0])
			w += " width=\"%s\"" % cmd
		command = req.args.get(b"hight", None)
		if command is not None:
			cmd = ensure_str(command[0])
			w += " height=\"%s\"" % cmd
		html = "<html>"
		html += "<head>\n"
		html += "<meta http-equiv=\"Content-Language\" content=\"de\">\n"
		html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\">\n"
		html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"expires\" content=\"0\">\n"
		html += "<link rel=\"shortcut icon\" href=\"/lcd4linux/data/favicon.png\">"
		if LCD4linux.WebIfType.value == "1":
			JavaRefresh = ""
			html += "<meta http-equiv=\"refresh\" content=\"%s\">\n" % LCD4linux.WebIfRefresh.value
		else:
			if LCD4linux.WebIfType.value == "0":
				html += "<meta http-equiv=\"refresh\" content=\"300\">\n"
			JavaRefresh = " id=\"reloader%%d\" onload=\"setTimeout('document.getElementById(\\'reloader%%d\\').src=\\'/lcd4linux/%%s?\\'+new Date().getTime()', %d)\"" % (int(LCD4linux.WebIfRefresh.value) * 1000)
		html += "<title>LCD4linux</title>\n"
		html += "</head>"
		html += "<body bgcolor=\"%s\" text=\"#FFFFFF\">\n" % ("#666666" if getConfigMode() == True else "#000000")
		html += "<form method=\"POST\" action=\"--WEBBOT-SELF--\">\n"
		datei = req.args.get(b"file", None)
		if datei is not None:
			datei[0] = datei[0].decode("utf-8")
			if isfile("%s%s" % (getTMPL(), datei[0])):
				t = getmtime("%s%s" % (getTMPL(), datei[0]))
				JR = "" if JavaRefresh == "" else JavaRefresh % (1, 1, datei[0])
				html += "<a %s><img border=\"0\" src=\"/lcd4linux/%s?%d\" %s %s></a> \n" % (self.HREF, datei[0], t, JR, w)
		elif isfile("%sdpf.jpg" % getTMPL()):
			t = getmtime("%sdpf.jpg" % getTMPL())
			JR = "" if JavaRefresh == "" else JavaRefresh % (2, 2, "dpf.jpg")
			html += "<a %s><img border=\"0\" src=\"/lcd4linux/dpf.jpg?%d\" %s %s></a> \n" % (self.HREF, t, JR, w)
		elif isfile("%sdpf.png" % getTMPL()):
			t = getmtime("%sdpf.png" % getTMPL())
			JR = "" if JavaRefresh == "" else JavaRefresh % (3, 3, "dpf.png")
			html += "<a %s><img border=\"0\" src=\"/lcd4linux/dpf.png?%d\" %s %s></a> \n" % (self.HREF, t, JR, w)
		elif isfile("%sdpf2.jpg" % getTMPL()):
			t = getmtime("%sdpf2.jpg" % getTMPL())
			JR = "" if JavaRefresh == "" else JavaRefresh % (4, 4, "dpf2.jpg")
			html += "<a %s><img border=\"0\" src=\"/lcd4linux/dpf2.jpg?%d\" %s %s></a> \n" % (self.HREF, t, JR, w)
		elif isfile("%sdpf2.png" % getTMPL()):
			t = getmtime("%sdpf2.png" % getTMPL())
			JR = "" if JavaRefresh == "" else JavaRefresh % (5, 5, "dpf2.png")
			html += "<a %s><img border=\"0\" src=\"/lcd4linux/dpf2.png?%d\" %s %s></a> \n" % (self.HREF, t, JR, w)
		elif isfile("%sdpf3.jpg" % getTMPL()):
			t = getmtime("%sdpf3.jpg" % getTMPL())
			JR = "" if JavaRefresh == "" else JavaRefresh % (6, 6, "dpf3.jpg")
			html += "<a %s><img border=\"0\" src=\"/lcd4linux/dpf3.jpg?%d\" %s %s></a> \n" % (self.HREF, t, JR, w)
		elif isfile("%sdpf3.png" % getTMPL()):
			t = getmtime("%sdpf3.png" % getTMPL())
			JR = "" if JavaRefresh == "" else JavaRefresh % (7, 7, "dpf3.png")
			html += "<a %s><img border=\"0\" src=\"/lcd4linux/dpf3.png?%d\" %s %s></a> \n" % (self.HREF, t, JR, w)
		else:
			html += "<a style=\"color:#FFCC00\" %s>no Picture .... Config-WebIF</a>" % self.HREF
		html += "</body>\n"
		html += "</html>\n"
		html += "</form>\n"
		return ensure_binary(html)


class LCD4linuxwebView(LCD4linuxweb):
	def __init__(self):
		self.HREF = ""

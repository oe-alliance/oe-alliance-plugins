from .. import log
import os, codecs, re
import xml.dom.minidom

class Tools():
	def parseXML(self, filename):
		try:
			tool = open(filename, "r")
		except Exception, e:
			print>>log, "[Tools] Cannot open %s: %s" % (filename, e)
			return None

		try:
			dom = xml.dom.minidom.parse(tool)
		except Exception, e:
			print>>log, "[Tools] XML parse error (%s): %s" % (filename, e)
			tool.close()
			return None

		tool.close()
		return dom
		
	def customLCN(self, services, section_identifier, current_bouquet_key):
		customLCN_tmp = []
		custom_dir = os.path.dirname(__file__) + "/../custom"
		skipextrachannels = 0

		# Write Example custom file	
		if current_bouquet_key.startswith('sd'):		
			xmlout = open(custom_dir + "/EXAMPLE_sd_" + section_identifier + "_CustomLCN.xml", "w")
		else:
			xmlout = open(custom_dir + "/EXAMPLE_hd_" + section_identifier + "_CustomLCN.xml", "w")
		xmlout.write("<custom>\n\t<include>yes</include>\n\t<lcnlist>\n")
		for number in services["video"]:
			servicename = unicode(services["video"][number]["service_name"], errors='ignore')
			xmlout.write("\t\t<configuration lcn=\"%d\" channelnumber=\"%d\" description=\"%s\"></configuration>\n" % (
				number,
				number,
				servicename.replace("&","+")
				))
		xmlout.write("\t</lcnlist>\n</custom>\n")
		xmlout.close()
		
		# Read custom file
		if current_bouquet_key.startswith('sd'):
			customfile = custom_dir + "/sd_" + section_identifier + "_CustomLCN.xml"
		else:
			customfile = custom_dir + "/hd_" + section_identifier + "_CustomLCN.xml"
		dom = self.parseXML(customfile)
		if dom is None:
			print>>log, "[Tools] No custom file."
		elif dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "custom":
			j = 0
			customlcndict = {}
			for node in dom.documentElement.childNodes:
				if node.nodeType != node.ELEMENT_NODE:
					continue
				if node.tagName == "include":
					node.normalize()
					if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
						if node.childNodes[0].data.encode("utf-8") == 'no':
							skipextrachannels = 1
				if node.tagName == "lcnlist":
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "configuration":
							customlcndict[j] = {}
							for i in range(0, node2.attributes.length):
								if node2.attributes.item(i).name == "lcn":
									customlcndict[j]["lcn"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "channelnumber":
									customlcndict[j]["channelnumber"] = int(node2.attributes.item(i).value)
							j += 1
			
			# Find new services for log file
			newservices = []
			for number in services["video"]:
				oldservices = 0
				for key in customlcndict:
					if number == customlcndict[key]["channelnumber"]:
						oldservices = 1
				if oldservices == 0:
					newservices.append(number)
			print>>log, "[Tools] New services %s" % (str(newservices))
			
			lastlcn = 1
			for number in customlcndict:
				if customlcndict[number]["lcn"] > lastlcn:
					lastlcn = customlcndict[number]["lcn"]
				
			# service video swap.
			video_services = {}
			video_services_tmp = {}
			video_services_tmp = services["video"]
			video_tmp ={}
			for key in video_services_tmp:
				servicefound = 0
				video_tmp = video_services_tmp[key]
				number = video_tmp["number"]
				for key2 in customlcndict:
					if number == customlcndict[key2]["channelnumber"]:
						video_tmp["logical_channel_number"] = customlcndict[key2]["lcn"]
						video_tmp["number"] = customlcndict[key2]["lcn"]
						video_services[customlcndict[key2]["lcn"]] = video_tmp
						servicefound = 1
				# Service not in custom lcn file, add at end of list.
				if servicefound == 0 and skipextrachannels == 0:
					video_services[lastlcn + 1] = video_tmp
					lastlcn += 1
					
			services["video"] = video_services

		return services

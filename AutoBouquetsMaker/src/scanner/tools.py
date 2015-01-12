from .. import log
import os, codecs, re
import xml.dom.minidom

class Tools():
	def parseXML(self, filename):
		try:
			tool = open(filename, "r")
		except Exception, e:
			#print>>log, "[Tools] Cannot open %s: %s" % (filename, e)
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

		# Write Example TV custom file	
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
		
		# Write Example Radio custom file	
		if current_bouquet_key.startswith('sd'):		
			xmlout = open(custom_dir + "/EXAMPLE_sd_" + section_identifier + "_CustomradioLCN.xml", "w")
		else:
			xmlout = open(custom_dir + "/EXAMPLE_hd_" + section_identifier + "_CustomradioLCN.xml", "w")
		xmlout.write("<custom>\n\t<include>yes</include>\n\t<lcnlist>\n")
		for number in services["radio"]:
			servicename = unicode(services["radio"][number]["service_name"], errors='ignore')
			xmlout.write("\t\t<configuration lcn=\"%d\" channelnumber=\"%d\" description=\"%s\"></configuration>\n" % (
				number,
				number,
				servicename.replace("&","+")
				))
		xmlout.write("\t</lcnlist>\n</custom>\n")
		xmlout.close()
		
		# Read custom TV file
		if current_bouquet_key.startswith('sd'):
			customfile = custom_dir + "/sd_" + section_identifier + "_CustomLCN.xml"
		else:
			customfile = custom_dir + "/hd_" + section_identifier + "_CustomLCN.xml"
		dom = self.parseXML(customfile)
		if dom is None:
			print>>log, "[Tools] No custom TV LCN file."
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
			print>>log, "[Tools] New TV services %s" % (str(newservices))
			
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

		# Read custom radio file
		if current_bouquet_key.startswith('sd'):
			customfile = custom_dir + "/sd_" + section_identifier + "_CustomradioLCN.xml"
		else:
			customfile = custom_dir + "/hd_" + section_identifier + "_CustomradioLCN.xml"
		dom = self.parseXML(customfile)
		if dom is None:
			print>>log, "[Tools] No custom radio LCN file."
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
			for number in services["radio"]:
				oldservices = 0
				for key in customlcndict:
					if number == customlcndict[key]["channelnumber"]:
						oldservices = 1
				if oldservices == 0:
					newservices.append(number)
			print>>log, "[Tools] New radio services %s" % (str(newservices))
			
			lastlcn = 1
			for number in customlcndict:
				if customlcndict[number]["lcn"] > lastlcn:
					lastlcn = customlcndict[number]["lcn"]
				
			# service radio swap.
			radio_services = {}
			radio_services_tmp = {}
			radio_services_tmp = services["radio"]
			radio_tmp ={}
			for key in radio_services_tmp:
				servicefound = 0
				radio_tmp = radio_services_tmp[key]
				number = radio_tmp["number"]
				for key2 in customlcndict:
					if number == customlcndict[key2]["channelnumber"]:
						radio_tmp["logical_channel_number"] = customlcndict[key2]["lcn"]
						radio_tmp["number"] = customlcndict[key2]["lcn"]
						radio_services[customlcndict[key2]["lcn"]] = radio_tmp
						servicefound = 1
				# Service not in custom lcn file, add at end of list.
				if servicefound == 0 and skipextrachannels == 0:
					radio_services[lastlcn + 1] = radio_tmp
					lastlcn += 1
					
			services["radio"] = radio_services
			
		return services
		
	def customtransponder(self, provider_key):
		customtransponderdict = {}
		custom_dir = os.path.dirname(__file__) + "/../custom"

		# Read custom file
		print>>log, "[Tools] Transponder provider name", provider_key
		customfile = custom_dir + "/" + provider_key + "_Custom_transponder.xml"
		dom = self.parseXML(customfile)
		if dom is None:
			print>>log, "[Tools] No custom transponder file."
		elif dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "custom":
			j = 0
			for node in dom.documentElement.childNodes:
				if node.nodeType != node.ELEMENT_NODE:
					continue
				if node.tagName == "transponderlist":
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "configuration":
							customtransponderdict[j] = {}
							for i in range(0, node2.attributes.length):
								if node2.attributes.item(i).name == "key":
									customtransponderdict[j]["key"] = node2.attributes.item(i).value
								elif node2.attributes.item(i).name == "transport_stream_id":
									customtransponderdict[j]["transport_stream_id"] = int(node2.attributes.item(i).value, 16)
								elif node2.attributes.item(i).name == "frequency":
									customtransponderdict[j]["frequency"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "bandwidth":
									customtransponderdict[j]["bandwidth"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "code_rate_hp":
									customtransponderdict[j]["code_rate_hp"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "code_rate_lp":
									customtransponderdict[j]["code_rate_lp"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "modulation":
									customtransponderdict[j]["modulation"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "transmission_mode":
									customtransponderdict[j]["transmission_mode"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "guard_interval":
									customtransponderdict[j]["guard_interval"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "hierarchy":
									customtransponderdict[j]["hierarchy"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "inversion":
									customtransponderdict[j]["inversion"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "flags":
									customtransponderdict[j]["flags"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "system":
									customtransponderdict[j]["system"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "plpid":
									customtransponderdict[j]["plpid"] = int(node2.attributes.item(i).value)
							j += 1

		return customtransponderdict
		
	def clearsections(self, services, sections, bouquettype, servicetype):
		# bouquettype = HD, FTAHD, FTA
		# servicetype = video, radio
		if len(sections) == 1:
			return sections
			
		active_sections = {}
		for key in services[servicetype].keys():
			if ("FTA" not in bouquettype or services[servicetype][key]["free_ca"] == 0) and ("HD" not in bouquettype or services[servicetype][key]["service_type"] >= 17):
				section_number = max((x for x in sections if int(x) <= key))
				if section_number not in active_sections:
					active_sections[section_number] = sections[section_number]
		if active_sections:
			return active_sections
		return sections
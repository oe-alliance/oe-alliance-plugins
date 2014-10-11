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
		
	def customLCN(self, services, preferred_order_tmp, higher_number, section_identifier):
		customLCN_tmp = []
		custom_dir = os.path.dirname(__file__) + "/../custom"
		
		# Write Example custom file		
		logout = open(custom_dir + "/EXAMPLE_" + section_identifier + "_CustomLCN.xml", "w")
		logout.write("<custom>\n\t<lcnlist>\n")
		for number in preferred_order_tmp:
			if number in services["video"]:
					logout.write("\t\t<configuration lcn=\"%d\" channelnumber=\"%d\" description=\"%s\"></configuration>\n" % (
							number,
							number,
							(services["video"][number]["service_name"]).replace("&","+")
						))
		logout.write("\t</lcnlist>\n</custom>\n")
		logout.close()
		
		# Read custom file
		customfile = custom_dir + "/" + section_identifier + "_CustomLCN.xml"
		dom = self.parseXML(customfile)
		if dom is None:
			print>>log, "[Tools] No custom file."
		elif dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "custom":
			j = 0
			customlcndict = {}
			for node in dom.documentElement.childNodes:
				if node.nodeType != node.ELEMENT_NODE:
					continue
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
			
			# Find new services
			newservices = []
			for number in services["video"]:
				oldservices = 0
				for key in customlcndict:
					if number == customlcndict[key]["channelnumber"]:
						oldservices = 1
				if oldservices == 0:
					newservices.append(number)
			print>>log, "[Tools] New services %s" % (str(newservices))
			
			# Write customlcn_tmp file
			x = 1
			for key in customlcndict:
				lcnfound = 0
				while x <= higher_number and lcnfound == 0:
					if customlcndict[key]["lcn"] == x:
						customLCN_tmp.append(customlcndict[key]["channelnumber"])
						x += 1
						lcnfound = 1
					else:
						customLCN_tmp.append(higher_number + 1)
						x += 1
						
			# Add new services at end of list.
			for i in range(0, len(newservices)):
				customLCN_tmp.append(newservices[i])
					
		return customLCN_tmp

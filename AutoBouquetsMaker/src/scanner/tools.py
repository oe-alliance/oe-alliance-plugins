from .. import log
import os, codecs, re
import xml.dom.minidom
from Components.config import config
from dvbscanner import DvbScanner

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
		custom_dir = os.path.dirname(__file__) + "/../custom"
		is_sorted = False

		for number in services["video"]:
			if number == services["video"][number]["service_id"]:
				continue
			is_sorted = True
			break

		for type in ["video", "radio"]:
			skipextrachannels = 0

			# Write Example CustomLCN file
			xml_out_list = []
			xml_out_list.append("<custom>\n\t<include>yes</include>\n\t<lcnlist>\n")
			numbers = sorted(services[type].keys())
			for number in numbers:
				servicename = unicode(services[type][number]["service_name"], errors='ignore')
				xml_out_list.append("\t\t<configuration lcn=\"%d\" channelnumber=\"%d\" description=\"%s\"></configuration>\n" % (
					number,
					number,
					servicename.replace("&","+")
					))
			xml_out_list.append("\t</lcnlist>\n</custom>\n")
			xmlout = open(custom_dir + "/EXAMPLE_" + ("sd" if current_bouquet_key.startswith('sd') else "hd") + "_" + section_identifier + "_Custom" + ("radio" if type == "radio" else "") + "LCN.xml", "w")
			xmlout.write(''.join(xml_out_list))
			xmlout.close()
			del xml_out_list

			# Read CustomLCN file
			customfile = custom_dir + "/" + ("sd" if current_bouquet_key.startswith('sd') else "hd") + "_" + section_identifier + "_Custom" + ("radio" if type == "radio" else "") + "LCN.xml"
			dom = self.parseXML(customfile)
			if dom is None:
				print>>log, "[Tools] No custom " + type + " LCN file for " + section_identifier + "."
			elif dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "custom":
				customlcndict = {}
				sort_order = [] # to process this file top down
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
								lcn = 0
								channelnumber = 0
								for i in range(0, node2.attributes.length):
									if node2.attributes.item(i).name == "lcn":
										lcn = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "channelnumber":
										channelnumber = int(node2.attributes.item(i).value)
								if channelnumber and lcn:
									customlcndict[channelnumber] = lcn
									if channelnumber in services[type]:
										sort_order.append(channelnumber)
				
				temp_services = {}
				extra_services = {}
				
				# add channels not in the CustomLCN file to the sort list.
				for number in sorted(services[type].keys()):
					if number not in sort_order:
						sort_order.append(number)

				# add services from CustomLCN file
				for number in sort_order:
					if number in customlcndict and customlcndict[number] not in temp_services:
						temp_services[customlcndict[number]] = services[type][number]
					else:
						extra_services[number] = services[type][number]

				# add services not in CustomLCN file to correct lcn positions if slots are vacant
				if is_sorted:
					for number in extra_services.keys():
						if number not in temp_services: # CustomLCN has priority
							temp_services[number] = extra_services[number]
							del extra_services[number]

				#add any remaining services to the end of list
				if is_sorted or skipextrachannels == 0:
					lastlcn = len(temp_services) and max(temp_services.keys())
					newservices = []
					for number in self.sortServicesAlpha(extra_services):
						temp_services[lastlcn + 1] = extra_services[number]
						lastlcn += 1
						newservices.append(number)
					print>>log, "[Tools] New " + type + " services %s" % (str(newservices))

				services[type] = temp_services

		return services
		
	def sortServicesAlpha(self, services):
		# services is a dict with LCNs as keys
		# returns keys, sorted flat alphabetic by service name (or interactive name if it is set).
		sort_list = []
		for lcn in services:
			if "interactive_name" in services[lcn]:
				sort_list.append((lcn, re.sub('^(?![a-z])', 'zzzzz', services[lcn]['interactive_name'].lower())))
			else:
				sort_list.append((lcn, re.sub('^(?![a-z])', 'zzzzz', services[lcn]['service_name'].lower())))
		sort_list = sorted(sort_list, key=lambda listItem: listItem[1])
		return [i[0] for i in sort_list]

	def customMix(self, services, section_identifier, sections, providerConfig):
		custom_dir = os.path.dirname(__file__) + "/../custom"
		customfile = custom_dir + "/" + section_identifier + "_CustomMix.xml"
		customised = {"video":{}, "radio":{}}
		for type in ["video", "radio"]:
			for number in services[section_identifier][type]:
				customised[type][number] = services[section_identifier][type][number]
		hacks = ""
		dom = self.parseXML(customfile)
		if dom is None:
			print>>log, "[Tools] No CustomMix file for " + section_identifier + "."
		elif dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "custommix":
			for node in dom.documentElement.childNodes:
				if node.nodeType != node.ELEMENT_NODE:
					continue
				if node.tagName == "inserts":
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "insert":
							provider = ''
							source = ''
							target = ''
							for i in range(0, node2.attributes.length):
								if node2.attributes.item(i).name == "provider":
									provider = node2.attributes.item(i).value
								elif node2.attributes.item(i).name == "source":
									source = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "target":
									target = int(node2.attributes.item(i).value)
							if provider and source and target and provider in services and source in services[provider]["video"]:
								customised["video"][target] = services[provider]["video"][source]

				elif node.tagName == "deletes":
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "delete":
							target = ''
							for i in range(0, node2.attributes.length):
								if node2.attributes.item(i).name == "target":
									target = int(node2.attributes.item(i).value)
									if target and target in customised["video"]:
										del customised["video"][target]
										
				elif node.tagName == "sections":
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "section":
							number = -1
							for i in range(0, node2.attributes.length):
								if node2.attributes.item(i).name == "number":
									number = int(node2.attributes.item(i).value)
								if number == -1:
									continue

								node2.normalize()
								if len(node2.childNodes) == 1 and node2.childNodes[0].nodeType == node2.TEXT_NODE:
									sections[number] = node2.childNodes[0].data.encode("utf-8")
							
				elif node.tagName == "hacks":
					node.normalize()
					for i in range(0, len(node.childNodes)):
						if node.childNodes[i].nodeType == node.CDATA_SECTION_NODE:
							hacks = node.childNodes[i].data.strip()

			if len(hacks) > 0:
				exec(hacks)

		return customised, sections

	def customtransponder(self, provider_key, bouquet_key):
		customtransponders = []
		providers_dir = os.path.dirname(__file__) + "/../providers"

		# Read custom file
		print>>log, "[Tools] Transponder provider name", provider_key
		providerfile = providers_dir + "/" + provider_key + ".xml"
		dom = self.parseXML(providerfile)
		if dom is None:
			print>>log, "[Tools] Cannot read custom transponders from provider file."
		elif dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "provider":
			for node in dom.documentElement.childNodes:
				if node.nodeType != node.ELEMENT_NODE:
					continue
				elif node.tagName == "customtransponders":
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "customtransponder":
							customtransponder = {} # add some defaults. Key, frequency and TSID must come from the provider file.
							customtransponder["bandwidth"] = 0
							customtransponder["code_rate_hp"] = 5
							customtransponder["code_rate_lp"] = 5
							customtransponder["modulation"] = 0
							customtransponder["transmission_mode"] = 3
							customtransponder["guard_interval"] = 4
							customtransponder["hierarchy"] = 4
							customtransponder["inversion"] = 2
							customtransponder["flags"] = 0
							customtransponder["system"] = 0
							customtransponder["plpid"] = 0
							for i in range(0, node2.attributes.length):
								if node2.attributes.item(i).name == "key":
									customtransponder["key"] = node2.attributes.item(i).value
								elif node2.attributes.item(i).name == "transport_stream_id":
									customtransponder["transport_stream_id"] = int(node2.attributes.item(i).value, 16)
								elif node2.attributes.item(i).name == "frequency":
									customtransponder["frequency"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "bandwidth":
									customtransponder["bandwidth"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "code_rate_hp":
									customtransponder["code_rate_hp"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "code_rate_lp":
									customtransponder["code_rate_lp"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "modulation":
									customtransponder["modulation"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "transmission_mode":
									customtransponder["transmission_mode"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "guard_interval":
									customtransponder["guard_interval"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "hierarchy":
									customtransponder["hierarchy"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "inversion":
									customtransponder["inversion"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "flags":
									customtransponder["flags"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "system":
									customtransponder["system"] = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "plpid":
									customtransponder["plpid"] = int(node2.attributes.item(i).value)
							if "key" in customtransponder and customtransponder["key"] == bouquet_key and "transport_stream_id" in customtransponder and "frequency" in customtransponder:
								customtransponders.append(customtransponder)
			if len(customtransponders) > 0:
				print>>log, "[Tools] %d custom transponders found for that region." % len(customtransponders)
		return customtransponders

	def favourites(self, path, services, providers, providerConfigs, bouquetsOrder):
		custom_dir = os.path.dirname(__file__) + "/../custom"
		provider_key = "favourites"
		customised = {"video":{}, "radio":{}}
		name = ""
		prefix = ""
		sections = {}
		bouquets = {"main":1, "sections":1}
		area_key = ""
		bouquets_to_hide = []
		bouquetsToHide = []
		channels_on_top = [[]]
		swaprules = []
		placement = 0
		hacks = ""

		# Read favourites file
		dom = self.parseXML(custom_dir + "/favourites.xml")
		if dom is None:
			print>>log, "[Tools] No favorite.xml file"
		elif dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "favourites":
			for node in dom.documentElement.childNodes:
				if node.nodeType != node.ELEMENT_NODE:
					continue

				if node.tagName == "name":
					node.normalize()
					if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
						name = node.childNodes[0].data.encode("utf-8")

				elif node.tagName == "sections":
					sections = {}
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "section":
							number = -1
							for i in range(0, node2.attributes.length):
								if node2.attributes.item(i).name == "number":
									number = int(node2.attributes.item(i).value)
								if number == -1:
									continue

								node2.normalize()
								if len(node2.childNodes) == 1 and node2.childNodes[0].nodeType == node2.TEXT_NODE:
									sections[number] = node2.childNodes[0].data.encode("utf-8")

				elif node.tagName == "inserts":
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "insert":
							provider = ''
							source = ''
							target = ''
							for i in range(0, node2.attributes.length):
								if node2.attributes.item(i).name == "provider":
									provider = node2.attributes.item(i).value
								elif node2.attributes.item(i).name == "source":
									source = int(node2.attributes.item(i).value)
								elif node2.attributes.item(i).name == "target":
									target = int(node2.attributes.item(i).value)
							if provider and source and target and provider in services and source in services[provider]["video"]:
								customised["video"][target] = services[provider]["video"][source]

				elif node.tagName == "bouquets":
					for node2 in node.childNodes:
						if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "main":
							node2.normalize()
							if len(node2.childNodes) == 1 and node2.childNodes[0].nodeType == node2.TEXT_NODE and node2.childNodes[0].data != "1":
								bouquets["main"] = 0
						elif node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "sections":
							node2.normalize()
							if len(node2.childNodes) == 1 and node2.childNodes[0].nodeType == node2.TEXT_NODE and node2.childNodes[0].data != "1":
								bouquets["sections"] = 0
								
				elif node.tagName == "placement":
					node.normalize()
					if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
						placement = min(int(node.childNodes[0].data) -1, len(bouquetsOrder))
						if placement < 0:
							placement = 0
							
				elif node.tagName == "hacks":
					node.normalize()
					for i in range(0, len(node.childNodes)):
						if node.childNodes[i].nodeType == node.CDATA_SECTION_NODE:
							hacks = node.childNodes[i].data.strip()

			if len(hacks) > 0:
				exec(hacks)

			if len(customised["video"]) > 0:
				providers[provider_key] = {}
				providers[provider_key]["name"] = name
				providers[provider_key]["bouquets"] = area_key
				providers[provider_key]["protocol"] = 'nolcn'
				providers[provider_key]["swapchannels"] = []
				providers[provider_key]["sdchannelsontop"] = []
				providers[provider_key]["hdchannelsontop"] = []
				providers[provider_key]["sections"] = sections
				if config.autobouquetsmaker.addprefix.value:
					prefix = name
				services[provider_key] = customised
				bouquetsOrder.insert(placement, provider_key)

				from providerconfig import ProviderConfig
				providerConfigs[provider_key] = ProviderConfig("%s::0:" % provider_key)
				if bouquets["main"] == 1:
					providerConfigs[provider_key].setMakeNormalMain()
				if bouquets["sections"] == 1:
					providerConfigs[provider_key].setMakeSections()
				from bouquetswriter import BouquetsWriter
				BouquetsWriter().buildBouquets(path, providerConfigs[provider_key], services[provider_key], sections, provider_key, swaprules, channels_on_top, bouquets_to_hide, prefix)
			else:
				print>>log, "[Tools] Favourites list is zero length."

	def clearsections(self, services, sections, bouquettype, servicetype):
		# bouquettype = HD, FTAHD, FTA, ALL
		# servicetype = video, radio
		if len(sections) == 1:
			return sections

		active_sections = {}
		for key in services[servicetype].keys():
			if (("FTA" not in bouquettype or services[servicetype][key]["free_ca"] == 0) and ("HD" not in bouquettype or (services[servicetype][key]["service_type"] in DvbScanner.VIDEO_ALLOWED_TYPES and services[servicetype][key]["service_type"] >= 17))) or 'ALL' in bouquettype:
				section_number = max((x for x in sections if int(x) <= key))
				if section_number not in active_sections:
					active_sections[section_number] = sections[section_number]
		if active_sections:
			return active_sections
		return sections
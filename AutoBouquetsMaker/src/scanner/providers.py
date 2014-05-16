from .. import log
import os
import xml.dom.minidom

class Providers():
	VALID_PROTOCOLS = [ "sky", "lcn", "fastscan", "freesat", "lcnbat" ]
	def parseXML(self, filename):
		try:
			provider = open(filename, "r")
		except Exception, e:
			print>>log, "[Providers] Cannot open %s: %s" % (filename, e)
			return None

		try:
			dom = xml.dom.minidom.parse(provider)
		except Exception, e:
			print>>log, "[Providers] XML parse error (%s): %s" % (filename, e)
			provider.close()
			return None

		provider.close()
		return dom

	def read(self):
		providers_dir = os.path.dirname(__file__) + "/../providers"
		providers = {}

		for filename in os.listdir(providers_dir):
			if filename[-4:] != ".xml":
				continue

			dom = self.parseXML(providers_dir + "/" + filename)
			if dom is None:
				continue

			provider = {}
			provider["key"] = filename[:-4]
			provider["swapchannels"] = []
			provider["channelsontop"] = []
			if dom.documentElement.nodeType == dom.documentElement.ELEMENT_NODE and dom.documentElement.tagName == "provider":
				for node in dom.documentElement.childNodes:
					if node.nodeType != node.ELEMENT_NODE:
						continue

					if node.tagName == "name":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
							provider["name"] = node.childNodes[0].data.encode("utf-8")
					elif node.tagName == "streamtype":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
							provider["streamtype"] = node.childNodes[0].data.encode("utf-8")
					elif node.tagName == "protocol":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE and node.childNodes[0].data in self.VALID_PROTOCOLS:
							provider["protocol"] = node.childNodes[0].data
							if provider["protocol"] not in ("sky", "freesat") and provider["streamtype"] not in ("dvbc", "dvbt"):	# prepare an empty dictionary for bouquets
								provider["bouquets"] = {}
							else:
								provider["namespace"] = 0
					elif node.tagName == "namespace":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
							provider["namespace"] = int(node.childNodes[0].data, 16)
					elif node.tagName == "transponder":
						transponder = {}
						transponder["nit_pid"] = 0x10
						transponder["nit_current_table_id"] = 0x40
						transponder["nit_other_table_id"] = 0x41
						transponder["sdt_pid"] = 0x11
						transponder["sdt_current_table_id"] = 0x42
						transponder["sdt_other_table_id"] = 0x46
						transponder["bat_pid"] = 0x11
						transponder["bat_table_id"] = 0x4a
						transponder["fastscan_pid"] = 0x00			# no default value
						transponder["fastscan_table_id"] = 0x00		# no default value
						for i in range(0, node.attributes.length):
							if node.attributes.item(i).name == "frequency":
								transponder["frequency"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "symbol_rate":
								transponder["symbol_rate"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "polarization":
								transponder["polarization"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "fec_inner":
								transponder["fec_inner"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "orbital_position":
								transponder["orbital_position"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "inversion":
								transponder["inversion"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "system":
								transponder["system"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "modulation":
								transponder["modulation"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "roll_off":
								transponder["roll_off"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "pilot":
								transponder["pilot"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "bandwidth":
								transponder["bandwidth"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "code_rate_hp":
								transponder["code_rate_hp"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "code_rate_lp":
								transponder["code_rate_lp"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "transmission_mode":
								transponder["transmission_mode"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "guard_interval":
								transponder["guard_interval"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "hierarchy":
								transponder["hierarchy"] = int(node.attributes.item(i).value)
							elif node.attributes.item(i).name == "nit_pid":
								transponder["nit_pid"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "nit_current_table_id":
								transponder["nit_current_table_id"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "nit_other_table_id":
								transponder["nit_other_table_id"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "sdt_pid":
								transponder["sdt_pid"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "sdt_current_table_id":
								transponder["sdt_current_table_id"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "sdt_other_table_id":
								transponder["sdt_other_table_id"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "bat_pid":
								transponder["bat_pid"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "bat_table_id":
								transponder["bat_table_id"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "fastscan_pid":
								transponder["fastscan_pid"] = int(node.attributes.item(i).value, 16)
							elif node.attributes.item(i).name == "fastscan_table_id":
								transponder["fastscan_table_id"] = int(node.attributes.item(i).value, 16)

						if len(transponder.keys()) in (20, 16):
							provider["transponder"] = transponder

					elif node.tagName == "bouquettype":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
							provider["bouquettype"] = node.childNodes[0].data.encode("utf-8")

					elif node.tagName == "netid":
						node.normalize()
						if len(node.childNodes) == 1 and node.childNodes[0].nodeType == node.TEXT_NODE:
							provider["netid"] = node.childNodes[0].data.encode("utf-8")

					elif node.tagName == "dvbsconfigs":
						provider["bouquets"] = {}
						for node2 in node.childNodes:
							if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "configuration":
								configuration = {}
								for i in range(0, node2.attributes.length):
									if node2.attributes.item(i).name == "key":
										configuration["key"] = node2.attributes.item(i).value
									elif node2.attributes.item(i).name == "bouquet":
										configuration["bouquet"] = int(node2.attributes.item(i).value, 16)
									elif node2.attributes.item(i).name == "region":
										configuration["region"] = int(node2.attributes.item(i).value, 16)
									elif node2.attributes.item(i).name == "namespace":
										configuration["namespace"] = int(node2.attributes.item(i).value, 16)

								node2.normalize()
								if len(node2.childNodes) == 1 and node2.childNodes[0].nodeType == node2.TEXT_NODE:
									configuration["name"] = node2.childNodes[0].data

								if len(configuration.keys()) == 5:
									provider["bouquets"][configuration["key"]] = configuration

					elif node.tagName == "dvbcconfigs":
						provider["bouquets"] = {}
						transponder = {}
						transponder["nit_pid"] = 0x10
						transponder["nit_current_table_id"] = 0x40
						transponder["nit_other_table_id"] = 0x41
						transponder["sdt_pid"] = 0x11
						transponder["sdt_current_table_id"] = 0x42
						transponder["sdt_other_table_id"] = 0x46
						transponder["bat_pid"] = 0x11
						transponder["bat_table_id"] = 0x4a
						for node2 in node.childNodes:
							if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "configuration":
								configuration = {}
								for i in range(0, node2.attributes.length):
									if node2.attributes.item(i).name == "key":
										configuration["key"] = node2.attributes.item(i).value
									elif node2.attributes.item(i).name == "netid":
										configuration["netid"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "bouquettype":
										configuration["bouquettype"] = node2.attributes.item(i).value
									elif node2.attributes.item(i).name == "frequency":
										configuration["frequency"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "symbol_rate":
										configuration["symbol_rate"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "fec_inner":
										configuration["fec_inner"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "inversion":
										configuration["inversion"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "system":
										configuration["system"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "modulation":
										configuration["modulation"] = int(node2.attributes.item(i).value)

								node2.normalize()
								if len(node2.childNodes) == 1 and node2.childNodes[0].nodeType == node2.TEXT_NODE:
									configuration["name"] = node2.childNodes[0].data

								if len(configuration.keys()) == 10:
									provider["bouquets"][configuration["key"]] = configuration

						if len(transponder.keys()) == 8:
							provider["transponder"] = transponder

					elif node.tagName == "dvbtconfigs":
						provider["bouquets"] = {}
						transponder = {}
						transponder["nit_pid"] = 0x10
						transponder["nit_current_table_id"] = 0x40
						transponder["nit_other_table_id"] = 0x00
						transponder["sdt_pid"] = 0x11
						transponder["sdt_current_table_id"] = 0x42
						transponder["sdt_other_table_id"] = 0x46
						transponder["bat_pid"] = 0x11
						transponder["bat_table_id"] = 0x4a

						for node2 in node.childNodes:
							if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "configuration":
								configuration = {}
								for i in range(0, node2.attributes.length):
									if node2.attributes.item(i).name == "key":
										configuration["key"] = node2.attributes.item(i).value
									elif node2.attributes.item(i).name == "frequency":
										configuration["frequency"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "inversion":
										configuration["inversion"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "modulation":
										configuration["modulation"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "system":
										configuration["system"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "bandwidth":
										configuration["bandwidth"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "code_rate_hp":
										configuration["code_rate_hp"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "code_rate_lp":
										configuration["code_rate_lp"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "transmission_mode":
										configuration["transmission_mode"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "guard_interval":
										configuration["guard_interval"] = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "hierarchy":
										configuration["hierarchy"] = int(node2.attributes.item(i).value)

								node2.normalize()
								if len(node2.childNodes) == 1 and node2.childNodes[0].nodeType == node2.TEXT_NODE:
									configuration["name"] = node2.childNodes[0].data

								# print 'PPPP:',len(configuration.keys())
								if len(configuration.keys()) == 12:
									provider["bouquets"][configuration["key"]] = configuration

						# print 'OOO:',len(transponder.keys())
						if len(transponder.keys()) == 8:
							provider["transponder"] = transponder
						# print 'provider["bouquets"]',provider["bouquets"]


					elif node.tagName == "sections":
						provider["sections"] = {}
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
									provider["sections"][number] = node2.childNodes[0].data

					elif node.tagName == "swapchannels":
						swapchannels_set = {}
						swapchannels_set["filters"] = []
						swapchannels_set["preferred_order"] = []

						for node2 in node.childNodes:
							if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "channel":
								channel_number = -1
								channel_with = -1
								for i in range(0, node2.attributes.length):
									if node2.attributes.item(i).name == "number":
										channel_number = int(node2.attributes.item(i).value)
									elif node2.attributes.item(i).name == "with":
										channel_with = int(node2.attributes.item(i).value)

								if channel_number != -1 and channel_with != -1:
									swapchannels_set["preferred_order"].append([channel_number, channel_with])

							if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "filter":
								filter_bouquet = -1
								filter_region = -1
								for i in range(0, node2.attributes.length):
									if node2.attributes.item(i).name == "bouquet":
										filter_bouquet = int(node2.attributes.item(i).value, 16)
									elif node2.attributes.item(i).name == "region":
										filter_region = int(node2.attributes.item(i).value, 16)

								if filter_bouquet != -1 and filter_region != -1:
									swapchannels_set["filters"].append([filter_bouquet, filter_region])

						provider["swapchannels"].append(swapchannels_set)

					elif node.tagName == "channelsontop":
						provider["channelsontop"] = []

						for node2 in node.childNodes:
							if node2.nodeType == node2.ELEMENT_NODE and node2.tagName == "channel":
								for i in range(0, node2.attributes.length):
									if node2.attributes.item(i).name == "number":
										provider["channelsontop"].append(int(node2.attributes.item(i).value))

					elif node.tagName == "servicehacks":
						node.normalize()
						for i in range(0, len(node.childNodes)):
							if node.childNodes[i].nodeType == node.CDATA_SECTION_NODE:
								provider["servicehacks"] = node.childNodes[i].data.strip()

			if not ("name" in provider
					and "protocol" in provider
					and "streamtype" in provider
					and "namespace" in provider
					and "bouquets" in provider
					and "sections" in provider
					and "transponder" in provider
					and "servicehacks" in provider):

				print>>log, "[Providers] Incomplete XML %s" % filename
				continue

			providers[provider["key"]] = provider

		return providers

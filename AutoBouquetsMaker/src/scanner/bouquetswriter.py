# -*- coding: utf-8 -*-
# for localized messages
from .. import _

from .. import log
from Components.config import config
from tools import Tools
from dvbscanner import DvbScanner
import os, codecs, re

class BouquetsWriter():
	
	ABM_BOUQUET_PREFIX = "userbouquet.abm."
		
	def writeLamedb(self, path, transponders):
		print>>log, "[BouquetsWriter] Writing lamedb..."

		transponders_count = 0
		services_count = 0

		lamedblist = []
		lamedblist.append("eDVB services /4/\n")
		lamedblist.append("transponders\n")

		for key in transponders.keys():
			transponder = transponders[key]
			lamedblist.append("%08x:%04x:%04x\n" %
				(transponder["namespace"],
				transponder["transport_stream_id"],
				transponder["original_network_id"]))

			if transponder["dvb_type"] == "dvbs":
				if transponder["orbital_position"] > 1800:
					orbital_position = transponder["orbital_position"] - 3600
				else:
					orbital_position = transponder["orbital_position"]

				if transponder["modulation_system"] == 0:
					lamedblist.append("\ts %d:%d:%d:%d:%d:%d:%d\n" %
						(transponder["frequency"],
						transponder["symbol_rate"],
						transponder["polarization"],
						transponder["fec_inner"],
						orbital_position,
						transponder["inversion"],
						transponder["flags"]))
				else:
					lamedblist.append("\ts %d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d\n" %
						(transponder["frequency"],
						transponder["symbol_rate"],
						transponder["polarization"],
						transponder["fec_inner"],
						orbital_position,
						transponder["inversion"],
						transponder["flags"],
						transponder["modulation_system"],
						transponder["modulation_type"],
						transponder["roll_off"],
						transponder["pilot"]))
			elif transponder["dvb_type"] == "dvbt":
				lamedblist.append("\tt %d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d\n" %
					(transponder["frequency"],
					transponder["bandwidth"],
					transponder["code_rate_hp"],
					transponder["code_rate_lp"],
					transponder["modulation"],
					transponder["transmission_mode"],
					transponder["guard_interval"],
					transponder["hierarchy"],
					transponder["inversion"],
					transponder["flags"],
					transponder["system"],
					transponder["plpid"]))
			elif transponder["dvb_type"] == "dvbc":
				lamedblist.append("\tc %d:%d:%d:%d:%d:%d:%d\n" %
					(transponder["frequency"],
					transponder["symbol_rate"],
					transponder["inversion"],
					transponder["modulation_type"],
					transponder["fec_inner"],
					transponder["flags"],
					transponder["modulation_system"]))
			lamedblist.append("/\n")
			transponders_count += 1

		lamedblist.append("end\nservices\n")
		for key in transponders.keys():
			transponder = transponders[key]
			if "services" not in transponder.keys():
				continue

			for key2 in transponder["services"].keys():
				service = transponder["services"][key2]
				lamedblist.append("%04x:%08x:%04x:%04x:%d:%d\n" %
					(service["service_id"],
					service["namespace"],
					service["transport_stream_id"],
					service["original_network_id"],
					service["service_type"],
					service["flags"]))

				control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
				control_char_re = re.compile('[%s]' % re.escape(control_chars))
				if 'provider_name' in service.keys():
					service_name = control_char_re.sub('', service["service_name"]).decode('latin-1').encode("utf8")
					provider_name = control_char_re.sub('', service["provider_name"]).decode('latin-1').encode("utf8")
				else:
					service_name = service["service_name"]

				lamedblist.append("%s\n" % service_name)

				if 'free_ca' in service.keys() and service["free_ca"] != 0:
					lamedblist.append("p:%s,C:0000\n" % provider_name)
				elif 'service_line' in service.keys():
					try:
						lamedblist.append("%s\n" % service["service_line"])
					except UnicodeDecodeError:
						try:
							print>>log, "[BouquetsWriter] UnicodeDecodeError, service line for '%s' contains illegal characters." % service_name
							lamedblist.append("%s\n" % service["service_line"].decode('latin-1').encode("utf8"))
						except UnicodeDecodeError:
							lamedblist.append("%s\n" % ("".join(i for i in service["service_line"] if ord(i)<128)))
				else:
					lamedblist.append("p:%s\n" % provider_name)
				services_count += 1

		lamedblist.append("end\nHave a lot of bugs!\n")
		lamedb = codecs.open(path + "/lamedb", "w", "utf-8")
		lamedb.write(''.join(lamedblist))
		lamedb.close()
		del lamedblist

		print>>log, "[BouquetsWriter] Wrote %d transponders and %d services" % (transponders_count, services_count)

	def makeCustomSeparator(self, path, filename, max_count):
		print>>log, "[BouquetsWriter] Make custom seperator for %s in main bouquet..." % filename

		try:
			bouquet_in = open(path + "/" + filename, "r")
		except Exception, e:
			print>>log, "[BouquetsWriter]", e
			return

		content = bouquet_in.read()
		bouquet_in.close()
		
		seperator_name = "/%s%s.separator.tv" % (self.ABM_BOUQUET_PREFIX, filename[:len(filename)-3])
		try:
			bouquet_out = open(path + seperator_name, "w")
		except Exception, e:
			print>>log, "[BouquetsWriter]", e
			return
			
		rows = content.split("\n")
		count = 0
		
		name = ''
		for row in rows:
			if len(row.strip()) == 0:
				break
				
			if row[:5] == "#NAME" and name == '':
				name = row.strip()[6:]

			if row[:8] == "#SERVICE" and row[:13] != "#SERVICE 1:64":
				count += 1
				if count > max_count:
					break

			#bouquet_out_list.append(row + "\n")
		
		print>>log, "[BouquetsWriter] Custom seperator name: %s" % name
		
		bouquet_out_list = []

		bouquet_out_list.append("#NAME CustomSeparatorMain for %s\n" % name)
		bouquet_out_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
		bouquet_out_list.append("#DESCRIPTION CustomSeparatorMain for %s\n" % name)

		if count < max_count:
			for i in range(count, max_count):
				bouquet_out_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
				bouquet_out_list.append("#DESCRIPTION  \n")

		bouquet_out.write(''.join(bouquet_out_list))
		bouquet_out.close()
		del bouquet_out_list
		
		print>>log, "[BouquetsWriter] Custom seperator made. %s" % seperator_name

	def containServices(self, path, filename):
		try:
			bouquets = open(path + "/" + filename, "r")
			content = bouquets.read().strip().split("\n")
			bouquets.close()
			return len(content) > 2
		except Exception, e:
			return False

	def containServicesLines(self, path, filename):
		try:
			bouquets = open(path + "/" + filename, "r")
			content = bouquets.read().strip().split("\n")
			bouquets.close()
			for line in content:
				if line[:13] == "#SERVICE 1:0:" or line[:16] == "#SERVICE 4097:0:":		#service or iptv line found
					return True
					break
			return False
		except Exception, e:
			return False

	def buildBouquetsIndex(self, path, bouquetsOrder, providers, bouquetsToKeep, currentBouquets, bouquets_to_hide, provider_configs):
		print>>log, "[BouquetsWriter] Writing bouquets index..."

		bouquets_tv = open(path + "/bouquets.tv", "w")
		bouquets_tv_list = []
		bouquets_tv_list.append("#NAME Bouquets (TV)\n")

		bouquets_radio = open(path + "/bouquets.radio", "w")
		bouquets_radio_list = []
		bouquets_radio_list.append("#NAME Bouquets (Radio)\n")

		bouquetsToKeep2 = {}
		bouquetsToKeep2["tv"] = []
		bouquetsToKeep2["radio"] = []

		customfilenames = []
		hidden_non_abm_bouquet = []
		display_empty_bouquet = ['userbouquet.favourites.tv', 'userbouquet.favourites.radio', 'userbouquet.LastScanned.tv']
		
		if config.autobouquetsmaker.placement.getValue() == 'bottom':
			for bouquet_type in ["tv", "radio"]:
				for filename in currentBouquets[bouquet_type]:
					if filename[:len(self.ABM_BOUQUET_PREFIX)] == self.ABM_BOUQUET_PREFIX:
						continue
					if filename in bouquetsToKeep[bouquet_type] and (self.containServicesLines(path, filename) or filename in display_empty_bouquet):
						to_write = "#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % filename
					else:
						to_write = "#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % filename
					if bouquet_type == "tv":
						bouquets_tv_list.append(to_write)
					else:
						bouquets_radio_list.append(to_write)

		for section_identifier in bouquetsOrder:
			sections = providers[section_identifier]["sections"]

			if provider_configs[section_identifier].isMakeNormalMain() or provider_configs[section_identifier].isMakeHDMain() or provider_configs[section_identifier].isMakeFTAHDMain():
				if self.containServices(path, "%s%s.main.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier)):
					bouquets_tv_list.append("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.main.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier))
				else:
					bouquets_tv_list.append("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.main.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier))
				bouquetsToKeep2["tv"].append("%s%s.main.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier))
			elif provider_configs[section_identifier].isMakeCustomMain() and config.autobouquetsmaker.placement.getValue() == 'top':
				customfilename = provider_configs[section_identifier].getCustomFilename()
				bouquets_tv_list.append("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % customfilename)
				customseperator = "%s%s.separator.tv" % (self.ABM_BOUQUET_PREFIX, customfilename[:len(customfilename)-3])
				bouquets_tv_list.append("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % customseperator)
				bouquetsToKeep2["tv"].append(customfilename)
				bouquetsToKeep2["tv"].append(customseperator)
				customfilenames.append(customfilename)

			if provider_configs[section_identifier].isMakeSections():
				for section_number in sorted(sections.keys()):
					if (section_identifier in bouquets_to_hide and section_number in bouquets_to_hide[section_identifier]) or not self.containServicesLines(path, "%s%s.%d.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_number)):
						bouquets_tv_list.append("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.%d.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_number))
					else:
						bouquets_tv_list.append("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.%d.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_number))
					bouquetsToKeep2["tv"].append("%s%s.%d.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_number))

			if provider_configs[section_identifier].isMakeNormalMain() or \
				provider_configs[section_identifier].isMakeHDMain() or \
				provider_configs[section_identifier].isMakeFTAHDMain() or \
				provider_configs[section_identifier].isMakeSections() or \
				provider_configs[section_identifier].isMakeCustomMain():
				bouquets_tv_list.append("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.separator.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier))
				bouquetsToKeep2["tv"].append("%s%s.separator.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier))

			if provider_configs[section_identifier].isMakeHD():
				section_type = "hd"
				if self.containServicesLines(path, "%s%s.%s.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type)):
					bouquets_tv_list.append("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.%s.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
				else:
					bouquets_tv_list.append("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.%s.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
				bouquetsToKeep2["tv"].append("%s%s.%s.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
				
			if provider_configs[section_identifier].isMakeFTAHD():
				section_type = "ftahd"
				if self.containServicesLines(path, "%s%s.%s.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type)):
					bouquets_tv_list.append("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.%s.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
				else:
					bouquets_tv_list.append("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.%s.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
				bouquetsToKeep2["tv"].append("%s%s.%s.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
				
			if provider_configs[section_identifier].isMakeFTA():
				section_type = "fta"
				if self.containServicesLines(path, "%s%s.%s.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type)):
					bouquets_tv_list.append("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.%s.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
				else:
					bouquets_tv_list.append("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.%s.tv\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
				bouquetsToKeep2["tv"].append("%s%s.%s.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_type))
			
			bouquets_radio_list.append("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s%s.main.radio\" ORDER BY bouquet\n" % (self.ABM_BOUQUET_PREFIX, section_identifier))
			bouquetsToKeep2["radio"].append("%s%s.main.radio" % (self.ABM_BOUQUET_PREFIX, section_identifier))

		if config.autobouquetsmaker.placement.getValue() == 'top':
			for bouquet_type in ["tv", "radio"]:
				for filename in currentBouquets[bouquet_type]:
					if filename[:len(self.ABM_BOUQUET_PREFIX)] == self.ABM_BOUQUET_PREFIX or filename in customfilenames:
						continue
					if filename in bouquetsToKeep[bouquet_type] and (self.containServicesLines(path, filename) or filename in display_empty_bouquet):
						to_write = "#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % filename
					else:
						to_write = "#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % filename
					if bouquet_type == "tv":
						bouquets_tv_list.append(to_write)
					else:
						bouquets_radio_list.append(to_write)

		bouquets_tv.write(''.join(bouquets_tv_list))
		bouquets_tv.close()
		del bouquets_tv_list
		
		bouquets_radio.write(''.join(bouquets_radio_list))
		bouquets_radio.close()
		del bouquets_radio_list

		for bouquet_type in ["tv", "radio"]:
			for filename in currentBouquets[bouquet_type]:
				if filename[:len(self.ABM_BOUQUET_PREFIX)] != self.ABM_BOUQUET_PREFIX or filename in bouquetsToKeep2[bouquet_type]:
					continue

				try:
					os.remove(path + "/" + filename)
				except Exception, e:
					print>>log, "[BouquetsWriter] Cannot delete %s: %s" % (filename, e)
					continue
		print>>log, "[BouquetsWriter] Done"

	def buildBouquets(self, path, provider_config, services, sections, section_identifier, preferred_order, channels_on_top, bouquets_to_hide, section_prefix):
		channels_on_top = channels_on_top[0]
		if len(section_prefix) > 0:
			section_prefix = section_prefix + " - "
		current_number = 0
		
		# as first thing we're going to cleanup channels
		# with a numeration inferior to the first section
		first_section_number = sorted(sections.keys())[0]
		for number in sorted(services["video"].keys()):
			if number >= first_section_number:
				break

			del(services["video"][number])

		print>>log, "[BouquetsWriter] Writing %s bouquet..." % section_identifier

		force_keep_numbers = False
		
		# swap channels
		swapDict = {}
		for swaprule in preferred_order:
			if swaprule[0] in services["video"] and swaprule[1] in services["video"] and services["video"][swaprule[1]]["service_type"] >= 17:
				swapDict[swaprule[0]] = swaprule[1]
				swapDict[swaprule[1]] = swaprule[0]
		
		if provider_config.isMakeNormalMain():
			bouquet_current = open(path + "/%s%s.main.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier), "w")
			current_bouquet_list = []
			current_bouquet_list.append("#NAME %s%s\n" % (section_prefix, _('All channels')))
			
			# Clear unused sections
			sections_c = sections.copy()
			sections_c = Tools().clearsections(services, sections_c, 'ALL', "video")

			# small hack to handle the "preferred_order" list
			higher_number = sorted(services["video"].keys())[-1]
			preferred_order_tmp = []

			# expand a range into a list
			for number in range(1, higher_number + 1):
				preferred_order_tmp.append(number)

			# Always write first not hidden section on top of list
			for number in preferred_order_tmp:
				if number in sections_c and number not in bouquets_to_hide:
					current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
					current_bouquet_list.append("#DESCRIPTION %s%s\n" % (section_prefix, sections_c[number]))
					first_section = number
					break
					
			# Use separate section counter. Preferred_order_tmp has swapped numbers. Can put sections on wrong places
			section_number = 1
			for number in preferred_order_tmp:
				if section_number in sections_c and section_number not in bouquets_to_hide and section_number != first_section:
					current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
					current_bouquet_list.append("#DESCRIPTION %s%s\n" % (section_prefix, sections_c[section_number]))
				if number in swapDict:
					number = swapDict[number]
				if number in services["video"] and number not in bouquets_to_hide:
					current_bouquet_list.append("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
							services["video"][number]["service_type"],
							services["video"][number]["service_id"],
							services["video"][number]["transport_stream_id"],
							services["video"][number]["original_network_id"],
							services["video"][number]["namespace"]
						))
					if "interactive_name" in services["video"][number]:
						current_bouquet_list.append("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])
				else:
					current_bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
					current_bouquet_list.append("#DESCRIPTION  \n")

				current_number += 1
				section_number += 1

			bouquet_current.write(''.join(current_bouquet_list))
			bouquet_current.close()
			del current_bouquet_list

		elif provider_config.isMakeHDMain() or provider_config.isMakeFTAHDMain():
			bouquet_current = open(path + "/%s%s.main.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier), "w")
			current_bouquet_list = []
			if provider_config.isMakeHDMain():
				hd_or_ftahd = "HD"
				current_bouquet_list.append("#NAME %s%s\n" % (section_prefix, _('HD Channels')))
			elif provider_config.isMakeFTAHDMain():
				hd_or_ftahd = "FTAHD"
				current_bouquet_list.append("#NAME %s%s\n" % (section_prefix, _('FTA HD Channels')))

			higher_number = sorted(sections.keys())[0]
			
			# Clear unused sections
			sections_c = sections.copy()
			sections_c = Tools().clearsections(services, sections_c, hd_or_ftahd, "video")
			
			section_keys_temp = sorted(sections_c.keys())
			section_key_current = section_keys_temp[0]

			if higher_number > 1:
				# small hack to handle the "channels_on_top" list
				hd_channels_numbers_tmp = sorted(services["video"].keys())
				channels_on_top_tmp = list(channels_on_top)
				for number in channels_on_top:
					if number in hd_channels_numbers_tmp:
						hd_channels_numbers_tmp.remove(number)
					else:
						channels_on_top_tmp.remove(number)
				hd_channels_numbers = channels_on_top_tmp
				hd_channels_numbers += hd_channels_numbers_tmp

				todo = None
				for number in hd_channels_numbers:
					if number >= section_key_current:
						todo = None
						if section_key_current not in bouquets_to_hide:
							current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
							current_bouquet_list.append("#DESCRIPTION %s%s\n" % (section_prefix, sections_c[section_key_current]))
							todo = section_key_current

						section_keys_temp.remove(section_key_current)
						if len(section_keys_temp) > 0:
							section_key_current = section_keys_temp[0]
						else:
							section_key_current = 65535

					if todo and number >= todo:
						if services["video"][number]["service_type"] in DvbScanner.VIDEO_ALLOWED_TYPES and services["video"][number]["service_type"] >= 17 and (provider_config.isMakeHDMain() or (provider_config.isMakeFTAHDMain() and services["video"][number]["free_ca"] == 0)):  # from 17 to higher are HD?
							current_number += 1
							current_bouquet_list.append("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
									services["video"][number]["service_type"],
									services["video"][number]["service_id"],
									services["video"][number]["transport_stream_id"],
									services["video"][number]["original_network_id"],
									services["video"][number]["namespace"]
								))
							if "interactive_name" in services["video"][number]:
								current_bouquet_list.append("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])

					if current_number == higher_number - 1:
						break

				for x in range(current_number, higher_number - 1):
					current_bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
					current_bouquet_list.append("#DESCRIPTION  \n")

				current_number = higher_number - 1

			bouquet_current.write(''.join(current_bouquet_list))
			bouquet_current.close()
			del current_bouquet_list
			force_keep_numbers = True

		elif provider_config.isMakeCustomMain() and config.autobouquetsmaker.placement.getValue() == 'top':
			current_number = sorted(sections.keys())[0] - 1
			self.makeCustomSeparator(path, provider_config.getCustomFilename(), current_number)
			force_keep_numbers = True
		else:
			force_keep_numbers = True

		if provider_config.isMakeSections():
			if not provider_config.isMakeNormalMain() and not provider_config.isMakeHDMain() and not provider_config.isMakeFTAHDMain() and not provider_config.isMakeCustomMain():
				section_current_number = 0
			else:
				section_current_number = sorted(sections.keys())[0] - 1

			for section_number in sorted(sections.keys()):
				section_name = sections[section_number]

				# discover the highest number for this section
				# it's tricky... i don't like it
				higher_number = 0
				key_found = False
				for key in sorted(sections.keys()):
					if key_found:
						higher_number = key - 1
						break;

					if key == section_number:
						key_found = True

				if higher_number == 0:	# it mean this is the last section
					higher_number = sorted(services["video"].keys())[-1]	# the highest number!

				# write it!
				bouquet_current = open(path + "/%s%s.%d.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier, section_number), "w")
				current_bouquet_list = []
				if section_number not in bouquets_to_hide:
					current_bouquet_list.append("#NAME %s%s\n" % (section_prefix, section_name))
					current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
					current_bouquet_list.append("#DESCRIPTION %s%s\n" % (section_prefix, section_name))
				elif section_current_number == 0:
					current_bouquet_list.append("#NAME %sHidden\n" % section_prefix)
					current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
					current_bouquet_list.append("#DESCRIPTION %sHidden\n" % section_prefix)

				#current_number += 1
				section_current_number += 1
				for number in range(section_current_number, higher_number + 1):
					if number in swapDict:
						number = swapDict[number]
					if number in services["video"] and section_number not in bouquets_to_hide:
						current_bouquet_list.append("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
								services["video"][number]["service_type"],
								services["video"][number]["service_id"],
								services["video"][number]["transport_stream_id"],
								services["video"][number]["original_network_id"],
								services["video"][number]["namespace"]
							))
						if "interactive_name" in services["video"][number]:
							current_bouquet_list.append("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])
						current_number += 1
					elif force_keep_numbers:
						current_bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
						current_bouquet_list.append("#DESCRIPTION  \n")
						current_number += 1

				bouquet_current.write(''.join(current_bouquet_list))
				bouquet_current.close()
				del current_bouquet_list
				section_current_number = higher_number

		# Seperator bouquet
		if provider_config.isMakeNormalMain() or \
			provider_config.isMakeHDMain() or \
			provider_config.isMakeFTAHDMain() or \
			provider_config.isMakeSections() or \
			provider_config.isMakeCustomMain():
			bouquet_current = open(path + "/%s%s.separator.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier), "w")
			current_bouquet_list = []
			current_bouquet_list.append("#NAME %sSeparator\n" % section_prefix)
			current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
			current_bouquet_list.append("#DESCRIPTION %sSeparator\n" % section_prefix)
	
			for x in range(current_number, (int(current_number/1000) + 1) * 1000):
				current_bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
				current_bouquet_list.append("#DESCRIPTION  \n")
				current_number += 1

			bouquet_current.write(''.join(current_bouquet_list))
			bouquet_current.close()
			del current_bouquet_list

		# HD channels
		if provider_config.isMakeHD():
			bouquet_current = open(path + "/%s%s.hd.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier), "w")
			current_bouquet_list = []
			current_bouquet_list.append("#NAME %s%s\n" % (section_prefix, _('HD Channels')))

			# Clear unused sections
			sections_c = sections.copy()
			sections_c = Tools().clearsections(services, sections_c, "HD", "video")
			
			section_keys_temp = sorted(sections_c.keys())
			section_key_current = section_keys_temp[0]

			# small hack to handle the "channels_on_top" list
			hd_channels_numbers_tmp = sorted(services["video"].keys())
			channels_on_top_tmp = list(channels_on_top)
			for number in channels_on_top:
				if number in hd_channels_numbers_tmp:
					hd_channels_numbers_tmp.remove(number)
				else:
					channels_on_top_tmp.remove(number)
			hd_channels_numbers = channels_on_top_tmp
			hd_channels_numbers += hd_channels_numbers_tmp

			todo = None
			for number in hd_channels_numbers:
				if number >= section_key_current:
					todo = None
					if section_key_current not in bouquets_to_hide:
						current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
						current_bouquet_list.append("#DESCRIPTION %s%s\n" % (section_prefix, sections_c[section_key_current]))
						todo = section_key_current

					section_keys_temp.remove(section_key_current)
					if len(section_keys_temp) > 0:
						section_key_current = section_keys_temp[0]
					else:
						section_key_current = 65535

				if todo and number >= todo:
					if services["video"][number]["service_type"] in DvbScanner.VIDEO_ALLOWED_TYPES and services["video"][number]["service_type"] >= 17:  # from 17 to higher are HD?
						current_number += 1
						current_bouquet_list.append("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
								services["video"][number]["service_type"],
								services["video"][number]["service_id"],
								services["video"][number]["transport_stream_id"],
								services["video"][number]["original_network_id"],
								services["video"][number]["namespace"]
							))
						if "interactive_name" in services["video"][number]:
							current_bouquet_list.append("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])

			for x in range(current_number, (int(current_number/1000) + 1) * 1000):
				current_bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
				current_bouquet_list.append("#DESCRIPTION  \n")
				current_number += 1

			bouquet_current.write(''.join(current_bouquet_list))
			bouquet_current.close()
			del current_bouquet_list

		# FTA HD channels
		if provider_config.isMakeFTAHD():
			bouquet_current = open(path + "/%s%s.ftahd.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier), "w")
			current_bouquet_list = []
			current_bouquet_list.append("#NAME %s%s\n" % (section_prefix, _('FTA HD Channels')))
			
			# Clear unused sections
			sections_c = sections.copy()
			sections_c = Tools().clearsections(services, sections_c, "FTAHD", "video")

			section_keys_temp = sorted(sections_c.keys())
			section_key_current = section_keys_temp[0]

			# small hack to handle the "channels_on_top" list
			hd_channels_numbers_tmp = sorted(services["video"].keys())
			channels_on_top_tmp = list(channels_on_top)
			for number in channels_on_top:
				if number in hd_channels_numbers_tmp:
					hd_channels_numbers_tmp.remove(number)
				else:
					channels_on_top_tmp.remove(number)
			hd_channels_numbers = channels_on_top_tmp
			hd_channels_numbers += hd_channels_numbers_tmp

			todo = None
			for number in hd_channels_numbers:
				if number >= section_key_current:
					todo = None
					if section_key_current not in bouquets_to_hide:
						current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
						current_bouquet_list.append("#DESCRIPTION %s%s\n" % (section_prefix, sections_c[section_key_current]))
						todo = section_key_current

					section_keys_temp.remove(section_key_current)
					if len(section_keys_temp) > 0:
						section_key_current = section_keys_temp[0]
					else:
						section_key_current = 65535

				if todo and number >= todo:
					if services["video"][number]["service_type"] in DvbScanner.VIDEO_ALLOWED_TYPES and services["video"][number]["service_type"] >= 17 and services["video"][number]["free_ca"] == 0: # from 17 to higher are HD?
						current_number += 1
						current_bouquet_list.append("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
								services["video"][number]["service_type"],
								services["video"][number]["service_id"],
								services["video"][number]["transport_stream_id"],
								services["video"][number]["original_network_id"],
								services["video"][number]["namespace"]
							))
						if "interactive_name" in services["video"][number]:
							current_bouquet_list.append("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])

			for x in range(current_number, (int(current_number/1000) + 1) * 1000):
				current_bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
				current_bouquet_list.append("#DESCRIPTION  \n")
				current_number += 1

			bouquet_current.write(''.join(current_bouquet_list))
			bouquet_current.close()
			del current_bouquet_list

		# FTA channels
		if provider_config.isMakeFTA():
			bouquet_current = open(path + "/%s%s.fta.tv" % (self.ABM_BOUQUET_PREFIX, section_identifier), "w")
			current_bouquet_list = []
			current_bouquet_list.append("#NAME %s%s\n" % (section_prefix, _('FTA Channels')))
			
			# Clear unused sections
			sections_c = sections.copy()
			sections_c = Tools().clearsections(services, sections_c, "FTA", "video")
			
			section_keys_temp = sorted(sections_c.keys())
			section_key_current = section_keys_temp[0]

			higher_number = sorted(services["video"].keys())[-1]
			
			todo = None
			for number in range(1, higher_number + 1):
				if number >= section_key_current:
					todo = None
					if section_key_current not in bouquets_to_hide:
						current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
						current_bouquet_list.append("#DESCRIPTION %s%s\n" % (section_prefix, sections_c[section_key_current]))
						todo = section_key_current

					section_keys_temp.remove(section_key_current)
					if len(section_keys_temp) > 0:
						section_key_current = section_keys_temp[0]
					else:
						section_key_current = 65535

				if todo and number >= todo:
					if number in services["video"] and services["video"][number]["free_ca"] == 0 and number not in bouquets_to_hide:
						current_number += 1
						current_bouquet_list.append("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
								services["video"][number]["service_type"],
								services["video"][number]["service_id"],
								services["video"][number]["transport_stream_id"],
								services["video"][number]["original_network_id"],
								services["video"][number]["namespace"]
							))
						if "interactive_name" in services["video"][number]:
							current_bouquet_list.append("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])
						
			for x in range(current_number, (int(current_number/1000) + 1) * 1000):
				current_bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
				current_bouquet_list.append("#DESCRIPTION  \n")
				current_number += 1

			bouquet_current.write(''.join(current_bouquet_list))
			bouquet_current.close()
			del current_bouquet_list

		# now the radio bouquet
		bouquet_current = open(path + "/%s%s.main.radio" % (self.ABM_BOUQUET_PREFIX, section_identifier), "w")
		current_bouquet_list = []
		current_bouquet_list.append("#NAME %s%s\n" % (section_prefix, _('Radio Channels')))
		current_bouquet_list.append("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
		current_bouquet_list.append("#DESCRIPTION %sRadio channels\n" % section_prefix)

		if len(services["radio"].keys()) > 0:
			higher_number = sorted(services["radio"].keys())[-1]	# the highest number!
			for number in range(1, higher_number + 1):
				if number in services["radio"]:
					current_bouquet_list.append("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
							services["radio"][number]["service_type"],
							services["radio"][number]["service_id"],
							services["radio"][number]["transport_stream_id"],
							services["radio"][number]["original_network_id"],
							services["radio"][number]["namespace"]
						))
				else:
					current_bouquet_list.append("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
					current_bouquet_list.append("#DESCRIPTION  \n")

		bouquet_current.write(''.join(current_bouquet_list))
		bouquet_current.close()
		del current_bouquet_list

		print>>log, "[BouquetsWriter] Done"
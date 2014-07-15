from .. import log
from Components.config import config
import os, codecs, re

class BouquetsWriter():
	def writeLamedb(self, path, transponders):
		print>>log, "[BouquetsWriter] Writing lamedb..."

		transponders_count = 0
		services_count = 0

		lamedb = codecs.open(path + "/lamedb", "w", "utf-8")
		lamedb.write("eDVB services /4/\n")
		lamedb.write("transponders\n")

		for key in transponders.keys():
			transponder = transponders[key]
			lamedb.write("%08x:%04x:%04x\n" %
				(transponder["namespace"],
				transponder["transport_stream_id"],
				transponder["original_network_id"]))

			if transponder["dvb_type"] == "dvbs":
				if transponder["orbital_position"] > 1800:
					orbital_position = transponder["orbital_position"] - 3600
				else:
					orbital_position = transponder["orbital_position"]

				if transponder["modulation_system"] == 0:
					lamedb.write("\ts %d:%d:%d:%d:%d:%d:%d\n" %
						(transponder["frequency"],
						transponder["symbol_rate"],
						transponder["polarization"],
						transponder["fec_inner"],
						orbital_position,
						transponder["inversion"],
						transponder["flags"]))
				else:
					lamedb.write("\ts %d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d\n" %
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
				lamedb.write("\tt %d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d\n" %
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
				lamedb.write("\tc %d:%d:%d:%d:%d:%d:%d\n" %
					(transponder["frequency"],
					transponder["symbol_rate"],
					transponder["inversion"],
					transponder["modulation_type"],
					transponder["fec_inner"],
					transponder["flags"],
					transponder["modulation_system"]))
			lamedb.write("/\n")
			transponders_count += 1

		lamedb.write("end\nservices\n")
		for key in transponders.keys():
			transponder = transponders[key]
			if "services" not in transponder.keys():
				continue

			for key2 in transponder["services"].keys():
				service = transponder["services"][key2]
				lamedb.write("%04x:%08x:%04x:%04x:%d:%d\n" %
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

				lamedb.write("%s\n" % service_name)

				if 'free_ca' in service.keys() and service["free_ca"] != 0:
					lamedb.write("p:%s,C:0000\n" % provider_name)
				elif 'service_line' in service.keys():
					lamedb.write("%s\n" % service["service_line"])
				else:
					lamedb.write("p:%s\n" % provider_name)
				services_count += 1

		lamedb.write("end\nHave a lot of bugs!\n")
		lamedb.close()

		print>>log, "[BouquetsWriter] Wrote %d transponders and %d services" % (transponders_count, services_count)

	def transformCustomInMain(self, path, filename, max_count):
		print>>log, "[BouquetsWriter] Transform bouquet %s in main bouquet..." % filename

		try:
			bouquet_in = open(path + "/" + filename, "r")
		except Exception, e:
			print>>log, "[BouquetsWriter]", e
			return

		content = bouquet_in.read()
		bouquet_in.close()

		try:
			bouquet_out = open(path + "/" + filename, "w")
		except Exception, e:
			print>>log, "[BouquetsWriter]", e
			return

		rows = content.split("\n")
		count = 0
		for row in rows:
			if len(row.strip()) == 0:
				break

			if row[:8] == "#SERVICE" and row[:13] != "#SERVICE 1:64":
				count += 1
				if count > max_count:
					break

			bouquet_out.write(row + "\n")

		if count < max_count:
			for i in range(count, max_count):
				bouquet_out.write("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
				bouquet_out.write("#DESCRIPTION  \n")

		bouquet_out.close()

		print>>log, "[BouquetsWriter] Done"

	def containServices(self, path, filename):
		try:
			bouquets = open(path + "/" + filename, "r")
			content = bouquets.read().strip().split("\n")
			bouquets.close()
			return len(content) > 2
		except Exception, e:
			return False

	def buildBouquetsIndex(self, path, bouquetsOrder, providers, bouquetsToKeep, currentBouquets, bouquets_to_hide, provider_configs):
		print>>log, "[BouquetsWriter] Writing bouquets index..."

		bouquets_tv = open(path + "/bouquets.tv", "w")
		bouquets_tv.write("#NAME Bouquets (TV)\n")

		bouquets_radio = open(path + "/bouquets.radio", "w")
		bouquets_radio.write("#NAME Bouquets (Radio)\n")

		bouquetsToKeep2 = {}
		bouquetsToKeep2["tv"] = []
		bouquetsToKeep2["radio"] = []

		customfilenames = []

		if config.autobouquetsmaker.placement.getValue() == 'bottom':
			for filename in bouquetsToKeep["tv"]:
				bouquets_tv.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % filename)

			for filename in bouquetsToKeep["radio"]:
				bouquets_radio.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % filename)

		for section_identifier in bouquetsOrder:
			sections = providers[section_identifier]["sections"]

			if provider_configs[section_identifier].isMakeNormalMain() or provider_configs[section_identifier].isMakeHDMain() or provider_configs[section_identifier].isMakeFTAHDMain():
				if self.containServices(path, "autobouquet.%s.main.tv" % section_identifier):
					bouquets_tv.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.main.tv\" ORDER BY bouquet\n" % section_identifier)
				else:
					bouquets_tv.write("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.main.tv\" ORDER BY bouquet\n" % section_identifier)
				bouquetsToKeep2["tv"].append("autobouquet.%s.main.tv" % section_identifier)
			elif provider_configs[section_identifier].isMakeCustomMain() and config.autobouquetsmaker.placement.getValue() == 'top':
				customfilename = provider_configs[section_identifier].getCustomFilename()
				if self.containServices(path, customfilename):
					bouquets_tv.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % customfilename)
				else:
					bouquets_tv.write("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % customfilename)
				bouquetsToKeep2["tv"].append(customfilename)
				customfilenames.append(customfilename)

			if provider_configs[section_identifier].isMakeSections():
				for section_number in sorted(sections.keys()):
					if section_identifier in bouquets_to_hide and section_number in bouquets_to_hide[section_identifier]:
						bouquets_tv.write("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.%d.tv\" ORDER BY bouquet\n" % (section_identifier, section_number))
					else:
						bouquets_tv.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.%d.tv\" ORDER BY bouquet\n" % (section_identifier, section_number))
					bouquetsToKeep2["tv"].append("autobouquet.%s.%d.tv" % (section_identifier, section_number))

			if provider_configs[section_identifier].isMakeHD():
				bouquets_tv.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.hd.tv\" ORDER BY bouquet\n" % section_identifier)
				bouquetsToKeep2["tv"].append("autobouquet.%s.hd.tv" % section_identifier)

			if provider_configs[section_identifier].isMakeFTAHD():
				bouquets_tv.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.ftahd.tv\" ORDER BY bouquet\n" % section_identifier)
				bouquetsToKeep2["tv"].append("autobouquet.%s.ftahd.tv" % section_identifier)

			if provider_configs[section_identifier].isMakeFTA():
				bouquets_tv.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.fta.tv\" ORDER BY bouquet\n" % section_identifier)
				bouquetsToKeep2["tv"].append("autobouquet.%s.fta.tv" % section_identifier)

			bouquets_tv.write("#SERVICE 1:519:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.separator.tv\" ORDER BY bouquet\n" % section_identifier)
			bouquetsToKeep2["tv"].append("autobouquet.%s.separator.tv" % section_identifier)

			bouquets_radio.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"autobouquet.%s.main.radio\" ORDER BY bouquet\n" % section_identifier)
			bouquetsToKeep2["radio"].append("autobouquet.%s.main.radio" % section_identifier)

		if config.autobouquetsmaker.placement.getValue() == 'top':
			for filename in bouquetsToKeep["tv"]:
				if filename in customfilenames:
					continue
				bouquets_tv.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % filename)

			for filename in bouquetsToKeep["radio"]:
				bouquets_radio.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % filename)

		bouquets_tv.close()
		bouquets_radio.close()

		for bouquet_type in ["tv", "radio"]:
			for filename in currentBouquets[bouquet_type]:
				if filename[:12] == "autobouquet.":
					continue

				if filename in bouquetsToKeep[bouquet_type] or filename in bouquetsToKeep2[bouquet_type]:
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
		if provider_config.isMakeNormalMain():
			bouquet_current = open(path + "/autobouquet.%s.main.tv" % section_identifier, "w")
			bouquet_current.write("#NAME %sAll channels\n" % section_prefix)

			# due an issue with the patch for hidden channels,
			# the first tag must be a description to keep the
			# numeration correct
			first_section = sorted(sections.keys())[0]
			bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
			if first_section not in bouquets_to_hide:
				bouquet_current.write("#DESCRIPTION %s%s\n" % (section_prefix, sections[first_section]))
			else:
				bouquet_current.write("#DESCRIPTION \n")

			# small hack to handle the "preferred_order" list
			higher_number = sorted(services["video"].keys())[-1]
			preferred_order_tmp = []

			# expand a range into a list
			for number in range(1, higher_number + 1):
				preferred_order_tmp.append(number)

			# swap channels
			for swaprule in preferred_order:
				if len(preferred_order_tmp) >= swaprule[0] and len(preferred_order_tmp) >= swaprule[1] and swaprule[0] > 0 and swaprule[1] > 0:
					tmp = preferred_order_tmp[swaprule[0] - 1]
					preferred_order_tmp[swaprule[0] - 1] = preferred_order_tmp[swaprule[1] - 1]
					preferred_order_tmp[swaprule[1] - 1] = tmp

			for number in preferred_order_tmp:
				if number not in bouquets_to_hide:
					if number in sections and number != first_section:
						bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
						bouquet_current.write("#DESCRIPTION %s%s\n" % (section_prefix, sections[number]))
				if number in services["video"] and number not in bouquets_to_hide:
					bouquet_current.write("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
							services["video"][number]["service_type"],
							services["video"][number]["service_id"],
							services["video"][number]["transport_stream_id"],
							services["video"][number]["original_network_id"],
							services["video"][number]["namespace"]
						))
					if "interactive_name" in services["video"][number]:
						bouquet_current.write("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])
				else:
					bouquet_current.write("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
					bouquet_current.write("#DESCRIPTION  \n")

				current_number += 1

			bouquet_current.close()

		elif provider_config.isMakeHDMain() or provider_config.isMakeFTAHDMain():
			bouquet_current = open(path + "/autobouquet.%s.main.tv" % section_identifier, "w")
			if provider_config.isMakeHDMain():
				bouquet_current.write("#NAME %sHD Channels\n" % section_prefix)
			elif provider_config.isMakeFTAHDMain():
				bouquet_current.write("#NAME %sFTA HD Channels\n" % section_prefix)

			higher_number = sorted(sections.keys())[0]
			section_keys_temp = sorted(sections.keys())
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

				for number in hd_channels_numbers:
					if number >= section_key_current:
						todo = None
						if section_key_current not in bouquets_to_hide:
							bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
							bouquet_current.write("#DESCRIPTION %s%s\n" % (section_prefix, sections[section_key_current]))
							todo = section_key_current

						section_keys_temp.remove(section_key_current)
						if len(section_keys_temp) > 0:
							section_key_current = section_keys_temp[0]
						else:
							section_key_current = 65535

					if todo and number >= todo:
						if services["video"][number]["service_type"] >= 17 and (provider_config.isMakeHDMain() or (provider_config.isMakeFTAHDMain() and services["video"][number]["free_ca"] == 0)):  # from 17 to higher are HD?
							current_number += 1
							bouquet_current.write("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
									services["video"][number]["service_type"],
									services["video"][number]["service_id"],
									services["video"][number]["transport_stream_id"],
									services["video"][number]["original_network_id"],
									services["video"][number]["namespace"]
								))
							if "interactive_name" in services["video"][number]:
								bouquet_current.write("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])

					if current_number == higher_number - 1:
						break

				for x in range(current_number, higher_number - 1):
					bouquet_current.write("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
					bouquet_current.write("#DESCRIPTION  \n")

				current_number = higher_number - 1

			bouquet_current.close()
			force_keep_numbers = True

		elif provider_config.isMakeCustomMain():
			current_number = sorted(sections.keys())[0] - 1
			self.transformCustomInMain(path, provider_config.getCustomFilename(), current_number)
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
				bouquet_current = open(path + "/autobouquet.%s.%d.tv" % (section_identifier, section_number), "w")
				if section_number not in bouquets_to_hide:
					bouquet_current.write("#NAME %s%s\n" % (section_prefix, section_name))
					bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
					bouquet_current.write("#DESCRIPTION %s%s\n" % (section_prefix, section_name))
				else:
					bouquet_current.write("#NAME %sHidden\n" % section_prefix)
					bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
					bouquet_current.write("#DESCRIPTION %sHidden\n" % section_prefix)

				#current_number += 1
				section_current_number += 1
				for number in range(section_current_number, higher_number + 1):
					if number in services["video"] and section_number not in bouquets_to_hide:
						bouquet_current.write("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
								services["video"][number]["service_type"],
								services["video"][number]["service_id"],
								services["video"][number]["transport_stream_id"],
								services["video"][number]["original_network_id"],
								services["video"][number]["namespace"]
							))
						if "interactive_name" in services["video"][number]:
							bouquet_current.write("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])
						current_number += 1
					elif force_keep_numbers:
						bouquet_current.write("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
						bouquet_current.write("#DESCRIPTION  \n")
						current_number += 1

				bouquet_current.close()
				section_current_number = higher_number

		# HD channels
		if provider_config.isMakeHD():
			bouquet_current = open(path + "/autobouquet.%s.hd.tv" % section_identifier, "w")

			bouquet_current.write("#NAME %sHD Channels\n" % section_prefix)

			section_keys_temp = sorted(sections.keys())
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

			for number in hd_channels_numbers:
				if number >= section_key_current:
					if section_key_current not in bouquets_to_hide:
						bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
						bouquet_current.write("#DESCRIPTION %s%s\n" % (section_prefix, sections[section_key_current]))
					section_keys_temp.remove(section_key_current)
					if len(section_keys_temp) > 0:
						section_key_current = section_keys_temp[0]
					else:
						section_key_current = 65535

				if section_key_current not in bouquets_to_hide:
					if services["video"][number]["service_type"] >= 17:		# from 17 to higher are HD?
						bouquet_current.write("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
								services["video"][number]["service_type"],
								services["video"][number]["service_id"],
								services["video"][number]["transport_stream_id"],
								services["video"][number]["original_network_id"],
								services["video"][number]["namespace"]
							))
						if "interactive_name" in services["video"][number]:
							bouquet_current.write("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])

						current_number += 1

			bouquet_current.close()

		# FTA channels
		if provider_config.isMakeFTA():
			bouquet_current = open(path + "/autobouquet.%s.fta.tv" % section_identifier, "w")
			bouquet_current.write("#NAME %sFTA Channels\n" % section_prefix)
			bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
			bouquet_current.write("#DESCRIPTION %sFTA Channels\n" % section_prefix)
			higher_number = sorted(services["video"].keys())[-1]
			for number in range(1, higher_number + 1):
				if number in services["video"] and services["video"][number]["free_ca"] == 0 and number not in bouquets_to_hide:
					bouquet_current.write("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
							services["video"][number]["service_type"],
							services["video"][number]["service_id"],
							services["video"][number]["transport_stream_id"],
							services["video"][number]["original_network_id"],
							services["video"][number]["namespace"]
						))
					if "interactive_name" in services["video"][number]:
						bouquet_current.write("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])
					current_number += 1

			bouquet_current.close()

		bouquet_current = open(path + "/autobouquet.%s.separator.tv" % section_identifier, "w")
		bouquet_current.write("#NAME %sSeparator\n" % section_prefix)
		bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
		bouquet_current.write("#DESCRIPTION %sSeparator\n" % section_prefix)

		for x in range(current_number, (int(current_number/1000) + 1) * 1000):
			bouquet_current.write("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
			bouquet_current.write("#DESCRIPTION  \n")

		bouquet_current.close()


		# FTA HD channels
		if provider_config.isMakeFTAHD():
			bouquet_current = open(path + "/autobouquet.%s.ftahd.tv" % section_identifier, "w")

			bouquet_current.write("#NAME %sFTA HD Channels\n" % section_prefix)

			section_keys_temp = sorted(sections.keys())
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

			for number in hd_channels_numbers:
				if number >= section_key_current:
					if section_key_current not in bouquets_to_hide:
						bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
						bouquet_current.write("#DESCRIPTION %s%s\n" % (section_prefix, sections[section_key_current]))
					section_keys_temp.remove(section_key_current)
					if len(section_keys_temp) > 0:
						section_key_current = section_keys_temp[0]
					else:
						section_key_current = 65535

				if section_key_current not in bouquets_to_hide:
					if services["video"][number]["service_type"] >= 17 and services["video"][number]["free_ca"] == 0 and number not in bouquets_to_hide:		# from 17 to higher are HD?
						bouquet_current.write("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
								services["video"][number]["service_type"],
								services["video"][number]["service_id"],
								services["video"][number]["transport_stream_id"],
								services["video"][number]["original_network_id"],
								services["video"][number]["namespace"]
							))
						if "interactive_name" in services["video"][number]:
							bouquet_current.write("#DESCRIPTION %s\n" % services["video"][number]["interactive_name"])

						current_number += 1

			bouquet_current.close()

		# now the radio bouquet
		bouquet_current = open(path + "/autobouquet.%s.main.radio" % section_identifier, "w")
		bouquet_current.write("#NAME %sRadio channels\n" % section_prefix)
		bouquet_current.write("#SERVICE 1:64:0:0:0:0:0:0:0:0:\n")
		bouquet_current.write("#DESCRIPTION %sRadio channels\n" % section_prefix)

		if len(services["radio"].keys()) > 0:
			higher_number = sorted(services["radio"].keys())[-1]	# the highest number!
			for number in range(1, higher_number + 1):
				if number in services["radio"]:
					bouquet_current.write("#SERVICE 1:0:%x:%x:%x:%x:%x:0:0:0:\n" % (
							services["radio"][number]["service_type"],
							services["radio"][number]["service_id"],
							services["radio"][number]["transport_stream_id"],
							services["radio"][number]["original_network_id"],
							services["radio"][number]["namespace"]
						))
				else:
					bouquet_current.write("#SERVICE 1:832:d:0:0:0:0:0:0:0:\n")
					bouquet_current.write("#DESCRIPTION  \n")

		bouquet_current.close()

		print>>log, "[BouquetsWriter] Done"

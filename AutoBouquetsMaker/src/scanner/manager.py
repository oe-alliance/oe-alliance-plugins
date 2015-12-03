from Components.config import config
from dvbscanner import DvbScanner
from bouquetswriter import BouquetsWriter
from bouquetsreader import BouquetsReader
from providers import Providers
from tools import Tools
from .. import log

class Manager():

	ABM_PREFIX = "userbouquet.abm."

	def __init__(self):
		self.path = "/etc/enigma2"
		self.bouquetsToKeep = {}
		self.bouquetsToHide = {}
		self.providerConfigs = {}
		self.transponders = {}
		self.services = {}
		self.bouquetsOrder = []
		self.serviceVideoRead = 0
		self.serviceAudioRead = 0
		self.addprefix = False
		self.adapter = 0
		self.demuxer = 0
		self.frontend = 0

	def setAdapter(self, id):
		self.adapter = id

	def setDemuxer(self, id):
		self.demuxer = id

	def setFrontend(self, id):
		self.frontend = id

	def setPath(self, path):
		self.path = path

	def getPath(self):
		return self.path

	def setBouquetsToKeep(self, bouquetsToKeepTv, bouquetsToKeepRadio):
		self.bouquetsToKeep["tv"] = bouquetsToKeepTv
		self.bouquetsToKeep["radio"] = bouquetsToKeepRadio

	def setBouquetsToHide(self, bouquetsToHide):
		self.bouquetsToHide = bouquetsToHide

	def setAddPrefix(self, value):
		self.addprefix = value

	def getServiceVideoRead(self):
		return self.serviceVideoRead

	def getServiceAudioRead(self):
		return self.serviceAudioRead

	def load(self):
		print>>log, "[Manager] Loading settings..."
		reader = BouquetsReader()
		self.transponders = reader.readLamedb(self.path)
		print>>log, "[Manager] Done"

	def save(self, providers, dependent_providers = {}):
		#merge dependent providers
		for provider_key in dependent_providers:
			if provider_key in self.services:
				for dependent_key in dependent_providers[provider_key]:
					if dependent_key in self.services:
						for type in ["video", "radio"]:
							for number in self.services[dependent_key][type]:
								self.services[provider_key][type][number] = self.services[dependent_key][type][number]

		print>>log, "[Manager] Saving..."

		old_bouquets = BouquetsReader().getBouquetsList(self.path)
		if "tv" not in old_bouquets:
			old_bouquets["tv"] = []
		if "radio" not in old_bouquets:
			old_bouquets["radio"] = []
		currentBouquets = {}
		currentBouquets["tv"] = []
		currentBouquets["radio"] = []
		for bouquet in old_bouquets["tv"]:
			currentBouquets["tv"].append(bouquet["filename"])
		for bouquet in old_bouquets["radio"]:
			currentBouquets["radio"].append(bouquet["filename"])
		if "tv" not in self.bouquetsToKeep:
			self.bouquetsToKeep["tv"] = []
		if "radio" not in self.bouquetsToKeep:
			self.bouquetsToKeep["radio"] = []

		print>>log, "[Manager] Bouquets to hide:", self.bouquetsToHide
		print>>log, "[Manager] TV bouquets to keep:", self.bouquetsToKeep["tv"]
		print>>log, "[Manager] Radio bouquets to keep:", self.bouquetsToKeep["radio"]
		#print>>log, "[Manager] Generate main bouquet:", str(self.makemain)
		#print>>log, "[Manager] Generate sections bouquets:", str(self.makesections)
		#print>>log, "[Manager] Generate HD bouquet:", str(self.makehd)
		#print>>log, "[Manager] Generate FTA bouquet:", str(self.makefta)
		print>>log, "[Manager] Add provider prefix to bouqets:", str(self.addprefix)

		writer = BouquetsWriter()
		writer.writeLamedb(self.path, self.transponders)
		#providers = Providers().read()
		bouquetsToHide = []

		for provider_key in self.bouquetsOrder:
			if provider_key in providers:
				# FTA_only
				if config.autobouquetsmaker.level.value == "expert" and provider_key in config.autobouquetsmaker.FTA_only.value:
					video_services_tmp = {}
					for number in self.services[provider_key]["video"]:
						if self.services[provider_key]["video"][number]["free_ca"] == 0:
							video_services_tmp[number] = self.services[provider_key]["video"][number]
					self.services[provider_key]["video"] = video_services_tmp

				# CustomLCN
				self.services[provider_key] = Tools().customLCN(self.services[provider_key], provider_key, self.providerConfigs[provider_key].getArea())

		for provider_key in self.bouquetsOrder:
			if provider_key in providers:
				bouquetsToHide = []
				if provider_key in self.bouquetsToHide:
					# expand section keys in channels numbers
					sections = sorted(providers[provider_key]["sections"].keys())
					for bouquetToHide in self.bouquetsToHide[provider_key]:
						try:
							#get closest section, just in case section numbers in the provider file have been updated
							bouquetToHide = min(sections, key=lambda x:abs(x-bouquetToHide))
							index = sections.index(bouquetToHide)
						except:
							continue
						if index < len(sections) - 1:
							bouquetsToHide += range(bouquetToHide, sections[index + 1])
						else:
							bouquetsToHide += range(bouquetToHide, 65535)

				prefix = ""
				if self.addprefix:
					prefix = providers[provider_key]["name"]

				current_bouquet_key = self.providerConfigs[provider_key].getArea()
				if current_bouquet_key in providers[provider_key]["bouquets"] and providers[provider_key]["protocol"] in ("sky", "freesat"):
					current_bouquet = providers[provider_key]["bouquets"][current_bouquet_key]["bouquet"]
					current_region = providers[provider_key]["bouquets"][current_bouquet_key]["region"]
				else:
					current_bouquet = -1
					current_region = -1

				preferred_order = []
				if (self.providerConfigs[provider_key].isMakeNormalMain() or self.providerConfigs[provider_key].isMakeSections()) and self.providerConfigs[provider_key].isSwapChannels():
					for swapchannels_set in providers[provider_key]["swapchannels"]:
						if len(preferred_order) == 0 and len(swapchannels_set["filters"]) == 0:
							preferred_order = swapchannels_set["preferred_order"]
							continue

						if len(swapchannels_set["filters"]) > 0:
							for cfilter in swapchannels_set["filters"]:
								if cfilter[0] == current_bouquet and cfilter[1] == current_region:
									preferred_order = swapchannels_set["preferred_order"]
									break

				if current_bouquet_key.startswith('sd'):
					channelsontop = providers[provider_key]["sdchannelsontop"],
				else:
					channelsontop = providers[provider_key]["hdchannelsontop"],

				# swap services between providers
				services, providers[provider_key]["sections"] = Tools().customMix(self.services, provider_key, providers[provider_key]["sections"], self.providerConfigs[provider_key])

				writer.buildBouquets(self.path,
						self.providerConfigs[provider_key],
						services,
						providers[provider_key]["sections"],
						provider_key,
						preferred_order,
						channelsontop,
						bouquetsToHide,
						prefix)

		# add a custom favourites list
		Tools().favourites(self.path, self.services, providers, self.providerConfigs, self.bouquetsOrder)

		writer.buildBouquetsIndex(self.path, self.bouquetsOrder, providers,
				self.bouquetsToKeep, currentBouquets, self.bouquetsToHide,
				self.providerConfigs)

		print>>log, "[Manager] Done"

	def read(self, provider_config, providers):
		ret = False
		provider_key = provider_config.getProvider()
		bouquet_key = provider_config.getArea()

		if bouquet_key is not None and len(bouquet_key) > 0:
			print>>log, "[Manager] Reading %s (%s)..." % (provider_key, bouquet_key)
		else:
			print>>log, "[Manager] Reading %s..." % provider_key

		# read custom transponder
		customtransponders = {}
		if bouquet_key is not None and len(bouquet_key) > 0:
			customtransponders = Tools().customtransponder(provider_key, bouquet_key)

		self.providerConfigs[provider_key] = provider_config

		#providers = Providers().read()
		if provider_key in providers:
			if bouquet_key in providers[provider_key]["bouquets"] or providers[provider_key]["protocol"] != "sky":
				scanner = DvbScanner()
				scanner.setAdapter(self.adapter)
				scanner.setDemuxer(self.demuxer)
				scanner.setFrontend(self.frontend)
				scanner.setDVBType(providers[provider_key]["streamtype"])
				scanner.setNitPid(providers[provider_key]["transponder"]["nit_pid"])
				scanner.setNitCurrentTableId(providers[provider_key]["transponder"]["nit_current_table_id"])
				scanner.setNitOtherTableId(providers[provider_key]["transponder"]["nit_other_table_id"])
				scanner.setVisibleServiceFlagIgnore(providers[provider_key]["ignore_visible_service_flag"])

				if providers[provider_key]["protocol"] in ('lcn', 'lcn2', 'lcnbat', 'lcnbat2', 'nolcn', 'vmuk'):
					scanner.setSdtPid(providers[provider_key]["transponder"]["sdt_pid"])
					scanner.setSdtCurrentTableId(providers[provider_key]["transponder"]["sdt_current_table_id"])
					scanner.setSdtOtherTableId(providers[provider_key]["transponder"]["sdt_other_table_id"])

					if providers[provider_key]["streamtype"] == 'dvbc':
						bouquet = providers[provider_key]["bouquets"][bouquet_key]
						tmp = scanner.updateTransponders(self.transponders, True, customtransponders, bouquet["netid"], bouquet["bouquettype"])
					else:
						try:
							bouquet_id = providers[provider_key]["bouquets"][bouquet_key]["bouquet"]
						except:
							bouquet_id = -1
						tmp = scanner.updateTransponders(self.transponders, True, customtransponders, bouquet_id = bouquet_id)
					if providers[provider_key]["protocol"] in ("lcnbat", "lcnbat2"):
						scanner.setBatPid(providers[provider_key]["transponder"]["bat_pid"])
						scanner.setBatTableId(providers[provider_key]["transponder"]["bat_table_id"])
						tmp["logical_channel_number_dict"], tmp["TSID_ONID_list"] = scanner.readLCNBAT(bouquet_id, providers[provider_key]["bouquets"][bouquet_key]["region"], tmp["TSID_ONID_list"])
					self.services[provider_key] = scanner.updateAndReadServicesLCN(
						self.transponders, providers[provider_key]["servicehacks"], tmp["TSID_ONID_list"],
						tmp["logical_channel_number_dict"], tmp["service_dict_tmp"], providers[provider_key]["protocol"], bouquet_key)

					ret = len(self.services[provider_key]["video"].keys()) > 0 or len(self.services[provider_key]["radio"].keys()) > 0

					self.serviceVideoRead += len(self.services[provider_key]["video"].keys())
					self.serviceAudioRead += len(self.services[provider_key]["radio"].keys())

				elif providers[provider_key]["protocol"] == "fastscan":
					scanner.setFastscanPid(providers[provider_key]["transponder"]["fastscan_pid"])
					scanner.setFastscanTableId(providers[provider_key]["transponder"]["fastscan_table_id"])

					tmp = scanner.updateTransponders(self.transponders, True)
					self.services[provider_key] = scanner.updateAndReadServicesFastscan(
							self.transponders, providers[provider_key]["servicehacks"],
							tmp["logical_channel_number_dict"])

					ret = len(self.services[provider_key]["video"].keys()) > 0 or len(self.services[provider_key]["radio"].keys()) > 0

					self.serviceVideoRead += len(self.services[provider_key]["video"].keys())
					self.serviceAudioRead += len(self.services[provider_key]["radio"].keys())

				elif providers[provider_key]["protocol"] == "sky":
					scanner.setSdtPid(providers[provider_key]["transponder"]["sdt_pid"])
					scanner.setSdtCurrentTableId(providers[provider_key]["transponder"]["sdt_current_table_id"])
					scanner.setSdtOtherTableId(providers[provider_key]["transponder"]["sdt_other_table_id"])
					scanner.setBatPid(providers[provider_key]["transponder"]["bat_pid"])
					scanner.setBatTableId(providers[provider_key]["transponder"]["bat_table_id"])

					scanner.updateTransponders(self.transponders, False)
					bouquet = providers[provider_key]["bouquets"][bouquet_key]
					self.services[provider_key] = scanner.updateAndReadServicesSKY(bouquet["bouquet"],
							bouquet["region"], bouquet["key"], self.transponders,
							providers[provider_key]["servicehacks"])

					ret = len(self.services[provider_key]["video"].keys()) > 0 or len(self.services[provider_key]["radio"].keys()) > 0

					self.serviceVideoRead += len(self.services[provider_key]["video"].keys())
					self.serviceAudioRead += len(self.services[provider_key]["radio"].keys())

				elif providers[provider_key]["protocol"] == "freesat":
					scanner.setSdtPid(providers[provider_key]["transponder"]["sdt_pid"])
					scanner.setSdtCurrentTableId(providers[provider_key]["transponder"]["sdt_current_table_id"])
					scanner.setSdtOtherTableId(providers[provider_key]["transponder"]["sdt_other_table_id"])
					scanner.setBatPid(providers[provider_key]["transponder"]["bat_pid"])
					scanner.setBatTableId(providers[provider_key]["transponder"]["bat_table_id"])

					scanner.updateTransponders(self.transponders, False)
					bouquet = providers[provider_key]["bouquets"][bouquet_key]
					self.services[provider_key] = scanner.updateAndReadServicesFreeSat(bouquet["bouquet"],
							bouquet["region"], bouquet["key"], self.transponders,
							providers[provider_key]["servicehacks"])

					ret = len(self.services[provider_key]["video"].keys()) > 0 or len(self.services[provider_key]["radio"].keys()) > 0

					self.serviceVideoRead += len(self.services[provider_key]["video"].keys())
					self.serviceAudioRead += len(self.services[provider_key]["radio"].keys())

				else:
					print>>log, "[Manager] Unsupported protocol %s" % providers[provider_key]["protocol"]
					ret = False

				if provider_key not in self.bouquetsOrder:
					if provider_key in config.autobouquetsmaker.providers.value: # not a descendent provider
						self.bouquetsOrder.append(provider_key)

		print>>log, "[Manager] Done"
		return ret

	def getBouquetsList(self):
		return BouquetsReader().getBouquetsList(self.path)

	def getProviders(self):
		return Providers().read()

#manager = Manager()
# #print manager.getBouquetsList()
# #providers = manager.getProviders()
# #print providers
# #for provider_key in providers:
# #	current_arealist = []
# #	bouquets = providers[provider_key]["bouquets"]
# #	for bouquet_key in bouquets.keys():
# #		current_arealist.append((bouquet_key, providers[provider_key]["bouquets"][bouquet_key]["name"]))
# #
# #	print provider_key, current_arealist
#
#manager.setPath("/tmp/settings")
# #manager.checkTransponderInLamedb(["skyit", "skyuk"])
# #if manager.checkTransponderInLamedb(["skyit"]):
# 	# ok.. if checkTransponderInLamedb return True the plugin must reload the lamedb. Otherwise the tune fail!!
# #	pass
#
# manager.setBouquetsToKeep(["userbouquet.dbe55.tv", "userbouquet.dbe26.tv"], ["userbouquet.dbe03.radio"])
# manager.setBouquetsToHide({ "skyit": [ 200, 700 ] })
#from providerconfig import ProviderConfig
#
#config = ProviderConfig()
#config.setProvider("skyit")
#config.setArea("sky_italy_hd")
#manager.load()
#manager.read(config)
#manager.save()
#

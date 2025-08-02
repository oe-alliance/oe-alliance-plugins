#
#   Copyright (C) 2021 Team OpenSPA
#   https://openspa.info/
#
#   Copyright (c) 2021-2024 Billy2011 @ vuplus-support.org
#   20210618 (1st release)
#   - adaptions for VTI
#   - many fixes, improvements, mods & rewrites
#   - py3 adaption
#   20240831 (latest release)
#
#   Copyright (c) 2025 jbleyel
#   20250731 (release)
#   - remove python2 code
#   - remove twisted downloadPage
#
#   SPDX-License-Identifier: GPL-2.0-or-later
#   See LICENSES/README.md for more information.
#
#   PlutoTV is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PlutoTV is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with PlutoTV.  If not, see <http://www.gnu.org/licenses/>.
#
#

import datetime
import os
import re
from pickle import dump, load
from shutil import copy2
import time
import traceback
import unicodedata
import uuid

import requests
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.config import ConfigDirectory, ConfigSelection, ConfigSubsection, ConfigYesNo, config
from Plugins.Extensions.PlutoTV import downloader
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists, pathExists
from enigma import eDVBDB, eEPGCache, eServiceCenter, eServiceReference, eTimer, getDesktop
from twisted.internet import defer, reactor

from . import _, update_qsd

BASE_API = "https://api.pluto.tv"
GUIDE_URL = "https://service-channels.clusters.pluto.tv/v1/guide"
BASE_GUIDE = BASE_API + "/v2/channels"
BASE_LINEUP = BASE_API + "/v2/channels"
BASE_VOD = BASE_API + "/v3/vod/categories"
SEASON_VOD = BASE_API + "/v3/vod/series/%s/seasons"
BOUQUET = "userbouquet.pluto_tv{0}.tv"

sid1_hex = str(uuid.uuid4().hex)
deviceId1_hex = str(uuid.uuid1().hex)

config.plugins.plutotv = ConfigSubsection()
config.plugins.plutotv.add_latin_regions = ConfigYesNo(default=True)
config.plugins.plutotv.add_xiaomi = ConfigYesNo(default=False)
config.plugins.plutotv.add_samsung = ConfigYesNo(default=True)

_regions = {
	"local": _("Local"),
	"at": f"{_('AT')}, {_('Austria')}",
	"ca": f"{_('CA')}, {_('Canada')}",
	"ch": f"{_('CH')}, {_('Switzerland')}",
	"de": f"{_('DE')}, {_('Germany')}",
	"es": f"{_('ES')}, {_('Spain')}",
	"fi": f"{_('FI')}, {_('Finland')}",
	"fr": f"{_('FR')}, {_('France')}",
	"it": f"{_('IT')}, {_('Italy')}",
	"mx": f"{_('MX')}, {_('Mexico')}",
	"uk": f"{_('UK')}, {_('United Kingdom')}",
	"us": f"{_('US')}, {_('United States')}",
	"ar": f"{_('AR')}, {_('Argentina')}",
	"br": f"{_('BR')}, {_('Brazil')}",
	"co": f"{_('CO')}, {_('Colombia')}",
	"cr": f"{_('CR')}, {_('Costa Rica')}",
	"pe": f"{_('PE')}, {_('Peru')}",
	"ve": f"{_('VE')}, {_('Venezuela')}",
	"cl": f"{_('CL')}, {_('Chile')}",
	"bo": f"{_('BO')}, {_('Bolivia')}",
	"sv": f"{_('SV')}, {_('El Salvador')}",
	"gt": f"{_('GT')}, {_('Guatemala')}",
	"hn": f"{_('HN')}, {_('Honduras')}",
	"ni": f"{_('NI')}, {_('Nicaragua')}",
	"pa": f"{_('PA')}, {_('Panama')}",
	"uy": f"{_('UY')}, {_('Uruguay')}",
	"ec": f"{_('EC')}, {_('Ecuador')}",
	"py": f"{_('PY')}, {_('Paraguay')}",
	"do": f"{_('DO')}, {_('Dominican Republic')}",
	"se": f"{_('SE')}, {_('Sweden')}",
	"dk": f"{_('DK')}, {_('Denmark')}",
	"no": f"{_('NO')}, {_('Norway')}",
	"au": f"{_('AU')}, {_('Australia')}",
}

BASE_REGIONS = [
	("at", f"{_regions['at']}"),
	("au", f"{_regions['au']}"),
	("ca", f"{_regions['ca']}"),
	("ch", f"{_regions['ch']}"),
	("de", f"{_regions['de']}"),
	("dk", f"{_regions['dk']}"),
	("es", f"{_regions['es']}"),
	("fi", f"{_regions['fi']}"),
	("fr", f"{_regions['fr']}"),
	("it", f"{_regions['it']}"),
	("mx", f"{_regions['mx']}"),
	("no", f"{_regions['no']}"),
	("se", f"{_regions['se']}"),
	("uk", f"{_regions['uk']}"),
	("us", f"{_regions['us']}"),
]

# Latin American regions
LATIN_REGIONS = [
	("ar", f"{_regions['ar']}"),
	("br", f"{_regions['br']}"),
	("co", f"{_regions['co']}"),
	("cr", f"{_regions['cr']}"),
	("pe", f"{_regions['pe']}"),
	("ve", f"{_regions['ve']}"),
	("cl", f"{_regions['cl']}"),
	("bo", f"{_regions['bo']}"),
	("sv", f"{_regions['sv']}"),
	("gt", f"{_regions['gt']}"),
	("hn", f"{_regions['hn']}"),
	("ni", f"{_regions['ni']}"),
	("pa", f"{_regions['pa']}"),
	("uy", f"{_regions['uy']}"),
	("ec", f"{_regions['ec']}"),
	("py", f"{_regions['py']}"),
	("do", f"{_regions['do']}"),
]

if config.plugins.plutotv.add_latin_regions.value:
	BASE_REGIONS += LATIN_REGIONS
	BASE_REGIONS.sort()
REGIONS = [("local", _("Local"))] + BASE_REGIONS
CH_REGIONS = REGIONS + [("none", _("NONE"))]

SERVICES = {
	"4097": _("Original (4097)"),
	"5001": "ServiceGstPlayer (5001)",
	"5002": "ServiceExtPlayer3 (5002)",
}
config.plugins.plutotv.live_tv_ch_numbering = ConfigSelection(
	default="original", choices={"original": _("Original"), "plugin": _("Plugin generated")}
)
config.plugins.plutotv.live_tv_mode = ConfigSelection(
	default="samsung", choices={"original": _("Original"), "roku": "Roku TV", "samsung": "Samsung TV"}
)
config.plugins.plutotv.region = ConfigSelection(default="local", choices=REGIONS)
config.plugins.plutotv.ch_region_1 = ConfigSelection(default="local", choices=CH_REGIONS)
config.plugins.plutotv.ch_region_2 = ConfigSelection(default="none", choices=CH_REGIONS)
config.plugins.plutotv.ch_region_3 = ConfigSelection(default="none", choices=CH_REGIONS)
config.plugins.plutotv.ch_region_4 = ConfigSelection(default="none", choices=CH_REGIONS)
config.plugins.plutotv.ch_region_5 = ConfigSelection(default="none", choices=CH_REGIONS)
config.plugins.plutotv.service_1 = ConfigSelection(default="4097", choices=SERVICES)
config.plugins.plutotv.service_2 = ConfigSelection(default="4097", choices=SERVICES)
config.plugins.plutotv.service_3 = ConfigSelection(default="4097", choices=SERVICES)
config.plugins.plutotv.service_4 = ConfigSelection(default="4097", choices=SERVICES)
config.plugins.plutotv.service_5 = ConfigSelection(default="4097", choices=SERVICES)

X_FORWARDS = {
	"us": "185.236.200.172",  # NOSONAR
#	"uk": "185.86.151.11",
	"uk": "185.199.220.58",  # NOSONAR
	"de": "85.214.132.117",  # NOSONAR
	"es": "88.26.241.248",  # NOSONAR
	"ca": "192.206.151.131",  # NOSONAR
	"br": "177.47.27.205",  # NOSONAR
	"mx": "200.68.128.83",  # NOSONAR
	"fr": "176.31.84.249",  # NOSONAR
	"at": "2.18.68.0",  # NOSONAR
	"ch": "5.144.31.245",  # NOSONAR
	"it": "5.133.48.0",  # NOSONAR
	"ar": "104.103.238.0",  # NOSONAR
	"co": "181.204.4.74",  # NOSONAR
	"cr": "138.122.24.0",  # NOSONAR
	"pe": "190.42.0.0",  # NOSONAR
	"ve": "103.83.193.0",  # NOSONAR
	"cl": "161.238.0.0",  # NOSONAR
	"bo": "186.27.64.0",  # NOSONAR
	"sv": "190.53.128.0",  # NOSONAR
	"gt": "190.115.2.25",  # NOSONAR
	"hn": "181.115.0.0",  # NOSONAR
	"ni": "186.76.0.0",  # NOSONAR
	"pa": "168.77.0.0",  # NOSONAR
	"uy": "179.24.0.0",  # NOSONAR
	"ec": "181.196.0.0",  # NOSONAR
	"py": "177.250.0.0",  # NOSONAR
	"do": "152.166.0.0",  # NOSONAR
	"se": "185.39.146.168",  # NOSONAR
	"dk": "80.63.84.58",  # NOSONAR
	"no": "84.214.150.146",  # NOSONAR
	"au": "144.48.37.140",  # NOSONAR
	"fi": "85.194.236.0",  # NOSONAR
}

TIDS = {
	"local": "0",
	"br": "100",
	"ca": "101",
	"de": "102",
	"es": "103",
	"fr": "104",
	"mx": "105",
	"uk": "106",
	"us": "107",
	"at": "108",
	"ch": "109",
	"it": "10A",
	"ar": "10B",
	"co": "10C",
	"cr": "10D",
	"pe": "10E",
	"ve": "10F",
	"cl": "110",
	"bo": "111",
	"sv": "112",
	"gt": "113",
	"hn": "114",
	"ni": "115",
	"pa": "116",
	"uy": "117",
	"ec": "118",
	"py": "119",
	"do": "11A",
	"se": "11B",
	"dk": "11C",
	"no": "11D",
	"au": "11E",
	"fi": "11F",
}

PICON_MODES = [("srp", _("Reference")), ("name", _("Name")), ("snp", _("SNP"))]
config.plugins.plutotv.picon_mode = ConfigSelection(default="srp", choices=PICON_MODES)

screenWidth = getDesktop(0).size().width()
config.usage.picon_dir = ConfigDirectory(default="/usr/share/enigma2/picon")
picon_dir = config.usage.picon_dir.value
if not pathExists(picon_dir):
	os.makedirs(picon_dir)


def transcode_str(s):
	return s.decode()


def getUUID():
	return sid1_hex, deviceId1_hex


def buildHeader():
	header_dict = {}
	header_dict["Accept"] = "application/json, text/javascript, */*; q=0.01"
	header_dict["Host"] = "api.pluto.tv"
	header_dict["Connection"] = "keep-alive"
	header_dict["Referer"] = "http://pluto.tv/"
	header_dict["Origin"] = "http://pluto.tv"
	header_dict["User-Agent"] = "Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0"
	return header_dict


def getVOD(epid, region=None):
	headers = buildHeader()
	region = region or config.plugins.plutotv.region.value
	if region in X_FORWARDS:
		headers["X-Forwarded-For"] = X_FORWARDS[region]
	params = {
		"includeItems": "true",
		"deviceType": "web",
		"deviceId": deviceId1_hex,
		"sid": sid1_hex,
	}
	return getURL(SEASON_VOD % epid, header=headers, param=params, life=datetime.timedelta(hours=1))


def getOndemand():
	headers = buildHeader()
	region = config.plugins.plutotv.region.value
	if region in X_FORWARDS:
		headers["X-Forwarded-For"] = X_FORWARDS[region]
	params = {
		"includeItems": "true",
		"deviceType": "web",
		"deviceId": deviceId1_hex,
		"sid": sid1_hex,
	}
	return region, getURL(BASE_VOD, header=headers, param=params, life=datetime.timedelta(hours=1))


def getURL(
	url,
	param={},
	header={"User-agent": "Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0"},
	life=datetime.timedelta(minutes=15),
):
	try:
		req = requests.get(url, param, headers=header)
		req.raise_for_status()
		return req.json()
	except Exception:
		print(f"[PlutoDownload] error: {traceback.format_exc()}")
		return {}


class DownloadComponent(downloader.PlutoDownloader):
	EVENT_DOWNLOAD = 0
	EVENT_DONE = 1
	EVENT_ERROR = 2

	def __init__(self, n, ref, picon=False):
		self.picon = picon
		self.number = n
		self.ref = ref

	def startCmd(self, cmd):
		filename = os.path.join(picon_dir, self.ref.replace(":", "_") + ".png")
		if filename:
			self.filename = filename
		else:
			self.filename = cmd.split("/")[-1]

		if not cmd:
			return defer.fail(self.EVENT_ERROR)
		elif not self.picon and fileExists(filename):
			return defer.succeed(self.EVENT_DONE)

		return (
			self.start(filename, str(cmd + "?h=132&w=220"), overwrite=self.picon)
			.addCallback(lambda result: self.EVENT_DONE)
			.addErrback(lambda result: filename)
		)


class PlutoAPIDownloader(object):
	service_types_tv = (
		"1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 134) || (type == 195)"
	)
	CH_NUMBERS_PATH = "/etc/enigma2/plutotv-numbers"

	def __init__(self, silent):
		self.silent = silent
		self.iprogress = 0
		self.total = 0
		self.epgcache = eEPGCache.getInstance()
		self.state = 1
		self.salir_called = False
		self.service_nums = {"local": config.plugins.plutotv.service_1.value}
		self.downloadActive = False
		self.ChannelsList = {}
		self.GuideList = {}
		self.Categories = []
		self.pfunc = {"name": lambda n: str(n).replace("/", "_"), "srp": lambda n: "", "snp": self._snp}
		self.skip_samsung = False
		self.skip_xiaomi = False

	@defer.inlineCallbacks
	def download(self):
		if self.downloadActive:
			if not self.silent:
				msg = _("The silent download is in progress.")
				res = self.session.openWithCallback(self.close, MessageBox, msg, MessageBox.TYPE_INFO, timeout=30)
			print("[PlutoDownload] download is in progress.")
			return

		self.downloadActive = True
		self.abort = False
		print("[PlutoDownload] download is active.")

		self.read_ch_numbers()
		upd_list = [
			config.plugins.plutotv.ch_region_1.value,
			config.plugins.plutotv.ch_region_2.value,
			config.plugins.plutotv.ch_region_3.value,
			config.plugins.plutotv.ch_region_4.value,
			config.plugins.plutotv.ch_region_5.value,
		]
		self.service_nums[config.plugins.plutotv.ch_region_1.value] = config.plugins.plutotv.service_1.value
		self.service_nums[config.plugins.plutotv.ch_region_2.value] = config.plugins.plutotv.service_2.value
		self.service_nums[config.plugins.plutotv.ch_region_3.value] = config.plugins.plutotv.service_3.value
		self.service_nums[config.plugins.plutotv.ch_region_4.value] = config.plugins.plutotv.service_4.value
		self.service_nums[config.plugins.plutotv.ch_region_5.value] = config.plugins.plutotv.service_5.value

		self.TimerTemp = eTimer()
		self.TimerTemp.callback.append(self.tmCallback)
		self.skip_samsung = not config.plugins.plutotv.add_samsung.value
		self.skip_xiaomi = not config.plugins.plutotv.add_xiaomi.value
		print("[PlutoDownload] skip_samsung: ", self.skip_samsung)
		print("[PlutoDownload] skip_xiaomi: ", self.skip_xiaomi)
		self.ch_numbering = config.plugins.plutotv.live_tv_ch_numbering.value
		print("[PlutoDownload] ch_numbering: ", self.ch_numbering)
		self.live_tv_mode = config.plugins.plutotv.live_tv_mode.value
		print("[PlutoDownload] live_tv_mode: ", self.live_tv_mode)
		self.picon_mode = config.plugins.plutotv.picon_mode.value
		print("[PlutoDownload] picon_mode: ", self.picon_mode)
		try:
			for region in filter(lambda v: v != "none", set(upd_list)):
				self.region = region
				_msg = _("Pluto TV download: {0}").format(_regions[region])
				if not self.silent:
					self["action"].setText(_msg)
				print(_msg)
				self.ChannelsList.clear()
				self.GuideList.clear()
				self.Categories *= 0

				print("[PlutoDownload] get channels...")
				channels = self.getChannels(ch_region=region)
				print("[PlutoDownload] get guide...")
				guide = self.getGuidedata(ch_region=region)
				print("[PlutoDownload] build m3u...")
				self.total = 0
				[self.buildM3U(channel) for channel in channels]

				if len(self.Categories) == 0:
					print(
						"[PlutoDownload] There is no data, it is possible that Pluto TV is not available in region '{0}'.".format(
							_regions[region]
						)
					)
					if not self.silent:
						self.d_close = defer.Deferred()
						self.session.openWithCallback(
							self.salirok,
							MessageBox,
							_(
								"There is no data, it is possible that Pluto TV is not available in region '{0}'. Exit now?"
							).format(_regions[region]),
							type=MessageBox.TYPE_YESNO,
							timeout=10,
						)
						res = yield self.d_close
						if res:
							raise Exception("[PlutoDownload] Update was canceled by the user.")
				else:
					print(f"[PlutoDownload] plutotv build guide, region '{_regions[region]}'...")
					self.keystot = len(self.ChannelsList)
					self.subtotal = len(self.ChannelsList[self.Categories[0]])
					self.key = 0
					self.chitem = 0
					for icnt, ch in enumerate(filter(lambda v: v.get("_id"), guide)):
						if self.abort:
							break
						self.iprogress = icnt * 50 // len(guide)
						self.buildGuide(ch, ch.get("_id"))
						self.deferred = defer.Deferred()
						self.TimerTemp.start(1, True)
						yield self.deferred

					print(f"[PlutoDownload] build bouquet, region '{_regions[region]}'...")
					bq = f"_{region}" if region != "local" else ""
					bq = BOUQUET.format(bq)
					pluto_refs = yield self.build_bouquet(bq, region)
					self.iprogress = 100
					if self.abort:
						break

					with open("/etc/enigma2/bouquets.tv", "r") as fd:
						bouquets = fd.read()
					if bq not in bouquets:
						print(f"[PlutoDownload] add bouquet, region '{_regions[region]}'...")
						self.addBouquet(bq, region)

					db = eDVBDB.getInstance()
					db.reloadServicelist()
					db.reloadBouquets()

					print(f"[PlutoDownload] import epg, region '{_regions[region]}'...")
					evt_cnt = 0
					for ch, ref in pluto_refs.items():
						for genre in iter(self.GuideList.get(ch, [])):
							evt_cnt += len(genre)
							self.epgcache.importEvents(ref, genre)
					print(f"[PlutoDownload] {evt_cnt} events imported, for {self.total} channels")

					if not self.silent:
						self["status"].setText(_("Wait..."))

					self.iprogress = 0
					self.deferred = defer.Deferred()
					self.TimerTemp.start(2 * 1000, True)
					yield self.deferred

			with open("/etc/Plutotv.timer", "w") as fd:
				fd.write(str(time.time()))
		except Exception:
			print(f"[PlutoDownload] error: {traceback.format_exc()}")
			if not self.silent and not self.abort:
				self.session.open(
					MessageBox,
					_("An error occurred while updating region '{0}', update aborted.").format(_regions[region]),
					type=MessageBox.TYPE_ERROR,
					timeout=10,
				)
			print(f"[PlutoDownload] an error occurred while updating region '{_regions[region]}', update aborted.")
			self.abort = True

		if not self.silent:
			self.salirok(deferred=False)
		else:
			self.start()

		self.ChannelsList.clear()
		self.GuideList.clear()
		self.Categories *= 0
		self.save_ch_numbers()
		self.ch_numbers.clear()
		self.downloadActive = False
		print("[PlutoDownload] download finished")

	def tmCallback(self):
		if not self.silent:
			self["progress"].setValue(self.iprogress)
			self["espera"].setText(f"{self.iprogress} %")

		if not self.deferred.called:
			self.deferred.callback(None)

	@defer.inlineCallbacks
	def salir(self):
		if self.salir_called:
			return

		self.salir_called = True
		self.d_close = defer.Deferred()
		stri = _("The download is in progress. Exit now?")
		self.session.openWithCallback(self.salirok, MessageBox, stri, MessageBox.TYPE_YESNO, timeout=30)
		yield self.d_close
		self.salir_called = False

	def salirok(self, answer=True, deferred=True):
		if answer and not deferred:
			Silent.stop()
			Silent.start()
			self.close(not self.abort)
		elif deferred:
			self.abort = answer
			if not self.d_close.called:
				self.d_close.callback(answer)

	@defer.inlineCallbacks
	def build_bouquet(self, bouquet, region):
		pluto_refs = {}
		service_num = self.service_nums[region]
		print("build_bouquet", service_num)
		bq = []
		nm = f" ({region.upper()})" if region != "local" else ""
		bq.append(f"#NAME Pluto TV{nm}\n")
		param = 0
		group = 0
		for cat in iter(self.Categories):
			bq.append(f"#SERVICE 1:64:{group}:0:0:0:0:0:0:0::{cat}\n#DESCRIPTION {cat}\n")
			group += 1
			for param, channel in enumerate(self.ChannelsList[cat], param + 1):
				if self.abort:
					return

				if not self.silent:
					self.iprogress = param * 50 // self.total + 50

				name = channel[2].replace(":", "%3A")
				sref = "#SERVICE %s:0:1:%s:%s:0:0:0:0:0:%s:%s" % (
					service_num,
					channel[0],
					TIDS[region],
					channel[4].replace(":", "%3A"),
					name,
				)
				bq.append(f"{sref}\n#DESCRIPTION {channel[2]}\n")

				ref = f"{service_num}:0:1:{channel[0]}:{TIDS[region]}:0:0:0:0:0"
				pluto_refs[channel[1]] = ref + ":0"
				if not self.silent:
					self["status"].setText(_("Wait for Channel: {0}").format(channel[2]))

				logo = channel[3]
				if config.plugins.plutotv.picon_mode.value == "srp":
					down = DownloadComponent(param, ref, not self.silent)
				else:
					down = DownloadComponent(param, channel[5], not self.silent)

				def downloadFini(result):
					if result != DownloadComponent.EVENT_DONE:
						copy2("/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/picon.png", result)
						return DownloadComponent.EVENT_DONE
					else:
						return result

				yield down.startCmd(logo).addBoth(downloadFini)
				self.deferred = defer.Deferred()
				self.TimerTemp.start(2, True)
				yield self.deferred

		with open("/etc/enigma2/" + bouquet, "w") as fd:
			[fd.write(v) for v in bq]
		defer.returnValue(pluto_refs)

	@staticmethod
	def getLocalTime():
		offset = datetime.datetime.utcnow() - datetime.datetime.now()
		return time.time() + offset.total_seconds()

	@staticmethod
	def strpTime(datestring, format="%Y-%m-%dT%H:%M:%S.%fZ"):
		try:
			return datetime.datetime.strptime(datestring, format)
		except TypeError:
			return datetime.datetime.fromtimestamp(time.mktime(time.strptime(datestring, format)))

	@staticmethod
	def getChannels(ch_region="local"):
		params = {
			"deviceId": deviceId1_hex,
			"sid": sid1_hex,
		}
		headers = buildHeader()
		if ch_region in X_FORWARDS:
			headers["X-Forwarded-For"] = X_FORWARDS[ch_region]
		return sorted(
			getURL(BASE_LINEUP, header=headers, param=params, life=datetime.timedelta(hours=1)),
			key=lambda i: i["number"],
		)

	def getGuidedata(self, full=False, ch_region="local"):
		start = datetime.datetime.fromtimestamp(self.getLocalTime()).strftime("%Y-%m-%dT%H:00:00Z")
		stop = (datetime.datetime.fromtimestamp(self.getLocalTime()) + datetime.timedelta(hours=24)).strftime(
			"%Y-%m-%dT%H:00:00Z"
		)

		params = {
			"start": start,
			"stop": stop,
			"deviceId": deviceId1_hex,
			"sid": sid1_hex,
		}
		headers = {}
		headers["User-agent"] = "Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0"
		if ch_region in X_FORWARDS:
			headers["X-Forwarded-For"] = X_FORWARDS[ch_region]
		if full:
			return getURL(GUIDE_URL, header=headers, param=params, life=datetime.timedelta(hours=1))
		else:
			return sorted(
				(getURL(BASE_GUIDE, header=headers, param=params, life=datetime.timedelta(hours=1))),
				key=lambda i: i["number"],
			)

	@staticmethod
	def _snp(name):
		name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore")
		name = transcode_str(name)
		return re.sub(r"[^a-z0-9]", "", name.replace("&", "and").replace("+", "plus").replace("*", "star").lower())

	def buildM3U(self, channel):
		group = channel.get("category", "")
		if self.skip_samsung and group == "Samsung":
			return
		if self.skip_xiaomi and group == "Xiaomi TV":
			return
		logo = channel.get("colorLogoPNG", {}).get("path", None)
		_id = channel["_id"]
		urls = channel.get("stitched", {}).get("urls")
		if not isinstance(urls, list) or len(urls) == 0:
			return False

		if self.live_tv_mode == "samsung":
			urls = (
				"http%3a//stitcher-ipv4.pluto.tv/v1/stitch/embed/hls/channel/{0}/master.m3u8"
				"?deviceType=samsung-tvplus&deviceMake=samsung&deviceModel=samsung&deviceVersion=unknown&appVersion=unknown"
				"&deviceLat=0&deviceLon=0&deviceDNT=%7BTARGETOPT%7D&deviceId=%7BPSID%7D&advertisingId=%7BPSID%7D"
				"&us_privacy=1YNY&samsung_app_domain=%7BAPP_DOMAIN%7D&samsung_app_name=%7BAPP_NAME%7D&profileLimit="
				"&profileFloor=&embedPartner=samsung-tvplus"
			).format(_id)
		elif self.live_tv_mode == "roku":
			urls = (
				"http%3a//stitcher-ipv4.pluto.tv/v1/stitch/embed/hls/channel/{0}/master.m3u8"
				"?deviceId=PSID&deviceModel=web&deviceVersion=1.0&appVersion=1.0&deviceType=rokuChannel"
				"&deviceMake=rokuChannel&deviceDNT=1"
			).format(_id)
		elif self.live_tv_mode == "original":
			urls = [
				update_qsd(
					url["url"],
					{
						"deviceType": "web",
						"deviceMake": "Chrome",
						"deviceModel": "web",
						"appName": "web",
						"deviceId": "bc83a564-4b91-11ef-8a44-83c5e90e038f"
					},
				)
				for url in urls
				if url["type"].lower() == "hls"
			][0]

		if group not in list(self.ChannelsList.keys()):
			self.ChannelsList[group] = []
			self.Categories.append(group)

		if self.ch_numbering == "original":
			if group == "Samsung":
				number = _id[-4:].upper().lstrip("0")
			elif group == "Xiaomi TV":
				number = _id[-4:].upper().lstrip("0")
			else:
				number = channel["number"]
		else:
			if _id in self.ch_numbers:
				number = self.ch_numbers[_id]["num"]
			else:
				number = self.ch_numbers["last_number"] + 1
				if number > 65535:
					raise ValueError(f"Generated channel number to big: {number}")
				self.ch_numbers["last_number"] = number
				number = f"{number:X}"
				self.ch_numbers[_id] = {}
				self.ch_numbers[_id]["num"] = number
				self.ch_numbers[_id]["name"] = channel["name"]
				self.ch_numbers_modified = True

		pname = self.pfunc[self.picon_mode](channel["name"])
		self.ChannelsList[group].append((str(number), _id, channel["name"], logo, urls, pname))
		self.total += 1
		return True

	@classmethod
	def addBouquet(cls, bouquet, region):
		if config.usage.multibouquet.value:
			bouquet_rootstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
		else:
			bouquet_rootstr = f'{cls.service_types_tv} FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
		bouquet_root = eServiceReference(bouquet_rootstr)
		serviceHandler = eServiceCenter.getInstance()
		mutableBouquetList = serviceHandler.list(bouquet_root).startEdit()
		if mutableBouquetList:
			esref = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + bouquet + '" ORDER BY bouquet'
			new_bouquet_ref = eServiceReference(esref)
			if not mutableBouquetList.addService(new_bouquet_ref):
				mutableBouquetList.flushChanges()
				eDVBDB.getInstance().reloadBouquets()
				mutableBouquet = serviceHandler.list(new_bouquet_ref).startEdit()
				if mutableBouquet:
					region = f" ({region.upper()})" if region != "local" else ""
					mutableBouquet.setListName(f"Pluto TV{region}")
					mutableBouquet.flushChanges()
				else:
					print("[PlutoDownload] get mutable list for new created bouquet failed")

	@staticmethod
	def convertgenre(genre):
		id = 0
		if any(
			(
				genre == "Classics",
				genre == "Romance",
				genre == "Thrillers",
				genre == "Horror",
				"Sci-Fi" in genre,
				"Action" in genre,
			)
		):
			id = 0x10
		elif "News" in genre or "Educational" in genre:
			id = 0x20
		elif genre == "Comedy":
			id = 0x30
		elif "Children" in genre:
			id = 0x50
		elif genre == "Music":
			id = 0x60
		elif genre == "Documentaries":
			id = 0xA0
		return id

	def buildGuide(self, ch, _id):
		timelines = ch.get("timelines", [])
		chplot = ch.get("description", "") or ch.get("summary", "")

		genres = set()
		self.GuideList[_id] = []
		for item in timelines:
			episode = item.get("episode", {}) or item
			series = episode.get("series", {}) or item
			epdur = int(episode.get("duration", "0") or "0") // 1000  # in seconds
			epgenre = episode.get("genre", "")

			genre = self.convertgenre(epgenre)
			if genre not in genres:
				genres.add(genre)
				self.GuideList[_id].append([])

			offset = datetime.datetime.now() - datetime.datetime.utcnow()
			starttime = self.strpTime(item["start"]) + offset
			start = time.mktime(starttime.timetuple())
			title = series.get("name", "") or item.get("title", "")
			tvplot = series.get("description", "") or series.get("summary", "") or chplot
			epnumber = episode.get("number", 0)
			epseason = episode.get("season", 0)
			eptype = series.get("type", "n/a")
			epname = episode["name"]
			epmpaa = episode.get("rating", "")
			epplot = episode.get("description", "") or tvplot or epname
			epsubgenre = episode.get("subGenre", "")

			if len(epmpaa) > 0 and "Not Rated" not in epmpaa:
				epplot = _("{0}\nAge rating: {1}").format(epplot, f"FSK-{epmpaa}" if epmpaa.isdigit() else epmpaa)

			if eptype == "tv" and (epseason > 0 and epnumber >= 0):
				epplot = _("{0}\n{1}. Season, episode {2}: {3}").format(epname, epseason, epnumber, epplot)
			elif eptype == "film" and epsubgenre not in ("None", ""):
				epplot = f"{epsubgenre}\n{epplot}"

			self.GuideList[_id][-1].append((int(round(start)), epdur, title, "", epplot, genre))

	def save_ch_numbers(self):
		if not self.ch_numbers_modified:
			return

		print("[PlutoDownload] Saving ch_numbers...")
		try:
			with open(self.CH_NUMBERS_PATH, "wb") as picklefile:
				dump(self.ch_numbers, picklefile, protocol=5)
				self.ch_numbers_modified = False
		except Exception as err:
			print("[PlutoDownload] Error saving ch_numbers: ", err)

	def read_ch_numbers(self):
		print("[PlutoDownload] Reading ch_numbers...")
		self.ch_numbers_modified = False
		self.ch_numbers = {"last_number": 0}
		try:
			with open(self.CH_NUMBERS_PATH, "rb") as picklefile:
				self.ch_numbers = load(picklefile)
		except Exception as err:
			print("[PlutoDownload] Error reading ch_numbers: ", err)


class PlutoDownload(Screen, PlutoAPIDownloader):
	if screenWidth and screenWidth == 1920:
		skin = """
		<screen name="PlutoTVdownload" position="60,60" size="615,195" title="PlutoTV EPG Download" flags="wfNoBorder" backgroundColor="#ff000000">
		<ePixmap name="background" position="0,0" size="615,195" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/backgroundHD.png" zPosition="-1" alphatest="off" />
		<widget name="picon" position="15,91" size="120,80" transparent="1" alphatest="blend" />
		<widget name="action" halign="left" valign="center" position="15,9" size="585,30" font="Regular;26" foregroundColor="#ffffff" transparent="1" backgroundColor="#000000" noWrap="1"/>
		<widget name="progress" position="150,127" size="420,12" backgroundColor="#1143495b" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/progresoHD.png" zPosition="2" />
		<eLabel name="fondoprogreso" position="150,127" size="420,12" backgroundColor="#102a3b58" />
		<widget name="espera" valign="center" halign="center" position="150,93" size="420,30" font="Regular;23" foregroundColor="#ffffff" transparent="1" backgroundColor="#000000" noWrap="1"/>
		<widget name="status" halign="center" valign="center" position="150,150" size="420,30" font="Regular;24" foregroundColor="#ffffff" transparent="1" backgroundColor="#000000" noWrap="1"/>
		</screen>"""
	else:
		skin = """
		<screen name="PlutoTVdownload" position="40,40" size="410,130" title="PlutoTV EPG Download" flags="wfNoBorder" backgroundColor="#ff000000">
		<ePixmap name="background" position="0,0" size="410,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/background.png" zPosition="-1" alphatest="off" />
		<widget name="picon" position="10,61" size="80,53" transparent="1" alphatest="blend" />
		<widget name="action" halign="left" valign="center" position="10,6" size="390,20" font="Regular;17" foregroundColor="#00ffffff" transparent="1" backgroundColor="#00000000" noWrap="1" />
		<widget name="progress" position="100,85" size="280,8" backgroundColor="#1143495b" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/progreso.png" zPosition="2" />
		<eLabel name="fondoprogreso" position="100,85" size="280,8" backgroundColor="#102a3b58" />
		<widget name="espera" valign="center" halign="center" position="100,62" size="280,20" font="Regular;15" foregroundColor="#00ffffff" transparent="1" backgroundColor="#00000000" noWrap="1" />
		<widget name="status" halign="center" valign="center" position="100,100" size="280,20" font="Regular;16" foregroundColor="#00ffffff" transparent="1" backgroundColor="#00000000" noWrap="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		PlutoAPIDownloader.__init__(self, False)
		self.skinName = "PlutoTVdownload"
		self["progress"] = ProgressBar()
		self["action"] = Label(_("Pluto TV download:"))
		self["espera"] = Label()
		self["status"] = Label(_("Wait..."))
		self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.salir}, -1)
		self["picon"] = Pixmap()
		self.onFirstExecBegin.append(self.init)

	def init(self):
		self["picon"].instance.setScale(1)
		self["picon"].instance.setPixmapFromFile("/usr/lib/enigma2/python/Plugins/Extensions/PlutoTV/images/picon.png")
		self["progress"].setValue(0)
		reactor.callLater(0, self.download)


class DownloadSilent(PlutoAPIDownloader):
	def __init__(self, session):
		PlutoAPIDownloader.__init__(self, True)
		self.timer = eTimer()
		self.timer.timeout.get().append(self.download)
		self.session = session
		self.start()

	def start(self):
		minutes = 60 * 5
		if fileExists("/etc/Plutotv.timer"):
			with open("/etc/Plutotv.timer", "r") as f:
				last = float(f.read().strip())
				minutes = minutes - int((time.time() - last) / 60)
				if minutes <= 0 or minutes > 60 * 24:
					minutes = 1
				self.timer.start(minutes * 60000, False)
		else:
			self.stop()

	def stop(self):
		self.timer.stop()


Silent = None

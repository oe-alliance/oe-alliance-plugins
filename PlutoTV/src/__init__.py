# -*- coding: utf-8 -*-
#
#   Copyright (C) 2021 Team OpenSPA
#   https://openspa.info/
#
#   Copyright (c) 2021-2024 Billy2011 @vuplus-support.org
#   Copyright (c) 2025 jbleyel
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
from __future__ import absolute_import
import gettext
import os
from collections import OrderedDict

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from enigma import getDesktop
from urllib.parse import parse_qsl, quote_plus, urlparse

__version__ = "20250731"

PluginLanguageDomain = "PlutoTV"
PluginLanguagePath = "Extensions/PlutoTV/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[" + PluginLanguageDomain + "] fallback to default translation for " + txt)
		return gettext.gettext(txt)


language.addCallback(localeInit)


def esHD():
	return getDesktop(0).size().width() > 1400


def update_qsd(url, qsd=None, safe="", quote_via=quote_plus):
	parsed = urlparse(url)
	current_qsd = OrderedDict(parse_qsl(parsed.query, keep_blank_values=True))

	for key, value in qsd.items():
		if value is not None:
			current_qsd[key] = value

	def dict2query(d):
		query = []
		for key in d.keys():
			query.append("{0}={1}".format(key, d[key]))
		return "&".join(query)

	query = quote_via(dict2query(current_qsd), safe="=&" + safe)

	return parsed._replace(query=query).geturl()


def bigStorage(minFree, default, *candidates):
	mounts = open("/proc/mounts", "rb").readlines()
	mountpoints = [x.split(b" ", 2)[1] for x in mounts]
	for candidate in candidates:
		if candidate.encode("utf-8") in mountpoints:
			try:
				diskstat = os.statvfs(candidate)
				free = diskstat.f_bavail * diskstat.f_frsize
				if free > minFree and free > 100 * 10 ** 6:
					print("[PlutoTV] Free space on selected mount {0}: {1}".format(candidate, free))
					return candidate
				else:
					print("[PlutoTV] Free space on test mount {0}: {1}".format(candidate, free))
			except Exception as err:
				print("[PlutoTV] Failed to stat %s:" % candidate, err)

	return default

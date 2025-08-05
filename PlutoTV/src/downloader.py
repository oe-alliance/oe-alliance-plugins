#   Copyright (c) 2021-2023 Billy2011 @ vuplus-support.org
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

from os.path import exists, getsize
import requests

from twisted.internet import threads, defer

from . import _


def download_with_requests(url, filename, timeout=30):
    def _download():
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        with open(filename, 'wb') as fd:
            fd.write(response.content)
        return filename

    return threads.deferToThread(_download)


class PlutoDownloader(object):

	def start(self, filename, sourcefile, overwrite=False):
		if not filename or not sourcefile:
			return defer.fail(Exception("[PlutoDownloader] Wrong arguments"))

		if not overwrite and exists(filename) and getsize(filename):
			return defer.succeed(filename)

		return download_with_requests(sourcefile, filename, timeout=30).addCallback(
			self.afterDownload, filename).addErrback(self.downloadFail, sourcefile)

	def afterDownload(self, result, filename):
		print("[PlutoDownloader] afterDownload", filename)
		try:
			if not getsize(filename):
				raise Exception("[PlutoDownloader] File is empty")
		except Exception as e:
			raise (e)
		else:
			return filename

	def downloadFail(self, failure, sourcefile):
		print(f"[PlutoDownloader] download failed, failure: {failure}\nsourcefile: {sourcefile}")
		return failure

# Copyright (C) 2023 jbleyel, Mr.Servo
#
# OAWeather is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# dogtag is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OAWeather.  If not, see <http://www.gnu.org/licenses/>.

# Some parts are taken from msnweathercomponent plugin for compatibility reasons.

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, BT_SCALE, BT_KEEP_ASPECT_RATIO, BT_HALIGN_CENTER, BT_VALIGN_CENTER
from Components.AVSwitch import AVSwitch
from enigma import ePicLoad, eSize


class OAWeatherPixmap(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintIconPixmapCB)
		self.iconFileName = ""

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		scaleSize = None
		for (attrib, value) in self.skinAttributes:
			if attrib == "size":
				x, y = value.split(',')
				scaleSize = eSize(int(x), int(y))
				break
		if scaleSize is None:
			print("OAWeatherPixmap ERROR size missing in skin")
			return
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((scaleSize.width(), scaleSize.height(), sc[0], sc[1], True, 2, '#ff000000'))

	def disconnectAll(self):
		self.picload.PictureData.get().remove(self.paintIconPixmapCB)
		self.picload = None
		Renderer.disconnectAll(self)

	def paintIconPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
			self.instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
		self.instance.setPixmap(ptr)

	def doSuspend(self, suspended):
		if suspended:
			self.changed((self.CHANGED_CLEAR,))
		else:
			self.changed((self.CHANGED_DEFAULT,))

	def updateIcon(self, filename: str):
		if self.iconFileName != filename:
			self.iconFileName = filename
			self.picload.startDecode(self.iconFileName)

	def changed(self, what):
		if what[0] != self.CHANGED_CLEAR:
			if self.instance:
				self.updateIcon(self.source.iconfilename)
		else:
			self.picload.startDecode("")

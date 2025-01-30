# -*- coding: utf-8 -*-
from six import PY2
try:
	from . import dpflib
except Exception:
	print("[LCD4linux] dpflib-Error")

PROPERTY_BRIGHTNESS = 0x01
PROPERTY_FGCOLOR = 0x02
PROPERTY_BGCOLOR = 0x03
PROPERTY_ORIENTATION = 0x10


def setBacklight(dev, value):
	try:
		dev.setProperty(PROPERTY_BRIGHTNESS, value)
		return True
	except Exception:
		print("[LCD4linux] Error set Backlight")
		return False


def showImage(dev, image):
	try:
		ir = image.convert("RGBA")
		x, y = image.size
		if PY2:
			dev.showRGBAImage(0, 0, x, y, ir.tostring())
		else:
			dev.showRGBAImage(0, 0, x, y, ir.tobytes())
		return True
	except Exception:
		print("[LCD4linux] Error writing DPF Device")
		return False


def open(usb):
	try:
		d = dpflib.open(usb)
#		d.setProperty(PROPERTY_ORIENTATION, 1)
		print("[LCD4linux] open %s" % usb)
	except Exception:
		d = None
		print("[LCD4linux] open Error: %s" % usb)
	return d


def close(dev):
	try:
		if dev is not None:
			dev.close()
	except Exception:
		pass

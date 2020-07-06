from __future__ import print_function
#import Image
from PIL import Image
try:
	import dpflib
except:
	print("[LCD4linux] dpflib-Error")


PROPERTY_BRIGHTNESS   = 0x01
PROPERTY_FGCOLOR      = 0x02
PROPERTY_BGCOLOR      = 0x03
PROPERTY_ORIENTATION  = 0x10

def setBacklight(dev, value):
	try:
		dev.setProperty(PROPERTY_BRIGHTNESS, value)
		return True
	except:
		print("[LCD4linux] Error set Backlight")
		return False
	
def showImage(dev, image):
	try:
		ir = image.convert("RGBA")
		x, y = image.size
		dev.showRGBAImage(0, 0, x, y, ir.tostring())
		return True
	except:
		print("[LCD4linux] Error writing DPF Device") 
		return False

def open(usb):
	try:
		d = dpflib.open(usb)
#		d.setProperty(PROPERTY_ORIENTATION, 1)
		print("[LCD4linux] open", usb)
	except:
		d = None
		print("[LCD4linux] open Error", usb)
	return d

def close(dev):
	try:
		if dev is not None:
			dev.close()
	except:
		pass

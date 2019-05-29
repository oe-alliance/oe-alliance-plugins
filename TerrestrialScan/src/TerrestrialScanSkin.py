#
# Note for people skinning the scan screen...
#
# There are six skinable outputs as follows:
#
# 1) self["Frontend"] > FrontendStatus
# 2) self["action"] > Label, 
# 3) self["status"] > Label,
# 4) self["tuner_text"] > Label, This is the tuner letter
# 5) self["progress"] > ProgressBar
# 6) self["progress_text"] > Progress
#

import os
import sys
from enigma import getDesktop

color = {
	"transpBlack": "#54111112",
#	"black" : "#00000000",
#	"red": "#00ff0000",
#	"grey": "#00888888",
#	"green": "#0056c856",
	}
plugin_root_folder = os.path.dirname(sys.modules[__name__].__file__) # no trailing slash
defaultDesktopHeight = 720
defaultDesktopWidth = 1280
multiplier = getDesktop(0).size().height() and 1.0 * getDesktop(0).size().height() / defaultDesktopHeight or 1.0
downloadBarHeight = 36
lockImageWidth = 38 # real width of .png
lockImageHeight = 36 # real height of .png
textBoxHeight = 30
fontSize = 22
textBoxTopMargin = 4
lockImageTopMargin = int((downloadBarHeight * multiplier / 2) - (lockImageHeight / 2))

actionBoxLeftAlign = 7
actionBoxWidth = 433
statusBoxLeftAlign = 466
statusBoxWidth = 433
lockImageRightAlign = 954
tunerBoxLeftAlign = 955
tunerBoxWidth = fontSize
snrBoxLeftAlign = 980
snrBoxWidth = 87 # up to 7 chars, e.g. "16.2 dB"
progressTextBoxLeftAlign = 1080
progressTextBoxWidth = 87
progressPercentLeftAlign = 1187
progressPercentBoxWidth = 73

downloadBar = \
	'<screen position="0,0" size="%d,%d" backgroundColor="%s" flags="wfNoBorder" >\n' % (int(defaultDesktopWidth * multiplier), int(downloadBarHeight * multiplier), color["transpBlack"]) + \
	'	<widget name="action" position="%d,%d" size="%d,%d" font="Regular;%d" backgroundColor="%s"/>\n' % (int(actionBoxLeftAlign * multiplier), int(textBoxTopMargin * multiplier), int(actionBoxWidth * multiplier), int(textBoxHeight * multiplier), int(fontSize * multiplier), color["transpBlack"]) + \
	'	<widget name="status" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" backgroundColor="%s"/>\n' % (int(statusBoxLeftAlign * multiplier), int(textBoxTopMargin * multiplier), int(statusBoxWidth * multiplier), int(textBoxHeight * multiplier), int(fontSize * multiplier), color["transpBlack"]) + \
	'	<widget source="Frontend" render="Pixmap" pixmap="%s/images/lock_on.png" position="%d,%d" size="%d,%d" alphatest="on">\n' % (plugin_root_folder, int(lockImageRightAlign * multiplier - lockImageWidth), lockImageTopMargin, lockImageWidth, lockImageHeight) + \
	'		<convert type="FrontendInfo">LOCK</convert>\n' + \
	'		<convert type="ConditionalShowHide"/>\n' + \
	'	</widget>\n' + \
	'	<widget source="Frontend" render="Pixmap" pixmap="%s/images/lock_off.png" position="%d,%d" size="%d,%d" alphatest="on">\n' % (plugin_root_folder, int(lockImageRightAlign * multiplier - lockImageWidth), lockImageTopMargin, lockImageWidth, lockImageHeight) + \
	'		<convert type="FrontendInfo">LOCK</convert>\n' + \
	'		<convert type="ConditionalShowHide">Invert</convert>\n' + \
	'	</widget>\n' + \
	'	<widget name="tuner_text" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" backgroundColor="%s"/>\n' % (int(tunerBoxLeftAlign * multiplier), int(textBoxTopMargin * multiplier), int(tunerBoxWidth * multiplier), int(textBoxHeight * multiplier), int(fontSize * multiplier), color["transpBlack"]) + \
	'	<widget source="Frontend" conditional="Frontend" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="left" backgroundColor="%s">\n' % (int(snrBoxLeftAlign * multiplier), int(textBoxTopMargin * multiplier), int(snrBoxWidth * multiplier), int(textBoxHeight * multiplier), int(fontSize * multiplier),  color["transpBlack"]) + \
	'		<convert type="FrontendInfo">SNRdB</convert>\n' + \
	'	</widget>\n' + \
	'	<widget source="progress_text" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="right" backgroundColor="%s">\n' % (int(progressTextBoxLeftAlign * multiplier), int(textBoxTopMargin * multiplier), int(progressTextBoxWidth * multiplier), int(textBoxHeight * multiplier), int(fontSize * multiplier),  color["transpBlack"]) + \
	'		<convert type="ProgressToText">InText</convert>\n' + \
	'	</widget>\n' + \
	'	<widget source="progress_text" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="left" backgroundColor="%s">\n' % (int(progressPercentLeftAlign * multiplier), int(textBoxTopMargin * multiplier), int(progressPercentBoxWidth * multiplier), int(textBoxHeight * multiplier), int(fontSize * multiplier),  color["transpBlack"]) + \
	'		<convert type="ProgressToText">InPercent</convert>\n' + \
	'	</widget>\n' + \
	'</screen>\n'

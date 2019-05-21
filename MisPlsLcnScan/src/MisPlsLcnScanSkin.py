#
# Note for people skinning the scanner screen...
#
# There are five skinable outputs as follows:
#
# 1) self["Frontend"] > FrontendStatus
# 2) self["action"] > Label
# 3) self["status"] > Label
# 4) self["progress"] > ProgressBar
# 5) self["progress_text"] > Progress
#

import os
import sys
from enigma import getDesktop

color = {
	"transpBlack": "#54111112",
#	"black" : "#00000000",
	}
plugin_root_folder = os.path.dirname(sys.modules[__name__].__file__) # no trailing slash
defaultDesktopHeight = 720
multiplier = getDesktop(0).size().height() and 1.0 * getDesktop(0).size().height() / defaultDesktopHeight or 1.0
downloadBarHeight = 36
lockImageWidth = 38
lockImageHeight = 36
fontSize = 22
fontTopMargin = 4
lockImageTopMargin = int((downloadBarHeight * multiplier / 2) - (lockImageHeight / 2))

downloadBar = \
	'<screen position="0,0" size="%d,%d" backgroundColor="%s" flags="wfNoBorder" >\n' % (int(1280 * multiplier), int(downloadBarHeight * multiplier), color["transpBlack"]) + \
	'	<widget name="action" position="%d,%d" size="%d,%d" font="Regular;%d" backgroundColor="%s"/>\n' % (int(7 * multiplier), int(fontTopMargin * multiplier), int(433 * multiplier), int(30 * multiplier), int(fontSize * multiplier), color["transpBlack"]) + \
	'	<widget name="status" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" backgroundColor="%s"/>\n' % (int(466 * multiplier), int(fontTopMargin * multiplier), int(433 * multiplier), int(30 * multiplier), int(fontSize * multiplier), color["transpBlack"]) + \
	'	<widget source="Frontend" conditional="Frontend" render="Pixmap" pixmap="%s/images/lock_on.png" position="%d,%d" size="%d,%d" alphatest="on">\n' % (plugin_root_folder, int(934 * multiplier), lockImageTopMargin, lockImageWidth, lockImageHeight) + \
	'		<convert type="FrontendInfo">LOCK</convert>\n' + \
	'		<convert type="ConditionalShowHide"/>\n' + \
	'	</widget>\n' + \
	'	<widget source="Frontend" conditional="Frontend" render="Pixmap" pixmap="%s/images/lock_off.png" position="%d,%d" size="%d,%d" alphatest="on">\n' % (plugin_root_folder, int(934 * multiplier), lockImageTopMargin, lockImageWidth, lockImageHeight) + \
	'		<convert type="FrontendInfo">LOCK</convert>\n' + \
	'		<convert type="ConditionalShowHide">Invert</convert>\n' + \
	'	</widget>\n' + \
	'	<widget source="Frontend" conditional="Frontend" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="left" backgroundColor="%s">\n' % (int((942 * multiplier) + lockImageWidth), int(4 * multiplier), int(87 * multiplier), int(30 * multiplier), int(fontSize * multiplier),  color["transpBlack"]) + \
	'		<convert type="FrontendInfo">SNRdB</convert>\n' + \
	'	</widget>\n' + \
	'	<widget source="progress_text" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="right" backgroundColor="%s">\n' % (int(1080 * multiplier), int(fontTopMargin * multiplier), int(87 * multiplier), int(30 * multiplier), int(fontSize * multiplier),  color["transpBlack"]) + \
	'		<convert type="ProgressToText">InText</convert>\n' + \
	'	</widget>\n' + \
	'	<widget source="progress_text" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="left" backgroundColor="%s">\n' % (int(1187 * multiplier), int(fontTopMargin * multiplier), int(73 * multiplier), int(30 * multiplier), int(fontSize * multiplier),  color["transpBlack"]) + \
	'		<convert type="ProgressToText">InPercent</convert>\n' + \
	'	</widget>\n' + \
	'</screen>\n'

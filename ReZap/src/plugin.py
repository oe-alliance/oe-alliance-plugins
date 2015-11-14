from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
import os
from enigma import eTimer
from time import sleep

#############

class LoopSyncMain(Screen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session
		self.gotSession()

	def gotSession(self):
		self.AVSyncTimer = eTimer()
		self.AVSyncTimer.callback.append(self.updateAVSync)
		self.AVSyncTimer.start(10000, True)

	def updateAVSync(self):
		self.current_service		= self.session.nav.getCurrentlyPlayingServiceReference()
		pts_diff = 0
		pts_diff1 = 0
		buff = "0"
		try:
			f = open("/sys/class/tsync/pts_audio", "r")
			pts_audio = int(f.read(),16)
			f.close()
			f = open("/sys/class/tsync/pts_video", "r")
			pts_video = int(f.read(),16)
			f.close()
			pts_diff = abs(pts_audio - pts_video)
			pts_diff1 = pts_audio - pts_video
			f = open("/sys/class/amstream/bufs", "r")
			line1 = f.read().replace('\n', '')
			f.close()
			strf1 = line1.find("Audio buffer:")
			strf2 = line1.find('buf current delay:' , strf1+1)
			strf3 = line1.find('ms' , strf2+1)
			if (strf3 - strf2) > 28:
				buff = "0"
			else:
				buff = line1[strf2+18:strf3]
		except Exception, e:
			print "[ReZap] Can't read class"
		msg = str(pts_diff)
		if pts_diff > 9000 and pts_video != 0: msg = msg + " Need restart !"
		if (pts_diff > 9000 and pts_video != 0 and pts_diff < 1000000) or (int(buff) > 47721800 and pts_video != 0):
			f_tmp = open("/tmp/restart.audio", "a")
			f_tmp.write("ReZap\n")
			f_tmp.close()
		self.AVSyncTimer.start(5000, True)

###################################                

def sessionstart(session, **kwargs):
	session.open(LoopSyncMain)
       
def Plugins(**kwargs):
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart)
		]

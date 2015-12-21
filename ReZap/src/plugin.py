from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
import os
from enigma import eTimer
from time import sleep

#########

class LoopSyncMain(Screen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session
		self.gotSession()

	def gotSession(self):
		self.debug = 1
		self.lstate = 0
		self.count1 = 0
		self.count2 = 0
		self.pts_diff_c = 0
		self.pts_diff_l = 0
		self.AVSyncTimer = eTimer()
		self.AVSyncTimer.callback.append(self.updateAVSync)
		self.AVSyncTimer.start(10000, True)

	def updateAVSync(self):
		self.current_service		= self.session.nav.getCurrentlyPlayingServiceReference()
		pts_diff = 0
		max_diff = 21000
		try:
			f = open("/sys/class/tsync/pts_audio", "r")
			pts_audio = int(f.read(),16)
			f.close()
			f = open("/sys/class/tsync/pts_video", "r")
			pts_video = int(f.read(),16)
			f.close()
			pts_diff = abs(pts_audio - pts_video)
			f = open("/sys/class/amstream/bufs", "r")
			line1 = f.read().replace('\n', '')
			f.close()
			strf1 = line1.find("Audio buffer:")
			strf2 = line1.find('buf bitrate latest:' , strf1+1)
			strf3 = line1.find(',avg:' , strf2+1)
			strf4 = line1.find('buf time after last pts:' , strf3+1)
			bitrate = int(line1[strf3+5:strf4-4])
			if bitrate < 110000: max_diff = 40000
			if self.debug == 1:
				print "[ReZap] *************************************"
#				print "[ReZap] pts_audio = " , pts_audio
#				print "[ReZap] pts_video = " , pts_video
				print "[ReZap] LastState = " , self.lstate
				print "[ReZap] pts_diff  = " , pts_diff
				print "[ReZap] max_diff  = " , max_diff
				print "[ReZap] a_bitrate = " , bitrate
				print "[ReZap] Reset(s)  = " , self.count1
				print "[ReZap] StopStart = " , self.count2
				print "[ReZap] ptsdiff_c = " , self.pts_diff_c
				print "[ReZap] *************************************"
		except Exception, e:
			print "[ReZap] Can't read class"
		if (self.lstate == 1) :
			if self.debug == 1 : print "[ReZap] change_mode (2) !!!"
			try:
				f_tmp = open("/sys/class/tsync/mode", "w")
				f_tmp.write("2")
				f_tmp.close()
			except Exception, e:
				print "[ReZap] Can't change mode"
			self.lstate = 0
			pts_video = 0
		if (self.pts_diff_l > max_diff and pts_diff > max_diff and pts_video != 0 and self.lstate == 0) :
			if self.debug == 1 : print "[ReZap] change_mode (1) !!!"
			try:
				f_tmp = open("/sys/class/tsync/mode", "w")
				f_tmp.write("1")
				f_tmp.close()
			except Exception, e:
				print "[ReZap] Can't change mode"
			self.lstate = 1
			self.count1 += 1
		if (pts_diff > 50000 and pts_video != 0) : self.pts_diff_c += 1
		if (pts_diff <= 50000 and pts_video != 0) : self.pts_diff_c = 0
		if self.pts_diff_c > 2 :
			if self.debug == 1 : print "[ReZap] DoAVSync !!!"
			self.session.open(DoAVSync)
			self.count2 += 1
			self.pts_diff_c = 0
		self.pts_diff_l = pts_diff
		self.AVSyncTimer.start(700, True)
                
###################################                
class DoAVSync(Screen):
  
	skin = """
		<screen position="center,center" size="1920,1080" title="ReZap" >
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		try:
			f_tmp = open("/sys/class/video/blackout_policy", "w")
			f_tmp.write("0")
			f_tmp.close()
		except Exception, e:
			print "[ReZap] Can't change policy"
		self.current_service		= self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		self.session.nav.playService(self.current_service)
		try:
			f_tmp = open("/sys/class/video/blackout_policy", "w")
			f_tmp.write("1")
			f_tmp.close()
		except Exception, e:
			print "[ReZap] Can't change policy"
		self.close()	


###################################                

def sessionstart(session, **kwargs):
	session.open(LoopSyncMain)
       
def Plugins(**kwargs):
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart)
		]

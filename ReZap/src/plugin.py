from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
import os
from enigma import eTimer
#########

class LoopSyncMain(Screen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session
		self.gotSession()

	def gotSession(self):
		self.AVSyncTimer = eTimer()
		self.AVSyncTimer.callback.append(self.UpdateStatus)
		self.AVSyncTimer.start(10000, True)

	def UpdateStatus(self):
		rst_status = 0
		try:
			f = open("/sys/class/tsync/reset_flag", "r")
			rst_status = int(f.read(),16)
			f.close()
		except Exception, e:
			print "[ReZap] Can't read class"
			self.AVSyncTimer.start(300, True)
			return
		if rst_status == 1 :
			print "[ReZap] DoReZap !!!"
			rst_status = 0
			self.session.open(DoReZap)
			self.AVSyncTimer.start(5000, True)
			return
		self.AVSyncTimer.start(100, True)
               
###################################                
class DoReZap(Screen):
  
	skin = """
		<screen position="center,center" size="1920,1080" title="" >
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		try:
			f_tmp = open("/sys/class/video/blackout_policy", "w")
			f_tmp.write("0")
			f_tmp.close()
			f_tmp = open("/sys/class/tsync/reset_flag", "w")
			f_tmp.write("0")
			f_tmp.close()
		except Exception, e:
			print "[ReZap] Can't change policy(0)"
		self.current_service		= self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		self.session.nav.playService(self.current_service)
		try:
			f_tmp = open("/sys/class/video/blackout_policy", "w")
			f_tmp.write("1")
			f_tmp.close()
		except Exception, e:
			print "[ReZap] Can't change policy(1)"
		self.close()	


###################################                

def sessionstart(session, **kwargs):
	session.open(LoopSyncMain)
       
def Plugins(**kwargs):
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart)
		]

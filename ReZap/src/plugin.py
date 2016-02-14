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
		self.ResetFlag()
		self.AVSyncTimer = eTimer()
		self.AVSyncTimer.callback.append(self.UpdateStatus)
		self.AVSyncTimer.start(10000, True)

	def UpdateStatus(self):
		frontendDataOrg = ""
		service1 = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		if service1:
			service = self.session.nav.getCurrentService()
			if service:
				feinfo = service.frontendInfo()
				frontendDataOrg = feinfo and feinfo.getAll(True)
				if frontendDataOrg:		### DVB-S/C/T ###
					if self.CheckFlag():
						print "[ReZap] DoReZap !!!"
						self.AVSyncTimer.start(500, True)
						self.ResetFlag()
						try:
							self.session.open(DoReZap,service1)
						except Exception, e:
							print "[ReZap] Can't ReZap"
					self.AVSyncTimer.start(100, True)
					return
				else:		### IPTV or VOD ###
					self.ResetFlag()
					self.AVSyncTimer.start(500, True)
					return
			else:
				self.AVSyncTimer.start(500, True)
				return

	def CheckFlag(self):
		try:
			if int(open("/sys/class/tsync/reset_flag", "r").read(),16) == 1: return True;
		except Exception, e:
			print "[ReZap] Can't read class"
			self.AVSyncTimer.start(500, True)
		return False;

	def ResetFlag(self):
		try:
			open("/sys/class/tsync/reset_flag", "w").write("0")
		except Exception, e:
			print "[ReZap] Can't ResetFlag"

###################################                
class DoReZap(Screen):
  
	skin = """
		<screen position="center,center" size="1920,1080" title="" >
		</screen>"""

	def __init__(self, session, xxx):
		Screen.__init__(self, session)

		try:
			open("/sys/class/video/blackout_policy", "w").write("0")
		except Exception, e:
			print "[ReZap] Can't change policy(0)"
		self.session.nav.stopService()
		self.session.nav.playService(xxx)
		try:
			open("/sys/class/video/blackout_policy", "w").write("1")
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
